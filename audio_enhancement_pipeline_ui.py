"""
Streamlit UI for Audio Enhancement Pipeline
Task 117: Build comprehensive audio enhancement pipeline

This module provides a user-friendly Streamlit interface for the audio enhancement pipeline,
allowing users to upload audio files, configure enhancement options, and download results.
"""

import streamlit as st
import os
import tempfile
import shutil
from pathlib import Path
import json
import time
import numpy as np
import librosa
import soundfile as sf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Any, Optional

from audio_enhancement_pipeline import AudioEnhancementPipeline, EnhancementResult, AudioQualityMetrics

# Page configuration
st.set_page_config(
    page_title="Audio Enhancement Pipeline",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
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
    .improvement-positive {
        color: #28a745;
        font-weight: bold;
    }
    .improvement-negative {
        color: #dc3545;
        font-weight: bold;
    }
    .improvement-neutral {
        color: #6c757d;
        font-weight: bold;
    }
    .processing-info {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class AudioEnhancementUI:
    """Streamlit UI for audio enhancement pipeline"""
    
    def __init__(self):
        """Initialize the UI"""
        if 'pipeline' not in st.session_state:
            st.session_state.pipeline = AudioEnhancementPipeline()
        
        if 'enhancement_results' not in st.session_state:
            st.session_state.enhancement_results = {}
        
        if 'temp_dir' not in st.session_state:
            st.session_state.temp_dir = tempfile.mkdtemp(prefix="audio_enhancement_ui_")
    
    def render_header(self):
        """Render the main header"""
        st.markdown('<h1 class="main-header">🎵 Audio Enhancement Pipeline</h1>', unsafe_allow_html=True)
        
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <p style="font-size: 1.2rem; color: #666;">
                Transform your audio with advanced AI-powered enhancement techniques
            </p>
            <p style="color: #888;">
                Noise reduction • Audio repair • Spectral enhancement • Dynamic processing • Normalization
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_sidebar(self) -> Dict[str, Any]:
        """Render the sidebar with enhancement options"""
        st.sidebar.header("🎛️ Enhancement Options")
        
        # Enhancement toggles
        st.sidebar.subheader("Processing Modules")
        
        noise_reduction = st.sidebar.checkbox(
            "🔇 Noise Reduction",
            value=True,
            help="Remove background noise and unwanted artifacts"
        )
        
        audio_repair = st.sidebar.checkbox(
            "🔧 Audio Repair",
            value=True,
            help="Fix clipping, dropouts, and corrupted segments"
        )
        
        spectral_enhancement = st.sidebar.checkbox(
            "✨ Spectral Enhancement",
            value=True,
            help="Improve clarity and presence through frequency enhancement"
        )
        
        dynamic_processing = st.sidebar.checkbox(
            "📊 Dynamic Processing",
            value=True,
            help="Apply compression and dynamic range control"
        )
        
        normalization = st.sidebar.checkbox(
            "📈 Normalization",
            value=True,
            help="Optimize audio levels and prevent clipping"
        )
        
        st.sidebar.divider()
        
        # Advanced options
        with st.sidebar.expander("⚙️ Advanced Options"):
            st.write("**Noise Reduction Settings**")
            nr_strength = st.slider("Strength", 0.1, 2.0, 1.0, 0.1)
            
            st.write("**Normalization Settings**")
            target_lufs = st.slider("Target Loudness (LUFS)", -30, -10, -23)
            max_peak_db = st.slider("Max Peak (dB)", -6, -1, -1)
            
            st.write("**Processing Options**")
            preserve_stereo = st.checkbox("Preserve Stereo", value=True)
            high_quality = st.checkbox("High Quality Mode", value=False)
        
        # File format options
        st.sidebar.subheader("📁 Output Options")
        output_format = st.sidebar.selectbox(
            "Output Format",
            [".wav", ".mp3", ".flac", ".m4a"],
            index=0
        )
        
        if output_format == ".mp3":
            mp3_bitrate = st.sidebar.selectbox(
                "MP3 Bitrate",
                ["128", "192", "256", "320"],
                index=3
            )
        
        return {
            "noise_reduction": noise_reduction,
            "audio_repair": audio_repair,
            "spectral_enhancement": spectral_enhancement,
            "dynamic_processing": dynamic_processing,
            "normalization": normalization,
            "advanced_options": {
                "nr_strength": nr_strength,
                "target_lufs": target_lufs,
                "max_peak_db": max_peak_db,
                "preserve_stereo": preserve_stereo,
                "high_quality": high_quality
            },
            "output_format": output_format,
            "mp3_bitrate": mp3_bitrate if output_format == ".mp3" else None
        }
    
    def render_file_upload(self) -> Optional[str]:
        """Render file upload section"""
        st.header("📁 Upload Audio File")
        
        uploaded_file = st.file_uploader(
            "Choose an audio file",
            type=['wav', 'mp3', 'm4a', 'flac', 'ogg', 'aac'],
            help="Supported formats: WAV, MP3, M4A, FLAC, OGG, AAC"
        )
        
        if uploaded_file is not None:
            # Save uploaded file
            file_path = os.path.join(st.session_state.temp_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Display file info
            file_size = len(uploaded_file.getbuffer()) / (1024 * 1024)  # MB
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📄 File Name", uploaded_file.name)
            with col2:
                st.metric("📊 File Size", f"{file_size:.2f} MB")
            with col3:
                st.metric("🎵 Format", Path(uploaded_file.name).suffix.upper())
            
            # Audio player for original file
            st.subheader("🎧 Original Audio")
            st.audio(uploaded_file.getvalue())
            
            return file_path
        
        return None
    
    def render_demo_files(self) -> Optional[str]:
        """Render demo files section"""
        with st.expander("🎭 Try Demo Files"):
            st.write("Don't have an audio file? Try our demo files with different audio issues:")
            
            demo_options = {
                "Clean Speech": "High-quality speech audio",
                "Noisy Audio": "Speech with background noise",
                "Clipped Audio": "Audio with clipping distortion",
                "Quiet Audio": "Very low volume audio",
                "Phone Quality": "Compressed phone call quality"
            }
            
            selected_demo = st.selectbox("Select Demo Audio", list(demo_options.keys()))
            
            if st.button("🎵 Generate Demo File"):
                with st.spinner("Generating demo audio..."):
                    demo_file = self._generate_demo_file(selected_demo)
                    if demo_file:
                        st.success(f"✅ Generated {selected_demo} demo file")
                        
                        # Play demo file
                        with open(demo_file, "rb") as f:
                            st.audio(f.read())
                        
                        return demo_file
        
        return None
    
    def _generate_demo_file(self, demo_type: str) -> Optional[str]:
        """Generate a demo audio file"""
        try:
            sample_rate = 16000
            duration = 3.0
            samples = int(sample_rate * duration)
            t = np.linspace(0, duration, samples)
            
            # Generate base speech-like signal
            speech_signal = self._generate_speech_signal(t)
            
            if demo_type == "Clean Speech":
                audio = speech_signal
            elif demo_type == "Noisy Audio":
                noise = np.random.normal(0, 0.08, samples)
                audio = speech_signal + noise
            elif demo_type == "Clipped Audio":
                audio = np.clip(speech_signal * 2.5, -0.95, 0.95)
            elif demo_type == "Quiet Audio":
                audio = speech_signal * 0.05
            elif demo_type == "Phone Quality":
                # Apply phone-like filtering
                from scipy import signal
                nyquist = sample_rate / 2
                low = 300 / nyquist
                high = 3400 / nyquist
                b, a = signal.butter(4, [low, high], btype='band')
                audio = signal.filtfilt(b, a, speech_signal)
                # Add compression artifacts
                audio = np.sign(audio) * (np.abs(audio) ** 0.7)
            else:
                audio = speech_signal
            
            # Save demo file
            demo_file = os.path.join(st.session_state.temp_dir, f"demo_{demo_type.lower().replace(' ', '_')}.wav")
            sf.write(demo_file, audio, sample_rate)
            
            return demo_file
            
        except Exception as e:
            st.error(f"Failed to generate demo file: {str(e)}")
            return None
    
    def _generate_speech_signal(self, t: np.ndarray) -> np.ndarray:
        """Generate a speech-like signal"""
        # Simulate formant frequencies
        formants = [(700, 0.3), (1220, 0.25), (2600, 0.2)]
        
        speech_signal = np.zeros_like(t)
        for freq, amplitude in formants:
            speech_signal += amplitude * np.sin(2 * np.pi * freq * t)
        
        # Add envelope
        envelope = 0.7 + 0.3 * np.sin(2 * np.pi * 2.5 * t)
        return speech_signal * envelope * 0.3
    
    def render_enhancement_process(self, file_path: str, options: Dict[str, Any]) -> Optional[EnhancementResult]:
        """Render the enhancement process"""
        st.header("🔧 Audio Enhancement")
        
        if st.button("🚀 Enhance Audio", type="primary"):
            with st.spinner("Enhancing audio... This may take a moment."):
                try:
                    # Create progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Update progress
                    progress_bar.progress(20)
                    status_text.text("Loading audio file...")
                    
                    # Enhance audio
                    start_time = time.time()
                    result = st.session_state.pipeline.enhance_audio(file_path, enhancement_options=options)
                    processing_time = time.time() - start_time
                    
                    progress_bar.progress(100)
                    status_text.text("Enhancement complete!")
                    
                    # Store result
                    st.session_state.enhancement_results[file_path] = result
                    
                    st.success(f"✅ Audio enhanced successfully in {processing_time:.2f} seconds!")
                    
                    return result
                    
                except Exception as e:
                    st.error(f"❌ Enhancement failed: {str(e)}")
                    return None
        
        # Show previous result if available
        if file_path in st.session_state.enhancement_results:
            return st.session_state.enhancement_results[file_path]
        
        return None
    
    def render_results(self, result: EnhancementResult):
        """Render enhancement results"""
        st.header("📊 Enhancement Results")
        
        # Enhanced audio player
        st.subheader("🎧 Enhanced Audio")
        if os.path.exists(result.enhanced_audio_path):
            with open(result.enhanced_audio_path, "rb") as f:
                st.audio(f.read())
            
            # Download button
            with open(result.enhanced_audio_path, "rb") as f:
                st.download_button(
                    label="💾 Download Enhanced Audio",
                    data=f.read(),
                    file_name=f"enhanced_{Path(result.enhanced_audio_path).name}",
                    mime="audio/wav"
                )
        
        # Quality metrics comparison
        self._render_quality_comparison(result)
        
        # Processing information
        self._render_processing_info(result)
        
        # Detailed metrics
        self._render_detailed_metrics(result)
        
        # Visualizations
        self._render_visualizations(result)
    
    def _render_quality_comparison(self, result: EnhancementResult):
        """Render quality metrics comparison"""
        st.subheader("📈 Quality Improvement")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            improvement_class = self._get_improvement_class(result.improvement_score)
            st.markdown(f"""
            <div class="metric-card">
                <h4>Overall Improvement</h4>
                <p class="{improvement_class}">{result.improvement_score:+.1f} points</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h4>Original Quality</h4>
                <p>{result.original_metrics.quality_score:.1f}/100</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h4>Enhanced Quality</h4>
                <p>{result.enhanced_metrics.quality_score:.1f}/100</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <h4>Processing Time</h4>
                <p>{result.processing_time:.2f}s</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Quality score gauge
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = result.enhanced_metrics.quality_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Audio Quality Score"},
            delta = {'reference': result.original_metrics.quality_score, 'increasing': {'color': "green"}},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "gray"},
                    {'range': [80, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    def _get_improvement_class(self, improvement_score: float) -> str:
        """Get CSS class for improvement score"""
        if improvement_score > 2:
            return "improvement-positive"
        elif improvement_score < -2:
            return "improvement-negative"
        else:
            return "improvement-neutral"
    
    def _render_processing_info(self, result: EnhancementResult):
        """Render processing information"""
        st.subheader("🛠️ Processing Information")
        
        st.markdown(f"""
        <div class="processing-info">
            <p><strong>Enhancements Applied:</strong> {', '.join(result.enhancement_applied)}</p>
            <p><strong>Processing Time:</strong> {result.processing_time:.2f} seconds</p>
            <p><strong>Audio Duration:</strong> {result.metadata.get('duration', 'Unknown'):.1f} seconds</p>
            <p><strong>Sample Rate:</strong> {result.metadata.get('sample_rate', 'Unknown')} Hz</p>
            <p><strong>Channels:</strong> {result.metadata.get('channels', 'Unknown')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_detailed_metrics(self, result: EnhancementResult):
        """Render detailed quality metrics"""
        with st.expander("📊 Detailed Quality Metrics"):
            
            # Create comparison dataframe
            metrics_data = {
                'Metric': [
                    'SNR (dB)',
                    'THD (%)',
                    'Dynamic Range (dB)',
                    'Spectral Centroid (Hz)',
                    'RMS Energy',
                    'Peak Level (dB)',
                    'Loudness (LUFS)'
                ],
                'Original': [
                    f"{result.original_metrics.snr_db:.1f}",
                    f"{result.original_metrics.thd_percent:.2f}",
                    f"{result.original_metrics.dynamic_range_db:.1f}",
                    f"{result.original_metrics.spectral_centroid:.0f}",
                    f"{result.original_metrics.rms_energy:.3f}",
                    f"{result.original_metrics.peak_level_db:.1f}",
                    f"{result.original_metrics.loudness_lufs:.1f}"
                ],
                'Enhanced': [
                    f"{result.enhanced_metrics.snr_db:.1f}",
                    f"{result.enhanced_metrics.thd_percent:.2f}",
                    f"{result.enhanced_metrics.dynamic_range_db:.1f}",
                    f"{result.enhanced_metrics.spectral_centroid:.0f}",
                    f"{result.enhanced_metrics.rms_energy:.3f}",
                    f"{result.enhanced_metrics.peak_level_db:.1f}",
                    f"{result.enhanced_metrics.loudness_lufs:.1f}"
                ],
                'Change': [
                    f"{result.enhanced_metrics.snr_db - result.original_metrics.snr_db:+.1f}",
                    f"{result.enhanced_metrics.thd_percent - result.original_metrics.thd_percent:+.2f}",
                    f"{result.enhanced_metrics.dynamic_range_db - result.original_metrics.dynamic_range_db:+.1f}",
                    f"{result.enhanced_metrics.spectral_centroid - result.original_metrics.spectral_centroid:+.0f}",
                    f"{result.enhanced_metrics.rms_energy - result.original_metrics.rms_energy:+.3f}",
                    f"{result.enhanced_metrics.peak_level_db - result.original_metrics.peak_level_db:+.1f}",
                    f"{result.enhanced_metrics.loudness_lufs - result.original_metrics.loudness_lufs:+.1f}"
                ]
            }
            
            df = pd.DataFrame(metrics_data)
            st.dataframe(df, use_container_width=True)
            
            # Recommendations
            st.subheader("💡 Recommendations")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Original Audio:**")
                for rec in result.original_metrics.recommendations:
                    st.write(f"• {rec}")
            
            with col2:
                st.write("**Enhanced Audio:**")
                for rec in result.enhanced_metrics.recommendations:
                    st.write(f"• {rec}")
    
    def _render_visualizations(self, result: EnhancementResult):
        """Render audio visualizations"""
        with st.expander("📈 Audio Visualizations"):
            
            # Quality metrics radar chart
            categories = ['SNR', 'Dynamic Range', 'Spectral Quality', 'Loudness', 'Overall Quality']
            
            # Normalize metrics to 0-100 scale for visualization
            original_values = [
                min(100, max(0, result.original_metrics.snr_db * 2)),  # SNR
                min(100, max(0, result.original_metrics.dynamic_range_db * 2)),  # DR
                min(100, max(0, result.original_metrics.spectral_centroid / 50)),  # Spectral
                min(100, max(0, (result.original_metrics.loudness_lufs + 60) * 2)),  # Loudness
                result.original_metrics.quality_score  # Overall
            ]
            
            enhanced_values = [
                min(100, max(0, result.enhanced_metrics.snr_db * 2)),
                min(100, max(0, result.enhanced_metrics.dynamic_range_db * 2)),
                min(100, max(0, result.enhanced_metrics.spectral_centroid / 50)),
                min(100, max(0, (result.enhanced_metrics.loudness_lufs + 60) * 2)),
                result.enhanced_metrics.quality_score
            ]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatterpolar(
                r=original_values,
                theta=categories,
                fill='toself',
                name='Original',
                line_color='red',
                fillcolor='rgba(255, 0, 0, 0.1)'
            ))
            
            fig.add_trace(go.Scatterpolar(
                r=enhanced_values,
                theta=categories,
                fill='toself',
                name='Enhanced',
                line_color='blue',
                fillcolor='rgba(0, 0, 255, 0.1)'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )),
                showlegend=True,
                title="Audio Quality Comparison"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Metrics improvement bar chart
            metrics_names = ['SNR (dB)', 'THD (%)', 'Dynamic Range (dB)', 'Loudness (LUFS)']
            improvements = [
                result.enhanced_metrics.snr_db - result.original_metrics.snr_db,
                result.original_metrics.thd_percent - result.enhanced_metrics.thd_percent,  # Lower is better
                result.enhanced_metrics.dynamic_range_db - result.original_metrics.dynamic_range_db,
                result.enhanced_metrics.loudness_lufs - result.original_metrics.loudness_lufs
            ]
            
            colors = ['green' if x > 0 else 'red' if x < 0 else 'gray' for x in improvements]
            
            fig = go.Figure(data=[
                go.Bar(x=metrics_names, y=improvements, marker_color=colors)
            ])
            
            fig.update_layout(
                title="Quality Metrics Improvement",
                yaxis_title="Improvement",
                xaxis_title="Metrics"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def render_format_recommendations(self, file_path: str):
        """Render format optimization recommendations"""
        with st.expander("📋 Format Optimization Recommendations"):
            
            if st.button("🔍 Analyze Format Options"):
                with st.spinner("Analyzing format options..."):
                    try:
                        recommendations = st.session_state.pipeline.get_format_recommendations(file_path)
                        
                        st.subheader("📊 Current File Information")
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Format", recommendations['current_format'])
                        with col2:
                            st.metric("Size", f"{recommendations['file_size_mb']:.2f} MB")
                        with col3:
                            st.metric("Duration", f"{recommendations['duration_seconds']:.1f}s")
                        with col4:
                            st.metric("Quality", f"{recommendations['quality_score']:.1f}/100")
                        
                        st.subheader("💡 Format Recommendations")
                        
                        for i, rec in enumerate(recommendations['recommendations']):
                            with st.container():
                                st.markdown(f"""
                                **Option {i+1}: {rec['format']}**
                                - **Reason:** {rec['reason']}
                                - **Size Reduction:** {rec['expected_size_reduction']}
                                - **Quality Impact:** {rec['quality_impact']}
                                """)
                                st.divider()
                        
                    except Exception as e:
                        st.error(f"Failed to analyze format options: {str(e)}")
    
    def render_batch_processing(self):
        """Render batch processing section"""
        with st.expander("📦 Batch Processing"):
            st.write("Process multiple audio files at once")
            
            uploaded_files = st.file_uploader(
                "Choose multiple audio files",
                type=['wav', 'mp3', 'm4a', 'flac', 'ogg', 'aac'],
                accept_multiple_files=True,
                help="Upload multiple files for batch processing"
            )
            
            if uploaded_files:
                st.write(f"Selected {len(uploaded_files)} files for processing")
                
                if st.button("🚀 Process All Files"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    results = []
                    
                    for i, uploaded_file in enumerate(uploaded_files):
                        status_text.text(f"Processing {uploaded_file.name}...")
                        progress_bar.progress((i + 1) / len(uploaded_files))
                        
                        # Save file
                        file_path = os.path.join(st.session_state.temp_dir, uploaded_file.name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        try:
                            # Process file
                            result = st.session_state.pipeline.enhance_audio(file_path)
                            results.append((uploaded_file.name, result))
                        except Exception as e:
                            st.error(f"Failed to process {uploaded_file.name}: {str(e)}")
                    
                    status_text.text("Batch processing complete!")
                    
                    # Display batch results
                    st.subheader("📊 Batch Processing Results")
                    
                    batch_data = []
                    for filename, result in results:
                        batch_data.append({
                            'File': filename,
                            'Original Quality': f"{result.original_metrics.quality_score:.1f}",
                            'Enhanced Quality': f"{result.enhanced_metrics.quality_score:.1f}",
                            'Improvement': f"{result.improvement_score:+.1f}",
                            'Processing Time': f"{result.processing_time:.2f}s"
                        })
                    
                    df = pd.DataFrame(batch_data)
                    st.dataframe(df, use_container_width=True)
                    
                    # Download all enhanced files
                    if st.button("💾 Download All Enhanced Files"):
                        # Create zip file with all enhanced audio
                        import zipfile
                        zip_path = os.path.join(st.session_state.temp_dir, "enhanced_audio_batch.zip")
                        
                        with zipfile.ZipFile(zip_path, 'w') as zipf:
                            for filename, result in results:
                                if os.path.exists(result.enhanced_audio_path):
                                    zipf.write(result.enhanced_audio_path, f"enhanced_{filename}")
                        
                        with open(zip_path, "rb") as f:
                            st.download_button(
                                label="📦 Download Batch Results (ZIP)",
                                data=f.read(),
                                file_name="enhanced_audio_batch.zip",
                                mime="application/zip"
                            )
    
    def run(self):
        """Run the Streamlit UI"""
        # Render header
        self.render_header()
        
        # Render sidebar
        options = self.render_sidebar()
        
        # Main content
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # File upload
            file_path = self.render_file_upload()
            
            # Demo files
            if not file_path:
                demo_file = self.render_demo_files()
                if demo_file:
                    file_path = demo_file
            
            # Enhancement process
            if file_path:
                result = self.render_enhancement_process(file_path, options)
                
                # Results
                if result:
                    self.render_results(result)
        
        with col2:
            if file_path:
                # Format recommendations
                self.render_format_recommendations(file_path)
        
        # Batch processing
        self.render_batch_processing()
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #666; margin-top: 2rem;">
            <p>🎵 Audio Enhancement Pipeline v1.0</p>
            <p>Built with Streamlit • Powered by AI</p>
        </div>
        """, unsafe_allow_html=True)

def main():
    """Main function to run the Streamlit app"""
    ui = AudioEnhancementUI()
    ui.run()

if __name__ == "__main__":
    main()