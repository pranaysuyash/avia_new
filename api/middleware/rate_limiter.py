"""
Rate limiting middleware for API endpoints
Implements token bucket algorithm with Redis support for distributed rate limiting
"""

import time
import json
import os
from typing import Dict, Optional, Tuple, Union
from datetime import datetime, timedelta
from collections import defaultdict
import redis
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class RateLimitExceeded(HTTPException):
    """Custom exception for rate limit exceeded"""
    def __init__(self, retry_after: int, message: str = "Rate limit exceeded"):
        super().__init__(
            status_code=429,
            detail={
                "error": message,
                "retry_after": retry_after
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": "0",
                "X-RateLimit-Remaining": "0"
            }
        )


class TokenBucket:
    """Token bucket implementation for rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float, refill_period: int = 1):
        """
        Initialize token bucket
        
        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens added per refill period
            refill_period: Period in seconds for refill
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.refill_period = refill_period
        self.tokens = capacity
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> Tuple[bool, float]:
        """
        Try to consume tokens
        
        Returns:
            Tuple of (success, tokens_remaining)
        """
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True, self.tokens
        
        return False, self.tokens
    
    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        
        if elapsed >= self.refill_period:
            tokens_to_add = (elapsed / self.refill_period) * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now
    
    def time_until_refill(self) -> int:
        """Calculate seconds until next token is available"""
        if self.tokens > 0:
            return 0
        
        time_since_refill = time.time() - self.last_refill
        time_until_next = self.refill_period - time_since_refill
        
        return max(1, int(time_until_next))


