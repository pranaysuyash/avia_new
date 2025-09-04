"""
Advanced Frame Extraction Service for OCR Processing

This module provides comprehensive frame extraction capabilities with multiple sampling strategies,
quality assessment, and intelligent content-based adaptation.
"""

import os
import cv2
import numpy as np
import subprocess
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import tempfile
import hashlib
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SamplingStrategy(Enum):
    """Frame sampling strategies"""
    TIME_BASED = "time_based"
    KEYFRAME = "keyframe"
    SCENE_CHANGE = "scene_change"
    ADAPTIVE = "adaptive"
    HYBRID = "hybrid"


class FrameQuality(Enum):
    """Frame quality assessment levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNUSABLE = "unusable"


@dataclass
class VideoMetadata:
    """Video file metadata"""
    duration: float
    fps: float
    width: int
    height: int
    total_frames: int
    format: str
    codec: str
    bitrate: int
    file_size: int
    aspect_ratio: float
    color_space: str
    has_audio: bool
    creation_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        if self.creation_time:
            data['creation_time'] = self.creation_time.isoformat()
        return data


@dataclass
class FrameQualityMetrics:
    """Frame quality assessment metrics"""
    blur_score: float
    contrast_score: float
    brightness_score: float
    noise_level: float
    sharpness_score: float
    perspective_skew: float
    text_region_density: float
    overall_quality: FrameQuality
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['overall_quality'] = self.overall_quality.value
        return data


@dataclass
class ExtractedFrame:
    """Extracted frame with metadata"""
    frame_number: int
    timestamp: float
    image_data: np.ndarray
    quality_metrics: FrameQualityMetrics
    sampling_reason: str
    file_path: Optional[str] = None
    processing_metadata: Optional[Dict[str, Any]] = None
    
    def save_frame(self, output_dir: str, prefix: str = "frame") -> str:
        """Save frame to disk and return file path"""
        filename = f"{prefix}_{self.frame_number:06d}_{self.timestamp:.3f}s.jpg"
        filepath = os.path.join(output_dir, filename)
        cv2.imwrite(filepath, self.image_data)
        self.file_path = filepath
        return filepath


@dataclass
class ExtractionConfig:
    """Configuration for frame extraction"""
    sampling_strategy: SamplingStrategy = SamplingStrategy.ADAPTIVE
    time_interval: float = 1.0  # seconds
    max_frames: int = 1000
    min_quality_threshold: float = 0.6
    enable_quality_assessment: bool = True
    enable_perspective_correction: bool = True
    enable_preprocessing: bool = True
    target_resolution: Optional[Tuple[int, int]] = None
    keyframe_threshold: float = 0.3
    scene_change_threshold: float = 0.4
    adaptive_complexity_threshold: float = 0.5
    output_format: str = "jpg"
    save_frames: bool = False
    output_directory: Optional[str] = None


class FrameExtractionService:
    """Advanced frame extraction service with multiple sampling strategies"""
    
    def __init__(self, config: Optional[ExtractionConfig] = None):
        self.config = config or ExtractionConfig()
        self.supported_formats = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
        
    def extract_frames(self, video_path: str, config: Optional[ExtractionConfig] = None) -> List[ExtractedFrame]:
        """
        Extract frames from video using configured sampling strategy
        
        Args:
            video_path: Path to video file
            config: Optional extraction configuration
            
        Returns:
            List of extracted frames with metadata
        """
        extraction_config = config or self.config
        
        # Validate video file
        if not self._validate_video_file(video_path):
            raise ValueError(f"Invalid or unsupported video file: {video_path}")
        
        # Get video metadata
        metadata = self.get_video_metadata(video_path)
        logger.info(f"Processing video: {Path(video_path).name}, Duration: {metadata.duration:.2f}s, FPS: {metadata.fps}")
        
        # Estimate frame count and validate limits
        estimated_frames = self.estimate_frame_count(video_path, extraction_config)
        if estimated_frames > extraction_config.max_frames:
            logger.warning(f"Estimated frames ({estimated_frames}) exceeds limit ({extraction_config.max_frames})")
        
        # Create output directory if saving frames
        if extraction_config.save_frames and extraction_config.output_directory:
            os.makedirs(extraction_config.output_directory, exist_ok=True)
        
        # Extract frames based on strategy
        if extraction_config.sampling_strategy == SamplingStrategy.TIME_BASED:
            frames = self._extract_time_based(video_path, extraction_config, metadata)
        elif extraction_config.sampling_strategy == SamplingStrategy.KEYFRAME:
            frames = self._extract_keyframes(video_path, extraction_config, metadata)
        elif extraction_config.sampling_strategy == SamplingStrategy.SCENE_CHANGE:
            frames = self._extract_scene_changes(video_path, extraction_config, metadata)
        elif extraction_config.sampling_strategy == SamplingStrategy.ADAPTIVE:
            frames = self._extract_adaptive(video_path, extraction_config, metadata)
        elif extraction_config.sampling_strategy == SamplingStrategy.HYBRID:
            frames = self._extract_hybrid(video_path, extraction_config, metadata)
        else:
            raise ValueError(f"Unsupported sampling strategy: {extraction_config.sampling_strategy}")
        
        # Apply quality filtering
        if extraction_config.enable_quality_assessment:
            frames = self._filter_by_quality(frames, extraction_config.min_quality_threshold)
        
        # Apply preprocessing if enabled
        if extraction_config.enable_preprocessing:
            frames = self._preprocess_frames(frames, extraction_config)
        
        # Save frames if requested
        if extraction_config.save_frames and extraction_config.output_directory:
            for frame in frames:
                frame.save_frame(extraction_config.output_directory)
        
        logger.info(f"Extracted {len(frames)} frames from video")
        return frames
    
    def get_video_metadata(self, video_path: str) -> VideoMetadata:
        """Extract comprehensive video metadata using FFprobe"""
        try:
            # Use FFprobe to get detailed metadata
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            probe_data = json.loads(result.stdout)
            
            # Find video stream
            video_stream = None
            audio_stream = None
            for stream in probe_data['streams']:
                if stream['codec_type'] == 'video' and not video_stream:
                    video_stream = stream
                elif stream['codec_type'] == 'audio' and not audio_stream:
                    audio_stream = stream
            
            if not video_stream:
                raise ValueError("No video stream found")
            
            # Extract metadata
            format_info = probe_data['format']
            duration = float(format_info.get('duration', 0))
            
            # Parse frame rate
            fps_str = video_stream.get('r_frame_rate', '25/1')
            if '/' in fps_str:
                num, den = map(int, fps_str.split('/'))
                fps = num / den if den != 0 else 25.0
            else:
                fps = float(fps_str)
            
            width = int(video_stream.get('width', 0))
            height = int(video_stream.get('height', 0))
            total_frames = int(video_stream.get('nb_frames', duration * fps))
            
            # Parse creation time if available
            creation_time = None
            if 'creation_time' in format_info.get('tags', {}):
                try:
                    creation_time = datetime.fromisoformat(
                        format_info['tags']['creation_time'].replace('Z', '+00:00')
                    )
                except:
                    pass
            
            return VideoMetadata(
                duration=duration,
                fps=fps,
                width=width,
                height=height,
                total_frames=total_frames,
                format=format_info.get('format_name', 'unknown'),
                codec=video_stream.get('codec_name', 'unknown'),
                bitrate=int(format_info.get('bit_rate', 0)),
                file_size=int(format_info.get('size', 0)),
                aspect_ratio=width / height if height > 0 else 16/9,
                color_space=video_stream.get('color_space', 'unknown'),
                has_audio=audio_stream is not None,
                creation_time=creation_time
            )
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFprobe failed: {e}")
            # Fallback to OpenCV
            return self._get_metadata_opencv(video_path)
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            return self._get_metadata_opencv(video_path)
    
    def estimate_frame_count(self, video_path: str, config: ExtractionConfig) -> int:
        """Estimate number of frames that would be extracted"""
        metadata = self.get_video_metadata(video_path)
        
        if config.sampling_strategy == SamplingStrategy.TIME_BASED:
            return min(int(metadata.duration / config.time_interval), config.max_frames)
        elif config.sampling_strategy == SamplingStrategy.KEYFRAME:
            # Estimate ~10% of frames are keyframes
            return min(int(metadata.total_frames * 0.1), config.max_frames)
        elif config.sampling_strategy == SamplingStrategy.SCENE_CHANGE:
            # Estimate scene changes every 10-30 seconds
            avg_scene_duration = 20.0
            return min(int(metadata.duration / avg_scene_duration), config.max_frames)
        elif config.sampling_strategy == SamplingStrategy.ADAPTIVE:
            # Adaptive sampling varies based on content
            base_frames = int(metadata.duration / config.time_interval)
            return min(int(base_frames * 1.5), config.max_frames)
        elif config.sampling_strategy == SamplingStrategy.HYBRID:
            # Hybrid combines multiple strategies
            time_frames = int(metadata.duration / config.time_interval)
            keyframes = int(metadata.total_frames * 0.1)
            return min(time_frames + keyframes, config.max_frames)
        
        return min(int(metadata.duration / config.time_interval), config.max_frames)
    
    def estimate_processing_cost(self, video_path: str, config: ExtractionConfig) -> Dict[str, Any]:
        """Estimate processing cost and resource requirements"""
        metadata = self.get_video_metadata(video_path)
        estimated_frames = self.estimate_frame_count(video_path, config)
        
        # Base processing time estimates (seconds per frame)
        base_time_per_frame = 0.1
        quality_assessment_overhead = 0.05 if config.enable_quality_assessment else 0
        preprocessing_overhead = 0.03 if config.enable_preprocessing else 0
        
        total_time_per_frame = base_time_per_frame + quality_assessment_overhead + preprocessing_overhead
        estimated_processing_time = estimated_frames * total_time_per_frame
        
        # Storage estimates
        avg_frame_size_kb = (metadata.width * metadata.height * 3) / 1024  # RGB estimate
        estimated_storage_mb = (estimated_frames * avg_frame_size_kb) / 1024
        
        return {
            'estimated_frames': estimated_frames,
            'estimated_processing_time_seconds': estimated_processing_time,
            'estimated_storage_mb': estimated_storage_mb,
            'video_duration': metadata.duration,
            'video_resolution': f"{metadata.width}x{metadata.height}",
            'sampling_strategy': config.sampling_strategy.value,
            'quality_assessment_enabled': config.enable_quality_assessment,
            'preprocessing_enabled': config.enable_preprocessing
        }   
 
    def _validate_video_file(self, video_path: str) -> bool:
        """Validate video file format and accessibility"""
        if not os.path.exists(video_path):
            return False
        
        file_ext = Path(video_path).suffix.lower()
        if file_ext not in self.supported_formats:
            return False
        
        # Try to open with OpenCV as basic validation
        try:
            cap = cv2.VideoCapture(video_path)
            ret = cap.isOpened()
            cap.release()
            return ret
        except:
            return False
    
    def _get_metadata_opencv(self, video_path: str) -> VideoMetadata:
        """Fallback metadata extraction using OpenCV"""
        cap = cv2.VideoCapture(video_path)
        
        try:
            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            
            file_size = os.path.getsize(video_path) if os.path.exists(video_path) else 0
            
            return VideoMetadata(
                duration=duration,
                fps=fps,
                width=width,
                height=height,
                total_frames=frame_count,
                format='unknown',
                codec='unknown',
                bitrate=0,
                file_size=file_size,
                aspect_ratio=width / height if height > 0 else 16/9,
                color_space='unknown',
                has_audio=False
            )
        finally:
            cap.release()
    
    def _extract_time_based(self, video_path: str, config: ExtractionConfig, metadata: VideoMetadata) -> List[ExtractedFrame]:
        """Extract frames at regular time intervals"""
        frames = []
        cap = cv2.VideoCapture(video_path)
        
        try:
            current_time = 0.0
            frame_count = 0
            
            while current_time < metadata.duration and len(frames) < config.max_frames:
                # Seek to timestamp
                cap.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                # Get actual frame number
                frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                actual_timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                
                # Assess frame quality
                quality_metrics = self._assess_frame_quality(frame)
                
                extracted_frame = ExtractedFrame(
                    frame_number=frame_number,
                    timestamp=actual_timestamp,
                    image_data=frame.copy(),
                    quality_metrics=quality_metrics,
                    sampling_reason=f"time_interval_{config.time_interval}s"
                )
                
                frames.append(extracted_frame)
                current_time += config.time_interval
                frame_count += 1
                
                if frame_count % 10 == 0:
                    logger.debug(f"Extracted {frame_count} frames at {current_time:.1f}s")
        
        finally:
            cap.release()
        
        return frames
    
    def _extract_keyframes(self, video_path: str, config: ExtractionConfig, metadata: VideoMetadata) -> List[ExtractedFrame]:
        """Extract keyframes using FFmpeg"""
        frames = []
        
        # Use FFmpeg to extract keyframes
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Extract keyframes to temporary directory
                cmd = [
                    'ffmpeg', '-i', video_path, '-vf', 'select=key', 
                    '-vsync', 'vfr', '-frame_pts', '1',
                    f'{temp_dir}/keyframe_%06d.jpg'
                ]
                
                subprocess.run(cmd, capture_output=True, check=True)
                
                # Load extracted keyframes
                keyframe_files = sorted([f for f in os.listdir(temp_dir) if f.startswith('keyframe_')])
                
                for i, filename in enumerate(keyframe_files[:config.max_frames]):
                    filepath = os.path.join(temp_dir, filename)
                    frame = cv2.imread(filepath)
                    
                    if frame is not None:
                        # Extract timestamp from filename or estimate
                        frame_number = i
                        timestamp = (frame_number / len(keyframe_files)) * metadata.duration
                        
                        quality_metrics = self._assess_frame_quality(frame)
                        
                        extracted_frame = ExtractedFrame(
                            frame_number=frame_number,
                            timestamp=timestamp,
                            image_data=frame,
                            quality_metrics=quality_metrics,
                            sampling_reason="keyframe_detection"
                        )
                        
                        frames.append(extracted_frame)
                        
            except subprocess.CalledProcessError:
                logger.warning("FFmpeg keyframe extraction failed, falling back to OpenCV")
                frames = self._extract_keyframes_opencv(video_path, config, metadata)
        
        return frames
    
    def _extract_keyframes_opencv(self, video_path: str, config: ExtractionConfig, metadata: VideoMetadata) -> List[ExtractedFrame]:
        """Fallback keyframe extraction using OpenCV"""
        frames = []
        cap = cv2.VideoCapture(video_path)
        
        try:
            prev_frame = None
            frame_count = 0
            
            while len(frames) < config.max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                
                # Simple keyframe detection based on frame difference
                if prev_frame is not None:
                    diff = cv2.absdiff(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                                     cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY))
                    diff_score = np.mean(diff) / 255.0
                    
                    if diff_score > config.keyframe_threshold:
                        quality_metrics = self._assess_frame_quality(frame)
                        
                        extracted_frame = ExtractedFrame(
                            frame_number=frame_number,
                            timestamp=timestamp,
                            image_data=frame.copy(),
                            quality_metrics=quality_metrics,
                            sampling_reason=f"keyframe_opencv_diff_{diff_score:.3f}"
                        )
                        
                        frames.append(extracted_frame)
                
                prev_frame = frame.copy()
                frame_count += 1
                
                # Skip frames to avoid processing every single frame
                if frame_count % 5 == 0:
                    for _ in range(4):
                        cap.read()
        
        finally:
            cap.release()
        
        return frames
    
    def _extract_scene_changes(self, video_path: str, config: ExtractionConfig, metadata: VideoMetadata) -> List[ExtractedFrame]:
        """Extract frames at scene change boundaries"""
        frames = []
        cap = cv2.VideoCapture(video_path)
        
        try:
            prev_hist = None
            frame_count = 0
            
            while len(frames) < config.max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                
                # Calculate histogram for scene change detection
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
                hist = cv2.normalize(hist, hist).flatten()
                
                if prev_hist is not None:
                    # Calculate histogram correlation
                    correlation = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
                    
                    # Scene change detected if correlation is low
                    if correlation < (1.0 - config.scene_change_threshold):
                        quality_metrics = self._assess_frame_quality(frame)
                        
                        extracted_frame = ExtractedFrame(
                            frame_number=frame_number,
                            timestamp=timestamp,
                            image_data=frame.copy(),
                            quality_metrics=quality_metrics,
                            sampling_reason=f"scene_change_corr_{correlation:.3f}"
                        )
                        
                        frames.append(extracted_frame)
                
                prev_hist = hist
                frame_count += 1
                
                # Skip frames for performance
                if frame_count % 3 == 0:
                    for _ in range(2):
                        cap.read()
        
        finally:
            cap.release()
        
        return frames
    
    def _extract_adaptive(self, video_path: str, config: ExtractionConfig, metadata: VideoMetadata) -> List[ExtractedFrame]:
        """Adaptive sampling based on content complexity"""
        frames = []
        cap = cv2.VideoCapture(video_path)
        
        try:
            prev_frame = None
            complexity_history = []
            adaptive_interval = config.time_interval
            
            current_time = 0.0
            
            while current_time < metadata.duration and len(frames) < config.max_frames:
                # Seek to timestamp
                cap.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                actual_timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                
                # Calculate content complexity
                complexity = self._calculate_content_complexity(frame)
                complexity_history.append(complexity)
                
                # Keep only recent complexity history
                if len(complexity_history) > 10:
                    complexity_history.pop(0)
                
                # Adapt sampling interval based on complexity
                avg_complexity = np.mean(complexity_history)
                if avg_complexity > config.adaptive_complexity_threshold:
                    # High complexity - sample more frequently
                    adaptive_interval = config.time_interval * 0.5
                else:
                    # Low complexity - sample less frequently
                    adaptive_interval = config.time_interval * 1.5
                
                # Assess frame quality
                quality_metrics = self._assess_frame_quality(frame)
                
                extracted_frame = ExtractedFrame(
                    frame_number=frame_number,
                    timestamp=actual_timestamp,
                    image_data=frame.copy(),
                    quality_metrics=quality_metrics,
                    sampling_reason=f"adaptive_complexity_{complexity:.3f}_interval_{adaptive_interval:.2f}s"
                )
                
                frames.append(extracted_frame)
                current_time += adaptive_interval
        
        finally:
            cap.release()
        
        return frames
    
    def _extract_hybrid(self, video_path: str, config: ExtractionConfig, metadata: VideoMetadata) -> List[ExtractedFrame]:
        """Hybrid sampling combining multiple strategies"""
        all_frames = []
        
        # Extract using different strategies with reduced limits
        time_config = ExtractionConfig(
            sampling_strategy=SamplingStrategy.TIME_BASED,
            time_interval=config.time_interval * 2,  # Less frequent
            max_frames=config.max_frames // 3
        )
        time_frames = self._extract_time_based(video_path, time_config, metadata)
        
        keyframe_config = ExtractionConfig(
            sampling_strategy=SamplingStrategy.KEYFRAME,
            max_frames=config.max_frames // 3
        )
        keyframes = self._extract_keyframes_opencv(video_path, keyframe_config, metadata)
        
        scene_config = ExtractionConfig(
            sampling_strategy=SamplingStrategy.SCENE_CHANGE,
            scene_change_threshold=config.scene_change_threshold,
            max_frames=config.max_frames // 3
        )
        scene_frames = self._extract_scene_changes(video_path, scene_config, metadata)
        
        # Combine and deduplicate frames
        all_frames.extend(time_frames)
        all_frames.extend(keyframes)
        all_frames.extend(scene_frames)
        
        # Remove duplicates based on timestamp proximity (within 0.5 seconds)
        unique_frames = []
        for frame in sorted(all_frames, key=lambda x: x.timestamp):
            is_duplicate = False
            for existing in unique_frames:
                if abs(frame.timestamp - existing.timestamp) < 0.5:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                frame.sampling_reason = f"hybrid_{frame.sampling_reason}"
                unique_frames.append(frame)
        
        return unique_frames[:config.max_frames]
    
    def _assess_frame_quality(self, frame: np.ndarray) -> FrameQualityMetrics:
        """Comprehensive frame quality assessment"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Blur detection using Laplacian variance
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        blur_normalized = min(blur_score / 1000.0, 1.0)
        
        # Contrast assessment
        contrast_score = gray.std() / 255.0
        
        # Brightness assessment
        brightness_score = gray.mean() / 255.0
        
        # Noise level estimation
        noise_level = self._estimate_noise_level(gray)
        
        # Sharpness using gradient magnitude
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        sharpness_score = np.mean(np.sqrt(grad_x**2 + grad_y**2)) / 255.0
        
        # Perspective skew detection
        perspective_skew = self._detect_perspective_skew(gray)
        
        # Text region density estimation
        text_density = self._estimate_text_density(gray)
        
        # Overall quality calculation
        quality_score = (
            blur_normalized * 0.25 +
            contrast_score * 0.20 +
            (1.0 - abs(brightness_score - 0.5) * 2) * 0.15 +  # Prefer mid-range brightness
            (1.0 - noise_level) * 0.15 +
            sharpness_score * 0.15 +
            (1.0 - perspective_skew) * 0.10
        )
        
        # Determine quality level
        if quality_score >= 0.8:
            overall_quality = FrameQuality.EXCELLENT
        elif quality_score >= 0.6:
            overall_quality = FrameQuality.GOOD
        elif quality_score >= 0.4:
            overall_quality = FrameQuality.FAIR
        elif quality_score >= 0.2:
            overall_quality = FrameQuality.POOR
        else:
            overall_quality = FrameQuality.UNUSABLE
        
        return FrameQualityMetrics(
            blur_score=blur_normalized,
            contrast_score=contrast_score,
            brightness_score=brightness_score,
            noise_level=noise_level,
            sharpness_score=sharpness_score,
            perspective_skew=perspective_skew,
            text_region_density=text_density,
            overall_quality=overall_quality,
            confidence=quality_score
        )
    
    def _estimate_noise_level(self, gray_image: np.ndarray) -> float:
        """Estimate noise level in grayscale image"""
        # Use Laplacian to detect noise
        laplacian = cv2.Laplacian(gray_image, cv2.CV_64F)
        noise_estimate = laplacian.var()
        return min(noise_estimate / 10000.0, 1.0)
    
    def _detect_perspective_skew(self, gray_image: np.ndarray) -> float:
        """Detect perspective skew in image"""
        # Use Hough line detection to find dominant lines
        edges = cv2.Canny(gray_image, 50, 150)
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        if lines is None or len(lines) < 2:
            return 0.0
        
        # Calculate angle deviations from horizontal/vertical
        angles = []
        for line in lines[:10]:  # Use first 10 lines
            rho, theta = line[0]
            angle = theta * 180 / np.pi
            # Normalize to 0-90 degrees
            angle = min(angle, 180 - angle)
            angles.append(angle)
        
        # Calculate deviation from expected angles (0, 45, 90 degrees)
        deviations = []
        for angle in angles:
            dev = min(abs(angle), abs(angle - 45), abs(angle - 90))
            deviations.append(dev)
        
        avg_deviation = np.mean(deviations) if deviations else 0
        return min(avg_deviation / 45.0, 1.0)  # Normalize to 0-1
    
    def _estimate_text_density(self, gray_image: np.ndarray) -> float:
        """Estimate text region density in image"""
        # Use MSER (Maximally Stable Extremal Regions) for text detection
        mser = cv2.MSER_create()
        regions, _ = mser.detectRegions(gray_image)
        
        if not regions:
            return 0.0
        
        # Calculate total area of detected regions
        total_area = 0
        image_area = gray_image.shape[0] * gray_image.shape[1]
        
        for region in regions:
            if len(region) > 10:  # Filter small regions
                hull = cv2.convexHull(region.reshape(-1, 1, 2))
                area = cv2.contourArea(hull)
                total_area += area
        
        text_density = min(total_area / image_area, 1.0)
        return text_density
    
    def _calculate_content_complexity(self, frame: np.ndarray) -> float:
        """Calculate content complexity for adaptive sampling"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Edge density
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # Texture complexity using Local Binary Pattern variance
        # Simplified texture measure using gradient variance
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        texture_complexity = np.var(np.sqrt(grad_x**2 + grad_y**2)) / 10000.0
        
        # Color variance
        color_variance = np.var(frame) / 10000.0
        
        # Combine metrics
        complexity = (edge_density * 0.4 + 
                     min(texture_complexity, 1.0) * 0.4 + 
                     min(color_variance, 1.0) * 0.2)
        
        return min(complexity, 1.0)
    
    def _filter_by_quality(self, frames: List[ExtractedFrame], min_threshold: float) -> List[ExtractedFrame]:
        """Filter frames by quality threshold"""
        filtered_frames = []
        
        for frame in frames:
            if frame.quality_metrics.confidence >= min_threshold:
                filtered_frames.append(frame)
            else:
                logger.debug(f"Filtered frame at {frame.timestamp:.2f}s due to low quality: {frame.quality_metrics.confidence:.3f}")
        
        logger.info(f"Quality filtering: {len(filtered_frames)}/{len(frames)} frames passed threshold {min_threshold}")
        return filtered_frames
    
    def _preprocess_frames(self, frames: List[ExtractedFrame], config: ExtractionConfig) -> List[ExtractedFrame]:
        """Apply preprocessing to improve OCR accuracy"""
        processed_frames = []
        
        for frame in frames:
            processed_image = frame.image_data.copy()
            
            # Resize if target resolution specified
            if config.target_resolution:
                target_width, target_height = config.target_resolution
                processed_image = cv2.resize(processed_image, (target_width, target_height))
            
            # Perspective correction if enabled and needed
            if config.enable_perspective_correction and frame.quality_metrics.perspective_skew > 0.3:
                processed_image = self._correct_perspective(processed_image)
            
            # Enhance contrast and brightness
            processed_image = self._enhance_image(processed_image)
            
            # Update frame with processed image
            frame.image_data = processed_image
            frame.processing_metadata = {
                'resized': config.target_resolution is not None,
                'perspective_corrected': config.enable_perspective_correction and frame.quality_metrics.perspective_skew > 0.3,
                'enhanced': True
            }
            
            processed_frames.append(frame)
        
        return processed_frames
    
    def _correct_perspective(self, image: np.ndarray) -> np.ndarray:
        """Apply basic perspective correction"""
        # This is a simplified perspective correction
        # In production, you might want more sophisticated methods
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours and approximate to rectangles
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            # Approximate contour to polygon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # If we found a quadrilateral, apply perspective transform
            if len(approx) == 4 and cv2.contourArea(approx) > 1000:
                # Order points: top-left, top-right, bottom-right, bottom-left
                rect = self._order_points(approx.reshape(4, 2))
                
                # Calculate dimensions of the corrected image
                width = max(
                    np.linalg.norm(rect[1] - rect[0]),
                    np.linalg.norm(rect[3] - rect[2])
                )
                height = max(
                    np.linalg.norm(rect[2] - rect[1]),
                    np.linalg.norm(rect[3] - rect[0])
                )
                
                # Define destination points
                dst = np.array([
                    [0, 0],
                    [width - 1, 0],
                    [width - 1, height - 1],
                    [0, height - 1]
                ], dtype=np.float32)
                
                # Calculate perspective transform matrix
                matrix = cv2.getPerspectiveTransform(rect.astype(np.float32), dst)
                
                # Apply perspective correction
                corrected = cv2.warpPerspective(image, matrix, (int(width), int(height)))
                return corrected
        
        return image  # Return original if no suitable quadrilateral found
    
    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        """Order points in clockwise order starting from top-left"""
        # Sort by y-coordinate
        y_sorted = pts[np.argsort(pts[:, 1])]
        
        # Top two points
        top = y_sorted[:2]
        top_left = top[np.argmin(top[:, 0])]
        top_right = top[np.argmax(top[:, 0])]
        
        # Bottom two points
        bottom = y_sorted[2:]
        bottom_left = bottom[np.argmin(bottom[:, 0])]
        bottom_right = bottom[np.argmax(bottom[:, 0])]
        
        return np.array([top_left, top_right, bottom_right, bottom_left])
    
    def _enhance_image(self, image: np.ndarray) -> np.ndarray:
        """Enhance image for better OCR accuracy"""
        # Convert to LAB color space for better contrast enhancement
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to L channel
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Merge channels and convert back to BGR
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        # Apply slight sharpening
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        # Blend original and sharpened (50% each)
        result = cv2.addWeighted(enhanced, 0.7, sharpened, 0.3, 0)
        
        return result


# Utility functions for external use
def create_extraction_config(**kwargs) -> ExtractionConfig:
    """Create extraction configuration with custom parameters"""
    return ExtractionConfig(**kwargs)


def extract_frames_from_video(video_path: str, **config_kwargs) -> List[ExtractedFrame]:
    """Convenience function to extract frames with custom configuration"""
    config = create_extraction_config(**config_kwargs)
    service = FrameExtractionService(config)
    return service.extract_frames(video_path)


def get_video_info(video_path: str) -> Dict[str, Any]:
    """Get video metadata as dictionary"""
    service = FrameExtractionService()
    metadata = service.get_video_metadata(video_path)
    return metadata.to_dict()


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python frame_extraction_service.py <video_path>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    
    # Create service with default configuration
    service = FrameExtractionService()
    
    # Get video metadata
    print("Video Metadata:")
    metadata = service.get_video_metadata(video_path)
    print(json.dumps(metadata.to_dict(), indent=2))
    
    # Estimate processing cost
    config = ExtractionConfig(sampling_strategy=SamplingStrategy.ADAPTIVE, max_frames=50)
    cost_estimate = service.estimate_processing_cost(video_path, config)
    print("\nProcessing Cost Estimate:")
    print(json.dumps(cost_estimate, indent=2))
    
    # Extract frames
    print(f"\nExtracting frames using {config.sampling_strategy.value} strategy...")
    frames = service.extract_frames(video_path, config)
    
    print(f"\nExtracted {len(frames)} frames:")
    for i, frame in enumerate(frames[:5]):  # Show first 5 frames
        print(f"Frame {i+1}: t={frame.timestamp:.2f}s, quality={frame.quality_metrics.overall_quality.value}, "
              f"confidence={frame.quality_metrics.confidence:.3f}, reason={frame.sampling_reason}")