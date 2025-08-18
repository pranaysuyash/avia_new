"""Correlation ID management for distributed tracing."""

import uuid
import contextvars
from typing import Optional
import logging

# Context variable to store correlation ID across async calls
correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    'correlation_id', default=None
)

logger = logging.getLogger(__name__)


def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid.uuid4())


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID from context."""
    return correlation_id_var.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID in context."""
    correlation_id_var.set(correlation_id)


class CorrelationIDMiddleware:
    """Middleware to handle correlation IDs in requests."""
    
    def __init__(self, app, header_name: str = "X-Correlation-ID"):
        self.app = app
        self.header_name = header_name
        
    async def __call__(self, scope, receive, send):
        """ASGI middleware implementation."""
        if scope["type"] == "http":
            # Extract correlation ID from headers or generate new one
            headers = dict(scope.get("headers", []))
            correlation_id = headers.get(self.header_name.lower().encode())
            
            if correlation_id:
                correlation_id = correlation_id.decode()
            else:
                correlation_id = generate_correlation_id()
                
            # Set correlation ID in context
            set_correlation_id(correlation_id)
            
            # Add correlation ID to response headers
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    headers.append([
                        self.header_name.encode(),
                        correlation_id.encode()
                    ])
                    message["headers"] = headers
                await send(message)
                
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)


class CorrelationIDFilter(logging.Filter):
    """Logging filter to add correlation ID to log records."""
    
    def filter(self, record):
        """Add correlation ID to log record."""
        correlation_id = get_correlation_id()
        record.correlation_id = correlation_id or "N/A"
        return True