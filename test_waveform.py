#!/usr/bin/env python3
"""
Test script for waveform visualization functionality
"""

import os
import sys
import tempfile
import numpy as np
import soundfile as sf
from waveform_visualizer import waveform_visualizer, audio_navigator

def create_test_audio():
    """Create a test audio file for testing"""
    # Generate a simple test audio signal
    duration = 10  # seconds
    sample_rate = 16000
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create a signal with different frequencies to make an interesting waveform
    signal = (np.sin(2 * np.pi * 440 * t) * 0.3 +  # A4 note
              np.sin(2 * np.pi * 880 * t) * 0.2 +  # A5 note
              np.sin(2 * np.pi * 220 * t) * 0.1)   # A3 note
    
    # Add some amplitude variation
    envelope = np.exp(-t/5) + 0.3  # Exponential decay with offset
    signal = signal * envelope
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        sf.write(temp_file.name, signal, sample_rate)
        return temp_file.name

def test_waveform_generation():
    """Test basic waveform generation"""
    print("Testing waveform generation...")
    
    try:
        # Create test audio
        audio_path = create_test_audio()
        print(f"Created test audio: {audio_path}")
        
        # Generate waveform
        waveform_path = waveform_visualizer.generate_waveform_image(audio_path)
        print(f"Generated waveform: {waveform_path}")
        
        # Check if file exists
        if os.path.exists(waveform_path):
            print("✅ Waveform generation successful!")
            file_size = os.path.getsize(waveform_path)
            print(f"   Waveform image size: {file_size} bytes")
        else:
            print("❌ Waveform file not created")
            return False
        
        # Test timeline waveform
        timeline_path = waveform_visualizer.create_waveform_with_timeline(audio_path)
        print(f"Generated timeline waveform: {timeline_path}")
        
        if os.path.exists(timeline_path):
            print("✅ Timeline waveform generation successful!")
        else:
            print("❌ Timeline waveform file not created")
            return False
        
        # Test interactive data generation
        interactive_data = waveform_visualizer.generate_interactive_waveform_data(audio_path)
        print(f"Generated interactive data with {len(interactive_data['segments'])} segments")
        print(f"Total duration: {interactive_data['total_duration']:.1f}s")
        
        # Test audio navigator
        audio_navigator.initialize_navigation(audio_path)
        nav_data = audio_navigator.get_navigation_controls()
        print(f"Navigation initialized: {len(nav_data['segments'])} segments")
        
        # Cleanup
        os.unlink(audio_path)
        os.unlink(waveform_path)
        os.unlink(timeline_path)
        
        print("✅ All waveform tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Waveform test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_with_speaker_segments():
    """Test waveform with speaker segments"""
    print("\nTesting waveform with speaker segments...")
    
    try:
        # Create test audio
        audio_path = create_test_audio()
        
        # Create mock speaker segments
        speaker_segments = [
            {'start': 0, 'end': 3, 'speaker': 'Speaker 1'},
            {'start': 3, 'end': 6, 'speaker': 'Speaker 2'},
            {'start': 6, 'end': 10, 'speaker': 'Speaker 1'}
        ]
        
        # Generate waveform with speaker markers
        waveform_path = waveform_visualizer.generate_waveform_image(
            audio_path, 
            speaker_segments=speaker_segments
        )
        
        if os.path.exists(waveform_path):
            print("✅ Waveform with speaker segments generated successfully!")
            
            # Cleanup
            os.unlink(audio_path)
            os.unlink(waveform_path)
            return True
        else:
            print("❌ Waveform with speaker segments failed")
            return False
            
    except Exception as e:
        print(f"❌ Speaker segments test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🌊 Testing Waveform Visualization Module")
    print("=" * 50)
    
    # Run tests
    test1_passed = test_waveform_generation()
    test2_passed = test_with_speaker_segments()
    
    print("\n" + "=" * 50)
    if test1_passed and test2_passed:
        print("🎉 All tests passed! Waveform visualization is working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Check the error messages above.")
        sys.exit(1)