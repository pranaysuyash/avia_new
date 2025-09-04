"""
Enterprise OCR Processing Engine with Provider Abstraction

This module provides a comprehensive OCR processing system with pluggable provider
architecture, advanced preprocessing, confidence calibration, and policy-driven routing.
"""

import os
import cv2
import numpy as np
import logging
from typing import List, Dict, Any, Optional, Tuple, Union, Protocol
from dataclasses import dataclass, asdict
from enum import Enum
from abc import ABC, abstractmethod
import json
import time
from datetime import datetime
import hashlib
import tempfile
from pathlib import Path
import asyncio
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import threading
from collections import defaultdict
import statistics
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import OCR providers (with fallbacks for missing dependencies)
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("Tesseract not available")

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logger.warning("EasyOCR not available")

try:
    import requests
    CLOUD_PROVIDERS_AVAILABLE = True
except ImportError:
    CLOUD_PROVIDERS_AVAILABLE = False
    logger.warning("Cloud providers not available")


class OCRProvider(Enum):
    """Available OCR providers"""
    TESSERACT = "tesseract"
    EASYOCR = "easyocr"
    GOOGLE_VISION = "google_vision"
    AWS_TEXTRACT = "aws_textract"
    AZURE_COMPUTER_VISION = "azure_computer_vision"
    PADDLE_OCR = "paddle_ocr"


class TextDetectionMethod(Enum):
    """Text detection methods"""
    EAST = "east"
    CRAFT = "craft"
    MSER = "mser"
    CONTOUR = "contour"
    PROVIDER_NATIVE = "provider_native"


class PreprocessingMode(Enum):
    """Preprocessing modes"""
    MINIMAL = "minimal"
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"
    CUSTOM = "custom"


class RoutingPolicy(Enum):
    """OCR engine routing policies"""
    ACCURACY_FIRST = "accuracy_first"
    COST_OPTIMIZED = "cost_optimized"
    LATENCY_OPTIMIZED = "latency_optimized"
    BALANCED = "balanced"
    CUSTOM = "custom"


@dataclass
class BoundingBox:
    """Text bounding box with confidence"""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    text: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def area(self) -> int:
        return self.width * self.height
    
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)


@dataclass
class TextSegment:
    """Detected text segment with metadata"""
    text: str
    confidence: float
    bounding_box: BoundingBox
    language: str
    font_size: Optional[float] = None
    font_style: Optional[str] = None
    text_direction: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['bounding_box'] = self.bounding_box.to_dict()
        return data


@dataclass
class OCRResult:
    """Complete OCR processing result"""
    segments: List[TextSegment]
    processing_time: float
    provider: str
    detection_method: str
    preprocessing_applied: List[str]
    image_hash: str
    confidence_calibrated: bool = False
    language_detected: Optional[str] = None
    quality_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['segments'] = [seg.to_dict() for seg in self.segments]
        return data
    
    def get_text(self, separator: str = " ") -> str:
        """Get all text concatenated"""
        return separator.join(seg.text for seg in self.segments if seg.text.strip())
    
    def get_average_confidence(self) -> float:
        """Get average confidence across all segments"""
        if not self.segments:
            return 0.0
        return statistics.mean(seg.confidence for seg in self.segments)


@dataclass
class OCRConfig:
    """OCR processing configuration"""
    providers: List[OCRProvider] = None
    detection_method: TextDetectionMethod = TextDetectionMethod.PROVIDER_NATIVE
    preprocessing_mode: PreprocessingMode = PreprocessingMode.STANDARD
    languages: List[str] = None
    confidence_threshold: float = 0.5
    enable_confidence_calibration: bool = True
    enable_text_normalization: bool = True
    enable_language_detection: bool = True
    routing_policy: RoutingPolicy = RoutingPolicy.BALANCED
    max_processing_time: float = 30.0
    enable_region_optimization: bool = True
    custom_preprocessing: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.providers is None:
            self.providers = [OCRProvider.TESSERACT, OCRProvider.EASYOCR]
        if self.languages is None:
            self.languages = ['eng']  # Use 'eng' for Tesseract compatibility


@dataclass
class ProviderMetrics:
    """Performance metrics for OCR providers"""
    provider: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_latency: float = 0.0
    average_confidence: float = 0.0
    accuracy_score: float = 0.0
    cost_per_request: float = 0.0
    last_updated: datetime = None
    
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    def update_metrics(self, latency: float, confidence: float, success: bool, cost: float = 0.0):
        """Update provider metrics with new data point"""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        
        # Update running averages
        if self.total_requests == 1:
            self.average_latency = latency
            self.average_confidence = confidence
        else:
            alpha = 0.1  # Exponential moving average factor
            self.average_latency = (1 - alpha) * self.average_latency + alpha * latency
            self.average_confidence = (1 - alpha) * self.average_confidence + alpha * confidence
        
        self.cost_per_request = (1 - 0.1) * self.cost_per_request + 0.1 * cost
        self.last_updated = datetime.now()


class OCRProviderInterface(Protocol):
    """Interface for OCR providers"""
    
    def process_image(self, image: np.ndarray, config: OCRConfig) -> OCRResult:
        """Process image and return OCR result"""
        ...
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        ...
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        ...
    
    def estimate_cost(self, image: np.ndarray) -> float:
        """Estimate processing cost for image"""
        ...


