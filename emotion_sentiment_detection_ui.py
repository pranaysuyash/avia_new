"""
Streamlit UI for Emotion and Sentiment Detection System

This module provides a comprehensive user interface for emotion detection,
sentiment analysis, mood tracking, and stress/fatigue analysis from audio recordings.
"""

import streamlit as st
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import tempfile
import logging

# Import the main emotion detection system
try:
    from emotion_sentiment_detection import (
        EmotionSentimentSystem, EmotionResult, SentimentResult, 
        MoodState, StressFatigueResult
    )
except ImportError:
    st.error("Could not import emotion_sentiment_detection module. Please ensure it's available.")
    st.stop()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_session_state():
    """Initialize session state variables"""
    if 'emotion_system' not in st.session_state:
        st.session_state.emotion_system = EmotionSentimentSystem()
    
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False

def display_emotion_timeline(emotion_results):
    """Display emotion timeline visualization"""
    if not emotion_results:
        st.warning("No emotion data available for visualization")
        return
    
    # Convert to DataFrame for easier handling
    df = pd.DataFrame([
        {
            'timestamp': r['timestamp'],
            'emotion': r['primary_emotion'],
            'confidence': r['confidence'],
            'arousal': r['arousal'],
            'valence': r['valence'],
            'intensity': r['intensity']
        }
        for r in emotion_results
    ])
    
    # Create emotion timeline
    fig = make_subplots(
        rows=4, cols=1,
        subplot_titles=['Primary Emotions', 'Confidence', 'Arousal (Energy)', 'Valence (Positive/Negative)'],
        vertical_spacing=0.08
    )
    
    # Color mapping for emotions
    emotion_colors = {
        'happy': '#FFD700', 'excited': '#FF6347', 'surprise': '#FF69B4',
        'calm': '#87CEEB', 'neutral': '#D3D3D3', 'sad': '#4169E1',
        'angry': '#DC143C', 'fear': '#8A2BE2', 'disgust': '#228B22',
        'stressed': '#B22222'
    }
    
    # Primary emotions
    colors = [emotion_colors.get(emotion, '#D3D3D3') for emotion in df['emotion']]
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['emotion'],
            mode='markers+lines',
            marker=dict(color=colors, size=10),
            name='Primary Emotion',
            hovertemplate='<b>Time:</b> %{x:.1f}s<br><b>Emotion:</b> %{y}<br><b>Confidence:</b> %{customdata:.2f}<extra></extra>',
            customdata=df['confidence']
        ),
        row=1, col=1
    )
    
    # Confidence
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'], y=df['confidence'],
            mode='lines+markers', marker=dict(color='blue', size=6),
            name='Confidence'
        ),
        row=2, col=1
    )
    
    # Arousal
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'], y=df['arousal'],
            mode='lines+markers', marker=dict(color='red', size=6),
            name='Arousal'
        ),
        row=3, col=1
    )
    
    # Valence
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'], y=df['valence'],
            mode='lines+markers', marker=dict(color='green', size=6),
            name='Valence'
        ),
        row=4, col=1
    )
    
    fig.update_layout(
        title='Emotional Timeline Analysis',
        height=800,
        showlegend=False
    )
    
    fig.update_xaxes(title_text="Time (seconds)")
    fig.update_yaxes(title_text="Emotion", row=1, col=1)
    fig.update_yaxes(title_text="Confidence", range=[0, 1], row=2, col=1)
    fig.update_yaxes(title_text="Arousal", range=[0, 1], row=3, col=1)
    fig.update_yaxes(title_text="Valence", range=[0, 1], row=4, col=1)
    
    st.plotly_chart(fig, use_container_width=True)

