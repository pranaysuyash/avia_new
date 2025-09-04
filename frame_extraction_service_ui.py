"""
Streamlit UI for Advanced Frame Extraction Service

This module provides a comprehensive web interface for configuring and running
frame extraction with real-time monitoring and visualization.
"""

import streamlit as st
import cv2
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import tempfile
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

from frame_extraction_service import (
    FrameExtractionService, ExtractionConfig, SamplingStrategy, 
    FrameQuality, ExtractedFrame, VideoMetadata
)


def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Advanced Frame Extraction Service",
        page_icon="🎬",
        layout="wide"
    )
    
    st.title("🎬 Advanced Frame Extraction Service")
    st.markdown("Extract frames from videos with intelligent sampling and quality assessment")
    
    # Initialize session state
    if 'extraction_results' not in st.session_state:
        st.session_state.extraction_results = None
    if 'video_metadata' not in st.session_state:
        st.session_state.video_metadata = None
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = None
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        config = configure_extraction()
        
        st.header("📊 Quick Stats")
        if st.session_state.video_metadata:
            display_video_stats(st.session_state.video_metadata)
    
    # Main content area
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.header("📁 Video Upload")
        uploaded_file = st.file_uploader(
            "Choose a video file",
            type=['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v'],
            help="Upload a video file for frame extraction"
        )
        
        if uploaded_file is not None:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                tmp_file.write(uploaded_file.read())
                video_path = tmp_file.name
            
            # Get video metadata
            try:
                service = FrameExtractionService()
                metadata = service.get_video_metadata(video_path)
                st.session_state.video_metadata = metadata
                
                st.success(f"Video loaded: {uploaded_file.name}")
                display_video_info(metadata)
                
                # Cost estimation
                cost_estimate = service.estimate_processing_cost(video_path, config)
                display_cost_estimate(cost_estimate)
                
                # Extract frames button
                if st.button("🚀 Extract Frames", type="primary"):
                    extract_frames_with_progress(video_path, config, service)
                
            except Exception as e:
                st.error(f"Error processing video: {str(e)}")
            
            finally:
                # Clean up temporary file
                if os.path.exists(video_path):
                    os.unlink(video_path)
    
    with col2:
        st.header("📈 Results & Visualization")
        
        if st.session_state.extraction_results:
            display_extraction_results(st.session_state.extraction_results)
        else:
            st.info("Upload a video and extract frames to see results here")


def configure_extraction() -> ExtractionConfig:
    """Configure extraction parameters in sidebar"""
    
    # Sampling strategy
    strategy = st.selectbox(
        "Sampling Strategy",
        options=[s.value for s in SamplingStrategy],
        index=3,  # Default to adaptive
        help="Choose how frames are selected from the video"
    )
    
    # Basic parameters
    time_interval = st.slider(
        "Time Interval (seconds)",
        min_value=0.1,
        max_value=10.0,
        value=1.0,
        step=0.1,
        help="Interval between frames for time-based sampling"
    )
    
    max_frames = st.number_input(
        "Maximum Frames",
        min_value=1,
        max_value=10000,
        value=100,
        help="Maximum number of frames to extract"
    )
    
    # Quality settings
    st.subheader("Quality Settings")
    
    enable_quality = st.checkbox(
        "Enable Quality Assessment",
        value=True,
        help="Assess and filter frames based on quality metrics"
    )
    
    quality_threshold = st.slider(
        "Minimum Quality Threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.6,
        step=0.05,
        disabled=not enable_quality,
        help="Minimum quality score for frame inclusion"
    )
    
    # Advanced settings
    with st.expander("🔧 Advanced Settings"):
        enable_preprocessing = st.checkbox(
            "Enable Preprocessing",
            value=True,
            help="Apply image enhancement for better OCR"
        )
        
        enable_perspective = st.checkbox(
            "Enable Perspective Correction",
            value=True,
            help="Correct perspective distortion in frames"
        )
        
        keyframe_threshold = st.slider(
            "Keyframe Detection Threshold",
            min_value=0.1,
            max_value=1.0,
            value=0.3,
            step=0.05,
            help="Sensitivity for keyframe detection"
        )
        
        scene_threshold = st.slider(
            "Scene Change Threshold",
            min_value=0.1,
            max_value=1.0,
            value=0.4,
            step=0.05,
            help="Sensitivity for scene change detection"
        )
        
        adaptive_threshold = st.slider(
            "Adaptive Complexity Threshold",
            min_value=0.1,
            max_value=1.0,
            value=0.5,
            step=0.05,
            help="Complexity threshold for adaptive sampling"
        )
        
        # Target resolution
        use_target_resolution = st.checkbox("Set Target Resolution")
        target_resolution = None
        if use_target_resolution:
            col1, col2 = st.columns(2)
            with col1:
                width = st.number_input("Width", min_value=100, max_value=4000, value=1920)
            with col2:
                height = st.number_input("Height", min_value=100, max_value=4000, value=1080)
            target_resolution = (width, height)
    
    return ExtractionConfig(
        sampling_strategy=SamplingStrategy(strategy),
        time_interval=time_interval,
        max_frames=max_frames,
        min_quality_threshold=quality_threshold,
        enable_quality_assessment=enable_quality,
        enable_perspective_correction=enable_perspective,
        enable_preprocessing=enable_preprocessing,
        target_resolution=target_resolution,
        keyframe_threshold=keyframe_threshold,
        scene_change_threshold=scene_threshold,
        adaptive_complexity_threshold=adaptive_threshold,
        save_frames=False  # Don't save to disk in UI mode
    )


