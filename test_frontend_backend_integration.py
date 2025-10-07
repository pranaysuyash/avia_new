#!/usr/bin/env python3
"""
Comprehensive test to verify frontend-backend integration
Tests CORS, API endpoints, and data flow
"""
import requests
import json
import time
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def test_cors_and_api_integration():
    """Test CORS configuration and API endpoints"""
    
    print("=== Frontend-Backend Integration Test ===")
    
    # Test 1: Check if backend is running
    print("\n1. Testing backend availability...")
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        print(f"✅ Backend is running: {response.status_code}")
        print(f"   Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend not available: {e}")
        return False
    
    # Test 2: Test CORS headers with frontend origin
    print("\n2. Testing CORS headers for frontend origin...")
    headers = {
        "Origin": "http://localhost:3005",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Content-Type"
    }
    
    try:
        # Preflight request
        response = requests.options("http://localhost:8000/api/health", headers=headers, timeout=5)
        print(f"   Preflight response: {response.status_code}")
        print(f"   CORS headers: {dict(response.headers)}")
        
        # Check for required CORS headers
        cors_headers = response.headers
        if "Access-Control-Allow-Origin" in cors_headers:
            print(f"✅ CORS Allow-Origin: {cors_headers['Access-Control-Allow-Origin']}")
        else:
            print("❌ Missing Access-Control-Allow-Origin header")
            
        # Actual request with origin
        response = requests.get("http://localhost:8000/api/health", headers={"Origin": "http://localhost:3005"}, timeout=5)
        print(f"   Actual request: {response.status_code}")
        print(f"   Response headers: {dict(response.headers)}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ CORS test failed: {e}")
        return False
    
    # Test 3: Test key API endpoints that frontend uses
    print("\n3. Testing key API endpoints...")
    
    endpoints_to_test = [
        "/api/health",
        "/api/dashboard/stats", 
        "/api/dashboard/recent-jobs",
        "/api/ai/engines/status"
    ]
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", 
                                  headers={"Origin": "http://localhost:3005"}, 
                                  timeout=5)
            print(f"   {endpoint}: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"      Data keys: {list(data.keys()) if isinstance(data, dict) else 'Non-dict response'}")
            else:
                print(f"      Error: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"   {endpoint}: ❌ Failed - {e}")
    
    # Test 4: Check environment variable loading
    print("\n4. Testing environment configuration...")
    allowed_origins = os.getenv("ALLOWED_ORIGINS")
    print(f"   ALLOWED_ORIGINS: {allowed_origins}")
    
    if allowed_origins and "http://localhost:3005" in allowed_origins:
        print("✅ Port 3005 is in ALLOWED_ORIGINS")
    else:
        print("❌ Port 3005 NOT in ALLOWED_ORIGINS")
    
    return True

def test_backend_server_type():
    """Determine which backend server is running"""
    print("\n5. Identifying backend server type...")
    
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        data = response.json()
        
        # Check response structure to identify server type
        if "service" in data:
            print(f"   Running: api/main.py (Production server)")
            print(f"   Service: {data.get('service')}")
        elif "ok" in data:
            print(f"   Running: backend_server.py (Development server)")
        else:
            print(f"   Unknown server type: {data}")
            
    except Exception as e:
        print(f"   Could not identify server: {e}")

if __name__ == "__main__":
    test_cors_and_api_integration()
    test_backend_server_type()