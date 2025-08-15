"""
Enhanced Authentication Middleware
JWT-based authentication with medical role permissions and API key support
"""

import jwt
import json
import time
import hashlib
from typing import Optional, Dict, List, Any, Callable
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
import redis
import logging

from api.database import get_db, User

logger = logging.getLogger(__name__)


class UserRole:
    """User role definitions for medical transcription platform"""
    
    ANONYMOUS = "anonymous"
    USER = "user"
    MEDICAL_PROFESSIONAL = "medical_professional"
    HEALTHCARE_ADMIN = "healthcare_admin"
    SYSTEM_ADMIN = "system_admin"
    API_USER = "api_user"
    
    # Role hierarchy (higher numbers have more permissions)
    ROLE_HIERARCHY = {
        ANONYMOUS: 0,
        USER: 10,
        API_USER: 15,
        MEDICAL_PROFESSIONAL: 20,
        HEALTHCARE_ADMIN: 30,
        SYSTEM_ADMIN: 100
    }
    
    @classmethod
    def has_permission(cls, user_role: str, required_role: str) -> bool:
        """Check if user role has required permissions"""
        user_level = cls.ROLE_HIERARCHY.get(user_role, 0)
        required_level = cls.ROLE_HIERARCHY.get(required_role, 0)
        return user_level >= required_level


class MedicalPermission:
    """Medical-specific permission definitions"""
    
    # General permissions
    READ_OWN_DATA = "read_own_data"
    WRITE_OWN_DATA = "write_own_data"
    DELETE_OWN_DATA = "delete_own_data"
    
    # Medical transcription permissions
    PROCESS_MEDICAL_TRANSCRIPTION = "process_medical_transcription"
    ACCESS_PHI_DATA = "access_phi_data"
    EXPORT_PHI_DATA = "export_phi_data"
    MANAGE_PHI_SETTINGS = "manage_phi_settings"
    
    # Patient data permissions
    ACCESS_PATIENT_DATA = "access_patient_data"
    MODIFY_PATIENT_DATA = "modify_patient_data"
    DELETE_PATIENT_DATA = "delete_patient_data"
    CROSS_PATIENT_ANALYTICS = "cross_patient_analytics"
    
    # Provider permissions
    MANAGE_PROVIDERS = "manage_providers"
    ACCESS_PROVIDER_ANALYTICS = "access_provider_analytics"
    
    # Administrative permissions
    MANAGE_USERS = "manage_users"
    MANAGE_SYSTEM_SETTINGS = "manage_system_settings"
    ACCESS_AUDIT_LOGS = "access_audit_logs"
    MANAGE_API_KEYS = "manage_api_keys"
    
    # Role-based permission mapping
    ROLE_PERMISSIONS = {
        UserRole.ANONYMOUS: [],
        UserRole.USER: [
            READ_OWN_DATA,
            WRITE_OWN_DATA
        ],
        UserRole.API_USER: [
            READ_OWN_DATA,
            WRITE_OWN_DATA,
            PROCESS_MEDICAL_TRANSCRIPTION
        ],
        UserRole.MEDICAL_PROFESSIONAL: [
            READ_OWN_DATA,
            WRITE_OWN_DATA,
            DELETE_OWN_DATA,
            PROCESS_MEDICAL_TRANSCRIPTION,
            ACCESS_PHI_DATA,
            EXPORT_PHI_DATA,
            ACCESS_PATIENT_DATA,
            MODIFY_PATIENT_DATA,
            ACCESS_PROVIDER_ANALYTICS
        ],
        UserRole.HEALTHCARE_ADMIN: [
            READ_OWN_DATA,
            WRITE_OWN_DATA,
            DELETE_OWN_DATA,
            PROCESS_MEDICAL_TRANSCRIPTION,
            ACCESS_PHI_DATA,
            EXPORT_PHI_DATA,
            MANAGE_PHI_SETTINGS,
            ACCESS_PATIENT_DATA,
            MODIFY_PATIENT_DATA,
            DELETE_PATIENT_DATA,
            CROSS_PATIENT_ANALYTICS,
            MANAGE_PROVIDERS,
            ACCESS_PROVIDER_ANALYTICS,
            MANAGE_USERS,
            ACCESS_AUDIT_LOGS
        ],
        UserRole.SYSTEM_ADMIN: [
            # System admins have all permissions
            READ_OWN_DATA,
            WRITE_OWN_DATA,
            DELETE_OWN_DATA,
            PROCESS_MEDICAL_TRANSCRIPTION,
            ACCESS_PHI_DATA,
            EXPORT_PHI_DATA,
            MANAGE_PHI_SETTINGS,
            ACCESS_PATIENT_DATA,
            MODIFY_PATIENT_DATA,
            DELETE_PATIENT_DATA,
            CROSS_PATIENT_ANALYTICS,
            MANAGE_PROVIDERS,
            ACCESS_PROVIDER_ANALYTICS,
            MANAGE_USERS,
            MANAGE_SYSTEM_SETTINGS,
            ACCESS_AUDIT_LOGS,
            MANAGE_API_KEYS
        ]
    }
    
    @classmethod
    def has_permission(cls, user_role: str, permission: str) -> bool:
        """Check if user role has specific permission"""
        role_permissions = cls.ROLE_PERMISSIONS.get(user_role, [])
        return permission in role_permissions


