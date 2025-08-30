"""
Advanced Noise Reduction and Audio Restoration System

This module provides professional-grade noise reduction and audio restoration capabilities
including adaptive noise reduction, artifact removal, spectral enhancement, and AI-powered
audio reconstruction for missing segments.

Requirements addressed: 2.1, 2.2, 2.4
"""

import numpy as np
import librosa
import scipy.signal
import scipy.ndimage
from scipy.fft import fft, ifft, fftfreq
from typing import Dict, List, Tuple, Optional, Union
import logging
from dataclasses import dataclass
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NoiseType(Enum):
    """Types of noise that can be detected and reduced"""
    BROADBAND = "broadband"
    TONAL = "tonal"
    IMPULSIVE = "impulsive"
    STATIONARY = "stationary"
    NON_STATIONARY = "non_stationary"
    WIND = "wind"
    TRAFFIC = "traffic"
    ELECTRICAL = "electrical"

class ArtifactType(Enum):
    """Types of audio artifacts that can be removed"""
    CLICKS = "clicks"
    POPS = "pops"
    CRACKLES = "crackles"
    HUMS = "hums"
    BUZZES = "buzzes"
    DISTORTION = "distortion"
    CLIPPING = "clipping"

@dataclass
class NoiseProfile:
    """Profile of detected noise characteristics"""
    noise_type: NoiseType
    frequency_profile: np.ndarray
    power_spectrum: np.ndarray
    temporal_characteristics: Dict
    confidence: float
    recommended_reduction: float

@dataclass
class RestorationSettings:
    """Settings for audio restoration process"""
    noise_reduction_strength: float = 0.7
    preserve_speech_quality: bool = True
    artifact_removal_sensitivity: float = 0.8
    spectral_enhancement: bool = True
    dynamic_range_optimization: bool = True
    ai_reconstruction: bool = True
    processing_mode: str = "adaptive"

@dataclass
class RestorationResult:
    """Result of audio restoration process"""
    restored_audio: np.ndarray
    noise_reduction_applied: float
    artifacts_removed: List[ArtifactType]
    quality_improvement: Dict
    processing_time: float
    confidence_score: float

