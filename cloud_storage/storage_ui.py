"""
Streamlit UI components for cloud storage management
"""

import streamlit as st
from typing import Dict, Any
from .storage_manager import cloud_storage_manager, StorageProviderType


def render_cloud_storage_settings():
    """Render cloud storage management interface"""
    
    st.header("☁️ Cloud Storage Settings")
    
    # System status
    stats = cloud_storage_manager.get_stats()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Providers", stats['total_providers'])
    with col2:
        st.metric("Available Providers", len(stats['available_providers']))
    with col3:
        st.metric("Default Provider", stats['default_provider'] or "None")
    
    # Provider configuration tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📁 Google Drive", "📦 Dropbox", "🪣 AWS S3", "📊 Status"])
    
    with tab1:
        render_google_drive_config()
    
    with tab2:
        render_dropbox_config()
    
    with tab3:
        render_s3_config()
    
    with tab4:
        render_storage_status()


def render_google_drive_config():
    """Render Google Drive configuration"""
    
    st.subheader("Google Drive Configuration")
    
    with st.form("google_drive_form"):
        st.write("**OAuth 2.0 Credentials:**")
        
        client_id = st.text_input(
            "Client ID",
            type="password",
            help="Google OAuth 2.0 Client ID"
        )
        
        client_secret = st.text_input(
            "Client Secret", 
            type="password",
            help="Google OAuth 2.0 Client Secret"
        )
        
        refresh_token = st.text_input(
            "Refresh Token (Optional)",
            type="password",
            help="Pre-obtained refresh token"
        )
        
        submitted = st.form_submit_button("Configure Google Drive")
        
        if submitted:
            if client_id and client_secret:
                st.success("✅ Google Drive configuration saved!")
                st.info("🔗 In a real implementation, this would initiate OAuth flow")
            else:
                st.error("❌ Please provide both Client ID and Client Secret")
    
    st.write("---")
    st.write("**Setup Instructions:**")
    st.write("1. Go to Google Cloud Console")
    st.write("2. Create a new project or select existing")
    st.write("3. Enable Google Drive API")
    st.write("4. Create OAuth 2.0 credentials")
    st.write("5. Add authorized redirect URIs")


def render_dropbox_config():
    """Render Dropbox configuration"""
    
    st.subheader("Dropbox Configuration")
    
    with st.form("dropbox_form"):
        st.write("**App Credentials:**")
        
        access_token = st.text_input(
            "Access Token",
            type="password",
            help="Dropbox App Access Token"
        )
        
        submitted = st.form_submit_button("Configure Dropbox")
        
        if submitted:
            if access_token:
                st.success("✅ Dropbox configuration saved!")
                st.info("🔗 In a real implementation, this would test the connection")
            else:
                st.error("❌ Please provide Access Token")
    
    st.write("---")
    st.write("**Setup Instructions:**")
    st.write("1. Go to Dropbox App Console")
    st.write("2. Create a new app")
    st.write("3. Choose 'Scoped access' and 'Full Dropbox'")
    st.write("4. Generate access token")
    st.write("5. Set required permissions")


def render_s3_config():
    """Render AWS S3 configuration"""
    
    st.subheader("AWS S3 Configuration")
    
    with st.form("s3_form"):
        st.write("**AWS Credentials:**")
        
        access_key_id = st.text_input(
            "Access Key ID",
            type="password",
            help="AWS Access Key ID"
        )
        
        secret_access_key = st.text_input(
            "Secret Access Key",
            type="password", 
            help="AWS Secret Access Key"
        )
        
        bucket_name = st.text_input(
            "Bucket Name",
            help="S3 bucket name for storage"
        )
        
        region = st.selectbox(
            "Region",
            options=[
                "us-east-1", "us-east-2", "us-west-1", "us-west-2",
                "eu-west-1", "eu-west-2", "eu-central-1",
                "ap-southeast-1", "ap-southeast-2", "ap-northeast-1"
            ],
            index=0
        )
        
        submitted = st.form_submit_button("Configure S3")
        
        if submitted:
            if access_key_id and secret_access_key and bucket_name:
                st.success("✅ S3 configuration saved!")
                st.info("🔗 In a real implementation, this would test bucket access")
            else:
                st.error("❌ Please provide all required fields")
    
    st.write("---")
    st.write("**Setup Instructions:**")
    st.write("1. Create AWS account and IAM user")
    st.write("2. Attach S3 permissions policy")
    st.write("3. Generate access keys")
    st.write("4. Create S3 bucket")
    st.write("5. Configure bucket permissions")


def render_storage_status():
    """Render storage system status"""
    
    st.subheader("Storage System Status")
    
    stats = cloud_storage_manager.get_stats()
    
    # Provider status
    st.write("**Configured Providers:**")
    for provider in stats['available_providers']:
        provider_name = provider.replace('_', ' ').title()
        st.write(f"• {provider_name}")
    
    if not stats['available_providers']:
        st.info("No cloud storage providers configured")
    
    # Default provider
    if stats['default_provider']:
        st.write(f"**Default Provider:** {stats['default_provider'].replace('_', ' ').title()}")
    else:
        st.warning("No default provider set")
    
    # Test connections
    st.write("---")
    st.write("**Connection Tests:**")
    
    if st.button("🧪 Test All Connections"):
        with st.spinner("Testing connections..."):
            # Mock connection tests
            for provider in stats['available_providers']:
                provider_name = provider.replace('_', ' ').title()
                st.write(f"✅ {provider_name}: Connected (Mock)")
    
    # Usage statistics (mock)
    st.write("---")
    st.write("**Usage Statistics:**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Files Uploaded", "42")
    with col2:
        st.metric("Total Size", "1.2 GB")
    with col3:
        st.metric("Last Backup", "2 hours ago")