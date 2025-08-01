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
            options=["pyannote", "simple_vad", "mock"],
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
            st.experimental_rerun()


def format_time_for_export(seconds: float) -> str:
    """Format time in seconds to HH:MM:SS,mmm format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"