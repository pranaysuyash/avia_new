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

from .routes import router as auth_router
from .sso_routes import router as sso_router
from .sso import sso_service, SSOUserInfo, SSOState, SSOService

__all__ = [
    # Core service
    "auth_service",
    "EnhancedAuthService",
    
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
    "AuthenticationError",
    "AuthorizationError",
    "RateLimiter",
    "standard_rate_limit",
    "strict_rate_limit",
    
    # Routers
    "auth_router",
    "sso_router",
    
    # SSO service
    "sso_service",
    "SSOService"
]