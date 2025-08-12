"""
Core middleware components for authentication, validation, and error handling
"""

from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, Dict, Any, Callable
import time
import json
from datetime import datetime

from .logging import get_logger
from .metrics import MetricsCollector
from .exceptions import AuthenticationError, ValidationError, RateLimitError

logger = get_logger("middleware")

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware that validates JWT tokens and API keys
    """
    
    def __init__(
        self,
        app,
        token_validator: Callable[[str], Dict[str, Any]],
        api_key_validator: Optional[Callable[[str], Dict[str, Any]]] = None,
        exclude_paths: Optional[list] = None
    ):
        super().__init__(app)
        self.token_validator = token_validator
        self.api_key_validator = api_key_validator
        self.exclude_paths = exclude_paths or [
            "/health", "/metrics", "/api/docs", "/api/redoc", "/openapi.json"
        ]
        self.security = HTTPBearer(auto_error=False)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip authentication for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Skip WebSocket connections
        if request.url.path.startswith("/ws/"):
            return await call_next(request)
        
        try:
            # Try to authenticate the request
            user_context = await self._authenticate_request(request)
            request.state.user = user_context
            
            return await call_next(request)
            
        except AuthenticationError as e:
            logger.warning(f"Authentication failed: {e.message}")
            return Response(
                content=json.dumps({
                    "error": {
                        "code": e.status_code,
                        "message": e.message,
                        "type": "authentication_error"
                    }
                }),
                status_code=e.status_code,
                media_type="application/json"
            )
    
    async def _authenticate_request(self, request: Request) -> Dict[str, Any]:
        """Authenticate request using JWT token or API key"""
        
        # Try Authorization header first (JWT token)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                user_context = self.token_validator(token)
                if user_context:
                    return user_context
            except Exception as e:
                logger.debug(f"JWT validation failed: {str(e)}")
        
        # Try API key authentication
        api_key = request.headers.get("X-API-Key")
        if api_key and self.api_key_validator:
            try:
                user_context = self.api_key_validator(api_key)
                if user_context:
                    return user_context
            except Exception as e:
                logger.debug(f"API key validation failed: {str(e)}")
        
        # No valid authentication found
        raise AuthenticationError("Valid authentication required")

class ValidationMiddleware(BaseHTTPMiddleware):
    """
    Request validation middleware
    """
    
    def __init__(
        self,
        app,
        max_request_size: int = 100 * 1024 * 1024,  # 100MB
        allowed_content_types: Optional[list] = None
    ):
        super().__init__(app)
        self.max_request_size = max_request_size
        self.allowed_content_types = allowed_content_types or [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
            "text/plain"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            # Validate request size
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.max_request_size:
                raise ValidationError(
                    f"Request too large. Maximum size: {self.max_request_size} bytes"
                )
            
            # Validate content type for POST/PUT requests
            if request.method in ["POST", "PUT", "PATCH"]:
                content_type = request.headers.get("content-type", "").split(";")[0]
                if content_type and content_type not in self.allowed_content_types:
                    raise ValidationError(f"Unsupported content type: {content_type}")
            
            return await call_next(request)
            
        except ValidationError as e:
            logger.warning(f"Validation failed: {e.message}")
            return Response(
                content=json.dumps({
                    "error": {
                        "code": e.status_code,
                        "message": e.message,
                        "type": "validation_error",
                        "details": e.details
                    }
                }),
                status_code=e.status_code,
                media_type="application/json"
            )

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Global error handling middleware
    """
    
    def __init__(self, app, debug: bool = False):
        super().__init__(app)
        self.debug = debug
        self.metrics = MetricsCollector("error_handling")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
            
        except HTTPException:
            # Let FastAPI handle HTTP exceptions
            raise
            
        except Exception as e:
            # Handle unexpected errors
            request_id = getattr(request.state, 'request_id', 'unknown')
            
            logger.error(
                f"Unhandled error in request {request_id}: {str(e)}",
                extra={"request_id": request_id},
                exc_info=True
            )
            
            self.metrics.increment_counter("unhandled_errors")
            
            error_response = {
                "error": {
                    "code": 500,
                    "message": "Internal server error",
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            # Include stack trace in debug mode
            if self.debug:
                import traceback
                error_response["error"]["traceback"] = traceback.format_exc()
            
            return Response(
                content=json.dumps(error_response),
                status_code=500,
                media_type="application/json"
            )

class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Metrics collection middleware
    """
    
    def __init__(self, app, service_name: str = "api"):
        super().__init__(app)
        self.metrics = MetricsCollector(service_name)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Increment request counter
        self.metrics.increment_counter("requests_total")
        self.metrics.increment_counter(f"requests_by_method.{request.method.lower()}")
        
        try:
            response = await call_next(request)
            
            # Record response metrics
            duration = time.time() - start_time
            self.metrics.record_histogram("request_duration_seconds", duration)
            self.metrics.increment_counter(f"responses_by_status.{response.status_code}")
            
            # Add metrics headers
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            
            return response
            
        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            self.metrics.record_histogram("request_duration_seconds", duration)
            self.metrics.increment_counter("requests_failed")
            self.metrics.increment_counter(f"errors_by_type.{type(e).__name__.lower()}")
            
            raise

class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using sliding window algorithm
    """
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        storage_backend: Optional[Any] = None,
        exclude_paths: Optional[list] = None
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.storage = storage_backend or {}  # In-memory fallback
        self.exclude_paths = exclude_paths or ["/health", "/metrics"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Check rate limits
        if not await self._check_rate_limit(client_id):
            raise RateLimitError(retry_after=60)
        
        return await call_next(request)
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get user ID from request state
        user = getattr(request.state, 'user', None)
        if user and user.get('user_id'):
            return f"user:{user['user_id']}"
        
        # Fall back to IP address
        client_ip = request.client.host
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return f"ip:{client_ip}"
    
    async def _check_rate_limit(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit"""
        current_time = time.time()
        
        # Simple in-memory rate limiting (use Redis in production)
        if client_id not in self.storage:
            self.storage[client_id] = {"minute": [], "hour": []}
        
        client_data = self.storage[client_id]
        
        # Clean old entries
        client_data["minute"] = [
            t for t in client_data["minute"] 
            if current_time - t < 60
        ]
        client_data["hour"] = [
            t for t in client_data["hour"] 
            if current_time - t < 3600
        ]
        
        # Check limits
        if len(client_data["minute"]) >= self.requests_per_minute:
            return False
        if len(client_data["hour"]) >= self.requests_per_hour:
            return False
        
        # Record request
        client_data["minute"].append(current_time)
        client_data["hour"].append(current_time)
        
        return True