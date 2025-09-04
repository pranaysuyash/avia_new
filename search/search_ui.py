"""
Streamlit UI components for advanced search functionality
"""

import streamlit as st
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
import json

from .search_manager import SearchManager, SearchQuery, SearchResult
from enhanced_components_refactored import render_empty_state, render_page_frame
from enhanced_components_refactored import log_ux_event
from enhanced_components_refactored import render_empty_state


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
            # Sync query param for deep-linkable search
            default_value = ""
            try:
                qp = st.experimental_get_query_params() or {}
                default_value = qp.get("q", [""])[0] or ""
            except Exception:
                default_value = ""
            # Get search suggestions if available
            search_query = st.text_input(
                "Search transcripts",
                value=default_value,
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
                # Date range (deep-linkable)
                st.subheader("Date Range")
                try:
                    qp = st.experimental_get_query_params() or {}
                    qp_date = qp.get("date", ["Any time"])[0]
                    qp_start = qp.get("start", [None])[0]
                    qp_end = qp.get("end", [None])[0]
                except Exception:
                    qp_date, qp_start, qp_end = "Any time", None, None
                date_options = ["Any time", "Today", "Yesterday", "Last 7 days", "Last 30 days", "Custom range"]
                date_option = st.selectbox("Date filter", date_options, index=(date_options.index(qp_date) if qp_date in date_options else 0))
                if date_option == "Custom range":
                    start_default = None
                    end_default = None
                    try:
                        if qp_start:
                            start_default = date.fromisoformat(qp_start)
                        if qp_end:
                            end_default = date.fromisoformat(qp_end)
                    except Exception:
                        start_default, end_default = None, None
                    start_date = st.date_input("Start date", value=start_default)
                    end_date = st.date_input("End date", value=end_default)
                    if start_date and end_date:
                        filters['date_range'] = {
                            'start': start_date.isoformat(),
                            'end': end_date.isoformat()
                        }
                    # Persist custom date params
                    try:
                        current = st.experimental_get_query_params() or {}
                        current['date'] = ['Custom range']
                        if start_date:
                            current['start'] = [start_date.isoformat()]
                        if end_date:
                            current['end'] = [end_date.isoformat()]
                        st.experimental_set_query_params(**current)
                    except Exception:
                        pass
                elif date_option != "Any time":
                    filters.update(self._get_date_filter(date_option))
                    # Persist date option and clear custom params
                    try:
                        current = st.experimental_get_query_params() or {}
                        current['date'] = [date_option]
                        current.pop('start', None)
                        current.pop('end', None)
                        st.experimental_set_query_params(**current)
                    except Exception:
                        pass
                else:
                    # Clear date params if Any time
                    try:
                        current = st.experimental_get_query_params() or {}
                        for k in ['date','start','end']:
                            current.pop(k, None)
                        st.experimental_set_query_params(**current)
                    except Exception:
                        pass
                
                # Language filter (deep-linkable)
                try:
                    qp = st.experimental_get_query_params() or {}
                    qp_lang = qp.get("lang", ["Any"])[0]
                except Exception:
                    qp_lang = "Any"
                language_options = ["Any", "en", "es", "fr", "de", "it", "pt", "nl", "ru", "ja", "ko", "zh"]
                language = st.selectbox("Language", language_options, index=(language_options.index(qp_lang) if qp_lang in language_options else 0))
                if language != "Any":
                    filters['language'] = language
                # Persist language selection
                try:
                    current = st.experimental_get_query_params() or {}
                    if language == "Any":
                        current.pop('lang', None)
                    else:
                        current['lang'] = [language]
                    st.experimental_set_query_params(**current)
                    try:
                        log_ux_event('search_language_changed', lang=language)
                    except Exception:
                        pass
                except Exception:
                    pass
                    
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
                # Deep-linkable speakers CSV
                try:
                    qp = st.experimental_get_query_params() or {}
                    qp_speakers = qp.get("speakers", [""])[0]
                except Exception:
                    qp_speakers = ""
                speaker_input = st.text_input(
                    "Speaker names (comma-separated)",
                    placeholder="John, Mary, Speaker 1",
                    value=qp_speakers
                )
                if speaker_input:
                    speakers = [s.strip() for s in speaker_input.split(',') if s.strip()]
                    if speakers:
                        filters['speakers'] = speakers
                # Persist speakers
                try:
                    current = st.experimental_get_query_params() or {}
                    if speaker_input.strip():
                        current['speakers'] = [speaker_input]
                    else:
                        current.pop('speakers', None)
                    st.experimental_set_query_params(**current)
                    try:
                        log_ux_event('search_speakers_changed', speakers=speaker_input)
                    except Exception:
                        pass
                except Exception:
                    pass
                
                # Tag filter
                # Deep-linkable tags CSV
                try:
                    qp = st.experimental_get_query_params() or {}
                    qp_tags = qp.get("tags", [""])[0]
                except Exception:
                    qp_tags = ""
                tag_input = st.text_input(
                    "Tags (comma-separated)",
                    placeholder="important, review, action-item",
                    value=qp_tags
                )
                if tag_input:
                    tags = [t.strip() for t in tag_input.split(',') if t.strip()]
                    if tags:
                        filters['tags'] = tags
                # Persist tags
                try:
                    current = st.experimental_get_query_params() or {}
                    if tag_input.strip():
                        current['tags'] = [tag_input]
                    else:
                        current.pop('tags', None)
                    st.experimental_set_query_params(**current)
                    try:
                        log_ux_event('search_tags_changed', tags=tag_input)
                    except Exception:
                        pass
                except Exception:
                    pass
            
            # Restore facet filters from query params (used in the search call)
            try:
                qp = st.experimental_get_query_params() or {}
                for k, v in list(qp.items()):
                    if k.startswith('facet_') and v:
                        facet_type = k[len('facet_'):]
                        vals = [x for x in v[0].split(',') if x]
                        if vals:
                            filters.setdefault('facets', {})[facet_type] = vals
            except Exception:
                pass
                        
        # Search options
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Deep-linkable results per page
            try:
                qp = st.experimental_get_query_params() or {}
                qp_limit = int(qp.get("limit", [25])[0])
            except Exception:
                qp_limit = 25
            options_limits = [10, 25, 50, 100]
            results_per_page = st.selectbox(
                "Results per page",
                options_limits,
                index=(options_limits.index(qp_limit) if qp_limit in options_limits else 1)
            )
            try:
                current = st.experimental_get_query_params() or {}
                if int(current.get("limit", [0])[0] or 0) != results_per_page:
                    current["limit"] = [str(results_per_page)]
                    st.experimental_set_query_params(**current)
            except Exception:
                pass
            
        with col2:
            # Deep-linkable sort
            try:
                qp = st.experimental_get_query_params() or {}
                qp_sort = qp.get("sort", ["relevance"])[0]
            except Exception:
                qp_sort = "relevance"
            sort_labels = ["Relevance", "Date (newest)", "Date (oldest)", "Title"]
            sort_map = {
                "relevance": "Relevance",
                "date_desc": "Date (newest)",
                "date_asc": "Date (oldest)",
                "title": "Title"
            }
            sort_inverse = {v: k for k, v in sort_map.items()}
            sort_default_label = sort_map.get(qp_sort, "Relevance")
            sort_by = st.selectbox(
                "Sort by",
                sort_labels,
                index=(sort_labels.index(sort_default_label))
            )
            # Persist sort param
            try:
                desired = sort_inverse.get(sort_by, "relevance")
                current = st.experimental_get_query_params() or {}
                if current.get("sort", [None])[0] != desired:
                    current["sort"] = [desired]
                    st.experimental_set_query_params(**current)
                    try:
                        log_ux_event('search_sort_changed', sort=desired)
                    except Exception:
                        pass
            except Exception:
                pass
            
        with col3:
            highlight = st.checkbox("Highlight matches", value=True)
            
        with col4:
            fuzzy_search = st.checkbox("Fuzzy matching", value=False)

        # Clear All Filters action
        if st.button("Clear All Filters"):
            try:
                current = st.experimental_get_query_params() or {}
                # Keys to clear
                for k in [
                    'q','sort','limit','offset','page','date','start','end','lang','entities'
                ]:
                    current.pop(k, None)
                # Remove all facet_* keys
                for k in list(current.keys()):
                    if k.startswith('facet_'):
                        current.pop(k, None)
                st.experimental_set_query_params(**current)
                st.session_state['search_offset'] = 0
                try:
                    log_ux_event('search_filters_cleared')
                except Exception:
                    pass
                st.experimental_rerun()
            except Exception:
                pass
            
        # Build search options
        options = {
            'limit': results_per_page,
            'highlight': highlight,
            'fuzzy': fuzzy_search,
            'include_facets': True
        }
        # Deep-linkable offset/page
        try:
            qp = st.experimental_get_query_params() or {}
            qp_page = qp.get("page", [None])[0]
            qp_offset = qp.get("offset", [None])[0]
            if qp_page is not None:
                page_num = max(1, int(qp_page))
                qp_offset = (page_num - 1) * results_per_page
            qp_offset = int(qp_offset) if qp_offset is not None else st.session_state.get('search_offset', 0)
        except Exception:
            qp_offset = st.session_state.get('search_offset', 0)
        st.session_state['search_offset'] = max(0, qp_offset)
        options['offset'] = st.session_state['search_offset']
        
        if sort_by == "Date (newest)":
            options['sort_by'] = 'date_desc'
        elif sort_by == "Date (oldest)":
            options['sort_by'] = 'date_asc'
        elif sort_by == "Title":
            options['sort_by'] = 'title'
        else:
            options['sort_by'] = 'relevance'

        # If no query and no filters – show helpful empty state
        if not search_query and not filters:
            render_empty_state(
                title="Search your transcripts",
                description="Start with a keyword or add filters like dates, speakers, or tags.",
                icon="🔍"
            )
            return

        # Update query param if search executed or changed
        try:
            current = st.experimental_get_query_params() or {}
            if current.get("q", [None])[0] != search_query:
                current["q"] = [search_query]
                st.experimental_set_query_params(**current)
        except Exception:
            pass
            
        # Execute search
        if search_button or search_query:
            # Pre-render skeleton placeholders for better perceived performance
            skeleton_placeholder = st.container()
            with skeleton_placeholder:
                self._render_skeleton_results(count=3)
            search_query_obj = SearchQuery(
                query=search_query,
                filters=filters,
                options=options
            )
            
            with st.spinner("Searching..."):
                results = asyncio.run(self.search_manager.search(search_query_obj))
                try:
                    log_ux_event("search_executed", query=search_query, options=options, filters=filters)
                except Exception:
                    pass
                
            # Clear skeletons
            skeleton_placeholder.empty()
            # Display results
            self._display_search_results(results)
            
        # Saved searches sidebar
        self._render_saved_searches()

        # Shareable link helper
        with st.sidebar:
            st.subheader("🔗 Share This Search")
            try:
                qp = st.experimental_get_query_params() or {}
                # Build query string from current params
                parts = []
                for k, vals in qp.items():
                    for v in vals:
                        parts.append(f"{k}={v}")
                query_str = ("?" + "&".join(parts)) if parts else ""
                st.text_input("URL params", value=query_str, help="Append to your app URL to recreate this search", key="share_link_params")
            except Exception:
                st.info("Link unavailable in this environment.")
        
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
                # Suggestions from backend if available
                if results.suggestions:
                    st.write("**Try these searches:**")
                    for suggestion in results.suggestions:
                        if st.button(suggestion, key=f"suggestion_{suggestion}"):
                            st.rerun()
                else:
                    with st.expander("Tips to refine your search", expanded=True):
                        st.write("• Check spelling or try synonyms")
                        st.write("• Broaden the date range or remove filters")
                        st.write("• Try fewer keywords, then refine with facets")
                        # Reset query param button
                        if st.button("Reset query", use_container_width=True):
                            try:
                                current = st.experimental_get_query_params() or {}
                                current.pop('q', None)
                                st.experimental_set_query_params(**current)
                                st.experimental_rerun()
                            except Exception:
                                pass
                            
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
                # Read current facet selections from query params
                try:
                    qp = st.experimental_get_query_params() or {}
                except Exception:
                    qp = {}
                for idx, (facet_type, facet_values) in enumerate(results.facets.items()):
                    if facet_values:
                        with facet_cols[idx]:
                            st.write(f"**{facet_type.title()}**")
                            options = [""] + [v for v, _ in list(facet_values.items())[:20]]
                            current = qp.get(f"facet_{facet_type}", [""])[0]
                            sel = st.selectbox(
                                label=f"{facet_type} value",
                                options=options,
                                index=(options.index(current) if current in options else 0),
                                key=f"facet_select_{facet_type}"
                            )
                            # Persist selection
                            try:
                                current_qp = st.experimental_get_query_params() or {}
                                if sel:
                                    current_qp[f"facet_{facet_type}"] = [sel]
                                else:
                                    current_qp.pop(f"facet_{facet_type}", None)
                    st.experimental_set_query_params(**current_qp)
                    try:
                        log_ux_event('search_facet_changed', facet=facet_type, values=sel)
                    except Exception:
                        pass
            except Exception:
                pass
                                    
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

    def _render_skeleton_results(self, count: int = 3):
        """Render lightweight skeleton placeholders while loading"""
        for i in range(count):
            with st.container():
                st.markdown(
                    """
                    <div style="padding: 12px; border: 1px solid var(--border-color); border-radius: 8px; margin-bottom: 12px;">
                        <div style="height: 18px; background: var(--surface-variant-color); border-radius: 4px; width: 60%; margin-bottom: 8px;"></div>
                        <div style="height: 12px; background: var(--surface-variant-color); border-radius: 4px; width: 90%; margin-bottom: 6px;"></div>
                        <div style="height: 12px; background: var(--surface-variant-color); border-radius: 4px; width: 80%;"></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
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
                    try:
                        current = st.experimental_get_query_params() or {}
                        current['offset'] = ['0']
                        current['page'] = ['1']
                        st.experimental_set_query_params(**current)
                    except Exception:
                        pass
                    st.rerun()
                    
        with col2:
            if current_page > 1:
                if st.button("◀️ Previous"):
                    new_offset = (current_page - 2) * results.query.options['limit']
                    st.session_state['search_offset'] = new_offset
                    try:
                        current = st.experimental_get_query_params() or {}
                        current['offset'] = [str(new_offset)]
                        current['page'] = [str(current_page - 1)]
                        st.experimental_set_query_params(**current)
                    except Exception:
                        pass
                    st.rerun()
                    
        with col3:
            st.write(f"Page {current_page} of {total_pages}")
            
        with col4:
            if current_page < total_pages:
                if st.button("Next ▶️"):
                    new_offset = current_page * results.query.options['limit']
                    st.session_state['search_offset'] = new_offset
                    try:
                        current = st.experimental_get_query_params() or {}
                        current['offset'] = [str(new_offset)]
                        current['page'] = [str(current_page + 1)]
                        st.experimental_set_query_params(**current)
                    except Exception:
                        pass
                    st.rerun()
                    
        with col5:
            if current_page < total_pages:
                if st.button("Last ⏭️"):
                    new_offset = (total_pages - 1) * results.query.options['limit']
                    st.session_state['search_offset'] = new_offset
                    try:
                        current = st.experimental_get_query_params() or {}
                        current['offset'] = [str(new_offset)]
                        current['page'] = [str(total_pages)]
                        st.experimental_set_query_params(**current)
                    except Exception:
                        pass
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
    # Standard page frame with env/role chips
    try:
        render_page_frame(
            title="🔍 Advanced Search",
            subtitle="Find transcripts quickly with deep-linked filters",
            breadcrumb=["Search"],
            env_label=st.session_state.get('env', 'Demo'),
            role_label=st.session_state.get('user', {}).get('role', 'guest')
        )
    except Exception:
        pass
    
    # Initialize search UI
    search_ui = SearchUI()
    
    # Apply any saved filters from session state
    if 'search_offset' not in st.session_state:
        st.session_state['search_offset'] = 0
        
    # Render the interface
    search_ui.render_search_interface()


if __name__ == "__main__":
    render_search_page()
