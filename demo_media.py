#!/usr/bin/env python3
"""
Demonstration script for media processing utilities
"""

import os
import tempfile
from media import (
    validate_media_file,
    extract_audio,
    convert_audio_format,
    get_media_info,
    cleanup_temp_file,
    is_video_file,
    is_audio_file,
    MediaProcessingError
)
import ffmpeg

def create_test_audio():
    """Create a test audio file using FFmpeg"""
    test_audio = os.path.join("temp", "demo_audio.wav")
    
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
    """Demonstrate media processing functionality"""
    print("=== Media Processing Demo ===\n")
    
    # Create test audio file
    test_file = create_test_audio()
    if not test_file:
        return
    
    try:
        # Test file type detection
        print("1. File Type Detection:")
        print(f"   Is audio file: {is_audio_file(test_file)}")
        print(f"   Is video file: {is_video_file(test_file)}")
        print()
        
        # Test file validation
        print("2. File Validation:")
        is_valid = validate_media_file(test_file)
        print(f"   File is valid: {is_valid}")
        print()
        
        # Test media info extraction
        print("3. Media Information:")
        info = get_media_info(test_file)
        print(f"   Duration: {info['duration']:.2f} seconds")
        print(f"   Format: {info['format_name']}")
        print(f"   Sample Rate: {info['sample_rate']} Hz")
        print(f"   Channels: {info['channels']}")
        print(f"   Codec: {info['codec']}")
        print(f"   Size: {info['size']} bytes")
        print()
        
        # Test audio format conversion
        print("4. Audio Format Conversion:")
        converted_file = convert_audio_format(test_file)
        print(f"   Converted to: {converted_file}")
        
        # Get info of converted file
        converted_info = get_media_info(converted_file)
        print(f"   New Sample Rate: {converted_info['sample_rate']} Hz")
        print(f"   New Channels: {converted_info['channels']}")
        print()
        
        # Test audio extraction (simulate video file)
        print("5. Audio Extraction (from same file as demo):")
        extracted_file = extract_audio(test_file)
        print(f"   Extracted to: {extracted_file}")
        
        extracted_info = get_media_info(extracted_file)
        print(f"   Extracted Sample Rate: {extracted_info['sample_rate']} Hz")
        print(f"   Extracted Channels: {extracted_info['channels']}")
        print()
        
        # Clean up temporary files
        print("6. Cleanup:")
        cleanup_temp_file(converted_file)
        cleanup_temp_file(extracted_file)
        print("   ✓ Temporary files cleaned up")
        
        print("\n=== Demo Complete ===")
        
    except MediaProcessingError as e:
        print(f"✗ Media processing error: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

if __name__ == "__main__":
    demo_media_processing()