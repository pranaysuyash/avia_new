#!/usr/bin/env python3
"""
Test script to verify the refactored API works correctly
"""

import sys
import traceback
from fastapi.testclient import TestClient

def test_api_refactoring():
    """Test that the refactored API works correctly"""
    
    print("🧪 Testing API Refactoring...")
    
    try:
        # Test 1: Import the main app
        print("1️⃣ Testing API import...")
        from api.main import app
        print("   ✅ API imports successfully")
        
        # Test 2: Create test client
        print("2️⃣ Creating test client...")
        client = TestClient(app)
        print("   ✅ Test client created")
        
        # Test 3: Check health endpoint
        print("3️⃣ Testing health endpoint...")
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"   ✅ Health check passed: {data['status']}")
        
        # Test 4: Check API health endpoint
        print("4️⃣ Testing API health endpoint...")
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"   ✅ API health check passed: {data['status']}")
        
        # Test 5: Check router endpoints exist
        print("5️⃣ Testing router endpoints...")
        routes = [route.path for route in app.routes]
        
        # Check auth routes
        auth_routes = [r for r in routes if r.startswith('/api/auth')]
        assert len(auth_routes) >= 4, f"Expected at least 4 auth routes, got {len(auth_routes)}"
        print(f"   ✅ Auth routes: {len(auth_routes)} found")
        
        # Check user routes  
        user_routes = [r for r in routes if r.startswith('/api/users')]
        assert len(user_routes) >= 5, f"Expected at least 5 user routes, got {len(user_routes)}"
        print(f"   ✅ User routes: {len(user_routes)} found")
        
        # Check transcription routes
        transcription_routes = [r for r in routes if r.startswith('/api/transcriptions')]
        assert len(transcription_routes) >= 4, f"Expected at least 4 transcription routes, got {len(transcription_routes)}"
        print(f"   ✅ Transcription routes: {len(transcription_routes)} found")
        
        # Check team routes
        team_routes = [r for r in routes if r.startswith('/api/teams')]
        assert len(team_routes) >= 3, f"Expected at least 3 team routes, got {len(team_routes)}"
        print(f"   ✅ Team routes: {len(team_routes)} found")
        
        # Check storage routes
        storage_routes = [r for r in routes if r.startswith('/api/storage')]
        assert len(storage_routes) >= 3, f"Expected at least 3 storage routes, got {len(storage_routes)}"
        print(f"   ✅ Storage routes: {len(storage_routes)} found")
        
        print(f"   ✅ Total routes: {len(routes)}")
        
        # Test 6: Check OpenAPI docs are available
        print("6️⃣ Testing OpenAPI documentation...")
        response = client.get("/api/docs")
        assert response.status_code == 200
        print("   ✅ OpenAPI docs accessible")
        
        print("\n🎉 All tests passed! API refactoring is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_api_refactoring()
    sys.exit(0 if success else 1)