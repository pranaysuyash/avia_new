#!/usr/bin/env python3
"""
Authentication UI Components for Audio/Video Transcription App
Handles login, signup, and authentication flow in Streamlit
"""

import streamlit as st
from typing import Optional, Callable
import logging
from functools import wraps

from .auth_manager import auth_manager
from database.models import User

# Import localization
try:
    from localization import get_text
    from localization.localized_ui import (
        localized_header, localized_button, localized_text_input,
        localized_info, localized_error, localized_success
    )
    LOCALIZATION_AVAILABLE = True
except ImportError:
    LOCALIZATION_AVAILABLE = False
    # Fallback functions if localization not available
    def get_text(key):
        return key
    def localized_button(key, **kwargs):
        return st.button(key, **kwargs)
    def localized_text_input(key, **kwargs):
        return st.text_input(key, **kwargs)
    def localized_error(key):
        st.error(key)
    def localized_success(key):
        st.success(key)
    def localized_info(key):
        st.info(key)

logger = logging.getLogger(__name__)

def init_auth_session_state():
    """Initialize authentication session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
    if 'auth_token' not in st.session_state:
        st.session_state.auth_token = None
    if 'show_login' not in st.session_state:
        st.session_state.show_login = True

def render_auth_page():
    """Render authentication page with login/signup forms"""
    init_auth_session_state()
    
    st.markdown("""
    <style>
    .auth-container {
        max-width: 400px;
        margin: auto;
        padding: 2rem;
    }
    .auth-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="auth-header">', unsafe_allow_html=True)
        st.title("🎤 Transcription App")
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Toggle between login and signup
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            render_login_form()
        
        with tab2:
            render_signup_form()
        
        # Add password reset link
        st.markdown("---")
        if st.button("Forgot Password?", key="forgot_password", help="Reset your password"):
            render_password_reset_form()

def render_login_form():
    """Render login form"""
    st.subheader("Welcome Back!")
    
    with st.form("login_form"):
        username_or_email = st.text_input(
            "Username or Email",
            placeholder="Enter your username or email",
            key="login_username"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="login_password"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            remember_me = st.checkbox("Remember me", key="remember_me")
        
        with col2:
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
        
        if submitted:
            if not username_or_email or not password:
                st.error("Please fill in all fields")
                return
            
            # Attempt login
            success, user, session_id, token = auth_manager.login_user(
                username_or_email,
                password,
                ip_address=None,  # Could get from request
                user_agent=None   # Could get from request
            )
            
            if success:
                # Update session state
                st.session_state.authenticated = True
                st.session_state.user = user
                st.session_state.session_id = session_id
                st.session_state.auth_token = token
                
                st.success(f"Welcome back, {user.username}!")
                st.balloons()
                
                # Redirect to main app
                st.rerun()
            else:
                st.error(token)  # Error message is in token parameter

def render_signup_form():
    """Render signup form"""
    st.subheader("Create Account")
    
    with st.form("signup_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            full_name = st.text_input(
                "Full Name",
                placeholder="John Doe",
                key="signup_fullname"
            )
        
        with col2:
            username = st.text_input(
                "Username",
                placeholder="johndoe",
                key="signup_username",
                help="Choose a unique username"
            )
        
        email = st.text_input(
            "Email",
            placeholder="john@example.com",
            key="signup_email"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Min 8 characters",
                key="signup_password"
            )
        
        with col2:
            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Re-enter password",
                key="signup_confirm_password"
            )
        
        terms = st.checkbox(
            "I agree to the Terms of Service and Privacy Policy",
            key="terms_agreement"
        )
        
        submitted = st.form_submit_button("Sign Up", type="primary", use_container_width=True)
        
        if submitted:
            # Validate inputs
            if not all([username, email, password, confirm_password]):
                st.error("Please fill in all required fields")
                return
            
            if password != confirm_password:
                st.error("Passwords do not match")
                return
            
            if not terms:
                st.error("Please agree to the terms and conditions")
                return
            
            # Attempt registration
            success, user, error = auth_manager.register_user(
                email=email,
                username=username,
                password=password,
                full_name=full_name if full_name else None
            )
            
            if success:
                st.success("Account created successfully! Please log in.")
                st.info("A verification email has been sent to your email address.")
                # Switch to login tab
                st.session_state.show_login = True
                st.rerun()
            else:
                st.error(error)

