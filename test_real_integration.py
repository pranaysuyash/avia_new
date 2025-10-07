#!/usr/bin/env python3
"""
Test real frontend-backend integration with actual data flow
"""
import requests
import json
import time

def test_backend_endpoints():
    """Test all backend endpoints that frontend uses"""
    
    print("=== Testing Backend Endpoints ===")
    
    # Headers to simulate frontend requests
    headers = {
        "Origin": "http://localhost:3005",
        "Content-Type": "application/json"
    }
    
    endpoints = [
        ("/api/health", "GET"),
        ("/api/dashboard/stats", "GET"),
        ("/api/dashboard/recent-jobs", "GET"),
        ("/api/dashboard/system-status", "GET"),
        ("/api/ai/engines/status", "GET"),
        ("/api/users/profile", "GET"),
        ("/api/media/list", "GET")
    ]
    
    results = {}
    
    for endpoint, method in endpoints:
        try:
            url = f"http://localhost:8000{endpoint}"
            response = requests.get(url, headers=headers, timeout=5)
            
            print(f"\n{method} {endpoint}")
            print(f"  Status: {response.status_code}")
            
            # Check CORS headers
            cors_header = response.headers.get('Access-Control-Allow-Origin')
            if cors_header:
                print(f"  CORS: ✅ {cors_header}")
            else:
                print(f"  CORS: ❌ Missing")
            
            if response.status_code == 200:
                data = response.json()
                print(f"  Data: ✅ {len(str(data))} chars")
                results[endpoint] = data
            else:
                print(f"  Error: {response.text}")
                results[endpoint] = None
                
        except Exception as e:
            print(f"  Failed: {e}")
            results[endpoint] = None
    
    return results

def test_file_upload():
    """Test file upload endpoint"""
    print("\n=== Testing File Upload ===")
    
    # Create a test file
    test_content = b"This is a test audio file content"
    files = {'file': ('test_audio.mp3', test_content, 'audio/mpeg')}
    headers = {"Origin": "http://localhost:3005"}
    
    try:
        response = requests.post(
            "http://localhost:8000/api/media_ingestion",
            files=files,
            headers=headers,
            timeout=10
        )
        
        print(f"Upload Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Upload Response: ✅")
            print(f"  File ID: {data.get('file', {}).get('id')}")
            print(f"  File Name: {data.get('file', {}).get('name')}")
            return data
        else:
            print(f"Upload Error: {response.text}")
            
    except Exception as e:
        print(f"Upload Failed: {e}")
    
    return None

def verify_data_structure():
    """Verify the data structure matches frontend expectations"""
    print("\n=== Verifying Data Structure ===")
    
    # Test dashboard stats structure
    try:
        response = requests.get("http://localhost:8000/api/dashboard/stats", 
                              headers={"Origin": "http://localhost:3005"})
        if response.status_code == 200:
            data = response.json()
            stats = data.get('stats', {})
            
            expected_fields = ['totalFiles', 'totalProcessingTime', 'accuracyRate', 'activeJobs']
            missing_fields = [field for field in expected_fields if field not in stats]
            
            if missing_fields:
                print(f"  Dashboard Stats: ❌ Missing fields: {missing_fields}")
            else:
                print(f"  Dashboard Stats: ✅ All required fields present")
                print(f"    Total Files: {stats.get('totalFiles')}")
                print(f"    Active Jobs: {stats.get('activeJobs')}")
        
    except Exception as e:
        print(f"  Dashboard Stats: ❌ {e}")

if __name__ == "__main__":
    print("Testing Real Frontend-Backend Integration...")
    
    # Test all endpoints
    results = test_backend_endpoints()
    
    # Test file upload
    upload_result = test_file_upload()
    
    # Verify data structure
    verify_data_structure()
    
    # Summary
    print("\n=== Integration Summary ===")
    working_endpoints = sum(1 for r in results.values() if r is not None)
    total_endpoints = len(results)
    
    print(f"Working Endpoints: {working_endpoints}/{total_endpoints}")
    print(f"File Upload: {'✅' if upload_result else '❌'}")
    
    if working_endpoints == total_endpoints and upload_result:
        print("🎉 Backend integration is working!")
        print("\nNext steps:")
        print("1. Start frontend on port 3005")
        print("2. Verify frontend receives real data")
        print("3. Remove mock data fallbacks")
    else:
        print("❌ Integration issues found - check logs above")