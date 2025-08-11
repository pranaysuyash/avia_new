"""
User Engagement Analytics Dashboard
Interactive Streamlit interface for advanced user behavior analytics,
heatmaps, user journeys, and predictive insights
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
from datetime import datetime, timedelta
import asyncio
import json
from typing import Dict, List, Optional

# Page configuration
st.set_page_config(
    page_title="User Engagement Analytics",
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
        margin: 0.5rem 0;
    }
    .insight-card {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .recommendation-card {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .risk-high {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
    }
    .risk-medium {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
    }
    .risk-low {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
    }
</style>
""", unsafe_allow_html=True)

class UserEngagementUI:
    def __init__(self):
        self.api_base = st.session_state.get('api_base', 'http://localhost:8000')
        # Initialize with sample data for demo
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Initialize with sample data for demonstration"""
        # Sample real-time metrics
        self.real_time_data = {
            'active_users_last_hour': 145,
            'active_users_last_24h': 2847,
            'events_last_hour': 1249,
            'avg_session_duration_last_24h': 892.5,
            'real_time_users': 23,
            'bounce_rate_last_24h': 0.32,
            'top_pages_last_hour': [
                ('dashboard', 156),
                ('transcription', 98),
                ('analytics', 67),
                ('settings', 45),
                ('help', 33)
            ],
            'top_events_last_hour': [
                ('page_view', 456),
                ('feature_use', 234),
                ('transcription_start', 89),
                ('search', 67),
                ('download', 45)
            ]
        }
        
        # Sample user segments
        self.user_segments = {
            'power_user': {
                'count': 234,
                'avg_engagement': 87.5,
                'retention_rate': 0.89,
                'avg_session_duration': 1245.0,
                'characteristics': [
                    'Uses 8+ different features regularly',
                    'Long session durations (20+ minutes)',
                    'High feature adoption rate',
                    'Low churn risk (5%)'
                ]
            },
            'regular_user': {
                'count': 1456,
                'avg_engagement': 62.3,
                'retention_rate': 0.67,
                'avg_session_duration': 678.0,
                'characteristics': [
                    'Uses 3-5 features regularly',
                    'Moderate session durations (11 minutes)',
                    'Good retention rate',
                    'Medium churn risk (15%)'
                ]
            },
            'occasional_user': {
                'count': 892,
                'avg_engagement': 34.1,
                'retention_rate': 0.45,
                'avg_session_duration': 234.0,
                'characteristics': [
                    'Uses 1-2 features',
                    'Short session durations (4 minutes)',
                    'Lower retention rate',
                    'Higher churn risk (35%)'
                ]
            },
            'churning_user': {
                'count': 167,
                'avg_engagement': 12.4,
                'retention_rate': 0.12,
                'avg_session_duration': 89.0,
                'characteristics': [
                    'Declining activity patterns',
                    'Very short sessions',
                    'High churn probability (78%)',
                    'Needs immediate attention'
                ]
            }
        }
        
        # Sample engagement insights
        self.engagement_insights = [
            {
                'type': 'engagement_trend',
                'title': 'Engagement Trending Up',
                'description': 'User engagement has increased 15% over the last 7 days',
                'metric_value': 15.2,
                'trend': 'increasing',
                'confidence': 0.87,
                'recommendations': [
                    'Analyze successful engagement drivers',
                    'Scale effective strategies',
                    'Monitor for sustainability'
                ]
            },
            {
                'type': 'feature_adoption',
                'title': 'Advanced Analytics Gaining Traction',
                'description': 'Advanced analytics feature usage up 32% this week',
                'metric_value': 32.1,
                'trend': 'increasing',
                'confidence': 0.91,
                'recommendations': [
                    'Promote advanced analytics in onboarding',
                    'Create tutorial content',
                    'Gather user feedback'
                ]
            },
            {
                'type': 'churn_risk',
                'title': 'Churn Risk Alert',
                'description': '12% of users showing early churn indicators',
                'metric_value': 12.3,
                'trend': 'stable',
                'confidence': 0.76,
                'recommendations': [
                    'Implement targeted retention campaigns',
                    'Provide personalized support',
                    'Analyze common churn patterns'
                ]
            }
        ]

def main():
    ui = UserEngagementUI()
    
    st.title("📊 User Engagement Analytics Dashboard")
    st.markdown("Advanced analytics for user behavior, engagement patterns, and predictive insights")
    
    # Sidebar navigation
    st.sidebar.title("Analytics Navigation")
    page = st.sidebar.selectbox(
        "Select Analysis View",
        [
            "Real-time Overview",
            "User Behavior Analysis",
            "Engagement Heatmaps",
            "User Journey Mapping",
            "Predictive Analytics",
            "Segment Analysis",
            "Churn Prevention",
            "Feature Usage Analytics"
        ]
    )
    
    # Time range selector
    st.sidebar.subheader("Time Range")
    time_range = st.sidebar.selectbox(
        "Analysis Period",
        ["Last Hour", "Last 24 Hours", "Last 7 Days", "Last 30 Days", "Last 90 Days"]
    )
    
    # Route to selected page
    if page == "Real-time Overview":
        show_real_time_overview(ui)
    elif page == "User Behavior Analysis":
        show_user_behavior_analysis(ui)
    elif page == "Engagement Heatmaps":
        show_engagement_heatmaps(ui)
    elif page == "User Journey Mapping":
        show_user_journey_mapping(ui)
    elif page == "Predictive Analytics":
        show_predictive_analytics(ui)
    elif page == "Segment Analysis":
        show_segment_analysis(ui)
    elif page == "Churn Prevention":
        show_churn_prevention(ui)
    elif page == "Feature Usage Analytics":
        show_feature_usage_analytics(ui)

def show_real_time_overview(ui: UserEngagementUI):
    """Real-time engagement overview"""
    st.header("🔴 Real-time Engagement Overview")
    
    # Real-time metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "🟢 Live Users",
            ui.real_time_data['real_time_users'],
            delta="5 min avg"
        )
    
    with col2:
        st.metric(
            "👥 Users (1h)",
            ui.real_time_data['active_users_last_hour'],
            delta=f"+{ui.real_time_data['active_users_last_hour'] - 132}"
        )
    
    with col3:
        st.metric(
            "📊 Events (1h)",
            ui.real_time_data['events_last_hour'],
            delta="+156"
        )
    
    with col4:
        avg_duration = ui.real_time_data['avg_session_duration_last_24h']
        st.metric(
            "⏱️ Avg Session",
            f"{avg_duration/60:.1f} min",
            delta="+2.3 min"
        )
    
    with col5:
        bounce_rate = ui.real_time_data['bounce_rate_last_24h']
        st.metric(
            "⚡ Bounce Rate",
            f"{bounce_rate:.1%}",
            delta="-3.2%",
            delta_color="inverse"
        )
    
    st.divider()
    
    # Real-time charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔥 Top Pages (Last Hour)")
        pages_df = pd.DataFrame(
            ui.real_time_data['top_pages_last_hour'],
            columns=['Page', 'Views']
        )
        fig = px.bar(
            pages_df, 
            x='Views', 
            y='Page',
            orientation='h',
            color='Views',
            color_continuous_scale='viridis'
        )
        fig.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📈 Top Events (Last Hour)")
        events_df = pd.DataFrame(
            ui.real_time_data['top_events_last_hour'],
            columns=['Event Type', 'Count']
        )
        fig = px.pie(
            events_df,
            values='Count',
            names='Event Type',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    # Real-time activity stream
    st.subheader("🌊 Live Activity Stream")
    
    # Sample real-time events
    activity_data = [
        {"time": "2 sec ago", "user": "user_1234", "action": "Started transcription", "page": "/transcribe"},
        {"time": "5 sec ago", "user": "user_5678", "action": "Downloaded results", "page": "/results"},
        {"time": "12 sec ago", "user": "user_9101", "action": "Viewed dashboard", "page": "/dashboard"},
        {"time": "18 sec ago", "user": "user_1121", "action": "Used search", "page": "/search"},
        {"time": "23 sec ago", "user": "user_3141", "action": "Opened help", "page": "/help"},
        {"time": "31 sec ago", "user": "user_5161", "action": "Updated profile", "page": "/profile"},
        {"time": "45 sec ago", "user": "user_7181", "action": "Started session", "page": "/login"},
        {"time": "1 min ago", "user": "user_9202", "action": "Completed onboarding", "page": "/onboard"},
    ]
    
    activity_df = pd.DataFrame(activity_data)
    st.dataframe(
        activity_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "time": "⏰ Time",
            "user": "👤 User",
            "action": "🎬 Action",
            "page": "📄 Page"
        }
    )
    
    # Auto-refresh option
    if st.button("🔄 Refresh Real-time Data"):
        st.rerun()

def show_user_behavior_analysis(ui: UserEngagementUI):
    """Comprehensive user behavior analysis"""
    st.header("🧠 User Behavior Analysis")
    
    # Behavior patterns overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📊 Session Patterns")
        # Sample session duration distribution
        session_durations = np.random.lognormal(mean=3, sigma=1, size=1000) * 60  # in seconds
        session_durations = session_durations[session_durations < 3600]  # cap at 1 hour
        
        fig = px.histogram(
            x=session_durations/60,
            nbins=30,
            title="Session Duration Distribution",
            labels={'x': 'Duration (minutes)', 'y': 'Number of Sessions'}
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Feature Usage")
        feature_data = {
            'Feature': ['Transcription', 'Analytics', 'Search', 'Export', 'Collaboration', 'API'],
            'Usage': [1245, 892, 734, 567, 234, 156]
        }
        fig = px.bar(
            feature_data,
            x='Feature',
            y='Usage',
            color='Usage',
            color_continuous_scale='plasma'
        )
        fig.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        st.subheader("⏰ Activity Patterns")
        # Hourly activity pattern
        hours = list(range(24))
        activity = [12, 8, 5, 3, 2, 4, 15, 45, 89, 134, 156, 178, 
                   165, 189, 198, 185, 167, 145, 123, 98, 67, 45, 32, 18]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hours,
            y=activity,
            mode='lines+markers',
            fill='tonexty',
            name='Hourly Activity'
        ))
        fig.update_layout(
            title="24-Hour Activity Pattern",
            xaxis_title="Hour of Day",
            yaxis_title="Active Users",
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # User journey flow
    st.subheader("🗺️ User Journey Flow")
    
    # Create a simplified sankey diagram for user flow
    fig = go.Figure(data=[go.Sankey(
        node = dict(
            pad = 15,
            thickness = 20,
            line = dict(color = "black", width = 0.5),
            label = ["Landing Page", "Dashboard", "Transcription", "Analytics", 
                    "Export", "Help", "Settings", "Exit"],
            color = "blue"
        ),
        link = dict(
            source = [0, 0, 1, 1, 1, 2, 2, 3, 4, 5, 6],
            target = [1, 7, 2, 3, 7, 4, 7, 7, 7, 7, 7],
            value = [800, 200, 400, 250, 150, 200, 200, 100, 150, 80, 70]
        )
    )])
    
    fig.update_layout(title_text="User Flow Through Application", font_size=10)
    st.plotly_chart(fig, use_container_width=True)
    
    # Behavioral insights
    st.subheader("💡 Behavioral Insights")
    
    insights = [
        {
            "icon": "📈",
            "title": "High Engagement Sessions",
            "insight": "Users with sessions longer than 15 minutes show 3x higher retention rates",
            "action": "Focus on increasing session duration through better content flow"
        },
        {
            "icon": "🔄",
            "title": "Feature Discovery Pattern",
            "insight": "87% of power users discover new features within their first 3 sessions",
            "action": "Improve feature discoverability in early user experience"
        },
        {
            "icon": "⚡",
            "title": "Quick Exit Points",
            "insight": "32% of users exit after viewing help page - suggests usability issues",
            "action": "Redesign help system and improve in-app guidance"
        }
    ]
    
    for insight in insights:
        st.markdown(f"""
        <div class="insight-card">
            <h4>{insight['icon']} {insight['title']}</h4>
            <p><strong>Insight:</strong> {insight['insight']}</p>
            <p><strong>Recommended Action:</strong> {insight['action']}</p>
        </div>
        """, unsafe_allow_html=True)

def show_engagement_heatmaps(ui: UserEngagementUI):
    """Interactive engagement heatmaps"""
    st.header("🔥 Engagement Heatmaps")
    
    # Time-based heatmap
    st.subheader("⏰ Time-based Activity Heatmap")
    
    # Generate sample heatmap data
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    hours = [f"{h:02d}:00" for h in range(24)]
    
    # Create random but realistic activity data
    np.random.seed(42)
    activity_data = np.random.poisson(lam=50, size=(7, 24))
    
    # Make weekdays more active, and business hours busier
    for i, day in enumerate(days):
        for j, hour in enumerate(range(24)):
            base_activity = activity_data[i][j]
            
            # Weekend penalty
            if i >= 5:  # Saturday, Sunday
                base_activity *= 0.6
            
            # Business hours boost
            if 9 <= hour <= 17:
                base_activity *= 1.8
            # Evening boost
            elif 18 <= hour <= 22:
                base_activity *= 1.3
            # Night/early morning reduction
            elif hour < 6 or hour > 23:
                base_activity *= 0.3
            
            activity_data[i][j] = int(base_activity)
    
    # Create heatmap
    fig = px.imshow(
        activity_data,
        x=hours[::2],  # Show every 2nd hour to reduce clutter
        y=days,
        aspect="auto",
        color_continuous_scale='viridis',
        title="User Activity Intensity by Day and Hour"
    )
    fig.update_layout(
        xaxis_title="Hour of Day",
        yaxis_title="Day of Week",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Feature usage heatmap
    st.subheader("🛠️ Feature Usage Heatmap")
    
    # Sample feature usage by user segment
    features = ['Transcription', 'Analytics', 'Search', 'Export', 'API', 'Collaboration', 'Templates', 'Integrations']
    segments = ['Power Users', 'Regular Users', 'Occasional Users', 'New Users']
    
    feature_usage = np.array([
        [95, 87, 78, 65, 54, 89, 67, 78],  # Power Users
        [78, 45, 67, 34, 23, 45, 34, 29],  # Regular Users  
        [56, 23, 45, 12, 8, 23, 18, 15],   # Occasional Users
        [34, 12, 23, 8, 3, 12, 9, 6]       # New Users
    ])
    
    fig = px.imshow(
        feature_usage,
        x=features,
        y=segments,
        aspect="auto",
        color_continuous_scale='plasma',
        title="Feature Usage by User Segment (%)"
    )
    fig.update_layout(
        xaxis_title="Features",
        yaxis_title="User Segments",
        height=300
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Geographic engagement heatmap
    st.subheader("🌍 Geographic Engagement")
    
    # Sample geographic data
    locations = {
        'Country': ['United States', 'United Kingdom', 'Germany', 'France', 'Canada', 
                   'Australia', 'Japan', 'India', 'Brazil', 'Netherlands'],
        'Users': [1245, 567, 423, 334, 298, 234, 189, 156, 134, 98],
        'Avg_Session': [12.3, 15.7, 18.2, 14.1, 13.9, 16.4, 11.8, 9.7, 8.9, 17.3],
        'Engagement_Score': [78, 82, 85, 79, 81, 84, 73, 68, 65, 86]
    }
    
    geo_df = pd.DataFrame(locations)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # User distribution by country
        fig = px.choropleth(
            geo_df,
            locations='Country',
            locationmode='country names',
            color='Users',
            title="User Distribution by Country",
            color_continuous_scale='viridis'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Engagement score by country
        fig = px.bar(
            geo_df.sort_values('Engagement_Score', ascending=True),
            x='Engagement_Score',
            y='Country',
            orientation='h',
            color='Engagement_Score',
            title="Engagement Score by Country",
            color_continuous_scale='plasma'
        )
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

def show_user_journey_mapping(ui: UserEngagementUI):
    """User journey visualization and analysis"""
    st.header("🗺️ User Journey Mapping")
    
    # Journey overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Journeys", "1,247", delta="12%")
    with col2:
        st.metric("Completion Rate", "68.3%", delta="5.2%")
    with col3:
        st.metric("Avg Journey Time", "8.7 min", delta="-1.2 min")
    with col4:
        st.metric("Drop-off Rate", "31.7%", delta="-5.2%", delta_color="inverse")
    
    st.divider()
    
    # Journey funnel analysis
    st.subheader("📈 Onboarding Journey Funnel")
    
    # Sample funnel data
    funnel_data = {
        'Stage': ['Landing Page', 'Sign Up', 'Email Verification', 'Profile Setup', 
                 'First Upload', 'First Transcription', 'Feature Discovery', 'Completed Onboarding'],
        'Users': [1000, 750, 680, 620, 520, 450, 380, 320],
        'Conversion_Rate': [100.0, 75.0, 90.7, 91.2, 83.9, 86.5, 84.4, 84.2]
    }
    
    funnel_df = pd.DataFrame(funnel_data)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Funnel chart
        fig = go.Figure(go.Funnel(
            y = funnel_df['Stage'],
            x = funnel_df['Users'],
            textinfo = "value+percent initial",
            marker = dict(
                color = ["deepskyblue", "lightsalmon", "tan", "teal", "silver", 
                        "gold", "lightcoral", "lightgreen"]
            )
        ))
        fig.update_layout(title="User Onboarding Funnel", height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Drop-off analysis
        st.subheader("🚨 Drop-off Points")
        
        drop_offs = []
        for i in range(1, len(funnel_df)):
            prev_users = funnel_df.iloc[i-1]['Users']
            curr_users = funnel_df.iloc[i]['Users']
            drop_off = prev_users - curr_users
            drop_off_rate = (drop_off / prev_users) * 100
            
            if drop_off_rate > 15:  # Significant drop-off
                drop_offs.append({
                    'stage': funnel_df.iloc[i]['Stage'],
                    'drop_off': drop_off,
                    'rate': drop_off_rate
                })
        
        for drop_off in drop_offs:
            st.markdown(f"""
            <div class="recommendation-card">
                <h5>⚠️ {drop_off['stage']}</h5>
                <p><strong>{drop_off['drop_off']} users</strong> ({drop_off['rate']:.1f}%) dropped off</p>
            </div>
            """, unsafe_allow_html=True)
    
    # User path analysis
    st.subheader("🛤️ Common User Paths")
    
    # Sample path data
    paths = [
        {"path": "Landing → Sign Up → Profile → Upload → Transcribe", "users": 245, "completion": "95%"},
        {"path": "Landing → Sign Up → Profile → Help → Exit", "users": 89, "completion": "15%"},
        {"path": "Landing → Sign Up → Verify → Exit", "users": 67, "completion": "25%"},
        {"path": "Landing → Browse → Sign Up → Profile → Upload", "users": 156, "completion": "87%"},
        {"path": "Landing → Demo → Sign Up → Complete Onboarding", "users": 134, "completion": "92%"}
    ]
    
    paths_df = pd.DataFrame(paths)
    
    # Create a more detailed path visualization
    col1, col2 = st.columns([3, 1])
    
    with col1:
        fig = px.bar(
            paths_df.sort_values('users', ascending=True),
            x='users',
            y='path',
            orientation='h',
            color='users',
            title="Most Common User Paths",
            color_continuous_scale='viridis'
        )
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📊 Path Metrics")
        for path in paths:
            completion_rate = float(path['completion'].strip('%'))
            if completion_rate >= 80:
                color_class = "risk-low"
                icon = "✅"
            elif completion_rate >= 50:
                color_class = "risk-medium"
                icon = "⚠️"
            else:
                color_class = "risk-high"
                icon = "🚨"
            
            st.markdown(f"""
            <div class="metric-card {color_class}">
                <p><strong>{icon} {path['users']} users</strong></p>
                <p>Completion: {path['completion']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Journey timing analysis
    st.subheader("⏱️ Journey Timing Analysis")
    
    # Sample timing data
    timing_data = {
        'Stage': ['Sign Up', 'Profile Setup', 'First Upload', 'First Transcription'],
        'Avg_Time_Minutes': [2.3, 4.7, 8.2, 12.5],
        'Median_Time_Minutes': [1.8, 3.1, 5.4, 8.7],
        'Users_Completed': [750, 620, 520, 450]
    }
    
    timing_df = pd.DataFrame(timing_data)
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Time to Complete Each Stage", "Completion Distribution"),
        specs=[[{"secondary_y": False}, {"secondary_y": True}]]
    )
    
    # Average time bars
    fig.add_trace(
        go.Bar(x=timing_df['Stage'], y=timing_df['Avg_Time_Minutes'], 
               name='Avg Time', marker_color='lightblue'),
        row=1, col=1
    )
    
    # Median time line
    fig.add_trace(
        go.Scatter(x=timing_df['Stage'], y=timing_df['Median_Time_Minutes'],
                  mode='lines+markers', name='Median Time', line=dict(color='red')),
        row=1, col=1
    )
    
    # Users completed bars
    fig.add_trace(
        go.Bar(x=timing_df['Stage'], y=timing_df['Users_Completed'],
               name='Users Completed', marker_color='lightgreen'),
        row=1, col=2
    )
    
    fig.update_layout(height=400, title_text="Journey Stage Analysis")
    st.plotly_chart(fig, use_container_width=True)

