# Centralized Error Handling Module
# Custom exception classes and error handling utilities

import logging
import traceback
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)

class ErrorCode(Enum):
    """Enumeration of error codes for categorization"""
    # API Errors
    API_KEY_MISSING = "API_KEY_MISSING"
    API_RATE_LIMIT = "API_RATE_LIMIT"
    API_QUOTA_EXCEEDED = "API_QUOTA_EXCEEDED"
    API_NETWORK_ERROR = "API_NETWORK_ERROR"
    API_AUTHENTICATION_ERROR = "API_AUTHENTICATION_ERROR"
    API_SERVICE_UNAVAILABLE = "API_SERVICE_UNAVAILABLE"
    API_INVALID_REQUEST = "API_INVALID_REQUEST"
    
    # File Processing Errors
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    FILE_CORRUPTED = "FILE_CORRUPTED"
    FILE_UNSUPPORTED_FORMAT = "FILE_UNSUPPORTED_FORMAT"
    FILE_PERMISSION_ERROR = "FILE_PERMISSION_ERROR"
    FILE_PROCESSING_ERROR = "FILE_PROCESSING_ERROR"
    
    # Media Processing Errors
    MEDIA_EXTRACTION_ERROR = "MEDIA_EXTRACTION_ERROR"
    MEDIA_CONVERSION_ERROR = "MEDIA_CONVERSION_ERROR"
    MEDIA_VALIDATION_ERROR = "MEDIA_VALIDATION_ERROR"
    FFMPEG_ERROR = "FFMPEG_ERROR"
    
    # Transcription Errors
    TRANSCRIPTION_FAILED = "TRANSCRIPTION_FAILED"
    TRANSCRIPTION_TIMEOUT = "TRANSCRIPTION_TIMEOUT"
    TRANSCRIPTION_QUALITY_LOW = "TRANSCRIPTION_QUALITY_LOW"
    LOCAL_MODEL_ERROR = "LOCAL_MODEL_ERROR"
    
    # Entity Extraction Errors
    NER_PROCESSING_ERROR = "NER_PROCESSING_ERROR"
    NER_MODEL_ERROR = "NER_MODEL_ERROR"
    NER_INVALID_INPUT = "NER_INVALID_INPUT"
    
    # TTS Errors
    TTS_SYNTHESIS_ERROR = "TTS_SYNTHESIS_ERROR"
    TTS_VOICE_ERROR = "TTS_VOICE_ERROR"
    TTS_TEXT_TOO_LONG = "TTS_TEXT_TOO_LONG"
    
    # System Errors
    SYSTEM_RESOURCE_ERROR = "SYSTEM_RESOURCE_ERROR"
    SYSTEM_PERMISSION_ERROR = "SYSTEM_PERMISSION_ERROR"
    SYSTEM_DEPENDENCY_ERROR = "SYSTEM_DEPENDENCY_ERROR"
    
    # Network Errors
    NETWORK_CONNECTION_ERROR = "NETWORK_CONNECTION_ERROR"
    NETWORK_TIMEOUT_ERROR = "NETWORK_TIMEOUT_ERROR"
    NETWORK_DNS_ERROR = "NETWORK_DNS_ERROR"
    
    # Configuration Errors
    CONFIG_MISSING = "CONFIG_MISSING"
    CONFIG_INVALID = "CONFIG_INVALID"
    
    # Unknown/Generic Errors
    UNKNOWN_ERROR = "UNKNOWN_ERROR"