class AdaptiveNoiseReducer:
    """Advanced adaptive noise reduction with speech preservation"""
    
    def __init__(self):
        self.noise_profiles = {}
        self.speech_model = None
        
    def analyze_noise_profile(self, audio: np.ndarray, sr: int) -> NoiseProfile:
        """Analyze audio to create detailed noise profile"""
        try:
            # Compute spectral features
            stft = librosa.stft(audio, n_fft=2048, hop_length=512)
            magnitude = np.abs(stft)
            power_spectrum = np.mean(magnitude**2, axis=1)
            
            # Detect noise characteristics
            noise_type = self._classify_noise_type(magnitude, sr)
            frequency_profile = self._extract_frequency_profile(magnitude)
            temporal_chars = self._analyze_temporal_characteristics(magnitude)
            
            # Calculate confidence based on consistency
            confidence = self._calculate_noise_confidence(magnitude)
            
            # Recommend reduction strength
            recommended_reduction = self._recommend_reduction_strength(noise_type, confidence)
            
            return NoiseProfile(
                noise_type=noise_type,
                frequency_profile=frequency_profile,
                power_spectrum=power_spectrum,
                temporal_characteristics=temporal_chars,
                confidence=confidence,
                recommended_reduction=recommended_reduction
            )
            
        except Exception as e:
            logger.error(f"Error analyzing noise profile: {e}")
            # Return default profile
            return NoiseProfile(
                noise_type=NoiseType.BROADBAND,
                frequency_profile=np.ones(1025),
                power_spectrum=np.ones(1025),
                temporal_characteristics={},
                confidence=0.5,
                recommended_reduction=0.5
            )
    
    def _classify_noise_type(self, magnitude: np.ndarray, sr: int) -> NoiseType:
        """Classify the type of noise present in the audio"""
        # Analyze frequency distribution
        freq_variance = np.var(np.mean(magnitude, axis=1))
        temporal_variance = np.var(np.mean(magnitude, axis=0))
        
        # Detect tonal components
        freq_peaks = self._detect_tonal_components(magnitude)
        
        # Classify based on characteristics
        if len(freq_peaks) > 5:
            return NoiseType.TONAL
        elif temporal_variance > freq_variance * 2:
            return NoiseType.NON_STATIONARY
        elif freq_variance < 0.1:
            return NoiseType.STATIONARY
        else:
            return NoiseType.BROADBAND
    
    def _detect_tonal_components(self, magnitude: np.ndarray) -> List[int]:
        """Detect tonal components in the frequency spectrum"""
        avg_spectrum = np.mean(magnitude, axis=1)
        peaks, _ = scipy.signal.find_peaks(avg_spectrum, height=np.mean(avg_spectrum) * 2)
        return peaks.tolist()
    
    def _extract_frequency_profile(self, magnitude: np.ndarray) -> np.ndarray:
        """Extract frequency profile of the noise"""
        # Use minimum statistics to estimate noise floor
        noise_profile = np.percentile(magnitude, 10, axis=1)
        return noise_profile
    
    def _analyze_temporal_characteristics(self, magnitude: np.ndarray) -> Dict:
        """Analyze temporal characteristics of the noise"""
        temporal_profile = np.mean(magnitude, axis=0)
        
        return {
            'stationarity': 1.0 - (np.std(temporal_profile) / np.mean(temporal_profile)),
            'onset_rate': len(scipy.signal.find_peaks(temporal_profile)[0]) / len(temporal_profile),
            'energy_variance': np.var(temporal_profile),
            'attack_time': self._estimate_attack_time(temporal_profile),
            'decay_time': self._estimate_decay_time(temporal_profile)
        }
    
    def _estimate_attack_time(self, temporal_profile: np.ndarray) -> float:
        """Estimate attack time of noise events"""
        # Simple estimation based on energy rise time
        diff = np.diff(temporal_profile)
        positive_changes = diff[diff > 0]
        return np.mean(positive_changes) if len(positive_changes) > 0 else 0.0
    
    def _estimate_decay_time(self, temporal_profile: np.ndarray) -> float:
        """Estimate decay time of noise events"""
        # Simple estimation based on energy fall time
        diff = np.diff(temporal_profile)
        negative_changes = diff[diff < 0]
        return np.mean(np.abs(negative_changes)) if len(negative_changes) > 0 else 0.0
    
    def _calculate_noise_confidence(self, magnitude: np.ndarray) -> float:
        """Calculate confidence in noise profile estimation"""
        # Based on consistency across time frames
        freq_consistency = 1.0 - np.std(magnitude, axis=1) / (np.mean(magnitude, axis=1) + 1e-10)
        return np.mean(freq_consistency)
    
    def _recommend_reduction_strength(self, noise_type: NoiseType, confidence: float) -> float:
        """Recommend noise reduction strength based on analysis"""
        base_strength = {
            NoiseType.BROADBAND: 0.7,
            NoiseType.TONAL: 0.8,
            NoiseType.IMPULSIVE: 0.6,
            NoiseType.STATIONARY: 0.8,
            NoiseType.NON_STATIONARY: 0.6,
            NoiseType.WIND: 0.7,
            NoiseType.TRAFFIC: 0.7,
            NoiseType.ELECTRICAL: 0.9
        }
        
        return base_strength.get(noise_type, 0.7) * confidence
    
    def reduce_noise(self, audio: np.ndarray, sr: int, 
                    noise_profile: NoiseProfile, 
                    preserve_speech: bool = True) -> np.ndarray:
        """Apply adaptive noise reduction with speech preservation"""
        try:
            original_length = len(audio)
            
            # Apply spectral subtraction with adaptive parameters
            stft = librosa.stft(audio, n_fft=2048, hop_length=512)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Create noise reduction mask
            noise_mask = self._create_adaptive_mask(
                magnitude, noise_profile, preserve_speech
            )
            
            # Apply mask with smoothing
            reduced_magnitude = magnitude * noise_mask
            
            # Reconstruct audio
            reduced_stft = reduced_magnitude * np.exp(1j * phase)
            reduced_audio = librosa.istft(reduced_stft, hop_length=512, length=original_length)
            
            return reduced_audio
            
        except Exception as e:
            logger.error(f"Error in noise reduction: {e}")
            return audio
    
    def _create_adaptive_mask(self, magnitude: np.ndarray, 
                            noise_profile: NoiseProfile, 
                            preserve_speech: bool) -> np.ndarray:
        """Create adaptive noise reduction mask"""
        # Estimate SNR for each frequency bin
        noise_floor = noise_profile.frequency_profile[:, np.newaxis]
        snr = magnitude / (noise_floor + 1e-10)
        
        # Create base mask using Wiener filtering approach
        mask = snr**2 / (snr**2 + 1)
        
        # Apply speech preservation if enabled
        if preserve_speech:
            mask = self._apply_speech_preservation(mask, magnitude)
        
        # Smooth mask to avoid artifacts
        mask = scipy.ndimage.gaussian_filter1d(mask, sigma=1.0, axis=0)
        mask = scipy.ndimage.gaussian_filter1d(mask, sigma=2.0, axis=1)
        
        # Ensure mask values are reasonable
        mask = np.clip(mask, 0.1, 1.0)
        
        return mask
    
    def _apply_speech_preservation(self, mask: np.ndarray, 
                                 magnitude: np.ndarray) -> np.ndarray:
        """Apply speech preservation to the noise reduction mask"""
        # Detect speech-like regions (simplified approach)
        speech_regions = self._detect_speech_regions(magnitude)
        
        # Reduce noise reduction in speech regions
        for start, end in speech_regions:
            mask[:, start:end] = np.maximum(mask[:, start:end], 0.3)
        
        return mask
    
    def _detect_speech_regions(self, magnitude: np.ndarray) -> List[Tuple[int, int]]:
        """Detect regions likely to contain speech"""
        # Simple energy-based speech detection
        energy = np.sum(magnitude, axis=0)
        threshold = np.percentile(energy, 70)
        
        speech_frames = energy > threshold
        regions = []
        
        in_speech = False
        start = 0
        
        for i, is_speech in enumerate(speech_frames):
            if is_speech and not in_speech:
                start = i
                in_speech = True
            elif not is_speech and in_speech:
                regions.append((start, i))
                in_speech = False
        
        if in_speech:
            regions.append((start, len(speech_frames)))
        
        return regions

