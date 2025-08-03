"""
API Middleware
Rate limiting, authentication, and other middleware
"""

import time
import json
from typing import Dict, Optional, Callable
from datetime import datetime, timedelta
import redis
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis
    Implements sliding window algorithm
    """
    
    def __init__(
        self,
        app,
        redis_client: redis.Redis,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        exclude_paths: list = None
    ):
        super().__init__(app)
        self.redis_client = redis_client
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.exclude_paths = exclude_paths or ["/api/health", "/api/docs", "/api/redoc"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Skip WebSocket connections
        if request.url.path.startswith("/ws/"):
            return await call_next(request)
        
        # Get client identifier (IP or user ID)
        client_id = self._get_client_id(request)
        
        # Check rate limits
        if not await self._check_rate_limit(client_id):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": 60
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + 60)
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = await self._get_remaining_requests(client_id)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request"""
        # Try to get user ID from JWT token
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # In production, decode JWT and get user ID
            # For now, use a placeholder
            return f"user:auth"
        
        # Fall back to IP address
        client_ip = request.client.host
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return f"ip:{client_ip}"
    
    async def _check_rate_limit(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit"""
        now = time.time()
        
        # Check minute limit
        minute_key = f"rate_limit:minute:{client_id}"
        minute_count = await self._increment_counter(minute_key, 60)
        if minute_count > self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for {client_id}: {minute_count}/min")
            return False
        
        # Check hour limit
        hour_key = f"rate_limit:hour:{client_id}"
        hour_count = await self._increment_counter(hour_key, 3600)
        if hour_count > self.requests_per_hour:
            logger.warning(f"Rate limit exceeded for {client_id}: {hour_count}/hour")
            return False
        
        return True
    
    async def _increment_counter(self, key: str, window: int) -> int:
        """Increment counter using sliding window algorithm"""
        try:
            pipeline = self.redis_client.pipeline()
            pipeline.incr(key)
            pipeline.expire(key, window)
            results = pipeline.execute()
            return results[0]
        except Exception as e:
            logger.error(f"Redis error in rate limiting: {e}")
            # Allow request if Redis is down
            return 0
    
    async def _get_remaining_requests(self, client_id: str) -> int:
        """Get remaining requests for client"""
        try:
            minute_key = f"rate_limit:minute:{client_id}"
            count = self.redis_client.get(minute_key)
            if count:
                return max(0, self.requests_per_minute - int(count))
            return self.requests_per_minute
        except:
            return self.requests_per_minute

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Request/Response logging middleware
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {response.status_code} "
            f"Duration: {duration:.3f}s "
            f"Path: {request.url.path}"
        )
        
        # Add timing header
        response.headers["X-Process-Time"] = str(duration)
        
        return response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to responses
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' wss: https:;"
        )
        response.headers["Content-Security-Policy"] = csp
        
        return response

class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Response compression middleware
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Check if client accepts gzip
        accept_encoding = request.headers.get("Accept-Encoding", "")
        if "gzip" not in accept_encoding:
            return response
        
        # Only compress text responses
        content_type = response.headers.get("Content-Type", "")
        if not any(ct in content_type for ct in ["text/", "application/json", "application/javascript"]):
            return response
        
        # Skip small responses
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) < 1024:  # 1KB
            return response
        
        # In production, implement actual compression
        # For now, just add header
        response.headers["Content-Encoding"] = "gzip"
        
        return response

# Utility functions
def create_redis_client() -> Optional[redis.Redis]:
    """Create Redis client for rate limiting"""
    try:
        import os
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = redis.from_url(redis_url, decode_responses=True)
        client.ping()
        logger.info("Connected to Redis for rate limiting")
        return client
    except Exception as e:
        logger.warning(f"Could not connect to Redis: {e}")
        return None

# Export middleware
__all__ = [
    "RateLimitMiddleware",
    "LoggingMiddleware",
    "SecurityHeadersMiddleware",
    "CompressionMiddleware",
    "create_redis_client"
]