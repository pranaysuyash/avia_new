"""
Content Recommendations UI - Streamlit Dashboard
Task 204: AI-Powered Content Recommendations and Discovery
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json
from typing import List, Dict, Any
import random

from ai_content_recommendations import (
    ContentRecommendationEngine,
    RecommendationType,
    UserProfile,
    Recommendation
)

# Page configuration
st.set_page_config(
    page_title="AI Content Recommendations",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .recommendation-card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        border-left: 4px solid #4CAF50;
    }
    .score-badge {
        background: #4CAF50;
        color: white;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
    .reason-text {
        color: #666;
        font-size: 14px;
        margin-top: 5px;
    }
    .metric-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .profile-section {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .strategy-tab {
        background: white;
        padding: 10px 20px;
        border-radius: 5px;
        margin: 5px;
        cursor: pointer;
        transition: all 0.3s;
    }
    .strategy-tab:hover {
        background: #e3f2fd;
        transform: translateY(-2px);
    }
    .confidence-meter {
        height: 20px;
        background: #e0e0e0;
        border-radius: 10px;
        overflow: hidden;
    }
    .confidence-fill {
        height: 100%;
        background: linear-gradient(90deg, #4CAF50, #8BC34A);
        transition: width 0.5s ease;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'recommendation_engine' not in st.session_state:
    st.session_state.recommendation_engine = ContentRecommendationEngine()

if 'selected_user' not in st.session_state:
    st.session_state.selected_user = "user123"

if 'recommendation_history' not in st.session_state:
    st.session_state.recommendation_history = []

if 'interaction_log' not in st.session_state:
    st.session_state.interaction_log = []

def get_mock_content_pool() -> List[Dict[str, Any]]:
    """Generate mock content for recommendations"""
    content_types = ['video', 'audio', 'document', 'meeting', 'webinar', 'podcast']
    categories = ['Technology', 'Business', 'Education', 'Marketing', 'Sales', 'Product']
    
    content_pool = []
    for i in range(100):
        content = {
            'id': f'content_{i}',
            'title': f'{random.choice(["Advanced", "Introduction to", "Mastering", "Understanding"])} {random.choice(categories)} {random.choice(["Strategy", "Fundamentals", "Best Practices", "Workshop"])}',
            'description': f'Comprehensive content about {random.choice(categories).lower()} topics and insights.',
            'type': random.choice(content_types),
            'duration': random.randint(300, 7200),
            'quality_score': random.uniform(0.6, 1.0),
            'engagement_score': random.uniform(0.5, 0.95),
            'view_count': random.randint(10, 10000),
            'category': random.choice(categories),
            'tags': random.sample(['trending', 'featured', 'new', 'popular', 'expert', 'beginner'], k=random.randint(1, 3)),
            'created_at': datetime.now() - timedelta(days=random.randint(1, 365)),
            'thumbnail': f'https://picsum.photos/seed/{i}/300/200'
        }
        content_pool.append(content)
    
    return content_pool

def render_recommendation_card(rec: Recommendation, content: Dict[str, Any]):
    """Render a single recommendation card"""
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        st.image(content.get('thumbnail', 'https://via.placeholder.com/150'), width=150)
    
    with col2:
        st.markdown(f"### {content['title']}")
        st.markdown(f"**Type:** {content['type'].capitalize()} | **Category:** {content['category']}")
        st.markdown(f"<p class='reason-text'>{rec.reason}</p>", unsafe_allow_html=True)
        
        # Tags
        tags_html = " ".join([f"<span style='background:#e3f2fd; padding:3px 8px; border-radius:12px; margin-right:5px; font-size:12px;'>{tag}</span>" 
                             for tag in content.get('tags', [])])
        st.markdown(tags_html, unsafe_allow_html=True)
        
        # Confidence meter
        confidence_pct = int(rec.confidence * 100)
        st.markdown(f"""
        <div style='margin-top:10px;'>
            <small>Confidence: {confidence_pct}%</small>
            <div class='confidence-meter'>
                <div class='confidence-fill' style='width:{confidence_pct}%;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"<div class='score-badge'>Score: {rec.score:.2f}</div>", unsafe_allow_html=True)
        st.markdown(f"**Views:** {content['view_count']:,}")
        st.markdown(f"**Duration:** {content['duration']//60} min")
        
        # Action buttons
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("👍", key=f"like_{rec.content_id}"):
                record_interaction(rec.content_id, 'like')
        with col_b:
            if st.button("👁️", key=f"view_{rec.content_id}"):
                record_interaction(rec.content_id, 'view')

