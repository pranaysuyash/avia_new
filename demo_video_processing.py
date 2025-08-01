#!/usr/bin/env python3
"""
Demo script for video processing functionality
"""

import os
import sys
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from video_processing import VideoProcessor
from test_video_processing import create_test_video


def demo_video_processing():
    """Demonstrate video processing capabilities"""
    print("🎬 Video Processing Demo")
    print("=" * 50)
    
    processor = VideoProcessor()
    test_video_path = None
    
    try:
        # Create test video
        print("\n1. Creating test video...")
        test_video_path = create_test_video(duration_seconds=5, fps=15)
        print(f"✅ Test video created: {test_video_path}")
        
        # Analyze video
        print("\n2. Analyzing video...")
        analysis = processor.analyze_video(
            test_video_path,
            extract_frames=True,
            detect_scenes=True,
            keyframe_interval=2.0
        )
        
        print("✅ Video analysis completed!")
        print(f"   📊 Basic Info:")
        print(f"      - Duration: {analysis.duration:.2f} seconds")
        print(f"      - Resolution: {analysis.width}x{analysis.height}")
        print(f"      - FPS: {analysis.fps:.2f}")
        print(f"      - Total frames: {analysis.total_frames}")
        
        print(f"   🎯 Content Analysis:")
        print(f"      - Scenes detected: {len(analysis.scenes)}")
        print(f"      - Keyframes extracted: {len(analysis.keyframes)}")
        
        # Show scene breakdown
        if analysis.scenes:
            print(f"   🎬 Scene Breakdown:")
            for i, scene in enumerate(analysis.scenes):
                print(f"      Scene {i+1}: {scene.start_time:.1f}s - {scene.end_time:.1f}s ({scene.duration:.1f}s)")
        
        # Create thumbnail
        print("\n3. Creating thumbnail...")
        thumbnail_path = processor.create_video_thumbnail(test_video_path, timestamp=2.5)
        print(f"✅ Thumbnail created: {thumbnail_path}")
        
        # Extract specific frames
        print("\n4. Extracting specific frames...")
        timestamps = [1.0, 2.5, 4.0]
        frames = processor.extract_frames_at_timestamps(test_video_path, timestamps)
        print(f"✅ Extracted {len(frames)} frames at specific timestamps")
        
        for frame in frames:
            print(f"   Frame at {frame.timestamp:.1f}s: {frame.width}x{frame.height}, brightness={frame.brightness:.1f}")
        
        # Generate summary
        print("\n5. Generating video summary...")
        summary = processor.get_video_summary(analysis)
        print("✅ Video summary:")
        
        basic_info = summary['basic_info']
        print(f"   📊 Basic: {basic_info['duration']}, {basic_info['resolution']}, {basic_info['fps']} FPS")
        
        content_analysis = summary['content_analysis']
        print(f"   🎯 Content: {content_analysis['scene_count']} scenes, {content_analysis['keyframe_count']} keyframes")
        
        technical = summary['technical_details']
        print(f"   🔧 Technical: {technical.get('video_codec', 'unknown')} codec, {technical.get('file_size', 0)} bytes")
        
        print("\n✅ Video processing demo completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        if test_video_path and os.path.exists(test_video_path):
            os.unlink(test_video_path)
            print("🧹 Cleaned up test video")


if __name__ == "__main__":
    demo_video_processing()