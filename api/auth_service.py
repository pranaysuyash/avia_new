"""
JWT Authentication Service with PostgreSQL Integration
Handles user authentication, token generation, and session management
"""

import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
import logging
import secrets
import string

# Add project root to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import User, Session as UserSession, APIKey
from db_config.database_config import DatabaseConfig
from utils import validate_email

logger = logging.getLogger(__name__)


class JWTAuthService:
    """JWT Authentication Service with database integration"""
    
    def __init__(self):
        self.secret_key = os.getenv('JWT_SECRET_KEY', 'change-this-in-production')
        self.algorithm = 'HS256'
        self.access_token_expire = timedelta(hours=24)
        self.refresh_token_expire = timedelta(days=30)
        
        # Database setup
        db_url = DatabaseConfig.get_database_url()
        db_settings = DatabaseConfig.get_database_settings(db_url)
        self.engine = create_engine(db_url, **db_settings)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def _get_db(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def _generate_token(self, payload: Dict[str, Any], expires_delta: timedelta) -> str:
        """Generate JWT token"""
        expire = datetime.utcnow() + expires_delta
        payload.update({
            'exp': expire,
            'iat': datetime.utcnow()
        })
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def _decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def register_user(self, email: str, username: str, password: str, 
                     full_name: Optional[str] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Register a new user
        Returns: (success, message, user_data)
        """
        db = self._get_db()
        try:
            # Validate email
            if not validate_email(email):
                return False, "Invalid email format", None
            
            # Check if user exists
            existing_user = db.query(User).filter(
                (User.email == email) | (User.username == username)
            ).first()
            
            if existing_user:
                if existing_user.email == email:
                    return False, "Email already registered", None
                else:
                    return False, "Username already taken", None
            
            # Create new user
            password_hash = self._hash_password(password)
            verification_token = secrets.token_urlsafe(32)
            
            user = User(
                email=email,
                username=username,
                password_hash=password_hash,
                full_name=full_name,
                verification_token=verification_token,
                created_at=datetime.utcnow(),
                is_active=True,
                is_verified=False
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            user_data = {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'full_name': user.full_name,
                'role': user.role.value if user.role else 'user',
                'verification_token': verification_token
            }
            
            logger.info(f"User registered successfully: {username}")
            return True, "Registration successful", user_data
            
        except Exception as e:
            db.rollback()
            logger.error(f"Registration error: {e}")
            return False, "Registration failed", None
        finally:
            db.close()
    
    def authenticate_user(self, username_or_email: str, password: str, 
                         ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Authenticate user and create session
        Returns: (success, message, session_data)
        """
        db = self._get_db()
        try:
            # Find user by email or username
            user = db.query(User).filter(
                (User.email == username_or_email) | (User.username == username_or_email)
            ).first()
            
            if not user:
                return False, "Invalid credentials", None
            
            # Check if user is active
            if not user.is_active:
                return False, "Account is disabled", None
            
            # Verify password
            if not self._verify_password(password, user.password_hash):
                return False, "Invalid credentials", None
            
            # Generate tokens
            access_token_payload = {
                'user_id': user.id,
                'username': user.username,
                'role': user.role.value if user.role else 'user',
                'type': 'access'
            }
            
            refresh_token_payload = {
                'user_id': user.id,
                'type': 'refresh'
            }
            
            access_token = self._generate_token(access_token_payload, self.access_token_expire)
            refresh_token = self._generate_token(refresh_token_payload, self.refresh_token_expire)
            
            # Create session
            session = UserSession(
                user_id=user.id,
                session_token=access_token,
                refresh_token=refresh_token,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=datetime.utcnow() + self.access_token_expire,
                is_active=True
            )
            
            db.add(session)
            
            # Update last login
            user.last_login = datetime.utcnow()
            
            db.commit()
            
            session_data = {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'bearer',
                'expires_in': int(self.access_token_expire.total_seconds()),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role.value if user.role else 'user',
                    'is_verified': user.is_verified
                }
            }
            
            logger.info(f"User authenticated: {username_or_email}")
            return True, "Authentication successful", session_data
            
        except Exception as e:
            db.rollback()
            logger.error(f"Authentication error: {e}")
            return False, "Authentication failed", None
        finally:
            db.close()
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate access token and return user info
        """
        payload = self._decode_token(token)
        if not payload or payload.get('type') != 'access':
            return None
        
        db = self._get_db()
        try:
            # Check if session exists and is active
            session = db.query(UserSession).filter(
                UserSession.session_token == token,
                UserSession.is_active == True
            ).first()
            
            if not session:
                return None
            
            # Check if session is expired
            if session.expires_at < datetime.utcnow():
                session.is_active = False
                db.commit()
                return None
            
            # Update last accessed
            session.last_accessed = datetime.utcnow()
            db.commit()
            
            # Get user info
            user = db.query(User).filter(User.id == payload['user_id']).first()
            if not user or not user.is_active:
                return None
            
            return {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role.value if user.role else 'user',
                'is_verified': user.is_verified
            }
            
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None
        finally:
            db.close()
    
    def refresh_token(self, refresh_token: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Refresh access token using refresh token
        Returns: (success, message, new_tokens)
        """
        payload = self._decode_token(refresh_token)
        if not payload or payload.get('type') != 'refresh':
            return False, "Invalid refresh token", None
        
        db = self._get_db()
        try:
            # Find session by refresh token
            session = db.query(UserSession).filter(
                UserSession.refresh_token == refresh_token,
                UserSession.is_active == True
            ).first()
            
            if not session:
                return False, "Invalid refresh token", None
            
            # Get user
            user = db.query(User).filter(User.id == payload['user_id']).first()
            if not user or not user.is_active:
                return False, "User not found or inactive", None
            
            # Generate new access token
            access_token_payload = {
                'user_id': user.id,
                'username': user.username,
                'role': user.role.value if user.role else 'user',
                'type': 'access'
            }
            
            new_access_token = self._generate_token(access_token_payload, self.access_token_expire)
            
            # Update session
            session.session_token = new_access_token
            session.expires_at = datetime.utcnow() + self.access_token_expire
            session.last_accessed = datetime.utcnow()
            
            db.commit()
            
            return True, "Token refreshed", {
                'access_token': new_access_token,
                'token_type': 'bearer',
                'expires_in': int(self.access_token_expire.total_seconds())
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Token refresh error: {e}")
            return False, "Token refresh failed", None
        finally:
            db.close()
    
    def logout(self, token: str) -> bool:
        """Logout user by invalidating session"""
        db = self._get_db()
        try:
            session = db.query(UserSession).filter(
                UserSession.session_token == token
            ).first()
            
            if session:
                session.is_active = False
                db.commit()
                logger.info(f"User logged out: {session.user_id}")
                return True
            
            return False
            
        except Exception as e:
            db.rollback()
            logger.error(f"Logout error: {e}")
            return False
        finally:
            db.close()
    
    def create_api_key(self, user_id: int, name: str, permissions: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Create API key for user
        Returns: (success, message, api_key_data)
        """
        db = self._get_db()
        try:
            # Generate API key
            key = 'pk_' + ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
            key_hash = self._hash_password(key)
            key_prefix = key[:7]
            
            api_key = APIKey(
                user_id=user_id,
                key_hash=key_hash,
                key_prefix=key_prefix,
                name=name,
                permissions=permissions or {},
                is_active=True
            )
            
            db.add(api_key)
            db.commit()
            db.refresh(api_key)
            
            api_key_data = {
                'id': api_key.id,
                'key': key,  # Only returned once
                'key_prefix': key_prefix,
                'name': name,
                'created_at': api_key.created_at.isoformat()
            }
            
            logger.info(f"API key created for user {user_id}: {name}")
            return True, "API key created", api_key_data
            
        except Exception as e:
            db.rollback()
            logger.error(f"API key creation error: {e}")
            return False, "Failed to create API key", None
        finally:
            db.close()
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate API key and return user info"""
        if not api_key.startswith('pk_'):
            return None
        
        db = self._get_db()
        try:
            # Get all API keys with matching prefix
            key_prefix = api_key[:7]
            api_keys = db.query(APIKey).filter(
                APIKey.key_prefix == key_prefix,
                APIKey.is_active == True
            ).all()
            
            # Check each key
            for key_record in api_keys:
                if self._verify_password(api_key, key_record.key_hash):
                    # Check if expired
                    if key_record.expires_at and key_record.expires_at < datetime.utcnow():
                        key_record.is_active = False
                        db.commit()
                        return None
                    
                    # Update usage
                    key_record.last_used = datetime.utcnow()
                    key_record.total_requests += 1
                    
                    # Get user
                    user = db.query(User).filter(User.id == key_record.user_id).first()
                    if not user or not user.is_active:
                        return None
                    
                    db.commit()
                    
                    return {
                        'user_id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'role': user.role.value if user.role else 'user',
                        'api_key_id': key_record.id,
                        'api_key_name': key_record.name,
                        'permissions': key_record.permissions
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return None
        finally:
            db.close()
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        db = self._get_db()
        try:
            expired_sessions = db.query(UserSession).filter(
                UserSession.expires_at < datetime.utcnow(),
                UserSession.is_active == True
            ).all()
            
            count = len(expired_sessions)
            for session in expired_sessions:
                session.is_active = False
            
            db.commit()
            logger.info(f"Cleaned up {count} expired sessions")
            return count
            
        except Exception as e:
            db.rollback()
            logger.error(f"Session cleanup error: {e}")
            return 0
        finally:
            db.close()


# Global instance
jwt_auth_service = JWTAuthService()