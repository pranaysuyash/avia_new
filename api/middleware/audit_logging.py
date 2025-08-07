"""
Audit Logging Middleware
Tracks all user actions for compliance and security monitoring
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps
from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, JSON, Integer, Float

from api.auth_middleware import get_current_user
from database.connection import get_db
from database.models import Base
import uuid

logger = logging.getLogger(__name__)

# Database model for audit logs
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    action = Column(String, nullable=False)  # CREATE, READ, UPDATE, DELETE, LOGIN, etc.
    resource_type = Column(String, nullable=False)  # transcription, user, team, etc.
    resource_id = Column(String)  # ID of the affected resource
    endpoint = Column(String, nullable=False)  # API endpoint called
    method = Column(String, nullable=False)  # HTTP method
    ip_address = Column(String)
    user_agent = Column(String)
    request_data = Column(JSON)  # Request payload (sanitized)
    response_status = Column(Integer)  # HTTP status code
    processing_time_ms = Column(Float)  # Time taken to process request
    risk_score = Column(Integer, default=0)  # Security risk assessment
    extra_data = Column(JSON)  # Additional context
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLogger:
    """Central audit logging service"""
    
    RISK_LEVELS = {
        'LOW': 1,
        'MEDIUM': 5,
        'HIGH': 8,
        'CRITICAL': 10
    }
    
    HIGH_RISK_ACTIONS = {
        'DELETE', 'ADMIN_ACTION', 'PASSWORD_CHANGE', 'PERMISSION_CHANGE',
        'EXPORT_DATA', 'TEAM_MEMBER_REMOVE', 'API_KEY_CREATE', 'API_KEY_DELETE'
    }
    
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
    
    def _get_db(self) -> Session:
        """Get database session"""
        return self.db_session_factory()
    
    def _sanitize_request_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive data from request payload"""
        if not data:
            return {}
        
        sanitized = data.copy()
        
        # List of sensitive fields to redact
        sensitive_fields = {
            'password', 'token', 'api_key', 'secret', 'private_key',
            'authorization', 'auth_token', 'refresh_token', 'session_id',
            'credit_card', 'ssn', 'social_security', 'bank_account'
        }
        
        def redact_sensitive(obj, path=""):
            if isinstance(obj, dict):
                result = {}
                for key, value in obj.items():
                    key_lower = key.lower()
                    if any(sensitive in key_lower for sensitive in sensitive_fields):
                        result[key] = "[REDACTED]"
                    else:
                        result[key] = redact_sensitive(value, f"{path}.{key}")
                return result
            elif isinstance(obj, list):
                return [redact_sensitive(item, f"{path}[{i}]") for i, item in enumerate(obj)]
            else:
                return obj
        
        return redact_sensitive(sanitized)
    
    def _calculate_risk_score(self, action: str, resource_type: str, user_id: str, 
                            ip_address: str, method: str) -> int:
        """Calculate security risk score for the action"""
        score = self.RISK_LEVELS['LOW']
        
        # High-risk actions
        if action in self.HIGH_RISK_ACTIONS:
            score = self.RISK_LEVELS['HIGH']
        
        # Admin actions are always high risk
        if 'ADMIN' in action.upper():
            score = self.RISK_LEVELS['HIGH']
        
        # DELETE operations are medium risk
        if action == 'DELETE' or method == 'DELETE':
            score = max(score, self.RISK_LEVELS['MEDIUM'])
        
        # Sensitive resource types
        sensitive_resources = {'user', 'team', 'api_key', 'webhook', 'payment'}
        if resource_type.lower() in sensitive_resources:
            score = max(score, self.RISK_LEVELS['MEDIUM'])
        
        # Bulk operations
        if 'BATCH' in action.upper() or 'BULK' in action.upper():
            score = max(score, self.RISK_LEVELS['MEDIUM'])
        
        return score
    
    def log_action(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        endpoint: str,
        method: str,
        resource_id: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        response_status: Optional[int] = None,
        processing_time_ms: Optional[float] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log an audit event"""
        db = self._get_db()
        try:
            # Calculate risk score
            risk_score = self._calculate_risk_score(
                action, resource_type, user_id, ip_address or '', method
            )
            
            # Create audit log entry
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                endpoint=endpoint,
                method=method,
                ip_address=ip_address,
                user_agent=user_agent,
                request_data=self._sanitize_request_data(request_data or {}),
                response_status=response_status,
                processing_time_ms=processing_time_ms,
                risk_score=risk_score,
                extra_data=extra_data or {}
            )
            
            db.add(audit_log)
            db.commit()
            
            # Log high-risk actions to system logger
            if risk_score >= self.RISK_LEVELS['HIGH']:
                logger.warning(
                    f"HIGH RISK ACTION: User {user_id} performed {action} on {resource_type} "
                    f"from IP {ip_address} - Risk Score: {risk_score}"
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {str(e)}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_risk_score: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Query audit logs with filters"""
        db = self._get_db()
        try:
            query = db.query(AuditLog)
            
            # Apply filters
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            if action:
                query = query.filter(AuditLog.action == action)
            if resource_type:
                query = query.filter(AuditLog.resource_type == resource_type)
            if start_date:
                query = query.filter(AuditLog.created_at >= start_date)
            if end_date:
                query = query.filter(AuditLog.created_at <= end_date)
            if min_risk_score:
                query = query.filter(AuditLog.risk_score >= min_risk_score)
            
            # Get total count
            total = query.count()
            
            # Apply pagination and ordering
            logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
            
            return {
                'total': total,
                'logs': [
                    {
                        'id': log.id,
                        'user_id': log.user_id,
                        'action': log.action,
                        'resource_type': log.resource_type,
                        'resource_id': log.resource_id,
                        'endpoint': log.endpoint,
                        'method': log.method,
                        'ip_address': log.ip_address,
                        'response_status': log.response_status,
                        'processing_time_ms': log.processing_time_ms,
                        'risk_score': log.risk_score,
                        'extra_data': log.extra_data,
                        'created_at': log.created_at.isoformat()
                    }
                    for log in logs
                ]
            }
            
        finally:
            db.close()

# Global audit logger instance
from database.connection import get_db_session_factory
db_session_factory = get_db_session_factory()
audit_logger = AuditLogger(db_session_factory)

def audit_action(
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    include_request_data: bool = False
):
    """
    Decorator to automatically audit API endpoint calls
    
    Usage:
        @audit_action('CREATE', 'transcription', include_request_data=True)
        async def create_transcription(...)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request and current_user in kwargs
            request = None
            current_user = None
            start_time = datetime.now()
            
            for key, value in kwargs.items():
                if key == 'request' and hasattr(value, 'method'):
                    request = value
                elif key == 'current_user' and isinstance(value, dict):
                    current_user = value
            
            # Extract request info
            endpoint = request.url.path if request else func.__name__
            method = request.method if request else 'UNKNOWN'
            ip_address = request.client.host if request else None
            user_agent = request.headers.get('user-agent') if request else None
            
            # Get request data if requested
            request_data = None
            if include_request_data and request:
                try:
                    if request.method in ['POST', 'PUT', 'PATCH']:
                        # For JSON requests, try to get the body
                        # Note: This is a simplified approach
                        request_data = dict(request.query_params)
                except Exception:
                    request_data = None
            
            # Execute the function
            response_status = 200
            error = None
            result = None
            
            try:
                result = await func(*args, **kwargs)
                return result
            except HTTPException as e:
                response_status = e.status_code
                error = str(e)
                raise
            except Exception as e:
                response_status = 500
                error = str(e)
                raise
            finally:
                # Calculate processing time
                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                
                # Log the action
                if current_user:
                    audit_logger.log_action(
                        user_id=current_user.get('id', 'unknown'),
                        action=action,
                        resource_type=resource_type,
                        endpoint=endpoint,
                        method=method,
                        resource_id=resource_id,
                        request_data=request_data,
                        response_status=response_status,
                        processing_time_ms=processing_time,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        extra_data={
                            'function': func.__name__,
                            'error': error
                        }
                    )
        
        return wrapper
    return decorator

# Utility functions for common audit patterns
def audit_login(user_id: str, ip_address: str, user_agent: str, success: bool):
    """Log login attempts"""
    audit_logger.log_action(
        user_id=user_id,
        action='LOGIN_SUCCESS' if success else 'LOGIN_FAILED',
        resource_type='auth',
        endpoint='/api/v1/auth/login',
        method='POST',
        ip_address=ip_address,
        user_agent=user_agent,
        response_status=200 if success else 401,
        extra_data={'success': success}
    )

def audit_data_export(user_id: str, export_type: str, resource_count: int, ip_address: str):
    """Log data export operations"""
    audit_logger.log_action(
        user_id=user_id,
        action='EXPORT_DATA',
        resource_type='data_export',
        endpoint='/api/v1/export',
        method='POST',
        ip_address=ip_address,
        extra_data={
            'export_type': export_type,
            'resource_count': resource_count
        }
    )

def audit_admin_action(user_id: str, admin_action: str, target_user_id: str, ip_address: str):
    """Log administrative actions"""
    audit_logger.log_action(
        user_id=user_id,
        action=f'ADMIN_{admin_action.upper()}',
        resource_type='admin',
        endpoint='/api/v1/admin',
        method='POST',
        resource_id=target_user_id,
        ip_address=ip_address,
        extra_data={'admin_action': admin_action, 'target_user': target_user_id}
    )

def audit_log(
    user_id: str,
    action: str,
    resource_type: str,
    endpoint: str,
    method: str = 'POST',
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    extra_data: Optional[Dict[str, Any]] = None
):
    """Simple audit logging function for database module"""
    return audit_logger.log_action(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        endpoint=endpoint,
        method=method,
        resource_id=resource_id,
        ip_address=ip_address,
        extra_data=extra_data
    )