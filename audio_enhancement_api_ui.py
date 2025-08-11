"""
Enhanced Streamlit UI for Audio Enhancement Pipeline with API Integration
This module provides a comprehensive Streamlit interface that connects to the FastAPI backend
"""

import streamlit as st
import os
import tempfile
import requests
import json
import time
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Any, Optional
import base64
from datetime import datetime

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_ENDPOINT = f"{API_BASE_URL}/api/v1/audio-enhancement"

# Page configuration
st.set_page_config(
    page_title="Audio Enhancement Pipeline - Enterprise",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enterprise styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .enhancement-card {
        background: white;
        border-radius: 1rem;
        padding: 1.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 0.5rem;
        font-weight: bold;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialize session state variables"""
    if 'enhancement_task' not in st.session_state:
        st.session_state.enhancement_task = None
    if 'original_metrics' not in st.session_state:
        st.session_state.original_metrics = None
    if 'enhanced_metrics' not in st.session_state:
        st.session_state.enhanced_metrics = None
    if 'processing_history' not in st.session_state:
        st.session_state.processing_history = []

def check_api_health():
    """Check if the API is healthy"""
    try:
        response = requests.get(f"{API_ENDPOINT}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_enhancement_presets():
    """Fetch available enhancement presets from API"""
    try:
        response = requests.get(f"{API_ENDPOINT}/presets")
        if response.status_code == 200:
            return response.json().get('data', {}).get('presets', [])
    except:
        pass
    
    # Fallback presets if API is not available
    return [
        {
            "id": "podcast",
            "name": "Podcast Optimization",
            "description": "Optimized for spoken word podcasts",
            "settings": {
                "enable_noise_reduction": True,
                "noise_reduction_strength": 0.8,
                "enable_normalization": True,
                "target_loudness_lufs": -16.0,
                "enable_compression": True,
                "compression_ratio": 3.0
            }
        },
        {
            "id": "music",
            "name": "Music Enhancement",
            "description": "Enhance music recordings",
            "settings": {
                "enable_noise_reduction": False,
                "enable_normalization": True,
                "target_loudness_lufs": -14.0,
                "enable_compression": False
            }
        },
        {
            "id": "interview",
            "name": "Interview Cleanup",
            "description": "Clean up interview recordings",
            "settings": {
                "enable_noise_reduction": True,
                "noise_reduction_strength": 0.6,
                "enable_normalization": True,
                "target_loudness_lufs": -18.0
            }
        },
        {
            "id": "restoration",
            "name": "Audio Restoration",
            "description": "Restore old or damaged recordings",
            "settings": {
                "enable_noise_reduction": True,
                "noise_reduction_strength": 0.9,
                "enable_normalization": True,
                "target_loudness_lufs": -20.0,
                "enable_declick": True,
                "enable_dehum": True
            }
        }
    ]

def analyze_audio(file_bytes, filename):
    """Analyze audio quality via API"""
    try:
        files = {'file': (filename, file_bytes, 'audio/wav')}
        response = requests.post(f"{API_ENDPOINT}/analyze", files=files, timeout=30)
        if response.status_code == 200:
            return response.json().get('data', {}).get('metrics')
    except Exception as e:
        st.error(f"Analysis failed: {str(e)}")
    return None

def enhance_audio(file_bytes, filename, settings):
    """Enhance audio via API"""
    try:
        files = {'file': (filename, file_bytes, 'audio/wav')}
        data = {'settings': json.dumps(settings)}
        response = requests.post(f"{API_ENDPOINT}/enhance", files=files, data=data, timeout=60)
        if response.status_code == 200:
            return response.json().get('data')
    except Exception as e:
        st.error(f"Enhancement failed: {str(e)}")
    return None

def download_enhanced_audio(task_id):
    """Download enhanced audio from API"""
    try:
        response = requests.get(f"{API_ENDPOINT}/download/{task_id}", timeout=30)
        if response.status_code == 200:
            return response.content
    except Exception as e:
        st.error(f"Download failed: {str(e)}")
    return None

def create_metrics_visualization(original_metrics, enhanced_metrics=None):
    """Create visualization comparing original and enhanced metrics"""
    metrics_names = ['SNR (dB)', 'Dynamic Range (dB)', 'Loudness (LUFS)', 'Quality Score']
    
    if enhanced_metrics:
        original_values = [
            original_metrics.get('snr_db', 0),
            original_metrics.get('dynamic_range_db', 0),
            original_metrics.get('loudness_lufs', 0),
            original_metrics.get('quality_score', 0)
        ]
        enhanced_values = [
            enhanced_metrics.get('snr_db', 0),
            enhanced_metrics.get('dynamic_range_db', 0),
            enhanced_metrics.get('loudness_lufs', 0),
            enhanced_metrics.get('quality_score', 0)
        ]
        
        fig = go.Figure(data=[
            go.Bar(name='Original', x=metrics_names, y=original_values, marker_color='lightcoral'),
            go.Bar(name='Enhanced', x=metrics_names, y=enhanced_values, marker_color='lightgreen')
        ])
        fig.update_layout(
            title="Audio Quality Metrics Comparison",
            barmode='group',
            height=400,
            showlegend=True
        )
    else:
        values = [
            original_metrics.get('snr_db', 0),
            original_metrics.get('dynamic_range_db', 0),
            original_metrics.get('loudness_lufs', 0),
            original_metrics.get('quality_score', 0)
        ]
        
        fig = go.Figure(data=[
            go.Bar(x=metrics_names, y=values, marker_color='steelblue')
        ])
        fig.update_layout(
            title="Audio Quality Metrics",
            height=400
        )
    
    return fig

def create_improvement_gauge(improvement_score):
    """Create a gauge chart for improvement score"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = improvement_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Overall Improvement"},
        delta = {'reference': 0, 'increasing': {'color': "green"}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 25], 'color': 'lightgray'},
                {'range': [25, 50], 'color': 'gray'},
                {'range': [50, 75], 'color': 'lightgreen'},
                {'range': [75, 100], 'color': 'green'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    fig.update_layout(height=300)
    return fig

def main():
    init_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🎧 Audio Enhancement Pipeline</h1>', unsafe_allow_html=True)
    
    # API Status
    api_status = check_api_health()
    if api_status:
        st.success("✅ API Connected and Healthy")
    else:
        st.warning("⚠️ API Not Available - Running in Demo Mode")
    
    # Main layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 🎛️ Enhancement Settings")
        
        # Preset selection
        presets = get_enhancement_presets()
        preset_names = ["Custom"] + [p['name'] for p in presets]
        selected_preset = st.selectbox("Select Preset", preset_names)
        
        # Apply preset settings
        if selected_preset != "Custom":
            preset = next((p for p in presets if p['name'] == selected_preset), None)
            if preset:
                st.info(f"📋 {preset['description']}")
                settings = preset['settings']
        else:
            settings = {}
        
        # Enhancement options
        with st.expander("🔧 Noise Reduction", expanded=True):
            enable_noise = st.checkbox("Enable Noise Reduction", value=settings.get('enable_noise_reduction', True))
            if enable_noise:
                noise_strength = st.slider("Reduction Strength", 0.0, 1.0, 
                                          settings.get('noise_reduction_strength', 0.7), 0.1)
                settings['enable_noise_reduction'] = True
                settings['noise_reduction_strength'] = noise_strength
            else:
                settings['enable_noise_reduction'] = False
        
        with st.expander("📊 Audio Normalization", expanded=True):
            enable_norm = st.checkbox("Enable Normalization", value=settings.get('enable_normalization', True))
            if enable_norm:
                target_lufs = st.slider("Target Loudness (LUFS)", -30.0, -6.0, 
                                       settings.get('target_loudness_lufs', -16.0), 0.5)
                settings['enable_normalization'] = True
                settings['target_loudness_lufs'] = target_lufs
            else:
                settings['enable_normalization'] = False
        
        with st.expander("🎚️ Dynamic Compression", expanded=False):
            enable_comp = st.checkbox("Enable Compression", value=settings.get('enable_compression', False))
            if enable_comp:
                comp_ratio = st.slider("Compression Ratio", 1.0, 20.0, 
                                      settings.get('compression_ratio', 4.0), 0.5)
                settings['enable_compression'] = True
                settings['compression_ratio'] = comp_ratio
            else:
                settings['enable_compression'] = False
        
        with st.expander("🔌 Additional Processing", expanded=False):
            settings['enable_declick'] = st.checkbox("Remove Clicks", 
                                                     value=settings.get('enable_declick', True))
            settings['enable_dehum'] = st.checkbox("Remove Hum", 
                                                   value=settings.get('enable_dehum', True))
            settings['enable_eq'] = st.checkbox("Apply EQ", 
                                               value=settings.get('enable_eq', False))
            if settings['enable_eq']:
                settings['eq_preset'] = st.selectbox("EQ Preset", 
                                                     ["speech", "music", "podcast"])
        
        # Output settings
        st.markdown("### 📤 Output Settings")
        settings['output_format'] = st.selectbox("Output Format", ["wav", "mp3", "flac"])
        settings['output_sample_rate'] = st.selectbox("Sample Rate", 
                                                      [22050, 44100, 48000], index=1)
    
    with col2:
        st.markdown("### 📁 Audio Upload & Processing")
        
        # File upload
        uploaded_file = st.file_uploader("Choose an audio file", 
                                        type=['wav', 'mp3', 'm4a', 'flac', 'ogg'])
        
        if uploaded_file:
            st.success(f"✅ File uploaded: {uploaded_file.name}")
            file_bytes = uploaded_file.read()
            
            # Action buttons
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            
            with col_btn1:
                if st.button("🔍 Analyze Quality", type="primary"):
                    with st.spinner("Analyzing audio quality..."):
                        metrics = analyze_audio(file_bytes, uploaded_file.name)
                        if metrics:
                            st.session_state.original_metrics = metrics
                            st.success("✅ Analysis complete!")
            
            with col_btn2:
                if st.button("⚡ Enhance Audio", type="primary"):
                    with st.spinner("Enhancing audio..."):
                        result = enhance_audio(file_bytes, uploaded_file.name, settings)
                        if result:
                            st.session_state.enhancement_task = result
                            st.session_state.enhanced_metrics = result.get('enhanced_metrics')
                            st.success("✅ Enhancement complete!")
                            
                            # Add to history
                            st.session_state.processing_history.append({
                                'filename': uploaded_file.name,
                                'timestamp': datetime.now().isoformat(),
                                'improvement': result.get('improvement_score', 0)
                            })
            
            with col_btn3:
                if st.session_state.enhancement_task and st.session_state.enhancement_task.get('task_id'):
                    if st.button("💾 Download Enhanced", type="primary"):
                        audio_data = download_enhanced_audio(st.session_state.enhancement_task['task_id'])
                        if audio_data:
                            st.download_button(
                                label="📥 Save Enhanced Audio",
                                data=audio_data,
                                file_name=f"enhanced_{uploaded_file.name}",
                                mime="audio/wav"
                            )
            
            # Display metrics
            if st.session_state.original_metrics or st.session_state.enhanced_metrics:
                st.markdown("### 📊 Quality Metrics")
                
                if st.session_state.enhanced_metrics:
                    # Show comparison
                    col_orig, col_enh = st.columns(2)
                    
                    with col_orig:
                        st.markdown("#### Original")
                        orig = st.session_state.original_metrics
                        st.metric("Quality Score", f"{orig.get('quality_score', 0):.1f}/100")
                        st.metric("SNR", f"{orig.get('snr_db', 0):.1f} dB")
                        st.metric("Loudness", f"{orig.get('loudness_lufs', 0):.1f} LUFS")
                    
                    with col_enh:
                        st.markdown("#### Enhanced")
                        enh = st.session_state.enhanced_metrics
                        orig_score = st.session_state.original_metrics.get('quality_score', 0)
                        enh_score = enh.get('quality_score', 0)
                        improvement = enh_score - orig_score
                        
                        st.metric("Quality Score", f"{enh_score:.1f}/100", 
                                 delta=f"+{improvement:.1f}")
                        st.metric("SNR", f"{enh.get('snr_db', 0):.1f} dB",
                                 delta=f"+{enh.get('snr_db', 0) - orig.get('snr_db', 0):.1f}")
                        st.metric("Loudness", f"{enh.get('loudness_lufs', 0):.1f} LUFS")
                    
                    # Visualization
                    fig = create_metrics_visualization(st.session_state.original_metrics, 
                                                      st.session_state.enhanced_metrics)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Improvement gauge
                    if st.session_state.enhancement_task:
                        improvement_score = st.session_state.enhancement_task.get('improvement_score', 0)
                        if improvement_score:
                            gauge_fig = create_improvement_gauge(abs(improvement_score))
                            st.plotly_chart(gauge_fig, use_container_width=True)
                
                elif st.session_state.original_metrics:
                    # Show only original metrics
                    metrics = st.session_state.original_metrics
                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    
                    with col_m1:
                        st.metric("Quality Score", f"{metrics.get('quality_score', 0):.1f}/100")
                    with col_m2:
                        st.metric("SNR", f"{metrics.get('snr_db', 0):.1f} dB")
                    with col_m3:
                        st.metric("Loudness", f"{metrics.get('loudness_lufs', 0):.1f} LUFS")
                    with col_m4:
                        st.metric("Dynamic Range", f"{metrics.get('dynamic_range_db', 0):.1f} dB")
                    
                    # Recommendations
                    if metrics.get('recommendations'):
                        st.markdown("#### 💡 Recommendations")
                        for rec in metrics['recommendations']:
                            st.info(f"• {rec}")
                    
                    # Visualization
                    fig = create_metrics_visualization(metrics)
                    st.plotly_chart(fig, use_container_width=True)
            
            # Processing details
            if st.session_state.enhancement_task:
                with st.expander("🔧 Processing Details", expanded=False):
                    task = st.session_state.enhancement_task
                    st.json({
                        "Task ID": task.get('task_id'),
                        "Status": task.get('status'),
                        "Processing Time": f"{task.get('processing_time', 0):.2f}s",
                        "Enhancements Applied": task.get('enhancements_applied', []),
                        "Created At": task.get('created_at'),
                        "Completed At": task.get('completed_at')
                    })
    
    # Processing History
    if st.session_state.processing_history:
        st.markdown("---")
        st.markdown("### 📜 Processing History")
        
        history_df = pd.DataFrame(st.session_state.processing_history)
        history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
        history_df = history_df.sort_values('timestamp', ascending=False)
        
        st.dataframe(
            history_df[['filename', 'timestamp', 'improvement']].head(10),
            use_container_width=True,
            hide_index=True
        )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray;'>
        <p>Audio Enhancement Pipeline v2.0 | Enterprise Edition</p>
        <p>Powered by Advanced AI Audio Processing</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()