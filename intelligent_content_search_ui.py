#!/usr/bin/env python3
"""
Intelligent Content Search UI
Streamlit interface for visual scene search and audio pattern recognition
"""

import streamlit as st
import os
import json
import tempfile
from datetime import datetime, timedelta
import cv2
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import io

from intelligent_content_search import (
    IntelligentContentSearchSystem, VisualScene, AudioPattern, SearchResult
)

# Page configuration
st.set_page_config(
    page_title="Intelligent Content Search",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .search-box {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #e9ecef;
        margin-bottom: 2rem;
    }
    
    .result-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border-left: 4px solid #007bff;
    }
    
    .visual-result {
        border-left-color: #28a745;
    }
    
    .audio-result {
        border-left-color: #ffc107;
    }
    
    .timeline-event {
        background: #f8f9fa;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        position: relative;
        left: 20px;
    }
    
    .timeline-event::before {
        content: '';
        position: absolute;
        left: -10px;
        top: 50%;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #007bff;
        transform: translateY(-50%);
    }
    
    .stats-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
    }
    
    .pattern-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.875rem;
        font-weight: 500;
        margin: 0.25rem;
    }
    
    .pattern-music {
        background: #e3f2fd;
        color: #1976d2;
    }
    
    .pattern-speech {
        background: #f3e5f5;
        color: #7b1fa2;
    }
    
    .pattern-applause {
        background: #fff3e0;
        color: #f57c00;
    }
    
    .pattern-silence {
        background: #e8f5e9;
        color: #388e3c;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'search_system' not in st.session_state:
    st.session_state.search_system = IntelligentContentSearchSystem()
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'processed_videos' not in st.session_state:
    st.session_state.processed_videos = {}
if 'current_results' not in st.session_state:
    st.session_state.current_results = []

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🔍 Intelligent Content Search</h1>
        <p>Visual scene description, semantic video search, and audio pattern recognition</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("🎛️ Search Settings")
        
        # Search mode
        search_mode = st.radio(
            "Search Mode",
            ["Visual Scene Search", "Audio Pattern Search", "Combined Search"],
            help="Choose the type of content to search"
        )
        
        # Advanced settings
        with st.expander("⚙️ Advanced Settings"):
            max_results = st.slider("Max Results", 5, 50, 10)
            confidence_threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.5)
            
            if search_mode == "Visual Scene Search":
                scene_sampling = st.slider(
                    "Scene Sampling Interval (seconds)",
                    0.5, 5.0, 1.0,
                    help="How often to analyze video frames"
                )
            
            if search_mode == "Audio Pattern Search":
                pattern_types = st.multiselect(
                    "Pattern Types",
                    ["music", "speech", "applause", "silence", "noise"],
                    default=["music", "speech", "applause"]
                )
        
        # Statistics
        st.header("📊 System Statistics")
        stats = st.session_state.search_system.get_statistics()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Scenes Analyzed", stats['total_scenes'])
            st.metric("Audio Patterns", stats['total_patterns'])
        with col2:
            st.metric("Files Processed", stats['files_processed'])
            st.metric("Total Searches", stats['total_searches'])
    
    # Main content area
    tabs = st.tabs(["🔍 Search", "📤 Upload & Process", "📊 Analytics", "📜 Timeline View"])
    
    with tabs[0]:
        search_tab(search_mode, max_results, confidence_threshold)
    
    with tabs[1]:
        upload_tab()
    
    with tabs[2]:
        analytics_tab()
    
    with tabs[3]:
        timeline_tab()

