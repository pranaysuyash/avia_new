"""
Comprehensive Audio Enhancement Pipeline
Task 117: Build comprehensive audio enhancement pipeline

This module implements advanced audio enhancement capabilities including:
- Noise reduction using noisereduce library
- Audio normalization and gain control
- Automatic audio quality assessment
- Audio repair for corrupted segments
- Audio format optimization recommendations

Requirements: 1.1, 2.1
Tools: noisereduce, pydub, librosa, scipy
"""

import os
import logging
import numpy as np
import librosa
import soundfile as sf
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import tempfile
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

try:
    import noisereduce as nr
    NOISEREDUCE_AVAILABLE = True
except ImportError:
    NOISEREDUCE_AVAILABLE = False
    logging.warning("noisereduce library not available. Noise reduction will be limited.")

try:
    from pydub import AudioSegment
    from pydub.effects import normalize, compress_dynamic_range
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logging.warning("pydub library not available. Some audio processing features will be limited.")

from scipy import signal
from scipy.stats import entropy
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AudioQualityMetrics:
    """Comprehensive audio quality assessment metrics"""
    snr_db: float  # Signal-to-noise ratio in dB
    thd_percent: float  # Total harmonic distortion
    dynamic_range_db: float  # Dynamic range
    spectral_centroid: float  # Spectral centroid (brightness)
    spectral_rolloff: float  # Spectral rolloff frequency
    zero_crossing_rate: float  # Zero crossing rate
    rms_energy: float  # RMS energy level
    peak_level_db: float  # Peak level in dB
    loudness_lufs: float  # Loudness in LUFS
    quality_score: float  # Overall quality score (0-100)
    recommendations: List[str]  # Enhancement recommendations

@dataclass
class EnhancementResult:
    """Result of audio enhancement processing"""
    enhanced_audio_path: str
    original_metrics: AudioQualityMetrics
    enhanced_metrics: AudioQualityMetrics
    processing_time: float
    enhancement_applied: List[str]
    improvement_score: float
    metadata: Dict[str, Any]

