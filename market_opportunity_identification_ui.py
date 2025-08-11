"""
Market Opportunity Identification System UI

Streamlit interface for the market opportunity identification system.
Provides comprehensive market intelligence dashboard and opportunity analysis tools.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

from market_opportunity_identification import (
    MarketOpportunityIdentificationSystem,
    create_sample_content_data
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketOpportunityUI:
    """Streamlit UI for Market Opportunity Identification System"""
    
    def __init__(self):
        self.system = MarketOpportunityIdentificationSystem()
        self.setup_page_config()
    
    def setup_page_config(self):
        """Configure Streamlit page settings"""
        st.set_page_config(
            page_title="Market Opportunity Intelligence",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS for better styling
        st.markdown("""
        <style>
        .metric-card {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #1f77b4;
            margin: 0.5rem 0;
        }
        .opportunity-card {
            background-color: #ffffff;
            padding: 1.5rem;
            border-radius: 0.5rem;
            border: 1px solid #e0e0e0;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .high-priority {
            border-left: 4px solid #ff4444;
        }
        .medium-priority {
            border-left: 4px solid #ffaa00;
        }
        .low-priority {
            border-left: 4px solid #00aa00;
        }
        .trend-positive {
            color: #00aa00;
            font-weight: bold;
        }
        .trend-negative {
            color: #ff4444;
            font-weight: bold;
        }
        .trend-neutral {
            color: #666666;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def render_main_interface(self):
        """Render the main UI interface"""
        st.title("🎯 Market Opportunity Intelligence System")
        st.markdown("Discover untapped content opportunities through advanced data analysis and market intelligence.")
        
        # Sidebar navigation
        with st.sidebar:
            st.header("Navigation")
            page = st.selectbox(
                "Select Page",
                ["Dashboard", "Opportunity Analysis", "Trend Analysis", "Content Analysis", "Settings"]
            )
        
        # Route to appropriate page
        if page == "Dashboard":
            self.render_dashboard()
        elif page == "Opportunity Analysis":
            self.render_opportunity_analysis()
        elif page == "Trend Analysis":
            self.render_trend_analysis()
        elif page == "Content Analysis":
            self.render_content_analysis()
        elif page == "Settings":
            self.render_settings()
    
    def render_dashboard(self):
        """Render the main dashboard"""
        st.header("📊 Market Intelligence Dashboard")
        
        # Get dashboard data
        with st.spinner("Loading market intelligence data..."):
            dashboard_data = self.system.get_market_intelligence_dashboard()
        
        if not dashboard_data:
            st.warning("No market intelligence data available. Please run an analysis first.")
            return
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        opp_summary = dashboard_data.get('opportunity_summary', {})
        trend_summary = dashboard_data.get('trend_summary', {})
        
        with col1:
            st.metric(
                "Total Opportunities",
                opp_summary.get('total_opportunities', 0),
                delta=None
            )
        
        with col2:
            st.metric(
                "High Priority",
                opp_summary.get('high_priority_count', 0),
                delta=None
            )
        
        with col3:
            st.metric(
                "Avg Opportunity Score",
                f"{opp_summary.get('average_opportunity_score', 0):.2f}",
                delta=None
            )
        
        with col4:
            st.metric(
                "Market Size",
                f"${opp_summary.get('total_market_size', 0):,.0f}",
                delta=None
            )
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            self.render_opportunity_distribution_chart(dashboard_data)
        
        with col2:
            self.render_trend_strength_chart(dashboard_data)
        
        # Top opportunities and trends
        col1, col2 = st.columns(2)
        
        with col1:
            self.render_top_opportunities_table(dashboard_data)
        
        with col2:
            self.render_top_trends_table(dashboard_data)
    
    def render_opportunity_analysis(self):
        """Render opportunity analysis page"""
        st.header("🎯 Opportunity Analysis")
        
        # Analysis controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            time_period = st.selectbox(
                "Analysis Period",
                [7, 14, 30, 60, 90],
                index=2,
                format_func=lambda x: f"{x} days"
            )
        
        with col2:
            use_sample_data = st.checkbox("Use Sample Data", value=True)
        
        with col3:
            if st.button("Run Analysis", type="primary"):
                self.run_opportunity_analysis(time_period, use_sample_data)
        
        # File upload for custom content data
        if not use_sample_data:
            st.subheader("Upload Content Data")
            uploaded_file = st.file_uploader(
                "Choose a JSON file with content data",
                type=['json'],
                help="Upload a JSON file containing content items for analysis"
            )
            
            if uploaded_file:
                try:
                    content_data = json.load(uploaded_file)
                    st.success(f"Loaded {len(content_data)} content items")
                    st.session_state['custom_content_data'] = content_data
                except Exception as e:
                    st.error(f"Error loading file: {str(e)}")
        
        # Display analysis results
        if 'analysis_results' in st.session_state:
            self.display_analysis_results(st.session_state['analysis_results'])
    
    def render_trend_analysis(self):
        """Render trend analysis page"""
        st.header("📈 Trend Analysis")
        
        # Get recent trends from database
        dashboard_data = self.system.get_market_intelligence_dashboard()
        trends = dashboard_data.get('top_trends', [])
        
        if not trends:
            st.info("No trend data available. Please run an analysis first.")
            return
        
        # Trend overview metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Trends", len(trends))
        
        with col2:
            high_impact = len([t for t in trends if t.get('market_impact') == 'High'])
            st.metric("High Impact Trends", high_impact)
        
        with col3:
            avg_growth = sum(t.get('growth_rate', 0) for t in trends) / len(trends) if trends else 0
            st.metric("Avg Growth Rate", f"{avg_growth:.1f}%")
        
        # Trend visualization
        self.render_trend_growth_chart(trends)
        
        # Detailed trend table
        st.subheader("Detailed Trend Analysis")
        
        if trends:
            df = pd.DataFrame(trends)
            
            # Format the dataframe for display
            display_df = df[['trend_name', 'trend_strength', 'growth_rate', 'market_impact']].copy()
            display_df.columns = ['Trend Name', 'Strength', 'Growth Rate (%)', 'Market Impact']
            display_df['Growth Rate (%)'] = display_df['Growth Rate (%)'].round(2)
            display_df['Strength'] = display_df['Strength'].round(2)
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
    
    def render_content_analysis(self):
        """Render content analysis page"""
        st.header("📝 Content Analysis")
        
        st.markdown("""
        This section provides insights into your content portfolio and identifies
        opportunities for content optimization and gap filling.
        """)
        
        # Content analysis controls
        col1, col2 = st.columns(2)
        
        with col1:
            analysis_type = st.selectbox(
                "Analysis Type",
                ["Content Gaps", "Sentiment Analysis", "Keyword Analysis", "Topic Distribution"]
            )
        
        with col2:
            if st.button("Analyze Content"):
                self.run_content_analysis(analysis_type)
        
        # Display content analysis results
        if 'content_analysis_results' in st.session_state:
            results = st.session_state['content_analysis_results']
            
            if analysis_type == "Content Gaps":
                self.display_content_gaps(results)
            elif analysis_type == "Sentiment Analysis":
                self.display_sentiment_analysis(results)
            elif analysis_type == "Keyword Analysis":
                self.display_keyword_analysis(results)
            elif analysis_type == "Topic Distribution":
                self.display_topic_distribution(results)
    
    def render_settings(self):
        """Render settings page"""
        st.header("⚙️ Settings")
        
        st.subheader("Analysis Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.number_input(
                "Minimum Opportunity Score",
                min_value=0.0,
                max_value=10.0,
                value=5.0,
                step=0.1,
                key="min_opportunity_score"
            )
            
            st.number_input(
                "Minimum Trend Strength",
                min_value=0.0,
                max_value=10.0,
                value=3.0,
                step=0.1,
                key="min_trend_strength"
            )
        
        with col2:
            st.selectbox(
                "Default Analysis Period",
                [7, 14, 30, 60, 90],
                index=2,
                format_func=lambda x: f"{x} days",
                key="default_analysis_period"
            )
            
            st.selectbox(
                "Competition Assessment Method",
                ["Content Volume", "Keyword Density", "Market Share"],
                key="competition_method"
            )
        
        st.subheader("Data Sources")
        
        st.multiselect(
            "Enable Data Sources",
            ["Content Analysis", "Trend Analysis", "External APIs", "User Feedback"],
            default=["Content Analysis", "Trend Analysis"],
            key="enabled_data_sources"
        )
        
        if st.button("Save Settings"):
            st.success("Settings saved successfully!")
    
    def run_opportunity_analysis(self, time_period: int, use_sample_data: bool):
        """Run opportunity analysis"""
        try:
            with st.spinner("Running opportunity analysis..."):
                # Get content data
                if use_sample_data:
                    content_data = create_sample_content_data()
                else:
                    content_data = st.session_state.get('custom_content_data', [])
                
                if not content_data:
                    st.error("No content data available for analysis")
                    return
                
                # Run analysis
                results = asyncio.run(
                    self.system.identify_opportunities(content_data, time_period)
                )
                
                if results['success']:
                    st.session_state['analysis_results'] = results
                    st.success(f"Analysis completed! {results['message']}")
                else:
                    st.error(f"Analysis failed: {results['message']}")
                    
        except Exception as e:
            st.error(f"Error running analysis: {str(e)}")
            logger.error(f"Error in opportunity analysis: {str(e)}")
    
    def display_analysis_results(self, results: Dict[str, Any]):
        """Display comprehensive analysis results"""
        st.subheader("📊 Analysis Results")
        
        # Summary metrics
        metadata = results.get('analysis_metadata', {})
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Content Items", metadata.get('content_items_analyzed', 0))
        with col2:
            st.metric("Opportunities", metadata.get('opportunities_found', 0))
        with col3:
            st.metric("Trends", metadata.get('trends_identified', 0))
        with col4:
            st.metric("Analysis Date", metadata.get('analysis_date', 'N/A')[:10])
        
        # Opportunities section
        opportunities = results.get('opportunities', [])
        if opportunities:
            st.subheader("🎯 Identified Opportunities")
            
            # Filter controls
            col1, col2, col3 = st.columns(3)
            
            with col1:
                priority_filter = st.selectbox(
                    "Filter by Priority",
                    ["All", "High", "Medium", "Low"]
                )
            
            with col2:
                category_filter = st.selectbox(
                    "Filter by Category",
                    ["All"] + list(set(opp['category'] for opp in opportunities))
                )
            
            with col3:
                min_score = st.slider(
                    "Minimum Score",
                    0.0, 10.0, 0.0, 0.1
                )
            
            # Apply filters
            filtered_opportunities = self.filter_opportunities(
                opportunities, priority_filter, category_filter, min_score
            )
            
            # Display opportunities
            for opp in filtered_opportunities[:10]:  # Show top 10
                self.render_opportunity_card(opp)
        
        # Summary insights
        summary = results.get('summary', {})
        if summary:
            st.subheader("💡 Key Insights")
            
            executive_summary = summary.get('executive_summary', {})
            key_insights = summary.get('key_insights', [])
            
            # Executive summary metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Total Market Size",
                    f"${executive_summary.get('estimated_total_market_size', 0):,.0f}"
                )
            
            with col2:
                st.metric(
                    "High Priority Opps",
                    executive_summary.get('high_priority_opportunities', 0)
                )
            
            with col3:
                st.metric(
                    "High Growth Trends",
                    executive_summary.get('high_growth_trends', 0)
                )
            
            # Key insights
            if key_insights:
                st.markdown("**Key Insights:**")
                for insight in key_insights:
                    st.markdown(f"• {insight}")
            
            # Market outlook
            market_outlook = summary.get('market_outlook', {})
            if market_outlook:
                st.subheader("🔮 Market Outlook")
                
                outlook = market_outlook.get('outlook', 'Neutral')
                confidence = market_outlook.get('confidence', 'Medium')
                
                outlook_color = {
                    'Very Positive': '🟢',
                    'Positive': '🟢',
                    'Neutral': '🟡',
                    'Negative': '🔴'
                }.get(outlook, '🟡')
                
                st.markdown(f"{outlook_color} **{outlook}** outlook with **{confidence}** confidence")
                st.markdown(market_outlook.get('summary', ''))
    
    def render_opportunity_card(self, opportunity: Dict[str, Any]):
        """Render an individual opportunity card"""
        priority = opportunity.get('priority_level', 'Medium')
        priority_class = f"{priority.lower()}-priority"
        
        st.markdown(f"""
        <div class="opportunity-card {priority_class}">
            <h4>{opportunity.get('title', 'Untitled Opportunity')}</h4>
            <p><strong>Category:</strong> {opportunity.get('category', 'N/A')}</p>
            <p><strong>Score:</strong> {opportunity.get('opportunity_score', 0):.2f}/10</p>
            <p><strong>Market Size:</strong> ${opportunity.get('market_size_estimate', 0):,.0f}</p>
            <p><strong>Competition:</strong> {opportunity.get('competition_level', 'Unknown')}</p>
            <p><strong>Description:</strong> {opportunity.get('description', 'No description available')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Expandable details
        with st.expander("View Details"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Keywords:**")
                keywords = opportunity.get('keywords', [])
                if keywords:
                    st.markdown(", ".join(keywords[:10]))
                else:
                    st.markdown("No keywords available")
                
                st.markdown("**Target Audience:**")
                audience = opportunity.get('target_audience', [])
                if audience:
                    for aud in audience:
                        st.markdown(f"• {aud}")
                else:
                    st.markdown("No target audience defined")
            
            with col2:
                st.markdown("**Content Gaps:**")
                gaps = opportunity.get('content_gaps', [])
                if gaps:
                    for gap in gaps:
                        st.markdown(f"• {gap}")
                else:
                    st.markdown("No content gaps identified")
                
                st.markdown("**Recommended Actions:**")
                actions = opportunity.get('recommended_actions', [])
                if actions:
                    for action in actions[:3]:  # Show top 3
                        st.markdown(f"• {action}")
                else:
                    st.markdown("No recommendations available")
    
    def filter_opportunities(self, opportunities: List[Dict[str, Any]], 
                           priority_filter: str, category_filter: str, 
                           min_score: float) -> List[Dict[str, Any]]:
        """Filter opportunities based on criteria"""
        filtered = opportunities
        
        if priority_filter != "All":
            filtered = [opp for opp in filtered if opp.get('priority_level') == priority_filter]
        
        if category_filter != "All":
            filtered = [opp for opp in filtered if opp.get('category') == category_filter]
        
        filtered = [opp for opp in filtered if opp.get('opportunity_score', 0) >= min_score]
        
        return sorted(filtered, key=lambda x: x.get('opportunity_score', 0), reverse=True)
    
    def render_opportunity_distribution_chart(self, dashboard_data: Dict[str, Any]):
        """Render opportunity distribution chart"""
        st.subheader("Opportunity Distribution by Category")
        
        category_dist = dashboard_data.get('opportunity_summary', {}).get('category_distribution', {})
        
        if category_dist:
            fig = px.pie(
                values=list(category_dist.values()),
                names=list(category_dist.keys()),
                title="Opportunities by Category"
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No category distribution data available")
    
    def render_trend_strength_chart(self, dashboard_data: Dict[str, Any]):
        """Render trend strength chart"""
        st.subheader("Trend Strength Analysis")
        
        trends = dashboard_data.get('top_trends', [])
        
        if trends:
            df = pd.DataFrame(trends)
            
            fig = px.bar(
                df.head(10),
                x='trend_strength',
                y='trend_name',
                orientation='h',
                title="Top 10 Trends by Strength",
                color='trend_strength',
                color_continuous_scale='viridis'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trend data available")
    
    def render_top_opportunities_table(self, dashboard_data: Dict[str, Any]):
        """Render top opportunities table"""
        st.subheader("Top Opportunities")
        
        opportunities = dashboard_data.get('top_opportunities', [])
        
        if opportunities:
            df = pd.DataFrame(opportunities)
            display_df = df[['category', 'opportunity_score', 'priority_level']].head(5)
            display_df.columns = ['Category', 'Score', 'Priority']
            display_df['Score'] = display_df['Score'].round(2)
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No opportunities data available")
    
    def render_top_trends_table(self, dashboard_data: Dict[str, Any]):
        """Render top trends table"""
        st.subheader("Top Trends")
        
        trends = dashboard_data.get('top_trends', [])
        
        if trends:
            df = pd.DataFrame(trends)
            display_df = df[['trend_name', 'trend_strength', 'growth_rate']].head(5)
            display_df.columns = ['Trend', 'Strength', 'Growth %']
            display_df['Strength'] = display_df['Strength'].round(2)
            display_df['Growth %'] = display_df['Growth %'].round(1)
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No trends data available")
    
    def render_trend_growth_chart(self, trends: List[Dict[str, Any]]):
        """Render trend growth rate chart"""
        if not trends:
            return
        
        df = pd.DataFrame(trends)
        
        fig = px.scatter(
            df,
            x='trend_strength',
            y='growth_rate',
            size='confidence_level',
            color='market_impact',
            hover_name='trend_name',
            title="Trend Strength vs Growth Rate",
            labels={
                'trend_strength': 'Trend Strength',
                'growth_rate': 'Growth Rate (%)',
                'confidence_level': 'Confidence'
            }
        )
        
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    def run_content_analysis(self, analysis_type: str):
        """Run content analysis"""
        try:
            with st.spinner(f"Running {analysis_type.lower()}..."):
                # Simulate content analysis results
                results = {
                    'analysis_type': analysis_type,
                    'timestamp': datetime.now().isoformat(),
                    'data': self.generate_mock_content_analysis(analysis_type)
                }
                
                st.session_state['content_analysis_results'] = results
                st.success(f"{analysis_type} completed successfully!")
                
        except Exception as e:
            st.error(f"Error running content analysis: {str(e)}")
    
    def generate_mock_content_analysis(self, analysis_type: str) -> Dict[str, Any]:
        """Generate mock content analysis data"""
        if analysis_type == "Content Gaps":
            return {
                'identified_gaps': [
                    {'topic': 'AI Ethics', 'gap_score': 8.5, 'opportunity_size': 'Large'},
                    {'topic': 'Sustainable Technology', 'gap_score': 7.2, 'opportunity_size': 'Medium'},
                    {'topic': 'Remote Work Tools', 'gap_score': 6.8, 'opportunity_size': 'Medium'},
                    {'topic': 'Cybersecurity Basics', 'gap_score': 9.1, 'opportunity_size': 'Large'},
                    {'topic': 'Digital Wellness', 'gap_score': 5.9, 'opportunity_size': 'Small'}
                ]
            }
        elif analysis_type == "Sentiment Analysis":
            return {
                'overall_sentiment': 0.65,
                'sentiment_distribution': {
                    'Positive': 45,
                    'Neutral': 35,
                    'Negative': 20
                },
                'sentiment_trends': [
                    {'date': '2024-01-01', 'sentiment': 0.6},
                    {'date': '2024-01-15', 'sentiment': 0.7},
                    {'date': '2024-02-01', 'sentiment': 0.65},
                    {'date': '2024-02-15', 'sentiment': 0.8}
                ]
            }
        elif analysis_type == "Keyword Analysis":
            return {
                'top_keywords': [
                    {'keyword': 'artificial intelligence', 'frequency': 156, 'trend': 'up'},
                    {'keyword': 'machine learning', 'frequency': 134, 'trend': 'up'},
                    {'keyword': 'digital transformation', 'frequency': 98, 'trend': 'stable'},
                    {'keyword': 'automation', 'frequency': 87, 'trend': 'up'},
                    {'keyword': 'data analytics', 'frequency': 76, 'trend': 'down'}
                ]
            }
        elif analysis_type == "Topic Distribution":
            return {
                'topics': [
                    {'topic': 'Technology', 'percentage': 35, 'content_count': 42},
                    {'topic': 'Business', 'percentage': 28, 'content_count': 34},
                    {'topic': 'Education', 'percentage': 18, 'content_count': 22},
                    {'topic': 'Health', 'percentage': 12, 'content_count': 14},
                    {'topic': 'Finance', 'percentage': 7, 'content_count': 8}
                ]
            }
        
        return {}
    
    def display_content_gaps(self, results: Dict[str, Any]):
        """Display content gaps analysis"""
        st.subheader("📊 Content Gaps Analysis")
        
        gaps = results.get('data', {}).get('identified_gaps', [])
        
        if gaps:
            df = pd.DataFrame(gaps)
            
            # Gap score chart
            fig = px.bar(
                df,
                x='topic',
                y='gap_score',
                color='opportunity_size',
                title="Content Gaps by Topic",
                labels={'gap_score': 'Gap Score', 'topic': 'Topic'}
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Detailed table
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No content gaps identified")
    
    def display_sentiment_analysis(self, results: Dict[str, Any]):
        """Display sentiment analysis results"""
        st.subheader("😊 Sentiment Analysis")
        
        data = results.get('data', {})
        overall_sentiment = data.get('overall_sentiment', 0)
        
        # Overall sentiment metric
        sentiment_label = "Positive" if overall_sentiment > 0.1 else "Negative" if overall_sentiment < -0.1 else "Neutral"
        st.metric("Overall Sentiment", f"{overall_sentiment:.2f} ({sentiment_label})")
        
        # Sentiment distribution
        distribution = data.get('sentiment_distribution', {})
        if distribution:
            fig = px.pie(
                values=list(distribution.values()),
                names=list(distribution.keys()),
                title="Sentiment Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def display_keyword_analysis(self, results: Dict[str, Any]):
        """Display keyword analysis results"""
        st.subheader("🔍 Keyword Analysis")
        
        keywords = results.get('data', {}).get('top_keywords', [])
        
        if keywords:
            df = pd.DataFrame(keywords)
            
            # Keyword frequency chart
            fig = px.bar(
                df,
                x='keyword',
                y='frequency',
                color='trend',
                title="Top Keywords by Frequency"
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Detailed table
            st.dataframe(df, use_container_width=True, hide_index=True)
    
    def display_topic_distribution(self, results: Dict[str, Any]):
        """Display topic distribution analysis"""
        st.subheader("📚 Topic Distribution")
        
        topics = results.get('data', {}).get('topics', [])
        
        if topics:
            df = pd.DataFrame(topics)
            
            # Topic distribution chart
            fig = px.pie(
                df,
                values='percentage',
                names='topic',
                title="Content Distribution by Topic"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Detailed metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Topics", len(topics))
            
            with col2:
                total_content = sum(t['content_count'] for t in topics)
                st.metric("Total Content Items", total_content)
            
            # Detailed table
            st.dataframe(df, use_container_width=True, hide_index=True)

def main():
    """Main function to run the Streamlit app"""
    try:
        ui = MarketOpportunityUI()
        ui.render_main_interface()
        
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        logger.error(f"Streamlit app error: {str(e)}")

if __name__ == "__main__":
    main()