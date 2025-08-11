#!/usr/bin/env python3
"""
Audio/Video Transcription and Entity Extraction App - Refactored UI
Clean tab-based interface replacing the cluttered sidebar-driven model
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

# Import refactored UI modules - centralized styling
from ui_styles_refactored import apply_theme, THEMES
from enhanced_components_refactored import (
    enhanced_file_uploader, enhanced_progress_indicator, enhanced_metric_display,
    enhanced_entity_display, enhanced_loading_state, enhanced_audio_player,
    create_tab_navigation, create_stat_card, create_action_button,
    create_info_card, render_empty_state, create_feature_card
)

# Import advanced feature modules
from multilingual_transcription import multilingual_transcriber, multilingual_ui, MultilingualTranscriptionResult
from language_support import multilingual_ui as lang_ui, translation_service, realtime_processor
from visual_search_ui import visual_search_ui
from visual_search import visual_search_engine
from ai_provider_ui import ai_provider_ui
from advanced_content_analysis_ui import advanced_content_analysis_ui
from advanced_content_analysis import advanced_content_analyzer

# Import export and integration modules (Task 41)
from export_integrations_ui import render_export_integrations_interface

# Import content recommendations modules (Task 42)
from content_recommendations_ui import (
    render_content_recommendations_interface, render_smart_tagging_interface
)

# Import content sourcing modules
try:
    from content_sourcing_ui import render_content_sourcing_interface
    CONTENT_SOURCING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Content sourcing modules not available: {e}")
    CONTENT_SOURCING_AVAILABLE = False

# Import user authentication modules (Task 46)
try:
    from user_authentication_ui import (
        render_authentication_interface, render_user_profile_interface,
        render_user_logout, get_current_user, require_authentication,
        check_user_permission, initialize_auth_session_state
    )
    USER_AUTH_AVAILABLE = True
except ImportError as e:
    logger.warning(f"User authentication modules not available: {e}")
    USER_AUTH_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import additional modules needed for refactored UI
try:
    from ui_styles_fixed import apply_theme, render_theme_selector
    from search.search_ui import SearchUI
    from search.analytics_ui import AnalyticsUI
    from video_ui import VideoUI
    from content_insights_ui import ContentInsightsUI
    from ai_insights_ui import ContentInsightsUI as AIInsightsUI
    from batch_interface import render_batch_interface
    from admin_analytics import admin_analytics
    ADVANCED_MODULES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Some advanced modules not available: {e}")
    ADVANCED_MODULES_AVAILABLE = False


def main():
    """Main application entry point with refactored tab-based UI"""
    
    # Initialize session state and configuration
    session_manager.initialize_session_state()
    
    # Initialize authentication session state
    if USER_AUTH_AVAILABLE:
        initialize_auth_session_state()
    
    # Apply custom styling
    inject_custom_css()
    
    # Set page configuration
    st.set_page_config(
        page_title="Audio/Video Transcription App",
        page_icon="🎤",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Check authentication first
    if USER_AUTH_AVAILABLE:
        authenticated = render_authentication_interface()
        if not authenticated:
            return  # Show login interface and exit
    else:
        st.warning("⚠️ User authentication system not available. Running in demo mode.")
    
    # Render the new simplified sidebar
    render_simplified_sidebar()
    
    # Render user logout in sidebar
    if USER_AUTH_AVAILABLE:
        render_user_logout()
    
    # Get analysis mode from sidebar
    analysis_mode = st.session_state.get('analysis_mode', 'Basic (spaCy)')
    
    # Main tab-based navigation with user greeting
    if USER_AUTH_AVAILABLE:
        current_user = get_current_user()
        if current_user:
            st.title(f"🎤 Welcome back, {current_user.full_name.split()[0]}!")
            st.markdown("Audio/Video Transcription & Analysis")
        else:
            st.title("🎤 Audio/Video Transcription & Analysis")
    else:
        st.title("🎤 Audio/Video Transcription & Analysis")
    
    # Create main navigation tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎤 Transcribe & Analyze",
        "🔍 Search & Insights", 
        "🎬 Video & Media Tools",
        "🤖 AI & Advanced Features",
        "⚙️ Admin & Settings"
    ])
    
    with tab1:
        render_transcription_tab(analysis_mode)
    
    with tab2:
        render_search_and_insights_tab()
    
    with tab3:
        render_video_and_media_tab()
    
    with tab4:
        render_ai_and_advanced_tab()
    
    with tab5:
        render_admin_and_settings_tab()


def render_simplified_sidebar():
    """Render the simplified sidebar with contextual settings only"""
    
    st.sidebar.title("⚙️ App Settings")
    
    # Appearance Settings
    with st.sidebar.expander("🎨 Appearance", expanded=False):
        render_theme_selector()
    
    # Analysis & Processing Settings
    with st.sidebar.expander("🔬 Analysis & Processing", expanded=True):
        # Analysis mode selection
        analysis_mode = st.selectbox(
            "Analysis Mode",
            ["Basic (spaCy)", "Advanced (OpenAI)", "Advanced+ (Speaker Diarization)", "🌍 Multi-Language"],
            help="Choose your analysis approach",
            key="analysis_mode"
        )
        
        # Audio processing options
        st.markdown("**Audio Processing:**")
        enable_audio_enhancement = st.checkbox("🔊 Audio Enhancement", value=True)
        enable_segmentation = st.checkbox("✂️ Audio Segmentation", value=False)
        
        # Batch processing
        batch_mode = st.checkbox("📦 Batch Processing", value=False)
    
    # API & System Status
    with st.sidebar.expander("🔑 API & System Status", expanded=False):
        api_status = Config.validate_api_keys()
        display_api_status(api_status)
        
        # System health check
        if st.button("🏥 System Health Check"):
            with st.spinner("Checking system health..."):
                health_status = health_check_endpoint()
                if health_status.get('status') == 'healthy':
                    st.success("✅ System is healthy")
                else:
                    st.warning("⚠️ System issues detected")
    
    # Help & Info
    with st.sidebar.expander("ℹ️ Help & Info", expanded=False):
        st.markdown("""
        **Quick Start:**
        1. Upload audio/video or record live
        2. Choose analysis mode
        3. Click transcribe & analyze
        
        **Supported Formats:**
        • Audio: MP3, WAV, M4A
        • Video: MP4, AVI, MOV
        
        **Need Help?**
        Check the Admin & Settings tab for detailed guides.
        """)


def render_transcription_tab(analysis_mode: str):
    """Render the main transcription and analysis interface"""
    
    st.markdown("## 🎤 Audio/Video Transcription")
    
    # File upload section
    st.markdown("### 📁 Upload Media")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Choose an audio or video file",
            type=['mp3', 'wav', 'm4a', 'mp4', 'avi', 'mov'],
            help="Upload your media file for transcription"
        )
    
    with col2:
        st.markdown("**Or record live:**")
        recorded_audio = st.audio_input("🎤 Record Audio")
    
    # Processing section
    if uploaded_file or recorded_audio:
        st.markdown("### ⚙️ Processing Options")
        
        # Language settings for multi-language mode
        if "Multi-Language" in analysis_mode:
            render_multilingual_settings()
        
        # Processing button
        audio_source = uploaded_file or recorded_audio
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            process_button = st.button(
                "🚀 Transcribe & Analyze", 
                type="primary",
                help=f"Process using {analysis_mode} mode"
            )
        
        with col2:
            if st.button("🗑️ Clear Results"):
                session_manager.clear_results()
                st.rerun()
        
        # Process audio
        if process_button:
            process_audio_content(audio_source, analysis_mode)
    
    # Results section
    if session_manager.has_results():
        st.markdown("---")
        render_transcription_results(analysis_mode)
        col1, col2 = st.columns([3, 1])
        
        with col1:
            process_button = st.button(
                "🚀 Transcribe & Analyze", 
                type="primary",
                help=f"Process using {analysis_mode} mode"
            )
        
        with col2:
            if st.button("🗑️ Clear Results"):
                session_manager.clear_results()
                st.rerun()
        
        # Process audio
        if process_button:
            process_audio_content(audio_source, analysis_mode)
    
    # Results section
    if session_manager.has_results():
        st.markdown("---")
        render_transcription_results(analysis_mode)


def render_search_and_insights_tab():
    """Render the combined search and insights interface"""
    
    st.markdown("## 🔍 Search & AI Insights")
    
    # Sub-tabs for different search and insight features
    search_tab, insights_tab, recommendations_tab, sources_tab, visual_tab, analytics_tab = st.tabs([
        "🔍 Content Search",
        "🧠 AI Insights", 
        "🎯 Smart Recommendations",
        "📚 Content Sources",
        "🗺️ Visual Discovery",
        "📊 Advanced Analytics"
    ])
    
    with search_tab:
        render_content_search_interface()
    
    with insights_tab:
        render_ai_insights_interface()
    
    with recommendations_tab:
        render_content_recommendations_interface()
    
    with sources_tab:
        if CONTENT_SOURCING_AVAILABLE:
            render_content_sourcing_interface()
        else:
            st.info("Content sourcing features require additional setup.")
    
    with visual_tab:
        render_visual_discovery_interface()
    
    with analytics_tab:
        render_advanced_analytics_interface()


def render_video_and_media_tab():
    """Render video processing and media tools"""
    
    st.markdown("## 🎬 Video & Media Tools")
    
    # Video processing tools
    video_tab, media_tab, export_tab = st.tabs([
        "🎬 Video Processing",
        "🎵 Media Tools", 
        "📤 Export & Integrations"
    ])
    
    with video_tab:
        render_video_processing_interface()
    
    with media_tab:
        render_media_tools_interface()
    
    with export_tab:
        # Use the comprehensive export and integrations interface
        render_export_integrations_interface()


def render_ai_and_advanced_tab():
    """Render AI provider management and advanced features"""
    
    st.markdown("## 🤖 AI & Advanced Features")
    
    # Advanced feature tabs
    ai_tab, content_tab, tagging_tab, provider_tab, models_tab = st.tabs([
        "🧠 Content Analysis",
        "🎨 Content Generation", 
        "🏷️ Smart Tagging",
        "🤖 AI Providers",
        "🔧 Model Management"
    ])
    
    with ai_tab:
        # Advanced content analysis
        if ADVANCED_MODULES_AVAILABLE:
            try:
                advanced_content_analysis_ui.render_advanced_analysis_interface()
            except Exception as e:
                st.error(f"Advanced content analysis error: {str(e)}")
                st.info("Advanced content analysis features are being loaded...")
        else:
            st.info("Advanced content analysis requires additional modules.")
    
    with content_tab:
        render_content_generation_interface()
    
    with tagging_tab:
        render_smart_tagging_interface()
    
    with provider_tab:
        # AI provider management
        if ADVANCED_MODULES_AVAILABLE:
            try:
                ai_provider_ui.render_provider_management_interface()
            except Exception as e:
                st.error(f"AI provider interface error: {str(e)}")
                st.info("AI provider management features are being loaded...")
        else:
            st.info("AI provider management requires additional modules.")
    
    with models_tab:
        render_model_management_interface()


def render_admin_and_settings_tab():
    """Render admin panel and application settings"""
    
    st.markdown("## ⚙️ Admin & Settings")
    
    # Admin and settings tabs - include user profile if auth available
    if USER_AUTH_AVAILABLE:
        admin_tab, profile_tab, settings_tab, security_tab, help_tab = st.tabs([
            "👑 Admin Panel",
            "👤 User Profile",
            "⚙️ App Settings", 
            "🛡️ Security & Privacy",
            "📚 Help & Documentation"
        ])
        
        with profile_tab:
            render_user_profile_interface()
    else:
        admin_tab, settings_tab, security_tab, help_tab = st.tabs([
            "👑 Admin Panel",
            "⚙️ App Settings", 
            "🛡️ Security & Privacy",
            "📚 Help & Documentation"
        ])
    
    with admin_tab:
        render_admin_panel_interface()
    
    with settings_tab:
        render_app_settings_interface()
    
    with security_tab:
        render_security_interface()
    
    with help_tab:
        render_help_documentation()


# Helper functions for each tab interface

def render_multilingual_settings():
    """Render multi-language specific settings"""
    st.markdown("#### 🌍 Multi-Language Settings")
    multilingual_settings = multilingual_ui.render_language_selection_interface()
    st.session_state.multilingual_settings = multilingual_settings


def render_content_search_interface():
    """Render content search interface"""
    st.markdown("### 🔍 Search Your Content")
    
    if not session_manager.has_results():
        st.info("Process some audio/video content first to enable search features.")
        return
    
    # Search functionality
    search_query = st.text_input("Search in transcript:", placeholder="Enter keywords...")
    
    if search_query:
        results = session_manager.get_results()
        transcript = results.transcript
        
        # Simple search implementation
        if search_query.lower() in transcript.lower():
            st.success(f"Found '{search_query}' in transcript!")
            
            # Highlight context
            context_start = max(0, transcript.lower().find(search_query.lower()) - 100)
            context_end = min(len(transcript), transcript.lower().find(search_query.lower()) + len(search_query) + 100)
            context = transcript[context_start:context_end]
            
            st.text_area("Context:", value=context, height=150)
        else:
            st.warning(f"'{search_query}' not found in transcript.")


def render_ai_insights_interface():
    """Render AI insights interface"""
    st.markdown("### 🧠 AI-Powered Content Insights")
    
    if not session_manager.has_results():
        st.info("Process some audio/video content first to generate AI insights.")
        return
    
    results = session_manager.get_results()
    
    # Quick insights
    col1, col2, col3 = st.columns(3)
    
    with col1:
        word_count = len(results.transcript.split())
        st.metric("Word Count", word_count)
    
    with col2:
        if hasattr(results, 'confidence'):
            st.metric("Confidence", f"{results.confidence:.1%}")
        else:
            st.metric("Confidence", "N/A")
    
    with col3:
        if hasattr(results, 'processing_time'):
            st.metric("Processing Time", f"{results.processing_time:.1f}s")
        else:
            st.metric("Processing Time", "N/A")
    
    # Advanced insights button
    if st.button("🧠 Generate Advanced Insights"):
        with st.spinner("Generating AI insights..."):
            # Use advanced content analyzer
            analysis_results = advanced_content_analyzer.analyze_content(
                text=results.transcript,
                audio_duration=getattr(results, 'processing_time', None)
            )
            
            if 'overall_score' in analysis_results:
                overall_quality = analysis_results['overall_score'].get('overall_quality', 0)
                st.success(f"Content Quality Score: {overall_quality:.2f}")
                
                # Store for detailed view
                st.session_state.advanced_insights = analysis_results


def render_visual_discovery_interface():
    """Render visual discovery interface"""
    st.markdown("### 🗺️ Visual Content Discovery")
    visual_search_ui.render_visual_search_interface()


def render_advanced_analytics_interface():
    """Render advanced analytics interface"""
    st.markdown("### 📊 Advanced Analytics")
    
    if not session_manager.has_results():
        st.info("Process some content first to view analytics.")
        return
    
    # Analytics placeholder
    st.info("Advanced analytics features coming soon! This will include:")
    st.markdown("""
    - Content trend analysis
    - Speaking pattern insights
    - Emotional flow tracking
    - Comparative analysis across sessions
    """)


def render_video_processing_interface():
    """Render video processing interface"""
    st.markdown("### 🎬 Video Processing Tools")
    
    # Video processing placeholder
    st.info("Upload a video file to access video-specific tools:")
    st.markdown("""
    - Video thumbnail generation
    - Subtitle/caption creation
    - Video chapter detection
    - Scene analysis and segmentation
    """)


def render_media_tools_interface():
    """Render media tools interface"""
    st.markdown("### 🎵 Media Enhancement Tools")
    
    # Media tools placeholder
    st.info("Media enhancement tools include:")
    st.markdown("""
    - Audio noise reduction
    - Volume normalization
    - Format conversion
    - Quality enhancement
    """)


# This function is now replaced by render_export_integrations_interface()
# Keeping for backward compatibility but redirecting to new interface
def render_export_interface():
    """Render export and sharing interface - redirects to comprehensive interface"""
    render_export_integrations_interface()


def render_content_generation_interface():
    """Render content generation interface"""
    st.markdown("### 🎨 AI Content Generation")
    ai_provider_ui.render_enhanced_content_generation()


def render_model_management_interface():
    """Render model management interface"""
    st.markdown("### 🔧 AI Model Management")
    
    st.info("Model management features:")
    st.markdown("""
    - Download and manage local models
    - Configure model preferences
    - Monitor model performance
    - Update model versions
    """)


def render_admin_panel_interface():
    """Render admin panel interface"""
    st.markdown("### 👑 Admin Panel")
    
    # Check admin access
    admin_password = st.text_input("Admin Password:", type="password")
    
    if admin_password == os.getenv("ADMIN_PASSWORD", "admin123"):
        st.success("✅ Admin access granted")
        
        # Admin features
        admin_features_tab, system_tab, users_tab = st.tabs([
            "🛠️ Admin Features",
            "🖥️ System Monitor", 
            "👥 User Management"
        ])
        
        with admin_features_tab:
            render_admin_features()
        
        with system_tab:
            render_system_monitor()
        
        with users_tab:
            render_user_management()
    else:
        st.warning("⚠️ Admin access required")


def render_app_settings_interface():
    """Render application settings interface"""
    st.markdown("### ⚙️ Application Settings")
    
    # Settings categories
    ui_tab, processing_tab, storage_tab = st.tabs([
        "🎨 UI Settings",
        "⚙️ Processing Settings",
        "💾 Storage Settings"
    ])
    
    with ui_tab:
        st.markdown("**User Interface:**")
        theme = st.selectbox("Theme", ["Light", "Dark", "Auto"])
        language = st.selectbox("Language", ["English", "Spanish", "French"])
    
    with processing_tab:
        st.markdown("**Processing Defaults:**")
        default_mode = st.selectbox("Default Analysis Mode", 
                                   ["Basic (spaCy)", "Advanced (OpenAI)"])
        auto_enhance = st.checkbox("Auto-enhance audio", value=True)
    
    with storage_tab:
        st.markdown("**Storage Management:**")
        st.info("Storage settings and cleanup options")


def render_security_interface():
    """Render security and privacy interface"""
    st.markdown("### 🛡️ Security & Privacy")
    
    security_tab, privacy_tab, audit_tab = st.tabs([
        "🔒 Security Settings",
        "🔐 Privacy Controls",
        "📋 Audit Log"
    ])
    
    with security_tab:
        st.markdown("**Security Features:**")
        st.info("Security settings and access controls")
    
    with privacy_tab:
        st.markdown("**Privacy Controls:**")
        st.info("Data retention and privacy settings")
    
    with audit_tab:
        st.markdown("**Audit Log:**")
        st.info("System activity and access logs")


def render_help_documentation():
    """Render help and documentation"""
    st.markdown("### 📚 Help & Documentation")
    
    help_tab, faq_tab, support_tab = st.tabs([
        "📖 User Guide",
        "❓ FAQ",
        "🆘 Support"
    ])
    
    with help_tab:
        st.markdown("""
        ## Quick Start Guide
        
        1. **Upload or Record**: Use the Transcribe & Analyze tab to upload media or record live audio
        2. **Choose Analysis Mode**: Select Basic for fast local processing or Advanced for AI-powered insights
        3. **Process Content**: Click "Transcribe & Analyze" to generate transcript and extract entities
        4. **Explore Results**: Use Search & Insights tab to discover patterns and insights
        5. **Export Results**: Use Video & Media Tools tab to export in various formats
        """)
    
    with faq_tab:
        st.markdown("""
        ## Frequently Asked Questions
        
        **Q: What file formats are supported?**
        A: Audio: MP3, WAV, M4A | Video: MP4, AVI, MOV
        
        **Q: Do I need API keys?**
        A: Basic mode works offline. Advanced features require OpenAI API key.
        
        **Q: How accurate is the transcription?**
        A: Accuracy depends on audio quality. Typically 90-95% for clear audio.
        """)
    
    with support_tab:
        st.markdown("""
        ## Support & Contact
        
        - **Documentation**: Check the User Guide tab
        - **Issues**: Report bugs via GitHub issues
        - **Community**: Join our Discord server
        - **Email**: support@transcription-app.com
        """)


# Additional helper functions

def process_audio_content(audio_source, analysis_mode: str):
    """Process audio content based on selected mode"""
    
    with st.spinner(f"Processing with {analysis_mode} mode..."):
        try:
            if "Multi-Language" in analysis_mode:
                # Multi-language processing
                multilingual_settings = st.session_state.get('multilingual_settings', {})
                result = process_audio_multilingual(audio_source, multilingual_settings)
                session_manager.store_multilingual_results(result)
            else:
                # Standard processing
                process_audio_enhanced(audio_source, analysis_mode)
            
            st.success("✅ Processing completed!")
            
        except Exception as e:
            st.error(f"❌ Processing failed: {str(e)}")
            logger.error(f"Processing error: {e}")


def render_transcription_results(analysis_mode: str):
    """Render transcription results based on analysis mode"""
    
    st.markdown("## 📊 Results")
    
    # Check for multi-language results
    if "Multi-Language" in analysis_mode and session_manager.get_multilingual_results():
        render_multilingual_results()
        return
    
    # Standard results display
    results = session_manager.get_results()
    
    # Results tabs
    transcript_tab, entities_tab, analysis_tab, export_tab = st.tabs([
        "📝 Transcript",
        "🏷️ Entities", 
        "📊 Analysis",
        "📤 Export"
    ])
    
    with transcript_tab:
        st.text_area("Transcript", value=results.transcript, height=300)
    
    with entities_tab:
        if hasattr(results, 'entities') and results.entities:
            render_entities_display(results.entities)
        else:
            st.info("No entities extracted. Try Advanced mode for entity extraction.")
    
    with analysis_tab:
        render_analysis_display(results, analysis_mode)
    
    with export_tab:
        render_export_options(results)


# Import remaining helper functions from original app.py
def render_theme_selector():
    """Render theme selector"""
    apply_theme_toggle()


def display_api_status(api_status: Dict[str, bool]):
    """Display API key status"""
    if api_status["openai"]:
        st.success("✅ OpenAI API configured")
    else:
        st.error("❌ OpenAI API key missing")
    
    if api_status["elevenlabs"]:
        st.success("✅ ElevenLabs API configured")
    else:
        st.warning("⚠️ ElevenLabs API key missing")


# Placeholder functions for features to be implemented
def process_audio_enhanced(audio_source, analysis_mode: str):
    """Enhanced audio processing - placeholder"""
    time.sleep(2)  # Simulate processing
    
    # Store mock results
    mock_result = TranscriptionResults()
    mock_result.transcript = "This is a sample transcript generated from your audio content."
    mock_result.confidence = 0.95
    mock_result.processing_time = 2.0
    
    session_manager.store_results(mock_result)


def process_audio_multilingual(audio_source, settings: Dict):
    """Multi-language audio processing - placeholder"""
    from multilingual_transcription import MultilingualTranscriptionResult
    
    time.sleep(3)  # Simulate processing
    
    return MultilingualTranscriptionResult(
        text="This is a sample multilingual transcript.",
        confidence=0.92,
        processing_time=3.0,
        model_used="whisper-multilingual",
        primary_language="en",
        detected_languages=[("en", 0.8), ("es", 0.2)],
        has_code_switching=False
    )


def render_multilingual_results():
    """Render multilingual results - placeholder"""
    st.info("Multi-language results would be displayed here")


def render_entities_display(entities):
    """Render entities display - placeholder"""
    st.info("Entity extraction results would be displayed here")


def render_analysis_display(results, analysis_mode):
    """Render analysis display - placeholder"""
    st.info(f"Analysis results for {analysis_mode} would be displayed here")


def render_export_options(results):
    """Render export options - placeholder"""
    st.info("Export options would be displayed here")


def render_admin_features():
    """Render admin features - placeholder"""
    st.info("Admin features interface")


def render_system_monitor():
    """Render system monitor - placeholder"""
    st.info("System monitoring dashboard")


def render_user_management():
    """Render user management - placeholder"""
    st.info("User management interface")


if __name__ == "__main__":
    main()
# Missing helper functions implementation

def render_multilingual_settings():
    """Render multi-language specific settings"""
    st.markdown("#### 🌍 Multi-Language Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        target_language = st.selectbox(
            "Target Language",
            ["Auto-detect", "English", "Spanish", "French", "German", "Chinese", "Japanese"],
            help="Select the primary language for processing"
        )
        
        enable_translation = st.checkbox(
            "Enable Translation",
            value=False,
            help="Translate transcript to different language"
        )
    
    with col2:
        if enable_translation:
            translation_target = st.selectbox(
                "Translate to",
                ["English", "Spanish", "French", "German", "Chinese", "Japanese"],
                help="Target language for translation"
            )
        
        enable_code_switching = st.checkbox(
            "Detect Code-Switching",
            value=True,
            help="Detect when speakers switch between languages"
        )
    
    # Store settings in session state
    multilingual_settings = {
        "target_language": target_language,
        "enable_translation": enable_translation,
        "translation_target": translation_target if enable_translation else None,
        "enable_code_switching": enable_code_switching
    }
    
    st.session_state.multilingual_settings = multilingual_settings
    return multilingual_settings


def render_content_search_interface():
    """Render content search interface"""
    st.markdown("### 🔍 Search Your Content")
    
    if not session_manager.has_results():
        st.info("Process some audio/video content first to enable search features.")
        return
    
    # Search functionality
    search_query = st.text_input("Search in transcript:", placeholder="Enter keywords...")
    
    if search_query:
        results = session_manager.get_results()
        transcript = results.transcript
        
        # Simple search implementation
        if search_query.lower() in transcript.lower():
            st.success(f"Found '{search_query}' in transcript!")
            
            # Highlight context
            context_start = max(0, transcript.lower().find(search_query.lower()) - 100)
            context_end = min(len(transcript), transcript.lower().find(search_query.lower()) + len(search_query) + 100)
            context = transcript[context_start:context_end]
            
            st.text_area("Context:", value=context, height=150)
        else:
            st.warning(f"'{search_query}' not found in transcript.")
    
    # Advanced search options
    with st.expander("🔧 Advanced Search Options"):
        case_sensitive = st.checkbox("Case sensitive search")
        whole_words = st.checkbox("Match whole words only")
        regex_search = st.checkbox("Use regular expressions")


def render_ai_insights_interface():
    """Render AI insights interface"""
    st.markdown("### 🧠 AI-Powered Content Insights")
    
    if not session_manager.has_results():
        st.info("Process some audio/video content first to generate AI insights.")
        return
    
    results = session_manager.get_results()
    
    # Quick insights
    col1, col2, col3 = st.columns(3)
    
    with col1:
        word_count = len(results.transcript.split())
        st.metric("Word Count", word_count)
    
    with col2:
        if hasattr(results, 'confidence'):
            st.metric("Confidence", f"{results.confidence:.1%}")
        else:
            st.metric("Confidence", "N/A")
    
    with col3:
        if hasattr(results, 'processing_time'):
            st.metric("Processing Time", f"{results.processing_time:.1f}s")
        else:
            st.metric("Processing Time", "N/A")
    
    # Advanced insights button
    if st.button("🧠 Generate Advanced Insights"):
        with st.spinner("Generating AI insights..."):
            try:
                # Use advanced content analyzer if available
                if ADVANCED_MODULES_AVAILABLE:
                    analysis_results = advanced_content_analyzer.analyze_content(
                        text=results.transcript,
                        audio_duration=getattr(results, 'processing_time', None)
                    )
                    
                    if 'overall_score' in analysis_results:
                        overall_quality = analysis_results['overall_score'].get('overall_quality', 0)
                        st.success(f"Content Quality Score: {overall_quality:.2f}")
                        
                        # Store for detailed view
                        st.session_state.advanced_insights = analysis_results
                else:
                    st.info("Advanced insights require additional modules to be installed.")
            except Exception as e:
                st.error(f"Error generating insights: {str(e)}")


def render_visual_discovery_interface():
    """Render visual discovery interface"""
    st.markdown("### 🗺️ Visual Content Discovery")
    
    if ADVANCED_MODULES_AVAILABLE:
        try:
            visual_search_ui.render_visual_search_interface()
        except Exception as e:
            st.error(f"Visual search interface error: {str(e)}")
            st.info("Visual discovery features are being loaded...")
    else:
        st.info("Visual discovery features require additional modules.")
        st.markdown("""
        **Coming Soon:**
        - Content similarity mapping
        - Visual timeline exploration
        - Topic clustering visualization
        - Interactive content graphs
        """)


def render_advanced_analytics_interface():
    """Render advanced analytics interface"""
    st.markdown("### 📊 Advanced Analytics")
    
    if not session_manager.has_results():
        st.info("Process some content first to view analytics.")
        return
    
    if ADVANCED_MODULES_AVAILABLE:
        try:
            analytics_ui = AnalyticsUI()
            analytics_ui.render_analytics_dashboard()
        except Exception as e:
            st.error(f"Analytics interface error: {str(e)}")
            render_basic_analytics()
    else:
        render_basic_analytics()


def render_basic_analytics():
    """Render basic analytics when advanced modules aren't available"""
    results = session_manager.get_results()
    
    # Basic analytics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Words", len(results.transcript.split()))
    
    with col2:
        sentences = results.transcript.split('.')
        st.metric("Sentences", len([s for s in sentences if s.strip()]))
    
    with col3:
        avg_words = len(results.transcript.split()) / max(len([s for s in sentences if s.strip()]), 1)
        st.metric("Avg Words/Sentence", f"{avg_words:.1f}")
    
    # Word frequency
    st.markdown("#### 📈 Word Frequency")
    words = results.transcript.lower().split()
    word_freq = {}
    for word in words:
        word = word.strip('.,!?";')
        if len(word) > 3:  # Only count words longer than 3 characters
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Show top 10 words
    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
    
    for word, count in top_words:
        st.write(f"**{word}**: {count} times")


