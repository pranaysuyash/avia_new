"""
Comprehensive Audio Enhancement Pipeline

This module provides advanced audio enhancement capabilities including noise reduction,
audio normalization, gain control, automatic quality assessment, audio repair for
corrupted segments, and format optimization recommendations.

Features:
- Noise reduction using advanced algorithms
- Audio normalization and gain control
- Automatic audio quality assessment
- Audio repair for corrupted segments
- Format optimization recommendations
- Real-time audio enhancement
- Batch processing capabilities
- Quality metrics and reporting
"""

import os
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

# Audio processing
import librosa
import soundfile as sf
from scipy import signal, stats
from scipy.ndimage import median_filter
from scipy.signal import butter, filtfilt, hilbert

# Audio enhancement libraries
try:
    import noisereduce as nr
except ImportError:
    nr = None
    
try:
    from pydub import AudioSegment
    from pydub.effects import normalize, compress_dynamic_range
except ImportError:
    AudioSegment = None

# Machine learning
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.metrics import mean_squared_error

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AudioQualityMetrics:
    """Comprehensive audio quality assessment metrics"""
    # Signal quality metrics
    snr_db: float  # Signal-to-noise ratio
    thd_percent: float  # Total harmonic distortion
    dynamic_range_db: float  # Dynamic range
    peak_level_db: float  # Peak level
    rms_level_db: float  # RMS level
    
    # Spectral quality metrics
    spectral_flatness: float  # Spectral flatness measure
    spectral_centroid_hz: float  # Spectral centroid
    spectral_bandwidth_hz: float  # Spectral bandwidth
    spectral_rolloff_hz: float  # Spectral rolloff
    
    # Temporal quality metrics
    zero_crossing_rate: float  # Zero crossing rate
    silence_ratio: float  # Ratio of silence to total duration
    clipping_ratio: float  # Ratio of clipped samples
    
    # Perceptual quality metrics
    loudness_lufs: float  # Loudness in LUFS
    perceived_quality_score: float  # Overall perceived quality (0-100)
    
    # Enhancement recommendations
    needs_noise_reduction: bool
    needs_normalization: bool
    needs_gain_adjustment: bool
    needs_repair: bool
    
    # Overall quality rating
    quality_rating: str  # excellent, good, fair, poor

@dataclass
class EnhancementResult:
    """Result of audio enhancement processing"""
    original_path: str
    enhanced_path: str
    enhancement_applied: List[str]
    quality_before: AudioQualityMetrics
    quality_after: AudioQualityMetrics
    improvement_score: float
    processing_time: float
    recommendations: List[str]

@dataclass
class AudioRepairResult:
    """Result of audio repair processing"""
    corrupted_segments: List[Tuple[float, float]]  # Start and end times
    repair_methods_used: List[str]
    repair_success_rate: float
    repaired_duration: float
    total_duration: floatc
