#!/usr/bin/env python3
"""
Comprehensive Timestamping System
Implements word-level timestamps, segment timing, interactive navigation,
and synchronized transcript playback
"""

import asyncio
import json
import logging
import os
import tempfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import numpy as np
import torch
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
import whisper
from faster_whisper import WhisperModel
import librosa
import soundfile as sf
from scipy import signal
import wave
import struct
import webrtcvad
from pyannote.audio import Pipeline
from pyannote.audio.pipelines import VoiceActivityDetection
from pyannote.core import Segment, Annotation
import pandas as pd
from collections import deque
import bisect
import subprocess
import ffmpeg

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TimestampGranularity(Enum):
    """Levels of timestamp granularity"""
    WORD = "word"
    PHRASE = "phrase"
    SENTENCE = "sentence"
    SEGMENT = "segment"
    PARAGRAPH = "paragraph"
    SPEAKER = "speaker"


class NavigationType(Enum):
    """Types of navigation interactions"""
    CLICK = "click"
    SEARCH = "search"
    BOOKMARK = "bookmark"
    CHAPTER = "chapter"
    SPEAKER = "speaker"
    KEYWORD = "keyword"


@dataclass
class WordTimestamp:
    """Word-level timestamp information"""
    word: str
    start_time: float
    end_time: float
    confidence: float
    speaker_id: Optional[str] = None
    is_punctuation: bool = False
    phonemes: Optional[List[str]] = None


@dataclass
class SegmentTimestamp:
    """Segment-level timestamp information"""
    segment_id: str
    text: str
    start_time: float
    end_time: float
    words: List[WordTimestamp]
    speaker_id: Optional[str] = None
    confidence: float = 0.0
    segment_type: Optional[str] = None  # sentence, paragraph, etc.


@dataclass
class Bookmark:
    """Bookmark for important moments"""
    bookmark_id: str
    timestamp: float
    label: str
    description: Optional[str] = None
    color: str = "#FF0000"
    category: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Chapter:
    """Chapter marker for navigation"""
    chapter_id: str
    title: str
    start_time: float
    end_time: float
    description: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    summary: Optional[str] = None


