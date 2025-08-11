#!/usr/bin/env python3
"""
Real-time Video Analytics System
Implements AI-powered video analysis with object detection, scene understanding,
activity recognition, and behavioral analytics
"""

import asyncio
import json
import logging
import hashlib
import os
import tempfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from pathlib import Path
import cv2
import torch
import torch.nn as nn
import torchvision
from torchvision import transforms, models
from transformers import (
    AutoImageProcessor,
    AutoModelForObjectDetection,
    AutoModelForVideoClassification,
    pipeline
)
import mediapipe as mp
from collections import deque, defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor
import queue
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalyticsType(Enum):
    """Types of video analytics"""
    OBJECT_DETECTION = "object_detection"
    FACE_DETECTION = "face_detection"
    POSE_ESTIMATION = "pose_estimation"
    ACTIVITY_RECOGNITION = "activity_recognition"
    SCENE_UNDERSTANDING = "scene_understanding"
    EMOTION_DETECTION = "emotion_detection"
    CROWD_ANALYSIS = "crowd_analysis"
    ANOMALY_DETECTION = "anomaly_detection"
    VEHICLE_TRACKING = "vehicle_tracking"
    TEXT_RECOGNITION = "text_recognition"


class VideoSource(Enum):
    """Video input sources"""
    FILE = "file"
    WEBCAM = "webcam"
    RTSP = "rtsp"
    HTTP_STREAM = "http_stream"
    YOUTUBE = "youtube"


@dataclass
class DetectedObject:
    """Detected object in video frame"""
    object_id: str
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    frame_number: int
    timestamp: float
    tracking_id: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VideoScene:
    """Scene analysis result"""
    scene_id: str
    scene_type: str
    confidence: float
    objects: List[DetectedObject]
    activities: List[str]
    start_frame: int
    end_frame: int
    duration: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalyticsResult:
    """Complete analytics result for a video segment"""
    video_id: str
    timestamp: datetime
    frame_count: int
    duration: float
    detected_objects: List[DetectedObject]
    scenes: List[VideoScene]
    activities: List[Dict[str, Any]]
    anomalies: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    heatmaps: Optional[np.ndarray] = None


class ObjectTracker:
    """Multi-object tracker using SORT algorithm"""
    
    def __init__(self, max_age: int = 30, min_hits: int = 3):
        self.max_age = max_age
        self.min_hits = min_hits
        self.trackers = {}
        self.frame_count = 0
        self.next_id = 0
        
    def update(self, detections: List[Tuple[int, int, int, int]]) -> List[Tuple[int, Tuple[int, int, int, int]]]:
        """Update tracker with new detections"""
        self.frame_count += 1
        
        # Simple IoU-based tracking
        tracked_objects = []
        
        for detection in detections:
            best_iou = 0
            best_tracker_id = None
            
            # Find best matching tracker
            for tracker_id, tracker_info in self.trackers.items():
                iou = self._calculate_iou(detection, tracker_info['bbox'])
                if iou > best_iou:
                    best_iou = iou
                    best_tracker_id = tracker_id
            
            # Update existing tracker or create new one
            if best_iou > 0.3:
                self.trackers[best_tracker_id]['bbox'] = detection
                self.trackers[best_tracker_id]['age'] = 0
                self.trackers[best_tracker_id]['hits'] += 1
                tracked_objects.append((best_tracker_id, detection))
            else:
                # Create new tracker
                tracker_id = self.next_id
                self.next_id += 1
                self.trackers[tracker_id] = {
                    'bbox': detection,
                    'age': 0,
                    'hits': 1
                }
                tracked_objects.append((tracker_id, detection))
        
        # Age out old trackers
        trackers_to_delete = []
        for tracker_id, tracker_info in self.trackers.items():
            tracker_info['age'] += 1
            if tracker_info['age'] > self.max_age:
                trackers_to_delete.append(tracker_id)
        
        for tracker_id in trackers_to_delete:
            del self.trackers[tracker_id]
        
        return tracked_objects
    
    def _calculate_iou(self, box1: Tuple, box2: Tuple) -> float:
        """Calculate Intersection over Union"""
        x1_min, y1_min, w1, h1 = box1
        x2_min, y2_min, w2, h2 = box2
        
        x1_max = x1_min + w1
        y1_max = y1_min + h1
        x2_max = x2_min + w2
        y2_max = y2_min + h2
        
        # Calculate intersection
        inter_xmin = max(x1_min, x2_min)
        inter_ymin = max(y1_min, y2_min)
        inter_xmax = min(x1_max, x2_max)
        inter_ymax = min(y1_max, y2_max)
        
        if inter_xmax < inter_xmin or inter_ymax < inter_ymin:
            return 0.0
        
        inter_area = (inter_xmax - inter_xmin) * (inter_ymax - inter_ymin)
        box1_area = w1 * h1
        box2_area = w2 * h2
        union_area = box1_area + box2_area - inter_area
        
        return inter_area / union_area if union_area > 0 else 0.0