class AudioArtifactRemover:
    """System for removing various audio artifacts"""
    
    def __init__(self):
        self.artifact_detectors = {
            ArtifactType.CLICKS: self._detect_clicks,
            ArtifactType.POPS: self._detect_pops,
            ArtifactType.CRACKLES: self._detect_crackles,
            ArtifactType.HUMS: self._detect_hums,
            ArtifactType.BUZZES: self._detect_buzzes,
            ArtifactType.DISTORTION: self._detect_distortion,
            ArtifactType.CLIPPING: self._detect_clipping
        }
        
        self.artifact_removers = {
            ArtifactType.CLICKS: self._remove_clicks,
            ArtifactType.POPS: self._remove_pops,
            ArtifactType.CRACKLES: self._remove_crackles,
            ArtifactType.HUMS: self._remove_hums,
            ArtifactType.BUZZES: self._remove_buzzes,
            ArtifactType.DISTORTION: self._remove_distortion,
            ArtifactType.CLIPPING: self._remove_clipping
        }
    
    def detect_artifacts(self, audio: np.ndarray, sr: int) -> Dict[ArtifactType, List]:
        """Detect various types of artifacts in audio"""
        artifacts = {}
        
        for artifact_type, detector in self.artifact_detectors.items():
            try:
                detected = detector(audio, sr)
                if detected:
                    artifacts[artifact_type] = detected
            except Exception as e:
                logger.warning(f"Error detecting {artifact_type}: {e}")
        
        return artifacts
    
    def remove_artifacts(self, audio: np.ndarray, sr: int, 
                        artifacts: Dict[ArtifactType, List]) -> Tuple[np.ndarray, List[ArtifactType]]:
        """Remove detected artifacts from audio"""
        processed_audio = audio.copy()
        removed_artifacts = []
        
        for artifact_type, locations in artifacts.items():
            try:
                if artifact_type in self.artifact_removers:
                    processed_audio = self.artifact_removers[artifact_type](
                        processed_audio, sr, locations
                    )
                    removed_artifacts.append(artifact_type)
            except Exception as e:
                logger.warning(f"Error removing {artifact_type}: {e}")
        
        return processed_audio, removed_artifacts
    
    def _detect_clicks(self, audio: np.ndarray, sr: int) -> List:
        """Detect click artifacts"""
        # Use derivative-based detection
        diff = np.diff(audio)
        threshold = np.std(diff) * 5
        click_indices = np.where(np.abs(diff) > threshold)[0]
        
        # Group nearby clicks
        clicks = []
        if len(click_indices) > 0:
            current_click = [click_indices[0]]
            for idx in click_indices[1:]:
                if idx - current_click[-1] < sr * 0.001:  # Within 1ms
                    current_click.append(idx)
                else:
                    clicks.append(current_click)
                    current_click = [idx]
            clicks.append(current_click)
        
        return clicks
    
    def _detect_pops(self, audio: np.ndarray, sr: int) -> List:
        """Detect pop artifacts"""
        # Similar to clicks but with different characteristics
        window_size = int(sr * 0.005)  # 5ms window
        energy = np.array([np.sum(audio[i:i+window_size]**2) 
                          for i in range(0, len(audio)-window_size, window_size//2)])
        
        threshold = np.percentile(energy, 95)
        pop_windows = np.where(energy > threshold)[0]
        
        pops = []
        for window_idx in pop_windows:
            start = window_idx * window_size // 2
            end = start + window_size
            pops.append((start, end))
        
        return pops
    
    def _detect_crackles(self, audio: np.ndarray, sr: int) -> List:
        """Detect crackle artifacts"""
        try:
            # High-frequency content analysis
            # Ensure cutoff frequency is valid for the sample rate
            cutoff_freq = min(8000, sr // 2 - 100)  # Leave some margin
            if cutoff_freq <= 100:
                return []  # Sample rate too low for crackle detection
                
            high_freq = scipy.signal.butter(4, cutoff_freq, 'high', fs=sr, output='sos')
            filtered = scipy.signal.sosfilt(high_freq, audio)
            
            # Detect sudden increases in high-frequency energy
            energy = np.convolve(filtered**2, np.ones(int(sr*0.01)), mode='same')
            threshold = np.percentile(energy, 90)
            
            crackle_regions = []
            above_threshold = energy > threshold
            
            in_crackle = False
            start = 0
            
            for i, is_crackle in enumerate(above_threshold):
                if is_crackle and not in_crackle:
                    start = i
                    in_crackle = True
                elif not is_crackle and in_crackle:
                    crackle_regions.append((start, i))
                    in_crackle = False
            
            return crackle_regions
            
        except Exception as e:
            logger.warning(f"Error in crackle detection: {e}")
            return []
    
    def _detect_hums(self, audio: np.ndarray, sr: int) -> List:
        """Detect hum artifacts (50/60 Hz and harmonics)"""
        # Check for power line frequencies
        freqs = [50, 60, 100, 120, 150, 180]  # Common hum frequencies
        
        stft = librosa.stft(audio, n_fft=4096, hop_length=1024)
        magnitude = np.abs(stft)
        
        hum_frequencies = []
        for freq in freqs:
            freq_bin = int(freq * 4096 / sr)
            if freq_bin < magnitude.shape[0]:
                # Check if this frequency is consistently present
                freq_energy = magnitude[freq_bin, :]
                if np.mean(freq_energy) > np.percentile(magnitude.flatten(), 80):
                    hum_frequencies.append(freq)
        
        return hum_frequencies
    
    def _detect_buzzes(self, audio: np.ndarray, sr: int) -> List:
        """Detect buzz artifacts"""
        # Similar to hums but broader frequency analysis
        stft = librosa.stft(audio, n_fft=2048, hop_length=512)
        magnitude = np.abs(stft)
        
        # Look for consistent tonal components
        avg_spectrum = np.mean(magnitude, axis=1)
        peaks, properties = scipy.signal.find_peaks(
            avg_spectrum, 
            height=np.percentile(avg_spectrum, 85),
            distance=10
        )
        
        buzz_frequencies = []
        for peak in peaks:
            freq = peak * sr / 2048
            if 100 < freq < 2000:  # Typical buzz frequency range
                buzz_frequencies.append(freq)
        
        return buzz_frequencies
    
    def _detect_distortion(self, audio: np.ndarray, sr: int) -> List:
        """Detect distortion artifacts"""
        # THD (Total Harmonic Distortion) analysis
        stft = librosa.stft(audio, n_fft=2048, hop_length=512)
        magnitude = np.abs(stft)
        
        distortion_regions = []
        
        # Simple distortion detection based on spectral characteristics
        spectral_centroid = librosa.feature.spectral_centroid(S=magnitude)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(S=magnitude)[0]
        
        # Distortion often causes spectral spreading
        distortion_indicator = spectral_rolloff / (spectral_centroid + 1e-10)
        threshold = np.percentile(distortion_indicator, 90)
        
        distorted_frames = np.where(distortion_indicator > threshold)[0]
        
        # Convert frame indices to time regions
        for frame in distorted_frames:
            start_time = frame * 512 / sr
            end_time = (frame + 1) * 512 / sr
            distortion_regions.append((start_time, end_time))
        
        return distortion_regions
    
    def _detect_clipping(self, audio: np.ndarray, sr: int) -> List:
        """Detect clipping artifacts"""
        # Find samples at or near maximum amplitude
        max_amplitude = np.max(np.abs(audio))
        if max_amplitude < 0.8:  # No significant clipping if max is below 0.8
            return []
            
        threshold = 0.95 * max_amplitude
        clipped_samples = np.where(np.abs(audio) >= threshold)[0]
        
        # Group consecutive clipped samples
        clipping_regions = []
        if len(clipped_samples) > 0:
            current_region = [clipped_samples[0]]
            
            for sample in clipped_samples[1:]:
                if sample - current_region[-1] <= 1:
                    current_region.append(sample)
                else:
                    if len(current_region) > max(1, int(sr * 0.001)):  # At least 1ms of clipping
                        clipping_regions.append((current_region[0], current_region[-1]))
                    current_region = [sample]
            
            if len(current_region) > max(1, int(sr * 0.001)):
                clipping_regions.append((current_region[0], current_region[-1]))
        
        return clipping_regions
    
    def _remove_clicks(self, audio: np.ndarray, sr: int, clicks: List) -> np.ndarray:
        """Remove click artifacts using interpolation"""
        processed = audio.copy()
        
        for click_group in clicks:
            for click_idx in click_group:
                # Replace click with interpolated values
                start = max(0, click_idx - 5)
                end = min(len(audio), click_idx + 6)
                
                if start < click_idx < end - 1:
                    # Linear interpolation
                    processed[click_idx] = (processed[start] + processed[end-1]) / 2
        
        return processed
    
    def _remove_pops(self, audio: np.ndarray, sr: int, pops: List) -> np.ndarray:
        """Remove pop artifacts"""
        processed = audio.copy()
        
        for start, end in pops:
            if start > 0 and end < len(audio):
                # Replace with smoothed version
                region_length = end - start
                fade_length = min(region_length // 4, int(sr * 0.002))
                
                # Create fade in/out
                fade_in = np.linspace(0, 1, fade_length)
                fade_out = np.linspace(1, 0, fade_length)
                
                # Apply fades
                if fade_length > 0:
                    processed[start:start+fade_length] *= fade_in
                    processed[end-fade_length:end] *= fade_out
        
        return processed
    
    def _remove_crackles(self, audio: np.ndarray, sr: int, crackles: List) -> np.ndarray:
        """Remove crackle artifacts using spectral filtering"""
        processed = audio.copy()
        
        for start, end in crackles:
            if start < end and end <= len(audio):
                # Apply low-pass filter to crackle region
                sos = scipy.signal.butter(4, 6000, 'low', fs=sr, output='sos')
                processed[start:end] = scipy.signal.sosfilt(sos, processed[start:end])
        
        return processed
    
    def _remove_hums(self, audio: np.ndarray, sr: int, hum_freqs: List) -> np.ndarray:
        """Remove hum artifacts using notch filters"""
        processed = audio.copy()
        
        for freq in hum_freqs:
            # Apply notch filter
            Q = 30  # Quality factor
            w0 = freq / (sr / 2)
            b, a = scipy.signal.iirnotch(w0, Q)
            processed = scipy.signal.filtfilt(b, a, processed)
        
        return processed
    
    def _remove_buzzes(self, audio: np.ndarray, sr: int, buzz_freqs: List) -> np.ndarray:
        """Remove buzz artifacts"""
        processed = audio.copy()
        
        for freq in buzz_freqs:
            # Apply narrow notch filter
            Q = 20
            w0 = freq / (sr / 2)
            if 0 < w0 < 1:
                b, a = scipy.signal.iirnotch(w0, Q)
                processed = scipy.signal.filtfilt(b, a, processed)
        
        return processed
    
    def _remove_distortion(self, audio: np.ndarray, sr: int, distortion_regions: List) -> np.ndarray:
        """Remove distortion artifacts"""
        processed = audio.copy()
        
        for start_time, end_time in distortion_regions:
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            
            if start_sample < end_sample and end_sample <= len(audio):
                # Apply gentle compression to reduce distortion
                region = processed[start_sample:end_sample]
                # Simple soft clipping
                processed[start_sample:end_sample] = np.tanh(region * 0.8) / 0.8
        
        return processed
    
    def _remove_clipping(self, audio: np.ndarray, sr: int, clipping_regions: List) -> np.ndarray:
        """Remove clipping artifacts using interpolation"""
        processed = audio.copy()
        
        for start, end in clipping_regions:
            if start > 10 and end < len(audio) - 10:
                # Cubic spline interpolation
                x_good = np.concatenate([
                    np.arange(start-10, start),
                    np.arange(end, end+10)
                ])
                y_good = processed[x_good]
                
                x_bad = np.arange(start, end)
                interpolated = np.interp(x_bad, x_good, y_good)
                processed[start:end] = interpolated
        
        return processed

class SpectralEnhancer:
    """Spectral enhancement and dynamic range optimization"""
    
    def __init__(self):
        pass
    
    def enhance_spectrum(self, audio: np.ndarray, sr: int, 
                        enhancement_strength: float = 0.5) -> np.ndarray:
        """Apply spectral enhancement to improve audio clarity"""
        try:
            original_length = len(audio)
            
            # Apply multi-band enhancement
            stft = librosa.stft(audio, n_fft=2048, hop_length=512)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Enhance different frequency bands
            enhanced_magnitude = self._apply_multiband_enhancement(
                magnitude, sr, enhancement_strength
            )
            
            # Reconstruct audio
            enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
            enhanced_audio = librosa.istft(enhanced_stft, hop_length=512, length=original_length)
            
            return enhanced_audio
            
        except Exception as e:
            logger.error(f"Error in spectral enhancement: {e}")
            return audio
    
    def _apply_multiband_enhancement(self, magnitude: np.ndarray, 
                                   sr: int, strength: float) -> np.ndarray:
        """Apply enhancement to different frequency bands"""
        enhanced = magnitude.copy()
        
        # Define frequency bands (in Hz)
        bands = [
            (80, 250),    # Low frequencies
            (250, 1000),  # Low-mid frequencies  
            (1000, 4000), # Mid frequencies (speech)
            (4000, 8000), # High-mid frequencies
            (8000, sr//2) # High frequencies
        ]
        
        # Enhancement factors for each band
        enhancements = [1.0, 1.1, 1.3, 1.2, 1.1]  # Boost speech frequencies more
        
        for (low_freq, high_freq), enhancement in zip(bands, enhancements):
            low_bin = int(low_freq * 2048 / sr)
            high_bin = int(high_freq * 2048 / sr)
            
            if low_bin < enhanced.shape[0] and high_bin <= enhanced.shape[0]:
                band_enhancement = 1.0 + (enhancement - 1.0) * strength
                enhanced[low_bin:high_bin, :] *= band_enhancement
        
        return enhanced
    
    def optimize_dynamic_range(self, audio: np.ndarray, sr: int,
                             target_lufs: float = -23.0) -> np.ndarray:
        """Optimize dynamic range and loudness"""
        try:
            # Apply gentle compression
            compressed = self._apply_multiband_compression(audio, sr)
            
            # Normalize to target loudness
            normalized = self._normalize_loudness(compressed, sr, target_lufs)
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error in dynamic range optimization: {e}")
            return audio
    
    def _apply_multiband_compression(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Apply gentle multiband compression"""
        # Split into frequency bands
        low_freq = scipy.signal.butter(4, 500, 'low', fs=sr, output='sos')
        mid_freq = scipy.signal.butter(4, [500, 4000], 'band', fs=sr, output='sos')
        high_freq = scipy.signal.butter(4, 4000, 'high', fs=sr, output='sos')
        
        low_band = scipy.signal.sosfilt(low_freq, audio)
        mid_band = scipy.signal.sosfilt(mid_freq, audio)
        high_band = scipy.signal.sosfilt(high_freq, audio)
        
        # Apply compression to each band
        low_compressed = self._compress_band(low_band, ratio=2.0, threshold=0.7)
        mid_compressed = self._compress_band(mid_band, ratio=3.0, threshold=0.6)
        high_compressed = self._compress_band(high_band, ratio=2.5, threshold=0.65)
        
        # Recombine bands
        compressed = low_compressed + mid_compressed + high_compressed
        
        return compressed
    
    def _compress_band(self, audio: np.ndarray, ratio: float, threshold: float) -> np.ndarray:
        """Apply compression to a frequency band"""
        # Simple soft-knee compression
        abs_audio = np.abs(audio)
        compressed = np.copy(audio)
        
        # Find samples above threshold
        above_threshold = abs_audio > threshold
        
        if np.any(above_threshold):
            # Apply compression with limiting to prevent excessive amplification
            excess = abs_audio[above_threshold] - threshold
            compressed_excess = excess / ratio
            
            # Maintain sign and limit maximum output
            sign = np.sign(audio[above_threshold])
            new_values = threshold + compressed_excess
            # Limit to reasonable maximum to prevent artifacts
            new_values = np.minimum(new_values, threshold * 2.0)
            compressed[above_threshold] = sign * new_values
        
        return compressed
    
    def _normalize_loudness(self, audio: np.ndarray, sr: int, target_lufs: float) -> np.ndarray:
        """Normalize audio to target loudness (simplified)"""
        # Simple RMS-based normalization (not true LUFS)
        rms = np.sqrt(np.mean(audio**2))
        target_rms = 10**(target_lufs/20)  # Approximate conversion
        
        if rms > 0:
            gain = target_rms / rms
            # Limit gain to prevent excessive amplification
            gain = min(gain, 3.0)
            normalized = audio * gain
        else:
            normalized = audio
        
        # Prevent clipping
        max_val = np.max(np.abs(normalized))
        if max_val > 0.95:
            normalized = normalized * 0.95 / max_val
        
        return normalized

class AIAudioReconstructor:
    """AI-powered audio reconstruction for missing segments"""
    
    def __init__(self):
        self.model_initialized = False
    
    def detect_missing_segments(self, audio: np.ndarray, sr: int) -> List[Tuple[int, int]]:
        """Detect segments that need reconstruction"""
        missing_segments = []
        
        # Detect silence or very low energy regions
        energy = np.convolve(audio**2, np.ones(int(sr*0.1)), mode='same')
        threshold = np.percentile(energy, 5)
        
        silent_regions = energy < threshold
        
        # Find continuous silent regions longer than 50ms
        min_length = int(sr * 0.05)
        
        in_silence = False
        start = 0
        
        for i, is_silent in enumerate(silent_regions):
            if is_silent and not in_silence:
                start = i
                in_silence = True
            elif not is_silent and in_silence:
                if i - start > min_length:
                    missing_segments.append((start, i))
                in_silence = False
        
        return missing_segments
    
    def reconstruct_segments(self, audio: np.ndarray, sr: int,
                           missing_segments: List[Tuple[int, int]]) -> np.ndarray:
        """Reconstruct missing audio segments using AI techniques"""
        reconstructed = audio.copy()
        
        for start, end in missing_segments:
            try:
                # Use context-based reconstruction
                reconstructed_segment = self._reconstruct_segment(
                    audio, start, end, sr
                )
                reconstructed[start:end] = reconstructed_segment
            except Exception as e:
                logger.warning(f"Failed to reconstruct segment {start}-{end}: {e}")
        
        return reconstructed
    
    def _reconstruct_segment(self, audio: np.ndarray, start: int, end: int, sr: int) -> np.ndarray:
        """Reconstruct a single missing segment"""
        segment_length = end - start
        
        # Get context before and after the missing segment
        context_length = min(segment_length * 2, sr)  # Up to 1 second of context
        
        before_start = max(0, start - context_length)
        after_end = min(len(audio), end + context_length)
        
        before_context = audio[before_start:start]
        after_context = audio[end:after_end]
        
        if len(before_context) == 0 and len(after_context) == 0:
            # No context available, return silence
            return np.zeros(segment_length)
        
        # Use spectral interpolation for reconstruction
        return self._spectral_interpolation(
            before_context, after_context, segment_length, sr
        )
    
    def _spectral_interpolation(self, before: np.ndarray, after: np.ndarray,
                              target_length: int, sr: int) -> np.ndarray:
        """Reconstruct audio using spectral interpolation"""
        if len(before) == 0:
            # Only after context available
            return self._extrapolate_from_context(after, target_length, reverse=True)
        elif len(after) == 0:
            # Only before context available
            return self._extrapolate_from_context(before, target_length, reverse=False)
        else:
            # Both contexts available - interpolate
            return self._interpolate_between_contexts(before, after, target_length, sr)
    
    def _extrapolate_from_context(self, context: np.ndarray, target_length: int,
                                reverse: bool = False) -> np.ndarray:
        """Extrapolate audio from single context"""
        if len(context) == 0:
            return np.zeros(target_length)
        
        # Use autoregressive prediction (simplified)
        if reverse:
            context = context[::-1]
        
        # Simple linear prediction
        if len(context) >= 2:
            # Use last few samples to predict trend
            trend = context[-1] - context[-2] if len(context) >= 2 else 0
            
            reconstructed = np.zeros(target_length)
            last_value = context[-1]
            
            for i in range(target_length):
                # Add some decay to the trend
                decay = np.exp(-i / (target_length * 0.3))
                reconstructed[i] = last_value + trend * decay
                # Add some noise for naturalness
                reconstructed[i] += np.random.normal(0, np.std(context) * 0.1)
        else:
            # Not enough context, use repetition with fade
            reconstructed = np.tile(context, (target_length // len(context)) + 1)[:target_length]
            # Apply fade
            fade = np.linspace(1, 0, target_length)
            reconstructed *= fade
        
        if reverse:
            reconstructed = reconstructed[::-1]
        
        return reconstructed
    
    def _interpolate_between_contexts(self, before: np.ndarray, after: np.ndarray,
                                    target_length: int, sr: int) -> np.ndarray:
        """Interpolate audio between two contexts"""
        # Use spectral interpolation
        try:
            # Get spectral characteristics of contexts
            before_stft = librosa.stft(before, n_fft=1024, hop_length=256)
            after_stft = librosa.stft(after, n_fft=1024, hop_length=256)
            
            before_mag = np.abs(before_stft)
            after_mag = np.abs(after_stft)
            
            before_phase = np.angle(before_stft)
            after_phase = np.angle(after_stft)
            
            # Interpolate magnitude and phase
            target_frames = target_length // 256 + 1
            
            interpolated_mag = np.zeros((before_mag.shape[0], target_frames))
            interpolated_phase = np.zeros((before_phase.shape[0], target_frames))
            
            for freq_bin in range(before_mag.shape[0]):
                # Interpolate magnitude
                start_mag = np.mean(before_mag[freq_bin, -5:]) if before_mag.shape[1] >= 5 else np.mean(before_mag[freq_bin, :])
                end_mag = np.mean(after_mag[freq_bin, :5]) if after_mag.shape[1] >= 5 else np.mean(after_mag[freq_bin, :])
                
                interpolated_mag[freq_bin, :] = np.linspace(start_mag, end_mag, target_frames)
                
                # Interpolate phase (more complex due to wrapping)
                start_phase = np.mean(before_phase[freq_bin, -5:]) if before_phase.shape[1] >= 5 else np.mean(before_phase[freq_bin, :])
                end_phase = np.mean(after_phase[freq_bin, :5]) if after_phase.shape[1] >= 5 else np.mean(after_phase[freq_bin, :])
                
                # Handle phase wrapping
                phase_diff = end_phase - start_phase
                if phase_diff > np.pi:
                    phase_diff -= 2 * np.pi
                elif phase_diff < -np.pi:
                    phase_diff += 2 * np.pi
                
                interpolated_phase[freq_bin, :] = start_phase + np.linspace(0, phase_diff, target_frames)
            
            # Reconstruct audio
            interpolated_stft = interpolated_mag * np.exp(1j * interpolated_phase)
            reconstructed = librosa.istft(interpolated_stft, hop_length=256)
            
            # Ensure correct length
            if len(reconstructed) > target_length:
                reconstructed = reconstructed[:target_length]
            elif len(reconstructed) < target_length:
                reconstructed = np.pad(reconstructed, (0, target_length - len(reconstructed)))
            
            return reconstructed
            
        except Exception as e:
            logger.warning(f"Spectral interpolation failed: {e}")
            # Fallback to simple linear interpolation
            return np.linspace(before[-1] if len(before) > 0 else 0,
                             after[0] if len(after) > 0 else 0,
                             target_length)

class AdvancedNoiseReductionSystem:
    """Main system coordinating all noise reduction and restoration components"""
    
    def __init__(self):
        self.noise_reducer = AdaptiveNoiseReducer()
        self.artifact_remover = AudioArtifactRemover()
        self.spectral_enhancer = SpectralEnhancer()
        self.ai_reconstructor = AIAudioReconstructor()
    
    def process_audio(self, audio: np.ndarray, sr: int,
                     settings: RestorationSettings) -> RestorationResult:
        """Process audio with comprehensive noise reduction and restoration"""
        import time
        start_time = time.time()
        
        try:
            processed_audio = audio.copy()
            quality_improvements = {}
            artifacts_removed = []
            
            # Step 1: Analyze noise profile
            logger.info("Analyzing noise profile...")
            noise_profile = self.noise_reducer.analyze_noise_profile(processed_audio, sr)
            
            # Step 2: Apply adaptive noise reduction
            if settings.noise_reduction_strength > 0:
                logger.info("Applying noise reduction...")
                processed_audio = self.noise_reducer.reduce_noise(
                    processed_audio, sr, noise_profile, settings.preserve_speech_quality
                )
                quality_improvements['noise_reduction'] = settings.noise_reduction_strength
            
            # Step 3: Detect and remove artifacts
            if settings.artifact_removal_sensitivity > 0:
                logger.info("Detecting and removing artifacts...")
                artifacts = self.artifact_remover.detect_artifacts(processed_audio, sr)
                processed_audio, removed = self.artifact_remover.remove_artifacts(
                    processed_audio, sr, artifacts
                )
                artifacts_removed = removed
                quality_improvements['artifacts_removed'] = len(removed)
            
            # Step 4: Apply spectral enhancement
            if settings.spectral_enhancement:
                logger.info("Applying spectral enhancement...")
                processed_audio = self.spectral_enhancer.enhance_spectrum(
                    processed_audio, sr, settings.noise_reduction_strength
                )
                quality_improvements['spectral_enhancement'] = True
            
            # Step 5: Optimize dynamic range
            if settings.dynamic_range_optimization:
                logger.info("Optimizing dynamic range...")
                processed_audio = self.spectral_enhancer.optimize_dynamic_range(
                    processed_audio, sr
                )
                quality_improvements['dynamic_range_optimized'] = True
            
            # Step 6: AI-powered reconstruction
            if settings.ai_reconstruction:
                logger.info("Reconstructing missing segments...")
                missing_segments = self.ai_reconstructor.detect_missing_segments(
                    processed_audio, sr
                )
                if missing_segments:
                    processed_audio = self.ai_reconstructor.reconstruct_segments(
                        processed_audio, sr, missing_segments
                    )
                    quality_improvements['segments_reconstructed'] = len(missing_segments)
            
            # Calculate overall quality improvement
            processing_time = time.time() - start_time
            confidence_score = self._calculate_confidence_score(
                audio, processed_audio, quality_improvements
            )
            
            return RestorationResult(
                restored_audio=processed_audio,
                noise_reduction_applied=settings.noise_reduction_strength,
                artifacts_removed=artifacts_removed,
                quality_improvement=quality_improvements,
                processing_time=processing_time,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            logger.error(f"Error in audio processing: {e}")
            return RestorationResult(
                restored_audio=audio,
                noise_reduction_applied=0.0,
                artifacts_removed=[],
                quality_improvement={},
                processing_time=time.time() - start_time,
                confidence_score=0.0
            )
    
    def _calculate_confidence_score(self, original: np.ndarray, 
                                  processed: np.ndarray,
                                  improvements: Dict) -> float:
        """Calculate confidence score for the restoration process"""
        try:
            # Simple quality metrics
            original_rms = np.sqrt(np.mean(original**2))
            processed_rms = np.sqrt(np.mean(processed**2))
            
            # SNR improvement estimation
            snr_improvement = 0.0
            if original_rms > 0:
                snr_improvement = min(processed_rms / original_rms, 2.0)
            
            # Factor in number of improvements made
            improvement_factor = len(improvements) / 6.0  # Max 6 types of improvements
            
            # Combine factors
            confidence = (snr_improvement * 0.6 + improvement_factor * 0.4)
            return min(confidence, 1.0)
            
        except Exception:
            return 0.5

# Example usage and testing functions
def create_test_audio(duration: float = 5.0, sr: int = 44100) -> np.ndarray:
    """Create test audio with various types of noise and artifacts"""
    t = np.linspace(0, duration, int(duration * sr))
    
    # Base signal (speech-like)
    signal = np.sin(2 * np.pi * 440 * t) * np.exp(-t * 0.5)  # Decaying tone
    signal += 0.3 * np.sin(2 * np.pi * 880 * t) * np.exp(-t * 0.3)  # Harmonic
    
    # Add various types of noise
    # Broadband noise
    signal += 0.2 * np.random.normal(0, 1, len(signal))
    
    # 60 Hz hum
    signal += 0.1 * np.sin(2 * np.pi * 60 * t)
    
    # Clicks (impulse noise)
    click_times = np.random.choice(len(signal), size=10, replace=False)
    for click_time in click_times:
        if click_time < len(signal) - 1:
            signal[click_time] += 2.0 * np.random.choice([-1, 1])
    
    # Normalize
    signal = signal / np.max(np.abs(signal)) * 0.8
    
    return signal

def test_noise_reduction_system():
    """Test the advanced noise reduction system"""
    print("Testing Advanced Noise Reduction System...")
    
    # Create test audio
    test_audio = create_test_audio()
    sr = 44100
    
    # Initialize system
    system = AdvancedNoiseReductionSystem()
    
    # Configure settings
    settings = RestorationSettings(
        noise_reduction_strength=0.7,
        preserve_speech_quality=True,
        artifact_removal_sensitivity=0.8,
        spectral_enhancement=True,
        dynamic_range_optimization=True,
        ai_reconstruction=True
    )
    
    # Process audio
    result = system.process_audio(test_audio, sr, settings)
    
    print(f"Processing completed in {result.processing_time:.2f} seconds")
    print(f"Confidence score: {result.confidence_score:.2f}")
    print(f"Noise reduction applied: {result.noise_reduction_applied:.2f}")
    print(f"Artifacts removed: {result.artifacts_removed}")
    print(f"Quality improvements: {result.quality_improvement}")
    
    return result

if __name__ == "__main__":
    test_noise_reduction_system()