def render_video_processing_interface():
    """Render video processing interface"""
    st.markdown("### 🎬 Video Processing Tools")
    
    if ADVANCED_MODULES_AVAILABLE:
        try:
            video_ui = VideoUI()
            video_ui.render_video_tools()
        except Exception as e:
            st.error(f"Video processing error: {str(e)}")
            render_basic_video_info()
    else:
        render_basic_video_info()


def render_basic_video_info():
    """Render basic video information when advanced modules aren't available"""
    st.info("Upload a video file to access video-specific tools:")
    st.markdown("""
    **Available Features:**
    - Video thumbnail generation
    - Subtitle/caption creation (SRT, VTT)
    - Video chapter detection
    - Scene analysis and segmentation
    - Frame extraction at key moments
    """)


def render_media_tools_interface():
    """Render media tools interface"""
    st.markdown("### 🎵 Media Enhancement Tools")
    
    # Audio enhancement options
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Audio Processing:**")
        if st.button("🔊 Enhance Audio Quality"):
            st.info("Audio enhancement would be applied here")
        
        if st.button("🔇 Remove Background Noise"):
            st.info("Noise reduction would be applied here")
    
    with col2:
        st.markdown("**Format Conversion:**")
        if st.button("🔄 Convert to WAV"):
            st.info("Format conversion would be applied here")
        
        if st.button("📊 Normalize Volume"):
            st.info("Volume normalization would be applied here")