class AppError(Exception):
    """Base exception class for all application errors"""
    
    def __init__(self, 
                 message: str, 
                 error_code: ErrorCode, 
                 user_message: str,
                 suggestions: Optional[List[str]] = None,
                 details: Optional[Dict[str, Any]] = None,
                 original_error: Optional[Exception] = None):
        """
        Initialize application error
        
        Args:
            message: Technical error message for logging
            error_code: Categorized error code
            user_message: User-friendly error message
            suggestions: List of suggested actions for the user
            details: Additional error details for debugging
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.user_message = user_message
        self.suggestions = suggestions or []
        self.details = details or {}
        self.original_error = original_error
        
        # Log the error
        error_code_str = error_code.value if hasattr(error_code, 'value') else str(error_code)
        logger.error(f"AppError [{error_code_str}]: {message}")
        if original_error:
            logger.error(f"Original error: {str(original_error)}")
        if details:
            logger.debug(f"Error details: {details}")

class APIError(AppError):
    """Errors related to external API calls"""
    
    def __init__(self, message: str, error_code: ErrorCode, user_message: str,
                 api_name: str, status_code: Optional[int] = None, **kwargs):
        super().__init__(message, error_code, user_message, **kwargs)
        self.api_name = api_name
        self.status_code = status_code
        self.details.update({"api_name": api_name, "status_code": status_code})

class FileProcessingError(AppError):
    """Errors related to file processing operations"""
    
    def __init__(self, message: str, error_code: ErrorCode, user_message: str,
                 file_path: Optional[str] = None, file_size: Optional[int] = None, **kwargs):
        super().__init__(message, error_code, user_message, **kwargs)
        self.file_path = file_path
        self.file_size = file_size
        self.details.update({"file_path": file_path, "file_size": file_size})

class MediaProcessingError(AppError):
    """Errors related to media processing operations"""
    
    def __init__(self, message: str, error_code: ErrorCode, user_message: str,
                 media_type: Optional[str] = None, duration: Optional[float] = None, **kwargs):
        super().__init__(message, error_code, user_message, **kwargs)
        self.media_type = media_type
        self.duration = duration
        self.details.update({"media_type": media_type, "duration": duration})

class TranscriptionError(AppError):
    """Errors related to speech-to-text processing"""
    
    def __init__(self, message: str, error_code: ErrorCode, user_message: str,
                 model_used: Optional[str] = None, confidence: Optional[float] = None, **kwargs):
        super().__init__(message, error_code, user_message, **kwargs)
        self.model_used = model_used
        self.confidence = confidence
        self.details.update({"model_used": model_used, "confidence": confidence})

class NERError(AppError):
    """Errors related to named entity recognition"""
    
    def __init__(self, message: str, error_code: ErrorCode, user_message: str,
                 ner_type: Optional[str] = None, text_length: Optional[int] = None, **kwargs):
        super().__init__(message, error_code, user_message, **kwargs)
        self.ner_type = ner_type
        self.text_length = text_length
        self.details.update({"ner_type": ner_type, "text_length": text_length})

class TTSError(AppError):
    """Errors related to text-to-speech synthesis"""
    
    def __init__(self, message: str, error_code: ErrorCode, user_message: str,
                 voice_id: Optional[str] = None, text_length: Optional[int] = None, **kwargs):
        super().__init__(message, error_code, user_message, **kwargs)
        self.voice_id = voice_id
        self.text_length = text_length
        self.details.update({"voice_id": voice_id, "text_length": text_length})

class NetworkError(AppError):
    """Errors related to network connectivity"""
    
    def __init__(self, message: str, error_code: ErrorCode, user_message: str,
                 endpoint: Optional[str] = None, timeout: Optional[float] = None, **kwargs):
        super().__init__(message, error_code, user_message, **kwargs)
        self.endpoint = endpoint
        self.timeout = timeout
        self.details.update({"endpoint": endpoint, "timeout": timeout})

class ConfigurationError(AppError):
    """Errors related to application configuration"""
    
    def __init__(self, message: str, error_code: ErrorCode, user_message: str,
                 config_key: Optional[str] = None, **kwargs):
        super().__init__(message, error_code, user_message, **kwargs)
        self.config_key = config_key
        self.details.update({"config_key": config_key})

class ErrorHandler:
    """Centralized error handling and recovery system"""
    
    def __init__(self):
        self.error_counts = {}
        self.fallback_strategies = {}
        self._setup_fallback_strategies()
    
    def _setup_fallback_strategies(self):
        """Setup fallback strategies for different error types"""
        self.fallback_strategies = {
            ErrorCode.API_RATE_LIMIT: self._handle_rate_limit,
            ErrorCode.API_SERVICE_UNAVAILABLE: self._handle_api_unavailable,
            ErrorCode.API_AUTHENTICATION_ERROR: self._handle_auth_error,
            ErrorCode.TRANSCRIPTION_FAILED: self._handle_transcription_fallback,
            ErrorCode.NER_PROCESSING_ERROR: self._handle_ner_fallback,
            ErrorCode.NETWORK_CONNECTION_ERROR: self._handle_network_error,
            ErrorCode.FILE_CORRUPTED: self._handle_file_corruption,
            ErrorCode.LOCAL_MODEL_ERROR: self._handle_model_error,
        }
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> AppError:
        """
        Handle any exception and convert to appropriate AppError
        
        Args:
            error: The exception to handle
            context: Additional context information
            
        Returns:
            AppError with appropriate categorization and user guidance
        """
        context = context or {}
        
        # If already an AppError, apply fallback strategies and return
        if isinstance(error, AppError):
            self._track_error(error.error_code)
            # Apply fallback strategy if available
            if error.error_code in self.fallback_strategies:
                try:
                    self.fallback_strategies[error.error_code](error, context)
                except Exception as fallback_error:
                    logger.error(f"Fallback strategy failed: {fallback_error}")
            return error
        
        # Convert common exceptions to AppErrors
        app_error = self._convert_to_app_error(error, context)
        self._track_error(app_error.error_code)
        
        # Apply fallback strategy if available
        if app_error.error_code in self.fallback_strategies:
            try:
                self.fallback_strategies[app_error.error_code](app_error, context)
            except Exception as fallback_error:
                logger.error(f"Fallback strategy failed: {fallback_error}")
        
        return app_error
    
    def _convert_to_app_error(self, error: Exception, context: Dict[str, Any]) -> AppError:
        """Convert generic exceptions to AppError instances"""
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # API-related errors
        if "api" in error_str or "openai" in error_str or "elevenlabs" in error_str:
            return self._handle_api_error(error, context)
        
        # File-related errors
        elif "file" in error_str or isinstance(error, (FileNotFoundError, PermissionError, OSError)):
            return self._handle_file_error(error, context)
        
        # Network-related errors
        elif any(term in error_str for term in ["network", "connection", "timeout", "dns"]):
            return self._handle_network_error_conversion(error, context)
        
        # FFmpeg/Media errors
        elif "ffmpeg" in error_str or "media" in error_str:
            return self._handle_media_error(error, context)
        
        # Model loading errors
        elif "model" in error_str or "spacy" in error_str or "whisper" in error_str:
            return self._handle_model_error_conversion(error, context)
        
        # Generic error
        else:
            return AppError(
                message=f"Unexpected error: {str(error)}",
                error_code=ErrorCode.UNKNOWN_ERROR,
                user_message="An unexpected error occurred. Please try again.",
                suggestions=[
                    "Try refreshing the page and attempting the operation again",
                    "Check your internet connection",
                    "Contact support if the issue persists"
                ],
                original_error=error,
                details=context
            )
    
    def _handle_api_error(self, error: Exception, context: Dict[str, Any]) -> APIError:
        """Handle API-related errors"""
        error_str = str(error).lower()
        
        if "api key" in error_str or "authentication" in error_str:
            return APIError(
                message=f"API authentication failed: {str(error)}",
                error_code=ErrorCode.API_AUTHENTICATION_ERROR,
                user_message="API authentication failed. Please check your API key configuration.",
                api_name=context.get("api_name", "unknown"),
                suggestions=[
                    "Verify your API key is correctly set in the .env file",
                    "Check that your API key has the required permissions",
                    "Ensure your API key hasn't expired"
                ],
                original_error=error
            )
        elif "rate limit" in error_str:
            return APIError(
                message=f"API rate limit exceeded: {str(error)}",
                error_code=ErrorCode.API_RATE_LIMIT,
                user_message="API rate limit exceeded. Please wait before trying again.",
                api_name=context.get("api_name", "unknown"),
                suggestions=[
                    "Wait a few minutes before retrying",
                    "Consider upgrading your API plan for higher limits",
                    "Try using offline mode if available"
                ],
                original_error=error
            )
        elif "quota" in error_str or "billing" in error_str:
            return APIError(
                message=f"API quota exceeded: {str(error)}",
                error_code=ErrorCode.API_QUOTA_EXCEEDED,
                user_message="API quota exceeded. Please check your account billing.",
                api_name=context.get("api_name", "unknown"),
                suggestions=[
                    "Check your API account billing and usage",
                    "Add credits to your API account",
                    "Try using offline mode if available"
                ],
                original_error=error
            )
        else:
            return APIError(
                message=f"API service error: {str(error)}",
                error_code=ErrorCode.API_SERVICE_UNAVAILABLE,
                user_message="API service is temporarily unavailable.",
                api_name=context.get("api_name", "unknown"),
                suggestions=[
                    "Try again in a few minutes",
                    "Check the service status page",
                    "Use offline mode if available"
                ],
                original_error=error
            ) 
   
    def _handle_file_error(self, error: Exception, context: Dict[str, Any]) -> FileProcessingError:
        """Handle file-related errors"""
        error_str = str(error).lower()
        
        if isinstance(error, FileNotFoundError) or "not found" in error_str:
            return FileProcessingError(
                message=f"File not found: {str(error)}",
                error_code=ErrorCode.FILE_NOT_FOUND,
                user_message="The specified file could not be found.",
                file_path=context.get("file_path"),
                suggestions=[
                    "Check that the file exists and the path is correct",
                    "Ensure the file hasn't been moved or deleted",
                    "Try uploading the file again"
                ],
                original_error=error
            )
        elif isinstance(error, PermissionError) or "permission" in error_str:
            return FileProcessingError(
                message=f"File permission error: {str(error)}",
                error_code=ErrorCode.FILE_PERMISSION_ERROR,
                user_message="Permission denied accessing the file.",
                file_path=context.get("file_path"),
                suggestions=[
                    "Check file permissions",
                    "Ensure the file is not locked by another application",
                    "Try copying the file to a different location"
                ],
                original_error=error
            )
        elif "size" in error_str or "too large" in error_str:
            return FileProcessingError(
                message=f"File too large: {str(error)}",
                error_code=ErrorCode.FILE_TOO_LARGE,
                user_message="The file is too large to process.",
                file_path=context.get("file_path"),
                file_size=context.get("file_size"),
                suggestions=[
                    f"Reduce file size to under {context.get('max_size', 2048)}MB",
                    "Compress the audio/video file",
                    "Split large files into smaller segments"
                ],
                original_error=error
            )
        elif "format" in error_str or "unsupported" in error_str:
            return FileProcessingError(
                message=f"Unsupported file format: {str(error)}",
                error_code=ErrorCode.FILE_UNSUPPORTED_FORMAT,
                user_message="The file format is not supported.",
                file_path=context.get("file_path"),
                suggestions=[
                    "Convert to a supported format (MP3, WAV, MP4, M4A)",
                    "Check that the file is not corrupted",
                    "Try a different file"
                ],
                original_error=error
            )
        else:
            return FileProcessingError(
                message=f"File processing error: {str(error)}",
                error_code=ErrorCode.FILE_PROCESSING_ERROR,
                user_message="An error occurred while processing the file.",
                file_path=context.get("file_path"),
                suggestions=[
                    "Try a different file",
                    "Check that the file is not corrupted",
                    "Ensure the file format is supported"
                ],
                original_error=error
            )
    
    def _handle_network_error_conversion(self, error: Exception, context: Dict[str, Any]) -> NetworkError:
        """Handle network-related errors"""
        error_str = str(error).lower()
        
        if "timeout" in error_str:
            return NetworkError(
                message=f"Network timeout: {str(error)}",
                error_code=ErrorCode.NETWORK_TIMEOUT_ERROR,
                user_message="The request timed out. Please check your internet connection.",
                endpoint=context.get("endpoint"),
                timeout=context.get("timeout"),
                suggestions=[
                    "Check your internet connection",
                    "Try again with a stable network connection",
                    "Use offline mode if available"
                ],
                original_error=error
            )
        elif "dns" in error_str or "resolve" in error_str:
            return NetworkError(
                message=f"DNS resolution error: {str(error)}",
                error_code=ErrorCode.NETWORK_DNS_ERROR,
                user_message="Unable to resolve the server address.",
                endpoint=context.get("endpoint"),
                suggestions=[
                    "Check your internet connection",
                    "Try using a different DNS server",
                    "Check if the service is currently available"
                ],
                original_error=error
            )
        else:
            return NetworkError(
                message=f"Network connection error: {str(error)}",
                error_code=ErrorCode.NETWORK_CONNECTION_ERROR,
                user_message="Unable to connect to the service.",
                endpoint=context.get("endpoint"),
                suggestions=[
                    "Check your internet connection",
                    "Verify firewall settings",
                    "Try again later"
                ],
                original_error=error
            )
    
    def _handle_media_error(self, error: Exception, context: Dict[str, Any]) -> MediaProcessingError:
        """Handle media processing errors"""
        error_str = str(error).lower()
        
        if "ffmpeg" in error_str:
            return MediaProcessingError(
                message=f"FFmpeg error: {str(error)}",
                error_code=ErrorCode.FFMPEG_ERROR,
                user_message="Media processing failed due to FFmpeg error.",
                media_type=context.get("media_type"),
                suggestions=[
                    "Check that the media file is not corrupted",
                    "Try a different file format",
                    "Ensure FFmpeg is properly installed"
                ],
                original_error=error
            )
        elif "extract" in error_str:
            return MediaProcessingError(
                message=f"Audio extraction failed: {str(error)}",
                error_code=ErrorCode.MEDIA_EXTRACTION_ERROR,
                user_message="Failed to extract audio from the video file.",
                media_type=context.get("media_type"),
                suggestions=[
                    "Try a different video file",
                    "Check that the video contains an audio track",
                    "Convert the video to a different format"
                ],
                original_error=error
            )
        else:
            return MediaProcessingError(
                message=f"Media processing error: {str(error)}",
                error_code=ErrorCode.MEDIA_PROCESSING_ERROR,
                user_message="An error occurred while processing the media file.",
                media_type=context.get("media_type"),
                suggestions=[
                    "Try a different media file",
                    "Check that the file is not corrupted",
                    "Ensure the file format is supported"
                ],
                original_error=error
            )
    
    def _handle_model_error_conversion(self, error: Exception, context: Dict[str, Any]) -> AppError:
        """Handle model loading/processing errors"""
        error_str = str(error).lower()
        
        if "spacy" in error_str:
            return NERError(
                message=f"spaCy model error: {str(error)}",
                error_code=ErrorCode.NER_MODEL_ERROR,
                user_message="The language processing model failed to load.",
                ner_type="spacy",
                suggestions=[
                    "Install the spaCy English model: python -m spacy download en_core_web_sm",
                    "Try using Advanced mode instead",
                    "Restart the application"
                ],
                original_error=error
            )
        elif "whisper" in error_str:
            return TranscriptionError(
                message=f"Whisper model error: {str(error)}",
                error_code=ErrorCode.LOCAL_MODEL_ERROR,
                user_message="The transcription model failed to load.",
                model_used="whisper-local",
                suggestions=[
                    "Try using API mode instead of local processing",
                    "Restart the application",
                    "Check available disk space and memory"
                ],
                original_error=error
            )
        else:
            return AppError(
                message=f"Model error: {str(error)}",
                error_code=ErrorCode.SYSTEM_DEPENDENCY_ERROR,
                user_message="A required model or dependency failed to load.",
                suggestions=[
                    "Restart the application",
                    "Check that all dependencies are installed",
                    "Try a different processing mode"
                ],
                original_error=error
            )
    
    def _track_error(self, error_code: ErrorCode):
        """Track error occurrences for monitoring"""
        if error_code not in self.error_counts:
            self.error_counts[error_code] = 0
        self.error_counts[error_code] += 1
        
        # Log frequent errors
        if self.error_counts[error_code] % 5 == 0:
            logger.warning(f"Error {error_code.value} has occurred {self.error_counts[error_code]} times")
    
    # Fallback strategy implementations
    def _handle_rate_limit(self, error: AppError, context: Dict[str, Any]):
        """Handle rate limit errors with exponential backoff"""
        logger.info("Implementing rate limit fallback strategy")
        if "wait" not in " ".join(error.suggestions).lower():
            error.suggestions.insert(0, "Wait a few minutes before retrying")
    
    def _handle_api_unavailable(self, error: AppError, context: Dict[str, Any]):
        """Handle API unavailability by suggesting fallback modes"""
        logger.info("API unavailable, suggesting fallback to local processing")
        if "offline" not in " ".join(error.suggestions).lower():
            error.suggestions.insert(0, "Try switching to Basic (offline) mode")
    
    def _handle_auth_error(self, error: AppError, context: Dict[str, Any]):
        """Handle authentication errors"""
        logger.info("Authentication error detected")
        error.suggestions.insert(0, "Check your API key configuration in the .env file")
    
    def _handle_transcription_fallback(self, error: AppError, context: Dict[str, Any]):
        """Handle transcription failures with fallback suggestions"""
        logger.info("Transcription failed, suggesting alternatives")
        if "api" in error.message.lower():
            error.suggestions.insert(0, "Try using offline transcription mode")
        else:
            error.suggestions.insert(0, "Try using API transcription mode")
    
    def _handle_ner_fallback(self, error: AppError, context: Dict[str, Any]):
        """Handle NER failures with mode switching suggestions"""
        logger.info("NER processing failed, suggesting alternative mode")
        if isinstance(error, NERError):
            if error.ner_type == "advanced":
                if "basic" not in " ".join(error.suggestions).lower():
                    error.suggestions.insert(0, "Try switching to Basic (spaCy) mode")
            else:
                if "advanced" not in " ".join(error.suggestions).lower():
                    error.suggestions.insert(0, "Try switching to Advanced (AI) mode")
    
    def _handle_network_error(self, error: AppError, context: Dict[str, Any]):
        """Handle network errors with offline suggestions"""
        logger.info("Network error detected, suggesting offline alternatives")
        error.suggestions.insert(0, "Try using offline processing modes")
    
    def _handle_file_corruption(self, error: AppError, context: Dict[str, Any]):
        """Handle file corruption with recovery suggestions"""
        logger.info("File corruption detected")
        error.suggestions.extend([
            "Try re-uploading the file",
            "Check the original file for corruption",
            "Convert the file to a different format"
        ])
    
    def _handle_model_error(self, error: AppError, context: Dict[str, Any]):
        """Handle model loading errors"""
        logger.info("Model error detected, suggesting alternatives")
        error.suggestions.insert(0, "Try restarting the application")
    
    def get_error_statistics(self) -> Dict[str, int]:
        """Get error occurrence statistics"""
        return dict(self.error_counts)
    
    def reset_error_counts(self):
        """Reset error tracking counters"""
        self.error_counts.clear()
        logger.info("Error tracking counters reset")

# Global error handler instance
_error_handler = None

def get_error_handler() -> ErrorHandler:
    """Get or create global error handler instance"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler

