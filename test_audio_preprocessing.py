#!/usr/bin/env python3
"""
Test script for Audio Preprocessing System (Task 83)
"""

import numpy as np
import tempfile
import os
import librosa
import soundfile as sf
from audio_preprocessing_system import AudioPreprocessor, AudioPreprocessingConfig

def create_test_audio_with_issues(duration=5.0, sr=16000):
    """Create a test audio signal with various issues to test preprocessing"""
    # Create base signal (sine wave + speech-like frequencies)
    t = np.linspace(0, duration, int(duration * sr), False)
    
    # Base speech-like signal (multiple frequencies)
    signal = (
        0.3 * np.sin(2 * np.pi * 200 * t) +      # Fundamental
        0.2 * np.sin(2 * np.pi * 400 * t) +      # Harmonic
        0.1 * np.sin(2 * np.pi * 800 * t) +      # Higher harmonic
        0.1 * np.sin(2 * np.pi * 150 * t)        # Lower component
    )
    
    # Add noise
    noise = np.random.normal(0, 0.1, signal.shape)
    signal += noise
    
    # Add 60Hz hum
    hum = 0.05 * np.sin(2 * np.pi * 60 * t)
    signal += hum
    
    # Add some clicks (impulse noise)
    click_positions = np.random.choice(len(signal), size=10, replace=False)
    for pos in click_positions:
        if pos < len(signal) - 5:
            signal[pos:pos+5] += np.random.uniform(-0.5, 0.5, 5)
    
    # Add quiet sections (silence)
    quiet_start = int(0.2 * sr)
    quiet_end = int(0.5 * sr)
    signal[quiet_start:quiet_end] *= 0.02
    
    quiet_start2 = int(3.5 * sr)
    quiet_end2 = int(4.0 * sr)
    signal[quiet_start2:quiet_end2] *= 0.02
    
    # Normalize to prevent clipping during processing
    signal = signal / np.max(np.abs(signal)) * 0.8
    
    return signal.astype(np.float32), sr