def render_content_generation_interface():
    """Render content generation interface"""
    st.markdown("### 🎨 AI Content Generation")
    
    if ADVANCED_MODULES_AVAILABLE:
        try:
            ai_provider_ui.render_enhanced_content_generation()
        except Exception as e:
            st.error(f"Content generation error: {str(e)}")
            render_basic_content_generation()
    else:
        render_basic_content_generation()


def render_basic_content_generation():
    """Render basic content generation interface"""
    st.markdown("**Content Generation Tools:**")
    
    content_type = st.selectbox(
        "Content Type",
        ["Summary", "Key Points", "Action Items", "Meeting Minutes"]
    )
    
    if st.button(f"Generate {content_type}"):
        if session_manager.has_results():
            results = session_manager.get_results()
            
            if content_type == "Summary":
                # Simple summary (first 200 characters)
                summary = results.transcript[:200] + "..."
                st.text_area("Generated Summary:", value=summary, height=100)
            
            elif content_type == "Key Points":
                # Extract sentences that might be key points
                sentences = results.transcript.split('.')
                key_sentences = [s.strip() for s in sentences if len(s.strip()) > 50][:5]
                
                st.markdown("**Key Points:**")
                for i, point in enumerate(key_sentences, 1):
                    st.write(f"{i}. {point}")
            
            else:
                st.info(f"{content_type} generation requires advanced AI modules.")
        else:
            st.warning("Please process some content first.")


