#!/usr/bin/env python3
"""
Test script to verify the complete transcription flow
"""

import requests
import time
import json
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000"

# Test audio file
AUDIO_FILE = "test_data/audio/business_meeting.wav"

def test_transcription_flow():
    """Test the complete file upload and transcription flow"""
    
    print("=== Testing Transcription Flow ===\n")
    
    # Step 1: Check API health
    print("1. Checking API health...")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code == 200:
            print("✓ API is healthy")
        else:
            print(f"✗ API health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"✗ Cannot connect to API: {e}")
        return
    
    # Step 2: Upload audio file
    print("\n2. Uploading audio file...")
    try:
        with open(AUDIO_FILE, 'rb') as f:
            files = {'file': (Path(AUDIO_FILE).name, f, 'audio/wav')}
            response = requests.post(f"{BASE_URL}/api/transcription/upload", files=files)
        
        if response.status_code == 200:
            upload_result = response.json()
            file_id = upload_result['data']['file_id']
            print(f"✓ File uploaded successfully. File ID: {file_id}")
            print(f"  - File name: {upload_result['data']['file_name']}")
            print(f"  - File size: {upload_result['data']['file_size']} bytes")
        else:
            print(f"✗ Upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            return
    except Exception as e:
        print(f"✗ Upload error: {e}")
        return
    
    # Step 3: Process transcription
    print("\n3. Processing transcription...")
    transcribe_data = {
        "use_api": False,
        "language": "en",
        "model": "base",
        "enable_diarization": False,
        "extract_entities": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/transcription/process?file_id={file_id}",
            json=transcribe_data
        )
        
        if response.status_code == 200:
            result = response.json()
            transcription = result['data']
            print(f"✓ Transcription completed successfully")
            print(f"  - Transcript ID: {transcription['transcript_id']}")
            print(f"  - Language: {transcription['language']}")
            print(f"  - Duration: {transcription['duration']}s")
            print(f"  - Word count: {transcription['word_count']}")
            print(f"  - Processing time: {transcription['processing_time']}s")
            print(f"\n  - Text preview: {transcription['text'][:200]}...")
            
            if transcription.get('entities'):
                print(f"\n  - Entities found: {len(transcription['entities'])}")
                for i, entity in enumerate(transcription['entities'][:5]):
                    print(f"    • {entity['text']} ({entity['label']})")
                if len(transcription['entities']) > 5:
                    print(f"    ... and {len(transcription['entities']) - 5} more")
        else:
            print(f"✗ Transcription failed: {response.status_code}")
            print(f"Response: {response.text}")
            return
    except Exception as e:
        print(f"✗ Transcription error: {e}")
        return
    
    # Step 4: Test other methods
    print("\n4. Testing different transcription methods...")
    methods = [
        ("basic", "base"),
        ("advanced", "medium"),
        ("multilingual", "large"),
        ("whisperx", "large")
    ]
    
    for method_name, model in methods:
        print(f"\n  Testing {method_name} method...")
        
        # Upload file again for each test
        try:
            with open(AUDIO_FILE, 'rb') as f:
                files = {'file': (Path(AUDIO_FILE).name, f, 'audio/wav')}
                response = requests.post(f"{BASE_URL}/api/transcription/upload", files=files)
            
            if response.status_code != 200:
                print(f"  ✗ Upload failed for {method_name}")
                continue
                
            file_id = response.json()['data']['file_id']
            
            # Process with different method
            transcribe_data = {
                "use_api": False,
                "language": "auto",
                "model": model,
                "enable_diarization": method_name == "whisperx",
                "extract_entities": True
            }
            
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/api/transcription/process?file_id={file_id}",
                json=transcribe_data
            )
            
            if response.status_code == 200:
                processing_time = time.time() - start_time
                print(f"  ✓ {method_name} completed in {processing_time:.2f}s")
            else:
                print(f"  ✗ {method_name} failed: {response.status_code}")
                
        except Exception as e:
            print(f"  ✗ Error testing {method_name}: {e}")
    
    # Step 5: Test history endpoint
    print("\n5. Testing history endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/transcription/history")
        if response.status_code == 200:
            history = response.json()['data']
            print(f"✓ History retrieved: {history['total_count']} transcriptions")
            for item in history['transcriptions'][:3]:
                print(f"  - {item['file_name']} ({item['created_at']})")
        else:
            print(f"✗ History retrieval failed: {response.status_code}")
    except Exception as e:
        print(f"✗ History error: {e}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_transcription_flow()