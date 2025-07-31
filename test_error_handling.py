# Error Handling Tests
# Comprehensive tests for the centralized error handling system

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from errors import (
    ErrorCode, AppError, APIError, FileProcessingError, MediaProcessingError,
    TranscriptionError, NERError, TTSError, NetworkError, ConfigurationError,
    ErrorHandler, handle_error, create_api_key_error, create_file_size_error,
    create_network_timeout_error, create_user_error_message
)

class TestErrorClasses:
    """Test custom error classes"""
    
    def test_app_error_creation(self):
        """Test basic AppError creation"""
        error = AppError(
            message="Test error",
            error_code=ErrorCode.UNKNOWN_ERROR,
            user_message="User friendly message",
            suggestions=["Try again"],
            details={"key": "value"}
        )
        
        assert error.message == "Test error"
        assert error.error_code == ErrorCode.UNKNOWN_ERROR
        assert error.user_message == "User friendly message"
        assert error.suggestions == ["Try again"]
        assert error.details == {"key": "value"}
    
    def test_api_error_creation(self):
        """Test APIError with specific fields"""
        error = APIError(
            message="API failed",
            error_code=ErrorCode.API_RATE_LIMIT,
            user_message="Rate limit exceeded",
            api_name="OpenAI",
            status_code=429
        )
        
        assert error.api_name == "OpenAI"
        assert error.status_code == 429
        assert error.details["api_name"] == "OpenAI"
        assert error.details["status_code"] == 429
    
    def test_file_processing_error_creation(self):
        """Test FileProcessingError with file details"""
        error = FileProcessingError(
            message="File too large",
            error_code=ErrorCode.FILE_TOO_LARGE,
            user_message="File exceeds size limit",
            file_path="/test/file.mp3",
            file_size=150
        )
        
        assert error.file_path == "/test/file.mp3"
        assert error.file_size == 150
        assert error.details["file_path"] == "/test/file.mp3"
        assert error.details["file_size"] == 150

class TestErrorHandler:
    """Test the centralized error handler"""
    
    def setup_method(self):
        """Setup for each test"""
        self.handler = ErrorHandler()
    
    def test_handle_generic_exception(self):
        """Test handling of generic exceptions"""
        original_error = ValueError("Test value error")
        app_error = self.handler.handle_error(original_error)
        
        assert isinstance(app_error, AppError)
        assert app_error.error_code == ErrorCode.UNKNOWN_ERROR
        assert app_error.original_error == original_error
        assert "unexpected error" in app_error.user_message.lower()
    
    def test_handle_file_not_found_error(self):
        """Test handling of FileNotFoundError"""
        original_error = FileNotFoundError("File not found")
        app_error = self.handler.handle_error(original_error, {"file_path": "/test/file.mp3"})
        
        assert isinstance(app_error, FileProcessingError)
        assert app_error.error_code == ErrorCode.FILE_NOT_FOUND
        assert app_error.file_path == "/test/file.mp3"
    
    def test_handle_permission_error(self):
        """Test handling of PermissionError"""
        original_error = PermissionError("Permission denied")
        app_error = self.handler.handle_error(original_error)
        
        assert isinstance(app_error, FileProcessingError)
        assert app_error.error_code == ErrorCode.FILE_PERMISSION_ERROR
    
    def test_handle_api_related_error(self):
        """Test handling of API-related errors"""
        original_error = Exception("OpenAI API rate limit exceeded")
        app_error = self.handler.handle_error(original_error, {"api_name": "OpenAI"})
        
        assert isinstance(app_error, APIError)
        assert app_error.error_code == ErrorCode.API_RATE_LIMIT
        assert app_error.api_name == "OpenAI"
    
    def test_error_tracking(self):
        """Test error occurrence tracking"""
        error1 = ValueError("Test error 1")
        error2 = ValueError("Test error 2")
        
        self.handler.handle_error(error1)
        self.handler.handle_error(error2)
        
        stats = self.handler.get_error_statistics()
        assert stats[ErrorCode.UNKNOWN_ERROR] == 2
    
    def test_fallback_strategy_application(self):
        """Test that fallback strategies are applied"""
        # Create an error that has a fallback strategy
        api_error = APIError(
            message="Service unavailable",
            error_code=ErrorCode.API_SERVICE_UNAVAILABLE,
            user_message="Service down",
            api_name="OpenAI"
        )
        
        result = self.handler.handle_error(api_error)
        
        # Check that fallback suggestion was added
        assert any("offline" in suggestion.lower() for suggestion in result.suggestions)

class TestErrorCreationHelpers:
    """Test error creation helper functions"""
    
    def test_create_api_key_error(self):
        """Test API key error creation"""
        error = create_api_key_error("OpenAI")
        
        assert isinstance(error, APIError)
        assert error.error_code == ErrorCode.API_KEY_MISSING
        assert error.api_name == "OpenAI"
        assert "API key" in error.user_message
    
    def test_create_file_size_error(self):
        """Test file size error creation"""
        error = create_file_size_error("/test/file.mp3", 150, 100)
        
        assert isinstance(error, FileProcessingError)
        assert error.error_code == ErrorCode.FILE_TOO_LARGE
        assert error.file_path == "/test/file.mp3"
        assert error.file_size == 150
        assert "150MB" in error.user_message
        assert "100MB" in error.user_message
    
    def test_create_network_timeout_error(self):
        """Test network timeout error creation"""
        error = create_network_timeout_error("https://api.openai.com", 30.0)
        
        assert isinstance(error, NetworkError)
        assert error.error_code == ErrorCode.NETWORK_TIMEOUT_ERROR
        assert error.endpoint == "https://api.openai.com"
        assert error.timeout == 30.0