def handle_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> AppError:
    """
    Global error handling function
    
    Args:
        error: The exception to handle
        context: Additional context information
        
    Returns:
        AppError with appropriate categorization and user guidance
    """
    handler = get_error_handler()
    return handler.handle_error(error, context)

def create_user_error_message(error: AppError) -> Dict[str, Any]:
    """
    Create a user-friendly error message dictionary for UI display
    
    Args:
        error: The AppError to format
        
    Returns:
        Dictionary with formatted error information for UI
    """
    return {
        "title": "Error Occurred",
        "message": error.user_message,
        "error_code": error.error_code.value,
        "suggestions": error.suggestions,
        "details": {
            "error_type": type(error).__name__,
            "timestamp": logger.handlers[0].formatter.formatTime(logger.makeRecord(
                "error", logging.ERROR, "", 0, "", (), None
            )) if logger.handlers else "unknown"
        }
    }

def log_error_for_monitoring(error: AppError, user_id: Optional[str] = None):
    """
    Log error for monitoring and analytics
    
    Args:
        error: The AppError to log
        user_id: Optional user identifier
    """
    log_data = {
        "error_code": error.error_code.value,
        "error_type": type(error).__name__,
        "message": error.message,
        "user_id": user_id,
        "details": error.details
    }
    
    logger.error(f"Error monitoring: {log_data}")