class TesseractProvider:
    """Tesseract OCR provider implementation"""
    
    def __init__(self):
        self.name = "tesseract"
        self.available = TESSERACT_AVAILABLE
        
    def is_available(self) -> bool:
        return self.available and self._check_tesseract_installation()
    
    def _check_tesseract_installation(self) -> bool:
        """Check if Tesseract is properly installed"""
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
    
    def get_supported_languages(self) -> List[str]:
        """Get supported languages from Tesseract"""
        if not self.is_available():
            return []
        
        try:
            langs = pytesseract.get_languages(config='')
            return langs
        except Exception:
            return ['eng']  # Default fallback
    
    def process_image(self, image: np.ndarray, config: OCRConfig) -> OCRResult:
        """Process image with Tesseract"""
        start_time = time.time()
        
        # Prepare Tesseract configuration
        tesseract_config = self._build_tesseract_config(config)
        
        try:
            # Get detailed OCR data
            data = pytesseract.image_to_data(
                image, 
                config=tesseract_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Parse results into segments
            segments = self._parse_tesseract_data(data, config)
            
            processing_time = time.time() - start_time
            image_hash = hashlib.md5(image.tobytes()).hexdigest()
            
            return OCRResult(
                segments=segments,
                processing_time=processing_time,
                provider=self.name,
                detection_method="tesseract_native",
                preprocessing_applied=[],
                image_hash=image_hash,
                language_detected=self._detect_primary_language(segments)
            )
            
        except Exception as e:
            logger.error(f"Tesseract processing failed: {e}")
            processing_time = time.time() - start_time
            return OCRResult(
                segments=[],
                processing_time=processing_time,
                provider=self.name,
                detection_method="tesseract_native",
                preprocessing_applied=[],
                image_hash=hashlib.md5(image.tobytes()).hexdigest()
            )
    
    def _build_tesseract_config(self, config: OCRConfig) -> str:
        """Build Tesseract configuration string"""
        tesseract_config = []
        
        # Language configuration
        if config.languages:
            # Convert 'en' to 'eng' for Tesseract compatibility
            tesseract_langs = []
            for lang in config.languages:
                if lang == 'en':
                    tesseract_langs.append('eng')
                else:
                    tesseract_langs.append(lang)
            lang_string = '+'.join(tesseract_langs)
            tesseract_config.append(f'-l {lang_string}')
        
        # PSM (Page Segmentation Mode)
        tesseract_config.append('--psm 6')  # Uniform block of text
        
        # OEM (OCR Engine Mode)
        tesseract_config.append('--oem 3')  # Default, based on what is available
        
        return ' '.join(tesseract_config)
    
    def _parse_tesseract_data(self, data: Dict, config: OCRConfig) -> List[TextSegment]:
        """Parse Tesseract output data into text segments"""
        segments = []
        
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            confidence = float(data['conf'][i]) / 100.0  # Convert to 0-1 range
            
            # Filter out low-confidence and empty results
            if not text or confidence < config.confidence_threshold:
                continue
            
            # Create bounding box
            bbox = BoundingBox(
                x=data['left'][i],
                y=data['top'][i],
                width=data['width'][i],
                height=data['height'][i],
                confidence=confidence,
                text=text
            )
            
            # Create text segment
            segment = TextSegment(
                text=text,
                confidence=confidence,
                bounding_box=bbox,
                language=config.languages[0] if config.languages else 'en'
            )
            
            segments.append(segment)
        
        return segments
    
    def _detect_primary_language(self, segments: List[TextSegment]) -> Optional[str]:
        """Detect primary language from segments"""
        if not segments:
            return None
        
        # Simple heuristic: return language of highest confidence segment
        best_segment = max(segments, key=lambda s: s.confidence)
        return best_segment.language
    
    def estimate_cost(self, image: np.ndarray) -> float:
        """Estimate processing cost (Tesseract is free)"""
        return 0.0


class EasyOCRProvider:
    """EasyOCR provider implementation"""
    
    def __init__(self):
        self.name = "easyocr"
        self.available = EASYOCR_AVAILABLE
        self._reader_cache = {}
        self._lock = threading.Lock()
    
    def is_available(self) -> bool:
        return self.available
    
    def get_supported_languages(self) -> List[str]:
        """Get supported languages from EasyOCR"""
        if not self.is_available():
            return []
        
        # EasyOCR supported languages (subset)
        return ['en', 'ch_sim', 'ch_tra', 'ja', 'ko', 'fr', 'de', 'es', 'pt', 'ru']
    
    def _get_reader(self, languages: List[str]) -> 'easyocr.Reader':
        """Get cached EasyOCR reader for languages"""
        lang_key = '+'.join(sorted(languages))
        
        with self._lock:
            if lang_key not in self._reader_cache:
                try:
                    self._reader_cache[lang_key] = easyocr.Reader(languages, gpu=False)
                except Exception as e:
                    logger.error(f"Failed to create EasyOCR reader: {e}")
                    # Fallback to English only
                    self._reader_cache[lang_key] = easyocr.Reader(['en'], gpu=False)
            
            return self._reader_cache[lang_key]
    
    def process_image(self, image: np.ndarray, config: OCRConfig) -> OCRResult:
        """Process image with EasyOCR"""
        start_time = time.time()
        
        try:
            # Get appropriate reader
            languages = config.languages if config.languages else ['en']
            reader = self._get_reader(languages)
            
            # Process image
            results = reader.readtext(image)
            
            # Parse results into segments
            segments = self._parse_easyocr_results(results, config)
            
            processing_time = time.time() - start_time
            image_hash = hashlib.md5(image.tobytes()).hexdigest()
            
            return OCRResult(
                segments=segments,
                processing_time=processing_time,
                provider=self.name,
                detection_method="easyocr_native",
                preprocessing_applied=[],
                image_hash=image_hash,
                language_detected=self._detect_primary_language(segments)
            )
            
        except Exception as e:
            logger.error(f"EasyOCR processing failed: {e}")
            processing_time = time.time() - start_time
            return OCRResult(
                segments=[],
                processing_time=processing_time,
                provider=self.name,
                detection_method="easyocr_native",
                preprocessing_applied=[],
                image_hash=hashlib.md5(image.tobytes()).hexdigest()
            )
    
    def _parse_easyocr_results(self, results: List, config: OCRConfig) -> List[TextSegment]:
        """Parse EasyOCR results into text segments"""
        segments = []
        
        for result in results:
            bbox_coords, text, confidence = result
            
            # Filter by confidence threshold
            if confidence < config.confidence_threshold:
                continue
            
            # Calculate bounding box from coordinates
            x_coords = [point[0] for point in bbox_coords]
            y_coords = [point[1] for point in bbox_coords]
            
            x = int(min(x_coords))
            y = int(min(y_coords))
            width = int(max(x_coords) - min(x_coords))
            height = int(max(y_coords) - min(y_coords))
            
            bbox = BoundingBox(
                x=x, y=y, width=width, height=height,
                confidence=confidence, text=text
            )
            
            segment = TextSegment(
                text=text,
                confidence=confidence,
                bounding_box=bbox,
                language=config.languages[0] if config.languages else 'en'
            )
            
            segments.append(segment)
        
        return segments
    
    def _detect_primary_language(self, segments: List[TextSegment]) -> Optional[str]:
        """Detect primary language from segments"""
        if not segments:
            return None
        
        # Return language of highest confidence segment
        best_segment = max(segments, key=lambda s: s.confidence)
        return best_segment.language
    
    def estimate_cost(self, image: np.ndarray) -> float:
        """Estimate processing cost (EasyOCR is free)"""
        return 0.0


class CloudOCRProvider:
    """Base class for cloud OCR providers"""
    
    def __init__(self, provider_name: str):
        self.name = provider_name
        self.available = CLOUD_PROVIDERS_AVAILABLE
    
    def is_available(self) -> bool:
        return self.available and self._check_credentials()
    
    def _check_credentials(self) -> bool:
        """Check if cloud provider credentials are available"""
        # Override in subclasses
        return False
    
    def estimate_cost(self, image: np.ndarray) -> float:
        """Estimate processing cost based on image size"""
        # Base cost estimation (override in subclasses)
        height, width = image.shape[:2]
        pixels = height * width
        
        # Rough cost estimation (varies by provider)
        if pixels < 1000000:  # < 1MP
            return 0.001
        elif pixels < 4000000:  # < 4MP
            return 0.002
        else:
            return 0.005


class ImagePreprocessor:
    """Advanced image preprocessing for OCR optimization"""
    
    def __init__(self):
        self.preprocessing_methods = {
            'grayscale': self._convert_grayscale,
            'denoise': self._denoise_image,
            'threshold': self._apply_threshold,
            'deskew': self._deskew_image,
            'enhance_contrast': self._enhance_contrast,
            'sharpen': self._sharpen_image,
            'resize': self._resize_image,
            'perspective_correction': self._correct_perspective,
            'region_extraction': self._extract_text_regions
        }
    
    def preprocess_image(self, image: np.ndarray, mode: PreprocessingMode, 
                        custom_config: Optional[Dict[str, Any]] = None) -> Tuple[np.ndarray, List[str]]:
        """Apply preprocessing based on mode"""
        applied_methods = []
        processed_image = image.copy()
        
        if mode == PreprocessingMode.MINIMAL:
            processed_image, methods = self._apply_minimal_preprocessing(processed_image)
            applied_methods.extend(methods)
        elif mode == PreprocessingMode.STANDARD:
            processed_image, methods = self._apply_standard_preprocessing(processed_image)
            applied_methods.extend(methods)
        elif mode == PreprocessingMode.AGGRESSIVE:
            processed_image, methods = self._apply_aggressive_preprocessing(processed_image)
            applied_methods.extend(methods)
        elif mode == PreprocessingMode.CUSTOM and custom_config:
            processed_image, methods = self._apply_custom_preprocessing(processed_image, custom_config)
            applied_methods.extend(methods)
        
        return processed_image, applied_methods
    
    def _apply_minimal_preprocessing(self, image: np.ndarray) -> Tuple[np.ndarray, List[str]]:
        """Apply minimal preprocessing"""
        methods = []
        
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            image = self._convert_grayscale(image)
            methods.append('grayscale')
        
        return image, methods
    
    def _apply_standard_preprocessing(self, image: np.ndarray) -> Tuple[np.ndarray, List[str]]:
        """Apply standard preprocessing pipeline"""
        methods = []
        
        # Grayscale conversion
        if len(image.shape) == 3:
            image = self._convert_grayscale(image)
            methods.append('grayscale')
        
        # Denoising
        image = self._denoise_image(image)
        methods.append('denoise')
        
        # Contrast enhancement
        image = self._enhance_contrast(image)
        methods.append('enhance_contrast')
        
        # Adaptive thresholding
        image = self._apply_threshold(image)
        methods.append('threshold')
        
        return image, methods
    
    def _apply_aggressive_preprocessing(self, image: np.ndarray) -> Tuple[np.ndarray, List[str]]:
        """Apply aggressive preprocessing for challenging images"""
        methods = []
        
        # Start with standard preprocessing
        image, std_methods = self._apply_standard_preprocessing(image)
        methods.extend(std_methods)
        
        # Additional aggressive steps
        image = self._deskew_image(image)
        methods.append('deskew')
        
        image = self._sharpen_image(image)
        methods.append('sharpen')
        
        # Perspective correction if needed
        corrected_image = self._correct_perspective(image)
        if not np.array_equal(image, corrected_image):
            image = corrected_image
            methods.append('perspective_correction')
        
        return image, methods
    
    def _apply_custom_preprocessing(self, image: np.ndarray, 
                                  config: Dict[str, Any]) -> Tuple[np.ndarray, List[str]]:
        """Apply custom preprocessing based on configuration"""
        methods = []
        
        for method_name, params in config.items():
            if method_name in self.preprocessing_methods:
                if isinstance(params, dict):
                    image = self.preprocessing_methods[method_name](image, **params)
                else:
                    image = self.preprocessing_methods[method_name](image)
                methods.append(method_name)
        
        return image, methods
    
    def _convert_grayscale(self, image: np.ndarray) -> np.ndarray:
        """Convert image to grayscale"""
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image
    
    def _denoise_image(self, image: np.ndarray) -> np.ndarray:
        """Apply denoising"""
        return cv2.fastNlMeansDenoising(image)
    
    def _apply_threshold(self, image: np.ndarray) -> np.ndarray:
        """Apply adaptive thresholding"""
        return cv2.adaptiveThreshold(
            image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Enhance contrast using CLAHE"""
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(image)
    
    def _sharpen_image(self, image: np.ndarray) -> np.ndarray:
        """Apply sharpening filter"""
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        return cv2.filter2D(image, -1, kernel)
    
    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """Correct skew in image"""
        # Simple deskewing using Hough line detection
        edges = cv2.Canny(image, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        if lines is not None and len(lines) > 0:
            # Calculate average angle
            angles = []
            for line in lines[:10]:  # Use first 10 lines
                rho, theta = line[0]
                angle = theta * 180 / np.pi
                if angle > 90:
                    angle = angle - 180
                angles.append(angle)
            
            if angles:
                avg_angle = np.mean(angles)
                if abs(avg_angle) > 1:  # Only correct if significant skew
                    center = (image.shape[1] // 2, image.shape[0] // 2)
                    rotation_matrix = cv2.getRotationMatrix2D(center, avg_angle, 1.0)
                    return cv2.warpAffine(image, rotation_matrix, (image.shape[1], image.shape[0]))
        
        return image
    
    def _resize_image(self, image: np.ndarray, target_height: int = 800) -> np.ndarray:
        """Resize image while maintaining aspect ratio"""
        height, width = image.shape[:2]
        if height > target_height:
            scale = target_height / height
            new_width = int(width * scale)
            return cv2.resize(image, (new_width, target_height))
        return image
    
    def _correct_perspective(self, image: np.ndarray) -> np.ndarray:
        """Attempt perspective correction"""
        # This is a simplified version - in production you might want more sophisticated methods
        edges = cv2.Canny(image, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            # Approximate contour to polygon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # If we found a quadrilateral with sufficient area
            if len(approx) == 4 and cv2.contourArea(approx) > 1000:
                # Apply perspective transform
                pts = approx.reshape(4, 2).astype(np.float32)
                
                # Order points: top-left, top-right, bottom-right, bottom-left
                rect = self._order_points(pts)
                
                # Calculate dimensions
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
                
                # Apply perspective transform
                matrix = cv2.getPerspectiveTransform(rect, dst)
                return cv2.warpPerspective(image, matrix, (int(width), int(height)))
        
        return image
    
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
    
    def _extract_text_regions(self, image: np.ndarray) -> np.ndarray:
        """Extract potential text regions"""
        # Use MSER to detect text regions
        mser = cv2.MSER_create()
        regions, _ = mser.detectRegions(image)
        
        # Create mask for text regions
        mask = np.zeros(image.shape, dtype=np.uint8)
        for region in regions:
            hull = cv2.convexHull(region.reshape(-1, 1, 2))
            cv2.fillPoly(mask, [hull], 255)
        
        # Apply mask to original image
        return cv2.bitwise_and(image, mask)


class ConfidenceCalibrator:
    """Calibrate OCR confidence scores based on historical accuracy"""
    
    def __init__(self):
        self.calibration_data = defaultdict(list)  # provider -> [(predicted_conf, actual_accuracy)]
        self.calibration_models = {}  # provider -> calibration function
    
    def add_calibration_data(self, provider: str, predicted_confidence: float, actual_accuracy: float):
        """Add calibration data point"""
        self.calibration_data[provider].append((predicted_confidence, actual_accuracy))
        
        # Rebuild calibration model if we have enough data
        if len(self.calibration_data[provider]) >= 10:
            self._build_calibration_model(provider)
    
    def calibrate_confidence(self, provider: str, confidence: float) -> float:
        """Calibrate confidence score for provider"""
        if provider in self.calibration_models:
            return self.calibration_models[provider](confidence)
        return confidence  # Return original if no calibration available
    
    def _build_calibration_model(self, provider: str):
        """Build simple linear calibration model"""
        data = self.calibration_data[provider]
        if len(data) < 10:
            return
        
        # Simple linear regression for calibration
        predicted_confs = [d[0] for d in data]
        actual_accs = [d[1] for d in data]
        
        # Calculate linear fit
        n = len(data)
        sum_x = sum(predicted_confs)
        sum_y = sum(actual_accs)
        sum_xy = sum(x * y for x, y in data)
        sum_x2 = sum(x * x for x in predicted_confs)
        
        # Linear regression: y = ax + b
        if n * sum_x2 - sum_x * sum_x != 0:
            a = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            b = (sum_y - a * sum_x) / n
            
            # Create calibration function
            self.calibration_models[provider] = lambda x: max(0.0, min(1.0, a * x + b))


class TextNormalizer:
    """Normalize and clean OCR text output"""
    
    def __init__(self):
        self.normalization_rules = {
            'remove_extra_spaces': True,
            'fix_common_ocr_errors': True,
            'normalize_punctuation': True,
            'fix_case_errors': True,
            'remove_artifacts': True
        }
    
    def normalize_text(self, text: str, language: str = 'en') -> str:
        """Apply text normalization rules"""
        normalized = text
        
        if self.normalization_rules['remove_extra_spaces']:
            normalized = self._remove_extra_spaces(normalized)
        
        if self.normalization_rules['fix_common_ocr_errors']:
            normalized = self._fix_common_ocr_errors(normalized, language)
        
        if self.normalization_rules['normalize_punctuation']:
            normalized = self._normalize_punctuation(normalized)
        
        if self.normalization_rules['remove_artifacts']:
            normalized = self._remove_artifacts(normalized)
        
        return normalized.strip()
    
    def _remove_extra_spaces(self, text: str) -> str:
        """Remove extra whitespace"""
        import re
        return re.sub(r'\s+', ' ', text)
    
    def _fix_common_ocr_errors(self, text: str, language: str) -> str:
        """Fix common OCR recognition errors"""
        # Common character substitutions
        substitutions = {
            '0': 'O',  # Zero to O in words
            '1': 'I',  # One to I in words
            '5': 'S',  # Five to S in words
            '8': 'B',  # Eight to B in words
            'rn': 'm',  # Common OCR error
            'cl': 'd',  # Common OCR error
        }
        
        # Apply context-aware substitutions
        for old, new in substitutions.items():
            # Only apply if it makes sense in context
            if old in text and self._should_substitute(text, old, new):
                text = text.replace(old, new)
        
        return text
    
    def _should_substitute(self, text: str, old: str, new: str) -> bool:
        """Determine if substitution should be applied based on context"""
        # Simple heuristic: if the text looks like a word (has letters around it)
        import re
        pattern = f'[a-zA-Z]{old}[a-zA-Z]'
        return bool(re.search(pattern, text))
    
    def _normalize_punctuation(self, text: str) -> str:
        """Normalize punctuation marks"""
        # Replace multiple punctuation with single
        import re
        text = re.sub(r'[.]{2,}', '.', text)
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        return text
    
    def _remove_artifacts(self, text: str) -> str:
        """Remove OCR artifacts and noise"""
        import re
        # Remove single characters that are likely artifacts
        text = re.sub(r'\b[^\w\s]\b', '', text)
        # Remove very short "words" that are likely noise
        text = re.sub(r'\b\w{1}\b', '', text)
        return text


class LanguageDetector:
    """Detect language of OCR text"""
    
    def __init__(self):
        # Simple language detection based on character patterns
        self.language_patterns = {
            'en': r'[a-zA-Z\s.,!?;:\'"-]+',
            'es': r'[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ\s.,!?;:\'"-]+',
            'fr': r'[a-zA-ZàâäéèêëïîôöùûüÿçÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÇ\s.,!?;:\'"-]+',
            'de': r'[a-zA-ZäöüßÄÖÜ\s.,!?;:\'"-]+',
            'zh': r'[\u4e00-\u9fff]+',
            'ja': r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]+',
            'ko': r'[\uac00-\ud7af]+',
            'ar': r'[\u0600-\u06ff]+',
            'ru': r'[а-яёА-ЯЁ\s.,!?;:\'"-]+'
        }
    
    def detect_language(self, text: str) -> str:
        """Detect most likely language of text"""
        if not text.strip():
            return 'unknown'
        
        scores = {}
        for lang, pattern in self.language_patterns.items():
            import re
            matches = re.findall(pattern, text)
            if matches:
                # Calculate coverage score
                matched_chars = sum(len(match) for match in matches)
                total_chars = len(text)
                scores[lang] = matched_chars / total_chars if total_chars > 0 else 0
        
        if scores:
            return max(scores, key=scores.get)
        
        return 'en'  # Default to English


class PolicyEngine:
    """Policy-driven OCR engine routing"""
    
    def __init__(self):
        self.provider_metrics = {}
        self.routing_policies = {
            RoutingPolicy.ACCURACY_FIRST: self._accuracy_first_routing,
            RoutingPolicy.COST_OPTIMIZED: self._cost_optimized_routing,
            RoutingPolicy.LATENCY_OPTIMIZED: self._latency_optimized_routing,
            RoutingPolicy.BALANCED: self._balanced_routing
        }
    
    def select_provider(self, available_providers: List[str], policy: RoutingPolicy, 
                       image: np.ndarray, config: OCRConfig) -> str:
        """Select best provider based on policy"""
        if not available_providers:
            raise ValueError("No available providers")
        
        if len(available_providers) == 1:
            return available_providers[0]
        
        if policy in self.routing_policies:
            return self.routing_policies[policy](available_providers, image, config)
        
        # Default to first available
        return available_providers[0]
    
    def _accuracy_first_routing(self, providers: List[str], image: np.ndarray, config: OCRConfig) -> str:
        """Select provider with highest accuracy"""
        best_provider = providers[0]
        best_accuracy = 0.0
        
        for provider in providers:
            if provider in self.provider_metrics:
                accuracy = self.provider_metrics[provider].accuracy_score
                if accuracy > best_accuracy:
                    best_accuracy = accuracy
                    best_provider = provider
        
        return best_provider
    
    def _cost_optimized_routing(self, providers: List[str], image: np.ndarray, config: OCRConfig) -> str:
        """Select provider with lowest cost"""
        best_provider = providers[0]
        best_cost = float('inf')
        
        for provider in providers:
            if provider in self.provider_metrics:
                cost = self.provider_metrics[provider].cost_per_request
                if cost < best_cost:
                    best_cost = cost
                    best_provider = provider
        
        return best_provider
    
    def _latency_optimized_routing(self, providers: List[str], image: np.ndarray, config: OCRConfig) -> str:
        """Select provider with lowest latency"""
        best_provider = providers[0]
        best_latency = float('inf')
        
        for provider in providers:
            if provider in self.provider_metrics:
                latency = self.provider_metrics[provider].average_latency
                if latency < best_latency:
                    best_latency = latency
                    best_provider = provider
        
        return best_provider
    
    def _balanced_routing(self, providers: List[str], image: np.ndarray, config: OCRConfig) -> str:
        """Select provider with best balanced score"""
        best_provider = providers[0]
        best_score = -1.0
        
        for provider in providers:
            if provider in self.provider_metrics:
                metrics = self.provider_metrics[provider]
                
                # Balanced score considering accuracy, latency, and cost
                accuracy_score = metrics.accuracy_score
                latency_score = 1.0 / (1.0 + metrics.average_latency)  # Lower latency = higher score
                cost_score = 1.0 / (1.0 + metrics.cost_per_request)    # Lower cost = higher score
                
                # Weighted combination
                balanced_score = (0.5 * accuracy_score + 0.3 * latency_score + 0.2 * cost_score)
                
                if balanced_score > best_score:
                    best_score = balanced_score
                    best_provider = provider
        
        return best_provider
    
    def update_provider_metrics(self, provider: str, metrics: ProviderMetrics):
        """Update metrics for provider"""
        self.provider_metrics[provider] = metrics


class OCRProcessingService:
    """Enterprise OCR processing service with provider abstraction"""
    
    def __init__(self, config: Optional[OCRConfig] = None):
        self.config = config or OCRConfig()
        self.providers = {}
        self.preprocessor = ImagePreprocessor()
        self.confidence_calibrator = ConfidenceCalibrator()
        self.text_normalizer = TextNormalizer()
        self.language_detector = LanguageDetector()
        self.policy_engine = PolicyEngine()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize providers
        self._initialize_providers()
        
        # Performance metrics
        self.metrics = defaultdict(lambda: ProviderMetrics("unknown"))
        
    def _initialize_providers(self):
        """Initialize available OCR providers"""
        # Initialize Tesseract
        tesseract_provider = TesseractProvider()
        if tesseract_provider.is_available():
            self.providers[OCRProvider.TESSERACT.value] = tesseract_provider
            logger.info("Tesseract provider initialized")
        
        # Initialize EasyOCR
        easyocr_provider = EasyOCRProvider()
        if easyocr_provider.is_available():
            self.providers[OCRProvider.EASYOCR.value] = easyocr_provider
            logger.info("EasyOCR provider initialized")
        
        # Initialize cloud providers (placeholder implementations)
        # In production, these would have full implementations
        if CLOUD_PROVIDERS_AVAILABLE:
            logger.info("Cloud providers available but not implemented in this demo")
        
        if not self.providers:
            logger.warning("No OCR providers available!")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names"""
        return list(self.providers.keys())
    
    def process_image(self, image: np.ndarray, config: Optional[OCRConfig] = None) -> OCRResult:
        """Process single image with OCR"""
        processing_config = config or self.config
        
        # Validate input
        if image is None or image.size == 0:
            raise ValueError("Invalid image input")
        
        # Apply preprocessing
        processed_image, preprocessing_methods = self.preprocessor.preprocess_image(
            image, processing_config.preprocessing_mode, processing_config.custom_preprocessing
        )
        
        # Select provider based on policy
        available_providers = [p for p in processing_config.providers 
                             if p.value in self.providers]
        
        if not available_providers:
            raise RuntimeError("No available OCR providers")
        
        provider_names = [p.value for p in available_providers]
        selected_provider = self.policy_engine.select_provider(
            provider_names, processing_config.routing_policy, processed_image, processing_config
        )
        
        # Process with selected provider
        start_time = time.time()
        try:
            provider = self.providers[selected_provider]
            result = provider.process_image(processed_image, processing_config)
            
            # Post-process results
            result = self._post_process_result(result, processing_config)
            result.preprocessing_applied = preprocessing_methods
            
            # Update metrics
            processing_time = time.time() - start_time
            success = len(result.segments) > 0
            cost = provider.estimate_cost(processed_image)
            
            self.metrics[selected_provider].update_metrics(
                processing_time, result.get_average_confidence(), success, cost
            )
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.metrics[selected_provider].update_metrics(processing_time, 0.0, False, 0.0)
            logger.error(f"OCR processing failed with {selected_provider}: {e}")
            raise
    
    def batch_process_images(self, images: List[np.ndarray], 
                           config: Optional[OCRConfig] = None) -> List[OCRResult]:
        """Process multiple images in batch"""
        processing_config = config or self.config
        
        # Process images in parallel
        futures = []
        for image in images:
            future = self.executor.submit(self.process_image, image, processing_config)
            futures.append(future)
        
        # Collect results
        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result(timeout=processing_config.max_processing_time)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch processing failed for image: {e}")
                # Create empty result for failed image
                results.append(OCRResult(
                    segments=[],
                    processing_time=0.0,
                    provider="failed",
                    detection_method="none",
                    preprocessing_applied=[],
                    image_hash=""
                ))
        
        return results
    
    def _post_process_result(self, result: OCRResult, config: OCRConfig) -> OCRResult:
        """Apply post-processing to OCR result"""
        processed_segments = []
        
        for segment in result.segments:
            # Apply text normalization
            if config.enable_text_normalization:
                normalized_text = self.text_normalizer.normalize_text(
                    segment.text, segment.language
                )
                segment.text = normalized_text
            
            # Apply confidence calibration
            if config.enable_confidence_calibration:
                calibrated_confidence = self.confidence_calibrator.calibrate_confidence(
                    result.provider, segment.confidence
                )
                segment.confidence = calibrated_confidence
            
            # Language detection
            if config.enable_language_detection:
                detected_language = self.language_detector.detect_language(segment.text)
                segment.language = detected_language
            
            # Filter by confidence threshold
            if segment.confidence >= config.confidence_threshold:
                processed_segments.append(segment)
        
        result.segments = processed_segments
        result.confidence_calibrated = config.enable_confidence_calibration
        
        # Detect primary language for result
        if processed_segments:
            result.language_detected = self._detect_result_language(processed_segments)
        
        return result
    
    def _detect_result_language(self, segments: List[TextSegment]) -> str:
        """Detect primary language for entire result"""
        if not segments:
            return "unknown"
        
        # Count languages by confidence-weighted frequency
        language_scores = defaultdict(float)
        for segment in segments:
            language_scores[segment.language] += segment.confidence
        
        if language_scores:
            return max(language_scores, key=language_scores.get)
        
        return "unknown"
    
    def validate_result(self, result: OCRResult, expected_text: Optional[str] = None) -> Dict[str, Any]:
        """Validate OCR result quality"""
        validation_metrics = {
            'segment_count': len(result.segments),
            'average_confidence': result.get_average_confidence(),
            'total_text_length': len(result.get_text()),
            'processing_time': result.processing_time,
            'provider': result.provider,
            'has_text': len(result.segments) > 0
        }
        
        # If expected text is provided, calculate accuracy
        if expected_text:
            extracted_text = result.get_text()
            accuracy = self._calculate_text_accuracy(extracted_text, expected_text)
            validation_metrics['accuracy'] = accuracy
            
            # Add calibration data
            avg_confidence = result.get_average_confidence()
            self.confidence_calibrator.add_calibration_data(
                result.provider, avg_confidence, accuracy
            )
        
        return validation_metrics
    
    def _calculate_text_accuracy(self, extracted: str, expected: str) -> float:
        """Calculate text accuracy using edit distance"""
        if not expected:
            return 1.0 if not extracted else 0.0
        
        # Simple character-level accuracy
        import difflib
        matcher = difflib.SequenceMatcher(None, extracted.lower(), expected.lower())
        return matcher.ratio()
    
    def get_provider_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get performance metrics for all providers"""
        metrics_dict = {}
        for provider_name, metrics in self.metrics.items():
            metrics_dict[provider_name] = {
                'total_requests': metrics.total_requests,
                'success_rate': metrics.success_rate(),
                'average_latency': metrics.average_latency,
                'average_confidence': metrics.average_confidence,
                'accuracy_score': metrics.accuracy_score,
                'cost_per_request': metrics.cost_per_request,
                'last_updated': metrics.last_updated.isoformat() if metrics.last_updated else None
            }
        return metrics_dict
    
    def update_configuration(self, new_config: OCRConfig):
        """Update service configuration"""
        self.config = new_config
        
        # Update policy engine metrics
        for provider_name, metrics in self.metrics.items():
            self.policy_engine.update_provider_metrics(provider_name, metrics)
    
    def estimate_processing_cost(self, images: List[np.ndarray], 
                               config: Optional[OCRConfig] = None) -> Dict[str, Any]:
        """Estimate processing cost for batch of images"""
        processing_config = config or self.config
        
        total_cost = 0.0
        total_time = 0.0
        
        for image in images:
            # Estimate cost per provider
            provider_costs = {}
            for provider_name, provider in self.providers.items():
                cost = provider.estimate_cost(image)
                provider_costs[provider_name] = cost
            
            # Use policy to select provider and get its cost
            available_providers = [p.value for p in processing_config.providers 
                                 if p.value in self.providers]
            
            if available_providers:
                selected_provider = self.policy_engine.select_provider(
                    available_providers, processing_config.routing_policy, image, processing_config
                )
                
                image_cost = provider_costs.get(selected_provider, 0.0)
                total_cost += image_cost
                
                # Estimate processing time
                if selected_provider in self.metrics:
                    estimated_time = self.metrics[selected_provider].average_latency
                else:
                    estimated_time = 2.0  # Default estimate
                
                total_time += estimated_time
        
        return {
            'total_images': len(images),
            'estimated_total_cost': total_cost,
            'estimated_processing_time': total_time,
            'average_cost_per_image': total_cost / len(images) if images else 0.0,
            'average_time_per_image': total_time / len(images) if images else 0.0,
            'routing_policy': processing_config.routing_policy.value
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self.executor.shutdown(wait=True)


# Utility functions for external use
def create_ocr_config(**kwargs) -> OCRConfig:
    """Create OCR configuration with custom parameters"""
    return OCRConfig(**kwargs)


def process_image_with_ocr(image: np.ndarray, **config_kwargs) -> OCRResult:
    """Convenience function to process single image"""
    config = create_ocr_config(**config_kwargs)
    service = OCRProcessingService(config)
    try:
        return service.process_image(image)
    finally:
        service.cleanup()


def batch_process_images_with_ocr(images: List[np.ndarray], **config_kwargs) -> List[OCRResult]:
    """Convenience function to process multiple images"""
    config = create_ocr_config(**config_kwargs)
    service = OCRProcessingService(config)
    try:
        return service.batch_process_images(images)
    finally:
        service.cleanup()


def get_available_ocr_providers() -> List[str]:
    """Get list of available OCR providers"""
    service = OCRProcessingService()
    try:
        return service.get_available_providers()
    finally:
        service.cleanup()


# Text detection utilities (separate from recognition)
class TextDetectionService:
    """Separate text detection service using EAST/CRAFT methods"""
    
    def __init__(self):
        self.detection_methods = {
            TextDetectionMethod.EAST: self._detect_text_east,
            TextDetectionMethod.CRAFT: self._detect_text_craft,
            TextDetectionMethod.MSER: self._detect_text_mser,
            TextDetectionMethod.CONTOUR: self._detect_text_contour
        }
    
    def detect_text_regions(self, image: np.ndarray, 
                          method: TextDetectionMethod = TextDetectionMethod.MSER) -> List[BoundingBox]:
        """Detect text regions in image"""
        if method in self.detection_methods:
            return self.detection_methods[method](image)
        else:
            logger.warning(f"Unsupported detection method: {method}")
            return self._detect_text_mser(image)  # Fallback
    
    def _detect_text_east(self, image: np.ndarray) -> List[BoundingBox]:
        """EAST text detection (requires pre-trained model)"""
        try:
            # Check if EAST model is available
            east_model_path = os.getenv("EAST_MODEL_PATH", "models/east_icdar2015_resnet_v1_50_rbox.pb")
            
            if not os.path.exists(east_model_path):
                logger.warning(f"EAST model not found at {east_model_path}, falling back to MSER")
                return self._detect_text_mser(image)
            
            # Load EAST model
            net = cv2.dnn.readNet(east_model_path)
            
            # Prepare image for EAST
            height, width = image.shape[:2]
            
            # Resize image to multiples of 32 for EAST
            new_width = (width // 32) * 32
            new_height = (height // 32) * 32
            
            # Create blob from image
            blob = cv2.dnn.blobFromImage(
                image, 1.0, (new_width, new_height), (123.68, 116.78, 103.94), swapRB=True, crop=False
            )
            
            # Set input to the network
            net.setInput(blob)
            
            # Run forward pass to get output layers
            output_layers = net.forward(["feature_fusion/Conv_7/Sigmoid", "feature_fusion/concat_3"])
            
            # Extract text regions
            scores = output_layers[0]
            geometry = output_layers[1]
            
            # Decode predictions
            boxes, confidences = self._decode_predictions(scores, geometry)
            
            # Apply non-maximum suppression
            indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
            
            # Create bounding boxes
            bounding_boxes = []
            if len(indices) > 0:
                for i in indices.flatten():
                    x, y, w, h = boxes[i]
                    bounding_boxes.append(BoundingBox(
                        x=int(x),
                        y=int(y),
                        width=int(w),
                        height=int(h),
                        confidence=float(confidences[i])
                    ))
            
            logger.info(f"Detected {len(bounding_boxes)} text regions using EAST")
            return bounding_boxes
            
        except Exception as e:
            logger.warning(f"EAST detection failed: {e}, falling back to MSER")
            return self._detect_text_mser(image)
    
    def _decode_predictions(self, scores, geometry):
        """Decode EAST model predictions"""
        boxes = []
        confidences = []
        
        height, width = scores.shape[2:4]
        for y in range(height):
            scores_data = scores[0, 0, y]
            x_data0 = geometry[0, 0, y]
            x_data1 = geometry[0, 1, y]
            x_data2 = geometry[0, 2, y]
            x_data3 = geometry[0, 3, y]
            angles_data = geometry[0, 4, y]
            
            for x in range(width):
                score = scores_data[x]
                
                # Ignore low-confidence regions
                if score < 0.5:
                    continue
                
                # Compute offset factor
                offset_x, offset_y = x * 4.0, y * 4.0
                
                # Extract rotation angle
                angle = angles_data[x]
                
                # Calculate cos and sin of angle
                cos_a = np.cos(angle)
                sin_a = np.sin(angle)
                
                # Calculate height and width of bounding box
                h = x_data0[x] + x_data2[x]
                w = x_data1[x] + x_data3[x]
                
                # Calculate coordinates of bounding box
                end_x = int(offset_x + (cos_a * x_data1[x]) + (sin_a * x_data2[x]))
                end_y = int(offset_y - (sin_a * x_data1[x]) + (cos_a * x_data2[x]))
                start_x = int(end_x - w)
                start_y = int(end_y - h)
                
                boxes.append((start_x, start_y, w, h))
                confidences.append(float(score))
        
        return boxes, confidences
    
    def _detect_text_craft(self, image: np.ndarray) -> List[BoundingBox]:
        """CRAFT text detection (requires pre-trained model)"""
        try:
            # Check if CRAFT model is available
            craft_model_path = os.getenv("CRAFT_MODEL_PATH", "models/craft_mlt_25k.pth")
            
            if not os.path.exists(craft_model_path):
                logger.warning(f"CRAFT model not found at {craft_model_path}, falling back to MSER")
                return self._detect_text_mser(image)
            
            # Try to import CRAFT dependencies
            try:
                import torch
                from craft_text_detector import Craft
            except ImportError:
                logger.warning("CRAFT dependencies not available, falling back to MSER")
                return self._detect_text_mser(image)
            
            # Initialize CRAFT model
            craft = Craft(
                output_dir="outputs/",
                crop_type="poly",
                cuda=torch.cuda.is_available()
            )
            
            # Convert image to RGB if needed
            if len(image.shape) == 3 and image.shape[2] == 3:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            
            # Run CRAFT detection
            prediction_result = craft.detect_text(rgb_image)
            
            # Extract bounding boxes
            bounding_boxes = []
            for box in prediction_result["boxes"]:
                # Convert polygon to rectangle
                x_coords = [point[0] for point in box]
                y_coords = [point[1] for point in box]
                
                x_min, x_max = min(x_coords), max(x_coords)
                y_min, y_max = min(y_coords), max(y_coords)
                
                bounding_boxes.append(BoundingBox(
                    x=int(x_min),
                    y=int(y_min),
                    width=int(x_max - x_min),
                    height=int(y_max - y_min),
                    confidence=0.9  # Placeholder confidence
                ))
            
            logger.info(f"Detected {len(bounding_boxes)} text regions using CRAFT")
            return bounding_boxes
            
        except Exception as e:
            logger.warning(f"CRAFT detection failed: {e}, falling back to MSER")
            return self._detect_text_mser(image)
    
    def _detect_text_mser(self, image: np.ndarray) -> List[BoundingBox]:
        """MSER-based text detection"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Create MSER detector
        mser = cv2.MSER_create()
        regions, _ = mser.detectRegions(gray)
        
        bounding_boxes = []
        for region in regions:
            if len(region) < 10:  # Filter small regions
                continue
            
            # Calculate bounding box
            x_coords = region[:, 0]
            y_coords = region[:, 1]
            
            x = int(np.min(x_coords))
            y = int(np.min(y_coords))
            width = int(np.max(x_coords) - np.min(x_coords))
            height = int(np.max(y_coords) - np.min(y_coords))
            
            # Filter by aspect ratio and size
            aspect_ratio = width / height if height > 0 else 0
            if 0.1 < aspect_ratio < 10 and width > 10 and height > 5:
                bbox = BoundingBox(
                    x=x, y=y, width=width, height=height,
                    confidence=0.8  # MSER doesn't provide confidence
                )
                bounding_boxes.append(bbox)
        
        return bounding_boxes
    
    def _detect_text_contour(self, image: np.ndarray) -> List[BoundingBox]:
        """Contour-based text detection"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Apply threshold
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        bounding_boxes = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by size and aspect ratio
            aspect_ratio = w / h if h > 0 else 0
            area = cv2.contourArea(contour)
            
            if (area > 100 and 0.2 < aspect_ratio < 8 and 
                w > 15 and h > 8):
                
                bbox = BoundingBox(
                    x=x, y=y, width=w, height=h,
                    confidence=0.7  # Estimated confidence
                )
                bounding_boxes.append(bbox)
        
        return bounding_boxes


if __name__ == "__main__":
    # Example usage and testing
    import sys
    
    def create_test_image():
        """Create a test image with text"""
        # Create white background
        img = np.ones((200, 400, 3), dtype=np.uint8) * 255
        
        # Add some text
        cv2.putText(img, "Hello World", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(img, "OCR Test", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(img, "Enterprise System", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        
        return img
    
    def test_basic_ocr():
        """Test basic OCR functionality"""
        print("Testing Basic OCR Functionality")
        print("=" * 50)
        
        # Create test image
        test_image = create_test_image()
        
        # Create OCR service
        config = OCRConfig(
            providers=[OCRProvider.TESSERACT, OCRProvider.EASYOCR],
            preprocessing_mode=PreprocessingMode.STANDARD,
            confidence_threshold=0.3,
            routing_policy=RoutingPolicy.BALANCED
        )
        
        service = OCRProcessingService(config)
        
        try:
            print(f"Available providers: {service.get_available_providers()}")
            
            # Process image
            result = service.process_image(test_image)
            
            print(f"\nOCR Results:")
            print(f"Provider: {result.provider}")
            print(f"Processing time: {result.processing_time:.3f}s")
            print(f"Segments found: {len(result.segments)}")
            print(f"Average confidence: {result.get_average_confidence():.3f}")
            print(f"Extracted text: '{result.get_text()}'")
            
            # Validate result
            expected_text = "Hello World OCR Test Enterprise System"
            validation = service.validate_result(result, expected_text)
            print(f"\nValidation metrics:")
            for key, value in validation.items():
                print(f"  {key}: {value}")
            
            # Show provider metrics
            print(f"\nProvider metrics:")
            metrics = service.get_provider_metrics()
            for provider, provider_metrics in metrics.items():
                print(f"  {provider}:")
                for metric, value in provider_metrics.items():
                    print(f"    {metric}: {value}")
        
        finally:
            service.cleanup()
    
    def test_text_detection():
        """Test text detection functionality"""
        print("\nTesting Text Detection")
        print("=" * 50)
        
        # Create test image
        test_image = create_test_image()
        
        # Test text detection
        detector = TextDetectionService()
        regions = detector.detect_text_regions(test_image, TextDetectionMethod.MSER)
        
        print(f"Detected {len(regions)} text regions:")
        for i, region in enumerate(regions):
            print(f"  Region {i+1}: x={region.x}, y={region.y}, "
                  f"w={region.width}, h={region.height}, conf={region.confidence:.3f}")
    
    def test_preprocessing():
        """Test image preprocessing"""
        print("\nTesting Image Preprocessing")
        print("=" * 50)
        
        # Create test image
        test_image = create_test_image()
        
        # Test different preprocessing modes
        preprocessor = ImagePreprocessor()
        
        modes = [
            PreprocessingMode.MINIMAL,
            PreprocessingMode.STANDARD,
            PreprocessingMode.AGGRESSIVE
        ]
        
        for mode in modes:
            processed, methods = preprocessor.preprocess_image(test_image, mode)
            print(f"{mode.value}: Applied methods: {methods}")
    
    # Run tests
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_basic_ocr()
        test_text_detection()
        test_preprocessing()
    else:
        print("OCR Processing Engine loaded successfully!")
        print("Available providers:", get_available_ocr_providers())
        print("Run with 'test' argument to execute tests")