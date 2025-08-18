#!/usr/bin/env python3
"""
Simple Service Testing Script

Tests if the core services are responding correctly.
"""

import requests
import time
import sys

def test_service(name, url, timeout=10):
    """Test if a service is responding."""
    try:
        print(f"Testing {name} at {url}...")
        response = requests.get(url, timeout=timeout)
        
        if response.status_code == 200:
            print(f"✅ {name} is healthy (status: {response.status_code})")
            try:
                data = response.json()
                if 'status' in data:
                    print(f"   Status: {data['status']}")
            except:
                pass
            return True
        else:
            print(f"⚠️  {name} responded with status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ {name} connection refused - service not running")
        return False
    except requests.exceptions.Timeout:
        print(f"⏰ {name} timed out after {timeout}s")
        return False
    except Exception as e:
        print(f"❌ {name} error: {e}")
        return False

def main():
    """Test all services."""
    print("🧪 Testing Core Services")
    print("=" * 30)
    
    services = [
        ("FastAPI Backend", "http://localhost:8000/health"),
        ("FastAPI API Health", "http://localhost:8000/api/health"),
        ("Streamlit App", "http://localhost:8501/_stcore/health"),
        ("React Frontend", "http://localhost:3000"),
        ("PostgreSQL (via API)", "http://localhost:8000/api/health"),
        ("Redis (via API)", "http://localhost:8000/api/health"),
    ]
    
    results = []
    
    for name, url in services:
        result = test_service(name, url)
        results.append((name, result))
        time.sleep(1)  # Brief pause between tests
        print()
    
    # Summary
    print("📊 Test Summary:")
    print("-" * 20)
    
    healthy_count = 0
    for name, result in results:
        status = "✅ HEALTHY" if result else "❌ UNHEALTHY"
        print(f"{name}: {status}")
        if result:
            healthy_count += 1
    
    print(f"\nOverall: {healthy_count}/{len(results)} services healthy")
    
    if healthy_count == len(results):
        print("🎉 All services are working!")
        return 0
    else:
        print("⚠️  Some services need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())