"""
Mock provider for testing and development
"""

import logging
from typing import Optional, Dict, Any
import asyncio
import random

from .base import BaseDiarizationProvider
from ..diarization_manager import DiarizationResult, SpeakerSegment

logger = logging.getLogger(__name__)


class MockProvider(BaseDiarizationProvider):
    """Mock diarization provider for testing"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.processing_delay = (config or {}).get('processing_delay', 1.0)
        
    def is_available(self) -> bool:
        """Always available for testing"""
        return True
    
    async def diarize(self, 
                     audio_path: str,
                     min_segment_duration: float = 1.0,
                     max_speakers: Optional[int] = None) -> DiarizationResult:
        """Generate mock diarization results"""
        self.validate_audio_file(audio_path)
        
        # Simulate processing delay
        await asyncio.sleep(self.processing_delay)
        
        # Get audio duration (mock it as 5 minutes)
        audio_duration = 300.0  # 5 minutes
        
        # Create result
        result = DiarizationResult(audio_duration=audio_duration)
        result.metadata = {
            'provider': 'mock',
            'test_mode': True,
            'audio_path': audio_path
        }
        
        # Generate mock segments
        num_speakers = min(max_speakers or 3, 3)
        speakers = [f"speaker_{i+1}" for i in range(num_speakers)]
        
        # Create realistic conversation pattern
        current_time = 0.0
        segment_count = 50  # Total segments
        
        for i in range(segment_count):
            # Pick a speaker (with some continuity)
            if i == 0 or random.random() > 0.7:
                current_speaker = random.choice(speakers)
            else:
                # Continue with same speaker
                current_speaker = result.segments[-1].speaker_id if result.segments else speakers[0]
            
            # Generate segment duration (between 2 and 15 seconds)
            duration = random.uniform(2.0, 15.0)
            
            # Add small gap between speakers (0.1 to 0.5 seconds)
            if i > 0 and result.segments[-1].speaker_id != current_speaker:
                gap = random.uniform(0.1, 0.5)
                current_time += gap
            
            # Create segment
            segment = SpeakerSegment(
                speaker_id=current_speaker,
                start_time=current_time,
                end_time=current_time + duration,
                confidence=random.uniform(0.85, 0.99),
                text=f"Mock speech segment {i+1}"
            )
            
            if segment.duration >= min_segment_duration:
                result.add_segment(segment)
            
            current_time = segment.end_time
            
            # Stop if we've reached the audio duration
            if current_time >= audio_duration - 10:
                break
        
        # Add some realistic patterns
        self._add_conversation_patterns(result)
        
        logger.info(f"Mock diarization completed: {len(result.speakers)} speakers, {len(result.segments)} segments")
        return result
    
    def _add_conversation_patterns(self, result: DiarizationResult):
        """Add realistic conversation patterns to mock data"""
        # Simulate a meeting scenario with introduction, discussion, and conclusion
        if len(result.segments) > 10:
            # Introduction phase - mostly speaker 1
            for i in range(min(5, len(result.segments))):
                if random.random() > 0.3:
                    result.segments[i].speaker_id = "speaker_1"
            
            # Discussion phase - more balanced
            # (segments already have good distribution)
            
            # Conclusion phase - mostly speaker 1 again
            for i in range(max(0, len(result.segments) - 5), len(result.segments)):
                if random.random() > 0.4:
                    result.segments[i].speaker_id = "speaker_1"
    
    def get_requirements(self) -> Dict[str, str]:
        """Get provider requirements"""
        return {
            'name': 'Mock Provider',
            'description': 'Mock diarization for testing and development',
            'dependencies': [],
            'features': [
                'No dependencies required',
                'Instant results',
                'Configurable patterns',
                'Reproducible results'
            ],
            'limitations': [
                'Not real diarization',
                'For testing only'
            ]
        }