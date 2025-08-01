#!/usr/bin/env python3
"""
Demo script for advanced audio processing features
Demonstrates the implementation of task 22 features
"""

import os
import sys
import tempfile
import numpy as np
import soundfile as sf

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from advanced_audio_processor import (
    AdvancedAudioProcessor, enhance_audio_for_transcription,
    analyze_audio_quality, create_audio_segments
)

def create_demo_audio():
    """Create a demo audio file with speech-like characteristics"""
    print("🎵 Creating demo audio file...")
    
    duration = 10.0  # 10 seconds
    sample_rate = 16000
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create a more complex audio signal that simulates speech
    # Multiple frequency components
    signal = (
        0.3 * np.sin(2 * np.pi * 200 * t) +  # Low frequency component
        0.4 * np.sin(2 * np.pi * 800 * t) +  # Mid frequency component
        0.2 * np.sin(2 * np.pi * 1600 * t)   # High frequency component
    )
    
    # Add some amplitude modulation to simulate speech patterns
    envelope = 0.5 + 0.5 * np.sin(2 * np.pi * 2 * t)  # 2 Hz modulation
    signal *= envelope
    
    # Add noise
    noise = 0.15 * np.random.randn(len(signal))
    noisy_signal = signal + noise
    
    # Add some silence at the beginning and end
    silence_samples = int(0.5 * sample_rate)  # 0.5 seconds of silence
    final_signal = np.concatenate([
        np.zeros(silence_samples),
        noisy_signal,
        np.zeros(silence_samples)
    ])
    
    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    sf.write(temp_file.name, final_signal, sample_rate)
    temp_file.close()
    
    print(f"✅ Demo audio created: {temp_file.name}")
    print(f"   Duration: {len(final_signal) / sample_rate:.1f} seconds")
    print(f"   Sample rate: {sample_rate} Hz")
    
    return temp_file.name

def demo_audio_quality_analysis(audio_path):
    """Demonstrate audio quality analysis"""
    print("\n🔍 Audio Quality Analysis")
    print("=" * 40)
    
    metrics = analyze_audio_quality(audio_path)
    
    print(f"Overall Quality Score: {metrics.quality_score:.1f}/100")
    print(f"Signal-to-Noise Ratio: {metrics.snr_db:.1f} dB")
    print(f"Dynamic Range: {metrics.dynamic_range_db:.1f} dB")
    print(f"Spectral Centroid: {metrics.spectral_centroid:.0f} Hz")
    print(f"Zero Crossing Rate: {metrics.zero_crossing_rate:.4f}")
    print(f"RMS Energy: {metrics.rms_energy:.4f}")
    
    print("\n💡 Recommendations:")
    for i, rec in enumerate(metrics.recommendations, 1):
        print(f"   {i}. {rec}")
    
    return metrics

def demo_noise_reduction(audio_path):
    """Demonstrate noise reduction"""
    print("\n🔇 Noise Reduction")
    print("=" * 40)
    
    processor = AdvancedAudioProcessor()
    
    # Apply noise reduction
    print("Applying spectral subtraction noise reduction...")
    reduced_path = processor.noise_reducer.reduce_noise(audio_path)
    
    if reduced_path != audio_path:
        print(f"✅ Noise reduction applied: {reduced_path}")
        
        # Compare file sizes (just for demo)
        original_size = os.path.getsize(audio_path)
        reduced_size = os.path.getsize(reduced_path)
        print(f"   Original size: {original_size:,} bytes")
        print(f"   Processed size: {reduced_size:,} bytes")
        
        return reduced_path
    else:
        print("⚠️ Noise reduction returned original file")
        return audio_path

def demo_audio_enhancement(audio_path):
    """Demonstrate comprehensive audio enhancement"""
    print("\n🎛️ Audio Enhancement")
    print("=" * 40)
    
    print("Applying comprehensive audio enhancement...")
    enhanced_path = enhance_audio_for_transcription(
        audio_path,
        apply_noise_reduction=True,
        apply_normalization=True,
        trim_silence=True
    )
    
    if enhanced_path != audio_path and os.path.exists(enhanced_path):
        print(f"✅ Audio enhanced: {enhanced_path}")
        
        try:
            # Load and compare audio
            original, sr1 = sf.read(audio_path)
            enhanced, sr2 = sf.read(enhanced_path)
            
            print(f"   Original length: {len(original)} samples ({len(original)/sr1:.1f}s)")
            print(f"   Enhanced length: {len(enhanced)} samples ({len(enhanced)/sr2:.1f}s)")
            print(f"   Length change: {len(enhanced) - len(original)} samples")
        except Exception as e:
            print(f"   ⚠️ Could not compare files: {e}")
        
        return enhanced_path
    else:
        print("⚠️ Enhancement returned original file or file was cleaned up")
        return audio_path

def demo_audio_segmentation(audio_path):
    """Demonstrate audio segmentation"""
    print("\n📑 Audio Segmentation")
    print("=" * 40)
    
    processor = AdvancedAudioProcessor()
    
    # Create segments with bookmarks
    print("Creating audio segments with automatic bookmarks...")
    result = processor.create_segments_with_bookmarks(audio_path, "silence")
    
    segments = result['segments']
    bookmarks = result['bookmarks']
    chapters = result['chapters']
    
    print(f"✅ Segmentation complete:")
    print(f"   Total segments: {len(segments)}")
    print(f"   Bookmarks created: {len(bookmarks)}")
    print(f"   Auto chapters: {len(chapters)}")
    
    # Show segment details
    if len(segments) > 1:
        print("\n📊 Segment Details:")
        for i, segment_path in enumerate(segments):
            if os.path.exists(segment_path):
                segment_audio, sr = sf.read(segment_path)
                duration = len(segment_audio) / sr
                print(f"   Segment {i+1}: {duration:.1f}s")
    
    # Show bookmarks
    if bookmarks:
        print("\n🔖 Bookmarks:")
        for bookmark in bookmarks:
            print(f"   {bookmark.title} at {bookmark.timestamp:.1f}s")
    
    # Show chapters
    if chapters:
        print("\n📖 Chapters:")
        for chapter in chapters:
            print(f"   {chapter.title}: {chapter.start_time:.1f}s - {chapter.end_time:.1f}s")
    
    return result

