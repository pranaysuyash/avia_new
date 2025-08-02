#!/usr/bin/env python3
"""
Test the enhanced API server with real Whisper integration
"""

import requests
import json

API_BASE = "http://localhost:8000/api/v1"

def test_real_whisper_transcription():
    """Test real Whisper transcription with ElevenLabs audio"""
    print("🎙️ Testing Real Whisper Integration...")
    
    # Use a proper test file with actual content
    test_file = "/Users/pranay/Projects/LLM/video/ner/test_data/audio/business_meeting.wav"
    
    try:
        # Step 1: Upload file
        print("1. Uploading test audio file...")
        with open(test_file, 'rb') as f:
            files = {'file': ('edge_very_short.wav', f, 'audio/wav')}
            response = requests.post(f"{API_BASE}/transcription/upload", files=files)
        
        if response.status_code != 200:
            print(f"❌ Upload failed: {response.status_code}")
            return
            
        upload_result = response.json()
        file_id = upload_result['data']['file_id']
        print(f"✅ File uploaded: {file_id}")
        
        # Step 2: Process with real Whisper
        print("2. Processing with real Whisper (this may take a moment)...")
        process_data = {
            'file_id': file_id,
            'language': 'auto',
            'enable_diarization': True,
            'extract_entities': True
        }
        
        response = requests.post(f"{API_BASE}/transcription/process", data=process_data)
        
        if response.status_code != 200:
            print(f"❌ Processing failed: {response.status_code}")
            print(response.text)
            return
            
        process_result = response.json()
        
        if process_result['success']:
            result = process_result['data']['result']
            print(f"✅ Real Whisper transcription completed!")
            print(f"   Transcript ID: {result['transcript_id']}")
            print(f"   Language: {result['language']}")
            print(f"   Confidence: {result['confidence']}")
            print(f"   Duration: {result['duration']}s")
            print(f"   Word count: {result['word_count']}")
            print(f"   Processing time: {result['processing_time']:.1f}s")
            print(f"   Text preview: {result['text'][:100]}...")
            
            if result.get('segments'):
                print(f"   Speaker segments: {len(result['segments'])}")
                
            if result.get('entities'):
                print(f"   Entities found: {len(result['entities'])}")
                for entity in result['entities'][:3]:  # Show first 3
                    print(f"      - {entity['label']}: {entity['text']}")
            
            # Step 3: Generate insights
            print("\n3. Generating insights with real data...")
            insights_data = {'transcript_id': result['transcript_id']}
            
            response = requests.post(f"{API_BASE}/insights/generate", data=insights_data)
            if response.status_code == 200:
                insights = response.json()
                if insights['success']:
                    print(f"✅ Insights generated successfully!")
                    print(f"   Summary: {insights['data']['summary']['executive'][:100]}...")
                    print(f"   Action items: {len(insights['data']['actionItems'])}")
                    print(f"   Topics identified: {len(insights['data']['topics'])}")
            
            return True
            
        else:
            print(f"❌ Processing failed: {process_result}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_real_whisper_transcription()
    if success:
        print("\n🎉 Real Whisper integration working perfectly!")
        print("The application now uses actual Whisper AI for transcription!")
    else:
        print("\n⚠️ Real Whisper test failed, check error messages above")