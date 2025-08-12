#!/usr/bin/env python3
"""
Visual Content Analysis and Scene Understanding System
Implements object detection, scene description, visual search, face detection,
image similarity, and comprehensive visual content analysis
"""

import asyncio
import logging
import os
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
from enum import Enum
import numpy as np
from pathlib import Path
import hashlib
from collections import defaultdict, Counter

# Computer Vision
import cv2
from PIL import Image, ImageDraw, ImageFont
import torch
import torchvision
from torchvision import transforms
from torchvision.models.detection import fasterrcnn_resnet50_fpn
from torchvision.models import resnet50, efficientnet_b0

# Object Detection
from ultralytics import YOLO
import supervision as sv

# Face Detection and Recognition
import face_recognition
import mediapipe as mp

# Scene Understanding
from transformers import (
    BlipProcessor, BlipForConditionalGeneration,
    CLIPProcessor, CLIPModel,
    DetrImageProcessor, DetrForObjectDetection,
    ViTImageProcessor, ViTForImageClassification,
    pipeline
)

# OCR
import pytesseract
import easyocr

# Image Processing
from skimage import io, transform, feature, color
from skimage.metrics import structural_similarity as ssim
import albumentations as A

# Video Processing
import moviepy.editor as mpe
from decord import VideoReader, cpu

