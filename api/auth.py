"""
API Authentication and Authorization
Handles JWT tokens, API keys, and permission validation
"""

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import os
import sys
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security_manager import SecurityManager

logger = logging.getLogger(__name__)

# Security schemes
security_scheme = HTTPBearer()

# Global security manager
security_manager = SecurityManager()


class APIAuthManager:
    """Manage API authentication and authorization"""
    
    def __init__(self):
        self.security_manager = security_manager
    
    def validate_jwt_token(self, token: str) -> Optional[str]:
        """Validate JWT token and return user ID"""
        try:
            user_id = self.security_manager.access_control.validate_token(token)
            if user_id:
                # Log successful authentication
                self.security_manager.audit_logger.log_authentication(
                    user_id, True, "API"
                )
                return user_id
            else:
                return None
        except Exception as e:
            logger.error(f"JWT validation error: {e}")
            return None
    
    def validate_api_key(self, api_key: str) -> Optional[str]:
        """Validate API key and return user ID"""
        try:
            user_id = self.security_manager.access_control.validate_api_key(api_key)
            if user_id:
                # Log successful API key authentication
                self.security_manager.audit_logger.log_authentication(
                    user_id, True, "API_KEY"
                )
                return user_id
            else:
                return None
        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return None
    
    def check_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has required permission"""
        has_permission = self.security_manager.access_control.check_permission(
            user_id, permission
        )
        
        # Log access attempt
        self.security_manager.audit_logger.log_access_attempt(
            user_id, "API", permission, has_permission
        )
        
        return has_permission
    
    def check_rate_limit(self, user_id: str) -> bool:
        """Check if user is within rate limits"""
        return self.security_manager.access_control.check_rate_limit(user_id)


# Global auth manager
auth_manager = APIAuthManager()


async def get_current_user_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> str:
    """Get current user from JWT token"""
    token = credentials.credentials
    user_id = auth_manager.validate_jwt_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


async def get_current_user_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> str:
    """Get current user from API key"""
    if not credentials.scheme == "ApiKey":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme. Use 'ApiKey <key>'",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    api_key = credentials.credentials
    user_id = auth_manager.validate_api_key(api_key)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return user_id


async def get_current_user_flexible(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> str:
    """Get current user from either JWT token or API key"""
    if credentials.scheme.lower() == "bearer":
        # Try JWT token
        user_id = auth_manager.validate_jwt_token(credentials.credentials)
        if user_id:
            return user_id
    elif credentials.scheme.lower() == "apikey":
        # Try API key
        user_id = auth_manager.validate_api_key(credentials.credentials)
        if user_id:
            return user_id
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer, ApiKey"},
    )


def require_permission(permission: str):
    """Decorator to require specific permission"""
    def permission_checker(user_id: str = Depends(get_current_user_flexible)):
        if not auth_manager.check_permission(user_id, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return user_id
    return permission_checker


def require_admin():
    """Require admin permission"""
    return require_permission("admin")


def require_write():
    """Require write permission"""
    return require_permission("write")


def require_read():
    """Require read permission"""
    return require_permission("read")


def require_export():
    """Require export permission"""
    return require_permission("export")


# Convenience dependency functions (return callable functions for FastAPI Depends)
def jwt_required():
    return Depends(get_current_user_jwt)

def api_key_required():
    return Depends(get_current_user_api_key)

def auth_required():
    return Depends(get_current_user_flexible)

def admin_required():
    return require_admin()

def write_required():
    return require_write()

def read_required():
    return require_read()

def export_required():
    return require_export()


def create_api_response(data: Any, message: str = "Success") -> Dict[str, Any]:
    """Create standardized API response"""
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }


def create_error_response(error: str, status_code: int = 400) -> Dict[str, Any]:
    """Create standardized error response"""
    return {
        "success": False,
        "error": error,
        "status_code": status_code,
        "timestamp": datetime.now().isoformat()
    }


# Export the security_manager and auth_manager for use in endpoints
__all__ = [
    'auth_manager',
    'security_manager',
    'jwt_required',
    'api_key_required',
    'auth_required',
    'admin_required',
    'write_required',
    'read_required',
    'export_required',
    'create_api_response',
    'create_error_response'
]