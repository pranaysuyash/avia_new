#!/usr/bin/env python3
"""
Task 83: Advanced Audio Preprocessing Pipeline - Fast Version
Optimized for performance with essential preprocessing capabilities
"""

import librosa
import numpy as np
import scipy.signal
from scipy.io import wavfile
import soundfile as sf
from typing import Tuple, List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
import logging
import tempfile
import os
from datetime import datetime
import json

logger = logging.getLogger(__name__)

@dataclass
class AudioPreprocessingConfig:
    """Configuration for audio preprocessing operations"""
    # Basic audio parameters
    target_sample_rate: int = 16000
    target_channels: int = 1
    
    # Noise reduction
    enable_noise_reduction: bool = True
    noise_reduction_strength: float = 0.7
    
    # Dynamic range and normalization
    enable_normalization: bool = True
    normalization_method: str = "peak"  # peak, rms
    
    # Filtering
    enable_high_pass_filter: bool = True
    high_pass_cutoff: float = 80.0
    enable_low_pass_filter: bool = True
    low_pass_cutoff: float = 8000.0
    
    # Silence handling
    remove_silence: bool = True
    silence_threshold: float = -40.0  # dB
    
    # Output format
    output_format: str = "wav"

@dataclass
class AudioQualityMetrics:
    """Simplified audio quality metrics"""
    snr: float = 0.0
    dynamic_range: float = 0.0
    energy: float = 0.0
    peak_level: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'snr': float(self.snr),
            'dynamic_range': float(self.dynamic_range),
            'energy': float(self.energy),
            'peak_level': float(self.peak_level)
        }

@dataclass
class AudioPreprocessingResult:
    """Result of audio preprocessing operations"""
    processed_audio: np.ndarray
    sample_rate: int
    original_audio: np.ndarray
    original_sample_rate: int
    operations_applied: List[str]
    quality_metrics: AudioQualityMetrics
    processing_time: float
    config_used: AudioPreprocessingConfig
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def save_audio(self, output_path: str):
        """Save processed audio to file"""
        sf.write(output_path, self.processed_audio, self.sample_rate)

