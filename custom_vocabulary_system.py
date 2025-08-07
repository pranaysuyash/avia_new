"""
Custom Vocabulary and Domain Adaptation System

This module provides comprehensive custom vocabulary management with user-submitted,
verified, and validated vocabulary support for domain-specific and industry-specific
terminology. It includes pronunciation guides, phonetic transcriptions, and adaptive
learning capabilities.

Features:
- Domain-specific vocabulary management
- User-submitted vocabulary with verification workflow
- Custom pronunciation guides and phonetic transcriptions
- Vocabulary validation and quality control
- Industry-specific terminology databases
- Adaptive vocabulary learning from usage patterns
- Multi-language vocabulary support
- Vocabulary analytics and usage tracking
"""

import os
import json
import sqlite3
import hashlib
import re
from typing import Dict, List, Tuple, Optional, Any, Set, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging
from pathlib import Path
import unicodedata
import difflib

# Audio processing for pronunciation
import librosa
import soundfile as sf
import numpy as np

# NLP and text processing
import spacy
from textblob import TextBlob
import nltk
from nltk.corpus import cmudict
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag

# Machine learning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VocabularyStatus(Enum):
    """Status of vocabulary entries"""
    PENDING = "pending"
    VERIFIED = "verified"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"

class DomainCategory(Enum):
    """Domain categories for vocabulary"""
    MEDICAL = "medical"
    LEGAL = "legal"
    TECHNICAL = "technical"
    FINANCIAL = "financial"
    SCIENTIFIC = "scientific"
    ACADEMIC = "academic"
    BUSINESS = "business"
    MANUFACTURING = "manufacturing"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    GOVERNMENT = "government"
    MILITARY = "military"
    AVIATION = "aviation"
    MARITIME = "maritime"
    AUTOMOTIVE = "automotive"
    PHARMACEUTICAL = "pharmaceutical"
    BIOTECHNOLOGY = "biotechnology"
    TELECOMMUNICATIONS = "telecommunications"
    ENERGY = "energy"
    AGRICULTURE = "agriculture"
    GENERAL = "general"

@dataclass
class VocabularyEntry:
    """Vocabulary entry with comprehensive metadata"""
    id: str
    term: str
    definition: str
    pronunciation: str  # IPA or phonetic
    phonetic_spelling: str
    domain: DomainCategory
    language: str
    alternatives: List[str]
    context_examples: List[str]
    frequency_score: float
    confidence_score: float
    status: VocabularyStatus
    submitter_id: str
    verifier_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    usage_count: int
    accuracy_score: float
    tags: List[str]
    related_terms: List[str]
    audio_samples: List[str]  # Paths to audio files
    source_references: List[str]

@dataclass
class ValidationResult:
    """Result of vocabulary validation"""
    is_valid: bool
    confidence: float
    issues: List[str]
    suggestions: List[str]
    quality_score: float

@dataclass
class DomainAdaptationConfig:
    """Configuration for domain adaptation"""
    domain: DomainCategory
    vocabulary_weight: float
    context_sensitivity: float
    adaptation_threshold: float
    learning_rate: float
    max_vocabulary_size: int
    quality_threshold: float

