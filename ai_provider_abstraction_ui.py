"""
AI Provider Abstraction Layer UI

Streamlit interface for managing AI providers, monitoring their status,
and testing provider functionality with real-time metrics.
"""

import streamlit as st
import asyncio
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from typing import Dict, List

from ai_provider_abstraction import (
    ProviderAbstraction, AIRequest, ProviderConfig, RequestType, 
    ProviderType, ProviderStatus
)

class ProviderAbstractionUI:
    """Streamlit UI for Provider Abstraction Layer"""
    
    def __init__(self):
        self.abstraction = None
        if 'provider_abstraction' not in st.session_state:
            st.session_state.provider_abstraction = ProviderAbstraction()
        self.abstraction = st.session_state.provider_abstraction
    
    def render(self):
        """Render the main UI"""
        st.title("🔗 AI Provider Abstraction Layer")
        st.markdown("Unified interface for managing and monitoring AI providers")
        
        # Sidebar for navigation
        page = st.sidebar.selectbox(
            "Navigation",
            ["Provider Overview", "Request Testing", "Provider Management", "Metrics & Analytics", "Request History"]
        )
        
        if page == "Provider Overview":
            self.render_provider_overview()
        elif page == "Request Testing":
            self.render_request_testing()
        elif page == "Provider Management":
            self.render_provider_management()
        elif page == "Metrics & Analytics":
            self.render_metrics_analytics()
        elif page == "Request History":
            self.render_request_history()
    
    def render_provider_overview(self):
        """Render provider overview dashboard"""
        st.header("📊 Provider Overview")
        
        # Get provider metrics
        metrics = self.abstraction.get_provider_metrics()
        
        if not metrics:
            st.warning("No providers registered")
            return
        
        # Provider status cards
        st.subheader("Provider Status")
        
        cols = st.columns(min(len(metrics), 4))
        
        for i, (provider_name, provider_metrics) in enumerate(metrics.items()):
            with cols[i % 4]:
                status = provider_metrics['status']
                status_color = {
                    'available': '🟢',
                    'unavailable': '🔴',
                    'degraded': '🟡',
                    'maintenance': '🔵'
                }.get(status, '⚪')
                
                st.metric(
                    f"{status_color} {provider_name.title()}",
                    f"{provider_metrics['request_count']} requests",
                    delta=f"{provider_metrics['error_rate']:.1%} error rate"
                )
        
        # Detailed provider information
        st.subheader("Provider Details")
        
        for provider_name, provider_metrics in metrics.items():
            with st.expander(f"📋 {provider_name.title()} Details", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**Status Information:**")
                    st.write(f"Status: {provider_metrics['status'].title()}")
                    st.write(f"Total Requests: {provider_metrics['request_count']}")
                    st.write(f"Failed Requests: {provider_metrics['error_count']}")
                
                with col2:
                    st.write("**Performance Metrics:**")
                    st.write(f"Error Rate: {provider_metrics['error_rate']:.2%}")
                    st.write(f"Avg Response Time: {provider_metrics['average_processing_time']:.3f}s")
                    
                    # Performance indicator
                    if provider_metrics['error_rate'] < 0.05:
                        st.success("Excellent Performance")
                    elif provider_metrics['error_rate'] < 0.15:
                        st.warning("Good Performance")
                    else:
                        st.error("Poor Performance")
                
                with col3:
                    st.write("**Supported Capabilities:**")
                    for capability in provider_metrics['supported_types']:
                        st.write(f"• {capability.replace('_', ' ').title()}")
        
        # Provider comparison chart
        if len(metrics) > 1:
            st.subheader("📈 Provider Comparison")
            
            # Create comparison DataFrame
            comparison_data = []
            for provider_name, provider_metrics in metrics.items():
                comparison_data.append({
                    'Provider': provider_name.title(),
                    'Error Rate': provider_metrics['error_rate'],
                    'Avg Response Time': provider_metrics['average_processing_time'],
                    'Total Requests': provider_metrics['request_count']
                })
            
            df = pd.DataFrame(comparison_data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Error rate comparison
                fig_error = px.bar(
                    df,
                    x='Provider',
                    y='Error Rate',
                    title='Error Rate by Provider',
                    color='Error Rate',
                    color_continuous_scale='RdYlGn_r'
                )
                st.plotly_chart(fig_error, use_container_width=True)
            
            with col2:
                # Response time comparison
                fig_time = px.bar(
                    df,
                    x='Provider',
                    y='Avg Response Time',
                    title='Average Response Time by Provider',
                    color='Avg Response Time',
                    color_continuous_scale='RdYlBu_r'
                )
                st.plotly_chart(fig_time, use_container_width=True)
    
    def render_request_testing(self):
        """Render request testing interface"""
        st.header("🧪 Request Testing")
        st.markdown("Test AI providers with different request types")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Request Configuration")
            
            # Request type selection
            request_type = st.selectbox(
                "Request Type",
                options=[rt.value for rt in RequestType],
                help="Select the type of AI request to test"
            )
            
            # Content input based on request type
            if request_type == "transcription":
                content = st.text_input(
                    "Audio File Path",
                    value="sample_audio.wav",
                    help="Path to audio file for transcription"
                )
            elif request_type == "text_to_speech":
                content = st.text_area(
                    "Text to Convert",
                    value="Hello, this is a test message for text-to-speech conversion.",
                    help="Text to convert to speech"
                )
            elif request_type in ["entity_extraction", "sentiment_analysis"]:
                content = st.text_area(
                    "Text to Analyze",
                    value="John Doe works at OpenAI in San Francisco. He loves working on AI projects.",
                    help="Text for NLP analysis"
                )
            elif request_type == "text_generation":
                content = st.text_area(
                    "Prompt",
                    value="Write a short story about artificial intelligence.",
                    help="Prompt for text generation"
                )
            else:
                content = st.text_area(
                    "Content",
                    value="Sample content for processing",
                    help="Content to process"
                )
            
            # Provider selection
            metrics = self.abstraction.get_provider_metrics()
            available_providers = [name for name, m in metrics.items() 
                                 if request_type in m['supported_types']]
            
            provider_choice = st.selectbox(
                "Provider",
                options=["Auto-select"] + available_providers,
                help="Choose specific provider or let system auto-select"
            )
            
            # Additional parameters
            st.subheader("Parameters")
            
            parameters = {}
            if request_type == "text_to_speech":
                voice_id = st.selectbox(
                    "Voice ID",
                    options=["default", "voice_1", "voice_2"],
                    help="Voice to use for TTS"
                )
                parameters["voice_id"] = voice_id
            
            elif request_type == "text_generation":
                max_tokens = st.number_input(
                    "Max Tokens",
                    min_value=10,
                    max_value=1000,
                    value=100,
                    help="Maximum tokens to generate"
                )
                parameters["max_tokens"] = max_tokens
            
            elif request_type == "transcription":
                language = st.selectbox(
                    "Language",
                    options=["auto", "en", "es", "fr", "de"],
                    help="Audio language"
                )
                parameters["language"] = language
            
            # Execute request
            if st.button("🚀 Execute Request", type="primary"):
                with st.spinner("Processing request..."):
                    result = self.execute_test_request(
                        request_type, content, parameters, 
                        provider_choice if provider_choice != "Auto-select" else None
                    )
                    
                    if result:
                        st.session_state.last_test_result = result
        
        with col2:
            st.subheader("Available Providers")
            
            # Show providers that support selected request type
            for provider_name, provider_metrics in metrics.items():
                if request_type in provider_metrics['supported_types']:
                    status_icon = {
                        'available': '🟢',
                        'unavailable': '🔴',
                        'degraded': '🟡'
                    }.get(provider_metrics['status'], '⚪')
                    
                    with st.expander(f"{status_icon} {provider_name.title()}", expanded=False):
                        st.write(f"**Status:** {provider_metrics['status'].title()}")
                        st.write(f"**Requests:** {provider_metrics['request_count']}")
                        st.write(f"**Error Rate:** {provider_metrics['error_rate']:.2%}")
                        st.write(f"**Avg Time:** {provider_metrics['average_processing_time']:.3f}s")
        
        # Display test result
        if hasattr(st.session_state, 'last_test_result') and st.session_state.last_test_result:
            self.display_test_result(st.session_state.last_test_result)
    
    def execute_test_request(self, request_type: str, content: str, parameters: Dict, provider_name: str = None):
        """Execute test request"""
        try:
            # Create request
            request = AIRequest(
                id=f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                type=RequestType(request_type),
                content=content,
                parameters=parameters
            )
            
            # Execute request
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(
                self.abstraction.execute_request(request, provider_name)
            )
            loop.close()
            
            return {
                'request': request,
                'response': response,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            st.error(f"Error executing request: {str(e)}")
            return None
    
    def display_test_result(self, result):
        """Display test result"""
        st.subheader("🎯 Test Result")
        
        response = result['response']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status = "✅ Success" if response.success else "❌ Failed"
            st.metric("Status", status)
        
        with col2:
            st.metric(
                "Processing Time",
                f"{response.processing_time:.3f}s"
            )
        
        with col3:
            st.metric(
                "Provider",
                response.provider.title() if response.provider else "Unknown"
            )
        
        # Response details
        if response.success:
            st.subheader("Response Data")
            
            if isinstance(response.result, dict):
                # Display structured result
                for key, value in response.result.items():
                    if key == "text" or key == "summary":
                        st.text_area(f"{key.title()}:", value, height=100)
                    elif isinstance(value, (list, dict)):
                        st.json({key: value})
                    else:
                        st.write(f"**{key.title()}:** {value}")
            else:
                st.write("**Result:**")
                st.write(response.result)
            
            # Metadata
            if response.metadata:
                st.subheader("Metadata")
                st.json(response.metadata)
        
        else:
            st.error(f"Request failed: {response.error}")
        
        # Request details
        with st.expander("📋 Request Details", expanded=False):
            request = result['request']
            st.write(f"**Request ID:** {request.id}")
            st.write(f"**Type:** {request.type.value}")
            st.write(f"**Content:** {str(request.content)[:200]}...")
            if request.parameters:
                st.write("**Parameters:**")
                st.json(request.parameters)
    
    def render_provider_management(self):
        """Render provider management interface"""
        st.header("⚙️ Provider Management")
        
        tab1, tab2, tab3 = st.tabs(["Provider Configuration", "Add Provider", "Error Handling"])
        
        with tab1:
            st.subheader("Configure Existing Providers")
            
            metrics = self.abstraction.get_provider_metrics()
            
            if metrics:
                provider_to_config = st.selectbox(
                    "Select Provider to Configure",
                    options=list(metrics.keys())
                )
                
                if provider_to_config:
                    st.write(f"**Configuring: {provider_to_config.title()}**")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        max_retries = st.number_input(
                            "Max Retries",
                            min_value=0,
                            max_value=10,
                            value=3,
                            help="Maximum retry attempts"
                        )
                        
                        timeout = st.number_input(
                            "Timeout (seconds)",
                            min_value=1.0,
                            max_value=300.0,
                            value=30.0,
                            help="Request timeout"
                        )
                    
                    with col2:
                        api_key = st.text_input(
                            "API Key",
                            type="password",
                            help="Provider API key (if required)"
                        )
                        
                        model_name = st.text_input(
                            "Model Name",
                            help="Specific model to use"
                        )
                    
                    if st.button("💾 Update Configuration"):
                        # Update provider configuration
                        config = ProviderConfig(
                            provider_type=ProviderType.CUSTOM,  # Will be overridden
                            api_key=api_key if api_key else None,
                            model_name=model_name if model_name else None,
                            max_retries=max_retries,
                            timeout=timeout
                        )
                        
                        self.abstraction.configure_provider(provider_to_config, config)
                        st.success(f"Updated configuration for {provider_to_config}")
                        st.rerun()
            else:
                st.info("No providers available to configure")
        
        with tab2:
            st.subheader("Add Custom Provider")
            st.info("Custom provider registration would be implemented here")
            
            provider_name = st.text_input("Provider Name")
            provider_type = st.selectbox(
                "Provider Type",
                options=[pt.value for pt in ProviderType]
            )
            
            st.write("**Configuration:**")
            api_key = st.text_input("API Key", type="password")
            base_url = st.text_input("Base URL")
            model_name = st.text_input("Model Name")
            
            if st.button("➕ Add Provider"):
                st.info("Custom provider addition would be implemented here")
        
        with tab3:
            st.subheader("Error Handling Configuration")
            
            st.write("**Current Error Handlers:**")
            
            # Show registered error handlers
            if hasattr(self.abstraction, 'error_handlers'):
                if self.abstraction.error_handlers:
                    for error_type in self.abstraction.error_handlers.keys():
                        st.write(f"• {error_type}")
                else:
                    st.write("No custom error handlers registered")
            
            st.write("**Add Custom Error Handler:**")
            
            error_type = st.text_input("Error Type", placeholder="rate_limit_error")
            action = st.selectbox("Action", options=["retry", "fallback", "fail"])
            
            if action == "retry":
                retry_after = st.number_input("Retry After (seconds)", min_value=0.0, value=1.0)
            elif action == "fallback":
                fallback_provider = st.text_input("Fallback Provider")
            
            if st.button("📝 Register Error Handler"):
                st.info("Error handler registration would be implemented here")
    
    def render_metrics_analytics(self):
        """Render metrics and analytics"""
        st.header("📊 Metrics & Analytics")
        
        # Get request history
        history = self.abstraction.get_request_history(limit=1000)
        
        if not history:
            st.warning("No request history available")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(history)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['success_rate'] = df['success'].astype(int)
        
        # Time-based metrics
        st.subheader("📈 Request Trends")
        
        # Requests over time
        hourly_requests = df.set_index('timestamp').resample('H').size()
        
        fig_requests = px.line(
            x=hourly_requests.index,
            y=hourly_requests.values,
            title='Requests per Hour',
            labels={'x': 'Time', 'y': 'Request Count'}
        )
        st.plotly_chart(fig_requests, use_container_width=True)
        
        # Success rate over time
        hourly_success = df.set_index('timestamp').resample('H')['success_rate'].mean()
        
        fig_success = px.line(
            x=hourly_success.index,
            y=hourly_success.values,
            title='Success Rate Over Time',
            labels={'x': 'Time', 'y': 'Success Rate'}
        )
        fig_success.update_yaxis(range=[0, 1])
        st.plotly_chart(fig_success, use_container_width=True)
        
        # Provider performance comparison
        st.subheader("🏆 Provider Performance")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Requests by provider
            provider_counts = df['provider'].value_counts()
            
            fig_provider = px.pie(
                values=provider_counts.values,
                names=provider_counts.index,
                title='Requests by Provider'
            )
            st.plotly_chart(fig_provider, use_container_width=True)
        
        with col2:
            # Processing time by provider
            avg_times = df.groupby('provider')['processing_time'].mean()
            
            fig_times = px.bar(
                x=avg_times.index,
                y=avg_times.values,
                title='Average Processing Time by Provider',
                labels={'x': 'Provider', 'y': 'Processing Time (s)'}
            )
            st.plotly_chart(fig_times, use_container_width=True)
        
        # Request type analysis
        st.subheader("📋 Request Type Analysis")
        
        type_success = df.groupby('request_type').agg({
            'success_rate': 'mean',
            'processing_time': 'mean',
            'request_id': 'count'
        }).rename(columns={'request_id': 'count'})
        
        st.dataframe(
            type_success,
            column_config={
                'success_rate': st.column_config.NumberColumn('Success Rate', format="%.2%"),
                'processing_time': st.column_config.NumberColumn('Avg Time (s)', format="%.3f"),
                'count': st.column_config.NumberColumn('Total Requests')
            }
        )
    
    def render_request_history(self):
        """Render request history"""
        st.header("📋 Request History")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            provider_filter = st.selectbox(
                "Filter by Provider",
                options=["All"] + list(self.abstraction.get_provider_metrics().keys())
            )
        
        with col2:
            success_filter = st.selectbox(
                "Filter by Status",
                options=["All", "Success", "Failed"]
            )
        
        with col3:
            limit = st.number_input(
                "Number of Records",
                min_value=10,
                max_value=1000,
                value=100
            )
        
        # Get filtered history
        history = self.abstraction.get_request_history(limit=limit)
        
        if history:
            # Apply filters
            filtered_history = history
            
            if provider_filter != "All":
                filtered_history = [h for h in filtered_history if h['provider'] == provider_filter]
            
            if success_filter == "Success":
                filtered_history = [h for h in filtered_history if h['success']]
            elif success_filter == "Failed":
                filtered_history = [h for h in filtered_history if not h['success']]
            
            # Display as DataFrame
            if filtered_history:
                df = pd.DataFrame(filtered_history)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                st.dataframe(
                    df,
                    column_config={
                        'timestamp': st.column_config.DatetimeColumn('Timestamp'),
                        'success': st.column_config.CheckboxColumn('Success'),
                        'processing_time': st.column_config.NumberColumn('Time (s)', format="%.3f"),
                        'error_message': st.column_config.TextColumn('Error', width="medium")
                    },
                    use_container_width=True
                )
                
                # Export option
                if st.button("📥 Export History"):
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"request_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            else:
                st.info("No records match the selected filters")
        else:
            st.info("No request history available")

def main():
    """Main Streamlit app"""
    st.set_page_config(
        page_title="AI Provider Abstraction",
        page_icon="🔗",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    
    .provider-card {
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .success-result {
        background-color: #e8f5e8;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4caf50;
    }
    
    .error-result {
        background-color: #ffeaea;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f44336;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize and render UI
    ui = ProviderAbstractionUI()
    ui.render()

if __name__ == "__main__":
    main()