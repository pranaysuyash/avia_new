#!/usr/bin/env python3
"""
Punctuation Restoration and Text Enhancement System
Implements Task 88: Build punctuation restoration and text enhancement

This module provides AI-powered punctuation restoration, capitalization correction,
and text formatting for transcribed content to improve readability and accuracy.
"""

import logging
import re
import string
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import torch
from transformers import (
    AutoTokenizer, AutoModelForTokenClassification,
    pipeline, AutoModelForSequenceClassification
)
from sentence_transformers import SentenceTransformer
import spacy
from textblob import TextBlob
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('stopwords', quiet=True)
except Exception as e:
    logger.warning(f"Failed to download NLTK data: {e}")

@dataclass
class TextEnhancementResult:
    """Result of text enhancement processing"""
    original_text: str
    enhanced_text: str
    confidence_score: float
    changes_made: List[Dict[str, Any]]
    processing_time: float
    metadata: Dict[str, Any]

@dataclass
class PunctuationChange:
    """Represents a punctuation change made to text"""
    position: int
    original: str
    replacement: str
    change_type: str  # 'add', 'replace', 'remove'
    confidence: float
    reason: str

class PunctuationRestorer:
    """AI-powered punctuation restoration system"""
    
    def __init__(self, model_name: str = "oliverguhr/fullstop-punctuation-multilang-large"):
        """Initialize the punctuation restoration system"""
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.punctuation_pipeline = None
        self.sentence_model = None
        
        # Punctuation mapping
        self.punctuation_map = {
            'PERIOD': '.',
            'COMMA': ',',
            'QUESTION': '?',
            'EXCLAMATION': '!',
            'COLON': ':',
            'SEMICOLON': ';',
            'DASH': '—',
            'QUOTE': '"'
        }
        
        # Load models
        self._load_models()
        
        # Load spaCy for additional processing
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Some features may be limited.")
            self.nlp = None
    
    def _load_models(self):
        """Load the punctuation restoration models"""
        try:
            # Load punctuation restoration model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForTokenClassification.from_pretrained(self.model_name)
            
            # Create pipeline
            self.punctuation_pipeline = pipeline(
                "token-classification",
                model=self.model,
                tokenizer=self.tokenizer,
                aggregation_strategy="simple"
            )
            
            # Load sentence transformer for context understanding
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            logger.info(f"Punctuation restoration models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load punctuation models: {e}")
            # Fallback to rule-based approach
            self.punctuation_pipeline = None
    
    def restore_punctuation(self, text: str, confidence_threshold: float = 0.7) -> TextEnhancementResult:
        """Restore punctuation in the given text"""
        start_time = datetime.now()
        changes_made = []
        
        try:
            # Clean and prepare text
            cleaned_text = self._preprocess_text(text)
            
            if self.punctuation_pipeline:
                # Use AI model for punctuation restoration
                enhanced_text, ai_changes = self._restore_with_ai(cleaned_text, confidence_threshold)
                changes_made.extend(ai_changes)
            else:
                # Fallback to rule-based restoration
                enhanced_text, rule_changes = self._restore_with_rules(cleaned_text)
                changes_made.extend(rule_changes)
            
            # Apply additional enhancements
            enhanced_text, additional_changes = self._apply_additional_enhancements(enhanced_text)
            changes_made.extend(additional_changes)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence(text, enhanced_text, changes_made)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return TextEnhancementResult(
                original_text=text,
                enhanced_text=enhanced_text,
                confidence_score=confidence_score,
                changes_made=changes_made,
                processing_time=processing_time,
                metadata={
                    'model_used': self.model_name if self.punctuation_pipeline else 'rule_based',
                    'changes_count': len(changes_made),
                    'enhancement_ratio': len(enhanced_text) / len(text) if text else 1.0
                }
            )
            
        except Exception as e:
            logger.error(f"Punctuation restoration failed: {e}")
            return TextEnhancementResult(
                original_text=text,
                enhanced_text=text,
                confidence_score=0.0,
                changes_made=[],
                processing_time=(datetime.now() - start_time).total_seconds(),
                metadata={'error': str(e)}
            )
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for punctuation restoration"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove existing punctuation for clean restoration
        # Keep some punctuation that's likely correct
        text = re.sub(r'[.]{2,}', ' ', text)  # Remove multiple periods
        text = re.sub(r'[,]{2,}', ',', text)  # Remove multiple commas
        
        return text
    
    def _restore_with_ai(self, text: str, confidence_threshold: float) -> Tuple[str, List[Dict[str, Any]]]:
        """Restore punctuation using AI model"""
        changes_made = []
        
        try:
            # Split text into manageable chunks
            chunks = self._split_into_chunks(text, max_length=512)
            enhanced_chunks = []
            
            for chunk in chunks:
                # Get predictions from the model
                predictions = self.punctuation_pipeline(chunk)
                
                # Apply predictions to text
                enhanced_chunk, chunk_changes = self._apply_predictions(chunk, predictions, confidence_threshold)
                enhanced_chunks.append(enhanced_chunk)
                changes_made.extend(chunk_changes)
            
            enhanced_text = ' '.join(enhanced_chunks)
            return enhanced_text, changes_made
            
        except Exception as e:
            logger.error(f"AI punctuation restoration failed: {e}")
            return text, []
    
    def _split_into_chunks(self, text: str, max_length: int = 512) -> List[str]:
        """Split text into chunks for processing"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            
            if current_length + word_length > max_length and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _apply_predictions(self, text: str, predictions: List[Dict], confidence_threshold: float) -> Tuple[str, List[Dict[str, Any]]]:
        """Apply model predictions to text"""
        changes_made = []
        enhanced_text = text
        
        # Sort predictions by position (reverse order for safe insertion)
        predictions = sorted(predictions, key=lambda x: x['start'], reverse=True)
        
        for pred in predictions:
            if pred['score'] >= confidence_threshold:
                label = pred['entity_group']
                position = pred['end']
                
                # Map label to punctuation
                punctuation = self._map_label_to_punctuation(label)
                
                if punctuation:
                    # Insert punctuation
                    enhanced_text = enhanced_text[:position] + punctuation + enhanced_text[position:]
                    
                    changes_made.append({
                        'position': position,
                        'original': '',
                        'replacement': punctuation,
                        'change_type': 'add',
                        'confidence': pred['score'],
                        'reason': f'AI model prediction ({label})'
                    })
        
        return enhanced_text, changes_made
    
    def _map_label_to_punctuation(self, label: str) -> str:
        """Map model label to punctuation mark"""
        label_map = {
            'PERIOD': '.',
            'COMMA': ',',
            'QUESTION': '?',
            'EXCLAMATION': '!',
            'COLON': ':',
            'SEMICOLON': ';'
        }
        return label_map.get(label, '')
    
    def _restore_with_rules(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Restore punctuation using rule-based approach"""
        changes_made = []
        enhanced_text = text
        
        # Rule 1: Add periods at the end of sentences
        sentences = self._split_into_sentences_heuristic(text)
        enhanced_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and not sentence[-1] in '.!?':
                if self._is_question(sentence):
                    sentence += '?'
                    changes_made.append({
                        'position': len(sentence) - 1,
                        'original': '',
                        'replacement': '?',
                        'change_type': 'add',
                        'confidence': 0.8,
                        'reason': 'Question detection rule'
                    })
                else:
                    sentence += '.'
                    changes_made.append({
                        'position': len(sentence) - 1,
                        'original': '',
                        'replacement': '.',
                        'change_type': 'add',
                        'confidence': 0.9,
                        'reason': 'Sentence ending rule'
                    })
            
            enhanced_sentences.append(sentence)
        
        enhanced_text = ' '.join(enhanced_sentences)
        
        # Rule 2: Add commas in lists and before conjunctions
        enhanced_text, comma_changes = self._add_commas_with_rules(enhanced_text)
        changes_made.extend(comma_changes)
        
        return enhanced_text, changes_made
    
    def _split_into_sentences_heuristic(self, text: str) -> List[str]:
        """Split text into sentences using heuristics"""
        # Simple sentence splitting based on common patterns
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # If no existing punctuation, split on long pauses or conjunctions
        if len(sentences) == 1:
            # Split on common sentence boundaries
            sentences = re.split(r'\s+(?:and then|so|but|however|therefore|meanwhile)\s+', text, flags=re.IGNORECASE)
        
        return [s.strip() for s in sentences if s.strip()]
    
    def _is_question(self, sentence: str) -> bool:
        """Determine if a sentence is a question"""
        question_words = ['what', 'when', 'where', 'who', 'why', 'how', 'which', 'whose', 'whom']
        sentence_lower = sentence.lower().strip()
        
        # Check for question words at the beginning
        for word in question_words:
            if sentence_lower.startswith(word + ' '):
                return True
        
        # Check for auxiliary verbs at the beginning (inverted questions)
        aux_verbs = ['is', 'are', 'was', 'were', 'do', 'does', 'did', 'can', 'could', 'will', 'would', 'should']
        first_word = sentence_lower.split()[0] if sentence_lower.split() else ''
        
        return first_word in aux_verbs
    
    def _add_commas_with_rules(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Add commas using grammatical rules"""
        changes_made = []
        enhanced_text = text
        
        # Rule: Add comma before coordinating conjunctions in compound sentences
        conjunctions = ['and', 'but', 'or', 'nor', 'for', 'so', 'yet']
        
        for conj in conjunctions:
            pattern = r'\s+(' + conj + r')\s+'
            matches = list(re.finditer(pattern, enhanced_text, re.IGNORECASE))
            
            # Process matches in reverse order
            for match in reversed(matches):
                start, end = match.span()
                # Check if this looks like a compound sentence (simple heuristic)
                before = enhanced_text[:start].strip()
                after = enhanced_text[end:].strip()
                
                if len(before.split()) > 3 and len(after.split()) > 3:
                    # Add comma before conjunction
                    enhanced_text = enhanced_text[:start] + ', ' + enhanced_text[start+1:]
                    changes_made.append({
                        'position': start,
                        'original': ' ',
                        'replacement': ', ',
                        'change_type': 'replace',
                        'confidence': 0.7,
                        'reason': f'Comma before conjunction ({conj})'
                    })
        
        return enhanced_text, changes_made
    
    def _apply_additional_enhancements(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Apply additional text enhancements"""
        changes_made = []
        enhanced_text = text
        
        # Capitalization correction
        enhanced_text, cap_changes = self._fix_capitalization(enhanced_text)
        changes_made.extend(cap_changes)
        
        # Fix spacing issues
        enhanced_text, space_changes = self._fix_spacing(enhanced_text)
        changes_made.extend(space_changes)
        
        # Fix common abbreviations
        enhanced_text, abbrev_changes = self._fix_abbreviations(enhanced_text)
        changes_made.extend(abbrev_changes)
        
        return enhanced_text, changes_made
    
    def _fix_capitalization(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Fix capitalization issues"""
        changes_made = []
        
        # Split into sentences
        sentences = re.split(r'([.!?]+)', text)
        enhanced_sentences = []
        
        for i, sentence in enumerate(sentences):
            if sentence.strip() and not re.match(r'^[.!?]+$', sentence):
                # Capitalize first letter of sentence
                sentence = sentence.strip()
                if sentence and sentence[0].islower():
                    sentence = sentence[0].upper() + sentence[1:]
                    changes_made.append({
                        'position': 0,
                        'original': sentence[0].lower(),
                        'replacement': sentence[0].upper(),
                        'change_type': 'replace',
                        'confidence': 0.95,
                        'reason': 'Sentence capitalization'
                    })
                
                # Capitalize proper nouns (simple heuristic)
                words = sentence.split()
                for j, word in enumerate(words):
                    if self._is_proper_noun(word) and word[0].islower():
                        words[j] = word[0].upper() + word[1:]
                        changes_made.append({
                            'position': j,
                            'original': word,
                            'replacement': words[j],
                            'change_type': 'replace',
                            'confidence': 0.8,
                            'reason': 'Proper noun capitalization'
                        })
                
                sentence = ' '.join(words)
            
            enhanced_sentences.append(sentence)
        
        return ''.join(enhanced_sentences), changes_made
    
    def _is_proper_noun(self, word: str) -> bool:
        """Simple heuristic to identify proper nouns"""
        # Common proper noun indicators
        proper_indicators = [
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december',
            'america', 'europe', 'asia', 'africa', 'australia',
            'english', 'spanish', 'french', 'german', 'chinese', 'japanese'
        ]
        
        return word.lower() in proper_indicators
    
    def _fix_spacing(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Fix spacing issues"""
        changes_made = []
        enhanced_text = text
        
        # Fix multiple spaces
        enhanced_text = re.sub(r'\s{2,}', ' ', enhanced_text)
        
        # Fix spacing around punctuation
        enhanced_text = re.sub(r'\s+([,.!?;:])', r'\1', enhanced_text)  # Remove space before punctuation
        enhanced_text = re.sub(r'([.!?;:])\s*([A-Za-z])', r'\1 \2', enhanced_text)  # Add space after punctuation
        
        return enhanced_text, changes_made
    
    def _fix_abbreviations(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Fix common abbreviations"""
        changes_made = []
        enhanced_text = text
        
        # Common abbreviations
        abbreviations = {
            r'\bi\.e\.': 'i.e.',
            r'\be\.g\.': 'e.g.',
            r'\betc\b': 'etc.',
            r'\bvs\b': 'vs.',
            r'\bdr\b': 'Dr.',
            r'\bmr\b': 'Mr.',
            r'\bms\b': 'Ms.',
            r'\bmrs\b': 'Mrs.'
        }
        
        for pattern, replacement in abbreviations.items():
            enhanced_text = re.sub(pattern, replacement, enhanced_text, flags=re.IGNORECASE)
        
        return enhanced_text, changes_made
    
    def _calculate_confidence(self, original: str, enhanced: str, changes: List[Dict]) -> float:
        """Calculate confidence score for the enhancement"""
        if not changes:
            return 1.0 if original == enhanced else 0.0
        
        # Base confidence on individual change confidences
        total_confidence = sum(change.get('confidence', 0.5) for change in changes)
        avg_confidence = total_confidence / len(changes)
        
        # Adjust based on text length and change ratio
        change_ratio = len(changes) / len(original.split()) if original.split() else 0
        
        # Penalize too many changes (might indicate over-correction)
        if change_ratio > 0.3:
            avg_confidence *= 0.8
        
        return min(max(avg_confidence, 0.0), 1.0)


class TextFormatter:
    """Advanced text formatting and enhancement"""
    
    def __init__(self):
        """Initialize the text formatter"""
        self.punctuation_restorer = PunctuationRestorer()
        
        # Common formatting patterns
        self.formatting_rules = {
            'quotes': r'(\w+)\s+quote\s+([^"]+)\s+unquote',
            'numbers': r'\b(one|two|three|four|five|six|seven|eight|nine|ten)\b',
            'dates': r'\b(\w+)\s+(\d{1,2})\s+(\d{4})\b',
            'times': r'\b(\d{1,2})\s+(am|pm)\b'
        }
    
    def format_text(self, text: str, options: Dict[str, bool] = None) -> TextEnhancementResult:
        """Apply comprehensive text formatting"""
        if options is None:
            options = {
                'restore_punctuation': True,
                'fix_capitalization': True,
                'format_numbers': True,
                'format_quotes': True,
                'format_dates': True
            }
        
        start_time = datetime.now()
        all_changes = []
        enhanced_text = text
        
        # Step 1: Restore punctuation
        if options.get('restore_punctuation', True):
            punct_result = self.punctuation_restorer.restore_punctuation(enhanced_text)
            enhanced_text = punct_result.enhanced_text
            all_changes.extend(punct_result.changes_made)
        
        # Step 2: Format specific patterns
        if options.get('format_quotes', True):
            enhanced_text, quote_changes = self._format_quotes(enhanced_text)
            all_changes.extend(quote_changes)
        
        if options.get('format_numbers', True):
            enhanced_text, number_changes = self._format_numbers(enhanced_text)
            all_changes.extend(number_changes)
        
        if options.get('format_dates', True):
            enhanced_text, date_changes = self._format_dates(enhanced_text)
            all_changes.extend(date_changes)
        
        # Calculate overall confidence
        confidence = self._calculate_overall_confidence(text, enhanced_text, all_changes)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return TextEnhancementResult(
            original_text=text,
            enhanced_text=enhanced_text,
            confidence_score=confidence,
            changes_made=all_changes,
            processing_time=processing_time,
            metadata={
                'formatting_options': options,
                'total_changes': len(all_changes)
            }
        )
    
    def _format_quotes(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Format quoted text"""
        changes_made = []
        enhanced_text = text
        
        # Convert "quote ... unquote" to proper quotes
        pattern = r'(\w+\s+)?quote\s+([^"]+?)\s+unquote'
        matches = list(re.finditer(pattern, enhanced_text, re.IGNORECASE))
        
        for match in reversed(matches):
            quoted_text = match.group(2).strip()
            replacement = f'"{quoted_text}"'
            
            enhanced_text = enhanced_text[:match.start()] + replacement + enhanced_text[match.end():]
            
            changes_made.append({
                'position': match.start(),
                'original': match.group(0),
                'replacement': replacement,
                'change_type': 'replace',
                'confidence': 0.9,
                'reason': 'Quote formatting'
            })
        
        return enhanced_text, changes_made
    
    def _format_numbers(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Format number words to digits where appropriate"""
        changes_made = []
        enhanced_text = text
        
        number_words = {
            'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
            'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
            'eleven': '11', 'twelve': '12', 'thirteen': '13', 'fourteen': '14',
            'fifteen': '15', 'sixteen': '16', 'seventeen': '17', 'eighteen': '18',
            'nineteen': '19', 'twenty': '20'
        }
        
        for word, digit in number_words.items():
            pattern = r'\b' + word + r'\b'
            matches = list(re.finditer(pattern, enhanced_text, re.IGNORECASE))
            
            for match in reversed(matches):
                # Only replace if it seems like a quantity (simple heuristic)
                context_before = enhanced_text[max(0, match.start()-20):match.start()]
                context_after = enhanced_text[match.end():match.end()+20]
                
                if any(indicator in context_before.lower() + context_after.lower() 
                       for indicator in ['page', 'chapter', 'step', 'number', 'item', 'point']):
                    enhanced_text = enhanced_text[:match.start()] + digit + enhanced_text[match.end():]
                    
                    changes_made.append({
                        'position': match.start(),
                        'original': match.group(0),
                        'replacement': digit,
                        'change_type': 'replace',
                        'confidence': 0.8,
                        'reason': 'Number word to digit conversion'
                    })
        
        return enhanced_text, changes_made
    
    def _format_dates(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Format date expressions"""
        changes_made = []
        enhanced_text = text
        
        # Format "January 1st 2023" style dates
        date_pattern = r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:st|nd|rd|th)?\s+(\d{4})\b'
        matches = list(re.finditer(date_pattern, enhanced_text, re.IGNORECASE))
        
        for match in reversed(matches):
            month, day, year = match.groups()
            formatted_date = f"{month} {day}, {year}"
            
            enhanced_text = enhanced_text[:match.start()] + formatted_date + enhanced_text[match.end():]
            
            changes_made.append({
                'position': match.start(),
                'original': match.group(0),
                'replacement': formatted_date,
                'change_type': 'replace',
                'confidence': 0.9,
                'reason': 'Date formatting'
            })
        
        return enhanced_text, changes_made
    
    def _calculate_overall_confidence(self, original: str, enhanced: str, changes: List[Dict]) -> float:
        """Calculate overall confidence for formatting"""
        if not changes:
            return 1.0
        
        # Weight by change type and confidence
        total_weight = 0
        weighted_confidence = 0
        
        for change in changes:
            weight = 1.0
            if change['change_type'] == 'add':
                weight = 1.2  # Adding punctuation is usually good
            elif change['change_type'] == 'replace':
                weight = 0.9  # Replacements are slightly less certain
            
            weighted_confidence += change.get('confidence', 0.5) * weight
            total_weight += weight
        
        return weighted_confidence / total_weight if total_weight > 0 else 0.5


class PunctuationEnhancementService:
    """Main service for punctuation restoration and text enhancement"""
    
    def __init__(self):
        """Initialize the enhancement service"""
        self.text_formatter = TextFormatter()
        self.enhancement_history = []
        self.max_history = 100
    
    def enhance_transcript(self, transcript: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Enhance a transcript with punctuation and formatting"""
        if options is None:
            options = {
                'restore_punctuation': True,
                'fix_capitalization': True,
                'format_numbers': True,
                'format_quotes': True,
                'format_dates': True,
                'confidence_threshold': 0.7
            }
        
        try:
            # Apply text formatting
            result = self.text_formatter.format_text(transcript, options)
            
            # Store in history
            self._add_to_history(result)
            
            # Return formatted result
            return {
                'success': True,
                'original_text': result.original_text,
                'enhanced_text': result.enhanced_text,
                'confidence_score': result.confidence_score,
                'changes_made': result.changes_made,
                'processing_time': result.processing_time,
                'metadata': result.metadata,
                'statistics': {
                    'original_length': len(result.original_text),
                    'enhanced_length': len(result.enhanced_text),
                    'changes_count': len(result.changes_made),
                    'improvement_ratio': len(result.enhanced_text) / len(result.original_text) if result.original_text else 1.0
                }
            }
            
        except Exception as e:
            logger.error(f"Transcript enhancement failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'original_text': transcript,
                'enhanced_text': transcript
            }
    
    def batch_enhance(self, transcripts: List[str], options: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Enhance multiple transcripts"""
        results = []
        
        for i, transcript in enumerate(transcripts):
            logger.info(f"Enhancing transcript {i+1}/{len(transcripts)}")
            result = self.enhance_transcript(transcript, options)
            results.append(result)
        
        return results
    
    def get_enhancement_statistics(self) -> Dict[str, Any]:
        """Get statistics about enhancement performance"""
        if not self.enhancement_history:
            return {'message': 'No enhancement history available'}
        
        total_enhancements = len(self.enhancement_history)
        avg_confidence = sum(r.confidence_score for r in self.enhancement_history) / total_enhancements
        avg_processing_time = sum(r.processing_time for r in self.enhancement_history) / total_enhancements
        total_changes = sum(len(r.changes_made) for r in self.enhancement_history)
        
        return {
            'total_enhancements': total_enhancements,
            'average_confidence': avg_confidence,
            'average_processing_time': avg_processing_time,
            'total_changes_made': total_changes,
            'average_changes_per_text': total_changes / total_enhancements
        }
    
    def _add_to_history(self, result: TextEnhancementResult):
        """Add result to enhancement history"""
        self.enhancement_history.append(result)
        
        # Maintain history size limit
        if len(self.enhancement_history) > self.max_history:
            self.enhancement_history = self.enhancement_history[-self.max_history:]


# Global service instance
punctuation_service = PunctuationEnhancementService()

def get_punctuation_service() -> PunctuationEnhancementService:
    """Get the punctuation enhancement service instance"""
    return punctuation_service

if __name__ == "__main__":
    # Example usage
    service = get_punctuation_service()
    
    sample_text = "hello world this is a test can you hear me yes i can hear you perfectly what time is it now its three thirty pm"
    
    result = service.enhance_transcript(sample_text)
    
    print("Original:", result['original_text'])
    print("Enhanced:", result['enhanced_text'])
    print("Confidence:", result['confidence_score'])
    print("Changes:", len(result['changes_made']))