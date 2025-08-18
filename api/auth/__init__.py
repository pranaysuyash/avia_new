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
    "create_api_response",
    "create_error_response",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimiter",
    "standard_rate_limit",
    "strict_rate_limit",
    
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