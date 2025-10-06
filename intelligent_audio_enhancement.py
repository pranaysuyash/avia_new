"""
Intelligent Audio Enhancement and Clarity Optimization System

This module provides advanced audio enhancement capabilities including:
- Spectral enhancement with frequency-specific processing
- Dynamic range optimization and loudness management
- Speech clarity enhancement with intelligibility optimization
- Automatic audio quality improvement with user control

Requirements: 2.3, 2.6
"""

import numpy as np
import librosa
import scipy.signal
from scipy.fft import fft, ifft
from typing import Dict, List, Tuple, Optional, Any
import logging
from dataclasses import dataclass
from enum import Enum
import json
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancementMode(Enum):
    """Audio enhancement processing modes"""
    AUTOMATIC = "automatic"
    SPEECH_FOCUSED = "speech_focused"
    MUSIC_FOCUSED = "music_focused"
    BROADCAST = "broadcast"
    CUSTOM = "custom"

class QualityMetric(Enum):
    """Audio quality assessment metrics"""
    SNR = "signal_to_noise_ratio"
    THD = "total_harmonic_distortion"
    CLARITY = "speech_clarity"
    LOUDNESS = "perceived_loudness"
    DYNAMIC_RANGE = "dynamic_range"
    FREQUENCY_BALANCE = "frequency_balance"

@dataclass
class SpectralEnhancementConfig:
    """Configuration for spectral enhancement processing"""
    frequency_bands: List[Tuple[float, float]]  # Frequency ranges for processing
    enhancement_factors: List[float]  # Enhancement factor per band
    smoothing_factor: float = 0.3
    preserve_phase: bool = True
    adaptive_processing: bool = True

@dataclass
class DynamicRangeConfig:
    """Configuration for dynamic range optimization"""
    target_lufs: float = -23.0  # Target loudness (LUFS)
    max_peak: float = -1.0  # Maximum peak level (dBFS)
    compression_ratio: float = 3.0
    attack_time: float = 0.003  # Attack time in seconds
    release_time: float = 0.1  # Release time in seconds
    knee_width: float = 2.0  # Soft knee width in dB

@dataclass
class SpeechClarityConfig:
    """Configuration for speech clarity enhancement"""
    formant_enhancement: bool = True
    consonant_boost: bool = True
    vowel_clarity: bool = True
    sibilance_control: bool = True
    intelligibility_target: float = 0.85  # Target intelligibility score

@dataclass
class QualityAssessment:
    """Audio quality assessment results"""
    overall_score: float
    metrics: Dict[QualityMetric, float]
    recommendations: List[str]
    processing_confidence: float

class SpectralEnhancer:
    """Advanced spectral enhancement with frequency-specific processing"""
    
    def __init__(self):
        self.sample_rate = 44100
        self.fft_size = 2048
        self.hop_length = 512
        
    def analyze_spectrum(self, audio: np.ndarray, sr: int) -> Dict[str, Any]:
        """Analyze audio spectrum for enhancement planning"""
        try:
            # Compute spectral features
            stft = librosa.stft(audio, n_fft=self.fft_size, hop_length=self.hop_length)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Frequency analysis
            freqs = librosa.fft_frequencies(sr=sr, n_fft=self.fft_size)
            spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)[0]
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sr)[0]
            
            # Energy distribution analysis
            low_energy = np.mean(magnitude[freqs < 500])
            mid_energy = np.mean(magnitude[(freqs >= 500) & (freqs < 4000)])
            high_energy = np.mean(magnitude[freqs >= 4000])
            
            return {
                'stft': stft,
                'magnitude': magnitude,
                'phase': phase,
                'freqs': freqs,
                'spectral_centroid': np.mean(spectral_centroid),
                'spectral_rolloff': np.mean(spectral_rolloff),
                'spectral_bandwidth': np.mean(spectral_bandwidth),
                'energy_distribution': {
                    'low': low_energy,
                    'mid': mid_energy,
                    'high': high_energy
                }
            }
        except Exception as e:
            logger.error(f"Error in spectrum analysis: {e}")
            raise
    
    def enhance_spectrum(self, audio: np.ndarray, sr: int, 
                        config: SpectralEnhancementConfig) -> np.ndarray:
        """Apply frequency-specific spectral enhancement"""
        try:
            # Analyze spectrum
            analysis = self.analyze_spectrum(audio, sr)
            stft = analysis['stft']
            magnitude = analysis['magnitude']
            phase = analysis['phase']
            freqs = analysis['freqs']
            
            # Apply frequency-specific enhancement
            enhanced_magnitude = magnitude.copy()
            
            for i, (freq_low, freq_high) in enumerate(config.frequency_bands):
                if i < len(config.enhancement_factors):
                    # Find frequency indices
                    freq_mask = (freqs >= freq_low) & (freqs <= freq_high)
                    
                    # Apply enhancement factor
                    enhancement_factor = config.enhancement_factors[i]
                    
                    if config.adaptive_processing:
                        # Adaptive enhancement based on existing energy
                        current_energy = np.mean(magnitude[freq_mask])
                        adaptive_factor = self._calculate_adaptive_factor(
                            current_energy, enhancement_factor
                        )
                        enhanced_magnitude[freq_mask] *= adaptive_factor
                    else:
                        enhanced_magnitude[freq_mask] *= enhancement_factor
            
            # Apply smoothing
            if config.smoothing_factor > 0:
                enhanced_magnitude = self._apply_spectral_smoothing(
                    enhanced_magnitude, config.smoothing_factor
                )
            
            # Reconstruct audio
            if config.preserve_phase:
                enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
            else:
                enhanced_stft = enhanced_magnitude * np.exp(1j * np.angle(stft))
            
            enhanced_audio = librosa.istft(enhanced_stft, hop_length=self.hop_length, length=len(audio))
            
            logger.info("Spectral enhancement completed successfully")
            return enhanced_audio
            
        except Exception as e:
            logger.error(f"Error in spectral enhancement: {e}")
            raise
    
    def _calculate_adaptive_factor(self, current_energy: float, 
                                 target_factor: float) -> float:
        """Calculate adaptive enhancement factor based on current energy"""
        # Reduce enhancement for already strong frequencies
        if current_energy > 0.1:
            return target_factor * 0.7
        elif current_energy > 0.05:
            return target_factor * 0.85
        else:
            return target_factor
    
    def _apply_spectral_smoothing(self, magnitude: np.ndarray, 
                                smoothing_factor: float) -> np.ndarray:
        """Apply spectral smoothing to reduce artifacts"""
        # Apply moving average smoothing across frequency bins
        kernel_size = max(3, int(magnitude.shape[0] * smoothing_factor * 0.01))
        kernel = np.ones(kernel_size) / kernel_size
        
        smoothed = np.zeros_like(magnitude)
        for i in range(magnitude.shape[1]):
            smoothed[:, i] = np.convolve(magnitude[:, i], kernel, mode='same')
        
        return smoothed

