"""
Streamlit UI components for SSO management
"""

import streamlit as st
from typing import Dict, Any
from .sso_manager import sso_manager, SSOProviderType


def render_sso_settings():
    """Render SSO management interface"""
    
    st.header("🔐 Single Sign-On (SSO) Settings")
    
    if not sso_manager:
        st.warning("⚠️ SSO system not initialized")
        st.info("SSO requires proper configuration in your environment settings.")
        return
    
    # System status
    stats = sso_manager.get_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Providers", stats['total_providers'])
    with col2:
        st.metric("Enabled Providers", stats['enabled_providers'])
    with col3:
        st.metric("Active Sessions", stats['active_sessions'])
    with col4:
        st.metric("Total Sessions", stats['total_sessions'])
    
    # Provider configuration tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔑 OAuth Providers", "🏢 SAML Providers", "🌐 OIDC Providers", "📊 Sessions"])
    
    with tab1:
        render_oauth_providers()
    
    with tab2:
        render_saml_providers()
    
    with tab3:
        render_oidc_providers()
    
    with tab4:
        render_sso_sessions()


def render_oauth_providers():
    """Render OAuth provider configuration"""
    
    st.subheader("OAuth 2.0 Providers")
    
    # Add new OAuth provider
    with st.expander("➕ Add OAuth Provider"):
        with st.form("oauth_provider_form"):
            provider_name = st.text_input("Provider Name", placeholder="e.g., Google, Microsoft, GitHub")
            
            col1, col2 = st.columns(2)
            with col1:
                client_id = st.text_input("Client ID", type="password")
                authorization_url = st.text_input(
                    "Authorization URL",
                    placeholder="https://accounts.google.com/oauth/authorize"
                )
            
            with col2:
                client_secret = st.text_input("Client Secret", type="password")
                token_url = st.text_input(
                    "Token URL", 
                    placeholder="https://oauth2.googleapis.com/token"
                )
            
            user_info_url = st.text_input(
                "User Info URL",
                placeholder="https://www.googleapis.com/oauth2/v2/userinfo"
            )
            
            scopes = st.text_input(
                "Scopes",
                placeholder="openid email profile",
                help="Space-separated list of OAuth scopes"
            )
            
            submitted = st.form_submit_button("Add OAuth Provider")
            
            if submitted:
                if provider_name and client_id and client_secret:
                    st.success(f"✅ OAuth provider '{provider_name}' added!")
                    st.info("🔗 In a real implementation, this would register the provider")
                else:
                    st.error("❌ Please fill in all required fields")
    
    # Existing OAuth providers (mock)
    st.write("**Configured OAuth Providers:**")
    
    mock_oauth_providers = [
        {
            'name': 'Google',
            'client_id': 'google-client-id',
            'enabled': True,
            'users': 45
        },
        {
            'name': 'Microsoft',
            'client_id': 'microsoft-client-id', 
            'enabled': True,
            'users': 23
        },
        {
            'name': 'GitHub',
            'client_id': 'github-client-id',
            'enabled': False,
            'users': 8
        }
    ]
    
    for provider in mock_oauth_providers:
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                status_icon = "✅" if provider['enabled'] else "❌"
                st.write(f"{status_icon} **{provider['name']}**")
                st.write(f"Client ID: `{provider['client_id'][:12]}...`")
            
            with col2:
                st.metric("Users", provider['users'])
            
            with col3:
                if provider['enabled']:
                    if st.button("⏸️ Disable", key=f"disable_oauth_{provider['name']}"):
                        st.success(f"Disabled {provider['name']}")
                        st.rerun()
                else:
                    if st.button("▶️ Enable", key=f"enable_oauth_{provider['name']}"):
                        st.success(f"Enabled {provider['name']}")
                        st.rerun()
            
            with col4:
                if st.button("⚙️ Configure", key=f"config_oauth_{provider['name']}"):
                    st.info(f"Configuration for {provider['name']} would open here")
            
            st.write("---")


