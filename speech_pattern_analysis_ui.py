"""
Speech Pattern Analysis UI

Streamlit interface for comprehensive speech pattern analysis including:
- Speech rate analysis and speaking pattern detection
- Pause detection and silence analysis
- Filler word detection and removal
- Speaking confidence and hesitation analysis
- Speech coaching suggestions based on patterns

Requirements: 3.1, 5.1
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import io
import base64

# Import our speech analysis system
from speech_pattern_analysis import (
    SpeechPatternAnalysisSystem,
    SpeechSegment,
    ComprehensiveSpeechAnalysis,
    format_analysis_report,
    create_sample_segments
)

def init_session_state():
    """Initialize session state variables"""
    if 'speech_analysis_system' not in st.session_state:
        st.session_state.speech_analysis_system = SpeechPatternAnalysisSystem()
    
    if 'current_analysis' not in st.session_state:
        st.session_state.current_analysis = None
    
    if 'analysis_history' not in st.session_state:
        st.session_state.analysis_history = []

def create_speech_rate_chart(analysis: ComprehensiveSpeechAnalysis) -> go.Figure:
    """Create speech rate visualization"""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Words per Minute', 'Rate Variability', 'Speaking Time Distribution', 'Tempo Changes'),
        specs=[[{"type": "indicator"}, {"type": "bar"}],
               [{"type": "pie"}, {"type": "scatter"}]]
    )
    
    # Words per minute gauge
    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=analysis.speech_rate.words_per_minute,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "WPM"},
            delta={'reference': 160},  # Optimal WPM
            gauge={
                'axis': {'range': [None, 250]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 140], 'color': "lightgray"},
                    {'range': [140, 180], 'color': "lightgreen"},
                    {'range': [180, 250], 'color': "lightgray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 180
                }
            }
        ),
        row=1, col=1
    )
    
    # Rate variability
    fig.add_trace(
        go.Bar(
            x=['Rate Variability'],
            y=[analysis.speech_rate.speech_rate_variability],
            marker_color='orange',
            name='Variability'
        ),
        row=1, col=2
    )
    
    # Speaking time distribution
    speaking_time = analysis.speech_rate.speaking_time
    total_time = analysis.speech_rate.total_time
    pause_time = total_time - speaking_time
    
    fig.add_trace(
        go.Pie(
            labels=['Speaking Time', 'Pause Time'],
            values=[speaking_time, pause_time],
            hole=0.3,
            marker_colors=['lightblue', 'lightcoral']
        ),
        row=2, col=1
    )
    
    # Tempo changes
    if analysis.speech_rate.tempo_changes:
        times, rates = zip(*analysis.speech_rate.tempo_changes)
        fig.add_trace(
            go.Scatter(
                x=times,
                y=rates,
                mode='markers+lines',
                marker=dict(size=8, color='red'),
                name='Tempo Changes'
            ),
            row=2, col=2
        )
    
    fig.update_layout(
        height=600,
        title_text="Speech Rate Analysis",
        showlegend=False
    )
    
    return fig

def create_pause_analysis_chart(analysis: ComprehensiveSpeechAnalysis) -> go.Figure:
    """Create pause analysis visualization"""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Pause Timeline', 'Pause Duration Distribution', 'Pause Statistics', 'Pause Frequency'),
        specs=[[{"type": "scatter"}, {"type": "histogram"}],
               [{"type": "bar"}, {"type": "indicator"}]]
    )
    
    # Pause timeline
    if analysis.pause_analysis.pause_locations:
        starts, ends = zip(*analysis.pause_analysis.pause_locations)
        durations = [end - start for start, end in analysis.pause_analysis.pause_locations]
        
        fig.add_trace(
            go.Scatter(
                x=starts,
                y=durations,
                mode='markers',
                marker=dict(
                    size=[d*10 for d in durations],  # Size proportional to duration
                    color=durations,
                    colorscale='Reds',
                    showscale=True,
                    colorbar=dict(title="Duration (s)")
                ),
                name='Pauses',
                hovertemplate='Time: %{x:.1f}s<br>Duration: %{y:.2f}s<extra></extra>'
            ),
            row=1, col=1
        )
    
    # Pause duration distribution
    if analysis.pause_analysis.pause_locations:
        durations = [end - start for start, end in analysis.pause_analysis.pause_locations]
        fig.add_trace(
            go.Histogram(
                x=durations,
                nbinsx=10,
                marker_color='lightblue',
                name='Duration Distribution'
            ),
            row=1, col=2
        )
    
    # Pause statistics
    stats = [
        analysis.pause_analysis.total_pause_time,
        analysis.pause_analysis.pause_count,
        analysis.pause_analysis.average_pause_duration,
        analysis.pause_analysis.longest_pause
    ]
    stat_names = ['Total Time', 'Count', 'Avg Duration', 'Longest']
    
    fig.add_trace(
        go.Bar(
            x=stat_names,
            y=stats,
            marker_color=['lightgreen', 'lightblue', 'orange', 'red'],
            name='Statistics'
        ),
        row=2, col=1
    )
    
    # Pause frequency indicator
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=analysis.pause_analysis.pause_frequency,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Pauses/Min"},
            gauge={
                'axis': {'range': [None, 30]},
                'bar': {'color': "darkgreen"},
                'steps': [
                    {'range': [0, 8], 'color': "lightgray"},
                    {'range': [8, 15], 'color': "lightgreen"},
                    {'range': [15, 30], 'color': "lightgray"}
                ]
            }
        ),
        row=2, col=2
    )
    
    fig.update_layout(
        height=600,
        title_text="Pause Analysis",
        showlegend=False
    )
    
    return fig

def create_filler_analysis_chart(analysis: ComprehensiveSpeechAnalysis) -> go.Figure:
    """Create filler word analysis visualization"""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Filler Word Frequency', 'Filler Timeline', 'Hesitation Types', 'Filler Percentage'),
        specs=[[{"type": "bar"}, {"type": "scatter"}],
               [{"type": "pie"}, {"type": "indicator"}]]
    )
    
    # Filler word frequency
    if analysis.filler_analysis.filler_words:
        words = list(analysis.filler_analysis.filler_words.keys())
        counts = list(analysis.filler_analysis.filler_words.values())
        
        fig.add_trace(
            go.Bar(
                x=words,
                y=counts,
                marker_color='lightcoral',
                name='Filler Words'
            ),
            row=1, col=1
        )
    
    # Filler timeline
    if analysis.filler_analysis.hesitation_markers:
        times, fillers = zip(*analysis.filler_analysis.hesitation_markers)
        fig.add_trace(
            go.Scatter(
                x=times,
                y=[1] * len(times),  # All at same height
                mode='markers',
                marker=dict(
                    size=10,
                    color='red',
                    symbol='x'
                ),
                text=fillers,
                hovertemplate='Time: %{x:.1f}s<br>Filler: %{text}<extra></extra>',
                name='Hesitations'
            ),
            row=1, col=2
        )
    
    # Hesitation types
    hesitation_types = {
        'Filler Words': analysis.filler_analysis.total_filler_count,
        'Repetitions': len(analysis.filler_analysis.repetitions),
        'False Starts': len(analysis.filler_analysis.false_starts)
    }
    
    fig.add_trace(
        go.Pie(
            labels=list(hesitation_types.keys()),
            values=list(hesitation_types.values()),
            hole=0.3,
            marker_colors=['lightcoral', 'orange', 'yellow']
        ),
        row=2, col=1
    )
    
    # Filler percentage indicator
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=analysis.filler_analysis.filler_percentage,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Filler %"},
            gauge={
                'axis': {'range': [None, 20]},
                'bar': {'color': "darkred"},
                'steps': [
                    {'range': [0, 5], 'color': "lightgreen"},
                    {'range': [5, 10], 'color': "yellow"},
                    {'range': [10, 20], 'color': "lightcoral"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 5
                }
            }
        ),
        row=2, col=2
    )
    
    fig.update_layout(
        height=600,
        title_text="Filler Word Analysis",
        showlegend=False
    )
    
    return fig

def create_confidence_analysis_chart(analysis: ComprehensiveSpeechAnalysis) -> go.Figure:
    """Create confidence analysis visualization"""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Overall Confidence', 'Confidence Components', 'Confidence Timeline', 'Hesitation Frequency'),
        specs=[[{"type": "indicator"}, {"type": "bar"}],
               [{"type": "scatter"}, {"type": "indicator"}]]
    )
    
    # Overall confidence indicator
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=analysis.confidence_analysis.overall_confidence_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Confidence"},
            gauge={
                'axis': {'range': [None, 1]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 0.4], 'color': "lightcoral"},
                    {'range': [0.4, 0.7], 'color': "yellow"},
                    {'range': [0.7, 1], 'color': "lightgreen"}
                ]
            }
        ),
        row=1, col=1
    )
    
    # Confidence components
    components = [
        'Voice Stability',
        'Pace Consistency',
        'Volume Consistency'
    ]
    values = [
        analysis.confidence_analysis.voice_stability,
        analysis.confidence_analysis.pace_consistency,
        analysis.confidence_analysis.volume_consistency
    ]
    
    fig.add_trace(
        go.Bar(
            x=components,
            y=values,
            marker_color=['lightblue', 'lightgreen', 'orange'],
            name='Components'
        ),
        row=1, col=2
    )
    
    # Confidence timeline
    if analysis.confidence_analysis.confidence_timeline:
        times, confidences = zip(*analysis.confidence_analysis.confidence_timeline)
        fig.add_trace(
            go.Scatter(
                x=times,
                y=confidences,
                mode='lines+markers',
                marker=dict(color='blue'),
                name='Confidence Over Time'
            ),
            row=2, col=1
        )
    
    # Hesitation frequency indicator
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=analysis.confidence_analysis.hesitation_frequency,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Hesitations/s"},
            gauge={
                'axis': {'range': [None, 2]},
                'bar': {'color': "darkorange"},
                'steps': [
                    {'range': [0, 0.2], 'color': "lightgreen"},
                    {'range': [0.2, 0.5], 'color': "yellow"},
                    {'range': [0.5, 2], 'color': "lightcoral"}
                ]
            }
        ),
        row=2, col=2
    )
    
    fig.update_layout(
        height=600,
        title_text="Confidence Analysis",
        showlegend=False
    )
    
    return fig

def display_coaching_suggestions(analysis: ComprehensiveSpeechAnalysis):
    """Display coaching suggestions in an organized format"""
    suggestions = analysis.coaching_suggestions
    
    # Overall rating
    st.subheader("📊 Overall Performance Rating")
    
    rating_color = {
        "Excellent": "green",
        "Good": "blue", 
        "Fair": "orange",
        "Needs Improvement": "red"
    }.get(suggestions.overall_rating, "gray")
    
    st.markdown(f"<h3 style='color: {rating_color};'>{suggestions.overall_rating}</h3>", 
                unsafe_allow_html=True)
    
    # Priority areas
    if suggestions.priority_areas:
        st.subheader("🎯 Priority Areas for Improvement")
        for area in suggestions.priority_areas:
            st.markdown(f"• **{area}**")
    
    # Detailed suggestions in tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🏃 Pace", "⏸️ Pauses", "🗣️ Fillers", "💪 Confidence"])
    
    with tab1:
        st.subheader("Speaking Pace Suggestions")
        if suggestions.pace_suggestions:
            for suggestion in suggestions.pace_suggestions:
                st.markdown(f"• {suggestion}")
        else:
            st.info("No specific pace suggestions - you're doing well!")
    
    with tab2:
        st.subheader("Pause Management Suggestions")
        if suggestions.pause_suggestions:
            for suggestion in suggestions.pause_suggestions:
                st.markdown(f"• {suggestion}")
        else:
            st.info("Your pause usage is well-balanced!")
    
    with tab3:
        st.subheader("Filler Word Reduction Tips")
        if suggestions.filler_reduction_tips:
            for tip in suggestions.filler_reduction_tips:
                st.markdown(f"• {tip}")
        else:
            st.info("Great job keeping filler words to a minimum!")
    
    with tab4:
        st.subheader("Confidence Building Tips")
        if suggestions.confidence_building_tips:
            for tip in suggestions.confidence_building_tips:
                st.markdown(f"• {tip}")
        else:
            st.info("You're speaking with good confidence!")

def create_summary_metrics(analysis: ComprehensiveSpeechAnalysis):
    """Create summary metrics display"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Words per Minute",
            value=f"{analysis.speech_rate.words_per_minute:.0f}",
            delta=f"{analysis.speech_rate.words_per_minute - 160:.0f}" if analysis.speech_rate.words_per_minute > 0 else None
        )
    
    with col2:
        st.metric(
            label="Filler Percentage",
            value=f"{analysis.filler_analysis.filler_percentage:.1f}%",
            delta=f"{5.0 - analysis.filler_analysis.filler_percentage:.1f}%" if analysis.filler_analysis.filler_percentage > 0 else None,
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            label="Confidence Score",
            value=f"{analysis.confidence_analysis.overall_confidence_score:.2f}",
            delta=f"{analysis.confidence_analysis.overall_confidence_score - 0.7:.2f}"
        )
    
    with col4:
        st.metric(
            label="Pauses per Minute",
            value=f"{analysis.pause_analysis.pause_frequency:.1f}",
            delta=f"{analysis.pause_analysis.pause_frequency - 11.5:.1f}" if analysis.pause_analysis.pause_frequency > 0 else None
        )

