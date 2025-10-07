#!/usr/bin/env python3
"""
Test script to verify CORS configuration fix
"""

import requests
import sys
import time
import subprocess
import threading
from pathlib import Path

def test_cors_preflight(origin_port):
    """Test CORS preflight request for a specific origin port"""
    origin = f"http://localhost:{origin_port}"
    api_url = "http://localhost:8000/api/health"
    
    try:
        # Send preflight request
        response = requests.options(
            api_url,
            headers={
                'Origin': origin,
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type'
            },
            timeout=5
        )
        
        # Check if CORS headers are present
        cors_origin = response.headers.get('Access-Control-Allow-Origin')
        cors_methods = response.headers.get('Access-Control-Allow-Methods')
        cors_headers = response.headers.get('Access-Control-Allow-Headers')
        
        print(f"🔍 Testing origin: {origin}")
        print(f"   Status: {response.status_code}")
        print(f"   Access-Control-Allow-Origin: {cors_origin}")
        print(f"   Access-Control-Allow-Methods: {cors_methods}")
        print(f"   Access-Control-Allow-Headers: {cors_headers}")
        
        if cors_origin == origin or cors_origin == "*":
            print(f"   ✅ CORS configured correctly for {origin}")
            return True
        else:
            print(f"   ❌ CORS not configured for {origin}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Failed to connect to API: {e}")
        return False

def start_api_server():
    """Start the API server for testing"""
    print("🚀 Starting API server for CORS testing...")
    
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Wait for server to start
        print("⏳ Waiting for API server to start...")
        time.sleep(5)
        
        # Check if server is running
        try:
            response = requests.get("http://localhost:8000/api/health", timeout=5)
            if response.status_code == 200:
                print("✅ API server started successfully")
                return process
            else:
                print(f"❌ API server health check failed: {response.status_code}")
                return None
        except requests.exceptions.RequestException:
            print("❌ API server not responding")
            return None
            
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return None

def main():
    print("=" * 60)
    print("🔧 CORS Configuration Test")
    print("=" * 60)
    
    # Start API server
    api_process = start_api_server()
    if not api_process:
        print("❌ Cannot test CORS without running API server")
        sys.exit(1)
    
    try:
        print("\n🧪 Testing CORS for different frontend ports...")
        print("-" * 60)
        
        # Test different frontend ports
        test_ports = [3000, 3001, 3003, 5173]
        results = []
        
        for port in test_ports:
            success = test_cors_preflight(port)
            results.append((port, success))
            print()
        
        # Summary
        print("=" * 60)
        print("📊 CORS Test Results Summary")
        print("=" * 60)
        
        all_passed = True
        for port, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"Port {port}: {status}")
            if not success:
                all_passed = False
        
        print()
        if all_passed:
            print("🎉 All CORS tests passed! Frontend should now connect successfully.")
        else:
            print("⚠️  Some CORS tests failed. Check the API server configuration.")
            
    finally:
        # Clean up
        if api_process and api_process.poll() is None:
            print("\n🛑 Stopping API server...")
            api_process.terminate()
            try:
                api_process.wait(timeout=5)
                print("✅ API server stopped")
            except subprocess.TimeoutExpired:
                api_process.kill()
                print("✅ API server force stopped")

if __name__ == "__main__":
    main()