class RateLimiter:
    """Rate limiter with multiple strategies"""
    
    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        default_limit: int = 100,
        default_window: int = 3600,
        use_redis: bool = True
    ):
        """
        Initialize rate limiter
        
        Args:
            redis_client: Redis client for distributed rate limiting
            default_limit: Default request limit
            default_window: Default window in seconds
            use_redis: Whether to use Redis (if False, use in-memory)
        """
        self.redis_client = redis_client
        self.default_limit = default_limit
        self.default_window = default_window
        self.use_redis = use_redis and redis_client is not None
        
        # In-memory storage for local rate limiting
        self.local_buckets: Dict[str, TokenBucket] = {}
        self.local_counters: Dict[str, Dict[str, int]] = defaultdict(dict)
        
        # Check if we're in development mode
        is_development = os.getenv("ENVIRONMENT", "development") == "development"
        
        # Rate limit configurations by endpoint
        if is_development:
            # Very lenient limits for development
            self.endpoint_limits = {
                # High frequency endpoints
                "/api/health": {"limit": 10000, "window": 60},
                "/api/monitoring/metrics": {"limit": 1000, "window": 60},
                
                # Authentication endpoints - much more lenient for dev
                "/api/auth/login": {"limit": 100, "window": 60},  # 100 per minute
                "/api/auth/register": {"limit": 50, "window": 60},  # 50 per minute 
                "/api/auth/refresh": {"limit": 100, "window": 60},
                
                # Transcription endpoints
                "/api/transcription/upload": {"limit": 500, "window": 3600},  
                "/api/transcription/process": {"limit": 200, "window": 3600},  
                
                # Search and analytics
                "/api/search": {"limit": 1000, "window": 300},  
                "/api/analytics": {"limit": 500, "window": 300},
                
                # Export endpoints
                "/api/export": {"limit": 300, "window": 3600},  
                
                # WebSocket endpoints
                "/ws": {"limit": 100, "window": 60},  
            }
        else:
            # Production limits
            self.endpoint_limits = {
                # High frequency endpoints
                "/api/health": {"limit": 1000, "window": 60},
                "/api/monitoring/metrics": {"limit": 100, "window": 60},
                
                # Authentication endpoints
                "/api/auth/login": {"limit": 10, "window": 300},  # 10 per 5 minutes
                "/api/auth/register": {"limit": 5, "window": 3600},  # 5 per hour
                "/api/auth/refresh": {"limit": 20, "window": 300},
                
                # Transcription endpoints
                "/api/transcription/upload": {"limit": 50, "window": 3600},  # 50 per hour
                "/api/transcription/process": {"limit": 20, "window": 3600},  # 20 per hour
                
                # Search and analytics
                "/api/search": {"limit": 100, "window": 300},  # 100 per 5 minutes
                "/api/analytics": {"limit": 50, "window": 300},
                
                # Export endpoints
                "/api/export": {"limit": 30, "window": 3600},  # 30 per hour
                
                # WebSocket endpoints
                "/ws": {"limit": 10, "window": 60},  # 10 connections per minute
            }
        
        # User tier limits (can be overridden per user)
        self.tier_limits = {
            "free": {"limit": 100, "window": 3600},
            "basic": {"limit": 500, "window": 3600},
            "pro": {"limit": 2000, "window": 3600},
            "enterprise": {"limit": 10000, "window": 3600}
        }
    
    def _get_redis_key(self, identifier: str, endpoint: str = "") -> str:
        """Generate Redis key for rate limiting"""
        if endpoint:
            return f"rate_limit:{identifier}:{endpoint}"
        return f"rate_limit:{identifier}"
    
    def _get_limit_config(self, endpoint: str, user_tier: Optional[str] = None) -> Dict[str, int]:
        """Get rate limit configuration for endpoint"""
        # Check endpoint-specific limits first
        if endpoint in self.endpoint_limits:
            return self.endpoint_limits[endpoint]
        
        # Check user tier limits
        if user_tier and user_tier in self.tier_limits:
            return self.tier_limits[user_tier]
        
        # Default limits
        return {"limit": self.default_limit, "window": self.default_window}
    
    async def check_rate_limit(
        self,
        identifier: str,
        endpoint: str = "",
        user_tier: Optional[str] = None,
        cost: int = 1
    ) -> Tuple[bool, Dict[str, Union[int, str]]]:
        """
        Check if request is within rate limit
        
        Args:
            identifier: Unique identifier (IP, user ID, API key)
            endpoint: API endpoint path
            user_tier: User subscription tier
            cost: Cost of the request (default 1)
            
        Returns:
            Tuple of (allowed, rate_limit_info)
        """
        config = self._get_limit_config(endpoint, user_tier)
        limit = config["limit"]
        window = config["window"]
        
        if self.use_redis:
            return await self._check_redis_rate_limit(identifier, endpoint, limit, window, cost)
        else:
            return self._check_local_rate_limit(identifier, endpoint, limit, window, cost)
    
    async def _check_redis_rate_limit(
        self,
        identifier: str,
        endpoint: str,
        limit: int,
        window: int,
        cost: int
    ) -> Tuple[bool, Dict[str, Union[int, str]]]:
        """Check rate limit using Redis sliding window"""
        key = self._get_redis_key(identifier, endpoint)
        now = time.time()
        window_start = now - window
        
        try:
            # Remove old entries
            self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count current requests in window
            current_count = self.redis_client.zcard(key)
            
            if current_count + cost > limit:
                # Get oldest request timestamp to calculate retry after
                oldest = self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest:
                    oldest_timestamp = oldest[0][1]
                    retry_after = int(oldest_timestamp + window - now) + 1
                else:
                    retry_after = window
                
                return False, {
                    "limit": limit,
                    "remaining": max(0, limit - current_count),
                    "reset": int(now + retry_after),
                    "retry_after": retry_after
                }
            
            # Add current request
            for _ in range(cost):
                self.redis_client.zadd(key, {f"{now}:{id(now)}": now})
            
            # Set expiry
            self.redis_client.expire(key, window)
            
            return True, {
                "limit": limit,
                "remaining": max(0, limit - current_count - cost),
                "reset": int(now + window)
            }
            
        except Exception as e:
            logger.error(f"Redis rate limit error: {e}")
            # Fallback to local rate limiting
            return self._check_local_rate_limit(identifier, endpoint, limit, window, cost)
    
    def _check_local_rate_limit(
        self,
        identifier: str,
        endpoint: str,
        limit: int,
        window: int,
        cost: int
    ) -> Tuple[bool, Dict[str, Union[int, str]]]:
        """Check rate limit using local token bucket"""
        key = f"{identifier}:{endpoint}" if endpoint else identifier
        
        # Create bucket if doesn't exist
        if key not in self.local_buckets:
            # Calculate refill rate: tokens per second
            refill_rate = limit / window
            self.local_buckets[key] = TokenBucket(limit, refill_rate)
        
        bucket = self.local_buckets[key]
        allowed, remaining = bucket.consume(cost)
        
        if not allowed:
            retry_after = bucket.time_until_refill()
            return False, {
                "limit": limit,
                "remaining": int(remaining),
                "reset": int(time.time() + retry_after),
                "retry_after": retry_after
            }
        
        return True, {
            "limit": limit,
            "remaining": int(remaining),
            "reset": int(time.time() + window)
        }
    
    def reset_limit(self, identifier: str, endpoint: str = ""):
        """Reset rate limit for identifier"""
        if self.use_redis:
            key = self._get_redis_key(identifier, endpoint)
            self.redis_client.delete(key)
        else:
            key = f"{identifier}:{endpoint}" if endpoint else identifier
            if key in self.local_buckets:
                del self.local_buckets[key]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""
    
    def __init__(
        self,
        app: ASGIApp,
        rate_limiter: RateLimiter,
        identifier_extractor: Optional[callable] = None,
        skip_paths: Optional[list] = None,
        cost_calculator: Optional[callable] = None
    ):
        """
        Initialize rate limit middleware
        
        Args:
            app: FastAPI application
            rate_limiter: RateLimiter instance
            identifier_extractor: Function to extract identifier from request
            skip_paths: Paths to skip rate limiting
            cost_calculator: Function to calculate request cost
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.identifier_extractor = identifier_extractor or self._default_identifier_extractor
        self.skip_paths = skip_paths or ["/docs", "/redoc", "/openapi.json"]
        self.cost_calculator = cost_calculator or self._default_cost_calculator
    
    async def dispatch(self, request: Request, call_next):
        """Process request through rate limiter"""
        # Skip rate limiting for certain paths
        if any(request.url.path.startswith(path) for path in self.skip_paths):
            return await call_next(request)
        
        # Extract identifier
        identifier = await self.identifier_extractor(request)
        if not identifier:
            return await call_next(request)
        
        # Calculate request cost
        cost = await self.cost_calculator(request)
        
        # Get user tier if available
        user_tier = None
        if hasattr(request.state, "user") and request.state.user:
            user_tier = getattr(request.state.user, "tier", "free")
        
        # Check rate limit
        allowed, rate_info = await self.rate_limiter.check_rate_limit(
            identifier=identifier,
            endpoint=request.url.path,
            user_tier=user_tier,
            cost=cost
        )
        
        # Add rate limit headers to response
        response = await call_next(request) if allowed else None
        
        if allowed:
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])
            
            return response
        else:
            # Rate limit exceeded
            retry_after = rate_info["retry_after"]
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": retry_after,
                    "limit": rate_info["limit"],
                    "reset": rate_info["reset"]
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(rate_info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(rate_info["reset"])
                }
            )
    
    async def _default_identifier_extractor(self, request: Request) -> Optional[str]:
        """Extract identifier from request (IP by default)"""
        # Try to get authenticated user ID first
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.id}"
        
        # Try to get API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key[:8]}"  # Use prefix for privacy
        
        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get the first IP in the chain
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        return f"ip:{client_ip}"
    
    async def _default_cost_calculator(self, request: Request) -> int:
        """Calculate request cost (can be customized per endpoint)"""
        # Higher cost for resource-intensive operations
        if request.url.path.startswith("/api/transcription/process"):
            return 5
        elif request.url.path.startswith("/api/export"):
            return 3
        elif request.method == "POST":
            return 2
        
        return 1


def create_rate_limiter(redis_url: Optional[str] = None) -> RateLimiter:
    """Create rate limiter instance with optional Redis support"""
    redis_client = None
    
    if redis_url:
        try:
            redis_client = redis.from_url(redis_url, decode_responses=True)
            redis_client.ping()
            logger.info("Connected to Redis for distributed rate limiting")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Using local rate limiting.")
            redis_client = None
    
    return RateLimiter(redis_client=redis_client)


# Decorator for rate limiting specific endpoints
def rate_limit(limit: int = 100, window: int = 3600, key_func: Optional[callable] = None):
    """
    Decorator for rate limiting specific endpoints
    
    Args:
        limit: Number of requests allowed
        window: Time window in seconds
        key_func: Function to extract rate limit key from request
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            # Get rate limiter from app state
            rate_limiter = getattr(request.app.state, "rate_limiter", None)
            if not rate_limiter:
                return await func(request, *args, **kwargs)
            
            # Extract identifier
            if key_func:
                identifier = await key_func(request)
            else:
                identifier = request.client.host if request.client else "unknown"
            
            # Check rate limit
            allowed, rate_info = await rate_limiter.check_rate_limit(
                identifier=identifier,
                endpoint=request.url.path,
                cost=1
            )
            
            if not allowed:
                raise RateLimitExceeded(
                    retry_after=rate_info["retry_after"],
                    message=f"Rate limit exceeded. Please retry after {rate_info['retry_after']} seconds"
                )
            
            # Add rate limit info to response
            response = await func(request, *args, **kwargs)
            if hasattr(response, "headers"):
                response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
                response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
                response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])
            
            return response
        
        return wrapper
    return decorator