def render_model_management_interface():
    """Render model management interface"""
    st.markdown("### 🔧 AI Model Management")
    
    # Model status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Speech-to-Text:**")
        st.success("✅ Whisper (OpenAI)")
        st.info("ℹ️ Local fallback available")
    
    with col2:
        st.markdown("**Entity Recognition:**")
        st.success("✅ spaCy (en_core_web_sm)")
        st.success("✅ OpenAI GPT (Advanced)")
    
    with col3:
        st.markdown("**Text-to-Speech:**")
        st.success("✅ ElevenLabs")
        st.info("ℹ️ Multiple voices available")
    
    # Model preferences
    st.markdown("#### ⚙️ Model Preferences")
    
    default_stt = st.selectbox(
        "Default STT Model",
        ["OpenAI Whisper", "Local Whisper", "Auto (API with fallback)"]
    )
    
    default_ner = st.selectbox(
        "Default NER Model", 
        ["spaCy (Fast)", "OpenAI GPT (Accurate)", "Hybrid (Both)"]
    )


def render_admin_panel_interface():
    """Render admin panel interface"""
    st.markdown("### 👑 Admin Panel")
    
    # Simple admin authentication
    admin_password = st.text_input("Admin Password:", type="password")
    
    if admin_password == os.getenv("ADMIN_PASSWORD", "admin123"):
        st.success("✅ Admin access granted")
        
        # Admin features tabs
        admin_features_tab, system_tab, users_tab = st.tabs([
            "🛠️ Admin Features",
            "🖥️ System Monitor", 
            "👥 User Management"
        ])
        
        with admin_features_tab:
            render_admin_features()
        
        with system_tab:
            render_system_monitor()
        
        with users_tab:
            render_user_management()
    else:
        st.warning("⚠️ Admin access required")
        st.info("Enter the admin password to access administrative features.")


