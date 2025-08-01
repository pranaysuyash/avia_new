"""
Content Insights UI Components for Streamlit
"""

import streamlit as st
import asyncio
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Optional, Dict, Any, List

from content_insights import ContentInsightsAnalyzer, ContentInsights


class ContentInsightsUI:
    """Content insights user interface"""
    
    def __init__(self):
        self.analyzer = ContentInsightsAnalyzer()
    
    def render_insights_analyzer(self, 
                               transcript: str = None,
                               speaker_segments: List[Dict[str, Any]] = None) -> Optional[ContentInsights]:
        """Render content insights analysis interface"""
        st.header("🧠 AI Content Insights")
        
        if not transcript:
            # Text input for analysis
            transcript = st.text_area(
                "Enter transcript text for analysis",
                height=200,
                placeholder="Paste your transcript here..."
            )
        
        if not transcript or not transcript.strip():
            st.info("Enter transcript text to generate AI-powered insights")
            return None
        
        # Analysis options
        st.subheader("Analysis Options")
        col1, col2 = st.columns(2)
        
        with col1:
            include_sentiment = st.checkbox("Sentiment Analysis", value=True)
            include_topics = st.checkbox("Topic Extraction", value=True)
        
        with col2:
            include_summary = st.checkbox("Content Summary", value=True)
            include_speakers = st.checkbox("Speaker Analysis", value=bool(speaker_segments))
        
        # Run analysis
        if st.button("Generate Insights", type="primary"):
            with st.spinner("Analyzing content with AI..."):
                try:
                    # Run async analysis
                    insights = asyncio.run(self.analyzer.analyze_content(
                        transcript=transcript,
                        speaker_segments=speaker_segments if include_speakers else None
                    ))
                    
                    # Display results
                    self._display_insights(insights, include_sentiment, include_topics, include_summary, include_speakers)
                    return insights
                    
                except Exception as e:
                    st.error(f"Analysis failed: {str(e)}")
                    return None
        
        return None
    
    def _display_insights(self, 
                         insights: ContentInsights,
                         show_sentiment: bool = True,
                         show_topics: bool = True,
                         show_summary: bool = True,
                         show_speakers: bool = True):
        """Display content insights results"""
        st.success("🎉 Content insights generated successfully!")
        
        # Create tabs for different sections
        tabs = []
        if show_summary:
            tabs.append("📝 Summary")
        if show_sentiment:
            tabs.append("😊 Sentiment")
        if show_topics:
            tabs.append("🏷️ Topics")
        if show_speakers and insights.speaker_insights:
            tabs.append("🎤 Speakers")
        tabs.extend(["⭐ Key Moments", "📊 Analytics"])
        
        tab_objects = st.tabs(tabs)
        tab_index = 0
        
        # Summary tab
        if show_summary:
            with tab_objects[tab_index]:
                self._render_summary_tab(insights.summary)
            tab_index += 1
        
        # Sentiment tab
        if show_sentiment:
            with tab_objects[tab_index]:
                self._render_sentiment_tab(insights.sentiment)
            tab_index += 1
        
        # Topics tab
        if show_topics:
            with tab_objects[tab_index]:
                self._render_topics_tab(insights.topics)
            tab_index += 1
        
        # Speakers tab
        if show_speakers and insights.speaker_insights:
            with tab_objects[tab_index]:
                self._render_speakers_tab(insights.speaker_insights)
            tab_index += 1
        
        # Key moments tab
        with tab_objects[tab_index]:
            self._render_key_moments_tab(insights.key_moments)
        tab_index += 1
        
        # Analytics tab
        with tab_objects[tab_index]:
            self._render_analytics_tab(insights)
        
        # Export options
        st.markdown("---")
        st.subheader("📤 Export Insights")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Download JSON"):
                insights_json = json.dumps(insights.to_dict(), indent=2)
                st.download_button(
                    label="💾 Download JSON",
                    data=insights_json,
                    file_name=f"content_insights_{insights.transcript_id}.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("Generate Report"):
                report = self._generate_text_report(insights)
                st.download_button(
                    label="📄 Download Report",
                    data=report,
                    file_name=f"insights_report_{insights.transcript_id}.txt",
                    mime="text/plain"
                )
        
        with col3:
            if st.button("Copy Summary"):
                st.code(insights.summary.standard, language=None)
                st.info("Copy the summary text above")
    
    def _render_summary_tab(self, summary):
        """Render summary tab content"""
        st.subheader("📝 Content Summary")
        
        # Summary levels
        st.markdown("**Brief Summary (1-2 sentences):**")
        st.info(summary.brief)
        
        st.markdown("**Standard Summary:**")
        st.write(summary.standard)
        
        if summary.detailed != summary.standard:
            st.markdown("**Detailed Summary:**")
            st.write(summary.detailed)
        
        # Key points
        if summary.key_points:
            st.markdown("**Key Points:**")
            for i, point in enumerate(summary.key_points, 1):
                st.write(f"{i}. {point}")
        
        # Action items
        if summary.action_items:
            st.markdown("**Action Items:**")
            for i, item in enumerate(summary.action_items, 1):
                st.write(f"• {item}")
    
    def _render_sentiment_tab(self, sentiment):
        """Render sentiment analysis tab"""
        st.subheader("😊 Sentiment Analysis")
        
        # Overall sentiment
        col1, col2 = st.columns(2)
        
        with col1:
            # Sentiment indicator
            sentiment_emoji = {
                'positive': '😊',
                'negative': '😞', 
                'neutral': '😐'
            }
            
            st.metric(
                "Overall Sentiment",
                f"{sentiment_emoji.get(sentiment.overall_sentiment, '😐')} {sentiment.overall_sentiment.title()}",
                f"Confidence: {sentiment.confidence:.1%}"
            )
        
        with col2:
            # Sentiment scores chart
            fig = go.Figure(data=[
                go.Bar(
                    x=['Positive', 'Negative', 'Neutral'],
                    y=[sentiment.positive_score, sentiment.negative_score, sentiment.neutral_score],
                    marker_color=['green', 'red', 'gray']
                )
            ])
            fig.update_layout(
                title="Sentiment Scores",
                yaxis_title="Score",
                showlegend=False,
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Emotions
        if sentiment.emotions:
            st.markdown("**Detected Emotions:**")
            
            # Create emotions chart
            emotions_df = pd.DataFrame([
                {'Emotion': emotion.title(), 'Score': score}
                for emotion, score in sentiment.emotions.items()
            ]).sort_values('Score', ascending=True)
            
            if not emotions_df.empty:
                fig = px.bar(
                    emotions_df,
                    x='Score',
                    y='Emotion',
                    orientation='h',
                    title="Emotion Analysis",
                    color='Score',
                    color_continuous_scale='viridis'
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
    
    def _render_topics_tab(self, topics):
        """Render topics analysis tab"""
        st.subheader("🏷️ Topic Analysis")
        
        if not topics:
            st.info("No topics identified in the content")
            return
        
        # Topics overview
        st.markdown(f"**{len(topics)} main topics identified:**")
        
        for i, topic in enumerate(topics, 1):
            with st.expander(f"🏷️ Topic {i}: {topic.topic}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Confidence", f"{topic.confidence:.1%}")
                    st.metric("Relevance", f"{topic.relevance_score:.1%}")
                
                with col2:
                    st.markdown("**Keywords:**")
                    st.write(", ".join(topic.keywords))
                
                st.markdown("**Description:**")
                st.write(topic.description)
        
        # Topics visualization
        if len(topics) > 1:
            fig = go.Figure(data=[
                go.Scatter(
                    x=[t.confidence for t in topics],
                    y=[t.relevance_score for t in topics],
                    mode='markers+text',
                    text=[t.topic for t in topics],
                    textposition="top center",
                    marker=dict(size=20, color=[t.confidence for t in topics], colorscale='viridis', showscale=True)
                )
            ])
            fig.update_layout(
                title="Topics: Confidence vs Relevance",
                xaxis_title="Confidence",
                yaxis_title="Relevance Score",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_speakers_tab(self, speaker_insights):
        """Render speaker analysis tab"""
        st.subheader("🎤 Speaker Analysis")
        
        if not speaker_insights:
            st.info("No speaker data available")
            return
        
        # Speaker metrics overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Speakers", len(speaker_insights))
        
        with col2:
            total_time = sum(s.speaking_time for s in speaker_insights)
            st.metric("Total Speaking Time", f"{total_time:.1f}s")
        
        with col3:
            total_words = sum(s.word_count for s in speaker_insights)
            st.metric("Total Words", total_words)
        
        # Individual speaker analysis
        for speaker in speaker_insights:
            with st.expander(f"🎤 {speaker.speaker_id}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Speaking Time", f"{speaker.speaking_time:.1f}s")
                    st.metric("Word Count", speaker.word_count)
                
                with col2:
                    st.metric("Speaking Pace", f"{speaker.avg_speaking_pace:.1f} WPM")
                    st.metric("Communication Style", speaker.communication_style.title())
                
                with col3:
                    sentiment_emoji = {'positive': '😊', 'negative': '😞', 'neutral': '😐'}
                    st.metric(
                        "Sentiment",
                        f"{sentiment_emoji.get(speaker.sentiment.overall_sentiment, '😐')} {speaker.sentiment.overall_sentiment.title()}"
                    )
                
                if speaker.key_topics:
                    st.markdown("**Key Topics:**")
                    st.write(", ".join(speaker.key_topics))
        
        # Speaker comparison chart
        if len(speaker_insights) > 1:
            speakers_df = pd.DataFrame([
                {
                    'Speaker': s.speaker_id,
                    'Speaking Time': s.speaking_time,
                    'Word Count': s.word_count,
                    'Speaking Pace': s.avg_speaking_pace
                }
                for s in speaker_insights
            ])
            
            fig = make_subplots(
                rows=1, cols=3,
                subplot_titles=('Speaking Time', 'Word Count', 'Speaking Pace'),
                specs=[[{"type": "bar"}, {"type": "bar"}, {"type": "bar"}]]
            )
            
            fig.add_trace(go.Bar(x=speakers_df['Speaker'], y=speakers_df['Speaking Time'], name='Time'), row=1, col=1)
            fig.add_trace(go.Bar(x=speakers_df['Speaker'], y=speakers_df['Word Count'], name='Words'), row=1, col=2)
            fig.add_trace(go.Bar(x=speakers_df['Speaker'], y=speakers_df['Speaking Pace'], name='Pace'), row=1, col=3)
            
            fig.update_layout(height=400, showlegend=False, title_text="Speaker Comparison")
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_key_moments_tab(self, key_moments):
        """Render key moments tab"""
        st.subheader("⭐ Key Moments")
        
        if not key_moments:
            st.info("No key moments identified")
            return
        
        for i, moment in enumerate(key_moments, 1):
            with st.container():
                st.markdown(f"**Key Moment {i}:**")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(moment.get('description', 'No description'))
                    if moment.get('significance'):
                        st.caption(f"*{moment['significance']}*")
                
                with col2:
                    if 'timestamp' in moment:
                        st.metric("Time", f"{moment['timestamp']:.1f}s")
                    
                    moment_type = moment.get('type', 'highlight')
                    type_emoji = {
                        'decision': '🎯',
                        'highlight': '⭐',
                        'action': '✅',
                        'important': '❗'
                    }
                    st.caption(f"{type_emoji.get(moment_type, '⭐')} {moment_type.title()}")
                
                st.markdown("---")
    
    def _render_analytics_tab(self, insights):
        """Render analytics and metrics tab"""
        st.subheader("📊 Content Analytics")
        
        # Content metrics
        st.markdown("**Content Metrics:**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Topics Identified", len(insights.topics))
        
        with col2:
            st.metric("Key Moments", len(insights.key_moments))
        
        with col3:
            if insights.summary.action_items:
                st.metric("Action Items", len(insights.summary.action_items))
            else:
                st.metric("Action Items", 0)
        
        with col4:
            st.metric("Speakers Analyzed", len(insights.speaker_insights))
        
        # Sentiment distribution
        if insights.sentiment:
            st.markdown("**Sentiment Distribution:**")
            sentiment_data = {
                'Positive': insights.sentiment.positive_score,
                'Negative': insights.sentiment.negative_score,
                'Neutral': insights.sentiment.neutral_score
            }
            
            fig = px.pie(
                values=list(sentiment_data.values()),
                names=list(sentiment_data.keys()),
                title="Overall Sentiment Distribution",
                color_discrete_map={
                    'Positive': 'green',
                    'Negative': 'red',
                    'Neutral': 'gray'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Analysis metadata
        if insights.metadata:
            st.markdown("**Analysis Metadata:**")
            st.json(insights.metadata)
    
    def _generate_text_report(self, insights: ContentInsights) -> str:
        """Generate a text report of the insights"""
        report = f"""
CONTENT INSIGHTS REPORT
Generated: {insights.analyzed_at.strftime('%Y-%m-%d %H:%M:%S')}
Transcript ID: {insights.transcript_id}

SUMMARY
=======
{insights.summary.standard}

KEY POINTS:
{chr(10).join(f"• {point}" for point in insights.summary.key_points)}

SENTIMENT ANALYSIS
==================
Overall Sentiment: {insights.sentiment.overall_sentiment.title()} (Confidence: {insights.sentiment.confidence:.1%})
Positive Score: {insights.sentiment.positive_score:.1%}
Negative Score: {insights.sentiment.negative_score:.1%}
Neutral Score: {insights.sentiment.neutral_score:.1%}

TOPICS IDENTIFIED
=================
{chr(10).join(f"{i+1}. {topic.topic} (Confidence: {topic.confidence:.1%})" for i, topic in enumerate(insights.topics))}

KEY MOMENTS
===========
{chr(10).join(f"• {moment.get('description', 'No description')}" for moment in insights.key_moments)}

ACTION ITEMS
============
{chr(10).join(f"• {item}" for item in insights.summary.action_items)}
        """
        
        return report.strip()


def render_content_insights_ui():
    """Main function to render content insights UI"""
    insights_ui = ContentInsightsUI()
    insights_ui.render_insights_analyzer()