class ActivityRecognizer:
    """Recognize activities from video sequences"""
    
    def __init__(self):
        self.activity_buffer = deque(maxlen=30)  # 1 second at 30fps
        self.pose_detector = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.5
        )
        
    def recognize_activity(self, frame: np.ndarray) -> List[str]:
        """Recognize activities in frame"""
        activities = []
        
        # Detect pose
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose_detector.process(frame_rgb)
        
        if results.pose_landmarks:
            # Extract pose features
            pose_features = self._extract_pose_features(results.pose_landmarks)
            self.activity_buffer.append(pose_features)
            
            # Analyze activity from buffer
            if len(self.activity_buffer) >= 15:
                activity = self._classify_activity(list(self.activity_buffer))
                if activity:
                    activities.append(activity)
        
        return activities
    
    def _extract_pose_features(self, landmarks) -> np.ndarray:
        """Extract features from pose landmarks"""
        features = []
        
        # Key points for activity recognition
        key_points = [
            mp.solutions.pose.PoseLandmark.LEFT_SHOULDER,
            mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER,
            mp.solutions.pose.PoseLandmark.LEFT_ELBOW,
            mp.solutions.pose.PoseLandmark.RIGHT_ELBOW,
            mp.solutions.pose.PoseLandmark.LEFT_WRIST,
            mp.solutions.pose.PoseLandmark.RIGHT_WRIST,
            mp.solutions.pose.PoseLandmark.LEFT_HIP,
            mp.solutions.pose.PoseLandmark.RIGHT_HIP,
            mp.solutions.pose.PoseLandmark.LEFT_KNEE,
            mp.solutions.pose.PoseLandmark.RIGHT_KNEE,
        ]
        
        for point in key_points:
            landmark = landmarks.landmark[point]
            features.extend([landmark.x, landmark.y, landmark.z])
        
        return np.array(features)
    
    def _classify_activity(self, pose_sequence: List[np.ndarray]) -> Optional[str]:
        """Classify activity from pose sequence"""
        # Simple rule-based classification
        # In production, use trained ML model
        
        pose_array = np.array(pose_sequence)
        
        # Calculate motion metrics
        motion = np.std(pose_array, axis=0)
        mean_motion = np.mean(motion)
        
        # Detect specific activities
        if mean_motion > 0.1:
            # Check for walking pattern
            hip_motion = motion[18:22]  # Hip points
            if np.mean(hip_motion) > 0.05:
                return "walking"
            
            # Check for hand gestures
            hand_motion = motion[12:18]  # Hand points
            if np.mean(hand_motion) > 0.15:
                return "gesturing"
        
        elif mean_motion < 0.02:
            return "standing"
        
        return None


