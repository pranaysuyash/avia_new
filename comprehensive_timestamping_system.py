#!/usr/bin/env python3
"""
Comprehensive Timestamping System
Task 231: Add word-level timestamps, segment timestamps, interactive navigation,
clickable transcripts with audio synchronization, and bookmark system.
"""

import asyncio
import json
import os
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
import hashlib
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TimestampType(Enum):
    """Types of timestamps."""
    WORD_LEVEL = "word_level"
    SENTENCE_LEVEL = "sentence_level"
    PARAGRAPH_LEVEL = "paragraph_level"
    SPEAKER_SEGMENT = "speaker_segment"
    TOPIC_SEGMENT = "topic_segment"
    CHAPTER = "chapter"
    BOOKMARK = "bookmark"

class BookmarkCategory(Enum):
    """Bookmark categories."""
    IMPORTANT = "important"
    ACTION_ITEM = "action_item"
    KEY_POINT = "key_point"
    QUESTION = "question"
    DECISION = "decision"
    FOLLOW_UP = "follow_up"
    CUSTOM = "custom"

class NavigationMode(Enum):
    """Navigation modes."""
    CONTINUOUS = "continuous"
    SENTENCE_BY_SENTENCE = "sentence_by_sentence"
    PARAGRAPH_BY_PARAGRAPH = "paragraph_by_paragraph"
    SPEAKER_BY_SPEAKER = "speaker_by_speaker"
    BOOKMARK_TO_BOOKMARK = "bookmark_to_bookmark"

@dataclass
class WordTimestamp:
    """Individual word timestamp information."""
    word: str
    start_time: float
    end_time: float
    confidence: float
    speaker_id: Optional[str] = None
    word_index: int = 0
    is_punctuation: bool = False
    phonemes: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SegmentTimestamp:
    """Segment-level timestamp information."""
    segment_id: str
    segment_type: TimestampType
    text: str
    start_time: float
    end_time: float
    words: List[WordTimestamp]
    speaker_id: Optional[str] = None
    confidence: float = 0.0
    topic: Optional[str] = None
    chapter_title: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Bookmark:
    """Bookmark with timestamp and metadata."""
    bookmark_id: str
    title: str
    description: str
    timestamp: float
    category: BookmarkCategory
    created_at: datetime
    created_by: str
    color: str = "#FFD700"  # Gold color by default
    is_shared: bool = False
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TimeCode:
    """Time code for navigation and reference."""
    time_code_id: str
    timestamp: float
    display_format: str  # "HH:MM:SS.mmm", "MM:SS", etc.
    reference_text: str
    url_fragment: Optional[str] = None  # For deep linking
    is_public: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class NavigationPoint:
    """Navigation waypoint."""
    point_id: str
    title: str
    timestamp: float
    point_type: TimestampType
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    auto_generated: bool = True

@dataclass
class TranscriptSession:
    """Complete timestamped transcript session."""
    session_id: str
    title: str
    audio_file_path: str
    duration: float
    transcript_text: str
    word_timestamps: List[WordTimestamp]
    segment_timestamps: List[SegmentTimestamp]
    bookmarks: List[Bookmark]
    time_codes: List[TimeCode]
    navigation_points: List[NavigationPoint]
    speakers: Dict[str, str]  # speaker_id -> name
    chapters: List[Dict[str, Any]]
    created_at: datetime
    last_modified: datetime
    playback_speed: float = 1.0
    current_position: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class WordLevelTimestamper:
    """Generates word-level timestamps using forced alignment."""
    
    def __init__(self):
        self.alignment_models = self._initialize_alignment_models()
    
    def _initialize_alignment_models(self) -> Dict[str, Any]:
        """Initialize alignment models for different languages."""
        # In real implementation, would load actual alignment models
        return {
            'en': {'model': 'english_phoneme_model', 'phoneme_set': 'arpabet'},
            'es': {'model': 'spanish_phoneme_model', 'phoneme_set': 'spanish'},
            'fr': {'model': 'french_phoneme_model', 'phoneme_set': 'french'},
            'de': {'model': 'german_phoneme_model', 'phoneme_set': 'german'}
        }
    
    def generate_word_timestamps(self, transcript_text: str, audio_duration: float, 
                                language: str = 'en') -> List[WordTimestamp]:
        """Generate word-level timestamps using forced alignment."""
        words = self._tokenize_text(transcript_text)
        
        # Mock word-level alignment (real implementation would use Gentle, P2FA, or similar)
        word_timestamps = []
        current_time = 0.0
        
        for i, word in enumerate(words):
            # Estimate word duration based on length and speaking rate
            # Typical speaking rate: 150-200 words per minute
            speaking_rate = 180  # words per minute
            
            if word.strip() and not self._is_punctuation(word):
                # Actual words
                estimated_duration = max(0.1, len(word) * 0.08 + 0.2)  # Min 0.1s per word
                confidence = 0.85 + (0.1 * (1 - len(word) / 20))  # Longer words less confident
                
                word_timestamps.append(WordTimestamp(
                    word=word.strip(),
                    start_time=current_time,
                    end_time=current_time + estimated_duration,
                    confidence=min(0.95, confidence),
                    word_index=i,
                    is_punctuation=False,
                    phonemes=self._get_phonemes(word, language)
                ))
                
                current_time += estimated_duration + 0.05  # Small pause between words
            else:
                # Punctuation - no timing but preserve for text structure
                if word.strip():
                    word_timestamps.append(WordTimestamp(
                        word=word.strip(),
                        start_time=current_time,
                        end_time=current_time,
                        confidence=1.0,
                        word_index=i,
                        is_punctuation=True
                    ))
        
        # Normalize to fit actual audio duration
        if word_timestamps and current_time > 0:
            scale_factor = audio_duration / current_time
            for word_ts in word_timestamps:
                word_ts.start_time *= scale_factor
                word_ts.end_time *= scale_factor
        
        return word_timestamps
    
    def _tokenize_text(self, text: str) -> List[str]:
        """Tokenize text into words and punctuation."""
        # Simple tokenization - in real implementation, use advanced tokenizers
        tokens = re.findall(r'\w+|[.,!?;:]', text.lower())
        return tokens
    
    def _is_punctuation(self, word: str) -> bool:
        """Check if token is punctuation."""
        return not word.isalnum()
    
    def _get_phonemes(self, word: str, language: str) -> Optional[List[str]]:
        """Get phoneme representation of word."""
        # Mock phoneme generation - real implementation would use phoneme dictionaries
        if language == 'en':
            # Simple mapping for demo
            phoneme_map = {
                'hello': ['HH', 'AH', 'L', 'OW'],
                'world': ['W', 'ER', 'L', 'D'],
                'time': ['T', 'AY', 'M'],
                'audio': ['AO', 'D', 'IY', 'OW']
            }
            return phoneme_map.get(word.lower())
        return None
    
    def improve_alignment_quality(self, word_timestamps: List[WordTimestamp], 
                                 audio_features: Dict[str, Any]) -> List[WordTimestamp]:
        """Improve alignment quality using audio features."""
        # Mock improvement - real implementation would use speech features
        for word_ts in word_timestamps:
            if not word_ts.is_punctuation:
                # Adjust confidence based on audio quality indicators
                if audio_features.get('snr', 0) > 15:  # Good signal-to-noise ratio
                    word_ts.confidence = min(0.98, word_ts.confidence + 0.05)
                elif audio_features.get('snr', 0) < 5:  # Poor SNR
                    word_ts.confidence = max(0.3, word_ts.confidence - 0.15)
        
        return word_timestamps

