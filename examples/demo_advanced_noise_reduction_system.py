"""
Demo script for Advanced Noise Reduction System

This script demonstrates the capabilities of the advanced noise reduction and audio
restoration system with various test scenarios and audio examples.
"""

import numpy as np
import librosa
import soundfile as sf
import matplotlib.pyplot as plt
import time
import os
from typing import Dict, List, Tuple

from advanced_noise_reduction_system import (
    AdvancedNoiseReductionSystem,
    RestorationSettings,
    NoiseType,
    ArtifactType,
    create_test_audio
)

def create_comprehensive_test_audio(duration: float = 10.0, sr: int = 44100) -> Dict[str, np.ndarray]:
    """Create comprehensive test audio with various noise types and artifacts"""
    
    test_cases = {}
    t = np.linspace(0, duration, int(duration * sr))
    
    # 1. Clean speech-like signal
    clean_signal = (
        np.sin(2 * np.pi * 440 * t) * np.exp(-t * 0.3) +  # Fundamental
        0.5 * np.sin(2 * np.pi * 880 * t) * np.exp(-t * 0.4) +  # First harmonic
        0.3 * np.sin(2 * np.pi * 1320 * t) * np.exp(-t * 0.5)   # Second harmonic
    )
    
    # Add speech-like modulation
    modulation = 1 + 0.3 * np.sin(2 * np.pi * 5 * t)  # 5 Hz modulation
    clean_signal *= modulation
    
    test_cases['clean'] = clean_signal * 0.5
    
    # 2. Broadband noise
    broadband_noise = 0.3 * np.random.normal(0, 1, len(t))
    test_cases['broadband_noise'] = clean_signal * 0.5 + broadband_noise
    
    # 3. Tonal noise (multiple frequencies)
    tonal_noise = (
        0.2 * np.sin(2 * np.pi * 60 * t) +    # 60 Hz hum
        0.15 * np.sin(2 * np.pi * 120 * t) +  # 120 Hz harmonic
        0.1 * np.sin(2 * np.pi * 1000 * t) +  # 1 kHz tone
        0.08 * np.sin(2 * np.pi * 2500 * t)   # 2.5 kHz tone
    )
    test_cases['tonal_noise'] = clean_signal * 0.5 + tonal_noise
    
    # 4. Impulsive noise (clicks and pops)
    impulsive_signal = clean_signal * 0.5
    # Add clicks
    click_times = np.random.choice(len(t), size=20, replace=False)
    for click_time in click_times:
        if click_time < len(t) - 5:
            # Sharp click
            impulsive_signal[click_time:click_time+3] += 1.5 * np.random.choice([-1, 1])
    
    # Add pops (longer duration)
    pop_times = np.random.choice(len(t), size=5, replace=False)
    for pop_time in pop_times:
        pop_duration = int(sr * 0.01)  # 10ms pops
        if pop_time < len(t) - pop_duration:
            pop_envelope = np.exp(-np.linspace(0, 5, pop_duration))
            impulsive_signal[pop_time:pop_time+pop_duration] += 0.8 * pop_envelope * np.random.choice([-1, 1])
    
    test_cases['impulsive_noise'] = impulsive_signal
    
    # 5. Mixed noise (realistic scenario)
    mixed_noise = (
        0.2 * np.random.normal(0, 1, len(t)) +  # Broadband
        0.15 * np.sin(2 * np.pi * 60 * t) +     # Hum
        0.1 * np.sin(2 * np.pi * 120 * t)       # Harmonic
    )
    
    mixed_signal = clean_signal * 0.5 + mixed_noise
    
    # Add some clicks
    click_times = np.random.choice(len(t), size=8, replace=False)
    for click_time in click_times:
        if click_time < len(t) - 2:
            mixed_signal[click_time:click_time+2] += 1.0 * np.random.choice([-1, 1])
    
    test_cases['mixed_noise'] = mixed_signal
    
    # 6. Clipped audio
    clipped_signal = clean_signal * 1.2
    clipped_signal = np.clip(clipped_signal, -0.8, 0.8)  # Hard clipping
    test_cases['clipped'] = clipped_signal
    
    # 7. Audio with missing segments
    missing_segments_signal = clean_signal * 0.5
    # Create gaps
    gap_starts = [int(sr * 2), int(sr * 5), int(sr * 8)]
    gap_durations = [int(sr * 0.1), int(sr * 0.2), int(sr * 0.15)]
    
    for start, duration in zip(gap_starts, gap_durations):
        if start + duration < len(missing_segments_signal):
            missing_segments_signal[start:start+duration] = 0
    
    test_cases['missing_segments'] = missing_segments_signal
    
    # Normalize all test cases
    for key in test_cases:
        max_val = np.max(np.abs(test_cases[key]))
        if max_val > 0:
            test_cases[key] = test_cases[key] / max_val * 0.8
    
    return test_cases

