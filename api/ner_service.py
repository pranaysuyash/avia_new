"""
Named Entity Recognition Service
Extracts entities from transcribed text
"""

import re
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract named entities from text
    This is a simplified version using regex patterns
    In production, use spaCy, Hugging Face, or similar NLP libraries
    """
    entities = {
        "PERSON": [],
        "ORG": [],
        "LOC": [],
        "DATE": [],
        "TIME": [],
        "EMAIL": [],
        "URL": [],
        "PHONE": [],
        "MONEY": []
    }
    
    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    entities["EMAIL"] = list(set(re.findall(email_pattern, text)))
    
    # URL pattern
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    entities["URL"] = list(set(re.findall(url_pattern, text)))
    
    # Phone pattern (US format)
    phone_patterns = [
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',
        r'\b\d{3}\s\d{3}\s\d{4}\b'
    ]
    phones = []
    for pattern in phone_patterns:
        phones.extend(re.findall(pattern, text))
    entities["PHONE"] = list(set(phones))
    
    # Date patterns
    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',
        r'\b\d{1,2} (?:January|February|March|April|May|June|July|August|September|October|November|December) \d{4}\b'
    ]
    dates = []
    for pattern in date_patterns:
        dates.extend(re.findall(pattern, text, re.IGNORECASE))
    entities["DATE"] = list(set(dates))
    
    # Time patterns
    time_patterns = [
        r'\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\b',
        r'\b\d{1,2}\s*(?:AM|PM|am|pm)\b'
    ]
    times = []
    for pattern in time_patterns:
        times.extend(re.findall(pattern, text))
    entities["TIME"] = list(set(times))
    
    # Money patterns
    money_patterns = [
        r'\$\d+(?:,\d{3})*(?:\.\d{2})?',
        r'\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|USD|usd)\b'
    ]
    money = []
    for pattern in money_patterns:
        money.extend(re.findall(pattern, text, re.IGNORECASE))
    entities["MONEY"] = list(set(money))
    
    # Simple organization detection (companies ending with Inc, LLC, etc.)
    org_pattern = r'\b[A-Z][A-Za-z\s&]+(?:Inc|LLC|Ltd|Corp|Corporation|Company|Co)\b'
    entities["ORG"] = list(set(re.findall(org_pattern, text)))
    
    # Common person name patterns (very basic)
    # This would need a proper NLP library for accuracy
    name_pattern = r'\b(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
    entities["PERSON"] = list(set(re.findall(name_pattern, text)))
    
    # Location patterns (basic - cities with state abbreviations)
    location_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2}\b'
    entities["LOC"] = list(set(re.findall(location_pattern, text)))
    
    # Remove empty lists
    entities = {k: v for k, v in entities.items() if v}
    
    logger.info(f"Extracted {sum(len(v) for v in entities.values())} entities from text")
    
    return entities

def extract_entities_advanced(text: str, use_spacy: bool = True) -> Dict[str, List[str]]:
    """
    Advanced entity extraction using spaCy
    This requires spacy and a language model to be installed:
    pip install spacy
    python -m spacy download en_core_web_sm
    """
    try:
        import spacy
        
        # Load spaCy model
        nlp = spacy.load("en_core_web_sm")
        
        # Process text
        doc = nlp(text)
        
        # Extract entities
        entities = {}
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            entities[ent.label_].append(ent.text)
        
        # Remove duplicates
        for label in entities:
            entities[label] = list(set(entities[label]))
        
        # Also extract patterns not caught by spaCy
        basic_entities = extract_entities(text)
        
        # Merge results
        for entity_type, values in basic_entities.items():
            if entity_type not in entities:
                entities[entity_type] = values
            else:
                entities[entity_type].extend(values)
                entities[entity_type] = list(set(entities[entity_type]))
        
        return entities
        
    except ImportError:
        logger.warning("spaCy not available, falling back to basic entity extraction")
        return extract_entities(text)
    except Exception as e:
        logger.error(f"Error in advanced entity extraction: {e}")
        return extract_entities(text)

def summarize_entities(entities: Dict[str, List[str]]) -> str:
    """Generate a summary of extracted entities"""
    if not entities:
        return "No entities found"
    
    summary_parts = []
    for entity_type, values in entities.items():
        if values:
            summary_parts.append(f"{entity_type}: {len(values)} found")
    
    return ", ".join(summary_parts)

# Export functions
__all__ = [
    "extract_entities",
    "extract_entities_advanced",
    "summarize_entities"
]