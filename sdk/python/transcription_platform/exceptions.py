#!/usr/bin/env python3
"""
Transcription Platform Exceptions
Custom exceptions for the SDK
"""

class TranscriptionError(Exception):
    """Base exception for all SDK errors"""
    pass

class AuthenticationError(TranscriptionError):
    """Raised when authentication fails"""
    pass

class RateLimitError(TranscriptionError):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, message: str, retry_after: int = None, reset_time: int = None):
        super().__init__(message)
        self.retry_after = retry_after
        self.reset_time = reset_time

class ValidationError(TranscriptionError):
    """Raised when request validation fails"""
    pass

class NotFoundError(TranscriptionError):
    """Raised when a resource is not found"""
    pass

class ServerError(TranscriptionError):
    """Raised when the server returns a 5xx error"""
    pass