def display_sentiment_analysis(sentiment_results):
    """Display sentiment analysis results"""
    if not sentiment_results:
        st.warning("No sentiment data available for visualization")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame([
        {
            'timestamp': r['timestamp'],
            'sentiment': r['sentiment'],
            'polarity': r['polarity'],
            'subjectivity': r['subjectivity'],
            'confidence': r['confidence'],
            'text_sentiment': r['text_sentiment'],
            'audio_sentiment': r['audio_sentiment']
        }
        for r in sentiment_results
    ])
    
    # Create sentiment visualization
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=['Sentiment Over Time', 'Polarity Distribution', 
                       'Text vs Audio Sentiment', 'Subjectivity'],
        vertical_spacing=0.15
    )
    
    # Sentiment timeline
    sentiment_colors = {'positive': 'green', 'negative': 'red', 'neutral': 'gray'}
    colors = [sentiment_colors.get(s, 'gray') for s in df['sentiment']]
    
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'], y=df['polarity'],
            mode='markers+lines',
            marker=dict(color=colors, size=8),
            name='Sentiment Polarity'
        ),
        row=1, col=1
    )
    
    # Polarity distribution
    fig.add_trace(
        go.Histogram(x=df['polarity'], nbinsx=20, name='Polarity Distribution'),
        row=1, col=2
    )
    
    # Text vs Audio sentiment
    fig.add_trace(
        go.Scatter(
            x=df['text_sentiment'], y=df['audio_sentiment'],
            mode='markers',
            marker=dict(color=df['confidence'], colorscale='Viridis', size=8),
            name='Text vs Audio'
        ),
        row=2, col=1
    )
    
    # Subjectivity
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'], y=df['subjectivity'],
            mode='lines+markers', marker=dict(color='purple', size=6),
            name='Subjectivity'
        ),
        row=2, col=2
    )
    
    fig.update_layout(
        title='Sentiment Analysis Results',
        height=700,
        showlegend=False
    )
    
    # Add reference lines
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=1)
    fig.add_shape(type="line", x0=-1, y0=-1, x1=1, y1=1, 
                  line=dict(dash="dash", color="gray"), row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)

def display_mood_tracking(mood_states):
    """Display mood tracking results"""
    if not mood_states:
        st.warning("No mood data available for visualization")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame([
        {
            'timestamp': m['timestamp'],
            'mood': m['mood'],
            'energy_level': m['energy_level'],
            'stress_level': m['stress_level'],
            'fatigue_level': m['fatigue_level'],
            'engagement_level': m['engagement_level'],
            'emotional_stability': m['emotional_stability']
        }
        for m in mood_states
    ])
    
    # Create mood dashboard
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=['Energy Level', 'Stress Level', 'Fatigue Level', 
                       'Engagement Level', 'Emotional Stability', 'Mood Distribution'],
        vertical_spacing=0.1,
        horizontal_spacing=0.1
    )
    
    # Energy level
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['energy_level'], 
                  mode='lines+markers', name='Energy', 
                  line=dict(color='orange')),
        row=1, col=1
    )
    
    # Stress level
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['stress_level'], 
                  mode='lines+markers', name='Stress', 
                  line=dict(color='red')),
        row=1, col=2
    )
    
    # Fatigue level
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['fatigue_level'], 
                  mode='lines+markers', name='Fatigue', 
                  line=dict(color='purple')),
        row=2, col=1
    )
    
    # Engagement level
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['engagement_level'], 
                  mode='lines+markers', name='Engagement', 
                  line=dict(color='green')),
        row=2, col=2
    )
    
    # Emotional stability
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['emotional_stability'], 
                  mode='lines+markers', name='Stability', 
                  line=dict(color='blue')),
        row=3, col=1
    )
    
    # Mood distribution
    mood_counts = df['mood'].value_counts()
    fig.add_trace(
        go.Bar(x=list(mood_counts.index), y=list(mood_counts.values), 
              name='Mood Distribution', marker_color='lightblue'),
        row=3, col=2
    )
    
    fig.update_layout(
        title='Comprehensive Mood Analysis',
        height=900,
        showlegend=False
    )
    
    # Update y-axes to 0-1 range except mood distribution
    for row in range(1, 4):
        for col in range(1, 3):
            if not (row == 3 and col == 2):
                fig.update_yaxes(range=[0, 1], row=row, col=col)
    
    st.plotly_chart(fig, use_container_width=True)

