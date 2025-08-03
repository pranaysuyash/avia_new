#!/usr/bin/env python3
"""
Streamlit Developer Portal
Interface for developers to manage API keys, view documentation, and monitor usage
"""

import streamlit as st
from typing import Dict, Any, Optional, List
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import pyperclip

from ui_styles_refactored import apply_theme
from enhanced_components_refactored import (
    enhanced_button,
    enhanced_card,
    enhanced_progress_indicator,
    enhanced_metric,
    enhanced_tabs,
    enhanced_code_block
)

class DeveloperPortal:
    """Developer portal for API management"""
    
    def __init__(self):
        self.api_base_url = st.session_state.get('api_base_url', 'http://localhost:8000/api')
        self.headers = self._get_auth_headers()
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        if 'access_token' in st.session_state:
            return {'Authorization': f"Bearer {st.session_state.access_token}"}
        return {}
    
    def _api_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Any:
        """Make API request with error handling"""
        url = f"{self.api_base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=data)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=self.headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=self.headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {str(e)}")
            return None
    
    def render_main(self):
        """Render main developer portal"""
        st.title("🚀 Developer Portal")
        
        # Apply theme
        apply_theme(st.session_state.get('theme', 'light'))
        
        # Check authentication
        if 'user' not in st.session_state:
            st.warning("Please log in to access the developer portal")
            return
        
        # Tab selection
        tabs = ["Overview", "API Keys", "Documentation", "SDKs", "Webhooks", "Usage Analytics", "Code Examples"]
        selected_tab = enhanced_tabs(tabs, key="developer_tabs")
        
        if selected_tab == "Overview":
            self._render_overview()
        elif selected_tab == "API Keys":
            self._render_api_keys()
        elif selected_tab == "Documentation":
            self._render_documentation()
        elif selected_tab == "SDKs":
            self._render_sdks()
        elif selected_tab == "Webhooks":
            self._render_webhooks()
        elif selected_tab == "Usage Analytics":
            self._render_usage_analytics()
        elif selected_tab == "Code Examples":
            self._render_code_examples()
    
    def _render_overview(self):
        """Render developer overview"""
        st.header("Developer Overview")
        
        # Quick stats
        api_keys = self._api_request('GET', '/v1/developers/keys')
        webhooks = self._api_request('GET', '/v1/developers/webhooks')
        usage = self._api_request('GET', '/v1/analytics/usage')
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            enhanced_metric(
                "API Keys",
                str(len(api_keys) if api_keys else 0),
                "Active"
            )
        
        with col2:
            enhanced_metric(
                "Webhooks",
                str(len(webhooks) if webhooks else 0),
                "Configured"
            )
        
        with col3:
            if usage and 'usage' in usage:
                api_calls = usage['usage'].get('api_calls', {}).get('current', 0)
                enhanced_metric(
                    "API Calls",
                    f"{api_calls:,}",
                    "This month"
                )
        
        with col4:
            enhanced_metric(
                "Rate Limit",
                "1000/hour",
                "Default"
            )
        
        # Getting started
        st.subheader("🏁 Getting Started")
        
        with enhanced_card():
            st.write("### Quick Start Guide")
            st.write("1. **Create an API Key** - Generate your first API key in the API Keys tab")
            st.write("2. **Install SDK** - Choose Python or JavaScript SDK from the SDKs tab")
            st.write("3. **Make Your First Call** - Use the code examples to start transcribing")
            st.write("4. **Set Up Webhooks** - Configure webhooks to receive real-time updates")
        
        # API endpoints
        st.subheader("📡 Available Endpoints")
        
        endpoints = [
            ("POST /v1/transcripts", "Create a new transcript"),
            ("GET /v1/transcripts/{id}", "Get transcript details"),
            ("GET /v1/transcripts", "List transcripts"),
            ("DELETE /v1/transcripts/{id}", "Delete a transcript"),
            ("GET /v1/analytics/usage", "Get usage statistics"),
            ("POST /v1/teams", "Create a team"),
            ("POST /v1/developers/webhooks", "Create webhook")
        ]
        
        for endpoint, description in endpoints:
            col1, col2 = st.columns([2, 3])
            with col1:
                st.code(endpoint)
            with col2:
                st.write(description)
    
    def _render_api_keys(self):
        """Render API keys management"""
        st.header("API Key Management")
        
        # Create new API key
        with st.expander("➕ Create New API Key", expanded=False):
            with st.form("create_api_key"):
                col1, col2 = st.columns(2)
                
                with col1:
                    name = st.text_input("Key Name", placeholder="Production API Key")
                    description = st.text_area("Description", placeholder="Used for production environment")
                    
                    # Rate limits
                    st.write("### Rate Limits")
                    rate_per_minute = st.number_input("Requests per minute", value=60, min_value=1, max_value=600)
                    rate_per_hour = st.number_input("Requests per hour", value=1000, min_value=1, max_value=10000)
                
                with col2:
                    # Scopes
                    st.write("### Permissions (Scopes)")
                    scopes = []
                    if st.checkbox("Transcripts - Read", value=True):
                        scopes.append("transcripts:read")
                    if st.checkbox("Transcripts - Write", value=True):
                        scopes.append("transcripts:write")
                    if st.checkbox("Transcripts - Delete"):
                        scopes.append("transcripts:delete")
                    if st.checkbox("Analytics - Read", value=True):
                        scopes.append("analytics:read")
                    if st.checkbox("Teams - Read"):
                        scopes.append("teams:read")
                    if st.checkbox("Teams - Write"):
                        scopes.append("teams:write")
                    if st.checkbox("Webhooks - Write"):
                        scopes.append("webhooks:write")
                    
                    # Advanced options
                    st.write("### Advanced Options")
                    expires_in_days = st.number_input("Expires in days (0 = never)", value=0, min_value=0, max_value=365)
                    
                    # IP restrictions
                    ip_restriction = st.text_area("Allowed IPs (one per line)", placeholder="192.168.1.1\n10.0.0.0/24")
                
                if st.form_submit_button("Create API Key", type="primary"):
                    if name and scopes:
                        # Prepare data
                        data = {
                            "name": name,
                            "description": description,
                            "scopes": scopes,
                            "rate_limits": {
                                "per_minute": rate_per_minute,
                                "per_hour": rate_per_hour,
                                "per_day": rate_per_hour * 24
                            }
                        }
                        
                        if expires_in_days > 0:
                            data["expires_in_days"] = expires_in_days
                        
                        if ip_restriction:
                            data["allowed_ips"] = [ip.strip() for ip in ip_restriction.split('\n') if ip.strip()]
                        
                        # Create API key
                        result = self._api_request('POST', '/v1/developers/keys', data)
                        
                        if result:
                            st.success(f"API Key created successfully!")
                            st.warning("⚠️ Save this key now - it won't be shown again!")
                            
                            # Display the key with copy button
                            with enhanced_card():
                                st.code(result['key'])
                                if st.button("📋 Copy to Clipboard", key="copy_new_key"):
                                    pyperclip.copy(result['key'])
                                    st.success("Copied to clipboard!")
                    else:
                        st.error("Please provide a name and select at least one scope")
        
        # List existing API keys
        st.subheader("Your API Keys")
        
        api_keys = self._api_request('GET', '/v1/developers/keys')
        
        if api_keys:
            for key in api_keys:
                with enhanced_card():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.write(f"### {key['name']}")
                        st.write(f"**Key:** `{key['key_prefix']}...`")
                        if key.get('description'):
                            st.write(key['description'])
                        st.write(f"**Created:** {key['created_at']}")
                        if key.get('last_used_at'):
                            st.write(f"**Last used:** {key['last_used_at']}")
                    
                    with col2:
                        st.write("**Status:**", key['status'])
                        st.write("**Usage:**", f"{key['usage_count']} requests")
                        if key.get('expires_at'):
                            st.write("**Expires:**", key['expires_at'])
                        
                        # Display scopes
                        st.write("**Scopes:**")
                        for scope in key['scopes']:
                            st.caption(f"• {scope}")
                    
                    with col3:
                        # Actions
                        if key['status'] == 'active':
                            if st.button("🔄 Regenerate", key=f"regen_{key['id']}"):
                                if st.checkbox(f"Confirm regenerate {key['name']}", key=f"confirm_regen_{key['id']}"):
                                    result = self._api_request('POST', f"/v1/developers/keys/{key['id']}/regenerate")
                                    if result:
                                        st.success("Key regenerated!")
                                        st.rerun()
                            
                            if st.button("❌ Revoke", key=f"revoke_{key['id']}"):
                                if st.checkbox(f"Confirm revoke {key['name']}", key=f"confirm_revoke_{key['id']}"):
                                    result = self._api_request('DELETE', f"/v1/developers/keys/{key['id']}")
                                    if result:
                                        st.success("Key revoked!")
                                        st.rerun()
                        
                        if st.button("📊 View Stats", key=f"stats_{key['id']}"):
                            st.session_state.selected_key_id = key['id']
        else:
            st.info("No API keys yet. Create your first key above!")
        
        # Show detailed stats if selected
        if 'selected_key_id' in st.session_state:
            key_details = self._api_request('GET', f"/v1/developers/keys/{st.session_state.selected_key_id}")
            if key_details:
                st.subheader(f"Statistics for {key_details['name']}")
                
                # Usage stats
                if 'usage_stats' in key_details:
                    stats = key_details['usage_stats']
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Requests", f"{stats['total_requests']:,}")
                    with col2:
                        st.metric("Avg Response Time", f"{stats['average_response_time_ms']:.0f}ms")
                    with col3:
                        success_rate = sum(s['count'] for s in stats['status_distribution'] if s['status'] < 400)
                        total = sum(s['count'] for s in stats['status_distribution'])
                        st.metric("Success Rate", f"{(success_rate/total*100):.1f}%" if total > 0 else "N/A")
                    
                    # Top endpoints
                    if stats['top_endpoints']:
                        st.write("### Top Endpoints")
                        df = pd.DataFrame(stats['top_endpoints'])
                        fig = px.bar(df, x='count', y='endpoint', orientation='h', title='API Usage by Endpoint')
                        st.plotly_chart(fig, use_container_width=True)
    
    def _render_documentation(self):
        """Render API documentation"""
        st.header("API Documentation")
        
        # API version and base URL
        col1, col2 = st.columns(2)
        with col1:
            st.info("**API Version:** v1")
        with col2:
            st.info("**Base URL:** https://api.example.com/v1")
        
        # Authentication
        st.subheader("🔐 Authentication")
        
        with enhanced_card():
            st.write("All API requests must include your API key in the Authorization header:")
            enhanced_code_block(
                "Authorization: Bearer YOUR_API_KEY",
                language="http"
            )
            
            st.write("Alternatively, you can use the X-API-Key header:")
            enhanced_code_block(
                "X-API-Key: YOUR_API_KEY",
                language="http"
            )
        
        # Quick reference
        st.subheader("📚 Quick Reference")
        
        # Transcripts endpoints
        with st.expander("Transcripts", expanded=True):
            # Create transcript
            st.write("### Create Transcript")
            col1, col2 = st.columns([1, 2])
            with col1:
                st.code("POST /v1/transcripts")
            with col2:
                st.write("Create a new transcript from audio/video URL")
            
            enhanced_code_block("""
{
  "audio_url": "https://example.com/audio.mp3",
  "language": "en",
  "enable_diarization": true,
  "max_speakers": 3,
  "webhook_url": "https://your-app.com/webhook",
  "metadata": {
    "project": "interview",
    "episode": 42
  }
}
""", language="json")
            
            # Get transcript
            st.write("### Get Transcript")
            col1, col2 = st.columns([1, 2])
            with col1:
                st.code("GET /v1/transcripts/{id}")
            with col2:
                st.write("Retrieve transcript details and status")
            
            # List transcripts
            st.write("### List Transcripts")
            col1, col2 = st.columns([1, 2])
            with col1:
                st.code("GET /v1/transcripts")
            with col2:
                st.write("List all transcripts with pagination")
            
            st.write("Query parameters:")
            params = [
                ("page", "integer", "Page number (default: 1)"),
                ("per_page", "integer", "Items per page (max: 100)"),
                ("status", "string", "Filter by status"),
                ("language", "string", "Filter by language"),
                ("team_id", "integer", "Filter by team")
            ]
            
            df = pd.DataFrame(params, columns=["Parameter", "Type", "Description"])
            st.dataframe(df, hide_index=True)
        
        # Response formats
        st.subheader("📄 Response Formats")
        
        with enhanced_card():
            st.write("### Success Response")
            enhanced_code_block("""
{
  "id": "tr_abc123def456",
  "status": "completed",
  "created_at": "2024-01-20T12:00:00Z",
  "completed_at": "2024-01-20T12:05:30Z",
  "language": "en",
  "duration": 300.5,
  "text": "This is the transcribed text...",
  "speakers": [
    {"id": "SPEAKER_00", "name": "Speaker 1"},
    {"id": "SPEAKER_01", "name": "Speaker 2"}
  ],
  "segments": [
    {
      "start": 0.0,
      "end": 5.2,
      "speaker": "SPEAKER_00",
      "text": "Hello, this is the beginning.",
      "confidence": 0.95
    }
  ]
}
""", language="json")
            
            st.write("### Error Response")
            enhanced_code_block("""
{
  "error": "validation_error",
  "message": "Invalid audio URL",
  "details": {
    "field": "audio_url",
    "reason": "URL must be accessible"
  }
}
""", language="json")
        
        # Rate limiting
        st.subheader("⏱️ Rate Limiting")
        
        with enhanced_card():
            st.write("Rate limits are enforced per API key:")
            
            limits = [
                ("Free", "60/min", "1,000/hour", "10,000/day"),
                ("Basic", "120/min", "5,000/hour", "50,000/day"),
                ("Pro", "300/min", "20,000/hour", "200,000/day"),
                ("Enterprise", "Custom", "Custom", "Custom")
            ]
            
            df = pd.DataFrame(limits, columns=["Plan", "Per Minute", "Per Hour", "Per Day"])
            st.dataframe(df, hide_index=True)
            
            st.write("Rate limit headers are included in all responses:")
            enhanced_code_block("""
X-RateLimit-Limit-Minute: 60
X-RateLimit-Remaining-Minute: 45
X-RateLimit-Reset: 1234567890
""", language="http")
    
    def _render_sdks(self):
        """Render SDK information"""
        st.header("SDKs & Libraries")
        
        col1, col2 = st.columns(2)
        
        with col1:
            with enhanced_card():
                st.write("### 🐍 Python SDK")
                st.write("Official Python SDK for the Transcription Platform API")
                
                st.write("**Installation:**")
                enhanced_code_block("pip install transcription-platform", language="bash")
                
                st.write("**Quick Example:**")
                enhanced_code_block("""
from transcription_platform import TranscriptionClient

client = TranscriptionClient(api_key="YOUR_API_KEY")

# Create transcript
transcript = client.create_transcript(
    audio_url="https://example.com/audio.mp3",
    language="en",
    enable_diarization=True
)

# Wait for completion
transcript = client.wait_for_completion(transcript.id)
print(transcript.text)
""", language="python")
                
                if enhanced_button("View Python Docs", "primary", key="python_docs"):
                    st.info("📖 Full documentation at: https://docs.example.com/sdk/python")
        
        with col2:
            with enhanced_card():
                st.write("### 📜 JavaScript/TypeScript SDK")
                st.write("Official JavaScript SDK with full TypeScript support")
                
                st.write("**Installation:**")
                enhanced_code_block("npm install @transcription/sdk", language="bash")
                
                st.write("**Quick Example:**")
                enhanced_code_block("""
import { TranscriptionClient } from '@transcription/sdk';

const client = new TranscriptionClient('YOUR_API_KEY');

// Create transcript
const transcript = await client.createTranscript({
  audioUrl: 'https://example.com/audio.mp3',
  language: 'en',
  enableDiarization: true
});

// Wait for completion
const completed = await client.waitForCompletion(transcript.id);
console.log(completed.text);
""", language="typescript")
                
                if enhanced_button("View JS Docs", "primary", key="js_docs"):
                    st.info("📖 Full documentation at: https://docs.example.com/sdk/javascript")
        
        # Other languages
        st.subheader("🌐 Community SDKs")
        
        community_sdks = [
            ("Ruby", "transcription-platform-ruby", "gem install transcription-platform"),
            ("Go", "go-transcription", "go get github.com/transcription/go-sdk"),
            ("PHP", "transcription-php", "composer require transcription/sdk"),
            ("Java", "transcription-java", "Maven: com.transcription:sdk:1.0.0"),
            ("C#/.NET", "Transcription.NET", "dotnet add package Transcription.SDK")
        ]
        
        for lang, name, install in community_sdks:
            with st.expander(f"{lang} - {name}"):
                st.code(install)
                st.write("Community maintained SDK. See GitHub for documentation.")
    
    def _render_webhooks(self):
        """Render webhook management"""
        st.header("Webhook Management")
        
        # Create webhook
        with st.expander("➕ Create New Webhook", expanded=False):
            with st.form("create_webhook"):
                col1, col2 = st.columns(2)
                
                with col1:
                    name = st.text_input("Webhook Name", placeholder="Production Webhook")
                    url = st.text_input("Webhook URL", placeholder="https://your-app.com/webhook")
                    
                    # Retry settings
                    st.write("### Retry Configuration")
                    max_retries = st.slider("Max Retries", 0, 10, 3)
                    timeout = st.slider("Timeout (seconds)", 5, 120, 30)
                
                with col2:
                    st.write("### Events to Subscribe")
                    events = []
                    
                    st.write("**Transcript Events**")
                    if st.checkbox("transcript.created"):
                        events.append("transcript.created")
                    if st.checkbox("transcript.completed", value=True):
                        events.append("transcript.completed")
                    if st.checkbox("transcript.failed", value=True):
                        events.append("transcript.failed")
                    if st.checkbox("transcript.deleted"):
                        events.append("transcript.deleted")
                    
                    st.write("**Team Events**")
                    if st.checkbox("team.member.added"):
                        events.append("team.member.added")
                    if st.checkbox("team.member.removed"):
                        events.append("team.member.removed")
                    
                    st.write("**Usage Events**")
                    if st.checkbox("usage.limit.warning"):
                        events.append("usage.limit.warning")
                    if st.checkbox("usage.limit.exceeded"):
                        events.append("usage.limit.exceeded")
                
                if st.form_submit_button("Create Webhook", type="primary"):
                    if name and url and events:
                        data = {
                            "name": name,
                            "url": url,
                            "events": events,
                            "max_retries": max_retries,
                            "timeout_seconds": timeout
                        }
                        
                        result = self._api_request('POST', '/v1/developers/webhooks', data)
                        
                        if result:
                            st.success("Webhook created successfully!")
                            st.warning("⚠️ Save this secret for signature verification:")
                            st.code(result['secret'])
                    else:
                        st.error("Please fill all required fields")
        
        # List webhooks
        st.subheader("Your Webhooks")
        
        webhooks = self._api_request('GET', '/v1/developers/webhooks')
        
        if webhooks:
            for webhook in webhooks:
                with enhanced_card():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.write(f"### {webhook['name']}")
                        st.write(f"**URL:** `{webhook['url']}`")
                        st.write(f"**Status:** {webhook['status']}")
                        st.write(f"**Events:** {', '.join(webhook['events'])}")
                    
                    with col2:
                        st.write(f"**Success:** {webhook['success_count']}")
                        st.write(f"**Failures:** {webhook['failure_count']}")
                        if webhook.get('last_triggered_at'):
                            st.write(f"**Last triggered:** {webhook['last_triggered_at']}")
                    
                    with col3:
                        if st.button("🧪 Test", key=f"test_{webhook['id']}"):
                            result = self._api_request('POST', f"/v1/developers/webhooks/{webhook['id']}/test")
                            if result:
                                st.success("Test event sent!")
                        
                        if st.button("📊 Logs", key=f"logs_{webhook['id']}"):
                            st.session_state.selected_webhook_id = webhook['id']
                        
                        if st.button("🗑️ Delete", key=f"delete_{webhook['id']}"):
                            if st.checkbox(f"Confirm delete {webhook['name']}", key=f"confirm_del_{webhook['id']}"):
                                result = self._api_request('DELETE', f"/v1/developers/webhooks/{webhook['id']}")
                                if result:
                                    st.success("Webhook deleted!")
                                    st.rerun()
        else:
            st.info("No webhooks configured yet. Create your first webhook above!")
        
        # Show webhook logs if selected
        if 'selected_webhook_id' in st.session_state:
            webhook_details = self._api_request('GET', f"/v1/developers/webhooks/{st.session_state.selected_webhook_id}")
            
            if webhook_details and 'recent_deliveries' in webhook_details:
                st.subheader(f"Recent Deliveries for {webhook_details['name']}")
                
                deliveries = webhook_details['recent_deliveries']
                if deliveries:
                    df = pd.DataFrame(deliveries)
                    st.dataframe(df, hide_index=True)
                else:
                    st.info("No recent deliveries")
    
    def _render_usage_analytics(self):
        """Render API usage analytics"""
        st.header("API Usage Analytics")
        
        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            days_range = st.selectbox("Time Range", [7, 30, 60, 90], index=1)
        
        # Get usage data
        usage = self._api_request('GET', '/v1/analytics/usage', {'days': days_range})
        
        if usage:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            api_usage = usage.get('usage', {}).get('api_calls', {})
            transcript_usage = usage.get('usage', {}).get('transcripts', {})
            
            with col1:
                enhanced_metric(
                    "API Calls",
                    f"{api_usage.get('current', 0):,}",
                    f"of {api_usage.get('limit', 0):,}"
                )
            
            with col2:
                enhanced_metric(
                    "Transcripts",
                    f"{transcript_usage.get('current', 0):,}",
                    f"of {transcript_usage.get('limit', 0):,}"
                )
            
            with col3:
                success_rate = 98.5  # Mock data
                enhanced_metric(
                    "Success Rate",
                    f"{success_rate}%",
                    "API calls"
                )
            
            with col4:
                avg_response = 145  # Mock data
                enhanced_metric(
                    "Avg Response Time",
                    f"{avg_response}ms",
                    "Last 24h"
                )
            
            # Usage trends chart
            st.subheader("Usage Trends")
            
            # Mock trend data
            dates = pd.date_range(end=datetime.now(), periods=days_range, freq='D')
            trend_data = {
                'Date': dates,
                'API Calls': [100 + i * 10 + (i % 7) * 20 for i in range(days_range)],
                'Transcripts': [10 + i * 2 + (i % 7) * 3 for i in range(days_range)]
            }
            
            df_trends = pd.DataFrame(trend_data)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_trends['Date'],
                y=df_trends['API Calls'],
                name='API Calls',
                line=dict(color='blue', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=df_trends['Date'],
                y=df_trends['Transcripts'],
                name='Transcripts',
                yaxis='y2',
                line=dict(color='green', width=2)
            ))
            
            fig.update_layout(
                title='API Usage Over Time',
                xaxis_title='Date',
                yaxis=dict(title='API Calls', side='left'),
                yaxis2=dict(title='Transcripts', overlaying='y', side='right'),
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Endpoint breakdown
            st.subheader("Endpoint Usage")
            
            # Mock endpoint data
            endpoints = [
                '/v1/transcripts',
                '/v1/transcripts/{id}',
                '/v1/analytics/usage',
                '/v1/teams',
                '/v1/transcripts/export'
            ]
            
            calls = [450, 320, 180, 120, 80]
            
            fig_endpoints = px.bar(
                x=calls,
                y=endpoints,
                orientation='h',
                title='API Calls by Endpoint',
                labels={'x': 'Number of Calls', 'y': 'Endpoint'}
            )
            
            st.plotly_chart(fig_endpoints, use_container_width=True)
    
    def _render_code_examples(self):
        """Render code examples"""
        st.header("Code Examples")
        
        # Language selector
        language = st.selectbox("Select Language", ["Python", "JavaScript", "cURL", "Ruby", "Go"])
        
        # Example selector
        example = st.selectbox(
            "Select Example",
            [
                "Basic Transcription",
                "Transcription with Diarization",
                "Batch Processing",
                "Webhook Handling",
                "Export Formats",
                "Team Collaboration"
            ]
        )
        
        # Display example based on selection
        if language == "Python":
            if example == "Basic Transcription":
                enhanced_code_block("""
from transcription_platform import TranscriptionClient

# Initialize client
client = TranscriptionClient(api_key="YOUR_API_KEY")

# Create transcript from URL
transcript = client.create_transcript(
    audio_url="https://example.com/audio.mp3",
    language="en"
)

# Poll for completion
import time
while transcript.status in ['pending', 'processing']:
    time.sleep(5)
    transcript = client.get_transcript(transcript.id)
    print(f"Status: {transcript.status}")

# Get results
if transcript.is_complete:
    print(f"Transcription complete!")
    print(f"Text: {transcript.text}")
    print(f"Duration: {transcript.duration} seconds")
    print(f"Word count: {transcript.word_count}")
""", language="python")
                
            elif example == "Transcription with Diarization":
                enhanced_code_block("""
from transcription_platform import TranscriptionClient

client = TranscriptionClient(api_key="YOUR_API_KEY")

# Create transcript with speaker diarization
transcript = client.create_transcript(
    audio_url="https://example.com/interview.mp3",
    language="en",
    enable_diarization=True,
    max_speakers=3
)

# Wait for completion
transcript = client.wait_for_completion(transcript.id)

# Process speaker segments
for segment in transcript.segments:
    print(f"[{segment.speaker}] ({segment.start:.1f}s - {segment.end:.1f}s)")
    print(f"  {segment.text}")
    print()

# Get speaker statistics
speakers = {}
for segment in transcript.segments:
    speaker = segment.speaker
    if speaker not in speakers:
        speakers[speaker] = {"count": 0, "duration": 0}
    speakers[speaker]["count"] += 1
    speakers[speaker]["duration"] += segment.end - segment.start

print("Speaker Statistics:")
for speaker, stats in speakers.items():
    print(f"  {speaker}: {stats['count']} segments, {stats['duration']:.1f}s total")
""", language="python")
        
        elif language == "JavaScript":
            if example == "Basic Transcription":
                enhanced_code_block("""
import { TranscriptionClient } from '@transcription/sdk';

// Initialize client
const client = new TranscriptionClient('YOUR_API_KEY');

async function transcribeAudio() {
  // Create transcript
  const transcript = await client.createTranscript({
    audioUrl: 'https://example.com/audio.mp3',
    language: 'en'
  });
  
  console.log(`Transcript created: ${transcript.id}`);
  
  // Wait for completion with progress updates
  const completed = await client.waitForCompletion(transcript.id, {
    pollInterval: 5000,
    onProgress: (t) => {
      console.log(`Status: ${t.status}`);
    }
  });
  
  // Display results
  console.log('Transcription complete!');
  console.log(`Text: ${completed.text}`);
  console.log(`Duration: ${completed.duration} seconds`);
}

transcribeAudio().catch(console.error);
""", language="javascript")
        
        elif language == "cURL":
            if example == "Basic Transcription":
                enhanced_code_block("""
# Create transcript
curl -X POST https://api.example.com/v1/transcripts \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "https://example.com/audio.mp3",
    "language": "en"
  }'

# Response:
# {
#   "id": "tr_abc123",
#   "status": "processing",
#   "created_at": "2024-01-20T12:00:00Z"
# }

# Check status
curl https://api.example.com/v1/transcripts/tr_abc123 \
  -H "Authorization: Bearer YOUR_API_KEY"

# Export as text
curl https://api.example.com/v1/transcripts/tr_abc123/export?format=txt \
  -H "Authorization: Bearer YOUR_API_KEY"
""", language="bash")
        
        # Additional resources
        st.subheader("📚 Additional Resources")
        
        resources = [
            ("API Reference", "https://docs.example.com/api"),
            ("SDK Documentation", "https://docs.example.com/sdk"),
            ("Postman Collection", "https://postman.com/transcription-api"),
            ("GitHub Examples", "https://github.com/transcription/examples"),
            ("Community Forum", "https://forum.example.com")
        ]
        
        for name, url in resources:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{name}**")
            with col2:
                st.write(f"[Visit →]({url})")

# Initialize and render
def main():
    """Main function to render developer portal"""
    portal = DeveloperPortal()
    portal.render_main()

if __name__ == "__main__":
    main()