#!/usr/bin/env python3
"""
Word Cloud Generation for Audio/Video Transcription App
Creates visual word clouds from transcript text and extracted entities
"""

import logging
from typing import Dict, List, Optional
from collections import Counter
import re

logger = logging.getLogger(__name__)

def generate_word_frequency(text: str, min_word_length: int = 3, max_words: int = 50) -> Dict[str, int]:
    """
    Generate word frequency data for word cloud
    
    Args:
        text: Input text to analyze
        min_word_length: Minimum word length to include
        max_words: Maximum number of words to return
        
    Returns:
        Dictionary of word frequencies
    """
    if not text or not text.strip():
        return {}
    
    try:
        # Clean and normalize text
        text = text.lower()
        # Remove punctuation and special characters
        text = re.sub(r'[^\w\s]', ' ', text)
        # Split into words
        words = text.split()
        
        # Filter words
        filtered_words = []
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'between', 'among', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
            'my', 'your', 'his', 'her', 'its', 'our', 'their', 'am', 'so', 'also', 'just',
            'now', 'then', 'here', 'there', 'when', 'where', 'why', 'how', 'what', 'which',
            'who', 'whom', 'whose', 'if', 'unless', 'until', 'while', 'since', 'because',
            'although', 'though', 'however', 'therefore', 'thus', 'hence', 'moreover',
            'furthermore', 'nevertheless', 'nonetheless', 'meanwhile', 'otherwise'
        }
        
        for word in words:
            word = word.strip()
            if (len(word) >= min_word_length and 
                word not in stop_words and 
                word.isalpha()):  # Only alphabetic words
                filtered_words.append(word)
        
        # Count word frequencies
        word_counts = Counter(filtered_words)
        
        # Return top words
        top_words = dict(word_counts.most_common(max_words))
        
        logger.info(f"Generated word frequency data for {len(top_words)} words")
        return top_words
        
    except Exception as e:
        logger.error(f"Failed to generate word frequency: {e}")
        return {}

def generate_entity_frequency(entities: Dict[str, List[str]]) -> Dict[str, int]:
    """
    Generate frequency data from extracted entities
    
    Args:
        entities: Dictionary of entity types and their values
        
    Returns:
        Dictionary of entity frequencies
    """
    if not entities:
        return {}
    
    try:
        entity_freq = {}
        
        for entity_type, entity_list in entities.items():
            if entity_list:
                for entity in entity_list:
                    # Clean entity name
                    entity = entity.strip()
                    if entity and len(entity) > 1:
                        # Weight entities by type importance
                        weight = _get_entity_weight(entity_type)
                        entity_freq[entity] = entity_freq.get(entity, 0) + weight
        
        logger.info(f"Generated entity frequency data for {len(entity_freq)} entities")
        return entity_freq
        
    except Exception as e:
        logger.error(f"Failed to generate entity frequency: {e}")
        return {}

def _get_entity_weight(entity_type: str) -> int:
    """Get weight for different entity types"""
    weights = {
        'PERSON': 3,
        'ORG': 3,
        'GPE': 2,
        'PRODUCT': 2,
        'TECHNOLOGY': 2,
        'EVENT': 2,
        'DATE': 1,
        'MONEY': 1,
        'TOPIC': 2,
        'EMOTION': 1
    }
    return weights.get(entity_type, 1)

def create_word_cloud_data(text: str, entities: Dict[str, List[str]] = None) -> Dict[str, int]:
    """
    Create combined word cloud data from text and entities
    
    Args:
        text: Input transcript text
        entities: Extracted entities dictionary
        
    Returns:
        Combined frequency data for word cloud
    """
    try:
        # Get word frequencies from text
        word_freq = generate_word_frequency(text, max_words=30)
        
        # Get entity frequencies
        if entities:
            entity_freq = generate_entity_frequency(entities)
            
            # Combine frequencies, giving entities higher weight
            for entity, freq in entity_freq.items():
                # Boost entity frequency to make them more prominent
                word_freq[entity] = word_freq.get(entity, 0) + freq * 2
        
        # Sort by frequency and return top items
        sorted_items = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        logger.info(f"Created word cloud data with {len(sorted_items)} items")
        return dict(sorted_items[:40])  # Top 40 items for word cloud
        
    except Exception as e:
        logger.error(f"Failed to create word cloud data: {e}")
        return {}

def format_word_cloud_for_display(word_freq: Dict[str, int]) -> str:
    """
    Format word cloud data for text-based display
    
    Args:
        word_freq: Word frequency dictionary
        
    Returns:
        Formatted string for display
    """
    if not word_freq:
        return "No word cloud data available"
    
    try:
        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        # Create text representation with different sizes
        lines = []
        for i, (word, freq) in enumerate(sorted_words[:20]):  # Top 20 words
            if i < 3:  # Top 3 - largest
                lines.append(f"**{word.upper()}** ({freq})")
            elif i < 8:  # Next 5 - medium
                lines.append(f"**{word.title()}** ({freq})")
            else:  # Rest - normal
                lines.append(f"{word} ({freq})")
        
        return " • ".join(lines)
        
    except Exception as e:
        logger.error(f"Failed to format word cloud: {e}")
        return "Error formatting word cloud data"