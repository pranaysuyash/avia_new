"""
Monitoring middleware for FastAPI
Provides request logging, metrics collection, and error tracking
"""

import time
import json
from typing import Callable, Optional, Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import traceback

from monitoring.logger_config import get_logger, set_correlation_id, get_correlation_id
from monitoring.metrics_collector import app_metrics

logger = get_logger(__name__)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive request monitoring
    - Request/response logging
    - Performance metrics
    - Error tracking
    - Correlation ID management
    """
    
    def __init__(
        self,
        app: ASGIApp,
        skip_paths: Optional[list] = None,
        log_request_body: bool = False,
        log_response_body: bool = False,
        max_body_log_size: int = 1024
    ):
        super().__init__(app)
        self.skip_paths = skip_paths or ['/health', '/metrics', '/docs', '/openapi.json']
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_log_size = max_body_log_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with monitoring"""
        # Skip monitoring for certain paths
        if any(request.url.path.startswith(path) for path in self.skip_paths):
            return await call_next(request)
        
        # Set correlation ID
        correlation_id = request.headers.get('X-Correlation-ID')
        if not correlation_id:
            correlation_id = set_correlation_id()
        else:
            set_correlation_id(correlation_id)
        
        # Start timing
        start_time = time.time()
        
        # Extract request info
        request_info = {
            'method': request.method,
            'path': request.url.path,
            'query_params': str(request.query_params),
            'client': request.client.host if request.client else 'unknown',
            'user_agent': request.headers.get('User-Agent', 'unknown'),
            'correlation_id': correlation_id
        }
        
        # Get user info if available
        user_id = None
        if hasattr(request.state, 'user'):
            user_id = getattr(request.state.user, 'id', None)
            request_info['user_id'] = user_id
        
        # Log request body if enabled
        if self.log_request_body and request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = await request.body()
                if body:
                    body_str = body.decode('utf-8')
                    if len(body_str) <= self.max_body_log_size:
                        try:
                            request_info['body'] = json.loads(body_str)
                        except json.JSONDecodeError:
                            request_info['body'] = body_str[:self.max_body_log_size]
                    else:
                        request_info['body_truncated'] = True
                        request_info['body_size'] = len(body_str)
                    
                    # Restore body for the actual handler
                    async def receive():
                        return {'type': 'http.request', 'body': body}
                    request._receive = receive
            except Exception as e:
                logger.warning(f"Failed to log request body: {e}")
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                'request_id': correlation_id,
                'method': request.method,
                'path': request.url.path,
                'user_id': user_id,
                **request_info
            }
        )
        
        # Process request
        response = None
        error_occurred = False
        error_details = None
        
        try:
            response = await call_next(request)
            
            # Log response body if enabled
            if self.log_response_body and response.status_code >= 400:
                if hasattr(response, 'body'):
                    try:
                        body = response.body
                        if isinstance(body, bytes):
                            body = body.decode('utf-8')
                        if len(body) <= self.max_body_log_size:
                            try:
                                response_data = json.loads(body)
                                logger.error(
                                    f"Error response body",
                                    extra={
                                        'response_body': response_data,
                                        'status_code': response.status_code,
                                        'correlation_id': correlation_id
                                    }
                                )
                            except json.JSONDecodeError:
                                pass
                    except Exception:
                        pass
            
        except Exception as e:
            error_occurred = True
            error_details = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'traceback': traceback.format_exc()
            }
            
            # Log error
            logger.exception(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    'request_id': correlation_id,
                    'method': request.method,
                    'path': request.url.path,
                    'user_id': user_id,
                    **error_details
                }
            )
            
            # Create error response
            response = JSONResponse(
                status_code=500,
                content={
                    'error': 'Internal Server Error',
                    'correlation_id': correlation_id,
                    'message': 'An unexpected error occurred'
                }
            )
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Add correlation ID to response headers
        response.headers['X-Correlation-ID'] = correlation_id
        
        # Log response
        logger.info(
            f"Response: {response.status_code} for {request.method} {request.url.path} ({duration_ms:.2f}ms)",
            extra={
                'request_id': correlation_id,
                'method': request.method,
                'path': request.url.path,
                'status_code': response.status_code,
                'duration_ms': duration_ms,
                'user_id': user_id,
                'error_occurred': error_occurred
            }
        )
        
        # Record metrics
        app_metrics.track_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms
        )
        
        return response


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """
    Specialized middleware for error logging and tracking
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with error tracking"""
        try:
            response = await call_next(request)
            
            # Log client errors (4xx)
            if 400 <= response.status_code < 500:
                logger.warning(
                    f"Client error: {response.status_code} {request.method} {request.url.path}",
                    extra={
                        'status_code': response.status_code,
                        'method': request.method,
                        'path': request.url.path,
                        'client': request.client.host if request.client else 'unknown',
                        'correlation_id': get_correlation_id()
                    }
                )
            
            # Log server errors (5xx)
            elif response.status_code >= 500:
                logger.error(
                    f"Server error: {response.status_code} {request.method} {request.url.path}",
                    extra={
                        'status_code': response.status_code,
                        'method': request.method,
                        'path': request.url.path,
                        'correlation_id': get_correlation_id()
                    }
                )
            
            return response
            
        except Exception as e:
            # Log unexpected errors
            logger.exception(
                f"Unhandled exception in {request.method} {request.url.path}",
                extra={
                    'method': request.method,
                    'path': request.url.path,
                    'error_type': type(e).__name__,
                    'correlation_id': get_correlation_id()
                }
            )
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    'error': 'Internal Server Error',
                    'correlation_id': get_correlation_id()
                }
            )


class SlowRequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log slow requests
    """
    
    def __init__(self, app: ASGIApp, threshold_ms: float = 1000):
        super().__init__(app)
        self.threshold_ms = threshold_ms
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log if slow"""
        start_time = time.time()
        
        response = await call_next(request)
        
        duration_ms = (time.time() - start_time) * 1000
        
        if duration_ms > self.threshold_ms:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} took {duration_ms:.2f}ms",
                extra={
                    'method': request.method,
                    'path': request.url.path,
                    'duration_ms': duration_ms,
                    'threshold_ms': self.threshold_ms,
                    'correlation_id': get_correlation_id()
                }
            )
        
        return response


class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for security-related logging
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with security logging"""
        # Log authentication attempts
        if request.url.path in ['/api/auth/login', '/api/auth/register']:
            client_ip = request.client.host if request.client else 'unknown'
            
            response = await call_next(request)
            
            # Log result
            if request.url.path == '/api/auth/login':
                success = response.status_code == 200
                logger.info(
                    f"Authentication attempt: {'success' if success else 'failed'}",
                    extra={
                        'event_type': 'auth_attempt',
                        'success': success,
                        'client_ip': client_ip,
                        'user_agent': request.headers.get('User-Agent', 'unknown'),
                        'correlation_id': get_correlation_id()
                    }
                )
                
                # Log repeated failures
                if not success:
                    # In production, track failed attempts per IP
                    pass
            
            return response
        
        # Log access to sensitive endpoints
        sensitive_paths = ['/api/admin', '/api/settings', '/api/users']
        if any(request.url.path.startswith(path) for path in sensitive_paths):
            logger.info(
                f"Access to sensitive endpoint: {request.url.path}",
                extra={
                    'event_type': 'sensitive_access',
                    'path': request.url.path,
                    'method': request.method,
                    'user_id': getattr(request.state, 'user_id', None),
                    'correlation_id': get_correlation_id()
                }
            )
        
        return await call_next(request)