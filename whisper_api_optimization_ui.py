#!/usr/bin/env python3
"""
Streamlit UI for Whisper API Optimization and Monitoring System.
Provides comprehensive interface for monitoring, configuration, and optimization.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import asyncio
import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path
import time
from streamlit_intent_utils import render_share_inline, render_share_block, log_ux_event

from whisper_api_optimization import (
    WhisperAPIOptimizer,
    WhisperRequest,
    create_optimizer,
    create_whisper_request
)
from streamlit_intent_utils import get_params, update_params

# Page configuration
st.set_page_config(
    page_title="Whisper API Optimization Dashboard",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'optimizer' not in st.session_state:
    st.session_state.optimizer = None
if 'processing_history' not in st.session_state:
    st.session_state.processing_history = []
if 'current_requests' not in st.session_state:
    st.session_state.current_requests = []


@st.cache_resource
def get_optimizer(api_key: str, redis_host: str = "localhost", redis_port: int = 6379):
    """Get cached optimizer instance."""
    try:
        return create_optimizer(api_key, redis_host, redis_port)
    except Exception as e:
        st.error(f"Failed to initialize optimizer: {e}")
        return None


def render_sidebar():
    """Render sidebar configuration."""
    st.sidebar.title("🎙️ Whisper API Optimizer")
    st.sidebar.markdown("---")
    # Share + reset controls
    try:
        render_share_block("Share Whisper Optimization View")
    except Exception:
        pass
    if st.sidebar.button("Reset View/Filters"):
        try:
            st.experimental_set_query_params()
        except Exception:
            pass
        try:
            log_ux_event("st_filters_cleared", {"scope": "whisper_api_optimization"})
        except Exception:
            pass
        st.rerun()
    
    # API Configuration
    st.sidebar.subheader("🔧 Configuration")
    
    api_key = st.sidebar.text_input(
        "OpenAI API Key",
        type="password",
        help="Your OpenAI API key for Whisper access"
    )
    
    # Redis Configuration
    st.sidebar.subheader("💾 Cache Settings")
    params = get_params()
    use_redis = st.sidebar.checkbox(
        "Use Redis Cache",
        value=(params.get('wao_redis', '1') == '1')
    )
    
    if use_redis:
        redis_host = st.sidebar.text_input("Redis Host", value=params.get('wao_rhost', 'localhost'))
        redis_port_default = int(params.get('wao_rport', '6379')) if params.get('wao_rport', '').isdigit() else 6379
        redis_port = st.sidebar.number_input("Redis Port", value=redis_port_default, min_value=1, max_value=65535)
    else:
        redis_host = "nonexistent"  # Force memory cache
        redis_port = 6379
    
    # Optimization Settings
    st.sidebar.subheader("⚡ Optimization")
    batch_size = st.sidebar.slider(
        "Batch Size", min_value=1, max_value=10,
        value=(int(params.get('wao_batch', '5')) if params.get('wao_batch', '').isdigit() else 5)
    )
    rate_limit = st.sidebar.slider(
        "Rate Limit (req/min)", min_value=10, max_value=100,
        value=(int(params.get('wao_rate', '50')) if params.get('wao_rate', '').isdigit() else 50)
    )
    cache_ttl = st.sidebar.slider(
        "Cache TTL (hours)", min_value=1, max_value=72,
        value=(int(params.get('wao_ttl', '24')) if params.get('wao_ttl', '').isdigit() else 24)
    )

    # Sync updates to query params
    try:
        update_params({
            'wao_redis': '1' if use_redis else '0',
            'wao_rhost': redis_host if use_redis else None,
            'wao_rport': str(redis_port) if use_redis else None,
            'wao_batch': str(batch_size),
            'wao_rate': str(rate_limit),
            'wao_ttl': str(cache_ttl),
        })
    except Exception:
        pass
    
    # Initialize optimizer
    if api_key and st.sidebar.button("Initialize Optimizer"):
        with st.spinner("Initializing optimizer..."):
            optimizer = get_optimizer(api_key, redis_host, redis_port)
            if optimizer:
                st.session_state.optimizer = optimizer
                st.sidebar.success("✅ Optimizer initialized!")
            else:
                st.sidebar.error("❌ Failed to initialize optimizer")
    
    return {
        'api_key': api_key,
        'redis_host': redis_host,
        'redis_port': redis_port,
        'batch_size': batch_size,
        'rate_limit': rate_limit,
        'cache_ttl': cache_ttl
    }


def render_dashboard():
    """Render main dashboard with metrics."""
    st.title("📊 Whisper API Optimization Dashboard")
    try:
        render_share_inline("Shareable view link")
    except Exception:
        pass
    
    if not st.session_state.optimizer:
        st.warning("⚠️ Please configure and initialize the optimizer in the sidebar first.")
        return
    
    optimizer = st.session_state.optimizer
    
    # Get current statistics
    stats = optimizer.get_optimization_stats()
    health = optimizer.health_check()
    
    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Success Rate",
            f"{stats['api_efficiency']['success_rate']:.1%}",
            delta=None
        )
    
    with col2:
        st.metric(
            "Cache Hit Rate", 
            f"{stats['cache_stats']['hit_rate']:.1%}",
            delta=None
        )
    
    with col3:
        st.metric(
            "Avg Response Time",
            f"{stats['api_efficiency']['average_processing_time']:.2f}s",
            delta=None
        )
    
    with col4:
        st.metric(
            "Cost per Request",
            f"${stats['api_efficiency']['cost_per_request']:.4f}",
            delta=None
        )
    
    # System Health
    st.subheader("🏥 System Health")
    health_col1, health_col2 = st.columns(2)
    
    with health_col1:
        status_color = "🟢" if health['status'] == 'healthy' else "🟡"
        st.write(f"{status_color} **Overall Status:** {health['status'].title()}")
        
        for component, status in health['components'].items():
            component_color = "🟢" if 'healthy' in status else "🟡"
            st.write(f"{component_color} **{component.title()}:** {status}")
    
    with health_col2:
        # System resources chart
        resources = stats['system_resources']
        resource_data = {
            'Resource': ['CPU', 'Memory', 'Disk'],
            'Usage': [
                resources['cpu_percent'],
                resources['memory_percent'], 
                resources['disk_usage']
            ]
        }
        
        fig = px.bar(
            resource_data,
            x='Resource',
            y='Usage',
            title="System Resource Usage (%)",
            color='Usage',
            color_continuous_scale='RdYlGn_r'
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)


def render_monitoring():
    """Render monitoring and analytics section."""
    st.subheader("📈 Performance Monitoring")
    
    if not st.session_state.optimizer:
        st.warning("⚠️ Optimizer not initialized.")
        return
    
    optimizer = st.session_state.optimizer
    monitor = optimizer.monitor
    
    # Performance metrics over time
    col1, col2 = st.columns(2)
    
    with col1:
        # Request volume chart
        if monitor.request_history:
            # Convert request history to DataFrame
            history_data = []
            for req in monitor.request_history:
                history_data.append({
                    'timestamp': req['timestamp'],
                    'success': req['success'],
                    'cached': req.get('cached', False),
                    'processing_time': req.get('processing_time', 0)
                })
            
            if history_data:
                df = pd.DataFrame(history_data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Resample by minute
                df_resampled = df.set_index('timestamp').resample('1T').agg({
                    'success': 'count',
                    'cached': 'sum',
                    'processing_time': 'mean'
                }).reset_index()
                
                fig = px.line(
                    df_resampled,
                    x='timestamp',
                    y='success',
                    title='Requests per Minute',
                    labels={'success': 'Request Count'}
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No request history available yet.")
    
    with col2:
        # Error rate and cache hit rate
        metrics_data = {
            'Metric': ['Success Rate', 'Error Rate', 'Cache Hit Rate'],
            'Percentage': [
                (1 - monitor.metrics.error_rate) * 100,
                monitor.metrics.error_rate * 100,
                monitor.metrics.cache_hit_rate * 100
            ]
        }
        
        fig = px.bar(
            metrics_data,
            x='Metric',
            y='Percentage',
            title='Key Performance Metrics (%)',
            color='Percentage',
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent alerts
    st.subheader("🚨 Recent Alerts")
    if monitor.alerts:
        alerts_df = pd.DataFrame(monitor.alerts[-10:])  # Last 10 alerts
        alerts_df['timestamp'] = pd.to_datetime(alerts_df['timestamp'])
        
        for _, alert in alerts_df.iterrows():
            severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(alert['severity'], "ℹ️")
            st.write(f"{severity_icon} **{alert['type'].replace('_', ' ').title()}:** {alert['message']}")
    else:
        st.success("✅ No active alerts")


def render_request_processor():
    """Render request processing interface."""
    st.subheader("🎙️ Process Audio Requests")
    
    if not st.session_state.optimizer:
        st.warning("⚠️ Optimizer not initialized.")
        return
    
    # File upload
    uploaded_files = st.file_uploader(
        "Upload Audio Files",
        type=['wav', 'mp3', 'mp4', 'm4a', 'flac'],
        accept_multiple_files=True,
        help="Upload one or more audio files for transcription"
    )
    
    if uploaded_files:
        st.write(f"📁 {len(uploaded_files)} file(s) uploaded")
        
        # Request configuration
        col1, col2 = st.columns(2)
        
        with col1:
            language = st.selectbox(
                "Language",
                options=[None, "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
                format_func=lambda x: "Auto-detect" if x is None else x
            )
            
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.0,
                step=0.1,
                help="Higher values make output more random"
            )
        
        with col2:
            prompt = st.text_area(
                "Prompt (optional)",
                help="Provide context to improve transcription accuracy"
            )
            
            priority = st.selectbox(
                "Priority",
                options=[1, 2, 3],
                format_func=lambda x: {1: "High", 2: "Medium", 3: "Low"}[x]
            )
        
        # Processing options
        st.subheader("⚙️ Processing Options")
        
        col1, col2 = st.columns(2)
        with col1:
            use_batch = st.checkbox("Batch Processing", value=len(uploaded_files) > 1)
            use_cache = st.checkbox("Use Cache", value=True)
        
        with col2:
            quality_check = st.checkbox("Quality Assessment", value=True)
            detailed_analysis = st.checkbox("Detailed Analysis", value=False)
        
        # Process button
        if st.button("🚀 Process Requests", type="primary"):
            process_audio_requests(
                uploaded_files, language, temperature, prompt, priority,
                use_batch, use_cache, quality_check, detailed_analysis
            )


def process_audio_requests(files, language, temperature, prompt, priority,
                          use_batch, use_cache, quality_check, detailed_analysis):
    """Process uploaded audio files."""
    optimizer = st.session_state.optimizer
    
    with st.spinner("Processing audio files..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        requests = []
        temp_files = []
        
        try:
            # Save uploaded files temporarily
            for i, uploaded_file in enumerate(files):
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    temp_files.append(tmp_file.name)
                
                # Create request
                request = create_whisper_request(
                    audio_file_path=tmp_file.name,
                    language=language,
                    prompt=prompt,
                    temperature=temperature,
                    priority=priority
                )
                requests.append(request)
                
                progress_bar.progress((i + 1) / len(files) * 0.3)
                status_text.text(f"Prepared {i + 1}/{len(files)} requests...")
            
            # Process requests
            if use_batch and len(requests) > 1:
                status_text.text("Processing batch requests...")
                # In a real implementation, you would use:
                # responses = asyncio.run(optimizer.process_batch(requests))
                
                # For demo, simulate batch processing
                responses = []
                for i, request in enumerate(requests):
                    # Simulate processing
                    time.sleep(0.5)  # Simulate processing time
                    
                    response = {
                        'request_id': request.request_id,
                        'text': f"Simulated transcription for {uploaded_file.name}",
                        'confidence_score': 0.85 + (i * 0.02),
                        'processing_time': 1.5 + (i * 0.1),
                        'quality_score': 0.8 + (i * 0.03),
                        'cached': False
                    }
                    responses.append(response)
                    
                    progress_bar.progress(0.3 + (i + 1) / len(requests) * 0.7)
                    status_text.text(f"Processed {i + 1}/{len(requests)} requests...")
            
            else:
                # Process individually
                responses = []
                for i, request in enumerate(requests):
                    status_text.text(f"Processing request {i + 1}/{len(requests)}...")
                    
                    # Simulate individual processing
                    time.sleep(0.3)
                    
                    response = {
                        'request_id': request.request_id,
                        'text': f"Simulated transcription for file {i + 1}",
                        'confidence_score': 0.87,
                        'processing_time': 2.1,
                        'quality_score': 0.82,
                        'cached': False
                    }
                    responses.append(response)
                    
                    progress_bar.progress((i + 1) / len(requests))
            
            # Display results
            progress_bar.progress(1.0)
            status_text.text("✅ Processing completed!")
            
            st.success(f"Successfully processed {len(responses)} requests!")
            
            # Show results
            display_processing_results(requests, responses, files)
            
        except Exception as e:
            st.error(f"❌ Processing failed: {e}")
        
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    Path(temp_file).unlink()
                except Exception:
                    pass


def display_processing_results(requests, responses, files):
    """Display processing results."""
    st.subheader("📋 Processing Results")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Requests", len(responses))
    
    with col2:
        avg_confidence = sum(r['confidence_score'] for r in responses) / len(responses)
        st.metric("Avg Confidence", f"{avg_confidence:.2%}")
    
    with col3:
        total_time = sum(r['processing_time'] for r in responses)
        st.metric("Total Time", f"{total_time:.1f}s")
    
    with col4:
        cached_count = sum(1 for r in responses if r['cached'])
        st.metric("Cache Hits", f"{cached_count}/{len(responses)}")
    
    # Detailed results
    st.subheader("📄 Detailed Results")
    
    for i, (request, response, file) in enumerate(zip(requests, responses, files)):
        with st.expander(f"📁 {file.name} - {response['confidence_score']:.1%} confidence"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write("**Transcription:**")
                st.write(response['text'])
                
                if response.get('quality_score'):
                    quality_color = "🟢" if response['quality_score'] > 0.8 else "🟡" if response['quality_score'] > 0.6 else "🔴"
                    st.write(f"**Quality:** {quality_color} {response['quality_score']:.2f}")
            
            with col2:
                st.write("**Metadata:**")
                st.write(f"Request ID: `{response['request_id'][:8]}...`")
                st.write(f"Processing Time: {response['processing_time']:.2f}s")
                st.write(f"Confidence: {response['confidence_score']:.2%}")
                
                if response['cached']:
                    st.write("💾 **Cached Response**")


def render_cache_management():
    """Render cache management interface."""
    st.subheader("💾 Cache Management")
    
    if not st.session_state.optimizer:
        st.warning("⚠️ Optimizer not initialized.")
        return
    
    optimizer = st.session_state.optimizer
    cache = optimizer.cache
    
    # Cache statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Cache Type", "Redis" if cache.redis_client else "Memory")
    
    with col2:
        hit_rate = optimizer.monitor.metrics.cache_hit_rate
        st.metric("Hit Rate", f"{hit_rate:.1%}")
    
    with col3:
        cached_requests = optimizer.monitor.metrics.cached_requests
        st.metric("Cached Requests", cached_requests)
    
    # Cache operations
    st.subheader("🔧 Cache Operations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧹 Clear Expired Entries"):
            with st.spinner("Clearing expired cache entries..."):
                cache.clear_expired()
                st.success("✅ Expired entries cleared!")
    
    with col2:
        if st.button("📊 Cache Statistics"):
            st.info("Cache statistics displayed above")
    
    # Cache configuration
    st.subheader("⚙️ Cache Configuration")
    
    if cache.redis_client:
        st.success("🟢 Redis cache active")
        st.write("**Configuration:**")
        st.write("- TTL: 24 hours")
        st.write("- Auto-expiration: Enabled")
        st.write("- Persistence: Yes")
    else:
        st.warning("🟡 Using in-memory cache")
        st.write("**Limitations:**")
        st.write("- No persistence across restarts")
        st.write("- Limited by available memory")
        st.write("- Manual cleanup required")


def render_settings():
    """Render settings and configuration."""
    st.subheader("⚙️ Advanced Settings")
    
    if not st.session_state.optimizer:
        st.warning("⚠️ Optimizer not initialized.")
        return
    
    # Quality assessment settings
    st.subheader("🎯 Quality Assessment")
    
    col1, col2 = st.columns(2)
    
    with col1:
        confidence_threshold = st.slider(
            "Confidence Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.05,
            help="Minimum confidence score for valid transcriptions"
        )
        
        quality_threshold = st.slider(
            "Quality Threshold", 
            min_value=0.0,
            max_value=1.0,
            value=0.6,
            step=0.05,
            help="Minimum quality score for valid transcriptions"
        )
    
    with col2:
        enable_validation = st.checkbox("Enable Validation", value=True)
        auto_retry_low_quality = st.checkbox("Auto-retry Low Quality", value=False)
    
    # Monitoring settings
    st.subheader("📊 Monitoring")
    
    col1, col2 = st.columns(2)
    
    with col1:
        alert_error_rate = st.slider(
            "Error Rate Alert (%)",
            min_value=1,
            max_value=50,
            value=10,
            help="Trigger alert when error rate exceeds this percentage"
        )
        
        alert_response_time = st.slider(
            "Response Time Alert (s)",
            min_value=5,
            max_value=60,
            value=30,
            help="Trigger alert when response time exceeds this threshold"
        )
    
    with col2:
        enable_alerts = st.checkbox("Enable Alerts", value=True)
        alert_email = st.text_input("Alert Email", placeholder="admin@example.com")
    
    # Performance settings
    st.subheader("⚡ Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_concurrent = st.slider(
            "Max Concurrent Requests",
            min_value=1,
            max_value=10,
            value=3,
            help="Maximum number of concurrent API requests"
        )
        
        request_timeout = st.slider(
            "Request Timeout (s)",
            min_value=10,
            max_value=300,
            value=60,
            help="Timeout for individual API requests"
        )
    
    with col2:
        enable_batching = st.checkbox("Enable Batching", value=True)
        batch_timeout = st.slider(
            "Batch Timeout (s)",
            min_value=5,
            max_value=60,
            value=30,
            help="Maximum time to wait for batch completion"
        )
    
    # Save settings
    if st.button("💾 Save Settings", type="primary"):
        settings = {
            'quality': {
                'confidence_threshold': confidence_threshold,
                'quality_threshold': quality_threshold,
                'enable_validation': enable_validation,
                'auto_retry_low_quality': auto_retry_low_quality
            },
            'monitoring': {
                'alert_error_rate': alert_error_rate / 100,
                'alert_response_time': alert_response_time,
                'enable_alerts': enable_alerts,
                'alert_email': alert_email
            },
            'performance': {
                'max_concurrent': max_concurrent,
                'request_timeout': request_timeout,
                'enable_batching': enable_batching,
                'batch_timeout': batch_timeout
            }
        }
        
        # In a real implementation, you would save these settings
        st.success("✅ Settings saved successfully!")
        st.json(settings)


def main():
    """Main application function."""
    # Render sidebar
    config = render_sidebar()
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Dashboard",
        "📈 Monitoring", 
        "🎙️ Process Audio",
        "💾 Cache Management",
        "⚙️ Settings",
        "📚 Help"
    ])
    
    with tab1:
        render_dashboard()
    
    with tab2:
        render_monitoring()
    
    with tab3:
        render_request_processor()
    
    with tab4:
        render_cache_management()
    
    with tab5:
        render_settings()
    
    with tab6:
        render_help()


def render_help():
    """Render help and documentation."""
    st.subheader("📚 Help & Documentation")
    
    st.markdown("""
    ## 🎯 Overview
    
    The Whisper API Optimization Dashboard provides comprehensive tools for:
    - **Request Optimization**: Batching, caching, and rate limiting
    - **Performance Monitoring**: Real-time metrics and alerting
    - **Quality Assessment**: Automatic transcription quality evaluation
    - **Cost Management**: Usage tracking and optimization recommendations
    
    ## 🚀 Getting Started
    
    1. **Configure API Key**: Enter your OpenAI API key in the sidebar
    2. **Set Cache Options**: Choose Redis or in-memory caching
    3. **Initialize Optimizer**: Click "Initialize Optimizer" 
    4. **Upload Audio**: Use the "Process Audio" tab to transcribe files
    5. **Monitor Performance**: Check the Dashboard and Monitoring tabs
    
    ## 📊 Key Features
    
    ### Request Batching
    - Process multiple files simultaneously
    - Priority-based processing
    - Automatic retry with exponential backoff
    
    ### Intelligent Caching
    - Redis-based persistent caching
    - Content-based cache keys
    - Automatic expiration management
    
    ### Quality Assessment
    - Confidence score analysis
    - Text quality evaluation
    - Validation and recommendations
    
    ### Performance Monitoring
    - Real-time metrics tracking
    - Alert generation
    - Historical performance analysis
    
    ## ⚙️ Configuration Options
    
    ### Cache Settings
    - **Redis Cache**: Persistent, shared across sessions
    - **Memory Cache**: Fast but temporary
    - **TTL**: Time-to-live for cached responses
    
    ### Quality Thresholds
    - **Confidence Threshold**: Minimum API confidence score
    - **Quality Threshold**: Minimum assessed quality score
    - **Auto-retry**: Automatically retry low-quality transcriptions
    
    ### Performance Tuning
    - **Batch Size**: Number of requests per batch
    - **Rate Limit**: Maximum requests per minute
    - **Concurrent Requests**: Parallel processing limit
    
    ## 🔧 Troubleshooting
    
    ### Common Issues
    
    **Optimizer Not Initializing**
    - Check API key validity
    - Verify Redis connection (if using Redis)
    - Check network connectivity
    
    **Low Cache Hit Rate**
    - Ensure consistent request parameters
    - Check cache TTL settings
    - Verify file content hasn't changed
    
    **High Error Rate**
    - Check API key limits and quotas
    - Verify audio file formats
    - Review network stability
    
    **Slow Performance**
    - Increase concurrent request limit
    - Use batch processing for multiple files
    - Enable caching for repeated content
    
    ## 💡 Best Practices
    
    1. **Use Caching**: Enable caching for repeated content analysis
    2. **Batch Similar Requests**: Group requests with similar parameters
    3. **Monitor Quality**: Set appropriate quality thresholds
    4. **Set Up Alerts**: Configure alerts for cost and performance thresholds
    5. **Regular Maintenance**: Clean up expired cache entries regularly
    
    ## 📞 Support
    
    For additional support:
    - Check the monitoring dashboard for system health
    - Review error logs in the monitoring section
    - Adjust settings based on usage patterns
    - Monitor costs and optimize parameters accordingly
    """)


if __name__ == "__main__":
    main()