lass NoiseReducer:
    """Advanced noise reduction system"""
    
    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self.noise_gate_threshold = -40  # dB
        self.reduction_strength = 0.8
        
    def reduce_noise(self, audio_path: str, output_path: str = None, 
                    method: str = 'spectral_gating') -> str:
        """Apply noise reduction to audio file"""
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Apply noise reduction based on method
            if method == 'spectral_gating' and nr is not None:
                # Use noisereduce library for spectral gating
                reduced_noise = nr.reduce_noise(y=y, sr=sr)
            elif method == 'wiener_filter':
                reduced_noise = self._wiener_filter(y)
            elif method == 'spectral_subtraction':
                reduced_noise = self._spectral_subtraction(y, sr)
            elif method == 'adaptive_filter':
                reduced_noise = self._adaptive_filter(y)
            else:
                # Fallback to basic noise gate
                reduced_noise = self._noise_gate(y)
            
            # Generate output path if not provided
            if output_path is None:
                base_path = Path(audio_path)
                output_path = str(base_path.parent / f"{base_path.stem}_denoised{base_path.suffix}")
            
            # Save enhanced audio
            sf.write(output_path, reduced_noise, sr)
            
            logger.info(f"Noise reduction applied: {audio_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error in noise reduction: {e}")
            return audio_path
    
    def _wiener_filter(self, y: np.ndarray, noise_factor: float = 0.1) -> np.ndarray:
        """Apply Wiener filter for noise reduction"""
        try:
            # Estimate noise from first 0.5 seconds
            noise_sample_length = min(int(0.5 * self.sample_rate), len(y) // 4)
            noise_estimate = np.var(y[:noise_sample_length])
            
            # Apply Wiener filter
            signal_power = np.var(y)
            wiener_gain = signal_power / (signal_power + noise_estimate * noise_factor)
            
            return y * wiener_gain
            
        except Exception as e:
            logger.error(f"Error in Wiener filter: {e}")
            return y
    
    def _spectral_subtraction(self, y: np.ndarray, sr: int) -> np.ndarray:
        """Apply spectral subtraction for noise reduction"""
        try:
            # Compute STFT
            stft = librosa.stft(y, hop_length=512, n_fft=2048)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Estimate noise spectrum from first 0.5 seconds
            noise_frames = int(0.5 * sr / 512)
            noise_spectrum = np.mean(magnitude[:, :noise_frames], axis=1, keepdims=True)
            
            # Apply spectral subtraction
            alpha = 2.0  # Over-subtraction factor
            enhanced_magnitude = magnitude - alpha * noise_spectrum
            
            # Ensure non-negative values
            enhanced_magnitude = np.maximum(enhanced_magnitude, 0.1 * magnitude)
            
            # Reconstruct signal
            enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
            enhanced_audio = librosa.istft(enhanced_stft, hop_length=512)
            
            return enhanced_audio
            
        except Exception as e:
            logger.error(f"Error in spectral subtraction: {e}")
            return y
    
    def _adaptive_filter(self, y: np.ndarray, filter_length: int = 64) -> np.ndarray:
        """Apply adaptive filter for noise reduction"""
        try:
            # Simple LMS adaptive filter
            filtered = np.zeros_like(y)
            w = np.zeros(filter_length)
            mu = 0.01  # Step size
            
            for i in range(filter_length, len(y)):
                x = y[i-filter_length:i]
                y_pred = np.dot(w, x)
                error = y[i] - y_pred
                w += mu * error * x
                filtered[i] = y_pred
            
            return filtered
            
        except Exception as e:
            logger.error(f"Error in adaptive filter: {e}")
            return y
    
    def _noise_gate(self, y: np.ndarray) -> np.ndarray:
        """Apply noise gate to reduce low-level noise"""
        try:
            # Convert to dB
            y_db = 20 * np.log10(np.abs(y) + 1e-10)
            
            # Apply gate
            gate_mask = y_db > self.noise_gate_threshold
            gated_audio = y * gate_mask
            
            return gated_audio
            
        except Exception as e:
            logger.error(f"Error in noise gate: {e}")
            return y

class AudioNormalizer:
    """Advanced audio normalization and gain control"""
    
    def __init__(self):
        self.target_lufs = -23.0  # EBU R128 standard
        self.peak_limit_db = -1.0
        self.dynamic_range_target = 20.0  # dB
    
    def normalize_audio(self, audio_path: str, output_path: str = None,
                       method: str = 'peak_normalization') -> str:
        """Normalize audio using specified method"""
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=None)
            
            # Apply normalization based on method
            if method == 'peak_normalization':
                normalized = self._peak_normalization(y)
            elif method == 'rms_normalization':
                normalized = self._rms_normalization(y)
            elif method == 'lufs_normalization':
                normalized = self._lufs_normalization(y, sr)
            elif method == 'dynamic_range_compression':
                normalized = self._dynamic_range_compression(y)
            else:
                normalized = self._peak_normalization(y)  # Default
            
            # Generate output path if not provided
            if output_path is None:
                base_path = Path(audio_path)
                output_path = str(base_path.parent / f"{base_path.stem}_normalized{base_path.suffix}")
            
            # Save normalized audio
            sf.write(output_path, normalized, sr)
            
            logger.info(f"Audio normalized: {audio_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error in audio normalization: {e}")
            return audio_path
    
    def _peak_normalization(self, y: np.ndarray, target_db: float = -1.0) -> np.ndarray:
        """Normalize audio to target peak level"""
        try:
            # Find peak level
            peak_level = np.max(np.abs(y))
            
            if peak_level > 0:
                # Calculate gain needed
                target_linear = 10 ** (target_db / 20)
                gain = target_linear / peak_level
                
                # Apply gain
                normalized = y * gain
                
                return normalized
            
            return y
            
        except Exception as e:
            logger.error(f"Error in peak normalization: {e}")
            return y
    
    def _rms_normalization(self, y: np.ndarray, target_db: float = -20.0) -> np.ndarray:
        """Normalize audio to target RMS level"""
        try:
            # Calculate RMS
            rms_level = np.sqrt(np.mean(y**2))
            
            if rms_level > 0:
                # Calculate gain needed
                target_linear = 10 ** (target_db / 20)
                gain = target_linear / rms_level
                
                # Apply gain with peak limiting
                normalized = y * gain
                peak_level = np.max(np.abs(normalized))
                
                if peak_level > 0.95:  # Prevent clipping
                    normalized = normalized * (0.95 / peak_level)
                
                return normalized
            
            return y
            
        except Exception as e:
            logger.error(f"Error in RMS normalization: {e}")
            return y
    
    def _lufs_normalization(self, y: np.ndarray, sr: int) -> np.ndarray:
        """Normalize audio to target LUFS level"""
        try:
            # Simplified LUFS calculation (basic implementation)
            # Real LUFS requires more complex filtering and gating
            
            # Apply K-weighting filter (simplified)
            # High-frequency pre-filter
            b, a = butter(2, 1500 / (sr / 2), btype='high')
            filtered = filtfilt(b, a, y)
            
            # Calculate mean square with gating
            mean_square = np.mean(filtered**2)
            
            if mean_square > 0:
                current_lufs = -0.691 + 10 * np.log10(mean_square)
                gain_db = self.target_lufs - current_lufs
                gain_linear = 10 ** (gain_db / 20)
                
                normalized = y * gain_linear
                
                # Peak limiting
                peak_level = np.max(np.abs(normalized))
                if peak_level > 0.95:
                    normalized = normalized * (0.95 / peak_level)
                
                return normalized
            
            return y
            
        except Exception as e:
            logger.error(f"Error in LUFS normalization: {e}")
            return y
    
    def _dynamic_range_compression(self, y: np.ndarray, 
                                  threshold_db: float = -20.0,
                                  ratio: float = 4.0) -> np.ndarray:
        """Apply dynamic range compression"""
        try:
            # Convert to dB
            y_abs = np.abs(y)
            y_db = 20 * np.log10(y_abs + 1e-10)
            
            # Apply compression
            compressed_db = np.where(
                y_db > threshold_db,
                threshold_db + (y_db - threshold_db) / ratio,
                y_db
            )
            
            # Convert back to linear
            compressed_linear = 10 ** (compressed_db / 20)
            
            # Preserve sign
            compressed = compressed_linear * np.sign(y)
            
            return compressed
            
        except Exception as e:
            logger.error(f"Error in dynamic range compression: {e}")
            return y

