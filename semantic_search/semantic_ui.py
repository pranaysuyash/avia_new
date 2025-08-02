"""
Streamlit UI components for semantic search functionality
"""

import streamlit as st
import asyncio
import logging
from typing import List, Dict, Any, Optional
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

from .semantic_engine import SemanticSearchEngine, SemanticSearchResult
from .transcript_library import TranscriptLibrary, TranscriptEntry, TranscriptMetadata

logger = logging.getLogger(__name__)


class SemanticSearchUI:
    """UI components for semantic search"""
    
    def __init__(self, search_engine: SemanticSearchEngine = None, transcript_library: TranscriptLibrary = None):
        self.search_engine = search_engine or SemanticSearchEngine()
        self.transcript_library = transcript_library or TranscriptLibrary()
    
    def render_semantic_search_interface(self):
        """Render the main semantic search interface"""
        st.subheader("🔍 Semantic Search")
        
        # Search input
        col1, col2 = st.columns([3, 1])
        
        with col1:
            query = st.text_input(
                "Search transcripts by meaning",
                placeholder="e.g., 'discussions about project deadlines' or 'customer complaints'",
                help="Use natural language to find transcripts with similar meaning"
            )
        
        with col2:
            search_type = st.selectbox(
                "Search Type",
                ["Semantic", "Hybrid", "Traditional"],
                help="Semantic: AI-powered meaning search\nHybrid: Combines semantic + keyword\nTraditional: Keyword-based"
            )
        
        # Advanced options
        with st.expander("Advanced Options"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                limit = st.slider("Max Results", 5, 50, 10)
            
            with col2:
                min_similarity = st.slider("Min Similarity", 0.1, 1.0, 0.7, 0.1)
            
            with col3:
                if search_type == "Hybrid":
                    semantic_weight = st.slider("Semantic Weight", 0.0, 1.0, 0.6, 0.1)
                else:
                    semantic_weight = 0.6
        
        # Search button and results
        if st.button("Search", type="primary") and query:
            with st.spinner("Searching transcripts..."):
                results = self._perform_search(
                    query, search_type, limit, min_similarity, semantic_weight
                )
                
                if results:
                    self._display_search_results(results, query)
                else:
                    st.info("No results found. Try adjusting your search terms or similarity threshold.")
    
    def render_similarity_finder(self):
        """Render interface for finding similar transcripts"""
        st.subheader("🔗 Find Similar Transcripts")
        
        # Transcript selection
        transcript_id = st.text_input(
            "Transcript ID",
            placeholder="Enter transcript ID to find similar content",
            help="Find transcripts with similar content to a specific transcript"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            limit = st.slider("Max Similar Results", 3, 20, 5, key="similarity_limit")
        
        with col2:
            min_similarity = st.slider("Min Similarity", 0.1, 1.0, 0.6, 0.1, key="similarity_threshold")
        
        if st.button("Find Similar", type="primary") and transcript_id:
            with st.spinner("Finding similar transcripts..."):
                results = self._find_similar_transcripts(transcript_id, limit, min_similarity)
                
                if results:
                    self._display_similarity_results(results, transcript_id)
                else:
                    st.info("No similar transcripts found or transcript ID not found.")
    
    def render_recommendations(self):
        """Render content recommendations interface"""
        st.subheader("💡 Content Recommendations")
        
        # User history input
        st.write("Get personalized recommendations based on your viewing history:")
        
        history_input = st.text_area(
            "Transcript History (one ID per line)",
            placeholder="transcript_1\ntranscript_2\ntranscript_3",
            help="Enter transcript IDs you've viewed, one per line"
        )
        
        limit = st.slider("Number of Recommendations", 5, 20, 10, key="rec_limit")
        
        if st.button("Get Recommendations", type="primary") and history_input:
            history = [tid.strip() for tid in history_input.split('\n') if tid.strip()]
            
            if history:
                with st.spinner("Generating recommendations..."):
                    results = self._get_recommendations(history, limit)
                    
                    if results:
                        self._display_recommendations(results, history)
                    else:
                        st.info("No recommendations available. Try adding more transcript IDs to your history.")
    
    def render_search_analytics(self):
        """Render search analytics and statistics"""
        st.subheader("📊 Search Analytics")
        
        # Get search statistics
        stats = self.search_engine.get_search_stats()
        
        if stats.get('semantic_search_enabled'):
            embedding_stats = stats.get('embedding_stats', {})
            
            # Display key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Indexed Transcripts",
                    embedding_stats.get('total_transcripts', 0)
                )
            
            with col2:
                st.metric(
                    "Total Chunks",
                    embedding_stats.get('total_chunks', 0)
                )
            
            with col3:
                st.metric(
                    "Avg Chunks/Transcript",
                    embedding_stats.get('avg_chunks_per_transcript', 0)
                )
            
            with col4:
                st.metric(
                    "Embedding Dimension",
                    embedding_stats.get('embedding_dimension', 0)
                )
            
            # Model information
            st.write("**Embedding Model:**", embedding_stats.get('embedding_model', 'Unknown'))
            
            # Capabilities
            capabilities = stats.get('search_capabilities', [])
            if capabilities:
                st.write("**Available Search Types:**")
                for capability in capabilities:
                    st.write(f"• {capability.replace('_', ' ').title()}")
        else:
            st.error("Semantic search is not enabled or configured properly.")
    
    def render_transcript_library(self):
        """Render the transcript library interface"""
        st.subheader("📚 Transcript Library")
        
        # Library statistics
        stats = self.transcript_library.get_library_stats()
        
        if stats:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Transcripts", stats.get('total_transcripts', 0))
            
            with col2:
                st.metric("Total Duration", f"{stats.get('total_duration_hours', 0):.1f}h")
            
            with col3:
                st.metric("Categories", stats.get('unique_categories', 0))
            
            with col4:
                st.metric("Languages", stats.get('unique_languages', 0))
        
        # Search and filter interface
        col1, col2 = st.columns([2, 1])
        
        with col1:
            search_query = st.text_input(
                "Search Library",
                placeholder="Search transcripts by content, title, or tags...",
                help="Use natural language or keywords to search your transcript library"
            )
        
        with col2:
            search_type = st.selectbox(
                "Search Method",
                ["Hybrid", "Semantic", "Full-text"],
                help="Hybrid combines semantic and keyword search"
            )
        
        # Advanced filters
        with st.expander("🔍 Advanced Filters"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                category_filter = st.selectbox(
                    "Category",
                    ["All"] + list(stats.get('category_breakdown', {}).keys()),
                    help="Filter by transcript category"
                )
            
            with col2:
                language_filter = st.selectbox(
                    "Language",
                    ["All"] + list(stats.get('language_breakdown', {}).keys()),
                    help="Filter by transcript language"
                )
            
            with col3:
                source_filter = st.selectbox(
                    "Source",
                    ["All", "upload", "recording", "batch"],
                    help="Filter by how transcript was created"
                )
            
            # Duration filter
            col1, col2 = st.columns(2)
            with col1:
                min_duration = st.number_input("Min Duration (minutes)", min_value=0, value=0)
            with col2:
                max_duration = st.number_input("Max Duration (minutes)", min_value=0, value=0)
        
        # Search button and results
        if st.button("Search Library", type="primary") or search_query:
            filters = {}
            if category_filter != "All":
                filters['category'] = category_filter
            if language_filter != "All":
                filters['language'] = language_filter
            if source_filter != "All":
                filters['source'] = source_filter
            if min_duration > 0:
                filters['min_duration'] = min_duration * 60
            if max_duration > 0:
                filters['max_duration'] = max_duration * 60
            
            if search_query:
                with st.spinner("Searching library..."):
                    results = self.transcript_library.search_transcripts(
                        search_query,
                        search_type.lower().replace('-', ''),
                        limit=20,
                        filters=filters
                    )
                    
                    if results:
                        self._display_library_results(results, search_query)
                    else:
                        st.info("No transcripts found matching your search criteria.")
            else:
                # Show recent transcripts
                with st.spinner("Loading recent transcripts..."):
                    results = self.transcript_library.list_transcripts(
                        limit=20,
                        filters=filters
                    )
                    
                    if results:
                        st.write("**Recent Transcripts:**")
                        self._display_library_results(results)
                    else:
                        st.info("No transcripts found in your library.")
    
    def render_transcript_indexer(self):
        """Render interface for indexing transcripts"""
        st.subheader("📝 Add to Library")
        
        st.write("Add transcripts to your searchable library:")
        
        # Single transcript indexing
        with st.expander("Add Single Transcript", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                transcript_id = st.text_input("Transcript ID", key="index_id")
                title = st.text_input("Title", key="index_title")
                category = st.text_input("Category", key="index_category", placeholder="e.g., Meeting, Interview, Lecture")
            
            with col2:
                language = st.selectbox("Language", ["en", "es", "fr", "de", "it", "pt", "zh", "ja"], key="index_language")
                source = st.selectbox("Source", ["upload", "recording", "batch"], key="index_source")
                tags_input = st.text_input("Tags (comma-separated)", key="index_tags", placeholder="tag1, tag2, tag3")
            
            content = st.text_area("Content", height=200, key="index_content", placeholder="Paste transcript content here...")
            
            # Optional metadata
            with st.expander("Optional Metadata"):
                col1, col2 = st.columns(2)
                with col1:
                    duration = st.number_input("Duration (minutes)", min_value=0.0, key="index_duration")
                    file_path = st.text_input("File Path", key="index_file_path")
                with col2:
                    file_size = st.number_input("File Size (MB)", min_value=0.0, key="index_file_size")
                    speaker_count = st.number_input("Speaker Count", min_value=1, key="index_speakers")
            
            if st.button("Add to Library", type="primary") and all([transcript_id, title, content]):
                with st.spinner("Adding transcript to library..."):
                    # Parse tags
                    tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()] if tags_input else []
                    
                    # Create transcript entry
                    metadata = TranscriptMetadata(
                        transcript_id=transcript_id,
                        title=title,
                        duration=duration * 60 if duration > 0 else None,
                        file_size=int(file_size * 1024 * 1024) if file_size > 0 else None,
                        language=language,
                        speaker_count=speaker_count if speaker_count > 0 else None,
                        tags=tags,
                        category=category if category else None,
                        source=source,
                        file_path=file_path if file_path else None
                    )
                    
                    transcript_entry = TranscriptEntry(
                        metadata=metadata,
                        content=content
                    )
                    
                    success = self.transcript_library.add_transcript(transcript_entry)
                    
                    if success:
                        st.success(f"Successfully added transcript to library: {transcript_id}")
                        # Clear form
                        for key in ['index_id', 'index_title', 'index_content', 'index_category', 'index_tags']:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()
                    else:
                        st.error("Failed to add transcript to library. Check logs for details.")
        
        # Batch indexing
        with st.expander("Batch Add Transcripts"):
            st.write("Upload a JSON file with transcript data:")
            
            uploaded_file = st.file_uploader(
                "Choose JSON file",
                type=['json'],
                help="JSON format: [{'id': 'transcript_1', 'title': 'Title', 'content': 'Content', 'metadata': {}}]"
            )
            
            if uploaded_file and st.button("Batch Add"):
                with st.spinner("Processing batch add..."):
                    success_count = self._batch_add_transcripts(uploaded_file)
                    
                    if success_count > 0:
                        st.success(f"Successfully added {success_count} transcripts to library")
                    else:
                        st.error("Failed to add transcripts. Check file format and logs.")
    
    def render_content_discovery(self):
        """Render content discovery and recommendations interface"""
        st.subheader("🔍 Content Discovery")
        
        tab1, tab2, tab3 = st.tabs(["Similar Content", "Recommendations", "Trending Topics"])
        
        with tab1:
            st.write("Find transcripts similar to a specific one:")
            
            # Get list of available transcripts
            recent_transcripts = self.transcript_library.list_transcripts(limit=50)
            transcript_options = {f"{t.metadata.title} ({t.metadata.transcript_id})": t.metadata.transcript_id 
                                for t in recent_transcripts}
            
            if transcript_options:
                selected_transcript = st.selectbox(
                    "Select Reference Transcript",
                    options=list(transcript_options.keys()),
                    help="Find transcripts with similar content"
                )
                
                similarity_limit = st.slider("Number of Similar Transcripts", 3, 15, 5)
                
                if st.button("Find Similar Content"):
                    reference_id = transcript_options[selected_transcript]
                    
                    with st.spinner("Finding similar transcripts..."):
                        similar_transcripts = self.transcript_library.find_similar_transcripts(
                            reference_id, similarity_limit
                        )
                        
                        if similar_transcripts:
                            self._display_similar_content(similar_transcripts, reference_id)
                        else:
                            st.info("No similar transcripts found.")
            else:
                st.info("No transcripts available in your library yet.")
        
        with tab2:
            st.write("Get personalized recommendations based on your viewing history:")
            
            # User history input
            if 'user_transcript_history' not in st.session_state:
                st.session_state.user_transcript_history = []
            
            # Show current history
            if st.session_state.user_transcript_history:
                st.write("**Your Recent Activity:**")
                for i, tid in enumerate(st.session_state.user_transcript_history[-5:]):
                    transcript = self.transcript_library.get_transcript(tid)
                    if transcript:
                        st.write(f"• {transcript.metadata.title}")
            
            # Add to history
            if transcript_options:
                add_to_history = st.selectbox(
                    "Add to History",
                    [""] + list(transcript_options.keys()),
                    help="Add transcripts you've viewed to get better recommendations"
                )
                
                if add_to_history and st.button("Add to History"):
                    tid = transcript_options[add_to_history]
                    if tid not in st.session_state.user_transcript_history:
                        st.session_state.user_transcript_history.append(tid)
                        st.success("Added to your history!")
                        st.rerun()
            
            # Generate recommendations
            if st.session_state.user_transcript_history:
                rec_limit = st.slider("Number of Recommendations", 5, 20, 10)
                
                if st.button("Get Recommendations"):
                    with st.spinner("Generating personalized recommendations..."):
                        recommendations = self.transcript_library.get_recommendations(
                            st.session_state.user_transcript_history, rec_limit
                        )
                        
                        if recommendations:
                            self._display_recommendations_enhanced(recommendations)
                        else:
                            st.info("No recommendations available. Try adding more transcripts to your history.")
            else:
                st.info("Add some transcripts to your history to get personalized recommendations.")
        
        with tab3:
            st.write("Discover trending topics and popular content:")
            
            # Get library stats for trending analysis
            stats = self.transcript_library.get_library_stats()
            
            if stats.get('category_breakdown'):
                st.write("**Popular Categories:**")
                category_df = pd.DataFrame(
                    list(stats['category_breakdown'].items()),
                    columns=['Category', 'Count']
                )
                
                fig = px.bar(
                    category_df,
                    x='Count',
                    y='Category',
                    orientation='h',
                    title="Transcripts by Category"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            if stats.get('language_breakdown'):
                st.write("**Language Distribution:**")
                lang_df = pd.DataFrame(
                    list(stats['language_breakdown'].items()),
                    columns=['Language', 'Count']
                )
                
                fig = px.pie(
                    lang_df,
                    values='Count',
                    names='Language',
                    title="Transcripts by Language"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    def _perform_search(self, 
                       query: str, 
                       search_type: str, 
                       limit: int, 
                       min_similarity: float,
                       semantic_weight: float) -> List[SemanticSearchResult]:
        """Perform search based on type"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            if search_type == "Semantic":
                results = loop.run_until_complete(
                    self.search_engine.semantic_search(query, limit, min_similarity)
                )
            elif search_type == "Hybrid":
                results = loop.run_until_complete(
                    self.search_engine.hybrid_search(query, limit, semantic_weight, min_similarity)
                )
            else:  # Traditional - fallback to semantic for now
                results = loop.run_until_complete(
                    self.search_engine.semantic_search(query, limit, min_similarity)
                )
            
            loop.close()
            return results
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            st.error(f"Search failed: {str(e)}")
            return []
    
    def _find_similar_transcripts(self, 
                                transcript_id: str, 
                                limit: int, 
                                min_similarity: float) -> List[SemanticSearchResult]:
        """Find similar transcripts"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            results = loop.run_until_complete(
                self.search_engine.find_similar_transcripts(transcript_id, limit, min_similarity)
            )
            
            loop.close()
            return results
            
        except Exception as e:
            logger.error(f"Similarity search error: {e}")
            st.error(f"Similarity search failed: {str(e)}")
            return []
    
    def _get_recommendations(self, 
                           history: List[str], 
                           limit: int) -> List[SemanticSearchResult]:
        """Get content recommendations"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            results = loop.run_until_complete(
                self.search_engine.get_recommendations(history, limit)
            )
            
            loop.close()
            return results
            
        except Exception as e:
            logger.error(f"Recommendations error: {e}")
            st.error(f"Recommendations failed: {str(e)}")
            return []
    
    def _index_transcript(self, transcript_id: str, title: str, content: str) -> bool:
        """Index a single transcript"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            success = loop.run_until_complete(
                self.search_engine.index_transcript(transcript_id, title, content)
            )
            
            loop.close()
            return success
            
        except Exception as e:
            logger.error(f"Indexing error: {e}")
            st.error(f"Indexing failed: {str(e)}")
            return False
    
    def _batch_add_transcripts(self, uploaded_file) -> int:
        """Batch add transcripts from uploaded file"""
        try:
            import json
            
            # Read and parse JSON file
            content = uploaded_file.read()
            transcripts_data = json.loads(content)
            
            if not isinstance(transcripts_data, list):
                st.error("JSON file must contain a list of transcript objects")
                return 0
            
            # Validate format
            required_fields = ['id', 'title', 'content']
            for i, transcript_data in enumerate(transcripts_data):
                if not all(field in transcript_data for field in required_fields):
                    st.error(f"Transcript {i} missing required fields: {required_fields}")
                    return 0
            
            # Process each transcript
            success_count = 0
            
            for transcript_data in transcripts_data:
                try:
                    # Create metadata
                    metadata = TranscriptMetadata(
                        transcript_id=transcript_data['id'],
                        title=transcript_data['title'],
                        language=transcript_data.get('language', 'en'),
                        category=transcript_data.get('category'),
                        source=transcript_data.get('source', 'batch'),
                        tags=transcript_data.get('tags', []),
                        duration=transcript_data.get('duration'),
                        file_size=transcript_data.get('file_size'),
                        speaker_count=transcript_data.get('speaker_count')
                    )
                    
                    # Create transcript entry
                    transcript_entry = TranscriptEntry(
                        metadata=metadata,
                        content=transcript_data['content'],
                        entities=transcript_data.get('entities', {}),
                        speaker_segments=transcript_data.get('speaker_segments', []),
                        analysis_results=transcript_data.get('analysis_results', {})
                    )
                    
                    # Add to library
                    if self.transcript_library.add_transcript(transcript_entry):
                        success_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing transcript {transcript_data.get('id', 'unknown')}: {e}")
                    continue
            
            return success_count
            
        except json.JSONDecodeError:
            st.error("Invalid JSON file format")
            return 0
        except Exception as e:
            logger.error(f"Batch add error: {e}")
            st.error(f"Batch add failed: {str(e)}")
            return 0
    
    def _display_library_results(self, results: List[TranscriptEntry], query: str = None):
        """Display transcript library search results"""
        if query:
            st.write(f"**Found {len(results)} transcripts for:** *{query}*")
        else:
            st.write(f"**Showing {len(results)} transcripts:**")
        
        # Create results visualization
        if len(results) > 1 and query:
            df = pd.DataFrame([
                {
                    'Title': r.metadata.title[:30] + '...' if len(r.metadata.title) > 30 else r.metadata.title,
                    'Score': r.analysis_results.get('search_score', 0),
                    'Category': r.metadata.category or 'Uncategorized',
                    'Duration': f"{r.metadata.duration/60:.1f}m" if r.metadata.duration else 'Unknown'
                }
                for r in results if r.analysis_results.get('search_score', 0) > 0
            ])
            
            if not df.empty:
                fig = px.bar(
                    df, 
                    x='Score', 
                    y='Title',
                    color='Category',
                    orientation='h',
                    title="Search Results by Relevance Score",
                    hover_data=['Duration']
                )
                fig.update_layout(height=min(400, len(df) * 40 + 100))
                st.plotly_chart(fig, use_container_width=True)
        
        # Display individual results
        for i, transcript in enumerate(results):
            metadata = transcript.metadata
            
            # Create expandable result
            score_text = ""
            if transcript.analysis_results.get('search_score'):
                score = transcript.analysis_results['search_score']
                search_type = transcript.analysis_results.get('search_type', 'unknown')
                score_text = f" (Score: {score:.3f}, Type: {search_type})"
            
            with st.expander(f"📄 {metadata.title}{score_text}"):
                # Metadata display
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**ID:** {metadata.transcript_id}")
                    st.write(f"**Category:** {metadata.category or 'Uncategorized'}")
                    st.write(f"**Language:** {metadata.language}")
                
                with col2:
                    if metadata.duration:
                        st.write(f"**Duration:** {metadata.duration/60:.1f} minutes")
                    if metadata.speaker_count:
                        st.write(f"**Speakers:** {metadata.speaker_count}")
                    st.write(f"**Source:** {metadata.source or 'Unknown'}")
                
                with col3:
                    if metadata.created_at:
                        st.write(f"**Created:** {metadata.created_at.strftime('%Y-%m-%d %H:%M')}")
                    if metadata.file_size:
                        st.write(f"**File Size:** {metadata.file_size/(1024*1024):.1f} MB")
                
                # Tags
                if metadata.tags:
                    st.write("**Tags:**")
                    tag_cols = st.columns(min(len(metadata.tags), 4))
                    for j, tag in enumerate(metadata.tags):
                        with tag_cols[j % 4]:
                            st.badge(tag)
                
                # Content preview
                st.write("**Content Preview:**")
                preview_length = 300
                content_preview = transcript.content[:preview_length]
                if len(transcript.content) > preview_length:
                    content_preview += "..."
                st.write(content_preview)
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button(f"View Full Content", key=f"view_{metadata.transcript_id}"):
                        st.session_state[f"show_full_{metadata.transcript_id}"] = True
                
                with col2:
                    if st.button(f"Find Similar", key=f"similar_{metadata.transcript_id}"):
                        similar = self.transcript_library.find_similar_transcripts(metadata.transcript_id, 5)
                        if similar:
                            st.write("**Similar Transcripts:**")
                            for sim in similar:
                                score = sim.analysis_results.get('similarity_score', 0)
                                st.write(f"• {sim.metadata.title} (Similarity: {score:.3f})")
                
                with col3:
                    if st.button(f"Delete", key=f"delete_{metadata.transcript_id}"):
                        if self.transcript_library.delete_transcript(metadata.transcript_id):
                            st.success("Transcript deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete transcript")
                
                # Show full content if requested
                if st.session_state.get(f"show_full_{metadata.transcript_id}"):
                    st.write("**Full Content:**")
                    st.text_area("", value=transcript.content, height=300, key=f"full_content_{metadata.transcript_id}")
                    if st.button(f"Hide Full Content", key=f"hide_{metadata.transcript_id}"):
                        st.session_state[f"show_full_{metadata.transcript_id}"] = False
                        st.rerun()
    
    def _display_similar_content(self, similar_transcripts: List[TranscriptEntry], reference_id: str):
        """Display similar content results"""
        st.write(f"**Found {len(similar_transcripts)} transcripts similar to reference transcript:**")
        
        # Get reference transcript info
        reference = self.transcript_library.get_transcript(reference_id)
        if reference:
            st.info(f"**Reference:** {reference.metadata.title}")
        
        # Similarity visualization
        if similar_transcripts:
            df = pd.DataFrame([
                {
                    'Title': t.metadata.title[:25] + '...' if len(t.metadata.title) > 25 else t.metadata.title,
                    'Similarity': t.analysis_results.get('similarity_score', 0),
                    'Category': t.metadata.category or 'Uncategorized'
                }
                for t in similar_transcripts
            ])
            
            fig = px.bar(
                df,
                x='Similarity',
                y='Title',
                color='Category',
                orientation='h',
                title=f"Content Similar to {reference.metadata.title if reference else reference_id}"
            )
            fig.update_layout(height=min(300, len(similar_transcripts) * 40 + 100))
            st.plotly_chart(fig, use_container_width=True)
        
        # Display results
        for transcript in similar_transcripts:
            similarity_score = transcript.analysis_results.get('similarity_score', 0)
            
            with st.expander(f"📄 {transcript.metadata.title} (Similarity: {similarity_score:.3f})"):
                st.write(f"**Transcript ID:** {transcript.metadata.transcript_id}")
                st.write(f"**Category:** {transcript.metadata.category or 'Uncategorized'}")
                
                # Content preview
                st.write("**Content Preview:**")
                preview = transcript.content[:200] + '...' if len(transcript.content) > 200 else transcript.content
                st.write(preview)
    
    def _display_recommendations_enhanced(self, recommendations: List[TranscriptEntry]):
        """Display enhanced content recommendations"""
        st.write(f"**{len(recommendations)} personalized recommendations:**")
        
        # Recommendation visualization
        if recommendations:
            df = pd.DataFrame([
                {
                    'Title': r.metadata.title[:30] + '...' if len(r.metadata.title) > 30 else r.metadata.title,
                    'Score': r.analysis_results.get('recommendation_score', 0),
                    'Category': r.metadata.category or 'Uncategorized',
                    'Duration': f"{r.metadata.duration/60:.1f}m" if r.metadata.duration else 'Unknown'
                }
                for r in recommendations
            ])
            
            fig = px.scatter(
                df,
                x='Score',
                y='Title',
                color='Category',
                size=[1] * len(df),  # Uniform size
                title="Personalized Recommendations",
                hover_data=['Duration']
            )
            fig.update_layout(height=min(400, len(recommendations) * 30 + 100))
            st.plotly_chart(fig, use_container_width=True)
        
        # Display recommendations
        for i, transcript in enumerate(recommendations, 1):
            score = transcript.analysis_results.get('recommendation_score', 0)
            
            with st.expander(f"💡 Recommendation {i}: {transcript.metadata.title} (Score: {score:.3f})"):
                st.write(f"**Transcript ID:** {transcript.metadata.transcript_id}")
                st.write(f"**Category:** {transcript.metadata.category or 'Uncategorized'}")
                st.write(f"**Why recommended:** Based on your viewing history and content similarity")
                
                if transcript.metadata.duration:
                    st.write(f"**Duration:** {transcript.metadata.duration/60:.1f} minutes")
                
                # Content preview
                st.write("**Preview:**")
                preview = transcript.content[:150] + '...' if len(transcript.content) > 150 else transcript.content
                st.write(preview)
                
                # Add to history button
                if st.button(f"Mark as Viewed", key=f"viewed_{transcript.metadata.transcript_id}"):
                    if 'user_transcript_history' not in st.session_state:
                        st.session_state.user_transcript_history = []
                    
                    if transcript.metadata.transcript_id not in st.session_state.user_transcript_history:
                        st.session_state.user_transcript_history.append(transcript.metadata.transcript_id)
                        st.success("Added to your viewing history!")
                        st.rerun()
    
    def _display_search_results(self, results: List[SemanticSearchResult], query: str):
        """Display search results"""
        st.write(f"**Found {len(results)} results for:** *{query}*")
        
        # Create similarity score chart
        if len(results) > 1:
            df = pd.DataFrame([
                {
                    'Transcript': r.title[:30] + '...' if len(r.title) > 30 else r.title,
                    'Similarity': r.similarity_score,
                    'Type': r.search_type
                }
                for r in results
            ])
            
            fig = px.bar(
                df, 
                x='Similarity', 
                y='Transcript',
                color='Type',
                orientation='h',
                title="Search Results by Similarity Score"
            )
            fig.update_layout(height=min(400, len(results) * 40 + 100))
            st.plotly_chart(fig, use_container_width=True)
        
        # Display individual results
        for i, result in enumerate(results):
            with st.expander(f"📄 {result.title} (Similarity: {result.similarity_score:.3f})"):
                st.write(f"**Transcript ID:** {result.transcript_id}")
                st.write(f"**Search Type:** {result.search_type}")
                
                if result.content_snippet:
                    st.write("**Content Preview:**")
                    st.write(result.content_snippet)
                
                if result.matching_chunks:
                    st.write("**Matching Sections:**")
                    for j, chunk in enumerate(result.matching_chunks[:3]):
                        st.write(f"*Section {j+1} (Similarity: {chunk['similarity']:.3f}):*")
                        st.write(chunk['text'])
                        st.write("---")
                
                if result.metadata:
                    with st.expander("Metadata"):
                        st.json(result.metadata)
    
    def _display_similarity_results(self, results: List[SemanticSearchResult], reference_id: str):
        """Display similarity search results"""
        st.write(f"**Found {len(results)} transcripts similar to:** *{reference_id}*")
        
        # Similarity visualization
        if results:
            df = pd.DataFrame([
                {
                    'Transcript': r.title[:25] + '...' if len(r.title) > 25 else r.title,
                    'Similarity': r.similarity_score
                }
                for r in results
            ])
            
            fig = px.bar(
                df,
                x='Similarity',
                y='Transcript',
                orientation='h',
                title=f"Transcripts Similar to {reference_id}"
            )
            fig.update_layout(height=min(300, len(results) * 40 + 100))
            st.plotly_chart(fig, use_container_width=True)
        
        # Display results
        for result in results:
            with st.expander(f"📄 {result.title} (Similarity: {result.similarity_score:.3f})"):
                st.write(f"**Transcript ID:** {result.transcript_id}")
                
                if result.matching_chunks:
                    st.write("**Similar Content:**")
                    for chunk in result.matching_chunks[:2]:
                        st.write(f"*Similarity: {chunk['similarity']:.3f}*")
                        st.write(chunk['text'])
                        st.write("---")
    
    def _display_recommendations(self, results: List[SemanticSearchResult], history: List[str]):
        """Display content recommendations"""
        st.write(f"**{len(results)} recommendations based on {len(history)} transcripts in your history:**")
        
        # Show history
        with st.expander("Your History"):
            for tid in history:
                st.write(f"• {tid}")
        
        # Display recommendations
        for i, result in enumerate(results, 1):
            with st.expander(f"💡 Recommendation {i}: {result.title} (Score: {result.similarity_score:.3f})"):
                st.write(f"**Transcript ID:** {result.transcript_id}")
                st.write(f"**Why recommended:** Based on similarity to your viewing history")
                
                if result.content_snippet:
                    st.write("**Preview:**")
                    st.write(result.content_snippet)
                
                if result.matching_chunks:
                    st.write("**Relevant Content:**")
                    for chunk in result.matching_chunks[:1]:
                        st.write(chunk['text'])


def render_semantic_search_page():
    """Render the complete semantic search page"""
    st.title("🧠 Semantic Search & Transcript Library")
    
    # Initialize search engine and library
    try:
        transcript_library = TranscriptLibrary()
        search_engine = SemanticSearchEngine(transcript_library.embedding_manager)
        ui = SemanticSearchUI(search_engine, transcript_library)
        
        # Sidebar navigation
        st.sidebar.title("Search & Library Features")
        feature = st.sidebar.radio(
            "Choose Feature",
            [
                "Transcript Library",
                "Semantic Search", 
                "Content Discovery",
                "Add to Library",
                "Analytics"
            ]
        )
        
        # Render selected feature
        if feature == "Transcript Library":
            ui.render_transcript_library()
        elif feature == "Semantic Search":
            ui.render_semantic_search_interface()
        elif feature == "Content Discovery":
            ui.render_content_discovery()
        elif feature == "Add to Library":
            ui.render_transcript_indexer()
        elif feature == "Analytics":
            ui.render_search_analytics()
            
    except Exception as e:
        st.error(f"Failed to initialize semantic search: {str(e)}")
        st.write("Please check your configuration and API keys.")
        logger.error(f"Semantic search initialization error: {e}")


if __name__ == "__main__":
    render_semantic_search_page()