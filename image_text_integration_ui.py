#!/usr/bin/env python3
"""
Image-to-Text Workflow Integration UI
Streamlit interface for unified media processing and search
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import tempfile
import os
from typing import List, Dict, Any

from image_text_integration import (
    ImageTextIntegrationPipeline,
    CrossModalRecommendationEngine,
    WorkflowResult
)

# Page configuration
st.set_page_config(
    page_title="Unified Media Processing Hub",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        height: 100%;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #667eea;
    }
    
    .metric-label {
        color: #6c757d;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    
    .process-step {
        background: #e3f2fd;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
        margin: 0.25rem;
        font-size: 0.85rem;
    }
    
    .entity-tag {
        background: #fff3cd;
        color: #856404;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        display: inline-block;
        margin: 0.25rem;
        font-size: 0.85rem;
    }
    
    .search-result {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        transition: all 0.3s;
    }
    
    .search-result:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }
    
    .recommendation-card {
        background: #f0f7ff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin-bottom: 0.5rem;
    }
    
    .source-badge {
        background: #28a745;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        margin-right: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'pipeline' not in st.session_state:
    st.session_state.pipeline = ImageTextIntegrationPipeline()
    st.session_state.recommendation_engine = CrossModalRecommendationEngine(st.session_state.pipeline)

if 'processed_results' not in st.session_state:
    st.session_state.processed_results = []

if 'search_history' not in st.session_state:
    st.session_state.search_history = []

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🔄 Unified Media Processing Hub</h1>
        <p>Integrate text extraction from images, documents, audio, and video into a unified search experience</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("🎯 Navigation")
        page = st.radio(
            "Select Function",
            ["Process Media", "Search Content", "Analytics", "Recommendations", "Export Data"]
        )
    
    # Main content
    if page == "Process Media":
        render_process_media()
    elif page == "Search Content":
        render_search_content()
    elif page == "Analytics":
        render_analytics()
    elif page == "Recommendations":
        render_recommendations()
    elif page == "Export Data":
        render_export_data()

def render_process_media():
    """Render media processing interface"""
    st.header("📤 Process Media Files")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # File upload
        uploaded_file = st.file_uploader(
            "Choose a file to process",
            type=['jpg', 'jpeg', 'png', 'pdf', 'mp3', 'wav', 'm4a', 'mp4', 'avi', 'mov'],
            help="Supports images, documents, audio, and video files"
        )
        
        if uploaded_file:
            # Save temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                tmp.write(uploaded_file.getvalue())
                temp_path = tmp.name
            
            # Process button
            if st.button("🚀 Process File", type="primary"):
                with st.spinner("Processing... This may take a moment"):
                    try:
                        # Process file
                        result = st.session_state.pipeline.process_media_file(temp_path)
                        st.session_state.processed_results.append(result)
                        
                        # Display results
                        render_workflow_result(result)
                        
                        # Success message
                        st.success(f"✅ Successfully processed {uploaded_file.name}")
                        
                    except Exception as e:
                        st.error(f"Error processing file: {str(e)}")
                    finally:
                        # Clean up
                        os.unlink(temp_path)
    
    with col2:
        # Processing info
        st.markdown("### 📋 Supported Formats")
        st.markdown("""
        **Images:** JPG, PNG, BMP  
        **Documents:** PDF, DOCX, TXT  
        **Audio:** MP3, WAV, M4A  
        **Video:** MP4, AVI, MOV
        """)
        
        st.markdown("### 🔍 What We Extract")
        st.markdown("""
        - Text from images (OCR)
        - Document structure
        - Audio transcriptions
        - Named entities
        - Keywords & summaries
        - Visual descriptions
        """)

def render_workflow_result(result: WorkflowResult):
    """Display workflow processing results"""
    st.markdown("### 📊 Processing Results")
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(result.text_sources)}</div>
            <div class="metric-label">Text Sources</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        total_entities = sum(len(v) for v in result.entities.values())
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_entities}</div>
            <div class="metric-label">Entities Found</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(result.keywords)}</div>
            <div class="metric-label">Keywords</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{result.processing_time:.1f}s</div>
            <div class="metric-label">Processing Time</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Processing steps
    st.markdown("### 🔄 Processing Steps")
    steps_html = " ".join([f'<span class="process-step">{step}</span>' for step in result.processing_steps])
    st.markdown(steps_html, unsafe_allow_html=True)
    
    # Text sources
    if result.text_sources:
        st.markdown("### 📝 Extracted Text")
        
        tabs = st.tabs(list(result.text_sources.keys()))
        for i, (source, text) in enumerate(result.text_sources.items()):
            with tabs[i]:
                st.text_area(f"{source.title()} Text", text, height=200)
    
    # Entities
    if result.entities:
        st.markdown("### 🏷️ Extracted Entities")
        
        for entity_type, entities in result.entities.items():
            if entities:
                st.markdown(f"**{entity_type}:**")
                entities_html = " ".join([f'<span class="entity-tag">{e}</span>' for e in entities])
                st.markdown(entities_html, unsafe_allow_html=True)
    
    # Summary
    if result.summary:
        st.markdown("### 📋 Summary")
        st.info(result.summary)
    
    # Similar content
    if result.similar_content:
        st.markdown("### 🔗 Similar Content")
        st.write(f"Found {len(result.similar_content)} similar items in the database")

def render_search_content():
    """Render content search interface"""
    st.header("🔍 Search Across All Media")
    
    # Search input
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input(
            "Search query",
            placeholder="Enter keywords, entities, or descriptions...",
            help="Search across all processed content"
        )
    
    with col2:
        media_types = st.multiselect(
            "Filter by type",
            ["image", "document", "audio", "video"],
            default=[]
        )
    
    if st.button("🔍 Search", type="primary"):
        if query:
            with st.spinner("Searching..."):
                # Perform search
                results = st.session_state.pipeline.search_across_media(
                    query,
                    media_types=media_types if media_types else None,
                    top_k=10
                )
                
                # Add to search history
                st.session_state.search_history.append({
                    'query': query,
                    'timestamp': datetime.now(),
                    'results_count': len(results)
                })
                
                # Display results
                if results:
                    st.markdown(f"### Found {len(results)} results")
                    
                    for result in results:
                        render_search_result(result)
                else:
                    st.info("No results found. Try different keywords or process more content.")
    
    # Search history
    if st.session_state.search_history:
        with st.expander("📜 Recent Searches"):
            for search in reversed(st.session_state.search_history[-5:]):
                st.write(f"**{search['query']}** - {search['results_count']} results - {search['timestamp'].strftime('%H:%M:%S')}")

def render_search_result(result: Dict[str, Any]):
    """Display a single search result"""
    st.markdown(f"""
    <div class="search-result">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span class="source-badge">{result['content_type'].upper()}</span>
                <strong>{os.path.basename(result['source_path'])}</strong>
            </div>
            <div style="color: #6c757d;">
                Score: {result['score']:.3f}
            </div>
        </div>
        <div style="margin-top: 0.5rem; color: #495057;">
            {result['text_preview']}
        </div>
        <div style="margin-top: 0.5rem;">
            <small style="color: #6c757d;">Created: {result['created_at']}</small>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_analytics():
    """Render analytics dashboard"""
    st.header("📊 Content Analytics")
    
    analytics = st.session_state.pipeline.get_content_analytics()
    
    if analytics['total_content'] == 0:
        st.info("No content processed yet. Upload and process some files to see analytics.")
        return
    
    # Overview metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Content", analytics['total_content'])
    
    with col2:
        st.metric("Total Entities", analytics['total_entities'])
    
    with col3:
        st.metric("Avg Entities/Content", f"{analytics['average_entities_per_content']:.1f}")
    
    # Content type distribution
    if analytics['content_by_type']:
        st.markdown("### 📈 Content Distribution")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart
            fig_pie = px.pie(
                values=list(analytics['content_by_type'].values()),
                names=list(analytics['content_by_type'].keys()),
                title="Content by Type"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Bar chart for text sources
            fig_bar = go.Figure(data=[
                go.Bar(
                    x=list(analytics['text_sources'].keys()),
                    y=list(analytics['text_sources'].values()),
                    marker_color=['#667eea', '#764ba2', '#f093fb', '#4facfe']
                )
            ])
            fig_bar.update_layout(
                title="Text Source Distribution",
                xaxis_title="Source Type",
                yaxis_title="Count"
            )
            st.plotly_chart(fig_bar, use_container_width=True)
    
    # Processing timeline
    if st.session_state.processed_results:
        st.markdown("### 📅 Processing Timeline")
        
        # Create timeline data
        timeline_data = []
        for result in st.session_state.processed_results:
            timeline_data.append({
                'Content': os.path.basename(result.original_path),
                'Type': result.content_type,
                'Processing Time': result.processing_time,
                'Entities': sum(len(v) for v in result.entities.values())
            })
        
        df_timeline = pd.DataFrame(timeline_data)
        
        # Line chart
        fig_timeline = px.line(
            df_timeline,
            x=df_timeline.index,
            y='Processing Time',
            markers=True,
            title="Processing Time Trend"
        )
        st.plotly_chart(fig_timeline, use_container_width=True)

def render_recommendations():
    """Render content recommendations"""
    st.header("🎯 Content Recommendations")
    
    if not st.session_state.pipeline.media_contents:
        st.info("Process some content first to see recommendations.")
        return
    
    # Select content
    content_ids = list(st.session_state.pipeline.media_contents.keys())
    content_options = {
        cid: f"{st.session_state.pipeline.media_contents[cid].content_type} - {os.path.basename(st.session_state.pipeline.media_contents[cid].source_path)}"
        for cid in content_ids
    }
    
    selected_id = st.selectbox(
        "Select content to get recommendations for:",
        options=list(content_options.keys()),
        format_func=lambda x: content_options[x]
    )
    
    if selected_id:
        col1, col2 = st.columns(2)
        
        with col1:
            cross_modal = st.checkbox("Prefer cross-modal recommendations", value=True)
        
        with col2:
            top_k = st.slider("Number of recommendations", 1, 10, 5)
        
        if st.button("🎯 Get Recommendations"):
            recommendations = st.session_state.recommendation_engine.get_recommendations(
                selected_id,
                cross_modal=cross_modal,
                top_k=top_k
            )
            
            if recommendations:
                st.markdown("### 📌 Recommended Content")
                
                for rec in recommendations:
                    st.markdown(f"""
                    <div class="recommendation-card">
                        <div style="font-weight: bold;">
                            {os.path.basename(rec['source_path'])}
                        </div>
                        <div style="color: #6c757d; font-size: 0.9rem;">
                            Type: {rec['content_type']} | {rec['reason']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No recommendations found. Process more diverse content for better recommendations.")

def render_export_data():
    """Render data export interface"""
    st.header("💾 Export Data")
    
    st.markdown("""
    Export your processed content and analysis results in various formats for further analysis
    or integration with other systems.
    """)
    
    if not st.session_state.pipeline.media_contents:
        st.info("No content to export. Process some files first.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📁 Unified Dataset")
        st.markdown("Export all processed content with extracted text, entities, and metadata.")
        
        if st.button("Export Unified Dataset", type="primary"):
            # Export to temporary file
            temp_path = tempfile.mktemp(suffix='.json')
            st.session_state.pipeline.export_unified_dataset(temp_path)
            
            # Read and offer download
            with open(temp_path, 'r') as f:
                data = f.read()
            
            st.download_button(
                label="📥 Download JSON Dataset",
                data=data,
                file_name=f"unified_dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
            # Clean up
            os.unlink(temp_path)
    
    with col2:
        st.markdown("### 📊 Analytics Report")
        st.markdown("Export analytics and insights from your processed content.")
        
        if st.button("Generate Analytics Report"):
            analytics = st.session_state.pipeline.get_content_analytics()
            
            # Create report
            report = f"""# Content Analytics Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview
- Total Content Processed: {analytics['total_content']}
- Total Entities Extracted: {analytics['total_entities']}
- Average Entities per Content: {analytics['average_entities_per_content']:.1f}

## Content Distribution
"""
            for content_type, count in analytics['content_by_type'].items():
                report += f"- {content_type.title()}: {count}\n"
            
            report += "\n## Text Sources\n"
            for source, count in analytics['text_sources'].items():
                report += f"- {source.title()}: {count}\n"
            
            st.download_button(
                label="📥 Download Report",
                data=report,
                file_name=f"analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )
    
    # Export search history
    if st.session_state.search_history:
        st.markdown("### 🔍 Search History")
        
        search_df = pd.DataFrame(st.session_state.search_history)
        csv = search_df.to_csv(index=False)
        
        st.download_button(
            label="📥 Download Search History",
            data=csv,
            file_name=f"search_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()