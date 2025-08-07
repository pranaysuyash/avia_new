"""
Comprehensive Search Service
Provides advanced search functionality across all data types with full-text search,
semantic search, filtering, and ranking capabilities.
"""

import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import re
import math
from collections import defaultdict, Counter

from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_, func
import redis.asyncio as redis

from api.database import get_db, User, Transcript
from services.audit_logging_service import audit_service, AuditEventType
from api.cache.redis_cache import redis_cache

logger = logging.getLogger(__name__)


class SearchType(Enum):
    """Types of search operations"""
    FULL_TEXT = "full_text"
    SEMANTIC = "semantic"
    FUZZY = "fuzzy"
    REGEX = "regex"
    EXACT = "exact"


class SearchScope(Enum):
    """Scope of search operations"""
    TRANSCRIPTS = "transcripts"
    USERS = "users"
    CONTENT = "content"
    METADATA = "metadata"
    ALL = "all"


class SortOrder(Enum):
    """Search result sorting options"""
    RELEVANCE = "relevance"
    DATE_DESC = "date_desc"
    DATE_ASC = "date_asc"
    TITLE_ASC = "title_asc"
    TITLE_DESC = "title_desc"
    DURATION_ASC = "duration_asc"
    DURATION_DESC = "duration_desc"


@dataclass
class SearchFilter:
    """Search filter configuration"""
    field: str
    operator: str  # eq, ne, gt, lt, gte, lte, contains, in, not_in
    value: Any
    case_sensitive: bool = False


@dataclass
class SearchQuery:
    """Search query configuration"""
    query: str
    search_type: SearchType = SearchType.FULL_TEXT
    scope: SearchScope = SearchScope.ALL
    filters: List[SearchFilter] = None
    sort_order: SortOrder = SortOrder.RELEVANCE
    limit: int = 20
    offset: int = 0
    highlight: bool = True
    facets: List[str] = None
    user_id: Optional[int] = None


@dataclass
class SearchResult:
    """Single search result"""
    id: str
    type: str
    title: str
    content: str
    highlighted_content: str
    metadata: Dict[str, Any]
    score: float
    created_at: datetime
    updated_at: datetime


@dataclass
class SearchResponse:
    """Complete search response"""
    results: List[SearchResult]
    total_count: int
    query: str
    search_time_ms: float
    facets: Dict[str, Dict[str, int]]
    suggestions: List[str]
    filters_applied: List[SearchFilter]
    page: int
    per_page: int
    has_more: bool


@dataclass
class SearchAnalytics:
    """Search analytics data"""
    query: str
    user_id: Optional[int]
    search_type: SearchType
    scope: SearchScope
    results_count: int
    search_time_ms: float
    clicked_result_ids: List[str]
    timestamp: datetime


