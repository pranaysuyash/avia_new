"""
Streamlit UI for Processing Router and Workflow Engine
Interactive interface for intelligent media processing routing and workflow orchestration
"""

import streamlit as st
import asyncio
import json
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import tempfile
import os

# Import our processing router
try:
    from processing_router_workflow_engine import (
        ProcessingRouterWorkflowEngine,
        MediaType,
        ContentComplexity,
        ProcessingStrategy,
        WorkflowPriority,
        WorkflowStatus
    )
    ROUTER_AVAILABLE = True
except ImportError as e:
    st.error(f"Processing Router not available: {e}")
    ROUTER_AVAILABLE = False

def init_session_state():
    """Initialize session state variables"""
    if 'processing_engine' not in st.session_state:
        if ROUTER_AVAILABLE:
            st.session_state.processing_engine = ProcessingRouterWorkflowEngine(max_concurrent_jobs=3)
        else:
            st.session_state.processing_engine = None
    
    if 'active_jobs' not in st.session_state:
        st.session_state.active_jobs = {}
    
    if 'job_history' not in st.session_state:
        st.session_state.job_history = []
    
    if 'selected_tab' not in st.session_state:
        st.session_state.selected_tab = "Process Media"

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Processing Router & Workflow Engine",
        page_icon="⚙️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    init_session_state()
    
    # Header
    st.title("⚙️ Processing Router & Workflow Engine")
    st.markdown("Intelligent media processing routing and workflow orchestration")
    
    if not ROUTER_AVAILABLE:
        st.error("Processing Router is not available. Please check the installation.")
        return
    
    # Sidebar
    with st.sidebar:
        st.header("🎛️ Control Panel")
        
        # Engine status
        if st.session_state.processing_engine:
            metrics = st.session_state.processing_engine.get_performance_metrics()
            st.success("🟢 Engine Online")
            st.metric("Active Jobs", metrics['active_jobs'])
            st.metric("Total Processed", metrics['total_jobs'])
            st.metric("Success Rate", f"{metrics['successful_jobs']}/{metrics['total_jobs']}")
        else:
            st.error("🔴 Engine Offline")
        
        # Navigation
        st.header("📋 Navigation")
        tabs = ["Process Media", "Job Monitor", "Route Manager", "Analytics", "Settings"]
        selected_tab = st.selectbox("Select View", tabs, index=tabs.index(st.session_state.selected_tab))
        st.session_state.selected_tab = selected_tab
        
        # Quick actions
        st.header("⚡ Quick Actions")
        if st.button("🔄 Refresh Status"):
            st.rerun()
        
        if st.button("🧹 Clear History"):
            st.session_state.job_history = []
            st.success("History cleared!")
    
    # Main content based on selected tab
    if st.session_state.selected_tab == "Process Media":
        show_process_media_tab()
    elif st.session_state.selected_tab == "Job Monitor":
        show_job_monitor_tab()
    elif st.session_state.selected_tab == "Route Manager":
        show_route_manager_tab()
    elif st.session_state.selected_tab == "Analytics":
        show_analytics_tab()
    elif st.session_state.selected_tab == "Settings":
        show_settings_tab()

