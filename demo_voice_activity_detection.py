"""
Voice Activity Detection (VAD) System Demo
Demonstrates comprehensive voice activity detection capabilities including
multiple VAD methods, silence removal, and audio quality assessment
"""

import os
import sys
import numpy as np
import librosa
import soundfile as sf
import matplotlib.pyplot as plt
from voice_activity_detection import (
    VoiceActivityDetector, VADMethod, VADResult, AudioQualityMetrics
)
import tempfile
import time
from datetime import datetime

def create_demo_audio():
    """Create a demo audio file with speech and silence segments"""
    print("🎵 Creating demo audio file...")
    
    # Parameters
    sr = 16000  # Sample rate
    duration = 10  # Total duration in seconds
    
    # Create time axis
    t = np.linspace(0, duration, int(sr * duration))
    
    # Create audio segments
    audio = np.zeros_like(t)
    
    # Speech segments (sine waves with varying frequencies)
    speech_segments = [
        (1, 2.5, 440),    # A4 note
        (3.5, 5, 523),    # C5 note
        (6, 7.5, 659),    # E5 note
        (8.5, 9.5, 784)   # G5 note
    ]
    
    for start, end, freq in speech_segments:
        start_idx = int(start * sr)
        end_idx = int(end * sr)
        
        # Create a modulated sine wave to simulate speech
        segment_t = t[start_idx:end_idx]
        speech_signal = np.sin(2 * np.pi * freq * segment_t)
        
        # Add some amplitude modulation to make it more speech-like
        modulation = 0.5 + 0.5 * np.sin(2 * np.pi * 5 * segment_t)
        speech_signal *= modulation
        
        # Add some noise
        noise = 0.1 * np.random.randn(len(speech_signal))
        speech_signal += noise
        
        audio[start_idx:end_idx] = speech_signal
    
    # Add background noise to silence segments
    noise_level = 0.02
    audio += noise_level * np.random.randn(len(audio))
    
    # Normalize
    audio = audio / np.max(np.abs(audio)) * 0.8
    
    # Save demo audio
    demo_file = "demo_audio.wav"
    sf.write(demo_file, audio, sr)
    
    print(f"✅ Demo audio created: {demo_file}")
    print(f"   Duration: {duration}s")
    print(f"   Sample Rate: {sr} Hz")
    print(f"   Speech segments: {len(speech_segments)}")
    
    return demo_file

def demonstrate_vad_methods(audio_file):
    """Demonstrate different VAD methods"""
    print("\n" + "="*70)
    print("🎤 VOICE ACTIVITY DETECTION METHODS COMPARISON")
    print("="*70)
    
    vad = VoiceActivityDetector()
    
    methods_to_test = [
        VADMethod.WEBRTC,
        VADMethod.ENERGY_BASED,
        VADMethod.ENSEMBLE
    ]
    
    results = {}
    
    for method in methods_to_test:
        print(f"\n--- Testing {method.value.upper()} Method ---")
        
        start_time = time.time()
        result = vad.detect_voice_activity(audio_file, method)
        processing_time = time.time() - start_time
        
        results[method.value] = result
        
        print(f"✅ Processing completed in {processing_time:.3f}s")
        print(f"📊 Results:")
        print(f"   Total Duration: {result.total_duration:.2f}s")
        print(f"   Speech Duration: {result.speech_duration:.2f}s")
        print(f"   Silence Duration: {result.silence_duration:.2f}s")
        print(f"   Speech Ratio: {result.speech_ratio:.1%}")
        print(f"   Quality Score: {result.quality_score:.1f}/100")
        print(f"   Segments Detected: {len(result.segments)}")
        
        # Show segment details
        print(f"   Segment Breakdown:")
        speech_count = sum(1 for seg in result.segments if seg.is_speech)
        silence_count = len(result.segments) - speech_count
        print(f"     Speech segments: {speech_count}")
        print(f"     Silence segments: {silence_count}")
        
        if result.segments:
            avg_confidence = np.mean([seg.confidence for seg in result.segments])
            print(f"     Average confidence: {avg_confidence:.2f}")
    
    return results

