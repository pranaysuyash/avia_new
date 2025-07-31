#!/usr/bin/env python3
"""
Audio/Video Transcription and Entity Extraction App with Authentication
Enhanced version with user authentication and collaboration features
"""

import streamlit as st
import os
import logging
import tempfile
import time
from typing import Optional, Dict, Any

# Import authentication components
from auth import render_auth_page, require_authentication, get_current_user, render_user_menu, check_authentication
from database import init_db

# Import sharing components
from sharing import render_share_dialog, render_public_share_page, render_share_management_page

# Import annotation components
from annotations import AnnotationManager, render_annotation_ui, render_annotation_sidebar

# Import versioning components
from versioning import VersionManager, render_version_history, render_edit_transcript_dialog

# Import notification components
from notifications import NotificationManager, render_notification_bell, render_notification_panel

# Import enhanced export components
from export_enhanced import ExportManager

# Import team components
from teams import TeamManager, ResourceManager, render_team_dashboard, render_team_management, render_team_settings

# Import localization components
from localization import get_text, set_language, get_current_language, render_language_selector
from localization.translations import TRANSLATIONS
from localization.localized_ui import (
    localized_header, localized_button, localized_text_input,
    render_localized_page_header, localized_info, localized_error,
    localized_success, localized_warning, localized_tab
)

# Import segmentation components
from segmentation import SegmentManager, render_segmentation_view

# Import tagging components
from tagging import TagManager, render_tagging_view, MockAIProvider

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

# Setup logging and configuration
Config.setup_logging()
logger = logging.getLogger(__name__)

# Initialize database
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")

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

def handle_special_routes():
    """Handle special routes including health checks and share links"""
    # Check for special routes via query parameters
    query_params = st.experimental_get_query_params()
    
    # Handle share links first (before authentication)
    if 'share' in query_params:
        share_token = query_params.get('share', [None])[0]
        if share_token:
            render_public_share_page(share_token)
            st.stop()
    
    elif 'health' in query_params:
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
    """Main application logic with authentication"""
    
    # Handle special routes (share links, health checks)
    handle_special_routes()
    
    # Check authentication
    if not check_authentication():
        render_auth_page()
        return
    
    # Get current user
    current_user = get_current_user()
    if not current_user:
        st.error("Authentication error. Please log in again.")
        render_auth_page()
        return
    
    # Apply localization settings
    render_localized_page_header()
    
    # Header with user info
    col1, col2, col3, col4 = st.columns([2, 3, 1, 1])
    with col1:
        st.title(f"🎵 {get_text('app.title')}")
    with col2:
        welcome_text = get_text('message.welcome')
        st.markdown(f"<div style='text-align: center; padding-top: 20px;'>{welcome_text}, **{current_user.username}**!</div>", unsafe_allow_html=True)
    with col3:
        # Notification bell
        st.markdown("<div style='text-align: center; padding-top: 15px;'>", unsafe_allow_html=True)
        from database.models import get_db_session
        notification_session = get_db_session()
        notification_manager = NotificationManager(notification_session)
        render_notification_bell(notification_manager, current_user)
        st.markdown("</div>", unsafe_allow_html=True)
    with col4:
        st.markdown("<div style='text-align: right; padding-top: 15px;'>", unsafe_allow_html=True)
        if localized_button("auth.logout", key="header_logout_btn"):
            from auth.auth_ui import logout_user
            logout_user()
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Show notification panel if bell clicked
    if st.session_state.get('show_notifications', False):
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                render_notification_panel(notification_manager, current_user)
            with col2:
                if st.button("✖️ Close", key="close_notifications"):
                    st.session_state.show_notifications = False
                    st.rerun()
    
    # Render user menu in sidebar
    render_user_menu()
    
    # Main sidebar for app navigation
    with st.sidebar:
        st.header("Navigation")
        
        # Mode selection with localization
        mode_options = [
            "Transcription & Analysis", 
            "Batch Processing", 
            "Admin Panel", 
            "My Transcripts", 
            "Team Workspaces", 
            "Manage Shares", 
            "Notifications"
        ]
        
        mode_keys = [
            'nav.transcription',
            'nav.batch',
            'nav.admin',
            'nav.my_transcripts',
            'nav.teams',
            'nav.shares',
            'nav.notifications'
        ]
        
        localized_options = [get_text(key) for key in mode_keys]
        
        selected_mode = st.radio(
            get_text('nav.select_mode') if 'nav.select_mode' in TRANSLATIONS else "Select Mode",
            options=localized_options,
            help="Choose the application mode"
        )
        
        # Get the actual mode value
        mode_index = localized_options.index(selected_mode)
        mode = mode_options[mode_index]
        
        # Processing options for transcription mode
        if mode == "Transcription & Analysis":
            st.header("Processing Options")
            
            analysis_mode = st.selectbox(
                "Analysis Mode",
                ["Basic (spaCy)", "Advanced (OpenAI)", "Advanced+ (Speaker Diarization)"],
                index=session_manager.get_preferences().preferred_analysis_mode,
                help="Choose between local or AI-powered entity extraction"
            )
            
            # Update user preference
            if analysis_mode != session_manager.get_preferences().preferred_analysis_mode:
                session_manager.update_preference('preferred_analysis_mode', analysis_mode)
            
            # Show advanced options
            if "Advanced" in analysis_mode:
                render_advanced_processing_options()
        
        # Environment status
        with st.expander("⚙️ Configuration Status", expanded=False):
            print_configuration_status()
        
        # Tips and guidance
        if mode == "Transcription & Analysis":
            show_processing_tips()
        elif mode == "Batch Processing":
            st.info("💡 Process multiple files simultaneously with progress tracking")
    
    # Main content area
    if mode == "Transcription & Analysis":
        render_transcription_mode(analysis_mode, current_user)
    elif mode == "Batch Processing":
        render_batch_interface(analysis_mode)
    elif mode == "Admin Panel":
        render_admin_panel(current_user)
    elif mode == "My Transcripts":
        render_user_transcripts(current_user)
    elif mode == "Team Workspaces":
        render_team_mode(current_user)
    elif mode == "Manage Shares":
        render_share_management_page()
    elif mode == "Notifications":
        render_notifications_mode(current_user)
    
    # Error display
    if session_manager.has_error():
        error_container = st.container()
        with error_container:
            user_message = create_user_error_message(
                session_manager.error_object if hasattr(session_manager, 'error_object') else None
            )
            st.error(user_message)
            
            if st.button("Clear Error"):
                session_manager.clear_error()
                st.rerun()

