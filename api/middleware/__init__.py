"""
API Middleware Package
Comprehensive middleware for authentication, rate limiting, CORS, and medical compliance
"""

from .cors_config import setup_cors, CORSConfig, CORSPresets
from .rate_limiter import RateLimitMiddleware, create_rate_limiter

# Enhanced authentication and rate limiting
from .authentication import (
    MedicalAuthenticationMiddleware,
    JWTTokenManager,
    APIKeyManager,
    UserRole,
    MedicalPermission,
    get_current_user,
    require_permission,
    require_role,
    require_medical_professional,
    require_phi_access,
    require_patient_data_access
)

from .rate_limiting import (
    RateLimitingMiddleware,
    MedicalRateLimiter,
    RateLimitRule,
    RateLimitResult,
    get_rate_limiter,
    check_medical_rate_limit,
    get_tier_rules,
    TIER_CONFIGURATIONS
)

__all__ = [
    # Legacy CORS and rate limiting
    'setup_cors',
    'CORSConfig', 
    'CORSPresets',
    'RateLimitMiddleware',
    'create_rate_limiter',
    
    # Enhanced authentication
    "MedicalAuthenticationMiddleware",
    "JWTTokenManager", 
    "APIKeyManager",
    "UserRole",
    "MedicalPermission",
    "get_current_user",
    "require_permission",
    "require_role",
    "require_medical_professional",
    "require_phi_access",
    "require_patient_data_access",
    
    # Enhanced rate limiting
    "RateLimitingMiddleware",
    "MedicalRateLimiter",
    "RateLimitRule",
    "RateLimitResult", 
    "get_rate_limiter",
    "check_medical_rate_limit",
    "get_tier_rules",
    "TIER_CONFIGURATIONS"
]