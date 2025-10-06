"""
Enhanced Authentication and Authorization Module
"""

from .enhanced_auth import (
    auth_service,
    Permission,
    MFAMethod,
    SSOProvider,
    Token,
    MFASetup,
    MFAVerification,
    UserPreferences,
    EnhancedAuthService
)

from .dependencies import (
    get_current_user,
    get_current_active_user,
    get_current_user_permissions,
    get_token_data,
    require_permissions,
    require_any_permission,
    require_role,
    require_admin,
    require_self_or_admin,
    get_current_user_optional,
    AuthenticationError,
    AuthorizationError,
    RateLimiter,
    standard_rate_limit,
    strict_rate_limit
)

# Add missing functions for API compatibility
def get_current_user_or_api_key(*args, **kwargs):
    """Compatibility function - delegates to get_current_user_optional"""
    return get_current_user_optional(*args, **kwargs)

def create_api_response(data, message="Success"):
    """Create standardized API response"""
    return {"status": "success", "message": message, "data": data}

def create_error_response(message, status_code=400):
    """Create standardized error response"""
    return {"status": "error", "message": message, "status_code": status_code}

# Direct function exports from auth_service for API compatibility
def authenticate_user(db, email: str, password: str):
    """Authenticate user - delegates to auth_service"""
    return auth_service.authenticate_user(db, email, password)

def create_user(db, email: str, password: str, **kwargs):
    """Create user - delegates to auth_service"""
    return auth_service.create_user(db, email, password, **kwargs)

def create_access_token(user_id: int, permissions=None, expires_delta=None):
    """Create access token - delegates to auth_service"""
    return auth_service.create_access_token(user_id, permissions, expires_delta)

def create_refresh_token(user_id: int, session_id: str):
    """Create refresh token - delegates to auth_service"""
    return auth_service.create_refresh_token(user_id, session_id)

def get_user_by_email(db, email: str):
    """Get user by email - delegates to auth_service"""
    return auth_service.get_user_by_email(db, email)

def create_api_key(db, user_id: int, name: str = None):
    """Create API key - delegates to auth_service"""
    return auth_service.create_api_key(db, user_id, name)

def get_current_admin_user(*args, **kwargs):
    """Get current admin user - delegates to require_admin"""
    return require_admin(*args, **kwargs)

# Legacy compatibility functions
api_key_required = get_current_user  # Alias for backward compatibility
jwt_required = get_current_user  # Alias for backward compatibility  
auth_required = get_current_user  # Alias for backward compatibility
admin_required = require_admin  # Direct mapping

# APIAuthManager class for backward compatibility
class APIAuthManager:
    """Legacy auth manager class for backward compatibility"""
    
    def __init__(self):
        self.auth_service = auth_service
    
    def verify_token(self, token: str):
        """Verify JWT token"""
        return self.auth_service.verify_token(token)
    
    def verify_api_key(self, api_key: str):
        """Verify API key"""
        return self.auth_service.verify_api_key(api_key)

from .routes import router as auth_router
from .sso_routes import router as sso_router
from .sso import sso_service, SSOUserInfo, SSOState, SSOService

__all__ = [
    # Core service
    "auth_service",
    "EnhancedAuthService",
    "APIAuthManager",
    
    # Enums and models
    "Permission",
    "MFAMethod", 
    "SSOProvider",
    "Token",
    "MFASetup",
    "MFAVerification",
    "UserPreferences",
    "SSOUserInfo",
    "SSOState",
    
    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "get_current_user_permissions",
    "get_token_data",
    "require_permissions",
    "require_any_permission",
    "require_role",
    "require_admin",
    "require_self_or_admin",
    "get_current_user_optional",
    "get_current_user_or_api_key",
    "get_current_admin_user",
    "create_api_response",
    "create_error_response",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimiter",
    "standard_rate_limit",
    "strict_rate_limit",
    
    # Direct function exports
    "authenticate_user",
    "create_user", 
    "create_access_token",
    "create_refresh_token",
    "get_user_by_email",
    "create_api_key",
    
    # Legacy compatibility
    "api_key_required",
    "jwt_required",
    "auth_required",
    "admin_required",
    
    # Routers
    "auth_router",
    "sso_router",
    
    # SSO service
    "sso_service",
    "SSOService"
]