class RealtimeVideoAnalytics:
    """Main real-time video analytics system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.models = {}
        self.trackers = {}
        self.activity_recognizer = ActivityRecognizer()
        self.analytics_queue = queue.Queue(maxsize=100)
        self.result_callbacks: List[Callable] = []
        self.is_running = False
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._initialize_models()
        
    def _initialize_models(self):
        """Initialize AI models for video analytics"""
        try:
            # Object detection model (YOLO or DETR)
            self.models['object_detector'] = AutoModelForObjectDetection.from_pretrained(
                "facebook/detr-resnet-50"
            )
            self.models['object_processor'] = AutoImageProcessor.from_pretrained(
                "facebook/detr-resnet-50"
            )
            
            # Face detection
            self.models['face_cascade'] = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            
            # Scene classification
            self.models['scene_classifier'] = models.resnet50(pretrained=True)
            self.models['scene_classifier'].eval()
            
            # Text detection (OCR)
            try:
                import easyocr
                self.models['text_reader'] = easyocr.Reader(['en'])
            except ImportError:
                logger.warning("EasyOCR not available, text detection disabled")
                self.models['text_reader'] = None
            
            logger.info("Video analytics models initialized")
            
        except Exception as e:
            logger.warning(f"Could not initialize all models: {e}")
    
    async def analyze_video(
        self,
        video_source: str,
        source_type: VideoSource = VideoSource.FILE,
        analytics_types: List[AnalyticsType] = None,
        real_time: bool = True,
        save_output: Optional[str] = None
    ) -> AnalyticsResult:
        """Analyze video with specified analytics types"""
        
        if analytics_types is None:
            analytics_types = [
                AnalyticsType.OBJECT_DETECTION,
                AnalyticsType.ACTIVITY_RECOGNITION,
                AnalyticsType.SCENE_UNDERSTANDING
            ]
        
        video_id = hashlib.md5(f"{video_source}_{datetime.now()}".encode()).hexdigest()
        
        # Open video source
        cap = self._open_video_source(video_source, source_type)
        if not cap.isOpened():
            raise ValueError(f"Failed to open video source: {video_source}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Initialize tracker
        self.trackers[video_id] = ObjectTracker()
        
        # Analytics results
        all_objects = []
        all_scenes = []
        all_activities = []
        all_anomalies = []
        frame_count = 0
        start_time = time.time()
        
        # Video writer for output
        out = None
        if save_output:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            out = cv2.VideoWriter(save_output, fourcc, fps, (frame_width, frame_height))
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                timestamp = frame_count / fps
                
                # Perform analytics based on types
                frame_results = {}
                
                if AnalyticsType.OBJECT_DETECTION in analytics_types:
                    objects = await self._detect_objects(frame, frame_count, timestamp)
                    frame_results['objects'] = objects
                    all_objects.extend(objects)
                
                if AnalyticsType.ACTIVITY_RECOGNITION in analytics_types:
                    activities = self.activity_recognizer.recognize_activity(frame)
                    if activities:
                        activity_data = {
                            'frame': frame_count,
                            'timestamp': timestamp,
                            'activities': activities
                        }
                        frame_results['activities'] = activity_data
                        all_activities.append(activity_data)
                
                if AnalyticsType.SCENE_UNDERSTANDING in analytics_types:
                    if frame_count % 30 == 0:  # Analyze scene every second
                        scene = await self._analyze_scene(frame, frame_count, timestamp)
                        frame_results['scene'] = scene
                        all_scenes.append(scene)
                
                if AnalyticsType.ANOMALY_DETECTION in analytics_types:
                    anomaly = await self._detect_anomalies(frame, frame_count, timestamp)
                    if anomaly:
                        frame_results['anomaly'] = anomaly
                        all_anomalies.append(anomaly)
                
                # Draw analytics on frame
                annotated_frame = self._annotate_frame(frame, frame_results)
                
                # Save annotated frame
                if out:
                    out.write(annotated_frame)
                
                # Callback for real-time results
                if real_time and frame_results:
                    for callback in self.result_callbacks:
                        callback(frame_count, frame_results)
                
                # Display frame (if in real-time mode)
                if real_time and self.config.get('display', False):
                    cv2.imshow('Video Analytics', annotated_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
        
        finally:
            cap.release()
            if out:
                out.release()
            cv2.destroyAllWindows()
        
        # Calculate statistics
        duration = time.time() - start_time
        statistics = self._calculate_statistics(
            all_objects, all_scenes, all_activities, all_anomalies
        )
        
        return AnalyticsResult(
            video_id=video_id,
            timestamp=datetime.now(),
            frame_count=frame_count,
            duration=duration,
            detected_objects=all_objects,
            scenes=all_scenes,
            activities=all_activities,
            anomalies=all_anomalies,
            statistics=statistics
        )
    
    def _open_video_source(self, source: str, source_type: VideoSource) -> cv2.VideoCapture:
        """Open video source based on type"""
        if source_type == VideoSource.FILE:
            return cv2.VideoCapture(source)
        elif source_type == VideoSource.WEBCAM:
            return cv2.VideoCapture(int(source) if source.isdigit() else 0)
        elif source_type == VideoSource.RTSP:
            return cv2.VideoCapture(source)
        elif source_type == VideoSource.HTTP_STREAM:
            return cv2.VideoCapture(source)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")
    
    async def _detect_objects(
        self,
        frame: np.ndarray,
        frame_number: int,
        timestamp: float
    ) -> List[DetectedObject]:
        """Detect objects in frame"""
        objects = []
        
        if 'object_detector' not in self.models:
            return objects
        
        # Prepare image
        processor = self.models['object_processor']
        model = self.models['object_detector']
        
        # Convert frame to PIL Image
        from PIL import Image
        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        # Process image
        inputs = processor(images=pil_image, return_tensors="pt")
        
        # Detect objects
        with torch.no_grad():
            outputs = model(**inputs)
        
        # Post-process results
        target_sizes = torch.tensor([pil_image.size[::-1]])
        results = processor.post_process_object_detection(
            outputs, 
            target_sizes=target_sizes, 
            threshold=0.5
        )[0]
        
        # Extract detections
        for score, label, box in zip(
            results["scores"], 
            results["labels"], 
            results["boxes"]
        ):
            box = [round(i, 2) for i in box.tolist()]
            x, y, x2, y2 = box
            
            obj = DetectedObject(
                object_id=hashlib.md5(f"{frame_number}_{x}_{y}".encode()).hexdigest()[:8],
                class_name=model.config.id2label[label.item()],
                confidence=score.item(),
                bbox=(int(x), int(y), int(x2-x), int(y2-y)),
                frame_number=frame_number,
                timestamp=timestamp
            )
            objects.append(obj)
        
        # Update tracker
        if objects:
            detections = [obj.bbox for obj in objects]
            video_id = list(self.trackers.keys())[0] if self.trackers else None
            if video_id and video_id in self.trackers:
                tracked = self.trackers[video_id].update(detections)
                for i, (track_id, _) in enumerate(tracked):
                    if i < len(objects):
                        objects[i].tracking_id = str(track_id)
        
        return objects
    
    async def _analyze_scene(
        self,
        frame: np.ndarray,
        frame_number: int,
        timestamp: float
    ) -> VideoScene:
        """Analyze scene content"""
        
        if 'scene_classifier' not in self.models:
            return None
        
        model = self.models['scene_classifier']
        
        # Prepare image
        from PIL import Image
        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        # Transform for ResNet
        transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        
        img_tensor = transform(pil_image).unsqueeze(0)
        
        # Classify scene
        with torch.no_grad():
            outputs = model(img_tensor)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
        
        # Get top prediction
        top_prob, top_class = torch.topk(probabilities, 1)
        
        # Load ImageNet class names (simplified - use actual class names in production)
        scene_type = f"scene_class_{top_class[0].item()}"
        
        return VideoScene(
            scene_id=hashlib.md5(f"{frame_number}_{scene_type}".encode()).hexdigest()[:8],
            scene_type=scene_type,
            confidence=top_prob[0].item(),
            objects=[],
            activities=[],
            start_frame=frame_number,
            end_frame=frame_number,
            duration=0.0
        )
    
    async def _detect_anomalies(
        self,
        frame: np.ndarray,
        frame_number: int,
        timestamp: float
    ) -> Optional[Dict[str, Any]]:
        """Detect anomalies in frame"""
        
        # Simple anomaly detection based on motion
        # In production, use trained anomaly detection model
        
        if not hasattr(self, '_prev_frame'):
            self._prev_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return None
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate frame difference
        frame_diff = cv2.absdiff(self._prev_frame, gray)
        _, thresh = cv2.threshold(frame_diff, 30, 255, cv2.THRESH_BINARY)
        
        # Calculate motion score
        motion_pixels = np.sum(thresh > 0)
        total_pixels = thresh.shape[0] * thresh.shape[1]
        motion_ratio = motion_pixels / total_pixels
        
        self._prev_frame = gray
        
        # Detect anomaly if motion is too high
        if motion_ratio > 0.3:
            return {
                'type': 'high_motion',
                'frame': frame_number,
                'timestamp': timestamp,
                'severity': 'medium' if motion_ratio < 0.5 else 'high',
                'motion_ratio': motion_ratio
            }
        
        return None
    
    def _annotate_frame(
        self,
        frame: np.ndarray,
        results: Dict[str, Any]
    ) -> np.ndarray:
        """Annotate frame with analytics results"""
        
        annotated = frame.copy()
        
        # Draw detected objects
        if 'objects' in results:
            for obj in results['objects']:
                x, y, w, h = obj.bbox
                color = (0, 255, 0) if obj.confidence > 0.7 else (0, 255, 255)
                
                # Draw bounding box
                cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
                
                # Draw label
                label = f"{obj.class_name}: {obj.confidence:.2f}"
                if obj.tracking_id:
                    label = f"[{obj.tracking_id}] {label}"
                
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(
                    annotated,
                    (x, y - label_size[1] - 4),
                    (x + label_size[0], y),
                    color,
                    -1
                )
                cv2.putText(
                    annotated,
                    label,
                    (x, y - 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1
                )
        
        # Draw activities
        if 'activities' in results and results['activities']['activities']:
            activities_text = ", ".join(results['activities']['activities'])
            cv2.putText(
                annotated,
                f"Activity: {activities_text}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
        
        # Draw scene info
        if 'scene' in results:
            scene = results['scene']
            cv2.putText(
                annotated,
                f"Scene: {scene.scene_type} ({scene.confidence:.2f})",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 0),
                2
            )
        
        # Draw anomaly warning
        if 'anomaly' in results:
            anomaly = results['anomaly']
            cv2.putText(
                annotated,
                f"ANOMALY: {anomaly['type']} ({anomaly['severity']})",
                (10, annotated.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )
        
        return annotated
    
    def _calculate_statistics(
        self,
        objects: List[DetectedObject],
        scenes: List[VideoScene],
        activities: List[Dict[str, Any]],
        anomalies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate analytics statistics"""
        
        stats = {
            'total_objects': len(objects),
            'unique_objects': len(set(obj.class_name for obj in objects)),
            'total_scenes': len(scenes),
            'total_activities': len(activities),
            'total_anomalies': len(anomalies),
            'object_counts': {},
            'activity_counts': {},
            'anomaly_types': {}
        }
        
        # Count objects by type
        for obj in objects:
            if obj.class_name not in stats['object_counts']:
                stats['object_counts'][obj.class_name] = 0
            stats['object_counts'][obj.class_name] += 1
        
        # Count activities
        for activity_data in activities:
            for activity in activity_data['activities']:
                if activity not in stats['activity_counts']:
                    stats['activity_counts'][activity] = 0
                stats['activity_counts'][activity] += 1
        
        # Count anomalies by type
        for anomaly in anomalies:
            anomaly_type = anomaly['type']
            if anomaly_type not in stats['anomaly_types']:
                stats['anomaly_types'][anomaly_type] = 0
            stats['anomaly_types'][anomaly_type] += 1
        
        return stats
    
    def add_result_callback(self, callback: Callable):
        """Add callback for real-time results"""
        self.result_callbacks.append(callback)
    
    def remove_result_callback(self, callback: Callable):
        """Remove result callback"""
        if callback in self.result_callbacks:
            self.result_callbacks.remove(callback)
    
    async def generate_heatmap(
        self,
        video_path: str,
        heatmap_type: str = "motion"
    ) -> np.ndarray:
        """Generate heatmap for video"""
        
        cap = cv2.VideoCapture(video_path)
        
        # Initialize heatmap
        ret, first_frame = cap.read()
        if not ret:
            raise ValueError("Cannot read video")
        
        heatmap = np.zeros((first_frame.shape[0], first_frame.shape[1]), dtype=np.float32)
        frame_count = 0
        
        # Reset video
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        prev_gray = None
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if prev_gray is not None:
                if heatmap_type == "motion":
                    # Motion heatmap
                    flow = cv2.calcOpticalFlowFarneback(
                        prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
                    )
                    magnitude, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
                    heatmap += magnitude
                
                elif heatmap_type == "presence":
                    # Object presence heatmap
                    objects = await self._detect_objects(frame, frame_count, frame_count/30.0)
                    for obj in objects:
                        x, y, w, h = obj.bbox
                        heatmap[y:y+h, x:x+w] += 1
            
            prev_gray = gray
            frame_count += 1
        
        cap.release()
        
        # Normalize heatmap
        heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min() + 1e-8)
        
        return heatmap
    
    async def extract_key_frames(
        self,
        video_path: str,
        num_frames: int = 10,
        method: str = "uniform"
    ) -> List[Tuple[int, np.ndarray]]:
        """Extract key frames from video"""
        
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        key_frames = []
        
        if method == "uniform":
            # Extract frames at uniform intervals
            interval = total_frames // num_frames
            for i in range(num_frames):
                frame_idx = i * interval
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if ret:
                    key_frames.append((frame_idx, frame))
        
        elif method == "scene_change":
            # Extract frames at scene changes
            prev_frame = None
            frame_idx = 0
            
            while cap.isOpened() and len(key_frames) < num_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if prev_frame is not None:
                    # Calculate frame difference
                    diff = cv2.absdiff(frame, prev_frame)
                    diff_score = np.mean(diff)
                    
                    # Detect scene change
                    if diff_score > 30:  # Threshold for scene change
                        key_frames.append((frame_idx, frame))
                
                prev_frame = frame
                frame_idx += 1
        
        cap.release()
        
        return key_frames


