#!/usr/bin/env python3
"""
User Authentication UI Components (Task 46)
Streamlit interface for user registration, login, profile management, and MFA
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import base64
from io import BytesIO

from user_authentication import auth_manager, User, UserSession

def initialize_auth_session_state():
    """Initialize authentication-related session state"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_session' not in st.session_state:
        st.session_state.user_session = None
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'auth_page' not in st.session_state:
        st.session_state.auth_page = 'login'

def render_authentication_interface():
    """Main authentication interface"""
    
    # Initialize session state
    initialize_auth_session_state()
    
    # Check if user is already authenticated
    if st.session_state.authenticated and st.session_state.user_session:
        # Validate session
        session = auth_manager.validate_session(st.session_state.user_session.session_id)
        if session:
            return True  # User is authenticated
        else:
            # Session expired, clear state
            st.session_state.authenticated = False
            st.session_state.user_session = None
            st.session_state.current_user = None
    
    # Show authentication interface
    st.markdown("## 🔐 User Authentication")
    
    # Authentication tabs
    login_tab, register_tab, forgot_tab = st.tabs([
        "🔑 Login",
        "📝 Register",
        "🔄 Forgot Password"
    ])
    
    with login_tab:
        render_login_interface()
    
    with register_tab:
        render_registration_interface()
    
    with forgot_tab:
        render_forgot_password_interface()
    
    return False  # User not authenticated

def render_login_interface():
    """Render login interface"""
    
    st.markdown("### 🔑 Login to Your Account")
    
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        # MFA token field (initially hidden)
        mfa_token = ""
        if st.session_state.get('mfa_required', False):
            mfa_token = st.text_input("MFA Code", placeholder="Enter 6-digit code from your authenticator app")
        
        remember_me = st.checkbox("Remember me")
        
        col1, col2 = st.columns(2)
        
        with col1:
            login_button = st.form_submit_button("🔑 Login", type="primary")
        
        with col2:
            if st.form_submit_button("👤 Demo Login"):
                # Demo login for testing
                demo_login()
                return
        
        if login_button:
            if not username or not password:
                st.error("Please enter both username and password")
                return
            
            # Attempt authentication
            success, message, user = auth_manager.authenticate_user(username, password, mfa_token)
            
            if success and user:
                # Create session
                session = auth_manager.create_session(user)
                if session:
                    # Set session state
                    st.session_state.authenticated = True
                    st.session_state.user_session = session
                    st.session_state.current_user = user
                    st.session_state.mfa_required = False
                    
                    st.success(f"Welcome back, {user.full_name}!")
                    st.rerun()
                else:
                    st.error("Failed to create session")
            
            elif message == "MFA_REQUIRED":
                # Show MFA input
                st.session_state.mfa_required = True
                st.info("Please enter your MFA code to complete login")
                st.rerun()
            
            else:
                st.error(message)
                st.session_state.mfa_required = False
    
    # Additional options
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Forgot Password?"):
            st.session_state.auth_page = 'forgot'
            st.rerun()
    
    with col2:
        if st.button("📝 Create Account"):
            st.session_state.auth_page = 'register'
            st.rerun()

