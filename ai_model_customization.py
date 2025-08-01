#!/usr/bin/env python3
"""
AI Model Customization Module
Implements custom vocabulary training, speaker voice recognition, 
custom entity types, and model fine-tuning capabilities
"""

import os
import json
import logging
import pickle
import hashlib
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import sqlite3
from pathlib import Path

# ML/AI imports
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

import openai
from openai import OpenAI

# Internal imports
from errors import (
    TranscriptionError, NERError, APIError, handle_error, 
    ErrorCode, create_api_key_error
)
from stt import WhisperTranscriber, TranscriptionResult
from advanced_transcription import (
    AdvancedTranscriber, AdvancedTranscriptionResult, 
    SpeakerSegment, TimestampedWord
)

logger = logging.getLogger(__name__)

@dataclass
class CustomVocabulary:
    """Custom vocabulary for domain-specific transcription"""
    name: str
    domain: str  # e.g., "medical", "legal", "technical", "business"
    terms: List[str]
    replacements: Dict[str, str]  # Common misrecognitions -> correct terms
    boost_words: List[str]  # Words to boost in recognition
    created_at: datetime
    usage_count: int = 0
    accuracy_improvement: float = 0.0
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CustomVocabulary':
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)

@dataclass
class VoiceProfile:
    """Speaker voice profile for recognition"""
    profile_id: str
    name: str
    speaker_features: Dict[str, float]  # Voice characteristics
    sample_segments: List[Dict]  # Reference audio segments
    recognition_accuracy: float
    created_at: datetime
    last_used: datetime
    usage_count: int = 0
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['last_used'] = self.last_used.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'VoiceProfile':
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_used'] = datetime.fromisoformat(data['last_used'])
        return cls(**data)

@dataclass
class CustomEntityType:
    """Custom entity type definition"""
    name: str
    category: str
    patterns: List[str]  # Regex patterns for detection
    examples: List[str]  # Example instances
    context_clues: List[str]  # Words that often appear near this entity
    extraction_prompt: str  # GPT prompt for extraction
    validation_rules: List[str]  # Rules for validation
    created_at: datetime
    accuracy: float = 0.0
    usage_count: int = 0
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CustomEntityType':
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)

@dataclass
class ModelConfiguration:
    """Model configuration for A/B testing"""
    config_id: str
    name: str
    description: str
    parameters: Dict[str, Any]
    performance_metrics: Dict[str, float]
    is_active: bool
    created_at: datetime
    test_results: List[Dict] = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ModelConfiguration':
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)

