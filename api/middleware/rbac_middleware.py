#!/usr/bin/env python3
"""
RBAC Middleware for FastAPI
Enforces role-based permissions on API endpoints
"""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List, Callable
import logging
from functools import wraps

from auth.rbac_service import Permission, ResourceType, rbac_service
from auth.auth_service_enhanced import AuthenticationService
from database.models import User
from database.connection import get_db

logger = logging.getLogger(__name__)

class RBACMiddleware:
    """Middleware for enforcing RBAC permissions"""
    
    def __init__(self):
        self.auth_service = AuthenticationService(get_db)
        self.bearer_scheme = HTTPBearer(auto_error=False)
    
    def require_permission(
        self,
        permission: Permission,
        resource_type: Optional[ResourceType] = None,
        resource_id_param: Optional[str] = None,
        resource_id_header: Optional[str] = None,
        resource_id_body: Optional[str] = None
    ):
        """
        Decorator to require specific permission for an endpoint
        
        Args:
            permission: Required permission
            resource_type: Type of resource being accessed
            resource_id_param: Path parameter name containing resource ID
            resource_id_header: Header name containing resource ID
            resource_id_body: Request body field containing resource ID
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract request from args/kwargs
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                if not request:
                    request = kwargs.get('request')
                
                if not request:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Request object not found"
                    )
                
                # Get current user
                user = await self._get_current_user(request)
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                # Extract resource ID
                resource_id = None
                if resource_id_param and resource_id_param in kwargs:
                    resource_id = kwargs[resource_id_param]
                elif resource_id_header:
                    resource_id = request.headers.get(resource_id_header)
                elif resource_id_body and hasattr(request, '_body'):
                    # Parse body if needed
                    try:
                        import json
                        body = json.loads(request._body)
                        resource_id = body.get(resource_id_body)
                    except Exception:
                        pass
                
                # Check permission
                if not rbac_service.check_permission(
                    user=user,
                    permission=permission,
                    resource_type=resource_type,
                    resource_id=resource_id
                ):
                    logger.warning(
                        f"Permission denied for user {user.id} ({user.username}): "
                        f"{permission.value} on {resource_type.value if resource_type else 'system'} "
                        f"resource {resource_id if resource_id else 'N/A'}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: {permission.value}"
                    )
                
                # Add user to kwargs for endpoint use
                kwargs['current_user'] = user
                
                # Log successful permission check
                logger.info(
                    f"Permission granted for user {user.id} ({user.username}): "
                    f"{permission.value} on {resource_type.value if resource_type else 'system'}"
                )
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def require_any_permission(self, permissions: List[Permission]):
        """Require at least one of the specified permissions"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Get request and user
                request = self._extract_request(args, kwargs)
                user = await self._get_current_user(request)
                
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                # Check if user has any of the permissions
                user_permissions = rbac_service.get_user_permissions(user)
                if not any(perm in user_permissions for perm in permissions):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions"
                    )
                
                kwargs['current_user'] = user
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def require_all_permissions(self, permissions: List[Permission]):
        """Require all of the specified permissions"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Get request and user
                request = self._extract_request(args, kwargs)
                user = await self._get_current_user(request)
                
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                # Check if user has all permissions
                user_permissions = rbac_service.get_user_permissions(user)
                if not all(perm in user_permissions for perm in permissions):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions"
                    )
                
                kwargs['current_user'] = user
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def require_team_permission(
        self,
        permission: Permission,
        team_id_param: Optional[str] = "team_id"
    ):
        """Require permission within a specific team context"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Get request and user
                request = self._extract_request(args, kwargs)
                user = await self._get_current_user(request)
                
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                # Get team ID
                team_id = kwargs.get(team_id_param)
                if not team_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Team ID required"
                    )
                
                # Check team permission
                team_permissions = rbac_service.get_user_team_permissions(user, team_id)
                if permission not in team_permissions:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: {permission.value} in team"
                    )
                
                kwargs['current_user'] = user
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    async def _get_current_user(self, request: Request) -> Optional[User]:
        """Extract and validate user from request"""
        # Check Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = self.auth_service._decode_token(token)
            if payload:
                db = next(get_db())
                user = db.query(User).filter(User.id == payload['user_id']).first()
                if user and user.is_active:
                    return user
        
        # Check API key header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            is_valid, user = self.auth_service.validate_api_key(api_key)
            if is_valid and user:
                return user
        
        return None
    
    def _extract_request(self, args: tuple, kwargs: dict) -> Request:
        """Extract request object from function arguments"""
        for arg in args:
            if isinstance(arg, Request):
                return arg
        
        if 'request' in kwargs:
            return kwargs['request']
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Request object not found"
        )

# Global instance
rbac_middleware = RBACMiddleware()

# Convenience decorators
require_permission = rbac_middleware.require_permission
require_any_permission = rbac_middleware.require_any_permission
require_all_permissions = rbac_middleware.require_all_permissions
require_team_permission = rbac_middleware.require_team_permission