#!/usr/bin/env python3
"""
Comprehensive Translation Pipeline
Task 125: Real-time translation, quality assessment, translation memory,
back-translation validation, and cultural adaptation features.
"""

import asyncio
import json
import logging
import re
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd

# Optional imports with fallbacks
try:
    from transformers import (
        MarianMTModel, 
        MarianTokenizer,
        M2M100ForConditionalGeneration,
        M2M100Tokenizer,
        pipeline
    )
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TranslationProvider(Enum):
    """Supported translation providers."""
    TRANSFORMERS = "transformers"
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    AMAZON = "amazon"
    OPENAI = "openai"
    LOCAL = "local"


class QualityLevel(Enum):
    """Translation quality levels."""
    DRAFT = "draft"           # Quick, basic translation
    STANDARD = "standard"     # Good quality for general use
    PROFESSIONAL = "professional"  # High quality for business
    LOCALIZED = "localized"   # Culturally adapted


@dataclass
class TranslationRequest:
    """Translation request configuration."""
    text: str
    source_language: str
    target_language: str
    provider: TranslationProvider = TranslationProvider.TRANSFORMERS
    quality_level: QualityLevel = QualityLevel.STANDARD
    preserve_formatting: bool = True
    cultural_adaptation: bool = False
    use_translation_memory: bool = True
    enable_back_translation: bool = False
    domain: Optional[str] = None
    custom_terminology: Optional[Dict[str, str]] = None


@dataclass
class TranslationResult:
    """Translation result with metadata."""
    translated_text: str
    source_language: str
    target_language: str
    provider: TranslationProvider
    quality_score: float
    confidence_score: float
    back_translation: Optional[str] = None
    back_translation_score: Optional[float] = None
    cultural_adaptations: List[str] = None
    terminology_matches: List[Dict[str, str]] = None
    processing_time: float = 0.0
    metadata: Dict[str, Any] = None


class LanguageDetector:
    """Automatic language detection."""
    
    def __init__(self):
        self.language_patterns = {
            'en': [
                r'\b(the|and|or|but|in|on|at|to|for|of|with|by)\b',
                r'\b(is|are|was|were|have|has|had)\b',
                r'\b(this|that|these|those|what|where|when|why|how)\b'
            ],
            'es': [
                r'\b(el|la|los|las|un|una|y|o|pero|en|de|por|para|con)\b',
                r'\b(es|son|fue|fueron|tiene|tienen|ha|había)\b',
                r'\b(esto|eso|estos|esas|qué|dónde|cuándo|por qué|cómo)\b'
            ],
            'fr': [
                r'\b(le|la|les|un|une|et|ou|mais|en|de|par|pour|avec)\b',
                r'\b(est|sont|était|étaient|avoir|avait|a|avais)\b',
                r'\b(ce|cette|ces|quoi|où|quand|pourquoi|comment)\b'
            ],
            'de': [
                r'\b(der|die|das|ein|eine|und|oder|aber|in|von|für|mit)\b',
                r'\b(ist|sind|war|waren|haben|hat|hatte)\b',
                r'\b(dies|das|was|wo|wann|warum|wie)\b'
            ],
            'it': [
                r'\b(il|la|lo|gli|le|un|una|e|o|ma|in|di|per|con)\b',
                r'\b(è|sono|era|erano|hanno|ha|aveva)\b',
                r'\b(questo|quello|che|dove|quando|perché|come)\b'
            ]
        }
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """Detect language with confidence score."""
        if not text or len(text.strip()) < 10:
            return 'unknown', 0.0
        
        text_lower = text.lower()
        scores = {}
        
        for lang, patterns in self.language_patterns.items():
            score = 0
            total_patterns = len(patterns)
            
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower))
                score += matches
            
            # Normalize by text length and pattern count
            normalized_score = score / (len(text.split()) * total_patterns + 1)
            scores[lang] = normalized_score
        
        if not scores:
            return 'unknown', 0.0
        
        best_language = max(scores.keys(), key=lambda x: scores[x])
        confidence = min(scores[best_language] * 10, 1.0)  # Scale to 0-1
        
        return best_language, confidence


