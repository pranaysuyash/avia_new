"""
PyAnnote audio provider for speaker diarization
"""

import logging
from typing import Optional, Dict, Any
import asyncio
from pathlib import Path

from .base import BaseDiarizationProvider
from ..diarization_manager import DiarizationResult, SpeakerSegment

logger = logging.getLogger(__name__)


class PyannoteProvider(BaseDiarizationProvider):
    """Speaker diarization using pyannote.audio"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.pipeline = None
        config = config or {}
        self.model_name = config.get('model', 'pyannote/speaker-diarization')
        self.use_auth_token = config.get('huggingface_token')
        self._initialize_pipeline()
        
    def _initialize_pipeline(self):
        """Initialize the pyannote pipeline"""
        try:
            from pyannote.audio import Pipeline
            
            logger.info(f"Loading pyannote model: {self.model_name}")
            self.pipeline = Pipeline.from_pretrained(
                self.model_name,
                use_auth_token=self.use_auth_token
            )
            
            # Use GPU if available
            import torch
            if torch.cuda.is_available() and self.config.get('use_gpu', True):
                self.pipeline = self.pipeline.to(torch.device('cuda'))
                logger.info("Using GPU for diarization")
            else:
                logger.info("Using CPU for diarization")
                
        except ImportError:
            logger.warning("pyannote.audio not installed. Install with: pip install pyannote.audio")
            self.pipeline = None
        except Exception as e:
            logger.error(f"Failed to initialize pyannote pipeline: {e}")
            self.pipeline = None
    
    def is_available(self) -> bool:
        """Check if pyannote is available"""
        try:
            import pyannote.audio
            import torch
            return self.pipeline is not None
        except ImportError:
            return False
    
    async def diarize(self, 
                     audio_path: str,
                     min_segment_duration: float = 1.0,
                     max_speakers: Optional[int] = None) -> DiarizationResult:
        """Perform speaker diarization using pyannote"""
        if not self.is_available():
            raise RuntimeError("PyAnnote provider is not available")
        
        self.validate_audio_file(audio_path)
        
        # Get audio duration
        audio_duration = self.get_audio_duration(audio_path)
        
        # Run diarization in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        diarization = await loop.run_in_executor(
            None,
            self._run_diarization,
            audio_path,
            min_segment_duration,
            max_speakers
        )
        
        # Convert pyannote output to our format
        result = DiarizationResult(audio_duration=audio_duration)
        result.metadata = {
            'provider': 'pyannote',
            'model': self.model_name,
            'min_segment_duration': min_segment_duration,
            'max_speakers': max_speakers
        }
        
        # Process diarization output
        speaker_mapping = {}
        speaker_counter = 1
        
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            # Map pyannote speaker labels to our format
            if speaker not in speaker_mapping:
                speaker_mapping[speaker] = f"speaker_{speaker_counter}"
                speaker_counter += 1
            
            speaker_id = speaker_mapping[speaker]
            
            # Create segment
            segment = SpeakerSegment(
                speaker_id=speaker_id,
                start_time=turn.start,
                end_time=turn.end,
                confidence=0.95  # PyAnnote doesn't provide confidence scores
            )
            
            # Skip segments that are too short
            if segment.duration >= min_segment_duration:
                result.add_segment(segment)
        
        logger.info(f"Diarization completed: {len(result.speakers)} speakers, {len(result.segments)} segments")
        return result
    
    def _run_diarization(self, 
                        audio_path: str,
                        min_segment_duration: float,
                        max_speakers: Optional[int]) -> Any:
        """Run the actual diarization (blocking)"""
        # Configure pipeline parameters
        params = {}
        
        if min_segment_duration:
            params['min_duration_on'] = min_segment_duration
            
        if max_speakers:
            params['max_speakers'] = max_speakers
        
        # Run diarization
        logger.info(f"Running pyannote diarization on {audio_path}")
        diarization = self.pipeline(audio_path, **params)
        
        return diarization
    
    def get_requirements(self) -> Dict[str, str]:
        """Get provider requirements"""
        return {
            'name': 'PyAnnote Audio',
            'description': 'State-of-the-art speaker diarization using deep learning',
            'dependencies': [
                'pyannote.audio>=2.1',
                'torch>=1.9',
                'torchaudio',
                'speechbrain'
            ],
            'features': [
                'High accuracy',
                'GPU acceleration',
                'Pre-trained models',
                'Overlapping speech detection'
            ],
            'limitations': [
                'Requires HuggingFace token for some models',
                'Large model size (~1GB)',
                'Slower on CPU'
            ]
        }