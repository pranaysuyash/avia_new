"""
Advanced Noise Reduction System UI

Streamlit interface for the advanced noise reduction and audio restoration system.
Provides professional-grade controls for noise reduction, artifact removal, 
spectral enhancement, and AI-powered audio reconstruction.
"""

import streamlit as st
import numpy as np
import librosa
import soundfile as sf
import io
import time
from typing import Optional, Dict, Any
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from advanced_noise_reduction_system import (
    AdvancedNoiseReductionSystem,
    RestorationSettings,
    NoiseType,
    ArtifactType
)

def init_session_state():
    """Initialize session state variables"""
    if 'noise_reduction_system' not in st.session_state:
        st.session_state.noise_reduction_system = AdvancedNoiseReductionSystem()
    
    if 'processed_audio' not in st.session_state:
        st.session_state.processed_audio = None
    
    if 'original_audio' not in st.session_state:
        st.session_state.original_audio = None
    
    if 'sample_rate' not in st.session_state:
        st.session_state.sample_rate = 44100
    
    if 'restoration_result' not in st.session_state:
        st.session_state.restoration_result = None

def create_audio_visualization(audio: np.ndarray, sr: int, title: str) -> go.Figure:
    """Create audio waveform and spectrogram visualization"""
    
    # Create time axis
    time_axis = np.linspace(0, len(audio) / sr, len(audio))
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=[f'{title} - Waveform', f'{title} - Spectrogram'],
        vertical_spacing=0.1
    )
    
    # Waveform
    fig.add_trace(
        go.Scatter(
            x=time_axis,
            y=audio,
            mode='lines',
            name='Amplitude',
            line=dict(color='blue', width=1)
        ),
        row=1, col=1
    )
    
    # Spectrogram
    try:
        stft = librosa.stft(audio, n_fft=2048, hop_length=512)
        magnitude_db = librosa.amplitude_to_db(np.abs(stft))
        
        times = librosa.frames_to_time(np.arange(magnitude_db.shape[1]), sr=sr, hop_length=512)
        frequencies = librosa.fft_frequencies(sr=sr, n_fft=2048)
        
        fig.add_trace(
            go.Heatmap(
                x=times,
                y=frequencies[:magnitude_db.shape[0]//4],  # Show only lower frequencies for clarity
                z=magnitude_db[:magnitude_db.shape[0]//4],
                colorscale='Viridis',
                name='Magnitude (dB)',
                showscale=True
            ),
            row=2, col=1
        )
    except Exception as e:
        st.warning(f"Could not generate spectrogram: {e}")
    
    # Update layout
    fig.update_layout(
        height=600,
        title_text=title,
        showlegend=False
    )
    
    fig.update_xaxes(title_text="Time (s)", row=1, col=1)
    fig.update_yaxes(title_text="Amplitude", row=1, col=1)
    fig.update_xaxes(title_text="Time (s)", row=2, col=1)
    fig.update_yaxes(title_text="Frequency (Hz)", row=2, col=1)
    
    return fig

def create_noise_analysis_display(noise_profile, artifacts: Dict) -> None:
    """Display noise analysis results"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔍 Noise Analysis")
        
        if noise_profile:
            st.metric("Noise Type", noise_profile.noise_type.value.title())
            st.metric("Confidence", f"{noise_profile.confidence:.2%}")
            st.metric("Recommended Reduction", f"{noise_profile.recommended_reduction:.1%}")
            
            # Temporal characteristics
            if noise_profile.temporal_characteristics:
                st.write("**Temporal Characteristics:**")
                for key, value in noise_profile.temporal_characteristics.items():
                    if isinstance(value, float):
                        st.write(f"- {key.replace('_', ' ').title()}: {value:.3f}")
    
    with col2:
        st.subheader("⚠️ Detected Artifacts")
        
        if artifacts:
            for artifact_type, locations in artifacts.items():
                st.write(f"**{artifact_type.value.title()}:** {len(locations)} detected")
                
                # Show some details for different artifact types
                if artifact_type == ArtifactType.HUMS and locations:
                    st.write(f"  - Frequencies: {', '.join([f'{f:.0f} Hz' for f in locations[:5]])}")
                elif artifact_type == ArtifactType.BUZZES and locations:
                    st.write(f"  - Frequencies: {', '.join([f'{f:.0f} Hz' for f in locations[:5]])}")
                elif artifact_type == ArtifactType.CLICKS and locations:
                    st.write(f"  - Click groups: {len(locations)}")
                elif artifact_type == ArtifactType.CLIPPING and locations:
                    st.write(f"  - Clipped regions: {len(locations)}")
        else:
            st.info("No significant artifacts detected")

def create_quality_metrics_display(result) -> None:
    """Display quality improvement metrics"""
    
    if not result or not result.quality_improvement:
        return
    
    st.subheader("📊 Quality Improvements")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Processing Time", 
            f"{result.processing_time:.2f}s"
        )
        
        st.metric(
            "Confidence Score",
            f"{result.confidence_score:.2%}"
        )
    
    with col2:
        st.metric(
            "Noise Reduction",
            f"{result.noise_reduction_applied:.1%}"
        )
        
        artifacts_count = len(result.artifacts_removed)
        st.metric(
            "Artifacts Removed",
            f"{artifacts_count} types"
        )
    
    with col3:
        improvements = result.quality_improvement
        
        if 'segments_reconstructed' in improvements:
            st.metric(
                "Segments Reconstructed",
                improvements['segments_reconstructed']
            )
        
        if 'spectral_enhancement' in improvements:
            st.success("✅ Spectral Enhancement Applied")
        
        if 'dynamic_range_optimized' in improvements:
            st.success("✅ Dynamic Range Optimized")

def create_advanced_settings_panel() -> RestorationSettings:
    """Create advanced settings panel"""
    
    st.subheader("⚙️ Advanced Settings")
    
    with st.expander("Noise Reduction Settings", expanded=True):
        noise_strength = st.slider(
            "Noise Reduction Strength",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Higher values provide more aggressive noise reduction"
        )
        
        preserve_speech = st.checkbox(
            "Preserve Speech Quality",
            value=True,
            help="Protect speech regions from over-processing"
        )
    
    with st.expander("Artifact Removal Settings"):
        artifact_sensitivity = st.slider(
            "Artifact Detection Sensitivity",
            min_value=0.0,
            max_value=1.0,
            value=0.8,
            step=0.1,
            help="Higher values detect more subtle artifacts"
        )
    
    with st.expander("Enhancement Settings"):
        spectral_enhancement = st.checkbox(
            "Spectral Enhancement",
            value=True,
            help="Enhance frequency response for better clarity"
        )
        
        dynamic_range_opt = st.checkbox(
            "Dynamic Range Optimization",
            value=True,
            help="Optimize loudness and dynamic range"
        )
        
        ai_reconstruction = st.checkbox(
            "AI-Powered Reconstruction",
            value=True,
            help="Reconstruct missing or damaged audio segments"
        )
    
    processing_mode = st.selectbox(
        "Processing Mode",
        options=["adaptive", "conservative", "aggressive"],
        index=0,
        help="Choose processing approach"
    )
    
    return RestorationSettings(
        noise_reduction_strength=noise_strength,
        preserve_speech_quality=preserve_speech,
        artifact_removal_sensitivity=artifact_sensitivity,
        spectral_enhancement=spectral_enhancement,
        dynamic_range_optimization=dynamic_range_opt,
        ai_reconstruction=ai_reconstruction,
        processing_mode=processing_mode
    )

def export_processed_audio(audio: np.ndarray, sr: int, filename: str) -> bytes:
    """Export processed audio to bytes"""
    buffer = io.BytesIO()
    sf.write(buffer, audio, sr, format='WAV')
    buffer.seek(0)
    return buffer.getvalue()

def main():
    """Main Streamlit application"""
    
    st.set_page_config(
        page_title="Advanced Noise Reduction System",
        page_icon="🎵",
        layout="wide"
    )
    
    init_session_state()
    
    st.title("🎵 Advanced Noise Reduction & Audio Restoration")
    st.markdown("Professional-grade audio processing with adaptive noise reduction, artifact removal, and AI-powered reconstruction")
    
    # Sidebar for file upload and settings
    with st.sidebar:
        st.header("📁 Audio Input")
        
        uploaded_file = st.file_uploader(
            "Upload Audio File",
            type=['wav', 'mp3', 'flac', 'm4a', 'ogg'],
            help="Upload an audio file for processing"
        )
        
        if uploaded_file is not None:
            try:
                # Load audio file
                audio_data, sr = librosa.load(uploaded_file, sr=None)
                st.session_state.original_audio = audio_data
                st.session_state.sample_rate = sr
                
                st.success(f"✅ Audio loaded: {len(audio_data)/sr:.1f}s @ {sr} Hz")
                
                # Play original audio
                st.audio(uploaded_file, format='audio/wav')
                
            except Exception as e:
                st.error(f"Error loading audio: {e}")
        
        # Generate test audio option
        st.header("🧪 Test Audio")
        if st.button("Generate Test Audio"):
            from advanced_noise_reduction_system import create_test_audio
            test_audio = create_test_audio(duration=3.0, sr=44100)
            st.session_state.original_audio = test_audio
            st.session_state.sample_rate = 44100
            st.success("✅ Test audio generated")
    
    # Main content area
    if st.session_state.original_audio is not None:
        
        # Settings panel
        settings = create_advanced_settings_panel()
        
        # Processing button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Process Audio", type="primary", use_container_width=True):
                
                with st.spinner("Processing audio... This may take a moment."):
                    
                    # Process audio
                    result = st.session_state.noise_reduction_system.process_audio(
                        st.session_state.original_audio,
                        st.session_state.sample_rate,
                        settings
                    )
                    
                    st.session_state.restoration_result = result
                    st.session_state.processed_audio = result.restored_audio
                
                st.success("✅ Audio processing completed!")
        
        # Display results if available
        if st.session_state.restoration_result is not None:
            
            result = st.session_state.restoration_result
            
            # Quality metrics
            create_quality_metrics_display(result)
            
            # Audio comparison
            st.subheader("🎧 Audio Comparison")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Original Audio**")
                original_bytes = export_processed_audio(
                    st.session_state.original_audio,
                    st.session_state.sample_rate,
                    "original.wav"
                )
                st.audio(original_bytes, format='audio/wav')
            
            with col2:
                st.write("**Processed Audio**")
                processed_bytes = export_processed_audio(
                    st.session_state.processed_audio,
                    st.session_state.sample_rate,
                    "processed.wav"
                )
                st.audio(processed_bytes, format='audio/wav')
                
                # Download button
                st.download_button(
                    label="📥 Download Processed Audio",
                    data=processed_bytes,
                    file_name="restored_audio.wav",
                    mime="audio/wav"
                )
            
            # Visualizations
            st.subheader("📈 Audio Analysis")
            
            tab1, tab2, tab3 = st.tabs(["Waveform Comparison", "Noise Analysis", "Processing Details"])
            
            with tab1:
                # Original audio visualization
                fig_original = create_audio_visualization(
                    st.session_state.original_audio,
                    st.session_state.sample_rate,
                    "Original Audio"
                )
                st.plotly_chart(fig_original, use_container_width=True)
                
                # Processed audio visualization
                fig_processed = create_audio_visualization(
                    st.session_state.processed_audio,
                    st.session_state.sample_rate,
                    "Processed Audio"
                )
                st.plotly_chart(fig_processed, use_container_width=True)
            
            with tab2:
                # Analyze current audio for display
                noise_profile = st.session_state.noise_reduction_system.noise_reducer.analyze_noise_profile(
                    st.session_state.original_audio,
                    st.session_state.sample_rate
                )
                
                artifacts = st.session_state.noise_reduction_system.artifact_remover.detect_artifacts(
                    st.session_state.original_audio,
                    st.session_state.sample_rate
                )
                
                create_noise_analysis_display(noise_profile, artifacts)
            
            with tab3:
                st.subheader("🔧 Processing Details")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Applied Settings:**")
                    st.json({
                        "noise_reduction_strength": settings.noise_reduction_strength,
                        "preserve_speech_quality": settings.preserve_speech_quality,
                        "artifact_removal_sensitivity": settings.artifact_removal_sensitivity,
                        "spectral_enhancement": settings.spectral_enhancement,
                        "dynamic_range_optimization": settings.dynamic_range_optimization,
                        "ai_reconstruction": settings.ai_reconstruction,
                        "processing_mode": settings.processing_mode
                    })
                
                with col2:
                    st.write("**Results Summary:**")
                    st.json({
                        "processing_time_seconds": round(result.processing_time, 2),
                        "confidence_score": round(result.confidence_score, 3),
                        "noise_reduction_applied": round(result.noise_reduction_applied, 2),
                        "artifacts_removed": [art.value for art in result.artifacts_removed],
                        "quality_improvements": result.quality_improvement
                    })
    
    else:
        # Welcome screen
        st.info("👆 Upload an audio file or generate test audio to get started")
        
        # Feature overview
        st.subheader("🌟 Features")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **🔇 Noise Reduction**
            - Adaptive algorithms
            - Speech preservation
            - Multiple noise types
            - Real-time analysis
            """)
        
        with col2:
            st.markdown("""
            **🛠️ Artifact Removal**
            - Click & pop removal
            - Hum & buzz filtering
            - Distortion correction
            - Clipping repair
            """)
        
        with col3:
            st.markdown("""
            **🎨 Enhancement**
            - Spectral enhancement
            - Dynamic range optimization
            - AI reconstruction
            - Professional mastering
            """)
        
        # Technical specifications
        with st.expander("📋 Technical Specifications"):
            st.markdown("""
            - **Supported Formats:** WAV, MP3, FLAC, M4A, OGG
            - **Sample Rates:** Up to 192 kHz
            - **Bit Depths:** 16, 24, 32-bit
            - **Processing:** Multi-threaded, GPU-accelerated
            - **Algorithms:** Spectral subtraction, Wiener filtering, AI reconstruction
            - **Standards:** Broadcast quality, professional audio
            """)

if __name__ == "__main__":
    main()