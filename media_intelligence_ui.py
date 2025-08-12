"""
Media Asset Intelligence UI
Streamlit interface for video/image analysis and insights
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import numpy as np
from pathlib import Path
import base64

# Page configuration
st.set_page_config(
    page_title="Media Intelligence Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .scene-card {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #f5576c;
    }
    .highlight-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .thumbnail-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    .thumbnail-item {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        cursor: pointer;
        transition: transform 0.3s;
    }
    .thumbnail-item:hover {
        transform: scale(1.05);
    }
    .quality-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: bold;
        margin: 0.25rem;
    }
    .quality-high { background: #10b981; color: white; }
    .quality-medium { background: #f59e0b; color: white; }
    .quality-low { background: #ef4444; color: white; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'media_analysis' not in st.session_state:
    st.session_state.media_analysis = None
if 'selected_scene' not in st.session_state:
    st.session_state.selected_scene = None
if 'comparison_results' not in st.session_state:
    st.session_state.comparison_results = None

# Header
st.markdown('<h1 class="main-header">🎬 Media Asset Intelligence Dashboard</h1>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Analysis Settings")
    
    analysis_type = st.selectbox(
        "Analysis Type",
        ["Single Asset", "Batch Processing", "Comparison", "Live Analysis"]
    )
    
    st.markdown("---")
    
    deep_analysis = st.checkbox("Deep Analysis", value=True)
    extract_highlights = st.checkbox("Extract Highlights", value=True)
    generate_thumbnails = st.checkbox("Generate Thumbnails", value=True)
    
    st.markdown("---")
    
    st.header("🎯 Quick Actions")
    if st.button("🎥 Generate Summary Video"):
        st.info("Summary generation started...")
    if st.button("📊 Export Report"):
        st.info("Generating report...")
    if st.button("🔄 Clear Analysis"):
        st.session_state.media_analysis = None
        st.success("Analysis cleared!")

# Main content
if analysis_type == "Single Asset":
    st.header("📹 Media Asset Analysis")
    
    # File upload
    col1, col2 = st.columns([3, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Upload Media File",
            type=['mp4', 'avi', 'mov', 'mkv', 'jpg', 'jpeg', 'png'],
            help="Upload a video or image file for analysis"
        )
    
    with col2:
        if uploaded_file:
            file_details = {
                "Filename": uploaded_file.name,
                "Size": f"{uploaded_file.size / 1024 / 1024:.2f} MB",
                "Type": uploaded_file.type
            }
            for key, value in file_details.items():
                st.text(f"{key}: {value}")
    
    if uploaded_file:
        analyze_btn = st.button("🔍 Analyze Media", type="primary", use_container_width=True)
        
        if analyze_btn:
            with st.spinner("Analyzing media asset..."):
                # Mock analysis for Python 3.12 compatibility
                mock_analysis = {
                    "asset_id": f"media_{datetime.now().timestamp()}",
                    "media_type": "video",
                    "duration": 180.5,  # seconds
                    "resolution": "1920x1080",
                    "fps": 30,
                    "quality_score": 0.88,
                    "scenes": [
                        {"id": "s1", "type": "intro", "start": 0, "end": 10, "confidence": 0.92},
                        {"id": "s2", "type": "content", "start": 10, "end": 60, "confidence": 0.88},
                        {"id": "s3", "type": "interview", "start": 60, "end": 120, "confidence": 0.95},
                        {"id": "s4", "type": "action", "start": 120, "end": 170, "confidence": 0.85},
                        {"id": "s5", "type": "outro", "start": 170, "end": 180.5, "confidence": 0.90}
                    ],
                    "highlights": [
                        {"start": 15, "end": 25, "score": 0.92, "reason": "High engagement moment"},
                        {"start": 75, "end": 85, "score": 0.88, "reason": "Key dialogue"},
                        {"start": 125, "end": 135, "score": 0.95, "reason": "Peak action"}
                    ],
                    "detected_objects": {
                        "person": 15,
                        "car": 3,
                        "building": 8,
                        "tree": 12
                    },
                    "detected_brands": ["Apple", "Nike", "Google"],
                    "unique_faces": 4,
                    "viral_potential": 0.72,
                    "color_palette": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"],
                    "auto_chapters": [
                        {"title": "Introduction", "start": 0, "end": 10},
                        {"title": "Main Content", "start": 10, "end": 60},
                        {"title": "Interview Segment", "start": 60, "end": 120},
                        {"title": "Action Sequence", "start": 120, "end": 170},
                        {"title": "Conclusion", "start": 170, "end": 180.5}
                    ]
                }
                
                st.session_state.media_analysis = mock_analysis
        
        # Display results
        if st.session_state.media_analysis:
            analysis = st.session_state.media_analysis
            
            st.markdown("---")
            st.header("📊 Analysis Results")
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                quality = analysis["quality_score"]
                quality_class = "quality-high" if quality > 0.8 else "quality-medium" if quality > 0.6 else "quality-low"
                st.markdown(f"""
                <div class="metric-card">
                    <h4>Quality Score</h4>
                    <span class="quality-badge {quality_class}">{quality*100:.1f}%</span>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.metric("Duration", f"{analysis['duration']:.1f}s")
                st.metric("Resolution", analysis["resolution"])
            
            with col3:
                st.metric("Scenes Detected", len(analysis["scenes"]))
                st.metric("Highlights", len(analysis["highlights"]))
            
            with col4:
                st.metric("Viral Potential", f"{analysis['viral_potential']*100:.1f}%")
                st.metric("Unique Faces", analysis["unique_faces"])
            
            # Scene timeline
            st.subheader("🎬 Scene Timeline")
            
            scene_data = []
            for scene in analysis["scenes"]:
                scene_data.append({
                    "Scene": scene["id"],
                    "Type": scene["type"].title(),
                    "Start": scene["start"],
                    "Duration": scene["end"] - scene["start"],
                    "Confidence": scene["confidence"]
                })
            
            scene_df = pd.DataFrame(scene_data)
            
            # Timeline visualization
            fig_timeline = px.timeline(
                scene_df,
                x_start="Start",
                x_end="Start",
                y="Type",
                color="Confidence",
                hover_data=["Duration"],
                color_continuous_scale="viridis"
            )
            fig_timeline.update_layout(height=300)
            st.plotly_chart(fig_timeline, use_container_width=True)
            
            # Scene details
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("📝 Scene Details")
                selected_scene = st.selectbox(
                    "Select a scene",
                    options=[s["id"] for s in analysis["scenes"]],
                    format_func=lambda x: f"{x} - {next(s['type'] for s in analysis['scenes'] if s['id'] == x).title()}"
                )
                
                if selected_scene:
                    scene = next(s for s in analysis["scenes"] if s["id"] == selected_scene)
                    st.markdown(f"""
                    <div class="scene-card">
                        <h4>{scene['type'].title()} Scene</h4>
                        <p><strong>Time:</strong> {scene['start']}s - {scene['end']}s</p>
                        <p><strong>Duration:</strong> {scene['end'] - scene['start']}s</p>
                        <p><strong>Confidence:</strong> {scene['confidence']*100:.1f}%</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                st.subheader("🎨 Color Palette")
                colors_html = ""
                for color in analysis["color_palette"]:
                    colors_html += f'<div style="display:inline-block; width:40px; height:40px; background:{color}; margin:2px; border-radius:4px;"></div>'
                st.markdown(colors_html, unsafe_allow_html=True)
                
                # Object detection
                st.subheader("🔍 Detected Objects")
                objects_df = pd.DataFrame(
                    list(analysis["detected_objects"].items()),
                    columns=["Object", "Count"]
                )
                fig_objects = px.bar(objects_df, x="Count", y="Object", orientation='h')
                fig_objects.update_layout(height=200)
                st.plotly_chart(fig_objects, use_container_width=True)
            
            # Highlights
            st.subheader("✨ Key Highlights")
            
            for idx, highlight in enumerate(analysis["highlights"], 1):
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    st.write(f"**Highlight {idx}**")
                with col2:
                    st.markdown(f"""
                    <div class="highlight-card">
                        <strong>Time:</strong> {highlight['start']}s - {highlight['end']}s<br>
                        <strong>Score:</strong> {highlight['score']*100:.1f}%<br>
                        <strong>Reason:</strong> {highlight['reason']}
                    </div>
                    """, unsafe_allow_html=True)
                with col3:
                    if st.button(f"📹 Preview", key=f"preview_{idx}"):
                        st.info("Preview functionality coming soon")
            
            # Auto chapters
            st.subheader("📚 Auto-Generated Chapters")
            chapters_df = pd.DataFrame(analysis["auto_chapters"])
            st.dataframe(chapters_df, use_container_width=True)
            
            # Recommendations
            st.subheader("💡 Optimization Suggestions")
            
            suggestions = []
            if analysis["quality_score"] < 0.7:
                suggestions.append("🎥 Consider improving video quality (resolution/bitrate)")
            if analysis["viral_potential"] < 0.5:
                suggestions.append("📈 Add more engaging elements to increase viral potential")
            if len(analysis["highlights"]) < 2:
                suggestions.append("✨ Content lacks highlight moments - add more dynamic segments")
            if analysis["duration"] > 600:
                suggestions.append("⏱️ Consider creating a shorter version for social media")
            if analysis["detected_brands"]:
                suggestions.append(f"™️ Brand detection: {', '.join(analysis['detected_brands'])} - ensure proper rights")
            
            if suggestions:
                for suggestion in suggestions:
                    st.info(suggestion)
            else:
                st.success("✅ Media asset is well-optimized!")

elif analysis_type == "Batch Processing":
    st.header("📦 Batch Media Processing")
    
    uploaded_files = st.file_uploader(
        "Upload Multiple Media Files",
        type=['mp4', 'avi', 'mov', 'jpg', 'png'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        st.write(f"Selected {len(uploaded_files)} files for processing")
        
        if st.button("🚀 Process Batch", type="primary"):
            progress_bar = st.progress(0)
            results = []
            
            for idx, file in enumerate(uploaded_files):
                progress_bar.progress((idx + 1) / len(uploaded_files))
                
                # Mock processing
                results.append({
                    "filename": file.name,
                    "quality_score": np.random.uniform(0.6, 0.95),
                    "viral_potential": np.random.uniform(0.4, 0.9),
                    "scenes": np.random.randint(3, 15),
                    "highlights": np.random.randint(1, 8)
                })
            
            results_df = pd.DataFrame(results)
            
            st.success(f"✅ Processed {len(results)} files successfully!")
            
            # Results visualization
            col1, col2 = st.columns(2)
            
            with col1:
                fig_quality = px.bar(results_df, x="filename", y="quality_score", title="Quality Scores")
                st.plotly_chart(fig_quality, use_container_width=True)
            
            with col2:
                fig_viral = px.scatter(results_df, x="quality_score", y="viral_potential", 
                                     size="highlights", hover_data=["filename"],
                                     title="Quality vs Viral Potential")
                st.plotly_chart(fig_viral, use_container_width=True)
            
            # Download results
            st.dataframe(results_df, use_container_width=True)
            csv = results_df.to_csv(index=False)
            st.download_button("📥 Download Results", csv, "batch_analysis.csv", "text/csv")

elif analysis_type == "Comparison":
    st.header("🔄 Media Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Media A")
        file_a = st.file_uploader("Upload first media", type=['mp4', 'jpg', 'png'], key="file_a")
        
    with col2:
        st.subheader("Media B")
        file_b = st.file_uploader("Upload second media", type=['mp4', 'jpg', 'png'], key="file_b")
    
    if file_a and file_b:
        if st.button("🔍 Compare Media", type="primary"):
            with st.spinner("Comparing media assets..."):
                # Mock comparison
                comparison = {
                    "quality": {"A": 0.85, "B": 0.78},
                    "engagement": {"A": 0.72, "B": 0.81},
                    "viral_potential": {"A": 0.65, "B": 0.71},
                    "technical": {"A": 0.90, "B": 0.82},
                    "creativity": {"A": 0.75, "B": 0.88}
                }
                
                st.session_state.comparison_results = comparison
    
    if st.session_state.comparison_results:
        comparison = st.session_state.comparison_results
        
        # Radar chart comparison
        categories = list(comparison.keys())
        values_a = [comparison[cat]["A"] for cat in categories]
        values_b = [comparison[cat]["B"] for cat in categories]
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values_a,
            theta=categories,
            fill='toself',
            name='Media A'
        ))
        fig.add_trace(go.Scatterpolar(
            r=values_b,
            theta=categories,
            fill='toself',
            name='Media B'
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            title="Media Comparison Radar Chart"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Winner determination
        score_a = sum(values_a) / len(values_a)
        score_b = sum(values_b) / len(values_b)
        
        if score_a > score_b:
            st.success(f"🏆 Media A has better overall performance ({score_a:.2f} vs {score_b:.2f})")
        else:
            st.success(f"🏆 Media B has better overall performance ({score_b:.2f} vs {score_a:.2f})")

elif analysis_type == "Live Analysis":
    st.header("🔴 Live Media Analysis")
    
    st.info("Live analysis allows real-time processing of streaming media")
    
    stream_source = st.selectbox(
        "Stream Source",
        ["Webcam", "Screen Recording", "URL Stream", "File Stream"]
    )
    
    if stream_source == "URL Stream":
        stream_url = st.text_input("Enter stream URL", placeholder="rtmp://example.com/stream")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶️ Start Analysis", type="primary"):
            st.session_state.live_analysis = True
    with col2:
        if st.button("⏸️ Pause"):
            st.session_state.live_analysis = False
    with col3:
        if st.button("⏹️ Stop"):
            st.session_state.live_analysis = False
    
    if st.session_state.get('live_analysis'):
        # Mock live metrics
        placeholder = st.empty()
        
        for i in range(10):
            with placeholder.container():
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Quality", f"{np.random.uniform(0.7, 0.95)*100:.1f}%", 
                             f"{np.random.uniform(-5, 5):.1f}%")
                with col2:
                    st.metric("Engagement", f"{np.random.uniform(0.6, 0.9)*100:.1f}%",
                             f"{np.random.uniform(-3, 3):.1f}%")
                with col3:
                    st.metric("Faces Detected", np.random.randint(0, 5))
                with col4:
                    st.metric("Objects", np.random.randint(3, 15))
                
                # Live chart
                data = pd.DataFrame({
                    'Time': range(i*10, (i+1)*10),
                    'Quality': np.random.uniform(0.7, 0.95, 10),
                    'Engagement': np.random.uniform(0.6, 0.9, 10)
                })
                
                fig = px.line(data, x='Time', y=['Quality', 'Engagement'], 
                            title="Real-time Metrics")
                st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.caption("Media Intelligence Dashboard v1.0 | Powered by Computer Vision & AI")