class CustomVocabularyManager:
    """Manages custom vocabularies for domain-specific transcription"""
    
    def __init__(self, db_path: str = "data/customizations.db"):
        self.db_path = db_path
        if SKLEARN_AVAILABLE:
            self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        else:
            self.vectorizer = None
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for storing vocabularies"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS custom_vocabularies (
                    name TEXT PRIMARY KEY,
                    domain TEXT,
                    data TEXT,  -- JSON serialized vocabulary
                    created_at TIMESTAMP,
                    usage_count INTEGER DEFAULT 0,
                    accuracy_improvement REAL DEFAULT 0.0
                )
            """)
            conn.commit()
    
    def create_vocabulary(self, name: str, domain: str, terms: List[str], 
                         replacements: Dict[str, str] = None, 
                         boost_words: List[str] = None) -> CustomVocabulary:
        """Create a new custom vocabulary"""
        try:
            # Validate inputs
            if not name or not domain or not terms:
                raise ValueError("Name, domain, and terms are required")
            
            # Clean and validate terms
            cleaned_terms = [term.strip().lower() for term in terms if term.strip()]
            if len(cleaned_terms) < 3:
                raise ValueError("At least 3 terms are required")
            
            vocabulary = CustomVocabulary(
                name=name,
                domain=domain,
                terms=cleaned_terms,
                replacements=replacements or {},
                boost_words=boost_words or [],
                created_at=datetime.now()
            )
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO custom_vocabularies 
                    (name, domain, data, created_at, usage_count, accuracy_improvement)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    vocabulary.name,
                    vocabulary.domain,
                    json.dumps(vocabulary.to_dict()),
                    vocabulary.created_at,
                    vocabulary.usage_count,
                    vocabulary.accuracy_improvement
                ))
                conn.commit()
            
            logger.info(f"Created custom vocabulary '{name}' with {len(cleaned_terms)} terms")
            return vocabulary
            
        except Exception as e:
            logger.error(f"Failed to create custom vocabulary: {e}")
            raise NERError(
                message=f"Failed to create custom vocabulary: {e}",
                error_code=ErrorCode.NER_PROCESSING_ERROR,
                user_message="Failed to create custom vocabulary. Please check your inputs.",
                ner_type="custom_vocabulary",
                suggestions=[
                    "Ensure vocabulary name is unique",
                    "Provide at least 3 terms",
                    "Check that domain is specified"
                ]
            )
    
    def get_vocabulary(self, name: str) -> Optional[CustomVocabulary]:
        """Get custom vocabulary by name"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT data FROM custom_vocabularies WHERE name = ?",
                    (name,)
                )
                row = cursor.fetchone()
                
                if row:
                    data = json.loads(row[0])
                    return CustomVocabulary.from_dict(data)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get vocabulary '{name}': {e}")
            return None
    
    def list_vocabularies(self) -> List[CustomVocabulary]:
        """List all custom vocabularies"""
        try:
            vocabularies = []
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT data FROM custom_vocabularies ORDER BY created_at DESC"
                )
                
                for row in cursor.fetchall():
                    data = json.loads(row[0])
                    vocabularies.append(CustomVocabulary.from_dict(data))
            
            return vocabularies
            
        except Exception as e:
            logger.error(f"Failed to list vocabularies: {e}")
            return []
    
    def apply_vocabulary_corrections(self, text: str, vocabulary_name: str) -> str:
        """Apply vocabulary corrections to transcribed text"""
        try:
            vocabulary = self.get_vocabulary(vocabulary_name)
            if not vocabulary:
                return text
            
            corrected_text = text
            
            # Apply replacement corrections
            for wrong, correct in vocabulary.replacements.items():
                corrected_text = corrected_text.replace(wrong.lower(), correct)
            
            # Update usage count
            self._update_vocabulary_usage(vocabulary_name)
            
            logger.info(f"Applied vocabulary corrections from '{vocabulary_name}'")
            return corrected_text
            
        except Exception as e:
            logger.error(f"Failed to apply vocabulary corrections: {e}")
            return text
    
    def _update_vocabulary_usage(self, name: str):
        """Update vocabulary usage statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE custom_vocabularies 
                    SET usage_count = usage_count + 1 
                    WHERE name = ?
                """, (name,))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to update vocabulary usage: {e}")

