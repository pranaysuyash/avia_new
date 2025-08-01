"""
Streamlit UI components for speaker diarization
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime, timedelta

from .diarization_manager import DiarizationResult, SpeakerInfo


def render_speaker_timeline(result: DiarizationResult, height: int = 200):
    """Render interactive speaker timeline visualization"""
    if not result.segments:
        st.info("No speaker segments to display")
        return
    
    # Create timeline figure
    fig = go.Figure()
    
    # Add a trace for each speaker
    y_positions = {speaker_id: i for i, speaker_id in enumerate(result.speakers.keys())}
    
    for speaker_id, speaker_info in result.speakers.items():
        segments = [seg for seg in result.segments if seg.speaker_id == speaker_id]
        
        if not segments:
            continue
        
        # Create rectangles for each segment
        for segment in segments:
            fig.add_shape(
                type="rect",
                x0=segment.start_time,
                x1=segment.end_time,
                y0=y_positions[speaker_id] - 0.4,
                y1=y_positions[speaker_id] + 0.4,
                fillcolor=speaker_info.color,
                opacity=0.8,
                line=dict(width=0)
            )
            
            # Add hover text
            fig.add_trace(go.Scatter(
                x=[(segment.start_time + segment.end_time) / 2],
                y=[y_positions[speaker_id]],
                mode='markers',
                marker=dict(size=0.1, opacity=0),
                hovertext=f"{speaker_info.label or speaker_id}<br>"
                         f"{segment.start_time:.1f}s - {segment.end_time:.1f}s<br>"
                         f"Duration: {segment.duration:.1f}s<br>"
                         f"Confidence: {segment.confidence:.0%}",
                hoverinfo='text',
                showlegend=False
            ))
    
    # Update layout
    fig.update_layout(
        title="Speaker Timeline",
        xaxis=dict(
            title="Time (seconds)",
            range=[0, result.audio_duration],
            tickformat=".0f"
        ),
        yaxis=dict(
            title="Speakers",
            tickvals=list(y_positions.values()),
            ticktext=[speaker.label or sid for sid, speaker in result.speakers.items()],
            range=[-0.5, len(y_positions) - 0.5]
        ),
        height=height,
        hovermode='closest',
        showlegend=False,
        margin=dict(l=100, r=20, t=40, b=40)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_speaker_statistics(result: DiarizationResult):
    """Render speaker statistics and controls"""
    if not result.speakers:
        st.info("No speakers detected")
        return
    
    st.subheader("Speaker Statistics")
    
    # Create columns for each speaker
    cols = st.columns(min(len(result.speakers), 4))
    
    for idx, (speaker_id, speaker_info) in enumerate(result.speakers.items()):
        col_idx = idx % len(cols)
        with cols[col_idx]:
            # Speaker card
            st.markdown(f"""
            <div style="background-color: {speaker_info.color}20; padding: 10px; border-radius: 5px; border: 2px solid {speaker_info.color};">
                <h4 style="margin: 0; color: {speaker_info.color};">{speaker_info.label or speaker_id}</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Statistics
            st.metric("Speaking Time", f"{speaker_info.total_time:.1f}s")
            st.metric("Segments", speaker_info.segment_count)
            
            if hasattr(speaker_info, 'speaking_percentage'):
                st.metric("Speaking %", f"{speaker_info.speaking_percentage:.1f}%")
            
            # Rename speaker
            new_label = st.text_input(
                "Rename", 
                value=speaker_info.label or "",
                key=f"rename_{speaker_id}",
                placeholder=speaker_id
            )
            
            if new_label and new_label != speaker_info.label:
                speaker_info.label = new_label
                st.success("Updated!")