class ComprehensiveSearchService:
    """Service for comprehensive search functionality"""
    
    def __init__(self):
        self.cache_ttl = 3600  # 1 hour cache
        self.max_search_terms = 50
        self.max_results = 1000
        
        # Search analytics storage
        self.search_analytics: List[SearchAnalytics] = []
        
        # Search suggestions cache
        self.popular_queries: Dict[str, int] = defaultdict(int)
        self.query_completions: Dict[str, List[str]] = {}
        
        # Initialize search indexes
        self.search_indexes = {
            'transcripts': {},
            'users': {},
            'content': {}
        }
    
    async def search(
        self, 
        search_query: SearchQuery,
        user_id: Optional[int] = None
    ) -> SearchResponse:
        """
        Perform comprehensive search across data types
        
        Args:
            search_query: Search query configuration
            user_id: User performing the search
            
        Returns:
            SearchResponse with results and metadata
        """
        
        start_time = datetime.utcnow()
        
        try:
            # Log search request
            audit_service.log_event(
                event_type=AuditEventType.SEARCH_QUERY,
                action=f"Search query: {search_query.query[:100]}",
                user_id=user_id,
                details={
                    "query": search_query.query,
                    "search_type": search_query.search_type.value,
                    "scope": search_query.scope.value,
                    "filters_count": len(search_query.filters) if search_query.filters else 0
                }
            )
            
            # Check cache first
            cache_key = self._generate_cache_key(search_query, user_id)
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                return cached_result
            
            # Validate and sanitize query
            search_query = self._validate_search_query(search_query)
            
            # Perform search based on scope
            results = []
            total_count = 0
            facets = {}
            
            if search_query.scope in [SearchScope.ALL, SearchScope.TRANSCRIPTS]:
                transcript_results, transcript_count, transcript_facets = await self._search_transcripts(
                    search_query, user_id
                )
                results.extend(transcript_results)
                total_count += transcript_count
                facets.update(transcript_facets)
            
            if search_query.scope in [SearchScope.ALL, SearchScope.USERS]:
                user_results, user_count, user_facets = await self._search_users(
                    search_query, user_id
                )
                results.extend(user_results)
                total_count += user_count
                facets.update(user_facets)
            
            if search_query.scope in [SearchScope.ALL, SearchScope.CONTENT]:
                content_results, content_count, content_facets = await self._search_content(
                    search_query, user_id
                )
                results.extend(content_results)
                total_count += content_count
                facets.update(content_facets)
            
            # Sort and paginate results
            results = self._sort_results(results, search_query.sort_order)
            paginated_results = results[search_query.offset:search_query.offset + search_query.limit]
            
            # Generate search suggestions
            suggestions = await self._generate_suggestions(search_query.query)
            
            # Calculate search time
            search_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Create response
            response = SearchResponse(
                results=paginated_results,
                total_count=total_count,
                query=search_query.query,
                search_time_ms=search_time_ms,
                facets=facets,
                suggestions=suggestions,
                filters_applied=search_query.filters or [],
                page=search_query.offset // search_query.limit + 1,
                per_page=search_query.limit,
                has_more=search_query.offset + search_query.limit < total_count
            )
            
            # Cache result
            await self._cache_result(cache_key, response)
            
            # Record analytics
            await self._record_search_analytics(
                search_query, user_id, len(paginated_results), search_time_ms
            )
            
            # Update search suggestions
            self._update_search_suggestions(search_query.query)
            
            return response
            
        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            
            # Log search error
            audit_service.log_event(
                event_type=AuditEventType.SEARCH_ERROR,
                action="Search query failed",
                user_id=user_id,
                error_message=str(e),
                details={"query": search_query.query}
            )
            
            # Return empty results
            return SearchResponse(
                results=[],
                total_count=0,
                query=search_query.query,
                search_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
                facets={},
                suggestions=[],
                filters_applied=[],
                page=1,
                per_page=search_query.limit,
                has_more=False
            )
    
    async def _search_transcripts(
        self, 
        search_query: SearchQuery, 
        user_id: Optional[int]
    ) -> Tuple[List[SearchResult], int, Dict[str, Dict[str, int]]]:
        """Search transcripts with full-text search"""
        
        db = next(get_db())
        results = []
        facets = defaultdict(lambda: defaultdict(int))
        
        try:
            # Build base query
            query = db.query(Transcript)
            
            # Apply user filter
            if user_id:
                query = query.filter(Transcript.user_id == user_id)
            
            # Apply search filters
            if search_query.filters:
                query = self._apply_filters(query, search_query.filters, Transcript)
            
            # Apply text search
            if search_query.query.strip():
                search_terms = self._parse_search_terms(search_query.query)
                
                if search_query.search_type == SearchType.FULL_TEXT:
                    # Full-text search across multiple fields
                    search_conditions = []
                    for term in search_terms:
                        term_condition = or_(
                            Transcript.title.ilike(f'%{term}%'),
                            Transcript.content.ilike(f'%{term}%'),
                            func.cast(Transcript.metadata, str).ilike(f'%{term}%')
                        )
                        search_conditions.append(term_condition)
                    
                    if search_conditions:
                        query = query.filter(and_(*search_conditions))
                
                elif search_query.search_type == SearchType.EXACT:
                    # Exact phrase search
                    exact_condition = or_(
                        Transcript.title.ilike(f'%{search_query.query}%'),
                        Transcript.content.ilike(f'%{search_query.query}%')
                    )
                    query = query.filter(exact_condition)
                
                elif search_query.search_type == SearchType.REGEX:
                    # Regex search (be careful with user input)
                    try:
                        regex_pattern = search_query.query
                        # Validate regex
                        re.compile(regex_pattern)
                        regex_condition = or_(
                            Transcript.title.op('~')(regex_pattern),
                            Transcript.content.op('~')(regex_pattern)
                        )
                        query = query.filter(regex_condition)
                    except re.error:
                        # Invalid regex, fall back to full-text search
                        query = query.filter(
                            or_(
                                Transcript.title.ilike(f'%{search_query.query}%'),
                                Transcript.content.ilike(f'%{search_query.query}%')
                            )
                        )
            
            # Get total count
            total_count = query.count()
            
            # Get results for scoring and processing
            transcripts = query.all()
            
            # Score and convert results
            for transcript in transcripts:
                score = self._calculate_relevance_score(
                    transcript, search_query.query, search_terms if 'search_terms' in locals() else []
                )
                
                highlighted_content = self._highlight_matches(
                    transcript.content or "", search_query.query
                ) if search_query.highlight else transcript.content or ""
                
                result = SearchResult(
                    id=str(transcript.id),
                    type="transcript",
                    title=transcript.title or f"Transcript {transcript.id}",
                    content=transcript.content or "",
                    highlighted_content=highlighted_content,
                    metadata={
                        "duration": transcript.duration,
                        "language": transcript.language,
                        "file_url": getattr(transcript, 'file_url', None),
                        "created_at": transcript.created_at.isoformat() if transcript.created_at else None,
                        "updated_at": transcript.updated_at.isoformat() if transcript.updated_at else None,
                    },
                    score=score,
                    created_at=transcript.created_at or datetime.utcnow(),
                    updated_at=transcript.updated_at or datetime.utcnow()
                )
                results.append(result)
                
                # Build facets
                if transcript.language:
                    facets["language"][transcript.language] += 1
                if transcript.duration:
                    duration_bucket = self._get_duration_bucket(transcript.duration)
                    facets["duration"][duration_bucket] += 1
                
                created_date = transcript.created_at or datetime.utcnow()
                date_bucket = created_date.strftime("%Y-%m")
                facets["created_month"][date_bucket] += 1
            
            return results, total_count, dict(facets)
            
        finally:
            db.close()
    
    async def _search_users(
        self, 
        search_query: SearchQuery, 
        user_id: Optional[int]
    ) -> Tuple[List[SearchResult], int, Dict[str, Dict[str, int]]]:
        """Search users (admin only or public profiles)"""
        
        # For privacy, only admins can search users or users can search public profiles
        # This is a simplified implementation
        results = []
        facets = {}
        
        if not user_id:  # No user context, return empty results
            return results, 0, facets
        
        db = next(get_db())
        
        try:
            # Check if user is admin (simplified check)
            current_user = db.query(User).filter(User.id == user_id).first()
            if not current_user or not hasattr(current_user, 'role') or current_user.role != 'admin':
                return results, 0, facets
            
            # Build user search query
            query = db.query(User)
            
            if search_query.query.strip():
                search_terms = self._parse_search_terms(search_query.query)
                search_conditions = []
                
                for term in search_terms:
                    term_condition = or_(
                        User.username.ilike(f'%{term}%'),
                        User.email.ilike(f'%{term}%'),
                        User.full_name.ilike(f'%{term}%')
                    )
                    search_conditions.append(term_condition)
                
                if search_conditions:
                    query = query.filter(and_(*search_conditions))
            
            # Apply filters
            if search_query.filters:
                query = self._apply_filters(query, search_query.filters, User)
            
            total_count = query.count()
            users = query.all()
            
            # Convert to search results
            for user in users:
                score = self._calculate_user_relevance_score(
                    user, search_query.query, search_terms if 'search_terms' in locals() else []
                )
                
                result = SearchResult(
                    id=str(user.id),
                    type="user",
                    title=user.full_name or user.username,
                    content=f"{user.username} - {user.email}",
                    highlighted_content=self._highlight_matches(
                        f"{user.username} - {user.email}", search_query.query
                    ) if search_query.highlight else f"{user.username} - {user.email}",
                    metadata={
                        "username": user.username,
                        "email": user.email,
                        "role": getattr(user, 'role', 'user'),
                        "is_active": user.is_active,
                        "last_login": user.last_login.isoformat() if user.last_login else None,
                    },
                    score=score,
                    created_at=user.created_at or datetime.utcnow(),
                    updated_at=user.updated_at or datetime.utcnow()
                )
                results.append(result)
            
            return results, total_count, facets
            
        finally:
            db.close()
    
    async def _search_content(
        self, 
        search_query: SearchQuery, 
        user_id: Optional[int]
    ) -> Tuple[List[SearchResult], int, Dict[str, Dict[str, int]]]:
        """Search other content types (files, metadata, etc.)"""
        
        # Placeholder for other content types
        # This could include file metadata, annotations, comments, etc.
        results = []
        facets = {}
        
        # Example: Search in cached data or other storage systems
        if redis_cache.is_connected():
            try:
                # Search in Redis cache for user-specific content
                pattern = f"user:{user_id}:*" if user_id else "*"
                content_results = []
                
                async for key in redis_cache.client.scan_iter(match=pattern):
                    key_str = key.decode() if isinstance(key, bytes) else key
                    
                    # Skip sensitive keys
                    if any(sensitive in key_str.lower() for sensitive in ['password', 'token', 'secret']):
                        continue
                    
                    try:
                        value = await redis_cache.get(key_str)
                        if value and search_query.query.lower() in str(value).lower():
                            content_results.append({
                                "key": key_str,
                                "value": str(value)[:200] + "..." if len(str(value)) > 200 else str(value),
                                "full_value": value
                            })
                            
                            if len(content_results) >= 10:  # Limit cache search results
                                break
                    except Exception as e:
                        logger.warning(f"Error reading cache key {key_str}: {e}")
                        continue
                
                # Convert cache results to search results
                for i, cache_item in enumerate(content_results):
                    result = SearchResult(
                        id=f"cache_{hash(cache_item['key'])}",
                        type="cached_content",
                        title=f"Cached Data: {cache_item['key'].split(':')[-1]}",
                        content=cache_item['value'],
                        highlighted_content=self._highlight_matches(
                            cache_item['value'], search_query.query
                        ) if search_query.highlight else cache_item['value'],
                        metadata={
                            "cache_key": cache_item['key'],
                            "data_type": "cached"
                        },
                        score=0.5,  # Lower score for cached content
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    results.append(result)
                
            except Exception as e:
                logger.error(f"Cache search error: {e}")
        
        return results, len(results), facets
    
    def _validate_search_query(self, search_query: SearchQuery) -> SearchQuery:
        """Validate and sanitize search query"""
        
        # Sanitize query
        if search_query.query:
            # Remove potentially dangerous characters for regex search
            if search_query.search_type == SearchType.REGEX:
                # Basic regex sanitization - in production, use more robust validation
                dangerous_patterns = ['.*.*.*', '.{1000,}', '(?:(?:(?:(?:']
                for pattern in dangerous_patterns:
                    if pattern in search_query.query:
                        search_query.search_type = SearchType.FULL_TEXT
                        break
            
            # Limit query length
            search_query.query = search_query.query[:500]
        
        # Limit results
        if search_query.limit > self.max_results:
            search_query.limit = self.max_results
        
        # Validate filters
        if search_query.filters:
            search_query.filters = [f for f in search_query.filters if self._is_valid_filter(f)]
        
        return search_query
    
    def _is_valid_filter(self, filter_obj: SearchFilter) -> bool:
        """Validate search filter"""
        
        allowed_fields = {
            'title', 'content', 'language', 'duration', 'created_at', 
            'updated_at', 'user_id', 'is_active', 'role'
        }
        allowed_operators = {
            'eq', 'ne', 'gt', 'lt', 'gte', 'lte', 'contains', 'in', 'not_in'
        }
        
        return (
            filter_obj.field in allowed_fields and 
            filter_obj.operator in allowed_operators and
            filter_obj.value is not None
        )
    
    def _apply_filters(self, query, filters: List[SearchFilter], model_class):
        """Apply search filters to database query"""
        
        for filter_obj in filters:
            if not hasattr(model_class, filter_obj.field):
                continue
            
            field = getattr(model_class, filter_obj.field)
            
            if filter_obj.operator == 'eq':
                query = query.filter(field == filter_obj.value)
            elif filter_obj.operator == 'ne':
                query = query.filter(field != filter_obj.value)
            elif filter_obj.operator == 'gt':
                query = query.filter(field > filter_obj.value)
            elif filter_obj.operator == 'lt':
                query = query.filter(field < filter_obj.value)
            elif filter_obj.operator == 'gte':
                query = query.filter(field >= filter_obj.value)
            elif filter_obj.operator == 'lte':
                query = query.filter(field <= filter_obj.value)
            elif filter_obj.operator == 'contains':
                if filter_obj.case_sensitive:
                    query = query.filter(field.like(f'%{filter_obj.value}%'))
                else:
                    query = query.filter(field.ilike(f'%{filter_obj.value}%'))
            elif filter_obj.operator == 'in':
                if isinstance(filter_obj.value, list):
                    query = query.filter(field.in_(filter_obj.value))
            elif filter_obj.operator == 'not_in':
                if isinstance(filter_obj.value, list):
                    query = query.filter(~field.in_(filter_obj.value))
        
        return query
    
    def _parse_search_terms(self, query: str) -> List[str]:
        """Parse search query into individual terms"""
        
        if not query:
            return []
        
        # Handle quoted phrases
        terms = []
        in_quote = False
        current_term = ""
        
        for char in query + " ":  # Add space to flush last term
            if char == '"':
                if in_quote and current_term:
                    terms.append(current_term.strip())
                    current_term = ""
                in_quote = not in_quote
            elif char == ' ' and not in_quote:
                if current_term.strip():
                    terms.append(current_term.strip())
                current_term = ""
            else:
                current_term += char
        
        # Split non-quoted terms further
        final_terms = []
        for term in terms:
            if ' ' in term and '"' not in query:
                final_terms.extend(term.split())
            else:
                final_terms.append(term)
        
        # Remove empty terms and duplicates while preserving order
        seen = set()
        result = []
        for term in final_terms:
            term = term.lower().strip()
            if term and term not in seen and len(term) >= 2:
                seen.add(term)
                result.append(term)
        
        return result[:self.max_search_terms]
    
    def _calculate_relevance_score(
        self, 
        transcript, 
        query: str, 
        search_terms: List[str]
    ) -> float:
        """Calculate relevance score for transcript"""
        
        score = 0.0
        
        if not query or not search_terms:
            return 0.1
        
        title = (transcript.title or "").lower()
        content = (transcript.content or "").lower()
        query_lower = query.lower()
        
        # Exact phrase match in title (highest score)
        if query_lower in title:
            score += 10.0
        
        # Exact phrase match in content
        if query_lower in content:
            score += 5.0
        
        # Individual term matches
        for term in search_terms:
            term_lower = term.lower()
            
            # Title matches are weighted higher
            title_count = title.count(term_lower)
            score += title_count * 3.0
            
            # Content matches
            content_count = content.count(term_lower)
            score += content_count * 1.0
            
            # Word boundary matches get bonus
            if re.search(r'\b' + re.escape(term_lower) + r'\b', title):
                score += 2.0
            if re.search(r'\b' + re.escape(term_lower) + r'\b', content):
                score += 1.0
        
        # Recency bonus (newer content gets slight boost)
        if transcript.created_at:
            days_old = (datetime.utcnow() - transcript.created_at).days
            recency_bonus = max(0, 1.0 - (days_old / 365))  # Decay over a year
            score += recency_bonus
        
        # Duration penalty for very long or very short content
        if transcript.duration:
            if 60 <= transcript.duration <= 3600:  # Sweet spot: 1min - 1hour
                score += 0.5
            elif transcript.duration > 7200:  # Penalty for very long content
                score -= 0.5
        
        return max(0.0, score)
    
    def _calculate_user_relevance_score(
        self, 
        user, 
        query: str, 
        search_terms: List[str]
    ) -> float:
        """Calculate relevance score for user"""
        
        score = 0.0
        
        if not query or not search_terms:
            return 0.1
        
        username = (user.username or "").lower()
        email = (user.email or "").lower()
        full_name = (user.full_name or "").lower()
        
        for term in search_terms:
            term_lower = term.lower()
            
            # Exact matches
            if term_lower == username:
                score += 10.0
            elif term_lower in username:
                score += 5.0
            
            if term_lower in email:
                score += 3.0
            
            if term_lower in full_name:
                score += 4.0
        
        # Active users get bonus
        if user.is_active:
            score += 1.0
        
        # Recent login bonus
        if user.last_login:
            days_since_login = (datetime.utcnow() - user.last_login).days
            if days_since_login <= 30:
                score += 0.5
        
        return max(0.0, score)
    
    def _sort_results(self, results: List[SearchResult], sort_order: SortOrder) -> List[SearchResult]:
        """Sort search results"""
        
        if sort_order == SortOrder.RELEVANCE:
            return sorted(results, key=lambda x: x.score, reverse=True)
        elif sort_order == SortOrder.DATE_DESC:
            return sorted(results, key=lambda x: x.created_at, reverse=True)
        elif sort_order == SortOrder.DATE_ASC:
            return sorted(results, key=lambda x: x.created_at)
        elif sort_order == SortOrder.TITLE_ASC:
            return sorted(results, key=lambda x: x.title.lower())
        elif sort_order == SortOrder.TITLE_DESC:
            return sorted(results, key=lambda x: x.title.lower(), reverse=True)
        elif sort_order == SortOrder.DURATION_DESC:
            return sorted(results, key=lambda x: x.metadata.get('duration', 0), reverse=True)
        elif sort_order == SortOrder.DURATION_ASC:
            return sorted(results, key=lambda x: x.metadata.get('duration', 0))
        else:
            return results
    
    def _highlight_matches(self, text: str, query: str) -> str:
        """Highlight search matches in text"""
        
        if not text or not query:
            return text
        
        # Simple highlighting - in production, use more sophisticated highlighting
        highlighted = text
        search_terms = self._parse_search_terms(query)
        
        for term in search_terms:
            if len(term) >= 2:
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                highlighted = pattern.sub(f'<mark>{term}</mark>', highlighted)
        
        return highlighted
    
    def _get_duration_bucket(self, duration: float) -> str:
        """Get duration bucket for faceting"""
        
        if duration < 60:
            return "0-1min"
        elif duration < 300:
            return "1-5min"
        elif duration < 900:
            return "5-15min"
        elif duration < 1800:
            return "15-30min"
        elif duration < 3600:
            return "30-60min"
        else:
            return "60min+"
    
    def _generate_cache_key(self, search_query: SearchQuery, user_id: Optional[int]) -> str:
        """Generate cache key for search results"""
        
        key_data = {
            "query": search_query.query,
            "type": search_query.search_type.value,
            "scope": search_query.scope.value,
            "filters": [asdict(f) for f in (search_query.filters or [])],
            "sort": search_query.sort_order.value,
            "limit": search_query.limit,
            "offset": search_query.offset,
            "user_id": user_id
        }
        
        import hashlib
        key_str = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        
        return f"search_cache:{key_hash}"
    
    async def _get_cached_result(self, cache_key: str) -> Optional[SearchResponse]:
        """Get cached search result"""
        
        if not redis_cache.is_connected():
            return None
        
        try:
            cached_data = await redis_cache.get(cache_key)
            if cached_data:
                # Deserialize cached result
                data = json.loads(cached_data)
                
                # Convert back to objects
                results = []
                for result_data in data.get('results', []):
                    result = SearchResult(
                        id=result_data['id'],
                        type=result_data['type'],
                        title=result_data['title'],
                        content=result_data['content'],
                        highlighted_content=result_data['highlighted_content'],
                        metadata=result_data['metadata'],
                        score=result_data['score'],
                        created_at=datetime.fromisoformat(result_data['created_at']),
                        updated_at=datetime.fromisoformat(result_data['updated_at'])
                    )
                    results.append(result)
                
                return SearchResponse(
                    results=results,
                    total_count=data['total_count'],
                    query=data['query'],
                    search_time_ms=data['search_time_ms'],
                    facets=data['facets'],
                    suggestions=data['suggestions'],
                    filters_applied=[],  # Simplified for cache
                    page=data['page'],
                    per_page=data['per_page'],
                    has_more=data['has_more']
                )
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")
        
        return None
    
    async def _cache_result(self, cache_key: str, response: SearchResponse):
        """Cache search result"""
        
        if not redis_cache.is_connected():
            return
        
        try:
            # Serialize response for caching
            cache_data = {
                "results": [asdict(result) for result in response.results],
                "total_count": response.total_count,
                "query": response.query,
                "search_time_ms": response.search_time_ms,
                "facets": response.facets,
                "suggestions": response.suggestions,
                "page": response.page,
                "per_page": response.per_page,
                "has_more": response.has_more
            }
            
            # Convert datetime objects to strings
            for result in cache_data["results"]:
                if isinstance(result.get('created_at'), datetime):
                    result['created_at'] = result['created_at'].isoformat()
                if isinstance(result.get('updated_at'), datetime):
                    result['updated_at'] = result['updated_at'].isoformat()
            
            await redis_cache.set(
                cache_key, 
                json.dumps(cache_data, default=str), 
                expiry=self.cache_ttl
            )
        except Exception as e:
            logger.warning(f"Cache storage error: {e}")
    
    async def _record_search_analytics(
        self, 
        search_query: SearchQuery, 
        user_id: Optional[int], 
        results_count: int, 
        search_time_ms: float
    ):
        """Record search analytics"""
        
        analytics = SearchAnalytics(
            query=search_query.query,
            user_id=user_id,
            search_type=search_query.search_type,
            scope=search_query.scope,
            results_count=results_count,
            search_time_ms=search_time_ms,
            clicked_result_ids=[],
            timestamp=datetime.utcnow()
        )
        
        self.search_analytics.append(analytics)
        
        # Keep only recent analytics (last 10000 searches)
        if len(self.search_analytics) > 10000:
            self.search_analytics = self.search_analytics[-10000:]
    
    def _update_search_suggestions(self, query: str):
        """Update search suggestions based on query"""
        
        if len(query.strip()) >= 3:
            self.popular_queries[query.lower().strip()] += 1
            
            # Generate completion suggestions
            terms = query.lower().split()
            if terms:
                prefix = terms[-1]
                if len(prefix) >= 2:
                    if prefix not in self.query_completions:
                        self.query_completions[prefix] = []
                    
                    if query not in self.query_completions[prefix]:
                        self.query_completions[prefix].append(query)
                        # Keep only top 10 completions per prefix
                        self.query_completions[prefix] = self.query_completions[prefix][-10:]
    
    async def _generate_suggestions(self, query: str) -> List[str]:
        """Generate search suggestions"""
        
        suggestions = []
        
        if not query or len(query.strip()) < 2:
            # Return popular queries
            popular = sorted(
                self.popular_queries.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            return [q for q, _ in popular]
        
        query_lower = query.lower().strip()
        
        # Exact matches
        if query_lower in self.popular_queries:
            suggestions.append(query)
        
        # Prefix matches
        for popular_query, count in self.popular_queries.items():
            if popular_query.startswith(query_lower) and popular_query != query_lower:
                suggestions.append(popular_query)
                if len(suggestions) >= 5:
                    break
        
        # Partial matches
        if len(suggestions) < 5:
            for popular_query, count in self.popular_queries.items():
                if query_lower in popular_query and popular_query not in suggestions:
                    suggestions.append(popular_query)
                    if len(suggestions) >= 5:
                        break
        
        return suggestions[:5]
    
    async def get_search_analytics(
        self, 
        user_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get search analytics"""
        
        since = datetime.utcnow() - timedelta(days=days)
        
        # Filter analytics
        relevant_analytics = [
            a for a in self.search_analytics 
            if a.timestamp >= since and (user_id is None or a.user_id == user_id)
        ]
        
        if not relevant_analytics:
            return {
                "total_searches": 0,
                "unique_queries": 0,
                "avg_search_time_ms": 0,
                "avg_results_count": 0,
                "popular_queries": [],
                "search_types": {},
                "search_scopes": {},
                "daily_stats": {}
            }
        
        # Calculate statistics
        total_searches = len(relevant_analytics)
        unique_queries = len(set(a.query.lower() for a in relevant_analytics))
        avg_search_time = sum(a.search_time_ms for a in relevant_analytics) / total_searches
        avg_results = sum(a.results_count for a in relevant_analytics) / total_searches
        
        # Popular queries
        query_counts = Counter(a.query.lower() for a in relevant_analytics)
        popular_queries = query_counts.most_common(10)
        
        # Search types and scopes
        search_types = Counter(a.search_type.value for a in relevant_analytics)
        search_scopes = Counter(a.scope.value for a in relevant_analytics)
        
        # Daily statistics
        daily_stats = defaultdict(lambda: {"searches": 0, "avg_time": 0, "avg_results": 0})
        daily_groups = defaultdict(list)
        
        for analytics in relevant_analytics:
            day_key = analytics.timestamp.strftime("%Y-%m-%d")
            daily_groups[day_key].append(analytics)
        
        for day, day_analytics in daily_groups.items():
            daily_stats[day] = {
                "searches": len(day_analytics),
                "avg_time": sum(a.search_time_ms for a in day_analytics) / len(day_analytics),
                "avg_results": sum(a.results_count for a in day_analytics) / len(day_analytics)
            }
        
        return {
            "total_searches": total_searches,
            "unique_queries": unique_queries,
            "avg_search_time_ms": round(avg_search_time, 2),
            "avg_results_count": round(avg_results, 2),
            "popular_queries": [{"query": q, "count": c} for q, c in popular_queries],
            "search_types": dict(search_types),
            "search_scopes": dict(search_scopes),
            "daily_stats": dict(daily_stats)
        }
    
    async def record_search_click(self, user_id: Optional[int], query: str, result_id: str):
        """Record when a user clicks on a search result"""
        
        # Find recent search analytics for this user and query
        for analytics in reversed(self.search_analytics):
            if (analytics.user_id == user_id and 
                analytics.query.lower() == query.lower() and 
                (datetime.utcnow() - analytics.timestamp).total_seconds() < 3600):  # Within last hour
                
                if result_id not in analytics.clicked_result_ids:
                    analytics.clicked_result_ids.append(result_id)
                break
    
    async def get_search_suggestions(self, prefix: str, limit: int = 10) -> List[str]:
        """Get search suggestions for autocomplete"""
        
        if len(prefix) < 2:
            return []
        
        suggestions = set()
        prefix_lower = prefix.lower()
        
        # Check query completions
        for stored_prefix, completions in self.query_completions.items():
            if stored_prefix.startswith(prefix_lower):
                suggestions.update(completions)
        
        # Check popular queries
        for query in self.popular_queries.keys():
            if query.startswith(prefix_lower):
                suggestions.add(query)
        
        # Sort by popularity and return top results
        sorted_suggestions = sorted(
            suggestions, 
            key=lambda x: self.popular_queries.get(x, 0), 
            reverse=True
        )
        
        return sorted_suggestions[:limit]


# Global search service instance
search_service = ComprehensiveSearchService()