class PhoneticTranscriber:
    """Advanced phonetic transcription system"""
    
    def __init__(self):
        self.cmu_dict = None
        self._load_phonetic_resources()
    
    def _load_phonetic_resources(self):
        """Load phonetic transcription resources"""
        try:
            # Download NLTK data if not present
            nltk.download('cmudict', quiet=True)
            nltk.download('punkt', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            
            self.cmu_dict = cmudict.dict()
            logger.info("Phonetic resources loaded successfully")
        except Exception as e:
            logger.error(f"Error loading phonetic resources: {e}")
            self.cmu_dict = {}
    
    def get_phonetic_transcription(self, word: str) -> Tuple[str, str]:
        """Get phonetic transcription for a word"""
        try:
            word_clean = word.lower().strip()
            
            # Try CMU dictionary first
            if self.cmu_dict and word_clean in self.cmu_dict:
                phonemes = self.cmu_dict[word_clean][0]  # Take first pronunciation
                ipa_transcription = self._arpabet_to_ipa(phonemes)
                phonetic_spelling = self._phonemes_to_spelling(phonemes)
                return ipa_transcription, phonetic_spelling
            
            # Fallback to rule-based transcription
            return self._rule_based_transcription(word)
            
        except Exception as e:
            logger.error(f"Error in phonetic transcription: {e}")
            return word, word
    
    def _arpabet_to_ipa(self, phonemes: List[str]) -> str:
        """Convert ARPAbet phonemes to IPA"""
        # Simplified ARPAbet to IPA mapping
        arpabet_to_ipa_map = {
            'AA': 'ɑ', 'AE': 'æ', 'AH': 'ʌ', 'AO': 'ɔ', 'AW': 'aʊ',
            'AY': 'aɪ', 'B': 'b', 'CH': 'tʃ', 'D': 'd', 'DH': 'ð',
            'EH': 'ɛ', 'ER': 'ɝ', 'EY': 'eɪ', 'F': 'f', 'G': 'g',
            'HH': 'h', 'IH': 'ɪ', 'IY': 'i', 'JH': 'dʒ', 'K': 'k',
            'L': 'l', 'M': 'm', 'N': 'n', 'NG': 'ŋ', 'OW': 'oʊ',
            'OY': 'ɔɪ', 'P': 'p', 'R': 'r', 'S': 's', 'SH': 'ʃ',
            'T': 't', 'TH': 'θ', 'UH': 'ʊ', 'UW': 'u', 'V': 'v',
            'W': 'w', 'Y': 'j', 'Z': 'z', 'ZH': 'ʒ'
        }
        
        ipa_symbols = []
        for phoneme in phonemes:
            # Remove stress markers
            clean_phoneme = re.sub(r'[0-9]', '', phoneme)
            ipa_symbol = arpabet_to_ipa_map.get(clean_phoneme, clean_phoneme.lower())
            ipa_symbols.append(ipa_symbol)
        
        return ''.join(ipa_symbols)
    
    def _phonemes_to_spelling(self, phonemes: List[str]) -> str:
        """Convert phonemes to phonetic spelling"""
        # Simplified phonetic spelling
        phonetic_map = {
            'AA': 'ah', 'AE': 'a', 'AH': 'uh', 'AO': 'aw', 'AW': 'ow',
            'AY': 'eye', 'B': 'b', 'CH': 'ch', 'D': 'd', 'DH': 'th',
            'EH': 'eh', 'ER': 'er', 'EY': 'ay', 'F': 'f', 'G': 'g',
            'HH': 'h', 'IH': 'ih', 'IY': 'ee', 'JH': 'j', 'K': 'k',
            'L': 'l', 'M': 'm', 'N': 'n', 'NG': 'ng', 'OW': 'oh',
            'OY': 'oy', 'P': 'p', 'R': 'r', 'S': 's', 'SH': 'sh',
            'T': 't', 'TH': 'th', 'UH': 'uh', 'UW': 'oo', 'V': 'v',
            'W': 'w', 'Y': 'y', 'Z': 'z', 'ZH': 'zh'
        }
        
        spelling_parts = []
        for phoneme in phonemes:
            clean_phoneme = re.sub(r'[0-9]', '', phoneme)
            spelling = phonetic_map.get(clean_phoneme, clean_phoneme.lower())
            spelling_parts.append(spelling)
        
        return '-'.join(spelling_parts)
    
    def _rule_based_transcription(self, word: str) -> Tuple[str, str]:
        """Rule-based phonetic transcription fallback"""
        # Very basic rule-based transcription
        # This is a simplified version - real implementation would be much more complex
        
        word_lower = word.lower()
        
        # Basic vowel mappings
        phonetic = word_lower
        phonetic = re.sub(r'ph', 'f', phonetic)
        phonetic = re.sub(r'gh', 'f', phonetic)
        phonetic = re.sub(r'tion', 'shun', phonetic)
        phonetic = re.sub(r'sion', 'zhun', phonetic)
        phonetic = re.sub(r'ch', 'ch', phonetic)
        phonetic = re.sub(r'sh', 'sh', phonetic)
        phonetic = re.sub(r'th', 'th', phonetic)
        
        # Simple IPA approximation
        ipa = phonetic
        ipa = re.sub(r'ee', 'i', ipa)
        ipa = re.sub(r'oo', 'u', ipa)
        ipa = re.sub(r'sh', 'ʃ', ipa)
        ipa = re.sub(r'ch', 'tʃ', ipa)
        ipa = re.sub(r'th', 'θ', ipa)
        
        return ipa, phonetic

class VocabularyValidator:
    """Advanced vocabulary validation system"""
    
    def __init__(self):
        self.transcriber = PhoneticTranscriber()
        self.nlp = self._load_nlp_model()
        self.quality_thresholds = {
            'min_definition_length': 10,
            'max_definition_length': 500,
            'min_term_length': 2,
            'max_term_length': 50,
            'min_examples': 1,
            'max_examples': 10
        }
    
    def _load_nlp_model(self):
        """Load spaCy NLP model"""
        try:
            return spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
            return None
    
    def validate_entry(self, entry: VocabularyEntry) -> ValidationResult:
        """Comprehensive validation of vocabulary entry"""
        issues = []
        suggestions = []
        quality_scores = []
        
        # Validate term
        term_score = self._validate_term(entry.term, issues, suggestions)
        quality_scores.append(term_score)
        
        # Validate definition
        definition_score = self._validate_definition(entry.definition, issues, suggestions)
        quality_scores.append(definition_score)
        
        # Validate pronunciation
        pronunciation_score = self._validate_pronunciation(entry.pronunciation, entry.term, issues, suggestions)
        quality_scores.append(pronunciation_score)
        
        # Validate context examples
        examples_score = self._validate_examples(entry.context_examples, entry.term, issues, suggestions)
        quality_scores.append(examples_score)
        
        # Validate domain consistency
        domain_score = self._validate_domain_consistency(entry, issues, suggestions)
        quality_scores.append(domain_score)
        
        # Calculate overall quality score
        quality_score = np.mean(quality_scores)
        
        # Determine if valid
        is_valid = len(issues) == 0 and quality_score >= 0.7
        confidence = min(quality_score, 1.0)
        
        return ValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            issues=issues,
            suggestions=suggestions,
            quality_score=quality_score
        )
    
    def _validate_term(self, term: str, issues: List[str], suggestions: List[str]) -> float:
        """Validate vocabulary term"""
        score = 1.0
        
        # Check length
        if len(term) < self.quality_thresholds['min_term_length']:
            issues.append(f"Term too short (minimum {self.quality_thresholds['min_term_length']} characters)")
            score -= 0.3
        
        if len(term) > self.quality_thresholds['max_term_length']:
            issues.append(f"Term too long (maximum {self.quality_thresholds['max_term_length']} characters)")
            score -= 0.2
        
        # Check for invalid characters
        if not re.match(r'^[a-zA-Z0-9\s\-\'\.]+$', term):
            issues.append("Term contains invalid characters")
            score -= 0.4
        
        # Check for proper capitalization
        if term.islower() and len(term) > 1:
            suggestions.append("Consider proper capitalization for the term")
            score -= 0.1
        
        return max(0, score)
    
    def _validate_definition(self, definition: str, issues: List[str], suggestions: List[str]) -> float:
        """Validate definition quality"""
        score = 1.0
        
        # Check length
        if len(definition) < self.quality_thresholds['min_definition_length']:
            issues.append(f"Definition too short (minimum {self.quality_thresholds['min_definition_length']} characters)")
            score -= 0.4
        
        if len(definition) > self.quality_thresholds['max_definition_length']:
            issues.append(f"Definition too long (maximum {self.quality_thresholds['max_definition_length']} characters)")
            score -= 0.2
        
        # Check for circular definition (term in definition)
        definition_lower = definition.lower()
        if any(word.lower() in definition_lower for word in definition.split() if len(word) > 3):
            suggestions.append("Avoid using the term itself in the definition")
            score -= 0.1
        
        # Check for completeness
        if not definition.strip().endswith('.'):
            suggestions.append("Definition should end with proper punctuation")
            score -= 0.05
        
        # Check readability using NLP
        if self.nlp:
            doc = self.nlp(definition)
            if len(list(doc.sents)) == 0:
                issues.append("Definition should contain at least one complete sentence")
                score -= 0.3
        
        return max(0, score)
    
    def _validate_pronunciation(self, pronunciation: str, term: str, issues: List[str], suggestions: List[str]) -> float:
        """Validate pronunciation guide"""
        score = 1.0
        
        if not pronunciation or pronunciation.strip() == "":
            # Try to generate pronunciation
            ipa, phonetic = self.transcriber.get_phonetic_transcription(term)
            suggestions.append(f"Suggested pronunciation: {ipa} ({phonetic})")
            score -= 0.2
        else:
            # Validate existing pronunciation
            if not re.match(r'^[a-zA-Z0-9\s\-\'\.ɑæʌɔaʊaɪbtʃdðɛɝeɪfghɪijdʒklmnŋoʊɔɪprsʃtθʊuvwjzʒ]+$', pronunciation):
                suggestions.append("Pronunciation contains unusual characters - please verify")
                score -= 0.1
        
        return max(0, score)
    
    def _validate_examples(self, examples: List[str], term: str, issues: List[str], suggestions: List[str]) -> float:
        """Validate context examples"""
        score = 1.0
        
        if len(examples) < self.quality_thresholds['min_examples']:
            issues.append(f"Need at least {self.quality_thresholds['min_examples']} context example(s)")
            score -= 0.3
        
        if len(examples) > self.quality_thresholds['max_examples']:
            suggestions.append(f"Consider reducing to {self.quality_thresholds['max_examples']} or fewer examples")
            score -= 0.1
        
        # Check if examples actually contain the term
        term_lower = term.lower()
        for i, example in enumerate(examples):
            if term_lower not in example.lower():
                suggestions.append(f"Example {i+1} should contain the term '{term}'")
                score -= 0.2
        
        return max(0, score)
    
    def _validate_domain_consistency(self, entry: VocabularyEntry, issues: List[str], suggestions: List[str]) -> float:
        """Validate domain consistency"""
        score = 1.0
        
        # Check if definition matches domain
        domain_keywords = self._get_domain_keywords(entry.domain)
        definition_lower = entry.definition.lower()
        
        keyword_matches = sum(1 for keyword in domain_keywords if keyword in definition_lower)
        if keyword_matches == 0:
            suggestions.append(f"Consider adding domain-specific context for {entry.domain.value}")
            score -= 0.1
        
        return max(0, score)
    
    def _get_domain_keywords(self, domain: DomainCategory) -> List[str]:
        """Get keywords associated with a domain"""
        domain_keywords = {
            DomainCategory.MEDICAL: ['medical', 'health', 'patient', 'treatment', 'diagnosis', 'clinical'],
            DomainCategory.LEGAL: ['legal', 'law', 'court', 'contract', 'attorney', 'litigation'],
            DomainCategory.TECHNICAL: ['technical', 'system', 'process', 'method', 'procedure', 'specification'],
            DomainCategory.FINANCIAL: ['financial', 'money', 'investment', 'banking', 'economic', 'fiscal'],
            DomainCategory.SCIENTIFIC: ['scientific', 'research', 'study', 'analysis', 'experiment', 'theory'],
            # Add more domain keywords as needed
        }
        
        return domain_keywords.get(domain, [])

