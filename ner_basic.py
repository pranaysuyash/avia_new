# Basic Named Entity Recognition Module
# Handles entity extraction using spaCy's pre-trained models

import logging
import spacy
from typing import Dict, List, Set
from collections import defaultdict

from errors import NERError, handle_error, ErrorCode

logger = logging.getLogger(__name__)

# Global variable to store the loaded model
_nlp_model = None

def _load_model():
    """Load the spaCy English model with error handling"""
    global _nlp_model
    if _nlp_model is None:
        try:
            _nlp_model = spacy.load("en_core_web_sm")
            logger.info("Successfully loaded spaCy en_core_web_sm model")
        except OSError as e:
            logger.error("spaCy en_core_web_sm model not found. Please install it with: python -m spacy download en_core_web_sm")
            raise NERError(
                message=f"spaCy model not found: {e}",
                error_code=ErrorCode.NER_MODEL_ERROR,
                user_message="The language processing model is not installed.",
                ner_type="spacy",
                suggestions=[
                    "Install the spaCy English model: python -m spacy download en_core_web_sm",
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
    return _nlp_model

def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract and categorize named entities from text using spaCy with improved filtering
    
    Args:
        text: Input text to process
        
    Returns:
        Dictionary with entity types as keys and lists of unique entities as values
    """
    if not text or not text.strip():
        return {}
    
    try:
        nlp = _load_model()
        
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
        
        doc = nlp(text)
        
        # Dictionary to store categorized entities
        entities = defaultdict(set)
        
        # Extract entities and categorize them with improved filtering
        for ent in doc.ents:
            entity_text = ent.text.strip()
            entity_label = ent.label_
            
            # Skip empty entities or very short ones
            if not entity_text or len(entity_text) < 2:
                continue
            
            # Skip entities that are mostly numbers or punctuation (likely errors)
            if _is_likely_error(entity_text, entity_label):
                continue
                
            # Map spaCy labels to our target categories with better validation
            if entity_label == "PERSON" and _is_valid_person(entity_text):
                entities["PERSON"].add(entity_text)
            elif entity_label == "ORG" and _is_valid_organization(entity_text):
                entities["ORG"].add(entity_text)
            elif entity_label in ["DATE", "TIME"] and _is_valid_date_time(entity_text):
                entities["DATE"].add(entity_text)
            elif entity_label == "GPE" and _is_valid_location(entity_text):  # Geopolitical entity
                entities["GPE"].add(entity_text)
        
        # Convert sets to sorted lists for consistent output
        result = {}
        for entity_type, entity_set in entities.items():
            if entity_set:  # Only include non-empty categories
                result[entity_type] = sorted(list(entity_set))
            
        logger.info(f"Extracted {sum(len(v) for v in result.values())} entities from text")
        return result
        
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

def _is_likely_error(entity_text: str, entity_label: str) -> bool:
    """Check if an entity is likely to be an extraction error"""
    # Skip entities that are mostly digits (like "35 July" or "748 AM")
    if entity_label in ["DATE", "TIME"]:
        # Check for malformed dates/times
        if any(char.isdigit() for char in entity_text) and len([c for c in entity_text if c.isdigit()]) > len([c for c in entity_text if c.isalpha()]):
            # More digits than letters - likely an error
            return True
    
    # Skip very short entities that are likely noise
    if len(entity_text.strip()) < 2:
        return True
    
    # Skip entities that are just punctuation or numbers
    if entity_text.replace(' ', '').replace('.', '').replace(',', '').isdigit():
        return True
    
    return False

def _is_valid_person(entity_text: str) -> bool:
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

def _is_valid_organization(entity_text: str) -> bool:
    """Validate if an entity is likely a real organization"""
    # Should contain at least one alphabetic character
    if not any(c.isalpha() for c in entity_text):
        return False
    
    # Should not be just a single common word
    common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    if entity_text.lower() in common_words:
        return False
    
    return True

def _is_valid_date_time(entity_text: str) -> bool:
    """Validate if an entity is likely a real date or time"""
    import re
    
    # Common date/time patterns
    date_patterns = [
        r'\d{1,2}/\d{1,2}/\d{2,4}',  # MM/DD/YYYY
        r'\d{1,2}-\d{1,2}-\d{2,4}',  # MM-DD-YYYY
        r'\d{4}-\d{1,2}-\d{1,2}',    # YYYY-MM-DD
        r'\b\d{1,2}:\d{2}\s*(AM|PM|am|pm)?\b',  # Time format
        r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4}\b',  # Month DD, YYYY
        r'\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b',  # DD Month YYYY
        r'\b(today|tomorrow|yesterday|tonight|morning|afternoon|evening|night)\b',  # Relative time
        r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',  # Days of week
    ]
    
    # Check if it matches any valid date/time pattern
    for pattern in date_patterns:
        if re.search(pattern, entity_text, re.IGNORECASE):
            return True
    
    # Reject obviously wrong patterns like "35 July" or "748 AM"
    if re.search(r'\b\d{2,}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\b', entity_text):
        # Check if day is valid (1-31)
        day_match = re.search(r'\b(\d{2,})\s+', entity_text)
        if day_match:
            day = int(day_match.group(1))
            if day > 31:
                return False
    
    # Reject malformed times like "748 AM"
    if re.search(r'\b\d{3,}\s*(AM|PM|am|pm)\b', entity_text):
        return False
    
    return False  # If no valid pattern found, likely an error

def _is_valid_location(entity_text: str) -> bool:
    """Validate if an entity is likely a real location"""
    # Should contain at least one alphabetic character
    if not any(c.isalpha() for c in entity_text):
        return False
    
    # Should not be mostly numbers
    if sum(c.isdigit() for c in entity_text) > sum(c.isalpha() for c in entity_text):
        return False
    
    # Should start with capital letter
    if not entity_text[0].isupper():
        return False
    
    return True

def get_entity_confidence(text: str) -> Dict[str, Dict[str, float]]:
    """
    Return confidence scores for extracted entities
    
    Args:
        text: Input text to process
        
    Returns:
        Nested dictionary with entity types and their confidence scores
    """
    if not text or not text.strip():
        return {}
    
    try:
        nlp = _load_model()
        doc = nlp(text)
        
        # Dictionary to store entity confidence scores
        confidence_scores = defaultdict(dict)
        
        for ent in doc.ents:
            entity_text = ent.text.strip()
            entity_label = ent.label_
            
            if not entity_text:
                continue
                
            # spaCy doesn't provide direct confidence scores, but we can use
            # the entity's probability from the model's predictions
            # For now, we'll use a simple heuristic based on entity length and context
            confidence = min(0.95, max(0.6, len(entity_text) / 20.0))
            
            # Map to our target categories
            if entity_label == "PERSON":
                confidence_scores["PERSON"][entity_text] = confidence
            elif entity_label == "ORG":
                confidence_scores["ORG"][entity_text] = confidence
            elif entity_label in ["DATE", "TIME"]:
                confidence_scores["DATE"][entity_text] = confidence
            elif entity_label == "GPE":
                confidence_scores["GPE"][entity_text] = confidence
            elif entity_label == "TIME":
                confidence_scores["TIME"][entity_text] = confidence
        
        return dict(confidence_scores)
        
    except Exception as e:
        logger.error(f"Error getting entity confidence: {str(e)}")
        return {}

def filter_entities_by_type(entities: Dict, entity_types: List[str]) -> Dict:
    """
    Filter entities by specified types
    
    Args:
        entities: Dictionary of entities from extract_entities()
        entity_types: List of entity types to keep
        
    Returns:
        Filtered dictionary containing only specified entity types
    """
    if not entities or not entity_types:
        return {}
    
    filtered = {}
    for entity_type in entity_types:
        if entity_type in entities:
            filtered[entity_type] = entities[entity_type]
    
    return filtered