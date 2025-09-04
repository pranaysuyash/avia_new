#!/usr/bin/env python3
"""
Advanced Search System UI - Task 133 Interface
Comprehensive Streamlit interface for the advanced search and discovery system
"""

import streamlit as st
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from advanced_search_system import (
    AdvancedSearchSystem, AdvancedSearchQuery, SearchStrategy, 
    RelevanceModel, SearchFilter, advanced_search_system
)
from services.comprehensive_search_service import SearchType, SearchScope, SortOrder
from streamlit_unified_components import UnifiedComponents
from streamlit_intent_utils import get_params, update_params, render_share_block, log_ux_event, render_skeleton_list, render_share_inline


class AdvancedSearchSystemUI:
    """Streamlit UI for Advanced Search System"""
    
    def __init__(self):
        self.unified = UnifiedComponents()
        self.search_system = advanced_search_system
        
        # Initialize session state
        if 'search_ui_state' not in st.session_state:
            st.session_state.search_ui_state = {
                'search_history': [],
                'saved_queries': [],
                'search_results': None,
                'last_query': '',
                'active_filters': [],
                'selected_facets': {},
                'search_analytics': None
            }
    
    def render_advanced_search_interface(self):
        """Render the complete advanced search interface"""
        
        # Header
        st.markdown("# 🔍 Advanced Search & Discovery System")
        st.markdown("*Semantic search, fuzzy matching, faceted search, and intelligent ranking*")
        render_share_inline()
        
        # Deep-linked tabs via as_tab (search|analytics|settings|help)
        tab_map = [
            ("search", "🔍 Search"),
            ("analytics", "📊 Analytics"),
            ("settings", "⚙️ Settings"),
            ("help", "❓ Help"),
        ]
        current_tab_key = get_params().get('as_tab', 'search')
        ordered = [x for x in tab_map if x[0] == current_tab_key] + [x for x in tab_map if x[0] != current_tab_key]
        tab_labels = [label for _, label in ordered]
        tabs = st.tabs(tab_labels)
        key_to_tab = {k: tabs[i] for i, (k, _) in enumerate(ordered)}
        
        with key_to_tab["search"]:
            self._render_search_interface()
        
        with key_to_tab["analytics"]:
            self._render_analytics_dashboard()
        
        with key_to_tab["settings"]:
            self._render_search_settings()
        
        with key_to_tab["help"]:
            self._render_help_documentation()
        
        # Sidebar quick section selector
        with st.sidebar:
            st.markdown("---")
            section_key = st.selectbox(
                "Section",
                options=[k for k, _ in tab_map],
                index=[k for k, _ in tab_map].index(current_tab_key) if current_tab_key in [k for k, _ in tab_map] else 0,
                format_func=lambda k: dict(tab_map)[k]
            )
            if section_key != current_tab_key:
                try:
                    update_params({'as_tab': section_key})
                except Exception:
                    pass
                st.experimental_rerun()
    
    def _render_search_interface(self):
        """Render the main search interface"""
        # Sync deep-linked params into session defaults (one-way)
        params = get_params()
        if params.get('q'):
            st.session_state.search_ui_state['last_query'] = params.get('q')
            st.session_state['main_search_query'] = params.get('q')
        if params.get('sort'):
            st.session_state['sort_order'] = params.get('sort')
        if params.get('strategy'):
            st.session_state['search_strategy'] = params.get('strategy')
        if params.get('scope'):
            st.session_state['search_scope'] = params.get('scope')

        # Search query input
        st.markdown("### 🔍 Search Query")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            query = st.text_input(
                "Enter your search query",
                value=st.session_state.search_ui_state.get('last_query', ''),
                placeholder="e.g., 'machine learning presentation' or 'speaker:john meeting AND quarterly'",
                help="Use quotes for exact phrases, AND/OR/NOT for boolean search, speaker: for specific speakers",
                key="main_search_query"
            )
            update_params({'q': query or None})
        
        with col2:
            search_button = st.button("🔍 Search", type="primary")
        
        # Quick search suggestions
        if query and len(query) >= 2:
            suggestions = self._get_search_suggestions(query)
            if suggestions:
                st.markdown("**💡 Suggestions:**")
                suggestion_cols = st.columns(min(len(suggestions), 3))
                for i, suggestion in enumerate(suggestions[:3]):
                    with suggestion_cols[i]:
                        if st.button(f"💭 {suggestion}", key=f"suggestion_{i}"):
                            st.session_state.main_search_query = suggestion
                            st.rerun()
        
        # Advanced search options
        with st.expander("🎛️ Advanced Search Options", expanded=False):
            self._render_advanced_options()
        
        # Active filters display
        if st.session_state.search_ui_state.get('active_filters'):
            st.markdown("**🏷️ Active Filters:**")
            self._render_active_filters()
        
        # Perform search
        if search_button and query:
            # Show skeleton results while performing search
            skel = st.container()
            with skel:
                render_skeleton_list(items=3)
            log_ux_event('search_executed', {
                'q': query,
                'sort': st.session_state.get('sort_order'),
                'strategy': st.session_state.get('search_strategy'),
                'scope': st.session_state.get('search_scope')
            })
            st.session_state.search_ui_state['last_query'] = query
            with st.spinner("🔍 Searching..."):
                self._perform_search(query)
            skel.empty()
        
        # Display search results
        if st.session_state.search_ui_state.get('search_results'):
            self._render_search_results()
    
    def _render_advanced_options(self):
        """Render advanced search options"""
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🎯 Search Strategy**")
            search_strategy = st.selectbox(
                "Search Strategy",
                options=[s.value for s in SearchStrategy],
                index=0,
                format_func=lambda x: {
                    'hybrid': '🔄 Hybrid (Semantic + Traditional)',
                    'semantic_only': '🧠 Semantic Only',
                    'traditional_only': '📝 Traditional Only',
                    'fuzzy_enhanced': '🔤 Fuzzy Enhanced',
                    'neural_ranking': '🤖 Neural Ranking'
                }.get(x, x),
                key="search_strategy"
            )
            update_params({'strategy': search_strategy})
            
            relevance_model = st.selectbox(
                "Relevance Model",
                options=[r.value for r in RelevanceModel],
                index=3,  # Default to hybrid_ensemble
                format_func=lambda x: {
                    'bm25': '📊 BM25',
                    'tfidf': '📈 TF-IDF',
                    'neural': '🧠 Neural',
                    'hybrid_ensemble': '🎯 Hybrid Ensemble'
                }.get(x, x),
                key="relevance_model"
            )
        
        with col2:
            st.markdown("**🔍 Search Scope**")
            search_scope = st.selectbox(
                "Search Scope",
                options=[s.value for s in SearchScope],
                format_func=lambda x: {
                    'all': '🌐 All Content',
                    'transcripts': '📄 Transcripts Only',
                    'users': '👥 Users Only',
                    'content': '📁 Content Only',
                    'metadata': '📋 Metadata Only'
                }.get(x, x),
                key="search_scope"
            )
            update_params({'scope': search_scope})
            
            sort_order = st.selectbox(
                "Sort Order",
                options=[s.value for s in SortOrder],
                format_func=lambda x: {
                    'relevance': '⭐ Relevance',
                    'date_desc': '📅 Date (Newest First)',
                    'date_asc': '📅 Date (Oldest First)',
                    'title_asc': '🔤 Title (A-Z)',
                    'title_desc': '🔤 Title (Z-A)',
                    'duration_desc': '⏱️ Duration (Longest)',
                    'duration_asc': '⏱️ Duration (Shortest)'
                }.get(x, x),
                key="sort_order"
            )
            update_params({'sort': sort_order})
        
        with col3:
            st.markdown("**⚙️ Search Options**")
            
            diversify_results = st.checkbox(
                "🎭 Diversify Results",
                value=True,
                help="Reduce redundancy in search results",
                key="diversify_results"
            )
            
            explain_ranking = st.checkbox(
                "📖 Explain Ranking",
                value=False,
                help="Show why results were ranked as they were",
                key="explain_ranking"
            )
            
            semantic_threshold = st.slider(
                "🎯 Semantic Similarity Threshold",
                min_value=0.1,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="Minimum similarity for semantic search",
                key="semantic_threshold"
            )
        
        # Faceted search options
        st.markdown("**📊 Faceted Search**")
        facets = st.multiselect(
            "Select Facets to Display",
            options=['content_type', 'language', 'duration', 'date_created', 'speaker', 'topic'],
            default=['content_type', 'duration'],
            format_func=lambda x: {
                'content_type': '📄 Content Type',
                'language': '🌐 Language',
                'duration': '⏱️ Duration',
                'date_created': '📅 Date Created',
                'speaker': '👤 Speaker',
                'topic': '🏷️ Topic'
            }.get(x, x),
            key="selected_facets"
        )
        # Sidebar share/reset for Search view
        with st.sidebar:
            render_share_block("Share Search View")
            if st.button("Clear All (Query + Options)"):
                update_params({'q': None, 'sort': None, 'strategy': None, 'scope': None})
                log_ux_event('search_filters_cleared', {'scope': 'advanced_search'})
        
        # Field boosting
        st.markdown("**⚡ Field Boosting**")
        boost_col1, boost_col2 = st.columns(2)
        
        with boost_col1:
            title_boost = st.slider(
                "📰 Title Boost",
                min_value=0.1,
                max_value=5.0,
                value=2.0,
                step=0.1,
                key="title_boost"
            )
        
        with boost_col2:
            content_boost = st.slider(
                "📝 Content Boost",
                min_value=0.1,
                max_value=5.0,
                value=1.0,
                step=0.1,
                key="content_boost"
            )
    
    def _render_active_filters(self):
        """Render active search filters"""
        
        active_filters = st.session_state.search_ui_state.get('active_filters', [])
        
        if not active_filters:
            st.info("No active filters")
            return
        
        filter_cols = st.columns(min(len(active_filters), 4))
        
        for i, filter_obj in enumerate(active_filters):
            with filter_cols[i % 4]:
                filter_text = f"{filter_obj.field} {filter_obj.operator} {filter_obj.value}"
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.info(filter_text)
                with col2:
                    if st.button("❌", key=f"remove_filter_{i}"):
                        active_filters.pop(i)
                        st.session_state.search_ui_state['active_filters'] = active_filters
                        st.rerun()
        
        if st.button("🗑️ Clear All Filters"):
            st.session_state.search_ui_state['active_filters'] = []
            st.rerun()
    
    def _get_search_suggestions(self, query: str) -> List[str]:
        """Get search suggestions based on query"""
        
        # Simple suggestion logic (in production, use proper suggestion engine)
        suggestions = []
        
        query_lower = query.lower()
        
        # Common search patterns
        if 'meeting' in query_lower:
            suggestions.extend(['meeting minutes', 'team meeting', 'quarterly meeting'])
        elif 'presentation' in query_lower:
            suggestions.extend(['presentation slides', 'technical presentation', 'sales presentation'])
        elif 'interview' in query_lower:
            suggestions.extend(['job interview', 'technical interview', 'interview questions'])
        
        # Add generic suggestions
        if len(query.split()) == 1:
            suggestions.extend([f'{query} summary', f'{query} transcript', f'{query} analysis'])
        
        return list(set(suggestions))[:5]
    
    def _perform_search(self, query: str):
        """Perform advanced search"""
        
        try:
            # Build search query from UI settings
            search_query = AdvancedSearchQuery(
                query=query,
                search_strategy=SearchStrategy(st.session_state.get('search_strategy', 'hybrid')),
                relevance_model=RelevanceModel(st.session_state.get('relevance_model', 'hybrid_ensemble')),
                search_type=SearchType.FULL_TEXT,
                scope=SearchScope(st.session_state.get('search_scope', 'all')),
                filters=st.session_state.search_ui_state.get('active_filters', []),
                facets=st.session_state.get('selected_facets', []),
                sort_order=SortOrder(st.session_state.get('sort_order', 'relevance')),
                limit=20,
                offset=0,
                boost_factors={
                    'title': st.session_state.get('title_boost', 2.0),
                    'content': st.session_state.get('content_boost', 1.0)
                },
                diversify_results=st.session_state.get('diversify_results', True),
                explain_ranking=st.session_state.get('explain_ranking', False),
                semantic_similarity_threshold=st.session_state.get('semantic_threshold', 0.7),
                user_context={'user_id': 'streamlit_user'}
            )
            
            # Note: In actual implementation, this would be:
            # results = asyncio.run(self.search_system.search(search_query))
            
            # For demo purposes, create mock results
            mock_results = self._create_mock_search_results(query)
            st.session_state.search_ui_state['search_results'] = mock_results
            
            # Add to search history
            history_entry = {
                'query': query,
                'timestamp': datetime.now(),
                'results_count': len(mock_results.get('results', [])),
                'search_time_ms': mock_results.get('search_time_ms', 0)
            }
            
            search_history = st.session_state.search_ui_state.get('search_history', [])
            search_history.insert(0, history_entry)
            st.session_state.search_ui_state['search_history'] = search_history[:10]  # Keep last 10
            
            st.success(f"✅ Found {len(mock_results.get('results', []))} results in {mock_results.get('search_time_ms', 0):.0f}ms")
            
        except Exception as e:
            st.error(f"❌ Search error: {e}")
    
    def _create_mock_search_results(self, query: str) -> Dict[str, Any]:
        """Create mock search results for demo"""
        
        # Generate mock results based on query
        mock_results = []
        
        base_results = [
            {
                'id': 'result_1',
                'type': 'transcript',
                'title': f'Team Meeting - {query.title()} Discussion',
                'content': f'In this meeting, we discussed {query} and its implications for our project. The team reviewed various aspects and made important decisions.',
                'score': 0.95,
                'created_at': datetime.now() - timedelta(days=1),
                'metadata': {'duration': 1800, 'speaker': 'John Smith', 'language': 'en'}
            },
            {
                'id': 'result_2',
                'type': 'transcript',
                'title': f'Presentation on {query.title()}',
                'content': f'This presentation covers the fundamentals of {query}, including best practices and implementation strategies.',
                'score': 0.88,
                'created_at': datetime.now() - timedelta(days=3),
                'metadata': {'duration': 2400, 'speaker': 'Sarah Johnson', 'language': 'en'}
            },
            {
                'id': 'result_3',
                'type': 'transcript',
                'title': f'Technical Interview - {query.title()} Skills',
                'content': f'A technical interview discussing {query} skills and experience. Candidate demonstrates good understanding of the topic.',
                'score': 0.82,
                'created_at': datetime.now() - timedelta(days=5),
                'metadata': {'duration': 3600, 'speaker': 'Mike Chen', 'language': 'en'}
            },
            {
                'id': 'result_4',
                'type': 'transcript',
                'title': f'Training Session: {query.title()} Basics',
                'content': f'Training session covering the basics of {query}. Great for beginners who want to understand fundamental concepts.',
                'score': 0.76,
                'created_at': datetime.now() - timedelta(days=7),
                'metadata': {'duration': 4200, 'speaker': 'Emily Davis', 'language': 'en'}
            }
        ]
        
        return {
            'results': base_results,
            'total_count': len(base_results),
            'search_time_ms': 45.2,
            'query': query,
            'facets': {
                'content_type': {
                    'type': 'categorical',
                    'values': [
                        {'value': 'transcript', 'count': 4, 'selected': False}
                    ]
                },
                'duration': {
                    'type': 'range',
                    'ranges': [
                        {'label': '15-30 min', 'min': 900, 'max': 1800, 'count': 1},
                        {'label': '30-60 min', 'min': 1800, 'max': 3600, 'count': 2},
                        {'label': '60+ min', 'min': 3600, 'max': None, 'count': 1}
                    ]
                }
            },
            'query_suggestions': [f'{query} tutorial', f'{query} examples', f'{query} best practices'],
            'related_queries': [f'{query} implementation', f'{query} strategy', f'{query} analysis']
        }
    
    def _render_search_results(self):
        """Render search results"""
        
        results_data = st.session_state.search_ui_state['search_results']
        results = results_data.get('results', [])
        
        if not results:
            st.info("No results found")
            return
        
        st.markdown("---")
        st.markdown("## 📋 Search Results")
        
        # Results summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🔍 Total Results", results_data.get('total_count', 0))
        
        with col2:
            st.metric("⚡ Search Time", f"{results_data.get('search_time_ms', 0):.1f}ms")
        
        with col3:
            avg_score = sum(r['score'] for r in results) / len(results)
            st.metric("⭐ Avg. Relevance", f"{avg_score:.2f}")
        
        with col4:
            st.metric("📊 Result Types", len(set(r['type'] for r in results)))
        
        # Search insights
        insights_col1, insights_col2 = st.columns(2)
        
        with insights_col1:
            suggestions = results_data.get('query_suggestions', [])
            if suggestions:
                st.markdown("**💡 Query Suggestions:**")
                for suggestion in suggestions:
                    if st.button(f"💭 {suggestion}", key=f"result_suggestion_{suggestion}"):
                        st.session_state.main_search_query = suggestion
                        st.rerun()
        
        with insights_col2:
            related = results_data.get('related_queries', [])
            if related:
                st.markdown("**🔗 Related Queries:**")
                for related_query in related:
                    if st.button(f"🔗 {related_query}", key=f"related_{related_query}"):
                        st.session_state.main_search_query = related_query
                        st.rerun()
        
        # Facets sidebar
        if results_data.get('facets'):
            st.markdown("### 📊 Filter Results")
            self._render_facets(results_data['facets'])
        
        # Individual results
        st.markdown("### 📄 Results")
        
        for i, result in enumerate(results):
            with st.container():
                # Result header
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**{result['title']}**")
                    st.markdown(f"*{result['type'].title()}* • Score: {result['score']:.2f}")
                
                with col2:
                    if st.button("👁️ View Details", key=f"view_{result['id']}"):
                        st.session_state.selected_result = result
                        st.rerun()
                
                # Result content
                st.markdown(result['content'][:300] + "..." if len(result['content']) > 300 else result['content'])
                
                # Result metadata
                metadata = result.get('metadata', {})
                meta_items = []
                
                if metadata.get('speaker'):
                    meta_items.append(f"👤 {metadata['speaker']}")
                if metadata.get('duration'):
                    duration_min = metadata['duration'] // 60
                    meta_items.append(f"⏱️ {duration_min}m")
                if metadata.get('language'):
                    meta_items.append(f"🌐 {metadata['language']}")
                
                if meta_items:
                    st.markdown(" • ".join(meta_items))
                
                # Result actions
                action_col1, action_col2, action_col3, action_col4 = st.columns(4)
                
                with action_col1:
                    if st.button("⭐ Relevant", key=f"relevant_{result['id']}"):
                        st.success("Marked as relevant!")
                
                with action_col2:
                    if st.button("❌ Not Relevant", key=f"not_relevant_{result['id']}"):
                        st.info("Marked as not relevant")
                
                with action_col3:
                    if st.button("💾 Save", key=f"save_{result['id']}"):
                        st.success("Result saved!")
                
                with action_col4:
                    if st.button("📤 Share", key=f"share_{result['id']}"):
                        st.info("Share link copied!")
                
                st.markdown("---")
        
        # Pagination
        if results_data.get('total_count', 0) > len(results):
            st.markdown("### 📖 Pagination")
            if st.button("📄 Load More Results"):
                st.info("Loading more results...")
    
    def _render_facets(self, facets: Dict[str, Any]):
        """Render search facets for filtering"""
        
        for facet_name, facet_data in facets.items():
            st.markdown(f"**{facet_name.replace('_', ' ').title()}**")
            
            if facet_data['type'] == 'categorical':
                values = facet_data.get('values', [])
                
                for value_data in values:
                    value = value_data['value']
                    count = value_data['count']
                    
                    if st.checkbox(f"{value} ({count})", key=f"facet_{facet_name}_{value}"):
                        # Add filter
                        new_filter = SearchFilter(
                            field=facet_name,
                            operator='eq',
                            value=value
                        )
                        
                        active_filters = st.session_state.search_ui_state.get('active_filters', [])
                        if new_filter not in active_filters:
                            active_filters.append(new_filter)
                            st.session_state.search_ui_state['active_filters'] = active_filters
                            st.rerun()
            
            elif facet_data['type'] == 'range':
                ranges = facet_data.get('ranges', [])
                
                for range_data in ranges:
                    label = range_data['label']
                    count = range_data['count']
                    
                    if st.checkbox(f"{label} ({count})", key=f"facet_{facet_name}_{label}"):
                        # Add range filter
                        new_filter = SearchFilter(
                            field=facet_name,
                            operator='gte',
                            value=range_data.get('min', 0)
                        )
                        
                        active_filters = st.session_state.search_ui_state.get('active_filters', [])
                        if new_filter not in active_filters:
                            active_filters.append(new_filter)
                            st.session_state.search_ui_state['active_filters'] = active_filters
                            st.rerun()
    
    def _render_analytics_dashboard(self):
        """Render search analytics dashboard"""
        
        st.markdown("### 📊 Search Analytics Dashboard")
        
        # Get analytics data (mock data for demo)
        analytics_data = self._get_mock_analytics_data()
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🔍 Total Searches", analytics_data['total_searches'])
        
        with col2:
            st.metric("⚡ Avg Search Time", f"{analytics_data['avg_search_time_ms']:.1f}ms")
        
        with col3:
            st.metric("📄 Avg Results", f"{analytics_data['avg_results_count']:.1f}")
        
        with col4:
            st.metric("📈 Success Rate", f"{analytics_data['success_rate']:.1f}%")
        
        # Charts
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("#### 🎯 Search Strategy Usage")
            strategy_df = pd.DataFrame(list(analytics_data['strategy_usage'].items()), 
                                     columns=['Strategy', 'Count'])
            fig = px.pie(strategy_df, values='Count', names='Strategy', 
                        title="Search Strategy Distribution")
            st.plotly_chart(fig, use_container_width=True)
        
        with chart_col2:
            st.markdown("#### 📊 Relevance Model Usage")
            model_df = pd.DataFrame(list(analytics_data['model_usage'].items()), 
                                  columns=['Model', 'Count'])
            fig = px.bar(model_df, x='Model', y='Count', 
                        title="Relevance Model Usage")
            st.plotly_chart(fig, use_container_width=True)
        
        # Performance trends
        st.markdown("#### 📈 Performance Trends")
        
        # Create mock trend data
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        trend_data = pd.DataFrame({
            'Date': dates,
            'Searches': [50 + i * 2 + (i % 7) * 10 for i in range(30)],
            'Avg_Time': [100 + (i % 10) * 20 for i in range(30)],
            'Success_Rate': [85 + (i % 15) for i in range(30)]
        })
        
        # Multi-axis chart
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Scatter(x=trend_data['Date'], y=trend_data['Searches'], name="Daily Searches"),
            secondary_y=False,
        )
        
        fig.add_trace(
            go.Scatter(x=trend_data['Date'], y=trend_data['Avg_Time'], name="Avg Search Time (ms)"),
            secondary_y=True,
        )
        
        fig.update_xaxes(title_text="Date")
        fig.update_yaxes(title_text="Number of Searches", secondary_y=False)
        fig.update_yaxes(title_text="Average Search Time (ms)", secondary_y=True)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Search history
        st.markdown("#### 📋 Recent Search History")
        
        search_history = st.session_state.search_ui_state.get('search_history', [])
        if search_history:
            history_df = pd.DataFrame([
                {
                    'Query': h['query'],
                    'Results': h['results_count'],
                    'Time (ms)': f"{h['search_time_ms']:.1f}",
                    'Timestamp': h['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                }
                for h in search_history
            ])
            
            st.dataframe(history_df, use_container_width=True)
        else:
            st.info("No search history available")
        
        # Query analysis
        st.markdown("#### 🔍 Popular Search Terms")
        
        # Mock popular terms
        popular_terms = [
            {'term': 'machine learning', 'count': 45},
            {'term': 'presentation', 'count': 38},
            {'term': 'meeting', 'count': 32},
            {'term': 'interview', 'count': 28},
            {'term': 'training', 'count': 24}
        ]
        
        terms_df = pd.DataFrame(popular_terms)
        fig = px.bar(terms_df, x='term', y='count', 
                    title="Most Popular Search Terms")
        st.plotly_chart(fig, use_container_width=True)
    
    def _get_mock_analytics_data(self) -> Dict[str, Any]:
        """Get mock analytics data for demo"""
        
        return {
            'total_searches': 1247,
            'avg_search_time_ms': 156.7,
            'avg_results_count': 8.3,
            'success_rate': 89.2,
            'strategy_usage': {
                'hybrid': 520,
                'semantic_only': 312,
                'traditional_only': 245,
                'fuzzy_enhanced': 170
            },
            'model_usage': {
                'hybrid_ensemble': 450,
                'neural': 298,
                'bm25': 267,
                'tfidf': 232
            }
        }
    
    def _render_search_settings(self):
        """Render search system settings"""
        
        st.markdown("### ⚙️ Search System Settings")
        
        # Performance settings
        st.markdown("#### ⚡ Performance Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            cache_enabled = st.checkbox(
                "🗃️ Enable Result Caching",
                value=True,
                help="Cache search results for faster subsequent searches"
            )
            
            max_results = st.slider(
                "📊 Maximum Results per Page",
                min_value=5,
                max_value=100,
                value=20,
                step=5
            )
        
        with col2:
            search_timeout = st.slider(
                "⏱️ Search Timeout (seconds)",
                min_value=1,
                max_value=30,
                value=10,
                step=1
            )
            
            enable_analytics = st.checkbox(
                "📈 Enable Analytics Tracking",
                value=True,
                help="Track search queries and performance metrics"
            )
        
        # Default search preferences
        st.markdown("#### 🎯 Default Search Preferences")
        
        pref_col1, pref_col2 = st.columns(2)
        
        with pref_col1:
            default_strategy = st.selectbox(
                "Default Search Strategy",
                options=[s.value for s in SearchStrategy],
                index=0,
                format_func=lambda x: x.replace('_', ' ').title()
            )
            
            default_model = st.selectbox(
                "Default Relevance Model",
                options=[r.value for r in RelevanceModel],
                index=3,
                format_func=lambda x: x.replace('_', ' ').title()
            )
        
        with pref_col2:
            auto_suggest = st.checkbox(
                "💡 Enable Auto-Suggestions",
                value=True,
                help="Show query suggestions as you type"
            )
            
            auto_correct = st.checkbox(
                "✏️ Enable Auto-Correction",
                value=True,
                help="Automatically correct common typos in queries"
            )
        
        # Index management
        st.markdown("#### 🗂️ Search Index Management")
        
        index_col1, index_col2, index_col3 = st.columns(3)
        
        with index_col1:
            if st.button("🔄 Rebuild Search Index"):
                with st.spinner("Rebuilding search index..."):
                    time.sleep(2)  # Simulate rebuild
                st.success("✅ Search index rebuilt successfully!")
        
        with index_col2:
            if st.button("🧹 Clear Search Cache"):
                with st.spinner("Clearing search cache..."):
                    time.sleep(1)  # Simulate cache clear
                st.success("✅ Search cache cleared!")
        
        with index_col3:
            if st.button("📊 Export Analytics"):
                st.success("✅ Analytics exported to CSV!")
        
        # Advanced configuration
        with st.expander("🔧 Advanced Configuration", expanded=False):
            st.markdown("#### 🔬 Experimental Features")
            
            exp_col1, exp_col2 = st.columns(2)
            
            with exp_col1:
                enable_neural_search = st.checkbox(
                    "🧠 Enable Neural Search (Beta)",
                    value=False,
                    help="Use neural networks for semantic understanding"
                )
                
                enable_multilingual = st.checkbox(
                    "🌐 Enable Multilingual Search",
                    value=False,
                    help="Search across different languages"
                )
            
            with exp_col2:
                enable_personalization = st.checkbox(
                    "👤 Enable Search Personalization",
                    value=False,
                    help="Personalize results based on user behavior"
                )
                
                enable_real_time = st.checkbox(
                    "⚡ Enable Real-time Indexing",
                    value=False,
                    help="Index new content immediately"
                )
    
    def _render_help_documentation(self):
        """Render help and documentation"""
        
        st.markdown("### ❓ Advanced Search Help")
        
        # Quick start guide
        st.markdown("#### 🚀 Quick Start Guide")
        
        st.markdown("""
        **Basic Search:**
        - Simply type your query and click Search
        - Use quotes for exact phrases: `"machine learning"`
        - Results are ranked by relevance automatically
        
        **Boolean Search:**
        - Use AND, OR, NOT operators: `python AND machine learning`
        - Group with parentheses: `(AI OR ML) AND tutorial`
        - Exclude terms: `python NOT snake`
        
        **Field Search:**
        - Search specific fields: `speaker:john` or `title:presentation`
        - Combine with other terms: `speaker:sarah machine learning`
        
        **Advanced Features:**
        - Enable semantic search for concept-based results
        - Use facets to filter by content type, duration, etc.
        - Try different relevance models for varied results
        """)
        
        # Search strategies
        st.markdown("#### 🎯 Search Strategies")
        
        strategy_info = {
            'Hybrid': 'Combines semantic understanding with traditional keyword matching',
            'Semantic Only': 'Uses AI to understand meaning and context',
            'Traditional Only': 'Classic keyword-based search with boolean operators',
            'Fuzzy Enhanced': 'Tolerates typos and finds similar terms',
            'Neural Ranking': 'Uses machine learning to rank results'
        }
        
        for strategy, description in strategy_info.items():
            st.markdown(f"**{strategy}**: {description}")
        
        # Relevance models
        st.markdown("#### 📊 Relevance Models")
        
        model_info = {
            'BM25': 'Classic information retrieval ranking function',
            'TF-IDF': 'Term frequency-inverse document frequency scoring',
            'Neural': 'Deep learning-based semantic similarity',
            'Hybrid Ensemble': 'Combines multiple models for best results'
        }
        
        for model, description in model_info.items():
            st.markdown(f"**{model}**: {description}")
        
        # Tips and tricks
        st.markdown("#### 💡 Tips and Tricks")
        
        with st.expander("🔍 Search Tips", expanded=False):
            st.markdown("""
            - **Be specific**: "quarterly sales meeting" vs "meeting"
            - **Use synonyms**: Try different words for the same concept
            - **Filter results**: Use facets to narrow down by type, date, etc.
            - **Check spelling**: Use fuzzy search if you're unsure of spelling
            - **Try different strategies**: Semantic search for concepts, traditional for exact terms
            - **Use field boosting**: Increase importance of title vs content matches
            - **Enable diversification**: Avoid too many similar results
            """)
        
        with st.expander("⚡ Performance Tips", expanded=False):
            st.markdown("""
            - **Use filters**: Narrow search scope for faster results
            - **Limit results**: Don't load too many results at once
            - **Cache frequently used queries**: Enable result caching
            - **Use specific terms**: Avoid very general queries
            - **Optimize index**: Regularly rebuild search index
            """)
        
        # Troubleshooting
        st.markdown("#### 🔧 Troubleshooting")
        
        with st.expander("❓ Common Issues", expanded=False):
            st.markdown("""
            **No results found:**
            - Check spelling and try fuzzy search
            - Use broader terms or synonyms
            - Remove some filters
            - Try different search strategy
            
            **Too many irrelevant results:**
            - Use more specific terms
            - Add filters to narrow scope
            - Use quotes for exact phrases
            - Enable result diversification
            
            **Search is slow:**
            - Reduce number of results per page
            - Use more specific queries
            - Enable caching
            - Check system resources
            
            **Results not as expected:**
            - Try different relevance models
            - Adjust field boosting
            - Use semantic search for concept matching
            - Enable ranking explanation to understand scoring
            """)
        
        # API documentation
        st.markdown("#### 🔌 API Integration")
        
        with st.expander("📚 API Documentation", expanded=False):
            st.code("""
# Example API Usage
from advanced_search_system import AdvancedSearchQuery, SearchStrategy

# Create search query
query = AdvancedSearchQuery(
    query="machine learning presentation",
    search_strategy=SearchStrategy.HYBRID,
    relevance_model=RelevanceModel.HYBRID_ENSEMBLE,
    facets=['content_type', 'duration'],
    diversify_results=True,
    explain_ranking=True
)

# Perform search
results = await search_system.search(query)

# Access results
for result in results.results:
    print(f"Title: {result.title}")
    print(f"Score: {result.score}")
    print(f"Content: {result.content[:100]}...")
            """, language='python')


def demo_advanced_search_ui():
    """Demo the advanced search UI"""
    
    st.set_page_config(
        page_title="Advanced Search System",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize the UI
    search_ui = AdvancedSearchSystemUI()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🔍 Search System")
        st.markdown("Advanced search with semantic understanding, fuzzy matching, and intelligent ranking.")
        
        st.markdown("---")
        
        st.markdown("### 🎯 Quick Actions")
        
        if st.button("🔄 Popular Queries"):
            popular_queries = [
                "machine learning tutorial",
                "team meeting minutes", 
                "presentation slides",
                "technical interview",
                "quarterly review"
            ]
            query_choice = st.selectbox("Select Query", popular_queries)
            if st.button("🔍 Search"):
                st.session_state.main_search_query = query_choice
                st.rerun()
        
        if st.button("📊 View Analytics"):
            st.info("Analytics tab activated")
        
        st.markdown("---")
        
        st.markdown("### 📈 System Status")
        st.success("🟢 Search Engine: Online")
        st.success("🟢 Semantic Models: Loaded")
        st.success("🟢 Index: Up to date")
        st.info("🔄 Cache: 1,247 entries")
    
    # Main interface
    search_ui.render_advanced_search_interface()


if __name__ == "__main__":
    demo_advanced_search_ui()