class SegmentTimestamper:
    """Generates segment-level timestamps for different types of content."""
    
    def __init__(self):
        self.segment_detectors = self._initialize_segment_detectors()
    
    def _initialize_segment_detectors(self) -> Dict[str, Any]:
        """Initialize different segment detection models."""
        return {
            'sentence': {'model': 'sentence_boundary_detector'},
            'speaker': {'model': 'speaker_diarization_model'},
            'topic': {'model': 'topic_segmentation_model'},
            'chapter': {'model': 'chapter_detection_model'}
        }
    
    def generate_sentence_segments(self, word_timestamps: List[WordTimestamp], 
                                  transcript_text: str) -> List[SegmentTimestamp]:
        """Generate sentence-level segments."""
        segments = []
        current_sentence_words = []
        current_start_time = 0.0
        
        # Split into sentences using punctuation
        sentence_endings = ['.', '!', '?']
        
        for word_ts in word_timestamps:
            if not word_ts.is_punctuation:
                if not current_sentence_words:
                    current_start_time = word_ts.start_time
                current_sentence_words.append(word_ts)
            else:
                if word_ts.word in sentence_endings and current_sentence_words:
                    # Complete sentence
                    sentence_text = ' '.join([w.word for w in current_sentence_words])
                    end_time = current_sentence_words[-1].end_time
                    
                    segment = SegmentTimestamp(
                        segment_id=str(uuid.uuid4()),
                        segment_type=TimestampType.SENTENCE_LEVEL,
                        text=sentence_text,
                        start_time=current_start_time,
                        end_time=end_time,
                        words=current_sentence_words.copy(),
                        confidence=sum(w.confidence for w in current_sentence_words) / len(current_sentence_words)
                    )
                    segments.append(segment)
                    
                    current_sentence_words = []
        
        # Handle remaining words if no final punctuation
        if current_sentence_words:
            sentence_text = ' '.join([w.word for w in current_sentence_words])
            segment = SegmentTimestamp(
                segment_id=str(uuid.uuid4()),
                segment_type=TimestampType.SENTENCE_LEVEL,
                text=sentence_text,
                start_time=current_start_time,
                end_time=current_sentence_words[-1].end_time,
                words=current_sentence_words,
                confidence=sum(w.confidence for w in current_sentence_words) / len(current_sentence_words)
            )
            segments.append(segment)
        
        return segments
    
    def generate_speaker_segments(self, word_timestamps: List[WordTimestamp],
                                 speaker_changes: List[Tuple[float, str]]) -> List[SegmentTimestamp]:
        """Generate speaker-based segments."""
        segments = []
        current_speaker = None
        current_segment_words = []
        current_start_time = 0.0
        
        # Create speaker change lookup
        speaker_change_dict = {timestamp: speaker for timestamp, speaker in speaker_changes}
        
        for word_ts in word_timestamps:
            # Check for speaker change
            new_speaker = None
            for change_time, speaker_id in speaker_changes:
                if change_time <= word_ts.start_time:
                    new_speaker = speaker_id
                else:
                    break
            
            if new_speaker != current_speaker and current_segment_words:
                # Complete current segment
                segment_text = ' '.join([w.word for w in current_segment_words if not w.is_punctuation])
                
                segment = SegmentTimestamp(
                    segment_id=str(uuid.uuid4()),
                    segment_type=TimestampType.SPEAKER_SEGMENT,
                    text=segment_text,
                    start_time=current_start_time,
                    end_time=current_segment_words[-1].end_time,
                    words=current_segment_words.copy(),
                    speaker_id=current_speaker,
                    confidence=sum(w.confidence for w in current_segment_words if not w.is_punctuation) / max(1, len([w for w in current_segment_words if not w.is_punctuation]))
                )
                segments.append(segment)
                
                current_segment_words = []
                current_start_time = word_ts.start_time
            
            if not current_segment_words:
                current_start_time = word_ts.start_time
            
            current_segment_words.append(word_ts)
            word_ts.speaker_id = new_speaker
            current_speaker = new_speaker
        
        # Handle final segment
        if current_segment_words:
            segment_text = ' '.join([w.word for w in current_segment_words if not w.is_punctuation])
            segment = SegmentTimestamp(
                segment_id=str(uuid.uuid4()),
                segment_type=TimestampType.SPEAKER_SEGMENT,
                text=segment_text,
                start_time=current_start_time,
                end_time=current_segment_words[-1].end_time,
                words=current_segment_words,
                speaker_id=current_speaker,
                confidence=sum(w.confidence for w in current_segment_words if not w.is_punctuation) / max(1, len([w for w in current_segment_words if not w.is_punctuation]))
            )
            segments.append(segment)
        
        return segments
    
    def generate_topic_segments(self, sentence_segments: List[SegmentTimestamp]) -> List[SegmentTimestamp]:
        """Generate topic-based segments."""
        # Mock topic segmentation - real implementation would use topic modeling
        topic_segments = []
        current_topic_sentences = []
        current_topic = "introduction"
        
        topic_keywords = {
            'introduction': ['hello', 'welcome', 'introduction', 'begin', 'start'],
            'main_content': ['main', 'important', 'key', 'focus', 'discuss'],
            'conclusion': ['conclusion', 'summary', 'end', 'final', 'thank']
        }
        
        for sentence in sentence_segments:
            # Determine topic based on keywords
            sentence_lower = sentence.text.lower()
            detected_topic = current_topic
            
            for topic, keywords in topic_keywords.items():
                if any(keyword in sentence_lower for keyword in keywords):
                    detected_topic = topic
                    break
            
            if detected_topic != current_topic and current_topic_sentences:
                # Complete current topic segment
                combined_words = []
                for sentence in current_topic_sentences:
                    combined_words.extend(sentence.words)
                
                combined_text = ' '.join([s.text for s in current_topic_sentences])
                
                topic_segment = SegmentTimestamp(
                    segment_id=str(uuid.uuid4()),
                    segment_type=TimestampType.TOPIC_SEGMENT,
                    text=combined_text,
                    start_time=current_topic_sentences[0].start_time,
                    end_time=current_topic_sentences[-1].end_time,
                    words=combined_words,
                    topic=current_topic,
                    confidence=sum(s.confidence for s in current_topic_sentences) / len(current_topic_sentences)
                )
                topic_segments.append(topic_segment)
                
                current_topic_sentences = []
            
            current_topic_sentences.append(sentence)
            current_topic = detected_topic
        
        # Handle final topic segment
        if current_topic_sentences:
            combined_words = []
            for sentence in current_topic_sentences:
                combined_words.extend(sentence.words)
            
            combined_text = ' '.join([s.text for s in current_topic_sentences])
            
            topic_segment = SegmentTimestamp(
                segment_id=str(uuid.uuid4()),
                segment_type=TimestampType.TOPIC_SEGMENT,
                text=combined_text,
                start_time=current_topic_sentences[0].start_time,
                end_time=current_topic_sentences[-1].end_time,
                words=combined_words,
                topic=current_topic,
                confidence=sum(s.confidence for s in current_topic_sentences) / len(current_topic_sentences)
            )
            topic_segments.append(topic_segment)
        
        return topic_segments

