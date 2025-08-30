"""
Simple test script to verify the standalone production app works correctly
"""

import sys
from fastapi.testclient import TestClient

def test_production_app():
    """Test the standalone production app"""
    print("🚀 Testing Standalone Production App")
    print("=" * 50)
    
    try:
        # Import the standalone app
        from api.production_app_standalone import app
        
        # Create test client
        client = TestClient(app)
        
        print("✅ App imported successfully")
        
        # Test basic health endpoint
        print("\n🏥 Testing health endpoints...")
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"   ✅ Basic health check: {data['status']}")
        
        # Test detailed health endpoint
        response = client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"   ✅ Detailed health check: {data['summary']['success_rate']}% success rate")
        
        # Test metrics endpoint
        print("\n📊 Testing metrics endpoint...")
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        print(f"   ✅ Metrics endpoint: {len(data['counters'])} counters tracked")
        
        # Test demo endpoints
        print("\n🎯 Testing demo endpoints...")
        response = client.get("/demo/hello")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"   ✅ Hello endpoint: {data['message']}")
        
        print("\n" + "=" * 50)
        print("✅ All tests passed! Production app is working correctly.")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_production_app()
    sys.exit(0 if success else 1)