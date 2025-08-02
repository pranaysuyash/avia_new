"""
UI components for advanced segmentation
"""

import streamlit as st
from typing import List, Optional, Dict, Any
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from .segment_manager import SegmentManager, Segment, SegmentType
import json


def render_segmentation_view(
    transcript: str,
    segments: List[Segment],
    editable: bool = True,
    audio_path: Optional[str] = None
) -> List[Segment]:
    """Render the segmentation view with interactive segments"""
    
    st.markdown("### 📊 Advanced Segmentation")
    
    # Segmentation controls
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
    
    with col1:
        view_mode = st.selectbox(
            "View Mode",
            ["Timeline", "List", "Grid", "Analytics", "Chapter Editor"],
            help="Choose how to display segments"
        )
    
    with col2:
        color_by = st.selectbox(
            "Color By",
            ["Type", "Speaker", "Length", "Keywords"],
            help="Choose segment coloring scheme"
        )
    
    with col3:
        filter_type = st.multiselect(
            "Filter Types",
            [t.value for t in SegmentType],
            default=[t.value for t in SegmentType],
            help="Show only selected segment types"
        )
    
    with col4:
        if st.button("⚙️ Settings"):
            st.session_state.show_segment_settings = True
    
    with col5:
        if st.button("📖 Chapters"):
            st.session_state.show_chapter_editor = True
    
    # Filter segments
    filtered_segments = [
        seg for seg in segments 
        if seg.type.value in filter_type
    ]
    
    # Display segments based on view mode
    if view_mode == "Timeline":
        updated_segments = render_timeline_view(filtered_segments, transcript, color_by, editable)
    elif view_mode == "List":
        updated_segments = render_list_view(filtered_segments, editable)
    elif view_mode == "Grid":
        updated_segments = render_grid_view(filtered_segments, editable)
    elif view_mode == "Chapter Editor":
        updated_segments = render_chapter_editor_view(filtered_segments, transcript, audio_path, editable)
    else:  # Analytics
        render_analytics_view(filtered_segments, transcript)
        updated_segments = filtered_segments
    
    # Show chapter editor if requested
    if st.session_state.get('show_chapter_editor', False):
        with st.expander("📖 Manual Chapter Editor", expanded=True):
            render_manual_chapter_editor(segments, transcript, audio_path)
            if st.button("Close Chapter Editor"):
                st.session_state.show_chapter_editor = False
                st.rerun()
    
    # Export options
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📥 Export JSON"):
            manager = SegmentManager()
            json_data = manager.export_segments(filtered_segments, "json")
            st.download_button(
                "Download JSON",
                json_data,
                "segments.json",
                "application/json"
            )
    
    with col2:
        if st.button("📥 Export SRT"):
            manager = SegmentManager()
            srt_data = manager.export_segments(filtered_segments, "srt")
            st.download_button(
                "Download SRT",
                srt_data,
                "segments.srt",
                "text/plain"
            )
    
    with col3:
        if st.button("📥 Export VTT"):
            manager = SegmentManager()
            vtt_data = manager.export_segments(filtered_segments, "vtt")
            st.download_button(
                "Download VTT",
                vtt_data,
                "segments.vtt",
                "text/plain"
            )
    
    with col4:
        if st.button("📥 Export Text"):
            manager = SegmentManager()
            text_data = manager.export_segments(filtered_segments, "text")
            st.download_button(
                "Download Text",
                text_data,
                "segments.txt",
                "text/plain"
            )
    
    return updated_segments