def analyze_audio_quality(audio: np.ndarray, sr: int) -> Dict[str, float]:
    """Analyze audio quality metrics"""
    
    # RMS energy
    rms = np.sqrt(np.mean(audio**2))
    
    # Peak amplitude
    peak = np.max(np.abs(audio))
    
    # Crest factor (peak to RMS ratio)
    crest_factor = peak / (rms + 1e-10)
    
    # Spectral centroid (brightness)
    stft = librosa.stft(audio, n_fft=2048, hop_length=512)
    spectral_centroid = np.mean(librosa.feature.spectral_centroid(S=np.abs(stft))[0])
    
    # Spectral rolloff
    spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(S=np.abs(stft))[0])
    
    # Zero crossing rate (roughness indicator)
    zcr = np.mean(librosa.feature.zero_crossing_rate(audio)[0])
    
    # Estimate SNR (simplified)
    # Use high-frequency content as noise estimate
    high_freq_filter = librosa.effects.preemphasis(audio)
    noise_estimate = np.std(high_freq_filter)
    signal_estimate = rms
    snr_estimate = 20 * np.log10((signal_estimate + 1e-10) / (noise_estimate + 1e-10))
    
    return {
        'rms_energy': rms,
        'peak_amplitude': peak,
        'crest_factor': crest_factor,
        'spectral_centroid': spectral_centroid,
        'spectral_rolloff': spectral_rolloff,
        'zero_crossing_rate': zcr,
        'estimated_snr_db': snr_estimate
    }

