#!/usr/bin/env python3
"""
API Authentication Middleware
Handles API key authentication for public API endpoints
"""

import logging
import time
from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from database.connection import get_db
from services.api_key_service import APIKeyService
from database.api_models import APIKey

logger = logging.getLogger(__name__)

class APIKeyAuth(HTTPBearer):
    """API Key authentication scheme"""
    
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request) -> Optional[str]:
        """Extract API key from request"""
        # Try Authorization header first
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if credentials and credentials.scheme == "Bearer":
            return credentials.credentials
        
        # Try X-API-Key header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return api_key
        
        # Try query parameter (not recommended for production)
        api_key = request.query_params.get("api_key")
        if api_key:
            return api_key
        
        if self.auto_error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return None

class APIAuthMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication"""
    
    def __init__(self, app, public_paths: Optional[set] = None):
        super().__init__(app)
        self.public_paths = public_paths or {
            '/api/v1/docs',
            '/api/v1/openapi.json',
            '/api/v1/health',
            '/api/v1/auth/register',
            '/api/v1/developers/docs'
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """Process request with API authentication"""
        # Skip authentication for public paths
        if any(request.url.path.startswith(path) for path in self.public_paths):
            return await call_next(request)
        
        # Skip if not a public API endpoint
        if not request.url.path.startswith('/api/v1/'):
            return await call_next(request)
        
        # Check if regular auth is present (JWT)
        if request.headers.get("Authorization", "").startswith("Bearer ey"):
            # This is a JWT token, let regular auth handle it
            return await call_next(request)
        
        # Try to authenticate with API key
        start_time = time.time()
        api_key_auth = APIKeyAuth(auto_error=False)
        
        try:
            api_key_str = await api_key_auth(request)
            
            if not api_key_str:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "unauthorized",
                        "message": "API key required"
                    },
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Authenticate the API key
            db = next(get_db())
            api_key_service = APIKeyService(db)
            
            api_key = api_key_service.authenticate_api_key(api_key_str)
            
            if not api_key:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "invalid_api_key",
                        "message": "Invalid or expired API key"
                    }
                )
            
            # Check IP restrictions
            client_ip = request.client.host if request.client else None
            if api_key.allowed_ips and client_ip not in api_key.allowed_ips:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "error": "ip_not_allowed",
                        "message": "Request from this IP address is not allowed"
                    }
                )
            
            # Check rate limits
            allowed, message, rate_info = api_key_service.check_rate_limit(
                api_key, client_ip
            )
            
            if not allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "rate_limit_exceeded",
                        "message": message,
                        "rate_limit": rate_info
                    },
                    headers={
                        "X-RateLimit-Limit": str(rate_info.get('limit', 0)),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time()) + rate_info.get('reset_in', 60))
                    }
                )
            
            # Check required scopes for endpoint
            required_scope = self._get_required_scope(request)
            if required_scope and not api_key.has_scope(required_scope):
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "error": "insufficient_scope",
                        "message": f"This endpoint requires '{required_scope}' scope"
                    }
                )
            
            # Add API key info to request state
            request.state.api_key = api_key
            request.state.api_key_id = api_key.id
            request.state.api_user_id = api_key.user_id
            
            # Process request
            response = await call_next(request)
            
            # Log usage
            response_time = int((time.time() - start_time) * 1000)
            
            api_key_service.log_usage(
                api_key=api_key,
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                response_time_ms=response_time,
                ip_address=client_ip,
                user_agent=request.headers.get("user-agent", ""),
                request_id=request.headers.get("x-request-id")
            )
            
            # Add rate limit headers
            if 'remaining' in rate_info:
                response.headers["X-RateLimit-Limit-Minute"] = str(api_key.rate_limit_per_minute)
                response.headers["X-RateLimit-Remaining-Minute"] = str(rate_info['remaining']['minute'])
                response.headers["X-RateLimit-Limit-Hour"] = str(api_key.rate_limit_per_hour)
                response.headers["X-RateLimit-Remaining-Hour"] = str(rate_info['remaining']['hour'])
            
            return response
            
        except Exception as e:
            logger.error(f"API auth error: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "internal_error",
                    "message": "Authentication error"
                }
            )
        
        finally:
            if 'db' in locals():
                db.close()
    
    def _get_required_scope(self, request: Request) -> Optional[str]:
        """Determine required scope for endpoint"""
        path = request.url.path
        method = request.method
        
        # Transcript endpoints
        if path.startswith('/api/v1/transcripts'):
            if method == 'GET':
                return 'transcripts:read'
            elif method in ['POST', 'PUT', 'PATCH']:
                return 'transcripts:write'
            elif method == 'DELETE':
                return 'transcripts:delete'
        
        # Analytics endpoints
        elif path.startswith('/api/v1/analytics'):
            return 'analytics:read'
        
        # Team endpoints
        elif path.startswith('/api/v1/teams'):
            if method == 'GET':
                return 'teams:read'
            else:
                return 'teams:write'
        
        # Webhook endpoints
        elif path.startswith('/api/v1/webhooks'):
            return 'webhooks:write'
        
        # Account endpoints
        elif path.startswith('/api/v1/account'):
            return 'account:read'
        
        # Default read scope
        return 'transcripts:read'

def get_current_api_key(request: Request) -> APIKey:
    """Get current API key from request"""
    if not hasattr(request.state, 'api_key'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return request.state.api_key

def require_api_scope(scope: str):
    """Decorator to require specific API scope"""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            api_key = get_current_api_key(request)
            
            if not api_key.has_scope(scope):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires '{scope}' scope"
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator