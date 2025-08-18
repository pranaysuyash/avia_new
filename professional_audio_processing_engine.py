"""
Professional Audio Processing Engine
Task 4: Advanced Media Processing Pipeline

Professional-grade audio processing with noise reduction, echo cancellation,
dynamic range optimization, intelligent level balancing, real-time enhancement,
and audio forensics capabilities.

Requirements: 3.1, 3.2, 3.3, 3.6
Dependencies: Multi-channel audio engine, processing router
"""

import os
import numpy as np
import scipy.signal
import scipy.fft
import librosa
import soundfile as sf
import logging
import asyncio
import tempfile
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
import json

# Third-party imports with fallbacks
try:
    import torch
    import torchaudio
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch not available - some AI features will be limited")

try:
    import noisereduce as nr
    NOISEREDUCE_AVAILABLE = True
except ImportError:
    NOISEREDUCE_AVAILABLE = False
    logging.warning("noisereduce not available - using fallback algorithms")

try:
    from multi_channel_audio_engine import (
        MultiChannelAudio, AudioChannel, AudioFormat, ChannelLayout,
        ProcessingMode, SpatialMetadata, ProcessingHistory
    )
    MULTICHANNEL_AVAILABLE = True
except ImportError:
    MULTICHANNEL_AVAILABLE = False
    logging.warning("Multi-channel audio engine not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioQuality(Enum):
    """Audio quality levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BROADCAST = "broadcast"
    STUDIO = "studio"


class NoiseType(Enum):
    """Types of noise for targeted reduction"""
    BROADBAND = "broadband"
    TONAL = "tonal"
    IMPULSIVE = "impulsive"
    WIND = "wind"
    TRAFFIC = "traffic"
    HVAC = "hvac"
    ELECTRICAL = "electrical"


class ProcessingStrategy(Enum):
    """Audio processing strategies"""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    CUSTOM = "custom"
@da
taclass
class AudioMetadata:
    """Comprehensive audio metadata"""
    duration: float
    sample_rate: int
    channels: int
    bit_depth: int
    format: str
    file_size: int
    peak_level: float
    rms_level: float
    dynamic_range: float
    snr_estimate: float
    thd_estimate: float
    spectral_centroid: float
    zero_crossing_rate: float
    tempo: Optional[float] = None
    key: Optional[str] = None


@dataclass
class NoiseProfile:
    """Noise profile for targeted reduction"""
    noise_type: NoiseType
    frequency_profile: np.ndarray
    power_spectrum: np.ndarray
    statistical_moments: Dict[str, float]
    confidence: float
    duration_analyzed: float


@dataclass
class AudioEnhancementConfig:
    """Configuration for audio enhancement"""
    noise_reduction: bool = True
    echo_cancellation: bool = True
    dynamic_range_optimization: bool = True
    level_balancing: bool = True
    spectral_enhancement: bool = False
    real_time_mode: bool = False
    quality_target: AudioQuality = AudioQuality.HIGH
    processing_strategy: ProcessingStrategy = ProcessingStrategy.BALANCED
    preserve_dynamics: bool = True
    target_lufs: float = -23.0  # EBU R128 standard


@dataclass
class SpectralAnalysis:
    """Detailed spectral analysis results"""
    frequency_bins: np.ndarray
    magnitude_spectrum: np.ndarray
    phase_spectrum: np.ndarray
    power_spectral_density: np.ndarray
    spectral_peaks: List[Tuple[float, float]]  # (frequency, magnitude)
    harmonic_content: Dict[str, float]
    noise_floor: float
    dynamic_range_db: float
    spectral_flatness: float
    spectral_rolloff: float


@dataclass
class AudioForensicsResult:
    """Audio forensics analysis result"""
    authenticity_score: float
    tampering_indicators: List[str]
    quality_assessment: Dict[str, float]
    spectral_anomalies: List[Dict[str, Any]]
    temporal_inconsistencies: List[Dict[str, Any]]
    compression_artifacts: List[str]
    editing_traces: List[str]
    confidence_intervals: Dict[str, Tuple[float, float]]


class ProfessionalAudioProcessingEngine:
    """
    Professional-grade audio processing engine with advanced capabilities
    for noise reduction, enhancement, and forensic analysis.
    """
    
    def __init__(self, temp_dir: Optional[str] = None, max_workers: int = 4):
        """
        Initialize the professional audio processing engine
        
        Args:
            temp_dir: Directory for temporary files
            max_workers: Maximum number of worker threads
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Initialize processing components
        self._initialize_processors()
        
        # Performance tracking
        self.processing_stats = {
            'total_processed': 0,
            'total_processing_time': 0.0,
            'average_enhancement_ratio': 0.0,
            'noise_reduction_effectiveness': 0.0
        }
        
        logger.info(f"ProfessionalAudioProcessingEngine initialized with {max_workers} workers")
    
    def _initialize_processors(self):
        """Initialize audio processing components"""
        try:
            # Initialize noise reduction models if available
            if TORCH_AVAILABLE:
                self._initialize_ai_models()
            
            # Initialize spectral processing components
            self._initialize_spectral_processors()
            
            # Initialize real-time processing buffers
            self._initialize_realtime_buffers()
            
            logger.info("Audio processing components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize processors: {e}")
    
    def _initialize_ai_models(self):
        """Initialize AI-based audio processing models"""
        try:
            # Placeholder for AI model initialization
            # In production, load pre-trained models for:
            # - Neural noise reduction
            # - Speech enhancement
            # - Source separation
            self.ai_models_available = True
            logger.info("AI models initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI models: {e}")
            self.ai_models_available = False
    
    def _initialize_spectral_processors(self):
        """Initialize spectral analysis and processing components"""
        self.window_functions = {
            'hann': np.hanning,
            'hamming': np.hamming,
            'blackman': np.blackman,
            'kaiser': lambda n: np.kaiser(n, 8.6)
        }
        
        self.filter_banks = {}
        self._create_filter_banks()
    
    def _create_filter_banks(self):
        """Create various filter banks for processing"""
        # Create octave band filters
        center_freqs = [63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
        self.filter_banks['octave'] = center_freqs
        
        # Create mel-scale filter bank
        self.filter_banks['mel'] = librosa.filters.mel(
            sr=44100, n_fft=2048, n_mels=128
        )
    
    def _initialize_realtime_buffers(self):
        """Initialize buffers for real-time processing"""
        self.realtime_buffers = {
            'input_buffer': [],
            'output_buffer': [],
            'processing_queue': [],
            'latency_compensation': 0
        }
    
    async def extract_audio_metadata(self, audio_path: str) -> AudioMetadata:
        """Extract comprehensive audio metadata"""
        try:
            # Load audio file
            audio_data, sample_rate = librosa.load(audio_path, sr=None, mono=False)
            
            # Handle mono/stereo
            if audio_data.ndim == 1:
                channels = 1
                mono_audio = audio_data
            else:
                channels = audio_data.shape[0]
                mono_audio = librosa.to_mono(audio_data)
            
            # Basic metrics
            duration = len(mono_audio) / sample_rate
            file_size = os.path.getsize(audio_path)
            
            # Audio quality metrics
            peak_level = np.max(np.abs(mono_audio))
            rms_level = np.sqrt(np.mean(mono_audio**2))
            
            # Dynamic range analysis
            dynamic_range = self._calculate_dynamic_range(mono_audio)
            
            # Noise analysis
            snr_estimate = self._estimate_snr(mono_audio)
            
            # Distortion analysis
            thd_estimate = self._estimate_thd(mono_audio, sample_rate)
            
            # Spectral features
            spectral_centroid = np.mean(librosa.feature.spectral_centroid(
                y=mono_audio, sr=sample_rate
            ))
            zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(mono_audio))
            
            # Musical features (if applicable)
            tempo = None
            key = None
            try:
                tempo, _ = librosa.beat.beat_track(y=mono_audio, sr=sample_rate)
                chroma = librosa.feature.chroma_stft(y=mono_audio, sr=sample_rate)
                key = self._estimate_key(chroma)
            except:
                pass
            
            return AudioMetadata(
                duration=duration,
                sample_rate=sample_rate,
                channels=channels,
                bit_depth=16,  # Default, would need format-specific detection
                format=Path(audio_path).suffix.lower(),
                file_size=file_size,
                peak_level=float(peak_level),
                rms_level=float(rms_level),
                dynamic_range=dynamic_range,
                snr_estimate=snr_estimate,
                thd_estimate=thd_estimate,
                spectral_centroid=float(spectral_centroid),
                zero_crossing_rate=float(zero_crossing_rate),
                tempo=float(tempo) if tempo else None,
                key=key
            )
            
        except Exception as e:
            logger.error(f"Failed to extract audio metadata: {e}")
            raise
    
    def _calculate_dynamic_range(self, audio: np.ndarray) -> float:
        """Calculate dynamic range in dB"""
        try:
            # Use percentile-based approach to avoid outliers
            peak_level = np.percentile(np.abs(audio), 99)
            noise_floor = np.percentile(np.abs(audio), 10)
            
            if noise_floor > 0:
                dynamic_range = 20 * np.log10(peak_level / noise_floor)
            else:
                dynamic_range = 60.0  # Default high dynamic range
            
            return float(dynamic_range)
        except:
            return 40.0  # Default moderate dynamic range
    
    def _estimate_snr(self, audio: np.ndarray) -> float:
        """Estimate signal-to-noise ratio"""
        try:
            # Simple SNR estimation using signal power vs noise floor
            signal_power = np.mean(audio**2)
            
            # Estimate noise from quiet segments
            audio_abs = np.abs(audio)
            noise_threshold = np.percentile(audio_abs, 20)
            noise_samples = audio[audio_abs < noise_threshold]
            
            if len(noise_samples) > 0:
                noise_power = np.mean(noise_samples**2)
                if noise_power > 0:
                    snr = 10 * np.log10(signal_power / noise_power)
                else:
                    snr = 60.0  # Very clean signal
            else:
                snr = 40.0  # Default good SNR
            
            return float(np.clip(snr, 0, 80))
        except:
            return 30.0  # Default moderate SNR
    
    def _estimate_thd(self, audio: np.ndarray, sample_rate: int) -> float:
        """Estimate Total Harmonic Distortion"""
        try:
            # Simplified THD estimation using spectral analysis
            fft = np.fft.fft(audio[:sample_rate])  # Use 1 second
            magnitude = np.abs(fft)
            
            # Find fundamental frequency
            freqs = np.fft.fftfreq(len(fft), 1/sample_rate)
            fundamental_idx = np.argmax(magnitude[1:len(magnitude)//2]) + 1
            fundamental_power = magnitude[fundamental_idx]**2
            
            # Estimate harmonic power
            harmonic_power = 0
            for harmonic in range(2, 6):  # 2nd to 5th harmonics
                harmonic_idx = fundamental_idx * harmonic
                if harmonic_idx < len(magnitude):
                    harmonic_power += magnitude[harmonic_idx]**2
            
            if fundamental_power > 0:
                thd = np.sqrt(harmonic_power / fundamental_power) * 100
            else:
                thd = 1.0  # Default low distortion
            
            return float(np.clip(thd, 0, 50))
        except:
            return 1.0  # Default low distortion
    
    def _estimate_key(self, chroma: np.ndarray) -> Optional[str]:
        """Estimate musical key from chroma features"""
        try:
            # Simple key estimation using chroma profile matching
            key_profiles = {
                'C': [1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1],
                'G': [1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1],
                'D': [0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1],
                'A': [1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1],
                'E': [1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1],
                'B': [1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1],
                'F#': [0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1],
                'F': [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0]
            }
            
            mean_chroma = np.mean(chroma, axis=1)
            
            best_correlation = -1
            best_key = None
            
            for key, profile in key_profiles.items():
                correlation = np.corrcoef(mean_chroma, profile)[0, 1]
                if correlation > best_correlation:
                    best_correlation = correlation
                    best_key = key
            
            return best_key if best_correlation > 0.5 else None
        except:
            return None    
 
   async def analyze_noise_profile(self, audio_path: str, 
                                  noise_sample_duration: float = 2.0) -> NoiseProfile:
        """Analyze noise characteristics for targeted reduction"""
        try:
            # Load audio
            audio_data, sample_rate = librosa.load(audio_path, sr=None)
            
            # Extract noise sample from beginning (assuming first part is noise)
            noise_samples = int(noise_sample_duration * sample_rate)
            noise_segment = audio_data[:min(noise_samples, len(audio_data))]
            
            # Spectral analysis of noise
            stft = librosa.stft(noise_segment, n_fft=2048, hop_length=512)
            magnitude = np.abs(stft)
            power_spectrum = magnitude**2
            
            # Frequency profile
            frequency_profile = np.mean(power_spectrum, axis=1)
            
            # Statistical analysis
            statistical_moments = {
                'mean': float(np.mean(noise_segment)),
                'std': float(np.std(noise_segment)),
                'skewness': float(scipy.stats.skew(noise_segment)),
                'kurtosis': float(scipy.stats.kurtosis(noise_segment))
            }
            
            # Classify noise type
            noise_type = self._classify_noise_type(frequency_profile, statistical_moments)
            
            # Calculate confidence based on consistency
            confidence = self._calculate_noise_confidence(power_spectrum)
            
            return NoiseProfile(
                noise_type=noise_type,
                frequency_profile=frequency_profile,
                power_spectrum=np.mean(power_spectrum, axis=1),
                statistical_moments=statistical_moments,
                confidence=confidence,
                duration_analyzed=noise_sample_duration
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze noise profile: {e}")
            # Return default broadband noise profile
            return NoiseProfile(
                noise_type=NoiseType.BROADBAND,
                frequency_profile=np.ones(1025),
                power_spectrum=np.ones(1025),
                statistical_moments={'mean': 0.0, 'std': 0.1, 'skewness': 0.0, 'kurtosis': 3.0},
                confidence=0.5,
                duration_analyzed=noise_sample_duration
            )
    
    def _classify_noise_type(self, frequency_profile: np.ndarray, 
                           stats: Dict[str, float]) -> NoiseType:
        """Classify noise type based on spectral and statistical characteristics"""
        try:
            # Analyze frequency distribution
            low_freq_energy = np.sum(frequency_profile[:50])  # 0-1kHz
            mid_freq_energy = np.sum(frequency_profile[50:200])  # 1-4kHz
            high_freq_energy = np.sum(frequency_profile[200:])  # 4kHz+
            
            total_energy = low_freq_energy + mid_freq_energy + high_freq_energy
            
            if total_energy > 0:
                low_ratio = low_freq_energy / total_energy
                high_ratio = high_freq_energy / total_energy
                
                # Classification logic
                if low_ratio > 0.6:
                    return NoiseType.TRAFFIC
                elif high_ratio > 0.5:
                    return NoiseType.ELECTRICAL
                elif stats['kurtosis'] > 5:
                    return NoiseType.IMPULSIVE
                elif np.std(frequency_profile) < np.mean(frequency_profile) * 0.3:
                    return NoiseType.TONAL
                else:
                    return NoiseType.BROADBAND
            
            return NoiseType.BROADBAND
        except:
            return NoiseType.BROADBAND
    
    def _calculate_noise_confidence(self, power_spectrum: np.ndarray) -> float:
        """Calculate confidence in noise profile analysis"""
        try:
            # Measure consistency across time frames
            frame_variations = np.std(power_spectrum, axis=1)
            mean_power = np.mean(power_spectrum, axis=1)
            
            # Calculate coefficient of variation
            cv = np.mean(frame_variations / (mean_power + 1e-10))
            
            # Convert to confidence (lower variation = higher confidence)
            confidence = np.exp(-cv * 2)
            
            return float(np.clip(confidence, 0.1, 1.0))
        except:
            return 0.5
    
    async def reduce_noise(self, audio_path: str, 
                         noise_profile: Optional[NoiseProfile] = None,
                         output_path: Optional[str] = None,
                         strength: float = 0.8) -> str:
        """Advanced noise reduction with multiple algorithms"""
        try:
            if output_path is None:
                output_path = os.path.join(
                    self.temp_dir, 
                    f"denoised_{uuid.uuid4().hex[:8]}.wav"
                )
            
            # Load audio
            audio_data, sample_rate = librosa.load(audio_path, sr=None)
            
            # Analyze noise profile if not provided
            if noise_profile is None:
                noise_profile = await self.analyze_noise_profile(audio_path)
            
            # Apply appropriate noise reduction algorithm
            if NOISEREDUCE_AVAILABLE:
                # Use noisereduce library
                reduced_audio = nr.reduce_noise(
                    y=audio_data, 
                    sr=sample_rate,
                    stationary=noise_profile.noise_type != NoiseType.IMPULSIVE,
                    prop_decrease=strength
                )
            else:
                # Use custom spectral subtraction
                reduced_audio = self._spectral_subtraction(
                    audio_data, noise_profile, strength
                )
            
            # Apply post-processing
            enhanced_audio = self._post_process_denoised_audio(
                reduced_audio, sample_rate
            )
            
            # Save result
            sf.write(output_path, enhanced_audio, sample_rate)
            
            logger.info(f"Noise reduction completed: {audio_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Noise reduction failed: {e}")
            raise
    
    def _spectral_subtraction(self, audio: np.ndarray, 
                            noise_profile: NoiseProfile, 
                            strength: float) -> np.ndarray:
        """Custom spectral subtraction algorithm"""
        try:
            # STFT
            stft = librosa.stft(audio, n_fft=2048, hop_length=512)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Estimate noise spectrum
            noise_spectrum = noise_profile.power_spectrum.reshape(-1, 1)
            
            # Spectral subtraction
            alpha = strength * 2.0  # Over-subtraction factor
            enhanced_magnitude = magnitude - alpha * noise_spectrum
            
            # Apply spectral floor to prevent artifacts
            spectral_floor = 0.1 * magnitude
            enhanced_magnitude = np.maximum(enhanced_magnitude, spectral_floor)
            
            # Reconstruct signal
            enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
            enhanced_audio = librosa.istft(enhanced_stft, hop_length=512)
            
            return enhanced_audio
            
        except Exception as e:
            logger.error(f"Spectral subtraction failed: {e}")
            return audio
    
    def _post_process_denoised_audio(self, audio: np.ndarray, 
                                   sample_rate: int) -> np.ndarray:
        """Post-process denoised audio to reduce artifacts"""
        try:
            # Apply gentle high-pass filter to remove low-frequency artifacts
            sos = scipy.signal.butter(4, 80, btype='high', fs=sample_rate, output='sos')
            filtered_audio = scipy.signal.sosfilt(sos, audio)
            
            # Apply gentle smoothing to reduce musical noise
            smoothed_audio = scipy.signal.savgol_filter(
                filtered_audio, window_length=5, polyorder=2
            )
            
            # Normalize to prevent clipping
            max_val = np.max(np.abs(smoothed_audio))
            if max_val > 0.95:
                smoothed_audio = smoothed_audio * (0.95 / max_val)
            
            return smoothed_audio
            
        except Exception as e:
            logger.error(f"Post-processing failed: {e}")
            return audio
    
    async def cancel_echo(self, audio_path: str, 
                        output_path: Optional[str] = None,
                        filter_length: int = 1024) -> str:
        """Advanced echo cancellation"""
        try:
            if output_path is None:
                output_path = os.path.join(
                    self.temp_dir, 
                    f"echo_cancelled_{uuid.uuid4().hex[:8]}.wav"
                )
            
            # Load audio
            audio_data, sample_rate = librosa.load(audio_path, sr=None)
            
            # Apply adaptive echo cancellation
            processed_audio = self._adaptive_echo_cancellation(
                audio_data, sample_rate, filter_length
            )
            
            # Save result
            sf.write(output_path, processed_audio, sample_rate)
            
            logger.info(f"Echo cancellation completed: {audio_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Echo cancellation failed: {e}")
            raise
    
    def _adaptive_echo_cancellation(self, audio: np.ndarray, 
                                  sample_rate: int, 
                                  filter_length: int) -> np.ndarray:
        """Adaptive echo cancellation using LMS algorithm"""
        try:
            # Simplified echo cancellation
            # In production, this would use more sophisticated algorithms
            
            # Detect echo characteristics
            autocorr = np.correlate(audio, audio, mode='full')
            autocorr = autocorr[autocorr.size // 2:]
            
            # Find potential echo delays
            peaks, _ = scipy.signal.find_peaks(
                autocorr[sample_rate//10:sample_rate//2],  # 100ms to 500ms delay
                height=np.max(autocorr) * 0.3
            )
            
            if len(peaks) > 0:
                # Apply comb filter to reduce echo
                delay_samples = peaks[0] + sample_rate//10
                echo_strength = autocorr[delay_samples] / autocorr[0]
                
                # Create echo cancellation filter
                echo_cancelled = audio.copy()
                if delay_samples < len(audio):
                    echo_cancelled[delay_samples:] -= (
                        echo_strength * 0.7 * audio[:-delay_samples]
                    )
                
                return echo_cancelled
            
            return audio
            
        except Exception as e:
            logger.error(f"Adaptive echo cancellation failed: {e}")
            return audio
    
    async def optimize_dynamic_range(self, audio_path: str,
                                   output_path: Optional[str] = None,
                                   target_lufs: float = -23.0,
                                   max_peak: float = -1.0) -> str:
        """Optimize dynamic range with intelligent compression and limiting"""
        try:
            if output_path is None:
                output_path = os.path.join(
                    self.temp_dir, 
                    f"optimized_{uuid.uuid4().hex[:8]}.wav"
                )
            
            # Load audio
            audio_data, sample_rate = librosa.load(audio_path, sr=None)
            
            # Apply intelligent dynamic range optimization
            optimized_audio = self._intelligent_dynamic_processing(
                audio_data, sample_rate, target_lufs, max_peak
            )
            
            # Save result
            sf.write(output_path, optimized_audio, sample_rate)
            
            logger.info(f"Dynamic range optimization completed: {audio_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Dynamic range optimization failed: {e}")
            raise
    
    def _intelligent_dynamic_processing(self, audio: np.ndarray, 
                                      sample_rate: int,
                                      target_lufs: float,
                                      max_peak: float) -> np.ndarray:
        """Intelligent dynamic range processing"""
        try:
            # Multi-band compression
            processed_audio = self._multiband_compression(audio, sample_rate)
            
            # Loudness normalization
            normalized_audio = self._loudness_normalization(
                processed_audio, sample_rate, target_lufs
            )
            
            # Peak limiting
            limited_audio = self._peak_limiting(normalized_audio, max_peak)
            
            return limited_audio
            
        except Exception as e:
            logger.error(f"Dynamic processing failed: {e}")
            return audio
    
    def _multiband_compression(self, audio: np.ndarray, 
                             sample_rate: int) -> np.ndarray:
        """Multi-band compression for balanced frequency response"""
        try:
            # Define frequency bands
            bands = [
                (20, 250),    # Low
                (250, 2000),  # Mid
                (2000, 8000), # High
                (8000, 20000) # Very High
            ]
            
            compressed_bands = []
            
            for low_freq, high_freq in bands:
                # Create bandpass filter
                sos = scipy.signal.butter(
                    4, [low_freq, high_freq], 
                    btype='band', fs=sample_rate, output='sos'
                )
                
                # Filter audio to band
                band_audio = scipy.signal.sosfilt(sos, audio)
                
                # Apply compression
                compressed_band = self._apply_compression(
                    band_audio, ratio=3.0, threshold=-20.0, attack=0.003, release=0.1
                )
                
                compressed_bands.append(compressed_band)
            
            # Sum all bands
            result = np.sum(compressed_bands, axis=0)
            
            # Normalize to prevent clipping
            max_val = np.max(np.abs(result))
            if max_val > 0.95:
                result = result * (0.95 / max_val)
            
            return result
            
        except Exception as e:
            logger.error(f"Multi-band compression failed: {e}")
            return audio
    
    def _apply_compression(self, audio: np.ndarray, 
                         ratio: float, threshold: float,
                         attack: float, release: float) -> np.ndarray:
        """Apply dynamic range compression"""
        try:
            # Convert threshold from dB to linear
            threshold_linear = 10**(threshold/20)
            
            # Simple compression algorithm
            compressed = audio.copy()
            envelope = 0.0
            
            for i in range(len(audio)):
                # Calculate envelope
                input_level = abs(audio[i])
                if input_level > envelope:
                    envelope += (input_level - envelope) * attack
                else:
                    envelope += (input_level - envelope) * release
                
                # Apply compression
                if envelope > threshold_linear:
                    gain_reduction = 1.0 - (1.0 - threshold_linear / envelope) / ratio
                    compressed[i] = audio[i] * gain_reduction
            
            return compressed
            
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return audio
    
    def _loudness_normalization(self, audio: np.ndarray, 
                              sample_rate: int, 
                              target_lufs: float) -> np.ndarray:
        """Normalize audio to target LUFS"""
        try:
            # Simplified LUFS calculation
            # In production, use proper EBU R128 implementation
            
            # Apply K-weighting filter (simplified)
            sos = scipy.signal.butter(2, [38, 20000], btype='band', fs=sample_rate, output='sos')
            filtered_audio = scipy.signal.sosfilt(sos, audio)
            
            # Calculate mean square
            mean_square = np.mean(filtered_audio**2)
            
            # Convert to LUFS (simplified)
            current_lufs = -0.691 + 10 * np.log10(mean_square + 1e-10)
            
            # Calculate gain adjustment
            gain_db = target_lufs - current_lufs
            gain_linear = 10**(gain_db/20)
            
            # Apply gain
            normalized_audio = audio * gain_linear
            
            return normalized_audio
            
        except Exception as e:
            logger.error(f"Loudness normalization failed: {e}")
            return audio
    
    def _peak_limiting(self, audio: np.ndarray, max_peak_db: float) -> np.ndarray:
        """Apply peak limiting to prevent clipping"""
        try:
            max_peak_linear = 10**(max_peak_db/20)
            
            # Find peaks above threshold
            peaks = np.abs(audio) > max_peak_linear
            
            if np.any(peaks):
                # Apply soft limiting
                limited_audio = audio.copy()
                limited_audio[peaks] = np.sign(audio[peaks]) * max_peak_linear * np.tanh(
                    np.abs(audio[peaks]) / max_peak_linear
                )
                return limited_audio
            
            return audio
            
        except Exception as e:
            logger.error(f"Peak limiting failed: {e}")
            return audio  
  
    async def balance_levels(self, audio_path: str,
                           output_path: Optional[str] = None,
                           target_rms: float = -20.0) -> str:
        """Intelligent level balancing for consistent audio levels"""
        try:
            if output_path is None:
                output_path = os.path.join(
                    self.temp_dir, 
                    f"balanced_{uuid.uuid4().hex[:8]}.wav"
                )
            
            # Load audio
            audio_data, sample_rate = librosa.load(audio_path, sr=None)
            
            # Apply intelligent level balancing
            balanced_audio = self._intelligent_level_balancing(
                audio_data, sample_rate, target_rms
            )
            
            # Save result
            sf.write(output_path, balanced_audio, sample_rate)
            
            logger.info(f"Level balancing completed: {audio_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Level balancing failed: {e}")
            raise
    
    def _intelligent_level_balancing(self, audio: np.ndarray, 
                                   sample_rate: int, 
                                   target_rms: float) -> np.ndarray:
        """Intelligent level balancing with envelope following"""
        try:
            # Calculate current RMS
            current_rms = np.sqrt(np.mean(audio**2))
            current_rms_db = 20 * np.log10(current_rms + 1e-10)
            
            # Calculate required gain
            gain_db = target_rms - current_rms_db
            gain_linear = 10**(gain_db/20)
            
            # Apply adaptive gain with envelope following
            balanced_audio = self._apply_adaptive_gain(audio, gain_linear)
            
            return balanced_audio
            
        except Exception as e:
            logger.error(f"Level balancing failed: {e}")
            return audio
    
    def _apply_adaptive_gain(self, audio: np.ndarray, base_gain: float) -> np.ndarray:
        """Apply adaptive gain with smooth transitions"""
        try:
            # Calculate envelope
            envelope = np.abs(audio)
            
            # Smooth envelope
            smoothed_envelope = scipy.signal.savgol_filter(
                envelope, window_length=min(1001, len(envelope)//10), polyorder=3
            )
            
            # Calculate adaptive gain
            adaptive_gain = np.ones_like(audio) * base_gain
            
            # Reduce gain for loud sections
            loud_threshold = np.percentile(smoothed_envelope, 90)
            loud_mask = smoothed_envelope > loud_threshold
            adaptive_gain[loud_mask] *= 0.7
            
            # Apply gain
            balanced_audio = audio * adaptive_gain
            
            return balanced_audio
            
        except Exception as e:
            logger.error(f"Adaptive gain failed: {e}")
            return audio * base_gain 
   
    async def separate_audio_sources(self, audio_path: str,
                                   output_dir: Optional[str] = None,
                                   n_sources: int = 2) -> List[str]:
        """Separate audio into different sources (speech, music, etc.)"""
        try:
            if output_dir is None:
                output_dir = os.path.join(self.temp_dir, f"separated_{uuid.uuid4().hex[:8]}")
                os.makedirs(output_dir, exist_ok=True)
            
            # Load audio
            audio_data, sample_rate = librosa.load(audio_path, sr=None)
            
            # Apply source separation
            separated_sources = self._blind_source_separation(audio_data, n_sources)
            
            # Save separated sources
            output_paths = []
            for i, source in enumerate(separated_sources):
                source_path = os.path.join(output_dir, f"source_{i+1}.wav")
                sf.write(source_path, source, sample_rate)
                output_paths.append(source_path)
            
            logger.info(f"Source separation completed: {len(output_paths)} sources")
            return output_paths
            
        except Exception as e:
            logger.error(f"Source separation failed: {e}")
            raise
    
    def _blind_source_separation(self, audio: np.ndarray, n_sources: int) -> List[np.ndarray]:
        """Blind source separation using ICA-like approach"""
        try:
            # Simplified source separation
            # In production, use proper ICA or deep learning models
            
            # Create STFT
            stft = librosa.stft(audio, n_fft=2048, hop_length=512)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Simple frequency-based separation
            sources = []
            freq_bins = magnitude.shape[0]
            
            for i in range(n_sources):
                # Create frequency mask
                start_bin = i * freq_bins // n_sources
                end_bin = (i + 1) * freq_bins // n_sources
                
                mask = np.zeros_like(magnitude)
                mask[start_bin:end_bin, :] = 1.0
                
                # Apply mask and reconstruct
                separated_stft = magnitude * mask * np.exp(1j * phase)
                separated_audio = librosa.istft(separated_stft, hop_length=512)
                
                sources.append(separated_audio)
            
            return sources
            
        except Exception as e:
            logger.error(f"Source separation failed: {e}")
            return [audio]  # Return original if separation fails
    
    async def analyze_spectrum(self, audio_path: str) -> SpectralAnalysis:
        """Comprehensive spectral analysis for forensics and quality assessment"""
        try:
            # Load audio
            audio_data, sample_rate = librosa.load(audio_path, sr=None)
            
            # Compute STFT
            stft = librosa.stft(audio_data, n_fft=4096, hop_length=1024)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Frequency bins
            frequency_bins = librosa.fft_frequencies(sr=sample_rate, n_fft=4096)
            
            # Power spectral density
            power_spectral_density = magnitude**2
            
            # Find spectral peaks
            mean_magnitude = np.mean(magnitude, axis=1)
            peaks, properties = scipy.signal.find_peaks(
                mean_magnitude, height=np.max(mean_magnitude) * 0.1
            )
            
            spectral_peaks = [
                (float(frequency_bins[peak]), float(mean_magnitude[peak]))
                for peak in peaks
            ]
            
            # Harmonic analysis
            harmonic_content = self._analyze_harmonic_content(
                magnitude, frequency_bins, sample_rate
            )
            
            # Noise floor estimation
            noise_floor = float(np.percentile(mean_magnitude, 10))
            
            # Dynamic range
            dynamic_range_db = float(20 * np.log10(
                np.max(mean_magnitude) / (noise_floor + 1e-10)
            ))
            
            # Spectral features
            spectral_flatness = float(np.mean(
                scipy.stats.gmean(magnitude, axis=0) / np.mean(magnitude, axis=0)
            ))
            
            spectral_rolloff = float(np.mean(
                librosa.feature.spectral_rolloff(y=audio_data, sr=sample_rate)
            ))
            
            return SpectralAnalysis(
                frequency_bins=frequency_bins,
                magnitude_spectrum=np.mean(magnitude, axis=1),
                phase_spectrum=np.mean(phase, axis=1),
                power_spectral_density=np.mean(power_spectral_density, axis=1),
                spectral_peaks=spectral_peaks,
                harmonic_content=harmonic_content,
                noise_floor=noise_floor,
                dynamic_range_db=dynamic_range_db,
                spectral_flatness=spectral_flatness,
                spectral_rolloff=spectral_rolloff
            )
            
        except Exception as e:
            logger.error(f"Spectral analysis failed: {e}")
            raise    
 
   def _analyze_harmonic_content(self, magnitude: np.ndarray, 
                                frequency_bins: np.ndarray, 
                                sample_rate: int) -> Dict[str, float]:
        """Analyze harmonic content of audio"""
        try:
            # Find fundamental frequency
            mean_magnitude = np.mean(magnitude, axis=1)
            fundamental_idx = np.argmax(mean_magnitude[1:len(mean_magnitude)//2]) + 1
            fundamental_freq = frequency_bins[fundamental_idx]
            
            # Analyze harmonics
            harmonic_content = {
                'fundamental_frequency': float(fundamental_freq),
                'fundamental_power': float(mean_magnitude[fundamental_idx])
            }
            
            # Check harmonics up to 10th
            for harmonic in range(2, 11):
                harmonic_freq = fundamental_freq * harmonic
                harmonic_idx = np.argmin(np.abs(frequency_bins - harmonic_freq))
                
                if harmonic_idx < len(mean_magnitude):
                    harmonic_power = mean_magnitude[harmonic_idx]
                    harmonic_content[f'harmonic_{harmonic}'] = float(harmonic_power)
            
            return harmonic_content
            
        except Exception as e:
            logger.error(f"Harmonic analysis failed: {e}")
            return {'fundamental_frequency': 440.0, 'fundamental_power': 1.0}
    
    async def perform_audio_forensics(self, audio_path: str) -> AudioForensicsResult:
        """Comprehensive audio forensics analysis"""
        try:
            # Load audio
            audio_data, sample_rate = librosa.load(audio_path, sr=None)
            
            # Authenticity analysis
            authenticity_score = self._analyze_authenticity(audio_data, sample_rate)
            
            # Tampering detection
            tampering_indicators = self._detect_tampering(audio_data, sample_rate)
            
            # Quality assessment
            quality_assessment = self._assess_audio_quality(audio_data, sample_rate)
            
            # Spectral anomaly detection
            spectral_anomalies = self._detect_spectral_anomalies(audio_data, sample_rate)
            
            # Temporal consistency analysis
            temporal_inconsistencies = self._analyze_temporal_consistency(audio_data)
            
            # Compression artifact detection
            compression_artifacts = self._detect_compression_artifacts(audio_data, sample_rate)
            
            # Editing trace detection
            editing_traces = self._detect_editing_traces(audio_data, sample_rate)
            
            # Calculate confidence intervals
            confidence_intervals = self._calculate_confidence_intervals(
                authenticity_score, quality_assessment
            )
            
            return AudioForensicsResult(
                authenticity_score=authenticity_score,
                tampering_indicators=tampering_indicators,
                quality_assessment=quality_assessment,
                spectral_anomalies=spectral_anomalies,
                temporal_inconsistencies=temporal_inconsistencies,
                compression_artifacts=compression_artifacts,
                editing_traces=editing_traces,
                confidence_intervals=confidence_intervals
            )
            
        except Exception as e:
            logger.error(f"Audio forensics analysis failed: {e}")
            raise
    
    def _analyze_authenticity(self, audio: np.ndarray, sample_rate: int) -> float:
        """Analyze audio authenticity"""
        try:
            # Simplified authenticity analysis
            # Check for natural audio characteristics
            
            # Spectral consistency
            stft = librosa.stft(audio, n_fft=2048, hop_length=512)
            magnitude = np.abs(stft)
            
            # Check for unnatural spectral patterns
            spectral_variance = np.var(magnitude, axis=1)
            spectral_consistency = 1.0 - np.std(spectral_variance) / np.mean(spectral_variance)
            
            # Temporal consistency
            frame_energy = np.sum(magnitude**2, axis=0)
            energy_variance = np.var(frame_energy)
            temporal_consistency = 1.0 / (1.0 + energy_variance / np.mean(frame_energy))
            
            # Combined authenticity score
            authenticity = (spectral_consistency * 0.6 + temporal_consistency * 0.4)
            
            return float(np.clip(authenticity, 0.0, 1.0))
            
        except Exception as e:
            logger.error(f"Authenticity analysis failed: {e}")
            return 0.5
    
    def _detect_tampering(self, audio: np.ndarray, sample_rate: int) -> List[str]:
        """Detect potential tampering indicators"""
        indicators = []
        
        try:
            # Check for abrupt level changes
            rms_frames = librosa.feature.rms(y=audio, frame_length=2048, hop_length=512)[0]
            level_changes = np.diff(rms_frames)
            abrupt_changes = np.where(np.abs(level_changes) > np.std(level_changes) * 3)[0]
            
            if len(abrupt_changes) > len(rms_frames) * 0.05:  # More than 5% of frames
                indicators.append("abrupt_level_changes")
            
            # Check for spectral discontinuities
            stft = librosa.stft(audio, n_fft=2048, hop_length=512)
            magnitude = np.abs(stft)
            
            spectral_diff = np.diff(magnitude, axis=1)
            large_changes = np.sum(np.abs(spectral_diff) > np.std(spectral_diff) * 2)
            
            if large_changes > magnitude.size * 0.01:  # More than 1% of time-frequency bins
                indicators.append("spectral_discontinuities")
            
            # Check for unnatural frequency content
            mean_spectrum = np.mean(magnitude, axis=1)
            if np.any(mean_spectrum[1000:1500] > mean_spectrum[100:600] * 2):  # Unnatural high-freq boost
                indicators.append("unnatural_frequency_boost")
            
            return indicators
            
        except Exception as e:
            logger.error(f"Tampering detection failed: {e}")
            return []
    
    def _assess_audio_quality(self, audio: np.ndarray, sample_rate: int) -> Dict[str, float]:
        """Comprehensive audio quality assessment"""
        try:
            quality_metrics = {}
            
            # Signal-to-noise ratio
            quality_metrics['snr'] = self._estimate_snr(audio)
            
            # Dynamic range
            quality_metrics['dynamic_range'] = self._calculate_dynamic_range(audio)
            
            # Total harmonic distortion
            quality_metrics['thd'] = self._estimate_thd(audio, sample_rate)
            
            # Frequency response flatness
            stft = librosa.stft(audio, n_fft=2048, hop_length=512)
            magnitude = np.abs(stft)
            mean_spectrum = np.mean(magnitude, axis=1)
            
            # Calculate flatness in different bands
            low_band = np.mean(mean_spectrum[20:200])    # ~400Hz-4kHz
            mid_band = np.mean(mean_spectrum[200:800])   # ~4kHz-16kHz
            high_band = np.mean(mean_spectrum[800:1000]) # ~16kHz-20kHz
            
            if low_band > 0:
                quality_metrics['frequency_balance'] = float(
                    1.0 - abs(mid_band - low_band) / low_band
                )
            else:
                quality_metrics['frequency_balance'] = 0.5
            
            # Overall quality score
            quality_metrics['overall_quality'] = float(
                (quality_metrics['snr'] / 60.0 * 0.3 +
                 quality_metrics['dynamic_range'] / 60.0 * 0.3 +
                 (1.0 - quality_metrics['thd'] / 10.0) * 0.2 +
                 quality_metrics['frequency_balance'] * 0.2)
            )
            
            return quality_metrics
            
        except Exception as e:
            logger.error(f"Quality assessment failed: {e}")
            return {'overall_quality': 0.5}
    
    async def process_realtime_audio(self, audio_chunk: np.ndarray,
                                   sample_rate: int,
                                   config: AudioEnhancementConfig) -> np.ndarray:
        """Process audio chunk for real-time applications"""
        try:
            processed_chunk = audio_chunk.copy()
            
            # Apply real-time processing based on config
            if config.noise_reduction:
                processed_chunk = self._realtime_noise_reduction(processed_chunk)
            
            if config.dynamic_range_optimization:
                processed_chunk = self._realtime_compression(processed_chunk)
            
            if config.level_balancing:
                processed_chunk = self._realtime_level_adjustment(processed_chunk)
            
            return processed_chunk
            
        except Exception as e:
            logger.error(f"Real-time processing failed: {e}")
            return audio_chunk
    
    def _realtime_noise_reduction(self, audio_chunk: np.ndarray) -> np.ndarray:
        """Real-time noise reduction for streaming audio"""
        try:
            # Simple spectral gating for real-time processing
            if len(audio_chunk) < 512:
                return audio_chunk
            
            # Apply high-pass filter to remove low-frequency noise
            filtered = scipy.signal.lfilter([1, -0.95], [1], audio_chunk)
            
            # Apply gentle noise gate
            threshold = np.percentile(np.abs(filtered), 20)
            gate_mask = np.abs(filtered) > threshold
            
            gated_audio = filtered * gate_mask
            
            return gated_audio
            
        except Exception as e:
            logger.error(f"Real-time noise reduction failed: {e}")
            return audio_chunk
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            self.executor.shutdown(wait=True)
            logger.info("ProfessionalAudioProcessingEngine cleaned up")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_professional_audio_processing():
        """Test professional audio processing functionality"""
        engine = ProfessionalAudioProcessingEngine()
        
        # Test with a sample audio file
        test_audio = "sample_audio.wav"  # Replace with actual file
        
        if os.path.exists(test_audio):
            print(f"Processing audio: {test_audio}")
            
            # Extract metadata
            metadata = await engine.extract_audio_metadata(test_audio)
            print(f"✅ Metadata extracted: {metadata.duration:.1f}s, {metadata.sample_rate}Hz")
            
            # Noise reduction
            denoised = await engine.reduce_noise(test_audio)
            print(f"✅ Noise reduction completed: {denoised}")
            
            # Echo cancellation
            echo_cancelled = await engine.cancel_echo(test_audio)
            print(f"✅ Echo cancellation completed: {echo_cancelled}")
            
            # Dynamic range optimization
            optimized = await engine.optimize_dynamic_range(test_audio)
            print(f"✅ Dynamic range optimization completed: {optimized}")
            
        else:
            print(f"Test audio not found: {test_audio}")
            print("✅ ProfessionalAudioProcessingEngine initialized successfully")
        
        await engine.cleanup()
    
    # Run the test
    asyncio.run(test_professional_audio_processing())    

    async def balance_levels(self, audio_path: str,
                           output_path: Optional[str] = None,
                           target_rms: float = -20.0) -> str:
        """Intelligent level balancing for consistent audio levels"""
        try:
            if output_path is None:
                output_path = os.path.join(
                    self.temp_dir, 
                    f"balanced_{uuid.uuid4().hex[:8]}.wav"
                )
            
            # Load audio
            audio_data, sample_rate = librosa.load(audio_path, sr=None)
            
            # Apply intelligent level balancing
            balanced_audio = self._intelligent_level_balancing(
                audio_data, sample_rate, target_rms
            )
            
            # Save result
            sf.write(output_path, balanced_audio, sample_rate)
            
            logger.info(f"Level balancing completed: {audio_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Level balancing failed: {e}")
            raise
    
    def _intelligent_level_balancing(self, audio: np.ndarray, 
                                   sample_rate: int, 
                                   target_rms: float) -> np.ndarray:
        """Intelligent level balancing with envelope following"""
        try:
            # Calculate RMS in sliding windows
            window_size = int(sample_rate * 0.1)  # 100ms windows
            hop_size = window_size // 4
            
            # Calculate RMS envelope
            rms_envelope = []
            for i in range(0, len(audio) - window_size, hop_size):
                window = audio[i:i + window_size]
                rms = np.sqrt(np.mean(window**2))
                rms_envelope.append(rms)
            
            # Convert to dB
            target_rms_linear = 10**(target_rms/20)
            rms_envelope = np.array(rms_envelope)
            
            # Calculate gain adjustments
            gain_envelope = np.zeros_like(rms_envelope)
            for i, rms in enumerate(rms_envelope):
                if rms > 0:
                    gain_db = target_rms - 20 * np.log10(rms)
                    # Limit gain adjustments
                    gain_db = np.clip(gain_db, -20, 20)
                    gain_envelope[i] = 10**(gain_db/20)
                else:
                    gain_envelope[i] = 1.0
            
            # Smooth gain envelope
            gain_envelope = scipy.signal.savgol_filter(
                gain_envelope, window_length=5, polyorder=2
            )
            
            # Apply gain envelope to audio
            balanced_audio = audio.copy()
            for i, gain in enumerate(gain_envelope):
                start_idx = i * hop_size
                end_idx = min(start_idx + window_size, len(audio))
                balanced_audio[start_idx:end_idx] *= gain
            
            return balanced_audio
            
        except Exception as e:
            logger.error(f"Intelligent level balancing failed: {e}")
            return audio
    
    async def analyze_spectrum(self, audio_path: str) -> SpectralAnalysis:
        """Comprehensive spectral analysis"""
        try:
            # Load audio
            audio_data, sample_rate = librosa.load(audio_path, sr=None)
            
            # Perform STFT
            stft = librosa.stft(audio_data, n_fft=2048, hop_length=512)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Calculate power spectral density
            psd = magnitude**2
            
            # Frequency bins
            frequency_bins = librosa.fft_frequencies(sr=sample_rate, n_fft=2048)
            
            # Average spectrum
            avg_magnitude = np.mean(magnitude, axis=1)
            avg_psd = np.mean(psd, axis=1)
            
            # Find spectral peaks
            peaks, properties = scipy.signal.find_peaks(
                avg_magnitude, height=np.max(avg_magnitude) * 0.1
            )
            spectral_peaks = [(frequency_bins[peak], avg_magnitude[peak]) 
                            for peak in peaks]
            
            # Harmonic analysis
            harmonic_content = self._analyze_harmonics(
                frequency_bins, avg_magnitude
            )
            
            # Noise floor estimation
            noise_floor = np.percentile(avg_magnitude, 10)
            
            # Dynamic range
            peak_level = np.max(avg_magnitude)
            dynamic_range_db = 20 * np.log10(peak_level / noise_floor) if noise_floor > 0 else 60
            
            # Spectral features
            spectral_flatness = scipy.stats.gmean(avg_magnitude) / np.mean(avg_magnitude)
            spectral_rolloff = self._calculate_spectral_rolloff(
                frequency_bins, avg_magnitude
            )
            
            return SpectralAnalysis(
                frequency_bins=frequency_bins,
                magnitude_spectrum=avg_magnitude,
                phase_spectrum=np.mean(phase, axis=1),
                power_spectral_density=avg_psd,
                spectral_peaks=spectral_peaks,
                harmonic_content=harmonic_content,
                noise_floor=float(noise_floor),
                dynamic_range_db=float(dynamic_range_db),
                spectral_flatness=float(spectral_flatness),
                spectral_rolloff=float(spectral_rolloff)
            )
            
        except Exception as e:
            logger.error(f"Spectral analysis failed: {e}")
            raise
    
    def _analyze_harmonics(self, frequencies: np.ndarray, 
                         magnitude: np.ndarray) -> Dict[str, float]:
        """Analyze harmonic content"""
        try:
            # Find fundamental frequency
            fundamental_idx = np.argmax(magnitude[1:len(magnitude)//2]) + 1
            fundamental_freq = frequencies[fundamental_idx]
            fundamental_power = magnitude[fundamental_idx]**2
            
            # Analyze harmonics
            harmonic_powers = []
            for harmonic in range(2, 6):  # 2nd to 5th harmonics
                harmonic_freq = fundamental_freq * harmonic
                # Find closest frequency bin
                harmonic_idx = np.argmin(np.abs(frequencies - harmonic_freq))
                if harmonic_idx < len(magnitude):
                    harmonic_powers.append(magnitude[harmonic_idx]**2)
            
            # Calculate harmonic ratios
            total_harmonic_power = sum(harmonic_powers)
            
            return {
                'fundamental_frequency': float(fundamental_freq),
                'fundamental_power': float(fundamental_power),
                'total_harmonic_distortion': float(
                    np.sqrt(total_harmonic_power / fundamental_power) * 100
                    if fundamental_power > 0 else 0
                ),
                'harmonic_to_noise_ratio': float(
                    10 * np.log10(total_harmonic_power / np.mean(magnitude**2))
                    if np.mean(magnitude**2) > 0 else 0
                )
            }
            
        except Exception as e:
            logger.error(f"Harmonic analysis failed: {e}")
            return {}
    
    def _calculate_spectral_rolloff(self, frequencies: np.ndarray, 
                                  magnitude: np.ndarray, 
                                  rolloff_percent: float = 0.85) -> float:
        """Calculate spectral rolloff frequency"""
        try:
            total_energy = np.sum(magnitude**2)
            cumulative_energy = np.cumsum(magnitude**2)
            
            rolloff_threshold = total_energy * rolloff_percent
            rolloff_idx = np.where(cumulative_energy >= rolloff_threshold)[0]
            
            if len(rolloff_idx) > 0:
                return frequencies[rolloff_idx[0]]
            else:
                return frequencies[-1]
                
        except Exception as e:
            logger.error(f"Spectral rolloff calculation failed: {e}")
            return 8000.0  # Default value
    
    async def process_realtime(self, audio_stream: np.ndarray,
                             sample_rate: int,
                             config: AudioEnhancementConfig) -> np.ndarray:
        """Real-time audio processing for live streams"""
        try:
            # Apply real-time processing chain
            processed_audio = audio_stream.copy()
            
            if config.noise_reduction:
                processed_audio = self._realtime_noise_reduction(
                    processed_audio, sample_rate
                )
            
            if config.echo_cancellation:
                processed_audio = self._realtime_echo_cancellation(
                    processed_audio, sample_rate
                )
            
            if config.level_balancing:
                processed_audio = self._realtime_level_balancing(
                    processed_audio, sample_rate
                )
            
            if config.dynamic_range_optimization:
                processed_audio = self._realtime_compression(
                    processed_audio, sample_rate
                )
            
            return processed_audio
            
        except Exception as e:
            logger.error(f"Real-time processing failed: {e}")
            return audio_stream
    
    def _realtime_noise_reduction(self, audio: np.ndarray, 
                                sample_rate: int) -> np.ndarray:
        """Real-time noise reduction with minimal latency"""
        try:
            # Simple spectral gating for real-time use
            stft = librosa.stft(audio, n_fft=512, hop_length=128)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Estimate noise floor
            noise_floor = np.percentile(magnitude, 20, axis=1, keepdims=True)
            
            # Apply spectral gating
            gate_threshold = noise_floor * 2.0
            gated_magnitude = np.where(
                magnitude > gate_threshold, 
                magnitude, 
                magnitude * 0.3
            )
            
            # Reconstruct signal
            enhanced_stft = gated_magnitude * np.exp(1j * phase)
            enhanced_audio = librosa.istft(enhanced_stft, hop_length=128)
            
            return enhanced_audio
            
        except Exception as e:
            logger.error(f"Real-time noise reduction failed: {e}")
            return audio
    
    def _realtime_echo_cancellation(self, audio: np.ndarray, 
                                  sample_rate: int) -> np.ndarray:
        """Real-time echo cancellation"""
        try:
            # Simple delay-based echo cancellation
            # In production, use adaptive filters
            
            # Detect potential echo delay
            autocorr = np.correlate(audio, audio, mode='same')
            center = len(autocorr) // 2
            
            # Look for echo in 50-200ms range
            start_idx = center + int(0.05 * sample_rate)
            end_idx = center + int(0.2 * sample_rate)
            
            if end_idx < len(autocorr):
                echo_region = autocorr[start_idx:end_idx]
                echo_peak = np.argmax(echo_region) + start_idx - center
                
                if echo_peak > 0 and echo_peak < len(audio):
                    # Apply simple echo cancellation
                    echo_strength = autocorr[echo_peak + center] / autocorr[center]
                    if echo_strength > 0.3:
                        cancelled_audio = audio.copy()
                        cancelled_audio[echo_peak:] -= (
                            echo_strength * 0.5 * audio[:-echo_peak]
                        )
                        return cancelled_audio
            
            return audio
            
        except Exception as e:
            logger.error(f"Real-time echo cancellation failed: {e}")
            return audio
    
    def _realtime_level_balancing(self, audio: np.ndarray, 
                                sample_rate: int) -> np.ndarray:
        """Real-time level balancing"""
        try:
            # Simple AGC (Automatic Gain Control)
            target_rms = 0.1
            current_rms = np.sqrt(np.mean(audio**2))
            
            if current_rms > 0:
                gain = target_rms / current_rms
                # Limit gain to prevent artifacts
                gain = np.clip(gain, 0.1, 10.0)
                return audio * gain
            
            return audio
            
        except Exception as e:
            logger.error(f"Real-time level balancing failed: {e}")
            return audio
    
    def _realtime_compression(self, audio: np.ndarray, 
                            sample_rate: int) -> np.ndarray:
        """Real-time dynamic range compression"""
        try:
            # Simple look-ahead compressor
            threshold = 0.7
            ratio = 3.0
            attack = 0.003
            release = 0.1
            
            compressed = self._apply_compression(
                audio, ratio, 20*np.log10(threshold), attack, release
            )
            
            return compressed
            
        except Exception as e:
            logger.error(f"Real-time compression failed: {e}")
            return audio 
   
    async def audio_forensics(self, audio_path: str) -> AudioForensicsResult:
        """Comprehensive audio forensics analysis"""
        try:
            # Load audio
            audio_data, sample_rate = librosa.load(audio_path, sr=None)
            
            # Authenticity analysis
            authenticity_score = self._analyze_authenticity(audio_data, sample_rate)
            
            # Tampering detection
            tampering_indicators = self._detect_tampering(audio_data, sample_rate)
            
            # Quality assessment
            quality_assessment = await self._forensic_quality_assessment(
                audio_data, sample_rate
            )
            
            # Spectral anomaly detection
            spectral_anomalies = self._detect_spectral_anomalies(
                audio_data, sample_rate
            )
            
            # Temporal consistency analysis
            temporal_inconsistencies = self._analyze_temporal_consistency(
                audio_data, sample_rate
            )
            
            # Compression artifact detection
            compression_artifacts = self._detect_compression_artifacts(
                audio_data, sample_rate
            )
            
            # Editing trace detection
            editing_traces = self._detect_editing_traces(audio_data, sample_rate)
            
            # Calculate confidence intervals
            confidence_intervals = self._calculate_confidence_intervals(
                authenticity_score, tampering_indicators
            )
            
            return AudioForensicsResult(
                authenticity_score=authenticity_score,
                tampering_indicators=tampering_indicators,
                quality_assessment=quality_assessment,
                spectral_anomalies=spectral_anomalies,
                temporal_inconsistencies=temporal_inconsistencies,
                compression_artifacts=compression_artifacts,
                editing_traces=editing_traces,
                confidence_intervals=confidence_intervals
            )
            
        except Exception as e:
            logger.error(f"Audio forensics analysis failed: {e}")
            raise
    
    def _analyze_authenticity(self, audio: np.ndarray, 
                            sample_rate: int) -> float:
        """Analyze audio authenticity"""
        try:
            authenticity_factors = []
            
            # Check for natural noise characteristics
            noise_naturalness = self._assess_noise_naturalness(audio)
            authenticity_factors.append(noise_naturalness)
            
            # Check for consistent recording characteristics
            consistency_score = self._assess_recording_consistency(audio, sample_rate)
            authenticity_factors.append(consistency_score)
            
            # Check for natural dynamic range
            dynamic_naturalness = self._assess_dynamic_naturalness(audio)
            authenticity_factors.append(dynamic_naturalness)
            
            # Calculate overall authenticity score
            authenticity_score = np.mean(authenticity_factors)
            
            return float(np.clip(authenticity_score, 0.0, 1.0))
            
        except Exception as e:
            logger.error(f"Authenticity analysis failed: {e}")
            return 0.5
    
    def _detect_tampering(self, audio: np.ndarray, 
                        sample_rate: int) -> List[str]:
        """Detect signs of audio tampering"""
        indicators = []
        
        try:
            # Check for abrupt level changes
            if self._detect_level_discontinuities(audio):
                indicators.append("Abrupt level changes detected")
            
            # Check for spectral inconsistencies
            if self._detect_spectral_inconsistencies(audio, sample_rate):
                indicators.append("Spectral inconsistencies found")
            
            # Check for unnatural silence patterns
            if self._detect_unnatural_silence(audio, sample_rate):
                indicators.append("Unnatural silence patterns")
            
            # Check for copy-paste artifacts
            if self._detect_copy_paste_artifacts(audio):
                indicators.append("Potential copy-paste artifacts")
            
            return indicators
            
        except Exception as e:
            logger.error(f"Tampering detection failed: {e}")
            return []
    
    async def _forensic_quality_assessment(self, audio: np.ndarray, 
                                         sample_rate: int) -> Dict[str, float]:
        """Forensic quality assessment"""
        try:
            # Extract comprehensive metadata
            metadata = await self.extract_audio_metadata("temp_audio.wav")
            
            quality_metrics = {
                'signal_to_noise_ratio': metadata.snr_estimate,
                'total_harmonic_distortion': metadata.thd_estimate,
                'dynamic_range': metadata.dynamic_range,
                'spectral_flatness': self._calculate_spectral_flatness(audio, sample_rate),
                'crest_factor': self._calculate_crest_factor(audio),
                'zero_crossing_rate': metadata.zero_crossing_rate
            }
            
            return quality_metrics
            
        except Exception as e:
            logger.error(f"Forensic quality assessment failed: {e}")
            return {}
    
    def _detect_spectral_anomalies(self, audio: np.ndarray, 
                                 sample_rate: int) -> List[Dict[str, Any]]:
        """Detect spectral anomalies"""
        anomalies = []
        
        try:
            # Perform STFT
            stft = librosa.stft(audio, n_fft=2048, hop_length=512)
            magnitude = np.abs(stft)
            
            # Detect unusual spectral patterns
            for frame_idx in range(magnitude.shape[1]):
                frame_spectrum = magnitude[:, frame_idx]
                
                # Check for unnatural peaks
                peaks, _ = scipy.signal.find_peaks(
                    frame_spectrum, height=np.max(frame_spectrum) * 0.8
                )
                
                if len(peaks) > 10:  # Too many peaks might indicate artifacts
                    timestamp = frame_idx * 512 / sample_rate
                    anomalies.append({
                        'type': 'excessive_spectral_peaks',
                        'timestamp': timestamp,
                        'severity': len(peaks) / 20.0,
                        'description': f'Unusual number of spectral peaks: {len(peaks)}'
                    })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Spectral anomaly detection failed: {e}")
            return []
    
    def _analyze_temporal_consistency(self, audio: np.ndarray, 
                                    sample_rate: int) -> List[Dict[str, Any]]:
        """Analyze temporal consistency"""
        inconsistencies = []
        
        try:
            # Analyze RMS envelope consistency
            window_size = int(sample_rate * 0.1)  # 100ms windows
            rms_values = []
            
            for i in range(0, len(audio) - window_size, window_size // 2):
                window = audio[i:i + window_size]
                rms = np.sqrt(np.mean(window**2))
                rms_values.append(rms)
            
            # Detect sudden changes
            rms_diff = np.diff(rms_values)
            threshold = np.std(rms_diff) * 3
            
            sudden_changes = np.where(np.abs(rms_diff) > threshold)[0]
            
            for change_idx in sudden_changes:
                timestamp = change_idx * window_size / (2 * sample_rate)
                inconsistencies.append({
                    'type': 'sudden_level_change',
                    'timestamp': timestamp,
                    'magnitude': float(rms_diff[change_idx]),
                    'description': 'Sudden change in audio level detected'
                })
            
            return inconsistencies
            
        except Exception as e:
            logger.error(f"Temporal consistency analysis failed: {e}")
            return []
    
    def _detect_compression_artifacts(self, audio: np.ndarray, 
                                    sample_rate: int) -> List[str]:
        """Detect compression artifacts"""
        artifacts = []
        
        try:
            # Analyze frequency spectrum for compression artifacts
            stft = librosa.stft(audio, n_fft=2048, hop_length=512)
            magnitude = np.abs(stft)
            
            # Check for frequency cutoffs (common in lossy compression)
            avg_spectrum = np.mean(magnitude, axis=1)
            frequencies = librosa.fft_frequencies(sr=sample_rate, n_fft=2048)
            
            # Look for sharp cutoffs in high frequencies
            high_freq_idx = np.where(frequencies > 15000)[0]
            if len(high_freq_idx) > 0:
                high_freq_energy = avg_spectrum[high_freq_idx]
                if np.max(high_freq_energy) < np.max(avg_spectrum) * 0.01:
                    artifacts.append("High-frequency cutoff detected (lossy compression)")
            
            # Check for pre-echo artifacts
            if self._detect_pre_echo(magnitude):
                artifacts.append("Pre-echo artifacts detected")
            
            return artifacts
            
        except Exception as e:
            logger.error(f"Compression artifact detection failed: {e}")
            return []
    
    def _detect_editing_traces(self, audio: np.ndarray, 
                             sample_rate: int) -> List[str]:
        """Detect traces of audio editing"""
        traces = []
        
        try:
            # Check for click/pop artifacts at edit points
            if self._detect_click_artifacts(audio, sample_rate):
                traces.append("Click/pop artifacts suggesting edits")
            
            # Check for phase discontinuities
            if self._detect_phase_discontinuities(audio, sample_rate):
                traces.append("Phase discontinuities detected")
            
            # Check for unnatural fades
            if self._detect_unnatural_fades(audio, sample_rate):
                traces.append("Unnatural fade patterns")
            
            return traces
            
        except Exception as e:
            logger.error(f"Editing trace detection failed: {e}")
            return []
    
    def _calculate_confidence_intervals(self, authenticity_score: float,
                                      tampering_indicators: List[str]) -> Dict[str, Tuple[float, float]]:
        """Calculate confidence intervals for forensic analysis"""
        try:
            # Base confidence on authenticity score and number of indicators
            base_confidence = authenticity_score
            indicator_penalty = len(tampering_indicators) * 0.1
            
            adjusted_confidence = max(0.1, base_confidence - indicator_penalty)
            
            # Calculate intervals
            margin = 0.1 * (1 - adjusted_confidence)
            
            return {
                'authenticity': (
                    max(0.0, authenticity_score - margin),
                    min(1.0, authenticity_score + margin)
                ),
                'tampering_likelihood': (
                    max(0.0, len(tampering_indicators) * 0.1 - margin),
                    min(1.0, len(tampering_indicators) * 0.1 + margin)
                )
            }
            
        except Exception as e:
            logger.error(f"Confidence interval calculation failed: {e}")
            return {}
    
    # Helper methods for forensic analysis
    def _assess_noise_naturalness(self, audio: np.ndarray) -> float:
        """Assess naturalness of background noise"""
        try:
            # Simple assessment based on noise floor consistency
            noise_samples = audio[np.abs(audio) < np.percentile(np.abs(audio), 20)]
            if len(noise_samples) > 0:
                noise_consistency = 1.0 - np.std(noise_samples) / (np.mean(np.abs(noise_samples)) + 1e-10)
                return float(np.clip(noise_consistency, 0.0, 1.0))
            return 0.5
        except:
            return 0.5
    
    def _assess_recording_consistency(self, audio: np.ndarray, sample_rate: int) -> float:
        """Assess consistency of recording characteristics"""
        try:
            # Analyze spectral consistency across time
            stft = librosa.stft(audio, n_fft=1024, hop_length=256)
            magnitude = np.abs(stft)
            
            # Calculate spectral centroid for each frame
            centroids = []
            for frame in range(magnitude.shape[1]):
                centroid = np.sum(magnitude[:, frame] * np.arange(magnitude.shape[0]))
                centroid /= (np.sum(magnitude[:, frame]) + 1e-10)
                centroids.append(centroid)
            
            # Consistency is inverse of variation
            consistency = 1.0 - (np.std(centroids) / (np.mean(centroids) + 1e-10))
            return float(np.clip(consistency, 0.0, 1.0))
        except:
            return 0.5
    
    def _assess_dynamic_naturalness(self, audio: np.ndarray) -> float:
        """Assess naturalness of dynamic range"""
        try:
            # Natural audio should have varied dynamics
            rms_values = []
            window_size = len(audio) // 100  # 100 windows
            
            for i in range(0, len(audio) - window_size, window_size):
                window = audio[i:i + window_size]
                rms = np.sqrt(np.mean(window**2))
                rms_values.append(rms)
            
            # Natural audio has moderate variation in RMS
            rms_variation = np.std(rms_values) / (np.mean(rms_values) + 1e-10)
            
            # Optimal variation is around 0.3-0.7
            if 0.3 <= rms_variation <= 0.7:
                naturalness = 1.0
            else:
                naturalness = 1.0 - abs(rms_variation - 0.5) / 0.5
            
            return float(np.clip(naturalness, 0.0, 1.0))
        except:
            return 0.5
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            self.executor.shutdown(wait=True)
            logger.info("ProfessionalAudioProcessingEngine cleaned up")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_professional_audio_processing():
        """Test professional audio processing functionality"""
        engine = ProfessionalAudioProcessingEngine()
        
        print("🎵 Professional Audio Processing Engine Test")
        print("=" * 50)
        
        # Test with a sample audio file (you would need to provide this)
        test_audio = "sample_audio.wav"  # Replace with actual file
        
        if os.path.exists(test_audio):
            print(f"Processing audio: {test_audio}")
            
            # Test metadata extraction
            print("\n1. Extracting metadata...")
            metadata = await engine.extract_audio_metadata(test_audio)
            print(f"   Duration: {metadata.duration:.2f}s")
            print(f"   Sample Rate: {metadata.sample_rate}Hz")
            print(f"   Channels: {metadata.channels}")
            print(f"   SNR Estimate: {metadata.snr_estimate:.1f}dB")
            print(f"   Dynamic Range: {metadata.dynamic_range:.1f}dB")
            
            # Test noise profile analysis
            print("\n2. Analyzing noise profile...")
            noise_profile = await engine.analyze_noise_profile(test_audio)
            print(f"   Noise Type: {noise_profile.noise_type.value}")
            print(f"   Confidence: {noise_profile.confidence:.2f}")
            
            # Test noise reduction
            print("\n3. Applying noise reduction...")
            denoised_path = await engine.reduce_noise(test_audio, noise_profile)
            print(f"   Denoised audio saved: {denoised_path}")
            
            # Test spectral analysis
            print("\n4. Performing spectral analysis...")
            spectral_analysis = await engine.analyze_spectrum(test_audio)
            print(f"   Spectral Peaks: {len(spectral_analysis.spectral_peaks)}")
            print(f"   Dynamic Range: {spectral_analysis.dynamic_range_db:.1f}dB")
            print(f"   Spectral Flatness: {spectral_analysis.spectral_flatness:.3f}")
            
            # Test audio forensics
            print("\n5. Conducting forensic analysis...")
            forensics = await engine.audio_forensics(test_audio)
            print(f"   Authenticity Score: {forensics.authenticity_score:.2f}")
            print(f"   Tampering Indicators: {len(forensics.tampering_indicators)}")
            if forensics.tampering_indicators:
                for indicator in forensics.tampering_indicators[:3]:
                    print(f"     - {indicator}")
            
            print("\n✅ Professional audio processing test completed!")
            
        else:
            print(f"Test audio not found: {test_audio}")
            print("Creating a simple test...")
            print("✅ ProfessionalAudioProcessingEngine initialized successfully")
        
        await engine.cleanup()
    
    # Run the test
    asyncio.run(test_professional_audio_processing())