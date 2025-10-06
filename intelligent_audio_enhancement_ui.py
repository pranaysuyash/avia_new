"""
Streamlit UI for Intelligent Audio Enhancement and Clarity Optimization

This module provides a user-friendly interface for the intelligent audio enhancement system,
allowing users to upload audio files, configure enhancement settings, and preview results.
"""

import streamlit as st
import numpy as np
import librosa
import soundfile as sf
import io
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, Any, Optional
import tempfile
import os

# Import the enhancement system
from intelligent_audio_enhancement import (
    IntelligentAudioEnhancer, EnhancementMode, QualityMetric,
    SpectralEnhancementConfig, DynamicRangeConfig, SpeechClarityConfig
)

def init_session_state():
    """Initialize session state variables"""
    if 'enhancement_results' not in st.session_state:
        st.session_state.enhancement_results = None
    if 'original_audio' not in st.session_state:
        st.session_state.original_audio = None
    if 'enhanced_audio' not in st.session_state:
        st.session_state.enhanced_audio = None
    if 'sample_rate' not in st.session_state:
        st.session_state.sample_rate = None

def create_audio_player(audio_data: np.ndarray, sample_rate: int, label: str):
    """Create an audio player widget"""
    # Convert to bytes for playback
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
        sf.write(tmp_file.name, audio_data, sample_rate)
        
        with open(tmp_file.name, 'rb') as audio_file:
            audio_bytes = audio_file.read()
        
        st.audio(audio_bytes, format='audio/wav', start_time=0)
        
        # Clean up temporary file
        os.unlink(tmp_file.name)

def plot_waveform_comparison(original: np.ndarray, enhanced: np.ndarray, 
                           sample_rate: int):
    """Create waveform comparison plot"""
    # Create time axis
    duration = len(original) / sample_rate
    time = np.linspace(0, duration, len(original))
    
    # Downsample for plotting if too long
    if len(time) > 10000:
        step = len(time) // 10000
        time = time[::step]
        original = original[::step]
        enhanced = enhanced[::step]
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Original Audio', 'Enhanced Audio'),
        vertical_spacing=0.1
    )
    
    # Original waveform
    fig.add_trace(
        go.Scatter(x=time, y=original, name='Original', line=dict(color='blue')),
        row=1, col=1
    )
    
    # Enhanced waveform
    fig.add_trace(
        go.Scatter(x=time, y=enhanced, name='Enhanced', line=dict(color='red')),
        row=2, col=1
    )
    
    fig.update_layout(
        title='Waveform Comparison',
        height=500,
        showlegend=False
    )
    
    fig.update_xaxes(title_text="Time (seconds)")
    fig.update_yaxes(title_text="Amplitude")
    
    return fig