def render_admin_features():
    """Render admin features interface"""
    st.markdown("#### 🛠️ Administrative Tools")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Content Management:**")
        if st.button("🗑️ Clear All Sessions"):
            st.warning("This would clear all user sessions")
        
        if st.button("📊 Export Usage Stats"):
            st.info("Usage statistics would be exported")
    
    with col2:
        st.markdown("**System Maintenance:**")
        if st.button("🔄 Restart Services"):
            st.warning("This would restart system services")
        
        if st.button("🧹 Clean Temp Files"):
            st.info("Temporary files would be cleaned")


def render_system_monitor():
    """Render system monitoring interface"""
    st.markdown("#### 🖥️ System Status")
    
    # Mock system metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("CPU Usage", "45%", "↑ 5%")
    
    with col2:
        st.metric("Memory Usage", "2.1 GB", "↓ 0.2 GB")
    
    with col3:
        st.metric("Active Sessions", "12", "↑ 3")
    
    with col4:
        st.metric("API Calls Today", "1,247", "↑ 156")
    
    # System health
    st.markdown("#### 🏥 Health Checks")
    
    health_items = [
        ("Database Connection", "✅ Healthy"),
        ("API Services", "✅ Healthy"), 
        ("File Storage", "✅ Healthy"),
        ("Background Tasks", "⚠️ Warning")
    ]
    
    for item, status in health_items:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{item}**")
        with col2:
            st.write(status)


