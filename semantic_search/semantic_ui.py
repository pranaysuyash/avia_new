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

from .semantic_engine import SemanticSearchEngine, SemanticSearchResult

logger = logging.getLogger(__name__)


class SemanticSearchUI:
    """UI components for semantic search"""
    
    def __init__(self, search_engine: SemanticSearchEngine):
        self.search_engine = search_engine
    
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
    
    def render_transcript_indexer(self):
        """Render interface for indexing transcripts"""
        st.subheader("📝 Index Transcripts")
        
        st.write("Add transcripts to the semantic search index:")
        
        # Single transcript indexing
        with st.expander("Index Single Transcript"):
            transcript_id = st.text_input("Transcript ID", key="index_id")
            title = st.text_input("Title", key="index_title")
            content = st.text_area("Content", height=200, key="index_content")
            
            if st.button("Index Transcript") and all([transcript_id, title, content]):
                with st.spinner("Indexing transcript..."):
                    success = self._index_transcript(transcript_id, title, content)
                    
                    if success:
                        st.success(f"Successfully indexed transcript: {transcript_id}")
                    else:
                        st.error("Failed to index transcript. Check logs for details.")
        
        # Batch indexing
        with st.expander("Batch Index Transcripts"):
            st.write("Upload a JSON file with transcript data:")
            
            uploaded_file = st.file_uploader(
                "Choose JSON file",
                type=['json'],
                help="JSON format: [{'id': 'transcript_1', 'title': 'Title', 'content': 'Content', 'metadata': {}}]"
            )
            
            if uploaded_file and st.button("Batch Index"):
                with st.spinner("Processing batch index..."):
                    success_count = self._batch_index_transcripts(uploaded_file)
                    
                    if success_count > 0:
                        st.success(f"Successfully indexed {success_count} transcripts")
                    else:
                        st.error("Failed to index transcripts. Check file format and logs.")
    
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
    
    def _batch_index_transcripts(self, uploaded_file) -> int:
        """Batch index transcripts from uploaded file"""
        try:
            import json
            
            # Read and parse JSON file
            content = uploaded_file.read()
            transcripts = json.loads(content)
            
            if not isinstance(transcripts, list):
                st.error("JSON file must contain a list of transcript objects")
                return 0
            
            # Validate format
            required_fields = ['id', 'title', 'content']
            for i, transcript in enumerate(transcripts):
                if not all(field in transcript for field in required_fields):
                    st.error(f"Transcript {i} missing required fields: {required_fields}")
                    return 0
            
            # Batch index
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            results = loop.run_until_complete(
                self.search_engine.batch_index_transcripts(transcripts)
            )
            
            loop.close()
            
            # Count successful indexing
            success_count = sum(1 for success in results.values() if success)
            return success_count
            
        except json.JSONDecodeError:
            st.error("Invalid JSON file format")
            return 0
        except Exception as e:
            logger.error(f"Batch indexing error: {e}")
            st.error(f"Batch indexing failed: {str(e)}")
            return 0
    
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
    st.title("🧠 Semantic Search & Recommendations")
    
    # Initialize search engine
    try:
        search_engine = SemanticSearchEngine()
        ui = SemanticSearchUI(search_engine)
        
        # Sidebar navigation
        st.sidebar.title("Search Features")
        feature = st.sidebar.radio(
            "Choose Feature",
            [
                "Semantic Search",
                "Find Similar",
                "Recommendations",
                "Index Transcripts",
                "Analytics"
            ]
        )
        
        # Render selected feature
        if feature == "Semantic Search":
            ui.render_semantic_search_interface()
        elif feature == "Find Similar":
            ui.render_similarity_finder()
        elif feature == "Recommendations":
            ui.render_recommendations()
        elif feature == "Index Transcripts":
            ui.render_transcript_indexer()
        elif feature == "Analytics":
            ui.render_search_analytics()
            
    except Exception as e:
        st.error(f"Failed to initialize semantic search: {str(e)}")
        st.write("Please check your configuration and API keys.")


if __name__ == "__main__":
    render_semantic_search_page()