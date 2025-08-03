#!/usr/bin/env python3
"""
User Authentication and Account Management System (Task 46)
Enterprise-grade user authentication with secure password handling, MFA, and profile management
"""

import streamlit as st
import hashlib
import secrets
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
import bcrypt
import pyotp
import qrcode
from io import BytesIO
import base64
import re
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

logger = logging.getLogger(__name__)

@dataclass
class User:
    """User data model"""
    user_id: str
    username: str
    email: str
    password_hash: str
    salt: str
    full_name: str
    role: str  # 'admin', 'pro', 'free'
    subscription_tier: str  # 'free', 'pro', 'enterprise'
    created_at: str
    last_login: Optional[str]
    is_active: bool
    email_verified: bool
    mfa_enabled: bool
    mfa_secret: Optional[str]
    profile_data: Dict[str, Any]
    api_keys: List[Dict[str, str]]
    usage_stats: Dict[str, Any]

@dataclass
class UserSession:
    """User session data"""
    session_id: str
    user_id: str
    username: str
    role: str
    subscription_tier: str
    created_at: str
    expires_at: str
    ip_address: str
    user_agent: str
    is_active: bool

class DatabaseManager:
    """SQLite database manager for user data"""
    
    def __init__(self, db_path: str = "user_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Users table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id TEXT PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        salt TEXT NOT NULL,
                        full_name TEXT NOT NULL,
                        role TEXT DEFAULT 'free',
                        subscription_tier TEXT DEFAULT 'free',
                        created_at TEXT NOT NULL,
                        last_login TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        email_verified BOOLEAN DEFAULT 0,
                        mfa_enabled BOOLEAN DEFAULT 0,
                        mfa_secret TEXT,
                        profile_data TEXT DEFAULT '{}',
                        api_keys TEXT DEFAULT '[]',
                        usage_stats TEXT DEFAULT '{}'
                    )
                """)
                
                # Sessions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        username TEXT NOT NULL,
                        role TEXT NOT NULL,
                        subscription_tier TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        expires_at TEXT NOT NULL,
                        ip_address TEXT,
                        user_agent TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)
                
                # Password reset tokens table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS password_reset_tokens (
                        token TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        expires_at TEXT NOT NULL,
                        used BOOLEAN DEFAULT 0,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)
                
                # Email verification tokens table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS email_verification_tokens (
                        token TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        expires_at TEXT NOT NULL,
                        used BOOLEAN DEFAULT 0,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)
                
                # Audit log table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS audit_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT,
                        action TEXT NOT NULL,
                        details TEXT,
                        ip_address TEXT,
                        user_agent TEXT,
                        timestamp TEXT NOT NULL
                    )
                """)
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def create_user(self, user: User) -> bool:
        """Create a new user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (
                        user_id, username, email, password_hash, salt, full_name,
                        role, subscription_tier, created_at, is_active, email_verified,
                        mfa_enabled, mfa_secret, profile_data, api_keys, usage_stats
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user.user_id, user.username, user.email, user.password_hash,
                    user.salt, user.full_name, user.role, user.subscription_tier,
                    user.created_at, user.is_active, user.email_verified,
                    user.mfa_enabled, user.mfa_secret, json.dumps(user.profile_data),
                    json.dumps(user.api_keys), json.dumps(user.usage_stats)
                ))
                conn.commit()
                return True
        except sqlite3.IntegrityError as e:
            logger.error(f"User creation failed - integrity error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_user(row)
                return None
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_user(row)
                return None
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_user(row)
                return None
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    def update_user(self, user: User) -> bool:
        """Update user data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users SET
                        username = ?, email = ?, password_hash = ?, salt = ?,
                        full_name = ?, role = ?, subscription_tier = ?,
                        last_login = ?, is_active = ?, email_verified = ?,
                        mfa_enabled = ?, mfa_secret = ?, profile_data = ?,
                        api_keys = ?, usage_stats = ?
                    WHERE user_id = ?
                """, (
                    user.username, user.email, user.password_hash, user.salt,
                    user.full_name, user.role, user.subscription_tier,
                    user.last_login, user.is_active, user.email_verified,
                    user.mfa_enabled, user.mfa_secret, json.dumps(user.profile_data),
                    json.dumps(user.api_keys), json.dumps(user.usage_stats),
                    user.user_id
                ))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False
    
    def create_session(self, session: UserSession) -> bool:
        """Create user session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sessions (
                        session_id, user_id, username, role, subscription_tier,
                        created_at, expires_at, ip_address, user_agent, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session.session_id, session.user_id, session.username,
                    session.role, session.subscription_tier, session.created_at,
                    session.expires_at, session.ip_address, session.user_agent,
                    session.is_active
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get session by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM sessions WHERE session_id = ? AND is_active = 1", (session_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_session(row)
                return None
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE sessions SET is_active = 0 WHERE session_id = ?", (session_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error invalidating session: {e}")
            return False
    
    def log_audit_event(self, user_id: Optional[str], action: str, details: str = "", 
                       ip_address: str = "", user_agent: str = ""):
        """Log audit event"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO audit_log (user_id, action, details, ip_address, user_agent, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, action, details, ip_address, user_agent, datetime.now().isoformat()))
                conn.commit()
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")
    
    def _row_to_user(self, row) -> User:
        """Convert database row to User object"""
        return User(
            user_id=row[0],
            username=row[1],
            email=row[2],
            password_hash=row[3],
            salt=row[4],
            full_name=row[5],
            role=row[6],
            subscription_tier=row[7],
            created_at=row[8],
            last_login=row[9],
            is_active=bool(row[10]),
            email_verified=bool(row[11]),
            mfa_enabled=bool(row[12]),
            mfa_secret=row[13],
            profile_data=json.loads(row[14]) if row[14] else {},
            api_keys=json.loads(row[15]) if row[15] else [],
            usage_stats=json.loads(row[16]) if row[16] else {}
        )
    
    def _row_to_session(self, row) -> UserSession:
        """Convert database row to UserSession object"""
        return UserSession(
            session_id=row[0],
            user_id=row[1],
            username=row[2],
            role=row[3],
            subscription_tier=row[4],
            created_at=row[5],
            expires_at=row[6],
            ip_address=row[7],
            user_agent=row[8],
            is_active=bool(row[9])
        )

class PasswordManager:
    """Secure password handling with bcrypt"""
    
    @staticmethod
    def generate_salt() -> str:
        """Generate a random salt"""
        return secrets.token_hex(32)
    
    @staticmethod
    def hash_password(password: str, salt: str) -> str:
        """Hash password with salt using bcrypt"""
        # Combine password and salt
        password_with_salt = (password + salt).encode('utf-8')
        # Generate bcrypt hash
        hashed = bcrypt.hashpw(password_with_salt, bcrypt.gensalt())
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, salt: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            password_with_salt = (password + salt).encode('utf-8')
            return bcrypt.checkpw(password_with_salt, hashed_password.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
        """Validate password strength"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors

