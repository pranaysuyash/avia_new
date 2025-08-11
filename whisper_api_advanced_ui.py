"""
Whisper API Advanced Configuration UI

Streamlit interface for advanced Whisper API configuration and transcription.
Provides comprehensive controls for all advanced features including custom prompts,
temperature control, vocabulary injection, and domain-specific presets.
"""

import streamlit as st
import asyncio
import json
import os
import tempfile
from typing import Dict, List, Optional, Any
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import logging

from whisper_api_advanced import (
    WhisperAPIAdvanced,
    WhisperConfig,
    WhisperModel,
    ResponseFormat,
    LanguageCode,
    TranscriptionResult,
    create_medical_transcription_config,
    create_meeting_transcription_config,
    create_interview_transcription_config
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhisperAdvancedUI:
    """Streamlit UI for Advanced Whisper API Configuration"""
    
    def __init__(self):
        self.setup_page_config()
        self.initialize_session_state()
    
    def setup_page_config(self):
        """Configure Streamlit page settings"""
        st.set_page_config(
            page_title="Advanced Whisper API Configuration",
            page_icon="🎙️",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS for better styling
        st.markdown("""
        <style>
        .config-section {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
            border-left: 4px solid #007bff;
        }
        .result-card {
            background-color: #ffffff;
            padding: 1.5rem;
            border-radius: 0.5rem;
            border: 1px solid #dee2e6;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric-card {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            text-align: center;
            border: 1px solid #dee2e6;
        }
        .high-confidence {
            color: #28a745;
            font-weight: bold;
        }
        .medium-confidence {
            color: #ffc107;
            font-weight: bold;
        }
        .low-confidence {
            color: #dc3545;
            font-weight: bold;
        }
        .advanced-controls {
            background-color: #f1f3f4;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def initialize_session_state(self):
        """Initialize Streamlit session state variables"""
        if 'whisper_client' not in st.session_state:
            try:
                st.session_state.whisper_client = WhisperAPIAdvanced()
            except Exception as e:
                st.session_state.whisper_client = None
                st.session_state.api_error = str(e)
        
        if 'transcription_results' not in st.session_state:
            st.session_state.transcription_results = []
        
        if 'current_config' not in st.session_state:
            st.session_state.current_config = WhisperConfig()
        
        if 'usage_history' not in st.session_state:
            st.session_state.usage_history = []
    
    def render_main_interface(self):
        """Render the main UI interface"""
        st.title("🎙️ Advanced Whisper API Configuration")
        st.markdown("Configure and optimize Whisper API transcription with advanced settings and domain-specific presets.")
        
        # Check API key availability
        if st.session_state.whisper_client is None:
            self.render_api_key_setup()
            return
        
        # Sidebar navigation
        with st.sidebar:
            st.header("Navigation")
            page = st.selectbox(
                "Select Page",
                ["Configuration", "Transcription", "Batch Processing", "Analytics", "Presets"]
            )
        
        # Route to appropriate page
        if page == "Configuration":
            self.render_configuration_page()
        elif page == "Transcription":
            self.render_transcription_page()
        elif page == "Batch Processing":
            self.render_batch_processing_page()
        elif page == "Analytics":
            self.render_analytics_page()
        elif page == "Presets":
            self.render_presets_page()
    
    def render_api_key_setup(self):
        """Render API key setup interface"""
        st.error("OpenAI API key is required to use the Advanced Whisper API")
        
        st.markdown("""
        ### Setup Instructions:
        1. Get your OpenAI API key from [OpenAI Platform](https://platform.openai.com/api-keys)
        2. Set it as an environment variable: `OPENAI_API_KEY=your_key_here`
        3. Or enter it below (not recommended for production)
        """)
        
        api_key = st.text_input("OpenAI API Key", type="password", help="Enter your OpenAI API key")
        
        if st.button("Initialize Client") and api_key:
            try:
                os.environ['OPENAI_API_KEY'] = api_key
                st.session_state.whisper_client = WhisperAPIAdvanced(api_key)
                st.success("API client initialized successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to initialize client: {str(e)}")
    
    def render_configuration_page(self):
        """Render the configuration page"""
        st.header("🔧 Advanced Configuration")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self.render_basic_configuration()
            self.render_advanced_configuration()
            self.render_context_configuration()
        
        with col2:
            self.render_configuration_preview()
            self.render_quick_actions()
    
    def render_basic_configuration(self):
        """Render basic configuration options"""
        st.subheader("Basic Settings")
        
        with st.container():
            st.markdown('<div class="config-section">', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                model = st.selectbox(
                    "Model",
                    options=[model.value for model in WhisperModel],
                    index=0,
                    help="Whisper model to use for transcription"
                )
                
                language = st.selectbox(
                    "Language",
                    options=["Auto-detect"] + [lang.value for lang in LanguageCode if lang.value],
                    index=0,
                    help="Source language (auto-detect recommended)"
                )
                
                response_format = st.selectbox(
                    "Response Format",
                    options=[fmt.value for fmt in ResponseFormat],
                    index=3,  # Default to verbose_json
                    help="Output format for transcription results"
                )
            
            with col2:
                temperature = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.0,
                    step=0.1,
                    help="Controls randomness (0.0 = deterministic, 1.0 = creative)"
                )
                
                confidence_threshold = st.slider(
                    "Confidence Threshold",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.0,
                    step=0.1,
                    help="Minimum confidence score for including words (0.0 = include all)"
                )
                
                enable_timestamps = st.checkbox(
                    "Enable Word Timestamps",
                    value=True,
                    help="Include precise word-level timestamps"
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Update session state
            st.session_state.current_config.model = WhisperModel(model)
            st.session_state.current_config.language = LanguageCode.AUTO if language == "Auto-detect" else LanguageCode(language)
            st.session_state.current_config.response_format = ResponseFormat(response_format)
            st.session_state.current_config.temperature = temperature
            st.session_state.current_config.confidence_threshold = confidence_threshold
            st.session_state.current_config.enable_word_timestamps = enable_timestamps
    
    def render_advanced_configuration(self):
        """Render advanced configuration options"""
        st.subheader("Advanced Settings")
        
        with st.expander("Advanced Controls", expanded=False):
            st.markdown('<div class="advanced-controls">', unsafe_allow_html=True)
            
            # Custom prompt
            custom_prompt = st.text_area(
                "Custom Prompt",
                value=st.session_state.current_config.prompt or "",
                height=100,
                help="Custom prompt to guide transcription (e.g., context, terminology, style)"
            )
            
            # Custom vocabulary
            st.markdown("**Custom Vocabulary**")
            vocab_input = st.text_area(
                "Enter custom terms (one per line)",
                value="\n".join(st.session_state.current_config.custom_vocabulary or []),
                height=80,
                help="Domain-specific terms to improve recognition accuracy"
            )
            custom_vocabulary = [term.strip() for term in vocab_input.split('\n') if term.strip()]
            
            # Timestamp granularities
            timestamp_options = st.multiselect(
                "Timestamp Granularities",
                options=["word", "segment"],
                default=st.session_state.current_config.timestamp_granularities or ["segment"],
                help="Level of timestamp detail to include"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                suppress_silence = st.checkbox(
                    "Suppress Silence",
                    value=st.session_state.current_config.suppress_silence,
                    help="Remove silent segments from transcription"
                )
                
                max_segment_length = st.number_input(
                    "Max Segment Length (seconds)",
                    min_value=1,
                    max_value=300,
                    value=st.session_state.current_config.max_segment_length or 30,
                    help="Maximum length for transcript segments"
                )
            
            with col2:
                enable_segment_timestamps = st.checkbox(
                    "Enable Segment Timestamps",
                    value=st.session_state.current_config.enable_segment_timestamps,
                    help="Include segment-level timestamps"
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Update session state
            st.session_state.current_config.prompt = custom_prompt if custom_prompt else None
            st.session_state.current_config.custom_vocabulary = custom_vocabulary
            st.session_state.current_config.timestamp_granularities = timestamp_options
            st.session_state.current_config.suppress_silence = suppress_silence
            st.session_state.current_config.max_segment_length = max_segment_length if max_segment_length > 0 else None
            st.session_state.current_config.enable_segment_timestamps = enable_segment_timestamps
    
    def render_context_configuration(self):
        """Render context and domain configuration"""
        st.subheader("Context & Domain Settings")
        
        with st.expander("Context Configuration", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                domain_context = st.selectbox(
                    "Domain Context",
                    options=["", "medical", "legal", "technical", "business", "education", "interview"],
                    index=0,
                    help="Domain-specific context for better accuracy"
                )
                
                content_type = st.text_input(
                    "Content Type",
                    value=st.session_state.current_config.content_type or "",
                    help="Type of content (e.g., 'meeting', 'lecture', 'interview')"
                )
            
            with col2:
                speaker_context = st.text_input(
                    "Speaker Context",
                    value=st.session_state.current_config.speaker_context or "",
                    help="Information about speakers (e.g., 'Dr. Smith and Patient')"
                )
            
            # Update session state
            st.session_state.current_config.domain_context = domain_context if domain_context else None
            st.session_state.current_config.content_type = content_type if content_type else None
            st.session_state.current_config.speaker_context = speaker_context if speaker_context else None
    
    def render_configuration_preview(self):
        """Render configuration preview"""
        st.subheader("Configuration Preview")
        
        with st.container():
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            
            config_dict = {
                "Model": st.session_state.current_config.model.value,
                "Language": st.session_state.current_config.language.value if st.session_state.current_config.language != LanguageCode.AUTO else "Auto-detect",
                "Temperature": st.session_state.current_config.temperature,
                "Response Format": st.session_state.current_config.response_format.value,
                "Confidence Threshold": st.session_state.current_config.confidence_threshold,
                "Custom Vocabulary Count": len(st.session_state.current_config.custom_vocabulary or []),
                "Domain": st.session_state.current_config.domain_context or "General"
            }
            
            for key, value in config_dict.items():
                st.markdown(f"**{key}:** {value}")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    def render_quick_actions(self):
        """Render quick action buttons"""
        st.subheader("Quick Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🎯 Optimize for Quality", use_container_width=True):
                optimized = st.session_state.whisper_client.optimize_config_for_quality(st.session_state.current_config)
                st.session_state.current_config = optimized
                st.success("Configuration optimized for quality!")
                st.rerun()
        
        with col2:
            if st.button("⚡ Optimize for Speed", use_container_width=True):
                optimized = st.session_state.whisper_client.optimize_config_for_speed(st.session_state.current_config)
                st.session_state.current_config = optimized
                st.success("Configuration optimized for speed!")
                st.rerun()
        
        if st.button("💾 Save Configuration", use_container_width=True):
            self.save_configuration()
        
        if st.button("📁 Load Configuration", use_container_width=True):
            self.load_configuration()
    
    def render_transcription_page(self):
        """Render the transcription page"""
        st.header("🎤 Audio Transcription")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # File upload
            uploaded_file = st.file_uploader(
                "Choose an audio file",
                type=['mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm'],
                help="Upload an audio file for transcription"
            )
            
            if uploaded_file is not None:
                # Display file info
                st.info(f"File: {uploaded_file.name} ({uploaded_file.size / 1024 / 1024:.1f} MB)")
                
                # Transcription controls
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    use_retry = st.checkbox("Enable Retry", value=True, help="Automatic retry on failure")
                
                with col_b:
                    max_retries = st.number_input("Max Retries", min_value=1, max_value=5, value=3) if use_retry else 1
                
                with col_c:
                    if st.button("🚀 Start Transcription", type="primary", use_container_width=True):
                        self.run_transcription(uploaded_file, use_retry, max_retries)
        
        with col2:
            self.render_transcription_status()
        
        # Display results
        if st.session_state.transcription_results:
            self.render_transcription_results()
    
    def render_batch_processing_page(self):
        """Render the batch processing page"""
        st.header("📦 Batch Processing")
        
        st.markdown("Upload multiple audio files for batch transcription with the current configuration.")
        
        # Multiple file upload
        uploaded_files = st.file_uploader(
            "Choose audio files",
            type=['mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm'],
            accept_multiple_files=True,
            help="Upload multiple audio files for batch processing"
        )
        
        if uploaded_files:
            st.info(f"Selected {len(uploaded_files)} files for batch processing")
            
            # Batch processing controls
            col1, col2, col3 = st.columns(3)
            
            with col1:
                max_concurrent = st.slider("Max Concurrent", min_value=1, max_value=5, value=3)
            
            with col2:
                use_retry = st.checkbox("Enable Retry", value=True, key="batch_retry")
            
            with col3:
                if st.button("🚀 Start Batch Processing", type="primary"):
                    self.run_batch_transcription(uploaded_files, max_concurrent, use_retry)
            
            # Display file list
            if st.checkbox("Show File Details"):
                file_data = []
                for file in uploaded_files:
                    file_data.append({
                        "Filename": file.name,
                        "Size (MB)": f"{file.size / 1024 / 1024:.1f}",
                        "Type": file.type
                    })
                
                df = pd.DataFrame(file_data)
                st.dataframe(df, use_container_width=True)
    
    def render_analytics_page(self):
        """Render the analytics page"""
        st.header("📊 Usage Analytics")
        
        if st.session_state.whisper_client:
            stats = st.session_state.whisper_client.get_usage_statistics()
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Total Requests", stats['total_requests'])
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Total Duration", f"{stats['total_duration']:.1f}s")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Estimated Cost", f"${stats['total_cost_estimate']:.3f}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col4:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Avg Processing Time", f"{stats['average_processing_time']:.2f}s")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                if stats['requests_by_model']:
                    fig = px.pie(
                        values=list(stats['requests_by_model'].values()),
                        names=list(stats['requests_by_model'].keys()),
                        title="Requests by Model"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if st.session_state.usage_history:
                    df = pd.DataFrame(st.session_state.usage_history)
                    fig = px.line(df, x='timestamp', y='processing_time', title="Processing Time Over Time")
                    st.plotly_chart(fig, use_container_width=True)
            
            # Cache information
            st.subheader("Cache Statistics")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Cache Size", stats['cache_size'])
                st.metric("Cache Hit Rate", f"{stats['cache_hit_rate']:.1%}")
            
            with col2:
                if st.button("Clear Cache"):
                    st.session_state.whisper_client.clear_cache()
                    st.success("Cache cleared successfully!")
                    st.rerun()
    
    def render_presets_page(self):
        """Render the presets page"""
        st.header("🎛️ Configuration Presets")
        
        st.markdown("Use pre-configured settings optimized for specific domains and use cases.")
        
        # Preset categories
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Domain Presets")
            
            if st.button("🏥 Medical Transcription", use_container_width=True):
                config = create_medical_transcription_config()
                st.session_state.current_config = config
                st.success("Medical transcription preset loaded!")
                st.rerun()
            
            if st.button("💼 Business Meeting", use_container_width=True):
                config = create_meeting_transcription_config()
                st.session_state.current_config = config
                st.success("Business meeting preset loaded!")
                st.rerun()
            
            if st.button("🎤 Interview", use_container_width=True):
                config = create_interview_transcription_config()
                st.session_state.current_config = config
                st.success("Interview preset loaded!")
                st.rerun()
        
        with col2:
            st.subheader("Quality Presets")
            
            if st.button("🎯 Maximum Quality", use_container_width=True):
                config = st.session_state.whisper_client.optimize_config_for_quality(st.session_state.current_config)
                st.session_state.current_config = config
                st.success("Maximum quality preset loaded!")
                st.rerun()
            
            if st.button("⚡ Maximum Speed", use_container_width=True):
                config = st.session_state.whisper_client.optimize_config_for_speed(st.session_state.current_config)
                st.session_state.current_config = config
                st.success("Maximum speed preset loaded!")
                st.rerun()
            
            if st.button("⚖️ Balanced", use_container_width=True):
                config = WhisperConfig(temperature=0.2, confidence_threshold=0.5)
                st.session_state.current_config = config
                st.success("Balanced preset loaded!")
                st.rerun()
        
        # Custom preset management
        st.subheader("Custom Presets")
        
        preset_name = st.text_input("Preset Name", help="Name for your custom preset")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Save Current Config as Preset") and preset_name:
                self.save_custom_preset(preset_name)
        
        with col2:
            if st.button("📁 Load Custom Preset") and preset_name:
                self.load_custom_preset(preset_name)
    
    def render_transcription_status(self):
        """Render transcription status and progress"""
        st.subheader("Status")
        
        if 'transcription_in_progress' in st.session_state and st.session_state.transcription_in_progress:
            st.info("🔄 Transcription in progress...")
            st.progress(0.5)  # Indeterminate progress
        else:
            st.success("✅ Ready for transcription")
        
        # Recent activity
        if st.session_state.transcription_results:
            st.subheader("Recent Results")
            recent = st.session_state.transcription_results[-3:]  # Last 3 results
            
            for i, result in enumerate(reversed(recent)):
                with st.expander(f"Result {len(recent) - i}"):
                    st.markdown(f"**Text:** {result.text[:100]}...")
                    st.markdown(f"**Duration:** {result.duration:.1f}s")
                    st.markdown(f"**Confidence:** {result.get_average_confidence():.2f}")
    
    def render_transcription_results(self):
        """Render detailed transcription results"""
        st.subheader("📝 Transcription Results")
        
        # Result selector
        if len(st.session_state.transcription_results) > 1:
            selected_idx = st.selectbox(
                "Select Result",
                range(len(st.session_state.transcription_results)),
                index=len(st.session_state.transcription_results) - 1,
                format_func=lambda x: f"Result {x + 1}"
            )
        else:
            selected_idx = 0
        
        result = st.session_state.transcription_results[selected_idx]
        
        # Result overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Duration", f"{result.duration:.1f}s" if result.duration else "N/A")
        
        with col2:
            confidence = result.get_average_confidence()
            confidence_class = "high-confidence" if confidence > 0.8 else "medium-confidence" if confidence > 0.5 else "low-confidence"
            st.markdown(f'<div class="{confidence_class}">Confidence: {confidence:.2f}</div>', unsafe_allow_html=True)
        
        with col3:
            st.metric("Processing Time", f"{result.processing_time:.2f}s")
        
        with col4:
            st.metric("Model", result.model_used)
        
        # Transcription text
        st.subheader("Transcription Text")
        st.text_area("", value=result.text, height=200, disabled=True)
        
        # Detailed analysis
        if result.segments or result.words:
            with st.expander("Detailed Analysis"):
                tab1, tab2, tab3 = st.tabs(["Segments", "Words", "Confidence Analysis"])
                
                with tab1:
                    if result.segments:
                        segments_df = pd.DataFrame(result.segments)
                        st.dataframe(segments_df, use_container_width=True)
                    else:
                        st.info("No segment data available")
                
                with tab2:
                    if result.words:
                        words_df = pd.DataFrame(result.words)
                        st.dataframe(words_df, use_container_width=True)
                    else:
                        st.info("No word-level data available")
                
                with tab3:
                    if result.confidence_scores:
                        st.json(result.confidence_scores)
                        
                        # Low confidence segments
                        low_conf = result.get_low_confidence_segments()
                        if low_conf:
                            st.subheader("Low Confidence Segments")
                            for segment in low_conf:
                                st.warning(f"Segment: {segment.get('text', 'N/A')} (Confidence: {segment.get('avg_logprob', 0):.2f})")
                    else:
                        st.info("No confidence data available")
        
        # Export options
        st.subheader("Export Options")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 Download Text"):
                st.download_button(
                    "Download",
                    data=result.text,
                    file_name=f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
        
        with col2:
            if st.button("📊 Download JSON"):
                json_data = {
                    'text': result.text,
                    'segments': result.segments,
                    'words': result.words,
                    'metadata': result.metadata
                }
                st.download_button(
                    "Download",
                    data=json.dumps(json_data, indent=2),
                    file_name=f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col3:
            if result.segments and st.button("📺 Download SRT"):
                srt_content = self.generate_srt(result.segments)
                st.download_button(
                    "Download",
                    data=srt_content,
                    file_name=f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.srt",
                    mime="text/plain"
                )
    
    def run_transcription(self, uploaded_file, use_retry: bool, max_retries: int):
        """Run transcription on uploaded file"""
        try:
            st.session_state.transcription_in_progress = True
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            # Run transcription
            with st.spinner("Transcribing audio..."):
                if use_retry:
                    result = asyncio.run(
                        st.session_state.whisper_client.transcribe_with_retry(
                            tmp_file_path,
                            st.session_state.current_config,
                            max_retries=max_retries
                        )
                    )
                else:
                    result = asyncio.run(
                        st.session_state.whisper_client.transcribe(
                            tmp_file_path,
                            st.session_state.current_config
                        )
                    )
            
            # Store result
            st.session_state.transcription_results.append(result)
            
            # Update usage history
            st.session_state.usage_history.append({
                'timestamp': datetime.now(),
                'processing_time': result.processing_time,
                'confidence': result.get_average_confidence(),
                'duration': result.duration
            })
            
            # Cleanup
            os.unlink(tmp_file_path)
            
            st.success(f"Transcription completed in {result.processing_time:.2f}s!")
            
        except Exception as e:
            st.error(f"Transcription failed: {str(e)}")
        finally:
            st.session_state.transcription_in_progress = False
            st.rerun()
    
    def run_batch_transcription(self, uploaded_files, max_concurrent: int, use_retry: bool):
        """Run batch transcription on multiple files"""
        try:
            st.session_state.transcription_in_progress = True
            
            # Save all files temporarily
            temp_files = []
            for uploaded_file in uploaded_files:
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    temp_files.append(tmp_file.name)
            
            # Run batch transcription
            with st.spinner(f"Processing {len(uploaded_files)} files..."):
                results = asyncio.run(
                    st.session_state.whisper_client.batch_transcribe(
                        temp_files,
                        st.session_state.current_config,
                        max_concurrent=max_concurrent
                    )
                )
            
            # Store results
            st.session_state.transcription_results.extend(results)
            
            # Update usage history
            for result in results:
                st.session_state.usage_history.append({
                    'timestamp': datetime.now(),
                    'processing_time': result.processing_time,
                    'confidence': result.get_average_confidence(),
                    'duration': result.duration
                })
            
            # Cleanup
            for temp_file in temp_files:
                os.unlink(temp_file)
            
            successful = len([r for r in results if not r.metadata.get('error')])
            st.success(f"Batch processing completed! {successful}/{len(results)} files processed successfully.")
            
        except Exception as e:
            st.error(f"Batch processing failed: {str(e)}")
        finally:
            st.session_state.transcription_in_progress = False
            st.rerun()
    
    def save_configuration(self):
        """Save current configuration to session state"""
        if 'saved_configs' not in st.session_state:
            st.session_state.saved_configs = {}
        
        config_name = f"config_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        st.session_state.saved_configs[config_name] = st.session_state.current_config
        st.success(f"Configuration saved as {config_name}")
    
    def load_configuration(self):
        """Load configuration from session state"""
        if 'saved_configs' not in st.session_state or not st.session_state.saved_configs:
            st.warning("No saved configurations found")
            return
        
        config_names = list(st.session_state.saved_configs.keys())
        selected_config = st.selectbox("Select configuration to load", config_names)
        
        if st.button("Load Selected Configuration"):
            st.session_state.current_config = st.session_state.saved_configs[selected_config]
            st.success(f"Configuration {selected_config} loaded!")
            st.rerun()
    
    def save_custom_preset(self, preset_name: str):
        """Save current configuration as custom preset"""
        if 'custom_presets' not in st.session_state:
            st.session_state.custom_presets = {}
        
        st.session_state.custom_presets[preset_name] = st.session_state.current_config
        st.success(f"Preset '{preset_name}' saved!")
    
    def load_custom_preset(self, preset_name: str):
        """Load custom preset"""
        if 'custom_presets' not in st.session_state or preset_name not in st.session_state.custom_presets:
            st.warning(f"Preset '{preset_name}' not found")
            return
        
        st.session_state.current_config = st.session_state.custom_presets[preset_name]
        st.success(f"Preset '{preset_name}' loaded!")
        st.rerun()
    
    def generate_srt(self, segments: List[Dict[str, Any]]) -> str:
        """Generate SRT subtitle format from segments"""
        srt_content = ""
        
        for i, segment in enumerate(segments, 1):
            start_time = self.format_timestamp(segment.get('start', 0))
            end_time = self.format_timestamp(segment.get('end', 0))
            text = segment.get('text', '').strip()
            
            srt_content += f"{i}\n{start_time} --> {end_time}\n{text}\n\n"
        
        return srt_content
    
    def format_timestamp(self, seconds: float) -> str:
        """Format timestamp for SRT format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

def main():
    """Main function to run the Streamlit app"""
    try:
        ui = WhisperAdvancedUI()
        ui.render_main_interface()
        
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        logger.error(f"Streamlit app error: {str(e)}")

if __name__ == "__main__":
    main()