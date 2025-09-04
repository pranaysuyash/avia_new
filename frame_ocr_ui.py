#!/usr/bin/env python3
"""
Frame OCR System UI
Streamlit interface for Frame OCR processing and search
"""

import streamlit as st
import asyncio
import tempfile
import os
from datetime import datetime
from typing import List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_intent_utils import render_share_inline, render_share_block, log_ux_event

# Import Frame OCR components
try:
    from frame_ocr_pipeline import FrameOCRPipeline
    from frame_ocr_models import (
        FrameOCRJob, JobStatus, OCRJobConfig, SamplingStrategy, OCREngine
    )
    FRAME_OCR_AVAILABLE = True
except ImportError:
    FRAME_OCR_AVAILABLE = False
    st.warning("Frame OCR components not available")

# Configure page
st.set_page_config(
    page_title="Frame OCR System",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state
if 'pipeline' not in st.session_state:
    if FRAME_OCR_AVAILABLE:
        st.session_state.pipeline = FrameOCRPipeline()
    else:
        st.session_state.pipeline = None

if 'jobs' not in st.session_state:
    st.session_state.jobs = []

if 'selected_job' not in st.session_state:
    st.session_state.selected_job = None


def main():
    """Main Streamlit application"""
    st.title("🔍 Frame OCR System")
    st.markdown("""
    Extract text from video frames and make videos searchable by their visual content.
    Upload a video to start processing and enable search within frames that lack transcripts.
    """)
    # Inline share link for this view
    try:
        render_share_inline("Shareable view link")
    except Exception:
        pass
    # Sidebar share + reset controls
    with st.sidebar:
        try:
            render_share_block("Share Frame OCR View")
        except Exception:
            pass
        if st.button("Reset View/Filters"):
            try:
                # Clear all query params
                st.experimental_set_query_params()
            except Exception:
                pass
            try:
                log_ux_event("st_filters_cleared", {"scope": "frame_ocr"})
            except Exception:
                pass
            st.rerun()
    
    if not FRAME_OCR_AVAILABLE:
        st.error("Frame OCR system is not available. Please check dependencies.")
        return
    
    # Deep-linked tabs via fo_tab (process|jobs|search|analytics)
    params = get_params()
    tab_map = [
        ("process", "📤 Process Video"),
        ("jobs", "📋 Job Status"),
        ("search", "🔍 Search Results"),
        ("analytics", "📊 Analytics"),
    ]
    current_key = params.get('fo_tab', 'process')
    ordered = [x for x in tab_map if x[0] == current_key] + [x for x in tab_map if x[0] != current_key]
    tab_labels = [label for _, label in ordered]
    tabs = st.tabs(tab_labels)
    key_to_tab = {k: tabs[i] for i, (k, _) in enumerate(ordered)}

    with key_to_tab["process"]:
        process_video_tab()
    
    with key_to_tab["jobs"]:
        try:
            from streamlit_intent_utils import render_skeleton_list
            ph = st.container()
            with ph:
                render_skeleton_list(items=3)
        except Exception:
            ph = None
        job_status_tab()
        if ph:
            ph.empty()
    
    with key_to_tab["search"]:
        try:
            from streamlit_intent_utils import render_skeleton_list
            ph2 = st.container()
            with ph2:
                render_skeleton_list(items=3)
        except Exception:
            ph2 = None
        search_results_tab()
        if ph2:
            ph2.empty()
    
    with key_to_tab["analytics"]:
        try:
            from streamlit_intent_utils import render_skeleton_list
            ph3 = st.container()
            with ph3:
                render_skeleton_list(items=3)
        except Exception:
            ph3 = None
        analytics_tab()
        if ph3:
            ph3.empty()

    # Sidebar quick section selector synced with fo_tab
    with st.sidebar:
        st.markdown("---")
        sel = st.selectbox(
            "Section",
            options=[k for k, _ in tab_map],
            index=[k for k, _ in tab_map].index(current_key) if current_key in [k for k, _ in tab_map] else 0,
            format_func=lambda k: dict(tab_map)[k]
        )
        if sel != current_key:
            try:
                update_params({'fo_tab': sel})
            except Exception:
                pass
            st.experimental_rerun()


def process_video_tab():
    """Tab for uploading and processing videos"""
    st.header("Upload Video for Frame OCR Processing")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a video file",
        type=["mp4", "avi", "mov", "wmv", "flv", "webm", "mkv"],
        key="video_uploader"
    )
    
    if uploaded_file is not None:
        st.success(f"Selected file: {uploaded_file.name}")
        
        # Processing configuration
        st.subheader("Processing Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            sampling_strategy = st.selectbox(
                "Sampling Strategy",
                options=[strategy.value for strategy in SamplingStrategy],
                index=4,  # Adaptive
                help="Strategy for selecting frames to process"
            )
            
            sampling_interval = st.number_input(
                "Sampling Interval (seconds)",
                min_value=0.1,
                max_value=60.0,
                value=2.0,
                step=0.5,
                help="Interval between frames (for time-based sampling)"
            )
            
            max_frames = st.number_input(
                "Maximum Frames",
                min_value=1,
                max_value=10000,
                value=100,
                help="Maximum number of frames to process"
            )
            
            quality_threshold = st.slider(
                "Quality Threshold",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="Minimum frame quality for processing"
            )
        
        with col2:
            ocr_engine = st.selectbox(
                "OCR Engine",
                options=[engine.value for engine in OCREngine],
                index=0,  # Tesseract
                help="OCR engine to use for text extraction"
            )
            
            languages = st.multiselect(
                "Languages",
                options=["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"],
                default=["en"],
                help="Languages to detect in frames"
            )
            
            preprocess = st.checkbox(
                "Enable Preprocessing",
                value=True,
                help="Apply image preprocessing to improve OCR accuracy"
            )
            
            confidence_threshold = st.slider(
                "Confidence Threshold",
                min_value=0.0,
                max_value=1.0,
                value=0.8,
                step=0.1,
                help="Minimum confidence for text recognition"
            )
        
        enable_spell_check = st.checkbox(
            "Enable Spell Check",
            value=True,
            help="Apply spell checking and correction to extracted text"
        )
        
        enable_gpu_acceleration = st.checkbox(
            "Enable GPU Acceleration",
            value=False,
            help="Use GPU for processing (if available)"
        )
        
        # Process button
        if st.button("🚀 Start Processing", type="primary", use_container_width=True):
            with st.spinner("Processing video..."):
                try:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
                        temp_file.write(uploaded_file.getvalue())
                        temp_file_path = temp_file.name
                    
                    # Create job configuration
                    job_config = OCRJobConfig(
                        sampling_strategy=SamplingStrategy(sampling_strategy),
                        sampling_interval=sampling_interval,
                        max_frames=max_frames,
                        quality_threshold=quality_threshold,
                        ocr_engine=OCREngine(ocr_engine),
                        languages=languages,
                        preprocess=preprocess,
                        confidence_threshold=confidence_threshold,
                        enable_spell_check=enable_spell_check,
                        enable_gpu_acceleration=enable_gpu_acceleration
                    )
                    
                    # Process video
                    job_id = asyncio.run(
                        st.session_state.pipeline.process_video(temp_file_path, job_config)
                    )
                    
                    st.success(f"✅ Processing started! Job ID: {job_id}")
                    st.info("Check the 'Job Status' tab to monitor progress.")
                    
                    # Clean up temporary file
                    os.unlink(temp_file_path)
                    
                except Exception as e:
                    st.error(f"❌ Error processing video: {str(e)}")


