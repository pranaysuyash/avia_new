"""
Filter engine for advanced search
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, date
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class SearchFilter:
    """Represents a search filter"""
    field: str
    operator: str  # =, >, <, >=, <=, in, contains, between
    value: Any
    
    def to_sql(self) -> tuple:
        """Convert to SQL WHERE clause and parameters"""
        if self.operator == '=':
            return f"{self.field} = ?", [self.value]
        elif self.operator == '>':
            return f"{self.field} > ?", [self.value]
        elif self.operator == '<':
            return f"{self.field} < ?", [self.value]
        elif self.operator == '>=':
            return f"{self.field} >= ?", [self.value]
        elif self.operator == '<=':
            return f"{self.field} <= ?", [self.value]
        elif self.operator == 'in':
            placeholders = ','.join(['?' for _ in self.value])
            return f"{self.field} IN ({placeholders})", list(self.value)
        elif self.operator == 'contains':
            return f"{self.field} LIKE ?", [f"%{self.value}%"]
        elif self.operator == 'between':
            return f"{self.field} BETWEEN ? AND ?", [self.value[0], self.value[1]]
        else:
            raise ValueError(f"Unknown operator: {self.operator}")


class FilterEngine:
    """Engine for applying complex filters to search results"""
    
    def __init__(self):
        self.custom_filters: Dict[str, Callable] = {}
        self._register_default_filters()
        
    def _register_default_filters(self):
        """Register default filter handlers"""
        self.register_filter('entity_type', self._filter_entity_type)
        self.register_filter('word_count', self._filter_word_count)
        self.register_filter('has_entities', self._filter_has_entities)
        self.register_filter('sentiment', self._filter_sentiment)
        
    def register_filter(self, name: str, handler: Callable):
        """Register a custom filter handler"""
        self.custom_filters[name] = handler
        
    def apply_filters(self, results: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
        """Apply filters to search results"""
        filtered_results = results
        
        # Apply custom filters
        for filter_name, filter_value in filters.items():
            if filter_name in self.custom_filters:
                handler = self.custom_filters[filter_name]
                filtered_results = handler(filtered_results, filter_value)
                
        return filtered_results
        
    def _filter_entity_type(self, results: List[Dict], entity_types: List[str]) -> List[Dict]:
        """Filter results by entity types"""
        if not entity_types:
            return results
            
        filtered = []
        for result in results:
            metadata = result.get('metadata', {})
            entities = metadata.get('entities', [])
            
            # Check if any entity matches the requested types
            has_matching_entity = any(
                entity.get('label') in entity_types 
                for entity in entities
            )
            
            if has_matching_entity:
                filtered.append(result)
                
        return filtered
        
    def _filter_word_count(self, results: List[Dict], word_count_filter: Dict) -> List[Dict]:
        """Filter by word count"""
        min_words = word_count_filter.get('min', 0)
        max_words = word_count_filter.get('max', float('inf'))
        
        filtered = []
        for result in results:
            content = result.get('content', '')
            word_count = len(content.split())
            
            if min_words <= word_count <= max_words:
                filtered.append(result)
                
        return filtered
        
    def _filter_has_entities(self, results: List[Dict], has_entities: bool) -> List[Dict]:
        """Filter by presence of entities"""
        filtered = []
        for result in results:
            metadata = result.get('metadata', {})
            entities = metadata.get('entities', [])
            
            if has_entities and entities:
                filtered.append(result)
            elif not has_entities and not entities:
                filtered.append(result)
                
        return filtered
        
    def _filter_sentiment(self, results: List[Dict], sentiment_filter: str) -> List[Dict]:
        """Filter by sentiment (if available in metadata)"""
        filtered = []
        for result in results:
            metadata = result.get('metadata', {})
            sentiment = metadata.get('sentiment')
            
            if sentiment and sentiment.lower() == sentiment_filter.lower():
                filtered.append(result)
                
        return filtered
        
    def build_facets(self, results: List[Dict]) -> Dict[str, Dict[str, int]]:
        """Build facet counts from results"""
        facets = {
            'entity_types': {},
            'tags': {},
            'speakers': {},
            'languages': {},
            'sentiments': {},
            'years': {}
        }
        
        for result in results:
            # Entity types
            metadata = result.get('metadata', {})
            entities = metadata.get('entities', [])
            for entity in entities:
                entity_type = entity.get('label', 'UNKNOWN')
                facets['entity_types'][entity_type] = facets['entity_types'].get(entity_type, 0) + 1
                
            # Tags
            tags = result.get('tags', [])
            for tag in tags:
                facets['tags'][tag] = facets['tags'].get(tag, 0) + 1
                
            # Speakers
            speakers = result.get('speakers', [])
            for speaker in speakers:
                facets['speakers'][speaker] = facets['speakers'].get(speaker, 0) + 1
                
            # Language
            language = result.get('language', 'unknown')
            facets['languages'][language] = facets['languages'].get(language, 0) + 1
            
            # Sentiment
            sentiment = metadata.get('sentiment')
            if sentiment:
                facets['sentiments'][sentiment] = facets['sentiments'].get(sentiment, 0) + 1
                
            # Year
            created_at = result.get('created_at')
            if created_at:
                try:
                    year = datetime.fromisoformat(created_at).year
                    facets['years'][str(year)] = facets['years'].get(str(year), 0) + 1
                except:
                    pass
                    
        # Sort facets by count
        for facet_type in facets:
            facets[facet_type] = dict(
                sorted(facets[facet_type].items(), 
                      key=lambda x: x[1], 
                      reverse=True)
            )
            
        return facets
        
    def validate_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize filter values"""
        validated = {}
        
        # Date range validation
        if 'date_range' in filters:
            date_range = filters['date_range']
            if 'start' in date_range:
                try:
                    # Ensure it's a valid date
                    datetime.fromisoformat(date_range['start'])
                    validated.setdefault('date_range', {})['start'] = date_range['start']
                except:
                    logger.warning(f"Invalid start date: {date_range['start']}")
                    
            if 'end' in date_range:
                try:
                    datetime.fromisoformat(date_range['end'])
                    validated.setdefault('date_range', {})['end'] = date_range['end']
                except:
                    logger.warning(f"Invalid end date: {date_range['end']}")
                    
        # Confidence validation
        if 'min_confidence' in filters:
            try:
                confidence = float(filters['min_confidence'])
                if 0 <= confidence <= 1:
                    validated['min_confidence'] = confidence
            except:
                logger.warning(f"Invalid confidence value: {filters['min_confidence']}")
                
        # List filters
        for list_filter in ['tags', 'speakers', 'entity_types']:
            if list_filter in filters:
                value = filters[list_filter]
                if isinstance(value, list):
                    # Sanitize each item
                    validated[list_filter] = [str(item).strip() for item in value if item]
                elif isinstance(value, str):
                    validated[list_filter] = [value.strip()]
                    
        # Language validation
        if 'language' in filters:
            lang = str(filters['language']).lower().strip()
            if len(lang) == 2:  # Simple validation for 2-letter codes
                validated['language'] = lang
                
        return validated
        
    def merge_filters(self, *filter_sets: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple filter sets"""
        merged = {}
        
        for filters in filter_sets:
            for key, value in filters.items():
                if key == 'date_range' and key in merged:
                    # Special handling for date ranges
                    merged[key].update(value)
                elif key in ['tags', 'speakers', 'entity_types'] and key in merged:
                    # Merge lists
                    existing = set(merged[key])
                    new_items = set(value) if isinstance(value, list) else {value}
                    merged[key] = list(existing.union(new_items))
                else:
                    merged[key] = value
                    
        return merged