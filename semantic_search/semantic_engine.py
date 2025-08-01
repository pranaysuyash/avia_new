"""
Semantic search engine integrating embeddings with traditional search
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import asyncio

from .transcript_embeddings import TranscriptEmbeddingManager, SimilarTranscript

logger = logging.getLogger(__name__)


@dataclass
class SemanticSearchResult:
    """Result from semantic search"""
    transcript_id: str
    title: str
    content_snippet: str
    similarity_score: float
    search_type: str  # 'semantic', 'hybrid', 'recommendation'
    matching_chunks: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'transcript_id': self.transcript_id,
            'title': self.title,
            'content_snippet': self.content_snippet,
            'similarity_score': self.similarity_score,
            'search_type': self.search_type,
            'matching_chunks': self.matching_chunks,
            'metadata': self.metadata
        }


class SemanticSearchEngine:
    """Main semantic search engine"""
    
    def __init__(self, 
                 embedding_manager: Optional[TranscriptEmbeddingManager] = None,
                 traditional_search_manager=None):
        
        self.embedding_manager = embedding_manager or TranscriptEmbeddingManager()
        self.traditional_search = traditional_search_manager
        
    async def semantic_search(self, 
                            query: str,
                            limit: int = 10,
                            min_similarity: float = 0.7) -> List[SemanticSearchResult]:
        """
        Perform semantic search using embeddings
        
        Args:
            query: Search query
            limit: Maximum results
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of semantic search results
        """
        try:
            # Run semantic search
            similar_transcripts = await asyncio.get_event_loop().run_in_executor(
                None,
                self.embedding_manager.search_similar_transcripts,
                query,
                limit,
                min_similarity
            )
            
            # Convert to search results
            results = []
            for transcript in similar_transcripts:
                # Create content snippet from best matching chunk
                content_snippet = ""
                if transcript.matching_chunks:
                    content_snippet = transcript.matching_chunks[0]['text']
                
                result = SemanticSearchResult(
                    transcript_id=transcript.transcript_id,
                    title=transcript.title,
                    content_snippet=content_snippet,
                    similarity_score=transcript.similarity_score,
                    search_type='semantic',
                    matching_chunks=transcript.matching_chunks,
                    metadata=transcript.metadata
                )
                results.append(result)
            
            logger.info(f"Semantic search returned {len(results)} results for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    async def hybrid_search(self, 
                          query: str,
                          limit: int = 10,
                          semantic_weight: float = 0.6,
                          min_similarity: float = 0.5) -> List[SemanticSearchResult]:
        """
        Combine semantic and traditional search results
        
        Args:
            query: Search query
            limit: Maximum results
            semantic_weight: Weight for semantic results (0-1)
            min_similarity: Minimum similarity for semantic results
            
        Returns:
            Combined search results
        """
        try:
            # Run both searches concurrently
            semantic_task = self.semantic_search(query, limit * 2, min_similarity)
            
            # Traditional search (if available)
            traditional_results = []
            if self.traditional_search:
                try:
                    from ..search.search_manager import SearchQuery
                    search_query = SearchQuery(query=query, options={'limit': limit * 2})
                    traditional_search_result = await self.traditional_search.search(search_query)
                    traditional_results = traditional_search_result.results
                except Exception as e:
                    logger.warning(f"Traditional search failed: {e}")
            
            semantic_results = await semantic_task
            
            # Combine and score results
            combined_results = {}
            
            # Add semantic results
            for result in semantic_results:
                score = result.similarity_score * semantic_weight
                combined_results[result.transcript_id] = {
                    'result': result,
                    'score': score,
                    'sources': ['semantic']
                }
            
            # Add traditional results
            traditional_weight = 1.0 - semantic_weight
            for trad_result in traditional_results:
                transcript_id = trad_result.get('doc_id', trad_result.get('transcript_id'))
                
                if transcript_id in combined_results:
                    # Boost score for results found in both searches
                    combined_results[transcript_id]['score'] += 0.5 * traditional_weight
                    combined_results[transcript_id]['sources'].append('traditional')
                else:
                    # Add new traditional result
                    semantic_result = SemanticSearchResult(
                        transcript_id=transcript_id,
                        title=trad_result.get('title', ''),
                        content_snippet=trad_result.get('content_snippet', ''),
                        similarity_score=0.8,  # Default score for traditional results
                        search_type='hybrid',
                        matching_chunks=[],
                        metadata=trad_result.get('metadata', {})
                    )
                    
                    combined_results[transcript_id] = {
                        'result': semantic_result,
                        'score': 0.8 * traditional_weight,
                        'sources': ['traditional']
                    }
            
            # Sort by combined score and return top results
            sorted_results = sorted(
                combined_results.values(),
                key=lambda x: x['score'],
                reverse=True
            )
            
            final_results = []
            for item in sorted_results[:limit]:
                result = item['result']
                result.search_type = 'hybrid'
                result.metadata['search_sources'] = item['sources']
                result.metadata['combined_score'] = item['score']
                final_results.append(result)
            
            logger.info(f"Hybrid search returned {len(final_results)} results")
            return final_results
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return await self.semantic_search(query, limit, min_similarity)
    
    async def find_similar_transcripts(self, 
                                     transcript_id: str,
                                     limit: int = 5,
                                     min_similarity: float = 0.6) -> List[SemanticSearchResult]:
        """
        Find transcripts similar to a given transcript
        
        Args:
            transcript_id: Reference transcript ID
            limit: Maximum results
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of similar transcripts
        """
        try:
            similar_transcripts = await asyncio.get_event_loop().run_in_executor(
                None,
                self.embedding_manager.find_similar_content,
                transcript_id,
                limit,
                min_similarity
            )
            
            results = []
            for transcript in similar_transcripts:
                content_snippet = ""
                if transcript.matching_chunks:
                    content_snippet = transcript.matching_chunks[0]['text']
                
                result = SemanticSearchResult(
                    transcript_id=transcript.transcript_id,
                    title=transcript.title,
                    content_snippet=content_snippet,
                    similarity_score=transcript.similarity_score,
                    search_type='similarity',
                    matching_chunks=transcript.matching_chunks,
                    metadata=transcript.metadata
                )
                results.append(result)
            
            logger.info(f"Found {len(results)} similar transcripts for {transcript_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error finding similar transcripts: {e}")
            return []
    
    async def get_recommendations(self, 
                                user_history: List[str],
                                limit: int = 10) -> List[SemanticSearchResult]:
        """
        Get content recommendations based on user history
        
        Args:
            user_history: List of transcript IDs user has viewed
            limit: Maximum recommendations
            
        Returns:
            List of recommended transcripts
        """
        try:
            recommendations = await asyncio.get_event_loop().run_in_executor(
                None,
                self.embedding_manager.get_content_recommendations,
                user_history,
                limit
            )
            
            results = []
            for transcript in recommendations:
                content_snippet = ""
                if transcript.matching_chunks:
                    content_snippet = transcript.matching_chunks[0]['text']
                
                result = SemanticSearchResult(
                    transcript_id=transcript.transcript_id,
                    title=transcript.title,
                    content_snippet=content_snippet,
                    similarity_score=transcript.similarity_score,
                    search_type='recommendation',
                    matching_chunks=transcript.matching_chunks,
                    metadata=transcript.metadata
                )
                results.append(result)
            
            logger.info(f"Generated {len(results)} recommendations")
            return results
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    async def index_transcript(self, 
                             transcript_id: str,
                             title: str,
                             content: str,
                             metadata: Dict[str, Any] = None) -> bool:
        """
        Index a transcript for semantic search
        
        Args:
            transcript_id: Unique transcript identifier
            title: Transcript title
            content: Full transcript content
            metadata: Additional metadata
            
        Returns:
            True if indexing was successful
        """
        try:
            success = await asyncio.get_event_loop().run_in_executor(
                None,
                self.embedding_manager.index_transcript,
                transcript_id,
                title,
                content,
                metadata
            )
            
            if success:
                logger.info(f"Successfully indexed transcript {transcript_id} for semantic search")
            else:
                logger.error(f"Failed to index transcript {transcript_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error indexing transcript {transcript_id}: {e}")
            return False
    
    async def delete_transcript(self, transcript_id: str) -> bool:
        """
        Delete transcript from semantic search index
        
        Args:
            transcript_id: Transcript to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            success = await asyncio.get_event_loop().run_in_executor(
                None,
                self.embedding_manager.delete_transcript,
                transcript_id
            )
            
            if success:
                logger.info(f"Deleted transcript {transcript_id} from semantic search")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting transcript {transcript_id}: {e}")
            return False
    
    async def batch_index_transcripts(self, 
                                    transcripts: List[Dict[str, Any]]) -> Dict[str, bool]:
        """
        Index multiple transcripts efficiently
        
        Args:
            transcripts: List of transcript dictionaries with id, title, content, metadata
            
        Returns:
            Dictionary mapping transcript IDs to success status
        """
        results = {}
        
        # Process in smaller batches to avoid overwhelming the system
        batch_size = 10
        
        for i in range(0, len(transcripts), batch_size):
            batch = transcripts[i:i + batch_size]
            
            # Process batch concurrently
            tasks = []
            for transcript in batch:
                task = self.index_transcript(
                    transcript['id'],
                    transcript['title'],
                    transcript['content'],
                    transcript.get('metadata', {})
                )
                tasks.append((transcript['id'], task))
            
            # Wait for batch to complete
            for transcript_id, task in tasks:
                try:
                    success = await task
                    results[transcript_id] = success
                except Exception as e:
                    logger.error(f"Error indexing transcript {transcript_id}: {e}")
                    results[transcript_id] = False
        
        successful = sum(1 for success in results.values() if success)
        logger.info(f"Batch indexed {successful}/{len(transcripts)} transcripts")
        
        return results
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get semantic search statistics"""
        try:
            stats = self.embedding_manager.get_stats()
            return {
                'semantic_search_enabled': True,
                'embedding_stats': stats,
                'search_capabilities': [
                    'semantic_search',
                    'similarity_search',
                    'content_recommendations',
                    'hybrid_search'
                ]
            }
        except Exception as e:
            logger.error(f"Error getting search stats: {e}")
            return {'semantic_search_enabled': False}
    
    async def search_within_transcript(self, 
                                     transcript_id: str,
                                     query: str,
                                     limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for specific content within a single transcript
        
        Args:
            transcript_id: Target transcript ID
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching chunks within the transcript
        """
        try:
            # Generate query embedding
            query_embedding = await asyncio.get_event_loop().run_in_executor(
                None,
                self.embedding_manager.embedding_manager.get_embedding,
                query
            )
            
            if query_embedding is None:
                return []
            
            # Search within specific transcript
            import sqlite3
            results = []
            
            with sqlite3.connect(self.embedding_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT chunk_id, text, start_pos, end_pos, embedding
                    FROM transcript_embeddings
                    WHERE transcript_id = ?
                """, (transcript_id,))
                
                for row in cursor.fetchall():
                    chunk_id, text, start_pos, end_pos, embedding_bytes = row
                    
                    # Convert embedding and calculate similarity
                    import numpy as np
                    embedding = np.frombuffer(embedding_bytes, dtype=np.float64)
                    
                    similarity = self.embedding_manager.embedding_manager.compute_similarity(
                        query_embedding, embedding, metric="cosine"
                    )
                    
                    results.append({
                        'chunk_id': chunk_id,
                        'text': text,
                        'start_pos': start_pos,
                        'end_pos': end_pos,
                        'similarity': similarity
                    })
            
            # Sort by similarity and return top results
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching within transcript {transcript_id}: {e}")
            return []