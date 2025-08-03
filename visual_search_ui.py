"""
Visual Search and Content Discovery UI Components
UI implementation for Task 38: Build visual search and content discovery
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import time
from PIL import Image
import io
import base64

from visual_search import (
    visual_search_engine, timeline_generator, ContentItem, SearchResult, ContentCluster
)


class VisualSearchUI:
    """UI components for visual search and content discovery"""
    
    def __init__(self):
        self.search_engine = visual_search_engine
        self.timeline_generator = timeline_generator
    
    def render_visual_search_interface(self):
        """Render the main visual search interface"""
        st.markdown("## 🔍 Visual Search & Content Discovery")
        
        # Create tabs for different search modes
        tab1, tab2, tab3, tab4 = st.tabs([
            "🔍 Text Search", 
            "🗺️ Content Map", 
            "📊 Timeline View", 
            "🎯 Clusters"
        ])
        
        with tab1:
            self._render_text_search()
        
        with tab2:
            self._render_content_map()
        
        with tab3:
            self._render_timeline_view()
        
        with tab4:
            self._render_cluster_view()
    
    def _render_text_search(self):
        """Render text-based visual search"""
        st.markdown("### 🔍 Semantic Text Search")
        
        # Search input
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input(
                "Search query",
                placeholder="Enter keywords or describe the content you're looking for...",
                help="Use natural language to describe what you're looking for"
            )
        
        with col2:
            search_button = st.button("🔍 Search", type="primary")
        
        # Search options
        with st.expander("🔧 Search Options"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                max_results = st.slider("Max Results", 5, 50, 10)
            
            with col2:
                similarity_threshold = st.slider("Similarity Threshold", 0.0, 1.0, 0.3)
            
            with col3:
                search_mode = st.selectbox(
                    "Search Mode",
                    ["Semantic", "Keyword", "Hybrid"],
                    help="Choose how to match your query"
                )
        
        # Perform search
        if search_button and search_query:
            with st.spinner("🔍 Searching content..."):
                results = self.search_engine.search_by_text(search_query, max_results)
                
                # Filter by similarity threshold
                filtered_results = [
                    r for r in results 
                    if r.similarity_score >= similarity_threshold
                ]
                
                self._display_search_results(filtered_results, search_query)
        
        # Show sample searches if no query
        if not search_query:
            self._render_sample_searches()
    
    def _render_content_map(self):
        """Render interactive content map"""
        st.markdown("### 🗺️ Interactive Content Map")
        
        if not self.search_engine.content_items:
            st.info("No content available. Add some transcripts to see the content map.")
            return
        
        # Map options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            reduction_method = st.selectbox(
                "Visualization Method",
                ["tsne", "pca", "umap"],
                help="Method for reducing dimensions"
            )
        
        with col2:
            color_by = st.selectbox(
                "Color By",
                ["Clusters", "Duration", "Timestamp", "None"],
                help="How to color the points"
            )
        
        with col3:
            show_labels = st.checkbox("Show Labels", value=True)
        
        # Generate map data
        with st.spinner("🗺️ Generating content map..."):
            map_data = self.search_engine.get_content_map_data(reduction_method)
            
            if map_data:
                self._render_interactive_map(map_data, color_by, show_labels)
            else:
                st.error("Failed to generate content map")
    
    def _render_timeline_view(self):
        """Render timeline visualization"""
        st.markdown("### 📊 Content Timeline")
        
        if not self.search_engine.content_items:
            st.info("No content available. Add some transcripts to see the timeline.")
            return
        
        # Timeline options
        col1, col2 = st.columns(2)
        
        with col1:
            time_granularity = st.selectbox(
                "Time Granularity",
                ["hour", "day", "week", "month"],
                index=1,
                help="How to group content by time"
            )
        
        with col2:
            metric = st.selectbox(
                "Metric",
                ["Content Count", "Total Duration", "Both"],
                help="What to show on the timeline"
            )
        
        # Generate timeline
        with st.spinner("📊 Generating timeline..."):
            timeline_data = self.timeline_generator.generate_timeline_data(time_granularity)
            
            if timeline_data:
                self._render_timeline_chart(timeline_data, metric)
            else:
                st.error("Failed to generate timeline")
        
        # Content density map
        st.markdown("#### 🌡️ Content Density Map")
        
        with st.spinner("🌡️ Generating density map..."):
            density_data = self.timeline_generator.generate_content_density_map()
            
            if density_data:
                self._render_density_map(density_data)
    
    def _render_cluster_view(self):
        """Render content clusters"""
        st.markdown("### 🎯 Content Clusters")
        
        if not self.search_engine.content_items:
            st.info("No content available. Add some transcripts to see clusters.")
            return
        
        # Clustering options
        col1, col2 = st.columns(2)
        
        with col1:
            n_clusters = st.slider(
                "Number of Clusters",
                2, min(10, len(self.search_engine.content_items)),
                5,
                help="How many clusters to create"
            )
        
        with col2:
            cluster_button = st.button("🎯 Generate Clusters", type="primary")
        
        # Generate clusters
        if cluster_button or 'clusters_generated' not in st.session_state:
            with st.spinner("🎯 Generating clusters..."):
                clusters = self.search_engine.get_content_clusters(n_clusters)
                st.session_state.clusters_generated = True
                st.session_state.current_clusters = clusters
        
        # Display clusters
        if 'current_clusters' in st.session_state:
            self._display_clusters(st.session_state.current_clusters)
    
    def _display_search_results(self, results: List[SearchResult], query: str):
        """Display search results"""
        if not results:
            st.warning(f"No results found for '{query}'")
            return
        
        st.success(f"Found {len(results)} results for '{query}'")
        
        # Results display options
        col1, col2 = st.columns(2)
        
        with col1:
            view_mode = st.radio(
                "View Mode",
                ["List", "Grid", "Detailed"],
                horizontal=True
            )
        
        with col2:
            sort_by = st.selectbox(
                "Sort By",
                ["Relevance", "Date", "Duration", "Title"]
            )
        
        # Sort results
        if sort_by == "Relevance":
            sorted_results = sorted(results, key=lambda x: x.similarity_score, reverse=True)
        elif sort_by == "Date":
            sorted_results = sorted(results, key=lambda x: x.content_item.timestamp, reverse=True)
        elif sort_by == "Duration":
            sorted_results = sorted(results, key=lambda x: x.content_item.duration, reverse=True)
        else:  # Title
            sorted_results = sorted(results, key=lambda x: x.content_item.title)
        
        # Display results based on view mode
        if view_mode == "List":
            self._display_results_list(sorted_results)
        elif view_mode == "Grid":
            self._display_results_grid(sorted_results)
        else:  # Detailed
            self._display_results_detailed(sorted_results)
    
    def _display_results_list(self, results: List[SearchResult]):
        """Display results in list format"""
        for i, result in enumerate(results):
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{result.content_item.title}**")
                    st.caption(result.relevance_explanation)
                    
                    # Show snippet
                    snippet = result.content_item.transcript[:150] + "..."
                    st.text(snippet)
                
                with col2:
                    st.metric("Similarity", f"{result.similarity_score:.2%}")
                    st.caption(f"Duration: {result.content_item.duration:.1f}s")
                
                with col3:
                    if st.button(f"View Details", key=f"view_{i}"):
                        self._show_content_details(result.content_item)
                    
                    if st.button(f"Find Similar", key=f"similar_{i}"):
                        self._find_similar_content(result.content_item)
                
                st.divider()
    
    def _display_results_grid(self, results: List[SearchResult]):
        """Display results in grid format"""
        cols_per_row = 3
        
        for i in range(0, len(results), cols_per_row):
            cols = st.columns(cols_per_row)
            
            for j, col in enumerate(cols):
                if i + j < len(results):
                    result = results[i + j]
                    
                    with col:
                        with st.container():
                            st.markdown(f"**{result.content_item.title}**")
                            st.progress(result.similarity_score)
                            st.caption(f"Similarity: {result.similarity_score:.2%}")
                            
                            # Thumbnail placeholder
                            st.image("https://via.placeholder.com/150x100?text=Audio", width=150)
                            
                            if st.button(f"View", key=f"grid_view_{i+j}"):
                                self._show_content_details(result.content_item)
    
    def _display_results_detailed(self, results: List[SearchResult]):
        """Display results in detailed format"""
        for i, result in enumerate(results):
            with st.expander(f"📄 {result.content_item.title} (Similarity: {result.similarity_score:.2%})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("**Full Transcript:**")
                    st.text_area(
                        "",
                        value=result.content_item.transcript,
                        height=200,
                        key=f"transcript_{i}"
                    )
                
                with col2:
                    st.markdown("**Metadata:**")
                    st.json(result.content_item.metadata)
                    
                    st.markdown("**Actions:**")
                    if st.button(f"Find Similar Content", key=f"detailed_similar_{i}"):
                        self._find_similar_content(result.content_item)
    
    def _render_interactive_map(self, map_data: Dict[str, Any], color_by: str, show_labels: bool):
        """Render interactive content map"""
        # Create scatter plot
        fig = go.Figure()
        
        # Determine colors
        if color_by == "Clusters" and 'cluster_colors' in map_data:
            colors = map_data['cluster_colors']
            colorscale = 'viridis'
        elif color_by == "Duration":
            colors = map_data['durations']
            colorscale = 'blues'
        elif color_by == "Timestamp":
            colors = map_data['timestamps']
            colorscale = 'reds'
        else:
            colors = ['blue'] * len(map_data['x'])
            colorscale = None
        
        # Add scatter trace
        fig.add_trace(go.Scatter(
            x=map_data['x'],
            y=map_data['y'],
            mode='markers+text' if show_labels else 'markers',
            marker=dict(
                size=10,
                color=colors,
                colorscale=colorscale,
                showscale=True if colorscale else False,
                colorbar=dict(title=color_by) if colorscale else None
            ),
            text=map_data['titles'] if show_labels else None,
            textposition="top center",
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Duration: %{customdata[0]:.1f}s<br>"
                "Preview: %{customdata[1]}<br>"
                "<extra></extra>"
            ),
            customdata=list(zip(map_data['durations'], map_data['transcripts']))
        ))
        
        # Update layout
        fig.update_layout(
            title="Interactive Content Map",
            xaxis_title="Dimension 1",
            yaxis_title="Dimension 2",
            height=600,
            showlegend=False
        )
        
        # Display plot
        selected_points = st.plotly_chart(fig, use_container_width=True, key="content_map")
        
        # Handle point selection
        if selected_points and 'selection' in selected_points:
            st.info("Click on points to explore content!")
    
    def _render_timeline_chart(self, timeline_data: Dict[str, Any], metric: str):
        """Render timeline chart"""
        # Create subplot
        if metric == "Both":
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Content Count', 'Total Duration'),
                vertical_spacing=0.1
            )
            
            # Add content count
            fig.add_trace(
                go.Scatter(
                    x=timeline_data['dates'],
                    y=timeline_data['content_counts'],
                    mode='lines+markers',
                    name='Content Count',
                    line=dict(color='blue')
                ),
                row=1, col=1
            )
            
            # Add duration
            fig.add_trace(
                go.Scatter(
                    x=timeline_data['dates'],
                    y=timeline_data['total_durations'],
                    mode='lines+markers',
                    name='Total Duration (s)',
                    line=dict(color='red')
                ),
                row=2, col=1
            )
            
            fig.update_layout(height=600)
        else:
            fig = go.Figure()
            
            if metric == "Content Count":
                y_data = timeline_data['content_counts']
                y_title = "Number of Content Items"
            else:  # Total Duration
                y_data = timeline_data['total_durations']
                y_title = "Total Duration (seconds)"
            
            fig.add_trace(go.Scatter(
                x=timeline_data['dates'],
                y=y_data,
                mode='lines+markers',
                fill='tonexty',
                hovertemplate=(
                    "Date: %{x}<br>"
                    f"{y_title}: %{{y}}<br>"
                    "Sample Content: %{customdata}<br>"
                    "<extra></extra>"
                ),
                customdata=timeline_data['sample_titles']
            ))
            
            fig.update_layout(
                title=f"Content Timeline - {metric}",
                xaxis_title="Date",
                yaxis_title=y_title,
                height=400
            )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_density_map(self, density_data: Dict[str, Any]):
        """Render content density heatmap"""
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=density_data['x'],
            y=density_data['y'],
            mode='markers',
            marker=dict(
                size=15,
                color=density_data['densities'],
                colorscale='hot',
                showscale=True,
                colorbar=dict(title="Content Density")
            ),
            text=density_data['titles'],
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Density: %{marker.color}<br>"
                "<extra></extra>"
            )
        ))
        
        fig.update_layout(
            title="Content Density Map",
            xaxis_title="Dimension 1",
            yaxis_title="Dimension 2",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _display_clusters(self, clusters: List[ContentCluster]):
        """Display content clusters"""
        if not clusters:
            st.warning("No clusters generated")
            return
        
        st.success(f"Generated {len(clusters)} clusters")
        
        # Cluster overview
        cluster_sizes = [len(cluster.items) for cluster in clusters]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Clusters", len(clusters))
        
        with col2:
            st.metric("Avg Cluster Size", f"{np.mean(cluster_sizes):.1f}")
        
        with col3:
            st.metric("Largest Cluster", max(cluster_sizes))
        
        # Display each cluster
        for i, cluster in enumerate(clusters):
            with st.expander(f"🎯 {cluster.name} ({len(cluster.items)} items)"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("**Cluster Summary:**")
                    st.write(cluster.summary)
                    
                    st.markdown("**Main Topics:**")
                    st.write(", ".join(cluster.topics))
                    
                    st.markdown("**Content Items:**")
                    for item in cluster.items:
                        st.markdown(f"• **{item.title}** ({item.duration:.1f}s)")
                
                with col2:
                    # Cluster visualization
                    if len(cluster.items) > 1:
                        # Simple cluster visualization
                        item_names = [item.title[:20] + "..." if len(item.title) > 20 else item.title for item in cluster.items]
                        item_durations = [item.duration for item in cluster.items]
                        
                        fig = px.bar(
                            x=item_durations,
                            y=item_names,
                            orientation='h',
                            title=f"Cluster {i+1} Items"
                        )
                        fig.update_layout(height=300)
                        st.plotly_chart(fig, use_container_width=True)
    
    def _render_sample_searches(self):
        """Render sample search suggestions"""
        st.markdown("### 💡 Try These Sample Searches")
        
        sample_queries = [
            "meeting discussion",
            "technical presentation",
            "customer feedback",
            "project planning",
            "training session",
            "interview questions"
        ]
        
        cols = st.columns(3)
        
        for i, query in enumerate(sample_queries):
            with cols[i % 3]:
                if st.button(f"🔍 {query}", key=f"sample_{i}"):
                    st.session_state.sample_search_query = query
                    st.rerun()
        
        # Handle sample search
        if 'sample_search_query' in st.session_state:
            query = st.session_state.sample_search_query
            del st.session_state.sample_search_query
            
            with st.spinner(f"🔍 Searching for '{query}'..."):
                results = self.search_engine.search_by_text(query, 10)
                self._display_search_results(results, query)
    
    def _show_content_details(self, content_item: ContentItem):
        """Show detailed view of content item"""
        st.session_state.selected_content = content_item
        st.rerun()
    
    def _find_similar_content(self, content_item: ContentItem):
        """Find and display similar content"""
        with st.spinner("🔍 Finding similar content..."):
            similar_results = self.search_engine.search_by_content(content_item, 5)
            
            if similar_results:
                st.markdown(f"### 🔍 Content Similar to '{content_item.title}'")
                self._display_search_results(similar_results, f"Similar to: {content_item.title}")
            else:
                st.info("No similar content found")
    
    def render_content_upload_interface(self):
        """Render interface for adding content to search index"""
        st.markdown("### 📤 Add Content to Search Index")
        
        with st.expander("➕ Add New Content"):
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("Content Title")
                transcript = st.text_area("Transcript", height=200)
            
            with col2:
                duration = st.number_input("Duration (seconds)", min_value=0.0, value=0.0)
                file_path = st.text_input("File Path (optional)")
                
                # Additional metadata
                st.markdown("**Metadata:**")
                speaker = st.text_input("Speaker")
                category = st.selectbox("Category", ["Meeting", "Presentation", "Interview", "Training", "Other"])
                tags = st.text_input("Tags (comma-separated)")
            
            if st.button("➕ Add to Index"):
                if title and transcript:
                    metadata = {
                        'duration': duration,
                        'file_path': file_path,
                        'speaker': speaker,
                        'category': category,
                        'tags': [tag.strip() for tag in tags.split(',') if tag.strip()]
                    }
                    
                    content_item = self.search_engine.add_transcript(
                        transcript_id=f"content_{int(time.time())}",
                        title=title,
                        transcript=transcript,
                        metadata=metadata
                    )
                    
                    st.success(f"Added '{title}' to search index!")
                    st.rerun()
                else:
                    st.error("Please provide both title and transcript")
    
    def render_search_analytics(self):
        """Render search analytics and insights"""
        st.markdown("### 📊 Search Analytics")
        
        if not self.search_engine.content_items:
            st.info("No content available for analytics")
            return
        
        # Basic statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Content", len(self.search_engine.content_items))
        
        with col2:
            total_duration = sum(item.duration for item in self.search_engine.content_items)
            st.metric("Total Duration", f"{total_duration/3600:.1f}h")
        
        with col3:
            avg_duration = total_duration / len(self.search_engine.content_items)
            st.metric("Avg Duration", f"{avg_duration:.1f}s")
        
        with col4:
            total_words = sum(len(item.transcript.split()) for item in self.search_engine.content_items)
            st.metric("Total Words", f"{total_words:,}")
        
        # Content distribution
        st.markdown("#### 📈 Content Distribution")
        
        # By category
        categories = {}
        for item in self.search_engine.content_items:
            category = item.metadata.get('category', 'Unknown')
            categories[category] = categories.get(category, 0) + 1
        
        if categories:
            fig = px.pie(
                values=list(categories.values()),
                names=list(categories.keys()),
                title="Content by Category"
            )
            st.plotly_chart(fig, use_container_width=True)


# Global UI instance
visual_search_ui = VisualSearchUI()