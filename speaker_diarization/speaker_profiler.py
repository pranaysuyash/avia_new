"""
Speaker profiling and recognition system for voice identification across recordings
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import sqlite3

logger = logging.getLogger(__name__)


@dataclass
class SpeakerProfile:
    """Comprehensive speaker profile with voice characteristics"""
    speaker_id: str
    name: Optional[str] = None
    embedding: Optional[List[float]] = None
    voice_characteristics: Dict[str, Any] = None
    speaking_patterns: Dict[str, Any] = None
    recognition_confidence: float = 0.0
    total_speaking_time: float = 0.0
    recording_count: int = 0
    last_updated: str = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.voice_characteristics is None:
            self.voice_characteristics = {}
        if self.speaking_patterns is None:
            self.speaking_patterns = {}
        if self.metadata is None:
            self.metadata = {}
        if self.last_updated is None:
            self.last_updated = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpeakerProfile':
        """Create from dictionary"""
        return cls(**data)


class SpeakerProfiler:
    """Manages speaker profiles and voice recognition across recordings"""
    
    def __init__(self, profile_dir: str = "cache/speaker_profiles"):
        self.profile_dir = Path(profile_dir)
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        
        # Database for speaker profiles
        self.db_path = self.profile_dir / "speaker_profiles.db"
        self._init_database()
        
        # In-memory cache
        self._profile_cache: Dict[str, SpeakerProfile] = {}
        self._load_profiles()
        
        # Recognition thresholds
        self.similarity_threshold = 0.85
        self.confidence_threshold = 0.75
    
    def _init_database(self):
        """Initialize SQLite database for speaker profiles"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS speaker_profiles (
                    speaker_id TEXT PRIMARY KEY,
                    name TEXT,
                    embedding TEXT,
                    voice_characteristics TEXT,
                    speaking_patterns TEXT,
                    recognition_confidence REAL,
                    total_speaking_time REAL,
                    recording_count INTEGER,
                    last_updated TEXT,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS recognition_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recording_id TEXT,
                    speaker_id TEXT,
                    recognized_as TEXT,
                    confidence REAL,
                    timestamp TEXT,
                    audio_path TEXT
                )
            """)
    
    def _load_profiles(self):
        """Load speaker profiles from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT * FROM speaker_profiles")
                for row in cursor.fetchall():
                    profile_data = {
                        'speaker_id': row[0],
                        'name': row[1],
                        'embedding': json.loads(row[2]) if row[2] else None,
                        'voice_characteristics': json.loads(row[3]) if row[3] else {},
                        'speaking_patterns': json.loads(row[4]) if row[4] else {},
                        'recognition_confidence': row[5],
                        'total_speaking_time': row[6],
                        'recording_count': row[7],
                        'last_updated': row[8],
                        'metadata': json.loads(row[9]) if row[9] else {}
                    }
                    profile = SpeakerProfile.from_dict(profile_data)
                    self._profile_cache[profile.speaker_id] = profile
                    
            logger.info(f"Loaded {len(self._profile_cache)} speaker profiles")
        except Exception as e:
            logger.error(f"Failed to load speaker profiles: {e}")
    
    def create_profile(self, 
                      speaker_id: str,
                      embedding: np.ndarray,
                      voice_characteristics: Dict[str, Any],
                      speaking_patterns: Dict[str, Any],
                      name: Optional[str] = None) -> SpeakerProfile:
        """Create a new speaker profile"""
        profile = SpeakerProfile(
            speaker_id=speaker_id,
            name=name,
            embedding=embedding.tolist() if embedding is not None else None,
            voice_characteristics=voice_characteristics,
            speaking_patterns=speaking_patterns,
            recognition_confidence=1.0,  # High confidence for new profile
            recording_count=1
        )
        
        self._profile_cache[speaker_id] = profile
        self._save_profile(profile)
        
        logger.info(f"Created new speaker profile: {speaker_id}")
        return profile
    
    def update_profile(self, 
                      speaker_id: str,
                      new_embedding: Optional[np.ndarray] = None,
                      new_characteristics: Optional[Dict[str, Any]] = None,
                      new_patterns: Optional[Dict[str, Any]] = None,
                      speaking_time: float = 0.0) -> Optional[SpeakerProfile]:
        """Update an existing speaker profile"""
        if speaker_id not in self._profile_cache:
            logger.warning(f"Speaker profile not found: {speaker_id}")
            return None
        
        profile = self._profile_cache[speaker_id]
        
        # Update embedding (weighted average with existing)
        if new_embedding is not None and profile.embedding:
            existing_embedding = np.array(profile.embedding)
            # Weight: 70% existing, 30% new
            updated_embedding = 0.7 * existing_embedding + 0.3 * new_embedding
            profile.embedding = updated_embedding.tolist()
        elif new_embedding is not None:
            profile.embedding = new_embedding.tolist()
        
        # Update characteristics
        if new_characteristics:
            profile.voice_characteristics.update(new_characteristics)
        
        # Update speaking patterns
        if new_patterns:
            profile.speaking_patterns.update(new_patterns)
        
        # Update statistics
        profile.total_speaking_time += speaking_time
        profile.recording_count += 1
        profile.last_updated = datetime.now().isoformat()
        
        self._save_profile(profile)
        
        logger.info(f"Updated speaker profile: {speaker_id}")
        return profile
    
    def recognize_speaker(self, 
                         embedding: np.ndarray,
                         voice_characteristics: Optional[Dict[str, Any]] = None) -> Tuple[Optional[str], float]:
        """Recognize a speaker based on voice embedding and characteristics"""
        if not self._profile_cache:
            return None, 0.0
        
        best_match = None
        best_similarity = 0.0
        
        for speaker_id, profile in self._profile_cache.items():
            if not profile.embedding:
                continue
            
            # Calculate embedding similarity
            profile_embedding = np.array(profile.embedding)
            similarity = self._calculate_similarity(embedding, profile_embedding)
            
            # Boost similarity based on voice characteristics match
            if voice_characteristics and profile.voice_characteristics:
                char_similarity = self._calculate_characteristic_similarity(
                    voice_characteristics, 
                    profile.voice_characteristics
                )
                similarity = 0.8 * similarity + 0.2 * char_similarity
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = speaker_id
        
        # Check if similarity meets threshold
        if best_similarity >= self.similarity_threshold:
            return best_match, best_similarity
        
        return None, best_similarity
    
    def _calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings"""
        try:
            # Normalize embeddings
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Cosine similarity
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            
            # Convert to 0-1 range
            return (similarity + 1) / 2
            
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0
    
    def _calculate_characteristic_similarity(self, 
                                           chars1: Dict[str, Any], 
                                           chars2: Dict[str, Any]) -> float:
        """Calculate similarity between voice characteristics"""
        try:
            # Compare numerical characteristics
            numerical_keys = ['embedding_norm', 'embedding_mean', 'embedding_std']
            similarities = []
            
            for key in numerical_keys:
                if key in chars1 and key in chars2:
                    val1, val2 = chars1[key], chars2[key]
                    if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                        # Normalized difference
                        max_val = max(abs(val1), abs(val2), 1e-6)
                        similarity = 1.0 - abs(val1 - val2) / max_val
                        similarities.append(max(0.0, similarity))
            
            # Compare categorical characteristics
            if 'voice_type' in chars1 and 'voice_type' in chars2:
                type_similarity = 1.0 if chars1['voice_type'] == chars2['voice_type'] else 0.0
                similarities.append(type_similarity)
            
            return np.mean(similarities) if similarities else 0.0
            
        except Exception as e:
            logger.error(f"Failed to calculate characteristic similarity: {e}")
            return 0.0
    
    def get_speaker_timeline(self, speaker_id: str) -> List[Dict[str, Any]]:
        """Get recognition timeline for a speaker"""
        timeline = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT recording_id, recognized_as, confidence, timestamp, audio_path
                    FROM recognition_history 
                    WHERE speaker_id = ? OR recognized_as = ?
                    ORDER BY timestamp DESC
                """, (speaker_id, speaker_id))
                
                for row in cursor.fetchall():
                    timeline.append({
                        'recording_id': row[0],
                        'recognized_as': row[1],
                        'confidence': row[2],
                        'timestamp': row[3],
                        'audio_path': row[4]
                    })
        except Exception as e:
            logger.error(f"Failed to get speaker timeline: {e}")
        
        return timeline
    
    def log_recognition(self, 
                       recording_id: str,
                       speaker_id: str,
                       recognized_as: Optional[str],
                       confidence: float,
                       audio_path: str):
        """Log a recognition event"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO recognition_history 
                    (recording_id, speaker_id, recognized_as, confidence, timestamp, audio_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    recording_id,
                    speaker_id,
                    recognized_as,
                    confidence,
                    datetime.now().isoformat(),
                    audio_path
                ))
        except Exception as e:
            logger.error(f"Failed to log recognition: {e}")
    
    def _save_profile(self, profile: SpeakerProfile):
        """Save speaker profile to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO speaker_profiles 
                    (speaker_id, name, embedding, voice_characteristics, speaking_patterns,
                     recognition_confidence, total_speaking_time, recording_count, 
                     last_updated, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    profile.speaker_id,
                    profile.name,
                    json.dumps(profile.embedding) if profile.embedding else None,
                    json.dumps(profile.voice_characteristics),
                    json.dumps(profile.speaking_patterns),
                    profile.recognition_confidence,
                    profile.total_speaking_time,
                    profile.recording_count,
                    profile.last_updated,
                    json.dumps(profile.metadata)
                ))
        except Exception as e:
            logger.error(f"Failed to save profile: {e}")
    
    def get_all_profiles(self) -> Dict[str, SpeakerProfile]:
        """Get all speaker profiles"""
        return self._profile_cache.copy()
    
    def get_profile(self, speaker_id: str) -> Optional[SpeakerProfile]:
        """Get a specific speaker profile"""
        return self._profile_cache.get(speaker_id)
    
    def delete_profile(self, speaker_id: str) -> bool:
        """Delete a speaker profile"""
        try:
            if speaker_id in self._profile_cache:
                del self._profile_cache[speaker_id]
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM speaker_profiles WHERE speaker_id = ?", (speaker_id,))
                conn.execute("DELETE FROM recognition_history WHERE speaker_id = ? OR recognized_as = ?", 
                           (speaker_id, speaker_id))
            
            logger.info(f"Deleted speaker profile: {speaker_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete profile: {e}")
            return False
    
    def merge_profiles(self, primary_id: str, secondary_id: str) -> bool:
        """Merge two speaker profiles"""
        try:
            primary_profile = self._profile_cache.get(primary_id)
            secondary_profile = self._profile_cache.get(secondary_id)
            
            if not primary_profile or not secondary_profile:
                logger.error("Both profiles must exist for merging")
                return False
            
            # Merge embeddings (weighted average)
            if primary_profile.embedding and secondary_profile.embedding:
                primary_emb = np.array(primary_profile.embedding)
                secondary_emb = np.array(secondary_profile.embedding)
                
                # Weight by recording count
                total_recordings = primary_profile.recording_count + secondary_profile.recording_count
                primary_weight = primary_profile.recording_count / total_recordings
                secondary_weight = secondary_profile.recording_count / total_recordings
                
                merged_embedding = primary_weight * primary_emb + secondary_weight * secondary_emb
                primary_profile.embedding = merged_embedding.tolist()
            
            # Merge statistics
            primary_profile.total_speaking_time += secondary_profile.total_speaking_time
            primary_profile.recording_count += secondary_profile.recording_count
            
            # Merge characteristics and patterns
            primary_profile.voice_characteristics.update(secondary_profile.voice_characteristics)
            primary_profile.speaking_patterns.update(secondary_profile.speaking_patterns)
            
            # Update metadata
            primary_profile.metadata['merged_from'] = secondary_id
            primary_profile.last_updated = datetime.now().isoformat()
            
            # Save updated primary profile
            self._save_profile(primary_profile)
            
            # Update recognition history
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE recognition_history 
                    SET recognized_as = ? 
                    WHERE recognized_as = ?
                """, (primary_id, secondary_id))
                
                conn.execute("""
                    UPDATE recognition_history 
                    SET speaker_id = ? 
                    WHERE speaker_id = ?
                """, (primary_id, secondary_id))
            
            # Delete secondary profile
            self.delete_profile(secondary_id)
            
            logger.info(f"Merged speaker profiles: {secondary_id} -> {primary_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to merge profiles: {e}")
            return False
    
    def export_profiles(self, export_path: str) -> bool:
        """Export all profiles to JSON file"""
        try:
            export_data = {
                'profiles': {sid: profile.to_dict() for sid, profile in self._profile_cache.items()},
                'export_timestamp': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Exported {len(self._profile_cache)} profiles to {export_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export profiles: {e}")
            return False
    
    def import_profiles(self, import_path: str) -> bool:
        """Import profiles from JSON file"""
        try:
            with open(import_path, 'r') as f:
                import_data = json.load(f)
            
            profiles_data = import_data.get('profiles', {})
            imported_count = 0
            
            for speaker_id, profile_data in profiles_data.items():
                profile = SpeakerProfile.from_dict(profile_data)
                self._profile_cache[speaker_id] = profile
                self._save_profile(profile)
                imported_count += 1
            
            logger.info(f"Imported {imported_count} profiles from {import_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to import profiles: {e}")
            return False