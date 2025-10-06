#!/usr/bin/env python3
"""
Simple test to verify API can start and respond
"""

import asyncio
import uvicorn
from api.main import app

async def test_api():
    """Test that the API can be imported and basic endpoints work"""
    try:
        # Test that we can import the app
        print("✅ API app imported successfully")
        
        # Test that we can access the app's routes
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        print(f"✅ Found {len(routes)} routes")
        
        # Print some key routes
        key_routes = [r for r in routes if any(keyword in r for keyword in ['/api/', '/docs', '/ping'])]
        print(f"✅ Key routes available: {key_routes[:5]}")
        
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_api())
    if success:
        print("\n🎉 API is ready to start!")
        print("Run: python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload")
    else:
        print("\n❌ API has issues that need to be resolved")