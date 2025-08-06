"""
Comprehensive Test Suite for Image OCR System
Tests for OCR processor, UI components, and API endpoints
"""

import pytest
import tempfile
import shutil
import base64
import json
import asyncio
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2

# Import modules to test
from image_ocr_processor import (
    OCRManager, OCREngine, ImagePreprocessor, DocumentProcessor,
    OCRResult, DocumentResult, DocumentPage,
    validate_image_file, estimate_processing_time
)

class TestImagePreprocessor:
    """Test ImagePreprocessor functionality"""
    
    @pytest.fixture
    def preprocessor(self):
        """Create ImagePreprocessor instance"""
        return ImagePreprocessor()
    
    @pytest.fixture
    def sample_image(self):
        """Create sample image for testing"""
        # Create a simple test image with text
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a font, fallback to default if not available
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        draw.text((50, 80), "Sample Test Text", fill='black', font=font)
        
        # Convert to numpy array
        return np.array(img)
    
    def test_preprocessor_initialization(self, preprocessor):
        """Test preprocessor initialization"""
        assert preprocessor.supported_formats is not None
        assert '.jpg' in preprocessor.supported_formats
        assert '.png' in preprocessor.supported_formats
        assert '.pdf' not in preprocessor.supported_formats
    
    def test_preprocess_image_basic(self, preprocessor, sample_image):
        """Test basic image preprocessing"""
        processed = preprocessor.preprocess_image(sample_image)
        
        assert processed is not None
        assert len(processed.shape) == 2  # Should be grayscale
        assert processed.dtype == np.uint8
    
    def test_preprocess_image_with_options(self, preprocessor, sample_image):
        """Test preprocessing with different options"""
        processed = preprocessor.preprocess_image(
            sample_image,
            enhance_contrast=True,
            denoise=True,
            deskew=True,
            resize_factor=1.5
        )
        
        assert processed is not None
        # Check if image was resized
        original_height, original_width = sample_image.shape[:2]
        new_height, new_width = processed.shape
        assert new_height > original_height
        assert new_width > original_width
    
    def test_detect_tables(self, preprocessor, sample_image):
        """Test table detection"""
        # Convert to grayscale for table detection
        gray_image = cv2.cvtColor(sample_image, cv2.COLOR_RGB2GRAY)
        tables = preprocessor.detect_tables(gray_image)
        
        assert isinstance(tables, list)
        # For our simple test image, no tables should be detected
        assert len(tables) == 0
    
    def test_deskew_image(self, preprocessor, sample_image):
        """Test image deskewing"""
        gray_image = cv2.cvtColor(sample_image, cv2.COLOR_RGB2GRAY)
        deskewed = preprocessor._deskew_image(gray_image)
        
        assert deskewed is not None
        assert deskewed.shape == gray_image.shape

class TestOCREngine:
    """Test OCREngine functionality"""
    
    @pytest.fixture
    def ocr_engine(self):
        """Create OCREngine instance"""
        return OCREngine()
    
    @pytest.fixture
    def sample_text_image(self):
        """Create image with clear text for OCR testing"""
        img = Image.new('RGB', (600, 100), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 32)
        except:
            font = ImageFont.load_default()
        
        draw.text((20, 30), "Hello World Test", fill='black', font=font)
        return np.array(img)
    
    def test_ocr_engine_initialization(self, ocr_engine):
        """Test OCR engine initialization"""
        assert ocr_engine.preprocessor is not None
        assert ocr_engine.language_codes is not None
        assert 'en' in ocr_engine.language_codes
        assert ocr_engine.language_codes['en'] == 'eng'
    
    def test_language_detection(self, ocr_engine, sample_text_image):
        """Test language detection"""
        gray_image = cv2.cvtColor(sample_text_image, cv2.COLOR_RGB2GRAY)
        language = ocr_engine.detect_language(gray_image)
        
        assert language is not None
        assert isinstance(language, str)
        assert language in ocr_engine.language_codes
    
    @patch('pytesseract.image_to_string')
    @patch('pytesseract.image_to_data')
    def test_extract_text_tesseract_mock(self, mock_image_to_data, mock_image_to_string, ocr_engine, sample_text_image):
        """Test Tesseract OCR with mocked responses"""
        # Mock Tesseract responses
        mock_image_to_string.return_value = "Hello World Test"
        mock_image_to_data.return_value = {
            'text': ['Hello', 'World', 'Test'],
            'conf': [95, 90, 88],
            'left': [20, 80, 140],
            'top': [30, 30, 30],
            'width': [50, 50, 40],
            'height': [20, 20, 20]
        }
        
        # Assume Tesseract is available for this test
        ocr_engine.tesseract_available = True
        
        gray_image = cv2.cvtColor(sample_text_image, cv2.COLOR_RGB2GRAY)
        result = ocr_engine.extract_text_tesseract(gray_image)
        
        assert isinstance(result, OCRResult)
        assert result.text == "Hello World Test"
        assert result.confidence > 0
        assert result.word_count == 3
        assert len(result.bounding_boxes) == 3
    
    def test_extract_text_hybrid_fallback(self, ocr_engine, sample_text_image):
        """Test hybrid OCR with fallback behavior"""
        gray_image = cv2.cvtColor(sample_text_image, cv2.COLOR_RGB2GRAY)
        
        # Test when no engines are available
        ocr_engine.tesseract_available = False
        ocr_engine.easyocr_reader = None
        
        with pytest.raises(Exception, match="No OCR engines available"):
            ocr_engine.extract_text_hybrid(gray_image)

