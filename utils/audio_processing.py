"""
Audio Processing Utilities
Handles audio preprocessing, enhancement, and format conversion
"""

import os
import logging
import numpy as np
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
import tempfile

import librosa
import soundfile as sf
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
from pydub.silence import detect_nonsilent
import noisereduce as nr
from scipy import signal
from scipy.io import wavfile
import torch
import torchaudio
import torchaudio.transforms as T

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Audio processing and enhancement utilities"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.target_sample_rate = self.config.get('sample_rate', 16000)
        self.target_channels = self.config.get('channels', 1)  # Mono by default
        
    async def process_audio(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        normalize: bool = True,
        remove_noise: bool = True,
        enhance_speech: bool = True,
        remove_silence: bool = False,
        convert_format: Optional[str] = 'wav'
    ) -> str:
        """Process and enhance audio file"""
        
        try:
            # Create temporary output if not specified
            if not output_path:
                temp_dir = tempfile.mkdtemp()
                output_path = os.path.join(temp_dir, f"processed.{convert_format or 'wav'}")
            
            # Load audio
            audio = AudioSegment.from_file(input_path)
            
            # Convert to mono if needed
            if audio.channels > 1 and self.target_channels == 1:
                audio = audio.set_channels(1)
            
            # Resample if needed
            if audio.frame_rate != self.target_sample_rate:
                audio = audio.set_frame_rate(self.target_sample_rate)
            
            # Normalize audio levels
            if normalize:
                audio = self._normalize_audio(audio)
            
            # Remove noise
            if remove_noise:
                audio = await self._remove_noise(audio)
            
            # Enhance speech
            if enhance_speech:
                audio = await self._enhance_speech(audio)
            
            # Remove silence
            if remove_silence:
                audio = self._remove_silence(audio)
            
            # Apply dynamic range compression
            audio = compress_dynamic_range(audio)
            
            # Export processed audio
            audio.export(output_path, format=convert_format or 'wav')
            
            logger.info(f"Audio processed successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Audio processing failed: {e}")
            raise
    
    def _normalize_audio(self, audio: AudioSegment) -> AudioSegment:
        """Normalize audio levels"""
        return normalize(audio)
    
    async def _remove_noise(self, audio: AudioSegment) -> AudioSegment:
        """Remove background noise from audio"""
        
        try:
            # Convert to numpy array
            samples = np.array(audio.get_array_of_samples())
            
            # Apply noise reduction
            reduced_noise = nr.reduce_noise(
                y=samples.astype(np.float32),
                sr=audio.frame_rate,
                stationary=True,
                prop_decrease=self.config.get('noise_reduction_amount', 0.8)
            )
            
            # Convert back to AudioSegment
            reduced_audio = AudioSegment(
                reduced_noise.tobytes(),
                frame_rate=audio.frame_rate,
                sample_width=audio.sample_width,
                channels=audio.channels
            )
            
            return reduced_audio
            
        except Exception as e:
            logger.warning(f"Noise reduction failed: {e}")
            return audio
    
    async def _enhance_speech(self, audio: AudioSegment) -> AudioSegment:
        """Enhance speech clarity"""
        
        try:
            # Convert to numpy array
            samples = np.array(audio.get_array_of_samples()).astype(np.float32)
            samples = samples / np.max(np.abs(samples))  # Normalize to [-1, 1]
            
            # Apply high-pass filter to remove low-frequency noise
            nyquist = audio.frame_rate / 2
            cutoff = 80  # Hz
            normal_cutoff = cutoff / nyquist
            b, a = signal.butter(5, normal_cutoff, btype='high', analog=False)
            filtered = signal.filtfilt(b, a, samples)
            
            # Apply spectral subtraction for speech enhancement
            enhanced = self._spectral_subtraction(filtered, audio.frame_rate)
            
            # Convert back to AudioSegment
            enhanced_int = (enhanced * 32767).astype(np.int16)
            enhanced_audio = AudioSegment(
                enhanced_int.tobytes(),
                frame_rate=audio.frame_rate,
                sample_width=2,
                channels=audio.channels
            )
            
            return enhanced_audio
            
        except Exception as e:
            logger.warning(f"Speech enhancement failed: {e}")
            return audio
    
    def _spectral_subtraction(
        self,
        signal: np.ndarray,
        sample_rate: int,
        noise_factor: float = 0.1
    ) -> np.ndarray:
        """Apply spectral subtraction for noise reduction"""
        
        # Compute STFT
        f, t, Zxx = scipy.signal.stft(signal, fs=sample_rate, nperseg=256)
        
        # Estimate noise spectrum (using first 10% of signal)
        noise_frames = int(Zxx.shape[1] * noise_factor)
        noise_spectrum = np.mean(np.abs(Zxx[:, :noise_frames]), axis=1, keepdims=True)
        
        # Subtract noise spectrum
        enhanced_spectrum = np.abs(Zxx) - noise_spectrum
        enhanced_spectrum = np.maximum(enhanced_spectrum, 0)
        
        # Preserve phase
        enhanced_complex = enhanced_spectrum * np.exp(1j * np.angle(Zxx))
        
        # Inverse STFT
        _, enhanced_signal = scipy.signal.istft(enhanced_complex, fs=sample_rate, nperseg=256)
        
        return enhanced_signal.real
    
    def _remove_silence(
        self,
        audio: AudioSegment,
        min_silence_len: int = 1000,
        silence_thresh: int = -40
    ) -> AudioSegment:
        """Remove silence from audio"""
        
        nonsilent_chunks = detect_nonsilent(
            audio,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh
        )
        
        if not nonsilent_chunks:
            return audio
        
        # Concatenate non-silent chunks
        concatenated = AudioSegment.empty()
        for start, end in nonsilent_chunks:
            concatenated += audio[start:end]
        
        return concatenated
    
    def extract_features(
        self,
        audio_path: str,
        feature_type: str = 'mfcc'
    ) -> np.ndarray:
        """Extract audio features for analysis"""
        
        # Load audio
        y, sr = librosa.load(audio_path, sr=self.target_sample_rate)
        
        if feature_type == 'mfcc':
            # Extract MFCC features
            features = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        elif feature_type == 'melspectrogram':
            # Extract mel-spectrogram
            features = librosa.feature.melspectrogram(y=y, sr=sr)
        elif feature_type == 'chroma':
            # Extract chroma features
            features = librosa.feature.chroma_stft(y=y, sr=sr)
        elif feature_type == 'spectral_centroid':
            # Extract spectral centroid
            features = librosa.feature.spectral_centroid(y=y, sr=sr)
        else:
            raise ValueError(f"Unsupported feature type: {feature_type}")
        
        return features
    
    def split_audio(
        self,
        audio_path: str,
        chunk_duration: int = 30000  # milliseconds
    ) -> list:
        """Split audio into chunks"""
        
        audio = AudioSegment.from_file(audio_path)
        chunks = []
        
        for i in range(0, len(audio), chunk_duration):
            chunk = audio[i:i + chunk_duration]
            chunks.append(chunk)
        
        return chunks
    
    def convert_format(
        self,
        input_path: str,
        output_format: str,
        output_path: Optional[str] = None
    ) -> str:
        """Convert audio format"""
        
        if not output_path:
            base_path = os.path.splitext(input_path)[0]
            output_path = f"{base_path}.{output_format}"
        
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format=output_format)
        
        return output_path
    
    def get_audio_info(self, audio_path: str) -> Dict[str, Any]:
        """Get audio file information"""
        
        audio = AudioSegment.from_file(audio_path)
        
        return {
            'duration_seconds': len(audio) / 1000,
            'channels': audio.channels,
            'sample_rate': audio.frame_rate,
            'sample_width': audio.sample_width,
            'frame_count': audio.frame_count(),
            'max_amplitude': audio.max,
            'rms': audio.rms,
            'dBFS': audio.dBFS
        }
    
    def apply_effects(
        self,
        audio_path: str,
        effects: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """Apply various audio effects"""
        
        audio = AudioSegment.from_file(audio_path)
        
        # Apply fade in/out
        if effects.get('fade_in'):
            audio = audio.fade_in(effects['fade_in'])
        if effects.get('fade_out'):
            audio = audio.fade_out(effects['fade_out'])
        
        # Apply gain
        if effects.get('gain'):
            audio = audio + effects['gain']
        
        # Apply speed change
        if effects.get('speed'):
            audio = audio.speedup(playback_speed=effects['speed'])
        
        # Apply reverb (simplified)
        if effects.get('reverb'):
            audio = audio.overlay(audio - 10, position=50)
        
        if not output_path:
            output_path = audio_path.replace('.', '_processed.')
        
        audio.export(output_path, format='wav')
        return output_path
    
    def detect_speech_regions(
        self,
        audio_path: str,
        energy_threshold: float = 0.01
    ) -> list:
        """Detect speech regions in audio"""
        
        y, sr = librosa.load(audio_path, sr=self.target_sample_rate)
        
        # Calculate energy
        energy = librosa.feature.rms(y=y)[0]
        
        # Find speech regions
        speech_regions = []
        in_speech = False
        start_time = 0
        
        for i, e in enumerate(energy):
            time = i * 512 / sr  # Frame to time conversion
            
            if e > energy_threshold and not in_speech:
                start_time = time
                in_speech = True
            elif e <= energy_threshold and in_speech:
                speech_regions.append((start_time, time))
                in_speech = False
        
        # Add final region if still in speech
        if in_speech:
            speech_regions.append((start_time, len(y) / sr))
        
        return speech_regions