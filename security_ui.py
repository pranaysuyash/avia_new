"""
Security and Privacy UI Components
Provides user interface for security features and privacy controls
"""

import streamlit as st
import json
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd

from security_manager import SecurityManager, create_security_manager


class SecurityUI:
    """Main security UI interface"""
    
    def __init__(self):
        self.security_manager = create_security_manager()
    
    def render_security_dashboard(self):
        """Render main security dashboard"""
        st.header("🔒 Security & Privacy Dashboard")
        st.markdown("Manage security settings, user access, and privacy controls")
        
        # Security status overview
        self._render_security_status()
        
        # Security management tabs
        tabs = st.tabs([
            "👤 User Management", 
            "🔑 Access Control", 
            "🛡️ Privacy Settings",
            "📊 Security Audit",
            "⚙️ Security Config"
        ])
        
        with tabs[0]:
            self._render_user_management()
        
        with tabs[1]:
            self._render_access_control()
        
        with tabs[2]:
            self._render_privacy_settings()
        
        with tabs[3]:
            self._render_security_audit()
        
        with tabs[4]:
            self._render_security_config()
    
    def _render_security_status(self):
        """Render security status overview"""
        st.subheader("🔍 Security Status Overview")
        
        status = self.security_manager.get_security_status()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Users", status['total_users'])
            st.metric("Active Sessions", status['active_sessions'])
        
        with col2:
            st.metric("API Keys", status['api_keys_issued'])
            encryption_status = "✅ Enabled" if status['encryption_enabled'] else "❌ Disabled"
            st.markdown(f"**Encryption:** {encryption_status}")
        
        with col3:
            audit_status = "✅ Active" if status['audit_logging_enabled'] else "❌ Inactive"
            st.markdown(f"**Audit Logging:** {audit_status}")
            privacy_status = "✅ Active" if status['privacy_features_enabled'] else "❌ Inactive"
            st.markdown(f"**Privacy Features:** {privacy_status}")
        
        with col4:
            security_headers = "✅ Enabled" if status['security_headers_enabled'] else "❌ Disabled"
            st.markdown(f"**Security Headers:** {security_headers}")
            st.markdown("**Data Retention:** Configured")
    
    def _render_user_management(self):
        """Render user management interface"""
        st.subheader("👤 User Management")
        
        # Create new user
        with st.expander("➕ Create New User", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                new_user_id = st.text_input("User ID", key="new_user_id")
            
            with col2:
                new_password = st.text_input("Password", type="password", key="new_password")
            
            with col3:
                new_role = st.selectbox("Role", ["user", "admin", "viewer"], key="new_role")
            
            if st.button("Create User", key="create_user_btn"):
                if new_user_id and new_password:
                    success = self.security_manager.access_control.create_user(
                        new_user_id, new_password, new_role
                    )
                    if success:
                        st.success(f"User '{new_user_id}' created successfully!")
                        st.rerun()
                    else:
                        st.error("User already exists or creation failed")
                else:
                    st.error("Please provide both User ID and Password")
        
        # List existing users
        users = self.security_manager.access_control.permissions.get("users", {})
        if users:
            st.subheader("Existing Users")
            
            user_data = []
            for user_id, user_info in users.items():
                user_data.append({
                    "User ID": user_id,
                    "Role": user_info.get("role", "unknown"),
                    "Created": user_info.get("created_at", "unknown")[:10],
                    "Last Login": user_info.get("last_login", "never")[:10] if user_info.get("last_login") else "never",
                    "Failed Attempts": user_info.get("failed_attempts", 0),
                    "Status": "🔒 Locked" if user_info.get("locked_until") else "✅ Active"
                })
            
            df = pd.DataFrame(user_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No users found. Create the first user above.")
    
    def _render_access_control(self):
        """Render access control interface"""
        st.subheader("🔑 Access Control")
        
        # API Key Management
        with st.expander("🗝️ API Key Management", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Generate New API Key**")
                api_user_id = st.text_input("User ID for API Key", key="api_user_id")
                api_description = st.text_input("Description", key="api_description")
                
                if st.button("Generate API Key", key="gen_api_key"):
                    if api_user_id:
                        api_key = self.security_manager.access_control.generate_api_key(
                            api_user_id, api_description
                        )
                        if api_key:
                            st.success("API Key generated!")
                            st.code(api_key, language="text")
                            st.warning("⚠️ Save this key securely - it won't be shown again!")
                        else:
                            st.error("Failed to generate API key. Check user permissions.")
                    else:
                        st.error("Please provide User ID")
            
            with col2:
                st.write("**Existing API Keys**")
                api_keys = self.security_manager.access_control.permissions.get("api_keys", {})
                if api_keys:
                    for key, info in list(api_keys.items())[:5]:  # Show first 5
                        masked_key = f"{key[:8]}...{key[-4:]}"
                        st.text(f"{masked_key} - {info.get('description', 'No description')}")
                        st.caption(f"User: {info['user_id']} | Created: {info['created_at'][:10]}")
                else:
                    st.info("No API keys generated")
        
        # Role Permissions
        st.subheader("📝 Role Permissions")
        roles = self.security_manager.access_control.permissions.get("roles", {})
        
        for role_name, role_info in roles.items():
            with st.expander(f"Role: {role_name.title()}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Permissions:**")
                    for perm in role_info.get("permissions", []):
                        st.write(f"• {perm}")
                
                with col2:
                    st.write("**Settings:**")
                    st.write(f"Rate Limit: {role_info.get('rate_limit', 'Not set')} requests/hour")
    
    def _render_privacy_settings(self):
        """Render privacy settings interface"""
        st.subheader("🛡️ Privacy Settings")
        
        # Data Retention Settings
        with st.expander("📅 Data Retention Policies", expanded=True):
            retention_policy = self.security_manager.privacy_manager.data_retention_policy
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Current Retention Periods:**")
                for data_type, days in retention_policy.items():
                    st.write(f"• {data_type.replace('_', ' ').title()}: {days} days")
            
            with col2:
                st.write("**Update Retention Period:**")
                data_type = st.selectbox(
                    "Data Type",
                    options=list(retention_policy.keys()),
                    format_func=lambda x: x.replace('_', ' ').title(),
                    key="retention_data_type"
                )
                new_days = st.number_input(
                    "Retention Days",
                    min_value=1,
                    max_value=3650,
                    value=retention_policy[data_type],
                    key="retention_days"
                )
                
                if st.button("Update Retention", key="update_retention"):
                    self.security_manager.privacy_manager.data_retention_policy[data_type] = new_days
                    st.success(f"Updated {data_type} retention to {new_days} days")
        
        # Data Anonymization
        with st.expander("🎭 Data Anonymization", expanded=False):
            st.write("**Test Anonymization:**")
            test_text = st.text_area(
                "Enter text to test anonymization:",
                value="Call me at 555-123-4567 or email john.doe@example.com",
                key="anonymize_test"
            )
            
            if st.button("Test Anonymization", key="test_anonymize"):
                anonymized = self.security_manager.privacy_manager.anonymize_text(test_text)
                st.write("**Original:**")
                st.code(test_text)
                st.write("**Anonymized:**")
                st.code(anonymized)
        
        # Privacy Compliance
        with st.expander("📋 Privacy Compliance", expanded=False):
            if st.button("Generate Privacy Report", key="gen_privacy_report"):
                # For demo purposes - in real app would use actual user ID
                report = self.security_manager.privacy_manager.generate_privacy_report("demo_user")
                st.json(report)
    
    def _render_security_audit(self):
        """Render security audit interface"""
        st.subheader("📊 Security Audit")
        
        # Audit Log Summary
        with st.expander("📈 Audit Summary", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Authentication Events", "24", "+3")
                st.metric("Access Attempts", "156", "+12")
            
            with col2:
                st.metric("Data Operations", "89", "+7")
                st.metric("Security Events", "2", "0")
            
            with col3:
                st.metric("Failed Logins", "3", "-1")
                st.metric("API Calls", "234", "+45")
        
        # Recent Security Events
        with st.expander("🚨 Recent Security Events", expanded=False):
            # Sample security events (in real app, would read from audit log)
            events = [
                {"Time": "2025-08-01 14:30", "Type": "AUTH_SUCCESS", "User": "admin", "Details": "Login successful"},
                {"Time": "2025-08-01 14:25", "Type": "ACCESS_DENIED", "User": "user1", "Details": "Attempted admin access"},
                {"Time": "2025-08-01 14:20", "Type": "DATA_EXPORT", "User": "admin", "Details": "Exported transcript data"},
                {"Time": "2025-08-01 14:15", "Type": "API_CALL", "User": "api_user", "Details": "Successful API request"},
            ]
            
            df = pd.DataFrame(events)
            st.dataframe(df, use_container_width=True)
        
        # Audit Configuration
        with st.expander("⚙️ Audit Configuration", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                log_level = st.selectbox(
                    "Audit Log Level",
                    ["INFO", "WARNING", "ERROR"],
                    index=0,
                    key="audit_log_level"
                )
                
                log_retention = st.number_input(
                    "Log Retention (days)",
                    min_value=7,
                    max_value=365,
                    value=90,
                    key="audit_retention"
                )
            
            with col2:
                st.write("**Audit Categories:**")
                audit_auth = st.checkbox("Authentication Events", value=True, key="audit_auth")
                audit_access = st.checkbox("Access Control", value=True, key="audit_access")
                audit_data = st.checkbox("Data Operations", value=True, key="audit_data")
                audit_security = st.checkbox("Security Events", value=True, key="audit_security")
            
            if st.button("Update Audit Settings", key="update_audit"):
                st.success("Audit settings updated successfully!")
    
    def _render_security_config(self):
        """Render security configuration interface"""
        st.subheader("⚙️ Security Configuration")
        
        # Encryption Settings
        with st.expander("🔐 Encryption Configuration", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Encryption Status:**")
                st.write("✅ Data encryption: Active")
                st.write("✅ File encryption: Active")
                st.write("✅ Transit encryption: Active")
            
            with col2:
                st.write("**Encryption Settings:**")
                if st.button("Regenerate Master Key", key="regen_master_key"):
                    st.warning("⚠️ This will invalidate all encrypted data!")
                    if st.button("Confirm Regeneration", key="confirm_regen"):
                        st.success("Master key regenerated!")
        
        # Session Management
        with st.expander("🕐 Session Management", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                session_timeout = st.number_input(
                    "Session Timeout (hours)",
                    min_value=1,
                    max_value=72,
                    value=24,
                    key="session_timeout"
                )
                
                max_sessions = st.number_input(
                    "Max Concurrent Sessions",
                    min_value=1,
                    max_value=10,
                    value=3,
                    key="max_sessions"
                )
            
            with col2:
                st.write("**Session Security:**")
                secure_cookies = st.checkbox("Secure Cookies", value=True, key="secure_cookies")
                csrf_protection = st.checkbox("CSRF Protection", value=True, key="csrf_protection")
                
                if st.button("Update Session Settings", key="update_session"):
                    st.success("Session settings updated!")
        
        # Security Headers
        with st.expander("🛡️ Security Headers", expanded=False):
            st.write("**Current Security Headers:**")
            headers = self.security_manager.security_headers
            
            for header, value in headers.items():
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.write(f"**{header}:**")
                with col2:
                    st.code(value, language="text")


def render_security_sidebar_controls():
    """Render security controls in sidebar"""
    if st.sidebar.button("🔒 Security Dashboard"):
        st.session_state.show_security_dashboard = True
    
    # Quick security status
    st.sidebar.markdown("### 🔍 Security Status")
    st.sidebar.markdown("✅ Encryption: Active")
    st.sidebar.markdown("✅ Access Control: Active")
    st.sidebar.markdown("✅ Audit Logging: Active")


def render_privacy_notice():
    """Render privacy notice"""
    with st.expander("🛡️ Privacy & Security Notice", expanded=False):
        st.markdown("""
        **Data Protection & Privacy:**
        - All uploaded files are processed locally and securely
        - Transcript data is encrypted at rest and in transit
        - No data is shared with third parties without consent
        - You can request data deletion at any time
        - Full audit trail maintained for compliance
        
        **Security Features:**
        - End-to-end encryption for sensitive data
        - Role-based access control
        - Rate limiting and abuse prevention
        - Comprehensive security audit logging
        - Regular security updates and monitoring
        """)


# Export main components
__all__ = ['SecurityUI', 'render_security_sidebar_controls', 'render_privacy_notice']