class DynamicRangeOptimizer:
    """Dynamic range optimization and loudness management"""
    
    def __init__(self):
        self.sample_rate = 44100
        
    def analyze_dynamics(self, audio: np.ndarray, sr: int) -> Dict[str, float]:
        """Analyze audio dynamics and loudness characteristics"""
        try:
            # RMS and peak analysis
            rms = np.sqrt(np.mean(audio**2))
            peak = np.max(np.abs(audio))
            crest_factor = peak / rms if rms > 0 else 0
            
            # Dynamic range estimation
            dynamic_range = self._estimate_dynamic_range(audio)
            
            # Loudness estimation (simplified LUFS approximation)
            loudness_lufs = self._estimate_loudness_lufs(audio, sr)
            
            return {
                'rms': rms,
                'peak': peak,
                'crest_factor': crest_factor,
                'dynamic_range': dynamic_range,
                'loudness_lufs': loudness_lufs,
                'peak_dbfs': 20 * np.log10(peak) if peak > 0 else -np.inf
            }
        except Exception as e:
            logger.error(f"Error in dynamics analysis: {e}")
            raise
    
    def optimize_dynamic_range(self, audio: np.ndarray, sr: int,
                             config: DynamicRangeConfig) -> np.ndarray:
        """Optimize dynamic range with compression and limiting"""
        try:
            # Analyze current dynamics
            dynamics = self.analyze_dynamics(audio, sr)
            
            # Apply compression
            compressed_audio = self._apply_compression(audio, sr, config)
            
            # Apply loudness normalization
            normalized_audio = self._normalize_loudness(
                compressed_audio, sr, config.target_lufs
            )
            
            # Apply peak limiting
            limited_audio = self._apply_peak_limiting(
                normalized_audio, config.max_peak
            )
            
            logger.info(f"Dynamic range optimization completed. "
                       f"Original LUFS: {dynamics['loudness_lufs']:.1f}, "
                       f"Target LUFS: {config.target_lufs}")
            
            return limited_audio
            
        except Exception as e:
            logger.error(f"Error in dynamic range optimization: {e}")
            raise
    
    def _apply_compression(self, audio: np.ndarray, sr: int,
                         config: DynamicRangeConfig) -> np.ndarray:
        """Apply dynamic range compression"""
        # Simple compression implementation
        threshold_linear = 0.5  # -6 dBFS threshold
        ratio = config.compression_ratio
        
        # Calculate gain reduction
        audio_abs = np.abs(audio)
        gain_reduction = np.ones_like(audio_abs)
        
        # Apply compression above threshold
        above_threshold = audio_abs > threshold_linear
        excess = audio_abs[above_threshold] - threshold_linear
        compressed_excess = excess / ratio
        gain_reduction[above_threshold] = (threshold_linear + compressed_excess) / audio_abs[above_threshold]
        
        # Apply gain reduction with attack/release
        smoothed_gain = self._apply_attack_release(
            gain_reduction, sr, config.attack_time, config.release_time
        )
        
        return audio * smoothed_gain
    
    def _apply_attack_release(self, gain_reduction: np.ndarray, sr: int,
                            attack_time: float, release_time: float) -> np.ndarray:
        """Apply attack and release smoothing to gain reduction"""
        attack_coeff = np.exp(-1.0 / (attack_time * sr))
        release_coeff = np.exp(-1.0 / (release_time * sr))
        
        smoothed_gain = np.zeros_like(gain_reduction)
        smoothed_gain[0] = gain_reduction[0]
        
        for i in range(1, len(gain_reduction)):
            if gain_reduction[i] < smoothed_gain[i-1]:  # Attack
                smoothed_gain[i] = attack_coeff * smoothed_gain[i-1] + (1 - attack_coeff) * gain_reduction[i]
            else:  # Release
                smoothed_gain[i] = release_coeff * smoothed_gain[i-1] + (1 - release_coeff) * gain_reduction[i]
        
        return smoothed_gain
    
    def _normalize_loudness(self, audio: np.ndarray, sr: int, 
                          target_lufs: float) -> np.ndarray:
        """Normalize audio to target LUFS loudness"""
        current_lufs = self._estimate_loudness_lufs(audio, sr)
        gain_db = target_lufs - current_lufs
        gain_linear = 10**(gain_db / 20)
        return audio * gain_linear
    
    def _apply_peak_limiting(self, audio: np.ndarray, max_peak_dbfs: float) -> np.ndarray:
        """Apply peak limiting to prevent clipping"""
        max_peak_linear = 10**(max_peak_dbfs / 20)
        current_peak = np.max(np.abs(audio))
        
        if current_peak > max_peak_linear:
            gain = max_peak_linear / current_peak
            return audio * gain
        
        return audio
    
    def _estimate_dynamic_range(self, audio: np.ndarray) -> float:
        """Estimate dynamic range of audio signal"""
        # Calculate percentile-based dynamic range
        audio_db = 20 * np.log10(np.abs(audio) + 1e-10)
        p95 = np.percentile(audio_db, 95)
        p5 = np.percentile(audio_db, 5)
        return p95 - p5
    
    def _estimate_loudness_lufs(self, audio: np.ndarray, sr: int) -> float:
        """Simplified LUFS loudness estimation"""
        # This is a simplified approximation
        rms = np.sqrt(np.mean(audio**2))
        lufs_approx = 20 * np.log10(rms) - 0.691
        return lufs_approx

