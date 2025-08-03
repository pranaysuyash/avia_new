#!/usr/bin/env python3
"""Test script to verify API endpoints"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_upload():
    print("Testing file upload endpoint...")
    # Create a dummy file
    files = {'file': ('test.wav', b'dummy audio content', 'audio/wav')}
    response = requests.post(f"{BASE_URL}/api/transcription/upload", files=files)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    if response.status_code == 200:
        return response.json()['data']['file_id']
    print()
    return None

def test_transcribe(file_id):
    if not file_id:
        print("Skipping transcribe test - no file_id")
        return
    
    print("Testing transcribe endpoint...")
    data = {
        "file_id": file_id,
        "language": "en",
        "detect_code_switching": False
    }
    response = requests.post(f"{BASE_URL}/api/transcription/transcribe", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

if __name__ == "__main__":
    print(f"Testing API at {BASE_URL}")
    print("-" * 50)
    
    test_health()
    file_id = test_upload()
    test_transcribe(file_id)
    
    print("-" * 50)
    print("API test complete!")