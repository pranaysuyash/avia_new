#!/usr/bin/env python3
"""
Test Enhanced Audio Processing
Comprehensive test of all audio processing features
"""

import os
import sys
import logging
import tempfile
import numpy as np
from datetime import datetime
from pydub import AudioSegment
from pydub.generators import Sine

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from audio_processing_integration import AudioProcessingIntegration, enhance_audio_auto
from audio_processor import AudioProcessor
from advanced_audio_processor import (
    AdvancedAudioProcessor,
    analyze_audio_quality,
    enhance_audio_for_transcription,
    create_audio_segments
)

def create_test_audio(duration_seconds=10, include_noise=True, include_silence=True):
    """Create a test audio file with various characteristics"""
    logger.info("Creating test audio file...")
    
    # Create base tone (440Hz - A4 note)
    tone = Sine(440).to_audio_segment(duration=duration_seconds * 1000)
    
    # Adjust volume to simulate speech levels
    tone = tone - 10  # Reduce volume by 10dB
    
    if include_noise:
        # Add white noise
        noise_duration = duration_seconds * 1000
        noise = AudioSegment.silent(duration=noise_duration)
        
        # Generate white noise by overlaying random samples
        samples = np.random.normal(0, 0.01, int(44100 * duration_seconds))
        noise_segment = AudioSegment(
            samples.tobytes(),
            frame_rate=44100,
            sample_width=2,
            channels=1
        )
        noise_segment = noise_segment - 30  # Make noise quieter
        
        # Mix tone with noise
        tone = tone.overlay(noise_segment)
    
    if include_silence:
        # Add silence at beginning and end
        silence_start = AudioSegment.silent(duration=2000)  # 2 seconds
        silence_end = AudioSegment.silent(duration=1500)    # 1.5 seconds
        tone = silence_start + tone + silence_end
    
    # Save test audio
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tone.export(temp_file.name, format="wav")
    
    logger.info(f"Test audio created: {temp_file.name}")
    return temp_file.name

def test_basic_audio_processing():
    """Test basic audio processing features"""
    print("\n" + "="*60)
    print("Testing Basic Audio Processing")
    print("="*60)
    
    # Create test audio
    test_audio = create_test_audio(duration_seconds=5)
    
    try:
        processor = AudioProcessor()
        
        # Test volume normalization
        logger.info("Testing volume normalization...")
        normalized = processor.normalize_volume(test_audio, target_dBFS=-20.0)
        print(f"✅ Volume normalization: {os.path.basename(normalized)}")
        
        # Test dynamic range compression
        logger.info("Testing dynamic range compression...")
        compressed = processor.compress_dynamic_range(normalized)
        print(f"✅ Dynamic range compression: {os.path.basename(compressed)}")
        
        # Test segmentation
        logger.info("Testing audio segmentation...")
        segments = processor.segment_audio(test_audio, segment_length_ms=2000)
        print(f"✅ Audio segmentation: Created {len(segments)} segments")
        
        # Cleanup
        processor.cleanup()
        
        return True
        
    except Exception as e:
        logger.error(f"Basic audio processing test failed: {e}")
        return False
    finally:
        if os.path.exists(test_audio):
            os.unlink(test_audio)

def test_advanced_audio_processing():
    """Test advanced audio processing features"""
    print("\n" + "="*60)
    print("Testing Advanced Audio Processing")
    print("="*60)
    
    # Create test audio with noise
    test_audio = create_test_audio(duration_seconds=8, include_noise=True)
    
    try:
        processor = AdvancedAudioProcessor()
        
        # Test quality analysis
        logger.info("Testing audio quality analysis...")
        metrics = analyze_audio_quality(test_audio)
        print(f"✅ Quality analysis:")
        print(f"   - Quality score: {metrics.quality_score:.1f}/100")
        print(f"   - SNR: {metrics.snr_db:.1f} dB")
        print(f"   - Dynamic range: {metrics.dynamic_range_db:.1f} dB")
        print(f"   - Recommendations: {len(metrics.recommendations)}")
        
        # Test noise reduction
        logger.info("Testing noise reduction...")
        denoised = processor.noise_reducer.reduce_noise(test_audio)
        print(f"✅ Noise reduction: {os.path.basename(denoised)}")
        
        # Test silence trimming
        logger.info("Testing silence trimming...")
        trimmed = processor.trimmer.trim_silence(test_audio)
        print(f"✅ Silence trimming: {os.path.basename(trimmed)}")
        
        # Test comprehensive enhancement
        logger.info("Testing comprehensive enhancement...")
        enhanced = processor.enhance_audio(test_audio)
        print(f"✅ Comprehensive enhancement: {os.path.basename(enhanced)}")
        
        # Test auto-generated chapters
        logger.info("Testing chapter generation...")
        chapters = processor.bookmark_manager.auto_generate_chapters(test_audio, min_chapter_length=2.0)
        print(f"✅ Chapter generation: Created {len(chapters)} chapters")
        
        # Cleanup
        processor.cleanup()
        
        return True
        
    except Exception as e:
        logger.error(f"Advanced audio processing test failed: {e}")
        return False
    finally:
        if os.path.exists(test_audio):
            os.unlink(test_audio)

