#!/usr/bin/env python3
"""
Audio/Video Transcription and Entity Extraction App (API Refactored Version)
This version uses API endpoints instead of direct backend imports
"""

import streamlit as st
import os
import logging
import tempfile
import time
from typing import Optional, Dict, Any
from ui_styles_fixed import apply_theme, render_theme_selector

# Import configuration
from config import Config, validate_environment, print_configuration_status

# Import API wrappers instead of direct modules
from api_wrappers import media, stt, ner_basic, ner_advanced, tts, utils

# Import other unchanged modules
from errors import (
    handle_error, create_user_error_message, AppError, 
    APIError, FileProcessingError, MediaProcessingError,
    TranscriptionError, NERError, TTSError, NetworkError,
    ErrorCode
)
from session_manager import session_manager, TranscriptionResults
from progress_indicators import (
    progress_context, create_processing_steps, create_admin_processing_steps,
    show_file_validation_feedback, show_processing_tips, show_loading_animation
)
from health_check import health_check_endpoint, detailed_health_endpoint, metrics_endpoint

# Import UI enhancement modules
from ui_styles import inject_custom_css, apply_theme_toggle, create_drag_drop_enhancement, add_smooth_transitions
from enhanced_components import (
    enhanced_file_uploader, enhanced_progress_indicator, enhanced_metric_display,
    enhanced_entity_display, enhanced_loading_state, enhanced_audio_player,
    create_responsive_layout
)
from entity_visualization import render_enhanced_entity_display, create_entity_visualizer

# Import advanced processing modules
from advanced_processing import (
    process_audio_with_advanced_features, render_advanced_results,
    render_advanced_processing_options, show_advanced_features_help,
    initialize_advanced_session_state
)

# Import multi-language support modules
from multilingual_transcription import (
    multilingual_transcriber, multilingual_ui, MultilingualTranscriptionResult
)
from language_support import (
    multilingual_ui as lang_ui, translation_service, realtime_processor,
    get_supported_languages, get_language_name
)

# Import visual search modules
from visual_search_ui import visual_search_ui
from visual_search import visual_search_engine

# Import AI provider integration modules
from ai_provider_ui import ai_provider_ui
from ai_provider_integrations import provider_manager, enhanced_tts, enhanced_stt

# Import advanced content analysis modules
from advanced_content_analysis_ui import advanced_content_analysis_ui
from advanced_content_analysis import advanced_content_analyzer

# Import batch processing modules
from batch_interface import render_batch_interface, cleanup_batch_session

# Import admin analytics modules
from admin_analytics import admin_analytics
from voice_library import voice_library_manager
from script_templates import script_template_manager

# Import search and diarization modules
from search.search_ui import SearchUI
from search.analytics_ui import AnalyticsUI
from speaker_diarization.diarization_ui import DiarizationUI

# Import video processing modules
from video_ui import VideoUI

# Import content insights modules
from content_insights_ui import ContentInsightsUI

# Import export modules
from export_ui import ExportUI

# Import theme and security modules
from ui_styles_fixed import apply_theme, render_theme_selector
from security_ui import SecurityUI, render_privacy_notice
from security_manager import create_security_manager

# Import structured content analyzer
from structured_content_analyzer import StructuredContentAnalyzer

# Import accessibility modules
from accessibility import check_accessibility, AccessibilityReport

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Streamlit page
st.set_page_config(
    page_title="Audio/Video Transcription & Analysis",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/audio-transcription',
        'Report a bug': 'https://github.com/yourusername/audio-transcription/issues',
        'About': 'Audio/Video Transcription and Entity Extraction Tool'
    }
)

# Initialize session state
def init_session_state():
    """Initialize all session state variables"""
    if 'config' not in st.session_state:
        st.session_state.config = Config()
    
    # Initialize advanced features
    initialize_advanced_session_state()
    
    # Initialize other session variables
    if 'current_theme' not in st.session_state:
        st.session_state.current_theme = 'light'
    
    if 'processing_history' not in st.session_state:
        st.session_state.processing_history = []
    
    if 'user_preferences' not in st.session_state:
        st.session_state.user_preferences = {
            'default_language': 'en-US',
            'auto_save': True,
            'show_tips': True
        }

