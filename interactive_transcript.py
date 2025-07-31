#!/usr/bin/env python3
"""
Interactive Transcript Component
Provides clickable transcripts with audio playback synchronization and advanced features
"""

import streamlit as st
import logging
from typing import List, Dict, Optional, Tuple, Any
import json
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TranscriptSegment:
    """Data class for transcript segments with timing"""
    text: str
    start_time: float
    end_time: float
    speaker: str = "Unknown"
    confidence: float = 1.0
    
    def duration(self) -> float:
        return self.end_time - self.start_time

class InteractiveTranscript:
    """Interactive transcript with clickable segments and audio sync"""
    
    def __init__(self, transcript_text: str, timestamps: Optional[List[Dict]] = None):
        self.transcript_text = transcript_text
        self.timestamps = timestamps or []
        self.segments = self._create_segments()
    
    def _create_segments(self) -> List[Dict]:
        """Create clickable segments from transcript and timestamps"""
        if not self.timestamps:
            # Create basic segments from sentences if no timestamps
            sentences = self.transcript_text.split('.')
            segments = []
            for i, sentence in enumerate(sentences):
                if sentence.strip():
                    segments.append({
                        'id': i,
                        'text': sentence.strip() + '.',
                        'start': i * 3.0,  # Estimated timing
                        'end': (i + 1) * 3.0,
                        'confidence': 0.8
                    })
            return segments
        
        # Use actual timestamps
        segments = []
        for i, timestamp in enumerate(self.timestamps):
            segments.append({
                'id': i,
                'text': timestamp.get('text', ''),
                'start': timestamp.get('start', 0),
                'end': timestamp.get('end', 0),
                'confidence': timestamp.get('confidence', 0.8),
                'words': timestamp.get('words', [])
            })
        
        return segments
    
    def render_interactive_transcript(self, audio_file_path: Optional[str] = None):
        """Render interactive transcript with clickable segments"""
        st.subheader("🎯 Interactive Transcript")
        
        if not self.segments:
            st.warning("No transcript segments available")
            return
        
        # Audio player if file is provided
        if audio_file_path:
            try:
                with open(audio_file_path, "rb") as audio_file:
                    audio_bytes = audio_file.read()
                    st.audio(audio_bytes, format="audio/wav")
            except Exception as e:
                logger.warning(f"Could not load audio file: {e}")
        
        # Transcript controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            show_timestamps = st.checkbox("Show Timestamps", value=True)
        with col2:
            show_confidence = st.checkbox("Show Confidence", value=False)
        with col3:
            highlight_low_confidence = st.checkbox("Highlight Low Confidence", value=True)
        
        # Search functionality
        search_term = st.text_input("🔍 Search in transcript", placeholder="Enter text to search...")
        
        # Render segments
        st.markdown("---")
        st.markdown("**Click on any segment to jump to that part of the audio:**")
        
        for segment in self.segments:
            self._render_segment(
                segment, 
                show_timestamps, 
                show_confidence, 
                highlight_low_confidence,
                search_term
            )
    
    def _render_segment(self, segment: Dict, show_timestamps: bool, show_confidence: bool, 
                       highlight_low_confidence: bool, search_term: str = ""):
        """Render individual transcript segment"""
        text = segment.get('text', '')
        start_time = segment.get('start', 0)
        end_time = segment.get('end', 0)
        confidence = segment.get('confidence', 0.8)
        
        # Skip empty segments
        if not text.strip():
            return
        
        # Highlight search terms
        display_text = text
        if search_term and search_term.lower() in text.lower():
            display_text = text.replace(
                search_term, 
                f"**{search_term}**"
            )
        
        # Determine styling based on confidence
        confidence_class = ""
        if highlight_low_confidence and confidence < 0.6:
            confidence_class = "🔴"  # Low confidence
        elif confidence > 0.9:
            confidence_class = "🟢"  # High confidence
        else:
            confidence_class = "🟡"  # Medium confidence
        
        # Create segment container
        with st.container():
            col1, col2 = st.columns([4, 1])
            
            with col1:
                # Main text with optional highlighting
                if highlight_low_confidence and confidence < 0.6:
                    st.markdown(f"⚠️ {display_text}")
                else:
                    st.markdown(display_text)
                
                # Show word-level details if available
                if 'words' in segment and segment['words']:
                    with st.expander(f"Word details ({len(segment['words'])} words)", expanded=False):
                        self._render_word_details(segment['words'])
            
            with col2:
                # Timestamp and confidence info
                if show_timestamps:
                    st.caption(f"⏱️ {self._format_time(start_time)} - {self._format_time(end_time)}")
                
                if show_confidence:
                    st.caption(f"{confidence_class} {confidence:.2f}")
                
                # Jump button (placeholder - would need audio player integration)
                if st.button(f"▶️", key=f"play_{segment['id']}", help=f"Jump to {self._format_time(start_time)}"):
                    st.info(f"🎵 Would jump to {self._format_time(start_time)}")
                    # In a real implementation, this would control audio playback
        
        st.markdown("---")
    
    def _render_word_details(self, words: List[Dict]):
        """Render word-level timestamp details"""
        for word_data in words:
            word = word_data.get('word', '')
            start = word_data.get('start', 0)
            end = word_data.get('end', 0)
            confidence = word_data.get('confidence', 0.8)
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{word}**")
            with col2:
                st.caption(f"{self._format_time(start)}-{self._format_time(end)}")
            with col3:
                confidence_emoji = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.6 else "🔴"
                st.caption(f"{confidence_emoji} {confidence:.2f}")
    
    def _format_time(self, seconds: float) -> str:
        """Format time in MM:SS format"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_transcript_statistics(self) -> Dict:
        """Get statistics about the transcript"""
        if not self.segments:
            return {}
        
        total_duration = max(segment.get('end', 0) for segment in self.segments)
        total_words = sum(len(segment.get('text', '').split()) for segment in self.segments)
        avg_confidence = sum(segment.get('confidence', 0.8) for segment in self.segments) / len(self.segments)
        
        low_confidence_segments = sum(1 for segment in self.segments if segment.get('confidence', 0.8) < 0.6)
        
        return {
            'total_segments': len(self.segments),
            'total_duration': total_duration,
            'total_words': total_words,
            'average_confidence': avg_confidence,
            'low_confidence_segments': low_confidence_segments,
            'words_per_minute': (total_words / total_duration * 60) if total_duration > 0 else 0
        }
    
    def export_transcript_formats(self) -> Dict[str, str]:
        """Export transcript in various formats"""
        formats = {}
        
        # Plain text
        formats['plain_text'] = self.transcript_text
        
        # SRT subtitle format
        srt_content = ""
        for i, segment in enumerate(self.segments, 1):
            start_time = self._format_srt_time(segment.get('start', 0))
            end_time = self._format_srt_time(segment.get('end', 0))
            text = segment.get('text', '').strip()
            
            srt_content += f"{i}\n{start_time} --> {end_time}\n{text}\n\n"
        
        formats['srt'] = srt_content
        
        # VTT format
        vtt_content = "WEBVTT\n\n"
        for segment in self.segments:
            start_time = self._format_vtt_time(segment.get('start', 0))
            end_time = self._format_vtt_time(segment.get('end', 0))
            text = segment.get('text', '').strip()
            
            vtt_content += f"{start_time} --> {end_time}\n{text}\n\n"
        
        formats['vtt'] = vtt_content
        
        # JSON format with full data
        formats['json'] = json.dumps({
            'transcript': self.transcript_text,
            'segments': self.segments,
            'statistics': self.get_transcript_statistics()
        }, indent=2)
        
        return formats
    
    def _format_srt_time(self, seconds: float) -> str:
        """Format time for SRT subtitle format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def _format_vtt_time(self, seconds: float) -> str:
        """Format time for VTT subtitle format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

def create_interactive_transcript(transcript_text: str, timestamps: Optional[List[Dict]] = None) -> InteractiveTranscript:
    """Factory function to create interactive transcript"""
    return InteractiveTranscript(transcript_text, timestamps)

def render_transcript_with_audio_sync(transcript_text: str, timestamps: Optional[List[Dict]] = None, 
                                    audio_file_path: Optional[str] = None):
    """Render interactive transcript with audio synchronization"""
    interactive_transcript = create_interactive_transcript(transcript_text, timestamps)
    interactive_transcript.render_interactive_transcript(audio_file_path)
    
    # Show statistics
    stats = interactive_transcript.get_transcript_statistics()
    if stats:
        st.markdown("### 📊 Transcript Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Segments", stats.get('total_segments', 0))
        with col2:
            st.metric("Duration", f"{stats.get('total_duration', 0):.1f}s")
        with col3:
            st.metric("Words/Min", f"{stats.get('words_per_minute', 0):.0f}")
        with col4:
            confidence = stats.get('average_confidence', 0)
            st.metric("Avg Confidence", f"{confidence:.2f}")
    
    # Export options
    with st.expander("📥 Export Transcript", expanded=False):
        formats = interactive_transcript.export_transcript_formats()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                "📄 Download as SRT",
                data=formats['srt'],
                file_name="transcript.srt",
                mime="text/plain"
            )
            
            st.download_button(
                "📄 Download as VTT",
                data=formats['vtt'],
                file_name="transcript.vtt",
                mime="text/plain"
            )
        
        with col2:
            st.download_button(
                "📄 Download as JSON",
                data=formats['json'],
                file_name="transcript.json",
                mime="application/json"
            )
            
            st.download_button(
                "📄 Download as TXT",
                data=formats['plain_text'],
                file_name="transcript.txt",
                mime="text/plain"
            )
c
lass AdvancedTranscriptUI:
    """Advanced transcript UI with language detection and editing features"""
    
    def __init__(self):
        self.supported_languages = {
            'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
            'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese',
            'ko': 'Korean', 'zh': 'Chinese', 'ar': 'Arabic', 'hi': 'Hindi',
            'nl': 'Dutch', 'sv': 'Swedish', 'da': 'Danish', 'no': 'Norwegian'
        }
    
    def render_language_selector(self, detected_languages: List[Dict] = None) -> Optional[str]:
        """Render language selection interface"""
        st.markdown("### 🌍 Language Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Auto-detection results
            if detected_languages:
                st.markdown("**Detected Languages:**")
                for lang in detected_languages[:3]:  # Show top 3
                    confidence_bar = "█" * int(lang['confidence'] * 10)
                    st.markdown(f"• {lang['name']}: {confidence_bar} ({lang['confidence']:.1%})")
            else:
                st.info("No language detection results available")
        
        with col2:
            # Manual language selection
            language_options = ['Auto-detect'] + [f"{code} - {name}" for code, name in self.supported_languages.items()]
            
            selected = st.selectbox(
                "Select Language:",
                options=language_options,
                help="Choose the language for transcription, or use auto-detect"
            )
            
            if selected == 'Auto-detect':
                return None
            else:
                return selected.split(' - ')[0]  # Extract language code
    
    def render_transcription_options(self) -> Dict[str, Any]:
        """Render advanced transcription options"""
        st.markdown("### ⚙️ Advanced Options")
        
        col1, col2 = st.columns(2)
        
        options = {}
        
        with col1:
            options['enable_diarization'] = st.checkbox(
                "Speaker Diarization",
                value=True,
                help="Identify and separate different speakers in the audio"
            )
            
            options['enable_timestamps'] = st.checkbox(
                "Word-level Timestamps",
                value=True,
                help="Generate precise timestamps for each word"
            )
            
            options['show_confidence'] = st.checkbox(
                "Show Confidence Scores",
                value=False,
                help="Display confidence scores for transcription quality"
            )
        
        with col2:
            options['enable_editing'] = st.checkbox(
                "Enable Transcript Editing",
                value=False,
                help="Allow manual editing of the transcript"
            )
            
            options['export_format'] = st.selectbox(
                "Export Format:",
                options=['txt', 'json', 'srt', 'vtt', 'csv'],
                help="Choose format for transcript export"
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
    
    def render_processing_status(self, status: Dict[str, Any]) -> None:
        """Render processing status with detailed progress"""
        if not status:
            return
        
        st.markdown("### 🔄 Processing Status")
        
        # Progress indicators
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if status.get('language_detection', False):
                st.success("✅ Language Detection")
            else:
                st.info("🔄 Language Detection")
        
        with col2:
            if status.get('transcription', False):
                st.success("✅ Transcription")
            else:
                st.info("🔄 Transcription")
        
        with col3:
            if status.get('diarization', False):
                st.success("✅ Speaker Diarization")
            else:
                st.info("🔄 Speaker Diarization")
        
        # Detailed status
        if status.get('current_step'):
            st.info(f"Current: {status['current_step']}")
        
        if status.get('progress'):
            st.progress(status['progress'])
    
    def render_quality_metrics(self, result_data: Dict[str, Any]) -> None:
        """Render quality metrics and analysis"""
        if not result_data:
            return
        
        st.markdown("### 📈 Quality Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            overall_confidence = result_data.get('confidence', 0)
            confidence_color = "🟢" if overall_confidence > 0.8 else "🟡" if overall_confidence > 0.6 else "🔴"
            st.metric("Overall Quality", f"{confidence_color} {overall_confidence:.1%}")
        
        with col2:
            speaker_count = result_data.get('speaker_count', 0)
            st.metric("Speakers Detected", speaker_count)
        
        with col3:
            total_duration = result_data.get('total_duration', 0)
            st.metric("Duration", f"{total_duration:.1f}s")
        
        with col4:
            processing_time = result_data.get('processing_time', 0)
            st.metric("Processing Time", f"{processing_time:.1f}s")
        
        # Quality warnings
        if overall_confidence < 0.7:
            st.warning("⚠️ Low transcription confidence detected. Consider:")
            st.markdown("• Improving audio quality")
            st.markdown("• Using a different language model")
            st.markdown("• Manual review of the transcript")

def render_advanced_interactive_transcript(segments_data: List[Dict], 
                                         audio_bytes: Optional[bytes] = None,
                                         show_speakers: bool = True,
                                         show_timestamps: bool = True,
                                         show_confidence: bool = False,
                                         editable: bool = False) -> Dict[str, Any]:
    """
    Render advanced interactive transcript component
    
    Args:
        segments_data: List of segment dictionaries
        audio_bytes: Audio data for playback
        show_speakers: Whether to show speaker labels
        show_timestamps: Whether to show timestamps
        show_confidence: Whether to show confidence scores
        editable: Whether transcript is editable
        
    Returns:
        Dictionary with user interactions and edits
    """
    if not segments_data:
        st.info("No transcript segments available")
        return {}
    
    # Convert segments data to TranscriptSegment objects
    segments = []
    for seg_data in segments_data:
        segment = TranscriptSegment(
            text=seg_data.get('text', ''),
            start_time=seg_data.get('start_time', 0.0),
            end_time=seg_data.get('end_time', 0.0),
            speaker=seg_data.get('speaker', 'Unknown'),
            confidence=seg_data.get('confidence', 1.0)
        )
        segments.append(segment)
    
    # Audio player if audio is provided
    if audio_bytes:
        st.audio(audio_bytes, format="audio/mp3")
    
    # Transcript controls
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        show_speakers = st.checkbox("Show Speakers", value=show_speakers)
    with col2:
        show_timestamps = st.checkbox("Show Timestamps", value=show_timestamps)
    with col3:
        show_confidence = st.checkbox("Show Confidence", value=show_confidence)
    with col4:
        editable = st.checkbox("Enable Editing", value=editable)
    
    # Search functionality
    search_term = st.text_input("🔍 Search in transcript", placeholder="Enter search term...")
    
    # Transcript display
    st.markdown("### 📝 Interactive Transcript")
    
    interactions = {
        'clicked_segments': [],
        'edited_segments': [],
        'search_results': []
    }
    
    # Create scrollable transcript container
    transcript_container = st.container()
    
    with transcript_container:
        for i, segment in enumerate(segments):
            # Check if segment matches search
            is_search_match = (search_term.lower() in segment.text.lower() 
                             if search_term else False)
            
            if is_search_match:
                interactions['search_results'].append(i)
            
            # Segment styling based on state
            if is_search_match:
                segment_style = "background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 5px 0; border-radius: 5px;"
            else:
                segment_style = "border-left: 3px solid #007bff; padding: 10px; margin: 5px 0; border-radius: 5px;"
            
            with st.container():
                st.markdown(f'<div style="{segment_style}">', unsafe_allow_html=True)
                
                # Segment header with controls
                header_cols = st.columns([1, 3, 1] if show_timestamps else [1, 4])
                
                with header_cols[0]:
                    # Play button for segment
                    if st.button(f"▶️", key=f"play_{i}", help=f"Play from {_format_time(segment.start_time)}"):
                        interactions['clicked_segments'].append({
                            'index': i,
                            'action': 'play',
                            'timestamp': segment.start_time
                        })
                
                with header_cols[1]:
                    # Speaker and timestamp info
                    info_parts = []
                    if show_speakers:
                        info_parts.append(f"**{segment.speaker}**")
                    if show_timestamps:
                        time_str = f"{_format_time(segment.start_time)} - {_format_time(segment.end_time)}"
                        info_parts.append(f"*{time_str}*")
                    if show_confidence:
                        conf_color = _get_confidence_color(segment.confidence)
                        info_parts.append(f'<span style="color: {conf_color}">({segment.confidence:.2f})</span>')
                    
                    if info_parts:
                        st.markdown(" | ".join(info_parts), unsafe_allow_html=True)
                
                if show_timestamps and len(header_cols) > 2:
                    with header_cols[2]:
                        # Duration info
                        st.caption(f"({segment.duration():.1f}s)")
                
                # Segment text (editable if enabled)
                if editable:
                    edited_text = st.text_area(
                        f"Edit segment {i+1}:",
                        value=segment.text,
                        key=f"edit_{i}",
                        height=60,
                        label_visibility="collapsed"
                    )
                    
                    if edited_text != segment.text:
                        interactions['edited_segments'].append({
                            'index': i,
                            'original_text': segment.text,
                            'edited_text': edited_text
                        })
                else:
                    # Display text with highlighting for search
                    display_text = segment.text
                    if search_term and is_search_match:
                        # Highlight search term
                        highlighted_text = display_text.replace(
                            search_term, 
                            f'<mark style="background-color: #ffeb3b;">{search_term}</mark>'
                        )
                        st.markdown(highlighted_text, unsafe_allow_html=True)
                    else:
                        st.markdown(display_text)
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    # Summary statistics
    if segments:
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_duration = sum(seg.duration() for seg in segments)
            st.metric("Total Duration", f"{total_duration:.1f}s")
        
        with col2:
            total_words = sum(len(seg.text.split()) for seg in segments)
            st.metric("Total Words", total_words)
        
        with col3:
            unique_speakers = len(set(seg.speaker for seg in segments))
            st.metric("Speakers", unique_speakers)
        
        with col4:
            avg_confidence = sum(seg.confidence for seg in segments) / len(segments)
            st.metric("Avg Confidence", f"{avg_confidence:.2f}")
    
    return interactions

def render_speaker_timeline(segments_data: List[Dict]) -> None:
    """Render visual timeline showing speaker segments"""
    if not segments_data:
        return
    
    st.markdown("### 👥 Speaker Timeline")
    
    # Convert to segments
    segments = [TranscriptSegment(
        text=seg.get('text', ''),
        start_time=seg.get('start_time', 0.0),
        end_time=seg.get('end_time', 0.0),
        speaker=seg.get('speaker', 'Unknown'),
        confidence=seg.get('confidence', 1.0)
    ) for seg in segments_data]
    
    # Get unique speakers and assign colors
    speakers = list(set(seg.speaker for seg in segments))
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
    speaker_colors = {speaker: colors[i % len(colors)] for i, speaker in enumerate(speakers)}
    
    # Create timeline visualization
    total_duration = max(seg.end_time for seg in segments) if segments else 0
    
    # Timeline container
    timeline_html = '<div style="position: relative; height: 100px; background: #f0f0f0; border-radius: 5px; margin: 10px 0;">'
    
    for segment in segments:
        # Calculate position and width as percentages
        start_percent = (segment.start_time / total_duration) * 100
        width_percent = (segment.duration() / total_duration) * 100
        
        color = speaker_colors.get(segment.speaker, '#cccccc')
        
        timeline_html += f'''
        <div style="
            position: absolute;
            left: {start_percent}%;
            width: {width_percent}%;
            height: 60px;
            top: 20px;
            background: {color};
            border: 1px solid #fff;
            border-radius: 3px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            color: white;
            text-shadow: 1px 1px 1px rgba(0,0,0,0.5);
        " title="{segment.speaker}: {segment.text[:50]}...">
            {segment.speaker}
        </div>
        '''
    
    timeline_html += '</div>'
    
    st.markdown(timeline_html, unsafe_allow_html=True)
    
    # Speaker legend
    legend_cols = st.columns(len(speakers))
    for i, speaker in enumerate(speakers):
        with legend_cols[i]:
            color = speaker_colors[speaker]
            st.markdown(f'<div style="display: flex; align-items: center;"><div style="width: 20px; height: 20px; background: {color}; border-radius: 3px; margin-right: 10px;"></div>{speaker}</div>', unsafe_allow_html=True)

def render_confidence_analysis(segments_data: List[Dict]) -> None:
    """Render confidence score analysis"""
    if not segments_data:
        return
    
    st.markdown("### 📊 Confidence Analysis")
    
    # Convert to segments
    segments = [TranscriptSegment(
        text=seg.get('text', ''),
        start_time=seg.get('start_time', 0.0),
        end_time=seg.get('end_time', 0.0),
        speaker=seg.get('speaker', 'Unknown'),
        confidence=seg.get('confidence', 1.0)
    ) for seg in segments_data]
    
    # Calculate confidence statistics
    confidences = [seg.confidence for seg in segments]
    avg_confidence = sum(confidences) / len(confidences)
    min_confidence = min(confidences)
    max_confidence = max(confidences)
    
    # Confidence distribution
    low_conf_count = sum(1 for c in confidences if c < 0.7)
    med_conf_count = sum(1 for c in confidences if 0.7 <= c < 0.9)
    high_conf_count = sum(1 for c in confidences if c >= 0.9)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Average", f"{avg_confidence:.3f}")
    with col2:
        st.metric("Range", f"{min_confidence:.3f} - {max_confidence:.3f}")
    with col3:
        st.metric("Low Confidence", f"{low_conf_count} segments")
    with col4:
        st.metric("High Confidence", f"{high_conf_count} segments")
    
    # Show segments with low confidence
    if low_conf_count > 0:
        with st.expander(f"⚠️ Low Confidence Segments ({low_conf_count})"):
            for i, segment in enumerate(segments):
                if segment.confidence < 0.7:
                    st.markdown(f"**Segment {i+1}** (Confidence: {segment.confidence:.3f})")
                    st.markdown(f"*{_format_time(segment.start_time)} - {_format_time(segment.end_time)}*")
                    st.markdown(f"**{segment.speaker}:** {segment.text}")
                    st.markdown("---")

def render_advanced_transcript_ui(detected_languages: List[Dict] = None,
                                 processing_status: Dict[str, Any] = None,
                                 result_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Render complete advanced transcript UI
    
    Args:
        detected_languages: Language detection results
        processing_status: Current processing status
        result_data: Transcription result data
        
    Returns:
        Dictionary with user selections and options
    """
    ui = AdvancedTranscriptUI()
    
    # Language selection
    selected_language = ui.render_language_selector(detected_languages)
    
    # Transcription options
    options = ui.render_transcription_options()
    options['selected_language'] = selected_language
    
    # Processing status
    if processing_status:
        ui.render_processing_status(processing_status)
    
    # Quality metrics
    if result_data:
        ui.render_quality_metrics(result_data)
    
    return options

def _format_time(seconds: float) -> str:
    """Format time as MM:SS"""
    minutes = int(seconds // 60)
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:05.2f}"

def _get_confidence_color(confidence: float) -> str:
    """Get color based on confidence score"""
    if confidence >= 0.9:
        return "#28a745"  # Green
    elif confidence >= 0.7:
        return "#ffc107"  # Yellow
    else:
        return "#dc3545"  # Red

# Global instances
_advanced_ui = None

def get_advanced_transcript_ui() -> AdvancedTranscriptUI:
    """Get or create global advanced transcript UI instance"""
    global _advanced_ui
    if _advanced_ui is None:
        _advanced_ui = AdvancedTranscriptUI()
    return _advanced_ui