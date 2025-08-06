"""
Advanced Image-Based Entity Extraction and Analysis System
Comprehensive implementation with multiple open source options, libraries, and Hugging Face models
for visual entity detection, image metadata extraction, and content analysis.
"""

import streamlit as st
import cv2
import numpy as np
import pandas as pd
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS
import spacy
from typing import Dict, List, Tuple, Optional, Any, Union
import json
import re
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import base64
import io
import datetime
import hashlib
import os
from pathlib import Path

# Computer Vision and Image Processing
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy import ndimage
import skimage
from skimage import filters, morphology, measure, feature, segmentation
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics.pairwise import cosine_similarity

# Advanced ML and AI Models
from transformers import (
    AutoTokenizer, AutoModel, AutoProcessor, AutoImageProcessor,
    CLIPProcessor, CLIPModel, BlipProcessor, BlipForConditionalGeneration,
    DetrImageProcessor, DetrForObjectDetection,
    ViTImageProcessor, ViTForImageClassification
)
import torch
import torchvision.transforms as transforms
from torchvision.models import resnet50, ResNet50_Weights

# YOLO for object detection
try:
    import ultralytics
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

# Google Vision API (optional)
try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EntityType(Enum):
    """Visual entity types"""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    DATE = "date"
    MONEY = "money"
    PRODUCT = "product"
    LOGO = "logo"
    SIGNATURE = "signature"
    STAMP = "stamp"
    BARCODE = "barcode"
    QR_CODE = "qr_code"
    CHART = "chart"
    GRAPH = "graph"
    DIAGRAM = "diagram"
    TABLE = "table"
    TEXT_BLOCK = "text_block"
    IMAGE = "image"
    UNKNOWN = "unknown"