class APIKey(BaseModel):
    """API Key model"""
    
    key_id: str
    key_hash: str
    user_id: int
    name: str
    permissions: List[str]
    rate_limit_tier: str
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime
    metadata: Dict[str, Any] = {}


class JWTTokenManager:
    """JWT token management for authentication"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
    
    def create_access_token(
        self, 
        user_id: int, 
        role: str, 
        permissions: List[str],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": str(user_id),
            "role": role,
            "permissions": permissions,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: int) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """Generate new access token from refresh token"""
        payload = self.verify_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = int(payload["sub"])
        
        # In a real implementation, fetch user data from database
        # For now, return a new access token with default permissions
        return self.create_access_token(
            user_id=user_id,
            role=UserRole.USER,
            permissions=MedicalPermission.ROLE_PERMISSIONS[UserRole.USER]
        )


class APIKeyManager:
    """API Key management system"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.api_keys_cache: Dict[str, APIKey] = {}
        self.use_redis = redis_client is not None
        
        if self.use_redis:
            try:
                self.redis_client.ping()
            except Exception as e:
                logger.warning(f"Redis not available for API key caching: {e}")
                self.use_redis = False
    
    def _hash_api_key(self, api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def _get_cache_key(self, key_hash: str) -> str:
        """Get Redis cache key for API key"""
        return f"api_key:{key_hash}"
    
    def create_api_key(
        self,
        user_id: int,
        name: str,
        permissions: List[str],
        rate_limit_tier: str = "basic",
        expires_in_days: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> tuple[str, APIKey]:
        """Create new API key"""
        import secrets
        
        # Generate API key
        api_key = f"med_{''.join(secrets.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(40))}"
        key_hash = self._hash_api_key(api_key)
        key_id = f"key_{int(time.time())}_{user_id}"
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        api_key_obj = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            user_id=user_id,
            name=name,
            permissions=permissions,
            rate_limit_tier=rate_limit_tier,
            expires_at=expires_at,
            is_active=True,
            created_at=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        # Store in cache
        self._store_api_key(api_key_obj)
        
        return api_key, api_key_obj
    
    def _store_api_key(self, api_key: APIKey):
        """Store API key in cache"""
        if self.use_redis:
            try:
                cache_key = self._get_cache_key(api_key.key_hash)
                self.redis_client.setex(
                    cache_key,
                    timedelta(days=30),  # Cache for 30 days
                    api_key.json()
                )
            except Exception as e:
                logger.warning(f"Failed to cache API key in Redis: {e}")
        
        # Always store in memory cache as fallback
        self.api_keys_cache[api_key.key_hash] = api_key
    
    def verify_api_key(self, api_key: str) -> Optional[APIKey]:
        """Verify API key and return key info"""
        key_hash = self._hash_api_key(api_key)
        
        # Try Redis first
        if self.use_redis:
            try:
                cache_key = self._get_cache_key(key_hash)
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    api_key_obj = APIKey.parse_raw(cached_data)
                    
                    # Check if key is expired
                    if api_key_obj.expires_at and datetime.utcnow() > api_key_obj.expires_at:
                        return None
                    
                    if not api_key_obj.is_active:
                        return None
                    
                    # Update last used timestamp
                    api_key_obj.last_used = datetime.utcnow()
                    self._store_api_key(api_key_obj)
                    
                    return api_key_obj
            except Exception as e:
                logger.warning(f"Error retrieving API key from Redis: {e}")
        
        # Fall back to memory cache
        api_key_obj = self.api_keys_cache.get(key_hash)
        if api_key_obj:
            # Check if key is expired
            if api_key_obj.expires_at and datetime.utcnow() > api_key_obj.expires_at:
                del self.api_keys_cache[key_hash]
                return None
            
            if not api_key_obj.is_active:
                return None
            
            # Update last used timestamp
            api_key_obj.last_used = datetime.utcnow()
            
            return api_key_obj
        
        return None
    
    def revoke_api_key(self, key_hash: str) -> bool:
        """Revoke API key"""
        if self.use_redis:
            try:
                cache_key = self._get_cache_key(key_hash)
                self.redis_client.delete(cache_key)
            except Exception as e:
                logger.warning(f"Error revoking API key in Redis: {e}")
        
        if key_hash in self.api_keys_cache:
            del self.api_keys_cache[key_hash]
        
        return True


class MedicalAuthenticationMiddleware(BaseHTTPMiddleware):
    """Authentication middleware with medical-specific features"""
    
    def __init__(
        self,
        app,
        jwt_secret: str,
        redis_client: Optional[redis.Redis] = None
    ):
        super().__init__(app)
        self.jwt_manager = JWTTokenManager(jwt_secret)
        self.api_key_manager = APIKeyManager(redis_client)
        self.public_paths = {
            "/health", "/metrics", "/docs", "/redoc", "/openapi.json",
            "/auth/login", "/auth/register", "/auth/refresh",
            "/.well-known/"
        }
    
    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (doesn't require authentication)"""
        return any(path.startswith(public_path) for public_path in self.public_paths)
    
    def _extract_token_from_header(self, request: Request) -> Optional[str]:
        """Extract JWT token from Authorization header"""
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix
        return None
    
    def _extract_api_key_from_request(self, request: Request) -> Optional[str]:
        """Extract API key from request headers or query params"""
        # Check X-API-Key header first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return api_key
        
        # Check query parameter
        api_key = request.query_params.get("api_key")
        if api_key:
            return api_key
        
        return None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through authentication"""
        
        # Skip authentication for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)
        
        # Try API key authentication first
        api_key = self._extract_api_key_from_request(request)
        if api_key:
            api_key_obj = self.api_key_manager.verify_api_key(api_key)
            if api_key_obj:
                # Set request state for API key authentication
                request.state.auth_type = "api_key"
                request.state.user_id = api_key_obj.user_id
                request.state.user_role = UserRole.API_USER
                request.state.permissions = api_key_obj.permissions
                request.state.rate_limit_tier = api_key_obj.rate_limit_tier
                request.state.api_key_id = api_key_obj.key_id
                
                return await call_next(request)
            else:
                return Response(
                    content=json.dumps({"error": "Invalid or expired API key"}),
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    media_type="application/json"
                )
        
        # Try JWT token authentication
        token = self._extract_token_from_header(request)
        if token:
            try:
                payload = self.jwt_manager.verify_token(token)
                user_id = int(payload["sub"])
                role = payload.get("role", UserRole.USER)
                permissions = payload.get("permissions", [])
                
                # Set request state for JWT authentication
                request.state.auth_type = "jwt"
                request.state.user_id = user_id
                request.state.user_role = role
                request.state.permissions = permissions
                request.state.rate_limit_tier = "authenticated"
                
                return await call_next(request)
                
            except HTTPException:
                return Response(
                    content=json.dumps({"error": "Invalid or expired token"}),
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    media_type="application/json"
                )
        
        # No valid authentication found
        return Response(
            content=json.dumps({
                "error": "Authentication required", 
                "message": "Please provide a valid JWT token or API key"
            }),
            status_code=status.HTTP_401_UNAUTHORIZED,
            media_type="application/json"
        )


# FastAPI dependencies for authentication and authorization

security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    request: Request = None
) -> Dict[str, Any]:
    """Get current authenticated user"""
    if hasattr(request.state, "user_id") and request.state.user_id:
        return {
            "user_id": request.state.user_id,
            "role": request.state.user_role,
            "permissions": request.state.permissions,
            "auth_type": request.state.auth_type
        }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required"
    )


def require_permission(permission: str):
    """FastAPI dependency factory for permission checking"""
    
    async def permission_checker(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> bool:
        user_permissions = current_user.get("permissions", [])
        user_role = current_user.get("role", UserRole.ANONYMOUS)
        
        # Check explicit permission
        if permission in user_permissions:
            return True
        
        # Check role-based permission
        if MedicalPermission.has_permission(user_role, permission):
            return True
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required: {permission}"
        )
    
    return permission_checker


def require_role(required_role: str):
    """FastAPI dependency factory for role checking"""
    
    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> bool:
        user_role = current_user.get("role", UserRole.ANONYMOUS)
        
        if UserRole.has_permission(user_role, required_role):
            return True
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient role. Required: {required_role}, Current: {user_role}"
        )
    
    return role_checker


# Specialized dependencies for medical endpoints

async def require_medical_professional(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> bool:
    """Require medical professional role"""
    return await require_role(UserRole.MEDICAL_PROFESSIONAL)(current_user)


async def require_phi_access(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> bool:
    """Require PHI access permission"""
    return await require_permission(MedicalPermission.ACCESS_PHI_DATA)(current_user)


async def require_patient_data_access(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> bool:
    """Require patient data access permission"""
    return await require_permission(MedicalPermission.ACCESS_PATIENT_DATA)(current_user)