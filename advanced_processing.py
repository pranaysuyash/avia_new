#!/usr/bin/env python3
"""
Advanced Processing Integration
Integrates advanced transcription features with the main application
"""

import streamlit as st
import os
import logging
import tempfile
import time
from typing import Optional, Dict, Any, List

# Import advanced transcription modules
from advanced_transcription import (
    transcribe_advanced, detect_audio_language, get_supported_languages,
    edit_transcript, export_transcript, AdvancedTranscriptionResult
)
from interactive_transcript import (
    render_advanced_interactive_transcript, render_speaker_timeline,
    render_confidence_analysis, render_advanced_transcript_ui
)
from session_manager import session_manager
from errors import handle_error, TranscriptionError
import utils

logger = logging.getLogger(__name__)

def process_audio_with_advanced_features(audio_source, analysis_mode: str = "Advanced") -> Optional[Dict[str, Any]]:
    """
    Process audio with advanced transcription features
    
    Args:
        audio_source: Audio file or recorded audio
        analysis_mode: Processing mode
        
    Returns:
        Dictionary with advanced transcription results
    """
    try:
        # Save audio to temporary file
        temp_dir = utils.ensure_temp_directory()
        
        if hasattr(audio_source, 'name'):
            # Uploaded file
            temp_path = os.path.join(temp_dir, f"temp_{audio_source.name}")
            with open(temp_path, "wb") as f:
                f.write(audio_source.read())
            audio_source.seek(0)  # Reset for potential reuse
        else:
            # Recorded audio
            temp_path = os.path.join(temp_dir, "recorded_audio.wav")
            with open(temp_path, "wb") as f:
                f.write(audio_source.read())
            audio_source.seek(0)  # Reset for potential reuse
        
        # Initialize processing status
        processing_status = {
            'language_detection': False,
            'transcription': False,
            'diarization': False,
            'current_step': 'Starting...',
            'progress': 0.0
        }
        
        # Create status container
        status_container = st.empty()
        
        # Step 1: Language Detection
        processing_status['current_step'] = 'Detecting language...'
        processing_status['progress'] = 0.2
        status_container.write("🔄 Detecting language...")
        
        detected_languages = detect_audio_language(temp_path)
        processing_status['language_detection'] = True
        processing_status['progress'] = 0.4
        
        # Step 2: Advanced Transcription with Speaker Diarization
        processing_status['current_step'] = 'Transcribing with speaker diarization...'
        status_container.write("🔄 Transcribing with speaker diarization...")
        
        # Get language preference from session state or use auto-detected
        selected_language = st.session_state.get('selected_language', None)
        if not selected_language and detected_languages:
            selected_language = detected_languages[0]['code']
        
        # Perform advanced transcription
        advanced_result = transcribe_advanced(
            audio_path=temp_path,
            language=selected_language,
            use_api=True  # Prefer API for better quality
        )
        
        processing_status['transcription'] = True
        processing_status['diarization'] = True
        processing_status['progress'] = 1.0
        processing_status['current_step'] = 'Complete!'
        
        status_container.success("✅ Advanced transcription completed!")
        
        # Convert result to dictionary format for UI
        result_data = advanced_result.to_dict()
        
        # Store in session state
        session_manager.store_advanced_results(advanced_result, detected_languages)
        
        # Clean up temporary file
        utils.cleanup_file(temp_path)
        
        return {
            'advanced_result': advanced_result,
            'detected_languages': detected_languages,
            'processing_status': processing_status,
            'result_data': result_data
        }
        
    except Exception as e:
        logger.error(f"Advanced processing failed: {e}")
        error_message = handle_error(e, {
            "operation": "advanced_transcription",
            "audio_source": str(type(audio_source))
        })
        st.error(f"❌ Advanced processing failed: {error_message}")
        
        # Clean up on error
        if 'temp_path' in locals():
            utils.cleanup_file(temp_path)
        
        return None

