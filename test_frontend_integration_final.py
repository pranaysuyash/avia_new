#!/usr/bin/env python3
"""
Final test to verify frontend-backend integration with real data
"""
import requests
import json

def test_frontend_backend_integration():
    """Test that frontend can get real data from backend"""
    
    print("=== Final Frontend-Backend Integration Test ===")
    
    # Test the exact endpoints the frontend will call
    frontend_endpoints = [
        ("/api/health", "Health check"),
        ("/api/dashboard/stats", "Dashboard statistics"),
        ("/api/dashboard/recent-jobs", "Recent processing jobs"),
        ("/api/dashboard/system-status", "System status"),
        ("/api/ai/engines/status", "AI engines status"),
        ("/api/users/profile", "User profile"),
    ]
    
    headers = {
        "Origin": "http://localhost:3005",
        "Content-Type": "application/json"
    }
    
    all_working = True
    
    for endpoint, description in frontend_endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", headers=headers, timeout=5)
            
            print(f"\n{description} ({endpoint})")
            print(f"  Status: {response.status_code}")
            
            # Check CORS
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            if cors_origin:
                print(f"  CORS: ✅ {cors_origin}")
            else:
                print(f"  CORS: ❌ Missing")
                all_working = False
            
            if response.status_code == 200:
                data = response.json()
                print(f"  Response: ✅ Valid JSON ({len(str(data))} chars)")
                
                # Show sample data structure
                if isinstance(data, dict):
                    keys = list(data.keys())[:3]  # Show first 3 keys
                    print(f"  Keys: {keys}{'...' if len(data.keys()) > 3 else ''}")
                
            else:
                print(f"  Response: ❌ {response.status_code} - {response.text}")
                all_working = False
                
        except Exception as e:
            print(f"\n{description} ({endpoint})")
            print(f"  Error: ❌ {e}")
            all_working = False
    
    # Test file upload
    print(f"\nFile Upload Test (/api/media_ingestion)")
    try:
        files = {'file': ('test.mp3', b'fake audio data', 'audio/mpeg')}
        response = requests.post("http://localhost:8000/api/media_ingestion", 
                               files=files, headers={"Origin": "http://localhost:3005"})
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Upload: ✅ File ID: {data.get('file', {}).get('id')}")
        else:
            print(f"  Upload: ❌ {response.status_code}")
            all_working = False
            
    except Exception as e:
        print(f"  Upload: ❌ {e}")
        all_working = False
    
    # Summary
    print(f"\n=== Integration Summary ===")
    if all_working:
        print("🎉 ALL TESTS PASSED!")
        print("\nFrontend should now show REAL DATA instead of mock data!")
        print("\nTo verify:")
        print("1. Open frontend at http://localhost:3005")
        print("2. Check browser console for '✅ Backend connected - using real data'")
        print("3. Verify dashboard shows actual backend data")
        print("4. No more 'Backend not available' messages")
    else:
        print("❌ Some tests failed - check errors above")
    
    return all_working

if __name__ == "__main__":
    test_frontend_backend_integration()