class TestModuleIntegration:
    """Test error handling integration with existing modules"""
    
    @patch('media.ffmpeg.probe')
    def test_media_validation_error_handling(self, mock_probe):
        """Test media module error handling"""
        from media import validate_media_file
        
        # Test file not found
        with pytest.raises(FileProcessingError) as exc_info:
            validate_media_file("/nonexistent/file.mp3")
        
        assert exc_info.value.error_code == ErrorCode.FILE_NOT_FOUND
        assert "could not be found" in exc_info.value.user_message.lower()
    
    def test_media_file_size_validation(self):
        """Test file size validation in media module"""
        from media import validate_media_file
        
        # Create a temporary file that's too large
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            # Write some data to make it non-empty
            temp_file.write(b"test data")
            temp_path = temp_file.name
        
        try:
            with pytest.raises(FileProcessingError) as exc_info:
                validate_media_file(temp_path, max_size_mb=0)  # Set very small limit
            
            assert exc_info.value.error_code == ErrorCode.FILE_TOO_LARGE
        finally:
            os.unlink(temp_path)
    
    @patch('ner_basic.spacy.load')
    def test_ner_basic_model_error_handling(self, mock_spacy_load):
        """Test NER basic module error handling"""
        from ner_basic import extract_entities
        
        # Mock spaCy model loading failure
        mock_spacy_load.side_effect = OSError("Model not found")
        
        with pytest.raises(NERError) as exc_info:
            extract_entities("Test text")
        
        assert exc_info.value.error_code == ErrorCode.NER_MODEL_ERROR
        assert exc_info.value.ner_type == "spacy"
        assert "install" in exc_info.value.suggestions[0].lower()
    
    @patch.dict(os.environ, {}, clear=True)
    def test_api_key_missing_errors(self):
        """Test API key missing error handling"""
        from errors import create_api_key_error
        
        # Test OpenAI API key missing
        error = create_api_key_error("OpenAI")
        assert error.error_code == ErrorCode.API_KEY_MISSING
        assert "OpenAI" in error.user_message
        
        # Test ElevenLabs API key missing
        error = create_api_key_error("ElevenLabs")
        assert error.error_code == ErrorCode.API_KEY_MISSING
        assert "ElevenLabs" in error.user_message

class TestGracefulDegradation:
    """Test graceful degradation scenarios"""
    
    def test_transcription_api_to_local_fallback(self):
        """Test fallback from API to local transcription"""
        # This would be implemented in the actual transcription logic
        # Here we test the error handling structure
        
        api_error = APIError(
            message="API unavailable",
            error_code=ErrorCode.API_SERVICE_UNAVAILABLE,
            user_message="Service unavailable",
            api_name="OpenAI"
        )
        
        handler = ErrorHandler()
        result = handler.handle_error(api_error)
        
        # Check that offline suggestion is provided
        assert any("offline" in suggestion.lower() for suggestion in result.suggestions)
    
    def test_advanced_to_basic_ner_fallback(self):
        """Test fallback from advanced to basic NER"""
        ner_error = NERError(
            message="Advanced NER failed",
            error_code=ErrorCode.NER_PROCESSING_ERROR,
            user_message="AI analysis failed",
            ner_type="advanced"
        )
        
        handler = ErrorHandler()
        result = handler.handle_error(ner_error)
        
        # Check that basic mode suggestion is provided
        assert any("basic" in suggestion.lower() for suggestion in result.suggestions)

class TestUserErrorMessages:
    """Test user-friendly error message creation"""
    
    def test_create_user_error_message(self):
        """Test user error message formatting"""
        error = AppError(
            message="Technical error",
            error_code=ErrorCode.FILE_NOT_FOUND,
            user_message="File not found",
            suggestions=["Try again", "Check path"]
        )
        
        user_message = create_user_error_message(error)
        
        assert user_message["title"] == "Error Occurred"
        assert user_message["message"] == "File not found"
        assert user_message["error_code"] == "FILE_NOT_FOUND"
        assert user_message["suggestions"] == ["Try again", "Check path"]
        assert "error_type" in user_message["details"]
    
    def test_error_message_suggestions(self):
        """Test that appropriate suggestions are provided"""
        # Test API error suggestions
        api_error = create_api_key_error("OpenAI")
        assert any("API key" in suggestion for suggestion in api_error.suggestions)
        assert any(".env" in suggestion for suggestion in api_error.suggestions)
        
        # Test file error suggestions
        file_error = create_file_size_error("/test.mp3", 150, 100)
        assert any("compress" in suggestion.lower() for suggestion in file_error.suggestions)
        assert any("100MB" in suggestion for suggestion in file_error.suggestions)

class TestErrorRecovery:
    """Test error recovery and retry mechanisms"""
    
    def test_retry_logic_structure(self):
        """Test that retry logic is properly structured"""
        handler = ErrorHandler()
        
        # Test that rate limit errors suggest waiting
        rate_limit_error = APIError(
            message="Rate limited",
            error_code=ErrorCode.API_RATE_LIMIT,
            user_message="Too many requests",
            api_name="OpenAI"
        )
        
        result = handler.handle_error(rate_limit_error)
        assert any("wait" in suggestion.lower() for suggestion in result.suggestions)
    
    def test_network_error_recovery(self):
        """Test network error recovery suggestions"""
        network_error = create_network_timeout_error("https://api.openai.com", 30.0)
        
        assert any("connection" in suggestion.lower() for suggestion in network_error.suggestions)
        assert any("offline" in suggestion.lower() for suggestion in network_error.suggestions)

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])