#!/usr/bin/env python3
"""
Base NER (Named Entity Recognition) Module
Provides abstract base class and common utilities for NER implementations
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
import logging
import re

logger = logging.getLogger(__name__)

@dataclass
class EntityValidationConfig:
    """Configuration for entity validation"""
    min_length: int = 2
    max_length: int = 100
    blacklist_patterns: List[str] = None
    whitelist_patterns: List[str] = None
    case_sensitive: bool = False
    
    def __post_init__(self):
        if self.blacklist_patterns is None:
            self.blacklist_patterns = [
                r'^\d+$',  # Pure numbers
                r'^[^\w\s]+$',  # Only special characters
                r'^\s+$',  # Only whitespace
            ]
        if self.whitelist_patterns is None:
            self.whitelist_patterns = []


class BaseNER(ABC):
    """Abstract base class for Named Entity Recognition implementations"""
    
    def __init__(self, validation_config: Optional[EntityValidationConfig] = None):
        """
        Initialize the NER extractor
        
        Args:
            validation_config: Configuration for entity validation
        """
        self.validation_config = validation_config or EntityValidationConfig()
        self._initialize()
    
    @abstractmethod
    def _initialize(self):
        """Initialize the specific NER implementation (models, API clients, etc.)"""
        pass
    
    @abstractmethod
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities from text
        
        Args:
            text: Input text for entity extraction
            
        Returns:
            Dictionary mapping entity types to lists of entity values
        """
        pass
    
    def validate_entity(self, entity: str) -> bool:
        """
        Validate a single entity based on configuration
        
        Args:
            entity: Entity text to validate
            
        Returns:
            True if entity is valid, False otherwise
        """
        if not entity or not isinstance(entity, str):
            return False
        
        entity_clean = entity.strip()
        
        # Check length constraints
        if len(entity_clean) < self.validation_config.min_length:
            return False
        if len(entity_clean) > self.validation_config.max_length:
            return False
        
        # Check blacklist patterns
        for pattern in self.validation_config.blacklist_patterns:
            flags = 0 if self.validation_config.case_sensitive else re.IGNORECASE
            if re.match(pattern, entity_clean, flags):
                return False
        
        # Check whitelist patterns (if any specified)
        if self.validation_config.whitelist_patterns:
            matched = False
            for pattern in self.validation_config.whitelist_patterns:
                flags = 0 if self.validation_config.case_sensitive else re.IGNORECASE
                if re.match(pattern, entity_clean, flags):
                    matched = True
                    break
            if not matched:
                return False
        
        return True
    
    def filter_entities(self, entities: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Filter and clean extracted entities
        
        Args:
            entities: Dictionary of entity types to entity lists
            
        Returns:
            Filtered dictionary with valid entities only
        """
        filtered = {}
        
        for entity_type, entity_list in entities.items():
            if not isinstance(entity_list, list):
                logger.warning(f"Invalid entity list for type {entity_type}")
                continue
            
            # Filter valid entities and remove duplicates
            valid_entities = []
            seen = set()
            
            for entity in entity_list:
                if not self.validate_entity(entity):
                    continue
                
                # Normalize for duplicate detection
                normalized = entity.strip()
                if not self.validation_config.case_sensitive:
                    normalized = normalized.lower()
                
                if normalized not in seen:
                    seen.add(normalized)
                    valid_entities.append(entity.strip())
            
            if valid_entities:
                filtered[entity_type] = valid_entities
        
        return filtered
    
    def merge_entities(self, *entity_dicts: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Merge multiple entity dictionaries, removing duplicates
        
        Args:
            *entity_dicts: Variable number of entity dictionaries to merge
            
        Returns:
            Merged dictionary with unique entities
        """
        merged = {}
        
        for entity_dict in entity_dicts:
            for entity_type, entity_list in entity_dict.items():
                if entity_type not in merged:
                    merged[entity_type] = []
                
                # Add unique entities
                existing = set(merged[entity_type])
                if not self.validation_config.case_sensitive:
                    existing = set(e.lower() for e in existing)
                
                for entity in entity_list:
                    check_entity = entity if self.validation_config.case_sensitive else entity.lower()
                    if check_entity not in existing:
                        merged[entity_type].append(entity)
                        existing.add(check_entity)
        
        return merged
    
    def get_entity_statistics(self, entities: Dict[str, List[str]]) -> Dict[str, int]:
        """
        Get statistics about extracted entities
        
        Args:
            entities: Dictionary of entity types to entity lists
            
        Returns:
            Dictionary with entity counts by type
        """
        stats = {
            'total': 0,
            'types': {}
        }
        
        for entity_type, entity_list in entities.items():
            count = len(entity_list)
            stats['types'][entity_type] = count
            stats['total'] += count
        
        return stats
    
    def format_entities_for_display(self, entities: Dict[str, List[str]], 
                                   max_per_type: int = 5) -> str:
        """
        Format entities for human-readable display
        
        Args:
            entities: Dictionary of entity types to entity lists
            max_per_type: Maximum number of entities to show per type
            
        Returns:
            Formatted string representation
        """
        if not entities:
            return "No entities found."
        
        lines = []
        for entity_type, entity_list in sorted(entities.items()):
            if not entity_list:
                continue
            
            # Format entity type name
            type_display = entity_type.replace('_', ' ').title()
            lines.append(f"\n{type_display}:")
            
            # Show entities (limited by max_per_type)
            for i, entity in enumerate(entity_list[:max_per_type]):
                lines.append(f"  • {entity}")
            
            # Show count if there are more
            if len(entity_list) > max_per_type:
                remaining = len(entity_list) - max_per_type
                lines.append(f"  ... and {remaining} more")
        
        return '\n'.join(lines)


# Common entity type mappings for consistency across implementations
ENTITY_TYPE_MAPPINGS = {
    # spaCy to standard mappings
    'PERSON': 'person',
    'PER': 'person',
    'ORG': 'organization',
    'GPE': 'location',
    'LOC': 'location',
    'DATE': 'date',
    'TIME': 'time',
    'MONEY': 'money',
    'PERCENT': 'percentage',
    'PRODUCT': 'product',
    'EVENT': 'event',
    'FAC': 'facility',
    'LAW': 'law',
    'LANGUAGE': 'language',
    'WORK_OF_ART': 'work_of_art',
    'NORP': 'group',  # Nationalities, religious, political groups
    'QUANTITY': 'quantity',
    'ORDINAL': 'ordinal',
    'CARDINAL': 'cardinal',
    
    # Additional mappings for other NER systems
    'MISC': 'miscellaneous',
    'EMAIL': 'email',
    'URL': 'url',
    'PHONE': 'phone_number',
}


def normalize_entity_type(entity_type: str) -> str:
    """
    Normalize entity type names for consistency
    
    Args:
        entity_type: Raw entity type from NER system
        
    Returns:
        Normalized entity type
    """
    # Check mapping first
    if entity_type in ENTITY_TYPE_MAPPINGS:
        return ENTITY_TYPE_MAPPINGS[entity_type]
    
    # Otherwise, lowercase and replace spaces/special chars
    return entity_type.lower().replace(' ', '_').replace('-', '_')


def combine_ner_results(basic_entities: Dict[str, List[str]], 
                       advanced_entities: Optional[Tuple[Dict[str, List[str]], str]] = None,
                       normalize_types: bool = True) -> Dict[str, List[str]]:
    """
    Combine results from basic and advanced NER
    
    Args:
        basic_entities: Results from basic NER
        advanced_entities: Results from advanced NER (entities, summary)
        normalize_types: Whether to normalize entity types
        
    Returns:
        Combined entity dictionary
    """
    # Handle advanced entities format (tuple with summary)
    if advanced_entities and isinstance(advanced_entities, tuple):
        advanced_dict = advanced_entities[0]
    else:
        advanced_dict = advanced_entities or {}
    
    # Normalize types if requested
    if normalize_types:
        basic_normalized = {}
        for entity_type, entities in basic_entities.items():
            normalized_type = normalize_entity_type(entity_type)
            if normalized_type not in basic_normalized:
                basic_normalized[normalized_type] = []
            basic_normalized[normalized_type].extend(entities)
        
        advanced_normalized = {}
        for entity_type, entities in advanced_dict.items():
            normalized_type = normalize_entity_type(entity_type)
            if normalized_type not in advanced_normalized:
                advanced_normalized[normalized_type] = []
            advanced_normalized[normalized_type].extend(entities)
        
        basic_entities = basic_normalized
        advanced_dict = advanced_normalized
    
    # Merge results
    combined = {}
    all_types = set(basic_entities.keys()) | set(advanced_dict.keys())
    
    for entity_type in all_types:
        combined[entity_type] = list(set(
            basic_entities.get(entity_type, []) + 
            advanced_dict.get(entity_type, [])
        ))
    
    return combined