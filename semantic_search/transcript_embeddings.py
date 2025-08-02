"""
Transcript embedding management for semantic search
"""

import logging
import sqlite3
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import hashlib
from pathlib import Path

from .embeddings import EmbeddingManager
from .providers import OpenAIEmbeddingProvider, SentenceTransformerProvider
from .vector_store import create_vector_store, VectorSearchResult

logger = logging.getLogger(__name__)


@dataclass
class TranscriptChunk:
    """Represents a chunk of transcript text"""
    transcript_id: str
    chunk_id: str
    text: str
    start_pos: int
    end_pos: int
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SimilarTranscript:
    """Represents a similar transcript result"""
    transcript_id: str
    title: str
    similarity_score: float
    matching_chunks: List[Dict[str, Any]]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TranscriptEmbeddingManager:
    """Manages embeddings for transcripts with chunking and similarity search"""
    
    def __init__(self, 
                 embedding_provider=None,
                 db_path: str = "transcript_embeddings.db",
                 chunk_size: int = 500,
                 chunk_overlap: int = 50,
                 vector_store_type: str = "faiss"):
        
        # Set up embedding provider
        if embedding_provider is None:
            try:
                embedding_provider = OpenAIEmbeddingProvider()
                logger.info("Using OpenAI embedding provider")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI provider: {e}")
                logger.info("Falling back to SentenceTransformer provider")
                embedding_provider = SentenceTransformerProvider()
        
        self.embedding_manager = EmbeddingManager(embedding_provider)
        self.db_path = db_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize vector store
        dimension = embedding_provider.get_embedding_dimension()
        self.vector_store = create_vector_store(
            store_type=vector_store_type,
            dimension=dimension
        )
        
        # Initialize database for metadata
        self._init_db()
    
    def _init_db(self):
        """Initialize the embedding database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transcript_embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transcript_id TEXT NOT NULL,
                    chunk_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    start_pos INTEGER NOT NULL,
                    end_pos INTEGER NOT NULL,
                    embedding BLOB NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(transcript_id, chunk_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transcript_metadata (
                    transcript_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    embedding_model TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_transcript_id ON transcript_embeddings(transcript_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunk_id ON transcript_embeddings(chunk_id)")
            
            conn.commit()
    
    def index_transcript(self, 
                        transcript_id: str,
                        title: str,
                        content: str,
                        metadata: Dict[str, Any] = None) -> bool:
        """
        Index a transcript by generating embeddings for its chunks
        
        Args:
            transcript_id: Unique identifier for the transcript
            title: Title of the transcript
            content: Full transcript content
            metadata: Additional metadata
            
        Returns:
            True if indexing was successful
        """
        try:
            # Check if transcript already exists and is up to date
            content_hash = self._get_content_hash(content)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT content_hash FROM transcript_metadata WHERE transcript_id = ?",
                    (transcript_id,)
                )
                result = cursor.fetchone()
                
                if result and result[0] == content_hash:
                    logger.info(f"Transcript {transcript_id} already indexed with current content")
                    return True
            
            # Chunk the transcript
            chunks = self._chunk_transcript(transcript_id, content)
            
            if not chunks:
                logger.warning(f"No chunks generated for transcript {transcript_id}")
                return False
            
            # Generate embeddings for chunks
            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = self.embedding_manager.get_embeddings(chunk_texts)
            
            # Delete existing vectors from vector store
            existing_chunk_ids = []
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT chunk_id FROM transcript_embeddings WHERE transcript_id = ?",
                    (transcript_id,)
                )
                existing_chunk_ids = [row[0] for row in cursor.fetchall()]
            
            if existing_chunk_ids:
                self.vector_store.delete(existing_chunk_ids)
            
            # Add new vectors to vector store
            chunk_ids = [chunk.chunk_id for chunk in chunks]
            chunk_metadata = []
            
            for chunk in chunks:
                chunk_meta = {
                    'transcript_id': chunk.transcript_id,
                    'text': chunk.text[:200],  # Store preview in vector store
                    'start_pos': chunk.start_pos,
                    'end_pos': chunk.end_pos,
                    **chunk.metadata
                }
                chunk_metadata.append(chunk_meta)
            
            vector_success = self.vector_store.add_vectors(chunk_ids, embeddings, chunk_metadata)
            
            if not vector_success:
                logger.warning(f"Failed to add vectors to vector store for transcript {transcript_id}")
            
            # Store embeddings in database (for fallback and metadata)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete existing embeddings for this transcript
                cursor.execute(
                    "DELETE FROM transcript_embeddings WHERE transcript_id = ?",
                    (transcript_id,)
                )
                
                # Insert new embeddings
                for chunk, embedding in zip(chunks, embeddings):
                    cursor.execute("""
                        INSERT OR REPLACE INTO transcript_embeddings 
                        (transcript_id, chunk_id, text, start_pos, end_pos, embedding, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        chunk.transcript_id,
                        chunk.chunk_id,
                        chunk.text,
                        chunk.start_pos,
                        chunk.end_pos,
                        embedding.tobytes(),
                        json.dumps(chunk.metadata, default=self._json_serializer)
                    ))
                
                # Update transcript metadata
                cursor.execute("""
                    INSERT OR REPLACE INTO transcript_metadata
                    (transcript_id, title, content_hash, chunk_count, embedding_model, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    transcript_id,
                    title,
                    content_hash,
                    len(chunks),
                    self.embedding_manager.provider.get_model_name(),
                    json.dumps(metadata or {}, default=self._json_serializer)
                ))
                
                conn.commit()
            
            logger.info(f"Successfully indexed transcript {transcript_id} with {len(chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Failed to index transcript {transcript_id}: {e}")
            return False
    
    def search_similar_transcripts(self, 
                                 query: str,
                                 limit: int = 10,
                                 min_similarity: float = 0.7) -> List[SimilarTranscript]:
        """
        Search for transcripts similar to the query
        
        Args:
            query: Search query text
            limit: Maximum number of results
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of similar transcripts
        """
        try:
            # Generate embedding for query
            query_embedding = self.embedding_manager.get_embedding(query)
            
            if query_embedding is None:
                logger.error("Failed to generate query embedding")
                return []
            
            # Search for similar chunks
            similar_chunks = self._find_similar_chunks(
                query_embedding, 
                limit * 3,  # Get more chunks to group by transcript
                min_similarity
            )
            
            # Group chunks by transcript and calculate transcript-level similarity
            transcript_groups = {}
            
            for chunk_data in similar_chunks:
                transcript_id = chunk_data['transcript_id']
                
                if transcript_id not in transcript_groups:
                    transcript_groups[transcript_id] = {
                        'chunks': [],
                        'max_similarity': 0,
                        'avg_similarity': 0
                    }
                
                transcript_groups[transcript_id]['chunks'].append(chunk_data)
                transcript_groups[transcript_id]['max_similarity'] = max(
                    transcript_groups[transcript_id]['max_similarity'],
                    chunk_data['similarity']
                )
            
            # Calculate average similarity for each transcript
            for transcript_id, group in transcript_groups.items():
                similarities = [chunk['similarity'] for chunk in group['chunks']]
                group['avg_similarity'] = sum(similarities) / len(similarities)
            
            # Get transcript metadata and create results
            results = []
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for transcript_id, group in transcript_groups.items():
                    cursor.execute(
                        "SELECT title, metadata FROM transcript_metadata WHERE transcript_id = ?",
                        (transcript_id,)
                    )
                    meta_result = cursor.fetchone()
                    
                    if meta_result:
                        title, metadata_json = meta_result
                        metadata = json.loads(metadata_json) if metadata_json else {}
                        
                        # Use max similarity as the transcript similarity score
                        similarity_score = group['max_similarity']
                        
                        # Format matching chunks
                        matching_chunks = []
                        for chunk in group['chunks'][:3]:  # Top 3 chunks per transcript
                            matching_chunks.append({
                                'text': chunk['text'][:200] + '...' if len(chunk['text']) > 200 else chunk['text'],
                                'similarity': chunk['similarity'],
                                'start_pos': chunk['start_pos'],
                                'end_pos': chunk['end_pos']
                            })
                        
                        results.append(SimilarTranscript(
                            transcript_id=transcript_id,
                            title=title,
                            similarity_score=similarity_score,
                            matching_chunks=matching_chunks,
                            metadata=metadata
                        ))
            
            # Sort by similarity score and limit results
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching similar transcripts: {e}")
            return []
    
    def find_similar_content(self, 
                           transcript_id: str,
                           limit: int = 5,
                           min_similarity: float = 0.6) -> List[SimilarTranscript]:
        """
        Find transcripts similar to a given transcript
        
        Args:
            transcript_id: ID of the reference transcript
            limit: Maximum number of results
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of similar transcripts
        """
        try:
            # Get embeddings for the reference transcript
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT embedding FROM transcript_embeddings 
                    WHERE transcript_id = ?
                """, (transcript_id,))
                
                embedding_rows = cursor.fetchall()
                
                if not embedding_rows:
                    logger.warning(f"No embeddings found for transcript {transcript_id}")
                    return []
                
                # Calculate average embedding for the transcript
                embeddings = [np.frombuffer(row[0], dtype=np.float64) for row in embedding_rows]
                avg_embedding = np.mean(embeddings, axis=0)
            
            # Search for similar transcripts using the average embedding
            similar_chunks = self._find_similar_chunks(
                avg_embedding,
                limit * 5,  # Get more chunks to find diverse transcripts
                min_similarity
            )
            
            # Filter out the reference transcript and group results
            filtered_chunks = [
                chunk for chunk in similar_chunks 
                if chunk['transcript_id'] != transcript_id
            ]
            
            # Group by transcript and create results
            transcript_groups = {}
            
            for chunk_data in filtered_chunks:
                tid = chunk_data['transcript_id']
                
                if tid not in transcript_groups:
                    transcript_groups[tid] = {
                        'chunks': [],
                        'max_similarity': 0
                    }
                
                transcript_groups[tid]['chunks'].append(chunk_data)
                transcript_groups[tid]['max_similarity'] = max(
                    transcript_groups[tid]['max_similarity'],
                    chunk_data['similarity']
                )
            
            # Create results
            results = []
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for tid, group in transcript_groups.items():
                    cursor.execute(
                        "SELECT title, metadata FROM transcript_metadata WHERE transcript_id = ?",
                        (tid,)
                    )
                    meta_result = cursor.fetchone()
                    
                    if meta_result:
                        title, metadata_json = meta_result
                        metadata = json.loads(metadata_json) if metadata_json else {}
                        
                        matching_chunks = []
                        for chunk in group['chunks'][:2]:  # Top 2 chunks per transcript
                            matching_chunks.append({
                                'text': chunk['text'][:150] + '...' if len(chunk['text']) > 150 else chunk['text'],
                                'similarity': chunk['similarity'],
                                'start_pos': chunk['start_pos'],
                                'end_pos': chunk['end_pos']
                            })
                        
                        results.append(SimilarTranscript(
                            transcript_id=tid,
                            title=title,
                            similarity_score=group['max_similarity'],
                            matching_chunks=matching_chunks,
                            metadata=metadata
                        ))
            
            # Sort and limit results
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error finding similar content for transcript {transcript_id}: {e}")
            return []
    
    def get_content_recommendations(self, 
                                  user_history: List[str],
                                  limit: int = 10) -> List[SimilarTranscript]:
        """
        Get content recommendations based on user's transcript history
        
        Args:
            user_history: List of transcript IDs the user has viewed
            limit: Maximum number of recommendations
            
        Returns:
            List of recommended transcripts
        """
        if not user_history:
            return []
        
        try:
            # Get embeddings for user's history
            all_embeddings = []
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for transcript_id in user_history[-5:]:  # Use last 5 transcripts
                    cursor.execute("""
                        SELECT embedding FROM transcript_embeddings 
                        WHERE transcript_id = ?
                    """, (transcript_id,))
                    
                    embedding_rows = cursor.fetchall()
                    
                    for row in embedding_rows:
                        embedding = np.frombuffer(row[0], dtype=np.float64)
                        all_embeddings.append(embedding)
            
            if not all_embeddings:
                return []
            
            # Calculate user preference vector (average of history embeddings)
            preference_vector = np.mean(all_embeddings, axis=0)
            
            # Find similar content
            similar_chunks = self._find_similar_chunks(
                preference_vector,
                limit * 3,
                min_similarity=0.5  # Lower threshold for recommendations
            )
            
            # Filter out transcripts from user history
            filtered_chunks = [
                chunk for chunk in similar_chunks 
                if chunk['transcript_id'] not in user_history
            ]
            
            # Group and create recommendations
            transcript_groups = {}
            
            for chunk_data in filtered_chunks:
                tid = chunk_data['transcript_id']
                
                if tid not in transcript_groups:
                    transcript_groups[tid] = {
                        'chunks': [chunk_data],
                        'max_similarity': chunk_data['similarity']
                    }
                else:
                    transcript_groups[tid]['chunks'].append(chunk_data)
                    transcript_groups[tid]['max_similarity'] = max(
                        transcript_groups[tid]['max_similarity'],
                        chunk_data['similarity']
                    )
            
            # Create results
            results = []
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for tid, group in transcript_groups.items():
                    cursor.execute(
                        "SELECT title, metadata FROM transcript_metadata WHERE transcript_id = ?",
                        (tid,)
                    )
                    meta_result = cursor.fetchone()
                    
                    if meta_result:
                        title, metadata_json = meta_result
                        metadata = json.loads(metadata_json) if metadata_json else {}
                        
                        matching_chunks = []
                        for chunk in group['chunks'][:1]:  # Top chunk per transcript
                            matching_chunks.append({
                                'text': chunk['text'][:100] + '...' if len(chunk['text']) > 100 else chunk['text'],
                                'similarity': chunk['similarity'],
                                'start_pos': chunk['start_pos'],
                                'end_pos': chunk['end_pos']
                            })
                        
                        results.append(SimilarTranscript(
                            transcript_id=tid,
                            title=title,
                            similarity_score=group['max_similarity'],
                            matching_chunks=matching_chunks,
                            metadata=metadata
                        ))
            
            # Sort and limit results
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error generating content recommendations: {e}")
            return []
    
    def _chunk_transcript(self, transcript_id: str, content: str) -> List[TranscriptChunk]:
        """Split transcript into overlapping chunks"""
        if not content.strip():
            return []
        
        words = content.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            # Calculate character positions
            start_pos = len(' '.join(words[:i])) + (1 if i > 0 else 0)
            end_pos = start_pos + len(chunk_text)
            
            chunk_id = f"{transcript_id}_chunk_{len(chunks)}"
            
            chunks.append(TranscriptChunk(
                transcript_id=transcript_id,
                chunk_id=chunk_id,
                text=chunk_text,
                start_pos=start_pos,
                end_pos=end_pos,
                metadata={'chunk_index': len(chunks)}
            ))
        
        return chunks
    
    def _find_similar_chunks(self, 
                           query_embedding: np.ndarray,
                           limit: int,
                           min_similarity: float) -> List[Dict[str, Any]]:
        """Find chunks similar to the query embedding using vector store"""
        try:
            # Search in vector store
            vector_results = self.vector_store.search(query_embedding, k=limit * 2)
            
            # Convert to expected format and filter by similarity
            results = []
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for vector_result in vector_results:
                    if vector_result.score < min_similarity:
                        continue
                    
                    # Get chunk details from database
                    cursor.execute("""
                        SELECT transcript_id, text, start_pos, end_pos
                        FROM transcript_embeddings
                        WHERE chunk_id = ?
                    """, (vector_result.id,))
                    
                    row = cursor.fetchone()
                    if row:
                        transcript_id, text, start_pos, end_pos = row
                        
                        results.append({
                            'transcript_id': transcript_id,
                            'chunk_id': vector_result.id,
                            'text': text,
                            'start_pos': start_pos,
                            'end_pos': end_pos,
                            'similarity': vector_result.score
                        })
                        
                        if len(results) >= limit:
                            break
            
            return results
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            # Fallback to original method if vector store fails
            return self._find_similar_chunks_fallback(query_embedding, limit, min_similarity)
    
    def _find_similar_chunks_fallback(self, 
                                    query_embedding: np.ndarray,
                                    limit: int,
                                    min_similarity: float) -> List[Dict[str, Any]]:
        """Fallback method using SQLite similarity calculation"""
        results = []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT transcript_id, chunk_id, text, start_pos, end_pos, embedding
                FROM transcript_embeddings
            """)
            
            for row in cursor.fetchall():
                transcript_id, chunk_id, text, start_pos, end_pos, embedding_bytes = row
                
                # Convert embedding from bytes
                embedding = np.frombuffer(embedding_bytes, dtype=np.float64)
                
                # Calculate similarity
                similarity = self.embedding_manager.compute_similarity(
                    query_embedding, embedding, metric="cosine"
                )
                
                if similarity >= min_similarity:
                    results.append({
                        'transcript_id': transcript_id,
                        'chunk_id': chunk_id,
                        'text': text,
                        'start_pos': start_pos,
                        'end_pos': end_pos,
                        'similarity': similarity
                    })
        
        # Sort by similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:limit]
    
    def _get_content_hash(self, content: str) -> str:
        """Generate hash for content to detect changes"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def _json_serializer(self, obj):
        """JSON serializer for datetime objects"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    def delete_transcript(self, transcript_id: str) -> bool:
        """Delete transcript embeddings"""
        try:
            # Get chunk IDs to delete from vector store
            chunk_ids = []
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT chunk_id FROM transcript_embeddings WHERE transcript_id = ?",
                    (transcript_id,)
                )
                chunk_ids = [row[0] for row in cursor.fetchall()]
                
                # Delete from database
                cursor.execute(
                    "DELETE FROM transcript_embeddings WHERE transcript_id = ?",
                    (transcript_id,)
                )
                cursor.execute(
                    "DELETE FROM transcript_metadata WHERE transcript_id = ?",
                    (transcript_id,)
                )
                conn.commit()
            
            # Delete from vector store
            if chunk_ids:
                vector_success = self.vector_store.delete(chunk_ids)
                if not vector_success:
                    logger.warning(f"Failed to delete vectors from vector store for transcript {transcript_id}")
            
            logger.info(f"Deleted embeddings for transcript {transcript_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting transcript embeddings: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get embedding database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM transcript_metadata")
                transcript_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM transcript_embeddings")
                chunk_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT AVG(chunk_count) FROM transcript_metadata")
                avg_chunks = cursor.fetchone()[0] or 0
            
            # Get vector store stats
            vector_stats = self.vector_store.get_stats()
            
            return {
                'total_transcripts': transcript_count,
                'total_chunks': chunk_count,
                'avg_chunks_per_transcript': round(avg_chunks, 2),
                'embedding_model': self.embedding_manager.provider.get_model_name(),
                'embedding_dimension': self.embedding_manager.provider.get_embedding_dimension(),
                'database_path': self.db_path,
                'vector_store': vector_stats
            }
                
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}