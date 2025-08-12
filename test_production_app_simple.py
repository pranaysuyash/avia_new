"""
Simple test for the production app without external dependencies
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_core_production_app():
    """Test the core production app functionality"""
    print("🧪 Testing Production App Core Components...")
    
    try:
        # Import core components
        from api.core import APIGateway, setup_logging, MetricsCollector, HealthChecker
        from fastapi.testclient import TestClient
        
        # Setup logging
        logger = setup_logging(
            service_name="test_production_api",
            log_level="INFO",
            enable_console=False  # Disable console logging for cleaner output
        )
        
        # Create API Gateway (similar to production app but without external dependencies)
        gateway = APIGateway(
            title="Test Production API",
            description="Test production-ready API",
            version="1.0.0",
            debug=True
        )
        
        # Add a simple test endpoint
        @gateway.app.get("/test")
        async def test_endpoint():
            return {"message": "Test endpoint working", "status": "success"}
        
        # Get the app and create test client
        app = gateway.get_app()
        client = TestClient(app)
        
        print("✅ Production app components created successfully")
        
        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✅ Health endpoint: {response.status_code} - {data['status']}")
        
        # Test metrics endpoint
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        print(f"✅ Metrics endpoint: {response.status_code} - service: {data['service']}")
        
        # Test custom endpoint
        response = client.get("/test")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        print(f"✅ Custom endpoint: {response.status_code} - {data['message']}")
        
        # Test error handling
        response = client.get("/nonexistent")
        assert response.status_code == 404
        print(f"✅ Error handling: {response.status_code} - 404 for nonexistent endpoint")
        
        # Test request headers (middleware)
        response = client.get("/test")
        assert "X-Request-ID" in response.headers
        assert "X-Process-Time" in response.headers
        print(f"✅ Middleware headers: X-Request-ID and X-Process-Time present")
        
        return True
        
    except Exception as e:
        print(f"❌ Production app test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_service_architecture_integration():
    """Test the complete service architecture integration"""
    print("\n🧪 Testing Service Architecture Integration...")
    
    try:
        from api.core import (
            BaseService, ServiceConfig, ServiceRequest,
            APIGateway, HealthChecker, MetricsCollector
        )
        
        # Create a test service
        class TestIntegrationService(BaseService):
            async def _initialize_service(self):
                self.test_data = {"initialized": True}
            
            async def _shutdown_service(self):
                self.test_data = {"shutdown": True}
            
            async def _process_request(self, request):
                return {
                    "processed": True,
                    "request_id": request.request_id,
                    "user_id": request.user_id
                }
        
        # Test service with gateway integration
        config = ServiceConfig(name="integration_test", version="1.0.0")
        service = TestIntegrationService(config)
        
        # Initialize service
        import asyncio
        async def run_integration_test():
            await service.initialize()
            
            # Process a request
            request = ServiceRequest(user_id="test_user")
            response = await service.process(request)
            
            assert response.success is True
            assert response.data["processed"] is True
            
            # Check health
            health = await service.health_check()
            assert health["status"] == "healthy"
            
            await service.shutdown()
            return True
        
        result = asyncio.run(run_integration_test())
        
        print("✅ Service architecture integration working correctly")
        return result
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all production app tests"""
    print("🚀 Production App Testing")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 2
    
    # Run tests
    if test_core_production_app():
        tests_passed += 1
    
    if test_service_architecture_integration():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("✅ All production app tests passed!")
        print("\n🎯 Verified Components:")
        print("   ✅ API Gateway with middleware stack")
        print("   ✅ Health and metrics endpoints")
        print("   ✅ Error handling and request processing")
        print("   ✅ Service architecture integration")
        print("   ✅ Request/response middleware")
        
        print(f"\n🚀 Production app is ready!")
        print("   - Core architecture: ✅ Working")
        print("   - Middleware stack: ✅ Working") 
        print("   - Health monitoring: ✅ Working")
        print("   - Metrics collection: ✅ Working")
        print("   - Error handling: ✅ Working")
        
        return True
    else:
        print(f"❌ {total_tests - tests_passed} tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)