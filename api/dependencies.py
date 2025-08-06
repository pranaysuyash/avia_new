"""
API Dependencies
Common dependencies for API endpoints
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from database.connection import get_db
from .auth import get_current_user as _get_current_user, create_api_response

def create_error_response(message: str, status_code: int = 400):
    """Create error response"""
    return create_api_response(
        data=None,
        message=message,
        status_code=status_code
    )

# Re-export for convenience
get_current_user = _get_current_user

# Alias for backward compatibility
auth_required = get_current_user
write_required = get_current_user
read_required = get_current_user

def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current active user"""
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user

def get_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current admin user"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

def require_role(role: str):
    """Decorator to require specific role"""
    def decorator(func):
        async def wrapper(*args, current_user: Dict[str, Any] = Depends(get_current_user), **kwargs):
            if current_user.get("role") != role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"{role} access required"
                )
            return await func(*args, current_user=current_user, **kwargs)
        # Copy function attributes for FastAPI
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator

def require_roles(roles: list):
    """Decorator to require one of specified roles"""
    def decorator(func):
        async def wrapper(*args, current_user: Dict[str, Any] = Depends(get_current_user), **kwargs):
            if current_user.get("role") not in roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of {roles} access required"
                )
            return await func(*args, current_user=current_user, **kwargs)
        # Copy function attributes for FastAPI
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator