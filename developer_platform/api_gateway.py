"""
API Gateway and Authentication System

Provides comprehensive API management with authentication, rate limiting, and monitoring
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
import secrets
import hashlib
import time
from pydantic import BaseModel, Field, validator
import jwt
from collections import defaultdict
import asyncio
from functools import wraps

class APIKeyType(str, Enum):
    """Types of API keys"""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    SANDBOX = "sandbox"

class APIKeyStatus(str, Enum):
    """API key status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"

class RateLimitPlan(str, Enum):
    """Rate limiting plans"""
    FREE = "free"          # 100 requests/hour
    STARTER = "starter"    # 1000 requests/hour
    GROWTH = "growth"      # 10000 requests/hour
    SCALE = "scale"        # 100000 requests/hour
    ENTERPRISE = "enterprise"  # Custom

class WebhookEvent(str, Enum):
    """Webhook event types"""
    TRANSCRIPTION_STARTED = "transcription.started"
    TRANSCRIPTION_COMPLETED = "transcription.completed"
    TRANSCRIPTION_FAILED = "transcription.failed"
    ENTITY_EXTRACTION_COMPLETED = "entity_extraction.completed"
    SUMMARY_GENERATED = "summary.generated"
    EXPORT_COMPLETED = "export.completed"
    QUOTA_WARNING = "quota.warning"
    QUOTA_EXCEEDED = "quota.exceeded"

class APIKey(BaseModel):
    """API key model"""
    key_id: str
    key_hash: str  # Hashed API key
    key_prefix: str  # First 8 chars for identification
    name: str
    description: Optional[str]
    
    organization_id: str
    user_id: str
    
    key_type: APIKeyType
    status: APIKeyStatus
    rate_limit_plan: RateLimitPlan
    
    permissions: List[str] = []
    allowed_ips: List[str] = []
    allowed_origins: List[str] = []
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    
    # Usage tracking
    total_requests: int = 0
    requests_this_month: int = 0
    requests_today: int = 0

class APIRequest(BaseModel):
    """API request tracking"""
    request_id: str
    api_key_id: str
    endpoint: str
    method: str
    ip_address: str
    user_agent: Optional[str]
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    response_time_ms: Optional[float]
    status_code: Optional[int]
    error_message: Optional[str]
    
    # Request details
    request_size_bytes: int = 0
    response_size_bytes: int = 0
    processing_time_ms: Optional[float]

class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self):
        self.buckets: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "tokens": 0,
            "last_refill": time.time()
        })
        
        # Rate limit configurations (requests per hour)
        self.limits = {
            RateLimitPlan.FREE: {"requests": 100, "burst": 10},
            RateLimitPlan.STARTER: {"requests": 1000, "burst": 50},
            RateLimitPlan.GROWTH: {"requests": 10000, "burst": 200},
            RateLimitPlan.SCALE: {"requests": 100000, "burst": 1000},
            RateLimitPlan.ENTERPRISE: {"requests": 1000000, "burst": 5000}
        }
    
    def check_rate_limit(self, key_id: str, plan: RateLimitPlan) -> tuple[bool, Dict[str, Any]]:
        """Check if request is within rate limits"""
        config = self.limits[plan]
        max_tokens = config["burst"]
        refill_rate = config["requests"] / 3600  # Per second
        
        bucket = self.buckets[key_id]
        current_time = time.time()
        time_passed = current_time - bucket["last_refill"]
        
        # Refill tokens
        bucket["tokens"] = min(
            max_tokens,
            bucket["tokens"] + time_passed * refill_rate
        )
        bucket["last_refill"] = current_time
        
        # Check if request allowed
        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            return True, {
                "allowed": True,
                "remaining": int(bucket["tokens"]),
                "limit": config["requests"],
                "reset": int(current_time + 3600)
            }
        
        return False, {
            "allowed": False,
            "remaining": 0,
            "limit": config["requests"],
            "reset": int(current_time + 3600),
            "retry_after": int(1 / refill_rate)
        }

