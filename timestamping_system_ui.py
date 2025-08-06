"""
Streamlit UI for Comprehensive Timestamping System

This module provides the user interface for:
- Word-level timestamp visualization
- Segment navigation and management
- Clickable transcript with audio synchronization
- Bookmark creation and management
- Time code navigation

Requirements: 3.1, 7.4
"""

import streamlit as st
import json
import time
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Any
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Import the timestamping system
from timestamping_system import (
    TimestampingSystem, WordTimestamp, SegmentTimestamp, 
    TimeCode, Bookmark, TranscriptSegment
)

class TimestampingSystemUI:
    """Streamlit UI for the Timestamping System"""
    
    def __init__(self):
        self.ts_system = TimestampingSystem()
        
        # Initialize session state
        if 'current_audio_time' not in st.session_state:
            st.session_state.current_audio_time = 0.0
        if 'selected_content_id' not in st.session_state:
            st.session_state.selected_content_id = None
        if 'bookmarks' not in st.session_state:
            st.session_state.bookmarks = []
        if 'word_timestamps' not in st.session_state:
            st.session_state.word_timestamps = []
        if 'segment_timestamps' not in st.session_state:
            st.session_state.segment_timestamps = []
        if 'transcript_segments' not in st.session_state:
            st.session_state.transcript_segments = []
    
    def render_main_interface(self):
        """Render the main timestamping interface"""
        st.title("🕒 Comprehensive Timestamping System")
        st.markdown("Advanced timestamp management with word-level precision and audio synchronization")
        
        # Sidebar for content selection and controls
        with st.sidebar:
            self.render_content_selector()
            self.render_audio_controls()
            self.render_bookmark_manager()
        
        # Main content area
        if st.session_state.selected_content_id:
            self.render_timestamp_interface()
        else:
            self.render_welcome_screen()
    
    def render_content_selector(self):
        """Render content selection interface"""
        st.subheader("📁 Content Selection")
        
        # Content ID input
        content_id = st.text_input(
            "Content ID",
            value=st.session_state.selected_content_id or "",
            help="Enter the unique identifier for your audio/video content"
        )
        
        if content_id and content_id != st.session_state.selected_content_id:
            st.session_state.selected_content_id = content_id
            self.load_content_data(content_id)
        
        # File upload for new content
        st.subheader("📤 Upload New Content")
        uploaded_file = st.file_uploader(
            "Choose audio/video file",
            type=['mp3', 'wav', 'm4a', 'mp4', 'avi', 'mov'],
            help="Upload audio or video file for timestamp generation"
        )
        
        if uploaded_file:
            self.handle_file_upload(uploaded_file)
    
    def render_audio_controls(self):
        """Render audio playback controls"""
        st.subheader("🎵 Audio Controls")
        
        # Current time display
        current_time = st.session_state.current_audio_time
        formatted_time = self.format_time(current_time)
        st.metric("Current Time", formatted_time)
        
        # Time navigation
        if st.session_state.word_timestamps:
            max_time = max(w['end_time'] for w in st.session_state.word_timestamps)
            new_time = st.slider(
                "Seek to time",
                min_value=0.0,
                max_value=max_time,
                value=current_time,
                step=0.1,
                format="%.1fs"
            )
            
            if new_time != current_time:
                st.session_state.current_audio_time = new_time
                st.rerun()
        
        # Quick navigation buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⏪ -10s"):
                st.session_state.current_audio_time = max(0, current_time - 10)
                st.rerun()
        
        with col2:
            if st.button("⏸️ Pause"):
                st.info("Audio paused")
        
        with col3:
            if st.button("⏩ +10s"):
                st.session_state.current_audio_time = current_time + 10
                st.rerun()
    
    def render_bookmark_manager(self):
        """Render bookmark management interface"""
        st.subheader("🔖 Bookmarks")
        
        # Create new bookmark
        with st.expander("➕ Add Bookmark"):
            bookmark_title = st.text_input("Bookmark Title")
            bookmark_desc = st.text_area("Description (optional)")
            bookmark_tags = st.text_input("Tags (comma-separated)")
            
            if st.button("Create Bookmark"):
                if bookmark_title and st.session_state.selected_content_id:
                    tags = [tag.strip() for tag in bookmark_tags.split(',') if tag.strip()]
                    
                    bookmark = self.ts_system.create_bookmark(
                        content_id=st.session_state.selected_content_id,
                        timestamp=st.session_state.current_audio_time,
                        title=bookmark_title,
                        description=bookmark_desc or None,
                        tags=tags,
                        user_id="current_user"
                    )
                    
                    st.success(f"Bookmark created at {self.format_time(bookmark.timestamp)}")
                    self.load_bookmarks()
                    st.rerun()
        
        # Display existing bookmarks
        if st.session_state.bookmarks:
            st.write("**Existing Bookmarks:**")
            for bookmark in st.session_state.bookmarks:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**{bookmark['title']}**")
                        st.write(f"⏰ {self.format_time(bookmark['timestamp'])}")
                        if bookmark['description']:
                            st.write(f"📝 {bookmark['description']}")
                        if bookmark['tags']:
                            st.write(f"🏷️ {', '.join(bookmark['tags'])}")
                    
                    with col2:
                        if st.button("Go", key=f"goto_{bookmark['id']}"):
                            st.session_state.current_audio_time = bookmark['timestamp']
                            st.rerun()
                    
                    st.divider()
    
    def render_timestamp_interface(self):
        """Render the main timestamp interface"""
        content_id = st.session_state.selected_content_id
        
        # Tabs for different views
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📝 Clickable Transcript", 
            "📊 Timeline View", 
            "🔍 Word Analysis", 
            "📑 Segments", 
            "📤 Export"
        ])
        
        with tab1:
            self.render_clickable_transcript()
        
        with tab2:
            self.render_timeline_view()
        
        with tab3:
            self.render_word_analysis()
        
        with tab4:
            self.render_segment_view()
        
        with tab5:
            self.render_export_interface()
    
    def render_clickable_transcript(self):
        """Render clickable transcript with audio synchronization"""
        st.subheader("📝 Interactive Transcript")
        
        if not st.session_state.transcript_segments:
            st.info("No transcript segments available. Upload content to generate timestamps.")
            return
        
        # Current word highlight
        current_time = st.session_state.current_audio_time
        current_word = self.get_current_word(current_time)
        
        if current_word:
            st.info(f"🎯 Currently speaking: **{current_word['word']}** "
                   f"({self.format_time(current_word['start_time'])} - "
                   f"{self.format_time(current_word['end_time'])})")
        
        # Render transcript segments
        for i, segment in enumerate(st.session_state.transcript_segments):
            # Highlight current segment
            is_current = (segment['start_time'] <= current_time <= segment['end_time'])
            
            with st.container():
                if is_current:
                    st.markdown(f"""
                    <div style="background-color: #e6f3ff; padding: 10px; border-radius: 5px; border-left: 4px solid #0066cc;">
                        <strong>🔊 {segment['text']}</strong><br>
                        <small>⏰ {self.format_time(segment['start_time'])} - {self.format_time(segment['end_time'])}</small>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        # Clickable text
                        if st.button(
                            f"{segment['text'][:100]}..." if len(segment['text']) > 100 else segment['text'],
                            key=f"segment_{i}",
                            help=f"Click to jump to {self.format_time(segment['start_time'])}"
                        ):
                            st.session_state.current_audio_time = segment['start_time']
                            st.rerun()
                    
                    with col2:
                        st.caption(f"⏰ {self.format_time(segment['start_time'])}")
                
                # Word-level navigation within segment
                if is_current and 'words' in segment:
                    with st.expander("🔍 Word-level Navigation"):
                        word_cols = st.columns(min(len(segment['words']), 5))
                        
                        for j, word in enumerate(segment['words'][:5]):  # Show first 5 words
                            with word_cols[j]:
                                if st.button(
                                    word['word'],
                                    key=f"word_{i}_{j}",
                                    help=f"Jump to {self.format_time(word['start_time'])}"
                                ):
                                    st.session_state.current_audio_time = word['start_time']
                                    st.rerun()
                
                st.divider()
    
    def render_timeline_view(self):
        """Render timeline visualization"""
        st.subheader("📊 Timeline Visualization")
        
        if not st.session_state.word_timestamps:
            st.info("No timestamp data available.")
            return
        
        # Create timeline chart
        fig = self.create_timeline_chart()
        st.plotly_chart(fig, use_container_width=True)
        
        # Timeline controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            zoom_level = st.selectbox(
                "Zoom Level",
                ["Full", "Current Minute", "Current 10 seconds"],
                help="Adjust timeline zoom level"
            )
        
        with col2:
            show_confidence = st.checkbox(
                "Show Confidence",
                value=True,
                help="Display confidence scores for timestamps"
            )
        
        with col3:
            show_speakers = st.checkbox(
                "Show Speakers",
                value=True,
                help="Highlight different speakers"
            )
        
        # Update chart based on controls
        if zoom_level != "Full":
            current_time = st.session_state.current_audio_time
            if zoom_level == "Current Minute":
                start_time = max(0, current_time - 30)
                end_time = current_time + 30
            else:  # Current 10 seconds
                start_time = max(0, current_time - 5)
                end_time = current_time + 5
            
            fig.update_xaxes(range=[start_time, end_time])
            st.plotly_chart(fig, use_container_width=True)
    
    def render_word_analysis(self):
        """Render word-level analysis interface"""
        st.subheader("🔍 Word-Level Analysis")
        
        if not st.session_state.word_timestamps:
            st.info("No word timestamp data available.")
            return
        
        # Word statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_words = len(st.session_state.word_timestamps)
            st.metric("Total Words", total_words)
        
        with col2:
            avg_confidence = sum(w['confidence'] for w in st.session_state.word_timestamps) / total_words
            st.metric("Avg Confidence", f"{avg_confidence:.2f}")
        
        with col3:
            total_duration = max(w['end_time'] for w in st.session_state.word_timestamps)
            words_per_minute = (total_words / total_duration) * 60
            st.metric("Words/Minute", f"{words_per_minute:.1f}")
        
        with col4:
            low_confidence_words = sum(1 for w in st.session_state.word_timestamps if w['confidence'] < 0.7)
            st.metric("Low Confidence", low_confidence_words)
        
        # Word search and navigation
        st.subheader("🔍 Word Search")
        search_term = st.text_input("Search for word or phrase")
        
        if search_term:
            matching_words = [
                w for w in st.session_state.word_timestamps 
                if search_term.lower() in w['word'].lower()
            ]
            
            if matching_words:
                st.write(f"Found {len(matching_words)} matches:")
                
                for word in matching_words[:10]:  # Show first 10 matches
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**{word['word']}**")
                    
                    with col2:
                        st.write(f"⏰ {self.format_time(word['start_time'])}")
                        st.write(f"🎯 Confidence: {word['confidence']:.2f}")
                    
                    with col3:
                        if st.button("Go", key=f"search_{word['start_time']}"):
                            st.session_state.current_audio_time = word['start_time']
                            st.rerun()
            else:
                st.info("No matches found.")
        
        # Confidence analysis
        st.subheader("📊 Confidence Analysis")
        
        confidence_data = pd.DataFrame(st.session_state.word_timestamps)
        
        # Confidence histogram
        fig_hist = px.histogram(
            confidence_data, 
            x='confidence',
            bins=20,
            title="Word Confidence Distribution"
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Low confidence words table
        low_conf_threshold = st.slider("Low Confidence Threshold", 0.0, 1.0, 0.7, 0.1)
        low_conf_words = confidence_data[confidence_data['confidence'] < low_conf_threshold]
        
        if not low_conf_words.empty:
            st.write(f"**Words with confidence < {low_conf_threshold}:**")
            st.dataframe(
                low_conf_words[['word', 'start_time', 'end_time', 'confidence']],
                use_container_width=True
            )
    
    def render_segment_view(self):
        """Render segment management interface"""
        st.subheader("📑 Segment Management")
        
        if not st.session_state.segment_timestamps:
            st.info("No segment data available.")
            return
        
        # Segment statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_segments = len(st.session_state.segment_timestamps)
            st.metric("Total Segments", total_segments)
        
        with col2:
            segment_types = set(s['segment_type'] for s in st.session_state.segment_timestamps)
            st.metric("Segment Types", len(segment_types))
        
        with col3:
            avg_duration = sum(
                s['end_time'] - s['start_time'] 
                for s in st.session_state.segment_timestamps
            ) / total_segments
            st.metric("Avg Duration", f"{avg_duration:.1f}s")
        
        # Segment filter
        segment_type_filter = st.selectbox(
            "Filter by Type",
            ["All"] + list(segment_types),
            help="Filter segments by type"
        )
        
        # Display segments
        filtered_segments = st.session_state.segment_timestamps
        if segment_type_filter != "All":
            filtered_segments = [
                s for s in st.session_state.segment_timestamps 
                if s['segment_type'] == segment_type_filter
            ]
        
        for i, segment in enumerate(filtered_segments):
            with st.expander(
                f"{segment['segment_type'].title()} - {self.format_time(segment['start_time'])} "
                f"({segment['end_time'] - segment['start_time']:.1f}s)"
            ):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Content:** {segment['content'][:200]}...")
                    st.write(f"**Duration:** {segment['end_time'] - segment['start_time']:.1f} seconds")
                    st.write(f"**Confidence:** {segment['confidence']:.2f}")
                    
                    if segment.get('speaker_id'):
                        st.write(f"**Speaker:** {segment['speaker_id']}")
                    
                    if segment.get('topic'):
                        st.write(f"**Topic:** {segment['topic']}")
                
                with col2:
                    if st.button("Jump to Start", key=f"seg_start_{i}"):
                        st.session_state.current_audio_time = segment['start_time']
                        st.rerun()
                    
                    if st.button("Jump to End", key=f"seg_end_{i}"):
                        st.session_state.current_audio_time = segment['end_time']
                        st.rerun()
    
    def render_export_interface(self):
        """Render export interface"""
        st.subheader("📤 Export Timestamps")
        
        if not st.session_state.selected_content_id:
            st.info("Select content to export timestamps.")
            return
        
        # Export format selection
        export_format = st.selectbox(
            "Export Format",
            ["JSON", "SRT", "VTT", "ELAN", "CSV"],
            help="Choose export format for timestamps"
        )
        
        # Export options
        col1, col2 = st.columns(2)
        
        with col1:
            include_words = st.checkbox("Include Word Timestamps", value=True)
            include_segments = st.checkbox("Include Segments", value=True)
        
        with col2:
            include_bookmarks = st.checkbox("Include Bookmarks", value=True)
            include_confidence = st.checkbox("Include Confidence Scores", value=True)
        
        # Export button
        if st.button("📥 Export Timestamps"):
            try:
                content_id = st.session_state.selected_content_id
                
                if export_format.lower() == "csv":
                    # Create CSV export
                    export_data = self.create_csv_export(
                        content_id, include_words, include_segments, 
                        include_bookmarks, include_confidence
                    )
                    
                    st.download_button(
                        label="Download CSV",
                        data=export_data,
                        file_name=f"{content_id}_timestamps.csv",
                        mime="text/csv"
                    )
                else:
                    # Use timestamping system export
                    export_data = self.ts_system.export_timestamps(
                        content_id, 
                        export_format.lower()
                    )
                    
                    if export_data:
                        file_extension = export_format.lower()
                        mime_type = {
                            'json': 'application/json',
                            'srt': 'text/plain',
                            'vtt': 'text/vtt',
                            'elan': 'application/xml'
                        }.get(file_extension, 'text/plain')
                        
                        st.download_button(
                            label=f"Download {export_format.upper()}",
                            data=export_data,
                            file_name=f"{content_id}_timestamps.{file_extension}",
                            mime=mime_type
                        )
                        
                        st.success(f"Export ready! Click the download button above.")
                    else:
                        st.error("Export failed. Please try again.")
                        
            except Exception as e:
                st.error(f"Export error: {str(e)}")
        
        # Preview export data
        if st.checkbox("Preview Export Data"):
            try:
                content_id = st.session_state.selected_content_id
                preview_data = self.ts_system.export_timestamps(content_id, "json")
                
                if preview_data:
                    st.code(preview_data[:1000] + "..." if len(preview_data) > 1000 else preview_data)
                else:
                    st.info("No data to preview.")
                    
            except Exception as e:
                st.error(f"Preview error: {str(e)}")
    
    def render_welcome_screen(self):
        """Render welcome screen when no content is selected"""
        st.markdown("""
        ## Welcome to the Comprehensive Timestamping System! 🕒
        
        This advanced system provides:
        
        ### 🎯 **Word-Level Precision**
        - Precise word-level timestamps with confidence scoring
        - Multiple alignment methods (forced alignment, VAD-based, ML-based)
        - Real-time word highlighting during playback
        
        ### 📑 **Intelligent Segmentation**
        - Speaker-based segmentation with diarization
        - Topic-based content organization
        - Automatic chapter detection
        
        ### 🔖 **Smart Bookmarking**
        - Create bookmarks at important moments
        - Tag and categorize bookmarks
        - Quick navigation to bookmarked sections
        
        ### 📝 **Interactive Transcripts**
        - Clickable transcript with audio synchronization
        - Real-time highlighting of current words
        - Seamless navigation between text and audio
        
        ### 📊 **Advanced Analytics**
        - Confidence analysis and quality metrics
        - Speaking pattern analysis
        - Timeline visualization
        
        ### 📤 **Multiple Export Formats**
        - JSON, SRT, VTT, ELAN, CSV formats
        - Customizable export options
        - Professional subtitle generation
        
        ---
        
        **To get started:**
        1. Select a Content ID in the sidebar
        2. Or upload a new audio/video file
        3. Generate timestamps and explore the features!
        """)
    
    # Helper methods
    def load_content_data(self, content_id: str):
        """Load all timestamp data for a content ID"""
        try:
            # This would typically load from the database
            # For now, we'll use placeholder data
            st.session_state.word_timestamps = []
            st.session_state.segment_timestamps = []
            st.session_state.transcript_segments = []
            
            # Load bookmarks
            self.load_bookmarks()
            
        except Exception as e:
            st.error(f"Error loading content data: {str(e)}")
    
    def load_bookmarks(self):
        """Load bookmarks for current content"""
        if st.session_state.selected_content_id:
            bookmarks = self.ts_system.get_bookmarks(
                st.session_state.selected_content_id,
                user_id="current_user"
            )
            st.session_state.bookmarks = [b.to_dict() for b in bookmarks]
    
    def handle_file_upload(self, uploaded_file):
        """Handle file upload and timestamp generation"""
        try:
            # Save uploaded file
            file_path = f"temp_{uploaded_file.name}"
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Generate content ID
            content_id = f"upload_{int(time.time())}"
            
            # Show progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Simulate timestamp generation process
            status_text.text("Analyzing audio...")
            progress_bar.progress(25)
            
            # This would call the actual timestamp generation
            # For demo purposes, we'll create sample data
            transcript = "This is a sample transcript for the uploaded file."
            
            status_text.text("Generating word timestamps...")
            progress_bar.progress(50)
            
            # Generate timestamps (this would use the actual audio file)
            word_timestamps = self.ts_system.generate_word_timestamps(
                file_path, transcript, content_id, method="forced_alignment"
            )
            
            status_text.text("Creating segments...")
            progress_bar.progress(75)
            
            segment_timestamps = self.ts_system.generate_segment_timestamps(
                file_path, transcript, content_id
            )
            
            status_text.text("Finalizing...")
            progress_bar.progress(100)
            
            # Update session state
            st.session_state.selected_content_id = content_id
            st.session_state.word_timestamps = [w.to_dict() for w in word_timestamps]
            st.session_state.segment_timestamps = [s.to_dict() for s in segment_timestamps]
            
            # Clean up temp file
            import os
            if os.path.exists(file_path):
                os.remove(file_path)
            
            status_text.text("✅ Processing complete!")
            st.success(f"Timestamps generated for {uploaded_file.name}")
            
        except Exception as e:
            st.error(f"File processing error: {str(e)}")
    
    def get_current_word(self, timestamp: float) -> Optional[Dict[str, Any]]:
        """Get the word being spoken at current timestamp"""
        for word in st.session_state.word_timestamps:
            if word['start_time'] <= timestamp <= word['end_time']:
                return word
        return None
    
    def format_time(self, seconds: float) -> str:
        """Format time in HH:MM:SS.mmm format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"
        else:
            return f"{minutes:02d}:{secs:02d}.{millisecs:03d}"
    
    def create_timeline_chart(self):
        """Create interactive timeline chart"""
        if not st.session_state.word_timestamps:
            return go.Figure()
        
        # Create subplot with secondary y-axis
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Word Timeline', 'Confidence Scores'),
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3]
        )
        
        # Word timeline
        words = st.session_state.word_timestamps
        
        # Create bars for each word
        for i, word in enumerate(words):
            fig.add_trace(
                go.Bar(
                    x=[word['end_time'] - word['start_time']],
                    y=[word['word']],
                    base=word['start_time'],
                    orientation='h',
                    name=word['word'],
                    showlegend=False,
                    hovertemplate=f"<b>{word['word']}</b><br>" +
                                f"Start: {self.format_time(word['start_time'])}<br>" +
                                f"End: {self.format_time(word['end_time'])}<br>" +
                                f"Confidence: {word['confidence']:.2f}<extra></extra>",
                    marker_color=px.colors.qualitative.Set3[i % len(px.colors.qualitative.Set3)]
                ),
                row=1, col=1
            )
        
        # Confidence timeline
        times = [w['start_time'] for w in words]
        confidences = [w['confidence'] for w in words]
        
        fig.add_trace(
            go.Scatter(
                x=times,
                y=confidences,
                mode='lines+markers',
                name='Confidence',
                line=dict(color='red', width=2),
                marker=dict(size=4),
                hovertemplate="Time: %{x:.1f}s<br>Confidence: %{y:.2f}<extra></extra>"
            ),
            row=2, col=1
        )
        
        # Add current time indicator
        current_time = st.session_state.current_audio_time
        fig.add_vline(
            x=current_time,
            line_dash="dash",
            line_color="blue",
            annotation_text="Current Time",
            annotation_position="top"
        )
        
        # Update layout
        fig.update_layout(
            height=600,
            title="Audio Timeline with Word-Level Timestamps",
            showlegend=False
        )
        
        fig.update_xaxes(title_text="Time (seconds)")
        fig.update_yaxes(title_text="Words", row=1, col=1)
        fig.update_yaxes(title_text="Confidence", row=2, col=1, range=[0, 1])
        
        return fig
    
    def create_csv_export(self, content_id: str, include_words: bool, 
                         include_segments: bool, include_bookmarks: bool, 
                         include_confidence: bool) -> str:
        """Create CSV export data"""
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Type', 'Start_Time', 'End_Time', 'Content', 'Confidence', 'Additional_Info'])
        
        # Write word data
        if include_words and st.session_state.word_timestamps:
            for word in st.session_state.word_timestamps:
                confidence = word['confidence'] if include_confidence else ''
                writer.writerow([
                    'Word',
                    word['start_time'],
                    word['end_time'],
                    word['word'],
                    confidence,
                    word.get('speaker_id', '')
                ])
        
        # Write segment data
        if include_segments and st.session_state.segment_timestamps:
            for segment in st.session_state.segment_timestamps:
                confidence = segment['confidence'] if include_confidence else ''
                writer.writerow([
                    f"Segment_{segment['segment_type']}",
                    segment['start_time'],
                    segment['end_time'],
                    segment['content'][:100] + '...' if len(segment['content']) > 100 else segment['content'],
                    confidence,
                    segment.get('speaker_id', '') or segment.get('topic', '')
                ])
        
        # Write bookmark data
        if include_bookmarks and st.session_state.bookmarks:
            for bookmark in st.session_state.bookmarks:
                writer.writerow([
                    'Bookmark',
                    bookmark['timestamp'],
                    bookmark['timestamp'],
                    bookmark['title'],
                    '',
                    bookmark.get('description', '')
                ])
        
        return output.getvalue()


def main():
    """Main function to run the Timestamping System UI"""
    st.set_page_config(
        page_title="Timestamping System",
        page_icon="🕒",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .current-word {
        background-color: #e6f3ff;
        padding: 5px;
        border-radius: 3px;
        border-left: 3px solid #0066cc;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize and render the UI
    ui = TimestampingSystemUI()
    ui.render_main_interface()


if __name__ == "__main__":
    main()