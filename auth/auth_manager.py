#!/usr/bin/env python3
"""
Authentication Manager for Audio/Video Transcription App
Handles user registration, login, sessions, and password management
"""

import os
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
import hashlib
import jwt
from passlib.context import CryptContext
import streamlit as st
from email_validator import validate_email, EmailNotValidError

from database.models import User, Session, UserRole, get_db_session

logger = logging.getLogger(__name__)

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
SESSION_EXPIRE_HOURS = 24 * 7  # 7 days

class AuthManager:
    """Manages authentication and user sessions"""
    
    def __init__(self):
        self.db = get_db_session()
        self._ensure_jwt_secret()
    
    def _ensure_jwt_secret(self):
        """Ensure JWT secret is set"""
        if os.getenv('JWT_SECRET_KEY') is None:
            logger.warning("JWT_SECRET_KEY not set in environment, using generated key")
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, user_id: int) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "user_id": user_id,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    
    def decode_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
    
    def validate_email_address(self, email: str) -> Tuple[bool, Optional[str]]:
        """Validate email address format"""
        try:
            validated = validate_email(email)
            return True, validated.email
        except EmailNotValidError as e:
            return False, str(e)
    
    def register_user(self, email: str, username: str, password: str, 
                     full_name: Optional[str] = None) -> Tuple[bool, Optional[User], Optional[str]]:
        """Register a new user"""
        try:
            # Validate email
            is_valid, validated_email = self.validate_email_address(email)
            if not is_valid:
                return False, None, f"Invalid email: {validated_email}"
            
            # Check if user already exists
            existing_user = self.db.query(User).filter(
                (User.email == validated_email) | (User.username == username)
            ).first()
            
            if existing_user:
                if existing_user.email == validated_email:
                    return False, None, "Email already registered"
                else:
                    return False, None, "Username already taken"
            
            # Validate password strength
            if len(password) < 8:
                return False, None, "Password must be at least 8 characters long"
            
            # Create verification token
            verification_token = secrets.token_urlsafe(32)
            
            # Create new user
            new_user = User(
                email=validated_email,
                username=username,
                password_hash=self.hash_password(password),
                full_name=full_name,
                verification_token=verification_token,
                role=UserRole.USER
            )
            
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            
            logger.info(f"New user registered: {username} ({validated_email})")
            
            # TODO: Send verification email
            
            return True, new_user, None
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error registering user: {e}")
            return False, None, "Registration failed. Please try again."
    
    def login_user(self, username_or_email: str, password: str, 
                  ip_address: Optional[str] = None, 
                  user_agent: Optional[str] = None) -> Tuple[bool, Optional[User], Optional[str], Optional[str]]:
        """Login user and create session"""
        try:
            # Find user by email or username
            user = self.db.query(User).filter(
                (User.email == username_or_email) | (User.username == username_or_email)
            ).first()
            
            if not user:
                return False, None, None, "Invalid username/email or password"
            
            # Verify password
            if not self.verify_password(password, user.password_hash):
                return False, None, None, "Invalid username/email or password"
            
            # Check if user is active
            if not user.is_active:
                return False, None, None, "Account is deactivated"
            
            # Check if user is verified (optional, can be enforced)
            # if not user.is_verified:
            #     return False, None, None, "Please verify your email first"
            
            # Create session
            session_id = secrets.token_urlsafe(32)
            session_token = self.create_access_token(user.id)
            
            # Deactivate old sessions
            old_sessions = self.db.query(Session).filter(
                Session.user_id == user.id,
                Session.is_active == True
            ).all()
            
            for old_session in old_sessions:
                old_session.is_active = False
            
            # Create new session
            new_session = Session(
                session_id=session_id,
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=datetime.utcnow() + timedelta(hours=SESSION_EXPIRE_HOURS)
            )
            
            self.db.add(new_session)
            
            # Update last login
            user.last_login = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"User logged in: {user.username}")
            
            return True, user, session_id, session_token
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during login: {e}")
            return False, None, None, "Login failed. Please try again."
    
    def logout_user(self, session_id: str) -> bool:
        """Logout user by invalidating session"""
        try:
            session = self.db.query(Session).filter(
                Session.session_id == session_id,
                Session.is_active == True
            ).first()
            
            if session:
                session.is_active = False
                self.db.commit()
                logger.info(f"User logged out: session {session_id}")
                return True
            
            return False
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during logout: {e}")
            return False
    
    def get_user_from_session(self, session_id: str) -> Optional[User]:
        """Get user from session ID"""
        try:
            session = self.db.query(Session).filter(
                Session.session_id == session_id,
                Session.is_active == True,
                Session.expires_at > datetime.utcnow()
            ).first()
            
            if session:
                return session.user
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user from session: {e}")
            return None
    
    def get_user_from_token(self, token: str) -> Optional[User]:
        """Get user from JWT token"""
        try:
            payload = self.decode_access_token(token)
            if not payload:
                return None
            
            user_id = payload.get("user_id")
            if not user_id:
                return None
            
            user = self.db.query(User).filter(
                User.id == user_id,
                User.is_active == True
            ).first()
            
            return user
            
        except Exception as e:
            logger.error(f"Error getting user from token: {e}")
            return None
    
    def request_password_reset(self, email: str) -> Tuple[bool, Optional[str]]:
        """Request password reset"""
        try:
            user = self.db.query(User).filter(User.email == email).first()
            
            if not user:
                # Don't reveal if email exists
                return True, "If the email exists, a reset link has been sent"
            
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            user.reset_token = reset_token
            user.reset_token_expires = datetime.utcnow() + timedelta(hours=24)
            
            self.db.commit()
            
            logger.info(f"Password reset requested for: {email}")
            
            # TODO: Send reset email
            
            return True, "If the email exists, a reset link has been sent"
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error requesting password reset: {e}")
            return False, "Failed to process request"
    
    def reset_password(self, reset_token: str, new_password: str) -> Tuple[bool, Optional[str]]:
        """Reset password using token"""
        try:
            user = self.db.query(User).filter(
                User.reset_token == reset_token,
                User.reset_token_expires > datetime.utcnow()
            ).first()
            
            if not user:
                return False, "Invalid or expired reset token"
            
            # Validate password
            if len(new_password) < 8:
                return False, "Password must be at least 8 characters long"
            
            # Update password
            user.password_hash = self.hash_password(new_password)
            user.reset_token = None
            user.reset_token_expires = None
            
            # Invalidate all sessions
            sessions = self.db.query(Session).filter(
                Session.user_id == user.id,
                Session.is_active == True
            ).all()
            
            for session in sessions:
                session.is_active = False
            
            self.db.commit()
            
            logger.info(f"Password reset successful for user: {user.username}")
            
            return True, "Password reset successful"
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error resetting password: {e}")
            return False, "Failed to reset password"
    
    def verify_email(self, verification_token: str) -> Tuple[bool, Optional[str]]:
        """Verify user email"""
        try:
            user = self.db.query(User).filter(
                User.verification_token == verification_token
            ).first()
            
            if not user:
                return False, "Invalid verification token"
            
            user.is_verified = True
            user.verification_token = None
            
            self.db.commit()
            
            logger.info(f"Email verified for user: {user.username}")
            
            return True, "Email verified successfully"
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error verifying email: {e}")
            return False, "Failed to verify email"
    
    def update_user_profile(self, user_id: int, full_name: Optional[str] = None,
                          email: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """Update user profile"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            
            if not user:
                return False, "User not found"
            
            if full_name is not None:
                user.full_name = full_name
            
            if email is not None and email != user.email:
                # Validate new email
                is_valid, validated_email = self.validate_email_address(email)
                if not is_valid:
                    return False, f"Invalid email: {validated_email}"
                
                # Check if email already exists
                existing = self.db.query(User).filter(
                    User.email == validated_email,
                    User.id != user_id
                ).first()
                
                if existing:
                    return False, "Email already in use"
                
                user.email = validated_email
                # Could require re-verification here
            
            user.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Profile updated for user: {user.username}")
            
            return True, "Profile updated successfully"
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating profile: {e}")
            return False, "Failed to update profile"
    
    def delete_user_account(self, user_id: int, password: str) -> Tuple[bool, Optional[str]]:
        """Delete user account (soft delete by deactivating)"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            
            if not user:
                return False, "User not found"
            
            # Verify password
            if not self.verify_password(password, user.password_hash):
                return False, "Invalid password"
            
            # Deactivate user
            user.is_active = False
            
            # Invalidate all sessions
            sessions = self.db.query(Session).filter(
                Session.user_id == user_id,
                Session.is_active == True
            ).all()
            
            for session in sessions:
                session.is_active = False
            
            self.db.commit()
            
            logger.info(f"Account deactivated for user: {user.username}")
            
            return True, "Account deleted successfully"
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting account: {e}")
            return False, "Failed to delete account"

# Global auth manager instance
auth_manager = AuthManager()