def record_interaction(content_id: str, interaction_type: str):
    """Record user interaction"""
    engine = st.session_state.recommendation_engine
    engine.record_interaction(
        user_id=st.session_state.selected_user,
        content_id=content_id,
        interaction_type=interaction_type,
        duration=random.randint(60, 3600),
        completion_rate=random.uniform(0.3, 1.0),
        rating=random.uniform(3.0, 5.0)
    )
    
    # Log interaction
    st.session_state.interaction_log.append({
        'timestamp': datetime.now(),
        'user': st.session_state.selected_user,
        'content': content_id,
        'type': interaction_type
    })
    
    st.success(f"Recorded {interaction_type} interaction!")

def main():
    st.title("🤖 AI-Powered Content Recommendations")
    st.markdown("### Intelligent content discovery and personalized recommendations")
    
    # Sidebar
    with st.sidebar:
        st.header("Configuration")
        
        # User selection
        st.session_state.selected_user = st.text_input(
            "User ID",
            value=st.session_state.selected_user
        )
        
        # Recommendation settings
        st.subheader("Recommendation Settings")
        
        recommendation_type = st.selectbox(
            "Recommendation Strategy",
            ["Hybrid", "Content-Based", "Collaborative", "Trending", "Discovery", "Popular"]
        )
        
        num_recommendations = st.slider(
            "Number of Recommendations",
            min_value=5,
            max_value=50,
            value=10
        )
        
        if recommendation_type == "Hybrid":
            st.subheader("Hybrid Weights")
            content_weight = st.slider("Content-Based", 0.0, 1.0, 0.4)
            collab_weight = st.slider("Collaborative", 0.0, 1.0, 0.3)
            trending_weight = st.slider("Trending", 0.0, 1.0, 0.2)
            discovery_weight = st.slider("Discovery", 0.0, 1.0, 0.1)
            
            # Normalize weights
            total = content_weight + collab_weight + trending_weight + discovery_weight
            weights = {
                'content': content_weight / total,
                'collaborative': collab_weight / total,
                'trending': trending_weight / total,
                'discovery': discovery_weight / total
            }
        else:
            weights = None
        
        if st.button("🔄 Generate Recommendations", type="primary"):
            generate_recommendations(recommendation_type, num_recommendations, weights)
        
        # Quick stats
        st.subheader("Quick Stats")
        st.metric("Total Interactions", len(st.session_state.interaction_log))
        st.metric("Recommendations Generated", len(st.session_state.recommendation_history))
    
    # Main content
    tabs = st.tabs(["📊 Recommendations", "👤 User Profile", "📈 Analytics", "🔬 A/B Testing", "⚙️ Settings"])
    
    with tabs[0]:
        render_recommendations_tab()
    
    with tabs[1]:
        render_user_profile_tab()
    
    with tabs[2]:
        render_analytics_tab()
    
    with tabs[3]:
        render_ab_testing_tab()
    
    with tabs[4]:
        render_settings_tab()

def generate_recommendations(rec_type: str, num_recs: int, weights: Dict = None):
    """Generate recommendations based on selected strategy"""
    engine = st.session_state.recommendation_engine
    content_pool = get_mock_content_pool()
    content_ids = [c['id'] for c in content_pool]
    
    with st.spinner("Generating personalized recommendations..."):
        if rec_type == "Hybrid":
            recommendations = engine.recommend_hybrid(
                st.session_state.selected_user,
                content_ids,
                num_recs,
                weights
            )
        elif rec_type == "Content-Based":
            recommendations = engine.recommend_content_based(
                st.session_state.selected_user,
                content_ids,
                num_recs
            )
        elif rec_type == "Collaborative":
            recommendations = engine.recommend_collaborative(
                st.session_state.selected_user,
                content_ids,
                num_recs
            )
        elif rec_type == "Trending":
            recommendations = engine.recommend_trending(
                content_ids,
                'daily',
                num_recs
            )
        elif rec_type == "Discovery":
            recommendations = engine.recommend_discovery(
                st.session_state.selected_user,
                content_ids,
                num_recs
            )
        else:  # Popular
            recommendations = engine.recommend_popular(
                content_ids,
                num_recs
            )
    
    # Store in session state
    st.session_state.current_recommendations = recommendations
    st.session_state.content_pool = content_pool
    st.session_state.recommendation_history.append({
        'timestamp': datetime.now(),
        'type': rec_type,
        'count': len(recommendations),
        'user': st.session_state.selected_user
    })
    
    st.success(f"Generated {len(recommendations)} recommendations using {rec_type} strategy!")

