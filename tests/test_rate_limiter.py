"""
Unit tests for rate limiting middleware
"""

import pytest
import time
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import redis
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.middleware.rate_limiter import (
    TokenBucket,
    RateLimiter,
    RateLimitMiddleware,
    RateLimitExceeded,
    create_rate_limiter
)


class TestTokenBucket:
    """Test token bucket implementation"""
    
    def test_initialization(self):
        """Test token bucket initialization"""
        bucket = TokenBucket(capacity=10, refill_rate=2)
        
        assert bucket.capacity == 10
        assert bucket.tokens == 10
        assert bucket.refill_rate == 2
        assert bucket.refill_period == 1
    
    def test_consume_tokens(self):
        """Test consuming tokens"""
        bucket = TokenBucket(capacity=10, refill_rate=2)
        
        # Consume 1 token
        success, remaining = bucket.consume(1)
        assert success == True
        assert remaining == 9
        
        # Consume 5 more tokens
        success, remaining = bucket.consume(5)
        assert success == True
        assert remaining == 4
        
        # Try to consume more than available
        success, remaining = bucket.consume(5)
        assert success == False
        assert remaining == 4
    
    def test_refill_tokens(self):
        """Test token refilling"""
        bucket = TokenBucket(capacity=10, refill_rate=10, refill_period=1)
        
        # Consume all tokens
        bucket.consume(10)
        assert bucket.tokens == 0
        
        # Wait for refill
        time.sleep(1.1)
        
        # Try consuming again (should have refilled)
        success, remaining = bucket.consume(1)
        assert success == True
        assert remaining >= 8  # Should have refilled at least 9 tokens
    
    def test_time_until_refill(self):
        """Test calculating time until refill"""
        bucket = TokenBucket(capacity=10, refill_rate=2, refill_period=2)
        
        # With tokens available
        assert bucket.time_until_refill() == 0
        
        # With no tokens
        bucket.consume(10)
        time_until = bucket.time_until_refill()
        assert time_until > 0 and time_until <= 2