def demonstrate_silence_removal(audio_file, vad_results):
    """Demonstrate silence removal functionality"""
    print("\n" + "="*70)
    print("🔇 SILENCE REMOVAL DEMONSTRATION")
    print("="*70)
    
    vad = VoiceActivityDetector()
    
    # Test different methods for silence removal
    methods_to_test = [VADMethod.ENSEMBLE, VADMethod.WEBRTC]
    
    for method in methods_to_test:
        print(f"\n--- Silence Removal with {method.value.upper()} ---")
        
        output_file = f"processed_{method.value}.wav"
        
        start_time = time.time()
        processed_file = vad.remove_silence(audio_file, output_file, method, padding_ms=100)
        processing_time = time.time() - start_time
        
        if os.path.exists(processed_file):
            # Get file sizes and durations
            original_audio, sr = librosa.load(audio_file, sr=None)
            processed_audio, _ = librosa.load(processed_file, sr=None)
            
            original_duration = len(original_audio) / sr
            processed_duration = len(processed_audio) / sr
            
            compression_ratio = processed_duration / original_duration
            
            print(f"✅ Silence removal completed in {processing_time:.3f}s")
            print(f"📊 Results:")
            print(f"   Original Duration: {original_duration:.2f}s")
            print(f"   Processed Duration: {processed_duration:.2f}s")
            print(f"   Time Saved: {original_duration - processed_duration:.2f}s")
            print(f"   Compression Ratio: {compression_ratio:.1%}")
            print(f"   Output File: {processed_file}")
        else:
            print(f"❌ Silence removal failed")

def demonstrate_audio_quality_assessment(audio_file):
    """Demonstrate audio quality assessment"""
    print("\n" + "="*70)
    print("🔊 AUDIO QUALITY ASSESSMENT")
    print("="*70)
    
    vad = VoiceActivityDetector()
    
    # Load audio
    audio, sr = librosa.load(audio_file, sr=None)
    
    # Assess quality
    quality_metrics = vad.assess_audio_quality(audio, sr)
    
    print(f"📊 Quality Metrics for {os.path.basename(audio_file)}:")
    print(f"   Signal-to-Noise Ratio: {quality_metrics.snr_db:.1f} dB")
    print(f"   Total Harmonic Distortion: {quality_metrics.thd_percent:.2f}%")
    print(f"   Dynamic Range: {quality_metrics.dynamic_range_db:.1f} dB")
    print(f"   Spectral Centroid: {quality_metrics.spectral_centroid_hz:.0f} Hz")
    print(f"   Spectral Rolloff: {quality_metrics.spectral_rolloff_hz:.0f} Hz")
    print(f"   Zero Crossing Rate: {quality_metrics.zero_crossing_rate:.4f}")
    print(f"   Energy Entropy: {quality_metrics.energy_entropy:.2f}")
    print(f"   Spectral Entropy: {quality_metrics.spectral_entropy:.2f}")
    
    # MFCC features summary
    if quality_metrics.mfcc_features:
        mfcc_mean = np.mean(quality_metrics.mfcc_features)
        mfcc_std = np.std(quality_metrics.mfcc_features)
        print(f"   MFCC Features (13 coefficients):")
        print(f"     Mean: {mfcc_mean:.3f}")
        print(f"     Std Dev: {mfcc_std:.3f}")
    
    # Quality assessment
    print(f"\n🎯 Quality Assessment:")
    
    if quality_metrics.snr_db > 20:
        print("   ✅ Excellent signal quality (SNR > 20 dB)")
    elif quality_metrics.snr_db > 10:
        print("   ⚠️  Good signal quality (SNR 10-20 dB)")
    else:
        print("   ❌ Poor signal quality (SNR < 10 dB)")
    
    if quality_metrics.dynamic_range_db > 40:
        print("   ✅ Good dynamic range")
    else:
        print("   ⚠️  Limited dynamic range")
    
    if quality_metrics.spectral_centroid_hz > 1000:
        print("   ✅ Good spectral content for speech")
    else:
        print("   ⚠️  Low spectral content")