def job_status_tab():
    """Tab for viewing job status and monitoring"""
    st.header("Job Status and Monitoring")
    
    # Refresh button
    if st.button("🔄 Refresh Status", key="refresh_jobs"):
        # In a real implementation, this would fetch current job status
        pass
    
    # Display jobs table
    if st.session_state.jobs:
        jobs_df = pd.DataFrame([
            {
                "Job ID": job.job_id,
                "Status": job.status.value,
                "Progress": f"{job.progress}%",
                "Video": job.video_path.split("/")[-1],
                "Created": job.created_at.strftime("%Y-%m-%d %H:%M"),
                "Updated": job.updated_at.strftime("%Y-%m-%d %H:%M")
            }
            for job in st.session_state.jobs
        ])
        
        st.dataframe(jobs_df, use_container_width=True)
        
        # Job details
        selected_job_id = st.selectbox(
            "Select Job for Details",
            options=[job.job_id for job in st.session_state.jobs],
            key="job_details_selector"
        )
        
        if selected_job_id:
            job = next((j for j in st.session_state.jobs if j.job_id == selected_job_id), None)
            if job:
                st.subheader(f"Job Details: {job.job_id}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Status", job.status.value)
                    st.metric("Progress", f"{job.progress}%")
                
                with col2:
                    st.metric("Frames Processed", getattr(job, 'frames_processed', 'N/A'))
                    st.metric("Results Indexed", getattr(job, 'results_indexed', 'N/A'))
                
                with col3:
                    st.metric("Created", job.created_at.strftime("%Y-%m-%d"))
                    st.metric("Last Update", job.updated_at.strftime("%H:%M:%S"))
                
                if job.message:
                    st.info(f"Message: {job.message}")
                
                # Progress bar
                st.progress(job.progress / 100)
                
                # Cancel button for active jobs
                if job.status in [JobStatus.PENDING, JobStatus.QUEUED, JobStatus.PROCESSING]:
                    if st.button("⏹️ Cancel Job", key=f"cancel_{job.job_id}"):
                        st.warning("Cancellation requested (simulated)")
    else:
        st.info("No processing jobs found. Upload a video to get started.")


