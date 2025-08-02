"""
Main search manager coordinating all search functionality
"""

import logging
import time
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from pathlib import Path

from .search_index import SearchIndex, DocumentIndex
from .query_parser import QueryParser, ParsedQuery
from .filters import FilterEngine
from .advanced_analytics import AdvancedAnalytics

logger = logging.getLogger(__name__)


@dataclass
class SearchQuery:
    """Represents a complete search query"""
    query: str
    filters: Dict[str, Any] = field(default_factory=dict)
    options: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        # Set default options
        default_options = {
            'limit': 50,
            'offset': 0,
            'highlight': True,
            'fuzzy': False,
            'include_facets': True,
            'sort_by': 'relevance'  # or 'date', 'title'
        }
        for key, value in default_options.items():
            if key not in self.options:
                self.options[key] = value


@dataclass
class SearchResult:
    """Represents search results"""
    query: SearchQuery
    results: List[Dict[str, Any]]
    total_count: int
    facets: Dict[str, Dict[str, int]] = field(default_factory=dict)
    search_time_ms: float = 0
    suggestions: List[str] = field(default_factory=list)
    
    @property
    def has_results(self) -> bool:
        return self.total_count > 0
    
    @property
    def page_info(self) -> Dict[str, int]:
        """Get pagination information"""
        limit = self.query.options.get('limit', 50)
        offset = self.query.options.get('offset', 0)
        current_page = (offset // limit) + 1
        total_pages = (self.total_count + limit - 1) // limit
        
        return {
            'current_page': current_page,
            'total_pages': total_pages,
            'per_page': limit,
            'total_results': self.total_count,
            'showing_from': offset + 1,
            'showing_to': min(offset + limit, self.total_count)
        }


class SearchManager:
    """Main coordinator for search functionality"""
    
    def __init__(self, index_path: str = "search_index.db"):
        self.index = SearchIndex(index_path)
        self.parser = QueryParser()
        self.filter_engine = FilterEngine()
        self.analytics = AdvancedAnalytics(index_path)
        self.search_cache = {}  # Simple in-memory cache
        self.cache_ttl = 300  # 5 minutes
        
    async def search(self, search_query: SearchQuery) -> SearchResult:
        """Execute a search query"""
        start_time = time.time()
        
        # Check cache
        cache_key = self._get_cache_key(search_query)
        if cache_key in self.search_cache:
            cached_result, cached_time = self.search_cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                logger.info(f"Returning cached results for query: {search_query.query}")
                return cached_result
        
        # Parse query
        parsed_query = self.parser.parse(search_query.query)
        
        # Merge parsed filters with explicit filters
        all_filters = self.filter_engine.merge_filters(
            parsed_query.filters,
            search_query.filters
        )
        
        # Validate filters
        validated_filters = self.filter_engine.validate_filters(all_filters)
        
        # Execute search
        results, total_count = await self._execute_search(
            parsed_query,
            validated_filters,
            search_query.options
        )
        
        # Apply post-processing filters
        if validated_filters.get('entity_types'):
            results = self.filter_engine.apply_filters(results, {
                'entity_type': validated_filters['entity_types']
            })
            # Update count after filtering
            total_count = len(results)
            
            # Re-apply pagination after filtering
            offset = search_query.options.get('offset', 0)
            limit = search_query.options.get('limit', 50)
            results = results[offset:offset + limit]
        
        # Build facets if requested
        facets = {}
        if search_query.options.get('include_facets', True):
            facets = self.filter_engine.build_facets(results)
        
        # Get suggestions for empty results
        suggestions = []
        if total_count == 0:
            suggestions = await self._get_search_suggestions(search_query.query)
        
        # Calculate search time
        search_time_ms = (time.time() - start_time) * 1000
        
        # Create result
        result = SearchResult(
            query=search_query,
            results=results,
            total_count=total_count,
            facets=facets,
            search_time_ms=search_time_ms,
            suggestions=suggestions
        )
        
        # Cache result
        self.search_cache[cache_key] = (result, time.time())
        
        # Clean old cache entries
        self._clean_cache()
        
        logger.info(f"Search completed: {total_count} results in {search_time_ms:.2f}ms")
        
        return result
    
    async def _execute_search(self, 
                            parsed_query: ParsedQuery,
                            filters: Dict[str, Any],
                            options: Dict[str, Any]) -> Tuple[List[Dict], int]:
        """Execute the actual search against the index"""
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        
        return await loop.run_in_executor(
            None,
            self.index.search,
            parsed_query.to_fts_query(),
            filters,
            options.get('limit', 50),
            options.get('offset', 0),
            options.get('highlight', True)
        )
    
    async def index_transcript(self, 
                             transcript_id: str,
                             title: str,
                             content: str,
                             metadata: Dict[str, Any] = None):
        """Index a transcript for searching"""
        document = DocumentIndex(
            doc_id=transcript_id,
            title=title,
            content=content,
            metadata=metadata
        )
        
        # Run in thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self.index.index_document,
            document
        )
        
        # Clear cache when new content is indexed
        self.search_cache.clear()
        
        logger.info(f"Indexed transcript: {transcript_id}")
    
    async def index_batch(self, transcripts: List[Dict[str, Any]]):
        """Index multiple transcripts efficiently"""
        documents = []
        
        for transcript in transcripts:
            doc = DocumentIndex(
                doc_id=transcript['id'],
                title=transcript['title'],
                content=transcript['content'],
                metadata=transcript.get('metadata', {})
            )
            documents.append(doc)
        
        # Run in thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self.index.index_batch,
            documents
        )
        
        # Clear cache
        self.search_cache.clear()
        
        logger.info(f"Indexed {len(documents)} transcripts")
    
    async def delete_transcript(self, transcript_id: str):
        """Remove transcript from search index"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self.index.delete_document,
            transcript_id
        )
        
        # Clear cache
        self.search_cache.clear()
        
        logger.info(f"Deleted transcript from index: {transcript_id}")
    
    async def update_transcript(self,
                              transcript_id: str,
                              updates: Dict[str, Any]):
        """Update indexed transcript"""
        # For now, re-index the entire document
        # In a real implementation, you might want partial updates
        
        if all(key in updates for key in ['title', 'content']):
            await self.index_transcript(
                transcript_id,
                updates['title'],
                updates['content'],
                updates.get('metadata', {})
            )
    
    async def get_search_suggestions(self, partial_query: str) -> List[str]:
        """Get search suggestions for autocomplete"""
        # Get search history
        history = self.index.get_search_history(limit=50)
        history_queries = [h['query'] for h in history]
        
        # Get query suggestions
        suggestions = self.parser.suggest_query(partial_query, history_queries)
        
        return suggestions
    
    async def _get_search_suggestions(self, failed_query: str) -> List[str]:
        """Get suggestions for failed searches"""
        suggestions = []
        
        # Suggest simpler query
        if len(failed_query.split()) > 3:
            # Take first few words
            suggestions.append(' '.join(failed_query.split()[:2]))
        
        # Suggest without filters
        if any(char in failed_query for char in [':',  '"', '-']):
            # Remove special syntax
            simple_query = re.sub(r'[:"\\+\-]', ' ', failed_query).strip()
            suggestions.append(simple_query)
        
        # Get popular searches
        history = self.index.get_search_history(limit=10)
        for hist in history[:3]:
            if hist['result_count'] > 0:
                suggestions.append(hist['query'])
        
        return list(set(suggestions))[:5]
    
    def save_search(self, name: str, query: str, filters: Dict[str, Any] = None):
        """Save a search for later use"""
        self.index.save_search(name, query, filters)
        
    def get_saved_searches(self) -> List[Dict[str, Any]]:
        """Get saved searches"""
        return self.index.get_saved_searches()
    
    def get_search_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent search history"""
        return self.index.get_search_history(limit)
    
    def export_results(self, results: SearchResult, format: str = 'json') -> str:
        """Export search results in various formats"""
        if format == 'json':
            import json
            return json.dumps({
                'query': results.query.query,
                'total_results': results.total_count,
                'results': results.results,
                'search_time_ms': results.search_time_ms,
                'exported_at': datetime.utcnow().isoformat()
            }, indent=2)
            
        elif format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            if results.results:
                writer = csv.DictWriter(
                    output, 
                    fieldnames=['doc_id', 'title', 'content_snippet', 'created_at']
                )
                writer.writeheader()
                
                for result in results.results:
                    writer.writerow({
                        'doc_id': result.get('doc_id'),
                        'title': result.get('title'),
                        'content_snippet': result.get('content_snippet', '')[:200],
                        'created_at': result.get('created_at')
                    })
                    
            return output.getvalue()
            
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _get_cache_key(self, search_query: SearchQuery) -> str:
        """Generate cache key for search query"""
        import hashlib
        key_parts = [
            search_query.query,
            json.dumps(search_query.filters, sort_keys=True),
            json.dumps(search_query.options, sort_keys=True)
        ]
        key_str = '|'.join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _clean_cache(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, cached_time) in self.search_cache.items()
            if current_time - cached_time > self.cache_ttl
        ]
        for key in expired_keys:
            del self.search_cache[key]
    
    def close(self):
        """Close search index"""
        self.index.close()
    
    # Advanced analytics methods
    async def analyze_trends(self, time_period: str = "30d", analysis_type: str = "keywords", filters: Dict[str, Any] = None):
        """Analyze trends across transcripts"""
        return await self.analytics.analyze_trends(time_period, analysis_type, filters)
    
    async def extract_topics(self, transcript_ids: List[str] = None, num_topics: int = 5, method: str = "keyword_clustering"):
        """Extract topics from transcripts"""
        return await self.analytics.extract_topics(transcript_ids, num_topics, method)
    
    async def compare_sources(self, source_a: str, source_b: str, comparison_type: str = "comprehensive"):
        """Compare two audio sources or transcript collections"""
        return await self.analytics.compare_sources(source_a, source_b, comparison_type)
    
    def get_analytics_stats(self) -> Dict[str, Any]:
        """Get analytics statistics"""
        return {
            'analytics_enabled': True,
            'supported_analyses': [
                'trend_analysis',
                'topic_modeling', 
                'comparative_analysis',
                'keyword_extraction'
            ],
            'trend_periods': ['7d', '30d', '90d', '1y'],
            'analysis_types': ['keywords', 'topics', 'entities', 'sentiment']
        }