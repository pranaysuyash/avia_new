"""
Advanced Audio Processing Capabilities
Extended features for the Audio Enhancement Pipeline
"""

import numpy as np
import librosa
import soundfile as sf
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import logging
from scipy import signal
from scipy.fft import fft, fftfreq
import noisereduce as nr
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
import tempfile
import os

logger = logging.getLogger(__name__)

@dataclass
class SpectralAnalysis:
    """Detailed spectral analysis results"""
    frequency_spectrum: np.ndarray
    magnitude_spectrum: np.ndarray
    phase_spectrum: np.ndarray
    dominant_frequencies: List[float]
    harmonic_content: float
    spectral_flatness: float
    spectral_entropy: float
    spectral_kurtosis: float

@dataclass
class PsychoacousticMetrics:
    """Psychoacoustic analysis metrics"""
    perceived_loudness: float  # Zwicker loudness
    sharpness: float  # Zwicker sharpness
    roughness: float  # Sensory roughness
    fluctuation_strength: float  # Temporal variation
    tonality: float  # Tonal vs noise content
    pleasantness_score: float  # Overall pleasantness estimation

@dataclass 
class AudioFingerprint:
    """Audio fingerprint for similarity matching"""
    chromagram: np.ndarray
    mfcc_sequence: np.ndarray
    spectral_hash: str
    tempo: float
    key_signature: str
    time_signature: str

