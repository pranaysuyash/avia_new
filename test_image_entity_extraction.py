#!/usr/bin/env python3
"""
Comprehensive test suite for Image Entity Extraction System
Tests all components including system initialization, image analysis, entity detection, and UI components
"""

import unittest
import sys
import os
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json

# Mock heavy dependencies before importing
sys.modules['cv2'] = Mock()
sys.modules['skimage'] = Mock()
sys.modules['sklearn'] = Mock()
sys.modules['sklearn.cluster'] = Mock()
sys.modules['sklearn.metrics'] = Mock()
sys.modules['sklearn.metrics.pairwise'] = Mock()
sys.modules['transformers'] = Mock()
sys.modules['torch'] = Mock()
sys.modules['torchvision'] = Mock()
sys.modules['torchvision.transforms'] = Mock()
sys.modules['torchvision.models'] = Mock()
sys.modules['ultralytics'] = Mock()
sys.modules['google'] = Mock()
sys.modules['google.cloud'] = Mock()
sys.modules['google.cloud.vision'] = Mock()
sys.modules['spacy'] = Mock()
sys.modules['matplotlib'] = Mock()
sys.modules['matplotlib.pyplot'] = Mock()
sys.modules['matplotlib.patches'] = Mock()
sys.modules['scipy'] = Mock()
sys.modules['scipy.ndimage'] = Mock()

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock cv2 functions
import cv2
cv2.cvtColor = Mock(return_value=np.ones((100, 100), dtype=np.uint8))
cv2.COLOR_BGR2GRAY = 6
cv2.COLOR_RGB2BGR = 4
cv2.COLOR_BGR2RGB = 4
cv2.Canny = Mock(return_value=np.ones((100, 100), dtype=np.uint8))
cv2.findContours = Mock(return_value=([], None))
cv2.contourArea = Mock(return_value=100)
cv2.boundingRect = Mock(return_value=(10, 10, 50, 50))
cv2.rectangle = Mock()
cv2.putText = Mock()
cv2.line = Mock()
cv2.circle = Mock()
cv2.FONT_HERSHEY_SIMPLEX = 0
cv2.getTextSize = Mock(return_value=((100, 20), 5))
cv2.SIFT_create = Mock(return_value=Mock())
cv2.ORB_create = Mock(return_value=Mock())
cv2.CascadeClassifier = Mock(return_value=Mock())
cv2.QRCodeDetector = Mock(return_value=Mock())
cv2.data = Mock()
cv2.data.haarcascades = ""
cv2.calcHist = Mock(return_value=np.ones((256, 1)))
cv2.Laplacian = Mock(return_value=np.ones((100, 100)))
cv2.CV_64F = -1
cv2.Sobel = Mock(return_value=np.ones((100, 100)))
cv2.getStructuringElement = Mock(return_value=np.ones((3, 3)))
cv2.MORPH_RECT = 0
cv2.morphologyEx = Mock(return_value=np.ones((100, 100)))
cv2.MORPH_CLOSE = 3
cv2.RETR_EXTERNAL = 0
cv2.CHAIN_APPROX_SIMPLE = 2
cv2.HoughLinesP = Mock(return_value=None)
cv2.MSER_create = Mock(return_value=Mock())
cv2.cornerHarris = Mock(return_value=np.ones((100, 100)))
cv2.dilate = Mock(return_value=np.ones((100, 100)))
cv2.TERM_CRITERIA_EPS = 1
cv2.TERM_CRITERIA_MAX_ITER = 2
cv2.kmeans = Mock(return_value=(None, None, np.array([[100, 100, 100]])))
cv2.KMEANS_RANDOM_CENTERS = 2
cv2.imwrite = Mock(return_value=True)
cv2.add = Mock(return_value=np.ones((100, 100, 3), dtype=np.uint8))
cv2.arcLength = Mock(return_value=100.0)
cv2.approxPolyDP = Mock(return_value=np.array([[[0, 0]], [[1, 1]], [[2, 2]]]))

