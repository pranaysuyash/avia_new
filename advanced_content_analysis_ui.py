"""
Advanced Content Analysis UI Components
UI implementation for Task 39: Create advanced AI-powered content analysis
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import time

from advanced_content_analysis import (
    advanced_content_analyzer, emotion_detector, speaking_pattern_analyzer,
    complexity_analyzer, bias_detector, plagiarism_detector,
    EmotionAnalysis, SpeakingPatternAnalysis, ContentComplexityAnalysis,
    BiasDetectionAnalysis, PlagiarismAnalysis
)


class AdvancedContentAnalysisUI:
    """UI components for advanced content analysis"""
    
    def __init__(self):
        self.analyzer = advanced_content_analyzer
    
    def render_advanced_analysis_interface(self):
        """Render the main advanced content analysis interface"""
        st.markdown("## 🧠 Advanced AI-Powered Content Analysis")
        
        st.info("Analyze your content for emotions, speaking patterns, complexity, bias, and originality using advanced AI techniques.")
        
        # Create tabs for different analysis types
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Complete Analysis",
            "😊 Emotion Analysis", 
            "🎤 Speaking Patterns",
            "📚 Content Complexity",
            "⚖️ Bias Detection",
            "🔍 Plagiarism Check"
        ])
        
        with tab1:
            self._render_complete_analysis()
        
        with tab2:
            self._render_emotion_analysis()
        
        with tab3:
            self._render_speaking_pattern_analysis()
        
        with tab4:
            self._render_complexity_analysis()
        
        with tab5:
            self._render_bias_detection()
        
        with tab6:
            self._render_plagiarism_detection()
    
    def _render_complete_analysis(self):
        """Render complete content analysis"""
        st.markdown("### 🎯 Comprehensive Content Analysis")
        
        # Input selection
        content_source = st.radio(
            "Content Source",
            ["Current Session", "Upload Text", "Enter Manually"],
            horizontal=True,
            help="Choose the source of content to analyze"
        )
        
        content_text = ""
        audio_duration = None
        
        if content_source == "Current Session":
            # Get from current session if available
            if hasattr(st.session_state, 'transcript') and st.session_state.transcript:
                content_text = st.session_state.transcript
                audio_duration = getattr(st.session_state, 'audio_duration', None)
                
                st.text_area("Current Session Content", value=content_text, height=200, disabled=True)
                
                if audio_duration:
                    st.info(f"Audio duration: {audio_duration:.1f} seconds")
            else:
                st.warning("No content available in current session")
        
        elif content_source == "Upload Text":
            uploaded_file = st.file_uploader("Upload Text File", type=['txt'])
            if uploaded_file:
                content_text = uploaded_file.read().decode('utf-8')
                st.text_area("Uploaded Content", value=content_text, height=200, disabled=True)
        
        else:  # Enter Manually
            content_text = st.text_area(
                "Enter Content to Analyze",
                height=200,
                placeholder="Paste or type your content here..."
            )
            
            # Optional audio duration input
            audio_duration = st.number_input(
                "Audio Duration (seconds, optional)",
                min_value=0.0,
                value=0.0,
                help="If this content comes from audio, specify the duration for speaking pattern analysis"
            )
            if audio_duration == 0.0:
                audio_duration = None
        
        # Analysis options
        st.markdown("#### Analysis Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            include_emotions = st.checkbox("Emotion Analysis", value=True)
            include_patterns = st.checkbox("Speaking Patterns", value=True)
            include_complexity = st.checkbox("Content Complexity", value=True)
        
        with col2:
            include_bias = st.checkbox("Bias Detection", value=True)
            include_plagiarism = st.checkbox("Plagiarism Check", value=False, 
                                           help="Requires reference database")
            
            if include_plagiarism:
                st.info("Plagiarism detection requires a reference database. Upload reference texts or use built-in database.")
        
        # Run analysis
        if content_text and st.button("🧠 Run Complete Analysis", type="primary"):
            self._run_complete_analysis(
                content_text, audio_duration, 
                include_emotions, include_patterns, include_complexity,
                include_bias, include_plagiarism
            )
    
    def _run_complete_analysis(self, text: str, audio_duration: Optional[float],
                              include_emotions: bool, include_patterns: bool,
                              include_complexity: bool, include_bias: bool,
                              include_plagiarism: bool):
        """Run complete content analysis"""
        
        with st.spinner("🧠 Running comprehensive content analysis..."):
            # Prepare analysis parameters
            analysis_params = {
                'text': text,
                'audio_duration': audio_duration,
                'timestamps': None,  # Could be enhanced to use actual timestamps
                'reference_database': None  # Could be enhanced with user-provided database
            }
            
            # Run analysis
            results = self.analyzer.analyze_content(**analysis_params)
        
        if 'error' in results:
            st.error(f"Analysis failed: {results['error']}")
            return
        
        # Display results
        st.success("✅ Analysis completed!")
        
        # Overall scores
        if 'overall_score' in results:
            self._display_overall_scores(results['overall_score'])
        
        # Individual analysis results
        if include_emotions and 'emotions' in results:
            st.markdown("---")
            st.markdown("### 😊 Emotion Analysis Results")
            self._display_emotion_results(results['emotions'])
        
        if include_patterns and 'speaking_patterns' in results:
            st.markdown("---")
            st.markdown("### 🎤 Speaking Pattern Results")
            self._display_speaking_pattern_results(results['speaking_patterns'])
        
        if include_complexity and 'complexity' in results:
            st.markdown("---")
            st.markdown("### 📚 Content Complexity Results")
            self._display_complexity_results(results['complexity'])
        
        if include_bias and 'bias' in results:
            st.markdown("---")
            st.markdown("### ⚖️ Bias Detection Results")
            self._display_bias_results(results['bias'])
        
        if include_plagiarism and 'plagiarism' in results:
            st.markdown("---")
            st.markdown("### 🔍 Plagiarism Check Results")
            self._display_plagiarism_results(results['plagiarism'])
    
    def _display_overall_scores(self, scores: Dict[str, float]):
        """Display overall quality scores"""
        st.markdown("### 🎯 Overall Content Quality Scores")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            score = scores.get('emotional_engagement', 0)
            st.metric("Emotional Engagement", f"{score:.2f}", delta=None)
            st.progress(score)
        
        with col2:
            score = scores.get('communication_clarity', 0)
            st.metric("Communication Clarity", f"{score:.2f}", delta=None)
            st.progress(score)
        
        with col3:
            score = scores.get('inclusivity', 0)
            st.metric("Inclusivity", f"{score:.2f}", delta=None)
            st.progress(score)
        
        with col4:
            score = scores.get('originality', 0)
            st.metric("Originality", f"{score:.2f}", delta=None)
            st.progress(score)
        
        with col5:
            score = scores.get('overall_quality', 0)
            st.metric("Overall Quality", f"{score:.2f}", delta=None)
            st.progress(score)
        
        # Radar chart of scores
        categories = list(scores.keys())
        values = list(scores.values())
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Content Quality Scores'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=False,
            title="Content Quality Overview"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_emotion_analysis(self):
        """Render emotion analysis interface"""
        st.markdown("### 😊 Emotion Detection and Mood Tracking")
        
        st.info("Analyze the emotional content and mood patterns in your text.")
        
        # Input text
        text_input = st.text_area(
            "Text to Analyze",
            height=150,
            placeholder="Enter text for emotion analysis..."
        )
        
        if text_input and st.button("😊 Analyze Emotions"):
            with st.spinner("Analyzing emotions..."):
                result = emotion_detector.analyze_emotions(text_input)
            
            self._display_emotion_results(result)
    
    def _display_emotion_results(self, result: EmotionAnalysis):
        """Display emotion analysis results"""
        
        # Main emotion metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Dominant Emotion", result.dominant_emotion.title())
        
        with col2:
            st.metric("Confidence", f"{result.confidence:.2%}")
        
        with col3:
            st.metric("Emotional Intensity", f"{result.emotional_intensity:.2f}")
        
        # Emotion scores chart
        if result.emotion_scores:
            emotions = list(result.emotion_scores.keys())
            scores = list(result.emotion_scores.values())
            
            fig = px.bar(
                x=emotions,
                y=scores,
                title="Emotion Scores",
                labels={'x': 'Emotions', 'y': 'Score'}
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        # Emotion timeline if available
        if result.emotion_timeline:
            st.markdown("#### Emotion Timeline")
            
            timeline_data = []
            for segment in result.emotion_timeline:
                timeline_data.append({
                    'Segment': segment['timestamp'],
                    'Dominant Emotion': segment['dominant_emotion'],
                    'Text Preview': segment['text_segment']
                })
            
            df = pd.DataFrame(timeline_data)
            st.dataframe(df, use_container_width=True)
    
    def _render_speaking_pattern_analysis(self):
        """Render speaking pattern analysis interface"""
        st.markdown("### 🎤 Speaking Pattern Analysis")
        
        st.info("Analyze speaking pace, pauses, emphasis, and confidence indicators.")
        
        # Input text and optional duration
        col1, col2 = st.columns([3, 1])
        
        with col1:
            text_input = st.text_area(
                "Text to Analyze",
                height=150,
                placeholder="Enter transcript for speaking pattern analysis..."
            )
        
        with col2:
            audio_duration = st.number_input(
                "Audio Duration (seconds)",
                min_value=0.0,
                value=0.0,
                help="Optional: Specify audio duration for accurate pace calculation"
            )
            if audio_duration == 0.0:
                audio_duration = None
        
        if text_input and st.button("🎤 Analyze Speaking Patterns"):
            with st.spinner("Analyzing speaking patterns..."):
                result = speaking_pattern_analyzer.analyze_speaking_patterns(
                    text_input, audio_duration
                )
            
            self._display_speaking_pattern_results(result)
    
    def _display_speaking_pattern_results(self, result: SpeakingPatternAnalysis):
        """Display speaking pattern analysis results"""
        
        # Main metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Average Pace", f"{result.average_pace:.1f} WPM")
        
        with col2:
            st.metric("Pace Variation", f"{result.pace_variation:.2f}")
        
        with col3:
            st.metric("Pause Frequency", f"{result.pause_frequency:.3f}")
        
        with col4:
            st.metric("Speaking Rhythm", result.speaking_rhythm.title())
        
        # Emphasis points
        if result.emphasis_points:
            st.markdown("#### Emphasis Points")
            
            emphasis_data = []
            for point in result.emphasis_points:
                emphasis_data.append({
                    'Type': point['type'],
                    'Content': point.get('word', point.get('text', '')),
                    'Context': point.get('context', ''),
                    'Frequency': point.get('frequency', 1)
                })
            
            df = pd.DataFrame(emphasis_data)
            st.dataframe(df, use_container_width=True)
        
        # Confidence indicators
        if result.confidence_indicators:
            st.markdown("#### Confidence Indicators")
            
            confidence_types = {'confidence': [], 'uncertainty': []}
            
            for indicator in result.confidence_indicators:
                if indicator.startswith('uncertainty:'):
                    confidence_types['uncertainty'].append(indicator.replace('uncertainty: ', ''))
                else:
                    confidence_types['confidence'].append(indicator)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if confidence_types['confidence']:
                    st.markdown("**Confidence Indicators:**")
                    for indicator in confidence_types['confidence']:
                        st.write(f"• {indicator}")
            
            with col2:
                if confidence_types['uncertainty']:
                    st.markdown("**Uncertainty Indicators:**")
                    for indicator in confidence_types['uncertainty']:
                        st.write(f"• {indicator}")
    
    def _render_complexity_analysis(self):
        """Render content complexity analysis interface"""
        st.markdown("### 📚 Content Complexity and Readability Analysis")
        
        st.info("Analyze content complexity, readability, and get suggestions for improvement.")
        
        # Input text
        text_input = st.text_area(
            "Text to Analyze",
            height=150,
            placeholder="Enter text for complexity analysis..."
        )
        
        if text_input and st.button("📚 Analyze Complexity"):
            with st.spinner("Analyzing content complexity..."):
                result = complexity_analyzer.analyze_complexity(text_input)
            
            self._display_complexity_results(result)
    
    def _display_complexity_results(self, result: ContentComplexityAnalysis):
        """Display content complexity analysis results"""
        
        # Main metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Readability Score", f"{result.readability_score:.1f}")
            st.caption("Higher = easier to read")
        
        with col2:
            st.metric("Grade Level", f"{result.grade_level:.1f}")
            st.caption("Education level required")
        
        with col3:
            st.metric("Complexity Rating", result.complexity_rating.title())
            
            # Color code the rating
            color_map = {
                'simple': '🟢',
                'moderate': '🟡', 
                'complex': '🟠',
                'advanced': '🔴'
            }
            st.caption(f"{color_map.get(result.complexity_rating, '⚪')} Complexity level")
        
        with col4:
            st.metric("Vocabulary Diversity", f"{result.vocabulary_diversity:.2f}")
            st.caption("Unique words ratio")
        
        # Additional metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Sentence Complexity", f"{result.sentence_complexity:.2f}")
            st.caption("Average subordinate clauses")
        
        with col2:
            st.metric("Technical Density", f"{result.technical_density:.3f}")
            st.caption("Technical terms ratio")
        
        # Recommendations
        if result.recommendations:
            st.markdown("#### 💡 Recommendations")
            
            for i, recommendation in enumerate(result.recommendations, 1):
                st.write(f"{i}. {recommendation}")
        
        # Complexity visualization
        complexity_data = {
            'Metric': ['Readability', 'Vocabulary Diversity', 'Sentence Complexity', 'Technical Density'],
            'Score': [
                result.readability_score / 100,  # Normalize to 0-1
                result.vocabulary_diversity,
                min(1.0, result.sentence_complexity / 3),  # Cap at 1.0
                min(1.0, result.technical_density * 10)  # Scale up
            ]
        }
        
        fig = px.bar(
            x=complexity_data['Metric'],
            y=complexity_data['Score'],
            title="Content Complexity Breakdown",
            labels={'x': 'Metrics', 'y': 'Normalized Score'}
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_bias_detection(self):
        """Render bias detection interface"""
        st.markdown("### ⚖️ Bias Detection and Inclusive Language Analysis")
        
        st.info("Detect potential bias and get suggestions for more inclusive language.")
        
        # Input text
        text_input = st.text_area(
            "Text to Analyze",
            height=150,
            placeholder="Enter text for bias detection analysis..."
        )
        
        if text_input and st.button("⚖️ Analyze for Bias"):
            with st.spinner("Analyzing for bias and inclusive language..."):
                result = bias_detector.analyze_bias(text_input)
            
            self._display_bias_results(result)
    
    def _display_bias_results(self, result: BiasDetectionAnalysis):
        """Display bias detection results"""
        
        # Main metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Overall Bias Score", f"{result.bias_score:.2f}")
            st.caption("Lower is better")
            
            # Color code the score
            if result.bias_score < 0.3:
                st.success("Low bias detected")
            elif result.bias_score < 0.6:
                st.warning("Moderate bias detected")
            else:
                st.error("High bias detected")
        
        with col2:
            st.metric("Inclusive Language Score", f"{result.inclusive_language_score:.2f}")
            st.caption("Higher is better")
            st.progress(result.inclusive_language_score)
        
        # Bias categories
        if result.bias_categories:
            st.markdown("#### Bias by Category")
            
            categories = list(result.bias_categories.keys())
            scores = list(result.bias_categories.values())
            
            fig = px.bar(
                x=categories,
                y=scores,
                title="Bias Scores by Category",
                labels={'x': 'Bias Category', 'y': 'Bias Score'}
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        # Detected biases
        if result.detected_biases:
            st.markdown("#### 🚨 Detected Biases")
            
            for bias in result.detected_biases:
                severity_color = {'low': '🟡', 'medium': '🟠', 'high': '🔴'}
                
                with st.expander(f"{severity_color[bias['severity']]} {bias['category'].title()} Bias - {bias['pattern']}"):
                    st.write(f"**Pattern:** {bias['pattern']}")
                    st.write(f"**Severity:** {bias['severity'].title()}")
                    st.write(f"**Context:** {bias['context']}")
        
        # Problematic phrases
        if result.problematic_phrases:
            st.markdown("#### 💡 Suggested Improvements")
            
            for phrase in result.problematic_phrases:
                st.write(f"• Replace **'{phrase['phrase']}'** with **'{phrase['alternative']}'**")
                st.caption(f"Context: {phrase['context']}")
        
        # General suggestions
        if result.suggestions:
            st.markdown("#### 📝 General Suggestions")
            
            for suggestion in result.suggestions:
                st.write(f"• {suggestion}")
    
    def _render_plagiarism_detection(self):
        """Render plagiarism detection interface"""
        st.markdown("### 🔍 Plagiarism Detection and Originality Check")
        
        st.info("Check content originality against reference databases.")
        
        # Input text
        text_input = st.text_area(
            "Text to Analyze",
            height=150,
            placeholder="Enter text for plagiarism detection..."
        )
        
        # Reference database options
        st.markdown("#### Reference Database")
        
        database_option = st.radio(
            "Database Source",
            ["Built-in Database", "Upload Reference Texts", "No Database (Originality Only)"],
            help="Choose the reference database for comparison"
        )
        
        reference_database = None
        
        if database_option == "Upload Reference Texts":
            uploaded_files = st.file_uploader(
                "Upload Reference Text Files",
                type=['txt'],
                accept_multiple_files=True,
                help="Upload text files to use as reference database"
            )
            
            if uploaded_files:
                reference_database = []
                for file in uploaded_files:
                    content = file.read().decode('utf-8')
                    reference_database.append(content)
                
                st.success(f"Loaded {len(reference_database)} reference documents")
        
        if text_input and st.button("🔍 Check for Plagiarism"):
            with st.spinner("Checking for plagiarism and analyzing originality..."):
                result = plagiarism_detector.analyze_plagiarism(text_input, reference_database)
            
            self._display_plagiarism_results(result)
    
    def _display_plagiarism_results(self, result: PlagiarismAnalysis):
        """Display plagiarism detection results"""
        
        # Main metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Similarity Score", f"{result.similarity_score:.2%}")
            st.caption("Lower is better")
            
            # Color code the score
            if result.similarity_score < 0.15:
                st.success("Low similarity")
            elif result.similarity_score < 0.4:
                st.warning("Moderate similarity")
            else:
                st.error("High similarity")
        
        with col2:
            st.metric("Originality Score", f"{result.originality_score:.2%}")
            st.caption("Higher is better")
            st.progress(result.originality_score)
        
        with col3:
            st.metric("Analysis Confidence", f"{result.confidence:.2%}")
            st.caption("Based on database size")
        
        # Potential matches
        if result.potential_matches:
            st.markdown("#### 🎯 Potential Matches")
            
            matches_data = []
            for match in result.potential_matches:
                matches_data.append({
                    'Reference ID': match['reference_id'],
                    'Similarity': f"{match['similarity']:.2%}",
                    'Match Type': match['match_type'],
                    'Reference Text': match['reference_text']
                })
            
            df = pd.DataFrame(matches_data)
            st.dataframe(df, use_container_width=True)
        
        # Flagged segments
        if result.flagged_segments:
            st.markdown("#### 🚨 Flagged Segments")
            
            for i, segment in enumerate(result.flagged_segments, 1):
                with st.expander(f"Flagged Segment {i} (Similarity: {segment['similarity']:.2%})"):
                    st.markdown("**Your Text:**")
                    st.write(segment['segment'])
                    
                    st.markdown("**Similar Reference:**")
                    st.write(segment['reference_segment'])
        
        # Overall assessment
        st.markdown("#### 📋 Overall Assessment")
        
        if result.originality_score > 0.8:
            st.success("✅ Content appears to be highly original")
        elif result.originality_score > 0.6:
            st.info("ℹ️ Content shows good originality with minor similarities")
        elif result.originality_score > 0.4:
            st.warning("⚠️ Content has moderate similarities to existing sources")
        else:
            st.error("🚨 Content shows significant similarities to existing sources")


# Global UI instance
advanced_content_analysis_ui = AdvancedContentAnalysisUI()