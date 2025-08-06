#!/usr/bin/env python3
"""
Task 78: Advanced Image Analysis and Insights Generation System

A comprehensive system for analyzing images and generating actionable insights by combining:
- Entity extraction results
- Visual content analysis
- Statistical insights
- Pattern recognition
- Quality assessment
- Semantic understanding
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter, defaultdict
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import statistics
import time
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Try importing advanced ML libraries
try:
    from PIL import Image, ImageStat, ImageFilter
    from PIL.ExifTags import TAGS
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import torch
    import torchvision.transforms as transforms
    from torchvision.models import resnet50, mobilenet_v2
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from sklearn.metrics import silhouette_score
    from scipy import stats
    from scipy.spatial.distance import euclidean
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ColorAnalysis:
    """Color analysis results"""
    dominant_colors: List[Tuple[int, int, int]]
    color_histogram: Dict[str, int]
    color_temperature: str  # warm, cool, neutral
    brightness_level: str   # dark, normal, bright
    contrast_level: str     # low, medium, high
    saturation_level: str   # low, medium, high
    color_diversity: float  # 0-1 score
    
@dataclass 
class CompositionAnalysis:
    """Image composition analysis results"""
    rule_of_thirds_alignment: float  # 0-1 score
    symmetry_score: float           # 0-1 score
    balance_score: float            # 0-1 score
    leading_lines_detected: bool
    depth_of_field_estimate: str    # shallow, medium, deep
    focal_points: List[Tuple[int, int]]
    aspect_ratio: float
    orientation: str                # landscape, portrait, square
    
@dataclass
class ContentAnalysis:
    """Content analysis results"""
    scene_type: str                 # indoor, outdoor, studio, etc.
    scene_complexity: str           # simple, moderate, complex
    primary_subjects: List[str]
    object_count: Dict[str, int]
    text_regions: List[Dict[str, Any]]
    faces_detected: int
    estimated_age_group: Optional[str]
    emotional_tone: Optional[str]
    
@dataclass
class QualityMetrics:
    """Image quality assessment metrics"""
    overall_quality: str            # poor, fair, good, excellent
    sharpness_score: float         # 0-100
    noise_level: str               # low, medium, high
    exposure_quality: str          # underexposed, optimal, overexposed
    white_balance: str             # poor, fair, good
    compression_artifacts: bool
    resolution_quality: str        # low, medium, high
    technical_score: float         # 0-100 overall technical quality
    
@dataclass
class SemanticInsights:
    """Semantic understanding and insights"""
    scene_description: str
    key_themes: List[str]
    emotional_impact: str
    commercial_potential: str       # low, medium, high
    target_audience: List[str]
    content_categories: List[str]
    similar_stock_tags: List[str]
    accessibility_description: str
    
@dataclass
class ComprehensiveImageInsights:
    """Complete image analysis results"""
    file_info: Dict[str, Any]
    color_analysis: ColorAnalysis
    composition_analysis: CompositionAnalysis
    content_analysis: ContentAnalysis
    quality_metrics: QualityMetrics
    semantic_insights: SemanticInsights
    processing_time: float
    analysis_timestamp: str
    confidence_scores: Dict[str, float]

class ImageAnalysisInsightsSystem:
    """Advanced Image Analysis and Insights Generation System"""
    
    def __init__(self, use_gpu: bool = False):
        """
        Initialize the image analysis system
        
        Args:
            use_gpu: Whether to use GPU acceleration if available
        """
        self.use_gpu = use_gpu and torch.cuda.is_available() if TORCH_AVAILABLE else False
        self.device = torch.device('cuda' if self.use_gpu else 'cpu') if TORCH_AVAILABLE else None
        
        # Initialize models if available
        self.models = {}
        self.models_loaded = False
        if TORCH_AVAILABLE:
            self._load_models()
            
        # Color analysis constants
        self.color_names = {
            (255, 0, 0): 'red', (0, 255, 0): 'green', (0, 0, 255): 'blue',
            (255, 255, 0): 'yellow', (255, 0, 255): 'magenta', (0, 255, 255): 'cyan',
            (255, 255, 255): 'white', (0, 0, 0): 'black', (128, 128, 128): 'gray',
            (255, 165, 0): 'orange', (128, 0, 128): 'purple', (165, 42, 42): 'brown',
            (255, 192, 203): 'pink', (0, 128, 0): 'dark_green', (0, 0, 128): 'navy'
        }
        
        logger.info(f"ImageAnalysisSystem initialized with GPU: {self.use_gpu}")
    
    def _load_models(self):
        """Load pre-trained models for analysis"""
        try:
            # Load feature extraction model
            self.models['feature_extractor'] = resnet50(pretrained=True)
            self.models['feature_extractor'].eval()
            
            # Load mobile model for efficient processing
            self.models['mobile_net'] = mobilenet_v2(pretrained=True)
            self.models['mobile_net'].eval()
            
            if self.use_gpu:
                for model in self.models.values():
                    model.to(self.device)
                    
            logger.info("Successfully loaded pre-trained models")
            self.models_loaded = True
        except Exception as e:
            logger.warning(f"Could not load some models: {e}")
            self.models_loaded = False
    
    def analyze_image(self, image_path: Union[str, Path, np.ndarray], options: Optional[Dict[str, Any]] = None) -> ComprehensiveImageInsights:
        """
        Perform comprehensive image analysis and generate insights
        
        Args:
            image_path: Path to image file or numpy array
            options: Analysis options and configuration
            
        Returns:
            ComprehensiveImageInsights: Complete analysis results
        """
        start_time = time.time()
        
        # Handle options
        if options is None:
            options = {}
        
        include_sections = options.get('include_sections', ['all'])
        
        # Load image
        if isinstance(image_path, (str, Path)):
            image_cv2 = cv2.imread(str(image_path))
            image_path_str = str(image_path)
        else:
            image_cv2 = image_path
            image_path_str = "array_input"
            
        if image_cv2 is None or image_cv2.size == 0:
            raise ValueError("Could not load image or image is empty")
            
        # Handle grayscale images
        if len(image_cv2.shape) == 2:
            image_cv2 = cv2.cvtColor(image_cv2, cv2.COLOR_GRAY2BGR)
        elif len(image_cv2.shape) == 3 and image_cv2.shape[2] == 3:
            image_rgb = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image_cv2
        
        # Perform analyses based on options
        file_info = self._extract_file_info(image_path_str, image_cv2)
        
        if 'all' in include_sections or 'color' in include_sections:
            color_analysis = self._analyze_colors(image_rgb)
        else:
            color_analysis = ColorAnalysis([], "neutral", "medium", "medium", "medium", 0.5, {})
        
        if 'all' in include_sections or 'composition' in include_sections:
            composition_analysis = self._analyze_composition(image_cv2, image_rgb)
        else:
            composition_analysis = CompositionAnalysis(1.0, "landscape", 0.5, 0.5, 0.5, [], False, "medium")
        
        if 'all' in include_sections or 'content' in include_sections:
            content_analysis = self._analyze_content(image_cv2, image_rgb)
        else:
            content_analysis = ContentAnalysis("unknown", "simple", [], {}, [], 0, None, "neutral")
        
        if 'all' in include_sections or 'quality' in include_sections:
            quality_metrics = self._assess_quality(image_cv2, image_rgb)
        else:
            quality_metrics = QualityMetrics(50.0, "optimal", "good", "medium", "medium", "fair", 50.0, False)
        
        if 'all' in include_sections or 'semantic' in include_sections:
            semantic_insights = self._generate_semantic_insights(
                image_rgb, color_analysis, composition_analysis, content_analysis
            )
        else:
            semantic_insights = SemanticInsights("Image analysis", [], [], "medium", "neutral", [], "Image for analysis", [])
        
        # Calculate confidence scores
        confidence_scores = self._calculate_confidence_scores(
            color_analysis, composition_analysis, content_analysis, quality_metrics
        )
        
        processing_time = time.time() - start_time
        
        return ComprehensiveImageInsights(
            file_info=file_info,
            color_analysis=color_analysis,
            composition_analysis=composition_analysis,
            content_analysis=content_analysis,
            quality_metrics=quality_metrics,
            semantic_insights=semantic_insights,
            processing_time=processing_time,
            analysis_timestamp=datetime.now().isoformat(),
            confidence_scores=confidence_scores
        )
    
    def _extract_file_info(self, image_path: str, image: np.ndarray) -> Dict[str, Any]:
        """Extract basic file information"""
        info = {
            'file_path': image_path,
            'dimensions': f"{image.shape[1]}x{image.shape[0]}",
            'width': image.shape[1],
            'height': image.shape[0],
            'channels': image.shape[2] if len(image.shape) > 2 else 1,
            'total_pixels': image.shape[0] * image.shape[1],
            'file_size_estimate': image.nbytes,  # Size in memory
            'estimated_format': 'array_input' if image_path == 'array_input' else Path(image_path).suffix.lower().lstrip('.'),
        }
        
        # Try to get file size and EXIF data if it's a real file
        if Path(image_path).exists() and PIL_AVAILABLE:
            try:
                pil_image = Image.open(image_path)
                info['format'] = pil_image.format
                info['mode'] = pil_image.mode
                
                # Extract EXIF data
                exif_data = {}
                if hasattr(pil_image, '_getexif') and pil_image._getexif():
                    exif = pil_image._getexif()
                    for tag_id, value in exif.items():
                        tag = TAGS.get(tag_id, tag_id)
                        exif_data[tag] = str(value)
                info['exif'] = exif_data
                
                # File size
                info['file_size'] = Path(image_path).stat().st_size
            except Exception as e:
                logger.warning(f"Could not extract EXIF data: {e}")
        
        return info
    
    def _analyze_colors(self, image: np.ndarray) -> ColorAnalysis:
        """Analyze color characteristics of the image"""
        # Dominant colors using K-means
        pixels = image.reshape(-1, 3)
        # Sample pixels for performance
        if len(pixels) > 10000:
            indices = np.random.choice(len(pixels), 10000, replace=False)
            pixels = pixels[indices]
        
        try:
            kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
            kmeans.fit(pixels)
            dominant_colors = [tuple(map(int, color)) for color in kmeans.cluster_centers_]
        except:
            # Fallback if clustering fails
            dominant_colors = [(128, 128, 128)]
        
        # Color histogram
        color_hist = {}
        for color in dominant_colors:
            color_name = self._get_closest_color_name(color)
            color_hist[color_name] = color_hist.get(color_name, 0) + 1
            
        # Color temperature
        avg_color = np.mean(image, axis=(0, 1))
        if avg_color[0] > avg_color[2]:  # More red than blue
            color_temp = "warm"
        elif avg_color[2] > avg_color[0]:  # More blue than red
            color_temp = "cool"
        else:
            color_temp = "neutral"
            
        # Brightness level
        brightness = np.mean(cv2.cvtColor(image, cv2.COLOR_RGB2GRAY))
        if brightness < 85:
            brightness_level = "dark"
        elif brightness > 170:
            brightness_level = "bright"
        else:
            brightness_level = "normal"
            
        # Contrast level
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        contrast = np.std(gray)
        if contrast < 30:
            contrast_level = "low"
        elif contrast > 60:
            contrast_level = "high"
        else:
            contrast_level = "medium"
            
        # Saturation level
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        saturation = np.mean(hsv[:, :, 1])
        if saturation < 85:
            saturation_level = "low"
        elif saturation > 170:
            saturation_level = "high"
        else:
            saturation_level = "medium"
            
        # Color diversity (entropy-based)
        hist = cv2.calcHist([image], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        hist_norm = hist / hist.sum()
        entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-10))
        color_diversity = min(entropy / 10.0, 1.0)  # Normalize to 0-1
        
        return ColorAnalysis(
            dominant_colors=dominant_colors,
            color_histogram=color_hist,
            color_temperature=color_temp,
            brightness_level=brightness_level,
            contrast_level=contrast_level,
            saturation_level=saturation_level,
            color_diversity=color_diversity
        )
    
    def _analyze_composition(self, image_bgr: np.ndarray, image_rgb: np.ndarray) -> CompositionAnalysis:
        """Analyze image composition and aesthetic elements"""
        height, width = image_bgr.shape[:2]
        
        # Rule of thirds alignment
        # Check if important features align with rule of thirds lines
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        
        # Detect edges to find composition elements
        edges = cv2.Canny(gray, 50, 150)
        
        # Rule of thirds lines
        third_h = height // 3
        third_w = width // 3
        
        # Count edge pixels near rule of thirds lines
        roi_lines = [
            edges[third_h-5:third_h+5, :],      # Horizontal lines
            edges[2*third_h-5:2*third_h+5, :],
            edges[:, third_w-5:third_w+5],       # Vertical lines
            edges[:, 2*third_w-5:2*third_w+5]
        ]
        
        edge_density = sum(np.sum(roi) for roi in roi_lines) / (40 * max(width, height))
        rule_of_thirds = min(edge_density / 100.0, 1.0)
        
        # Symmetry score
        left_half = gray[:, :width//2]
        right_half = cv2.flip(gray[:, width//2:], 1)
        min_width = min(left_half.shape[1], right_half.shape[1])
        
        if min_width > 0:
            left_resized = cv2.resize(left_half, (min_width, height))
            right_resized = cv2.resize(right_half, (min_width, height))
            symmetry = 1.0 - (np.mean(np.abs(left_resized - right_resized)) / 255.0)
        else:
            symmetry = 0.0
            
        # Balance score (weight distribution)
        moments = cv2.moments(gray)
        if moments['m00'] != 0:
            cx = int(moments['m10'] / moments['m00'])
            cy = int(moments['m01'] / moments['m00'])
            center_x, center_y = width // 2, height // 2
            balance = 1.0 - (abs(cx - center_x) / width + abs(cy - center_y) / height) / 2
        else:
            balance = 0.5
            
        # Leading lines detection
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=width//4, maxLineGap=10)
        leading_lines = lines is not None and len(lines) > 2
        
        # Depth of field estimate (based on blur analysis)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplacian_var > 500:
            dof = "deep"
        elif laplacian_var > 100:
            dof = "medium"
        else:
            dof = "shallow"
            
        # Focal points (using corner detection)
        corners = cv2.goodFeaturesToTrack(gray, maxCorners=5, qualityLevel=0.01, minDistance=30)
        focal_points = [(int(x), int(y)) for [[x, y]] in corners] if corners is not None else []
        
        # Aspect ratio and orientation
        aspect_ratio = width / height
        if abs(aspect_ratio - 1.0) < 0.1:
            orientation = "square"
        elif aspect_ratio > 1.0:
            orientation = "landscape"
        else:
            orientation = "portrait"
            
        return CompositionAnalysis(
            rule_of_thirds_alignment=rule_of_thirds,
            symmetry_score=symmetry,
            balance_score=balance,
            leading_lines_detected=leading_lines,
            depth_of_field_estimate=dof,
            focal_points=focal_points,
            aspect_ratio=aspect_ratio,
            orientation=orientation
        )
    
    def _analyze_content(self, image_bgr: np.ndarray, image_rgb: np.ndarray) -> ContentAnalysis:
        """Analyze image content and detect objects"""
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        
        # Scene type estimation (indoor/outdoor)
        # Based on color temperature and brightness
        avg_color = np.mean(image_rgb, axis=(0, 1))
        brightness = np.mean(gray)
        
        if brightness > 150 and avg_color[2] > avg_color[0]:  # Bright and cool
            scene_type = "outdoor"
        elif brightness < 100:
            scene_type = "indoor"
        else:
            scene_type = "mixed"
            
        # Scene complexity (based on edge density)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        if edge_density < 0.05:
            complexity = "simple"
        elif edge_density > 0.15:
            complexity = "complex"
        else:
            complexity = "moderate"
            
        # Face detection
        try:
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            faces_detected = len(faces)
        except:
            faces_detected = 0
            
        # Text region detection (simple approach)
        # Use MSER for text detection
        try:
            mser = cv2.MSER_create()
            regions, _ = mser.detectRegions(gray)
            text_regions = []
            
            for region in regions:
                if len(region) > 10:  # Filter small regions
                    x, y, w, h = cv2.boundingRect(region.reshape(-1, 1, 2))
                    if w > 20 and h > 10 and w/h > 2:  # Text-like aspect ratio
                        text_regions.append({
                            'bbox': [x, y, w, h],
                            'confidence': 0.7  # Rough estimate
                        })
        except:
            text_regions = []
            
        # Primary subjects (simplified object detection)
        primary_subjects = []
        object_count = {}
        
        # Basic color-based object detection
        hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
        
        # Detect different color regions that might be objects
        color_ranges = {
            'red_objects': [np.array([0, 50, 50]), np.array([10, 255, 255])],
            'green_objects': [np.array([40, 50, 50]), np.array([80, 255, 255])],
            'blue_objects': [np.array([100, 50, 50]), np.array([130, 255, 255])],
        }
        
        for color_name, (lower, upper) in color_ranges.items():
            mask = cv2.inRange(hsv, lower, upper)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            significant_contours = [c for c in contours if cv2.contourArea(c) > 1000]
            
            if significant_contours:
                object_count[color_name] = len(significant_contours)
                primary_subjects.append(color_name)
        
        # Emotional tone estimation
        if faces_detected > 0:
            emotional_tone = "positive"
        elif scene_type == "outdoor" and brightness > 150:
            emotional_tone = "positive"
        elif brightness < 80:
            emotional_tone = "negative"
        else:
            emotional_tone = "neutral"
            
        # Age group estimation (very basic)
        if faces_detected > 0:
            # This is a placeholder - would need more sophisticated analysis
            age_group = "adults"
        else:
            age_group = None
            
        return ContentAnalysis(
            scene_type=scene_type,
            scene_complexity=complexity,
            primary_subjects=primary_subjects,
            object_count=object_count,
            text_regions=text_regions,
            faces_detected=faces_detected,
            estimated_age_group=age_group,
            emotional_tone=emotional_tone
        )
    
    def _assess_quality(self, image_bgr: np.ndarray, image_rgb: np.ndarray) -> QualityMetrics:
        """Assess technical image quality"""
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        
        # Sharpness (Laplacian variance)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharpness_score = min(laplacian_var / 10.0, 100.0)
        
        # Noise level estimation
        noise = cv2.medianBlur(gray, 5)
        noise_diff = cv2.absdiff(gray, noise)
        noise_level_val = np.mean(noise_diff)
        
        if noise_level_val < 5:
            noise_level = "low"
        elif noise_level_val > 15:
            noise_level = "high"
        else:
            noise_level = "medium"
            
        # Exposure quality
        brightness = np.mean(gray)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        
        # Check for clipping
        shadows_clipped = hist[0] > gray.size * 0.01  # 1% of pixels are pure black
        highlights_clipped = hist[255] > gray.size * 0.01  # 1% of pixels are pure white
        
        if shadows_clipped and not highlights_clipped:
            exposure = "underexposed"
        elif highlights_clipped and not shadows_clipped:
            exposure = "overexposed"
        elif shadows_clipped and highlights_clipped:
            exposure = "poor"
        else:
            exposure = "optimal"
            
        # White balance assessment
        b, g, r = cv2.split(image_bgr)
        b_mean, g_mean, r_mean = np.mean(b), np.mean(g), np.mean(r)
        
        # Calculate color cast
        max_channel = max(b_mean, g_mean, r_mean)
        min_channel = min(b_mean, g_mean, r_mean)
        color_cast = (max_channel - min_channel) / max_channel if max_channel > 0 else 0
        
        if color_cast < 0.05:
            white_balance = "good"
        elif color_cast < 0.15:
            white_balance = "fair"
        else:
            white_balance = "poor"
            
        # Compression artifacts detection (simple approach)
        # Look for block artifacts in 8x8 patterns
        compression_artifacts = False
        if image_bgr.shape[0] > 16 and image_bgr.shape[1] > 16:
            # Sample a few 8x8 blocks and check for uniformity
            for i in range(0, min(image_bgr.shape[0] - 8, 64), 8):
                for j in range(0, min(image_bgr.shape[1] - 8, 64), 8):
                    block = gray[i:i+8, j:j+8]
                    if np.std(block) < 2:  # Very uniform block might indicate compression
                        compression_artifacts = True
                        break
                if compression_artifacts:
                    break
                    
        # Resolution quality
        total_pixels = image_bgr.shape[0] * image_bgr.shape[1]
        if total_pixels < 300000:  # Less than ~640x480
            resolution_quality = "low"
        elif total_pixels > 2000000:  # More than ~1600x1200
            resolution_quality = "high"
        else:
            resolution_quality = "medium"
            
        # Overall quality score
        quality_factors = {
            'sharpness': min(sharpness_score / 100.0, 1.0),
            'noise': 1.0 - (noise_level_val / 20.0),
            'exposure': 1.0 if exposure == "optimal" else 0.5,
            'white_balance': {'good': 1.0, 'fair': 0.7, 'poor': 0.3}[white_balance],
            'compression': 0.8 if compression_artifacts else 1.0,
            'resolution': {'high': 1.0, 'medium': 0.8, 'low': 0.5}[resolution_quality]
        }
        
        technical_score = np.mean(list(quality_factors.values())) * 100
        
        if technical_score > 80:
            overall_quality = "excellent"
        elif technical_score > 60:
            overall_quality = "good"
        elif technical_score > 40:
            overall_quality = "fair"
        else:
            overall_quality = "poor"
            
        return QualityMetrics(
            overall_quality=overall_quality,
            sharpness_score=sharpness_score,
            noise_level=noise_level,
            exposure_quality=exposure,
            white_balance=white_balance,
            compression_artifacts=compression_artifacts,
            resolution_quality=resolution_quality,
            technical_score=technical_score
        )
    
    def _generate_semantic_insights(self, image: np.ndarray, color_analysis: ColorAnalysis, 
                                  composition_analysis: CompositionAnalysis, 
                                  content_analysis: ContentAnalysis) -> SemanticInsights:
        """Generate high-level semantic insights about the image"""
        
        # Scene description
        scene_elements = []
        if content_analysis.scene_type == "outdoor":
            scene_elements.append("outdoor scene")
        elif content_analysis.scene_type == "indoor":
            scene_elements.append("indoor environment")
            
        if content_analysis.faces_detected > 0:
            scene_elements.append(f"{content_analysis.faces_detected} person(s)")
            
        if len(content_analysis.text_regions) > 0:
            scene_elements.append("text elements")
            
        scene_description = f"An image showing {', '.join(scene_elements) if scene_elements else 'various visual elements'}"
        
        # Key themes
        themes = []
        if content_analysis.faces_detected > 0:
            themes.append("people")
        if content_analysis.scene_type == "outdoor":
            themes.append("nature")
        if len(content_analysis.text_regions) > 0:
            themes.append("information")
        if color_analysis.color_temperature == "warm":
            themes.append("warmth")
        elif color_analysis.color_temperature == "cool":
            themes.append("coolness")
            
        # Emotional impact
        if content_analysis.emotional_tone == "uplifting":
            emotional_impact = "positive and energetic"
        elif content_analysis.emotional_tone == "moody":
            emotional_impact = "dramatic and atmospheric"
        elif content_analysis.faces_detected > 0:
            emotional_impact = "human-centered and engaging"
        else:
            emotional_impact = "neutral and informative"
            
        # Commercial potential
        commercial_factors = []
        if composition_analysis.rule_of_thirds_alignment > 0.5:
            commercial_factors.append("good composition")
        if len(content_analysis.text_regions) > 0:
            commercial_factors.append("text content")
        if content_analysis.faces_detected > 0:
            commercial_factors.append("human element")
            
        if len(commercial_factors) >= 2:
            commercial_potential = "high"
        elif len(commercial_factors) == 1:
            commercial_potential = "medium"
        else:
            commercial_potential = "low"
            
        # Target audience
        audience = []
        if content_analysis.faces_detected > 0:
            audience.append("general public")
        if content_analysis.scene_type == "outdoor":
            audience.append("nature enthusiasts")
        if len(content_analysis.text_regions) > 0:
            audience.append("readers")
            
        # Content categories
        categories = []
        if content_analysis.faces_detected > 0:
            categories.append("people")
        if content_analysis.scene_type == "outdoor":
            categories.extend(["nature", "landscape"])
        if len(content_analysis.text_regions) > 0:
            categories.extend(["text", "document"])
        if color_analysis.brightness_level == "bright":
            categories.append("lifestyle")
            
        # Stock photo tags
        stock_tags = []
        stock_tags.extend(themes)
        stock_tags.append(color_analysis.color_temperature)
        stock_tags.append(composition_analysis.orientation)
        if content_analysis.scene_complexity == "simple":
            stock_tags.append("minimalist")
        elif content_analysis.scene_complexity == "complex":
            stock_tags.append("detailed")
            
        # Accessibility description
        accessibility_desc = scene_description
        if color_analysis.dominant_colors:
            main_colors = [self._get_closest_color_name(color) for color in color_analysis.dominant_colors[:3]]
            accessibility_desc += f" with predominantly {', '.join(main_colors)} colors"
            
        return SemanticInsights(
            scene_description=scene_description,
            key_themes=themes,
            emotional_impact=emotional_impact,
            commercial_potential=commercial_potential,
            target_audience=audience,
            content_categories=categories,
            similar_stock_tags=stock_tags,
            accessibility_description=accessibility_desc
        )
    
    def _calculate_confidence_scores(self, color_analysis: ColorAnalysis,
                                   composition_analysis: CompositionAnalysis,
                                   content_analysis: ContentAnalysis,
                                   quality_metrics: QualityMetrics) -> Dict[str, float]:
        """Calculate confidence scores for different analysis aspects"""
        
        scores = {}
        
        # Color analysis confidence
        scores['color'] = min(color_analysis.color_diversity * 2, 1.0)
        
        # Composition confidence
        composition_factors = [
            composition_analysis.balance_score,
            composition_analysis.symmetry_score,
            composition_analysis.rule_of_thirds_alignment
        ]
        # Handle case where factors might be strings (defaults)
        numeric_factors = []
        for factor in composition_factors:
            if isinstance(factor, (int, float)):
                numeric_factors.append(factor)
            else:
                numeric_factors.append(0.5)  # Default numeric value
        scores['composition'] = np.mean(numeric_factors)
        
        # Content analysis confidence
        content_confidence = 0.5  # Base confidence
        if content_analysis.faces_detected > 0:
            content_confidence += 0.3
        if len(content_analysis.text_regions) > 0:
            content_confidence += 0.2
        scores['content'] = min(content_confidence, 1.0)
        
        # Quality assessment confidence
        scores['quality'] = quality_metrics.technical_score / 100.0
        
        # Semantic confidence (placeholder)
        scores['semantic'] = 0.75
        
        # Overall confidence
        scores['overall'] = np.mean(list(scores.values()))
        
        return scores
    
    def _get_closest_color_name(self, rgb_color: Tuple[int, int, int]) -> str:
        """Get the closest named color for an RGB value"""
        min_distance = float('inf')
        closest_color = 'unknown'
        
        for named_rgb, name in self.color_names.items():
            distance = sum((a - b) ** 2 for a, b in zip(rgb_color, named_rgb))
            if distance < min_distance:
                min_distance = distance
                closest_color = name
                
        return closest_color
    
    def generate_analysis_report(self, insights: ComprehensiveImageInsights, 
                               output_format: str = 'dict') -> Union[Dict, str, pd.DataFrame]:
        """
        Generate a comprehensive analysis report
        
        Args:
            insights: Analysis results
            output_format: 'dict', 'json', 'html', or 'dataframe'
            
        Returns:
            Report in requested format
        """
        if output_format == 'dict':
            return asdict(insights)
        elif output_format == 'json':
            return json.dumps(asdict(insights), indent=2, default=str)
        elif output_format == 'dataframe' and 'pd' in globals():
            # Flatten the insights for DataFrame
            flat_data = {}
            insights_dict = asdict(insights)
            
            def flatten_dict(d, parent_key='', sep='_'):
                for k, v in d.items():
                    new_key = f"{parent_key}{sep}{k}" if parent_key else k
                    if isinstance(v, dict):
                        flatten_dict(v, new_key, sep)
                    else:
                        flat_data[new_key] = v
                        
            flatten_dict(insights_dict)
            return pd.DataFrame([flat_data])
        elif output_format == 'html':
            return self._generate_html_report(insights)
        else:
            raise ValueError(f"Unsupported format: {output_format}")
    
    def _generate_html_report(self, insights: ComprehensiveImageInsights) -> str:
        """Generate an HTML report"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Image Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .section {{ margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .header {{ background-color: #f5f5f5; font-weight: bold; }}
                .metric {{ margin: 5px 0; }}
                .score {{ color: #2196F3; font-weight: bold; }}
                .good {{ color: #4CAF50; }}
                .warning {{ color: #FF9800; }}
                .poor {{ color: #F44336; }}
            </style>
        </head>
        <body>
            <h1>Image Analysis Report</h1>
            <p><strong>Generated:</strong> {insights.analysis_timestamp}</p>
            <p><strong>Processing Time:</strong> {insights.processing_time:.2f} seconds</p>
            
            <div class="section">
                <div class="header">File Information</div>
                <div class="metric">Dimensions: {insights.file_info['dimensions']}</div>
                <div class="metric">Total Pixels: {insights.file_info['total_pixels']:,}</div>
                <div class="metric">Channels: {insights.file_info['channels']}</div>
            </div>
            
            <div class="section">
                <div class="header">Quality Assessment</div>
                <div class="metric">Overall Quality: <span class="score">{insights.quality_metrics.overall_quality}</span></div>
                <div class="metric">Technical Score: <span class="score">{insights.quality_metrics.technical_score:.1f}/100</span></div>
                <div class="metric">Sharpness: <span class="score">{insights.quality_metrics.sharpness_score:.1f}</span></div>
                <div class="metric">Noise Level: {insights.quality_metrics.noise_level}</div>
                <div class="metric">Exposure: {insights.quality_metrics.exposure_quality}</div>
            </div>
            
            <div class="section">
                <div class="header">Color Analysis</div>
                <div class="metric">Color Temperature: {insights.color_analysis.color_temperature}</div>
                <div class="metric">Brightness: {insights.color_analysis.brightness_level}</div>
                <div class="metric">Contrast: {insights.color_analysis.contrast_level}</div>
                <div class="metric">Saturation: {insights.color_analysis.saturation_level}</div>
                <div class="metric">Color Diversity: <span class="score">{insights.color_analysis.color_diversity:.2f}</span></div>
            </div>
            
            <div class="section">
                <div class="header">Composition Analysis</div>
                <div class="metric">Rule of Thirds: <span class="score">{insights.composition_analysis.rule_of_thirds_alignment:.2f}</span></div>
                <div class="metric">Symmetry Score: <span class="score">{insights.composition_analysis.symmetry_score:.2f}</span></div>
                <div class="metric">Balance Score: <span class="score">{insights.composition_analysis.balance_score:.2f}</span></div>
                <div class="metric">Orientation: {insights.composition_analysis.orientation}</div>
                <div class="metric">Aspect Ratio: {insights.composition_analysis.aspect_ratio:.2f}</div>
            </div>
            
            <div class="section">
                <div class="header">Content Analysis</div>
                <div class="metric">Scene Type: {insights.content_analysis.scene_type}</div>
                <div class="metric">Complexity: {insights.content_analysis.scene_complexity}</div>
                <div class="metric">Faces Detected: {insights.content_analysis.faces_detected}</div>
                <div class="metric">Text Regions: {len(insights.content_analysis.text_regions)}</div>
                <div class="metric">Emotional Tone: {insights.content_analysis.emotional_tone}</div>
            </div>
            
            <div class="section">
                <div class="header">Semantic Insights</div>
                <div class="metric">Description: {insights.semantic_insights.scene_description}</div>
                <div class="metric">Emotional Impact: {insights.semantic_insights.emotional_impact}</div>
                <div class="metric">Commercial Potential: {insights.semantic_insights.commercial_potential}</div>
                <div class="metric">Key Themes: {', '.join(insights.semantic_insights.key_themes)}</div>
                <div class="metric">Target Audience: {', '.join(insights.semantic_insights.target_audience)}</div>
            </div>
            
            <div class="section">
                <div class="header">Confidence Scores</div>
                <div class="metric">Overall Confidence: <span class="score">{insights.confidence_scores['overall']:.2f}</span></div>
                <div class="metric">Color Analysis: <span class="score">{insights.confidence_scores['color']:.2f}</span></div>
                <div class="metric">Composition: <span class="score">{insights.confidence_scores['composition']:.2f}</span></div>
                <div class="metric">Content Analysis: <span class="score">{insights.confidence_scores['content']:.2f}</span></div>
                <div class="metric">Quality Assessment: <span class="score">{insights.confidence_scores['quality']:.2f}</span></div>
            </div>
        </body>
        </html>
        """
        return html
    
    def batch_analyze_images(self, image_paths: List[Union[str, Path]], 
                           progress_callback: Optional[callable] = None) -> List[ComprehensiveImageInsights]:
        """
        Analyze multiple images in batch
        
        Args:
            image_paths: List of image paths
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of analysis results
        """
        results = []
        total = len(image_paths)
        
        for i, image_path in enumerate(image_paths):
            try:
                insights = self.analyze_image(image_path)
                results.append(insights)
                
                if progress_callback:
                    progress_callback(i + 1, total, str(image_path))
                    
            except Exception as e:
                logger.error(f"Failed to analyze {image_path}: {e}")
                
        return results
    
    def save_insights(self, insights: ComprehensiveImageInsights, output_path: Union[str, Path]):
        """Save insights to file"""
        output_path = Path(output_path)
        
        if output_path.suffix.lower() == '.json':
            with open(output_path, 'w') as f:
                json.dump(asdict(insights), f, indent=2, default=str)
        elif output_path.suffix.lower() == '.html':
            with open(output_path, 'w') as f:
                f.write(self.generate_analysis_report(insights, 'html'))
        elif output_path.suffix.lower() == '.csv' and 'pd' in globals():
            df = self.generate_analysis_report(insights, 'dataframe')
            df.to_csv(output_path, index=False)
        else:
            raise ValueError(f"Unsupported file format: {output_path.suffix}")
    
    def batch_analyze(self, images: List[np.ndarray]) -> List[ComprehensiveImageInsights]:
        """
        Perform batch analysis on multiple images
        
        Args:
            images: List of images as numpy arrays
            
        Returns:
            List of ComprehensiveImageInsights
        """
        results = []
        for i, image in enumerate(images):
            logger.info(f"Analyzing image {i+1}/{len(images)}")
            result = self.analyze_image(image)
            results.append(result)
        return results
    
    def compare_images(self, image1: np.ndarray, image2: np.ndarray) -> Dict[str, Any]:
        """
        Compare two images and generate comparison analysis
        
        Args:
            image1: First image as numpy array
            image2: Second image as numpy array
            
        Returns:
            Dictionary containing comparison results
        """
        # Analyze both images
        insights1 = self.analyze_image(image1)
        insights2 = self.analyze_image(image2)
        
        comparison = {
            'image_1': {},
            'image_2': {},
            'differences': {},
            'similarities': {}
        }
        
        # Quality comparison
        comparison['image_1']['quality'] = insights1.quality_metrics.__dict__
        comparison['image_2']['quality'] = insights2.quality_metrics.__dict__
        
        comparison['differences']['quality_score'] = {
            'image_1': insights1.quality_metrics.technical_score,
            'image_2': insights2.quality_metrics.technical_score,
            'difference': abs(insights1.quality_metrics.technical_score - insights2.quality_metrics.technical_score),
            'better_image': 'image_1' if insights1.quality_metrics.technical_score > insights2.quality_metrics.technical_score else 'image_2'
        }
        
        # Composition comparison
        comp1_avg = (insights1.composition_analysis.rule_of_thirds_alignment + 
                     insights1.composition_analysis.symmetry_score + 
                     insights1.composition_analysis.balance_score) / 3
        comp2_avg = (insights2.composition_analysis.rule_of_thirds_alignment + 
                     insights2.composition_analysis.symmetry_score + 
                     insights2.composition_analysis.balance_score) / 3
        
        comparison['differences']['composition_score'] = {
            'image_1': comp1_avg,
            'image_2': comp2_avg,
            'difference': abs(comp1_avg - comp2_avg),
            'better_image': 'image_1' if comp1_avg > comp2_avg else 'image_2'
        }
        
        # Color similarities
        comparison['similarities']['color_temperature'] = insights1.color_analysis.color_temperature == insights2.color_analysis.color_temperature
        comparison['similarities']['brightness_level'] = insights1.color_analysis.brightness_level == insights2.color_analysis.brightness_level
        
        return comparison
    
    def export_analysis(self, insights: ComprehensiveImageInsights, format: str = 'json') -> Union[str, Dict[str, Any]]:
        """
        Export analysis results in specified format
        
        Args:
            insights: Analysis results to export
            format: Export format ('json', 'csv', 'html')
            
        Returns:
            Exported data as string or dictionary
        """
        if format == 'json':
            return asdict(insights)
        elif format == 'csv':
            # Flatten the nested structure for CSV
            flat_data = {}
            
            def flatten_dict(d, parent_key='', sep='_'):
                for k, v in d.items():
                    new_key = f"{parent_key}{sep}{k}" if parent_key else k
                    if isinstance(v, dict):
                        flatten_dict(v, new_key, sep)
                    elif isinstance(v, list):
                        flat_data[new_key] = str(v)
                    else:
                        flat_data[new_key] = v
            
            insights_dict = asdict(insights)
            flatten_dict(insights_dict)
            
            # Convert to CSV format
            csv_lines = ["metric,value"]
            for key, value in flat_data.items():
                csv_lines.append(f"{key},{value}")
            
            return "\n".join(csv_lines)
        elif format == 'html':
            return self.generate_analysis_report(insights, 'html')
        else:
            raise ValueError(f"Unsupported export format: {format}")

def main():
    """Demo function to test the system"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Image Analysis and Insights System")
    parser.add_argument('image_path', help='Path to image file')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--format', '-f', choices=['json', 'html', 'csv'], default='json', help='Output format')
    parser.add_argument('--gpu', action='store_true', help='Use GPU if available')
    
    args = parser.parse_args()
    
    # Initialize system
    system = ImageAnalysisInsightsSystem(use_gpu=args.gpu)
    
    # Analyze image
    print(f"Analyzing image: {args.image_path}")
    insights = system.analyze_image(args.image_path)
    
    # Print summary
    print(f"\n=== Analysis Summary ===")
    print(f"Overall Quality: {insights.quality_metrics.overall_quality}")
    print(f"Technical Score: {insights.quality_metrics.technical_score:.1f}/100")
    print(f"Scene Type: {insights.content_analysis.scene_type}")
    print(f"Complexity: {insights.content_analysis.scene_complexity}")
    print(f"Faces Detected: {insights.content_analysis.faces_detected}")
    print(f"Commercial Potential: {insights.semantic_insights.commercial_potential}")
    print(f"Processing Time: {insights.processing_time:.2f} seconds")
    print(f"Overall Confidence: {insights.confidence_scores['overall']:.2f}")
    
    # Save results if requested
    if args.output:
        if args.format == 'json':
            output_path = Path(args.output).with_suffix('.json')
        elif args.format == 'html':
            output_path = Path(args.output).with_suffix('.html')
        elif args.format == 'csv':
            output_path = Path(args.output).with_suffix('.csv')
        
        system.save_insights(insights, output_path)
        print(f"Results saved to: {output_path}")

if __name__ == "__main__":
    main()