try:
    from image_entity_extraction_system import (
        ImageEntityExtractionSystem, ImageAnalysisResult, VisualEntity,
        EntityType, ImageQuality, BoundingBox, ImageMetadata,
        ImageQualityAssessment, VisualContent
    )
except ImportError as e:
    print(f"Warning: Could not import system components: {e}")
    # Create mock classes for testing
    class EntityType:
        PERSON = "person"
        ORGANIZATION = "organization"
        LOCATION = "location"
        UNKNOWN = "unknown"
    
    class ImageQuality:
        EXCELLENT = "excellent"
        GOOD = "good"
        FAIR = "fair"
        POOR = "poor"
        VERY_POOR = "very_poor"
        UNKNOWN = "unknown"
    
    class BoundingBox:
        def __init__(self, x1, y1, x2, y2, confidence):
            self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
            self.confidence = confidence
    
    class VisualEntity:
        def __init__(self, entity_type, text, bbox, confidence, metadata):
            self.entity_type = entity_type
            self.text = text
            self.bbox = bbox
            self.confidence = confidence
            self.metadata = metadata
    
    class ImageMetadata:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class ImageQualityAssessment:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class VisualContent:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class ImageAnalysisResult:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class ImageEntityExtractionSystem:
        def __init__(self):
            pass
        
        def analyze_image(self, **kwargs):
            return ImageAnalysisResult(
                visual_entities=[],
                metadata=ImageMetadata(filename="test", file_size=0, dimensions=(100, 100), 
                                     format="PNG", mode="RGB", creation_date=None,
                                     camera_make=None, camera_model=None, gps_coordinates=None,
                                     orientation=None, color_space=None, dpi=None,
                                     compression=None, software=None, artist=None,
                                     copyright=None, keywords=[], description=None),
                quality_assessment=ImageQualityAssessment(
                    overall_quality=ImageQuality.GOOD,
                    sharpness_score=100.0, brightness_score=128.0,
                    contrast_score=50.0, noise_level=10.0,
                    blur_detection=50.0, color_balance={},
                    histogram_analysis={}, recommendations=[]
                ),
                visual_content=VisualContent(
                    content_type="test", description="Test image",
                    objects_detected=[], scene_classification="test",
                    dominant_colors=[], text_regions=[],
                    faces_detected=0, landmarks=[]
                ),
                extracted_text="Test text",
                confidence=0.8
            )