# Visualization
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import seaborn as sns

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Types of visual content"""
    IMAGE = "image"
    VIDEO = "video"
    FRAME = "frame"
    SCREENSHOT = "screenshot"
    DOCUMENT = "document"
    DIAGRAM = "diagram"


class DetectionType(Enum):
    """Types of detection"""
    OBJECT = "object"
    FACE = "face"
    TEXT = "text"
    SCENE = "scene"
    ACTIVITY = "activity"
    EMOTION = "emotion"


class PrivacyLevel(Enum):
    """Privacy levels for face detection"""
    NONE = "none"  # No privacy, show all faces
    BLUR = "blur"  # Blur faces
    PIXELATE = "pixelate"  # Pixelate faces
    REMOVE = "remove"  # Remove face regions
    ANONYMOUS = "anonymous"  # Replace with generic avatar


@dataclass
class BoundingBox:
    """Bounding box for detected objects"""
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    label: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DetectedObject:
    """Detected object in image/video"""
    object_id: str
    label: str
    confidence: float
    bbox: BoundingBox
    features: Optional[np.ndarray] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    frame_number: Optional[int] = None
    timestamp: Optional[float] = None


@dataclass
class Face:
    """Detected face with privacy controls"""
    face_id: str
    bbox: BoundingBox
    landmarks: Optional[Dict[str, Tuple[int, int]]] = None
    encoding: Optional[np.ndarray] = None
    emotion: Optional[str] = None
    age_estimate: Optional[int] = None
    gender_estimate: Optional[str] = None
    is_anonymized: bool = False


@dataclass
class SceneDescription:
    """Scene description and understanding"""
    description: str
    caption: str
    scene_type: str
    objects: List[str]
    activities: List[str]
    attributes: Dict[str, Any]
    confidence: float


@dataclass
class VisualSearchResult:
    """Result from visual search"""
    content_id: str
    similarity_score: float
    content_type: ContentType
    location: str  # File path or frame number
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VisualAnalysisResult:
    """Complete visual analysis result"""
    content_id: str
    content_type: ContentType
    objects: List[DetectedObject]
    faces: List[Face]
    scene: SceneDescription
    text_regions: List[Dict[str, Any]]
    tags: List[str]
    safety_scores: Dict[str, float]
    metadata: Dict[str, Any]
    processing_time: float


class VisualContentAnalyzer:
    """Main visual content analysis system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize models
        self._initialize_models()
        
        # Privacy settings
        self.privacy_level = PrivacyLevel[
            self.config.get('privacy_level', 'BLUR').upper()
        ]
        
        # Cache for embeddings
        self.embedding_cache: Dict[str, np.ndarray] = {}
        
        # Safety thresholds
        self.safety_thresholds = self.config.get('safety_thresholds', {
            'adult': 0.7,
            'violence': 0.7,
            'offensive': 0.7
        })
    
    def _initialize_models(self):
        """Initialize computer vision models"""
        try:
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            
            # Object Detection
            if self.config.get('use_yolo', True):
                self.yolo_model = YOLO('yolov8n.pt')
            
            # Faster R-CNN for detailed detection
            self.frcnn_model = fasterrcnn_resnet50_fpn(pretrained=True)
            self.frcnn_model.eval()
            self.frcnn_model.to(device)
            
            # DETR for advanced object detection
            if self.config.get('use_detr', False):
                self.detr_processor = DetrImageProcessor.from_pretrained(
                    "facebook/detr-resnet-50"
                )
                self.detr_model = DetrForObjectDetection.from_pretrained(
                    "facebook/detr-resnet-50"
                )
                self.detr_model.to(device)
            
            # CLIP for visual search and understanding
            self.clip_processor = CLIPProcessor.from_pretrained(
                "openai/clip-vit-base-patch32"
            )
            self.clip_model = CLIPModel.from_pretrained(
                "openai/clip-vit-base-patch32"
            )
            self.clip_model.to(device)
            
            # BLIP for image captioning
            self.blip_processor = BlipProcessor.from_pretrained(
                "Salesforce/blip-image-captioning-base"
            )
            self.blip_model = BlipForConditionalGeneration.from_pretrained(
                "Salesforce/blip-image-captioning-base"
            )
            self.blip_model.to(device)
            
            # Face detection
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            
            # MediaPipe for face mesh and landmarks
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=10,
                refine_landmarks=True,
                min_detection_confidence=0.5
            )
            
            # OCR
            self.ocr_reader = easyocr.Reader(['en'])
            
            # Image classification for scene understanding
            self.vit_processor = ViTImageProcessor.from_pretrained(
                'google/vit-base-patch16-224'
            )
            self.vit_model = ViTForImageClassification.from_pretrained(
                'google/vit-base-patch16-224'
            )
            self.vit_model.to(device)
            
            self.device = device
            logger.info("Visual analysis models initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize models: {e}")
            self.device = torch.device('cpu')
    
    async def analyze_image(
        self,
        image_path: str,
        detect_objects: bool = True,
        detect_faces: bool = True,
        extract_text: bool = True,
        generate_description: bool = True,
        check_safety: bool = True
    ) -> VisualAnalysisResult:
        """Analyze a single image"""
        
        import time
        start_time = time.time()
        
        # Load image
        image = Image.open(image_path).convert('RGB')
        image_np = np.array(image)
        
        # Generate content ID
        content_id = self._generate_content_id(image_path)
        
        # Detect objects
        objects = []
        if detect_objects:
            objects = await self._detect_objects(image_np)
        
        # Detect faces with privacy controls
        faces = []
        if detect_faces:
            faces = await self._detect_faces(image_np)
            
            # Apply privacy controls
            if self.privacy_level != PrivacyLevel.NONE:
                image_np = self._apply_privacy(image_np, faces)
        
        # Extract text
        text_regions = []
        if extract_text:
            text_regions = await self._extract_text(image_np)
        
        # Generate scene description
        scene = None
        if generate_description:
            scene = await self._generate_scene_description(image)
        
        # Generate tags
        tags = self._generate_tags(objects, scene, text_regions)
        
        # Check content safety
        safety_scores = {}
        if check_safety:
            safety_scores = await self._check_safety(image)
        
        # Calculate metadata
        metadata = {
            'width': image.width,
            'height': image.height,
            'format': image.format,
            'mode': image.mode,
            'file_size': os.path.getsize(image_path),
            'file_path': image_path
        }
        
        processing_time = time.time() - start_time
        
        return VisualAnalysisResult(
            content_id=content_id,
            content_type=ContentType.IMAGE,
            objects=objects,
            faces=faces,
            scene=scene,
            text_regions=text_regions,
            tags=tags,
            safety_scores=safety_scores,
            metadata=metadata,
            processing_time=processing_time
        )
    
    async def analyze_video(
        self,
        video_path: str,
        sample_rate: int = 1,  # Sample every N frames
        max_frames: int = 100,
        detect_objects: bool = True,
        detect_faces: bool = True,
        track_objects: bool = True
    ) -> List[VisualAnalysisResult]:
        """Analyze video content"""
        
        results = []
        
        # Open video
        vr = VideoReader(video_path, ctx=cpu(0))
        total_frames = len(vr)
        fps = vr.get_avg_fps()
        
        # Calculate sampling
        frames_to_process = min(max_frames, total_frames // sample_rate)
        frame_indices = np.linspace(0, total_frames - 1, frames_to_process, dtype=int)
        
        # Object tracker for continuity
        tracker = None
        if track_objects and hasattr(self, 'yolo_model'):
            tracker = sv.ByteTrack()
        
        # Process frames
        for frame_idx in frame_indices:
            frame = vr[frame_idx].asnumpy()
            
            # Analyze frame
            frame_result = await self._analyze_frame(
                frame,
                frame_number=int(frame_idx),
                timestamp=frame_idx / fps,
                detect_objects=detect_objects,
                detect_faces=detect_faces
            )
            
            # Track objects across frames
            if tracker and frame_result.objects:
                # Update tracking
                detections = self._objects_to_detections(frame_result.objects)
                tracked = tracker.update_with_detections(detections)
                
                # Update object IDs for continuity
                for obj, track_id in zip(frame_result.objects, tracked.tracker_id):
                    obj.attributes['track_id'] = int(track_id)
            
            results.append(frame_result)
        
        # Generate video-level summary
        video_summary = self._generate_video_summary(results, video_path)
        
        # Add summary as metadata to all results
        for result in results:
            result.metadata['video_summary'] = video_summary
        
        return results
    
    async def _detect_objects(self, image_np: np.ndarray) -> List[DetectedObject]:
        """Detect objects in image"""
        
        objects = []
        
        try:
            # Use YOLO for detection
            if hasattr(self, 'yolo_model'):
                results = self.yolo_model(image_np)
                
                for r in results:
                    boxes = r.boxes
                    if boxes is not None:
                        for i, box in enumerate(boxes):
                            bbox = BoundingBox(
                                x1=float(box.xyxy[0][0]),
                                y1=float(box.xyxy[0][1]),
                                x2=float(box.xyxy[0][2]),
                                y2=float(box.xyxy[0][3]),
                                confidence=float(box.conf[0]),
                                label=r.names[int(box.cls[0])]
                            )
                            
                            objects.append(DetectedObject(
                                object_id=self._generate_id(),
                                label=bbox.label,
                                confidence=bbox.confidence,
                                bbox=bbox
                            ))
            
            # Use Faster R-CNN for additional detection
            if hasattr(self, 'frcnn_model'):
                image_tensor = transforms.ToTensor()(image_np).unsqueeze(0)
                image_tensor = image_tensor.to(self.device)
                
                with torch.no_grad():
                    predictions = self.frcnn_model(image_tensor)
                
                # COCO class names
                COCO_CLASSES = [
                    '__background__', 'person', 'bicycle', 'car', 'motorcycle',
                    'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light',
                    'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird',
                    'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear',
                    'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie',
                    'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
                    'kite', 'baseball bat', 'baseball glove', 'skateboard',
                    'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
                    'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
                    'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza',
                    'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed',
                    'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote',
                    'keyboard', 'cell phone', 'microwave', 'oven', 'toaster',
                    'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors',
                    'teddy bear', 'hair drier', 'toothbrush'
                ]
                
                for pred in predictions:
                    for i in range(len(pred['boxes'])):
                        if pred['scores'][i] > 0.5:
                            box = pred['boxes'][i].cpu().numpy()
                            label_idx = pred['labels'][i].item()
                            label = COCO_CLASSES[label_idx] if label_idx < len(COCO_CLASSES) else 'unknown'
                            
                            # Check if not duplicate
                            is_duplicate = any(
                                obj.label == label and 
                                self._iou(obj.bbox, BoundingBox(
                                    x1=box[0], y1=box[1], x2=box[2], y2=box[3],
                                    confidence=pred['scores'][i].item(),
                                    label=label
                                )) > 0.5
                                for obj in objects
                            )
                            
                            if not is_duplicate:
                                bbox = BoundingBox(
                                    x1=float(box[0]),
                                    y1=float(box[1]),
                                    x2=float(box[2]),
                                    y2=float(box[3]),
                                    confidence=float(pred['scores'][i]),
                                    label=label
                                )
                                
                                objects.append(DetectedObject(
                                    object_id=self._generate_id(),
                                    label=label,
                                    confidence=bbox.confidence,
                                    bbox=bbox,
                                    attributes={'model': 'faster_rcnn'}
                                ))
            
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
        
        return objects
    
    async def _detect_faces(self, image_np: np.ndarray) -> List[Face]:
        """Detect faces with privacy controls"""
        
        faces = []
        
        try:
            # Convert to RGB if needed
            if len(image_np.shape) == 2:
                image_rgb = cv2.cvtColor(image_np, cv2.COLOR_GRAY2RGB)
            else:
                image_rgb = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
            
            # Detect faces using face_recognition
            face_locations = face_recognition.face_locations(image_rgb)
            face_encodings = face_recognition.face_encodings(image_rgb, face_locations)
            
            for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
                bbox = BoundingBox(
                    x1=float(left),
                    y1=float(top),
                    x2=float(right),
                    y2=float(bottom),
                    confidence=1.0,
                    label="face"
                )
                
                face = Face(
                    face_id=self._generate_id(),
                    bbox=bbox,
                    encoding=encoding
                )
                
                # Get face landmarks using MediaPipe
                face_roi = image_rgb[top:bottom, left:right]
                if face_roi.size > 0:
                    results = self.face_mesh.process(face_roi)
                    
                    if results.multi_face_landmarks:
                        landmarks = {}
                        for face_landmarks in results.multi_face_landmarks:
                            # Extract key landmarks
                            landmarks['left_eye'] = (
                                int(face_landmarks.landmark[33].x * face_roi.shape[1] + left),
                                int(face_landmarks.landmark[33].y * face_roi.shape[0] + top)
                            )
                            landmarks['right_eye'] = (
                                int(face_landmarks.landmark[133].x * face_roi.shape[1] + left),
                                int(face_landmarks.landmark[133].y * face_roi.shape[0] + top)
                            )
                            landmarks['nose'] = (
                                int(face_landmarks.landmark[1].x * face_roi.shape[1] + left),
                                int(face_landmarks.landmark[1].y * face_roi.shape[0] + top)
                            )
                            landmarks['mouth'] = (
                                int(face_landmarks.landmark[13].x * face_roi.shape[1] + left),
                                int(face_landmarks.landmark[13].y * face_roi.shape[0] + top)
                            )
                        
                        face.landmarks = landmarks
                
                faces.append(face)
            
            # Alternative: OpenCV cascade classifier
            if not faces:
                gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
                cv_faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                
                for (x, y, w, h) in cv_faces:
                    bbox = BoundingBox(
                        x1=float(x),
                        y1=float(y),
                        x2=float(x + w),
                        y2=float(y + h),
                        confidence=0.8,
                        label="face"
                    )
                    
                    faces.append(Face(
                        face_id=self._generate_id(),
                        bbox=bbox
                    ))
            
        except Exception as e:
            logger.error(f"Face detection failed: {e}")
        
        return faces
    
    def _apply_privacy(
        self,
        image_np: np.ndarray,
        faces: List[Face]
    ) -> np.ndarray:
        """Apply privacy controls to faces"""
        
        if self.privacy_level == PrivacyLevel.NONE:
            return image_np
        
        image_copy = image_np.copy()
        
        for face in faces:
            bbox = face.bbox
            x1, y1, x2, y2 = int(bbox.x1), int(bbox.y1), int(bbox.x2), int(bbox.y2)
            
            if self.privacy_level == PrivacyLevel.BLUR:
                # Apply Gaussian blur
                face_region = image_copy[y1:y2, x1:x2]
                if face_region.size > 0:
                    blurred = cv2.GaussianBlur(face_region, (99, 99), 30)
                    image_copy[y1:y2, x1:x2] = blurred
                    
            elif self.privacy_level == PrivacyLevel.PIXELATE:
                # Pixelate face
                face_region = image_copy[y1:y2, x1:x2]
                if face_region.size > 0:
                    h, w = face_region.shape[:2]
                    temp = cv2.resize(face_region, (w//10, h//10), interpolation=cv2.INTER_LINEAR)
                    pixelated = cv2.resize(temp, (w, h), interpolation=cv2.INTER_NEAREST)
                    image_copy[y1:y2, x1:x2] = pixelated
                    
            elif self.privacy_level == PrivacyLevel.REMOVE:
                # Black out face region
                image_copy[y1:y2, x1:x2] = 0
                
            elif self.privacy_level == PrivacyLevel.ANONYMOUS:
                # Replace with generic avatar
                cv2.rectangle(image_copy, (x1, y1), (x2, y2), (128, 128, 128), -1)
                cv2.putText(
                    image_copy, "ANONYMOUS",
                    (x1 + 5, y1 + 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (255, 255, 255), 1
                )
            
            face.is_anonymized = True
        
        return image_copy
    
    async def _extract_text(self, image_np: np.ndarray) -> List[Dict[str, Any]]:
        """Extract text from image using OCR"""
        
        text_regions = []
        
        try:
            # Use EasyOCR
            results = self.ocr_reader.readtext(image_np)
            
            for (bbox, text, confidence) in results:
                # Convert bbox format
                points = np.array(bbox).astype(int)
                x_coords = points[:, 0]
                y_coords = points[:, 1]
                
                text_region = {
                    'text': text,
                    'confidence': confidence,
                    'bbox': {
                        'x1': int(x_coords.min()),
                        'y1': int(y_coords.min()),
                        'x2': int(x_coords.max()),
                        'y2': int(y_coords.max())
                    },
                    'polygon': bbox
                }
                
                text_regions.append(text_region)
            
            # Alternative: Tesseract OCR
            if not text_regions:
                text = pytesseract.image_to_string(image_np)
                if text.strip():
                    text_regions.append({
                        'text': text.strip(),
                        'confidence': 0.7,
                        'bbox': None,
                        'method': 'tesseract'
                    })
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
        
        return text_regions
    
    async def _generate_scene_description(self, image: Image.Image) -> SceneDescription:
        """Generate scene description using vision models"""
        
        try:
            # Generate caption using BLIP
            inputs = self.blip_processor(image, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                out = self.blip_model.generate(**inputs, max_length=50)
                caption = self.blip_processor.decode(out[0], skip_special_tokens=True)
            
            # Generate detailed description
            prompt = "Describe this image in detail:"
            inputs = self.blip_processor(image, prompt, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                out = self.blip_model.generate(**inputs, max_length=100)
                description = self.blip_processor.decode(out[0], skip_special_tokens=True)
            
            # Classify scene type using ViT
            inputs = self.vit_processor(images=image, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                outputs = self.vit_model(**inputs)
                logits = outputs.logits
                predicted_class_idx = logits.argmax(-1).item()
                scene_type = self.vit_model.config.id2label[predicted_class_idx]
            
            # Extract objects and activities from description
            objects = self._extract_objects_from_text(description)
            activities = self._extract_activities_from_text(description)
            
            return SceneDescription(
                description=description,
                caption=caption,
                scene_type=scene_type,
                objects=objects,
                activities=activities,
                attributes={
                    'indoor_outdoor': self._classify_indoor_outdoor(description),
                    'time_of_day': self._estimate_time_of_day(image),
                    'weather': self._detect_weather(description)
                },
                confidence=0.85
            )
            
        except Exception as e:
            logger.error(f"Scene description generation failed: {e}")
            return SceneDescription(
                description="Unable to generate description",
                caption="",
                scene_type="unknown",
                objects=[],
                activities=[],
                attributes={},
                confidence=0.0
            )
    
    async def visual_search(
        self,
        query: Union[str, Image.Image, np.ndarray],
        image_database: List[str],
        top_k: int = 10
    ) -> List[VisualSearchResult]:
        """Search for visually similar content"""
        
        results = []
        
        try:
            # Get query embedding
            if isinstance(query, str):
                # Text query
                inputs = self.clip_processor(
                    text=[query],
                    return_tensors="pt",
                    padding=True
                ).to(self.device)
                
                with torch.no_grad():
                    query_embedding = self.clip_model.get_text_features(**inputs)
                    
            else:
                # Image query
                if isinstance(query, np.ndarray):
                    query = Image.fromarray(query)
                
                inputs = self.clip_processor(
                    images=query,
                    return_tensors="pt"
                ).to(self.device)
                
                with torch.no_grad():
                    query_embedding = self.clip_model.get_image_features(**inputs)
            
            query_embedding = query_embedding.cpu().numpy().flatten()
            
            # Search through database
            similarities = []
            
            for image_path in image_database:
                # Get or compute image embedding
                if image_path in self.embedding_cache:
                    image_embedding = self.embedding_cache[image_path]
                else:
                    image = Image.open(image_path).convert('RGB')
                    inputs = self.clip_processor(
                        images=image,
                        return_tensors="pt"
                    ).to(self.device)
                    
                    with torch.no_grad():
                        image_embedding = self.clip_model.get_image_features(**inputs)
                    
                    image_embedding = image_embedding.cpu().numpy().flatten()
                    self.embedding_cache[image_path] = image_embedding
                
                # Calculate similarity
                similarity = np.dot(query_embedding, image_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(image_embedding)
                )
                
                similarities.append((image_path, float(similarity)))
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Create results
            for image_path, similarity in similarities[:top_k]:
                results.append(VisualSearchResult(
                    content_id=self._generate_content_id(image_path),
                    similarity_score=similarity,
                    content_type=ContentType.IMAGE,
                    location=image_path,
                    metadata={'query': query if isinstance(query, str) else 'image_query'}
                ))
                
        except Exception as e:
            logger.error(f"Visual search failed: {e}")
        
        return results
    
    async def _check_safety(self, image: Image.Image) -> Dict[str, float]:
        """Check content safety using various models"""
        
        safety_scores = {
            'safe': 1.0,
            'adult': 0.0,
            'violence': 0.0,
            'offensive': 0.0
        }
        
        try:
            # Use CLIP for zero-shot classification
            safety_labels = [
                "safe content",
                "adult content",
                "violent content",
                "offensive content"
            ]
            
            inputs = self.clip_processor(
                text=safety_labels,
                images=image,
                return_tensors="pt",
                padding=True
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.clip_model(**inputs)
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1).cpu().numpy()[0]
            
            safety_scores = {
                'safe': float(probs[0]),
                'adult': float(probs[1]),
                'violence': float(probs[2]),
                'offensive': float(probs[3])
            }
            
        except Exception as e:
            logger.error(f"Safety check failed: {e}")
        
        return safety_scores
    
    async def _analyze_frame(
        self,
        frame: np.ndarray,
        frame_number: int,
        timestamp: float,
        detect_objects: bool = True,
        detect_faces: bool = True
    ) -> VisualAnalysisResult:
        """Analyze a single video frame"""
        
        # Convert frame to PIL Image
        image = Image.fromarray(frame)
        
        # Detect objects
        objects = []
        if detect_objects:
            objects = await self._detect_objects(frame)
            
            # Add frame information
            for obj in objects:
                obj.frame_number = frame_number
                obj.timestamp = timestamp
        
        # Detect faces
        faces = []
        if detect_faces:
            faces = await self._detect_faces(frame)
        
        # Generate simple scene description
        scene = SceneDescription(
            description=f"Frame {frame_number} at {timestamp:.2f}s",
            caption="",
            scene_type="video_frame",
            objects=[obj.label for obj in objects],
            activities=[],
            attributes={'frame_number': frame_number, 'timestamp': timestamp},
            confidence=0.9
        )
        
        return VisualAnalysisResult(
            content_id=f"frame_{frame_number}",
            content_type=ContentType.FRAME,
            objects=objects,
            faces=faces,
            scene=scene,
            text_regions=[],
            tags=[],
            safety_scores={},
            metadata={'frame_number': frame_number, 'timestamp': timestamp},
            processing_time=0.0
        )
    
    def _generate_video_summary(
        self,
        frame_results: List[VisualAnalysisResult],
        video_path: str
    ) -> Dict[str, Any]:
        """Generate summary of video analysis"""
        
        # Aggregate objects across frames
        all_objects = []
        for result in frame_results:
            all_objects.extend([obj.label for obj in result.objects])
        
        object_counts = Counter(all_objects)
        
        # Track unique faces
        unique_faces = set()
        for result in frame_results:
            unique_faces.update([f.face_id for f in result.faces])
        
        # Calculate statistics
        return {
            'video_path': video_path,
            'frames_analyzed': len(frame_results),
            'unique_objects': list(object_counts.keys()),
            'object_frequency': dict(object_counts),
            'unique_faces_detected': len(unique_faces),
            'dominant_objects': [obj for obj, _ in object_counts.most_common(5)],
            'has_text': any(result.text_regions for result in frame_results)
        }
    
    def _extract_objects_from_text(self, text: str) -> List[str]:
        """Extract object mentions from text description"""
        
        # Simple noun extraction
        import nltk
        try:
            tokens = nltk.word_tokenize(text.lower())
            pos_tags = nltk.pos_tag(tokens)
            
            objects = [
                word for word, pos in pos_tags
                if pos in ['NN', 'NNS', 'NNP', 'NNPS']
            ]
            
            return list(set(objects))[:10]
            
        except:
            return []
    
    def _extract_activities_from_text(self, text: str) -> List[str]:
        """Extract activity mentions from text description"""
        
        # Simple verb extraction
        import nltk
        try:
            tokens = nltk.word_tokenize(text.lower())
            pos_tags = nltk.pos_tag(tokens)
            
            activities = [
                word for word, pos in pos_tags
                if pos in ['VB', 'VBG', 'VBD', 'VBN', 'VBP', 'VBZ']
            ]
            
            return list(set(activities))[:5]
            
        except:
            return []
    
    def _classify_indoor_outdoor(self, description: str) -> str:
        """Classify scene as indoor or outdoor"""
        
        outdoor_keywords = ['sky', 'tree', 'street', 'road', 'mountain', 'beach', 'park']
        indoor_keywords = ['room', 'wall', 'ceiling', 'floor', 'furniture', 'table', 'chair']
        
        description_lower = description.lower()
        
        outdoor_score = sum(1 for word in outdoor_keywords if word in description_lower)
        indoor_score = sum(1 for word in indoor_keywords if word in description_lower)
        
        if outdoor_score > indoor_score:
            return 'outdoor'
        elif indoor_score > outdoor_score:
            return 'indoor'
        else:
            return 'unknown'
    
    def _estimate_time_of_day(self, image: Image.Image) -> str:
        """Estimate time of day from image brightness"""
        
        # Convert to grayscale and calculate average brightness
        gray = image.convert('L')
        brightness = np.array(gray).mean()
        
        if brightness < 50:
            return 'night'
        elif brightness < 100:
            return 'evening'
        elif brightness < 150:
            return 'day'
        else:
            return 'bright_day'
    
    def _detect_weather(self, description: str) -> str:
        """Detect weather conditions from description"""
        
        weather_keywords = {
            'sunny': ['sun', 'sunny', 'bright', 'clear'],
            'cloudy': ['cloud', 'cloudy', 'overcast'],
            'rainy': ['rain', 'rainy', 'wet'],
            'snowy': ['snow', 'snowy', 'winter']
        }
        
        description_lower = description.lower()
        
        for weather, keywords in weather_keywords.items():
            if any(word in description_lower for word in keywords):
                return weather
        
        return 'unknown'
    
    def _iou(self, box1: BoundingBox, box2: BoundingBox) -> float:
        """Calculate Intersection over Union"""
        
        x1 = max(box1.x1, box2.x1)
        y1 = max(box1.y1, box2.y1)
        x2 = min(box1.x2, box2.x2)
        y2 = min(box1.y2, box2.y2)
        
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        
        area1 = (box1.x2 - box1.x1) * (box1.y2 - box1.y1)
        area2 = (box2.x2 - box2.x1) * (box2.y2 - box2.y1)
        
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0
    
    def _objects_to_detections(self, objects: List[DetectedObject]) -> sv.Detections:
        """Convert objects to supervision detections format"""
        
        if not objects:
            return sv.Detections.empty()
        
        xyxy = np.array([
            [obj.bbox.x1, obj.bbox.y1, obj.bbox.x2, obj.bbox.y2]
            for obj in objects
        ])
        
        confidence = np.array([obj.confidence for obj in objects])
        class_id = np.array([hash(obj.label) % 100 for obj in objects])
        
        return sv.Detections(
            xyxy=xyxy,
            confidence=confidence,
            class_id=class_id
        )
    
    def _generate_tags(
        self,
        objects: List[DetectedObject],
        scene: Optional[SceneDescription],
        text_regions: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate tags from analysis results"""
        
        tags = set()
        
        # Object tags
        for obj in objects:
            tags.add(obj.label)
        
        # Scene tags
        if scene:
            tags.update(scene.objects)
            tags.update(scene.activities)
            if scene.scene_type:
                tags.add(scene.scene_type)
        
        # Text tags
        for region in text_regions:
            # Add significant words from text
            text = region.get('text', '')
            words = text.split()
            tags.update([w.lower() for w in words if len(w) > 4])
        
        return list(tags)[:20]
    
    def _generate_content_id(self, content_path: str) -> str:
        """Generate unique content ID"""
        
        return hashlib.md5(content_path.encode()).hexdigest()[:12]
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        
        import uuid
        return str(uuid.uuid4())[:8]
    
    def visualize_analysis(
        self,
        image_path: str,
        result: VisualAnalysisResult,
        output_path: Optional[str] = None
    ) -> Image.Image:
        """Visualize analysis results on image"""
        
        # Load image
        image = Image.open(image_path).convert('RGB')
        draw = ImageDraw.Draw(image)
        
        # Draw object bounding boxes
        for obj in result.objects:
            bbox = obj.bbox
            color = (0, 255, 0) if obj.confidence > 0.7 else (255, 255, 0)
            
            draw.rectangle(
                [(bbox.x1, bbox.y1), (bbox.x2, bbox.y2)],
                outline=color,
                width=2
            )
            
            # Add label
            label = f"{obj.label} ({obj.confidence:.2f})"
            draw.text(
                (bbox.x1, bbox.y1 - 20),
                label,
                fill=color
            )
        
        # Draw face boxes (if not anonymized)
        if self.privacy_level == PrivacyLevel.NONE:
            for face in result.faces:
                bbox = face.bbox
                draw.rectangle(
                    [(bbox.x1, bbox.y1), (bbox.x2, bbox.y2)],
                    outline=(255, 0, 0),
                    width=2
                )
        
        # Draw text regions
        for region in result.text_regions:
            if region.get('bbox'):
                bbox = region['bbox']
                draw.rectangle(
                    [(bbox['x1'], bbox['y1']), (bbox['x2'], bbox['y2'])],
                    outline=(0, 0, 255),
                    width=1
                )
        
        # Add scene description
        if result.scene:
            # Add text overlay
            text = f"Scene: {result.scene.caption}"
            draw.text((10, 10), text, fill=(255, 255, 255))
        
        # Save if requested
        if output_path:
            image.save(output_path)
        
        return image


# Example usage
async def main():
    """Example usage of visual content analysis"""
    
    # Initialize analyzer
    analyzer = VisualContentAnalyzer({
        'privacy_level': 'BLUR',
        'use_yolo': True,
        'use_detr': False
    })
    
    # Analyze image
    result = await analyzer.analyze_image(
        "sample_image.jpg",
        detect_objects=True,
        detect_faces=True,
        extract_text=True,
        generate_description=True,
        check_safety=True
    )
    
    print(f"Detected {len(result.objects)} objects:")
    for obj in result.objects[:5]:
        print(f"  - {obj.label}: {obj.confidence:.2f}")
    
    print(f"\nDetected {len(result.faces)} faces")
    
    if result.scene:
        print(f"\nScene Description: {result.scene.caption}")
        print(f"Scene Type: {result.scene.scene_type}")
    
    if result.text_regions:
        print(f"\nExtracted text: {len(result.text_regions)} regions")
        for region in result.text_regions[:3]:
            print(f"  - {region['text']}")
    
    print(f"\nSafety Scores:")
    for key, score in result.safety_scores.items():
        print(f"  {key}: {score:.2f}")
    
    print(f"\nTags: {', '.join(result.tags[:10])}")
    
    # Visual search example
    search_results = await analyzer.visual_search(
        "find images with cars",
        ["image1.jpg", "image2.jpg", "image3.jpg"],
        top_k=5
    )
    
    print(f"\nVisual search results:")
    for res in search_results:
        print(f"  - {res.location}: {res.similarity_score:.2f}")
    
    # Visualize results
    analyzer.visualize_analysis(
        "sample_image.jpg",
        result,
        "analysis_visualization.jpg"
    )
    print("\nVisualization saved")


if __name__ == "__main__":
    asyncio.run(main())