def show_process_media_tab():
    """Show media processing interface"""
    st.header("📁 Media Processing")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Upload Media File")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a media file",
            type=['mp3', 'wav', 'm4a', 'flac', 'mp4', 'avi', 'mov', 'mkv', 'pdf', 'jpg', 'png'],
            help="Supported formats: Audio (MP3, WAV, M4A, FLAC), Video (MP4, AVI, MOV, MKV), Documents (PDF), Images (JPG, PNG)"
        )
        
        if uploaded_file is not None:
            # Display file info
            st.info(f"📄 File: {uploaded_file.name} ({uploaded_file.size / 1024 / 1024:.2f} MB)")
            
            # Processing options
            st.subheader("⚙️ Processing Options")
            
            col_opt1, col_opt2 = st.columns(2)
            
            with col_opt1:
                # Priority selection
                priority = st.selectbox(
                    "Priority",
                    ["low", "normal", "high", "critical"],
                    index=1,
                    help="Processing priority level"
                )
                
                # Custom route selection
                if st.session_state.processing_engine:
                    routes = list(st.session_state.processing_engine.processing_routes.keys())
                    custom_route = st.selectbox(
                        "Custom Route (Optional)",
                        ["Auto-select"] + routes,
                        help="Select a specific processing route or let the system choose automatically"
                    )
                    if custom_route == "Auto-select":
                        custom_route = None
                else:
                    custom_route = None
            
            with col_opt2:
                # Advanced options
                st.write("**Advanced Options**")
                enable_fallback = st.checkbox("Enable Fallback Routes", value=True)
                enable_monitoring = st.checkbox("Real-time Monitoring", value=True)
                save_intermediate = st.checkbox("Save Intermediate Results", value=False)
            
            # Process button
            if st.button("🚀 Start Processing", type="primary"):
                process_uploaded_file(uploaded_file, priority, custom_route, {
                    'enable_fallback': enable_fallback,
                    'enable_monitoring': enable_monitoring,
                    'save_intermediate': save_intermediate
                })
    
    with col2:
        st.subheader("📊 Content Analysis Preview")
        
        if uploaded_file is not None and st.session_state.processing_engine:
            # Save file temporarily for analysis
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_file_path = tmp_file.name
            
            try:
                # Analyze content
                with st.spinner("Analyzing content..."):
                    analysis = asyncio.run(st.session_state.processing_engine.analyze_content(tmp_file_path))
                
                # Display analysis results
                st.metric("Media Type", analysis.media_type.value.title())
                st.metric("Complexity", analysis.complexity.value.title())
                st.metric("Quality Score", f"{analysis.quality_score:.2f}")
                st.metric("Est. Processing Time", f"{analysis.estimated_processing_time:.1f}s")
                
                # Processing requirements
                st.write("**Processing Requirements:**")
                for req in analysis.processing_requirements:
                    st.write(f"• {req.replace('_', ' ').title()}")
                
                # Resource requirements
                st.write("**Resource Requirements:**")
                st.write(f"• CPU: {analysis.resource_requirements.get('cpu', 1)} cores")
                st.write(f"• Memory: {analysis.resource_requirements.get('memory', 512)} MB")
                st.write(f"• Disk: {analysis.resource_requirements.get('disk', 0)} MB")
                
                # Recommended route
                route = st.session_state.processing_engine.select_processing_route(analysis)
                st.success(f"**Recommended Route:** {route.name}")
                
            except Exception as e:
                st.error(f"Analysis failed: {e}")
            finally:
                os.unlink(tmp_file_path)

def process_uploaded_file(uploaded_file, priority, custom_route, options):
    """Process the uploaded file"""
    try:
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_file_path = tmp_file.name
        
        # Convert priority string to enum
        priority_enum = WorkflowPriority(priority.lower())
        
        # Start processing
        with st.spinner("Starting processing..."):
            job_id = asyncio.run(st.session_state.processing_engine.process_media(
                tmp_file_path,
                custom_route=custom_route,
                priority=priority_enum
            ))
        
        # Add to active jobs
        st.session_state.active_jobs[job_id] = {
            'filename': uploaded_file.name,
            'started_at': datetime.now(),
            'options': options
        }
        
        st.success(f"✅ Processing started! Job ID: {job_id}")
        st.info("Switch to the 'Job Monitor' tab to track progress.")
        
        # Schedule cleanup
        # Note: In a real application, you'd want a better cleanup mechanism
        
    except Exception as e:
        st.error(f"❌ Processing failed: {e}")

def show_job_monitor_tab():
    """Show job monitoring interface"""
    st.header("📈 Job Monitor")
    
    if not st.session_state.processing_engine:
        st.error("Processing engine not available")
        return
    
    # Auto-refresh toggle
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        auto_refresh = st.checkbox("Auto Refresh", value=True)
    with col2:
        refresh_interval = st.selectbox("Refresh Interval", [1, 2, 5, 10], index=1)
    with col3:
        if st.button("🔄 Manual Refresh"):
            st.rerun()
    
    # Get current jobs
    active_jobs = []
    completed_jobs = []
    
    for job_id in st.session_state.active_jobs.keys():
        status = st.session_state.processing_engine.get_job_status(job_id)
        if status:
            job_info = {
                'job_id': job_id,
                'filename': st.session_state.active_jobs[job_id]['filename'],
                **status
            }
            
            if status['status'] in ['completed', 'failed', 'cancelled']:
                completed_jobs.append(job_info)
                # Move to history
                if job_id not in [j['job_id'] for j in st.session_state.job_history]:
                    st.session_state.job_history.append(job_info)
            else:
                active_jobs.append(job_info)
    
    # Active jobs section
    st.subheader("🔄 Active Jobs")
    if active_jobs:
        for job in active_jobs:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    st.write(f"**{job['filename']}**")
                    st.write(f"Job ID: `{job['job_id'][:8]}...`")
                
                with col2:
                    status_color = {
                        'pending': '🟡',
                        'running': '🔵',
                        'completed': '🟢',
                        'failed': '🔴',
                        'cancelled': '⚫'
                    }
                    st.write(f"{status_color.get(job['status'], '⚪')} {job['status'].title()}")
                
                with col3:
                    progress = job.get('progress', 0.0)
                    st.progress(progress)
                    st.write(f"{progress:.1%}")
                
                with col4:
                    st.write(f"Route: {job.get('route', 'Unknown')}")
                
                # Progress details
                if job['status'] == 'running' and job.get('results'):
                    st.write("**Current Step:**")
                    results = job['results']
                    for step, result in results.items():
                        if isinstance(result, dict) and result.get('success'):
                            st.write(f"✅ {step.replace('_', ' ').title()}")
                
                st.divider()
    else:
        st.info("No active jobs")
    
    # Completed jobs section
    st.subheader("✅ Recent Completed Jobs")
    if completed_jobs or st.session_state.job_history:
        all_completed = completed_jobs + st.session_state.job_history[-10:]  # Show last 10
        
        # Create DataFrame for better display
        df_data = []
        for job in all_completed:
            df_data.append({
                'Filename': job['filename'],
                'Status': job['status'].title(),
                'Route': job.get('route', 'Unknown'),
                'Progress': f"{job.get('progress', 0.0):.1%}",
                'Started': job.get('started_at', 'Unknown'),
                'Completed': job.get('completed_at', 'Unknown')
            })
        
        if df_data:
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
    else:
        st.info("No completed jobs")
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

