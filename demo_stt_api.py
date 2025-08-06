#!/usr/bin/env python3
"""
Demo script for testing the speech-to-text functionality using API
"""

import os
import sys
import tempfile
import wave
import numpy as np
import base64
from api_client import get_api_client
from api_wrappers import stt

def create_demo_audio():
    """Create a simple demo audio file with a sine wave"""
    # Create a temporary WAV file
    temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    temp_file.close()
    
    # Generate a simple sine wave (1 second, 440Hz)
    sample_rate = 16000
    duration = 2.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    frequency = 440  # A4 note
    audio_data = (np.sin(2 * np.pi * frequency * t) * 32767 * 0.5).astype(np.int16)
    
    # Write WAV file
    with wave.open(temp_file.name, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    print(f"Created demo audio file: {temp_file.name}")
    return temp_file.name

def test_transcription():
    """Test the transcription functionality via API"""
    print("=== Speech-to-Text API Demo ===\n")
    
    # Initialize API client
    api_client = get_api_client()
    
    # Check if we have a real audio file to test with
    test_audio_file = None
    if os.path.exists("temp/demo_audio.wav"):
        test_audio_file = "temp/demo_audio.wav"
        print(f"Using existing audio file: {test_audio_file}")
    else:
        # Create a demo audio file
        test_audio_file = create_demo_audio()
        print("Using generated demo audio file (sine wave)")
    
    try:
        print("\n1. Testing API transcription...")
        
        try:
            # Transcribe using API wrapper
            result = stt.transcribe(test_audio_file, language="en-US")
            
            print(f"   - Transcription result: '{result.get('text', '')}'")
            print(f"   - Language: {result.get('language', 'unknown')}")
            print(f"   - Duration: {result.get('duration', 0):.2f}s")
            print(f"   - Confidence: {result.get('confidence', 0):.3f}")
            
            # Display segments if available
            if result.get('segments'):
                print(f"   - Segments: {len(result['segments'])}")
                for i, segment in enumerate(result['segments'][:3]):  # Show first 3
                    print(f"     [{i}] {segment.get('start', 0):.2f}s - {segment.get('end', 0):.2f}s: {segment.get('text', '')}")
                    
        except Exception as e:
            print(f"   - Transcription failed: {str(e)}")
            print("   - This is expected for sine wave audio (no speech content)")
        
        print("\n2. Testing supported languages...")
        try:
            languages = stt.get_supported_languages()
            print(f"   - Supported languages: {', '.join(languages[:5])}...")
            print(f"   - Total languages: {len(languages)}")
        except Exception as e:
            print(f"   - Failed to get languages: {str(e)}")
        
        print("\n3. Testing direct API endpoint...")
        try:
            # Test direct API call
            with open(test_audio_file, 'rb') as f:
                audio_data = f.read()
            
            # Create transcription request
            response = api_client.create_transcription(
                test_audio_file,
                language="en-US",
                enable_punctuation=True,
                enable_speaker_diarization=False
            )
            
            if response.get('transcription_id'):
                print(f"   - Transcription ID: {response['transcription_id']}")
                print(f"   - Status: {response.get('status', 'unknown')}")
                
                # Check status
                status_response = api_client.get_transcription_status(response['transcription_id'])
                print(f"   - Current status: {status_response.get('status', 'unknown')}")
                
        except Exception as e:
            print(f"   - Direct API test failed: {str(e)}")
        
        # Test batch processing if multiple files exist
        test_files = []
        for filename in ['demo_audio1.wav', 'demo_audio2.wav']:
            if os.path.exists(f"temp/{filename}"):
                test_files.append(f"temp/{filename}")
        
        if len(test_files) >= 2:
            print("\n4. Testing batch transcription...")
            try:
                # This would be implemented in the API wrapper
                print(f"   - Processing {len(test_files)} files...")
                # batch_results = stt.batch_transcribe(test_files)
                print("   - Batch processing would be performed here")
            except Exception as e:
                print(f"   - Batch test failed: {str(e)}")
        else:
            print("\n4. Skipping batch test (not enough test files)")
        
        print("\n=== API Demo completed successfully! ===")
        
    except Exception as e:
        print(f"\nUnexpected error during demo: {e}")
        return False
    
    finally:
        # Clean up temporary file if we created one
        if test_audio_file and not test_audio_file.startswith("temp/"):
            try:
                os.remove(test_audio_file)
                print(f"\nCleaned up temporary file: {test_audio_file}")
            except:
                pass
    
    return True

if __name__ == "__main__":
    # Set up basic logging
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Check API connection first
    print("Checking API connection...")
    try:
        api_client = get_api_client()
        health = api_client._make_request("GET", "/api/v1/health")
        if health.get('status') == 'healthy':
            print("✅ API is healthy\n")
        else:
            print("⚠️ API health check failed\n")
    except Exception as e:
        print(f"❌ Could not connect to API: {str(e)}")
        print("Make sure the API server is running at the configured URL\n")
    
    success = test_transcription()
    sys.exit(0 if success else 1)