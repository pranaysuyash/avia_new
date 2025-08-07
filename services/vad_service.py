"""
Voice Activity Detection Service
Detects speech segments in audio files
"""

import webrtcvad
import wave
import contextlib
import collections
from typing import List, Dict, Tuple
import numpy as np
from pydub import AudioSegment
import tempfile
import os
import logging

logger = logging.getLogger(__name__)


class VADService:
    """Voice Activity Detection service using WebRTC VAD"""
    
    def __init__(self, aggressiveness: int = 2):
        """
        Initialize VAD service
        
        Args:
            aggressiveness: VAD aggressiveness level (0-3)
                0: Less aggressive (more permissive)
                3: Most aggressive (more restrictive)
        """
        self.vad = webrtcvad.Vad(aggressiveness)
        self.frame_duration_ms = 30  # Frame duration in milliseconds
        self.sample_rate = 16000  # Required sample rate for WebRTC VAD
        self.padding_duration_ms = 300  # Padding around speech segments
    
    def detect_speech_segments(
        self,
        audio_path: str,
        min_silence_duration: float = 0.5
    ) -> List[Dict[str, float]]:
        """
        Detect speech segments in audio file
        
        Args:
            audio_path: Path to audio file
            min_silence_duration: Minimum silence duration to split segments
        
        Returns:
            List of segments with start and end times
        """
        # Convert audio to required format
        wav_path = self._convert_to_wav(audio_path)
        
        try:
            # Read audio frames
            audio, sample_rate = self._read_wave(wav_path)
            
            # Resample if necessary
            if sample_rate != self.sample_rate:
                audio = self._resample_audio(audio, sample_rate, self.sample_rate)
            
            # Detect voiced frames
            frames = self._frame_generator(audio)
            voiced_frames = self._detect_voiced_frames(frames)
            
            # Convert to segments
            segments = self._frames_to_segments(voiced_frames, min_silence_duration)
            
            return segments
            
        finally:
            # Clean up temp file
            if wav_path != audio_path and os.path.exists(wav_path):
                os.unlink(wav_path)
    
    def _convert_to_wav(self, audio_path: str) -> str:
        """Convert audio to WAV format if needed"""
        if audio_path.endswith('.wav'):
            return audio_path
        
        # Convert using pydub
        audio = AudioSegment.from_file(audio_path)
        
        # Convert to mono and correct sample rate
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(self.sample_rate)
        
        # Save to temp file
        temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        audio.export(temp_wav.name, format="wav")
        temp_wav.close()
        
        return temp_wav.name
    
    def _read_wave(self, path: str) -> Tuple[bytes, int]:
        """Read wave file and return audio data and sample rate"""
        with contextlib.closing(wave.open(path, 'rb')) as wf:
            num_channels = wf.getnchannels()
            assert num_channels == 1, "Audio must be mono"
            
            sample_width = wf.getsampwidth()
            assert sample_width == 2, "Audio must be 16-bit"
            
            sample_rate = wf.getframerate()
            frames = wf.readframes(wf.getnframes())
            
            return frames, sample_rate
    
    def _resample_audio(
        self,
        audio: bytes,
        orig_sample_rate: int,
        target_sample_rate: int
    ) -> bytes:
        """Resample audio to target sample rate"""
        # Convert bytes to numpy array
        audio_array = np.frombuffer(audio, dtype=np.int16)
        
        # Calculate resampling ratio
        ratio = target_sample_rate / orig_sample_rate
        
        # Resample
        new_length = int(len(audio_array) * ratio)
        resampled = np.interp(
            np.linspace(0, len(audio_array) - 1, new_length),
            np.arange(len(audio_array)),
            audio_array
        ).astype(np.int16)
        
        return resampled.tobytes()
    
    def _frame_generator(self, audio: bytes) -> List[bytes]:
        """Generate audio frames"""
        frame_size = int(self.sample_rate * self.frame_duration_ms / 1000) * 2
        offset = 0
        frames = []
        
        while offset + frame_size <= len(audio):
            frames.append(audio[offset:offset + frame_size])
            offset += frame_size
        
        return frames
    
    def _detect_voiced_frames(self, frames: List[bytes]) -> List[bool]:
        """Detect which frames contain speech"""
        voiced = []
        
        for frame in frames:
            is_speech = self.vad.is_speech(frame, self.sample_rate)
            voiced.append(is_speech)
        
        return voiced
    
    def _frames_to_segments(
        self,
        voiced_frames: List[bool],
        min_silence_duration: float
    ) -> List[Dict[str, float]]:
        """Convert voiced frames to time segments"""
        segments = []
        
        # Convert frame duration to seconds
        frame_duration_s = self.frame_duration_ms / 1000.0
        
        # Minimum silence frames
        min_silence_frames = int(min_silence_duration / frame_duration_s)
        
        # Padding frames
        padding_frames = int(self.padding_duration_ms / self.frame_duration_ms)
        
        # Find segments
        in_segment = False
        segment_start = 0
        silence_count = 0
        
        for i, is_voiced in enumerate(voiced_frames):
            if is_voiced:
                if not in_segment:
                    # Start new segment
                    segment_start = max(0, i - padding_frames)
                    in_segment = True
                silence_count = 0
            else:
                if in_segment:
                    silence_count += 1
                    if silence_count >= min_silence_frames:
                        # End segment
                        segment_end = min(len(voiced_frames) - 1, i - silence_count + padding_frames)
                        segments.append({
                            "start": segment_start * frame_duration_s,
                            "end": segment_end * frame_duration_s
                        })
                        in_segment = False
                        silence_count = 0
        
        # Handle last segment
        if in_segment:
            segment_end = len(voiced_frames) - 1
            segments.append({
                "start": segment_start * frame_duration_s,
                "end": segment_end * frame_duration_s
            })
        
        return segments
    
    def get_speech_ratio(self, audio_path: str) -> float:
        """Get ratio of speech to total audio duration"""
        segments = self.detect_speech_segments(audio_path)
        
        if not segments:
            return 0.0
        
        # Calculate total speech duration
        speech_duration = sum(s["end"] - s["start"] for s in segments)
        
        # Get total audio duration
        audio = AudioSegment.from_file(audio_path)
        total_duration = len(audio) / 1000.0
        
        return speech_duration / total_duration if total_duration > 0 else 0.0