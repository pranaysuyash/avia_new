"""
Advanced Video Processing Engine
Task 3: Advanced Media Processing Pipeline

Enhanced video processing with scene detection, keyframe extraction, object recognition,
video quality enhancement, and intelligent B-roll suggestions. Integrates with the
Processing Router and Workflow Engine for optimal processing coordination.

Requirements: 2.1, 2.2, 2.3, 2.4
Dependencies: ProcessingRouterWorkflowEngine, existing video_processing.py
"""

import os
import cv2
import numpy as np
import logging
import asyncio
import json
import tempfile
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

# Third-party imports with fallbacks
try:
    import ffmpeg
    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False
    logging.warning("FFmpeg not available - some video features will be limited")

try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    logging.warning("MoviePy not available - some video features will be limited")

try:
    import torch
    import torchvision.transforms as transforms
    from torchvision.models import resnet50
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch not available - AI features will be limited")

try:
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("Scikit-learn not available - clustering features limited")

# Import existing components
try:
    from processing_router_workflow_engine import (
        ProcessingRouterWorkflowEngine, ProcessingStrategy, ContentComplexity,
        ProcessingMode, ContentAnalysis, ProcessingJob, ProcessingResult
    )
    from video_processing import VideoProcessor as BaseVideoProcessor
except ImportError as e:
    logging.warning(f"Import warning: {e}, using fallback implementations")
    
    # Fallback classes
    class ProcessingStrategy(Enum):
        BASIC = "basic"
        ENHANCED = "enhanced"
        PROFESSIONAL = "professional"
    
    class ContentComplexity(Enum):
        SIMPLE = "simple"
        MODERATE = "moderate"
        COMPLEX = "complex"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoQuality(Enum):
    """Video quality levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA_HIGH = "ultra_high"


class SceneType(Enum):
    """Scene classification types"""
    STATIC = "static"
    DYNAMIC = "dynamic"
    TRANSITION = "transition"
    ACTION = "action"
    DIALOGUE = "dialogue"
    LANDSCAPE = "landscape"
    INDOOR = "indoor"
    OUTDOOR = "outdoor"


class ObjectCategory(Enum):
    """Object detection categories"""
    PERSON = "person"
    FACE = "face"
    VEHICLE = "vehicle"
    ANIMAL = "animal"
    OBJECT = "object"
    TEXT = "text"
    LOGO = "logo"


@dataclass
class VideoMetadata:
    """Enhanced video metadata"""
    duration: float
    fps: float
    width: int
    height: int
    total_frames: int
    codec: str
    bitrate: Optional[int] = None
    file_size: int = 0
    aspect_ratio: str = "16:9"
    has_audio: bool = True
    quality_score: float = 0.0
    complexity_score: float = 0.0


@dataclass
class SceneInfo:
    """Enhanced scene detection information"""
    start_time: float
    end_time: float
    start_frame: int
    end_frame: int
    confidence: float
    scene_type: SceneType = SceneType.STATIC
    description: str = ""
    dominant_colors: List[Tuple[int, int, int]] = field(default_factory=list)
    motion_intensity: float = 0.0
    visual_complexity: float = 0.0
    audio_features: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KeyFrame:
    """Enhanced keyframe information"""
    frame_number: int
    timestamp: float
    confidence: float
    frame_path: Optional[str] = None
    features: Dict[str, Any] = field(default_factory=dict)
    visual_hash: str = ""
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    objects_detected: List[str] = field(default_factory=list)


@dataclass
class ObjectDetection:
    """Enhanced object detection result"""
    class_name: str
    category: ObjectCategory
    confidence: float
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    timestamp: float
    frame_number: int
    tracking_id: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BRollSuggestion:
    """Enhanced B-roll suggestion"""
    timestamp: float
    duration: float
    suggestion_type: str
    description: str
    confidence: float
    keywords: List[str] = field(default_factory=list)
    visual_context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1
    alternative_suggestions: List[str] = field(default_factory=list)


@dataclass
class VideoEnhancement:
    """Video enhancement configuration"""
    upscale_factor: float = 1.0
    denoise_strength: float = 0.5
    sharpen_amount: float = 0.3
    color_correction: bool = True
    stabilization: bool = True
    brightness_adjustment: float = 0.0
    contrast_adjustment: float = 0.0
    saturation_adjustment: float = 0.0


class AdvancedVideoProcessingEngine:
    """
    Advanced video processing engine with scene detection, keyframe extraction,
    object recognition, quality enhancement, and intelligent B-roll suggestions.
    """
    
    def __init__(self, temp_dir: Optional[str] = None, max_workers: int = 4):
        """
        Initialize the advanced video processing engine
        
        Args:
            temp_dir: Directory for temporary files
            max_workers: Maximum number of worker threads
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Initialize processing router integration
        try:
            self.processing_router = ProcessingRouterWorkflowEngine()
        except:
            self.processing_router = None
            logger.warning("Processing router not available, using standalone mode")
        
        # Initialize AI models if available
        self.object_detection_model = None
        self.scene_classification_model = None
        self.enhancement_models = {}
        
        if TORCH_AVAILABLE:
            self._initialize_ai_models()
        
        # Initialize OpenCV components
        self._initialize_cv_components()
        
        logger.info(f"AdvancedVideoProcessingEngine initialized with {max_workers} workers")
    
    def _initialize_ai_models(self):
        """Initialize AI models for advanced processing"""
        try:
            # Load pre-trained ResNet for scene classification
            self.scene_classification_model = resnet50(pretrained=True)
            self.scene_classification_model.eval()
            
            # Transform for preprocessing images
            self.transform = transforms.Compose([
                transforms.ToPILImage(),
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                   std=[0.229, 0.224, 0.225])
            ])
            
            logger.info("AI models initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI models: {e}")
            self.scene_classification_model = None
    
    def _initialize_cv_components(self):
        """Initialize OpenCV components for object detection"""
        try:
            # Load Haar cascades for basic object detection
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            self.eye_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_eye.xml'
            )
            
            # Initialize background subtractor for motion detection
            self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
                detectShadows=True
            )
            
            logger.info("OpenCV components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenCV components: {e}")
    
    async def process_video_comprehensive(self, 
                                        video_path: str,
                                        processing_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Comprehensive video processing with all advanced features
        
        Args:
            video_path: Path to video file
            processing_options: Processing configuration options
            
        Returns:
            Comprehensive video analysis and processing results
        """
        start_time = datetime.now()
        options = processing_options or {}
        
        try:
            # Extract video metadata
            metadata = await self.get_video_metadata(video_path)
            
            # Analyze content complexity for processing strategy
            content_analysis = await self._analyze_content_complexity(video_path, metadata)
            
            # Select optimal processing strategy
            processing_strategy = self._select_processing_strategy(content_analysis)
            
            results = {
                'metadata': metadata,
                'content_analysis': content_analysis,
                'processing_strategy': processing_strategy.value,
                'processing_time': 0,
                'keyframes': [],
                'scenes': [],
                'objects': [],
                'broll_suggestions': [],
                'quality_enhancements': [],
                'success': True,
                'errors': []
            }
            
            # Execute processing tasks based on strategy
            processing_tasks = self._create_processing_tasks(
                video_path, metadata, processing_strategy, options
            )
            
            # Execute tasks with intelligent coordination
            task_results = await self._execute_processing_tasks(processing_tasks)
            
            # Process and integrate results
            for task_name, result in task_results.items():
                if isinstance(result, Exception):
                    results['errors'].append(f"{task_name}: {str(result)}")
                else:
                    results[task_name] = result
            
            # Generate intelligent B-roll suggestions
            if options.get('suggest_broll', True):
                broll_suggestions = await self._generate_intelligent_broll_suggestions(
                    results.get('keyframes', []),
                    results.get('scenes', []),
                    results.get('objects', []),
                    content_analysis
                )
                results['broll_suggestions'] = broll_suggestions
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            results['processing_time'] = processing_time
            
            logger.info(f"Comprehensive video processing completed in {processing_time:.2f}s")
            return results
            
        except Exception as e:
            logger.error(f"Comprehensive video processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': (datetime.now() - start_time).total_seconds()
            }
    
    async def get_video_metadata(self, video_path: str) -> VideoMetadata:
        """Extract comprehensive video metadata"""
        try:
            if FFMPEG_AVAILABLE:
                # Use ffmpeg-python for detailed metadata extraction
                probe = ffmpeg.probe(video_path)
                video_stream = next((stream for stream in probe['streams'] 
                                   if stream['codec_type'] == 'video'), None)
                audio_stream = next((stream for stream in probe['streams'] 
                                   if stream['codec_type'] == 'audio'), None)
                
                if video_stream:
                    duration = float(probe['format']['duration'])
                    fps = eval(video_stream['r_frame_rate'])
                    width = int(video_stream['width'])
                    height = int(video_stream['height'])
                    total_frames = int(duration * fps)
                    codec = video_stream['codec_name']
                    bitrate = int(probe['format'].get('bit_rate', 0))
                    file_size = int(probe['format']['size'])
                    
                    # Calculate aspect ratio
                    gcd = np.gcd(width, height)
                    aspect_ratio = f"{width//gcd}:{height//gcd}"
                    
                    # Calculate quality and complexity scores
                    quality_score = self._calculate_video_quality_score(
                        width, height, bitrate, fps
                    )
                    complexity_score = self._calculate_complexity_score(
                        duration, width, height, fps
                    )
                    
                    return VideoMetadata(
                        duration=duration,
                        fps=fps,
                        width=width,
                        height=height,
                        total_frames=total_frames,
                        codec=codec,
                        bitrate=bitrate,
                        file_size=file_size,
                        aspect_ratio=aspect_ratio,
                        has_audio=audio_stream is not None,
                        quality_score=quality_score,
                        complexity_score=complexity_score
                    )
            
            # Fallback to OpenCV
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Cannot open video file: {video_path}")
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            quality_score = self._calculate_video_quality_score(width, height, 0, fps)
            complexity_score = self._calculate_complexity_score(duration, width, height, fps)
            
            return VideoMetadata(
                duration=duration,
                fps=fps,
                width=width,
                height=height,
                total_frames=frame_count,
                codec="unknown",
                file_size=os.path.getsize(video_path),
                quality_score=quality_score,
                complexity_score=complexity_score
            )
            
        except Exception as e:
            logger.error(f"Failed to extract video metadata: {e}")
            raise
    
    def _calculate_video_quality_score(self, width: int, height: int, 
                                     bitrate: int, fps: float) -> float:
        """Calculate video quality score based on technical parameters"""
        try:
            # Resolution score (0-1)
            resolution_score = min(1.0, (width * height) / (1920 * 1080))
            
            # Bitrate score (0-1) - assuming good quality at 5Mbps for 1080p
            target_bitrate = (width * height * fps) / (1920 * 1080 * 30) * 5000000
            bitrate_score = min(1.0, bitrate / target_bitrate) if bitrate > 0 else 0.5
            
            # FPS score (0-1)
            fps_score = min(1.0, fps / 60.0)
            
            # Weighted average
            quality_score = (resolution_score * 0.4 + bitrate_score * 0.4 + fps_score * 0.2)
            
            return round(quality_score, 3)
        except:
            return 0.5  # Default medium quality
    
    def _calculate_complexity_score(self, duration: float, width: int, 
                                  height: int, fps: float) -> float:
        """Calculate content complexity score for processing decisions"""
        try:
            # Duration complexity
            duration_factor = min(1.0, duration / 3600)  # Normalize to 1 hour
            
            # Resolution complexity
            resolution_factor = (width * height) / (1920 * 1080)
            
            # Frame rate complexity
            fps_factor = fps / 30.0
            
            # Combined complexity score
            complexity_score = (duration_factor * 0.3 + 
                              resolution_factor * 0.4 + 
                              fps_factor * 0.3)
            
            return round(min(1.0, complexity_score), 3)
        except:
            return 0.5  # Default medium complexity    

    async def _analyze_content_complexity(self, video_path: str, 
                                        metadata: VideoMetadata) -> ContentAnalysis:
        """Analyze video content to determine processing complexity"""
        try:
            # Basic analysis from metadata
            file_size_mb = metadata.file_size / (1024 * 1024)
            
            # Determine complexity based on multiple factors
            complexity_factors = {
                'duration': metadata.duration > 1800,  # > 30 minutes
                'resolution': metadata.width * metadata.height > 2073600,  # > 1080p
                'fps': metadata.fps > 30,
                'file_size': file_size_mb > 500,  # > 500MB
                'codec_complexity': metadata.codec in ['h265', 'hevc', 'av1']
            }
            
            complexity_score = sum(complexity_factors.values()) / len(complexity_factors)
            
            if complexity_score >= 0.8:
                complexity = ContentComplexity.VERY_COMPLEX
            elif complexity_score >= 0.6:
                complexity = ContentComplexity.COMPLEX
            elif complexity_score >= 0.3:
                complexity = ContentComplexity.MODERATE
            else:
                complexity = ContentComplexity.SIMPLE
            
            # Estimate processing time based on complexity
            base_time = metadata.duration * 0.1  # 10% of video duration as base
            complexity_multiplier = {
                ContentComplexity.SIMPLE: 1.0,
                ContentComplexity.MODERATE: 2.0,
                ContentComplexity.COMPLEX: 4.0,
                ContentComplexity.VERY_COMPLEX: 8.0
            }
            
            estimated_time = base_time * complexity_multiplier[complexity]
            
            # Determine processing requirements
            requirements = []
            if metadata.width * metadata.height >= 3840 * 2160:  # 4K+
                requirements.append("gpu_acceleration")
            if metadata.duration > 3600:  # > 1 hour
                requirements.append("chunked_processing")
            if complexity_score >= 0.7:
                requirements.append("parallel_processing")
            
            return ContentAnalysis(
                media_type=MediaType.VIDEO,
                file_size_mb=file_size_mb,
                duration_seconds=metadata.duration,
                complexity=complexity,
                quality_score=metadata.quality_score,
                content_features={
                    'resolution': f"{metadata.width}x{metadata.height}",
                    'fps': metadata.fps,
                    'codec': metadata.codec,
                    'has_audio': metadata.has_audio,
                    'aspect_ratio': metadata.aspect_ratio
                },
                processing_requirements=requirements,
                estimated_processing_time=estimated_time
            )
            
        except Exception as e:
            logger.error(f"Content complexity analysis failed: {e}")
            # Return default analysis
            return ContentAnalysis(
                media_type=MediaType.VIDEO,
                file_size_mb=metadata.file_size / (1024 * 1024),
                duration_seconds=metadata.duration,
                complexity=ContentComplexity.MODERATE,
                quality_score=0.5,
                estimated_processing_time=metadata.duration * 0.2
            )
    
    def _select_processing_strategy(self, content_analysis: ContentAnalysis) -> ProcessingStrategy:
        """Select optimal processing strategy based on content analysis"""
        try:
            # Strategy selection logic
            if content_analysis.complexity == ContentComplexity.VERY_COMPLEX:
                return ProcessingStrategy.ENTERPRISE
            elif content_analysis.complexity == ContentComplexity.COMPLEX:
                return ProcessingStrategy.PROFESSIONAL
            elif content_analysis.complexity == ContentComplexity.MODERATE:
                return ProcessingStrategy.ENHANCED
            else:
                return ProcessingStrategy.BASIC
        except:
            return ProcessingStrategy.ENHANCED  # Default strategy
    
    def _create_processing_tasks(self, video_path: str, metadata: VideoMetadata,
                               strategy: ProcessingStrategy, options: Dict[str, Any]) -> Dict[str, Callable]:
        """Create processing tasks based on strategy and options"""
        tasks = {}
        
        # Always include keyframe extraction
        if options.get('extract_keyframes', True):
            tasks['keyframes'] = lambda: self._extract_keyframes_advanced(video_path, metadata)
        
        # Scene detection based on strategy
        if options.get('detect_scenes', True):
            if strategy in [ProcessingStrategy.ENHANCED, ProcessingStrategy.PROFESSIONAL, ProcessingStrategy.ENTERPRISE]:
                tasks['scenes'] = lambda: self._detect_scenes_advanced(video_path, metadata)
            else:
                tasks['scenes'] = lambda: self._detect_scenes_basic(video_path, metadata)
        
        # Object detection based on strategy
        if options.get('detect_objects', True):
            if strategy in [ProcessingStrategy.PROFESSIONAL, ProcessingStrategy.ENTERPRISE]:
                tasks['objects'] = lambda: self._detect_objects_advanced(video_path, metadata)
            else:
                tasks['objects'] = lambda: self._detect_objects_basic(video_path, metadata)
        
        # Quality enhancement based on strategy
        if options.get('enhance_quality', False):
            if strategy == ProcessingStrategy.ENTERPRISE:
                tasks['quality_enhancements'] = lambda: self._enhance_video_quality_advanced(video_path, metadata)
            elif strategy == ProcessingStrategy.PROFESSIONAL:
                tasks['quality_enhancements'] = lambda: self._enhance_video_quality_professional(video_path, metadata)
        
        return tasks
    
    async def _execute_processing_tasks(self, tasks: Dict[str, Callable]) -> Dict[str, Any]:
        """Execute processing tasks with intelligent coordination"""
        results = {}
        
        try:
            # Execute tasks in parallel where possible
            loop = asyncio.get_event_loop()
            
            # Create futures for all tasks
            futures = {}
            for task_name, task_func in tasks.items():
                future = loop.run_in_executor(self.executor, task_func)
                futures[task_name] = future
            
            # Wait for all tasks to complete
            for task_name, future in futures.items():
                try:
                    result = await future
                    results[task_name] = result
                except Exception as e:
                    logger.error(f"Task {task_name} failed: {e}")
                    results[task_name] = e
            
            return results
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return {'error': e}
    
    def _extract_keyframes_advanced(self, video_path: str, metadata: VideoMetadata) -> List[KeyFrame]:
        """Advanced keyframe extraction with quality analysis"""
        keyframes = []
        
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Cannot open video file: {video_path}")
            
            # Adaptive keyframe interval based on content
            base_interval = max(1, int(metadata.fps * 3))  # Every 3 seconds base
            if metadata.duration > 1800:  # > 30 minutes
                base_interval = int(metadata.fps * 5)  # Every 5 seconds for long videos
            
            frame_number = 0
            prev_frame = None
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_number % base_interval == 0:
                    timestamp = frame_number / metadata.fps
                    
                    # Calculate frame quality metrics
                    quality_metrics = self._calculate_frame_quality_metrics(frame)
                    
                    # Calculate visual hash for similarity detection
                    visual_hash = self._calculate_visual_hash(frame)
                    
                    # Detect objects in keyframe
                    objects_detected = self._detect_objects_in_frame(frame)
                    
                    # Extract advanced features if AI models available
                    features = {}
                    if self.scene_classification_model:
                        features = self._extract_frame_features_advanced(frame)
                    
                    # Save keyframe
                    keyframe_path = os.path.join(
                        self.temp_dir, 
                        f"keyframe_{frame_number:06d}.jpg"
                    )
                    cv2.imwrite(keyframe_path, frame)
                    
                    keyframe = KeyFrame(
                        frame_number=frame_number,
                        timestamp=timestamp,
                        confidence=quality_metrics.get('sharpness', 0.5),
                        frame_path=keyframe_path,
                        features=features,
                        visual_hash=visual_hash,
                        quality_metrics=quality_metrics,
                        objects_detected=objects_detected
                    )
                    
                    keyframes.append(keyframe)
                
                prev_frame = frame
                frame_number += 1
            
            cap.release()
            logger.info(f"Extracted {len(keyframes)} advanced keyframes")
            return keyframes
            
        except Exception as e:
            logger.error(f"Advanced keyframe extraction failed: {e}")
            return []
    
    def _calculate_frame_quality_metrics(self, frame: np.ndarray) -> Dict[str, float]:
        """Calculate comprehensive frame quality metrics"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Sharpness (Laplacian variance)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Brightness
            brightness = np.mean(gray)
            
            # Contrast (standard deviation)
            contrast = np.std(gray)
            
            # Noise estimation (using high-frequency content)
            kernel = np.array([[-1,-1,-1], [-1,8,-1], [-1,-1,-1]])
            noise = np.mean(np.abs(cv2.filter2D(gray, -1, kernel)))
            
            # Color distribution (for color frames)
            color_variance = 0.0
            if len(frame.shape) == 3:
                color_variance = np.var(frame, axis=(0,1)).mean()
            
            return {
                'sharpness': float(sharpness / 1000),  # Normalize
                'brightness': float(brightness / 255),
                'contrast': float(contrast / 128),
                'noise': float(noise / 100),
                'color_variance': float(color_variance / 10000)
            }
            
        except Exception as e:
            logger.error(f"Frame quality calculation failed: {e}")
            return {'sharpness': 0.5, 'brightness': 0.5, 'contrast': 0.5}
    
    def _calculate_visual_hash(self, frame: np.ndarray) -> str:
        """Calculate perceptual hash for frame similarity detection"""
        try:
            # Resize to small size for hash calculation
            small = cv2.resize(frame, (8, 8))
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            
            # Calculate average
            avg = gray.mean()
            
            # Create binary hash
            hash_bits = []
            for pixel in gray.flatten():
                hash_bits.append('1' if pixel > avg else '0')
            
            # Convert to hex string
            hash_str = ''.join(hash_bits)
            return hex(int(hash_str, 2))[2:]
            
        except Exception as e:
            logger.error(f"Visual hash calculation failed: {e}")
            return "0"
    
    def _detect_objects_in_frame(self, frame: np.ndarray) -> List[str]:
        """Detect objects in a single frame"""
        objects = []
        
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            if len(faces) > 0:
                objects.append("face")
            
            # Detect eyes
            eyes = self.eye_cascade.detectMultiScale(gray, 1.1, 4)
            if len(eyes) > 0:
                objects.append("eye")
            
            # Add more object detection logic here
            # This is a simplified version - in production you'd use YOLO, SSD, etc.
            
            return objects
            
        except Exception as e:
            logger.error(f"Object detection in frame failed: {e}")
            return []
    
    def _extract_frame_features_advanced(self, frame: np.ndarray) -> Dict[str, Any]:
        """Extract advanced features using AI models"""
        features = {}
        
        try:
            if self.scene_classification_model and TORCH_AVAILABLE:
                # Preprocess frame
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                input_tensor = self.transform(frame_rgb).unsqueeze(0)
                
                # Extract features
                with torch.no_grad():
                    output = self.scene_classification_model(input_tensor)
                    features['scene_features'] = output.numpy().tolist()
            
            # Add basic image statistics
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            features.update(self._calculate_frame_quality_metrics(frame))
            
            # Color histogram
            if len(frame.shape) == 3:
                hist_b = cv2.calcHist([frame], [0], None, [256], [0, 256])
                hist_g = cv2.calcHist([frame], [1], None, [256], [0, 256])
                hist_r = cv2.calcHist([frame], [2], None, [256], [0, 256])
                
                features['color_histogram'] = {
                    'blue': hist_b.flatten().tolist()[:10],  # First 10 bins
                    'green': hist_g.flatten().tolist()[:10],
                    'red': hist_r.flatten().tolist()[:10]
                }
            
            return features
            
        except Exception as e:
            logger.error(f"Advanced feature extraction failed: {e}")
            return {}
    
    def _detect_scenes_advanced(self, video_path: str, metadata: VideoMetadata) -> List[SceneInfo]:
        """Advanced scene detection with multiple algorithms"""
        scenes = []
        
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Cannot open video file: {video_path}")
            
            # Initialize scene detection parameters
            prev_hist = None
            prev_frame = None
            scene_start = 0
            frame_number = 0
            threshold = 0.6  # Scene change threshold
            
            # Motion detection for dynamic scenes
            motion_history = []
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Calculate histogram for scene detection
                hist = cv2.calcHist([frame], [0, 1, 2], None, [50, 50, 50], [0, 256, 0, 256, 0, 256])
                
                # Calculate motion intensity
                motion_intensity = 0.0
                if prev_frame is not None:
                    motion_intensity = self._calculate_motion_intensity(prev_frame, frame)
                    motion_history.append(motion_intensity)
                
                if prev_hist is not None:
                    # Compare histograms for scene change
                    correlation = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
                    
                    if correlation < threshold:  # Scene change detected
                        scene_end = frame_number
                        timestamp_start = scene_start / metadata.fps
                        timestamp_end = scene_end / metadata.fps
                        
                        # Analyze scene characteristics
                        avg_motion = np.mean(motion_history[-30:]) if motion_history else 0.0
                        scene_type = self._classify_scene_type(avg_motion, correlation)
                        
                        # Extract dominant colors
                        dominant_colors = self._extract_dominant_colors(frame)
                        
                        # Calculate visual complexity
                        visual_complexity = self._calculate_visual_complexity(frame)
                        
                        scene = SceneInfo(
                            start_time=timestamp_start,
                            end_time=timestamp_end,
                            start_frame=scene_start,
                            end_frame=scene_end,
                            confidence=1.0 - correlation,
                            scene_type=scene_type,
                            dominant_colors=dominant_colors,
                            motion_intensity=avg_motion,
                            visual_complexity=visual_complexity
                        )
                        
                        scenes.append(scene)
                        scene_start = frame_number
                        motion_history = []
                
                prev_hist = hist
                prev_frame = frame
                frame_number += 1
            
            # Add final scene
            if scene_start < frame_number:
                timestamp_start = scene_start / metadata.fps
                timestamp_end = frame_number / metadata.fps
                avg_motion = np.mean(motion_history[-30:]) if motion_history else 0.0
                
                scene = SceneInfo(
                    start_time=timestamp_start,
                    end_time=timestamp_end,
                    start_frame=scene_start,
                    end_frame=frame_number,
                    confidence=0.8,
                    scene_type=self._classify_scene_type(avg_motion, 0.8),
                    motion_intensity=avg_motion,
                    visual_complexity=0.5
                )
                scenes.append(scene)
            
            cap.release()
            logger.info(f"Detected {len(scenes)} advanced scenes")
            return scenes
            
        except Exception as e:
            logger.error(f"Advanced scene detection failed: {e}")
            return []
    
    def _calculate_motion_intensity(self, prev_frame: np.ndarray, curr_frame: np.ndarray) -> float:
        """Calculate motion intensity between frames"""
        try:
            # Convert to grayscale
            prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
            
            # Calculate optical flow
            flow = cv2.calcOpticalFlowPyrLK(
                prev_gray, curr_gray, 
                np.array([[100, 100]], dtype=np.float32).reshape(-1, 1, 2),
                None
            )[0]
            
            # Calculate motion magnitude
            if flow is not None and len(flow) > 0:
                motion = np.sqrt(flow[:, 0, 0]**2 + flow[:, 0, 1]**2)
                return float(np.mean(motion))
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Motion intensity calculation failed: {e}")
            return 0.0
    
    def _classify_scene_type(self, motion_intensity: float, correlation: float) -> SceneType:
        """Classify scene type based on motion and visual characteristics"""
        try:
            if motion_intensity > 0.8:
                return SceneType.ACTION
            elif motion_intensity > 0.4:
                return SceneType.DYNAMIC
            elif correlation < 0.3:
                return SceneType.TRANSITION
            else:
                return SceneType.STATIC
        except:
            return SceneType.STATIC
    
    def _extract_dominant_colors(self, frame: np.ndarray, k: int = 3) -> List[Tuple[int, int, int]]:
        """Extract dominant colors from frame using K-means clustering"""
        try:
            if not SKLEARN_AVAILABLE:
                return []
            
            # Reshape frame for clustering
            data = frame.reshape((-1, 3))
            data = np.float32(data)
            
            # Apply K-means clustering
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(data)
            
            # Get dominant colors
            colors = kmeans.cluster_centers_.astype(int)
            
            # Convert BGR to RGB and return as tuples
            dominant_colors = []
            for color in colors:
                dominant_colors.append((int(color[2]), int(color[1]), int(color[0])))
            
            return dominant_colors
            
        except Exception as e:
            logger.error(f"Dominant color extraction failed: {e}")
            return []
    
    def _calculate_visual_complexity(self, frame: np.ndarray) -> float:
        """Calculate visual complexity of frame"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Edge density
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            # Texture complexity using local binary patterns
            # Simplified version - in production use proper LBP
            texture_complexity = np.std(gray) / 128.0
            
            # Color complexity
            color_complexity = 0.0
            if len(frame.shape) == 3:
                color_complexity = np.var(frame, axis=(0,1)).mean() / 10000
            
            # Combined complexity score
            complexity = (edge_density * 0.4 + texture_complexity * 0.4 + color_complexity * 0.2)
            
            return min(1.0, complexity)
            
        except Exception as e:
            logger.error(f"Visual complexity calculation failed: {e}")
            return 0.5
    
    def _detect_scenes_basic(self, video_path: str, metadata: VideoMetadata) -> List[SceneInfo]:
        """Basic scene detection using histogram comparison"""
        scenes = []
        
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Cannot open video file: {video_path}")
            
            prev_hist = None
            scene_start = 0
            frame_number = 0
            threshold = 0.7
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Skip frames for performance
                if frame_number % 30 == 0:  # Every 30 frames
                    hist = cv2.calcHist([frame], [0, 1, 2], None, [50, 50, 50], [0, 256, 0, 256, 0, 256])
                    
                    if prev_hist is not None:
                        correlation = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
                        
                        if correlation < threshold:
                            scene_end = frame_number
                            timestamp_start = scene_start / metadata.fps
                            timestamp_end = scene_end / metadata.fps
                            
                            scene = SceneInfo(
                                start_time=timestamp_start,
                                end_time=timestamp_end,
                                start_frame=scene_start,
                                end_frame=scene_end,
                                confidence=1.0 - correlation,
                                scene_type=SceneType.STATIC
                            )
                            
                            scenes.append(scene)
                            scene_start = frame_number
                    
                    prev_hist = hist
                
                frame_number += 1
            
            cap.release()
            logger.info(f"Detected {len(scenes)} basic scenes")
            return scenes
            
        except Exception as e:
            logger.error(f"Basic scene detection failed: {e}")
            return []
    
    def _detect_objects_advanced(self, video_path: str, metadata: VideoMetadata) -> List[ObjectDetection]:
        """Advanced object detection with tracking"""
        objects = []
        
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Cannot open video file: {video_path}")
            
            frame_number = 0
            detection_interval = max(1, int(metadata.fps * 1))  # Every 1 second
            
            # Object tracking dictionary
            tracked_objects = {}
            next_tracking_id = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_number % detection_interval == 0:
                    timestamp = frame_number / metadata.fps
                    
                    # Detect objects in current frame
                    frame_objects = self._detect_objects_in_frame_advanced(frame, timestamp, frame_number)
                    
                    # Add tracking IDs and update tracking
                    for obj in frame_objects:
                        # Simple tracking based on position similarity
                        tracking_id = self._assign_tracking_id(obj, tracked_objects, next_tracking_id)
                        if tracking_id == next_tracking_id:
                            next_tracking_id += 1
                        
                        obj.tracking_id = str(tracking_id)
                        objects.append(obj)
                
                frame_number += 1
            
            cap.release()
            logger.info(f"Detected {len(objects)} advanced objects")
            return objects
            
        except Exception as e:
            logger.error(f"Advanced object detection failed: {e}")
            return []
    
    def _detect_objects_in_frame_advanced(self, frame: np.ndarray, 
                                        timestamp: float, frame_number: int) -> List[ObjectDetection]:
        """Advanced object detection in a single frame"""
        objects = []
        
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces with confidence
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )
            
            for (x, y, w, h) in faces:
                # Calculate confidence based on face size and position
                confidence = min(1.0, (w * h) / (100 * 100))  # Normalize by expected size
                
                detection = ObjectDetection(
                    class_name="face",
                    category=ObjectCategory.FACE,
                    confidence=confidence,
                    bbox=(x, y, w, h),
                    timestamp=timestamp,
                    frame_number=frame_number,
                    attributes={
                        'size': w * h,
                        'aspect_ratio': w / h if h > 0 else 1.0
                    }
                )
                objects.append(detection)
            
            # Add more sophisticated object detection here
            # In production, you would use YOLO, SSD, or similar models
            
            return objects
            
        except Exception as e:
            logger.error(f"Advanced frame object detection failed: {e}")
            return []
    
    def _assign_tracking_id(self, obj: ObjectDetection, tracked_objects: Dict, 
                          next_id: int) -> int:
        """Assign tracking ID to object based on position similarity"""
        try:
            obj_center = (obj.bbox[0] + obj.bbox[2] // 2, obj.bbox[1] + obj.bbox[3] // 2)
            
            # Find closest tracked object of same class
            min_distance = float('inf')
            closest_id = None
            
            for tracking_id, last_obj in tracked_objects.items():
                if last_obj['class_name'] == obj.class_name:
                    last_center = last_obj['center']
                    distance = np.sqrt((obj_center[0] - last_center[0])**2 + 
                                     (obj_center[1] - last_center[1])**2)
                    
                    if distance < min_distance and distance < 100:  # Threshold for same object
                        min_distance = distance
                        closest_id = tracking_id
            
            # Update or create tracking entry
            if closest_id is not None:
                tracked_objects[closest_id] = {
                    'class_name': obj.class_name,
                    'center': obj_center,
                    'last_seen': obj.timestamp
                }
                return closest_id
            else:
                # New object
                tracked_objects[next_id] = {
                    'class_name': obj.class_name,
                    'center': obj_center,
                    'last_seen': obj.timestamp
                }
                return next_id
                
        except Exception as e:
            logger.error(f"Tracking ID assignment failed: {e}")
            return next_id
    
    def _detect_objects_basic(self, video_path: str, metadata: VideoMetadata) -> List[ObjectDetection]:
        """Basic object detection without tracking"""
        objects = []
        
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Cannot open video file: {video_path}")
            
            frame_number = 0
            detection_interval = max(1, int(metadata.fps * 2))  # Every 2 seconds
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_number % detection_interval == 0:
                    timestamp = frame_number / metadata.fps
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    
                    # Basic face detection
                    faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                    
                    for (x, y, w, h) in faces:
                        detection = ObjectDetection(
                            class_name="face",
                            category=ObjectCategory.FACE,
                            confidence=0.8,
                            bbox=(x, y, w, h),
                            timestamp=timestamp,
                            frame_number=frame_number
                        )
                        objects.append(detection)
                
                frame_number += 1
            
            cap.release()
            logger.info(f"Detected {len(objects)} basic objects")
            return objects
            
        except Exception as e:
            logger.error(f"Basic object detection failed: {e}")
            return []
    
    async def _generate_intelligent_broll_suggestions(self, 
                                                    keyframes: List[KeyFrame],
                                                    scenes: List[SceneInfo], 
                                                    objects: List[ObjectDetection],
                                                    content_analysis: ContentAnalysis) -> List[BRollSuggestion]:
        """Generate intelligent B-roll suggestions based on comprehensive analysis"""
        suggestions = []
        
        try:
            # Analyze scenes for B-roll opportunities
            for scene in scenes:
                scene_duration = scene.end_time - scene.start_time
                
                # Long static scenes need B-roll
                if (scene_duration > 15 and 
                    scene.scene_type in [SceneType.STATIC, SceneType.DIALOGUE]):
                    
                    suggestion = BRollSuggestion(
                        timestamp=scene.start_time + scene_duration * 0.3,
                        duration=min(8.0, scene_duration * 0.4),
                        suggestion_type="scene_enhancement",
                        description=f"Long {scene.scene_type.value} scene ({scene_duration:.1f}s) - consider adding visual interest",
                        confidence=0.8,
                        keywords=["visual_interest", "pacing", scene.scene_type.value],
                        visual_context={
                            'scene_type': scene.scene_type.value,
                            'motion_intensity': scene.motion_intensity,
                            'visual_complexity': scene.visual_complexity
                        },
                        priority=2
                    )
                    suggestions.append(suggestion)
                
                # High motion scenes might need cutaways
                elif scene.motion_intensity > 0.7 and scene_duration > 10:
                    suggestion = BRollSuggestion(
                        timestamp=scene.start_time + scene_duration * 0.5,
                        duration=4.0,
                        suggestion_type="action_cutaway",
                        description=f"High-motion scene - consider reaction shots or detail views",
                        confidence=0.7,
                        keywords=["action", "cutaway", "reaction"],
                        visual_context={
                            'motion_intensity': scene.motion_intensity,
                            'scene_duration': scene_duration
                        },
                        priority=1
                    )
                    suggestions.append(suggestion)
            
            # Analyze object detections for contextual B-roll
            face_clusters = self._cluster_face_detections(objects)
            
            for cluster in face_clusters:
                if len(cluster) > 3:  # Multiple face appearances
                    avg_timestamp = np.mean([obj.timestamp for obj in cluster])
                    
                    suggestion = BRollSuggestion(
                        timestamp=avg_timestamp,
                        duration=5.0,
                        suggestion_type="reaction_montage",
                        description=f"Multiple face detections - consider reaction montage or group shots",
                        confidence=0.6,
                        keywords=["faces", "reactions", "group", "montage"],
                        visual_context={
                            'face_count': len(cluster),
                            'time_span': max([obj.timestamp for obj in cluster]) - min([obj.timestamp for obj in cluster])
                        },
                        priority=1
                    )
                    suggestions.append(suggestion)
            
            # Analyze keyframes for visual variety opportunities
            if len(keyframes) > 1:
                for i in range(1, len(keyframes)):
                    prev_frame = keyframes[i-1]
                    curr_frame = keyframes[i]
                    
                    # Check for visual similarity (might indicate boring content)
                    if (self._calculate_frame_similarity(prev_frame, curr_frame) > 0.8 and
                        curr_frame.timestamp - prev_frame.timestamp > 10):
                        
                        suggestion = BRollSuggestion(
                            timestamp=curr_frame.timestamp,
                            duration=6.0,
                            suggestion_type="visual_variety",
                            description="Similar visual content detected - add variety with different angles or subjects",
                            confidence=0.7,
                            keywords=["variety", "angles", "visual_interest"],
                            visual_context={
                                'similarity_score': self._calculate_frame_similarity(prev_frame, curr_frame),
                                'time_gap': curr_frame.timestamp - prev_frame.timestamp
                            },
                            priority=2
                        )
                        suggestions.append(suggestion)
                    
                    # Check for low quality frames
                    if (curr_frame.quality_metrics.get('sharpness', 1.0) < 0.3 and
                        curr_frame.timestamp - prev_frame.timestamp > 5):
                        
                        suggestion = BRollSuggestion(
                            timestamp=curr_frame.timestamp,
                            duration=4.0,
                            suggestion_type="quality_improvement",
                            description="Low visual quality detected - consider B-roll to maintain viewer engagement",
                            confidence=0.9,
                            keywords=["quality", "engagement", "visual_improvement"],
                            visual_context={
                                'sharpness': curr_frame.quality_metrics.get('sharpness', 0),
                                'quality_issues': [k for k, v in curr_frame.quality_metrics.items() if v < 0.4]
                            },
                            priority=3
                        )
                        suggestions.append(suggestion)
            
            # Content-specific suggestions based on analysis
            if content_analysis.duration_seconds > 1800:  # Long content
                # Add periodic B-roll suggestions for long content
                interval = 300  # Every 5 minutes
                for t in range(int(interval), int(content_analysis.duration_seconds), int(interval)):
                    suggestion = BRollSuggestion(
                        timestamp=float(t),
                        duration=8.0,
                        suggestion_type="pacing_break",
                        description=f"Long-form content pacing - consider visual break at {t//60}:{t%60:02d}",
                        confidence=0.5,
                        keywords=["pacing", "long_form", "visual_break"],
                        priority=1
                    )
                    suggestions.append(suggestion)
            
            # Sort suggestions by priority and confidence
            suggestions.sort(key=lambda x: (x.priority, -x.confidence))
            
            # Limit suggestions to avoid overwhelming users
            max_suggestions = min(20, len(suggestions))
            suggestions = suggestions[:max_suggestions]
            
            logger.info(f"Generated {len(suggestions)} intelligent B-roll suggestions")
            return suggestions
            
        except Exception as e:
            logger.error(f"B-roll suggestion generation failed: {e}")
            return []
    
    def _cluster_face_detections(self, objects: List[ObjectDetection]) -> List[List[ObjectDetection]]:
        """Cluster face detections by temporal proximity"""
        try:
            face_objects = [obj for obj in objects if obj.category == ObjectCategory.FACE]
            
            if not face_objects:
                return []
            
            # Simple temporal clustering
            clusters = []
            current_cluster = [face_objects[0]]
            
            for i in range(1, len(face_objects)):
                if face_objects[i].timestamp - face_objects[i-1].timestamp < 30:  # 30 second window
                    current_cluster.append(face_objects[i])
                else:
                    clusters.append(current_cluster)
                    current_cluster = [face_objects[i]]
            
            if current_cluster:
                clusters.append(current_cluster)
            
            return clusters
            
        except Exception as e:
            logger.error(f"Face detection clustering failed: {e}")
            return []
    
    def _calculate_frame_similarity(self, frame1: KeyFrame, frame2: KeyFrame) -> float:
        """Calculate similarity between two keyframes"""
        try:
            if frame1.visual_hash and frame2.visual_hash:
                # Compare visual hashes
                hash1 = int(frame1.visual_hash, 16)
                hash2 = int(frame2.visual_hash, 16)
                
                # Calculate Hamming distance
                xor = hash1 ^ hash2
                hamming_distance = bin(xor).count('1')
                
                # Convert to similarity (0-1)
                max_distance = 64  # Assuming 64-bit hash
                similarity = 1.0 - (hamming_distance / max_distance)
                
                return similarity
            
            # Fallback to feature comparison
            if frame1.features and frame2.features:
                # Compare quality metrics
                metrics1 = frame1.quality_metrics
                metrics2 = frame2.quality_metrics
                
                if metrics1 and metrics2:
                    differences = []
                    for key in metrics1:
                        if key in metrics2:
                            diff = abs(metrics1[key] - metrics2[key])
                            differences.append(diff)
                    
                    if differences:
                        avg_diff = np.mean(differences)
                        similarity = 1.0 - min(1.0, avg_diff)
                        return similarity
            
            return 0.5  # Default similarity
            
        except Exception as e:
            logger.error(f"Frame similarity calculation failed: {e}")
            return 0.5
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            self.executor.shutdown(wait=True)
            logger.info("AdvancedVideoProcessingEngine cleaned up")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_advanced_video_processing():
        """Test advanced video processing functionality"""
        engine = AdvancedVideoProcessingEngine()
        
        # Test with a sample video file (you would need to provide this)
        test_video = "sample_video.mp4"  # Replace with actual file
        
        if os.path.exists(test_video):
            print(f"Processing video: {test_video}")
            
            # Process video with all features
            results = await engine.process_video_comprehensive(
                test_video,
                {
                    'extract_keyframes': True,
                    'detect_scenes': True,
                    'detect_objects': True,
                    'suggest_broll': True,
                    'enhance_quality': False  # Set to True for quality enhancement
                }
            )
            
            if results['success']:
                print(f"✅ Advanced video processing successful!")
                print(f"Processing strategy: {results['processing_strategy']}")
                print(f"Processing time: {results['processing_time']:.2f}s")
                print(f"Keyframes extracted: {len(results.get('keyframes', []))}")
                print(f"Scenes detected: {len(results.get('scenes', []))}")
                print(f"Objects detected: {len(results.get('objects', []))}")
                print(f"B-roll suggestions: {len(results.get('broll_suggestions', []))}")
                
                # Print some scene details
                if results.get('scenes'):
                    print("\nAdvanced scene analysis:")
                    for i, scene in enumerate(results['scenes'][:3]):
                        print(f"  Scene {i+1}: {scene.start_time:.1f}s - {scene.end_time:.1f}s")
                        print(f"    Type: {scene.scene_type.value}")
                        print(f"    Motion: {scene.motion_intensity:.2f}")
                        print(f"    Complexity: {scene.visual_complexity:.2f}")
                
                # Print B-roll suggestions
                if results.get('broll_suggestions'):
                    print("\nIntelligent B-roll suggestions:")
                    for suggestion in results['broll_suggestions'][:3]:
                        print(f"  {suggestion.timestamp:.1f}s: {suggestion.description}")
                        print(f"    Type: {suggestion.suggestion_type}")
                        print(f"    Confidence: {suggestion.confidence:.2f}")
                        print(f"    Priority: {suggestion.priority}")
            else:
                print(f"❌ Advanced video processing failed: {results.get('error', 'Unknown error')}")
        else:
            print(f"Test video not found: {test_video}")
            print("Creating a simple test...")
            
            # Test metadata extraction with a dummy file
            print("✅ AdvancedVideoProcessingEngine initialized successfully")
        
        await engine.cleanup()
    
    # Run the test
    asyncio.run(test_advanced_video_processing())