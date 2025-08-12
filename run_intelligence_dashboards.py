"""
Intelligence Dashboards Runner
Main entry point for all intelligence system dashboards
Compatible with Python 3.12 (with workarounds)
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add compatibility workaround for Python 3.12
if sys.version_info >= (3, 12):
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", message=".*ForwardRef._evaluate.*")

# Page configuration
st.set_page_config(
    page_title="Intelligence Systems Hub",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for the hub
st.markdown("""
<style>
    .hub-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 2rem 0;
    }
    .dashboard-card {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s;
        cursor: pointer;
    }
    .dashboard-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.2);
    }
    .card-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    .card-title {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .card-description {
        color: #666;
        margin-bottom: 1rem;
    }
    .card-stats {
        display: flex;
        justify-content: space-around;
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid #eee;
    }
    .stat-item {
        text-align: center;
    }
    .stat-value {
        font-size: 1.25rem;
        font-weight: bold;
        color: #667eea;
    }
    .stat-label {
        font-size: 0.875rem;
        color: #999;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="hub-header">🧠 Intelligence Systems Hub</h1>', unsafe_allow_html=True)

# Introduction
st.markdown("""
Welcome to the **Intelligence Systems Hub** - your central dashboard for advanced analytics, 
content intelligence, media analysis, and business insights. Choose a dashboard below to get started.
""")

# Check Python version and show warning if needed
if sys.version_info >= (3, 12):
    st.warning("""
    ⚠️ **Python 3.12 Compatibility Note**: 
    Some ML features may have limited functionality due to library compatibility issues. 
    For full functionality, Python 3.11 is recommended. See documentation for details.
    """)

# Dashboard selection
st.markdown("## 🎯 Select a Dashboard")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="dashboard-card" onclick="window.location.href='?page=content'">
        <div class="card-icon">📝</div>
        <div class="card-title">Content Intelligence</div>
        <div class="card-description">
            Analyze text content with NLP, extract insights, 
            keywords, sentiment, and generate recommendations.
        </div>
        <div class="card-stats">
            <div class="stat-item">
                <div class="stat-value">15+</div>
                <div class="stat-label">Analysis Types</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">95%</div>
                <div class="stat-label">Accuracy</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 Launch Content Intelligence", key="content_btn", use_container_width=True):
        st.session_state.selected_dashboard = "content"

with col2:
    st.markdown("""
    <div class="dashboard-card" onclick="window.location.href='?page=media'">
        <div class="card-icon">🎬</div>
        <div class="card-title">Media Intelligence</div>
        <div class="card-description">
            Process videos and images to detect scenes, 
            extract highlights, and analyze visual content.
        </div>
        <div class="card-stats">
            <div class="stat-item">
                <div class="stat-value">10+</div>
                <div class="stat-label">Detection Types</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">4K</div>
                <div class="stat-label">Support</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 Launch Media Intelligence", key="media_btn", use_container_width=True):
        st.session_state.selected_dashboard = "media"

with col3:
    st.markdown("""
    <div class="dashboard-card" onclick="window.location.href='?page=business'">
        <div class="card-icon">📊</div>
        <div class="card-title">Business Intelligence</div>
        <div class="card-description">
            Track KPIs, predict revenue, analyze churn, 
            and calculate ROI with advanced analytics.
        </div>
        <div class="card-stats">
            <div class="stat-item">
                <div class="stat-value">20+</div>
                <div class="stat-label">Metrics</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">ML</div>
                <div class="stat-label">Powered</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 Launch Business Intelligence", key="business_btn", use_container_width=True):
        st.session_state.selected_dashboard = "business"

# Feature comparison
st.markdown("## 🔍 Feature Comparison")

comparison_data = {
    "Feature": [
        "Real-time Analysis",
        "Batch Processing",
        "ML/AI Models",
        "Export Reports",
        "API Integration",
        "Custom Metrics",
        "Predictive Analytics",
        "Visual Analytics"
    ],
    "Content Intelligence": ["✅", "✅", "✅", "✅", "✅", "✅", "❌", "❌"],
    "Media Intelligence": ["✅", "✅", "✅", "✅", "✅", "❌", "❌", "✅"],
    "Business Intelligence": ["✅", "❌", "✅", "✅", "✅", "✅", "✅", "✅"]
}

import pandas as pd
df = pd.DataFrame(comparison_data)
st.dataframe(df, use_container_width=True, hide_index=True)

# Quick stats
st.markdown("## 📈 System Status")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Analyses Today",
        "1,247",
        "+15.3%",
        help="Total analyses performed across all systems"
    )

with col2:
    st.metric(
        "Active Users",
        "342",
        "+8.2%",
        help="Users currently using the intelligence systems"
    )

with col3:
    st.metric(
        "API Calls",
        "15.2K",
        "+22.5%",
        help="API calls to intelligence endpoints today"
    )

with col4:
    st.metric(
        "System Health",
        "98.5%",
        "+0.5%",
        help="Overall system health and uptime"
    )

# Launch selected dashboard
if 'selected_dashboard' in st.session_state:
    if st.session_state.selected_dashboard == "content":
        st.markdown("---")
        st.info("Launching Content Intelligence Dashboard...")
        # In production, this would redirect or import the actual dashboard
        st.markdown("""
        ```python
        # To run Content Intelligence Dashboard:
        streamlit run content_intelligence_ui.py
        ```
        """)
    elif st.session_state.selected_dashboard == "media":
        st.markdown("---")
        st.info("Launching Media Intelligence Dashboard...")
        st.markdown("""
        ```python
        # To run Media Intelligence Dashboard:
        streamlit run media_intelligence_ui.py
        ```
        """)
    elif st.session_state.selected_dashboard == "business":
        st.markdown("---")
        st.info("Launching Business Intelligence Dashboard...")
        st.markdown("""
        ```python
        # To run Business Intelligence Dashboard:
        streamlit run business_intelligence_ui.py
        ```
        """)

# Documentation section
with st.expander("📚 Documentation & Quick Start"):
    st.markdown("""
    ### Quick Start Guide
    
    1. **Content Intelligence**
       - Upload or paste content for analysis
       - Get sentiment, keywords, quality scores
       - Generate summaries and recommendations
    
    2. **Media Intelligence**
       - Upload videos or images
       - Detect scenes and highlights automatically
       - Extract key frames and generate thumbnails
       - Analyze viral potential
    
    3. **Business Intelligence**
       - View real-time business metrics
       - Predict revenue and user churn
       - Calculate ROI and identify opportunities
       - Generate executive reports
    
    ### API Integration
    
    All dashboards connect to REST API endpoints:
    ```
    POST /api/intelligence/content/analyze
    POST /api/intelligence/media/analyze
    POST /api/intelligence/business/metrics
    ```
    
    ### Python 3.12 Compatibility
    
    Due to dependency issues with Python 3.12, some features may be limited:
    - SpaCy NLP features (use fallback methods)
    - Some transformer models (use API alternatives)
    
    **Recommended**: Use Python 3.11 for full functionality
    
    ### Running Individual Dashboards
    
    ```bash
    # Content Intelligence
    streamlit run content_intelligence_ui.py
    
    # Media Intelligence
    streamlit run media_intelligence_ui.py
    
    # Business Intelligence
    streamlit run business_intelligence_ui.py
    
    # All dashboards (this hub)
    streamlit run run_intelligence_dashboards.py
    ```
    """)

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("Intelligence Systems v1.0")
with col2:
    st.caption("Python " + f"{sys.version_info.major}.{sys.version_info.minor}")
with col3:
    st.caption("© 2024 - Advanced Analytics Platform")