def test_basic_preprocessing():
    """Test basic preprocessing functionality"""
    print("Testing Basic Audio Preprocessing...")
    
    try:
        # Create test audio
        test_audio, sr = create_test_audio_with_issues()
        print(f"✓ Created test audio: {len(test_audio)/sr:.1f}s at {sr}Hz")
        
        # Initialize preprocessor
        config = AudioPreprocessingConfig(
            enable_noise_reduction=True,
            enable_normalization=True,
            remove_silence=True,
            enable_dehum=True
        )
        preprocessor = AudioPreprocessor(config)
        print("✓ Initialized audio preprocessor")
        
        # Process audio
        result = preprocessor.preprocess_audio((test_audio, sr), config)
        print(f"✓ Processed audio in {result.processing_time:.2f}s")
        
        # Check operations
        print(f"✓ Applied operations: {result.operations_applied}")
        print(f"✓ Original duration: {len(result.original_audio)/result.original_sample_rate:.2f}s")
        print(f"✓ Processed duration: {len(result.processed_audio)/result.sample_rate:.2f}s")
        
        # Check quality metrics
        print("Quality Metrics:")
        metrics = result.quality_metrics.to_dict()
        for metric, value in metrics.items():
            if metric != 'mfcc_shape':
                print(f"  - {metric}: {value:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_different_configurations():
    """Test different preprocessing configurations"""
    print("\nTesting Different Configurations...")
    
    try:
        test_audio, sr = create_test_audio_with_issues()
        
        # Test different configs
        configs = [
            ("Minimal", AudioPreprocessingConfig(
                enable_noise_reduction=True,
                enable_normalization=False,
                remove_silence=False
            )),
            ("Transcription Optimized", AudioPreprocessingConfig(
                enable_noise_reduction=True,
                noise_reduction_strength=0.8,
                enable_normalization=True,
                remove_silence=True,
                enable_vad=True,
                target_sample_rate=16000
            )),
            ("High Quality", AudioPreprocessingConfig(
                enable_noise_reduction=True,
                noise_reduction_method="spectral_gating",
                enable_normalization=True,
                normalization_method="lufs",
                enable_dynamic_range_compression=True,
                enable_dehum=True,
                enable_declick=True,
                remove_silence=True,
                enable_vad=True
            ))
        ]
        
        preprocessor = AudioPreprocessor()
        
        for name, config in configs:
            print(f"\n  Testing {name} configuration:")
            result = preprocessor.preprocess_audio((test_audio, sr), config)
            print(f"    - Processing time: {result.processing_time:.2f}s")
            print(f"    - Operations: {len(result.operations_applied)}")
            print(f"    - SNR: {result.quality_metrics.snr:.1f} dB")
            print(f"    - Duration change: {(len(result.processed_audio) - len(test_audio))/len(test_audio)*100:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_voice_activity_detection():
    """Test voice activity detection functionality"""
    print("\nTesting Voice Activity Detection...")
    
    try:
        # Create audio with clear voice/silence pattern
        sr = 16000
        duration = 6.0
        t = np.linspace(0, duration, int(duration * sr), False)
        
        # Create signal with alternating voice and silence
        signal = np.zeros_like(t)
        
        # Voice segments: 0-1s, 2-3s, 4-5s
        voice_segments = [(0, 1), (2, 3), (4, 5)]
        
        for start, end in voice_segments:
            start_idx = int(start * sr)
            end_idx = int(end * sr)
            # Add speech-like signal
            t_segment = t[start_idx:end_idx]
            signal[start_idx:end_idx] = (
                0.5 * np.sin(2 * np.pi * 200 * t_segment) +
                0.3 * np.sin(2 * np.pi * 400 * t_segment) +
                0.1 * np.random.normal(0, 0.1, len(t_segment))
            )
        
        # Add background noise throughout
        signal += np.random.normal(0, 0.02, signal.shape)
        
        config = AudioPreprocessingConfig(
            enable_vad=True,
            remove_silence=True,
            vad_method="energy",
            vad_threshold=0.01
        )
        
        preprocessor = AudioPreprocessor(config)
        result = preprocessor.preprocess_audio((signal.astype(np.float32), sr), config)
        
        print(f"✓ Original duration: {len(signal)/sr:.1f}s")
        print(f"✓ Processed duration: {len(result.processed_audio)/sr:.1f}s")
        print(f"✓ Detected {len(result.segments)} voice segments")
        
        if result.segments:
            for i, (start, end) in enumerate(result.segments):
                print(f"    Segment {i+1}: {start:.2f}s - {end:.2f}s ({end-start:.2f}s)")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_noise_reduction_methods():
    """Test different noise reduction methods"""
    print("\nTesting Noise Reduction Methods...")
    
    try:
        # Create very noisy audio
        clean_audio, sr = create_test_audio_with_issues(duration=3.0)
        
        # Add extra noise
        noise = np.random.normal(0, 0.3, clean_audio.shape)
        noisy_audio = clean_audio + noise
        
        methods = ["spectral_gating", "wiener", "adaptive"]
        preprocessor = AudioPreprocessor()
        
        # Assess initial quality
        initial_quality = preprocessor._assess_audio_quality(noisy_audio, sr)
        print(f"  Initial SNR: {initial_quality.snr:.1f} dB")
        
        for method in methods:
            config = AudioPreprocessingConfig(
                enable_noise_reduction=True,
                noise_reduction_method=method,
                noise_reduction_strength=0.7
            )
            
            result = preprocessor.preprocess_audio((noisy_audio, sr), config)
            print(f"  {method.capitalize()}: SNR = {result.quality_metrics.snr:.1f} dB "
                  f"(improvement: {result.quality_metrics.snr - initial_quality.snr:.1f} dB)")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_file_operations():
    """Test file loading and saving operations"""
    print("\nTesting File Operations...")
    
    try:
        # Create and save test audio
        test_audio, sr = create_test_audio_with_issues()
        temp_input = tempfile.mktemp(suffix='.wav')
        sf.write(temp_input, test_audio, sr)
        print("✓ Created temporary test audio file")
        
        # Process from file
        preprocessor = AudioPreprocessor()
        result = preprocessor.preprocess_audio(temp_input)
        print("✓ Processed audio from file path")
        
        # Save processed audio
        temp_output = tempfile.mktemp(suffix='.wav')
        result.save_audio(temp_output)
        print("✓ Saved processed audio")
        
        # Verify saved file
        saved_audio, saved_sr = sf.read(temp_output)
        print(f"✓ Verified saved audio: {len(saved_audio)/saved_sr:.1f}s at {saved_sr}Hz")
        
        # Clean up
        os.unlink(temp_input)
        os.unlink(temp_output)
        print("✓ Cleaned up temporary files")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_quality_assessment():
    """Test audio quality assessment"""
    print("\nTesting Quality Assessment...")
    
    try:
        preprocessor = AudioPreprocessor()
        
        # Create different quality audio samples
        sr = 16000
        duration = 2.0
        t = np.linspace(0, duration, int(duration * sr), False)
        
        # High quality audio
        high_quality = 0.5 * np.sin(2 * np.pi * 440 * t)  # Pure tone
        quality_hq = preprocessor._assess_audio_quality(high_quality, sr)
        
        # Low quality audio (noisy)
        low_quality = high_quality + np.random.normal(0, 0.2, high_quality.shape)
        quality_lq = preprocessor._assess_audio_quality(low_quality, sr)
        
        print(f"  High Quality Audio:")
        print(f"    - SNR: {quality_hq.snr:.1f} dB")
        print(f"    - Dynamic Range: {quality_hq.dynamic_range:.1f} dB")
        print(f"    - Energy: {quality_hq.energy:.3f}")
        
        print(f"  Low Quality Audio:")
        print(f"    - SNR: {quality_lq.snr:.1f} dB")
        print(f"    - Dynamic Range: {quality_lq.dynamic_range:.1f} dB")
        print(f"    - Energy: {quality_lq.energy:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Run all audio preprocessing tests"""
    print("Audio Preprocessing System Tests (Task 83)")
    print("=" * 60)
    
    tests = [
        test_basic_preprocessing,
        test_different_configurations,
        test_voice_activity_detection,
        test_noise_reduction_methods,
        test_file_operations,
        test_quality_assessment
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"Tests completed: {passed}/{len(tests)} passed")
    
    if passed == len(tests):
        print("✅ All audio preprocessing tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    main()