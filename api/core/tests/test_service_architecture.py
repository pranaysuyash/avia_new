"""
Comprehensive tests for the FastAPI service architecture foundation
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException

from ..base_service import BaseService, ServiceConfig, ServiceRequest, ServiceResponse
from ..api_gateway import APIGateway
from ..middleware import AuthenticationMiddleware, ValidationMiddleware, MetricsMiddleware
from ..health import HealthChecker, HealthStatus
from ..metrics import MetricsCollector
from ..logging import setup_logging, get_logger
from ..exceptions import ServiceError, AuthenticationError, ValidationError

class TestServiceConfig:
    """Test service configuration"""
    
    def test_service_config_creation(self):
        config = ServiceConfig(
            name="test_service",
            version="1.0.0",
            debug=True,
            timeout=30
        )
        
        assert config.name == "test_service"
        assert config.version == "1.0.0"
        assert config.debug is True
        assert config.timeout == 30
        assert config.max_retries == 3  # default value

class TestBaseService:
    """Test base service functionality"""
    
    class MockService(BaseService):
        def __init__(self, config: ServiceConfig):
            super().__init__(config)
            self.initialized_called = False
            self.shutdown_called = False
            self.process_called = False
        
        async def _initialize_service(self):
            self.initialized_called = True
        
        async def _shutdown_service(self):
            self.shutdown_called = True
        
        async def _process_request(self, request):
            self.process_called = True
            return {"result": "success", "data": request.dict()}
    
    @pytest.fixture
    def service_config(self):
        return ServiceConfig(
            name="test_service",
            version="1.0.0",
            debug=True,
            timeout=5,
            max_retries=2
        )
    
    @pytest.fixture
    def mock_service(self, service_config):
        return self.MockService(service_config)
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, mock_service):
        """Test service initialization"""
        assert not mock_service._initialized
        
        await mock_service.initialize()
        
        assert mock_service._initialized
        assert mock_service.initialized_called
    
    @pytest.mark.asyncio
    async def test_service_shutdown(self, mock_service):
        """Test service shutdown"""
        await mock_service.initialize()
        await mock_service.shutdown()
        
        assert not mock_service._initialized
        assert mock_service.shutdown_called
    
    @pytest.mark.asyncio
    async def test_service_process_success(self, mock_service):
        """Test successful request processing"""
        request = ServiceRequest(user_id="test_user")
        
        response = await mock_service.process(request)
        
        assert isinstance(response, ServiceResponse)
        assert response.success is True
        assert response.request_id == request.request_id
        assert mock_service.process_called
    
    @pytest.mark.asyncio
    async def test_service_process_with_user_context(self, mock_service):
        """Test request processing with user context"""
        request = ServiceRequest(user_id="test_user")
        user_context = {"user_id": "test_user", "authenticated": True, "is_active": True}
        
        response = await mock_service.process(request, user_context)
        
        assert response.success is True
    
    @pytest.mark.asyncio
    async def test_service_authentication_error(self, mock_service):
        """Test authentication error handling"""
        request = ServiceRequest(user_id="test_user")
        user_context = {"authenticated": False}
        
        response = await mock_service.process(request, user_context)
        
        assert response.success is False
        assert "authentication" in response.message.lower()
    
    @pytest.mark.asyncio
    async def test_service_health_check(self, mock_service):
        """Test service health check"""
        await mock_service.initialize()
        
        health = await mock_service.health_check()
        
        assert health["service"] == "test_service"
        assert health["status"] == "healthy"
        assert "uptime" in health

class TestAPIGateway:
    """Test API Gateway functionality"""
    
    @pytest.fixture
    def gateway(self):
        return APIGateway(
            title="Test API",
            description="Test API Gateway",
            version="1.0.0",
            debug=True
        )
    
    def test_gateway_creation(self, gateway):
        """Test API Gateway creation"""
        assert gateway.app.title == "Test API"
        assert gateway.app.version == "1.0.0"
        assert gateway.app.debug is True
    
    def test_gateway_health_endpoint(self, gateway):
        """Test health endpoint"""
        client = TestClient(gateway.get_app())
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_gateway_metrics_endpoint(self, gateway):
        """Test metrics endpoint"""
        client = TestClient(gateway.get_app())
        response = client.get("/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "timestamp" in data

class TestMiddleware:
    """Test middleware components"""
    
    @pytest.fixture
    def test_app(self):
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        @app.get("/protected")
        async def protected_endpoint(request):
            user = getattr(request.state, 'user', None)
            return {"user": user}
        
        return app
    
    def test_authentication_middleware_success(self, test_app):
        """Test successful authentication"""
        def mock_validator(token):
            if token == "valid_token":
                return {"user_id": "123", "authenticated": True}
            return None
        
        test_app.add_middleware(
            AuthenticationMiddleware,
            token_validator=mock_validator,
            exclude_paths=["/test"]
        )
        
        client = TestClient(test_app)
        
        # Test excluded path
        response = client.get("/test")
        assert response.status_code == 200
        
        # Test protected path with valid token
        response = client.get(
            "/protected",
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 200
    
    def test_authentication_middleware_failure(self, test_app):
        """Test authentication failure"""
        def mock_validator(token):
            return None
        
        test_app.add_middleware(
            AuthenticationMiddleware,
            token_validator=mock_validator,
            exclude_paths=["/test"]
        )
        
        client = TestClient(test_app)
        
        # Test protected path without token
        response = client.get("/protected")
        assert response.status_code == 401
        
        # Test protected path with invalid token
        response = client.get(
            "/protected",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
    
    def test_validation_middleware(self, test_app):
        """Test request validation middleware"""
        test_app.add_middleware(
            ValidationMiddleware,
            max_request_size=1024,  # 1KB limit
            allowed_content_types=["application/json"]
        )
        
        client = TestClient(test_app)
        
        # Test valid request
        response = client.get("/test")
        assert response.status_code == 200
        
        # Test request with unsupported content type
        response = client.post(
            "/test",
            data="test data",
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code == 422
    
    def test_metrics_middleware(self, test_app):
        """Test metrics collection middleware"""
        test_app.add_middleware(MetricsMiddleware, service_name="test")
        
        client = TestClient(test_app)
        response = client.get("/test")
        
        assert response.status_code == 200
        assert "X-Response-Time" in response.headers

class TestHealthChecker:
    """Test health checking system"""
    
    @pytest.fixture
    def health_checker(self):
        return HealthChecker()
    
    @pytest.mark.asyncio
    async def test_add_health_check(self, health_checker):
        """Test adding health checks"""
        async def mock_check():
            return {"status": "healthy"}
        
        health_checker.add_check("test_check", mock_check)
        
        assert "test_check" in health_checker.checks
        assert health_checker.checks["test_check"].name == "test_check"
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, health_checker):
        """Test successful health check"""
        async def healthy_check():
            return {"status": "healthy", "message": "All good"}
        
        health_checker.add_check("healthy_service", healthy_check)
        
        result = await health_checker.check_all()
        
        assert result["status"] == "healthy"
        assert "healthy_service" in result["checks"]
        assert result["checks"]["healthy_service"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, health_checker):
        """Test failed health check"""
        async def unhealthy_check():
            return {"status": "unhealthy", "error": "Service down"}
        
        health_checker.add_check("unhealthy_service", unhealthy_check, critical=True)
        
        result = await health_checker.check_all()
        
        assert result["status"] == "unhealthy"
        assert "unhealthy_service" in result["checks"]
        assert result["checks"]["unhealthy_service"]["status"] == "unhealthy"
    
    @pytest.mark.asyncio
    async def test_health_check_timeout(self, health_checker):
        """Test health check timeout"""
        async def slow_check():
            await asyncio.sleep(10)  # Longer than timeout
            return {"status": "healthy"}
        
        health_checker.add_check("slow_service", slow_check, timeout=1)
        
        result = await health_checker.check_single("slow_service")
        
        assert result["status"] == "unhealthy"
        assert "timeout" in result["error"].lower()

class TestMetricsCollector:
    """Test metrics collection"""
    
    @pytest.fixture
    def metrics(self):
        return MetricsCollector("test_service")
    
    def test_counter_increment(self, metrics):
        """Test counter increment"""
        metrics.increment_counter("test_counter", 5)
        metrics.increment_counter("test_counter", 3)
        
        assert metrics.get_counter("test_counter") == 8
    
    def test_gauge_set(self, metrics):
        """Test gauge setting"""
        metrics.set_gauge("test_gauge", 42.5)
        
        assert metrics.get_gauge("test_gauge") == 42.5
    
    def test_histogram_record(self, metrics):
        """Test histogram recording"""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        for value in values:
            metrics.record_histogram("test_histogram", value)
        
        stats = metrics.get_histogram_stats("test_histogram")
        
        assert stats["count"] == 5
        assert stats["sum"] == 15.0
        assert stats["avg"] == 3.0
        assert stats["min"] == 1.0
        assert stats["max"] == 5.0
    
    def test_timer_context(self, metrics):
        """Test timer context manager"""
        from ..metrics import timer
        
        with timer(metrics, "test_timer"):
            time.sleep(0.1)
        
        stats = metrics.get_histogram_stats("test_timer")
        assert stats["count"] == 1
        assert stats["avg"] > 0.05  # Should be around 0.1 seconds
    
    def test_prometheus_format(self, metrics):
        """Test Prometheus format export"""
        metrics.increment_counter("requests_total", 10)
        metrics.set_gauge("memory_usage", 75.5)
        
        prometheus_output = metrics.get_prometheus_format()
        
        assert "requests_total" in prometheus_output
        assert "memory_usage" in prometheus_output
        assert "service_info" in prometheus_output

class TestLogging:
    """Test logging configuration"""
    
    def test_logging_setup(self):
        """Test logging setup"""
        logger = setup_logging(
            service_name="test_service",
            log_level="INFO",
            log_format="json",
            enable_console=True
        )
        
        assert logger.name == "test_service"
        
        # Test logging
        logger.info("Test message")
        logger.error("Test error", extra={"request_id": "123"})
    
    def test_get_logger(self):
        """Test logger retrieval"""
        logger = get_logger("test_module")
        
        assert logger.name == "test_module"

# Integration tests
class TestServiceIntegration:
    """Integration tests for the complete service architecture"""
    
    @pytest.mark.asyncio
    async def test_complete_service_flow(self):
        """Test complete service request flow"""
        # Create a test service
        config = ServiceConfig(name="integration_test", version="1.0.0")
        
        class TestService(BaseService):
            async def _initialize_service(self):
                pass
            
            async def _shutdown_service(self):
                pass
            
            async def _process_request(self, request):
                return {"processed": True, "input": request.dict()}
        
        service = TestService(config)
        
        # Test the complete flow
        request = ServiceRequest(user_id="test_user")
        user_context = {"user_id": "test_user", "authenticated": True, "is_active": True}
        
        response = await service.process(request, user_context)
        
        assert response.success is True
        assert response.data["processed"] is True
        assert "processing_time" in response.metadata
    
    def test_production_app_creation(self):
        """Test production app creation"""
        from ..production_app import create_production_app
        
        app = create_production_app()
        
        assert app.title == "Production Transcription API"
        assert app.version == "1.0.0"
        
        # Test with client
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        
        # Test info endpoint
        response = client.get("/info")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "production_api"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])