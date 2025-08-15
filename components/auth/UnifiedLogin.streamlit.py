#!/usr/bin/env python3
"""
Unified Login Component - Streamlit
Accessible login form using the unified design system
Follows WCAG 2.1 AA guidelines
"""

import streamlit as st
from typing import Optional, Dict, Any, Callable
import re
from dataclasses import dataclass

from design_system import get_design_system, ComponentVariant, ComponentSize

@dataclass
class LoginCredentials:
    """Login credentials data structure"""
    email: str
    password: str
    remember_me: bool = False

@dataclass
class ValidationResult:
    """Validation result data structure"""
    is_valid: bool
    message: str = ""

class UnifiedLoginStreamlit:
    """
    Unified Login Component for Streamlit
    Provides accessible, consistent login interface
    """
    
    def __init__(self):
        self.ds = get_design_system()
        
    def validate_email(self, email: str) -> ValidationResult:
        """Validate email address"""
        if not email:
            return ValidationResult(False, "Email is required")
        
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, email):
            return ValidationResult(False, "Please enter a valid email address")
        
        return ValidationResult(True)
    
    def validate_password(self, password: str) -> ValidationResult:
        """Validate password"""
        if not password:
            return ValidationResult(False, "Password is required")
        
        if len(password) < 6:
            return ValidationResult(False, "Password must be at least 6 characters")
        
        return ValidationResult(True)
    
    def render_login_form(
        self,
        on_submit: Callable[[LoginCredentials], bool],
        on_forgot_password: Optional[Callable] = None,
        on_register: Optional[Callable] = None,
        show_social_login: bool = True,
        show_remember_me: bool = True,
        form_key: str = "unified_login"
    ) -> Optional[LoginCredentials]:
        """
        Render the unified login form
        
        Args:
            on_submit: Callback function for form submission
            on_forgot_password: Optional callback for forgot password
            on_register: Optional callback for registration
            show_social_login: Whether to show social login options
            show_remember_me: Whether to show remember me checkbox
            form_key: Unique key for the form
            
        Returns:
            LoginCredentials if form is submitted successfully, None otherwise
        """
        
        # Initialize session state
        if f"{form_key}_email" not in st.session_state:
            st.session_state[f"{form_key}_email"] = ""
        if f"{form_key}_password" not in st.session_state:
            st.session_state[f"{form_key}_password"] = ""
        if f"{form_key}_remember_me" not in st.session_state:
            st.session_state[f"{form_key}_remember_me"] = False
        if f"{form_key}_error" not in st.session_state:
            st.session_state[f"{form_key}_error"] = ""
        if f"{form_key}_loading" not in st.session_state:
            st.session_state[f"{form_key}_loading"] = False
            
        # Header
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 style="color: var(--text-primary); margin-bottom: 0.5rem;">
                Sign in to your account
            </h1>
        </div>
        """, unsafe_allow_html=True)
        
        # Registration link
        if on_register:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown("""
                <div style="text-align: center; margin-bottom: 1.5rem;">
                    <span style="color: var(--text-secondary); font-size: 0.875rem;">
                        Or 
                        <a href="#" onclick="window.parent.postMessage({type: 'register'}, '*')" 
                           style="color: var(--primary); text-decoration: none; font-weight: 500;">
                            create a new account
                        </a>
                    </span>
                </div>
                """, unsafe_allow_html=True)
        
        # Error display
        if st.session_state[f"{form_key}_error"]:
            self.ds.info_alert(
                st.session_state[f"{form_key}_error"],
                variant=ComponentVariant.ERROR,
                icon=True
            )
        
        # Main form
        with st.form(key=form_key, clear_on_submit=False):
            # Email input
            st.markdown("""
            <label for="email" style="display: block; margin-bottom: 0.5rem; font-weight: 500; color: var(--text-primary);">
                Email Address <span style="color: var(--error);" aria-label="required">*</span>
            </label>
            """, unsafe_allow_html=True)
            
            email = st.text_input(
                label="Email Address",
                value=st.session_state[f"{form_key}_email"],
                placeholder="Enter your email address",
                key=f"{form_key}_email_input",
                label_visibility="collapsed",
                help="Enter the email address associated with your account"
            )
            
            # Email validation feedback
            if email and email != st.session_state[f"{form_key}_email"]:
                email_validation = self.validate_email(email)
                if not email_validation.is_valid:
                    st.error(f"📧 {email_validation.message}")
            
            # Password input
            st.markdown("""
            <label for="password" style="display: block; margin-bottom: 0.5rem; margin-top: 1rem; font-weight: 500; color: var(--text-primary);">
                Password <span style="color: var(--error);" aria-label="required">*</span>
            </label>
            """, unsafe_allow_html=True)
            
            password = st.text_input(
                label="Password",
                value=st.session_state[f"{form_key}_password"],
                placeholder="Enter your password",
                type="password",
                key=f"{form_key}_password_input",
                label_visibility="collapsed",
                help="Enter your account password (minimum 6 characters)"
            )
            
            # Password validation feedback
            if password and password != st.session_state[f"{form_key}_password"]:
                password_validation = self.validate_password(password)
                if not password_validation.is_valid:
                    st.error(f"🔒 {password_validation.message}")
            
            # Remember me and forgot password row
            col1, col2 = st.columns([1, 1])
            
            with col1:
                if show_remember_me:
                    remember_me = st.checkbox(
                        "Remember me",
                        value=st.session_state[f"{form_key}_remember_me"],
                        key=f"{form_key}_remember_checkbox",
                        help="Keep me signed in on this device"
                    )
            
            with col2:
                if on_forgot_password:
                    if st.button(
                        "Forgot Password?",
                        key=f"{form_key}_forgot_btn",
                        help="Reset your password",
                        type="secondary"
                    ):
                        on_forgot_password()
            
            # Submit button
            st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
            
            submit_clicked = st.form_submit_button(
                "🔐 Sign In" if not st.session_state[f"{form_key}_loading"] else "⏳ Signing In...",
                disabled=st.session_state[f"{form_key}_loading"],
                use_container_width=True,
                type="primary"
            )
            
            # Form submission handling
            if submit_clicked and not st.session_state[f"{form_key}_loading"]:
                # Validate inputs
                email_validation = self.validate_email(email)
                password_validation = self.validate_password(password)
                
                if not email_validation.is_valid:
                    st.session_state[f"{form_key}_error"] = email_validation.message
                    st.rerun()
                elif not password_validation.is_valid:
                    st.session_state[f"{form_key}_error"] = password_validation.message
                    st.rerun()
                else:
                    # Clear any previous errors
                    st.session_state[f"{form_key}_error"] = ""
                    
                    # Set loading state
                    st.session_state[f"{form_key}_loading"] = True
                    
                    # Create credentials object
                    credentials = LoginCredentials(
                        email=email,
                        password=password,
                        remember_me=remember_me if show_remember_me else False
                    )
                    
                    # Update session state
                    st.session_state[f"{form_key}_email"] = email
                    st.session_state[f"{form_key}_password"] = password
                    if show_remember_me:
                        st.session_state[f"{form_key}_remember_me"] = remember_me
                    
                    try:
                        # Call the submit handler
                        success = on_submit(credentials)
                        
                        if success:
                            # Clear form data on successful login
                            st.session_state[f"{form_key}_email"] = ""
                            st.session_state[f"{form_key}_password"] = ""
                            st.session_state[f"{form_key}_remember_me"] = False
                            st.session_state[f"{form_key}_error"] = ""
                            
                            st.success("🎉 Login successful! Welcome back.")
                            return credentials
                        else:
                            st.session_state[f"{form_key}_error"] = "Invalid email or password. Please try again."
                    
                    except Exception as e:
                        st.session_state[f"{form_key}_error"] = f"Login failed: {str(e)}"
                    
                    finally:
                        st.session_state[f"{form_key}_loading"] = False
                        st.rerun()
        
        # Social login section
        if show_social_login:
            self.ds.divider(style="solid", spacing="lg")
            
            st.markdown("""
            <div style="text-align: center; margin: 1.5rem 0;">
                <span style="color: var(--text-secondary); font-size: 0.875rem;">
                    Or continue with
                </span>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button(
                    "🔍 Google",
                    key=f"{form_key}_google",
                    use_container_width=True,
                    help="Sign in with your Google account"
                ):
                    self._handle_oauth_login("google")
            
            with col2:
                if st.button(
                    "🐙 GitHub",
                    key=f"{form_key}_github",
                    use_container_width=True,
                    help="Sign in with your GitHub account"
                ):
                    self._handle_oauth_login("github")
        
        return None
    
    def _handle_oauth_login(self, provider: str):
        """Handle OAuth login redirect"""
        oauth_url = f"http://localhost:8001/api/auth/{provider}"
        
        st.markdown(f"""
        <script>
        window.open('{oauth_url}', '_blank', 'width=500,height=600');
        </script>
        """, unsafe_allow_html=True)
        
        st.info(f"🔄 Redirecting to {provider.title()} for authentication...")
    
    def render_compact_login(
        self,
        on_submit: Callable[[LoginCredentials], bool],
        form_key: str = "compact_login"
    ) -> Optional[LoginCredentials]:
        """
        Render a compact login form for sidebars or modals
        
        Args:
            on_submit: Callback function for form submission
            form_key: Unique key for the form
            
        Returns:
            LoginCredentials if form is submitted successfully, None otherwise
        """
        
        st.markdown("### 🔐 Sign In")
        
        with st.form(key=form_key, clear_on_submit=False):
            email = st.text_input(
                "Email",
                placeholder="your@email.com",
                key=f"{form_key}_email"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="••••••••",
                key=f"{form_key}_password"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                submit = st.form_submit_button("Sign In", use_container_width=True)
            
            with col2:
                if st.form_submit_button("Forgot?", use_container_width=True):
                    st.info("Password reset functionality would be triggered here")
            
            if submit:
                if email and password:
                    credentials = LoginCredentials(
                        email=email,
                        password=password,
                        remember_me=False
                    )
                    
                    if on_submit(credentials):
                        st.success("Login successful!")
                        return credentials
                    else:
                        st.error("Invalid credentials")
                else:
                    st.error("Please enter both email and password")
        
        return None

# Convenience function for easy import
def render_unified_login(
    on_submit: Callable[[LoginCredentials], bool],
    **kwargs
) -> Optional[LoginCredentials]:
    """
    Convenience function to render unified login form
    
    Args:
        on_submit: Callback function for form submission
        **kwargs: Additional arguments passed to render_login_form
        
    Returns:
        LoginCredentials if form is submitted successfully, None otherwise
    """
    login_component = UnifiedLoginStreamlit()
    return login_component.render_login_form(on_submit, **kwargs)

# Export for easy usage
__all__ = ["UnifiedLoginStreamlit", "LoginCredentials", "render_unified_login"]