#!/usr/bin/env python3
"""Test script for upload and transcription workflow"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

# For testing, use a hardcoded test API key or no auth
# In production, you would get a proper auth token
print("1. Using test authentication...")
headers = {}  # No auth for testing

# Upload a test file
print("\n2. Uploading test audio file...")
with open("test_audio.wav", "rb") as f:
    files = {"file": ("test_audio.wav", f, "audio/wav")}
    upload_response = requests.post(
        f"{BASE_URL}/transcription/upload",
        files=files,
        headers=headers
    )

if upload_response.status_code == 200:
    upload_data = upload_response.json()["data"]
    file_id = upload_data["file_id"]
    print(f"File uploaded successfully. File ID: {file_id}")
else:
    print(f"Upload failed: {upload_response.text}")
    exit(1)

# Start transcription
print("\n3. Starting transcription...")
transcription_response = requests.post(
    f"{BASE_URL}/transcription/process",
    json={
        "file_id": file_id,
        "use_api": False,
        "language": "auto",
        "model": "base",
        "enable_diarization": False,
        "extract_entities": True
    },
    headers=headers
)

if transcription_response.status_code == 200:
    transcription_data = transcription_response.json()["data"]
    print("Transcription completed successfully!")
    print(f"Text: {transcription_data['text'][:100]}...")
    print(f"Duration: {transcription_data['duration']} seconds")
    print(f"Word count: {transcription_data['word_count']}")
    print(f"Entities found: {len(transcription_data['entities'])}")
else:
    print(f"Transcription failed: {transcription_response.text}")
    exit(1)

# Get transcription list
print("\n4. Getting transcription list...")
list_response = requests.get(
    f"{BASE_URL}/transcription/list?limit=5",
    headers=headers
)

if list_response.status_code == 200:
    list_data = list_response.json()["data"]
    print(f"Found {list_data['total']} transcriptions")
    for item in list_data['items']:
        print(f"  - {item['title']} ({item['word_count']} words)")
else:
    print(f"Failed to get list: {list_response.text}")

# Test dashboard stats
print("\n5. Getting dashboard stats...")
stats_response = requests.get(
    f"{BASE_URL}/insights/dashboard-stats",
    headers=headers
)

if stats_response.status_code == 200:
    stats = stats_response.json()["data"]
    print(f"Total transcriptions: {stats['totalTranscriptions']}")
    print(f"Hours processed: {stats['hoursProcessed']}")
    print(f"Entities found: {stats['entitiesFound']}")
    print(f"Accuracy rate: {stats['accuracyRate']}%")
else:
    print(f"Failed to get stats: {stats_response.text}")

print("\n✅ All tests completed!")