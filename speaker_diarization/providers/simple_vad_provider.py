"""
Simple Voice Activity Detection based speaker diarization
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
import asyncio
import numpy as np
from pathlib import Path

from .base import BaseDiarizationProvider
from ..diarization_manager import DiarizationResult, SpeakerSegment

logger = logging.getLogger(__name__)


class SimpleVADProvider(BaseDiarizationProvider):
    """Simple speaker diarization using energy-based VAD and speaker changes"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        config = config or {}
        self.energy_threshold = config.get('energy_threshold', 0.02)
        self.min_silence_duration = config.get('min_silence_duration', 0.5)
        self.min_speech_duration = config.get('min_speech_duration', 0.5)
        
    def is_available(self) -> bool:
        """Check if required libraries are available"""
        try:
            import scipy.io.wavfile
            import numpy as np
            return True
        except ImportError:
            return False
    
    async def diarize(self, 
                     audio_path: str,
                     min_segment_duration: float = 1.0,
                     max_speakers: Optional[int] = None) -> DiarizationResult:
        """Perform simple VAD-based speaker diarization"""
        if not self.is_available():
            raise RuntimeError("SimpleVAD provider is not available (requires scipy)")
        
        self.validate_audio_file(audio_path)
        
        # Load audio
        loop = asyncio.get_event_loop()
        sample_rate, audio_data = await loop.run_in_executor(
            None,
            self._load_audio,
            audio_path
        )
        
        # Get audio duration
        audio_duration = len(audio_data) / sample_rate
        
        # Detect speech segments
        speech_segments = await loop.run_in_executor(
            None,
            self._detect_speech_segments,
            audio_data,
            sample_rate
        )
        
        # Simple speaker assignment based on gaps
        result = DiarizationResult(audio_duration=audio_duration)
        result.metadata = {
            'provider': 'simple_vad',
            'energy_threshold': self.energy_threshold,
            'sample_rate': sample_rate
        }
        
        # Assign speakers based on silence gaps
        current_speaker = 1
        speaker_id = f"speaker_{current_speaker}"
        
        for i, (start, end) in enumerate(speech_segments):
            # Check if there's a significant gap indicating speaker change
            if i > 0:
                gap = start - speech_segments[i-1][1]
                if gap > 2.0:  # 2 second gap suggests speaker change
                    current_speaker = 2 if current_speaker == 1 else 1
                    speaker_id = f"speaker_{current_speaker}"
            
            # Create segment
            segment = SpeakerSegment(
                speaker_id=speaker_id,
                start_time=start,
                end_time=end,
                confidence=0.7  # Lower confidence for simple VAD
            )
            
            if segment.duration >= min_segment_duration:
                result.add_segment(segment)
        
        # Limit speakers if requested
        if max_speakers and len(result.speakers) > max_speakers:
            # Simple merging of least active speakers
            speakers_by_time = sorted(
                result.speakers.values(),
                key=lambda s: s.total_time
            )
            
            while len(result.speakers) > max_speakers:
                # Merge least active speaker into second least
                to_merge = speakers_by_time[0].speaker_id
                merge_into = speakers_by_time[1].speaker_id
                result.merge_speakers(to_merge, merge_into)
                speakers_by_time = speakers_by_time[1:]
        
        logger.info(f"Simple VAD diarization completed: {len(result.speakers)} speakers, {len(result.segments)} segments")
        return result
    
    def _load_audio(self, audio_path: str) -> Tuple[int, np.ndarray]:
        """Load audio file and convert to mono"""
        try:
            import scipy.io.wavfile as wavfile
            
            # Try to load as WAV first
            if audio_path.endswith('.wav'):
                sample_rate, audio_data = wavfile.read(audio_path)
            else:
                # Convert to WAV using ffmpeg
                import subprocess
                import tempfile
                
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    tmp_path = tmp_file.name
                
                cmd = [
                    'ffmpeg', '-i', audio_path,
                    '-ar', '16000',  # 16kHz sample rate
                    '-ac', '1',      # Mono
                    '-y', tmp_path
                ]
                
                subprocess.run(cmd, check=True, capture_output=True)
                sample_rate, audio_data = wavfile.read(tmp_path)
                
                # Clean up
                Path(tmp_path).unlink()
            
            # Convert to float and normalize
            if audio_data.dtype == np.int16:
                audio_data = audio_data.astype(np.float32) / 32768.0
            elif audio_data.dtype == np.int32:
                audio_data = audio_data.astype(np.float32) / 2147483648.0
            
            # Convert to mono if stereo
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            return sample_rate, audio_data
            
        except Exception as e:
            logger.error(f"Failed to load audio: {e}")
            raise
    
    def _detect_speech_segments(self, 
                               audio_data: np.ndarray,
                               sample_rate: int) -> List[Tuple[float, float]]:
        """Detect speech segments using energy-based VAD"""
        # Calculate frame energy
        frame_size = int(0.025 * sample_rate)  # 25ms frames
        frame_shift = int(0.010 * sample_rate)  # 10ms shift
        
        energies = []
        for i in range(0, len(audio_data) - frame_size, frame_shift):
            frame = audio_data[i:i + frame_size]
            energy = np.sqrt(np.mean(frame ** 2))
            energies.append(energy)
        
        energies = np.array(energies)
        
        # Dynamic threshold based on energy distribution
        sorted_energies = np.sort(energies)
        noise_level = np.mean(sorted_energies[:len(sorted_energies)//10])  # Bottom 10%
        threshold = max(self.energy_threshold, noise_level * 3)
        
        # Detect speech frames
        speech_frames = energies > threshold
        
        # Apply smoothing to remove short gaps/spikes
        min_silence_frames = int(self.min_silence_duration * sample_rate / frame_shift)
        min_speech_frames = int(self.min_speech_duration * sample_rate / frame_shift)
        
        # Fill short gaps
        for i in range(min_silence_frames, len(speech_frames) - min_silence_frames):
            if not speech_frames[i]:
                # Check if surrounded by speech
                if np.all(speech_frames[i-min_silence_frames:i]) and \
                   np.all(speech_frames[i+1:i+min_silence_frames+1]):
                    speech_frames[i] = True
        
        # Remove short speech segments
        segments = []
        start_idx = None
        
        for i, is_speech in enumerate(speech_frames):
            if is_speech and start_idx is None:
                start_idx = i
            elif not is_speech and start_idx is not None:
                if i - start_idx >= min_speech_frames:
                    start_time = start_idx * frame_shift / sample_rate
                    end_time = i * frame_shift / sample_rate
                    segments.append((start_time, end_time))
                start_idx = None
        
        # Handle final segment
        if start_idx is not None:
            end_time = len(speech_frames) * frame_shift / sample_rate
            if len(speech_frames) - start_idx >= min_speech_frames:
                start_time = start_idx * frame_shift / sample_rate
                segments.append((start_time, end_time))
        
        return segments
    
    def get_requirements(self) -> Dict[str, str]:
        """Get provider requirements"""
        return {
            'name': 'Simple VAD',
            'description': 'Basic speaker diarization using Voice Activity Detection',
            'dependencies': [
                'scipy',
                'numpy',
                'ffmpeg (system)'
            ],
            'features': [
                'Lightweight',
                'Fast processing',
                'No model download required',
                'Works offline'
            ],
            'limitations': [
                'Limited accuracy',
                'No overlapping speech detection',
                'Simple speaker change detection',
                'Best for clear, two-speaker conversations'
            ]
        }