#!/usr/bin/env python3
"""
Demo script for Admin Panel functionality
Shows how to use the admin panel features programmatically
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_admin_features():
    """Demonstrate admin panel functionality"""
    print("=à Admin Panel Demo")
    print("=" * 60)
    
    # Check if running as admin
    admin_password = os.getenv('ADMIN_PASSWORD')
    if not admin_password:
        print("  ADMIN_PASSWORD not set in environment variables")
        print("Please set ADMIN_PASSWORD in your .env file to use admin features")
        return
    
    print(" Admin environment configured")
    print("\nAvailable Admin Features:")
    print("1. Generate audio from text (TTS)")
    print("2. View system statistics")
    print("3. Manage user accounts")
    print("4. Export analytics data")
    print("5. Configure system settings")
    
    # Demo TTS generation
    print("\n=â Text-to-Speech Generation")
    print("-" * 40)
    
    try:
        from tts import synthesize_speech, list_available_voices
        
        # List available voices
        voices = list_available_voices()
        print(f"Available voices: {len(voices)}")
        for i, voice in enumerate(voices[:5]):  # Show first 5
            print(f"  {i+1}. {voice.name}")
        
        # Example TTS generation
        sample_text = "Welcome to the admin panel demonstration."
        print(f"\nGenerating speech for: '{sample_text}'")
        print("(Note: Actual synthesis requires ElevenLabs API key)")
        
    except ImportError as e:
        print(f"TTS module not available: {e}")
    except Exception as e:
        print(f"Error demonstrating TTS: {e}")
    
    # Demo system stats
    print("\n=Ê System Statistics")
    print("-" * 40)
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python version: {sys.version.split()[0]}")
    print(f"Working directory: {os.getcwd()}")
    
    # Demo file management
    print("\n=Á File Management")
    print("-" * 40)
    temp_dir = Path("temp")
    print(f"Temp directory exists: {temp_dir.exists()}")
    print(f"Number of files in temp: {len(list(temp_dir.glob('*'))) if temp_dir.exists() else 0}")
    
    print("\n( Admin panel demo completed!")

if __name__ == "__main__":
    demo_admin_features()