class AudioQualityAssessor:
    """Automatic audio quality assessment system"""
    
    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
    
    def assess_quality(self, audio_path: str) -> AudioQualityMetrics:
        """Perform comprehensive audio quality assessment"""
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Calculate all quality metrics
            metrics = AudioQualityMetrics(
                snr_db=self._calculate_snr(y),
                thd_percent=self._calculate_thd(y, sr),
                dynamic_range_db=self._calculate_dynamic_range(y),
                peak_level_db=self._calculate_peak_level(y),
                rms_level_db=self._calculate_rms_level(y),
                spectral_flatness=self._calculate_spectral_flatness(y),
                spectral_centroid_hz=self._calculate_spectral_centroid(y, sr),
                spectral_bandwidth_hz=self._calculate_spectral_bandwidth(y, sr),
                spectral_rolloff_hz=self._calculate_spectral_rolloff(y, sr),
                zero_crossing_rate=self._calculate_zcr(y),
                silence_ratio=self._calculate_silence_ratio(y),
                clipping_ratio=self._calculate_clipping_ratio(y),
                loudness_lufs=self._calculate_loudness(y, sr),
                perceived_quality_score=0.0,  # Will be calculated
                needs_noise_reduction=False,  # Will be determined
                needs_normalization=False,  # Will be determined
                needs_gain_adjustment=False,  # Will be determined
                needs_repair=False,  # Will be determined
                quality_rating="good"  # Will be determined
            )
            
            # Calculate perceived quality score
            metrics.perceived_quality_score = self._calculate_perceived_quality(metrics)
            
            # Determine enhancement needs
            self._determine_enhancement_needs(metrics)
            
            # Determine overall quality rating
            metrics.quality_rating = self._determine_quality_rating(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error in quality assessment: {e}")
            return self._default_quality_metrics()
    
    def _calculate_snr(self, y: np.ndarray) -> float:
        """Calculate signal-to-noise ratio"""
        try:
            # Estimate noise from quietest 10% of signal
            sorted_abs = np.sort(np.abs(y))
            noise_threshold_idx = int(0.1 * len(sorted_abs))
            noise_level = np.mean(sorted_abs[:noise_threshold_idx])
            
            # Calculate signal level (RMS of entire signal)
            signal_level = np.sqrt(np.mean(y**2))
            
            if noise_level > 0:
                snr = 20 * np.log10(signal_level / noise_level)
                return float(snr)
            
            return 60.0  # High SNR if no noise detected
            
        except Exception:
            return 30.0  # Default moderate SNR
    
    def _calculate_thd(self, y: np.ndarray, sr: int) -> float:
        """Calculate total harmonic distortion"""
        try:
            # Simplified THD calculation
            # Find fundamental frequency
            fft = np.fft.fft(y)
            freqs = np.fft.fftfreq(len(y), 1/sr)
            
            # Find peak frequency (fundamental)
            positive_freqs = freqs[:len(freqs)//2]
            positive_fft = np.abs(fft[:len(fft)//2])
            
            if len(positive_fft) > 0:
                fundamental_idx = np.argmax(positive_fft)
                fundamental_freq = positive_freqs[fundamental_idx]
                
                if fundamental_freq > 0:
                    # Calculate harmonic content
                    fundamental_power = positive_fft[fundamental_idx]**2
                    total_power = np.sum(positive_fft**2)
                    
                    if total_power > 0:
                        thd = np.sqrt((total_power - fundamental_power) / fundamental_power) * 100
                        return min(float(thd), 50.0)  # Cap at 50%
            
            return 1.0  # Low distortion default
            
        except Exception:
            return 1.0
    
    def _calculate_dynamic_range(self, y: np.ndarray) -> float:
        """Calculate dynamic range"""
        try:
            if len(y) > 0:
                peak_level = np.max(np.abs(y))
                # Use 10th percentile as noise floor
                noise_floor = np.percentile(np.abs(y), 10)
                
                if noise_floor > 0:
                    dynamic_range = 20 * np.log10(peak_level / noise_floor)
                    return float(dynamic_range)
            
            return 40.0  # Default dynamic range
            
        except Exception:
            return 40.0
    
    def _calculate_peak_level(self, y: np.ndarray) -> float:
        """Calculate peak level in dB"""
        try:
            peak = np.max(np.abs(y))
            if peak > 0:
                return float(20 * np.log10(peak))
            return -60.0
            
        except Exception:
            return -20.0
    
    def _calculate_rms_level(self, y: np.ndarray) -> float:
        """Calculate RMS level in dB"""
        try:
            rms = np.sqrt(np.mean(y**2))
            if rms > 0:
                return float(20 * np.log10(rms))
            return -60.0
            
        except Exception:
            return -30.0
    
    def _calculate_spectral_flatness(self, y: np.ndarray) -> float:
        """Calculate spectral flatness"""
        try:
            spectral_flatness = librosa.feature.spectral_flatness(y=y)[0]
            return float(np.mean(spectral_flatness))
            
        except Exception:
            return 0.5
    
    def _calculate_spectral_centroid(self, y: np.ndarray, sr: int) -> float:
        """Calculate spectral centroid"""
        try:
            centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            return float(np.mean(centroid))
            
        except Exception:
            return 2000.0
    
    def _calculate_spectral_bandwidth(self, y: np.ndarray, sr: int) -> float:
        """Calculate spectral bandwidth"""
        try:
            bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
            return float(np.mean(bandwidth))
            
        except Exception:
            return 1000.0
    
    def _calculate_spectral_rolloff(self, y: np.ndarray, sr: int) -> float:
        """Calculate spectral rolloff"""
        try:
            rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            return float(np.mean(rolloff))
            
        except Exception:
            return 4000.0
    
    def _calculate_zcr(self, y: np.ndarray) -> float:
        """Calculate zero crossing rate"""
        try:
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            return float(np.mean(zcr))
            
        except Exception:
            return 0.1
    
    def _calculate_silence_ratio(self, y: np.ndarray, threshold_db: float = -40.0) -> float:
        """Calculate ratio of silence to total duration"""
        try:
            # Convert to dB
            y_db = 20 * np.log10(np.abs(y) + 1e-10)
            
            # Count silent samples
            silent_samples = np.sum(y_db < threshold_db)
            silence_ratio = silent_samples / len(y)
            
            return float(silence_ratio)
            
        except Exception:
            return 0.1
    
    def _calculate_clipping_ratio(self, y: np.ndarray, threshold: float = 0.95) -> float:
        """Calculate ratio of clipped samples"""
        try:
            clipped_samples = np.sum(np.abs(y) >= threshold)
            clipping_ratio = clipped_samples / len(y)
            
            return float(clipping_ratio)
            
        except Exception:
            return 0.0
    
    def _calculate_loudness(self, y: np.ndarray, sr: int) -> float:
        """Calculate loudness in LUFS (simplified)"""
        try:
            # Simplified loudness calculation
            rms = np.sqrt(np.mean(y**2))
            if rms > 0:
                # Approximate LUFS conversion
                lufs = -0.691 + 10 * np.log10(rms**2)
                return float(lufs)
            
            return -50.0
            
        except Exception:
            return -23.0
    
    def _calculate_perceived_quality(self, metrics: AudioQualityMetrics) -> float:
        """Calculate overall perceived quality score (0-100)"""
        try:
            # Weighted combination of metrics
            snr_score = min(100, max(0, (metrics.snr_db + 10) * 2))  # SNR contribution
            dynamic_range_score = min(100, max(0, metrics.dynamic_range_db * 2))  # Dynamic range
            distortion_score = max(0, 100 - metrics.thd_percent * 10)  # THD penalty
            clipping_score = max(0, 100 - metrics.clipping_ratio * 1000)  # Clipping penalty
            
            # Combine scores
            quality_score = (
                snr_score * 0.3 +
                dynamic_range_score * 0.25 +
                distortion_score * 0.25 +
                clipping_score * 0.2
            )
            
            return float(min(100, max(0, quality_score)))
            
        except Exception:
            return 70.0
    
    def _determine_enhancement_needs(self, metrics: AudioQualityMetrics):
        """Determine what enhancements are needed"""
        try:
            # Noise reduction needed if SNR is low
            metrics.needs_noise_reduction = metrics.snr_db < 20.0
            
            # Normalization needed if levels are too low or too high
            metrics.needs_normalization = (
                metrics.peak_level_db < -10.0 or 
                metrics.peak_level_db > -1.0 or
                metrics.rms_level_db < -30.0
            )
            
            # Gain adjustment needed if loudness is off target
            metrics.needs_gain_adjustment = abs(metrics.loudness_lufs - (-23.0)) > 3.0
            
            # Repair needed if significant clipping or distortion
            metrics.needs_repair = (
                metrics.clipping_ratio > 0.01 or 
                metrics.thd_percent > 5.0
            )
            
        except Exception as e:
            logger.error(f"Error determining enhancement needs: {e}")
    
    def _determine_quality_rating(self, metrics: AudioQualityMetrics) -> str:
        """Determine overall quality rating"""
        try:
            score = metrics.perceived_quality_score
            
            if score >= 85:
                return "excellent"
            elif score >= 70:
                return "good"
            elif score >= 50:
                return "fair"
            else:
                return "poor"
                
        except Exception:
            return "fair"
    
    def _default_quality_metrics(self) -> AudioQualityMetrics:
        """Return default quality metrics in case of error"""
        return AudioQualityMetrics(
            snr_db=30.0, thd_percent=1.0, dynamic_range_db=40.0,
            peak_level_db=-6.0, rms_level_db=-20.0, spectral_flatness=0.5,
            spectral_centroid_hz=2000.0, spectral_bandwidth_hz=1000.0,
            spectral_rolloff_hz=4000.0, zero_crossing_rate=0.1,
            silence_ratio=0.1, clipping_ratio=0.0, loudness_lufs=-23.0,
            perceived_quality_score=70.0, needs_noise_reduction=False,
            needs_normalization=False, needs_gain_adjustment=False,
            needs_repair=False, quality_rating="good"
        )class A
udioRepairer:
    """Audio repair system for corrupted segments"""
    
    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
    
    def repair_audio(self, audio_path: str, output_path: str = None) -> AudioRepairResult:
        """Detect and repair corrupted audio segments"""
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            duration = len(y) / sr
            
            # Detect corrupted segments
            corrupted_segments = self._detect_corrupted_segments(y, sr)
            
            # Repair corrupted segments
            repaired_audio, repair_methods = self._repair_segments(y, corrupted_segments)
            
            # Calculate repair statistics
            repaired_duration = sum(end - start for start, end in corrupted_segments)
            success_rate = min(1.0, len(repair_methods) / max(1, len(corrupted_segments)))
            
            # Save repaired audio if output path provided
            if output_path:
                sf.write(output_path, repaired_audio, sr)
            
            return AudioRepairResult(
                corrupted_segments=corrupted_segments,
                repair_methods_used=repair_methods,
                repair_success_rate=success_rate,
                repaired_duration=repaired_duration,
                total_duration=duration
            )
            
        except Exception as e:
            logger.error(f"Error in audio repair: {e}")
            return AudioRepairResult([], [], 0.0, 0.0, 0.0)
    
    def _detect_corrupted_segments(self, y: np.ndarray, sr: int) -> List[Tuple[float, float]]:
        """Detect corrupted audio segments"""
        try:
            corrupted_segments = []
            
            # Detect clipping
            clipping_segments = self._detect_clipping(y, sr)
            corrupted_segments.extend(clipping_segments)
            
            # Detect dropouts (silence in unexpected places)
            dropout_segments = self._detect_dropouts(y, sr)
            corrupted_segments.extend(dropout_segments)
            
            # Detect artifacts using anomaly detection
            artifact_segments = self._detect_artifacts(y, sr)
            corrupted_segments.extend(artifact_segments)
            
            # Merge overlapping segments
            merged_segments = self._merge_segments(corrupted_segments)
            
            return merged_segments
            
        except Exception as e:
            logger.error(f"Error detecting corrupted segments: {e}")
            return []
    
    def _detect_clipping(self, y: np.ndarray, sr: int, threshold: float = 0.95) -> List[Tuple[float, float]]:
        """Detect clipped audio segments"""
        try:
            clipped_mask = np.abs(y) >= threshold
            
            # Find continuous clipped regions
            clipped_segments = []
            in_clipped_region = False
            start_idx = 0
            
            for i, is_clipped in enumerate(clipped_mask):
                if is_clipped and not in_clipped_region:
                    start_idx = i
                    in_clipped_region = True
                elif not is_clipped and in_clipped_region:
                    # End of clipped region
                    start_time = start_idx / sr
                    end_time = i / sr
                    if end_time - start_time > 0.01:  # Minimum 10ms
                        clipped_segments.append((start_time, end_time))
                    in_clipped_region = False
            
            return clipped_segments
            
        except Exception:
            return []
    
    def _detect_dropouts(self, y: np.ndarray, sr: int, silence_threshold: float = -50.0) -> List[Tuple[float, float]]:
        """Detect audio dropouts (unexpected silence)"""
        try:
            # Convert to dB
            y_db = 20 * np.log10(np.abs(y) + 1e-10)
            
            # Find silent regions
            silent_mask = y_db < silence_threshold
            
            # Find continuous silent regions
            dropout_segments = []
            in_silent_region = False
            start_idx = 0
            
            for i, is_silent in enumerate(silent_mask):
                if is_silent and not in_silent_region:
                    start_idx = i
                    in_silent_region = True
                elif not is_silent and in_silent_region:
                    # End of silent region
                    start_time = start_idx / sr
                    end_time = i / sr
                    # Only consider dropouts longer than 50ms but shorter than 2s
                    if 0.05 < (end_time - start_time) < 2.0:
                        dropout_segments.append((start_time, end_time))
                    in_silent_region = False
            
            return dropout_segments
            
        except Exception:
            return []
    
    def _detect_artifacts(self, y: np.ndarray, sr: int) -> List[Tuple[float, float]]:
        """Detect audio artifacts using anomaly detection"""
        try:
            # Extract features for anomaly detection
            frame_length = int(0.1 * sr)  # 100ms frames
            hop_length = frame_length // 2
            
            features = []
            for i in range(0, len(y) - frame_length, hop_length):
                frame = y[i:i + frame_length]
                
                # Extract features
                rms = np.sqrt(np.mean(frame**2))
                zcr = np.mean(np.abs(np.diff(np.sign(frame))))
                spectral_centroid = np.mean(np.abs(np.fft.fft(frame)))
                
                features.append([rms, zcr, spectral_centroid])
            
            if len(features) < 10:  # Need minimum samples for anomaly detection
                return []
            
            features = np.array(features)
            
            # Detect anomalies
            anomalies = self.anomaly_detector.fit_predict(features)
            
            # Convert anomaly indices to time segments
            artifact_segments = []
            for i, is_anomaly in enumerate(anomalies):
                if is_anomaly == -1:  # Anomaly detected
                    start_time = i * hop_length / sr
                    end_time = (i * hop_length + frame_length) / sr
                    artifact_segments.append((start_time, end_time))
            
            return artifact_segments
            
        except Exception:
            return []
    
    def _merge_segments(self, segments: List[Tuple[float, float]], 
                       merge_threshold: float = 0.1) -> List[Tuple[float, float]]:
        """Merge overlapping or nearby segments"""
        try:
            if not segments:
                return []
            
            # Sort segments by start time
            sorted_segments = sorted(segments)
            merged = [sorted_segments[0]]
            
            for current in sorted_segments[1:]:
                last = merged[-1]
                
                # Check if segments overlap or are close
                if current[0] <= last[1] + merge_threshold:
                    # Merge segments
                    merged[-1] = (last[0], max(last[1], current[1]))
                else:
                    merged.append(current)
            
            return merged
            
        except Exception:
            return segments
    
    def _repair_segments(self, y: np.ndarray, corrupted_segments: List[Tuple[float, float]]) -> Tuple[np.ndarray, List[str]]:
        """Repair corrupted audio segments"""
        try:
            repaired_audio = y.copy()
            repair_methods = []
            sr = self.sample_rate
            
            for start_time, end_time in corrupted_segments:
                start_idx = int(start_time * sr)
                end_idx = int(end_time * sr)
                
                if start_idx >= len(y) or end_idx >= len(y):
                    continue
                
                # Choose repair method based on segment characteristics
                segment_length = end_idx - start_idx
                
                if segment_length < sr * 0.05:  # Short segments (< 50ms)
                    # Use interpolation
                    repaired_audio[start_idx:end_idx] = self._interpolate_segment(
                        repaired_audio, start_idx, end_idx
                    )
                    repair_methods.append("interpolation")
                    
                elif segment_length < sr * 0.5:  # Medium segments (< 500ms)
                    # Use autoregressive prediction
                    repaired_audio[start_idx:end_idx] = self._predict_segment(
                        repaired_audio, start_idx, end_idx
                    )
                    repair_methods.append("prediction")
                    
                else:  # Long segments
                    # Use noise substitution
                    repaired_audio[start_idx:end_idx] = self._substitute_noise(
                        repaired_audio, start_idx, end_idx
                    )
                    repair_methods.append("noise_substitution")
            
            return repaired_audio, repair_methods
            
        except Exception as e:
            logger.error(f"Error repairing segments: {e}")
            return y, []
    
    def _interpolate_segment(self, y: np.ndarray, start_idx: int, end_idx: int) -> np.ndarray:
        """Repair segment using linear interpolation"""
        try:
            if start_idx > 0 and end_idx < len(y):
                # Linear interpolation between boundaries
                start_val = y[start_idx - 1]
                end_val = y[end_idx]
                
                interpolated = np.linspace(start_val, end_val, end_idx - start_idx)
                return interpolated
            else:
                # Fill with zeros if at boundaries
                return np.zeros(end_idx - start_idx)
                
        except Exception:
            return np.zeros(end_idx - start_idx)
    
    def _predict_segment(self, y: np.ndarray, start_idx: int, end_idx: int) -> np.ndarray:
        """Repair segment using autoregressive prediction"""
        try:
            # Use previous samples for prediction
            context_length = min(1024, start_idx)
            
            if context_length > 10:
                context = y[start_idx - context_length:start_idx]
                
                # Simple AR prediction using linear prediction
                predicted = np.zeros(end_idx - start_idx)
                
                # Use last few samples to predict next samples
                for i in range(len(predicted)):
                    if i < 10:
                        # Use context for first few samples
                        predicted[i] = context[-(10-i)] if (10-i) <= len(context) else 0
                    else:
                        # Use predicted samples for continuation
                        predicted[i] = np.mean(predicted[max(0, i-5):i])
                
                return predicted
            else:
                return np.zeros(end_idx - start_idx)
                
        except Exception:
            return np.zeros(end_idx - start_idx)
    
    def _substitute_noise(self, y: np.ndarray, start_idx: int, end_idx: int) -> np.ndarray:
        """Repair segment by substituting with appropriate noise"""
        try:
            # Estimate noise characteristics from surrounding audio
            context_length = min(2048, start_idx, len(y) - end_idx)
            
            if context_length > 100:
                # Get noise samples from before and after
                before_context = y[max(0, start_idx - context_length):start_idx]
                after_context = y[end_idx:min(len(y), end_idx + context_length)]
                
                # Estimate noise level
                noise_level = np.std(np.concatenate([before_context, after_context]))
                
                # Generate noise with similar characteristics
                noise = np.random.normal(0, noise_level, end_idx - start_idx)
                
                # Apply envelope to make transition smooth
                envelope_length = min(100, len(noise) // 4)
                if envelope_length > 0:
                    fade_in = np.linspace(0, 1, envelope_length)
                    fade_out = np.linspace(1, 0, envelope_length)
                    
                    noise[:envelope_length] *= fade_in
                    noise[-envelope_length:] *= fade_out
                
                return noise
            else:
                return np.zeros(end_idx - start_idx)
                
        except Exception:
            return np.zeros(end_idx - start_idx)

class FormatOptimizer:
    """Audio format optimization recommendations"""
    
    def __init__(self):
        self.format_specs = {
            'speech': {
                'sample_rate': 16000,
                'bit_depth': 16,
                'channels': 1,
                'codec': 'opus',
                'bitrate': 32000
            },
            'music': {
                'sample_rate': 44100,
                'bit_depth': 24,
                'channels': 2,
                'codec': 'flac',
                'bitrate': None  # Lossless
            },
            'podcast': {
                'sample_rate': 22050,
                'bit_depth': 16,
                'channels': 1,
                'codec': 'mp3',
                'bitrate': 128000
            },
            'broadcast': {
                'sample_rate': 48000,
                'bit_depth': 24,
                'channels': 2,
                'codec': 'wav',
                'bitrate': None  # Uncompressed
            }
        }
    
    def recommend_format(self, audio_path: str, use_case: str = 'general') -> Dict[str, Any]:
        """Recommend optimal audio format based on content and use case"""
        try:
            # Analyze audio characteristics
            y, sr = librosa.load(audio_path, sr=None)
            
            # Get audio info
            duration = len(y) / sr
            channels = 1 if y.ndim == 1 else y.shape[0]
            current_sample_rate = sr
            
            # Analyze content type
            content_type = self._analyze_content_type(y, sr)
            
            # Get format recommendation
            if use_case in self.format_specs:
                recommended = self.format_specs[use_case].copy()
            else:
                recommended = self.format_specs[content_type].copy()
            
            # Calculate file size estimates
            current_size = self._estimate_file_size(duration, current_sample_rate, channels, 16, 'wav')
            recommended_size = self._estimate_file_size(
                duration, 
                recommended['sample_rate'], 
                recommended['channels'],
                recommended['bit_depth'],
                recommended['codec']
            )
            
            return {
                'current_format': {
                    'sample_rate': current_sample_rate,
                    'channels': channels,
                    'duration': duration,
                    'estimated_size_mb': current_size
                },
                'recommended_format': recommended,
                'estimated_size_mb': recommended_size,
                'size_reduction_percent': ((current_size - recommended_size) / current_size) * 100 if current_size > 0 else 0,
                'content_type': content_type,
                'optimization_benefits': self._get_optimization_benefits(recommended, content_type)
            }
            
        except Exception as e:
            logger.error(f"Error in format optimization: {e}")
            return {}
    
    def _analyze_content_type(self, y: np.ndarray, sr: int) -> str:
        """Analyze audio to determine content type"""
        try:
            # Extract features for content classification
            
            # Spectral features
            spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
            spectral_bandwidth = np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))
            spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))
            
            # Temporal features
            zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(y))
            
            # Energy features
            rms_energy = np.mean(librosa.feature.rms(y=y))
            
            # Simple heuristic classification
            if spectral_centroid < 2000 and zero_crossing_rate < 0.1:
                return 'speech'
            elif spectral_bandwidth > 3000 and rms_energy > 0.1:
                return 'music'
            elif spectral_centroid < 3000:
                return 'podcast'
            else:
                return 'broadcast'
                
        except Exception:
            return 'general'
    
    def _estimate_file_size(self, duration: float, sample_rate: int, channels: int, 
                           bit_depth: int, codec: str) -> float:
        """Estimate file size in MB"""
        try:
            if codec in ['wav', 'flac']:
                # Uncompressed or lossless
                bits_per_second = sample_rate * channels * bit_depth
                bytes_per_second = bits_per_second / 8
                total_bytes = bytes_per_second * duration
                
                if codec == 'flac':
                    total_bytes *= 0.6  # Typical FLAC compression ratio
                    
            elif codec == 'mp3':
                # Assume 128 kbps for MP3
                bits_per_second = 128000
                total_bytes = (bits_per_second / 8) * duration
                
            elif codec == 'opus':
                # Assume 64 kbps for Opus
                bits_per_second = 64000
                total_bytes = (bits_per_second / 8) * duration
                
            else:
                # Default to uncompressed
                bits_per_second = sample_rate * channels * bit_depth
                total_bytes = (bits_per_second / 8) * duration
            
            return total_bytes / (1024 * 1024)  # Convert to MB
            
        except Exception:
            return 0.0
    
    def _get_optimization_benefits(self, format_spec: Dict[str, Any], content_type: str) -> List[str]:
        """Get list of optimization benefits"""
        benefits = []
        
        if format_spec['codec'] in ['opus', 'mp3']:
            benefits.append("Reduced file size through compression")
        
        if format_spec['sample_rate'] <= 22050 and content_type == 'speech':
            benefits.append("Optimized sample rate for speech content")
        
        if format_spec['channels'] == 1 and content_type in ['speech', 'podcast']:
            benefits.append("Mono encoding suitable for voice content")
        
        if format_spec['codec'] == 'opus':
            benefits.append("Superior compression efficiency")
            benefits.append("Low latency encoding")
        
        if format_spec['codec'] == 'flac':
            benefits.append("Lossless compression preserves quality")
        
        return benefits