class VoiceProfileManager:
    """Manages speaker voice profiles for recognition"""
    
    def __init__(self, db_path: str = "data/customizations.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database for voice profiles"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS voice_profiles (
                    profile_id TEXT PRIMARY KEY,
                    name TEXT,
                    data TEXT,  -- JSON serialized profile
                    created_at TIMESTAMP,
                    last_used TIMESTAMP,
                    usage_count INTEGER DEFAULT 0,
                    recognition_accuracy REAL DEFAULT 0.0
                )
            """)
            conn.commit()
    
    def create_voice_profile(self, name: str, audio_segments: List[Dict]) -> VoiceProfile:
        """Create voice profile from audio segments"""
        try:
            if not name or not audio_segments:
                raise ValueError("Name and audio segments are required")
            
            # Generate unique profile ID
            profile_id = hashlib.md5(f"{name}_{time.time()}".encode()).hexdigest()[:8]
            
            # Extract voice features (simplified - in production would use more sophisticated analysis)
            features = self._extract_voice_features(audio_segments)
            
            profile = VoiceProfile(
                profile_id=profile_id,
                name=name,
                speaker_features=features,
                sample_segments=audio_segments,
                recognition_accuracy=0.0,
                created_at=datetime.now(),
                last_used=datetime.now()
            )
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO voice_profiles 
                    (profile_id, name, data, created_at, last_used, usage_count, recognition_accuracy)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    profile.profile_id,
                    profile.name,
                    json.dumps(profile.to_dict()),
                    profile.created_at,
                    profile.last_used,
                    profile.usage_count,
                    profile.recognition_accuracy
                ))
                conn.commit()
            
            logger.info(f"Created voice profile '{name}' with ID {profile_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Failed to create voice profile: {e}")
            raise TranscriptionError(
                message=f"Failed to create voice profile: {e}",
                error_code=ErrorCode.TRANSCRIPTION_FAILED,
                user_message="Failed to create voice profile. Please check audio quality.",
                model_used="voice_profile_creator",
                suggestions=[
                    "Ensure audio segments are clear and consistent",
                    "Provide at least 3 audio segments",
                    "Use high-quality audio recordings"
                ]
            )
    
    def _extract_voice_features(self, audio_segments: List[Dict]) -> Dict[str, float]:
        """Extract voice characteristics from audio segments"""
        # Simplified feature extraction - in production would use advanced audio analysis
        features = {
            'avg_duration': np.mean([seg.get('duration', 0) for seg in audio_segments]),
            'avg_confidence': np.mean([seg.get('confidence', 0.5) for seg in audio_segments]),
            'speaking_rate': np.mean([
                len(seg.get('text', '').split()) / max(seg.get('duration', 1), 0.1)
                for seg in audio_segments
            ]),
            'segment_count': len(audio_segments),
            'total_words': sum(len(seg.get('text', '').split()) for seg in audio_segments)
        }
        
        return features
    
    def match_voice_profile(self, speaker_segment: SpeakerSegment) -> Optional[str]:
        """Match speaker segment to existing voice profile"""
        try:
            profiles = self.list_voice_profiles()
            if not profiles:
                return None
            
            # Extract features from current segment
            current_features = {
                'duration': speaker_segment.duration(),
                'confidence': speaker_segment.confidence,
                'speaking_rate': len(speaker_segment.text.split()) / max(speaker_segment.duration(), 0.1),
                'word_count': len(speaker_segment.text.split())
            }
            
            best_match = None
            best_similarity = 0.0
            
            for profile in profiles:
                similarity = self._calculate_voice_similarity(current_features, profile.speaker_features)
                if similarity > best_similarity and similarity > 0.7:  # Threshold for matching
                    best_similarity = similarity
                    best_match = profile.profile_id
            
            if best_match:
                self._update_profile_usage(best_match)
                logger.info(f"Matched speaker to profile {best_match} with similarity {best_similarity:.3f}")
            
            return best_match
            
        except Exception as e:
            logger.error(f"Failed to match voice profile: {e}")
            return None
    
    def _calculate_voice_similarity(self, features1: Dict, features2: Dict) -> float:
        """Calculate similarity between voice features"""
        try:
            # Normalize and compare key features
            similarities = []
            
            # Speaking rate similarity
            if 'speaking_rate' in features1 and 'speaking_rate' in features2:
                rate_diff = abs(features1['speaking_rate'] - features2.get('speaking_rate', 0))
                rate_sim = max(0, 1 - (rate_diff / 10))  # Normalize by typical range
                similarities.append(rate_sim)
            
            # Confidence similarity
            if 'confidence' in features1 and 'avg_confidence' in features2:
                conf_diff = abs(features1['confidence'] - features2.get('avg_confidence', 0))
                conf_sim = max(0, 1 - conf_diff)
                similarities.append(conf_sim)
            
            if NUMPY_AVAILABLE:
                return np.mean(similarities) if similarities else 0.0
            else:
                return sum(similarities) / len(similarities) if similarities else 0.0
            
        except Exception as e:
            logger.error(f"Failed to calculate voice similarity: {e}")
            return 0.0
    
    def list_voice_profiles(self) -> List[VoiceProfile]:
        """List all voice profiles"""
        try:
            profiles = []
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT data FROM voice_profiles ORDER BY last_used DESC"
                )
                
                for row in cursor.fetchall():
                    data = json.loads(row[0])
                    profiles.append(VoiceProfile.from_dict(data))
            
            return profiles
            
        except Exception as e:
            logger.error(f"Failed to list voice profiles: {e}")
            return []
    
    def _update_profile_usage(self, profile_id: str):
        """Update profile usage statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE voice_profiles 
                    SET usage_count = usage_count + 1, last_used = ?
                    WHERE profile_id = ?
                """, (datetime.now(), profile_id))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to update profile usage: {e}")

class CustomEntityExtractor:
    """Manages custom entity types and extraction"""
    
    def __init__(self, db_path: str = "data/customizations.db"):
        self.db_path = db_path
        self._init_database()
        self.openai_client = self._get_openai_client()
    
    def _init_database(self):
        """Initialize database for custom entity types"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS custom_entity_types (
                    name TEXT PRIMARY KEY,
                    category TEXT,
                    data TEXT,  -- JSON serialized entity type
                    created_at TIMESTAMP,
                    usage_count INTEGER DEFAULT 0,
                    accuracy REAL DEFAULT 0.0
                )
            """)
            conn.commit()
    
    def _get_openai_client(self) -> Optional[OpenAI]:
        """Get OpenAI client for custom entity extraction"""
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            try:
                return OpenAI(api_key=api_key)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
        return None
    
    def create_entity_type(self, name: str, category: str, patterns: List[str],
                          examples: List[str], context_clues: List[str] = None,
                          validation_rules: List[str] = None) -> CustomEntityType:
        """Create a new custom entity type"""
        try:
            if not name or not category or not patterns or not examples:
                raise ValueError("Name, category, patterns, and examples are required")
            
            # Generate extraction prompt
            extraction_prompt = self._generate_extraction_prompt(name, category, examples, context_clues)
            
            entity_type = CustomEntityType(
                name=name,
                category=category,
                patterns=patterns,
                examples=examples,
                context_clues=context_clues or [],
                extraction_prompt=extraction_prompt,
                validation_rules=validation_rules or [],
                created_at=datetime.now()
            )
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO custom_entity_types 
                    (name, category, data, created_at, usage_count, accuracy)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    entity_type.name,
                    entity_type.category,
                    json.dumps(entity_type.to_dict()),
                    entity_type.created_at,
                    entity_type.usage_count,
                    entity_type.accuracy
                ))
                conn.commit()
            
            logger.info(f"Created custom entity type '{name}' in category '{category}'")
            return entity_type
            
        except Exception as e:
            logger.error(f"Failed to create custom entity type: {e}")
            raise NERError(
                message=f"Failed to create custom entity type: {e}",
                error_code=ErrorCode.NER_PROCESSING_ERROR,
                user_message="Failed to create custom entity type. Please check your inputs.",
                ner_type="custom_entity",
                suggestions=[
                    "Ensure entity name is unique",
                    "Provide clear examples and patterns",
                    "Check that category is specified"
                ]
            )
    
    def _generate_extraction_prompt(self, name: str, category: str, 
                                  examples: List[str], context_clues: List[str] = None) -> str:
        """Generate GPT prompt for custom entity extraction"""
        prompt = f"""Extract {name} entities from the text. These are {category} entities.

