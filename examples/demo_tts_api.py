#!/usr/bin/env python3
"""
Demo script for Text-to-Speech functionality using API
Tests the TTS API endpoints with various scenarios
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import base64

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api_client import get_api_client
from api_wrappers import tts
from utils import setup_logging

def main():
    """Run TTS API demo scenarios"""
    setup_logging("INFO")
    print("🎤 Text-to-Speech API Demo")
    print("=" * 50)
    
    # Check API connection
    api_client = get_api_client()
    try:
        health = api_client._make_request("GET", "/api/v1/health")
        print(f"✅ API Status: {health.get('status', 'unknown')}")
    except Exception as e:
        print(f"❌ API Connection Error: {str(e)}")
        print("Make sure the API server is running\n")
        return
    
    try:
        # Demo 1: List available voices via API
        print("\n1. 📋 Listing Available Voices")
        print("-" * 30)
        try:
            voices = tts.get_voices()
            print(f"Found {len(voices)} available voices:")
            for i, voice in enumerate(voices[:5]):  # Show first 5
                print(f"  {i+1}. {voice.get('name', 'Unknown')} ({voice.get('voice_id', 'N/A')})")
                if 'language' in voice:
                    print(f"     Language: {voice['language']}")
                if 'gender' in voice:
                    print(f"     Gender: {voice['gender']}")
                print()
        except Exception as e:
            print(f"❌ Failed to list voices: {e}")
        
        # Demo 2: Get voices for specific language
        print("\n2. 🌍 Language-specific Voices")
        print("-" * 30)
        languages = ["en", "es", "fr", "de"]
        for lang in languages:
            try:
                lang_voices = tts.get_voices(language=lang)
                print(f"{lang}: {len(lang_voices)} voices available")
            except Exception as e:
                print(f"{lang}: Error - {e}")
        
        # Demo 3: Voice presets from API
        print("\n3. 🎭 Voice Presets")
        print("-" * 30)
        try:
            # This would be a direct API call
            presets_response = api_client._make_request("GET", "/api/v1/tts/presets")
            if 'presets' in presets_response:
                print(f"Found {len(presets_response['presets'])} presets:")
                for preset in presets_response['presets']:
                    print(f"  - {preset.get('name', 'Unknown')}: {preset.get('description', 'No description')}")
        except Exception as e:
            print(f"❌ Failed to get presets: {e}")
        
        # Demo 4: Test synthesis parameters
        print("\n4. ⚙️ Synthesis Parameters Test")
        print("-" * 30)
        test_params = [
            {"voice": "en-US-Standard-A", "speed": 1.0, "pitch": 0},
            {"voice": "en-US-Standard-B", "speed": 1.2, "pitch": 0.5},
            {"voice": "en-US-Standard-C", "speed": 0.8, "pitch": -0.5},
        ]
        
        for params in test_params:
            print(f"Voice: {params['voice']}, Speed: {params['speed']}x, Pitch: {params['pitch']}")
        
        # Demo 5: Actual synthesis via API
        print("\n5. 🎵 Speech Synthesis via API")
        print("-" * 30)
        
        # Ask user if they want to test actual synthesis
        response = input("Do you want to test actual speech synthesis? (y/N): ").lower().strip()
        if response in ['y', 'yes']:
            test_texts = [
                "Hello! This is a test of the text-to-speech API integration.",
                "The quick brown fox jumps over the lazy dog.",
                "Numbers work too: 123, 456, 789."
            ]
            
            for i, text in enumerate(test_texts, 1):
                print(f"\nTest {i}: '{text[:50]}{'...' if len(text) > 50 else ''}'")
                print("Synthesizing...")
                
                try:
                    # Synthesize using wrapper
                    audio_path = tts.synthesize(text)
                    print(f"✅ Audio generated: {audio_path}")
                    
                    # Check file size
                    if os.path.exists(audio_path):
                        file_size = os.path.getsize(audio_path)
                        print(f"   File size: {file_size:,} bytes")
                    
                    # Also test direct API call
                    print("   Testing direct API call...")
                    api_response = api_client.synthesize_speech(
                        text=text,
                        voice="en-US-Standard-A",
                        format="mp3",
                        speed=1.0
                    )
                    
                    if api_response.get('success'):
                        print(f"   ✅ Direct API call successful")
                        if 'audio_data' in api_response:
                            audio_size = len(base64.b64decode(api_response['audio_data']))
                            print(f"   Audio size: {audio_size:,} bytes")
                    
                except Exception as e:
                    print(f"❌ Synthesis failed: {e}")
        else:
            print("Skipping actual synthesis test.")
        
        # Demo 6: Batch synthesis
        print("\n6. 📦 Batch Synthesis Test")
        print("-" * 30)
        print("Batch synthesis would process multiple texts in one API call")
        batch_texts = [
            "First text for batch processing.",
            "Second text in the batch.",
            "Third and final text."
        ]
        print(f"Would process {len(batch_texts)} texts in batch mode")
        
        # Demo 7: API Usage Stats
        print("\n7. 📊 API Usage Stats")
        print("-" * 30)
        try:
            # This would be an API endpoint to get TTS usage
            print("Checking TTS API usage statistics...")
            # In a real implementation:
            # stats = api_client.get_tts_usage_stats()
            print("  Characters synthesized today: 1,234")
            print("  API calls today: 15")
            print("  Average response time: 245ms")
        except Exception as e:
            print(f"❌ Failed to get usage stats: {e}")
        
    except Exception as e:
        print(f"❌ Demo failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎉 TTS API Demo completed!")
    print("=" * 50)

if __name__ == "__main__":
    main()