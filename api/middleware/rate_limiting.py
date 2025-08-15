"""
Advanced Rate Limiting Middleware
Comprehensive rate limiting with medical-specific quotas and Redis backend
"""

import time
import json
import hashlib
from typing import Dict, Optional, List, Any, Callable
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import redis
import logging

logger = logging.getLogger(__name__)

class RateLimitRule:
    """Rate limiting rule definition"""
    
    def __init__(
        self,
        key: str,
        limit: int,
        window_seconds: int,
        scope: str = "global",
        description: str = ""
    ):
        self.key = key
        self.limit = limit
        self.window_seconds = window_seconds
        self.scope = scope
        self.description = description
    
    def __str__(self):
        return f"RateLimitRule({self.key}: {self.limit}/{self.window_seconds}s)"


class RateLimitResult:
    """Rate limiting check result"""
    
    def __init__(
        self,
        allowed: bool,
        limit: int,
        remaining: int,
        reset_time: int,
        retry_after: Optional[int] = None
    ):
        self.allowed = allowed
        self.limit = limit
        self.remaining = remaining
        self.reset_time = reset_time
        self.retry_after = retry_after


class MedicalRateLimiter:
    """Advanced rate limiter with medical-specific features"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client or redis.Redis(host='localhost', port=6379, db=0)
        self.fallback_store: Dict[str, Dict] = {}  # In-memory fallback
        self.use_redis = True
        
        # Test Redis connection
        try:
            self.redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory store: {e}")
            self.use_redis = False
    
    def _get_key(self, identifier: str, rule: RateLimitRule) -> str:
        """Generate cache key for rate limiting"""
        window_start = int(time.time()) // rule.window_seconds
        return f"rate_limit:{rule.scope}:{identifier}:{rule.key}:{window_start}"
    
    def _get_requests_count(self, cache_key: str) -> int:
        """Get current request count for key"""
        if self.use_redis:
            try:
                count = self.redis_client.get(cache_key)
                return int(count) if count else 0
            except Exception as e:
                logger.warning(f"Redis error, falling back: {e}")
                # Fall through to in-memory store
        
        # In-memory fallback
        current_time = int(time.time())
        if cache_key in self.fallback_store:
            data = self.fallback_store[cache_key]
            if current_time - data['timestamp'] < data['window']:
                return data['count']
        
        return 0
    
    def _increment_requests(self, cache_key: str, rule: RateLimitRule) -> int:
        """Increment request count"""
        if self.use_redis:
            try:
                pipe = self.redis_client.pipeline()
                pipe.incr(cache_key)
                pipe.expire(cache_key, rule.window_seconds)
                results = pipe.execute()
                return results[0]
            except Exception as e:
                logger.warning(f"Redis error, falling back: {e}")
                # Fall through to in-memory store
        
        # In-memory fallback
        current_time = int(time.time())
        if cache_key not in self.fallback_store:
            self.fallback_store[cache_key] = {
                'count': 0,
                'timestamp': current_time,
                'window': rule.window_seconds
            }
        
        data = self.fallback_store[cache_key]
        if current_time - data['timestamp'] >= data['window']:
            # Reset window
            data['count'] = 0
            data['timestamp'] = current_time
        
        data['count'] += 1
        return data['count']
    
    def check_rate_limit(
        self, 
        identifier: str, 
        rule: RateLimitRule
    ) -> RateLimitResult:
        """Check if request is within rate limits"""
        cache_key = self._get_key(identifier, rule)
        current_count = self._get_requests_count(cache_key)
        
        # Calculate reset time
        window_start = int(time.time()) // rule.window_seconds
        reset_time = (window_start + 1) * rule.window_seconds
        
        # Check if limit exceeded
        if current_count >= rule.limit:
            retry_after = reset_time - int(time.time())
            return RateLimitResult(
                allowed=False,
                limit=rule.limit,
                remaining=0,
                reset_time=reset_time,
                retry_after=max(1, retry_after)
            )
        
        # Allow request and increment counter
        new_count = self._increment_requests(cache_key, rule)
        remaining = max(0, rule.limit - new_count)
        
        return RateLimitResult(
            allowed=True,
            limit=rule.limit,
            remaining=remaining,
            reset_time=reset_time
        )
    
    def get_rate_limit_status(
        self, 
        identifier: str, 
        rules: List[RateLimitRule]
    ) -> Dict[str, RateLimitResult]:
        """Get rate limit status for multiple rules"""
        results = {}
        for rule in rules:
            cache_key = self._get_key(identifier, rule)
            current_count = self._get_requests_count(cache_key)
            
            window_start = int(time.time()) // rule.window_seconds
            reset_time = (window_start + 1) * rule.window_seconds
            remaining = max(0, rule.limit - current_count)
            
            results[rule.key] = RateLimitResult(
                allowed=current_count < rule.limit,
                limit=rule.limit,
                remaining=remaining,
                reset_time=reset_time
            )
        
        return results


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting with medical-specific rules"""
    
    def __init__(
        self, 
        app,
        redis_client: Optional[redis.Redis] = None,
        custom_rules: Optional[Dict[str, List[RateLimitRule]]] = None
    ):
        super().__init__(app)
        self.limiter = MedicalRateLimiter(redis_client)
        self.custom_rules = custom_rules or {}
        self.default_rules = self._get_default_rules()
    
    def _get_default_rules(self) -> Dict[str, List[RateLimitRule]]:
        """Get default rate limiting rules"""
        return {
            "anonymous": [
                RateLimitRule("requests", 100, 3600, "global", "100 requests per hour"),
                RateLimitRule("transcription", 5, 3600, "feature", "5 transcriptions per hour"),
            ],
            "authenticated": [
                RateLimitRule("requests", 1000, 3600, "user", "1000 requests per hour"),
                RateLimitRule("transcription", 50, 3600, "feature", "50 transcriptions per hour"),
                RateLimitRule("search", 200, 3600, "feature", "200 searches per hour"),
            ],
            "medical_professional": [
                RateLimitRule("requests", 5000, 3600, "user", "5000 requests per hour"),
                RateLimitRule("medical_transcription", 200, 3600, "feature", "200 medical transcriptions per hour"),
                RateLimitRule("phi_processing", 100, 3600, "feature", "100 PHI processing requests per hour"),
                RateLimitRule("analytics", 500, 3600, "feature", "500 analytics requests per hour"),
            ],
            "enterprise": [
                RateLimitRule("requests", 10000, 3600, "organization", "10000 requests per hour"),
                RateLimitRule("medical_transcription", 1000, 3600, "feature", "1000 medical transcriptions per hour"),
                RateLimitRule("bulk_processing", 50, 3600, "feature", "50 bulk operations per hour"),
            ],
            "api_key": [
                RateLimitRule("requests", 2000, 3600, "api_key", "2000 requests per hour per API key"),
                RateLimitRule("medical_api", 300, 3600, "feature", "300 medical API calls per hour"),
            ]
        }
    
    def _get_user_identifier(self, request: Request) -> tuple[str, str]:
        """Get user identifier and tier from request"""
        # Check for API key first
        api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
        if api_key:
            # Hash API key for privacy
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
            return f"api_key:{key_hash}", "api_key"
        
        # Check for authenticated user
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            user_tier = getattr(request.state, "user_tier", "authenticated")
            return f"user:{user_id}", user_tier
        
        # Fall back to IP-based identification for anonymous users
        client_ip = request.client.host
        return f"ip:{client_ip}", "anonymous"
    
    def _get_feature_type(self, request: Request) -> str:
        """Determine feature type from request path"""
        path = request.url.path
        
        if "/medical/" in path:
            if "/transcriptions" in path:
                return "medical_transcription"
            elif "/analytics" in path:
                return "analytics"
            else:
                return "medical_api"
        elif "/transcriptions" in path:
            return "transcription"
        elif "/search" in path:
            return "search"
        elif "/api/graphql" in path:
            return "graphql"
        elif path.startswith("/api/"):
            return "api"
        else:
            return "general"
    
    def _get_applicable_rules(
        self, 
        user_tier: str, 
        feature_type: str,
        method: str
    ) -> List[RateLimitRule]:
        """Get applicable rate limiting rules"""
        rules = []
        
        # Add tier-based rules
        tier_rules = self.default_rules.get(user_tier, self.default_rules["anonymous"])
        rules.extend(tier_rules)
        
        # Add custom rules if defined
        custom_key = f"{user_tier}:{feature_type}"
        if custom_key in self.custom_rules:
            rules.extend(self.custom_rules[custom_key])
        
        # Add method-specific rules for destructive operations
        if method in ["POST", "PUT", "DELETE"]:
            rules.append(RateLimitRule(
                f"{method.lower()}_operations", 
                100, 
                3600, 
                "user", 
                f"{method} operations per hour"
            ))
        
        return rules
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through rate limiting"""
        # Skip rate limiting for health checks and admin endpoints
        if request.url.path in ["/health", "/metrics", "/.well-known/health"]:
            return await call_next(request)
        
        # Get user information
        identifier, user_tier = self._get_user_identifier(request)
        feature_type = self._get_feature_type(request)
        method = request.method
        
        # Get applicable rules
        rules = self._get_applicable_rules(user_tier, feature_type, method)
        
        # Check each rule
        rate_limit_results = {}
        blocked_rule = None
        
        for rule in rules:
            result = self.limiter.check_rate_limit(identifier, rule)
            rate_limit_results[rule.key] = result
            
            if not result.allowed:
                blocked_rule = rule
                break
        
        # If any rule blocks the request, return 429
        if blocked_rule:
            result = rate_limit_results[blocked_rule.key]
            
            error_detail = {
                "error": "Rate limit exceeded",
                "rule": blocked_rule.description,
                "limit": result.limit,
                "remaining": result.remaining,
                "reset_time": result.reset_time,
                "retry_after": result.retry_after,
                "identifier_type": user_tier,
                "feature_type": feature_type
            }
            
            # Log rate limit violation
            logger.warning(
                f"Rate limit exceeded for {identifier} on {blocked_rule.key}: "
                f"{blocked_rule.description}"
            )
            
            # Create response with rate limit headers
            response = Response(
                content=json.dumps(error_detail),
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json"
            )
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(result.limit)
            response.headers["X-RateLimit-Remaining"] = str(result.remaining)
            response.headers["X-RateLimit-Reset"] = str(result.reset_time)
            if result.retry_after:
                response.headers["Retry-After"] = str(result.retry_after)
            
            return response
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        if rate_limit_results:
            # Use the most restrictive rule for headers
            most_restrictive = min(
                rate_limit_results.values(), 
                key=lambda r: r.remaining
            )
            
            response.headers["X-RateLimit-Limit"] = str(most_restrictive.limit)
            response.headers["X-RateLimit-Remaining"] = str(most_restrictive.remaining)
            response.headers["X-RateLimit-Reset"] = str(most_restrictive.reset_time)
        
        return response


# Utility functions for FastAPI dependency injection

def get_rate_limiter(redis_client: Optional[redis.Redis] = None) -> MedicalRateLimiter:
    """Dependency to get rate limiter instance"""
    return MedicalRateLimiter(redis_client)


async def check_medical_rate_limit(
    request: Request,
    limiter: MedicalRateLimiter = None
) -> bool:
    """FastAPI dependency for medical endpoint rate limiting"""
    if not limiter:
        limiter = MedicalRateLimiter()
    
    # Medical professionals get higher limits
    user_tier = getattr(request.state, "user_tier", "authenticated")
    
    medical_rule = RateLimitRule(
        "medical_transcription", 
        200 if user_tier == "medical_professional" else 50,
        3600,
        "feature",
        "Medical transcription rate limit"
    )
    
    # Get identifier
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        identifier = f"user:{user_id}"
    else:
        identifier = f"ip:{request.client.host}"
    
    result = limiter.check_rate_limit(identifier, medical_rule)
    
    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Medical transcription rate limit exceeded",
                "limit": result.limit,
                "remaining": result.remaining,
                "reset_time": result.reset_time,
                "retry_after": result.retry_after
            }
        )
    
    return True


# Rate limiting configuration for different subscription tiers
TIER_CONFIGURATIONS = {
    "free": {
        "requests_per_hour": 100,
        "transcriptions_per_hour": 5,
        "medical_transcriptions_per_hour": 2,
        "search_queries_per_hour": 50,
        "api_calls_per_hour": 100
    },
    "basic": {
        "requests_per_hour": 1000,
        "transcriptions_per_hour": 50,
        "medical_transcriptions_per_hour": 20,
        "search_queries_per_hour": 200,
        "api_calls_per_hour": 500
    },
    "professional": {
        "requests_per_hour": 5000,
        "transcriptions_per_hour": 200,
        "medical_transcriptions_per_hour": 100,
        "search_queries_per_hour": 1000,
        "api_calls_per_hour": 2000
    },
    "enterprise": {
        "requests_per_hour": 20000,
        "transcriptions_per_hour": 1000,
        "medical_transcriptions_per_hour": 500,
        "search_queries_per_hour": 5000,
        "api_calls_per_hour": 10000
    }
}


def get_tier_rules(tier: str) -> List[RateLimitRule]:
    """Get rate limiting rules for subscription tier"""
    config = TIER_CONFIGURATIONS.get(tier, TIER_CONFIGURATIONS["free"])
    
    rules = [
        RateLimitRule("requests", config["requests_per_hour"], 3600, "user", "General requests"),
        RateLimitRule("transcription", config["transcriptions_per_hour"], 3600, "feature", "Transcriptions"),
        RateLimitRule("medical_transcription", config["medical_transcriptions_per_hour"], 3600, "feature", "Medical transcriptions"),
        RateLimitRule("search", config["search_queries_per_hour"], 3600, "feature", "Search queries"),
        RateLimitRule("api", config["api_calls_per_hour"], 3600, "feature", "API calls")
    ]
    
    return rules