class TestRateLimiter:
    """Test rate limiter functionality"""
    
    @pytest.fixture
    def rate_limiter(self):
        """Create rate limiter without Redis"""
        return RateLimiter(redis_client=None, use_redis=False)
    
    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client"""
        mock = Mock(spec=redis.Redis)
        mock.zremrangebyscore = Mock()
        mock.zcard = Mock(return_value=0)
        mock.zadd = Mock()
        mock.expire = Mock()
        mock.zrange = Mock(return_value=[])
        mock.delete = Mock()
        return mock
    
    def test_get_limit_config(self, rate_limiter):
        """Test getting rate limit configuration"""
        # Test endpoint-specific limit
        config = rate_limiter._get_limit_config("/api/auth/login")
        assert config["limit"] == 10
        assert config["window"] == 300
        
        # Test tier-specific limit
        config = rate_limiter._get_limit_config("/api/unknown", user_tier="pro")
        assert config["limit"] == 2000
        assert config["window"] == 3600
        
        # Test default limit
        config = rate_limiter._get_limit_config("/api/unknown")
        assert config["limit"] == 100
        assert config["window"] == 3600
    
    @pytest.mark.asyncio
    async def test_local_rate_limit_allow(self, rate_limiter):
        """Test local rate limiting allowing requests"""
        identifier = "test_user"
        
        # First request should be allowed
        allowed, info = await rate_limiter.check_rate_limit(
            identifier=identifier,
            endpoint="/api/test",
            cost=1
        )
        
        assert allowed == True
        assert info["limit"] == 100
        assert info["remaining"] == 99
    
    @pytest.mark.asyncio
    async def test_local_rate_limit_exceed(self, rate_limiter):
        """Test local rate limiting blocking requests"""
        identifier = "test_user_2"
        
        # Configure a low limit for testing
        rate_limiter.endpoint_limits["/api/test"] = {"limit": 2, "window": 60}
        
        # First two requests should be allowed
        for i in range(2):
            allowed, info = await rate_limiter.check_rate_limit(
                identifier=identifier,
                endpoint="/api/test"
            )
            assert allowed == True
        
        # Third request should be blocked
        allowed, info = await rate_limiter.check_rate_limit(
            identifier=identifier,
            endpoint="/api/test"
        )
        
        assert allowed == False
        assert info["remaining"] == 0
        assert info["retry_after"] > 0
    
    @pytest.mark.asyncio
    async def test_redis_rate_limit(self, mock_redis):
        """Test Redis-based rate limiting"""
        rate_limiter = RateLimiter(redis_client=mock_redis, use_redis=True)
        
        # Mock Redis responses
        mock_redis.zcard.return_value = 5  # 5 requests in window
        
        allowed, info = await rate_limiter.check_rate_limit(
            identifier="user123",
            endpoint="/api/test",
            cost=1
        )
        
        assert allowed == True
        assert info["remaining"] == 94  # 100 - 5 - 1
        
        # Verify Redis calls
        mock_redis.zremrangebyscore.assert_called_once()
        mock_redis.zcard.assert_called_once()
        mock_redis.zadd.assert_called_once()
        mock_redis.expire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_redis_rate_limit_exceeded(self, mock_redis):
        """Test Redis rate limit exceeded"""
        rate_limiter = RateLimiter(redis_client=mock_redis, use_redis=True)
        
        # Mock Redis to show limit exceeded
        mock_redis.zcard.return_value = 100  # At limit
        mock_redis.zrange.return_value = [(b"entry", time.time() - 1800)]  # 30 min ago
        
        allowed, info = await rate_limiter.check_rate_limit(
            identifier="user123",
            endpoint="/api/test",
            cost=1
        )
        
        assert allowed == False
        assert info["remaining"] == 0
        assert info["retry_after"] > 0
    
    @pytest.mark.asyncio
    async def test_redis_fallback(self, mock_redis):
        """Test fallback to local when Redis fails"""
        rate_limiter = RateLimiter(redis_client=mock_redis, use_redis=True)
        
        # Make Redis fail
        mock_redis.zremrangebyscore.side_effect = Exception("Redis error")
        
        # Should fall back to local rate limiting
        allowed, info = await rate_limiter.check_rate_limit(
            identifier="user123",
            endpoint="/api/test"
        )
        
        assert allowed == True  # Local bucket starts full
        assert info["remaining"] == 99
    
    def test_reset_limit(self, rate_limiter, mock_redis):
        """Test resetting rate limits"""
        # Test local reset
        identifier = "test_user"
        rate_limiter.local_buckets[f"{identifier}:/api/test"] = TokenBucket(10, 1)
        
        rate_limiter.reset_limit(identifier, "/api/test")
        assert f"{identifier}:/api/test" not in rate_limiter.local_buckets
        
        # Test Redis reset
        redis_limiter = RateLimiter(redis_client=mock_redis, use_redis=True)
        redis_limiter.reset_limit("user123", "/api/test")
        
        mock_redis.delete.assert_called_once_with("rate_limit:user123:/api/test")


class TestRateLimitMiddleware:
    """Test rate limit middleware integration"""
    
    @pytest.fixture
    def app(self):
        """Create test FastAPI app"""
        app = FastAPI()
        
        @app.get("/api/test")
        async def test_endpoint():
            return {"message": "success"}
        
        @app.post("/api/auth/login")
        async def login_endpoint():
            return {"token": "test_token"}
        
        @app.get("/health")
        async def health_endpoint():
            return {"status": "ok"}
        
        return app
    
    @pytest.fixture
    def client_with_rate_limit(self, app):
        """Create test client with rate limiting"""
        rate_limiter = RateLimiter(use_redis=False, default_limit=5, default_window=60)
        
        # Override limits for testing
        rate_limiter.endpoint_limits["/api/test"] = {"limit": 3, "window": 60}
        
        app.add_middleware(
            RateLimitMiddleware,
            rate_limiter=rate_limiter,
            skip_paths=["/health"]
        )
        
        return TestClient(app)
    
    def test_rate_limit_headers(self, client_with_rate_limit):
        """Test rate limit headers in response"""
        response = client_with_rate_limit.get("/api/test")
        
        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert response.headers["X-RateLimit-Limit"] == "3"
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
    
    def test_rate_limit_exceeded(self, client_with_rate_limit):
        """Test rate limit exceeded response"""
        # Make 3 requests (the limit)
        for i in range(3):
            response = client_with_rate_limit.get("/api/test")
            assert response.status_code == 200
        
        # 4th request should be rate limited
        response = client_with_rate_limit.get("/api/test")
        assert response.status_code == 429
        assert "Retry-After" in response.headers
        
        data = response.json()
        assert "error" in data
        assert "retry_after" in data
        assert data["error"] == "Rate limit exceeded"
    
    def test_skip_paths(self, client_with_rate_limit):
        """Test that skip paths bypass rate limiting"""
        # Make many requests to health endpoint
        for i in range(10):
            response = client_with_rate_limit.get("/health")
            assert response.status_code == 200
            assert "X-RateLimit-Limit" not in response.headers
    
    @pytest.mark.asyncio
    async def test_custom_identifier_extractor(self, app):
        """Test custom identifier extraction"""
        rate_limiter = RateLimiter(use_redis=False)
        
        # Custom extractor that uses user ID from state
        async def custom_extractor(request: Request):
            if hasattr(request.state, "user_id"):
                return f"user:{request.state.user_id}"
            return "anonymous"
        
        middleware = RateLimitMiddleware(
            app,
            rate_limiter=rate_limiter,
            identifier_extractor=custom_extractor
        )
        
        # Create mock request
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user_id = 123
        
        identifier = await middleware._default_identifier_extractor(request)
        assert identifier == "user:123"
    
    @pytest.mark.asyncio
    async def test_cost_calculator(self, app):
        """Test request cost calculation"""
        rate_limiter = RateLimiter(use_redis=False)
        middleware = RateLimitMiddleware(app, rate_limiter=rate_limiter)
        
        # Test different endpoint costs
        request = Mock(spec=Request)
        
        request.url.path = "/api/transcription/process"
        cost = await middleware._default_cost_calculator(request)
        assert cost == 5
        
        request.url.path = "/api/export"
        cost = await middleware._default_cost_calculator(request)
        assert cost == 3
        
        request.url.path = "/api/test"
        request.method = "POST"
        cost = await middleware._default_cost_calculator(request)
        assert cost == 2
        
        request.method = "GET"
        cost = await middleware._default_cost_calculator(request)
        assert cost == 1


class TestRateLimitIntegration:
    """Test rate limiter integration scenarios"""
    
    def test_create_rate_limiter_with_redis(self):
        """Test creating rate limiter with Redis URL"""
        with patch('redis.from_url') as mock_from_url:
            mock_redis = Mock()
            mock_redis.ping = Mock()
            mock_from_url.return_value = mock_redis
            
            limiter = create_rate_limiter("redis://localhost:6379")
            
            assert limiter.use_redis == True
            assert limiter.redis_client == mock_redis
            mock_redis.ping.assert_called_once()
    
    def test_create_rate_limiter_redis_failure(self):
        """Test creating rate limiter when Redis fails"""
        with patch('redis.from_url') as mock_from_url:
            mock_from_url.side_effect = Exception("Connection failed")
            
            limiter = create_rate_limiter("redis://localhost:6379")
            
            assert limiter.use_redis == False
            assert limiter.redis_client is None
    
    @pytest.mark.asyncio
    async def test_rate_limit_decorator(self):
        """Test rate limit decorator"""
        from api.middleware.rate_limiter import rate_limit
        
        # Create mock request
        request = Mock(spec=Request)
        request.app.state.rate_limiter = RateLimiter(use_redis=False)
        request.client = Mock(host="127.0.0.1")
        request.url.path = "/api/test"
        
        # Decorate function
        @rate_limit(limit=2, window=60)
        async def test_function(request):
            return {"status": "ok"}
        
        # First two calls should succeed
        for i in range(2):
            result = await test_function(request)
            assert result["status"] == "ok"
        
        # Third call should raise exception
        with pytest.raises(RateLimitExceeded):
            await test_function(request)
    
    def test_user_tier_limits(self):
        """Test different rate limits for user tiers"""
        rate_limiter = RateLimiter(use_redis=False)
        
        # Test free tier
        config = rate_limiter._get_limit_config("/api/unknown", user_tier="free")
        assert config["limit"] == 100
        
        # Test pro tier
        config = rate_limiter._get_limit_config("/api/unknown", user_tier="pro")
        assert config["limit"] == 2000
        
        # Test enterprise tier
        config = rate_limiter._get_limit_config("/api/unknown", user_tier="enterprise")
        assert config["limit"] == 10000


if __name__ == '__main__':
    pytest.main([__file__, '-v'])