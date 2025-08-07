"""
Comprehensive Timestamping System for Audio/Video Transcription

This module provides advanced timestamping capabilities including:
- Word-level timestamps for precise navigation
- Segment timestamps for speakers and topics
- Time codes for audio reference
- Clickable transcript synchronization
- Bookmark system for important moments

Requirements: 3.1, 7.4
Tools: Gentle, pyAudioAnalysis, Audioread, Elan
"""

import json
import logging
import math
import os
import sqlite3
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from decimal import Decimal, getcontext
from typing import List, Dict, Optional, Tuple, Any, Union
import wave
import numpy as np
from pathlib import Path

# Set decimal precision for high-precision timestamps
getcontext().prec = 10

# Audio processing libraries
try:
    import librosa
    import soundfile as sf
    from scipy import signal
    import webrtcvad
except ImportError as e:
    logging.warning(f"Audio processing libraries not available: {e}")
    librosa = None
    sf = None
    signal = None
    webrtcvad = None

# Database setup
DATABASE_PATH = "timestamping_system.db"

@dataclass
class WordTimestamp:
    """Word-level timestamp with confidence scoring using Decimal precision"""
    word: str
    start_time: Union[float, Decimal]
    end_time: Union[float, Decimal]
    confidence: Union[float, Decimal]
    speaker_id: Optional[str] = None
    segment_id: Optional[str] = None
    
    def __post_init__(self):
        # Convert to Decimal for high precision
        self.start_time = Decimal(str(self.start_time))
        self.end_time = Decimal(str(self.end_time))
        self.confidence = Decimal(str(self.confidence))
    
    def duration(self) -> Decimal:
        return self.end_time - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            'word': self.word,
            'start_time': float(self.start_time),
            'end_time': float(self.end_time),
            'confidence': float(self.confidence),
            'speaker_id': self.speaker_id,
            'segment_id': self.segment_id,
            'duration': float(self.duration())
        }
        return data

@dataclass
class SegmentTimestamp:
    """Segment-level timestamp for speakers or topics with Decimal precision"""
    id: str
    start_time: Union[float, Decimal]
    end_time: Union[float, Decimal]
    segment_type: str  # 'speaker', 'topic', 'silence', 'music'
    content: str
    speaker_id: Optional[str] = None
    topic: Optional[str] = None
    confidence: Union[float, Decimal] = Decimal('1.0')
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        # Convert to Decimal for high precision
        self.start_time = Decimal(str(self.start_time))
        self.end_time = Decimal(str(self.end_time))
        self.confidence = Decimal(str(self.confidence))
    
    def duration(self) -> Decimal:
        return self.end_time - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'start_time': float(self.start_time),
            'end_time': float(self.end_time),
            'segment_type': self.segment_type,
            'content': self.content,
            'speaker_id': self.speaker_id,
            'topic': self.topic,
            'confidence': float(self.confidence),
            'metadata': self.metadata,
            'duration': float(self.duration())
        }

@dataclass
class TimeCode:
    """Time code reference for easy navigation with Decimal precision"""
    timestamp: Union[float, Decimal]
    label: str
    description: Optional[str] = None
    category: str = "general"  # 'chapter', 'topic', 'speaker_change', 'bookmark'
    
    def __post_init__(self):
        # Convert to Decimal for high precision
        self.timestamp = Decimal(str(self.timestamp))
    
    def format_time(self, format_type: str = "hms") -> str:
        """Format timestamp in various formats with high precision"""
        timestamp_float = float(self.timestamp)
        
        if format_type == "hms":
            hours = int(timestamp_float // 3600)
            minutes = int((timestamp_float % 3600) // 60)
            seconds = int(timestamp_float % 60)
            milliseconds = int((timestamp_float % 1) * 1000)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
        elif format_type == "ms":
            minutes = int(timestamp_float // 60)
            seconds = timestamp_float % 60
            return f"{minutes:02d}:{seconds:06.3f}"
        elif format_type == "seconds":
            return f"{self.timestamp:.6f}s"
        elif format_type == "precise":
            return f"{self.timestamp:.9f}s"
        return str(self.timestamp)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': float(self.timestamp),
            'label': self.label,
            'description': self.description,
            'category': self.category
        }

@dataclass
class Bookmark:
    """Bookmark for important moments with Decimal precision"""
    id: str
    timestamp: Union[float, Decimal]
    title: str
    description: Optional[str] = None
    tags: List[str] = None
    created_at: datetime = None
    user_id: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.now()
        # Convert to Decimal for high precision
        self.timestamp = Decimal(str(self.timestamp))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'timestamp': float(self.timestamp),
            'title': self.title,
            'description': self.description,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'user_id': self.user_id
        }

@dataclass
class TranscriptSegment:
    """Enhanced transcript segment with timing using Decimal precision"""
    text: str
    start_time: Union[float, Decimal]
    end_time: Union[float, Decimal]
    words: List[WordTimestamp]
    speaker_id: Optional[str] = None
    confidence: Union[float, Decimal] = Decimal('1.0')
    is_clickable: bool = True
    
    def __post_init__(self):
        # Convert to Decimal for high precision
        self.start_time = Decimal(str(self.start_time))
        self.end_time = Decimal(str(self.end_time))
        self.confidence = Decimal(str(self.confidence))
    
    def get_word_at_time(self, timestamp: Union[float, Decimal]) -> Optional[WordTimestamp]:
        """Get the word being spoken at a specific timestamp"""
        timestamp = Decimal(str(timestamp))
        for word in self.words:
            if word.start_time <= timestamp <= word.end_time:
                return word
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'text': self.text,
            'start_time': float(self.start_time),
            'end_time': float(self.end_time),
            'words': [word.to_dict() for word in self.words],
            'speaker_id': self.speaker_id,
            'confidence': float(self.confidence),
            'is_clickable': self.is_clickable
        }