class MFAManager:
    """Multi-Factor Authentication manager"""
    
    @staticmethod
    def generate_secret() -> str:
        """Generate MFA secret"""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_code(username: str, secret: str, issuer: str = "Transcription App") -> str:
        """Generate QR code for MFA setup"""
        try:
            # Create TOTP URI
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=username,
                issuer_name=issuer
            )
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            # Create QR code image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return img_str
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return ""
    
    @staticmethod
    def verify_totp(secret: str, token: str) -> bool:
        """Verify TOTP token"""
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=1)  # Allow 1 window tolerance
        except Exception as e:
            logger.error(f"Error verifying TOTP: {e}")
            return False

class EmailManager:
    """Email manager for verification and notifications"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_username)
    
    def send_verification_email(self, user_email: str, username: str, verification_token: str) -> bool:
        """Send email verification"""
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP credentials not configured - email verification disabled")
                return False
            
            subject = "Verify Your Email - Transcription App"
            
            # Create verification URL (would be actual URL in production)
            verification_url = f"http://localhost:8501/verify-email?token={verification_token}"
            
            body = f"""
            Hi {username},
            
            Thank you for registering with Transcription App!
            
            Please click the link below to verify your email address:
            {verification_url}
            
            If you didn't create this account, please ignore this email.
            
            Best regards,
            The Transcription App Team
            """
            
            return self._send_email(user_email, subject, body)
            
        except Exception as e:
            logger.error(f"Error sending verification email: {e}")
            return False
    
    def send_password_reset_email(self, user_email: str, username: str, reset_token: str) -> bool:
        """Send password reset email"""
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP credentials not configured - password reset disabled")
                return False
            
            subject = "Password Reset - Transcription App"
            
            # Create reset URL (would be actual URL in production)
            reset_url = f"http://localhost:8501/reset-password?token={reset_token}"
            
            body = f"""
            Hi {username},
            
            You requested a password reset for your Transcription App account.
            
            Please click the link below to reset your password:
            {reset_url}
            
            This link will expire in 1 hour.
            
            If you didn't request this reset, please ignore this email.
            
            Best regards,
            The Transcription App Team
            """
            
            return self._send_email(user_email, subject, body)
            
        except Exception as e:
            logger.error(f"Error sending password reset email: {e}")
            return False
    
    def _send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send email via SMTP"""
        try:
            msg = MimeMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            
            text = msg.as_string()
            server.sendmail(self.from_email, to_email, text)
            server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

