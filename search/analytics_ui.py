"""
Streamlit UI components for advanced analytics functionality
"""

import streamlit as st
import asyncio
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

from .advanced_analytics import AdvancedAnalytics, get_analytics_engine


class AnalyticsUI:
    """UI components for advanced analytics"""
    
    def __init__(self):
        self.analytics = get_analytics_engine()
        
    def render_analytics_dashboard(self):
        """Render the main analytics dashboard"""
        st.title("📊 Advanced Analytics Dashboard")
        
        # Analytics navigation tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "🔍 Trend Analysis", 
            "🏷️ Topic Modeling", 
            "⚖️ Comparative Analysis",
            "📈 Search Analytics"
        ])
        
        with tab1:
            self._render_trend_analysis()
            
        with tab2:
            self._render_topic_modeling()
            
        with tab3:
            self._render_comparative_analysis()
            
        with tab4:
            self._render_search_analytics()
    
    def _render_trend_analysis(self):
        """Render trend analysis interface"""
        st.header("📈 Trend Analysis")
        st.write("Analyze trends in your transcripts over time")
        
        # Configuration options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            time_period = st.selectbox(
                "Time Period",
                ["7d", "30d", "90d", "1y"],
                index=1,
                help="Select the time period for trend analysis"
            )
            
        with col2:
            analysis_type = st.selectbox(
                "Analysis Type",
                ["keywords", "topics", "entities", "sentiment"],
                help="Choose what to analyze for trends"
            )
            
        with col3:
            if st.button("🔍 Analyze Trends", type="primary"):
                st.session_state['run_trend_analysis'] = True
        
        # Advanced filters
        with st.expander("🔧 Advanced Filters"):
            filter_col1, filter_col2 = st.columns(2)
            
            with filter_col1:
                language_filter = st.selectbox(
                    "Language",
                    ["All", "en", "es", "fr", "de", "it"],
                    help="Filter by transcript language"
                )
                
                speaker_filter = st.text_input(
                    "Speaker Filter",
                    placeholder="Enter speaker names (comma-separated)",
                    help="Filter by specific speakers"
                )
                
            with filter_col2:
                tag_filter = st.text_input(
                    "Tag Filter",
                    placeholder="Enter tags (comma-separated)",
                    help="Filter by transcript tags"
                )
                
                min_confidence = st.slider(
                    "Minimum Confidence",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.0,
                    step=0.1,
                    help="Filter by minimum transcription confidence"
                )
        
        # Build filters
        filters = {}
        if language_filter != "All":
            filters['language'] = language_filter
        if speaker_filter:
            filters['speakers'] = [s.strip() for s in speaker_filter.split(',')]
        if tag_filter:
            filters['tags'] = [t.strip() for t in tag_filter.split(',')]
        if min_confidence > 0:
            filters['min_confidence'] = min_confidence
        
        # Run analysis
        if st.session_state.get('run_trend_analysis', False):
            with st.spinner(f"Analyzing {analysis_type} trends over {time_period}..."):
                try:
                    result = asyncio.run(
                        self.analytics.analyze_trends(
                            time_period=time_period,
                            analysis_type=analysis_type,
                            filters=filters
                        )
                    )
                    
                    if result.trends:
                        self._display_trend_results(result)
                    else:
                        st.warning("No trend data found for the selected criteria")
                        
                except Exception as e:
                    st.error(f"Trend analysis failed: {str(e)}")
                    
            st.session_state['run_trend_analysis'] = False
    
    def _display_trend_results(self, result):
        """Display trend analysis results"""
        st.subheader(f"📊 {result.analysis_type.title()} Trends - {result.time_period}")
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Transcripts", result.total_transcripts)
            
        with col2:
            st.metric("Time Periods", len(result.trends))
            
        with col3:
            if result.trends:
                avg_items = sum(len(trend.get('keywords', trend.get('topics', []))) 
                              for trend in result.trends) / len(result.trends)
                st.metric("Avg Items/Period", f"{avg_items:.1f}")
            
        with col4:
            st.metric("Analysis Type", result.analysis_type.title())
        
        # Visualizations based on analysis type
        if result.analysis_type == "keywords":
            self._plot_keyword_trends(result.trends)
        elif result.analysis_type == "topics":
            self._plot_topic_trends(result.trends)
        elif result.analysis_type == "entities":
            self._plot_entity_trends(result.trends)
        elif result.analysis_type == "sentiment":
            self._plot_sentiment_trends(result.trends)
        
        # Detailed data table
        with st.expander("📋 Detailed Trend Data"):
            for i, trend in enumerate(result.trends):
                st.write(f"**{trend['time_bucket']}** ({trend['transcript_count']} transcripts)")
                
                if result.analysis_type == "keywords":
                    keywords_df = pd.DataFrame(trend['keywords'])
                    if not keywords_df.empty:
                        st.dataframe(keywords_df, use_container_width=True)
                elif result.analysis_type == "topics":
                    st.json(trend['topics'])
                elif result.analysis_type == "entities":
                    entities_df = pd.DataFrame(trend['top_entities'])
                    if not entities_df.empty:
                        st.dataframe(entities_df, use_container_width=True)
                elif result.analysis_type == "sentiment":
                    st.json(trend['sentiment_distribution'])
                
                if i < len(result.trends) - 1:
                    st.divider()
    
    def _plot_keyword_trends(self, trends: List[Dict[str, Any]]):
        """Plot keyword trends over time"""
        try:
            # Prepare data for plotting
            time_buckets = [trend['time_bucket'] for trend in trends]
            
            # Get top keywords across all time periods
            all_keywords = {}
            for trend in trends:
                for kw_data in trend['keywords'][:5]:  # Top 5 keywords per period
                    keyword = kw_data['keyword']
                    if keyword not in all_keywords:
                        all_keywords[keyword] = []
                    all_keywords[keyword].append({
                        'time_bucket': trend['time_bucket'],
                        'score': kw_data['score'],
                        'frequency': kw_data['frequency']
                    })
            
            # Create line plot for keyword scores
            fig = go.Figure()
            
            for keyword, data_points in list(all_keywords.items())[:10]:  # Top 10 keywords
                scores = []
                time_labels = []
                
                for bucket in time_buckets:
                    bucket_data = next((d for d in data_points if d['time_bucket'] == bucket), None)
                    scores.append(bucket_data['score'] if bucket_data else 0)
                    time_labels.append(bucket)
                
                fig.add_trace(go.Scatter(
                    x=time_labels,
                    y=scores,
                    mode='lines+markers',
                    name=keyword,
                    line=dict(width=2),
                    marker=dict(size=6)
                ))
            
            fig.update_layout(
                title="Keyword Trends Over Time",
                xaxis_title="Time Period",
                yaxis_title="Keyword Score",
                hovermode='x unified',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Keyword growth rate chart
            growth_data = []
            for trend in trends[1:]:  # Skip first period (no growth rate)
                for kw_data in trend['keywords']:
                    if 'growth_rate' in kw_data:
                        growth_data.append({
                            'keyword': kw_data['keyword'],
                            'growth_rate': kw_data['growth_rate'],
                            'time_bucket': trend['time_bucket']
                        })
            
            if growth_data:
                growth_df = pd.DataFrame(growth_data)
                
                # Top growing keywords
                top_growth = growth_df.nlargest(10, 'growth_rate')
                
                fig_growth = px.bar(
                    top_growth,
                    x='keyword',
                    y='growth_rate',
                    title="Top Growing Keywords",
                    labels={'growth_rate': 'Growth Rate (%)', 'keyword': 'Keyword'}
                )
                fig_growth.update_xaxis(tickangle=45)
                
                st.plotly_chart(fig_growth, use_container_width=True)
                
        except Exception as e:
            st.error(f"Failed to plot keyword trends: {str(e)}")
    
    def _plot_topic_trends(self, trends: List[Dict[str, Any]]):
        """Plot topic trends over time"""
        try:
            # Topic coherence over time
            time_buckets = [trend['time_bucket'] for trend in trends]
            coherence_scores = [trend['coherence_score'] for trend in trends]
            
            fig_coherence = go.Figure()
            fig_coherence.add_trace(go.Scatter(
                x=time_buckets,
                y=coherence_scores,
                mode='lines+markers',
                name='Topic Coherence',
                line=dict(color='blue', width=3),
                marker=dict(size=8)
            ))
            
            fig_coherence.update_layout(
                title="Topic Coherence Over Time",
                xaxis_title="Time Period",
                yaxis_title="Coherence Score",
                height=400
            )
            
            st.plotly_chart(fig_coherence, use_container_width=True)
            
            # Topic distribution heatmap
            if trends:
                topic_data = []
                for trend in trends:
                    for topic_id, weight in trend['topic_distribution'].items():
                        topic_data.append({
                            'time_bucket': trend['time_bucket'],
                            'topic': topic_id,
                            'weight': weight
                        })
                
                if topic_data:
                    topic_df = pd.DataFrame(topic_data)
                    pivot_df = topic_df.pivot(index='topic', columns='time_bucket', values='weight')
                    
                    fig_heatmap = px.imshow(
                        pivot_df,
                        title="Topic Distribution Heatmap",
                        labels=dict(x="Time Period", y="Topic", color="Weight"),
                        aspect="auto"
                    )
                    
                    st.plotly_chart(fig_heatmap, use_container_width=True)
                    
        except Exception as e:
            st.error(f"Failed to plot topic trends: {str(e)}")
    
    def _plot_entity_trends(self, trends: List[Dict[str, Any]]):
        """Plot entity trends over time"""
        try:
            # Entity type distribution over time
            time_buckets = [trend['time_bucket'] for trend in trends]
            
            # Collect entity type data
            entity_type_data = []
            for trend in trends:
                for entity_type, count in trend['entity_types'].items():
                    entity_type_data.append({
                        'time_bucket': trend['time_bucket'],
                        'entity_type': entity_type,
                        'count': count
                    })
            
            if entity_type_data:
                entity_df = pd.DataFrame(entity_type_data)
                
                fig_entities = px.bar(
                    entity_df,
                    x='time_bucket',
                    y='count',
                    color='entity_type',
                    title="Entity Types Over Time",
                    labels={'count': 'Entity Count', 'time_bucket': 'Time Period'}
                )
                
                st.plotly_chart(fig_entities, use_container_width=True)
            
            # Top entities timeline
            top_entities_data = []
            for trend in trends:
                for entity_data in trend['top_entities'][:5]:  # Top 5 entities
                    top_entities_data.append({
                        'time_bucket': trend['time_bucket'],
                        'entity': entity_data['entity'],
                        'count': entity_data['count']
                    })
            
            if top_entities_data:
                entities_df = pd.DataFrame(top_entities_data)
                
                # Get top entities overall
                top_entities = entities_df.groupby('entity')['count'].sum().nlargest(10).index
                filtered_df = entities_df[entities_df['entity'].isin(top_entities)]
                
                fig_top = px.line(
                    filtered_df,
                    x='time_bucket',
                    y='count',
                    color='entity',
                    title="Top Entities Timeline",
                    labels={'count': 'Mention Count', 'time_bucket': 'Time Period'}
                )
                
                st.plotly_chart(fig_top, use_container_width=True)
                
        except Exception as e:
            st.error(f"Failed to plot entity trends: {str(e)}")
    
    def _plot_sentiment_trends(self, trends: List[Dict[str, Any]]):
        """Plot sentiment trends over time"""
        try:
            time_buckets = [trend['time_bucket'] for trend in trends]
            avg_sentiments = [trend['average_sentiment'] for trend in trends]
            
            # Average sentiment over time
            fig_sentiment = go.Figure()
            fig_sentiment.add_trace(go.Scatter(
                x=time_buckets,
                y=avg_sentiments,
                mode='lines+markers',
                name='Average Sentiment',
                line=dict(color='green', width=3),
                marker=dict(size=8)
            ))
            
            # Add neutral line
            fig_sentiment.add_hline(y=0, line_dash="dash", line_color="gray", 
                                  annotation_text="Neutral")
            
            fig_sentiment.update_layout(
                title="Sentiment Trends Over Time",
                xaxis_title="Time Period",
                yaxis_title="Average Sentiment Score",
                yaxis=dict(range=[-1, 1]),
                height=400
            )
            
            st.plotly_chart(fig_sentiment, use_container_width=True)
            
            # Sentiment distribution stacked bar chart
            sentiment_data = []
            for trend in trends:
                dist = trend['sentiment_distribution']
                sentiment_data.append({
                    'time_bucket': trend['time_bucket'],
                    'positive': dist['positive'],
                    'neutral': dist['neutral'],
                    'negative': dist['negative']
                })
            
            if sentiment_data:
                sentiment_df = pd.DataFrame(sentiment_data)
                
                fig_dist = go.Figure()
                
                fig_dist.add_trace(go.Bar(
                    x=sentiment_df['time_bucket'],
                    y=sentiment_df['positive'],
                    name='Positive',
                    marker_color='green'
                ))
                
                fig_dist.add_trace(go.Bar(
                    x=sentiment_df['time_bucket'],
                    y=sentiment_df['neutral'],
                    name='Neutral',
                    marker_color='gray'
                ))
                
                fig_dist.add_trace(go.Bar(
                    x=sentiment_df['time_bucket'],
                    y=sentiment_df['negative'],
                    name='Negative',
                    marker_color='red'
                ))
                
                fig_dist.update_layout(
                    title="Sentiment Distribution Over Time",
                    xaxis_title="Time Period",
                    yaxis_title="Number of Transcripts",
                    barmode='stack',
                    height=400
                )
                
                st.plotly_chart(fig_dist, use_container_width=True)
                
        except Exception as e:
            st.error(f"Failed to plot sentiment trends: {str(e)}")
    
    def _render_topic_modeling(self):
        """Render topic modeling interface"""
        st.header("🏷️ Topic Modeling")
        st.write("Extract and analyze topics from your transcripts")
        
        # Configuration options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            num_topics = st.slider(
                "Number of Topics",
                min_value=2,
                max_value=20,
                value=5,
                help="Number of topics to extract"
            )
            
        with col2:
            method = st.selectbox(
                "Extraction Method",
                ["keyword_clustering", "semantic_clustering"],
                help="Method for topic extraction"
            )
            
        with col3:
            if st.button("🔍 Extract Topics", type="primary"):
                st.session_state['run_topic_modeling'] = True
        
        # Transcript selection
        with st.expander("📄 Transcript Selection"):
            selection_type = st.radio(
                "Select transcripts",
                ["All transcripts", "Specific transcripts", "By date range"],
                horizontal=True
            )
            
            transcript_ids = None
            
            if selection_type == "Specific transcripts":
                transcript_input = st.text_area(
                    "Transcript IDs (one per line)",
                    placeholder="transcript_1\ntranscript_2\ntranscript_3",
                    help="Enter transcript IDs to analyze"
                )
                if transcript_input:
                    transcript_ids = [tid.strip() for tid in transcript_input.split('\n') if tid.strip()]
            
            elif selection_type == "By date range":
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Start Date")
                with col2:
                    end_date = st.date_input("End Date")
                
                # Note: In a full implementation, you'd filter by date range
                st.info("Date range filtering will be applied to transcript selection")
        
        # Run topic modeling
        if st.session_state.get('run_topic_modeling', False):
            with st.spinner(f"Extracting {num_topics} topics using {method}..."):
                try:
                    result = asyncio.run(
                        self.analytics.extract_topics(
                            transcript_ids=transcript_ids,
                            num_topics=num_topics,
                            method=method
                        )
                    )
                    
                    if result.topics:
                        self._display_topic_results(result)
                    else:
                        st.warning("No topics found. Try adjusting the parameters or check your transcript data.")
                        
                except Exception as e:
                    st.error(f"Topic modeling failed: {str(e)}")
                    
            st.session_state['run_topic_modeling'] = False
    
    def _display_topic_results(self, result):
        """Display topic modeling results"""
        st.subheader(f"📊 Extracted Topics ({result.num_topics} topics)")
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Number of Topics", result.num_topics)
            
        with col2:
            st.metric("Coherence Score", f"{result.coherence_score:.3f}")
            
        with col3:
            st.metric("Method", result.metadata.get('method', 'Unknown'))
        
        # Topic visualization
        if result.topics:
            # Topic weights bar chart
            topic_names = [f"Topic {i+1}" for i in range(len(result.topics))]
            topic_weights = [topic.get('weight', 0) for topic in result.topics]
            
            fig_weights = px.bar(
                x=topic_names,
                y=topic_weights,
                title="Topic Weights",
                labels={'x': 'Topic', 'y': 'Weight'}
            )
            
            st.plotly_chart(fig_weights, use_container_width=True)
            
            # Topic distribution pie chart
            if result.topic_distribution:
                fig_pie = px.pie(
                    values=list(result.topic_distribution.values()),
                    names=list(result.topic_distribution.keys()),
                    title="Topic Distribution"
                )
                
                st.plotly_chart(fig_pie, use_container_width=True)
        
        # Detailed topic information
        st.subheader("📋 Topic Details")
        
        for i, topic in enumerate(result.topics):
            with st.expander(f"Topic {i+1}: {topic.get('description', 'No description')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Keywords:**")
                    keywords = topic.get('keywords', [])
                    if keywords:
                        for keyword in keywords:
                            st.write(f"• {keyword}")
                    else:
                        st.write("No keywords available")
                
                with col2:
                    st.write("**Topic Metrics:**")
                    st.write(f"Weight: {topic.get('weight', 0):.3f}")
                    st.write(f"Topic ID: {topic.get('topic_id', 'Unknown')}")
                    
                    if 'keywords' in topic:
                        st.write(f"Keyword Count: {len(topic['keywords'])}")
        
        # Export options
        st.subheader("💾 Export Topics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Export as JSON"):
                json_data = json.dumps(result.__dict__, indent=2, default=str)
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name=f"topics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("📊 Export as CSV"):
                # Create CSV data
                csv_data = []
                for i, topic in enumerate(result.topics):
                    csv_data.append({
                        'topic_id': topic.get('topic_id', f'topic_{i+1}'),
                        'description': topic.get('description', ''),
                        'weight': topic.get('weight', 0),
                        'keywords': ', '.join(topic.get('keywords', []))
                    })
                
                df = pd.DataFrame(csv_data)
                csv_string = df.to_csv(index=False)
                
                st.download_button(
                    label="Download CSV",
                    data=csv_string,
                    file_name=f"topics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    def _render_comparative_analysis(self):
        """Render comparative analysis interface"""
        st.header("⚖️ Comparative Analysis")
        st.write("Compare different audio sources or transcript collections")
        
        # Source selection
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📄 Source A")
            source_a_type = st.radio(
                "Source A Type",
                ["Single Transcript", "Collection/Tag"],
                key="source_a_type"
            )
            
            if source_a_type == "Single Transcript":
                source_a = st.text_input(
                    "Transcript ID A",
                    placeholder="Enter transcript ID",
                    key="source_a_id"
                )
            else:
                source_a = st.text_input(
                    "Collection/Tag A",
                    placeholder="Enter collection name or tag",
                    key="source_a_collection"
                )
        
        with col2:
            st.subheader("📄 Source B")
            source_b_type = st.radio(
                "Source B Type",
                ["Single Transcript", "Collection/Tag"],
                key="source_b_type"
            )
            
            if source_b_type == "Single Transcript":
                source_b = st.text_input(
                    "Transcript ID B",
                    placeholder="Enter transcript ID",
                    key="source_b_id"
                )
            else:
                source_b = st.text_input(
                    "Collection/Tag B",
                    placeholder="Enter collection name or tag",
                    key="source_b_collection"
                )
        
        # Comparison options
        st.subheader("🔧 Comparison Options")
        
        comparison_type = st.selectbox(
            "Comparison Type",
            ["comprehensive", "keywords", "topics", "sentiment"],
            help="Type of comparison to perform"
        )
        
        # Run comparison
        if st.button("⚖️ Compare Sources", type="primary"):
            if source_a and source_b:
                with st.spinner(f"Comparing {source_a} and {source_b}..."):
                    try:
                        result = asyncio.run(
                            self.analytics.compare_sources(
                                source_a=source_a,
                                source_b=source_b,
                                comparison_type=comparison_type
                            )
                        )
                        
                        self._display_comparative_results(result)
                        
                    except Exception as e:
                        st.error(f"Comparative analysis failed: {str(e)}")
            else:
                st.warning("Please specify both sources for comparison")
    
    def _display_comparative_results(self, result):
        """Display comparative analysis results"""
        st.subheader(f"📊 Comparison Results: {result.source_a} vs {result.source_b}")
        
        # Similarity metrics
        if result.similarities:
            st.subheader("🔗 Similarities")
            
            # Similarity metrics in columns
            similarity_cols = st.columns(len(result.similarities))
            
            for i, (metric, value) in enumerate(result.similarities.items()):
                with similarity_cols[i]:
                    st.metric(
                        metric.replace('_', ' ').title(),
                        f"{value:.3f}",
                        help=f"Similarity score for {metric}"
                    )
            
            # Similarity radar chart
            if len(result.similarities) > 2:
                fig_radar = go.Figure()
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=list(result.similarities.values()),
                    theta=[metric.replace('_', ' ').title() for metric in result.similarities.keys()],
                    fill='toself',
                    name='Similarity Scores'
                ))
                
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 1]
                        )),
                    title="Similarity Profile",
                    height=400
                )
                
                st.plotly_chart(fig_radar, use_container_width=True)
        
        # Common themes
        if result.common_themes:
            st.subheader("🤝 Common Themes")
            
            for theme in result.common_themes:
                st.write(f"• {theme}")
        
        # Unique themes
        if result.unique_themes:
            st.subheader("🎯 Unique Themes")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Unique to {result.source_a}:**")
                for theme in result.unique_themes.get('source_a_unique', []):
                    st.write(f"• {theme}")
            
            with col2:
                st.write(f"**Unique to {result.source_b}:**")
                for theme in result.unique_themes.get('source_b_unique', []):
                    st.write(f"• {theme}")
        
        # Differences
        if result.differences:
            st.subheader("📊 Differences")
            
            with st.expander("📋 Detailed Differences"):
                st.json(result.differences)
        
        # Export comparison results
        st.subheader("💾 Export Results")
        
        if st.button("📄 Export Comparison"):
            json_data = json.dumps(result.__dict__, indent=2, default=str)
            st.download_button(
                label="Download Comparison Results",
                data=json_data,
                file_name=f"comparison_{result.source_a}_{result.source_b}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    def _render_search_analytics(self):
        """Render search analytics interface"""
        st.header("📈 Search Analytics")
        st.write("Analyze search patterns and performance")
        
        # This would integrate with the search manager to show:
        # - Most popular search terms
        # - Search success rates
        # - Query performance metrics
        # - User search behavior patterns
        
        st.info("🚧 Search analytics coming soon! This will show:")
        st.write("""
        - **Popular Search Terms**: Most frequently searched keywords
        - **Search Success Rates**: Percentage of searches returning results
        - **Query Performance**: Average search response times
        - **Search Patterns**: Trending search behaviors over time
        - **Result Click-through Rates**: Which results users find most relevant
        """)
        
        # Placeholder visualization
        sample_data = {
            'search_term': ['meeting', 'project', 'discussion', 'presentation', 'interview'],
            'frequency': [45, 32, 28, 21, 18],
            'success_rate': [0.89, 0.76, 0.82, 0.91, 0.73]
        }
        
        df = pd.DataFrame(sample_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_freq = px.bar(
                df,
                x='search_term',
                y='frequency',
                title="Sample: Popular Search Terms",
                labels={'frequency': 'Search Frequency', 'search_term': 'Search Term'}
            )
            st.plotly_chart(fig_freq, use_container_width=True)
        
        with col2:
            fig_success = px.bar(
                df,
                x='search_term',
                y='success_rate',
                title="Sample: Search Success Rates",
                labels={'success_rate': 'Success Rate', 'search_term': 'Search Term'}
            )
            st.plotly_chart(fig_success, use_container_width=True)


def render_analytics_page():
    """Main entry point for analytics page"""
    st.set_page_config(
        page_title="Advanced Analytics",
        page_icon="📊",
        layout="wide"
    )
    
    # Initialize analytics UI
    analytics_ui = AnalyticsUI()
    
    # Render the interface
    analytics_ui.render_analytics_dashboard()


if __name__ == "__main__":
    render_analytics_page()