class TimestampingSystem:
    """Comprehensive timestamping system for audio/video content"""
    
    def __init__(self, database_path: str = DATABASE_PATH):
        self.database_path = database_path
        self.logger = logging.getLogger(__name__)
        self._init_database()
        
        # Audio analysis parameters
        self.sample_rate = 16000
        self.frame_duration = 30  # ms for VAD
        self.vad_aggressiveness = 2
        
    def _init_database(self):
        """Initialize SQLite database for storing timestamps and bookmarks"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Word timestamps table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS word_timestamps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_id TEXT NOT NULL,
                    word TEXT NOT NULL,
                    start_time REAL NOT NULL,
                    end_time REAL NOT NULL,
                    confidence REAL NOT NULL,
                    speaker_id TEXT,
                    segment_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Segment timestamps table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS segment_timestamps (
                    id TEXT PRIMARY KEY,
                    content_id TEXT NOT NULL,
                    start_time REAL NOT NULL,
                    end_time REAL NOT NULL,
                    segment_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    speaker_id TEXT,
                    topic TEXT,
                    confidence REAL DEFAULT 1.0,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Time codes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS time_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    label TEXT NOT NULL,
                    description TEXT,
                    category TEXT DEFAULT 'general',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Bookmarks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id TEXT PRIMARY KEY,
                    content_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    tags TEXT,
                    user_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Transcript segments table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transcript_segments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    start_time REAL NOT NULL,
                    end_time REAL NOT NULL,
                    speaker_id TEXT,
                    confidence REAL DEFAULT 1.0,
                    is_clickable BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_word_timestamps_content_time ON word_timestamps(content_id, start_time)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_segment_timestamps_content_time ON segment_timestamps(content_id, start_time)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bookmarks_content_time ON bookmarks(content_id, timestamp)')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Database initialization error: {e}")
            raise
    
    def generate_word_timestamps(self, audio_path: str, transcript: str, 
                                content_id: str, method: str = "forced_alignment") -> List[WordTimestamp]:
        """
        Generate word-level timestamps using various methods
        
        Args:
            audio_path: Path to audio file
            transcript: Text transcript
            content_id: Unique identifier for content
            method: Alignment method ('forced_alignment', 'vad_based', 'ml_based')
        """
        try:
            if method == "forced_alignment":
                return self._forced_alignment_timestamps(audio_path, transcript, content_id)
            elif method == "vad_based":
                return self._vad_based_timestamps(audio_path, transcript, content_id)
            elif method == "ml_based":
                return self._ml_based_timestamps(audio_path, transcript, content_id)
            else:
                raise ValueError(f"Unknown timestamping method: {method}")
                
        except Exception as e:
            self.logger.error(f"Word timestamp generation error: {e}")
            # Fallback to simple time-based estimation
            return self._estimate_word_timestamps(transcript, audio_path, content_id)
    
    def _forced_alignment_timestamps(self, audio_path: str, transcript: str, 
                                   content_id: str) -> List[WordTimestamp]:
        """Generate timestamps using forced alignment (Gentle-like approach)"""
        try:
            if not librosa:
                raise ImportError("librosa required for forced alignment")
            
            # Load audio
            audio, sr = librosa.load(audio_path, sr=self.sample_rate)
            duration = len(audio) / sr
            
            # Split transcript into words
            words = transcript.split()
            if not words:
                return []
            
            # Simple forced alignment simulation
            # In production, this would use a proper forced alignment tool like Gentle
            word_timestamps = []
            words_per_second = len(words) / duration
            
            for i, word in enumerate(words):
                start_time = i / words_per_second
                end_time = (i + 1) / words_per_second
                
                # Add some variation based on word length
                word_duration = len(word) * 0.1  # Rough estimate
                adjustment = min(word_duration, 0.5)
                end_time = start_time + adjustment
                
                # Ensure we don't exceed audio duration
                end_time = min(end_time, duration)
                
                confidence = self._calculate_alignment_confidence(audio, start_time, end_time, word)
                
                word_timestamps.append(WordTimestamp(
                    word=word,
                    start_time=start_time,
                    end_time=end_time,
                    confidence=confidence
                ))
            
            # Store in database
            self._store_word_timestamps(content_id, word_timestamps)
            return word_timestamps
            
        except Exception as e:
            self.logger.error(f"Forced alignment error: {e}")
            return self._estimate_word_timestamps(transcript, audio_path, content_id)
    
    def _vad_based_timestamps(self, audio_path: str, transcript: str, 
                            content_id: str) -> List[WordTimestamp]:
        """Generate timestamps using Voice Activity Detection"""
        try:
            if not webrtcvad or not librosa:
                raise ImportError("webrtcvad and librosa required for VAD-based timestamping")
            
            # Load audio
            audio, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Convert to 16-bit PCM - handle both numpy arrays and lists
            if isinstance(audio, list):
                audio = np.array(audio)
            audio_int16 = (audio * 32767).astype(np.int16)
            
            # Initialize VAD
            vad = webrtcvad.Vad(self.vad_aggressiveness)
            
            # Frame parameters
            frame_duration_ms = self.frame_duration
            frame_length = int(self.sample_rate * frame_duration_ms / 1000)
            
            # Detect speech segments
            speech_segments = []
            for i in range(0, len(audio_int16) - frame_length, frame_length):
                frame = audio_int16[i:i + frame_length].tobytes()
                is_speech = vad.is_speech(frame, self.sample_rate)
                
                if is_speech:
                    start_time = i / self.sample_rate
                    end_time = (i + frame_length) / self.sample_rate
                    speech_segments.append((start_time, end_time))
            
            # Merge consecutive speech segments
            merged_segments = self._merge_speech_segments(speech_segments)
            
            # Align words to speech segments
            words = transcript.split()
            word_timestamps = self._align_words_to_segments(words, merged_segments)
            
            # Store in database
            self._store_word_timestamps(content_id, word_timestamps)
            return word_timestamps
            
        except Exception as e:
            self.logger.error(f"VAD-based timestamping error: {e}")
            return self._estimate_word_timestamps(transcript, audio_path, content_id)
    
    def _ml_based_timestamps(self, audio_path: str, transcript: str, 
                           content_id: str) -> List[WordTimestamp]:
        """Generate timestamps using ML-based approach (placeholder for advanced models)"""
        try:
            # This would integrate with advanced ML models like Wav2Vec2 with CTC
            # For now, we'll use a hybrid approach combining audio features and text
            
            if not librosa:
                raise ImportError("librosa required for ML-based timestamping")
            
            # Load audio and extract features
            audio, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Extract MFCC features
            mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
            
            # Extract spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sr)
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)
            
            # Combine features for word boundary detection
            features = np.vstack([mfcc, spectral_centroids, spectral_rolloff])
            
            # Simple word boundary detection based on feature changes
            words = transcript.split()
            word_boundaries = self._detect_word_boundaries(features, len(words))
            
            # Create word timestamps
            word_timestamps = []
            for i, word in enumerate(words):
                if i < len(word_boundaries) - 1:
                    start_time = word_boundaries[i] / sr
                    end_time = word_boundaries[i + 1] / sr
                else:
                    start_time = word_boundaries[i] / sr if i < len(word_boundaries) else 0
                    end_time = len(audio) / sr
                
                confidence = self._calculate_ml_confidence(features, start_time, end_time)
                
                word_timestamps.append(WordTimestamp(
                    word=word,
                    start_time=start_time,
                    end_time=end_time,
                    confidence=confidence
                ))
            
            # Store in database
            self._store_word_timestamps(content_id, word_timestamps)
            return word_timestamps
            
        except Exception as e:
            self.logger.error(f"ML-based timestamping error: {e}")
            return self._estimate_word_timestamps(transcript, audio_path, content_id)
    
    def _estimate_word_timestamps(self, transcript: str, audio_path: str, 
                                content_id: str) -> List[WordTimestamp]:
        """Fallback method for word timestamp estimation"""
        try:
            # Get audio duration
            duration = None
            
            # Try different methods to get audio duration
            if os.path.exists(audio_path):
                try:
                    if librosa:
                        audio, sr = librosa.load(audio_path, sr=None)
                        duration = len(audio) / sr
                except Exception:
                    try:
                        # Fallback using wave module
                        with wave.open(audio_path, 'rb') as wav_file:
                            frames = wav_file.getnframes()
                            sample_rate = wav_file.getframerate()
                            duration = frames / sample_rate
                    except Exception:
                        duration = None
            
            # If we can't get duration from audio, estimate from text
            if duration is None:
                # Estimate duration based on text length (average speaking rate)
                words = transcript.split()
                estimated_words_per_minute = 150  # Average speaking rate
                duration = (len(words) / estimated_words_per_minute) * 60
            
            words = transcript.split()
            if not words:
                return []
            
            # Simple linear distribution
            word_timestamps = []
            time_per_word = duration / len(words)
            
            for i, word in enumerate(words):
                start_time = i * time_per_word
                end_time = (i + 1) * time_per_word
                
                # Adjust based on word length (longer words get more time)
                word_length_factor = len(word) / 5.0  # Average word length
                adjustment = time_per_word * 0.2 * word_length_factor
                end_time = start_time + time_per_word + adjustment
                
                # Ensure we don't exceed duration
                end_time = min(end_time, duration)
                
                word_timestamps.append(WordTimestamp(
                    word=word,
                    start_time=start_time,
                    end_time=end_time,
                    confidence=0.7  # Lower confidence for estimation
                ))
            
            # Store in database
            self._store_word_timestamps(content_id, word_timestamps)
            return word_timestamps
            
        except Exception as e:
            self.logger.error(f"Word timestamp estimation error: {e}")
            return []
    
    def _merge_speech_segments(self, segments: List[Tuple[float, float]], gap_threshold: float = 0.2) -> List[Tuple[float, float]]:
        """Merge consecutive speech segments with small gaps"""
        if not segments:
            return []
        
        # Sort segments by start time
        sorted_segments = sorted(segments, key=lambda x: x[0])
        merged = [sorted_segments[0]]
        
        for current_start, current_end in sorted_segments[1:]:
            last_start, last_end = merged[-1]
            
            # Calculate gap between segments
            gap = current_start - last_end
            
            # If gap is small enough (or negative for overlapping), merge segments
            # Use small epsilon to handle floating-point precision issues
            if gap <= gap_threshold + 1e-10:
                merged[-1] = (last_start, max(last_end, current_end))
            else:
                merged.append((current_start, current_end))
        
        return merged
    
    def _align_words_to_segments(self, words: List[str], segments: List[Tuple[float, float]]) -> List[WordTimestamp]:
        """Align words to speech segments"""
        word_timestamps = []
        
        if not segments or not words:
            return word_timestamps
        
        # Calculate total speech time
        total_speech_time = sum(end - start for start, end in segments)
        
        # Distribute words across segments proportionally
        word_index = 0
        for segment_start, segment_end in segments:
            segment_duration = segment_end - segment_start
            words_in_segment = max(1, int(len(words) * (segment_duration / total_speech_time)))
            
            # Don't exceed remaining words
            words_in_segment = min(words_in_segment, len(words) - word_index)
            
            if words_in_segment > 0:
                time_per_word = segment_duration / words_in_segment
                
                for i in range(words_in_segment):
                    if word_index < len(words):
                        start_time = segment_start + (i * time_per_word)
                        end_time = segment_start + ((i + 1) * time_per_word)
                        
                        word_timestamps.append(WordTimestamp(
                            word=words[word_index],
                            start_time=start_time,
                            end_time=end_time,
                            confidence=0.8  # VAD-based confidence
                        ))
                        word_index += 1
        
        # Handle any remaining words
        if word_index < len(words) and segments:
            last_segment_end = segments[-1][1]
            remaining_words = len(words) - word_index
            time_per_word = 0.5  # Default duration
            
            for i in range(remaining_words):
                start_time = last_segment_end + (i * time_per_word)
                end_time = start_time + time_per_word
                
                word_timestamps.append(WordTimestamp(
                    word=words[word_index + i],
                    start_time=start_time,
                    end_time=end_time,
                    confidence=0.7
                ))
        
        return word_timestamps
 
    def generate_segment_timestamps(self, audio_path: str, transcript: str, 
                                  content_id: str, speakers: List[str] = None) -> List[SegmentTimestamp]:
        """Generate segment-level timestamps for speakers or topics"""
        try:
            # Load audio for analysis
            if librosa:
                audio, sr = librosa.load(audio_path, sr=self.sample_rate)
                duration = len(audio) / sr
            else:
                with wave.open(audio_path, 'rb') as wav_file:
                    duration = wav_file.getnframes() / wav_file.getframerate()
            
            segments = []
            
            # Split transcript into sentences for topic segmentation
            sentences = self._split_into_sentences(transcript)
            
            if speakers and len(speakers) > 1:
                # Speaker-based segmentation
                segments = self._create_speaker_segments(sentences, duration, speakers, content_id)
            else:
                # Topic-based segmentation
                segments = self._create_topic_segments(sentences, duration, content_id)
            
            # Store in database
            self._store_segment_timestamps(content_id, segments)
            return segments
            
        except Exception as e:
            self.logger.error(f"Segment timestamp generation error: {e}")
            return []
    
    def create_time_codes(self, content_id: str, segments: List[SegmentTimestamp], 
                         bookmarks: List[Bookmark] = None) -> List[TimeCode]:
        """Create time codes for easy navigation"""
        try:
            time_codes = []
            
            # Create time codes from segments
            for segment in segments:
                if segment.segment_type == "speaker":
                    label = f"Speaker {segment.speaker_id}" if segment.speaker_id else "Speaker Change"
                    time_codes.append(TimeCode(
                        timestamp=segment.start_time,
                        label=label,
                        description=segment.content[:100] + "..." if len(segment.content) > 100 else segment.content,
                        category="speaker_change"
                    ))
                elif segment.segment_type == "topic":
                    time_codes.append(TimeCode(
                        timestamp=segment.start_time,
                        label=f"Topic: {segment.topic}" if segment.topic else "Topic Change",
                        description=segment.content[:100] + "..." if len(segment.content) > 100 else segment.content,
                        category="topic"
                    ))
            
            # Create time codes from bookmarks
            if bookmarks:
                for bookmark in bookmarks:
                    time_codes.append(TimeCode(
                        timestamp=bookmark.timestamp,
                        label=bookmark.title,
                        description=bookmark.description,
                        category="bookmark"
                    ))
            
            # Store in database
            self._store_time_codes(content_id, time_codes)
            return time_codes
            
        except Exception as e:
            self.logger.error(f"Time code creation error: {e}")
            return []
    
    def create_clickable_transcript(self, content_id: str, transcript: str, 
                                  word_timestamps: List[WordTimestamp]) -> List[TranscriptSegment]:
        """Create clickable transcript with audio synchronization"""
        try:
            # Group words into sentences or logical segments
            sentences = self._split_into_sentences(transcript)
            transcript_segments = []
            
            word_index = 0
            for sentence in sentences:
                sentence_words = sentence.split()
                segment_words = []
                
                # Find corresponding word timestamps
                for word in sentence_words:
                    if word_index < len(word_timestamps):
                        segment_words.append(word_timestamps[word_index])
                        word_index += 1
                
                if segment_words:
                    start_time = segment_words[0].start_time
                    end_time = segment_words[-1].end_time
                    
                    # Calculate average confidence
                    avg_confidence = sum(w.confidence for w in segment_words) / len(segment_words)
                    
                    transcript_segments.append(TranscriptSegment(
                        text=sentence,
                        start_time=start_time,
                        end_time=end_time,
                        words=segment_words,
                        confidence=avg_confidence,
                        is_clickable=True
                    ))
            
            # Store in database
            self._store_transcript_segments(content_id, transcript_segments)
            return transcript_segments
            
        except Exception as e:
            self.logger.error(f"Clickable transcript creation error: {e}")
            return []
    
    def create_bookmark(self, content_id: str, timestamp: float, title: str, 
                       description: str = None, tags: List[str] = None, 
                       user_id: str = None) -> Bookmark:
        """Create a bookmark for an important moment"""
        try:
            bookmark_id = f"{content_id}_{timestamp}_{int(time.time())}"
            bookmark = Bookmark(
                id=bookmark_id,
                timestamp=timestamp,
                title=title,
                description=description,
                tags=tags or [],
                user_id=user_id
            )
            
            # Store in database
            self._store_bookmark(content_id, bookmark)
            return bookmark
            
        except Exception as e:
            self.logger.error(f"Bookmark creation error: {e}")
            raise
    
    def get_word_at_timestamp(self, content_id: str, timestamp: float) -> Optional[WordTimestamp]:
        """Get the word being spoken at a specific timestamp"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT word, start_time, end_time, confidence, speaker_id, segment_id
                FROM word_timestamps
                WHERE content_id = ? AND start_time <= ? AND end_time >= ?
                ORDER BY start_time
                LIMIT 1
            ''', (content_id, timestamp, timestamp))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return WordTimestamp(
                    word=result[0],
                    start_time=result[1],
                    end_time=result[2],
                    confidence=result[3],
                    speaker_id=result[4],
                    segment_id=result[5]
                )
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting word at timestamp: {e}")
            return None
    
    def get_segment_at_timestamp(self, content_id: str, timestamp: float) -> Optional[SegmentTimestamp]:
        """Get the segment at a specific timestamp"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, start_time, end_time, segment_type, content, speaker_id, topic, confidence, metadata
                FROM segment_timestamps
                WHERE content_id = ? AND start_time <= ? AND end_time >= ?
                ORDER BY start_time
                LIMIT 1
            ''', (content_id, timestamp, timestamp))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                metadata = json.loads(result[8]) if result[8] else {}
                return SegmentTimestamp(
                    id=result[0],
                    start_time=result[1],
                    end_time=result[2],
                    segment_type=result[3],
                    content=result[4],
                    speaker_id=result[5],
                    topic=result[6],
                    confidence=result[7],
                    metadata=metadata
                )
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting segment at timestamp: {e}")
            return None
    
    def get_bookmarks(self, content_id: str, user_id: str = None) -> List[Bookmark]:
        """Get all bookmarks for content"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('''
                    SELECT id, timestamp, title, description, tags, user_id, created_at
                    FROM bookmarks
                    WHERE content_id = ? AND user_id = ?
                    ORDER BY timestamp
                ''', (content_id, user_id))
            else:
                cursor.execute('''
                    SELECT id, timestamp, title, description, tags, user_id, created_at
                    FROM bookmarks
                    WHERE content_id = ?
                    ORDER BY timestamp
                ''', (content_id,))
            
            results = cursor.fetchall()
            conn.close()
            
            bookmarks = []
            for result in results:
                tags = json.loads(result[4]) if result[4] else []
                created_at = datetime.fromisoformat(result[6]) if result[6] else datetime.now()
                
                bookmarks.append(Bookmark(
                    id=result[0],
                    timestamp=result[1],
                    title=result[2],
                    description=result[3],
                    tags=tags,
                    user_id=result[5],
                    created_at=created_at
                ))
            
            return bookmarks
            
        except Exception as e:
            self.logger.error(f"Error getting bookmarks: {e}")
            return []
    
    def search_by_timestamp(self, content_id: str, start_time: float, 
                          end_time: float) -> Dict[str, Any]:
        """Search content within a time range"""
        try:
            result = {
                'words': [],
                'segments': [],
                'bookmarks': [],
                'time_codes': []
            }
            
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Get words in time range
            cursor.execute('''
                SELECT word, start_time, end_time, confidence, speaker_id, segment_id
                FROM word_timestamps
                WHERE content_id = ? AND start_time >= ? AND end_time <= ?
                ORDER BY start_time
            ''', (content_id, start_time, end_time))
            
            for row in cursor.fetchall():
                result['words'].append(WordTimestamp(
                    word=row[0],
                    start_time=row[1],
                    end_time=row[2],
                    confidence=row[3],
                    speaker_id=row[4],
                    segment_id=row[5]
                ).to_dict())
            
            # Get segments in time range
            cursor.execute('''
                SELECT id, start_time, end_time, segment_type, content, speaker_id, topic, confidence, metadata
                FROM segment_timestamps
                WHERE content_id = ? AND start_time >= ? AND end_time <= ?
                ORDER BY start_time
            ''', (content_id, start_time, end_time))
            
            for row in cursor.fetchall():
                metadata = json.loads(row[8]) if row[8] else {}
                result['segments'].append(SegmentTimestamp(
                    id=row[0],
                    start_time=row[1],
                    end_time=row[2],
                    segment_type=row[3],
                    content=row[4],
                    speaker_id=row[5],
                    topic=row[6],
                    confidence=row[7],
                    metadata=metadata
                ).to_dict())
            
            # Get bookmarks in time range
            cursor.execute('''
                SELECT id, timestamp, title, description, tags, user_id, created_at
                FROM bookmarks
                WHERE content_id = ? AND timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp
            ''', (content_id, start_time, end_time))
            
            for row in cursor.fetchall():
                tags = json.loads(row[4]) if row[4] else []
                created_at = datetime.fromisoformat(row[6]) if row[6] else datetime.now()
                result['bookmarks'].append(Bookmark(
                    id=row[0],
                    timestamp=row[1],
                    title=row[2],
                    description=row[3],
                    tags=tags,
                    user_id=row[5],
                    created_at=created_at
                ).to_dict())
            
            conn.close()
            return result
            
        except Exception as e:
            self.logger.error(f"Error searching by timestamp: {e}")
            return {'words': [], 'segments': [], 'bookmarks': [], 'time_codes': []}
    
    def export_timestamps(self, content_id: str, format_type: str = "json") -> str:
        """Export timestamps in various formats"""
        try:
            # Get all timestamp data
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            export_data = {
                'content_id': content_id,
                'exported_at': datetime.now().isoformat(),
                'words': [],
                'segments': [],
                'bookmarks': [],
                'time_codes': []
            }
            
            # Export words
            cursor.execute('''
                SELECT word, start_time, end_time, confidence, speaker_id, segment_id
                FROM word_timestamps
                WHERE content_id = ?
                ORDER BY start_time
            ''', (content_id,))
            
            for row in cursor.fetchall():
                export_data['words'].append({
                    'word': row[0],
                    'start_time': row[1],
                    'end_time': row[2],
                    'confidence': row[3],
                    'speaker_id': row[4],
                    'segment_id': row[5]
                })
            
            # Export segments
            cursor.execute('''
                SELECT id, start_time, end_time, segment_type, content, speaker_id, topic, confidence, metadata
                FROM segment_timestamps
                WHERE content_id = ?
                ORDER BY start_time
            ''', (content_id,))
            
            for row in cursor.fetchall():
                metadata = json.loads(row[8]) if row[8] else {}
                export_data['segments'].append({
                    'id': row[0],
                    'start_time': row[1],
                    'end_time': row[2],
                    'segment_type': row[3],
                    'content': row[4],
                    'speaker_id': row[5],
                    'topic': row[6],
                    'confidence': row[7],
                    'metadata': metadata
                })
            
            # Export bookmarks
            cursor.execute('''
                SELECT id, timestamp, title, description, tags, user_id, created_at
                FROM bookmarks
                WHERE content_id = ?
                ORDER BY timestamp
            ''', (content_id,))
            
            for row in cursor.fetchall():
                tags = json.loads(row[4]) if row[4] else []
                export_data['bookmarks'].append({
                    'id': row[0],
                    'timestamp': row[1],
                    'title': row[2],
                    'description': row[3],
                    'tags': tags,
                    'user_id': row[5],
                    'created_at': row[6]
                })
            
            conn.close()
            
            if format_type == "json":
                return json.dumps(export_data, indent=2)
            elif format_type == "srt":
                return self._export_to_srt(export_data)
            elif format_type == "vtt":
                return self._export_to_vtt(export_data)
            elif format_type == "elan":
                return self._export_to_elan(export_data)
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
                
        except ValueError:
            # Re-raise ValueError for proper error handling
            raise
        except Exception as e:
            self.logger.error(f"Export error: {e}")
            return ""
    
    # Helper methods
    def _calculate_alignment_confidence(self, audio: np.ndarray, start_time: float, 
                                      end_time: float, word: str) -> float:
        """Calculate confidence score for forced alignment"""
        try:
            # Simple confidence calculation based on audio energy and word characteristics
            start_sample = int(start_time * self.sample_rate)
            end_sample = int(end_time * self.sample_rate)
            
            if start_sample >= len(audio) or end_sample >= len(audio):
                return 0.5
            
            segment = audio[start_sample:end_sample]
            energy = np.mean(segment ** 2)
            
            # Normalize energy and combine with word length factor
            energy_score = min(energy * 1000, 1.0)  # Normalize to 0-1
            length_score = min(len(word) / 10.0, 1.0)  # Longer words are more reliable
            
            return (energy_score + length_score) / 2
            
        except Exception:
            return 0.7  # Default confidence
    
    def _merge_speech_segments_duplicate(self, segments: List[Tuple[float, float]], 
                             gap_threshold: float = 0.1) -> List[Tuple[float, float]]:
        """Merge consecutive speech segments with small gaps (duplicate method - to be removed)"""
        if not segments:
            return []
        
        # Sort segments by start time first
        sorted_segments = sorted(segments, key=lambda x: x[0])
        merged = [sorted_segments[0]]
        
        for start, end in sorted_segments[1:]:
            last_end = merged[-1][1]
            
            if start - last_end <= gap_threshold:
                # Merge with previous segment
                merged[-1] = (merged[-1][0], max(end, last_end))
            else:
                merged.append((start, end))
        
        return merged
    
    def _align_words_to_segments(self, words: List[str], 
                               segments: List[Tuple[float, float]]) -> List[WordTimestamp]:
        """Align words to detected speech segments"""
        word_timestamps = []
        
        if not words or not segments:
            return word_timestamps
        
        words_per_segment = len(words) / len(segments)
        word_index = 0
        
        for segment_start, segment_end in segments:
            segment_duration = segment_end - segment_start
            words_in_segment = max(1, int(words_per_segment))
            
            # Don't exceed available words
            words_in_segment = min(words_in_segment, len(words) - word_index)
            
            if words_in_segment > 0:
                time_per_word = segment_duration / words_in_segment
                
                for i in range(words_in_segment):
                    if word_index < len(words):
                        word_start = segment_start + (i * time_per_word)
                        word_end = segment_start + ((i + 1) * time_per_word)
                        
                        word_timestamps.append(WordTimestamp(
                            word=words[word_index],
                            start_time=word_start,
                            end_time=word_end,
                            confidence=0.8
                        ))
                        word_index += 1
        
        return word_timestamps
    
    def _detect_word_boundaries(self, features: np.ndarray, num_words: int) -> List[int]:
        """Detect word boundaries from audio features"""
        try:
            # Calculate feature changes (simple derivative)
            feature_changes = np.sum(np.abs(np.diff(features, axis=1)), axis=0)
            
            # Smooth the changes
            if len(feature_changes) > 10:
                window_size = min(5, len(feature_changes) // 10)
                feature_changes = np.convolve(feature_changes, np.ones(window_size)/window_size, mode='same')
            
            # Find peaks (potential word boundaries)
            if len(feature_changes) > 0:
                threshold = np.mean(feature_changes) + np.std(feature_changes)
                peaks = []
                
                for i in range(1, len(feature_changes) - 1):
                    if (feature_changes[i] > feature_changes[i-1] and 
                        feature_changes[i] > feature_changes[i+1] and 
                        feature_changes[i] > threshold):
                        peaks.append(i)
                
                # Select the most prominent peaks
                if len(peaks) > num_words:
                    # Sort by prominence and take top num_words
                    peak_values = [(i, feature_changes[i]) for i in peaks]
                    peak_values.sort(key=lambda x: x[1], reverse=True)
                    peaks = [x[0] for x in peak_values[:num_words]]
                    peaks.sort()
                
                # Ensure we have enough boundaries
                while len(peaks) < num_words:
                    # Add evenly spaced boundaries
                    if peaks:
                        gap = len(feature_changes) // (num_words - len(peaks) + 1)
                        new_peak = peaks[-1] + gap
                        if new_peak < len(feature_changes):
                            peaks.append(new_peak)
                        else:
                            break
                    else:
                        # No peaks found, use even distribution
                        peaks = [i * len(feature_changes) // num_words for i in range(num_words)]
                        break
                
                return peaks
            
            # Fallback: even distribution
            return [i * len(feature_changes) // num_words for i in range(num_words)]
            
        except Exception:
            # Fallback: even distribution
            return list(range(0, len(features[0]), len(features[0]) // num_words))[:num_words]
    
    def calculate_quality_metrics(self, word_timestamps: List[WordTimestamp], 
                                 content_id: str) -> Dict[str, Any]:
        """Calculate comprehensive quality metrics for timestamps"""
        if not word_timestamps:
            return {
                'overall_score': Decimal('0.0'),
                'rating': 'No Data',
                'metrics': {},
                'recommendations': []
            }
        
        # Convert to Decimal for precise calculations
        confidences = [Decimal(str(w.confidence)) for w in word_timestamps]
        durations = [w.duration() for w in word_timestamps]
        
        # Basic metrics
        total_words = len(word_timestamps)
        total_duration = max(w.end_time for w in word_timestamps)
        avg_confidence = sum(confidences) / total_words
        
        # Realistic words per minute calculation (accounting for pauses)
        # Assume 20% of time is pauses/silence
        effective_speaking_time = total_duration * Decimal('0.8')
        words_per_minute = (Decimal(str(total_words)) / effective_speaking_time) * Decimal('60') if effective_speaking_time > 0 else Decimal('0')
        
        # Confidence distribution
        high_confidence = sum(1 for c in confidences if c >= Decimal('0.9'))
        medium_confidence = sum(1 for c in confidences if Decimal('0.7') <= c < Decimal('0.9'))
        low_confidence = sum(1 for c in confidences if c < Decimal('0.7'))
        
        # Duration consistency (words should have reasonable durations)
        avg_duration = sum(durations) / len(durations)
        duration_variance = sum((d - avg_duration) ** 2 for d in durations) / len(durations)
        duration_consistency = max(Decimal('0'), Decimal('1') - (duration_variance / avg_duration))
        
        # Speaking rate quality (optimal range: 120-180 WPM)
        optimal_wpm_min = Decimal('120')
        optimal_wpm_max = Decimal('180')
        
        if optimal_wpm_min <= words_per_minute <= optimal_wpm_max:
            rate_score = Decimal('1.0')
        elif words_per_minute < optimal_wpm_min:
            rate_score = words_per_minute / optimal_wpm_min
        else:
            # Penalize very fast speech more heavily
            excess = words_per_minute - optimal_wpm_max
            rate_score = max(Decimal('0.1'), Decimal('1.0') - (excess / optimal_wpm_max))
        
        # Timestamp precision (check for overlaps and gaps)
        precision_issues = 0
        for i in range(len(word_timestamps) - 1):
            current_end = word_timestamps[i].end_time
            next_start = word_timestamps[i + 1].start_time
            
            # Check for overlaps or unrealistic gaps
            if current_end > next_start:  # Overlap
                precision_issues += 1
            elif next_start - current_end > Decimal('2.0'):  # Gap > 2 seconds
                precision_issues += 1
        
        precision_score = max(Decimal('0'), Decimal('1') - (Decimal(str(precision_issues)) / Decimal(str(total_words))))
        
        # Calculate overall quality score with improved weighting
        confidence_weight = Decimal('0.4')
        rate_weight = Decimal('0.25')
        precision_weight = Decimal('0.2')
        consistency_weight = Decimal('0.15')
        
        overall_score = (
            avg_confidence * confidence_weight +
            rate_score * rate_weight +
            precision_score * precision_weight +
            duration_consistency * consistency_weight
        )
        
        # Determine rating
        if overall_score >= Decimal('0.9'):
            rating = "Excellent"
        elif overall_score >= Decimal('0.8'):
            rating = "Very Good"
        elif overall_score >= Decimal('0.7'):
            rating = "Good"
        elif overall_score >= Decimal('0.6'):
            rating = "Fair"
        elif overall_score >= Decimal('0.4'):
            rating = "Needs Improvement"
        else:
            rating = "Poor"
        
        # Generate recommendations
        recommendations = []
        
        if avg_confidence < Decimal('0.8'):
            recommendations.append("Improve audio quality for better transcription accuracy")
        
        if words_per_minute > optimal_wpm_max:
            recommendations.append("Speaking rate is fast - consider slowing down for better clarity")
        elif words_per_minute < optimal_wpm_min:
            recommendations.append("Speaking rate is slow - consider increasing pace for better engagement")
        
        if low_confidence > total_words * 0.3:
            recommendations.append("High number of low-confidence words - check audio quality and background noise")
        
        if precision_issues > total_words * 0.1:
            recommendations.append("Timestamp precision issues detected - consider using better alignment methods")
        
        if duration_consistency < Decimal('0.7'):
            recommendations.append("Inconsistent word durations - may indicate audio processing issues")
        
        return {
            'overall_score': overall_score,
            'rating': rating,
            'metrics': {
                'total_words': total_words,
                'total_duration': float(total_duration),
                'avg_confidence': float(avg_confidence),
                'words_per_minute': float(words_per_minute),
                'confidence_distribution': {
                    'high': high_confidence,
                    'medium': medium_confidence,
                    'low': low_confidence
                },
                'duration_consistency': float(duration_consistency),
                'precision_score': float(precision_score),
                'rate_score': float(rate_score)
            },
            'recommendations': recommendations
        }
    
    def _calculate_ml_confidence(self, features: np.ndarray, start_time: float, 
                               end_time: float) -> float:
        """Calculate confidence score for ML-based timestamping"""
        try:
            # Simple confidence based on feature stability
            start_frame = int(start_time * self.sample_rate / 512)  # Assuming hop_length=512
            end_frame = int(end_time * self.sample_rate / 512)
            
            if start_frame >= features.shape[1] or end_frame >= features.shape[1]:
                return 0.6
            
            segment_features = features[:, start_frame:end_frame]
            
            if segment_features.shape[1] > 1:
                # Calculate feature variance (lower variance = higher confidence)
                variance = np.mean(np.var(segment_features, axis=1))
                confidence = max(0.3, 1.0 - min(variance, 1.0))
            else:
                confidence = 0.6
            
            return confidence
            
        except Exception:
            return 0.6
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        import re
        
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def _create_speaker_segments(self, sentences: List[str], duration: float, 
                               speakers: List[str], content_id: str) -> List[SegmentTimestamp]:
        """Create speaker-based segments"""
        segments = []
        time_per_sentence = duration / len(sentences) if sentences else 0
        
        for i, sentence in enumerate(sentences):
            start_time = i * time_per_sentence
            end_time = (i + 1) * time_per_sentence
            
            # Simple speaker assignment (in practice, this would use speaker diarization)
            speaker_id = speakers[i % len(speakers)]
            
            segment_id = f"{content_id}_speaker_{i}"
            segments.append(SegmentTimestamp(
                id=segment_id,
                start_time=start_time,
                end_time=end_time,
                segment_type="speaker",
                content=sentence,
                speaker_id=speaker_id,
                confidence=0.8
            ))
        
        return segments
    
    def _create_topic_segments(self, sentences: List[str], duration: float, 
                             content_id: str) -> List[SegmentTimestamp]:
        """Create topic-based segments"""
        segments = []
        time_per_sentence = duration / len(sentences) if sentences else 0
        
        # Simple topic segmentation (group sentences)
        sentences_per_topic = max(1, len(sentences) // 5)  # Roughly 5 topics
        
        for i in range(0, len(sentences), sentences_per_topic):
            topic_sentences = sentences[i:i + sentences_per_topic]
            start_time = i * time_per_sentence
            end_time = min((i + len(topic_sentences)) * time_per_sentence, duration)
            
            content = " ".join(topic_sentences)
            topic = f"Topic {i // sentences_per_topic + 1}"
            
            segment_id = f"{content_id}_topic_{i // sentences_per_topic}"
            segments.append(SegmentTimestamp(
                id=segment_id,
                start_time=start_time,
                end_time=end_time,
                segment_type="topic",
                content=content,
                topic=topic,
                confidence=0.7
            ))
        
        return segments
    
    # Database storage methods
    def _store_word_timestamps(self, content_id: str, word_timestamps: List[WordTimestamp]):
        """Store word timestamps in database"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Clear existing timestamps for this content
            cursor.execute('DELETE FROM word_timestamps WHERE content_id = ?', (content_id,))
            
            # Insert new timestamps
            for word_ts in word_timestamps:
                cursor.execute('''
                    INSERT INTO word_timestamps (content_id, word, start_time, end_time, confidence, speaker_id, segment_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (content_id, word_ts.word, float(word_ts.start_time), float(word_ts.end_time), 
                     float(word_ts.confidence), word_ts.speaker_id, word_ts.segment_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing word timestamps: {e}")
    
    def _store_segment_timestamps(self, content_id: str, segments: List[SegmentTimestamp]):
        """Store segment timestamps in database"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Clear existing segments for this content
            cursor.execute('DELETE FROM segment_timestamps WHERE content_id = ?', (content_id,))
            
            # Insert new segments
            for segment in segments:
                metadata_json = json.dumps(segment.metadata) if segment.metadata else None
                cursor.execute('''
                    INSERT INTO segment_timestamps (id, content_id, start_time, end_time, segment_type, content, speaker_id, topic, confidence, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (segment.id, content_id, float(segment.start_time), float(segment.end_time), 
                     segment.segment_type, segment.content, segment.speaker_id, 
                     segment.topic, float(segment.confidence), metadata_json))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing segment timestamps: {e}")
    
    def _store_time_codes(self, content_id: str, time_codes: List[TimeCode]):
        """Store time codes in database"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Clear existing time codes for this content
            cursor.execute('DELETE FROM time_codes WHERE content_id = ?', (content_id,))
            
            # Insert new time codes
            for time_code in time_codes:
                cursor.execute('''
                    INSERT INTO time_codes (content_id, timestamp, label, description, category)
                    VALUES (?, ?, ?, ?, ?)
                ''', (content_id, float(time_code.timestamp), time_code.label, 
                     time_code.description, time_code.category))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing time codes: {e}")
    
    def _store_bookmark(self, content_id: str, bookmark: Bookmark):
        """Store bookmark in database"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            tags_json = json.dumps(bookmark.tags) if bookmark.tags else None
            cursor.execute('''
                INSERT OR REPLACE INTO bookmarks (id, content_id, timestamp, title, description, tags, user_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (bookmark.id, content_id, float(bookmark.timestamp), bookmark.title, 
                 bookmark.description, tags_json, bookmark.user_id, 
                 bookmark.created_at.isoformat()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing bookmark: {e}")
    
    def _store_transcript_segments(self, content_id: str, segments: List[TranscriptSegment]):
        """Store transcript segments in database"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Clear existing transcript segments for this content
            cursor.execute('DELETE FROM transcript_segments WHERE content_id = ?', (content_id,))
            
            # Insert new segments
            for segment in segments:
                cursor.execute('''
                    INSERT INTO transcript_segments (content_id, text, start_time, end_time, speaker_id, confidence, is_clickable)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (content_id, segment.text, float(segment.start_time), float(segment.end_time), 
                     segment.speaker_id, float(segment.confidence), segment.is_clickable))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing transcript segments: {e}")
    
    # Export format methods
    def _export_to_srt(self, data: Dict[str, Any]) -> str:
        """Export to SRT subtitle format"""
        srt_content = []
        
        for i, segment in enumerate(data['segments'], 1):
            start_time = self._format_srt_time(segment['start_time'])
            end_time = self._format_srt_time(segment['end_time'])
            
            srt_content.append(f"{i}")
            srt_content.append(f"{start_time} --> {end_time}")
            srt_content.append(segment['content'])
            srt_content.append("")
        
        return "\n".join(srt_content)
    
    def _export_to_vtt(self, data: Dict[str, Any]) -> str:
        """Export to WebVTT format"""
        vtt_content = ["WEBVTT", ""]
        
        for segment in data['segments']:
            start_time = self._format_vtt_time(segment['start_time'])
            end_time = self._format_vtt_time(segment['end_time'])
            
            vtt_content.append(f"{start_time} --> {end_time}")
            vtt_content.append(segment['content'])
            vtt_content.append("")
        
        return "\n".join(vtt_content)
    
    def _export_to_elan(self, data: Dict[str, Any]) -> str:
        """Export to ELAN EAF format (simplified)"""
        # This would generate a proper ELAN XML file
        # For now, return a simplified XML structure
        elan_content = ['<?xml version="1.0" encoding="UTF-8"?>']
        elan_content.append('<ANNOTATION_DOCUMENT>')
        elan_content.append('<HEADER>')
        elan_content.append(f'<MEDIA_DESCRIPTOR MEDIA_URL="{data["content_id"]}" />')
        elan_content.append('</HEADER>')
        
        for i, segment in enumerate(data['segments']):
            start_ms = int(segment['start_time'] * 1000)
            end_ms = int(segment['end_time'] * 1000)
            
            elan_content.append(f'<TIER TIER_ID="tier_{i}">')
            elan_content.append(f'<ANNOTATION>')
            elan_content.append(f'<ALIGNABLE_ANNOTATION TIME_SLOT_REF1="{start_ms}" TIME_SLOT_REF2="{end_ms}">')
            elan_content.append(f'<ANNOTATION_VALUE>{segment["content"]}</ANNOTATION_VALUE>')
            elan_content.append('</ALIGNABLE_ANNOTATION>')
            elan_content.append('</ANNOTATION>')
            elan_content.append('</TIER>')
        
        elan_content.append('</ANNOTATION_DOCUMENT>')
        return "\n".join(elan_content)
    
    def _format_srt_time(self, seconds: float) -> str:
        """Format time for SRT format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def _format_vtt_time(self, seconds: float) -> str:
        """Format time for VTT format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


# Example usage and testing
if __name__ == "__main__":
    # Initialize the timestamping system
    ts_system = TimestampingSystem()
    
    # Example content
    content_id = "test_audio_001"
    transcript = "Hello world. This is a test transcript. We are testing the timestamping system."
    
    # This would normally be a real audio file
    # For testing, we'll simulate the process
    print("Timestamping System initialized successfully!")
    print(f"Database path: {ts_system.database_path}")
    
    # Test bookmark creation
    bookmark = ts_system.create_bookmark(
        content_id=content_id,
        timestamp=15.5,
        title="Important moment",
        description="This is where the key point was made",
        tags=["important", "key-point"],
        user_id="user123"
    )
    
    print(f"Created bookmark: {bookmark.title} at {bookmark.timestamp}s")