class ImageQuality(Enum):
    """Image quality assessment levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    VERY_POOR = "very_poor"

@dataclass
class BoundingBox:
    """Bounding box coordinates"""
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float = 0.0

@dataclass
class VisualEntity:
    """Visual entity detected in image"""
    entity_type: EntityType
    text: str
    bbox: BoundingBox
    confidence: float
    metadata: Dict[str, Any]

@dataclass
class ImageMetadata:
    """Comprehensive image metadata"""
    filename: str
    file_size: int
    dimensions: Tuple[int, int]
    format: str
    mode: str
    creation_date: Optional[datetime.datetime]
    camera_make: Optional[str]
    camera_model: Optional[str]
    gps_coordinates: Optional[Tuple[float, float]]
    orientation: Optional[int]
    color_space: Optional[str]
    dpi: Optional[Tuple[int, int]]
    compression: Optional[str]
    software: Optional[str]
    artist: Optional[str]
    copyright: Optional[str]
    keywords: List[str]
    description: Optional[str]

@dataclass
class ImageQualityAssessment:
    """Image quality assessment results"""
    overall_quality: ImageQuality
    sharpness_score: float
    brightness_score: float
    contrast_score: float
    noise_level: float
    blur_detection: float
    color_balance: Dict[str, float]
    histogram_analysis: Dict[str, Any]
    recommendations: List[str]

@dataclass
class VisualContent:
    """Visual content analysis results"""
    content_type: str
    description: str
    objects_detected: List[Dict[str, Any]]
    scene_classification: str
    dominant_colors: List[Tuple[int, int, int]]
    text_regions: List[BoundingBox]
    faces_detected: int
    landmarks: List[Dict[str, Any]]
    face_identities: List[Dict[str, Any]]
    scene_analysis: Dict[str, Any]
    logos_brands: List[Dict[str, Any]]
    safety_assessment: Dict[str, Any]

@dataclass
class ImageAnalysisResult:
    """Complete image analysis result"""
    visual_entities: List[VisualEntity]
    metadata: ImageMetadata
    quality_assessment: ImageQualityAssessment
    visual_content: VisualContent
    extracted_text: str
    confidence: float

class ImageEntityExtractionSystem:
    """Advanced image-based entity extraction and analysis system"""
    
    def __init__(self):
        self.setup_models()
        self.setup_nlp()
        self.setup_computer_vision()
        self.setup_face_recognition()
        self.setup_content_moderation()
        
    def setup_models(self):
        """Initialize AI models with progress indicators"""
        try:
            print("🔄 Loading AI models... This may take a few minutes on first run.")
            
            # CLIP for image-text understanding
            print("   📥 Loading CLIP model for image-text understanding...")
            self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            print("   ✅ CLIP model loaded successfully")
            
            # BLIP for image captioning
            print("   📥 Loading BLIP model for image captioning...")
            self.blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            self.blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
            print("   ✅ BLIP model loaded successfully")
            
            # DETR for object detection
            print("   📥 Loading DETR model for object detection...")
            self.detr_processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
            self.detr_model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50")
            print("   ✅ DETR model loaded successfully")
            
            # ViT for image classification
            print("   📥 Loading ViT model for image classification...")
            self.vit_processor = ViTImageProcessor.from_pretrained("google/vit-base-patch16-224")
            self.vit_model = ViTForImageClassification.from_pretrained("google/vit-base-patch16-224")
            print("   ✅ ViT model loaded successfully")
            
            # ResNet for feature extraction
            print("   📥 Loading ResNet model for feature extraction...")
            self.resnet_model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)
            self.resnet_model.eval()
            print("   ✅ ResNet model loaded successfully")
            
            # YOLO for object detection (if available)
            if YOLO_AVAILABLE:
                print("   📥 Loading YOLO model for real-time object detection...")
                self.yolo_model = YOLO('yolov8n.pt')
                print("   ✅ YOLO model loaded successfully")
            else:
                print("   ⚠️ YOLO not available - skipping")
                self.yolo_model = None
            
            print("🎉 All AI models loaded successfully!")
            logger.info("AI models loaded successfully")
            
        except Exception as e:
            print(f"❌ Error loading AI models: {e}")
            print("💡 This might be due to:")
            print("   - First-time model download (requires internet)")
            print("   - Missing dependencies (run: pip install -r requirements.txt)")
            print("   - Insufficient disk space for model files")
            logger.error(f"Error loading AI models: {e}")
            # Set fallback None values
            self.clip_processor = None
            self.clip_model = None
    
    def setup_nlp(self):
        """Initialize NLP models for text entity extraction"""
        try:
            # Load spaCy model for NER
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("NLP models loaded successfully")
        except Exception as e:
            logger.error(f"Error loading NLP models: {e}")
            self.nlp = None
    
    def setup_computer_vision(self):
        """Initialize computer vision components"""
        try:
            # Initialize feature detectors
            self.sift = cv2.SIFT_create()
            self.orb = cv2.ORB_create()
            
            # Initialize cascade classifiers
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            # QR Code and Barcode detector
            self.qr_detector = cv2.QRCodeDetector()
            
            logger.info("Computer vision components initialized")
            
        except Exception as e:
            logger.error(f"Error initializing computer vision: {e}")
    
    def setup_face_recognition(self):
        """Initialize face recognition capabilities"""
        try:
            # Initialize face recognition models
            import face_recognition
            self.face_recognition_available = True
            logger.info("Face recognition initialized")
        except ImportError:
            self.face_recognition_available = False
            logger.warning("face_recognition library not available")
        except Exception as e:
            logger.error(f"Error initializing face recognition: {e}")
            self.face_recognition_available = False
    
    def setup_content_moderation(self):
        """Initialize content moderation capabilities"""
        try:
            # Content safety keywords and patterns
            self.unsafe_content_patterns = [
                r'\b(violence|weapon|gun|knife|blood)\b',
                r'\b(nude|naked|explicit|sexual)\b',
                r'\b(drug|cocaine|marijuana|heroin)\b',
                r'\b(hate|racist|nazi|terrorist)\b'
            ]
            
            # Brand and logo detection patterns
            self.brand_patterns = [
                r'\b(coca.?cola|pepsi|mcdonalds|apple|google|microsoft|amazon)\b',
                r'\b(nike|adidas|puma|reebok)\b',
                r'\b(facebook|instagram|twitter|tiktok|youtube)\b'
            ]
            
            logger.info("Content moderation initialized")
        except Exception as e:
            logger.error(f"Error initializing content moderation: {e}")
    
    def extract_image_metadata(self, image_path: str, image: Image.Image) -> ImageMetadata:
        """Extract comprehensive metadata from image"""
        try:
            # Basic image information
            filename = os.path.basename(image_path) if image_path else "unknown"
            file_size = os.path.getsize(image_path) if image_path and os.path.exists(image_path) else 0
            dimensions = image.size
            format_type = image.format or "unknown"
            mode = image.mode
            
            # EXIF data extraction
            exif_data = {}
            if hasattr(image, '_getexif') and image._getexif():
                exif = image._getexif()
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = value
            
            # Parse specific EXIF fields
            creation_date = None
            if 'DateTime' in exif_data:
                try:
                    creation_date = datetime.datetime.strptime(exif_data['DateTime'], '%Y:%m:%d %H:%M:%S')
                except:
                    pass
            
            camera_make = exif_data.get('Make')
            camera_model = exif_data.get('Model')
            software = exif_data.get('Software')
            artist = exif_data.get('Artist')
            copyright_info = exif_data.get('Copyright')
            
            # GPS coordinates
            gps_coordinates = None
            if 'GPSInfo' in exif_data:
                gps_info = exif_data['GPSInfo']
                gps_coordinates = self._parse_gps_coordinates(gps_info)
            
            # Image properties
            orientation = exif_data.get('Orientation')
            color_space = exif_data.get('ColorSpace')
            
            # DPI information
            dpi = None
            if hasattr(image, 'info') and 'dpi' in image.info:
                dpi = image.info['dpi']
            
            return ImageMetadata(
                filename=filename,
                file_size=file_size,
                dimensions=dimensions,
                format=format_type,
                mode=mode,
                creation_date=creation_date,
                camera_make=camera_make,
                camera_model=camera_model,
                gps_coordinates=gps_coordinates,
                orientation=orientation,
                color_space=color_space,
                dpi=dpi,
                compression=exif_data.get('Compression'),
                software=software,
                artist=artist,
                copyright=copyright_info,
                keywords=[],  # Could be extracted from IPTC data
                description=exif_data.get('ImageDescription')
            )
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return ImageMetadata(
                filename=filename if 'filename' in locals() else "unknown",
                file_size=0,
                dimensions=(0, 0),
                format="unknown",
                mode="unknown",
                creation_date=None,
                camera_make=None,
                camera_model=None,
                gps_coordinates=None,
                orientation=None,
                color_space=None,
                dpi=None,
                compression=None,
                software=None,
                artist=None,
                copyright=None,
                keywords=[],
                description=None
            )
    
    def _parse_gps_coordinates(self, gps_info: Dict) -> Optional[Tuple[float, float]]:
        """Parse GPS coordinates from EXIF data"""
        try:
            def convert_to_degrees(value):
                d, m, s = value
                return d + (m / 60.0) + (s / 3600.0)
            
            lat = convert_to_degrees(gps_info[2])
            if gps_info[1] == 'S':
                lat = -lat
                
            lon = convert_to_degrees(gps_info[4])
            if gps_info[3] == 'W':
                lon = -lon
                
            return (lat, lon)
        except:
            return None
    
    def assess_image_quality(self, image: np.ndarray) -> ImageQualityAssessment:
        """Comprehensive image quality assessment"""
        try:
            # Convert to grayscale for analysis
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Sharpness assessment using Laplacian variance
            sharpness_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Brightness assessment
            brightness_score = np.mean(gray)
            
            # Contrast assessment using standard deviation
            contrast_score = np.std(gray)
            
            # Noise level estimation
            noise_level = self._estimate_noise_level(gray)
            
            # Blur detection using gradient magnitude
            blur_detection = self._detect_blur(gray)
            
            # Color balance analysis
            color_balance = self._analyze_color_balance(image)
            
            # Histogram analysis
            histogram_analysis = self._analyze_histogram(image)
            
            # Overall quality score
            quality_score = self._calculate_overall_quality(
                sharpness_score, brightness_score, contrast_score, 
                noise_level, blur_detection
            )
            
            # Generate recommendations
            recommendations = self._generate_quality_recommendations(
                sharpness_score, brightness_score, contrast_score,
                noise_level, blur_detection, color_balance
            )
            
            return ImageQualityAssessment(
                overall_quality=quality_score,
                sharpness_score=sharpness_score,
                brightness_score=brightness_score,
                contrast_score=contrast_score,
                noise_level=noise_level,
                blur_detection=blur_detection,
                color_balance=color_balance,
                histogram_analysis=histogram_analysis,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error in quality assessment: {e}")
            return ImageQualityAssessment(
                overall_quality=ImageQuality.UNKNOWN,
                sharpness_score=0.0,
                brightness_score=0.0,
                contrast_score=0.0,
                noise_level=0.0,
                blur_detection=0.0,
                color_balance={},
                histogram_analysis={},
                recommendations=["Error in quality assessment"]
            )
    
    def _estimate_noise_level(self, image: np.ndarray) -> float:
        """Estimate noise level in image"""
        try:
            # Use Laplacian to estimate noise
            laplacian = cv2.Laplacian(image, cv2.CV_64F)
            noise_level = np.var(laplacian)
            return float(noise_level)
        except:
            return 0.0
    
    def _detect_blur(self, image: np.ndarray) -> float:
        """Detect blur in image using gradient magnitude"""
        try:
            # Calculate gradient magnitude
            grad_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            blur_score = np.mean(gradient_magnitude)
            return float(blur_score)
        except:
            return 0.0
    
    def _analyze_color_balance(self, image: np.ndarray) -> Dict[str, float]:
        """Analyze color balance in image"""
        try:
            if len(image.shape) == 3:
                # Calculate mean values for each channel
                b_mean = np.mean(image[:, :, 0])
                g_mean = np.mean(image[:, :, 1])
                r_mean = np.mean(image[:, :, 2])
                
                return {
                    'red_balance': float(r_mean),
                    'green_balance': float(g_mean),
                    'blue_balance': float(b_mean),
                    'color_cast': float(abs(r_mean - g_mean) + abs(g_mean - b_mean) + abs(b_mean - r_mean))
                }
            else:
                return {'grayscale': float(np.mean(image))}
        except:
            return {}
    
    def _analyze_histogram(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze image histogram"""
        try:
            if len(image.shape) == 3:
                # Color histogram
                hist_b = cv2.calcHist([image], [0], None, [256], [0, 256])
                hist_g = cv2.calcHist([image], [1], None, [256], [0, 256])
                hist_r = cv2.calcHist([image], [2], None, [256], [0, 256])
                
                return {
                    'red_histogram': hist_r.flatten().tolist(),
                    'green_histogram': hist_g.flatten().tolist(),
                    'blue_histogram': hist_b.flatten().tolist(),
                    'dynamic_range': float(np.max(image) - np.min(image))
                }
            else:
                # Grayscale histogram
                hist = cv2.calcHist([image], [0], None, [256], [0, 256])
                return {
                    'grayscale_histogram': hist.flatten().tolist(),
                    'dynamic_range': float(np.max(image) - np.min(image))
                }
        except:
            return {}
    
    def _calculate_overall_quality(self, sharpness: float, brightness: float, 
                                 contrast: float, noise: float, blur: float) -> ImageQuality:
        """Calculate overall image quality score"""
        try:
            # Normalize scores (this is a simplified approach)
            sharpness_norm = min(sharpness / 1000, 1.0)  # Normalize sharpness
            brightness_norm = 1.0 - abs(brightness - 128) / 128  # Optimal brightness around 128
            contrast_norm = min(contrast / 64, 1.0)  # Normalize contrast
            noise_norm = max(0, 1.0 - noise / 1000)  # Lower noise is better
            blur_norm = min(blur / 100, 1.0)  # Higher gradient magnitude is better
            
            # Weighted average
            overall_score = (
                sharpness_norm * 0.3 +
                brightness_norm * 0.2 +
                contrast_norm * 0.2 +
                noise_norm * 0.15 +
                blur_norm * 0.15
            )
            
            if overall_score >= 0.8:
                return ImageQuality.EXCELLENT
            elif overall_score >= 0.6:
                return ImageQuality.GOOD
            elif overall_score >= 0.4:
                return ImageQuality.FAIR
            elif overall_score >= 0.2:
                return ImageQuality.POOR
            else:
                return ImageQuality.VERY_POOR
                
        except:
            return ImageQuality.UNKNOWN
    
    def _generate_quality_recommendations(self, sharpness: float, brightness: float,
                                        contrast: float, noise: float, blur: float,
                                        color_balance: Dict[str, float]) -> List[str]:
        """Generate image quality improvement recommendations"""
        recommendations = []
        
        try:
            if sharpness < 100:
                recommendations.append("Image appears soft - consider using sharpening filters")
            
            if brightness < 80:
                recommendations.append("Image is too dark - increase brightness")
            elif brightness > 180:
                recommendations.append("Image is too bright - decrease brightness")
            
            if contrast < 30:
                recommendations.append("Low contrast detected - consider contrast enhancement")
            
            if noise > 500:
                recommendations.append("High noise level detected - apply noise reduction")
            
            if blur < 20:
                recommendations.append("Motion blur detected - use faster shutter speed")
            
            if 'color_cast' in color_balance and color_balance['color_cast'] > 30:
                recommendations.append("Color cast detected - adjust white balance")
            
            if not recommendations:
                recommendations.append("Image quality is good - no major improvements needed")
                
        except:
            recommendations.append("Unable to generate quality recommendations")
        
        return recommendations    

    def detect_visual_entities(self, image: np.ndarray, extracted_text: str) -> List[VisualEntity]:
        """Detect visual entities in image"""
        entities = []
        
        try:
            # Method 1: Extract entities from OCR text using NLP
            text_entities = self._extract_text_entities(extracted_text)
            entities.extend(text_entities)
            
            # Method 2: Detect visual objects using YOLO
            if self.yolo_model:
                yolo_entities = self._detect_yolo_objects(image)
                entities.extend(yolo_entities)
            
            # Method 3: Detect objects using DETR
            if self.detr_model:
                detr_entities = self._detect_detr_objects(image)
                entities.extend(detr_entities)
            
            # Method 4: Detect logos and signatures
            logo_entities = self._detect_logos_signatures(image)
            entities.extend(logo_entities)
            
            # Method 5: Detect QR codes and barcodes
            code_entities = self._detect_codes(image)
            entities.extend(code_entities)
            
            # Method 6: Detect charts and graphs
            chart_entities = self._detect_charts_graphs(image)
            entities.extend(chart_entities)
            
        except Exception as e:
            logger.error(f"Error in visual entity detection: {e}")
        
        return entities
    
    def _extract_text_entities(self, text: str) -> List[VisualEntity]:
        """Extract entities from text using NLP"""
        entities = []
        
        if not self.nlp or not text:
            return entities
        
        try:
            doc = self.nlp(text)
            
            for ent in doc.ents:
                entity_type = self._map_spacy_to_visual_entity(ent.label_)
                
                entity = VisualEntity(
                    entity_type=entity_type,
                    text=ent.text,
                    bbox=BoundingBox(0, 0, 0, 0, 0.8),  # Text entities don't have visual bbox
                    confidence=0.8,
                    metadata={
                        'source': 'nlp',
                        'spacy_label': ent.label_,
                        'start_char': ent.start_char,
                        'end_char': ent.end_char
                    }
                )
                entities.append(entity)
                
        except Exception as e:
            logger.error(f"Error extracting text entities: {e}")
        
        return entities
    
    def _map_spacy_to_visual_entity(self, spacy_label: str) -> EntityType:
        """Map spaCy entity labels to visual entity types"""
        mapping = {
            'PERSON': EntityType.PERSON,
            'ORG': EntityType.ORGANIZATION,
            'GPE': EntityType.LOCATION,
            'LOC': EntityType.LOCATION,
            'DATE': EntityType.DATE,
            'TIME': EntityType.DATE,
            'MONEY': EntityType.MONEY,
            'PRODUCT': EntityType.PRODUCT,
        }
        return mapping.get(spacy_label, EntityType.UNKNOWN)
    
    def _detect_yolo_objects(self, image: np.ndarray) -> List[VisualEntity]:
        """Detect objects using YOLO"""
        entities = []
        
        if not self.yolo_model:
            return entities
        
        try:
            results = self.yolo_model(image)
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get bounding box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = float(box.conf[0].cpu().numpy())
                        class_id = int(box.cls[0].cpu().numpy())
                        
                        # Get class name
                        class_name = self.yolo_model.names[class_id]
                        
                        entity = VisualEntity(
                            entity_type=self._map_yolo_to_entity_type(class_name),
                            text=class_name,
                            bbox=BoundingBox(int(x1), int(y1), int(x2), int(y2), confidence),
                            confidence=confidence,
                            metadata={
                                'source': 'yolo',
                                'class_id': class_id,
                                'class_name': class_name
                            }
                        )
                        entities.append(entity)
                        
        except Exception as e:
            logger.error(f"Error in YOLO detection: {e}")
        
        return entities
    
    def _detect_detr_objects(self, image: np.ndarray) -> List[VisualEntity]:
        """Detect objects using DETR"""
        entities = []
        
        if not self.detr_model or not self.detr_processor:
            return entities
        
        try:
            # Convert numpy array to PIL Image
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            # Process image
            inputs = self.detr_processor(images=pil_image, return_tensors="pt")
            
            with torch.no_grad():
                outputs = self.detr_model(**inputs)
            
            # Process results
            target_sizes = torch.tensor([pil_image.size[::-1]])
            results = self.detr_processor.post_process_object_detection(
                outputs, target_sizes=target_sizes, threshold=0.5
            )[0]
            
            for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
                if score > 0.5:
                    x1, y1, x2, y2 = box.cpu().numpy()
                    class_name = self.detr_model.config.id2label[label.item()]
                    
                    entity = VisualEntity(
                        entity_type=self._map_detr_to_entity_type(class_name),
                        text=class_name,
                        bbox=BoundingBox(int(x1), int(y1), int(x2), int(y2), float(score)),
                        confidence=float(score),
                        metadata={
                            'source': 'detr',
                            'label_id': label.item(),
                            'class_name': class_name
                        }
                    )
                    entities.append(entity)
                    
        except Exception as e:
            logger.error(f"Error in DETR detection: {e}")
        
        return entities
    
    def _detect_logos_signatures(self, image: np.ndarray) -> List[VisualEntity]:
        """Detect logos and signatures using computer vision"""
        entities = []
        
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            
            # Detect potential logo regions using template matching and feature detection
            # This is a simplified approach - in production, you'd use trained models
            
            # Find contours that might be logos or signatures
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 500 < area < 10000:  # Filter by size
                    # Get bounding rectangle
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Analyze shape characteristics
                    aspect_ratio = w / h
                    extent = area / (w * h)
                    
                    # Heuristics for logo/signature detection
                    if 0.3 < aspect_ratio < 3.0 and extent > 0.3:
                        # Extract region for further analysis
                        roi = gray[y:y+h, x:x+w]
                        
                        # Simple signature detection based on stroke patterns
                        if self._is_signature_like(roi):
                            entity = VisualEntity(
                                entity_type=EntityType.SIGNATURE,
                                text="signature",
                                bbox=BoundingBox(x, y, x+w, y+h, 0.6),
                                confidence=0.6,
                                metadata={
                                    'source': 'cv_signature',
                                    'area': area,
                                    'aspect_ratio': aspect_ratio
                                }
                            )
                            entities.append(entity)
                        elif self._is_logo_like(roi):
                            entity = VisualEntity(
                                entity_type=EntityType.LOGO,
                                text="logo",
                                bbox=BoundingBox(x, y, x+w, y+h, 0.6),
                                confidence=0.6,
                                metadata={
                                    'source': 'cv_logo',
                                    'area': area,
                                    'aspect_ratio': aspect_ratio
                                }
                            )
                            entities.append(entity)
                            
        except Exception as e:
            logger.error(f"Error detecting logos/signatures: {e}")
        
        return entities
    
    def _is_signature_like(self, roi: np.ndarray) -> bool:
        """Heuristic to determine if region looks like a signature"""
        try:
            # Signatures typically have:
            # - Irregular, flowing lines
            # - Lower density than printed text
            # - Connected components
            
            # Calculate line density
            edges = cv2.Canny(roi, 50, 150)
            line_density = np.sum(edges > 0) / (roi.shape[0] * roi.shape[1])
            
            # Check for connected components
            num_labels, _ = cv2.connectedComponents(edges)
            
            # Simple heuristics
            return 0.05 < line_density < 0.3 and num_labels < 10
            
        except:
            return False
    
    def _is_logo_like(self, roi: np.ndarray) -> bool:
        """Heuristic to determine if region looks like a logo"""
        try:
            # Logos typically have:
            # - Geometric shapes
            # - Higher contrast
            # - Distinct boundaries
            
            # Calculate contrast
            contrast = np.std(roi)
            
            # Check for geometric shapes using contour analysis
            edges = cv2.Canny(roi, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            geometric_shapes = 0
            for contour in contours:
                # Approximate contour to polygon
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Count geometric shapes (triangles, rectangles, etc.)
                if 3 <= len(approx) <= 8:
                    geometric_shapes += 1
            
            return contrast > 30 and geometric_shapes > 0
            
        except:
            return False
    
    def _detect_codes(self, image: np.ndarray) -> List[VisualEntity]:
        """Detect QR codes and barcodes"""
        entities = []
        
        try:
            # QR Code detection
            data, bbox, _ = self.qr_detector.detectAndDecode(image)
            if data and bbox is not None:
                # Convert bbox to our format
                x_coords = bbox[0][:, 0]
                y_coords = bbox[0][:, 1]
                x1, y1 = int(np.min(x_coords)), int(np.min(y_coords))
                x2, y2 = int(np.max(x_coords)), int(np.max(y_coords))
                
                entity = VisualEntity(
                    entity_type=EntityType.QR_CODE,
                    text=data,
                    bbox=BoundingBox(x1, y1, x2, y2, 0.9),
                    confidence=0.9,
                    metadata={
                        'source': 'qr_detector',
                        'decoded_data': data
                    }
                )
                entities.append(entity)
            
            # Barcode detection (simplified approach)
            # In production, you'd use libraries like pyzbar
            barcode_regions = self._detect_barcode_regions(image)
            for region in barcode_regions:
                entity = VisualEntity(
                    entity_type=EntityType.BARCODE,
                    text="barcode",
                    bbox=region['bbox'],
                    confidence=region['confidence'],
                    metadata={
                        'source': 'barcode_detector',
                        'type': 'generic'
                    }
                )
                entities.append(entity)
                
        except Exception as e:
            logger.error(f"Error detecting codes: {e}")
        
        return entities
    
    def _detect_barcode_regions(self, image: np.ndarray) -> List[Dict]:
        """Detect potential barcode regions"""
        regions = []
        
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            
            # Barcodes have characteristic horizontal line patterns
            # Use morphological operations to detect them
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 7))
            closed = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 1000:  # Filter small regions
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    # Barcodes typically have high aspect ratio
                    if aspect_ratio > 3:
                        regions.append({
                            'bbox': BoundingBox(x, y, x+w, y+h, 0.7),
                            'confidence': 0.7
                        })
                        
        except Exception as e:
            logger.error(f"Error detecting barcode regions: {e}")
        
        return regions
    
    def _detect_charts_graphs(self, image: np.ndarray) -> List[VisualEntity]:
        """Detect charts and graphs in image"""
        entities = []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            
            # Detect potential chart/graph regions
            # Charts often have axes, grids, and data points
            
            # Detect lines (potential axes)
            edges = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=50, maxLineGap=10)
            
            if lines is not None:
                # Group lines to find potential chart regions
                chart_regions = self._group_lines_to_charts(lines, image.shape)
                
                for region in chart_regions:
                    entity = VisualEntity(
                        entity_type=EntityType.CHART,
                        text="chart/graph",
                        bbox=region['bbox'],
                        confidence=region['confidence'],
                        metadata={
                            'source': 'chart_detector',
                            'type': region['type']
                        }
                    )
                    entities.append(entity)
                    
        except Exception as e:
            logger.error(f"Error detecting charts/graphs: {e}")
        
        return entities
    
    def _group_lines_to_charts(self, lines: np.ndarray, image_shape: Tuple) -> List[Dict]:
        """Group detected lines into potential chart regions"""
        chart_regions = []
        
        try:
            # Separate horizontal and vertical lines
            horizontal_lines = []
            vertical_lines = []
            
            for line in lines:
                x1, y1, x2, y2 = line[0]
                
                # Calculate angle
                angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                
                if abs(angle) < 15 or abs(angle) > 165:  # Horizontal
                    horizontal_lines.append(line[0])
                elif 75 < abs(angle) < 105:  # Vertical
                    vertical_lines.append(line[0])
            
            # Look for intersections that might indicate chart axes
            for h_line in horizontal_lines:
                for v_line in vertical_lines:
                    intersection = self._find_line_intersection(h_line, v_line)
                    if intersection:
                        # Create a bounding box around the potential chart
                        x, y = intersection
                        # Expand region to capture the chart
                        x1 = max(0, x - 100)
                        y1 = max(0, y - 100)
                        x2 = min(image_shape[1], x + 200)
                        y2 = min(image_shape[0], y + 200)
                        
                        chart_regions.append({
                            'bbox': BoundingBox(x1, y1, x2, y2, 0.6),
                            'confidence': 0.6,
                            'type': 'axis_based'
                        })
                        break  # Only one chart per horizontal line
                        
        except Exception as e:
            logger.error(f"Error grouping lines to charts: {e}")
        
        return chart_regions
    
    def _find_line_intersection(self, line1: np.ndarray, line2: np.ndarray) -> Optional[Tuple[int, int]]:
        """Find intersection point of two lines"""
        try:
            x1, y1, x2, y2 = line1
            x3, y3, x4, y4 = line2
            
            # Calculate intersection
            denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
            if abs(denom) < 1e-10:
                return None  # Lines are parallel
            
            t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
            
            # Calculate intersection point
            x = x1 + t * (x2 - x1)
            y = y1 + t * (y2 - y1)
            
            return (int(x), int(y))
            
        except:
            return None
    
    def _map_yolo_to_entity_type(self, class_name: str) -> EntityType:
        """Map YOLO class names to entity types"""
        mapping = {
            'person': EntityType.PERSON,
            'car': EntityType.PRODUCT,
            'truck': EntityType.PRODUCT,
            'bus': EntityType.PRODUCT,
            'motorcycle': EntityType.PRODUCT,
            'bicycle': EntityType.PRODUCT,
            'book': EntityType.PRODUCT,
            'laptop': EntityType.PRODUCT,
            'cell phone': EntityType.PRODUCT,
            'clock': EntityType.PRODUCT,
        }
        return mapping.get(class_name, EntityType.UNKNOWN)
    
    def _map_detr_to_entity_type(self, class_name: str) -> EntityType:
        """Map DETR class names to entity types"""
        mapping = {
            'person': EntityType.PERSON,
            'car': EntityType.PRODUCT,
            'truck': EntityType.PRODUCT,
            'bus': EntityType.PRODUCT,
            'motorcycle': EntityType.PRODUCT,
            'bicycle': EntityType.PRODUCT,
            'book': EntityType.PRODUCT,
            'laptop': EntityType.PRODUCT,
            'cell phone': EntityType.PRODUCT,
            'clock': EntityType.PRODUCT,
        }
        return mapping.get(class_name, EntityType.UNKNOWN)
    
    def analyze_visual_content(self, image: np.ndarray) -> VisualContent:
        """Comprehensive visual content analysis"""
        try:
            # Image captioning using BLIP
            description = self._generate_image_caption(image)
            
            # Object detection summary
            objects_detected = self._get_detected_objects_summary(image)
            
            # Scene classification using ViT
            scene_classification = self._classify_scene(image)
            
            # Color analysis
            dominant_colors = self._extract_dominant_colors(image)
            
            # Text region detection
            text_regions = self._detect_text_regions(image)
            
            # Face detection
            faces_detected = self._count_faces(image)
            
            # Landmark detection (simplified)
            landmarks = self._detect_landmarks(image)
            
            # Determine content type
            content_type = self._determine_content_type(objects_detected, text_regions, faces_detected)
            
            return VisualContent(
                content_type=content_type,
                description=description,
                objects_detected=objects_detected,
                scene_classification=scene_classification,
                dominant_colors=dominant_colors,
                text_regions=text_regions,
                faces_detected=faces_detected,
                landmarks=landmarks
            )
            
        except Exception as e:
            logger.error(f"Error in visual content analysis: {e}")
            return VisualContent(
                content_type="unknown",
                description="Error in analysis",
                objects_detected=[],
                scene_classification="unknown",
                dominant_colors=[],
                text_regions=[],
                faces_detected=0,
                landmarks=[]
            )
    
    def _generate_image_caption(self, image: np.ndarray) -> str:
        """Generate image caption using BLIP"""
        try:
            if not self.blip_model or not self.blip_processor:
                return "Caption generation not available"
            
            # Convert numpy array to PIL Image
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            # Generate caption
            inputs = self.blip_processor(pil_image, return_tensors="pt")
            
            with torch.no_grad():
                out = self.blip_model.generate(**inputs, max_length=50)
            
            caption = self.blip_processor.decode(out[0], skip_special_tokens=True)
            return caption
            
        except Exception as e:
            logger.error(f"Error generating caption: {e}")
            return "Caption generation failed"
    
    def _get_detected_objects_summary(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Get summary of detected objects"""
        objects = []
        
        try:
            # Use YOLO if available
            if self.yolo_model:
                results = self.yolo_model(image)
                
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            class_id = int(box.cls[0].cpu().numpy())
                            confidence = float(box.conf[0].cpu().numpy())
                            class_name = self.yolo_model.names[class_id]
                            
                            objects.append({
                                'name': class_name,
                                'confidence': confidence,
                                'source': 'yolo'
                            })
                            
        except Exception as e:
            logger.error(f"Error getting object summary: {e}")
        
        return objects
    
    def _classify_scene(self, image: np.ndarray) -> str:
        """Classify scene using ViT"""
        try:
            if not self.vit_model or not self.vit_processor:
                return "Scene classification not available"
            
            # Convert numpy array to PIL Image
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            # Process image
            inputs = self.vit_processor(images=pil_image, return_tensors="pt")
            
            with torch.no_grad():
                outputs = self.vit_model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # Get top prediction
            predicted_class_idx = predictions.argmax(-1).item()
            predicted_class = self.vit_model.config.id2label[predicted_class_idx]
            
            return predicted_class
            
        except Exception as e:
            logger.error(f"Error in scene classification: {e}")
            return "Classification failed"
    
    def _extract_dominant_colors(self, image: np.ndarray, k: int = 5) -> List[Tuple[int, int, int]]:
        """Extract dominant colors using K-means clustering"""
        try:
            # Reshape image to be a list of pixels
            data = image.reshape((-1, 3))
            data = np.float32(data)
            
            # Apply K-means clustering
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
            _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            # Convert centers to integers and return as list of tuples
            centers = np.uint8(centers)
            dominant_colors = [tuple(map(int, color)) for color in centers]
            
            return dominant_colors
            
        except Exception as e:
            logger.error(f"Error extracting dominant colors: {e}")
            return []
    
    def _detect_text_regions(self, image: np.ndarray) -> List[BoundingBox]:
        """Detect text regions in image"""
        text_regions = []
        
        try:
            # Use EAST text detector or similar approach
            # For now, use a simple contour-based approach
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            
            # Apply morphological operations to find text regions
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            grad = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, kernel)
            
            # Binarize
            _, bw = cv2.threshold(grad, 0.0, 255.0, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            
            # Connect horizontally oriented regions
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1))
            connected = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(connected, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 100:  # Filter small regions
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Filter by aspect ratio (text regions are typically wider than tall)
                    aspect_ratio = w / h
                    if aspect_ratio > 1.5:
                        text_regions.append(BoundingBox(x, y, x+w, y+h, 0.7))
                        
        except Exception as e:
            logger.error(f"Error detecting text regions: {e}")
        
        return text_regions
    
    def _count_faces(self, image: np.ndarray) -> int:
        """Count faces in image"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            return len(faces)
        except:
            return 0
    
    def _detect_landmarks(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect landmarks in image (simplified)"""
        landmarks = []
        
        try:
            # This is a placeholder for landmark detection
            # In production, you'd use specialized landmark detection models
            
            # For now, detect corner features as "landmarks"
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            corners = cv2.goodFeaturesToTrack(gray, maxCorners=100, qualityLevel=0.01, minDistance=10)
            
            if corners is not None:
                for corner in corners:
                    x, y = corner.ravel()
                    landmarks.append({
                        'type': 'corner',
                        'x': int(x),
                        'y': int(y),
                        'confidence': 0.5
                    })
                    
        except Exception as e:
            logger.error(f"Error detecting landmarks: {e}")
        
        return landmarks
    
    def _determine_content_type(self, objects: List[Dict], text_regions: List[BoundingBox], 
                               faces: int) -> str:
        """Determine the type of content in the image"""
        try:
            # Simple heuristics to determine content type
            if faces > 0:
                return "portrait" if faces == 1 else "group_photo"
            
            if len(text_regions) > 5:
                return "document"
            
            if any(obj['name'] in ['car', 'truck', 'bus', 'motorcycle'] for obj in objects):
                return "vehicle"
            
            if any(obj['name'] in ['book', 'laptop', 'cell phone'] for obj in objects):
                return "technology"
            
            if len(objects) > 5:
                return "complex_scene"
            
            return "general"
            
        except:
            return "unknown"
    
    def analyze_image(self, image_path: str, image: Union[np.ndarray, Image.Image], 
                     extracted_text: str = "") -> ImageAnalysisResult:
        """Complete image analysis pipeline"""
        try:
            # Convert PIL Image to numpy array if needed
            if isinstance(image, Image.Image):
                pil_image = image
                image_array = np.array(image)
            else:
                image_array = image
                pil_image = Image.fromarray(cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB))
            
            # Extract metadata
            metadata = self.extract_image_metadata(image_path, pil_image)
            
            # Assess image quality
            quality_assessment = self.assess_image_quality(image_array)
            
            # Detect visual entities
            visual_entities = self.detect_visual_entities(image_array, extracted_text)
            
            # Analyze visual content
            visual_content = self.analyze_visual_content(image_array)
            
            # Calculate overall confidence
            confidences = [entity.confidence for entity in visual_entities]
            overall_confidence = np.mean(confidences) if confidences else 0.5
            
            return ImageAnalysisResult(
                visual_entities=visual_entities,
                metadata=metadata,
                quality_assessment=quality_assessment,
                visual_content=visual_content,
                extracted_text=extracted_text,
                confidence=overall_confidence
            )
            
        except Exception as e:
            logger.error(f"Error in image analysis: {e}")
            return ImageAnalysisResult(
                visual_entities=[],
                metadata=ImageMetadata(
                    filename="error", file_size=0, dimensions=(0, 0),
                    format="unknown", mode="unknown", creation_date=None,
                    camera_make=None, camera_model=None, gps_coordinates=None,
                    orientation=None, color_space=None, dpi=None,
                    compression=None, software=None, artist=None,
                    copyright=None, keywords=[], description=None
                ),
                quality_assessment=ImageQualityAssessment(
                    overall_quality=ImageQuality.UNKNOWN,
                    sharpness_score=0.0, brightness_score=0.0, contrast_score=0.0,
                    noise_level=0.0, blur_detection=0.0, color_balance={},
                    histogram_analysis={}, recommendations=[]
                ),
                visual_content=VisualContent(
                    content_type="error", description="Analysis failed",
                    objects_detected=[], scene_classification="unknown",
                    dominant_colors=[], text_regions=[], faces_detected=0,
                    landmarks=[]
                ),
                extracted_text="",
                confidence=0.0
            )
    
    def export_results(self, result: ImageAnalysisResult, format: str = 'json') -> str:
        """Export analysis results in various formats"""
        try:
            if format.lower() == 'json':
                # Convert to JSON-serializable format
                result_dict = {
                    'visual_entities': [
                        {
                            'entity_type': entity.entity_type.value,
                            'text': entity.text,
                            'bbox': asdict(entity.bbox),
                            'confidence': entity.confidence,
                            'metadata': entity.metadata
                        }
                        for entity in result.visual_entities
                    ],
                    'metadata': asdict(result.metadata),
                    'quality_assessment': {
                        'overall_quality': result.quality_assessment.overall_quality.value,
                        'sharpness_score': result.quality_assessment.sharpness_score,
                        'brightness_score': result.quality_assessment.brightness_score,
                        'contrast_score': result.quality_assessment.contrast_score,
                        'noise_level': result.quality_assessment.noise_level,
                        'blur_detection': result.quality_assessment.blur_detection,
                        'color_balance': result.quality_assessment.color_balance,
                        'histogram_analysis': result.quality_assessment.histogram_analysis,
                        'recommendations': result.quality_assessment.recommendations
                    },
                    'visual_content': asdict(result.visual_content),
                    'extracted_text': result.extracted_text,
                    'confidence': result.confidence
                }
                return json.dumps(result_dict, indent=2, default=str)
            
            elif format.lower() == 'csv':
                # Export entities as CSV
                import io
                output = io.StringIO()
                
                output.write("Entity Type,Text,Confidence,X1,Y1,X2,Y2,Source\n")
                for entity in result.visual_entities:
                    source = entity.metadata.get('source', 'unknown')
                    output.write(f"{entity.entity_type.value},{entity.text},{entity.confidence},"
                               f"{entity.bbox.x1},{entity.bbox.y1},{entity.bbox.x2},{entity.bbox.y2},{source}\n")
                
                return output.getvalue()
            
            else:
                return str(result)
                
        except Exception as e:
            logger.error(f"Error exporting results: {e}")
            return f"Error exporting: {e}"

    def _is_signature_like(self, roi: np.ndarray) -> bool:
        """Heuristic to determine if region looks like a signature"""
        try:
            # Signatures typically have:
            # - Irregular, flowing lines
            # - Lo
            # - Connected components with varying thickness
            
            # Calculate line density
            edges = cv2.Canny(roi, 50, 150)
            line_density = np.sum(edges > 0) / (roi.shape[0] * roi.shape[1])
            
            # Check for flowing, connected patterns
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Signatures typically have fewer, longer contours
            if len(contours) < 10 and line_density > 0.05:
                return True
                
        except:
            pass
        
        return False
    
    def _is_logo_like(self, roi: np.ndarray) -> bool:
        """Heuristic to determine if region looks like a logo"""
        try:
            # Logos typically have:
            # - Geometric shapes
            # - High contrast
            # - Structured patterns
            
            # Calculate contrast
            contrast = np.std(roi)
            
            # Find geometric shapes
            edges = cv2.Canny(roi, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Look for circular or rectangular shapes
            geometric_shapes = 0
            for contour in contours:
                # Approximate contour
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Count geometric shapes (triangles, rectangles, etc.)
                if len(approx) >= 3 and len(approx) <= 8:
                    geometric_shapes += 1
            
            if contrast > 30 and geometric_shapes > 0:
                return True
                
        except:
            pass
        
        return False
    
    def _detect_codes(self, image: np.ndarray) -> List[VisualEntity]:
        """Detect QR codes and barcodes"""
        entities = []
        
        try:
            # QR Code detection
            data, bbox, _ = self.qr_detector.detectAndDecode(image)
            if data and bbox is not None:
                # Convert bbox to our format
                points = bbox[0].astype(int)
                x1, y1 = np.min(points, axis=0)
                x2, y2 = np.max(points, axis=0)
                
                entity = VisualEntity(
                    entity_type=EntityType.QR_CODE,
                    text=data,
                    bbox=BoundingBox(x1, y1, x2, y2, 0.9),
                    confidence=0.9,
                    metadata={
                        'source': 'qr_detector',
                        'decoded_data': data
                    }
                )
                entities.append(entity)
            
            # Barcode detection (simplified approach)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            
            # Look for horizontal line patterns typical of barcodes
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 7))
            closed = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 1000:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    # Barcodes are typically wide and short
                    if aspect_ratio > 3:
                        entity = VisualEntity(
                            entity_type=EntityType.BARCODE,
                            text="barcode",
                            bbox=BoundingBox(x, y, x+w, y+h, 0.7),
                            confidence=0.7,
                            metadata={
                                'source': 'barcode_detector',
                                'aspect_ratio': aspect_ratio,
                                'area': area
                            }
                        )
                        entities.append(entity)
                        
        except Exception as e:
            logger.error(f"Error detecting codes: {e}")
        
        return entities
    
    def _detect_charts_graphs(self, image: np.ndarray) -> List[VisualEntity]:
        """Detect charts and graphs using computer vision"""
        entities = []
        
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            
            # Detect lines (potential axes)
            edges = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=50, maxLineGap=10)
            
            if lines is not None and len(lines) > 5:
                # Analyze line patterns
                horizontal_lines = []
                vertical_lines = []
                
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                    
                    if abs(angle) < 10 or abs(angle) > 170:  # Horizontal
                        horizontal_lines.append(line)
                    elif abs(abs(angle) - 90) < 10:  # Vertical
                        vertical_lines.append(line)
                
                # If we have both horizontal and vertical lines, likely a chart
                if len(horizontal_lines) > 2 and len(vertical_lines) > 2:
                    # Find bounding box of all lines
                    all_points = []
                    for line in lines:
                        x1, y1, x2, y2 = line[0]
                        all_points.extend([(x1, y1), (x2, y2)])
                    
                    if all_points:
                        xs, ys = zip(*all_points)
                        x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)
                        
                        entity = VisualEntity(
                            entity_type=EntityType.CHART,
                            text="chart/graph",
                            bbox=BoundingBox(x1, y1, x2, y2, 0.7),
                            confidence=0.7,
                            metadata={
                                'source': 'chart_detector',
                                'horizontal_lines': len(horizontal_lines),
                                'vertical_lines': len(vertical_lines),
                                'total_lines': len(lines)
                            }
                        )
                        entities.append(entity)
                        
        except Exception as e:
            logger.error(f"Error detecting charts: {e}")
        
        return entities
    
    def _map_yolo_to_entity_type(self, class_name: str) -> EntityType:
        """Map YOLO class names to entity types"""
        mapping = {
            'person': EntityType.PERSON,
            'car': EntityType.PRODUCT,
            'truck': EntityType.PRODUCT,
            'bus': EntityType.PRODUCT,
            'motorcycle': EntityType.PRODUCT,
            'bicycle': EntityType.PRODUCT,
            'laptop': EntityType.PRODUCT,
            'cell phone': EntityType.PRODUCT,
            'book': EntityType.PRODUCT,
            'clock': EntityType.PRODUCT,
        }
        return mapping.get(class_name, EntityType.UNKNOWN)
    
    def _map_detr_to_entity_type(self, class_name: str) -> EntityType:
        """Map DETR class names to entity types"""
        mapping = {
            'person': EntityType.PERSON,
            'car': EntityType.PRODUCT,
            'truck': EntityType.PRODUCT,
            'bus': EntityType.PRODUCT,
            'motorcycle': EntityType.PRODUCT,
            'bicycle': EntityType.PRODUCT,
            'laptop': EntityType.PRODUCT,
            'cell phone': EntityType.PRODUCT,
            'book': EntityType.PRODUCT,
            'clock': EntityType.PRODUCT,
        }
        return mapping.get(class_name, EntityType.UNKNOWN)
    
    def analyze_visual_content(self, image: np.ndarray) -> VisualContent:
        """Analyze visual content using AI models"""
        try:
            # Convert to PIL Image for model processing
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            # Generate image caption using BLIP
            description = self._generate_image_caption(pil_image)
            
            # Classify image content using ViT
            content_type = self._classify_image_content(pil_image)
            
            # Detect objects
            objects_detected = self._detect_all_objects(image)
            
            # Analyze dominant colors
            dominant_colors = self._extract_dominant_colors(image)
            
            # Detect text regions
            text_regions = self._detect_text_regions(image)
            
            # Count faces and perform face recognition
            faces_detected, face_identities = self._analyze_faces(image)
            
            # Detect landmarks (simplified)
            landmarks = self._detect_landmarks(image)
            
            # Perform scene understanding and contextual analysis
            scene_analysis = self._analyze_scene_context(pil_image)
            
            # Detect logos and brands for compliance monitoring
            logos_brands = self._detect_logos_brands(image, description)
            
            # Perform content moderation and safety detection
            safety_assessment = self._assess_content_safety(image, description)
            
            return VisualContent(
                content_type=content_type,
                description=description,
                objects_detected=objects_detected,
                scene_classification=scene_analysis.get('scene_type', content_type),
                dominant_colors=dominant_colors,
                text_regions=text_regions,
                faces_detected=faces_detected,
                landmarks=landmarks,
                face_identities=face_identities,
                scene_analysis=scene_analysis,
                logos_brands=logos_brands,
                safety_assessment=safety_assessment
            )
            
        except Exception as e:
            logger.error(f"Error in visual content analysis: {e}")
            return VisualContent(
                content_type="unknown",
                description="Error in content analysis",
                objects_detected=[],
                scene_classification="unknown",
                dominant_colors=[],
                text_regions=[],
                faces_detected=0,
                landmarks=[],
                face_identities=[],
                scene_analysis={},
                logos_brands=[],
                safety_assessment={"safe": True, "flags": [], "confidence": 0.0}
            )
    
    def _generate_image_caption(self, image: Image.Image) -> str:
        """Generate image caption using BLIP"""
        try:
            if self.blip_model and self.blip_processor:
                inputs = self.blip_processor(image, return_tensors="pt")
                
                with torch.no_grad():
                    out = self.blip_model.generate(**inputs, max_length=50)
                
                caption = self.blip_processor.decode(out[0], skip_special_tokens=True)
                return caption
        except Exception as e:
            logger.error(f"Error generating caption: {e}")
        
        return "Unable to generate description"
    
    def _classify_image_content(self, image: Image.Image) -> str:
        """Classify image content using ViT"""
        try:
            if self.vit_model and self.vit_processor:
                inputs = self.vit_processor(images=image, return_tensors="pt")
                
                with torch.no_grad():
                    outputs = self.vit_model(**inputs)
                
                predicted_class_idx = outputs.logits.argmax(-1).item()
                predicted_class = self.vit_model.config.id2label[predicted_class_idx]
                
                return predicted_class
        except Exception as e:
            logger.error(f"Error classifying content: {e}")
        
        return "unknown"
    
    def _detect_all_objects(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect all objects in image"""
        objects = []
        
        try:
            # Use YOLO if available
            if self.yolo_model:
                results = self.yolo_model(image)
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            confidence = float(box.conf[0].cpu().numpy())
                            class_id = int(box.cls[0].cpu().numpy())
                            class_name = self.yolo_model.names[class_id]
                            
                            objects.append({
                                'name': class_name,
                                'confidence': confidence,
                                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                                'source': 'yolo'
                            })
        except Exception as e:
            logger.error(f"Error detecting objects: {e}")
        
        return objects
    
    def _extract_dominant_colors(self, image: np.ndarray, k: int = 5) -> List[Tuple[int, int, int]]:
        """Extract dominant colors using K-means clustering"""
        try:
            # Reshape image to be a list of pixels
            data = image.reshape((-1, 3))
            data = np.float32(data)
            
            # Apply K-means clustering
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
            _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            # Convert centers to integers and return as list of tuples
            centers = np.uint8(centers)
            dominant_colors = [tuple(color) for color in centers]
            
            return dominant_colors
            
        except Exception as e:
            logger.error(f"Error extracting dominant colors: {e}")
            return []
    
    def _detect_text_regions(self, image: np.ndarray) -> List[BoundingBox]:
        """Detect text regions in image"""
        text_regions = []
        
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            
            # Use MSER (Maximally Stable Extremal Regions) for text detection
            mser = cv2.MSER_create()
            regions, _ = mser.detectRegions(gray)
            
            for region in regions:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(region)
                
                # Filter by size and aspect ratio
                if w > 10 and h > 10 and w/h < 10 and h/w < 10:
                    text_regions.append(BoundingBox(x, y, x+w, y+h, 0.7))
                    
        except Exception as e:
            logger.error(f"Error detecting text regions: {e}")
        
        return text_regions
    
    def _count_faces(self, image: np.ndarray) -> int:
        """Count faces in image"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            return len(faces)
        except Exception as e:
            logger.error(f"Error counting faces: {e}")
            return 0
    
    def _detect_landmarks(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect landmarks (simplified implementation)"""
        landmarks = []
        
        try:
            # This is a placeholder - in production, you'd use specialized landmark detection models
            # For now, we'll detect corner features as potential landmarks
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            
            # Detect corners using Harris corner detection
            corners = cv2.cornerHarris(gray, 2, 3, 0.04)
            corners = cv2.dilate(corners, None)
            
            # Find corner coordinates
            corner_coords = np.where(corners > 0.01 * corners.max())
            
            for y, x in zip(corner_coords[0], corner_coords[1]):
                landmarks.append({
                    'type': 'corner',
                    'x': int(x),
                    'y': int(y),
                    'confidence': 0.5
                })
                
        except Exception as e:
            logger.error(f"Error detecting landmarks: {e}")
        
        return landmarks[:20]  # Limit to top 20 landmarks
    
    def extract_text_from_image(self, image: np.ndarray) -> str:
        """Extract text from image using OCR (placeholder - would use Tesseract/EasyOCR)"""
        try:
            # This is a placeholder implementation
            # In production, you would use:
            # - Tesseract OCR: pytesseract.image_to_string(image)
            # - EasyOCR: reader.readtext(image)
            # - PaddleOCR: ocr.ocr(image)
            
            # For now, return a placeholder
            return "OCR text extraction would be implemented here using Tesseract, EasyOCR, or PaddleOCR"
            
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""
    
    def analyze_image(self, image_path: str = None, image_data: np.ndarray = None) -> ImageAnalysisResult:
        """Complete image analysis pipeline"""
        try:
            # Load image
            if image_path:
                pil_image = Image.open(image_path)
                image_array = np.array(pil_image)
                if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                    image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            elif image_data is not None:
                image_array = image_data
                pil_image = Image.fromarray(cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB))
            else:
                raise ValueError("Either image_path or image_data must be provided")
            
            # Extract metadata
            metadata = self.extract_image_metadata(image_path or "", pil_image)
            
            # Assess image quality
            quality_assessment = self.assess_image_quality(image_array)
            
            # Extract text from image
            extracted_text = self.extract_text_from_image(image_array)
            
            # Detect visual entities
            visual_entities = self.detect_visual_entities(image_array, extracted_text)
            
            # Analyze visual content
            visual_content = self.analyze_visual_content(image_array)
            
            # Calculate overall confidence
            confidence = self._calculate_overall_confidence(
                quality_assessment, visual_entities, visual_content
            )
            
            return ImageAnalysisResult(
                visual_entities=visual_entities,
                metadata=metadata,
                quality_assessment=quality_assessment,
                visual_content=visual_content,
                extracted_text=extracted_text,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error in image analysis: {e}")
            # Return empty result on error
            return ImageAnalysisResult(
                visual_entities=[],
                metadata=ImageMetadata(
                    filename="error", file_size=0, dimensions=(0, 0),
                    format="unknown", mode="unknown", creation_date=None,
                    camera_make=None, camera_model=None, gps_coordinates=None,
                    orientation=None, color_space=None, dpi=None,
                    compression=None, software=None, artist=None,
                    copyright=None, keywords=[], description=None
                ),
                quality_assessment=ImageQualityAssessment(
                    overall_quality=ImageQuality.UNKNOWN,
                    sharpness_score=0.0, brightness_score=0.0,
                    contrast_score=0.0, noise_level=0.0,
                    blur_detection=0.0, color_balance={},
                    histogram_analysis={}, recommendations=[]
                ),
                visual_content=VisualContent(
                    content_type="error", description="Error in analysis",
                    objects_detected=[], scene_classification="error",
                    dominant_colors=[], text_regions=[],
                    faces_detected=0, landmarks=[],
                    face_identities=[], scene_analysis={},
                    logos_brands=[], safety_assessment={"safe": True, "flags": [], "confidence": 0.0}
                ),
                extracted_text="",
                confidence=0.0
            )
    
    def _calculate_overall_confidence(self, quality: ImageQualityAssessment,
                                    entities: List[VisualEntity],
                                    content: VisualContent) -> float:
        """Calculate overall confidence score for the analysis"""
        try:
            # Base confidence on image quality
            quality_score = {
                ImageQuality.EXCELLENT: 0.9,
                ImageQuality.GOOD: 0.8,
                ImageQuality.FAIR: 0.6,
                ImageQuality.POOR: 0.4,
                ImageQuality.VERY_POOR: 0.2,
                ImageQuality.UNKNOWN: 0.5
            }.get(quality.overall_quality, 0.5)
            
            # Factor in entity detection confidence
            if entities:
                entity_confidence = np.mean([e.confidence for e in entities])
            else:
                entity_confidence = 0.5
            
            # Factor in content analysis success
            content_confidence = 0.8 if content.description != "Error in content analysis" else 0.3
            
            # Weighted average
            overall_confidence = (
                quality_score * 0.3 +
                entity_confidence * 0.4 +
                content_confidence * 0.3
            )
            
            return float(overall_confidence)
            
        except:
            return 0.5

    def _analyze_faces(self, image: np.ndarray) -> Tuple[int, List[Dict[str, Any]]]:
        """Enhanced face analysis with recognition capabilities"""
        try:
            # Basic face detection using OpenCV
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            face_count = len(faces)
            face_identities = []
            
            # Enhanced face recognition if available
            if self.face_recognition_available and face_count > 0:
                import face_recognition
                
                # Convert to RGB for face_recognition library
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
                # Find face locations and encodings
                face_locations = face_recognition.face_locations(rgb_image)
                face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
                
                for i, (face_encoding, face_location) in enumerate(zip(face_encodings, face_locations)):
                    top, right, bottom, left = face_location
                    
                    # Extract face features
                    face_info = {
                        'face_id': f"face_{i+1}",
                        'bbox': {'x1': left, 'y1': top, 'x2': right, 'y2': bottom},
                        'confidence': 0.8,  # Default confidence for detected faces
                        'features': {
                            'face_width': right - left,
                            'face_height': bottom - top,
                            'estimated_age': self._estimate_age_from_face(rgb_image[top:bottom, left:right]),
                            'estimated_gender': self._estimate_gender_from_face(rgb_image[top:bottom, left:right]),
                            'face_quality': self._assess_face_quality(rgb_image[top:bottom, left:right])
                        },
                        'encoding': face_encoding.tolist()  # Store for potential matching
                    }
                    face_identities.append(face_info)
            
            return face_count, face_identities
            
        except Exception as e:
            logger.error(f"Error in face analysis: {e}")
            return 0, []
    
    def _estimate_age_from_face(self, face_image: np.ndarray) -> str:
        """Estimate age range from face image (simplified)"""
        try:
            # This is a simplified approach - in production, use dedicated age estimation models
            face_area = face_image.shape[0] * face_image.shape[1]
            brightness = np.mean(face_image)
            
            if face_area < 2000:
                return "child"
            elif brightness > 150:
                return "young_adult"
            elif brightness > 100:
                return "adult"
            else:
                return "senior"
        except:
            return "unknown"
    
    def _estimate_gender_from_face(self, face_image: np.ndarray) -> str:
        """Estimate gender from face image (simplified)"""
        try:
            # This is a placeholder - in production, use dedicated gender classification models
            # For now, return neutral to avoid bias
            return "not_determined"
        except:
            return "unknown"
    
    def _assess_face_quality(self, face_image: np.ndarray) -> Dict[str, float]:
        """Assess face image quality"""
        try:
            # Calculate basic quality metrics
            if len(face_image.shape) == 3:
                gray_face = cv2.cvtColor(face_image, cv2.COLOR_RGB2GRAY)
            else:
                gray_face = face_image
            
            # Sharpness
            sharpness = cv2.Laplacian(gray_face, cv2.CV_64F).var()
            
            # Brightness
            brightness = np.mean(gray_face)
            
            # Contrast
            contrast = np.std(gray_face)
            
            return {
                'sharpness': float(sharpness),
                'brightness': float(brightness),
                'contrast': float(contrast),
                'overall_quality': float((sharpness/100 + brightness/255 + contrast/64) / 3)
            }
        except:
            return {'overall_quality': 0.0}
    
    def _analyze_scene_context(self, image: Image.Image) -> Dict[str, Any]:
        """Perform scene understanding and contextual analysis"""
        try:
            scene_analysis = {
                'scene_type': 'unknown',
                'setting': 'unknown',
                'lighting_conditions': 'unknown',
                'time_of_day': 'unknown',
                'weather_conditions': 'unknown',
                'indoor_outdoor': 'unknown',
                'activity_detected': [],
                'context_confidence': 0.0
            }
            
            # Use CLIP for scene understanding
            if self.clip_model and self.clip_processor:
                # Scene type classification
                scene_types = [
                    "indoor office", "outdoor park", "indoor home", "outdoor street",
                    "indoor restaurant", "outdoor beach", "indoor store", "outdoor city",
                    "indoor classroom", "outdoor nature", "indoor hospital", "outdoor parking"
                ]
                
                inputs = self.clip_processor(
                    text=scene_types, 
                    images=image, 
                    return_tensors="pt", 
                    padding=True
                )
                
                with torch.no_grad():
                    outputs = self.clip_model(**inputs)
                    probs = outputs.logits_per_image.softmax(dim=1)
                    
                    best_match_idx = probs.argmax().item()
                    confidence = probs[0][best_match_idx].item()
                    
                    scene_analysis['scene_type'] = scene_types[best_match_idx]
                    scene_analysis['context_confidence'] = float(confidence)
                    
                    # Determine indoor/outdoor
                    if 'indoor' in scene_types[best_match_idx]:
                        scene_analysis['indoor_outdoor'] = 'indoor'
                    elif 'outdoor' in scene_types[best_match_idx]:
                        scene_analysis['indoor_outdoor'] = 'outdoor'
                
                # Activity detection
                activities = [
                    "people walking", "people sitting", "people working", "people eating",
                    "people talking", "people exercising", "people shopping", "people driving"
                ]
                
                activity_inputs = self.clip_processor(
                    text=activities,
                    images=image,
                    return_tensors="pt",
                    padding=True
                )
                
                with torch.no_grad():
                    activity_outputs = self.clip_model(**activity_inputs)
                    activity_probs = activity_outputs.logits_per_image.softmax(dim=1)
                    
                    # Get top activities with confidence > 0.3
                    for i, prob in enumerate(activity_probs[0]):
                        if prob > 0.3:
                            scene_analysis['activity_detected'].append({
                                'activity': activities[i],
                                'confidence': float(prob)
                            })
            
            return scene_analysis
            
        except Exception as e:
            logger.error(f"Error in scene analysis: {e}")
            return {
                'scene_type': 'unknown',
                'setting': 'unknown',
                'context_confidence': 0.0,
                'activity_detected': []
            }
    
    def _detect_logos_brands(self, image: np.ndarray, description: str) -> List[Dict[str, Any]]:
        """Detect logos and brands for compliance monitoring"""
        try:
            logos_brands = []
            
            # Text-based brand detection from description and OCR
            text_to_analyze = description.lower()
            
            for pattern in self.brand_patterns:
                matches = re.finditer(pattern, text_to_analyze, re.IGNORECASE)
                for match in matches:
                    brand_info = {
                        'type': 'brand_mention',
                        'brand_name': match.group(0),
                        'confidence': 0.8,
                        'source': 'text_analysis',
                        'compliance_risk': self._assess_brand_compliance_risk(match.group(0)),
                        'bbox': None  # Text-based detection doesn't have bbox
                    }
                    logos_brands.append(brand_info)
            
            # Visual logo detection using template matching (simplified)
            logo_detections = self._detect_visual_logos(image)
            logos_brands.extend(logo_detections)
            
            return logos_brands
            
        except Exception as e:
            logger.error(f"Error in logo/brand detection: {e}")
            return []
    
    def _detect_visual_logos(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect visual logos using computer vision techniques"""
        try:
            # This is a simplified approach - in production, use trained logo detection models
            visual_logos = []
            
            # Convert to grayscale for processing
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Use corner detection to find potential logo regions
            corners = cv2.goodFeaturesToTrack(gray, maxCorners=100, qualityLevel=0.01, minDistance=10)
            
            if corners is not None:
                # Group corners into potential logo regions
                for corner in corners:
                    x, y = corner.ravel()
                    x, y = int(x), int(y)
                    
                    # Extract region around corner
                    region_size = 50
                    x1, y1 = max(0, x - region_size), max(0, y - region_size)
                    x2, y2 = min(image.shape[1], x + region_size), min(image.shape[0], y + region_size)
                    
                    region = gray[y1:y2, x1:x2]
                    
                    # Simple logo characteristics check
                    if self._has_logo_characteristics(region):
                        logo_info = {
                            'type': 'visual_logo',
                            'brand_name': 'unknown_logo',
                            'confidence': 0.6,
                            'source': 'visual_detection',
                            'bbox': {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2},
                            'compliance_risk': 'medium'
                        }
                        visual_logos.append(logo_info)
            
            return visual_logos[:5]  # Limit to top 5 detections
            
        except Exception as e:
            logger.error(f"Error in visual logo detection: {e}")
            return []
    
    def _has_logo_characteristics(self, region: np.ndarray) -> bool:
        """Check if image region has logo-like characteristics"""
        try:
            if region.size == 0:
                return False
            
            # Check for high contrast (logos often have sharp edges)
            contrast = np.std(region)
            
            # Check for geometric shapes (simplified)
            edges = cv2.Canny(region, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            # Logo characteristics: high contrast and moderate edge density
            return contrast > 30 and 0.1 < edge_density < 0.5
            
        except:
            return False
    
    def _assess_brand_compliance_risk(self, brand_name: str) -> str:
        """Assess compliance risk for detected brand"""
        try:
            # High-risk brands (require special handling)
            high_risk_brands = ['tobacco', 'alcohol', 'gambling', 'pharmaceutical']
            
            # Medium-risk brands (require attribution)
            medium_risk_brands = ['apple', 'google', 'microsoft', 'amazon', 'facebook']
            
            brand_lower = brand_name.lower()
            
            for high_risk in high_risk_brands:
                if high_risk in brand_lower:
                    return 'high'
            
            for medium_risk in medium_risk_brands:
                if medium_risk in brand_lower:
                    return 'medium'
            
            return 'low'
            
        except:
            return 'unknown'
    
    def _assess_content_safety(self, image: np.ndarray, description: str) -> Dict[str, Any]:
        """Perform content moderation and safety detection"""
        try:
            safety_assessment = {
                'safe': True,
                'confidence': 1.0,
                'flags': [],
                'categories': {
                    'violence': {'detected': False, 'confidence': 0.0},
                    'adult_content': {'detected': False, 'confidence': 0.0},
                    'hate_speech': {'detected': False, 'confidence': 0.0},
                    'drugs': {'detected': False, 'confidence': 0.0},
                    'weapons': {'detected': False, 'confidence': 0.0}
                },
                'recommendations': []
            }
            
            # Text-based safety analysis
            text_to_analyze = description.lower()
            
            for pattern in self.unsafe_content_patterns:
                matches = re.finditer(pattern, text_to_analyze, re.IGNORECASE)
                for match in matches:
                    flag_info = {
                        'type': 'text_based',
                        'category': self._categorize_unsafe_content(match.group(0)),
                        'content': match.group(0),
                        'confidence': 0.8,
                        'severity': 'medium'
                    }
                    safety_assessment['flags'].append(flag_info)
                    safety_assessment['safe'] = False
            
            # Visual safety analysis (simplified)
            visual_flags = self._analyze_visual_safety(image)
            safety_assessment['flags'].extend(visual_flags)
            
            if visual_flags:
                safety_assessment['safe'] = False
            
            # Update category flags
            for flag in safety_assessment['flags']:
                category = flag['category']
                if category in safety_assessment['categories']:
                    safety_assessment['categories'][category]['detected'] = True
                    safety_assessment['categories'][category]['confidence'] = max(
                        safety_assessment['categories'][category]['confidence'],
                        flag['confidence']
                    )
            
            # Calculate overall confidence
            if safety_assessment['flags']:
                avg_confidence = sum(flag['confidence'] for flag in safety_assessment['flags']) / len(safety_assessment['flags'])
                safety_assessment['confidence'] = 1.0 - avg_confidence
            
            # Generate recommendations
            if not safety_assessment['safe']:
                safety_assessment['recommendations'] = self._generate_safety_recommendations(safety_assessment['flags'])
            
            return safety_assessment
            
        except Exception as e:
            logger.error(f"Error in content safety assessment: {e}")
            return {
                'safe': True,
                'confidence': 0.0,
                'flags': [],
                'categories': {},
                'recommendations': ['Error in safety assessment - manual review recommended']
            }
    
    def _analyze_visual_safety(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Analyze visual content for safety issues"""
        try:
            visual_flags = []
            
            # Convert to different color spaces for analysis
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Check for excessive red (potential violence indicator)
            red_mask = cv2.inRange(hsv, (0, 50, 50), (10, 255, 255))
            red_percentage = np.sum(red_mask > 0) / red_mask.size
            
            if red_percentage > 0.3:  # More than 30% red
                visual_flags.append({
                    'type': 'visual',
                    'category': 'violence',
                    'content': 'excessive_red_detected',
                    'confidence': min(red_percentage, 0.8),
                    'severity': 'medium'
                })
            
            # Check for skin tone detection (simplified adult content detection)
            skin_mask = cv2.inRange(hsv, (0, 20, 70), (20, 255, 255))
            skin_percentage = np.sum(skin_mask > 0) / skin_mask.size
            
            if skin_percentage > 0.4:  # More than 40% skin tone
                visual_flags.append({
                    'type': 'visual',
                    'category': 'adult_content',
                    'content': 'high_skin_tone_detected',
                    'confidence': min(skin_percentage, 0.7),
                    'severity': 'high'
                })
            
            return visual_flags
            
        except Exception as e:
            logger.error(f"Error in visual safety analysis: {e}")
            return []
    
    def _categorize_unsafe_content(self, content: str) -> str:
        """Categorize unsafe content type"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['violence', 'weapon', 'gun', 'knife', 'blood']):
            return 'violence'
        elif any(word in content_lower for word in ['nude', 'naked', 'explicit', 'sexual']):
            return 'adult_content'
        elif any(word in content_lower for word in ['drug', 'cocaine', 'marijuana', 'heroin']):
            return 'drugs'
        elif any(word in content_lower for word in ['hate', 'racist', 'nazi', 'terrorist']):
            return 'hate_speech'
        else:
            return 'other'
    
    def _generate_safety_recommendations(self, flags: List[Dict[str, Any]]) -> List[str]:
        """Generate safety recommendations based on detected flags"""
        recommendations = []
        
        categories = set(flag['category'] for flag in flags)
        
        if 'violence' in categories:
            recommendations.append("Content may contain violent imagery - consider age restrictions")
        
        if 'adult_content' in categories:
            recommendations.append("Content may contain adult material - implement content warnings")
        
        if 'hate_speech' in categories:
            recommendations.append("Content may contain hate speech - review for policy violations")
        
        if 'drugs' in categories:
            recommendations.append("Content may reference controlled substances - check compliance")
        
        if 'weapons' in categories:
            recommendations.append("Content may show weapons - verify platform policies")
        
        if not recommendations:
            recommendations.append("Manual review recommended for flagged content")
        
        return recommendations

# Example usage and testing functions
def create_demo_analysis():
    """Create a demo analysis for testing"""
    system = ImageEntityExtractionSystem()
    
    # Create a sample image for testing with some text and shapes
    sample_image = np.ones((400, 600, 3), dtype=np.uint8) * 255
    
    # Add some text
    cv2.putText(sample_image, "DEMO IMAGE", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
    cv2.putText(sample_image, "Apple Inc. Logo", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(sample_image, "Contact: john@example.com", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    
    # Add some shapes to simulate objects
    cv2.rectangle(sample_image, (400, 50), (550, 150), (255, 0, 0), -1)  # Red rectangle
    cv2.circle(sample_image, (500, 300), 50, (0, 255, 0), -1)  # Green circle
    
    # Run analysis
    result = system.analyze_image(image_data=sample_image)
    
    return result

def demo_enhanced_features():
    """Demonstrate the enhanced image analysis features"""
    print("🎯 Enhanced Image Entity Extraction Demo")
    print("=" * 60)
    
    try:
        system = ImageEntityExtractionSystem()
        result = create_demo_analysis()
        
        print(f"\n📊 Analysis Results:")
        print(f"   Overall Confidence: {result.confidence:.2f}")
        print(f"   Entities Found: {len(result.visual_entities)}")
        print(f"   Faces Detected: {result.visual_content.faces_detected}")
        
        # Display face recognition results
        if hasattr(result.visual_content, 'face_identities') and result.visual_content.face_identities:
            print(f"\n👤 Face Recognition Results:")
            for i, face in enumerate(result.visual_content.face_identities):
                print(f"   Face {i+1}: {face['face_id']} (confidence: {face['confidence']:.2f})")
                print(f"      Age: {face['features']['estimated_age']}")
                print(f"      Quality: {face['features']['face_quality']['overall_quality']:.2f}")
        
        # Display scene analysis
        if hasattr(result.visual_content, 'scene_analysis') and result.visual_content.scene_analysis:
            scene = result.visual_content.scene_analysis
            print(f"\n🎬 Scene Analysis:")
            print(f"   Scene Type: {scene.get('scene_type', 'unknown')}")
            print(f"   Indoor/Outdoor: {scene.get('indoor_outdoor', 'unknown')}")
            print(f"   Confidence: {scene.get('context_confidence', 0):.2f}")
            
            if scene.get('activity_detected'):
                print(f"   Activities:")
                for activity in scene['activity_detected'][:3]:
                    print(f"      - {activity['activity']} ({activity['confidence']:.2f})")
        
        # Display logo/brand detection
        if hasattr(result.visual_content, 'logos_brands') and result.visual_content.logos_brands:
            print(f"\n🏷️ Logos & Brands:")
            for logo in result.visual_content.logos_brands:
                print(f"   {logo['brand_name']} - {logo['type']} (risk: {logo.get('compliance_risk', 'unknown')})")
        
        # Display safety assessment
        if hasattr(result.visual_content, 'safety_assessment') and result.visual_content.safety_assessment:
            safety = result.visual_content.safety_assessment
            print(f"\n🛡️ Content Safety:")
            print(f"   Safe: {safety['safe']}")
            print(f"   Confidence: {safety['confidence']:.2f}")
            
            if safety['flags']:
                print(f"   Flags:")
                for flag in safety['flags']:
                    print(f"      - {flag['category']}: {flag['content']} ({flag['severity']})")
        
        print(f"\n✅ Enhanced image analysis completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run enhanced demo
    demo_enhanced_features()