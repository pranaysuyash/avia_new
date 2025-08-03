#!/usr/bin/env python3
"""
API Key Service
Manages API keys for developer access
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import redis
import json

from database.api_models import APIKey, APIKeyUsage, APIKeyStatus, APIKeyScope
from database.models import User
from services.audit_logging_service import audit_service, AuditEventType

logger = logging.getLogger(__name__)

class APIKeyService:
    """Service for managing API keys"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.redis_client = self._init_redis()
        self.cache_ttl = 300  # 5 minutes
    
    def _init_redis(self) -> Optional[redis.Redis]:
        """Initialize Redis client for caching"""
        try:
            import os
            client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=1,  # Use DB 1 for API keys
                decode_responses=True
            )
            client.ping()
            return client
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            return None
    
    def create_api_key(
        self,
        user_id: int,
        name: str,
        description: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        rate_limits: Optional[Dict[str, int]] = None,
        expires_in_days: Optional[int] = None,
        allowed_ips: Optional[List[str]] = None,
        allowed_origins: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new API key"""
        try:
            # Generate the key
            full_key, key_hash = APIKey.generate_key()
            key_prefix = full_key[:8]
            
            # Create API key record
            api_key = APIKey(
                user_id=user_id,
                name=name,
                key_prefix=key_prefix,
                key_hash=key_hash,
                description=description,
                scopes=scopes or [APIKeyScope.TRANSCRIPTS_READ.value],
                allowed_ips=allowed_ips or [],
                allowed_origins=allowed_origins or []
            )
            
            # Set rate limits
            if rate_limits:
                api_key.rate_limit_per_minute = rate_limits.get('per_minute', 60)
                api_key.rate_limit_per_hour = rate_limits.get('per_hour', 1000)
                api_key.rate_limit_per_day = rate_limits.get('per_day', 10000)
            
            # Set expiration
            if expires_in_days:
                api_key.expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            
            self.db.add(api_key)
            self.db.commit()
            self.db.refresh(api_key)
            
            # Log creation
            audit_service.log_event(
                event_type=AuditEventType.API_ERROR,  # Using as general API event
                action="API key created",
                user_id=user_id,
                resource_type="api_key",
                resource_id=str(api_key.id),
                details={
                    'name': name,
                    'scopes': scopes,
                    'expires_in_days': expires_in_days
                }
            )
            
            return {
                'id': api_key.id,
                'name': api_key.name,
                'key': full_key,  # Only returned once!
                'key_prefix': key_prefix,
                'scopes': api_key.scopes,
                'created_at': api_key.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create API key: {e}")
            self.db.rollback()
            raise
    
    def authenticate_api_key(self, key: str) -> Optional[APIKey]:
        """Authenticate and retrieve API key"""
        # Check cache first
        if self.redis_client:
            cached = self.redis_client.get(f"api_key:{key}")
            if cached:
                key_data = json.loads(cached)
                # Reconstruct APIKey object (simplified)
                api_key = self.db.query(APIKey).filter(
                    APIKey.id == key_data['id']
                ).first()
                if api_key:
                    return api_key
        
        # Hash the key
        key_hash = APIKey.hash_key(key)
        
        # Find the key
        api_key = self.db.query(APIKey).filter(
            APIKey.key_hash == key_hash
        ).first()
        
        if not api_key:
            return None
        
        # Check if valid
        if not api_key.is_valid():
            return None
        
        # Update last used
        api_key.last_used_at = datetime.utcnow()
        api_key.usage_count += 1
        self.db.commit()
        
        # Cache the key
        if self.redis_client and api_key:
            cache_data = {
                'id': api_key.id,
                'user_id': api_key.user_id,
                'scopes': api_key.scopes,
                'rate_limits': {
                    'per_minute': api_key.rate_limit_per_minute,
                    'per_hour': api_key.rate_limit_per_hour,
                    'per_day': api_key.rate_limit_per_day
                }
            }
            self.redis_client.setex(
                f"api_key:{key}",
                self.cache_ttl,
                json.dumps(cache_data)
            )
        
        return api_key
    
    def check_rate_limit(
        self,
        api_key: APIKey,
        ip_address: str
    ) -> tuple[bool, Optional[str], Dict[str, Any]]:
        """Check if API key has exceeded rate limits"""
        if not self.redis_client:
            # Can't check rate limits without Redis
            return True, None, {}
        
        current_minute = datetime.utcnow().strftime('%Y%m%d%H%M')
        current_hour = datetime.utcnow().strftime('%Y%m%d%H')
        current_day = datetime.utcnow().strftime('%Y%m%d')
        
        # Keys for rate limiting
        minute_key = f"rate:{api_key.id}:minute:{current_minute}"
        hour_key = f"rate:{api_key.id}:hour:{current_hour}"
        day_key = f"rate:{api_key.id}:day:{current_day}"
        
        # Get current counts
        minute_count = int(self.redis_client.get(minute_key) or 0)
        hour_count = int(self.redis_client.get(hour_key) or 0)
        day_count = int(self.redis_client.get(day_key) or 0)
        
        # Check limits
        if minute_count >= api_key.rate_limit_per_minute:
            return False, "Rate limit exceeded (per minute)", {
                'limit': api_key.rate_limit_per_minute,
                'current': minute_count,
                'reset_in': 60
            }
        
        if hour_count >= api_key.rate_limit_per_hour:
            return False, "Rate limit exceeded (per hour)", {
                'limit': api_key.rate_limit_per_hour,
                'current': hour_count,
                'reset_in': 3600
            }
        
        if day_count >= api_key.rate_limit_per_day:
            return False, "Rate limit exceeded (per day)", {
                'limit': api_key.rate_limit_per_day,
                'current': day_count,
                'reset_in': 86400
            }
        
        # Increment counters
        pipe = self.redis_client.pipeline()
        pipe.incr(minute_key)
        pipe.expire(minute_key, 60)
        pipe.incr(hour_key)
        pipe.expire(hour_key, 3600)
        pipe.incr(day_key)
        pipe.expire(day_key, 86400)
        pipe.execute()
        
        return True, None, {
            'remaining': {
                'minute': api_key.rate_limit_per_minute - minute_count - 1,
                'hour': api_key.rate_limit_per_hour - hour_count - 1,
                'day': api_key.rate_limit_per_day - day_count - 1
            }
        }
    
    def log_usage(
        self,
        api_key: APIKey,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: int,
        ip_address: str,
        user_agent: str,
        request_id: Optional[str] = None
    ):
        """Log API key usage"""
        try:
            usage = APIKeyUsage(
                api_key_id=api_key.id,
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time_ms=response_time_ms,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id
            )
            
            self.db.add(usage)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log API usage: {e}")
    
    def list_api_keys(
        self,
        user_id: int,
        include_revoked: bool = False
    ) -> List[Dict[str, Any]]:
        """List user's API keys"""
        query = self.db.query(APIKey).filter(
            APIKey.user_id == user_id
        )
        
        if not include_revoked:
            query = query.filter(
                APIKey.status != APIKeyStatus.REVOKED
            )
        
        api_keys = query.order_by(APIKey.created_at.desc()).all()
        
        return [
            {
                'id': key.id,
                'name': key.name,
                'key_prefix': key.key_prefix,
                'description': key.description,
                'scopes': key.scopes,
                'status': key.status.value,
                'last_used_at': key.last_used_at.isoformat() if key.last_used_at else None,
                'usage_count': key.usage_count,
                'expires_at': key.expires_at.isoformat() if key.expires_at else None,
                'created_at': key.created_at.isoformat()
            }
            for key in api_keys
        ]
    
    def get_api_key(
        self,
        key_id: int,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get API key details"""
        api_key = self.db.query(APIKey).filter(
            and_(
                APIKey.id == key_id,
                APIKey.user_id == user_id
            )
        ).first()
        
        if not api_key:
            return None
        
        # Get usage statistics
        usage_stats = self.get_usage_statistics(key_id)
        
        return {
            'id': api_key.id,
            'name': api_key.name,
            'key_prefix': api_key.key_prefix,
            'description': api_key.description,
            'scopes': api_key.scopes,
            'status': api_key.status.value,
            'rate_limits': {
                'per_minute': api_key.rate_limit_per_minute,
                'per_hour': api_key.rate_limit_per_hour,
                'per_day': api_key.rate_limit_per_day
            },
            'allowed_ips': api_key.allowed_ips,
            'allowed_origins': api_key.allowed_origins,
            'last_used_at': api_key.last_used_at.isoformat() if api_key.last_used_at else None,
            'usage_count': api_key.usage_count,
            'expires_at': api_key.expires_at.isoformat() if api_key.expires_at else None,
            'created_at': api_key.created_at.isoformat(),
            'usage_stats': usage_stats
        }
    
    def update_api_key(
        self,
        key_id: int,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        rate_limits: Optional[Dict[str, int]] = None,
        allowed_ips: Optional[List[str]] = None,
        allowed_origins: Optional[List[str]] = None
    ) -> bool:
        """Update API key settings"""
        api_key = self.db.query(APIKey).filter(
            and_(
                APIKey.id == key_id,
                APIKey.user_id == user_id
            )
        ).first()
        
        if not api_key:
            return False
        
        # Update fields
        if name is not None:
            api_key.name = name
        if description is not None:
            api_key.description = description
        if scopes is not None:
            api_key.scopes = scopes
        if allowed_ips is not None:
            api_key.allowed_ips = allowed_ips
        if allowed_origins is not None:
            api_key.allowed_origins = allowed_origins
        
        if rate_limits:
            if 'per_minute' in rate_limits:
                api_key.rate_limit_per_minute = rate_limits['per_minute']
            if 'per_hour' in rate_limits:
                api_key.rate_limit_per_hour = rate_limits['per_hour']
            if 'per_day' in rate_limits:
                api_key.rate_limit_per_day = rate_limits['per_day']
        
        api_key.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        # Clear cache
        if self.redis_client:
            # We don't have the full key, so clear by pattern
            for key in self.redis_client.scan_iter(f"api_key:*"):
                cached = self.redis_client.get(key)
                if cached:
                    data = json.loads(cached)
                    if data.get('id') == key_id:
                        self.redis_client.delete(key)
                        break
        
        # Log update
        audit_service.log_event(
            event_type=AuditEventType.API_ERROR,
            action="API key updated",
            user_id=user_id,
            resource_type="api_key",
            resource_id=str(key_id)
        )
        
        return True
    
    def revoke_api_key(
        self,
        key_id: int,
        user_id: int,
        reason: Optional[str] = None
    ) -> bool:
        """Revoke an API key"""
        api_key = self.db.query(APIKey).filter(
            and_(
                APIKey.id == key_id,
                APIKey.user_id == user_id
            )
        ).first()
        
        if not api_key:
            return False
        
        api_key.status = APIKeyStatus.REVOKED
        api_key.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        # Clear cache
        if self.redis_client:
            for key in self.redis_client.scan_iter(f"api_key:*"):
                cached = self.redis_client.get(key)
                if cached:
                    data = json.loads(cached)
                    if data.get('id') == key_id:
                        self.redis_client.delete(key)
                        break
        
        # Log revocation
        audit_service.log_event(
            event_type=AuditEventType.API_ERROR,
            action="API key revoked",
            user_id=user_id,
            resource_type="api_key",
            resource_id=str(key_id),
            details={'reason': reason}
        )
        
        return True
    
    def get_usage_statistics(
        self,
        key_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get API key usage statistics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total requests
        total_requests = self.db.query(func.count(APIKeyUsage.id)).filter(
            and_(
                APIKeyUsage.api_key_id == key_id,
                APIKeyUsage.timestamp >= start_date
            )
        ).scalar()
        
        # Requests by status
        status_dist = self.db.query(
            APIKeyUsage.status_code,
            func.count(APIKeyUsage.id).label('count')
        ).filter(
            and_(
                APIKeyUsage.api_key_id == key_id,
                APIKeyUsage.timestamp >= start_date
            )
        ).group_by(APIKeyUsage.status_code).all()
        
        # Average response time
        avg_response_time = self.db.query(
            func.avg(APIKeyUsage.response_time_ms)
        ).filter(
            and_(
                APIKeyUsage.api_key_id == key_id,
                APIKeyUsage.timestamp >= start_date
            )
        ).scalar()
        
        # Top endpoints
        top_endpoints = self.db.query(
            APIKeyUsage.endpoint,
            func.count(APIKeyUsage.id).label('count')
        ).filter(
            and_(
                APIKeyUsage.api_key_id == key_id,
                APIKeyUsage.timestamp >= start_date
            )
        ).group_by(APIKeyUsage.endpoint).order_by(
            func.count(APIKeyUsage.id).desc()
        ).limit(10).all()
        
        return {
            'total_requests': total_requests or 0,
            'status_distribution': [
                {'status': status, 'count': count}
                for status, count in status_dist
            ],
            'average_response_time_ms': float(avg_response_time or 0),
            'top_endpoints': [
                {'endpoint': endpoint, 'count': count}
                for endpoint, count in top_endpoints
            ]
        }
    
    def cleanup_expired_keys(self):
        """Clean up expired API keys"""
        expired_keys = self.db.query(APIKey).filter(
            and_(
                APIKey.expires_at.isnot(None),
                APIKey.expires_at < datetime.utcnow(),
                APIKey.status == APIKeyStatus.ACTIVE
            )
        ).all()
        
        for key in expired_keys:
            key.status = APIKeyStatus.EXPIRED
        
        self.db.commit()
        
        return len(expired_keys)