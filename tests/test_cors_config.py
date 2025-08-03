"""
Unit tests for CORS configuration
"""

import pytest
import os
from unittest.mock import patch, Mock
from fastapi import FastAPI
from fastapi.testclient import TestClient
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.middleware.cors_config import (
    CORSConfig,
    setup_cors,
    create_cors_config,
    CORSPresets,
    validate_origin,
    get_origin_from_request,
    get_cors_config_for_environment,
    DynamicCORSConfig
)


class TestCORSConfig:
    """Test CORS configuration class"""
    
    def test_default_development_config(self):
        """Test default configuration for development"""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            config = CORSConfig()
            
            assert config.environment == "development"
            assert "http://localhost:3000" in config.allowed_origins
            assert "http://localhost:8501" in config.allowed_origins  # Streamlit
            assert config.allow_credentials == True
            assert "GET" in config.allowed_methods
            assert "POST" in config.allowed_methods
            assert "Authorization" in config.allowed_headers
    
    def test_production_config(self):
        """Test production configuration"""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            config = CORSConfig()
            
            assert config.environment == "production"
            assert "https://app.example.com" in config.allowed_origins
            assert "http://localhost:3000" not in config.allowed_origins
            assert config.allow_credentials == True
    
    def test_custom_origins_from_env(self):
        """Test custom origins from environment variable"""
        with patch.dict(os.environ, {
            "CORS_ALLOWED_ORIGINS": "https://custom1.com,https://custom2.com"
        }):
            config = CORSConfig()
            
            assert config.allowed_origins == ["https://custom1.com", "https://custom2.com"]
    
    def test_custom_methods_from_env(self):
        """Test custom methods from environment variable"""
        with patch.dict(os.environ, {
            "CORS_ALLOWED_METHODS": "GET,POST"
        }):
            config = CORSConfig()
            
            assert config.allowed_methods == ["GET", "POST"]
    
    def test_allow_credentials_from_env(self):
        """Test allow credentials from environment variable"""
        with patch.dict(os.environ, {"CORS_ALLOW_CREDENTIALS": "false"}):
            config = CORSConfig()
            assert config.allow_credentials == False
        
        with patch.dict(os.environ, {"CORS_ALLOW_CREDENTIALS": "true"}):
            config = CORSConfig()
            assert config.allow_credentials == True
    
    def test_max_age_from_env(self):
        """Test max age from environment variable"""
        with patch.dict(os.environ, {"CORS_MAX_AGE": "7200"}):
            config = CORSConfig()
            assert config.max_age == 7200
    
    def test_is_origin_allowed(self):
        """Test origin validation"""
        config = CORSConfig()
        config.allowed_origins = [
            "https://app.example.com",
            "*.subdomain.example.com",
            "*"
        ]
        
        # Test exact match
        assert config.is_origin_allowed("https://app.example.com") == True
        
        # Test wildcard subdomain
        config.allowed_origins = ["*.example.com"]
        assert config.is_origin_allowed("https://app.example.com") == True
        assert config.is_origin_allowed("https://api.example.com") == True
        assert config.is_origin_allowed("https://other.com") == False
        
        # Test wildcard all
        config.allowed_origins = ["*"]
        assert config.is_origin_allowed("https://any.domain.com") == True
    
    def test_get_middleware_kwargs(self):
        """Test middleware kwargs generation"""
        config = CORSConfig()
        kwargs = config.get_middleware_kwargs()
        
        assert "allow_origins" in kwargs
        assert "allow_credentials" in kwargs
        assert "allow_methods" in kwargs
        assert "allow_headers" in kwargs
        assert "expose_headers" in kwargs
        assert "max_age" in kwargs