def export_analysis_report(analysis: ComprehensiveSpeechAnalysis) -> str:
    """Export analysis as downloadable report"""
    report = format_analysis_report(analysis)
    return report

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Speech Pattern Analysis",
        page_icon="🎤",
        layout="wide"
    )
    
    init_session_state()
    
    st.title("🎤 Speech Pattern Analysis System")
    st.markdown("Comprehensive analysis of speech patterns, pace, pauses, and confidence")
    
    # Sidebar for controls
    with st.sidebar:
        st.header("Analysis Controls")
        
        # Analysis mode selection
        analysis_mode = st.selectbox(
            "Analysis Mode",
            ["Upload Audio", "Demo Analysis", "Analysis History"]
        )
        
        if analysis_mode == "Upload Audio":
            st.subheader("Upload Audio File")
            uploaded_file = st.file_uploader(
                "Choose an audio file",
                type=['wav', 'mp3', 'm4a', 'flac'],
                help="Upload an audio file for speech pattern analysis"
            )
            
            if uploaded_file:
                st.success(f"File uploaded: {uploaded_file.name}")
                
                # Transcript input
                st.subheader("Transcript")
                transcript_text = st.text_area(
                    "Enter the transcript (optional)",
                    height=150,
                    help="Provide transcript for more accurate analysis"
                )
                
                if st.button("Analyze Speech Patterns", type="primary"):
                    if transcript_text.strip():
                        # Save uploaded file temporarily
                        import tempfile
                        import os
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            temp_path = tmp_file.name
                        
                        try:
                            with st.spinner("Analyzing speech patterns..."):
                                # Create segments from transcript
                                segments = create_sample_segments(transcript_text, 60.0)  # Assume 60s duration
                                
                                # Perform analysis
                                analysis = st.session_state.speech_analysis_system.analyze_speech_patterns(
                                    temp_path, segments
                                )
                                
                                st.session_state.current_analysis = analysis
                                st.success("Analysis completed!")
                        
                        except Exception as e:
                            st.error(f"Analysis failed: {str(e)}")
                        
                        finally:
                            # Clean up temporary file
                            if os.path.exists(temp_path):
                                os.unlink(temp_path)
                    else:
                        st.warning("Please provide a transcript for analysis")
        
        elif analysis_mode == "Demo Analysis":
            st.subheader("Demo Analysis")
            
            demo_texts = {
                "Professional Speaker": "Good morning everyone. Today I want to discuss the importance of effective communication in business environments.",
                "Nervous Speaker": "Um, hello everyone. I, uh, I want to talk about, like, communication today. You know, it's really important and, er, I think we should focus on it.",
                "Fast Speaker": "Hello everyone today I want to talk about communication it's really important and we need to focus on effective strategies for business success.",
                "Slow Speaker": "Good... morning... everyone. Today... I want to... discuss... the importance... of effective... communication."
            }
            
            selected_demo = st.selectbox("Select Demo Type", list(demo_texts.keys()))
            
            if st.button("Run Demo Analysis", type="primary"):
                with st.spinner("Running demo analysis..."):
                    try:
                        # Create segments from demo text
                        demo_text = demo_texts[selected_demo]
                        segments = create_sample_segments(demo_text, 15.0)
                        
                        # Create a dummy audio path for demo
                        demo_audio_path = f"demo_{selected_demo.lower().replace(' ', '_')}.wav"
                        
                        # For demo, we'll create a mock analysis
                        from speech_pattern_analysis import (
                            SpeechRateAnalysis, PauseAnalysis, FillerWordAnalysis,
                            ConfidenceAnalysis, SpeechCoachingSuggestions, ComprehensiveSpeechAnalysis
                        )
                        
                        # Create mock analysis based on demo type
                        if "Nervous" in selected_demo:
                            mock_analysis = ComprehensiveSpeechAnalysis(
                                speech_rate=SpeechRateAnalysis(120, 180, 600, 12, 15, 25, [(5, 100), (10, 140)]),
                                pause_analysis=PauseAnalysis(3.5, 8, 0.44, 1.2, [(2, 2.5), (7, 8.2)], 32),
                                filler_analysis=FillerWordAnalysis(
                                    {'um': 3, 'uh': 2, 'like': 2, 'er': 1}, 8, 12.5,
                                    [(1.5, 'um'), (4.2, 'uh'), (8.7, 'like')], [], []
                                ),
                                confidence_analysis=ConfidenceAnalysis(0.45, 0.8, 0.4, 0.3, 0.6, [(0, 0.4), (7.5, 0.5)]),
                                coaching_suggestions=SpeechCoachingSuggestions([], [], [], [], "Needs Improvement", []),
                                analysis_timestamp=datetime.now(),
                                audio_duration=15.0
                            )
                        else:
                            mock_analysis = ComprehensiveSpeechAnalysis(
                                speech_rate=SpeechRateAnalysis(160, 240, 800, 13, 15, 15, []),
                                pause_analysis=PauseAnalysis(2.0, 5, 0.4, 0.8, [(3, 3.4), (9, 9.8)], 20),
                                filler_analysis=FillerWordAnalysis({'um': 1}, 1, 2.1, [(6.5, 'um')], [], []),
                                confidence_analysis=ConfidenceAnalysis(0.85, 0.2, 0.9, 0.8, 0.85, [(0, 0.8), (7.5, 0.9)]),
                                coaching_suggestions=SpeechCoachingSuggestions([], [], [], [], "Good", []),
                                analysis_timestamp=datetime.now(),
                                audio_duration=15.0
                            )
                        
                        # Generate coaching suggestions
                        mock_analysis.coaching_suggestions = st.session_state.speech_analysis_system.speech_coach.generate_suggestions(mock_analysis)
                        
                        st.session_state.current_analysis = mock_analysis
                        st.success("Demo analysis completed!")
                        
                    except Exception as e:
                        st.error(f"Demo analysis failed: {str(e)}")
        
        elif analysis_mode == "Analysis History":
            st.subheader("Analysis History")
            
            if st.button("Load Recent Analyses"):
                history = st.session_state.speech_analysis_system.get_analysis_history(10)
                st.session_state.analysis_history = history
                
                if history:
                    st.success(f"Loaded {len(history)} recent analyses")
                else:
                    st.info("No analysis history found")
            
            # Display history
            if st.session_state.analysis_history:
                for i, record in enumerate(st.session_state.analysis_history):
                    with st.expander(f"Analysis {i+1}: {record['created_at']}"):
                        st.write(f"**Audio:** {record['audio_path']}")
                        st.write(f"**Date:** {record['created_at']}")
                        
                        if st.button(f"Load Analysis {i+1}", key=f"load_{i}"):
                            # Reconstruct analysis object
                            analysis_data = record['analysis_data']
                            st.session_state.current_analysis = analysis_data
                            st.success("Analysis loaded!")
    
    # Main content area
    if st.session_state.current_analysis:
        analysis = st.session_state.current_analysis
        
        # Summary metrics
        st.subheader("📈 Summary Metrics")
        create_summary_metrics(analysis)
        
        st.divider()
        
        # Analysis tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🏃 Speech Rate", "⏸️ Pauses", "🗣️ Fillers", "💪 Confidence", "🎯 Coaching"
        ])
        
        with tab1:
            st.plotly_chart(create_speech_rate_chart(analysis), use_container_width=True)
            
            # Detailed metrics
            with st.expander("Detailed Speech Rate Metrics"):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Words per Minute", f"{analysis.speech_rate.words_per_minute:.1f}")
                    st.metric("Syllables per Minute", f"{analysis.speech_rate.syllables_per_minute:.1f}")
                with col2:
                    st.metric("Speaking Time", f"{analysis.speech_rate.speaking_time:.1f}s")
                    st.metric("Rate Variability", f"{analysis.speech_rate.speech_rate_variability:.2f}")
        
        with tab2:
            st.plotly_chart(create_pause_analysis_chart(analysis), use_container_width=True)
            
            # Detailed metrics
            with st.expander("Detailed Pause Metrics"):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Pause Time", f"{analysis.pause_analysis.total_pause_time:.1f}s")
                    st.metric("Number of Pauses", analysis.pause_analysis.pause_count)
                with col2:
                    st.metric("Average Duration", f"{analysis.pause_analysis.average_pause_duration:.2f}s")
                    st.metric("Longest Pause", f"{analysis.pause_analysis.longest_pause:.2f}s")
        
        with tab3:
            st.plotly_chart(create_filler_analysis_chart(analysis), use_container_width=True)
            
            # Detailed metrics
            with st.expander("Detailed Filler Word Analysis"):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Filler Words", analysis.filler_analysis.total_filler_count)
                    st.metric("Filler Percentage", f"{analysis.filler_analysis.filler_percentage:.1f}%")
                with col2:
                    st.metric("Repetitions", len(analysis.filler_analysis.repetitions))
                    st.metric("False Starts", len(analysis.filler_analysis.false_starts))
                
                if analysis.filler_analysis.filler_words:
                    st.subheader("Filler Word Breakdown")
                    filler_df = pd.DataFrame(
                        list(analysis.filler_analysis.filler_words.items()),
                        columns=['Filler Word', 'Count']
                    ).sort_values('Count', ascending=False)
                    st.dataframe(filler_df, use_container_width=True)
        
        with tab4:
            st.plotly_chart(create_confidence_analysis_chart(analysis), use_container_width=True)
            
            # Detailed metrics
            with st.expander("Detailed Confidence Metrics"):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Overall Confidence", f"{analysis.confidence_analysis.overall_confidence_score:.2f}")
                    st.metric("Voice Stability", f"{analysis.confidence_analysis.voice_stability:.2f}")
                with col2:
                    st.metric("Pace Consistency", f"{analysis.confidence_analysis.pace_consistency:.2f}")
                    st.metric("Volume Consistency", f"{analysis.confidence_analysis.volume_consistency:.2f}")
        
        with tab5:
            display_coaching_suggestions(analysis)
        
        st.divider()
        
        # Export options
        st.subheader("📄 Export Analysis")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 Copy Report to Clipboard"):
                report = export_analysis_report(analysis)
                st.code(report, language="text")
        
        with col2:
            report = export_analysis_report(analysis)
            st.download_button(
                label="📄 Download Report",
                data=report,
                file_name=f"speech_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
        
        with col3:
            # Export as JSON
            analysis_json = json.dumps(analysis.to_dict() if hasattr(analysis, 'to_dict') else analysis, 
                                     indent=2, default=str)
            st.download_button(
                label="📊 Download JSON",
                data=analysis_json,
                file_name=f"speech_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    else:
        # Welcome screen
        st.markdown("""
        ## Welcome to Speech Pattern Analysis! 🎤
        
        This comprehensive system analyzes your speech patterns and provides detailed insights including:
        
        ### 📊 Analysis Features
        - **Speech Rate Analysis**: Words per minute, syllables per minute, tempo variations
        - **Pause Detection**: Strategic pause usage, timing, and frequency
        - **Filler Word Analysis**: Detection of "um", "uh", "like" and other hesitations
        - **Confidence Assessment**: Voice stability, pace consistency, overall confidence
        - **Coaching Suggestions**: Personalized tips for improvement
        
        ### 🚀 Getting Started
        1. **Upload Audio**: Use the sidebar to upload your audio file
        2. **Provide Transcript**: Enter the spoken text for accurate analysis
        3. **Run Analysis**: Click "Analyze Speech Patterns" to begin
        4. **Review Results**: Explore detailed visualizations and coaching tips
        5. **Export Report**: Download your analysis for future reference
        
        ### 🎯 Demo Mode
        Try our demo analysis with different speaker types to see how the system works!
        
        ---
        *Select an option from the sidebar to begin your speech analysis journey.*
        """)

if __name__ == "__main__":
    main()