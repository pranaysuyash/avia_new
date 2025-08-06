"""
Exception classes for the Transcription API Python SDK
"""


class TranscriptionAPIError(Exception):
    """Base exception for all API errors"""
    
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}
    
    def __str__(self):
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(TranscriptionAPIError):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationError(TranscriptionAPIError):
    """Raised when user doesn't have permission for the requested action"""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status_code=403)


class ValidationError(TranscriptionAPIError):
    """Raised when request validation fails"""
    
    def __init__(self, message: str = "Validation error", errors: list = None):
        super().__init__(message, status_code=400)
        self.errors = errors or []


class NotFoundError(TranscriptionAPIError):
    """Raised when a resource is not found"""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class RateLimitError(TranscriptionAPIError):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class QuotaExceededError(TranscriptionAPIError):
    """Raised when usage quota is exceeded"""
    
    def __init__(self, message: str = "Usage quota exceeded"):
        super().__init__(message, status_code=402)


class ServerError(TranscriptionAPIError):
    """Raised when server returns 5xx error"""
    
    def __init__(self, message: str = "Internal server error", status_code: int = 500):
        super().__init__(message, status_code=status_code)


class TimeoutError(TranscriptionAPIError):
    """Raised when request times out"""
    
    def __init__(self, message: str = "Request timed out"):
        super().__init__(message)


class ConnectionError(TranscriptionAPIError):
    """Raised when connection to API fails"""
    
    def __init__(self, message: str = "Connection failed"):
        super().__init__(message)


class FileError(TranscriptionAPIError):
    """Raised when there's an issue with file handling"""
    
    def __init__(self, message: str = "File error"):
        super().__init__(message)


class UnsupportedFileTypeError(FileError):
    """Raised when file type is not supported"""
    
    def __init__(self, file_type: str = None):
        message = f"Unsupported file type: {file_type}" if file_type else "Unsupported file type"
        super().__init__(message)


class FileSizeError(FileError):
    """Raised when file is too large"""
    
    def __init__(self, size: int = None, max_size: int = None):
        if size and max_size:
            message = f"File size {size} bytes exceeds maximum {max_size} bytes"
        else:
            message = "File too large"
        super().__init__(message)


class TranscriptionError(TranscriptionAPIError):
    """Raised when transcription processing fails"""
    
    def __init__(self, message: str = "Transcription failed", transcript_id: str = None):
        super().__init__(message)
        self.transcript_id = transcript_id


class AnalysisError(TranscriptionAPIError):
    """Raised when content analysis fails"""
    
    def __init__(self, message: str = "Analysis failed", transcript_id: str = None):
        super().__init__(message)
        self.transcript_id = transcript_id


class WebhookError(TranscriptionAPIError):
    """Raised when webhook operations fail"""
    
    def __init__(self, message: str = "Webhook error"):
        super().__init__(message)


class TeamError(TranscriptionAPIError):
    """Raised when team operations fail"""
    
    def __init__(self, message: str = "Team operation failed"):
        super().__init__(message)


class ConfigurationError(TranscriptionAPIError):
    """Raised when SDK configuration is invalid"""
    
    def __init__(self, message: str = "Configuration error"):
        super().__init__(message)