class TestCORSSetup:
    """Test CORS setup functionality"""
    
    @pytest.fixture
    def app(self):
        """Create test FastAPI app"""
        return FastAPI()
    
    def test_setup_cors_default(self, app):
        """Test setting up CORS with default config"""
        setup_cors(app)
        
        # Check that middleware was added
        middlewares = [m for m in app.user_middleware]
        assert len(middlewares) > 0
        
        # The middleware is wrapped, so check the class name
        cors_middleware = None
        for middleware in middlewares:
            if "cors" in str(middleware).lower():
                cors_middleware = middleware
                break
        
        assert cors_middleware is not None
    
    def test_setup_cors_custom(self, app):
        """Test setting up CORS with custom config"""
        custom_config = create_cors_config(
            allowed_origins=["https://custom.domain.com"],
            allow_credentials=False
        )
        
        setup_cors(app, custom_config)
        
        assert custom_config.allowed_origins == ["https://custom.domain.com"]
        assert custom_config.allow_credentials == False
    
    def test_cors_headers_in_response(self):
        """Test CORS headers in actual response"""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        # Setup CORS with specific origin
        config = create_cors_config(
            allowed_origins=["http://testorigin.com"],
            allow_credentials=True
        )
        setup_cors(app, config)
        
        client = TestClient(app)
        
        # Test preflight request
        response = client.options(
            "/test",
            headers={
                "Origin": "http://testorigin.com",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://testorigin.com"
        assert response.headers.get("access-control-allow-credentials") == "true"


class TestCORSPresets:
    """Test CORS preset configurations"""
    
    def test_public_api_preset(self):
        """Test public API preset"""
        config = CORSPresets.public_api()
        
        assert config.allowed_origins == ["*"]
        assert config.allow_credentials == False
        assert config.allowed_methods == ["GET", "POST", "OPTIONS"]
        assert config.max_age == 86400
    
    def test_private_api_preset(self):
        """Test private API preset"""
        config = CORSPresets.private_api()
        
        assert "https://app.example.com" in config.allowed_origins
        assert config.allow_credentials == True
        assert "DELETE" in config.allowed_methods
        assert config.max_age == 3600
    
    def test_mobile_app_preset(self):
        """Test mobile app preset"""
        config = CORSPresets.mobile_app()
        
        assert config.allowed_origins == ["*"]
        assert config.allow_credentials == True
        assert config.allowed_headers == ["*"]
        assert config.exposed_headers == ["*"]
        assert config.max_age == 0
    
    def test_development_preset(self):
        """Test development preset"""
        config = CORSPresets.development()
        
        assert config.allowed_origins == ["*"]
        assert config.allow_credentials == True
        assert config.allowed_methods == ["*"]
        assert config.allowed_headers == ["*"]


class TestCORSUtilities:
    """Test CORS utility functions"""
    
    def test_validate_origin(self):
        """Test origin validation utility"""
        # Test exact match
        assert validate_origin("https://app.com", ["https://app.com"]) == True
        assert validate_origin("https://app.com", ["https://other.com"]) == False
        
        # Test wildcard
        assert validate_origin("https://any.com", ["*"]) == True
        
        # Test subdomain wildcard
        assert validate_origin("https://api.example.com", ["*.example.com"]) == True
        assert validate_origin("https://app.example.com", ["*.example.com"]) == True
        assert validate_origin("https://other.com", ["*.example.com"]) == False
        
        # Test regex pattern
        assert validate_origin(
            "https://app-123.example.com",
            ["^https://app-[0-9]+\\.example\\.com$"]
        ) == True
    
    def test_get_origin_from_request(self):
        """Test extracting origin from request"""
        # Test with Origin header
        request = Mock()
        request.headers = {"Origin": "https://app.com"}
        assert get_origin_from_request(request) == "https://app.com"
        
        # Test with Referer header
        request.headers = {"Referer": "https://app.com/page"}
        assert get_origin_from_request(request) == "https://app.com/page"
        
        # Test with both (Origin takes precedence)
        request.headers = {
            "Origin": "https://app.com",
            "Referer": "https://other.com"
        }
        assert get_origin_from_request(request) == "https://app.com"
        
        # Test with neither
        request.headers = {}
        assert get_origin_from_request(request) is None
    
    def test_get_cors_config_for_environment(self):
        """Test environment-based configuration"""
        # Test production
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            config = get_cors_config_for_environment()
            assert "https://app.example.com" in config.allowed_origins
            assert config.max_age == 86400
        
        # Test staging
        with patch.dict(os.environ, {"ENVIRONMENT": "staging"}):
            config = get_cors_config_for_environment()
            assert "http://localhost:3000" in config.allowed_origins
            assert config.max_age == 3600
        
        # Test development
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            config = get_cors_config_for_environment()
            assert config.allowed_origins == ["*"]


class TestDynamicCORS:
    """Test dynamic CORS configuration"""
    
    def test_dynamic_cors_config(self):
        """Test dynamic CORS for multi-tenant apps"""
        # Create tenant resolver
        def resolve_tenant(request):
            return request.headers.get("X-Tenant-ID", "default")
        
        dynamic_config = DynamicCORSConfig(resolve_tenant)
        
        # Add tenant configs
        tenant1_config = create_cors_config(
            allowed_origins=["https://tenant1.com"]
        )
        tenant2_config = create_cors_config(
            allowed_origins=["https://tenant2.com"]
        )
        
        dynamic_config.add_tenant_config("tenant1", tenant1_config)
        dynamic_config.add_tenant_config("tenant2", tenant2_config)
        
        # Test resolving config for tenant1
        request = Mock()
        request.headers = {"X-Tenant-ID": "tenant1"}
        config = dynamic_config.get_config_for_request(request)
        assert config.allowed_origins == ["https://tenant1.com"]
        
        # Test resolving config for tenant2
        request.headers = {"X-Tenant-ID": "tenant2"}
        config = dynamic_config.get_config_for_request(request)
        assert config.allowed_origins == ["https://tenant2.com"]
        
        # Test default config
        request.headers = {"X-Tenant-ID": "unknown"}
        config = dynamic_config.get_config_for_request(request)
        assert isinstance(config, CORSConfig)


class TestCORSIntegration:
    """Test CORS integration scenarios"""
    
    def test_cors_with_authentication(self):
        """Test CORS with authentication headers"""
        app = FastAPI()
        
        @app.get("/protected")
        async def protected_endpoint():
            return {"data": "secret"}
        
        # Setup CORS allowing credentials
        config = create_cors_config(
            allowed_origins=["http://frontend.com"],
            allow_credentials=True,
            allowed_headers=["Authorization", "Content-Type"]
        )
        setup_cors(app, config)
        
        client = TestClient(app)
        
        # Test with correct origin and auth header
        response = client.get(
            "/protected",
            headers={
                "Origin": "http://frontend.com",
                "Authorization": "Bearer token123"
            }
        )
        
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://frontend.com"
        assert response.headers.get("access-control-allow-credentials") == "true"
    
    def test_cors_preflight_caching(self):
        """Test CORS preflight caching headers"""
        app = FastAPI()
        
        @app.post("/data")
        async def create_data():
            return {"id": 123}
        
        # Setup CORS with max age
        config = create_cors_config(
            allowed_origins=["http://app.com"],
            max_age=7200  # 2 hours
        )
        setup_cors(app, config)
        
        client = TestClient(app)
        
        # Send preflight request
        response = client.options(
            "/data",
            headers={
                "Origin": "http://app.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        assert response.status_code == 200
        assert response.headers.get("access-control-max-age") == "7200"
    
    def test_cors_with_custom_headers(self):
        """Test CORS with custom headers"""
        app = FastAPI()
        
        @app.get("/api/data")
        async def get_data():
            return {"data": "value"}
        
        # Setup CORS with custom headers
        config = create_cors_config(
            allowed_origins=["http://app.com"],
            allowed_headers=["X-Custom-Header", "X-API-Version"],
            exposed_headers=["X-Response-ID", "X-Rate-Limit"]
        )
        setup_cors(app, config)
        
        client = TestClient(app)
        
        # Test preflight with custom headers
        response = client.options(
            "/api/data",
            headers={
                "Origin": "http://app.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "X-Custom-Header"
            }
        )
        
        assert response.status_code == 200
        allowed_headers = response.headers.get("access-control-allow-headers", "").lower()
        assert "x-custom-header" in allowed_headers


if __name__ == '__main__':
    pytest.main([__file__, '-v'])