def show_route_manager_tab():
    """Show processing route management interface"""
    st.header("🛤️ Route Manager")
    
    if not st.session_state.processing_engine:
        st.error("Processing engine not available")
        return
    
    # Route overview
    routes = st.session_state.processing_engine.processing_routes
    
    st.subheader("📋 Available Routes")
    
    # Route selection
    route_names = list(routes.keys())
    selected_route = st.selectbox("Select Route", route_names)
    
    if selected_route:
        route = routes[selected_route]
        
        # Route details
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Route Information**")
            st.write(f"**Name:** {route.name}")
            st.write(f"**Description:** {route.description}")
            st.write(f"**Strategy:** {route.strategy.value.title()}")
            st.write(f"**Mode:** {route.mode.value.title()}")
            st.write(f"**Priority:** {route.priority.value.title()}")
            
            st.write("**Media Types:**")
            for media_type in route.media_types:
                st.write(f"• {media_type.value.title()}")
            
            st.write("**Complexity Levels:**")
            for complexity in route.complexity_levels:
                st.write(f"• {complexity.value.title()}")
        
        with col2:
            st.write("**Processing Configuration**")
            st.metric("Estimated Duration", f"{route.estimated_duration}s")
            st.metric("Resource Cost", f"{route.resource_cost}")
            
            st.write("**Processing Steps:**")
            for i, step in enumerate(route.processing_steps, 1):
                st.write(f"{i}. {step.replace('_', ' ').title()}")
            
            if route.fallback_routes:
                st.write("**Fallback Routes:**")
                for fallback in route.fallback_routes:
                    st.write(f"• {fallback}")
    
    # Route comparison
    st.subheader("📊 Route Comparison")
    
    if len(routes) > 1:
        # Create comparison data
        comparison_data = []
        for route_id, route in routes.items():
            comparison_data.append({
                'Route': route.name,
                'Strategy': route.strategy.value,
                'Duration (s)': route.estimated_duration,
                'Resource Cost': route.resource_cost,
                'Steps': len(route.processing_steps),
                'Media Types': len(route.media_types),
                'Fallbacks': len(route.fallback_routes)
            })
        
        df = pd.DataFrame(comparison_data)
        st.dataframe(df, use_container_width=True)
        
        # Visualization
        fig = px.scatter(
            df, 
            x='Duration (s)', 
            y='Resource Cost',
            size='Steps',
            color='Strategy',
            hover_name='Route',
            title="Route Performance Comparison"
        )
        st.plotly_chart(fig, use_container_width=True)