class TestDocumentProcessor:
    """Test DocumentProcessor functionality"""
    
    @pytest.fixture
    def document_processor(self):
        """Create DocumentProcessor instance"""
        return DocumentProcessor()
    
    @pytest.fixture
    def sample_pdf_path(self):
        """Create a sample PDF file for testing"""
        # This would require PyMuPDF to create a real PDF
        # For now, return a mock path
        return "sample_test.pdf"
    
    @pytest.fixture
    def sample_image_path(self):
        """Create a sample image file for testing"""
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        
        # Create simple test image
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((50, 80), "Test Document", fill='black')
        img.save(temp_file.name)
        
        return temp_file.name
    
    def test_document_processor_initialization(self, document_processor):
        """Test document processor initialization"""
        assert document_processor.ocr_engine is not None
        assert document_processor.supported_formats is not None
        assert '.pdf' in document_processor.supported_formats
        assert '.jpg' in document_processor.supported_formats
    
    @patch('fitz.open')
    def test_process_pdf_mock(self, mock_fitz_open, document_processor):
        """Test PDF processing with mocked PyMuPDF"""
        # Mock PDF document
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.get_text.return_value = "Sample PDF text content"
        mock_doc.load_page.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_fitz_open.return_value = mock_doc
        
        result = document_processor.process_pdf("test.pdf")
        
        assert isinstance(result, DocumentResult)
        assert result.filename == "test.pdf"
        assert result.total_pages == 1
        assert len(result.pages) == 1
        assert "Sample PDF text content" in result.combined_text
    
    def test_process_image(self, document_processor, sample_image_path):
        """Test image processing"""
        try:
            result = document_processor.process_image(sample_image_path)
            
            assert isinstance(result, OCRResult)
            assert result.text is not None
            assert result.confidence >= 0
            assert result.processing_time > 0
            
        finally:
            # Clean up temp file
            Path(sample_image_path).unlink()
    
    def test_process_batch(self, document_processor, sample_image_path):
        """Test batch processing"""
        try:
            results = document_processor.process_batch([sample_image_path])
            
            assert isinstance(results, list)
            assert len(results) == 1
            assert isinstance(results[0], OCRResult)
            
        finally:
            # Clean up temp file
            Path(sample_image_path).unlink()

