"""
Core API infrastructure components
"""

try:
    from .base_service import BaseService, ServiceConfig, ServiceRequest, ServiceResponse
    from .api_gateway import APIGateway
    from .middleware import (
        AuthenticationMiddleware,
        ValidationMiddleware,
        ErrorHandlingMiddleware,
        MetricsMiddleware,
        RateLimitingMiddleware
    )
    from .health import HealthChecker, HealthStatus
    from .logging import setup_logging, get_logger
    from .metrics import MetricsCollector
    from .openapi import setup_openapi_docs
    from .exceptions import ServiceError, ValidationError, AuthenticationError
    
    __all__ = [
        "BaseService",
        "ServiceConfig",
        "ServiceRequest", 
        "ServiceResponse",
        "APIGateway",
        "AuthenticationMiddleware",
        "ValidationMiddleware",
        "ErrorHandlingMiddleware",
        "MetricsMiddleware",
        "RateLimitingMiddleware",
        "HealthChecker",
        "HealthStatus",
        "setup_logging",
        "get_logger",
        "MetricsCollector",
        "setup_openapi_docs",
        "ServiceError",
        "ValidationError",
        "AuthenticationError"
    ]
    
except ImportError as e:
    print(f"Warning: Could not import all core components: {e}")
    # Provide minimal exports for testing
    __all__ = []