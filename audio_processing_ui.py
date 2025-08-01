#!/usr/bin/env python3
"""
Audio Processing UI Module
Provides comprehensive UI for audio enhancement and processing features
"""

import streamlit as st
import os
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import json

from audio_processor import AudioProcessor
from advanced_audio_processor import (
    AdvancedAudioProcessor,
    AudioQualityMetrics,
    analyze_audio_quality,
    enhance_audio_for_transcription
)

class AudioProcessingUI:
    """Enhanced audio processing UI with all features integrated"""
    
    def __init__(self):
        self.audio_processor = AudioProcessor()
        self.advanced_processor = AdvancedAudioProcessor()
        
    def render_audio_enhancement_panel(self) -> Dict[str, Any]:
        """
        Render audio enhancement options panel
        
        Returns:
            Dictionary of selected enhancement options
        """
        st.subheader("🎵 Audio Enhancement Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔊 Basic Enhancements")
            
            # Volume normalization
            normalize_volume = st.checkbox(
                "Volume Normalization",
                value=True,
                help="Normalize audio to consistent volume levels"
            )
            
            if normalize_volume:
                target_volume = st.slider(
                    "Target Volume (dBFS)",
                    min_value=-30,
                    max_value=-10,
                    value=-20,
                    help="Target volume level in decibels"
                )
            else:
                target_volume = -20
            
            # Dynamic range compression
            compress_dynamic = st.checkbox(
                "Dynamic Range Compression",
                value=True,
                help="Compress dynamic range for consistent audio levels"
            )
            
            if compress_dynamic:
                compression_ratio = st.slider(
                    "Compression Ratio",
                    min_value=2.0,
                    max_value=10.0,
                    value=4.0,
                    step=0.5,
                    help="How much to compress loud sounds"
                )
            else:
                compression_ratio = 4.0
            
            # Noise reduction
            reduce_noise = st.checkbox(
                "Noise Reduction",
                value=True,
                help="Remove background noise and improve clarity"
            )
            
            if reduce_noise:
                noise_factor = st.slider(
                    "Noise Reduction Strength",
                    min_value=0.5,
                    max_value=1.0,
                    value=0.8,
                    step=0.1,
                    help="How aggressively to remove noise"
                )
            else:
                noise_factor = 0.8
        
        with col2:
            st.markdown("### ✂️ Audio Trimming")
            
            # Silence trimming
            trim_silence = st.checkbox(
                "Trim Silence",
                value=True,
                help="Remove silence from beginning and end"
            )
            
            if trim_silence:
                silence_threshold = st.slider(
                    "Silence Threshold (dBFS)",
                    min_value=-60,
                    max_value=-20,
                    value=-40,
                    help="Volume level considered as silence"
                )
            else:
                silence_threshold = -40
            
            # Audio segmentation
            segment_audio = st.checkbox(
                "Segment Long Audio",
                value=False,
                help="Split long recordings into smaller segments"
            )
            
            if segment_audio:
                segment_method = st.selectbox(
                    "Segmentation Method",
                    ["Silence-based", "Fixed Time", "Auto Chapters"],
                    help="How to split the audio"
                )
                
                if segment_method == "Fixed Time":
                    segment_minutes = st.number_input(
                        "Segment Length (minutes)",
                        min_value=1,
                        max_value=30,
                        value=5,
                        help="Length of each segment"
                    )
                else:
                    segment_minutes = 5
            else:
                segment_method = "Silence-based"
                segment_minutes = 5
        
        # Enhancement presets
        st.markdown("### 🎛️ Enhancement Presets")
        preset = st.selectbox(
            "Select Preset",
            [
                "Custom",
                "Speech Optimization",
                "Podcast Enhancement",
                "Meeting Recording",
                "Lecture Recording",
                "Interview Enhancement",
                "Noisy Environment"
            ],
            help="Pre-configured enhancement settings"
        )
        
        # Apply preset settings
        if preset != "Custom":
            preset_settings = self._get_preset_settings(preset)
            st.info(f"Using {preset} preset: {preset_settings['description']}")
        
        return {
            'normalize_volume': normalize_volume,
            'target_volume': target_volume,
            'compress_dynamic': compress_dynamic,
            'compression_ratio': compression_ratio,
            'reduce_noise': reduce_noise,
            'noise_factor': noise_factor,
            'trim_silence': trim_silence,
            'silence_threshold': silence_threshold,
            'segment_audio': segment_audio,
            'segment_method': segment_method,
            'segment_minutes': segment_minutes,
            'preset': preset
        }
    
    def render_quality_analysis(self, audio_path: str) -> AudioQualityMetrics:
        """
        Render audio quality analysis results
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            AudioQualityMetrics object
        """
        st.subheader("📊 Audio Quality Analysis")
        
        with st.spinner("Analyzing audio quality..."):
            metrics = analyze_audio_quality(audio_path)
        
        # Display quality score with color coding
        quality_color = self._get_quality_color(metrics.quality_score)
        st.metric(
            "Overall Quality Score",
            f"{metrics.quality_score:.1f}/100",
            delta=None,
            help="Overall audio quality assessment"
        )
        
        # Detailed metrics in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Signal-to-Noise Ratio",
                f"{metrics.snr_db:.1f} dB",
                help="Higher is better (>20dB is good)"
            )
            st.metric(
                "RMS Energy",
                f"{metrics.rms_energy:.3f}",
                help="Average signal strength"
            )
        
        with col2:
            st.metric(
                "Dynamic Range",
                f"{metrics.dynamic_range_db:.1f} dB",
                help="Difference between loud and quiet parts"
            )
            st.metric(
                "Zero Crossing Rate",
                f"{metrics.zero_crossing_rate:.3f}",
                help="Frequency content indicator"
            )
        
        with col3:
            st.metric(
                "Spectral Centroid",
                f"{metrics.spectral_centroid:.0f} Hz",
                help="Average frequency content"
            )
            st.metric(
                "Spectral Rolloff",
                f"{metrics.spectral_rolloff:.0f} Hz",
                help="Frequency below which 85% of energy is contained"
            )
        
        # Recommendations
        if metrics.recommendations:
            st.markdown("### 💡 Recommendations")
            for rec in metrics.recommendations:
                st.info(f"• {rec}")
        
        return metrics
    
    def process_audio_with_ui(self, audio_path: str, options: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Process audio with selected enhancements and UI feedback
        
        Args:
            audio_path: Path to input audio
            options: Enhancement options dictionary
            
        Returns:
            Tuple of (enhanced audio path, processing results)
        """
        results = {
            'original_path': audio_path,
            'enhanced_path': audio_path,
            'segments': [],
            'quality_before': None,
            'quality_after': None,
            'processing_time': 0,
            'enhancements_applied': []
        }
        
        start_time = datetime.now()
        
        try:
            # Analyze original quality
            st.info("Analyzing original audio quality...")
            results['quality_before'] = analyze_audio_quality(audio_path)
            
            current_path = audio_path
            
            # Apply volume normalization
            if options.get('normalize_volume', False):
                with st.spinner("Normalizing volume..."):
                    current_path = self.audio_processor.normalize_volume(
                        current_path,
                        target_dBFS=options.get('target_volume', -20)
                    )
                    results['enhancements_applied'].append('Volume Normalization')
            
            # Apply dynamic range compression
            if options.get('compress_dynamic', False):
                with st.spinner("Applying dynamic range compression..."):
                    current_path = self.audio_processor.compress_dynamic_range(
                        current_path,
                        ratio=options.get('compression_ratio', 4.0)
                    )
                    results['enhancements_applied'].append('Dynamic Range Compression')
            
            # Apply noise reduction
            if options.get('reduce_noise', False):
                with st.spinner("Reducing noise..."):
                    current_path = self.advanced_processor.noise_reducer.reduce_noise(
                        current_path,
                        noise_duration=1.0
                    )
                    results['enhancements_applied'].append('Noise Reduction')
            
            # Trim silence
            if options.get('trim_silence', False):
                with st.spinner("Trimming silence..."):
                    current_path = self.advanced_processor.trimmer.trim_silence(
                        current_path,
                        silence_thresh=options.get('silence_threshold', -40)
                    )
                    results['enhancements_applied'].append('Silence Trimming')
            
            # Segment audio if requested
            if options.get('segment_audio', False):
                with st.spinner("Segmenting audio..."):
                    segment_method = options.get('segment_method', 'Silence-based')
                    
                    if segment_method == "Silence-based":
                        segments = self.advanced_processor.trimmer.segment_by_silence(current_path)
                    elif segment_method == "Fixed Time":
                        segment_minutes = options.get('segment_minutes', 5)
                        segments = self._segment_by_time(current_path, segment_minutes)
                    else:  # Auto Chapters
                        segment_data = self.advanced_processor.create_segments_with_bookmarks(
                            current_path,
                            segment_method="auto"
                        )
                        segments = segment_data.get('segments', [current_path])
                    
                    results['segments'] = segments
                    results['enhancements_applied'].append(f'{segment_method} Segmentation')
            
            results['enhanced_path'] = current_path
            
            # Analyze enhanced quality
            if current_path != audio_path:
                st.info("Analyzing enhanced audio quality...")
                results['quality_after'] = analyze_audio_quality(current_path)
            
            # Calculate processing time
            results['processing_time'] = (datetime.now() - start_time).total_seconds()
            
            # Show success message
            st.success(f"✅ Audio processing complete! Applied {len(results['enhancements_applied'])} enhancements.")
            
        except Exception as e:
            st.error(f"Audio processing error: {str(e)}")
            results['error'] = str(e)
        
        return results['enhanced_path'], results
    
    def render_processing_results(self, results: Dict[str, Any]):
        """
        Render audio processing results
        
        Args:
            results: Processing results dictionary
        """
        st.subheader("📈 Processing Results")
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Enhancements Applied",
                len(results.get('enhancements_applied', [])),
                help="Number of audio enhancements applied"
            )
        
        with col2:
            st.metric(
                "Processing Time",
                f"{results.get('processing_time', 0):.1f}s",
                help="Total processing duration"
            )
        
        with col3:
            segments = results.get('segments', [])
            if segments:
                st.metric(
                    "Audio Segments",
                    len(segments),
                    help="Number of segments created"
                )
        
        # Applied enhancements
        if results.get('enhancements_applied'):
            st.markdown("### ✨ Applied Enhancements")
            for enhancement in results['enhancements_applied']:
                st.success(f"✓ {enhancement}")
        
        # Quality improvement
        if results.get('quality_before') and results.get('quality_after'):
            st.markdown("### 📊 Quality Improvement")
            
            before = results['quality_before']
            after = results['quality_after']
            
            improvement = after.quality_score - before.quality_score
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "Quality Before",
                    f"{before.quality_score:.1f}/100"
                )
                st.caption(f"SNR: {before.snr_db:.1f} dB")
            
            with col2:
                st.metric(
                    "Quality After",
                    f"{after.quality_score:.1f}/100",
                    delta=f"{improvement:+.1f}"
                )
                st.caption(f"SNR: {after.snr_db:.1f} dB")
        
        # Segments information
        if results.get('segments'):
            st.markdown("### 📂 Audio Segments")
            st.info(f"Audio split into {len(results['segments'])} segments")
            
            # Option to download segments
            if st.checkbox("Show segment details"):
                for i, segment in enumerate(results['segments']):
                    st.text(f"Segment {i+1}: {os.path.basename(segment)}")
    
    def _get_preset_settings(self, preset: str) -> Dict[str, Any]:
        """Get enhancement settings for a preset"""
        presets = {
            "Speech Optimization": {
                "description": "Optimized for clear speech and voice",
                "normalize_volume": True,
                "target_volume": -20,
                "compress_dynamic": True,
                "compression_ratio": 3.0,
                "reduce_noise": True,
                "noise_factor": 0.8,
                "trim_silence": True,
                "silence_threshold": -40
            },
            "Podcast Enhancement": {
                "description": "Professional podcast audio quality",
                "normalize_volume": True,
                "target_volume": -16,
                "compress_dynamic": True,
                "compression_ratio": 4.0,
                "reduce_noise": True,
                "noise_factor": 0.9,
                "trim_silence": True,
                "silence_threshold": -45
            },
            "Meeting Recording": {
                "description": "Multiple speakers and room acoustics",
                "normalize_volume": True,
                "target_volume": -18,
                "compress_dynamic": True,
                "compression_ratio": 5.0,
                "reduce_noise": True,
                "noise_factor": 0.7,
                "trim_silence": False,
                "silence_threshold": -35
            },
            "Lecture Recording": {
                "description": "Long-form educational content",
                "normalize_volume": True,
                "target_volume": -20,
                "compress_dynamic": True,
                "compression_ratio": 3.5,
                "reduce_noise": True,
                "noise_factor": 0.75,
                "trim_silence": True,
                "silence_threshold": -38,
                "segment_audio": True,
                "segment_method": "Fixed Time",
                "segment_minutes": 10
            },
            "Interview Enhancement": {
                "description": "Two-person conversation",
                "normalize_volume": True,
                "target_volume": -18,
                "compress_dynamic": True,
                "compression_ratio": 3.5,
                "reduce_noise": True,
                "noise_factor": 0.8,
                "trim_silence": True,
                "silence_threshold": -42
            },
            "Noisy Environment": {
                "description": "Aggressive noise reduction",
                "normalize_volume": True,
                "target_volume": -16,
                "compress_dynamic": True,
                "compression_ratio": 6.0,
                "reduce_noise": True,
                "noise_factor": 0.95,
                "trim_silence": True,
                "silence_threshold": -35
            }
        }
        
        return presets.get(preset, {
            "description": "Custom settings",
            "normalize_volume": True,
            "target_volume": -20
        })
    
    def _get_quality_color(self, score: float) -> str:
        """Get color based on quality score"""
        if score >= 80:
            return "green"
        elif score >= 60:
            return "yellow"
        elif score >= 40:
            return "orange"
        else:
            return "red"
    
    def _segment_by_time(self, audio_path: str, minutes: int) -> List[str]:
        """Segment audio by fixed time intervals"""
        from pydub import AudioSegment
        
        audio = AudioSegment.from_file(audio_path)
        duration_ms = len(audio)
        segment_length_ms = minutes * 60 * 1000
        
        segments = []
        for i in range(0, duration_ms, segment_length_ms):
            end_time = min(i + segment_length_ms, duration_ms)
            segment = audio[i:end_time]
            
            temp_file = tempfile.NamedTemporaryFile(
                suffix=f"_segment_{i//60000:03d}.wav",
                delete=False
            )
            segment.export(temp_file.name, format="wav")
            segments.append(temp_file.name)
        
        return segments

def render_audio_processing_page():
    """Render the audio processing page in Streamlit"""
    st.title("🎵 Advanced Audio Processing")
    st.markdown("Enhance your audio quality for better transcription accuracy")
    
    ui = AudioProcessingUI()
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose an audio file",
        type=['mp3', 'wav', 'flac', 'm4a', 'ogg', 'wma'],
        help="Upload an audio file to process"
    )
    
    if uploaded_file:
        # Save uploaded file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1])
        temp_file.write(uploaded_file.read())
        temp_file.close()
        
        # Display original audio
        st.audio(uploaded_file, format=f'audio/{uploaded_file.type.split("/")[1]}')
        
        # Render enhancement options
        enhancement_options = ui.render_audio_enhancement_panel()
        
        # Process button
        if st.button("🚀 Process Audio", type="primary"):
            # Process audio with UI feedback
            enhanced_path, results = ui.process_audio_with_ui(temp_file.name, enhancement_options)
            
            # Store results in session state
            st.session_state['audio_processing_results'] = results
            st.session_state['enhanced_audio_path'] = enhanced_path
        
        # Show results if available
        if 'audio_processing_results' in st.session_state:
            results = st.session_state['audio_processing_results']
            
            # Render processing results
            ui.render_processing_results(results)
            
            # Play enhanced audio
            if results.get('enhanced_path') and os.path.exists(results['enhanced_path']):
                st.markdown("### 🎧 Enhanced Audio")
                st.audio(results['enhanced_path'], format='audio/wav')
                
                # Download button
                with open(results['enhanced_path'], 'rb') as f:
                    st.download_button(
                        label="📥 Download Enhanced Audio",
                        data=f.read(),
                        file_name="enhanced_audio.wav",
                        mime="audio/wav"
                    )
        
        # Show quality analysis
        if st.checkbox("Show Detailed Quality Analysis"):
            ui.render_quality_analysis(temp_file.name)