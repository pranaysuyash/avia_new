"""
JWT Authentication Middleware for FastAPI
Provides authentication dependencies and middleware for protecting API endpoints
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from typing import Optional, Dict, Any
import logging

from .auth_service import jwt_auth_service

logger = logging.getLogger(__name__)

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    api_key: Optional[str] = Depends(api_key_header)
) -> Dict[str, Any]:
    """
    Validate authentication credentials and return current user info
    Supports both JWT tokens and API keys
    """
    # Try JWT token first
    if credentials and credentials.credentials:
        user_info = jwt_auth_service.validate_token(credentials.credentials)
        if user_info:
            return user_info
    
    # Try API key
    if api_key:
        user_info = jwt_auth_service.validate_api_key(api_key)
        if user_info:
            return user_info
    
    # No valid authentication found
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current active user (verified and not disabled)
    """
    if not current_user.get('is_verified', True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    
    return current_user


async def get_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get current user with admin role
    """
    if current_user.get('role') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    api_key: Optional[str] = Depends(api_key_header)
) -> Optional[Dict[str, Any]]:
    """
    Get current user if authenticated, otherwise return None
    Used for endpoints that have optional authentication
    """
    # Try JWT token
    if credentials and credentials.credentials:
        user_info = jwt_auth_service.validate_token(credentials.credentials)
        if user_info:
            return user_info
    
    # Try API key
    if api_key:
        user_info = jwt_auth_service.validate_api_key(api_key)
        if user_info:
            return user_info
    
    return None


class RoleChecker:
    """
    Dependency class for checking user roles
    """
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles
    
    async def __call__(
        self,
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        """
        Check if user has one of the allowed roles
        """
        user_role = current_user.get('role', 'user')
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted to roles: {', '.join(self.allowed_roles)}"
            )
        
        return current_user


class PermissionChecker:
    """
    Dependency class for checking specific permissions
    """
    def __init__(self, required_permissions: list):
        self.required_permissions = required_permissions
    
    async def __call__(
        self,
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        """
        Check if user has required permissions
        """
        user_permissions = current_user.get('permissions', {})
        
        # For API keys, check specific permissions
        if 'api_key_id' in current_user:
            for permission in self.required_permissions:
                if not user_permissions.get(permission, False):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Missing required permission: {permission}"
                    )
        
        return current_user


# Pre-defined role checkers
require_admin = RoleChecker(['admin'])
require_moderator = RoleChecker(['admin', 'moderator'])
require_premium = RoleChecker(['admin', 'moderator', 'premium'])

# Pre-defined permission checkers
require_read = PermissionChecker(['read'])
require_write = PermissionChecker(['write'])
require_delete = PermissionChecker(['delete'])
require_export = PermissionChecker(['export'])