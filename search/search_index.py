"""
Search indexing system using SQLite FTS5 for full-text search
"""

import sqlite3
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class DocumentIndex:
    """Represents a searchable document"""
    
    def __init__(self, 
                 doc_id: str,
                 title: str,
                 content: str,
                 metadata: Dict[str, Any] = None):
        self.doc_id = doc_id
        self.title = title
        self.content = content
        self.metadata = metadata or {}
        self.indexed_at = datetime.utcnow()
        
        # Extract searchable fields from metadata
        self.entities = metadata.get('entities', []) if metadata else []
        self.tags = metadata.get('tags', []) if metadata else []
        self.speakers = metadata.get('speakers', []) if metadata else []
        self.language = metadata.get('language', 'en') if metadata else 'en'
        self.created_at = metadata.get('created_at') if metadata else None
        self.confidence = metadata.get('confidence', 1.0) if metadata else 1.0


class SearchIndex:
    """SQLite FTS5 based search index"""
    
    def __init__(self, db_path: str = "search_index.db"):
        self.db_path = db_path
        self.conn = None
        self._initialize_database()
        
    def _initialize_database(self):
        """Initialize SQLite database with FTS5 tables"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Enable FTS5 extension
        self.conn.execute("PRAGMA journal_mode=WAL")
        
        # Create main documents table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                entities TEXT,
                tags TEXT,
                speakers TEXT,
                language TEXT,
                confidence REAL,
                created_at TIMESTAMP,
                indexed_at TIMESTAMP,
                metadata TEXT
            )
        """)
        
        # Create FTS5 virtual table for full-text search
        self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                doc_id UNINDEXED,
                title,
                content,
                entities,
                tags,
                speakers,
                tokenize = 'porter unicode61'
            )
        """)
        
        # Create indexes for filtering
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at ON documents(created_at)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_language ON documents(language)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_confidence ON documents(confidence)
        """)
        
        # Create saved searches table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS saved_searches (
                search_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                query TEXT NOT NULL,
                filters TEXT,
                created_at TIMESTAMP,
                last_used TIMESTAMP,
                use_count INTEGER DEFAULT 0
            )
        """)
        
        # Create search history table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                filters TEXT,
                result_count INTEGER,
                searched_at TIMESTAMP,
                search_time_ms INTEGER
            )
        """)
        
        self.conn.commit()
        logger.info(f"Search index initialized at {self.db_path}")
        
    def index_document(self, document: DocumentIndex):
        """Index a single document"""
        try:
            # Prepare data
            entities_str = ' '.join([e.get('text', '') for e in document.entities])
            tags_str = ' '.join(document.tags)
            speakers_str = ' '.join(document.speakers)
            
            # Insert into main table
            self.conn.execute("""
                INSERT OR REPLACE INTO documents 
                (doc_id, title, content, entities, tags, speakers, language, 
                 confidence, created_at, indexed_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document.doc_id,
                document.title,
                document.content,
                entities_str,
                tags_str,
                speakers_str,
                document.language,
                document.confidence,
                document.created_at,
                document.indexed_at,
                json.dumps(document.metadata)
            ))
            
            # Insert into FTS table
            self.conn.execute("""
                INSERT OR REPLACE INTO documents_fts 
                (doc_id, title, content, entities, tags, speakers)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                document.doc_id,
                document.title,
                document.content,
                entities_str,
                tags_str,
                speakers_str
            ))
            
            self.conn.commit()
            logger.info(f"Indexed document: {document.doc_id}")
            
        except Exception as e:
            logger.error(f"Error indexing document {document.doc_id}: {e}")
            self.conn.rollback()
            raise
            
    def index_batch(self, documents: List[DocumentIndex]):
        """Index multiple documents efficiently"""
        for doc in documents:
            self.index_document(doc)
            
    def search(self, 
               query: str,
               filters: Dict[str, Any] = None,
               limit: int = 50,
               offset: int = 0,
               highlight: bool = True) -> Tuple[List[Dict], int]:
        """
        Search documents with optional filters
        
        Returns: (results, total_count)
        """
        try:
            # Prepare FTS query
            fts_query = self._prepare_fts_query(query)
            
            # Build the base query
            if fts_query:
                # Use FTS5 for text search
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
                # No text query, just browse with filters
                base_query = """
                    SELECT d.*, d.title as title_snippet, 
                           substr(d.content, 1, 200) as content_snippet,
                           0 as rank
                    FROM documents d
                    WHERE 1=1
                """
                params = []
            
            # Apply filters
            filter_clauses = []
            
            if filters:
                # Date range filter
                if 'date_range' in filters:
                    start_date = filters['date_range'].get('start')
                    end_date = filters['date_range'].get('end')
                    if start_date:
                        filter_clauses.append("d.created_at >= ?")
                        params.append(start_date)
                    if end_date:
                        filter_clauses.append("d.created_at <= ?")
                        params.append(end_date)
                
                # Language filter
                if 'language' in filters:
                    filter_clauses.append("d.language = ?")
                    params.append(filters['language'])
                
                # Confidence filter
                if 'min_confidence' in filters:
                    filter_clauses.append("d.confidence >= ?")
                    params.append(filters['min_confidence'])
                
                # Entity type filter (requires JSON parsing)
                if 'entity_types' in filters and filters['entity_types']:
                    # This is more complex and might need a subquery
                    pass
                
                # Tags filter
                if 'tags' in filters and filters['tags']:
                    tag_conditions = []
                    for tag in filters['tags']:
                        tag_conditions.append("d.tags LIKE ?")
                        params.append(f"%{tag}%")
                    filter_clauses.append(f"({' OR '.join(tag_conditions)})")
                
                # Speakers filter
                if 'speakers' in filters and filters['speakers']:
                    speaker_conditions = []
                    for speaker in filters['speakers']:
                        speaker_conditions.append("d.speakers LIKE ?")
                        params.append(f"%{speaker}%")
                    filter_clauses.append(f"({' OR '.join(speaker_conditions)})")
            
            # Add filter clauses to query
            if filter_clauses:
                if "WHERE" in base_query:
                    base_query += " AND " + " AND ".join(filter_clauses)
                else:
                    base_query += " WHERE " + " AND ".join(filter_clauses)
            
            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM ({base_query})"
            cursor = self.conn.execute(count_query, params)
            total_count = cursor.fetchone()['total']
            
            # Add ordering and pagination
            if query.strip():
                base_query += " ORDER BY rank DESC"
            else:
                base_query += " ORDER BY d.created_at DESC"
                
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
                    'language': row['language'],
                    'confidence': row['confidence'],
                    'created_at': row['created_at'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {}
                }
                
                # Parse stored fields
                if row['entities']:
                    result['entities'] = row['entities'].split()
                if row['tags']:
                    result['tags'] = row['tags'].split()
                if row['speakers']:
                    result['speakers'] = row['speakers'].split()
                    
                results.append(result)
            
            # Log search to history
            self._log_search(query, filters, total_count)
            
            return results, total_count
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise
            
    def _prepare_fts_query(self, query: str) -> str:
        """Prepare query for FTS5 matching"""
        # If query is empty, return empty string
        if not query.strip():
            return ""
            
        # For FTS5, we need to be more careful with special characters
        # and operators. Let's simplify the approach.
        
        # Split query into words, preserving quoted phrases
        parts = []
        current_word = []
        in_quotes = False
        
        for i, char in enumerate(query):
            if char == '"':
                if in_quotes:
                    # End of quoted phrase
                    if current_word:
                        parts.append('"' + ''.join(current_word) + '"')
                        current_word = []
                    in_quotes = False
                else:
                    # Start of quoted phrase
                    if current_word:
                        parts.append(''.join(current_word))
                        current_word = []
                    in_quotes = True
            elif char == ' ' and not in_quotes:
                if current_word:
                    parts.append(''.join(current_word))
                    current_word = []
            else:
                current_word.append(char)
                
        # Add any remaining word
        if current_word:
            if in_quotes:
                parts.append('"' + ''.join(current_word) + '"')
            else:
                parts.append(''.join(current_word))
        
        # Process parts for FTS5
        fts_parts = []
        skip_next = False
        
        for i, part in enumerate(parts):
            if skip_next:
                skip_next = False
                continue
                
            part = part.strip()
            if not part:
                continue
                
            # Handle quoted phrases
            if part.startswith('"') and part.endswith('"') and len(part) > 2:
                fts_parts.append(part)
            # Handle OR operator
            elif part.upper() == 'OR':
                fts_parts.append('OR')
            # Handle NOT operator (convert to FTS5 NOT syntax)
            elif part.upper() == 'NOT' and i + 1 < len(parts):
                # FTS5 uses NOT before the term
                next_part = parts[i + 1].strip()
                if next_part:
                    fts_parts.append(f'NOT {next_part}')
                    skip_next = True
            # Handle negation prefix
            elif part.startswith('-') and len(part) > 1:
                # FTS5 uses NOT instead of -
                fts_parts.append(f'NOT {part[1:]}')
            # Regular terms - add them as-is (FTS5 will handle wildcards)
            else:
                fts_parts.append(part)
                
        return ' '.join(fts_parts)
        
    def get_facets(self, query: str = None, filters: Dict[str, Any] = None) -> Dict[str, Dict[str, int]]:
        """Get facet counts for search results"""
        facets = {
            'tags': {},
            'speakers': {},
            'languages': {},
            'entity_types': {}
        }
        
        # Get tag counts
        cursor = self.conn.execute("""
            SELECT tags, COUNT(*) as count 
            FROM documents 
            WHERE tags IS NOT NULL AND tags != ''
            GROUP BY tags
        """)
        
        for row in cursor:
            for tag in row['tags'].split():
                facets['tags'][tag] = facets['tags'].get(tag, 0) + row['count']
                
        # Get speaker counts
        cursor = self.conn.execute("""
            SELECT speakers, COUNT(*) as count 
            FROM documents 
            WHERE speakers IS NOT NULL AND speakers != ''
            GROUP BY speakers
        """)
        
        for row in cursor:
            for speaker in row['speakers'].split():
                facets['speakers'][speaker] = facets['speakers'].get(speaker, 0) + row['count']
                
        # Get language counts
        cursor = self.conn.execute("""
            SELECT language, COUNT(*) as count 
            FROM documents 
            GROUP BY language
        """)
        
        for row in cursor:
            facets['languages'][row['language']] = row['count']
            
        return facets
        
    def save_search(self, name: str, query: str, filters: Dict[str, Any] = None):
        """Save a search for later use"""
        self.conn.execute("""
            INSERT INTO saved_searches (name, query, filters, created_at, last_used)
            VALUES (?, ?, ?, ?, ?)
        """, (
            name,
            query,
            json.dumps(filters) if filters else None,
            datetime.utcnow(),
            datetime.utcnow()
        ))
        self.conn.commit()
        
    def get_saved_searches(self, limit: int = 20) -> List[Dict]:
        """Get saved searches"""
        cursor = self.conn.execute("""
            SELECT * FROM saved_searches 
            ORDER BY last_used DESC 
            LIMIT ?
        """, (limit,))
        
        searches = []
        for row in cursor:
            searches.append({
                'search_id': row['search_id'],
                'name': row['name'],
                'query': row['query'],
                'filters': json.loads(row['filters']) if row['filters'] else {},
                'created_at': row['created_at'],
                'last_used': row['last_used'],
                'use_count': row['use_count']
            })
            
        return searches
        
    def _log_search(self, query: str, filters: Dict[str, Any], result_count: int):
        """Log search to history"""
        self.conn.execute("""
            INSERT INTO search_history (query, filters, result_count, searched_at)
            VALUES (?, ?, ?, ?)
        """, (
            query,
            json.dumps(filters) if filters else None,
            result_count,
            datetime.utcnow()
        ))
        self.conn.commit()
        
    def get_search_history(self, limit: int = 20) -> List[Dict]:
        """Get recent search history"""
        cursor = self.conn.execute("""
            SELECT * FROM search_history 
            ORDER BY searched_at DESC 
            LIMIT ?
        """, (limit,))
        
        history = []
        for row in cursor:
            history.append({
                'query': row['query'],
                'filters': json.loads(row['filters']) if row['filters'] else {},
                'result_count': row['result_count'],
                'searched_at': row['searched_at']
            })
            
        return history
        
    def delete_document(self, doc_id: str):
        """Remove document from index"""
        self.conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        self.conn.execute("DELETE FROM documents_fts WHERE doc_id = ?", (doc_id,))
        self.conn.commit()
        
    def clear_index(self):
        """Clear all indexed documents"""
        self.conn.execute("DELETE FROM documents")
        self.conn.execute("DELETE FROM documents_fts")
        self.conn.commit()
        
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()