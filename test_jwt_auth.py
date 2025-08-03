#!/usr/bin/env python3
"""
Test script for JWT authentication with PostgreSQL
"""

import asyncio
import httpx
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

async def test_auth_flow():
    """Test the complete authentication flow"""
    async with httpx.AsyncClient() as client:
        print("=== JWT Authentication Test ===\n")
        
        # 1. Test Registration
        print("1. Testing user registration...")
        register_data = {
            "email": f"test_{int(datetime.now().timestamp())}@example.com",
            "username": f"testuser_{int(datetime.now().timestamp())}",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/auth/register", json=register_data)
            if response.status_code == 200:
                print(f"✅ Registration successful: {response.json()['message']}")
                print(f"   User ID: {response.json()['data']['id']}")
            else:
                print(f"❌ Registration failed: {response.status_code} - {response.text}")
                return
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return
        
        # 2. Test Login
        print("\n2. Testing user login...")
        login_data = {
            "username_or_email": register_data["username"],
            "password": register_data["password"]
        }
        
        try:
            response = await client.post(f"{BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                auth_data = response.json()['data']
                access_token = auth_data['access_token']
                refresh_token = auth_data['refresh_token']
                print(f"✅ Login successful")
                print(f"   Access token: {access_token[:20]}...")
                print(f"   Refresh token: {refresh_token[:20]}...")
                print(f"   User: {auth_data['user']['username']} ({auth_data['user']['email']})")
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return
        except Exception as e:
            print(f"❌ Login error: {e}")
            return
        
        # 3. Test authenticated endpoint (get current user)
        print("\n3. Testing authenticated endpoint...")
        headers = {"Authorization": f"Bearer {access_token}"}
        
        try:
            response = await client.get(f"{BASE_URL}/auth/me", headers=headers)
            if response.status_code == 200:
                user_info = response.json()['data']
                print(f"✅ Authentication successful")
                print(f"   Current user: {user_info['username']} (ID: {user_info['user_id']})")
                print(f"   Role: {user_info['role']}")
                print(f"   Verified: {user_info['is_verified']}")
            else:
                print(f"❌ Authentication failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Authentication error: {e}")
        
        # 4. Test token refresh
        print("\n4. Testing token refresh...")
        refresh_data = {"refresh_token": refresh_token}
        
        try:
            response = await client.post(f"{BASE_URL}/auth/refresh", json=refresh_data)
            if response.status_code == 200:
                new_token_data = response.json()['data']
                new_access_token = new_token_data['access_token']
                print(f"✅ Token refresh successful")
                print(f"   New access token: {new_access_token[:20]}...")
            else:
                print(f"❌ Token refresh failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Token refresh error: {e}")
        
        # 5. Test API key creation
        print("\n5. Testing API key creation...")
        api_key_data = {
            "name": "Test API Key",
            "permissions": {"read": True, "write": True},
            "expires_in_days": 30
        }
        
        try:
            response = await client.post(f"{BASE_URL}/auth/api-keys", json=api_key_data, headers=headers)
            if response.status_code == 200:
                key_data = response.json()['data']
                api_key = key_data['key']
                print(f"✅ API key created successfully")
                print(f"   Key: {api_key[:10]}...")
                print(f"   Name: {key_data['name']}")
            else:
                print(f"❌ API key creation failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ API key creation error: {e}")
        
        # 6. Test protected transcription endpoint
        print("\n6. Testing protected transcription endpoint...")
        
        # First, test without authentication
        try:
            response = await client.get(f"{BASE_URL}/transcription/list")
            if response.status_code == 401:
                print(f"✅ Correctly rejected unauthenticated request")
            else:
                print(f"❌ Expected 401, got {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Then test with authentication
        try:
            response = await client.get(f"{BASE_URL}/transcription/list", headers=headers)
            if response.status_code == 200:
                print(f"✅ Successfully accessed protected endpoint with JWT")
                data = response.json()['data']
                print(f"   Transcriptions: {data['total_count']} items")
            else:
                print(f"❌ Protected endpoint failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Protected endpoint error: {e}")
        
        # 7. Test logout
        print("\n7. Testing logout...")
        try:
            response = await client.post(f"{BASE_URL}/auth/logout", headers=headers)
            if response.status_code == 200:
                print(f"✅ Logout successful")
            else:
                print(f"❌ Logout failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Logout error: {e}")
        
        # 8. Test that the token is now invalid
        print("\n8. Testing invalidated token...")
        try:
            response = await client.get(f"{BASE_URL}/auth/me", headers=headers)
            if response.status_code == 401:
                print(f"✅ Token correctly invalidated after logout")
            else:
                print(f"❌ Expected 401, got {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n=== Authentication test complete ===")


async def main():
    """Main test function"""
    try:
        await test_auth_flow()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("Starting JWT authentication test...")
    print(f"Using API at: {BASE_URL}")
    print("Make sure the API server is running on port 8000\n")
    
    asyncio.run(main())