@require_authentication
def render_transcription_mode(analysis_mode: str, current_user):
    """Render the main transcription interface"""
    
    st.header("Upload Audio/Video File")
    
    # Team selection
    with st.expander("🏢 Team Settings", expanded=False):
        from database.models import get_db_session
        session = get_db_session()
        team_manager = TeamManager(session)
        
        teams = team_manager.get_user_teams(current_user.id)
        team_options = {"Personal (no team)": None}
        team_options.update({team.name: team.id for team in teams})
        
        selected_team_name = st.selectbox(
            "Save transcript to:",
            options=list(team_options.keys()),
            help="Choose whether to save this transcript to a team workspace or keep it personal"
        )
        
        selected_team_id = team_options[selected_team_name]
        st.session_state.selected_team_id = selected_team_id
        
        if selected_team_id:
            st.info(f"📋 Transcript will be saved to team: **{selected_team_name}**")
        else:
            st.info("📄 Transcript will be saved to your personal library")
    
    # File uploader with enhancements
    uploaded_file = enhanced_file_uploader(
        "Choose an audio or video file",
        type=["mp3", "wav", "mp4", "m4a"],
        help=f"Maximum file size: {utils.get_file_size_limit()}MB"
    )
    
    if uploaded_file is not None:
        # File validation
        is_valid, message = show_file_validation_feedback(uploaded_file)
        
        if is_valid:
            # Process button
            if st.button("🚀 Process File", type="primary"):
                process_uploaded_file(uploaded_file, analysis_mode, current_user)
        else:
            st.error(message)
    
    # Display results if available
    if session_manager.has_results():
        st.markdown("---")
        st.header("📊 Results")
        
        # Results tabs - add version history if transcript is saved
        results = session_manager.get_results()
        
        if hasattr(results, 'transcript_id') and results.transcript_id:
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["📝 Transcript", "📑 Segments", "🏷️ Tags", "🔍 Entities", "📊 Analysis", "🎤 Audio", "📚 History"])
        else:
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📝 Transcript", "📑 Segments", "🏷️ Tags", "🔍 Entities", "📊 Analysis", "🎤 Audio"])
        
        with tab1:
            render_transcript_tab(results)
        
        with tab2:
            render_segments_tab(results)
        
        with tab3:
            render_tags_tab(results)
        
        with tab4:
            render_entities_tab(results)
        
        with tab5:
            render_analysis_tab(results, analysis_mode)
        
        with tab6:
            render_audio_tab(results)
        
        # Version history tab (if available)
        if hasattr(results, 'transcript_id') and results.transcript_id:
            with tab7:
                from database.models import get_db_session
                session = get_db_session()
                version_manager = VersionManager(session)
                render_version_history(results.transcript_id, version_manager, current_user)
        
        # Export options
        st.markdown("---")
        render_export_options(results, current_user)

