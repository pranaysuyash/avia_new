"""
Core speaker diarization management system
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import json
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SpeakerSegment:
    """Represents a segment of audio attributed to a specific speaker"""
    speaker_id: str
    start_time: float
    end_time: float
    confidence: float = 1.0
    text: Optional[str] = None
    embedding: Optional[List[float]] = None
    
    @property
    def duration(self) -> float:
        """Duration of the segment in seconds"""
        return self.end_time - self.start_time
    
    def overlaps_with(self, other: 'SpeakerSegment') -> bool:
        """Check if this segment overlaps with another"""
        return not (self.end_time <= other.start_time or self.start_time >= other.end_time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'speaker_id': self.speaker_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'confidence': self.confidence,
            'text': self.text,
            'duration': self.duration
        }


@dataclass
class SpeakerInfo:
    """Information about a speaker"""
    speaker_id: str
    label: Optional[str] = None
    color: Optional[str] = None
    total_time: float = 0.0
    segment_count: int = 0
    average_confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'speaker_id': self.speaker_id,
            'label': self.label or self.speaker_id,
            'color': self.color,
            'total_time': self.total_time,
            'segment_count': self.segment_count,
            'average_confidence': self.average_confidence,
            'speaking_percentage': 0.0  # Will be calculated later
        }


@dataclass
class DiarizationResult:
    """Complete result of speaker diarization"""
    segments: List[SpeakerSegment] = field(default_factory=list)
    speakers: Dict[str, SpeakerInfo] = field(default_factory=dict)
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    audio_duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_segment(self, segment: SpeakerSegment):
        """Add a segment and update speaker info"""
        self.segments.append(segment)
        
        # Update or create speaker info
        if segment.speaker_id not in self.speakers:
            self.speakers[segment.speaker_id] = SpeakerInfo(
                speaker_id=segment.speaker_id,
                color=self._generate_color(len(self.speakers))
            )
        
        speaker = self.speakers[segment.speaker_id]
        speaker.total_time += segment.duration
        speaker.segment_count += 1
        
        # Update average confidence
        total_confidence = speaker.average_confidence * (speaker.segment_count - 1) + segment.confidence
        speaker.average_confidence = total_confidence / speaker.segment_count
    
    def _generate_color(self, index: int) -> str:
        """Generate a color for speaker visualization"""
        colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57',
            '#FF9FF3', '#54A0FF', '#48DBFB', '#A29BFE', '#FD79A8'
        ]
        return colors[index % len(colors)]
    
    def calculate_statistics(self):
        """Calculate speaking percentages and other statistics"""
        if self.audio_duration > 0:
            for speaker in self.speakers.values():
                speaker.speaking_percentage = (speaker.total_time / self.audio_duration) * 100
    
    def generate_timeline(self, resolution: float = 1.0):
        """Generate timeline data for visualization"""
        if not self.segments or self.audio_duration <= 0:
            return
        
        # Create timeline bins
        num_bins = int(self.audio_duration / resolution)
        timeline_data = []
        
        for i in range(num_bins):
            bin_start = i * resolution
            bin_end = (i + 1) * resolution
            bin_speakers = {}
            
            # Check which speakers are active in this bin
            for segment in self.segments:
                if segment.start_time < bin_end and segment.end_time > bin_start:
                    overlap_start = max(segment.start_time, bin_start)
                    overlap_end = min(segment.end_time, bin_end)
                    overlap_duration = overlap_end - overlap_start
                    
                    if segment.speaker_id not in bin_speakers:
                        bin_speakers[segment.speaker_id] = 0
                    bin_speakers[segment.speaker_id] += overlap_duration / resolution
            
            timeline_data.append({
                'time': bin_start,
                'speakers': bin_speakers
            })
        
        self.timeline = timeline_data
    
    def merge_speakers(self, speaker_id1: str, speaker_id2: str, new_id: Optional[str] = None):
        """Merge two speakers into one"""
        if speaker_id1 not in self.speakers or speaker_id2 not in self.speakers:
            raise ValueError("Both speaker IDs must exist")
        
        # Use first speaker ID if no new ID provided
        target_id = new_id or speaker_id1
        source_id = speaker_id2 if target_id == speaker_id1 else speaker_id1
        
        # Update segments
        for segment in self.segments:
            if segment.speaker_id == source_id:
                segment.speaker_id = target_id
        
        # Merge speaker info
        if target_id != speaker_id1:
            self.speakers[target_id] = self.speakers[speaker_id1]
            self.speakers[target_id].speaker_id = target_id
        
        target_speaker = self.speakers[target_id]
        source_speaker = self.speakers[source_id]
        
        # Combine statistics
        total_segments = target_speaker.segment_count + source_speaker.segment_count
        target_speaker.average_confidence = (
            (target_speaker.average_confidence * target_speaker.segment_count +
             source_speaker.average_confidence * source_speaker.segment_count) / total_segments
        )
        target_speaker.total_time += source_speaker.total_time
        target_speaker.segment_count = total_segments
        
        # Remove source speaker
        del self.speakers[source_id]
        if speaker_id1 != target_id:
            del self.speakers[speaker_id1]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'segments': [seg.to_dict() for seg in self.segments],
            'speakers': {sid: speaker.to_dict() for sid, speaker in self.speakers.items()},
            'timeline': self.timeline,
            'audio_duration': self.audio_duration,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DiarizationResult':
        """Create from dictionary"""
        result = cls(audio_duration=data.get('audio_duration', 0.0))
        
        # Reconstruct segments
        for seg_data in data.get('segments', []):
            segment = SpeakerSegment(
                speaker_id=seg_data['speaker_id'],
                start_time=seg_data['start_time'],
                end_time=seg_data['end_time'],
                confidence=seg_data.get('confidence', 1.0),
                text=seg_data.get('text')
            )
            result.segments.append(segment)
        
        # Reconstruct speakers
        for sid, speaker_data in data.get('speakers', {}).items():
            speaker = SpeakerInfo(
                speaker_id=sid,
                label=speaker_data.get('label'),
                color=speaker_data.get('color'),
                total_time=speaker_data.get('total_time', 0.0),
                segment_count=speaker_data.get('segment_count', 0),
                average_confidence=speaker_data.get('average_confidence', 1.0)
            )
            result.speakers[sid] = speaker
        
        result.timeline = data.get('timeline', [])
        result.metadata = data.get('metadata', {})
        
        return result


class DiarizationManager:
    """Manages speaker diarization operations"""
    
    def __init__(self, provider: Optional['BaseDiarizationProvider'] = None):
        self.provider = provider
        self.cache_dir = Path("cache/diarization")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def set_provider(self, provider: 'BaseDiarizationProvider'):
        """Set the diarization provider"""
        self.provider = provider
        
    async def process_audio(self, 
                          audio_path: str,
                          min_segment_duration: float = 1.0,
                          max_speakers: Optional[int] = None,
                          use_cache: bool = True) -> DiarizationResult:
        """Process audio file for speaker diarization"""
        if not self.provider:
            raise ValueError("No diarization provider set")
        
        # Check cache
        cache_key = self._get_cache_key(audio_path)
        if use_cache:
            cached_result = self._load_from_cache(cache_key)
            if cached_result:
                logger.info(f"Loaded diarization from cache for {audio_path}")
                return cached_result
        
        logger.info(f"Starting speaker diarization for {audio_path}")
        
        try:
            # Run diarization
            result = await self.provider.diarize(
                audio_path,
                min_segment_duration=min_segment_duration,
                max_speakers=max_speakers
            )
            
            # Post-process results
            result = self._post_process(result, min_segment_duration)
            
            # Generate timeline
            result.generate_timeline()
            
            # Calculate statistics
            result.calculate_statistics()
            
            # Cache result
            if use_cache:
                self._save_to_cache(cache_key, result)
            
            logger.info(f"Diarization completed: {len(result.speakers)} speakers found")
            return result
            
        except Exception as e:
            logger.error(f"Diarization failed: {str(e)}")
            raise
    
    def _post_process(self, result: DiarizationResult, min_duration: float) -> DiarizationResult:
        """Post-process diarization results"""
        # Remove very short segments
        result.segments = [
            seg for seg in result.segments 
            if seg.duration >= min_duration
        ]
        
        # Sort segments by start time
        result.segments.sort(key=lambda x: x.start_time)
        
        # Merge adjacent segments from same speaker
        merged_segments = []
        for segment in result.segments:
            if merged_segments and merged_segments[-1].speaker_id == segment.speaker_id:
                # Check if segments are close enough to merge
                gap = segment.start_time - merged_segments[-1].end_time
                if gap < 0.5:  # 500ms gap threshold
                    merged_segments[-1].end_time = segment.end_time
                    continue
            merged_segments.append(segment)
        
        result.segments = merged_segments
        
        # Recalculate speaker statistics
        result.speakers.clear()
        for segment in result.segments:
            result.add_segment(segment)
        
        return result
    
    def align_with_transcript(self, 
                            diarization_result: DiarizationResult,
                            transcript_segments: List[Dict[str, Any]]) -> DiarizationResult:
        """Align speaker segments with transcript segments"""
        # This will be implemented to match speaker segments with transcript text
        # For now, return the original result
        return diarization_result
    
    def update_speaker_label(self, 
                           result: DiarizationResult,
                           speaker_id: str,
                           new_label: str) -> DiarizationResult:
        """Update speaker label"""
        if speaker_id in result.speakers:
            result.speakers[speaker_id].label = new_label
        return result
    
    def _get_cache_key(self, audio_path: str) -> str:
        """Generate cache key for audio file"""
        import hashlib
        path_hash = hashlib.md5(audio_path.encode()).hexdigest()
        return f"diarization_{path_hash}"
    
    def _load_from_cache(self, cache_key: str) -> Optional[DiarizationResult]:
        """Load diarization result from cache"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                return DiarizationResult.from_dict(data)
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
        return None
    
    def _save_to_cache(self, cache_key: str, result: DiarizationResult):
        """Save diarization result to cache"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(result.to_dict(), f)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")