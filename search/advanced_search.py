"""
Advanced Search System with Operators
Supports complex queries with AND, OR, NOT, wildcards, phrases, and field-specific searches
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)


class SearchOperator(Enum):
    """Search operators"""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    NEAR = "NEAR"
    WILDCARD = "*"
    PHRASE = '"'
    FIELD = ":"


@dataclass
class SearchToken:
    """Represents a search token"""
    type: str  # 'term', 'operator', 'field', 'phrase'
    value: str
    field: Optional[str] = None
    proximity: Optional[int] = None


@dataclass
class SearchFilter:
    """Search filters"""
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    languages: List[str] = None
    speakers: List[str] = None
    duration_min: Optional[int] = None
    duration_max: Optional[int] = None
    entities: List[str] = None
    topics: List[str] = None
    file_types: List[str] = None
    tags: List[str] = None


@dataclass
class SearchResult:
    """Search result with relevance scoring"""
    transcript_id: str
    title: str
    snippet: str
    highlights: List[Dict[str, Any]]
    relevance_score: float
    matched_fields: List[str]
    metadata: Dict[str, Any]


class AdvancedSearchParser:
    """Parses advanced search queries into structured tokens"""
    
    def __init__(self):
        # Define searchable fields
        self.searchable_fields = {
            'title', 'content', 'speaker', 'entity', 'topic', 
            'tag', 'language', 'transcript', 'summary', 'note'
        }
        
        # Field aliases for user convenience
        self.field_aliases = {
            'text': 'content',
            'person': 'entity',
            'lang': 'language',
            'subject': 'topic'
        }
        
        # Operators pattern
        self.operator_pattern = re.compile(r'\b(AND|OR|NOT|NEAR)\b', re.IGNORECASE)
        
        # Field search pattern (field:value)
        self.field_pattern = re.compile(r'(\w+):([^\s]+|"[^"]+"|\'[^\']+\')')
        
        # Phrase pattern
        self.phrase_pattern = re.compile(r'"([^"]+)"|\'([^\']+)\'')
        
        # Date patterns
        self.relative_date_pattern = re.compile(
            r'(today|yesterday|tomorrow|last\s+\d+\s+days?|next\s+\d+\s+days?|'
            r'last\s+week|next\s+week|last\s+month|next\s+month)'
        )
    
    def parse(self, query: str) -> List[SearchToken]:
        """
        Parse search query into tokens
        
        Examples:
        - machine learning AND python
        - "artificial intelligence" NOT bias
        - speaker:john OR speaker:jane
        - entity:Google NEAR entity:AI
        - title:transcript* AND date:last-7-days
        """
        tokens = []
        remaining_query = query
        
        # Extract field searches first
        field_matches = list(self.field_pattern.finditer(remaining_query))
        field_positions = [(m.start(), m.end()) for m in field_matches]
        
        for match in field_matches:
            field = match.group(1).lower()
            value = match.group(2).strip('"\'')
            
            # Resolve field aliases
            field = self.field_aliases.get(field, field)
            
            if field in self.searchable_fields:
                tokens.append(SearchToken(
                    type='field',
                    value=value,
                    field=field
                ))
        
        # Remove field searches from query
        for start, end in reversed(field_positions):
            remaining_query = remaining_query[:start] + ' ' + remaining_query[end:]
        
        # Extract phrases
        phrase_matches = list(self.phrase_pattern.finditer(remaining_query))
        phrase_positions = [(m.start(), m.end()) for m in phrase_matches]
        
        for match in phrase_matches:
            phrase = match.group(1) or match.group(2)
            tokens.append(SearchToken(type='phrase', value=phrase))
        
        # Remove phrases from query
        for start, end in reversed(phrase_positions):
            remaining_query = remaining_query[:start] + ' ' + remaining_query[end:]
        
        # Extract operators
        parts = self.operator_pattern.split(remaining_query)
        operators = self.operator_pattern.findall(remaining_query)
        
        # Process remaining terms and operators
        for i, part in enumerate(parts):
            # Add terms
            terms = part.strip().split()
            for term in terms:
                if term:
                    # Check for wildcards
                    if '*' in term or '?' in term:
                        tokens.append(SearchToken(type='wildcard', value=term))
                    else:
                        tokens.append(SearchToken(type='term', value=term))
            
            # Add operator if exists
            if i < len(operators):
                tokens.append(SearchToken(
                    type='operator', 
                    value=operators[i].upper()
                ))
        
        # If no tokens, treat entire query as a phrase
        if not tokens and query.strip():
            tokens.append(SearchToken(type='phrase', value=query.strip()))
        
        return tokens
    
    def parse_filters(self, filter_string: str) -> SearchFilter:
        """Parse filter string into SearchFilter object"""
        filters = SearchFilter()
        
        # Parse date filters
        date_match = re.search(r'date:(\S+)', filter_string)
        if date_match:
            date_value = date_match.group(1)
            date_range = self._parse_date_range(date_value)
            if date_range:
                filters.date_from, filters.date_to = date_range
        
        # Parse language filters
        lang_matches = re.findall(r'language:(\w+)', filter_string)
        if lang_matches:
            filters.languages = lang_matches
        
        # Parse speaker filters
        speaker_matches = re.findall(r'speaker:([^\s]+)', filter_string)
        if speaker_matches:
            filters.speakers = [s.strip('"\'') for s in speaker_matches]
        
        # Parse duration filters
        duration_match = re.search(r'duration:(\d+)-(\d+)', filter_string)
        if duration_match:
            filters.duration_min = int(duration_match.group(1))
            filters.duration_max = int(duration_match.group(2))
        
        # Parse entity filters
        entity_matches = re.findall(r'entity:([^\s]+)', filter_string)
        if entity_matches:
            filters.entities = [e.strip('"\'') for e in entity_matches]
        
        # Parse topic filters
        topic_matches = re.findall(r'topic:([^\s]+)', filter_string)
        if topic_matches:
            filters.topics = [t.strip('"\'') for t in topic_matches]
        
        return filters
    
    def _parse_date_range(self, date_value: str) -> Optional[Tuple[datetime, datetime]]:
        """Parse date range from various formats"""
        now = datetime.now()
        
        # Relative dates
        if date_value == 'today':
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            return start, end
        
        elif date_value == 'yesterday':
            start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            return start, end
        
        elif date_value == 'last-7-days':
            end = now
            start = now - timedelta(days=7)
            return start, end
        
        elif date_value == 'last-30-days':
            end = now
            start = now - timedelta(days=30)
            return start, end
        
        elif date_value == 'this-week':
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7)
            return start, end
        
        elif date_value == 'last-week':
            start = now - timedelta(days=now.weekday() + 7)
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7)
            return start, end
        
        elif date_value == 'this-month':
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Get first day of next month
            if now.month == 12:
                end = now.replace(year=now.year + 1, month=1, day=1)
            else:
                end = now.replace(month=now.month + 1, day=1)
            return start, end
        
        # ISO date format
        elif re.match(r'\d{4}-\d{2}-\d{2}', date_value):
            try:
                date = datetime.strptime(date_value, '%Y-%m-%d')
                return date, date + timedelta(days=1)
            except ValueError:
                pass
        
        # Date range format
        elif '..' in date_value:
            parts = date_value.split('..')
            if len(parts) == 2:
                try:
                    start = datetime.strptime(parts[0], '%Y-%m-%d')
                    end = datetime.strptime(parts[1], '%Y-%m-%d')
                    return start, end
                except ValueError:
                    pass
        
        return None


class SearchQueryBuilder:
    """Builds search queries for different backends"""
    
    def __init__(self):
        self.parser = AdvancedSearchParser()
    
    def build_elasticsearch_query(self, tokens: List[SearchToken], filters: SearchFilter) -> Dict[str, Any]:
        """Build Elasticsearch query from tokens"""
        must_clauses = []
        must_not_clauses = []
        should_clauses = []
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            if token.type == 'term':
                # Check if followed by operator
                if i + 1 < len(tokens) and tokens[i + 1].type == 'operator':
                    operator = tokens[i + 1].value
                    if operator == 'NOT' and i + 2 < len(tokens):
                        must_not_clauses.append({
                            "match": {"content": tokens[i + 2].value}
                        })
                        i += 3
                        continue
                    elif operator == 'OR' and i + 2 < len(tokens):
                        should_clauses.append({
                            "match": {"content": token.value}
                        })
                        should_clauses.append({
                            "match": {"content": tokens[i + 2].value}
                        })
                        i += 3
                        continue
                
                # Default AND behavior
                must_clauses.append({
                    "match": {"content": token.value}
                })
            
            elif token.type == 'phrase':
                must_clauses.append({
                    "match_phrase": {"content": token.value}
                })
            
            elif token.type == 'wildcard':
                must_clauses.append({
                    "wildcard": {"content": token.value.lower()}
                })
            
            elif token.type == 'field':
                if token.field:
                    must_clauses.append({
                        "match": {token.field: token.value}
                    })
            
            i += 1
        
        # Build the query
        query = {
            "bool": {
                "must": must_clauses,
                "must_not": must_not_clauses,
                "should": should_clauses,
                "minimum_should_match": 1 if should_clauses else 0
            }
        }
        
        # Add filters
        filter_clauses = []
        
        if filters.date_from or filters.date_to:
            date_range = {}
            if filters.date_from:
                date_range["gte"] = filters.date_from.isoformat()
            if filters.date_to:
                date_range["lte"] = filters.date_to.isoformat()
            filter_clauses.append({"range": {"created_at": date_range}})
        
        if filters.languages:
            filter_clauses.append({"terms": {"language": filters.languages}})
        
        if filters.speakers:
            filter_clauses.append({"terms": {"speakers": filters.speakers}})
        
        if filters.duration_min is not None or filters.duration_max is not None:
            duration_range = {}
            if filters.duration_min is not None:
                duration_range["gte"] = filters.duration_min
            if filters.duration_max is not None:
                duration_range["lte"] = filters.duration_max
            filter_clauses.append({"range": {"duration": duration_range}})
        
        if filter_clauses:
            query["bool"]["filter"] = filter_clauses
        
        return {"query": query}
    
    def build_sql_query(self, tokens: List[SearchToken], filters: SearchFilter) -> Tuple[str, List[Any]]:
        """Build SQL query from tokens"""
        conditions = []
        params = []
        
        # Build search conditions
        search_conditions = []
        for token in tokens:
            if token.type == 'term':
                search_conditions.append("content LIKE ?")
                params.append(f"%{token.value}%")
            elif token.type == 'phrase':
                search_conditions.append("content LIKE ?")
                params.append(f"%{token.value}%")
            elif token.type == 'wildcard':
                # Convert wildcard to SQL LIKE pattern
                pattern = token.value.replace('*', '%').replace('?', '_')
                search_conditions.append("content LIKE ?")
                params.append(pattern)
            elif token.type == 'field' and token.field:
                search_conditions.append(f"{token.field} LIKE ?")
                params.append(f"%{token.value}%")
        
        if search_conditions:
            conditions.append(f"({' OR '.join(search_conditions)})")
        
        # Add filters
        if filters.date_from:
            conditions.append("created_at >= ?")
            params.append(filters.date_from)
        
        if filters.date_to:
            conditions.append("created_at <= ?")
            params.append(filters.date_to)
        
        if filters.languages:
            placeholders = ','.join(['?' for _ in filters.languages])
            conditions.append(f"language IN ({placeholders})")
            params.extend(filters.languages)
        
        if filters.speakers:
            speaker_conditions = []
            for speaker in filters.speakers:
                speaker_conditions.append("speakers LIKE ?")
                params.append(f"%{speaker}%")
            conditions.append(f"({' OR '.join(speaker_conditions)})")
        
        if filters.duration_min is not None:
            conditions.append("duration >= ?")
            params.append(filters.duration_min)
        
        if filters.duration_max is not None:
            conditions.append("duration <= ?")
            params.append(filters.duration_max)
        
        # Build final query
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"""
        SELECT 
            id, title, content, speakers, language, duration,
            created_at, metadata
        FROM transcripts
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT 100
        """
        
        return query, params


class RelevanceScorer:
    """Calculates relevance scores for search results"""
    
    def __init__(self):
        self.field_weights = {
            'title': 2.0,
            'content': 1.0,
            'speaker': 1.5,
            'entity': 1.5,
            'topic': 1.8,
            'tag': 1.3,
            'summary': 1.2
        }
    
    def score_result(self, result: Dict[str, Any], tokens: List[SearchToken]) -> float:
        """Calculate relevance score for a search result"""
        score = 0.0
        matched_fields = set()
        
        # Extract searchable text from result
        searchable_text = {
            'title': result.get('title', '').lower(),
            'content': result.get('content', '').lower(),
            'speaker': ' '.join(result.get('speakers', [])).lower(),
            'entity': ' '.join(result.get('entities', [])).lower(),
            'topic': ' '.join(result.get('topics', [])).lower(),
            'tag': ' '.join(result.get('tags', [])).lower(),
            'summary': result.get('summary', '').lower()
        }
        
        # Score each token
        for token in tokens:
            if token.type in ['term', 'phrase']:
                search_term = token.value.lower()
                
                # Check each field
                for field, text in searchable_text.items():
                    if search_term in text:
                        # Base score
                        field_score = self.field_weights.get(field, 1.0)
                        
                        # Exact match bonus
                        if f' {search_term} ' in f' {text} ':
                            field_score *= 1.5
                        
                        # Position bonus (earlier matches score higher)
                        position = text.find(search_term)
                        position_bonus = 1.0 + (1.0 - position / max(len(text), 1)) * 0.5
                        field_score *= position_bonus
                        
                        # Frequency bonus
                        frequency = text.count(search_term)
                        frequency_bonus = 1.0 + min(frequency - 1, 5) * 0.1
                        field_score *= frequency_bonus
                        
                        score += field_score
                        matched_fields.add(field)
            
            elif token.type == 'field' and token.field:
                # Field-specific search
                field_text = searchable_text.get(token.field, '')
                if token.value.lower() in field_text:
                    score += self.field_weights.get(token.field, 1.0) * 2  # Double weight for field match
                    matched_fields.add(token.field)
        
        # Bonus for matching multiple fields
        if len(matched_fields) > 1:
            score *= (1.0 + len(matched_fields) * 0.1)
        
        # Recency bonus
        if 'created_at' in result:
            try:
                created_at = datetime.fromisoformat(result['created_at'])
                days_old = (datetime.now() - created_at).days
                recency_factor = max(0.5, 1.0 - days_old / 365)  # Decay over a year
                score *= recency_factor
            except:
                pass
        
        # Popularity bonus
        if 'view_count' in result:
            popularity_factor = 1.0 + min(result['view_count'] / 1000, 1.0) * 0.2
            score *= popularity_factor
        
        return round(score, 2)
    
    def generate_snippet(self, text: str, tokens: List[SearchToken], max_length: int = 200) -> str:
        """Generate snippet with highlighted search terms"""
        if not text:
            return ""
        
        # Find best matching section
        search_terms = []
        for token in tokens:
            if token.type in ['term', 'phrase']:
                search_terms.append(token.value.lower())
        
        if not search_terms:
            return text[:max_length] + "..." if len(text) > max_length else text
        
        # Find first occurrence of any search term
        text_lower = text.lower()
        best_position = len(text)
        
        for term in search_terms:
            pos = text_lower.find(term)
            if pos != -1 and pos < best_position:
                best_position = pos
        
        # Extract snippet around the match
        start = max(0, best_position - max_length // 2)
        end = min(len(text), start + max_length)
        
        # Adjust to word boundaries
        if start > 0:
            start = text.rfind(' ', 0, start) + 1
        if end < len(text):
            end = text.find(' ', end)
            if end == -1:
                end = len(text)
        
        snippet = text[start:end]
        
        # Add ellipsis
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        
        return snippet


class AdvancedSearchEngine:
    """Main search engine combining all components"""
    
    def __init__(self):
        self.parser = AdvancedSearchParser()
        self.query_builder = SearchQueryBuilder()
        self.scorer = RelevanceScorer()
    
    def search(self, 
               query: str,
               filters: Optional[SearchFilter] = None,
               limit: int = 50,
               offset: int = 0) -> Dict[str, Any]:
        """
        Perform advanced search
        
        Args:
            query: Search query with operators
            filters: Additional filters
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            Search results with metadata
        """
        try:
            # Parse query
            tokens = self.parser.parse(query)
            
            # Parse filters from query if not provided
            if not filters:
                filters = self.parser.parse_filters(query)
            
            # For demo, return mock results
            # In production, this would query the actual database
            results = self._mock_search_results(tokens, filters, limit, offset)
            
            # Score and rank results
            for result in results:
                result['relevance_score'] = self.scorer.score_result(result, tokens)
                result['snippet'] = self.scorer.generate_snippet(
                    result.get('content', ''), tokens
                )
            
            # Sort by relevance
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Generate search metadata
            metadata = {
                'query': query,
                'tokens': [{'type': t.type, 'value': t.value, 'field': t.field} for t in tokens],
                'filters': {
                    'date_from': filters.date_from.isoformat() if filters.date_from else None,
                    'date_to': filters.date_to.isoformat() if filters.date_to else None,
                    'languages': filters.languages,
                    'speakers': filters.speakers,
                    'duration_min': filters.duration_min,
                    'duration_max': filters.duration_max
                },
                'total_results': len(results),
                'limit': limit,
                'offset': offset
            }
            
            return {
                'results': results,
                'metadata': metadata,
                'suggestions': self._generate_suggestions(query, results)
            }
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise
    
    def _mock_search_results(self, tokens: List[SearchToken], filters: SearchFilter, 
                           limit: int, offset: int) -> List[Dict[str, Any]]:
        """Generate mock search results for demo"""
        mock_results = [
            {
                'id': 'transcript_001',
                'title': 'Introduction to Machine Learning with Python',
                'content': 'Today we will explore machine learning concepts using Python. We\'ll cover supervised learning, neural networks, and practical applications.',
                'speakers': ['Dr. John Smith'],
                'language': 'en',
                'duration': 3600,
                'created_at': (datetime.now() - timedelta(days=2)).isoformat(),
                'entities': ['Python', 'Machine Learning', 'Neural Networks'],
                'topics': ['AI', 'Programming', 'Data Science'],
                'tags': ['tutorial', 'beginner-friendly'],
                'view_count': 1500
            },
            {
                'id': 'transcript_002',
                'title': 'Advanced AI Ethics and Bias Prevention',
                'content': 'Discussion on ethical considerations in artificial intelligence, focusing on bias detection and prevention strategies.',
                'speakers': ['Dr. Jane Doe', 'Prof. Mark Johnson'],
                'language': 'en',
                'duration': 5400,
                'created_at': (datetime.now() - timedelta(days=7)).isoformat(),
                'entities': ['Google', 'OpenAI', 'MIT'],
                'topics': ['AI Ethics', 'Bias', 'Fairness'],
                'tags': ['ethics', 'advanced', 'panel-discussion'],
                'view_count': 2300
            },
            {
                'id': 'transcript_003',
                'title': 'Natural Language Processing Fundamentals',
                'content': 'Learn the basics of NLP including tokenization, embeddings, and transformer models.',
                'speakers': ['Sarah Chen'],
                'language': 'en',
                'duration': 4200,
                'created_at': (datetime.now() - timedelta(days=14)).isoformat(),
                'entities': ['BERT', 'GPT', 'Transformers'],
                'topics': ['NLP', 'Deep Learning', 'AI'],
                'tags': ['technical', 'intermediate'],
                'view_count': 890
            }
        ]
        
        # Filter based on search tokens
        filtered_results = []
        for result in mock_results:
            match = False
            for token in tokens:
                if token.type in ['term', 'phrase']:
                    # Check if term appears in searchable fields
                    searchable = ' '.join([
                        result.get('title', ''),
                        result.get('content', ''),
                        ' '.join(result.get('speakers', [])),
                        ' '.join(result.get('entities', [])),
                        ' '.join(result.get('topics', [])),
                        ' '.join(result.get('tags', []))
                    ]).lower()
                    
                    if token.value.lower() in searchable:
                        match = True
                        break
            
            if match or not tokens:
                filtered_results.append(result)
        
        # Apply filters
        if filters.languages:
            filtered_results = [r for r in filtered_results if r.get('language') in filters.languages]
        
        if filters.speakers:
            filtered_results = [r for r in filtered_results 
                              if any(speaker in ' '.join(r.get('speakers', [])) 
                                    for speaker in filters.speakers)]
        
        # Apply pagination
        return filtered_results[offset:offset + limit]
    
    def _generate_suggestions(self, query: str, results: List[Dict[str, Any]]) -> List[str]:
        """Generate search suggestions based on query and results"""
        suggestions = []
        
        # Suggest related topics from results
        all_topics = set()
        for result in results[:10]:  # Look at top 10 results
            all_topics.update(result.get('topics', []))
        
        # Remove topics already in query
        query_lower = query.lower()
        suggested_topics = [t for t in all_topics if t.lower() not in query_lower]
        
        if suggested_topics:
            suggestions.extend([f'topic:{topic}' for topic in suggested_topics[:3]])
        
        # Suggest filters if not used
        if 'date:' not in query:
            suggestions.append('date:last-7-days')
        
        if 'language:' not in query:
            suggestions.append('language:en')
        
        # Suggest operators if not used
        if ' AND ' not in query.upper() and ' OR ' not in query.upper():
            tokens = query.split()
            if len(tokens) >= 2:
                suggestions.append(f'{tokens[0]} AND {tokens[1]}')
        
        return suggestions[:5]  # Return top 5 suggestions