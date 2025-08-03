"""
Authentication utilities for FastAPI
Handles JWT tokens, password hashing, and user authentication
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os
import secrets

from api.database import get_db, User, UserRole, APIKey

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# API Key header scheme
api_key_header = OAuth2PasswordBearer(tokenUrl="/api/auth/token", scheme_name="api_key", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password"""
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email"""
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get a user by ID"""
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, email: str, password: str, username: str, full_name: str = None) -> User:
    """Create a new user"""
    hashed_password = get_password_hash(password)
    user = User(
        email=email,
        username=username,
        password_hash=hashed_password,
        full_name=full_name,
        verification_token=secrets.token_urlsafe(32)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise credentials_exception
    
    user_id: int = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = get_user_by_id(db, user_id=int(user_id))
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure the current user is active"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user

async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure the current user is an admin"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

def create_api_key(db: Session, user: User, name: str) -> tuple[str, APIKey]:
    """Create a new API key for a user"""
    # Generate a secure random key
    raw_key = secrets.token_urlsafe(32)
    key_hash = get_password_hash(raw_key)
    
    api_key = APIKey(
        user_id=user.id,
        name=name,
        key_hash=key_hash
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    # Return both the raw key (to show once) and the model
    return raw_key, api_key

def validate_api_key(db: Session, api_key: str) -> Optional[User]:
    """Validate an API key and return the associated user"""
    # Try to find all active API keys and check against the hash
    api_keys = db.query(APIKey).filter(APIKey.is_active == True).all()
    
    for key in api_keys:
        if verify_password(api_key, key.key_hash):
            # Update last used timestamp
            key.last_used_at = datetime.utcnow()
            db.commit()
            
            # Check if key is expired
            if key.expires_at and key.expires_at < datetime.utcnow():
                key.is_active = False
                db.commit()
                return None
            
            return key.user
    
    return None

async def get_current_user_or_api_key(
    token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Depends(api_key_header),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from either JWT token or API key"""
    # Try JWT token first
    if token:
        try:
            return await get_current_user(token, db)
        except HTTPException:
            pass
    
    # Try API key
    if api_key:
        user = validate_api_key(db, api_key)
        if user:
            return user
    
    # Neither worked
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

def create_api_response(data=None, message="Success", status_code=200):
    """Create standardized API response"""
    return {
        "status": "success",
        "message": message,
        "data": data,
        "status_code": status_code
    }

def create_error_response(message="Error", status_code=400, details=None):
    """Create standardized error response"""
    response = {
        "status": "error",
        "message": message,
        "status_code": status_code
    }
    if details:
        response["details"] = details
    return response

# Export all utilities
__all__ = [
    'verify_password',
    'get_password_hash',
    'create_access_token',
    'create_refresh_token',
    'decode_token',
    'authenticate_user',
    'get_user_by_email',
    'get_user_by_id',
    'create_user',
    'get_current_user',
    'get_current_active_user',
    'get_current_admin_user',
    'create_api_key',
    'validate_api_key',
    'get_current_user_or_api_key',
    'create_api_response',
    'create_error_response'
]