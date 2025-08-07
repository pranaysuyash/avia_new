"""
Sentry Configuration for Python Backend
Handles error tracking and performance monitoring for FastAPI
"""

import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
import logging


def init_sentry(app_name: str = "media-analysis-api"):
    """Initialize Sentry for the Python backend"""
    
    # Get configuration from environment
    dsn = os.getenv("SENTRY_DSN")
    environment = os.getenv("SENTRY_ENVIRONMENT", "development")
    release = os.getenv("SENTRY_RELEASE", f"{app_name}@1.0.0")
    
    if not dsn:
        logging.warning("Sentry DSN not configured, skipping initialization")
        return
    
    # Configure integrations
    integrations = [
        # FastAPI integration
        FastApiIntegration(
            transaction_style="endpoint",
            failed_request_status_codes={400, 401, 403, 404, 405, 500, 502, 503, 504},
        ),
        
        # SQLAlchemy integration
        SqlalchemyIntegration(),
        
        # Redis integration
        RedisIntegration(),
        
        # Asyncio integration
        AsyncioIntegration(),
        
        # Logging integration
        LoggingIntegration(
            level=logging.INFO,  # Capture info and above as breadcrumbs
            event_level=logging.ERROR  # Send errors as events
        ),
    ]
    
    # Initialize Sentry
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=release,
        integrations=integrations,
        
        # Performance monitoring
        traces_sample_rate=0.1 if environment == "production" else 1.0,
        profiles_sample_rate=0.1 if environment == "production" else 1.0,
        
        # Session tracking
        release_health=True,
        
        # Error filtering
        ignore_errors=[
            # Client errors
            "CancelledError",
            "ConnectionError",
            "BrokenPipeError",
            
            # Expected errors
            "HTTPException",
            "ValidationError",
        ],
        
        # Data scrubbing
        before_send=before_send_filter,
        
        # Request data
        request_bodies="medium",
        with_locals=False,  # Don't capture local variables in production
        
        # Performance
        max_breadcrumbs=50,
        attach_stacktrace=True,
    )


def before_send_filter(event, hint):
    """Filter and sanitize events before sending to Sentry"""
    
    # Remove sensitive headers
    if "request" in event and "headers" in event["request"]:
        sensitive_headers = ["authorization", "cookie", "x-api-key", "x-auth-token"]
        for header in sensitive_headers:
            if header in event["request"]["headers"]:
                event["request"]["headers"][header] = "[FILTERED]"
    
    # Remove sensitive data from request body
    if "request" in event and "data" in event["request"]:
        if isinstance(event["request"]["data"], dict):
            sensitive_fields = ["password", "token", "secret", "api_key", "credit_card"]
            for field in sensitive_fields:
                if field in event["request"]["data"]:
                    event["request"]["data"][field] = "[FILTERED]"
    
    # Filter out non-actionable errors
    if "exception" in event:
        exception = hint.get("exc_info")
        if exception:
            error_type = type(exception[1]).__name__
            
            # Skip client disconnection errors
            if error_type in ["ConnectionResetError", "BrokenPipeError"]:
                return None
            
            # Skip expected validation errors
            if error_type == "ValidationError" and hasattr(exception[1], "status_code"):
                if exception[1].status_code < 500:
                    return None
    
    return event


def capture_exception(error: Exception, **kwargs):
    """Capture exception with additional context"""
    with sentry_sdk.push_scope() as scope:
        # Add custom context
        for key, value in kwargs.items():
            scope.set_extra(key, value)
        
        # Capture the exception
        sentry_sdk.capture_exception(error)


def capture_message(message: str, level: str = "info", **kwargs):
    """Capture a message with additional context"""
    with sentry_sdk.push_scope() as scope:
        # Add custom context
        for key, value in kwargs.items():
            scope.set_extra(key, value)
        
        # Capture the message
        sentry_sdk.capture_message(message, level=level)


def set_user_context(user_id: str, email: str = None, username: str = None, **kwargs):
    """Set user context for Sentry"""
    user_data = {
        "id": user_id,
        "email": email,
        "username": username,
    }
    user_data.update(kwargs)
    
    sentry_sdk.set_user(user_data)


def add_breadcrumb(message: str, category: str, level: str = "info", data: dict = None):
    """Add a breadcrumb for better error context"""
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {},
    )


def start_transaction(name: str, op: str = "http.server"):
    """Start a performance transaction"""
    return sentry_sdk.start_transaction(op=op, name=name)


# Middleware for FastAPI
async def sentry_middleware(request, call_next):
    """Middleware to capture request context"""
    # Set transaction name
    transaction = sentry_sdk.Hub.current.scope.transaction
    if transaction:
        transaction.name = f"{request.method} {request.url.path}"
    
    # Add request context
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("http.method", request.method)
        scope.set_tag("http.path", request.url.path)
        scope.set_tag("http.host", request.headers.get("host", "unknown"))
        
        # Add user context if available
        if hasattr(request.state, "user") and request.state.user:
            set_user_context(
                user_id=str(request.state.user.id),
                email=request.state.user.email,
                subscription_tier=request.state.user.subscription_tier,
            )
    
    # Process request
    response = await call_next(request)
    
    # Add response context
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("http.status_code", response.status_code)
    
    return response