"""
Advanced Audio Preprocessing System with Librosa

This module provides comprehensive audio preprocessing capabilities including
spectral analysis, audio feature extraction, pitch detection, fundamental frequency
analysis, audio fingerprinting, tempo and rhythm analysis, and audio similarity
comparison and clustering.

Features:
- Spectral analysis and audio feature extraction
- Pitch detection and fundamental frequency analysis
- Audio fingerprinting for duplicate detection
- Tempo and rhythm analysis capabilities
- Audio similarity comparison and clustering
- Advanced audio preprocessing pipeline
- Real-time audio processing capabilities
- Batch processing for large audio datasets
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
import hashlib
import pickle
import warnings
warnings.filterwarnings("ignore")

# Audio processing
import librosa
import librosa.display
import soundfile as sf
from scipy import signal, stats
from scipy.spatial.distance import cosine, euclidean
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster

# Machine learning
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors

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
class AudioFeatures:
    """Comprehensive audio features extracted from audio signal"""
    # Basic properties
    duration: float
    sample_rate: int
    channels: int
    
    # Spectral features
    spectral_centroid: np.ndarray
    spectral_bandwidth: np.ndarray
    spectral_rolloff: np.ndarray
    spectral_contrast: np.ndarray
    spectral_flatness: np.ndarray
    
    # Rhythm features
    tempo: float
    beat_frames: np.ndarray
    onset_frames: np.ndarray
    
    # Pitch features
    fundamental_frequency: np.ndarray
    pitch_confidence: np.ndarray
    chroma_features: np.ndarray
    
    # MFCC features
    mfcc: np.ndarray
    delta_mfcc: np.ndarray
    delta2_mfcc: np.ndarray
    
    # Zero crossing rate
    zcr: np.ndarray
    
    # RMS energy
    rms: np.ndarray
    
    # Tonnetz features
    tonnetz: np.ndarray
    
    # Mel spectrogram
    mel_spectrogram: np.ndarray
    
    # Audio fingerprint
    fingerprint: str
    
    # Statistical summaries
    feature_statistics: Dict[str, Dict[str, float]]

@dataclass
class AudioSimilarity:
    """Audio similarity comparison result"""
    audio1_path: str
    audio2_path: str
    similarity_score: float
    distance_metrics: Dict[str, float]
    feature_correlations: Dict[str, float]
    is_duplicate: bool
    confidence: float

@dataclass
class AudioCluster:
    """Audio clustering result"""
    cluster_id: int
    audio_files: List[str]
    centroid_features: Dict[str, float]
    cluster_size: int
    intra_cluster_similarity: float
    representative_audio: str

class SpectralAnalyzer:
    """Advanced spectral analysis for audio signals"""
    
    def __init__(self, sample_rate: int = 22050, hop_length: int = 512, n_fft: int = 2048):
        self.sample_rate = sample_rate
        self.hop_length = hop_length
        self.n_fft = n_fft
        self.n_mels = 128
        self.n_mfcc = 13
        self.n_chroma = 12
    
    def extract_spectral_features(self, audio_path: str) -> Dict[str, np.ndarray]:
        """Extract comprehensive spectral features from audio"""
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Spectral centroid
            spectral_centroid = librosa.feature.spectral_centroid(
                y=y, sr=sr, hop_length=self.hop_length
            )[0]
            
            # Spectral bandwidth
            spectral_bandwidth = librosa.feature.spectral_bandwidth(
                y=y, sr=sr, hop_length=self.hop_length
            )[0]
            
            # Spectral rolloff
            spectral_rolloff = librosa.feature.spectral_rolloff(
                y=y, sr=sr, hop_length=self.hop_length
            )[0]
            
            # Spectral contrast
            spectral_contrast = librosa.feature.spectral_contrast(
                y=y, sr=sr, hop_length=self.hop_length
            )
            
            # Spectral flatness
            spectral_flatness = librosa.feature.spectral_flatness(
                y=y, hop_length=self.hop_length
            )[0]
            
            # Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(
                y, frame_length=self.n_fft, hop_length=self.hop_length
            )[0]
            
            # RMS energy
            rms = librosa.feature.rms(
                y=y, frame_length=self.n_fft, hop_length=self.hop_length
            )[0]
            
            return {
                'spectral_centroid': spectral_centroid,
                'spectral_bandwidth': spectral_bandwidth,
                'spectral_rolloff': spectral_rolloff,
                'spectral_contrast': spectral_contrast,
                'spectral_flatness': spectral_flatness,
                'zero_crossing_rate': zcr,
                'rms_energy': rms
            }
            
        except Exception as e:
            logger.error(f"Error extracting spectral features: {e}")
            return {}
    
    def compute_spectrogram(self, audio_path: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Compute various spectrograms"""
        try:
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Short-time Fourier transform
            stft = librosa.stft(y, hop_length=self.hop_length, n_fft=self.n_fft)
            magnitude = np.abs(stft)
            
            # Mel spectrogram
            mel_spec = librosa.feature.melspectrogram(
                y=y, sr=sr, n_mels=self.n_mels, hop_length=self.hop_length
            )
            
            # Log-mel spectrogram
            log_mel_spec = librosa.power_to_db(mel_spec, ref=np.max)
            
            return magnitude, mel_spec, log_mel_spec
            
        except Exception as e:
            logger.error(f"Error computing spectrogram: {e}")
            return np.array([]), np.array([]), np.array([])
    
    def analyze_harmonic_percussive(self, audio_path: str) -> Tuple[np.ndarray, np.ndarray]:
        """Separate harmonic and percussive components"""
        try:
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Harmonic-percussive separation
            y_harmonic, y_percussive = librosa.effects.hpss(y)
            
            return y_harmonic, y_percussive
            
        except Exception as e:
            logger.error(f"Error in harmonic-percussive analysis: {e}")
            return np.array([]), np.array([])