def display_stress_fatigue_analysis(stress_fatigue_results):
    """Display stress and fatigue analysis"""
    if not stress_fatigue_results:
        st.warning("No stress/fatigue data available for visualization")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame([
        {
            'timestamp': r['timestamp'],
            'stress_level': r['stress_level'],
            'fatigue_level': r['fatigue_level'],
            'cognitive_load': r['cognitive_load'],
            'vocal_strain': r['vocal_strain'],
            'speaking_rate_deviation': r['speaking_rate_deviation'],
            'pause_frequency': r['pause_frequency']
        }
        for r in stress_fatigue_results
    ])
    
    # Create stress/fatigue analysis
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=['Stress & Fatigue Levels', 'Cognitive Load & Vocal Strain', 
                       'Speaking Rate Deviation', 'Pause Frequency'],
        vertical_spacing=0.15
    )
    
    # Stress and fatigue
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['stress_level'], 
                  mode='lines+markers', name='Stress', 
                  line=dict(color='red')),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['fatigue_level'], 
                  mode='lines+markers', name='Fatigue', 
                  line=dict(color='purple')),
        row=1, col=1
    )
    
    # Cognitive load and vocal strain
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['cognitive_load'], 
                  mode='lines+markers', name='Cognitive Load', 
                  line=dict(color='orange')),
        row=1, col=2
    )
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['vocal_strain'], 
                  mode='lines+markers', name='Vocal Strain', 
                  line=dict(color='brown')),
        row=1, col=2
    )
    
    # Speaking rate deviation
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['speaking_rate_deviation'], 
                  mode='lines+markers', name='Rate Deviation', 
                  line=dict(color='green')),
        row=2, col=1
    )
    
    # Pause frequency
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['pause_frequency'], 
                  mode='lines+markers', name='Pause Frequency', 
                  line=dict(color='blue')),
        row=2, col=2
    )
    
    fig.update_layout(
        title='Stress and Fatigue Analysis',
        height=700,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_analysis_summary(summary):
    """Display analysis summary"""
    if not summary:
        st.warning("No summary data available")
        return
    
    st.subheader("📊 Analysis Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Duration Analyzed", 
            f"{summary.get('duration_analyzed', 0):.1f}s"
        )
    
    with col2:
        st.metric(
            "Dominant Emotion", 
            summary.get('dominant_emotion', 'Unknown').title()
        )
    
    with col3:
        sentiment_score = summary.get('average_sentiment', 0)
        sentiment_label = "Positive" if sentiment_score > 0.1 else "Negative" if sentiment_score < -0.1 else "Neutral"
        st.metric(
            "Average Sentiment", 
            sentiment_label,
            f"{sentiment_score:.2f}"
        )
    
    with col4:
        stability = summary.get('emotional_stability', 0.5)
        st.metric(
            "Emotional Stability", 
            f"{stability:.2f}",
            delta=f"{(stability - 0.5):.2f}" if stability != 0.5 else None
        )
    
    # Stress indicators
    if 'stress_indicators' in summary:
        st.subheader("🚨 Stress Indicators")
        stress_data = summary['stress_indicators']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            stress_level = stress_data.get('average_stress_level', 0)
            st.metric(
                "Average Stress Level", 
                f"{stress_level:.2f}",
                delta="High" if stress_level > 0.7 else "Normal"
            )
        
        with col2:
            fatigue_level = stress_data.get('average_fatigue_level', 0)
            st.metric(
                "Average Fatigue Level", 
                f"{fatigue_level:.2f}",
                delta="High" if fatigue_level > 0.7 else "Normal"
            )
        
        with col3:
            cognitive_load = stress_data.get('average_cognitive_load', 0)
            st.metric(
                "Cognitive Load", 
                f"{cognitive_load:.2f}",
                delta="High" if cognitive_load > 0.7 else "Normal"
            )
        
        # High stress/fatigue periods
        if stress_data.get('high_stress_periods', 0) > 0 or stress_data.get('high_fatigue_periods', 0) > 0:
            st.warning(f"⚠️ Detected {stress_data.get('high_stress_periods', 0)} high-stress periods and {stress_data.get('high_fatigue_periods', 0)} high-fatigue periods")
    
    # Key insights
    if 'key_insights' in summary and summary['key_insights']:
        st.subheader("💡 Key Insights")
        for insight in summary['key_insights']:
            st.info(f"• {insight}")

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Emotion & Sentiment Detection",
        page_icon="🎭",
        layout="wide"
    )
    
    st.title("🎭 Emotion & Sentiment Detection System")
    st.markdown("Advanced emotion detection, sentiment analysis, mood tracking, and stress/fatigue analysis from audio recordings")
    
    # Initialize session state
    init_session_state()
    
    # Sidebar for controls
    with st.sidebar:
        st.header("🎛️ Analysis Controls")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload Audio File",
            type=['wav', 'mp3', 'm4a', 'flac'],
            help="Upload an audio file for emotion and sentiment analysis"
        )
        
        # Transcript input
        transcript = st.text_area(
            "Transcript (Optional)",
            height=100,
            help="Provide transcript for enhanced sentiment analysis. Leave empty for audio-only analysis."
        )
        
        # Analysis options
        st.subheader("Analysis Options")
        
        segment_duration = st.slider(
            "Segment Duration (seconds)",
            min_value=1.0,
            max_value=10.0,
            value=3.0,
            step=0.5,
            help="Duration of each analysis segment"
        )
        
        include_mood_tracking = st.checkbox(
            "Include Mood Tracking",
            value=True,
            help="Enable continuous mood tracking (requires transcript)"
        )
        
        include_stress_analysis = st.checkbox(
            "Include Stress/Fatigue Analysis",
            value=True,
            help="Enable stress and fatigue detection"
        )
        
        # Analysis button
        if st.button("🚀 Start Analysis", type="primary"):
            if uploaded_file is not None:
                with st.spinner("Processing audio file..."):
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        temp_audio_path = tmp_file.name
                    
                    try:
                        # Perform analysis
                        results = st.session_state.emotion_system.analyze_complete(
                            temp_audio_path, 
                            transcript if transcript.strip() else ""
                        )
                        
                        if 'error' not in results:
                            st.session_state.analysis_results = results
                            st.session_state.processing_complete = True
                            st.success("✅ Analysis completed successfully!")
                        else:
                            st.error(f"❌ Analysis failed: {results['error']}")
                    
                    except Exception as e:
                        st.error(f"❌ Error during analysis: {str(e)}")
                    
                    finally:
                        # Clean up temporary file
                        if os.path.exists(temp_audio_path):
                            os.unlink(temp_audio_path)
            else:
                st.warning("⚠️ Please upload an audio file first")
        
        # Export results
        if st.session_state.processing_complete and st.session_state.analysis_results:
            if st.button("💾 Export Results"):
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"emotion_analysis_{timestamp}.json"
                    
                    # Save results
                    with open(filename, 'w') as f:
                        json.dump(st.session_state.analysis_results, f, indent=2, default=str)
                    
                    # Provide download
                    with open(filename, 'r') as f:
                        st.download_button(
                            label="📥 Download Results",
                            data=f.read(),
                            file_name=filename,
                            mime="application/json"
                        )
                    
                    st.success(f"✅ Results exported to {filename}")
                
                except Exception as e:
                    st.error(f"❌ Export failed: {str(e)}")
    
    # Main content area
    if st.session_state.processing_complete and st.session_state.analysis_results:
        results = st.session_state.analysis_results
        
        # Display summary
        if 'summary' in results:
            display_analysis_summary(results['summary'])
        
        # Create tabs for different visualizations
        tabs = st.tabs([
            "🎭 Emotions", 
            "💭 Sentiment", 
            "🌡️ Mood Tracking", 
            "😰 Stress & Fatigue",
            "📊 Raw Data"
        ])
        
        with tabs[0]:
            st.header("🎭 Emotion Detection Results")
            if 'emotions' in results and results['emotions']:
                display_emotion_timeline(results['emotions'])
                
                # Emotion statistics
                st.subheader("📈 Emotion Statistics")
                emotion_df = pd.DataFrame(results['emotions'])
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Emotion distribution
                    emotion_counts = emotion_df['primary_emotion'].value_counts()
                    fig = px.pie(
                        values=emotion_counts.values,
                        names=emotion_counts.index,
                        title="Emotion Distribution"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Average metrics
                    st.metric("Average Confidence", f"{emotion_df['confidence'].mean():.2f}")
                    st.metric("Average Arousal", f"{emotion_df['arousal'].mean():.2f}")
                    st.metric("Average Valence", f"{emotion_df['valence'].mean():.2f}")
                    st.metric("Average Intensity", f"{emotion_df['intensity'].mean():.2f}")
            else:
                st.info("No emotion data available")
        
        with tabs[1]:
            st.header("💭 Sentiment Analysis Results")
            if 'sentiments' in results and results['sentiments']:
                display_sentiment_analysis(results['sentiments'])
                
                # Sentiment statistics
                st.subheader("📈 Sentiment Statistics")
                sentiment_df = pd.DataFrame(results['sentiments'])
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    avg_polarity = sentiment_df['polarity'].mean()
                    st.metric("Average Polarity", f"{avg_polarity:.2f}")
                
                with col2:
                    avg_subjectivity = sentiment_df['subjectivity'].mean()
                    st.metric("Average Subjectivity", f"{avg_subjectivity:.2f}")
                
                with col3:
                    sentiment_counts = sentiment_df['sentiment'].value_counts()
                    dominant_sentiment = sentiment_counts.index[0]
                    st.metric("Dominant Sentiment", dominant_sentiment.title())
            else:
                st.info("No sentiment data available (transcript required)")
        
        with tabs[2]:
            st.header("🌡️ Mood Tracking Results")
            if 'mood_states' in results and results['mood_states']:
                display_mood_tracking(results['mood_states'])
            else:
                st.info("No mood tracking data available (transcript required)")
        
        with tabs[3]:
            st.header("😰 Stress & Fatigue Analysis")
            if 'stress_fatigue' in results and results['stress_fatigue']:
                display_stress_fatigue_analysis(results['stress_fatigue'])
                
                # Stress/fatigue statistics
                st.subheader("📈 Stress & Fatigue Statistics")
                stress_df = pd.DataFrame(results['stress_fatigue'])
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    avg_stress = stress_df['stress_level'].mean()
                    st.metric("Average Stress", f"{avg_stress:.2f}")
                
                with col2:
                    avg_fatigue = stress_df['fatigue_level'].mean()
                    st.metric("Average Fatigue", f"{avg_fatigue:.2f}")
                
                with col3:
                    avg_cognitive = stress_df['cognitive_load'].mean()
                    st.metric("Average Cognitive Load", f"{avg_cognitive:.2f}")
                
                with col4:
                    avg_strain = stress_df['vocal_strain'].mean()
                    st.metric("Average Vocal Strain", f"{avg_strain:.2f}")
            else:
                st.info("No stress/fatigue data available")
        
        with tabs[4]:
            st.header("📊 Raw Data")
            
            # Display raw data tables
            data_tabs = st.tabs(["Emotions", "Sentiments", "Mood States", "Stress/Fatigue"])
            
            with data_tabs[0]:
                if 'emotions' in results and results['emotions']:
                    st.dataframe(pd.DataFrame(results['emotions']))
                else:
                    st.info("No emotion data available")
            
            with data_tabs[1]:
                if 'sentiments' in results and results['sentiments']:
                    st.dataframe(pd.DataFrame(results['sentiments']))
                else:
                    st.info("No sentiment data available")
            
            with data_tabs[2]:
                if 'mood_states' in results and results['mood_states']:
                    st.dataframe(pd.DataFrame(results['mood_states']))
                else:
                    st.info("No mood data available")
            
            with data_tabs[3]:
                if 'stress_fatigue' in results and results['stress_fatigue']:
                    st.dataframe(pd.DataFrame(results['stress_fatigue']))
                else:
                    st.info("No stress/fatigue data available")
    
    else:
        # Welcome screen
        st.markdown("""
        ## 🎯 Welcome to the Emotion & Sentiment Detection System
        
        This advanced system provides comprehensive analysis of emotional content in audio recordings:
        
        ### 🎭 **Emotion Detection**
        - Voice-based emotion recognition using acoustic features
        - Real-time emotion tracking with confidence scores
        - Arousal and valence analysis
        - Support for 10+ emotion categories
        
        ### 💭 **Sentiment Analysis**
        - Multi-modal sentiment analysis (text + audio)
        - Polarity and subjectivity scoring
        - Combined text and voice sentiment evaluation
        
        ### 🌡️ **Mood Tracking**
        - Continuous mood monitoring throughout recordings
        - Energy, stress, and engagement level tracking
        - Emotional stability analysis
        
        ### 😰 **Stress & Fatigue Detection**
        - Voice-based stress level detection
        - Fatigue and cognitive load analysis
        - Vocal strain and speaking pattern analysis
        
        ### 📊 **Interactive Visualizations**
        - Real-time emotional timeline charts
        - Sentiment heatmaps and distributions
        - Comprehensive mood dashboards
        - Stress and fatigue analysis plots
        
        ---
        
        **To get started:**
        1. Upload an audio file using the sidebar
        2. Optionally provide a transcript for enhanced analysis
        3. Configure analysis settings
        4. Click "Start Analysis" to begin processing
        
        **Supported formats:** WAV, MP3, M4A, FLAC
        """)
        
        # Feature showcase
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info("""
            **🎭 Emotion Features**
            - Real-time detection
            - 10+ emotion categories
            - Confidence scoring
            - Arousal/valence mapping
            """)
        
        with col2:
            st.success("""
            **💭 Sentiment Features**
            - Multi-modal analysis
            - Text + audio fusion
            - Polarity scoring
            - Subjectivity analysis
            """)
        
        with col3:
            st.warning("""
            **😰 Stress Features**
            - Voice stress detection
            - Fatigue monitoring
            - Cognitive load analysis
            - Speaking pattern analysis
            """)

if __name__ == "__main__":
    main()