def run_comprehensive_demo():
    """Run comprehensive demonstration of the noise reduction system"""
    
    print("🎵 Advanced Noise Reduction System - Comprehensive Demo")
    print("=" * 60)
    
    # Initialize system
    system = AdvancedNoiseReductionSystem()
    sr = 44100
    
    # Create test audio cases
    print("\n📊 Creating test audio cases...")
    test_cases = create_comprehensive_test_audio(duration=5.0, sr=sr)
    
    # Test different settings configurations
    settings_configs = {
        'conservative': RestorationSettings(
            noise_reduction_strength=0.4,
            preserve_speech_quality=True,
            artifact_removal_sensitivity=0.6,
            spectral_enhancement=False,
            dynamic_range_optimization=False,
            ai_reconstruction=False,
            processing_mode='conservative'
        ),
        'balanced': RestorationSettings(
            noise_reduction_strength=0.7,
            preserve_speech_quality=True,
            artifact_removal_sensitivity=0.8,
            spectral_enhancement=True,
            dynamic_range_optimization=True,
            ai_reconstruction=True,
            processing_mode='adaptive'
        ),
        'aggressive': RestorationSettings(
            noise_reduction_strength=0.9,
            preserve_speech_quality=False,
            artifact_removal_sensitivity=1.0,
            spectral_enhancement=True,
            dynamic_range_optimization=True,
            ai_reconstruction=True,
            processing_mode='aggressive'
        )
    }
    
    results = {}
    
    # Process each test case with each setting
    for case_name, audio in test_cases.items():
        print(f"\n🔧 Processing: {case_name}")
        results[case_name] = {}
        
        # Analyze original audio quality
        original_quality = analyze_audio_quality(audio, sr)
        results[case_name]['original'] = {
            'quality_metrics': original_quality,
            'audio': audio
        }
        
        for setting_name, settings in settings_configs.items():
            print(f"  - {setting_name} settings...", end=' ')
            
            start_time = time.time()
            result = system.process_audio(audio, sr, settings)
            processing_time = time.time() - start_time
            
            # Analyze processed audio quality
            processed_quality = analyze_audio_quality(result.restored_audio, sr)
            
            results[case_name][setting_name] = {
                'result': result,
                'quality_metrics': processed_quality,
                'processing_time': processing_time
            }
            
            print(f"✅ ({processing_time:.2f}s, confidence: {result.confidence_score:.2f})")
    
    # Generate comprehensive report
    print("\n📋 COMPREHENSIVE RESULTS REPORT")
    print("=" * 60)
    
    for case_name, case_results in results.items():
        print(f"\n🎯 Test Case: {case_name.upper()}")
        print("-" * 40)
        
        original_metrics = case_results['original']['quality_metrics']
        print(f"Original SNR: {original_metrics['estimated_snr_db']:.1f} dB")
        print(f"Original RMS: {original_metrics['rms_energy']:.3f}")
        
        for setting_name in ['conservative', 'balanced', 'aggressive']:
            if setting_name in case_results:
                setting_results = case_results[setting_name]
                result = setting_results['result']
                processed_metrics = setting_results['quality_metrics']
                
                print(f"\n  {setting_name.title()} Processing:")
                print(f"    - Processing time: {setting_results['processing_time']:.2f}s")
                print(f"    - Confidence: {result.confidence_score:.2%}")
                print(f"    - Noise reduction: {result.noise_reduction_applied:.1%}")
                print(f"    - Artifacts removed: {len(result.artifacts_removed)}")
                print(f"    - SNR improvement: {processed_metrics['estimated_snr_db'] - original_metrics['estimated_snr_db']:+.1f} dB")
                
                if result.artifacts_removed:
                    artifacts_str = ', '.join([art.value for art in result.artifacts_removed])
                    print(f"    - Artifact types: {artifacts_str}")
    
    # Performance summary
    print(f"\n⚡ PERFORMANCE SUMMARY")
    print("-" * 30)
    
    all_times = []
    all_confidences = []
    
    for case_results in results.values():
        for setting_name in ['conservative', 'balanced', 'aggressive']:
            if setting_name in case_results:
                all_times.append(case_results[setting_name]['processing_time'])
                all_confidences.append(case_results[setting_name]['result'].confidence_score)
    
    print(f"Average processing time: {np.mean(all_times):.2f}s")
    print(f"Average confidence score: {np.mean(all_confidences):.2%}")
    print(f"Processing time range: {np.min(all_times):.2f}s - {np.max(all_times):.2f}s")
    
    # Save sample outputs
    print(f"\n💾 Saving sample outputs...")
    output_dir = "noise_reduction_demo_outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save a few representative examples
    sample_cases = ['mixed_noise', 'tonal_noise', 'impulsive_noise']
    
    for case_name in sample_cases:
        if case_name in results:
            case_results = results[case_name]
            
            # Save original
            original_path = os.path.join(output_dir, f"{case_name}_original.wav")
            sf.write(original_path, case_results['original']['audio'], sr)
            
            # Save balanced processing result
            if 'balanced' in case_results:
                processed_path = os.path.join(output_dir, f"{case_name}_processed.wav")
                processed_audio = case_results['balanced']['result'].restored_audio
                sf.write(processed_path, processed_audio, sr)
    
    print(f"Sample audio files saved to: {output_dir}/")
    
    return results