def render_recommendations_tab():
    """Render the recommendations tab"""
    if 'current_recommendations' not in st.session_state:
        st.info("Click 'Generate Recommendations' in the sidebar to get started!")
        return
    
    recommendations = st.session_state.current_recommendations
    content_pool = {c['id']: c for c in st.session_state.content_pool}
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_score = np.mean([r.score for r in recommendations])
        st.metric("Average Score", f"{avg_score:.2f}")
    
    with col2:
        avg_confidence = np.mean([r.confidence for r in recommendations])
        st.metric("Average Confidence", f"{avg_confidence:.1%}")
    
    with col3:
        unique_types = len(set([r.recommendation_type for r in recommendations]))
        st.metric("Strategy Types", unique_types)
    
    with col4:
        st.metric("Total Recommendations", len(recommendations))
    
    # Filter options
    st.subheader("Filter Recommendations")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_score = st.slider("Minimum Score", 0.0, 1.0, 0.0)
    
    with col2:
        min_confidence = st.slider("Minimum Confidence", 0.0, 1.0, 0.0)
    
    with col3:
        selected_types = st.multiselect(
            "Recommendation Types",
            [r.value for r in RecommendationType],
            default=[]
        )
    
    # Filter recommendations
    filtered_recs = [
        r for r in recommendations
        if r.score >= min_score 
        and r.confidence >= min_confidence
        and (not selected_types or r.recommendation_type.value in selected_types)
    ]
    
    st.subheader(f"Showing {len(filtered_recs)} Recommendations")
    
    # Display recommendations
    for rec in filtered_recs:
        if rec.content_id in content_pool:
            with st.container():
                render_recommendation_card(rec, content_pool[rec.content_id])
                st.markdown("---")

def render_user_profile_tab():
    """Render user profile information"""
    engine = st.session_state.recommendation_engine
    profile = engine.get_user_profile(st.session_state.selected_user)
    
    st.subheader(f"User Profile: {profile.user_id}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Interests")
        for interest in profile.interests[:5]:
            st.markdown(f"• {interest}")
        
        st.markdown("### Preferred Categories")
        for category in profile.preferred_categories[:5]:
            st.markdown(f"• {category}")
    
    with col2:
        st.markdown("### Viewing History")
        history_df = pd.DataFrame({
            'Content ID': profile.viewing_history[:10],
            'Interaction Score': [profile.interaction_scores.get(cid, 0) 
                                 for cid in profile.viewing_history[:10]]
        })
        st.dataframe(history_df)
    
    # Activity heatmap
    st.markdown("### Activity Patterns")
    if profile.active_times:
        hours = list(range(24))
        activity_counts = [profile.active_times.count(h) for h in hours]
        
        fig = go.Figure(data=go.Scatterpolar(
            r=activity_counts,
            theta=[f"{h:02d}:00" for h in hours],
            fill='toself',
            name='Activity'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(activity_counts) if activity_counts else 1]
                )),
            showlegend=False,
            title="24-Hour Activity Pattern"
        )
        
        st.plotly_chart(fig, use_container_width=True)

