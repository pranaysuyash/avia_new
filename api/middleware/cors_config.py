"""
CORS (Cross-Origin Resource Sharing) configuration for production deployment
Handles secure cross-origin requests with environment-specific settings
"""

import os
from typing import List, Optional, Union
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

logger = logging.getLogger(__name__)


class CORSConfig:
    """CORS configuration manager with environment-specific settings"""
    
    def __init__(self):
        """Initialize CORS configuration from environment variables"""
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.allowed_origins = self._get_allowed_origins()
        self.allowed_methods = self._get_allowed_methods()
        self.allowed_headers = self._get_allowed_headers()
        self.exposed_headers = self._get_exposed_headers()
        self.allow_credentials = self._get_allow_credentials()
        self.max_age = self._get_max_age()
    
    def _get_allowed_origins(self) -> List[str]:
        """Get allowed origins based on environment"""
        # Get from environment variable
        env_origins = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
        if env_origins:
            origins = [origin.strip() for origin in env_origins.split(",")]
            logger.info(f"Using configured CORS origins: {origins}")
            return origins
        
        # Default based on environment
        if self.environment == "production":
            # Production: Restrict to specific domains
            return [
                "https://app.example.com",
                "https://www.example.com",
                "https://admin.example.com"
            ]
        elif self.environment == "staging":
            # Staging: Allow staging domains
            return [
                "https://staging.example.com",
                "https://app-staging.example.com",
                "http://localhost:3000",  # For testing
                "http://localhost:3001"
            ]
        else:
            # Development: Allow common local ports
            return [
                "http://localhost:3000",
                "http://localhost:3001",
                "http://localhost:5173",  # Vite
                "http://localhost:8080",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:8080",
                # Streamlit default port
                "http://localhost:8501",
                "http://127.0.0.1:8501"
            ]
    
    def _get_allowed_methods(self) -> List[str]:
        """Get allowed HTTP methods"""
        env_methods = os.getenv("CORS_ALLOWED_METHODS", "").strip()
        if env_methods:
            return [method.strip() for method in env_methods.split(",")]
        
        # Default methods
        return ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    
    def _get_allowed_headers(self) -> List[str]:
        """Get allowed request headers"""
        env_headers = os.getenv("CORS_ALLOWED_HEADERS", "").strip()
        if env_headers:
            return [header.strip() for header in env_headers.split(",")]
        
        # Default headers
        return [
            "Content-Type",
            "Authorization",
            "X-API-Key",
            "X-Correlation-ID",
            "X-Request-ID",
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Origin",
            "User-Agent",
            "Cache-Control"
        ]
    
    def _get_exposed_headers(self) -> List[str]:
        """Get headers exposed to the client"""
        env_exposed = os.getenv("CORS_EXPOSED_HEADERS", "").strip()
        if env_exposed:
            return [header.strip() for header in env_exposed.split(",")]
        
        # Default exposed headers
        return [
            "Content-Type",
            "Content-Length",
            "X-Request-ID",
            "X-Correlation-ID",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "Retry-After",
            "Location",
            "ETag",
            "Last-Modified"
        ]
    
    def _get_allow_credentials(self) -> bool:
        """Check if credentials (cookies, auth headers) are allowed"""
        return os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    
    def _get_max_age(self) -> int:
        """Get preflight cache duration in seconds"""
        return int(os.getenv("CORS_MAX_AGE", "3600"))  # Default 1 hour
    
    def is_origin_allowed(self, origin: str) -> bool:
        """Check if a specific origin is allowed"""
        # Handle wildcard
        if "*" in self.allowed_origins:
            return True
        
        # Exact match
        if origin in self.allowed_origins:
            return True
        
        # Check patterns (e.g., subdomains)
        for allowed in self.allowed_origins:
            if allowed.startswith("*."):
                # Wildcard subdomain
                domain = allowed[2:]  # Remove *.
                if origin.endswith(domain) or origin.endswith(f"://{domain}"):
                    return True
        
        return False
    
    def get_middleware_kwargs(self) -> dict:
        """Get kwargs for CORSMiddleware"""
        return {
            "allow_origins": self.allowed_origins,
            "allow_credentials": self.allow_credentials,
            "allow_methods": self.allowed_methods,
            "allow_headers": self.allowed_headers,
            "expose_headers": self.exposed_headers,
            "max_age": self.max_age
        }


def setup_cors(app: FastAPI, custom_config: Optional[CORSConfig] = None) -> None:
    """
    Set up CORS middleware for the FastAPI application
    
    Args:
        app: FastAPI application instance
        custom_config: Optional custom CORS configuration
    """
    config = custom_config or CORSConfig()
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        **config.get_middleware_kwargs()
    )
    
    logger.info(f"CORS configured for {config.environment} environment")
    logger.info(f"Allowed origins: {config.allowed_origins}")
    logger.info(f"Allow credentials: {config.allow_credentials}")


