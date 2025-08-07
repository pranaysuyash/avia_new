"""
Advanced Rate Limiting Service with Token Bucket Algorithm
Provides sophisticated rate limiting with multiple algorithms and flexible configuration
"""

import time
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import redis
from api.cache.redis_cache import redis_cache

logger = logging.getLogger(__name__)


class RateLimitAlgorithm(Enum):
    """Available rate limiting algorithms"""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"


class RateLimitScope(Enum):
    """Rate limiting scope levels"""
    GLOBAL = "global"
    USER = "user"
    IP = "ip"
    API_KEY = "api_key"
    ENDPOINT = "endpoint"


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests_per_second: float
    burst_capacity: int
    window_size: int = 60  # seconds
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET
    scope: RateLimitScope = RateLimitScope.USER
    enabled: bool = True
    
    
@dataclass
class RateLimitResult:
    """Rate limit check result"""
    allowed: bool
    remaining: int
    reset_time: float
    retry_after: Optional[int] = None
    headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


class TokenBucket:
    """Token bucket implementation for rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float, redis_key: str):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.redis_key = redis_key
        
    async def consume(self, tokens: int = 1) -> bool:
        """
        Attempt to consume tokens from the bucket
        Returns True if tokens were consumed, False if rate limited
        """
        if not redis_cache.is_connected():
            # Fallback to in-memory (less accurate but functional)
            return self._consume_memory(tokens)
            
        # Redis-based distributed token bucket
        lua_script = """
        local key = KEYS[1]
        local capacity = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local requested_tokens = tonumber(ARGV[3])
        local now = tonumber(ARGV[4])
        
        -- Get current state
        local bucket_data = redis.call('HMGET', key, 'tokens', 'last_refill')
        local current_tokens = tonumber(bucket_data[1]) or capacity
        local last_refill = tonumber(bucket_data[2]) or now
        
        -- Calculate tokens to add based on time elapsed
        local time_elapsed = math.max(0, now - last_refill)
        local tokens_to_add = math.floor(time_elapsed * refill_rate)
        current_tokens = math.min(capacity, current_tokens + tokens_to_add)
        
        -- Check if we can consume the requested tokens
        if current_tokens >= requested_tokens then
            current_tokens = current_tokens - requested_tokens
            
            -- Update bucket state
            redis.call('HMSET', key, 
                'tokens', current_tokens, 
                'last_refill', now)
            redis.call('EXPIRE', key, 3600)  -- 1 hour TTL
            
            return {1, current_tokens, now}
        else
            -- Update refill time but don't consume tokens
            redis.call('HMSET', key, 
                'tokens', current_tokens, 
                'last_refill', now)
            redis.call('EXPIRE', key, 3600)
            
            return {0, current_tokens, now}
        end
        """
        
        try:
            result = await redis_cache.client.eval(
                lua_script,
                1,  # Number of keys
                self.redis_key,
                self.capacity,
                self.refill_rate,
                tokens,
                time.time()
            )
            
            allowed, remaining_tokens, timestamp = result
            return bool(allowed), int(remaining_tokens), float(timestamp)
            
        except Exception as e:
            logger.error(f"Redis token bucket error: {e}")
            return self._consume_memory(tokens)
    
    def _consume_memory(self, tokens: int = 1) -> tuple:
        """Fallback in-memory token bucket (not distributed)"""
        # This is a simplified fallback - in production you'd want proper storage
        current_time = time.time()
        
        # For demo purposes, always allow with warning
        logger.warning("Using fallback in-memory rate limiting - not distributed")
        return True, self.capacity - tokens, current_time


class SlidingWindowRateLimiter:
    """Sliding window rate limiter implementation"""
    
    def __init__(self, requests_per_window: int, window_size: int, redis_key: str):
        self.requests_per_window = requests_per_window
        self.window_size = window_size  # seconds
        self.redis_key = redis_key
    
    async def is_allowed(self) -> tuple:
        """Check if request is allowed under sliding window"""
        if not redis_cache.is_connected():
            return True, self.requests_per_window, time.time()
            
        current_time = time.time()
        window_start = current_time - self.window_size
        
        lua_script = """
        local key = KEYS[1]
        local window_start = tonumber(ARGV[1])
        local current_time = tonumber(ARGV[2])
        local max_requests = tonumber(ARGV[3])
        
        -- Remove old entries
        redis.call('ZREMRANGEBYSCORE', key, 0, window_start)
        
        -- Count current requests in window
        local current_count = redis.call('ZCARD', key)
        
        if current_count < max_requests then
            -- Add current request
            redis.call('ZADD', key, current_time, current_time)
            redis.call('EXPIRE', key, math.ceil(ARGV[4]))
            return {1, max_requests - current_count - 1, current_time}
        else
            return {0, 0, current_time}
        end
        """
        
        try:
            result = await redis_cache.client.eval(
                lua_script,
                1,
                self.redis_key,
                window_start,
                current_time,
                self.requests_per_window,
                self.window_size + 10  # TTL buffer
            )
            
            allowed, remaining, timestamp = result
            return bool(allowed), int(remaining), float(timestamp)
            
        except Exception as e:
            logger.error(f"Redis sliding window error: {e}")
            return True, self.requests_per_window, current_time


class RateLimitingService:
    """Advanced rate limiting service with multiple algorithms"""
    
    def __init__(self):
        self.default_configs = {
            RateLimitScope.GLOBAL: RateLimitConfig(
                requests_per_second=100.0,
                burst_capacity=200,
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET
            ),
            RateLimitScope.USER: RateLimitConfig(
                requests_per_second=10.0,
                burst_capacity=50,
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET
            ),
            RateLimitScope.IP: RateLimitConfig(
                requests_per_second=5.0,
                burst_capacity=20,
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW
            ),
            RateLimitScope.API_KEY: RateLimitConfig(
                requests_per_second=50.0,
                burst_capacity=100,
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET
            ),
            RateLimitScope.ENDPOINT: RateLimitConfig(
                requests_per_second=20.0,
                burst_capacity=40,
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW
            )
        }
        
        # Endpoint-specific configurations
        self.endpoint_configs = {
            "/api/v1/transcription/transcribe": RateLimitConfig(
                requests_per_second=2.0,
                burst_capacity=5,
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET
            ),
            "/api/v1/transcription/upload": RateLimitConfig(
                requests_per_second=5.0,
                burst_capacity=10,
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW
            ),
            "/api/v1/auth/login": RateLimitConfig(
                requests_per_second=0.1,  # 1 per 10 seconds
                burst_capacity=3,
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET
            ),
            "/api/v1/backup/create": RateLimitConfig(
                requests_per_second=0.05,  # 1 per 20 seconds
                burst_capacity=2,
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET
            )
        }
        
        self.active_buckets = {}
        self.active_windows = {}
    
    async def check_rate_limit(
        self,
        identifier: str,
        scope: RateLimitScope,
        endpoint: Optional[str] = None,
        custom_config: Optional[RateLimitConfig] = None
    ) -> RateLimitResult:
        """
        Check if request should be rate limited
        
        Args:
            identifier: The identifier to rate limit (user_id, IP, api_key, etc.)
            scope: The scope of rate limiting
            endpoint: Optional endpoint for endpoint-specific limits
            custom_config: Optional custom configuration
        
        Returns:
            RateLimitResult with allow/deny decision and metadata
        """
        
        # Get configuration
        config = custom_config or self._get_config(scope, endpoint)
        
        if not config.enabled:
            return RateLimitResult(
                allowed=True,
                remaining=config.burst_capacity,
                reset_time=time.time() + config.window_size
            )
        
        # Generate Redis key
        redis_key = self._generate_key(identifier, scope, endpoint)
        
        # Apply rate limiting based on algorithm
        if config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            return await self._check_token_bucket(redis_key, config)
        elif config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            return await self._check_sliding_window(redis_key, config)
        elif config.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
            return await self._check_fixed_window(redis_key, config)
        else:
            # Default to token bucket
            return await self._check_token_bucket(redis_key, config)
    
    async def _check_token_bucket(self, redis_key: str, config: RateLimitConfig) -> RateLimitResult:
        """Check rate limit using token bucket algorithm"""
        
        if redis_key not in self.active_buckets:
            self.active_buckets[redis_key] = TokenBucket(
                capacity=config.burst_capacity,
                refill_rate=config.requests_per_second,
                redis_key=redis_key
            )
        
        bucket = self.active_buckets[redis_key]
        allowed, remaining, timestamp = await bucket.consume(1)
        
        # Calculate when bucket will have tokens available
        reset_time = timestamp + (1.0 / config.requests_per_second)
        retry_after = None if allowed else int(reset_time - time.time()) + 1
        
        headers = {
            'X-RateLimit-Limit': str(config.burst_capacity),
            'X-RateLimit-Remaining': str(remaining),
            'X-RateLimit-Reset': str(int(reset_time)),
            'X-RateLimit-Algorithm': 'token-bucket'
        }
        
        if not allowed:
            headers['Retry-After'] = str(retry_after)
        
        return RateLimitResult(
            allowed=allowed,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=retry_after,
            headers=headers
        )
    
    async def _check_sliding_window(self, redis_key: str, config: RateLimitConfig) -> RateLimitResult:
        """Check rate limit using sliding window algorithm"""
        
        if redis_key not in self.active_windows:
            self.active_windows[redis_key] = SlidingWindowRateLimiter(
                requests_per_window=int(config.requests_per_second * config.window_size),
                window_size=config.window_size,
                redis_key=redis_key
            )
        
        limiter = self.active_windows[redis_key]
        allowed, remaining, timestamp = await limiter.is_allowed()
        
        reset_time = timestamp + config.window_size
        retry_after = None if allowed else config.window_size
        
        headers = {
            'X-RateLimit-Limit': str(int(config.requests_per_second * config.window_size)),
            'X-RateLimit-Remaining': str(remaining),
            'X-RateLimit-Reset': str(int(reset_time)),
            'X-RateLimit-Algorithm': 'sliding-window'
        }
        
        if not allowed:
            headers['Retry-After'] = str(retry_after)
        
        return RateLimitResult(
            allowed=allowed,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=retry_after,
            headers=headers
        )
    
    async def _check_fixed_window(self, redis_key: str, config: RateLimitConfig) -> RateLimitResult:
        """Check rate limit using fixed window algorithm"""
        
        current_time = time.time()
        window_start = int(current_time // config.window_size) * config.window_size
        window_key = f"{redis_key}:{window_start}"
        
        max_requests = int(config.requests_per_second * config.window_size)
        
        try:
            if redis_cache.is_connected():
                # Increment counter for this window
                current_count = await redis_cache.client.incr(window_key)
                
                if current_count == 1:
                    # First request in window, set expiration
                    await redis_cache.client.expire(window_key, config.window_size + 10)
                
                allowed = current_count <= max_requests
                remaining = max(0, max_requests - current_count)
                
            else:
                # Fallback to allowing requests
                allowed = True
                remaining = max_requests
                current_count = 1
                
        except Exception as e:
            logger.error(f"Fixed window rate limit error: {e}")
            allowed = True
            remaining = max_requests
            current_count = 1
        
        reset_time = window_start + config.window_size
        retry_after = None if allowed else int(reset_time - current_time) + 1
        
        headers = {
            'X-RateLimit-Limit': str(max_requests),
            'X-RateLimit-Remaining': str(remaining),
            'X-RateLimit-Reset': str(int(reset_time)),
            'X-RateLimit-Algorithm': 'fixed-window'
        }
        
        if not allowed:
            headers['Retry-After'] = str(retry_after)
        
        return RateLimitResult(
            allowed=allowed,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=retry_after,
            headers=headers
        )
    
    def _get_config(self, scope: RateLimitScope, endpoint: Optional[str] = None) -> RateLimitConfig:
        """Get rate limiting configuration for scope and endpoint"""
        
        # Check for endpoint-specific config first
        if endpoint and endpoint in self.endpoint_configs:
            return self.endpoint_configs[endpoint]
        
        # Fall back to scope default
        return self.default_configs.get(scope, self.default_configs[RateLimitScope.USER])
    
    def _generate_key(self, identifier: str, scope: RateLimitScope, endpoint: Optional[str] = None) -> str:
        """Generate Redis key for rate limiting"""
        
        key_parts = ['ratelimit', scope.value, identifier]
        
        if endpoint:
            # Clean endpoint for Redis key
            clean_endpoint = endpoint.replace('/', '_').replace(':', '_')
            key_parts.append(clean_endpoint)
        
        return ':'.join(key_parts)
    
    async def get_rate_limit_info(self, identifier: str, scope: RateLimitScope) -> Dict[str, Any]:
        """Get current rate limiting information for an identifier"""
        
        config = self._get_config(scope)
        redis_key = self._generate_key(identifier, scope)
        
        try:
            if redis_cache.is_connected():
                if config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
                    bucket_data = await redis_cache.client.hmget(
                        redis_key, 'tokens', 'last_refill'
                    )
                    
                    current_tokens = float(bucket_data[0] or config.burst_capacity)
                    last_refill = float(bucket_data[1] or time.time())
                    
                    return {
                        'algorithm': config.algorithm.value,
                        'current_tokens': current_tokens,
                        'capacity': config.burst_capacity,
                        'refill_rate': config.requests_per_second,
                        'last_refill': last_refill,
                        'next_refill': last_refill + (1.0 / config.requests_per_second)
                    }
                
                elif config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
                    current_time = time.time()
                    window_start = current_time - config.window_size
                    
                    # Count requests in current window
                    request_count = await redis_cache.client.zcount(
                        redis_key, window_start, current_time
                    )
                    
                    max_requests = int(config.requests_per_second * config.window_size)
                    
                    return {
                        'algorithm': config.algorithm.value,
                        'current_requests': request_count,
                        'max_requests': max_requests,
                        'window_size': config.window_size,
                        'remaining': max_requests - request_count
                    }
            
            # Fallback info
            return {
                'algorithm': config.algorithm.value,
                'configured': True,
                'redis_connected': redis_cache.is_connected()
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limit info: {e}")
            return {'error': str(e)}
    
    async def reset_rate_limit(self, identifier: str, scope: RateLimitScope, endpoint: Optional[str] = None):
        """Reset rate limiting for a specific identifier"""
        
        redis_key = self._generate_key(identifier, scope, endpoint)
        
        try:
            if redis_cache.is_connected():
                await redis_cache.client.delete(redis_key)
                
            # Clean up local caches
            if redis_key in self.active_buckets:
                del self.active_buckets[redis_key]
            if redis_key in self.active_windows:
                del self.active_windows[redis_key]
                
            logger.info(f"Rate limit reset for {identifier} ({scope.value})")
            
        except Exception as e:
            logger.error(f"Error resetting rate limit: {e}")
    
    def update_config(self, scope: RateLimitScope, config: RateLimitConfig, endpoint: Optional[str] = None):
        """Update rate limiting configuration"""
        
        if endpoint:
            self.endpoint_configs[endpoint] = config
        else:
            self.default_configs[scope] = config
        
        logger.info(f"Rate limit config updated for {scope.value}" + (f" endpoint {endpoint}" if endpoint else ""))
    
    async def get_global_stats(self) -> Dict[str, Any]:
        """Get global rate limiting statistics"""
        
        stats = {
            'algorithm_usage': {},
            'scope_usage': {},
            'total_buckets': len(self.active_buckets),
            'total_windows': len(self.active_windows),
            'redis_connected': redis_cache.is_connected()
        }
        
        # Count algorithm usage
        for config in self.default_configs.values():
            algo = config.algorithm.value
            stats['algorithm_usage'][algo] = stats['algorithm_usage'].get(algo, 0) + 1
        
        for config in self.endpoint_configs.values():
            algo = config.algorithm.value
            stats['algorithm_usage'][algo] = stats['algorithm_usage'].get(algo, 0) + 1
        
        # Count scope configurations
        for scope in self.default_configs.keys():
            stats['scope_usage'][scope.value] = 1
        
        return stats


# Global rate limiting service instance
rate_limiting_service = RateLimitingService()