def process_media_file(uploaded_file, language: str, entity_types: list, enable_tts: bool = False) -> Dict[str, Any]:
    """Process uploaded media file through the pipeline using API"""
    results = {}
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            temp_path = tmp_file.name
        
        # Process based on file type
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        if file_extension in ['.mp4', '.avi', '.mov', '.mkv']:
            # Extract audio from video
            with st.spinner("Extracting audio from video..."):
                audio_path = media.extract_audio(temp_path)
                results['audio_path'] = audio_path
        else:
            audio_path = temp_path
        
        # Transcribe audio
        with st.spinner("Transcribing audio..."):
            transcription = stt.transcribe(audio_path, language=language)
            results['transcription'] = transcription
        
        # Extract entities
        if transcription and transcription.get('text'):
            with st.spinner("Extracting entities..."):
                entities = ner_basic.extract_entities(
                    transcription['text'],
                    entity_types=entity_types if entity_types else None
                )
                results['entities'] = entities
        
        # Generate TTS if enabled
        if enable_tts and transcription and transcription.get('text'):
            with st.spinner("Generating speech..."):
                tts_path = tts.synthesize(transcription['text'])
                results['tts_audio'] = tts_path
        
        # Clean up temporary files
        if temp_path != audio_path:
            os.unlink(temp_path)
        
        return results
        
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        st.error(f"Processing failed: {str(e)}")
        # Clean up on error
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        if 'audio_path' in locals() and audio_path != temp_path and os.path.exists(audio_path):
            os.unlink(audio_path)
        raise