def render_timeline_view(
    segments: List[Segment],
    full_transcript: str,
    color_by: str,
    editable: bool
) -> List[Segment]:
    """Render timeline visualization of segments"""
    
    if not segments:
        st.info("No segments to display")
        return segments
    
    # Prepare data for timeline
    timeline_data = []
    colors = get_segment_colors(segments, color_by)
    
    for i, seg in enumerate(segments):
        timeline_data.append({
            'Segment': f"Segment {seg.id}",
            'Type': seg.type.value,
            'Start': seg.start_char,
            'End': seg.end_char,
            'Duration': seg.end_char - seg.start_char,
            'Text': seg.text[:50] + "..." if len(seg.text) > 50 else seg.text,
            'Speaker': seg.speaker or "Unknown",
            'Keywords': ', '.join(seg.keywords[:3]),
            'Color': colors[i]
        })
    
    # Create timeline chart
    df = pd.DataFrame(timeline_data)
    
    fig = go.Figure()
    
    # Add segments as bars
    for _, row in df.iterrows():
        fig.add_trace(go.Bar(
            x=[row['Duration']],
            y=[row['Segment']],
            orientation='h',
            name=row['Type'],
            text=row['Text'],
            hovertemplate=(
                f"<b>{row['Type']}</b><br>" +
                f"Position: {row['Start']}-{row['End']}<br>" +
                f"Speaker: {row['Speaker']}<br>" +
                f"Keywords: {row['Keywords']}<br>" +
                f"<extra></extra>"
            ),
            marker_color=row['Color'],
            showlegend=False
        ))
    
    fig.update_layout(
        title="Segment Timeline",
        xaxis_title="Character Position",
        yaxis_title="Segments",
        height=max(400, len(segments) * 30),
        hovermode='closest'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Interactive segment display
    if editable:
        st.markdown("### 📝 Edit Segments")
        selected_segment = st.selectbox(
            "Select segment to edit",
            range(len(segments)),
            format_func=lambda x: f"Segment {segments[x].id}: {segments[x].type.value}"
        )
        
        if selected_segment is not None:
            segments[selected_segment] = render_segment_editor(
                segments[selected_segment],
                key=f"timeline_seg_{selected_segment}"
            )
    
    return segments


def render_list_view(segments: List[Segment], editable: bool) -> List[Segment]:
    """Render segments as an interactive list"""
    
    for i, segment in enumerate(segments):
        with st.expander(
            f"**Segment {segment.id}** - {segment.type.value.title()}",
            expanded=False
        ):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Display segment content
                st.write(f"**Speaker:** {segment.speaker or 'Unknown'}")
                if segment.start_time and segment.end_time:
                    st.write(f"**Time:** {segment.start_time:.1f}s - {segment.end_time:.1f}s")
                st.write(f"**Position:** Characters {segment.start_char} - {segment.end_char}")
                
                # Keywords
                if segment.keywords:
                    st.write(f"**Keywords:** {', '.join(segment.keywords)}")
                
                # Summary
                if segment.summary:
                    st.info(f"**Summary:** {segment.summary}")
                
                # Full text
                st.text_area(
                    "Content",
                    segment.text,
                    height=100,
                    disabled=not editable,
                    key=f"list_text_{i}"
                )
            
            with col2:
                # Segment stats
                st.metric("Words", len(segment.text.split()))
                st.metric("Characters", len(segment.text))
                st.metric("Confidence", f"{segment.confidence:.0%}")
                
                if editable:
                    if st.button("✏️ Edit", key=f"edit_list_{i}"):
                        st.session_state[f"editing_segment_{i}"] = True
            
            # Edit mode
            if editable and st.session_state.get(f"editing_segment_{i}", False):
                segments[i] = render_segment_editor(
                    segment,
                    key=f"list_editor_{i}"
                )
                if st.button("✅ Done", key=f"done_list_{i}"):
                    st.session_state[f"editing_segment_{i}"] = False
                    st.rerun()
    
    return segments


def render_grid_view(segments: List[Segment], editable: bool) -> List[Segment]:
    """Render segments in a grid layout"""
    
    # Group segments by type
    grouped = {}
    for seg in segments:
        seg_type = seg.type.value
        if seg_type not in grouped:
            grouped[seg_type] = []
        grouped[seg_type].append(seg)
    
    # Display each type in columns
    for seg_type, type_segments in grouped.items():
        st.subheader(f"{seg_type.replace('_', ' ').title()} ({len(type_segments)})")
        
        # Create columns for grid
        cols = st.columns(min(3, len(type_segments)))
        
        for i, seg in enumerate(type_segments):
            col_idx = i % len(cols)
            
            with cols[col_idx]:
                with st.container():
                    st.markdown(f"**Segment {seg.id}**")
                    
                    # Mini stats
                    if seg.speaker:
                        st.caption(f"Speaker: {seg.speaker}")
                    if seg.start_time and seg.end_time:
                        st.caption(f"⏱️ {seg.start_time:.1f}s - {seg.end_time:.1f}s")
                    
                    # Preview text
                    preview = seg.text[:100] + "..." if len(seg.text) > 100 else seg.text
                    st.write(preview)
                    
                    # Keywords as tags
                    if seg.keywords:
                        st.write("🏷️ " + " · ".join(seg.keywords[:3]))
                    
                    # Actions
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("👁️", key=f"view_grid_{seg.id}", help="View details"):
                            st.session_state[f"show_detail_{seg.id}"] = True
                    
                    with col2:
                        if editable and st.button("✏️", key=f"edit_grid_{seg.id}", help="Edit"):
                            st.session_state[f"edit_grid_{seg.id}"] = True
                    
                    # Detail view
                    if st.session_state.get(f"show_detail_{seg.id}", False):
                        with st.expander("Details", expanded=True):
                            st.text_area("Full Text", seg.text, height=150, disabled=True)
                            if st.button("Close", key=f"close_detail_{seg.id}"):
                                st.session_state[f"show_detail_{seg.id}"] = False
                                st.rerun()
    
    return segments


def render_analytics_view(segments: List[Segment], full_transcript: str):
    """Render analytics and insights about segments"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Segments", len(segments))
    
    with col2:
        avg_length = sum(len(seg.text) for seg in segments) / len(segments) if segments else 0
        st.metric("Avg Length", f"{avg_length:.0f} chars")
    
    with col3:
        unique_speakers = len(set(seg.speaker for seg in segments if seg.speaker))
        st.metric("Speakers", unique_speakers)
    
    with col4:
        total_duration = max((seg.end_time or 0) for seg in segments) if segments else 0
        st.metric("Duration", f"{total_duration:.1f}s")
    
    # Segment type distribution
    st.markdown("### 📊 Segment Type Distribution")
    type_counts = {}
    for seg in segments:
        type_counts[seg.type.value] = type_counts.get(seg.type.value, 0) + 1
    
    if type_counts:
        fig_types = px.pie(
            values=list(type_counts.values()),
            names=list(type_counts.keys()),
            title="Distribution by Type"
        )
        st.plotly_chart(fig_types, use_container_width=True)
    
    # Length distribution
    st.markdown("### 📏 Segment Length Distribution")
    lengths = [len(seg.text) for seg in segments]
    if lengths:
        fig_lengths = px.histogram(
            x=lengths,
            nbins=20,
            title="Character Length Distribution",
            labels={'x': 'Length (characters)', 'y': 'Count'}
        )
        st.plotly_chart(fig_lengths, use_container_width=True)
    
    # Keywords cloud
    st.markdown("### 🏷️ Top Keywords")
    all_keywords = []
    for seg in segments:
        all_keywords.extend(seg.keywords)
    
    if all_keywords:
        keyword_freq = {}
        for kw in all_keywords:
            keyword_freq[kw] = keyword_freq.get(kw, 0) + 1
        
        # Sort by frequency
        sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:20]
        
        # Display as word cloud-style
        keyword_html = ""
        max_freq = sorted_keywords[0][1] if sorted_keywords else 1
        
        for word, freq in sorted_keywords:
            size = 14 + (freq / max_freq) * 20
            keyword_html += f'<span style="font-size: {size}px; margin: 5px;">{word}</span> '
        
        st.markdown(keyword_html, unsafe_allow_html=True)
    
    # Speaker statistics
    if any(seg.speaker for seg in segments):
        st.markdown("### 🗣️ Speaker Statistics")
        speaker_data = {}
        
        for seg in segments:
            if seg.speaker:
                if seg.speaker not in speaker_data:
                    speaker_data[seg.speaker] = {
                        'segments': 0,
                        'total_chars': 0,
                        'total_time': 0
                    }
                
                speaker_data[seg.speaker]['segments'] += 1
                speaker_data[seg.speaker]['total_chars'] += len(seg.text)
                if seg.start_time and seg.end_time:
                    speaker_data[seg.speaker]['total_time'] += seg.end_time - seg.start_time
        
        # Create speaker dataframe
        speaker_df = pd.DataFrame.from_dict(speaker_data, orient='index')
        speaker_df['avg_chars'] = speaker_df['total_chars'] / speaker_df['segments']
        
        st.dataframe(speaker_df, use_container_width=True)
    
    # Segment flow
    st.markdown("### 🔄 Segment Flow")
    if len(segments) > 1:
        flow_data = []
        for i in range(len(segments) - 1):
            flow_data.append({
                'From': f"{segments[i].type.value} ({segments[i].id})",
                'To': f"{segments[i+1].type.value} ({segments[i+1].id})",
                'Count': 1
            })
        
        flow_df = pd.DataFrame(flow_data)
        flow_summary = flow_df.groupby(['From', 'To']).sum().reset_index()
        
        # Simple flow visualization
        st.dataframe(flow_summary, use_container_width=True)


def render_segment_editor(segment: Segment, key: str) -> Segment:
    """Render segment editor form"""
    
    with st.form(key=f"segment_editor_{key}"):
        st.markdown("### ✏️ Edit Segment")
        
        # Type selection
        new_type = st.selectbox(
            "Segment Type",
            [t.value for t in SegmentType],
            index=[t.value for t in SegmentType].index(segment.type.value)
        )
        
        # Speaker
        new_speaker = st.text_input(
            "Speaker",
            value=segment.speaker or "",
            placeholder="Enter speaker name"
        )
        
        # Text content
        new_text = st.text_area(
            "Content",
            value=segment.text,
            height=150
        )
        
        # Keywords
        keywords_str = st.text_input(
            "Keywords (comma-separated)",
            value=", ".join(segment.keywords)
        )
        new_keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
        
        # Summary
        new_summary = st.text_area(
            "Summary",
            value=segment.summary or "",
            height=50
        )
        
        # Time adjustment (if available)
        if segment.start_time is not None and segment.end_time is not None:
            col1, col2 = st.columns(2)
            with col1:
                new_start_time = st.number_input(
                    "Start Time (seconds)",
                    value=segment.start_time,
                    min_value=0.0,
                    step=0.1
                )
            with col2:
                new_end_time = st.number_input(
                    "End Time (seconds)",
                    value=segment.end_time,
                    min_value=new_start_time,
                    step=0.1
                )
        else:
            new_start_time = segment.start_time
            new_end_time = segment.end_time
        
        # Submit button
        if st.form_submit_button("💾 Save Changes"):
            # Update segment
            segment.type = SegmentType(new_type)
            segment.speaker = new_speaker if new_speaker else None
            segment.text = new_text
            segment.keywords = new_keywords
            segment.summary = new_summary if new_summary else None
            segment.start_time = new_start_time
            segment.end_time = new_end_time
            
            # Update character positions based on new text
            # (In real app, would recalculate properly)
            segment.end_char = segment.start_char + len(new_text)
            
            st.success("Segment updated!")
    
    return segment


def get_segment_colors(segments: List[Segment], color_by: str) -> List[str]:
    """Get colors for segments based on coloring scheme"""
    
    if color_by == "Type":
        # Define colors for each segment type
        type_colors = {
            SegmentType.INTRODUCTION: "#4CAF50",
            SegmentType.MAIN_TOPIC: "#2196F3",
            SegmentType.SUB_TOPIC: "#03A9F4",
            SegmentType.CONCLUSION: "#9C27B0",
            SegmentType.QUESTION: "#FF9800",
            SegmentType.ANSWER: "#FFC107",
            SegmentType.TRANSITION: "#607D8B",
            SegmentType.SPEAKER_CHANGE: "#795548",
            SegmentType.PAUSE: "#9E9E9E",
            SegmentType.CUSTOM: "#E91E63"
        }
        return [type_colors.get(seg.type, "#666666") for seg in segments]
    
    elif color_by == "Speaker":
        # Assign colors to speakers
        speakers = list(set(seg.speaker for seg in segments if seg.speaker))
        speaker_colors = px.colors.qualitative.Set3[:len(speakers)]
        speaker_color_map = dict(zip(speakers, speaker_colors))
        return [speaker_color_map.get(seg.speaker, "#999999") for seg in segments]
    
    elif color_by == "Length":
        # Color gradient based on length
        lengths = [len(seg.text) for seg in segments]
        min_len = min(lengths) if lengths else 0
        max_len = max(lengths) if lengths else 1
        
        colors = []
        for length in lengths:
            # Normalize to 0-1
            norm = (length - min_len) / (max_len - min_len) if max_len > min_len else 0.5
            # Create gradient from blue to red
            r = int(255 * norm)
            b = int(255 * (1 - norm))
            colors.append(f"rgb({r}, 100, {b})")
        return colors
    
    else:  # Keywords
        # Color based on keyword density
        densities = []
        for seg in segments:
            word_count = len(seg.text.split())
            keyword_count = len(seg.keywords)
            density = keyword_count / word_count if word_count > 0 else 0
            densities.append(density)
        
        max_density = max(densities) if densities else 1
        colors = []
        for density in densities:
            # Create gradient from light to dark green
            intensity = int(255 - (density / max_density * 155))
            colors.append(f"rgb(0, {intensity}, 0)")
        return colors


def render_chapter_editor_view(
    segments: List[Segment],
    transcript: str,
    audio_path: Optional[str],
    editable: bool
) -> List[Segment]:
    """Render chapter editor with visual timeline"""
    
    st.markdown("### 📖 Chapter Editor")
    
    # Get chapter segments
    chapters = [seg for seg in segments if seg.type == SegmentType.CHAPTER]
    
    if not chapters:
        st.info("No chapters found. Create manual chapters using the editor below.")
    else:
        # Display existing chapters
        st.markdown("#### Existing Chapters")
        
        for i, chapter in enumerate(chapters):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                title = chapter.chapter_title or f"Chapter {i+1}"
                st.write(f"**{title}**")
            
            with col2:
                if chapter.start_time:
                    st.write(f"⏱️ {chapter.start_time:.1f}s")
            
            with col3:
                if chapter.metadata.get('description'):
                    st.write(f"📝 {chapter.metadata['description'][:30]}...")
            
            with col4:
                if editable and st.button("🗑️", key=f"delete_chapter_{i}", help="Delete chapter"):
                    # Remove chapter from segments
                    segments = [seg for seg in segments if seg.id != chapter.id]
                    st.rerun()
    
    # Visual timeline for chapter creation
    if editable:
        st.markdown("#### Create New Chapter")
        render_visual_timeline_editor(segments, transcript, audio_path)
    
    return segments


def render_visual_timeline_editor(
    segments: List[Segment],
    transcript: str,
    audio_path: Optional[str]
):
    """Render visual timeline editor for creating chapters"""
    
    # Get timeline data
    timeline_segments = [seg for seg in segments if seg.start_time and seg.end_time]
    
    if not timeline_segments:
        st.warning("No timeline data available. Chapters require timestamp information.")
        return
    
    # Create timeline visualization
    fig = go.Figure()
    
    # Add segments to timeline
    for seg in timeline_segments:
        color = get_segment_color_by_type(seg.type)
        
        fig.add_trace(go.Scatter(
            x=[seg.start_time, seg.end_time],
            y=[1, 1],
            mode='lines+markers',
            name=f"{seg.type.value} {seg.id}",
            line=dict(color=color, width=8),
            hovertemplate=f"<b>{seg.type.value}</b><br>Time: {seg.start_time:.1f}s - {seg.end_time:.1f}s<br>Text: {seg.text[:50]}...<extra></extra>",
            showlegend=False
        ))
    
    # Add chapter markers
    chapters = [seg for seg in segments if seg.type == SegmentType.CHAPTER]
    for chapter in chapters:
        if chapter.start_time:
            fig.add_vline(
                x=chapter.start_time,
                line_dash="dash",
                line_color="red",
                annotation_text=chapter.chapter_title or "Chapter",
                annotation_position="top"
            )
    
    fig.update_layout(
        title="Timeline - Click to Add Chapter Markers",
        xaxis_title="Time (seconds)",
        yaxis=dict(visible=False),
        height=200,
        showlegend=False
    )
    
    # Display timeline
    timeline_event = st.plotly_chart(fig, use_container_width=True, key="timeline_editor")
    
    # Chapter creation form
    with st.form("create_chapter"):
        col1, col2 = st.columns(2)
        
        with col1:
            chapter_title = st.text_input(
                "Chapter Title",
                placeholder="Enter chapter title"
            )
            
            chapter_time = st.number_input(
                "Start Time (seconds)",
                min_value=0.0,
                max_value=max(seg.end_time for seg in timeline_segments if seg.end_time),
                step=0.1,
                value=0.0
            )
        
        with col2:
            chapter_description = st.text_area(
                "Description (optional)",
                placeholder="Brief description of this chapter",
                height=100
            )
        
        if st.form_submit_button("📖 Create Chapter"):
            if chapter_title:
                # Create new chapter marker
                manager = SegmentManager()
                new_chapter = manager.create_manual_chapter(
                    title=chapter_title,
                    start_time=chapter_time,
                    description=chapter_description
                )
                
                # Store in session state for processing
                if 'manual_chapters' not in st.session_state:
                    st.session_state.manual_chapters = []
                
                st.session_state.manual_chapters.append(new_chapter)
                st.success(f"Chapter '{chapter_title}' created at {chapter_time:.1f}s")
                st.rerun()
            else:
                st.error("Please enter a chapter title")


def render_manual_chapter_editor(
    segments: List[Segment],
    transcript: str,
    audio_path: Optional[str]
):
    """Render manual chapter editor interface"""
    
    st.markdown("#### Manual Chapter Management")
    
    # Show existing manual chapters
    manual_chapters = st.session_state.get('manual_chapters', [])
    
    if manual_chapters:
        st.markdown("**Pending Chapters:**")
        
        for i, chapter in enumerate(manual_chapters):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                st.write(f"**{chapter['title']}**")
            
            with col2:
                st.write(f"⏱️ {chapter['start_time']:.1f}s")
            
            with col3:
                if chapter.get('description'):
                    st.write(f"📝 {chapter['description'][:30]}...")
            
            with col4:
                if st.button("🗑️", key=f"remove_pending_{i}", help="Remove"):
                    st.session_state.manual_chapters.pop(i)
                    st.rerun()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Apply All Chapters"):
                st.success(f"Applied {len(manual_chapters)} chapters to segmentation")
                # Chapters will be applied in the main segmentation process
        
        with col2:
            if st.button("🗑️ Clear All"):
                st.session_state.manual_chapters = []
                st.rerun()
    
    # Batch chapter creation
    st.markdown("#### Batch Chapter Creation")
    
    with st.expander("Create Multiple Chapters", expanded=False):
        chapter_text = st.text_area(
            "Chapter List",
            placeholder="Enter chapters in format:\n00:30 - Introduction\n02:15 - Main Topic\n05:45 - Conclusion",
            height=150,
            help="Format: MM:SS - Title or HH:MM:SS - Title"
        )
        
        if st.button("📖 Parse and Create Chapters"):
            if chapter_text:
                chapters = parse_chapter_text(chapter_text)
                
                if chapters:
                    if 'manual_chapters' not in st.session_state:
                        st.session_state.manual_chapters = []
                    
                    st.session_state.manual_chapters.extend(chapters)
                    st.success(f"Created {len(chapters)} chapters")
                    st.rerun()
                else:
                    st.error("Could not parse chapter format. Please check the format.")


def parse_chapter_text(text: str) -> List[Dict[str, Any]]:
    """Parse chapter text into chapter objects"""
    chapters = []
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Try to match time - title format
        import re
        
        # Match MM:SS - Title or HH:MM:SS - Title
        match = re.match(r'(\d{1,2}):(\d{2})(?::(\d{2}))?\s*-\s*(.+)', line)
        
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            hours = int(match.group(3)) if match.group(3) else 0
            title = match.group(4).strip()
            
            # Convert to total seconds
            total_seconds = hours * 3600 + minutes * 60 + seconds
            
            manager = SegmentManager()
            chapter = manager.create_manual_chapter(
                title=title,
                start_time=float(total_seconds)
            )
            chapters.append(chapter)
    
    return chapters


def get_segment_color_by_type(segment_type: SegmentType) -> str:
    """Get color for segment type"""
    colors = {
        SegmentType.INTRODUCTION: "#4CAF50",
        SegmentType.MAIN_TOPIC: "#2196F3",
        SegmentType.SUB_TOPIC: "#03A9F4",
        SegmentType.CONCLUSION: "#9C27B0",
        SegmentType.QUESTION: "#FF9800",
        SegmentType.ANSWER: "#FFC107",
        SegmentType.TRANSITION: "#607D8B",
        SegmentType.SPEAKER_CHANGE: "#795548",
        SegmentType.PAUSE: "#9E9E9E",
        SegmentType.SILENCE: "#CCCCCC",
        SegmentType.CHAPTER: "#E91E63",
        SegmentType.CUSTOM: "#E91E63"
    }
    return colors.get(segment_type, "#666666")


def render_segmentation_settings():
    """Render segmentation settings dialog"""
    with st.expander("⚙️ Segmentation Settings", expanded=True):
        st.markdown("### Segmentation Parameters")
        
        method = st.selectbox(
            "Segmentation Method",
            ["hybrid", "semantic", "structural", "temporal", "silence"],
            help="Choose the segmentation algorithm"
        )
        
        if method == "semantic":
            similarity_threshold = st.slider(
                "Similarity Threshold",
                0.0, 1.0, 0.3,
                help="Lower values create more segments"
            )
        
        elif method == "temporal":
            segment_duration = st.slider(
                "Segment Duration (seconds)",
                10, 120, 30,
                help="Target duration for each segment"
            )
        
        elif method == "silence":
            st.markdown("#### Silence Detection Settings")
            
            silence_threshold = st.slider(
                "Silence Threshold",
                0.001, 0.1, 0.01,
                format="%.3f",
                help="Lower values detect quieter silences"
            )
            
            min_silence_duration = st.slider(
                "Minimum Silence Duration (seconds)",
                0.5, 5.0, 1.0,
                help="Minimum duration to consider as silence"
            )
            
            # Store settings in session state
            st.session_state.silence_threshold = silence_threshold
            st.session_state.min_silence_duration = min_silence_duration
        
        min_segment_length = st.slider(
            "Minimum Segment Length (characters)",
            10, 200, 50,
            help="Segments shorter than this will be merged"
        )
        
        merge_similar = st.checkbox(
            "Merge Similar Adjacent Segments",
            value=True,
            help="Combine segments of the same type"
        )
        
        # Advanced options
        st.markdown("#### Advanced Options")
        
        enable_silence_refinement = st.checkbox(
            "Enable Silence-based Refinement",
            value=True,
            help="Refine segments using audio silence detection"
        )
        
        preserve_manual_chapters = st.checkbox(
            "Preserve Manual Chapters",
            value=True,
            help="Keep manually created chapter markers"
        )
        
        # Store all settings
        if st.button("Apply Settings"):
            st.session_state.segmentation_settings = {
                'method': method,
                'min_segment_length': min_segment_length,
                'merge_similar': merge_similar,
                'enable_silence_refinement': enable_silence_refinement,
                'preserve_manual_chapters': preserve_manual_chapters
            }
            
            st.success("Settings updated!")
            st.session_state.show_segment_settings = False
            st.rerun()