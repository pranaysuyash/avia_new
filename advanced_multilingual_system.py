#!/usr/bin/env python3
"""
Advanced Multilingual Support System
Task 126: Comprehensive multilingual processing with code-switching detection,
dialect recognition, and cultural adaptation.
"""

import asyncio
import json
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set
import hashlib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Language(Enum):
    """Supported languages with ISO codes."""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"
    RUSSIAN = "ru"
    ARABIC = "ar"
    HINDI = "hi"
    DUTCH = "nl"
    SWEDISH = "sv"
    NORWEGIAN = "no"

class Dialect(Enum):
    """Regional dialect variations."""
    # Spanish
    SPANISH_SPAIN = "es-ES"
    SPANISH_MEXICO = "es-MX" 
    SPANISH_ARGENTINA = "es-AR"
    # English
    ENGLISH_US = "en-US"
    ENGLISH_UK = "en-GB"
    ENGLISH_AU = "en-AU"
    ENGLISH_CA = "en-CA"
    # French
    FRENCH_FRANCE = "fr-FR"
    FRENCH_CANADA = "fr-CA"
    FRENCH_BELGIUM = "fr-BE"
    # Portuguese
    PORTUGUESE_BRAZIL = "pt-BR"
    PORTUGUESE_PORTUGAL = "pt-PT"
    # Chinese
    CHINESE_SIMPLIFIED = "zh-CN"
    CHINESE_TRADITIONAL = "zh-TW"

class CodeSwitchType(Enum):
    """Types of code-switching patterns."""
    INTRA_SENTENTIAL = "intra_sentential"  # Within sentence
    INTER_SENTENTIAL = "inter_sentential"  # Between sentences
    TAG_SWITCHING = "tag_switching"        # Single words/phrases
    EMBLEMATIC = "emblematic"              # Cultural expressions
    CONTEXTUAL = "contextual"              # Context-driven

@dataclass
class LanguageSegment:
    """A text segment with language information."""
    text: str
    language: Language
    dialect: Optional[Dialect] = None
    confidence: float = 0.0
    start_pos: int = 0
    end_pos: int = 0
    features: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CodeSwitchEvent:
    """A detected code-switching event."""
    from_language: Language
    to_language: Language
    switch_type: CodeSwitchType
    position: int
    context_before: str
    context_after: str
    confidence: float
    trigger_type: str  # social, lexical, structural, etc.