def render_registration_interface():
    """Render user registration interface"""
    
    st.markdown("### 📝 Create Your Account")
    
    with st.form("registration_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            full_name = st.text_input("Full Name", placeholder="John Doe")
            username = st.text_input("Username", placeholder="johndoe")
        
        with col2:
            email = st.text_input("Email", placeholder="john@example.com")
            
        password = st.text_input("Password", type="password", placeholder="Enter a strong password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
        
        # Password strength indicator
        if password:
            is_strong, errors = auth_manager.password_manager.validate_password_strength(password)
            if is_strong:
                st.success("✅ Password strength: Strong")
            else:
                st.error("❌ Password requirements:")
                for error in errors:
                    st.write(f"  • {error}")
        
        # Terms and conditions
        agree_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
        
        register_button = st.form_submit_button("🚀 Create Account", type="primary")
        
        if register_button:
            # Validation
            if not all([full_name, username, email, password, confirm_password]):
                st.error("Please fill in all fields")
                return
            
            if password != confirm_password:
                st.error("Passwords do not match")
                return
            
            if not agree_terms:
                st.error("Please agree to the Terms of Service")
                return
            
            # Register user
            success, message = auth_manager.register_user(username, email, password, full_name)
            
            if success:
                st.success(message)
                st.info("You can now login with your credentials")
                st.balloons()
            else:
                st.error(message)

def render_forgot_password_interface():
    """Render forgot password interface"""
    
    st.markdown("### 🔄 Reset Your Password")
    
    with st.form("forgot_password_form"):
        email = st.text_input("Email Address", placeholder="Enter your registered email")
        
        reset_button = st.form_submit_button("📧 Send Reset Link", type="primary")
        
        if reset_button:
            if not email:
                st.error("Please enter your email address")
                return
            
            # Check if user exists
            user = auth_manager.db.get_user_by_email(email)
            if user:
                # In a real app, would send reset email
                st.success("If an account with this email exists, you will receive a password reset link.")
                st.info("Password reset functionality requires SMTP configuration.")
            else:
                # Don't reveal if email exists or not for security
                st.success("If an account with this email exists, you will receive a password reset link.")

def render_user_profile_interface():
    """Render user profile management interface"""
    
    if not st.session_state.authenticated:
        st.error("Please login to access your profile")
        return
    
    user = st.session_state.current_user
    
    st.markdown("## 👤 User Profile")
    
    # Profile tabs
    profile_tab, security_tab, mfa_tab, api_tab, usage_tab = st.tabs([
        "👤 Profile",
        "🔒 Security",
        "🛡️ Two-Factor Auth",
        "🔑 API Keys",
        "📊 Usage Stats"
    ])
    
    with profile_tab:
        render_profile_settings_tab(user)
    
    with security_tab:
        render_security_settings_tab(user)
    
    with mfa_tab:
        render_mfa_settings_tab(user)
    
    with api_tab:
        render_api_keys_tab(user)
    
    with usage_tab:
        render_usage_stats_tab(user)

def render_profile_settings_tab(user: User):
    """Render profile settings"""
    
    st.markdown("### 👤 Profile Information")
    
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            full_name = st.text_input("Full Name", value=user.full_name)
            username = st.text_input("Username", value=user.username, disabled=True, help="Username cannot be changed")
        
        with col2:
            email = st.text_input("Email", value=user.email)
            
            # Show subscription tier
            tier_color = {"free": "🆓", "pro": "⭐", "enterprise": "💎"}
            st.text_input(
                "Subscription", 
                value=f"{tier_color.get(user.subscription_tier, '')} {user.subscription_tier.title()}", 
                disabled=True
            )
        
        # Profile preferences
        st.markdown("#### ⚙️ Preferences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            timezone = st.selectbox(
                "Timezone",
                ["UTC", "US/Eastern", "US/Central", "US/Mountain", "US/Pacific", "Europe/London", "Europe/Berlin"],
                index=0
            )
            
            language = st.selectbox("Language", ["English", "Spanish", "French", "German"], index=0)
        
        with col2:
            email_notifications = st.checkbox("Email Notifications", value=True)
            marketing_emails = st.checkbox("Marketing Emails", value=False)
        
        if st.form_submit_button("💾 Save Changes", type="primary"):
            # Update user profile
            user.full_name = full_name
            user.email = email
            user.profile_data.update({
                'timezone': timezone,
                'language': language,
                'email_notifications': email_notifications,
                'marketing_emails': marketing_emails
            })
            
            if auth_manager.db.update_user(user):
                st.success("Profile updated successfully!")
                auth_manager.db.log_audit_event(user.user_id, "PROFILE_UPDATED", "Profile information updated")
            else:
                st.error("Failed to update profile")

def render_security_settings_tab(user: User):
    """Render security settings"""
    
    st.markdown("### 🔒 Security Settings")
    
    # Account status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_color = "🟢" if user.is_active else "🔴"
        st.metric("Account Status", f"{status_color} {'Active' if user.is_active else 'Disabled'}")
    
    with col2:
        email_status = "✅ Verified" if user.email_verified else "⚠️ Unverified"
        st.metric("Email Status", email_status)
    
    with col3:
        mfa_status = "🛡️ Enabled" if user.mfa_enabled else "❌ Disabled"
        st.metric("Two-Factor Auth", mfa_status)
    
    # Change password
    st.markdown("#### 🔑 Change Password")
    
    with st.form("change_password_form"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_new_password = st.text_input("Confirm New Password", type="password")
        
        if st.form_submit_button("🔄 Change Password"):
            if not all([current_password, new_password, confirm_new_password]):
                st.error("Please fill in all password fields")
                return
            
            if new_password != confirm_new_password:
                st.error("New passwords do not match")
                return
            
            # Verify current password
            if not auth_manager.password_manager.verify_password(current_password, user.salt, user.password_hash):
                st.error("Current password is incorrect")
                return
            
            # Validate new password strength
            is_strong, errors = auth_manager.password_manager.validate_password_strength(new_password)
            if not is_strong:
                st.error("New password does not meet requirements:")
                for error in errors:
                    st.write(f"  • {error}")
                return
            
            # Update password
            new_salt = auth_manager.password_manager.generate_salt()
            new_hash = auth_manager.password_manager.hash_password(new_password, new_salt)
            
            user.salt = new_salt
            user.password_hash = new_hash
            
            if auth_manager.db.update_user(user):
                st.success("Password changed successfully!")
                auth_manager.db.log_audit_event(user.user_id, "PASSWORD_CHANGED", "User password updated")
            else:
                st.error("Failed to change password")
    
    # Account actions
    st.markdown("#### ⚠️ Account Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📧 Resend Email Verification", disabled=user.email_verified):
            st.info("Email verification would be sent (requires SMTP configuration)")
    
    with col2:
        if st.button("🗑️ Delete Account", type="secondary"):
            st.error("Account deletion requires additional confirmation")

def render_mfa_settings_tab(user: User):
    """Render MFA settings"""
    
    st.markdown("### 🛡️ Two-Factor Authentication")
    
    if user.mfa_enabled:
        # MFA is enabled
        st.success("✅ Two-Factor Authentication is enabled")
        st.markdown("Your account is protected with an additional layer of security.")
        
        # Show backup codes (mock)
        with st.expander("🔑 Backup Codes", expanded=False):
            st.warning("⚠️ Save these backup codes in a safe place. Each code can only be used once.")
            backup_codes = [
                "1234-5678", "2345-6789", "3456-7890", "4567-8901", "5678-9012",
                "6789-0123", "7890-1234", "8901-2345", "9012-3456", "0123-4567"
            ]
            for i, code in enumerate(backup_codes, 1):
                st.code(f"{i:2d}. {code}")
        
        # Disable MFA
        st.markdown("#### ❌ Disable Two-Factor Authentication")
        
        with st.form("disable_mfa_form"):
            st.warning("⚠️ Disabling 2FA will make your account less secure.")
            password_confirm = st.text_input("Enter your password to confirm", type="password")
            
            if st.form_submit_button("❌ Disable 2FA", type="secondary"):
                if not password_confirm:
                    st.error("Please enter your password")
                    return
                
                success, message = auth_manager.disable_mfa(user.user_id, password_confirm)
                if success:
                    st.success(message)
                    user.mfa_enabled = False
                    st.rerun()
                else:
                    st.error(message)
    
    else:
        # MFA is disabled
        st.warning("⚠️ Two-Factor Authentication is disabled")
        st.markdown("Enable 2FA to add an extra layer of security to your account.")
        
        # Setup MFA
        st.markdown("#### 🛡️ Enable Two-Factor Authentication")
        
        if st.button("🚀 Setup 2FA", type="primary"):
            setup_mfa_interface(user)

def setup_mfa_interface(user: User):
    """Setup MFA interface"""
    
    st.markdown("#### 📱 Setup Two-Factor Authentication")
    
    # Step 1: Generate QR code
    success, secret, qr_code = auth_manager.setup_mfa(user.user_id)
    
    if success:
        st.markdown("**Step 1:** Install an authenticator app (Google Authenticator, Authy, etc.)")
        st.markdown("**Step 2:** Scan this QR code with your authenticator app:")
        
        if qr_code:
            # Display QR code
            qr_image = f"data:image/png;base64,{qr_code}"
            st.image(qr_image, width=200)
        
        st.markdown("**Step 3:** Enter the 6-digit code from your app:")
        
        with st.form("verify_mfa_setup"):
            mfa_code = st.text_input("Verification Code", placeholder="123456", max_chars=6)
            
            if st.form_submit_button("✅ Verify and Enable"):
                if not mfa_code or len(mfa_code) != 6:
                    st.error("Please enter a 6-digit code")
                    return
                
                success, message = auth_manager.enable_mfa(user.user_id, mfa_code)
                if success:
                    st.success(message)
                    user.mfa_enabled = True
                    st.balloons()
                    st.rerun()
                else:
                    st.error(message)
    else:
        st.error("Failed to setup MFA")

def render_api_keys_tab(user: User):
    """Render API keys management"""
    
    st.markdown("### 🔑 API Keys")
    st.markdown("Manage API keys for programmatic access to your account.")
    
    # Current API keys
    if user.api_keys:
        st.markdown("#### 🔑 Your API Keys")
        
        for i, api_key in enumerate(user.api_keys):
            with st.expander(f"API Key: {api_key['name']}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.code(api_key['key'][:8] + "..." + api_key['key'][-4:])  # Masked key
                    st.write(f"**Created:** {api_key['created_at'][:10]}")
                    st.write(f"**Last Used:** {api_key.get('last_used', 'Never')}")
                
                with col2:
                    if st.button(f"🗑️ Delete", key=f"delete_api_{i}"):
                        user.api_keys.pop(i)
                        auth_manager.db.update_user(user)
                        st.success("API key deleted")
                        st.rerun()
    else:
        st.info("No API keys created yet")
    
    # Create new API key
    st.markdown("#### ➕ Create New API Key")
    
    with st.form("create_api_key"):
        api_key_name = st.text_input("API Key Name", placeholder="My App Integration")
        api_key_description = st.text_area("Description (optional)", placeholder="What will this key be used for?")
        
        if st.form_submit_button("🔑 Generate API Key"):
            if not api_key_name:
                st.error("Please provide a name for the API key")
                return
            
            # Generate new API key
            import secrets
            new_api_key = {
                'name': api_key_name,
                'key': f"sk-{secrets.token_urlsafe(32)}",
                'description': api_key_description,
                'created_at': datetime.now().isoformat(),
                'last_used': None
            }
            
            user.api_keys.append(new_api_key)
            
            if auth_manager.db.update_user(user):
                st.success("API key created successfully!")
                st.code(new_api_key['key'])
                st.warning("⚠️ Save this key now - you won't be able to see it again!")
                auth_manager.db.log_audit_event(user.user_id, "API_KEY_CREATED", f"Key name: {api_key_name}")
            else:
                st.error("Failed to create API key")

def render_usage_stats_tab(user: User):
    """Render usage statistics"""
    
    st.markdown("### 📊 Usage Statistics")
    
    # Usage metrics
    usage = user.usage_stats
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Transcriptions", usage.get('transcriptions', 0))
    
    with col2:
        processing_time = usage.get('processing_time', 0)
        st.metric("Processing Time", f"{processing_time/3600:.1f} hours")
    
    with col3:
        storage_used = usage.get('storage_used', 0)
        st.metric("Storage Used", f"{storage_used/1024/1024:.1f} MB")
    
    # Subscription limits (mock data)
    st.markdown("#### 📋 Subscription Limits")
    
    limits = {
        'free': {'transcriptions': 10, 'processing_hours': 2, 'storage_mb': 100},
        'pro': {'transcriptions': 100, 'processing_hours': 20, 'storage_mb': 1000},
        'enterprise': {'transcriptions': -1, 'processing_hours': -1, 'storage_mb': -1}  # Unlimited
    }
    
    user_limits = limits.get(user.subscription_tier, limits['free'])
    
    # Usage bars
    for metric, limit in user_limits.items():
        if limit == -1:  # Unlimited
            st.progress(0.1, text=f"{metric.replace('_', ' ').title()}: Unlimited")
        else:
            current = usage.get(metric.replace('_mb', '').replace('_hours', '_time'), 0)
            if metric == 'processing_hours':
                current = current / 3600
            elif metric == 'storage_mb':
                current = current / 1024 / 1024
            
            progress = min(current / limit, 1.0) if limit > 0 else 0
            st.progress(progress, text=f"{metric.replace('_', ' ').title()}: {current:.1f} / {limit}")
    
    # Upgrade prompt for free users
    if user.subscription_tier == 'free':
        st.markdown("#### ⭐ Upgrade Your Plan")
        st.info("Upgrade to Pro or Enterprise for higher limits and advanced features!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("⭐ Upgrade to Pro"):
                st.info("Subscription management coming soon!")
        
        with col2:
            if st.button("💎 Upgrade to Enterprise"):
                st.info("Contact sales for Enterprise pricing!")

def render_user_logout():
    """Render logout interface"""
    
    if st.session_state.authenticated and st.session_state.user_session:
        user = st.session_state.current_user
        
        # User info in sidebar
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"👤 **{user.full_name}**")
        st.sidebar.markdown(f"🎫 {user.subscription_tier.title()}")
        
        if st.sidebar.button("🚪 Logout"):
            # Logout user
            if auth_manager.logout_user(st.session_state.user_session.session_id):
                st.session_state.authenticated = False
                st.session_state.user_session = None
                st.session_state.current_user = None
                st.success("Logged out successfully!")
                st.rerun()

def demo_login():
    """Demo login for testing"""
    # Create demo user if doesn't exist
    demo_user = auth_manager.db.get_user_by_username("demo")
    
    if not demo_user:
        # Create demo user
        success, message = auth_manager.register_user(
            "demo", "demo@example.com", "Demo123!", "Demo User"
        )
        if success:
            demo_user = auth_manager.db.get_user_by_username("demo")
    
    if demo_user:
        # Create session
        session = auth_manager.create_session(demo_user)
        if session:
            st.session_state.authenticated = True
            st.session_state.user_session = session
            st.session_state.current_user = demo_user
            st.success("Demo login successful!")
            st.rerun()

def get_current_user() -> Optional[User]:
    """Get current authenticated user"""
    if st.session_state.authenticated and st.session_state.current_user:
        return st.session_state.current_user
    return None

def require_authentication():
    """Decorator-like function to require authentication"""
    if not st.session_state.get('authenticated', False):
        st.error("🔐 Please login to access this feature")
        render_authentication_interface()
        return False
    return True

def check_user_permission(required_role: str) -> bool:
    """Check if current user has required role"""
    user = get_current_user()
    if not user:
        return False
    
    role_hierarchy = {'free': 0, 'pro': 1, 'admin': 2, 'enterprise': 3}
    user_level = role_hierarchy.get(user.role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level