class UserAuthenticationManager:
    """Main user authentication manager"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.password_manager = PasswordManager()
        self.mfa_manager = MFAManager()
        self.email_manager = EmailManager()
    
    def register_user(self, username: str, email: str, password: str, full_name: str) -> Tuple[bool, str]:
        """Register a new user"""
        try:
            # Validate input
            if not username or not email or not password or not full_name:
                return False, "All fields are required"
            
            # Validate email format
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                return False, "Invalid email format"
            
            # Validate username
            if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
                return False, "Username must be 3-20 characters, letters, numbers, and underscores only"
            
            # Validate password strength
            is_strong, password_errors = self.password_manager.validate_password_strength(password)
            if not is_strong:
                return False, "; ".join(password_errors)
            
            # Check if user already exists
            if self.db.get_user_by_username(username):
                return False, "Username already exists"
            
            if self.db.get_user_by_email(email):
                return False, "Email already registered"
            
            # Create user
            user_id = secrets.token_urlsafe(32)
            salt = self.password_manager.generate_salt()
            password_hash = self.password_manager.hash_password(password, salt)
            
            user = User(
                user_id=user_id,
                username=username,
                email=email,
                password_hash=password_hash,
                salt=salt,
                full_name=full_name,
                role='free',
                subscription_tier='free',
                created_at=datetime.now().isoformat(),
                last_login=None,
                is_active=True,
                email_verified=False,
                mfa_enabled=False,
                mfa_secret=None,
                profile_data={},
                api_keys=[],
                usage_stats={'transcriptions': 0, 'processing_time': 0, 'storage_used': 0}
            )
            
            if self.db.create_user(user):
                # Log audit event
                self.db.log_audit_event(user_id, "USER_REGISTERED", f"Username: {username}, Email: {email}")
                
                # Send verification email (if SMTP configured)
                verification_token = secrets.token_urlsafe(32)
                self.email_manager.send_verification_email(email, username, verification_token)
                
                return True, "User registered successfully! Please check your email for verification."
            else:
                return False, "Failed to create user account"
                
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return False, "Registration failed due to system error"
    
    def authenticate_user(self, username: str, password: str, mfa_token: str = "") -> Tuple[bool, str, Optional[User]]:
        """Authenticate user login"""
        try:
            # Get user
            user = self.db.get_user_by_username(username)
            if not user:
                # Log failed attempt
                self.db.log_audit_event(None, "LOGIN_FAILED", f"Username not found: {username}")
                return False, "Invalid username or password", None
            
            # Check if user is active
            if not user.is_active:
                self.db.log_audit_event(user.user_id, "LOGIN_FAILED", "Account disabled")
                return False, "Account is disabled", None
            
            # Verify password
            if not self.password_manager.verify_password(password, user.salt, user.password_hash):
                self.db.log_audit_event(user.user_id, "LOGIN_FAILED", "Invalid password")
                return False, "Invalid username or password", None
            
            # Check MFA if enabled
            if user.mfa_enabled:
                if not mfa_token:
                    return False, "MFA_REQUIRED", user
                
                if not self.mfa_manager.verify_totp(user.mfa_secret, mfa_token):
                    self.db.log_audit_event(user.user_id, "LOGIN_FAILED", "Invalid MFA token")
                    return False, "Invalid MFA token", None
            
            # Update last login
            user.last_login = datetime.now().isoformat()
            self.db.update_user(user)
            
            # Log successful login
            self.db.log_audit_event(user.user_id, "LOGIN_SUCCESS", f"Username: {username}")
            
            return True, "Login successful", user
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return False, "Authentication failed due to system error", None
    
    def create_session(self, user: User, ip_address: str = "", user_agent: str = "") -> Optional[UserSession]:
        """Create user session"""
        try:
            session_id = secrets.token_urlsafe(32)
            expires_at = (datetime.now() + timedelta(hours=24)).isoformat()  # 24 hour session
            
            session = UserSession(
                session_id=session_id,
                user_id=user.user_id,
                username=user.username,
                role=user.role,
                subscription_tier=user.subscription_tier,
                created_at=datetime.now().isoformat(),
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
                is_active=True
            )
            
            if self.db.create_session(session):
                self.db.log_audit_event(user.user_id, "SESSION_CREATED", f"Session ID: {session_id}")
                return session
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return None
    
    def validate_session(self, session_id: str) -> Optional[UserSession]:
        """Validate user session"""
        try:
            session = self.db.get_session(session_id)
            if not session:
                return None
            
            # Check if session is expired
            expires_at = datetime.fromisoformat(session.expires_at)
            if datetime.now() > expires_at:
                self.db.invalidate_session(session_id)
                return None
            
            return session
            
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return None
    
    def logout_user(self, session_id: str) -> bool:
        """Logout user and invalidate session"""
        try:
            session = self.db.get_session(session_id)
            if session:
                self.db.log_audit_event(session.user_id, "LOGOUT", f"Session ID: {session_id}")
                return self.db.invalidate_session(session_id)
            return False
        except Exception as e:
            logger.error(f"Error logging out user: {e}")
            return False
    
    def setup_mfa(self, user_id: str) -> Tuple[bool, str, str]:
        """Setup MFA for user"""
        try:
            user = self.db.get_user_by_id(user_id)
            if not user:
                return False, "User not found", ""
            
            # Generate MFA secret
            secret = self.mfa_manager.generate_secret()
            
            # Generate QR code
            qr_code = self.mfa_manager.generate_qr_code(user.username, secret)
            
            # Update user with MFA secret (but don't enable yet)
            user.mfa_secret = secret
            self.db.update_user(user)
            
            return True, secret, qr_code
            
        except Exception as e:
            logger.error(f"Error setting up MFA: {e}")
            return False, "MFA setup failed", ""
    
    def enable_mfa(self, user_id: str, token: str) -> Tuple[bool, str]:
        """Enable MFA after verification"""
        try:
            user = self.db.get_user_by_id(user_id)
            if not user or not user.mfa_secret:
                return False, "MFA not set up"
            
            # Verify token
            if not self.mfa_manager.verify_totp(user.mfa_secret, token):
                return False, "Invalid MFA token"
            
            # Enable MFA
            user.mfa_enabled = True
            self.db.update_user(user)
            
            self.db.log_audit_event(user_id, "MFA_ENABLED", "Multi-factor authentication enabled")
            
            return True, "MFA enabled successfully"
            
        except Exception as e:
            logger.error(f"Error enabling MFA: {e}")
            return False, "Failed to enable MFA"
    
    def disable_mfa(self, user_id: str, password: str) -> Tuple[bool, str]:
        """Disable MFA with password confirmation"""
        try:
            user = self.db.get_user_by_id(user_id)
            if not user:
                return False, "User not found"
            
            # Verify password
            if not self.password_manager.verify_password(password, user.salt, user.password_hash):
                return False, "Invalid password"
            
            # Disable MFA
            user.mfa_enabled = False
            user.mfa_secret = None
            self.db.update_user(user)
            
            self.db.log_audit_event(user_id, "MFA_DISABLED", "Multi-factor authentication disabled")
            
            return True, "MFA disabled successfully"
            
        except Exception as e:
            logger.error(f"Error disabling MFA: {e}")
            return False, "Failed to disable MFA"

# Global authentication manager instance
auth_manager = UserAuthenticationManager()