def plot_spectrum_comparison(original: np.ndarray, enhanced: np.ndarray, 
                           sample_rate: int):
    """Create spectrum comparison plot"""
    # Compute FFT for both signals
    fft_original = np.fft.fft(original)
    fft_enhanced = np.fft.fft(enhanced)
    
    # Get frequency axis
    freqs = np.fft.fftfreq(len(original), 1/sample_rate)
    
    # Take only positive frequencies
    positive_freqs = freqs[:len(freqs)//2]
    magnitude_original = np.abs(fft_original[:len(freqs)//2])
    magnitude_enhanced = np.abs(fft_enhanced[:len(freqs)//2])
    
    # Convert to dB
    magnitude_original_db = 20 * np.log10(magnitude_original + 1e-10)
    magnitude_enhanced_db = 20 * np.log10(magnitude_enhanced + 1e-10)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=positive_freqs, y=magnitude_original_db,
        name='Original', line=dict(color='blue', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=positive_freqs, y=magnitude_enhanced_db,
        name='Enhanced', line=dict(color='red', width=2)
    ))
    
    fig.update_layout(
        title='Frequency Spectrum Comparison',
        xaxis_title='Frequency (Hz)',
        yaxis_title='Magnitude (dB)',
        xaxis_type='log',
        height=400
    )
    
    return fig

def plot_quality_metrics(initial_assessment, final_assessment):
    """Create quality metrics comparison chart"""
    metrics_data = []
    
    for metric in QualityMetric:
        initial_score = initial_assessment.metrics.get(metric, 0)
        final_score = final_assessment.metrics.get(metric, 0)
        
        metrics_data.append({
            'Metric': metric.value.replace('_', ' ').title(),
            'Initial': initial_score,
            'Enhanced': final_score,
            'Improvement': final_score - initial_score
        })
    
    df = pd.DataFrame(metrics_data)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Initial',
        x=df['Metric'],
        y=df['Initial'],
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Bar(
        name='Enhanced',
        x=df['Metric'],
        y=df['Enhanced'],
        marker_color='darkblue'
    ))
    
    fig.update_layout(
        title='Audio Quality Metrics Comparison',
        xaxis_title='Quality Metrics',
        yaxis_title='Score (0-1)',
        barmode='group',
        height=400
    )
    
    return fig

def create_enhancement_controls():
    """Create enhancement configuration controls"""
    st.subheader("Enhancement Configuration")
    
    # Enhancement mode selection
    mode_options = {
        'Automatic': EnhancementMode.AUTOMATIC,
        'Speech Focused': EnhancementMode.SPEECH_FOCUSED,
        'Music Focused': EnhancementMode.MUSIC_FOCUSED,
        'Broadcast': EnhancementMode.BROADCAST,
        'Custom': EnhancementMode.CUSTOM
    }
    
    selected_mode = st.selectbox(
        "Enhancement Mode",
        options=list(mode_options.keys()),
        help="Choose the enhancement mode based on your content type"
    )
    
    enhancement_mode = mode_options[selected_mode]
    
    # User preferences (shown for Custom mode or as overrides)
    user_preferences = {}
    
    if selected_mode == 'Custom' or st.checkbox("Show Advanced Settings"):
        st.subheader("Advanced Settings")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**Enhancement Intensities**")
            spectral_intensity = st.slider(
                "Spectral Enhancement", 0.5, 2.0, 1.0, 0.1,
                help="Adjust frequency-specific processing intensity"
            )
            dynamic_intensity = st.slider(
                "Dynamic Processing", 0.5, 2.0, 1.0, 0.1,
                help="Adjust compression and loudness processing"
            )
            clarity_intensity = st.slider(
                "Speech Clarity", 0.5, 2.0, 1.0, 0.1,
                help="Adjust speech intelligibility enhancement"
            )
        
        with col2:
            st.write("**Processing Options**")
            disable_spectral = st.checkbox("Disable Spectral Enhancement")
            disable_dynamic = st.checkbox("Disable Dynamic Processing")
            disable_clarity = st.checkbox("Disable Speech Clarity")
        
        with col3:
            st.write("**Target Settings**")
            target_lufs = st.slider(
                "Target Loudness (LUFS)", -30.0, -10.0, -23.0, 1.0,
                help="Target loudness level for broadcast compliance"
            )
            compression_ratio = st.slider(
                "Compression Ratio", 1.0, 5.0, 2.5, 0.1,
                help="Dynamic range compression ratio"
            )
        
        # Build user preferences
        user_preferences = {
            'spectral_intensity': spectral_intensity,
            'dynamic_intensity': dynamic_intensity,
            'clarity_intensity': clarity_intensity,
            'disable_spectral': disable_spectral,
            'disable_dynamic': disable_dynamic,
            'disable_clarity': disable_clarity,
            'target_lufs': target_lufs,
            'compression_ratio': compression_ratio
        }
    
    return enhancement_mode, user_preferences

def display_quality_assessment(assessment, title):
    """Display quality assessment results"""
    st.subheader(title)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Overall score
        score_color = 'green' if assessment.overall_score > 0.8 else 'orange' if assessment.overall_score > 0.6 else 'red'
        st.metric(
            "Overall Quality Score",
            f"{assessment.overall_score:.3f}",
            delta=None
        )
        
        st.metric(
            "Processing Confidence",
            f"{assessment.processing_confidence:.3f}",
            delta=None
        )
    
    with col2:
        # Individual metrics
        st.write("**Quality Metrics:**")
        for metric, value in assessment.metrics.items():
            metric_name = metric.value.replace('_', ' ').title()
            st.write(f"• {metric_name}: {value:.3f}")
    
    # Recommendations
    if assessment.recommendations:
        st.write("**Recommendations:**")
        for i, recommendation in enumerate(assessment.recommendations, 1):
            st.write(f"{i}. {recommendation}")

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Intelligent Audio Enhancement",
        page_icon="🎵",
        layout="wide"
    )
    
    st.title("🎵 Intelligent Audio Enhancement & Clarity Optimization")
    st.markdown("Advanced audio processing with spectral enhancement, dynamic range optimization, and speech clarity improvement.")
    
    # Initialize session state
    init_session_state()
    
    # Sidebar for file upload and controls
    with st.sidebar:
        st.header("Audio Upload")
        
        uploaded_file = st.file_uploader(
            "Choose an audio file",
            type=['wav', 'mp3', 'flac', 'm4a', 'ogg'],
            help="Upload an audio file for enhancement"
        )
        
        if uploaded_file is not None:
            try:
                # Load audio file
                audio_data, sample_rate = librosa.load(uploaded_file, sr=None)
                st.session_state.original_audio = audio_data
                st.session_state.sample_rate = sample_rate
                
                st.success(f"Audio loaded successfully!")
                st.write(f"Duration: {len(audio_data)/sample_rate:.2f} seconds")
                st.write(f"Sample Rate: {sample_rate} Hz")
                st.write(f"Channels: {'Mono' if audio_data.ndim == 1 else 'Stereo'}")
                
            except Exception as e:
                st.error(f"Error loading audio file: {e}")
    
    # Main content area
    if st.session_state.original_audio is not None:
        
        # Enhancement controls
        enhancement_mode, user_preferences = create_enhancement_controls()
        
        # Process button
        if st.button("🚀 Enhance Audio", type="primary"):
            with st.spinner("Processing audio enhancement..."):
                try:
                    # Initialize enhancer
                    enhancer = IntelligentAudioEnhancer()
                    
                    # Process audio
                    results = enhancer.enhance_audio(
                        st.session_state.original_audio,
                        st.session_state.sample_rate,
                        enhancement_mode,
                        user_preferences if user_preferences else None
                    )
                    
                    # Store results
                    st.session_state.enhancement_results = results
                    st.session_state.enhanced_audio = results['enhanced_audio']
                    
                    st.success("Audio enhancement completed!")
                    
                except Exception as e:
                    st.error(f"Error during enhancement: {e}")
        
        # Display results if available
        if st.session_state.enhancement_results is not None:
            results = st.session_state.enhancement_results
            
            # Audio playback section
            st.header("🎧 Audio Playback")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Original Audio")
                create_audio_player(
                    st.session_state.original_audio,
                    st.session_state.sample_rate,
                    "Original"
                )
            
            with col2:
                st.subheader("Enhanced Audio")
                create_audio_player(
                    st.session_state.enhanced_audio,
                    st.session_state.sample_rate,
                    "Enhanced"
                )
            
            # Quality assessment comparison
            st.header("📊 Quality Assessment")
            
            col1, col2 = st.columns(2)
            
            with col1:
                display_quality_assessment(
                    results['initial_assessment'],
                    "Initial Quality"
                )
            
            with col2:
                display_quality_assessment(
                    results['final_assessment'],
                    "Enhanced Quality"
                )
            
            # Improvement summary
            improvement = results['improvement']
            improvement_color = 'green' if improvement > 0 else 'red'
            
            st.metric(
                "Overall Improvement",
                f"{improvement:+.3f}",
                delta=f"{improvement:+.3f}",
                delta_color='normal'
            )
            
            # Processing information
            st.subheader("Processing Information")
            st.write(f"**Processing Steps:** {', '.join(results['processing_steps'])}")
            
            # Visualizations
            st.header("📈 Analysis & Visualization")
            
            # Tabs for different visualizations
            tab1, tab2, tab3 = st.tabs(["Waveform Comparison", "Spectrum Analysis", "Quality Metrics"])
            
            with tab1:
                waveform_fig = plot_waveform_comparison(
                    st.session_state.original_audio,
                    st.session_state.enhanced_audio,
                    st.session_state.sample_rate
                )
                st.plotly_chart(waveform_fig, use_container_width=True)
            
            with tab2:
                spectrum_fig = plot_spectrum_comparison(
                    st.session_state.original_audio,
                    st.session_state.enhanced_audio,
                    st.session_state.sample_rate
                )
                st.plotly_chart(spectrum_fig, use_container_width=True)
            
            with tab3:
                metrics_fig = plot_quality_metrics(
                    results['initial_assessment'],
                    results['final_assessment']
                )
                st.plotly_chart(metrics_fig, use_container_width=True)
            
            # Download section
            st.header("💾 Download Enhanced Audio")
            
            # Create download button
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                sf.write(tmp_file.name, st.session_state.enhanced_audio, st.session_state.sample_rate)
                
                with open(tmp_file.name, 'rb') as file:
                    audio_bytes = file.read()
                
                st.download_button(
                    label="Download Enhanced Audio (WAV)",
                    data=audio_bytes,
                    file_name="enhanced_audio.wav",
                    mime="audio/wav"
                )
                
                # Clean up
                os.unlink(tmp_file.name)
    
    else:
        # Welcome message
        st.info("👆 Please upload an audio file using the sidebar to get started.")
        
        # Feature overview
        st.header("🌟 Features")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("🎛️ Spectral Enhancement")
            st.write("Frequency-specific processing to balance and enhance audio spectrum")
        
        with col2:
            st.subheader("🔊 Dynamic Optimization")
            st.write("Intelligent compression and loudness management for broadcast quality")
        
        with col3:
            st.subheader("🗣️ Speech Clarity")
            st.write("Advanced speech enhancement for improved intelligibility")
        
        # Enhancement modes
        st.header("🎯 Enhancement Modes")
        
        modes_info = {
            "Automatic": "AI-driven enhancement based on audio analysis",
            "Speech Focused": "Optimized for voice recordings and podcasts",
            "Music Focused": "Tailored for musical content and instruments",
            "Broadcast": "Compliant with broadcast standards and regulations",
            "Custom": "Full control over all enhancement parameters"
        }
        
        for mode, description in modes_info.items():
            st.write(f"**{mode}:** {description}")

if __name__ == "__main__":
    main()