def render_saml_providers():
    """Render SAML provider configuration"""
    
    st.subheader("SAML 2.0 Providers")
    
    # Add new SAML provider
    with st.expander("➕ Add SAML Provider"):
        with st.form("saml_provider_form"):
            provider_name = st.text_input("Provider Name", placeholder="e.g., Active Directory, Okta")
            
            col1, col2 = st.columns(2)
            with col1:
                entity_id = st.text_input("Entity ID")
                sso_url = st.text_input("SSO URL")
            
            with col2:
                x509_cert = st.text_area("X.509 Certificate", height=100)
            
            submitted = st.form_submit_button("Add SAML Provider")
            
            if submitted:
                if provider_name and entity_id and sso_url:
                    st.success(f"✅ SAML provider '{provider_name}' added!")
                    st.info("🔗 In a real implementation, this would register the provider")
                else:
                    st.error("❌ Please fill in all required fields")
    
    # SAML configuration help
    st.write("**SAML Configuration Help:**")
    st.info("""
    📋 **Required Information:**
    • Entity ID (Issuer)
    • Single Sign-On URL
    • X.509 Certificate
    • Attribute mappings (email, name, groups)
    
    🔧 **Service Provider Settings:**
    • SP Entity ID: `https://your-app.com/saml/metadata`
    • ACS URL: `https://your-app.com/saml/acs`
    • Binding: HTTP-POST
    """)
    
    # Mock SAML providers
    st.write("**Configured SAML Providers:**")
    st.info("No SAML providers configured. Add one above to get started.")


def render_oidc_providers():
    """Render OpenID Connect provider configuration"""
    
    st.subheader("OpenID Connect (OIDC) Providers")
    
    # Add new OIDC provider
    with st.expander("➕ Add OIDC Provider"):
        with st.form("oidc_provider_form"):
            provider_name = st.text_input("Provider Name", placeholder="e.g., Auth0, Keycloak")
            
            col1, col2 = st.columns(2)
            with col1:
                issuer_url = st.text_input(
                    "Issuer URL",
                    placeholder="https://your-domain.auth0.com/"
                )
                client_id = st.text_input("Client ID", type="password")
            
            with col2:
                client_secret = st.text_input("Client Secret", type="password")
                redirect_uri = st.text_input(
                    "Redirect URI",
                    placeholder="https://your-app.com/auth/callback"
                )
            
            submitted = st.form_submit_button("Add OIDC Provider")
            
            if submitted:
                if provider_name and issuer_url and client_id:
                    st.success(f"✅ OIDC provider '{provider_name}' added!")
                    st.info("🔗 In a real implementation, this would register the provider")
                else:
                    st.error("❌ Please fill in all required fields")
    
    # OIDC configuration help
    st.write("**OIDC Configuration Help:**")
    st.info("""
    📋 **Required Information:**
    • Issuer URL (Discovery endpoint)
    • Client ID and Secret
    • Redirect URI
    • Scopes (openid, email, profile)
    
    🔧 **Discovery:**
    OIDC providers expose a discovery document at:
    `{issuer}/.well-known/openid_configuration`
    """)
    
    # Mock OIDC providers
    st.write("**Configured OIDC Providers:**")
    st.info("No OIDC providers configured. Add one above to get started.")


def render_sso_sessions():
    """Render SSO session management"""
    
    st.subheader("SSO Sessions")
    
    # Session statistics
    if sso_manager:
        stats = sso_manager.get_stats()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Active Sessions", stats['active_sessions'])
        with col2:
            st.metric("Total Sessions", stats['total_sessions'])
        with col3:
            st.metric("Pending States", stats['pending_states'])
    
    # Mock active sessions
    st.write("**Active Sessions:**")
    
    mock_sessions = [
        {
            'user': 'john.doe@company.com',
            'provider': 'Google',
            'created': '2024-01-08 10:30:00',
            'expires': '2024-01-09 10:30:00',
            'ip': '192.168.1.100'
        },
        {
            'user': 'jane.smith@company.com',
            'provider': 'Microsoft',
            'created': '2024-01-08 09:15:00',
            'expires': '2024-01-09 09:15:00',
            'ip': '192.168.1.101'
        }
    ]
    
    for i, session in enumerate(mock_sessions):
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.write(f"**{session['user']}**")
                st.write(f"Provider: {session['provider']}")
                st.write(f"IP: {session['ip']}")
            
            with col2:
                st.write("**Created:**")
                st.write(session['created'])
            
            with col3:
                st.write("**Expires:**")
                st.write(session['expires'])
            
            with col4:
                if st.button("🚪 Logout", key=f"logout_session_{i}"):
                    st.success(f"Logged out {session['user']}")
                    st.rerun()
            
            st.write("---")
    
    if not mock_sessions:
        st.info("No active SSO sessions")
    
    # Session management actions
    st.write("**Session Management:**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🧹 Cleanup Expired"):
            st.success("Cleaned up expired sessions")
    
    with col2:
        if st.button("📊 Export Sessions"):
            st.info("Session data would be exported")
    
    with col3:
        if st.button("🔄 Refresh Stats"):
            st.rerun()