class WebhookEndpoint(BaseModel):
    """Webhook endpoint configuration"""
    endpoint_id: str
    organization_id: str
    url: str
    secret: str  # For HMAC signature
    
    events: List[WebhookEvent]
    is_active: bool = True
    
    # Delivery settings
    max_retries: int = 3
    timeout_seconds: int = 30
    
    # Statistics
    total_deliveries: int = 0
    successful_deliveries: int = 0
    failed_deliveries: int = 0
    last_delivery_at: Optional[datetime]
    last_error: Optional[str]

class APIGateway:
    """Main API gateway for authentication and request handling"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.rate_limiter = RateLimiter()
        self.api_keys: Dict[str, APIKey] = {}
        self.webhooks: Dict[str, List[WebhookEndpoint]] = defaultdict(list)
        self.request_history: List[APIRequest] = []
        
        # Endpoint permissions
        self.endpoint_permissions = {
            "/api/v1/transcribe": ["transcription.create"],
            "/api/v1/transcriptions": ["transcription.read"],
            "/api/v1/entities": ["entities.read"],
            "/api/v1/summaries": ["summaries.create"],
            "/api/v1/export": ["export.create"],
            "/api/v1/webhooks": ["webhooks.manage"],
            "/api/v1/usage": ["usage.read"]
        }
    
    def generate_api_key(
        self,
        organization_id: str,
        user_id: str,
        name: str,
        key_type: APIKeyType,
        rate_limit_plan: RateLimitPlan,
        permissions: List[str],
        expires_in_days: Optional[int] = None
    ) -> tuple[str, APIKey]:
        """Generate new API key"""
        # Generate secure random key
        raw_key = secrets.token_urlsafe(32)
        key_prefix = raw_key[:8]
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Create API key object
        api_key = APIKey(
            key_id=f"key_{secrets.token_urlsafe(16)}",
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=name,
            organization_id=organization_id,
            user_id=user_id,
            key_type=key_type,
            status=APIKeyStatus.ACTIVE,
            rate_limit_plan=rate_limit_plan,
            permissions=permissions
        )
        
        if expires_in_days:
            api_key.expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Store key
        self.api_keys[api_key.key_id] = api_key
        
        return raw_key, api_key
    
    def validate_api_key(self, raw_key: str) -> Optional[APIKey]:
        """Validate API key and return key object"""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        for api_key in self.api_keys.values():
            if api_key.key_hash == key_hash:
                # Check status
                if api_key.status != APIKeyStatus.ACTIVE:
                    return None
                
                # Check expiration
                if api_key.expires_at and api_key.expires_at < datetime.utcnow():
                    api_key.status = APIKeyStatus.EXPIRED
                    return None
                
                # Update last used
                api_key.last_used_at = datetime.utcnow()
                return api_key
        
        return None
    
    def check_permissions(self, api_key: APIKey, endpoint: str) -> bool:
        """Check if API key has permission for endpoint"""
        required_permissions = self.endpoint_permissions.get(endpoint, [])
        
        # Check if key has all required permissions
        for perm in required_permissions:
            if perm not in api_key.permissions:
                return False
        
        return True
    
    def authenticate_request(
        self,
        api_key_header: str,
        endpoint: str,
        method: str,
        ip_address: str,
        origin: Optional[str] = None
    ) -> tuple[bool, Optional[APIKey], Dict[str, Any]]:
        """Authenticate API request"""
        # Extract API key
        if not api_key_header or not api_key_header.startswith("Bearer "):
            return False, None, {"error": "Invalid authorization header"}
        
        raw_key = api_key_header.replace("Bearer ", "")
        
        # Validate key
        api_key = self.validate_api_key(raw_key)
        if not api_key:
            return False, None, {"error": "Invalid API key"}
        
        # Check IP whitelist
        if api_key.allowed_ips and ip_address not in api_key.allowed_ips:
            return False, None, {"error": "IP address not allowed"}
        
        # Check origin whitelist
        if api_key.allowed_origins and origin and origin not in api_key.allowed_origins:
            return False, None, {"error": "Origin not allowed"}
        
        # Check permissions
        if not self.check_permissions(api_key, endpoint):
            return False, None, {"error": "Insufficient permissions"}
        
        # Check rate limit
        allowed, rate_limit_info = self.rate_limiter.check_rate_limit(
            api_key.key_id,
            api_key.rate_limit_plan
        )
        
        if not allowed:
            return False, None, {
                "error": "Rate limit exceeded",
                "rate_limit": rate_limit_info
            }
        
        # Update usage counters
        api_key.total_requests += 1
        api_key.requests_today += 1
        api_key.requests_this_month += 1
        
        return True, api_key, {"rate_limit": rate_limit_info}
    
    def log_request(
        self,
        api_key: APIKey,
        endpoint: str,
        method: str,
        ip_address: str,
        response_time_ms: float,
        status_code: int,
        request_size: int = 0,
        response_size: int = 0,
        error_message: Optional[str] = None
    ):
        """Log API request"""
        request = APIRequest(
            request_id=f"req_{secrets.token_urlsafe(16)}",
            api_key_id=api_key.key_id,
            endpoint=endpoint,
            method=method,
            ip_address=ip_address,
            response_time_ms=response_time_ms,
            status_code=status_code,
            error_message=error_message,
            request_size_bytes=request_size,
            response_size_bytes=response_size
        )
        
        self.request_history.append(request)
        
        # Trim history to last 10000 requests
        if len(self.request_history) > 10000:
            self.request_history = self.request_history[-10000:]
    
    def register_webhook(
        self,
        organization_id: str,
        url: str,
        events: List[WebhookEvent],
        secret: Optional[str] = None
    ) -> WebhookEndpoint:
        """Register webhook endpoint"""
        webhook = WebhookEndpoint(
            endpoint_id=f"hook_{secrets.token_urlsafe(16)}",
            organization_id=organization_id,
            url=url,
            secret=secret or secrets.token_urlsafe(32),
            events=events
        )
        
        self.webhooks[organization_id].append(webhook)
        return webhook
    
    async def trigger_webhooks(
        self,
        organization_id: str,
        event: WebhookEvent,
        payload: Dict[str, Any]
    ):
        """Trigger webhooks for event"""
        webhooks = self.webhooks.get(organization_id, [])
        
        for webhook in webhooks:
            if webhook.is_active and event in webhook.events:
                # Create signed payload
                timestamp = int(time.time())
                signature_payload = f"{timestamp}.{json.dumps(payload)}"
                signature = hmac.new(
                    webhook.secret.encode(),
                    signature_payload.encode(),
                    hashlib.sha256
                ).hexdigest()
                
                # Send webhook
                headers = {
                    "X-Webhook-Timestamp": str(timestamp),
                    "X-Webhook-Signature": signature,
                    "X-Webhook-Event": event.value
                }
                
                # This would be async HTTP request in production
                await self._deliver_webhook(webhook, payload, headers)
    
    async def _deliver_webhook(
        self,
        webhook: WebhookEndpoint,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ):
        """Deliver webhook with retries"""
        # Implementation would include:
        # - Async HTTP request
        # - Exponential backoff retries
        # - Error handling
        # - Delivery statistics update
        pass
    
    def get_usage_statistics(
        self,
        api_key_id: str,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Get API usage statistics"""
        cutoff_date = datetime.utcnow() - timedelta(days=period_days)
        
        # Filter requests
        key_requests = [
            r for r in self.request_history
            if r.api_key_id == api_key_id and r.timestamp >= cutoff_date
        ]
        
        if not key_requests:
            return {
                "total_requests": 0,
                "average_response_time_ms": 0,
                "error_rate": 0,
                "endpoints": {},
                "daily_usage": {}
            }
        
        # Calculate statistics
        total_requests = len(key_requests)
        error_requests = len([r for r in key_requests if r.status_code >= 400])
        response_times = [r.response_time_ms for r in key_requests if r.response_time_ms]
        
        # Endpoint breakdown
        endpoint_stats = defaultdict(lambda: {"count": 0, "errors": 0})
        for req in key_requests:
            endpoint_stats[req.endpoint]["count"] += 1
            if req.status_code >= 400:
                endpoint_stats[req.endpoint]["errors"] += 1
        
        # Daily breakdown
        daily_stats = defaultdict(int)
        for req in key_requests:
            date_key = req.timestamp.date().isoformat()
            daily_stats[date_key] += 1
        
        return {
            "total_requests": total_requests,
            "average_response_time_ms": sum(response_times) / len(response_times) if response_times else 0,
            "error_rate": error_requests / total_requests if total_requests > 0 else 0,
            "endpoints": dict(endpoint_stats),
            "daily_usage": dict(daily_stats),
            "request_size_mb": sum(r.request_size_bytes for r in key_requests) / 1024 / 1024,
            "response_size_mb": sum(r.response_size_bytes for r in key_requests) / 1024 / 1024
        }