# Example usage
async def main():
    """Example usage of video analytics system"""
    
    # Initialize system
    analytics = RealtimeVideoAnalytics(config={'display': True})
    
    # Define callback for real-time results
    def on_frame_analyzed(frame_num: int, results: Dict[str, Any]):
        print(f"Frame {frame_num}: {len(results.get('objects', []))} objects detected")
    
    analytics.add_result_callback(on_frame_analyzed)
    
    # Analyze video
    result = await analytics.analyze_video(
        video_source="sample_video.mp4",
        source_type=VideoSource.FILE,
        analytics_types=[
            AnalyticsType.OBJECT_DETECTION,
            AnalyticsType.ACTIVITY_RECOGNITION,
            AnalyticsType.SCENE_UNDERSTANDING,
            AnalyticsType.ANOMALY_DETECTION
        ],
        real_time=True,
        save_output="annotated_output.mp4"
    )
    
    print(f"Analysis complete!")
    print(f"Total frames: {result.frame_count}")
    print(f"Objects detected: {result.statistics['total_objects']}")
    print(f"Activities recognized: {result.statistics['total_activities']}")
    print(f"Anomalies detected: {result.statistics['total_anomalies']}")
    print(f"Object types: {result.statistics['object_counts']}")
    
    # Generate heatmap
    heatmap = await analytics.generate_heatmap("sample_video.mp4", "motion")
    print(f"Motion heatmap generated: {heatmap.shape}")
    
    # Extract key frames
    key_frames = await analytics.extract_key_frames("sample_video.mp4", 10, "scene_change")
    print(f"Extracted {len(key_frames)} key frames")


if __name__ == "__main__":
    asyncio.run(main())