"""
Content Intelligence UI
Streamlit interface for content analysis and insights
"""

import streamlit as st
import asyncio
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Optional
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Content Intelligence Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .insight-box {
        background: #f7f9fc;
        border-left: 4px solid #667eea;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 5px 5px 0;
    }
    .tag-pill {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        margin: 0.25rem;
        background: #e0e7ff;
        color: #4c51bf;
        border-radius: 20px;
        font-size: 0.875rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'content_history' not in st.session_state:
    st.session_state.content_history = []

# API configuration
API_BASE_URL = "http://localhost:8000/api/intelligence"

# Header
st.markdown('<h1 class="main-header">🧠 Content Intelligence Dashboard</h1>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    analysis_mode = st.selectbox(
        "Analysis Mode",
        ["Quick Analysis", "Deep Analysis", "Comparison", "Batch Processing"]
    )
    
    st.markdown("---")
    
    st.header("📊 Quick Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Analyzed Today", "47", "+5")
    with col2:
        st.metric("Avg Quality", "8.2", "+0.3")
    
    st.markdown("---")
    
    if st.button("🔄 Clear Cache"):
        st.session_state.analysis_results = None
        st.session_state.content_history = []
        st.success("Cache cleared!")

# Main content area
if analysis_mode == "Quick Analysis":
    st.header("📝 Content Analysis")
    
    # Input section
    col1, col2 = st.columns([3, 1])
    
    with col1:
        content_title = st.text_input("Content Title", placeholder="Enter a descriptive title")
        content_text = st.text_area(
            "Content to Analyze",
            height=200,
            placeholder="Paste your content here for analysis..."
        )
    
    with col2:
        content_type = st.selectbox(
            "Content Type",
            ["transcript", "document", "article", "social_media", "email"]
        )
        
        deep_analysis = st.checkbox("Enable Deep Analysis", value=True)
        
        analyze_button = st.button("🔍 Analyze Content", type="primary", use_container_width=True)
    
    # Analysis execution
    if analyze_button and content_text:
        with st.spinner("Analyzing content..."):
            try:
                # Mock API call for Python 3.12 compatibility
                # In production, this would call the actual API
                mock_response = {
                    "content_id": f"content_{datetime.now().timestamp()}",
                    "title": content_title or "Untitled",
                    "category": "technology",
                    "tags": ["AI", "machine learning", "innovation", "technology", "future"],
                    "keywords": [
                        {"keyword": "artificial intelligence", "score": 0.95},
                        {"keyword": "machine learning", "score": 0.87},
                        {"keyword": "deep learning", "score": 0.76},
                        {"keyword": "neural networks", "score": 0.72},
                        {"keyword": "automation", "score": 0.68}
                    ],
                    "sentiment": {
                        "positive": 0.72,
                        "negative": 0.08,
                        "neutral": 0.20
                    },
                    "quality_score": 0.85,
                    "readability_score": 0.78,
                    "engagement_prediction": 0.82,
                    "virality_score": 0.65,
                    "target_audience": ["tech professionals", "students", "researchers"],
                    "summary": "• Discusses latest AI advancements\n• Explores practical applications\n• Highlights future possibilities"
                }
                
                st.session_state.analysis_results = mock_response
                st.session_state.content_history.append({
                    "timestamp": datetime.now(),
                    "title": content_title or "Untitled",
                    "score": mock_response["quality_score"]
                })
                
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
    
    # Results display
    if st.session_state.analysis_results:
        result = st.session_state.analysis_results
        
        st.markdown("---")
        st.header("📊 Analysis Results")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            quality_color = "green" if result["quality_score"] > 0.7 else "orange"
            st.markdown(f"""
            <div class="metric-card">
                <h4>Quality Score</h4>
                <h2 style="color: {quality_color};">{result["quality_score"]*100:.1f}%</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h4>Readability</h4>
                <h2>{result["readability_score"]*100:.1f}%</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            engagement_color = "green" if result["engagement_prediction"] > 0.8 else "orange"
            st.markdown(f"""
            <div class="metric-card">
                <h4>Engagement</h4>
                <h2 style="color: {engagement_color};">{result["engagement_prediction"]*100:.1f}%</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            viral_color = "purple" if result["virality_score"] > 0.6 else "gray"
            st.markdown(f"""
            <div class="metric-card">
                <h4>Viral Potential</h4>
                <h2 style="color: {viral_color};">{result["virality_score"]*100:.1f}%</h2>
            </div>
            """, unsafe_allow_html=True)
        
        # Content insights
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🎯 Content Insights")
            
            # Category and tags
            st.markdown(f"""
            <div class="insight-box">
                <strong>Category:</strong> {result["category"].title()}<br>
                <strong>Tags:</strong> {' '.join([f'<span class="tag-pill">{tag}</span>' for tag in result["tags"][:5]])}
            </div>
            """, unsafe_allow_html=True)
            
            # Keywords
            st.subheader("🔑 Top Keywords")
            keywords_df = pd.DataFrame(result["keywords"])
            fig_keywords = px.bar(
                keywords_df, 
                x="score", 
                y="keyword",
                orientation='h',
                color="score",
                color_continuous_scale="viridis"
            )
            fig_keywords.update_layout(height=250, showlegend=False)
            st.plotly_chart(fig_keywords, use_container_width=True)
            
            # Target audience
            st.subheader("👥 Target Audience")
            audience_html = ' '.join([f'<span class="tag-pill">{aud}</span>' for aud in result["target_audience"]])
            st.markdown(audience_html, unsafe_allow_html=True)
        
        with col2:
            # Sentiment analysis
            st.subheader("😊 Sentiment Analysis")
            sentiment_data = pd.DataFrame([result["sentiment"]])
            fig_sentiment = go.Figure(data=[
                go.Bar(
                    x=['Positive', 'Negative', 'Neutral'],
                    y=[result["sentiment"]["positive"], 
                       result["sentiment"]["negative"], 
                       result["sentiment"]["neutral"]],
                    marker_color=['green', 'red', 'gray']
                )
            ])
            fig_sentiment.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig_sentiment, use_container_width=True)
            
            # Summary
            if result.get("summary"):
                st.subheader("📄 Summary")
                st.markdown(f"""
                <div class="insight-box">
                    {result["summary"]}
                </div>
                """, unsafe_allow_html=True)
        
        # Recommendations
        st.subheader("💡 Recommendations")
        
        recommendations = []
        if result["quality_score"] < 0.7:
            recommendations.append("📝 Consider improving content structure and clarity")
        if result["readability_score"] < 0.6:
            recommendations.append("📖 Simplify language for better readability")
        if result["engagement_prediction"] < 0.5:
            recommendations.append("🎯 Add more engaging elements (stories, examples)")
        if result["virality_score"] > 0.7:
            recommendations.append("🚀 High viral potential - optimize for social sharing")
        if result["sentiment"]["negative"] > 0.3:
            recommendations.append("😊 Consider balancing negative sentiment with positive points")
        
        if recommendations:
            for rec in recommendations:
                st.info(rec)
        else:
            st.success("✅ Content is well-optimized!")

elif analysis_mode == "Comparison":
    st.header("📊 Content Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Content A")
        content_a = st.text_area("First Content", height=200)
        
    with col2:
        st.subheader("Content B")
        content_b = st.text_area("Second Content", height=200)
    
    if st.button("🔍 Compare Contents", type="primary"):
        with st.spinner("Comparing contents..."):
            # Mock comparison results
            comparison_data = pd.DataFrame({
                'Metric': ['Quality', 'Readability', 'Engagement', 'Sentiment', 'Virality'],
                'Content A': [0.82, 0.75, 0.68, 0.72, 0.55],
                'Content B': [0.78, 0.82, 0.71, 0.65, 0.62]
            })
            
            fig = go.Figure()
            fig.add_trace(go.Bar(name='Content A', x=comparison_data['Metric'], y=comparison_data['Content A']))
            fig.add_trace(go.Bar(name='Content B', x=comparison_data['Metric'], y=comparison_data['Content B']))
            fig.update_layout(barmode='group', height=400)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Winner determination
            score_a = comparison_data['Content A'].mean()
            score_b = comparison_data['Content B'].mean()
            
            if score_a > score_b:
                st.success(f"🏆 Content A performs better overall ({score_a:.2f} vs {score_b:.2f})")
            else:
                st.success(f"🏆 Content B performs better overall ({score_b:.2f} vs {score_a:.2f})")

elif analysis_mode == "Batch Processing":
    st.header("📦 Batch Content Processing")
    
    uploaded_file = st.file_uploader(
        "Upload CSV file with content",
        type=['csv'],
        help="CSV should have 'title' and 'content' columns"
    )
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write(f"Loaded {len(df)} items for processing")
        
        if st.button("🚀 Process Batch", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results = []
            for idx, row in df.iterrows():
                status_text.text(f"Processing {idx+1}/{len(df)}: {row.get('title', 'Untitled')}")
                progress_bar.progress((idx + 1) / len(df))
                
                # Mock processing
                results.append({
                    'title': row.get('title', 'Untitled'),
                    'quality_score': np.random.uniform(0.6, 0.95),
                    'engagement': np.random.uniform(0.5, 0.9),
                    'sentiment': np.random.choice(['Positive', 'Neutral', 'Negative'])
                })
            
            results_df = pd.DataFrame(results)
            
            st.success(f"✅ Processed {len(results)} items successfully!")
            
            # Display results
            st.subheader("📊 Batch Results")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_quality = results_df['quality_score'].mean()
                st.metric("Average Quality", f"{avg_quality:.2%}")
            with col2:
                avg_engagement = results_df['engagement'].mean()
                st.metric("Average Engagement", f"{avg_engagement:.2%}")
            with col3:
                positive_pct = (results_df['sentiment'] == 'Positive').mean()
                st.metric("Positive Sentiment", f"{positive_pct:.1%}")
            
            # Results table
            st.dataframe(results_df, use_container_width=True)
            
            # Download results
            csv = results_df.to_csv(index=False)
            st.download_button(
                "📥 Download Results",
                csv,
                "batch_results.csv",
                "text/csv"
            )

# Content history sidebar
if st.session_state.content_history:
    with st.sidebar:
        st.markdown("---")
        st.header("📜 Recent Analyses")
        for item in st.session_state.content_history[-5:]:
            st.markdown(f"""
            **{item['title']}**  
            Score: {item['score']*100:.1f}%  
            {item['timestamp'].strftime('%H:%M')}
            """)

# Footer
st.markdown("---")
st.caption("Content Intelligence Dashboard v1.0 | Powered by Advanced NLP")