def api_key_required(gateway: APIGateway):
    """Decorator for API key authentication"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            # Extract authentication info
            auth_header = request.headers.get("Authorization", "")
            endpoint = request.path
            method = request.method
            ip_address = request.client.host
            origin = request.headers.get("Origin")
            
            # Authenticate
            authenticated, api_key, info = gateway.authenticate_request(
                auth_header, endpoint, method, ip_address, origin
            )
            
            if not authenticated:
                return {"error": info.get("error", "Authentication failed")}, 401
            
            # Add API key to request
            request.state.api_key = api_key
            request.state.rate_limit = info.get("rate_limit", {})
            
            # Execute endpoint
            start_time = time.time()
            try:
                response = await func(request, *args, **kwargs)
                status_code = 200
                error_message = None
            except Exception as e:
                response = {"error": str(e)}
                status_code = 500
                error_message = str(e)
            
            # Log request
            response_time = (time.time() - start_time) * 1000
            gateway.log_request(
                api_key,
                endpoint,
                method,
                ip_address,
                response_time,
                status_code,
                error_message=error_message
            )
            
            return response
        
        return wrapper
    return decorator

# Example usage
if __name__ == "__main__":
    import json
    import hmac
    
    # Initialize gateway
    gateway = APIGateway(secret_key="your-secret-key")
    
    # Generate API key
    raw_key, api_key = gateway.generate_api_key(
        organization_id="org_123",
        user_id="user_456",
        name="Production API Key",
        key_type=APIKeyType.PRODUCTION,
        rate_limit_plan=RateLimitPlan.GROWTH,
        permissions=[
            "transcription.create",
            "transcription.read",
            "entities.read",
            "summaries.create"
        ]
    )
    
    print(f"Generated API Key: {raw_key}")
    print(f"Key ID: {api_key.key_id}")
    print(f"Key Prefix: {api_key.key_prefix}")
    
    # Test authentication
    auth_result = gateway.authenticate_request(
        f"Bearer {raw_key}",
        "/api/v1/transcribe",
        "POST",
        "192.168.1.1"
    )
    
    print(f"\nAuthentication result: {auth_result[0]}")
    if auth_result[0]:
        print(f"Rate limit info: {auth_result[2]['rate_limit']}")
    
    # Register webhook
    webhook = gateway.register_webhook(
        organization_id="org_123",
        url="https://example.com/webhooks",
        events=[
            WebhookEvent.TRANSCRIPTION_COMPLETED,
            WebhookEvent.ENTITY_EXTRACTION_COMPLETED
        ]
    )
    
    print(f"\nRegistered webhook: {webhook.endpoint_id}")
    print(f"Webhook secret: {webhook.secret}")