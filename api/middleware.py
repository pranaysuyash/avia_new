"""
Custom middleware for the API
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
from typing import Dict, Callable
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients: Dict[str, list] = defaultdict(list)
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_old_requests())
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip rate limiting for docs and health endpoints
        if request.url.path in ["/api/docs", "/api/redoc", "/api/openapi.json", "/api/v1/health"]:
            return await call_next(request)
        
        # Get client identifier (IP or user ID from token)
        client_id = self._get_client_id(request)
        
        # Check rate limit
        now = time.time()
        
        # Remove old requests
        self.clients[client_id] = [
            req_time for req_time in self.clients[client_id]
            if req_time > now - self.period
        ]
        
        # Check if limit exceeded
        if len(self.clients[client_id]) >= self.calls:
            logger.warning(f"Rate limit exceeded for client {client_id}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded. Max {self.calls} requests per {self.period} seconds.",
                    "retry_after": self.period
                },
                headers={
                    "X-RateLimit-Limit": str(self.calls),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + self.period)),
                    "Retry-After": str(self.period)
                }
            )
        
        # Add current request
        self.clients[client_id].append(now)
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(self.calls - len(self.clients[client_id]))
        response.headers["X-RateLimit-Reset"] = str(int(now + self.period))
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request"""
        # Try to get from Authorization header (user ID)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # In production, decode JWT to get user ID
            return f"user_{auth_header}"
        
        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        return request.client.host if request.client else "unknown"
    
    async def _cleanup_old_requests(self):
        """Periodically clean up old request records"""
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            now = time.time()
            
            for client_id in list(self.clients.keys()):
                self.clients[client_id] = [
                    req_time for req_time in self.clients[client_id]
                    if req_time > now - self.period
                ]
                
                # Remove client if no recent requests
                if not self.clients[client_id]:
                    del self.clients[client_id]


class LoggingMiddleware(BaseHTTPMiddleware):
    """Request/response logging middleware"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip logging for health checks
        if request.url.path == "/api/v1/health":
            return await call_next(request)
        
        # Start timer
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response: {request.method} {request.url.path} "
                f"- Status: {response.status_code} - Duration: {duration:.3f}s"
            )
            
            # Add timing header
            response.headers["X-Process-Time"] = f"{duration:.3f}"
            
            return response
            
        except Exception as e:
            # Log error
            duration = time.time() - start_time
            logger.error(
                f"Error: {request.method} {request.url.path} "
                f"- Exception: {type(e).__name__} - Duration: {duration:.3f}s",
                exc_info=True
            )
            raise


class CompressionMiddleware(BaseHTTPMiddleware):
    """Response compression middleware"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)
        
        # Check if client accepts compression
        accept_encoding = request.headers.get("Accept-Encoding", "")
        
        if "gzip" in accept_encoding and hasattr(response, "body"):
            # In production, implement gzip compression here
            response.headers["Content-Encoding"] = "gzip"
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy (adjust based on needs)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' wss: https:;"
        )
        
        return response