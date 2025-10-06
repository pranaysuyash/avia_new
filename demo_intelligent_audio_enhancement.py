"""
Demo script for Intelligent Audio Enhancement and Clarity Optimization

This script demonstrates the capabilities of the intelligent audio enhancement system
with various audio types and enhancement modes.
"""

import numpy as np
import matplotlib.pyplot as plt
import soundfile as sf
import tempfile
import os
from typing import Dict, Any
import time

from intelligent_audio_enhancement import (
    IntelligentAudioEnhancer, EnhancementMode, QualityMetric,
    create_test_audio
)

def create_demo_audio_samples() -> Dict[str, np.ndarray]:
    """Create various demo audio samples for testing"""
    sample_rate = 44100
    duration = 3.0
    
    samples = {}
    
    # 1. Clean speech-like signal
    t = np.linspace(0, duration, int(duration * sample_rate))
    fundamental = 200  # Hz
    speech_signal = (
        np.sin(2 * np.pi * fundamental * t) * 0.4 +
        np.sin(2 * np.pi * fundamental * 2 * t) * 0.2 +
        np.sin(2 * np.pi * fundamental * 3 * t) * 0.1
    )
    # Add envelope variation
    envelope = 0.5 + 0.5 * np.sin(2 * np.pi * 0.5 * t)
    samples['clean_speech'] = speech_signal * envelope
    
    # 2. Noisy speech
    noise = np.random.normal(0, 0.1, len(speech_signal))
    samples['noisy_speech'] = speech_signal * envelope + noise
    
    # 3. Low dynamic range (compressed) audio
    compressed_signal = np.tanh(speech_signal * envelope * 3) * 0.3
    samples['compressed_audio'] = compressed_signal
    
    # 4. Frequency-imbalanced audio (too much bass)
    bass_heavy = (
        np.sin(2 * np.pi * 80 * t) * 0.6 +
        np.sin(2 * np.pi * 160 * t) * 0.3 +
        np.sin(2 * np.pi * 1000 * t) * 0.1
    )
    samples['bass_heavy'] = bass_heavy * envelope
    
    # 5. High-frequency dominant (harsh) audio
    treble_heavy = (
        np.sin(2 * np.pi * 200 * t) * 0.1 +
        np.sin(2 * np.pi * 2000 * t) * 0.4 +
        np.sin(2 * np.pi * 4000 * t) * 0.5
    )
    samples['treble_heavy'] = treble_heavy * envelope
    
    return samples

