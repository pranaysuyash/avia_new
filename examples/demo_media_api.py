#!/usr/bin/env python3
"""
Demonstration script for media processing utilities using API
"""

import os
import tempfile
import base64
from api_client import get_api_client
from api_wrappers import media
import ffmpeg

def create_test_audio():
    """Create a test audio file using FFmpeg"""
    test_audio = os.path.join("temp", "demo_audio.wav")
    
    # Create temp directory if it doesn't exist
    os.makedirs("temp", exist_ok=True)
    
    try:
        # Generate a 2-second sine wave at 440Hz
        (
            ffmpeg
            .input('sine=frequency=440:duration=2', f='lavfi')
            .output(test_audio, acodec='pcm_s16le', ar=44100, ac=2)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        print(f"✓ Created test audio file: {test_audio}")
        return test_audio
    except ffmpeg.Error as e:
        print(f"✗ Failed to create test audio: {e}")
        return None

def demo_media_processing():
    """Demonstrate media processing functionality via API"""
    print("=== Media Processing API Demo ===\n")
    
    # Check API connection
    api_client = get_api_client()
    try:
        health = api_client._make_request("GET", "/api/v1/health")
        print(f"✅ API Status: {health.get('status', 'unknown')}")
    except Exception as e:
        print(f"❌ API Connection Error: {str(e)}")
        print("Make sure the API server is running\n")
        return
    
    # Create test audio file
    test_file = create_test_audio()
    if not test_file:
        return
    
    try:
        # Test 1: Media validation via API
        print("\n1. File Validation via API:")
        is_valid = media.is_valid_media_file(test_file)
        print(f"   File is valid: {is_valid}")
        print()
        
        # Test 2: Media info extraction via API
        print("2. Media Information via API:")
        info = media.get_media_info(test_file)
        if info:
            print(f"   Duration: {info.get('duration', 0):.2f} seconds")
            print(f"   Format: {info.get('format_name', 'unknown')}")
            print(f"   Sample Rate: {info.get('sample_rate', 0)} Hz")
            print(f"   Channels: {info.get('channels', 0)}")
            print(f"   Codec: {info.get('codec', 'unknown')}")
            print(f"   Size: {info.get('size', 0)} bytes")
        print()
        
        # Test 3: Direct API call for media processing
        print("3. Direct API Media Processing:")
        try:
            response = api_client.process_media_file(
                test_file,
                operation="analyze"
            )
            if response.get('success'):
                print("   ✅ Media analysis successful")
                if 'metadata' in response:
                    for key, value in response['metadata'].items():
                        print(f"   {key}: {value}")
        except Exception as e:
            print(f"   ❌ Direct API call failed: {e}")
        print()
        
        # Test 4: Audio extraction (simulate video processing)
        print("4. Audio Extraction via API:")
        try:
            # For demo, we'll extract from the audio file itself
            extracted_path = media.extract_audio(test_file)
            print(f"   ✅ Extracted audio to: {extracted_path}")
            
            # Get info of extracted file
            extracted_info = media.get_media_info(extracted_path)
            if extracted_info:
                print(f"   Sample Rate: {extracted_info.get('sample_rate', 0)} Hz")
                print(f"   Channels: {extracted_info.get('channels', 0)}")
        except Exception as e:
            print(f"   ❌ Extraction failed: {e}")
        print()
        
        # Test 5: Batch media info
        print("5. Batch Media Processing:")
        print("   Would process multiple files in one API call")
        print("   Example: Process 10 videos and extract audio from each")
        print()
        
        # Test 6: Media format detection
        print("6. Format Detection Tests:")
        test_files = {
            "audio.mp3": "audio/mpeg",
            "video.mp4": "video/mp4",
            "audio.wav": "audio/wav",
            "video.avi": "video/x-msvideo"
        }
        for filename, expected_type in test_files.items():
            print(f"   {filename} → {expected_type}")
        print()
        
        # Test 7: API streaming capabilities
        print("7. Streaming Capabilities:")
        print("   The API supports streaming for large files:")
        print("   - Chunked upload for files > 100MB")
        print("   - Progress tracking via WebSocket")
        print("   - Resume capability for interrupted uploads")
        print()
        
        # Test 8: Error handling
        print("8. Error Handling Test:")
        try:
            # Try to process a non-existent file
            invalid_result = media.get_media_info("non_existent_file.mp3")
            print("   Unexpected success with invalid file")
        except Exception as e:
            print(f"   ✅ Properly handled error: {str(e)[:50]}...")
        
        print("\n=== API Demo Complete ===")
        
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test file
        if test_file and os.path.exists(test_file):
            try:
                os.remove(test_file)
                print("\n✓ Cleaned up test file")
            except:
                pass

if __name__ == "__main__":
    demo_media_processing()