class SpeechClarityEnhancer:
    """Speech clarity enhancement with intelligibility optimization"""
    
    def __init__(self):
        self.sample_rate = 44100
        
    def analyze_speech_clarity(self, audio: np.ndarray, sr: int) -> Dict[str, float]:
        """Analyze speech clarity and intelligibility metrics"""
        try:
            # Spectral analysis for speech characteristics
            stft = librosa.stft(audio, n_fft=2048, hop_length=512)
            magnitude = np.abs(stft)
            freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
            
            # Speech frequency bands analysis
            formant_energy = np.mean(magnitude[(freqs >= 300) & (freqs <= 3400)])
            consonant_energy = np.mean(magnitude[(freqs >= 2000) & (freqs <= 8000)])
            vowel_energy = np.mean(magnitude[(freqs >= 200) & (freqs <= 2000)])
            
            # Spectral clarity metrics
            spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr))
            spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=audio, sr=sr))
            
            # Intelligibility estimation (simplified)
            intelligibility_score = self._estimate_intelligibility(
                formant_energy, consonant_energy, vowel_energy
            )
            
            return {
                'formant_energy': formant_energy,
                'consonant_energy': consonant_energy,
                'vowel_energy': vowel_energy,
                'spectral_centroid': spectral_centroid,
                'spectral_rolloff': spectral_rolloff,
                'intelligibility_score': intelligibility_score
            }
        except Exception as e:
            logger.error(f"Error in speech clarity analysis: {e}")
            raise
    
    def enhance_speech_clarity(self, audio: np.ndarray, sr: int,
                             config: SpeechClarityConfig) -> np.ndarray:
        """Enhance speech clarity and intelligibility"""
        try:
            enhanced_audio = audio.copy()
            
            # Analyze current speech characteristics
            clarity_metrics = self.analyze_speech_clarity(audio, sr)
            
            # Apply formant enhancement
            if config.formant_enhancement:
                enhanced_audio = self._enhance_formants(enhanced_audio, sr)
            
            # Apply consonant boost
            if config.consonant_boost:
                enhanced_audio = self._boost_consonants(enhanced_audio, sr)
            
            # Apply vowel clarity enhancement
            if config.vowel_clarity:
                enhanced_audio = self._enhance_vowel_clarity(enhanced_audio, sr)
            
            # Apply sibilance control
            if config.sibilance_control:
                enhanced_audio = self._control_sibilance(enhanced_audio, sr)
            
            # Verify intelligibility improvement
            final_metrics = self.analyze_speech_clarity(enhanced_audio, sr)
            
            logger.info(f"Speech clarity enhancement completed. "
                       f"Intelligibility: {clarity_metrics['intelligibility_score']:.3f} -> "
                       f"{final_metrics['intelligibility_score']:.3f}")
            
            return enhanced_audio
            
        except Exception as e:
            logger.error(f"Error in speech clarity enhancement: {e}")
            raise
    
    def _enhance_formants(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Enhance formant frequencies for better speech clarity"""
        # Apply gentle boost to formant regions (300-3400 Hz)
        nyquist = sr // 2
        low_freq = 300 / nyquist
        high_freq = 3400 / nyquist
        
        # Design bandpass filter for formant region
        b, a = scipy.signal.butter(4, [low_freq, high_freq], btype='band')
        formant_signal = scipy.signal.filtfilt(b, a, audio)
        
        # Add enhanced formants back to original signal
        return audio + 0.2 * formant_signal
    
    def _boost_consonants(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Boost consonant frequencies for better articulation"""
        # Apply gentle boost to consonant region (2000-8000 Hz)
        nyquist = sr // 2
        low_freq = 2000 / nyquist
        high_freq = min(8000, nyquist - 100) / nyquist
        
        # Design highpass filter for consonant region
        b, a = scipy.signal.butter(4, low_freq, btype='high')
        consonant_signal = scipy.signal.filtfilt(b, a, audio)
        
        # Add enhanced consonants back to original signal
        return audio + 0.15 * consonant_signal
    
    def _enhance_vowel_clarity(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Enhance vowel clarity in lower frequency range"""
        # Apply gentle boost to vowel region (200-2000 Hz)
        nyquist = sr // 2
        low_freq = 200 / nyquist
        high_freq = 2000 / nyquist
        
        # Design bandpass filter for vowel region
        b, a = scipy.signal.butter(4, [low_freq, high_freq], btype='band')
        vowel_signal = scipy.signal.filtfilt(b, a, audio)
        
        # Add enhanced vowels back to original signal
        return audio + 0.1 * vowel_signal
    
    def _control_sibilance(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Control excessive sibilance in high frequencies"""
        # Apply gentle compression to sibilant region (4000-10000 Hz)
        nyquist = sr // 2
        low_freq = 4000 / nyquist
        high_freq = min(10000, nyquist - 100) / nyquist
        
        # Extract sibilant frequencies
        b, a = scipy.signal.butter(4, [low_freq, high_freq], btype='band')
        sibilant_signal = scipy.signal.filtfilt(b, a, audio)
        
        # Apply gentle compression to sibilants
        compressed_sibilants = np.sign(sibilant_signal) * np.power(np.abs(sibilant_signal), 0.8)
        
        # Subtract original sibilants and add compressed ones
        return audio - sibilant_signal + compressed_sibilants
    
    def _estimate_intelligibility(self, formant_energy: float, 
                                consonant_energy: float, vowel_energy: float) -> float:
        """Estimate speech intelligibility score"""
        # Simplified intelligibility estimation based on energy distribution
        total_energy = formant_energy + consonant_energy + vowel_energy
        
        if total_energy == 0:
            return 0.0
        
        # Balanced energy distribution indicates better intelligibility
        formant_ratio = formant_energy / total_energy
        consonant_ratio = consonant_energy / total_energy
        vowel_ratio = vowel_energy / total_energy
        
        # Optimal ratios for good intelligibility
        optimal_formant = 0.5
        optimal_consonant = 0.3
        optimal_vowel = 0.2
        
        # Calculate deviation from optimal
        deviation = (abs(formant_ratio - optimal_formant) + 
                    abs(consonant_ratio - optimal_consonant) + 
                    abs(vowel_ratio - optimal_vowel))
        
        # Convert to intelligibility score (0-1)
        intelligibility = max(0, 1 - deviation)
        return intelligibility

class AudioQualityAssessor:
    """Automatic audio quality assessment and improvement recommendations"""
    
    def __init__(self):
        self.sample_rate = 44100
        
    def assess_quality(self, audio: np.ndarray, sr: int) -> QualityAssessment:
        """Comprehensive audio quality assessment"""
        try:
            metrics = {}
            
            # Signal-to-noise ratio estimation
            metrics[QualityMetric.SNR] = self._estimate_snr(audio)
            
            # Total harmonic distortion estimation
            metrics[QualityMetric.THD] = self._estimate_thd(audio, sr)
            
            # Speech clarity assessment
            clarity_enhancer = SpeechClarityEnhancer()
            clarity_metrics = clarity_enhancer.analyze_speech_clarity(audio, sr)
            metrics[QualityMetric.CLARITY] = clarity_metrics['intelligibility_score']
            
            # Loudness assessment
            dynamic_optimizer = DynamicRangeOptimizer()
            dynamics = dynamic_optimizer.analyze_dynamics(audio, sr)
            metrics[QualityMetric.LOUDNESS] = self._normalize_loudness_score(dynamics['loudness_lufs'])
            
            # Dynamic range assessment
            metrics[QualityMetric.DYNAMIC_RANGE] = self._normalize_dynamic_range_score(dynamics['dynamic_range'])
            
            # Frequency balance assessment
            metrics[QualityMetric.FREQUENCY_BALANCE] = self._assess_frequency_balance(audio, sr)
            
            # Calculate overall quality score
            overall_score = self._calculate_overall_score(metrics)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(metrics)
            
            # Calculate processing confidence
            confidence = self._calculate_processing_confidence(metrics)
            
            return QualityAssessment(
                overall_score=overall_score,
                metrics=metrics,
                recommendations=recommendations,
                processing_confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error in quality assessment: {e}")
            raise
    
    def _estimate_snr(self, audio: np.ndarray) -> float:
        """Estimate signal-to-noise ratio"""
        # Simple SNR estimation using signal energy vs noise floor
        signal_power = np.mean(audio**2)
        
        # Estimate noise floor from quietest 10% of samples
        sorted_power = np.sort(audio**2)
        noise_floor = np.mean(sorted_power[:len(sorted_power)//10])
        
        if noise_floor > 0:
            snr_db = 10 * np.log10(signal_power / noise_floor)
            return max(0, min(1, (snr_db + 10) / 50))  # Normalize to 0-1
        
        return 1.0
    
    def _estimate_thd(self, audio: np.ndarray, sr: int) -> float:
        """Estimate total harmonic distortion"""
        # Simplified THD estimation
        # In practice, this would require more sophisticated analysis
        
        # Calculate spectral content
        fft_result = np.fft.fft(audio)
        magnitude = np.abs(fft_result)
        
        # Estimate distortion based on spectral characteristics
        # Higher frequency content relative to fundamentals indicates distortion
        fundamental_energy = np.sum(magnitude[:len(magnitude)//4])
        harmonic_energy = np.sum(magnitude[len(magnitude)//4:])
        
        if fundamental_energy > 0:
            thd_estimate = harmonic_energy / fundamental_energy
            return max(0, min(1, 1 - thd_estimate))  # Normalize to 0-1 (higher is better)
        
        return 1.0
    
    def _normalize_loudness_score(self, loudness_lufs: float) -> float:
        """Normalize loudness to quality score (0-1)"""
        # Optimal range around -23 LUFS for broadcast
        optimal_lufs = -23.0
        deviation = abs(loudness_lufs - optimal_lufs)
        
        # Score decreases with deviation from optimal
        score = max(0, 1 - deviation / 20)
        return score
    
    def _normalize_dynamic_range_score(self, dynamic_range: float) -> float:
        """Normalize dynamic range to quality score (0-1)"""
        # Good dynamic range is typically 20-40 dB
        if dynamic_range >= 20:
            return min(1.0, dynamic_range / 40)
        else:
            return dynamic_range / 20
    
    def _assess_frequency_balance(self, audio: np.ndarray, sr: int) -> float:
        """Assess frequency balance across spectrum"""
        # Analyze energy distribution across frequency bands
        stft = librosa.stft(audio, n_fft=2048, hop_length=512)
        magnitude = np.abs(stft)
        freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
        
        # Define frequency bands
        low_band = magnitude[(freqs >= 20) & (freqs < 250)]
        mid_band = magnitude[(freqs >= 250) & (freqs < 4000)]
        high_band = magnitude[(freqs >= 4000) & (freqs < sr//2)]
        
        # Calculate energy in each band
        low_energy = np.mean(low_band) if len(low_band) > 0 else 0
        mid_energy = np.mean(mid_band) if len(mid_band) > 0 else 0
        high_energy = np.mean(high_band) if len(high_band) > 0 else 0
        
        total_energy = low_energy + mid_energy + high_energy
        
        if total_energy > 0:
            # Calculate balance score based on energy distribution
            low_ratio = low_energy / total_energy
            mid_ratio = mid_energy / total_energy
            high_ratio = high_energy / total_energy
            
            # Ideal distribution: more energy in mid frequencies
            ideal_low, ideal_mid, ideal_high = 0.2, 0.6, 0.2
            
            deviation = (abs(low_ratio - ideal_low) + 
                        abs(mid_ratio - ideal_mid) + 
                        abs(high_ratio - ideal_high))
            
            balance_score = max(0, 1 - deviation)
            return balance_score
        
        return 0.5  # Neutral score if no energy detected
    
    def _calculate_overall_score(self, metrics: Dict[QualityMetric, float]) -> float:
        """Calculate weighted overall quality score"""
        weights = {
            QualityMetric.SNR: 0.25,
            QualityMetric.THD: 0.15,
            QualityMetric.CLARITY: 0.25,
            QualityMetric.LOUDNESS: 0.15,
            QualityMetric.DYNAMIC_RANGE: 0.1,
            QualityMetric.FREQUENCY_BALANCE: 0.1
        }
        
        weighted_sum = sum(metrics[metric] * weights[metric] 
                          for metric in metrics if metric in weights)
        
        return weighted_sum
    
    def _generate_recommendations(self, metrics: Dict[QualityMetric, float]) -> List[str]:
        """Generate improvement recommendations based on quality metrics"""
        recommendations = []
        
        if metrics[QualityMetric.SNR] < 0.7:
            recommendations.append("Apply noise reduction to improve signal-to-noise ratio")
        
        if metrics[QualityMetric.THD] < 0.8:
            recommendations.append("Reduce distortion through dynamic range optimization")
        
        if metrics[QualityMetric.CLARITY] < 0.7:
            recommendations.append("Enhance speech clarity with formant and consonant processing")
        
        if metrics[QualityMetric.LOUDNESS] < 0.8:
            recommendations.append("Normalize loudness to broadcast standards")
        
        if metrics[QualityMetric.DYNAMIC_RANGE] < 0.6:
            recommendations.append("Optimize dynamic range with gentle compression")
        
        if metrics[QualityMetric.FREQUENCY_BALANCE] < 0.7:
            recommendations.append("Apply spectral enhancement to balance frequency content")
        
        if not recommendations:
            recommendations.append("Audio quality is good - minor enhancements may still be beneficial")
        
        return recommendations
    
    def _calculate_processing_confidence(self, metrics: Dict[QualityMetric, float]) -> float:
        """Calculate confidence in processing recommendations"""
        # Higher confidence when issues are clearly identified
        avg_score = sum(metrics.values()) / len(metrics)
        
        # Lower average scores indicate clearer improvement opportunities
        confidence = 1.0 - avg_score
        
        # Ensure confidence is in reasonable range
        return max(0.3, min(0.95, confidence))

class IntelligentAudioEnhancer:
    """Main intelligent audio enhancement system with user control"""
    
    def __init__(self):
        self.spectral_enhancer = SpectralEnhancer()
        self.dynamic_optimizer = DynamicRangeOptimizer()
        self.clarity_enhancer = SpeechClarityEnhancer()
        self.quality_assessor = AudioQualityAssessor()
        
    def enhance_audio(self, audio: np.ndarray, sr: int, 
                     mode: EnhancementMode = EnhancementMode.AUTOMATIC,
                     user_preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Comprehensive audio enhancement with user control
        
        Args:
            audio: Input audio signal
            sr: Sample rate
            mode: Enhancement mode
            user_preferences: User-defined enhancement preferences
            
        Returns:
            Dictionary containing enhanced audio and processing information
        """
        try:
            logger.info(f"Starting intelligent audio enhancement in {mode.value} mode")
            
            # Initial quality assessment
            initial_assessment = self.quality_assessor.assess_quality(audio, sr)
            
            # Determine enhancement strategy based on mode and assessment
            enhancement_config = self._create_enhancement_config(
                mode, initial_assessment, user_preferences
            )
            
            enhanced_audio = audio.copy()
            processing_steps = []
            
            # Apply spectral enhancement
            if enhancement_config.get('apply_spectral_enhancement', True):
                spectral_config = enhancement_config['spectral_config']
                enhanced_audio = self.spectral_enhancer.enhance_spectrum(
                    enhanced_audio, sr, spectral_config
                )
                processing_steps.append("Spectral Enhancement")
            
            # Apply dynamic range optimization
            if enhancement_config.get('apply_dynamic_optimization', True):
                dynamic_config = enhancement_config['dynamic_config']
                enhanced_audio = self.dynamic_optimizer.optimize_dynamic_range(
                    enhanced_audio, sr, dynamic_config
                )
                processing_steps.append("Dynamic Range Optimization")
            
            # Apply speech clarity enhancement
            if enhancement_config.get('apply_clarity_enhancement', True):
                clarity_config = enhancement_config['clarity_config']
                enhanced_audio = self.clarity_enhancer.enhance_speech_clarity(
                    enhanced_audio, sr, clarity_config
                )
                processing_steps.append("Speech Clarity Enhancement")
            
            # Final quality assessment
            final_assessment = self.quality_assessor.assess_quality(enhanced_audio, sr)
            
            # Calculate improvement metrics
            improvement = self._calculate_improvement(initial_assessment, final_assessment)
            
            logger.info(f"Audio enhancement completed. Overall improvement: {improvement:.2f}")
            
            return {
                'enhanced_audio': enhanced_audio,
                'initial_assessment': initial_assessment,
                'final_assessment': final_assessment,
                'improvement': improvement,
                'processing_steps': processing_steps,
                'enhancement_config': enhancement_config
            }
            
        except Exception as e:
            logger.error(f"Error in intelligent audio enhancement: {e}")
            raise
    
    def _create_enhancement_config(self, mode: EnhancementMode, 
                                 assessment: QualityAssessment,
                                 user_preferences: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Create enhancement configuration based on mode and assessment"""
        
        # Base configurations for different modes
        if mode == EnhancementMode.SPEECH_FOCUSED:
            config = self._get_speech_focused_config()
        elif mode == EnhancementMode.MUSIC_FOCUSED:
            config = self._get_music_focused_config()
        elif mode == EnhancementMode.BROADCAST:
            config = self._get_broadcast_config()
        else:  # AUTOMATIC or CUSTOM
            config = self._get_automatic_config(assessment)
        
        # Apply user preferences if provided
        if user_preferences:
            config = self._apply_user_preferences(config, user_preferences)
        
        return config
    
    def _get_speech_focused_config(self) -> Dict[str, Any]:
        """Configuration optimized for speech content"""
        return {
            'apply_spectral_enhancement': True,
            'apply_dynamic_optimization': True,
            'apply_clarity_enhancement': True,
            'spectral_config': SpectralEnhancementConfig(
                frequency_bands=[(300, 1000), (1000, 3400), (3400, 8000)],
                enhancement_factors=[1.1, 1.3, 1.2],
                smoothing_factor=0.2,
                adaptive_processing=True
            ),
            'dynamic_config': DynamicRangeConfig(
                target_lufs=-23.0,
                compression_ratio=2.5,
                attack_time=0.005,
                release_time=0.15
            ),
            'clarity_config': SpeechClarityConfig(
                formant_enhancement=True,
                consonant_boost=True,
                vowel_clarity=True,
                sibilance_control=True,
                intelligibility_target=0.9
            )
        }
    
    def _get_music_focused_config(self) -> Dict[str, Any]:
        """Configuration optimized for music content"""
        return {
            'apply_spectral_enhancement': True,
            'apply_dynamic_optimization': True,
            'apply_clarity_enhancement': False,
            'spectral_config': SpectralEnhancementConfig(
                frequency_bands=[(20, 200), (200, 2000), (2000, 8000), (8000, 20000)],
                enhancement_factors=[1.05, 1.1, 1.15, 1.1],
                smoothing_factor=0.3,
                adaptive_processing=True
            ),
            'dynamic_config': DynamicRangeConfig(
                target_lufs=-16.0,
                compression_ratio=1.8,
                attack_time=0.01,
                release_time=0.3
            )
        }
    
    def _get_broadcast_config(self) -> Dict[str, Any]:
        """Configuration for broadcast compliance"""
        return {
            'apply_spectral_enhancement': True,
            'apply_dynamic_optimization': True,
            'apply_clarity_enhancement': True,
            'spectral_config': SpectralEnhancementConfig(
                frequency_bands=[(100, 1000), (1000, 4000), (4000, 10000)],
                enhancement_factors=[1.0, 1.2, 1.1],
                smoothing_factor=0.25,
                adaptive_processing=True
            ),
            'dynamic_config': DynamicRangeConfig(
                target_lufs=-23.0,
                max_peak=-1.0,
                compression_ratio=3.0,
                attack_time=0.003,
                release_time=0.1
            ),
            'clarity_config': SpeechClarityConfig(
                formant_enhancement=True,
                consonant_boost=True,
                vowel_clarity=True,
                sibilance_control=True,
                intelligibility_target=0.85
            )
        }
    
    def _get_automatic_config(self, assessment: QualityAssessment) -> Dict[str, Any]:
        """Automatic configuration based on quality assessment"""
        # Analyze assessment to determine optimal configuration
        metrics = assessment.metrics
        
        # Determine enhancement intensity based on quality scores
        spectral_intensity = 1.0 + (1.0 - metrics.get(QualityMetric.FREQUENCY_BALANCE, 0.8)) * 0.5
        dynamic_intensity = 1.0 + (1.0 - metrics.get(QualityMetric.DYNAMIC_RANGE, 0.8)) * 0.3
        clarity_intensity = 1.0 + (1.0 - metrics.get(QualityMetric.CLARITY, 0.8)) * 0.4
        
        return {
            'apply_spectral_enhancement': metrics.get(QualityMetric.FREQUENCY_BALANCE, 1.0) < 0.8,
            'apply_dynamic_optimization': metrics.get(QualityMetric.DYNAMIC_RANGE, 1.0) < 0.8,
            'apply_clarity_enhancement': metrics.get(QualityMetric.CLARITY, 1.0) < 0.8,
            'spectral_config': SpectralEnhancementConfig(
                frequency_bands=[(200, 1000), (1000, 4000), (4000, 12000)],
                enhancement_factors=[spectral_intensity, spectral_intensity * 1.2, spectral_intensity],
                smoothing_factor=0.25,
                adaptive_processing=True
            ),
            'dynamic_config': DynamicRangeConfig(
                target_lufs=-20.0,
                compression_ratio=2.0 + dynamic_intensity,
                attack_time=0.005,
                release_time=0.2
            ),
            'clarity_config': SpeechClarityConfig(
                formant_enhancement=True,
                consonant_boost=clarity_intensity > 1.2,
                vowel_clarity=True,
                sibilance_control=True,
                intelligibility_target=0.8
            )
        }
    
    def _apply_user_preferences(self, config: Dict[str, Any], 
                              preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Apply user preferences to enhancement configuration"""
        
        # Allow users to override enhancement intensities
        if 'spectral_intensity' in preferences:
            intensity = preferences['spectral_intensity']
            if 'spectral_config' in config:
                factors = config['spectral_config'].enhancement_factors
                config['spectral_config'].enhancement_factors = [f * intensity for f in factors]
        
        if 'dynamic_intensity' in preferences:
            intensity = preferences['dynamic_intensity']
            if 'dynamic_config' in config:
                config['dynamic_config'].compression_ratio *= intensity
        
        if 'clarity_intensity' in preferences:
            intensity = preferences['clarity_intensity']
            if 'clarity_config' in config:
                config['clarity_config'].intelligibility_target = min(1.0, 
                    config['clarity_config'].intelligibility_target * intensity)
        
        # Allow users to disable specific enhancements
        if 'disable_spectral' in preferences and preferences['disable_spectral']:
            config['apply_spectral_enhancement'] = False
        
        if 'disable_dynamic' in preferences and preferences['disable_dynamic']:
            config['apply_dynamic_optimization'] = False
        
        if 'disable_clarity' in preferences and preferences['disable_clarity']:
            config['apply_clarity_enhancement'] = False
        
        return config
    
    def _calculate_improvement(self, initial: QualityAssessment, 
                             final: QualityAssessment) -> float:
        """Calculate overall improvement score"""
        return final.overall_score - initial.overall_score

# Example usage and testing functions
def create_test_audio(duration: float = 5.0, sr: int = 44100) -> np.ndarray:
    """Create test audio signal for demonstration"""
    t = np.linspace(0, duration, int(duration * sr))
    
    # Create a complex signal with speech-like characteristics
    fundamental = 200  # Hz
    signal = (np.sin(2 * np.pi * fundamental * t) * 0.3 +
             np.sin(2 * np.pi * fundamental * 2 * t) * 0.2 +
             np.sin(2 * np.pi * fundamental * 3 * t) * 0.1)
    
    # Add some noise
    noise = np.random.normal(0, 0.05, len(signal))
    signal += noise
    
    # Add some dynamic variation
    envelope = 0.5 + 0.5 * np.sin(2 * np.pi * 0.5 * t)
    signal *= envelope
    
    return signal

def demonstrate_enhancement():
    """Demonstrate the intelligent audio enhancement system"""
    print("Intelligent Audio Enhancement System Demo")
    print("=" * 50)
    
    # Create test audio
    test_audio = create_test_audio()
    sr = 44100
    
    # Initialize enhancer
    enhancer = IntelligentAudioEnhancer()
    
    # Test different enhancement modes
    modes = [EnhancementMode.AUTOMATIC, EnhancementMode.SPEECH_FOCUSED, 
             EnhancementMode.BROADCAST]
    
    for mode in modes:
        print(f"\nTesting {mode.value} mode:")
        print("-" * 30)
        
        try:
            result = enhancer.enhance_audio(test_audio, sr, mode)
            
            initial = result['initial_assessment']
            final = result['final_assessment']
            improvement = result['improvement']
            
            print(f"Initial quality score: {initial.overall_score:.3f}")
            print(f"Final quality score: {final.overall_score:.3f}")
            print(f"Improvement: {improvement:.3f}")
            print(f"Processing steps: {', '.join(result['processing_steps'])}")
            print(f"Recommendations: {len(final.recommendations)} items")
            
        except Exception as e:
            print(f"Error in {mode.value} mode: {e}")

if __name__ == "__main__":
    demonstrate_enhancement()