def demo_specific_features():
    """Demonstrate specific features of the system"""
    
    print("\n🔬 FEATURE-SPECIFIC DEMONSTRATIONS")
    print("=" * 50)
    
    system = AdvancedNoiseReductionSystem()
    sr = 44100
    
    # 1. Noise Profile Analysis
    print("\n1. 🔍 Noise Profile Analysis")
    print("-" * 30)
    
    test_audio = create_test_audio(duration=3.0, sr=sr)
    noise_profile = system.noise_reducer.analyze_noise_profile(test_audio, sr)
    
    print(f"Detected noise type: {noise_profile.noise_type.value}")
    print(f"Analysis confidence: {noise_profile.confidence:.2%}")
    print(f"Recommended reduction: {noise_profile.recommended_reduction:.1%}")
    print(f"Temporal characteristics: {len(noise_profile.temporal_characteristics)} metrics")
    
    # 2. Artifact Detection
    print("\n2. ⚠️ Artifact Detection")
    print("-" * 25)
    
    artifacts = system.artifact_remover.detect_artifacts(test_audio, sr)
    print(f"Detected artifact types: {len(artifacts)}")
    
    for artifact_type, locations in artifacts.items():
        print(f"  - {artifact_type.value}: {len(locations)} instances")
    
    # 3. Spectral Enhancement
    print("\n3. 🎨 Spectral Enhancement")
    print("-" * 26)
    
    clean_audio = np.sin(2 * np.pi * 440 * np.linspace(0, 2, sr * 2))
    enhanced_audio = system.spectral_enhancer.enhance_spectrum(clean_audio, sr, 0.5)
    
    original_centroid = np.mean(librosa.feature.spectral_centroid(y=clean_audio, sr=sr)[0])
    enhanced_centroid = np.mean(librosa.feature.spectral_centroid(y=enhanced_audio, sr=sr)[0])
    
    print(f"Original spectral centroid: {original_centroid:.0f} Hz")
    print(f"Enhanced spectral centroid: {enhanced_centroid:.0f} Hz")
    print(f"Enhancement effect: {((enhanced_centroid - original_centroid) / original_centroid * 100):+.1f}%")
    
    # 4. AI Reconstruction
    print("\n4. 🤖 AI Reconstruction")
    print("-" * 22)
    
    # Create audio with missing segments
    audio_with_gaps = clean_audio.copy()
    gap_start = sr // 2
    gap_end = gap_start + sr // 10  # 100ms gap
    audio_with_gaps[gap_start:gap_end] = 0
    
    missing_segments = system.ai_reconstructor.detect_missing_segments(audio_with_gaps, sr)
    print(f"Detected missing segments: {len(missing_segments)}")
    
    if missing_segments:
        reconstructed = system.ai_reconstructor.reconstruct_segments(
            audio_with_gaps, sr, missing_segments
        )
        
        # Calculate reconstruction quality
        original_segment = clean_audio[gap_start:gap_end]
        reconstructed_segment = reconstructed[gap_start:gap_end]
        
        mse = np.mean((original_segment - reconstructed_segment)**2)
        print(f"Reconstruction MSE: {mse:.6f}")
        print(f"Reconstruction quality: {'Good' if mse < 0.01 else 'Fair' if mse < 0.1 else 'Poor'}")

def benchmark_performance():
    """Benchmark system performance with different audio lengths and settings"""
    
    print("\n⚡ PERFORMANCE BENCHMARKING")
    print("=" * 35)
    
    system = AdvancedNoiseReductionSystem()
    sr = 44100
    
    # Test different audio durations
    durations = [1.0, 5.0, 10.0, 30.0]  # seconds
    
    # Different complexity settings
    settings_list = [
        ('minimal', RestorationSettings(
            noise_reduction_strength=0.5,
            preserve_speech_quality=True,
            artifact_removal_sensitivity=0.5,
            spectral_enhancement=False,
            dynamic_range_optimization=False,
            ai_reconstruction=False
        )),
        ('full', RestorationSettings(
            noise_reduction_strength=0.8,
            preserve_speech_quality=True,
            artifact_removal_sensitivity=0.8,
            spectral_enhancement=True,
            dynamic_range_optimization=True,
            ai_reconstruction=True
        ))
    ]
    
    print(f"{'Duration':<10} {'Settings':<10} {'Time (s)':<10} {'Speed':<15} {'Memory':<10}")
    print("-" * 65)
    
    for duration in durations:
        # Create test audio
        test_audio = create_test_audio(duration=duration, sr=sr)
        
        for settings_name, settings in settings_list:
            # Measure processing time
            start_time = time.time()
            result = system.process_audio(test_audio, sr, settings)
            processing_time = time.time() - start_time
            
            # Calculate real-time factor
            real_time_factor = duration / processing_time
            
            print(f"{duration:<10.1f} {settings_name:<10} {processing_time:<10.2f} "
                  f"{real_time_factor:<15.1f}x {'N/A':<10}")
    
    print(f"\nNote: Speed factor >1.0x means faster than real-time processing")

if __name__ == "__main__":
    try:
        # Run comprehensive demo
        results = run_comprehensive_demo()
        
        # Run feature-specific demos
        demo_specific_features()
        
        # Run performance benchmarks
        benchmark_performance()
        
        print(f"\n✅ Demo completed successfully!")
        print(f"Check the 'noise_reduction_demo_outputs' directory for sample audio files.")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()