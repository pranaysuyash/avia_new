"""
Advanced Video Processing Engine UI
Task 3: Advanced Media Processing Pipeline

Streamlit interface for advanced video processing with scene detection,
keyframe extraction, object recognition, and intelligent B-roll suggestions.
"""

import streamlit as st
import requests
import json
import time
import os
from typing import Dict, List, Any, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import tempfile
import uuid

# Configure page
st.set_page_config(
    page_title="Advanced Video Processing Engine",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
API_BASE_URL = "http://localhost:8000/api/v1/video"
SUPPORTED_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v']

def main():
    """Main Streamlit application"""
    st.title("🎬 Advanced Video Processing Engine")
    st.markdown("**Task 3: Advanced Media Processing Pipeline**")
    st.markdown("---")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Processing Configuration")
        
        # Processing options
        extract_keyframes = st.checkbox("Extract Keyframes", value=True, 
                                      help="Extract important frames for analysis")
        detect_scenes = st.checkbox("Detect Scenes", value=True,
                                  help="Automatically detect scene changes")
        detect_objects = st.checkbox("Detect Objects", value=True,
                                   help="Identify objects, faces, and elements")
        suggest_broll = st.checkbox("B-roll Suggestions", value=True,
                                  help="Generate intelligent B-roll recommendations")
        enhance_quality = st.checkbox("Enhance Quality", value=False,
                                    help="Apply video quality enhancements (slower)")
        
        # Processing strategy
        processing_strategy = st.selectbox(
            "Processing Strategy",
            ["auto", "basic", "enhanced", "professional", "enterprise"],
            index=0,
            help="Select processing complexity level"
        )
        
        st.markdown("---")
        
        # Quick actions
        st.header("🚀 Quick Actions")
        if st.button("📊 View Processing Jobs", use_container_width=True):
            st.session_state.show_jobs = True
        
        if st.button("🔍 Health Check", use_container_width=True):
            check_api_health()
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📤 Upload & Process", 
        "📊 Results Dashboard", 
        "🎯 Scene Analysis", 
        "🎬 B-roll Suggestions",
        "📈 Processing Jobs"
    ])
    
    with tab1:
        upload_and_process_tab(
            extract_keyframes, detect_scenes, detect_objects, 
            suggest_broll, enhance_quality, processing_strategy
        )
    
    with tab2:
        results_dashboard_tab()
    
    with tab3:
        scene_analysis_tab()
    
    with tab4:
        broll_suggestions_tab()
    
    with tab5:
        processing_jobs_tab()

def upload_and_process_tab(extract_keyframes: bool, detect_scenes: bool, 
                          detect_objects: bool, suggest_broll: bool, 
                          enhance_quality: bool, processing_strategy: str):
    """Upload and process video tab"""
    st.header("📤 Video Upload & Processing")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a video file",
        type=['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v'],
        help="Upload a video file for advanced processing"
    )
    
    if uploaded_file is not None:
        # Display file info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("File Name", uploaded_file.name)
        with col2:
            st.metric("File Size", f"{uploaded_file.size / (1024*1024):.1f} MB")
        with col3:
            st.metric("File Type", uploaded_file.type)
        
        # Processing options summary
        st.subheader("🔧 Processing Configuration")
        options_df = pd.DataFrame({
            'Option': ['Extract Keyframes', 'Detect Scenes', 'Detect Objects', 
                      'B-roll Suggestions', 'Enhance Quality'],
            'Enabled': [extract_keyframes, detect_scenes, detect_objects, 
                       suggest_broll, enhance_quality],
            'Description': [
                'Extract important frames for thumbnails and analysis',
                'Automatically detect scene changes and transitions',
                'Identify objects, faces, and elements in video',
                'Generate intelligent B-roll placement suggestions',
                'Apply video quality enhancements and upscaling'
            ]
        })
        
        st.dataframe(options_df, use_container_width=True)
        
        # Process button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Start Advanced Processing", 
                        type="primary", use_container_width=True):
                process_video(
                    uploaded_file, extract_keyframes, detect_scenes, 
                    detect_objects, suggest_broll, enhance_quality, 
                    processing_strategy
                )
    
    # Quick metadata extraction
    st.markdown("---")
    st.subheader("⚡ Quick Metadata Extraction")
    st.markdown("Extract basic video information without full processing")
    
    metadata_file = st.file_uploader(
        "Choose a video file for metadata",
        type=['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v'],
        key="metadata_upload"
    )
    
    if metadata_file is not None:
        if st.button("📋 Extract Metadata", use_container_width=True):
            extract_metadata(metadata_file)