class VocabularyDatabase:
    """Advanced vocabulary database with SQLite backend"""
    
    def __init__(self, db_path: str = "vocabulary.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database schema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Vocabulary entries table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS vocabulary_entries (
                        id TEXT PRIMARY KEY,
                        term TEXT NOT NULL,
                        definition TEXT NOT NULL,
                        pronunciation TEXT,
                        phonetic_spelling TEXT,
                        domain TEXT NOT NULL,
                        language TEXT DEFAULT 'en',
                        alternatives TEXT,  -- JSON array
                        context_examples TEXT,  -- JSON array
                        frequency_score REAL DEFAULT 0.0,
                        confidence_score REAL DEFAULT 0.0,
                        status TEXT DEFAULT 'pending',
                        submitter_id TEXT,
                        verifier_id TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        usage_count INTEGER DEFAULT 0,
                        accuracy_score REAL DEFAULT 0.0,
                        tags TEXT,  -- JSON array
                        related_terms TEXT,  -- JSON array
                        audio_samples TEXT,  -- JSON array
                        source_references TEXT  -- JSON array
                    )
                ''')
                
                # Vocabulary usage tracking
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS vocabulary_usage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        vocabulary_id TEXT,
                        user_id TEXT,
                        context TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        accuracy_feedback REAL,
                        FOREIGN KEY (vocabulary_id) REFERENCES vocabulary_entries (id)
                    )
                ''')
                
                # Domain configurations
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS domain_configs (
                        domain TEXT PRIMARY KEY,
                        config TEXT,  -- JSON configuration
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # User submissions and verification workflow
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS submission_workflow (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        vocabulary_id TEXT,
                        submitter_id TEXT,
                        verifier_id TEXT,
                        status TEXT,
                        submission_data TEXT,  -- JSON
                        verification_notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (vocabulary_id) REFERENCES vocabulary_entries (id)
                    )
                ''')
                
                # Create indexes for performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_term ON vocabulary_entries (term)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_domain ON vocabulary_entries (domain)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON vocabulary_entries (status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_language ON vocabulary_entries (language)')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def add_entry(self, entry: VocabularyEntry) -> bool:
        """Add vocabulary entry to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO vocabulary_entries (
                        id, term, definition, pronunciation, phonetic_spelling,
                        domain, language, alternatives, context_examples,
                        frequency_score, confidence_score, status, submitter_id,
                        verifier_id, created_at, updated_at, usage_count,
                        accuracy_score, tags, related_terms, audio_samples,
                        source_references
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    entry.id, entry.term, entry.definition, entry.pronunciation,
                    entry.phonetic_spelling, entry.domain.value, entry.language,
                    json.dumps(entry.alternatives), json.dumps(entry.context_examples),
                    entry.frequency_score, entry.confidence_score, entry.status.value,
                    entry.submitter_id, entry.verifier_id, entry.created_at.isoformat(),
                    entry.updated_at.isoformat(), entry.usage_count, entry.accuracy_score,
                    json.dumps(entry.tags), json.dumps(entry.related_terms),
                    json.dumps(entry.audio_samples), json.dumps(entry.source_references)
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error adding vocabulary entry: {e}")
            return False
    
    def get_entry(self, entry_id: str) -> Optional[VocabularyEntry]:
        """Get vocabulary entry by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM vocabulary_entries WHERE id = ?', (entry_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_entry(row)
                return None
                
        except Exception as e:
            logger.error(f"Error getting vocabulary entry: {e}")
            return None
    
    def search_entries(self, query: str, domain: Optional[DomainCategory] = None, 
                      status: Optional[VocabularyStatus] = None, limit: int = 50) -> List[VocabularyEntry]:
        """Search vocabulary entries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                sql = 'SELECT * FROM vocabulary_entries WHERE (term LIKE ? OR definition LIKE ?)'
                params = [f'%{query}%', f'%{query}%']
                
                if domain:
                    sql += ' AND domain = ?'
                    params.append(domain.value)
                
                if status:
                    sql += ' AND status = ?'
                    params.append(status.value)
                
                sql += ' ORDER BY frequency_score DESC, confidence_score DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                return [self._row_to_entry(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error searching vocabulary entries: {e}")
            return []
    
    def get_domain_vocabulary(self, domain: DomainCategory, status: VocabularyStatus = VocabularyStatus.APPROVED) -> List[VocabularyEntry]:
        """Get all vocabulary for a specific domain"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM vocabulary_entries WHERE domain = ? AND status = ? ORDER BY frequency_score DESC',
                    (domain.value, status.value)
                )
                rows = cursor.fetchall()
                
                return [self._row_to_entry(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting domain vocabulary: {e}")
            return []
    
    def update_usage(self, entry_id: str, user_id: str, context: str, accuracy_feedback: Optional[float] = None):
        """Update vocabulary usage statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Add usage record
                cursor.execute('''
                    INSERT INTO vocabulary_usage (vocabulary_id, user_id, context, accuracy_feedback)
                    VALUES (?, ?, ?, ?)
                ''', (entry_id, user_id, context, accuracy_feedback))
                
                # Update usage count
                cursor.execute('''
                    UPDATE vocabulary_entries 
                    SET usage_count = usage_count + 1, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (entry_id,))
                
                # Update accuracy score if feedback provided
                if accuracy_feedback is not None:
                    cursor.execute('''
                        UPDATE vocabulary_entries 
                        SET accuracy_score = (
                            SELECT AVG(accuracy_feedback) 
                            FROM vocabulary_usage 
                            WHERE vocabulary_id = ? AND accuracy_feedback IS NOT NULL
                        )
                        WHERE id = ?
                    ''', (entry_id, entry_id))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error updating vocabulary usage: {e}")
    
    def _row_to_entry(self, row) -> VocabularyEntry:
        """Convert database row to VocabularyEntry"""
        return VocabularyEntry(
            id=row[0],
            term=row[1],
            definition=row[2],
            pronunciation=row[3] or "",
            phonetic_spelling=row[4] or "",
            domain=DomainCategory(row[5]),
            language=row[6],
            alternatives=json.loads(row[7]) if row[7] else [],
            context_examples=json.loads(row[8]) if row[8] else [],
            frequency_score=row[9],
            confidence_score=row[10],
            status=VocabularyStatus(row[11]),
            submitter_id=row[12] or "",
            verifier_id=row[13],
            created_at=datetime.fromisoformat(row[14]),
            updated_at=datetime.fromisoformat(row[15]),
            usage_count=row[16],
            accuracy_score=row[17],
            tags=json.loads(row[18]) if row[18] else [],
            related_terms=json.loads(row[19]) if row[19] else [],
            audio_samples=json.loads(row[20]) if row[20] else [],
            source_references=json.loads(row[21]) if row[21] else []
        )

