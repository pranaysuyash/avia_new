"""
Custom Exception Classes for Whisper Advanced Integration

This module defines custom exception classes for different error types in the
Whisper Advanced Integration system, providing detailed error information and
recovery suggestions.

Requirements addressed:
- 7.5: Comprehensive error handling and recovery mechanisms
- 7.6: Detailed error logging and monitoring with alerting capabilities
"""

from typing import Optional, Dict, Any, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error category types"""
    VALIDATION = "validation"
    PROCESSING = "processing"
    RESOURCE = "resource"
    AUTHENTICATION = "authentication"
    NETWORK = "network"
    MODEL = "model"
    CONFIGURATION = "configuration"

class WhisperAdvancedException(Exception):
    """Base exception class for Whisper Advanced Integration"""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        recovery_suggestions: Optional[List[str]] = None,
        original_exception: Optional[Exception] = None
    ):
        """
        Initialize base exception
        
        Args:
            message: Human-readable error message
            error_code: Unique error code for identification
            category: Error category
            severity: Error severity level
            details: Additional error details
            recovery_suggestions: List of recovery suggestions
            original_exception: Original exception that caused this error
        """
        super().__init__(message)
        
        self.message = message
        self.error_code = error_code
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.recovery_suggestions = recovery_suggestions or []
        self.original_exception = original_exception
        
        # Log the error
        self._log_error()
    
    def _log_error(self):
        """Log the error with appropriate level"""
        log_message = f"[{self.error_code}] {self.message}"
        
        if self.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, extra=self._get_log_extra())
        elif self.severity == ErrorSeverity.HIGH:
            logger.error(log_message, extra=self._get_log_extra())
        elif self.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message, extra=self._get_log_extra())
        else:
            logger.info(log_message, extra=self._get_log_extra())
    
    def _get_log_extra(self) -> Dict[str, Any]:
        """Get extra logging information"""
        return {
            'error_code': self.error_code,
            'category': self.category.value,
            'severity': self.severity.value,
            'details': self.details,
            'recovery_suggestions': self.recovery_suggestions,
            'original_exception': str(self.original_exception) if self.original_exception else None
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            'error': True,
            'message': self.message,
            'error_code': self.error_code,
            'category': self.category.value,
            'severity': self.severity.value,
            'details': self.details,
            'recovery_suggestions': self.recovery_suggestions,
            'original_error': str(self.original_exception) if self.original_exception else None
        }

class ValidationError(WhisperAdvancedException):
    """Exception for input validation errors"""
    
    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        expected_format: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if field_name:
            details['field_name'] = field_name
        if field_value is not None:
            details['field_value'] = field_value
        if expected_format:
            details['expected_format'] = expected_format
        
        recovery_suggestions = kwargs.get('recovery_suggestions', [
            "Check input parameters and format",
            "Refer to API documentation for valid values",
            "Validate input data before submission"
        ])
        
        super().__init__(
            message=message,
            error_code=kwargs.get('error_code', 'VALIDATION_ERROR'),
            category=ErrorCategory.VALIDATION,
            severity=kwargs.get('severity', ErrorSeverity.LOW),
            details=details,
            recovery_suggestions=recovery_suggestions,
            original_exception=kwargs.get('original_exception')
        )

class AudioFileError(ValidationError):
    """Exception for audio file validation errors"""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        file_size_mb: Optional[float] = None,
        file_format: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if file_path:
            details['file_path'] = file_path
        if file_size_mb is not None:
            details['file_size_mb'] = file_size_mb
        if file_format:
            details['file_format'] = file_format
        
        recovery_suggestions = kwargs.get('recovery_suggestions', [
            "Check if file exists and is accessible",
            "Verify file format is supported (mp3, wav, m4a, etc.)",
            "Ensure file size is within limits (25MB for OpenAI API)",
            "Try converting to a supported format"
        ])
        
        super().__init__(
            message=message,
            error_code=kwargs.get('error_code', 'AUDIO_FILE_ERROR'),
            details=details,
            recovery_suggestions=recovery_suggestions,
            **kwargs
        )

class ConfigurationError(ValidationError):
    """Exception for configuration validation errors"""
    
    def __init__(
        self,
        message: str,
        config_parameter: Optional[str] = None,
        config_value: Optional[Any] = None,
        valid_range: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if config_parameter:
            details['config_parameter'] = config_parameter
        if config_value is not None:
            details['config_value'] = config_value
        if valid_range:
            details['valid_range'] = valid_range
        
        recovery_suggestions = kwargs.get('recovery_suggestions', [
            "Check configuration parameter values",
            "Refer to documentation for valid parameter ranges",
            "Use default configuration if unsure",
            "Validate configuration before processing"
        ])
        
        super().__init__(
            message=message,
            error_code=kwargs.get('error_code', 'CONFIGURATION_ERROR'),
            details=details,
            recovery_suggestions=recovery_suggestions,
            **kwargs
        )

class ProcessingError(WhisperAdvancedException):
    """Exception for processing errors during transcription"""
    
    def __init__(
        self,
        message: str,
        processing_stage: Optional[str] = None,
        audio_duration: Optional[float] = None,
        model_used: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if processing_stage:
            details['processing_stage'] = processing_stage
        if audio_duration is not None:
            details['audio_duration'] = audio_duration
        if model_used:
            details['model_used'] = model_used
        
        recovery_suggestions = kwargs.get('recovery_suggestions', [
            "Try with a different model size",
            "Reduce audio quality or duration",
            "Check audio file integrity",
            "Retry with different configuration parameters"
        ])
        
        super().__init__(
            message=message,
            error_code=kwargs.get('error_code', 'PROCESSING_ERROR'),
            category=ErrorCategory.PROCESSING,
            severity=kwargs.get('severity', ErrorSeverity.MEDIUM),
            details=details,
            recovery_suggestions=recovery_suggestions,
            original_exception=kwargs.get('original_exception')
        )

class ModelLoadingError(ProcessingError):
    """Exception for model loading errors"""
    
    def __init__(
        self,
        message: str,
        model_name: Optional[str] = None,
        required_memory_mb: Optional[float] = None,
        available_memory_mb: Optional[float] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if model_name:
            details['model_name'] = model_name
        if required_memory_mb is not None:
            details['required_memory_mb'] = required_memory_mb
        if available_memory_mb is not None:
            details['available_memory_mb'] = available_memory_mb
        
        recovery_suggestions = kwargs.get('recovery_suggestions', [
            "Try using a smaller model size",
            "Free up system memory",
            "Clear model cache",
            "Use cloud-based processing instead of local models"
        ])
        
        super().__init__(
            message=message,
            error_code=kwargs.get('error_code', 'MODEL_LOADING_ERROR'),
            processing_stage="model_loading",
            details=details,
            recovery_suggestions=recovery_suggestions,
            **kwargs
        )

class TranscriptionTimeoutError(ProcessingError):
    """Exception for transcription timeout errors"""
    
    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[float] = None,
        elapsed_seconds: Optional[float] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if timeout_seconds is not None:
            details['timeout_seconds'] = timeout_seconds
        if elapsed_seconds is not None:
            details['elapsed_seconds'] = elapsed_seconds
        
        recovery_suggestions = kwargs.get('recovery_suggestions', [
            "Increase timeout duration",
            "Use a faster model (tiny or base)",
            "Split audio into smaller chunks",
            "Reduce audio quality or sample rate"
        ])
        
        super().__init__(
            message=message,
            error_code=kwargs.get('error_code', 'TRANSCRIPTION_TIMEOUT'),
            processing_stage="transcription",
            severity=ErrorSeverity.HIGH,
            details=details,
            recovery_suggestions=recovery_suggestions,
            **kwargs
        )

class ResourceError(WhisperAdvancedException):
    """Exception for resource-related errors"""
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        required_amount: Optional[float] = None,
        available_amount: Optional[float] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if resource_type:
            details['resource_type'] = resource_type
        if required_amount is not None:
            details['required_amount'] = required_amount
        if available_amount is not None:
            details['available_amount'] = available_amount
        
        recovery_suggestions = kwargs.get('recovery_suggestions', [
            "Free up system resources",
            "Use a less resource-intensive configuration",
            "Process files in smaller batches",
            "Upgrade system resources if possible"
        ])
        
        super().__init__(
            message=message,
            error_code=kwargs.get('error_code', 'RESOURCE_ERROR'),
            category=ErrorCategory.RESOURCE,
            severity=kwargs.get('severity', ErrorSeverity.HIGH),
            details=details,
            recovery_suggestions=recovery_suggestions,
            original_exception=kwargs.get('original_exception')
        )

class InsufficientMemoryError(ResourceError):
    """Exception for insufficient memory errors"""
    
    def __init__(
        self,
        message: str,
        required_memory_mb: Optional[float] = None,
        available_memory_mb: Optional[float] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            resource_type="memory",
            required_amount=required_memory_mb,
            available_amount=available_memory_mb,
            error_code=kwargs.get('error_code', 'INSUFFICIENT_MEMORY'),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Close other applications to free memory",
                "Use a smaller model size",
                "Process audio in smaller chunks",
                "Clear model cache",
                "Restart the application"
            ]),
            **kwargs
        )

class DiskSpaceError(ResourceError):
    """Exception for insufficient disk space errors"""
    
    def __init__(
        self,
        message: str,
        required_space_mb: Optional[float] = None,
        available_space_mb: Optional[float] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            resource_type="disk_space",
            required_amount=required_space_mb,
            available_amount=available_space_mb,
            error_code=kwargs.get('error_code', 'INSUFFICIENT_DISK_SPACE'),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Free up disk space",
                "Clean temporary files",
                "Move files to external storage",
                "Clear cache directories"
            ]),
            **kwargs
        )

class AuthenticationError(WhisperAdvancedException):
    """Exception for authentication and authorization errors"""
    
    def __init__(
        self,
        message: str,
        auth_type: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if auth_type:
            details['auth_type'] = auth_type
        
        recovery_suggestions = kwargs.get('recovery_suggestions', [
            "Check API key validity",
            "Verify authentication credentials",
            "Check account permissions and quotas",
            "Contact support if issue persists"
        ])
        
        super().__init__(
            message=message,
            error_code=kwargs.get('error_code', 'AUTHENTICATION_ERROR'),
            category=ErrorCategory.AUTHENTICATION,
            severity=kwargs.get('severity', ErrorSeverity.HIGH),
            details=details,
            recovery_suggestions=recovery_suggestions,
            original_exception=kwargs.get('original_exception')
        )

class APIKeyError(AuthenticationError):
    """Exception for API key errors"""
    
    def __init__(
        self,
        message: str,
        **kwargs
    ):
        super().__init__(
            message=message,
            auth_type="api_key",
            error_code=kwargs.get('error_code', 'INVALID_API_KEY'),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Check if API key is set correctly",
                "Verify API key is valid and not expired",
                "Check environment variables",
                "Generate a new API key if needed"
            ]),
            **kwargs
        )

class RateLimitError(AuthenticationError):
    """Exception for rate limit errors"""
    
    def __init__(
        self,
        message: str,
        requests_per_minute: Optional[int] = None,
        retry_after_seconds: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if requests_per_minute is not None:
            details['requests_per_minute'] = requests_per_minute
        if retry_after_seconds is not None:
            details['retry_after_seconds'] = retry_after_seconds
        
        recovery_suggestions = kwargs.get('recovery_suggestions', [
            f"Wait {retry_after_seconds} seconds before retrying" if retry_after_seconds else "Wait before retrying",
            "Reduce request frequency",
            "Implement exponential backoff",
            "Upgrade to higher rate limit plan if available"
        ])
        
        super().__init__(
            message=message,
            auth_type="rate_limit",
            error_code=kwargs.get('error_code', 'RATE_LIMIT_EXCEEDED'),
            details=details,
            recovery_suggestions=recovery_suggestions,
            **kwargs
        )

class NetworkError(WhisperAdvancedException):
    """Exception for network-related errors"""
    
    def __init__(
        self,
        message: str,
        endpoint: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if endpoint:
            details['endpoint'] = endpoint
        if status_code is not None:
            details['status_code'] = status_code
        
        recovery_suggestions = kwargs.get('recovery_suggestions', [
            "Check internet connection",
            "Verify API endpoint availability",
            "Retry request after a delay",
            "Check firewall and proxy settings"
        ])
        
        super().__init__(
            message=message,
            error_code=kwargs.get('error_code', 'NETWORK_ERROR'),
            category=ErrorCategory.NETWORK,
            severity=kwargs.get('severity', ErrorSeverity.MEDIUM),
            details=details,
            recovery_suggestions=recovery_suggestions,
            original_exception=kwargs.get('original_exception')
        )

class APIConnectionError(NetworkError):
    """Exception for API connection errors"""
    
    def __init__(
        self,
        message: str,
        api_endpoint: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            endpoint=api_endpoint,
            error_code=kwargs.get('error_code', 'API_CONNECTION_ERROR'),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Check internet connection",
                "Verify API service status",
                "Try again in a few moments",
                "Check for service outages"
            ]),
            **kwargs
        )

class APIResponseError(NetworkError):
    """Exception for API response errors"""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if response_body:
            details['response_body'] = response_body
        
        super().__init__(
            message=message,
            status_code=status_code,
            error_code=kwargs.get('error_code', 'API_RESPONSE_ERROR'),
            details=details,
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Check API request format",
                "Verify request parameters",
                "Check API documentation",
                "Contact API support if error persists"
            ]),
            **kwargs
        )

# Error recovery utilities
class ErrorRecoveryManager:
    """Manages error recovery strategies"""
    
    def __init__(self):
        self.recovery_strategies = {
            'MODEL_LOADING_ERROR': self._recover_model_loading,
            'TRANSCRIPTION_TIMEOUT': self._recover_transcription_timeout,
            'INSUFFICIENT_MEMORY': self._recover_insufficient_memory,
            'RATE_LIMIT_EXCEEDED': self._recover_rate_limit,
            'API_CONNECTION_ERROR': self._recover_api_connection
        }
    
    def suggest_recovery(self, exception: WhisperAdvancedException) -> Dict[str, Any]:
        """
        Suggest recovery strategy for an exception
        
        Args:
            exception: The exception to recover from
            
        Returns:
            Recovery strategy information
        """
        strategy_func = self.recovery_strategies.get(exception.error_code)
        
        if strategy_func:
            return strategy_func(exception)
        else:
            return {
                'strategy': 'generic',
                'actions': exception.recovery_suggestions,
                'automatic_recovery': False,
                'retry_recommended': True,
                'retry_delay_seconds': 5
            }
    
    def _recover_model_loading(self, exception: WhisperAdvancedException) -> Dict[str, Any]:
        """Recovery strategy for model loading errors"""
        return {
            'strategy': 'fallback_model',
            'actions': [
                'Try smaller model size',
                'Clear model cache',
                'Free system memory'
            ],
            'automatic_recovery': True,
            'fallback_model': 'tiny',
            'retry_recommended': True,
            'retry_delay_seconds': 2
        }
    
    def _recover_transcription_timeout(self, exception: WhisperAdvancedException) -> Dict[str, Any]:
        """Recovery strategy for transcription timeout"""
        return {
            'strategy': 'optimize_processing',
            'actions': [
                'Use faster model',
                'Split audio into chunks',
                'Reduce audio quality'
            ],
            'automatic_recovery': True,
            'recommended_model': 'base',
            'chunk_size_seconds': 300,
            'retry_recommended': True,
            'retry_delay_seconds': 1
        }
    
    def _recover_insufficient_memory(self, exception: WhisperAdvancedException) -> Dict[str, Any]:
        """Recovery strategy for insufficient memory"""
        return {
            'strategy': 'memory_optimization',
            'actions': [
                'Clear caches',
                'Use smaller model',
                'Process in smaller batches'
            ],
            'automatic_recovery': True,
            'clear_caches': True,
            'fallback_model': 'tiny',
            'batch_size': 1,
            'retry_recommended': True,
            'retry_delay_seconds': 3
        }
    
    def _recover_rate_limit(self, exception: WhisperAdvancedException) -> Dict[str, Any]:
        """Recovery strategy for rate limit errors"""
        retry_after = exception.details.get('retry_after_seconds', 60)
        
        return {
            'strategy': 'exponential_backoff',
            'actions': [
                f'Wait {retry_after} seconds',
                'Implement request queuing',
                'Reduce request frequency'
            ],
            'automatic_recovery': True,
            'retry_recommended': True,
            'retry_delay_seconds': retry_after,
            'exponential_backoff': True,
            'max_retries': 3
        }
    
    def _recover_api_connection(self, exception: WhisperAdvancedException) -> Dict[str, Any]:
        """Recovery strategy for API connection errors"""
        return {
            'strategy': 'connection_retry',
            'actions': [
                'Check internet connection',
                'Retry with exponential backoff',
                'Verify API endpoint status'
            ],
            'automatic_recovery': True,
            'retry_recommended': True,
            'retry_delay_seconds': 5,
            'exponential_backoff': True,
            'max_retries': 5
        }

# Utility functions for error handling
def handle_exception(func):
    """Decorator for consistent exception handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except WhisperAdvancedException:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Convert generic exceptions to our custom format
            raise ProcessingError(
                message=f"Unexpected error in {func.__name__}: {str(e)}",
                error_code="UNEXPECTED_ERROR",
                processing_stage=func.__name__,
                severity=ErrorSeverity.HIGH,
                original_exception=e
            )
    return wrapper

def create_error_response(exception: WhisperAdvancedException) -> Dict[str, Any]:
    """Create standardized error response for API"""
    recovery_manager = ErrorRecoveryManager()
    recovery_info = recovery_manager.suggest_recovery(exception)
    
    response = exception.to_dict()
    response['recovery'] = recovery_info
    response['timestamp'] = logger.handlers[0].formatter.formatTime(
        logger.makeRecord(
            name=logger.name,
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="",
            args=(),
            exc_info=None
        )
    ) if logger.handlers else None
    
    return response

# Example usage and testing
if __name__ == "__main__":
    # Example of using custom exceptions
    try:
        raise AudioFileError(
            message="Audio file format not supported",
            file_path="/path/to/audio.xyz",
            file_format="xyz",
            expected_format="mp3, wav, m4a"
        )
    except WhisperAdvancedException as e:
        print("Exception details:")
        print(f"Message: {e.message}")
        print(f"Error Code: {e.error_code}")
        print(f"Category: {e.category.value}")
        print(f"Severity: {e.severity.value}")
        print(f"Recovery Suggestions: {e.recovery_suggestions}")
        
        # Create error response
        error_response = create_error_response(e)
        print(f"API Response: {error_response}")