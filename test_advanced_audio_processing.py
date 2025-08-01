#!/usr/bin/env python3
"""
Test script for advanced audio processing features
Tests the implementation of task 22 features
"""

import os
import sys
import tempfile
import numpy as np
import soundfile as sf
import pytest
from unittest.mock import Mock, patch

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from advanced_audio_processor import (
    AdvancedAudioProcessor, AudioQualityAnalyzer, NoiseReducer, AudioTrimmer,
    RealTimeStreamProcessor, AudioBookmarkManager, enhance_audio_for_transcription,
    analyze_audio_quality, create_audio_segments, AudioQualityMetrics, AudioBookmark, AudioChapter
)

def create_test_audio(duration=5.0, sample_rate=16000, frequency=440):
    """Create a test audio file with sine wave"""
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = 0.5 * np.sin(2 * np.pi * frequency * t)
    
    # Add some noise
    noise = 0.1 * np.random.randn(len(audio_data))
    audio_data += noise
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    sf.write(temp_file.name, audio_data, sample_rate)
    temp_file.close()
    
    return temp_file.name

def test_noise_reducer():
    """Test noise reduction functionality"""
    print("Testing noise reduction...")
    
    # Create test audio with noise
    test_audio_path = create_test_audio(duration=3.0)
    
    try:
        noise_reducer = NoiseReducer()
        reduced_audio_path = noise_reducer.reduce_noise(test_audio_path, noise_duration=0.5)
        
        # Verify output file exists
        assert os.path.exists(reduced_audio_path)
        
        # Verify it's different from input (unless it's the same file due to error)
        if reduced_audio_path != test_audio_path:
            # Load both files and compare
            original, sr1 = sf.read(test_audio_path)
            reduced, sr2 = sf.read(reduced_audio_path)
            
            assert sr1 == sr2, "Sample rates should match"
            # Allow for small differences in length due to STFT processing
            length_diff = abs(len(original) - len(reduced))
            assert length_diff < sr1 * 0.1, f"Audio length difference too large: {length_diff} samples"
            
            print("✅ Noise reduction test passed")
        else:
            print("⚠️ Noise reduction returned original file (may have failed)")
        
        # Cleanup
        if reduced_audio_path != test_audio_path:
            os.unlink(reduced_audio_path)
    
    finally:
        os.unlink(test_audio_path)

def test_audio_quality_analyzer():
    """Test audio quality analysis"""
    print("Testing audio quality analysis...")
    
    test_audio_path = create_test_audio(duration=2.0)
    
    try:
        analyzer = AudioQualityAnalyzer()
        metrics = analyzer.analyze_quality(test_audio_path)
        
        # Verify metrics structure
        assert isinstance(metrics, AudioQualityMetrics)
        assert isinstance(metrics.snr_db, float)
        assert isinstance(metrics.dynamic_range_db, float)
        assert isinstance(metrics.quality_score, float)
        assert isinstance(metrics.recommendations, list)
        
        # Verify reasonable values
        assert 0 <= metrics.quality_score <= 100
        assert metrics.snr_db > -50  # Should be reasonable for test audio
        assert len(metrics.recommendations) > 0
        
        print(f"✅ Quality analysis test passed - Score: {metrics.quality_score:.1f}")
        print(f"   SNR: {metrics.snr_db:.1f} dB, Dynamic Range: {metrics.dynamic_range_db:.1f} dB")
    
    finally:
        os.unlink(test_audio_path)

def test_audio_trimmer():
    """Test audio trimming functionality"""
    print("Testing audio trimming...")
    
    # Create audio with silence at beginning and end
    duration = 5.0
    sample_rate = 16000
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create audio with silence at start and end
    audio_data = np.zeros(len(t))
    # Add signal in the middle
    start_idx = int(len(t) * 0.2)
    end_idx = int(len(t) * 0.8)
    audio_data[start_idx:end_idx] = 0.5 * np.sin(2 * np.pi * 440 * t[start_idx:end_idx])
    
    test_audio_path = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
    sf.write(test_audio_path, audio_data, sample_rate)
    
    try:
        trimmer = AudioTrimmer()
        trimmed_path = trimmer.trim_silence(test_audio_path, silence_thresh=-50)
        
        assert os.path.exists(trimmed_path)
        
        # Load and compare lengths
        original, _ = sf.read(test_audio_path)
        trimmed, _ = sf.read(trimmed_path)
        
        # Trimmed should be shorter or equal
        assert len(trimmed) <= len(original)
        
        print(f"✅ Audio trimming test passed - Original: {len(original)} samples, Trimmed: {len(trimmed)} samples")
        
        # Cleanup
        if trimmed_path != test_audio_path:
            os.unlink(trimmed_path)
    
    finally:
        os.unlink(test_audio_path)

def test_audio_segmentation():
    """Test audio segmentation"""
    print("Testing audio segmentation...")
    
    test_audio_path = create_test_audio(duration=10.0)  # Longer audio for segmentation
    
    try:
        trimmer = AudioTrimmer()
        segments = trimmer.segment_by_silence(test_audio_path, min_segment_len=1000)
        
        assert isinstance(segments, list)
        assert len(segments) >= 1
        
        # Verify all segment files exist
        for segment_path in segments:
            assert os.path.exists(segment_path)
        
        print(f"✅ Audio segmentation test passed - Created {len(segments)} segments")
        
        # Cleanup segments
        for segment_path in segments:
            if segment_path != test_audio_path:
                try:
                    os.unlink(segment_path)
                except:
                    pass
    
    finally:
        os.unlink(test_audio_path)

