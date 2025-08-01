"""
Advanced Video Processing Module
Handles video-specific features like frame extraction, scene detection, 
metadata extraction, and visual analysis.
"""

import os
import cv2
import numpy as np
import logging
import tempfile
import ffmpeg
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import hashlib

from media import validate_media_file, is_video_file, get_media_info
from errors import MediaProcessingError, ErrorCode

logger = logging.getLogger(__name__)


@dataclass
class VideoFrame:
    """Represents a video frame with metadata"""
    timestamp: float
    frame_number: int
    image_data: Optional[np.ndarray] = None
    image_path: Optional[str] = None
    width: int = 0
    height: int = 0
    scene_id: Optional[int] = None
    motion_score: float = 0.0
    brightness: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'frame_number': self.frame_number,
            'width': self.width,
            'height': self.height,
            'scene_id': self.scene_id,
            'motion_score': self.motion_score,
            'brightness': self.brightness,
            'image_path': self.image_path
        }


@dataclass
class SceneSegment:
    """Represents a scene segment in video"""
    scene_id: int
    start_time: float
    end_time: float
    start_frame: int
    end_frame: int
    keyframes: List[VideoFrame] = field(default_factory=list)
    
    @property
    def duration(self) -> float:
        """Duration of the scene in seconds"""
        return self.end_time - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'scene_id': self.scene_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'start_frame': self.start_frame,
            'end_frame': self.end_frame,
            'duration': self.duration,
            'keyframes': [frame.to_dict() for frame in self.keyframes]
        }


@dataclass
class VideoAnalysis:
    """Complete video analysis results"""
    video_path: str
    duration: float
    fps: float
    total_frames: int
    width: int
    height: int
    scenes: List[SceneSegment] = field(default_factory=list)
    keyframes: List[VideoFrame] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'video_path': self.video_path,
            'duration': self.duration,
            'fps': self.fps,
            'total_frames': self.total_frames,
            'width': self.width,
            'height': self.height,
            'scenes': [scene.to_dict() for scene in self.scenes],
            'keyframes': [frame.to_dict() for frame in self.keyframes],
            'metadata': self.metadata
        }