class AudioEnhancementPipeline:
    """Comprehensive audio enhancement pipeline with advanced processing capabilities"""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize the audio enhancement pipeline
        
        Args:
            temp_dir: Directory for temporary files (optional)
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.supported_formats = ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac']
        
        # Enhancement parameters
        self.noise_reduction_params = {
            'stationary': True,
            'prop_decrease': 1.0,
            'n_grad_freq': 2,
            'n_grad_time': 4,
            'n_fft': 2048,
            'win_length': 2048,
            'hop_length': 512
        }
        
        self.normalization_params = {
            'target_lufs': -23.0,  # EBU R128 standard
            'max_peak_db': -1.0,
            'dynamic_range_target': 20.0
        }
        
        logger.info("Audio Enhancement Pipeline initialized")
    
    def enhance_audio(self, input_path: str, output_path: Optional[str] = None, 
                     enhancement_options: Optional[Dict[str, Any]] = None) -> EnhancementResult:
        """
        Apply comprehensive audio enhancement to input file
        
        Args:
            input_path: Path to input audio file
            output_path: Path for enhanced output (optional)
            enhancement_options: Custom enhancement parameters
            
        Returns:
            EnhancementResult with processing details and metrics
        """
        import time
        start_time = time.time()
        
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input audio file not found: {input_path}")
        
        # Generate output path if not provided
        if output_path is None:
            input_path_obj = Path(input_path)
            output_path = str(input_path_obj.parent / f"{input_path_obj.stem}_enhanced{input_path_obj.suffix}")
        
        logger.info(f"Starting audio enhancement: {input_path}")
        
        # Load audio file
        try:
            audio_data, sample_rate = librosa.load(input_path, sr=None, mono=False)
            if audio_data.ndim == 1:
                audio_data = audio_data.reshape(1, -1)
        except Exception as e:
            raise ValueError(f"Failed to load audio file: {str(e)}")
        
        # Assess original audio quality
        original_metrics = self._assess_audio_quality(audio_data, sample_rate)
        logger.info(f"Original audio quality score: {original_metrics.quality_score:.1f}/100")
        
        # Apply enhancement pipeline
        enhanced_audio = audio_data.copy()
        enhancement_applied = []
        
        # Merge enhancement options
        options = enhancement_options or {}
        
        # 1. Noise Reduction
        if options.get('noise_reduction', True) and NOISEREDUCE_AVAILABLE:
            enhanced_audio = self._apply_noise_reduction(enhanced_audio, sample_rate)
            enhancement_applied.append("noise_reduction")
            logger.info("Applied noise reduction")
        
        # 2. Audio Repair (detect and fix corrupted segments)
        if options.get('audio_repair', True):
            enhanced_audio = self._repair_audio_segments(enhanced_audio, sample_rate)
            enhancement_applied.append("audio_repair")
            logger.info("Applied audio repair")
        
        # 3. Spectral Enhancement
        if options.get('spectral_enhancement', True):
            enhanced_audio = self._apply_spectral_enhancement(enhanced_audio, sample_rate)
            enhancement_applied.append("spectral_enhancement")
            logger.info("Applied spectral enhancement")
        
        # 4. Dynamic Range Processing
        if options.get('dynamic_processing', True):
            enhanced_audio = self._apply_dynamic_processing(enhanced_audio, sample_rate)
            enhancement_applied.append("dynamic_processing")
            logger.info("Applied dynamic range processing")
        
        # 5. Audio Normalization
        if options.get('normalization', True):
            enhanced_audio = self._apply_normalization(enhanced_audio, sample_rate)
            enhancement_applied.append("normalization")
            logger.info("Applied audio normalization")
        
        # Save enhanced audio
        try:
            if enhanced_audio.shape[0] == 1:
                sf.write(output_path, enhanced_audio[0], sample_rate)
            else:
                sf.write(output_path, enhanced_audio.T, sample_rate)
        except Exception as e:
            raise ValueError(f"Failed to save enhanced audio: {str(e)}")
        
        # Assess enhanced audio quality
        enhanced_metrics = self._assess_audio_quality(enhanced_audio, sample_rate)
        
        # Calculate improvement score
        improvement_score = enhanced_metrics.quality_score - original_metrics.quality_score
        
        processing_time = time.time() - start_time
        
        logger.info(f"Enhancement completed in {processing_time:.2f}s")
        logger.info(f"Enhanced audio quality score: {enhanced_metrics.quality_score:.1f}/100")
        logger.info(f"Improvement: {improvement_score:+.1f} points")
        
        return EnhancementResult(
            enhanced_audio_path=output_path,
            original_metrics=original_metrics,
            enhanced_metrics=enhanced_metrics,
            processing_time=processing_time,
            enhancement_applied=enhancement_applied,
            improvement_score=improvement_score,
            metadata={
                'sample_rate': sample_rate,
                'channels': enhanced_audio.shape[0],
                'duration': enhanced_audio.shape[1] / sample_rate,
                'enhancement_options': options
            }
        )
    
    def _apply_noise_reduction(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply advanced noise reduction using multiple techniques"""
        enhanced_channels = []
        
        for channel_idx in range(audio_data.shape[0]):
            channel_data = audio_data[channel_idx]
            
            try:
                # Apply noisereduce if available
                if NOISEREDUCE_AVAILABLE:
                    # Stationary noise reduction
                    reduced_stationary = nr.reduce_noise(
                        y=channel_data,
                        sr=sample_rate,
                        **self.noise_reduction_params
                    )
                    
                    # Non-stationary noise reduction for more complex noise
                    reduced_nonstationary = nr.reduce_noise(
                        y=reduced_stationary,
                        sr=sample_rate,
                        stationary=False,
                        prop_decrease=0.8
                    )
                    
                    enhanced_channel = reduced_nonstationary
                else:
                    # Fallback: Simple spectral subtraction
                    enhanced_channel = self._spectral_subtraction(channel_data, sample_rate)
                
                enhanced_channels.append(enhanced_channel)
                
            except Exception as e:
                logger.warning(f"Noise reduction failed for channel {channel_idx}: {str(e)}")
                enhanced_channels.append(channel_data)
        
        return np.array(enhanced_channels)
    
    def _spectral_subtraction(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Fallback noise reduction using spectral subtraction"""
        # Compute STFT
        stft = librosa.stft(audio_data, n_fft=2048, hop_length=512)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Estimate noise from first 0.5 seconds
        noise_frames = int(0.5 * sample_rate / 512)
        noise_spectrum = np.mean(magnitude[:, :noise_frames], axis=1, keepdims=True)
        
        # Apply spectral subtraction
        alpha = 2.0  # Over-subtraction factor
        enhanced_magnitude = magnitude - alpha * noise_spectrum
        
        # Ensure non-negative values
        enhanced_magnitude = np.maximum(enhanced_magnitude, 0.1 * magnitude)
        
        # Reconstruct audio
        enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
        enhanced_audio = librosa.istft(enhanced_stft, hop_length=512)
        
        return enhanced_audio
    
    def _repair_audio_segments(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Detect and repair corrupted or problematic audio segments"""
        enhanced_channels = []
        
        for channel_idx in range(audio_data.shape[0]):
            channel_data = audio_data[channel_idx]
            
            # Detect problematic segments
            problematic_segments = self._detect_problematic_segments(channel_data, sample_rate)
            
            if problematic_segments:
                logger.info(f"Found {len(problematic_segments)} problematic segments in channel {channel_idx}")
                channel_data = self._fix_problematic_segments(channel_data, problematic_segments, sample_rate)
            
            enhanced_channels.append(channel_data)
        
        return np.array(enhanced_channels)
    
    def _detect_problematic_segments(self, audio_data: np.ndarray, sample_rate: int) -> List[Tuple[int, int]]:
        """Detect segments with clipping, dropouts, or other issues"""
        problematic_segments = []
        
        # Parameters
        frame_size = int(0.1 * sample_rate)  # 100ms frames
        hop_size = frame_size // 2
        
        # Detect clipping (values at or near maximum)
        clipping_threshold = 0.95
        clipped_samples = np.abs(audio_data) >= clipping_threshold
        
        # Detect dropouts (sudden amplitude drops)
        rms_frames = []
        for i in range(0, len(audio_data) - frame_size, hop_size):
            frame = audio_data[i:i + frame_size]
            rms_frames.append(np.sqrt(np.mean(frame**2)))
        
        rms_frames = np.array(rms_frames)
        median_rms = np.median(rms_frames)
        dropout_threshold = median_rms * 0.1
        
        # Find problematic regions
        for i in range(len(rms_frames)):
            start_sample = i * hop_size
            end_sample = min(start_sample + frame_size, len(audio_data))
            
            frame_clipped = np.any(clipped_samples[start_sample:end_sample])
            frame_dropout = rms_frames[i] < dropout_threshold
            
            if frame_clipped or frame_dropout:
                problematic_segments.append((start_sample, end_sample))
        
        # Merge overlapping segments
        if problematic_segments:
            merged_segments = [problematic_segments[0]]
            for start, end in problematic_segments[1:]:
                if start <= merged_segments[-1][1]:
                    merged_segments[-1] = (merged_segments[-1][0], max(merged_segments[-1][1], end))
                else:
                    merged_segments.append((start, end))
            problematic_segments = merged_segments
        
        return problematic_segments
    
    def _fix_problematic_segments(self, audio_data: np.ndarray, segments: List[Tuple[int, int]], 
                                sample_rate: int) -> np.ndarray:
        """Fix problematic audio segments using interpolation and filtering"""
        fixed_audio = audio_data.copy()
        
        for start, end in segments:
            segment_length = end - start
            
            if segment_length < sample_rate * 0.01:  # Very short segments (< 10ms)
                # Linear interpolation
                if start > 0 and end < len(fixed_audio):
                    start_val = fixed_audio[start - 1]
                    end_val = fixed_audio[end]
                    fixed_audio[start:end] = np.linspace(start_val, end_val, segment_length)
            
            else:  # Longer segments
                # Use surrounding context for reconstruction
                context_size = min(segment_length, sample_rate // 10)  # Max 100ms context
                
                if start >= context_size and end + context_size < len(fixed_audio):
                    # Extract context before and after
                    before_context = fixed_audio[start - context_size:start]
                    after_context = fixed_audio[end:end + context_size]
                    
                    # Create smooth transition
                    transition = self._create_smooth_transition(before_context, after_context, segment_length)
                    fixed_audio[start:end] = transition
                
                else:
                    # Fallback: Apply gentle low-pass filter to reduce artifacts
                    nyquist = sample_rate / 2
                    cutoff = min(4000, nyquist * 0.8)  # 4kHz or 80% of Nyquist
                    b, a = signal.butter(4, cutoff / nyquist, btype='low')
                    fixed_audio[start:end] = signal.filtfilt(b, a, fixed_audio[start:end])
        
        return fixed_audio
    
    def _create_smooth_transition(self, before_context: np.ndarray, after_context: np.ndarray, 
                                length: int) -> np.ndarray:
        """Create smooth transition between audio segments"""
        # Use autoregressive prediction for natural-sounding interpolation
        try:
            # Simple approach: weighted combination with fade
            fade_length = min(length // 4, len(before_context), len(after_context))
            
            transition = np.zeros(length)
            
            # Fade out from before context
            if fade_length > 0:
                fade_out = before_context[-fade_length:] * np.linspace(1, 0, fade_length)
                transition[:fade_length] += fade_out
            
            # Fade in to after context
            if fade_length > 0:
                fade_in = after_context[:fade_length] * np.linspace(0, 1, fade_length)
                transition[-fade_length:] += fade_in
            
            # Fill middle with interpolated values
            if length > 2 * fade_length:
                middle_start = fade_length
                middle_end = length - fade_length
                start_val = before_context[-1] if len(before_context) > 0 else 0
                end_val = after_context[0] if len(after_context) > 0 else 0
                transition[middle_start:middle_end] = np.linspace(start_val, end_val, middle_end - middle_start)
            
            return transition
            
        except Exception as e:
            logger.warning(f"Transition creation failed: {str(e)}")
            # Fallback: simple linear interpolation
            start_val = before_context[-1] if len(before_context) > 0 else 0
            end_val = after_context[0] if len(after_context) > 0 else 0
            return np.linspace(start_val, end_val, length)
    
    def _apply_spectral_enhancement(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply spectral enhancement to improve clarity and presence"""
        enhanced_channels = []
        
        for channel_idx in range(audio_data.shape[0]):
            channel_data = audio_data[channel_idx]
            
            # Apply multi-band enhancement
            enhanced_channel = self._multiband_enhancement(channel_data, sample_rate)
            enhanced_channels.append(enhanced_channel)
        
        return np.array(enhanced_channels)
    
    def _multiband_enhancement(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply frequency-specific enhancements"""
        # Define frequency bands for enhancement
        nyquist = sample_rate / 2
        
        # Band definitions: (low_freq, high_freq, gain_db)
        enhancement_bands = [
            (80, 250, -2.0),      # Reduce low-frequency rumble
            (250, 1000, 1.0),     # Slight boost for warmth
            (1000, 4000, 2.0),    # Boost presence/clarity
            (4000, 8000, 1.5),    # Enhance brilliance
            (8000, nyquist, 0.5)  # Gentle high-frequency enhancement
        ]
        
        enhanced_audio = audio_data.copy()
        
        for low_freq, high_freq, gain_db in enhancement_bands:
            if high_freq > nyquist:
                high_freq = nyquist * 0.95
            
            if low_freq >= high_freq:
                continue
            
            try:
                # Design bandpass filter
                low_norm = low_freq / nyquist
                high_norm = high_freq / nyquist
                
                if low_norm <= 0:
                    # High-pass filter
                    b, a = signal.butter(4, high_norm, btype='high')
                elif high_norm >= 1:
                    # Low-pass filter
                    b, a = signal.butter(4, low_norm, btype='low')
                else:
                    # Band-pass filter
                    b, a = signal.butter(4, [low_norm, high_norm], btype='band')
                
                # Extract band
                band_signal = signal.filtfilt(b, a, audio_data)
                
                # Apply gain
                gain_linear = 10**(gain_db / 20)
                band_signal *= gain_linear
                
                # Add back to enhanced audio
                enhanced_audio += band_signal * 0.2  # Gentle blending
                
            except Exception as e:
                logger.warning(f"Band enhancement failed for {low_freq}-{high_freq}Hz: {str(e)}")
        
        return enhanced_audio
    
    def _apply_dynamic_processing(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply dynamic range processing (compression/expansion)"""
        enhanced_channels = []
        
        for channel_idx in range(audio_data.shape[0]):
            channel_data = audio_data[channel_idx]
            
            # Apply gentle compression to control dynamics
            compressed_channel = self._apply_compression(channel_data, sample_rate)
            enhanced_channels.append(compressed_channel)
        
        return np.array(enhanced_channels)
    
    def _apply_compression(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply dynamic range compression"""
        # Parameters for gentle compression
        threshold_db = -20.0  # Compression threshold
        ratio = 3.0          # Compression ratio
        attack_time = 0.003  # 3ms attack
        release_time = 0.1   # 100ms release
        
        # Convert to dB
        audio_db = 20 * np.log10(np.abs(audio_data) + 1e-10)
        
        # Calculate gain reduction
        gain_reduction_db = np.zeros_like(audio_db)
        mask = audio_db > threshold_db
        gain_reduction_db[mask] = (audio_db[mask] - threshold_db) * (1 - 1/ratio)
        
        # Apply smoothing (attack/release)
        smoothed_gain_reduction = self._apply_attack_release(
            gain_reduction_db, sample_rate, attack_time, release_time
        )
        
        # Apply gain reduction
        gain_linear = 10**(-smoothed_gain_reduction / 20)
        compressed_audio = audio_data * gain_linear
        
        return compressed_audio
    
    def _apply_attack_release(self, gain_reduction_db: np.ndarray, sample_rate: int, 
                            attack_time: float, release_time: float) -> np.ndarray:
        """Apply attack and release smoothing to gain reduction"""
        attack_coeff = np.exp(-1 / (attack_time * sample_rate))
        release_coeff = np.exp(-1 / (release_time * sample_rate))
        
        smoothed = np.zeros_like(gain_reduction_db)
        smoothed[0] = gain_reduction_db[0]
        
        for i in range(1, len(gain_reduction_db)):
            if gain_reduction_db[i] > smoothed[i-1]:
                # Attack (faster)
                smoothed[i] = attack_coeff * smoothed[i-1] + (1 - attack_coeff) * gain_reduction_db[i]
            else:
                # Release (slower)
                smoothed[i] = release_coeff * smoothed[i-1] + (1 - release_coeff) * gain_reduction_db[i]
        
        return smoothed
    
    def _apply_normalization(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply intelligent audio normalization"""
        enhanced_channels = []
        
        for channel_idx in range(audio_data.shape[0]):
            channel_data = audio_data[channel_idx]
            
            # Calculate current levels
            rms_level = np.sqrt(np.mean(channel_data**2))
            peak_level = np.max(np.abs(channel_data))
            
            # Target levels
            target_rms_db = -20.0  # Target RMS level
            max_peak_db = self.normalization_params['max_peak_db']
            
            # Calculate required gain
            current_rms_db = 20 * np.log10(rms_level + 1e-10)
            rms_gain_db = target_rms_db - current_rms_db
            
            current_peak_db = 20 * np.log10(peak_level + 1e-10)
            peak_gain_db = max_peak_db - current_peak_db
            
            # Use the more conservative gain
            final_gain_db = min(rms_gain_db, peak_gain_db)
            final_gain_linear = 10**(final_gain_db / 20)
            
            # Apply normalization
            normalized_channel = channel_data * final_gain_linear
            
            # Ensure no clipping
            if np.max(np.abs(normalized_channel)) > 0.99:
                normalized_channel *= 0.99 / np.max(np.abs(normalized_channel))
            
            enhanced_channels.append(normalized_channel)
        
        return np.array(enhanced_channels)
    
    def _assess_audio_quality(self, audio_data: np.ndarray, sample_rate: int) -> AudioQualityMetrics:
        """Comprehensive audio quality assessment"""
        # Use first channel for analysis if stereo
        if audio_data.ndim > 1:
            analysis_channel = audio_data[0]
        else:
            analysis_channel = audio_data
        
        # Calculate various quality metrics
        metrics = {}
        
        # 1. Signal-to-Noise Ratio (SNR)
        metrics['snr_db'] = self._calculate_snr(analysis_channel, sample_rate)
        
        # 2. Total Harmonic Distortion (THD)
        metrics['thd_percent'] = self._calculate_thd(analysis_channel, sample_rate)
        
        # 3. Dynamic Range
        metrics['dynamic_range_db'] = self._calculate_dynamic_range(analysis_channel)
        
        # 4. Spectral features
        spectral_features = self._calculate_spectral_features(analysis_channel, sample_rate)
        metrics.update(spectral_features)
        
        # 5. Energy and level metrics
        energy_metrics = self._calculate_energy_metrics(analysis_channel)
        metrics.update(energy_metrics)
        
        # 6. Loudness estimation (simplified LUFS)
        metrics['loudness_lufs'] = self._estimate_loudness(analysis_channel, sample_rate)
        
        # 7. Overall quality score
        quality_score = self._calculate_quality_score(metrics)
        metrics['quality_score'] = quality_score
        
        # 8. Generate recommendations
        recommendations = self._generate_recommendations(metrics)
        
        return AudioQualityMetrics(
            snr_db=metrics['snr_db'],
            thd_percent=metrics['thd_percent'],
            dynamic_range_db=metrics['dynamic_range_db'],
            spectral_centroid=metrics['spectral_centroid'],
            spectral_rolloff=metrics['spectral_rolloff'],
            zero_crossing_rate=metrics['zero_crossing_rate'],
            rms_energy=metrics['rms_energy'],
            peak_level_db=metrics['peak_level_db'],
            loudness_lufs=metrics['loudness_lufs'],
            quality_score=quality_score,
            recommendations=recommendations
        )
    
    def _calculate_snr(self, audio_data: np.ndarray, sample_rate: int) -> float:
        """Calculate Signal-to-Noise Ratio"""
        try:
            # Estimate noise from quieter segments
            frame_size = int(0.1 * sample_rate)
            hop_size = frame_size // 2
            
            frame_energies = []
            for i in range(0, len(audio_data) - frame_size, hop_size):
                frame = audio_data[i:i + frame_size]
                energy = np.mean(frame**2)
                frame_energies.append(energy)
            
            frame_energies = np.array(frame_energies)
            
            # Assume bottom 20% of frames represent noise
            noise_threshold = np.percentile(frame_energies, 20)
            signal_energy = np.mean(frame_energies)
            
            if noise_threshold > 0:
                snr_linear = signal_energy / noise_threshold
                snr_db = 10 * np.log10(snr_linear)
            else:
                snr_db = 60.0  # Very high SNR
            
            return max(0, min(60, snr_db))  # Clamp between 0 and 60 dB
            
        except Exception:
            return 30.0  # Default moderate SNR
    
    def _calculate_thd(self, audio_data: np.ndarray, sample_rate: int) -> float:
        """Calculate Total Harmonic Distortion (simplified)"""
        try:
            # Use FFT to analyze harmonic content
            fft = np.fft.fft(audio_data)
            magnitude = np.abs(fft[:len(fft)//2])
            
            # Find fundamental frequency (simplified)
            fundamental_idx = np.argmax(magnitude[10:1000]) + 10  # Avoid DC
            
            if fundamental_idx > 0:
                # Calculate harmonic energy
                harmonic_energy = 0
                fundamental_energy = magnitude[fundamental_idx]**2
                
                for harmonic in range(2, 6):  # 2nd to 5th harmonics
                    harmonic_idx = fundamental_idx * harmonic
                    if harmonic_idx < len(magnitude):
                        harmonic_energy += magnitude[harmonic_idx]**2
                
                if fundamental_energy > 0:
                    thd = np.sqrt(harmonic_energy / fundamental_energy) * 100
                    return min(thd, 10.0)  # Cap at 10%
            
            return 1.0  # Default low THD
            
        except Exception:
            return 1.0
    
    def _calculate_dynamic_range(self, audio_data: np.ndarray) -> float:
        """Calculate dynamic range in dB"""
        try:
            peak_level = np.max(np.abs(audio_data))
            rms_level = np.sqrt(np.mean(audio_data**2))
            
            if rms_level > 0:
                dynamic_range = 20 * np.log10(peak_level / rms_level)
                return max(0, min(60, dynamic_range))
            
            return 20.0  # Default moderate dynamic range
            
        except Exception:
            return 20.0
    
    def _calculate_spectral_features(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, float]:
        """Calculate spectral features"""
        try:
            # Spectral centroid (brightness)
            spectral_centroids = librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)
            spectral_centroid = np.mean(spectral_centroids)
            
            # Spectral rolloff
            spectral_rolloffs = librosa.feature.spectral_rolloff(y=audio_data, sr=sample_rate)
            spectral_rolloff = np.mean(spectral_rolloffs)
            
            # Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(audio_data)
            zero_crossing_rate = np.mean(zcr)
            
            return {
                'spectral_centroid': float(spectral_centroid),
                'spectral_rolloff': float(spectral_rolloff),
                'zero_crossing_rate': float(zero_crossing_rate)
            }
            
        except Exception:
            return {
                'spectral_centroid': 2000.0,
                'spectral_rolloff': 4000.0,
                'zero_crossing_rate': 0.1
            }
    
    def _calculate_energy_metrics(self, audio_data: np.ndarray) -> Dict[str, float]:
        """Calculate energy and level metrics"""
        try:
            # RMS energy
            rms_energy = np.sqrt(np.mean(audio_data**2))
            
            # Peak level in dB
            peak_level = np.max(np.abs(audio_data))
            peak_level_db = 20 * np.log10(peak_level + 1e-10)
            
            return {
                'rms_energy': float(rms_energy),
                'peak_level_db': float(peak_level_db)
            }
            
        except Exception:
            return {
                'rms_energy': 0.1,
                'peak_level_db': -20.0
            }
    
    def _estimate_loudness(self, audio_data: np.ndarray, sample_rate: int) -> float:
        """Estimate loudness in LUFS (simplified)"""
        try:
            # Simplified loudness estimation
            # Apply K-weighting filter (simplified)
            nyquist = sample_rate / 2
            
            # High-pass filter at 38 Hz
            if nyquist > 38:
                b_hp, a_hp = signal.butter(4, 38 / nyquist, btype='high')
                filtered_audio = signal.filtfilt(b_hp, a_hp, audio_data)
            else:
                filtered_audio = audio_data
            
            # Calculate mean square
            mean_square = np.mean(filtered_audio**2)
            
            if mean_square > 0:
                loudness_lufs = -0.691 + 10 * np.log10(mean_square)
                return max(-70, min(0, loudness_lufs))  # Clamp to reasonable range
            
            return -30.0  # Default moderate loudness
            
        except Exception:
            return -30.0
    
    def _calculate_quality_score(self, metrics: Dict[str, float]) -> float:
        """Calculate overall quality score (0-100)"""
        try:
            score = 50.0  # Base score
            
            # SNR contribution (0-25 points)
            snr_score = min(25, metrics['snr_db'] * 25 / 40)
            score += snr_score
            
            # THD contribution (0-15 points, lower THD is better)
            thd_score = max(0, 15 - metrics['thd_percent'] * 3)
            score += thd_score
            
            # Dynamic range contribution (0-10 points)
            dr_score = min(10, metrics['dynamic_range_db'] * 10 / 30)
            score += dr_score
            
            # Clamp to 0-100 range
            return max(0, min(100, score))
            
        except Exception:
            return 50.0  # Default moderate quality
    
    def _generate_recommendations(self, metrics: Dict[str, float]) -> List[str]:
        """Generate enhancement recommendations based on quality metrics"""
        recommendations = []
        
        try:
            if metrics['snr_db'] < 20:
                recommendations.append("Apply noise reduction to improve signal-to-noise ratio")
            
            if metrics['thd_percent'] > 3:
                recommendations.append("Consider audio repair to reduce harmonic distortion")
            
            if metrics['dynamic_range_db'] < 10:
                recommendations.append("Apply dynamic range expansion to improve dynamics")
            
            if metrics['peak_level_db'] > -3:
                recommendations.append("Apply peak limiting to prevent clipping")
            
            if metrics['loudness_lufs'] < -40:
                recommendations.append("Apply normalization to increase overall loudness")
            
            if metrics['spectral_centroid'] < 1000:
                recommendations.append("Apply spectral enhancement to improve brightness")
            
            if not recommendations:
                recommendations.append("Audio quality is good - minimal enhancement needed")
            
        except Exception:
            recommendations.append("Unable to generate specific recommendations")
        
        return recommendations
    
    def get_format_recommendations(self, input_path: str) -> Dict[str, Any]:
        """Analyze audio file and provide format optimization recommendations"""
        try:
            # Load audio metadata
            audio_data, sample_rate = librosa.load(input_path, sr=None)
            duration = len(audio_data) / sample_rate
            
            # Get file size
            file_size = os.path.getsize(input_path)
            
            # Analyze content
            quality_metrics = self._assess_audio_quality(audio_data, sample_rate)
            
            recommendations = {
                'current_format': Path(input_path).suffix.lower(),
                'file_size_mb': file_size / (1024 * 1024),
                'duration_seconds': duration,
                'sample_rate': sample_rate,
                'quality_score': quality_metrics.quality_score,
                'recommendations': []
            }
            
            # Format recommendations based on use case
            if quality_metrics.quality_score > 80:
                recommendations['recommendations'].append({
                    'format': '.flac',
                    'reason': 'High quality audio - use lossless compression',
                    'expected_size_reduction': '0%',
                    'quality_impact': 'None'
                })
            
            elif quality_metrics.quality_score > 60:
                recommendations['recommendations'].append({
                    'format': '.mp3',
                    'bitrate': '320kbps',
                    'reason': 'Good quality - high bitrate MP3 suitable',
                    'expected_size_reduction': '60-70%',
                    'quality_impact': 'Minimal'
                })
            
            else:
                recommendations['recommendations'].append({
                    'format': '.mp3',
                    'bitrate': '192kbps',
                    'reason': 'Moderate quality - standard MP3 sufficient',
                    'expected_size_reduction': '70-80%',
                    'quality_impact': 'Low'
                })
            
            # Add speech-specific recommendations
            if quality_metrics.spectral_centroid < 2000:  # Likely speech
                recommendations['recommendations'].append({
                    'format': '.mp3',
                    'bitrate': '128kbps',
                    'reason': 'Speech content - lower bitrate acceptable',
                    'expected_size_reduction': '80-85%',
                    'quality_impact': 'Minimal for speech'
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate format recommendations: {str(e)}")
            return {
                'error': str(e),
                'recommendations': []
            }

def main():
    """Demo function for audio enhancement pipeline"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Audio Enhancement Pipeline Demo')
    parser.add_argument('input_file', help='Input audio file path')
    parser.add_argument('--output', help='Output file path (optional)')
    parser.add_argument('--no-noise-reduction', action='store_true', help='Skip noise reduction')
    parser.add_argument('--no-repair', action='store_true', help='Skip audio repair')
    parser.add_argument('--no-enhancement', action='store_true', help='Skip spectral enhancement')
    parser.add_argument('--format-analysis', action='store_true', help='Show format recommendations')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = AudioEnhancementPipeline()
    
    try:
        if args.format_analysis:
            # Show format recommendations
            recommendations = pipeline.get_format_recommendations(args.input_file)
            print("\n=== Format Recommendations ===")
            print(json.dumps(recommendations, indent=2))
        
        # Enhancement options
        options = {
            'noise_reduction': not args.no_noise_reduction,
            'audio_repair': not args.no_repair,
            'spectral_enhancement': not args.no_enhancement,
            'dynamic_processing': True,
            'normalization': True
        }
        
        # Enhance audio
        result = pipeline.enhance_audio(args.input_file, args.output, options)
        
        print(f"\n=== Enhancement Results ===")
        print(f"Enhanced audio saved to: {result.enhanced_audio_path}")
        print(f"Processing time: {result.processing_time:.2f} seconds")
        print(f"Enhancement applied: {', '.join(result.enhancement_applied)}")
        print(f"Quality improvement: {result.improvement_score:+.1f} points")
        
        print(f"\n=== Quality Metrics ===")
        print(f"Original quality score: {result.original_metrics.quality_score:.1f}/100")
        print(f"Enhanced quality score: {result.enhanced_metrics.quality_score:.1f}/100")
        
        print(f"\n=== Recommendations ===")
        for rec in result.enhanced_metrics.recommendations:
            print(f"- {rec}")
        
    except Exception as e:
        logger.error(f"Enhancement failed: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())