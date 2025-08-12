"""
Media Asset Intelligence System
Scene detection, highlight extraction, visual analysis, and smart thumbnail generation
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import cv2
from PIL import Image
import imagehash
import face_recognition
from scenedetect import detect, ContentDetector, AdaptiveDetector
from moviepy.editor import VideoFileClip
import torch
import torchvision.transforms as transforms
from transformers import pipeline, BlipProcessor, BlipForConditionalGeneration
from collections import defaultdict, Counter
import json
import os
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

logger = logging.getLogger(__name__)


class MediaType(Enum):
    """Types of media assets"""
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    DOCUMENT = "document"
    PRESENTATION = "presentation"


class SceneType(Enum):
    """Types of scenes detected"""
    INTRO = "intro"
    OUTRO = "outro"
    TRANSITION = "transition"
    CONTENT = "content"
    TITLE = "title"
    CREDITS = "credits"
    INTERVIEW = "interview"
    PRESENTATION = "presentation"
    ACTION = "action"
    DIALOGUE = "dialogue"


@dataclass
class SceneInfo:
    """Information about a detected scene"""
    scene_id: str
    start_time: float
    end_time: float
    duration: float
    scene_type: SceneType
    confidence: float
    
    # Visual characteristics
    dominant_colors: List[Tuple[int, int, int]] = field(default_factory=list)
    brightness: float = 0.0
    contrast: float = 0.0
    sharpness: float = 0.0
    
    # Content detection
    detected_objects: List[Dict[str, float]] = field(default_factory=list)
    detected_faces: List[Dict[str, Any]] = field(default_factory=list)
    detected_text: List[str] = field(default_factory=list)
    detected_brands: List[str] = field(default_factory=list)
    
    # Scene characteristics
    motion_intensity: float = 0.0
    audio_intensity: float = 0.0
    speech_ratio: float = 0.0
    
    # Thumbnails
    thumbnail_path: Optional[str] = None
    key_frame_timestamps: List[float] = field(default_factory=list)


@dataclass
class HighlightSegment:
    """A highlight segment from the media"""
    segment_id: str
    start_time: float
    end_time: float
    score: float
    reason: str
    tags: List[str] = field(default_factory=list)
    thumbnail_path: Optional[str] = None
    
    # Engagement metrics
    visual_interest: float = 0.0
    audio_peaks: float = 0.0
    motion_score: float = 0.0
    face_time: float = 0.0
    
    # Content
    transcript_excerpt: Optional[str] = None
    detected_emotions: List[str] = field(default_factory=list)


@dataclass
class MediaAssetMetadata:
    """Comprehensive metadata for media assets"""
    asset_id: str
    file_path: str
    media_type: MediaType
    
    # Basic properties
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    bitrate: Optional[int] = None
    codec: Optional[str] = None
    
    # Detected scenes
    scenes: List[SceneInfo] = field(default_factory=list)
    
    # Highlights
    highlights: List[HighlightSegment] = field(default_factory=list)
    auto_chapters: List[Dict[str, Any]] = field(default_factory=list)
    
    # Visual analysis
    dominant_colors: List[Tuple[int, int, int]] = field(default_factory=list)
    color_palette: List[str] = field(default_factory=list)
    visual_style: Optional[str] = None
    quality_score: float = 0.0
    
    # Object and face detection
    unique_faces: int = 0
    face_tracks: List[Dict[str, Any]] = field(default_factory=list)
    detected_objects: Dict[str, int] = field(default_factory=dict)
    detected_brands: List[str] = field(default_factory=list)
    
    # Text detection
    detected_text: List[Dict[str, Any]] = field(default_factory=list)
    captions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Smart thumbnails
    hero_thumbnail: Optional[str] = None
    timeline_thumbnails: List[str] = field(default_factory=list)
    highlight_thumbnails: List[str] = field(default_factory=list)
    
    # Recommendations
    suggested_edits: List[Dict[str, Any]] = field(default_factory=list)
    suggested_clips: List[Dict[str, Any]] = field(default_factory=list)
    viral_potential: float = 0.0


class MediaAssetIntelligence:
    """Advanced media asset analysis and intelligence system"""
    
    def __init__(self, db: Session = None):
        self.db = db
        
        # Initialize ML models
        self._init_models()
        
        # Initialize processors
        self._init_processors()
        
        # Cache for processed assets
        self.asset_cache = {}
        
        # Configuration
        self.config = {
            'scene_threshold': 0.3,
            'highlight_threshold': 0.7,
            'face_confidence': 0.8,
            'object_confidence': 0.5,
            'thumbnail_count': 10,
            'highlight_duration': 15.0  # seconds
        }
    
    def _init_models(self):
        """Initialize ML models for analysis"""
        try:
            # Object detection
            self.object_detector = pipeline(
                "object-detection",
                model="facebook/detr-resnet-50"
            )
            
            # Image captioning
            self.caption_processor = BlipProcessor.from_pretrained(
                "Salesforce/blip-image-captioning-base"
            )
            self.caption_model = BlipForConditionalGeneration.from_pretrained(
                "Salesforce/blip-image-captioning-base"
            )
            
            # Emotion detection
            self.emotion_detector = pipeline(
                "image-classification",
                model="dima806/facial_emotions_image_detection"
            )
            
            # Scene classification
            self.scene_classifier = pipeline(
                "image-classification",
                model="google/vit-base-patch16-224"
            )
            
            # OCR for text detection
            try:
                import easyocr
                self.ocr_reader = easyocr.Reader(['en'])
            except:
                logger.warning("EasyOCR not available, text detection disabled")
                self.ocr_reader = None
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            self.object_detector = None
            self.caption_model = None
            self.emotion_detector = None
            self.scene_classifier = None
    
    def _init_processors(self):
        """Initialize video and image processors"""
        self.scene_detector = ContentDetector()
        self.adaptive_detector = AdaptiveDetector()
        
        # Image transforms for feature extraction
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    
    async def analyze_media_asset(
        self,
        file_path: str,
        asset_id: str,
        media_type: MediaType = MediaType.VIDEO,
        deep_analysis: bool = True,
        extract_highlights: bool = True
    ) -> MediaAssetMetadata:
        """
        Perform comprehensive media asset analysis
        
        Args:
            file_path: Path to the media file
            asset_id: Unique identifier for the asset
            media_type: Type of media asset
            deep_analysis: Whether to perform deep analysis
            extract_highlights: Whether to extract highlights
        
        Returns:
            MediaAssetMetadata with all extracted features
        """
        
        metadata = MediaAssetMetadata(
            asset_id=asset_id,
            file_path=file_path,
            media_type=media_type
        )
        
        if media_type == MediaType.VIDEO:
            # Extract video properties
            metadata = await self._extract_video_properties(file_path, metadata)
            
            # Detect scenes
            metadata.scenes = await self._detect_scenes(file_path)
            
            # Extract visual features
            metadata = await self._extract_visual_features(file_path, metadata)
            
            if deep_analysis:
                # Detect objects and faces
                metadata = await self._detect_objects_and_faces(file_path, metadata)
                
                # Detect text and brands
                metadata = await self._detect_text_and_brands(file_path, metadata)
                
                # Generate smart thumbnails
                metadata = await self._generate_smart_thumbnails(file_path, metadata)
            
            if extract_highlights:
                # Extract highlights
                metadata.highlights = await self._extract_highlights(file_path, metadata)
                
                # Generate auto-chapters
                metadata.auto_chapters = await self._generate_chapters(metadata)
                
                # Calculate viral potential
                metadata.viral_potential = await self._calculate_viral_potential(metadata)
                
                # Generate edit suggestions
                metadata.suggested_edits = await self._generate_edit_suggestions(metadata)
        
        elif media_type == MediaType.IMAGE:
            # Analyze static image
            metadata = await self._analyze_image(file_path, metadata)
        
        # Cache the results
        self.asset_cache[asset_id] = metadata
        
        return metadata
    
    async def _extract_video_properties(self, file_path: str, metadata: MediaAssetMetadata) -> MediaAssetMetadata:
        """Extract basic video properties"""
        try:
            clip = VideoFileClip(file_path)
            
            metadata.duration = clip.duration
            metadata.width = clip.w
            metadata.height = clip.h
            metadata.fps = clip.fps
            
            # Calculate bitrate if possible
            file_size = os.path.getsize(file_path)
            if metadata.duration > 0:
                metadata.bitrate = int((file_size * 8) / metadata.duration)
            
            clip.close()
            
        except Exception as e:
            logger.error(f"Error extracting video properties: {e}")
        
        return metadata
    
    async def _detect_scenes(self, video_path: str, threshold: float = None) -> List[SceneInfo]:
        """Detect scenes in video"""
        threshold = threshold or self.config['scene_threshold']
        scenes = []
        
        try:
            from scenedetect import VideoManager, SceneManager
            
            video_manager = VideoManager([video_path])
            scene_manager = SceneManager()
            scene_manager.add_detector(ContentDetector(threshold=threshold))
            
            video_manager.start()
            scene_manager.detect_scenes(frame_source=video_manager)
            scene_list = scene_manager.get_scene_list()
            video_manager.release()
            
            # Process detected scenes
            for i, (start_time, end_time) in enumerate(scene_list):
                scene_info = SceneInfo(
                    scene_id=f"scene_{i}",
                    start_time=start_time.get_seconds(),
                    end_time=end_time.get_seconds(),
                    duration=end_time.get_seconds() - start_time.get_seconds(),
                    scene_type=SceneType.CONTENT,
                    confidence=0.8
                )
                
                # Classify scene type
                scene_info.scene_type = await self._classify_scene_type(
                    video_path,
                    scene_info.start_time,
                    scene_info.end_time
                )
                
                scenes.append(scene_info)
            
        except Exception as e:
            logger.error(f"Scene detection error: {e}")
        
        return scenes
    
    async def _classify_scene_type(self, video_path: str, start_time: float, end_time: float) -> SceneType:
        """Classify the type of scene"""
        # Extract frame from middle of scene
        mid_time = (start_time + end_time) / 2
        
        try:
            cap = cv2.VideoCapture(video_path)
            cap.set(cv2.CAP_PROP_POS_MSEC, mid_time * 1000)
            ret, frame = cap.read()
            cap.release()
            
            if ret and self.scene_classifier:
                # Convert to PIL Image
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                
                # Classify scene
                results = self.scene_classifier(pil_image)
                
                # Map classification to scene type
                top_label = results[0]['label'].lower() if results else ""
                
                if 'interview' in top_label or 'person' in top_label:
                    return SceneType.INTERVIEW
                elif 'presentation' in top_label or 'slide' in top_label:
                    return SceneType.PRESENTATION
                elif 'action' in top_label or 'sport' in top_label:
                    return SceneType.ACTION
                elif 'title' in top_label or 'text' in top_label:
                    return SceneType.TITLE
                else:
                    return SceneType.CONTENT
            
        except Exception as e:
            logger.error(f"Scene classification error: {e}")
        
        return SceneType.CONTENT
    
    async def _extract_visual_features(self, video_path: str, metadata: MediaAssetMetadata) -> MediaAssetMetadata:
        """Extract visual features from video"""
        try:
            cap = cv2.VideoCapture(video_path)
            
            # Sample frames throughout video
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            sample_interval = max(1, frame_count // 30)  # Sample 30 frames
            
            colors = []
            brightness_values = []
            contrast_values = []
            sharpness_values = []
            
            for i in range(0, frame_count, sample_interval):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                
                if not ret:
                    continue
                
                # Extract dominant colors
                dominant = self._get_dominant_colors(frame)
                colors.extend(dominant)
                
                # Calculate brightness
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                brightness_values.append(np.mean(gray))
                
                # Calculate contrast
                contrast_values.append(np.std(gray))
                
                # Calculate sharpness (using Laplacian)
                laplacian = cv2.Laplacian(gray, cv2.CV_64F)
                sharpness_values.append(np.var(laplacian))
            
            cap.release()
            
            # Aggregate features
            if colors:
                # Get most common colors
                color_counter = Counter(colors)
                metadata.dominant_colors = [color for color, _ in color_counter.most_common(5)]
                
                # Convert to hex palette
                metadata.color_palette = [
                    '#{:02x}{:02x}{:02x}'.format(r, g, b)
                    for r, g, b in metadata.dominant_colors
                ]
            
            # Calculate quality score based on technical metrics
            if brightness_values and contrast_values and sharpness_values:
                avg_brightness = np.mean(brightness_values)
                avg_contrast = np.mean(contrast_values)
                avg_sharpness = np.mean(sharpness_values)
                
                # Normalize and combine metrics
                brightness_score = min(1.0, avg_brightness / 128)  # Optimal around 128
                contrast_score = min(1.0, avg_contrast / 50)  # Good contrast around 50
                sharpness_score = min(1.0, avg_sharpness / 1000)  # Sharp images > 1000
                
                metadata.quality_score = (brightness_score + contrast_score + sharpness_score) / 3
            
            # Determine visual style
            metadata.visual_style = self._determine_visual_style(metadata)
            
        except Exception as e:
            logger.error(f"Visual feature extraction error: {e}")
        
        return metadata
    
    def _get_dominant_colors(self, frame: np.ndarray, k: int = 5) -> List[Tuple[int, int, int]]:
        """Extract dominant colors from frame using k-means"""
        try:
            # Resize for faster processing
            small_frame = cv2.resize(frame, (100, 100))
            
            # Reshape to list of pixels
            pixels = small_frame.reshape(-1, 3)
            
            # Apply k-means clustering
            from sklearn.cluster import KMeans
            kmeans = KMeans(n_clusters=k, random_state=42)
            kmeans.fit(pixels)
            
            # Get cluster centers (dominant colors)
            colors = kmeans.cluster_centers_.astype(int)
            
            return [tuple(color) for color in colors]
        
        except Exception as e:
            logger.error(f"Color extraction error: {e}")
            return []
    
    def _determine_visual_style(self, metadata: MediaAssetMetadata) -> str:
        """Determine the visual style of the video"""
        if not metadata.dominant_colors:
            return "unknown"
        
        # Analyze color palette
        colors = metadata.dominant_colors[:3]
        
        # Calculate average brightness
        avg_brightness = np.mean([sum(color) / 3 for color in colors])
        
        # Calculate color variance
        color_variance = np.std([color for color_tuple in colors for color in color_tuple])
        
        # Determine style based on characteristics
        if avg_brightness > 200:
            if color_variance < 30:
                return "minimal_light"
            else:
                return "bright_vibrant"
        elif avg_brightness < 100:
            if color_variance < 30:
                return "dark_moody"
            else:
                return "dark_contrast"
        else:
            if color_variance < 30:
                return "muted_neutral"
            else:
                return "balanced_natural"
    
    async def _detect_objects_and_faces(self, video_path: str, metadata: MediaAssetMetadata) -> MediaAssetMetadata:
        """Detect objects and faces in video"""
        try:
            cap = cv2.VideoCapture(video_path)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            sample_interval = max(1, frame_count // 20)  # Sample 20 frames
            
            all_objects = defaultdict(int)
            face_encodings = []
            face_tracks = []
            
            for i in range(0, frame_count, sample_interval):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                
                if not ret:
                    continue
                
                # Convert to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Detect objects
                if self.object_detector:
                    pil_image = Image.fromarray(frame_rgb)
                    objects = self.object_detector(pil_image)
                    
                    for obj in objects:
                        if obj['score'] > self.config['object_confidence']:
                            all_objects[obj['label']] += 1
                
                # Detect faces
                face_locations = face_recognition.face_locations(frame_rgb)
                face_encodings_frame = face_recognition.face_encodings(frame_rgb, face_locations)
                
                for encoding, location in zip(face_encodings_frame, face_locations):
                    # Check if this is a new face
                    is_new_face = True
                    for known_encoding in face_encodings:
                        if face_recognition.compare_faces([known_encoding], encoding, tolerance=0.6)[0]:
                            is_new_face = False
                            break
                    
                    if is_new_face:
                        face_encodings.append(encoding)
                        
                        # Create face track
                        face_tracks.append({
                            'face_id': f"face_{len(face_encodings)}",
                            'first_appearance': i / cap.get(cv2.CAP_PROP_FPS),
                            'appearances': [(i / cap.get(cv2.CAP_PROP_FPS), location)]
                        })
            
            cap.release()
            
            # Update metadata
            metadata.detected_objects = dict(all_objects)
            metadata.unique_faces = len(face_encodings)
            metadata.face_tracks = face_tracks
            
        except Exception as e:
            logger.error(f"Object/face detection error: {e}")
        
        return metadata
    
    async def _detect_text_and_brands(self, video_path: str, metadata: MediaAssetMetadata) -> MediaAssetMetadata:
        """Detect text and brand logos in video"""
        if not self.ocr_reader:
            return metadata
        
        try:
            cap = cv2.VideoCapture(video_path)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            sample_interval = max(1, frame_count // 10)  # Sample 10 frames
            
            all_text = []
            detected_brands = set()
            
            # Common brand keywords to look for
            brand_keywords = [
                'nike', 'adidas', 'apple', 'google', 'microsoft', 'amazon',
                'facebook', 'meta', 'twitter', 'instagram', 'youtube',
                'coca-cola', 'pepsi', 'mcdonalds', 'starbucks'
            ]
            
            for i in range(0, frame_count, sample_interval):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                
                if not ret:
                    continue
                
                # OCR text detection
                results = self.ocr_reader.readtext(frame)
                
                for (bbox, text, confidence) in results:
                    if confidence > 0.5:
                        all_text.append({
                            'text': text,
                            'timestamp': i / cap.get(cv2.CAP_PROP_FPS),
                            'confidence': confidence,
                            'bbox': bbox
                        })
                        
                        # Check for brand mentions
                        text_lower = text.lower()
                        for brand in brand_keywords:
                            if brand in text_lower:
                                detected_brands.add(brand.title())
            
            cap.release()
            
            # Update metadata
            metadata.detected_text = all_text
            metadata.detected_brands = list(detected_brands)
            
        except Exception as e:
            logger.error(f"Text/brand detection error: {e}")
        
        return metadata
    
    async def _extract_highlights(self, video_path: str, metadata: MediaAssetMetadata) -> List[HighlightSegment]:
        """Extract highlight segments from video"""
        highlights = []
        
        try:
            # Analyze scenes for highlight potential
            scene_scores = []
            
            for scene in metadata.scenes:
                score = 0.0
                
                # Score based on scene type
                if scene.scene_type in [SceneType.ACTION, SceneType.INTERVIEW]:
                    score += 0.3
                
                # Score based on motion intensity
                score += scene.motion_intensity * 0.2
                
                # Score based on face detection
                if scene.detected_faces:
                    score += 0.2
                
                # Score based on audio peaks
                score += scene.audio_intensity * 0.2
                
                # Score based on scene duration (prefer medium-length scenes)
                if 5 <= scene.duration <= 30:
                    score += 0.1
                
                scene_scores.append((scene, score))
            
            # Sort by score and select top highlights
            scene_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Create highlight segments
            for scene, score in scene_scores[:5]:  # Top 5 highlights
                if score >= self.config['highlight_threshold']:
                    highlight = HighlightSegment(
                        segment_id=f"highlight_{scene.scene_id}",
                        start_time=scene.start_time,
                        end_time=min(scene.end_time, scene.start_time + self.config['highlight_duration']),
                        score=score,
                        reason=self._get_highlight_reason(scene, score),
                        tags=self._get_highlight_tags(scene)
                    )
                    
                    # Extract thumbnail for highlight
                    highlight.thumbnail_path = await self._extract_frame(
                        video_path,
                        scene.start_time + (scene.duration / 2)
                    )
                    
                    highlights.append(highlight)
            
            # Find peak moments
            peak_highlights = await self._find_peak_moments(video_path, metadata)
            highlights.extend(peak_highlights)
            
            # Sort by timestamp
            highlights.sort(key=lambda x: x.start_time)
            
        except Exception as e:
            logger.error(f"Highlight extraction error: {e}")
        
        return highlights
    
    def _get_highlight_reason(self, scene: SceneInfo, score: float) -> str:
        """Generate reason for highlight selection"""
        reasons = []
        
        if scene.scene_type == SceneType.ACTION:
            reasons.append("High action content")
        elif scene.scene_type == SceneType.INTERVIEW:
            reasons.append("Interview segment")
        
        if scene.motion_intensity > 0.7:
            reasons.append("High motion")
        
        if scene.detected_faces:
            reasons.append(f"{len(scene.detected_faces)} faces detected")
        
        if scene.audio_intensity > 0.7:
            reasons.append("Audio peak")
        
        return " | ".join(reasons) if reasons else f"Score: {score:.2f}"
    
    def _get_highlight_tags(self, scene: SceneInfo) -> List[str]:
        """Generate tags for highlight"""
        tags = []
        
        tags.append(scene.scene_type.value)
        
        if scene.motion_intensity > 0.7:
            tags.append("dynamic")
        elif scene.motion_intensity < 0.3:
            tags.append("static")
        
        if scene.detected_faces:
            tags.append("people")
        
        if scene.detected_text:
            tags.append("text_overlay")
        
        return tags
    
    async def _find_peak_moments(self, video_path: str, metadata: MediaAssetMetadata) -> List[HighlightSegment]:
        """Find peak moments based on audio/visual intensity"""
        peak_highlights = []
        
        # This would analyze audio waveform and visual changes
        # to find moments of high intensity
        # Placeholder implementation
        
        return peak_highlights
    
    async def _generate_smart_thumbnails(self, video_path: str, metadata: MediaAssetMetadata) -> MediaAssetMetadata:
        """Generate smart thumbnails for the video"""
        try:
            # Generate hero thumbnail (most representative frame)
            hero_time = await self._find_hero_frame(video_path, metadata)
            metadata.hero_thumbnail = await self._extract_frame(video_path, hero_time, quality='high')
            
            # Generate timeline thumbnails
            if metadata.duration:
                interval = metadata.duration / self.config['thumbnail_count']
                for i in range(self.config['thumbnail_count']):
                    timestamp = i * interval
                    thumb_path = await self._extract_frame(video_path, timestamp)
                    if thumb_path:
                        metadata.timeline_thumbnails.append(thumb_path)
            
            # Generate highlight thumbnails
            for highlight in metadata.highlights[:5]:
                thumb_time = (highlight.start_time + highlight.end_time) / 2
                thumb_path = await self._extract_frame(video_path, thumb_time, quality='high')
                if thumb_path:
                    metadata.highlight_thumbnails.append(thumb_path)
            
        except Exception as e:
            logger.error(f"Thumbnail generation error: {e}")
        
        return metadata
    
    async def _find_hero_frame(self, video_path: str, metadata: MediaAssetMetadata) -> float:
        """Find the best frame to represent the video"""
        best_time = metadata.duration / 2 if metadata.duration else 0
        best_score = 0
        
        try:
            # Analyze key frames from scenes
            for scene in metadata.scenes:
                # Skip intro/outro
                if scene.scene_type in [SceneType.INTRO, SceneType.OUTRO, SceneType.CREDITS]:
                    continue
                
                # Calculate scene score
                score = 0
                
                # Prefer scenes with faces
                if scene.detected_faces:
                    score += 0.3
                
                # Prefer good visual quality
                score += scene.sharpness * 0.2
                
                # Prefer scenes with good composition (using rule of thirds)
                score += 0.2
                
                # Prefer middle scenes
                if metadata.duration:
                    distance_from_middle = abs((scene.start_time + scene.end_time) / 2 - metadata.duration / 2)
                    middle_score = 1 - (distance_from_middle / metadata.duration)
                    score += middle_score * 0.3
                
                if score > best_score:
                    best_score = score
                    best_time = (scene.start_time + scene.end_time) / 2
        
        except Exception as e:
            logger.error(f"Hero frame detection error: {e}")
        
        return best_time
    
    async def _extract_frame(self, video_path: str, timestamp: float, quality: str = 'normal') -> Optional[str]:
        """Extract a frame from video at given timestamp"""
        try:
            cap = cv2.VideoCapture(video_path)
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # Generate output path
                output_dir = Path("thumbnails") / Path(video_path).stem
                output_dir.mkdir(parents=True, exist_ok=True)
                
                filename = f"thumb_{int(timestamp*1000)}.jpg"
                output_path = output_dir / filename
                
                # Adjust quality
                if quality == 'high':
                    cv2.imwrite(str(output_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                else:
                    cv2.imwrite(str(output_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                
                return str(output_path)
        
        except Exception as e:
            logger.error(f"Frame extraction error: {e}")
        
        return None
    
    async def _generate_chapters(self, metadata: MediaAssetMetadata) -> List[Dict[str, Any]]:
        """Generate auto-chapters based on scene analysis"""
        chapters = []
        
        try:
            # Group similar consecutive scenes
            current_chapter = None
            
            for scene in metadata.scenes:
                if not current_chapter:
                    current_chapter = {
                        'title': self._generate_chapter_title(scene),
                        'start_time': scene.start_time,
                        'end_time': scene.end_time,
                        'scenes': [scene.scene_id]
                    }
                elif scene.scene_type == SceneType(current_chapter.get('type', scene.scene_type.value)):
                    # Extend current chapter
                    current_chapter['end_time'] = scene.end_time
                    current_chapter['scenes'].append(scene.scene_id)
                else:
                    # Save current chapter and start new one
                    if current_chapter['end_time'] - current_chapter['start_time'] >= 30:  # Min 30 seconds
                        chapters.append(current_chapter)
                    
                    current_chapter = {
                        'title': self._generate_chapter_title(scene),
                        'start_time': scene.start_time,
                        'end_time': scene.end_time,
                        'scenes': [scene.scene_id],
                        'type': scene.scene_type.value
                    }
            
            # Add last chapter
            if current_chapter and current_chapter['end_time'] - current_chapter['start_time'] >= 30:
                chapters.append(current_chapter)
            
        except Exception as e:
            logger.error(f"Chapter generation error: {e}")
        
        return chapters
    
    def _generate_chapter_title(self, scene: SceneInfo) -> str:
        """Generate title for a chapter"""
        titles = {
            SceneType.INTRO: "Introduction",
            SceneType.OUTRO: "Conclusion",
            SceneType.INTERVIEW: "Interview Segment",
            SceneType.PRESENTATION: "Presentation",
            SceneType.ACTION: "Action Sequence",
            SceneType.DIALOGUE: "Discussion",
            SceneType.TITLE: "Title Card",
            SceneType.CREDITS: "Credits",
            SceneType.CONTENT: "Main Content"
        }
        
        return titles.get(scene.scene_type, "Chapter")
    
    async def _calculate_viral_potential(self, metadata: MediaAssetMetadata) -> float:
        """Calculate viral potential score"""
        score = 0.0
        
        try:
            # Duration factor (optimal 1-3 minutes)
            if metadata.duration:
                if 60 <= metadata.duration <= 180:
                    score += 0.2
                elif 30 <= metadata.duration <= 300:
                    score += 0.1
            
            # Visual quality
            score += metadata.quality_score * 0.15
            
            # Faces increase engagement
            if metadata.unique_faces > 0:
                score += min(0.2, metadata.unique_faces * 0.05)
            
            # Highlights quality
            if metadata.highlights:
                avg_highlight_score = np.mean([h.score for h in metadata.highlights])
                score += avg_highlight_score * 0.2
            
            # Scene variety
            scene_types = set(s.scene_type for s in metadata.scenes)
            variety_score = min(1.0, len(scene_types) / 5)
            score += variety_score * 0.1
            
            # Brand presence (can increase reach)
            if metadata.detected_brands:
                score += 0.1
            
            # Text overlays (good for social media)
            if metadata.detected_text:
                score += 0.05
            
            # Color vibrancy
            if metadata.visual_style in ['bright_vibrant', 'balanced_natural']:
                score += 0.1
            
        except Exception as e:
            logger.error(f"Viral potential calculation error: {e}")
        
        return min(1.0, score)
    
    async def _generate_edit_suggestions(self, metadata: MediaAssetMetadata) -> List[Dict[str, Any]]:
        """Generate video editing suggestions"""
        suggestions = []
        
        try:
            # Check for long scenes that could be trimmed
            for scene in metadata.scenes:
                if scene.duration > 60 and scene.motion_intensity < 0.3:
                    suggestions.append({
                        'type': 'trim',
                        'scene_id': scene.scene_id,
                        'reason': 'Long static scene could be shortened',
                        'start_time': scene.start_time,
                        'end_time': scene.end_time,
                        'suggested_duration': 30
                    })
            
            # Suggest removing low-quality segments
            for scene in metadata.scenes:
                if scene.sharpness < 0.3 or scene.brightness < 0.2:
                    suggestions.append({
                        'type': 'quality',
                        'scene_id': scene.scene_id,
                        'reason': 'Low visual quality',
                        'start_time': scene.start_time,
                        'end_time': scene.end_time,
                        'fix': 'Consider color correction or removal'
                    })
            
            # Suggest highlight compilation
            if len(metadata.highlights) >= 3:
                suggestions.append({
                    'type': 'compilation',
                    'reason': 'Create highlight reel',
                    'highlights': [h.segment_id for h in metadata.highlights[:5]],
                    'estimated_duration': sum(h.end_time - h.start_time for h in metadata.highlights[:5])
                })
            
            # Suggest adding text overlays
            if not metadata.detected_text and metadata.media_type == MediaType.VIDEO:
                suggestions.append({
                    'type': 'enhancement',
                    'reason': 'Add text overlays for key points',
                    'locations': [h.start_time for h in metadata.highlights[:3]]
                })
            
            # Suggest optimal duration for platform
            if metadata.duration:
                if metadata.duration > 600:  # > 10 minutes
                    suggestions.append({
                        'type': 'platform_optimization',
                        'platform': 'instagram',
                        'reason': 'Create 60-second version for Instagram Reels',
                        'suggested_clips': [h.segment_id for h in metadata.highlights[:2]]
                    })
                
                if metadata.duration > 180:  # > 3 minutes
                    suggestions.append({
                        'type': 'platform_optimization',
                        'platform': 'tiktok',
                        'reason': 'Create 30-second version for TikTok',
                        'suggested_clips': [metadata.highlights[0].segment_id] if metadata.highlights else []
                    })
            
        except Exception as e:
            logger.error(f"Edit suggestion generation error: {e}")
        
        return suggestions
    
    async def _analyze_image(self, image_path: str, metadata: MediaAssetMetadata) -> MediaAssetMetadata:
        """Analyze a static image"""
        try:
            # Load image
            image = Image.open(image_path)
            image_np = np.array(image)
            
            # Basic properties
            metadata.width = image.width
            metadata.height = image.height
            
            # Extract dominant colors
            colors = self._get_dominant_colors(image_np)
            metadata.dominant_colors = colors
            metadata.color_palette = [
                '#{:02x}{:02x}{:02x}'.format(r, g, b)
                for r, g, b in colors
            ]
            
            # Detect objects
            if self.object_detector:
                objects = self.object_detector(image)
                metadata.detected_objects = {
                    obj['label']: 1
                    for obj in objects
                    if obj['score'] > self.config['object_confidence']
                }
            
            # Detect faces
            face_locations = face_recognition.face_locations(image_np)
            metadata.unique_faces = len(face_locations)
            
            # Generate caption
            if self.caption_model:
                inputs = self.caption_processor(image, return_tensors="pt")
                out = self.caption_model.generate(**inputs)
                caption = self.caption_processor.decode(out[0], skip_special_tokens=True)
                metadata.captions = [{'text': caption, 'confidence': 0.9}]
            
            # OCR text detection
            if self.ocr_reader:
                results = self.ocr_reader.readtext(image_np)
                metadata.detected_text = [
                    {'text': text, 'confidence': conf}
                    for _, text, conf in results
                    if conf > 0.5
                ]
            
            # Calculate quality score
            metadata.quality_score = self._calculate_image_quality(image_np)
            
        except Exception as e:
            logger.error(f"Image analysis error: {e}")
        
        return metadata
    
    def _calculate_image_quality(self, image: np.ndarray) -> float:
        """Calculate image quality score"""
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
            
            # Calculate sharpness using Laplacian
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            sharpness = np.var(laplacian)
            
            # Normalize sharpness score
            sharpness_score = min(1.0, sharpness / 1000)
            
            # Calculate contrast
            contrast = np.std(gray)
            contrast_score = min(1.0, contrast / 80)
            
            # Calculate brightness
            brightness = np.mean(gray)
            # Optimal brightness around 128
            brightness_score = 1.0 - abs(brightness - 128) / 128
            
            # Combine scores
            quality = (sharpness_score * 0.4 + contrast_score * 0.3 + brightness_score * 0.3)
            
            return float(quality)
        
        except Exception as e:
            logger.error(f"Quality calculation error: {e}")
            return 0.5
    
    async def compare_videos(self, video_paths: List[str]) -> Dict[str, Any]:
        """Compare multiple videos for similarity and differences"""
        comparison = {
            'videos': [],
            'similarity_matrix': [],
            'common_elements': {},
            'unique_elements': {},
            'recommendations': []
        }
        
        # Analyze each video
        for path in video_paths:
            asset_id = Path(path).stem
            metadata = await self.analyze_media_asset(path, asset_id, MediaType.VIDEO, deep_analysis=False)
            comparison['videos'].append({
                'path': path,
                'asset_id': asset_id,
                'duration': metadata.duration,
                'scenes': len(metadata.scenes),
                'quality': metadata.quality_score
            })
        
        # Calculate similarity matrix
        # This would compare visual features, scene structure, etc.
        
        return comparison
    
    async def generate_video_summary(self, video_path: str, output_path: str, duration: int = 60) -> bool:
        """Generate a video summary/trailer"""
        try:
            # Analyze video
            asset_id = Path(video_path).stem
            metadata = await self.analyze_media_asset(video_path, asset_id)
            
            if not metadata.highlights:
                logger.error("No highlights found for summary generation")
                return False
            
            # Select best highlights for target duration
            selected_highlights = []
            current_duration = 0
            
            for highlight in metadata.highlights:
                segment_duration = highlight.end_time - highlight.start_time
                if current_duration + segment_duration <= duration:
                    selected_highlights.append(highlight)
                    current_duration += segment_duration
            
            if not selected_highlights:
                return False
            
            # Use moviepy to create summary video
            from moviepy.editor import VideoFileClip, concatenate_videoclips
            
            clips = []
            original_clip = VideoFileClip(video_path)
            
            for highlight in selected_highlights:
                clip = original_clip.subclip(highlight.start_time, highlight.end_time)
                clips.append(clip)
            
            # Concatenate clips
            final_clip = concatenate_videoclips(clips)
            
            # Write output
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac'
            )
            
            # Clean up
            original_clip.close()
            final_clip.close()
            
            return True
        
        except Exception as e:
            logger.error(f"Summary generation error: {e}")
            return False


# Global instance
media_intelligence = MediaAssetIntelligence()