def process_uploaded_file(uploaded_file, analysis_mode: str, current_user):
    """Process the uploaded file with authentication context"""
    
    try:
        # Start processing
        session_manager.start_processing("Initializing...")
        
        # Create temporary file
        temp_dir = utils.ensure_temp_directory()
        temp_path = os.path.join(temp_dir, f"upload_{utils.get_timestamp()}_{uploaded_file.name}")
        
        # Save uploaded file
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.read())
        
        # Update file info
        session_manager.update_file_info(
            name=uploaded_file.name,
            size_bytes=uploaded_file.size,
            format=uploaded_file.name.split('.')[-1].lower()
        )
        
        # Create processing steps
        if "Advanced+" in analysis_mode:
            steps = create_admin_processing_steps()
        else:
            steps = create_processing_steps(use_api="Advanced" in analysis_mode)
        
        with progress_context(steps) as progress_callback:
            if "Advanced+" in analysis_mode:
                # Use advanced processing
                result = process_audio_with_advanced_features(
                    temp_path,
                    progress_callback,
                    options=st.session_state.get('advanced_options', {})
                )
                
                # Store advanced result
                st.session_state.advanced_transcription_state.advanced_result = result
                
                # Create TranscriptionResults from advanced result
                results = TranscriptionResults(
                    transcript=result.transcript,
                    entities=result.entities,
                    summary=getattr(result, 'summary', ''),
                    confidence=result.confidence,
                    processing_time=result.processing_time,
                    model_used=result.model,
                    language=result.language,
                    word_count=len(result.transcript.split()) if result.transcript else 0
                )
            else:
                # Standard processing
                start_time = time.time()
                
                # Media processing
                progress_callback(1, "Processing media file...")
                audio_path = temp_path
                if uploaded_file.name.lower().endswith(('.mp4', '.m4a')):
                    audio_path = media.extract_audio(temp_path)
                
                # Transcription
                progress_callback(2, "Transcribing audio...")
                use_api = "Advanced" in analysis_mode
                transcript = stt.transcribe(audio_path, use_api=use_api)
                
                if not transcript:
                    raise TranscriptionError("Failed to generate transcript")
                
                # Entity extraction
                progress_callback(3, "Extracting entities...")
                entities = {}
                summary = ""
                
                if analysis_mode == "Basic (spaCy)":
                    entities = ner_basic.extract_entities(transcript)
                elif "Advanced" in analysis_mode:
                    entities, summary = ner_advanced.extract_entities_advanced(transcript)
                
                # Create results
                processing_time = time.time() - start_time
                results = TranscriptionResults(
                    transcript=transcript,
                    entities=entities,
                    summary=summary,
                    confidence=0.95,
                    processing_time=processing_time,
                    model_used="whisper-api" if use_api else "whisper-base",
                    language="en",
                    word_count=len(transcript.split()) if transcript else 0
                )
            
            # Save to database (if user is authenticated)
            if current_user:
                from database import Transcript
                from auth.auth_manager import auth_manager
                
                # Get selected team from session state
                team_id = st.session_state.get('selected_team_id', None)
                
                db_transcript = Transcript(
                    user_id=current_user.id,
                    team_id=team_id,
                    title=uploaded_file.name,
                    content=results.transcript,
                    file_name=uploaded_file.name,
                    file_size=uploaded_file.size,
                    language=results.language,
                    confidence=results.confidence,
                    word_count=results.word_count,
                    entities=results.entities,
                    summary=results.summary,
                    model_used=results.model_used,
                    processing_time=results.processing_time
                )
                
                auth_manager.db.add(db_transcript)
                auth_manager.db.commit()
                auth_manager.db.refresh(db_transcript)
                
                # Store transcript ID in results for sharing
                results.transcript_id = db_transcript.id
                
                # Create initial version
                from database.models import get_db_session
                session = get_db_session()
                version_manager = VersionManager(session)
                version_manager.create_version(
                    transcript_id=db_transcript.id,
                    user_id=current_user.id,
                    change_summary="Initial transcript creation"
                )
                
                # Notify team members if saved to team
                if team_id:
                    from database.models import Team
                    notification_manager = NotificationManager(session)
                    team = session.query(Team).filter_by(id=team_id).first()
                    if team:
                        notification_manager.notify_team_members(
                            team_id=team_id,
                            notification_type='team_announcement',
                            title=f"New transcript in {team.name}",
                            message=f"{current_user.username} added '{uploaded_file.name}' to the team",
                            from_user_id=current_user.id
                        )
                
                logger.info(f"Transcript saved to database for user {current_user.username}, team_id: {team_id}")
            
            # Complete processing
            progress_callback(4, "Finalizing results...")
            session_manager.complete_processing(results)
            
            # Cleanup
            utils.cleanup_file(temp_path)
            if audio_path != temp_path:
                utils.cleanup_file(audio_path)
            
            # Show success
            st.success("✅ Processing completed successfully!")
            st.balloons()
            
    except Exception as e:
        logger.error(f"Processing error: {e}")
        error_handled = handle_error(e)
        session_manager.set_error(
            error_handled.user_message,
            error_handled
        )
        
        # Cleanup on error
        if 'temp_path' in locals():
            utils.cleanup_file(temp_path)

def render_transcript_tab(results: TranscriptionResults):
    """Render transcript tab with options and annotations"""
    # Check if we have a saved transcript with ID
    if hasattr(results, 'transcript_id') and results.transcript_id:
        # Get current user
        current_user = get_current_user()
        if current_user:
            # Get database session and annotation manager
            from database.models import get_db_session
            session = get_db_session()
            annotation_manager = AnnotationManager(session)
            
            # Render annotation UI
            render_annotation_ui(
                transcript_id=results.transcript_id,
                transcript_content=results.transcript,
                annotation_manager=annotation_manager,
                current_user=current_user
            )
        else:
            # No user logged in, show regular transcript
            render_basic_transcript(results)
    else:
        # No saved transcript, show basic view
        render_basic_transcript(results)
    
    # Show share dialog if button was clicked
    if st.session_state.get('show_share_dialog', False):
        with st.container():
            st.markdown("---")
            render_share_dialog(st.session_state.get('share_transcript_id'))
            if st.button("Close Share Dialog"):
                st.session_state.show_share_dialog = False
                st.rerun()


