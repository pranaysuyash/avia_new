"""
Core service exceptions
"""

from typing import Optional, Dict, Any


class ServiceError(Exception):
    """Base service error"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__.upper()
        self.details = details or {}
        super().__init__(message)


class ValidationError(ServiceError):
    """Request validation error"""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if field:
            error_details["field"] = field
        
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=error_details
        )


class AuthenticationError(ServiceError):
    """Authentication error"""
    
    def __init__(self, message: str = "Authentication required", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
            details=details
        )


class AuthorizationError(ServiceError):
    """Authorization error"""
    
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR",
            details=details
        )


class NotFoundError(ServiceError):
    """Resource not found error"""
    
    def __init__(self, resource: str, resource_id: Any):
        super().__init__(
            message=f"{resource} not found",
            status_code=404,
            error_code="NOT_FOUND",
            details={"resource": resource, "id": str(resource_id)}
        )


class ConflictError(ServiceError):
    """Resource conflict error"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
            details=details
        )


class RateLimitError(ServiceError):
    """Rate limit exceeded error"""
    
    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Rate limit exceeded",
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after}
        )


class ServiceUnavailableError(ServiceError):
    """Service unavailable error"""
    
    def __init__(self, message: str = "Service temporarily unavailable", retry_after: Optional[int] = None):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            status_code=503,
            error_code="SERVICE_UNAVAILABLE",
            details=details
        )


class TimeoutError(ServiceError):
    """Request timeout error"""
    
    def __init__(self, timeout: int):
        super().__init__(
            message=f"Request timeout after {timeout}s",
            status_code=408,
            error_code="TIMEOUT",
            details={"timeout": timeout}
        )