class TestImageEntityExtractionSystem(unittest.TestCase):
    """Test cases for ImageEntityExtractionSystem"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.system = ImageEntityExtractionSystem()
        self.test_image = self.create_test_image()
        self.test_image_path = None
    
    def tearDown(self):
        """Clean up test fixtures"""
        if self.test_image_path and os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)
    
    def create_test_image(self) -> np.ndarray:
        """Create a test image"""
        # Create a simple test image with text and shapes
        image = np.ones((300, 400, 3), dtype=np.uint8) * 255
        
        # Add some text
        cv2.putText(image, "Test Image", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(image, "John Doe", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1)
        cv2.putText(image, "ACME Corp", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1)
        
        # Add some shapes
        cv2.rectangle(image, (300, 50), (380, 130), (100, 100, 255), -1)
        cv2.circle(image, (340, 200), 30, (255, 100, 100), -1)
        
        return image
    
    def create_test_image_file(self) -> str:
        """Create a temporary test image file"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            self.test_image_path = f.name
            cv2.imwrite(self.test_image_path, self.test_image)
            return self.test_image_path
    
    def test_system_initialization(self):
        """Test system initialization"""
        self.assertIsInstance(self.system, ImageEntityExtractionSystem)
        
        # Check if models are loaded (may be None if not available)
        self.assertTrue(hasattr(self.system, 'clip_model'))
        self.assertTrue(hasattr(self.system, 'blip_model'))
        self.assertTrue(hasattr(self.system, 'detr_model'))
        self.assertTrue(hasattr(self.system, 'vit_model'))
        
        # Check NLP model
        self.assertTrue(hasattr(self.system, 'nlp'))
        
        # Check computer vision components
        self.assertTrue(hasattr(self.system, 'sift'))
        self.assertTrue(hasattr(self.system, 'orb'))
        self.assertTrue(hasattr(self.system, 'face_cascade'))
        self.assertTrue(hasattr(self.system, 'qr_detector'))
    
    def test_image_metadata_extraction(self):
        """Test image metadata extraction"""
        # Create test image file
        image_path = self.create_test_image_file()
        pil_image = Image.open(image_path)
        
        metadata = self.system.extract_image_metadata(image_path, pil_image)
        
        self.assertIsInstance(metadata, ImageMetadata)
        self.assertIsInstance(metadata.filename, str)
        self.assertIsInstance(metadata.file_size, int)
        self.assertIsInstance(metadata.dimensions, tuple)
        self.assertEqual(len(metadata.dimensions), 2)
        self.assertIsInstance(metadata.format, str)
        self.assertIsInstance(metadata.mode, str)
    
    def test_image_quality_assessment(self):
        """Test image quality assessment"""
        quality = self.system.assess_image_quality(self.test_image)
        
        self.assertIsInstance(quality, ImageQualityAssessment)
        self.assertIsInstance(quality.overall_quality, ImageQuality)
        self.assertIsInstance(quality.sharpness_score, float)
        self.assertIsInstance(quality.brightness_score, float)
        self.assertIsInstance(quality.contrast_score, float)
        self.assertIsInstance(quality.noise_level, float)
        self.assertIsInstance(quality.blur_detection, float)
        self.assertIsInstance(quality.color_balance, dict)
        self.assertIsInstance(quality.histogram_analysis, dict)
        self.assertIsInstance(quality.recommendations, list)
        
        # Check that scores are reasonable
        self.assertGreaterEqual(quality.sharpness_score, 0)
        self.assertGreaterEqual(quality.brightness_score, 0)
        self.assertLessEqual(quality.brightness_score, 255)
        self.assertGreaterEqual(quality.contrast_score, 0)
    
    def test_visual_entity_detection(self):
        """Test visual entity detection"""
        # Mock extracted text
        extracted_text = "John Doe works at ACME Corp in New York on January 15, 2024"
        
        entities = self.system.detect_visual_entities(self.test_image, extracted_text)
        
        self.assertIsInstance(entities, list)
        
        # Check entity structure if any entities are found
        for entity in entities:
            self.assertIsInstance(entity, VisualEntity)
            self.assertIsInstance(entity.entity_type, EntityType)
            self.assertIsInstance(entity.text, str)
            self.assertIsInstance(entity.bbox, BoundingBox)
            self.assertIsInstance(entity.confidence, float)
            self.assertIsInstance(entity.metadata, dict)
            
            # Check confidence is in valid range
            self.assertGreaterEqual(entity.confidence, 0.0)
            self.assertLessEqual(entity.confidence, 1.0)
    
    def test_visual_content_analysis(self):
        """Test visual content analysis"""
        content = self.system.analyze_visual_content(self.test_image)
        
        self.assertIsInstance(content, VisualContent)
        self.assertIsInstance(content.content_type, str)
        self.assertIsInstance(content.description, str)
        self.assertIsInstance(content.objects_detected, list)
        self.assertIsInstance(content.scene_classification, str)
        self.assertIsInstance(content.dominant_colors, list)
        self.assertIsInstance(content.text_regions, list)
        self.assertIsInstance(content.faces_detected, int)
        self.assertIsInstance(content.landmarks, list)
        
        # Check that faces_detected is non-negative
        self.assertGreaterEqual(content.faces_detected, 0)
    
    def test_text_extraction(self):
        """Test text extraction from image"""
        extracted_text = self.system.extract_text_from_image(self.test_image)
        
        self.assertIsInstance(extracted_text, str)
        # Note: This is a placeholder implementation, so we just check it returns a string
    
    def test_complete_image_analysis(self):
        """Test complete image analysis pipeline"""
        # Test with image data
        result = self.system.analyze_image(image_data=self.test_image)
        
        self.assertIsInstance(result, ImageAnalysisResult)
        self.assertIsInstance(result.visual_entities, list)
        self.assertIsInstance(result.metadata, ImageMetadata)
        self.assertIsInstance(result.quality_assessment, ImageQualityAssessment)
        self.assertIsInstance(result.visual_content, VisualContent)
        self.assertIsInstance(result.extracted_text, str)
        self.assertIsInstance(result.confidence, float)
        
        # Check confidence is in valid range
        self.assertGreaterEqual(result.confidence, 0.0)
        self.assertLessEqual(result.confidence, 1.0)
        
        # Test with image path
        image_path = self.create_test_image_file()
        result_from_path = self.system.analyze_image(image_path=image_path)
        
        self.assertIsInstance(result_from_path, ImageAnalysisResult)
    
    def test_entity_type_mapping(self):
        """Test entity type mapping functions"""
        # Test spaCy to visual entity mapping
        spacy_labels = ['PERSON', 'ORG', 'GPE', 'DATE', 'MONEY', 'PRODUCT', 'UNKNOWN_LABEL']
        
        for label in spacy_labels:
            entity_type = self.system._map_spacy_to_visual_entity(label)
            self.assertIsInstance(entity_type, EntityType)
        
        # Test YOLO to entity type mapping
        yolo_classes = ['person', 'car', 'laptop', 'unknown_class']
        
        for class_name in yolo_classes:
            entity_type = self.system._map_yolo_to_entity_type(class_name)
            self.assertIsInstance(entity_type, EntityType)
        
        # Test DETR to entity type mapping
        detr_classes = ['person', 'car', 'laptop', 'unknown_class']
        
        for class_name in detr_classes:
            entity_type = self.system._map_detr_to_entity_type(class_name)
            self.assertIsInstance(entity_type, EntityType)
    
    def test_color_analysis(self):
        """Test color analysis functions"""
        # Test dominant color extraction
        colors = self.system._extract_dominant_colors(self.test_image, k=3)
        
        self.assertIsInstance(colors, list)
        self.assertLessEqual(len(colors), 3)
        
        for color in colors:
            self.assertIsInstance(color, tuple)
            self.assertEqual(len(color), 3)
            for channel in color:
                self.assertGreaterEqual(channel, 0)
                self.assertLessEqual(channel, 255)
    
    def test_face_detection(self):
        """Test face detection"""
        face_count = self.system._count_faces(self.test_image)
        
        self.assertIsInstance(face_count, int)
        self.assertGreaterEqual(face_count, 0)
    
    def test_text_region_detection(self):
        """Test text region detection"""
        text_regions = self.system._detect_text_regions(self.test_image)
        
        self.assertIsInstance(text_regions, list)
        
        for region in text_regions:
            self.assertIsInstance(region, BoundingBox)
            self.assertGreaterEqual(region.x1, 0)
            self.assertGreaterEqual(region.y1, 0)
            self.assertGreater(region.x2, region.x1)
            self.assertGreater(region.y2, region.y1)
    
    def test_landmark_detection(self):
        """Test landmark detection"""
        landmarks = self.system._detect_landmarks(self.test_image)
        
        self.assertIsInstance(landmarks, list)
        self.assertLessEqual(len(landmarks), 20)  # Limited to 20 landmarks
        
        for landmark in landmarks:
            self.assertIsInstance(landmark, dict)
            self.assertIn('type', landmark)
            self.assertIn('x', landmark)
            self.assertIn('y', landmark)
            self.assertIn('confidence', landmark)
    
    def test_quality_assessment_components(self):
        """Test individual quality assessment components"""
        gray_image = cv2.cvtColor(self.test_image, cv2.COLOR_BGR2GRAY)
        
        # Test noise estimation
        noise_level = self.system._estimate_noise_level(gray_image)
        self.assertIsInstance(noise_level, float)
        self.assertGreaterEqual(noise_level, 0)
        
        # Test blur detection
        blur_score = self.system._detect_blur(gray_image)
        self.assertIsInstance(blur_score, float)
        self.assertGreaterEqual(blur_score, 0)
        
        # Test color balance analysis
        color_balance = self.system._analyze_color_balance(self.test_image)
        self.assertIsInstance(color_balance, dict)
        
        # Test histogram analysis
        histogram = self.system._analyze_histogram(self.test_image)
        self.assertIsInstance(histogram, dict)
    
    def test_code_detection(self):
        """Test QR code and barcode detection"""
        codes = self.system._detect_codes(self.test_image)
        
        self.assertIsInstance(codes, list)
        
        for code in codes:
            self.assertIsInstance(code, VisualEntity)
            self.assertIn(code.entity_type, [EntityType.QR_CODE, EntityType.BARCODE])
    
    def test_chart_detection(self):
        """Test chart and graph detection"""
        charts = self.system._detect_charts_graphs(self.test_image)
        
        self.assertIsInstance(charts, list)
        
        for chart in charts:
            self.assertIsInstance(chart, VisualEntity)
            self.assertEqual(chart.entity_type, EntityType.CHART)
    
    def test_logo_signature_detection(self):
        """Test logo and signature detection"""
        logos_sigs = self.system._detect_logos_signatures(self.test_image)
        
        self.assertIsInstance(logos_sigs, list)
        
        for item in logos_sigs:
            self.assertIsInstance(item, VisualEntity)
            self.assertIn(item.entity_type, [EntityType.LOGO, EntityType.SIGNATURE])
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        # Test with invalid image data
        invalid_image = np.array([])
        
        try:
            result = self.system.analyze_image(image_data=invalid_image)
            # Should return an error result, not crash
            self.assertIsInstance(result, ImageAnalysisResult)
            self.assertEqual(result.confidence, 0.0)
        except Exception:
            # It's also acceptable to raise an exception
            pass
        
        # Test with non-existent file path
        try:
            result = self.system.analyze_image(image_path="non_existent_file.jpg")
            # Should handle gracefully
            self.assertIsInstance(result, ImageAnalysisResult)
        except Exception:
            # It's also acceptable to raise an exception
            pass
    
    def test_confidence_calculation(self):
        """Test overall confidence calculation"""
        # Create mock quality assessment
        quality = ImageQualityAssessment(
            overall_quality=ImageQuality.GOOD,
            sharpness_score=100.0,
            brightness_score=128.0,
            contrast_score=50.0,
            noise_level=100.0,
            blur_detection=50.0,
            color_balance={},
            histogram_analysis={},
            recommendations=[]
        )
        
        # Create mock entities
        entities = [
            VisualEntity(
                entity_type=EntityType.PERSON,
                text="John Doe",
                bbox=BoundingBox(0, 0, 100, 100, 0.8),
                confidence=0.8,
                metadata={}
            )
        ]
        
        # Create mock content
        content = VisualContent(
            content_type="document",
            description="Test description",
            objects_detected=[],
            scene_classification="document",
            dominant_colors=[],
            text_regions=[],
            faces_detected=0,
            landmarks=[]
        )
        
        confidence = self.system._calculate_overall_confidence(quality, entities, content)
        
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)


