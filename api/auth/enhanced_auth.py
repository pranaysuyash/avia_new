"""
Enhanced Authentication and Authorization System
Provides JWT-based auth, RBAC, MFA, and SSO integration
"""

import os
import secrets
import pyotp
import qrcode
from io import BytesIO
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Union
from enum import Enum

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from pydantic import BaseModel, EmailStr

from api.database import get_db, User, UserRole, APIKey, UserSession

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
MFA_ISSUER = os.getenv("MFA_ISSUER", "Transcription Platform")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 schemes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
security = HTTPBearer()

class Permission(str, Enum):
    """System permissions"""
    # User permissions
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    
    # Transcript permissions
    TRANSCRIPT_READ = "transcript:read"
    TRANSCRIPT_WRITE = "transcript:write"
    TRANSCRIPT_DELETE = "transcript:delete"
    TRANSCRIPT_SHARE = "transcript:share"
    
    # Team permissions
    TEAM_READ = "team:read"
    TEAM_WRITE = "team:write"
    TEAM_DELETE = "team:delete"
    TEAM_MANAGE = "team:manage"
    
    # Admin permissions
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
    SYSTEM_MANAGE = "system:manage"
    
    # API permissions
    API_READ = "api:read"
    API_WRITE = "api:write"

class MFAMethod(str, Enum):
    """Multi-factor authentication methods"""
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    BACKUP_CODES = "backup_codes"

class SSOProvider(str, Enum):
    """SSO providers"""
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    OKTA = "okta"
    SAML = "saml"

# Role-based permissions mapping
ROLE_PERMISSIONS = {
    UserRole.USER: [
        Permission.USER_READ,
        Permission.TRANSCRIPT_READ,
        Permission.TRANSCRIPT_WRITE,
        Permission.TRANSCRIPT_SHARE,
        Permission.TEAM_READ,
        Permission.API_READ,
    ],
    UserRole.ADMIN: [
        Permission.USER_READ,
        Permission.USER_WRITE,
        Permission.USER_DELETE,
        Permission.TRANSCRIPT_READ,
        Permission.TRANSCRIPT_WRITE,
        Permission.TRANSCRIPT_DELETE,
        Permission.TRANSCRIPT_SHARE,
        Permission.TEAM_READ,
        Permission.TEAM_WRITE,
        Permission.TEAM_DELETE,
        Permission.TEAM_MANAGE,
        Permission.ADMIN_READ,
        Permission.ADMIN_WRITE,
        Permission.SYSTEM_MANAGE,
        Permission.API_READ,
        Permission.API_WRITE,
    ],
    UserRole.VIEWER: [
        Permission.USER_READ,
        Permission.TRANSCRIPT_READ,
        Permission.TEAM_READ,
        Permission.API_READ,
    ]
}

# Pydantic models
class TokenData(BaseModel):
    user_id: Optional[int] = None
    permissions: List[str] = []
    session_id: Optional[str] = None

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    permissions: List[str] = []

class MFASetup(BaseModel):
    method: MFAMethod
    secret: Optional[str] = None
    qr_code: Optional[str] = None
    backup_codes: Optional[List[str]] = None

class MFAVerification(BaseModel):
    method: MFAMethod
    code: str
    backup_code: Optional[str] = None

class UserPreferences(BaseModel):
    language: str = "en"
    timezone: str = "UTC"
    theme: str = "light"
    notifications: Dict[str, bool] = {}
    privacy_settings: Dict[str, Any] = {}