def search_results_tab():
    """Tab for searching OCR results"""
    st.header("Search OCR Results")
    
    # Search form
    with st.form("search_form"):
        query = st.text_input(
            "Search Query",
            placeholder="Enter text to search for in video frames...",
            help="Search for specific text extracted from video frames"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            job_filter = st.selectbox(
                "Filter by Job",
                options=["All Jobs"] + [job.job_id for job in st.session_state.jobs],
                index=0
            )
            
            min_confidence = st.slider(
                "Minimum Confidence",
                min_value=0.0,
                max_value=1.0,
                value=0.0,
                step=0.1
            )
        
        with col2:
            language_filter = st.selectbox(
                "Language Filter",
                options=["All Languages", "en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"],
                index=0
            )
            
            result_limit = st.number_input(
                "Results Limit",
                min_value=1,
                max_value=1000,
                value=50
            )
        
        search_submitted = st.form_submit_button("🔍 Search")
    
    if search_submitted and query:
        with st.spinner("Searching..."):
            try:
                # In a real implementation, this would search OCR results
                # For now, we'll show a simulated result
                st.success(f"Search completed for '{query}'")
                
                # Simulated results
                results_data = [
                    {
                        "Text": f"This is a sample result for '{query}' found in frame 123",
                        "Timestamp": "00:02:03",
                        "Frame": 123,
                        "Confidence": 0.95,
                        "Job ID": "job_12345"
                    },
                    {
                        "Text": f"Another occurrence of '{query}' in frame 456",
                        "Timestamp": "00:07:45",
                        "Frame": 456,
                        "Confidence": 0.87,
                        "Job ID": "job_12345"
                    }
                ]
                
                results_df = pd.DataFrame(results_data)
                st.dataframe(results_df, use_container_width=True)
                
                # Jump to video button
                if not results_df.empty:
                    st.button("🎬 Jump to First Result", type="primary")
                
            except Exception as e:
                st.error(f"Error searching: {str(e)}")
    elif search_submitted:
        st.warning("Please enter a search query.")


def analytics_tab():
    """Tab for analytics and insights"""
    st.header("Analytics and Insights")
    
    # Simulated analytics data
    st.subheader("Processing Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Jobs", "24", "↗️ 12%")
    
    with col2:
        st.metric("Successful Jobs", "21", "↗️ 8%")
    
    with col3:
        st.metric("Avg. Processing Time", "12m 34s", "↘️ 2m 15s")
    
    with col4:
        st.metric("Total Frames Processed", "12,456", "↗️ 3,245")
    
    # Processing time chart
    st.subheader("Processing Time Trends")
    
    # Simulated data
    import numpy as np
    dates = pd.date_range(start="2024-01-01", periods=30, freq='D')
    processing_times = np.random.normal(12, 3, 30)  # Mean 12 minutes, std 3 minutes
    
    df = pd.DataFrame({
        'Date': dates,
        'Processing Time (minutes)': processing_times
    })
    
    fig = px.line(df, x='Date', y='Processing Time (minutes)', 
                  title='Daily Processing Time Trend')
    fig.update_layout(yaxis_title="Minutes")
    st.plotly_chart(fig, use_container_width=True)
    
    # Success rate chart
    st.subheader("Job Success Rate")
    
    success_rates = np.random.normal(85, 5, 30)  # Mean 85% success rate
    df['Success Rate (%)'] = success_rates
    
    fig2 = px.bar(df.tail(10), x='Date', y='Success Rate (%)',
                  title='Recent Job Success Rates')
    fig2.update_layout(yaxis_title="Percentage (%)")
    st.plotly_chart(fig2, use_container_width=True)
    
    # Performance metrics
    st.subheader("Performance Metrics")
    
    metrics_col1, metrics_col2 = st.columns(2)
    
    with metrics_col1:
        st.metric("Avg. OCR Accuracy", "92%", "↗️ 3%")
        st.metric("Avg. Frame Quality", "87%", "↗️ 2%")
        st.metric("GPU Utilization", "65%", "↘️ 5%")
    
    with metrics_col2:
        st.metric("Storage Usage", "24.5 GB", "↗️ 2.1 GB")
        st.metric("API Requests", "1,243", "↗️ 342")
        st.metric("Errors Today", "12", "↘️ 3")


if __name__ == "__main__":
    main()