def render_segments_tab(results: TranscriptionResults):
    """Render segments tab with advanced segmentation"""
    st.markdown("### 📑 Advanced Segmentation")
    
    # Check if segments are already cached
    cache_key = f"segments_{hash(results.transcript)}"
    if cache_key not in st.session_state:
        # Segment controls
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            method = st.selectbox(
                "Segmentation Method",
                ["hybrid", "semantic", "structural", "temporal"],
                help="Choose how to segment the transcript"
            )
        
        with col2:
            if st.button("🔄 Generate Segments", type="primary"):
                with st.spinner("Segmenting transcript..."):
                    # Create segment manager
                    manager = SegmentManager()
                    
                    # Generate segments
                    segments = manager.segment_transcript(
                        results.transcript,
                        method=method
                    )
                    
                    # Cache segments
                    st.session_state[cache_key] = segments
                    st.success(f"Generated {len(segments)} segments!")
        
        with col3:
            if st.button("ℹ️ Help"):
                with st.expander("Segmentation Methods", expanded=True):
                    st.write("""
                    **Hybrid**: Combines multiple methods for best results
                    **Semantic**: Groups by meaning and topic similarity
                    **Structural**: Uses linguistic patterns and markers
                    **Temporal**: Divides by time intervals
                    """)
    
    # Display segments if available
    if cache_key in st.session_state:
        segments = st.session_state[cache_key]
        
        # Check if user can edit (if logged in and owns transcript)
        editable = False
        if hasattr(results, 'transcript_id') and results.transcript_id:
            current_user = get_current_user()
            if current_user:
                # Check if user owns the transcript
                from database.models import get_db_session, Transcript
                session = get_db_session()
                transcript = session.query(Transcript).filter_by(id=results.transcript_id).first()
                if transcript and transcript.user_id == current_user.id:
                    editable = True
        
        # Render segmentation view
        updated_segments = render_segmentation_view(
            results.transcript,
            segments,
            editable=editable
        )
        
        # Update cache if segments were edited
        if updated_segments != segments:
            st.session_state[cache_key] = updated_segments
    else:
        st.info("Click 'Generate Segments' to create an intelligent breakdown of your transcript.")


def render_basic_transcript(results: TranscriptionResults):
    """Render basic transcript without annotations"""
    if st.session_state.get('user_preferences', {}).get('show_line_numbers', False):
        # Show with line numbers
        lines = results.transcript.split('\n')
        numbered_text = '\n'.join([f"{i+1:3d} | {line}" for i, line in enumerate(lines)])
        st.text_area("Transcript with Line Numbers", numbered_text, height=400)
    else:
        st.text_area("Transcript", results.transcript, height=400)
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        # Copy button
        if st.button("📋 Copy to Clipboard"):
            st.write("```")
            st.code(results.transcript, language=None)
            st.write("```")
            st.info("Select the text above and copy it")
    
    with col2:
        # Share button (only if transcript has been saved)
        if hasattr(results, 'transcript_id') and results.transcript_id:
            if st.button("🔗 Share Transcript"):
                st.session_state.show_share_dialog = True
                st.session_state.share_transcript_id = results.transcript_id

def render_tags_tab(results: TranscriptionResults):
    """Render tags tab with AI-powered tagging"""
    st.markdown("### 🏷️ AI-Powered Content Tags")
    
    # Check if tags are already cached
    cache_key = f"tags_{hash(results.transcript)}"
    
    # Get existing tags from cache or database
    existing_tags = None
    if hasattr(results, 'transcript_id') and results.transcript_id:
        # Could load saved tags from database here
        pass
    
    # Use mock provider for demo
    provider = MockAIProvider()
    
    # Render tagging interface
    tags = render_tagging_view(
        results.transcript,
        existing_tags=existing_tags,
        editable=True
    )
    
    # Cache the tags
    if tags:
        st.session_state[cache_key] = tags
        
        # Save tags button (if transcript is saved)
        if hasattr(results, 'transcript_id') and results.transcript_id:
            current_user = get_current_user()
            if current_user:
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button("💾 Save Tags"):
                        # Here you would save tags to database
                        st.success("Tags saved successfully!")

def render_entities_tab(results: TranscriptionResults):
    """Render entities tab with visualizations"""
    if results.entities:
        render_enhanced_entity_display(results.entities)
    else:
        st.info("No entities found in the transcript")

