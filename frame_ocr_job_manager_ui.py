"""
Streamlit UI for Frame OCR Job Management System

This module provides a comprehensive web interface for managing Frame OCR jobs
with enterprise features including monitoring, analytics, and administration.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional
import time

from frame_ocr_job_manager import (
    FrameOCRJobManager, JobStatus, JobPriority, ProcessingMode,
    ResourceAllocation, RetryConfig, FrameOCRJob
)
from streamlit_intent_utils import render_share_inline, render_share_block, log_ux_event, get_params, update_params

# Page configuration
st.set_page_config(
    page_title="Frame OCR Job Management",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'job_manager' not in st.session_state:
    st.session_state.job_manager = FrameOCRJobManager()

if 'selected_tenant' not in st.session_state:
    st.session_state.selected_tenant = "tenant_1"

if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False

def main():
    """Main application interface"""
    st.title("🎬 Frame OCR Job Management System")
    st.markdown("Enterprise-grade job management and workflow orchestration")
    # Inline share and sidebar share/reset
    try:
        render_share_inline("Shareable view link")
    except Exception:
        pass
    with st.sidebar:
        try:
            render_share_block("Share Job Manager View")
        except Exception:
            pass
        if st.button("Reset View/Filters"):
            try:
                st.experimental_set_query_params()
            except Exception:
                pass
            try:
                log_ux_event("st_filters_cleared", {"scope": "frame_ocr_job_manager"})
            except Exception:
                pass
            st.rerun()
    
    # Sidebar navigation
    with st.sidebar:
        st.header("Navigation")
        params = get_params()
        pages = ["Dashboard", "Job Management", "Create Job", "Analytics", 
             "Resource Management", "System Settings", "Monitoring"]
        page_default = params.get('fojm_page', 'Dashboard')
        page = st.selectbox(
            "Select Page",
            pages,
            index=(pages.index(page_default) if page_default in pages else 0)
        )
        try:
            update_params({'fojm_page': page})
        except Exception:
            pass
        
        st.divider()
        
        # Tenant selection
        st.subheader("Tenant Selection")
        tenant_default = params.get('fojm_tenant', st.session_state.selected_tenant)
        tenant_id = st.text_input("Tenant ID", value=tenant_default)
        if tenant_id != st.session_state.selected_tenant:
            st.session_state.selected_tenant = tenant_id
        try:
            update_params({'fojm_tenant': tenant_id})
        except Exception:
            pass
        
        # Auto-refresh toggle
        st.subheader("Settings")
        auto_refresh = st.checkbox(
            "Auto-refresh (30s)",
            value=(params.get('fojm_auto', '1' if st.session_state.auto_refresh else '0') == '1')
        )
        st.session_state.auto_refresh = auto_refresh
        try:
            update_params({'fojm_auto': '1' if auto_refresh else '0'})
        except Exception:
            pass
        
        if auto_refresh:
            time.sleep(30)
            st.rerun()
    
    # Route to selected page
    if page == "Dashboard":
        show_dashboard()
    elif page == "Job Management":
        show_job_management()
    elif page == "Create Job":
        show_create_job()
    elif page == "Analytics":
        show_analytics()
    elif page == "Resource Management":
        show_resource_management()
    elif page == "System Settings":
        show_system_settings()
    elif page == "Monitoring":
        show_monitoring()

def show_dashboard():
    """Dashboard overview"""
    st.header("📊 Dashboard Overview")
    
    job_manager = st.session_state.job_manager
    tenant_id = st.session_state.selected_tenant
    
    # Get statistics
    stats = job_manager.get_job_statistics(tenant_id)
    cost_analytics = job_manager.get_cost_analytics(tenant_id)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Jobs",
            stats['total_jobs'],
            delta=None
        )
    
    with col2:
        st.metric(
            "Success Rate",
            f"{stats['success_rate']:.1%}",
            delta=None
        )
    
    with col3:
        st.metric(
            "Running Jobs",
            stats['running_jobs'],
            delta=None
        )
    
    with col4:
        st.metric(
            "Total Cost",
            f"${cost_analytics['total_cost']:.2f}",
            delta=None
        )
    
    # Status distribution chart
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Job Status Distribution")
        if stats['status_counts']:
            fig = px.pie(
                values=list(stats['status_counts'].values()),
                names=list(stats['status_counts'].keys()),
                title="Job Status Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No jobs found")
    
    with col2:
        st.subheader("Recent Jobs")
        recent_jobs = job_manager.list_jobs(tenant_id, limit=10)
        
        if recent_jobs:
            job_data = []
            for job in recent_jobs:
                job_data.append({
                    'Job ID': job.job_id[:8] + '...',
                    'Video ID': job.video_id,
                    'Status': job.status.value,
                    'Priority': job.priority.value,
                    'Progress': f"{job.progress:.1%}",
                    'Created': job.created_at.strftime('%Y-%m-%d %H:%M')
                })
            
            df = pd.DataFrame(job_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No recent jobs")
    
    # System health indicators
    st.subheader("System Health")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        queue_size = stats['queue_size']
        queue_status = "🟢 Normal" if queue_size < 10 else "🟡 Busy" if queue_size < 50 else "🔴 Overloaded"
        st.metric("Queue Size", queue_size, help=queue_status)
    
    with col2:
        avg_processing_time = cost_analytics['avg_processing_time']
        st.metric("Avg Processing Time", f"{avg_processing_time:.1f}s")
    
    with col3:
        cost_per_job = cost_analytics['cost_per_job']
        st.metric("Cost per Job", f"${cost_per_job:.3f}")

def show_job_management():
    """Job management interface"""
    st.header("🔧 Job Management")
    
    job_manager = st.session_state.job_manager
    tenant_id = st.session_state.selected_tenant
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All"] + [status.value for status in JobStatus]
        )
    
    with col2:
        priority_filter = st.selectbox(
            "Filter by Priority",
            ["All"] + [priority.value for priority in JobPriority]
        )
    
    with col3:
        limit = st.number_input("Limit", min_value=10, max_value=1000, value=50)
    
    with col4:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    # Get jobs
    status_enum = None if status_filter == "All" else JobStatus(status_filter)
    jobs = job_manager.list_jobs(tenant_id, status=status_enum, limit=limit)
    
    if priority_filter != "All":
        jobs = [job for job in jobs if job.priority.value == priority_filter]
    
    # Jobs table
    if jobs:
        st.subheader(f"Jobs ({len(jobs)} found)")
        
        # Prepare data for display
        job_data = []
        for job in jobs:
            job_data.append({
                'Select': False,
                'Job ID': job.job_id,
                'Video ID': job.video_id,
                'Status': job.status.value,
                'Priority': job.priority.value,
                'Progress': job.progress,
                'Created': job.created_at,
                'Started': job.started_at,
                'Completed': job.completed_at,
                'Error': job.error_message or '',
                'Retry Count': job.retry_count,
                'Cost Estimate': job.metrics.cost_estimate if job.metrics else 0.0
            })
        
        df = pd.DataFrame(job_data)
        
        # Display editable dataframe
        edited_df = st.data_editor(
            df,
            column_config={
                'Select': st.column_config.CheckboxColumn('Select'),
                'Job ID': st.column_config.TextColumn('Job ID', width='medium'),
                'Progress': st.column_config.ProgressColumn('Progress', min_value=0, max_value=1),
                'Created': st.column_config.DatetimeColumn('Created'),
                'Started': st.column_config.DatetimeColumn('Started'),
                'Completed': st.column_config.DatetimeColumn('Completed'),
                'Cost Estimate': st.column_config.NumberColumn('Cost ($)', format='$%.3f')
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Bulk actions
        selected_jobs = edited_df[edited_df['Select']]['Job ID'].tolist()
        
        if selected_jobs:
            st.subheader("Bulk Actions")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("🚫 Cancel Selected"):
                    for job_id in selected_jobs:
                        job_manager.cancel_job(job_id)
                    st.success(f"Cancelled {len(selected_jobs)} jobs")
                    st.rerun()
            
            with col2:
                if st.button("🔄 Retry Selected"):
                    retry_count = 0
                    for job_id in selected_jobs:
                        if job_manager.retry_job(job_id):
                            retry_count += 1
                    st.success(f"Retried {retry_count} jobs")
                    st.rerun()
            
            with col3:
                if st.button("⏸️ Pause Selected"):
                    pause_count = 0
                    for job_id in selected_jobs:
                        if job_manager.pause_job(job_id):
                            pause_count += 1
                    st.success(f"Paused {pause_count} jobs")
                    st.rerun()
            
            with col4:
                if st.button("▶️ Resume Selected"):
                    resume_count = 0
                    for job_id in selected_jobs:
                        if job_manager.resume_job(job_id):
                            resume_count += 1
                    st.success(f"Resumed {resume_count} jobs")
                    st.rerun()
        
        # Individual job details
        if st.checkbox("Show Job Details"):
            selected_job_id = st.selectbox("Select Job", [job.job_id for job in jobs])
            
            if selected_job_id:
                job = job_manager.get_job(selected_job_id)
                if job:
                    show_job_details(job)
    
    else:
        st.info("No jobs found matching the criteria")

def show_job_details(job: FrameOCRJob):
    """Show detailed job information"""
    st.subheader(f"Job Details: {job.job_id}")
    
    # Basic information
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Basic Information**")
        st.write(f"Job ID: `{job.job_id}`")
        st.write(f"Tenant ID: `{job.tenant_id}`")
        st.write(f"Video ID: `{job.video_id}`")
        st.write(f"Video Path: `{job.video_path}`")
        st.write(f"Status: `{job.status.value}`")
        st.write(f"Priority: `{job.priority.value}`")
        st.write(f"Progress: {job.progress:.1%}")
        st.write(f"Retry Count: {job.retry_count}")
    
    with col2:
        st.write("**Timestamps**")
        st.write(f"Created: {job.created_at}")
        st.write(f"Scheduled: {job.scheduled_at or 'N/A'}")
        st.write(f"Started: {job.started_at or 'N/A'}")
        st.write(f"Completed: {job.completed_at or 'N/A'}")
        
        if job.started_at and job.completed_at:
            duration = job.completed_at - job.started_at
            st.write(f"Duration: {duration}")
    
    # Configuration
    st.write("**Configuration**")
    st.json(job.config)
    
    # Metrics
    if job.metrics:
        st.write("**Metrics**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Frames Processed", job.metrics.frames_processed)
            st.metric("Total Frames", job.metrics.frames_total)
        
        with col2:
            st.metric("Cost Estimate", f"${job.metrics.cost_estimate:.3f}")
            st.metric("Actual Cost", f"${job.metrics.actual_cost:.3f}")
        
        with col3:
            st.metric("CPU Usage", f"{job.metrics.cpu_usage:.1%}")
            st.metric("Memory Usage", f"{job.metrics.memory_usage:.0f} MB")
    
    # Error information
    if job.error_message:
        st.error(f"Error: {job.error_message}")
    
    # Tags and dependencies
    if job.tags:
        st.write(f"**Tags:** {', '.join(job.tags)}")
    
    if job.dependencies:
        st.write(f"**Dependencies:** {', '.join(job.dependencies)}")

def show_create_job():
    """Job creation interface"""
    st.header("➕ Create New Job")
    
    job_manager = st.session_state.job_manager
    
    with st.form("create_job_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            tenant_id = st.text_input("Tenant ID", value=st.session_state.selected_tenant)
            video_id = st.text_input("Video ID", placeholder="video_123")
            video_path = st.text_input("Video Path", placeholder="/path/to/video.mp4")
            priority = st.selectbox("Priority", [p.value for p in JobPriority])
        
        with col2:
            # Scheduling
            schedule_later = st.checkbox("Schedule for later")
            scheduled_at = None
            if schedule_later:
                scheduled_date = st.date_input("Schedule Date")
                scheduled_time = st.time_input("Schedule Time")
                scheduled_at = datetime.combine(scheduled_date, scheduled_time)
            
            # Tags
            tags_input = st.text_input("Tags (comma-separated)", placeholder="tag1, tag2")
            tags = [tag.strip() for tag in tags_input.split(",")] if tags_input else []
            
            # Webhook
            webhook_url = st.text_input("Webhook URL (optional)", placeholder="https://example.com/webhook")
        
        # Configuration
        st.subheader("Processing Configuration")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            sampling_interval = st.number_input("Sampling Interval (seconds)", min_value=0.1, value=1.0, step=0.1)
            max_frames = st.number_input("Max Frames", min_value=1, value=1000)
        
        with col2:
            ocr_engines = st.multiselect(
                "OCR Engines",
                ["tesseract", "easyocr", "cloud_vision", "textract"],
                default=["tesseract"]
            )
            confidence_threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.8)
        
        with col3:
            languages = st.multiselect(
                "Languages",
                ["en", "es", "fr", "de", "zh", "ja", "ko"],
                default=["en"]
            )
            preprocessing_enabled = st.checkbox("Enable Preprocessing", value=True)
        
        # Dependencies
        st.subheader("Dependencies (Optional)")
        dependencies_input = st.text_input("Dependent Job IDs (comma-separated)")
        dependencies = [dep.strip() for dep in dependencies_input.split(",")] if dependencies_input else []
        
        # Submit button
        submitted = st.form_submit_button("Create Job", type="primary")
        
        if submitted:
            if not all([tenant_id, video_id, video_path]):
                st.error("Please fill in all required fields")
            else:
                config = {
                    'sampling_interval': sampling_interval,
                    'max_frames': max_frames,
                    'ocr_engines': ocr_engines,
                    'confidence_threshold': confidence_threshold,
                    'languages': languages,
                    'preprocessing_enabled': preprocessing_enabled
                }
                
                try:
                    job = job_manager.create_job(
                        tenant_id=tenant_id,
                        video_id=video_id,
                        video_path=video_path,
                        config=config,
                        priority=JobPriority(priority),
                        scheduled_at=scheduled_at,
                        tags=tags,
                        dependencies=dependencies,
                        webhook_url=webhook_url if webhook_url else None
                    )
                    
                    st.success(f"Job created successfully! Job ID: {job.job_id}")
                    
                    # Show job details
                    with st.expander("Job Details"):
                        st.json({
                            'job_id': job.job_id,
                            'status': job.status.value,
                            'priority': job.priority.value,
                            'cost_estimate': job.metrics.cost_estimate,
                            'config': config
                        })
                
                except Exception as e:
                    st.error(f"Failed to create job: {e}")

def show_analytics():
    """Analytics and reporting interface"""
    st.header("📈 Analytics & Reporting")
    
    job_manager = st.session_state.job_manager
    tenant_id = st.session_state.selected_tenant
    
    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", value=datetime.now())
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Get analytics data
    cost_analytics = job_manager.get_cost_analytics(tenant_id, start_datetime, end_datetime)
    stats = job_manager.get_job_statistics(tenant_id)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Cost", f"${cost_analytics['total_cost']:.2f}")
    
    with col2:
        st.metric("Jobs Processed", cost_analytics['job_count'])
    
    with col3:
        st.metric("Avg Processing Time", f"{cost_analytics['avg_processing_time']:.1f}s")
    
    with col4:
        st.metric("Cost per Job", f"${cost_analytics['cost_per_job']:.3f}")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Job Status Distribution")
        if stats['status_counts']:
            fig = px.bar(
                x=list(stats['status_counts'].keys()),
                y=list(stats['status_counts'].values()),
                title="Jobs by Status"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Success Rate Trend")
        # Simulate trend data
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        success_rates = [0.85 + 0.1 * (i % 7) / 7 for i in range(len(dates))]
        
        fig = px.line(
            x=dates,
            y=success_rates,
            title="Daily Success Rate",
            labels={'x': 'Date', 'y': 'Success Rate'}
        )
        fig.update_yaxis(tickformat='.1%')
        st.plotly_chart(fig, use_container_width=True)
    
    # Cost breakdown
    st.subheader("Cost Breakdown")
    
    # Simulate cost breakdown data
    cost_breakdown = {
        'OCR Processing': cost_analytics['total_cost'] * 0.6,
        'Frame Extraction': cost_analytics['total_cost'] * 0.2,
        'Storage': cost_analytics['total_cost'] * 0.1,
        'Compute': cost_analytics['total_cost'] * 0.1
    }
    
    fig = px.pie(
        values=list(cost_breakdown.values()),
        names=list(cost_breakdown.keys()),
        title="Cost Distribution by Component"
    )
    st.plotly_chart(fig, use_container_width=True)

def show_resource_management():
    """Resource allocation and management"""
    st.header("⚙️ Resource Management")
    
    job_manager = st.session_state.job_manager
    
    # Current allocations
    st.subheader("Tenant Resource Allocations")
    
    # Create/Edit allocation form
    with st.expander("Create/Edit Resource Allocation"):
        with st.form("resource_allocation_form"):
            tenant_id = st.text_input("Tenant ID")
            
            col1, col2 = st.columns(2)
            
            with col1:
                max_concurrent_jobs = st.number_input("Max Concurrent Jobs", min_value=1, value=5)
                cpu_limit = st.number_input("CPU Limit (cores)", min_value=0.1, value=1.0, step=0.1)
                memory_limit = st.number_input("Memory Limit (MB)", min_value=512, value=2048, step=256)
            
            with col2:
                gpu_allocation = st.number_input("GPU Allocation (fraction)", min_value=0.0, max_value=1.0, value=0.0, step=0.1)
                priority_weight = st.number_input("Priority Weight", min_value=0.1, value=1.0, step=0.1)
                cost_budget = st.number_input("Monthly Budget ($)", min_value=0.0, value=100.0)
            
            if st.form_submit_button("Save Allocation"):
                if tenant_id:
                    allocation = ResourceAllocation(
                        tenant_id=tenant_id,
                        max_concurrent_jobs=max_concurrent_jobs,
                        cpu_limit=cpu_limit,
                        memory_limit=memory_limit,
                        gpu_allocation=gpu_allocation,
                        priority_weight=priority_weight,
                        cost_budget=cost_budget
                    )
                    
                    job_manager.set_tenant_allocation(allocation)
                    st.success(f"Resource allocation saved for tenant {tenant_id}")
                else:
                    st.error("Please enter a tenant ID")
    
    # Resource utilization
    st.subheader("Resource Utilization")
    
    # Simulate resource utilization data
    utilization_data = {
        'CPU Usage': 65,
        'Memory Usage': 78,
        'GPU Usage': 45,
        'Storage Usage': 82
    }
    
    col1, col2, col3, col4 = st.columns(4)
    
    for i, (resource, usage) in enumerate(utilization_data.items()):
        with [col1, col2, col3, col4][i]:
            st.metric(
                resource,
                f"{usage}%",
                delta=f"{usage - 70}%" if usage != 70 else None
            )
    
    # Processing mode optimization
    st.subheader("Processing Mode Optimization")
    
    current_mode = st.selectbox(
        "Processing Mode",
        [mode.value for mode in ProcessingMode],
        index=1  # Default to BALANCED
    )
    
    if st.button("Apply Processing Mode"):
        job_manager.optimize_scheduling(ProcessingMode(current_mode))
        st.success(f"Applied {current_mode} processing mode")

def show_system_settings():
    """System configuration and settings"""
    st.header("🔧 System Settings")
    
    job_manager = st.session_state.job_manager
    
    # Retry configuration
    st.subheader("Retry Configuration")
    
    with st.form("retry_config_form"):
        tenant_id = st.text_input("Tenant ID (leave empty for default)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            max_attempts = st.number_input("Max Retry Attempts", min_value=1, value=3)
            base_delay = st.number_input("Base Delay (seconds)", min_value=0.1, value=1.0, step=0.1)
            max_delay = st.number_input("Max Delay (seconds)", min_value=1.0, value=300.0)
        
        with col2:
            exponential_base = st.number_input("Exponential Base", min_value=1.1, value=2.0, step=0.1)
            circuit_breaker_threshold = st.number_input("Circuit Breaker Threshold", min_value=1, value=5)
            circuit_breaker_timeout = st.number_input("Circuit Breaker Timeout (seconds)", min_value=1.0, value=60.0)
        
        jitter = st.checkbox("Enable Jitter", value=True)
        
        if st.form_submit_button("Save Retry Configuration"):
            retry_config = RetryConfig(
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay,
                exponential_base=exponential_base,
                jitter=jitter,
                circuit_breaker_threshold=circuit_breaker_threshold,
                circuit_breaker_timeout=circuit_breaker_timeout
            )
            
            if tenant_id:
                job_manager.set_retry_config(tenant_id, retry_config)
                st.success(f"Retry configuration saved for tenant {tenant_id}")
            else:
                job_manager.default_retry_config = retry_config
                st.success("Default retry configuration updated")
    
    # Data retention
    st.subheader("Data Retention")
    
    retention_days = st.number_input("Retention Period (days)", min_value=1, value=30)
    
    if st.button("Clean Up Old Jobs"):
        deleted_count = job_manager.cleanup_old_jobs(retention_days)
        st.success(f"Cleaned up {deleted_count} old jobs")
    
    # System maintenance
    st.subheader("System Maintenance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Restart Scheduler"):
            job_manager.stop_scheduler()
            job_manager.start_scheduler()
            st.success("Scheduler restarted")
    
    with col2:
        if st.button("🛑 Shutdown System"):
            if st.checkbox("Confirm shutdown"):
                job_manager.shutdown()
                st.success("System shutdown initiated")

def show_monitoring():
    """System monitoring and health dashboard"""
    st.header("📊 System Monitoring")
    
    job_manager = st.session_state.job_manager
    
    # System health status
    st.subheader("System Health")
    
    # Get current statistics
    stats = job_manager.get_job_statistics()
    
    # Health indicators
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        queue_size = stats['queue_size']
        queue_health = "🟢" if queue_size < 10 else "🟡" if queue_size < 50 else "🔴"
        st.metric("Queue Health", f"{queue_health} {queue_size} jobs")
    
    with col2:
        running_jobs = stats['running_jobs']
        capacity_health = "🟢" if running_jobs < 8 else "🟡" if running_jobs < 15 else "🔴"
        st.metric("Capacity", f"{capacity_health} {running_jobs}/20")
    
    with col3:
        success_rate = stats['success_rate']
        success_health = "🟢" if success_rate > 0.9 else "🟡" if success_rate > 0.8 else "🔴"
        st.metric("Success Rate", f"{success_health} {success_rate:.1%}")
    
    with col4:
        # Simulate system uptime
        uptime_hours = 72.5
        uptime_health = "🟢" if uptime_hours > 24 else "🟡"
        st.metric("Uptime", f"{uptime_health} {uptime_hours:.1f}h")
    
    # Real-time metrics
    st.subheader("Real-time Metrics")
    
    # Create placeholder for real-time updates
    metrics_placeholder = st.empty()
    
    with metrics_placeholder.container():
        # Simulate real-time data
        import random
        
        # CPU and Memory usage over time
        timestamps = pd.date_range(
            start=datetime.now() - timedelta(hours=1),
            end=datetime.now(),
            freq='5min'
        )
        
        cpu_usage = [50 + 20 * random.random() for _ in timestamps]
        memory_usage = [60 + 15 * random.random() for _ in timestamps]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=timestamps, y=cpu_usage, name='CPU Usage (%)', line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=timestamps, y=memory_usage, name='Memory Usage (%)', line=dict(color='red')))
        
        fig.update_layout(
            title="System Resource Usage (Last Hour)",
            xaxis_title="Time",
            yaxis_title="Usage (%)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Alert log
    st.subheader("Recent Alerts")
    
    # Simulate alert data
    alerts = [
        {"timestamp": datetime.now() - timedelta(minutes=15), "level": "WARNING", "message": "High queue size detected"},
        {"timestamp": datetime.now() - timedelta(hours=2), "level": "INFO", "message": "Scheduled maintenance completed"},
        {"timestamp": datetime.now() - timedelta(hours=6), "level": "ERROR", "message": "Job processing failure rate exceeded threshold"},
    ]
    
    for alert in alerts:
        level_color = {"ERROR": "🔴", "WARNING": "🟡", "INFO": "🔵"}[alert["level"]]
        st.write(f"{level_color} **{alert['level']}** - {alert['timestamp'].strftime('%Y-%m-%d %H:%M')} - {alert['message']}")

if __name__ == "__main__":
    main()
