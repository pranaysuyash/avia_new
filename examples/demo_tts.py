#!/usr/bin/env python3
"""
Demo script for Text-to-Speech functionality
Tests the TTS module with various scenarios
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tts import (
    synthesize_speech, list_available_voices, estimate_synthesis_cost,
    get_voice_by_name, validate_voice_settings, cleanup_tts_files,
    TTSError, VOICE_PRESETS
)
from elevenlabs import VoiceSettings
from utils import setup_logging

def main():
    """Run TTS demo scenarios"""
    setup_logging("INFO")
    print("🎤 Text-to-Speech Demo")
    print("=" * 50)
    
    # Check API key
    if not os.getenv("ELEVENLABS_API_KEY"):
        print("❌ ELEVENLABS_API_KEY not found in environment")
        print("Please set your ElevenLabs API key in .env file")
        return
    
    try:
        # Demo 1: List available voices
        print("\n1. 📋 Listing Available Voices")
        print("-" * 30)
        try:
            voices = list_available_voices()
            print(f"Found {len(voices)} available voices:")
            for i, voice in enumerate(voices[:5]):  # Show first 5
                print(f"  {i+1}. {voice['name']} ({voice['voice_id']})")
                print(f"     Category: {voice['category']}")
                print(f"     Description: {voice['description'][:60]}...")
                print()
        except TTSError as e:
            print(f"❌ Failed to list voices: {e}")
        
        # Demo 2: Cost estimation
        print("\n2. 💰 Cost Estimation")
        print("-" * 30)
        test_texts = [
            "Hello world!",
            "This is a longer text that will cost more to synthesize because it has more characters.",
            "A" * 1000  # 1000 character text
        ]
        
        for text in test_texts:
            cost = estimate_synthesis_cost(text)
            print(f"Text length: {len(text)} chars → Estimated cost: ${cost:.4f}")
        
        # Demo 3: Voice search
        print("\n3. 🔍 Voice Search")
        print("-" * 30)
        search_names = ["Rachel", "Domi", "NonExistent"]
        for name in search_names:
            voice = get_voice_by_name(name)
            if voice:
                print(f"✅ Found '{name}': {voice['voice_id']}")
            else:
                print(f"❌ Voice '{name}' not found")
        
        # Demo 4: Voice settings validation
        print("\n4. ⚙️ Voice Settings Validation")
        print("-" * 30)
        test_settings = [
            {"stability": 0.8, "similarity_boost": 0.7},
            {"stability": 1.5},  # Invalid - should fail
            {}  # Empty - should use defaults
        ]
        
        for i, settings in enumerate(test_settings):
            try:
                validated = validate_voice_settings(settings)
                print(f"✅ Settings {i+1}: Valid")
                print(f"   Stability: {validated.stability}")
                print(f"   Similarity Boost: {validated.similarity_boost}")
            except TTSError as e:
                print(f"❌ Settings {i+1}: {e}")
        
        # Demo 5: Voice presets
        print("\n5. 🎭 Voice Presets")
        print("-" * 30)
        for preset_name, preset_config in VOICE_PRESETS.items():
            print(f"{preset_name.title()}:")
            print(f"  Voice ID: {preset_config['voice_id']}")
            print(f"  Stability: {preset_config['settings'].stability}")
            print(f"  Similarity Boost: {preset_config['settings'].similarity_boost}")
            print()
        
        # Demo 6: Actual synthesis (if user confirms)
        print("\n6. 🎵 Speech Synthesis")
        print("-" * 30)
        
        # Ask user if they want to test actual synthesis
        response = input("Do you want to test actual speech synthesis? (y/N): ").lower().strip()
        if response in ['y', 'yes']:
            test_text = "Hello! This is a test of the ElevenLabs text-to-speech integration. The system is working correctly."
            
            print(f"Synthesizing: '{test_text}'")
            print("This may take a few seconds...")
            
            try:
                # Test with default settings
                audio_path = synthesize_speech(test_text)
                print(f"✅ Audio generated successfully: {audio_path}")
                
                # Check file size
                file_size = os.path.getsize(audio_path)
                print(f"   File size: {file_size:,} bytes")
                
                # Test with custom voice preset
                print("\nTesting with 'professional' preset...")
                preset = VOICE_PRESETS["professional"]
                audio_path_2 = synthesize_speech(
                    test_text,
                    voice_id=preset["voice_id"],
                    voice_settings=preset["settings"]
                )
                print(f"✅ Professional voice audio: {audio_path_2}")
                
                print(f"\n🎧 You can play these audio files:")
                print(f"   {audio_path}")
                print(f"   {audio_path_2}")
                
            except TTSError as e:
                print(f"❌ Synthesis failed: {e}")
        else:
            print("Skipping actual synthesis test.")
        
        # Demo 7: Cleanup
        print("\n7. 🧹 File Cleanup")
        print("-" * 30)
        print("Cleaning up old TTS files...")
        cleanup_tts_files(max_age_hours=0)  # Clean all files for demo
        print("✅ Cleanup completed")
        
    except Exception as e:
        print(f"❌ Demo failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎉 TTS Demo completed!")
    print("=" * 50)

if __name__ == "__main__":
    main()