def show_predictive_analytics(ui: UserEngagementUI):
    """Predictive analytics and AI insights"""
    st.header("🔮 Predictive Analytics")
    
    # Predictive metrics overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Churn Risk (7d)", "12.3%", delta="-2.1%", delta_color="inverse")
    with col2:
        st.metric("Growth Potential", "78 users", delta="+15 users")
    with col3:
        st.metric("Revenue Forecast", "$45.2K", delta="+$8.1K")
    with col4:
        st.metric("Feature Adoption", "67%", delta="+12%")
    
    st.divider()
    
    # Churn prediction model
    st.subheader("📉 Churn Prediction Analysis")
    
    # Sample churn risk data
    churn_data = {
        'User_ID': ['user_001', 'user_002', 'user_003', 'user_004', 'user_005', 
                   'user_006', 'user_007', 'user_008', 'user_009', 'user_010'],
        'Days_Since_Last_Active': [15, 3, 22, 8, 45, 7, 12, 31, 6, 18],
        'Session_Frequency_Decline': [65, 10, 78, 25, 89, 15, 45, 82, 8, 56],
        'Feature_Usage_Decline': [45, 5, 67, 18, 76, 12, 34, 71, 3, 42],
        'Churn_Probability': [0.78, 0.12, 0.85, 0.34, 0.91, 0.18, 0.56, 0.88, 0.09, 0.64],
        'Risk_Level': ['High', 'Low', 'High', 'Medium', 'High', 'Low', 'Medium', 'High', 'Low', 'High']
    }
    
    churn_df = pd.DataFrame(churn_data)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Churn probability scatter plot
        fig = px.scatter(
            churn_df,
            x='Days_Since_Last_Active',
            y='Churn_Probability',
            size='Feature_Usage_Decline',
            color='Risk_Level',
            color_discrete_map={'Low': 'green', 'Medium': 'orange', 'High': 'red'},
            title="Churn Risk Analysis by User Behavior",
            labels={
                'Days_Since_Last_Active': 'Days Since Last Activity',
                'Churn_Probability': 'Churn Probability'
            }
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🚨 High Risk Users")
        
        high_risk_users = churn_df[churn_df['Risk_Level'] == 'High']
        
        for _, user in high_risk_users.iterrows():
            st.markdown(f"""
            <div class="recommendation-card risk-high">
                <h5>👤 {user['User_ID']}</h5>
                <p><strong>Churn Risk:</strong> {user['Churn_Probability']:.0%}</p>
                <p><strong>Last Active:</strong> {user['Days_Since_Last_Active']} days ago</p>
                <p><strong>Action:</strong> Immediate intervention needed</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Feature adoption prediction
    st.subheader("🚀 Feature Adoption Forecasting")
    
    # Sample feature adoption trends
    days = pd.date_range('2024-01-01', periods=90, freq='D')
    features = ['Advanced Analytics', 'API Integration', 'Collaboration Tools', 'Mobile App']
    
    fig = go.Figure()
    
    colors = ['blue', 'red', 'green', 'orange']
    for i, feature in enumerate(features):
        # Generate realistic adoption curves
        base_adoption = np.random.normal(50, 10)
        growth_rate = np.random.uniform(0.01, 0.03)
        noise = np.random.normal(0, 2, len(days))
        
        adoption = base_adoption * (1 + growth_rate * np.arange(len(days))) + noise.cumsum()
        adoption = np.clip(adoption, 0, 100)
        
        fig.add_trace(go.Scatter(
            x=days,
            y=adoption,
            mode='lines',
            name=feature,
            line=dict(color=colors[i], width=3)
        ))
    
    fig.update_layout(
        title="Feature Adoption Trends & Forecasting",
        xaxis_title="Date",
        yaxis_title="Adoption Rate (%)",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # User growth prediction
    st.subheader("📈 User Growth Forecasting")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Historical vs predicted growth
        dates = pd.date_range('2024-01-01', periods=120, freq='D')
        historical_split = 90
        
        # Generate historical data
        base_users = 1000
        daily_growth = np.random.normal(0.02, 0.01, historical_split)
        historical_users = [base_users]
        
        for growth in daily_growth:
            new_users = historical_users[-1] * (1 + growth)
            historical_users.append(new_users)
        
        # Generate predictions
        predicted_growth = np.random.normal(0.025, 0.005, len(dates) - historical_split - 1)
        predicted_users = historical_users.copy()
        
        for growth in predicted_growth:
            new_users = predicted_users[-1] * (1 + growth)
            predicted_users.append(new_users)
        
        fig = go.Figure()
        
        # Historical data
        fig.add_trace(go.Scatter(
            x=dates[:historical_split],
            y=historical_users[:historical_split],
            mode='lines',
            name='Historical',
            line=dict(color='blue', width=3)
        ))
        
        # Predictions
        fig.add_trace(go.Scatter(
            x=dates[historical_split-1:],
            y=predicted_users[historical_split-1:],
            mode='lines',
            name='Predicted',
            line=dict(color='red', width=3, dash='dash')
        ))
        
        fig.update_layout(
            title="User Growth: Historical vs Predicted",
            xaxis_title="Date",
            yaxis_title="Total Users",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Growth Predictions")
        
        growth_metrics = [
            {"metric": "30-day Growth", "value": "+234 users", "confidence": "87%"},
            {"metric": "60-day Growth", "value": "+567 users", "confidence": "73%"},
            {"metric": "90-day Growth", "value": "+890 users", "confidence": "64%"},
            {"metric": "Revenue Impact", "value": "+$12.4K", "confidence": "71%"}
        ]
        
        for metric in growth_metrics:
            st.markdown(f"""
            <div class="metric-card">
                <h5>{metric['metric']}</h5>
                <p><strong>{metric['value']}</strong></p>
                <p>Confidence: {metric['confidence']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # AI-generated insights
    st.subheader("🤖 AI-Generated Insights")
    
    ai_insights = [
        {
            "insight": "Users who complete onboarding within 24 hours show 4x higher retention",
            "confidence": "94%",
            "action": "Implement time-sensitive onboarding incentives"
        },
        {
            "insight": "Feature usage patterns predict churn 14 days in advance with high accuracy",
            "confidence": "87%", 
            "action": "Deploy predictive alerts for at-risk users"
        },
        {
            "insight": "Geographic expansion to EMEA could yield 40% user growth",
            "confidence": "76%",
            "action": "Consider localization and regional marketing"
        }
    ]
    
    for insight in ai_insights:
        st.markdown(f"""
        <div class="insight-card">
            <h4>🧠 AI Insight</h4>
            <p><strong>Finding:</strong> {insight['insight']}</p>
            <p><strong>Confidence:</strong> {insight['confidence']}</p>
            <p><strong>Recommended Action:</strong> {insight['action']}</p>
        </div>
        """, unsafe_allow_html=True)

def show_segment_analysis(ui: UserEngagementUI):
    """User segment analysis and characteristics"""
    st.header("👥 User Segment Analysis")
    
    # Segment overview
    total_users = sum(segment['count'] for segment in ui.user_segments.values())
    
    col1, col2, col3, col4 = st.columns(4)
    segments_list = list(ui.user_segments.items())
    
    for i, (segment_name, data) in enumerate(segments_list):
        with [col1, col2, col3, col4][i]:
            percentage = (data['count'] / total_users) * 100
            st.metric(
                segment_name.replace('_', ' ').title(),
                f"{data['count']} ({percentage:.1f}%)",
                delta=f"{data['retention_rate']:.0%} retention"
            )
    
    st.divider()
    
    # Segment comparison
    st.subheader("📊 Segment Comparison")
    
    # Create comparison chart
    segments_df = pd.DataFrame([
        {
            'Segment': segment.replace('_', ' ').title(),
            'Users': data['count'],
            'Engagement': data['avg_engagement'],
            'Retention': data['retention_rate'] * 100,
            'Avg Session (min)': data['avg_session_duration'] / 60
        }
        for segment, data in ui.user_segments.items()
    ])
    
    # Multi-metric comparison
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("User Count by Segment", "Engagement Scores", 
                       "Retention Rates", "Average Session Duration"),
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "bar"}]]
    )
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    # User count
    fig.add_trace(
        go.Bar(x=segments_df['Segment'], y=segments_df['Users'], 
               marker_color=colors, name='Users'),
        row=1, col=1
    )
    
    # Engagement scores
    fig.add_trace(
        go.Bar(x=segments_df['Segment'], y=segments_df['Engagement'],
               marker_color=colors, name='Engagement'),
        row=1, col=2
    )
    
    # Retention rates
    fig.add_trace(
        go.Bar(x=segments_df['Segment'], y=segments_df['Retention'],
               marker_color=colors, name='Retention %'),
        row=2, col=1
    )
    
    # Session duration
    fig.add_trace(
        go.Bar(x=segments_df['Segment'], y=segments_df['Avg Session (min)'],
               marker_color=colors, name='Session (min)'),
        row=2, col=2
    )
    
    fig.update_layout(height=600, showlegend=False, title_text="Segment Analysis Dashboard")
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed segment characteristics
    st.subheader("🔍 Segment Deep Dive")
    
    selected_segment = st.selectbox(
        "Select segment to analyze:",
        list(ui.user_segments.keys()),
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    segment_data = ui.user_segments[selected_segment]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"### {selected_segment.replace('_', ' ').title()} Characteristics")
        
        # Key metrics
        metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
        
        with metrics_col1:
            st.metric("Users", f"{segment_data['count']:,}")
        with metrics_col2:
            st.metric("Engagement Score", f"{segment_data['avg_engagement']:.1f}")
        with metrics_col3:
            st.metric("Retention Rate", f"{segment_data['retention_rate']:.0%}")
        
        # Characteristics
        st.markdown("**Key Characteristics:**")
        for characteristic in segment_data['characteristics']:
            st.markdown(f"• {characteristic}")
    
    with col2:
        # Segment-specific recommendations
        st.markdown("### 💡 Recommendations")
        
        if selected_segment == 'power_user':
            recommendations = [
                "Provide beta feature access",
                "Create user advisory board",
                "Implement referral program",
                "Offer advanced training"
            ]
        elif selected_segment == 'churning_user':
            recommendations = [
                "Immediate intervention needed",
                "Personal success manager",
                "Feature re-discovery tour",
                "Special retention offers"
            ]
        elif selected_segment == 'regular_user':
            recommendations = [
                "Feature upgrade campaigns",
                "Usage expansion incentives",
                "Community engagement",
                "Success story sharing"
            ]
        else:  # occasional_user
            recommendations = [
                "Re-engagement campaigns",
                "Value demonstration",
                "Simplified workflows",
                "Use case education"
            ]
        
        for recommendation in recommendations:
            st.markdown(f"""
            <div class="recommendation-card">
                <p>💡 {recommendation}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Segment transition analysis
    st.subheader("🔄 Segment Transition Analysis")
    
    # Sample transition matrix data
    transition_data = np.array([
        [0.7, 0.2, 0.08, 0.02],  # Power user transitions
        [0.1, 0.6, 0.25, 0.05],  # Regular user transitions  
        [0.05, 0.3, 0.5, 0.15],  # Occasional user transitions
        [0.02, 0.08, 0.2, 0.7]   # Churning user transitions
    ])
    
    segment_labels = ['Power User', 'Regular User', 'Occasional User', 'Churning User']
    
    fig = px.imshow(
        transition_data,
        x=segment_labels,
        y=segment_labels,
        aspect="auto",
        color_continuous_scale='RdBu',
        title="User Segment Transition Probabilities (30-day period)"
    )
    fig.update_layout(
        xaxis_title="To Segment",
        yaxis_title="From Segment",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

def show_churn_prevention(ui: UserEngagementUI):
    """Churn prevention dashboard and recommendations"""
    st.header("🛡️ Churn Prevention Dashboard")
    
    # Churn risk overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("High Risk Users", "89", delta="-12", delta_color="inverse")
    with col2:
        st.metric("Medium Risk Users", "156", delta="+8")
    with col3:
        st.metric("Intervention Success", "73%", delta="+15%")
    with col4:
        st.metric("Saved Revenue", "$23.4K", delta="+$5.2K")
    
    st.divider()
    
    # Risk distribution
    st.subheader("⚠️ Churn Risk Distribution")
    
    risk_data = {
        'Risk Level': ['Low Risk (0-30%)', 'Medium Risk (31-60%)', 'High Risk (61-80%)', 'Critical Risk (81-100%)'],
        'User Count': [1234, 456, 123, 45],
        'Colors': ['#28a745', '#ffc107', '#fd7e14', '#dc3545']
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.pie(
            values=risk_data['User Count'],
            names=risk_data['Risk Level'],
            title="Users by Churn Risk Level",
            color_discrete_sequence=risk_data['Colors']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Risk factors analysis
        risk_factors = {
            'Factor': ['Days Since Last Login', 'Feature Usage Decline', 'Session Frequency Drop', 
                      'Support Tickets', 'Error Rate Increase'],
            'Impact_Score': [0.85, 0.73, 0.68, 0.56, 0.42]
        }
        
        fig = px.bar(
            risk_factors,
            x='Impact_Score',
            y='Factor',
            orientation='h',
            title="Top Churn Risk Factors",
            color='Impact_Score',
            color_continuous_scale='Reds'
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Individual user risk analysis
    st.subheader("👤 High-Risk User Analysis")
    
    high_risk_users = [
        {
            'User_ID': 'user_12345',
            'Last_Active': '15 days ago',
            'Churn_Probability': 0.87,
            'Primary_Risk': 'Extended inactivity',
            'Recommended_Action': 'Personal outreach + feature demo'
        },
        {
            'User_ID': 'user_67890', 
            'Last_Active': '8 days ago',
            'Churn_Probability': 0.74,
            'Primary_Risk': 'Feature usage decline',
            'Recommended_Action': 'Feature re-engagement campaign'
        },
        {
            'User_ID': 'user_13579',
            'Last_Active': '3 days ago', 
            'Churn_Probability': 0.69,
            'Primary_Risk': 'Multiple support tickets',
            'Recommended_Action': 'Priority customer success call'
        }
    ]
    
    for user in high_risk_users:
        risk_level = "Critical" if user['Churn_Probability'] > 0.8 else "High"
        color_class = "risk-high" if risk_level == "Critical" else "risk-medium"
        
        col1, col2, col3 = st.columns([2, 2, 3])
        
        with col1:
            st.markdown(f"""
            <div class="metric-card {color_class}">
                <h5>👤 {user['User_ID']}</h5>
                <p><strong>Risk:</strong> {user['Churn_Probability']:.0%} ({risk_level})</p>
                <p><strong>Last Active:</strong> {user['Last_Active']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="insight-card">
                <h5>🔍 Primary Risk Factor</h5>
                <p>{user['Primary_Risk']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="recommendation-card">
                <h5>💡 Recommended Action</h5>
                <p>{user['Recommended_Action']}</p>
                <button class="btn btn-primary">Execute Action</button>
            </div>
            """, unsafe_allow_html=True)
    
    # Intervention campaigns
    st.subheader("📢 Churn Prevention Campaigns")
    
    campaigns = [
        {
            'name': 'Win-Back Email Series',
            'target': 'Users inactive 7-14 days',
            'success_rate': '34%',
            'users_targeted': 234,
            'users_retained': 80
        },
        {
            'name': 'Feature Discovery Tour',
            'target': 'Low feature adoption users',  
            'success_rate': '52%',
            'users_targeted': 156,
            'users_retained': 81
        },
        {
            'name': 'Personal Success Call',
            'target': 'High-value at-risk users',
            'success_rate': '78%', 
            'users_targeted': 45,
            'users_retained': 35
        }
    ]
    
    campaigns_df = pd.DataFrame(campaigns)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Campaign success rates
        fig = px.bar(
            campaigns_df,
            x='name',
            y='success_rate',
            title="Campaign Success Rates",
            color='success_rate',
            color_continuous_scale='viridis'
        )
        fig.update_layout(showlegend=False, xaxis_title="Campaign", yaxis_title="Success Rate (%)")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Users retained by campaign
        fig = px.pie(
            campaigns_df,
            values='users_retained',
            names='name',
            title="Users Retained by Campaign Type"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Predictive intervention recommendations
    st.subheader("🎯 Predictive Intervention Recommendations")
    
    st.markdown("""
    <div class="insight-card">
        <h4>🤖 AI-Powered Recommendations</h4>
        <p><strong>Immediate Actions (Next 24 Hours):</strong></p>
        <ul>
            <li>Send personalized re-engagement email to 12 critical risk users</li>
            <li>Schedule customer success calls for 5 high-value at-risk accounts</li>
            <li>Deploy feature discovery notifications to 34 low-adoption users</li>
        </ul>
        <p><strong>Weekly Actions:</strong></p>
        <ul>
            <li>Launch win-back campaign for 89 users inactive 7-14 days</li>
            <li>Provide additional onboarding support to 23 new struggling users</li>
            <li>Offer feature training to 45 users showing usage decline</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # ROI Calculator
    st.subheader("💰 Intervention ROI Calculator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Calculate Intervention Value:**")
        
        avg_user_value = st.number_input("Average User Lifetime Value ($)", value=450)
        users_at_risk = st.number_input("Users at Risk", value=89)
        intervention_cost = st.number_input("Intervention Cost per User ($)", value=25)
        expected_success_rate = st.slider("Expected Success Rate (%)", 0, 100, 65)
    
    with col2:
        # Calculate ROI
        total_at_risk_value = avg_user_value * users_at_risk
        intervention_total_cost = intervention_cost * users_at_risk
        users_saved = users_at_risk * (expected_success_rate / 100)
        value_saved = users_saved * avg_user_value
        roi = ((value_saved - intervention_total_cost) / intervention_total_cost) * 100
        
        st.markdown("**ROI Analysis:**")
        st.metric("Value at Risk", f"${total_at_risk_value:,.0f}")
        st.metric("Intervention Cost", f"${intervention_total_cost:,.0f}")
        st.metric("Expected Value Saved", f"${value_saved:,.0f}")
        st.metric("ROI", f"{roi:.0f}%", delta=f"${value_saved - intervention_total_cost:,.0f} net")

def show_feature_usage_analytics(ui: UserEngagementUI):
    """Feature usage analytics and optimization"""
    st.header("🛠️ Feature Usage Analytics")
    
    # Feature usage overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Features", "24", delta="2 new")
    with col2:
        st.metric("Avg Features/User", "5.7", delta="+0.8")  
    with col3:
        st.metric("Feature Adoption Rate", "68%", delta="+12%")
    with col4:
        st.metric("Underutilized Features", "6", delta="-2", delta_color="inverse")
    
    st.divider()
    
    # Feature popularity analysis
    st.subheader("📊 Feature Popularity Analysis")
    
    feature_data = {
        'Feature': ['Transcription', 'Search', 'Export', 'Analytics Dashboard', 'Collaboration', 
                   'API Access', 'Advanced Filters', 'Templates', 'Integrations', 'Mobile Sync'],
        'Daily_Active_Users': [1245, 892, 734, 567, 234, 189, 156, 134, 98, 67],
        'Adoption_Rate': [0.87, 0.62, 0.51, 0.39, 0.16, 0.13, 0.11, 0.09, 0.07, 0.05],
        'User_Satisfaction': [4.6, 4.3, 4.1, 4.4, 3.9, 4.2, 3.7, 4.0, 3.8, 3.6]
    }
    
    feature_df = pd.DataFrame(feature_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Feature usage ranking
        fig = px.bar(
            feature_df.sort_values('Daily_Active_Users', ascending=True),
            x='Daily_Active_Users',
            y='Feature',
            orientation='h',
            color='Daily_Active_Users',
            title="Feature Usage Ranking (Daily Active Users)",
            color_continuous_scale='viridis'
        )
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Adoption vs Satisfaction scatter
        fig = px.scatter(
            feature_df,
            x='Adoption_Rate',
            y='User_Satisfaction',
            size='Daily_Active_Users',
            hover_name='Feature',
            title="Feature Adoption vs User Satisfaction",
            labels={
                'Adoption_Rate': 'Adoption Rate',
                'User_Satisfaction': 'User Satisfaction (1-5)'
            },
            color='Daily_Active_Users',
            color_continuous_scale='plasma'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Feature journey analysis
    st.subheader("🗺️ Feature Discovery Journey")
    
    # Feature adoption funnel
    funnel_stages = ['Feature Awareness', 'First Trial', 'Regular Usage', 'Power User', 'Advocate']
    funnel_values = [1000, 650, 420, 280, 150]
    
    fig = go.Figure(go.Funnel(
        y = funnel_stages,
        x = funnel_values,
        textinfo = "value+percent initial",
        marker = dict(color = ["lightblue", "orange", "lightgreen", "red", "gold"])
    ))
    fig.update_layout(title="Feature Adoption Funnel", height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Feature usage patterns
    st.subheader("📈 Usage Patterns & Trends")
    
    # Time-based feature usage
    dates = pd.date_range('2024-01-01', periods=30, freq='D')
    top_features = ['Transcription', 'Search', 'Export', 'Analytics']
    
    fig = go.Figure()
    
    colors = ['blue', 'red', 'green', 'orange']
    for i, feature in enumerate(top_features):
        # Generate realistic usage patterns
        base_usage = np.random.randint(100, 300)
        trend = np.random.uniform(-0.02, 0.05)  
        noise = np.random.normal(0, 10, len(dates))
        
        usage = base_usage * (1 + trend * np.arange(len(dates))) + noise
        usage = np.maximum(usage, 0)  # Ensure non-negative
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=usage,
            mode='lines+markers',
            name=feature,
            line=dict(color=colors[i], width=3)
        ))
    
    fig.update_layout(
        title="Feature Usage Trends (30 Days)",
        xaxis_title="Date",
        yaxis_title="Daily Active Users",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Feature optimization recommendations
    st.subheader("💡 Feature Optimization Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚀 High-Potential Features")
        
        high_potential = [
            {
                'feature': 'Advanced Analytics',
                'insight': 'High satisfaction (4.4/5) but low adoption (39%)',
                'recommendation': 'Improve feature discoverability and onboarding'
            },
            {
                'feature': 'API Access', 
                'insight': 'Growing usage among power users (+23% this month)',
                'recommendation': 'Create developer documentation and tutorials'
            },
            {
                'feature': 'Collaboration',
                'insight': 'Teams using this feature have 40% higher retention',
                'recommendation': 'Promote team collaboration features in enterprise sales'
            }
        ]
        
        for feature in high_potential:
            st.markdown(f"""
            <div class="insight-card">
                <h5>🎯 {feature['feature']}</h5>
                <p><strong>Insight:</strong> {feature['insight']}</p>
                <p><strong>Action:</strong> {feature['recommendation']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### ⚠️ Underperforming Features")
        
        underperforming = [
            {
                'feature': 'Mobile Sync',
                'insight': 'Lowest adoption rate (5%) and satisfaction (3.6/5)',
                'recommendation': 'Major UX overhaul or consider sunsetting'
            },
            {
                'feature': 'Advanced Filters',
                'insight': 'Users find it too complex - 78% abandon on first try',
                'recommendation': 'Simplify interface and add guided tutorials'
            },
            {
                'feature': 'Templates',
                'insight': 'Good satisfaction but hidden in navigation',
                'recommendation': 'Improve feature placement and visibility'
            }
        ]
        
        for feature in underperforming:
            st.markdown(f"""
            <div class="recommendation-card">
                <h5>⚠️ {feature['feature']}</h5>
                <p><strong>Issue:</strong> {feature['insight']}</p>
                <p><strong>Action:</strong> {feature['recommendation']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Feature matrix analysis
    st.subheader("📊 Feature Performance Matrix")
    
    # Create performance matrix
    fig = px.scatter(
        feature_df,
        x='Adoption_Rate',
        y='User_Satisfaction', 
        size='Daily_Active_Users',
        color='Daily_Active_Users',
        hover_name='Feature',
        title="Feature Performance Matrix: Adoption vs Satisfaction",
        labels={
            'Adoption_Rate': 'Adoption Rate →',
            'User_Satisfaction': 'User Satisfaction →'
        },
        color_continuous_scale='viridis'
    )
    
    # Add quadrant lines
    fig.add_hline(y=4.0, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=0.3, line_dash="dash", line_color="gray", opacity=0.5)
    
    # Add quadrant labels
    fig.add_annotation(x=0.1, y=4.5, text="Hidden Gems", showarrow=False, bgcolor="lightgreen", opacity=0.7)
    fig.add_annotation(x=0.7, y=4.5, text="Star Features", showarrow=False, bgcolor="gold", opacity=0.7)
    fig.add_annotation(x=0.1, y=3.5, text="Questionable", showarrow=False, bgcolor="lightcoral", opacity=0.7)
    fig.add_annotation(x=0.7, y=3.5, text="Cash Cows", showarrow=False, bgcolor="lightblue", opacity=0.7)
    
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    # Feature roadmap insights
    st.subheader("🗓️ Feature Roadmap Insights")
    
    st.markdown("""
    <div class="insight-card">
        <h4>🎯 Strategic Recommendations for Next Quarter</h4>
        
        <h5>🚀 Immediate Actions (Next 30 days):</h5>
        <ul>
            <li><strong>Analytics Dashboard:</strong> Add onboarding tutorial - potential to reach 60% adoption</li>
            <li><strong>Collaboration:</strong> Promote in team plans - could boost enterprise retention by 25%</li>
            <li><strong>Advanced Filters:</strong> Simplify UX based on user feedback</li>
        </ul>
        
        <h5>📈 Medium-term Goals (Next 90 days):</h5>
        <ul>
            <li><strong>API Access:</strong> Launch developer portal and documentation</li>
            <li><strong>Mobile Sync:</strong> Complete redesign or sunset analysis</li>
            <li><strong>New Feature Development:</strong> Focus on high-satisfaction, high-adoption potential</li>
        </ul>
        
        <h5>💡 Innovation Opportunities:</h5>
        <ul>
            <li><strong>AI-Powered Insights:</strong> 89% of power users requested advanced AI features</li>
            <li><strong>Workflow Automation:</strong> High demand from enterprise customers</li>
            <li><strong>Real-time Collaboration:</strong> Competitor analysis shows market gap</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()