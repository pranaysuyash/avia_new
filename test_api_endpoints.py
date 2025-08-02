"""
Test API Endpoints
Simple script to test the REST API functionality
"""

import requests
import json
import os
import time
from datetime import datetime

# API Base URL
BASE_URL = "http://localhost:8000"

# Test data
TEST_USER = "test_user"
TEST_PASSWORD = "test_password123"
TEST_ADMIN = "admin"
TEST_ADMIN_PASSWORD = "admin_password123"


def print_response(response):
    """Pretty print API response"""
    print(f"Status Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    print("-" * 50)


def test_health_check():
    """Test health check endpoint"""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/health")
    print_response(response)
    return response.status_code == 200


def test_root():
    """Test root endpoint"""
    print("\n=== Testing Root Endpoint ===")
    response = requests.get(f"{BASE_URL}/")
    print_response(response)
    return response.status_code == 200


def test_authentication():
    """Test authentication endpoints"""
    print("\n=== Testing Authentication ===")
    
    # Test login
    print("\n1. Testing Login:")
    login_data = {
        "username": TEST_ADMIN,
        "password": TEST_ADMIN_PASSWORD
    }
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    print_response(response)
    
    if response.status_code != 200:
        print("Login failed!")
        return None
    
    token = response.json()["data"]["token"]
    print(f"Got token: {token[:20]}...")
    
    return token


def test_api_key_generation(token):
    """Test API key generation"""
    print("\n=== Testing API Key Generation ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    api_key_data = {
        "description": "Test API key for development"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/api-key",
        json=api_key_data,
        headers=headers
    )
    print_response(response)
    
    if response.status_code == 200:
        api_key = response.json()["data"]["api_key"]
        print(f"Got API key: {api_key[:20]}...")
        return api_key
    
    return None


def test_transcription_upload(token):
    """Test file upload for transcription"""
    print("\n=== Testing File Upload ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Create a test audio file (you would use a real file in production)
    test_file_path = "test_audio.txt"
    with open(test_file_path, "w") as f:
        f.write("This is a test audio file")
    
    try:
        with open(test_file_path, "rb") as f:
            files = {
                "file": ("test_audio.mp3", f, "audio/mpeg")
            }
            response = requests.post(
                f"{BASE_URL}/api/v1/transcription/upload",
                files=files,
                headers=headers
            )
            print_response(response)
            
            if response.status_code == 200:
                file_id = response.json()["data"]["file_id"]
                print(f"File uploaded successfully. File ID: {file_id}")
                return file_id
    finally:
        # Cleanup
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
    
    return None


def test_transcription_process(token, file_id):
    """Test transcription processing"""
    print("\n=== Testing Transcription Processing ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    process_data = {
        "use_api": False,
        "language": "en",
        "model": "base",
        "enable_diarization": False,
        "extract_entities": True
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/transcription/process",
        json=process_data,
        headers=headers,
        params={"file_id": file_id}
    )
    print_response(response)
    
    if response.status_code == 200:
        transcript_id = response.json()["data"]["transcript_id"]
        print(f"Transcription completed. ID: {transcript_id}")
        return transcript_id
    
    return None


def test_search(token):
    """Test search functionality"""
    print("\n=== Testing Search ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    search_data = {
        "query": "test",
        "limit": 10,
        "offset": 0,
        "sort_by": "relevance",
        "include_snippets": True
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/search/query",
        json=search_data,
        headers=headers
    )
    print_response(response)
    
    return response.status_code == 200


def test_export(token, transcript_id):
    """Test export functionality"""
    print("\n=== Testing Export ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    export_data = {
        "transcript_id": transcript_id,
        "format": "json",
        "include_metadata": True,
        "include_entities": True,
        "include_speakers": True
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/export/generate",
        json=export_data,
        headers=headers
    )
    print_response(response)
    
    return response.status_code == 200


def test_user_info(token):
    """Test user info endpoint"""
    print("\n=== Testing User Info ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(
        f"{BASE_URL}/api/v1/auth/me",
        headers=headers
    )
    print_response(response)
    
    return response.status_code == 200


def test_metrics(api_key):
    """Test metrics endpoint with API key"""
    print("\n=== Testing Metrics (API Key Auth) ===")
    
    headers = {
        "Authorization": f"ApiKey {api_key}"
    }
    
    response = requests.get(
        f"{BASE_URL}/metrics",
        headers=headers
    )
    print_response(response)
    
    return response.status_code == 200


def main():
    """Run all API tests"""
    print("Starting API Tests...")
    print(f"Testing against: {BASE_URL}")
    print("=" * 50)
    
    # Test basic endpoints
    if not test_health_check():
        print("Health check failed!")
        return
    
    if not test_root():
        print("Root endpoint failed!")
        return
    
    # Test authentication
    token = test_authentication()
    if not token:
        print("Authentication failed!")
        return
    
    # Test API key generation
    api_key = test_api_key_generation(token)
    
    # Test user info
    test_user_info(token)
    
    # Test transcription workflow
    file_id = test_transcription_upload(token)
    if file_id:
        transcript_id = test_transcription_process(token, file_id)
        
        if transcript_id:
            # Test export
            test_export(token, transcript_id)
    
    # Test search
    test_search(token)
    
    # Test metrics with API key
    if api_key:
        test_metrics(api_key)
    
    print("\n" + "=" * 50)
    print("API Tests Completed!")


if __name__ == "__main__":
    main()