def render_analysis_tab(results: TranscriptionResults, analysis_mode: str):
    """Render analysis tab with metrics"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        enhanced_metric_display("Word Count", results.word_count, "📊")
    with col2:
        enhanced_metric_display("Confidence", f"{results.confidence:.2%}", "🎯")
    with col3:
        enhanced_metric_display("Processing Time", f"{results.processing_time:.1f}s", "⏱️")
    
    if results.summary:
        st.subheader("📝 Summary")
        st.write(results.summary)
    
    # Show advanced results if available
    if "Advanced+" in analysis_mode:
        render_advanced_results()

def render_audio_tab(results: TranscriptionResults):
    """Render audio tab with TTS options"""
    st.subheader("🎤 Text-to-Speech")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        selected_text = st.text_area(
            "Text to Convert",
            value=results.transcript[:500] + "..." if len(results.transcript) > 500 else results.transcript,
            height=150,
            help="Edit or select the text you want to convert to speech"
        )
    
    with col2:
        voice = st.selectbox(
            "Voice",
            ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
            help="Choose the voice for text-to-speech"
        )
        
        if st.button("🔊 Generate Audio", type="primary"):
            if selected_text:
                try:
                    with st.spinner("Generating audio..."):
                        audio_path = tts.text_to_speech(selected_text, voice=voice)
                        if audio_path and os.path.exists(audio_path):
                            enhanced_audio_player(audio_path)
                            
                            with open(audio_path, "rb") as audio_file:
                                st.download_button(
                                    "📥 Download Audio",
                                    data=audio_file.read(),
                                    file_name=f"tts_audio_{utils.get_timestamp()}.mp3",
                                    mime="audio/mp3"
                                )
                        else:
                            st.error("Failed to generate audio")
                except Exception as e:
                    st.error(f"TTS Error: {str(e)}")

def render_export_options(results: TranscriptionResults, current_user):
    """Render export options with enhanced formats and sharing features"""
    st.subheader("📤 Export & Share Options")
    
    # Initialize export manager
    export_manager = ExportManager()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Enhanced exports
        available_formats = export_manager.get_available_formats()
        format_labels = {
            'text': 'Text (.txt)',
            'json': 'JSON (.json)', 
            'markdown': 'Markdown (.md)',
            'docx': 'Word (.docx)'
        }
        
        format_options = [format_labels[fmt] for fmt in available_formats]
        
        selected_format_label = st.selectbox(
            "Export Format",
            format_options,
            help="Choose export format"
        )
        
        # Map back to format key
        format_map = {v: k for k, v in format_labels.items()}
        selected_format = format_map[selected_format_label]
        
        # Export options
        with st.expander("Export Options"):
            include_metadata = st.checkbox("Include metadata", value=True)
            include_entities = st.checkbox("Include entities", value=True)
            
            # DOCX-specific options
            if selected_format == 'docx':
                st.info("💡 Word documents include professional formatting and inline annotations")
        
        if st.button("📥 Export", use_container_width=True):
            try:
                export_options = {
                    'include_metadata': include_metadata,
                    'include_entities': include_entities
                }
                
                export_result = export_manager.export_results(
                    results=results,
                    format_type=selected_format,
                    filename="transcript",
                    export_options=export_options
                )
                
                # Handle binary vs text content
                if isinstance(export_result['content'], bytes):
                    st.download_button(
                        f"📥 Download {selected_format_label}",
                        data=export_result['content'],
                        file_name=export_result['filename'],
                        mime=export_result['mime_type'],
                        use_container_width=True
                    )
                else:
                    st.download_button(
                        f"📥 Download {selected_format_label}",
                        data=export_result['content'],
                        file_name=export_result['filename'],
                        mime=export_result['mime_type'],
                        use_container_width=True
                    )
                
                st.success(f"✅ {selected_format_label} export ready!")
                
            except Exception as e:
                if "python-docx" in str(e):
                    st.error("📝 Word export requires python-docx library. Please install it to enable Word exports.")
                else:
                    st.error(f"Export failed: {str(e)}")
    
    with col2:
        # Share options
        if hasattr(results, 'transcript_id') and results.transcript_id:
            st.write("**🔗 Share Transcript**")
            if st.button("Create Share Link", use_container_width=True):
                st.session_state.show_share_dialog = True
                st.session_state.share_transcript_id = results.transcript_id
                st.rerun()
            
            st.info("Share with view, comment, or edit permissions")
        else:
            st.info("🔗 Save transcript first to enable sharing")
    
    with col3:
        # Collaboration options
        if hasattr(results, 'transcript_id') and results.transcript_id:
            st.write("**👥 Collaboration**")
            
            # Get annotation stats
            from database.models import get_db_session
            session = get_db_session()
            annotation_manager = AnnotationManager(session)
            stats = annotation_manager.get_annotation_stats(results.transcript_id)
            
            st.metric("Comments", stats.get('total_annotations', 0))
            st.metric("Contributors", stats.get('unique_users', 0))
            
            if st.button("View All Comments", use_container_width=True):
                # This would scroll to the annotations section
                st.info("💬 See annotations in the Transcript tab")
        else:
            st.info("👥 Save transcript first to enable collaboration")

def format_results_for_export(results: TranscriptionResults, format_type: str) -> str:
    """Format results for export"""
    if format_type == "Text":
        export_data = f"Transcript\n{'='*50}\n{results.transcript}\n\n"
        if results.entities:
            export_data += f"Entities\n{'='*50}\n"
            for entity_type, entities in results.entities.items():
                export_data += f"{entity_type}: {', '.join(entities)}\n"
        if results.summary:
            export_data += f"\nSummary\n{'='*50}\n{results.summary}\n"
        return export_data
    
    elif format_type == "JSON":
        import json
        export_dict = {
            "transcript": results.transcript,
            "entities": results.entities,
            "summary": results.summary,
            "metadata": {
                "word_count": results.word_count,
                "confidence": results.confidence,
                "processing_time": results.processing_time,
                "model_used": results.model_used,
                "language": results.language
            }
        }
        return json.dumps(export_dict, indent=2)
    
    elif format_type == "Markdown":
        export_data = f"# Transcript\n\n{results.transcript}\n\n"
        if results.entities:
            export_data += "## Entities\n\n"
            for entity_type, entities in results.entities.items():
                export_data += f"**{entity_type}**: {', '.join(entities)}\n\n"
        if results.summary:
            export_data += f"## Summary\n\n{results.summary}\n\n"
        export_data += "## Metadata\n\n"
        export_data += f"- **Word Count**: {results.word_count}\n"
        export_data += f"- **Confidence**: {results.confidence:.2%}\n"
        export_data += f"- **Processing Time**: {results.processing_time:.1f}s\n"
        export_data += f"- **Model**: {results.model_used}\n"
        return export_data
    
    return ""

@require_authentication
def render_admin_panel(current_user):
    """Render admin panel (if user has admin role)"""
    from database import UserRole
    
    if current_user.role != UserRole.ADMIN:
        st.warning("You don't have permission to access the admin panel")
        return
    
    st.header("🛠️ Admin Panel")
    st.info("Admin features for testing and demonstration")
    
    # Import and render the existing admin panel
    from demo_admin_panel import render_admin_interface
    render_admin_interface()

@require_authentication
def render_user_transcripts(current_user):
    """Render user's transcript history"""
    st.header("📚 My Transcripts")
    
    from database import Transcript
    from auth.auth_manager import auth_manager
    
    # Get user's transcripts
    transcripts = auth_manager.db.query(Transcript).filter(
        Transcript.user_id == current_user.id
    ).order_by(Transcript.created_at.desc()).all()
    
    if not transcripts:
        st.info("You haven't created any transcripts yet. Start by uploading a file in the Transcription & Analysis mode.")
        return
    
    # Get annotation and version stats for all transcripts
    from database.models import get_db_session
    session = get_db_session()
    annotation_manager = AnnotationManager(session)
    version_manager = VersionManager(session)
    
    annotation_stats = {}
    version_stats = {}
    for transcript in transcripts:
        stats = annotation_manager.get_annotation_stats(transcript.id)
        annotation_stats[transcript.id] = stats
        v_stats = version_manager.get_version_stats(transcript.id)
        version_stats[transcript.id] = v_stats
    
    # Display transcripts
    st.write(f"You have {len(transcripts)} transcript(s)")
    
    for transcript in transcripts:
        # Add annotation and version counts to title
        stats = annotation_stats.get(transcript.id, {})
        annotation_count = stats.get('total_annotations', 0)
        unresolved_count = stats.get('unresolved_count', 0)
        
        v_stats = version_stats.get(transcript.id, {})
        version_count = v_stats.get('total_versions', 0)
        
        title = f"📄 {transcript.title} - {transcript.created_at.strftime('%Y-%m-%d %H:%M')}"
        if annotation_count > 0:
            title += f" 💬 {annotation_count}"
            if unresolved_count > 0:
                title += f" ({unresolved_count} unresolved)"
        if version_count > 0:
            title += f" 📚 v{version_count}"
        
        with st.expander(title):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**File**: {transcript.file_name}")
                st.write(f"**Words**: {transcript.word_count}")
                st.write(f"**Model**: {transcript.model_used}")
                st.write(f"**Confidence**: {transcript.confidence:.2%}")
                
                # Show transcript preview
                preview = transcript.content[:500] + "..." if len(transcript.content) > 500 else transcript.content
                st.text_area("Preview", preview, height=150, disabled=True)
            
            with col2:
                # Action buttons
                if st.button(f"View Full", key=f"view_{transcript.id}"):
                    st.session_state.selected_transcript = transcript
                    st.rerun()
                
                if st.button(f"🔗 Share", key=f"share_btn_{transcript.id}"):
                    st.session_state.show_share_dialog = True
                    st.session_state.share_transcript_id = transcript.id
                
                if st.button(f"Export", key=f"export_{transcript.id}"):
                    # Enhanced export with format selection
                    st.session_state[f'show_export_{transcript.id}'] = True
                    st.rerun()
                
                # Show export dialog if export button was clicked
                if st.session_state.get(f'show_export_{transcript.id}', False):
                    st.markdown("**Export Options**")
                    
                    # Initialize export manager
                    export_manager = ExportManager()
                    available_formats = export_manager.get_available_formats()
                    
                    format_labels = {
                        'text': 'Text (.txt)',
                        'json': 'JSON (.json)', 
                        'markdown': 'Markdown (.md)',
                        'docx': 'Word (.docx)'
                    }
                    
                    format_options = [format_labels[fmt] for fmt in available_formats]
                    
                    selected_format_label = st.selectbox(
                        "Format",
                        format_options,
                        key=f"format_{transcript.id}"
                    )
                    
                    # Map back to format key
                    format_map = {v: k for k, v in format_labels.items()}
                    selected_format = format_map[selected_format_label]
                    
                    # Export options
                    include_metadata = st.checkbox("Include metadata", value=True, key=f"meta_{transcript.id}")
                    include_entities = st.checkbox("Include entities", value=True, key=f"entities_{transcript.id}")
                    include_annotations = st.checkbox("Include annotations", value=True, key=f"annotations_{transcript.id}")
                    
                    col_export, col_cancel = st.columns(2)
                    
                    with col_export:
                        if st.button("📥 Export", key=f"do_export_{transcript.id}"):
                            try:
                                # Get annotations if requested
                                annotations = None
                                if include_annotations:
                                    from database.models import get_db_session
                                    session = get_db_session()
                                    annotation_manager = AnnotationManager(session)
                                    annotations = annotation_manager.get_transcript_annotations(transcript.id)
                                
                                export_options = {
                                    'include_metadata': include_metadata,
                                    'include_entities': include_entities,
                                    'include_annotations': include_annotations
                                }
                                
                                export_result = export_manager.export_transcript(
                                    transcript=transcript,
                                    format_type=selected_format,
                                    annotations=annotations,
                                    export_options=export_options
                                )
                                
                                # Provide download
                                st.download_button(
                                    f"📥 Download {selected_format_label}",
                                    data=export_result['content'],
                                    file_name=export_result['filename'],
                                    mime=export_result['mime_type'],
                                    key=f"download_{transcript.id}"
                                )
                                
                                st.success(f"✅ {selected_format_label} export ready!")
                                
                            except Exception as e:
                                if "python-docx" in str(e):
                                    st.error("📝 Word export requires python-docx library.")
                                else:
                                    st.error(f"Export failed: {str(e)}")
                    
                    with col_cancel:
                        if st.button("❌ Cancel", key=f"cancel_export_{transcript.id}"):
                            st.session_state[f'show_export_{transcript.id}'] = False
                            st.rerun()
                
    
    # Show share dialog if share button was clicked
    if st.session_state.get('show_share_dialog', False):
        st.markdown("---")
        st.subheader("Share Transcript")
        render_share_dialog(st.session_state.get('share_transcript_id'))
        if st.button("Close Share Dialog"):
            st.session_state.show_share_dialog = False
            st.rerun()
    
    # View selected transcript if any
    if hasattr(st.session_state, 'selected_transcript') and st.session_state.selected_transcript:
        st.markdown("---")
        transcript = st.session_state.selected_transcript
        st.subheader(f"Viewing: {transcript.title}")
        
        # Add tabs for viewing transcript
        view_tab1, view_tab2 = st.tabs(["📝 Content", "📚 History"])
        
        with view_tab1:
            # Get annotation manager
            from database.models import get_db_session
            session = get_db_session()
            annotation_manager = AnnotationManager(session)
            
            # Render annotation UI for the selected transcript
            render_annotation_ui(
                transcript_id=transcript.id,
                transcript_content=transcript.content,
                annotation_manager=annotation_manager,
                current_user=current_user
            )
        
        with view_tab2:
            # Show version history
            session = get_db_session()
            version_manager = VersionManager(session)
            render_version_history(transcript.id, version_manager, current_user)
        
        # Entities
        if transcript.entities:
            st.subheader("Entities")
            import json
            entities = json.loads(transcript.entities) if isinstance(transcript.entities, str) else transcript.entities
            render_enhanced_entity_display(entities)
        
        # Clear selection
        if st.button("← Back to List"):
            st.session_state.selected_transcript = None
            st.rerun()