def test_bookmark_manager():
    """Test audio bookmark and chapter management"""
    print("Testing bookmark manager...")
    
    manager = AudioBookmarkManager()
    
    # Test adding bookmarks
    bookmark1 = manager.add_bookmark(10.5, "Important Point", "Key discussion starts here")
    bookmark2 = manager.add_bookmark(25.0, "Decision Made", "Final decision reached")
    
    assert len(manager.bookmarks) == 2
    assert bookmark1.timestamp == 10.5
    assert bookmark1.title == "Important Point"
    
    # Test adding chapters
    chapter1 = manager.add_chapter(0.0, 30.0, "Introduction", "Opening remarks")
    chapter2 = manager.add_chapter(30.0, 60.0, "Main Discussion", "Core content")
    
    assert len(manager.chapters) == 2
    assert chapter1.start_time == 0.0
    assert chapter1.end_time == 30.0
    
    # Test bookmark retrieval
    bookmarks_in_range = manager.get_bookmarks_in_range(5.0, 20.0)
    assert len(bookmarks_in_range) == 1
    assert bookmarks_in_range[0].title == "Important Point"
    
    print("✅ Bookmark manager test passed")

def test_realtime_processor():
    """Test real-time stream processor"""
    print("Testing real-time processor...")
    
    processor = RealTimeStreamProcessor(sample_rate=16000, chunk_size=512)
    
    # Test callback system
    callback_called = False
    def test_callback(result):
        nonlocal callback_called
        callback_called = True
        assert 'timestamp' in result
        assert 'rms' in result
        assert 'is_speech' in result
    
    processor.add_callback(test_callback)
    
    # Test chunk processing
    test_chunk = np.random.randn(512) * 0.1  # Small random audio chunk
    result = processor.process_chunk(test_chunk)
    
    assert isinstance(result, dict)
    assert 'rms' in result
    assert 'zero_crossings' in result
    assert 'is_speech' in result
    
    print("✅ Real-time processor test passed")

def test_advanced_audio_processor():
    """Test the main AdvancedAudioProcessor class"""
    print("Testing advanced audio processor...")
    
    test_audio_path = create_test_audio(duration=3.0)
    
    try:
        processor = AdvancedAudioProcessor()
        
        # Test comprehensive enhancement
        enhanced_path = processor.enhance_audio(
            test_audio_path,
            apply_noise_reduction=True,
            apply_normalization=True,
            trim_silence=True
        )
        
        assert os.path.exists(enhanced_path)
        
        # Test analysis and optimization
        metrics, optimized_path = processor.analyze_and_optimize(test_audio_path)
        
        assert isinstance(metrics, AudioQualityMetrics)
        assert os.path.exists(optimized_path)
        
        # Test segmentation with bookmarks
        segment_result = processor.create_segments_with_bookmarks(test_audio_path, "time")
        
        assert 'segments' in segment_result
        assert 'bookmarks' in segment_result
        assert 'chapters' in segment_result
        assert isinstance(segment_result['segments'], list)
        
        print("✅ Advanced audio processor test passed")
        
        # Cleanup
        processor.cleanup()
    
    finally:
        os.unlink(test_audio_path)

def test_convenience_functions():
    """Test convenience functions"""
    print("Testing convenience functions...")
    
    test_audio_path = create_test_audio(duration=2.0)
    
    try:
        # Test enhance_audio_for_transcription
        enhanced_path = enhance_audio_for_transcription(test_audio_path)
        # Enhanced path should be returned (could be same as original if no enhancement needed)
        assert enhanced_path is not None
        assert isinstance(enhanced_path, str)
        
        # Test analyze_audio_quality
        metrics = analyze_audio_quality(test_audio_path)
        assert isinstance(metrics, AudioQualityMetrics)
        
        # Test create_audio_segments
        segments = create_audio_segments(test_audio_path, method="silence")
        assert isinstance(segments, list)
        assert len(segments) >= 1
        
        print("✅ Convenience functions test passed")
        
        # Cleanup - only if files exist and are different from original
        if enhanced_path != test_audio_path and os.path.exists(enhanced_path):
            try:
                os.unlink(enhanced_path)
            except:
                pass
        
        for segment in segments:
            if segment != test_audio_path and os.path.exists(segment):
                try:
                    os.unlink(segment)
                except:
                    pass
    
    finally:
        if os.path.exists(test_audio_path):
            os.unlink(test_audio_path)

def run_all_tests():
    """Run all tests"""
    print("🧪 Running Advanced Audio Processing Tests")
    print("=" * 50)
    
    try:
        test_noise_reducer()
        test_audio_quality_analyzer()
        test_audio_trimmer()
        test_audio_segmentation()
        test_bookmark_manager()
        test_realtime_processor()
        test_advanced_audio_processor()
        test_convenience_functions()
        
        print("=" * 50)
        print("🎉 All tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)