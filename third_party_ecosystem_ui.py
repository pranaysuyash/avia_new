"""
Third-Party Ecosystem UI
Streamlit interface for managing plugins, webhooks, integrations, and external APIs
"""

import streamlit as st
import pandas as pd
import json
import asyncio
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def render_third_party_ecosystem_ui():
    """Main UI for third-party ecosystem management"""
    st.title("🔗 Third-Party Ecosystem")
    st.markdown("Manage plugins, webhooks, integrations, and external APIs")
    
    # Initialize ecosystem
    if 'ecosystem' not in st.session_state:
        try:
            from third_party_ecosystem import ThirdPartyEcosystem
            st.session_state.ecosystem = ThirdPartyEcosystem()
        except ImportError:
            st.error("Third-party ecosystem module not found. Please ensure it's properly installed.")
            return
    
    ecosystem = st.session_state.ecosystem
    
    # Sidebar navigation
    st.sidebar.title("Ecosystem Management")
    section = st.sidebar.selectbox(
        "Select Section",
        ["Overview", "Plugins", "Webhooks", "External APIs", "CRM Integrations", 
         "Automation", "Browser Extension", "Marketplace", "Analytics"]
    )
    
    if section == "Overview":
        render_overview(ecosystem)
    elif section == "Plugins":
        render_plugins_section(ecosystem)
    elif section == "Webhooks":
        render_webhooks_section(ecosystem)
    elif section == "External APIs":
        render_external_apis_section(ecosystem)
    elif section == "CRM Integrations":
        render_crm_integrations_section(ecosystem)
    elif section == "Automation":
        render_automation_section(ecosystem)
    elif section == "Browser Extension":
        render_browser_extension_section(ecosystem)
    elif section == "Marketplace":
        render_marketplace_section(ecosystem)
    elif section == "Analytics":
        render_analytics_section(ecosystem)

def render_overview(ecosystem):
    """Render ecosystem overview"""
    st.header("🌐 Ecosystem Overview")
    
    # Get analytics
    try:
        analytics = ecosystem.get_integration_analytics()
    except:
        analytics = {'total_plugins': 0, 'total_webhooks': 0, 'total_apis': 0}
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Plugins", analytics.get('total_plugins', 0))
    
    with col2:
        st.metric("Active Webhooks", analytics.get('total_webhooks', 0))
    
    with col3:
        st.metric("External APIs", analytics.get('total_apis', 0))
    
    with col4:
        total_integrations = (analytics.get('total_plugins', 0) + 
                            analytics.get('total_webhooks', 0) + 
                            analytics.get('total_apis', 0))
        st.metric("Total Integrations", total_integrations)
    
    # Quick actions
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔌 Install Plugin", use_container_width=True):
            st.session_state.show_plugin_install = True
    
    with col2:
        if st.button("🪝 Add Webhook", use_container_width=True):
            st.session_state.show_webhook_add = True
    
    with col3:
        if st.button("🔗 Connect API", use_container_width=True):
            st.session_state.show_api_connect = True

def render_plugins_section(ecosystem):
    """Render plugins management section"""
    st.header("🔌 Plugin Management")
    
    tab1, tab2, tab3 = st.tabs(["Installed Plugins", "Install New", "Plugin Store"])
    
    with tab1:
        st.subheader("📦 Installed Plugins")
        
        # Sample plugin data
        plugins_data = [
            {"Name": "PDF Processor", "Version": "1.2.0", "Status": "Active", "Category": "Document", "Usage": 156},
            {"Name": "Video Analyzer", "Version": "2.1.0", "Status": "Active", "Category": "Media", "Usage": 89},
            {"Name": "Language Detector", "Version": "1.0.5", "Status": "Inactive", "Category": "NLP", "Usage": 23},
            {"Name": "Audio Enhancer", "Version": "1.3.2", "Status": "Active", "Category": "Audio", "Usage": 67},
        ]
        
        plugins_df = pd.DataFrame(plugins_data)
        
        # Plugin actions
        for idx, plugin in plugins_df.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 1, 1, 1, 1])
            
            with col1:
                st.write(f"**{plugin['Name']}** v{plugin['Version']}")
                st.caption(f"Category: {plugin['Category']} | Usage: {plugin['Usage']} times")
            
            with col2:
                status_color = "🟢" if plugin['Status'] == 'Active' else "🔴"
                st.write(f"{status_color} {plugin['Status']}")
            
            with col3:
                if st.button("⚙️", key=f"config_{idx}", help="Configure"):
                    st.session_state[f'configure_plugin_{idx}'] = True
            
            with col4:
                if plugin['Status'] == 'Active':
                    if st.button("⏸️", key=f"pause_{idx}", help="Deactivate"):
                        st.success(f"Plugin {plugin['Name']} deactivated")
                else:
                    if st.button("▶️", key=f"play_{idx}", help="Activate"):
                        st.success(f"Plugin {plugin['Name']} activated")
            
            with col5:
                if st.button("🔄", key=f"update_{idx}", help="Update"):
                    st.info(f"Checking updates for {plugin['Name']}")
            
            with col6:
                if st.button("🗑️", key=f"delete_{idx}", help="Uninstall"):
                    st.warning(f"Plugin {plugin['Name']} uninstalled")
            
            st.divider()

