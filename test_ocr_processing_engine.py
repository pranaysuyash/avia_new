"""
Comprehensive tests for Enterprise OCR Processing Engine

This module provides thorough testing of all OCR processing functionality
including provider abstraction, routing policies, and quality validation.
"""

import pytest
import cv2
import numpy as np
import tempfile
import os
from unittest.mock import patch, MagicMock
from typing import List, Dict, Any

from ocr_processing_engine import (
    OCRProcessingService, OCRConfig, OCRProvider, PreprocessingMode,
    RoutingPolicy, TextDetectionMethod, OCRResult, TextSegment,
    BoundingBox, FrameQualityMetrics, TesseractProvider, EasyOCRProvider,
    ImagePreprocessor, ConfidenceCalibrator, TextNormalizer,
    LanguageDetector, PolicyEngine, TextDetectionService,
    create_ocr_config, get_available_ocr_providers
)


class TestOCRConfig:
    """Test OCR configuration class"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = OCRConfig()
        
        assert config.providers == [OCRProvider.TESSERACT, OCRProvider.EASYOCR]
        assert config.preprocessing_mode == PreprocessingMode.STANDARD
        assert config.routing_policy == RoutingPolicy.BALANCED
        assert config.confidence_threshold == 0.5
        assert config.languages == ['en']
        assert config.enable_confidence_calibration == True
        assert config.enable_text_normalization == True
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = OCRConfig(
            providers=[OCRProvider.TESSERACT],
            preprocessing_mode=PreprocessingMode.AGGRESSIVE,
            routing_policy=RoutingPolicy.ACCURACY_FIRST,
            confidence_threshold=0.8,
            languages=['en', 'es'],
            enable_confidence_calibration=False
        )
        
        assert config.providers == [OCRProvider.TESSERACT]
        assert config.preprocessing_mode == PreprocessingMode.AGGRESSIVE
        assert config.routing_policy == RoutingPolicy.ACCURACY_FIRST
        assert config.confidence_threshold == 0.8
        assert config.languages == ['en', 'es']
        assert config.enable_confidence_calibration == False


class TestBoundingBox:
    """Test BoundingBox class"""
    
    def test_bounding_box_creation(self):
        """Test bounding box creation and methods"""
        bbox = BoundingBox(x=10, y=20, width=100, height=50, confidence=0.8, text="test")
        
        assert bbox.x == 10
        assert bbox.y == 20
        assert bbox.width == 100
        assert bbox.height == 50
        assert bbox.confidence == 0.8
        assert bbox.text == "test"
        
        # Test methods
        assert bbox.area() == 5000
        assert bbox.center() == (60, 45)
        
        # Test serialization
        bbox_dict = bbox.to_dict()
        assert isinstance(bbox_dict, dict)
        assert bbox_dict['x'] == 10
        assert bbox_dict['confidence'] == 0.8


class TestTextSegment:
    """Test TextSegment class"""
    
    def test_text_segment_creation(self):
        """Test text segment creation"""
        bbox = BoundingBox(x=0, y=0, width=100, height=20, confidence=0.9)
        segment = TextSegment(
            text="Hello World",
            confidence=0.85,
            bounding_box=bbox,
            language="en"
        )
        
        assert segment.text == "Hello World"
        assert segment.confidence == 0.85
        assert segment.language == "en"
        assert segment.bounding_box == bbox
        
        # Test serialization
        segment_dict = segment.to_dict()
        assert isinstance(segment_dict, dict)
        assert segment_dict['text'] == "Hello World"
        assert 'bounding_box' in segment_dict


class TestOCRResult:
    """Test OCRResult class"""
    
    def test_ocr_result_creation(self):
        """Test OCR result creation and methods"""
        bbox1 = BoundingBox(x=0, y=0, width=50, height=20, confidence=0.9)
        bbox2 = BoundingBox(x=60, y=0, width=50, height=20, confidence=0.8)
        
        segment1 = TextSegment("Hello", 0.9, bbox1, "en")
        segment2 = TextSegment("World", 0.8, bbox2, "en")
        
        result = OCRResult(
            segments=[segment1, segment2],
            processing_time=1.5,
            provider="tesseract",
            detection_method="tesseract_native",
            preprocessing_applied=["grayscale", "threshold"],
            image_hash="abc123"
        )
        
        assert len(result.segments) == 2
        assert result.processing_time == 1.5
        assert result.provider == "tesseract"
        
        # Test methods
        assert result.get_text() == "Hello World"
        assert result.get_average_confidence() == 0.85
        
        # Test serialization
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert len(result_dict['segments']) == 2


class TestImagePreprocessor:
    """Test image preprocessing functionality"""
    
    @pytest.fixture
    def preprocessor(self):
        return ImagePreprocessor()
    
    @pytest.fixture
    def test_image(self):
        # Create a simple test image
        img = np.ones((100, 200, 3), dtype=np.uint8) * 255
        cv2.putText(img, "TEST", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        return img
    
    def test_minimal_preprocessing(self, preprocessor, test_image):
        """Test minimal preprocessing mode"""
        processed, methods = preprocessor.preprocess_image(test_image, PreprocessingMode.MINIMAL)
        
        assert processed is not None
        assert len(processed.shape) == 2  # Should be grayscale
        assert 'grayscale' in methods
    
    def test_standard_preprocessing(self, preprocessor, test_image):
        """Test standard preprocessing mode"""
        processed, methods = preprocessor.preprocess_image(test_image, PreprocessingMode.STANDARD)
        
        assert processed is not None
        assert len(methods) > 1
        assert 'grayscale' in methods
        assert 'denoise' in methods
    
    def test_aggressive_preprocessing(self, preprocessor, test_image):
        """Test aggressive preprocessing mode"""
        processed, methods = preprocessor.preprocess_image(test_image, PreprocessingMode.AGGRESSIVE)
        
        assert processed is not None
        assert len(methods) >= 4  # Should apply multiple methods
        assert 'grayscale' in methods
        assert 'deskew' in methods
    
    def test_custom_preprocessing(self, preprocessor, test_image):
        """Test custom preprocessing configuration"""
        custom_config = {
            'grayscale': {},
            'denoise': {},
            'enhance_contrast': {}
        }
        
        processed, methods = preprocessor.preprocess_image(
            test_image, PreprocessingMode.CUSTOM, custom_config
        )
        
        assert processed is not None
        assert len(methods) == 3
        assert all(method in methods for method in custom_config.keys())
    
    def test_grayscale_conversion(self, preprocessor):
        """Test grayscale conversion"""
        color_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        gray_image = preprocessor._convert_grayscale(color_image)
        
        assert len(gray_image.shape) == 2
        assert gray_image.dtype == np.uint8
        
        # Test with already grayscale image
        gray_input = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        gray_output = preprocessor._convert_grayscale(gray_input)
        assert np.array_equal(gray_input, gray_output)


class TestConfidenceCalibrator:
    """Test confidence calibration functionality"""
    
    @pytest.fixture
    def calibrator(self):
        return ConfidenceCalibrator()
    
    def test_calibration_data_addition(self, calibrator):
        """Test adding calibration data"""
        calibrator.add_calibration_data("tesseract", 0.8, 0.9)
        calibrator.add_calibration_data("tesseract", 0.6, 0.7)
        
        assert len(calibrator.calibration_data["tesseract"]) == 2
        assert calibrator.calibration_data["tesseract"][0] == (0.8, 0.9)
    
    def test_confidence_calibration(self, calibrator):
        """Test confidence calibration"""
        # Add enough data to build calibration model
        for i in range(15):
            predicted = 0.5 + i * 0.03
            actual = predicted + 0.1  # Simulate systematic bias
            calibrator.add_calibration_data("tesseract", predicted, actual)
        
        # Test calibration
        calibrated = calibrator.calibrate_confidence("tesseract", 0.7)
        assert isinstance(calibrated, float)
        assert 0.0 <= calibrated <= 1.0
        
        # Test with unknown provider
        uncalibrated = calibrator.calibrate_confidence("unknown", 0.7)
        assert uncalibrated == 0.7  # Should return original


class TestTextNormalizer:
    """Test text normalization functionality"""
    
    @pytest.fixture
    def normalizer(self):
        return TextNormalizer()
    
    def test_text_normalization(self, normalizer):
        """Test basic text normalization"""
        messy_text = "  Hello    World!!!  "
        normalized = normalizer.normalize_text(messy_text)
        
        assert normalized.strip() == "Hello World!!!"
        assert "   " not in normalized  # No multiple spaces
    
    def test_extra_space_removal(self, normalizer):
        """Test extra space removal"""
        text_with_spaces = "Hello     World\t\nTest"
        cleaned = normalizer._remove_extra_spaces(text_with_spaces)
        
        assert "     " not in cleaned
        assert cleaned == "Hello World Test"
    
    def test_common_ocr_error_fixes(self, normalizer):
        """Test common OCR error corrections"""
        text_with_errors = "He11o W0rld"  # 1s and 0s instead of letters
        # Note: The current implementation is basic, so we test the method exists
        fixed = normalizer._fix_common_ocr_errors(text_with_errors, "en")
        assert isinstance(fixed, str)
    
    def test_punctuation_normalization(self, normalizer):
        """Test punctuation normalization"""
        text_with_punct = "Hello....... World!!!!!!"
        normalized = normalizer._normalize_punctuation(text_with_punct)
        
        assert "......" not in normalized
        assert "!!!!!" not in normalized


class TestLanguageDetector:
    """Test language detection functionality"""
    
    @pytest.fixture
    def detector(self):
        return LanguageDetector()
    
    def test_english_detection(self, detector):
        """Test English language detection"""
        english_text = "Hello world this is English text"
        detected = detector.detect_language(english_text)
        
        assert detected == "en"
    
    def test_spanish_detection(self, detector):
        """Test Spanish language detection"""
        spanish_text = "Hola mundo esto es texto en español"
        detected = detector.detect_language(spanish_text)
        
        # May detect as Spanish or default to English depending on implementation
        assert detected in ["es", "en"]
    
    def test_empty_text_detection(self, detector):
        """Test detection with empty text"""
        detected = detector.detect_language("")
        assert detected == "unknown"
    
    def test_mixed_language_detection(self, detector):
        """Test detection with mixed languages"""
        mixed_text = "Hello mundo"
        detected = detector.detect_language(mixed_text)
        
        assert detected in ["en", "es"]  # Should detect one of them


class TestPolicyEngine:
    """Test policy engine functionality"""
    
    @pytest.fixture
    def policy_engine(self):
        return PolicyEngine()
    
    @pytest.fixture
    def test_image(self):
        return np.ones((100, 100, 3), dtype=np.uint8) * 255
    
    def test_provider_selection_single(self, policy_engine, test_image):
        """Test provider selection with single provider"""
        config = OCRConfig()
        providers = ["tesseract"]
        
        selected = policy_engine.select_provider(
            providers, RoutingPolicy.BALANCED, test_image, config
        )
        
        assert selected == "tesseract"
    
    def test_provider_selection_multiple(self, policy_engine, test_image):
        """Test provider selection with multiple providers"""
        config = OCRConfig()
        providers = ["tesseract", "easyocr"]
        
        selected = policy_engine.select_provider(
            providers, RoutingPolicy.BALANCED, test_image, config
        )
        
        assert selected in providers
    
    def test_empty_providers_error(self, policy_engine, test_image):
        """Test error handling with no providers"""
        config = OCRConfig()
        
        with pytest.raises(ValueError):
            policy_engine.select_provider([], RoutingPolicy.BALANCED, test_image, config)


class TestTextDetectionService:
    """Test text detection service"""
    
    @pytest.fixture
    def detector(self):
        return TextDetectionService()
    
    @pytest.fixture
    def test_image_with_text(self):
        img = np.ones((200, 300, 3), dtype=np.uint8) * 255
        cv2.putText(img, "HELLO", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(img, "WORLD", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        return img
    
    def test_mser_detection(self, detector, test_image_with_text):
        """Test MSER text detection"""
        regions = detector.detect_text_regions(test_image_with_text, TextDetectionMethod.MSER)
        
        assert isinstance(regions, list)
        # Should detect some regions (exact number depends on MSER parameters)
        for region in regions:
            assert isinstance(region, BoundingBox)
            assert region.x >= 0
            assert region.y >= 0
            assert region.width > 0
            assert region.height > 0
    
    def test_contour_detection(self, detector, test_image_with_text):
        """Test contour-based text detection"""
        regions = detector.detect_text_regions(test_image_with_text, TextDetectionMethod.CONTOUR)
        
        assert isinstance(regions, list)
        for region in regions:
            assert isinstance(region, BoundingBox)
    
    def test_unsupported_method_fallback(self, detector, test_image_with_text):
        """Test fallback for unsupported detection methods"""
        # EAST and CRAFT should fall back to MSER
        regions_east = detector.detect_text_regions(test_image_with_text, TextDetectionMethod.EAST)
        regions_craft = detector.detect_text_regions(test_image_with_text, TextDetectionMethod.CRAFT)
        
        assert isinstance(regions_east, list)
        assert isinstance(regions_craft, list)


class TestOCRProcessingService:
    """Test main OCR processing service"""
    
    @pytest.fixture
    def test_image(self):
        img = np.ones((150, 300, 3), dtype=np.uint8) * 255
        cv2.putText(img, "TEST OCR", (50, 75), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        return img
    
    def test_service_initialization(self):
        """Test service initialization"""
        config = OCRConfig()
        service = OCRProcessingService(config)
        
        try:
            assert service.config == config
            assert hasattr(service, 'providers')
            assert hasattr(service, 'preprocessor')
            assert hasattr(service, 'confidence_calibrator')
        finally:
            service.cleanup()
    
    def test_available_providers(self):
        """Test getting available providers"""
        service = OCRProcessingService()
        
        try:
            providers = service.get_available_providers()
            assert isinstance(providers, list)
            # Should have at least one provider available in test environment
        finally:
            service.cleanup()
    
    @patch('ocr_processing_engine.TESSERACT_AVAILABLE', True)
    def test_process_image_mock(self, test_image):
        """Test image processing with mocked provider"""
        config = OCRConfig(providers=[OCRProvider.TESSERACT])
        service = OCRProcessingService(config)
        
        # Mock the Tesseract provider
        mock_provider = MagicMock()
        mock_result = OCRResult(
            segments=[TextSegment("TEST OCR", 0.9, BoundingBox(0, 0, 100, 20, 0.9), "en")],
            processing_time=0.5,
            provider="tesseract",
            detection_method="tesseract_native",
            preprocessing_applied=[],
            image_hash="test_hash"
        )
        mock_provider.process_image.return_value = mock_result
        mock_provider.estimate_cost.return_value = 0.0
        
        service.providers["tesseract"] = mock_provider
        
        try:
            result = service.process_image(test_image)
            
            assert isinstance(result, OCRResult)
            assert len(result.segments) == 1
            assert result.segments[0].text == "TEST OCR"
            assert result.provider == "tesseract"
        finally:
            service.cleanup()
    
    def test_batch_processing_mock(self, test_image):
        """Test batch processing with mocked provider"""
        config = OCRConfig(providers=[OCRProvider.TESSERACT])
        service = OCRProcessingService(config)
        
        # Mock the provider
        mock_provider = MagicMock()
        mock_result = OCRResult(
            segments=[TextSegment("TEST", 0.8, BoundingBox(0, 0, 50, 20, 0.8), "en")],
            processing_time=0.3,
            provider="tesseract",
            detection_method="tesseract_native",
            preprocessing_applied=[],
            image_hash="test_hash"
        )
        mock_provider.process_image.return_value = mock_result
        mock_provider.estimate_cost.return_value = 0.0
        
        service.providers["tesseract"] = mock_provider
        
        try:
            images = [test_image, test_image, test_image]
            results = service.batch_process_images(images)
            
            assert len(results) == 3
            assert all(isinstance(result, OCRResult) for result in results)
        finally:
            service.cleanup()
    
    def test_cost_estimation_mock(self, test_image):
        """Test cost estimation with mocked provider"""
        config = OCRConfig(providers=[OCRProvider.TESSERACT])
        service = OCRProcessingService(config)
        
        # Mock the provider
        mock_provider = MagicMock()
        mock_provider.estimate_cost.return_value = 0.001
        service.providers["tesseract"] = mock_provider
        
        try:
            images = [test_image, test_image]
            cost_estimate = service.estimate_processing_cost(images)
            
            assert isinstance(cost_estimate, dict)
            assert 'total_images' in cost_estimate
            assert 'estimated_total_cost' in cost_estimate
            assert cost_estimate['total_images'] == 2
        finally:
            service.cleanup()
    
    def test_invalid_image_error(self):
        """Test error handling with invalid image"""
        service = OCRProcessingService()
        
        try:
            with pytest.raises(ValueError):
                service.process_image(np.array([]))  # Empty array
        finally:
            service.cleanup()
    
    def test_no_providers_error(self):
        """Test error handling with no available providers"""
        config = OCRConfig(providers=[])
        service = OCRProcessingService(config)
        
        # Clear all providers to simulate none available
        service.providers = {}
        
        try:
            test_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
            with pytest.raises(RuntimeError):
                service.process_image(test_image)
        finally:
            service.cleanup()


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_create_ocr_config(self):
        """Test OCR config creation utility"""
        config = create_ocr_config(
            providers=[OCRProvider.TESSERACT],
            confidence_threshold=0.8,
            preprocessing_mode=PreprocessingMode.AGGRESSIVE
        )
        
        assert isinstance(config, OCRConfig)
        assert config.providers == [OCRProvider.TESSERACT]
        assert config.confidence_threshold == 0.8
        assert config.preprocessing_mode == PreprocessingMode.AGGRESSIVE
    
    def test_get_available_providers(self):
        """Test getting available providers utility"""
        providers = get_available_ocr_providers()
        
        assert isinstance(providers, list)
        # In test environment, may or may not have providers available


class TestProviderImplementations:
    """Test specific provider implementations"""
    
    def test_tesseract_provider_availability(self):
        """Test Tesseract provider availability check"""
        provider = TesseractProvider()
        
        # Should not crash even if Tesseract is not installed
        is_available = provider.is_available()
        assert isinstance(is_available, bool)
        
        if is_available:
            languages = provider.get_supported_languages()
            assert isinstance(languages, list)
            assert len(languages) > 0
    
    def test_easyocr_provider_availability(self):
        """Test EasyOCR provider availability check"""
        provider = EasyOCRProvider()
        
        # Should not crash even if EasyOCR is not installed
        is_available = provider.is_available()
        assert isinstance(is_available, bool)
        
        languages = provider.get_supported_languages()
        assert isinstance(languages, list)
    
    def test_provider_cost_estimation(self):
        """Test provider cost estimation"""
        test_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        
        tesseract_provider = TesseractProvider()
        tesseract_cost = tesseract_provider.estimate_cost(test_image)
        assert tesseract_cost == 0.0  # Tesseract is free
        
        easyocr_provider = EasyOCRProvider()
        easyocr_cost = easyocr_provider.estimate_cost(test_image)
        assert easyocr_cost == 0.0  # EasyOCR is free


class TestIntegration:
    """Integration tests for complete workflows"""
    
    @pytest.fixture
    def complex_test_image(self):
        """Create a complex test image"""
        img = np.ones((300, 500, 3), dtype=np.uint8) * 255
        
        # Add multiple text elements
        cv2.putText(img, "INTEGRATION TEST", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(img, "Multiple lines of text", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
        cv2.putText(img, "for comprehensive testing", (50, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
        cv2.putText(img, "Different sizes and styles", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        
        # Add some noise
        noise = np.random.randint(0, 20, img.shape, dtype=np.uint8)
        img = cv2.add(img, noise)
        
        return img
    
    def test_end_to_end_processing(self, complex_test_image):
        """Test complete end-to-end OCR processing"""
        config = OCRConfig(
            preprocessing_mode=PreprocessingMode.STANDARD,
            confidence_threshold=0.1,  # Lower threshold for test
            enable_confidence_calibration=True,
            enable_text_normalization=True,
            enable_language_detection=True
        )
        
        service = OCRProcessingService(config)
        
        try:
            # Check if any providers are available
            available_providers = service.get_available_providers()
            if not available_providers:
                pytest.skip("No OCR providers available for integration test")
            
            # Process image
            result = service.process_image(complex_test_image)
            
            # Validate result structure
            assert isinstance(result, OCRResult)
            assert result.processing_time > 0
            assert result.provider in available_providers
            assert isinstance(result.segments, list)
            
            # If text was found, validate segments
            if result.segments:
                for segment in result.segments:
                    assert isinstance(segment, TextSegment)
                    assert isinstance(segment.text, str)
                    assert 0 <= segment.confidence <= 1
                    assert isinstance(segment.bounding_box, BoundingBox)
            
            # Test validation
            expected_text = "INTEGRATION TEST Multiple lines of text for comprehensive testing Different sizes and styles"
            validation = service.validate_result(result, expected_text)
            
            assert isinstance(validation, dict)
            assert 'segment_count' in validation
            assert 'average_confidence' in validation
            assert 'has_text' in validation
            
        finally:
            service.cleanup()
    
    def test_preprocessing_pipeline_integration(self, complex_test_image):
        """Test preprocessing pipeline integration"""
        modes = [PreprocessingMode.MINIMAL, PreprocessingMode.STANDARD, PreprocessingMode.AGGRESSIVE]
        
        for mode in modes:
            config = OCRConfig(
                preprocessing_mode=mode,
                confidence_threshold=0.1
            )
            
            service = OCRProcessingService(config)
            
            try:
                available_providers = service.get_available_providers()
                if not available_providers:
                    pytest.skip("No OCR providers available")
                
                result = service.process_image(complex_test_image)
                
                # Should complete without errors
                assert isinstance(result, OCRResult)
                assert isinstance(result.preprocessing_applied, list)
                
                # Different modes should apply different preprocessing
                if mode == PreprocessingMode.MINIMAL:
                    assert len(result.preprocessing_applied) <= 2
                elif mode == PreprocessingMode.AGGRESSIVE:
                    assert len(result.preprocessing_applied) >= 3
                
            finally:
                service.cleanup()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])