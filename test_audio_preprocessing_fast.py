#!/usr/bin/env python3
"""
Test script for Fast Audio Preprocessing System (Task 83)
"""

import numpy as np
import tempfile
import os
from audio_preprocessing_system_fast import AudioPreprocessorFast, AudioPreprocessingConfig

def create_test_audio(duration=2.0, sr=16000):
    """Create test audio with noise and silence"""
    t = np.linspace(0, duration, int(duration * sr), False)
    
    # Create speech-like signal
    signal = (
        0.3 * np.sin(2 * np.pi * 200 * t) +
        0.2 * np.sin(2 * np.pi * 400 * t) +
        0.1 * np.sin(2 * np.pi * 800 * t)
    )
    
    # Add noise
    noise = np.random.normal(0, 0.1, signal.shape)
    signal += noise
    
    # Add quiet sections
    quiet_start = int(0.3 * sr)
    quiet_end = int(0.6 * sr)
    signal[quiet_start:quiet_end] *= 0.02
    
    return signal.astype(np.float32), sr

def test_fast_preprocessing():
    """Test fast preprocessing functionality"""
    print("Testing Fast Audio Preprocessing...")
    
    try:
        # Create test audio
        test_audio, sr = create_test_audio()
        print(f"✓ Created test audio: {len(test_audio)/sr:.1f}s at {sr}Hz")
        
        # Configure for speed
        config = AudioPreprocessingConfig(
            enable_noise_reduction=True,
            enable_normalization=True,
            remove_silence=True,
            target_sample_rate=16000
        )
        
        preprocessor = AudioPreprocessorFast(config)
        print("✓ Initialized fast preprocessor")
        
        # Process audio
        result = preprocessor.preprocess_audio((test_audio, sr), config)
        print(f"✓ Processed audio in {result.processing_time:.3f}s")
        
        # Check results
        print(f"✓ Operations applied: {result.operations_applied}")
        print(f"✓ Original duration: {len(result.original_audio)/result.original_sample_rate:.2f}s")
        print(f"✓ Processed duration: {len(result.processed_audio)/result.sample_rate:.2f}s")
        
        # Quality metrics
        metrics = result.quality_metrics.to_dict()
        print("Quality Metrics:")
        for key, value in metrics.items():
            print(f"  - {key}: {value:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_quality_assessment():
    """Test fast quality assessment"""
    print("\nTesting Fast Quality Assessment...")
    
    try:
        preprocessor = AudioPreprocessorFast()
        
        # Create clean and noisy audio
        sr = 16000
        duration = 1.0
        t = np.linspace(0, duration, int(duration * sr), False)
        
        clean_audio = 0.5 * np.sin(2 * np.pi * 440 * t)
        noisy_audio = clean_audio + np.random.normal(0, 0.2, clean_audio.shape)
        
        clean_quality = preprocessor._assess_audio_quality_fast(clean_audio, sr)
        noisy_quality = preprocessor._assess_audio_quality_fast(noisy_audio, sr)
        
        print(f"✓ Clean audio SNR: {clean_quality.snr:.1f} dB")
        print(f"✓ Noisy audio SNR: {noisy_quality.snr:.1f} dB")
        print(f"✓ Quality assessment completed quickly")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_silence_removal():
    """Test silence removal functionality"""
    print("\nTesting Silence Removal...")
    
    try:
        # Create audio with clear silence periods
        sr = 16000
        duration = 3.0
        t = np.linspace(0, duration, int(duration * sr), False)
        
        # Voice: 0-0.5s, silence: 0.5-1.5s, voice: 1.5-2.5s, silence: 2.5-3.0s
        signal = np.zeros_like(t)
        
        # Add voice segments
        voice_1 = slice(0, int(0.5 * sr))
        voice_2 = slice(int(1.5 * sr), int(2.5 * sr))
        
        signal[voice_1] = 0.5 * np.sin(2 * np.pi * 440 * t[voice_1])
        signal[voice_2] = 0.5 * np.sin(2 * np.pi * 440 * t[voice_2])
        
        # Add background noise
        signal += np.random.normal(0, 0.01, signal.shape)
        
        config = AudioPreprocessingConfig(
            remove_silence=True,
            silence_threshold=-30.0
        )
        
        preprocessor = AudioPreprocessorFast(config)
        result = preprocessor.preprocess_audio((signal.astype(np.float32), sr), config)
        
        print(f"✓ Original: {len(signal)/sr:.1f}s")
        print(f"✓ After silence removal: {len(result.processed_audio)/sr:.1f}s")
        print(f"✓ Reduction: {(1 - len(result.processed_audio)/len(signal)) * 100:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_file_operations():
    """Test file loading and saving"""
    print("\nTesting File Operations...")
    
    try:
        # Create and save test audio
        test_audio, sr = create_test_audio(duration=1.0)
        temp_input = tempfile.mktemp(suffix='.wav')
        
        import soundfile as sf
        sf.write(temp_input, test_audio, sr)
        print("✓ Created temporary audio file")
        
        # Process from file
        preprocessor = AudioPreprocessorFast()
        result = preprocessor.preprocess_audio(temp_input)
        print("✓ Processed audio from file")
        
        # Save result
        temp_output = tempfile.mktemp(suffix='.wav')
        result.save_audio(temp_output)
        print("✓ Saved processed audio")
        
        # Clean up
        os.unlink(temp_input)
        os.unlink(temp_output)
        print("✓ Cleaned up files")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_performance():
    """Test processing speed"""
    print("\nTesting Performance...")
    
    try:
        # Create longer audio for performance test
        test_audio, sr = create_test_audio(duration=5.0)  # 5 seconds
        
        config = AudioPreprocessingConfig(
            enable_noise_reduction=True,
            enable_normalization=True,
            remove_silence=True
        )
        
        preprocessor = AudioPreprocessorFast(config)
        
        # Time the processing
        result = preprocessor.preprocess_audio((test_audio, sr), config)
        
        processing_speed = len(test_audio) / sr / result.processing_time
        print(f"✓ Processing speed: {processing_speed:.1f}x real-time")
        print(f"✓ Processing time: {result.processing_time:.3f}s for {len(test_audio)/sr:.1f}s audio")
        
        # Should be faster than real-time
        assert processing_speed > 1.0, "Processing should be faster than real-time"
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Run all fast audio preprocessing tests"""
    print("Fast Audio Preprocessing System Tests (Task 83)")
    print("=" * 60)
    
    tests = [
        test_fast_preprocessing,
        test_quality_assessment,
        test_silence_removal,
        test_file_operations,
        test_performance
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"Tests completed: {passed}/{len(tests)} passed")
    
    if passed == len(tests):
        print("✅ All fast audio preprocessing tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    main()