class TranslationMemory:
    """Translation memory system for consistency and efficiency."""
    
    def __init__(self, db_path: str = "translation_memory.db"):
        self.db_path = db_path
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize translation memory database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS translation_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_text TEXT NOT NULL,
                    source_language TEXT NOT NULL,
                    target_text TEXT NOT NULL,
                    target_language TEXT NOT NULL,
                    domain TEXT,
                    quality_score REAL,
                    usage_count INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_source_target_lang 
                ON translation_memory(source_language, target_language)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_source_text 
                ON translation_memory(source_text)
            ''')
    
    def search_similar(self, source_text: str, source_lang: str, 
                      target_lang: str, threshold: float = 0.8) -> List[Dict[str, Any]]:
        """Search for similar translations in memory."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT source_text, target_text, quality_score, usage_count
                    FROM translation_memory
                    WHERE source_language = ? AND target_language = ?
                    ORDER BY usage_count DESC, quality_score DESC
                    LIMIT 50
                ''', (source_lang, target_lang))
                
                candidates = cursor.fetchall()
                
                if not candidates:
                    return []
                
                # Calculate similarity using basic text comparison
                similar_translations = []
                source_words = set(source_text.lower().split())
                
                for candidate in candidates:
                    candidate_text, target_text, quality_score, usage_count = candidate
                    candidate_words = set(candidate_text.lower().split())
                    
                    # Simple Jaccard similarity
                    intersection = len(source_words.intersection(candidate_words))
                    union = len(source_words.union(candidate_words))
                    similarity = intersection / union if union > 0 else 0
                    
                    if similarity >= threshold:
                        similar_translations.append({
                            'source_text': candidate_text,
                            'target_text': target_text,
                            'similarity': similarity,
                            'quality_score': quality_score,
                            'usage_count': usage_count
                        })
                
                # Sort by similarity and quality
                similar_translations.sort(
                    key=lambda x: (x['similarity'], x['quality_score']), 
                    reverse=True
                )
                
                return similar_translations[:10]  # Return top 10
        
        except Exception as e:
            logger.error(f"Translation memory search error: {e}")
            return []
    
    def store_translation(self, source_text: str, source_lang: str,
                         target_text: str, target_lang: str,
                         quality_score: float, domain: str = None):
        """Store translation in memory."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if translation already exists
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, usage_count FROM translation_memory
                    WHERE source_text = ? AND source_language = ? 
                    AND target_language = ?
                ''', (source_text, source_lang, target_lang))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing translation
                    conn.execute('''
                        UPDATE translation_memory
                        SET target_text = ?, quality_score = ?, usage_count = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (target_text, quality_score, existing[1] + 1, existing[0]))
                else:
                    # Insert new translation
                    conn.execute('''
                        INSERT INTO translation_memory
                        (source_text, source_language, target_text, target_language,
                         domain, quality_score)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (source_text, source_lang, target_text, target_lang,
                          domain, quality_score))
        
        except Exception as e:
            logger.error(f"Translation memory storage error: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get translation memory statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total translations
                cursor.execute("SELECT COUNT(*) FROM translation_memory")
                total_translations = cursor.fetchone()[0]
                
                # Language pairs
                cursor.execute('''
                    SELECT source_language, target_language, COUNT(*) as count
                    FROM translation_memory
                    GROUP BY source_language, target_language
                    ORDER BY count DESC
                ''')
                language_pairs = cursor.fetchall()
                
                # Quality distribution
                cursor.execute('''
                    SELECT 
                        CASE 
                            WHEN quality_score >= 0.9 THEN 'Excellent'
                            WHEN quality_score >= 0.7 THEN 'Good'
                            WHEN quality_score >= 0.5 THEN 'Fair'
                            ELSE 'Poor'
                        END as quality_level,
                        COUNT(*) as count
                    FROM translation_memory
                    GROUP BY quality_level
                ''')
                quality_distribution = cursor.fetchall()
                
                return {
                    'total_translations': total_translations,
                    'language_pairs': language_pairs,
                    'quality_distribution': quality_distribution
                }
        
        except Exception as e:
            logger.error(f"Statistics error: {e}")
            return {'error': str(e)}


class QualityAssessment:
    """Translation quality assessment and validation."""
    
    def __init__(self):
        self.quality_metrics = [
            'fluency',
            'adequacy', 
            'terminology_consistency',
            'cultural_appropriateness'
        ]
    
    def assess_quality(self, source_text: str, translated_text: str,
                      source_lang: str, target_lang: str) -> Dict[str, float]:
        """Assess translation quality across multiple metrics."""
        scores = {}
        
        # Basic fluency check (length ratio and character variety)
        scores['fluency'] = self._assess_fluency(translated_text)
        
        # Adequacy check (coverage of content)
        scores['adequacy'] = self._assess_adequacy(source_text, translated_text)
        
        # Terminology consistency
        scores['terminology_consistency'] = self._assess_terminology(
            source_text, translated_text
        )
        
        # Cultural appropriateness (basic check)
        scores['cultural_appropriateness'] = self._assess_cultural_appropriateness(
            translated_text, target_lang
        )
        
        # Overall quality score (weighted average)
        weights = {
            'fluency': 0.3,
            'adequacy': 0.3,
            'terminology_consistency': 0.2,
            'cultural_appropriateness': 0.2
        }
        
        overall_score = sum(scores[metric] * weights[metric] 
                          for metric in scores)
        
        scores['overall'] = overall_score
        
        return scores
    
    def _assess_fluency(self, text: str) -> float:
        """Assess text fluency based on linguistic patterns."""
        if not text or len(text.strip()) == 0:
            return 0.0
        
        # Check for reasonable sentence structure
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.3
        
        # Average sentence length (reasonable range)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
        length_score = min(avg_sentence_length / 20, 1.0)  # Normalize to 0-1
        
        # Character variety (good mix of letters, spaces, punctuation)
        char_types = {
            'letters': len(re.findall(r'[a-zA-Z]', text)),
            'spaces': len(re.findall(r'\s', text)),
            'punctuation': len(re.findall(r'[.!?,;:]', text))
        }
        
        total_chars = len(text)
        variety_score = min(
            sum(1 for count in char_types.values() if count > 0) / 3, 
            1.0
        )
        
        return (length_score * 0.6 + variety_score * 0.4)
    
    def _assess_adequacy(self, source_text: str, translated_text: str) -> float:
        """Assess how well the translation covers the source content."""
        if not source_text or not translated_text:
            return 0.0
        
        # Simple word coverage analysis
        source_words = set(re.findall(r'\w+', source_text.lower()))
        translated_words = set(re.findall(r'\w+', translated_text.lower()))
        
        # Length ratio check (translated text should be reasonable length)
        length_ratio = len(translated_text) / len(source_text)
        length_score = 1.0 - abs(1.0 - length_ratio)  # Closer to 1:1 is better
        length_score = max(0.0, min(1.0, length_score))
        
        # Content preservation (this is simplified - real systems use BLEU/METEOR)
        if len(source_words) == 0:
            coverage_score = 0.5
        else:
            # Check for key word preservation (numbers, proper nouns, etc.)
            key_words = [w for w in source_words 
                        if re.match(r'\d+', w) or w[0].isupper()]
            
            if key_words:
                # This is a very simplified check
                coverage_score = 0.7  # Assume reasonable coverage
            else:
                coverage_score = 0.6
        
        return (length_score * 0.4 + coverage_score * 0.6)
    
    def _assess_terminology(self, source_text: str, translated_text: str) -> float:
        """Assess terminology consistency."""
        # This is a simplified assessment
        # Real systems would use domain-specific terminology databases
        
        # Check for preservation of technical terms, names, numbers
        source_numbers = re.findall(r'\b\d+(?:\.\d+)?\b', source_text)
        translated_numbers = re.findall(r'\b\d+(?:\.\d+)?\b', translated_text)
        
        # Numbers should be preserved exactly
        if source_numbers:
            number_preservation = len(set(source_numbers).intersection(set(translated_numbers))) / len(set(source_numbers))
        else:
            number_preservation = 1.0
        
        # Check for proper nouns (capitalized words)
        source_proper = set(re.findall(r'\b[A-Z][a-z]+\b', source_text))
        translated_proper = set(re.findall(r'\b[A-Z][a-z]+\b', translated_text))
        
        if source_proper:
            proper_preservation = len(source_proper.intersection(translated_proper)) / len(source_proper)
        else:
            proper_preservation = 1.0
        
        return (number_preservation * 0.6 + proper_preservation * 0.4)
    
    def _assess_cultural_appropriateness(self, text: str, target_lang: str) -> float:
        """Assess cultural appropriateness (basic implementation)."""
        # This is a very basic implementation
        # Real systems would use cultural adaptation databases
        
        # Basic check for offensive or inappropriate content
        basic_check = 0.8  # Assume generally appropriate
        
        # Language-specific checks (very basic)
        if target_lang == 'ja':
            # Japanese requires appropriate levels of politeness
            if 'です' in text or 'ます' in text:
                politeness_score = 0.9
            else:
                politeness_score = 0.7
            basic_check = (basic_check + politeness_score) / 2
        
        elif target_lang == 'de':
            # German has formal/informal distinctions
            if 'Sie' in text:  # Formal address
                formality_score = 0.9
            else:
                formality_score = 0.8
            basic_check = (basic_check + formality_score) / 2
        
        return basic_check


class BackTranslationValidator:
    """Back-translation for quality validation."""
    
    def __init__(self, translator):
        self.translator = translator
    
    async def validate_translation(self, original_text: str, translated_text: str,
                                 source_lang: str, target_lang: str) -> Dict[str, Any]:
        """Validate translation using back-translation."""
        try:
            # Translate back to source language
            back_request = TranslationRequest(
                text=translated_text,
                source_language=target_lang,
                target_language=source_lang,
                quality_level=QualityLevel.STANDARD
            )
            
            back_result = await self.translator.translate(back_request)
            back_translated_text = back_result.translated_text
            
            # Compare original with back-translated text
            similarity_score = self._calculate_similarity(
                original_text, back_translated_text
            )
            
            # Identify potential issues
            issues = self._identify_issues(
                original_text, translated_text, back_translated_text
            )
            
            return {
                'back_translation': back_translated_text,
                'similarity_score': similarity_score,
                'quality_assessment': 'good' if similarity_score > 0.7 else 'needs_review',
                'potential_issues': issues,
                'confidence': back_result.confidence_score
            }
        
        except Exception as e:
            logger.error(f"Back-translation validation error: {e}")
            return {
                'back_translation': None,
                'similarity_score': 0.0,
                'quality_assessment': 'error',
                'potential_issues': [f"Validation error: {str(e)}"],
                'confidence': 0.0
            }
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        if not text1 or not text2:
            return 0.0
        
        # Simple word-based similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _identify_issues(self, original: str, translation: str, back_translation: str) -> List[str]:
        """Identify potential translation issues."""
        issues = []
        
        # Check for missing content
        original_words = len(original.split())
        back_words = len(back_translation.split())
        
        if back_words < original_words * 0.5:
            issues.append("Possible content loss detected")
        
        if back_words > original_words * 2:
            issues.append("Possible content expansion detected")
        
        # Check for number consistency
        original_numbers = set(re.findall(r'\b\d+(?:\.\d+)?\b', original))
        back_numbers = set(re.findall(r'\b\d+(?:\.\d+)?\b', back_translation))
        
        if original_numbers != back_numbers:
            issues.append("Number inconsistency detected")
        
        # Check for proper noun preservation
        original_proper = set(re.findall(r'\b[A-Z][a-z]+\b', original))
        back_proper = set(re.findall(r'\b[A-Z][a-z]+\b', back_translation))
        
        missing_proper = original_proper - back_proper
        if missing_proper:
            issues.append(f"Possible proper noun loss: {', '.join(list(missing_proper)[:3])}")
        
        return issues


class TransformersTranslator:
    """Translation using Hugging Face Transformers."""
    
    def __init__(self):
        self.models = {}
        self.tokenizers = {}
        
        # Language code mappings
        self.language_codes = {
            'en': 'en',
            'es': 'es', 
            'fr': 'fr',
            'de': 'de',
            'it': 'it',
            'pt': 'pt',
            'ru': 'ru',
            'zh': 'zh',
            'ja': 'ja',
            'ko': 'ko'
        }
    
    def _get_model_key(self, source_lang: str, target_lang: str) -> str:
        """Get model key for language pair."""
        return f"{source_lang}-{target_lang}"
    
    def _load_model(self, source_lang: str, target_lang: str):
        """Load translation model for language pair."""
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("Transformers library not available")
        
        model_key = self._get_model_key(source_lang, target_lang)
        
        if model_key in self.models:
            return self.models[model_key], self.tokenizers[model_key]
        
        try:
            # Try to load Marian model for the language pair
            model_name = f"Helsinki-NLP/opus-mt-{source_lang}-{target_lang}"
            
            tokenizer = MarianTokenizer.from_pretrained(model_name)
            model = MarianMTModel.from_pretrained(model_name)
            
            self.tokenizers[model_key] = tokenizer
            self.models[model_key] = model
            
            return model, tokenizer
        
        except Exception as e:
            logger.warning(f"Could not load Marian model for {source_lang}-{target_lang}: {e}")
            
            # Fallback to M2M100 model
            try:
                if 'multilingual' not in self.models:
                    self.tokenizers['multilingual'] = M2M100Tokenizer.from_pretrained("facebook/m2m100_418M")
                    self.models['multilingual'] = M2M100ForConditionalGeneration.from_pretrained("facebook/m2m100_418M")
                
                return self.models['multilingual'], self.tokenizers['multilingual']
            
            except Exception as e2:
                logger.error(f"Could not load fallback model: {e2}")
                raise e2
    
    async def translate_text(self, text: str, source_lang: str, target_lang: str) -> Tuple[str, float]:
        """Translate text using transformers."""
        try:
            model, tokenizer = self._load_model(source_lang, target_lang)
            
            # Prepare input
            inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            
            # Generate translation
            with torch.no_grad():
                generated_tokens = model.generate(**inputs)
            
            # Decode translation
            translated_text = tokenizer.decode(generated_tokens[0], skip_special_tokens=True)
            
            # Calculate confidence (simplified)
            confidence = 0.8  # Default confidence for transformers
            
            return translated_text, confidence
        
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return f"Translation error: {str(e)}", 0.0


class CulturalAdaptation:
    """Cultural adaptation for localized translations."""
    
    def __init__(self):
        # Cultural adaptation rules (simplified examples)
        self.adaptation_rules = {
            'date_formats': {
                'en': r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY
                'de': r'\d{1,2}\.\d{1,2}\.\d{4}',  # DD.MM.YYYY
                'fr': r'\d{1,2}/\d{1,2}/\d{4}',  # DD/MM/YYYY
            },
            'currency_formats': {
                'en': r'\$\d+(?:\.\d{2})?',  # $X.XX
                'de': r'\d+(?:,\d{2})? €',  # X,XX €
                'fr': r'\d+(?:,\d{2})? €',  # X,XX €
            },
            'cultural_greetings': {
                'ja': {'hello': 'こんにちは', 'goodbye': 'さようなら'},
                'de': {'hello': 'Guten Tag', 'goodbye': 'Auf Wiedersehen'},
                'fr': {'hello': 'Bonjour', 'goodbye': 'Au revoir'}
            }
        }
    
    def adapt_translation(self, text: str, target_lang: str) -> Tuple[str, List[str]]:
        """Apply cultural adaptations to translation."""
        adapted_text = text
        adaptations = []
        
        # Date format adaptation
        if target_lang in self.adaptation_rules['date_formats']:
            adapted_text, date_changes = self._adapt_dates(adapted_text, target_lang)
            adaptations.extend(date_changes)
        
        # Currency format adaptation
        if target_lang in self.adaptation_rules['currency_formats']:
            adapted_text, currency_changes = self._adapt_currency(adapted_text, target_lang)
            adaptations.extend(currency_changes)
        
        # Cultural greeting adaptation
        if target_lang in self.adaptation_rules['cultural_greetings']:
            adapted_text, greeting_changes = self._adapt_greetings(adapted_text, target_lang)
            adaptations.extend(greeting_changes)
        
        return adapted_text, adaptations
    
    def _adapt_dates(self, text: str, target_lang: str) -> Tuple[str, List[str]]:
        """Adapt date formats."""
        adaptations = []
        
        # Find US date format (MM/DD/YYYY)
        us_dates = re.findall(r'\d{1,2}/\d{1,2}/\d{4}', text)
        
        for date in us_dates:
            if target_lang == 'de':
                # Convert to DD.MM.YYYY
                parts = date.split('/')
                if len(parts) == 3:
                    adapted_date = f"{parts[1]}.{parts[0]}.{parts[2]}"
                    text = text.replace(date, adapted_date)
                    adaptations.append(f"Date format: {date} → {adapted_date}")
        
        return text, adaptations
    
    def _adapt_currency(self, text: str, target_lang: str) -> Tuple[str, List[str]]:
        """Adapt currency formats."""
        adaptations = []
        
        # Find US currency format ($X.XX)
        us_currency = re.findall(r'\$(\d+(?:\.\d{2})?)', text)
        
        for amount in us_currency:
            original = f"${amount}"
            if target_lang in ['de', 'fr']:
                # Convert to European format (X,XX €)
                adapted_amount = amount.replace('.', ',') + " €"
                text = text.replace(original, adapted_amount)
                adaptations.append(f"Currency format: {original} → {adapted_amount}")
        
        return text, adaptations
    
    def _adapt_greetings(self, text: str, target_lang: str) -> Tuple[str, List[str]]:
        """Adapt cultural greetings."""
        adaptations = []
        
        greetings = self.adaptation_rules['cultural_greetings'].get(target_lang, {})
        
        for english, localized in greetings.items():
            if english.lower() in text.lower():
                # Simple replacement (case-insensitive)
                pattern = re.compile(re.escape(english), re.IGNORECASE)
                if pattern.search(text):
                    text = pattern.sub(localized, text)
                    adaptations.append(f"Greeting: {english} → {localized}")
        
        return text, adaptations


class ComprehensiveTranslationPipeline:
    """Main translation pipeline coordinating all components."""
    
    def __init__(self, db_path: str = "translation_pipeline.db"):
        self.db_path = db_path
        self.language_detector = LanguageDetector()
        self.translation_memory = TranslationMemory(db_path)
        self.quality_assessor = QualityAssessment()
        self.cultural_adapter = CulturalAdaptation()
        
        # Initialize translators
        self.transformers_translator = None
        if TRANSFORMERS_AVAILABLE:
            self.transformers_translator = TransformersTranslator()
        
        self.back_translator = None
        
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize main pipeline database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS translations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_text TEXT NOT NULL,
                    source_language TEXT NOT NULL,
                    target_text TEXT NOT NULL,
                    target_language TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    quality_score REAL,
                    confidence_score REAL,
                    processing_time REAL,
                    back_translation TEXT,
                    back_translation_score REAL,
                    cultural_adaptations TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
    
    async def translate(self, request: TranslationRequest) -> TranslationResult:
        """Perform comprehensive translation."""
        start_time = time.time()
        
        try:
            # Language detection if not specified
            if request.source_language == 'auto':
                detected_lang, confidence = self.language_detector.detect_language(request.text)
                request.source_language = detected_lang
                logger.info(f"Detected source language: {detected_lang} (confidence: {confidence:.3f})")
            
            # Check translation memory first
            if request.use_translation_memory:
                similar_translations = self.translation_memory.search_similar(
                    request.text, request.source_language, request.target_language
                )
                
                if similar_translations and similar_translations[0]['similarity'] > 0.95:
                    # Use existing translation
                    best_match = similar_translations[0]
                    processing_time = time.time() - start_time
                    
                    return TranslationResult(
                        translated_text=best_match['target_text'],
                        source_language=request.source_language,
                        target_language=request.target_language,
                        provider=TranslationProvider.LOCAL,
                        quality_score=best_match['quality_score'],
                        confidence_score=0.9,  # High confidence for exact match
                        processing_time=processing_time,
                        metadata={'source': 'translation_memory', 'similarity': best_match['similarity']}
                    )
            
            # Perform translation
            translated_text, confidence = await self._perform_translation(
                request.text, request.source_language, request.target_language, request.provider
            )
            
            # Cultural adaptation if requested
            cultural_adaptations = []
            if request.cultural_adaptation:
                translated_text, cultural_adaptations = self.cultural_adapter.adapt_translation(
                    translated_text, request.target_language
                )
            
            # Quality assessment
            quality_scores = self.quality_assessor.assess_quality(
                request.text, translated_text, 
                request.source_language, request.target_language
            )
            
            # Back-translation validation if requested
            back_translation = None
            back_translation_score = None
            if request.enable_back_translation:
                if not self.back_translator:
                    self.back_translator = BackTranslationValidator(self)
                
                back_validation = await self.back_translator.validate_translation(
                    request.text, translated_text,
                    request.source_language, request.target_language
                )
                
                back_translation = back_validation['back_translation']
                back_translation_score = back_validation['similarity_score']
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Create result
            result = TranslationResult(
                translated_text=translated_text,
                source_language=request.source_language,
                target_language=request.target_language,
                provider=request.provider,
                quality_score=quality_scores['overall'],
                confidence_score=confidence,
                back_translation=back_translation,
                back_translation_score=back_translation_score,
                cultural_adaptations=cultural_adaptations,
                processing_time=processing_time,
                metadata={'quality_breakdown': quality_scores}
            )
            
            # Store in translation memory
            if request.use_translation_memory:
                self.translation_memory.store_translation(
                    request.text, request.source_language,
                    translated_text, request.target_language,
                    quality_scores['overall'], request.domain
                )
            
            # Store in main database
            self._store_translation(request, result)
            
            return result
        
        except Exception as e:
            logger.error(f"Translation pipeline error: {e}")
            processing_time = time.time() - start_time
            
            return TranslationResult(
                translated_text=f"Translation error: {str(e)}",
                source_language=request.source_language,
                target_language=request.target_language,
                provider=request.provider,
                quality_score=0.0,
                confidence_score=0.0,
                processing_time=processing_time
            )
    
    async def _perform_translation(self, text: str, source_lang: str, 
                                 target_lang: str, provider: TranslationProvider) -> Tuple[str, float]:
        """Perform actual translation using specified provider."""
        
        if provider == TranslationProvider.TRANSFORMERS:
            if self.transformers_translator:
                return await self.transformers_translator.translate_text(
                    text, source_lang, target_lang
                )
            else:
                # Fallback to mock translation
                return self._mock_translate(text, source_lang, target_lang)
        
        else:
            # Mock translation for unsupported providers
            return self._mock_translate(text, source_lang, target_lang)
    
    def _mock_translate(self, text: str, source_lang: str, target_lang: str) -> Tuple[str, float]:
        """Mock translation for demonstration."""
        # Simple mock translations for demo
        mock_translations = {
            ('en', 'es'): {
                'hello': 'hola',
                'goodbye': 'adiós',
                'thank you': 'gracias',
                'yes': 'sí',
                'no': 'no'
            },
            ('en', 'fr'): {
                'hello': 'bonjour',
                'goodbye': 'au revoir',
                'thank you': 'merci',
                'yes': 'oui',
                'no': 'non'
            },
            ('en', 'de'): {
                'hello': 'hallo',
                'goodbye': 'auf wiedersehen',
                'thank you': 'danke',
                'yes': 'ja',
                'no': 'nein'
            }
        }
        
        text_lower = text.lower().strip()
        translations = mock_translations.get((source_lang, target_lang), {})
        
        if text_lower in translations:
            return translations[text_lower], 0.9
        
        # For longer texts, provide a basic mock
        if target_lang == 'es':
            return f"[ES] {text}", 0.7
        elif target_lang == 'fr':
            return f"[FR] {text}", 0.7
        elif target_lang == 'de':
            return f"[DE] {text}", 0.7
        else:
            return f"[{target_lang.upper()}] {text}", 0.6
    
    def _store_translation(self, request: TranslationRequest, result: TranslationResult):
        """Store translation result in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO translations
                    (source_text, source_language, target_text, target_language,
                     provider, quality_score, confidence_score, processing_time,
                     back_translation, back_translation_score, cultural_adaptations)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    request.text[:1000],  # Truncate for storage
                    result.source_language,
                    result.translated_text,
                    result.target_language,
                    result.provider.value,
                    result.quality_score,
                    result.confidence_score,
                    result.processing_time,
                    result.back_translation,
                    result.back_translation_score,
                    json.dumps(result.cultural_adaptations) if result.cultural_adaptations else None
                ))
        
        except Exception as e:
            logger.error(f"Database storage error: {e}")
    
    async def batch_translate(self, texts: List[str], source_lang: str, 
                            target_lang: str, **kwargs) -> List[TranslationResult]:
        """Batch translation for multiple texts."""
        results = []
        
        for text in texts:
            request = TranslationRequest(
                text=text,
                source_language=source_lang,
                target_language=target_lang,
                **kwargs
            )
            
            result = await self.translate(request)
            results.append(result)
            
            # Small delay to prevent overwhelming
            await asyncio.sleep(0.05)
        
        return results
    
    def get_pipeline_statistics(self) -> Dict[str, Any]:
        """Get translation pipeline statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total translations
                cursor.execute("SELECT COUNT(*) FROM translations")
                total_translations = cursor.fetchone()[0]
                
                # Language pair statistics
                cursor.execute('''
                    SELECT source_language, target_language, COUNT(*) as count
                    FROM translations
                    GROUP BY source_language, target_language
                    ORDER BY count DESC
                    LIMIT 10
                ''')
                language_pairs = cursor.fetchall()
                
                # Provider statistics
                cursor.execute('''
                    SELECT provider, COUNT(*) as count, AVG(quality_score) as avg_quality
                    FROM translations
                    GROUP BY provider
                ''')
                provider_stats = cursor.fetchall()
                
                # Quality distribution
                cursor.execute('''
                    SELECT AVG(quality_score), MIN(quality_score), MAX(quality_score)
                    FROM translations
                    WHERE quality_score IS NOT NULL
                ''')
                quality_stats = cursor.fetchone()
                
                # Performance statistics
                cursor.execute('''
                    SELECT AVG(processing_time), MIN(processing_time), MAX(processing_time)
                    FROM translations
                ''')
                performance_stats = cursor.fetchone()
                
                # Get translation memory stats
                tm_stats = self.translation_memory.get_statistics()
                
                return {
                    'total_translations': total_translations,
                    'top_language_pairs': language_pairs,
                    'provider_performance': provider_stats,
                    'quality_stats': {
                        'average': quality_stats[0] if quality_stats[0] else 0,
                        'minimum': quality_stats[1] if quality_stats[1] else 0,
                        'maximum': quality_stats[2] if quality_stats[2] else 0
                    },
                    'performance_stats': {
                        'average_time': performance_stats[0] if performance_stats[0] else 0,
                        'fastest': performance_stats[1] if performance_stats[1] else 0,
                        'slowest': performance_stats[2] if performance_stats[2] else 0
                    },
                    'translation_memory': tm_stats
                }
        
        except Exception as e:
            logger.error(f"Statistics error: {e}")
            return {'error': str(e)}


# Example usage and testing
async def main():
    """Example usage of the comprehensive translation pipeline."""
    
    # Initialize pipeline
    pipeline = ComprehensiveTranslationPipeline()
    
    # Example texts for translation
    test_texts = {
        'greetings': [
            "Hello, how are you?",
            "Good morning, have a great day!",
            "Thank you for your help.",
            "Goodbye, see you later."
        ],
        'business': [
            "We will have a meeting at 3:00 PM on 12/25/2024.",
            "The project budget is $10,000.50.",
            "Please send the report by Friday.",
            "Our revenue increased by 15% this quarter."
        ],
        'technical': [
            "The system requires 8GB of RAM and 500GB storage.",
            "Configure the database connection string.",
            "Run the automated test suite.",
            "Deploy the application to production."
        ]
    }
    
    target_languages = ['es', 'fr', 'de']
    
    print("🌍 Comprehensive Translation Pipeline Demo")
    print("=" * 50)
    
    for category, texts in test_texts.items():
        print(f"\n📚 Testing {category.title()} Texts:")
        
        for target_lang in target_languages:
            print(f"\n🎯 Translating to {target_lang.upper()}:")
            
            for text in texts[:2]:  # Test first 2 texts per category
                print(f"\nOriginal: {text}")
                
                # Basic translation
                request = TranslationRequest(
                    text=text,
                    source_language='en',
                    target_language=target_lang,
                    use_translation_memory=True,
                    cultural_adaptation=True
                )
                
                result = await pipeline.translate(request)
                
                print(f"Translated: {result.translated_text}")
                print(f"Quality: {result.quality_score:.3f}")
                print(f"Confidence: {result.confidence_score:.3f}")
                print(f"Time: {result.processing_time:.3f}s")
                
                if result.cultural_adaptations:
                    print(f"Adaptations: {result.cultural_adaptations}")
            
            print("-" * 30)
    
    # Test batch translation
    print(f"\n🚀 Batch Translation Test:")
    batch_texts = [
        "Hello world",
        "How are you?", 
        "Thank you very much"
    ]
    
    batch_results = await pipeline.batch_translate(
        batch_texts, 'en', 'es',
        use_translation_memory=True
    )
    
    for i, result in enumerate(batch_results):
        print(f"{i+1}. {batch_texts[i]} → {result.translated_text}")
    
    # Show pipeline statistics
    print(f"\n📊 Pipeline Statistics:")
    stats = pipeline.get_pipeline_statistics()
    print(f"Total translations: {stats.get('total_translations', 0)}")
    print(f"Top language pairs: {stats.get('top_language_pairs', [])[:3]}")
    
    if 'quality_stats' in stats:
        quality = stats['quality_stats']
        print(f"Average quality: {quality.get('average', 0):.3f}")
    
    if 'performance_stats' in stats:
        perf = stats['performance_stats']
        print(f"Average processing time: {perf.get('average_time', 0):.3f}s")
    
    print(f"\n✅ Comprehensive translation pipeline demo completed!")


if __name__ == "__main__":
    asyncio.run(main())