@require_authentication
def render_team_mode(current_user):
    """Render team workspace interface"""
    from database.models import get_db_session
    
    session = get_db_session()
    team_manager = TeamManager(session)
    
    # Check for team management actions in session state
    if st.session_state.get('show_team_management', False):
        render_team_management(team_manager, current_user.id)
        return
    
    if st.session_state.get('show_team_analytics'):
        team_id = st.session_state.show_team_analytics
        team = team_manager.get_team(team_id, current_user.id)
        if team:
            st.header(f"📊 Analytics - {team.name}")
            render_team_analytics(team_manager, team, current_user.id)
            if st.button("← Back to Dashboard"):
                st.session_state.show_team_analytics = False
                st.rerun()
        return
    
    if st.session_state.get('show_team_settings'):
        team_id = st.session_state.show_team_settings
        team = team_manager.get_team(team_id, current_user.id)
        if team:
            st.header(f"⚙️ Settings - {team.name}")
            render_team_settings(team_manager, team, current_user.id)
            if st.button("← Back to Dashboard"):
                st.session_state.show_team_settings = False
                st.rerun()
        return
    
    # Default to team dashboard
    render_team_dashboard(team_manager, current_user.id)

@require_authentication
def render_notifications_mode(current_user):
    """Render notification preferences and history"""
    st.header("🔔 Notifications")
    
    from database.models import get_db_session
    from notifications import NotificationManager
    
    session = get_db_session()
    notification_manager = NotificationManager(session)
    
    # Tabs for different notification sections
    tab1, tab2, tab3 = st.tabs(["📋 Notification History", "⚙️ Preferences", "📊 Statistics"])
    
    with tab1:
        render_notification_history(notification_manager, current_user)
    
    with tab2:
        render_notification_preferences(notification_manager, current_user)
    
    with tab3:
        render_notification_statistics(notification_manager, current_user)

