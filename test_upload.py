#!/usr/bin/env python3
"""
Test script to upload and process a file using the enhanced API
"""

import requests
import json
import time
import tempfile
import os

# API base URL
API_BASE = "http://localhost:8000/api/v1"

def create_sample_audio_file():
    """Create a simple WAV file for testing"""
    import wave
    import numpy as np
    
    # Create a 5-second sine wave audio file
    sample_rate = 44100
    duration = 5  # seconds
    frequency = 440  # A note
    
    t = np.linspace(0, duration, sample_rate * duration, False)
    audio_data = np.sin(2 * np.pi * frequency * t) * 0.3
    
    # Convert to 16-bit integers
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Create temporary WAV file
    temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    
    with wave.open(temp_file.name, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    return temp_file.name

def test_upload_and_process():
    """Test the complete upload and processing workflow"""
    print("Creating sample audio file...")
    audio_file_path = create_sample_audio_file()
    print(f"Created audio file: {audio_file_path}")
    
    try:
        # Step 1: Upload file
        print("\n1. Uploading file...")
        with open(audio_file_path, 'rb') as f:
            files = {'file': ('test_audio.wav', f, 'audio/wav')}
            response = requests.post(f"{API_BASE}/transcription/upload", files=files)
        
        print(f"Upload response: {response.status_code}")
        print(f"Upload result: {response.json()}")
        
        if response.status_code != 200:
            print("Upload failed!")
            return
        
        upload_result = response.json()
        file_id = upload_result['data']['file_id']
        
        # Step 2: Process transcription
        print(f"\n2. Processing transcription for file_id: {file_id}")
        process_data = {
            'file_id': file_id,
            'language': 'auto',
            'enable_diarization': True,
            'extract_entities': True
        }
        
        response = requests.post(f"{API_BASE}/transcription/process", data=process_data)
        print(f"Processing response: {response.status_code}")
        process_result = response.json()
        print(f"Processing result: {json.dumps(process_result, indent=2)}")
        
        if response.status_code != 200:
            print("Processing failed!")
            return
        
        transcript_id = process_result['data']['transcript_id']
        
        # Step 3: Generate insights
        print(f"\n3. Generating insights for transcript_id: {transcript_id}")
        insights_data = {'transcript_id': transcript_id}
        
        response = requests.post(f"{API_BASE}/insights/generate", data=insights_data)
        print(f"Insights response: {response.status_code}")
        insights_result = response.json()
        print(f"Insights result keys: {list(insights_result['data'].keys()) if 'data' in insights_result else 'No data'}")
        
        # Step 4: Test dashboard stats
        print(f"\n4. Getting dashboard stats...")
        response = requests.get(f"{API_BASE}/insights/dashboard-stats")
        print(f"Stats response: {response.status_code}")
        stats_result = response.json()
        print(f"Stats: {stats_result}")
        
        print("\n✅ Complete workflow test successful!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        # Cleanup
        try:
            os.unlink(audio_file_path)
            print(f"Cleaned up temporary file: {audio_file_path}")
        except:
            pass

if __name__ == "__main__":
    test_upload_and_process()