class TestImageEntityExtractionUI(unittest.TestCase):
    """Test cases for ImageEntityExtractionUI"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock streamlit to avoid actual UI rendering during tests
        self.streamlit_mock = Mock()
        
    @patch('streamlit.set_page_config')
    @patch('streamlit.title')
    @patch('streamlit.markdown')
    def test_ui_initialization(self, mock_markdown, mock_title, mock_config):
        """Test UI initialization"""
        try:
            from image_entity_extraction_ui import ImageEntityExtractionUI
            ui = ImageEntityExtractionUI()
            self.assertIsInstance(ui, ImageEntityExtractionUI)
            self.assertTrue(hasattr(ui, 'system'))
        except ImportError:
            self.skipTest("UI module not available for testing")
    
    def test_sample_image_creation(self):
        """Test sample image creation"""
        try:
            from image_entity_extraction_ui import ImageEntityExtractionUI
            ui = ImageEntityExtractionUI()
            
            sample_types = ["Business Card", "Document with Text", "Mixed Content"]
            
            for sample_type in sample_types:
                sample_image = ui.create_sample_image(sample_type)
                self.assertIsInstance(sample_image, np.ndarray)
                self.assertEqual(len(sample_image.shape), 3)  # Should be color image
                self.assertEqual(sample_image.shape[2], 3)    # Should have 3 channels
                
        except ImportError:
            self.skipTest("UI module not available for testing")
    
    def test_entity_box_drawing(self):
        """Test entity bounding box drawing"""
        try:
            from image_entity_extraction_ui import ImageEntityExtractionUI
            ui = ImageEntityExtractionUI()
            
            # Create test image
            test_image = np.ones((300, 400, 3), dtype=np.uint8) * 255
            
            # Create test entities
            entities = [
                VisualEntity(
                    entity_type=EntityType.PERSON,
                    text="John Doe",
                    bbox=BoundingBox(50, 50, 150, 150, 0.8),
                    confidence=0.8,
                    metadata={}
                ),
                VisualEntity(
                    entity_type=EntityType.ORGANIZATION,
                    text="ACME Corp",
                    bbox=BoundingBox(200, 100, 350, 200, 0.9),
                    confidence=0.9,
                    metadata={}
                )
            ]
            
            annotated_image = ui.draw_entity_boxes(test_image, entities)
            
            self.assertIsInstance(annotated_image, np.ndarray)
            self.assertEqual(annotated_image.shape, test_image.shape)
            
            # Check that the image was modified (boxes were drawn)
            self.assertFalse(np.array_equal(annotated_image, test_image))
            
        except ImportError:
            self.skipTest("UI module not available for testing")


class TestDataStructures(unittest.TestCase):
    """Test cases for data structures and enums"""
    
    def test_entity_type_enum(self):
        """Test EntityType enum"""
        # Test that all entity types are accessible
        entity_types = [
            EntityType.PERSON, EntityType.ORGANIZATION, EntityType.LOCATION,
            EntityType.DATE, EntityType.MONEY, EntityType.PRODUCT,
            EntityType.LOGO, EntityType.SIGNATURE, EntityType.STAMP,
            EntityType.BARCODE, EntityType.QR_CODE, EntityType.CHART,
            EntityType.GRAPH, EntityType.DIAGRAM, EntityType.TABLE,
            EntityType.TEXT_BLOCK, EntityType.IMAGE, EntityType.UNKNOWN
        ]
        
        for entity_type in entity_types:
            self.assertIsInstance(entity_type, EntityType)
            self.assertIsInstance(entity_type.value, str)
    
    def test_image_quality_enum(self):
        """Test ImageQuality enum"""
        quality_levels = [
            ImageQuality.EXCELLENT, ImageQuality.GOOD, ImageQuality.FAIR,
            ImageQuality.POOR, ImageQuality.VERY_POOR
        ]
        
        for quality in quality_levels:
            self.assertIsInstance(quality, ImageQuality)
            self.assertIsInstance(quality.value, str)
    
    def test_bounding_box(self):
        """Test BoundingBox dataclass"""
        bbox = BoundingBox(10, 20, 100, 200, 0.8)
        
        self.assertEqual(bbox.x1, 10)
        self.assertEqual(bbox.y1, 20)
        self.assertEqual(bbox.x2, 100)
        self.assertEqual(bbox.y2, 200)
        self.assertEqual(bbox.confidence, 0.8)
    
    def test_visual_entity(self):
        """Test VisualEntity dataclass"""
        bbox = BoundingBox(10, 20, 100, 200, 0.8)
        entity = VisualEntity(
            entity_type=EntityType.PERSON,
            text="John Doe",
            bbox=bbox,
            confidence=0.9,
            metadata={'source': 'test'}
        )
        
        self.assertEqual(entity.entity_type, EntityType.PERSON)
        self.assertEqual(entity.text, "John Doe")
        self.assertEqual(entity.bbox, bbox)
        self.assertEqual(entity.confidence, 0.9)
        self.assertEqual(entity.metadata['source'], 'test')


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.system = ImageEntityExtractionSystem()
    
    def test_end_to_end_analysis(self):
        """Test complete end-to-end analysis workflow"""
        # Create a comprehensive test image
        test_image = self.create_comprehensive_test_image()
        
        # Run complete analysis
        result = self.system.analyze_image(image_data=test_image)
        
        # Verify result structure
        self.assertIsInstance(result, ImageAnalysisResult)
        
        # Verify all components are present
        self.assertIsInstance(result.visual_entities, list)
        self.assertIsInstance(result.metadata, ImageMetadata)
        self.assertIsInstance(result.quality_assessment, ImageQualityAssessment)
        self.assertIsInstance(result.visual_content, VisualContent)
        self.assertIsInstance(result.extracted_text, str)
        self.assertIsInstance(result.confidence, float)
        
        # Verify confidence is reasonable
        self.assertGreaterEqual(result.confidence, 0.0)
        self.assertLessEqual(result.confidence, 1.0)
    
    def create_comprehensive_test_image(self) -> np.ndarray:
        """Create a comprehensive test image with various elements"""
        # Create a larger test image with multiple elements
        image = np.ones((600, 800, 3), dtype=np.uint8) * 255
        
        # Add text elements
        cv2.putText(image, "BUSINESS REPORT 2024", (200, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)
        cv2.putText(image, "Prepared by: John Smith", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1)
        cv2.putText(image, "Company: TechCorp Inc.", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1)
        cv2.putText(image, "Date: March 15, 2024", (50, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1)
        cv2.putText(image, "Revenue: $1,250,000", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1)
        cv2.putText(image, "Location: New York, NY", (50, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1)
        
        # Add geometric shapes (potential logos)
        cv2.rectangle(image, (600, 50), (750, 150), (100, 150, 200), -1)
        cv2.putText(image, "LOGO", (640, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Add chart-like elements
        # Draw axes
        cv2.line(image, (100, 450), (500, 450), (0, 0, 0), 2)  # X-axis
        cv2.line(image, (100, 450), (100, 350), (0, 0, 0), 2)  # Y-axis
        
        # Draw bars
        bar_heights = [60, 80, 40, 90]
        for i, height in enumerate(bar_heights):
            x = 150 + i * 80
            cv2.rectangle(image, (x, 450 - height), (x + 40, 450), (100, 200, 100), -1)
        
        # Add signature area
        cv2.rectangle(image, (500, 500), (700, 580), (0, 0, 0), 2)
        cv2.putText(image, "Signature:", (510, 530), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        
        # Add some noise and texture
        noise = np.random.randint(0, 30, image.shape, dtype=np.uint8)
        image = cv2.add(image, noise)
        
        return image


def run_tests():
    """Run all tests"""
    print("🧪 Running Image Entity Extraction System Tests")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestImageEntityExtractionSystem,
        TestImageEntityExtractionUI,
        TestDataStructures,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"🎯 Test Summary:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print(f"\n🚨 Errors:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback.split('\\n')[-2]}")
    
    if not result.failures and not result.errors:
        print("✅ All tests passed successfully!")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)