def render_notification_history(notification_manager, current_user):
    """Render notification history"""
    st.subheader("Recent Notifications")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        show_read = st.checkbox("Show read", value=True)
    with col2:
        show_archived = st.checkbox("Show archived", value=False)
    with col3:
        limit = st.selectbox("Show", [10, 25, 50, 100], index=1)
    
    # Get notifications
    notifications = notification_manager.get_user_notifications(
        user_id=current_user.id,
        include_read=show_read,
        include_archived=show_archived,
        limit=limit
    )
    
    if not notifications:
        st.info("No notifications found.")
        return
    
    # Display notifications
    for notification in notifications:
        with st.container():
            col1, col2, col3 = st.columns([4, 1, 1])
            
            with col1:
                # Notification icon based on type
                icon_map = {
                    'mention': '🏷️',
                    'annotation_reply': '💬',
                    'transcript_edit': '✏️',
                    'share_access': '🔗'
                }
                icon = icon_map.get(notification.type, '🔔')
                
                if notification.is_read:
                    st.markdown(f"{icon} **{notification.title}**")
                else:
                    st.markdown(f"{icon} **{notification.title}** 🔴")
                
                st.text(notification.message)
                st.caption(f"{notification.created_at.strftime('%Y-%m-%d %H:%M')}")
                
                if notification.link:
                    st.markdown(f"[View →]({notification.link})")
            
            with col2:
                if not notification.is_read:
                    if st.button("Mark Read", key=f"read_{notification.id}"):
                        notification_manager.mark_notification_read(notification.id)
                        st.rerun()
                else:
                    if st.button("Mark Unread", key=f"unread_{notification.id}"):
                        notification_manager.mark_notification_unread(notification.id)
                        st.rerun()
            
            with col3:
                if not notification.is_archived:
                    if st.button("Archive", key=f"archive_{notification.id}"):
                        notification_manager.archive_notification(notification.id)
                        st.rerun()
                else:
                    if st.button("Unarchive", key=f"unarchive_{notification.id}"):
                        notification_manager.unarchive_notification(notification.id)
                        st.rerun()
            
            st.divider()
    
    # Bulk actions
    st.subheader("Bulk Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Mark All Read"):
            notification_manager.mark_all_read(current_user.id)
            st.success("All notifications marked as read")
            st.rerun()
    with col2:
        if st.button("Archive All Read"):
            notification_manager.archive_all_read(current_user.id)
            st.success("All read notifications archived")
            st.rerun()

