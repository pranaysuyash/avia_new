"""
Base class for speaker diarization providers
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging

from ..diarization_manager import DiarizationResult

logger = logging.getLogger(__name__)


class BaseDiarizationProvider(ABC):
    """Abstract base class for diarization providers"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = self.__class__.__name__
        
    @abstractmethod
    async def diarize(self, 
                     audio_path: str,
                     min_segment_duration: float = 1.0,
                     max_speakers: Optional[int] = None) -> DiarizationResult:
        """
        Perform speaker diarization on audio file
        
        Args:
            audio_path: Path to audio file
            min_segment_duration: Minimum duration for a speaker segment
            max_speakers: Maximum number of speakers to detect
            
        Returns:
            DiarizationResult with speaker segments
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available/installed"""
        pass
    
    def get_requirements(self) -> Dict[str, str]:
        """Get provider requirements"""
        return {
            'name': self.name,
            'description': 'Base diarization provider',
            'dependencies': []
        }
    
    def validate_audio_file(self, audio_path: str) -> bool:
        """Validate that audio file exists and is readable"""
        import os
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        if not os.access(audio_path, os.R_OK):
            raise PermissionError(f"Cannot read audio file: {audio_path}")
        
        return True
    
    def get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds"""
        try:
            import subprocess
            import json
            
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'json',
                audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return float(data['format']['duration'])
                
        except Exception as e:
            logger.warning(f"Could not get audio duration using ffprobe: {e}")
        
        # Fallback: try with wave or other libraries
        try:
            import wave
            with wave.open(audio_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                return frames / float(rate)
        except:
            pass
        
        # Default to 0 if we can't determine duration
        return 0.0