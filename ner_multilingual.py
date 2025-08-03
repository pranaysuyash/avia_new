"""
Multi-language Named Entity Recognition Module
Extends basic NER with support for 50+ languages
"""

import logging
import spacy
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict

from errors import NERError, handle_error, ErrorCode
from language_support import (
    language_detector, multilingual_extractor, 
    get_language_name, SUPPORTED_LANGUAGES
)

logger = logging.getLogger(__name__)


class MultilingualNER:
    """Named Entity Recognition with multi-language support"""
    
    def __init__(self):
        self.loaded_models = {}
        self.fallback_to_english = True
        
    def extract_entities(self, text: str, language: Optional[str] = None, 
                        detect_code_switching: bool = True) -> Dict[str, any]:
        """
        Extract entities from text with automatic language detection
        
        Args:
            text: Text to analyze
            language: Language code (optional, will auto-detect if not provided)
            detect_code_switching: Whether to detect and handle code-switching
            
        Returns:
            Dictionary containing entities and language information
        """
        try:
            # Detect language if not provided
            if not language:
                detection_result = language_detector.detect_language(text)
                language = detection_result.primary_language
                logger.info(f"Detected language: {language} (confidence: {detection_result.confidence:.2f})")
            
            # Check if we should handle code-switching
            if detect_code_switching and not language:
                detection_result = language_detector.detect_language(text)
                if detection_result.has_code_switching:
                    logger.info("Code-switching detected, processing multilingual text")
                    return self._extract_entities_multilingual(text, detection_result)
            
            # Single language extraction
            return self._extract_entities_single_language(text, language)
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            error_msg = handle_error(e, {'text_length': len(text), 'language': language})
            raise NERError(
                message=str(error_msg),
                error_code=ErrorCode.NER_EXTRACTION_ERROR,
                user_message="Failed to extract entities from text.",
                ner_type="multilingual",
                suggestions=[
                    "Try specifying the language explicitly",
                    "Use basic English-only mode",
                    "Check if the text is in a supported language"
                ]
            )
    
    def _extract_entities_single_language(self, text: str, language: str) -> Dict[str, any]:
        """Extract entities for a single language"""
        # Get language info
        lang_info = SUPPORTED_LANGUAGES.get(language)
        if not lang_info:
            logger.warning(f"Unsupported language: {language}, falling back to English")
            language = 'en'
            lang_info = SUPPORTED_LANGUAGES['en']
        
        # Check if spaCy model is available
        model_name = lang_info.get('spacy_model')
        if not model_name:
            logger.warning(f"No spaCy model for {language}, using language-agnostic extraction")
            return self._extract_entities_basic(text, language)
        
        # Load model
        nlp = self._load_model(language, model_name)
        if not nlp and self.fallback_to_english:
            logger.warning(f"Failed to load model for {language}, falling back to English")
            nlp = self._load_model('en', 'en_core_web_sm')
            language = 'en'
        
        if not nlp:
            return {
                'entities': {},
                'language': language,
                'language_name': get_language_name(language),
                'error': 'No NLP model available'
            }
        
        # Process text
        doc = nlp(text)
        
        # Extract and categorize entities
        entities_by_label = defaultdict(set)
        all_entities = []
        
        for ent in doc.ents:
            # Normalize entity label
            label = self._normalize_label(ent.label_)
            entities_by_label[label].add(ent.text)
            
            all_entities.append({
                'text': ent.text,
                'label': label,
                'start': ent.start_char,
                'end': ent.end_char,
                'original_label': ent.label_
            })
        
        # Convert sets to lists
        entities_dict = {label: list(entities) for label, entities in entities_by_label.items()}
        
        return {
            'entities': entities_dict,
            'all_entities': all_entities,
            'language': language,
            'language_name': get_language_name(language),
            'is_rtl': lang_info.get('rtl', False),
            'model_used': model_name
        }
    
    def _extract_entities_multilingual(self, text: str, detection_result) -> Dict[str, any]:
        """Extract entities from text containing multiple languages"""
        all_entities = defaultdict(set)
        all_entities_list = []
        language_stats = defaultdict(int)
        
        # Process each segment
        for segment in detection_result.segments:
            segment_result = self._extract_entities_single_language(
                segment['text'], 
                segment['language']
            )
            
            # Merge entities
            for label, entities in segment_result.get('entities', {}).items():
                all_entities[label].update(entities)
            
            # Adjust positions and add to list
            for entity in segment_result.get('all_entities', []):
                entity['start'] += segment['start_pos']
                entity['end'] += segment['start_pos']
                entity['language'] = segment['language']
                all_entities_list.append(entity)
            
            language_stats[segment['language']] += len(segment['text'])
        
        # Convert sets to lists
        entities_dict = {label: list(entities) for label, entities in all_entities.items()}
        
        # Calculate language distribution
        total_length = sum(language_stats.values())
        language_distribution = {
            lang: count / total_length for lang, count in language_stats.items()
        }
        
        return {
            'entities': entities_dict,
            'all_entities': all_entities_list,
            'languages': detection_result.all_languages,
            'primary_language': detection_result.primary_language,
            'language_distribution': language_distribution,
            'has_code_switching': True,
            'segments': detection_result.segments
        }
    
    def _extract_entities_basic(self, text: str, language: str) -> Dict[str, any]:
        """Basic entity extraction without spaCy model"""
        # This is a fallback for languages without spaCy support
        # Uses regex patterns for common entity types
        import re
        
        entities_by_label = defaultdict(set)
        all_entities = []
        
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, text):
            entities_by_label['EMAIL'].add(match.group())
            all_entities.append({
                'text': match.group(),
                'label': 'EMAIL',
                'start': match.start(),
                'end': match.end()
            })
        
        # URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        for match in re.finditer(url_pattern, text):
            entities_by_label['URL'].add(match.group())
            all_entities.append({
                'text': match.group(),
                'label': 'URL',
                'start': match.start(),
                'end': match.end()
            })
        
        # Phone numbers
        phone_pattern = r'[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{4,6}'
        for match in re.finditer(phone_pattern, text):
            entities_by_label['PHONE'].add(match.group())
            all_entities.append({
                'text': match.group(),
                'label': 'PHONE',
                'start': match.start(),
                'end': match.end()
            })
        
        # Numbers and money (basic)
        number_pattern = r'\b\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:dollars?|euros?|pounds?|USD|EUR|GBP))?\b'
        for match in re.finditer(number_pattern, text):
            if any(currency in match.group().lower() for currency in ['dollar', 'euro', 'pound', 'usd', 'eur', 'gbp']):
                label = 'MONEY'
            else:
                label = 'NUMBER'
            entities_by_label[label].add(match.group())
            all_entities.append({
                'text': match.group(),
                'label': label,
                'start': match.start(),
                'end': match.end()
            })
        
        # Convert sets to lists
        entities_dict = {label: list(entities) for label, entities in entities_by_label.items()}
        
        return {
            'entities': entities_dict,
            'all_entities': all_entities,
            'language': language,
            'language_name': get_language_name(language),
            'model_used': 'regex_fallback'
        }
    
    def _load_model(self, language: str, model_name: str):
        """Load spaCy model for specific language"""
        if model_name in self.loaded_models:
            return self.loaded_models[model_name]
        
        try:
            nlp = spacy.load(model_name)
            self.loaded_models[model_name] = nlp
            logger.info(f"Loaded spaCy model: {model_name}")
            return nlp
        except OSError:
            logger.warning(f"spaCy model {model_name} not installed")
            return None
        except Exception as e:
            logger.error(f"Failed to load spaCy model {model_name}: {e}")
            return None
    
    def _normalize_label(self, label: str) -> str:
        """Normalize entity labels across different language models"""
        # Common label mappings
        label_map = {
            'PER': 'PERSON',
            'PERS': 'PERSON',
            'LOC': 'GPE',
            'LOCATION': 'GPE',
            'PLACE': 'GPE',
            'ORG': 'ORGANIZATION',
            'CORP': 'ORGANIZATION',
            'COMPANY': 'ORGANIZATION',
            'MISC': 'OTHER',
            'EVT': 'EVENT',
            'PROD': 'PRODUCT',
            'TIME': 'TIME',
            'DATE': 'DATE',
            'MONEY': 'MONEY',
            'PERCENT': 'PERCENT',
            'QUANTITY': 'QUANTITY'
        }
        
        return label_map.get(label.upper(), label.upper())
    
    def get_supported_languages(self) -> List[Dict[str, any]]:
        """Get list of supported languages with their capabilities"""
        languages = []
        for code, info in SUPPORTED_LANGUAGES.items():
            languages.append({
                'code': code,
                'name': info['name'],
                'has_ner': info['spacy_model'] is not None,
                'is_rtl': info['rtl'],
                'spacy_model': info['spacy_model']
            })
        return sorted(languages, key=lambda x: x['name'])


# Global instance
multilingual_ner = MultilingualNER()


def extract_entities_multilingual(text: str, language: Optional[str] = None,
                                 detect_code_switching: bool = True) -> Dict[str, any]:
    """
    Extract entities from text with multi-language support
    
    Args:
        text: Text to analyze
        language: Language code (optional, will auto-detect if not provided)
        detect_code_switching: Whether to detect and handle code-switching
        
    Returns:
        Dictionary containing entities and language information
    """
    return multilingual_ner.extract_entities(text, language, detect_code_switching)