class BookmarkManager:
    """Manages bookmarks and navigation points."""
    
    def __init__(self):
        self.auto_bookmark_rules = self._initialize_auto_bookmark_rules()
    
    def _initialize_auto_bookmark_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize rules for automatic bookmark creation."""
        return {
            'action_items': {
                'keywords': ['action item', 'todo', 'follow up', 'next step', 'assign'],
                'category': BookmarkCategory.ACTION_ITEM,
                'color': '#FF6B6B'
            },
            'key_points': {
                'keywords': ['important', 'key point', 'crucial', 'critical', 'significant'],
                'category': BookmarkCategory.KEY_POINT,
                'color': '#4ECDC4'
            },
            'decisions': {
                'keywords': ['decision', 'conclude', 'agree', 'resolve', 'final'],
                'category': BookmarkCategory.DECISION,
                'color': '#45B7D1'
            },
            'questions': {
                'keywords': ['question', 'clarify', 'understand', 'explain'],
                'category': BookmarkCategory.QUESTION,
                'color': '#96CEB4'
            }
        }
    
    def create_bookmark(self, title: str, description: str, timestamp: float,
                       category: BookmarkCategory, created_by: str,
                       tags: List[str] = None) -> Bookmark:
        """Create a new bookmark."""
        return Bookmark(
            bookmark_id=str(uuid.uuid4()),
            title=title,
            description=description,
            timestamp=timestamp,
            category=category,
            created_at=datetime.now(),
            created_by=created_by,
            color=self._get_category_color(category),
            tags=tags or [],
            metadata={'manual': True}
        )
    
    def generate_auto_bookmarks(self, segments: List[SegmentTimestamp]) -> List[Bookmark]:
        """Generate automatic bookmarks based on content analysis."""
        auto_bookmarks = []
        
        for segment in segments:
            segment_lower = segment.text.lower()
            
            for rule_name, rule in self.auto_bookmark_rules.items():
                if any(keyword in segment_lower for keyword in rule['keywords']):
                    # Extract context around keyword
                    context_start = max(0, segment.start_time - 5)  # 5 seconds before
                    
                    bookmark = Bookmark(
                        bookmark_id=str(uuid.uuid4()),
                        title=f"Auto: {rule_name.replace('_', ' ').title()}",
                        description=segment.text[:100] + "..." if len(segment.text) > 100 else segment.text,
                        timestamp=segment.start_time,
                        category=rule['category'],
                        created_at=datetime.now(),
                        created_by='system',
                        color=rule['color'],
                        tags=['auto-generated', rule_name],
                        metadata={'auto_generated': True, 'rule': rule_name}
                    )
                    auto_bookmarks.append(bookmark)
                    break  # Only one bookmark per segment
        
        return auto_bookmarks
    
    def _get_category_color(self, category: BookmarkCategory) -> str:
        """Get color for bookmark category."""
        colors = {
            BookmarkCategory.IMPORTANT: '#FFD700',
            BookmarkCategory.ACTION_ITEM: '#FF6B6B',
            BookmarkCategory.KEY_POINT: '#4ECDC4',
            BookmarkCategory.QUESTION: '#96CEB4',
            BookmarkCategory.DECISION: '#45B7D1',
            BookmarkCategory.FOLLOW_UP: '#FECA57',
            BookmarkCategory.CUSTOM: '#A55EEA'
        }
        return colors.get(category, '#FFD700')
    
    def search_bookmarks(self, bookmarks: List[Bookmark], query: str, 
                        category: Optional[BookmarkCategory] = None,
                        tags: List[str] = None) -> List[Bookmark]:
        """Search bookmarks by query, category, or tags."""
        results = []
        query_lower = query.lower()
        
        for bookmark in bookmarks:
            matches = False
            
            # Query match
            if (query_lower in bookmark.title.lower() or 
                query_lower in bookmark.description.lower()):
                matches = True
            
            # Category match
            if category and bookmark.category != category:
                matches = False
            
            # Tags match
            if tags:
                bookmark_tags = [tag.lower() for tag in bookmark.tags]
                if not any(tag.lower() in bookmark_tags for tag in tags):
                    matches = False
            
            if matches:
                results.append(bookmark)
        
        # Sort by timestamp
        return sorted(results, key=lambda b: b.timestamp)

class TimeCodeGenerator:
    """Generates time codes for navigation and deep linking."""
    
    def __init__(self):
        self.format_patterns = {
            'full': 'HH:MM:SS.mmm',
            'short': 'MM:SS',
            'minimal': 'M:SS',
            'milliseconds': 'SS.mmm'
        }
    
    def generate_time_codes(self, segments: List[SegmentTimestamp], 
                           format_type: str = 'short') -> List[TimeCode]:
        """Generate time codes for segments."""
        time_codes = []
        
        for segment in segments:
            display_format = self._format_timestamp(segment.start_time, format_type)
            
            time_code = TimeCode(
                time_code_id=str(uuid.uuid4()),
                timestamp=segment.start_time,
                display_format=display_format,
                reference_text=segment.text[:50] + "..." if len(segment.text) > 50 else segment.text,
                url_fragment=f"t={int(segment.start_time)}s",
                metadata={
                    'segment_id': segment.segment_id,
                    'segment_type': segment.segment_type.value
                }
            )
            time_codes.append(time_code)
        
        return time_codes
    
    def _format_timestamp(self, timestamp: float, format_type: str) -> str:
        """Format timestamp according to specified format."""
        total_seconds = int(timestamp)
        milliseconds = int((timestamp - total_seconds) * 1000)
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if format_type == 'full':
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
        elif format_type == 'short':
            if hours > 0:
                return f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes:02d}:{seconds:02d}"
        elif format_type == 'minimal':
            if hours > 0:
                return f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes}:{seconds:02d}"
        elif format_type == 'milliseconds':
            return f"{seconds:02d}.{milliseconds:03d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def create_deep_link(self, base_url: str, timestamp: float) -> str:
        """Create deep link URL for specific timestamp."""
        return f"{base_url}#t={int(timestamp)}s"

class InteractiveTranscriptNavigator:
    """Handles interactive transcript navigation and playback control."""
    
    def __init__(self):
        self.current_session: Optional[TranscriptSession] = None
        self.playback_callbacks: List[Callable] = []
    
    def load_session(self, session: TranscriptSession):
        """Load a transcript session for navigation."""
        self.current_session = session
        logger.info(f"Loaded session: {session.title}")
    
    def jump_to_timestamp(self, timestamp: float) -> bool:
        """Jump to specific timestamp in audio/video."""
        if not self.current_session:
            return False
        
        if 0 <= timestamp <= self.current_session.duration:
            self.current_session.current_position = timestamp
            self._notify_playback_change('jump', timestamp)
            return True
        return False
    
    def jump_to_word(self, word_index: int) -> bool:
        """Jump to specific word in transcript."""
        if not self.current_session or word_index >= len(self.current_session.word_timestamps):
            return False
        
        word_timestamp = self.current_session.word_timestamps[word_index]
        return self.jump_to_timestamp(word_timestamp.start_time)
    
    def jump_to_segment(self, segment_id: str) -> bool:
        """Jump to specific segment."""
        if not self.current_session:
            return False
        
        for segment in self.current_session.segment_timestamps:
            if segment.segment_id == segment_id:
                return self.jump_to_timestamp(segment.start_time)
        return False
    
    def jump_to_bookmark(self, bookmark_id: str) -> bool:
        """Jump to specific bookmark."""
        if not self.current_session:
            return False
        
        for bookmark in self.current_session.bookmarks:
            if bookmark.bookmark_id == bookmark_id:
                return self.jump_to_timestamp(bookmark.timestamp)
        return False
    
    def get_words_at_timestamp(self, timestamp: float, window: float = 0.5) -> List[WordTimestamp]:
        """Get words active at specific timestamp."""
        if not self.current_session:
            return []
        
        active_words = []
        for word in self.current_session.word_timestamps:
            if (word.start_time <= timestamp + window and 
                word.end_time >= timestamp - window):
                active_words.append(word)
        
        return active_words
    
    def get_current_segment(self, timestamp: Optional[float] = None) -> Optional[SegmentTimestamp]:
        """Get current segment at timestamp."""
        if not self.current_session:
            return None
        
        target_time = timestamp or self.current_session.current_position
        
        for segment in self.current_session.segment_timestamps:
            if segment.start_time <= target_time <= segment.end_time:
                return segment
        return None
    
    def navigate_by_mode(self, direction: str, mode: NavigationMode) -> bool:
        """Navigate forward/backward by specified mode."""
        if not self.current_session:
            return False
        
        current_time = self.current_session.current_position
        
        if mode == NavigationMode.SENTENCE_BY_SENTENCE:
            return self._navigate_by_sentences(direction, current_time)
        elif mode == NavigationMode.PARAGRAPH_BY_PARAGRAPH:
            return self._navigate_by_paragraphs(direction, current_time)
        elif mode == NavigationMode.SPEAKER_BY_SPEAKER:
            return self._navigate_by_speakers(direction, current_time)
        elif mode == NavigationMode.BOOKMARK_TO_BOOKMARK:
            return self._navigate_by_bookmarks(direction, current_time)
        
        return False
    
    def _navigate_by_sentences(self, direction: str, current_time: float) -> bool:
        """Navigate by sentences."""
        sentence_segments = [s for s in self.current_session.segment_timestamps 
                           if s.segment_type == TimestampType.SENTENCE_LEVEL]
        
        if direction == 'forward':
            for segment in sentence_segments:
                if segment.start_time > current_time:
                    return self.jump_to_timestamp(segment.start_time)
        else:  # backward
            for segment in reversed(sentence_segments):
                if segment.start_time < current_time:
                    return self.jump_to_timestamp(segment.start_time)
        
        return False
    
    def _navigate_by_speakers(self, direction: str, current_time: float) -> bool:
        """Navigate by speaker segments."""
        speaker_segments = [s for s in self.current_session.segment_timestamps 
                          if s.segment_type == TimestampType.SPEAKER_SEGMENT]
        
        if direction == 'forward':
            for segment in speaker_segments:
                if segment.start_time > current_time:
                    return self.jump_to_timestamp(segment.start_time)
        else:  # backward
            for segment in reversed(speaker_segments):
                if segment.start_time < current_time:
                    return self.jump_to_timestamp(segment.start_time)
        
        return False
    
    def _navigate_by_bookmarks(self, direction: str, current_time: float) -> bool:
        """Navigate by bookmarks."""
        bookmarks = sorted(self.current_session.bookmarks, key=lambda b: b.timestamp)
        
        if direction == 'forward':
            for bookmark in bookmarks:
                if bookmark.timestamp > current_time:
                    return self.jump_to_timestamp(bookmark.timestamp)
        else:  # backward
            for bookmark in reversed(bookmarks):
                if bookmark.timestamp < current_time:
                    return self.jump_to_timestamp(bookmark.timestamp)
        
        return False
    
    def _notify_playback_change(self, action: str, timestamp: float):
        """Notify registered callbacks of playback changes."""
        for callback in self.playback_callbacks:
            try:
                callback(action, timestamp)
            except Exception as e:
                logger.error(f"Playback callback error: {str(e)}")

class TimestampDatabase:
    """SQLite database for storing timestamp information."""
    
    def __init__(self, db_path: str = "timestamps.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    title TEXT,
                    audio_file_path TEXT,
                    duration REAL,
                    transcript_text TEXT,
                    created_at TIMESTAMP,
                    last_modified TIMESTAMP,
                    playback_speed REAL,
                    current_position REAL,
                    metadata TEXT
                )
            """)
            
            # Word timestamps table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS word_timestamps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    word TEXT,
                    start_time REAL,
                    end_time REAL,
                    confidence REAL,
                    speaker_id TEXT,
                    word_index INTEGER,
                    is_punctuation BOOLEAN,
                    phonemes TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                )
            """)
            
            # Segment timestamps table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS segment_timestamps (
                    segment_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    segment_type TEXT,
                    text TEXT,
                    start_time REAL,
                    end_time REAL,
                    speaker_id TEXT,
                    confidence REAL,
                    topic TEXT,
                    chapter_title TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                )
            """)
            
            # Bookmarks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bookmarks (
                    bookmark_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    title TEXT,
                    description TEXT,
                    timestamp REAL,
                    category TEXT,
                    created_at TIMESTAMP,
                    created_by TEXT,
                    color TEXT,
                    is_shared BOOLEAN,
                    tags TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                )
            """)
            
            conn.commit()
    
    def store_session(self, session: TranscriptSession):
        """Store complete session data."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Store session
            cursor.execute("""
                INSERT OR REPLACE INTO sessions
                (session_id, title, audio_file_path, duration, transcript_text,
                 created_at, last_modified, playback_speed, current_position, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.session_id, session.title, session.audio_file_path,
                session.duration, session.transcript_text, session.created_at,
                session.last_modified, session.playback_speed, session.current_position,
                json.dumps(session.metadata)
            ))
            
            # Store word timestamps
            for word_ts in session.word_timestamps:
                cursor.execute("""
                    INSERT INTO word_timestamps
                    (session_id, word, start_time, end_time, confidence, speaker_id,
                     word_index, is_punctuation, phonemes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session.session_id, word_ts.word, word_ts.start_time,
                    word_ts.end_time, word_ts.confidence, word_ts.speaker_id,
                    word_ts.word_index, word_ts.is_punctuation,
                    json.dumps(word_ts.phonemes) if word_ts.phonemes else None
                ))
            
            # Store segment timestamps
            for segment in session.segment_timestamps:
                cursor.execute("""
                    INSERT OR REPLACE INTO segment_timestamps
                    (segment_id, session_id, segment_type, text, start_time, end_time,
                     speaker_id, confidence, topic, chapter_title)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    segment.segment_id, session.session_id, segment.segment_type.value,
                    segment.text, segment.start_time, segment.end_time,
                    segment.speaker_id, segment.confidence, segment.topic,
                    segment.chapter_title
                ))
            
            # Store bookmarks
            for bookmark in session.bookmarks:
                cursor.execute("""
                    INSERT OR REPLACE INTO bookmarks
                    (bookmark_id, session_id, title, description, timestamp,
                     category, created_at, created_by, color, is_shared, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    bookmark.bookmark_id, session.session_id, bookmark.title,
                    bookmark.description, bookmark.timestamp, bookmark.category.value,
                    bookmark.created_at, bookmark.created_by, bookmark.color,
                    bookmark.is_shared, json.dumps(bookmark.tags)
                ))
            
            conn.commit()