class PitchAnalyzer:
    """Advanced pitch detection and fundamental frequency analysis"""
    
    def __init__(self, sample_rate: int = 22050, hop_length: int = 512):
        self.sample_rate = sample_rate
        self.hop_length = hop_length
        self.fmin = 50.0  # Minimum frequency (Hz)
        self.fmax = 2000.0  # Maximum frequency (Hz)
    
    def extract_pitch_features(self, audio_path: str) -> Dict[str, np.ndarray]:
        """Extract comprehensive pitch-related features"""
        try:
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Fundamental frequency using piptrack
            pitches, magnitudes = librosa.piptrack(
                y=y, sr=sr, hop_length=self.hop_length,
                fmin=self.fmin, fmax=self.fmax
            )
            
            # Extract fundamental frequency
            f0 = []
            confidence = []
            
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                conf = magnitudes[index, t]
                
                if pitch > 0:
                    f0.append(pitch)
                    confidence.append(conf)
                else:
                    f0.append(0)
                    confidence.append(0)
            
            f0 = np.array(f0)
            confidence = np.array(confidence)
            
            # Chroma features
            chroma = librosa.feature.chroma_stft(
                y=y, sr=sr, hop_length=self.hop_length
            )
            
            # Tonnetz features (harmonic network)
            tonnetz = librosa.feature.tonnetz(
                y=librosa.effects.harmonic(y), sr=sr
            )
            
            return {
                'fundamental_frequency': f0,
                'pitch_confidence': confidence,
                'chroma_features': chroma,
                'tonnetz_features': tonnetz
            }
            
        except Exception as e:
            logger.error(f"Error extracting pitch features: {e}")
            return {}
    
    def analyze_pitch_contour(self, audio_path: str) -> Dict[str, Any]:
        """Analyze pitch contour characteristics"""
        try:
            pitch_features = self.extract_pitch_features(audio_path)
            f0 = pitch_features.get('fundamental_frequency', np.array([]))
            
            if len(f0) == 0:
                return {}
            
            # Remove zero values for analysis
            f0_nonzero = f0[f0 > 0]
            
            if len(f0_nonzero) == 0:
                return {}
            
            # Pitch statistics
            pitch_mean = np.mean(f0_nonzero)
            pitch_std = np.std(f0_nonzero)
            pitch_range = np.ptp(f0_nonzero)
            pitch_median = np.median(f0_nonzero)
            
            # Pitch stability (coefficient of variation)
            pitch_stability = pitch_std / pitch_mean if pitch_mean > 0 else 0
            
            # Pitch trend (linear regression slope)
            if len(f0_nonzero) > 1:
                x = np.arange(len(f0_nonzero))
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, f0_nonzero)
                pitch_trend = slope
            else:
                pitch_trend = 0
            
            return {
                'pitch_mean': pitch_mean,
                'pitch_std': pitch_std,
                'pitch_range': pitch_range,
                'pitch_median': pitch_median,
                'pitch_stability': pitch_stability,
                'pitch_trend': pitch_trend,
                'voiced_frames_ratio': len(f0_nonzero) / len(f0)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing pitch contour: {e}")
            return {}

class RhythmAnalyzer:
    """Advanced tempo and rhythm analysis"""
    
    def __init__(self, sample_rate: int = 22050, hop_length: int = 512):
        self.sample_rate = sample_rate
        self.hop_length = hop_length
    
    def extract_rhythm_features(self, audio_path: str) -> Dict[str, Any]:
        """Extract comprehensive rhythm and tempo features"""
        try:
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Tempo and beat tracking
            tempo, beats = librosa.beat.beat_track(
                y=y, sr=sr, hop_length=self.hop_length
            )
            
            # Onset detection
            onset_frames = librosa.onset.onset_detect(
                y=y, sr=sr, hop_length=self.hop_length
            )
            
            # Convert frames to time
            beat_times = librosa.frames_to_time(beats, sr=sr, hop_length=self.hop_length)
            onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=self.hop_length)
            
            # Rhythm regularity (beat consistency)
            if len(beat_times) > 1:
                beat_intervals = np.diff(beat_times)
                rhythm_regularity = 1.0 / (np.std(beat_intervals) + 1e-8)
            else:
                rhythm_regularity = 0
            
            # Onset density
            duration = len(y) / sr
            onset_density = len(onset_times) / duration if duration > 0 else 0
            
            # Tempo stability
            if len(beat_intervals) > 0:
                tempo_stability = 1.0 / (np.std(beat_intervals) / np.mean(beat_intervals) + 1e-8)
            else:
                tempo_stability = 0
            
            return {
                'tempo': tempo,
                'beat_frames': beats,
                'onset_frames': onset_frames,
                'beat_times': beat_times,
                'onset_times': onset_times,
                'rhythm_regularity': rhythm_regularity,
                'onset_density': onset_density,
                'tempo_stability': tempo_stability,
                'num_beats': len(beats),
                'num_onsets': len(onset_frames)
            }
            
        except Exception as e:
            logger.error(f"Error extracting rhythm features: {e}")
            return {}
    
    def analyze_rhythmic_patterns(self, audio_path: str) -> Dict[str, Any]:
        """Analyze complex rhythmic patterns"""
        try:
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Tempogram (tempo over time)
            hop_length = self.hop_length
            oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
            tempogram = librosa.feature.tempogram(
                onset_envelope=oenv, sr=sr, hop_length=hop_length
            )
            
            # Fourier tempogram
            ftempogram = librosa.feature.fourier_tempogram(
                onset_envelope=oenv, sr=sr, hop_length=hop_length
            )
            
            # Rhythmic complexity (entropy of tempogram)
            tempogram_flat = tempogram.flatten()
            tempogram_flat = tempogram_flat[tempogram_flat > 0]
            
            if len(tempogram_flat) > 0:
                # Normalize to create probability distribution
                tempogram_prob = tempogram_flat / np.sum(tempogram_flat)
                rhythmic_complexity = -np.sum(tempogram_prob * np.log2(tempogram_prob + 1e-8))
            else:
                rhythmic_complexity = 0
            
            return {
                'tempogram': tempogram,
                'fourier_tempogram': ftempogram,
                'rhythmic_complexity': rhythmic_complexity,
                'tempo_variance': np.var(tempogram),
                'dominant_tempo_bin': np.argmax(np.mean(tempogram, axis=1))
            }
            
        except Exception as e:
            logger.error(f"Error analyzing rhythmic patterns: {e}")
            return {}