def process_video(uploaded_file, extract_keyframes: bool, detect_scenes: bool,
                 detect_objects: bool, suggest_broll: bool, enhance_quality: bool,
                 processing_strategy: str):
    """Process video with advanced analysis"""
    try:
        with st.spinner("🎬 Starting advanced video processing..."):
            # Prepare form data
            files = {"video": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            data = {
                "extract_keyframes": extract_keyframes,
                "detect_scenes": detect_scenes,
                "detect_objects": detect_objects,
                "suggest_broll": suggest_broll,
                "enhance_quality": enhance_quality
            }
            
            if processing_strategy != "auto":
                data["processing_strategy"] = processing_strategy
            
            # Submit processing request
            response = requests.post(f"{API_BASE_URL}/process", files=files, data=data)
            
            if response.status_code == 202:
                result = response.json()
                job_id = result["job_id"]
                
                st.success(f"✅ Processing started! Job ID: {job_id}")
                st.session_state.current_job_id = job_id
                
                # Show progress tracking
                track_processing_progress(job_id)
                
            else:
                st.error(f"❌ Processing failed: {response.text}")
                
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def track_processing_progress(job_id: str):
    """Track processing progress with real-time updates"""
    progress_container = st.container()
    status_container = st.container()
    
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    # Poll for status updates
    max_attempts = 300  # 5 minutes max
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get(f"{API_BASE_URL}/status/{job_id}")
            
            if response.status_code == 200:
                status = response.json()
                
                # Update progress
                progress_bar.progress(status["progress"])
                status_text.text(f"Status: {status['status']} - {status['message']}")
                
                if status["status"] == "completed":
                    st.success("🎉 Processing completed successfully!")
                    
                    # Store result in session state
                    result_response = requests.get(f"{API_BASE_URL}/result/{job_id}")
                    if result_response.status_code == 200:
                        st.session_state.processing_result = result_response.json()
                        st.session_state.show_results = True
                        st.rerun()
                    break
                    
                elif status["status"] == "failed":
                    st.error(f"❌ Processing failed: {status['message']}")
                    break
                
                # Wait before next poll
                time.sleep(2)
                attempt += 1
                
            else:
                st.error(f"❌ Failed to get status: {response.text}")
                break
                
        except Exception as e:
            st.error(f"❌ Status check error: {str(e)}")
            break
    
    if attempt >= max_attempts:
        st.warning("⏰ Processing is taking longer than expected. Check the Processing Jobs tab for updates.")

def extract_metadata(uploaded_file):
    """Extract video metadata"""
    try:
        with st.spinner("📋 Extracting metadata..."):
            files = {"video": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            response = requests.post(f"{API_BASE_URL}/metadata", files=files)
            
            if response.status_code == 200:
                metadata = response.json()
                
                st.success("✅ Metadata extracted successfully!")
                
                # Display metadata in columns
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Duration", f"{metadata['duration']:.1f}s")
                    st.metric("Resolution", f"{metadata['width']}x{metadata['height']}")
                    st.metric("Aspect Ratio", metadata['aspect_ratio'])
                
                with col2:
                    st.metric("FPS", f"{metadata['fps']:.2f}")
                    st.metric("Codec", metadata['codec'])
                    st.metric("File Size", f"{metadata['file_size'] / (1024*1024):.1f} MB")
                
                with col3:
                    st.metric("Quality Score", f"{metadata['quality_score']:.2f}")
                    st.metric("Complexity Score", f"{metadata['complexity_score']:.2f}")
                    st.metric("Has Audio", "Yes" if metadata['has_audio'] else "No")
                
                # Additional details
                with st.expander("📊 Detailed Metadata"):
                    st.json(metadata)
                    
            else:
                st.error(f"❌ Metadata extraction failed: {response.text}")
                
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def results_dashboard_tab():
    """Results dashboard tab"""
    st.header("📊 Processing Results Dashboard")
    
    if 'processing_result' not in st.session_state:
        st.info("🎬 No processing results available. Upload and process a video first.")
        return
    
    result = st.session_state.processing_result
    
    # Summary metrics
    st.subheader("📈 Processing Summary")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Processing Time", f"{result['processing_time']:.1f}s")
    with col2:
        st.metric("Keyframes", len(result['keyframes']))
    with col3:
        st.metric("Scenes", len(result['scenes']))
    with col4:
        st.metric("Objects", len(result['objects']))
    with col5:
        st.metric("B-roll Ideas", len(result['broll_suggestions']))
    
    # Video metadata
    st.subheader("🎥 Video Information")
    metadata = result['metadata']
    
    col1, col2 = st.columns(2)
    with col1:
        metadata_df = pd.DataFrame({
            'Property': ['Duration', 'Resolution', 'FPS', 'Codec', 'File Size'],
            'Value': [
                f"{metadata['duration']:.1f}s",
                f"{metadata['width']}x{metadata['height']}",
                f"{metadata['fps']:.2f}",
                metadata['codec'],
                f"{metadata['file_size'] / (1024*1024):.1f} MB"
            ]
        })
        st.dataframe(metadata_df, use_container_width=True)
    
    with col2:
        quality_df = pd.DataFrame({
            'Metric': ['Quality Score', 'Complexity Score', 'Aspect Ratio', 'Has Audio'],
            'Value': [
                f"{metadata['quality_score']:.2f}",
                f"{metadata['complexity_score']:.2f}",
                metadata['aspect_ratio'],
                "Yes" if metadata['has_audio'] else "No"
            ]
        })
        st.dataframe(quality_df, use_container_width=True)
    
    # Processing strategy
    st.info(f"🎯 Processing Strategy Used: **{result['processing_strategy'].title()}**")
    
    # Errors (if any)
    if result.get('errors'):
        st.warning("⚠️ Processing Warnings:")
        for error in result['errors']:
            st.text(f"• {error}")

def scene_analysis_tab():
    """Scene analysis tab"""
    st.header("🎯 Scene Analysis")
    
    if 'processing_result' not in st.session_state:
        st.info("🎬 No scene analysis available. Process a video first.")
        return
    
    result = st.session_state.processing_result
    scenes = result.get('scenes', [])
    
    if not scenes:
        st.warning("🎬 No scenes detected in the processed video.")
        return
    
    st.subheader(f"📊 Detected {len(scenes)} Scenes")
    
    # Scene timeline visualization
    scene_data = []
    for i, scene in enumerate(scenes):
        scene_data.append({
            'Scene': f"Scene {i+1}",
            'Start': scene['start_time'],
            'End': scene['end_time'],
            'Duration': scene['end_time'] - scene['start_time'],
            'Type': scene['scene_type'],
            'Confidence': scene['confidence'],
            'Motion': scene['motion_intensity'],
            'Complexity': scene['visual_complexity']
        })
    
    scene_df = pd.DataFrame(scene_data)
    
    # Timeline chart
    fig = px.timeline(
        scene_df, 
        x_start="Start", 
        x_end="End", 
        y="Scene",
        color="Type",
        title="Scene Timeline",
        hover_data=['Duration', 'Confidence', 'Motion', 'Complexity']
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Scene statistics
    col1, col2 = st.columns(2)
    
    with col1:
        # Scene type distribution
        type_counts = scene_df['Type'].value_counts()
        fig_pie = px.pie(
            values=type_counts.values, 
            names=type_counts.index,
            title="Scene Type Distribution"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Motion intensity distribution
        fig_hist = px.histogram(
            scene_df, 
            x="Motion", 
            title="Motion Intensity Distribution",
            nbins=10
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    
    # Detailed scene table
    st.subheader("📋 Scene Details")
    
    # Add selection for detailed view
    selected_scene = st.selectbox(
        "Select scene for details:",
        options=range(len(scenes)),
        format_func=lambda x: f"Scene {x+1} ({scenes[x]['start_time']:.1f}s - {scenes[x]['end_time']:.1f}s)"
    )
    
    if selected_scene is not None:
        scene = scenes[selected_scene]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Duration", f"{scene['end_time'] - scene['start_time']:.1f}s")
            st.metric("Scene Type", scene['scene_type'])
        with col2:
            st.metric("Confidence", f"{scene['confidence']:.2f}")
            st.metric("Motion Intensity", f"{scene['motion_intensity']:.2f}")
        with col3:
            st.metric("Visual Complexity", f"{scene['visual_complexity']:.2f}")
            st.metric("Frame Range", f"{scene['start_frame']} - {scene['end_frame']}")
        
        if scene.get('description'):
            st.text_area("Description", scene['description'], disabled=True)

def broll_suggestions_tab():
    """B-roll suggestions tab"""
    st.header("🎬 B-roll Suggestions")
    
    if 'processing_result' not in st.session_state:
        st.info("🎬 No B-roll suggestions available. Process a video first.")
        return
    
    result = st.session_state.processing_result
    suggestions = result.get('broll_suggestions', [])
    
    if not suggestions:
        st.warning("🎬 No B-roll suggestions generated for this video.")
        return
    
    st.subheader(f"💡 {len(suggestions)} Intelligent Suggestions")
    
    # Priority filter
    priorities = sorted(list(set(s['priority'] for s in suggestions)))
    selected_priority = st.selectbox(
        "Filter by Priority:",
        options=['All'] + [f"Priority {p}" for p in priorities],
        index=0
    )
    
    # Filter suggestions
    filtered_suggestions = suggestions
    if selected_priority != 'All':
        priority_num = int(selected_priority.split()[-1])
        filtered_suggestions = [s for s in suggestions if s['priority'] == priority_num]
    
    # Suggestions timeline
    if filtered_suggestions:
        suggestion_data = []
        for i, suggestion in enumerate(filtered_suggestions):
            suggestion_data.append({
                'Suggestion': f"Suggestion {i+1}",
                'Timestamp': suggestion['timestamp'],
                'Duration': suggestion['duration'],
                'Type': suggestion['suggestion_type'],
                'Confidence': suggestion['confidence'],
                'Priority': suggestion['priority']
            })
        
        suggestion_df = pd.DataFrame(suggestion_data)
        
        # Timeline visualization
        fig = px.scatter(
            suggestion_df,
            x="Timestamp",
            y="Type",
            size="Duration",
            color="Priority",
            hover_data=['Confidence'],
            title="B-roll Suggestions Timeline"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed suggestions
    st.subheader("📝 Detailed Suggestions")
    
    for i, suggestion in enumerate(filtered_suggestions):
        with st.expander(f"💡 Suggestion {i+1}: {suggestion['suggestion_type'].replace('_', ' ').title()}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Timestamp", f"{suggestion['timestamp']:.1f}s")
                st.metric("Duration", f"{suggestion['duration']:.1f}s")
            
            with col2:
                st.metric("Confidence", f"{suggestion['confidence']:.2f}")
                st.metric("Priority", suggestion['priority'])
            
            with col3:
                st.metric("Type", suggestion['suggestion_type'].replace('_', ' ').title())
            
            st.text_area("Description", suggestion['description'], disabled=True, key=f"desc_{i}")
            
            if suggestion.get('keywords'):
                st.write("**Keywords:**", ", ".join(suggestion['keywords']))

def processing_jobs_tab():
    """Processing jobs management tab"""
    st.header("📈 Processing Jobs")
    
    try:
        response = requests.get(f"{API_BASE_URL}/jobs")
        
        if response.status_code == 200:
            jobs = response.json()
            
            if not jobs:
                st.info("📋 No processing jobs found.")
                return
            
            # Jobs summary
            st.subheader("📊 Jobs Summary")
            
            status_counts = {}
            for job in jobs:
                status = job['status']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Jobs", len(jobs))
            with col2:
                st.metric("Completed", status_counts.get('completed', 0))
            with col3:
                st.metric("Processing", status_counts.get('processing', 0))
            with col4:
                st.metric("Failed", status_counts.get('failed', 0))
            
            # Jobs table
            st.subheader("📋 Job Details")
            
            job_data = []
            for job in jobs:
                job_data.append({
                    'Job ID': job['job_id'][:8] + '...',
                    'Status': job['status'],
                    'Progress': f"{job['progress']:.1%}",
                    'Message': job['message'][:50] + '...' if len(job['message']) > 50 else job['message'],
                    'Started': job['started_at'],
                    'Completed': job.get('completed_at', 'N/A')
                })
            
            jobs_df = pd.DataFrame(job_data)
            st.dataframe(jobs_df, use_container_width=True)
            
            # Job management
            st.subheader("🔧 Job Management")
            
            job_ids = [job['job_id'] for job in jobs]
            selected_job = st.selectbox("Select job:", job_ids, format_func=lambda x: x[:8] + '...')
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔍 View Details", use_container_width=True):
                    view_job_details(selected_job)
            
            with col2:
                if st.button("📊 Get Result", use_container_width=True):
                    get_job_result(selected_job)
            
            with col3:
                if st.button("🗑️ Delete Job", use_container_width=True):
                    delete_job(selected_job)
        
        else:
            st.error(f"❌ Failed to fetch jobs: {response.text}")
            
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def view_job_details(job_id: str):
    """View detailed job information"""
    try:
        response = requests.get(f"{API_BASE_URL}/status/{job_id}")
        
        if response.status_code == 200:
            job = response.json()
            
            st.subheader(f"🔍 Job Details: {job_id[:8]}...")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Status", job['status'])
                st.metric("Progress", f"{job['progress']:.1%}")
                st.metric("Started", job['started_at'])
            
            with col2:
                st.metric("Message", job['message'])
                if job.get('completed_at'):
                    st.metric("Completed", job['completed_at'])
            
            st.json(job)
        
        else:
            st.error(f"❌ Failed to get job details: {response.text}")
            
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def get_job_result(job_id: str):
    """Get job result"""
    try:
        response = requests.get(f"{API_BASE_URL}/result/{job_id}")
        
        if response.status_code == 200:
            result = response.json()
            st.session_state.processing_result = result
            st.success("✅ Result loaded! Check the Results Dashboard tab.")
            
        else:
            st.error(f"❌ Failed to get result: {response.text}")
            
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def delete_job(job_id: str):
    """Delete a job"""
    try:
        response = requests.delete(f"{API_BASE_URL}/jobs/{job_id}")
        
        if response.status_code == 200:
            st.success("✅ Job deleted successfully!")
            st.rerun()
        else:
            st.error(f"❌ Failed to delete job: {response.text}")
            
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def check_api_health():
    """Check API health status"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        
        if response.status_code == 200:
            health = response.json()
            
            if health['status'] == 'healthy':
                st.success("✅ API is healthy and ready!")
            else:
                st.warning("⚠️ API is running but degraded")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Engine Available", "Yes" if health['engine_available'] else "No")
                st.metric("Active Jobs", health['active_jobs'])
            with col2:
                st.metric("Total Jobs", health['total_jobs'])
        
        else:
            st.error("❌ API is not responding")
            
    except Exception as e:
        st.error(f"❌ Cannot connect to API: {str(e)}")

if __name__ == "__main__":
    main()