class AdvancedAudioProcessor:
    """Advanced audio processing capabilities extending the basic enhancement pipeline"""
    
    def __init__(self):
        self.sample_rate = 44100
        self.fft_size = 2048
        self.hop_length = 512
        
    def spectral_analysis(self, audio_path: str) -> SpectralAnalysis:
        """Perform detailed spectral analysis"""
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Compute FFT
            fft_result = fft(y)
            freqs = fftfreq(len(y), 1/sr)
            
            # Get magnitude and phase
            magnitude = np.abs(fft_result)
            phase = np.angle(fft_result)
            
            # Find dominant frequencies
            peaks, _ = signal.find_peaks(magnitude[:len(magnitude)//2], height=np.max(magnitude)*0.1)
            dominant_freqs = freqs[peaks][:10].tolist()  # Top 10 peaks
            
            # Compute spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
            spectral_flatness = librosa.feature.spectral_flatness(y=y)
            
            # Harmonic content
            harmonic, percussive = librosa.effects.hpss(y)
            harmonic_ratio = np.sum(np.abs(harmonic)) / np.sum(np.abs(y))
            
            # Spectral entropy
            power_spectrum = magnitude ** 2
            normalized_spectrum = power_spectrum / np.sum(power_spectrum)
            spectral_entropy = -np.sum(normalized_spectrum * np.log2(normalized_spectrum + 1e-10))
            
            # Spectral kurtosis
            spectral_kurtosis = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))
            
            return SpectralAnalysis(
                frequency_spectrum=freqs[:len(freqs)//2],
                magnitude_spectrum=magnitude[:len(magnitude)//2],
                phase_spectrum=phase[:len(phase)//2],
                dominant_frequencies=dominant_freqs,
                harmonic_content=float(harmonic_ratio),
                spectral_flatness=float(np.mean(spectral_flatness)),
                spectral_entropy=float(spectral_entropy),
                spectral_kurtosis=float(spectral_kurtosis)
            )
            
        except Exception as e:
            logger.error(f"Spectral analysis failed: {e}")
            raise
    
    def psychoacoustic_analysis(self, audio_path: str) -> PsychoacousticMetrics:
        """Analyze psychoacoustic properties"""
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Perceived loudness (simplified Zwicker model)
            rms_energy = np.sqrt(np.mean(y**2))
            perceived_loudness = 20 * np.log10(rms_energy + 1e-10) + 94  # dB SPL approximation
            
            # Sharpness (high frequency content)
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
            sharpness = np.mean(spectral_centroids) / 1000  # Normalized to kHz
            
            # Roughness (amplitude modulation)
            envelope = np.abs(signal.hilbert(y))
            roughness = np.std(np.diff(envelope))
            
            # Fluctuation strength
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            fluctuation = len(beats) / (len(y) / sr)  # Beats per second
            
            # Tonality (harmonic vs noise)
            harmonic, percussive = librosa.effects.hpss(y)
            tonality = np.sum(np.abs(harmonic)) / (np.sum(np.abs(harmonic)) + np.sum(np.abs(percussive)))
            
            # Pleasantness score (heuristic combination)
            pleasantness = (
                (1.0 - min(abs(perceived_loudness - 70) / 50, 1.0)) * 0.3 +  # Optimal loudness ~70 dB
                (1.0 - min(sharpness / 5, 1.0)) * 0.2 +  # Lower sharpness preferred
                (1.0 - min(roughness * 10, 1.0)) * 0.2 +  # Lower roughness preferred
                tonality * 0.3  # Higher tonality preferred
            ) * 100
            
            return PsychoacousticMetrics(
                perceived_loudness=float(perceived_loudness),
                sharpness=float(sharpness),
                roughness=float(roughness),
                fluctuation_strength=float(fluctuation),
                tonality=float(tonality),
                pleasantness_score=float(pleasantness)
            )
            
        except Exception as e:
            logger.error(f"Psychoacoustic analysis failed: {e}")
            raise
    
    def adaptive_noise_profiling(self, audio_path: str) -> Dict[str, Any]:
        """Create adaptive noise profile for intelligent reduction"""
        try:
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Segment audio into quiet and active parts
            intervals = librosa.effects.split(y, top_db=20)
            
            # Analyze noise in quiet segments
            noise_profile = []
            for i in range(len(intervals)):
                if i == 0:
                    # Before first active segment
                    segment = y[:intervals[0][0]]
                elif i == len(intervals):
                    # After last active segment
                    segment = y[intervals[-1][1]:]
                else:
                    # Between active segments
                    segment = y[intervals[i-1][1]:intervals[i][0]]
                
                if len(segment) > 0:
                    noise_spectrum = np.abs(fft(segment))
                    noise_profile.append(noise_spectrum)
            
            # Average noise profile
            if noise_profile:
                avg_noise_profile = np.mean(noise_profile, axis=0)
            else:
                avg_noise_profile = np.zeros(len(y))
            
            # Classify noise type
            noise_characteristics = self._classify_noise(avg_noise_profile, sr)
            
            return {
                'noise_profile': avg_noise_profile.tolist()[:1000],  # Limit size
                'noise_type': noise_characteristics['type'],
                'noise_color': noise_characteristics['color'],
                'adaptive_threshold': noise_characteristics['threshold'],
                'frequency_bands': noise_characteristics['bands']
            }
            
        except Exception as e:
            logger.error(f"Adaptive noise profiling failed: {e}")
            raise
    
    def _classify_noise(self, noise_spectrum: np.ndarray, sr: int) -> Dict[str, Any]:
        """Classify noise type based on spectral characteristics"""
        freqs = fftfreq(len(noise_spectrum), 1/sr)
        
        # Analyze spectral slope
        positive_freqs = freqs[:len(freqs)//2]
        positive_spectrum = noise_spectrum[:len(noise_spectrum)//2]
        
        # Fit linear regression to log-log plot
        log_freqs = np.log10(positive_freqs[1:1000] + 1e-10)
        log_spectrum = np.log10(positive_spectrum[1:1000] + 1e-10)
        slope = np.polyfit(log_freqs, log_spectrum, 1)[0]
        
        # Classify based on slope
        if slope > -0.5:
            noise_color = "white"
            noise_type = "broadband"
        elif slope > -1.5:
            noise_color = "pink"
            noise_type = "natural"
        elif slope > -2.5:
            noise_color = "brown"
            noise_type = "low_frequency"
        else:
            noise_color = "colored"
            noise_type = "structured"
        
        # Find dominant frequency bands
        peaks, _ = signal.find_peaks(positive_spectrum, height=np.max(positive_spectrum)*0.3)
        dominant_bands = positive_freqs[peaks].tolist() if len(peaks) > 0 else []
        
        return {
            'type': noise_type,
            'color': noise_color,
            'threshold': float(np.percentile(positive_spectrum, 75)),
            'bands': dominant_bands[:5]  # Top 5 bands
        }
    
    def harmonic_enhancement(self, audio_path: str, output_path: str, 
                            enhancement_factor: float = 1.5) -> str:
        """Enhance harmonic content while preserving natural timbre"""
        try:
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Separate harmonic and percussive components
            harmonic, percussive = librosa.effects.hpss(y, margin=3.0)
            
            # Enhance harmonics
            enhanced_harmonic = harmonic * enhancement_factor
            
            # Apply soft clipping to prevent distortion
            enhanced_harmonic = np.tanh(enhanced_harmonic)
            
            # Recombine with original percussive
            enhanced_audio = enhanced_harmonic + percussive
            
            # Normalize
            enhanced_audio = enhanced_audio / np.max(np.abs(enhanced_audio))
            
            # Save
            sf.write(output_path, enhanced_audio, sr)
            return output_path
            
        except Exception as e:
            logger.error(f"Harmonic enhancement failed: {e}")
            raise
    
    def stereo_widening(self, audio_path: str, output_path: str, 
                        width_factor: float = 1.5) -> str:
        """Apply stereo widening effect"""
        try:
            # Load stereo audio
            y, sr = librosa.load(audio_path, sr=self.sample_rate, mono=False)
            
            if len(y.shape) == 1:
                # Mono audio, create pseudo-stereo
                y_stereo = np.array([y, y])
            else:
                y_stereo = y
            
            # Extract mid/side
            mid = (y_stereo[0] + y_stereo[1]) / 2
            side = (y_stereo[0] - y_stereo[1]) / 2
            
            # Enhance side signal
            side_enhanced = side * width_factor
            
            # Reconstruct stereo
            left = mid + side_enhanced
            right = mid - side_enhanced
            
            # Normalize
            stereo_enhanced = np.array([left, right])
            stereo_enhanced = stereo_enhanced / np.max(np.abs(stereo_enhanced))
            
            # Save
            sf.write(output_path, stereo_enhanced.T, sr)
            return output_path
            
        except Exception as e:
            logger.error(f"Stereo widening failed: {e}")
            raise
    
    def transient_shaping(self, audio_path: str, output_path: str,
                         attack_factor: float = 1.2,
                         sustain_factor: float = 0.8) -> str:
        """Shape transients for punchier or smoother sound"""
        try:
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Detect onsets (transients)
            onset_frames = librosa.onset.onset_detect(y=y, sr=sr, units='samples')
            
            # Create envelope
            envelope = np.ones_like(y)
            
            # Shape attack portions
            for onset in onset_frames:
                attack_len = int(0.01 * sr)  # 10ms attack
                if onset + attack_len < len(y):
                    attack_curve = np.linspace(1, attack_factor, attack_len)
                    envelope[onset:onset+attack_len] *= attack_curve
            
            # Apply sustain shaping
            sustain_mask = np.ones_like(y)
            for i in range(len(onset_frames)-1):
                start = onset_frames[i] + int(0.01 * sr)
                end = onset_frames[i+1]
                if start < end:
                    sustain_mask[start:end] *= sustain_factor
            
            # Apply shaping
            shaped_audio = y * envelope * sustain_mask
            
            # Normalize
            shaped_audio = shaped_audio / np.max(np.abs(shaped_audio))
            
            # Save
            sf.write(output_path, shaped_audio, sr)
            return output_path
            
        except Exception as e:
            logger.error(f"Transient shaping failed: {e}")
            raise
    
    def audio_fingerprinting(self, audio_path: str) -> AudioFingerprint:
        """Generate audio fingerprint for similarity matching"""
        try:
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Chromagram
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            
            # MFCCs
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            
            # Tempo and beat
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            
            # Key detection (simplified)
            chroma_mean = np.mean(chroma, axis=1)
            key_idx = np.argmax(chroma_mean)
            keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            estimated_key = keys[key_idx]
            
            # Time signature estimation (simplified)
            beat_times = librosa.frames_to_time(beats, sr=sr)
            if len(beat_times) > 1:
                beat_intervals = np.diff(beat_times)
                avg_interval = np.mean(beat_intervals)
                if avg_interval < 0.4:
                    time_sig = "4/4"
                elif avg_interval < 0.6:
                    time_sig = "3/4"
                else:
                    time_sig = "6/8"
            else:
                time_sig = "4/4"
            
            # Create spectral hash
            spectral_hash = self._compute_spectral_hash(y, sr)
            
            return AudioFingerprint(
                chromagram=chroma,
                mfcc_sequence=mfccs,
                spectral_hash=spectral_hash,
                tempo=float(tempo),
                key_signature=estimated_key,
                time_signature=time_sig
            )
            
        except Exception as e:
            logger.error(f"Audio fingerprinting failed: {e}")
            raise
    
    def _compute_spectral_hash(self, y: np.ndarray, sr: int) -> str:
        """Compute a spectral hash for audio identification"""
        # Compute spectrogram
        D = librosa.stft(y)
        magnitude = np.abs(D)
        
        # Reduce to binary hash
        mean_magnitude = np.mean(magnitude, axis=1)
        binary_hash = (mean_magnitude > np.median(mean_magnitude)).astype(int)
        
        # Convert to hex string
        hash_str = ''.join([str(b) for b in binary_hash[:64]])
        return hex(int(hash_str, 2))[2:].zfill(16)
    
    def intelligent_eq(self, audio_path: str, output_path: str, 
                      target_profile: str = "balanced") -> str:
        """Apply intelligent EQ based on content analysis"""
        try:
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Analyze current spectral profile
            stft = librosa.stft(y)
            magnitude = np.abs(stft)
            avg_spectrum = np.mean(magnitude, axis=1)
            
            # Define target profiles
            profiles = {
                "balanced": lambda f: 1.0,
                "bright": lambda f: 1.0 + 0.5 * (f / (sr/2)),
                "warm": lambda f: 1.0 + 0.5 * (1 - f / (sr/2)),
                "vocal": lambda f: 1.0 + 0.3 * np.exp(-((f-3000)**2)/(2*1000**2)),
                "bass_boost": lambda f: 1.0 + 0.5 * np.exp(-((f-100)**2)/(2*50**2))
            }
            
            # Get target curve
            freqs = librosa.fft_frequencies(sr=sr)
            target_curve = np.array([profiles[target_profile](f) for f in freqs])
            
            # Compute correction curve
            current_curve = avg_spectrum / np.max(avg_spectrum)
            correction = target_curve / (current_curve + 1e-10)
            correction = np.clip(correction, 0.1, 10)  # Limit correction range
            
            # Apply EQ
            stft_corrected = stft * correction[:, np.newaxis]
            y_corrected = librosa.istft(stft_corrected)
            
            # Normalize
            y_corrected = y_corrected / np.max(np.abs(y_corrected))
            
            # Save
            sf.write(output_path, y_corrected, sr)
            return output_path
            
        except Exception as e:
            logger.error(f"Intelligent EQ failed: {e}")
            raise
    
    def multiband_compression(self, audio_path: str, output_path: str,
                            bands: List[Tuple[float, float, float]] = None) -> str:
        """Apply multiband compression for professional mastering"""
        try:
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Default frequency bands and compression ratios
            if bands is None:
                bands = [
                    (0, 200, 2.0),      # Sub-bass: gentle compression
                    (200, 800, 3.0),    # Bass/low-mids: moderate compression
                    (800, 4000, 4.0),   # Mids: standard compression
                    (4000, 12000, 3.0), # Highs: moderate compression
                    (12000, 20000, 2.0) # Air: gentle compression
                ]
            
            # Process each band
            compressed_bands = []
            for low_freq, high_freq, ratio in bands:
                # Design bandpass filter
                nyquist = sr / 2
                low = low_freq / nyquist
                high = high_freq / nyquist
                
                if low > 0 and high < 1:
                    sos = signal.butter(4, [low, high], btype='band', output='sos')
                elif low == 0:
                    sos = signal.butter(4, high, btype='low', output='sos')
                else:
                    sos = signal.butter(4, low, btype='high', output='sos')
                
                # Filter band
                band_signal = signal.sosfilt(sos, y)
                
                # Apply compression
                threshold = np.percentile(np.abs(band_signal), 85)
                compressed = np.where(
                    np.abs(band_signal) > threshold,
                    np.sign(band_signal) * (threshold + (np.abs(band_signal) - threshold) / ratio),
                    band_signal
                )
                
                compressed_bands.append(compressed)
            
            # Sum compressed bands
            y_compressed = np.sum(compressed_bands, axis=0)
            
            # Apply final limiting
            y_compressed = np.tanh(y_compressed * 0.9)
            
            # Save
            sf.write(output_path, y_compressed, sr)
            return output_path
            
        except Exception as e:
            logger.error(f"Multiband compression failed: {e}")
            raise

# Export advanced capabilities
__all__ = [
    'AdvancedAudioProcessor',
    'SpectralAnalysis',
    'PsychoacousticMetrics',
    'AudioFingerprint'
]