def test_audio_processing_integration():
    """Test integrated audio processing workflow"""
    print("\n" + "="*60)
    print("Testing Audio Processing Integration")
    print("="*60)
    
    # Create test audio
    test_audio = create_test_audio(duration_seconds=15, include_noise=True, include_silence=True)
    
    try:
        integration = AudioProcessingIntegration()
        
        # Test automatic enhancement
        logger.info("Testing automatic enhancement for transcription...")
        result = integration.enhance_for_transcription(test_audio)
        
        print(f"✅ Automatic enhancement:")
        print(f"   - Enhancements applied: {', '.join(result['enhancements_applied'])}")
        print(f"   - Processing time: {result['processing_time']:.2f}s")
        print(f"   - Enhanced path: {os.path.basename(result['enhanced_path'])}")
        
        if result.get('quality_metrics'):
            print(f"   - Original quality: {result['quality_metrics'].quality_score:.1f}/100")
        if result.get('quality_after'):
            print(f"   - Enhanced quality: {result['quality_after'].quality_score:.1f}/100")
        
        # Test use-case specific processing
        logger.info("Testing use-case specific processing...")
        use_cases = ['meeting', 'podcast', 'lecture', 'interview', 'dictation']
        
        for use_case in use_cases:
            result = integration.process_for_specific_use_case(test_audio, use_case)
            print(f"✅ {use_case.capitalize()} processing: {len(result['enhancements_applied'])} enhancements")
        
        # Test batch processing
        logger.info("Testing batch processing...")
        test_files = [test_audio] * 3  # Process same file 3 times for testing
        
        batch_results = integration.batch_process_audio_files(
            test_files,
            progress_callback=lambda p, m: logger.info(f"Batch progress: {p*100:.0f}% - {m}")
        )
        
        print(f"✅ Batch processing: Processed {len(batch_results)} files")
        
        # Cleanup
        integration.cleanup_temp_files()
        
        return True
        
    except Exception as e:
        logger.error(f"Audio processing integration test failed: {e}")
        return False
    finally:
        if os.path.exists(test_audio):
            os.unlink(test_audio)

def test_quality_improvement():
    """Test and demonstrate quality improvement"""
    print("\n" + "="*60)
    print("Testing Quality Improvement")
    print("="*60)
    
    # Create challenging test audio
    logger.info("Creating challenging test audio with noise and volume issues...")
    
    # Create quiet tone with heavy noise
    tone = Sine(440).to_audio_segment(duration=5000) - 30  # Very quiet
    noise = AudioSegment.silent(duration=5000)
    
    # Add significant noise
    samples = np.random.normal(0, 0.05, int(44100 * 5))
    noise_segment = AudioSegment(
        samples.tobytes(),
        frame_rate=44100,
        sample_width=2,
        channels=1
    )
    noise_segment = noise_segment - 20
    
    noisy_audio = tone.overlay(noise_segment)
    
    # Add long silence
    silence = AudioSegment.silent(duration=3000)
    test_audio = silence + noisy_audio + silence
    
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    test_audio.export(temp_file.name, format="wav")
    
    try:
        # Analyze before
        logger.info("Analyzing original audio quality...")
        metrics_before = analyze_audio_quality(temp_file.name)
        
        # Enhance
        logger.info("Applying comprehensive enhancements...")
        enhanced_path = enhance_audio_for_transcription(
            temp_file.name,
            apply_noise_reduction=True,
            apply_normalization=True,
            trim_silence=True
        )
        
        # Analyze after
        logger.info("Analyzing enhanced audio quality...")
        metrics_after = analyze_audio_quality(enhanced_path)
        
        # Show improvement
        print(f"\n🎯 Quality Improvement Results:")
        print(f"   Quality Score: {metrics_before.quality_score:.1f} → {metrics_after.quality_score:.1f} "
              f"(+{metrics_after.quality_score - metrics_before.quality_score:.1f})")
        print(f"   SNR: {metrics_before.snr_db:.1f} dB → {metrics_after.snr_db:.1f} dB "
              f"(+{metrics_after.snr_db - metrics_before.snr_db:.1f} dB)")
        print(f"   RMS Energy: {metrics_before.rms_energy:.3f} → {metrics_after.rms_energy:.3f}")
        
        print(f"\n📋 Recommendations before enhancement:")
        for rec in metrics_before.recommendations[:3]:
            print(f"   - {rec}")
        
        print(f"\n📋 Recommendations after enhancement:")
        for rec in metrics_after.recommendations[:3]:
            print(f"   - {rec}")
        
        return True
        
    except Exception as e:
        logger.error(f"Quality improvement test failed: {e}")
        return False
    finally:
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

def main():
    """Run all audio processing tests"""
    print("\n🎵 Enhanced Audio Processing Test Suite")
    print("=" * 60)
    
    tests = [
        ("Basic Audio Processing", test_basic_audio_processing),
        ("Advanced Audio Processing", test_advanced_audio_processing),
        ("Audio Processing Integration", test_audio_processing_integration),
        ("Quality Improvement", test_quality_improvement)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {test_name}: PASSED")
            else:
                print(f"\n❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"{test_name} crashed: {e}")
            print(f"\n❌ {test_name}: CRASHED")
    
    print("\n" + "="*60)
    print(f"Test Results: {passed}/{total} passed")
    print("="*60)
    
    if passed == total:
        print("\n🎉 All audio processing features working correctly!")
    else:
        print(f"\n⚠️  {total - passed} tests failed")

if __name__ == "__main__":
    main()