Examples of {name}:
{chr(10).join(f"- {example}" for example in examples[:5])}

"""
        
        if context_clues:
            prompt += f"""Context clues that often appear near {name} entities:
{chr(10).join(f"- {clue}" for clue in context_clues[:3])}

"""
        
        prompt += f"""Return only valid {name} entities found in the text as a JSON array.
Be precise and only extract entities that clearly match the pattern."""
        
        return prompt
    
    def extract_custom_entities(self, text: str, entity_type_name: str) -> List[str]:
        """Extract custom entities from text"""
        try:
            entity_type = self.get_entity_type(entity_type_name)
            if not entity_type:
                return []
            
            if not self.openai_client:
                # Fallback to pattern matching
                return self._extract_with_patterns(text, entity_type)
            
            # Use GPT for extraction
            extracted = self._extract_with_gpt(text, entity_type)
            
            # Update usage count
            self._update_entity_type_usage(entity_type_name)
            
            return extracted
            
        except Exception as e:
            logger.error(f"Failed to extract custom entities: {e}")
            return []
    
    def _extract_with_gpt(self, text: str, entity_type: CustomEntityType) -> List[str]:
        """Extract entities using GPT"""
        try:
            messages = [
                {
                    "role": "system",
                    "content": entity_type.extraction_prompt
                },
                {
                    "role": "user",
                    "content": f"Extract {entity_type.name} from this text:\n\n{text}"
                }
            ]
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.1,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                entities = json.loads(result_text)
                if isinstance(entities, list):
                    return [str(entity).strip() for entity in entities if entity]
            except json.JSONDecodeError:
                # Extract from text if not JSON
                lines = result_text.split('\n')
                entities = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('*'):
                        # Remove common prefixes
                        for prefix in ['- ', '• ', '1. ', '2. ', '3. ']:
                            if line.startswith(prefix):
                                line = line[len(prefix):].strip()
                                break
                        if line:
                            entities.append(line)
                return entities[:10]  # Limit results
            
            return []
            
        except Exception as e:
            logger.error(f"GPT entity extraction failed: {e}")
            return []
    
    def _extract_with_patterns(self, text: str, entity_type: CustomEntityType) -> List[str]:
        """Extract entities using regex patterns"""
        import re
        
        entities = []
        for pattern in entity_type.patterns:
            try:
                matches = re.findall(pattern, text, re.IGNORECASE)
                entities.extend(matches)
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{pattern}': {e}")
        
        # Remove duplicates and return
        return list(set(entities))
    
    def get_entity_type(self, name: str) -> Optional[CustomEntityType]:
        """Get custom entity type by name"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT data FROM custom_entity_types WHERE name = ?",
                    (name,)
                )
                row = cursor.fetchone()
                
                if row:
                    data = json.loads(row[0])
                    return CustomEntityType.from_dict(data)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get entity type '{name}': {e}")
            return None
    
    def list_entity_types(self) -> List[CustomEntityType]:
        """List all custom entity types"""
        try:
            entity_types = []
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT data FROM custom_entity_types ORDER BY created_at DESC"
                )
                
                for row in cursor.fetchall():
                    data = json.loads(row[0])
                    entity_types.append(CustomEntityType.from_dict(data))
            
            return entity_types
            
        except Exception as e:
            logger.error(f"Failed to list entity types: {e}")
            return []
    
    def _update_entity_type_usage(self, name: str):
        """Update entity type usage statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE custom_entity_types 
                    SET usage_count = usage_count + 1 
                    WHERE name = ?
                """, (name,))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to update entity type usage: {e}")

