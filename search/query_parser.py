"""
Query parser for advanced search functionality
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
import shlex

logger = logging.getLogger(__name__)


@dataclass
class ParsedQuery:
    """Represents a parsed search query"""
    raw_query: str
    search_terms: List[str] = field(default_factory=list)
    exact_phrases: List[str] = field(default_factory=list)
    excluded_terms: List[str] = field(default_factory=list)
    required_terms: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    operators: List[str] = field(default_factory=list)
    
    def to_fts_query(self) -> str:
        """Convert to FTS5 query syntax"""
        parts = []
        
        # Add required terms with +
        for term in self.required_terms:
            parts.append(f"+{term}")
            
        # Add search terms
        parts.extend(self.search_terms)
        
        # Add exact phrases with quotes
        for phrase in self.exact_phrases:
            parts.append(f'"{phrase}"')
            
        # Add excluded terms with -
        for term in self.excluded_terms:
            parts.append(f"-{term}")
            
        return ' '.join(parts)


class QueryParser:
    """Parse and interpret advanced search queries"""
    
    # Define filter patterns
    FILTER_PATTERNS = {
        'date': re.compile(r'(date|created|before|after|since):(\S+)'),
        'speaker': re.compile(r'speaker:(["\']?)([^"\'\s]+)\1'),
        'tag': re.compile(r'tag:(["\']?)([^"\'\s]+)\1'),
        'entity': re.compile(r'entity:(\w+)'),
        'type': re.compile(r'type:(\w+)'),
        'confidence': re.compile(r'confidence:([><=]+)?(\d*\.?\d+)'),
        'language': re.compile(r'lang(?:uage)?:(\w+)'),
        'duration': re.compile(r'duration:([><=]+)?(\d+)'),
    }
    
    # Boolean operators
    OPERATORS = ['AND', 'OR', 'NOT']
    
    def __init__(self):
        self.current_year = datetime.now().year
        
    def parse(self, query: str) -> ParsedQuery:
        """Parse a search query into components"""
        parsed = ParsedQuery(raw_query=query)
        
        # First extract filters
        query, filters = self._extract_filters(query)
        parsed.filters = filters
        
        # Then parse the remaining query
        self._parse_query_terms(query, parsed)
        
        return parsed
        
    def _extract_filters(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """Extract filter expressions from query"""
        filters = {}
        remaining_query = query
        
        # Extract date filters
        for match in self.FILTER_PATTERNS['date'].finditer(query):
            keyword = match.group(1)
            date_str = match.group(2)
            
            if 'date_range' not in filters:
                filters['date_range'] = {}
                
            parsed_date = self._parse_date(date_str)
            if parsed_date:
                if keyword in ['before']:
                    filters['date_range']['end'] = parsed_date
                elif keyword in ['after', 'since']:
                    filters['date_range']['start'] = parsed_date
                elif keyword in ['date', 'created']:
                    # Exact date - set both start and end to same day
                    filters['date_range']['start'] = parsed_date
                    filters['date_range']['end'] = parsed_date
                    
            remaining_query = remaining_query.replace(match.group(0), '')
            
        # Extract speaker filters
        speakers = []
        for match in self.FILTER_PATTERNS['speaker'].finditer(query):
            speaker = match.group(2)
            speakers.append(speaker)
            remaining_query = remaining_query.replace(match.group(0), '')
            
        if speakers:
            filters['speakers'] = speakers
            
        # Extract tag filters
        tags = []
        for match in self.FILTER_PATTERNS['tag'].finditer(query):
            tag = match.group(2)
            tags.append(tag)
            remaining_query = remaining_query.replace(match.group(0), '')
            
        if tags:
            filters['tags'] = tags
            
        # Extract entity type filters
        entity_types = []
        for match in self.FILTER_PATTERNS['entity'].finditer(query):
            entity_type = match.group(1).upper()
            entity_types.append(entity_type)
            remaining_query = remaining_query.replace(match.group(0), '')
            
        if entity_types:
            filters['entity_types'] = entity_types
            
        # Extract confidence filter
        for match in self.FILTER_PATTERNS['confidence'].finditer(query):
            operator = match.group(1) or '>='
            value = float(match.group(2))
            
            if operator in ['>', '>=']:
                filters['min_confidence'] = value
            elif operator in ['<', '<=']:
                filters['max_confidence'] = value
            elif operator == '=':
                filters['exact_confidence'] = value
                
            remaining_query = remaining_query.replace(match.group(0), '')
            
        # Extract language filter
        for match in self.FILTER_PATTERNS['language'].finditer(query):
            language = match.group(1).lower()
            filters['language'] = language
            remaining_query = remaining_query.replace(match.group(0), '')
            
        return remaining_query.strip(), filters
        
    def _parse_query_terms(self, query: str, parsed: ParsedQuery):
        """Parse the text portion of the query"""
        # Handle quoted phrases first
        phrases = re.findall(r'"([^"]+)"', query)
        for phrase in phrases:
            parsed.exact_phrases.append(phrase)
            query = query.replace(f'"{phrase}"', '')
            
        # Split remaining query into tokens
        try:
            tokens = shlex.split(query)
        except ValueError:
            # Fallback to simple split if shlex fails
            tokens = query.split()
            
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            # Check for operators
            if token.upper() in self.OPERATORS:
                parsed.operators.append(token.upper())
                
                # Handle NOT operator
                if token.upper() == 'NOT' and i + 1 < len(tokens):
                    i += 1
                    parsed.excluded_terms.append(tokens[i])
                    
            # Check for excluded terms (starting with -)
            elif token.startswith('-') and len(token) > 1:
                parsed.excluded_terms.append(token[1:])
                
            # Check for required terms (starting with +)
            elif token.startswith('+') and len(token) > 1:
                parsed.required_terms.append(token[1:])
                
            # Regular search term
            else:
                parsed.search_terms.append(token)
                
            i += 1
            
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse various date formats"""
        date_str = date_str.strip()
        
        # Handle relative dates
        if date_str.lower() == 'today':
            return date.today().isoformat()
        elif date_str.lower() == 'yesterday':
            return (date.today() - timedelta(days=1)).isoformat()
        elif date_str.lower() == 'week':
            return (date.today() - timedelta(days=7)).isoformat()
        elif date_str.lower() == 'month':
            return (date.today() - timedelta(days=30)).isoformat()
        elif date_str.lower() == 'year':
            return (date.today() - timedelta(days=365)).isoformat()
            
        # Try to parse absolute dates
        date_formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%Y-%m',
            '%Y'
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt).date()
                return parsed_date.isoformat()
            except ValueError:
                continue
                
        # Handle year-only
        if date_str.isdigit() and len(date_str) == 4:
            return f"{date_str}-01-01"
            
        logger.warning(f"Could not parse date: {date_str}")
        return None
        
    def suggest_query(self, partial_query: str, search_history: List[str] = None) -> List[str]:
        """Suggest query completions based on partial input"""
        suggestions = []
        
        # Filter syntax suggestions
        if ':' in partial_query:
            last_part = partial_query.split()[-1]
            if last_part.startswith('speaker:'):
                # Could suggest known speakers
                pass
            elif last_part.startswith('tag:'):
                # Could suggest known tags
                pass
            elif last_part.startswith('entity:'):
                suggestions.extend(['entity:PERSON', 'entity:ORG', 'entity:LOC'])
                
        # Operator suggestions
        elif partial_query.endswith(' '):
            suggestions.extend(['AND', 'OR', 'NOT'])
            
        # Filter keyword suggestions
        else:
            filter_keywords = ['speaker:', 'tag:', 'entity:', 'date:', 'confidence:', 'language:']
            last_word = partial_query.split()[-1] if partial_query else ''
            
            for keyword in filter_keywords:
                if keyword.startswith(last_word.lower()):
                    suggestions.append(partial_query.rsplit(last_word, 1)[0] + keyword)
                    
        # Add history-based suggestions
        if search_history:
            for hist_query in search_history[:5]:
                if hist_query.lower().startswith(partial_query.lower()) and hist_query != partial_query:
                    suggestions.append(hist_query)
                    
        return suggestions[:10]  # Limit suggestions