class ComprehensiveTimestampingSystem:
    """Main system for comprehensive timestamping functionality."""
    
    def __init__(self, db_path: str = "timestamps.db"):
        self.word_timestamper = WordLevelTimestamper()
        self.segment_timestamper = SegmentTimestamper()
        self.bookmark_manager = BookmarkManager()
        self.timecode_generator = TimeCodeGenerator()
        self.navigator = InteractiveTranscriptNavigator()
        self.database = TimestampDatabase(db_path)
        
        logger.info("Comprehensive Timestamping System initialized")
    
    async def create_timestamped_session(self, 
                                       title: str,
                                       audio_file_path: str,
                                       transcript_text: str,
                                       duration: float,
                                       language: str = 'en',
                                       speaker_changes: List[Tuple[float, str]] = None) -> TranscriptSession:
        """Create a complete timestamped session."""
        try:
            session_id = str(uuid.uuid4())
            logger.info(f"Creating timestamped session: {title}")
            
            # 1. Generate word-level timestamps
            word_timestamps = self.word_timestamper.generate_word_timestamps(
                transcript_text, duration, language
            )
            
            # 2. Generate sentence segments
            sentence_segments = self.segment_timestamper.generate_sentence_segments(
                word_timestamps, transcript_text
            )
            
            # 3. Generate speaker segments if speaker changes provided
            speaker_segments = []
            if speaker_changes:
                speaker_segments = self.segment_timestamper.generate_speaker_segments(
                    word_timestamps, speaker_changes
                )
            
            # 4. Generate topic segments
            topic_segments = self.segment_timestamper.generate_topic_segments(sentence_segments)
            
            # 5. Combine all segments
            all_segments = sentence_segments + speaker_segments + topic_segments
            
            # 6. Generate automatic bookmarks
            auto_bookmarks = self.bookmark_manager.generate_auto_bookmarks(all_segments)
            
            # 7. Generate time codes
            time_codes = self.timecode_generator.generate_time_codes(sentence_segments)
            
            # 8. Generate navigation points
            navigation_points = self._generate_navigation_points(all_segments)
            
            # 9. Extract speaker information
            speakers = self._extract_speakers(speaker_changes or [])
            
            # 10. Create session
            session = TranscriptSession(
                session_id=session_id,
                title=title,
                audio_file_path=audio_file_path,
                duration=duration,
                transcript_text=transcript_text,
                word_timestamps=word_timestamps,
                segment_timestamps=all_segments,
                bookmarks=auto_bookmarks,
                time_codes=time_codes,
                navigation_points=navigation_points,
                speakers=speakers,
                chapters=[],  # Could be generated from topic segments
                created_at=datetime.now(),
                last_modified=datetime.now()
            )
            
            # 11. Store in database
            self.database.store_session(session)
            
            # 12. Load in navigator
            self.navigator.load_session(session)
            
            logger.info(f"Session created successfully with {len(word_timestamps)} words, "
                       f"{len(all_segments)} segments, {len(auto_bookmarks)} bookmarks")
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to create timestamped session: {str(e)}")
            raise
    
    def _generate_navigation_points(self, segments: List[SegmentTimestamp]) -> List[NavigationPoint]:
        """Generate navigation waypoints."""
        navigation_points = []
        
        # Add points for topic changes
        topic_segments = [s for s in segments if s.segment_type == TimestampType.TOPIC_SEGMENT]
        for segment in topic_segments:
            point = NavigationPoint(
                point_id=str(uuid.uuid4()),
                title=f"Topic: {segment.topic or 'Unknown'}",
                timestamp=segment.start_time,
                point_type=TimestampType.TOPIC_SEGMENT,
                description=segment.text[:100] + "..." if len(segment.text) > 100 else segment.text
            )
            navigation_points.append(point)
        
        # Add points for speaker changes
        speaker_segments = [s for s in segments if s.segment_type == TimestampType.SPEAKER_SEGMENT]
        current_speaker = None
        for segment in speaker_segments:
            if segment.speaker_id != current_speaker:
                point = NavigationPoint(
                    point_id=str(uuid.uuid4()),
                    title=f"Speaker: {segment.speaker_id or 'Unknown'}",
                    timestamp=segment.start_time,
                    point_type=TimestampType.SPEAKER_SEGMENT,
                    description=f"Speaker change to {segment.speaker_id}"
                )
                navigation_points.append(point)
                current_speaker = segment.speaker_id
        
        return sorted(navigation_points, key=lambda p: p.timestamp)
    
    def _extract_speakers(self, speaker_changes: List[Tuple[float, str]]) -> Dict[str, str]:
        """Extract speaker information."""
        speakers = {}
        for _, speaker_id in speaker_changes:
            if speaker_id not in speakers:
                speakers[speaker_id] = f"Speaker {len(speakers) + 1}"
        return speakers
    
    def add_manual_bookmark(self, session_id: str, title: str, description: str,
                           timestamp: float, category: BookmarkCategory,
                           created_by: str, tags: List[str] = None) -> bool:
        """Add a manual bookmark to session."""
        if self.navigator.current_session and self.navigator.current_session.session_id == session_id:
            bookmark = self.bookmark_manager.create_bookmark(
                title, description, timestamp, category, created_by, tags
            )
            self.navigator.current_session.bookmarks.append(bookmark)
            
            # Update database
            self.database.store_session(self.navigator.current_session)
            return True
        return False
    
    def search_in_session(self, session_id: str, query: str, 
                         timestamp_range: Optional[Tuple[float, float]] = None) -> Dict[str, List[Any]]:
        """Search within a session."""
        if not self.navigator.current_session or self.navigator.current_session.session_id != session_id:
            return {'words': [], 'segments': [], 'bookmarks': []}
        
        results = {'words': [], 'segments': [], 'bookmarks': []}
        query_lower = query.lower()
        
        # Search words
        for word in self.navigator.current_session.word_timestamps:
            if (query_lower in word.word.lower() and 
                (not timestamp_range or timestamp_range[0] <= word.start_time <= timestamp_range[1])):
                results['words'].append(word)
        
        # Search segments
        for segment in self.navigator.current_session.segment_timestamps:
            if (query_lower in segment.text.lower() and
                (not timestamp_range or timestamp_range[0] <= segment.start_time <= timestamp_range[1])):
                results['segments'].append(segment)
        
        # Search bookmarks
        results['bookmarks'] = self.bookmark_manager.search_bookmarks(
            self.navigator.current_session.bookmarks, query
        )
        
        return results