def display_video_info(metadata: VideoMetadata):
    """Display video information"""
    st.subheader("📹 Video Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Duration", f"{metadata.duration:.1f}s")
        st.metric("Resolution", f"{metadata.width}x{metadata.height}")
        st.metric("Frame Rate", f"{metadata.fps:.1f} fps")
    
    with col2:
        st.metric("Total Frames", f"{metadata.total_frames:,}")
        st.metric("File Size", f"{metadata.file_size / (1024*1024):.1f} MB")
        st.metric("Codec", metadata.codec)


def display_video_stats(metadata: VideoMetadata):
    """Display video stats in sidebar"""
    st.metric("Duration", f"{metadata.duration:.1f}s")
    st.metric("FPS", f"{metadata.fps:.1f}")
    st.metric("Resolution", f"{metadata.width}x{metadata.height}")
    st.metric("Total Frames", f"{metadata.total_frames:,}")


def display_cost_estimate(cost_estimate: Dict[str, Any]):
    """Display processing cost estimate"""
    st.subheader("💰 Processing Estimate")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Estimated Frames",
            f"{cost_estimate['estimated_frames']:,}",
            help="Number of frames expected to be extracted"
        )
    
    with col2:
        st.metric(
            "Processing Time",
            f"{cost_estimate['estimated_processing_time_seconds']:.1f}s",
            help="Estimated processing time"
        )
    
    with col3:
        st.metric(
            "Storage Required",
            f"{cost_estimate['estimated_storage_mb']:.1f} MB",
            help="Estimated storage for extracted frames"
        )


def extract_frames_with_progress(video_path: str, config: ExtractionConfig, service: FrameExtractionService):
    """Extract frames with progress tracking"""
    
    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("Starting frame extraction...")
        
        # Start extraction
        start_time = time.time()
        frames = service.extract_frames(video_path, config)
        end_time = time.time()
        
        progress_bar.progress(1.0)
        status_text.text(f"✅ Extraction completed in {end_time - start_time:.1f}s")
        
        # Store results
        st.session_state.extraction_results = {
            'frames': frames,
            'config': config,
            'processing_time': end_time - start_time,
            'timestamp': datetime.now()
        }
        
        st.success(f"Successfully extracted {len(frames)} frames!")
        
    except Exception as e:
        st.error(f"Extraction failed: {str(e)}")
        progress_bar.empty()
        status_text.empty()


