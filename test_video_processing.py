#!/usr/bin/env python3
"""
Test video processing functionality
"""

import os
import sys
import tempfile
import cv2
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from video_processing import VideoProcessor, VideoFrame, SceneSegment, VideoAnalysis


def create_test_video(duration_seconds: int = 5, fps: int = 30) -> str:
    """Create a simple test video file"""
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
        video_path = tmp.name
    
    # Define codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, fps, (640, 480))
    
    total_frames = duration_seconds * fps
    
    for i in range(total_frames):
        # Create a frame with changing colors to simulate scene changes
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Change colors every second to create scene changes
        scene_phase = (i // fps) % 3
        if scene_phase == 0:
            frame[:, :] = [100, 50, 200]  # Purple-ish
        elif scene_phase == 1:
            frame[:, :] = [50, 200, 100]  # Green-ish
        else:
            frame[:, :] = [200, 100, 50]  # Orange-ish
        
        # Add some text to make frames distinguishable
        cv2.putText(frame, f"Frame {i}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        out.write(frame)
    
    out.release()
    return video_path


def test_video_processor():
    """Test video processing functionality"""
    print("🎬 Testing Video Processing")
    print("=" * 50)
    
    processor = VideoProcessor()
    test_video_path = None
    
    try:
        # Create test video
        print("\n1️⃣ Creating test video...")
        test_video_path = create_test_video(duration_seconds=3, fps=10)
        print(f"✅ Test video created: {test_video_path}")
        
        # Test video analysis
        print("\n2️⃣ Testing video analysis...")
        analysis = processor.analyze_video(
            test_video_path,
            extract_frames=True,
            detect_scenes=True,
            keyframe_interval=1.0
        )
        
        print(f"✅ Analysis completed:")
        print(f"   - Duration: {analysis.duration:.2f} seconds")
        print(f"   - Resolution: {analysis.width}x{analysis.height}")
        print(f"   - FPS: {analysis.fps:.2f}")
        print(f"   - Total frames: {analysis.total_frames}")
        print(f"   - Keyframes extracted: {len(analysis.keyframes)}")
        print(f"   - Scenes detected: {len(analysis.scenes)}")
        
        # Test keyframe extraction at specific timestamps
        print("\n3️⃣ Testing keyframe extraction...")
        timestamps = [0.5, 1.5, 2.5]
        frames = processor.extract_frames_at_timestamps(test_video_path, timestamps)
        print(f"✅ Extracted {len(frames)} frames at specific timestamps")
        
        # Test thumbnail creation
        print("\n4️⃣ Testing thumbnail creation...")
        thumbnail_path = processor.create_video_thumbnail(test_video_path)
        print(f"✅ Thumbnail created: {thumbnail_path}")
        
        # Test video summary
        print("\n5️⃣ Testing video summary...")
        summary = processor.get_video_summary(analysis)
        print("✅ Video summary generated:")
        print(f"   - Scene count: {summary['content_analysis']['scene_count']}")
        print(f"   - Keyframe count: {summary['content_analysis']['keyframe_count']}")
        
        # Test data structures
        print("\n6️⃣ Testing data structures...")
        
        # Test VideoFrame
        if analysis.keyframes:
            frame_dict = analysis.keyframes[0].to_dict()
            print(f"✅ VideoFrame serialization: {len(frame_dict)} fields")
        
        # Test SceneSegment
        if analysis.scenes:
            scene_dict = analysis.scenes[0].to_dict()
            print(f"✅ SceneSegment serialization: {len(scene_dict)} fields")
        
        # Test VideoAnalysis
        analysis_dict = analysis.to_dict()
        print(f"✅ VideoAnalysis serialization: {len(analysis_dict)} fields")
        
        print("\n✅ All video processing tests passed!")
        
    except Exception as e:
        print(f"\n❌ Video processing test failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        if test_video_path and os.path.exists(test_video_path):
            os.unlink(test_video_path)
            print(f"🧹 Cleaned up test video")


def test_video_formats():
    """Test different video format support"""
    print("\n🎞️ Testing Video Format Support")
    print("=" * 30)
    
    from media import SUPPORTED_VIDEO_FORMATS, is_video_file
    
    print(f"Supported video formats: {', '.join(SUPPORTED_VIDEO_FORMATS)}")
    
    # Test format detection
    test_files = [
        "test.mp4",
        "test.avi", 
        "test.mov",
        "test.mkv",
        "test.webm",
        "test.mp3",  # Not a video
        "test.txt"   # Not a video
    ]
    
    for file_path in test_files:
        is_video = is_video_file(file_path)
        expected = Path(file_path).suffix.lower() in SUPPORTED_VIDEO_FORMATS
        status = "✅" if is_video == expected else "❌"
        print(f"{status} {file_path}: {is_video}")


if __name__ == "__main__":
    from pathlib import Path
    
    print("🧪 Video Processing Test Suite")
    print("=" * 50)
    
    # Check OpenCV availability
    try:
        print(f"OpenCV version: {cv2.__version__}")
    except:
        print("❌ OpenCV not available")
        sys.exit(1)
    
    # Run tests
    test_video_processor()
    test_video_formats()
    
    print("\n🎉 Video processing tests completed!")