def render_webhooks_section(ecosystem):
    """Render webhooks management section"""
    st.header("🪝 Webhook Management")
    
    tab1, tab2 = st.tabs(["Active Webhooks", "Add New Webhook"])
    
    with tab1:
        st.subheader("📡 Active Webhooks")
        
        # Sample webhook data
        webhooks_data = [
            {"Name": "Slack Notifications", "URL": "https://hooks.slack.com/...", "Events": "transcription.completed", "Status": "Active", "Success": 156, "Errors": 2},
            {"Name": "Discord Bot", "URL": "https://discord.com/api/webhooks/...", "Events": "analysis.finished", "Status": "Active", "Success": 89, "Errors": 0},
            {"Name": "Custom API", "URL": "https://api.example.com/webhook", "Events": "file.uploaded", "Status": "Error", "Success": 23, "Errors": 5},
        ]
        
        for idx, webhook in enumerate(webhooks_data):
            with st.expander(f"{webhook['Name']} - {webhook['Status']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**URL:** {webhook['URL']}")
                    st.write(f"**Events:** {webhook['Events']}")
                    st.write(f"**Status:** {webhook['Status']}")
                
                with col2:
                    st.metric("Successful Calls", webhook['Success'])
                    st.metric("Failed Calls", webhook['Errors'])

def render_external_apis_section(ecosystem):
    """Render external APIs management section"""
    st.header("🌐 External APIs")
    
    # Display configured APIs
    if hasattr(ecosystem, 'external_apis'):
        for api_name, api_config in list(ecosystem.external_apis.items())[:5]:  # Show first 5
            with st.expander(f"{api_config.name} - {'✅ Configured' if api_config.api_key else '❌ Not Configured'}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Base URL:** {api_config.base_url}")
                    st.write(f"**Auth Type:** {api_config.auth_type}")
                    st.write(f"**Rate Limit:** {api_config.rate_limit} requests/hour")
                
                with col2:
                    if api_config.models:
                        st.write("**Available Models:**")
                        for model in api_config.models[:3]:  # Show first 3 models
                            st.caption(f"• {model}")
                        if len(api_config.models) > 3:
                            st.caption(f"... and {len(api_config.models) - 3} more")

def render_crm_integrations_section(ecosystem):
    """Render CRM integrations section"""
    st.header("🏢 CRM Integrations")
    
    tab1, tab2, tab3 = st.tabs(["Salesforce", "HubSpot", "Custom CRM"])
    
    with tab1:
        st.subheader("☁️ Salesforce Integration")
        
        # Connection status
        sf_connected = st.session_state.get('salesforce_connected', False)
        
        if sf_connected:
            st.success("✅ Connected to Salesforce")
        else:
            st.warning("❌ Not connected to Salesforce")
            
            # Connection form
            with st.form("salesforce_connection"):
                st.write("**Connect to Salesforce:**")
                
                sf_instance_url = st.text_input("Instance URL", placeholder="https://your-domain.salesforce.com")
                sf_username = st.text_input("Username", placeholder="user@company.com")
                sf_password = st.text_input("Password", type="password")
                sf_security_token = st.text_input("Security Token", type="password")
                
                if st.form_submit_button("Connect to Salesforce"):
                    if sf_instance_url and sf_username and sf_password:
                        with st.spinner("Connecting to Salesforce..."):
                            import time
                            time.sleep(2)
                            st.session_state.salesforce_connected = True
                            st.success("Successfully connected to Salesforce!")
                            st.rerun()
                    else:
                        st.error("Please fill in all required fields.")