class DomainAdaptationEngine:
    """Advanced domain adaptation with machine learning"""
    
    def __init__(self, vocabulary_db: VocabularyDatabase):
        self.vocabulary_db = vocabulary_db
        self.vectorizer = TfidfVectorizer(max_features=10000, stop_words='english')
        self.domain_models = {}
        self.adaptation_configs = {}
    
    def configure_domain(self, domain: DomainCategory, config: DomainAdaptationConfig):
        """Configure domain adaptation parameters"""
        self.adaptation_configs[domain] = config
        
        # Save to database
        try:
            with sqlite3.connect(self.vocabulary_db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO domain_configs (domain, config, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (domain.value, json.dumps(asdict(config))))
                conn.commit()
        except Exception as e:
            logger.error(f"Error saving domain configuration: {e}")
    
    def adapt_vocabulary_for_domain(self, domain: DomainCategory, text_corpus: List[str]) -> List[str]:
        """Adapt vocabulary based on domain-specific text corpus"""
        try:
            # Get existing domain vocabulary
            existing_vocab = self.vocabulary_db.get_domain_vocabulary(domain)
            existing_terms = {entry.term.lower() for entry in existing_vocab}
            
            # Extract potential new terms from corpus
            potential_terms = self._extract_domain_terms(text_corpus, domain)
            
            # Filter out existing terms
            new_terms = [term for term in potential_terms if term.lower() not in existing_terms]
            
            # Score and rank new terms
            scored_terms = self._score_domain_terms(new_terms, text_corpus, domain)
            
            # Apply adaptation threshold
            config = self.adaptation_configs.get(domain, DomainAdaptationConfig(
                domain=domain,
                vocabulary_weight=1.0,
                context_sensitivity=0.5,
                adaptation_threshold=0.3,
                learning_rate=0.1,
                max_vocabulary_size=1000,
                quality_threshold=0.7
            ))
            
            adapted_terms = [
                term for term, score in scored_terms 
                if score >= config.adaptation_threshold
            ][:config.max_vocabulary_size]
            
            return adapted_terms
            
        except Exception as e:
            logger.error(f"Error in domain adaptation: {e}")
            return []
    
    def _extract_domain_terms(self, text_corpus: List[str], domain: DomainCategory) -> List[str]:
        """Extract potential domain-specific terms from text corpus"""
        try:
            # Combine all text
            combined_text = ' '.join(text_corpus)
            
            # Tokenize and extract candidate terms
            tokens = word_tokenize(combined_text.lower())
            pos_tags = pos_tag(tokens)
            
            # Filter for nouns, adjectives, and technical terms
            candidate_terms = []
            for token, pos in pos_tags:
                if (pos.startswith('NN') or pos.startswith('JJ')) and len(token) > 2:
                    if re.match(r'^[a-zA-Z][a-zA-Z0-9\-]*$', token):
                        candidate_terms.append(token)
            
            # Extract multi-word terms (bigrams, trigrams)
            words = combined_text.split()
            for i in range(len(words) - 1):
                bigram = f"{words[i]} {words[i+1]}"
                if self._is_valid_term(bigram):
                    candidate_terms.append(bigram)
            
            for i in range(len(words) - 2):
                trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
                if self._is_valid_term(trigram):
                    candidate_terms.append(trigram)
            
            # Remove duplicates and return
            return list(set(candidate_terms))
            
        except Exception as e:
            logger.error(f"Error extracting domain terms: {e}")
            return []
    
    def _score_domain_terms(self, terms: List[str], text_corpus: List[str], domain: DomainCategory) -> List[Tuple[str, float]]:
        """Score terms for domain relevance"""
        try:
            scored_terms = []
            
            for term in terms:
                # Calculate frequency score
                frequency_score = self._calculate_frequency_score(term, text_corpus)
                
                # Calculate domain relevance score
                domain_score = self._calculate_domain_relevance(term, domain)
                
                # Calculate uniqueness score
                uniqueness_score = self._calculate_uniqueness_score(term)
                
                # Combine scores
                final_score = (frequency_score * 0.4 + domain_score * 0.4 + uniqueness_score * 0.2)
                
                scored_terms.append((term, final_score))
            
            # Sort by score
            scored_terms.sort(key=lambda x: x[1], reverse=True)
            
            return scored_terms
            
        except Exception as e:
            logger.error(f"Error scoring domain terms: {e}")
            return []
    
    def _calculate_frequency_score(self, term: str, text_corpus: List[str]) -> float:
        """Calculate frequency-based score for term"""
        try:
            combined_text = ' '.join(text_corpus).lower()
            term_count = combined_text.count(term.lower())
            total_words = len(combined_text.split())
            
            if total_words == 0:
                return 0.0
            
            frequency = term_count / total_words
            # Normalize to 0-1 range
            return min(frequency * 1000, 1.0)
            
        except Exception:
            return 0.0
    
    def _calculate_domain_relevance(self, term: str, domain: DomainCategory) -> float:
        """Calculate domain relevance score"""
        try:
            # Get domain-specific keywords
            domain_keywords = {
                DomainCategory.MEDICAL: ['medical', 'clinical', 'patient', 'treatment', 'diagnosis', 'therapy', 'disease', 'symptom'],
                DomainCategory.LEGAL: ['legal', 'law', 'court', 'contract', 'attorney', 'litigation', 'statute', 'regulation'],
                DomainCategory.TECHNICAL: ['technical', 'system', 'process', 'method', 'procedure', 'specification', 'protocol', 'algorithm'],
                DomainCategory.FINANCIAL: ['financial', 'investment', 'banking', 'economic', 'fiscal', 'revenue', 'profit', 'asset'],
                DomainCategory.SCIENTIFIC: ['research', 'study', 'analysis', 'experiment', 'theory', 'hypothesis', 'data', 'methodology'],
            }
            
            keywords = domain_keywords.get(domain, [])
            
            # Check if term contains domain keywords
            term_lower = term.lower()
            relevance_score = 0.0
            
            for keyword in keywords:
                if keyword in term_lower:
                    relevance_score += 0.2
            
            # Check for domain-specific patterns
            if domain == DomainCategory.MEDICAL:
                if re.search(r'(itis|osis|emia|pathy|ology)$', term_lower):
                    relevance_score += 0.3
            elif domain == DomainCategory.TECHNICAL:
                if re.search(r'(tech|system|process|method)$', term_lower):
                    relevance_score += 0.3
            
            return min(relevance_score, 1.0)
            
        except Exception:
            return 0.0
    
    def _calculate_uniqueness_score(self, term: str) -> float:
        """Calculate uniqueness score (inverse of commonality)"""
        try:
            # Simple heuristic: longer terms and terms with specific patterns are more unique
            length_score = min(len(term) / 20, 1.0)
            
            # Check for technical patterns
            pattern_score = 0.0
            if re.search(r'[A-Z]{2,}', term):  # Acronyms
                pattern_score += 0.3
            if re.search(r'\d', term):  # Contains numbers
                pattern_score += 0.2
            if '-' in term:  # Hyphenated terms
                pattern_score += 0.1
            
            return min(length_score + pattern_score, 1.0)
            
        except Exception:
            return 0.0
    
    def _is_valid_term(self, term: str) -> bool:
        """Check if term is valid for vocabulary"""
        # Basic validation
        if len(term) < 3 or len(term) > 50:
            return False
        
        # Must contain at least one letter
        if not re.search(r'[a-zA-Z]', term):
            return False
        
        # Avoid common stop words in multi-word terms
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = term.lower().split()
        if len(words) > 1 and any(word in stop_words for word in words):
            return False
        
        return True

class UserSubmissionWorkflow:
    """Workflow for user-submitted vocabulary with verification"""
    
    def __init__(self, vocabulary_db: VocabularyDatabase, validator: VocabularyValidator):
        self.vocabulary_db = vocabulary_db
        self.validator = validator
        self.transcriber = PhoneticTranscriber()
    
    def submit_vocabulary(self, term: str, definition: str, domain: DomainCategory,
                         submitter_id: str, context_examples: List[str] = None,
                         pronunciation: str = None, alternatives: List[str] = None,
                         tags: List[str] = None, source_references: List[str] = None) -> Tuple[bool, str, VocabularyEntry]:
        """Submit new vocabulary for verification"""
        try:
            # Generate ID
            entry_id = hashlib.md5(f"{term}_{domain.value}_{submitter_id}".encode()).hexdigest()
            
            # Generate pronunciation if not provided
            if not pronunciation:
                ipa, phonetic = self.transcriber.get_phonetic_transcription(term)
                pronunciation = ipa
                phonetic_spelling = phonetic
            else:
                phonetic_spelling = pronunciation
            
            # Create vocabulary entry
            entry = VocabularyEntry(
                id=entry_id,
                term=term.strip(),
                definition=definition.strip(),
                pronunciation=pronunciation,
                phonetic_spelling=phonetic_spelling,
                domain=domain,
                language="en",
                alternatives=alternatives or [],
                context_examples=context_examples or [],
                frequency_score=0.0,
                confidence_score=0.0,
                status=VocabularyStatus.PENDING,
                submitter_id=submitter_id,
                verifier_id=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                usage_count=0,
                accuracy_score=0.0,
                tags=tags or [],
                related_terms=[],
                audio_samples=[],
                source_references=source_references or []
            )
            
            # Validate entry
            validation_result = self.validator.validate_entry(entry)
            
            if not validation_result.is_valid:
                return False, f"Validation failed: {'; '.join(validation_result.issues)}", entry
            
            # Update confidence score from validation
            entry.confidence_score = validation_result.confidence
            
            # Add to database
            success = self.vocabulary_db.add_entry(entry)
            
            if success:
                # Add to submission workflow
                self._add_to_workflow(entry, validation_result)
                return True, "Vocabulary submitted successfully for verification", asdict(entry)
            else:
                return False, "Failed to save vocabulary entry", asdict(entry)
                
        except Exception as e:
            logger.error(f"Error submitting vocabulary: {e}")
            return False, f"Submission error: {str(e)}", None
    
    def verify_submission(self, entry_id: str, verifier_id: str, 
                         approved: bool, notes: str = "") -> bool:
        """Verify submitted vocabulary"""
        try:
            with sqlite3.connect(self.vocabulary_db.db_path) as conn:
                cursor = conn.cursor()
                
                # Update entry status
                new_status = VocabularyStatus.APPROVED if approved else VocabularyStatus.REJECTED
                cursor.execute('''
                    UPDATE vocabulary_entries 
                    SET status = ?, verifier_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (new_status.value, verifier_id, entry_id))
                
                # Update workflow
                cursor.execute('''
                    UPDATE submission_workflow 
                    SET verifier_id = ?, status = ?, verification_notes = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE vocabulary_id = ?
                ''', (verifier_id, new_status.value, notes, entry_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error verifying submission: {e}")
            return False
    
    def get_pending_submissions(self, verifier_id: str = None) -> List[VocabularyEntry]:
        """Get pending vocabulary submissions"""
        return self.vocabulary_db.search_entries("", status=VocabularyStatus.PENDING)
    
    def _add_to_workflow(self, entry: VocabularyEntry, validation_result: ValidationResult):
        """Add entry to submission workflow"""
        try:
            with sqlite3.connect(self.vocabulary_db.db_path) as conn:
                cursor = conn.cursor()
                
                # Convert validation result to JSON-serializable format
                validation_dict = asdict(validation_result)
                # Handle numpy types
                for key, value in validation_dict.items():
                    if hasattr(value, 'item'):  # numpy scalar
                        validation_dict[key] = value.item()
                    elif isinstance(value, list):
                        validation_dict[key] = [v.item() if hasattr(v, 'item') else v for v in value]
                
                workflow_data = {
                    'validation_result': validation_dict,
                    'submission_timestamp': entry.created_at.isoformat()
                }
                
                cursor.execute('''
                    INSERT INTO submission_workflow (
                        vocabulary_id, submitter_id, status, submission_data
                    ) VALUES (?, ?, ?, ?)
                ''', (
                    entry.id, entry.submitter_id, entry.status.value,
                    json.dumps(workflow_data)
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error adding to workflow: {e}")

class CustomVocabularySystem:
    """Main custom vocabulary and domain adaptation system"""
    
    def __init__(self, db_path: str = "vocabulary.db"):
        self.vocabulary_db = VocabularyDatabase(db_path)
        self.validator = VocabularyValidator()
        self.adaptation_engine = DomainAdaptationEngine(self.vocabulary_db)
        self.submission_workflow = UserSubmissionWorkflow(self.vocabulary_db, self.validator)
        self.transcriber = PhoneticTranscriber()
    
    def submit_vocabulary(self, term: str, definition: str, domain: str,
                         submitter_id: str, **kwargs) -> Tuple[bool, str, Optional[VocabularyEntry]]:
        """Submit new vocabulary entry"""
        try:
            domain_enum = DomainCategory(domain.lower())
            return self.submission_workflow.submit_vocabulary(
                term, definition, domain_enum, submitter_id, **kwargs
            )
        except ValueError:
            return False, f"Invalid domain: {domain}", None
    
    def verify_vocabulary(self, entry_id: str, verifier_id: str, 
                         approved: bool, notes: str = "") -> bool:
        """Verify submitted vocabulary"""
        return self.submission_workflow.verify_submission(entry_id, verifier_id, approved, notes)
    
    def search_vocabulary(self, query: str, domain: str = None, 
                         status: str = "approved") -> List[Dict[str, Any]]:
        """Search vocabulary entries"""
        domain_enum = DomainCategory(domain.lower()) if domain else None
        status_enum = VocabularyStatus(status.lower()) if status else None
        
        entries = self.vocabulary_db.search_entries(query, domain_enum, status_enum)
        return [asdict(entry) for entry in entries]
    
    def get_domain_vocabulary(self, domain: str) -> List[Dict[str, Any]]:
        """Get all approved vocabulary for a domain"""
        domain_enum = DomainCategory(domain.lower())
        entries = self.vocabulary_db.get_domain_vocabulary(domain_enum)
        return [asdict(entry) for entry in entries]
    
    def adapt_domain_vocabulary(self, domain: str, text_corpus: List[str]) -> List[str]:
        """Adapt vocabulary for domain based on text corpus"""
        domain_enum = DomainCategory(domain.lower())
        return self.adaptation_engine.adapt_vocabulary_for_domain(domain_enum, text_corpus)
    
    def get_pronunciation(self, term: str) -> Tuple[str, str]:
        """Get pronunciation for a term"""
        return self.transcriber.get_phonetic_transcription(term)
    
    def get_pending_submissions(self) -> List[Dict[str, Any]]:
        """Get pending vocabulary submissions"""
        entries = self.submission_workflow.get_pending_submissions()
        return [asdict(entry) for entry in entries]
    
    def update_vocabulary_usage(self, entry_id: str, user_id: str, 
                               context: str, accuracy_feedback: float = None):
        """Update vocabulary usage statistics"""
        self.vocabulary_db.update_usage(entry_id, user_id, context, accuracy_feedback)
    
    def get_vocabulary_analytics(self, domain: str = None) -> Dict[str, Any]:
        """Get vocabulary analytics"""
        try:
            with sqlite3.connect(self.vocabulary_db.db_path) as conn:
                cursor = conn.cursor()
                
                # Basic statistics
                if domain:
                    cursor.execute('SELECT COUNT(*) FROM vocabulary_entries WHERE domain = ?', (domain,))
                else:
                    cursor.execute('SELECT COUNT(*) FROM vocabulary_entries')
                total_entries = cursor.fetchone()[0]
                
                # Status distribution
                if domain:
                    cursor.execute('''
                        SELECT status, COUNT(*) FROM vocabulary_entries 
                        WHERE domain = ? GROUP BY status
                    ''', (domain,))
                else:
                    cursor.execute('SELECT status, COUNT(*) FROM vocabulary_entries GROUP BY status')
                status_dist = dict(cursor.fetchall())
                
                # Top domains
                cursor.execute('''
                    SELECT domain, COUNT(*) FROM vocabulary_entries 
                    GROUP BY domain ORDER BY COUNT(*) DESC LIMIT 10
                ''')
                top_domains = dict(cursor.fetchall())
                
                # Usage statistics
                cursor.execute('''
                    SELECT AVG(usage_count), AVG(accuracy_score) 
                    FROM vocabulary_entries WHERE usage_count > 0
                ''')
                usage_stats = cursor.fetchone()
                
                return {
                    'total_entries': total_entries,
                    'status_distribution': status_dist,
                    'top_domains': top_domains,
                    'average_usage_count': usage_stats[0] or 0,
                    'average_accuracy_score': usage_stats[1] or 0,
                    'domain_filter': domain
                }
                
        except Exception as e:
            logger.error(f"Error getting vocabulary analytics: {e}")
            return {}

# Example usage and testing
if __name__ == "__main__":
    # Initialize the system
    vocab_system = CustomVocabularySystem()
    
    # Example vocabulary submission
    success, message, entry = vocab_system.submit_vocabulary(
        term="Myocardial Infarction",
        definition="A heart attack caused by blocked blood flow to the heart muscle, resulting in tissue death.",
        domain="medical",
        submitter_id="user123",
        context_examples=[
            "The patient was diagnosed with acute myocardial infarction.",
            "Myocardial infarction is a leading cause of death worldwide."
        ],
        alternatives=["Heart Attack", "MI"],
        tags=["cardiology", "emergency", "diagnosis"]
    )
    
    print(f"Submission result: {success} - {message}")
    
    if success and entry:
        print(f"Entry ID: {entry.id}")
        print(f"Pronunciation: {entry.pronunciation} ({entry.phonetic_spelling})")
    
    print("Custom Vocabulary System initialized successfully!")
    print("Available features:")
    print("- User-submitted vocabulary with verification workflow")
    print("- Domain-specific vocabulary management")
    print("- Phonetic transcription and pronunciation guides")
    print("- Vocabulary validation and quality control")
    print("- Domain adaptation with machine learning")
    print("- Usage tracking and analytics")