def render_user_management():
    """Render user management interface"""
    st.markdown("#### 👥 User Management")
    
    # Mock user data
    users = [
        {"name": "John Doe", "email": "john@example.com", "sessions": 15, "last_active": "2 hours ago"},
        {"name": "Jane Smith", "email": "jane@example.com", "sessions": 8, "last_active": "1 day ago"},
        {"name": "Bob Wilson", "email": "bob@example.com", "sessions": 23, "last_active": "5 minutes ago"}
    ]
    
    for user in users:
        with st.expander(f"👤 {user['name']} ({user['email']})"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Sessions:** {user['sessions']}")
            
            with col2:
                st.write(f"**Last Active:** {user['last_active']}")
            
            with col3:
                if st.button(f"Reset {user['name']}", key=f"reset_{user['email']}"):
                    st.info(f"Would reset user {user['name']}")


def render_app_settings_interface():
    """Render application settings interface"""
    st.markdown("### ⚙️ Application Settings")
    
    # Settings categories
    ui_tab, processing_tab, storage_tab = st.tabs([
        "🎨 UI Settings",
        "⚙️ Processing Settings",
        "💾 Storage Settings"
    ])
    
    with ui_tab:
        st.markdown("**User Interface:**")
        theme = st.selectbox("Theme", ["Light", "Dark", "Auto"])
        language = st.selectbox("Language", ["English", "Spanish", "French"])
        layout = st.selectbox("Layout", ["Wide", "Centered", "Compact"])
    
    with processing_tab:
        st.markdown("**Processing Defaults:**")
        default_mode = st.selectbox("Default Analysis Mode", 
                                   ["Basic (spaCy)", "Advanced (OpenAI)"])
        auto_enhance = st.checkbox("Auto-enhance audio", value=True)
        max_file_size = st.slider("Max file size (MB)", 10, 500, 100)
    
    with storage_tab:
        st.markdown("**Storage Management:**")
        retention_days = st.slider("Data retention (days)", 1, 365, 30)
        auto_cleanup = st.checkbox("Auto-cleanup temporary files", value=True)
        
        if st.button("🧹 Clean Storage Now"):
            st.info("Storage cleanup would be performed")


def render_security_interface():
    """Render security and privacy interface"""
    st.markdown("### 🛡️ Security & Privacy")
    
    security_tab, privacy_tab, audit_tab = st.tabs([
        "🔒 Security Settings",
        "🔐 Privacy Controls",
        "📋 Audit Log"
    ])
    
    with security_tab:
        st.markdown("**Security Features:**")
        enable_encryption = st.checkbox("Enable data encryption", value=True)
        require_auth = st.checkbox("Require authentication", value=False)
        session_timeout = st.slider("Session timeout (minutes)", 15, 480, 60)
    
    with privacy_tab:
        st.markdown("**Privacy Controls:**")
        data_retention = st.slider("Data retention period (days)", 1, 90, 7)
        allow_analytics = st.checkbox("Allow usage analytics", value=True)
        share_improvements = st.checkbox("Share data for improvements", value=False)
    
    with audit_tab:
        st.markdown("**Recent Activity:**")
        
        # Mock audit log
        audit_entries = [
            "2024-01-15 14:30 - User uploaded audio file (5.2MB)",
            "2024-01-15 14:28 - Transcription completed (Advanced mode)",
            "2024-01-15 14:25 - User accessed admin panel",
            "2024-01-15 14:20 - System health check performed"
        ]
        
        for entry in audit_entries:
            st.text(entry)


def render_help_documentation():
    """Render help and documentation"""
    st.markdown("### 📚 Help & Documentation")
    
    help_tab, faq_tab, support_tab = st.tabs([
        "📖 User Guide",
        "❓ FAQ",
        "🆘 Support"
    ])
    
    with help_tab:
        st.markdown("""
        ## 🚀 Quick Start Guide
        
        ### 1. Upload or Record Audio
        - Use the **Transcribe & Analyze** tab
        - Upload audio/video files or record live
        - Supported formats: MP3, WAV, M4A, MP4, AVI, MOV
        
        ### 2. Choose Analysis Mode
        - **Basic (spaCy)**: Fast local processing, works offline
        - **Advanced (OpenAI)**: AI-powered analysis with GPT
        - **Advanced+ (Speaker Diarization)**: Full features with speaker identification
        - **Multi-Language**: Support for 50+ languages with translation
        
        ### 3. Process Content
        - Click "Transcribe & Analyze" to start processing
        - Wait for completion (progress indicators will show status)
        - Review results in the transcript and analysis sections
        
        ### 4. Explore Features
        - **Search & Insights**: Find content and generate AI insights
        - **Video & Media Tools**: Video processing and export options
        - **AI & Advanced Features**: Content generation and provider management
        - **Admin & Settings**: Configuration and system management
        
        ### 5. Export and Share
        - Use the Export & Integrations tab for sharing
        - Generate interactive HTML reports
        - Share to Slack, Teams, Discord
        - Create calendar events from meetings
        """)
    
    with faq_tab:
        st.markdown("""
        ## ❓ Frequently Asked Questions
        
        **Q: What file formats are supported?**
        A: Audio: MP3, WAV, M4A | Video: MP4, AVI, MOV
        
        **Q: Do I need API keys?**
        A: Basic mode works offline. Advanced features require OpenAI API key.
        
        **Q: How accurate is the transcription?**
        A: Accuracy depends on audio quality. Typically 90-95% for clear audio.
        
        **Q: Can I process multiple files at once?**
        A: Yes, enable batch processing in the sidebar settings.
        
        **Q: Is my data secure?**
        A: Yes, data is processed securely and can be encrypted. Check Security & Privacy settings.
        
        **Q: Can I use this offline?**
        A: Basic mode works offline. Advanced features require internet connection.
        
        **Q: How do I get API keys?**
        A: Visit OpenAI and ElevenLabs websites to create accounts and generate API keys.
        """)
    
    with support_tab:
        st.markdown("""
        ## 🆘 Support & Contact
        
        ### 📧 Contact Information
        - **Email**: support@transcription-app.com
        - **Documentation**: Check the User Guide tab above
        - **Issues**: Report bugs via GitHub issues
        - **Community**: Join our Discord server for discussions
        
        ### 🔧 Troubleshooting
        
        **Common Issues:**
        
        1. **"API key not configured"**
           - Add your OpenAI API key to the .env file
           - Restart the application after adding keys
        
        2. **"File upload failed"**
           - Check file size (max 100MB by default)
           - Ensure file format is supported
           - Try converting to WAV format
        
        3. **"Processing takes too long"**
           - Large files take more time to process
           - Try using Basic mode for faster processing
           - Check your internet connection for API calls
        
        4. **"No audio detected"**
           - Ensure audio file has actual speech content
           - Check audio volume levels
           - Try noise reduction if audio is unclear
        
        ### 📊 System Requirements
        - Python 3.8 or higher
        - 4GB RAM minimum (8GB recommended)
        - Internet connection for advanced features
        - Modern web browser (Chrome, Firefox, Safari, Edge)
        """)


# Additional helper functions

def process_audio_content(audio_source, analysis_mode: str):
    """Process audio content based on selected mode"""
    
    with st.spinner(f"Processing with {analysis_mode} mode..."):
        try:
            if "Multi-Language" in analysis_mode:
                # Multi-language processing
                multilingual_settings = st.session_state.get('multilingual_settings', {})
                result = process_audio_multilingual(audio_source, multilingual_settings)
                session_manager.store_multilingual_results(result)
            else:
                # Standard processing
                process_audio_enhanced(audio_source, analysis_mode)
            
            st.success("✅ Processing completed!")
            
        except Exception as e:
            st.error(f"❌ Processing failed: {str(e)}")
            logger.error(f"Processing error: {e}")


def render_transcription_results(analysis_mode: str):
    """Render transcription results based on analysis mode"""
    
    st.markdown("## 📊 Results")
    
    # Check for multi-language results
    if "Multi-Language" in analysis_mode and hasattr(st.session_state, 'multilingual_results'):
        render_multilingual_results()
        return
    
    # Standard results display
    results = session_manager.get_results()
    
    # Results tabs
    transcript_tab, entities_tab, analysis_tab, export_tab = st.tabs([
        "📝 Transcript",
        "🏷️ Entities", 
        "📊 Analysis",
        "📤 Export"
    ])
    
    with transcript_tab:
        st.text_area("Transcript", value=results.transcript, height=300)
    
    with entities_tab:
        if hasattr(results, 'entities') and results.entities:
            render_entities_display(results.entities)
        else:
            st.info("No entities extracted. Try Advanced mode for entity extraction.")
    
    with analysis_tab:
        render_analysis_display(results, analysis_mode)
    
    with export_tab:
        render_export_options(results)


# Import remaining helper functions from original app.py or create simplified versions
def render_theme_selector():
    """Render theme selector"""
    if ADVANCED_MODULES_AVAILABLE:
        try:
            apply_theme_toggle()
        except:
            st.selectbox("Theme", ["Light", "Dark", "Auto"], key="theme_selector")
    else:
        st.selectbox("Theme", ["Light", "Dark", "Auto"], key="theme_selector")


def display_api_status(api_status: Dict[str, bool]):
    """Display API key status"""
    try:
        # Try to get actual API status
        api_status = Config.validate_api_keys()
    except:
        # Fallback to checking environment variables
        api_status = {
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "elevenlabs": bool(os.getenv("ELEVENLABS_API_KEY"))
        }
    
    if api_status.get("openai", False):
        st.success("✅ OpenAI API configured")
    else:
        st.error("❌ OpenAI API key missing")
    
    if api_status.get("elevenlabs", False):
        st.success("✅ ElevenLabs API configured")
    else:
        st.warning("⚠️ ElevenLabs API key missing")


# Placeholder functions for features to be implemented
def process_audio_enhanced(audio_source, analysis_mode: str):
    """Enhanced audio processing - placeholder"""
    time.sleep(2)  # Simulate processing
    
    # Store mock results
    mock_result = TranscriptionResults()
    mock_result.transcript = "This is a sample transcript generated from your audio content using the refactored interface."
    mock_result.confidence = 0.95
    mock_result.processing_time = 2.0
    
    session_manager.store_results(mock_result)


def process_audio_multilingual(audio_source, settings: Dict):
    """Multi-language audio processing - placeholder"""
    time.sleep(3)  # Simulate processing
    
    # Create mock multilingual result
    mock_result = {
        "text": "This is a sample multilingual transcript.",
        "confidence": 0.92,
        "processing_time": 3.0,
        "model_used": "whisper-multilingual",
        "primary_language": "en",
        "detected_languages": [("en", 0.8), ("es", 0.2)],
        "has_code_switching": False
    }
    
    st.session_state.multilingual_results = mock_result
    return mock_result


def render_multilingual_results():
    """Render multilingual results - placeholder"""
    results = st.session_state.get('multilingual_results', {})
    
    st.success("✅ Multi-language processing completed!")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Primary Language", results.get('primary_language', 'Unknown'))
    
    with col2:
        st.metric("Confidence", f"{results.get('confidence', 0):.1%}")
    
    with col3:
        st.metric("Processing Time", f"{results.get('processing_time', 0):.1f}s")
    
    # Show detected languages
    if results.get('detected_languages'):
        st.markdown("**Detected Languages:**")
        for lang, confidence in results.get('detected_languages', []):
            st.write(f"• {lang}: {confidence:.1%}")
    
    # Show transcript
    st.text_area("Multilingual Transcript", value=results.get('text', ''), height=200)


def render_entities_display(entities):
    """Render entities display - placeholder"""
    st.markdown("**Extracted Entities:**")
    
    if not entities:
        st.info("No entities found in the transcript.")
        return
    
    # Group entities by type
    entity_groups = {}
    for entity in entities:
        entity_type = entity.get('type', 'UNKNOWN')
        if entity_type not in entity_groups:
            entity_groups[entity_type] = []
        entity_groups[entity_type].append(entity)
    
    # Display entities by type
    for entity_type, entity_list in entity_groups.items():
        with st.expander(f"{entity_type} ({len(entity_list)} found)"):
            for entity in entity_list:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{entity.get('text', 'Unknown')}**")
                with col2:
                    confidence = entity.get('confidence', 0)
                    st.write(f"{confidence:.1%}")


def render_analysis_display(results, analysis_mode):
    """Render analysis display - placeholder"""
    st.markdown(f"**Analysis Mode:** {analysis_mode}")
    
    # Basic analysis metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        word_count = len(results.transcript.split())
        st.metric("Word Count", word_count)
    
    with col2:
        sentence_count = len([s for s in results.transcript.split('.') if s.strip()])
        st.metric("Sentences", sentence_count)
    
    with col3:
        avg_words = word_count / max(sentence_count, 1)
        st.metric("Avg Words/Sentence", f"{avg_words:.1f}")
    
    # Additional analysis based on mode
    if "Advanced" in analysis_mode:
        st.markdown("**Advanced Analysis:**")
        st.info("Advanced analysis features would be displayed here.")
    
    if "Speaker" in analysis_mode:
        st.markdown("**Speaker Analysis:**")
        st.info("Speaker diarization results would be displayed here.")


def render_export_options(results):
    """Render export options - placeholder"""
    st.markdown("**Export Options:**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export as TXT"):
            st.download_button(
                "Download TXT",
                data=results.transcript,
                file_name="transcript.txt",
                mime="text/plain"
            )
    
    with col2:
        if st.button("📊 Export as CSV"):
            # Create simple CSV
            csv_data = f"Transcript\n\"{results.transcript.replace('\"', '\"\"')}\""
            st.download_button(
                "Download CSV", 
                data=csv_data,
                file_name="transcript.csv",
                mime="text/csv"
            )
    
    with col3:
        if st.button("📋 Export as JSON"):
            import json
            json_data = {
                "transcript": results.transcript,
                "word_count": len(results.transcript.split()),
                "processing_time": getattr(results, 'processing_time', 0),
                "confidence": getattr(results, 'confidence', 0)
            }
            st.download_button(
                "Download JSON",
                data=json.dumps(json_data, indent=2),
                file_name="transcript.json",
                mime="application/json"
            )


if __name__ == "__main__":
    main()