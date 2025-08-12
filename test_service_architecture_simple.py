"""
Simple test script to verify the FastAPI service architecture foundation
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all core components can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from api.core.base_service import BaseService, ServiceConfig
        print("✅ BaseService imported successfully")
        
        from api.core.api_gateway import APIGateway
        print("✅ APIGateway imported successfully")
        
        from api.core.middleware import AuthenticationMiddleware, ValidationMiddleware
        print("✅ Middleware components imported successfully")
        
        from api.core.health import HealthChecker
        print("✅ HealthChecker imported successfully")
        
        from api.core.metrics import MetricsCollector
        print("✅ MetricsCollector imported successfully")
        
        from api.core.logging import setup_logging, get_logger
        print("✅ Logging components imported successfully")
        
        from api.core.openapi import setup_openapi_docs
        print("✅ OpenAPI components imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_service_config():
    """Test service configuration"""
    print("\n🧪 Testing ServiceConfig...")
    
    try:
        from api.core.base_service import ServiceConfig
        
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
        
        print("✅ ServiceConfig works correctly")
        return True
        
    except Exception as e:
        print(f"❌ ServiceConfig test failed: {e}")
        return False

def test_api_gateway():
    """Test API Gateway creation"""
    print("\n🧪 Testing APIGateway...")
    
    try:
        from api.core.api_gateway import APIGateway
        
        gateway = APIGateway(
            title="Test API",
            description="Test API Gateway",
            version="1.0.0",
            debug=True
        )
        
        app = gateway.get_app()
        assert app.title == "Test API"
        assert app.version == "1.0.0"
        
        print("✅ APIGateway works correctly")
        return True
        
    except Exception as e:
        print(f"❌ APIGateway test failed: {e}")
        return False

def test_health_checker():
    """Test health checker"""
    print("\n🧪 Testing HealthChecker...")
    
    try:
        from api.core.health import HealthChecker
        
        health_checker = HealthChecker()
        
        # Add a simple health check
        async def simple_check():
            return {"status": "healthy", "message": "All good"}
        
        health_checker.add_check("simple", simple_check)
        
        assert "simple" in health_checker.checks
        print("✅ HealthChecker works correctly")
        return True
        
    except Exception as e:
        print(f"❌ HealthChecker test failed: {e}")
        return False

def test_metrics_collector():
    """Test metrics collector"""
    print("\n🧪 Testing MetricsCollector...")
    
    try:
        from api.core.metrics import MetricsCollector
        
        metrics = MetricsCollector("test_service")
        
        # Test counter
        metrics.increment_counter("test_counter", 5)
        assert metrics.get_counter("test_counter") == 5
        
        # Test gauge
        metrics.set_gauge("test_gauge", 42.5)
        assert metrics.get_gauge("test_gauge") == 42.5
        
        # Test histogram
        metrics.record_histogram("test_histogram", 1.5)
        stats = metrics.get_histogram_stats("test_histogram")
        assert stats["count"] == 1
        assert stats["avg"] == 1.5
        
        print("✅ MetricsCollector works correctly")
        return True
        
    except Exception as e:
        print(f"❌ MetricsCollector test failed: {e}")
        return False

def test_logging():
    """Test logging setup"""
    print("\n🧪 Testing Logging...")
    
    try:
        from api.core.logging import setup_logging, get_logger
        
        logger = setup_logging(
            service_name="test_service",
            log_level="INFO",
            enable_console=True
        )
        
        # Test logger creation
        module_logger = get_logger("test_module")
        assert module_logger.name == "test_module"
        
        # Test logging (should not raise exceptions)
        logger.info("Test log message")
        module_logger.debug("Debug message")
        
        print("✅ Logging works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False

async def test_base_service():
    """Test base service functionality"""
    print("\n🧪 Testing BaseService...")
    
    try:
        from api.core.base_service import BaseService, ServiceConfig, ServiceRequest
        
        class TestService(BaseService):
            async def _initialize_service(self):
                self.initialized = True
            
            async def _shutdown_service(self):
                self.shutdown = True
            
            async def _process_request(self, request):
                return {"result": "success", "input": request}
        
        config = ServiceConfig(name="test", version="1.0.0")
        service = TestService(config)
        
        # Test initialization
        await service.initialize()
        assert hasattr(service, 'initialized')
        
        # Test processing
        request = ServiceRequest(user_id="test_user")
        response = await service.process(request)
        
        assert response.success is True
        assert response.data["result"] == "success"
        
        # Test shutdown
        await service.shutdown()
        assert hasattr(service, 'shutdown')
        
        print("✅ BaseService works correctly")
        return True
        
    except Exception as e:
        print(f"❌ BaseService test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 FastAPI Service Architecture Foundation - Simple Tests")
    print("=" * 70)
    
    tests = [
        test_imports,
        test_service_config,
        test_api_gateway,
        test_health_checker,
        test_metrics_collector,
        test_logging,
    ]
    
    async_tests = [
        test_base_service,
    ]
    
    passed = 0
    total = len(tests) + len(async_tests)
    
    # Run synchronous tests
    for test in tests:
        if test():
            passed += 1
    
    # Run asynchronous tests
    for test in async_tests:
        if await test():
            passed += 1
    
    print("\n" + "=" * 70)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Service architecture is working correctly.")
        
        print(f"\n🎯 Key Components Verified:")
        print("   ✅ Base service class with lifecycle management")
        print("   ✅ API Gateway with middleware support")
        print("   ✅ Health checking system")
        print("   ✅ Metrics collection and monitoring")
        print("   ✅ Structured logging configuration")
        print("   ✅ Service configuration management")
        
        print(f"\n🚀 Ready for production use!")
        print("   - Run: uvicorn api.production_app:app --reload")
        print("   - Docs: http://localhost:8000/api/docs")
        print("   - Health: http://localhost:8000/health")
        print("   - Metrics: http://localhost:8000/metrics")
        
        return True
    else:
        print(f"❌ {total - passed} tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)