#!/usr/bin/env python3
"""
Minimal test for audio preprocessing system
"""

import numpy as np

def test_imports():
    """Test basic imports"""
    print("Testing imports...")
    
    try:
        from audio_preprocessing_system import AudioPreprocessingConfig
        print("✓ Imported AudioPreprocessingConfig")
        
        config = AudioPreprocessingConfig()
        print("✓ Created config instance")
        
        from audio_preprocessing_system import AudioPreprocessor
        print("✓ Imported AudioPreprocessor")
        
        # Don't initialize yet, just test import
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_audio():
    """Test basic audio creation"""
    print("\nTesting basic audio operations...")
    
    try:
        # Create simple audio
        sr = 16000
        duration = 0.1  # Very short
        t = np.linspace(0, duration, int(duration * sr), False)
        audio = 0.5 * np.sin(2 * np.pi * 440 * t)
        
        print(f"✓ Created audio: {len(audio)} samples at {sr}Hz")
        
        # Test basic numpy operations
        mean_val = np.mean(audio)
        max_val = np.max(np.abs(audio))
        
        print(f"✓ Audio stats: mean={mean_val:.6f}, max={max_val:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Audio test failed: {e}")
        return False

def main():
    """Run minimal tests"""
    print("Audio Preprocessing - Minimal Tests")
    print("=" * 40)
    
    tests = [test_imports, test_basic_audio]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\nTests: {passed}/{len(tests)} passed")
    return passed == len(tests)

if __name__ == "__main__":
    main()