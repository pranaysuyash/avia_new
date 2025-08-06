#!/usr/bin/env python3
"""
Conversational Query Bot UI
Streamlit interface for the conversational query bot system
"""

import streamlit as st
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from conversational_query_bot import (
    ConversationalQueryBot, MediaContent, QueryResult, ConversationContext
)

# Page configuration
st.set_page_config(
    page_title="Conversational Query Bot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .query-box {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    
    .result-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e9ecef;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .relevance-score {
        background: #28a745;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .timestamp-badge {
        background: #17a2b8;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
    }
    
    .speaker-badge {
        background: #6f42c1;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
    }
    
    .content-type-badge {
        background: #fd7e14;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'bot' not in st.session_state:
        st.session_state.bot = ConversationalQueryBot()
    
    if 'conversation_id' not in st.session_state:
        st.session_state.conversation_id = str(uuid.uuid4())
    
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    if 'current_results' not in st.session_state:
        st.session_state.current_results = []

def render_header():
    """Render the main header"""
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Conversational Query Bot</h1>
        <p>Natural language querying of your media library with RAG technology</p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render the sidebar with controls and statistics"""
    st.sidebar.header("🎛️ Controls")
    
    # Conversation management
    st.sidebar.subheader("💬 Conversation")
    if st.sidebar.button("🔄 New Conversation"):
        st.session_state.conversation_id = str(uuid.uuid4())
        st.session_state.query_history = []
        st.session_state.current_results = []
        st.rerun()
    
    st.sidebar.text(f"ID: {st.session_state.conversation_id[:8]}...")
    
    # Content management
    st.sidebar.subheader("📚 Content Library")
    
    # Add new content
    with st.sidebar.expander("➕ Add Content"):
        content_title = st.text_input("Title")
        content_type = st.selectbox("Type", ["transcript", "document", "image_text", "video"])
        content_text = st.text_area("Content Text")
        
        col1, col2 = st.columns(2)
        with col1:
            timestamp = st.number_input("Timestamp (s)", min_value=0.0, value=0.0)
        with col2:
            speaker = st.text_input("Speaker")
        
        if st.button("Add Content"):
            if content_title and content_text:
                content = MediaContent(
                    id=str(uuid.uuid4()),
                    title=content_title,
                    content_type=content_type,
                    text_content=content_text,
                    timestamp=timestamp if timestamp > 0 else None,
                    speaker=speaker if speaker else None
                )
                
                if st.session_state.bot.add_content(content):
                    st.success("Content added successfully!")
                    st.rerun()
                else:
                    st.error("Failed to add content")
    
    # System statistics
    st.sidebar.subheader("📊 Statistics")
    stats = st.session_state.bot.get_statistics()
    
    if stats:
        st.sidebar.metric("Total Queries", stats.get('total_queries', 0))
        st.sidebar.metric("Active Conversations", stats.get('active_conversations', 0))
        
        avg_time = stats.get('average_processing_time', 0)
        st.sidebar.metric("Avg Processing Time", f"{avg_time:.3f}s")
        
        # Content type distribution
        content_stats = stats.get('content_statistics', {})
        if content_stats:
            st.sidebar.write("**Content Types:**")
            for content_type, count in content_stats.items():
                st.sidebar.write(f"• {content_type}: {count}")

def render_query_interface():
    """Render the main query interface"""
    st.header("🔍 Query Your Media Library")
    
    # Query input
    col1, col2 = st.columns([4, 1])
    
    with col1:
        query_text = st.text_input(
            "Ask a question about your media content:",
            placeholder="e.g., What did we discuss about the budget?",
            key="query_input"
        )
    
    with col2:
        st.write("")  # Spacing
        search_button = st.button("🔍 Search", type="primary")
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            max_results = st.slider("Max Results", 1, 20, 5)
            
        with col2:
            content_types = st.multiselect(
                "Filter by Content Type",
                ["transcript", "document", "image_text", "video"],
                default=[]
            )
    
    # Process query
    if search_button and query_text:
        with st.spinner("🔍 Searching your media library..."):
            results = st.session_state.bot.query(
                query_text,
                conversation_id=st.session_state.conversation_id,
                max_results=max_results,
                content_types=content_types if content_types else None
            )
            
            st.session_state.current_results = results
            st.session_state.query_history.append({
                'query': query_text,
                'timestamp': datetime.now(),
                'results_count': len(results)
            })
    
    # Display results
    if st.session_state.current_results:
        render_query_results(st.session_state.current_results)
    
    # Display query history
    if st.session_state.query_history:
        render_query_history()

def render_query_results(results: List[QueryResult]):
    """Render query results"""
    st.header(f"📋 Results ({len(results)} found)")
    
    if not results:
        st.info("No results found for your query.")
        return
    
    # Generate AI answer
    answer = st.session_state.bot.generate_answer(
        st.session_state.query_history[-1]['query'] if st.session_state.query_history else "",
        results
    )
    
    st.subheader("🤖 AI Answer")
    st.markdown(f"""
    <div class="query-box">
        {answer}
    </div>
    """, unsafe_allow_html=True)
    
    # Individual results
    st.subheader("📄 Detailed Results")
    
    for i, result in enumerate(results, 1):
        with st.container():
            st.markdown(f"""
            <div class="result-card">
                <h4>#{i}. {result.content.title}</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Badges
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <span class="relevance-score">
                    Relevance: {result.relevance_score:.3f}
                </span>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <span class="content-type-badge">
                    {result.content.content_type}
                </span>
                """, unsafe_allow_html=True)
            
            with col3:
                if result.timestamp_citation:
                    st.markdown(f"""
                    <span class="timestamp-badge">
                        ⏰ {result.timestamp_citation}
                    </span>
                    """, unsafe_allow_html=True)
            
            with col4:
                if result.content.speaker:
                    st.markdown(f"""
                    <span class="speaker-badge">
                        👤 {result.content.speaker}
                    </span>
                    """, unsafe_allow_html=True)
            
            # Content preview
            st.write("**Preview:**")
            st.write(result.snippet)
            
            # Context window
            if result.context_window:
                with st.expander("📖 Full Context"):
                    st.write(result.context_window)
            
            # Metadata
            if result.content.metadata:
                with st.expander("ℹ️ Metadata"):
                    st.json(result.content.metadata)
            
            st.markdown("---")

def render_query_history():
    """Render query history"""
    with st.expander("📜 Query History"):
        for i, query_data in enumerate(reversed(st.session_state.query_history[-10:]), 1):
            st.write(f"**{i}.** {query_data['query']}")
            st.write(f"   ⏰ {query_data['timestamp'].strftime('%H:%M:%S')} | 📊 {query_data['results_count']} results")

def render_analytics_tab():
    """Render analytics and insights"""
    st.header("📊 Analytics & Insights")
    
    stats = st.session_state.bot.get_statistics()
    
    if not stats:
        st.info("No analytics data available yet.")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Queries", stats.get('total_queries', 0))
    
    with col2:
        st.metric("Active Conversations", stats.get('active_conversations', 0))
    
    with col3:
        avg_time = stats.get('average_processing_time', 0)
        st.metric("Avg Processing Time", f"{avg_time:.3f}s")
    
    with col4:
        vector_stats = stats.get('vector_database', {})
        st.metric("Total Documents", vector_stats.get('total_documents', 0))
    
    # Content distribution
    content_stats = stats.get('content_statistics', {})
    if content_stats:
        st.subheader("📚 Content Distribution")
        
        # Create pie chart
        df = pd.DataFrame(list(content_stats.items()), columns=['Content Type', 'Count'])
        fig = px.pie(df, values='Count', names='Content Type', title="Content Types Distribution")
        st.plotly_chart(fig, use_container_width=True)
    
    # Query history visualization
    if st.session_state.query_history:
        st.subheader("🔍 Query Activity")
        
        # Create timeline
        query_df = pd.DataFrame(st.session_state.query_history)
        query_df['hour'] = query_df['timestamp'].dt.hour
        
        hourly_queries = query_df.groupby('hour').size().reset_index(name='count')
        
        fig = px.bar(hourly_queries, x='hour', y='count', title="Queries by Hour")
        st.plotly_chart(fig, use_container_width=True)

def render_content_management_tab():
    """Render content management interface"""
    st.header("📚 Content Management")
    
    # Bulk content upload
    st.subheader("📤 Bulk Content Upload")
    
    uploaded_file = st.file_uploader(
        "Upload JSON file with content",
        type=['json'],
        help="Upload a JSON file containing an array of content objects"
    )
    
    if uploaded_file:
        try:
            content_data = json.load(uploaded_file)
            
            if isinstance(content_data, list):
                st.write(f"Found {len(content_data)} content items")
                
                if st.button("Import All Content"):
                    success_count = 0
                    
                    progress_bar = st.progress(0)
                    
                    for i, item in enumerate(content_data):
                        try:
                            content = MediaContent(
                                id=item.get('id', str(uuid.uuid4())),
                                title=item['title'],
                                content_type=item['content_type'],
                                text_content=item['text_content'],
                                timestamp=item.get('timestamp'),
                                speaker=item.get('speaker'),
                                file_path=item.get('file_path'),
                                metadata=item.get('metadata')
                            )
                            
                            if st.session_state.bot.add_content(content):
                                success_count += 1
                        
                        except Exception as e:
                            st.error(f"Failed to import item {i+1}: {e}")
                        
                        progress_bar.progress((i + 1) / len(content_data))
                    
                    st.success(f"Successfully imported {success_count}/{len(content_data)} items")
                    st.rerun()
            
            else:
                st.error("JSON file must contain an array of content objects")
        
        except Exception as e:
            st.error(f"Failed to parse JSON file: {e}")
    
    # Sample content generation
    st.subheader("🎯 Sample Content")
    
    if st.button("Generate Sample Content"):
        sample_contents = [
            {
                "id": "sample_001",
                "title": "Team Meeting - Project Kickoff",
                "content_type": "transcript",
                "text_content": "Welcome everyone to the project kickoff meeting. Today we'll discuss the timeline, budget allocation, and team responsibilities. Sarah will lead the development team, while Mike handles the marketing strategy.",
                "timestamp": 30.0,
                "speaker": "John"
            },
            {
                "id": "sample_002",
                "title": "Product Requirements Document",
                "content_type": "document",
                "text_content": "The new feature should include real-time collaboration, advanced search capabilities, and integration with third-party APIs. The system must support up to 1000 concurrent users and maintain 99.9% uptime.",
                "metadata": {"version": "1.0", "author": "Product Team"}
            },
            {
                "id": "sample_003",
                "title": "Customer Interview",
                "content_type": "transcript",
                "text_content": "The customer expressed satisfaction with the current features but requested better mobile support and faster loading times. They mentioned that the search functionality could be more intuitive.",
                "timestamp": 120.5,
                "speaker": "Customer"
            }
        ]
        
        success_count = 0
        for item in sample_contents:
            content = MediaContent(**item)
            if st.session_state.bot.add_content(content):
                success_count += 1
        
        st.success(f"Generated {success_count} sample content items")
        st.rerun()

def main():
    """Main application function"""
    initialize_session_state()
    render_header()
    render_sidebar()
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["🔍 Query", "📊 Analytics", "📚 Content"])
    
    with tab1:
        render_query_interface()
    
    with tab2:
        render_analytics_tab()
    
    with tab3:
        render_content_management_tab()

if __name__ == "__main__":
    main()