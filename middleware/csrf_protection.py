#!/usr/bin/env python3
"""
CSRF Protection Middleware for Audio/Video Transcription App
Implements token-based CSRF protection for forms and API calls
"""

import secrets
import time
import hmac
import hashlib
import logging
from typing import Optional, Tuple
from datetime import datetime, timedelta
import streamlit as st
from functools import wraps

logger = logging.getLogger(__name__)

class CSRFProtection:
    """CSRF token generation and validation"""
    
    def __init__(self):
        # Secret key for CSRF token generation (should be from environment in production)
        self.secret_key = secrets.token_bytes(32)
        
        # Token expiration time (2 hours)
        self.token_lifetime = 7200
        
        # Store used tokens to prevent replay attacks
        self.used_tokens = set()
        self.last_cleanup = time.time()
        self.cleanup_interval = 3600  # 1 hour
    
    def _cleanup_old_tokens(self):
        """Periodically clean up used tokens to prevent memory growth"""
        current_time = time.time()
        
        if current_time - self.last_cleanup > self.cleanup_interval:
            # In a real implementation, we'd track token timestamps
            # For now, just clear if the set gets too large
            if len(self.used_tokens) > 10000:
                self.used_tokens.clear()
                logger.info("Cleared CSRF used tokens cache")
            
            self.last_cleanup = current_time
    
    def generate_token(self, session_id: str, user_id: Optional[int] = None) -> str:
        """Generate a CSRF token for a session"""
        # Create token data
        timestamp = int(time.time())
        user_str = str(user_id) if user_id else "anonymous"
        
        # Create message to sign
        message = f"{session_id}:{user_str}:{timestamp}"
        
        # Generate HMAC signature
        signature = hmac.new(
            self.secret_key,
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Create token
        token = f"{message}:{signature}"
        
        # Encode to make it URL-safe
        import base64
        encoded_token = base64.urlsafe_b64encode(token.encode()).decode()
        
        logger.debug(f"Generated CSRF token for session {session_id}")
        return encoded_token
    
    def validate_token(self, token: str, session_id: str, user_id: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        Validate a CSRF token
        Returns: (is_valid, error_message)
        """
        self._cleanup_old_tokens()
        
        try:
            # Decode token
            import base64
            decoded_token = base64.urlsafe_b64decode(token.encode()).decode()
            
            # Check if token was already used
            if decoded_token in self.used_tokens:
                return False, "Token has already been used"
            
            # Parse token
            parts = decoded_token.split(':')
            if len(parts) != 4:
                return False, "Invalid token format"
            
            token_session_id, token_user_str, token_timestamp, token_signature = parts
            
            # Verify session ID matches
            if token_session_id != session_id:
                return False, "Token session mismatch"
            
            # Verify user ID matches
            expected_user_str = str(user_id) if user_id else "anonymous"
            if token_user_str != expected_user_str:
                return False, "Token user mismatch"
            
            # Check token age
            token_age = int(time.time()) - int(token_timestamp)
            if token_age > self.token_lifetime:
                return False, "Token has expired"
            
            # Verify signature
            message = f"{token_session_id}:{token_user_str}:{token_timestamp}"
            expected_signature = hmac.new(
                self.secret_key,
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(token_signature, expected_signature):
                return False, "Invalid token signature"
            
            # Mark token as used
            self.used_tokens.add(decoded_token)
            
            logger.debug(f"CSRF token validated successfully for session {session_id}")
            return True, None
            
        except Exception as e:
            logger.warning(f"CSRF token validation error: {e}")
            return False, "Token validation failed"
    
    def get_token_from_session(self) -> Optional[str]:
        """Get or create CSRF token for current session"""
        if 'csrf_token' not in st.session_state:
            # Generate new token
            session_id = st.session_state.get('session_id', 'default')
            
            from auth import get_current_user
            user = get_current_user()
            user_id = user.id if user else None
            
            st.session_state.csrf_token = self.generate_token(session_id, user_id)
        
        return st.session_state.csrf_token
    
    def refresh_token(self):
        """Force refresh of CSRF token"""
        if 'csrf_token' in st.session_state:
            del st.session_state.csrf_token
        return self.get_token_from_session()

# Global CSRF protection instance
csrf_protection = CSRFProtection()

def csrf_protect(func):
    """Decorator to protect functions with CSRF validation"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get token from form data or headers
        token = kwargs.get('csrf_token') or st.session_state.get('submitted_csrf_token')
        
        if not token:
            st.error("CSRF token missing. Please refresh the page.")
            st.stop()
        
        # Get session info
        session_id = st.session_state.get('session_id', 'default')
        
        from auth import get_current_user
        user = get_current_user()
        user_id = user.id if user else None
        
        # Validate token
        is_valid, error_msg = csrf_protection.validate_token(token, session_id, user_id)
        
        if not is_valid:
            logger.warning(f"CSRF validation failed: {error_msg}")
            st.error(f"Security validation failed: {error_msg}. Please refresh the page.")
            st.stop()
        
        # Remove csrf_token from kwargs if present
        if 'csrf_token' in kwargs:
            del kwargs['csrf_token']
        
        return func(*args, **kwargs)
    
    return wrapper

def add_csrf_token_to_form():
    """Add CSRF token to current form (call within st.form)"""
    token = csrf_protection.get_token_from_session()
    
    # Hidden field workaround for Streamlit
    st.session_state.submitted_csrf_token = token
    
    # Display token in a hidden way (for forms that need it)
    st.markdown(
        f'<input type="hidden" name="csrf_token" value="{token}">',
        unsafe_allow_html=True
    )
    
    return token

def validate_api_csrf_token(request_headers: dict, session_id: str, user_id: Optional[int] = None) -> Tuple[bool, Optional[str]]:
    """Validate CSRF token from API request headers"""
    token = request_headers.get('X-CSRF-Token')
    
    if not token:
        return False, "CSRF token missing in headers"
    
    return csrf_protection.validate_token(token, session_id, user_id)

def get_csrf_headers() -> dict:
    """Get headers with CSRF token for API calls"""
    token = csrf_protection.get_token_from_session()
    return {
        'X-CSRF-Token': token,
        'X-Requested-With': 'XMLHttpRequest'
    }

# Middleware for Streamlit pages
def apply_csrf_protection():
    """Initialize CSRF protection for current page"""
    # Ensure session has an ID
    if 'session_id' not in st.session_state:
        st.session_state.session_id = secrets.token_urlsafe(16)
    
    # Ensure CSRF token exists
    csrf_protection.get_token_from_session()
    
    # Add custom CSS to hide CSRF inputs
    st.markdown("""
    <style>
    input[name="csrf_token"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)