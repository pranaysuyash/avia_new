"""
Test suite for Media Ingestion Controller
Tests the unified media ingestion system with format detection, validation, and preprocessing.
"""

import pytest
import asyncio
import tempfile
import os
import io
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from media_ingestion_controller import (
    MediaIngestionController, MediaFormat, QualityMetrics, ProcessingOptions,
    MediaFile, IngestionResult, StreamingUploadProgress
)
from errors import MediaProcessingError, FileProcessingError, ErrorCode


class TestMediaIngestionController:
    """Test cases for MediaIngestionController"""
    
    @pytest.fixture
    def controller(self):
        """Create a test controller instance"""
        return MediaIngestionController(max_file_size_mb=100)
    
    @pytest.fixture
    def sample_audio_file(self):
        """Create a temporary audio file for testing"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            # Write minimal WAV header
            f.write(b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00')
            yield f.name
        os.unlink(f.name)
    
    @pytest.fixture
    def sample_image_file(self):
        """Create a temporary image file for testing"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            # Write minimal PNG header
            f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00IEND\xaeB`\x82')
            yield f.name
        os.unlink(f.name)
    
    def test_controller_initialization(self, controller):
        """Test controller initialization"""
        assert controller.max_file_size_mb == 100
        assert controller.temp_dir is not None
        assert controller.executor is not None
        assert isinstance(controller._upload_progress, dict)
        assert isinstance(controller._upload_locks, dict)
    
    @pytest.mark.asyncio
    async def test_detect_format_audio(self, controller, sample_audio_file):
        """Test format detection for audio files"""
        format_info = await controller.detect_format(sample_audio_file, "test.wav")
        
        assert format_info.file_type == "audio"
        assert format_info.extension == ".wav"
        assert format_info.is_supported is True
        assert "audio" in format_info.mime_type.lower()
    
    @pytest.mark.asyncio
    async def test_detect_format_image(self, controller, sample_image_file):
        """Test format detection for image files"""
        format_info = await controller.detect_format(sample_image_file, "test.png")
        
        assert format_info.file_type == "image"
        assert format_info.extension == ".png"
        assert format_info.is_supported is True
    
    @pytest.mark.asyncio
    async def test_detect_format_unsupported(self, controller):
        """Test format detection for unsupported files"""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b'test content')
            temp_path = f.name
        
        try:
            format_info = await controller.detect_format(temp_path, "test.xyz")
            assert format_info.file_type == "unknown"
            assert format_info.extension == ".xyz"
            assert format_info.is_supported is False
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_validate_content_valid_file(self, controller, sample_audio_file):
        """Test content validation for valid files"""
        media_file = MediaFile(
            id="test123",
            original_path=sample_audio_file,
            format=MediaFormat(
                file_type="audio",
                mime_type="audio/wav",
                extension=".wav",
                is_supported=True
            )
        )
        
        with patch('media_ingestion_controller.validate_media_file') as mock_validate:
            mock_validate.return_value = True
            result = await controller.validate_content(media_file)
            
            assert result["valid"] is True
    
    @pytest.mark.asyncio
    async def test_validate_content_invalid_file(self, controller):
        """Test content validation for invalid files"""
        media_file = MediaFile(
            id="test123",
            original_path="/nonexistent/file.wav",
            format=MediaFormat(
                file_type="audio",
                mime_type="audio/wav",
                extension=".wav",
                is_supported=True
            )
        )
        
        result = await controller.validate_content(media_file)
        assert result["valid"] is False
        assert "does not exist" in result["error"]
    
    @pytest.mark.asyncio
    async def test_validate_content_empty_file(self, controller):
        """Test content validation for empty files"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name  # Empty file
        
        try:
            media_file = MediaFile(
                id="test123",
                original_path=temp_path,
                format=MediaFormat(
                    file_type="audio",
                    mime_type="audio/wav",
                    extension=".wav",
                    is_supported=True
                )
            )
            
            result = await controller.validate_content(media_file)
            assert result["valid"] is False
            assert "empty" in result["error"]
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_validate_content_oversized_file(self, controller):
        """Test content validation for oversized files"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            # Write more than max size (100MB for test controller)
            f.write(b'x' * (101 * 1024 * 1024))
            temp_path = f.name
        
        try:
            media_file = MediaFile(
                id="test123",
                original_path=temp_path,
                format=MediaFormat(
                    file_type="audio",
                    mime_type="audio/wav",
                    extension=".wav",
                    is_supported=True
                )
            )
            
            result = await controller.validate_content(media_file)
            assert result["valid"] is False
            assert "too large" in result["error"]
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_preprocess_media_audio(self, controller, sample_audio_file):
        """Test media preprocessing for audio files"""
        media_file = MediaFile(
            id="test123",
            original_path=sample_audio_file,
            format=MediaFormat(
                file_type="audio",
                mime_type="audio/wav",
                extension=".wav",
                is_supported=True
            )
        )
        
        options = ProcessingOptions(enable_preprocessing=True)
        processed_path, operations, warnings = await controller.preprocess_media(media_file, options)
        
        assert processed_path == sample_audio_file  # Should return original for now
        assert "audio_preprocessing_skipped" in operations
        assert len(warnings) > 0
    
    @pytest.mark.asyncio
    async def test_preprocess_media_image(self, controller, sample_image_file):
        """Test media preprocessing for image files"""
        media_file = MediaFile(
            id="test123",
            original_path=sample_image_file,
            format=MediaFormat(
                file_type="image",
                mime_type="image/png",
                extension=".png",
                is_supported=True
            )
        )
        
        options = ProcessingOptions(enable_preprocessing=True)
        processed_path, operations, warnings = await controller.preprocess_media(media_file, options)
        
        assert processed_path is not None
        assert "image_validation" in operations
    
    @pytest.mark.asyncio
    async def test_stream_upload(self, controller):
        """Test streaming upload functionality"""
        test_data = b"test file content for streaming upload"
        stream = io.BytesIO(test_data)
        filename = "test_stream.txt"
        total_size = len(test_data)
        
        uploaded_path = await controller.stream_upload(stream, filename, total_size)
        
        assert os.path.exists(uploaded_path)
        assert filename in uploaded_path
        
        # Verify content
        with open(uploaded_path, 'rb') as f:
            content = f.read()
            assert content == test_data
        
        # Cleanup
        os.unlink(uploaded_path)
    
    def test_get_upload_progress(self, controller):
        """Test upload progress tracking"""
        upload_id = "test_upload_123"
        progress = StreamingUploadProgress(
            total_size=1000,
            uploaded_size=500,
            progress_percentage=50.0,
            upload_speed=100.0,
            estimated_time_remaining=5.0
        )
        
        controller._upload_progress[upload_id] = progress
        
        retrieved_progress = controller.get_upload_progress(upload_id)
        assert retrieved_progress == progress
        assert retrieved_progress.progress_percentage == 50.0
    
    def test_generate_media_id(self, controller):
        """Test media ID generation"""
        filename = "test.wav"
        media_id = controller._generate_media_id(filename)
        
        assert isinstance(media_id, str)
        assert len(media_id) == 16  # MD5 hash truncated to 16 chars
        
        # Should generate different IDs for same filename (due to timestamp)
        media_id2 = controller._generate_media_id(filename)
        assert media_id != media_id2
    
    def test_determine_file_type(self, controller):
        """Test file type determination logic"""
        # Test audio
        assert controller._determine_file_type(".mp3", "audio/mpeg") == "audio"
        assert controller._determine_file_type(".unknown", "audio/wav") == "audio"
        
        # Test video
        assert controller._determine_file_type(".mp4", "video/mp4") == "video"
        assert controller._determine_file_type(".unknown", "video/avi") == "video"
        
        # Test image
        assert controller._determine_file_type(".jpg", "image/jpeg") == "image"
        assert controller._determine_file_type(".unknown", "image/png") == "image"
        
        # Test document
        assert controller._determine_file_type(".pdf", "application/pdf") == "document"
        assert controller._determine_file_type(".unknown", "text/plain") == "document"
        
        # Test unknown
        assert controller._determine_file_type(".xyz", "application/octet-stream") == "unknown"
    
    @pytest.mark.asyncio
    async def test_analyze_quality_audio(self, controller, sample_audio_file):
        """Test quality analysis for audio files"""
        media_file = MediaFile(
            id="test123",
            original_path=sample_audio_file,
            format=MediaFormat(
                file_type="audio",
                mime_type="audio/wav",
                extension=".wav",
                is_supported=True
            )
        )
        
        with patch('media_ingestion_controller.get_media_info') as mock_info:
            mock_info.return_value = {
                'duration': 10.0,
                'bit_rate': 128000,
                'sample_rate': 44100,
                'channels': 2
            }
            
            metrics = await controller._analyze_quality(media_file)
            
            assert metrics.duration == 10.0
            assert metrics.bitrate == 128000
            assert metrics.sample_rate == 44100
            assert metrics.channels == 2
            assert metrics.quality_score > 50.0
    
    @pytest.mark.asyncio
    async def test_analyze_quality_image(self, controller, sample_image_file):
        """Test quality analysis for image files"""
        media_file = MediaFile(
            id="test123",
            original_path=sample_image_file,
            format=MediaFormat(
                file_type="image",
                mime_type="image/png",
                extension=".png",
                is_supported=True
            )
        )
        
        metrics = await controller._analyze_quality(media_file)
        
        assert metrics.resolution is not None
        assert metrics.quality_score >= 0.0
        assert metrics.file_size > 0
    
    @pytest.mark.asyncio
    async def test_ingest_media_success(self, controller, sample_audio_file):
        """Test successful media ingestion end-to-end"""
        options = ProcessingOptions(
            enable_preprocessing=True,
            enable_optimization=False
        )
        
        with patch('media_ingestion_controller.validate_media_file') as mock_validate:
            mock_validate.return_value = True
            
            with patch('media_ingestion_controller.get_media_info') as mock_info:
                mock_info.return_value = {
                    'duration': 5.0,
                    'bit_rate': 128000,
                    'sample_rate': 44100,
                    'channels': 1
                }
                
                result = await controller.ingest_media(sample_audio_file, "test.wav", options)
                
                assert result.success is True
                assert result.media_file.id is not None
                assert result.media_file.format.file_type == "audio"
                assert result.processing_time > 0
                assert len(result.operations_applied) > 0
    
    @pytest.mark.asyncio
    async def test_ingest_media_failure(self, controller):
        """Test media ingestion failure handling"""
        nonexistent_file = "/nonexistent/file.wav"
        
        result = await controller.ingest_media(nonexistent_file, "test.wav")
        
        assert result.success is False
        assert len(result.errors) > 0
        assert result.media_file.processing_status == "failed"
    
    @pytest.mark.asyncio
    async def test_validate_image_content_valid(self, controller, sample_image_file):
        """Test image content validation for valid images"""
        result = await controller._validate_image_content(sample_image_file)
        assert result["valid"] is True
    
    @pytest.mark.asyncio
    async def test_validate_image_content_invalid(self, controller):
        """Test image content validation for invalid images"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'not an image')
            temp_path = f.name
        
        try:
            result = await controller._validate_image_content(temp_path)
            assert result["valid"] is False
            assert "Invalid image" in result["error"]
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_validate_document_content_pdf(self, controller):
        """Test document content validation for PDF files"""
        # Create a minimal PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            # Write minimal PDF header
            f.write(b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n')
            temp_path = f.name
        
        try:
            with patch('fitz.open') as mock_fitz:
                mock_doc = Mock()
                mock_doc.page_count = 1
                mock_fitz.return_value = mock_doc
                
                result = await controller._validate_document_content(temp_path)
                assert result["valid"] is True
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_validate_document_content_txt(self, controller):
        """Test document content validation for text files"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("This is a test document.")
            temp_path = f.name
        
        try:
            result = await controller._validate_document_content(temp_path)
            assert result["valid"] is True
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_validate_document_content_empty_txt(self, controller):
        """Test document content validation for empty text files"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("")  # Empty file
            temp_path = f.name
        
        try:
            result = await controller._validate_document_content(temp_path)
            assert result["valid"] is False
            assert "empty" in result["error"]
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])