class ModelConfigurationManager:
    """Manages model configurations for A/B testing"""
    
    def __init__(self, db_path: str = "data/customizations.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database for model configurations"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS model_configurations (
                    config_id TEXT PRIMARY KEY,
                    name TEXT,
                    data TEXT,  -- JSON serialized configuration
                    is_active BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP
                )
            """)
            conn.commit()
    
    def create_configuration(self, name: str, description: str, 
                           parameters: Dict[str, Any]) -> ModelConfiguration:
        """Create a new model configuration"""
        try:
            config_id = hashlib.md5(f"{name}_{time.time()}".encode()).hexdigest()[:8]
            
            config = ModelConfiguration(
                config_id=config_id,
                name=name,
                description=description,
                parameters=parameters,
                performance_metrics={},
                is_active=False,
                created_at=datetime.now(),
                test_results=[]
            )
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO model_configurations 
                    (config_id, name, data, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    config.config_id,
                    config.name,
                    json.dumps(config.to_dict()),
                    config.is_active,
                    config.created_at
                ))
                conn.commit()
            
            logger.info(f"Created model configuration '{name}' with ID {config_id}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to create model configuration: {e}")
            raise TranscriptionError(
                message=f"Failed to create model configuration: {e}",
                error_code=ErrorCode.TRANSCRIPTION_FAILED,
                user_message="Failed to create model configuration.",
                model_used="config_manager",
                suggestions=[
                    "Check configuration parameters",
                    "Ensure unique configuration name"
                ]
            )
    
    def run_ab_test(self, config_a_id: str, config_b_id: str, 
                    test_data: List[str]) -> Dict[str, Any]:
        """Run A/B test between two configurations"""
        try:
            config_a = self.get_configuration(config_a_id)
            config_b = self.get_configuration(config_b_id)
            
            if not config_a or not config_b:
                raise ValueError("Both configurations must exist")
            
            results = {
                'config_a': {'id': config_a_id, 'name': config_a.name, 'results': []},
                'config_b': {'id': config_b_id, 'name': config_b.name, 'results': []},
                'comparison': {}
            }
            
            # Run tests (simplified - would use actual model testing in production)
            for i, data in enumerate(test_data[:10]):  # Limit test size
                # Simulate testing with different configurations
                result_a = self._simulate_model_test(data, config_a.parameters)
                result_b = self._simulate_model_test(data, config_b.parameters)
                
                results['config_a']['results'].append(result_a)
                results['config_b']['results'].append(result_b)
            
            # Calculate comparison metrics
            if results['config_a']['results'] and results['config_b']['results']:
                results_a = [r['accuracy'] for r in results['config_a']['results']]
                results_b = [r['accuracy'] for r in results['config_b']['results']]
                
                if NUMPY_AVAILABLE:
                    avg_a = np.mean(results_a)
                    avg_b = np.mean(results_b)
                else:
                    avg_a = sum(results_a) / len(results_a)
                    avg_b = sum(results_b) / len(results_b)
                
                results['comparison'] = {
                    'config_a_avg_accuracy': avg_a,
                    'config_b_avg_accuracy': avg_b,
                    'winner': config_a_id if avg_a > avg_b else config_b_id,
                    'improvement': abs(avg_a - avg_b),
                    'statistical_significance': self._calculate_significance(results_a, results_b)
                }
            
            logger.info(f"Completed A/B test between {config_a_id} and {config_b_id}")
            return results
            
        except Exception as e:
            logger.error(f"A/B test failed: {e}")
            raise TranscriptionError(
                message=f"A/B test failed: {e}",
                error_code=ErrorCode.TRANSCRIPTION_FAILED,
                user_message="A/B test failed. Please check configurations.",
                model_used="ab_tester",
                suggestions=[
                    "Ensure both configurations exist",
                    "Provide valid test data",
                    "Check configuration parameters"
                ]
            )
    
    def _simulate_model_test(self, data: str, parameters: Dict[str, Any]) -> Dict[str, float]:
        """Simulate model testing (replace with actual testing in production)"""
        # This is a simplified simulation - in production would test actual models
        base_accuracy = 0.85
        
        # Adjust accuracy based on parameters
        if parameters.get('temperature', 0.5) < 0.3:
            base_accuracy += 0.05  # More conservative = higher accuracy
        if parameters.get('max_tokens', 1000) > 2000:
            base_accuracy -= 0.02  # Longer responses might be less accurate
        
        # Add some randomness
        import random
        if NUMPY_AVAILABLE:
            accuracy = base_accuracy + np.random.normal(0, 0.05)
            processing_time = np.random.uniform(1.0, 3.0)
        else:
            accuracy = base_accuracy + random.gauss(0, 0.05)
            processing_time = random.uniform(1.0, 3.0)
        
        accuracy = max(0.0, min(1.0, accuracy))
        
        return {
            'accuracy': accuracy,
            'processing_time': processing_time,
            'word_count': len(data.split())
        }
    
    def _calculate_significance(self, results_a: List[float], results_b: List[float]) -> float:
        """Calculate statistical significance (simplified)"""
        try:
            from scipy import stats
            t_stat, p_value = stats.ttest_ind(results_a, results_b)
            return p_value
        except ImportError:
            # Fallback if scipy not available
            return 0.05  # Assume moderate significance
    
    def get_configuration(self, config_id: str) -> Optional[ModelConfiguration]:
        """Get model configuration by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT data FROM model_configurations WHERE config_id = ?",
                    (config_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    data = json.loads(row[0])
                    return ModelConfiguration.from_dict(data)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get configuration '{config_id}': {e}")
            return None

# Main AI Customization Class
class AIModelCustomization:
    """Main class for AI model customization features"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, "customizations.db")
        
        # Initialize managers
        self.vocabulary_manager = CustomVocabularyManager(self.db_path)
        self.voice_manager = VoiceProfileManager(self.db_path)
        self.entity_manager = CustomEntityExtractor(self.db_path)
        self.config_manager = ModelConfigurationManager(self.db_path)
        
        # Initialize transcription components
        self.transcriber = WhisperTranscriber()
        self.advanced_transcriber = AdvancedTranscriber()
        
        logger.info("AI Model Customization system initialized")
    
    def transcribe_with_custom_vocabulary(self, audio_path: str, vocabulary_name: str,
                                        use_api: bool = True) -> TranscriptionResult:
        """Transcribe audio with custom vocabulary corrections"""
        try:
            # Perform base transcription
            result = self.transcriber.transcribe(audio_path, use_api)
            
            # Apply vocabulary corrections
            corrected_text = self.vocabulary_manager.apply_vocabulary_corrections(
                result.text, vocabulary_name
            )
            
            # Update result
            result.text = corrected_text
            result.model_used += f"_vocab_{vocabulary_name}"
            
            logger.info(f"Applied custom vocabulary '{vocabulary_name}' to transcription")
            return result
            
        except Exception as e:
            logger.error(f"Custom vocabulary transcription failed: {e}")
            raise TranscriptionError(
                message=f"Custom vocabulary transcription failed: {e}",
                error_code=ErrorCode.TRANSCRIPTION_FAILED,
                user_message="Transcription with custom vocabulary failed.",
                model_used="custom_vocab_transcriber",
                suggestions=[
                    "Try without custom vocabulary",
                    "Check vocabulary configuration",
                    "Use basic transcription mode"
                ]
            )
    
    def transcribe_with_voice_profiles(self, audio_path: str) -> AdvancedTranscriptionResult:
        """Transcribe with speaker identification using voice profiles"""
        try:
            # Perform advanced transcription
            result = self.advanced_transcriber.transcribe_with_speaker_diarization(audio_path)
            
            # Match speakers to voice profiles
            for speaker in result.speakers:
                profile_id = self.voice_manager.match_voice_profile(speaker)
                if profile_id:
                    # Get profile to get the name
                    profiles = self.voice_manager.list_voice_profiles()
                    profile = next((p for p in profiles if p.profile_id == profile_id), None)
                    if profile:
                        speaker.speaker_id = f"{profile.name} ({speaker.speaker_id})"
            
            result.model_used += "_voice_profiles"
            logger.info("Applied voice profile matching to transcription")
            return result
            
        except Exception as e:
            logger.error(f"Voice profile transcription failed: {e}")
            raise TranscriptionError(
                message=f"Voice profile transcription failed: {e}",
                error_code=ErrorCode.TRANSCRIPTION_FAILED,
                user_message="Transcription with voice profiles failed.",
                model_used="voice_profile_transcriber",
                suggestions=[
                    "Try without voice profiles",
                    "Check voice profile configuration",
                    "Use basic speaker diarization"
                ]
            )
    
    def extract_entities_with_custom_types(self, text: str, 
                                         custom_entity_types: List[str] = None) -> Dict[str, List[str]]:
        """Extract entities including custom types"""
        try:
            # Start with basic entity extraction
            from ner_basic import extract_entities_basic
            basic_entities = extract_entities_basic(text)
            
            # Add custom entities
            if custom_entity_types:
                for entity_type_name in custom_entity_types:
                    custom_entities = self.entity_manager.extract_custom_entities(
                        text, entity_type_name
                    )
                    if custom_entities:
                        basic_entities[entity_type_name.upper()] = custom_entities
            
            logger.info(f"Extracted entities with {len(custom_entity_types or [])} custom types")
            return basic_entities
            
        except Exception as e:
            logger.error(f"Custom entity extraction failed: {e}")
            raise NERError(
                message=f"Custom entity extraction failed: {e}",
                error_code=ErrorCode.NER_PROCESSING_ERROR,
                user_message="Entity extraction with custom types failed.",
                ner_type="custom_entities",
                suggestions=[
                    "Try without custom entity types",
                    "Check entity type configuration",
                    "Use basic entity extraction"
                ]
            )
    
    def get_customization_stats(self) -> Dict[str, Any]:
        """Get statistics about customizations"""
        try:
            stats = {
                'vocabularies': {
                    'total': len(self.vocabulary_manager.list_vocabularies()),
                    'most_used': None
                },
                'voice_profiles': {
                    'total': len(self.voice_manager.list_voice_profiles()),
                    'most_used': None
                },
                'entity_types': {
                    'total': len(self.entity_manager.list_entity_types()),
                    'most_used': None
                },
                'system_status': 'active'
            }
            
            # Get most used items
            vocabularies = self.vocabulary_manager.list_vocabularies()
            if vocabularies:
                most_used_vocab = max(vocabularies, key=lambda v: v.usage_count)
                stats['vocabularies']['most_used'] = {
                    'name': most_used_vocab.name,
                    'usage_count': most_used_vocab.usage_count
                }
            
            profiles = self.voice_manager.list_voice_profiles()
            if profiles:
                most_used_profile = max(profiles, key=lambda p: p.usage_count)
                stats['voice_profiles']['most_used'] = {
                    'name': most_used_profile.name,
                    'usage_count': most_used_profile.usage_count
                }
            
            entity_types = self.entity_manager.list_entity_types()
            if entity_types:
                most_used_entity = max(entity_types, key=lambda e: e.usage_count)
                stats['entity_types']['most_used'] = {
                    'name': most_used_entity.name,
                    'usage_count': most_used_entity.usage_count
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get customization stats: {e}")
            return {'error': str(e)}

# Global instance
_ai_customization = None

def get_ai_customization() -> AIModelCustomization:
    """Get or create global AI customization instance"""
    global _ai_customization
    if _ai_customization is None:
        _ai_customization = AIModelCustomization()
    return _ai_customization

# Public API functions
def create_custom_vocabulary(name: str, domain: str, terms: List[str], 
                           replacements: Dict[str, str] = None) -> CustomVocabulary:
    """Create a custom vocabulary for domain-specific transcription"""
    customization = get_ai_customization()
    return customization.vocabulary_manager.create_vocabulary(name, domain, terms, replacements)

def create_voice_profile(name: str, audio_segments: List[Dict]) -> VoiceProfile:
    """Create a voice profile for speaker recognition"""
    customization = get_ai_customization()
    return customization.voice_manager.create_voice_profile(name, audio_segments)

def create_custom_entity_type(name: str, category: str, patterns: List[str],
                            examples: List[str]) -> CustomEntityType:
    """Create a custom entity type for extraction"""
    customization = get_ai_customization()
    return customization.entity_manager.create_entity_type(name, category, patterns, examples)

def transcribe_with_customizations(audio_path: str, vocabulary_name: str = None,
                                 use_voice_profiles: bool = False,
                                 custom_entity_types: List[str] = None) -> Dict[str, Any]:
    """Transcribe audio with all customizations applied"""
    customization = get_ai_customization()
    
    # Transcribe with voice profiles if requested
    if use_voice_profiles:
        transcription_result = customization.transcribe_with_voice_profiles(audio_path)
        text = transcription_result.text
    else:
        # Use custom vocabulary if specified
        if vocabulary_name:
            transcription_result = customization.transcribe_with_custom_vocabulary(
                audio_path, vocabulary_name
            )
        else:
            transcription_result = customization.transcriber.transcribe(audio_path)
        text = transcription_result.text
    
    # Extract entities with custom types
    entities = customization.extract_entities_with_custom_types(text, custom_entity_types)
    
    return {
        'transcription': transcription_result,
        'entities': entities,
        'customizations_applied': {
            'vocabulary': vocabulary_name,
            'voice_profiles': use_voice_profiles,
            'custom_entity_types': custom_entity_types or []
        }
    }