@dataclass
class MultilingualAnalysis:
    """Complete multilingual analysis result."""
    text: str
    primary_language: Language
    detected_languages: List[Language]
    language_segments: List[LanguageSegment]
    code_switch_events: List[CodeSwitchEvent]
    dialect_analysis: Dict[Language, List[Dialect]]
    complexity_score: float
    cultural_markers: List[str]
    processing_metadata: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class LanguageDetector:
    """Advanced language detection with dialect support."""
    
    def __init__(self):
        self.language_patterns = self._initialize_patterns()
        self.dialect_markers = self._initialize_dialect_markers()
        
    def _initialize_patterns(self) -> Dict[Language, Dict[str, List[str]]]:
        """Initialize language detection patterns."""
        return {
            Language.ENGLISH: {
                'common_words': ['the', 'and', 'to', 'a', 'of', 'in', 'that', 'have', 'for', 'not'],
                'patterns': [r'\b(the|and|to|a|of|in|that|have|for|not)\b'],
                'character_sets': ['latin']
            },
            Language.SPANISH: {
                'common_words': ['el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se'],
                'patterns': [r'\b(el|la|de|que|y|a|en|un|es|se)\b', r'[ñáéíóúü]'],
                'character_sets': ['latin', 'spanish_accents']
            },
            Language.FRENCH: {
                'common_words': ['le', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir'],
                'patterns': [r'\b(le|de|et|à|un|il|être|et|en|avoir)\b', r'[àâäçéèêëïîôöùûüÿ]'],
                'character_sets': ['latin', 'french_accents']
            },
            Language.GERMAN: {
                'common_words': ['der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'sich'],
                'patterns': [r'\b(der|die|und|in|den|von|zu|das|mit|sich)\b', r'[äöüß]'],
                'character_sets': ['latin', 'german_special']
            },
            Language.CHINESE: {
                'common_words': ['的', '一', '是', '在', '不', '了', '有', '和', '人', '这'],
                'patterns': [r'[\u4e00-\u9fff]+'],
                'character_sets': ['chinese']
            }
        }
    
    def _initialize_dialect_markers(self) -> Dict[Dialect, Dict[str, List[str]]]:
        """Initialize dialect-specific markers."""
        return {
            Dialect.ENGLISH_US: {
                'vocabulary': ['color', 'center', 'neighbor', 'analyze', 'tire'],
                'expressions': ['you guys', 'awesome', 'totally']
            },
            Dialect.ENGLISH_UK: {
                'vocabulary': ['colour', 'centre', 'neighbour', 'analyse', 'tyre'],
                'expressions': ['brilliant', 'cheers', 'proper']
            },
            Dialect.SPANISH_MEXICO: {
                'vocabulary': ['ahorita', 'chamaco', 'padre', 'órale'],
                'expressions': ['¿qué onda?', 'está padrísimo']
            },
            Dialect.SPANISH_SPAIN: {
                'vocabulary': ['tío', 'guay', 'vale', 'joder'],
                'expressions': ['¿qué tal?', 'está fenomenal']
            },
            Dialect.PORTUGUESE_BRAZIL: {
                'vocabulary': ['ônibus', 'celular', 'abacaxi', 'saudade'],
                'expressions': ['tá bom', 'que legal']
            }
        }
    
    def detect_language_segments(self, text: str) -> List[LanguageSegment]:
        """Detect language for each segment of text."""
        segments = []
        sentences = self._split_sentences(text)
        position = 0
        
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            language, confidence, features = self._detect_sentence_language(sentence)
            dialect = self._detect_dialect(sentence, language)
            
            segment = LanguageSegment(
                text=sentence,
                language=language,
                dialect=dialect,
                confidence=confidence,
                start_pos=position,
                end_pos=position + len(sentence),
                features=features
            )
            segments.append(segment)
            position += len(sentence) + 1  # Account for separators
        
        return segments
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences handling multiple languages."""
        # Enhanced sentence splitting for multilingual text
        patterns = [
            r'[.!?]+\s+',  # Standard punctuation
            r'[。！？]+\s*',  # Chinese punctuation
            r'[।॥]+\s*',  # Hindi punctuation
            r'[؟!.]+\s*'   # Arabic punctuation
        ]
        
        sentences = [text]
        for pattern in patterns:
            new_sentences = []
            for sentence in sentences:
                new_sentences.extend(re.split(pattern, sentence))
            sentences = new_sentences
        
        return [s.strip() for s in sentences if s.strip()]
    
    def _detect_sentence_language(self, sentence: str) -> Tuple[Language, float, Dict[str, Any]]:
        """Detect language for a single sentence."""
        scores = {}
        features = {}
        
        sentence_lower = sentence.lower()
        
        for language, patterns in self.language_patterns.items():
            score = 0.0
            matched_features = []
            
            # Check common words
            for word in patterns['common_words']:
                if word in sentence_lower:
                    score += 2.0
                    matched_features.append(f"common_word_{word}")
            
            # Check regex patterns
            for pattern in patterns['patterns']:
                matches = re.findall(pattern, sentence_lower, re.IGNORECASE)
                score += len(matches) * 1.5
                if matches:
                    matched_features.extend([f"pattern_{m}" for m in matches[:3]])
            
            # Character set analysis
            if language == Language.CHINESE:
                chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', sentence))
                score += chinese_chars * 3.0
                matched_features.append(f"chinese_chars_{chinese_chars}")
            
            scores[language] = score
            features[language.value] = matched_features
        
        # Normalize scores
        max_score = max(scores.values()) if scores.values() else 0
        if max_score > 0:
            best_language = max(scores, key=scores.get)
            confidence = min(scores[best_language] / (len(sentence.split()) + 1), 1.0)
        else:
            best_language = Language.ENGLISH  # Default
            confidence = 0.1
        
        return best_language, confidence, features
    
    def _detect_dialect(self, text: str, language: Language) -> Optional[Dialect]:
        """Detect dialect within a language."""
        text_lower = text.lower()
        best_dialect = None
        best_score = 0
        
        # Get relevant dialects for this language
        relevant_dialects = [d for d in Dialect if d.value.startswith(language.value)]
        
        for dialect in relevant_dialects:
            if dialect not in self.dialect_markers:
                continue
            
            score = 0
            markers = self.dialect_markers[dialect]
            
            # Check vocabulary markers
            for word in markers.get('vocabulary', []):
                if word.lower() in text_lower:
                    score += 2
            
            # Check expressions
            for expression in markers.get('expressions', []):
                if expression.lower() in text_lower:
                    score += 3
            
            if score > best_score:
                best_score = score
                best_dialect = dialect
        
        return best_dialect if best_score > 0 else None

class CodeSwitchDetector:
    """Detect and analyze code-switching patterns."""
    
    def __init__(self, language_detector: LanguageDetector):
        self.language_detector = language_detector
        self.switch_patterns = self._initialize_switch_patterns()
    
    def _initialize_switch_patterns(self) -> Dict[str, List[str]]:
        """Initialize code-switching detection patterns."""
        return {
            'social_triggers': [
                'you know', 'como se dice', 'how do you say',
                'en español', 'in english', 'or rather'
            ],
            'discourse_markers': [
                'pero', 'but', 'and', 'y', 'so', 'entonces',
                'because', 'porque', 'like', 'como'
            ],
            'quotative_markers': [
                'he said', 'she said', 'dijo', 'dice',
                'told me', 'me dijo'
            ]
        }
    
    def detect_code_switches(self, segments: List[LanguageSegment]) -> List[CodeSwitchEvent]:
        """Detect code-switching events between language segments."""
        events = []
        
        for i in range(1, len(segments)):
            current = segments[i]
            previous = segments[i-1]
            
            if current.language != previous.language:
                switch_type = self._classify_switch_type(previous, current, segments, i)
                trigger_type = self._identify_trigger(previous, current)
                
                event = CodeSwitchEvent(
                    from_language=previous.language,
                    to_language=current.language,
                    switch_type=switch_type,
                    position=current.start_pos,
                    context_before=previous.text[-50:] if len(previous.text) > 50 else previous.text,
                    context_after=current.text[:50] if len(current.text) > 50 else current.text,
                    confidence=min(current.confidence, previous.confidence),
                    trigger_type=trigger_type
                )
                events.append(event)
        
        return events
    
    def _classify_switch_type(self, prev_segment: LanguageSegment, 
                            curr_segment: LanguageSegment,
                            all_segments: List[LanguageSegment], 
                            position: int) -> CodeSwitchType:
        """Classify the type of code-switching."""
        
        # Check for tag switching (single words/short phrases)
        if len(curr_segment.text.split()) <= 3:
            return CodeSwitchType.TAG_SWITCHING
        
        # Check for emblematic switching (cultural expressions)
        cultural_expressions = [
            'gracias', 'de nada', 'por favor', 'oui', 'non',
            'danke', 'bitte', 'arigato', 'konnichiwa'
        ]
        if any(expr in curr_segment.text.lower() for expr in cultural_expressions):
            return CodeSwitchType.EMBLEMATIC
        
        # Inter-sentential if switching between complete sentences
        if prev_segment.text.strip().endswith(('.', '!', '?')):
            return CodeSwitchType.INTER_SENTENTIAL
        
        # Default to intra-sentential
        return CodeSwitchType.INTRA_SENTENTIAL
    
    def _identify_trigger(self, prev_segment: LanguageSegment, 
                         curr_segment: LanguageSegment) -> str:
        """Identify what triggered the code-switch."""
        
        combined_text = (prev_segment.text + " " + curr_segment.text).lower()
        
        # Check for social triggers
        for trigger in self.switch_patterns['social_triggers']:
            if trigger in combined_text:
                return 'social'
        
        # Check for discourse markers
        for marker in self.switch_patterns['discourse_markers']:
            if marker in combined_text:
                return 'discourse'
        
        # Check for quotative markers
        for marker in self.switch_patterns['quotative_markers']:
            if marker in combined_text:
                return 'quotative'
        
        return 'lexical'

class CulturalAnalyzer:
    """Analyze cultural context and markers in multilingual text."""
    
    def __init__(self):
        self.cultural_markers = self._initialize_cultural_markers()
        self.cultural_contexts = self._initialize_cultural_contexts()
    
    def _initialize_cultural_markers(self) -> Dict[str, List[str]]:
        """Initialize cultural marker patterns."""
        return {
            'greeting_patterns': [
                'hello', 'hi', 'hola', 'bonjour', 'guten tag', 'konnichiwa',
                'namaste', 'shalom', 'salaam', 'ciao'
            ],
            'courtesy_expressions': [
                'please', 'thank you', 'por favor', 's\'il vous plaît',
                'bitte', 'arigato', 'gracias', 'merci', 'danke'
            ],
            'time_expressions': [
                'morning', 'afternoon', 'evening', 'mañana', 'tarde',
                'noche', 'matin', 'soir', 'morgen', 'abend'
            ],
            'cultural_concepts': [
                'family', 'familia', 'famille', 'familie',
                'respect', 'respeto', 'respect', 'respekt',
                'tradition', 'tradición', 'tradition', 'tradition'
            ]
        }
    
    def _initialize_cultural_contexts(self) -> Dict[Language, Dict[str, Any]]:
        """Initialize cultural context information."""
        return {
            Language.SPANISH: {
                'formality_markers': ['usted', 'señor', 'señora', 'don', 'doña'],
                'regional_variants': {
                    'vosotros': 'Spain',
                    'ustedes': 'Latin America',
                    'vos': 'Argentina/Uruguay'
                }
            },
            Language.FRENCH: {
                'formality_markers': ['vous', 'monsieur', 'madame', 'mademoiselle'],
                'regional_variants': {
                    'chocolatine': 'Southwest France',
                    'pain au chocolat': 'Standard French'
                }
            },
            Language.GERMAN: {
                'formality_markers': ['Sie', 'Herr', 'Frau', 'sehr geehrte'],
                'regional_variants': {
                    'grüß gott': 'Bavaria/Austria',
                    'moin': 'Northern Germany'
                }
            }
        }
    
    def analyze_cultural_markers(self, text: str, 
                               detected_languages: List[Language]) -> List[str]:
        """Identify cultural markers in the text."""
        markers = []
        text_lower = text.lower()
        
        # Check general cultural patterns
        for category, patterns in self.cultural_markers.items():
            for pattern in patterns:
                if pattern in text_lower:
                    markers.append(f"{category}:{pattern}")
        
        # Check language-specific cultural contexts
        for language in detected_languages:
            if language in self.cultural_contexts:
                context = self.cultural_contexts[language]
                
                # Check formality markers
                for marker in context.get('formality_markers', []):
                    if marker.lower() in text_lower:
                        markers.append(f"formality:{marker}")
                
                # Check regional variants
                for variant, region in context.get('regional_variants', {}).items():
                    if variant.lower() in text_lower:
                        markers.append(f"regional:{variant}:{region}")
        
        return markers

class MultilingualDatabase:
    """SQLite database for storing multilingual analysis results."""
    
    def __init__(self, db_path: str = "multilingual_analysis.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Main analysis table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS multilingual_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text_hash TEXT UNIQUE,
                    primary_language TEXT,
                    detected_languages TEXT,
                    complexity_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Language segments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS language_segments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id INTEGER,
                    text_segment TEXT,
                    language TEXT,
                    dialect TEXT,
                    confidence REAL,
                    start_pos INTEGER,
                    end_pos INTEGER,
                    FOREIGN KEY (analysis_id) REFERENCES multilingual_analyses (id)
                )
            """)
            
            # Code-switching events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS code_switch_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id INTEGER,
                    from_language TEXT,
                    to_language TEXT,
                    switch_type TEXT,
                    position INTEGER,
                    confidence REAL,
                    trigger_type TEXT,
                    FOREIGN KEY (analysis_id) REFERENCES multilingual_analyses (id)
                )
            """)
            
            conn.commit()
    
    def store_analysis(self, analysis: MultilingualAnalysis) -> int:
        """Store analysis results in database."""
        text_hash = hashlib.sha256(analysis.text.encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Store main analysis
            cursor.execute("""
                INSERT OR REPLACE INTO multilingual_analyses 
                (text_hash, primary_language, detected_languages, complexity_score)
                VALUES (?, ?, ?, ?)
            """, (
                text_hash,
                analysis.primary_language.value,
                json.dumps([lang.value for lang in analysis.detected_languages]),
                analysis.complexity_score
            ))
            
            analysis_id = cursor.lastrowid
            
            # Store language segments
            for segment in analysis.language_segments:
                cursor.execute("""
                    INSERT INTO language_segments 
                    (analysis_id, text_segment, language, dialect, confidence, start_pos, end_pos)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    analysis_id,
                    segment.text,
                    segment.language.value,
                    segment.dialect.value if segment.dialect else None,
                    segment.confidence,
                    segment.start_pos,
                    segment.end_pos
                ))
            
            # Store code-switching events
            for event in analysis.code_switch_events:
                cursor.execute("""
                    INSERT INTO code_switch_events 
                    (analysis_id, from_language, to_language, switch_type, position, confidence, trigger_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    analysis_id,
                    event.from_language.value,
                    event.to_language.value,
                    event.switch_type.value,
                    event.position,
                    event.confidence,
                    event.trigger_type
                ))
            
            conn.commit()
            return analysis_id
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get multilingual analysis statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total analyses
            cursor.execute("SELECT COUNT(*) FROM multilingual_analyses")
            total_analyses = cursor.fetchone()[0]
            
            # Language distribution
            cursor.execute("""
                SELECT primary_language, COUNT(*) 
                FROM multilingual_analyses 
                GROUP BY primary_language 
                ORDER BY COUNT(*) DESC
            """)
            language_distribution = cursor.fetchall()
            
            # Code-switching statistics
            cursor.execute("""
                SELECT switch_type, COUNT(*) 
                FROM code_switch_events 
                GROUP BY switch_type
            """)
            switch_type_stats = cursor.fetchall()
            
            # Average complexity
            cursor.execute("SELECT AVG(complexity_score) FROM multilingual_analyses")
            avg_complexity = cursor.fetchone()[0] or 0
            
            return {
                'total_analyses': total_analyses,
                'language_distribution': language_distribution,
                'switch_type_statistics': switch_type_stats,
                'average_complexity': avg_complexity
            }

class AdvancedMultilingualSystem:
    """Main system for advanced multilingual processing."""
    
    def __init__(self, db_path: str = "multilingual_analysis.db"):
        self.language_detector = LanguageDetector()
        self.code_switch_detector = CodeSwitchDetector(self.language_detector)
        self.cultural_analyzer = CulturalAnalyzer()
        self.database = MultilingualDatabase(db_path)
        
        logger.info("Advanced Multilingual System initialized")
    
    async def analyze_text(self, text: str) -> MultilingualAnalysis:
        """Perform comprehensive multilingual analysis."""
        try:
            logger.info(f"Analyzing text: {text[:50]}...")
            
            # 1. Language detection and segmentation
            language_segments = self.language_detector.detect_language_segments(text)
            
            # 2. Determine primary language and all detected languages
            primary_language = self._determine_primary_language(language_segments)
            detected_languages = list(set(segment.language for segment in language_segments))
            
            # 3. Code-switching detection
            code_switch_events = self.code_switch_detector.detect_code_switches(language_segments)
            
            # 4. Dialect analysis
            dialect_analysis = self._analyze_dialects(language_segments)
            
            # 5. Cultural marker analysis
            cultural_markers = self.cultural_analyzer.analyze_cultural_markers(text, detected_languages)
            
            # 6. Complexity scoring
            complexity_score = self._calculate_complexity(
                language_segments, code_switch_events, detected_languages
            )
            
            # 7. Create analysis result
            analysis = MultilingualAnalysis(
                text=text,
                primary_language=primary_language,
                detected_languages=detected_languages,
                language_segments=language_segments,
                code_switch_events=code_switch_events,
                dialect_analysis=dialect_analysis,
                complexity_score=complexity_score,
                cultural_markers=cultural_markers,
                processing_metadata={
                    'segments_count': len(language_segments),
                    'switches_count': len(code_switch_events),
                    'languages_count': len(detected_languages),
                    'processing_time': '<1s'
                }
            )
            
            # 8. Store in database
            self.database.store_analysis(analysis)
            
            logger.info("Multilingual analysis completed successfully")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in multilingual analysis: {str(e)}")
            # Return minimal analysis with error info
            return MultilingualAnalysis(
                text=text,
                primary_language=Language.ENGLISH,
                detected_languages=[Language.ENGLISH],
                language_segments=[],
                code_switch_events=[],
                dialect_analysis={},
                complexity_score=0.0,
                cultural_markers=[],
                processing_metadata={'error': str(e)}
            )
    
    def _determine_primary_language(self, segments: List[LanguageSegment]) -> Language:
        """Determine the primary language based on segments."""
        if not segments:
            return Language.ENGLISH
        
        # Calculate language weights based on text length and confidence
        language_weights = {}
        
        for segment in segments:
            weight = len(segment.text) * segment.confidence
            if segment.language in language_weights:
                language_weights[segment.language] += weight
            else:
                language_weights[segment.language] = weight
        
        return max(language_weights, key=language_weights.get)
    
    def _analyze_dialects(self, segments: List[LanguageSegment]) -> Dict[Language, List[Dialect]]:
        """Analyze dialects for each detected language."""
        dialect_analysis = {}
        
        for segment in segments:
            if segment.language not in dialect_analysis:
                dialect_analysis[segment.language] = []
            
            if segment.dialect and segment.dialect not in dialect_analysis[segment.language]:
                dialect_analysis[segment.language].append(segment.dialect)
        
        return dialect_analysis
    
    def _calculate_complexity(self, segments: List[LanguageSegment], 
                            events: List[CodeSwitchEvent],
                            languages: List[Language]) -> float:
        """Calculate multilingual complexity score (0-1)."""
        
        # Base score for number of languages
        language_score = min(len(languages) / 5.0, 1.0)  # Max at 5 languages
        
        # Code-switching frequency score
        if segments:
            switch_frequency = len(events) / len(segments)
            switch_score = min(switch_frequency * 2, 1.0)
        else:
            switch_score = 0.0
        
        # Segment variation score (how evenly distributed languages are)
        if len(segments) > 1:
            language_counts = {}
            for segment in segments:
                language_counts[segment.language] = language_counts.get(segment.language, 0) + 1
            
            # Calculate entropy-like measure
            total_segments = len(segments)
            entropy = 0
            for count in language_counts.values():
                prob = count / total_segments
                if prob > 0:
                    entropy -= prob * (prob ** 0.5)  # Modified entropy
            
            distribution_score = min(entropy, 1.0)
        else:
            distribution_score = 0.0
        
        # Weighted combination
        complexity = (language_score * 0.4 + switch_score * 0.4 + distribution_score * 0.2)
        return min(complexity, 1.0)
    
    async def batch_analyze(self, texts: List[str]) -> List[MultilingualAnalysis]:
        """Batch analyze multiple texts."""
        results = []
        
        for text in texts:
            try:
                analysis = await self.analyze_text(text)
                results.append(analysis)
            except Exception as e:
                # Create error analysis
                error_analysis = MultilingualAnalysis(
                    text=text,
                    primary_language=Language.ENGLISH,
                    detected_languages=[],
                    language_segments=[],
                    code_switch_events=[],
                    dialect_analysis={},
                    complexity_score=0.0,
                    cultural_markers=[],
                    processing_metadata={'error': str(e)}
                )
                results.append(error_analysis)
        
        return results
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get system statistics and insights."""
        try:
            db_stats = self.database.get_statistics()
            
            return {
                'database_statistics': db_stats,
                'supported_languages': len(Language),
                'supported_dialects': len(Dialect),
                'code_switch_types': len(CodeSwitchType),
                'system_status': 'operational'
            }
        except Exception as e:
            return {
                'error': str(e),
                'system_status': 'error'
            }
    
    def export_analysis_data(self, format: str = "json") -> str:
        """Export analysis data in specified format."""
        try:
            stats = self.get_system_statistics()
            
            if format.lower() == "json":
                return json.dumps(stats, indent=2, default=str)
            else:
                return f"Export format '{format}' not supported. Use 'json'."
        
        except Exception as e:
            return f"Export error: {str(e)}"

# Demo and testing functions
async def demo_multilingual_analysis():
    """Demonstrate the multilingual analysis capabilities."""
    system = AdvancedMultilingualSystem()
    
    print("🌍 Advanced Multilingual System Demo")
    print("=" * 50)
    
    # Test cases with different code-switching patterns
    test_cases = [
        # English-Spanish code-switching
        "I went to the store pero no había nada que me gustara.",
        
        # Spanish-English professional context
        "La reunión es mañana at 3 PM in the conference room.",
        
        # French-English casual conversation
        "C'est vraiment cool, you know what I mean?",
        
        # Multi-language tourist context
        "Excuse me, ¿dónde está la biblioteca? Je cherche la bibliothèque.",
        
        # German-English academic
        "The concept of Gemeinschaft und Gesellschaft is fundamental to sociology.",
        
        # Spanish regional variations
        "¡Órale! That's so cool, hermano. Está padrísimo este lugar.",
        
        # Chinese-English tech context
        "我们的 API works really well for 数据处理.",
    ]
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}:")
        print(f"Text: {text}")
        print("-" * 40)
        
        # Analyze text
        analysis = await system.analyze_text(text)
        
        # Display results
        print(f"Primary Language: {analysis.primary_language.value}")
        print(f"Detected Languages: {[lang.value for lang in analysis.detected_languages]}")
        print(f"Complexity Score: {analysis.complexity_score:.3f}")
        print(f"Code-Switch Events: {len(analysis.code_switch_events)}")
        
        # Show language segments
        if analysis.language_segments:
            print("Language Segments:")
            for segment in analysis.language_segments:
                dialect_info = f" ({segment.dialect.value})" if segment.dialect else ""
                print(f"  [{segment.language.value}{dialect_info}] '{segment.text}' (conf: {segment.confidence:.3f})")
        
        # Show code-switching events
        if analysis.code_switch_events:
            print("Code-Switch Events:")
            for event in analysis.code_switch_events:
                print(f"  {event.from_language.value} → {event.to_language.value} "
                      f"({event.switch_type.value}, {event.trigger_type})")
        
        # Show cultural markers
        if analysis.cultural_markers:
            print(f"Cultural Markers: {analysis.cultural_markers}")
    
    # System statistics
    print(f"\n📊 System Statistics:")
    stats = system.get_system_statistics()
    print(f"Total Analyses: {stats.get('database_statistics', {}).get('total_analyses', 0)}")
    print(f"Supported Languages: {stats.get('supported_languages', 0)}")
    print(f"System Status: {stats.get('system_status', 'unknown')}")
    
    print(f"\n✅ Advanced multilingual analysis demo completed!")

if __name__ == "__main__":
    asyncio.run(demo_multilingual_analysis())