def render_speaker_distribution(result: DiarizationResult):
    """Render pie chart of speaker distribution"""
    if not result.speakers:
        return
    
    # Prepare data
    data = []
    for speaker_id, speaker_info in result.speakers.items():
        data.append({
            'Speaker': speaker_info.label or speaker_id,
            'Speaking Time': speaker_info.total_time,
            'Color': speaker_info.color
        })
    
    df = pd.DataFrame(data)
    
    # Create pie chart
    fig = px.pie(
        df, 
        values='Speaking Time',
        names='Speaker',
        title='Speaking Time Distribution',
        color='Speaker',
        color_discrete_map={row['Speaker']: row['Color'] for _, row in df.iterrows()}
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Time: %{value:.1f}s<br>Percentage: %{percent}<extra></extra>'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_transcript_with_speakers(result: DiarizationResult, transcript_text: Optional[str] = None):
    """Render transcript with speaker labels"""
    st.subheader("Transcript with Speakers")
    
    if not result.segments:
        st.info("No speaker segments available")
        return
    
    # Group consecutive segments by speaker
    grouped_segments = []
    current_group = None
    
    for segment in result.segments:
        if current_group is None or current_group['speaker_id'] != segment.speaker_id:
            if current_group:
                grouped_segments.append(current_group)
            current_group = {
                'speaker_id': segment.speaker_id,
                'start_time': segment.start_time,
                'end_time': segment.end_time,
                'segments': [segment]
            }
        else:
            current_group['end_time'] = segment.end_time
            current_group['segments'].append(segment)
    
    if current_group:
        grouped_segments.append(current_group)
    
    # Render grouped segments
    for group in grouped_segments:
        speaker_info = result.speakers.get(group['speaker_id'])
        speaker_label = speaker_info.label if speaker_info else group['speaker_id']
        speaker_color = speaker_info.color if speaker_info else '#666666'
        
        # Format time
        start_time = timedelta(seconds=group['start_time'])
        end_time = timedelta(seconds=group['end_time'])
        time_str = f"{str(start_time).split('.')[0]} - {str(end_time).split('.')[0]}"
        
        # Render speaker header
        st.markdown(f"""
        <div style="margin: 10px 0;">
            <span style="color: {speaker_color}; font-weight: bold;">
                [{speaker_label}] {time_str}
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        # Render text for segments
        if transcript_text:
            # TODO: Align with actual transcript
            st.markdown(f"*[Transcript segment for {speaker_label}]*")
        else:
            # Show segment details
            for segment in group['segments']:
                if segment.text:
                    st.markdown(segment.text)
                else:
                    st.markdown(f"*[Speech from {segment.start_time:.1f}s to {segment.end_time:.1f}s]*")


def render_diarization_controls(key_prefix: str = "diarization"):
    """Render diarization configuration controls"""
    st.subheader("Diarization Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        provider = st.selectbox(
            "Diarization Provider",
            options=["whisperx", "pyannote", "simple_vad", "mock"],
            key=f"{key_prefix}_provider",
            help="Choose the speaker diarization method"
        )
        
        min_duration = st.slider(
            "Minimum Segment Duration (seconds)",
            min_value=0.5,
            max_value=5.0,
            value=1.0,
            step=0.5,
            key=f"{key_prefix}_min_duration",
            help="Minimum duration for a speaker segment"
        )
    
    with col2:
        max_speakers = st.number_input(
            "Maximum Speakers",
            min_value=2,
            max_value=10,
            value=5,
            key=f"{key_prefix}_max_speakers",
            help="Maximum number of speakers to detect"
        )
        
        use_gpu = st.checkbox(
            "Use GPU Acceleration",
            value=False,
            key=f"{key_prefix}_use_gpu",
            help="Use GPU for faster processing (if available)"
        )
    
    return {
        'provider': provider,
        'min_segment_duration': min_duration,
        'max_speakers': max_speakers,
        'use_gpu': use_gpu
    }


def render_speaker_merge_controls(result: DiarizationResult, key_prefix: str = "merge"):
    """Render controls for merging speakers"""
    if len(result.speakers) < 2:
        return
    
    st.subheader("Merge Speakers")
    st.caption("Combine two speakers if they were incorrectly separated")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    speaker_labels = {
        sid: speaker.label or sid 
        for sid, speaker in result.speakers.items()
    }
    
    with col1:
        speaker1 = st.selectbox(
            "First Speaker",
            options=list(speaker_labels.keys()),
            format_func=lambda x: speaker_labels[x],
            key=f"{key_prefix}_speaker1"
        )
    
    with col2:
        remaining_speakers = [s for s in speaker_labels.keys() if s != speaker1]
        speaker2 = st.selectbox(
            "Second Speaker",
            options=remaining_speakers,
            format_func=lambda x: speaker_labels[x],
            key=f"{key_prefix}_speaker2"
        )
    
    with col3:
        if st.button("Merge", key=f"{key_prefix}_merge_button"):
            result.merge_speakers(speaker1, speaker2)
            st.success(f"Merged {speaker_labels[speaker2]} into {speaker_labels[speaker1]}")
            st.rerun()


def render_speaker_profiling_controls(profiler, key_prefix: str = "profiling"):
    """Render speaker profiling and recognition controls"""
    st.subheader("Speaker Profiling & Recognition")
    
    # Get all profiles
    profiles = profiler.get_all_profiles()
    
    if profiles:
        st.write(f"**{len(profiles)} speaker profiles available**")
        
        # Profile management
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("View All Profiles", key=f"{key_prefix}_view_all"):
                st.session_state[f"{key_prefix}_show_profiles"] = True
        
        with col2:
            if st.button("Export Profiles", key=f"{key_prefix}_export"):
                export_path = f"speaker_profiles_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                if profiler.export_profiles(export_path):
                    st.success(f"Profiles exported to {export_path}")
                else:
                    st.error("Failed to export profiles")
        
        with col3:
            uploaded_file = st.file_uploader(
                "Import Profiles",
                type=['json'],
                key=f"{key_prefix}_import"
            )
            if uploaded_file:
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    if profiler.import_profiles(tmp_file.name):
                        st.success("Profiles imported successfully")
                        st.rerun()
                    else:
                        st.error("Failed to import profiles")
        
        # Show profiles if requested
        if st.session_state.get(f"{key_prefix}_show_profiles", False):
            render_speaker_profiles_table(profiles, profiler, key_prefix)
    else:
        st.info("No speaker profiles available. Process audio with WhisperX to create profiles.")


def render_speaker_profiles_table(profiles: Dict, profiler, key_prefix: str):
    """Render table of speaker profiles"""
    st.subheader("Speaker Profiles")
    
    # Create DataFrame for display
    profile_data = []
    for speaker_id, profile in profiles.items():
        profile_data.append({
            'Speaker ID': speaker_id,
            'Name': profile.name or 'Unnamed',
            'Total Time': f"{profile.total_speaking_time:.1f}s",
            'Recordings': profile.recording_count,
            'Confidence': f"{profile.recognition_confidence:.0%}",
            'Last Updated': profile.last_updated[:10] if profile.last_updated else 'Unknown',
            'Voice Type': profile.voice_characteristics.get('voice_type', 'Unknown')
        })
    
    df = pd.DataFrame(profile_data)
    st.dataframe(df, use_container_width=True)
    
    # Profile management actions
    st.subheader("Profile Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Rename Speaker**")
        speaker_to_rename = st.selectbox(
            "Select Speaker",
            options=list(profiles.keys()),
            key=f"{key_prefix}_rename_select"
        )
        new_name = st.text_input(
            "New Name",
            value=profiles[speaker_to_rename].name or "",
            key=f"{key_prefix}_new_name"
        )
        if st.button("Rename", key=f"{key_prefix}_rename_btn"):
            profile = profiles[speaker_to_rename]
            profile.name = new_name
            profiler._save_profile(profile)
            st.success(f"Renamed speaker to: {new_name}")
            st.rerun()
    
    with col2:
        st.write("**Merge Speakers**")
        primary_speaker = st.selectbox(
            "Primary Speaker (keep)",
            options=list(profiles.keys()),
            key=f"{key_prefix}_merge_primary"
        )
        secondary_options = [s for s in profiles.keys() if s != primary_speaker]
        if secondary_options:
            secondary_speaker = st.selectbox(
                "Secondary Speaker (merge into primary)",
                options=secondary_options,
                key=f"{key_prefix}_merge_secondary"
            )
            if st.button("Merge Speakers", key=f"{key_prefix}_merge_btn"):
                if profiler.merge_profiles(primary_speaker, secondary_speaker):
                    st.success(f"Merged {secondary_speaker} into {primary_speaker}")
                    st.rerun()
                else:
                    st.error("Failed to merge speakers")
    
    # Delete profile
    st.write("**Delete Profile**")
    speaker_to_delete = st.selectbox(
        "Select Speaker to Delete",
        options=list(profiles.keys()),
        key=f"{key_prefix}_delete_select"
    )
    if st.button("Delete Profile", key=f"{key_prefix}_delete_btn", type="secondary"):
        if profiler.delete_profile(speaker_to_delete):
            st.success(f"Deleted profile: {speaker_to_delete}")
            st.rerun()
        else:
            st.error("Failed to delete profile")


def render_speaker_timeline_visualization(result: DiarizationResult, height: int = 300):
    """Enhanced timeline visualization with speaker profiling information"""
    if not result.segments:
        st.info("No speaker segments to display")
        return
    
    # Create enhanced timeline figure
    fig = go.Figure()
    
    # Add a trace for each speaker with enhanced information
    y_positions = {speaker_id: i for i, speaker_id in enumerate(result.speakers.keys())}
    
    for speaker_id, speaker_info in result.speakers.items():
        segments = [seg for seg in result.segments if seg.speaker_id == speaker_id]
        
        if not segments:
            continue
        
        # Create rectangles for each segment with enhanced hover info
        for segment in segments:
            # Enhanced hover text with voice characteristics
            hover_text = f"{speaker_info.label or speaker_id}<br>"
            hover_text += f"{segment.start_time:.1f}s - {segment.end_time:.1f}s<br>"
            hover_text += f"Duration: {segment.duration:.1f}s<br>"
            hover_text += f"Confidence: {segment.confidence:.0%}"
            
            if segment.text:
                hover_text += f"<br>Text: {segment.text[:50]}..."
            
            fig.add_shape(
                type="rect",
                x0=segment.start_time,
                x1=segment.end_time,
                y0=y_positions[speaker_id] - 0.4,
                y1=y_positions[speaker_id] + 0.4,
                fillcolor=speaker_info.color,
                opacity=0.8,
                line=dict(width=1, color=speaker_info.color)
            )
            
            # Add invisible trace for hover
            fig.add_trace(go.Scatter(
                x=[(segment.start_time + segment.end_time) / 2],
                y=[y_positions[speaker_id]],
                mode='markers',
                marker=dict(size=0.1, opacity=0),
                hovertext=hover_text,
                hoverinfo='text',
                showlegend=False
            ))
    
    # Update layout with enhanced styling
    fig.update_layout(
        title="Enhanced Speaker Timeline with Voice Profiling",
        xaxis=dict(
            title="Time (seconds)",
            range=[0, result.audio_duration],
            tickformat=".0f",
            showgrid=True,
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title="Speakers",
            tickvals=list(y_positions.values()),
            ticktext=[f"{speaker.label or sid} ({speaker.total_time:.1f}s)" 
                     for sid, speaker in result.speakers.items()],
            range=[-0.5, len(y_positions) - 0.5],
            showgrid=True,
            gridcolor='lightgray'
        ),
        height=height,
        hovermode='closest',
        showlegend=False,
        margin=dict(l=150, r=20, t=60, b=40),
        plot_bgcolor='white'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_voice_characteristics_analysis(profiles: Dict, key_prefix: str = "voice_analysis"):
    """Render voice characteristics analysis"""
    if not profiles:
        return
    
    st.subheader("Voice Characteristics Analysis")
    
    # Voice type distribution
    voice_types = {}
    for profile in profiles.values():
        voice_type = profile.voice_characteristics.get('voice_type', 'Unknown')
        voice_types[voice_type] = voice_types.get(voice_type, 0) + 1
    
    if voice_types:
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart of voice types
            fig = px.pie(
                values=list(voice_types.values()),
                names=list(voice_types.keys()),
                title="Voice Type Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Speaking time distribution
            speaking_times = [profile.total_speaking_time for profile in profiles.values()]
            speaker_names = [profile.name or profile.speaker_id for profile in profiles.values()]
            
            fig = px.bar(
                x=speaker_names,
                y=speaking_times,
                title="Total Speaking Time by Speaker",
                labels={'x': 'Speaker', 'y': 'Speaking Time (seconds)'}
            )
            fig.update_xaxis(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)


def format_time_for_export(seconds: float) -> str:
    """Format time in seconds to HH:MM:SS,mmm format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


class DiarizationUI:
    """Main diarization UI class"""
    
    def __init__(self):
        from .diarization_manager import DiarizationManager
        from .providers.mock_provider import MockProvider
        self.manager = DiarizationManager()
        
        # Set up mock provider for testing
        mock_provider = MockProvider({"processing_delay": 0.1})
        self.manager.set_provider(mock_provider)
    
    def render_diarization_interface(self):
        """Main diarization interface"""
        st.header("🎤 Speaker Diarization")
        st.markdown("Identify and separate different speakers in audio files")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload Audio File",
            type=['wav', 'mp3', 'm4a', 'flac'],
            help="Upload an audio file for speaker diarization"
        )
        
        if not uploaded_file:
            st.info("Upload an audio file to analyze speakers")
            return
        
        # Diarization settings
        col1, col2 = st.columns(2)
        
        with col1:
            min_segment_duration = st.slider(
                "Minimum Segment Duration (seconds)",
                min_value=0.5,
                max_value=5.0,
                value=1.0,
                step=0.5
            )
        
        with col2:
            max_speakers = st.number_input(
                "Maximum Speakers",
                min_value=2,
                max_value=10,
                value=4
            )
        
        # Process audio
        if st.button("Analyze Speakers", type="primary"):
            with st.spinner("Analyzing speakers..."):
                try:
                    # Save uploaded file temporarily
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        audio_path = tmp_file.name
                    
                    # Run diarization
                    import asyncio
                    result = asyncio.run(self.manager.process_audio(
                        audio_path,
                        min_segment_duration=min_segment_duration
                    ))
                    
                    st.success(f"Speaker analysis completed!")
                    
                    # Display results
                    self._display_diarization_results(result)
                    
                    # Cleanup
                    import os
                    os.unlink(audio_path)
                    
                except Exception as e:
                    st.error(f"Speaker analysis failed: {str(e)}")
    
    def _display_diarization_results(self, result):
        """Display diarization analysis results"""
        # Overview metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Speakers Detected", len(result.speakers))
        
        with col2:
            st.metric("Total Segments", len(result.segments))
        
        with col3:
            st.metric("Audio Duration", f"{result.audio_duration:.1f}s")
        
        # Speaker timeline visualization
        if result.segments:
            st.subheader("Speaker Timeline")
            render_speaker_timeline(result, height=300)
        
        # Speaker breakdown
        st.subheader("Speaker Breakdown")
        
        for speaker_id in result.speakers:
            speaker_segments = [seg for seg in result.segments if seg.speaker_id == speaker_id]
            total_time = sum(seg.duration for seg in speaker_segments)
            
            with st.expander(f"🎤 {speaker_id} - {total_time:.1f}s total"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Segments", len(speaker_segments))
                    st.metric("Speaking Time", f"{total_time:.1f}s")
                
                with col2:
                    avg_confidence = sum(seg.confidence for seg in speaker_segments) / len(speaker_segments)
                    st.metric("Avg Confidence", f"{avg_confidence:.1%}")
                    
                    speaking_ratio = (total_time / result.audio_duration) * 100
                    st.metric("Speaking Ratio", f"{speaking_ratio:.1f}%")
                
                # Show segments
                st.markdown("**Segments:**")
                for i, segment in enumerate(speaker_segments[:5]):  # Show first 5 segments
                    st.write(f"{i+1}. {segment.start_time:.1f}s - {segment.end_time:.1f}s ({segment.duration:.1f}s)")
                    if segment.text:
                        st.caption(f"Text: {segment.text}")
                
                if len(speaker_segments) > 5:
                    st.caption(f"... and {len(speaker_segments) - 5} more segments")
        
        # Export options
        st.subheader("Export Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export Timeline Data"):
                # Convert to export format
                export_data = {
                    'speakers': list(result.speakers),
                    'segments': [seg.to_dict() for seg in result.segments],
                    'metadata': result.metadata,
                    'audio_duration': result.audio_duration
                }
                
                import json
                st.download_button(
                    label="Download JSON",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"speaker_diarization_{len(result.speakers)}_speakers.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("Export Speaker Stats"):
                # Create speaker statistics
                stats_data = []
                for speaker_id in result.speakers:
                    speaker_segments = [seg for seg in result.segments if seg.speaker_id == speaker_id]
                    total_time = sum(seg.duration for seg in speaker_segments)
                    avg_confidence = sum(seg.confidence for seg in speaker_segments) / len(speaker_segments)
                    
                    stats_data.append({
                        'Speaker': speaker_id,
                        'Segments': len(speaker_segments),
                        'Total Time (s)': round(total_time, 1),
                        'Avg Confidence': f"{avg_confidence:.1%}",
                        'Speaking Ratio': f"{(total_time / result.audio_duration) * 100:.1f}%"
                    })
                
                import pandas as pd
                df = pd.DataFrame(stats_data)
                csv = df.to_csv(index=False)
                
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"speaker_stats_{len(result.speakers)}_speakers.csv",
                    mime="text/csv"
                )