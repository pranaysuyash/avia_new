#!/usr/bin/env python3
"""
Audit Middleware
Automatically logs API requests for audit trail
"""

import logging
import time
import json
from typing import Optional, Dict, Any, Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message

from services.audit_logging_service import audit_service, AuditEventType

logger = logging.getLogger(__name__)

# Endpoints that should be audited
AUDIT_ENDPOINTS = {
    # Authentication
    '/api/auth/login': AuditEventType.LOGIN,
    '/api/auth/logout': AuditEventType.LOGOUT,
    '/api/auth/register': AuditEventType.USER_CREATE,
    '/api/auth/change-password': AuditEventType.PASSWORD_CHANGE,
    '/api/auth/reset-password': AuditEventType.PASSWORD_RESET,
    
    # Transcripts
    '/api/transcripts': AuditEventType.TRANSCRIPT_CREATE,
    '/api/transcripts/update': AuditEventType.TRANSCRIPT_UPDATE,
    '/api/transcripts/delete': AuditEventType.TRANSCRIPT_DELETE,
    '/api/transcripts/share': AuditEventType.TRANSCRIPT_SHARE,
    
    # Data export
    '/api/export': AuditEventType.DATA_EXPORT,
    '/api/transcripts/export': AuditEventType.DATA_EXPORT,
    '/api/audit/logs/export': AuditEventType.DATA_EXPORT,
    
    # User management
    '/api/admin/users': AuditEventType.USER_CREATE,
    '/api/admin/users/update': AuditEventType.USER_UPDATE,
    '/api/admin/users/delete': AuditEventType.USER_DELETE,
    '/api/admin/users/suspend': AuditEventType.USER_SUSPEND,
    
    # System
    '/api/admin/backup': AuditEventType.BACKUP_CREATE,
    '/api/admin/backup/restore': AuditEventType.BACKUP_RESTORE,
    '/api/admin/system/config': AuditEventType.CONFIG_CHANGE,
}

# Endpoints to skip audit logging
SKIP_AUDIT = {
    '/api/health',
    '/api/v1/health',
    '/docs',
    '/redoc',
    '/openapi.json',
    '/api/audit/logs',  # Prevent recursive logging
}

class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically audit API requests"""
    
    def __init__(self, app, skip_paths: Optional[set] = None):
        super().__init__(app)
        self.skip_paths = skip_paths or SKIP_AUDIT
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log audit event"""
        # Skip if path should not be audited
        if any(request.url.path.startswith(skip) for skip in self.skip_paths):
            return await call_next(request)
        
        # Skip WebSocket requests
        if request.url.path.startswith('/api/ws/'):
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        # Get request details
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get('user-agent', '')
        request_id = request.headers.get('x-request-id', '')
        
        # Get user info from request state
        user_id = None
        username = None
        if hasattr(request.state, 'user'):
            user_id = request.state.user.id
            username = request.state.user.username
        
        # Capture request body for certain endpoints
        request_body = None
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = await request.body()
                request._body = body  # Store for later use
                if len(body) < 10000:  # Only log small bodies
                    request_body = json.loads(body) if body else None
            except Exception:
                pass
        
        # Process request
        response = None
        error_message = None
        
        try:
            response = await call_next(request)
            
            # Log audit event if this is an auditable endpoint
            if response.status_code < 400:
                await self._log_success(
                    request=request,
                    response=response,
                    user_id=user_id,
                    username=username,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    request_id=request_id,
                    duration=time.time() - start_time,
                    request_body=request_body
                )
            else:
                await self._log_failure(
                    request=request,
                    response=response,
                    user_id=user_id,
                    username=username,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    request_id=request_id,
                    duration=time.time() - start_time,
                    request_body=request_body
                )
            
            return response
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Request failed: {error_message}")
            
            # Log error
            audit_service.log_event(
                event_type=AuditEventType.API_ERROR,
                action=f"{request.method} {request.url.path}",
                result="error",
                user_id=user_id,
                username=username,
                ip_address=client_ip,
                user_agent=user_agent,
                error_message=error_message,
                request_id=request_id
            )
            
            raise
    
    async def _log_success(
        self,
        request: Request,
        response: Response,
        user_id: Optional[int],
        username: Optional[str],
        ip_address: Optional[str],
        user_agent: str,
        request_id: str,
        duration: float,
        request_body: Optional[Dict]
    ):
        """Log successful request"""
        # Determine event type
        path = request.url.path
        method = request.method
        
        # Check for specific audit events
        event_type = None
        for endpoint, etype in AUDIT_ENDPOINTS.items():
            if path.startswith(endpoint) and method in ['POST', 'PUT', 'DELETE']:
                event_type = etype
                break
        
        # Only log if we have a specific event type
        if event_type:
            # Extract resource info from path
            resource_type, resource_id = self._extract_resource_info(path)
            
            # Build details
            details = {
                'method': method,
                'path': path,
                'duration_ms': int(duration * 1000),
                'status_code': response.status_code
            }
            
            # Add relevant request body fields
            if request_body and event_type in [
                AuditEventType.TRANSCRIPT_CREATE,
                AuditEventType.CONFIG_CHANGE
            ]:
                # Only include non-sensitive fields
                safe_fields = ['title', 'description', 'language', 'category']
                details['request'] = {
                    k: v for k, v in request_body.items()
                    if k in safe_fields
                }
            
            audit_service.log_event(
                event_type=event_type,
                action=f"{method} {path}",
                result="success",
                user_id=user_id,
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                request_id=request_id
            )
    
    async def _log_failure(
        self,
        request: Request,
        response: Response,
        user_id: Optional[int],
        username: Optional[str],
        ip_address: Optional[str],
        user_agent: str,
        request_id: str,
        duration: float,
        request_body: Optional[Dict]
    ):
        """Log failed request"""
        path = request.url.path
        method = request.method
        
        # Special handling for failed logins
        if path == '/api/auth/login' and response.status_code == 401:
            # Extract username from request body
            if request_body and 'username' in request_body:
                username = request_body['username']
            
            audit_service.log_event(
                event_type=AuditEventType.LOGIN_FAILED,
                action="Login attempt",
                result="failure",
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                details={
                    'status_code': response.status_code,
                    'duration_ms': int(duration * 1000)
                },
                request_id=request_id
            )
        
        # Log other failures for auditable endpoints
        elif any(path.startswith(endpoint) for endpoint in AUDIT_ENDPOINTS):
            resource_type, resource_id = self._extract_resource_info(path)
            
            audit_service.log_event(
                event_type=AuditEventType.API_ERROR,
                action=f"{method} {path}",
                result="failure",
                user_id=user_id,
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                resource_type=resource_type,
                resource_id=resource_id,
                details={
                    'status_code': response.status_code,
                    'duration_ms': int(duration * 1000)
                },
                request_id=request_id
            )
    
    def _extract_resource_info(self, path: str) -> tuple[Optional[str], Optional[str]]:
        """Extract resource type and ID from path"""
        parts = path.strip('/').split('/')
        
        # Common patterns
        if 'transcripts' in parts:
            idx = parts.index('transcripts')
            if idx + 1 < len(parts) and parts[idx + 1].isdigit():
                return 'transcript', parts[idx + 1]
            return 'transcript', None
        
        elif 'users' in parts:
            idx = parts.index('users')
            if idx + 1 < len(parts) and parts[idx + 1].isdigit():
                return 'user', parts[idx + 1]
            return 'user', None
        
        elif 'teams' in parts:
            idx = parts.index('teams')
            if idx + 1 < len(parts) and parts[idx + 1].isdigit():
                return 'team', parts[idx + 1]
            return 'team', None
        
        return None, None