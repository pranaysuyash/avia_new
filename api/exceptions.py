"""
Custom exceptions for the API
"""

from typing import Optional, Dict, Any


class APIException(Exception):
    """Base API exception"""
    
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(APIException):
    """Authentication failed"""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
            message=message,
            details=details
        )


class AuthorizationError(APIException):
    """Authorization failed"""
    
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=403,
            error_code="AUTHORIZATION_ERROR",
            message=message,
            details=details
        )


class NotFoundError(APIException):
    """Resource not found"""
    
    def __init__(self, resource: str, resource_id: Any):
        super().__init__(
            status_code=404,
            error_code="NOT_FOUND",
            message=f"{resource} not found",
            details={"resource": resource, "id": str(resource_id)}
        )


class ValidationError(APIException):
    """Validation error"""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if field:
            error_details["field"] = field
        
        super().__init__(
            status_code=422,
            error_code="VALIDATION_ERROR",
            message=message,
            details=error_details
        )


class ConflictError(APIException):
    """Resource conflict"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=409,
            error_code="CONFLICT",
            message=message,
            details=details
        )


class RateLimitError(APIException):
    """Rate limit exceeded"""
    
    def __init__(self, retry_after: int):
        super().__init__(
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            message="Rate limit exceeded",
            details={"retry_after": retry_after}
        )


class ServerError(APIException):
    """Internal server error"""
    
    def __init__(self, message: str = "Internal server error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=500,
            error_code="INTERNAL_ERROR",
            message=message,
            details=details
        )


class ServiceUnavailableError(APIException):
    """Service unavailable"""
    
    def __init__(self, message: str = "Service temporarily unavailable", retry_after: Optional[int] = None):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        
        super().__init__(
            status_code=503,
            error_code="SERVICE_UNAVAILABLE",
            message=message,
            details=details
        )