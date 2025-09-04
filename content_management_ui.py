"""
Content Management System UI
Task 203: Advanced Content Management and Organization System
Interactive Streamlit dashboard for managing transcribed content
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from streamlit_intent_utils import (
    render_share_inline,
    render_share_block,
    log_ux_event,
    get_params,
    update_params,
    render_skeleton_list,
)

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from advanced_content_management_system import (
        ContentManagementSystem, ContentType, ContentStatus, 
        ContentQuality, AccessLevel
    )
except ImportError:
    # Mock for development
    class ContentManagementSystem:
        def __init__(self, *args, **kwargs):
            pass
        async def search_content(self, *args, **kwargs):
            return {"results": [], "total_count": 0}
        async def get_user_analytics(self, *args, **kwargs):
            return {"overview": {"total_content": 0}}
    
    class ContentType:
        AUDIO_TRANSCRIPTION = "audio_transcription"
        VIDEO_TRANSCRIPTION = "video_transcription"
        INTERVIEW = "interview"
        MEETING = "meeting"
        LECTURE = "lecture"
        PODCAST = "podcast"

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = "demo_user"
if 'cms' not in st.session_state:
    st.session_state.cms = ContentManagementSystem("sqlite:///content_management.db")

def main():
    st.set_page_config(
        page_title="Content Management System",
        page_icon="📁",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("📁 Advanced Content Management System")
    st.markdown("Organize, search, and analyze your transcribed content")
    try:
        render_share_inline("Shareable view link")
    except Exception:
        pass

    # Sidebar navigation
    with st.sidebar:
        st.header("Navigation")
        params = get_params()
        pages = [
            "Content Library",
            "Search & Filter", 
            "Collections",
            "Tags & Categories",
            "Analytics Dashboard",
            "Content Upload",
            "Quality Management",
            "Sharing & Collaboration"
        ]
        default_page = params.get('cms_page', pages[0])
        page = st.selectbox("Select Page", pages, index=(pages.index(default_page) if default_page in pages else 0))
        try:
            update_params({'cms_page': page})
        except Exception:
            pass
        
        st.markdown("---")
        try:
            render_share_block("Share CMS View")
        except Exception:
            pass
        if st.button("Reset View/Filters"):
            try:
                st.experimental_set_query_params()
            except Exception:
                pass
            try:
                log_ux_event("st_filters_cleared", {"scope": "content_management"})
            except Exception:
                pass
            st.rerun()
        
        st.markdown("---")
        st.markdown(f"**User:** {st.session_state.user_id}")
        st.markdown(f"**Current Time:** {datetime.now().strftime('%H:%M:%S')}")

    # Route to selected page
    if page == "Content Library":
        show_content_library()
    elif page == "Search & Filter":
        show_search_filter()
    elif page == "Collections":
        show_collections()
    elif page == "Tags & Categories":
        show_tags_categories()
    elif page == "Analytics Dashboard":
        show_analytics_dashboard()
    elif page == "Content Upload":
        show_content_upload()
    elif page == "Quality Management":
        show_quality_management()
    elif page == "Sharing & Collaboration":
        show_sharing_collaboration()

def show_content_library():
    """Main content library view"""
    st.header("📚 Content Library")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Content", "156", "↗️ 12")
    with col2:
        st.metric("This Week", "23", "↗️ 5")
    with col3:
        st.metric("Processing", "3", "↗️ 1")
    with col4:
        st.metric("Storage Used", "2.4 GB", "↗️ 0.3 GB")
    
    st.markdown("---")
    
    # Recent content
    st.subheader("📄 Recent Content")
    
    # Mock data for demonstration
    recent_content = [
        {
            "title": "Team Meeting - Product Roadmap",
            "type": "Meeting",
            "status": "Ready",
            "quality": "Good",
            "duration": "45:30",
            "created": "2025-08-07 14:30",
            "tags": ["meeting", "roadmap", "product"]
        },
        {
            "title": "Customer Interview - User Research",
            "type": "Interview",
            "status": "Ready",
            "quality": "Excellent",
            "duration": "32:15",
            "created": "2025-08-07 11:20",
            "tags": ["interview", "research", "customers"]
        },
        {
            "title": "Webinar - AI in Healthcare",
            "type": "Webinar",
            "status": "Processing",
            "quality": "Needs Review",
            "duration": "58:45",
            "created": "2025-08-07 09:15",
            "tags": ["webinar", "ai", "healthcare"]
        },
        {
            "title": "Sales Call - Enterprise Client",
            "type": "Call Recording",
            "status": "Ready",
            "quality": "Good",
            "duration": "28:10",
            "created": "2025-08-06 16:45",
            "tags": ["sales", "enterprise", "client"]
        }
    ]
    
    # Display content in a table
    df = pd.DataFrame(recent_content)
    
    # Style the dataframe
    def style_status(val):
        if val == "Ready":
            return "background-color: #d4edda; color: #155724;"
        elif val == "Processing":
            return "background-color: #fff3cd; color: #856404;"
        else:
            return "background-color: #f8d7da; color: #721c24;"
    
    styled_df = df.style.applymap(style_status, subset=['status'])
    st.dataframe(styled_df, use_container_width=True)
    
    # Action buttons
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🔍 View Details", key="view_details"):
            st.success("Feature: View detailed content information")
    with col2:
        if st.button("✏️ Edit Content", key="edit_content"):
            st.success("Feature: Edit content metadata and transcription")
    with col3:
        if st.button("🏷️ Manage Tags", key="manage_tags"):
            st.success("Feature: Add/remove tags from content")
    with col4:
        if st.button("📤 Share Content", key="share_content"):
            st.success("Feature: Share content with team members")

def show_search_filter():
    """Advanced search and filtering interface"""
    st.header("🔍 Search & Filter Content")
    
    # Search form
    with st.form("search_form"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            params = get_params()
            search_query = st.text_input(
                "Search Content",
                placeholder="Enter keywords, titles, or content text...",
                value=params.get('cms_q', '')
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
            search_submitted = st.form_submit_button("🔍 Search", use_container_width=True)
    try:
        update_params({'cms_q': search_query or None})
    except Exception:
        pass
    
    # Advanced filters
    with st.expander("🎛️ Advanced Filters", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Deep-linked content types (comma-separated key 'cms_types')
            types_default = [t for t in (params.get('cms_types', '') or '').split(',') if t]
            content_types = st.multiselect(
                "Content Types",
                ["Audio Transcription", "Video Transcription", "Meeting", "Interview", "Lecture", "Podcast", "Webinar"],
                default=types_default
            )
            try:
                update_params({'cms_types': ','.join(content_types) if content_types else None})
            except Exception:
                pass
            
            # Deep-linked date range as ISO pair in 'cms_date' => YYYY-MM-DD,YYYY-MM-DD
            from datetime import datetime as _dt
            _date_param = params.get('cms_date')
            _start_default, _end_default = None, None
            if _date_param and ',' in _date_param:
                try:
                    _s, _e = _date_param.split(',', 1)
                    _start_default = _dt.fromisoformat(_s).date()
                    _end_default = _dt.fromisoformat(_e).date()
                except Exception:
                    _start_default, _end_default = None, None
            date_range = st.date_input(
                "Date Range",
                value=[_start_default or datetime.now() - timedelta(days=30), _end_default or datetime.now()],
                help="Select start and end dates"
            )
            try:
                if isinstance(date_range, list) and len(date_range) == 2:
                    update_params({'cms_date': f"{date_range[0].isoformat()},{date_range[1].isoformat()}"})
            except Exception:
                pass
        
        with col2:
            quality_filter = st.selectbox(
                "Quality Level",
                ["All", "Excellent", "Good", "Fair", "Poor", "Needs Review"]
            )
            try:
                update_params({'cms_quality': quality_filter if quality_filter != 'All' else None})
            except Exception:
                pass
            
            # Deep-linked duration range in minutes as 'cms_dur' => min-max
            _dur_param = params.get('cms_dur')
            _dur_default = [0, 180]
            if _dur_param and '-' in _dur_param:
                try:
                    _a, _b = _dur_param.split('-', 1)
                    _dur_default = [max(0, int(_a)), min(180, int(_b))]
                except Exception:
                    _dur_default = [0, 180]
            duration_range = st.slider(
                "Duration (minutes)",
                min_value=0,
                max_value=180,
                value=_dur_default,
                help="Filter by content duration"
            )
            try:
                update_params({'cms_dur': f"{duration_range[0]}-{duration_range[1]}"})
            except Exception:
                pass
        
        with col3:
            # Deep-linked tags (comma-separated in 'cms_tags')
            tags_default = [t for t in (params.get('cms_tags', '') or '').split(',') if t]
            tags_filter = st.multiselect(
                "Tags",
                ["meeting", "interview", "sales", "product", "research", "ai", "healthcare", "customer"],
                default=tags_default
            )
            try:
                update_params({'cms_tags': ','.join(tags_filter) if tags_filter else None})
            except Exception:
                pass
            
            status_filter = st.selectbox(
                "Status",
                ["All", "Ready", "Processing", "Archived", "Private", "Public"]
            )
            try:
                update_params({'cms_status': status_filter if status_filter != 'All' else None})
            except Exception:
                pass
    
    # Search results
    st.markdown("---")
    st.subheader("📋 Search Results")
    
    if search_submitted or st.button("🔄 Refresh Results"):
        # Lightweight skeletons to indicate loading
        try:
            render_skeleton_list(items=3)
        except Exception:
            pass
        # Mock search results
        search_results = [
            {
                "title": "Team Meeting - Product Roadmap",
                "type": "Meeting",
                "quality": "Good",
                "duration": "45:30",
                "created": "2025-08-07 14:30",
                "summary": "Discussion about Q4 product roadmap priorities and resource allocation...",
                "tags": ["meeting", "roadmap", "product"],
                "relevance": 95
            },
            {
                "title": "Customer Interview - User Research",
                "type": "Interview", 
                "quality": "Excellent",
                "duration": "32:15",
                "created": "2025-08-07 11:20",
                "summary": "In-depth user research interview covering pain points and feature requests...",
                "tags": ["interview", "research", "customers"],
                "relevance": 87
            }
        ]
        
        if search_query:
            st.success(f"Found {len(search_results)} results for '{search_query}'")
        else:
            st.info(f"Showing {len(search_results)} recent content items")
        
        # Display search results
        for i, result in enumerate(search_results):
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{result['title']}**")
                    st.caption(f"{result['summary']}")
                    
                    # Tags
                    tag_html = " ".join([f'<span style="background-color: #007bff; color: white; padding: 2px 6px; border-radius: 3px; font-size: 12px; margin-right: 4px;">{tag}</span>' for tag in result['tags']])
                    st.markdown(tag_html, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"**Type:** {result['type']}")
                    st.markdown(f"**Quality:** {result['quality']}")
                    st.markdown(f"**Duration:** {result['duration']}")
                
                with col3:
                    st.markdown(f"**Created:** {result['created']}")
                    if search_query:
                        st.markdown(f"**Relevance:** {result['relevance']}%")
                    
                    if st.button(f"📄 View", key=f"view_{i}"):
                        st.success(f"Opening: {result['title']}")
                
                st.markdown("---")

def show_collections():
    """Collections management interface"""
    st.header("📦 Content Collections")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("My Collections")
    
    with col2:
        if st.button("➕ New Collection", use_container_width=True):
            st.session_state.show_new_collection_form = True
    
    # New collection form
    if st.session_state.get('show_new_collection_form', False):
        with st.form("new_collection_form"):
            st.subheader("📝 Create New Collection")
            
            col1, col2 = st.columns(2)
            with col1:
                collection_name = st.text_input("Collection Name", placeholder="Enter collection name")
                collection_description = st.text_area("Description", placeholder="Optional description")
            
            with col2:
                access_level = st.selectbox("Access Level", ["Private", "Team", "Organization", "Public"])
                cover_image = st.file_uploader("Cover Image", type=['png', 'jpg', 'jpeg'])
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("✅ Create Collection"):
                    st.success(f"Created collection: {collection_name}")
                    st.session_state.show_new_collection_form = False
                    st.rerun()
            with col2:
                if st.form_submit_button("❌ Cancel"):
                    st.session_state.show_new_collection_form = False
                    st.rerun()
    
    # Display collections
    collections = [
        {
            "name": "Customer Interviews",
            "description": "All customer research interviews and feedback sessions",
            "items": 23,
            "access": "Team",
            "created": "2025-08-01",
            "updated": "2025-08-07"
        },
        {
            "name": "Team Meetings",
            "description": "Weekly team meetings and planning sessions",
            "items": 16,
            "access": "Private",
            "created": "2025-07-15",
            "updated": "2025-08-06"
        },
        {
            "name": "Product Research",
            "description": "Market research, competitor analysis, and product insights",
            "items": 31,
            "access": "Organization",
            "created": "2025-07-01",
            "updated": "2025-08-05"
        }
    ]
    
    for collection in collections:
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.markdown(f"**📁 {collection['name']}**")
                st.caption(collection['description'])
            
            with col2:
                st.metric("Items", collection['items'])
                st.markdown(f"**Access:** {collection['access']}")
            
            with col3:
                st.markdown(f"**Created:** {collection['created']}")
                st.markdown(f"**Updated:** {collection['updated']}")
            
            with col4:
                if st.button("📂 Open", key=f"open_{collection['name']}"):
                    st.success(f"Opening collection: {collection['name']}")
                if st.button("⚙️ Settings", key=f"settings_{collection['name']}"):
                    st.success(f"Collection settings: {collection['name']}")
            
            st.markdown("---")

def show_tags_categories():
    """Tags and categories management"""
    st.header("🏷️ Tags & Categories")
    
    tab1, tab2 = st.tabs(["🏷️ Tags", "📂 Categories"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Manage Tags")
        
        with col2:
            if st.button("➕ New Tag", key="new_tag_btn"):
                st.session_state.show_new_tag_form = True
        
        # New tag form
        if st.session_state.get('show_new_tag_form', False):
            with st.form("new_tag_form"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    tag_name = st.text_input("Tag Name", placeholder="Enter tag name")
                
                with col2:
                    tag_color = st.color_picker("Tag Color", "#007bff")
                
                with col3:
                    tag_description = st.text_input("Description", placeholder="Optional description")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("✅ Create Tag"):
                        st.success(f"Created tag: {tag_name}")
                        st.session_state.show_new_tag_form = False
                        st.rerun()
                with col2:
                    if st.form_submit_button("❌ Cancel"):
                        st.session_state.show_new_tag_form = False
                        st.rerun()
        
        # Display tags
        tags_data = [
            {"name": "meeting", "usage": 45, "color": "#007bff", "created": "2025-07-01"},
            {"name": "interview", "usage": 32, "color": "#28a745", "created": "2025-07-05"},
            {"name": "sales", "usage": 28, "color": "#dc3545", "created": "2025-07-10"},
            {"name": "product", "usage": 24, "color": "#ffc107", "created": "2025-07-12"},
            {"name": "research", "usage": 19, "color": "#6f42c1", "created": "2025-07-15"},
            {"name": "customer", "usage": 16, "color": "#fd7e14", "created": "2025-07-18"}
        ]
        
        # Tags visualization
        tag_usage = [tag["usage"] for tag in tags_data]
        tag_names = [tag["name"] for tag in tags_data]
        
        fig = px.bar(
            x=tag_names,
            y=tag_usage,
            title="Tag Usage Statistics",
            labels={"x": "Tags", "y": "Usage Count"}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Tags table
        df_tags = pd.DataFrame(tags_data)
        st.dataframe(df_tags, use_container_width=True)
    
    with tab2:
        st.subheader("Content Categories")
        
        # Category hierarchy visualization
        categories_data = {
            "Business": {
                "Meetings": 45,
                "Presentations": 23,
                "Training": 12
            },
            "Research": {
                "Customer Interviews": 32,
                "Market Research": 18,
                "User Testing": 15
            },
            "Media": {
                "Podcasts": 28,
                "Webinars": 24,
                "Lectures": 16
            }
        }
        
        # Create treemap
        categories = []
        subcategories = []
        values = []
        
        for cat, subcats in categories_data.items():
            for subcat, value in subcats.items():
                categories.append(cat)
                subcategories.append(subcat)
                values.append(value)
        
        fig = go.Figure(go.Treemap(
            labels=subcategories,
            parents=categories,
            values=values,
            textinfo="label+value"
        ))
        fig.update_layout(title="Content Distribution by Category", height=500)
        st.plotly_chart(fig, use_container_width=True)

def show_analytics_dashboard():
    """Analytics and insights dashboard"""
    st.header("📊 Content Analytics")
    
    # Key metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Content", "156", "↗️ 12")
    with col2:
        st.metric("This Month", "47", "↗️ 8")
    with col3:
        st.metric("Average Quality", "4.2/5", "↗️ 0.3")
    with col4:
        st.metric("Total Duration", "48.5h", "↗️ 6.2h")
    with col5:
        st.metric("Storage Used", "2.4 GB", "↗️ 0.3 GB")
    
    st.markdown("---")
    
    # Charts row 1
    col1, col2 = st.columns(2)
    
    with col1:
        # Content creation trend
        dates = pd.date_range(start="2025-07-01", end="2025-08-07", freq="D")
        content_counts = np.random.poisson(2, len(dates))  # Mock data
        
        fig = px.line(
            x=dates,
            y=content_counts,
            title="📈 Content Creation Trend",
            labels={"x": "Date", "y": "Content Items Created"}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Content type distribution
        content_types = ["Meeting", "Interview", "Webinar", "Podcast", "Lecture", "Call"]
        type_counts = [45, 32, 28, 24, 16, 11]
        
        fig = px.pie(
            values=type_counts,
            names=content_types,
            title="📊 Content by Type"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Charts row 2
    col1, col2 = st.columns(2)
    
    with col1:
        # Quality distribution
        quality_levels = ["Excellent", "Good", "Fair", "Poor", "Needs Review"]
        quality_counts = [34, 67, 32, 15, 8]
        
        fig = px.bar(
            x=quality_levels,
            y=quality_counts,
            title="⭐ Content Quality Distribution",
            color=quality_counts,
            color_continuous_scale="RdYlGn"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Duration analysis
        duration_ranges = ["0-15min", "15-30min", "30-45min", "45-60min", "60min+"]
        duration_counts = [28, 45, 38, 25, 20]
        
        fig = px.bar(
            x=duration_ranges,
            y=duration_counts,
            title="⏱️ Content Duration Distribution",
            color=duration_counts,
            color_continuous_scale="viridis"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Insights section
    st.subheader("🔍 AI-Generated Insights")
    
    insights = [
        {
            "type": "trend",
            "title": "Content Creation Trending Up",
            "description": "You've created 35% more content this month compared to last month. Keep up the great work!",
            "priority": "medium",
            "icon": "📈"
        },
        {
            "type": "quality",
            "title": "Quality Improvement Opportunity",
            "description": "23 content items need quality review. Consider batch processing for efficiency.",
            "priority": "high",
            "icon": "⚠️"
        },
        {
            "type": "usage",
            "title": "Popular Content Types",
            "description": "Meetings and interviews are your most frequent content types. Consider creating templates.",
            "priority": "low",
            "icon": "💡"
        }
    ]
    
    for insight in insights:
        priority_color = {
            "high": "#dc3545",
            "medium": "#ffc107", 
            "low": "#28a745"
        }
        
        with st.container():
            st.markdown(
                f"""
                <div style="border-left: 4px solid {priority_color[insight['priority']]}; padding: 10px; margin: 10px 0; background-color: #f8f9fa;">
                    <h4>{insight['icon']} {insight['title']}</h4>
                    <p>{insight['description']}</p>
                    <small>Priority: {insight['priority'].title()}</small>
                </div>
                """,
                unsafe_allow_html=True
            )

def show_content_upload():
    """Content upload and processing interface"""
    st.header("📤 Upload Content")
    
    # Upload form
    with st.form("content_upload_form", clear_on_submit=True):
        st.subheader("📁 Add New Content")
        
        col1, col2 = st.columns(2)
        
        with col1:
            content_title = st.text_input("Content Title", placeholder="Enter descriptive title")
            content_type = st.selectbox(
                "Content Type",
                ["Audio Transcription", "Video Transcription", "Meeting", "Interview", "Lecture", "Podcast", "Webinar", "Call Recording"]
            )
            content_description = st.text_area("Description", placeholder="Optional description")
        
        with col2:
            access_level = st.selectbox("Access Level", ["Private", "Team", "Organization", "Public"])
            
            # File upload options
            upload_method = st.radio("Upload Method", ["File Upload", "Text Input", "URL Import"])
            
            if upload_method == "File Upload":
                uploaded_file = st.file_uploader(
                    "Choose file",
                    type=['mp3', 'wav', 'mp4', 'avi', 'txt'],
                    help="Supported formats: MP3, WAV, MP4, AVI, TXT"
                )
            elif upload_method == "Text Input":
                transcription_text = st.text_area(
                    "Transcription Text",
                    height=200,
                    placeholder="Paste or type your transcription here..."
                )
            else:  # URL Import
                content_url = st.text_input("Content URL", placeholder="https://example.com/content")
        
        # Advanced options
        with st.expander("🔧 Advanced Options"):
            col1, col2 = st.columns(2)
            
            with col1:
                auto_tags = st.checkbox("Auto-generate tags", value=True)
                auto_categories = st.checkbox("Auto-assign categories", value=True)
            
            with col2:
                quality_check = st.checkbox("Run quality analysis", value=True)
                ai_analysis = st.checkbox("Perform AI analysis", value=True)
        
        # Submit button
        if st.form_submit_button("🚀 Upload & Process", use_container_width=True):
            if content_title:
                # Simulate upload process
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                import time
                
                # Simulated upload steps
                steps = [
                    "Validating file...",
                    "Extracting content...", 
                    "Running transcription...",
                    "Analyzing quality...",
                    "Generating tags...",
                    "Creating content item..."
                ]
                
                for i, step in enumerate(steps):
                    status_text.text(step)
                    progress_bar.progress((i + 1) / len(steps))
                    time.sleep(0.5)
                
                st.success(f"✅ Successfully uploaded: {content_title}")
                st.balloons()
            else:
                st.error("Please provide a content title")
    
    st.markdown("---")
    
    # Recent uploads
    st.subheader("📋 Recent Uploads")
    
    recent_uploads = [
        {
            "title": "Team Standup - August 7",
            "status": "✅ Processed",
            "uploaded": "2 minutes ago",
            "type": "Meeting",
            "quality": "Good"
        },
        {
            "title": "Customer Feedback Session",
            "status": "🔄 Processing",
            "uploaded": "5 minutes ago", 
            "type": "Interview",
            "quality": "Analyzing..."
        },
        {
            "title": "Product Demo Recording",
            "status": "⏳ Queued",
            "uploaded": "8 minutes ago",
            "type": "Presentation", 
            "quality": "Pending"
        }
    ]
    
    for upload in recent_uploads:
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.markdown(f"**{upload['title']}**")
                st.caption(f"Type: {upload['type']}")
            
            with col2:
                st.markdown(f"**Status:** {upload['status']}")
                
            with col3:
                st.markdown(f"**Quality:** {upload['quality']}")
                
            with col4:
                st.markdown(f"**Uploaded:** {upload['uploaded']}")
                if upload['status'] == "✅ Processed":
                    if st.button("📄 View", key=f"view_upload_{upload['title']}"):
                        st.success(f"Opening: {upload['title']}")
            
            st.markdown("---")

def show_quality_management():
    """Content quality management interface"""
    st.header("⭐ Quality Management")
    
    # Quality overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Avg Quality Score", "4.2/5", "↗️ 0.3")
    with col2:
        st.metric("Needs Review", "8", "↘️ 3")
    with col3:
        st.metric("Poor Quality", "5", "↘️ 2")
    with col4:
        st.metric("Auto-Reviewed", "143", "↗️ 15")
    
    st.markdown("---")
    
    # Quality filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        quality_filter = st.selectbox(
            "Filter by Quality",
            ["All", "Needs Review", "Poor", "Fair", "Good", "Excellent"]
        )
    
    with col2:
        review_status = st.selectbox(
            "Review Status",
            ["All", "Pending Review", "Reviewed", "Auto-Reviewed"]
        )
    
    with col3:
        sort_by = st.selectbox(
            "Sort by",
            ["Quality Score", "Date Created", "Date Modified", "Title"]
        )
    
    # Content requiring attention
    st.subheader("⚠️ Content Requiring Attention")
    
    quality_issues = [
        {
            "title": "Sales Call - Tech Startup",
            "quality_score": 2.1,
            "issues": ["Poor audio quality", "Multiple speakers overlap", "Background noise"],
            "created": "2025-08-06",
            "duration": "25:30",
            "status": "Needs Review"
        },
        {
            "title": "Conference Call - Strategy Discussion",
            "quality_score": 2.8,
            "issues": ["Incomplete transcription", "Technical terms not recognized"],
            "created": "2025-08-05",
            "duration": "45:15",
            "status": "Needs Review"
        }
    ]
    
    for item in quality_issues:
        with st.container():
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f"**{item['title']}**")
                
                # Quality score with color coding
                score_color = "#dc3545" if item['quality_score'] < 3 else "#ffc107" if item['quality_score'] < 4 else "#28a745"
                st.markdown(f"**Quality Score:** <span style='color: {score_color}'>{item['quality_score']}/5.0</span>", unsafe_allow_html=True)
                
                # Issues list
                for issue in item['issues']:
                    st.markdown(f"• ⚠️ {issue}")
            
            with col2:
                st.markdown(f"**Duration:** {item['duration']}")
                st.markdown(f"**Created:** {item['created']}")
                st.markdown(f"**Status:** {item['status']}")
            
            with col3:
                if st.button("🔧 Fix Issues", key=f"fix_{item['title']}"):
                    st.success("Opening quality improvement tools...")
                if st.button("✅ Mark Reviewed", key=f"reviewed_{item['title']}"):
                    st.success("Marked as reviewed")
                if st.button("📄 View Content", key=f"view_quality_{item['title']}"):
                    st.success(f"Opening: {item['title']}")
            
            st.markdown("---")
    
    # Quality improvement tools
    st.subheader("🛠️ Quality Improvement Tools")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🎯 Auto-Enhancement**")
        if st.button("Run Batch Enhancement", use_container_width=True):
            st.success("Running automatic quality enhancement on selected content...")
    
    with col2:
        st.markdown("**📊 Bulk Analysis**")
        if st.button("Analyze All Pending", use_container_width=True):
            st.success("Starting bulk quality analysis...")
    
    with col3:
        st.markdown("**📈 Quality Reports**")
        if st.button("Generate Report", use_container_width=True):
            st.success("Generating quality improvement report...")

def show_sharing_collaboration():
    """Content sharing and collaboration interface"""
    st.header("🤝 Sharing & Collaboration")
    
    # Sharing overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Shared Items", "34", "↗️ 6")
    with col2:
        st.metric("Team Access", "12", "↗️ 2") 
    with col3:
        st.metric("Public Links", "5", "→ 0")
    with col4:
        st.metric("Collaborators", "8", "↗️ 1")
    
    st.markdown("---")
    
    # Share new content
    st.subheader("📤 Share Content")
    
    with st.form("share_content_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            content_to_share = st.selectbox(
                "Select Content to Share",
                ["Team Meeting - Product Roadmap", "Customer Interview - User Research", "Sales Call - Enterprise Client"]
            )
            
            share_with = st.text_input(
                "Share with (email or username)",
                placeholder="Enter email addresses separated by commas"
            )
        
        with col2:
            permissions = st.multiselect(
                "Permissions",
                ["View", "Comment", "Edit", "Share"],
                default=["View"]
            )
            
            expiry_date = st.date_input(
                "Access Expires",
                value=datetime.now() + timedelta(days=7),
                help="Leave blank for permanent access"
            )
        
        share_message = st.text_area(
            "Message (optional)",
            placeholder="Add a note for the recipients..."
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("📧 Share via Email", use_container_width=True):
                st.success(f"Shared '{content_to_share}' via email")
        with col2:
            if st.form_submit_button("🔗 Generate Link", use_container_width=True):
                st.success("Generated shareable link")
                st.code("https://cms.example.com/shared/abc123def456", language="text")
    
    st.markdown("---")
    
    # Active shares
    st.subheader("📋 Active Shares")
    
    active_shares = [
        {
            "content": "Team Meeting - Product Roadmap",
            "shared_with": "john@example.com, sarah@example.com",
            "permissions": ["View", "Comment"],
            "expires": "2025-08-14",
            "last_accessed": "2025-08-07 14:30",
            "status": "Active"
        },
        {
            "content": "Customer Interview - User Research", 
            "shared_with": "research-team",
            "permissions": ["View", "Edit"],
            "expires": "Never",
            "last_accessed": "2025-08-07 11:45",
            "status": "Active"
        },
        {
            "content": "Sales Presentation Q3",
            "shared_with": "Public Link",
            "permissions": ["View"],
            "expires": "2025-08-10",
            "last_accessed": "2025-08-07 09:20",
            "status": "Expiring Soon"
        }
    ]
    
    for share in active_shares:
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.markdown(f"**{share['content']}**")
                st.caption(f"Shared with: {share['shared_with']}")
            
            with col2:
                permissions_text = ", ".join(share['permissions'])
                st.markdown(f"**Permissions:** {permissions_text}")
                
            with col3:
                st.markdown(f"**Expires:** {share['expires']}")
                st.markdown(f"**Last Access:** {share['last_accessed']}")
                
            with col4:
                status_color = "#28a745" if share['status'] == "Active" else "#ffc107"
                st.markdown(f"**Status:** <span style='color: {status_color}'>{share['status']}</span>", unsafe_allow_html=True)
                
                if st.button("⚙️ Manage", key=f"manage_{share['content']}"):
                    st.success(f"Managing sharing for: {share['content']}")
                if st.button("🚫 Revoke", key=f"revoke_{share['content']}"):
                    st.warning(f"Revoked access to: {share['content']}")
            
            st.markdown("---")
    
    # Collaboration activity
    st.subheader("💬 Recent Collaboration Activity")
    
    activity_feed = [
        {
            "user": "Sarah Chen",
            "action": "commented on",
            "content": "Team Meeting - Product Roadmap",
            "timestamp": "2 minutes ago",
            "type": "comment"
        },
        {
            "user": "John Smith", 
            "action": "edited",
            "content": "Customer Interview - User Research",
            "timestamp": "15 minutes ago",
            "type": "edit"
        },
        {
            "user": "Mike Johnson",
            "action": "shared",
            "content": "Sales Presentation Q3",
            "timestamp": "1 hour ago",
            "type": "share"
        }
    ]
    
    for activity in activity_feed:
        activity_icon = {"comment": "💬", "edit": "✏️", "share": "📤"}.get(activity['type'], "📝")
        
        st.markdown(
            f"{activity_icon} **{activity['user']}** {activity['action']} *{activity['content']}* - {activity['timestamp']}"
        )

if __name__ == "__main__":
    main()
