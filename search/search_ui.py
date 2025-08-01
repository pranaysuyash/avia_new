"""
Streamlit UI components for advanced search functionality
"""

import streamlit as st
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
import json

from .search_manager import SearchManager, SearchQuery, SearchResult


class SearchUI:
    """UI components for search functionality"""
    
    def __init__(self):
        self.search_manager = SearchManager()
        
    def render_search_interface(self):
        """Render the main search interface"""
        st.title("🔍 Advanced Search")
        
        # Search input with suggestions
        col1, col2 = st.columns([4, 1])
        
        with col1:
            # Get search suggestions if available
            search_query = st.text_input(
                "Search transcripts",
                placeholder="Enter search terms, use filters like speaker:john tag:important date:2024",
                help="Use quotes for exact phrases, - for exclusions, + for required terms"
            )
            
        with col2:
            search_button = st.button("Search", type="primary", use_container_width=True)
            
        # Quick filter buttons
        st.write("**Quick Filters:**")
        filter_cols = st.columns(5)
        
        filters = {}
        
        with filter_cols[0]:
            if st.button("📅 Today"):
                filters['date_range'] = {
                    'start': date.today().isoformat(),
                    'end': date.today().isoformat()
                }
                
        with filter_cols[1]:
            if st.button("📅 This Week"):
                filters['date_range'] = {
                    'start': (date.today() - timedelta(days=7)).isoformat(),
                    'end': date.today().isoformat()
                }
                
        with filter_cols[2]:
            if st.button("👥 With Speakers"):
                filters['has_speakers'] = True
                
        with filter_cols[3]:
            if st.button("🏷️ Tagged"):
                filters['has_tags'] = True
                
        with filter_cols[4]:
            if st.button("🔤 With Entities"):
                filters['has_entities'] = True
                
        # Advanced filters (expandable)
        with st.expander("Advanced Filters"):
            adv_col1, adv_col2, adv_col3 = st.columns(3)
            
            with adv_col1:
                # Date range
                st.subheader("Date Range")
                date_option = st.selectbox(
                    "Date filter",
                    ["Any time", "Today", "Yesterday", "Last 7 days", "Last 30 days", "Custom range"]
                )
                
                if date_option == "Custom range":
                    start_date = st.date_input("Start date")
                    end_date = st.date_input("End date")
                    if start_date and end_date:
                        filters['date_range'] = {
                            'start': start_date.isoformat(),
                            'end': end_date.isoformat()
                        }
                elif date_option != "Any time":
                    filters.update(self._get_date_filter(date_option))
                    
                # Language filter
                language = st.selectbox(
                    "Language",
                    ["Any", "en", "es", "fr", "de", "it", "pt", "nl", "ru", "ja", "ko", "zh"]
                )
                if language != "Any":
                    filters['language'] = language
                    
            with adv_col2:
                # Entity type filter
                st.subheader("Entity Types")
                entity_types = st.multiselect(
                    "Include entities",
                    ["PERSON", "ORG", "LOC", "DATE", "TIME", "MONEY", "PERCENT", "PRODUCT"]
                )
                if entity_types:
                    filters['entity_types'] = entity_types
                    
                # Confidence filter
                confidence = st.slider(
                    "Minimum confidence",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.7,
                    step=0.1
                )
                if confidence > 0:
                    filters['min_confidence'] = confidence
                    
            with adv_col3:
                # Speaker filter
                st.subheader("Speakers")
                speaker_input = st.text_input(
                    "Speaker names (comma-separated)",
                    placeholder="John, Mary, Speaker 1"
                )
                if speaker_input:
                    speakers = [s.strip() for s in speaker_input.split(',') if s.strip()]
                    if speakers:
                        filters['speakers'] = speakers
                        
                # Tag filter
                tag_input = st.text_input(
                    "Tags (comma-separated)",
                    placeholder="important, review, action-item"
                )
                if tag_input:
                    tags = [t.strip() for t in tag_input.split(',') if t.strip()]
                    if tags:
                        filters['tags'] = tags
                        
        # Search options
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            results_per_page = st.selectbox(
                "Results per page",
                [10, 25, 50, 100],
                index=1
            )
            
        with col2:
            sort_by = st.selectbox(
                "Sort by",
                ["Relevance", "Date (newest)", "Date (oldest)", "Title"]
            )
            
        with col3:
            highlight = st.checkbox("Highlight matches", value=True)
            
        with col4:
            fuzzy_search = st.checkbox("Fuzzy matching", value=False)
            
        # Build search options
        options = {
            'limit': results_per_page,
            'highlight': highlight,
            'fuzzy': fuzzy_search,
            'include_facets': True
        }
        
        if sort_by == "Date (newest)":
            options['sort_by'] = 'date_desc'
        elif sort_by == "Date (oldest)":
            options['sort_by'] = 'date_asc'
        elif sort_by == "Title":
            options['sort_by'] = 'title'
        else:
            options['sort_by'] = 'relevance'
            
        # Execute search
        if search_button or search_query:
            search_query_obj = SearchQuery(
                query=search_query,
                filters=filters,
                options=options
            )
            
            with st.spinner("Searching..."):
                results = asyncio.run(self.search_manager.search(search_query_obj))
                
            # Display results
            self._display_search_results(results)
            
        # Saved searches sidebar
        self._render_saved_searches()
        
    def _display_search_results(self, results: SearchResult):
        """Display search results"""
        # Results summary
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if results.has_results:
                page_info = results.page_info
                st.write(
                    f"**Found {results.total_count} results** "
                    f"(showing {page_info['showing_from']}-{page_info['showing_to']}) "
                    f"in {results.search_time_ms:.0f}ms"
                )
            else:
                st.warning("No results found")
                
                # Show suggestions
                if results.suggestions:
                    st.write("**Try these searches:**")
                    for suggestion in results.suggestions:
                        if st.button(suggestion, key=f"suggestion_{suggestion}"):
                            st.rerun()
                            
        with col2:
            # Export options
            if results.has_results:
                export_format = st.selectbox(
                    "Export",
                    ["", "JSON", "CSV"],
                    key="export_format"
                )
                
                if export_format:
                    export_data = self.search_manager.export_results(
                        results,
                        export_format.lower()
                    )
                    
                    st.download_button(
                        label=f"Download {export_format}",
                        data=export_data,
                        file_name=f"search_results.{export_format.lower()}",
                        mime=f"application/{export_format.lower()}"
                    )
                    
        # Display facets
        if results.facets and results.has_results:
            with st.expander("Filter by facets", expanded=False):
                facet_cols = st.columns(len(results.facets))
                
                for idx, (facet_type, facet_values) in enumerate(results.facets.items()):
                    if facet_values:
                        with facet_cols[idx]:
                            st.write(f"**{facet_type.title()}**")
                            for value, count in list(facet_values.items())[:10]:
                                if st.button(
                                    f"{value} ({count})",
                                    key=f"facet_{facet_type}_{value}"
                                ):
                                    # Add to filters
                                    st.session_state[f'filter_{facet_type}'] = value
                                    st.rerun()
                                    
        # Display results
        if results.has_results:
            for idx, result in enumerate(results.results):
                self._render_result_card(result, idx)
                
        # Pagination
        if results.total_count > results.query.options['limit']:
            self._render_pagination(results)
            
    def _render_result_card(self, result: Dict[str, Any], index: int):
        """Render a single search result"""
        with st.container():
            # Title and metadata
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"### {result['title']}")
                
            with col2:
                if st.button("View", key=f"view_{result['doc_id']}"):
                    st.session_state['selected_transcript'] = result['doc_id']
                    st.switch_page("pages/transcript_viewer.py")
                    
            # Snippet with highlighting
            if result.get('title_snippet') and '<mark>' in result['title_snippet']:
                st.markdown(
                    f"**Title match:** {result['title_snippet']}",
                    unsafe_allow_html=True
                )
                
            if result.get('content_snippet'):
                st.markdown(
                    f"{result['content_snippet']}",
                    unsafe_allow_html=True
                )
                
            # Metadata tags
            metadata_cols = st.columns(6)
            
            with metadata_cols[0]:
                if result.get('created_at'):
                    created = datetime.fromisoformat(result['created_at'])
                    st.caption(f"📅 {created.strftime('%Y-%m-%d')}")
                    
            with metadata_cols[1]:
                if result.get('language'):
                    st.caption(f"🌐 {result['language'].upper()}")
                    
            with metadata_cols[2]:
                if result.get('confidence'):
                    st.caption(f"🎯 {result['confidence']:.0%}")
                    
            with metadata_cols[3]:
                if result.get('speakers'):
                    st.caption(f"👥 {len(result['speakers'])} speakers")
                    
            with metadata_cols[4]:
                if result.get('tags'):
                    st.caption(f"🏷️ {', '.join(result['tags'][:3])}")
                    
            with metadata_cols[5]:
                if result.get('entities'):
                    st.caption(f"🔤 {len(result['entities'])} entities")
                    
            st.divider()
            
    def _render_pagination(self, results: SearchResult):
        """Render pagination controls"""
        page_info = results.page_info
        
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        current_page = page_info['current_page']
        total_pages = page_info['total_pages']
        
        with col1:
            if current_page > 1:
                if st.button("⏮️ First"):
                    st.session_state['search_offset'] = 0
                    st.rerun()
                    
        with col2:
            if current_page > 1:
                if st.button("◀️ Previous"):
                    new_offset = (current_page - 2) * results.query.options['limit']
                    st.session_state['search_offset'] = new_offset
                    st.rerun()
                    
        with col3:
            st.write(f"Page {current_page} of {total_pages}")
            
        with col4:
            if current_page < total_pages:
                if st.button("Next ▶️"):
                    new_offset = current_page * results.query.options['limit']
                    st.session_state['search_offset'] = new_offset
                    st.rerun()
                    
        with col5:
            if current_page < total_pages:
                if st.button("Last ⏭️"):
                    new_offset = (total_pages - 1) * results.query.options['limit']
                    st.session_state['search_offset'] = new_offset
                    st.rerun()
                    
    def _render_saved_searches(self):
        """Render saved searches in sidebar"""
        with st.sidebar:
            st.subheader("💾 Saved Searches")
            
            saved_searches = self.search_manager.get_saved_searches()
            
            if saved_searches:
                for search in saved_searches:
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        if st.button(
                            search['name'],
                            key=f"saved_{search['search_id']}",
                            use_container_width=True
                        ):
                            # Load saved search
                            st.session_state['search_query'] = search['query']
                            st.session_state['search_filters'] = search['filters']
                            st.rerun()
                            
                    with col2:
                        st.caption(f"({search['use_count']})")
                        
            else:
                st.info("No saved searches yet")
                
            # Save current search
            st.divider()
            
            if st.session_state.get('last_search_query'):
                save_name = st.text_input("Save current search as:")
                if st.button("Save Search"):
                    if save_name:
                        self.search_manager.save_search(
                            save_name,
                            st.session_state['last_search_query']
                        )
                        st.success("Search saved!")
                        st.rerun()
                        
            # Search history
            st.divider()
            st.subheader("🕐 Recent Searches")
            
            history = self.search_manager.get_search_history(limit=10)
            
            for hist in history:
                if st.button(
                    hist['query'][:30] + "..." if len(hist['query']) > 30 else hist['query'],
                    key=f"history_{hist['searched_at']}"
                ):
                    st.session_state['search_query'] = hist['query']
                    st.session_state['search_filters'] = hist['filters']
                    st.rerun()
                    
    def _get_date_filter(self, option: str) -> Dict[str, Any]:
        """Convert date option to filter"""
        today = date.today()
        
        if option == "Today":
            return {
                'date_range': {
                    'start': today.isoformat(),
                    'end': today.isoformat()
                }
            }
        elif option == "Yesterday":
            yesterday = today - timedelta(days=1)
            return {
                'date_range': {
                    'start': yesterday.isoformat(),
                    'end': yesterday.isoformat()
                }
            }
        elif option == "Last 7 days":
            return {
                'date_range': {
                    'start': (today - timedelta(days=7)).isoformat(),
                    'end': today.isoformat()
                }
            }
        elif option == "Last 30 days":
            return {
                'date_range': {
                    'start': (today - timedelta(days=30)).isoformat(),
                    'end': today.isoformat()
                }
            }
            
        return {}


def render_search_page():
    """Main entry point for search page"""
    st.set_page_config(
        page_title="Advanced Search",
        page_icon="🔍",
        layout="wide"
    )
    
    # Initialize search UI
    search_ui = SearchUI()
    
    # Apply any saved filters from session state
    if 'search_offset' not in st.session_state:
        st.session_state['search_offset'] = 0
        
    # Render the interface
    search_ui.render_search_interface()


if __name__ == "__main__":
    render_search_page()