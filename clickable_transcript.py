"""
Enhanced Clickable Transcript Component
Provides click-to-play functionality with audio synchronization
"""

import streamlit as st
import logging
from typing import List, Dict, Optional, Any
import json
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Import speaker management
try:
    from speaker_management import SpeakerManager, apply_speaker_names_to_segments, render_speaker_statistics
    SPEAKER_MANAGEMENT_AVAILABLE = True
except ImportError:
    SPEAKER_MANAGEMENT_AVAILABLE = False
    logger.warning("Speaker management not available")


class ClickableTranscript:
    """Enhanced transcript with click-to-play functionality"""
    
    def __init__(self, transcript_text: str, segments: Optional[List[Dict]] = None):
        self.transcript_text = transcript_text
        self.segments = segments or self._create_segments_from_text(transcript_text)
    
    def _create_segments_from_text(self, text: str) -> List[Dict]:
        """Create segments from plain text by splitting sentences"""
        sentences = re.split(r'[.!?]+', text)
        segments = []
        
        current_time = 0
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if sentence:
                # Estimate duration based on word count (average 150 words per minute)
                word_count = len(sentence.split())
                duration = max(2.0, word_count * 60 / 150)  # Minimum 2 seconds
                
                segments.append({
                    'id': i,
                    'text': sentence + '.',
                    'start_time': current_time,
                    'end_time': current_time + duration,
                    'speaker': 'Speaker 1',
                    'confidence': 0.8
                })
                current_time += duration
        
        return segments
    
    def render_clickable_transcript(self, audio_file_path: Optional[str] = None):
        """Render the clickable transcript interface"""
        # Add CSS for synchronized highlighting animation
        st.markdown("""
        <style>
        @keyframes pulse-highlight {
            0% { box-shadow: 0 2px 8px rgba(255, 193, 7, 0.4); }
            50% { box-shadow: 0 4px 12px rgba(255, 193, 7, 0.7); }
            100% { box-shadow: 0 2px 8px rgba(255, 193, 7, 0.4); }
        }
        
        .current-playback-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            background-color: #ffc107;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse-dot 1.5s infinite;
        }
        
        @keyframes pulse-dot {
            0% { opacity: 0.4; transform: scale(0.8); }
            50% { opacity: 1; transform: scale(1.2); }
            100% { opacity: 0.4; transform: scale(0.8); }
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🎯 Interactive Transcript")
        st.caption("Click on any segment to jump to that point in the audio")
        
        # Speaker management interface
        if SPEAKER_MANAGEMENT_AVAILABLE and len(self.segments) > 0:
            speaker_manager = SpeakerManager()
            speaker_manager.render_speaker_management_ui(self.segments)
            
            # Apply custom speaker names
            self.segments = apply_speaker_names_to_segments(self.segments)
            
            # Speaker statistics
            with st.expander("📊 Speaker Statistics", expanded=False):
                render_speaker_statistics(self.segments)
            
            st.markdown("---")
        
        # Audio player with custom controls
        if audio_file_path:
            self._render_audio_player(audio_file_path)
        
        # Transcript controls
        self._render_controls()
        
        # Render segments
        self._render_segments()
    
    def _render_audio_player(self, audio_file_path: str):
        """Render audio player with sync capabilities"""
        try:
            # Initialize audio player state
            if 'audio_current_time' not in st.session_state:
                st.session_state.audio_current_time = 0
            if 'audio_playing' not in st.session_state:
                st.session_state.audio_playing = False
            if 'auto_highlight' not in st.session_state:
                st.session_state.auto_highlight = True
            
            # Auto-highlight toggle
            col_toggle, col_space = st.columns([1, 3])
            with col_toggle:
                st.session_state.auto_highlight = st.checkbox(
                    "🎯 Auto-highlight", 
                    value=st.session_state.auto_highlight,
                    help="Automatically highlight current segment during playback"
                )
            
            # Enhanced audio player with jump capability
            from enhanced_audio_player import render_enhanced_audio_player
            render_enhanced_audio_player(audio_file_path, height=120, key="transcript_audio_player")
            
            # Auto-update current segment based on playback time
            if st.session_state.auto_highlight:
                self._update_current_segment_highlight()
            
            # Playback controls
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("⏮️ Previous", help="Go to previous segment"):
                    self._jump_to_previous_segment()
            
            with col2:
                if st.button("▶️ Play/Pause", help="Play or pause audio"):
                    st.session_state.audio_playing = not st.session_state.audio_playing
            
            with col3:
                if st.button("⏭️ Next", help="Go to next segment"):
                    self._jump_to_next_segment()
            
            with col4:
                if st.button("🔄 Restart", help="Restart from beginning"):
                    st.session_state.audio_current_time = 0
                    st.session_state.selected_segment = None
                    st.rerun()
            
            # Time display with current segment info
            current_time_str = self._format_time(st.session_state.audio_current_time)
            total_time = self.segments[-1]['end_time'] if self.segments else 0
            total_time_str = self._format_time(total_time)
            
            current_segment = self._get_current_segment()
            if current_segment and st.session_state.auto_highlight:
                st.caption(f"⏱️ {current_time_str} / {total_time_str} • 🎯 {current_segment.get('display_speaker', current_segment.get('speaker', 'Unknown'))}")
            else:
                st.caption(f"⏱️ {current_time_str} / {total_time_str}")
            
        except Exception as e:
            st.error(f"Could not load audio file: {str(e)}")
            logger.error(f"Audio loading error: {e}")
    
    def _render_controls(self):
        """Render transcript display controls"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            show_timestamps = st.checkbox("⏰ Timestamps", value=True, key="show_timestamps")
        
        with col2:
            show_speakers = st.checkbox("👤 Speakers", value=True, key="show_speakers")
        
        with col3:
            show_confidence = st.checkbox("📊 Confidence", value=False, key="show_confidence")
        
        with col4:
            compact_view = st.checkbox("📝 Compact", value=False, key="compact_view")
        
        # Edit mode toggle
        col_edit, col_save = st.columns([1, 1])
        with col_edit:
            edit_mode = st.checkbox("✏️ Edit Mode", value=False, key="edit_mode", help="Enable inline transcript editing")
        
        with col_save:
            if edit_mode and st.button("💾 Save Changes", help="Save transcript edits"):
                self._save_transcript_changes()
                st.success("Transcript changes saved!")
                st.rerun()
        
        return show_timestamps, show_speakers, show_confidence, compact_view, edit_mode
    
    def _render_segments(self):
        """Render clickable transcript segments"""
        show_timestamps = st.session_state.get("show_timestamps", True)
        show_speakers = st.session_state.get("show_speakers", True)
        show_confidence = st.session_state.get("show_confidence", False)
        compact_view = st.session_state.get("compact_view", False)
        edit_mode = st.session_state.get("edit_mode", False)
        
        # Playback progress indicator
        if st.session_state.get('auto_highlight', False) and self.segments:
            total_time = self.segments[-1]['end_time'] if self.segments else 0
            current_time = st.session_state.get('audio_current_time', 0)
            progress = current_time / total_time if total_time > 0 else 0
            
            st.markdown("#### 📊 Playback Progress")
            progress_col1, progress_col2 = st.columns([4, 1])
            
            with progress_col1:
                st.progress(progress, f"Progress: {self._format_time(current_time)} / {self._format_time(total_time)}")
            
            with progress_col2:
                percentage = progress * 100
                st.metric("", f"{percentage:.0f}%")
            
            st.markdown("---")
        
        # Search functionality
        search_term = st.text_input("🔍 Search in transcript", placeholder="Type to search...", key="segment_search")
        
        # Filter segments based on search
        filtered_segments = self.segments
        if search_term:
            filtered_segments = [
                seg for seg in self.segments 
                if search_term.lower() in seg['text'].lower()
            ]
            if filtered_segments:
                st.success(f"Found {len(filtered_segments)} matching segments")
            else:
                st.warning("No segments match your search")
        
        # Auto-scroll controls
        if st.session_state.get('auto_highlight', False):
            col_scroll, col_space = st.columns([1, 3])
            with col_scroll:
                auto_scroll = st.checkbox(
                    "📍 Auto-scroll", 
                    value=st.session_state.get('auto_scroll', True),
                    help="Automatically scroll to current segment during playback",
                    key="auto_scroll"
                )
        
        # Render segments
        st.markdown("---")
        
        # Find current playback segment for auto-scroll
        current_playback_segment_id = None
        if st.session_state.get('auto_highlight', False):
            current_segment = self._get_current_segment()
            if current_segment:
                current_playback_segment_id = current_segment['id']
        
        for i, segment in enumerate(filtered_segments):
            # Auto-scroll to current segment
            if (st.session_state.get('auto_scroll', True) and 
                current_playback_segment_id == segment['id'] and
                st.session_state.get('auto_highlight', False)):
                
                # Create anchor for auto-scroll
                st.markdown(f'<div id="current-segment-{segment["id"]}"></div>', unsafe_allow_html=True)
                
                # JavaScript to scroll to current segment (limited in Streamlit)
                st.markdown("""
                <script>
                document.getElementById('current-segment-{segment_id}')?.scrollIntoView({{
                    behavior: 'smooth',
                    block: 'center'
                }});
                </script>
                """.format(segment_id=segment['id']), unsafe_allow_html=True)
            
            self._render_clickable_segment(
                segment, i, show_timestamps, show_speakers, show_confidence, compact_view, search_term, edit_mode
            )
    
    def _render_clickable_segment(self, segment: Dict, index: int, show_timestamps: bool, 
                                 show_speakers: bool, show_confidence: bool, compact_view: bool, 
                                 search_term: str = "", edit_mode: bool = False):
        """Render a single clickable segment"""
        text = segment['text']
        start_time = segment['start_time']
        end_time = segment['end_time']
        speaker = segment.get('speaker', 'Unknown')
        display_speaker = segment.get('display_speaker', speaker)
        confidence = segment.get('confidence', 0.8)
        
        # Highlight search terms
        display_text = text
        if search_term and search_term.lower() in text.lower():
            # Use HTML highlighting for better visibility
            pattern = re.compile(re.escape(search_term), re.IGNORECASE)
            display_text = pattern.sub(
                lambda m: f'<mark style="background-color: #ffeb3b; padding: 1px 3px; border-radius: 3px;">{m.group()}</mark>',
                text
            )
        
        # Create segment container
        with st.container():
            # Segment header with click-to-play button
            col1, col2 = st.columns([1, 5])
            
            with col1:
                # Click-to-play button with current playback indicator
                is_current_playback = self._is_current_playback_segment(segment)
                button_text = f"▶️ {self._format_time(start_time)}"
                
                if is_current_playback and st.session_state.get('auto_highlight', False):
                    # Add visual indicator for currently playing segment
                    button_text = f"🔊 {self._format_time(start_time)}"
                
                if st.button(
                    button_text,
                    key=f"play_segment_{segment['id']}",
                    help="Click to jump to this segment",
                    type="primary" if is_current_playback else "secondary"
                ):
                    from enhanced_audio_player import jump_to_audio_time
                    st.session_state.audio_current_time = start_time
                    st.session_state.selected_segment = segment['id']
                    jump_to_audio_time(start_time, auto_play=True)
            
            with col2:
                # Segment metadata
                metadata_parts = []
                
                if show_speakers:
                    metadata_parts.append(f"👤 **{display_speaker}**")
                
                if show_timestamps:
                    time_range = f"{self._format_time(start_time)} - {self._format_time(end_time)}"
                    metadata_parts.append(f"⏰ {time_range}")
                
                if show_confidence:
                    conf_emoji = "🟢" if confidence > 0.9 else "🟡" if confidence > 0.7 else "🔴"
                    metadata_parts.append(f"{conf_emoji} {confidence:.1%}")
                
                if metadata_parts:
                    st.caption(" | ".join(metadata_parts))
            
            # Segment text with optional editing
            if edit_mode:
                # Edit mode: show editable text area
                edited_text = st.text_area(
                    "Edit text",
                    value=text,
                    key=f"edit_segment_{segment['id']}",
                    label_visibility="collapsed",
                    height=60
                )
                
                # Save edited text back to segment
                if edited_text != text:
                    segment['text'] = edited_text
                    segment['edited'] = True
                    if 'edited_segments' not in st.session_state:
                        st.session_state.edited_segments = {}
                    st.session_state.edited_segments[segment['id']] = edited_text
                
                # Show edit indicator
                if segment.get('edited', False):
                    st.caption("✏️ *Edited*")
                    
            elif compact_view:
                # Compact view: text only
                if search_term:
                    st.markdown(display_text, unsafe_allow_html=True)
                else:
                    st.write(text)
            else:
                # Full view: text in a bordered container
                is_current_playback = self._is_current_playback_segment(segment)
                segment_style = self._get_segment_style(
                    is_selected=st.session_state.get('selected_segment') == segment['id'],
                    is_current_playback=is_current_playback,
                    confidence=confidence
                )
                
                # Show edit indicator if segment was edited
                if segment.get('edited', False):
                    segment_style += "border-left-color: #ff9800; border-left-width: 6px;"
                
                if search_term:
                    st.markdown(
                        f'<div style="{segment_style}">{display_text}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'<div style="{segment_style}">{text}</div>',
                        unsafe_allow_html=True
                    )
                
                # Show edit indicator
                if segment.get('edited', False):
                    st.caption("✏️ *Modified*")
            
            # Add some spacing between segments
            if not compact_view:
                st.markdown("<br>", unsafe_allow_html=True)
    
    def _get_segment_style(self, is_selected: bool = False, is_current_playback: bool = False, confidence: float = 0.8) -> str:
        """Get CSS style for segment container"""
        base_style = """
            padding: 10px 15px;
            margin: 5px 0;
            border-radius: 8px;
            border-left: 4px solid;
            background-color: #f8f9fa;
            cursor: pointer;
            transition: all 0.2s ease;
        """
        
        if is_current_playback and st.session_state.get('auto_highlight', False):
            # Highlight currently playing segment
            base_style += """
                background-color: #fff8e1;
                border-left-color: #ffc107;
                box-shadow: 0 2px 8px rgba(255, 193, 7, 0.4);
                animation: pulse-highlight 2s infinite;
            """
        elif is_selected:
            base_style += """
                background-color: #e3f2fd;
                border-left-color: #2196f3;
                box-shadow: 0 2px 4px rgba(33, 150, 243, 0.3);
            """
        elif confidence < 0.7:
            base_style += """
                background-color: #fff3e0;
                border-left-color: #ff9800;
            """
        else:
            base_style += """
                border-left-color: #4caf50;
            """
        
        return base_style
    
    def _get_speaker_display_name(self, speaker: str) -> str:
        """Get display name for speaker, allowing custom names"""
        # Check if user has customized speaker names
        custom_names = st.session_state.get('speaker_names', {})
        display_name = custom_names.get(speaker, speaker)
        
        # If segment already has display_speaker, use that
        if isinstance(speaker, dict) and 'display_speaker' in speaker:
            return speaker['display_speaker']
        
        return display_name
    
    def _format_time(self, seconds: float) -> str:
        """Format time in MM:SS format"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def _jump_to_previous_segment(self):
        """Jump to the previous segment"""
        current_time = st.session_state.get('audio_current_time', 0)
        
        # Find the previous segment
        for i in range(len(self.segments) - 1, -1, -1):
            if self.segments[i]['start_time'] < current_time - 1:  # 1 second buffer
                st.session_state.audio_current_time = self.segments[i]['start_time']
                st.session_state.selected_segment = self.segments[i]['id']
                st.rerun()
                return
        
        # If no previous segment found, go to beginning
        st.session_state.audio_current_time = 0
        st.session_state.selected_segment = self.segments[0]['id'] if self.segments else None
        st.rerun()
    
    def _jump_to_next_segment(self):
        """Jump to the next segment"""
        current_time = st.session_state.get('audio_current_time', 0)
        
        # Find the next segment
        for segment in self.segments:
            if segment['start_time'] > current_time + 1:  # 1 second buffer
                st.session_state.audio_current_time = segment['start_time']
                st.session_state.selected_segment = segment['id']
                st.rerun()
                return
        
        # If no next segment found, stay at current position
        st.info("You're at the last segment")
    
    def _update_current_segment_highlight(self):
        """Update the highlighted segment based on current playback time"""
        current_time = st.session_state.get('audio_current_time', 0)
        
        # Find the segment that should be highlighted based on current time
        for segment in self.segments:
            if (segment['start_time'] <= current_time <= segment['end_time']):
                if st.session_state.get('current_playback_segment') != segment['id']:
                    st.session_state.current_playback_segment = segment['id']
                return
        
        # No segment found for current time
        st.session_state.current_playback_segment = None
    
    def _get_current_segment(self) -> Optional[Dict]:
        """Get the segment that should currently be highlighted"""
        current_time = st.session_state.get('audio_current_time', 0)
        
        for segment in self.segments:
            if segment['start_time'] <= current_time <= segment['end_time']:
                return segment
        
        return None
    
    def _is_current_playback_segment(self, segment: Dict) -> bool:
        """Check if this segment is currently being played"""
        if not st.session_state.get('auto_highlight', False):
            return False
        
        current_time = st.session_state.get('audio_current_time', 0)
        return segment['start_time'] <= current_time <= segment['end_time']
    
    def _save_transcript_changes(self):
        """Save transcript changes to session state and optionally to file"""
        if 'edited_segments' not in st.session_state:
            return
        
        # Update segments with edited text
        for segment in self.segments:
            segment_id = segment.get('id')
            if segment_id in st.session_state.edited_segments:
                segment['text'] = st.session_state.edited_segments[segment_id]
                segment['edited'] = True
        
        # Update the main transcript text
        updated_transcript = []
        for segment in self.segments:
            text = segment.get('text', '').strip()
            if segment.get('speaker') and segment.get('speaker') != 'Unknown':
                updated_transcript.append(f"[{segment['speaker']}] {text}")
            else:
                updated_transcript.append(text)
        
        self.transcript_text = '\n\n'.join(updated_transcript)
        
        # Store in session state for persistence
        if 'saved_transcript_edits' not in st.session_state:
            st.session_state.saved_transcript_edits = {}
        
        st.session_state.saved_transcript_edits = {
            'transcript': self.transcript_text,
            'segments': self.segments.copy(),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Saved transcript changes: {len(st.session_state.edited_segments)} segments modified")
    
    def export_edited_transcript(self, format: str = 'txt') -> str:
        """Export the edited transcript in specified format"""
        from export_manager import MultimediaExporter, ExportConfig
        
        if 'saved_transcript_edits' not in st.session_state:
            return self.transcript_text
        
        # Prepare export data
        export_data = {
            'transcript': st.session_state.saved_transcript_edits['transcript'],
            'segments': st.session_state.saved_transcript_edits['segments'],
            'metadata': {
                'edited': True,
                'edit_timestamp': st.session_state.saved_transcript_edits['timestamp'],
                'original_length': len(self.transcript_text),
                'edited_length': len(st.session_state.saved_transcript_edits['transcript'])
            }
        }
        
        # Create exporter and export
        exporter = MultimediaExporter()
        config = ExportConfig(format=format, include_metadata=True)
        
        try:
            file_path = exporter.export_transcript(export_data, config)
            return file_path
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return self.transcript_text


def render_clickable_transcript_ui(transcript_text: str, segments: Optional[List[Dict]] = None, 
                                  audio_file_path: Optional[str] = None):
    """
    Convenience function to render clickable transcript UI
    
    Args:
        transcript_text: The transcript text
        segments: Optional list of segment dictionaries with timing info
        audio_file_path: Optional path to audio file for playback
    """
    try:
        clickable_transcript = ClickableTranscript(transcript_text, segments)
        clickable_transcript.render_clickable_transcript(audio_file_path)
    except Exception as e:
        st.error(f"Error rendering clickable transcript: {str(e)}")
        logger.error(f"Clickable transcript error: {e}")
        
        # Fallback to simple text display
        st.text_area("Transcript (fallback view)", value=transcript_text, height=400)


def create_segments_from_whisper_result(whisper_result: Dict) -> List[Dict]:
    """
    Create segments from Whisper API result
    
    Args:
        whisper_result: Result dictionary from Whisper API
        
    Returns:
        List of segment dictionaries
    """
    segments = []
    
    if 'segments' in whisper_result:
        for i, segment in enumerate(whisper_result['segments']):
            segments.append({
                'id': i,
                'text': segment.get('text', '').strip(),
                'start_time': segment.get('start', 0),
                'end_time': segment.get('end', 0),
                'speaker': f"Speaker {i % 2 + 1}",  # Simple alternating speaker assignment
                'confidence': segment.get('avg_logprob', 0) if 'avg_logprob' in segment else 0.8
            })
    
    return segments


def integrate_with_diarization(segments: List[Dict], diarization_result: Optional[Dict]) -> List[Dict]:
    """
    Integrate segment timing with speaker diarization results
    
    Args:
        segments: List of transcript segments
        diarization_result: Speaker diarization result
        
    Returns:
        Updated segments with speaker information
    """
    if not diarization_result or 'speakers' not in diarization_result:
        return segments
    
    # Simple integration - assign speakers based on timing overlap
    for segment in segments:
        segment_start = segment['start_time']
        segment_end = segment['end_time']
        
        # Find overlapping speaker
        max_overlap = 0
        assigned_speaker = segment.get('speaker', 'Unknown')
        
        for speaker_info in diarization_result['speakers']:
            speaker_start = speaker_info.get('start', 0)
            speaker_end = speaker_info.get('end', 0)
            
            # Calculate overlap
            overlap_start = max(segment_start, speaker_start)
            overlap_end = min(segment_end, speaker_end)
            overlap = max(0, overlap_end - overlap_start)
            
            if overlap > max_overlap:
                max_overlap = overlap
                assigned_speaker = speaker_info.get('speaker', assigned_speaker)
        
        segment['speaker'] = assigned_speaker
    
    return segments