class VideoProcessor:
    """Advanced video processing functionality"""
    
    def __init__(self, cache_dir: str = "cache/video"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def analyze_video(self, 
                     video_path: str,
                     extract_frames: bool = True,
                     detect_scenes: bool = True,
                     keyframe_interval: float = 10.0) -> VideoAnalysis:
        """
        Perform comprehensive video analysis
        
        Args:
            video_path: Path to video file
            extract_frames: Whether to extract keyframes
            detect_scenes: Whether to detect scene changes
            keyframe_interval: Interval between keyframes in seconds
            
        Returns:
            VideoAnalysis: Complete analysis results
        """
        try:
            # Validate video file
            if not is_video_file(video_path):
                raise MediaProcessingError(
                    message=f"File is not a video: {video_path}",
                    error_code=ErrorCode.FILE_UNSUPPORTED_FORMAT,
                    user_message="The file is not a supported video format."
                )
            
            # For video processing, we don't require audio - validate file exists and format
            if not os.path.exists(video_path):
                raise MediaProcessingError(
                    message=f"Video file not found: {video_path}",
                    error_code=ErrorCode.FILE_NOT_FOUND,
                    user_message="Video file could not be found."
                )
            
            # Get basic video info using ffprobe (don't require audio for video processing)
            try:
                probe = ffmpeg.probe(video_path)
                format_info = probe.get('format', {})
                video_streams = [s for s in probe['streams'] if s['codec_type'] == 'video']
                
                if not video_streams:
                    raise MediaProcessingError(
                        message=f"No video stream found in file: {video_path}",
                        error_code=ErrorCode.MEDIA_VALIDATION_ERROR,
                        user_message="The file does not contain any video tracks."
                    )
                    
                media_info = {
                    'duration': float(format_info.get('duration', 0)),
                    'format_name': format_info.get('format_name', 'unknown'),
                    'size': int(format_info.get('size', 0))
                }
            except ffmpeg.Error as e:
                raise MediaProcessingError(
                    message=f"Failed to probe video file: {str(e)}",
                    error_code=ErrorCode.MEDIA_VALIDATION_ERROR,
                    user_message="Could not analyze the video file."
                )
            
            # Get detailed video properties using OpenCV
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise MediaProcessingError(
                    message=f"Could not open video file: {video_path}",
                    error_code=ErrorCode.MEDIA_VALIDATION_ERROR,
                    user_message="Could not open the video file for analysis."
                )
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = total_frames / fps if fps > 0 else media_info.get('duration', 0)
            
            # Create analysis object
            analysis = VideoAnalysis(
                video_path=video_path,
                duration=duration,
                fps=fps,
                total_frames=total_frames,
                width=width,
                height=height
            )
            
            # Extract keyframes if requested
            if extract_frames:
                analysis.keyframes = self._extract_keyframes(
                    cap, fps, duration, keyframe_interval
                )
            
            # Detect scenes if requested
            if detect_scenes:
                analysis.scenes = self._detect_scenes(cap, fps, analysis.keyframes)
            
            # Extract additional metadata
            analysis.metadata = self._extract_video_metadata(video_path)
            
            cap.release()
            
            logger.info(f"Video analysis completed: {video_path}")
            return analysis
            
        except Exception as e:
            if isinstance(e, MediaProcessingError):
                raise
            logger.error(f"Video analysis failed: {str(e)}")
            raise MediaProcessingError(
                message=f"Video analysis failed: {str(e)}",
                error_code=ErrorCode.MEDIA_PROCESSING_ERROR,
                user_message="Failed to analyze the video file."
            )
    
    def _extract_keyframes(self, 
                          cap: cv2.VideoCapture,
                          fps: float,
                          duration: float,
                          interval: float) -> List[VideoFrame]:
        """Extract keyframes at regular intervals"""
        keyframes = []
        frame_interval = int(fps * interval)
        
        frame_number = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_number % frame_interval == 0:
                timestamp = frame_number / fps
                
                # Calculate frame statistics
                brightness = np.mean(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
                
                # Save frame to cache
                frame_path = self._save_frame(frame, frame_number, timestamp)
                
                keyframe = VideoFrame(
                    timestamp=timestamp,
                    frame_number=frame_number,
                    width=frame.shape[1],
                    height=frame.shape[0],
                    brightness=float(brightness),
                    image_path=frame_path
                )
                
                keyframes.append(keyframe)
                logger.debug(f"Extracted keyframe at {timestamp:.2f}s")
            
            frame_number += 1
        
        return keyframes
    
    def _detect_scenes(self, 
                      cap: cv2.VideoCapture,
                      fps: float,
                      keyframes: List[VideoFrame]) -> List[SceneSegment]:
        """Detect scene changes using frame difference analysis"""
        scenes = []
        
        if not keyframes:
            # If no keyframes, create a single scene for entire video
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            
            scene = SceneSegment(
                scene_id=0,
                start_time=0.0,
                end_time=duration,
                start_frame=0,
                end_frame=total_frames
            )
            return [scene]
        
        # Simple scene detection based on significant brightness changes
        scene_threshold = 30.0  # Brightness difference threshold
        current_scene_start = 0
        scene_id = 0
        
        for i, frame in enumerate(keyframes):
            if i == 0:
                continue
            
            prev_frame = keyframes[i-1]
            brightness_diff = abs(frame.brightness - prev_frame.brightness)
            
            # Detect scene change
            if brightness_diff > scene_threshold or i == len(keyframes) - 1:
                # End current scene
                scene = SceneSegment(
                    scene_id=scene_id,
                    start_time=keyframes[current_scene_start].timestamp,
                    end_time=frame.timestamp,
                    start_frame=keyframes[current_scene_start].frame_number,
                    end_frame=frame.frame_number,
                    keyframes=keyframes[current_scene_start:i+1]
                )
                
                scenes.append(scene)
                
                # Start new scene
                current_scene_start = i
                scene_id += 1
        
        logger.info(f"Detected {len(scenes)} scenes")
        return scenes
    
    def _extract_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """Extract detailed video metadata"""
        try:
            probe = ffmpeg.probe(video_path)
            
            format_info = probe.get('format', {})
            video_streams = [s for s in probe['streams'] if s['codec_type'] == 'video']
            audio_streams = [s for s in probe['streams'] if s['codec_type'] == 'audio']
            
            metadata = {
                'creation_time': format_info.get('tags', {}).get('creation_time'),
                'format_name': format_info.get('format_name'),
                'format_long_name': format_info.get('format_long_name'),
                'size': int(format_info.get('size', 0)),
                'bit_rate': int(format_info.get('bit_rate', 0)),
                'nb_streams': format_info.get('nb_streams', 0),
                'nb_programs': format_info.get('nb_programs', 0)
            }
            
            # Video stream info
            if video_streams:
                video_stream = video_streams[0]
                metadata.update({
                    'video_codec': video_stream.get('codec_name'),
                    'video_codec_long': video_stream.get('codec_long_name'),
                    'video_profile': video_stream.get('profile'),
                    'video_pixel_format': video_stream.get('pix_fmt'),
                    'video_level': video_stream.get('level'),
                    'video_bit_rate': int(video_stream.get('bit_rate', 0)),
                    'video_avg_frame_rate': video_stream.get('avg_frame_rate'),
                    'video_color_space': video_stream.get('color_space'),
                    'video_color_range': video_stream.get('color_range')
                })
            
            # Audio stream info
            if audio_streams:
                audio_stream = audio_streams[0]
                metadata.update({
                    'audio_codec': audio_stream.get('codec_name'),
                    'audio_codec_long': audio_stream.get('codec_long_name'),
                    'audio_sample_rate': int(audio_stream.get('sample_rate', 0)),
                    'audio_channels': int(audio_stream.get('channels', 0)),
                    'audio_channel_layout': audio_stream.get('channel_layout'),
                    'audio_bit_rate': int(audio_stream.get('bit_rate', 0))
                })
            
            return metadata
            
        except Exception as e:
            logger.warning(f"Failed to extract detailed metadata: {str(e)}")
            return {}
    
    def _save_frame(self, frame: np.ndarray, frame_number: int, timestamp: float) -> str:
        """Save frame to cache directory"""
        try:
            frame_filename = f"frame_{frame_number}_{timestamp:.2f}.jpg"
            frame_path = self.cache_dir / frame_filename
            
            cv2.imwrite(str(frame_path), frame)
            return str(frame_path)
            
        except Exception as e:
            logger.warning(f"Failed to save frame {frame_number}: {str(e)}")
            return ""
    
    def extract_frames_at_timestamps(self, 
                                   video_path: str,
                                   timestamps: List[float]) -> List[VideoFrame]:
        """Extract frames at specific timestamps"""
        frames = []
        
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise MediaProcessingError(
                    message=f"Could not open video: {video_path}",
                    error_code=ErrorCode.MEDIA_VALIDATION_ERROR,
                    user_message="Could not open video file."
                )
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            for timestamp in timestamps:
                frame_number = int(timestamp * fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                
                ret, frame = cap.read()
                if ret:
                    frame_path = self._save_frame(frame, frame_number, timestamp)
                    
                    video_frame = VideoFrame(
                        timestamp=timestamp,
                        frame_number=frame_number,
                        width=frame.shape[1],
                        height=frame.shape[0],
                        brightness=float(np.mean(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))),
                        image_path=frame_path
                    )
                    
                    frames.append(video_frame)
            
            cap.release()
            return frames
            
        except Exception as e:
            logger.error(f"Failed to extract frames at timestamps: {str(e)}")
            raise MediaProcessingError(
                message=f"Frame extraction failed: {str(e)}",
                error_code=ErrorCode.MEDIA_PROCESSING_ERROR,
                user_message="Failed to extract frames from video."
            )
    
    def create_video_thumbnail(self, 
                             video_path: str,
                             timestamp: float = None,
                             size: Tuple[int, int] = (320, 240)) -> str:
        """Create thumbnail image from video"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise MediaProcessingError(
                    message=f"Could not open video: {video_path}",
                    error_code=ErrorCode.MEDIA_VALIDATION_ERROR,
                    user_message="Could not open video file."
                )
            
            # If no timestamp specified, use middle of video
            if timestamp is None:
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                timestamp = (total_frames / 2) / fps if fps > 0 else 0
            
            # Seek to timestamp
            frame_number = int(timestamp * cap.get(cv2.CAP_PROP_FPS))
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            ret, frame = cap.read()
            if not ret:
                raise MediaProcessingError(
                    message="Could not read frame for thumbnail",
                    error_code=ErrorCode.MEDIA_PROCESSING_ERROR,
                    user_message="Failed to create video thumbnail."
                )
            
            # Resize to thumbnail size
            thumbnail = cv2.resize(frame, size)
            
            # Save thumbnail
            video_name = Path(video_path).stem
            thumbnail_path = self.cache_dir / f"{video_name}_thumbnail.jpg"
            cv2.imwrite(str(thumbnail_path), thumbnail)
            
            cap.release()
            
            logger.info(f"Created thumbnail: {thumbnail_path}")
            return str(thumbnail_path)
            
        except Exception as e:
            logger.error(f"Thumbnail creation failed: {str(e)}")
            raise MediaProcessingError(
                message=f"Thumbnail creation failed: {str(e)}",
                error_code=ErrorCode.MEDIA_PROCESSING_ERROR,
                user_message="Failed to create video thumbnail."
            )
    
    def get_video_summary(self, analysis: VideoAnalysis) -> Dict[str, Any]:
        """Generate a summary of video analysis"""
        return {
            'basic_info': {
                'duration': f"{analysis.duration:.2f} seconds",
                'resolution': f"{analysis.width}x{analysis.height}",
                'fps': f"{analysis.fps:.2f}",
                'total_frames': analysis.total_frames
            },
            'content_analysis': {
                'scene_count': len(analysis.scenes),
                'keyframe_count': len(analysis.keyframes),
                'avg_scene_duration': sum(s.duration for s in analysis.scenes) / len(analysis.scenes) if analysis.scenes else 0
            },
            'technical_details': {
                'video_codec': analysis.metadata.get('video_codec', 'unknown'),
                'audio_codec': analysis.metadata.get('audio_codec', 'unknown'),
                'file_size': analysis.metadata.get('size', 0),
                'bit_rate': analysis.metadata.get('bit_rate', 0)
            }
        }