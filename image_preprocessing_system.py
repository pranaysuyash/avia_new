#!/usr/bin/env python3
"""
Task 82: Advanced Image Preprocessing System
Comprehensive image enhancement and preprocessing for optimal OCR and analysis
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import skimage
from skimage import restoration, filters, morphology, exposure, feature
from skimage.segmentation import clear_border
from skimage.measure import label, regionprops
from typing import Tuple, List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import logging
import tempfile
import os
from datetime import datetime
import json

logger = logging.getLogger(__name__)

@dataclass
class PreprocessingConfig:
    """Configuration for image preprocessing operations"""
    # Noise reduction
    enable_denoising: bool = True
    denoise_method: str = "bilateral"  # bilateral, gaussian, median, nlm
    denoise_strength: float = 0.5  # 0.0 to 1.0
    
    # Contrast and brightness
    auto_contrast: bool = True
    contrast_factor: float = 1.2
    brightness_factor: float = 1.0
    gamma_correction: float = 1.0
    
    # Sharpening
    enable_sharpening: bool = True
    sharpen_method: str = "unsharp_mask"  # unsharp_mask, kernel, adaptive
    sharpen_strength: float = 0.5
    
    # Geometric corrections
    auto_deskew: bool = True
    auto_rotate: bool = True
    perspective_correction: bool = False
    
    # Resolution enhancement
    upscale_factor: float = 2.0
    interpolation_method: str = "bicubic"  # nearest, bilinear, bicubic, lanczos
    
    # Binarization and thresholding
    auto_threshold: bool = True
    threshold_method: str = "otsu"  # otsu, adaptive_gaussian, adaptive_mean, sauvola
    invert_if_needed: bool = True
    
    # Morphological operations
    enable_morphology: bool = True
    morphology_operations: List[str] = field(default_factory=lambda: ["opening", "closing"])
    kernel_size: int = 3
    
    # Content-aware processing
    detect_text_regions: bool = True
    preserve_aspect_ratio: bool = True
    remove_borders: bool = True
    
    # Output format
    output_format: str = "RGB"  # RGB, GRAY, L
    target_dpi: int = 300

@dataclass
class PreprocessingResult:
    """Result of image preprocessing operations"""
    processed_image: np.ndarray
    original_image: np.ndarray
    operations_applied: List[str]
    quality_metrics: Dict[str, float]
    processing_time: float
    config_used: PreprocessingConfig
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def save_comparison(self, output_path: str):
        """Save before/after comparison"""
        # Create side-by-side comparison
        orig_h, orig_w = self.original_image.shape[:2]
        proc_h, proc_w = self.processed_image.shape[:2]
        
        # Resize to same height
        target_height = max(orig_h, proc_h)
        orig_resized = cv2.resize(self.original_image, 
                                (int(orig_w * target_height / orig_h), target_height))
        proc_resized = cv2.resize(self.processed_image,
                                (int(proc_w * target_height / proc_h), target_height))
        
        # Concatenate horizontally
        comparison = np.hstack([orig_resized, proc_resized])
        cv2.imwrite(output_path, comparison)

class ImagePreprocessor:
    """Advanced image preprocessing system for OCR and analysis optimization"""
    
    def __init__(self, config: Optional[PreprocessingConfig] = None):
        self.config = config or PreprocessingConfig()
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        
    def preprocess_image(self, image_input: Union[str, np.ndarray, Image.Image],
                        config: Optional[PreprocessingConfig] = None) -> PreprocessingResult:
        """
        Comprehensive image preprocessing pipeline
        
        Args:
            image_input: Image file path, numpy array, or PIL Image
            config: Custom preprocessing configuration
            
        Returns:
            PreprocessingResult with processed image and metadata
        """
        start_time = datetime.now()
        config = config or self.config
        operations_applied = []
        
        try:
            # Load and convert image
            original_image = self._load_image(image_input)
            processed_image = original_image.copy()
            
            # 1. Initial quality assessment
            initial_metrics = self._assess_image_quality(processed_image)
            operations_applied.append("quality_assessment")
            
            # 2. Geometric corrections first
            if config.auto_deskew:
                processed_image = self._deskew_image(processed_image)
                operations_applied.append("deskew")
            
            if config.auto_rotate:
                processed_image = self._auto_rotate(processed_image)
                operations_applied.append("auto_rotate")
            
            if config.perspective_correction:
                processed_image = self._correct_perspective(processed_image)
                operations_applied.append("perspective_correction")
            
            # 3. Resolution enhancement
            if config.upscale_factor > 1.0:
                processed_image = self._upscale_image(processed_image, config)
                operations_applied.append("upscale")
            
            # 4. Noise reduction
            if config.enable_denoising:
                processed_image = self._denoise_image(processed_image, config)
                operations_applied.append(f"denoise_{config.denoise_method}")
            
            # 5. Contrast and brightness enhancement
            if config.auto_contrast:
                processed_image = self._enhance_contrast(processed_image, config)
                operations_applied.append("contrast_enhancement")
            
            # 6. Gamma correction
            if config.gamma_correction != 1.0:
                processed_image = self._apply_gamma_correction(processed_image, config.gamma_correction)
                operations_applied.append("gamma_correction")
            
            # 7. Sharpening
            if config.enable_sharpening:
                processed_image = self._sharpen_image(processed_image, config)
                operations_applied.append(f"sharpen_{config.sharpen_method}")
            
            # 8. Text region detection and optimization
            if config.detect_text_regions:
                processed_image = self._optimize_text_regions(processed_image)
                operations_applied.append("text_optimization")
            
            # 9. Binarization and thresholding
            if config.auto_threshold:
                processed_image = self._apply_threshold(processed_image, config)
                operations_applied.append(f"threshold_{config.threshold_method}")
            
            # 10. Morphological operations
            if config.enable_morphology:
                processed_image = self._apply_morphology(processed_image, config)
                operations_applied.append("morphology")
            
            # 11. Border removal
            if config.remove_borders:
                processed_image = self._remove_borders(processed_image)
                operations_applied.append("border_removal")
            
            # 12. Final quality assessment
            final_metrics = self._assess_image_quality(processed_image)
            quality_improvement = self._calculate_improvement(initial_metrics, final_metrics)
            
            # 13. Format conversion
            processed_image = self._convert_format(processed_image, config.output_format)
            operations_applied.append(f"format_{config.output_format}")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return PreprocessingResult(
                processed_image=processed_image,
                original_image=original_image,
                operations_applied=operations_applied,
                quality_metrics=quality_improvement,
                processing_time=processing_time,
                config_used=config,
                metadata={
                    'initial_metrics': initial_metrics,
                    'final_metrics': final_metrics,
                    'original_shape': original_image.shape,
                    'processed_shape': processed_image.shape
                }
            )
            
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            raise
    
    def _load_image(self, image_input: Union[str, np.ndarray, Image.Image]) -> np.ndarray:
        """Load image from various input types"""
        if isinstance(image_input, str):
            if not os.path.exists(image_input):
                raise FileNotFoundError(f"Image file not found: {image_input}")
            return cv2.imread(image_input, cv2.IMREAD_COLOR)
        elif isinstance(image_input, Image.Image):
            return np.array(image_input)
        elif isinstance(image_input, np.ndarray):
            return image_input.copy()
        else:
            raise ValueError("Unsupported image input type")
    
    def _assess_image_quality(self, image: np.ndarray) -> Dict[str, float]:
        """Assess image quality metrics"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Sharpness (Laplacian variance)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Contrast (standard deviation)
        contrast = gray.std()
        
        # Brightness (mean)
        brightness = gray.mean()
        
        # Noise estimation (using bilateral filter difference)
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        noise_level = np.mean((gray.astype(float) - denoised.astype(float))**2)
        
        return {
            'sharpness': float(laplacian_var),
            'contrast': float(contrast),
            'brightness': float(brightness),
            'noise_level': float(noise_level)
        }
    
    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """Automatically deskew image using Hough line detection"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Hough line detection
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        if lines is not None:
            # Calculate average angle
            angles = []
            for line in lines:
                rho, theta = line[0]
                angle = (theta - np.pi/2) * 180 / np.pi
                if abs(angle) < 45:  # Only consider reasonable skew angles
                    angles.append(angle)
            
            if angles:
                avg_angle = np.median(angles)
                if abs(avg_angle) > 0.5:  # Only rotate if significant skew
                    return self._rotate_image(image, avg_angle)
        
        return image
    
    def _auto_rotate(self, image: np.ndarray) -> np.ndarray:
        """Auto-rotate image to correct orientation"""
        # Simple implementation - can be enhanced with ML-based orientation detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Check if image needs 90-degree rotation based on aspect ratio and content
        height, width = gray.shape
        if height > width * 1.5:  # Likely needs rotation
            # Analyze text direction using gradients
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            
            horizontal_edges = np.mean(np.abs(grad_y))
            vertical_edges = np.mean(np.abs(grad_x))
            
            if vertical_edges > horizontal_edges * 1.2:
                return self._rotate_image(image, 90)
        
        return image
    
    def _rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        """Rotate image by given angle"""
        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Calculate new image size
        cos = np.abs(rotation_matrix[0, 0])
        sin = np.abs(rotation_matrix[0, 1])
        new_width = int((height * sin) + (width * cos))
        new_height = int((height * cos) + (width * sin))
        
        # Adjust rotation matrix
        rotation_matrix[0, 2] += (new_width / 2) - center[0]
        rotation_matrix[1, 2] += (new_height / 2) - center[1]
        
        return cv2.warpAffine(image, rotation_matrix, (new_width, new_height), 
                             borderValue=(255, 255, 255))
    
    def _correct_perspective(self, image: np.ndarray) -> np.ndarray:
        """Correct perspective distortion"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Find contours
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Find largest rectangular contour
        for contour in sorted(contours, key=cv2.contourArea, reverse=True):
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
            
            if len(approx) == 4:
                # Found quadrilateral, apply perspective correction
                pts = approx.reshape(4, 2).astype(np.float32)
                
                # Order points: top-left, top-right, bottom-right, bottom-left
                rect = self._order_points(pts)
                
                # Calculate target dimensions
                width_top = np.linalg.norm(rect[1] - rect[0])
                width_bottom = np.linalg.norm(rect[2] - rect[3])
                width = max(int(width_top), int(width_bottom))
                
                height_left = np.linalg.norm(rect[3] - rect[0])
                height_right = np.linalg.norm(rect[2] - rect[1])
                height = max(int(height_left), int(height_right))
                
                # Define destination points
                dst = np.array([[0, 0], [width, 0], [width, height], [0, height]], dtype=np.float32)
                
                # Apply perspective transform
                transform_matrix = cv2.getPerspectiveTransform(rect, dst)
                return cv2.warpPerspective(image, transform_matrix, (width, height))
        
        return image
    
    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        """Order points in clockwise order starting from top-left"""
        # Sum and difference to find corners
        sum_pts = pts.sum(axis=1)
        diff_pts = np.diff(pts, axis=1)
        
        rect = np.zeros((4, 2), dtype=np.float32)
        rect[0] = pts[np.argmin(sum_pts)]  # top-left
        rect[2] = pts[np.argmax(sum_pts)]  # bottom-right
        rect[1] = pts[np.argmin(diff_pts)]  # top-right
        rect[3] = pts[np.argmax(diff_pts)]  # bottom-left
        
        return rect
    
    def _upscale_image(self, image: np.ndarray, config: PreprocessingConfig) -> np.ndarray:
        """Upscale image using specified method"""
        height, width = image.shape[:2]
        new_width = int(width * config.upscale_factor)
        new_height = int(height * config.upscale_factor)
        
        interpolation_map = {
            'nearest': cv2.INTER_NEAREST,
            'bilinear': cv2.INTER_LINEAR,
            'bicubic': cv2.INTER_CUBIC,
            'lanczos': cv2.INTER_LANCZOS4
        }
        
        interpolation = interpolation_map.get(config.interpolation_method, cv2.INTER_CUBIC)
        return cv2.resize(image, (new_width, new_height), interpolation=interpolation)
    
    def _denoise_image(self, image: np.ndarray, config: PreprocessingConfig) -> np.ndarray:
        """Apply denoising based on method"""
        if config.denoise_method == "bilateral":
            d = int(9 * config.denoise_strength)
            sigma_color = int(75 * config.denoise_strength)
            sigma_space = int(75 * config.denoise_strength)
            return cv2.bilateralFilter(image, d, sigma_color, sigma_space)
        
        elif config.denoise_method == "gaussian":
            ksize = int(5 * config.denoise_strength)
            if ksize % 2 == 0:
                ksize += 1
            return cv2.GaussianBlur(image, (ksize, ksize), 0)
        
        elif config.denoise_method == "median":
            ksize = int(5 * config.denoise_strength)
            if ksize % 2 == 0:
                ksize += 1
            return cv2.medianBlur(image, ksize)
        
        elif config.denoise_method == "nlm":
            return cv2.fastNlMeansDenoisingColored(image, None, 
                                                  h=10 * config.denoise_strength,
                                                  hColor=10 * config.denoise_strength,
                                                  templateWindowSize=7,
                                                  searchWindowSize=21)
        
        return image
    
    def _enhance_contrast(self, image: np.ndarray, config: PreprocessingConfig) -> np.ndarray:
        """Enhance image contrast"""
        # Convert to LAB for better contrast enhancement
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Merge channels
        enhanced = cv2.merge([l, a, b])
        return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    
    def _apply_gamma_correction(self, image: np.ndarray, gamma: float) -> np.ndarray:
        """Apply gamma correction"""
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype(np.uint8)
        return cv2.LUT(image, table)
    
    def _sharpen_image(self, image: np.ndarray, config: PreprocessingConfig) -> np.ndarray:
        """Apply sharpening based on method"""
        if config.sharpen_method == "kernel":
            kernel = np.array([[-1, -1, -1], 
                              [-1, 9, -1], 
                              [-1, -1, -1]]) * config.sharpen_strength
            return cv2.filter2D(image, -1, kernel)
        
        elif config.sharpen_method == "unsharp_mask":
            gaussian_blurred = cv2.GaussianBlur(image, (0, 0), 2.0)
            return cv2.addWeighted(image, 1.0 + config.sharpen_strength, 
                                 gaussian_blurred, -config.sharpen_strength, 0)
        
        return image
    
    def _optimize_text_regions(self, image: np.ndarray) -> np.ndarray:
        """Optimize text regions for better OCR"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Find text regions using MSER
        mser = cv2.MSER_create()
        regions, _ = mser.detectRegions(gray)
        
        # Create mask for text regions
        mask = np.zeros(gray.shape, dtype=np.uint8)
        for region in regions:
            hull = cv2.convexHull(region.reshape(-1, 1, 2))
            cv2.fillPoly(mask, [hull], 255)
        
        # Apply different processing to text regions
        text_enhanced = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                            cv2.THRESH_BINARY, 11, 2)
        
        # Combine with original
        result = gray.copy()
        result[mask > 0] = text_enhanced[mask > 0]
        
        return result if len(image.shape) == 2 else cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
    
    def _apply_threshold(self, image: np.ndarray, config: PreprocessingConfig) -> np.ndarray:
        """Apply thresholding based on method"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        if config.threshold_method == "otsu":
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        elif config.threshold_method == "adaptive_gaussian":
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                         cv2.THRESH_BINARY, 11, 2)
        
        elif config.threshold_method == "adaptive_mean":
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                         cv2.THRESH_BINARY, 11, 2)
        
        else:  # sauvola
            # Implement Sauvola thresholding
            thresh = self._sauvola_threshold(gray)
        
        # Invert if needed
        if config.invert_if_needed:
            if np.mean(thresh) > 127:  # More white pixels than black
                thresh = cv2.bitwise_not(thresh)
        
        return thresh if len(image.shape) == 2 else cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
    
    def _sauvola_threshold(self, image: np.ndarray, k: float = 0.2, r: float = 128) -> np.ndarray:
        """Sauvola local thresholding"""
        # Window size
        w = 15
        
        # Calculate local mean and variance
        mean = cv2.boxFilter(image.astype(np.float64), -1, (w, w))
        sqmean = cv2.boxFilter((image.astype(np.float64))**2, -1, (w, w))
        variance = sqmean - mean**2
        
        # Sauvola threshold
        threshold = mean * (1 + k * ((variance**0.5 / r) - 1))
        
        # Apply threshold
        return ((image > threshold) * 255).astype(np.uint8)
    
    def _apply_morphology(self, image: np.ndarray, config: PreprocessingConfig) -> np.ndarray:
        """Apply morphological operations"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, 
                                         (config.kernel_size, config.kernel_size))
        
        result = gray.copy()
        for operation in config.morphology_operations:
            if operation == "opening":
                result = cv2.morphologyEx(result, cv2.MORPH_OPEN, kernel)
            elif operation == "closing":
                result = cv2.morphologyEx(result, cv2.MORPH_CLOSE, kernel)
            elif operation == "erosion":
                result = cv2.erode(result, kernel, iterations=1)
            elif operation == "dilation":
                result = cv2.dilate(result, kernel, iterations=1)
        
        return result if len(image.shape) == 2 else cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
    
    def _remove_borders(self, image: np.ndarray) -> np.ndarray:
        """Remove image borders and margins"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Find content boundaries
        coords = cv2.findNonZero(gray)
        if coords is not None:
            x, y, w, h = cv2.boundingRect(coords)
            # Add small margin
            margin = 10
            x = max(0, x - margin)
            y = max(0, y - margin)
            w = min(gray.shape[1] - x, w + 2 * margin)
            h = min(gray.shape[0] - y, h + 2 * margin)
            
            return image[y:y+h, x:x+w]
        
        return image
    
    def _convert_format(self, image: np.ndarray, format_type: str) -> np.ndarray:
        """Convert image to specified format"""
        if format_type == "GRAY" and len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        elif format_type == "RGB" and len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        elif format_type == "RGB" and len(image.shape) == 2:
            return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        
        return image
    
    def _calculate_improvement(self, initial: Dict[str, float], 
                             final: Dict[str, float]) -> Dict[str, float]:
        """Calculate quality improvement metrics"""
        improvement = {}
        for key in initial:
            if key in final:
                if key == 'noise_level':
                    # Lower noise is better
                    improvement[f"{key}_improvement"] = (initial[key] - final[key]) / initial[key] * 100
                else:
                    # Higher values are better
                    improvement[f"{key}_improvement"] = (final[key] - initial[key]) / initial[key] * 100
        
        return improvement

    def batch_preprocess(self, image_paths: List[str], 
                        output_dir: str,
                        config: Optional[PreprocessingConfig] = None) -> List[PreprocessingResult]:
        """Batch process multiple images"""
        results = []
        os.makedirs(output_dir, exist_ok=True)
        
        for i, image_path in enumerate(image_paths):
            try:
                result = self.preprocess_image(image_path, config)
                
                # Save processed image
                output_path = os.path.join(output_dir, f"processed_{i:04d}.png")
                cv2.imwrite(output_path, result.processed_image)
                
                # Save comparison
                comparison_path = os.path.join(output_dir, f"comparison_{i:04d}.png")
                result.save_comparison(comparison_path)
                
                results.append(result)
                logger.info(f"Processed {image_path} -> {output_path}")
                
            except Exception as e:
                logger.error(f"Failed to process {image_path}: {e}")
        
        return results

# Example usage and testing
if __name__ == "__main__":
    # Create preprocessor
    config = PreprocessingConfig(
        enable_denoising=True,
        auto_contrast=True,
        enable_sharpening=True,
        auto_deskew=True,
        upscale_factor=2.0
    )
    
    preprocessor = ImagePreprocessor(config)
    
    print("Image Preprocessing System - Task 82 Implementation")
    print("Features:")
    print("- Advanced denoising (bilateral, gaussian, median, NLM)")
    print("- Auto contrast and brightness enhancement")
    print("- Intelligent sharpening")
    print("- Automatic deskewing and rotation")
    print("- Perspective correction")
    print("- Text region optimization")
    print("- Multiple thresholding methods")
    print("- Morphological operations")
    print("- Quality metrics and assessment")
    print("- Batch processing capabilities")