def create_cors_config(
    allowed_origins: Optional[List[str]] = None,
    allow_credentials: bool = True,
    allowed_methods: Optional[List[str]] = None,
    allowed_headers: Optional[List[str]] = None,
    exposed_headers: Optional[List[str]] = None,
    max_age: int = 3600
) -> CORSConfig:
    """
    Create a custom CORS configuration
    
    Args:
        allowed_origins: List of allowed origins
        allow_credentials: Whether to allow credentials
        allowed_methods: List of allowed HTTP methods
        allowed_headers: List of allowed request headers
        exposed_headers: List of headers exposed to client
        max_age: Preflight cache duration
        
    Returns:
        CORSConfig instance
    """
    config = CORSConfig()
    
    if allowed_origins is not None:
        config.allowed_origins = allowed_origins
    if allowed_methods is not None:
        config.allowed_methods = allowed_methods
    if allowed_headers is not None:
        config.allowed_headers = allowed_headers
    if exposed_headers is not None:
        config.exposed_headers = exposed_headers
    
    config.allow_credentials = allow_credentials
    config.max_age = max_age
    
    return config


# Preset configurations for common scenarios
class CORSPresets:
    """Common CORS configuration presets"""
    
    @staticmethod
    def public_api() -> CORSConfig:
        """Configuration for public APIs (no credentials)"""
        return create_cors_config(
            allowed_origins=["*"],
            allow_credentials=False,
            allowed_methods=["GET", "POST", "OPTIONS"],
            max_age=86400  # 24 hours
        )
    
    @staticmethod
    def private_api() -> CORSConfig:
        """Configuration for private APIs (strict origins)"""
        return create_cors_config(
            allowed_origins=[
                "https://app.example.com",
                "https://admin.example.com"
            ],
            allow_credentials=True,
            allowed_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            max_age=3600  # 1 hour
        )
    
    @staticmethod
    def mobile_app() -> CORSConfig:
        """Configuration for mobile app APIs"""
        return create_cors_config(
            allowed_origins=["*"],  # Mobile apps don't have origin
            allow_credentials=True,
            allowed_headers=["*"],  # Mobile apps may send custom headers
            exposed_headers=["*"],  # Expose all headers to mobile
            max_age=0  # No preflight caching for mobile
        )
    
    @staticmethod
    def development() -> CORSConfig:
        """Permissive configuration for development"""
        return create_cors_config(
            allowed_origins=["*"],
            allow_credentials=True,
            allowed_methods=["*"],
            allowed_headers=["*"],
            exposed_headers=["*"],
            max_age=3600
        )


# Security utilities
def validate_origin(origin: str, allowed_patterns: List[str]) -> bool:
    """
    Validate origin against allowed patterns
    
    Args:
        origin: Origin to validate
        allowed_patterns: List of allowed patterns (supports wildcards)
        
    Returns:
        True if origin is allowed
    """
    for pattern in allowed_patterns:
        if pattern == "*":
            return True
        
        if pattern == origin:
            return True
        
        # Handle wildcard subdomains
        if pattern.startswith("*.") and origin.endswith(pattern[1:]):
            return True
        
        # Handle regex patterns
        if pattern.startswith("^") and pattern.endswith("$"):
            import re
            if re.match(pattern, origin):
                return True
    
    return False


def get_origin_from_request(request) -> Optional[str]:
    """Extract origin from request headers"""
    return request.headers.get("Origin") or request.headers.get("Referer")


# Example usage for different deployment scenarios
def get_cors_config_for_environment() -> CORSConfig:
    """Get appropriate CORS config based on environment"""
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "production":
        # Production: Strict configuration
        return create_cors_config(
            allowed_origins=[
                "https://app.example.com",
                "https://www.example.com",
                "https://mobile.example.com"
            ],
            allow_credentials=True,
            max_age=86400  # 24 hour cache
        )
    elif environment == "staging":
        # Staging: Allow staging domains and localhost
        return create_cors_config(
            allowed_origins=[
                "https://*.staging.example.com",
                "http://localhost:3000",
                "http://localhost:3001"
            ],
            allow_credentials=True,
            max_age=3600  # 1 hour cache
        )
    else:
        # Development: Permissive
        return CORSPresets.development()


# Dynamic CORS for multi-tenant applications
class DynamicCORSConfig:
    """Dynamic CORS configuration for multi-tenant apps"""
    
    def __init__(self, tenant_resolver: callable):
        """
        Initialize dynamic CORS config
        
        Args:
            tenant_resolver: Function to resolve tenant from request
        """
        self.tenant_resolver = tenant_resolver
        self.tenant_configs = {}
    
    def add_tenant_config(self, tenant_id: str, config: CORSConfig):
        """Add CORS config for a specific tenant"""
        self.tenant_configs[tenant_id] = config
    
    def get_config_for_request(self, request) -> CORSConfig:
        """Get CORS config for the current request"""
        tenant_id = self.tenant_resolver(request)
        return self.tenant_configs.get(tenant_id, CORSConfig())


if __name__ == "__main__":
    # Example: Print current CORS configuration
    config = CORSConfig()
    print(f"Environment: {config.environment}")
    print(f"Allowed Origins: {config.allowed_origins}")
    print(f"Allow Credentials: {config.allow_credentials}")
    print(f"Allowed Methods: {config.allowed_methods}")
    print(f"Allowed Headers: {config.allowed_headers}")
    print(f"Exposed Headers: {config.exposed_headers}")
    print(f"Max Age: {config.max_age}")