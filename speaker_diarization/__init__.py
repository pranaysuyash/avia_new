"""
Speaker diarization module for identifying and separating speakers in audio
"""

from .diarization_manager import DiarizationManager, DiarizationResult, SpeakerSegment
from .providers import (
    BaseDiarizationProvider,
    PyannoteProvider,
    SimpleVADProvider,
    MockProvider
)

__all__ = [
    'DiarizationManager',
    'DiarizationResult', 
    'SpeakerSegment',
    'BaseDiarizationProvider',
    'PyannoteProvider',
    'SimpleVADProvider',
    'MockProvider'
]