def render_advanced_results(processing_result: Dict[str, Any]) -> None:
    """
    Render advanced transcription results with interactive features
    
    Args:
        processing_result: Result from advanced processing
    """
    if not processing_result:
        return
    
    advanced_result = processing_result['advanced_result']
    detected_languages = processing_result['detected_languages']
    result_data = processing_result['result_data']
    
    st.header("🚀 Advanced Transcription Results")
    
    # Language detection results
    if detected_languages:
        st.subheader("🌍 Language Detection")
        col1, col2, col3 = st.columns(3)
        
        for i, lang in enumerate(detected_languages[:3]):
            with [col1, col2, col3][i]:
                confidence_bar = "█" * int(lang['confidence'] * 10)
                st.metric(
                    lang['name'],
                    f"{lang['confidence']:.1%}",
                    help=f"Confidence: {confidence_bar}"
                )
    
    # Quality metrics
    st.subheader("📊 Quality Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        confidence_color = "🟢" if advanced_result.confidence > 0.8 else "🟡" if advanced_result.confidence > 0.6 else "🔴"
        st.metric("Overall Quality", f"{confidence_color} {advanced_result.confidence:.1%}")
    
    with col2:
        st.metric("Speakers Detected", advanced_result.get_speaker_count())
    
    with col3:
        st.metric("Duration", f"{advanced_result.get_total_duration():.1f}s")
    
    with col4:
        st.metric("Processing Time", f"{advanced_result.processing_time:.1f}s")
    
    # Speaker statistics
    if advanced_result.speakers:
        st.subheader("👥 Speaker Analysis")
        speaker_stats = advanced_result.get_speaker_statistics()
        
        # Create speaker stats table
        speaker_data = []
        for speaker_id, stats in speaker_stats.items():
            speaker_data.append({
                'Speaker': speaker_id,
                'Speaking Time': f"{stats['total_time']:.1f}s",
                'Word Count': stats['word_count'],
                'Segments': stats['segments'],
                'Avg Confidence': f"{stats['avg_confidence']:.2f}"
            })
        
        if speaker_data:
            import pandas as pd
            df = pd.DataFrame(speaker_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Interactive transcript
    st.subheader("📝 Interactive Transcript")
    
    # Convert speakers to segments format for UI
    segments_data = []
    for speaker in advanced_result.speakers:
        segments_data.append({
            'text': speaker.text,
            'start_time': speaker.start_time,
            'end_time': speaker.end_time,
            'speaker': speaker.speaker_id,
            'confidence': speaker.confidence
        })
    
    # Render interactive transcript
    interactions = render_advanced_interactive_transcript(
        segments_data=segments_data,
        show_speakers=True,
        show_timestamps=True,
        show_confidence=True,
        editable=True
    )
    
    # Handle transcript edits
    if interactions.get('edited_segments'):
        st.info(f"📝 {len(interactions['edited_segments'])} segments edited")
        
        if st.button("💾 Apply Edits"):
            apply_transcript_edits(advanced_result, interactions['edited_segments'])
            st.success("✅ Edits applied successfully!")
            st.rerun()
    
    # Speaker timeline
    render_speaker_timeline(segments_data)
    
    # Confidence analysis
    render_confidence_analysis(segments_data)
    
    # Export options
    render_export_options(advanced_result)

def apply_transcript_edits(advanced_result: AdvancedTranscriptionResult, 
                          edited_segments: List[Dict]) -> None:
    """
    Apply user edits to the transcript
    
    Args:
        advanced_result: Original transcription result
        edited_segments: List of edited segments
    """
    try:
        # Convert edits to the format expected by edit_transcript
        edits = []
        for edit in edited_segments:
            edits.append({
                'type': 'text_replace',
                'old_text': edit['original_text'],
                'new_text': edit['edited_text']
            })
        
        # Apply edits
        edited_result = edit_transcript(advanced_result, edits)
        
        # Update session state with edited result
        session_manager.store_advanced_results(edited_result, [])
        
        logger.info(f"Applied {len(edits)} transcript edits")
        
    except Exception as e:
        logger.error(f"Failed to apply transcript edits: {e}")
        st.error(f"❌ Failed to apply edits: {e}")

def render_export_options(advanced_result: AdvancedTranscriptionResult) -> None:
    """
    Render export options for advanced transcription results
    
    Args:
        advanced_result: Transcription result to export
    """
    st.subheader("📥 Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Export Format:**")
        export_format = st.selectbox(
            "Choose format:",
            options=['txt', 'json', 'srt', 'vtt', 'csv'],
            help="Select the format for transcript export"
        )
        
        include_speakers = st.checkbox("Include Speakers", value=True)
        include_timestamps = st.checkbox("Include Timestamps", value=True)
    
    with col2:
        st.markdown("**Export Actions:**")
        
        if st.button("📄 Generate Export", type="primary"):
            try:
                exported_content = export_transcript(
                    result=advanced_result,
                    format_type=export_format,
                    include_speakers=include_speakers,
                    include_timestamps=include_timestamps
                )
                
                # Determine MIME type
                mime_types = {
                    'txt': 'text/plain',
                    'json': 'application/json',
                    'srt': 'text/plain',
                    'vtt': 'text/vtt',
                    'csv': 'text/csv'
                }
                
                filename = f"advanced_transcript_{utils.get_timestamp()}.{export_format}"
                
                st.download_button(
                    label=f"💾 Download {export_format.upper()}",
                    data=exported_content,
                    file_name=filename,
                    mime=mime_types.get(export_format, 'text/plain'),
                    help=f"Download transcript in {export_format.upper()} format"
                )
                
                st.success(f"✅ Export ready! Click download to save as {export_format.upper()}")
                
            except Exception as e:
                logger.error(f"Export failed: {e}")
                st.error(f"❌ Export failed: {e}")

def render_advanced_processing_options() -> Dict[str, Any]:
    """
    Render advanced processing options UI
    
    Returns:
        Dictionary with selected options
    """
    st.subheader("⚙️ Advanced Processing Options")
    
    col1, col2 = st.columns(2)
    
    options = {}
    
    with col1:
        st.markdown("**Language Settings:**")
        
        # Language selection
        supported_languages = get_supported_languages()
        language_options = ['Auto-detect'] + [f"{code} - {name}" for code, name in supported_languages.items()]
        
        selected_language = st.selectbox(
            "Language:",
            options=language_options,
            help="Choose the language for transcription, or use auto-detect"
        )
        
        if selected_language == 'Auto-detect':
            options['language'] = None
        else:
            options['language'] = selected_language.split(' - ')[0]
        
        # Store in session state
        st.session_state['selected_language'] = options['language']
        
        options['use_api'] = st.checkbox(
            "Use API (Recommended)",
            value=True,
            help="Use OpenAI API for better transcription quality"
        )
    
    with col2:
        st.markdown("**Processing Features:**")
        
        options['enable_diarization'] = st.checkbox(
            "Speaker Diarization",
            value=True,
            help="Identify and separate different speakers"
        )
        
        options['enable_timestamps'] = st.checkbox(
            "Word-level Timestamps",
            value=True,
            help="Generate precise timestamps for each word"
        )
        
        options['quality_threshold'] = st.slider(
            "Quality Threshold:",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Minimum confidence score for segments"
        )
    
    return options

def show_advanced_features_help() -> None:
    """Show help information about advanced features"""
    with st.expander("ℹ️ Advanced Features Help"):
        st.markdown("""
        **🚀 Advanced Transcription Features:**
        
        **Speaker Diarization:**
        • Automatically identifies different speakers in the audio
        • Assigns speaker labels (Speaker_1, Speaker_2, etc.)
        • Shows speaking time statistics for each speaker
        
        **Multi-language Support:**
        • Automatic language detection for 60+ languages
        • Manual language selection for better accuracy
        • Support for code-switching in multilingual conversations
        
        **Interactive Transcript:**
        • Clickable segments with audio synchronization
        • Search functionality within transcript
        • Real-time editing capabilities
        • Visual speaker timeline
        
        **Quality Analysis:**
        • Confidence scoring for transcription quality
        • Low-confidence segment identification
        • Processing time and performance metrics
        
        **Export Options:**
        • Multiple formats: TXT, JSON, SRT, VTT, CSV
        • Include/exclude speakers and timestamps
        • Subtitle formats for video editing
        
        **💡 Tips for Best Results:**
        • Use clear, high-quality audio recordings
        • Minimize background noise
        • Ensure speakers don't overlap
        • Use API mode for better accuracy
        """)

# Session state management for advanced features
def initialize_advanced_session_state():
    """Initialize session state for advanced features"""
    if 'advanced_results' not in st.session_state:
        st.session_state.advanced_results = None
    
    if 'detected_languages' not in st.session_state:
        st.session_state.detected_languages = []
    
    if 'selected_language' not in st.session_state:
        st.session_state.selected_language = None
    
    if 'processing_options' not in st.session_state:
        st.session_state.processing_options = {}

def get_advanced_results() -> Optional[AdvancedTranscriptionResult]:
    """Get advanced results from session state"""
    return st.session_state.get('advanced_results', None)

def clear_advanced_results():
    """Clear advanced results from session state"""
    st.session_state.advanced_results = None
    st.session_state.detected_languages = []
    st.session_state.processing_options = {}