# Common error creation helpers
def create_api_key_error(api_name: str) -> APIError:
    """Create a standardized API key missing error"""
    return APIError(
        message=f"{api_name} API key not configured",
        error_code=ErrorCode.API_KEY_MISSING,
        user_message=f"{api_name} API key is required but not configured.",
        api_name=api_name,
        suggestions=[
            f"Add your {api_name} API key to the .env file",
            f"Ensure the {api_name.upper()}_API_KEY environment variable is set",
            "Restart the application after adding the API key"
        ]
    )

def create_file_size_error(file_path: str, file_size: int, max_size: int) -> FileProcessingError:
    """Create a standardized file size error"""
    return FileProcessingError(
        message=f"File {file_path} size {file_size}MB exceeds limit {max_size}MB",
        error_code=ErrorCode.FILE_TOO_LARGE,
        user_message=f"File is too large ({file_size}MB). Maximum allowed size is {max_size}MB.",
        file_path=file_path,
        file_size=file_size,
        suggestions=[
            f"Reduce file size to under {max_size}MB",
            "Compress the audio/video file",
            "Split large files into smaller segments"
        ]
    )

def create_network_timeout_error(endpoint: str, timeout: float) -> NetworkError:
    """Create a standardized network timeout error"""
    return NetworkError(
        message=f"Request to {endpoint} timed out after {timeout}s",
        error_code=ErrorCode.NETWORK_TIMEOUT_ERROR,
        user_message="The request timed out. Please check your internet connection.",
        endpoint=endpoint,
        timeout=timeout,
        suggestions=[
            "Check your internet connection",
            "Try again with a stable network connection",
            "Use offline mode if available"
        ]
    )