def search_tab(search_mode, max_results, confidence_threshold):
    """Search interface tab"""
    st.header("🔍 Intelligent Content Search")
    
    # Search input
    st.markdown('<div class="search-box">', unsafe_allow_html=True)
    
    if search_mode == "Visual Scene Search":
        search_query = st.text_input(
            "Describe the scene you're looking for:",
            placeholder="e.g., 'person getting out of black car', 'sunset over ocean', 'crowded street scene'",
            key="visual_search"
        )
        
        # Example queries
        st.write("**Example queries:**")
        example_cols = st.columns(4)
        examples = [
            "woman in red dress",
            "car accident scene",
            "people shaking hands",
            "dog playing in park"
        ]
        for i, example in enumerate(examples):
            with example_cols[i]:
                if st.button(example, key=f"example_{i}"):
                    search_query = example
    
    elif search_mode == "Audio Pattern Search":
        col1, col2 = st.columns([2, 1])
        with col1:
            pattern_type = st.selectbox(
                "Select pattern type:",
                ["All", "music", "speech", "applause", "silence", "noise"]
            )
        with col2:
            file_filter = st.text_input("Filter by filename (optional)")
    
    else:  # Combined Search
        search_query = st.text_input(
            "Enter your search query:",
            placeholder="Search across all content types...",
            key="combined_search"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Search button
    if st.button("🔍 Search", type="primary", use_container_width=True):
        perform_search(search_mode, max_results, confidence_threshold)
    
    # Display results
    if st.session_state.current_results:
        display_search_results(st.session_state.current_results)
    
    # Search history
    if st.session_state.search_history:
        with st.expander("📜 Recent Searches"):
            for i, search in enumerate(reversed(st.session_state.search_history[-5:])):
                st.write(f"{i+1}. **{search['query']}** - {search['timestamp']} ({search['results']} results)")

def perform_search(search_mode, max_results, confidence_threshold):
    """Perform content search"""
    results = []
    
    with st.spinner("🔍 Searching..."):
        if search_mode == "Visual Scene Search":
            query = st.session_state.get('visual_search', '')
            if query:
                results = st.session_state.search_system.search_visual_scenes(query, max_results)
                results = [r for r in results if r.relevance_score >= confidence_threshold]
        
        elif search_mode == "Audio Pattern Search":
            pattern_type = st.session_state.get('pattern_type', None)
            if pattern_type == "All":
                pattern_type = None
            results = st.session_state.search_system.search_audio_patterns(pattern_type)
            results = [r for r in results if r.relevance_score >= confidence_threshold]
        
        else:  # Combined Search
            query = st.session_state.get('combined_search', '')
            if query:
                # Search both visual and audio
                visual_results = st.session_state.search_system.search_visual_scenes(query, max_results//2)
                audio_results = st.session_state.search_system.search_audio_patterns()
                
                # Combine and sort by relevance
                results = visual_results + audio_results
                results.sort(key=lambda x: x.relevance_score, reverse=True)
                results = results[:max_results]
    
    # Update state
    st.session_state.current_results = results
    
    # Log search
    if results:
        st.session_state.search_history.append({
            'query': search_mode,
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'results': len(results)
        })
    
    # Show summary
    if results:
        st.success(f"Found {len(results)} results!")
    else:
        st.info("No results found. Try adjusting your search query or settings.")

def display_search_results(results):
    """Display search results"""
    st.subheader(f"📋 Search Results ({len(results)} found)")
    
    for i, result in enumerate(results):
        if result.content_type == 'visual':
            display_visual_result(result, i)
        else:  # audio
            display_audio_result(result, i)

def display_visual_result(result: SearchResult, index: int):
    """Display a visual search result"""
    st.markdown(f"""
    <div class="result-card visual-result">
        <h4>#{index + 1} - Visual Scene</h4>
        <p><strong>File:</strong> {os.path.basename(result.file_path)}</p>
        <p><strong>Timestamp:</strong> {result.timestamp:.1f}s</p>
        <p><strong>Description:</strong> {result.description}</p>
        <p><strong>Relevance:</strong> {result.relevance_score:.1%}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Try to show frame preview
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button(f"🎬 Jump to Scene", key=f"jump_visual_{index}"):
            st.info(f"Would jump to {result.timestamp:.1f}s in {result.file_path}")
    with col2:
        if st.button(f"📸 Show Frame", key=f"frame_{index}"):
            show_frame_preview(result.file_path, result.timestamp)

def display_audio_result(result: SearchResult, index: int):
    """Display an audio search result"""
    # Extract pattern type from description
    pattern_type = result.description.split()[0]
    pattern_class = f"pattern-{pattern_type}"
    
    st.markdown(f"""
    <div class="result-card audio-result">
        <h4>#{index + 1} - Audio Pattern</h4>
        <p><strong>File:</strong> {os.path.basename(result.file_path)}</p>
        <p><strong>Time:</strong> {result.timestamp:.1f}s - {result.metadata.get('end_time', result.timestamp + 5):.1f}s</p>
        <p><span class="pattern-badge {pattern_class}">{pattern_type.upper()}</span></p>
        <p><strong>Confidence:</strong> {result.relevance_score:.1%}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button(f"🔊 Play Audio Segment", key=f"play_audio_{index}"):
        st.info(f"Would play audio from {result.timestamp:.1f}s")

def show_frame_preview(video_path: str, timestamp: float):
    """Show a frame preview from video"""
    try:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_number = int(timestamp * fps)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        
        if ret:
            # Convert to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Display
            st.image(frame_rgb, caption=f"Frame at {timestamp:.1f}s", use_column_width=True)
        else:
            st.error("Could not extract frame")
        
        cap.release()
    except Exception as e:
        st.error(f"Error showing frame: {e}")

def upload_tab():
    """Upload and process videos tab"""
    st.header("📤 Upload & Process Videos")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a video file",
        type=['mp4', 'avi', 'mov', 'mkv'],
        help="Upload a video to analyze for intelligent search"
    )
    
    if uploaded_file:
        st.success(f"Uploaded: {uploaded_file.name}")
        
        # Processing options
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Visual Analysis Options")
            analyze_visual = st.checkbox("Analyze visual scenes", value=True)
            if analyze_visual:
                frame_interval = st.slider(
                    "Frame sampling interval (seconds)",
                    0.5, 5.0, 1.0,
                    help="Analyze one frame every N seconds"
                )
        
        with col2:
            st.subheader("Audio Analysis Options")
            analyze_audio = st.checkbox("Analyze audio patterns", value=True)
            if analyze_audio:
                segment_duration = st.slider(
                    "Audio segment duration (seconds)",
                    1.0, 10.0, 5.0,
                    help="Duration of audio segments to analyze"
                )
        
        # Process button
        if st.button("🚀 Process Video", type="primary", use_container_width=True):
            process_uploaded_video(uploaded_file, analyze_visual, analyze_audio, 
                                 frame_interval if analyze_visual else None,
                                 segment_duration if analyze_audio else None)
    
    # Show processed videos
    if st.session_state.processed_videos:
        st.subheader("📁 Processed Videos")
        
        for filename, info in st.session_state.processed_videos.items():
            with st.expander(f"📹 {filename}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Duration", f"{info['duration']:.1f}s")
                    st.metric("FPS", f"{info['fps']:.1f}")
                
                with col2:
                    st.metric("Scenes Analyzed", info['scenes_analyzed'])
                    st.metric("Visual Events", len(info.get('visual_scenes', [])))
                
                with col3:
                    st.metric("Audio Patterns", info['audio_patterns_found'])
                    st.metric("Total Frames", info['total_frames'])
                
                if st.button(f"🗑️ Remove", key=f"remove_{filename}"):
                    del st.session_state.processed_videos[filename]
                    st.rerun()

def process_uploaded_video(uploaded_file, analyze_visual, analyze_audio, 
                         frame_interval, segment_duration):
    """Process an uploaded video file"""
    with st.spinner("🎬 Processing video... This may take a few minutes."):
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            tmp_path = tmp_file.name
        
        try:
            # Process video
            results = st.session_state.search_system.process_video_file(
                tmp_path,
                sample_interval=frame_interval or 1.0
            )
            
            # Store results
            st.session_state.processed_videos[uploaded_file.name] = results['metadata']
            st.session_state.processed_videos[uploaded_file.name]['visual_scenes'] = results['visual_scenes']
            st.session_state.processed_videos[uploaded_file.name]['audio_patterns'] = results['audio_patterns']
            
            # Show success message
            st.success(f"""
            ✅ Video processed successfully!
            - Analyzed {len(results['visual_scenes'])} visual scenes
            - Found {len(results['audio_patterns'])} audio patterns
            - Duration: {results['metadata']['duration']:.1f} seconds
            """)
            
            # Show sample results
            if results['visual_scenes']:
                st.subheader("Sample Visual Scenes")
                for scene in results['visual_scenes'][:3]:
                    st.write(f"- **{scene.timestamp:.1f}s**: {scene.description}")
            
            if results['audio_patterns']:
                st.subheader("Audio Patterns Found")
                pattern_counts = {}
                for pattern in results['audio_patterns']:
                    pattern_counts[pattern.pattern_type] = pattern_counts.get(pattern.pattern_type, 0) + 1
                
                for pattern_type, count in pattern_counts.items():
                    st.write(f"- **{pattern_type}**: {count} segments")
            
        except Exception as e:
            st.error(f"Error processing video: {e}")
        
        finally:
            # Clean up
            try:
                os.unlink(tmp_path)
            except:
                pass

def analytics_tab():
    """Analytics and insights tab"""
    st.header("📊 Analytics & Insights")
    
    stats = st.session_state.search_system.get_statistics()
    
    if stats['total_scenes'] == 0 and stats['total_patterns'] == 0:
        st.info("No data available yet. Process some videos to see analytics.")
        return
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="stats-card">
            <h2>{}</h2>
            <p>Total Scenes</p>
        </div>
        """.format(stats['total_scenes']), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stats-card">
            <h2>{}</h2>
            <p>Audio Patterns</p>
        </div>
        """.format(stats['total_patterns']), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="stats-card">
            <h2>{}</h2>
            <p>Videos Processed</p>
        </div>
        """.format(stats['files_processed']), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="stats-card">
            <h2>{}</h2>
            <p>Total Searches</p>
        </div>
        """.format(stats['total_searches']), unsafe_allow_html=True)
    
    # Pattern distribution
    if stats['pattern_distribution']:
        st.subheader("🎵 Audio Pattern Distribution")
        
        # Create pie chart
        pattern_df = pd.DataFrame(
            list(stats['pattern_distribution'].items()),
            columns=['Pattern Type', 'Count']
        )
        
        fig = px.pie(
            pattern_df,
            values='Count',
            names='Pattern Type',
            title="Distribution of Audio Patterns",
            color_discrete_map={
                'music': '#1976d2',
                'speech': '#7b1fa2',
                'applause': '#f57c00',
                'silence': '#388e3c',
                'noise': '#d32f2f'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Search trends
    if st.session_state.search_history:
        st.subheader("🔍 Search Activity")
        
        # Create timeline
        search_times = [datetime.strptime(s['timestamp'], "%H:%M:%S") for s in st.session_state.search_history]
        search_counts = [s['results'] for s in st.session_state.search_history]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=search_times,
            y=search_counts,
            mode='lines+markers',
            name='Results Found',
            line=dict(color='#007bff', width=2)
        ))
        fig.update_layout(
            title="Search Results Over Time",
            xaxis_title="Time",
            yaxis_title="Number of Results",
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)

def timeline_tab():
    """Timeline view of processed videos"""
    st.header("📜 Video Timeline View")
    
    if not st.session_state.processed_videos:
        st.info("No videos processed yet. Upload and process a video to see its timeline.")
        return
    
    # Select video
    video_name = st.selectbox(
        "Select a video:",
        list(st.session_state.processed_videos.keys())
    )
    
    if video_name:
        video_info = st.session_state.processed_videos[video_name]
        
        # Video info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Duration", f"{video_info['duration']:.1f}s")
        with col2:
            st.metric("Visual Events", video_info['scenes_analyzed'])
        with col3:
            st.metric("Audio Events", video_info['audio_patterns_found'])
        
        # Create timeline visualization
        st.subheader("🎬 Content Timeline")
        
        # Combine events
        timeline_events = []
        
        # Add visual events
        if 'visual_scenes' in video_info:
            for scene in video_info['visual_scenes']:
                timeline_events.append({
                    'time': scene.timestamp,
                    'type': 'visual',
                    'description': scene.description,
                    'confidence': scene.confidence
                })
        
        # Add audio events
        if 'audio_patterns' in video_info:
            for pattern in video_info['audio_patterns']:
                timeline_events.append({
                    'time': pattern.start_time,
                    'type': 'audio',
                    'description': f"{pattern.pattern_type} pattern",
                    'confidence': pattern.confidence
                })
        
        # Sort by time
        timeline_events.sort(key=lambda x: x['time'])
        
        # Display timeline
        if timeline_events:
            # Create interactive timeline chart
            fig = go.Figure()
            
            # Add visual events
            visual_events = [e for e in timeline_events if e['type'] == 'visual']
            if visual_events:
                fig.add_trace(go.Scatter(
                    x=[e['time'] for e in visual_events],
                    y=[1] * len(visual_events),
                    mode='markers',
                    name='Visual Scenes',
                    marker=dict(size=10, color='#28a745'),
                    text=[e['description'] for e in visual_events],
                    hovertemplate='<b>%{text}</b><br>Time: %{x:.1f}s<extra></extra>'
                ))
            
            # Add audio events
            audio_events = [e for e in timeline_events if e['type'] == 'audio']
            if audio_events:
                fig.add_trace(go.Scatter(
                    x=[e['time'] for e in audio_events],
                    y=[0] * len(audio_events),
                    mode='markers',
                    name='Audio Patterns',
                    marker=dict(size=10, color='#ffc107'),
                    text=[e['description'] for e in audio_events],
                    hovertemplate='<b>%{text}</b><br>Time: %{x:.1f}s<extra></extra>'
                ))
            
            fig.update_layout(
                title="Video Content Timeline",
                xaxis_title="Time (seconds)",
                yaxis=dict(
                    ticktext=['Audio', 'Visual'],
                    tickvals=[0, 1],
                    range=[-0.5, 1.5]
                ),
                hovermode='closest',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Event list
            st.subheader("📋 Timeline Events")
            
            for event in timeline_events[:20]:  # Show first 20 events
                event_type = "🎬" if event['type'] == 'visual' else "🎵"
                st.markdown(f"""
                <div class="timeline-event">
                    {event_type} <strong>{event['time']:.1f}s</strong> - {event['description']} 
                    <small>(confidence: {event['confidence']:.1%})</small>
                </div>
                """, unsafe_allow_html=True)
            
            if len(timeline_events) > 20:
                st.info(f"Showing first 20 of {len(timeline_events)} events")

if __name__ == "__main__":
    main()