def render_notification_preferences(notification_manager, current_user):
    """Render notification preferences"""
    st.subheader("Notification Preferences")
    
    # Get current preferences (would need to add to notification manager)
    st.info("📧 Email notifications coming soon!")
    
    # Notification types
    st.write("**Notification Types**")
    
    mention_enabled = st.checkbox("Mentions (@username)", value=True, help="When someone mentions you in annotations")
    reply_enabled = st.checkbox("Annotation Replies", value=True, help="When someone replies to your annotations")
    edit_enabled = st.checkbox("Transcript Edits", value=True, help="When transcripts you've worked on are edited")
    share_enabled = st.checkbox("Share Access", value=True, help="When someone shares a transcript with you")
    
    # Delivery preferences
    st.write("**Delivery Settings**")
    in_app_enabled = st.checkbox("In-app notifications", value=True, disabled=True, help="Always enabled")
    email_enabled = st.checkbox("Email notifications", value=False, disabled=True, help="Coming soon")
    
    # Frequency settings
    st.write("**Frequency Settings**")
    frequency = st.selectbox(
        "Email digest frequency",
        ["Immediate", "Daily", "Weekly", "Never"],
        index=3,
        disabled=True,
        help="Coming soon"
    )
    
    if st.button("Save Preferences", disabled=True):
        st.info("Preference saving will be implemented soon!")

def render_notification_statistics(notification_manager, current_user):
    """Render notification statistics"""
    st.subheader("Notification Statistics")
    
    # Get stats
    stats = notification_manager.get_user_notification_stats(current_user.id)
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Notifications", stats.get('total', 0))
    with col2:
        st.metric("Unread", stats.get('unread', 0))
    with col3:
        st.metric("This Week", stats.get('this_week', 0))
    with col4:
        st.metric("This Month", stats.get('this_month', 0))
    
    # Notification types breakdown
    st.subheader("By Type")
    type_stats = stats.get('by_type', {})
    
    if type_stats:
        for notification_type, count in type_stats.items():
            icon_map = {
                'mention': '🏷️',
                'annotation_reply': '💬',
                'transcript_edit': '✏️',
                'share_access': '🔗'
            }
            icon = icon_map.get(notification_type, '🔔')
            st.write(f"{icon} **{notification_type.replace('_', ' ').title()}**: {count}")
    else:
        st.info("No notification statistics available yet.")

if __name__ == "__main__":
    main()