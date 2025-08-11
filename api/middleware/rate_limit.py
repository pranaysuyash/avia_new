"""
Rate limiting middleware for FastAPI
Implements token bucket algorithm with Redis backend
"""

import time
import hashlib
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from redis import Redis
import json
from datetime import datetime, timedelta

class RateLimiter:
    """
    Token bucket rate limiter with Redis backend
    """
    
    def __init__(
        self,
        redis_client: Redis,
        default_limit: int = 100,
        default_window: int = 3600,  # 1 hour in seconds
        prefix: str = "rate_limit"
    ):
        self.redis = redis_client
        self.default_limit = default_limit
        self.default_window = default_window
        self.prefix = prefix
        
        # Endpoint-specific limits
        self.endpoint_limits = {
            "/api/auth/login": {"limit": 5, "window": 300},  # 5 per 5 minutes
            "/api/auth/register": {"limit": 3, "window": 3600},  # 3 per hour
            "/api/transcriptions/upload": {"limit": 10, "window": 3600},  # 10 per hour
            "/api/transcriptions": {"limit": 100, "window": 3600},  # 100 per hour
            "/api/search": {"limit": 30, "window": 60},  # 30 per minute
        }
        
        # User tier limits (requests per hour)
        self.tier_limits = {
            "free": 100,
            "basic": 500,
            "premium": 2000,
            "enterprise": 10000
        }
    
    def get_identifier(self, request: Request) -> str:
        """
        Get unique identifier for rate limiting
        Uses authenticated user ID if available, otherwise IP address
        """
        # Check for authenticated user
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.id}"
        
        # Fallback to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        return f"ip:{ip}"
    
    def get_limits(self, request: Request) -> tuple[int, int]:
        """
        Get rate limits for the request
        Returns (limit, window) tuple
        """
        # Check endpoint-specific limits
        path = request.url.path
        for endpoint, limits in self.endpoint_limits.items():
            if path.startswith(endpoint):
                return limits["limit"], limits["window"]
        
        # Check user tier limits
        if hasattr(request.state, "user") and request.state.user:
            user = request.state.user
            tier = getattr(user, "tier", "free")
            if tier in self.tier_limits:
                return self.tier_limits[tier], 3600  # Per hour
        
        # Default limits
        return self.default_limit, self.default_window
    
    def check_rate_limit(self, request: Request) -> Dict[str, Any]:
        """
        Check if request exceeds rate limit
        Returns dict with limit info
        """
        identifier = self.get_identifier(request)
        limit, window = self.get_limits(request)
        
        # Create Redis key
        key = f"{self.prefix}:{identifier}:{request.url.path}"
        
        # Get current timestamp
        now = time.time()
        
        # Clean old entries and count requests
        pipeline = self.redis.pipeline()
        pipeline.zremrangebyscore(key, 0, now - window)
        pipeline.zcard(key)
        pipeline.zadd(key, {str(now): now})
        pipeline.expire(key, window)
        results = pipeline.execute()
        
        request_count = results[1]
        
        # Calculate remaining requests
        remaining = max(0, limit - request_count)
        
        # Calculate reset time
        if request_count >= limit:
            oldest_request = self.redis.zrange(key, 0, 0, withscores=True)
            if oldest_request:
                reset_time = int(oldest_request[0][1] + window)
            else:
                reset_time = int(now + window)
        else:
            reset_time = int(now + window)
        
        return {
            "limit": limit,
            "remaining": remaining,
            "reset": reset_time,
            "retry_after": reset_time - int(now) if request_count >= limit else None
        }
    
    async def __call__(self, request: Request, call_next):
        """
        Middleware handler
        """
        # Skip rate limiting for certain paths
        skip_paths = ["/docs", "/redoc", "/openapi.json", "/api/health"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)
        
        try:
            # Check rate limit
            rate_info = self.check_rate_limit(request)
            
            # Add rate limit headers to response
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])
            
            # If rate limit exceeded
            if rate_info["remaining"] == 0 and rate_info["retry_after"]:
                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Rate limit exceeded",
                        "retry_after": rate_info["retry_after"]
                    },
                    headers={
                        "Retry-After": str(rate_info["retry_after"]),
                        "X-RateLimit-Limit": str(rate_info["limit"]),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(rate_info["reset"])
                    }
                )
            
            return response
            
        except Exception as e:
            # Log error but don't block request
            print(f"Rate limiting error: {e}")
            return await call_next(request)


class DistributedRateLimiter(RateLimiter):
    """
    Distributed rate limiter using Redis with sliding window algorithm
    """
    
    def check_rate_limit(self, request: Request) -> Dict[str, Any]:
        """
        Check rate limit using sliding window counter
        More accurate than fixed window
        """
        identifier = self.get_identifier(request)
        limit, window = self.get_limits(request)
        
        # Create Redis keys for current and previous windows
        now = time.time()
        current_window = int(now // window)
        previous_window = current_window - 1
        
        current_key = f"{self.prefix}:{identifier}:{request.url.path}:{current_window}"
        previous_key = f"{self.prefix}:{identifier}:{request.url.path}:{previous_window}"
        
        # Get counts from both windows
        pipeline = self.redis.pipeline()
        pipeline.get(current_key)
        pipeline.get(previous_key)
        results = pipeline.execute()
        
        current_count = int(results[0] or 0)
        previous_count = int(results[1] or 0)
        
        # Calculate weighted count
        window_progress = (now % window) / window
        weighted_count = previous_count * (1 - window_progress) + current_count
        
        # Check if limit exceeded
        if weighted_count >= limit:
            remaining = 0
            retry_after = int(window - (now % window))
        else:
            remaining = int(limit - weighted_count)
            retry_after = None
            
            # Increment counter for current window
            pipeline = self.redis.pipeline()
            pipeline.incr(current_key)
            pipeline.expire(current_key, window * 2)
            pipeline.execute()
        
        return {
            "limit": limit,
            "remaining": remaining,
            "reset": int(now + window - (now % window)),
            "retry_after": retry_after
        }


class IPBasedRateLimiter:
    """
    Simple IP-based rate limiter for public endpoints
    """
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = {}
    
    def is_allowed(self, ip: str) -> bool:
        """
        Check if IP is allowed to make request
        """
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        if ip in self.requests:
            self.requests[ip] = [
                timestamp for timestamp in self.requests[ip]
                if timestamp > minute_ago
            ]
        else:
            self.requests[ip] = []
        
        # Check limit
        if len(self.requests[ip]) >= self.requests_per_minute:
            return False
        
        # Add current request
        self.requests[ip].append(now)
        return True


def create_rate_limiter(redis_url: Optional[str] = None) -> RateLimiter:
    """
    Factory function to create rate limiter
    """
    if redis_url:
        redis_client = Redis.from_url(redis_url)
        return DistributedRateLimiter(redis_client)
    else:
        # Fallback to in-memory rate limiting
        return IPBasedRateLimiter()