#!/usr/bin/env python3
"""
Task 78: Image Analysis Insights UI
Streamlit-based interactive interface for the Image Analysis and Insights System
"""

import streamlit as st
import cv2
import numpy as np
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import json
from pathlib import Path
import io
import base64
from typing import Dict, List, Optional
import time

# Import our analysis system
from image_analysis_insights_system import ImageAnalysisInsightsSystem, ComprehensiveImageInsights

# Configure Streamlit page
st.set_page_config(
    page_title="Image Analysis & Insights",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f77b4;
    margin: 0.5rem 0;
}

.quality-excellent { border-left-color: #2ca02c; }
.quality-good { border-left-color: #17becf; }
.quality-fair { border-left-color: #ff7f0e; }
.quality-poor { border-left-color: #d62728; }

.insight-box {
    background-color: #e8f4fd;
    padding: 1rem;
    border-radius: 0.5rem;
    border: 1px solid #1f77b4;
    margin: 0.5rem 0;
}

.section-header {
    color: #1f77b4;
    font-size: 1.2rem;
    font-weight: bold;
    margin: 1rem 0 0.5rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #1f77b4;
}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_analysis_system():
    """Load and cache the analysis system"""
    return ImageAnalysisInsightsSystem(use_gpu=False)

def create_color_palette_chart(color_analysis):
    """Create a color palette visualization"""
    colors = color_analysis.dominant_colors
    
    fig = go.Figure()
    
    # Create color swatches
    for i, color in enumerate(colors):
        fig.add_shape(
            type="rect",
            x0=i, y0=0, x1=i+1, y1=1,
            fillcolor=f"rgb({color[0]}, {color[1]}, {color[2]})",
            line=dict(color="black", width=1)
        )
    
    fig.update_layout(
        title="Dominant Colors",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        width=400,
        height=100,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    return fig

def create_quality_radar_chart(quality_metrics, confidence_scores):
    """Create a radar chart for quality metrics"""
    categories = ['Sharpness', 'Exposure', 'White Balance', 'Resolution', 'Overall']
    
    values = [
        quality_metrics.sharpness_score / 100,
        1.0 if quality_metrics.exposure_quality == "optimal" else 0.5,
        {'good': 1.0, 'fair': 0.7, 'poor': 0.3}[quality_metrics.white_balance],
        {'high': 1.0, 'medium': 0.8, 'low': 0.5}[quality_metrics.resolution_quality],
        quality_metrics.technical_score / 100
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Quality Scores',
        line_color='blue'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )),
        showlegend=False,
        title="Quality Assessment Radar"
    )
    
    return fig

def create_composition_chart(composition_analysis):
    """Create composition analysis chart"""
    metrics = {
        'Rule of Thirds': composition_analysis.rule_of_thirds_alignment,
        'Symmetry': composition_analysis.symmetry_score,
        'Balance': composition_analysis.balance_score
    }
    
    fig = go.Figure(data=[
        go.Bar(
            x=list(metrics.keys()),
            y=list(metrics.values()),
            marker_color=['#1f77b4', '#ff7f0e', '#2ca02c']
        )
    ])
    
    fig.update_layout(
        title="Composition Analysis",
        yaxis_title="Score (0-1)",
        showlegend=False,
        height=300
    )
    
    return fig

def create_confidence_chart(confidence_scores):
    """Create confidence scores visualization"""
    fig = go.Figure(data=[
        go.Bar(
            x=list(confidence_scores.keys()),
            y=list(confidence_scores.values()),
            marker_color=['#2ca02c', '#17becf', '#ff7f0e', '#d62728', '#9467bd'],
            text=[f"{v:.2f}" for v in confidence_scores.values()],
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        title="Analysis Confidence Scores",
        yaxis_title="Confidence (0-1)",
        xaxis_tickangle=-45,
        showlegend=False,
        height=400
    )
    
    return fig

def display_insights_summary(insights: ComprehensiveImageInsights):
    """Display a summary of key insights"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        quality_class = f"quality-{insights.quality_metrics.overall_quality}"
        st.markdown(f"""
        <div class="metric-card {quality_class}">
            <h4>Overall Quality</h4>
            <h2>{insights.quality_metrics.overall_quality.title()}</h2>
            <p>Technical Score: {insights.quality_metrics.technical_score:.1f}/100</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Scene Analysis</h4>
            <h2>{insights.content_analysis.scene_type.title()}</h2>
            <p>Complexity: {insights.content_analysis.scene_complexity}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Commercial Potential</h4>
            <h2>{insights.semantic_insights.commercial_potential.title()}</h2>
            <p>Confidence: {insights.confidence_scores['overall']:.2f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Processing Time</h4>
            <h2>{insights.processing_time:.2f}s</h2>
            <p>Timestamp: {insights.analysis_timestamp[:19]}</p>
        </div>
        """, unsafe_allow_html=True)

def display_detailed_analysis(insights: ComprehensiveImageInsights):
    """Display detailed analysis in tabs"""
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🎨 Color Analysis", 
        "📐 Composition", 
        "📋 Content", 
        "🏆 Quality", 
        "🧠 Semantic Insights",
        "📊 Technical Details"
    ])
    
    with tab1:
        st.markdown('<div class="section-header">Color Analysis</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Color palette
            fig_palette = create_color_palette_chart(insights.color_analysis)
            st.plotly_chart(fig_palette, use_container_width=True)
            
            # Color properties
            st.markdown("**Color Properties:**")
            st.write(f"🌡️ Temperature: **{insights.color_analysis.color_temperature}**")
            st.write(f"☀️ Brightness: **{insights.color_analysis.brightness_level}**")
            st.write(f"🎯 Contrast: **{insights.color_analysis.contrast_level}**")
            st.write(f"🎨 Saturation: **{insights.color_analysis.saturation_level}**")
            st.write(f"🌈 Diversity: **{insights.color_analysis.color_diversity:.2f}**")
        
        with col2:
            # Color histogram
            if insights.color_analysis.color_histogram:
                df_colors = pd.DataFrame(list(insights.color_analysis.color_histogram.items()), 
                                       columns=['Color', 'Count'])
                fig_hist = px.pie(df_colors, values='Count', names='Color', 
                                title="Color Distribution")
                st.plotly_chart(fig_hist, use_container_width=True)
    
    with tab2:
        st.markdown('<div class="section-header">Composition Analysis</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Composition chart
            fig_comp = create_composition_chart(insights.composition_analysis)
            st.plotly_chart(fig_comp, use_container_width=True)
        
        with col2:
            st.markdown("**Composition Details:**")
            st.write(f"📏 Aspect Ratio: **{insights.composition_analysis.aspect_ratio:.2f}**")
            st.write(f"🔄 Orientation: **{insights.composition_analysis.orientation}**")
            st.write(f"📍 Focal Points: **{len(insights.composition_analysis.focal_points)}**")
            st.write(f"📐 Leading Lines: **{'Yes' if insights.composition_analysis.leading_lines_detected else 'No'}**")
            st.write(f"🔍 Depth of Field: **{insights.composition_analysis.depth_of_field_estimate}**")
    
    with tab3:
        st.markdown('<div class="section-header">Content Analysis</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("**Scene Information:**")
            st.write(f"🏞️ Scene Type: **{insights.content_analysis.scene_type}**")
            st.write(f"🎭 Complexity: **{insights.content_analysis.scene_complexity}**")
            st.write(f"👥 Faces Detected: **{insights.content_analysis.faces_detected}**")
            st.write(f"📝 Text Regions: **{len(insights.content_analysis.text_regions)}**")
            st.write(f"😊 Emotional Tone: **{insights.content_analysis.emotional_tone}**")
            
        with col2:
            if insights.content_analysis.primary_subjects:
                st.markdown("**Primary Subjects:**")
                for subject in insights.content_analysis.primary_subjects:
                    st.write(f"• {subject}")
            
            if insights.content_analysis.object_count:
                st.markdown("**Object Counts:**")
                for obj, count in insights.content_analysis.object_count.items():
                    st.write(f"• {obj}: {count}")
    
    with tab4:
        st.markdown('<div class="section-header">Quality Assessment</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Quality radar chart
            fig_radar = create_quality_radar_chart(insights.quality_metrics, insights.confidence_scores)
            st.plotly_chart(fig_radar, use_container_width=True)
        
        with col2:
            st.markdown("**Quality Metrics:**")
            st.write(f"🔍 Sharpness: **{insights.quality_metrics.sharpness_score:.1f}/100**")
            st.write(f"📷 Exposure: **{insights.quality_metrics.exposure_quality}**")
            st.write(f"⚪ White Balance: **{insights.quality_metrics.white_balance}**")
            st.write(f"🔊 Noise Level: **{insights.quality_metrics.noise_level}**")
            st.write(f"📐 Resolution: **{insights.quality_metrics.resolution_quality}**")
            
            if insights.quality_metrics.compression_artifacts:
                st.warning("⚠️ Compression artifacts detected")
    
    with tab5:
        st.markdown('<div class="section-header">Semantic Insights</div>', unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="insight-box">
            <h4>Scene Description</h4>
            <p>{insights.semantic_insights.scene_description}</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("**Key Themes:**")
            for theme in insights.semantic_insights.key_themes:
                st.write(f"• {theme}")
                
            st.markdown("**Target Audience:**")
            for audience in insights.semantic_insights.target_audience:
                st.write(f"• {audience}")
        
        with col2:
            st.markdown("**Content Categories:**")
            for category in insights.semantic_insights.content_categories:
                st.write(f"• {category}")
                
            st.markdown("**Stock Photo Tags:**")
            tags_text = ", ".join(insights.semantic_insights.similar_stock_tags)
            st.text_area("Suggested Tags", tags_text, height=100)
        
        st.markdown("**Emotional Impact:**")
        st.write(insights.semantic_insights.emotional_impact)
        
        st.markdown("**Accessibility Description:**")
        st.write(insights.semantic_insights.accessibility_description)
    
    with tab6:
        st.markdown('<div class="section-header">Technical Details</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("**File Information:**")
            for key, value in insights.file_info.items():
                if key not in ['exif']:  # Skip EXIF for now
                    st.write(f"• **{key.replace('_', ' ').title()}:** {value}")
        
        with col2:
            # Confidence scores
            fig_conf = create_confidence_chart(insights.confidence_scores)
            st.plotly_chart(fig_conf, use_container_width=True)

def export_results(insights: ComprehensiveImageInsights):
    """Provide export options for analysis results"""
    st.sidebar.markdown("### 📥 Export Results")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("📄 Export JSON"):
            json_str = json.dumps(insights.__dict__, indent=2, default=str)
            st.sidebar.download_button(
                label="Download JSON",
                data=json_str,
                file_name=f"analysis_{int(time.time())}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("📊 Export CSV"):
            # Create a flattened DataFrame
            flat_data = {}
            
            def flatten_dict(d, parent_key='', sep='_'):
                for k, v in d.items():
                    new_key = f"{parent_key}{sep}{k}" if parent_key else k
                    if isinstance(v, dict):
                        flatten_dict(v, new_key, sep)
                    elif isinstance(v, list):
                        flat_data[new_key] = str(v)
                    else:
                        flat_data[new_key] = v
            
            flatten_dict(insights.__dict__)
            df = pd.DataFrame([flat_data])
            
            csv = df.to_csv(index=False)
            st.sidebar.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"analysis_{int(time.time())}.csv",
                mime="text/csv"
            )

def main():
    """Main Streamlit application"""
    st.title("🔍 Image Analysis & Insights System")
    st.markdown("**Advanced AI-powered image analysis with comprehensive insights**")
    
    # Sidebar for settings
    st.sidebar.title("⚙️ Settings")
    
    # Load analysis system
    with st.spinner("Loading analysis system..."):
        system = load_analysis_system()
    
    st.sidebar.success("✅ Analysis system loaded")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose an image file",
        type=['jpg', 'jpeg', 'png', 'bmp', 'tiff'],
        help="Upload an image file for comprehensive analysis"
    )
    
    # Demo images
    st.sidebar.markdown("### 🖼️ Demo Images")
    demo_option = st.sidebar.selectbox(
        "Select a demo image:",
        ["None", "Sample 1", "Sample 2", "Sample 3"]
    )
    
    if uploaded_file is not None:
        # Process uploaded image
        image = Image.open(uploaded_file)
        
        # Display image
        st.markdown("### 🖼️ Original Image")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(image, caption=uploaded_file.name, use_column_width=True)
        
        # Convert to OpenCV format
        image_array = np.array(image)
        if len(image_array.shape) == 3 and image_array.shape[2] == 3:
            # RGB to BGR for OpenCV
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        else:
            image_bgr = image_array
        
        # Analysis button
        if st.button("🔍 Analyze Image", type="primary"):
            with st.spinner("Performing comprehensive analysis..."):
                # Perform analysis
                progress_bar = st.progress(0)
                progress_bar.progress(20)
                
                insights = system.analyze_image(image_bgr)
                
                progress_bar.progress(100)
                progress_bar.empty()
            
            # Display results
            st.success(f"✅ Analysis completed in {insights.processing_time:.2f} seconds")
            
            # Summary section
            st.markdown("### 📊 Analysis Summary")
            display_insights_summary(insights)
            
            # Detailed analysis
            st.markdown("### 🔬 Detailed Analysis")
            display_detailed_analysis(insights)
            
            # Export options
            export_results(insights)
            
            # Store results in session state
            st.session_state['analysis_results'] = insights
    
    elif demo_option != "None":
        st.info("Demo functionality would load sample images here")
    
    else:
        # Welcome message
        st.markdown("""
        ### 🚀 Welcome to the Image Analysis & Insights System
        
        This advanced AI-powered tool provides comprehensive analysis of your images, including:
        
        - **🎨 Color Analysis**: Dominant colors, temperature, brightness, contrast
        - **📐 Composition**: Rule of thirds, symmetry, balance, focal points  
        - **📋 Content Detection**: Scene type, objects, faces, text regions
        - **🏆 Quality Assessment**: Sharpness, exposure, noise, compression
        - **🧠 Semantic Insights**: Scene description, themes, commercial potential
        - **📊 Technical Metrics**: File info, confidence scores, processing time
        
        **📁 Upload an image to get started!**
        """)
        
        # Feature highlights
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            #### 🎯 Accurate Analysis
            - Advanced computer vision
            - Multiple AI models
            - Confidence scoring
            """)
        
        with col2:
            st.markdown("""
            #### ⚡ Fast Processing
            - Optimized algorithms  
            - GPU acceleration
            - Real-time insights
            """)
        
        with col3:
            st.markdown("""
            #### 📊 Rich Insights
            - Visual analytics
            - Export options
            - Semantic understanding
            """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        🔍 Image Analysis & Insights System | Task 78 Implementation | 
        Powered by OpenCV, PyTorch & Advanced AI
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()