# Demo function
async def demo_timestamping_system():
    """Demonstrate comprehensive timestamping system capabilities."""
    print("⏰ Comprehensive Timestamping System Demo")
    print("=" * 50)
    
    # Initialize system
    system = ComprehensiveTimestampingSystem()
    
    # Sample transcript and metadata
    sample_transcript = """
    Hello everyone and welcome to today's meeting. I'm John Smith, the project manager.
    We have several important items to discuss today. First, let's review our progress on the new feature development.
    Sarah, can you give us an update on the user interface work?
    Thanks John. The UI work is progressing well. We've completed the main dashboard and user authentication pages.
    However, we've encountered some technical challenges with the data visualization component.
    That's an important issue we need to address. What do you think would be the best approach?
    I think we should schedule a follow-up meeting with the development team to discuss solutions.
    Great idea. Let's make that an action item. Any other questions or concerns before we move to the next topic?
    """
    
    sample_duration = 120.0  # 2 minutes
    speaker_changes = [(0.0, 'john_smith'), (25.0, 'sarah_jones'), (65.0, 'john_smith'), (95.0, 'sarah_jones')]
    
    print(f"📝 Sample Content:")
    print(f"Duration: {sample_duration} seconds")
    print(f"Speakers: {len(set(s[1] for s in speaker_changes))} participants")
    print(f"Text length: {len(sample_transcript)} characters")
    
    # Test 1: Create timestamped session
    print(f"\n🎯 Test 1: Creating Timestamped Session")
    print("-" * 30)
    
    session = await system.create_timestamped_session(
        title="Sample Meeting Recording",
        audio_file_path="/path/to/sample_meeting.mp3",
        transcript_text=sample_transcript,
        duration=sample_duration,
        language='en',
        speaker_changes=speaker_changes
    )
    
    print(f"✅ Session created: {session.session_id}")
    print(f"   Words: {len(session.word_timestamps)} timestamped")
    print(f"   Segments: {len(session.segment_timestamps)} identified")
    print(f"   Auto-bookmarks: {len(session.bookmarks)} generated")
    print(f"   Time codes: {len(session.time_codes)} created")
    
    # Test 2: Word-level analysis
    print(f"\n📝 Test 2: Word-Level Timestamps")
    print("-" * 30)
    
    sample_words = session.word_timestamps[:10]  # First 10 words
    for word in sample_words:
        if not word.is_punctuation:
            print(f"  {word.start_time:6.2f}s - {word.end_time:6.2f}s: '{word.word}' (conf: {word.confidence:.2f})")
    
    # Test 3: Segment analysis
    print(f"\n🔗 Test 3: Segment Analysis")
    print("-" * 30)
    
    segment_types = {}
    for segment in session.segment_timestamps:
        segment_type = segment.segment_type.value
        if segment_type not in segment_types:
            segment_types[segment_type] = []
        segment_types[segment_type].append(segment)
    
    for seg_type, segments in segment_types.items():
        print(f"  {seg_type.title()}: {len(segments)} segments")
        if segments:
            sample_segment = segments[0]
            print(f"    Example: {sample_segment.start_time:.1f}s - '{sample_segment.text[:50]}...'")
    
    # Test 4: Bookmark analysis
    print(f"\n🔖 Test 4: Auto-Generated Bookmarks")
    print("-" * 30)
    
    bookmark_categories = {}
    for bookmark in session.bookmarks:
        category = bookmark.category.value
        if category not in bookmark_categories:
            bookmark_categories[category] = []
        bookmark_categories[category].append(bookmark)
    
    for category, bookmarks in bookmark_categories.items():
        print(f"  {category.title()}: {len(bookmarks)} bookmarks")
        if bookmarks:
            sample_bookmark = bookmarks[0]
            print(f"    - {sample_bookmark.timestamp:.1f}s: {sample_bookmark.title}")
    
    # Test 5: Navigation testing
    print(f"\n🧭 Test 5: Interactive Navigation")
    print("-" * 30)
    
    navigator = system.navigator
    
    # Test jumping to different positions
    test_positions = [30.0, 60.0, 90.0]
    for pos in test_positions:
        success = navigator.jump_to_timestamp(pos)
        if success:
            current_segment = navigator.get_current_segment(pos)
            active_words = navigator.get_words_at_timestamp(pos)
            
            print(f"  Position {pos:.1f}s:")
            print(f"    Segment: {current_segment.text[:40] if current_segment else 'None'}...")
            print(f"    Active words: {len(active_words)}")
    
    # Test 6: Search functionality
    print(f"\n🔍 Test 6: Search Functionality")
    print("-" * 30)
    
    search_queries = ['meeting', 'development', 'action item']
    for query in search_queries:
        results = system.search_in_session(session.session_id, query)
        
        print(f"  Query '{query}':")
        print(f"    Words: {len(results['words'])} matches")
        print(f"    Segments: {len(results['segments'])} matches")
        print(f"    Bookmarks: {len(results['bookmarks'])} matches")
    
    # Test 7: Manual bookmark creation
    print(f"\n➕ Test 7: Manual Bookmark Creation")
    print("-" * 30)
    
    success = system.add_manual_bookmark(
        session.session_id,
        title="Key Decision Point",
        description="Important decision about technical approach",
        timestamp=75.0,
        category=BookmarkCategory.DECISION,
        created_by="demo_user",
        tags=['manual', 'important', 'decision']
    )
    
    if success:
        print(f"  ✅ Manual bookmark added successfully")
        print(f"  Total bookmarks now: {len(navigator.current_session.bookmarks)}")
    
    # Test 8: Time code generation
    print(f"\n⏱️  Test 8: Time Code Formats")
    print("-" * 30)
    
    sample_timestamps = [15.5, 45.25, 75.75, 105.125]
    formats = ['short', 'full', 'minimal', 'milliseconds']
    
    for fmt in formats:
        print(f"  {fmt.title()} format:")
        for ts in sample_timestamps[:2]:  # Show first 2
            formatted = system.timecode_generator._format_timestamp(ts, fmt)
            print(f"    {ts:.3f}s → {formatted}")
    
    # Test 9: Navigation modes
    print(f"\n🚶 Test 9: Navigation Modes")
    print("-" * 30)
    
    # Set position and test different navigation modes
    navigator.jump_to_timestamp(30.0)
    
    modes_to_test = [
        NavigationMode.SENTENCE_BY_SENTENCE,
        NavigationMode.SPEAKER_BY_SPEAKER,
        NavigationMode.BOOKMARK_TO_BOOKMARK
    ]
    
    for mode in modes_to_test:
        # Test forward navigation
        current_pos = navigator.current_session.current_position
        success = navigator.navigate_by_mode('forward', mode)
        
        if success:
            new_pos = navigator.current_session.current_position
            print(f"  {mode.value}: {current_pos:.1f}s → {new_pos:.1f}s")
        else:
            print(f"  {mode.value}: No next position found")
    
    # Cleanup
    print(f"\n🧹 Cleanup")
    print("-" * 30)
    
    try:
        os.remove("timestamps.db")
        print("Database cleaned up")
    except Exception as e:
        print(f"Cleanup note: {str(e)}")
    
    print(f"\n✅ Comprehensive timestamping demo completed!")

if __name__ == "__main__":
    asyncio.run(demo_timestamping_system())