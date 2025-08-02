#!/usr/bin/env python3
"""
AI Content Insights UI Components
Streamlit interface for AI-powered content analysis
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import tempfile
import os

from ai_content_insights import AIContentInsights, ContentType, SentimentType, ActionItemPriority


class AIInsightsUI:
    """Streamlit UI components for AI content insights"""
    
    def __init__(self):
        self.analyzer = AIContentInsights()
        
    def render_main_interface(self):
        """Render the main AI insights interface"""
        st.title("🧠 AI-Powered Content Insights")
        st.markdown("Transform your transcripts into actionable insights with advanced AI analysis")
        
        # Sidebar configuration
        with st.sidebar:
            st.header("⚙️ Analysis Settings")
            
            content_type = st.selectbox(
                "Content Type",
                options=[ct.value for ct in ContentType],
                index=0,
                help="Select the type of content for optimized analysis"
            )
            
            enable_openai = st.checkbox(
                "Enable OpenAI Analysis",
                value=bool(os.getenv('OPENAI_API_KEY')),
                help="Use OpenAI GPT for enhanced analysis (requires API key)"
            )
            
            if enable_openai and not os.getenv('OPENAI_API_KEY'):
                st.warning("⚠️ OpenAI API key not found in environment variables")
        
        # Main content area
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview", 
            "📝 Meeting Minutes", 
            "✅ Action Items", 
            "📈 Sentiment Analysis", 
            "🏷️ Topic Clusters"
        ])
        
        # File upload section
        st.header("📁 Upload Transcript")
        uploaded_file = st.file_uploader(
            "Choose a transcript file",
            type=['json', 'txt'],
            help="Upload a JSON transcript file or plain text file"
        )
        
        if uploaded_file is not None:
            # Process uploaded file
            transcript_data = self._process_uploaded_file(uploaded_file)
            
            if transcript_data:
                # Perform analysis
                with st.spinner("🔍 Analyzing content with AI..."):
                    try:
                        results = self.analyzer.analyze_content(
                            transcript_data=transcript_data,
                            content_type=ContentType(content_type)
                        )
                        
                        # Store results in session state
                        st.session_state.analysis_results = results
                        st.session_state.transcript_data = transcript_data
                        
                        st.success("✅ Analysis completed successfully!")
                        
                    except Exception as e:
                        st.error(f"❌ Analysis failed: {str(e)}")
                        return
        
        # Display results if available
        if hasattr(st.session_state, 'analysis_results'):
            results = st.session_state.analysis_results
            
            with tab1:
                self._render_overview_tab(results)
            
            with tab2:
                self._render_meeting_minutes_tab(results)
            
            with tab3:
                self._render_action_items_tab(results)
            
            with tab4:
                self._render_sentiment_analysis_tab(results)
            
            with tab5:
                self._render_topic_clusters_tab(results)
        
        else:
            st.info("👆 Upload a transcript file to begin AI analysis")
    
    def _process_uploaded_file(self, uploaded_file) -> Optional[Dict[str, Any]]:
        """Process uploaded transcript file"""
        try:
            if uploaded_file.type == "application/json":
                # JSON transcript file
                content = json.loads(uploaded_file.read().decode())
                return content
            
            elif uploaded_file.type == "text/plain":
                # Plain text file - convert to segments
                text = uploaded_file.read().decode()
                sentences = text.split('.')
                
                segments = []
                current_time = 0.0
                
                for i, sentence in enumerate(sentences):
                    if sentence.strip():
                        # Estimate timing (assume 3 seconds per sentence)
                        start_time = current_time
                        end_time = current_time + 3.0
                        
                        segments.append({
                            "start": start_time,
                            "end": end_time,
                            "text": sentence.strip() + ".",
                            "speaker": f"Speaker_{i % 3 + 1}"  # Rotate between 3 speakers
                        })
                        
                        current_time = end_time
                
                return {"segments": segments}
            
            else:
                st.error("Unsupported file type. Please upload JSON or TXT files.")
                return None
                
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            return None
    
    def _render_overview_tab(self, results: Dict[str, Any]):
        """Render the overview tab"""
        st.header("📊 Analysis Overview")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        stats = results.get('transcript_stats', {})
        action_items = results.get('action_items', [])
        topics = results.get('topic_clusters', [])
        sentiment_data = results.get('sentiment_analysis', [])
        
        with col1:
            st.metric(
                "Duration",
                f"{stats.get('total_duration', 0):.1f} min",
                help="Total duration of the content"
            )
        
        with col2:
            st.metric(
                "Word Count",
                f"{stats.get('word_count', 0):,}",
                help="Total number of words in transcript"
            )
        
        with col3:
            st.metric(
                "Action Items",
                len(action_items),
                help="Number of action items identified"
            )
        
        with col4:
            st.metric(
                "Topics",
                len(topics),
                help="Number of topic clusters identified"
            )
        
        # Summary section
        summary = results.get('summary', {})
        if isinstance(summary, dict) and summary.get('executive_summary'):
            st.subheader("📋 Executive Summary")
            st.write(summary['executive_summary'])
            
            if summary.get('key_points'):
                st.subheader("🔑 Key Points")
                for i, point in enumerate(summary['key_points'], 1):
                    st.write(f"{i}. {point}")
        
        # Content categorization
        categories = results.get('content_categories', {})
        if categories:
            st.subheader("🏷️ Content Classification")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Discussion Type:** {categories.get('discussion_type', 'Unknown').title()}")
                st.write(f"**Formality Level:** {categories.get('formality_level', 'Unknown').title()}")
            
            with col2:
                st.write(f"**Technical Level:** {categories.get('technical_level', 'Unknown').title()}")
                st.write(f"**Emotional Tone:** {categories.get('emotional_tone', 'Unknown').title()}")
            
            if categories.get('content_themes'):
                st.write(f"**Main Themes:** {', '.join(categories['content_themes'])}")
        
        # Key insights
        insights = results.get('key_insights', {})
        if insights:
            st.subheader("💡 Key Insights")
            
            for insight_type, insight_list in insights.items():
                if insight_type != 'overall_assessment' and insight_list:
                    st.write(f"**{insight_type.replace('_', ' ').title()}:**")
                    for insight in insight_list:
                        st.write(f"• {insight}")
    
    def _render_meeting_minutes_tab(self, results: Dict[str, Any]):
        """Render the meeting minutes tab"""
        st.header("📝 Meeting Minutes")
        
        meeting_minutes = results.get('meeting_minutes')
        
        if not meeting_minutes:
            st.info("Meeting minutes are only generated for meeting-type content.")
            return
        
        # Meeting header
        st.subheader(f"📅 {meeting_minutes.get('title', 'Meeting Minutes')}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Date:** {meeting_minutes.get('date', 'Unknown')}")
            st.write(f"**Duration:** {meeting_minutes.get('duration', 0):.1f} minutes")
        
        with col2:
            participants = meeting_minutes.get('participants', [])
            if participants:
                st.write(f"**Participants:** {', '.join(participants)}")
        
        # Summary
        if meeting_minutes.get('summary'):
            st.subheader("📋 Summary")
            st.write(meeting_minutes['summary'])
        
        # Agenda items
        agenda_items = meeting_minutes.get('agenda_items', [])
        if agenda_items:
            st.subheader("📋 Agenda Items")
            for i, item in enumerate(agenda_items, 1):
                st.write(f"{i}. {item}")
        
        # Key decisions
        decisions = meeting_minutes.get('key_decisions', [])
        if decisions:
            st.subheader("✅ Key Decisions")
            for i, decision in enumerate(decisions, 1):
                st.write(f"{i}. {decision}")
        
        # Action items
        action_items = meeting_minutes.get('action_items', [])
        if action_items:
            st.subheader("🎯 Action Items")
            for item in action_items:
                priority_color = {
                    'high': '🔴',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(item.get('priority', 'medium'), '🟡')
                
                assignee_text = f" (Assigned to: {item.get('assignee')})" if item.get('assignee') else ""
                due_date_text = f" (Due: {item.get('due_date')})" if item.get('due_date') else ""
                
                st.write(f"{priority_color} {item.get('text', '')}{assignee_text}{due_date_text}")
        
        # Next steps
        next_steps = meeting_minutes.get('next_steps', [])
        if next_steps:
            st.subheader("➡️ Next Steps")
            for i, step in enumerate(next_steps, 1):
                st.write(f"{i}. {step}")
        
        # Topics discussed
        topics = meeting_minutes.get('topics_discussed', [])
        if topics:
            st.subheader("🏷️ Topics Discussed")
            st.write(", ".join(topics))
        
        # Export options
        st.subheader("📤 Export Options")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Export as Text"):
                text_content = self._generate_minutes_text(meeting_minutes)
                st.download_button(
                    label="Download Text File",
                    data=text_content,
                    file_name=f"meeting_minutes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
        
        with col2:
            if st.button("📊 Export as JSON"):
                json_content = json.dumps(meeting_minutes, indent=2, default=str)
                st.download_button(
                    label="Download JSON File",
                    data=json_content,
                    file_name=f"meeting_minutes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
    
    def _render_action_items_tab(self, results: Dict[str, Any]):
        """Render the action items tab"""
        st.header("✅ Action Items Analysis")
        
        action_items = results.get('action_items', [])
        
        if not action_items:
            st.info("No action items were identified in this content.")
            return
        
        # Action items summary
        col1, col2, col3 = st.columns(3)
        
        high_priority = len([item for item in action_items if item.get('priority') == 'high'])
        medium_priority = len([item for item in action_items if item.get('priority') == 'medium'])
        low_priority = len([item for item in action_items if item.get('priority') == 'low'])
        
        with col1:
            st.metric("🔴 High Priority", high_priority)
        with col2:
            st.metric("🟡 Medium Priority", medium_priority)
        with col3:
            st.metric("🟢 Low Priority", low_priority)
        
        # Priority distribution chart
        if action_items:
            priority_data = {
                'Priority': ['High', 'Medium', 'Low'],
                'Count': [high_priority, medium_priority, low_priority],
                'Color': ['#FF4B4B', '#FFA500', '#00C851']
            }
            
            fig = px.pie(
                values=priority_data['Count'],
                names=priority_data['Priority'],
                title="Action Items by Priority",
                color_discrete_sequence=priority_data['Color']
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed action items list
        st.subheader("📋 Detailed Action Items")
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            priority_filter = st.selectbox(
                "Filter by Priority",
                options=['All', 'High', 'Medium', 'Low'],
                index=0
            )
        
        with col2:
            assignee_filter = st.selectbox(
                "Filter by Assignee",
                options=['All'] + list(set([item.get('assignee', 'Unassigned') for item in action_items])),
                index=0
            )
        
        # Apply filters
        filtered_items = action_items
        if priority_filter != 'All':
            filtered_items = [item for item in filtered_items if item.get('priority', '').lower() == priority_filter.lower()]
        
        if assignee_filter != 'All':
            filtered_items = [item for item in filtered_items if item.get('assignee', 'Unassigned') == assignee_filter]
        
        # Display filtered items
        for i, item in enumerate(filtered_items, 1):
            with st.expander(f"Action Item {i}: {item.get('text', '')[:50]}..."):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Full Text:** {item.get('text', '')}")
                    st.write(f"**Context:** {item.get('context', '')}")
                
                with col2:
                    priority_color = {
                        'high': '🔴',
                        'medium': '🟡',
                        'low': '🟢'
                    }.get(item.get('priority', 'medium'), '🟡')
                    
                    st.write(f"**Priority:** {priority_color} {item.get('priority', 'Medium').title()}")
                    st.write(f"**Assignee:** {item.get('assignee', 'Unassigned')}")
                    st.write(f"**Due Date:** {item.get('due_date', 'Not specified')}")
                    st.write(f"**Timestamp:** {item.get('timestamp', 0):.1f}s")
                    st.write(f"**Confidence:** {item.get('confidence', 0):.2f}")
        
        # Export action items
        if st.button("📤 Export Action Items"):
            df = pd.DataFrame(action_items)
            csv_content = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_content,
                file_name=f"action_items_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    def _render_sentiment_analysis_tab(self, results: Dict[str, Any]):
        """Render the sentiment analysis tab"""
        st.header("📈 Sentiment Analysis")
        
        sentiment_data = results.get('sentiment_analysis', [])
        
        if not sentiment_data:
            st.info("No sentiment analysis data available.")
            return
        
        # Sentiment overview
        positive_count = len([s for s in sentiment_data if s.get('sentiment') == 'positive'])
        negative_count = len([s for s in sentiment_data if s.get('sentiment') == 'negative'])
        neutral_count = len(sentiment_data) - positive_count - negative_count
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("😊 Positive", positive_count)
        with col2:
            st.metric("😐 Neutral", neutral_count)
        with col3:
            st.metric("😞 Negative", negative_count)
        
        # Sentiment distribution
        sentiment_counts = {
            'Positive': positive_count,
            'Neutral': neutral_count,
            'Negative': negative_count
        }
        
        fig = px.pie(
            values=list(sentiment_counts.values()),
            names=list(sentiment_counts.keys()),
            title="Overall Sentiment Distribution",
            color_discrete_map={
                'Positive': '#00C851',
                'Neutral': '#FFA500',
                'Negative': '#FF4B4B'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Sentiment timeline
        if len(sentiment_data) > 1:
            st.subheader("📊 Sentiment Timeline")
            
            # Prepare data for timeline
            timestamps = [s.get('timestamp', 0) for s in sentiment_data]
            scores = [s.get('score', 0) for s in sentiment_data]
            sentiments = [s.get('sentiment', 'neutral') for s in sentiment_data]
            
            # Create timeline chart
            fig = go.Figure()
            
            # Add sentiment score line
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=scores,
                mode='lines+markers',
                name='Sentiment Score',
                line=dict(color='blue', width=2),
                marker=dict(
                    color=[
                        '#00C851' if s == 'positive' else '#FF4B4B' if s == 'negative' else '#FFA500'
                        for s in sentiments
                    ],
                    size=8
                )
            ))
            
            # Add zero line
            fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
            
            fig.update_layout(
                title="Sentiment Score Over Time",
                xaxis_title="Time (seconds)",
                yaxis_title="Sentiment Score (-1 to 1)",
                yaxis=dict(range=[-1, 1]),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed sentiment segments
        st.subheader("📝 Sentiment Details")
        
        # Filter by sentiment
        sentiment_filter = st.selectbox(
            "Filter by Sentiment",
            options=['All', 'Positive', 'Negative', 'Neutral'],
            index=0
        )
        
        filtered_sentiment = sentiment_data
        if sentiment_filter != 'All':
            filtered_sentiment = [
                s for s in sentiment_data 
                if s.get('sentiment', '').lower() == sentiment_filter.lower()
            ]
        
        # Display sentiment segments
        for i, segment in enumerate(filtered_sentiment[:20], 1):  # Limit to 20 for performance
            sentiment_emoji = {
                'positive': '😊',
                'negative': '😞',
                'neutral': '😐'
            }.get(segment.get('sentiment', 'neutral'), '😐')
            
            score = segment.get('score', 0)
            confidence = segment.get('confidence', 0)
            
            with st.expander(f"{sentiment_emoji} Segment {i} (Score: {score:.2f})"):
                st.write(f"**Text:** {segment.get('text_segment', '')}")
                st.write(f"**Timestamp:** {segment.get('timestamp', 0):.1f}s")
                st.write(f"**Sentiment:** {segment.get('sentiment', 'Unknown').title()}")
                st.write(f"**Score:** {score:.3f}")
                st.write(f"**Confidence:** {confidence:.3f}")
                
                keywords = segment.get('keywords', [])
                if keywords:
                    st.write(f"**Keywords:** {', '.join(keywords)}")
    
    def _render_topic_clusters_tab(self, results: Dict[str, Any]):
        """Render the topic clusters tab"""
        st.header("🏷️ Topic Clusters")
        
        topics = results.get('topic_clusters', [])
        
        if not topics:
            st.info("No topic clusters were identified in this content.")
            return
        
        # Topics overview
        st.subheader("📊 Topics Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Topics", len(topics))
        
        with col2:
            avg_confidence = sum([t.get('confidence', 0) for t in topics]) / len(topics) if topics else 0
            st.metric("Average Confidence", f"{avg_confidence:.2f}")
        
        # Topic confidence chart
        if topics:
            topic_names = [t.get('name', f'Topic {i+1}') for i, t in enumerate(topics)]
            confidences = [t.get('confidence', 0) for t in topics]
            
            fig = px.bar(
                x=topic_names,
                y=confidences,
                title="Topic Confidence Scores",
                labels={'x': 'Topics', 'y': 'Confidence Score'}
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed topic information
        st.subheader("📋 Topic Details")
        
        for i, topic in enumerate(topics, 1):
            with st.expander(f"🏷️ Topic {i}: {topic.get('name', 'Unknown Topic')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Topic Name:** {topic.get('name', 'Unknown')}")
                    st.write(f"**Confidence:** {topic.get('confidence', 0):.3f}")
                    
                    keywords = topic.get('keywords', [])
                    if keywords:
                        st.write(f"**Keywords:** {', '.join(keywords)}")
                
                with col2:
                    segments = topic.get('segments', [])
                    timestamps = topic.get('timestamps', [])
                    
                    st.write(f"**Segments:** {len(segments)}")
                    if timestamps:
                        st.write(f"**Time Range:** {min(timestamps):.1f}s - {max(timestamps):.1f}s")
                
                # Topic summary
                summary = topic.get('summary', '')
                if summary:
                    st.write(f"**Summary:** {summary}")
                
                # Show sample segments
                if segments:
                    st.write("**Sample Segments:**")
                    for j, segment in enumerate(segments[:3], 1):  # Show first 3 segments
                        st.write(f"{j}. {segment[:100]}{'...' if len(segment) > 100 else ''}")
        
        # Export topics
        if st.button("📤 Export Topics"):
            topics_data = []
            for topic in topics:
                topics_data.append({
                    'name': topic.get('name', ''),
                    'keywords': ', '.join(topic.get('keywords', [])),
                    'confidence': topic.get('confidence', 0),
                    'segments_count': len(topic.get('segments', [])),
                    'summary': topic.get('summary', '')
                })
            
            df = pd.DataFrame(topics_data)
            csv_content = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_content,
                file_name=f"topic_clusters_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    def _generate_minutes_text(self, meeting_minutes: Dict[str, Any]) -> str:
        """Generate formatted text for meeting minutes"""
        lines = []
        
        lines.append(f"MEETING MINUTES")
        lines.append("=" * 50)
        lines.append(f"Title: {meeting_minutes.get('title', 'Meeting')}")
        lines.append(f"Date: {meeting_minutes.get('date', 'Unknown')}")
        lines.append(f"Duration: {meeting_minutes.get('duration', 0):.1f} minutes")
        
        participants = meeting_minutes.get('participants', [])
        if participants:
            lines.append(f"Participants: {', '.join(participants)}")
        
        lines.append("")
        
        # Summary
        if meeting_minutes.get('summary'):
            lines.append("SUMMARY")
            lines.append("-" * 20)
            lines.append(meeting_minutes['summary'])
            lines.append("")
        
        # Agenda items
        agenda_items = meeting_minutes.get('agenda_items', [])
        if agenda_items:
            lines.append("AGENDA ITEMS")
            lines.append("-" * 20)
            for i, item in enumerate(agenda_items, 1):
                lines.append(f"{i}. {item}")
            lines.append("")
        
        # Key decisions
        decisions = meeting_minutes.get('key_decisions', [])
        if decisions:
            lines.append("KEY DECISIONS")
            lines.append("-" * 20)
            for i, decision in enumerate(decisions, 1):
                lines.append(f"{i}. {decision}")
            lines.append("")
        
        # Action items
        action_items = meeting_minutes.get('action_items', [])
        if action_items:
            lines.append("ACTION ITEMS")
            lines.append("-" * 20)
            for item in action_items:
                assignee_text = f" (Assigned to: {item.get('assignee')})" if item.get('assignee') else ""
                due_date_text = f" (Due: {item.get('due_date')})" if item.get('due_date') else ""
                priority_text = f" [Priority: {item.get('priority', 'medium').upper()}]"
                
                lines.append(f"• {item.get('text', '')}{assignee_text}{due_date_text}{priority_text}")
            lines.append("")
        
        # Next steps
        next_steps = meeting_minutes.get('next_steps', [])
        if next_steps:
            lines.append("NEXT STEPS")
            lines.append("-" * 20)
            for i, step in enumerate(next_steps, 1):
                lines.append(f"{i}. {step}")
            lines.append("")
        
        return '\n'.join(lines)


def main():
    """Main function for testing the AI insights UI"""
    st.set_page_config(
        page_title="AI Content Insights",
        page_icon="🧠",
        layout="wide"
    )
    
    # Initialize UI
    ui = AIInsightsUI()
    ui.render_main_interface()


if __name__ == "__main__":
    main()