def show_analytics_tab():
    """Show analytics and performance metrics"""
    st.header("📊 Analytics & Performance")
    
    if not st.session_state.processing_engine:
        st.error("Processing engine not available")
        return
    
    # Get metrics
    metrics = st.session_state.processing_engine.get_performance_metrics()
    
    # Overview metrics
    st.subheader("📈 Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Jobs", metrics['total_jobs'])
    with col2:
        st.metric("Success Rate", f"{metrics['successful_jobs']}/{metrics['total_jobs']}")
    with col3:
        st.metric("Avg Processing Time", f"{metrics['average_processing_time']:.2f}s")
    with col4:
        st.metric("Active Jobs", metrics['active_jobs'])
    
    # Performance charts
    if metrics['total_jobs'] > 0:
        st.subheader("📊 Performance Charts")
        
        # Success rate pie chart
        col1, col2 = st.columns(2)
        
        with col1:
            success_data = {
                'Status': ['Successful', 'Failed'],
                'Count': [metrics['successful_jobs'], metrics['failed_jobs']]
            }
            fig_pie = px.pie(
                success_data, 
                values='Count', 
                names='Status',
                title="Job Success Rate"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Route usage (mock data for demonstration)
            route_usage = {
                'audio_basic': 15,
                'audio_professional': 8,
                'video_basic': 12,
                'video_professional': 5,
                'document_basic': 10
            }
            
            route_data = pd.DataFrame([
                {'Route': route, 'Usage': count} 
                for route, count in route_usage.items()
            ])
            
            fig_bar = px.bar(
                route_data,
                x='Route',
                y='Usage',
                title="Route Usage Statistics"
            )
            st.plotly_chart(fig_bar, use_container_width=True)
    
    # System resources
    st.subheader("💻 System Resources")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Available Routes", metrics['available_routes'])
    with col2:
        st.metric("Queued Jobs", metrics['queued_jobs'])
    with col3:
        # Mock resource utilization
        resource_util = min(metrics['active_jobs'] * 25, 100)
        st.metric("Resource Utilization", f"{resource_util}%")
    
    # Historical data (mock for demonstration)
    st.subheader("📈 Historical Trends")
    
    # Generate mock historical data
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    historical_data = pd.DataFrame({
        'Date': dates,
        'Jobs Processed': [max(0, 10 + int(5 * (i % 7 - 3.5))) for i in range(len(dates))],
        'Success Rate': [max(0.7, 0.95 - 0.1 * abs((i % 14 - 7) / 7)) for i in range(len(dates))],
        'Avg Processing Time': [max(30, 60 + 20 * ((i % 10 - 5) / 5)) for i in range(len(dates))]
    })
    
    # Time series charts
    fig_time = go.Figure()
    fig_time.add_trace(go.Scatter(
        x=historical_data['Date'],
        y=historical_data['Jobs Processed'],
        mode='lines+markers',
        name='Jobs Processed'
    ))
    fig_time.update_layout(title="Daily Job Processing Trend")
    st.plotly_chart(fig_time, use_container_width=True)

def show_settings_tab():
    """Show settings and configuration"""
    st.header("⚙️ Settings & Configuration")
    
    # Engine settings
    st.subheader("🔧 Engine Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Processing Settings**")
        max_concurrent = st.slider("Max Concurrent Jobs", 1, 10, 3)
        enable_fallbacks = st.checkbox("Enable Fallback Routes", value=True)
        auto_cleanup = st.checkbox("Auto Cleanup Temp Files", value=True)
        
        st.write("**Performance Settings**")
        cpu_limit = st.slider("CPU Usage Limit (%)", 10, 100, 80)
        memory_limit = st.slider("Memory Usage Limit (GB)", 1, 16, 8)
    
    with col2:
        st.write("**Monitoring Settings**")
        log_level = st.selectbox("Log Level", ["DEBUG", "INFO", "WARNING", "ERROR"], index=1)
        metrics_retention = st.slider("Metrics Retention (days)", 1, 90, 30)
        
        st.write("**Notification Settings**")
        notify_completion = st.checkbox("Notify on Job Completion", value=True)
        notify_failures = st.checkbox("Notify on Job Failures", value=True)
        email_notifications = st.text_input("Email for Notifications", placeholder="user@example.com")
    
    # Route configuration
    st.subheader("🛤️ Route Configuration")
    
    if st.session_state.processing_engine:
        routes = st.session_state.processing_engine.processing_routes
        
        # Route enable/disable
        st.write("**Enable/Disable Routes**")
        for route_id, route in routes.items():
            enabled = st.checkbox(f"{route.name}", value=True, key=f"route_{route_id}")
    
    # Advanced settings
    st.subheader("🔬 Advanced Settings")
    
    with st.expander("Advanced Configuration"):
        st.write("**Processing Timeouts**")
        default_timeout = st.number_input("Default Timeout (seconds)", 60, 3600, 300)
        
        st.write("**Retry Settings**")
        max_retries = st.number_input("Max Retries", 0, 10, 3)
        retry_delay = st.number_input("Retry Delay (seconds)", 1, 60, 5)
        
        st.write("**Storage Settings**")
        temp_dir = st.text_input("Temporary Directory", value="/tmp/processing")
        output_dir = st.text_input("Output Directory", value="/tmp/output")
    
    # Save settings
    if st.button("💾 Save Settings", type="primary"):
        st.success("Settings saved successfully!")
        # In a real application, you would save these settings to a configuration file

if __name__ == "__main__":
    main()