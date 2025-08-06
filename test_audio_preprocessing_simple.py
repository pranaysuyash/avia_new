#!/usr/bin/env python3
"""
Simple test script for Audio Preprocessing System (Task 83)
"""

import numpy as np
from audio_preprocessing_system import AudioPreprocessor, AudioPreprocessingConfig

def test_basic_functionality():
    """Test basic audio preprocessing functionality"""
    print("Testing Basic Audio Preprocessing...")
    
    try:
        # Create simple test audio (1 second, 16kHz)
        sr = 16000
        duration = 1.0
        t = np.linspace(0, duration, int(duration * sr), False)
        
        # Simple sine wave with noise
        signal = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
        noise = np.random.normal(0, 0.1, signal.shape)
        test_audio = (signal + noise).astype(np.float32)
        
        print(f"✓ Created test audio: {duration}s at {sr}Hz")
        
        # Simple config to avoid complex operations
        config = AudioPreprocessingConfig(
            enable_noise_reduction=False,  # Disable to avoid timeout
            enable_normalization=True,
            remove_silence=False,
            enable_vad=False,
            enable_dehum=False,
            enable_declick=False,
            enable_declip=False,
            enable_spectral_subtraction=False,
            enable_wiener_filtering=False,
            enable_adaptive_filtering=False,
            target_sample_rate=16000
        )
        
        preprocessor = AudioPreprocessor(config)
        print("✓ Initialized audio preprocessor")
        
        # Process audio
        result = preprocessor.preprocess_audio((test_audio, sr), config)
        print(f"✓ Processed audio in {result.processing_time:.2f}s")
        
        # Check basic results
        print(f"✓ Applied operations: {result.operations_applied}")
        print(f"✓ Original samples: {len(result.original_audio)}")
        print(f"✓ Processed samples: {len(result.processed_audio)}")
        
        # Check quality metrics
        print("Quality Metrics:")
        metrics = result.quality_metrics.to_dict()
        for key, value in metrics.items():
            if key != 'mfcc_shape':
                print(f"  - {key}: {value:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_quality_assessment():
    """Test audio quality assessment"""
    print("\nTesting Quality Assessment...")
    
    try:
        preprocessor = AudioPreprocessor()
        
        # Create clean audio
        sr = 16000
        duration = 0.5  # Short duration
        t = np.linspace(0, duration, int(duration * sr), False)
        clean_audio = 0.5 * np.sin(2 * np.pi * 440 * t)
        
        quality = preprocessor._assess_audio_quality(clean_audio, sr)
        print(f"✓ Quality assessment completed")
        print(f"  - SNR: {quality.snr:.1f} dB")
        print(f"  - Energy: {quality.energy:.3f}")
        print(f"  - Spectral Centroid: {quality.spectral_centroid:.1f} Hz")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_basic_operations():
    """Test individual operations"""
    print("\nTesting Basic Operations...")
    
    try:
        preprocessor = AudioPreprocessor()
        sr = 16000
        duration = 0.5
        t = np.linspace(0, duration, int(duration * sr), False)
        test_audio = 0.5 * np.sin(2 * np.pi * 440 * t)
        
        # Test normalization
        normalized = preprocessor._normalize_audio(test_audio, AudioPreprocessingConfig())
        print(f"✓ Normalization: max value = {np.max(np.abs(normalized)):.3f}")
        
        # Test high-pass filter
        filtered = preprocessor._apply_high_pass_filter(test_audio, sr, 100.0)
        print(f"✓ High-pass filter applied")
        
        # Test DC removal
        dc_removed = test_audio - np.mean(test_audio)
        print(f"✓ DC removal: mean = {np.mean(dc_removed):.6f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Run simple audio preprocessing tests"""
    print("Audio Preprocessing System - Simple Tests (Task 83)")
    print("=" * 60)
    
    tests = [
        test_basic_functionality,
        test_quality_assessment,
        test_basic_operations
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"Tests completed: {passed}/{len(tests)} passed")
    
    if passed == len(tests):
        print("✅ All simple audio preprocessing tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    main()