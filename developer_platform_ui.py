"""
Developer Platform UI
Provides a comprehensive interface for API management, documentation, and developer tools.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import requests
from typing import Dict, List, Optional
import time
import yaml
from api_platform_system import (
    APIManager, DeveloperPortal, SDKGenerator,
    WebhookManager, APIAnalytics
)

class DeveloperPlatformUI:
    def __init__(self):
        if 'api_manager' not in st.session_state:
            st.session_state.api_manager = APIManager()
        if 'developer_portal' not in st.session_state:
            st.session_state.developer_portal = DeveloperPortal()
        if 'sdk_generator' not in st.session_state:
            st.session_state.sdk_generator = SDKGenerator()
        if 'webhook_manager' not in st.session_state:
            st.session_state.webhook_manager = WebhookManager()
        if 'api_analytics' not in st.session_state:
            st.session_state.api_analytics = APIAnalytics()
        
        self.api_manager = st.session_state.api_manager
        self.developer_portal = st.session_state.developer_portal
        self.sdk_generator = st.session_state.sdk_generator
        self.webhook_manager = st.session_state.webhook_manager
        self.api_analytics = st.session_state.api_analytics
    
    def render_sidebar(self):
        """Render the sidebar navigation"""
        st.sidebar.title("🚀 Developer Platform")
        
        pages = {
            "📊 Dashboard": "dashboard",
            "🔑 API Keys": "api_keys",
            "📚 Documentation": "documentation",
            "⚡ API Explorer": "explorer",
            "🔗 Webhooks": "webhooks",
            "📦 SDK Generator": "sdk",
            "📈 Analytics": "analytics",
            "💻 Code Examples": "examples",
            "🛠️ API Versioning": "versioning",
            "👥 Community": "community"
        }
        
        selected_page = st.sidebar.radio(
            "Navigation",
            list(pages.keys()),
            format_func=lambda x: x
        )
        
        return pages[selected_page]
    
    def render_dashboard(self):
        """Render the main dashboard"""
        st.header("📊 Developer Dashboard")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Active API Keys", "12", "+2")
        
        with col2:
            st.metric("API Calls Today", "45.2K", "+15%")
        
        with col3:
            st.metric("Active Webhooks", "8", "0")
        
        with col4:
            st.metric("SDK Downloads", "324", "+23")
        
        # Usage chart
        st.subheader("API Usage Overview")
        
        # Generate sample data
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        usage_data = pd.DataFrame({
            'Date': dates,
            'Transcription': [1000 + i*50 + (i%7)*200 for i in range(30)],
            'NER': [500 + i*30 + (i%5)*100 for i in range(30)],
            'Analytics': [300 + i*20 + (i%3)*50 for i in range(30)]
        })
        
        fig = px.line(usage_data, x='Date', y=['Transcription', 'NER', 'Analytics'],
                      title='API Usage Trends (Last 30 Days)')
        st.plotly_chart(fig, use_container_width=True)
        
        # Recent activity
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Recent API Activity")
            activity_data = {
                'Endpoint': ['/api/v1/transcribe', '/api/v1/analyze', '/api/v1/extract'],
                'Calls': [15234, 8921, 6543],
                'Avg Response': ['245ms', '189ms', '167ms'],
                'Success Rate': ['99.8%', '99.5%', '99.9%']
            }
            st.dataframe(pd.DataFrame(activity_data))
        
        with col2:
            st.subheader("Top Applications")
            app_data = {
                'Application': ['Mobile App', 'Web Dashboard', 'Data Pipeline'],
                'API Calls': [23456, 18234, 12890],
                'Last Active': ['2 min ago', '5 min ago', '12 min ago']
            }
            st.dataframe(pd.DataFrame(app_data))
    
    def render_api_keys(self):
        """Render API key management interface"""
        st.header("🔑 API Key Management")
        
        tabs = st.tabs(["Active Keys", "Create New", "Usage Limits"])
        
        with tabs[0]:
            st.subheader("Your API Keys")
            
            # Sample API keys
            keys_data = {
                'Name': ['Production API', 'Development API', 'Testing Key'],
                'Key': ['sk_live_ABC...XYZ', 'sk_test_DEF...UVW', 'sk_test_GHI...RST'],
                'Created': ['2024-01-15', '2024-02-01', '2024-02-10'],
                'Last Used': ['2 min ago', '1 hour ago', '3 days ago'],
                'Status': ['Active', 'Active', 'Active']
            }
            
            df = pd.DataFrame(keys_data)
            
            for idx, row in df.iterrows():
                col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
                
                with col1:
                    st.text(row['Name'])
                
                with col2:
                    if st.button(f"Show {idx}", key=f"show_{idx}"):
                        st.code(f"sk_{'live' if 'live' in row['Key'] else 'test'}_{'x'*32}")
                
                with col3:
                    st.text(f"Last used: {row['Last Used']}")
                
                with col4:
                    if st.button("🗑️", key=f"del_{idx}"):
                        st.warning("Key deletion requested")
            
        with tabs[1]:
            st.subheader("Create New API Key")
            
            key_name = st.text_input("Key Name", placeholder="e.g., Production API")
            key_type = st.selectbox("Key Type", ["Production", "Development", "Testing"])
            
            st.subheader("Permissions")
            col1, col2 = st.columns(2)
            
            with col1:
                st.checkbox("Transcription API", value=True)
                st.checkbox("NER API", value=True)
                st.checkbox("Analytics API", value=True)
            
            with col2:
                st.checkbox("Webhook Management")
                st.checkbox("Account Management")
                st.checkbox("Billing Access")
            
            if st.button("Generate API Key", type="primary"):
                new_key = self.api_manager.generate_api_key(key_name)
                st.success("API Key Generated Successfully!")
                st.code(new_key)
                st.warning("⚠️ Save this key securely. It won't be shown again!")
        
        with tabs[2]:
            st.subheader("Usage Limits & Quotas")
            
            # Rate limits
            st.write("**Rate Limits**")
            limits_data = {
                'Tier': ['Free', 'Starter', 'Professional', 'Enterprise'],
                'Requests/Min': [10, 60, 300, 'Unlimited'],
                'Requests/Day': ['1K', '10K', '100K', 'Unlimited'],
                'Concurrent': [1, 5, 20, 100]
            }
            st.dataframe(pd.DataFrame(limits_data))
            
            # Current usage
            st.write("**Your Current Usage**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Today's Requests", "8,234 / 10,000", "82%")
            
            with col2:
                st.metric("This Minute", "45 / 60", "75%")
            
            with col3:
                st.metric("Concurrent", "3 / 5", "60%")
    
    def render_documentation(self):
        """Render API documentation"""
        st.header("📚 API Documentation")
        
        # Documentation sections
        sections = st.tabs(["Getting Started", "API Reference", "SDKs", "Guides", "Changelog"])
        
        with sections[0]:
            st.subheader("Getting Started with Video NER API")
            
            st.markdown("""
            ### Quick Start
            
            1. **Get your API Key**
               - Sign up for an account
               - Generate an API key from the dashboard
               - Keep it secure!
            
            2. **Make your first request**
            """)
            
            st.code("""
            curl -X POST https://api.vidner.com/v1/transcribe \\
              -H "Authorization: Bearer YOUR_API_KEY" \\
              -H "Content-Type: application/json" \\
              -d '{
                "video_url": "https://example.com/video.mp4",
                "language": "en",
                "enable_ner": true
              }'
            """, language="bash")
            
            st.markdown("""
            3. **Handle the response**
            """)
            
            st.code("""
            {
              "id": "txn_1234567890",
              "status": "processing",
              "created_at": "2024-02-15T10:30:00Z",
              "webhook_url": "https://your-app.com/webhook"
            }
            """, language="json")
        
        with sections[1]:
            st.subheader("API Reference")
            
            # Endpoint selector
            endpoint = st.selectbox(
                "Select Endpoint",
                [
                    "POST /v1/transcribe",
                    "GET /v1/transcription/{id}",
                    "POST /v1/analyze",
                    "GET /v1/entities",
                    "POST /v1/webhooks"
                ]
            )
            
            if "transcribe" in endpoint:
                st.markdown("""
                ### POST /v1/transcribe
                
                Transcribe video content with optional NER processing.
                
                **Request Body**
                """)
                
                st.code("""
                {
                  "video_url": "string",      // Required: URL of the video
                  "language": "string",       // Optional: Language code (default: auto-detect)
                  "enable_ner": boolean,      // Optional: Enable NER (default: true)
                  "webhook_url": "string",    // Optional: Webhook for results
                  "custom_vocabulary": []     // Optional: Custom terms
                }
                """, language="json")
                
                st.markdown("""
                **Response**
                """)
                
                st.code("""
                {
                  "id": "string",
                  "status": "queued|processing|completed|failed",
                  "created_at": "datetime",
                  "estimated_completion": "datetime",
                  "webhook_url": "string"
                }
                """, language="json")
        
        with sections[2]:
            st.subheader("SDKs & Libraries")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                ### Python
                ```bash
                pip install vidner-python
                ```
                
                ```python
                from vidner import Client
                
                client = Client(api_key="YOUR_KEY")
                result = client.transcribe(
                    video_url="...",
                    enable_ner=True
                )
                ```
                """)
            
            with col2:
                st.markdown("""
                ### JavaScript
                ```bash
                npm install @vidner/sdk
                ```
                
                ```javascript
                const VidNER = require('@vidner/sdk');
                
                const client = new VidNER('YOUR_KEY');
                const result = await client.transcribe({
                    videoUrl: '...',
                    enableNER: true
                });
                ```
                """)
            
            with col3:
                st.markdown("""
                ### Go
                ```bash
                go get github.com/vidner/go-sdk
                ```
                
                ```go
                import "github.com/vidner/go-sdk"
                
                client := vidner.NewClient("YOUR_KEY")
                result, err := client.Transcribe(
                    vidner.TranscribeOptions{
                        VideoURL: "...",
                        EnableNER: true,
                    }
                )
                ```
                """)
    
    def render_api_explorer(self):
        """Render interactive API explorer"""
        st.header("⚡ API Explorer")
        st.write("Test API endpoints interactively")
        
        # Endpoint selection
        col1, col2 = st.columns([1, 3])
        
        with col1:
            method = st.selectbox("Method", ["GET", "POST", "PUT", "DELETE"])
        
        with col2:
            endpoint = st.text_input("Endpoint", value="/v1/transcribe")
        
        # Headers
        st.subheader("Headers")
        if st.checkbox("Add Authentication", value=True):
            api_key = st.text_input("API Key", type="password", value="sk_test_...")
        
        # Request body
        if method in ["POST", "PUT"]:
            st.subheader("Request Body")
            request_body = st.text_area(
                "JSON Body",
                value=json.dumps({
                    "video_url": "https://example.com/sample.mp4",
                    "language": "en",
                    "enable_ner": True
                }, indent=2),
                height=200
            )
        
        # Send request button
        if st.button("Send Request", type="primary"):
            with st.spinner("Sending request..."):
                time.sleep(1)  # Simulate API call
                
                # Mock response
                st.subheader("Response")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Status", "200 OK")
                with col2:
                    st.metric("Time", "245ms")
                with col3:
                    st.metric("Size", "1.2 KB")
                
                st.code(json.dumps({
                    "id": "txn_" + str(uuid.uuid4())[:8],
                    "status": "processing",
                    "created_at": datetime.now().isoformat(),
                    "estimated_completion": (datetime.now() + timedelta(minutes=5)).isoformat()
                }, indent=2), language="json")
    
    def render_webhooks(self):
        """Render webhook management interface"""
        st.header("🔗 Webhook Management")
        
        tabs = st.tabs(["Active Webhooks", "Create Webhook", "Event Logs"])
        
        with tabs[0]:
            st.subheader("Your Webhooks")
            
            webhooks = [
                {
                    "name": "Production Webhook",
                    "url": "https://app.example.com/webhook",
                    "events": ["transcription.completed", "analysis.completed"],
                    "status": "Active",
                    "last_triggered": "5 min ago"
                },
                {
                    "name": "Error Handler",
                    "url": "https://app.example.com/errors",
                    "events": ["transcription.failed", "analysis.failed"],
                    "status": "Active",
                    "last_triggered": "2 hours ago"
                }
            ]
            
            for webhook in webhooks:
                with st.expander(f"🔗 {webhook['name']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**URL:** `{webhook['url']}`")
                        st.write(f"**Status:** {webhook['status']}")
                        st.write(f"**Last Triggered:** {webhook['last_triggered']}")
                    
                    with col2:
                        st.write("**Events:**")
                        for event in webhook['events']:
                            st.write(f"- {event}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("Test", key=f"test_{webhook['name']}"):
                            st.success("Test event sent!")
                    with col2:
                        if st.button("Edit", key=f"edit_{webhook['name']}"):
                            st.info("Edit mode")
                    with col3:
                        if st.button("Delete", key=f"del_{webhook['name']}"):
                            st.warning("Delete confirmation needed")
        
        with tabs[1]:
            st.subheader("Create New Webhook")
            
            webhook_name = st.text_input("Webhook Name")
            webhook_url = st.text_input("Webhook URL", placeholder="https://your-app.com/webhook")
            
            st.write("**Select Events**")
            col1, col2 = st.columns(2)
            
            with col1:
                st.checkbox("transcription.started")
                st.checkbox("transcription.completed")
                st.checkbox("transcription.failed")
            
            with col2:
                st.checkbox("analysis.started")
                st.checkbox("analysis.completed")
                st.checkbox("analysis.failed")
            
            st.write("**Security**")
            signing_secret = st.text_input(
                "Signing Secret (optional)",
                help="We'll use this to sign webhook payloads"
            )
            
            if st.button("Create Webhook", type="primary"):
                st.success("Webhook created successfully!")
                st.code(f"Webhook ID: wh_{uuid.uuid4().hex[:12]}")
        
        with tabs[2]:
            st.subheader("Webhook Event Logs")
            
            # Filter options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.selectbox("Webhook", ["All", "Production Webhook", "Error Handler"])
            
            with col2:
                st.selectbox("Status", ["All", "Success", "Failed", "Pending"])
            
            with col3:
                st.selectbox("Time Range", ["Last Hour", "Last 24 Hours", "Last 7 Days"])
            
            # Event logs
            events = [
                {
                    "timestamp": "2024-02-15 14:32:15",
                    "webhook": "Production Webhook",
                    "event": "transcription.completed",
                    "status": "Success",
                    "response_time": "145ms"
                },
                {
                    "timestamp": "2024-02-15 14:30:42",
                    "webhook": "Production Webhook",
                    "event": "analysis.completed",
                    "status": "Success",
                    "response_time": "203ms"
                },
                {
                    "timestamp": "2024-02-15 14:28:10",
                    "webhook": "Error Handler",
                    "event": "transcription.failed",
                    "status": "Failed",
                    "response_time": "Timeout"
                }
            ]
            
            df = pd.DataFrame(events)
            st.dataframe(df, use_container_width=True)
    
    def render_sdk_generator(self):
        """Render SDK generator interface"""
        st.header("📦 SDK Generator")
        st.write("Generate client libraries for your preferred language")
        
        col1, col2 = st.columns(2)
        
        with col1:
            language = st.selectbox(
                "Select Language",
                ["Python", "JavaScript", "TypeScript", "Go", "Java", "Ruby", "PHP", "C#"]
            )
            
            st.write("**Configuration Options**")
            include_examples = st.checkbox("Include code examples", value=True)
            include_tests = st.checkbox("Include test suite", value=True)
            async_support = st.checkbox("Async/await support", value=True)
            
        with col2:
            st.write("**Package Information**")
            package_name = st.text_input("Package Name", value=f"vidner-{language.lower()}")
            version = st.text_input("Version", value="1.0.0")
            author = st.text_input("Author", value="Your Name")
            
        if st.button("Generate SDK", type="primary"):
            with st.spinner(f"Generating {language} SDK..."):
                # Generate SDK
                sdk_path = self.sdk_generator.generate_sdk(
                    language=language.lower(),
                    config={
                        "package_name": package_name,
                        "version": version,
                        "include_examples": include_examples,
                        "include_tests": include_tests,
                        "async_support": async_support
                    }
                )
                
                st.success(f"SDK generated successfully!")
                
                # Show generated files
                st.subheader("Generated Files")
                st.code("""
                vidner-python/
                ├── README.md
                ├── setup.py
                ├── requirements.txt
                ├── vidner/
                │   ├── __init__.py
                │   ├── client.py
                │   ├── models.py
                │   ├── exceptions.py
                │   └── utils.py
                ├── examples/
                │   ├── basic_usage.py
                │   ├── async_example.py
                │   └── webhook_handler.py
                └── tests/
                    ├── test_client.py
                    ├── test_models.py
                    └── test_utils.py
                """)
                
                # Download button
                st.download_button(
                    label="Download SDK",
                    data="SDK package data",  # In real implementation, this would be the actual SDK package
                    file_name=f"{package_name}-{version}.zip",
                    mime="application/zip"
                )
    
    def render_analytics(self):
        """Render API analytics dashboard"""
        st.header("📈 API Analytics")
        
        # Time range selector
        time_range = st.selectbox(
            "Time Range",
            ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "Last 90 Days"]
        )
        
        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Requests", "1.2M", "+15.3%")
        
        with col2:
            st.metric("Success Rate", "99.8%", "+0.2%")
        
        with col3:
            st.metric("Avg Response Time", "187ms", "-23ms")
        
        with col4:
            st.metric("Active Users", "342", "+28")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Request Volume")
            
            # Generate sample data
            hours = list(range(24))
            requests = [1000 + h*100 + (h%6)*200 for h in hours]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hours, y=requests,
                mode='lines+markers',
                name='Requests'
            ))
            fig.update_layout(
                xaxis_title="Hour of Day",
                yaxis_title="Requests",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Response Times")
            
            # Generate sample data
            endpoints = ['Transcribe', 'Analyze', 'Extract', 'Search']
            avg_times = [245, 189, 156, 98]
            p95_times = [412, 298, 234, 145]
            
            fig = go.Figure()
            fig.add_trace(go.Bar(name='Average', x=endpoints, y=avg_times))
            fig.add_trace(go.Bar(name='95th Percentile', x=endpoints, y=p95_times))
            fig.update_layout(
                barmode='group',
                xaxis_title="Endpoint",
                yaxis_title="Response Time (ms)",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Error analysis
        st.subheader("Error Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            error_data = {
                'Error Type': ['Rate Limit', 'Invalid Request', 'Server Error', 'Timeout'],
                'Count': [234, 156, 45, 23],
                'Percentage': ['51.3%', '34.2%', '9.9%', '5.0%']
            }
            st.dataframe(pd.DataFrame(error_data))
        
        with col2:
            # Error trend chart
            fig = px.pie(
                values=[234, 156, 45, 23],
                names=['Rate Limit', 'Invalid Request', 'Server Error', 'Timeout'],
                title="Error Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Top users
        st.subheader("Top API Consumers")
        
        users_data = {
            'Application': ['Mobile App Pro', 'Data Analytics Tool', 'Web Dashboard', 'Research Platform'],
            'Requests': [234567, 189234, 156789, 123456],
            'Success Rate': ['99.9%', '99.7%', '99.8%', '99.5%'],
            'Avg Response': ['156ms', '234ms', '189ms', '267ms']
        }
        st.dataframe(pd.DataFrame(users_data), use_container_width=True)
    
    def render_code_examples(self):
        """Render code examples section"""
        st.header("💻 Code Examples")
        
        # Language selector
        language = st.selectbox(
            "Select Language",
            ["Python", "JavaScript", "Go", "Java", "cURL"]
        )
        
        # Example categories
        example_type = st.selectbox(
            "Example Type",
            ["Basic Usage", "Async Operations", "Webhook Handling", "Error Handling", "Batch Processing"]
        )
        
        if language == "Python" and example_type == "Basic Usage":
            st.code("""
import vidner

# Initialize client
client = vidner.Client(api_key="your_api_key")

# Transcribe a video
response = client.transcribe(
    video_url="https://example.com/video.mp4",
    language="en",
    enable_ner=True
)

print(f"Transcription ID: {response.id}")
print(f"Status: {response.status}")

# Wait for completion
result = client.wait_for_completion(response.id)

# Process results
for entity in result.entities:
    print(f"Entity: {entity.text} ({entity.type})")
    print(f"Confidence: {entity.confidence}")
    print(f"Timestamp: {entity.timestamp}")
            """, language="python")
        
        elif language == "JavaScript" and example_type == "Async Operations":
            st.code("""
const VidNER = require('@vidner/sdk');

const client = new VidNER({
    apiKey: 'your_api_key'
});

async function processVideo(videoUrl) {
    try {
        // Start transcription
        const job = await client.transcribe({
            videoUrl: videoUrl,
            language: 'en',
            enableNER: true,
            webhookUrl: 'https://your-app.com/webhook'
        });
        
        console.log(`Job started: ${job.id}`);
        
        // Poll for completion
        const result = await client.waitForCompletion(job.id, {
            interval: 5000,  // Poll every 5 seconds
            timeout: 300000  // Timeout after 5 minutes
        });
        
        // Process entities
        result.entities.forEach(entity => {
            console.log(`Found ${entity.type}: ${entity.text} at ${entity.timestamp}`);
        });
        
    } catch (error) {
        console.error('Error:', error.message);
    }
}

processVideo('https://example.com/video.mp4');
            """, language="javascript")
        
        # Copy button
        if st.button("📋 Copy Code"):
            st.success("Code copied to clipboard!")
        
        # Additional resources
        st.markdown("""
        ### Additional Resources
        
        - 📚 [Full API Documentation](https://docs.vidner.com)
        - 🐛 [Report Issues](https://github.com/vidner/sdk/issues)
        - 💬 [Community Forum](https://community.vidner.com)
        - 📧 [Contact Support](mailto:support@vidner.com)
        """)
    
    def render_versioning(self):
        """Render API versioning interface"""
        st.header("🛠️ API Versioning")
        
        tabs = st.tabs(["Current Versions", "Migration Guide", "Deprecation Timeline"])
        
        with tabs[0]:
            st.subheader("API Versions")
            
            versions_data = {
                'Version': ['v1', 'v2-beta', 'v2', 'v3-preview'],
                'Status': ['Stable', 'Beta', 'Stable', 'Preview'],
                'Released': ['2023-01-15', '2023-08-01', '2023-10-01', '2024-02-01'],
                'Sunset Date': ['2024-12-31', 'N/A', 'N/A', 'N/A']
            }
            
            df = pd.DataFrame(versions_data)
            
            for idx, row in df.iterrows():
                with st.expander(f"Version {row['Version']} - {row['Status']}"):
                    st.write(f"**Released:** {row['Released']}")
                    st.write(f"**Sunset Date:** {row['Sunset Date']}")
                    
                    st.write("**Key Features:**")
                    if row['Version'] == 'v1':
                        st.write("- Basic transcription and NER")
                        st.write("- RESTful API")
                        st.write("- Webhook support")
                    elif row['Version'] == 'v2':
                        st.write("- Advanced entity recognition")
                        st.write("- Batch processing")
                        st.write("- GraphQL support")
                        st.write("- Real-time streaming")
        
        with tabs[1]:
            st.subheader("Migration Guide: v1 → v2")
            
            st.markdown("""
            ### Breaking Changes
            
            1. **Authentication Header**
               - v1: `X-API-Key: your_key`
               - v2: `Authorization: Bearer your_key`
            
            2. **Response Format**
               ```python
               # v1 Response
               {
                   "data": {...},
                   "error": null
               }
               
               # v2 Response
               {
                   "result": {...},
                   "metadata": {
                       "request_id": "...",
                       "timestamp": "..."
                   }
               }
               ```
            
            3. **Endpoint Changes**
               - `/api/transcribe` → `/v2/transcriptions`
               - `/api/analyze` → `/v2/analysis`
               - `/api/entities` → `/v2/entities`
            
            ### Migration Steps
            
            1. Update your SDK to the latest version
            2. Update authentication headers
            3. Update endpoint URLs
            4. Adjust response parsing logic
            5. Test thoroughly in staging
            """)
        
        with tabs[2]:
            st.subheader("Deprecation Timeline")
            
            # Timeline visualization
            timeline_data = [
                {"Version": "v1", "Event": "Initial Release", "Date": "2023-01-15"},
                {"Version": "v1", "Event": "Deprecation Notice", "Date": "2024-06-01"},
                {"Version": "v1", "Event": "End of Life", "Date": "2024-12-31"},
                {"Version": "v2", "Event": "Beta Release", "Date": "2023-08-01"},
                {"Version": "v2", "Event": "Stable Release", "Date": "2023-10-01"},
                {"Version": "v3", "Event": "Preview Release", "Date": "2024-02-01"}
            ]
            
            df = pd.DataFrame(timeline_data)
            st.dataframe(df, use_container_width=True)
            
            st.warning("""
            ⚠️ **Important**: Version v1 will be deprecated on June 1, 2024, and reach end of life on December 31, 2024.
            Please plan your migration to v2 accordingly.
            """)
    
    def render_community(self):
        """Render developer community section"""
        st.header("👥 Developer Community")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Community Members", "1,234", "+89")
        
        with col2:
            st.metric("Forum Posts", "5,678", "+234")
        
        with col3:
            st.metric("Open Source Projects", "45", "+5")
        
        tabs = st.tabs(["Forum", "Showcase", "Contributions", "Events"])
        
        with tabs[0]:
            st.subheader("Recent Discussions")
            
            discussions = [
                {
                    "title": "Best practices for batch processing large video libraries",
                    "author": "developer123",
                    "replies": 23,
                    "views": 456,
                    "last_activity": "2 hours ago"
                },
                {
                    "title": "Implementing real-time transcription with WebSockets",
                    "author": "streamingpro",
                    "replies": 15,
                    "views": 234,
                    "last_activity": "5 hours ago"
                },
                {
                    "title": "Custom entity recognition for medical terminology",
                    "author": "healthtech",
                    "replies": 8,
                    "views": 123,
                    "last_activity": "1 day ago"
                }
            ]
            
            for discussion in discussions:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"**{discussion['title']}**")
                        st.caption(f"by {discussion['author']} • {discussion['last_activity']}")
                    
                    with col2:
                        st.metric("Replies", discussion['replies'])
                    
                    with col3:
                        st.metric("Views", discussion['views'])
                    
                    st.divider()
        
        with tabs[1]:
            st.subheader("Community Showcase")
            
            projects = [
                {
                    "name": "Video Content Analyzer",
                    "description": "Automated content moderation using VidNER API",
                    "author": "techstartup",
                    "stars": 234,
                    "language": "Python"
                },
                {
                    "name": "Subtitle Generator Pro",
                    "description": "Generate multi-language subtitles with entity highlighting",
                    "author": "mediapro",
                    "stars": 189,
                    "language": "JavaScript"
                }
            ]
            
            for project in projects:
                with st.expander(f"🚀 {project['name']}"):
                    st.write(f"**Description:** {project['description']}")
                    st.write(f"**Author:** @{project['author']}")
                    st.write(f"**Language:** {project['language']}")
                    st.write(f"⭐ {project['stars']} stars")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.button("View on GitHub", key=f"gh_{project['name']}")
                    with col2:
                        st.button("Try Demo", key=f"demo_{project['name']}")
        
        with tabs[2]:
            st.subheader("Contribute to VidNER")
            
            st.markdown("""
            ### How to Contribute
            
            1. **SDK Development**
               - Help maintain and improve our official SDKs
               - Create SDKs for new languages
               
            2. **Documentation**
               - Improve our docs with examples and tutorials
               - Translate documentation to other languages
               
            3. **Community Support**
               - Answer questions in the forum
               - Share your projects and use cases
               
            4. **Feature Requests**
               - Suggest new features and improvements
               - Vote on the roadmap
            """)
            
            st.info("🎁 Top contributors receive free API credits and exclusive swag!")
        
        with tabs[3]:
            st.subheader("Upcoming Events")
            
            events = [
                {
                    "name": "VidNER Developer Workshop",
                    "date": "March 15, 2024",
                    "type": "Virtual",
                    "description": "Learn advanced techniques for video analysis"
                },
                {
                    "name": "API Design Best Practices",
                    "date": "March 22, 2024",
                    "type": "Webinar",
                    "description": "Design patterns for scalable API integration"
                }
            ]
            
            for event in events:
                with st.container():
                    st.write(f"### 📅 {event['name']}")
                    st.write(f"**Date:** {event['date']} • **Type:** {event['type']}")
                    st.write(event['description'])
                    st.button("Register", key=f"reg_{event['name']}")
                    st.divider()
    
    def run(self):
        """Run the developer platform UI"""
        st.set_page_config(
            page_title="VidNER Developer Platform",
            page_icon="🚀",
            layout="wide"
        )
        
        # Custom CSS
        st.markdown("""
        <style>
        .stMetric {
            background-color: #f0f2f6;
            padding: 15px;
            border-radius: 10px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Render sidebar and get selected page
        page = self.render_sidebar()
        
        # Render selected page
        if page == "dashboard":
            self.render_dashboard()
        elif page == "api_keys":
            self.render_api_keys()
        elif page == "documentation":
            self.render_documentation()
        elif page == "explorer":
            self.render_api_explorer()
        elif page == "webhooks":
            self.render_webhooks()
        elif page == "sdk":
            self.render_sdk_generator()
        elif page == "analytics":
            self.render_analytics()
        elif page == "examples":
            self.render_code_examples()
        elif page == "versioning":
            self.render_versioning()
        elif page == "community":
            self.render_community()

if __name__ == "__main__":
    ui = DeveloperPlatformUI()
    ui.run()