def demonstrate_visualization(audio_file, vad_result):
    """Create and save VAD visualization"""
    print("\n" + "="*70)
    print("📊 VAD VISUALIZATION")
    print("="*70)
    
    try:
        vad = VoiceActivityDetector()
        
        # Create visualization
        output_file = "vad_visualization_demo.png"
        result_file = vad.visualize_vad_result(audio_file, vad_result, output_file)
        
        if result_file and os.path.exists(result_file):
            print(f"✅ VAD visualization saved to: {result_file}")
            print("   The visualization includes:")
            print("     • Audio waveform with VAD overlay")
            print("     • Spectrogram with speech/silence regions")
            print("     • Confidence scores over time")
        else:
            print("❌ Visualization creation failed")
            
    except Exception as e:
        print(f"❌ Visualization error: {e}")

def demonstrate_system_statistics():
    """Demonstrate system statistics and performance"""
    print("\n" + "="*70)
    print("📈 SYSTEM STATISTICS")
    print("="*70)
    
    vad = VoiceActivityDetector()
    
    # Get statistics
    stats = vad.get_vad_statistics()
    
    if stats:
        print("📊 Processing Statistics:")
        
        if stats.get('method_statistics'):
            print("\n   Method Performance:")
            for stat in stats['method_statistics']:
                method = stat[4]
                files_count = stat[0]
                avg_speech_ratio = stat[1]
                avg_quality = stat[2]
                avg_time = stat[3]
                
                print(f"     {method.upper()}:")
                print(f"       Files processed: {files_count}")
                if avg_speech_ratio:
                    print(f"       Avg speech ratio: {avg_speech_ratio:.1%}")
                if avg_quality:
                    print(f"       Avg quality score: {avg_quality:.1f}")
                if avg_time:
                    print(f"       Avg processing time: {avg_time:.3f}s")
        
        total_files = stats.get('total_processed_files', 0)
        print(f"\n   Total files processed: {total_files}")
        
        if stats.get('recent_activity'):
            print(f"\n   Recent activity: {len(stats['recent_activity'])} files")
    else:
        print("📊 No statistics available yet")

def demonstrate_batch_processing():
    """Demonstrate batch processing capabilities"""
    print("\n" + "="*70)
    print("⚡ BATCH PROCESSING DEMONSTRATION")
    print("="*70)
    
    # Create multiple demo files
    demo_files = []
    
    print("🎵 Creating multiple demo audio files...")
    
    for i in range(3):
        # Create different types of audio
        sr = 16000
        duration = 5
        t = np.linspace(0, duration, int(sr * duration))
        
        if i == 0:
            # High speech ratio
            audio = 0.5 * np.sin(2 * np.pi * 440 * t) * (1 + 0.3 * np.sin(2 * np.pi * 2 * t))
            audio += 0.05 * np.random.randn(len(audio))
            filename = f"demo_high_speech_{i}.wav"
        elif i == 1:
            # Medium speech ratio
            speech_mask = (t % 2) < 1  # 50% speech
            audio = np.zeros_like(t)
            audio[speech_mask] = 0.5 * np.sin(2 * np.pi * 523 * t[speech_mask])
            audio += 0.05 * np.random.randn(len(audio))
            filename = f"demo_medium_speech_{i}.wav"
        else:
            # Low speech ratio
            speech_mask = (t % 3) < 0.5  # ~17% speech
            audio = np.zeros_like(t)
            audio[speech_mask] = 0.5 * np.sin(2 * np.pi * 659 * t[speech_mask])
            audio += 0.1 * np.random.randn(len(audio))  # More noise
            filename = f"demo_low_speech_{i}.wav"
        
        # Normalize and save
        audio = audio / np.max(np.abs(audio)) * 0.8
        sf.write(filename, audio, sr)
        demo_files.append(filename)
    
    print(f"✅ Created {len(demo_files)} demo files")
    
    # Process all files
    vad = VoiceActivityDetector()
    results = []
    
    print("\n🚀 Processing files in batch...")
    
    total_start_time = time.time()
    
    for i, file in enumerate(demo_files):
        print(f"\n   Processing file {i+1}/{len(demo_files)}: {file}")
        
        start_time = time.time()
        result = vad.detect_voice_activity(file, VADMethod.ENSEMBLE)
        processing_time = time.time() - start_time
        
        results.append(result)
        
        print(f"     ✅ Completed in {processing_time:.3f}s")
        print(f"     Speech ratio: {result.speech_ratio:.1%}")
        print(f"     Quality score: {result.quality_score:.1f}")
    
    total_processing_time = time.time() - total_start_time
    
    # Summary
    print(f"\n📊 Batch Processing Summary:")
    print(f"   Total files: {len(demo_files)}")
    print(f"   Total processing time: {total_processing_time:.3f}s")
    print(f"   Average time per file: {total_processing_time/len(demo_files):.3f}s")
    
    avg_speech_ratio = np.mean([r.speech_ratio for r in results])
    avg_quality = np.mean([r.quality_score for r in results])
    
    print(f"   Average speech ratio: {avg_speech_ratio:.1%}")
    print(f"   Average quality score: {avg_quality:.1f}")
    
    # Clean up demo files
    for file in demo_files:
        try:
            os.remove(file)
        except:
            pass