def demo_bookmark_management():
    """Demonstrate bookmark and chapter management"""
    print("\n🔖 Bookmark Management")
    print("=" * 40)
    
    from advanced_audio_processor import AudioBookmarkManager
    
    manager = AudioBookmarkManager()
    
    # Add some demo bookmarks
    print("Adding demo bookmarks...")
    manager.add_bookmark(5.2, "Introduction", "Speaker introduces the topic")
    manager.add_bookmark(15.7, "Key Point", "Important information shared")
    manager.add_bookmark(28.3, "Question", "Audience question asked")
    manager.add_bookmark(35.1, "Conclusion", "Summary and wrap-up")
    
    # Add demo chapters
    print("Adding demo chapters...")
    manager.add_chapter(0.0, 10.0, "Opening", "Introduction and agenda")
    manager.add_chapter(10.0, 30.0, "Main Content", "Core discussion")
    manager.add_chapter(30.0, 40.0, "Q&A", "Questions and answers")
    
    print(f"✅ Bookmark management demo complete:")
    print(f"   Total bookmarks: {len(manager.bookmarks)}")
    print(f"   Total chapters: {len(manager.chapters)}")
    
    # Show bookmarks in a time range
    bookmarks_in_range = manager.get_bookmarks_in_range(10.0, 30.0)
    print(f"   Bookmarks in 10-30s range: {len(bookmarks_in_range)}")
    
    return manager

def demo_realtime_processing():
    """Demonstrate real-time processing capabilities"""
    print("\n🎤 Real-time Processing")
    print("=" * 40)
    
    from advanced_audio_processor import RealTimeStreamProcessor
    
    processor = RealTimeStreamProcessor(sample_rate=16000, chunk_size=512)
    
    # Add a demo callback
    results = []
    def demo_callback(result):
        results.append(result)
        if len(results) <= 3:  # Only show first few results
            print(f"   Chunk processed: RMS={result['rms']:.4f}, Speech={result['is_speech']}")
    
    processor.add_callback(demo_callback)
    
    print("Simulating real-time processing...")
    
    # Process a few demo chunks
    for i in range(5):
        # Create a demo audio chunk
        chunk = np.random.randn(512) * 0.1
        if i % 2 == 0:  # Make some chunks "speech-like"
            chunk += 0.2 * np.sin(2 * np.pi * 440 * np.linspace(0, 0.032, 512))
        
        result = processor.process_chunk(chunk)
    
    print(f"✅ Real-time processing demo complete:")
    print(f"   Processed {len(results)} chunks")
    print(f"   Speech detected in {sum(1 for r in results if r['is_speech'])} chunks")

def main():
    """Run the complete demo"""
    print("🎵 Advanced Audio Processing Demo")
    print("=" * 50)
    print("This demo showcases the advanced audio processing features")
    print("implemented for task 22:")
    print("• Noise reduction and audio enhancement")
    print("• Audio quality analysis and optimization")
    print("• Audio trimming and segmentation")
    print("• Real-time streaming support")
    print("• Audio bookmark and chapter creation")
    print("=" * 50)
    
    # Create demo audio
    demo_audio_path = create_demo_audio()
    
    try:
        # Run all demos
        quality_metrics = demo_audio_quality_analysis(demo_audio_path)
        reduced_path = demo_noise_reduction(demo_audio_path)
        enhanced_path = demo_audio_enhancement(demo_audio_path)
        segmentation_result = demo_audio_segmentation(demo_audio_path)
        bookmark_manager = demo_bookmark_management()
        demo_realtime_processing()
        
        print("\n🎉 Demo Complete!")
        print("=" * 50)
        print("All advanced audio processing features demonstrated successfully!")
        print("\nFeatures implemented:")
        print("✅ Noise reduction using spectral subtraction")
        print("✅ Audio quality analysis with recommendations")
        print("✅ Smart audio trimming and normalization")
        print("✅ Automatic audio segmentation")
        print("✅ Bookmark and chapter management")
        print("✅ Real-time processing framework")
        print("\nThese features enhance transcription accuracy and provide")
        print("better user experience for audio/video processing.")
        
    finally:
        # Cleanup demo files
        cleanup_files = [demo_audio_path]
        
        # Add processed files if they exist and are different
        if 'reduced_path' in locals() and reduced_path != demo_audio_path:
            cleanup_files.append(reduced_path)
        if 'enhanced_path' in locals() and enhanced_path != demo_audio_path:
            cleanup_files.append(enhanced_path)
        
        # Add segment files
        if 'segmentation_result' in locals():
            for segment in segmentation_result['segments']:
                if segment != demo_audio_path:
                    cleanup_files.append(segment)
        
        print(f"\n🧹 Cleaning up {len(cleanup_files)} temporary files...")
        for file_path in cleanup_files:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"   Warning: Could not cleanup {file_path}: {e}")

if __name__ == "__main__":
    main()