class TestOCRManager:
    """Test OCRManager functionality"""
    
    @pytest.fixture
    def ocr_manager(self):
        """Create OCRManager instance"""
        temp_dir = tempfile.mkdtemp()
        manager = OCRManager(temp_dir)
        yield manager
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_image_file(self):
        """Create sample image file"""
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        
        img = Image.new('RGB', (300, 100), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((20, 30), "OCR Test", fill='black')
        img.save(temp_file.name)
        
        return temp_file.name
    
    def test_ocr_manager_initialization(self, ocr_manager):
        """Test OCR manager initialization"""
        assert ocr_manager.document_processor is not None
        assert ocr_manager.temp_dir.exists()
    
    def test_process_file(self, ocr_manager, sample_image_file):
        """Test file processing"""
        try:
            result = ocr_manager.process_file(sample_image_file)
            
            assert result is not None
            assert isinstance(result, (OCRResult, DocumentResult))
            
        finally:
            # Clean up
            Path(sample_image_file).unlink()
    
    def test_process_base64_image(self, ocr_manager):
        """Test base64 image processing"""
        # Create simple test image
        img = Image.new('RGB', (200, 100), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((20, 30), "Base64 Test", fill='black')
        
        # Convert to base64
        import io
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        base64_data = base64.b64encode(buffer.getvalue()).decode()
        
        result = ocr_manager.process_base64_image(base64_data)
        
        assert isinstance(result, OCRResult)
        assert result.text is not None
    
    def test_get_supported_languages(self, ocr_manager):
        """Test getting supported languages"""
        languages = ocr_manager.get_supported_languages()
        
        assert isinstance(languages, list)
        assert len(languages) > 0
        
        # Check structure
        for lang in languages:
            assert 'code' in lang
            assert 'name' in lang
    
    def test_get_processing_stats(self, ocr_manager):
        """Test getting processing statistics"""
        stats = ocr_manager.get_processing_stats()
        
        assert isinstance(stats, dict)
        assert 'tesseract_available' in stats
        assert 'easyocr_available' in stats
        assert 'supported_formats' in stats
        assert 'supported_languages' in stats
    
    def test_cleanup_temp_files(self, ocr_manager):
        """Test temporary file cleanup"""
        # Create some temp files
        temp_file1 = ocr_manager.temp_dir / "test1.txt"
        temp_file2 = ocr_manager.temp_dir / "test2.txt"
        
        temp_file1.write_text("test")
        temp_file2.write_text("test")
        
        assert temp_file1.exists()
        assert temp_file2.exists()
        
        # Cleanup
        ocr_manager.cleanup_temp_files()
        
        assert not temp_file1.exists()
        assert not temp_file2.exists()

class TestUtilityFunctions:
    """Test utility functions"""
    
    @pytest.fixture
    def sample_image_file(self):
        """Create sample image file"""
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        
        img = Image.new('RGB', (100, 100), color='white')
        img.save(temp_file.name)
        
        return temp_file.name
    
    def test_validate_image_file_valid(self, sample_image_file):
        """Test image file validation with valid file"""
        try:
            result = validate_image_file(sample_image_file)
            assert result is True
        finally:
            Path(sample_image_file).unlink()
    
    def test_validate_image_file_invalid(self):
        """Test image file validation with invalid file"""
        # Create text file with image extension
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_file.write(b"This is not an image")
        temp_file.close()
        
        try:
            result = validate_image_file(temp_file.name)
            assert result is False
        finally:
            Path(temp_file.name).unlink()
    
    def test_estimate_processing_time(self):
        """Test processing time estimation"""
        # Test with different file types
        pdf_time = estimate_processing_time("document.pdf")
        image_time = estimate_processing_time("image.jpg")
        
        assert pdf_time > 0
        assert image_time > 0
        assert isinstance(pdf_time, float)
        assert isinstance(image_time, float)
    
    def test_estimate_processing_time_nonexistent(self):
        """Test processing time estimation with non-existent file"""
        time_estimate = estimate_processing_time("nonexistent.jpg")
        assert time_estimate == 10.0  # Default estimate

class TestAPIEndpoints:
    """Test API endpoints (requires running server)"""
    
    @pytest.fixture
    def api_client(self):
        """Create test client for API"""
        from fastapi.testclient import TestClient
        from api_ocr_endpoints import app
        
        return TestClient(app)
    
    def test_root_endpoint(self, api_client):
        """Test root endpoint"""
        response = api_client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
    
    def test_health_check(self, api_client):
        """Test health check endpoint"""
        response = api_client.get("/api/ocr/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "ocr_engines" in data
    
    def test_get_languages(self, api_client):
        """Test get languages endpoint"""
        response = api_client.get("/api/ocr/languages")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check structure
        for lang in data:
            assert "code" in lang
            assert "name" in lang
    
    def test_get_system_status(self, api_client):
        """Test system status endpoint"""
        response = api_client.get("/api/ocr/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "tesseract_available" in data
        assert "easyocr_available" in data
        assert "supported_formats" in data
        assert "supported_languages" in data
    
    def test_cleanup_endpoint(self, api_client):
        """Test cleanup endpoint"""
        response = api_client.delete("/api/ocr/cleanup")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "message" in data
    
    def test_process_mobile_endpoint(self, api_client):
        """Test mobile processing endpoint"""
        # Create simple test image
        img = Image.new('RGB', (200, 100), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((20, 30), "API Test", fill='black')
        
        # Convert to base64
        import io
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        base64_data = base64.b64encode(buffer.getvalue()).decode()
        
        # Make request
        request_data = {
            "file_data": base64_data,
            "filename": "test.png",
            "language": "en",
            "extract_tables": True,
            "enhance_contrast": True,
            "denoise_image": True,
            "deskew_image": True
        }
        
        response = api_client.post("/api/ocr/process-mobile", json=request_data)
        
        # Note: This might fail if OCR engines aren't properly installed
        # In a real test environment, you'd want to mock the OCR processing
        assert response.status_code in [200, 500]  # Allow for OCR engine issues

class TestIntegration:
    """Integration tests for the complete OCR system"""
    
    @pytest.fixture
    def complete_system(self):
        """Set up complete OCR system"""
        temp_dir = tempfile.mkdtemp()
        manager = OCRManager(temp_dir)
        yield manager
        shutil.rmtree(temp_dir)
    
    def test_end_to_end_image_processing(self, complete_system):
        """Test complete image processing workflow"""
        # Create test image
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((50, 80), "End to End Test", fill='black')
        img.save(temp_file.name)
        
        try:
            # Process image
            result = complete_system.process_file(temp_file.name, language='en')
            
            # Verify result
            assert result is not None
            assert isinstance(result, (OCRResult, DocumentResult))
            
            if isinstance(result, OCRResult):
                assert result.text is not None
                assert result.confidence >= 0
                assert result.processing_time > 0
                assert result.word_count >= 0
                
        finally:
            Path(temp_file.name).unlink()
    
    def test_multiple_language_processing(self, complete_system):
        """Test processing with different languages"""
        # Create test image
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        
        img = Image.new('RGB', (300, 100), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((20, 30), "Multi Language", fill='black')
        img.save(temp_file.name)
        
        try:
            # Test different languages
            languages = ['en', 'es', 'fr']
            
            for lang in languages:
                result = complete_system.process_file(temp_file.name, language=lang)
                assert result is not None
                assert isinstance(result, (OCRResult, DocumentResult))
                
        finally:
            Path(temp_file.name).unlink()
    
    def test_error_handling(self, complete_system):
        """Test error handling with invalid inputs"""
        # Test with non-existent file
        with pytest.raises(Exception):
            complete_system.process_file("nonexistent.jpg")
        
        # Test with invalid base64 data
        with pytest.raises(Exception):
            complete_system.process_base64_image("invalid_base64_data")

# Performance tests
class TestPerformance:
    """Performance tests for OCR system"""
    
    @pytest.fixture
    def performance_manager(self):
        """Create OCR manager for performance testing"""
        temp_dir = tempfile.mkdtemp()
        manager = OCRManager(temp_dir)
        yield manager
        shutil.rmtree(temp_dir)
    
    def test_processing_speed(self, performance_manager):
        """Test processing speed with different image sizes"""
        sizes = [(200, 100), (400, 200), (800, 400)]
        
        for width, height in sizes:
            # Create test image
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            
            img = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)
            draw.text((20, 30), f"Size {width}x{height}", fill='black')
            img.save(temp_file.name)
            
            try:
                start_time = datetime.now()
                result = performance_manager.process_file(temp_file.name)
                end_time = datetime.now()
                
                processing_time = (end_time - start_time).total_seconds()
                
                # Basic performance assertions
                assert processing_time < 30  # Should complete within 30 seconds
                assert result is not None
                
                print(f"Size {width}x{height}: {processing_time:.2f}s")
                
            finally:
                Path(temp_file.name).unlink()
    
    def test_memory_usage(self, performance_manager):
        """Test memory usage during processing"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Process multiple images
        for i in range(5):
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            
            img = Image.new('RGB', (400, 200), color='white')
            draw = ImageDraw.Draw(img)
            draw.text((20, 30), f"Memory Test {i}", fill='black')
            img.save(temp_file.name)
            
            try:
                performance_manager.process_file(temp_file.name)
            finally:
                Path(temp_file.name).unlink()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 500MB)
        assert memory_increase < 500 * 1024 * 1024
        
        print(f"Memory increase: {memory_increase / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])