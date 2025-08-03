#!/usr/bin/env python3
"""
Basic Named Entity Recognition Module
Handles entity extraction using spaCy's pre-trained models
Refactored to use BaseNER class
"""

import logging
import spacy
from typing import Dict, List, Optional
from collections import defaultdict

from errors import NERError, handle_error, ErrorCode
from ner_base import BaseNER, EntityValidationConfig, normalize_entity_type

logger = logging.getLogger(__name__)


class BasicNER(BaseNER):
    """Basic NER implementation using spaCy"""
    
    def __init__(self, model_name: str = "en_core_web_sm", 
                 validation_config: Optional[EntityValidationConfig] = None):
        """
        Initialize Basic NER with spaCy model
        
        Args:
            model_name: Name of spaCy model to use
            validation_config: Configuration for entity validation
        """
        self.model_name = model_name
        self.nlp = None
        
        # Set up validation config with additional patterns
        if validation_config is None:
            validation_config = EntityValidationConfig(
                min_length=2,
                max_length=100,
                blacklist_patterns=[
                    r'^\d+$',  # Pure numbers
                    r'^[^\w\s]+$',  # Only special characters
                    r'^\s+$',  # Only whitespace
                    r'^(the|and|or|but|in|on|at|to|for|of|with|by)$',  # Common words
                ]
            )
        
        super().__init__(validation_config)
    
    def _initialize(self):
        """Initialize the spaCy model"""
        try:
            self.nlp = spacy.load(self.model_name)
            logger.info(f"Successfully loaded spaCy {self.model_name} model")
        except OSError as e:
            logger.error(f"spaCy {self.model_name} model not found. Please install it with: python -m spacy download {self.model_name}")
            raise NERError(
                message=f"spaCy model not found: {e}",
                error_code=ErrorCode.NER_MODEL_ERROR,
                user_message="The language processing model is not installed.",
                ner_type="spacy",
                suggestions=[
                    f"Install the spaCy model: python -m spacy download {self.model_name}",
                    "Try using Advanced (AI) mode instead",
                    "Restart the application after installing the model"
                ]
            )
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {e}")
            raise NERError(
                message=f"Failed to load spaCy model: {e}",
                error_code=ErrorCode.NER_MODEL_ERROR,
                user_message="Failed to load the language processing model.",
                ner_type="spacy",
                suggestions=[
                    "Restart the application",
                    "Reinstall spaCy: pip install spacy",
                    "Try using Advanced (AI) mode instead"
                ]
            )
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract and categorize named entities from text using spaCy
        
        Args:
            text: Input text to process
            
        Returns:
            Dictionary with entity types as keys and lists of unique entities as values
        """
        if not text or not text.strip():
            return {}
        
        try:
            if not self.nlp:
                self._initialize()
            
            # Check text length for processing limits
            if len(text) > 1000000:  # 1MB text limit
                raise NERError(
                    message=f"Text too long for processing: {len(text)} characters",
                    error_code=ErrorCode.NER_INVALID_INPUT,
                    user_message="The text is too long for entity extraction.",
                    ner_type="spacy",
                    text_length=len(text),
                    suggestions=[
                        "Break the text into smaller chunks",
                        "Try processing a shorter transcript",
                        "Use Advanced (AI) mode for better handling of long texts"
                    ]
                )
            
            doc = self.nlp(text)
            
            # Dictionary to store categorized entities
            entities = defaultdict(set)
            
            # Extract entities
            for ent in doc.ents:
                entity_text = ent.text.strip()
                entity_label = ent.label_
                
                # Skip if doesn't pass basic validation
                if not self.validate_entity(entity_text):
                    continue
                
                # Additional spaCy-specific validation
                if self._is_likely_error(entity_text, entity_label):
                    continue
                
                # Normalize entity type
                normalized_type = normalize_entity_type(entity_label)
                entities[normalized_type].add(entity_text)
            
            # Convert sets to sorted lists
            result = {}
            for entity_type, entity_set in entities.items():
                if entity_set:
                    result[entity_type] = sorted(list(entity_set))
            
            # Apply final filtering
            filtered_result = self.filter_entities(result)
            
            logger.info(f"Extracted {sum(len(v) for v in filtered_result.values())} entities from text")
            return filtered_result
            
        except NERError:
            raise
        except Exception as e:
            logger.error(f"Error during entity extraction: {str(e)}")
            app_error = handle_error(e, {
                "ner_type": "spacy",
                "text_length": len(text) if text else 0,
                "operation": "entity_extraction"
            })
            raise app_error
    
    def _is_likely_error(self, entity_text: str, entity_label: str) -> bool:
        """Check if an entity is likely to be an extraction error"""
        import re
        
        # For DATE/TIME entities, special handling
        if entity_label in ["DATE", "TIME"]:
            # Check for invalid day numbers > 31 in month contexts
            if re.search(r'\b[3-9]\d\s+(January|February|March|April|May|June|July|August|September|October|November|December)\b', entity_text):
                return True
            # Check for invalid hour numbers > 24 without AM/PM
            if re.search(r'\b[2-9]\d:\d{2}\b', entity_text) and not re.search(r'\b(AM|PM|am|pm)\b', entity_text):
                return True
        
        # Entity-type specific validation
        if entity_label == "PERSON":
            return not self._is_valid_person(entity_text)
        elif entity_label == "ORG":
            return not self._is_valid_organization(entity_text)
        elif entity_label in ["DATE", "TIME"]:
            return not self._is_valid_date_time(entity_text)
        elif entity_label == "GPE":
            return not self._is_valid_location(entity_text)
        
        return False
    
    def _is_valid_person(self, entity_text: str) -> bool:
        """Validate if an entity is likely a real person name"""
        # Should contain at least one alphabetic character
        if not any(c.isalpha() for c in entity_text):
            return False
        
        # Should not be mostly numbers
        if sum(c.isdigit() for c in entity_text) > sum(c.isalpha() for c in entity_text):
            return False
        
        # Common person name patterns
        words = entity_text.split()
        if len(words) > 0:
            # First word should start with capital letter
            if not words[0][0].isupper():
                return False
        
        return True
    
    def _is_valid_organization(self, entity_text: str) -> bool:
        """Validate if an entity is likely a real organization"""
        # Should contain at least one alphabetic character
        if not any(c.isalpha() for c in entity_text):
            return False
        
        return True
    
    def _is_valid_date_time(self, entity_text: str) -> bool:
        """Validate if an entity is likely a real date or time"""
        import re
        
        # Common date/time patterns
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',  # MM/DD/YYYY
            r'\d{1,2}-\d{1,2}-\d{2,4}',  # MM-DD-YYYY
            r'\d{4}-\d{1,2}-\d{1,2}',    # YYYY-MM-DD
            r'\b\d{1,2}:\d{2}\s*(AM|PM|am|pm)?\b',  # Time format
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4}\b',
            r'\b(today|tomorrow|yesterday|tonight|morning|afternoon|evening|night)\b',
            r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, entity_text, re.IGNORECASE):
                return True
        
        return False
    
    def _is_valid_location(self, entity_text: str) -> bool:
        """Validate if an entity is likely a real location"""
        # Should contain at least one alphabetic character
        if not any(c.isalpha() for c in entity_text):
            return False
        
        # Should not be a single character
        if len(entity_text) == 1:
            return False
        
        return True


# Global instance for backward compatibility
_default_ner = None

def get_default_ner() -> BasicNER:
    """Get the default BasicNER instance"""
    global _default_ner
    if _default_ner is None:
        _default_ner = BasicNER()
    return _default_ner


# Legacy function for backward compatibility
def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract and categorize named entities from text using spaCy
    
    This is a legacy function maintained for backward compatibility.
    For new code, use BasicNER class directly.
    
    Args:
        text: Input text to process
        
    Returns:
        Dictionary with entity types as keys and lists of unique entities as values
    """
    ner = get_default_ner()
    return ner.extract_entities(text)


# Additional legacy functions that might be used elsewhere
def extract_entities_with_context(text: str, context_window: int = 50) -> Dict[str, List[Dict]]:
    """Extract entities with surrounding context"""
    ner = get_default_ner()
    entities = ner.extract_entities(text)
    
    # Convert to format with context (simplified version)
    result = {}
    for entity_type, entity_list in entities.items():
        result[entity_type] = []
        for entity in entity_list:
            # Find entity in text and extract context
            idx = text.find(entity)
            if idx != -1:
                start = max(0, idx - context_window)
                end = min(len(text), idx + len(entity) + context_window)
                context = text[start:end]
                result[entity_type].append({
                    'entity': entity,
                    'context': context,
                    'start': idx,
                    'end': idx + len(entity)
                })
    
    return result