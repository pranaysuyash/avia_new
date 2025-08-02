"""Mock video processor for testing"""

import os
import tempfile
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class MockVideoFrame:
    timestamp: float
    frame_path: str
    width: int
    height: int

@dataclass 
class MockVideoScene:
    start_time: float
    end_time: float
    duration: float
    frame_count: int
    thumbnail_path: Optional[str] = None

@dataclass
class MockVideoAnalysis:
    duration: float
    fps: float
    frame_count: int
    width: int
    height: int
    keyframes: List[MockVideoFrame] = field(default_factory=list)
    scenes: List[MockVideoScene] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class VideoProcessor:
    """Mock video processor for testing"""
    
    def analyze_video(self, video_path: str, extract_frames: bool = True, 
                     detect_scenes: bool = True, keyframe_interval: float = 10.0) -> MockVideoAnalysis:
        """Mock video analysis"""
        
        # Create mock frames
        keyframes = []
        if extract_frames:
            for i in range(3):
                frame_path = os.path.join(tempfile.gettempdir(), f"frame_{i}.jpg")
                # Create empty file
                open(frame_path, 'a').close()
                keyframes.append(MockVideoFrame(
                    timestamp=i * keyframe_interval,
                    frame_path=frame_path,
                    width=1920,
                    height=1080
                ))
        
        # Create mock scenes
        scenes = []
        if detect_scenes:
            scenes = [
                MockVideoScene(0.0, 15.0, 15.0, 450, None),
                MockVideoScene(15.0, 30.0, 15.0, 450, None),
                MockVideoScene(30.0, 45.0, 15.0, 450, None)
            ]
        
        return MockVideoAnalysis(
            duration=45.0,
            fps=30.0,
            frame_count=1350,
            width=1920,
            height=1080,
            keyframes=keyframes,
            scenes=scenes,
            metadata={
                "codec": "h264",
                "bitrate": 5000000,
                "format": "mp4"
            }
        )
    
    def generate_thumbnails(self, video_path: str, count: int = 5) -> List[str]:
        """Generate mock thumbnails"""
        thumbnails = []
        for i in range(count):
            thumb_path = os.path.join(tempfile.gettempdir(), f"thumb_{i}.jpg")
            # Create empty file
            open(thumb_path, 'a').close()
            thumbnails.append(thumb_path)
        return thumbnails
    
    def extract_frames_at_interval(self, video_path: str, interval: float = 5.0,
                                  start_time: Optional[float] = None,
                                  end_time: Optional[float] = None) -> List[MockVideoFrame]:
        """Extract frames at interval"""
        frames = []
        current_time = start_time or 0.0
        max_time = end_time or 45.0
        
        while current_time < max_time:
            frame_path = os.path.join(tempfile.gettempdir(), f"interval_frame_{int(current_time)}.jpg")
            open(frame_path, 'a').close()
            frames.append(MockVideoFrame(
                timestamp=current_time,
                frame_path=frame_path,
                width=1920,
                height=1080
            ))
            current_time += interval
            
        return frames