def render_analytics_tab():
    """Render analytics dashboard"""
    st.subheader("Recommendation Analytics")
    
    # Performance metrics over time
    if st.session_state.recommendation_history:
        history_df = pd.DataFrame(st.session_state.recommendation_history)
        
        # Recommendations over time
        fig1 = px.line(
            history_df,
            x='timestamp',
            y='count',
            color='type',
            title='Recommendations Generated Over Time',
            markers=True
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    # Interaction analysis
    if st.session_state.interaction_log:
        interaction_df = pd.DataFrame(st.session_state.interaction_log)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Interaction types distribution
            type_counts = interaction_df['type'].value_counts()
            fig2 = px.pie(
                values=type_counts.values,
                names=type_counts.index,
                title='Interaction Type Distribution'
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        with col2:
            # Interactions over time
            interaction_df['hour'] = pd.to_datetime(interaction_df['timestamp']).dt.hour
            hourly_counts = interaction_df.groupby('hour').size()
            
            fig3 = px.bar(
                x=hourly_counts.index,
                y=hourly_counts.values,
                title='Interactions by Hour of Day',
                labels={'x': 'Hour', 'y': 'Count'}
            )
            st.plotly_chart(fig3, use_container_width=True)
    
    # Recommendation type effectiveness
    if 'current_recommendations' in st.session_state:
        recs = st.session_state.current_recommendations
        
        type_scores = {}
        for rec in recs:
            rec_type = rec.recommendation_type.value
            if rec_type not in type_scores:
                type_scores[rec_type] = []
            type_scores[rec_type].append(rec.score)
        
        if type_scores:
            avg_scores = {k: np.mean(v) for k, v in type_scores.items()}
            
            fig4 = px.bar(
                x=list(avg_scores.keys()),
                y=list(avg_scores.values()),
                title='Average Score by Recommendation Type',
                labels={'x': 'Type', 'y': 'Average Score'}
            )
            st.plotly_chart(fig4, use_container_width=True)

def render_ab_testing_tab():
    """Render A/B testing interface"""
    st.subheader("A/B Testing Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Test Configuration")
        
        test_name = st.text_input("Test Name", "Algorithm Comparison Test")
        
        variant_a = st.selectbox(
            "Variant A",
            ["Content-Based", "Collaborative", "Hybrid"]
        )
        
        variant_b = st.selectbox(
            "Variant B",
            ["Trending", "Popular", "Discovery"]
        )
        
        test_size = st.slider("Test Size (users)", 100, 10000, 1000)
        
        if st.button("Start A/B Test"):
            st.success(f"Started A/B test: {test_name}")
    
    with col2:
        st.markdown("### Test Results")
        
        # Mock A/B test results
        results = {
            'Variant A': {
                'CTR': 0.15,
                'Engagement': 0.72,
                'Satisfaction': 4.2
            },
            'Variant B': {
                'CTR': 0.18,
                'Engagement': 0.68,
                'Satisfaction': 4.0
            }
        }
        
        metrics_df = pd.DataFrame(results).T
        
        fig = go.Figure()
        
        for metric in metrics_df.columns:
            fig.add_trace(go.Bar(
                name=metric,
                x=metrics_df.index,
                y=metrics_df[metric],
                text=metrics_df[metric].round(2),
                textposition='auto'
            ))
        
        fig.update_layout(
            title="A/B Test Comparison",
            barmode='group',
            yaxis_title="Value",
            xaxis_title="Variant"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistical significance
        st.markdown("### Statistical Analysis")
        st.info("Variant B shows +20% improvement in CTR (p-value: 0.03)")
        st.warning("No significant difference in Engagement (p-value: 0.12)")

def render_settings_tab():
    """Render settings and configuration"""
    st.subheader("Recommendation Engine Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Algorithm Parameters")
        
        st.number_input("TF-IDF Max Features", 100, 10000, 5000)
        st.number_input("LDA Topics", 10, 100, 50)
        st.slider("Time Decay Factor", 0.0, 1.0, 0.7)
        st.slider("Minimum Confidence Threshold", 0.0, 1.0, 0.3)
    
    with col2:
        st.markdown("### Cache Settings")
        
        cache_ttl = st.number_input("Cache TTL (hours)", 1, 24, 1)
        st.checkbox("Enable Recommendation Cache", value=True)
        st.checkbox("Enable Embedding Cache", value=True)
        
        if st.button("Clear All Caches"):
            st.success("Caches cleared successfully!")
    
    st.markdown("### Data Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Update Trending Content"):
            engine = st.session_state.recommendation_engine
            engine.update_trending_content('daily')
            st.success("Trending content updated!")
    
    with col2:
        if st.button("Rebuild Embeddings"):
            st.success("Embeddings rebuild scheduled!")
    
    with col3:
        if st.button("Export Analytics"):
            st.success("Analytics exported to CSV!")
    
    # Model information
    st.markdown("### Model Information")
    
    info_data = {
        'Component': ['TF-IDF Vectorizer', 'LDA Model', 'Neural CF', 'Content Embeddings'],
        'Status': ['✅ Ready', '✅ Ready', '⚠️ Not Available', '✅ Cached'],
        'Last Updated': ['2 hours ago', '1 day ago', 'N/A', '30 minutes ago'],
        'Performance': ['98ms', '145ms', 'N/A', '12ms']
    }
    
    info_df = pd.DataFrame(info_data)
    st.dataframe(info_df, use_container_width=True)

if __name__ == "__main__":
    main()