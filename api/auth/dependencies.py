"""
Authentication dependencies for FastAPI endpoints
Provides decorators and dependency functions for auth and authorization
"""

from typing import List, Optional, Callable, Any
from functools import wraps

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from api.database import get_db, User, UserSession
from .enhanced_auth import auth_service, Permission, TokenData

security = HTTPBearer()

class AuthenticationError(HTTPException):
    """Authentication error exception"""
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class AuthorizationError(HTTPException):
    """Authorization error exception"""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    
    if not credentials:
        raise AuthenticationError("No authentication credentials provided")
    
    # Decode token
    payload = auth_service.decode_token(credentials.credentials)
    if not payload:
        raise AuthenticationError("Invalid or expired token")
    
    user_id = payload.get("sub")
    session_id = payload.get("session_id")
    
    if not user_id:
        raise AuthenticationError("Invalid token payload")
    
    # Get user
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise AuthenticationError("User not found")
    
    if not user.is_active:
        raise AuthenticationError("User account is inactive")
    
    # Validate session if present
    if session_id:
        session = db.query(UserSession).filter(
            UserSession.session_id == session_id,
            UserSession.user_id == user.id,
            UserSession.is_active == True
        ).first()
        
        if not session:
            raise AuthenticationError("Invalid session")
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure current user is active"""
    if not current_user.is_active:
        raise AuthenticationError("User account is inactive")
    return current_user

async def get_current_user_permissions(
    current_user: User = Depends(get_current_user)
) -> List[str]:
    """Get current user's permissions"""
    return auth_service.get_user_permissions(current_user)

async def get_token_data(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """Extract token data from JWT"""
    if not credentials:
        raise AuthenticationError("No authentication credentials provided")
    
    payload = auth_service.decode_token(credentials.credentials)
    if not payload:
        raise AuthenticationError("Invalid or expired token")
    
    return TokenData(
        user_id=int(payload.get("sub", 0)),
        permissions=payload.get("permissions", []),
        session_id=payload.get("session_id")
    )

def require_permissions(*required_permissions: Permission):
    """Dependency factory for requiring specific permissions"""
    
    async def permission_checker(
        token_data: TokenData = Depends(get_token_data)
    ) -> TokenData:
        """Check if user has required permissions"""
        if not auth_service.has_all_permissions(
            token_data.permissions, 
            list(required_permissions)
        ):
            missing_perms = [
                perm.value for perm in required_permissions 
                if perm.value not in token_data.permissions
            ]
            raise AuthorizationError(
                f"Missing required permissions: {', '.join(missing_perms)}"
            )
        
        return token_data
    
    return permission_checker

def require_any_permission(*required_permissions: Permission):
    """Dependency factory for requiring any of the specified permissions"""
    
    async def permission_checker(
        token_data: TokenData = Depends(get_token_data)
    ) -> TokenData:
        """Check if user has any of the required permissions"""
        if not auth_service.has_any_permission(
            token_data.permissions, 
            list(required_permissions)
        ):
            raise AuthorizationError(
                f"Requires one of: {', '.join(perm.value for perm in required_permissions)}"
            )
        
        return token_data
    
    return permission_checker

def require_role(*required_roles):
    """Dependency factory for requiring specific user roles"""
    
    async def role_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """Check if user has required role"""
        if current_user.role not in required_roles:
            raise AuthorizationError(
                f"Requires role: {' or '.join(role.value for role in required_roles)}"
            )
        
        return current_user
    
    return role_checker

def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require admin role"""
    from api.database import UserRole
    
    if current_user.role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    return current_user

def require_self_or_admin(user_id: int):
    """Dependency factory for requiring user to be accessing their own data or be admin"""
    
    async def self_or_admin_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """Check if user is accessing their own data or is admin"""
        from api.database import UserRole
        
        if current_user.id != user_id and current_user.role != UserRole.ADMIN:
            raise AuthorizationError("Can only access your own data or admin required")
        
        return current_user
    
    return self_or_admin_checker

# Optional authentication (for public endpoints that can benefit from auth)
async def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        payload = auth_service.decode_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user or not user.is_active:
            return None
        
        return user
    except Exception:
        return None

# Decorator for protecting functions
def auth_required(permissions: Optional[List[Permission]] = None):
    """Decorator for requiring authentication and optional permissions"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This is a simplified decorator - in practice, you'd use FastAPI dependencies
            # This is mainly for documentation and can be used with non-FastAPI functions
            return await func(*args, **kwargs)
        
        # Add metadata for documentation
        wrapper._auth_required = True
        wrapper._required_permissions = permissions or []
        
        return wrapper
    
    return decorator

# Rate limiting dependency
class RateLimiter:
    """Rate limiting for authenticated users"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.user_requests = {}  # In production, use Redis
    
    async def __call__(
        self, 
        request: Request,
        current_user: User = Depends(get_current_user)
    ):
        """Check rate limit for current user"""
        import time
        
        current_time = time.time()
        user_id = current_user.id
        
        # Clean old entries
        if user_id in self.user_requests:
            self.user_requests[user_id] = [
                req_time for req_time in self.user_requests[user_id]
                if current_time - req_time < 60  # Last minute
            ]
        else:
            self.user_requests[user_id] = []
        
        # Check limit
        if len(self.user_requests[user_id]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        # Record request
        self.user_requests[user_id].append(current_time)
        
        return current_user

# Create rate limiter instances
standard_rate_limit = RateLimiter(60)  # 60 requests per minute
strict_rate_limit = RateLimiter(10)    # 10 requests per minute