def render_password_reset_form():
    """Render password reset form in a dialog"""
    @st.dialog("Reset Password")
    def reset_dialog():
        st.write("Enter your email address to receive a password reset link.")
        
        email = st.text_input(
            "Email Address",
            placeholder="john@example.com",
            key="reset_email"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Cancel", use_container_width=True):
                st.rerun()
        
        with col2:
            if st.button("Send Reset Link", type="primary", use_container_width=True):
                if not email:
                    st.error("Please enter your email address")
                    return
                
                success, message = auth_manager.request_password_reset(email)
                
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    reset_dialog()

def render_user_menu():
    """Render user menu in sidebar when authenticated"""
    if st.session_state.authenticated and st.session_state.user:
        user = st.session_state.user
        
        with st.sidebar:
            st.markdown("---")
            st.markdown(f"### 👤 {user.username}")
            st.caption(f"{user.email}")
            
            if st.button("🚪 Logout", use_container_width=True):
                logout_user()
            
            with st.expander("⚙️ Account Settings"):
                if st.button("Edit Profile", use_container_width=True):
                    render_profile_editor()
                
                if st.button("Change Password", use_container_width=True):
                    render_password_change_dialog()

def logout_user():
    """Logout current user"""
    if st.session_state.session_id:
        auth_manager.logout_user(st.session_state.session_id)
    
    # Clear session state
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.session_id = None
    st.session_state.auth_token = None
    
    # Clear other session data
    for key in list(st.session_state.keys()):
        if key not in ['authenticated', 'user', 'session_id', 'auth_token', 'show_login']:
            del st.session_state[key]
    
    st.success("Logged out successfully")
    st.rerun()

def render_profile_editor():
    """Render profile editing dialog"""
    @st.dialog("Edit Profile")
    def profile_dialog():
        user = st.session_state.user
        
        full_name = st.text_input(
            "Full Name",
            value=user.full_name or "",
            key="edit_fullname"
        )
        
        email = st.text_input(
            "Email",
            value=user.email,
            key="edit_email"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Cancel", use_container_width=True):
                st.rerun()
        
        with col2:
            if st.button("Save Changes", type="primary", use_container_width=True):
                success, message = auth_manager.update_user_profile(
                    user.id,
                    full_name=full_name if full_name != user.full_name else None,
                    email=email if email != user.email else None
                )
                
                if success:
                    st.success(message)
                    # Refresh user data
                    st.session_state.user = auth_manager.db.query(User).filter(
                        User.id == user.id
                    ).first()
                    st.rerun()
                else:
                    st.error(message)
    
    profile_dialog()

def render_password_change_dialog():
    """Render password change dialog"""
    @st.dialog("Change Password")
    def password_dialog():
        current_password = st.text_input(
            "Current Password",
            type="password",
            key="current_password"
        )
        
        new_password = st.text_input(
            "New Password",
            type="password",
            placeholder="Min 8 characters",
            key="new_password"
        )
        
        confirm_password = st.text_input(
            "Confirm New Password",
            type="password",
            key="confirm_new_password"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Cancel", use_container_width=True):
                st.rerun()
        
        with col2:
            if st.button("Change Password", type="primary", use_container_width=True):
                if not all([current_password, new_password, confirm_password]):
                    st.error("Please fill in all fields")
                    return
                
                if new_password != confirm_password:
                    st.error("New passwords do not match")
                    return
                
                # Verify current password
                user = st.session_state.user
                if not auth_manager.verify_password(current_password, user.password_hash):
                    st.error("Current password is incorrect")
                    return
                
                # Update password (using reset functionality)
                user.reset_token = "temp_token"
                user.reset_token_expires = datetime.utcnow() + timedelta(minutes=5)
                auth_manager.db.commit()
                
                success, message = auth_manager.reset_password("temp_token", new_password)
                
                if success:
                    st.success("Password changed successfully! Please log in again.")
                    logout_user()
                else:
                    st.error(message)
    
    password_dialog()

def require_authentication(func: Callable) -> Callable:
    """Decorator to require authentication for a function"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        init_auth_session_state()
        
        if not st.session_state.authenticated:
            st.warning("Please log in to access this feature")
            render_auth_page()
            st.stop()
        
        # Check if session is still valid
        if st.session_state.session_id:
            user = auth_manager.get_user_from_session(st.session_state.session_id)
            if not user:
                st.warning("Session expired. Please log in again.")
                logout_user()
                st.stop()
            
            # Update user data
            st.session_state.user = user
        
        return func(*args, **kwargs)
    
    return wrapper

def get_current_user() -> Optional[User]:
    """Get current authenticated user"""
    init_auth_session_state()
    
    if st.session_state.authenticated and st.session_state.user:
        return st.session_state.user
    
    return None

def check_authentication() -> bool:
    """Check if user is authenticated"""
    init_auth_session_state()
    return st.session_state.authenticated

# Import datetime for password change dialog
from datetime import datetime, timedelta