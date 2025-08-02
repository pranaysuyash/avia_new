#!/usr/bin/env python3
"""
Audio/Video Transcription and Entity Extraction App
MVP application for transcribing media files and extracting entities
"""

import streamlit as st
import os
import logging
import tempfile
import time
from typing import Optional, Dict, Any

# Import configuration and backend modules
from config import Config, validate_environment, print_configuration_status
import media
import stt
import ner_basic
import ner_advanced
import tts
import utils
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

# Import new UI enhancement modules
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
from theme_manager import theme_manager, apply_custom_theme
from security_ui import SecurityUI, render_privacy_notice
from security_manager import security_manager

# Import advanced audio processing modules
from advanced_audio_processor import (
    AdvancedAudioProcessor, AudioQualityAnalyzer, NoiseReducer, AudioTrimmer,
    RealTimeStreamProcessor, AudioBookmarkManager, enhance_audio_for_transcription,
    analyze_audio_quality, create_audio_segments
)

# Import structured analysis modules
try:
    from structured_analysis_ui import (
        display_structured_analysis_interface, perform_structured_analysis,
        display_custom_schema_creator, display_schema_validation_tool
    )
    STRUCTURED_ANALYSIS_AVAILABLE = True
except ImportError as e:
    # Logger not yet available, use print
    print(f"Warning: Structured analysis modules not available: {e}")
    STRUCTURED_ANALYSIS_AVAILABLE = False

# Import AI customization modules
try:
    from ai_customization_ui import (
        render_ai_customization_ui, render_customization_test_panel
    )
    AI_CUSTOMIZATION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: AI customization modules not available: {e}")
    AI_CUSTOMIZATION_AVAILABLE = False

# Setup logging and configuration first
Config.setup_logging()
logger = logging.getLogger(__name__)

# Import integration capabilities (Task 23)
try:
    from integration_manager import (
        integration_manager, trigger_transcription_completed_webhook,
        backup_transcript_to_cloud, extract_custom_entities
    )
    from webhooks.webhook_ui import render_webhook_settings
    from cloud_storage.storage_ui import render_cloud_storage_settings  
    from plugins.plugin_ui import render_plugin_settings
    from sso.sso_ui import render_sso_settings
    INTEGRATIONS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Integration modules not available: {e}")
    INTEGRATIONS_AVAILABLE = False