class AudioPreprocessorFast:
    """Fast audio preprocessing system optimized for performance"""
    
    def __init__(self, config: Optional[AudioPreprocessingConfig] = None):
        self.config = config or AudioPreprocessingConfig()
        
    def preprocess_audio(self, audio_input: Union[str, np.ndarray, Tuple[np.ndarray, int]],
                        config: Optional[AudioPreprocessingConfig] = None) -> AudioPreprocessingResult:
        """Fast audio preprocessing pipeline"""
        start_time = datetime.now()
        config = config or self.config
        operations_applied = []
        
        try:
            # Load audio
            original_audio, original_sr = self._load_audio(audio_input)
            processed_audio = original_audio.copy()
            current_sr = original_sr
            
            # 1. Sample rate conversion
            if current_sr != config.target_sample_rate:
                processed_audio = librosa.resample(processed_audio, 
                                                 orig_sr=current_sr,
                                                 target_sr=config.target_sample_rate)
                current_sr = config.target_sample_rate
                operations_applied.append("resample")
            
            # 2. Convert to mono
            if len(processed_audio.shape) > 1:
                processed_audio = np.mean(processed_audio, axis=0)
                operations_applied.append("to_mono")
            
            # 3. Remove DC offset
            processed_audio = processed_audio - np.mean(processed_audio)
            operations_applied.append("dc_removal")
            
            # 4. Simple noise reduction (high-pass filter)
            if config.enable_noise_reduction:
                processed_audio = self._simple_noise_reduction(processed_audio, current_sr)
                operations_applied.append("noise_reduction")
            
            # 5. Apply filters
            if config.enable_high_pass_filter:
                processed_audio = self._apply_high_pass_filter(processed_audio, current_sr, 
                                                             config.high_pass_cutoff)
                operations_applied.append("high_pass_filter")
            
            if config.enable_low_pass_filter:
                processed_audio = self._apply_low_pass_filter(processed_audio, current_sr,
                                                            config.low_pass_cutoff)
                operations_applied.append("low_pass_filter")
            
            # 6. Simple silence removal
            if config.remove_silence:
                processed_audio = self._remove_silence(processed_audio, current_sr, config)
                operations_applied.append("silence_removal")
            
            # 7. Normalization
            if config.enable_normalization:
                processed_audio = self._normalize_audio(processed_audio, config)
                operations_applied.append("normalize")
            
            # 8. Quick quality assessment
            quality_metrics = self._assess_audio_quality_fast(processed_audio, current_sr)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return AudioPreprocessingResult(
                processed_audio=processed_audio,
                sample_rate=current_sr,
                original_audio=original_audio,
                original_sample_rate=original_sr,
                operations_applied=operations_applied,
                quality_metrics=quality_metrics,
                processing_time=processing_time,
                config_used=config,
                metadata={
                    'duration_original': len(original_audio) / original_sr,
                    'duration_processed': len(processed_audio) / current_sr
                }
            )
            
        except Exception as e:
            logger.error(f"Audio preprocessing failed: {e}")
            raise
    
    def _load_audio(self, audio_input: Union[str, np.ndarray, Tuple[np.ndarray, int]]) -> Tuple[np.ndarray, int]:
        """Load audio from various input types"""
        if isinstance(audio_input, str):
            if not os.path.exists(audio_input):
                raise FileNotFoundError(f"Audio file not found: {audio_input}")
            audio, sr = librosa.load(audio_input, sr=None, mono=False)
            return audio, sr
        elif isinstance(audio_input, tuple) and len(audio_input) == 2:
            return audio_input[0], audio_input[1]
        elif isinstance(audio_input, np.ndarray):
            return audio_input, 22050  # Default sample rate
        else:
            raise ValueError("Unsupported audio input type")
    
    def _assess_audio_quality_fast(self, audio: np.ndarray, sr: int) -> AudioQualityMetrics:
        """Fast audio quality assessment without expensive operations"""
        # Ensure audio is 1D
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=0)
        
        # Simple SNR estimation
        # Split into segments and estimate noise from quietest segment
        segment_size = min(len(audio) // 10, sr // 2)  # 0.5s segments
        if segment_size > 0:
            segments = [audio[i:i+segment_size] for i in range(0, len(audio) - segment_size, segment_size)]
            segment_energies = [np.mean(seg**2) for seg in segments]
            
            if len(segment_energies) > 1:
                noise_energy = np.min(segment_energies)
                signal_energy = np.mean(segment_energies)
                snr = 10 * np.log10(max(signal_energy / max(noise_energy, 1e-10), 1.0))
            else:
                snr = 20.0  # Default reasonable SNR
        else:
            snr = 20.0
        
        # Dynamic range
        peak_level = np.max(np.abs(audio))
        rms_level = np.sqrt(np.mean(audio**2))
        dynamic_range = 20 * np.log10(max(peak_level / max(rms_level, 1e-10), 1.0))
        
        # Energy
        energy = rms_level
        
        return AudioQualityMetrics(
            snr=snr,
            dynamic_range=dynamic_range,
            energy=energy,
            peak_level=peak_level
        )
    
    def _simple_noise_reduction(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Simple noise reduction using spectral subtraction"""
        # Simple spectral subtraction
        stft = librosa.stft(audio, n_fft=2048, hop_length=512)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Estimate noise from first 0.5 seconds
        noise_frames = min(int(0.5 * sr / 512), magnitude.shape[1] // 4)
        noise_spectrum = np.mean(magnitude[:, :noise_frames], axis=1, keepdims=True)
        
        # Apply spectral subtraction
        alpha = 2.0  # Over-subtraction factor
        beta = 0.1   # Spectral floor
        
        enhanced_magnitude = magnitude - alpha * noise_spectrum
        enhanced_magnitude = np.maximum(enhanced_magnitude, beta * magnitude)
        
        # Reconstruct
        enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
        return librosa.istft(enhanced_stft, hop_length=512)
    
    def _apply_high_pass_filter(self, audio: np.ndarray, sr: int, cutoff: float) -> np.ndarray:
        """Apply high-pass filter"""
        nyquist = sr / 2
        normalized_cutoff = cutoff / nyquist
        
        if normalized_cutoff >= 0.95:
            return audio
        
        b, a = scipy.signal.butter(2, normalized_cutoff, btype='high')  # Reduced order for speed
        return scipy.signal.filtfilt(b, a, audio)
    
    def _apply_low_pass_filter(self, audio: np.ndarray, sr: int, cutoff: float) -> np.ndarray:
        """Apply low-pass filter"""
        nyquist = sr / 2
        normalized_cutoff = cutoff / nyquist
        
        if normalized_cutoff >= 0.95:
            return audio
        
        b, a = scipy.signal.butter(2, normalized_cutoff, btype='low')  # Reduced order for speed
        return scipy.signal.filtfilt(b, a, audio)
    
    def _remove_silence(self, audio: np.ndarray, sr: int, config: AudioPreprocessingConfig) -> np.ndarray:
        """Simple silence removal"""
        # Calculate frame energy
        frame_length = int(0.025 * sr)  # 25ms frames
        hop_length = int(0.010 * sr)    # 10ms hop
        
        # Frame the audio
        frames = librosa.util.frame(audio, frame_length=frame_length, hop_length=hop_length)
        energy = np.mean(frames**2, axis=0)
        
        # Simple threshold-based VAD
        energy_db = 10 * np.log10(energy + 1e-10)
        threshold = config.silence_threshold
        voice_frames = energy_db > threshold
        
        # Convert frame indices to sample indices
        voice_samples = np.zeros(len(audio), dtype=bool)
        for i, is_voice in enumerate(voice_frames):
            start_sample = i * hop_length
            end_sample = min(start_sample + frame_length, len(audio))
            if is_voice:
                voice_samples[start_sample:end_sample] = True
        
        # Extract voice regions with small padding
        padding_samples = int(0.1 * sr)  # 0.1s padding
        
        # Find voice regions
        voice_regions = []
        in_voice = False
        start_idx = 0
        
        for i, is_voice in enumerate(voice_samples):
            if is_voice and not in_voice:
                start_idx = max(0, i - padding_samples)
                in_voice = True
            elif not is_voice and in_voice:
                end_idx = min(len(audio), i + padding_samples)
                voice_regions.append((start_idx, end_idx))
                in_voice = False
        
        # Handle case where audio ends in voice
        if in_voice:
            voice_regions.append((start_idx, len(audio)))
        
        # Concatenate voice regions
        if voice_regions:
            voice_segments = [audio[start:end] for start, end in voice_regions]
            return np.concatenate(voice_segments)
        else:
            return audio  # Return original if no voice detected
    
    def _normalize_audio(self, audio: np.ndarray, config: AudioPreprocessingConfig) -> np.ndarray:
        """Normalize audio"""
        if config.normalization_method == "peak":
            max_val = np.max(np.abs(audio))
            if max_val > 0:
                return audio / max_val * 0.95  # Leave headroom
        elif config.normalization_method == "rms":
            rms = np.sqrt(np.mean(audio**2))
            if rms > 0:
                target_rms = 0.1
                return audio * (target_rms / rms)
        
        return audio

# Example usage
if __name__ == "__main__":
    # Test the fast preprocessor
    config = AudioPreprocessingConfig(
        enable_noise_reduction=True,
        enable_normalization=True,
        remove_silence=True
    )
    
    preprocessor = AudioPreprocessorFast(config)
    
    print("Fast Audio Preprocessing System - Task 83 Implementation")
    print("Optimized for performance with essential features:")
    print("- Fast sample rate conversion")
    print("- Simple but effective noise reduction")
    print("- Efficient silence removal")
    print("- Quick quality assessment")
    print("- High-pass and low-pass filtering")
    print("- Peak and RMS normalization")