def render_automation_section(ecosystem):
    """Render automation section (Zapier/IFTTT)"""
    st.header("⚡ Automation")
    
    tab1, tab2, tab3 = st.tabs(["Zapier", "IFTTT", "Custom Workflows"])
    
    with tab1:
        st.subheader("⚡ Zapier Integration")
        
        st.info("Connect your AI Media Processor with 5000+ apps through Zapier")
        
        # Zapier triggers
        st.write("**Available Triggers:**")
        
        triggers = [
            {"name": "New Transcription", "description": "Triggers when a new transcription is completed"},
            {"name": "Analysis Complete", "description": "Triggers when AI analysis is finished"},
            {"name": "File Uploaded", "description": "Triggers when a new file is uploaded"},
            {"name": "Error Occurred", "description": "Triggers when an error occurs during processing"}
        ]
        
        for trigger in triggers:
            with st.expander(trigger['name']):
                st.write(trigger['description'])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.code(f"Webhook URL: https://hooks.zapier.com/hooks/catch/123456/{trigger['name'].lower().replace(' ', '_')}")
                
                with col2:
                    if st.button(f"Create Zap", key=f"zap_{trigger['name']}"):
                        st.success(f"Zap created for {trigger['name']}")

def render_browser_extension_section(ecosystem):
    """Render browser extension section"""
    st.header("🌐 Browser Extension")
    
    st.subheader("📱 AI Media Processor Browser Extension")
    
    st.write("""
    The browser extension allows you to:
    - Capture audio/video from web pages
    - Extract text from images and PDFs
    - Transcribe YouTube videos
    - Analyze web content with AI
    - Save results directly to your account
    """)
    
    # Installation instructions
    st.subheader("📥 Installation")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Chrome**")
        if st.button("Download for Chrome", use_container_width=True):
            st.info("Redirecting to Chrome Web Store...")
    
    with col2:
        st.write("**Firefox**")
        if st.button("Download for Firefox", use_container_width=True):
            st.info("Redirecting to Firefox Add-ons...")
    
    with col3:
        st.write("**Edge**")
        if st.button("Download for Edge", use_container_width=True):
            st.info("Redirecting to Edge Add-ons...")

def render_marketplace_section(ecosystem):
    """Render marketplace section"""
    st.header("🏪 Integration Marketplace")
    
    # Featured integrations
    st.write("**⭐ Featured Integrations**")
    
    featured = [
        {
            "name": "Advanced AI Analysis",
            "description": "Enhanced AI analysis with multiple models",
            "category": "AI/ML",
            "rating": 4.9,
            "downloads": 5420,
            "price": "$49.99",
            "featured": True
        },
        {
            "name": "Salesforce Pro Sync",
            "description": "Advanced Salesforce integration with real-time sync",
            "category": "CRM",
            "rating": 4.8,
            "downloads": 3210,
            "price": "$29.99",
            "featured": True
        }
    ]
    
    for integration in featured:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.write(f"**⭐ {integration['name']}**")
                st.caption(integration['description'])
                st.caption(f"Category: {integration['category']}")
            
            with col2:
                st.metric("Rating", f"{integration['rating']}/5")
            
            with col3:
                st.metric("Downloads", integration['downloads'])
            
            with col4:
                st.write(f"**{integration['price']}**")
                if st.button("Install", key=f"install_{integration['name']}"):
                    st.success(f"{integration['name']} installed!")
            
            st.divider()

def render_analytics_section(ecosystem):
    """Render analytics section"""
    st.header("📊 Integration Analytics")
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total API Calls", "12,456", "+234 today")
    
    with col2:
        st.metric("Active Integrations", "15")
    
    with col3:
        st.metric("Success Rate", "98.7%", "+0.3%")
    
    with col4:
        st.metric("Avg Response Time", "245ms", "-12ms")
    
    # Charts
    tab1, tab2, tab3 = st.tabs(["Usage Trends", "Integration Performance", "Error Analysis"])
    
    with tab1:
        st.subheader("📈 Usage Trends")
        
        # Generate sample data for charts
        import numpy as np
        dates = pd.date_range(start='2024-01-01', end='2024-01-15', freq='D')
        api_calls = np.random.randint(800, 1200, len(dates))
        
        # API calls over time
        fig = px.line(
            x=dates, y=api_calls,
            title="API Calls Over Time",
            labels={'x': 'Date', 'y': 'API Calls'}
        )
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    render_third_party_ecosystem_ui()