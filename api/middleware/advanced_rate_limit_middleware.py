"""
Advanced Rate Limiting Middleware
Integrates with the rate limiting service to provide comprehensive rate limiting
"""

import time
import logging
from typing import Optional, Dict, Any
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from services.rate_limiting_service import (
    rate_limiting_service, 
    RateLimitScope,
    RateLimitResult
)
from services.audit_logging_service import audit_service, AuditEventType

logger = logging.getLogger(__name__)


class AdvancedRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Advanced rate limiting middleware with multiple algorithms and scopes
    """
    
    def __init__(
        self,
        app: ASGIApp,
        enabled: bool = True,
        skip_paths: Optional[list] = None,
        enforce_global_limits: bool = True,
        enforce_user_limits: bool = True,
        enforce_ip_limits: bool = True,
        enforce_endpoint_limits: bool = True
    ):
        super().__init__(app)
        self.enabled = enabled
        self.skip_paths = skip_paths or [
            "/health",
            "/metrics", 
            "/docs",
            "/openapi.json",
            "/redoc",
            "/favicon.ico"
        ]
        self.enforce_global_limits = enforce_global_limits
        self.enforce_user_limits = enforce_user_limits
        self.enforce_ip_limits = enforce_ip_limits
        self.enforce_endpoint_limits = enforce_endpoint_limits
        
    async def dispatch(self, request: Request, call_next):
        """Process request through rate limiting"""
        
        if not self.enabled:
            return await call_next(request)
        
        # Skip certain paths
        if any(request.url.path.startswith(skip_path) for skip_path in self.skip_paths):
            return await call_next(request)
        
        # Extract identifiers
        user_id = await self._extract_user_id(request)
        ip_address = self._extract_ip_address(request)
        api_key = await self._extract_api_key(request)
        endpoint = request.url.path
        method = request.method
        
        # Track rate limit checks for audit
        rate_limit_checks = []
        
        try:
            # 1. Global rate limiting (if enabled)
            if self.enforce_global_limits:
                global_result = await rate_limiting_service.check_rate_limit(
                    identifier="global",
                    scope=RateLimitScope.GLOBAL
                )
                rate_limit_checks.append(("global", global_result))
                
                if not global_result.allowed:
                    return await self._create_rate_limit_response(
                        global_result, "Global rate limit exceeded"
                    )
            
            # 2. IP-based rate limiting (if enabled)
            if self.enforce_ip_limits and ip_address:
                ip_result = await rate_limiting_service.check_rate_limit(
                    identifier=ip_address,
                    scope=RateLimitScope.IP
                )
                rate_limit_checks.append(("ip", ip_result))
                
                if not ip_result.allowed:
                    # Log potential abuse
                    audit_service.log_event(
                        event_type=AuditEventType.SECURITY_ALERT,
                        action=f"IP rate limit exceeded",
                        ip_address=ip_address,
                        resource=endpoint,
                        details={
                            "remaining": ip_result.remaining,
                            "reset_time": ip_result.reset_time,
                            "method": method
                        }
                    )
                    
                    return await self._create_rate_limit_response(
                        ip_result, f"IP rate limit exceeded for {ip_address}"
                    )
            
            # 3. API Key rate limiting (if API key present)
            if api_key:
                api_key_result = await rate_limiting_service.check_rate_limit(
                    identifier=api_key,
                    scope=RateLimitScope.API_KEY
                )
                rate_limit_checks.append(("api_key", api_key_result))
                
                if not api_key_result.allowed:
                    audit_service.log_event(
                        event_type=AuditEventType.API_KEY_RATE_LIMIT,
                        action=f"API key rate limit exceeded",
                        api_key=api_key[:8] + "...",  # Truncate for security
                        resource=endpoint,
                        details={
                            "remaining": api_key_result.remaining,
                            "reset_time": api_key_result.reset_time
                        }
                    )
                    
                    return await self._create_rate_limit_response(
                        api_key_result, "API key rate limit exceeded"
                    )
            
            # 4. User-based rate limiting (if user authenticated)
            elif user_id and self.enforce_user_limits:
                user_result = await rate_limiting_service.check_rate_limit(
                    identifier=str(user_id),
                    scope=RateLimitScope.USER
                )
                rate_limit_checks.append(("user", user_result))
                
                if not user_result.allowed:
                    audit_service.log_event(
                        event_type=AuditEventType.USER_RATE_LIMIT,
                        action=f"User rate limit exceeded",
                        user_id=user_id,
                        resource=endpoint,
                        details={
                            "remaining": user_result.remaining,
                            "reset_time": user_result.reset_time
                        }
                    )
                    
                    return await self._create_rate_limit_response(
                        user_result, "User rate limit exceeded"
                    )
            
            # 5. Endpoint-specific rate limiting (if enabled)
            if self.enforce_endpoint_limits:
                # Use most specific identifier available
                endpoint_identifier = api_key or (str(user_id) if user_id else ip_address) or "anonymous"
                
                endpoint_result = await rate_limiting_service.check_rate_limit(
                    identifier=endpoint_identifier,
                    scope=RateLimitScope.ENDPOINT,
                    endpoint=endpoint
                )
                rate_limit_checks.append(("endpoint", endpoint_result))
                
                if not endpoint_result.allowed:
                    audit_service.log_event(
                        event_type=AuditEventType.ENDPOINT_RATE_LIMIT,
                        action=f"Endpoint rate limit exceeded",
                        user_id=user_id,
                        api_key=api_key[:8] + "..." if api_key else None,
                        ip_address=ip_address,
                        resource=endpoint,
                        details={
                            "remaining": endpoint_result.remaining,
                            "reset_time": endpoint_result.reset_time,
                            "method": method
                        }
                    )
                    
                    return await self._create_rate_limit_response(
                        endpoint_result, f"Endpoint rate limit exceeded for {endpoint}"
                    )
            
            # All rate limits passed - proceed with request
            start_time = time.time()
            response = await call_next(request)
            end_time = time.time()
            
            # Add rate limit headers to response
            await self._add_rate_limit_headers(response, rate_limit_checks)
            
            # Log successful request with rate limit info
            audit_service.log_event(
                event_type=AuditEventType.API_REQUEST,
                action=f"{method} {endpoint}",
                user_id=user_id,
                api_key=api_key[:8] + "..." if api_key else None,
                ip_address=ip_address,
                resource=endpoint,
                result="success",
                details={
                    "response_time": end_time - start_time,
                    "status_code": response.status_code,
                    "rate_limit_checks": len(rate_limit_checks)
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limiting middleware error: {e}", exc_info=True)
            
            # Log the error but don't block the request
            audit_service.log_event(
                event_type=AuditEventType.SYSTEM_ERROR,
                action="Rate limiting middleware error",
                error_message=str(e),
                resource=endpoint,
                details={"user_id": user_id, "ip_address": ip_address}
            )
            
            # Continue with request if rate limiting fails
            return await call_next(request)
    
    async def _extract_user_id(self, request: Request) -> Optional[int]:
        """Extract user ID from request"""
        try:
            # Check if user is set by auth middleware
            if hasattr(request.state, 'user') and request.state.user:
                return request.state.user.id
            
            # Try to extract from JWT token
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]
                # You would decode JWT here and extract user_id
                # For now, return None to use IP-based limiting
                return None
            
        except Exception as e:
            logger.debug(f"Could not extract user ID: {e}")
        
        return None
    
    def _extract_ip_address(self, request: Request) -> str:
        """Extract client IP address from request"""
        
        # Check common proxy headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP if multiple are present
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
    
    async def _extract_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from request"""
        try:
            # Check for API key in header
            api_key = request.headers.get("X-API-Key")
            if api_key:
                return api_key
            
            # Check for API key in query params
            api_key = request.query_params.get("api_key")
            if api_key:
                return api_key
            
        except Exception as e:
            logger.debug(f"Could not extract API key: {e}")
        
        return None
    
    async def _create_rate_limit_response(
        self, 
        rate_limit_result: RateLimitResult, 
        message: str
    ) -> JSONResponse:
        """Create standardized rate limit response"""
        
        response_data = {
            "error": "RATE_LIMIT_EXCEEDED",
            "message": message,
            "details": {
                "remaining": rate_limit_result.remaining,
                "reset_time": rate_limit_result.reset_time,
                "retry_after": rate_limit_result.retry_after
            }
        }
        
        headers = rate_limit_result.headers or {}
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=response_data,
            headers=headers
        )
    
    async def _add_rate_limit_headers(
        self, 
        response: Response, 
        rate_limit_checks: list
    ):
        """Add rate limit headers to successful responses"""
        try:
            # Add headers from the most restrictive rate limit check
            most_restrictive = None
            min_remaining = float('inf')
            
            for check_type, result in rate_limit_checks:
                if result.remaining < min_remaining:
                    min_remaining = result.remaining
                    most_restrictive = result
            
            if most_restrictive and most_restrictive.headers:
                for header, value in most_restrictive.headers.items():
                    response.headers[header] = value
                    
        except Exception as e:
            logger.debug(f"Could not add rate limit headers: {e}")


def create_advanced_rate_limit_middleware(
    enabled: bool = True,
    **kwargs
) -> AdvancedRateLimitMiddleware:
    """Factory function to create advanced rate limiting middleware"""
    
    return AdvancedRateLimitMiddleware(
        app=None,  # Will be set by FastAPI
        enabled=enabled,
        **kwargs
    )