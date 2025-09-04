#!/usr/bin/env python3
"""
Demo script for testing the speech-to-text functionality
"""

import os
import sys
import tempfile
import wave
import numpy as np
from stt import transcribe, transcribe_detailed, get_transcription_confidence, TranscriptionError

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
    """Test the transcription functionality"""
    print("=== Speech-to-Text Demo ===\n")
    
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
        print("\n1. Testing basic transcription...")
        
        # Test with local model only (no API key required)
        print("   - Using local Whisper model...")
        try:
            result = transcribe(test_audio_file, use_api=False)
            print(f"   - Transcription result: '{result}'")
        except TranscriptionError as e:
            print(f"   - Local transcription failed: {e.user_message}")
            print("   - This is expected for sine wave audio (no speech content)")
        
        print("\n2. Testing detailed transcription...")
        try:
            detailed_result = transcribe_detailed(test_audio_file, use_api=False)
            print(f"   - Text: '{detailed_result.text}'")
            print(f"   - Confidence: {detailed_result.confidence:.3f}")
            print(f"   - Processing time: {detailed_result.processing_time:.2f}s")
            print(f"   - Model used: {detailed_result.model_used}")
            print(f"   - Language: {detailed_result.language}")
            print(f"   - Word count: {detailed_result.word_count()}")
        except TranscriptionError as e:
            print(f"   - Detailed transcription failed: {e.user_message}")
        
        print("\n3. Testing confidence assessment...")
        try:
            confidence = get_transcription_confidence(test_audio_file)
            print(f"   - Confidence score: {confidence:.3f}")
        except TranscriptionError as e:
            print(f"   - Confidence assessment failed: {e.user_message}")
        
        # Test API functionality if API key is available
        if os.getenv('OPENAI_API_KEY'):
            print("\n4. Testing OpenAI API transcription...")
            try:
                api_result = transcribe(test_audio_file, use_api=True)
                print(f"   - API transcription result: '{api_result}'")
            except TranscriptionError as e:
                print(f"   - API transcription failed: {e.user_message}")
        else:
            print("\n4. Skipping API test (no OPENAI_API_KEY found)")
        
        print("\n=== Demo completed successfully! ===")
        
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
    
    success = test_transcription()
    sys.exit(0 if success else 1)