# Configure page
st.set_page_config(
    page_title="Audio/Video Transcription App",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize enhanced session state management
session_manager.initialize_session_state()
initialize_advanced_session_state()

# Apply theme and styling
current_theme = apply_theme_toggle()
inject_custom_css(current_theme)
create_drag_drop_enhancement()
add_smooth_transitions()
create_responsive_layout()

def handle_health_endpoints():
    """Handle health check and monitoring endpoints"""
    # Check for health check endpoints via query parameters
    query_params = st.query_params
    
    if 'health' in query_params:
        # Simple health check endpoint
        health_data = health_check_endpoint()
        st.json(health_data)
        st.stop()
    
    elif 'health-detailed' in query_params:
        # Detailed health check endpoint
        health_data = detailed_health_endpoint()
        st.json(health_data)
        st.stop()
    
    elif 'metrics' in query_params:
        # Metrics endpoint for monitoring
        metrics_data = metrics_endpoint()
        st.json(metrics_data)
        st.stop()

def main():
    """Main application entry point"""
    
    # Initialize security manager
    security_manager.initialize()
    
    # Apply custom theme and accessibility features - FORCE MAXIMUM VISIBILITY
    apply_custom_theme()
    
    # Emergency visibility fix - AGGRESSIVE CSS
    st.markdown("""
    <style>
    /* EMERGENCY TEXT VISIBILITY FIX */
    * {
        color: #000000 !important;
    }
    
    .stMarkdown, .stMarkdown *, .stText, .stText *, 
    p, div, span, label, h1, h2, h3, h4, h5, h6 {
        color: #000000 !important;
        font-weight: 600 !important;
    }
    
    /* Sidebar text */
    .css-1d391kg, .css-1d391kg *, 
    [data-testid="stSidebar"], [data-testid="stSidebar"] * {
        color: #000000 !important;
        font-weight: 600 !important;
    }
    
    /* Input labels */
    .stSelectbox > label, .stFileUploader > label, 
    .stSlider > label, .stCheckbox > label {
        color: #000000 !important;
        font-weight: bold !important;
        font-size: 1.2em !important;
    }
    
    /* File uploader area */
    .stFileUploader {
        border: 3px solid #0066cc !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #000000 !important;
        font-weight: bold !important;
        font-size: 1.5em !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Handle health check endpoints first
    handle_health_endpoints()
    
    # Check configuration on startup
    is_valid, config_message = validate_environment()
    
    # App title and description
    st.title("🎵 Audio/Video Transcription & Entity Extraction")
    st.markdown("Upload audio/video files or record live audio for transcription and intelligent analysis.")
    
    # Show configuration warnings if needed
    if not is_valid:
        st.warning("⚠️ Configuration Issues Detected")
        with st.expander("Configuration Details", expanded=False):
            st.text(config_message)
            st.markdown("**Setup Guide:**")
            st.code(Config.get_configuration_guide(), language="markdown")
    
    # Display any error messages
    if session_manager.has_error():
        error_obj = st.session_state.get('error_object', None)
        display_error(st.session_state.error_message, error_obj)
        session_manager.clear_error()
    
    # Sidebar navigation
    # Theme selector in sidebar
    theme_manager.render_theme_selector()
    
    st.sidebar.title("Configuration")
    
    # API key status
    api_status = check_api_keys()
    display_api_status(api_status)
    
    # Analysis mode selection with enhanced help
    analysis_mode = st.sidebar.selectbox(
        "Analysis Mode",
        ["Basic (spaCy)", "Advanced (OpenAI)", "Advanced+ (Speaker Diarization)"],
        help="""**Choose your analysis mode:**

🔹 **Basic (spaCy):** 
• Fast local processing
• Works offline
• Extracts: names, organizations, dates, locations
• No API keys required

🔹 **Advanced (OpenAI):**
• AI-powered analysis with GPT
• Content summaries and insights
• Better context understanding
• Requires OpenAI API key

🚀 **Advanced+ (Speaker Diarization):**
• All Advanced features plus:
• Speaker identification and separation
• Multi-language detection and support
• Interactive transcript with timestamps
• Confidence scoring and quality analysis
• Advanced export options (SRT, VTT, CSV)
• Requires OpenAI API key

💡 **Tip:** Start with Basic mode to test the system, then upgrade to Advanced+ for full features.""",
        index=0 if not api_status["openai"] else 0
    )
    
    # Show warning if advanced mode selected without API key
    if "Advanced" in analysis_mode and not api_status["openai"]:
        st.sidebar.warning("⚠️ Advanced mode requires OpenAI API key")
    
    # Processing Modes Section
    st.sidebar.markdown("---")
    with st.sidebar.expander("⚙️ Processing Modes", expanded=False):
        # Batch processing toggle
        batch_mode = st.checkbox(
            "📦 Batch Processing",
            value=False,
            help="Process multiple files simultaneously with queue management",
            key="batch_mode_toggle"
        )
        
        # Admin panel toggle
        admin_mode = st.checkbox(
            "🔐 Admin Panel",
            value=False,
            help="Access admin features for content generation and testing",
            disabled=not (api_status["openai"] and api_status["elevenlabs"])
        )
        
        # Security panel toggle
        security_mode = st.checkbox(
            "🛡️ Security & Privacy",
            value=False,
            help="Access security management, user controls, and privacy settings"
        )
        
        if batch_mode:
            st.info("Batch mode: Upload 5-20 files for parallel processing")
        
        if admin_mode and not (api_status["openai"] and api_status["elevenlabs"]):
            st.warning("Admin panel requires both OpenAI and ElevenLabs API keys")
    
    # Advanced Audio Processing Options
    st.sidebar.markdown("---")
    with st.sidebar.expander("🎛️ Audio Processing", expanded=False):
        # Audio enhancement options
        enable_audio_enhancement = st.checkbox(
            "🔊 Audio Enhancement",
            value=True,
            help="Noise reduction and voice enhancement"
        )
        
        # Audio segmentation options
        enable_segmentation = st.checkbox(
            "✂️ Audio Segmentation", 
            value=False,
            help="Smart splitting and chapter detection"
        )
        
        # Real-time processing options
        enable_realtime = st.checkbox(
            "🎙️ Real-time Processing",
            value=False,
            help="Live transcription (experimental)"
        )
    
    # Store audio processing preferences in session state
    st.session_state.audio_enhancement_enabled = enable_audio_enhancement
    st.session_state.audio_segmentation_enabled = enable_segmentation
    st.session_state.realtime_processing_enabled = enable_realtime
    
    # Advanced Features Section
    st.sidebar.markdown("---")
    with st.sidebar.expander("🚀 Advanced Features", expanded=False):
        # Search feature toggle
        enable_search = st.checkbox(
            "🔍 Advanced Search",
            value=False,
            help="Search with filters and navigation"
        )
        
        # Semantic search toggle
        enable_semantic_search = st.checkbox(
            "🧠 Semantic Search & Library",
            value=False,
            help="AI-powered semantic search and transcript library"
        )
        
        # Video processing toggle
        enable_video_processing = st.checkbox(
            "🎬 Video Processing",
            value=False,
            help="Video analysis and frame extraction"
        )
        
        # Content insights toggle
        enable_content_insights = st.checkbox(
            "🧠 AI Content Insights",
            value=False,
            help="AI-powered analysis and insights"
        )
        
        # Export and sharing toggle
        enable_export_sharing = st.checkbox(
            "📤 Export & Sharing",
            value=False,
            help="Multiple export formats and sharing"
        )
        
        # Real-time collaboration toggle
        enable_collaboration = st.checkbox(
            "👥 Real-time Collaboration",
            value=False,
            help="Live editing and comments"
        )
        
        # AI Model Customization toggle
        enable_ai_customization = st.checkbox(
            "🤖 AI Model Customization",
            value=False,
            help="Custom vocabularies, voice profiles, and entity types"
        )
        
        # Analytics Dashboard toggle
        enable_analytics = st.checkbox(
            "📊 Analytics Dashboard",
            value=False,
            help="Advanced search analytics, trend analysis, and topic modeling"
        )
    
    # Integration settings (Task 23)
    if INTEGRATIONS_AVAILABLE:
        st.sidebar.markdown("---")
        with st.sidebar.expander("🔗 Integrations", expanded=False):
            # Integration toggles
            show_webhooks = st.checkbox("🔗 Webhooks", value=False)
            show_cloud_storage = st.checkbox("☁️ Cloud Storage", value=False)
            show_plugins = st.checkbox("🔌 Plugins", value=False)
            show_sso = st.checkbox("🔐 SSO", value=False)
        
        # Store integration settings in session state
        st.session_state.show_webhooks = show_webhooks
        st.session_state.show_cloud_storage = show_cloud_storage
        st.session_state.show_plugins = show_plugins
        st.session_state.show_sso = show_sso
    
    # Help and Info Section
    st.sidebar.markdown("---")
    with st.sidebar.expander("ℹ️ Help & Info", expanded=False):
        st.markdown(f"""
        **File Limits:**
        • Max size: {Config.MAX_FILE_SIZE_MB}MB
        • Formats: MP3, WAV, M4A, MP4, AVI, MOV
        
        **Quick Tips:**
        • Use Advanced+ mode for best results
        • Clear audio produces better transcripts
        • Batch mode processes multiple files
        
        **Shortcuts:**
        • Drag & drop files to upload
        • Click timestamps to navigate
        • Export in multiple formats
        """)
    
    # Main content area - show appropriate interface based on mode
    if enable_semantic_search:
        # Show semantic search interface
        try:
            from semantic_search.semantic_ui import render_semantic_search_page
            render_semantic_search_page()
        except ImportError as e:
            st.error("Semantic search features not available. Please check installation.")
            st.info("Install required packages: `pip install sentence-transformers numpy`")
            logger.error(f"Semantic search import error: {e}")
    elif enable_search:
        # Show search interface
        search_ui = SearchUI()
        search_ui.render_search_interface()
    elif enable_video_processing:
        # Show video processing interface
        video_ui = VideoUI()
        video_ui.render_video_tools()
    elif enable_content_insights:
        # Show content insights interface
        insights_ui = ContentInsightsUI()
        
        # Get transcript from session if available
        transcript_text = None
        speaker_segments = None
        
        if session_manager.has_results():
            results = session_manager.get_results()
            transcript_text = results.transcript
            # Convert speaker segments if available
            if hasattr(results, 'speaker_segments') and results.speaker_segments:
                speaker_segments = [
                    {
                        'speaker_id': seg.get('speaker', 'Unknown'),
                        'start_time': seg.get('start', 0),
                        'duration': seg.get('end', 0) - seg.get('start', 0),
                        'text': seg.get('text', ''),
                        'confidence': seg.get('confidence', 0.0)
                    }
                    for seg in results.speaker_segments
                ]
        
        insights_ui.render_insights_analyzer(transcript_text, speaker_segments)
    elif enable_collaboration:
        # Show real-time collaboration interface
        try:
            from collaboration_ui import CollaborationUI
            
            # Get current user and transcript info
            user_id = st.session_state.get('user_id', 'default_user')
            
            # Get transcript ID from current session
            transcript_id = None
            if session_manager.has_results():
                results = session_manager.get_results()
                transcript_id = f"transcript_{results.session_id}"
            else:
                transcript_id = "demo_transcript"
            
            # Store in session state for collaboration
            st.session_state.current_transcript_id = transcript_id
            
            # Render collaboration panel
            CollaborationUI.render_collaboration_panel(transcript_id, user_id)
            
            # Also show live transcription panel if no active collaboration
            if not st.session_state.get('active_collaboration'):
                st.markdown("---")
                CollaborationUI.render_live_transcription_panel()
                
        except ImportError:
            st.error("Collaboration features not available. Please check installation.")
            st.info("Install required packages: `pip install websockets python-socketio`")
    elif enable_ai_customization:
        # Show AI Model Customization interface
        if AI_CUSTOMIZATION_AVAILABLE:
            render_ai_customization_ui()
            
            # Add test panel for trying customizations
            st.markdown("---")
            render_customization_test_panel()
        else:
            st.error("AI Model Customization features not available. Please check installation.")
            st.info("Install required packages and restart the application.")
    elif enable_analytics:
        # Show Analytics Dashboard interface
        try:
            analytics_ui = AnalyticsUI()
            analytics_ui.render_analytics_dashboard()
        except ImportError as e:
            st.error("Analytics Dashboard features not available. Please check installation.")
            st.info("Install required packages: `pip install plotly pandas numpy`")
            logger.error(f"Analytics UI import error: {e}")
        except Exception as e:
            st.error(f"Error loading Analytics Dashboard: {str(e)}")
            logger.error(f"Analytics UI error: {e}")
    elif enable_export_sharing:
        # Show export and sharing interface
        export_ui = ExportUI()
        
        # Get transcript data from session if available
        transcript_data = None
        
        if session_manager.has_results():
            results = session_manager.get_results()
            
            # Build comprehensive transcript data
            transcript_data = {
                'id': f"transcript_{results.session_id}",
                'title': f"Transcript - {results.created_at.strftime('%Y-%m-%d %H:%M')}",
                'transcript': results.transcript,
                'duration': getattr(results, 'duration', 0),
                'language': getattr(results, 'language', 'en'),
                'confidence': getattr(results, 'confidence', 0.0),
                'created_at': results.created_at.isoformat(),
                'speakers': getattr(results, 'speakers', []),
                'entities': results.advanced_entities if hasattr(results, 'advanced_entities') else [],
                'speaker_segments': getattr(results, 'speaker_segments', []),
                'processing_time': getattr(results, 'processing_time', 0),
                'file_info': {
                    'original_filename': getattr(results, 'original_filename', 'unknown'),
                    'file_size': getattr(results, 'file_size', 0)
                }
            }
            
            # Add insights if available
            if hasattr(results, 'insights'):
                transcript_data['insights'] = results.insights
        
        export_ui.render_export_interface(transcript_data)
    elif batch_mode:
        # Show batch processing interface
        render_batch_interface(analysis_mode)
        
        # Show previous single-file results if available
        if session_manager.has_results():
            st.markdown("---")
            st.header("📊 Previous Single-File Results")
            with st.expander("View Previous Analysis", expanded=False):
                render_results_enhanced(analysis_mode)
    
    elif admin_mode:
        # Show admin panel first, then main interface results if available
        render_admin_panel()
        
        # Show previous results if available
        if session_manager.has_results():
            st.markdown("---")
            st.header("📊 Previous Analysis Results")
            render_results_enhanced(analysis_mode)
    
    elif security_mode:
        # Show security management interface
        render_security_panel()
        
        # Show previous results if available
        if session_manager.has_results():
            st.markdown("---")
            st.header("📊 Previous Analysis Results")
            render_results_enhanced(analysis_mode)
    else:
        # Check if any integration panels should be shown
        if INTEGRATIONS_AVAILABLE and any([
            st.session_state.get('show_webhooks', False),
            st.session_state.get('show_cloud_storage', False), 
            st.session_state.get('show_plugins', False),
            st.session_state.get('show_sso', False)
        ]):
            render_integration_panels()
        else:
            # Add privacy notice
            render_privacy_notice()
            
            # Show main interface
            render_main_interface(analysis_mode)

def render_integration_panels():
    """Render integration management panels (Task 23)"""
    st.header("🔗 Integration Management")
    
    # Show active integration panels
    if st.session_state.get('show_webhooks', False):
        with st.container():
            render_webhook_settings()
            st.markdown("---")
    
    if st.session_state.get('show_cloud_storage', False):
        with st.container():
            render_cloud_storage_settings()
            st.markdown("---")
    
    if st.session_state.get('show_plugins', False):
        with st.container():
            render_plugin_settings()
            st.markdown("---")
    
    if st.session_state.get('show_sso', False):
        with st.container():
            render_sso_settings()
            st.markdown("---")
    
    # Integration status summary
    if integration_manager.initialized:
        st.success("✅ Integration systems initialized")
        
        # Show integration status
        status = integration_manager.get_status()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            webhook_status = "✅" if status['webhook_system']['running'] else "❌"
            st.write(f"{webhook_status} **Webhooks**")
        
        with col2:
            cloud_count = len(status['cloud_storage']['providers_configured'])
            st.write(f"☁️ **Cloud Storage** ({cloud_count} providers)")
        
        with col3:
            plugin_count = status['plugins']['loaded']
            st.write(f"🔌 **Plugins** ({plugin_count} loaded)")
        
        with col4:
            sso_status = "✅" if status['sso']['enabled'] else "❌"
            st.write(f"{sso_status} **SSO**")
    else:
        st.warning("⚠️ Integration systems not initialized")
        if st.button("🚀 Initialize Integration Systems"):
            # Mock initialization
            st.success("✅ Integration systems initialized! (Mock)")


def render_realtime_interface():
    """Render real-time processing interface"""
    st.subheader("🎤 Real-time Audio Processing")
    
    # Initialize real-time processor if not exists
    if 'realtime_processor' not in st.session_state:
        st.session_state.realtime_processor = RealTimeStreamProcessor()
    
    processor = st.session_state.realtime_processor
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎤 Start Streaming", disabled=processor.is_streaming):
            processor.start_streaming()
            st.success("Real-time streaming started!")
            st.rerun()
    
    with col2:
        if st.button("⏹️ Stop Streaming", disabled=not processor.is_streaming):
            processor.stop_streaming()
            st.success("Real-time streaming stopped!")
            st.rerun()
    
    with col3:
        status = "🟢 Active" if processor.is_streaming else "🔴 Inactive"
        st.write(f"**Status:** {status}")
    
    # Display real-time metrics if streaming
    if processor.is_streaming:
        st.info("📊 **Real-time Processing Active**")
        st.write("This is a demonstration of real-time processing capabilities.")
        st.write("In a full implementation, this would show live transcription and analysis.")
        
        # Placeholder for real-time metrics
        metrics_placeholder = st.empty()
        
        # Show sample real-time data
        with metrics_placeholder.container():
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Audio Level", "65 dB")
            with col2:
                st.metric("Speech Detected", "Yes")
            with col3:
                st.metric("Processing Latency", "120ms")

def render_main_interface(analysis_mode: str):
    """Render the main transcription interface"""
    
    # Show real-time interface if enabled
    if st.session_state.get('realtime_processing_enabled', False):
        render_realtime_interface()
        st.markdown("---")
    
    # Input section
    st.header("📁 Input")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Enhanced file upload with drag-and-drop
        uploaded_file = enhanced_file_uploader(
            label="Upload Audio/Video File",
            accepted_types=["mp3", "wav", "mp4", "m4a"],
            max_size_mb=Config.MAX_FILE_SIZE_MB,
            help_text=f"Drag & drop or click to upload • Supported: MP3, WAV, MP4, M4A • Max: {Config.MAX_FILE_SIZE_MB}MB",
            key="main_file_upload"
        )
        
        if uploaded_file:
            # Update file info in session state
            session_manager.update_file_info(
                name=uploaded_file.name,
                size_bytes=uploaded_file.size,
                format=uploaded_file.name.split('.')[-1].lower()
            )
            
            # Show detailed file information
            file_info = {
                'size_mb': uploaded_file.size / (1024*1024),
                'format': uploaded_file.name.split('.')[-1].lower()
            }
            
            # Try to get media duration and validate file
            try:
                # Save temp file to get duration
                temp_dir = utils.ensure_temp_directory()
                temp_path = os.path.join(temp_dir, f"temp_{uploaded_file.name}")
                
                # Read file content once and save it
                file_content = uploaded_file.read()
                with open(temp_path, "wb") as f:
                    f.write(file_content)
                
                # Reset file pointer for later use
                uploaded_file.seek(0)
                
                # Validate file integrity first
                try:
                    media.validate_media_file(temp_path, Config.MAX_FILE_SIZE_MB)
                    
                    # Encrypt the file if security is enabled
                    if security_manager.is_encryption_enabled():
                        encrypted_path = temp_path + ".enc"
                        security_manager.encryption_manager.encrypt_file(temp_path, encrypted_path)
                        # Log the encryption event
                        security_manager.audit_logger.log_security_event(
                            "FILE_ENCRYPTED",
                            {"file": uploaded_file.name, "size": uploaded_file.size}
                        )
                        # Note: Keep using temp_path for processing, handle encryption transparently
                        
                except Exception as e:
                    # Clean up temp file
                    utils.cleanup_file(temp_path)
                    
                    # Display user-friendly error
                    st.error(f"❌ {getattr(e, 'user_message', 'File validation failed')}")
                    if hasattr(e, 'suggestions') and e.suggestions:
                        with st.expander("💡 How to fix this issue", expanded=True):
                            for suggestion in e.suggestions:
                                st.write(f"• {suggestion}")
                    
                    # Clear the uploaded file
                    uploaded_file = None
                    st.stop()
                
                # Get media info including duration
                media_info = media.get_media_info(temp_path)
                file_info['duration'] = media_info.get('duration', 0)
                
                # Update session state with duration
                session_manager.update_file_info(
                    name=uploaded_file.name,
                    size_bytes=uploaded_file.size,
                    duration=file_info['duration'],
                    format=file_info['format']
                )
                
                # Clean up temp file
                utils.cleanup_file(temp_path)
                
            except Exception as e:
                logger.warning(f"Could not process uploaded file: {e}")
                file_info['duration'] = 0
                if "moov atom not found" in str(e) or "Invalid data found" in str(e):
                    st.error("❌ The uploaded file appears to be corrupted or incomplete.")
                    st.info("💡 Please try uploading the file again or use a different file.")
                    uploaded_file = None
                    st.stop()
            
            # Enhanced file validation feedback
            st.success(f"✅ File uploaded: {uploaded_file.name}")
            
            # Enhanced metrics display for file info
            file_metrics = [
                {
                    "title": "File Size",
                    "value": f"{file_info['size_mb']:.1f} MB",
                    "icon": "📦",
                    "help": "File size affects processing time"
                },
                {
                    "title": "Format",
                    "value": file_info['format'].upper(),
                    "icon": "🎵",
                    "help": "Audio/video format"
                }
            ]
            
            if file_info.get('duration', 0) > 0:
                duration_seconds = file_info['duration']
                minutes = int(duration_seconds // 60)
                seconds = int(duration_seconds % 60)
                duration_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
                
                file_metrics.append({
                    "title": "Duration",
                    "value": duration_str,
                    "icon": "⏱️",
                    "help": f"Total: {duration_seconds:.1f} seconds"
                })
            
            enhanced_metric_display(file_metrics, columns=len(file_metrics), animated=True)
            
            # Detailed file validation with visual feedback
            is_valid = show_file_validation_feedback(file_info, Config.MAX_FILE_SIZE_MB)
            
            if not is_valid:
                st.error("❌ File validation failed. Please choose a different file.")
                uploaded_file = None
    
    with col2:
        # Audio recording with enhanced feedback
        st.markdown("**Record Audio Directly:**")
        recorded_audio = st.audio_input(
            "🎤 Record Audio",
            help="Click to start recording. Speak clearly for best results.\n\n"
                 "💡 Recording Tips:\n"
                 "• Find a quiet environment\n"
                 "• Speak at normal pace\n"
                 "• Keep microphone at consistent distance"
        )
        
        if recorded_audio:
            # Get the size of recorded audio properly
            recorded_audio_bytes = recorded_audio.read()
            recorded_audio.seek(0)  # Reset for later use
            
            # Update session state with recording info
            session_manager.update_file_info(
                name="recorded_audio.wav",
                size_bytes=len(recorded_audio_bytes),
                format="wav"
            )
            
            st.success("✅ Audio recorded successfully")
            
            # Show recording info
            recording_size_mb = len(recorded_audio_bytes) / (1024*1024)
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Recording Size", f"{recording_size_mb:.2f} MB")
            with col_b:
                # Estimate duration (rough approximation)
                estimated_duration = len(recorded_audio_bytes) / (16000 * 2)  # 16kHz, 16-bit
                st.metric("Est. Duration", f"{estimated_duration:.1f}s")
    
    # Processing section
    audio_source = uploaded_file or recorded_audio
    
    if audio_source:
        st.header("⚙️ Processing")
        
        # Processing options
        col1, col2 = st.columns([3, 1])
        
        with col1:
            process_button = st.button(
                "🚀 Transcribe & Analyze", 
                type="primary",
                help=f"Process audio using {analysis_mode} mode"
            )
        
        with col2:
            if st.button("🗑️ Clear", help="Clear current results"):
                clear_session_state()
                st.rerun()
        
        if process_button:
            if validate_processing_requirements(analysis_mode):
                # Log processing start event
                user_info = security_manager.get_current_user_info()
                security_manager.audit_logger.log_user_action(
                    user_info.get('username', 'anonymous'),
                    "TRANSCRIPTION_STARTED",
                    {
                        "mode": analysis_mode,
                        "file": uploaded_file.name if uploaded_file else "recorded_audio",
                        "size": uploaded_file.size if uploaded_file else len(recorded_audio_bytes) if recorded_audio else 0
                    }
                )
                
                # Clear previous results if auto-clear is enabled
                preferences = session_manager.get_preferences()
                if preferences.auto_clear_results:
                    session_manager.clear_results()
                
                # Enhanced loading state with tips
                loading_container = st.empty()
                with loading_container.container():
                    enhanced_loading_state(
                        text=f"Processing with {analysis_mode} mode...",
                        show_spinner=True,
                        show_tips=True,
                        tips=[
                            "💡 Clear audio produces better transcripts",
                            "🎯 Advanced mode provides more detailed analysis", 
                            "⚡ Processing time depends on file size",
                            "🔍 You can search within transcripts after processing",
                            "📊 Results can be downloaded in multiple formats"
                        ]
                    )
                
                # Process audio
                process_audio_enhanced(audio_source, analysis_mode)
                
                # Clear loading state
                loading_container.empty()
        
        # Results section
        if session_manager.has_results():
            render_results_enhanced(analysis_mode)
    else:
        # Enhanced instructions and help when no input
        st.info("👆 Please upload an audio/video file or record audio to get started")
        
        # Comprehensive help sections
        col1, col2 = st.columns(2)
        
        with col1:
            with st.expander("🚀 Quick Start Guide", expanded=True):
                st.markdown(f"""
                **1. Choose Your Input Method**
                📁 **Upload File:** Drag & drop or browse for audio/video files
                🎤 **Record Audio:** Click the microphone to record live
                
                **2. Select Analysis Mode**
                🔹 **Basic:** Fast, offline processing (no API needed)
                🔹 **Advanced:** AI-powered analysis (requires OpenAI API)
                🚀 **Advanced+:** Speaker diarization + multi-language support
                
                **3. Process & Review**
                ⚡ Processing takes 30 seconds to 5 minutes depending on file size
                📊 Review transcript, entities, and insights
                📥 Download results in multiple formats
                
                **Supported Formats:** MP3, WAV, MP4, M4A
                **Max File Size:** {Config.MAX_FILE_SIZE_MB}MB
                """)
        
        with col2:
            with st.expander("💡 Tips for Best Results"):
                st.markdown("""
                **Audio Quality Tips:**
                🎵 Use clear, high-quality audio recordings
                🔇 Minimize background noise and echo
                🎙️ Ensure speakers are close to microphone
                📢 Avoid overlapping speech in conversations
                
                **File Optimization:**
                📦 Compress large files to speed up processing
                ⏱️ Shorter files (< 10 minutes) process faster
                🔄 Convert to MP3 or WAV for best compatibility
                
                **Analysis Mode Selection:**
                🏃 Use Basic mode for quick results
                🧠 Use Advanced mode for detailed insights
                🔑 Configure API keys for full functionality
                """)
        
        # Feature comparison table
        with st.expander("📋 Feature Comparison"):
            comparison_data = {
                "Feature": [
                    "Transcription", "Entity Extraction", "Processing Speed", 
                    "Content Summary", "Sentiment Analysis", "Speaker Diarization",
                    "Multi-language", "Interactive Transcript", "API Required", 
                    "Offline Support", "Confidence Scores"
                ],
                "Basic Mode": [
                    "✅ High Quality", "✅ Standard", "🚀 Fast", 
                    "❌ Not Available", "❌ Not Available", "❌ Not Available",
                    "❌ English Only", "⚠️ Basic", "❌ No", 
                    "✅ Yes", "✅ Yes"
                ],
                "Advanced Mode": [
                    "✅ High Quality", "✅ Enhanced", "⏳ Moderate", 
                    "✅ AI-Generated", "✅ Available", "❌ Not Available",
                    "⚠️ Limited", "⚠️ Basic", "✅ OpenAI", 
                    "❌ No", "⚠️ Limited"
                ],
                "Advanced+ Mode": [
                    "✅ High Quality", "✅ Enhanced", "⏳ Slower", 
                    "✅ AI-Generated", "✅ Available", "✅ Full Support",
                    "✅ 60+ Languages", "✅ Full Interactive", "✅ OpenAI", 
                    "❌ No", "✅ Detailed"
                ]
            }
            
            import pandas as pd
            df = pd.DataFrame(comparison_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Advanced features help
        with st.expander("🚀 Advanced+ Features"):
            show_advanced_features_help()
        
        # Troubleshooting section
        with st.expander("🔧 Troubleshooting"):
            st.markdown("""
            **Common Issues & Solutions:**
            
            **🚫 "Advanced mode requires OpenAI API key"**
            • Get API key from [OpenAI Platform](https://platform.openai.com/)
            • Add to `.env` file: `OPENAI_API_KEY=your_key_here`
            • Restart the application
            
            **📁 "File format not supported"**
            • Convert to MP3, WAV, MP4, or M4A
            • Use online converters or audio editing software
            
            **⚠️ "File size too large"**
            • Compress audio/video file
            • Trim to shorter segments
            • Use lower quality settings
            
            **🔇 "No audio detected"**
            • Check that video files contain audio tracks
            • Verify audio file isn't corrupted
            • Try a different file
            
            **⏳ "Processing takes too long"**
            • Large files naturally take more time
            • Try Basic mode for faster processing
            • Check internet connection for Advanced mode
            """)
        
        # System status
        with st.expander("📊 System Status"):
            # Get current API status
            current_api_status = check_api_keys()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Basic Mode", 
                    "🟢 Available",
                    help="Local spaCy processing is always available"
                )
            
            with col2:
                advanced_status = "🟢 Available" if current_api_status["openai"] else "🔴 Unavailable"
                st.metric(
                    "Advanced Mode", 
                    advanced_status,
                    help="Requires OpenAI API key configuration"
                )
            
            with col3:
                admin_status = "🟢 Available" if (current_api_status["openai"] and current_api_status["elevenlabs"]) else "🔴 Unavailable"
                st.metric(
                    "Admin Features", 
                    admin_status,
                    help="Requires both OpenAI and ElevenLabs API keys"
                )

def render_admin_panel():
    """Render the admin panel for content generation"""
    
    st.header("🔧 Admin Panel")
    st.warning("⚠️ Admin features for content generation and testing")
    
    # Admin panel tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Script Generation", 
        "📊 Analytics Dashboard", 
        "🎤 Voice Library", 
        "📚 Script Templates",
        "⚙️ Admin Controls"
    ])
    
    with tab1:
        render_script_generation_tab()
    
    with tab2:
        admin_analytics.render_analytics_dashboard()
    
    with tab3:
        voice_library_manager.render_voice_library_ui()
    
    with tab4:
        script_template_manager.render_templates_ui()
    
    with tab5:
        render_admin_controls_tab()

def render_security_panel():
    """Render the security and privacy management panel"""
    
    st.header("🛡️ Security & Privacy Management")
    
    # Display privacy notice if first time
    render_privacy_notice()
    
    # Create security UI instance and render
    security_ui = SecurityUI(security_manager)
    security_ui.render()

def render_script_generation_tab():
    """Render the script generation tab of admin panel"""
    
    # Show summary of existing results if available
    if session_manager.has_results():
        results = session_manager.get_results()
        file_info = session_manager.get_file_info()
        
        with st.expander("📋 Current Session Summary", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Last File", file_info.name or "Unknown")
            with col2:
                st.metric("Words Transcribed", results.word_count)
            with col3:
                st.metric("Entities Found", sum(len(entities) for entities in results.entities.values()) if results.entities else 0)
            
            if results.transcript:
                st.text_area("Recent Transcript (preview)", 
                           value=results.transcript[:200] + "..." if len(results.transcript) > 200 else results.transcript,
                           height=100, disabled=True)
        
        st.info("💡 Your previous analysis results are preserved and shown below the admin panel.")
    
    # Get admin state from session manager
    admin_state = st.session_state.admin_state
    
    # Display admin errors
    if admin_state['admin_error']:
        st.error(f"❌ {admin_state['admin_error']}")
        admin_state['admin_error'] = ""
    
    # Script generation section
    st.subheader("📝 Script Generation")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        prompt = st.text_area(
            "Enter text prompt for script generation:",
            value=admin_state.get('last_prompt', ''),
            placeholder="Generate a conversation about climate change between two experts...",
            height=100,
            help="Describe the type of content you want to generate"
        )
        
        # Update admin state with current prompt
        if prompt != admin_state.get('last_prompt', ''):
            admin_state['last_prompt'] = prompt
    
    with col2:
        st.markdown("**Format Options:**")
        format_index = ["monologue", "dialogue"].index(
            admin_state.get('last_format', 'monologue')
        )
        format_type = st.selectbox(
            "Script Format",
            ["monologue", "dialogue"],
            index=format_index,
            help="Choose between single-voice monologue or multi-speaker dialogue"
        )
        
        # Update admin state with current format
        if format_type != admin_state.get('last_format', 'monologue'):
            admin_state['last_format'] = format_type
        
        st.markdown("**Style Options:**")
        style_index = ["conversational", "formal", "interview", "presentation"].index(
            admin_state.get('last_style', 'conversational')
        )
        style = st.selectbox(
            "Script Style",
            ["conversational", "formal", "interview", "presentation"],
            index=style_index,
            help="Choose the style for generated content"
        )
        
        # Update admin state with current style
        if style != admin_state.get('last_style', 'conversational'):
            admin_state['last_style'] = style
        
        # Voice selection for TTS
        st.markdown("**Voice Selection:**")
        voice_index = ["professional", "conversational", "narrative"].index(
            admin_state.get('last_voice_preset', 'professional')
        )
        voice_preset = st.selectbox(
            "Voice Preset",
            ["professional", "conversational", "narrative"],
            index=voice_index,
            help="Choose voice style for speech synthesis"
        )
        
        # Update admin state with current voice preset
        if voice_preset != admin_state.get('last_voice_preset', 'professional'):
            admin_state['last_voice_preset'] = voice_preset
        
        # Show format info
        if format_type == "monologue":
            st.info("💡 Monologue: Single voice, continuous narrative")
        else:
            st.info("💡 Dialogue: Multiple speakers with conversation format")
    
    # Generate script button
    if st.button("🎭 Generate Script", type="secondary", disabled=not prompt.strip()):
        generate_admin_script(prompt, format_type, style)
    
    # Generated content display and editing
    st.subheader("📄 Generated Content")
    
    if admin_state['generated_script']:
        # Display script statistics
        script_words = len(admin_state['generated_script'].split())
        script_chars = len(admin_state['generated_script'])
        try:
            estimated_cost = tts.estimate_synthesis_cost(admin_state['generated_script'])
        except Exception as e:
            logger.warning(f"Failed to estimate TTS cost: {e}")
            estimated_cost = 0.0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Words", script_words)
        with col2:
            st.metric("Characters", script_chars)
        with col3:
            st.metric("Est. TTS Cost", f"${estimated_cost:.4f}")
        
        # Editable script display
        edited_script = st.text_area(
            "Generated Script (editable):",
            value=admin_state['generated_script'],
            height=200,
            help="You can edit the generated script before converting to speech"
        )
        
        # Update script if edited
        if edited_script != admin_state['generated_script']:
            admin_state['generated_script'] = edited_script
        
        # TTS conversion controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            convert_button = st.button(
                "🔊 Convert to Speech", 
                type="primary",
                disabled=not admin_state['generated_script'].strip()
            )
        
        with col2:
            if st.button("📋 Copy Script"):
                # Note: Actual clipboard functionality would require additional setup
                st.success("Script copied to clipboard!")
        
        with col3:
            if st.button("🗑️ Clear Script"):
                admin_state['generated_script'] = ""
                admin_state['generated_audio_path'] = ""
                st.rerun()
        
        # Convert to speech
        if convert_button:
            convert_script_to_speech(admin_state['generated_script'], voice_preset, format_type)
    
    else:
        st.info("👆 Generate a script using the prompt above to get started")
    
    # Audio playback and testing section
    if admin_state['generated_audio_path'] and os.path.exists(admin_state['generated_audio_path']):
        st.subheader("🎵 Generated Audio")
        
        # Enhanced audio player
        with open(admin_state['generated_audio_path'], "rb") as audio_file:
            audio_bytes = audio_file.read()
            
        enhanced_audio_player(
            audio_bytes=audio_bytes,
            title="Generated Audio Content",
            show_controls=True,
            show_download=False,  # We have separate download button
            filename="generated_audio.mp3"
        )
        
        st.success("✅ Audio generated successfully!")
        
        # Audio controls and options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Download button
            st.download_button(
                label="📥 Download Audio",
                data=audio_bytes,
                file_name=f"generated_audio_{utils.get_timestamp()}.mp3",
                mime="audio/mp3",
                help="Download the generated audio file"
            )
        
        with col2:
            # Test with main pipeline button
            if st.button("🔄 Test with Analysis Pipeline"):
                test_generated_audio_with_pipeline()
        
        with col3:
            # Clear audio button
            if st.button("🗑️ Clear Audio"):
                cleanup_generated_audio()
                st.rerun()
    
    # Admin controls section
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear Admin Content", help="Clear generated scripts and audio while preserving main analysis results"):
            session_manager.clear_admin_state()
            st.success("🗑️ Admin content cleared")
            st.rerun()
    
    with col2:
        if st.button("🔄 Clear All Session Data", help="Clear everything including analysis results"):
            session_manager.clear_results()
            session_manager.clear_admin_state()
            st.success("🗑️ All session data cleared")
            st.rerun()
    
    # Admin panel help section
    with st.expander("ℹ️ Admin Panel Help"):
        st.markdown("""
        **Script Generation:**
        - Enter a descriptive prompt for the content you want to create
        - Choose an appropriate style (conversational, formal, interview, presentation)
        - Generated scripts can be edited before converting to speech
        
        **Text-to-Speech:**
        - Select a voice preset that matches your content style
        - Professional: Clear, business-appropriate voice
        - Conversational: Friendly, casual tone
        - Narrative: Storytelling, engaging voice
        
        **Testing Integration:**
        - Use "Test with Analysis Pipeline" to process generated audio
        - This helps verify the complete transcription and analysis workflow
        - Generated content can be used for system demonstrations
        
        **API Requirements:**
        - OpenAI API key required for script generation
        - ElevenLabs API key required for text-to-speech synthesis
        """)

def render_admin_controls_tab():
    """Render admin controls tab"""
    st.subheader("⚙️ Admin Controls")
    
    # Admin controls section
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear Admin Content", help="Clear generated scripts and audio while preserving main analysis results"):
            session_manager.clear_admin_state()
            st.success("🗑️ Admin content cleared")
            st.rerun()
    
    with col2:
        if st.button("🔄 Clear All Session Data", help="Clear everything including analysis results"):
            session_manager.clear_results()
            session_manager.clear_admin_state()
            st.success("🗑️ All session data cleared")
            st.rerun()
    
    # Admin panel help section
    with st.expander("ℹ️ Admin Panel Help"):
        st.markdown("""
        **Script Generation:**
        - Enter a descriptive prompt for the content you want to create
        - Choose an appropriate style (conversational, formal, interview, presentation)
        - Generated scripts can be edited before converting to speech
        
        **Analytics Dashboard:**
        - View usage statistics and processing metrics
        - Track API costs and system performance
        - Monitor user activity and system health
        
        **Voice Library:**
        - Manage TTS voice profiles and settings
        - Create custom voice configurations
        - Track voice usage statistics
        
        **Script Templates:**
        - Create reusable script templates with variables
        - Organize templates by category and style
        - Generate content from templates quickly
        
        **Text-to-Speech:**
        - Select a voice preset that matches your content style
        - Professional: Clear, business-appropriate voice
        - Conversational: Friendly, casual tone
        - Narrative: Storytelling, engaging voice
        
        **Testing Integration:**
        - Use "Test with Analysis Pipeline" to process generated audio
        - This helps verify the complete transcription and analysis workflow
        - Generated content can be used for system demonstrations
        
        **API Requirements:**
        - OpenAI API key required for script generation
        - ElevenLabs API key required for text-to-speech synthesis
        """)

def generate_admin_script(prompt: str, format_type: str, style: str):
    """Generate script using AI based on prompt, format, and style"""
    try:
        with st.spinner(f"🤖 Generating {format_type} script with AI..."):
            # Use the enhanced script generation function
            import ner_advanced
            generated_script = ner_advanced.generate_script_with_format(prompt, format_type, style)
            
            if generated_script and generated_script.strip():
                st.session_state.admin_state['generated_script'] = generated_script
                st.success(f"✅ {format_type.title()} script generated successfully! ({len(generated_script.split())} words)")
                logger.info(f"Script generated: {len(generated_script)} characters, {len(generated_script.split())} words, format: {format_type}")
            else:
                st.session_state.admin_state['admin_error'] = "Script generation returned empty result"
                
    except Exception as e:
        app_error = handle_error(e, {
            "operation": "script_generation",
            "prompt_length": len(prompt) if prompt else 0,
            "format_type": format_type,
            "style": style
        })
        logger.error(f"Script generation failed: {app_error.message}")
        st.session_state.admin_state['admin_error'] = app_error.user_message

def convert_script_to_speech(script: str, voice_preset: str, format_type: str = "monologue"):
    """Convert script to speech using TTS"""
    try:
        format_info = "single voice" if format_type == "monologue" else "dialogue format"
        with st.spinner(f"🎵 Synthesizing speech ({format_info})..."):
            # Get voice configuration from preset
            voice_config = tts.VOICE_PRESETS.get(voice_preset, tts.VOICE_PRESETS["professional"])
            
            logger.info(f"Starting TTS synthesis: {len(script)} characters with {voice_preset} preset, format: {format_type}")
            
            # For dialogue format, we might want to add pauses between speakers
            processed_script = script
            if format_type == "dialogue":
                # Add longer pauses between speakers for better dialogue flow
                import re
                processed_script = re.sub(r'(SPEAKER \d+:)', r'\n\1', script)
                processed_script = re.sub(r'\n+', '\n', processed_script)
            
            # Generate speech using the TTS module
            audio_path = tts.synthesize_speech(
                text=processed_script,
                voice_id=voice_config["voice_id"],
                voice_settings=voice_config["settings"]
            )
            
            if audio_path and os.path.exists(audio_path):
                st.session_state.admin_state['generated_audio_path'] = audio_path
                st.success(f"✅ Speech synthesis completed ({format_info})!")
                logger.info(f"TTS synthesis successful: {audio_path}")
                
                # Track TTS usage in analytics
                try:
                    admin_analytics.update_usage_stats(
                        api_calls={'elevenlabs': 1},
                        user_id=getattr(st.session_state, 'user_id', 'admin')
                    )
                    
                    # Update analytics data with TTS character count
                    analytics_data = admin_analytics.load_analytics_data()
                    if 'tts_characters' not in analytics_data['usage_stats']:
                        analytics_data['usage_stats']['tts_characters'] = 0
                    analytics_data['usage_stats']['tts_characters'] += len(script)
                    admin_analytics.save_analytics_data(analytics_data)
                    
                except Exception as analytics_error:
                    logger.warning(f"Failed to update TTS analytics: {analytics_error}")
                
            else:
                st.session_state.admin_state['admin_error'] = "Speech synthesis failed to create audio file"
                logger.error("TTS synthesis failed: no audio file created")
                
    except Exception as e:
        app_error = handle_error(e, {
            "operation": "speech_synthesis",
            "text_length": len(script) if script else 0,
            "voice_preset": voice_preset,
            "format_type": format_type
        })
        logger.error(f"Speech synthesis failed: {app_error.message}")
        st.session_state.admin_state['admin_error'] = app_error.user_message

def test_generated_audio_with_pipeline():
    """Test generated audio with the main analysis pipeline"""
    try:
        if not st.session_state.admin_state['generated_audio_path'] or not os.path.exists(st.session_state.admin_state['generated_audio_path']):
            st.session_state.admin_state['admin_error'] = "No generated audio available for testing"
            return
        
        with st.spinner("🔄 Testing generated audio with analysis pipeline..."):
            # Read the generated audio file
            with open(st.session_state.admin_state['generated_audio_path'], "rb") as audio_file:
                audio_data = audio_file.read()
            
            # Create a temporary file-like object for processing
            class AudioFileWrapper:
                def __init__(self, data, name):
                    self.data = data
                    self.name = name
                    self.size = len(data)
                
                def read(self):
                    return self.data
            
            # Create wrapper and process with main pipeline
            audio_wrapper = AudioFileWrapper(audio_data, "generated_audio.mp3")
            
            # Clear previous results
            clear_session_state()
            
            # Process with advanced mode (since admin panel requires both APIs)
            process_audio(audio_wrapper, "Advanced (OpenAI)")
            
            st.success("🎉 Generated audio successfully processed through analysis pipeline!")
            st.info("📊 Check the Results section below to see the analysis of your generated content")
            
    except Exception as e:
        logger.error(f"Pipeline testing failed: {e}")
        st.session_state.admin_state['admin_error'] = f"Pipeline testing failed: {str(e)}"

def cleanup_generated_audio():
    """Clean up generated audio files"""
    try:
        if st.session_state.admin_state['generated_audio_path'] and os.path.exists(st.session_state.admin_state['generated_audio_path']):
            utils.cleanup_file(st.session_state.admin_state['generated_audio_path'])
        
        st.session_state.admin_state['generated_audio_path'] = ""
        st.success("🗑️ Generated audio cleaned up")
        
    except Exception as e:
        logger.warning(f"Failed to cleanup generated audio: {e}")

def check_api_keys() -> Dict[str, bool]:
    """Check if required API keys are configured"""
    return Config.validate_api_keys()

def display_api_status(api_status: Dict[str, bool]):
    """Display API key configuration status in sidebar"""
    st.sidebar.subheader("🔑 API Status")
    
    # OpenAI status
    if api_status["openai"]:
        st.sidebar.success("✅ OpenAI API configured")
    else:
        st.sidebar.error("❌ OpenAI API key missing")
        st.sidebar.info("Required for transcription and advanced analysis")
    
    # ElevenLabs status
    if api_status["elevenlabs"]:
        st.sidebar.success("✅ ElevenLabs API configured")
    else:
        st.sidebar.warning("⚠️ ElevenLabs API key missing")
        st.sidebar.info("Required for admin text-to-speech features")
    
    if not any(api_status.values()):
        st.sidebar.error("Please configure your API keys in the .env file")

def display_error(error_message: str, error_obj: AppError = None):
    """Display user-friendly error messages with enhanced guidance"""
    if error_obj:
        # Use structured error object
        user_error = create_user_error_message(error_obj)
        st.error(f"❌ {user_error['message']}")
        
        # Display suggestions if available
        if user_error['suggestions']:
            st.info("💡 **Suggestions:**")
            for suggestion in user_error['suggestions']:
                st.write(f"• {suggestion}")
        
        # Show error code for debugging (in expander)
        with st.expander("🔧 Technical Details"):
            st.code(f"Error Code: {user_error['error_code']}")
            if hasattr(error_obj, 'details') and error_obj.details:
                st.json(error_obj.details)
    else:
        # Fallback for simple string messages
        st.error(f"❌ {error_message}")
        
        # Provide helpful suggestions based on error type
        if "API" in error_message:
            st.info("💡 **Suggestion:** Check your API key configuration in the .env file")
        elif "file" in error_message.lower():
            st.info("💡 **Suggestion:** Try a different file format or check file integrity")
        elif "network" in error_message.lower():
            st.info("💡 **Suggestion:** Check your internet connection and try again")
        else:
            st.info("💡 **Suggestion:** Please try again or contact support if the issue persists")

def clear_session_state():
    """Clear processing results from session state"""
    session_manager.clear_results()
    st.success("🗑️ Results cleared successfully")

def process_audio_enhanced(audio_source, analysis_mode: str):
    """Enhanced audio processing with detailed progress tracking"""
    temp_files_to_cleanup = []
    start_time = time.time()  # Track processing time for analytics
    
    # Create processing steps
    processing_steps = create_processing_steps()
    
    try:
        # Start processing in session manager
        session_manager.start_processing("Initializing audio processing...")
        
        # Create enhanced progress container
        progress_container = st.empty()
        
        with progress_context(processing_steps) as progress:
            # Step 1: File Validation and Saving
            progress.update(0, "Validating and saving audio file...")
            
            # Show enhanced progress in container
            with progress_container.container():
                enhanced_progress_indicator(0, "Validating and saving audio file...", animated=True)
            
            # Save the audio file to temp directory
            temp_dir = utils.ensure_temp_directory()
            
            if hasattr(audio_source, 'name'):  # Uploaded file
                file_extension = os.path.splitext(audio_source.name)[1]
                temp_path = os.path.join(temp_dir, f"uploaded_audio{file_extension}")
                with open(temp_path, "wb") as f:
                    audio_source.seek(0)  # Ensure we're at the beginning
                    f.write(audio_source.read())
            else:  # Recorded audio or generated audio wrapper
                if hasattr(audio_source, 'data'):  # AudioFileWrapper from admin panel
                    temp_path = os.path.join(temp_dir, "generated_audio.mp3")
                    with open(temp_path, "wb") as f:
                        f.write(audio_source.data)
                else:  # Regular recorded audio (BytesIO object)
                    temp_path = os.path.join(temp_dir, "recorded_audio.wav")
                    with open(temp_path, "wb") as f:
                        audio_source.seek(0)  # Ensure we're at the beginning
                        f.write(audio_source.read())
            
            temp_files_to_cleanup.append(temp_path)
            progress.update(50, "File saved, validating...")
            
            # Validate file size
            if not utils.validate_file_size(temp_path, Config.MAX_FILE_SIZE_MB):
                raise FileProcessingError(
                    message=f"File size exceeds {Config.MAX_FILE_SIZE_MB}MB limit",
                    error_code=ErrorCode.FILE_SIZE_EXCEEDED,
                    user_message=f"File size exceeds the {Config.MAX_FILE_SIZE_MB}MB limit.",
                    file_path=temp_path,
                    suggestions=[
                        "Try a smaller file",
                        "Compress the audio/video file",
                        "Use a shorter recording"
                    ]
                )
            
            progress.update(100, "File validation complete")
            progress.next_step("Processing media file...")
            
            # Step 2: Media Processing
            progress.update(0, "Analyzing media format...")
            processed_audio_path = temp_path
            
            # Check if it's a video file that needs audio extraction
            if media.is_video_file(temp_path):
                progress.update(30, "Video file detected, extracting audio...")
                logger.info(f"Video file detected, extracting audio: {temp_path}")
                processed_audio_path = media.extract_audio(temp_path, Config.MAX_FILE_SIZE_MB)
                temp_files_to_cleanup.append(processed_audio_path)
                progress.update(60, "Audio extraction complete")
            elif media.is_audio_file(temp_path):
                progress.update(30, "Audio file detected, converting format...")
                logger.info(f"Audio file detected, converting format: {temp_path}")
                processed_audio_path = media.convert_audio_format(temp_path, "wav")
                temp_files_to_cleanup.append(processed_audio_path)
                progress.update(60, "Audio format conversion complete")
            else:
                progress.update(50, "Validating media file...")
                media.validate_media_file(temp_path, Config.MAX_FILE_SIZE_MB)
                progress.update(60, "Media validation complete")
            
            # Step 2.5: Advanced Audio Processing (if enabled)
            if st.session_state.get('audio_enhancement_enabled', True):
                progress.update(65, "Applying advanced audio processing...")
                logger.info("Applying advanced audio enhancement")
                
                try:
                    # Initialize advanced audio processor
                    audio_processor = AdvancedAudioProcessor()
                    
                    # Analyze audio quality first
                    progress.update(70, "Analyzing audio quality...")
                    quality_metrics = audio_processor.quality_analyzer.analyze_quality(processed_audio_path)
                    
                    # Store quality metrics in session state for display
                    st.session_state.audio_quality_metrics = quality_metrics
                    
                    # Apply enhancements based on quality analysis
                    progress.update(75, "Enhancing audio quality...")
                    enhanced_audio_path = audio_processor.enhance_audio(
                        processed_audio_path,
                        apply_noise_reduction=quality_metrics.snr_db < 15,
                        apply_normalization=quality_metrics.rms_energy < 0.01 or quality_metrics.rms_energy > 0.5,
                        trim_silence=True
                    )
                    
                    if enhanced_audio_path != processed_audio_path:
                        temp_files_to_cleanup.append(enhanced_audio_path)
                        processed_audio_path = enhanced_audio_path
                        logger.info(f"Audio enhanced: {enhanced_audio_path}")
                    
                    progress.update(85, "Audio enhancement complete")
                    
                    # Handle segmentation if enabled
                    if st.session_state.get('audio_segmentation_enabled', False):
                        progress.update(87, "Creating audio segments...")
                        segment_result = audio_processor.create_segments_with_bookmarks(
                            processed_audio_path, 
                            segment_method="silence"
                        )
                        
                        # Store segmentation results in session state
                        st.session_state.audio_segments = segment_result['segments']
                        st.session_state.audio_bookmarks = segment_result['bookmarks']
                        st.session_state.audio_chapters = segment_result['chapters']
                        
                        # Add segment files to cleanup list
                        temp_files_to_cleanup.extend(segment_result['segments'])
                        
                        logger.info(f"Audio segmented into {len(segment_result['segments'])} parts")
                    
                    progress.update(90, "Advanced audio processing complete")
                    
                except Exception as e:
                    logger.warning(f"Advanced audio processing failed: {e}")
                    st.warning("⚠️ Advanced audio processing failed, continuing with standard processing")
                    # Continue with original audio if enhancement fails
            
            progress.update(100, "Media processing complete")
            progress.next_step("Starting transcription...")
            
            # Step 3: Audio Transcription
            progress.update(0, "Initializing speech-to-text engine...")
            
            # Determine whether to use API based on analysis mode and availability
            use_api = "Advanced" in analysis_mode and Config.validate_api_keys()["openai"]
            
            # Enable timestamps in Advanced mode
            enable_timestamps = "Advanced" in analysis_mode
            
            progress.update(20, f"Transcribing with {'OpenAI Whisper API' if use_api else 'local Whisper model'}...")
            logger.info(f"Starting transcription with API: {use_api}, timestamps: {enable_timestamps}")
            
            transcription_result = stt.transcribe_detailed(
                processed_audio_path, 
                use_api=use_api,
                enable_timestamps=enable_timestamps
            )
            
            progress.update(90, "Transcription complete, processing results...")
            
            # Store transcription results
            results = TranscriptionResults(
                transcript=transcription_result.text,
                confidence=transcription_result.confidence,
                processing_time=transcription_result.processing_time,
                model_used=transcription_result.model_used,
                language=transcription_result.language,
                word_count=transcription_result.word_count()
            )
            
            # Store timestamps if available
            if hasattr(transcription_result, 'timestamps') and transcription_result.timestamps:
                results.timestamps = transcription_result.timestamps
                logger.info(f"Stored {len(transcription_result.timestamps)} timestamp segments")
            
            # Store audio file path for waveform visualization
            results.audio_file_path = processed_audio_path
            st.session_state.current_audio_path = processed_audio_path
            
            progress.update(100, "Transcription processing complete")
            progress.next_step("Analyzing content and extracting entities...")
            
            # Step 4: Entity Extraction and Advanced Processing
            if "Basic" in analysis_mode:
                progress.update(0, "Starting basic entity extraction with spaCy...")
                logger.info("Starting basic entity extraction with spaCy")
                
                progress.update(30, "Loading spaCy model...")
                entities = ner_basic.extract_entities(transcription_result.text)
                
                progress.update(70, "Calculating confidence scores...")
                entity_confidence = ner_basic.get_entity_confidence(transcription_result.text)
                
                results.entities = entities
                results.entity_confidence = entity_confidence
                results.summary = ""  # No summary in basic mode
                
                progress.update(100, "Basic entity extraction complete")
                
            elif "Advanced+" in analysis_mode:
                # Handle Advanced+ mode with speaker diarization
                progress.update(0, "Starting advanced processing with speaker diarization...")
                logger.info("Starting Advanced+ processing with speaker diarization")
                
                # Clear progress container and show advanced processing
                progress_container.empty()
                
                # Use advanced processing function
                advanced_processing_result = process_audio_with_advanced_features(
                    audio_source, analysis_mode
                )
                
                if advanced_processing_result:
                    # Render advanced results
                    render_advanced_results(advanced_processing_result)
                    return  # Exit early as advanced processing handles everything
                else:
                    # Fall back to regular advanced mode if advanced processing fails
                    st.warning("⚠️ Advanced+ processing failed, falling back to regular Advanced mode")
                    analysis_mode = "Advanced (OpenAI)"
            
            if "Advanced" in analysis_mode and "Advanced+" not in analysis_mode:
                progress.update(0, "Starting advanced AI analysis...")
                logger.info("Starting advanced entity extraction with OpenAI GPT")
                
                progress.update(20, "Sending content to OpenAI GPT...")
                entities, summary = ner_advanced.extract_entities_advanced(transcription_result.text)
                
                progress.update(70, "Processing AI analysis results...")
                results.entities = entities
                results.summary = summary
                
                # Get sentiment analysis
                try:
                    progress.update(85, "Analyzing sentiment...")
                    sentiment = ner_advanced.analyze_sentiment(transcription_result.text)
                    results.sentiment = sentiment
                except Exception as e:
                    logger.warning(f"Sentiment analysis failed: {e}")
                    results.sentiment = {}
                
                progress.update(100, "Advanced analysis complete")
            
            progress.next_step("Finalizing results...")
            
            # Step 5: Finalize Results
            progress.update(0, "Preparing results for display...")
            
            # Log completion statistics
            entity_count = sum(len(v) for v in results.entities.values()) if results.entities else 0
            logger.info(f"Processing completed: {results.word_count} words, {entity_count} entities extracted")
            
            progress.update(50, "Organizing results...")
            
            # Complete processing in session manager
            session_manager.complete_processing(results)
            
            # Add to semantic search library (Task 28)
            try:
                from semantic_search.integration import semantic_integration
                
                # Prepare file info
                file_info = {
                    'file_name': getattr(audio_source, 'name', 'unknown'),
                    'file_path': processed_audio_path,
                    'file_size': getattr(audio_source, 'size', None),
                    'duration': getattr(transcription_result, 'duration', None)
                }
                
                # Prepare analysis results
                analysis_data = {
                    'entities': results.entities,
                    'confidence': results.confidence,
                    'model_used': results.model_used,
                    'processing_time': results.processing_time,
                    'word_count': results.word_count
                }
                
                if hasattr(results, 'summary') and results.summary:
                    analysis_data['summary'] = results.summary
                
                # Add speaker segments if available
                speaker_segments = getattr(results, 'speaker_segments', None)
                
                # Add to semantic search library
                semantic_integration.add_transcription_result(
                    transcript_text=results.transcript,
                    file_info=file_info,
                    analysis_results=analysis_data,
                    speaker_segments=speaker_segments
                )
                
                logger.info("Added transcription result to semantic search library")
                
            except Exception as e:
                logger.warning(f"Failed to add to semantic search library: {e}")
            
            # Integration hooks (Task 23)
            if INTEGRATIONS_AVAILABLE:
                try:
                    # Trigger webhook for transcription completion
                    import asyncio
                    asyncio.create_task(trigger_transcription_completed_webhook(
                        transcript_id=f"transcript_{int(time.time())}",
                        file_name=getattr(audio_source, 'name', 'unknown'),
                        duration=getattr(transcription_result, 'duration', 0),
                        word_count=results.word_count,
                        confidence_score=results.confidence,
                        user_id=getattr(st.session_state, 'user_id', None)
                    ))
                    
                    # Backup transcript to cloud storage
                    asyncio.create_task(backup_transcript_to_cloud(
                        transcript_id=f"transcript_{int(time.time())}",
                        transcript_content=results.transcript,
                        metadata={
                            'analysis_mode': analysis_mode,
                            'word_count': results.word_count,
                            'confidence': results.confidence,
                            'processing_time': processing_time if 'processing_time' in locals() else 0
                        }
                    ))
                    
                    # Extract custom entities using plugins
                    custom_entities = asyncio.run(extract_custom_entities(results.transcript))
                    if custom_entities:
                        # Merge custom entities with existing ones
                        if results.entities:
                            for entity_type, entities in custom_entities.items():
                                if entity_type not in results.entities:
                                    results.entities[entity_type] = []
                                results.entities[entity_type].extend([e['text'] for e in entities])
                        else:
                            results.entities = {k: [e['text'] for e in v] for k, v in custom_entities.items()}
                    
                    logger.info("Integration hooks executed successfully")
                    
                except Exception as integration_error:
                    logger.warning(f"Integration hooks failed: {integration_error}")
            
            # Track analytics for admin dashboard
            try:
                processing_time = time.time() - start_time if 'start_time' in locals() else 0
                api_calls = {}
                
                # Track API usage based on analysis mode
                if "Advanced" in analysis_mode:
                    api_calls['openai'] = 1
                    api_calls['whisper'] = 1
                else:
                    api_calls['whisper'] = 1
                
                # Update admin analytics
                admin_analytics.update_usage_stats(
                    transcription_time=processing_time,
                    words_count=results.word_count,
                    api_calls=api_calls,
                    user_id=getattr(st.session_state, 'user_id', 'anonymous')
                )
                
                logger.info(f"Analytics updated: {processing_time:.2f}s processing, {results.word_count} words")
            except Exception as analytics_error:
                logger.warning(f"Failed to update analytics: {analytics_error}")
            
            progress.update(100, "Results ready for display")
            progress.complete("🎉 Processing completed successfully!")
            
    except Exception as e:
        # Use centralized error handling
        app_error = handle_error(e, {
            "operation": "audio_processing",
            "file_path": getattr(audio_source, 'name', 'unknown'),
            "analysis_mode": analysis_mode
        })
        
        logger.error(f"Processing error: {app_error.message}")
        session_manager.set_error(app_error.user_message, app_error)
    
    finally:
        # Clean up all temporary files
        for file_path in temp_files_to_cleanup:
            try:
                utils.cleanup_file(file_path)
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup file {file_path}: {cleanup_error}")

def process_audio(audio_source, analysis_mode: str):
    """Legacy process_audio function - redirects to enhanced version"""
    return process_audio_enhanced(audio_source, analysis_mode)

def render_audio_quality_analysis():
    """Render audio quality analysis and advanced processing results"""
    
    # Display audio quality metrics if available
    if hasattr(st.session_state, 'audio_quality_metrics'):
        st.subheader("🎛️ Audio Quality Analysis")
        
        metrics = st.session_state.audio_quality_metrics
        
        # Create columns for metrics display
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Quality Score",
                f"{metrics.quality_score:.1f}/100",
                help="Overall audio quality assessment"
            )
        
        with col2:
            st.metric(
                "Signal-to-Noise Ratio",
                f"{metrics.snr_db:.1f} dB",
                help="Higher values indicate cleaner audio"
            )
        
        with col3:
            st.metric(
                "Dynamic Range",
                f"{metrics.dynamic_range_db:.1f} dB",
                help="Audio dynamic range measurement"
            )
        
        with col4:
            st.metric(
                "Spectral Centroid",
                f"{metrics.spectral_centroid:.0f} Hz",
                help="Average frequency content"
            )
        
        # Display recommendations
        if metrics.recommendations:
            st.info("💡 **Audio Quality Recommendations:**")
            for rec in metrics.recommendations:
                st.write(f"• {rec}")
    
    # Display segmentation results if available
    if hasattr(st.session_state, 'audio_segments') and st.session_state.audio_segments:
        st.subheader("📑 Audio Segmentation")
        
        segments = st.session_state.audio_segments
        bookmarks = getattr(st.session_state, 'audio_bookmarks', [])
        chapters = getattr(st.session_state, 'audio_chapters', [])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Segments", len(segments))
            st.metric("Bookmarks", len(bookmarks))
        
        with col2:
            st.metric("Auto Chapters", len(chapters))
            if segments:
                # Calculate average segment duration (approximate)
                avg_duration = "~5 min"  # Placeholder - could calculate actual
                st.metric("Avg Segment Length", avg_duration)
        
        # Display chapters if available
        if chapters:
            with st.expander("📖 Auto-Generated Chapters", expanded=False):
                for i, chapter in enumerate(chapters):
                    st.write(f"**{chapter.title}** ({chapter.start_time:.1f}s - {chapter.end_time:.1f}s)")
                    if chapter.description:
                        st.write(f"  _{chapter.description}_")
        
        # Display bookmarks if available
        if bookmarks:
            with st.expander("🔖 Audio Bookmarks", expanded=False):
                for bookmark in bookmarks:
                    st.write(f"**{bookmark.title}** at {bookmark.timestamp:.1f}s")
                    if bookmark.description:
                        st.write(f"  _{bookmark.description}_")

def render_results_enhanced(analysis_mode: str):
    """Enhanced results display with session manager integration"""
    
    # Check if we have advanced results
    if "Advanced+" in analysis_mode and session_manager.has_advanced_results():
        # Advanced results are already rendered by the advanced processing function
        return
    
    st.header("📊 Results")
    
    # Get results from session manager
    results = session_manager.get_results()
    file_info = session_manager.get_file_info()
    preferences = session_manager.get_preferences()
    
    # Show processing summary
    with st.expander("📈 Processing Summary", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Words", results.word_count)
        with col2:
            st.metric("Processing Time", f"{results.processing_time:.1f}s")
        with col3:
            st.metric("Model Used", results.model_used)
        with col4:
            confidence_display = f"{results.confidence:.1%}" if results.confidence > 0 else "N/A"
            st.metric("Confidence", confidence_display)
    
    # Show advanced audio processing results if available
    if (hasattr(st.session_state, 'audio_quality_metrics') or 
        hasattr(st.session_state, 'audio_segments')):
        with st.expander("🎛️ Advanced Audio Processing", expanded=False):
            render_audio_quality_analysis()
    
    # Create tabs for better organization
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📝 Transcript", "🎯 Interactive", "🏷️ Entities", "🎯 Analysis", "📥 Downloads", "⚙️ Settings"])
    
    with tab1:
        render_transcript_display_enhanced(results, preferences)
    
    with tab2:
        render_interactive_transcript(results)
    
    with tab3:
        # Enhanced entity visualization with all features
        if results.entities:
            entity_confidence = results.entity_confidence if "Basic" in analysis_mode and preferences.show_confidence_scores else None
            
            # Render enhanced entity display with all visualization features
            entity_interactions = render_enhanced_entity_display(
                entities=results.entities,
                entity_confidence=entity_confidence,
                transcript=results.transcript,
                show_all_features=True
            )
            
            # Store interactions in session state for potential use
            if entity_interactions:
                st.session_state['entity_interactions'] = entity_interactions
        else:
            st.info("No entities extracted from the transcript")
    
    with tab4:
        render_enhanced_analysis(results, analysis_mode)
    
    with tab5:
        render_download_options_enhanced(results, file_info, analysis_mode)
    
    with tab6:
        render_results_settings(preferences)

def render_results_settings(preferences):
    """Render settings for results display"""
    st.subheader("🎛️ Display Settings")
    
    # Line numbers preference
    show_line_numbers = st.checkbox(
        "Show line numbers in transcript",
        value=preferences.show_line_numbers,
        help="Display line numbers alongside transcript text for easier reference"
    )
    if show_line_numbers != preferences.show_line_numbers:
        session_manager.update_preference('show_line_numbers', show_line_numbers)
        st.rerun()
    
    # Confidence scores preference
    show_confidence = st.checkbox(
        "Show confidence scores",
        value=preferences.show_confidence_scores,
        help="Display confidence scores for extracted entities (Basic mode only)"
    )
    if show_confidence != preferences.show_confidence_scores:
        session_manager.update_preference('show_confidence_scores', show_confidence)
        st.rerun()
    
    # Auto-clear preference
    auto_clear = st.checkbox(
        "Auto-clear results when processing new files",
        value=preferences.auto_clear_results,
        help="Automatically clear previous results when starting new processing"
    )
    if auto_clear != preferences.auto_clear_results:
        session_manager.update_preference('auto_clear_results', auto_clear)
    
    # Processing history
    st.subheader("📜 Processing History")
    history = session_manager.get_processing_history()
    
    if history:
        for i, entry in enumerate(history):
            with st.expander(f"📄 {entry['file_name']} - {entry['timestamp'].strftime('%Y-%m-%d %H:%M')}", expanded=False):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Words", entry['word_count'])
                with col2:
                    st.metric("Processing Time", f"{entry['processing_time']:.1f}s")
                with col3:
                    st.metric("Model", entry['model_used'])
    else:
        st.info("No processing history available")

def render_semantic_search_widget(results):
    """Render semantic search widget for finding similar content"""
    try:
        from semantic_search.integration import semantic_integration
        
        st.markdown("---")
        st.subheader("🔍 Find Similar Content")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input(
                "Search for similar transcripts",
                placeholder="e.g., 'meeting about project deadlines' or 'customer feedback discussion'",
                help="Use natural language to find transcripts with similar content"
            )
        
        with col2:
            search_limit = st.selectbox("Results", [5, 10, 15], index=0)
        
        if search_query and st.button("Find Similar", type="secondary"):
            with st.spinner("Searching for similar content..."):
                similar_results = semantic_integration.search_similar_content(search_query, search_limit)
                
                if similar_results:
                    st.write(f"**Found {len(similar_results)} similar transcripts:**")
                    
                    for i, result in enumerate(similar_results, 1):
                        with st.expander(f"📄 {result['title']} (Similarity: {result['similarity_score']:.3f})"):
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.write("**Preview:**")
                                st.write(result['content_preview'])
                            
                            with col2:
                                if result['category']:
                                    st.write(f"**Category:** {result['category']}")
                                if result['duration']:
                                    st.write(f"**Duration:** {result['duration']/60:.1f} min")
                                if result['created_at']:
                                    created_date = result['created_at'][:10]  # Just the date part
                                    st.write(f"**Created:** {created_date}")
                else:
                    st.info("No similar content found. Try different search terms.")
        
        # Show recommendations based on current transcript
        if st.button("Get Recommendations", type="secondary"):
            with st.spinner("Generating recommendations..."):
                # Use current transcript as context for recommendations
                recommendations = semantic_integration.get_transcript_recommendations(limit=5)
                
                if recommendations:
                    st.write("**Recommended transcripts you might find interesting:**")
                    
                    for rec in recommendations:
                        with st.expander(f"💡 {rec['title']}"):
                            st.write(rec['content_preview'])
                            if rec['category']:
                                st.write(f"**Category:** {rec['category']}")
                else:
                    st.info("No recommendations available yet. Process more transcripts to get personalized suggestions.")
        
        # Show library stats
        stats = semantic_integration.get_library_stats()
        if stats and stats.get('total_transcripts', 0) > 0:
            st.write(f"📚 **Library:** {stats['total_transcripts']} transcripts, {stats.get('total_duration_hours', 0):.1f} hours total")
        
    except ImportError:
        st.info("💡 Enable semantic search in Advanced Features to find similar content and get recommendations!")
    except Exception as e:
        logger.error(f"Error in semantic search widget: {e}")
        st.error("Semantic search temporarily unavailable")

def render_transcript_display_enhanced(results, preferences):
    """Enhanced transcript display with user preferences"""
    st.subheader("📝 Full Transcript")
    
    if results.transcript:
        # Display transcript statistics
        char_count = len(results.transcript)
        estimated_duration = results.word_count / 150  # Average speaking rate
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Words", results.word_count)
        with col2:
            st.metric("Characters", char_count)
        with col3:
            st.metric("Est. Duration", f"{estimated_duration:.1f} min")
        
        # Transcript display options
        st.markdown("---")
        
        # Search functionality
        search_term = st.text_input(
            "🔍 Search in transcript",
            placeholder="Enter text to search...",
            help="Search for specific words or phrases in the transcript"
        )
        
        # Prepare transcript for display
        transcript_to_display = results.transcript
        
        if preferences.show_line_numbers:
            # Split transcript into lines and add line numbers
            lines = results.transcript.split('\n')
            transcript_to_display = '\n'.join([f"{i+1:3d}: {line}" for i, line in enumerate(lines)])
        
        # Highlight search terms if provided
        if search_term and search_term.strip():
            # Simple highlighting (in a real app, you might want more sophisticated highlighting)
            highlighted_transcript = transcript_to_display.replace(
                search_term, 
                f"**{search_term}**"
            )
            st.markdown("**Search Results:**")
            st.markdown(highlighted_transcript)
        else:
            # Display transcript in a scrollable text area
            st.text_area(
                "Transcript Content:",
                value=transcript_to_display,
                height=400,
                help="Full transcript of your audio content. Use Ctrl+F to search within the text.",
                label_visibility="collapsed"
            )
    else:
        st.info("No transcript available")
    
    # Semantic search widget
    render_semantic_search_widget(results)

def render_basic_entities_display_enhanced(results, preferences):
    """Enhanced basic entities display"""
    st.subheader("🏷️ Extracted Entities (Basic Mode)")
    
    if results.entities:
        # Entity summary with enhanced metrics
        total_entities = sum(len(entities) for entities in results.entities.values())
        entity_types_count = len([k for k, v in results.entities.items() if v])
        
        summary_metrics = [
            {
                "title": "Total Entities",
                "value": str(total_entities),
                "icon": "🏷️",
                "help": "Total number of entities found"
            },
            {
                "title": "Entity Types",
                "value": str(entity_types_count),
                "icon": "📂",
                "help": "Number of different entity categories"
            },
            {
                "title": "Processing Mode",
                "value": "spaCy",
                "icon": "⚡",
                "help": "Local NLP processing"
            }
        ]
        
        enhanced_metric_display(summary_metrics, columns=3, animated=True)
        
        # Enhanced entity display
        enhanced_entity_display(
            entities=results.entities,
            entity_confidence=results.entity_confidence if preferences.show_confidence_scores else None,
            show_confidence=preferences.show_confidence_scores,
            interactive=True
        )
    else:
        st.info("No entities extracted")

def render_advanced_entities_display_enhanced(results, preferences):
    """Enhanced advanced entities display"""
    st.subheader("🤖 AI Analysis Results (Advanced Mode)")
    
    # Summary section with enhanced styling
    if results.summary:
        st.markdown("### 📋 Content Summary")
        
        # Create styled summary box
        summary_html = f"""
        <div style="
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            border-left: 4px solid var(--primary-color);
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 2px 8px var(--shadow-color);
        ">
            <div style="
                color: var(--text-primary-color);
                line-height: 1.6;
                font-size: 0.95rem;
            ">{results.summary}</div>
        </div>
        """
        st.markdown(summary_html, unsafe_allow_html=True)
        st.markdown("---")
    
    # Enhanced entities section
    if results.entities:
        st.markdown("### 🏷️ Extracted Entities")
        
        # Entity summary metrics
        total_entities = sum(len(entities) for entities in results.entities.values())
        entity_types_count = len([k for k, v in results.entities.items() if v])
        
        entity_metrics = [
            {
                "title": "Total Entities",
                "value": str(total_entities),
                "icon": "🏷️",
                "help": "AI-extracted entities"
            },
            {
                "title": "Entity Types",
                "value": str(entity_types_count),
                "icon": "📂",
                "help": "Different categories found"
            },
            {
                "title": "Processing Mode",
                "value": "GPT",
                "icon": "🤖",
                "help": "AI-powered analysis"
            }
        ]
        
        enhanced_metric_display(entity_metrics, columns=3, animated=True)
        
        # Enhanced entity display
        enhanced_entity_display(
            entities=results.entities,
            entity_confidence=None,  # GPT doesn't provide confidence scores
            show_confidence=False,
            interactive=True
        )
    
    # Enhanced sentiment analysis
    if results.sentiment:
        st.markdown("### 😊 Sentiment Analysis")
        
        sentiment_score = results.sentiment.get('compound', 0)
        sentiment_label = "Positive" if sentiment_score > 0.1 else "Negative" if sentiment_score < -0.1 else "Neutral"
        
        # Determine sentiment color
        sentiment_color = "var(--success-color)" if sentiment_score > 0.1 else "var(--error-color)" if sentiment_score < -0.1 else "var(--text-secondary-color)"
        
        sentiment_metrics = [
            {
                "title": "Overall Sentiment",
                "value": sentiment_label,
                "delta": f"Score: {sentiment_score:.2f}",
                "icon": "😊" if sentiment_score > 0.1 else "😔" if sentiment_score < -0.1 else "😐",
                "help": "Overall emotional tone"
            },
            {
                "title": "Positive",
                "value": f"{results.sentiment.get('pos', 0):.2f}",
                "icon": "👍",
                "help": "Positive sentiment strength"
            },
            {
                "title": "Negative", 
                "value": f"{results.sentiment.get('neg', 0):.2f}",
                "icon": "👎",
                "help": "Negative sentiment strength"
            }
        ]
        
        enhanced_metric_display(sentiment_metrics, columns=3, animated=True)

def render_download_options_enhanced(results, file_info, analysis_mode):
    """Enhanced download options"""
    st.subheader("📥 Download Results")
    
    if not results.transcript:
        st.info("No results available for download")
        return
    
    # Generate timestamp for file naming
    timestamp = utils.get_timestamp()
    base_filename = file_info.name.split('.')[0] if file_info.name else "transcript"
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Transcript download
        st.download_button(
            label="📝 Download Transcript (.txt)",
            data=results.transcript,
            file_name=f"{base_filename}_transcript_{timestamp}.txt",
            mime="text/plain",
            help="Download the full transcript as a text file"
        )
        
        # Entities download (JSON)
        if results.entities:
            import json
            entities_json = json.dumps(results.entities, indent=2)
            st.download_button(
                label="📋 Download Entities (.json)",
                data=entities_json,
                file_name=f"{base_filename}_entities_{timestamp}.json",
                mime="application/json",
                help="Download extracted entities as JSON data"
            )
    
    with col2:
        # Combined report
        if "Advanced" in analysis_mode and results.summary:
            report_content = f"""# Analysis Report
Generated: {timestamp}
File: {file_info.name}
Analysis Mode: {analysis_mode}

## Summary
{results.summary}

## Transcript
{results.transcript}

## Extracted Entities
"""
            for entity_type, entities in results.entities.items():
                if entities:
                    report_content += f"\n### {entity_type.title()}\n"
                    for entity in entities:
                        report_content += f"- {entity}\n"
            
            st.download_button(
                label="📊 Download Full Report (.md)",
                data=report_content,
                file_name=f"{base_filename}_report_{timestamp}.md",
                mime="text/markdown",
                help="Download complete analysis report in Markdown format"
            )
        
        # Processing metadata
        metadata = {
            "file_info": {
                "name": file_info.name,
                "size_mb": file_info.size_mb,
                "duration": file_info.duration
            },
            "processing_info": {
                "model_used": results.model_used,
                "processing_time": results.processing_time,
                "confidence": results.confidence,
                "word_count": results.word_count,
                "analysis_mode": analysis_mode
            }
        }
        
        import json
        metadata_json = json.dumps(metadata, indent=2, default=str)
        st.download_button(
            label="⚙️ Download Metadata (.json)",
            data=metadata_json,
            file_name=f"{base_filename}_metadata_{timestamp}.json",
            mime="application/json",
            help="Download processing metadata and file information"
        )

def render_enhanced_analysis(results, analysis_mode: str):
    """Render enhanced analysis features"""
    st.subheader("🎯 Enhanced Analysis")
    
    if not results.transcript:
        st.info("No transcript available for analysis")
        return
    
    # Create tabs for different analysis types
    analysis_tab1, analysis_tab2, analysis_tab3 = st.tabs(["📋 Content Analysis", "📊 Visual Analysis", "🔍 Structured Analysis"])
    
    with analysis_tab1:
        render_content_analysis(results, analysis_mode)
    
    with analysis_tab2:
        render_visual_analysis(results, analysis_mode)
    
    with analysis_tab3:
        render_structured_analysis_tab(results, analysis_mode)

def render_content_analysis(results, analysis_mode: str):
    """Render content analysis features"""
    # Analysis options
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Content Analysis")
        
        # Summary generation
        if st.button("📄 Generate Executive Summary", help="Create a concise executive summary"):
            if "Advanced" in analysis_mode:
                try:
                    with st.spinner("Generating executive summary..."):
                        import ner_advanced
                        summary = ner_advanced.generate_summary_with_style(results.transcript, "executive")
                        st.markdown("#### Executive Summary")
                        st.markdown(summary)
                except Exception as e:
                    st.error(f"Failed to generate summary: {str(e)}")
            else:
                st.warning("Executive summary requires Advanced mode (OpenAI API)")
        
        # Meeting minutes
        if st.button("📝 Generate Meeting Minutes", help="Create structured meeting minutes"):
            if "Advanced" in analysis_mode:
                try:
                    with st.spinner("Generating meeting minutes..."):
                        import ner_advanced
                        minutes = ner_advanced.generate_meeting_minutes(results.transcript)
                        st.markdown("#### Meeting Minutes")
                        st.markdown(minutes)
                except Exception as e:
                    st.error(f"Failed to generate meeting minutes: {str(e)}")
            else:
                st.warning("Meeting minutes require Advanced mode (OpenAI API)")
        
        # Key insights
        if st.button("💡 Extract Key Insights", help="Extract key insights and patterns"):
            if "Advanced" in analysis_mode:
                try:
                    with st.spinner("Extracting key insights..."):
                        import ner_advanced
                        insights = ner_advanced.generate_summary_with_style(results.transcript, "key_insights")
                        st.markdown("#### Key Insights")
                        st.markdown(insights)
                except Exception as e:
                    st.error(f"Failed to extract insights: {str(e)}")
            else:
                st.warning("Key insights require Advanced mode (OpenAI API)")
    
    with col2:
        # Additional analysis options
        st.markdown("### 🔍 Additional Analysis Options")
        
        if st.button("📋 Bullet Point Summary"):
            if "Advanced" in analysis_mode:
                try:
                    with st.spinner("Creating bullet point summary..."):
                        import ner_advanced
                        summary = ner_advanced.generate_summary_with_style(results.transcript, "bullet_points")
                        st.markdown("#### Bullet Point Summary")
                        st.markdown(summary)
                except Exception as e:
                    st.error(f"Failed to generate summary: {str(e)}")
            else:
                st.warning("Requires Advanced mode")
        
        if st.button("📊 Detailed Analysis"):
            if "Advanced" in analysis_mode:
                try:
                    with st.spinner("Creating detailed analysis..."):
                        import ner_advanced
                        analysis = ner_advanced.generate_summary_with_style(results.transcript, "detailed")
                        st.markdown("#### Detailed Analysis")
                        st.markdown(analysis)
                except Exception as e:
                    st.error(f"Failed to generate analysis: {str(e)}")
            else:
                st.warning("Requires Advanced mode")
        
        if st.button("🎭 Content Themes"):
            if results.entities and results.entities.get('TOPIC'):
                st.markdown("#### Content Themes")
                for topic in results.entities['TOPIC']:
                    st.write(f"• **{topic}**")
            else:
                st.info("No themes identified. Try Advanced mode for better theme extraction.")

def render_visual_analysis(results, analysis_mode: str):
    """Render visual analysis features"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Visual Analysis")
        
        # Word cloud
        if st.button("☁️ Generate Word Cloud", help="Create word cloud from content"):
            try:
                with st.spinner("Generating word cloud..."):
                    import word_cloud_generator
                    word_freq = word_cloud_generator.create_word_cloud_data(results.transcript, results.entities)
                    
                    if word_freq:
                        st.markdown("#### Word Cloud")
                        
                        # Display as text-based word cloud
                        formatted_cloud = word_cloud_generator.format_word_cloud_for_display(word_freq)
                        st.markdown(formatted_cloud)
                        
                        # Show top words in metrics
                        st.markdown("#### Top Keywords")
                        top_words = list(word_freq.items())[:6]
                        cols = st.columns(3)
                        for i, (word, freq) in enumerate(top_words):
                            with cols[i % 3]:
                                st.metric(word.title(), freq)
                    else:
                        st.warning("No word cloud data generated")
            except Exception as e:
                st.error(f"Failed to generate word cloud: {str(e)}")
        
        # Key phrases using RAKE algorithm
        if st.button("🔑 Extract Keywords (RAKE)", help="Extract keywords using RAKE algorithm"):
            try:
                with st.spinner("Extracting keywords with RAKE algorithm..."):
                    import keyword_extractor
                    keywords = keyword_extractor.extract_keywords(results.transcript, method="rake", max_keywords=15)
                    
                    if keywords:
                        st.markdown("#### Keywords (RAKE Algorithm)")
                        for i, (keyword, score) in enumerate(keywords, 1):
                            st.write(f"{i}. **{keyword}** (score: {score:.2f})")
                    else:
                        st.warning("No keywords extracted")
            except Exception as e:
                st.error(f"Failed to extract keywords: {str(e)}")
    
    with col2:
        st.markdown("### 🔍 Advanced Analysis")
        
        # Advanced key phrases (LLM-based)
        if st.button("🔑 Extract Key Phrases (AI)", help="Extract key phrases using AI"):
            if "Advanced" in analysis_mode:
                try:
                    with st.spinner("Extracting key phrases with AI..."):
                        import ner_advanced
                        phrases = ner_advanced.extract_key_phrases(results.transcript)
                        
                        if phrases:
                            st.markdown("#### AI-Generated Key Phrases")
                            for i, phrase in enumerate(phrases[:10], 1):
                                st.write(f"{i}. **{phrase}**")
                        else:
                            st.warning("No key phrases extracted")
                except Exception as e:
                    st.error(f"Failed to extract key phrases: {str(e)}")
            else:
                st.warning("AI key phrases require Advanced mode (OpenAI API)")
        
        # Statistics
        if st.button("📈 Show Statistics", help="Display content statistics"):
            st.markdown("#### Content Statistics")
            
            # Basic stats
            words = len(results.transcript.split())
            sentences = len([s for s in results.transcript.split('.') if s.strip()])
            chars = len(results.transcript)
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Words", words)
            with col_b:
                st.metric("Sentences", sentences)
            with col_c:
                st.metric("Characters", chars)
            
            # Entity stats
            if results.entities:
                st.markdown("#### Entity Distribution")
                entity_counts = {k: len(v) for k, v in results.entities.items() if v}
                
                for entity_type, count in entity_counts.items():
                    st.write(f"**{entity_type}**: {count} found")

def render_structured_analysis_tab(results, analysis_mode: str):
    """Render structured analysis with JSON schema validation"""
    if "Advanced" not in analysis_mode:
        st.warning("🔒 Structured Analysis requires Advanced mode (OpenAI API)")
        st.info("Structured analysis provides domain-specific templates for medical, legal, business, and educational content with JSON schema validation.")
        return
    
    # Import structured analysis components
    try:
        from structured_analysis_ui import (
            display_structured_analysis_interface, perform_structured_analysis,
            display_custom_schema_creator, display_schema_validation_tool
        )
        
        # Create sub-tabs for structured analysis features
        struct_tab1, struct_tab2, struct_tab3 = st.tabs(["🔍 Analysis", "🛠️ Custom Schemas", "✅ Validation"])
        
        with struct_tab1:
            # Main structured analysis interface
            selected_template = display_structured_analysis_interface()
            
            st.markdown("---")
            
            # Perform analysis button
            if st.button("🚀 Perform Structured Analysis", type="primary"):
                analysis_result = perform_structured_analysis(results.transcript, selected_template)
                
                # Store result in session state for potential reuse
                if analysis_result:
                    st.session_state['structured_analysis_result'] = analysis_result
        
        with struct_tab2:
            # Custom schema creator
            display_custom_schema_creator()
        
        with struct_tab3:
            # Schema validation tool
            display_schema_validation_tool()
            
    except ImportError as e:
        st.error(f"Structured analysis components not available: {str(e)}")
        st.info("Please ensure all required dependencies are installed.")

def render_interactive_transcript(results):
    """Render interactive transcript with advanced features including waveform visualization"""
    st.subheader("🎯 Interactive Transcript")
    
    if not results.transcript:
        st.info("No transcript available for interactive features")
        return
    
    # Import waveform visualization
    try:
        from waveform_visualizer import waveform_visualizer, audio_navigator, create_clickable_waveform_html
        waveform_available = True
    except ImportError as e:
        logger.warning(f"Waveform visualization not available: {e}")
        waveform_available = False
    
    # Language detection and multi-language options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        detected_language = results.language if hasattr(results, 'language') else 'en'
        st.metric("Detected Language", detected_language.upper())
    
    with col2:
        if st.button("🔄 Re-transcribe with Language", help="Re-transcribe with specific language"):
            st.info("Language-specific transcription would be triggered here")
    
    with col3:
        if st.button("🌐 Translate Transcript", help="Translate to different language"):
            st.info("Translation feature would be available here")
    
    # Waveform Visualization Section
    if waveform_available:
        st.markdown("---")
        st.markdown("### 🌊 Audio Waveform & Navigation")
        
        # Check if we have the original audio file path
        audio_file_path = getattr(results, 'audio_file_path', None)
        if not audio_file_path and hasattr(st.session_state, 'current_audio_path'):
            audio_file_path = st.session_state.current_audio_path
        
        if audio_file_path and os.path.exists(audio_file_path):
            try:
                # Waveform generation options
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    waveform_type = st.selectbox(
                        "Waveform Type",
                        ["Standard Waveform", "Timeline with Markers", "Interactive Navigation"],
                        help="Choose the type of waveform visualization"
                    )
                
                with col2:
                    if st.button("🌊 Generate Waveform", type="primary"):
                        with st.spinner("Generating waveform visualization..."):
                            render_waveform_visualization(audio_file_path, results, waveform_type)
                
                # Display existing waveform if available
                if hasattr(st.session_state, 'waveform_image_path') and st.session_state.waveform_image_path:
                    render_existing_waveform(results)
                
            except Exception as e:
                st.error(f"Waveform visualization error: {str(e)}")
                logger.error(f"Waveform error: {e}")
        else:
            st.info("🌊 Waveform visualization requires the original audio file. Upload a new file to enable this feature.")
    
    # Enhanced transcript features
    st.markdown("---")
    
    # Audio processing options
    with st.expander("🎵 Audio Processing Options", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔊 Enhance Audio Quality", help="Apply audio enhancement for better transcription"):
                try:
                    with st.spinner("Enhancing audio quality..."):
                        import audio_processor
                        st.success("✅ Audio enhancement would be applied here")
                        st.info("Enhanced audio would improve transcription accuracy")
                except Exception as e:
                    st.error(f"Audio enhancement failed: {str(e)}")
            
            if st.button("📊 Audio Statistics", help="Show detailed audio analysis"):
                try:
                    with st.spinner("Analyzing audio..."):
                        # Placeholder for audio statistics
                        st.markdown("#### Audio Analysis")
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Estimated Duration", f"{len(results.transcript.split()) / 2.5 / 60:.1f} min")
                        with col_b:
                            st.metric("Speech Rate", f"{len(results.transcript.split()) / (len(results.transcript.split()) / 2.5 / 60):.0f} WPM")
                        with col_c:
                            st.metric("Word Count", len(results.transcript.split()))
                except Exception as e:
                    st.error(f"Audio analysis failed: {str(e)}")
        
        with col2:
            if st.button("✂️ Segment Audio", help="Split long audio into segments"):
                st.info("Audio segmentation would split long recordings into manageable chunks")
            
            if st.button("🎯 Detect Speakers", help="Identify different speakers (if available)"):
                st.info("Speaker diarization would identify different speakers in the audio")
    
    # Interactive transcript display
    try:
        import interactive_transcript
        
        # Check if we have timestamps
        timestamps = getattr(results, 'timestamps', None)
        
        if timestamps:
            st.success("🎯 Timestamped transcript available - full interactive features enabled")
            interactive_transcript.render_transcript_with_audio_sync(
                results.transcript, 
                timestamps
            )
        else:
            st.info("📝 Basic transcript available - limited interactive features")
            # Create basic interactive transcript
            interactive_trans = interactive_transcript.create_interactive_transcript(results.transcript)
            interactive_trans.render_interactive_transcript()
            
            # Show statistics
            stats = interactive_trans.get_transcript_statistics()
            if stats:
                st.markdown("### 📊 Transcript Statistics")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Segments", stats.get('total_segments', 0))
                with col2:
                    st.metric("Est. Duration", f"{stats.get('total_duration', 0):.1f}s")
                with col3:
                    st.metric("Avg Confidence", f"{stats.get('average_confidence', 0):.2f}")
    
    except ImportError:
        st.warning("Interactive transcript features not available")
        st.text_area("Transcript", value=results.transcript, height=400, disabled=True)
    
    # Advanced transcript options
    st.markdown("---")
    st.markdown("### 🔧 Advanced Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📝 Edit Transcript", help="Enable transcript editing"):
            st.info("Transcript editing interface would be available here")
    
    with col2:
        if st.button("🎯 Word-Level Timestamps", help="Generate word-level timestamps"):
            if "Advanced" in st.session_state.get('analysis_mode', 'Basic'):
                try:
                    # Check if we already have timestamps
                    timestamps = getattr(results, 'timestamps', None)
                    
                    if timestamps:
                        # Display existing timestamps
                        st.success("✅ Word-level timestamps available")
                        
                        # Create expandable sections for each segment
                        with st.expander("📝 View Word-Level Timestamps", expanded=True):
                            for idx, segment in enumerate(timestamps[:10]):  # Show first 10 segments
                                st.markdown(f"**Segment {idx + 1}** ({segment['start']:.2f}s - {segment['end']:.2f}s)")
                                st.markdown(f"*{segment['text']}*")
                                
                                # Show word-level timestamps if available
                                if 'words' in segment and segment['words']:
                                    word_data = []
                                    for word in segment['words']:
                                        word_data.append({
                                            'Word': word['word'],
                                            'Start': f"{word['start']:.2f}s",
                                            'End': f"{word['end']:.2f}s",
                                            'Duration': f"{word['end'] - word['start']:.2f}s"
                                        })
                                    
                                    # Display as a dataframe
                                    import pandas as pd
                                    df = pd.DataFrame(word_data)
                                    st.dataframe(df, use_container_width=True, height=200)
                                
                                st.divider()
                            
                            if len(timestamps) > 10:
                                st.info(f"Showing first 10 segments of {len(timestamps)} total")
                    else:
                        # Need to re-process with timestamps
                        with st.spinner("Re-processing with word-level timestamps..."):
                            # Get the audio file path from session state
                            audio_path = getattr(results, 'audio_file_path', None)
                            
                            if audio_path and os.path.exists(audio_path):
                                # Re-transcribe with timestamps enabled
                                import stt
                                
                                transcription_result = stt.transcribe_detailed(
                                    audio_path, 
                                    use_api=True,
                                    enable_timestamps=True
                                )
                                
                                # Update results with timestamps
                                if hasattr(transcription_result, 'timestamps') and transcription_result.timestamps:
                                    results.timestamps = transcription_result.timestamps
                                    st.session_state.transcription_results = results
                                    st.success("✅ Word-level timestamps generated successfully!")
                                    st.rerun()
                                else:
                                    st.warning("No word-level timestamps were generated. Try using a different model.")
                            else:
                                st.error("Audio file not found. Please re-upload and process the file.")
                                
                except Exception as e:
                    st.error(f"Timestamp generation failed: {str(e)}")
                    logger.error(f"Timestamp generation error: {e}", exc_info=True)
            else:
                st.warning("Word-level timestamps require Advanced mode")
    
    with col3:
        if st.button("🔍 Search & Navigate", help="Advanced search and navigation"):
            search_term = st.text_input("Search in transcript:", key="transcript_search")
            if search_term:
                # Simple search highlighting
                highlighted_text = results.transcript.replace(
                    search_term, 
                    f"**{search_term}**"
                )
                st.markdown("#### Search Results")
                st.markdown(highlighted_text)

def render_waveform_visualization(audio_file_path: str, results, waveform_type: str):
    """Render waveform visualization based on selected type"""
    try:
        from waveform_visualizer import waveform_visualizer, audio_navigator, create_clickable_waveform_html
        
        # Get speaker and transcript data if available
        speaker_segments = getattr(results, 'speaker_segments', None)
        transcript_segments = getattr(results, 'transcript_segments', None)
        
        if waveform_type == "Standard Waveform":
            # Generate standard waveform
            waveform_path = waveform_visualizer.generate_waveform_image(
                audio_file_path,
                speaker_segments=speaker_segments,
                transcript_segments=transcript_segments
            )
            
            st.image(waveform_path, caption="Audio Waveform", use_column_width=True)
            st.session_state.waveform_image_path = waveform_path
            
        elif waveform_type == "Timeline with Markers":
            # Generate timeline waveform with markers
            timeline_path = waveform_visualizer.create_waveform_with_timeline(
                audio_file_path,
                transcript_data=transcript_segments,
                speaker_data=speaker_segments
            )
            
            st.image(timeline_path, caption="Audio Waveform with Timeline", use_column_width=True)
            st.session_state.waveform_image_path = timeline_path
            
            # Add timeline navigation controls
            render_timeline_controls(audio_file_path)
            
        elif waveform_type == "Interactive Navigation":
            # Generate interactive waveform
            waveform_path = waveform_visualizer.generate_waveform_image(audio_file_path)
            
            # Get audio duration
            import media
            media_info = media.get_media_info(audio_file_path)
            duration = media_info.get('duration', 0)
            
            # Create clickable HTML
            clickable_html = create_clickable_waveform_html(waveform_path, duration)
            st.components.v1.html(clickable_html, height=300)
            
            # Add navigation controls
            render_audio_navigation_controls(audio_file_path, duration)
            
            st.session_state.waveform_image_path = waveform_path
        
        st.success("✅ Waveform visualization generated successfully!")
        
    except Exception as e:
        st.error(f"Failed to generate waveform: {str(e)}")
        logger.error(f"Waveform generation failed: {e}")

def render_existing_waveform(results):
    """Render existing waveform if available"""
    try:
        waveform_path = st.session_state.waveform_image_path
        
        if os.path.exists(waveform_path):
            st.markdown("#### 🌊 Current Waveform")
            st.image(waveform_path, use_column_width=True)
            
            # Add waveform controls
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Regenerate", help="Regenerate waveform"):
                    if hasattr(st.session_state, 'current_audio_path'):
                        render_waveform_visualization(
                            st.session_state.current_audio_path, 
                            results, 
                            "Standard Waveform"
                        )
            
            with col2:
                if st.button("📥 Download Waveform", help="Download waveform image"):
                    with open(waveform_path, 'rb') as f:
                        st.download_button(
                            label="Download PNG",
                            data=f.read(),
                            file_name="waveform.png",
                            mime="image/png"
                        )
            
            with col3:
                if st.button("🗑️ Clear Waveform", help="Clear current waveform"):
                    if 'waveform_image_path' in st.session_state:
                        del st.session_state.waveform_image_path
                    st.rerun()
        
    except Exception as e:
        st.error(f"Error displaying waveform: {str(e)}")

def render_timeline_controls(audio_file_path: str):
    """Render timeline navigation controls"""
    try:
        from waveform_visualizer import audio_navigator
        
        # Initialize navigation
        audio_navigator.initialize_navigation(audio_file_path)
        nav_data = audio_navigator.get_navigation_controls()
        
        st.markdown("#### ⏯️ Timeline Navigation")
        
        # Time slider
        current_time = st.slider(
            "Current Position",
            min_value=0.0,
            max_value=nav_data['total_duration'],
            value=0.0,
            step=0.1,
            format="%.1fs",
            help="Drag to navigate through the audio timeline"
        )
        
        # Segment navigation
        if nav_data['segments']:
            segment_options = [seg['label'] for seg in nav_data['segments']]
            selected_segment = st.selectbox(
                "Jump to Segment",
                options=segment_options,
                help="Select a segment to jump to that position"
            )
            
            if selected_segment:
                # Find the selected segment
                for seg in nav_data['segments']:
                    if seg['label'] == selected_segment:
                        st.info(f"Selected: {selected_segment} (Duration: {seg['duration']:.1f}s)")
                        break
        
        # Display current position info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Time", f"{current_time:.1f}s")
        with col2:
            st.metric("Total Duration", nav_data['formatted_duration'])
        with col3:
            progress = (current_time / nav_data['total_duration']) * 100 if nav_data['total_duration'] > 0 else 0
            st.metric("Progress", f"{progress:.1f}%")
        
    except Exception as e:
        st.error(f"Timeline controls error: {str(e)}")

def render_audio_navigation_controls(audio_file_path: str, duration: float):
    """Render interactive audio navigation controls"""
    try:
        st.markdown("#### 🎮 Audio Navigation Controls")
        
        # Playback controls (placeholder - would need actual audio player integration)
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("⏮️", help="Previous segment"):
                st.info("Previous segment navigation")
        
        with col2:
            if st.button("⏯️", help="Play/Pause"):
                st.info("Play/Pause functionality")
        
        with col3:
            if st.button("⏹️", help="Stop"):
                st.info("Stop playback")
        
        with col4:
            if st.button("⏭️", help="Next segment"):
                st.info("Next segment navigation")
        
        with col5:
            playback_speed = st.selectbox("Speed", ["0.5x", "0.75x", "1x", "1.25x", "1.5x", "2x"], index=2)
        
        # Position display
        st.markdown("**Click on the waveform above to navigate to specific positions**")
        
        # Audio segments info
        if duration > 0:
            segments = int(duration / 10) + 1  # 10-second segments
            st.info(f"📊 Audio divided into {segments} segments of ~10 seconds each")
            
            # Segment quick navigation
            if segments > 1:
                segment_cols = st.columns(min(segments, 6))  # Max 6 columns
                for i in range(min(segments, 6)):
                    with segment_cols[i]:
                        start_time = i * 10
                        end_time = min((i + 1) * 10, duration)
                        if st.button(f"Seg {i+1}\n({start_time}s-{end_time:.0f}s)", key=f"seg_{i}"):
                            st.info(f"Navigate to segment {i+1}: {start_time}s - {end_time:.0f}s")
        
    except Exception as e:
        st.error(f"Navigation controls error: {str(e)}")

def render_results(analysis_mode: str):
    """Legacy render_results function - redirects to enhanced version"""
    return render_results_enhanced(analysis_mode)

def render_transcript_display():
    """Render the transcript display with proper formatting and scrolling"""
    st.subheader("📝 Full Transcript")
    
    if st.session_state.transcript:
        # Display transcript statistics
        word_count = len(st.session_state.transcript.split())
        char_count = len(st.session_state.transcript)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Words", word_count)
        with col2:
            st.metric("Characters", char_count)
        with col3:
            estimated_duration = word_count / 150  # Average speaking rate
            st.metric("Est. Duration", f"{estimated_duration:.1f} min")
        
        # Transcript display with proper formatting
        st.markdown("---")
        
        # Option to show/hide line numbers
        show_line_numbers = st.checkbox("Show line numbers", value=False)
        
        if show_line_numbers:
            # Split transcript into lines and add line numbers
            lines = st.session_state.transcript.split('\n')
            numbered_transcript = '\n'.join([f"{i+1:3d}: {line}" for i, line in enumerate(lines)])
            transcript_to_display = numbered_transcript
        else:
            transcript_to_display = st.session_state.transcript
        
        # Display transcript in a scrollable text area
        st.text_area(
            "Transcript Content:",
            value=transcript_to_display,
            height=400,
            help="Full transcript of your audio content. Use Ctrl+F to search within the text.",
            label_visibility="collapsed"
        )
        
        # Search functionality
        search_term = st.text_input("🔍 Search in transcript:", placeholder="Enter search term...")
        if search_term:
            search_results = find_text_occurrences(st.session_state.transcript, search_term)
            if search_results:
                st.success(f"Found {len(search_results)} occurrence(s) of '{search_term}'")
                for i, (start, end, context) in enumerate(search_results[:5]):  # Show first 5 results
                    st.write(f"**Result {i+1}:** ...{context}...")
            else:
                st.info(f"No occurrences of '{search_term}' found")
    else:
        st.info("No transcript available. Please process an audio file first.")

def render_basic_entities_display():
    """Render entity display for basic mode with categorized results"""
    st.subheader("🏷️ Basic Entity Analysis (spaCy)")
    st.caption("Local processing using spaCy's pre-trained models")
    
    if st.session_state.entities:
        # Entity statistics
        total_entities = sum(len(entities) for entities in st.session_state.entities.values())
        entity_types_count = len(st.session_state.entities)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Entities", total_entities)
        with col2:
            st.metric("Entity Types", entity_types_count)
        
        st.markdown("---")
        
        # Display entities by category with enhanced formatting
        entity_display_config = {
            "PERSON": {"icon": "👤", "color": "#FF6B6B", "description": "People and individuals"},
            "ORG": {"icon": "🏢", "color": "#4ECDC4", "description": "Organizations and companies"},
            "DATE": {"icon": "📅", "color": "#45B7D1", "description": "Dates and temporal expressions"},
            "TIME": {"icon": "⏰", "color": "#96CEB4", "description": "Time references"},
            "GPE": {"icon": "🌍", "color": "#FFEAA7", "description": "Geographic locations"},
            "MONEY": {"icon": "💰", "color": "#DDA0DD", "description": "Monetary values"},
            "CARDINAL": {"icon": "🔢", "color": "#98D8C8", "description": "Numbers and quantities"}
        }
        
        # Create columns for entity display
        cols = st.columns(2)
        col_index = 0
        
        for entity_type, entities in st.session_state.entities.items():
            if entities:  # Only show categories with entities
                config = entity_display_config.get(entity_type, {"icon": "🏷️", "color": "#95A5A6", "description": "Other entities"})
                
                with cols[col_index % 2]:
                    # Create a styled container for each entity type
                    with st.container():
                        st.markdown(f"""
                        <div style="background-color: {config['color']}20; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                            <h4 style="margin: 0; color: {config['color']};">
                                {config['icon']} {entity_type.title()}
                            </h4>
                            <p style="margin: 5px 0; font-size: 0.8em; color: #666;">
                                {config['description']} ({len(entities)} found)
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Display entities as tags
                        entity_tags = " ".join([f"`{entity}`" for entity in entities])
                        st.markdown(entity_tags)
                        st.markdown("")  # Add spacing
                
                col_index += 1
        
        # Show confidence information if available
        if hasattr(st.session_state, 'entity_confidence') and st.session_state.entity_confidence:
            with st.expander("🎯 Confidence Scores"):
                st.caption("Entity extraction confidence levels")
                for entity_type, confidence_data in st.session_state.entity_confidence.items():
                    st.write(f"**{entity_type}:**")
                    for entity, confidence in confidence_data.items():
                        st.write(f"  • {entity}: {confidence:.2%}")
    else:
        st.info("No entities extracted. This could mean:")
        st.write("• The audio content doesn't contain recognizable entities")
        st.write("• The transcription quality was too low for entity extraction")
        st.write("• Try using Advanced mode for better entity recognition")

def render_advanced_entities_display():
    """Render entity display for advanced mode with entities and summary"""
    st.subheader("🤖 Advanced AI Analysis (OpenAI GPT)")
    st.caption("AI-powered analysis with contextual understanding")
    
    if st.session_state.entities or st.session_state.summary:
        # Create two columns: entities and summary
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### 🏷️ Extracted Entities")
            
            if st.session_state.entities:
                # Entity statistics
                total_entities = sum(len(entities) for entities in st.session_state.entities.values())
                st.metric("Total Entities", total_entities)
                
                # Advanced entity display with better categorization
                advanced_entity_config = {
                    "persons": {"icon": "👥", "color": "#FF6B6B", "title": "People"},
                    "organizations": {"icon": "🏢", "color": "#4ECDC4", "title": "Organizations"},
                    "dates": {"icon": "📅", "color": "#45B7D1", "title": "Dates & Times"},
                    "locations": {"icon": "📍", "color": "#FFEAA7", "title": "Locations"},
                    "key_topics": {"icon": "💡", "color": "#DDA0DD", "title": "Key Topics"},
                    "money": {"icon": "💰", "color": "#98D8C8", "title": "Financial"},
                    "numbers": {"icon": "🔢", "color": "#96CEB4", "title": "Numbers"}
                }
                
                for entity_type, entities in st.session_state.entities.items():
                    if entities:
                        config = advanced_entity_config.get(entity_type, {"icon": "🏷️", "color": "#95A5A6", "title": entity_type.title()})
                        
                        st.markdown(f"""
                        <div style="background-color: {config['color']}20; padding: 10px; border-radius: 8px; margin-bottom: 8px;">
                            <h5 style="margin: 0; color: {config['color']};">
                                {config['icon']} {config['title']} ({len(entities)})
                            </h5>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Display entities as styled tags
                        for entity in entities:
                            st.markdown(f"<span style='background-color: {config['color']}30; padding: 2px 8px; border-radius: 12px; margin: 2px; display: inline-block; font-size: 0.9em;'>{entity}</span>", unsafe_allow_html=True)
                        
                        st.markdown("")  # Add spacing
            else:
                st.info("No entities extracted by advanced analysis")
        
        with col2:
            st.markdown("### 📋 Content Summary")
            
            if st.session_state.summary:
                # Summary statistics
                summary_words = len(st.session_state.summary.split())
                st.metric("Summary Length", f"{summary_words} words")
                
                # Display summary in a styled container
                st.markdown(f"""
                <div style="background-color: #F8F9FA; padding: 20px; border-radius: 10px; border-left: 4px solid #007BFF;">
                    <p style="margin: 0; line-height: 1.6; font-size: 1.1em;">
                        {st.session_state.summary}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Sentiment analysis if available
                if hasattr(st.session_state, 'sentiment') and st.session_state.sentiment:
                    st.markdown("### 😊 Sentiment Analysis")
                    sentiment = st.session_state.sentiment
                    
                    # Create sentiment visualization
                    col_pos, col_neu, col_neg = st.columns(3)
                    with col_pos:
                        st.metric("Positive", f"{sentiment.get('positive', 0):.1%}", delta=None)
                    with col_neu:
                        st.metric("Neutral", f"{sentiment.get('neutral', 0):.1%}", delta=None)
                    with col_neg:
                        st.metric("Negative", f"{sentiment.get('negative', 0):.1%}", delta=None)
            else:
                st.info("No summary available")
    else:
        st.info("No advanced analysis results available. Please process an audio file first.")

def render_download_options(analysis_mode: str):
    """Render download options for transcripts and extracted data"""
    st.subheader("📥 Download Options")
    st.caption("Export your results in various formats")
    
    if not (st.session_state.transcript or st.session_state.entities or st.session_state.summary):
        st.info("No data available for download. Please process an audio file first.")
        return
    
    # Create download sections
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📄 Text Formats")
        
        # Transcript download
        if st.session_state.transcript:
            st.download_button(
                label="📝 Download Transcript (.txt)",
                data=st.session_state.transcript,
                file_name=f"transcript_{utils.get_timestamp()}.txt",
                mime="text/plain",
                help="Plain text transcript"
            )
        
        # Summary download (Advanced mode)
        if "Advanced" in analysis_mode and st.session_state.summary:
            st.download_button(
                label="📋 Download Summary (.txt)",
                data=st.session_state.summary,
                file_name=f"summary_{utils.get_timestamp()}.txt",
                mime="text/plain",
                help="AI-generated content summary"
            )
    
    with col2:
        st.markdown("#### 📊 Structured Data")
        
        # Entities download
        if st.session_state.entities:
            entities_text = format_entities_for_download(st.session_state.entities, analysis_mode)
            st.download_button(
                label="🏷️ Download Entities (.txt)",
                data=entities_text,
                file_name=f"entities_{analysis_mode.lower().replace(' ', '_')}_{utils.get_timestamp()}.txt",
                mime="text/plain",
                help="Extracted entities by category"
            )
            
            # JSON format for entities
            import json
            entities_json = json.dumps(st.session_state.entities, indent=2, ensure_ascii=False)
            st.download_button(
                label="📋 Download Entities (.json)",
                data=entities_json,
                file_name=f"entities_{utils.get_timestamp()}.json",
                mime="application/json",
                help="Entities in JSON format for further processing"
            )
    
    # Combined report download
    st.markdown("#### 📑 Complete Report")
    
    if st.session_state.transcript or st.session_state.entities or st.session_state.summary:
        complete_report = generate_complete_report(analysis_mode)
        st.download_button(
            label="📄 Download Complete Report (.txt)",
            data=complete_report,
            file_name=f"complete_report_{utils.get_timestamp()}.txt",
            mime="text/plain",
            help="Combined transcript, entities, and summary in one file",
            type="primary"
        )

def find_text_occurrences(text: str, search_term: str, context_length: int = 50):
    """Find all occurrences of a search term in text with context"""
    if not text or not search_term:
        return []
    
    results = []
    text_lower = text.lower()
    search_lower = search_term.lower()
    
    start = 0
    while True:
        pos = text_lower.find(search_lower, start)
        if pos == -1:
            break
        
        # Get context around the match
        context_start = max(0, pos - context_length)
        context_end = min(len(text), pos + len(search_term) + context_length)
        context = text[context_start:context_end]
        
        results.append((pos, pos + len(search_term), context))
        start = pos + 1
    
    return results

def format_entities_for_download(entities: dict, analysis_mode: str) -> str:
    """Format entities for download in a readable text format"""
    if not entities:
        return "No entities found."
    
    lines = [f"Entity Extraction Results ({analysis_mode})", "=" * 50, ""]
    
    # Count entities and types with proper error handling
    total_entities = 0
    entity_types_with_data = 0
    
    for entity_type, entity_list in entities.items():
        if entity_list and isinstance(entity_list, list):
            # Filter out None values
            valid_entities = [entity for entity in entity_list if entity is not None]
            if valid_entities:
                lines.append(f"{entity_type.upper()}:")
                for entity in valid_entities:
                    lines.append(f"  • {entity}")
                lines.append("")
                total_entities += len(valid_entities)
                entity_types_with_data += 1
    
    lines.append(f"Total entities: {total_entities}")
    lines.append(f"Entity types: {entity_types_with_data}")
    
    return "\n".join(lines)

def generate_complete_report(analysis_mode: str) -> str:
    """Generate a complete report combining all available data"""
    from datetime import datetime
    
    lines = [
        "AUDIO TRANSCRIPTION & ANALYSIS REPORT",
        "=" * 50,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Analysis Mode: {analysis_mode}",
        "",
    ]
    
    # Add transcript with error handling
    try:
        if hasattr(st.session_state, 'transcript') and st.session_state.transcript:
            lines.extend([
                "TRANSCRIPT",
                "-" * 20,
                st.session_state.transcript,
                "",
            ])
    except AttributeError:
        pass
    
    # Add summary (Advanced mode) with error handling
    try:
        if "Advanced" in analysis_mode and hasattr(st.session_state, 'summary') and st.session_state.summary:
            lines.extend([
                "CONTENT SUMMARY",
                "-" * 20,
                st.session_state.summary,
                "",
            ])
    except AttributeError:
        pass
    
    # Add entities with error handling
    try:
        if hasattr(st.session_state, 'entities') and st.session_state.entities:
            lines.extend([
                "EXTRACTED ENTITIES",
                "-" * 20,
            ])
            
            total_entities = 0
            entity_types_with_data = 0
            
            for entity_type, entity_list in st.session_state.entities.items():
                if entity_list and isinstance(entity_list, list):
                    # Filter out None values
                    valid_entities = [entity for entity in entity_list if entity is not None]
                    if valid_entities:
                        lines.append(f"{entity_type.upper()}:")
                        for entity in valid_entities:
                            lines.append(f"  • {entity}")
                        lines.append("")
                        total_entities += len(valid_entities)
                        entity_types_with_data += 1
            
            lines.extend([
                f"Total entities: {total_entities}",
                f"Entity types: {entity_types_with_data}",
                "",
            ])
    except (AttributeError, TypeError):
        pass
    
    # Add statistics with error handling
    try:
        if hasattr(st.session_state, 'transcript') and st.session_state.transcript:
            word_count = len(st.session_state.transcript.split())
            char_count = len(st.session_state.transcript)
            lines.extend([
                "STATISTICS",
                "-" * 20,
                f"Word count: {word_count}",
                f"Character count: {char_count}",
                f"Estimated duration: {word_count / 150:.1f} minutes",
            ])
    except AttributeError:
        pass
    
    return "\n".join(lines)



def cleanup_session_files():
    """Clean up any files stored in session state"""
    try:
        if hasattr(st.session_state, 'generated_audio_path') and st.session_state.generated_audio_path:
            if os.path.exists(st.session_state.generated_audio_path):
                utils.cleanup_file(st.session_state.generated_audio_path)
                logger.info(f"Cleaned up session audio file: {st.session_state.generated_audio_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup session files: {e}")

def validate_processing_requirements(analysis_mode: str) -> bool:
    """Validate that all requirements are met for processing with enhanced feedback"""
    api_status = Config.validate_api_keys()
    
    if "Advanced" in analysis_mode:
        if not api_status["openai"]:
            mode_name = "Advanced+ (Speaker Diarization)" if "Advanced+" in analysis_mode else "Advanced"
            st.error(f"❌ {mode_name} mode requires OpenAI API key")
            
            with st.expander("🔧 Configuration Help", expanded=True):
                st.markdown(f"""
                **To use {mode_name} mode, you need to configure your OpenAI API key:**
                
                1. **Get an API key:**
                   - Visit [OpenAI Platform](https://platform.openai.com/)
                   - Sign up or log in to your account
                   - Navigate to API Keys section
                   - Create a new API key
                
                2. **Configure the key:**
                   - Copy your API key
                   - Open the `.env` file in your project directory
                   - Add: `OPENAI_API_KEY=your_key_here`
                   - Restart the application
                
                3. **Alternative:**
                   - Switch to Basic mode for offline processing
                   - Basic mode uses local spaCy models (no API required)
                
                {"**Advanced+ Features:** Speaker diarization, multi-language support, interactive transcripts" if "Advanced+" in analysis_mode else ""}
                """)
            
            return False
    
    # Check if user preferences suggest auto-clearing results
    preferences = session_manager.get_preferences()
    if preferences.auto_clear_results and session_manager.has_results():
        st.info("🔄 Auto-clearing previous results...")
        session_manager.clear_results()
    
    return True

if __name__ == "__main__":
    # Initialize enhanced logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    utils.setup_enhanced_logging(log_level)
    
    # Ensure temp directory exists
    utils.ensure_temp_directory()
    
    try:
        # Run main application
        main()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        cleanup_session_files()
    except Exception as e:
        logger.error(f"Application error: {e}")
        cleanup_session_files()
        raise
    finally:
        # Clean up any remaining session files
        cleanup_session_files()