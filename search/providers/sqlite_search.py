"""
SQLite FTS5 search provider implementation
"""

import sqlite3
import json
import logging
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from pathlib import Path

from .base import BaseSearchProvider, SearchDocument

logger = logging.getLogger(__name__)


class SQLiteSearchProvider(BaseSearchProvider):
    """SQLite FTS5 based search provider"""
    
    def __init__(self):
        self.conn = None
        self.db_path = None
        
    def initialize(self, config: Dict[str, Any]):
        """Initialize SQLite database with FTS5"""
        self.db_path = config.get('db_path', 'search_index.db')
        
        # Create directory if needed
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Enable WAL mode for better concurrency
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        
        self._create_schema()
        logger.info(f"SQLite search provider initialized: {self.db_path}")
        
    def _create_schema(self):
        """Create database schema"""
        # Main documents table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # FTS5 virtual table
        self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                doc_id UNINDEXED,
                title,
                content,
                metadata_text,
                tokenize = 'porter unicode61'
            )
        """)
        
        # Indexes for metadata filtering
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_indexed_at 
            ON documents(indexed_at)
        """)
        
        self.conn.commit()
        
    def index_document(self, document: SearchDocument):
        """Index a single document"""
        try:
            # Prepare metadata as searchable text
            metadata_text = self._extract_searchable_metadata(document.metadata)
            
            # Insert into main table
            self.conn.execute("""
                INSERT OR REPLACE INTO documents 
                (doc_id, title, content, metadata)
                VALUES (?, ?, ?, ?)
            """, (
                document.doc_id,
                document.title,
                document.content,
                json.dumps(document.metadata)
            ))
            
            # Insert into FTS table
            self.conn.execute("""
                INSERT OR REPLACE INTO documents_fts 
                (doc_id, title, content, metadata_text)
                VALUES (?, ?, ?, ?)
            """, (
                document.doc_id,
                document.title,
                document.content,
                metadata_text
            ))
            
            self.conn.commit()
            logger.debug(f"Indexed document: {document.doc_id}")
            
        except Exception as e:
            logger.error(f"Error indexing document {document.doc_id}: {e}")
            self.conn.rollback()
            raise
            
    def index_batch(self, documents: List[SearchDocument]):
        """Index multiple documents efficiently"""
        try:
            doc_data = []
            fts_data = []
            
            for doc in documents:
                metadata_text = self._extract_searchable_metadata(doc.metadata)
                
                doc_data.append((
                    doc.doc_id,
                    doc.title,
                    doc.content,
                    json.dumps(doc.metadata)
                ))
                
                fts_data.append((
                    doc.doc_id,
                    doc.title,
                    doc.content,
                    metadata_text
                ))
            
            # Batch insert
            self.conn.executemany("""
                INSERT OR REPLACE INTO documents 
                (doc_id, title, content, metadata)
                VALUES (?, ?, ?, ?)
            """, doc_data)
            
            self.conn.executemany("""
                INSERT OR REPLACE INTO documents_fts 
                (doc_id, title, content, metadata_text)
                VALUES (?, ?, ?, ?)
            """, fts_data)
            
            self.conn.commit()
            logger.info(f"Batch indexed {len(documents)} documents")
            
        except Exception as e:
            logger.error(f"Error batch indexing: {e}")
            self.conn.rollback()
            raise
    
    def search(self, 
               query: str,
               filters: Dict[str, Any] = None,
               limit: int = 50,
               offset: int = 0,
               highlight: bool = True) -> Tuple[List[Dict], int]:
        """Search documents"""
        try:
            # Prepare FTS query
            fts_query = self._prepare_fts_query(query)
            
            # Build base query
            if fts_query:
                # Full-text search
                base_query = """
                    SELECT 
                        d.*,
                        snippet(documents_fts, 1, '<mark>', '</mark>', '...', 30) as title_snippet,
                        snippet(documents_fts, 2, '<mark>', '</mark>', '...', 50) as content_snippet,
                        bm25(documents_fts) as rank
                    FROM documents d
                    JOIN documents_fts ON d.doc_id = documents_fts.doc_id
                    WHERE documents_fts MATCH ?
                """
                params = [fts_query]
            else:
                # Browse mode
                base_query = """
                    SELECT d.*, 
                           d.title as title_snippet,
                           substr(d.content, 1, 200) as content_snippet,
                           0 as rank
                    FROM documents d
                    WHERE 1=1
                """
                params = []
            
            # Apply filters
            filter_clauses, filter_params = self._build_filter_clauses(filters)
            if filter_clauses:
                if "WHERE" in base_query:
                    base_query += " AND " + " AND ".join(filter_clauses)
                else:
                    base_query += " WHERE " + " AND ".join(filter_clauses)
                params.extend(filter_params)
            
            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM ({base_query})"
            cursor = self.conn.execute(count_query, params)
            total_count = cursor.fetchone()['total']
            
            # Add ordering and pagination
            if fts_query:
                base_query += " ORDER BY rank DESC"
            else:
                base_query += " ORDER BY d.indexed_at DESC"
                
            base_query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            # Execute search
            cursor = self.conn.execute(base_query, params)
            results = []
            
            for row in cursor:
                result = {
                    'doc_id': row['doc_id'],
                    'title': row['title'],
                    'content': row['content'],
                    'title_snippet': row['title_snippet'] if highlight else row['title'],
                    'content_snippet': row['content_snippet'] if highlight else row['content'][:200],
                    'rank': row['rank'],
                    'indexed_at': row['indexed_at'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {}
                }
                results.append(result)
            
            return results, total_count
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise
    
    def delete_document(self, doc_id: str):
        """Delete a document from the index"""
        try:
            self.conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
            self.conn.execute("DELETE FROM documents_fts WHERE doc_id = ?", (doc_id,))
            self.conn.commit()
            logger.debug(f"Deleted document: {doc_id}")
            
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            self.conn.rollback()
            raise
    
    def clear_index(self):
        """Clear all documents from the index"""
        try:
            self.conn.execute("DELETE FROM documents")
            self.conn.execute("DELETE FROM documents_fts")
            self.conn.commit()
            logger.info("Cleared all documents from index")
            
        except Exception as e:
            logger.error(f"Error clearing index: {e}")
            self.conn.rollback()
            raise
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("SQLite search provider closed")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        try:
            cursor = self.conn.execute("SELECT COUNT(*) as doc_count FROM documents")
            doc_count = cursor.fetchone()['doc_count']
            
            # Get database size
            db_size = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
            
            return {
                'provider': 'sqlite',
                'document_count': doc_count,
                'index_size_bytes': db_size,
                'index_size_mb': round(db_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'provider': 'sqlite', 'error': str(e)}
    
    def optimize_index(self):
        """Optimize the FTS index"""
        try:
            self.conn.execute("INSERT INTO documents_fts(documents_fts) VALUES('optimize')")
            self.conn.execute("VACUUM")
            self.conn.commit()
            logger.info("Optimized SQLite index")
            
        except Exception as e:
            logger.error(f"Error optimizing index: {e}")
    
    def _extract_searchable_metadata(self, metadata: Dict[str, Any]) -> str:
        """Extract searchable text from metadata"""
        searchable_parts = []
        
        # Extract entities
        if 'entities' in metadata:
            for entity in metadata['entities']:
                if isinstance(entity, dict) and 'text' in entity:
                    searchable_parts.append(entity['text'])
                elif isinstance(entity, str):
                    searchable_parts.append(entity)
        
        # Extract tags
        if 'tags' in metadata:
            if isinstance(metadata['tags'], list):
                searchable_parts.extend(metadata['tags'])
            elif isinstance(metadata['tags'], str):
                searchable_parts.append(metadata['tags'])
        
        # Extract speakers
        if 'speakers' in metadata:
            if isinstance(metadata['speakers'], list):
                searchable_parts.extend(metadata['speakers'])
            elif isinstance(metadata['speakers'], str):
                searchable_parts.append(metadata['speakers'])
        
        # Extract other string fields
        for key, value in metadata.items():
            if key not in ['entities', 'tags', 'speakers'] and isinstance(value, str):
                searchable_parts.append(value)
        
        return ' '.join(str(part) for part in searchable_parts)
    
    def _prepare_fts_query(self, query: str) -> str:
        """Prepare query for FTS5"""
        if not query.strip():
            return ""
        
        # Simple FTS5 query preparation
        # Remove special characters that could break FTS5
        cleaned = query.strip()
        
        # Handle quoted phrases
        if '"' in cleaned:
            return cleaned  # Let FTS5 handle quoted phrases
        
        # Split into terms and join with AND
        terms = cleaned.split()
        if len(terms) > 1:
            return ' AND '.join(terms)
        else:
            return terms[0] if terms else ""
    
    def _build_filter_clauses(self, filters: Dict[str, Any]) -> Tuple[List[str], List[Any]]:
        """Build SQL filter clauses from filters"""
        clauses = []
        params = []
        
        if not filters:
            return clauses, params
        
        # Date range filter
        if 'date_range' in filters:
            date_range = filters['date_range']
            if 'start' in date_range:
                clauses.append("d.indexed_at >= ?")
                params.append(date_range['start'])
            if 'end' in date_range:
                clauses.append("d.indexed_at <= ?")
                params.append(date_range['end'])
        
        # Metadata filters (simple JSON contains check)
        for key in ['tags', 'speakers', 'entity_types']:
            if key in filters and filters[key]:
                values = filters[key] if isinstance(filters[key], list) else [filters[key]]
                for value in values:
                    clauses.append("d.metadata LIKE ?")
                    params.append(f"%{value}%")
        
        return clauses, params