def analyze_audio_characteristics(audio: np.ndarray, sample_rate: int, name: str):
    """Analyze and display audio characteristics"""
    print(f"\n📊 Audio Analysis: {name}")
    print("-" * 40)
    
    # Basic statistics
    rms = np.sqrt(np.mean(audio**2))
    peak = np.max(np.abs(audio))
    crest_factor = peak / rms if rms > 0 else 0
    
    print(f"RMS Level: {rms:.4f}")
    print(f"Peak Level: {peak:.4f}")
    print(f"Crest Factor: {crest_factor:.2f}")
    print(f"Duration: {len(audio)/sample_rate:.2f} seconds")
    
    # Frequency analysis
    fft_result = np.fft.fft(audio)
    freqs = np.fft.fftfreq(len(audio), 1/sample_rate)
    magnitude = np.abs(fft_result)
    
    # Energy in different frequency bands
    low_energy = np.sum(magnitude[(freqs >= 20) & (freqs < 250)])
    mid_energy = np.sum(magnitude[(freqs >= 250) & (freqs < 4000)])
    high_energy = np.sum(magnitude[(freqs >= 4000) & (freqs < sample_rate//2)])
    
    total_energy = low_energy + mid_energy + high_energy
    if total_energy > 0:
        print(f"Low Freq Energy (20-250 Hz): {low_energy/total_energy:.1%}")
        print(f"Mid Freq Energy (250-4000 Hz): {mid_energy/total_energy:.1%}")
        print(f"High Freq Energy (4000+ Hz): {high_energy/total_energy:.1%}")

def demonstrate_enhancement_modes():
    """Demonstrate different enhancement modes"""
    print("\n🎯 Enhancement Modes Demonstration")
    print("=" * 50)
    
    # Create test audio
    test_audio = create_test_audio(duration=2.0)
    sample_rate = 44100
    
    # Initialize enhancer
    enhancer = IntelligentAudioEnhancer()
    
    # Test each enhancement mode
    modes = [
        (EnhancementMode.AUTOMATIC, "Automatic (AI-driven)"),
        (EnhancementMode.SPEECH_FOCUSED, "Speech Focused"),
        (EnhancementMode.MUSIC_FOCUSED, "Music Focused"),
        (EnhancementMode.BROADCAST, "Broadcast Compliant")
    ]
    
    for mode, description in modes:
        print(f"\n🔧 Testing {description}")
        print("-" * 30)
        
        start_time = time.time()
        results = enhancer.enhance_audio(test_audio, sample_rate, mode)
        processing_time = time.time() - start_time
        
        initial_score = results['initial_assessment'].overall_score
        final_score = results['final_assessment'].overall_score
        improvement = results['improvement']
        
        print(f"Processing Time: {processing_time:.2f} seconds")
        print(f"Initial Quality: {initial_score:.3f}")
        print(f"Final Quality: {final_score:.3f}")
        print(f"Improvement: {improvement:+.3f}")
        print(f"Steps Applied: {', '.join(results['processing_steps'])}")
        
        # Show top recommendations
        recommendations = results['final_assessment'].recommendations[:2]
        if recommendations:
            print(f"Top Recommendations: {'; '.join(recommendations)}")

def demonstrate_quality_assessment():
    """Demonstrate quality assessment on different audio types"""
    print("\n📈 Quality Assessment Demonstration")
    print("=" * 50)
    
    # Create demo samples
    demo_samples = create_demo_audio_samples()
    sample_rate = 44100
    
    # Initialize enhancer for quality assessment
    enhancer = IntelligentAudioEnhancer()
    
    for sample_name, audio_data in demo_samples.items():
        print(f"\n🎵 Sample: {sample_name.replace('_', ' ').title()}")
        print("-" * 30)
        
        # Analyze characteristics
        analyze_audio_characteristics(audio_data, sample_rate, sample_name)
        
        # Quality assessment
        assessment = enhancer.quality_assessor.assess_quality(audio_data, sample_rate)
        
        print(f"\n📊 Quality Metrics:")
        print(f"Overall Score: {assessment.overall_score:.3f}")
        print(f"Processing Confidence: {assessment.processing_confidence:.3f}")
        
        # Individual metrics
        for metric, value in assessment.metrics.items():
            metric_name = metric.value.replace('_', ' ').title()
            print(f"  {metric_name}: {value:.3f}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(assessment.recommendations[:3], 1):
            print(f"  {i}. {rec}")

def demonstrate_before_after_enhancement():
    """Demonstrate before/after enhancement comparison"""
    print("\n🔄 Before/After Enhancement Comparison")
    print("=" * 50)
    
    # Create problematic audio sample
    sample_rate = 44100
    duration = 2.0
    t = np.linspace(0, duration, int(duration * sample_rate))
    
    # Create audio with multiple issues
    signal = np.sin(2 * np.pi * 300 * t) * 0.3  # Base signal
    signal += np.random.normal(0, 0.15, len(signal))  # Add noise
    signal = np.tanh(signal * 4) * 0.2  # Add distortion and compress
    
    print("🎵 Original Audio Issues:")
    print("- High noise level")
    print("- Distortion from clipping")
    print("- Low dynamic range")
    print("- Poor frequency balance")
    
    # Initialize enhancer
    enhancer = IntelligentAudioEnhancer()
    
    # Enhance with automatic mode
    print("\n🔧 Applying Automatic Enhancement...")
    results = enhancer.enhance_audio(signal, sample_rate, EnhancementMode.AUTOMATIC)
    
    # Compare before and after
    initial = results['initial_assessment']
    final = results['final_assessment']
    
    print(f"\n📊 Quality Comparison:")
    print(f"{'Metric':<25} {'Before':<10} {'After':<10} {'Change':<10}")
    print("-" * 55)
    
    for metric in QualityMetric:
        before_val = initial.metrics.get(metric, 0)
        after_val = final.metrics.get(metric, 0)
        change = after_val - before_val
        
        metric_name = metric.value.replace('_', ' ').title()[:24]
        print(f"{metric_name:<25} {before_val:<10.3f} {after_val:<10.3f} {change:+.3f}")
    
    print(f"\n🎯 Overall Improvement: {results['improvement']:+.3f}")
    print(f"🔧 Processing Steps: {', '.join(results['processing_steps'])}")

def demonstrate_custom_preferences():
    """Demonstrate custom user preferences"""
    print("\n⚙️  Custom Preferences Demonstration")
    print("=" * 50)
    
    # Create test audio
    test_audio = create_test_audio(duration=1.5)
    sample_rate = 44100
    
    # Initialize enhancer
    enhancer = IntelligentAudioEnhancer()
    
    # Test different preference configurations
    preference_sets = [
        {
            'name': 'Gentle Enhancement',
            'prefs': {
                'spectral_intensity': 0.7,
                'dynamic_intensity': 0.8,
                'clarity_intensity': 0.6
            }
        },
        {
            'name': 'Aggressive Enhancement',
            'prefs': {
                'spectral_intensity': 1.8,
                'dynamic_intensity': 1.5,
                'clarity_intensity': 1.4
            }
        },
        {
            'name': 'Speech Only',
            'prefs': {
                'disable_spectral': True,
                'disable_dynamic': True,
                'clarity_intensity': 1.3
            }
        },
        {
            'name': 'Broadcast Ready',
            'prefs': {
                'target_lufs': -23.0,
                'compression_ratio': 3.0,
                'spectral_intensity': 1.1
            }
        }
    ]
    
    for pref_set in preference_sets:
        print(f"\n🎛️  {pref_set['name']} Settings:")
        print("-" * 30)
        
        results = enhancer.enhance_audio(
            test_audio, sample_rate, 
            EnhancementMode.CUSTOM, 
            pref_set['prefs']
        )
        
        print(f"Quality Improvement: {results['improvement']:+.3f}")
        print(f"Processing Steps: {', '.join(results['processing_steps'])}")
        print(f"Final Quality Score: {results['final_assessment'].overall_score:.3f}")

def save_demo_audio_files():
    """Save demo audio files for listening comparison"""
    print("\n💾 Saving Demo Audio Files")
    print("=" * 50)
    
    # Create output directory
    output_dir = "audio_enhancement_demo_outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create and enhance demo samples
    demo_samples = create_demo_audio_samples()
    sample_rate = 44100
    
    enhancer = IntelligentAudioEnhancer()
    
    for sample_name, audio_data in demo_samples.items():
        print(f"Processing {sample_name}...")
        
        # Save original
        original_path = os.path.join(output_dir, f"{sample_name}_original.wav")
        sf.write(original_path, audio_data, sample_rate)
        
        # Enhance and save
        results = enhancer.enhance_audio(audio_data, sample_rate, EnhancementMode.AUTOMATIC)
        enhanced_path = os.path.join(output_dir, f"{sample_name}_enhanced.wav")
        sf.write(enhanced_path, results['enhanced_audio'], sample_rate)
        
        print(f"  ✅ Saved: {original_path}")
        print(f"  ✅ Saved: {enhanced_path}")
        print(f"  📈 Improvement: {results['improvement']:+.3f}")
    
    print(f"\n📁 All demo files saved to: {output_dir}")

def main():
    """Run the complete demonstration"""
    print("🎵 Intelligent Audio Enhancement System Demo")
    print("=" * 60)
    print("This demo showcases the capabilities of the intelligent audio")
    print("enhancement system with various audio types and processing modes.")
    print("=" * 60)
    
    try:
        # Run demonstrations
        demonstrate_quality_assessment()
        demonstrate_enhancement_modes()
        demonstrate_before_after_enhancement()
        demonstrate_custom_preferences()
        
        # Ask user if they want to save audio files
        print("\n" + "=" * 60)
        save_files = input("Would you like to save demo audio files? (y/n): ").lower().strip()
        if save_files in ['y', 'yes']:
            save_demo_audio_files()
        
        print("\n🎉 Demo completed successfully!")
        print("\nKey Features Demonstrated:")
        print("✅ Spectral enhancement with frequency-specific processing")
        print("✅ Dynamic range optimization and loudness management")
        print("✅ Speech clarity enhancement with intelligibility optimization")
        print("✅ Automatic audio quality improvement with user control")
        print("✅ Multiple enhancement modes for different use cases")
        print("✅ Comprehensive quality assessment and recommendations")
        
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()