def display_extraction_results(results: Dict[str, Any]):
    """Display extraction results with visualizations"""
    frames = results['frames']
    config = results['config']
    processing_time = results['processing_time']
    
    # Summary metrics
    st.subheader("📊 Extraction Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Frames Extracted", len(frames))
    
    with col2:
        st.metric("Processing Time", f"{processing_time:.1f}s")
    
    with col3:
        avg_quality = np.mean([f.quality_metrics.confidence for f in frames])
        st.metric("Average Quality", f"{avg_quality:.3f}")
    
    with col4:
        st.metric("Strategy Used", config.sampling_strategy.value.title())
    
    # Quality distribution
    st.subheader("📈 Quality Analysis")
    
    # Create quality metrics dataframe
    quality_data = []
    for i, frame in enumerate(frames):
        quality_data.append({
            'Frame': i + 1,
            'Timestamp': frame.timestamp,
            'Quality Score': frame.quality_metrics.confidence,
            'Quality Level': frame.quality_metrics.overall_quality.value,
            'Blur Score': frame.quality_metrics.blur_score,
            'Contrast': frame.quality_metrics.contrast_score,
            'Brightness': frame.quality_metrics.brightness_score,
            'Sharpness': frame.quality_metrics.sharpness_score,
            'Text Density': frame.quality_metrics.text_region_density,
            'Sampling Reason': frame.sampling_reason
        })
    
    df = pd.DataFrame(quality_data)
    
    # Quality over time chart
    fig_timeline = px.line(
        df, 
        x='Timestamp', 
        y='Quality Score',
        title='Frame Quality Over Time',
        labels={'Timestamp': 'Time (seconds)', 'Quality Score': 'Quality Score (0-1)'}
    )
    fig_timeline.add_hline(y=config.min_quality_threshold, line_dash="dash", 
                          annotation_text="Quality Threshold")
    st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Quality distribution
    col1, col2 = st.columns(2)
    
    with col1:
        fig_hist = px.histogram(
            df, 
            x='Quality Score',
            nbins=20,
            title='Quality Score Distribution'
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        quality_counts = df['Quality Level'].value_counts()
        fig_pie = px.pie(
            values=quality_counts.values,
            names=quality_counts.index,
            title='Quality Level Distribution'
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Detailed metrics comparison
    st.subheader("🔍 Detailed Quality Metrics")
    
    metrics_cols = ['Blur Score', 'Contrast', 'Brightness', 'Sharpness', 'Text Density']
    fig_metrics = make_subplots(
        rows=2, cols=3,
        subplot_titles=metrics_cols + ['Overall Comparison'],
        specs=[[{"type": "scatter"}, {"type": "scatter"}, {"type": "scatter"}],
               [{"type": "scatter"}, {"type": "scatter"}, {"type": "bar"}]]
    )
    
    for i, metric in enumerate(metrics_cols):
        row = (i // 3) + 1
        col = (i % 3) + 1
        
        fig_metrics.add_trace(
            go.Scatter(
                x=df['Timestamp'],
                y=df[metric],
                mode='lines+markers',
                name=metric,
                showlegend=False
            ),
            row=row, col=col
        )
    
    # Overall comparison bar chart
    avg_metrics = df[metrics_cols].mean()
    fig_metrics.add_trace(
        go.Bar(
            x=metrics_cols,
            y=avg_metrics.values,
            name='Average Scores',
            showlegend=False
        ),
        row=2, col=3
    )
    
    fig_metrics.update_layout(height=600, title_text="Quality Metrics Analysis")
    st.plotly_chart(fig_metrics, use_container_width=True)
    
    # Frame gallery
    st.subheader("🖼️ Frame Gallery")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        quality_filter = st.selectbox(
            "Filter by Quality",
            options=['All'] + [q.value for q in FrameQuality],
            index=0
        )
    
    with col2:
        max_display = st.slider(
            "Max Frames to Display",
            min_value=5,
            max_value=min(50, len(frames)),
            value=min(20, len(frames))
        )
    
    with col3:
        sort_by = st.selectbox(
            "Sort by",
            options=['Timestamp', 'Quality Score', 'Frame Number'],
            index=0
        )
    
    # Filter and sort frames
    display_frames = frames.copy()
    
    if quality_filter != 'All':
        display_frames = [f for f in display_frames 
                         if f.quality_metrics.overall_quality.value == quality_filter]
    
    if sort_by == 'Quality Score':
        display_frames.sort(key=lambda x: x.quality_metrics.confidence, reverse=True)
    elif sort_by == 'Frame Number':
        display_frames.sort(key=lambda x: x.frame_number)
    else:  # Timestamp
        display_frames.sort(key=lambda x: x.timestamp)
    
    display_frames = display_frames[:max_display]
    
    # Display frames in grid
    cols_per_row = 4
    for i in range(0, len(display_frames), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j, col in enumerate(cols):
            if i + j < len(display_frames):
                frame = display_frames[i + j]
                
                with col:
                    # Convert BGR to RGB for display
                    rgb_image = cv2.cvtColor(frame.image_data, cv2.COLOR_BGR2RGB)
                    
                    st.image(
                        rgb_image,
                        caption=f"t={frame.timestamp:.1f}s | Q={frame.quality_metrics.confidence:.3f}",
                        use_column_width=True
                    )
                    
                    # Frame details in expander
                    with st.expander("Details"):
                        st.write(f"**Frame:** {frame.frame_number}")
                        st.write(f"**Timestamp:** {frame.timestamp:.2f}s")
                        st.write(f"**Quality:** {frame.quality_metrics.overall_quality.value}")
                        st.write(f"**Confidence:** {frame.quality_metrics.confidence:.3f}")
                        st.write(f"**Reason:** {frame.sampling_reason}")
                        
                        if frame.processing_metadata:
                            st.write("**Processing:**")
                            for key, value in frame.processing_metadata.items():
                                st.write(f"- {key}: {value}")
    
    # Export options
    st.subheader("💾 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export Quality Data"):
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"frame_quality_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📋 Export Summary Report"):
            report = generate_summary_report(results)
            st.download_button(
                label="Download Report",
                data=report,
                file_name=f"extraction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col3:
        if st.button("🖼️ Export Frame List"):
            frame_list = generate_frame_list(frames)
            st.download_button(
                label="Download Frame List",
                data=frame_list,
                file_name=f"frame_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )


def generate_summary_report(results: Dict[str, Any]) -> str:
    """Generate comprehensive summary report"""
    frames = results['frames']
    config = results['config']
    
    report = {
        'extraction_summary': {
            'timestamp': results['timestamp'].isoformat(),
            'processing_time_seconds': results['processing_time'],
            'frames_extracted': len(frames),
            'sampling_strategy': config.sampling_strategy.value,
            'configuration': {
                'time_interval': config.time_interval,
                'max_frames': config.max_frames,
                'quality_threshold': config.min_quality_threshold,
                'quality_assessment_enabled': config.enable_quality_assessment,
                'preprocessing_enabled': config.enable_preprocessing,
                'perspective_correction_enabled': config.enable_perspective_correction
            }
        },
        'quality_statistics': {
            'average_quality': np.mean([f.quality_metrics.confidence for f in frames]),
            'median_quality': np.median([f.quality_metrics.confidence for f in frames]),
            'min_quality': np.min([f.quality_metrics.confidence for f in frames]),
            'max_quality': np.max([f.quality_metrics.confidence for f in frames]),
            'quality_distribution': {
                quality.value: sum(1 for f in frames 
                                 if f.quality_metrics.overall_quality == quality)
                for quality in FrameQuality
            }
        },
        'sampling_analysis': {
            'time_range': {
                'start': min(f.timestamp for f in frames),
                'end': max(f.timestamp for f in frames),
                'span': max(f.timestamp for f in frames) - min(f.timestamp for f in frames)
            },
            'sampling_reasons': {
                reason: sum(1 for f in frames if reason in f.sampling_reason)
                for reason in set(f.sampling_reason.split('_')[0] for f in frames)
            }
        }
    }
    
    return json.dumps(report, indent=2, default=str)


def generate_frame_list(frames: List[ExtractedFrame]) -> str:
    """Generate detailed frame list"""
    frame_list = []
    
    for frame in frames:
        frame_data = {
            'frame_number': frame.frame_number,
            'timestamp': frame.timestamp,
            'quality_metrics': frame.quality_metrics.to_dict(),
            'sampling_reason': frame.sampling_reason,
            'processing_metadata': frame.processing_metadata
        }
        frame_list.append(frame_data)
    
    return json.dumps(frame_list, indent=2, default=str)


if __name__ == "__main__":
    main()