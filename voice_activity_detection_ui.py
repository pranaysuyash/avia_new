"""
Voice Activity Detection (VAD) System - Streamlit UI
Provides a comprehensive interface for voice activity detection, silence removal,
and audio quality assessment
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import librosa
import soundfile as sf
import tempfile
import os
from datetime import datetime
import json
import sqlite3
from voice_activity_detection import (
    VoiceActivityDetector, VADMethod, VADMode, 
    VADResult, AudioQualityMetrics
)

# Page configuration
st.set_page_config(
    page_title="Voice Activity Detection System",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'vad_detector' not in st.session_state:
        st.session_state.vad_detector = VoiceActivityDetector()
    if 'vad_results' not in st.session_state:
        st.session_state.vad_results = {}
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = []

def display_audio_player(audio_file, label="Audio"):
    """Display audio player with waveform"""
    try:
        audio_bytes = open(audio_file, 'rb').read()
        st.audio(audio_bytes, format='audio/wav')
        
        # Load and display basic info
        audio, sr = librosa.load(audio_file, sr=None)
        duration = len(audio) / sr
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Duration", f"{duration:.2f}s")
        with col2:
            st.metric("Sample Rate", f"{sr} Hz")
        with col3:
            st.metric("Channels", "Mono")
            
    except Exception as e:
        st.error(f"Error loading audio: {e}")

def create_vad_visualization(audio_file, vad_result):
    """Create interactive VAD visualization"""
    try:
        # Load audio
        audio, sr = librosa.load(audio_file, sr=None)
        time_axis = np.linspace(0, len(audio) / sr, len(audio))
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=('Audio Waveform with VAD', 'VAD Segments', 'Confidence Over Time'),
            vertical_spacing=0.08,
            specs=[[{"secondary_y": False}],
                   [{"secondary_y": False}],
                   [{"secondary_y": False}]]
        )
        
        # Plot waveform
        fig.add_trace(
            go.Scatter(
                x=time_axis,
                y=audio,
                mode='lines',
                name='Waveform',
                line=dict(color='blue', width=1),
                opacity=0.7
            ),
            row=1, col=1
        )
        
        # Add VAD segments to waveform
        for i, segment in enumerate(vad_result.segments):
            color = 'green' if segment.is_speech else 'red'
            opacity = segment.confidence if segment.confidence else 0.3
            
            fig.add_vrect(
                x0=segment.start_time,
                x1=segment.end_time,
                fillcolor=color,
                opacity=opacity * 0.3,
                layer="below",
                line_width=0,
                row=1, col=1
            )
        
        # Plot VAD segments as bars
        segment_times = []
        segment_values = []
        segment_colors = []
        segment_text = []
        
        for segment in vad_result.segments:
            segment_times.append(segment.start_time + segment.duration / 2)
            segment_values.append(1 if segment.is_speech else 0)
            segment_colors.append('green' if segment.is_speech else 'red')
            segment_text.append(
                f"{'Speech' if segment.is_speech else 'Silence'}<br>"
                f"Duration: {segment.duration:.2f}s<br>"
                f"Confidence: {segment.confidence:.2f}"
            )
        
        fig.add_trace(
            go.Bar(
                x=segment_times,
                y=segment_values,
                width=[seg.duration for seg in vad_result.segments],
                marker_color=segment_colors,
                name='VAD Segments',
                text=segment_text,
                hovertemplate='%{text}<extra></extra>',
                opacity=0.7
            ),
            row=2, col=1
        )
        
        # Plot confidence over time
        confidence_times = []
        confidences = []
        colors = []
        
        for segment in vad_result.segments:
            confidence_times.extend([segment.start_time, segment.end_time])
            confidences.extend([segment.confidence, segment.confidence])
            colors.extend(['green' if segment.is_speech else 'red'] * 2)
        
        if confidence_times:
            fig.add_trace(
                go.Scatter(
                    x=confidence_times,
                    y=confidences,
                    mode='lines+markers',
                    name='Confidence',
                    line=dict(color='purple', width=2),
                    marker=dict(size=4)
                ),
                row=3, col=1
            )
        
        # Update layout
        fig.update_layout(
            height=800,
            title_text="Voice Activity Detection Results",
            showlegend=True,
            template="plotly_white"
        )
        
        fig.update_xaxes(title_text="Time (seconds)", row=3, col=1)
        fig.update_yaxes(title_text="Amplitude", row=1, col=1)
        fig.update_yaxes(title_text="Speech/Silence", row=2, col=1)
        fig.update_yaxes(title_text="Confidence", row=3, col=1, range=[0, 1])
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating visualization: {e}")
        return None

def display_vad_results(vad_result):
    """Display VAD results in a formatted way"""
    st.subheader("📊 VAD Analysis Results")
    
    # Main metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h4>Total Duration</h4>
            <h2>{:.2f}s</h2>
        </div>
        """.format(vad_result.total_duration), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h4>Speech Duration</h4>
            <h2>{:.2f}s</h2>
        </div>
        """.format(vad_result.speech_duration), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h4>Speech Ratio</h4>
            <h2>{:.1%}</h2>
        </div>
        """.format(vad_result.speech_ratio), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h4>Quality Score</h4>
            <h2>{:.1f}/100</h2>
        </div>
        """.format(vad_result.quality_score), unsafe_allow_html=True)
    
    # Detailed segments
    st.subheader("🎯 Detected Segments")
    
    segments_data = []
    for i, segment in enumerate(vad_result.segments):
        segments_data.append({
            'Segment': i + 1,
            'Type': 'Speech' if segment.is_speech else 'Silence',
            'Start Time (s)': f"{segment.start_time:.2f}",
            'End Time (s)': f"{segment.end_time:.2f}",
            'Duration (s)': f"{segment.duration:.2f}",
            'Confidence': f"{segment.confidence:.2f}",
            'Method': segment.method
        })
    
    if segments_data:
        df = pd.DataFrame(segments_data)
        
        # Color code the dataframe
        def highlight_speech(row):
            if row['Type'] == 'Speech':
                return ['background-color: #d4edda'] * len(row)
            else:
                return ['background-color: #f8d7da'] * len(row)
        
        st.dataframe(
            df.style.apply(highlight_speech, axis=1),
            use_container_width=True,
            hide_index=True
        )
        
        # Summary statistics
        speech_segments = [seg for seg in vad_result.segments if seg.is_speech]
        silence_segments = [seg for seg in vad_result.segments if not seg.is_speech]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Speech Segments:**")
            st.write(f"• Count: {len(speech_segments)}")
            if speech_segments:
                st.write(f"• Average Duration: {np.mean([seg.duration for seg in speech_segments]):.2f}s")
                st.write(f"• Average Confidence: {np.mean([seg.confidence for seg in speech_segments]):.2f}")
        
        with col2:
            st.markdown("**Silence Segments:**")
            st.write(f"• Count: {len(silence_segments)}")
            if silence_segments:
                st.write(f"• Average Duration: {np.mean([seg.duration for seg in silence_segments]):.2f}s")
                st.write(f"• Average Confidence: {np.mean([seg.confidence for seg in silence_segments]):.2f}")

def display_quality_metrics(audio_file):
    """Display audio quality metrics"""
    try:
        # Load audio and assess quality
        audio, sr = librosa.load(audio_file, sr=None)
        quality_metrics = st.session_state.vad_detector.assess_audio_quality(audio, sr)
        
        st.subheader("🔊 Audio Quality Assessment")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("SNR", f"{quality_metrics.snr_db:.1f} dB")
            st.metric("THD", f"{quality_metrics.thd_percent:.2f}%")
            st.metric("Dynamic Range", f"{quality_metrics.dynamic_range_db:.1f} dB")
        
        with col2:
            st.metric("Spectral Centroid", f"{quality_metrics.spectral_centroid_hz:.0f} Hz")
            st.metric("Spectral Rolloff", f"{quality_metrics.spectral_rolloff_hz:.0f} Hz")
            st.metric("Zero Crossing Rate", f"{quality_metrics.zero_crossing_rate:.4f}")
        
        with col3:
            st.metric("Energy Entropy", f"{quality_metrics.energy_entropy:.2f}")
            st.metric("Spectral Entropy", f"{quality_metrics.spectral_entropy:.2f}")
        
        # MFCC visualization
        if quality_metrics.mfcc_features:
            st.subheader("📈 MFCC Features")
            mfcc_df = pd.DataFrame({
                'MFCC Coefficient': [f'MFCC {i}' for i in range(len(quality_metrics.mfcc_features))],
                'Value': quality_metrics.mfcc_features
            })
            
            fig = px.bar(mfcc_df, x='MFCC Coefficient', y='Value', 
                        title='MFCC Feature Values')
            st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error assessing audio quality: {e}")

def main():
    """Main Streamlit application"""
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🎤 Voice Activity Detection System</h1>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <strong>Voice Activity Detection (VAD)</strong> automatically identifies speech and silence 
        segments in audio recordings. This system uses multiple algorithms including WebRTC VAD, 
        pyAudioAnalysis, energy-based detection, and machine learning approaches.
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.header("⚙️ Configuration")
    
    # VAD method selection
    vad_method = st.sidebar.selectbox(
        "VAD Method",
        options=[method.value for method in VADMethod],
        index=6,  # Default to ensemble
        help="Choose the voice activity detection method"
    )
    
    # WebRTC VAD mode (if WebRTC is selected)
    if vad_method == VADMethod.WEBRTC.value:
        vad_mode = st.sidebar.selectbox(
            "WebRTC VAD Mode",
            options=[mode.value for mode in VADMode],
            index=2,  # Default to normal
            help="WebRTC VAD aggressiveness mode"
        )
    
    # Processing options
    st.sidebar.subheader("Processing Options")
    remove_silence = st.sidebar.checkbox("Remove Silence", value=False)
    padding_ms = st.sidebar.slider("Padding (ms)", 0, 500, 100, 
                                  help="Padding around speech segments")
    
    # Visualization options
    st.sidebar.subheader("Visualization")
    show_waveform = st.sidebar.checkbox("Show Waveform", value=True)
    show_spectrogram = st.sidebar.checkbox("Show Spectrogram", value=False)
    show_quality_metrics = st.sidebar.checkbox("Show Quality Metrics", value=True)
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🎵 Audio Processing", "📊 Results Analysis", 
                                      "📈 Statistics", "⚙️ System Info"])
    
    with tab1:
        st.header("Audio Upload and Processing")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose an audio file",
            type=['wav', 'mp3', 'flac', 'm4a', 'ogg'],
            help="Upload an audio file for voice activity detection"
        )
        
        if uploaded_file is not None:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                tmp_file.write(uploaded_file.read())
                temp_audio_path = tmp_file.name
            
            st.success(f"✅ Audio file uploaded: {uploaded_file.name}")
            
            # Display audio player
            st.subheader("🎵 Original Audio")
            display_audio_player(temp_audio_path, "Original Audio")
            
            # Process button
            if st.button("🚀 Start VAD Processing", type="primary"):
                with st.spinner("Processing audio with VAD..."):
                    try:
                        # Convert VAD method string to enum
                        method_enum = VADMethod(vad_method)
                        
                        # Perform VAD
                        vad_result = st.session_state.vad_detector.detect_voice_activity(
                            temp_audio_path, method_enum
                        )
                        
                        # Store results
                        st.session_state.vad_results[uploaded_file.name] = vad_result
                        st.session_state.processed_files.append(uploaded_file.name)
                        
                        st.success(f"✅ VAD processing completed in {vad_result.processing_time:.2f}s")
                        
                        # Display results
                        display_vad_results(vad_result)
                        
                        # Create and display visualization
                        if show_waveform:
                            st.subheader("📊 VAD Visualization")
                            fig = create_vad_visualization(temp_audio_path, vad_result)
                            if fig:
                                st.plotly_chart(fig, use_container_width=True)
                        
                        # Display quality metrics
                        if show_quality_metrics:
                            display_quality_metrics(temp_audio_path)
                        
                        # Remove silence if requested
                        if remove_silence:
                            st.subheader("🔇 Silence Removal")
                            with st.spinner("Removing silence..."):
                                output_path = temp_audio_path.replace('.wav', '_processed.wav')
                                processed_file = st.session_state.vad_detector.remove_silence(
                                    temp_audio_path, output_path, method_enum, padding_ms
                                )
                                
                                if os.path.exists(processed_file):
                                    st.success("✅ Silence removed successfully")
                                    
                                    # Display processed audio
                                    st.subheader("🎵 Processed Audio (Silence Removed)")
                                    display_audio_player(processed_file, "Processed Audio")
                                    
                                    # Download button
                                    with open(processed_file, 'rb') as f:
                                        st.download_button(
                                            label="📥 Download Processed Audio",
                                            data=f.read(),
                                            file_name=f"processed_{uploaded_file.name}",
                                            mime="audio/wav"
                                        )
                        
                    except Exception as e:
                        st.error(f"❌ VAD processing failed: {e}")
            
            # Clean up temporary file
            try:
                os.unlink(temp_audio_path)
            except:
                pass
    
    with tab2:
        st.header("Results Analysis")
        
        if st.session_state.vad_results:
            # File selection for analysis
            selected_file = st.selectbox(
                "Select file for detailed analysis",
                options=list(st.session_state.vad_results.keys())
            )
            
            if selected_file:
                vad_result = st.session_state.vad_results[selected_file]
                
                # Detailed analysis
                st.subheader(f"📋 Analysis for {selected_file}")
                display_vad_results(vad_result)
                
                # Comparison with other methods
                st.subheader("🔄 Method Comparison")
                st.info("Upload the same file and process with different methods to compare results")
                
        else:
            st.info("👆 Process some audio files first to see analysis results")
    
    with tab3:
        st.header("System Statistics")
        
        # Get VAD statistics
        stats = st.session_state.vad_detector.get_vad_statistics()
        
        if stats and stats.get('method_statistics'):
            st.subheader("📊 Processing Statistics by Method")
            
            method_data = []
            for stat in stats['method_statistics']:
                method_data.append({
                    'Method': stat[4],
                    'Files Processed': stat[0],
                    'Avg Speech Ratio': f"{stat[1]:.2%}" if stat[1] else "N/A",
                    'Avg Quality Score': f"{stat[2]:.1f}" if stat[2] else "N/A",
                    'Avg Processing Time': f"{stat[3]:.3f}s" if stat[3] else "N/A"
                })
            
            df_stats = pd.DataFrame(method_data)
            st.dataframe(df_stats, use_container_width=True, hide_index=True)
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Files processed by method
                fig_files = px.bar(df_stats, x='Method', y='Files Processed',
                                 title='Files Processed by Method')
                st.plotly_chart(fig_files, use_container_width=True)
            
            with col2:
                # Processing time by method
                processing_times = [float(stat[3]) if stat[3] else 0 for stat in stats['method_statistics']]
                methods = [stat[4] for stat in stats['method_statistics']]
                
                fig_time = px.bar(x=methods, y=processing_times,
                                title='Average Processing Time by Method',
                                labels={'x': 'Method', 'y': 'Time (seconds)'})
                st.plotly_chart(fig_time, use_container_width=True)
        
        # Recent activity
        if stats and stats.get('recent_activity'):
            st.subheader("🕒 Recent Activity")
            
            recent_data = []
            for activity in stats['recent_activity']:
                recent_data.append({
                    'File': os.path.basename(activity[0]),
                    'Method': activity[1],
                    'Speech Ratio': f"{activity[2]:.2%}" if activity[2] else "N/A",
                    'Quality Score': f"{activity[3]:.1f}" if activity[3] else "N/A",
                    'Processed At': activity[4]
                })
            
            df_recent = pd.DataFrame(recent_data)
            st.dataframe(df_recent, use_container_width=True, hide_index=True)
        
        # System performance
        st.subheader("⚡ System Performance")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_files = stats.get('total_processed_files', 0)
            st.metric("Total Files Processed", total_files)
        
        with col2:
            if st.session_state.vad_results:
                avg_processing_time = np.mean([
                    result.processing_time for result in st.session_state.vad_results.values()
                ])
                st.metric("Avg Processing Time", f"{avg_processing_time:.3f}s")
            else:
                st.metric("Avg Processing Time", "N/A")
        
        with col3:
            if st.session_state.vad_results:
                avg_speech_ratio = np.mean([
                    result.speech_ratio for result in st.session_state.vad_results.values()
                ])
                st.metric("Avg Speech Ratio", f"{avg_speech_ratio:.1%}")
            else:
                st.metric("Avg Speech Ratio", "N/A")
    
    with tab4:
        st.header("System Information")
        
        # VAD methods info
        st.subheader("🔧 Available VAD Methods")
        
        method_info = {
            'WebRTC': {
                'description': 'Google WebRTC Voice Activity Detection',
                'pros': 'Fast, lightweight, real-time capable',
                'cons': 'Limited to 16kHz, basic features',
                'use_case': 'Real-time applications, low latency'
            },
            'pyAudioAnalysis': {
                'description': 'Python audio analysis library',
                'pros': 'Good accuracy, multiple features',
                'cons': 'Slower processing, more complex',
                'use_case': 'Offline processing, high accuracy needed'
            },
            'Energy-based': {
                'description': 'Simple energy threshold detection',
                'pros': 'Very fast, simple implementation',
                'cons': 'Sensitive to noise, basic accuracy',
                'use_case': 'Quick processing, clean audio'
            },
            'ML Classifier': {
                'description': 'Machine learning based detection',
                'pros': 'Adaptable, good accuracy with training',
                'cons': 'Requires training data, more complex',
                'use_case': 'Custom domains, specific requirements'
            },
            'Ensemble': {
                'description': 'Combination of multiple methods',
                'pros': 'Best overall accuracy, robust',
                'cons': 'Slower processing, more complex',
                'use_case': 'High accuracy requirements, mixed audio'
            }
        }
        
        for method, info in method_info.items():
            with st.expander(f"📋 {method} Method"):
                st.write(f"**Description:** {info['description']}")
                st.write(f"**Pros:** {info['pros']}")
                st.write(f"**Cons:** {info['cons']}")
                st.write(f"**Best Use Case:** {info['use_case']}")
        
        # System requirements
        st.subheader("💻 System Requirements")
        st.markdown("""
        **Required Libraries:**
        - librosa (audio processing)
        - webrtcvad (WebRTC VAD)
        - pyAudioAnalysis (audio analysis)
        - scikit-learn (machine learning)
        - torch (deep learning)
        - soundfile (audio I/O)
        
        **Recommended Hardware:**
        - CPU: Multi-core processor for faster processing
        - RAM: 4GB+ for large audio files
        - Storage: SSD for better I/O performance
        """)
        
        # Database info
        st.subheader("🗄️ Database Information")
        try:
            conn = sqlite3.connect(st.session_state.vad_detector.db_path)
            cursor = conn.cursor()
            
            # Get table sizes
            cursor.execute("SELECT COUNT(*) FROM vad_results")
            vad_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM audio_quality")
            quality_count = cursor.fetchone()[0]
            
            conn.close()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("VAD Results Stored", vad_count)
            with col2:
                st.metric("Quality Assessments", quality_count)
                
        except Exception as e:
            st.error(f"Database error: {e}")

if __name__ == "__main__":
    main()