class AudioFingerprinter:
    """Audio fingerprinting for duplicate detection and identification"""
    
    def __init__(self, sample_rate: int = 22050, n_mels: int = 128):
        self.sample_rate = sample_rate
        self.n_mels = n_mels
        self.hop_length = 512
        self.n_fft = 2048
    
    def generate_fingerprint(self, audio_path: str) -> str:
        """Generate unique audio fingerprint"""
        try:
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Extract mel spectrogram
            mel_spec = librosa.feature.melspectrogram(
                y=y, sr=sr, n_mels=self.n_mels, hop_length=self.hop_length
            )
            
            # Convert to log scale
            log_mel_spec = librosa.power_to_db(mel_spec, ref=np.max)
            
            # Compute spectral peaks
            peaks = self._extract_spectral_peaks(log_mel_spec)
            
            # Generate hash from peaks
            fingerprint = self._hash_peaks(peaks)
            
            return fingerprint
            
        except Exception as e:
            logger.error(f"Error generating fingerprint: {e}")
            return ""
    
    def _extract_spectral_peaks(self, spectrogram: np.ndarray, 
                               threshold_percentile: float = 90) -> List[Tuple[int, int]]:
        """Extract spectral peaks from spectrogram"""
        try:
            # Find peaks above threshold
            threshold = np.percentile(spectrogram, threshold_percentile)
            peak_mask = spectrogram > threshold
            
            # Get peak coordinates
            peaks = []
            for freq_idx in range(spectrogram.shape[0]):
                for time_idx in range(spectrogram.shape[1]):
                    if peak_mask[freq_idx, time_idx]:
                        peaks.append((freq_idx, time_idx))
            
            return peaks
            
        except Exception as e:
            logger.error(f"Error extracting spectral peaks: {e}")
            return []
    
    def _hash_peaks(self, peaks: List[Tuple[int, int]]) -> str:
        """Generate hash from spectral peaks"""
        try:
            # Sort peaks by time, then frequency
            peaks_sorted = sorted(peaks, key=lambda x: (x[1], x[0]))
            
            # Create hash pairs (anchor point + target point)
            hash_pairs = []
            
            for i, anchor in enumerate(peaks_sorted):
                # Look for target points within a time window
                for j in range(i + 1, min(i + 10, len(peaks_sorted))):
                    target = peaks_sorted[j]
                    
                    # Create hash from frequency difference and time difference
                    freq_diff = target[0] - anchor[0]
                    time_diff = target[1] - anchor[1]
                    
                    if time_diff > 0:  # Ensure target is after anchor
                        hash_value = f"{freq_diff}_{time_diff}_{anchor[1]}"
                        hash_pairs.append(hash_value)
            
            # Create final fingerprint by hashing all pairs
            fingerprint_data = "_".join(sorted(hash_pairs))
            fingerprint = hashlib.md5(fingerprint_data.encode()).hexdigest()
            
            return fingerprint
            
        except Exception as e:
            logger.error(f"Error hashing peaks: {e}")
            return ""
    
    def compare_fingerprints(self, fingerprint1: str, fingerprint2: str) -> float:
        """Compare two audio fingerprints"""
        try:
            if not fingerprint1 or not fingerprint2:
                return 0.0
            
            # Simple Hamming distance for MD5 hashes
            if fingerprint1 == fingerprint2:
                return 1.0
            
            # Convert hex to binary for bit-level comparison
            bin1 = bin(int(fingerprint1, 16))[2:].zfill(128)
            bin2 = bin(int(fingerprint2, 16))[2:].zfill(128)
            
            # Calculate Hamming distance
            hamming_distance = sum(b1 != b2 for b1, b2 in zip(bin1, bin2))
            similarity = 1.0 - (hamming_distance / 128.0)
            
            return similarity
            
        except Exception as e:
            logger.error(f"Error comparing fingerprints: {e}")
            return 0.0