@dataclass
class TimestampedTranscript:
    """Complete timestamped transcript"""
    transcript_id: str
    full_text: str
    segments: List[SegmentTimestamp]
    words: List[WordTimestamp]
    bookmarks: List[Bookmark]
    chapters: List[Chapter]
    duration: float
    sample_rate: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NavigationEvent:
    """Navigation interaction event"""
    event_type: NavigationType
    timestamp: float
    target_time: float
    context: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class AdvancedTimestampingSystem:
    """Main comprehensive timestamping system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.models: Dict[str, Any] = {}
        self.processors: Dict[str, Any] = {}
        
        # Initialize models
        self._initialize_models()
        
        # Navigation state
        self.current_position: float = 0.0
        self.playback_speed: float = 1.0
        self.is_playing: bool = False
        
        # Cache for performance
        self.timestamp_cache: Dict[str, TimestampedTranscript] = {}
        
    def _initialize_models(self):
        """Initialize models for timestamping"""
        try:
            # Faster Whisper for word-level timestamps
            self.models['faster_whisper'] = WhisperModel(
                "base",
                device="cpu",
                compute_type="int8"
            )
            
            # Standard Whisper as fallback
            self.models['whisper'] = whisper.load_model("base")
            
            # Wav2Vec2 for phoneme alignment (optional)
            if self.config.get('enable_phoneme_alignment', False):
                self.processors['wav2vec2'] = Wav2Vec2Processor.from_pretrained(
                    "facebook/wav2vec2-base-960h"
                )
                self.models['wav2vec2'] = Wav2Vec2ForCTC.from_pretrained(
                    "facebook/wav2vec2-base-960h"
                )
            
            # VAD for silence detection
            self.vad = webrtcvad.Vad(2)
            
            logger.info("Timestamping models initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize models: {e}")
    
    async def generate_timestamps(
        self,
        audio_file: str,
        granularity: TimestampGranularity = TimestampGranularity.WORD,
        enable_diarization: bool = False,
        language: str = "auto"
    ) -> TimestampedTranscript:
        """Generate comprehensive timestamps for audio"""
        
        import time
        start_time = time.time()
        
        try:
            # Load audio
            audio, sr = librosa.load(audio_file, sr=16000)
            duration = len(audio) / sr
            
            # Generate word-level timestamps
            words = await self._generate_word_timestamps(
                audio_file, 
                language
            )
            
            # Generate segments based on granularity
            segments = await self._generate_segments(
                words, 
                granularity,
                audio,
                sr
            )
            
            # Add speaker diarization if enabled
            if enable_diarization:
                segments = await self._add_speaker_diarization(
                    segments,
                    audio_file
                )
            
            # Generate full text
            full_text = ' '.join([w.word for w in words if not w.is_punctuation])
            
            # Auto-generate chapters
            chapters = await self._generate_chapters(segments)
            
            # Create transcript
            transcript = TimestampedTranscript(
                transcript_id=self._generate_id(),
                full_text=full_text,
                segments=segments,
                words=words,
                bookmarks=[],
                chapters=chapters,
                duration=duration,
                sample_rate=sr,
                metadata={
                    'audio_file': audio_file,
                    'language': language,
                    'granularity': granularity.value,
                    'processing_time': time.time() - start_time
                }
            )
            
            # Cache result
            self.timestamp_cache[transcript.transcript_id] = transcript
            
            return transcript
            
        except Exception as e:
            logger.error(f"Timestamp generation failed: {e}")
            raise
    
    async def _generate_word_timestamps(
        self,
        audio_file: str,
        language: str
    ) -> List[WordTimestamp]:
        """Generate word-level timestamps"""
        
        words = []
        
        try:
            model = self.models['faster_whisper']
            
            # Transcribe with word timestamps
            segments, info = model.transcribe(
                audio_file,
                language=None if language == "auto" else language,
                word_timestamps=True,
                vad_filter=True
            )
            
            # Extract words
            for segment in segments:
                if segment.words:
                    for word in segment.words:
                        words.append(WordTimestamp(
                            word=word.word.strip(),
                            start_time=word.start,
                            end_time=word.end,
                            confidence=word.probability
                        ))
            
            # Add punctuation detection
            words = self._detect_punctuation(words)
            
            return words
            
        except Exception as e:
            logger.error(f"Word timestamp generation failed: {e}")
            # Fallback to segment-based estimation
            return self._estimate_word_timestamps(audio_file, language)
    
    def _detect_punctuation(self, words: List[WordTimestamp]) -> List[WordTimestamp]:
        """Detect and mark punctuation in words"""
        
        punctuation_marks = set('.,!?;:"\'-')
        
        for word in words:
            # Check if word ends with punctuation
            if word.word and word.word[-1] in punctuation_marks:
                # Split word and punctuation
                actual_word = word.word.rstrip(''.join(punctuation_marks))
                punct = word.word[len(actual_word):]
                
                if punct:
                    # Update current word
                    word.word = actual_word
                    
                    # Create punctuation entry
                    punct_timestamp = WordTimestamp(
                        word=punct,
                        start_time=word.end_time - 0.01,
                        end_time=word.end_time,
                        confidence=word.confidence,
                        is_punctuation=True
                    )
                    
                    # Insert after current word
                    idx = words.index(word)
                    words.insert(idx + 1, punct_timestamp)
        
        return words
    
    def _estimate_word_timestamps(
        self,
        audio_file: str,
        language: str
    ) -> List[WordTimestamp]:
        """Estimate word timestamps when precise alignment unavailable"""
        
        words = []
        
        try:
            # Use standard Whisper
            model = self.models['whisper']
            result = model.transcribe(audio_file, language=language)
            
            # Estimate based on segments
            for segment in result.get('segments', []):
                text = segment['text'].strip()
                start = segment['start']
                end = segment['end']
                
                # Split into words
                word_list = text.split()
                if not word_list:
                    continue
                
                # Estimate timing for each word
                duration = end - start
                word_duration = duration / len(word_list)
                
                for i, word in enumerate(word_list):
                    word_start = start + (i * word_duration)
                    word_end = word_start + word_duration
                    
                    words.append(WordTimestamp(
                        word=word,
                        start_time=word_start,
                        end_time=word_end,
                        confidence=0.7  # Lower confidence for estimates
                    ))
            
            return words
            
        except Exception as e:
            logger.error(f"Word timestamp estimation failed: {e}")
            return []
    
    async def _generate_segments(
        self,
        words: List[WordTimestamp],
        granularity: TimestampGranularity,
        audio: np.ndarray,
        sr: int
    ) -> List[SegmentTimestamp]:
        """Generate segments based on granularity"""
        
        segments = []
        
        if granularity == TimestampGranularity.WORD:
            # Each word is a segment
            for word in words:
                if not word.is_punctuation:
                    segments.append(SegmentTimestamp(
                        segment_id=self._generate_id(),
                        text=word.word,
                        start_time=word.start_time,
                        end_time=word.end_time,
                        words=[word],
                        confidence=word.confidence,
                        segment_type="word"
                    ))
        
        elif granularity == TimestampGranularity.SENTENCE:
            # Group words into sentences
            current_sentence = []
            
            for word in words:
                current_sentence.append(word)
                
                # Check for sentence end
                if word.is_punctuation and word.word in '.!?':
                    if current_sentence:
                        # Create sentence segment
                        sentence_text = ' '.join([
                            w.word for w in current_sentence 
                            if not w.is_punctuation
                        ])
                        
                        segments.append(SegmentTimestamp(
                            segment_id=self._generate_id(),
                            text=sentence_text,
                            start_time=current_sentence[0].start_time,
                            end_time=current_sentence[-1].end_time,
                            words=current_sentence.copy(),
                            confidence=np.mean([w.confidence for w in current_sentence]),
                            segment_type="sentence"
                        ))
                        
                        current_sentence = []
            
            # Add remaining words as final sentence
            if current_sentence:
                sentence_text = ' '.join([
                    w.word for w in current_sentence 
                    if not w.is_punctuation
                ])
                
                segments.append(SegmentTimestamp(
                    segment_id=self._generate_id(),
                    text=sentence_text,
                    start_time=current_sentence[0].start_time,
                    end_time=current_sentence[-1].end_time,
                    words=current_sentence,
                    confidence=np.mean([w.confidence for w in current_sentence]),
                    segment_type="sentence"
                ))
        
        elif granularity == TimestampGranularity.PARAGRAPH:
            # Group sentences into paragraphs
            # Use silence detection to identify paragraph breaks
            segments = await self._segment_by_silence(words, audio, sr, "paragraph")
        
        elif granularity == TimestampGranularity.SEGMENT:
            # Natural segments based on pauses
            segments = await self._segment_by_pauses(words, audio, sr)
        
        return segments
    
    async def _segment_by_silence(
        self,
        words: List[WordTimestamp],
        audio: np.ndarray,
        sr: int,
        segment_type: str
    ) -> List[SegmentTimestamp]:
        """Segment based on silence detection"""
        
        segments = []
        
        # Detect silence periods
        silence_threshold = 0.01
        min_silence_duration = 1.0  # seconds
        
        # Convert audio to frames
        frame_length = int(sr * 0.02)  # 20ms frames
        hop_length = int(sr * 0.01)  # 10ms hop
        
        # Calculate energy
        energy = librosa.feature.rms(
            y=audio,
            frame_length=frame_length,
            hop_length=hop_length
        )[0]
        
        # Find silence periods
        silence_frames = energy < silence_threshold
        
        # Group consecutive silence frames
        silence_regions = []
        start_idx = None
        
        for i, is_silent in enumerate(silence_frames):
            if is_silent and start_idx is None:
                start_idx = i
            elif not is_silent and start_idx is not None:
                duration = (i - start_idx) * hop_length / sr
                if duration >= min_silence_duration:
                    silence_regions.append((
                        start_idx * hop_length / sr,
                        i * hop_length / sr
                    ))
                start_idx = None
        
        # Segment words based on silence regions
        current_segment = []
        silence_idx = 0
        
        for word in words:
            current_segment.append(word)
            
            # Check if word ends near a silence region
            if silence_idx < len(silence_regions):
                silence_start, silence_end = silence_regions[silence_idx]
                
                if abs(word.end_time - silence_start) < 0.1:
                    # Create segment
                    if current_segment:
                        segment_text = ' '.join([
                            w.word for w in current_segment 
                            if not w.is_punctuation
                        ])
                        
                        segments.append(SegmentTimestamp(
                            segment_id=self._generate_id(),
                            text=segment_text,
                            start_time=current_segment[0].start_time,
                            end_time=current_segment[-1].end_time,
                            words=current_segment.copy(),
                            confidence=np.mean([w.confidence for w in current_segment]),
                            segment_type=segment_type
                        ))
                        
                        current_segment = []
                        silence_idx += 1
        
        # Add remaining words
        if current_segment:
            segment_text = ' '.join([
                w.word for w in current_segment 
                if not w.is_punctuation
            ])
            
            segments.append(SegmentTimestamp(
                segment_id=self._generate_id(),
                text=segment_text,
                start_time=current_segment[0].start_time,
                end_time=current_segment[-1].end_time,
                words=current_segment,
                confidence=np.mean([w.confidence for w in current_segment]),
                segment_type=segment_type
            ))
        
        return segments
    
    async def _segment_by_pauses(
        self,
        words: List[WordTimestamp],
        audio: np.ndarray,
        sr: int
    ) -> List[SegmentTimestamp]:
        """Segment based on natural pauses"""
        
        segments = []
        current_segment = []
        pause_threshold = 0.3  # seconds
        
        for i, word in enumerate(words):
            current_segment.append(word)
            
            # Check for pause after current word
            if i < len(words) - 1:
                next_word = words[i + 1]
                pause_duration = next_word.start_time - word.end_time
                
                if pause_duration >= pause_threshold:
                    # Create segment
                    if current_segment:
                        segment_text = ' '.join([
                            w.word for w in current_segment 
                            if not w.is_punctuation
                        ])
                        
                        segments.append(SegmentTimestamp(
                            segment_id=self._generate_id(),
                            text=segment_text,
                            start_time=current_segment[0].start_time,
                            end_time=current_segment[-1].end_time,
                            words=current_segment.copy(),
                            confidence=np.mean([w.confidence for w in current_segment]),
                            segment_type="segment"
                        ))
                        
                        current_segment = []
        
        # Add remaining words
        if current_segment:
            segment_text = ' '.join([
                w.word for w in current_segment 
                if not w.is_punctuation
            ])
            
            segments.append(SegmentTimestamp(
                segment_id=self._generate_id(),
                text=segment_text,
                start_time=current_segment[0].start_time,
                end_time=current_segment[-1].end_time,
                words=current_segment,
                confidence=np.mean([w.confidence for w in current_segment]),
                segment_type="segment"
            ))
        
        return segments
    
    async def _add_speaker_diarization(
        self,
        segments: List[SegmentTimestamp],
        audio_file: str
    ) -> List[SegmentTimestamp]:
        """Add speaker diarization to segments"""
        
        try:
            # Use pyannote for speaker diarization
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization",
                use_auth_token=self.config.get('huggingface_token')
            )
            
            diarization = pipeline(audio_file)
            
            # Map segments to speakers
            for segment in segments:
                # Find speaker for segment time
                segment_time = Segment(segment.start_time, segment.end_time)
                
                # Get overlapping speakers
                speakers = []
                for turn, _, speaker in diarization.itertracks(yield_label=True):
                    if turn.intersects(segment_time):
                        speakers.append(speaker)
                
                # Assign most likely speaker
                if speakers:
                    # Use majority vote
                    from collections import Counter
                    speaker_counts = Counter(speakers)
                    segment.speaker_id = speaker_counts.most_common(1)[0][0]
                    
                    # Update words with speaker
                    for word in segment.words:
                        word.speaker_id = segment.speaker_id
            
        except Exception as e:
            logger.warning(f"Speaker diarization failed: {e}")
        
        return segments
    
    async def _generate_chapters(
        self,
        segments: List[SegmentTimestamp]
    ) -> List[Chapter]:
        """Auto-generate chapters from segments"""
        
        chapters = []
        
        # Simple heuristic: create chapters every N segments or M seconds
        chapter_duration = 300  # 5 minutes
        min_segments_per_chapter = 10
        
        current_chapter_segments = []
        current_start_time = 0
        
        for segment in segments:
            current_chapter_segments.append(segment)
            
            # Check if chapter should end
            duration = segment.end_time - current_start_time
            
            if (duration >= chapter_duration or 
                len(current_chapter_segments) >= min_segments_per_chapter):
                
                # Create chapter
                chapter_text = ' '.join([s.text for s in current_chapter_segments])
                
                # Generate title (first few words)
                title_words = chapter_text.split()[:5]
                title = ' '.join(title_words) + '...'
                
                chapters.append(Chapter(
                    chapter_id=self._generate_id(),
                    title=title,
                    start_time=current_start_time,
                    end_time=segment.end_time,
                    description=f"Chapter {len(chapters) + 1}",
                    keywords=self._extract_keywords(chapter_text)
                ))
                
                current_chapter_segments = []
                current_start_time = segment.end_time
        
        # Add final chapter
        if current_chapter_segments:
            chapter_text = ' '.join([s.text for s in current_chapter_segments])
            title_words = chapter_text.split()[:5]
            title = ' '.join(title_words) + '...'
            
            chapters.append(Chapter(
                chapter_id=self._generate_id(),
                title=title,
                start_time=current_start_time,
                end_time=current_chapter_segments[-1].end_time,
                description=f"Chapter {len(chapters) + 1}",
                keywords=self._extract_keywords(chapter_text)
            ))
        
        return chapters
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        
        # Simple keyword extraction
        from collections import Counter
        import re
        
        # Remove punctuation and lowercase
        text = re.sub(r'[^\w\s]', '', text.lower())
        words = text.split()
        
        # Remove common words
        common_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 
                           'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 
                           'was', 'are', 'were', 'be', 'been', 'being', 'have', 
                           'has', 'had', 'do', 'does', 'did', 'will', 'would'])
        
        words = [w for w in words if w not in common_words and len(w) > 3]
        
        # Get most common words
        word_counts = Counter(words)
        keywords = [word for word, _ in word_counts.most_common(5)]
        
        return keywords
    
    def navigate_to_time(
        self,
        transcript: TimestampedTranscript,
        target_time: float
    ) -> Dict[str, Any]:
        """Navigate to specific time in transcript"""
        
        # Find corresponding segment
        segment = None
        for seg in transcript.segments:
            if seg.start_time <= target_time <= seg.end_time:
                segment = seg
                break
        
        # Find corresponding word
        word = None
        for w in transcript.words:
            if w.start_time <= target_time <= w.end_time:
                word = w
                break
        
        # Update current position
        self.current_position = target_time
        
        # Log navigation event
        event = NavigationEvent(
            event_type=NavigationType.CLICK,
            timestamp=datetime.now().timestamp(),
            target_time=target_time,
            context={
                'segment': segment.text if segment else None,
                'word': word.word if word else None
            }
        )
        
        return {
            'current_time': target_time,
            'segment': segment,
            'word': word,
            'chapter': self._find_chapter(transcript, target_time)
        }
    
    def search_and_navigate(
        self,
        transcript: TimestampedTranscript,
        query: str
    ) -> List[Dict[str, Any]]:
        """Search transcript and return navigation points"""
        
        results = []
        query_lower = query.lower()
        
        # Search in segments
        for segment in transcript.segments:
            if query_lower in segment.text.lower():
                results.append({
                    'type': 'segment',
                    'text': segment.text,
                    'start_time': segment.start_time,
                    'end_time': segment.end_time,
                    'match_context': self._get_match_context(
                        segment.text, 
                        query_lower
                    )
                })
        
        # Search in words for exact matches
        for word in transcript.words:
            if query_lower == word.word.lower():
                results.append({
                    'type': 'word',
                    'text': word.word,
                    'start_time': word.start_time,
                    'end_time': word.end_time,
                    'confidence': word.confidence
                })
        
        return results
    
    def _get_match_context(self, text: str, query: str, context_size: int = 50) -> str:
        """Get context around matched query"""
        
        idx = text.lower().find(query)
        if idx == -1:
            return text
        
        start = max(0, idx - context_size)
        end = min(len(text), idx + len(query) + context_size)
        
        context = text[start:end]
        
        # Add ellipsis if truncated
        if start > 0:
            context = '...' + context
        if end < len(text):
            context = context + '...'
        
        return context
    
    def add_bookmark(
        self,
        transcript: TimestampedTranscript,
        timestamp: float,
        label: str,
        description: Optional[str] = None,
        category: Optional[str] = None
    ) -> Bookmark:
        """Add bookmark to transcript"""
        
        bookmark = Bookmark(
            bookmark_id=self._generate_id(),
            timestamp=timestamp,
            label=label,
            description=description,
            category=category
        )
        
        transcript.bookmarks.append(bookmark)
        
        # Sort bookmarks by timestamp
        transcript.bookmarks.sort(key=lambda b: b.timestamp)
        
        return bookmark
    
    def remove_bookmark(
        self,
        transcript: TimestampedTranscript,
        bookmark_id: str
    ) -> bool:
        """Remove bookmark from transcript"""
        
        for i, bookmark in enumerate(transcript.bookmarks):
            if bookmark.bookmark_id == bookmark_id:
                transcript.bookmarks.pop(i)
                return True
        
        return False
    
    def get_bookmarks_in_range(
        self,
        transcript: TimestampedTranscript,
        start_time: float,
        end_time: float
    ) -> List[Bookmark]:
        """Get bookmarks within time range"""
        
        return [
            b for b in transcript.bookmarks
            if start_time <= b.timestamp <= end_time
        ]
    
    def _find_chapter(
        self,
        transcript: TimestampedTranscript,
        timestamp: float
    ) -> Optional[Chapter]:
        """Find chapter containing timestamp"""
        
        for chapter in transcript.chapters:
            if chapter.start_time <= timestamp <= chapter.end_time:
                return chapter
        
        return None
    
    def export_timestamps(
        self,
        transcript: TimestampedTranscript,
        format: str = "json"
    ) -> str:
        """Export timestamps in various formats"""
        
        if format == "json":
            return self._export_json(transcript)
        elif format == "srt":
            return self._export_srt(transcript)
        elif format == "vtt":
            return self._export_vtt(transcript)
        elif format == "csv":
            return self._export_csv(transcript)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_json(self, transcript: TimestampedTranscript) -> str:
        """Export as JSON"""
        
        data = {
            'transcript_id': transcript.transcript_id,
            'duration': transcript.duration,
            'full_text': transcript.full_text,
            'segments': [
                {
                    'text': seg.text,
                    'start': seg.start_time,
                    'end': seg.end_time,
                    'speaker': seg.speaker_id,
                    'confidence': seg.confidence
                }
                for seg in transcript.segments
            ],
            'words': [
                {
                    'word': w.word,
                    'start': w.start_time,
                    'end': w.end_time,
                    'confidence': w.confidence,
                    'speaker': w.speaker_id
                }
                for w in transcript.words
            ],
            'chapters': [
                {
                    'title': ch.title,
                    'start': ch.start_time,
                    'end': ch.end_time,
                    'description': ch.description
                }
                for ch in transcript.chapters
            ],
            'bookmarks': [
                {
                    'timestamp': b.timestamp,
                    'label': b.label,
                    'description': b.description,
                    'category': b.category
                }
                for b in transcript.bookmarks
            ]
        }
        
        return json.dumps(data, indent=2)
    
    def _export_srt(self, transcript: TimestampedTranscript) -> str:
        """Export as SRT subtitle file"""
        
        srt_content = []
        
        for i, segment in enumerate(transcript.segments, 1):
            start_time = self._format_srt_time(segment.start_time)
            end_time = self._format_srt_time(segment.end_time)
            
            srt_content.append(f"{i}")
            srt_content.append(f"{start_time} --> {end_time}")
            srt_content.append(segment.text)
            srt_content.append("")  # Empty line between entries
        
        return '\n'.join(srt_content)
    
    def _export_vtt(self, transcript: TimestampedTranscript) -> str:
        """Export as WebVTT file"""
        
        vtt_content = ["WEBVTT", ""]
        
        for segment in transcript.segments:
            start_time = self._format_vtt_time(segment.start_time)
            end_time = self._format_vtt_time(segment.end_time)
            
            vtt_content.append(f"{start_time} --> {end_time}")
            vtt_content.append(segment.text)
            vtt_content.append("")  # Empty line between entries
        
        return '\n'.join(vtt_content)
    
    def _export_csv(self, transcript: TimestampedTranscript) -> str:
        """Export as CSV"""
        
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['start_time', 'end_time', 'text', 'speaker', 'confidence'])
        
        # Data
        for segment in transcript.segments:
            writer.writerow([
                segment.start_time,
                segment.end_time,
                segment.text,
                segment.speaker_id or '',
                segment.confidence
            ])
        
        return output.getvalue()
    
    def _format_srt_time(self, seconds: float) -> str:
        """Format time for SRT"""
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')
    
    def _format_vtt_time(self, seconds: float) -> str:
        """Format time for WebVTT"""
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        
        import uuid
        return str(uuid.uuid4())


# Interactive transcript component
class InteractiveTranscript:
    """Interactive transcript with click-to-play functionality"""
    
    def __init__(self, timestamping_system: AdvancedTimestampingSystem):
        self.timestamping_system = timestamping_system
        self.audio_player = None
        self.current_transcript: Optional[TimestampedTranscript] = None
        
    def load_transcript(self, transcript: TimestampedTranscript):
        """Load transcript for interaction"""
        self.current_transcript = transcript
        
    def handle_click(self, position: Dict[str, Any]) -> Dict[str, Any]:
        """Handle click on transcript"""
        
        if not self.current_transcript:
            return {'error': 'No transcript loaded'}
        
        # Find word at position
        word_index = position.get('word_index')
        
        if word_index is not None and 0 <= word_index < len(self.current_transcript.words):
            word = self.current_transcript.words[word_index]
            
            # Navigate to word time
            result = self.timestamping_system.navigate_to_time(
                self.current_transcript,
                word.start_time
            )
            
            # Trigger audio playback
            if self.audio_player:
                self.audio_player.seek(word.start_time)
                self.audio_player.play()
            
            return {
                'success': True,
                'current_time': word.start_time,
                'word': word.word,
                'segment': result.get('segment')
            }
        
        return {'error': 'Invalid position'}
    
    def handle_search(self, query: str) -> List[Dict[str, Any]]:
        """Handle search in transcript"""
        
        if not self.current_transcript:
            return []
        
        return self.timestamping_system.search_and_navigate(
            self.current_transcript,
            query
        )
    
    def get_current_word(self, current_time: float) -> Optional[WordTimestamp]:
        """Get word at current playback time"""
        
        if not self.current_transcript:
            return None
        
        for word in self.current_transcript.words:
            if word.start_time <= current_time <= word.end_time:
                return word
        
        return None
    
    def get_visible_range(
        self,
        current_time: float,
        window_size: float = 10.0
    ) -> Tuple[List[WordTimestamp], List[SegmentTimestamp]]:
        """Get words and segments in visible range"""
        
        if not self.current_transcript:
            return [], []
        
        start_time = max(0, current_time - window_size / 2)
        end_time = min(
            self.current_transcript.duration,
            current_time + window_size / 2
        )
        
        # Get words in range
        visible_words = [
            w for w in self.current_transcript.words
            if start_time <= w.start_time <= end_time
        ]
        
        # Get segments in range
        visible_segments = [
            s for s in self.current_transcript.segments
            if s.start_time <= end_time and s.end_time >= start_time
        ]
        
        return visible_words, visible_segments


# Example usage
async def main():
    """Example usage of timestamping system"""
    
    # Initialize system
    timestamp_system = AdvancedTimestampingSystem()
    
    # Generate timestamps
    transcript = await timestamp_system.generate_timestamps(
        "sample_audio.mp3",
        granularity=TimestampGranularity.SENTENCE,
        enable_diarization=True,
        language="en"
    )
    
    print(f"Generated transcript with {len(transcript.words)} words")
    print(f"Segments: {len(transcript.segments)}")
    print(f"Chapters: {len(transcript.chapters)}")
    
    # Add bookmark
    bookmark = timestamp_system.add_bookmark(
        transcript,
        timestamp=30.5,
        label="Important moment",
        description="Key point discussed"
    )
    print(f"Added bookmark: {bookmark.label}")
    
    # Search and navigate
    results = timestamp_system.search_and_navigate(transcript, "hello")
    print(f"Found {len(results)} matches for 'hello'")
    
    # Export
    json_export = timestamp_system.export_timestamps(transcript, "json")
    print("Exported to JSON")
    
    # Interactive usage
    interactive = InteractiveTranscript(timestamp_system)
    interactive.load_transcript(transcript)
    
    # Simulate click on word
    click_result = interactive.handle_click({'word_index': 10})
    print(f"Clicked word: {click_result.get('word')}")


if __name__ == "__main__":
    asyncio.run(main())