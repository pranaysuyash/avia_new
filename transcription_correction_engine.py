"""
Speech-to-Text Correction System
Intelligent system for automatic and manual correction of transcription errors with learning capabilities
"""

import asyncio
import json
import re
import difflib
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
import numpy as np
import pandas as pd
from collections import defaultdict, Counter
import spacy
from spacy.tokens import Doc, Token
from spacy.language import Language
import language_tool_python
from symspellpy import SymSpell, Verbosity
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    AutoModelForSequenceClassification,
    pipeline
)
import torch
import torch.nn as nn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import fuzz, process
import editdistance
import logging
from abc import ABC, abstractmethod
import sqlite3
import redis.asyncio as redis
import hashlib

logger = logging.getLogger(__name__)

class CorrectionType(str, Enum):
    """Types of corrections"""
    SPELLING = "spelling"
    GRAMMAR = "grammar"
    PUNCTUATION = "punctuation"
    CAPITALIZATION = "capitalization"
    WORD_BOUNDARY = "word_boundary"
    HOMOPHONE = "homophone"
    CONTEXT = "context"
    TECHNICAL = "technical"
    NAME = "name"
    NUMBER = "number"
    ABBREVIATION = "abbreviation"

class ConfidenceLevel(str, Enum):
    """Confidence levels for corrections"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MANUAL = "manual"

@dataclass
class CorrectionSuggestion:
    """A correction suggestion"""
    original_text: str
    corrected_text: str
    correction_type: CorrectionType
    confidence: float
    confidence_level: ConfidenceLevel
    position: Tuple[int, int]  # (start, end) character positions
    context: str
    reason: str
    alternatives: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'original_text': self.original_text,
            'corrected_text': self.corrected_text,
            'correction_type': self.correction_type.value,
            'confidence': self.confidence,
            'confidence_level': self.confidence_level.value,
            'position': self.position,
            'context': self.context,
            'reason': self.reason,
            'alternatives': self.alternatives,
            'metadata': self.metadata
        }

@dataclass
class CorrectionPattern:
    """A learned correction pattern"""
    pattern_id: str
    error_pattern: str
    correction_pattern: str
    correction_type: CorrectionType
    frequency: int
    confidence: float
    examples: List[Dict[str, str]]
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'pattern_id': self.pattern_id,
            'error_pattern': self.error_pattern,
            'correction_pattern': self.correction_pattern,
            'correction_type': self.correction_type.value,
            'frequency': self.frequency,
            'confidence': self.confidence,
            'examples': self.examples,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

@dataclass
class CustomDictionary:
    """Custom dictionary for domain-specific terms"""
    dictionary_id: str
    name: str
    domain: str
    terms: Dict[str, Dict[str, Any]]  # term -> {definition, frequency, variations}
    abbreviations: Dict[str, str]  # abbreviation -> full form
    created_at: datetime
    updated_at: datetime
    
    def add_term(self, term: str, definition: str = "", variations: List[str] = None):
        """Add a term to the dictionary"""
        self.terms[term.lower()] = {
            'definition': definition,
            'frequency': 1,
            'variations': variations or [],
            'original_case': term
        }
        self.updated_at = datetime.utcnow()
        
    def add_abbreviation(self, abbr: str, full_form: str):
        """Add an abbreviation"""
        self.abbreviations[abbr.upper()] = full_form
        self.updated_at = datetime.utcnow()

class CorrectionEngine(ABC):
    """Abstract base class for correction engines"""
    
    @abstractmethod
    async def correct(self, text: str, context: Optional[str] = None) -> List[CorrectionSuggestion]:
        """Perform corrections on text"""
        pass

class SpellingCorrector(CorrectionEngine):
    """Spelling correction engine"""
    
    def __init__(self, custom_dictionary: Optional[CustomDictionary] = None):
        # Initialize SymSpell for fast spell correction
        self.sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
        
        # Load frequency dictionary
        dictionary_path = Path(__file__).parent / "data" / "frequency_dictionary_en_82_765.txt"
        if dictionary_path.exists():
            self.sym_spell.load_dictionary(
                str(dictionary_path),
                term_index=0,
                count_index=1
            )
        
        self.custom_dictionary = custom_dictionary
        
        # Add custom terms to SymSpell
        if custom_dictionary:
            for term, info in custom_dictionary.terms.items():
                self.sym_spell.create_dictionary_entry(term, info.get('frequency', 1))
                
    async def correct(self, text: str, context: Optional[str] = None) -> List[CorrectionSuggestion]:
        """Correct spelling errors"""
        suggestions = []
        words = text.split()
        position = 0
        
        for word in words:
            # Skip if in custom dictionary
            if self.custom_dictionary and word.lower() in self.custom_dictionary.terms:
                position += len(word) + 1
                continue
                
            # Check spelling
            suggestions_list = self.sym_spell.lookup(
                word,
                Verbosity.CLOSEST,
                max_edit_distance=2
            )
            
            if suggestions_list and suggestions_list[0].term != word.lower():
                best_suggestion = suggestions_list[0]
                
                # Calculate confidence based on edit distance
                confidence = 1.0 - (best_suggestion.distance / max(len(word), 1))
                
                # Get alternatives
                alternatives = [s.term for s in suggestions_list[1:4]]
                
                suggestion = CorrectionSuggestion(
                    original_text=word,
                    corrected_text=best_suggestion.term,
                    correction_type=CorrectionType.SPELLING,
                    confidence=confidence,
                    confidence_level=ConfidenceLevel.HIGH if confidence > 0.8 else ConfidenceLevel.MEDIUM,
                    position=(position, position + len(word)),
                    context=context or text,
                    reason=f"Possible spelling error: '{word}' -> '{best_suggestion.term}'",
                    alternatives=alternatives,
                    metadata={'edit_distance': best_suggestion.distance}
                )
                suggestions.append(suggestion)
                
            position += len(word) + 1
            
        return suggestions

class GrammarCorrector(CorrectionEngine):
    """Grammar correction engine"""
    
    def __init__(self):
        # Initialize LanguageTool for grammar checking
        self.tool = language_tool_python.LanguageTool('en-US')
        
        # Load spaCy for advanced grammar analysis
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
            
    async def correct(self, text: str, context: Optional[str] = None) -> List[CorrectionSuggestion]:
        """Correct grammar errors"""
        suggestions = []
        
        # Check with LanguageTool
        matches = self.tool.check(text)
        
        for match in matches:
            if match.replacements:
                # Calculate confidence based on rule confidence
                confidence = 0.9 if match.ruleIssueType == 'misspelling' else 0.7
                
                suggestion = CorrectionSuggestion(
                    original_text=text[match.offset:match.offset + match.errorLength],
                    corrected_text=match.replacements[0] if match.replacements else "",
                    correction_type=self._get_correction_type(match.ruleId),
                    confidence=confidence,
                    confidence_level=ConfidenceLevel.HIGH if confidence > 0.8 else ConfidenceLevel.MEDIUM,
                    position=(match.offset, match.offset + match.errorLength),
                    context=context or text,
                    reason=match.message,
                    alternatives=match.replacements[1:4] if len(match.replacements) > 1 else [],
                    metadata={'rule_id': match.ruleId, 'category': match.category}
                )
                suggestions.append(suggestion)
                
        return suggestions
        
    def _get_correction_type(self, rule_id: str) -> CorrectionType:
        """Map LanguageTool rule to correction type"""
        if 'SPELL' in rule_id:
            return CorrectionType.SPELLING
        elif 'GRAMMAR' in rule_id:
            return CorrectionType.GRAMMAR
        elif 'PUNCT' in rule_id:
            return CorrectionType.PUNCTUATION
        elif 'UPPERCASE' in rule_id or 'LOWERCASE' in rule_id:
            return CorrectionType.CAPITALIZATION
        else:
            return CorrectionType.GRAMMAR

class PunctuationCorrector(CorrectionEngine):
    """Punctuation restoration and correction"""
    
    def __init__(self):
        # Load punctuation restoration model
        self.tokenizer = AutoTokenizer.from_pretrained("oliverguhr/fullstop-punctuation-multilang-large")
        self.model = AutoModelForTokenClassification.from_pretrained("oliverguhr/fullstop-punctuation-multilang-large")
        
        # Punctuation rules
        self.sentence_endings = {'.', '!', '?'}
        self.mid_punctuation = {',', ';', ':'}
        
    async def correct(self, text: str, context: Optional[str] = None) -> List[CorrectionSuggestion]:
        """Restore and correct punctuation"""
        suggestions = []
        
        # Tokenize text
        tokens = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        
        # Get predictions
        with torch.no_grad():
            outputs = self.model(**tokens)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
        # Get token labels
        predicted_labels = torch.argmax(predictions, dim=-1).squeeze().tolist()
        
        # Map predictions to punctuation
        word_tokens = self.tokenizer.convert_ids_to_tokens(tokens['input_ids'].squeeze())
        
        current_position = 0
        for i, (token, label_id) in enumerate(zip(word_tokens, predicted_labels)):
            if token in ['[CLS]', '[SEP]', '[PAD]']:
                continue
                
            # Get punctuation for this position
            punct = self._label_to_punctuation(label_id)
            
            if punct and punct != ' ':
                # Check if punctuation is missing
                next_char_pos = text.find(' ', current_position)
                if next_char_pos == -1:
                    next_char_pos = len(text)
                    
                if next_char_pos < len(text) and text[next_char_pos - 1] not in self.sentence_endings.union(self.mid_punctuation):
                    suggestion = CorrectionSuggestion(
                        original_text=text[current_position:next_char_pos],
                        corrected_text=text[current_position:next_char_pos] + punct,
                        correction_type=CorrectionType.PUNCTUATION,
                        confidence=float(predictions[0, i, label_id]),
                        confidence_level=ConfidenceLevel.HIGH if predictions[0, i, label_id] > 0.8 else ConfidenceLevel.MEDIUM,
                        position=(current_position, next_char_pos),
                        context=context or text,
                        reason=f"Missing punctuation: add '{punct}'",
                        alternatives=[],
                        metadata={'predicted_label': label_id}
                    )
                    suggestions.append(suggestion)
                    
            current_position = next_char_pos + 1
            
        return suggestions
        
    def _label_to_punctuation(self, label_id: int) -> str:
        """Convert label ID to punctuation mark"""
        # This mapping depends on the specific model used
        label_map = {
            0: '',      # No punctuation
            1: '.',     # Period
            2: ',',     # Comma
            3: '?',     # Question mark
            4: '!',     # Exclamation mark
            5: ':',     # Colon
            6: ';',     # Semicolon
        }
        return label_map.get(label_id, '')

class ContextualCorrector(CorrectionEngine):
    """Context-aware correction using language models"""
    
    def __init__(self):
        # Load BERT for context understanding
        self.tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
        self.model = AutoModelForSequenceClassification.from_pretrained("bert-base-uncased")
        
        # Common homophones
        self.homophones = {
            'there': ['their', 'they\'re'],
            'their': ['there', 'they\'re'],
            'they\'re': ['there', 'their'],
            'to': ['too', 'two'],
            'too': ['to', 'two'],
            'two': ['to', 'too'],
            'your': ['you\'re'],
            'you\'re': ['your'],
            'its': ['it\'s'],
            'it\'s': ['its'],
            'whose': ['who\'s'],
            'who\'s': ['whose'],
            'accept': ['except'],
            'except': ['accept'],
            'affect': ['effect'],
            'effect': ['affect'],
        }
        
    async def correct(self, text: str, context: Optional[str] = None) -> List[CorrectionSuggestion]:
        """Correct based on context"""
        suggestions = []
        words = text.split()
        
        for i, word in enumerate(words):
            word_lower = word.lower()
            
            # Check for homophones
            if word_lower in self.homophones:
                alternatives = self.homophones[word_lower]
                
                # Test each alternative in context
                best_alternative = None
                best_score = 0
                
                for alt in alternatives:
                    # Replace word with alternative
                    test_text = ' '.join(words[:i] + [alt] + words[i+1:])
                    
                    # Score the alternative
                    score = await self._score_text(test_text)
                    
                    if score > best_score:
                        best_score = score
                        best_alternative = alt
                        
                # Compare with original
                original_score = await self._score_text(text)
                
                if best_alternative and best_score > original_score * 1.1:  # 10% improvement threshold
                    position_start = sum(len(w) + 1 for w in words[:i])
                    position_end = position_start + len(word)
                    
                    suggestion = CorrectionSuggestion(
                        original_text=word,
                        corrected_text=best_alternative,
                        correction_type=CorrectionType.HOMOPHONE,
                        confidence=(best_score - original_score) / original_score,
                        confidence_level=ConfidenceLevel.MEDIUM,
                        position=(position_start, position_end),
                        context=context or text,
                        reason=f"Possible homophone error: '{word}' might be '{best_alternative}'",
                        alternatives=alternatives,
                        metadata={'original_score': original_score, 'best_score': best_score}
                    )
                    suggestions.append(suggestion)
                    
        return suggestions
        
    async def _score_text(self, text: str) -> float:
        """Score text coherence using language model"""
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Use the model's confidence as a proxy for text quality
            score = torch.nn.functional.softmax(outputs.logits, dim=-1).max().item()
            
        return score

class TechnicalTermCorrector(CorrectionEngine):
    """Correction for technical terms and domain-specific vocabulary"""
    
    def __init__(self, custom_dictionary: Optional[CustomDictionary] = None):
        self.custom_dictionary = custom_dictionary
        self.technical_patterns = {
            # Common technical term patterns
            r'\b(\w+)\.(\w+)\b': self._check_file_extension,
            r'\b([A-Z]{2,})\b': self._check_acronym,
            r'\b(\d+)([KMG]B?)\b': self._check_size_unit,
            r'\b(v?\d+\.\d+\.\d+)\b': self._check_version_number,
        }
        
    async def correct(self, text: str, context: Optional[str] = None) -> List[CorrectionSuggestion]:
        """Correct technical terms"""
        suggestions = []
        
        for pattern, checker in self.technical_patterns.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                suggestion = checker(match, text)
                if suggestion:
                    suggestions.append(suggestion)
                    
        return suggestions
        
    def _check_file_extension(self, match: re.Match, text: str) -> Optional[CorrectionSuggestion]:
        """Check file extensions"""
        full_match = match.group(0)
        name = match.group(1)
        ext = match.group(2)
        
        # Common extensions
        common_extensions = {
            'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
            'jpg', 'jpeg', 'png', 'gif', 'mp3', 'mp4', 'wav', 'avi',
            'py', 'js', 'java', 'cpp', 'c', 'h', 'css', 'html', 'xml', 'json',
            'zip', 'tar', 'gz', 'rar', '7z'
        }
        
        if ext.lower() not in common_extensions:
            # Find closest match
            closest = process.extractOne(ext.lower(), common_extensions, scorer=fuzz.ratio)
            if closest and closest[1] > 80:  # 80% similarity threshold
                return CorrectionSuggestion(
                    original_text=full_match,
                    corrected_text=f"{name}.{closest[0]}",
                    correction_type=CorrectionType.TECHNICAL,
                    confidence=closest[1] / 100,
                    confidence_level=ConfidenceLevel.MEDIUM,
                    position=match.span(),
                    context=text,
                    reason=f"Possible file extension error: '.{ext}' -> '.{closest[0]}'",
                    alternatives=[],
                    metadata={'extension': ext, 'suggested': closest[0]}
                )
        return None
        
    def _check_acronym(self, match: re.Match, text: str) -> Optional[CorrectionSuggestion]:
        """Check acronyms"""
        acronym = match.group(0)
        
        if self.custom_dictionary and acronym in self.custom_dictionary.abbreviations:
            # Acronym is in dictionary, no correction needed
            return None
            
        # Check common misspellings of acronyms
        common_acronyms = {
            'HTTP', 'HTTPS', 'API', 'URL', 'JSON', 'XML', 'SQL', 'HTML', 'CSS',
            'PDF', 'CPU', 'GPU', 'RAM', 'SSD', 'HDD', 'USB', 'HDMI',
            'AI', 'ML', 'DL', 'NLP', 'CV', 'IoT', 'AR', 'VR'
        }
        
        closest = process.extractOne(acronym, common_acronyms, scorer=fuzz.ratio)
        if closest and closest[1] > 85 and closest[0] != acronym:
            return CorrectionSuggestion(
                original_text=acronym,
                corrected_text=closest[0],
                correction_type=CorrectionType.ABBREVIATION,
                confidence=closest[1] / 100,
                confidence_level=ConfidenceLevel.LOW,
                position=match.span(),
                context=text,
                reason=f"Possible acronym error: '{acronym}' -> '{closest[0]}'",
                alternatives=[],
                metadata={'acronym': acronym, 'suggested': closest[0]}
            )
        return None
        
    def _check_size_unit(self, match: re.Match, text: str) -> Optional[CorrectionSuggestion]:
        """Check data size units"""
        number = match.group(1)
        unit = match.group(2)
        
        # Correct units
        correct_units = {'KB', 'MB', 'GB', 'TB', 'PB', 'K', 'M', 'G', 'T', 'P'}
        
        if unit.upper() not in correct_units:
            # Find closest match
            closest = process.extractOne(unit.upper(), correct_units, scorer=fuzz.ratio)
            if closest and closest[1] > 70:
                return CorrectionSuggestion(
                    original_text=match.group(0),
                    corrected_text=f"{number}{closest[0]}",
                    correction_type=CorrectionType.TECHNICAL,
                    confidence=closest[1] / 100,
                    confidence_level=ConfidenceLevel.MEDIUM,
                    position=match.span(),
                    context=text,
                    reason=f"Possible unit error: '{unit}' -> '{closest[0]}'",
                    alternatives=[],
                    metadata={'original_unit': unit, 'suggested_unit': closest[0]}
                )
        return None
        
    def _check_version_number(self, match: re.Match, text: str) -> Optional[CorrectionSuggestion]:
        """Check version numbers"""
        version = match.group(0)
        
        # Check for common version formats
        if not re.match(r'^v?\d+\.\d+(\.\d+)?(-[a-zA-Z0-9]+)?$', version):
            # Suggest standard format
            parts = re.findall(r'\d+', version)
            if len(parts) >= 2:
                suggested = '.'.join(parts[:3])  # Major.Minor.Patch
                if version.lower().startswith('v'):
                    suggested = 'v' + suggested
                    
                if suggested != version:
                    return CorrectionSuggestion(
                        original_text=version,
                        corrected_text=suggested,
                        correction_type=CorrectionType.TECHNICAL,
                        confidence=0.7,
                        confidence_level=ConfidenceLevel.LOW,
                        position=match.span(),
                        context=text,
                        reason=f"Standardize version format: '{version}' -> '{suggested}'",
                        alternatives=[],
                        metadata={'original': version, 'suggested': suggested}
                    )
        return None

class CorrectionLearningSystem:
    """System that learns from user corrections"""
    
    def __init__(self, db_path: str = "corrections.db"):
        self.db_path = db_path
        self.patterns: Dict[str, CorrectionPattern] = {}
        self.user_corrections: List[Dict[str, Any]] = []
        self._init_database()
        self._load_patterns()
        
    def _init_database(self):
        """Initialize SQLite database for storing corrections"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS correction_patterns (
                pattern_id TEXT PRIMARY KEY,
                error_pattern TEXT,
                correction_pattern TEXT,
                correction_type TEXT,
                frequency INTEGER,
                confidence REAL,
                examples TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_text TEXT,
                corrected_text TEXT,
                correction_type TEXT,
                context TEXT,
                timestamp TEXT,
                accepted BOOLEAN
            )
        """)
        
        conn.commit()
        conn.close()
        
    def _load_patterns(self):
        """Load learned patterns from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM correction_patterns")
        rows = cursor.fetchall()
        
        for row in rows:
            pattern = CorrectionPattern(
                pattern_id=row[0],
                error_pattern=row[1],
                correction_pattern=row[2],
                correction_type=CorrectionType(row[3]),
                frequency=row[4],
                confidence=row[5],
                examples=json.loads(row[6]),
                created_at=datetime.fromisoformat(row[7]),
                updated_at=datetime.fromisoformat(row[8])
            )
            self.patterns[pattern.pattern_id] = pattern
            
        conn.close()
        
    async def learn_from_correction(
        self,
        original: str,
        corrected: str,
        correction_type: CorrectionType,
        context: str,
        accepted: bool = True
    ):
        """Learn from a user correction"""
        # Store correction
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO user_corrections 
            (original_text, corrected_text, correction_type, context, timestamp, accepted)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (original, corrected, correction_type.value, context, datetime.utcnow().isoformat(), accepted))
        
        conn.commit()
        conn.close()
        
        if accepted:
            # Extract pattern
            pattern = self._extract_pattern(original, corrected)
            
            if pattern:
                # Update or create pattern
                pattern_id = hashlib.md5(f"{pattern[0]}_{pattern[1]}".encode()).hexdigest()
                
                if pattern_id in self.patterns:
                    # Update existing pattern
                    existing = self.patterns[pattern_id]
                    existing.frequency += 1
                    existing.confidence = min(0.95, existing.confidence + 0.05)
                    existing.examples.append({'original': original, 'corrected': corrected})
                    existing.updated_at = datetime.utcnow()
                    
                    # Keep only last 10 examples
                    if len(existing.examples) > 10:
                        existing.examples = existing.examples[-10:]
                else:
                    # Create new pattern
                    new_pattern = CorrectionPattern(
                        pattern_id=pattern_id,
                        error_pattern=pattern[0],
                        correction_pattern=pattern[1],
                        correction_type=correction_type,
                        frequency=1,
                        confidence=0.5,
                        examples=[{'original': original, 'corrected': corrected}],
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    self.patterns[pattern_id] = new_pattern
                    
                # Save to database
                await self._save_pattern(self.patterns[pattern_id])
                
    def _extract_pattern(self, original: str, corrected: str) -> Optional[Tuple[str, str]]:
        """Extract a pattern from a correction"""
        # Simple pattern extraction based on word differences
        original_words = original.split()
        corrected_words = corrected.split()
        
        if len(original_words) == len(corrected_words):
            # Word-level replacement
            for i, (o, c) in enumerate(zip(original_words, corrected_words)):
                if o != c:
                    # Create pattern
                    return (o.lower(), c.lower())
                    
        # Character-level patterns for small differences
        if editdistance.eval(original, corrected) <= 3:
            # Find the difference
            matcher = difflib.SequenceMatcher(None, original, corrected)
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == 'replace':
                    return (original[i1:i2], corrected[j1:j2])
                    
        return None
        
    async def _save_pattern(self, pattern: CorrectionPattern):
        """Save pattern to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO correction_patterns
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pattern.pattern_id,
            pattern.error_pattern,
            pattern.correction_pattern,
            pattern.correction_type.value,
            pattern.frequency,
            pattern.confidence,
            json.dumps(pattern.examples),
            pattern.created_at.isoformat(),
            pattern.updated_at.isoformat()
        ))
        
        conn.commit()
        conn.close()
        
    async def apply_learned_patterns(self, text: str) -> List[CorrectionSuggestion]:
        """Apply learned patterns to text"""
        suggestions = []
        
        for pattern in self.patterns.values():
            if pattern.confidence < 0.6:  # Skip low-confidence patterns
                continue
                
            # Find all occurrences of the error pattern
            if pattern.error_pattern in text.lower():
                # Find exact position
                for match in re.finditer(re.escape(pattern.error_pattern), text.lower()):
                    suggestion = CorrectionSuggestion(
                        original_text=text[match.start():match.end()],
                        corrected_text=pattern.correction_pattern,
                        correction_type=pattern.correction_type,
                        confidence=pattern.confidence,
                        confidence_level=ConfidenceLevel.HIGH if pattern.confidence > 0.8 else ConfidenceLevel.MEDIUM,
                        position=match.span(),
                        context=text,
                        reason=f"Learned pattern: '{pattern.error_pattern}' -> '{pattern.correction_pattern}' (seen {pattern.frequency} times)",
                        alternatives=[],
                        metadata={'pattern_id': pattern.pattern_id, 'frequency': pattern.frequency}
                    )
                    suggestions.append(suggestion)
                    
        return suggestions
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get learning statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get correction statistics
        cursor.execute("SELECT COUNT(*) FROM user_corrections")
        total_corrections = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM user_corrections WHERE accepted = 1")
        accepted_corrections = cursor.fetchone()[0]
        
        cursor.execute("SELECT correction_type, COUNT(*) FROM user_corrections GROUP BY correction_type")
        corrections_by_type = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_corrections': total_corrections,
            'accepted_corrections': accepted_corrections,
            'rejection_rate': 1 - (accepted_corrections / max(total_corrections, 1)),
            'corrections_by_type': corrections_by_type,
            'learned_patterns': len(self.patterns),
            'high_confidence_patterns': sum(1 for p in self.patterns.values() if p.confidence > 0.8)
        }

class TranscriptionCorrectionSystem:
    """Main transcription correction system"""
    
    def __init__(
        self,
        custom_dictionary: Optional[CustomDictionary] = None,
        enable_learning: bool = True
    ):
        self.custom_dictionary = custom_dictionary
        self.enable_learning = enable_learning
        
        # Initialize correction engines
        self.spelling_corrector = SpellingCorrector(custom_dictionary)
        self.grammar_corrector = GrammarCorrector()
        self.punctuation_corrector = PunctuationCorrector()
        self.contextual_corrector = ContextualCorrector()
        self.technical_corrector = TechnicalTermCorrector(custom_dictionary)
        
        # Learning system
        if enable_learning:
            self.learning_system = CorrectionLearningSystem()
        else:
            self.learning_system = None
            
        # Correction history
        self.correction_history: List[Dict[str, Any]] = []
        
    async def correct_transcription(
        self,
        text: str,
        correction_types: Optional[List[CorrectionType]] = None,
        context: Optional[str] = None,
        confidence_threshold: float = 0.5
    ) -> Dict[str, Any]:
        """Perform comprehensive transcription correction"""
        
        if not correction_types:
            correction_types = list(CorrectionType)
            
        all_suggestions = []
        
        # Apply learned patterns first
        if self.learning_system:
            learned_suggestions = await self.learning_system.apply_learned_patterns(text)
            all_suggestions.extend(learned_suggestions)
            
        # Apply different correction engines
        if CorrectionType.SPELLING in correction_types:
            spelling_suggestions = await self.spelling_corrector.correct(text, context)
            all_suggestions.extend(spelling_suggestions)
            
        if CorrectionType.GRAMMAR in correction_types:
            grammar_suggestions = await self.grammar_corrector.correct(text, context)
            all_suggestions.extend(grammar_suggestions)
            
        if CorrectionType.PUNCTUATION in correction_types:
            punctuation_suggestions = await self.punctuation_corrector.correct(text, context)
            all_suggestions.extend(punctuation_suggestions)
            
        if CorrectionType.CONTEXT in correction_types or CorrectionType.HOMOPHONE in correction_types:
            contextual_suggestions = await self.contextual_corrector.correct(text, context)
            all_suggestions.extend(contextual_suggestions)
            
        if CorrectionType.TECHNICAL in correction_types:
            technical_suggestions = await self.technical_corrector.correct(text, context)
            all_suggestions.extend(technical_suggestions)
            
        # Filter by confidence threshold
        filtered_suggestions = [
            s for s in all_suggestions
            if s.confidence >= confidence_threshold
        ]
        
        # Resolve conflicts (overlapping corrections)
        resolved_suggestions = self._resolve_conflicts(filtered_suggestions)
        
        # Apply corrections to generate corrected text
        corrected_text = self._apply_corrections(text, resolved_suggestions)
        
        # Calculate overall confidence
        overall_confidence = np.mean([s.confidence for s in resolved_suggestions]) if resolved_suggestions else 1.0
        
        # Store in history
        result = {
            'original_text': text,
            'corrected_text': corrected_text,
            'suggestions': [s.to_dict() for s in resolved_suggestions],
            'total_corrections': len(resolved_suggestions),
            'overall_confidence': overall_confidence,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.correction_history.append(result)
        
        return result
        
    def _resolve_conflicts(self, suggestions: List[CorrectionSuggestion]) -> List[CorrectionSuggestion]:
        """Resolve overlapping correction suggestions"""
        # Sort by position
        suggestions.sort(key=lambda s: s.position[0])
        
        resolved = []
        last_end = -1
        
        for suggestion in suggestions:
            # Check for overlap
            if suggestion.position[0] >= last_end:
                # No overlap, add suggestion
                resolved.append(suggestion)
                last_end = suggestion.position[1]
            else:
                # Overlap detected, choose higher confidence
                if resolved and suggestion.confidence > resolved[-1].confidence:
                    # Replace previous with current
                    resolved[-1] = suggestion
                    last_end = suggestion.position[1]
                    
        return resolved
        
    def _apply_corrections(self, text: str, suggestions: List[CorrectionSuggestion]) -> str:
        """Apply corrections to generate corrected text"""
        if not suggestions:
            return text
            
        # Sort by position (reverse order to maintain positions)
        suggestions.sort(key=lambda s: s.position[0], reverse=True)
        
        corrected = text
        for suggestion in suggestions:
            start, end = suggestion.position
            corrected = corrected[:start] + suggestion.corrected_text + corrected[end:]
            
        return corrected
        
    async def accept_correction(
        self,
        original: str,
        corrected: str,
        correction_type: CorrectionType,
        context: str = ""
    ):
        """Accept a user correction for learning"""
        if self.learning_system:
            await self.learning_system.learn_from_correction(
                original,
                corrected,
                correction_type,
                context,
                accepted=True
            )
            
    async def reject_correction(
        self,
        original: str,
        suggested: str,
        correction_type: CorrectionType,
        context: str = ""
    ):
        """Reject a suggested correction for learning"""
        if self.learning_system:
            await self.learning_system.learn_from_correction(
                original,
                suggested,
                correction_type,
                context,
                accepted=False
            )
            
    def add_to_dictionary(self, term: str, definition: str = "", variations: List[str] = None):
        """Add term to custom dictionary"""
        if self.custom_dictionary:
            self.custom_dictionary.add_term(term, definition, variations)
            
    def add_abbreviation(self, abbr: str, full_form: str):
        """Add abbreviation to dictionary"""
        if self.custom_dictionary:
            self.custom_dictionary.add_abbreviation(abbr, full_form)
            
    def get_statistics(self) -> Dict[str, Any]:
        """Get correction statistics"""
        stats = {
            'total_corrections_made': len(self.correction_history),
            'corrections_by_type': defaultdict(int)
        }
        
        for correction in self.correction_history:
            for suggestion in correction['suggestions']:
                stats['corrections_by_type'][suggestion['correction_type']] += 1
                
        if self.learning_system:
            stats['learning_statistics'] = self.learning_system.get_statistics()
            
        return dict(stats)
        
    def export_corrections(self, output_path: str):
        """Export correction history"""
        with open(output_path, 'w') as f:
            json.dump(self.correction_history, f, indent=2)
            
    def import_custom_dictionary(self, dictionary_path: str):
        """Import custom dictionary from file"""
        with open(dictionary_path, 'r') as f:
            data = json.load(f)
            
        self.custom_dictionary = CustomDictionary(
            dictionary_id=data.get('dictionary_id', str(uuid.uuid4())),
            name=data.get('name', 'Imported Dictionary'),
            domain=data.get('domain', 'general'),
            terms=data.get('terms', {}),
            abbreviations=data.get('abbreviations', {}),
            created_at=datetime.fromisoformat(data.get('created_at', datetime.utcnow().isoformat())),
            updated_at=datetime.utcnow()
        )

# Usage example
async def demo_correction():
    """Demonstrate transcription correction"""
    
    # Create custom dictionary
    custom_dict = CustomDictionary(
        dictionary_id="tech_dict",
        name="Technology Dictionary",
        domain="technology",
        terms={},
        abbreviations={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Add technical terms
    custom_dict.add_term("kubernetes", "Container orchestration platform")
    custom_dict.add_term("docker", "Container platform")
    custom_dict.add_abbreviation("K8s", "Kubernetes")
    custom_dict.add_abbreviation("API", "Application Programming Interface")
    
    # Initialize correction system
    correction_system = TranscriptionCorrectionSystem(
        custom_dictionary=custom_dict,
        enable_learning=True
    )
    
    # Example transcription with errors
    transcription = """
    the kubernetis cluster is runing on amazone web servises. 
    we are using dokker containers with a REST AP interface. 
    the system processess about 10 GB of data evry hour.
    their are multiple microservices communicating threw message queues.
    """
    
    # Perform correction
    result = await correction_system.correct_transcription(
        transcription,
        confidence_threshold=0.6
    )
    
    print("Original text:")
    print(transcription)
    print("\nCorrected text:")
    print(result['corrected_text'])
    print(f"\nTotal corrections: {result['total_corrections']}")
    print(f"Overall confidence: {result['overall_confidence']:.2f}")
    
    # Show individual suggestions
    print("\nCorrection suggestions:")
    for suggestion in result['suggestions']:
        print(f"  - '{suggestion['original_text']}' -> '{suggestion['corrected_text']}'")
        print(f"    Type: {suggestion['correction_type']}, Confidence: {suggestion['confidence']:.2f}")
        print(f"    Reason: {suggestion['reason']}")
        
    # Simulate user feedback
    await correction_system.accept_correction(
        "kubernetis",
        "kubernetes",
        CorrectionType.SPELLING,
        transcription
    )
    
    # Get statistics
    stats = correction_system.get_statistics()
    print(f"\nStatistics: {json.dumps(stats, indent=2)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_correction())