def main():
    """Main demo function"""
    print("🎤 VOICE ACTIVITY DETECTION (VAD) SYSTEM DEMO")
    print("=" * 70)
    print("This demo showcases comprehensive voice activity detection capabilities")
    print("including multiple VAD methods, silence removal, and audio quality assessment.")
    print("=" * 70)
    
    try:
        # Create demo audio
        demo_audio_file = create_demo_audio()
        
        # Demonstrate VAD methods
        vad_results = demonstrate_vad_methods(demo_audio_file)
        
        # Demonstrate silence removal
        demonstrate_silence_removal(demo_audio_file, vad_results)
        
        # Demonstrate audio quality assessment
        demonstrate_audio_quality_assessment(demo_audio_file)
        
        # Demonstrate visualization
        if vad_results:
            best_result = list(vad_results.values())[0]  # Use first result
            demonstrate_visualization(demo_audio_file, best_result)
        
        # Demonstrate system statistics
        demonstrate_system_statistics()
        
        # Demonstrate batch processing
        demonstrate_batch_processing()
        
        print("\n" + "="*70)
        print("🎉 VAD SYSTEM DEMO COMPLETED SUCCESSFULLY!")
        print("="*70)
        print("Key Features Demonstrated:")
        print("✅ Multiple VAD algorithms (WebRTC, Energy-based, Ensemble)")
        print("✅ Silence detection and removal")
        print("✅ Audio quality assessment")
        print("✅ Comprehensive visualization")
        print("✅ Performance statistics")
        print("✅ Batch processing capabilities")
        print("✅ Database storage and retrieval")
        
        print(f"\nGenerated Files:")
        if os.path.exists(demo_audio_file):
            print(f"• {demo_audio_file} - Demo audio file")
        
        processed_files = [f for f in os.listdir('.') if f.startswith('processed_')]
        for pf in processed_files:
            print(f"• {pf} - Processed audio (silence removed)")
        
        if os.path.exists("vad_visualization_demo.png"):
            print(f"• vad_visualization_demo.png - VAD visualization")
        
        if os.path.exists("vad_system.db"):
            print(f"• vad_system.db - VAD results database")
        
        print(f"\n💡 Next Steps:")
        print("• Run 'streamlit run voice_activity_detection_ui.py' for the web interface")
        print("• Upload your own audio files for processing")
        print("• Experiment with different VAD methods")
        print("• Use the silence removal feature to optimize audio files")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up demo files
        cleanup_files = ["demo_audio.wav"]
        for file in cleanup_files:
            try:
                if os.path.exists(file):
                    os.remove(file)
                    print(f"🧹 Cleaned up: {file}")
            except:
                pass
        
        print("\n🧹 Demo cleanup completed")

if __name__ == "__main__":
    main()