"""
Whoosh search provider implementation
"""

import json
import logging
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
import re

from .base import BaseSearchProvider, SearchDocument

logger = logging.getLogger(__name__)

try:
    from whoosh import fields, writing
    from whoosh.index import create_index, open_dir
    from whoosh.qparser import QueryParser, MultifieldParser
    from whoosh.query import And, Or, Not, Term, Phrase
    from whoosh.highlight import HtmlFormatter, ContextFragmenter
    from whoosh.analysis import StemmingAnalyzer
    WHOOSH_AVAILABLE = True
except ImportError:
    WHOOSH_AVAILABLE = False
    logger.warning("Whoosh not available. Install with: pip install whoosh")


class WhooshSearchProvider(BaseSearchProvider):
    """Whoosh-based search provider with advanced features"""
    
    def __init__(self):
        if not WHOOSH_AVAILABLE:
            raise ImportError("Whoosh is required for WhooshSearchProvider")
            
        self.index = None
        self.index_dir = None
        self.schema = None
        
    def initialize(self, config: Dict[str, Any]):
        """Initialize Whoosh index"""
        self.index_dir = config.get('index_dir', 'whoosh_index')
        
        # Create index directory
        Path(self.index_dir).mkdir(parents=True, exist_ok=True)
        
        # Define schema
        analyzer = StemmingAnalyzer(stoplist=None)
        
        self.schema = fields.Schema(
            doc_id=fields.ID(stored=True, unique=True),
            title=fields.TEXT(stored=True, analyzer=analyzer, phrase=True),
            content=fields.TEXT(stored=True, analyzer=analyzer, phrase=True),
            entities=fields.TEXT(stored=True, analyzer=analyzer),
            tags=fields.KEYWORD(stored=True, commas=True),
            speakers=fields.KEYWORD(stored=True, commas=True),
            language=fields.ID(stored=True),
            indexed_at=fields.DATETIME(stored=True),
            metadata=fields.TEXT(stored=True)
        )
        
        # Create or open index
        try:
            self.index = open_dir(self.index_dir)
            # Verify schema compatibility
            if self.index.schema != self.schema:
                logger.warning("Schema mismatch, recreating index")
                self.index.close()
                self.index = create_index(self.schema, self.index_dir)
        except:
            # Create new index
            self.index = create_index(self.schema, self.index_dir)
            
        logger.info(f"Whoosh search provider initialized: {self.index_dir}")
        
    def index_document(self, document: SearchDocument):
        """Index a single document"""
        try:
            writer = self.index.writer()
            
            # Extract metadata fields
            metadata = document.metadata
            entities_text = self._extract_entities_text(metadata.get('entities', []))
            tags = ','.join(metadata.get('tags', []))
            speakers = ','.join(metadata.get('speakers', []))
            language = metadata.get('language', 'en')
            
            writer.update_document(
                doc_id=document.doc_id,
                title=document.title,
                content=document.content,
                entities=entities_text,
                tags=tags,
                speakers=speakers,
                language=language,
                metadata=json.dumps(metadata)
            )
            
            writer.commit()
            logger.debug(f"Indexed document: {document.doc_id}")
            
        except Exception as e:
            logger.error(f"Error indexing document {document.doc_id}: {e}")
            raise
            
    def index_batch(self, documents: List[SearchDocument]):
        """Index multiple documents efficiently"""
        try:
            writer = self.index.writer()
            
            for doc in documents:
                metadata = doc.metadata
                entities_text = self._extract_entities_text(metadata.get('entities', []))
                tags = ','.join(metadata.get('tags', []))
                speakers = ','.join(metadata.get('speakers', []))
                language = metadata.get('language', 'en')
                
                writer.update_document(
                    doc_id=doc.doc_id,
                    title=doc.title,
                    content=doc.content,
                    entities=entities_text,
                    tags=tags,
                    speakers=speakers,
                    language=language,
                    metadata=json.dumps(metadata)
                )
            
            writer.commit()
            logger.info(f"Batch indexed {len(documents)} documents")
            
        except Exception as e:
            logger.error(f"Error batch indexing: {e}")
            raise
    
    def search(self, 
               query: str,
               filters: Dict[str, Any] = None,
               limit: int = 50,
               offset: int = 0,
               highlight: bool = True) -> Tuple[List[Dict], int]:
        """Search documents with Whoosh"""
        try:
            with self.index.searcher() as searcher:
                # Parse query
                whoosh_query = self._parse_query(query, filters)
                
                # Execute search
                search_results = searcher.search(
                    whoosh_query,
                    limit=limit + offset,  # Get extra results for offset
                    terms=True
                )
                
                # Get total count
                total_count = len(search_results)
                
                # Apply offset
                results = []
                fragmenter = ContextFragmenter(maxchars=200, surround=30)
                formatter = HtmlFormatter(tagname="mark")
                
                for i, hit in enumerate(search_results[offset:offset + limit]):
                    result = {
                        'doc_id': hit['doc_id'],
                        'title': hit['title'],
                        'content': hit['content'],
                        'rank': hit.score,
                        'metadata': json.loads(hit['metadata']) if hit['metadata'] else {}
                    }
                    
                    # Add highlighting
                    if highlight and query.strip():
                        title_highlights = hit.highlights("title", formatter=formatter)
                        content_highlights = hit.highlights("content", fragmenter=fragmenter, formatter=formatter)
                        
                        result['title_snippet'] = title_highlights if title_highlights else hit['title']
                        result['content_snippet'] = content_highlights if content_highlights else hit['content'][:200]
                    else:
                        result['title_snippet'] = hit['title']
                        result['content_snippet'] = hit['content'][:200]
                        
                    results.append(result)
                
                return results, total_count
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise
    
    def delete_document(self, doc_id: str):
        """Delete a document from the index"""
        try:
            writer = self.index.writer()
            writer.delete_by_term('doc_id', doc_id)
            writer.commit()
            logger.debug(f"Deleted document: {doc_id}")
            
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            raise
    
    def clear_index(self):
        """Clear all documents from the index"""
        try:
            writer = self.index.writer()
            writer.commit(mergetype=writing.CLEAR)
            logger.info("Cleared all documents from index")
            
        except Exception as e:
            logger.error(f"Error clearing index: {e}")
            raise
    
    def close(self):
        """Close the index"""
        if self.index:
            self.index.close()
            self.index = None
            logger.info("Whoosh search provider closed")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        try:
            with self.index.searcher() as searcher:
                doc_count = searcher.doc_count()
                
            # Get index size
            index_size = sum(
                f.stat().st_size 
                for f in Path(self.index_dir).rglob('*') 
                if f.is_file()
            )
            
            return {
                'provider': 'whoosh',
                'document_count': doc_count,
                'index_size_bytes': index_size,
                'index_size_mb': round(index_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'provider': 'whoosh', 'error': str(e)}
    
    def optimize_index(self):
        """Optimize the Whoosh index"""
        try:
            writer = self.index.writer()
            writer.commit(optimize=True)
            logger.info("Optimized Whoosh index")
            
        except Exception as e:
            logger.error(f"Error optimizing index: {e}")
    
    def _extract_entities_text(self, entities: List[Dict]) -> str:
        """Extract searchable text from entities"""
        entity_texts = []
        
        for entity in entities:
            if isinstance(entity, dict):
                if 'text' in entity:
                    entity_texts.append(entity['text'])
                elif 'name' in entity:
                    entity_texts.append(entity['name'])
            elif isinstance(entity, str):
                entity_texts.append(entity)
                
        return ' '.join(entity_texts)
    
    def _parse_query(self, query: str, filters: Dict[str, Any] = None) -> Any:
        """Parse query string into Whoosh query object"""
        queries = []
        
        # Main text query
        if query.strip():
            # Use multifield parser for searching across title and content
            parser = MultifieldParser(['title', 'content', 'entities'], self.index.schema)
            text_query = parser.parse(query)
            queries.append(text_query)
        
        # Apply filters
        if filters:
            filter_queries = self._build_filter_queries(filters)
            queries.extend(filter_queries)
        
        # Combine queries
        if len(queries) == 1:
            return queries[0]
        elif len(queries) > 1:
            return And(queries)
        else:
            # Match all documents if no query
            parser = QueryParser('content', self.index.schema)
            return parser.parse('*')
    
    def _build_filter_queries(self, filters: Dict[str, Any]) -> List[Any]:
        """Build Whoosh filter queries"""
        filter_queries = []
        
        # Language filter
        if 'language' in filters:
            filter_queries.append(Term('language', filters['language']))
        
        # Tags filter
        if 'tags' in filters and filters['tags']:
            tag_queries = []
            for tag in filters['tags']:
                tag_queries.append(Term('tags', tag))
            if tag_queries:
                filter_queries.append(Or(tag_queries))
        
        # Speakers filter
        if 'speakers' in filters and filters['speakers']:
            speaker_queries = []
            for speaker in filters['speakers']:
                speaker_queries.append(Term('speakers', speaker))
            if speaker_queries:
                filter_queries.append(Or(speaker_queries))
        
        # Entity types filter (requires metadata search)
        if 'entity_types' in filters and filters['entity_types']:
            entity_queries = []
            for entity_type in filters['entity_types']:
                # This is a simplified approach - in practice you might want
                # to parse the metadata JSON more carefully
                entity_queries.append(Term('metadata', entity_type))
            if entity_queries:
                filter_queries.append(Or(entity_queries))
        
        return filter_queries