def main():
    """Main application function"""
    # Initialize session state
    init_session_state()
    
    # Apply theme
    apply_theme()
    
    # Inject custom CSS
    inject_custom_css()
    add_smooth_transitions()
    
    # Create security manager
    security_manager = create_security_manager()
    
    # Render privacy notice if needed
    render_privacy_notice(security_manager)
    
    # Sidebar
    with st.sidebar:
        st.title("🎙️ Transcription & Analysis")
        
        # Theme selector
        render_theme_selector()
        
        # Navigation
        page = st.selectbox(
            "Navigation",
            ["Home", "Batch Processing", "Search", "Analytics", "Settings", "Help"]
        )
        
        # API Connection Status
        with st.expander("API Status", expanded=False):
            try:
                from api_client import get_api_client
                api_client = get_api_client()
                user_info = api_client.get_current_user()
                if user_info:
                    st.success("✅ Connected to API")
                    st.caption(f"User: {user_info.get('email', 'Unknown')}")
                else:
                    st.warning("⚠️ Not authenticated")
            except:
                st.error("❌ API connection failed")
        
        # Language selection
        st.subheader("Language Settings")
        languages = stt.get_supported_languages()
        selected_language = st.selectbox(
            "Transcription Language",
            languages,
            index=languages.index("en-US") if "en-US" in languages else 0
        )
        
        # Entity types selection
        st.subheader("Entity Extraction")
        entity_types = st.multiselect(
            "Entity Types",
            ["PERSON", "ORG", "LOC", "DATE", "TIME", "MONEY", "PERCENT"],
            default=["PERSON", "ORG", "LOC"]
        )
        
        # TTS option
        enable_tts = st.checkbox("Enable Text-to-Speech", value=False)
    
    # Main content area
    if page == "Home":
        st.title("Audio/Video Transcription & Entity Extraction")
        st.markdown("Upload your media files to transcribe and analyze content")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['mp3', 'wav', 'mp4', 'avi', 'mov', 'mkv', 'flac', 'ogg'],
            help="Supported formats: MP3, WAV, MP4, AVI, MOV, MKV, FLAC, OGG"
        )
        
        if uploaded_file is not None:
            # File info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("File Size", f"{uploaded_file.size / 1024 / 1024:.2f} MB")
            with col2:
                st.metric("File Type", uploaded_file.type)
            with col3:
                st.metric("File Name", uploaded_file.name)
            
            # Process button
            if st.button("Process File", type="primary", use_container_width=True):
                try:
                    # Process the file
                    results = process_media_file(
                        uploaded_file,
                        selected_language,
                        entity_types,
                        enable_tts
                    )
                    
                    # Display results
                    st.success("Processing completed successfully!")
                    
                    # Transcription results
                    if 'transcription' in results:
                        st.subheader("📝 Transcription")
                        transcription = results['transcription']
                        
                        # Display text
                        st.text_area(
                            "Transcribed Text",
                            transcription.get('text', ''),
                            height=200
                        )
                        
                        # Metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Duration", utils.format_duration(transcription.get('duration', 0)))
                        with col2:
                            st.metric("Confidence", f"{transcription.get('confidence', 0):.2%}")
                        with col3:
                            st.metric("Words", len(transcription.get('text', '').split()))
                    
                    # Entity results
                    if 'entities' in results:
                        st.subheader("🏷️ Named Entities")
                        entities = results['entities']
                        
                        if entities:
                            # Entity visualization
                            render_enhanced_entity_display(entities, transcription.get('text', ''))
                        else:
                            st.info("No entities found in the text")
                    
                    # TTS results
                    if 'tts_audio' in results:
                        st.subheader("🔊 Text-to-Speech")
                        st.audio(results['tts_audio'])
                        
                        # Download button
                        with open(results['tts_audio'], 'rb') as f:
                            st.download_button(
                                "Download Audio",
                                f.read(),
                                file_name=f"{os.path.splitext(uploaded_file.name)[0]}_tts.mp3",
                                mime="audio/mp3"
                            )
                    
                    # Save to session
                    session_manager.save_results(
                        TranscriptionResults(
                            filename=uploaded_file.name,
                            transcription=results.get('transcription', {}),
                            entities=results.get('entities', []),
                            processing_time=time.time()
                        )
                    )
                    
                except Exception as e:
                    st.error(f"Processing failed: {str(e)}")
                    logger.error(f"Processing error: {str(e)}", exc_info=True)
    
    elif page == "Batch Processing":
        render_batch_interface()
    
    elif page == "Search":
        search_ui = SearchUI()
        search_ui.render()
    
    elif page == "Analytics":
        analytics_ui = AnalyticsUI()
        analytics_ui.render()
    
    elif page == "Settings":
        st.title("⚙️ Settings")
        
        # User preferences
        st.subheader("User Preferences")
        
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.user_preferences['default_language'] = st.selectbox(
                "Default Language",
                stt.get_supported_languages(),
                index=0
            )
        
        with col2:
            st.session_state.user_preferences['auto_save'] = st.checkbox(
                "Auto-save Results",
                value=st.session_state.user_preferences['auto_save']
            )
        
        st.session_state.user_preferences['show_tips'] = st.checkbox(
            "Show Processing Tips",
            value=st.session_state.user_preferences['show_tips']
        )
        
        # API Configuration
        st.subheader("API Configuration")
        api_url = st.text_input(
            "API URL",
            value=st.secrets.get("API_URL", "http://localhost:8000"),
            help="URL of the backend API server"
        )
        
        if st.button("Test Connection"):
            try:
                from api_client import APIClient
                test_client = APIClient(api_url)
                response = test_client._make_request("GET", "/api/v1/health")
                if response:
                    st.success("✅ Connection successful!")
                else:
                    st.error("❌ Connection failed")
            except Exception as e:
                st.error(f"Connection error: {str(e)}")
    
    elif page == "Help":
        st.title("📚 Help & Documentation")
        
        st.markdown("""
        ### Getting Started
        
        1. **Upload a File**: Use the file uploader to select your audio or video file
        2. **Select Language**: Choose the language of the audio content
        3. **Choose Entity Types**: Select which types of entities to extract
        4. **Process**: Click the Process button to start transcription and analysis
        
        ### Supported Formats
        - Audio: MP3, WAV, FLAC, OGG
        - Video: MP4, AVI, MOV, MKV
        
        ### Features
        - **Transcription**: Convert speech to text with high accuracy
        - **Entity Extraction**: Identify people, organizations, locations, and more
        - **Text-to-Speech**: Convert transcribed text back to speech
        - **Batch Processing**: Process multiple files at once
        - **Search**: Search through your transcription history
        - **Analytics**: View insights and statistics
        
        ### API Integration
        This application uses REST APIs for all processing. Make sure the API server is running and accessible.
        """)

if __name__ == "__main__":
    main()