"""
Transcript library management for searchable transcript collection
"""

import logging
import sqlite3
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import hashlib

from .transcript_embeddings import TranscriptEmbeddingManager, SimilarTranscript
from .semantic_engine import SemanticSearchEngine

logger = logging.getLogger(__name__)


@dataclass
class TranscriptMetadata:
    """Metadata for a transcript in the library"""
    transcript_id: str
    title: str
    file_path: Optional[str] = None
    duration: Optional[float] = None
    file_size: Optional[int] = None
    language: str = "en"
    speaker_count: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tags: List[str] = None
    category: Optional[str] = None
    source: Optional[str] = None  # 'upload', 'recording', 'batch'
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class TranscriptEntry:
    """Complete transcript entry with content and metadata"""
    metadata: TranscriptMetadata
    content: str
    entities: Dict[str, Any] = None
    speaker_segments: List[Dict[str, Any]] = None
    analysis_results: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.entities is None:
            self.entities = {}
        if self.speaker_segments is None:
            self.speaker_segments = []
        if self.analysis_results is None:
            self.analysis_results = {}


class TranscriptLibrary:
    """Manages a searchable library of transcripts"""
    
    def __init__(self, 
                 db_path: str = "transcript_library.db",
                 embedding_manager: Optional[TranscriptEmbeddingManager] = None):
        self.db_path = db_path
        self.embedding_manager = embedding_manager or TranscriptEmbeddingManager()
        self.search_engine = SemanticSearchEngine(self.embedding_manager)
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize the transcript library database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transcript_library (
                    transcript_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    file_path TEXT,
                    duration REAL,
                    file_size INTEGER,
                    language TEXT DEFAULT 'en',
                    speaker_count INTEGER,
                    tags TEXT,  -- JSON array
                    category TEXT,
                    source TEXT,
                    entities TEXT,  -- JSON object
                    speaker_segments TEXT,  -- JSON array
                    analysis_results TEXT,  -- JSON object
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better search performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_title ON transcript_library(title)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON transcript_library(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_language ON transcript_library(language)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON transcript_library(created_at)")
            
            # Full-text search index for content
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS transcript_fts USING fts5(
                    transcript_id,
                    title,
                    content,
                    tags,
                    category
                )
            """)
            
            conn.commit()
    
    def add_transcript(self, transcript: TranscriptEntry) -> bool:
        """
        Add a transcript to the library
        
        Args:
            transcript: TranscriptEntry object
            
        Returns:
            True if successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert into main table
                cursor.execute("""
                    INSERT OR REPLACE INTO transcript_library
                    (transcript_id, title, content, file_path, duration, file_size,
                     language, speaker_count, tags, category, source, entities,
                     speaker_segments, analysis_results, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transcript.metadata.transcript_id,
                    transcript.metadata.title,
                    transcript.content,
                    transcript.metadata.file_path,
                    transcript.metadata.duration,
                    transcript.metadata.file_size,
                    transcript.metadata.language,
                    transcript.metadata.speaker_count,
                    json.dumps(transcript.metadata.tags),
                    transcript.metadata.category,
                    transcript.metadata.source,
                    json.dumps(transcript.entities),
                    json.dumps(transcript.speaker_segments),
                    json.dumps(transcript.analysis_results),
                    transcript.metadata.created_at,
                    transcript.metadata.updated_at
                ))
                
                # Insert into FTS table
                cursor.execute("""
                    INSERT OR REPLACE INTO transcript_fts
                    (transcript_id, title, content, tags, category)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    transcript.metadata.transcript_id,
                    transcript.metadata.title,
                    transcript.content,
                    ' '.join(transcript.metadata.tags),
                    transcript.metadata.category or ''
                ))
                
                conn.commit()
            
            # Index for semantic search
            success = self.embedding_manager.index_transcript(
                transcript.metadata.transcript_id,
                transcript.metadata.title,
                transcript.content,
                asdict(transcript.metadata)
            )
            
            if success:
                logger.info(f"Added transcript to library: {transcript.metadata.transcript_id}")
                return True
            else:
                logger.error(f"Failed to index transcript for semantic search: {transcript.metadata.transcript_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding transcript to library: {e}")
            return False
    
    def get_transcript(self, transcript_id: str) -> Optional[TranscriptEntry]:
        """
        Get a transcript by ID
        
        Args:
            transcript_id: Transcript identifier
            
        Returns:
            TranscriptEntry if found, None otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM transcript_library WHERE transcript_id = ?
                """, (transcript_id,))
                
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_transcript_entry(row)
                    
                return None
                
        except Exception as e:
            logger.error(f"Error getting transcript {transcript_id}: {e}")
            return None
    
    def search_transcripts(self, 
                          query: str,
                          search_type: str = "hybrid",
                          limit: int = 10,
                          filters: Dict[str, Any] = None) -> List[TranscriptEntry]:
        """
        Search transcripts using various methods
        
        Args:
            query: Search query
            search_type: 'semantic', 'fulltext', 'hybrid'
            limit: Maximum results
            filters: Additional filters (category, language, etc.)
            
        Returns:
            List of matching transcripts
        """
        try:
            if search_type == "semantic":
                return self._semantic_search(query, limit, filters)
            elif search_type == "fulltext":
                return self._fulltext_search(query, limit, filters)
            elif search_type == "hybrid":
                return self._hybrid_search(query, limit, filters)
            else:
                raise ValueError(f"Unknown search type: {search_type}")
                
        except Exception as e:
            logger.error(f"Error searching transcripts: {e}")
            return []
    
    def find_similar_transcripts(self, 
                               transcript_id: str,
                               limit: int = 5) -> List[TranscriptEntry]:
        """
        Find transcripts similar to a given transcript
        
        Args:
            transcript_id: Reference transcript ID
            limit: Maximum results
            
        Returns:
            List of similar transcripts
        """
        try:
            similar_results = self.embedding_manager.find_similar_content(
                transcript_id, limit
            )
            
            transcripts = []
            for result in similar_results:
                transcript = self.get_transcript(result.transcript_id)
                if transcript:
                    # Add similarity score to metadata
                    transcript.analysis_results['similarity_score'] = result.similarity_score
                    transcripts.append(transcript)
            
            return transcripts
            
        except Exception as e:
            logger.error(f"Error finding similar transcripts: {e}")
            return []
    
    def get_recommendations(self, 
                          user_history: List[str],
                          limit: int = 10) -> List[TranscriptEntry]:
        """
        Get content recommendations based on user history
        
        Args:
            user_history: List of transcript IDs user has viewed
            limit: Maximum recommendations
            
        Returns:
            List of recommended transcripts
        """
        try:
            recommendations = self.embedding_manager.get_content_recommendations(
                user_history, limit
            )
            
            transcripts = []
            for result in recommendations:
                transcript = self.get_transcript(result.transcript_id)
                if transcript:
                    # Add recommendation score to metadata
                    transcript.analysis_results['recommendation_score'] = result.similarity_score
                    transcripts.append(transcript)
            
            return transcripts
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []
    
    def list_transcripts(self, 
                        limit: int = 50,
                        offset: int = 0,
                        filters: Dict[str, Any] = None) -> List[TranscriptEntry]:
        """
        List transcripts with optional filters
        
        Args:
            limit: Maximum results
            offset: Results offset for pagination
            filters: Optional filters
            
        Returns:
            List of transcripts
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build query with filters
                where_clauses = []
                params = []
                
                if filters:
                    if 'category' in filters:
                        where_clauses.append("category = ?")
                        params.append(filters['category'])
                    
                    if 'language' in filters:
                        where_clauses.append("language = ?")
                        params.append(filters['language'])
                    
                    if 'source' in filters:
                        where_clauses.append("source = ?")
                        params.append(filters['source'])
                    
                    if 'min_duration' in filters:
                        where_clauses.append("duration >= ?")
                        params.append(filters['min_duration'])
                    
                    if 'max_duration' in filters:
                        where_clauses.append("duration <= ?")
                        params.append(filters['max_duration'])
                
                where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
                
                query = f"""
                    SELECT * FROM transcript_library
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """
                
                params.extend([limit, offset])
                cursor.execute(query, params)
                
                rows = cursor.fetchall()
                return [self._row_to_transcript_entry(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error listing transcripts: {e}")
            return []
    
    def delete_transcript(self, transcript_id: str) -> bool:
        """
        Delete a transcript from the library
        
        Args:
            transcript_id: Transcript to delete
            
        Returns:
            True if successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete from main table
                cursor.execute(
                    "DELETE FROM transcript_library WHERE transcript_id = ?",
                    (transcript_id,)
                )
                
                # Delete from FTS table
                cursor.execute(
                    "DELETE FROM transcript_fts WHERE transcript_id = ?",
                    (transcript_id,)
                )
                
                conn.commit()
            
            # Delete from semantic search index
            self.embedding_manager.delete_transcript(transcript_id)
            
            logger.info(f"Deleted transcript from library: {transcript_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting transcript: {e}")
            return False
    
    def get_library_stats(self) -> Dict[str, Any]:
        """Get library statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Basic counts
                cursor.execute("SELECT COUNT(*) FROM transcript_library")
                total_transcripts = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT category) FROM transcript_library WHERE category IS NOT NULL")
                unique_categories = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT language) FROM transcript_library")
                unique_languages = cursor.fetchone()[0]
                
                # Duration statistics
                cursor.execute("SELECT AVG(duration), SUM(duration) FROM transcript_library WHERE duration IS NOT NULL")
                duration_stats = cursor.fetchone()
                avg_duration = duration_stats[0] or 0
                total_duration = duration_stats[1] or 0
                
                # File size statistics
                cursor.execute("SELECT AVG(file_size), SUM(file_size) FROM transcript_library WHERE file_size IS NOT NULL")
                size_stats = cursor.fetchone()
                avg_size = size_stats[0] or 0
                total_size = size_stats[1] or 0
                
                # Category breakdown
                cursor.execute("""
                    SELECT category, COUNT(*) 
                    FROM transcript_library 
                    WHERE category IS NOT NULL 
                    GROUP BY category 
                    ORDER BY COUNT(*) DESC
                """)
                category_breakdown = dict(cursor.fetchall())
                
                # Language breakdown
                cursor.execute("""
                    SELECT language, COUNT(*) 
                    FROM transcript_library 
                    GROUP BY language 
                    ORDER BY COUNT(*) DESC
                """)
                language_breakdown = dict(cursor.fetchall())
                
                # Get embedding stats
                embedding_stats = self.embedding_manager.get_stats()
                
                return {
                    'total_transcripts': total_transcripts,
                    'unique_categories': unique_categories,
                    'unique_languages': unique_languages,
                    'avg_duration_minutes': round(avg_duration / 60, 2) if avg_duration else 0,
                    'total_duration_hours': round(total_duration / 3600, 2) if total_duration else 0,
                    'avg_file_size_mb': round(avg_size / (1024 * 1024), 2) if avg_size else 0,
                    'total_file_size_gb': round(total_size / (1024 * 1024 * 1024), 2) if total_size else 0,
                    'category_breakdown': category_breakdown,
                    'language_breakdown': language_breakdown,
                    'embedding_stats': embedding_stats,
                    'database_path': self.db_path
                }
                
        except Exception as e:
            logger.error(f"Error getting library stats: {e}")
            return {}
    
    def _semantic_search(self, query: str, limit: int, filters: Dict[str, Any]) -> List[TranscriptEntry]:
        """Perform semantic search"""
        import asyncio
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(
                self.search_engine.semantic_search(query, limit)
            )
            
            transcripts = []
            for result in results:
                transcript = self.get_transcript(result.transcript_id)
                if transcript and self._matches_filters(transcript, filters):
                    transcript.analysis_results['search_score'] = result.similarity_score
                    transcript.analysis_results['search_type'] = 'semantic'
                    transcripts.append(transcript)
            
            return transcripts
            
        finally:
            loop.close()
    
    def _fulltext_search(self, query: str, limit: int, filters: Dict[str, Any]) -> List[TranscriptEntry]:
        """Perform full-text search"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # FTS search
                cursor.execute("""
                    SELECT transcript_id, rank
                    FROM transcript_fts
                    WHERE transcript_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """, (query, limit * 2))  # Get more results to apply filters
                
                results = cursor.fetchall()
                
                transcripts = []
                for transcript_id, rank in results:
                    transcript = self.get_transcript(transcript_id)
                    if transcript and self._matches_filters(transcript, filters):
                        transcript.analysis_results['search_score'] = 1.0 / (1.0 + rank)  # Convert rank to score
                        transcript.analysis_results['search_type'] = 'fulltext'
                        transcripts.append(transcript)
                        
                        if len(transcripts) >= limit:
                            break
                
                return transcripts
                
        except Exception as e:
            logger.error(f"Error in fulltext search: {e}")
            return []
    
    def _hybrid_search(self, query: str, limit: int, filters: Dict[str, Any]) -> List[TranscriptEntry]:
        """Perform hybrid search combining semantic and fulltext"""
        # Get results from both methods
        semantic_results = self._semantic_search(query, limit, filters)
        fulltext_results = self._fulltext_search(query, limit, filters)
        
        # Combine and deduplicate
        combined = {}
        
        # Add semantic results with higher weight
        for transcript in semantic_results:
            tid = transcript.metadata.transcript_id
            semantic_score = transcript.analysis_results.get('search_score', 0)
            combined[tid] = {
                'transcript': transcript,
                'score': semantic_score * 0.7  # 70% weight for semantic
            }
        
        # Add fulltext results
        for transcript in fulltext_results:
            tid = transcript.metadata.transcript_id
            fulltext_score = transcript.analysis_results.get('search_score', 0)
            
            if tid in combined:
                # Boost score for results found in both
                combined[tid]['score'] += fulltext_score * 0.3  # 30% weight for fulltext
                combined[tid]['transcript'].analysis_results['search_type'] = 'hybrid'
            else:
                combined[tid] = {
                    'transcript': transcript,
                    'score': fulltext_score * 0.3
                }
        
        # Sort by combined score and return
        sorted_results = sorted(
            combined.values(),
            key=lambda x: x['score'],
            reverse=True
        )
        
        final_results = []
        for item in sorted_results[:limit]:
            transcript = item['transcript']
            transcript.analysis_results['search_score'] = item['score']
            if 'search_type' not in transcript.analysis_results:
                transcript.analysis_results['search_type'] = 'hybrid'
            final_results.append(transcript)
        
        return final_results
    
    def _matches_filters(self, transcript: TranscriptEntry, filters: Dict[str, Any]) -> bool:
        """Check if transcript matches filters"""
        if not filters:
            return True
        
        metadata = transcript.metadata
        
        if 'category' in filters and metadata.category != filters['category']:
            return False
        
        if 'language' in filters and metadata.language != filters['language']:
            return False
        
        if 'source' in filters and metadata.source != filters['source']:
            return False
        
        if 'min_duration' in filters and (not metadata.duration or metadata.duration < filters['min_duration']):
            return False
        
        if 'max_duration' in filters and (not metadata.duration or metadata.duration > filters['max_duration']):
            return False
        
        return True
    
    def _row_to_transcript_entry(self, row) -> TranscriptEntry:
        """Convert database row to TranscriptEntry"""
        (transcript_id, title, content, file_path, duration, file_size,
         language, speaker_count, tags_json, category, source, entities_json,
         speaker_segments_json, analysis_results_json, created_at, updated_at) = row
        
        # Parse JSON fields
        tags = json.loads(tags_json) if tags_json else []
        entities = json.loads(entities_json) if entities_json else {}
        speaker_segments = json.loads(speaker_segments_json) if speaker_segments_json else []
        analysis_results = json.loads(analysis_results_json) if analysis_results_json else {}
        
        # Parse timestamps
        created_at = datetime.fromisoformat(created_at) if created_at else None
        updated_at = datetime.fromisoformat(updated_at) if updated_at else None
        
        metadata = TranscriptMetadata(
            transcript_id=transcript_id,
            title=title,
            file_path=file_path,
            duration=duration,
            file_size=file_size,
            language=language,
            speaker_count=speaker_count,
            tags=tags,
            category=category,
            source=source,
            created_at=created_at,
            updated_at=updated_at
        )
        
        return TranscriptEntry(
            metadata=metadata,
            content=content,
            entities=entities,
            speaker_segments=speaker_segments,
            analysis_results=analysis_results
        )