class EnhancedAuthService:
    """Enhanced authentication service with RBAC, MFA, and SSO"""
    
    def __init__(self):
        self.pwd_context = pwd_context
    
    # Password utilities
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)
    
    # JWT token utilities
    def create_access_token(
        self, 
        user_id: int, 
        permissions: List[str],
        session_id: Optional[str] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode = {
            "sub": str(user_id),
            "permissions": permissions,
            "session_id": session_id,
            "exp": expire,
            "type": "access",
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    def create_refresh_token(self, user_id: int, session_id: str) -> str:
        """Create a JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode = {
            "sub": str(user_id),
            "session_id": session_id,
            "exp": expire,
            "type": "refresh",
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    
    def decode_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Decode and validate a JWT token"""
        try:
            secret_key = SECRET_KEY if token_type == "access" else REFRESH_SECRET_KEY
            payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
            
            if payload.get("type") != token_type:
                return None
                
            return payload
        except JWTError:
            return None
    
    # User management
    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate a user by email and password"""
        user = db.query(User).filter(User.email == email).first()
        if not user or not self.verify_password(password, user.password_hash):
            return None
        
        if not user.is_active:
            return None
            
        return user
    
    def get_user_permissions(self, user: User) -> List[str]:
        """Get user permissions based on role"""
        return [perm.value for perm in ROLE_PERMISSIONS.get(user.role, [])]
    
    def has_permission(self, user_permissions: List[str], required_permission: Permission) -> bool:
        """Check if user has required permission"""
        return required_permission.value in user_permissions
    
    def has_any_permission(self, user_permissions: List[str], required_permissions: List[Permission]) -> bool:
        """Check if user has any of the required permissions"""
        return any(perm.value in user_permissions for perm in required_permissions)
    
    def has_all_permissions(self, user_permissions: List[str], required_permissions: List[Permission]) -> bool:
        """Check if user has all required permissions"""
        return all(perm.value in user_permissions for perm in required_permissions)
    
    # Session management
    def create_user_session(
        self, 
        db: Session, 
        user: User, 
        ip_address: str, 
        user_agent: str
    ) -> UserSession:
        """Create a new user session"""
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        session = UserSession(
            session_id=session_id,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return session
    
    def invalidate_session(self, db: Session, session_id: str) -> bool:
        """Invalidate a user session"""
        session = db.query(UserSession).filter(
            UserSession.session_id == session_id,
            UserSession.is_active == True
        ).first()
        
        if session:
            session.is_active = False
            db.commit()
            return True
        
        return False
    
    def cleanup_expired_sessions(self, db: Session) -> int:
        """Clean up expired sessions"""
        expired_count = db.query(UserSession).filter(
            UserSession.expires_at < datetime.utcnow()
        ).update({"is_active": False})
        
        db.commit()
        return expired_count
    
    # Multi-factor authentication
    def setup_totp_mfa(self, user: User) -> MFASetup:
        """Setup TOTP-based MFA for user"""
        secret = pyotp.random_base32()
        
        # Generate QR code
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name=MFA_ISSUER
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code_data = base64.b64encode(buffer.getvalue()).decode()
        
        return MFASetup(
            method=MFAMethod.TOTP,
            secret=secret,
            qr_code=f"data:image/png;base64,{qr_code_data}"
        )
    
    def verify_totp_code(self, secret: str, code: str) -> bool:
        """Verify TOTP code"""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes for MFA"""
        return [secrets.token_hex(4).upper() for _ in range(count)]
    
    # Token creation and validation
    def create_tokens(
        self, 
        db: Session, 
        user: User, 
        ip_address: str, 
        user_agent: str
    ) -> Token:
        """Create access and refresh tokens for user"""
        # Create session
        session = self.create_user_session(db, user, ip_address, user_agent)
        
        # Get user permissions
        permissions = self.get_user_permissions(user)
        
        # Create tokens
        access_token = self.create_access_token(
            user_id=user.id,
            permissions=permissions,
            session_id=session.session_id
        )
        
        refresh_token = self.create_refresh_token(
            user_id=user.id,
            session_id=session.session_id
        )
        
        # Update user last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            permissions=permissions
        )
    
    def refresh_access_token(self, db: Session, refresh_token: str) -> Optional[Token]:
        """Refresh access token using refresh token"""
        payload = self.decode_token(refresh_token, "refresh")
        if not payload:
            return None
        
        user_id = int(payload.get("sub"))
        session_id = payload.get("session_id")
        
        # Validate session
        session = db.query(UserSession).filter(
            UserSession.session_id == session_id,
            UserSession.user_id == user_id,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        ).first()
        
        if not session:
            return None
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            return None
        
        # Get permissions
        permissions = self.get_user_permissions(user)
        
        # Create new access token
        access_token = self.create_access_token(
            user_id=user.id,
            permissions=permissions,
            session_id=session_id
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,  # Keep same refresh token
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            permissions=permissions
        )

# Global auth service instance
auth_service = EnhancedAuthService()