class AudioSimilarityAnalyzer:
    """Advanced audio similarity comparison and analysis"""
    
    def __init__(self):
        self.spectral_analyzer = SpectralAnalyzer()
        self.pitch_analyzer = PitchAnalyzer()
        self.rhythm_analyzer = RhythmAnalyzer()
        self.fingerprinter = AudioFingerprinter()
        self.scaler = StandardScaler()
    
    def extract_similarity_features(self, audio_path: str) -> np.ndarray:
        """Extract features for similarity comparison"""
        try:
            # Extract various features
            spectral_features = self.spectral_analyzer.extract_spectral_features(audio_path)
            pitch_features = self.pitch_analyzer.extract_pitch_features(audio_path)
            rhythm_features = self.rhythm_analyzer.extract_rhythm_features(audio_path)
            
            # Aggregate features into a single vector
            feature_vector = []
            
            # Spectral features (statistical summaries)
            for feature_name, feature_data in spectral_features.items():
                if len(feature_data) > 0:
                    feature_vector.extend([
                        np.mean(feature_data),
                        np.std(feature_data),
                        np.median(feature_data),
                        np.percentile(feature_data, 25),
                        np.percentile(feature_data, 75)
                    ])
                else:
                    feature_vector.extend([0, 0, 0, 0, 0])
            
            # Pitch features
            f0 = pitch_features.get('fundamental_frequency', np.array([]))
            if len(f0) > 0:
                f0_nonzero = f0[f0 > 0]
                if len(f0_nonzero) > 0:
                    feature_vector.extend([
                        np.mean(f0_nonzero),
                        np.std(f0_nonzero),
                        np.median(f0_nonzero)
                    ])
                else:
                    feature_vector.extend([0, 0, 0])
            else:
                feature_vector.extend([0, 0, 0])
            
            # Chroma features
            chroma = pitch_features.get('chroma_features', np.array([]))
            if chroma.size > 0:
                feature_vector.extend(np.mean(chroma, axis=1))
            else:
                feature_vector.extend([0] * 12)
            
            # Rhythm features
            feature_vector.extend([
                rhythm_features.get('tempo', 0),
                rhythm_features.get('rhythm_regularity', 0),
                rhythm_features.get('onset_density', 0),
                rhythm_features.get('tempo_stability', 0)
            ])
            
            return np.array(feature_vector)
            
        except Exception as e:
            logger.error(f"Error extracting similarity features: {e}")
            return np.array([])
    
    def compare_audio_similarity(self, audio_path1: str, audio_path2: str) -> AudioSimilarity:
        """Compare similarity between two audio files"""
        try:
            # Extract features
            features1 = self.extract_similarity_features(audio_path1)
            features2 = self.extract_similarity_features(audio_path2)
            
            if len(features1) == 0 or len(features2) == 0:
                return AudioSimilarity(
                    audio1_path=audio_path1,
                    audio2_path=audio_path2,
                    similarity_score=0.0,
                    distance_metrics={},
                    feature_correlations={},
                    is_duplicate=False,
                    confidence=0.0
                )
            
            # Normalize features
            features_combined = np.vstack([features1, features2])
            features_normalized = self.scaler.fit_transform(features_combined)
            features1_norm = features_normalized[0]
            features2_norm = features_normalized[1]
            
            # Calculate distance metrics
            cosine_dist = cosine(features1_norm, features2_norm)
            euclidean_dist = euclidean(features1_norm, features2_norm)
            
            # Cosine similarity
            cosine_sim = 1 - cosine_dist
            
            # Correlation coefficient
            correlation = np.corrcoef(features1_norm, features2_norm)[0, 1]
            if np.isnan(correlation):
                correlation = 0.0
            
            # Generate fingerprints
            fingerprint1 = self.fingerprinter.generate_fingerprint(audio_path1)
            fingerprint2 = self.fingerprinter.generate_fingerprint(audio_path2)
            fingerprint_similarity = self.fingerprinter.compare_fingerprints(fingerprint1, fingerprint2)
            
            # Combined similarity score
            similarity_score = (cosine_sim * 0.4 + 
                              abs(correlation) * 0.3 + 
                              fingerprint_similarity * 0.3)
            
            # Determine if duplicate
            is_duplicate = similarity_score > 0.85
            confidence = min(similarity_score, 1.0)
            
            return AudioSimilarity(
                audio1_path=audio_path1,
                audio2_path=audio_path2,
                similarity_score=similarity_score,
                distance_metrics={
                    'cosine_distance': cosine_dist,
                    'euclidean_distance': euclidean_dist,
                    'cosine_similarity': cosine_sim
                },
                feature_correlations={
                    'pearson_correlation': correlation,
                    'fingerprint_similarity': fingerprint_similarity
                },
                is_duplicate=is_duplicate,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error comparing audio similarity: {e}")
            return AudioSimilarity(
                audio1_path=audio_path1,
                audio2_path=audio_path2,
                similarity_score=0.0,
                distance_metrics={},
                feature_correlations={},
                is_duplicate=False,
                confidence=0.0
            )

class AudioClusteringEngine:
    """Advanced audio clustering and grouping"""
    
    def __init__(self):
        self.similarity_analyzer = AudioSimilarityAnalyzer()
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=0.95)  # Keep 95% of variance
    
    def cluster_audio_files(self, audio_paths: List[str], 
                           method: str = 'kmeans', 
                           n_clusters: Optional[int] = None) -> List[AudioCluster]:
        """Cluster audio files based on similarity"""
        try:
            if len(audio_paths) < 2:
                logger.warning("Need at least 2 audio files for clustering")
                return []
            
            # Extract features for all audio files
            logger.info(f"Extracting features from {len(audio_paths)} audio files...")
            features_list = []
            valid_paths = []
            
            for audio_path in audio_paths:
                features = self.similarity_analyzer.extract_similarity_features(audio_path)
                if len(features) > 0:
                    features_list.append(features)
                    valid_paths.append(audio_path)
            
            if len(features_list) < 2:
                logger.warning("Not enough valid audio files for clustering")
                return []
            
            # Normalize features
            features_matrix = np.vstack(features_list)
            features_normalized = self.scaler.fit_transform(features_matrix)
            
            # Apply PCA for dimensionality reduction
            features_pca = self.pca.fit_transform(features_normalized)
            
            # Perform clustering
            if method == 'kmeans':
                clusters = self._kmeans_clustering(features_pca, valid_paths, n_clusters)
            elif method == 'dbscan':
                clusters = self._dbscan_clustering(features_pca, valid_paths)
            elif method == 'hierarchical':
                clusters = self._hierarchical_clustering(features_pca, valid_paths, n_clusters)
            else:
                logger.error(f"Unknown clustering method: {method}")
                return []
            
            return clusters
            
        except Exception as e:
            logger.error(f"Error clustering audio files: {e}")
            return []
    
    def _kmeans_clustering(self, features: np.ndarray, audio_paths: List[str], 
                          n_clusters: Optional[int] = None) -> List[AudioCluster]:
        """Perform K-means clustering"""
        try:
            # Determine optimal number of clusters if not specified
            if n_clusters is None:
                n_clusters = min(8, max(2, len(audio_paths) // 3))
            
            # Perform K-means clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(features)
            
            # Create cluster objects
            clusters = []
            for cluster_id in range(n_clusters):
                cluster_indices = np.where(cluster_labels == cluster_id)[0]
                cluster_paths = [audio_paths[i] for i in cluster_indices]
                
                if len(cluster_paths) > 0:
                    # Calculate centroid features
                    cluster_features = features[cluster_indices]
                    centroid = np.mean(cluster_features, axis=0)
                    
                    # Calculate intra-cluster similarity
                    if len(cluster_features) > 1:
                        similarities = []
                        for i in range(len(cluster_features)):
                            for j in range(i + 1, len(cluster_features)):
                                sim = 1 - cosine(cluster_features[i], cluster_features[j])
                                similarities.append(sim)
                        intra_similarity = np.mean(similarities)
                    else:
                        intra_similarity = 1.0
                    
                    # Find representative audio (closest to centroid)
                    distances = [euclidean(feat, centroid) for feat in cluster_features]
                    representative_idx = np.argmin(distances)
                    representative_audio = cluster_paths[representative_idx]
                    
                    cluster = AudioCluster(
                        cluster_id=cluster_id,
                        audio_files=cluster_paths,
                        centroid_features={f'feature_{i}': float(val) for i, val in enumerate(centroid)},
                        cluster_size=len(cluster_paths),
                        intra_cluster_similarity=intra_similarity,
                        representative_audio=representative_audio
                    )
                    
                    clusters.append(cluster)
            
            return clusters
            
        except Exception as e:
            logger.error(f"Error in K-means clustering: {e}")
            return []
    
    def _dbscan_clustering(self, features: np.ndarray, audio_paths: List[str]) -> List[AudioCluster]:
        """Perform DBSCAN clustering"""
        try:
            # DBSCAN clustering
            dbscan = DBSCAN(eps=0.5, min_samples=2)
            cluster_labels = dbscan.fit_predict(features)
            
            # Get unique cluster labels (excluding noise points labeled as -1)
            unique_labels = set(cluster_labels)
            if -1 in unique_labels:
                unique_labels.remove(-1)
            
            clusters = []
            for cluster_id in unique_labels:
                cluster_indices = np.where(cluster_labels == cluster_id)[0]
                cluster_paths = [audio_paths[i] for i in cluster_indices]
                
                # Calculate cluster statistics
                cluster_features = features[cluster_indices]
                centroid = np.mean(cluster_features, axis=0)
                
                # Calculate intra-cluster similarity
                if len(cluster_features) > 1:
                    similarities = []
                    for i in range(len(cluster_features)):
                        for j in range(i + 1, len(cluster_features)):
                            sim = 1 - cosine(cluster_features[i], cluster_features[j])
                            similarities.append(sim)
                    intra_similarity = np.mean(similarities)
                else:
                    intra_similarity = 1.0
                
                # Find representative audio
                distances = [euclidean(feat, centroid) for feat in cluster_features]
                representative_idx = np.argmin(distances)
                representative_audio = cluster_paths[representative_idx]
                
                cluster = AudioCluster(
                    cluster_id=int(cluster_id),
                    audio_files=cluster_paths,
                    centroid_features={f'feature_{i}': float(val) for i, val in enumerate(centroid)},
                    cluster_size=len(cluster_paths),
                    intra_cluster_similarity=intra_similarity,
                    representative_audio=representative_audio
                )
                
                clusters.append(cluster)
            
            return clusters
            
        except Exception as e:
            logger.error(f"Error in DBSCAN clustering: {e}")
            return []
    
    def _hierarchical_clustering(self, features: np.ndarray, audio_paths: List[str], 
                                n_clusters: Optional[int] = None) -> List[AudioCluster]:
        """Perform hierarchical clustering"""
        try:
            # Hierarchical clustering
            linkage_matrix = linkage(features, method='ward')
            
            # Determine number of clusters
            if n_clusters is None:
                n_clusters = min(8, max(2, len(audio_paths) // 3))
            
            # Get cluster labels
            cluster_labels = fcluster(linkage_matrix, n_clusters, criterion='maxclust')
            
            clusters = []
            for cluster_id in range(1, n_clusters + 1):
                cluster_indices = np.where(cluster_labels == cluster_id)[0]
                cluster_paths = [audio_paths[i] for i in cluster_indices]
                
                if len(cluster_paths) > 0:
                    # Calculate cluster statistics
                    cluster_features = features[cluster_indices]
                    centroid = np.mean(cluster_features, axis=0)
                    
                    # Calculate intra-cluster similarity
                    if len(cluster_features) > 1:
                        similarities = []
                        for i in range(len(cluster_features)):
                            for j in range(i + 1, len(cluster_features)):
                                sim = 1 - cosine(cluster_features[i], cluster_features[j])
                                similarities.append(sim)
                        intra_similarity = np.mean(similarities)
                    else:
                        intra_similarity = 1.0
                    
                    # Find representative audio
                    distances = [euclidean(feat, centroid) for feat in cluster_features]
                    representative_idx = np.argmin(distances)
                    representative_audio = cluster_paths[representative_idx]
                    
                    cluster = AudioCluster(
                        cluster_id=cluster_id - 1,  # Convert to 0-based indexing
                        audio_files=cluster_paths,
                        centroid_features={f'feature_{i}': float(val) for i, val in enumerate(centroid)},
                        cluster_size=len(cluster_paths),
                        intra_cluster_similarity=intra_similarity,
                        representative_audio=representative_audio
                    )
                    
                    clusters.append(cluster)
            
            return clusters
            
        except Exception as e:
            logger.error(f"Error in hierarchical clustering: {e}")
            return []

class AdvancedAudioPreprocessor:
    """Main advanced audio preprocessing system"""
    
    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self.spectral_analyzer = SpectralAnalyzer(sample_rate)
        self.pitch_analyzer = PitchAnalyzer(sample_rate)
        self.rhythm_analyzer = RhythmAnalyzer(sample_rate)
        self.fingerprinter = AudioFingerprinter(sample_rate)
        self.similarity_analyzer = AudioSimilarityAnalyzer()
        self.clustering_engine = AudioClusteringEngine()
    
    def extract_comprehensive_features(self, audio_path: str) -> AudioFeatures:
        """Extract comprehensive audio features"""
        try:
            logger.info(f"Extracting comprehensive features from: {audio_path}")
            
            # Load audio for basic properties
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            duration = len(y) / sr
            
            # Extract spectral features
            spectral_features = self.spectral_analyzer.extract_spectral_features(audio_path)
            
            # Extract pitch features
            pitch_features = self.pitch_analyzer.extract_pitch_features(audio_path)
            
            # Extract rhythm features
            rhythm_features = self.rhythm_analyzer.extract_rhythm_features(audio_path)
            
            # Extract MFCC features
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            delta_mfcc = librosa.feature.delta(mfcc)
            delta2_mfcc = librosa.feature.delta(mfcc, order=2)
            
            # Extract mel spectrogram
            mel_spec = librosa.feature.melspectrogram(y=y, sr=sr)
            
            # Generate fingerprint
            fingerprint = self.fingerprinter.generate_fingerprint(audio_path)
            
            # Calculate feature statistics
            feature_stats = self._calculate_feature_statistics({
                **spectral_features,
                **pitch_features,
                'mfcc': mfcc,
                'delta_mfcc': delta_mfcc,
                'delta2_mfcc': delta2_mfcc
            })
            
            # Create AudioFeatures object
            audio_features = AudioFeatures(
                duration=duration,
                sample_rate=sr,
                channels=1,  # Librosa loads as mono by default
                spectral_centroid=spectral_features.get('spectral_centroid', np.array([])),
                spectral_bandwidth=spectral_features.get('spectral_bandwidth', np.array([])),
                spectral_rolloff=spectral_features.get('spectral_rolloff', np.array([])),
                spectral_contrast=spectral_features.get('spectral_contrast', np.array([])),
                spectral_flatness=spectral_features.get('spectral_flatness', np.array([])),
                tempo=rhythm_features.get('tempo', 0.0),
                beat_frames=rhythm_features.get('beat_frames', np.array([])),
                onset_frames=rhythm_features.get('onset_frames', np.array([])),
                fundamental_frequency=pitch_features.get('fundamental_frequency', np.array([])),
                pitch_confidence=pitch_features.get('pitch_confidence', np.array([])),
                chroma_features=pitch_features.get('chroma_features', np.array([])),
                mfcc=mfcc,
                delta_mfcc=delta_mfcc,
                delta2_mfcc=delta2_mfcc,
                zcr=spectral_features.get('zero_crossing_rate', np.array([])),
                rms=spectral_features.get('rms_energy', np.array([])),
                tonnetz=pitch_features.get('tonnetz_features', np.array([])),
                mel_spectrogram=mel_spec,
                fingerprint=fingerprint,
                feature_statistics=feature_stats
            )
            
            logger.info("Feature extraction completed successfully")
            return audio_features
            
        except Exception as e:
            logger.error(f"Error extracting comprehensive features: {e}")
            # Return empty AudioFeatures object
            return AudioFeatures(
                duration=0.0, sample_rate=self.sample_rate, channels=1,
                spectral_centroid=np.array([]), spectral_bandwidth=np.array([]),
                spectral_rolloff=np.array([]), spectral_contrast=np.array([]),
                spectral_flatness=np.array([]), tempo=0.0,
                beat_frames=np.array([]), onset_frames=np.array([]),
                fundamental_frequency=np.array([]), pitch_confidence=np.array([]),
                chroma_features=np.array([]), mfcc=np.array([]),
                delta_mfcc=np.array([]), delta2_mfcc=np.array([]),
                zcr=np.array([]), rms=np.array([]),
                tonnetz=np.array([]), mel_spectrogram=np.array([]),
                fingerprint="", feature_statistics={}
            )
    
    def _calculate_feature_statistics(self, features: Dict[str, np.ndarray]) -> Dict[str, Dict[str, float]]:
        """Calculate statistical summaries of features"""
        try:
            stats = {}
            
            for feature_name, feature_data in features.items():
                if isinstance(feature_data, np.ndarray) and feature_data.size > 0:
                    # Handle multi-dimensional arrays
                    if feature_data.ndim > 1:
                        # Calculate statistics along time axis (axis=1 for most features)
                        axis = 1 if feature_data.shape[1] > feature_data.shape[0] else 0
                        feature_stats = {
                            'mean': float(np.mean(feature_data)),
                            'std': float(np.std(feature_data)),
                            'min': float(np.min(feature_data)),
                            'max': float(np.max(feature_data)),
                            'median': float(np.median(feature_data)),
                            'q25': float(np.percentile(feature_data, 25)),
                            'q75': float(np.percentile(feature_data, 75))
                        }
                    else:
                        # 1D array statistics
                        feature_stats = {
                            'mean': float(np.mean(feature_data)),
                            'std': float(np.std(feature_data)),
                            'min': float(np.min(feature_data)),
                            'max': float(np.max(feature_data)),
                            'median': float(np.median(feature_data)),
                            'q25': float(np.percentile(feature_data, 25)),
                            'q75': float(np.percentile(feature_data, 75))
                        }
                    
                    stats[feature_name] = feature_stats
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating feature statistics: {e}")
            return {}
    
    def find_duplicate_audio(self, audio_paths: List[str], 
                           similarity_threshold: float = 0.85) -> List[Tuple[str, str, float]]:
        """Find duplicate or highly similar audio files"""
        try:
            logger.info(f"Searching for duplicates among {len(audio_paths)} audio files...")
            
            duplicates = []
            
            # Compare all pairs of audio files
            for i in range(len(audio_paths)):
                for j in range(i + 1, len(audio_paths)):
                    similarity = self.similarity_analyzer.compare_audio_similarity(
                        audio_paths[i], audio_paths[j]
                    )
                    
                    if similarity.similarity_score >= similarity_threshold:
                        duplicates.append((
                            audio_paths[i],
                            audio_paths[j],
                            similarity.similarity_score
                        ))
            
            logger.info(f"Found {len(duplicates)} potential duplicate pairs")
            return duplicates
            
        except Exception as e:
            logger.error(f"Error finding duplicate audio: {e}")
            return []
    
    def cluster_similar_audio(self, audio_paths: List[str], 
                            method: str = 'kmeans',
                            n_clusters: Optional[int] = None) -> List[AudioCluster]:
        """Cluster similar audio files"""
        try:
            logger.info(f"Clustering {len(audio_paths)} audio files using {method}")
            
            clusters = self.clustering_engine.cluster_audio_files(
                audio_paths, method, n_clusters
            )
            
            logger.info(f"Created {len(clusters)} clusters")
            return clusters
            
        except Exception as e:
            logger.error(f"Error clustering audio files: {e}")
            return []
    
    def batch_process_audio(self, audio_paths: List[str], 
                          output_dir: str = "audio_features") -> Dict[str, Any]:
        """Batch process multiple audio files"""
        try:
            logger.info(f"Batch processing {len(audio_paths)} audio files...")
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            results = {
                'processed_files': [],
                'failed_files': [],
                'features': {},
                'duplicates': [],
                'clusters': [],
                'processing_stats': {}
            }
            
            # Process each audio file
            for i, audio_path in enumerate(audio_paths):
                try:
                    logger.info(f"Processing {i+1}/{len(audio_paths)}: {audio_path}")
                    
                    # Extract features
                    features = self.extract_comprehensive_features(audio_path)
                    
                    # Save features
                    feature_file = os.path.join(output_dir, f"{Path(audio_path).stem}_features.json")
                    with open(feature_file, 'w') as f:
                        # Convert numpy arrays to lists for JSON serialization
                        features_dict = asdict(features)
                        for key, value in features_dict.items():
                            if isinstance(value, np.ndarray):
                                features_dict[key] = value.tolist()
                        json.dump(features_dict, f, indent=2)
                    
                    results['processed_files'].append(audio_path)
                    results['features'][audio_path] = features_dict
                    
                except Exception as e:
                    logger.error(f"Error processing {audio_path}: {e}")
                    results['failed_files'].append(audio_path)
            
            # Find duplicates
            if len(results['processed_files']) > 1:
                logger.info("Searching for duplicate audio files...")
                duplicates = self.find_duplicate_audio(results['processed_files'])
                results['duplicates'] = duplicates
            
            # Cluster audio files
            if len(results['processed_files']) > 2:
                logger.info("Clustering similar audio files...")
                clusters = self.cluster_similar_audio(results['processed_files'])
                results['clusters'] = [asdict(cluster) for cluster in clusters]
            
            # Processing statistics
            results['processing_stats'] = {
                'total_files': len(audio_paths),
                'processed_successfully': len(results['processed_files']),
                'failed_processing': len(results['failed_files']),
                'duplicates_found': len(results['duplicates']),
                'clusters_created': len(results['clusters']),
                'processing_time': datetime.now().isoformat()
            }
            
            # Save batch results
            batch_results_file = os.path.join(output_dir, "batch_processing_results.json")
            with open(batch_results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Batch processing completed. Results saved to {output_dir}")
            return results
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            return {}
    
    def save_features(self, features: AudioFeatures, output_path: str):
        """Save audio features to file"""
        try:
            # Convert to dictionary and handle numpy arrays
            features_dict = asdict(features)
            for key, value in features_dict.items():
                if isinstance(value, np.ndarray):
                    features_dict[key] = value.tolist()
            
            # Save to JSON
            with open(output_path, 'w') as f:
                json.dump(features_dict, f, indent=2)
            
            logger.info(f"Features saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving features: {e}")
    
    def load_features(self, input_path: str) -> AudioFeatures:
        """Load audio features from file"""
        try:
            with open(input_path, 'r') as f:
                features_dict = json.load(f)
            
            # Convert lists back to numpy arrays
            for key, value in features_dict.items():
                if isinstance(value, list) and key != 'feature_statistics':
                    features_dict[key] = np.array(value)
            
            # Create AudioFeatures object
            features = AudioFeatures(**features_dict)
            
            logger.info(f"Features loaded from: {input_path}")
            return features
            
        except Exception as e:
            logger.error(f"Error loading features: {e}")
            return None

# Example usage and testing
if __name__ == "__main__":
    # Initialize the system
    preprocessor = AdvancedAudioPreprocessor()
    
    print("Advanced Audio Preprocessing System initialized successfully!")
    print("Available features:")
    print("- Spectral analysis and audio feature extraction")
    print("- Pitch detection and fundamental frequency analysis")
    print("- Audio fingerprinting for duplicate detection")
    print("- Tempo and rhythm analysis capabilities")
    print("- Audio similarity comparison and clustering")
    print("- Batch processing for large audio datasets")
    print("- Comprehensive feature extraction and analysis")