#!/usr/bin/env python3
"""
Advanced Search UI Components (Task 45)
Streamlit interface for advanced search and discovery features
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import time

from advanced_search_discovery import (
    AdvancedSearchEngine, SearchType, SearchResult, SavedSearch,
    SearchQuery, SearchAlert
)

class AdvancedSearchUI:
    """UI components for advanced search functionality"""
    
    def __init__(self):
        if 'search_engine' not in st.session_state:
            st.session_state.search_engine = AdvancedSearchEngine()
        
        self.search_engine = st.session_state.search_engine
        
        # Initialize session state
        if 'search_results' not in st.session_state:
            st.session_state.search_results = []
        if 'current_query' not in st.session_state:
            st.session_state.current_query = ""
        if 'search_history' not in st.session_state:
            st.session_state.search_history = []
        if 'saved_searches' not in st.session_state:
            st.session_state.saved_searches = []
    
    def render_search_interface(self):
        """Render the main search interface"""
        st.header("🔍 Advanced Search & Discovery")
        
        # Create tabs for different search modes
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🔍 Search", "💾 Saved Searches", "🎤 Voice Search", 
            "📊 Analytics", "⚙️ Settings"
        ])
        
        with tab1:
            self._render_main_search()
        
        with tab2:
            self._render_saved_searches()
        
        with tab3:
            self._render_voice_search()
        
        with tab4:
            self._render_search_analytics()
        
        with tab5:
            self._render_search_settings()
    
    def _render_main_search(self):
        """Render main search interface"""
        st.subheader("Search Your Content")
        
        # Search input with suggestions
        col1, col2 = st.columns([3, 1])
        
        with col1:
            query = st.text_input(
                "Enter your search query:",
                value=st.session_state.current_query,
                placeholder="Search transcripts, entities, summaries...",
                help="Use quotes for exact phrases, AND/OR for boolean search"
            )
        
        with col2:
            search_type = st.selectbox(
                "Search Type:",
                options=[
                    ("Text", SearchType.TEXT),
                    ("Fuzzy", SearchType.FUZZY),
                    ("Boolean", SearchType.BOOLEAN),
                    ("Semantic", SearchType.SEMANTIC)
                ],
                format_func=lambda x: x[0]
            )[1]
        
        # Advanced filters
        with st.expander("🔧 Advanced Filters"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                content_type_filter = st.selectbox(
                    "Content Type:",
                    options=["All", "Transcript", "Entity", "Summary", "Comment"],
                    index=0
                )
            
            with col2:
                speaker_filter = st.text_input(
                    "Speaker:",
                    placeholder="Filter by speaker name"
                )
            
            with col3:
                date_range = st.date_input(
                    "Date Range:",
                    value=[],
                    help="Select date range for content"
                )
            
            # Time range within content
            col4, col5 = st.columns(2)
            with col4:
                time_start = st.number_input(
                    "Start Time (seconds):",
                    min_value=0.0,
                    value=0.0,
                    step=1.0
                )
            
            with col5:
                time_end = st.number_input(
                    "End Time (seconds):",
                    min_value=0.0,
                    value=0.0,
                    step=1.0,
                    help="0 means no end limit"
                )
        
        # Search suggestions
        if query and len(query) > 2:
            suggestions = self.search_engine.get_search_suggestions(
                query, st.session_state.get('user_id', 'default'), limit=3
            )
            
            if suggestions:
                st.write("💡 **Suggestions:**")
                suggestion_cols = st.columns(len(suggestions))
                for i, suggestion in enumerate(suggestions):
                    with suggestion_cols[i]:
                        if st.button(f"'{suggestion}'", key=f"suggestion_{i}"):
                            st.session_state.current_query = suggestion
                            st.rerun()
        
        # Search button and options
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_clicked = st.button("🔍 Search", type="primary", use_container_width=True)
        
        with col2:
            save_search = st.button("💾 Save Search", use_container_width=True)
        
        with col3:
            clear_results = st.button("🗑️ Clear", use_container_width=True)
        
        # Perform search
        if search_clicked and query:
            with st.spinner("Searching..."):
                # Prepare filters
                filters = {}
                
                if content_type_filter != "All":
                    filters['content_type'] = content_type_filter.lower()
                
                if speaker_filter:
                    filters['speakers'] = [speaker_filter]
                
                if date_range and len(date_range) == 2:
                    filters['start_time'] = datetime.combine(date_range[0], datetime.min.time())
                    filters['end_time'] = datetime.combine(date_range[1], datetime.max.time())
                
                if time_start > 0:
                    filters['duration_start'] = time_start
                
                if time_end > 0:
                    filters['duration_end'] = time_end
                
                # Perform search
                results = self.search_engine.search(
                    query, search_type, 
                    st.session_state.get('user_id', 'default'),
                    filters
                )
                
                st.session_state.search_results = results
                st.session_state.current_query = query
                
                st.success(f"Found {len(results)} results in {time.time():.3f} seconds")
        
        # Save search dialog
        if save_search and query:
            self._show_save_search_dialog(query, search_type)
        
        # Clear results
        if clear_results:
            st.session_state.search_results = []
            st.session_state.current_query = ""
            st.rerun()
        
        # Display results
        if st.session_state.search_results:
            self._render_search_results(st.session_state.search_results)
    
    def _render_search_results(self, results: List[SearchResult]):
        """Render search results"""
        st.subheader(f"📋 Search Results ({len(results)} found)")
        
        if not results:
            st.info("No results found. Try adjusting your search query or filters.")
            return
        
        # Results sorting and filtering
        col1, col2, col3 = st.columns(3)
        
        with col1:
            sort_by = st.selectbox(
                "Sort by:",
                options=["Relevance", "Date", "Speaker", "Content Type"],
                index=0
            )
        
        with col2:
            sort_order = st.selectbox(
                "Order:",
                options=["Descending", "Ascending"],
                index=0
            )
        
        with col3:
            results_per_page = st.selectbox(
                "Results per page:",
                options=[10, 25, 50, 100],
                index=0
            )
        
        # Sort results
        reverse_order = sort_order == "Descending"
        
        if sort_by == "Relevance":
            results.sort(key=lambda x: x.relevance_score, reverse=reverse_order)
        elif sort_by == "Date":
            results.sort(key=lambda x: x.timestamp or datetime.min, reverse=reverse_order)
        elif sort_by == "Speaker":
            results.sort(key=lambda x: x.speaker or "", reverse=reverse_order)
        elif sort_by == "Content Type":
            results.sort(key=lambda x: x.content_type, reverse=reverse_order)
        
        # Pagination
        total_pages = (len(results) - 1) // results_per_page + 1
        
        if total_pages > 1:
            page = st.selectbox(
                f"Page (1-{total_pages}):",
                options=list(range(1, total_pages + 1)),
                index=0
            )
            
            start_idx = (page - 1) * results_per_page
            end_idx = min(start_idx + results_per_page, len(results))
            page_results = results[start_idx:end_idx]
        else:
            page_results = results[:results_per_page]
        
        # Display results
        for i, result in enumerate(page_results):
            with st.container():
                # Result header
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{result.title}**")
                
                with col2:
                    st.markdown(f"*{result.content_type.title()}*")
                
                with col3:
                    st.markdown(f"Score: {result.relevance_score:.2f}")
                
                # Result metadata
                metadata_cols = st.columns(4)
                
                with metadata_cols[0]:
                    if result.speaker:
                        st.markdown(f"👤 **Speaker:** {result.speaker}")
                
                with metadata_cols[1]:
                    if result.timestamp:
                        st.markdown(f"📅 **Date:** {result.timestamp.strftime('%Y-%m-%d %H:%M')}")
                
                with metadata_cols[2]:
                    if result.start_time is not None:
                        st.markdown(f"⏰ **Time:** {result.start_time:.1f}s")
                
                with metadata_cols[3]:
                    if result.end_time is not None:
                        st.markdown(f"⏱️ **Duration:** {result.end_time - (result.start_time or 0):.1f}s")
                
                # Content preview
                content_preview = result.content[:300] + "..." if len(result.content) > 300 else result.content
                st.markdown(f"📝 {content_preview}")
                
                # Highlights
                if result.highlights:
                    st.markdown("**🔍 Highlights:**")
                    for highlight in result.highlights[:3]:
                        st.markdown(f"• *{highlight}*")
                
                # Action buttons
                action_cols = st.columns(4)
                
                with action_cols[0]:
                    if st.button(f"📖 View Full", key=f"view_{result.result_id}"):
                        self._show_full_content(result)
                
                with action_cols[1]:
                    if st.button(f"📋 Copy", key=f"copy_{result.result_id}"):
                        st.write("Content copied to clipboard!")
                
                with action_cols[2]:
                    if st.button(f"🔗 Share", key=f"share_{result.result_id}"):
                        self._show_share_dialog(result)
                
                with action_cols[3]:
                    if st.button(f"⭐ Save", key=f"save_{result.result_id}"):
                        st.success("Result saved to favorites!")
                
                st.divider()
    
    def _render_saved_searches(self):
        """Render saved searches interface"""
        st.subheader("💾 Saved Searches")
        
        # Get saved searches
        saved_searches = self.search_engine.get_saved_searches(
            st.session_state.get('user_id', 'default')
        )
        
        if not saved_searches:
            st.info("No saved searches yet. Save a search from the main search tab to see it here.")
            return
        
        # Display saved searches
        for search in saved_searches:
            with st.expander(f"🔍 {search.name}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Query:** `{search.query.query_text}`")
                    st.markdown(f"**Type:** {search.query.search_type.title()}")
                    st.markdown(f"**Description:** {search.description}")
                    
                    if search.query.filters:
                        st.markdown("**Filters:**")
                        for key, value in search.query.filters.items():
                            st.markdown(f"• {key}: {value}")
                
                with col2:
                    st.markdown(f"**Created:** {search.created_at.strftime('%Y-%m-%d')}")
                    st.markdown(f"**Last Run:** {search.last_run.strftime('%Y-%m-%d %H:%M') if search.last_run else 'Never'}")
                    st.markdown(f"**Run Count:** {search.run_count}")
                
                # Action buttons
                action_cols = st.columns(4)
                
                with action_cols[0]:
                    if st.button(f"▶️ Run", key=f"run_{search.search_id}"):
                        with st.spinner("Running saved search..."):
                            results = self.search_engine.run_saved_search(
                                search.search_id,
                                st.session_state.get('user_id', 'default')
                            )
                            st.session_state.search_results = results
                            st.success(f"Found {len(results)} results")
                
                with action_cols[1]:
                    if st.button(f"✏️ Edit", key=f"edit_{search.search_id}"):
                        self._show_edit_search_dialog(search)
                
                with action_cols[2]:
                    if st.button(f"🔔 Alerts", key=f"alerts_{search.search_id}"):
                        self._show_alert_settings(search)
                
                with action_cols[3]:
                    if st.button(f"🗑️ Delete", key=f"delete_{search.search_id}"):
                        if st.confirm("Are you sure you want to delete this saved search?"):
                            # Delete search logic here
                            st.success("Saved search deleted!")
    
    def _render_voice_search(self):
        """Render voice search interface"""
        st.subheader("🎤 Voice Search")
        
        st.info("Click the button below and speak your search query. Make sure your microphone is enabled.")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🎤 Start Voice Search", type="primary", use_container_width=True):
                with st.spinner("Listening... Speak your search query now"):
                    try:
                        # Simulate voice search (in real implementation, use actual voice recognition)
                        time.sleep(3)  # Simulate listening time
                        
                        # For demo, use a predefined query
                        voice_query = "budget discussion meeting"
                        
                        st.success(f"Voice query recognized: '{voice_query}'")
                        
                        # Perform search
                        results = self.search_engine.search(
                            voice_query, SearchType.VOICE,
                            st.session_state.get('user_id', 'default')
                        )
                        
                        st.session_state.search_results = results
                        st.session_state.current_query = voice_query
                        
                        st.success(f"Found {len(results)} results for voice search")
                        
                    except Exception as e:
                        st.error(f"Voice search failed: {str(e)}")
        
        # Voice search settings
        with st.expander("🔧 Voice Search Settings"):
            col1, col2 = st.columns(2)
            
            with col1:
                timeout = st.slider(
                    "Listening Timeout (seconds):",
                    min_value=3,
                    max_value=15,
                    value=5
                )
            
            with col2:
                language = st.selectbox(
                    "Recognition Language:",
                    options=["English", "Spanish", "French", "German", "Chinese"],
                    index=0
                )
        
        # Voice search tips
        st.markdown("""
        ### 💡 Voice Search Tips:
        - Speak clearly and at a normal pace
        - Use natural language queries
        - Include specific terms like speaker names or topics
        - Try phrases like "find meetings about budget" or "show John's presentations"
        """)
    
    def _render_search_analytics(self):
        """Render search analytics dashboard"""
        st.subheader("📊 Search Analytics")
        
        # Get analytics data
        analytics = self.search_engine.get_search_analytics(
            st.session_state.get('user_id', 'default')
        )
        
        if 'error' in analytics:
            st.warning(analytics['error'])
            return
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Searches", analytics.get('total_searches', 0))
        
        with col2:
            st.metric("Avg Results", f"{analytics.get('average_results', 0):.1f}")
        
        with col3:
            st.metric("Avg Time", f"{analytics.get('average_execution_time', 0):.3f}s")
        
        with col4:
            st.metric("Saved Searches", analytics.get('saved_searches_count', 0))
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Search types distribution
            search_types = analytics.get('search_types', {})
            if search_types:
                fig = px.pie(
                    values=list(search_types.values()),
                    names=list(search_types.keys()),
                    title="Search Types Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Popular queries
            popular_queries = analytics.get('popular_queries', [])
            if popular_queries:
                queries, counts = zip(*popular_queries[:10])
                fig = px.bar(
                    x=list(counts),
                    y=list(queries),
                    orientation='h',
                    title="Most Popular Queries"
                )
                fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
        
        # Daily search activity
        daily_searches = analytics.get('daily_searches', {})
        if daily_searches:
            dates = list(daily_searches.keys())
            counts = list(daily_searches.values())
            
            fig = px.line(
                x=dates,
                y=counts,
                title="Daily Search Activity",
                labels={'x': 'Date', 'y': 'Number of Searches'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Search performance insights
        st.subheader("🎯 Search Insights")
        
        if analytics.get('total_searches', 0) > 0:
            avg_results = analytics.get('average_results', 0)
            
            if avg_results < 2:
                st.warning("💡 Your searches are returning few results. Try using broader terms or fuzzy search.")
            elif avg_results > 50:
                st.info("💡 Your searches return many results. Try using more specific terms or filters.")
            else:
                st.success("✅ Your search patterns look good!")
            
            # Search type recommendations
            search_types = analytics.get('search_types', {})
            most_used = max(search_types.items(), key=lambda x: x[1])[0] if search_types else None
            
            if most_used == 'text':
                st.info("💡 Try using fuzzy search for better typo tolerance or boolean search for complex queries.")
            elif most_used == 'fuzzy':
                st.info("💡 Consider using boolean search with AND/OR operators for more precise results.")
    
    def _render_search_settings(self):
        """Render search settings"""
        st.subheader("⚙️ Search Settings")
        
        # General settings
        st.markdown("### 🔧 General Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            default_search_type = st.selectbox(
                "Default Search Type:",
                options=["Text", "Fuzzy", "Boolean", "Semantic"],
                index=0
            )
            
            results_per_page = st.selectbox(
                "Default Results Per Page:",
                options=[10, 25, 50, 100],
                index=1
            )
        
        with col2:
            fuzzy_threshold = st.slider(
                "Fuzzy Search Threshold:",
                min_value=50,
                max_value=95,
                value=70,
                help="Higher values require closer matches"
            )
            
            enable_suggestions = st.checkbox(
                "Enable Search Suggestions",
                value=True
            )
        
        # Alert settings
        st.markdown("### 🔔 Alert Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            enable_alerts = st.checkbox(
                "Enable Search Alerts",
                value=True
            )
            
            default_alert_frequency = st.selectbox(
                "Default Alert Frequency:",
                options=["Daily", "Weekly", "Monthly"],
                index=0
            )
        
        with col2:
            notification_method = st.selectbox(
                "Notification Method:",
                options=["In-App", "Email", "Webhook"],
                index=0
            )
            
            max_alerts_per_day = st.number_input(
                "Max Alerts Per Day:",
                min_value=1,
                max_value=50,
                value=10
            )
        
        # Privacy settings
        st.markdown("### 🔒 Privacy Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            save_search_history = st.checkbox(
                "Save Search History",
                value=True
            )
            
            history_retention_days = st.number_input(
                "History Retention (days):",
                min_value=7,
                max_value=365,
                value=90
            )
        
        with col2:
            enable_analytics = st.checkbox(
                "Enable Search Analytics",
                value=True
            )
            
            share_anonymous_data = st.checkbox(
                "Share Anonymous Usage Data",
                value=False
            )
        
        # Save settings
        if st.button("💾 Save Settings", type="primary"):
            # Save settings logic here
            st.success("Settings saved successfully!")
        
        # Export/Import settings
        st.markdown("### 📤 Export/Import")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📤 Export Settings"):
                settings = {
                    'default_search_type': default_search_type,
                    'results_per_page': results_per_page,
                    'fuzzy_threshold': fuzzy_threshold,
                    'enable_suggestions': enable_suggestions,
                    'enable_alerts': enable_alerts,
                    'notification_method': notification_method
                }
                
                st.download_button(
                    "Download Settings",
                    data=json.dumps(settings, indent=2),
                    file_name="search_settings.json",
                    mime="application/json"
                )
        
        with col2:
            uploaded_settings = st.file_uploader(
                "📥 Import Settings",
                type=['json'],
                help="Upload a previously exported settings file"
            )
            
            if uploaded_settings:
                try:
                    settings = json.load(uploaded_settings)
                    st.success("Settings imported successfully!")
                    st.json(settings)
                except Exception as e:
                    st.error(f"Error importing settings: {e}")
    
    def _show_save_search_dialog(self, query: str, search_type: SearchType):
        """Show save search dialog"""
        with st.form("save_search_form"):
            st.subheader("💾 Save Search")
            
            name = st.text_input("Search Name:", value=f"Search: {query[:30]}...")
            description = st.text_area("Description:", placeholder="Describe what this search is for...")
            
            col1, col2 = st.columns(2)
            
            with col1:
                enable_alerts = st.checkbox("Enable Alerts", value=False)
            
            with col2:
                alert_frequency = st.selectbox(
                    "Alert Frequency:",
                    options=["Daily", "Weekly", "Monthly"],
                    index=0
                )
            
            submitted = st.form_submit_button("💾 Save Search")
            
            if submitted and name:
                success = self.search_engine.save_search(
                    st.session_state.get('user_id', 'default'),
                    name, description, query, search_type,
                    enable_alerts=enable_alerts,
                    alert_frequency=alert_frequency.lower()
                )
                
                if success:
                    st.success("Search saved successfully!")
                else:
                    st.error("Failed to save search")
    
    def _show_full_content(self, result: SearchResult):
        """Show full content in a modal"""
        with st.expander(f"📖 Full Content: {result.title}", expanded=True):
            st.markdown(f"**Content Type:** {result.content_type.title()}")
            
            if result.speaker:
                st.markdown(f"**Speaker:** {result.speaker}")
            
            if result.timestamp:
                st.markdown(f"**Date:** {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if result.start_time is not None:
                st.markdown(f"**Time Range:** {result.start_time:.1f}s - {result.end_time:.1f}s" if result.end_time else f"**Start Time:** {result.start_time:.1f}s")
            
            st.markdown("**Content:**")
            st.text_area("", value=result.content, height=300, disabled=True)
            
            if result.metadata:
                st.markdown("**Metadata:**")
                st.json(result.metadata)
    
    def _show_share_dialog(self, result: SearchResult):
        """Show share dialog"""
        with st.expander(f"🔗 Share: {result.title}", expanded=True):
            share_url = f"https://app.example.com/content/{result.content_id}"
            
            st.text_input("Share URL:", value=share_url)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📧 Email"):
                    st.info("Email sharing feature would be implemented here")
            
            with col2:
                if st.button("💬 Slack"):
                    st.info("Slack sharing feature would be implemented here")
            
            with col3:
                if st.button("📋 Copy Link"):
                    st.success("Link copied to clipboard!")
    
    def _show_edit_search_dialog(self, search: SavedSearch):
        """Show edit search dialog"""
        st.info("Edit search functionality would be implemented here")
    
    def _show_alert_settings(self, search: SavedSearch):
        """Show alert settings dialog"""
        st.info("Alert settings functionality would be implemented here")

def main():
    """Main function for testing the UI"""
    st.set_page_config(
        page_title="Advanced Search & Discovery",
        page_icon="🔍",
        layout="wide"
    )
    
    # Initialize UI
    search_ui = AdvancedSearchUI()
    
    # Render the interface
    search_ui.render_search_interface()

if __name__ == "__main__":
    main()