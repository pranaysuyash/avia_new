#!/usr/bin/env python3
"""
Streamlit Authentication UI - Enterprise-grade authentication interface
Integrates with existing JWT authentication backend
"""

import streamlit as st
import logging
from typing import Optional, Dict, Any, Tuple
import requests
import time
from datetime import datetime, timedelta
import re

# Import refactored UI components
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui_styles_refactored import apply_theme
from enhanced_components_refactored import (
    create_info_card, show_success_message, show_error_message,
    render_empty_state, create_action_button
)

logger = logging.getLogger(__name__)

class StreamlitAuthUI:
    """Streamlit-based authentication UI"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize authentication session state"""
        if 'auth_token' not in st.session_state:
            st.session_state.auth_token = None
        if 'refresh_token' not in st.session_state:
            st.session_state.refresh_token = None
        if 'user' not in st.session_state:
            st.session_state.user = None
        if 'auth_mode' not in st.session_state:
            st.session_state.auth_mode = 'login'
        if 'show_mfa' not in st.session_state:
            st.session_state.show_mfa = False
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return st.session_state.auth_token is not None
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user"""
        return st.session_state.user
    
    def render_auth_page(self):
        """Render the main authentication page"""
        # Apply theme
        apply_theme(st.session_state.get('theme', 'light'))
        
        if self.is_authenticated():
            self._render_authenticated_view()
        else:
            self._render_authentication_forms()
    
    def _render_authentication_forms(self):
        """Render login/register forms"""
        # Center the auth forms
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # Logo and title
            st.markdown(
                """
                <div style="text-align: center; margin-bottom: 2rem;">
                    <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem;">
                        🎵 TranscriptPro
                    </h1>
                    <p style="color: var(--text-secondary-color);">
                        Enterprise Audio/Video Transcription Platform
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Auth mode tabs
            tab1, tab2, tab3 = st.tabs(["Sign In", "Sign Up", "Reset Password"])
            
            with tab1:
                self._render_login_form()
            
            with tab2:
                self._render_register_form()
            
            with tab3:
                self._render_password_reset_form()
            
            # OAuth options
            st.markdown("---")
            st.markdown(
                """
                <div style="text-align: center;">
                    <p style="color: var(--text-secondary-color); margin-bottom: 1rem;">
                        Or continue with
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            col_oauth1, col_oauth2, col_oauth3 = st.columns(3)
            with col_oauth1:
                if st.button("🔵 Google", use_container_width=True):
                    self._initiate_oauth("google")
            with col_oauth2:
                if st.button("⚫ GitHub", use_container_width=True):
                    self._initiate_oauth("github")
            with col_oauth3:
                if st.button("🔷 Microsoft", use_container_width=True):
                    self._initiate_oauth("microsoft")
    
    def _render_login_form(self):
        """Render login form"""
        with st.form("login_form"):
            st.markdown("### Welcome Back")
            
            username_or_email = st.text_input(
                "Email or Username",
                placeholder="john@example.com",
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
                remember_me = st.checkbox("Remember me", key="login_remember")
            with col2:
                st.markdown(
                    '<div style="text-align: right; padding-top: 0.5rem;">'
                    '<a href="#" style="color: var(--primary-color); text-decoration: none;">'
                    'Forgot password?</a></div>',
                    unsafe_allow_html=True
                )
            
            submitted = st.form_submit_button(
                "Sign In",
                type="primary",
                use_container_width=True
            )
            
            if submitted:
                if username_or_email and password:
                    self._handle_login(username_or_email, password, remember_me)
                else:
                    st.error("Please fill in all fields")
    
    def _render_register_form(self):
        """Render registration form"""
        with st.form("register_form"):
            st.markdown("### Create Account")
            
            col1, col2 = st.columns(2)
            with col1:
                full_name = st.text_input(
                    "Full Name",
                    placeholder="John Doe",
                    key="register_fullname"
                )
            with col2:
                username = st.text_input(
                    "Username",
                    placeholder="johndoe",
                    key="register_username",
                    help="Unique username for your account"
                )
            
            email = st.text_input(
                "Email",
                placeholder="john@example.com",
                key="register_email"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Create a strong password",
                key="register_password",
                help="At least 8 characters with uppercase, lowercase, number, and special character"
            )
            
            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Re-enter your password",
                key="register_confirm_password"
            )
            
            # Password strength indicator
            if password:
                strength = self._calculate_password_strength(password)
                self._render_password_strength(strength)
            
            terms = st.checkbox(
                "I agree to the Terms of Service and Privacy Policy",
                key="register_terms"
            )
            
            submitted = st.form_submit_button(
                "Create Account",
                type="primary",
                use_container_width=True
            )
            
            if submitted:
                if self._validate_registration(
                    full_name, username, email, 
                    password, confirm_password, terms
                ):
                    self._handle_registration(
                        full_name, username, email, password
                    )
    
    def _render_password_reset_form(self):
        """Render password reset form"""
        if 'reset_token_sent' not in st.session_state:
            st.session_state.reset_token_sent = False
        
        if not st.session_state.reset_token_sent:
            with st.form("reset_form"):
                st.markdown("### Reset Password")
                st.markdown("Enter your email address and we'll send you a link to reset your password.")
                
                email = st.text_input(
                    "Email",
                    placeholder="john@example.com",
                    key="reset_email"
                )
                
                submitted = st.form_submit_button(
                    "Send Reset Link",
                    type="primary",
                    use_container_width=True
                )
                
                if submitted and email:
                    self._handle_password_reset_request(email)
        else:
            # Show success message
            create_info_card(
                "Reset Link Sent",
                "We've sent a password reset link to your email. Please check your inbox and follow the instructions.",
                variant="success",
                icon="✉️"
            )
            
            if st.button("Back to Login"):
                st.session_state.reset_token_sent = False
                st.rerun()
    
    def _render_authenticated_view(self):
        """Render view for authenticated users"""
        user = st.session_state.user
        
        # User profile header
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### Welcome back, {user.get('full_name', user.get('username', 'User'))}!")
            st.caption(f"Logged in as: {user.get('email', '')}")
        
        with col2:
            if st.button("🚪 Sign Out", type="secondary"):
                self._handle_logout()
        
        # Show user dashboard
        st.markdown("---")
        
        # Quick stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Transcriptions", "42", delta="+5 this week")
        
        with col2:
            st.metric("Total Duration", "127h", delta="+12h")
        
        with col3:
            st.metric("Storage Used", "2.4 GB", delta="+0.3 GB")
        
        with col4:
            st.metric("API Calls", "1,234", delta="+156")
        
        # Recent activity
        st.markdown("### Recent Activity")
        
        activities = [
            {"time": "2 hours ago", "action": "Transcribed", "item": "Meeting_2024_01_15.mp4"},
            {"time": "5 hours ago", "action": "Exported", "item": "Interview_John_Doe.srt"},
            {"time": "Yesterday", "action": "Shared", "item": "Product_Demo.mp3"},
        ]
        
        for activity in activities:
            st.markdown(
                f"• **{activity['time']}** - {activity['action']} *{activity['item']}*"
            )
    
    def _handle_login(self, username_or_email: str, password: str, remember_me: bool):
        """Handle login request"""
        with st.spinner("Signing in..."):
            try:
                response = requests.post(
                    f"{self.api_base_url}/api/auth/login",
                    json={
                        "username": username_or_email,
                        "password": password,
                        "remember_me": remember_me
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if MFA is required
                    if data.get('mfa_required'):
                        st.session_state.show_mfa = True
                        st.session_state.mfa_session = data.get('session_id')
                        st.rerun()
                    else:
                        # Store tokens and user data
                        st.session_state.auth_token = data['access_token']
                        st.session_state.refresh_token = data.get('refresh_token')
                        st.session_state.user = data['user']
                        
                        show_success_message("Login successful! Redirecting...")
                        time.sleep(1)
                        st.rerun()
                
                elif response.status_code == 401:
                    st.error("Invalid username/email or password")
                else:
                    st.error(f"Login failed: {response.json().get('detail', 'Unknown error')}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {str(e)}")
    
    def _handle_registration(self, full_name: str, username: str, email: str, password: str):
        """Handle registration request"""
        with st.spinner("Creating account..."):
            try:
                response = requests.post(
                    f"{self.api_base_url}/api/auth/register",
                    json={
                        "full_name": full_name,
                        "username": username,
                        "email": email,
                        "password": password
                    }
                )
                
                if response.status_code == 201:
                    show_success_message(
                        "Account created successfully! Please check your email to verify your account."
                    )
                    time.sleep(2)
                    st.session_state.auth_mode = 'login'
                    st.rerun()
                else:
                    error_data = response.json()
                    st.error(f"Registration failed: {error_data.get('detail', 'Unknown error')}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {str(e)}")
    
    def _handle_password_reset_request(self, email: str):
        """Handle password reset request"""
        with st.spinner("Sending reset link..."):
            try:
                response = requests.post(
                    f"{self.api_base_url}/api/auth/forgot-password",
                    json={"email": email}
                )
                
                if response.status_code == 200:
                    st.session_state.reset_token_sent = True
                    st.rerun()
                else:
                    st.error("Failed to send reset link. Please check your email address.")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {str(e)}")
    
    def _handle_logout(self):
        """Handle logout"""
        try:
            # Call logout endpoint
            headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
            requests.post(f"{self.api_base_url}/api/auth/logout", headers=headers)
        except:
            pass  # Continue with local logout even if API call fails
        
        # Clear session state
        st.session_state.auth_token = None
        st.session_state.refresh_token = None
        st.session_state.user = None
        
        show_success_message("Logged out successfully")
        time.sleep(1)
        st.rerun()
    
    def _initiate_oauth(self, provider: str):
        """Initiate OAuth flow"""
        st.info(f"OAuth with {provider.title()} coming soon!")
    
    def _calculate_password_strength(self, password: str) -> Dict[str, Any]:
        """Calculate password strength"""
        strength = {
            "score": 0,
            "level": "Weak",
            "color": "red",
            "requirements": {
                "length": len(password) >= 8,
                "uppercase": bool(re.search(r'[A-Z]', password)),
                "lowercase": bool(re.search(r'[a-z]', password)),
                "number": bool(re.search(r'\d', password)),
                "special": bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
            }
        }
        
        # Calculate score
        strength["score"] = sum(strength["requirements"].values()) * 20
        
        # Determine level
        if strength["score"] >= 80:
            strength["level"] = "Strong"
            strength["color"] = "green"
        elif strength["score"] >= 60:
            strength["level"] = "Medium"
            strength["color"] = "orange"
        else:
            strength["level"] = "Weak"
            strength["color"] = "red"
        
        return strength
    
    def _render_password_strength(self, strength: Dict[str, Any]):
        """Render password strength indicator"""
        # Progress bar
        st.progress(strength["score"] / 100)
        
        # Strength text
        st.markdown(
            f'<p style="color: {strength["color"]}; font-size: 0.875rem; margin-top: 0.5rem;">'
            f'Password Strength: {strength["level"]}</p>',
            unsafe_allow_html=True
        )
        
        # Requirements checklist
        reqs = strength["requirements"]
        req_text = []
        if not reqs["length"]:
            req_text.append("• At least 8 characters")
        if not reqs["uppercase"]:
            req_text.append("• One uppercase letter")
        if not reqs["lowercase"]:
            req_text.append("• One lowercase letter")
        if not reqs["number"]:
            req_text.append("• One number")
        if not reqs["special"]:
            req_text.append("• One special character")
        
        if req_text:
            st.caption("Requirements: " + ", ".join(req_text))
    
    def _validate_registration(self, full_name: str, username: str, email: str,
                             password: str, confirm_password: str, terms: bool) -> bool:
        """Validate registration form"""
        errors = []
        
        if not full_name:
            errors.append("Full name is required")
        
        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters")
        
        if not email or '@' not in email:
            errors.append("Valid email is required")
        
        if not password or len(password) < 8:
            errors.append("Password must be at least 8 characters")
        
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        if not terms:
            errors.append("You must accept the terms and conditions")
        
        if errors:
            for error in errors:
                st.error(error)
            return False
        
        return True
    
    def require_auth(self, func):
        """Decorator to require authentication for a function"""
        def wrapper(*args, **kwargs):
            if not self.is_authenticated():
                st.warning("Please log in to access this feature")
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        if st.session_state.auth_token:
            return {"Authorization": f"Bearer {st.session_state.auth_token}"}
        return {}


# Global instance
auth_ui = StreamlitAuthUI()


def render_user_menu():
    """Render user menu in app header"""
    if auth_ui.is_authenticated():
        user = auth_ui.get_current_user()
        
        with st.popover("👤"):
            st.markdown(f"**{user.get('full_name', 'User')}**")
            st.caption(user.get('email', ''))
            st.markdown("---")
            
            if st.button("Profile Settings", use_container_width=True):
                st.session_state.current_tab = 'settings'
                st.rerun()
            
            if st.button("API Keys", use_container_width=True):
                st.session_state.current_tab = 'settings'
                st.session_state.settings_tab = 'api'
                st.rerun()
            
            st.markdown("---")
            
            if st.button("Sign Out", type="secondary", use_container_width=True):
                auth_ui._handle_logout()
    else:
        if st.button("Sign In", type="primary"):
            st.session_state.show_auth = True
            st.rerun()