#!/usr/bin/env python3
"""
Enhanced Authentication Service - Platform-agnostic authentication backend
Supports Streamlit, Desktop (Electron), Mobile, and API access
"""

import os
import jwt
import bcrypt
import secrets
import string
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select, and_, or_
from sqlalchemy.orm import sessionmaker
import hashlib
import base64
from enum import Enum

# Import database models
from database.models import User, Session as UserSession, APIKey, Team, TeamMember, UserRole, TeamRole

logger = logging.getLogger(__name__)

class AuthProvider(Enum):
    """Authentication providers"""
    LOCAL = "local"
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"
    SAML = "saml"
    OAUTH2 = "oauth2"

class TokenType(Enum):
    """Token types"""
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"
    RESET_PASSWORD = "reset_password"
    EMAIL_VERIFICATION = "email_verification"
    MFA = "mfa"

class AuthenticationService:
    """
    Enhanced authentication service supporting multiple platforms and features:
    - JWT tokens for web/mobile
    - API keys for programmatic access
    - OAuth/SSO integration
    - Multi-factor authentication (MFA)
    - Team/organization support
    - Session management
    - Rate limiting
    - Audit logging
    """
    
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.jwt_secret = os.getenv('JWT_SECRET_KEY', self._generate_secret())
        self.jwt_algorithm = 'HS256'
        
        # Token expiration settings
        self.token_expiry = {
            TokenType.ACCESS: timedelta(hours=1),
            TokenType.REFRESH: timedelta(days=30),
            TokenType.RESET_PASSWORD: timedelta(hours=1),
            TokenType.EMAIL_VERIFICATION: timedelta(days=7),
            TokenType.MFA: timedelta(minutes=5)
        }
        
        # Rate limiting settings
        self.max_login_attempts = 5
        self.lockout_duration = timedelta(minutes=30)
        
        # MFA settings
        self.mfa_issuer = "TranscriptPro"
        
    def _generate_secret(self) -> str:
        """Generate a secure secret key"""
        return secrets.token_urlsafe(32)
    
    def _get_db(self) -> Session:
        """Get database session"""
        return self.db_session_factory()
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def _generate_token(self, payload: Dict[str, Any], token_type: TokenType) -> str:
        """Generate JWT token"""
        expire = datetime.utcnow() + self.token_expiry[token_type]
        payload.update({
            'exp': expire,
            'iat': datetime.utcnow(),
            'type': token_type.value,
            'jti': secrets.token_urlsafe(16)  # JWT ID for revocation
        })
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def _decode_token(self, token: str, expected_type: Optional[TokenType] = None) -> Optional[Dict[str, Any]]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Verify token type if specified
            if expected_type and payload.get('type') != expected_type.value:
                logger.warning(f"Token type mismatch: expected {expected_type.value}, got {payload.get('type')}")
                return None
            
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def _generate_api_key(self) -> str:
        """Generate a secure API key"""
        # Format: tpro_live_<random_string>
        prefix = "tpro_live_" if os.getenv('ENVIRONMENT') == 'production' else "tpro_test_"
        random_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        return f"{prefix}{random_part}"
    
    def _hash_api_key(self, api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    # User Registration and Management
    
    def register_user(self, email: str, username: str, password: str,
                     full_name: Optional[str] = None,
                     organization: Optional[str] = None,
                     provider: AuthProvider = AuthProvider.LOCAL) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Register a new user
        Returns: (success, message, user_data)
        """
        db = self._get_db()
        try:
            # Check if user exists
            existing_user = db.query(User).filter(
                or_(User.email == email, User.username == username)
            ).first()
            
            if existing_user:
                if existing_user.email == email:
                    return False, "Email already registered", None
                else:
                    return False, "Username already taken", None
            
            # Create user
            user = User(
                email=email,
                username=username,
                password_hash=self._hash_password(password) if provider == AuthProvider.LOCAL else None,
                full_name=full_name,
                auth_provider=provider.value,
                organization=organization,
                role=UserRole.USER,
                is_active=True,
                is_verified=False,
                verification_token=secrets.token_urlsafe(32)
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Send verification email (async)
            self._send_verification_email(user)
            
            # Log registration
            self._log_auth_event(user.id, "user_registered", {"provider": provider.value})
            
            return True, "User registered successfully", {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "requires_verification": True
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Registration error: {e}")
            return False, "Registration failed", None
        finally:
            db.close()
    
    def authenticate_user(self, username_or_email: str, password: str,
                         ip_address: Optional[str] = None,
                         user_agent: Optional[str] = None,
                         platform: str = "web") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Authenticate user and create session
        Returns: (success, message, auth_data)
        """
        db = self._get_db()
        try:
            # Find user
            user = db.query(User).filter(
                or_(User.email == username_or_email, User.username == username_or_email)
            ).first()
            
            if not user:
                return False, "Invalid credentials", None
            
            # Check if user is locked out
            if self._is_user_locked_out(user):
                return False, "Account temporarily locked due to too many failed attempts", None
            
            # Verify password
            if not self._verify_password(password, user.password_hash):
                self._record_failed_login(user)
                return False, "Invalid credentials", None
            
            # Check if user is active
            if not user.is_active:
                return False, "Account is disabled", None
            
            # Check if email verification is required
            if not user.is_verified and os.getenv('REQUIRE_EMAIL_VERIFICATION') == 'true':
                return False, "Email verification required", None
            
            # Check if MFA is enabled
            if user.mfa_enabled:
                # Generate MFA session token
                mfa_token = self._generate_token(
                    {"user_id": user.id, "purpose": "mfa"},
                    TokenType.MFA
                )
                return True, "MFA required", {
                    "mfa_required": True,
                    "mfa_token": mfa_token,
                    "mfa_methods": self._get_user_mfa_methods(user)
                }
            
            # Generate tokens
            access_token = self._generate_token(
                {
                    "user_id": user.id,
                    "username": user.username,
                    "role": user.role.value,
                    "platform": platform
                },
                TokenType.ACCESS
            )
            
            refresh_token = self._generate_token(
                {
                    "user_id": user.id,
                    "username": user.username,
                    "platform": platform
                },
                TokenType.REFRESH
            )
            
            # Create session
            session = UserSession(
                user_id=user.id,
                session_id=secrets.token_urlsafe(32),
                ip_address=ip_address,
                user_agent=user_agent,
                platform=platform,
                expires_at=datetime.utcnow() + self.token_expiry[TokenType.REFRESH],
                refresh_token_hash=self._hash_api_key(refresh_token)
            )
            
            db.add(session)
            
            # Update last login
            user.last_login = datetime.utcnow()
            user.failed_login_attempts = 0
            
            db.commit()
            
            # Log successful login
            self._log_auth_event(user.id, "user_login", {
                "platform": platform,
                "ip": ip_address
            })
            
            return True, "Authentication successful", {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": int(self.token_expiry[TokenType.ACCESS].total_seconds()),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "role": user.role.value,
                    "organization": user.organization,
                    "teams": [{"id": tm.team_id, "name": tm.team.name, "role": tm.role.value} 
                             for tm in user.team_memberships]
                }
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Authentication error: {e}")
            return False, "Authentication failed", None
        finally:
            db.close()
    
    def refresh_access_token(self, refresh_token: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Refresh access token using refresh token
        Returns: (success, message, token_data)
        """
        payload = self._decode_token(refresh_token, TokenType.REFRESH)
        if not payload:
            return False, "Invalid refresh token", None
        
        db = self._get_db()
        try:
            # Verify session
            session = db.query(UserSession).filter(
                and_(
                    UserSession.user_id == payload['user_id'],
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.utcnow()
                )
            ).first()
            
            if not session:
                return False, "Session expired or invalid", None
            
            # Verify refresh token matches session
            if not self._verify_refresh_token(refresh_token, session.refresh_token_hash):
                return False, "Invalid refresh token", None
            
            # Get user
            user = db.query(User).filter(User.id == payload['user_id']).first()
            if not user or not user.is_active:
                return False, "User not found or inactive", None
            
            # Generate new access token
            access_token = self._generate_token(
                {
                    "user_id": user.id,
                    "username": user.username,
                    "role": user.role.value,
                    "platform": payload.get('platform', 'web')
                },
                TokenType.ACCESS
            )
            
            return True, "Token refreshed successfully", {
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": int(self.token_expiry[TokenType.ACCESS].total_seconds())
            }
            
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return False, "Token refresh failed", None
        finally:
            db.close()
    
    def create_api_key(self, user_id: int, name: str, 
                      scopes: List[str] = None,
                      expires_in_days: Optional[int] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Create API key for programmatic access
        Returns: (success, message, api_key_data)
        """
        db = self._get_db()
        try:
            # Verify user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, "User not found", None
            
            # Generate API key
            api_key = self._generate_api_key()
            key_hash = self._hash_api_key(api_key)
            
            # Set expiration
            expires_at = None
            if expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            
            # Create API key record
            api_key_record = APIKey(
                user_id=user_id,
                name=name,
                key_hash=key_hash,
                scopes=scopes or ["read", "write"],
                expires_at=expires_at,
                is_active=True
            )
            
            db.add(api_key_record)
            db.commit()
            db.refresh(api_key_record)
            
            # Log API key creation
            self._log_auth_event(user_id, "api_key_created", {"key_id": api_key_record.id})
            
            return True, "API key created successfully", {
                "id": api_key_record.id,
                "key": api_key,  # Only returned once
                "name": name,
                "created_at": api_key_record.created_at.isoformat(),
                "expires_at": expires_at.isoformat() if expires_at else None,
                "scopes": api_key_record.scopes
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"API key creation error: {e}")
            return False, "Failed to create API key", None
        finally:
            db.close()
    
    def validate_api_key(self, api_key: str) -> Tuple[bool, Optional[User]]:
        """
        Validate API key and return associated user
        Returns: (is_valid, user)
        """
        db = self._get_db()
        try:
            key_hash = self._hash_api_key(api_key)
            
            # Find API key
            api_key_record = db.query(APIKey).filter(
                and_(
                    APIKey.key_hash == key_hash,
                    APIKey.is_active == True
                )
            ).first()
            
            if not api_key_record:
                return False, None
            
            # Check expiration
            if api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
                return False, None
            
            # Update last used
            api_key_record.last_used_at = datetime.utcnow()
            db.commit()
            
            # Get user
            user = api_key_record.user
            if not user or not user.is_active:
                return False, None
            
            return True, user
            
        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return False, None
        finally:
            db.close()
    
    # Helper methods
    
    def _is_user_locked_out(self, user: User) -> bool:
        """Check if user is locked out due to failed attempts"""
        if user.locked_until and user.locked_until > datetime.utcnow():
            return True
        return False
    
    def _record_failed_login(self, user: User):
        """Record failed login attempt"""
        db = self._get_db()
        try:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            
            if user.failed_login_attempts >= self.max_login_attempts:
                user.locked_until = datetime.utcnow() + self.lockout_duration
            
            db.commit()
        except:
            db.rollback()
        finally:
            db.close()
    
    def _verify_refresh_token(self, token: str, stored_hash: str) -> bool:
        """Verify refresh token against stored hash"""
        return self._hash_api_key(token) == stored_hash
    
    def _get_user_mfa_methods(self, user: User) -> List[str]:
        """Get user's available MFA methods"""
        methods = []
        if user.mfa_totp_secret:
            methods.append("totp")
        if user.mfa_sms_enabled:
            methods.append("sms")
        if user.mfa_email_enabled:
            methods.append("email")
        return methods
    
    def _send_verification_email(self, user: User):
        """Send email verification (implement based on email service)"""
        # This would integrate with your email service
        logger.info(f"Sending verification email to {user.email}")
    
    def _log_auth_event(self, user_id: int, event_type: str, metadata: Dict[str, Any]):
        """Log authentication event for audit trail"""
        # This would integrate with your audit logging system
        logger.info(f"Auth event: {event_type} for user {user_id}", extra=metadata)