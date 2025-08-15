"""
Voice Activity Detection (VAD) System
Implements comprehensive voice activity detection using multiple algorithms including
WebRTC VAD, pyAudioAnalysis, and custom ML-based approaches for speech vs silence detection
"""

import os
import logging
import numpy as np
import librosa
import soundfile as sf
from typing import List, Tuple, Dict, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import sqlite3
import json
from pathlib import Path
import time
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import signal
from scipy.stats import entropy
import webrtcvad
from pyAudioAnalysis import audioSegmentation
import torch
import torch.nn as nn
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VADMethod(Enum):
    WEBRTC = "webrtc"
    PYAUDIO_ANALYSIS = "pyaudio_analysis"
    ENERGY_BASED = "energy_based"
    SPECTRAL_CENTROID = "spectral_centroid"
    ZERO_CROSSING_RATE = "zero_crossing_rate"
    ML_CLASSIFIER = "ml_classifier"
    ENSEMBLE = "ensemble"
    DEEP_LEARNING = "deep_learning"

class VADMode(Enum):
    QUALITY = 0      # Most aggressive filtering
    LOW_BITRATE = 1  # Less aggressive filtering
    NORMAL = 2       # Least aggressive filtering
    VERY_AGGRESSIVE = 3  # Custom very aggressive mode

@dataclass
class VADSegment:
    start_time: float
    end_time: float
    duration: float
    is_speech: bool
    confidence: float
    method: str
    features: Dict[str, float] = None
    
@dataclass
class VADResult:
    segments: List[VADSegment]
    total_duration: float
    speech_duration: float
    silence_duration: float
    speech_ratio: float
    quality_score: float
    method_used: str
    processing_time: float

@dataclass
class AudioQualityMetrics:
    snr_db: float
    thd_percent: float
    dynamic_range_db: float
    spectral_centroid_hz: float
    spectral_rolloff_hz: float
    zero_crossing_rate: float
    mfcc_features: List[float]
    energy_entropy: float
    spectral_entropy: float

class DeepVADModel(nn.Module):
    """Deep learning model for voice activity detection"""
    
    def __init__(self, input_size=13, hidden_size=128, num_layers=2):
        super(DeepVADModel, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
        self.fc1 = nn.Linear(hidden_size, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, 1)
        self.dropout = nn.Dropout(0.3)
        self.relu = nn.ReLU()
        self.sigmoid = nn.Sigmoid()
        
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        # Take the last output
        x = lstm_out[:, -1, :]
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.sigmoid(self.fc3(x))
        return x

class VoiceActivityDetector:
    def __init__(self, db_path: str = "vad_system.db", webrtc_vad_mode: int = 2):
        self.db_path = db_path
        self.webrtc_vad_mode = webrtc_vad_mode
        self.webrtc_vad = None
        self.ml_classifier = None
        self.scaler = None
        self.deep_model = None
        self.init_database()
        self.init_models()
        
    def init_database(self):
        """Initialize the VAD database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # VAD results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vad_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                method TEXT NOT NULL,
                total_duration REAL,
                speech_duration REAL,
                silence_duration REAL,
                speech_ratio REAL,
                quality_score REAL,
                processing_time REAL,
                segments TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Audio quality metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audio_quality (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                snr_db REAL,
                thd_percent REAL,
                dynamic_range_db REAL,
                spectral_centroid_hz REAL,
                spectral_rolloff_hz REAL,
                zero_crossing_rate REAL,
                mfcc_features TEXT,
                energy_entropy REAL,
                spectral_entropy REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # VAD performance metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vad_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method TEXT NOT NULL,
                accuracy REAL,
                precision REAL,
                recall REAL,
                f1_score REAL,
                processing_speed REAL,
                memory_usage REAL,
                test_files_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("VAD database initialized")

    def init_models(self):
        """Initialize VAD models"""
        try:
            # Initialize WebRTC VAD
            self.webrtc_vad = webrtcvad.Vad()
            self.webrtc_vad.set_mode(self.webrtc_vad_mode)
            
            # Initialize ML classifier
            self.ml_classifier = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            self.scaler = StandardScaler()
            
            # Initialize deep learning model
            self.deep_model = DeepVADModel()
            
            # Try to load pre-trained models
            self.load_pretrained_models()
            
            logger.info("VAD models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing VAD models: {e}")

    def set_webrtc_vad_mode(self, mode: int):
        """Set WebRTC VAD mode (0-3, where 0 is most aggressive, 3 is least aggressive)"""
        if self.webrtc_vad and 0 <= mode <= 3:
            self.webrtc_vad_mode = mode
            self.webrtc_vad.set_mode(mode)
            logger.info(f"WebRTC VAD mode updated to {mode}")
        else:
            logger.warning(f"Invalid WebRTC VAD mode: {mode}")
    
    def get_webrtc_vad_mode(self) -> int:
        """Get current WebRTC VAD mode"""
        return self.webrtc_vad_mode

    def load_pretrained_models(self):
        """Load pre-trained models if available"""
        try:
            # Load ML classifier
            if os.path.exists("models/vad_classifier.joblib"):
                self.ml_classifier = joblib.load("models/vad_classifier.joblib")
                logger.info("Loaded pre-trained ML classifier")
            
            # Load scaler
            if os.path.exists("models/vad_scaler.joblib"):
                self.scaler = joblib.load("models/vad_scaler.joblib")
                logger.info("Loaded pre-trained scaler")
            
            # Load deep learning model
            if os.path.exists("models/vad_deep_model.pth"):
                self.deep_model.load_state_dict(torch.load("models/vad_deep_model.pth"))
                self.deep_model.eval()
                logger.info("Loaded pre-trained deep learning model")
                
        except Exception as e:
            logger.warning(f"Could not load pre-trained models: {e}")

    def extract_audio_features(self, audio: np.ndarray, sr: int, 
                              frame_length: int = 2048, hop_length: int = 512) -> Dict[str, float]:
        """Extract comprehensive audio features for VAD"""
        try:
            features = {}
            
            # Energy-based features
            energy = np.sum(audio ** 2)
            features['energy'] = float(energy)
            features['log_energy'] = float(np.log(energy + 1e-10))
            
            # Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(audio, frame_length=frame_length, 
                                                   hop_length=hop_length)[0]
            features['zcr_mean'] = float(np.mean(zcr))
            features['zcr_std'] = float(np.std(zcr))
            
            # Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
            features['spectral_centroid_mean'] = float(np.mean(spectral_centroids))
            features['spectral_centroid_std'] = float(np.std(spectral_centroids))
            
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)[0]
            features['spectral_rolloff_mean'] = float(np.mean(spectral_rolloff))
            features['spectral_rolloff_std'] = float(np.std(spectral_rolloff))
            
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sr)[0]
            features['spectral_bandwidth_mean'] = float(np.mean(spectral_bandwidth))
            features['spectral_bandwidth_std'] = float(np.std(spectral_bandwidth))
            
            # MFCC features
            mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
            for i in range(13):
                features[f'mfcc_{i}_mean'] = float(np.mean(mfccs[i]))
                features[f'mfcc_{i}_std'] = float(np.std(mfccs[i]))
            
            # Chroma features
            chroma = librosa.feature.chroma_stft(y=audio, sr=sr)
            features['chroma_mean'] = float(np.mean(chroma))
            features['chroma_std'] = float(np.std(chroma))
            
            # Spectral contrast
            contrast = librosa.feature.spectral_contrast(y=audio, sr=sr)
            features['spectral_contrast_mean'] = float(np.mean(contrast))
            features['spectral_contrast_std'] = float(np.std(contrast))
            
            # Tonnetz
            tonnetz = librosa.feature.tonnetz(y=librosa.effects.harmonic(audio), sr=sr)
            features['tonnetz_mean'] = float(np.mean(tonnetz))
            features['tonnetz_std'] = float(np.std(tonnetz))
            
            # Entropy features
            stft = librosa.stft(audio)
            magnitude = np.abs(stft)
            
            # Spectral entropy
            normalized_magnitude = magnitude / (np.sum(magnitude, axis=0) + 1e-10)
            spectral_entropy = -np.sum(normalized_magnitude * np.log(normalized_magnitude + 1e-10), axis=0)
            features['spectral_entropy_mean'] = float(np.mean(spectral_entropy))
            features['spectral_entropy_std'] = float(np.std(spectral_entropy))
            
            # Energy entropy
            frame_energies = np.sum(magnitude ** 2, axis=0)
            normalized_energies = frame_energies / (np.sum(frame_energies) + 1e-10)
            energy_entropy = -np.sum(normalized_energies * np.log(normalized_energies + 1e-10))
            features['energy_entropy'] = float(energy_entropy)
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting audio features: {e}")
            return {}

    def webrtc_vad_detection(self, audio: np.ndarray, sr: int, 
                           frame_duration_ms: int = 30) -> List[VADSegment]:
        """Perform VAD using WebRTC VAD"""
        try:
            # Convert to 16kHz if necessary (WebRTC VAD requirement)
            if sr != 16000:
                audio_16k = librosa.resample(audio, orig_sr=sr, target_sr=16000)
            else:
                audio_16k = audio
            
            # Convert to 16-bit PCM
            audio_16bit = (audio_16k * 32767).astype(np.int16)
            
            # Frame parameters
            frame_length = int(16000 * frame_duration_ms / 1000)  # 16kHz sample rate
            hop_length = frame_length
            
            segments = []
            current_segment_start = None
            current_is_speech = None
            
            for i in range(0, len(audio_16bit) - frame_length, hop_length):
                frame = audio_16bit[i:i + frame_length]
                
                # WebRTC VAD requires specific frame sizes
                if len(frame) == frame_length:
                    is_speech = self.webrtc_vad.is_speech(frame.tobytes(), 16000)
                    
                    current_time = i / 16000  # Convert to seconds
                    
                    if current_segment_start is None:
                        current_segment_start = current_time
                        current_is_speech = is_speech
                    elif current_is_speech != is_speech:
                        # Segment boundary detected
                        segment = VADSegment(
                            start_time=current_segment_start,
                            end_time=current_time,
                            duration=current_time - current_segment_start,
                            is_speech=current_is_speech,
                            confidence=0.8,  # WebRTC doesn't provide confidence
                            method="webrtc"
                        )
                        segments.append(segment)
                        
                        current_segment_start = current_time
                        current_is_speech = is_speech
            
            # Add final segment
            if current_segment_start is not None:
                final_time = len(audio_16bit) / 16000
                segment = VADSegment(
                    start_time=current_segment_start,
                    end_time=final_time,
                    duration=final_time - current_segment_start,
                    is_speech=current_is_speech,
                    confidence=0.8,
                    method="webrtc"
                )
                segments.append(segment)
            
            return segments
            
        except Exception as e:
            logger.error(f"WebRTC VAD detection failed: {e}")
            return []

    def pyaudio_analysis_vad(self, audio_file: str) -> List[VADSegment]:
        """Perform VAD using pyAudioAnalysis"""
        try:
            # Use pyAudioAnalysis for silence removal
            segments_limits = audioSegmentation.silence_removal(
                audio_file, 
                Fs=16000, 
                st_win=0.05, 
                st_step=0.05, 
                smooth_window=1.0, 
                weight=0.3, 
                plot=False
            )
            
            segments = []
            for i, (start, end) in enumerate(segments_limits):
                segment = VADSegment(
                    start_time=start,
                    end_time=end,
                    duration=end - start,
                    is_speech=True,  # pyAudioAnalysis returns speech segments
                    confidence=0.75,
                    method="pyaudio_analysis"
                )
                segments.append(segment)
            
            return segments
            
        except Exception as e:
            logger.error(f"pyAudioAnalysis VAD failed: {e}")
            return []

    def energy_based_vad(self, audio: np.ndarray, sr: int, 
                        frame_length: int = 2048, hop_length: int = 512,
                        energy_threshold: float = 0.01) -> List[VADSegment]:
        """Perform energy-based VAD"""
        try:
            # Calculate frame-wise energy
            frames = librosa.util.frame(audio, frame_length=frame_length, 
                                      hop_length=hop_length, axis=0)
            energy = np.sum(frames ** 2, axis=1)
            
            # Normalize energy
            energy = energy / np.max(energy)
            
            # Apply threshold
            is_speech = energy > energy_threshold
            
            # Convert to time-based segments
            segments = []
            current_segment_start = None
            current_is_speech = None
            
            for i, speech_flag in enumerate(is_speech):
                current_time = i * hop_length / sr
                
                if current_segment_start is None:
                    current_segment_start = current_time
                    current_is_speech = speech_flag
                elif current_is_speech != speech_flag:
                    segment = VADSegment(
                        start_time=current_segment_start,
                        end_time=current_time,
                        duration=current_time - current_segment_start,
                        is_speech=current_is_speech,
                        confidence=float(energy[i-1]) if i > 0 else 0.5,
                        method="energy_based"
                    )
                    segments.append(segment)
                    
                    current_segment_start = current_time
                    current_is_speech = speech_flag
            
            # Add final segment
            if current_segment_start is not None:
                final_time = len(audio) / sr
                segment = VADSegment(
                    start_time=current_segment_start,
                    end_time=final_time,
                    duration=final_time - current_segment_start,
                    is_speech=current_is_speech,
                    confidence=0.5,
                    method="energy_based"
                )
                segments.append(segment)
            
            return segments
            
        except Exception as e:
            logger.error(f"Energy-based VAD failed: {e}")
            return []

    def ml_classifier_vad(self, audio: np.ndarray, sr: int,
                         frame_length: int = 2048, hop_length: int = 512) -> List[VADSegment]:
        """Perform VAD using ML classifier"""
        try:
            if self.ml_classifier is None or self.scaler is None:
                logger.warning("ML classifier not trained, using default predictions")
                return self.energy_based_vad(audio, sr, frame_length, hop_length)
            
            # Extract features for each frame
            frames = librosa.util.frame(audio, frame_length=frame_length, 
                                      hop_length=hop_length, axis=0)
            
            features_list = []
            for frame in frames:
                features = self.extract_audio_features(frame, sr)
                if features:
                    # Convert to feature vector
                    feature_vector = [
                        features.get('energy', 0),
                        features.get('log_energy', 0),
                        features.get('zcr_mean', 0),
                        features.get('spectral_centroid_mean', 0),
                        features.get('spectral_rolloff_mean', 0),
                        features.get('spectral_bandwidth_mean', 0),
                        features.get('mfcc_0_mean', 0),
                        features.get('mfcc_1_mean', 0),
                        features.get('mfcc_2_mean', 0),
                        features.get('spectral_entropy_mean', 0),
                        features.get('energy_entropy', 0)
                    ]
                    features_list.append(feature_vector)
                else:
                    features_list.append([0] * 11)  # Default feature vector
            
            if not features_list:
                return []
            
            # Scale features and predict
            features_array = np.array(features_list)
            features_scaled = self.scaler.transform(features_array)
            predictions = self.ml_classifier.predict(features_scaled)
            probabilities = self.ml_classifier.predict_proba(features_scaled)
            
            # Convert predictions to segments
            segments = []
            current_segment_start = None
            current_is_speech = None
            
            for i, (prediction, prob) in enumerate(zip(predictions, probabilities)):
                current_time = i * hop_length / sr
                is_speech = bool(prediction)
                confidence = float(np.max(prob))
                
                if current_segment_start is None:
                    current_segment_start = current_time
                    current_is_speech = is_speech
                elif current_is_speech != is_speech:
                    segment = VADSegment(
                        start_time=current_segment_start,
                        end_time=current_time,
                        duration=current_time - current_segment_start,
                        is_speech=current_is_speech,
                        confidence=confidence,
                        method="ml_classifier"
                    )
                    segments.append(segment)
                    
                    current_segment_start = current_time
                    current_is_speech = is_speech
            
            # Add final segment
            if current_segment_start is not None:
                final_time = len(audio) / sr
                segment = VADSegment(
                    start_time=current_segment_start,
                    end_time=final_time,
                    duration=final_time - current_segment_start,
                    is_speech=current_is_speech,
                    confidence=confidence,
                    method="ml_classifier"
                )
                segments.append(segment)
            
            return segments
            
        except Exception as e:
            logger.error(f"ML classifier VAD failed: {e}")
            return []

    def ensemble_vad(self, audio: np.ndarray, sr: int, audio_file: str = None) -> List[VADSegment]:
        """Perform ensemble VAD using multiple methods"""
        try:
            # Get predictions from multiple methods
            webrtc_segments = self.webrtc_vad_detection(audio, sr)
            energy_segments = self.energy_based_vad(audio, sr)
            
            # If audio file is provided, use pyAudioAnalysis
            pyaudio_segments = []
            if audio_file and os.path.exists(audio_file):
                pyaudio_segments = self.pyaudio_analysis_vad(audio_file)
            
            # Combine segments using voting
            total_duration = len(audio) / sr
            time_resolution = 0.01  # 10ms resolution
            time_points = np.arange(0, total_duration, time_resolution)
            
            # Create voting arrays
            votes = np.zeros(len(time_points))
            confidences = np.zeros(len(time_points))
            
            # Add votes from each method
            for segments in [webrtc_segments, energy_segments, pyaudio_segments]:
                for segment in segments:
                    start_idx = int(segment.start_time / time_resolution)
                    end_idx = int(segment.end_time / time_resolution)
                    start_idx = max(0, min(start_idx, len(votes) - 1))
                    end_idx = max(0, min(end_idx, len(votes)))
                    
                    if segment.is_speech:
                        votes[start_idx:end_idx] += 1
                        confidences[start_idx:end_idx] += segment.confidence
            
            # Majority voting
            speech_threshold = 1  # At least 1 method should agree
            is_speech_array = votes >= speech_threshold
            
            # Convert back to segments
            segments = []
            current_segment_start = None
            current_is_speech = None
            
            for i, is_speech in enumerate(is_speech_array):
                current_time = i * time_resolution
                
                if current_segment_start is None:
                    current_segment_start = current_time
                    current_is_speech = is_speech
                elif current_is_speech != is_speech:
                    avg_confidence = confidences[int(current_segment_start/time_resolution):i].mean() if votes[int(current_segment_start/time_resolution):i].sum() > 0 else 0.5
                    
                    segment = VADSegment(
                        start_time=current_segment_start,
                        end_time=current_time,
                        duration=current_time - current_segment_start,
                        is_speech=current_is_speech,
                        confidence=float(avg_confidence),
                        method="ensemble"
                    )
                    segments.append(segment)
                    
                    current_segment_start = current_time
                    current_is_speech = is_speech
            
            # Add final segment
            if current_segment_start is not None:
                segment = VADSegment(
                    start_time=current_segment_start,
                    end_time=total_duration,
                    duration=total_duration - current_segment_start,
                    is_speech=current_is_speech,
                    confidence=0.7,
                    method="ensemble"
                )
                segments.append(segment)
            
            return segments
            
        except Exception as e:
            logger.error(f"Ensemble VAD failed: {e}")
            return []

    def assess_audio_quality(self, audio: np.ndarray, sr: int) -> AudioQualityMetrics:
        """Assess audio quality metrics"""
        try:
            # Signal-to-Noise Ratio (simplified estimation)
            signal_power = np.mean(audio ** 2)
            noise_power = np.var(audio - signal.medfilt(audio, kernel_size=5))
            snr_db = 10 * np.log10(signal_power / (noise_power + 1e-10))
            
            # Total Harmonic Distortion (simplified)
            fft = np.fft.fft(audio)
            fundamental_freq = np.argmax(np.abs(fft[:len(fft)//2]))
            harmonics = [2*fundamental_freq, 3*fundamental_freq, 4*fundamental_freq]
            
            fundamental_power = np.abs(fft[fundamental_freq]) ** 2
            harmonic_power = sum(np.abs(fft[h]) ** 2 for h in harmonics if h < len(fft)//2)
            thd_percent = 100 * np.sqrt(harmonic_power / (fundamental_power + 1e-10))
            
            # Dynamic Range
            dynamic_range_db = 20 * np.log10(np.max(np.abs(audio)) / (np.mean(np.abs(audio)) + 1e-10))
            
            # Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)[0]
            zcr = librosa.feature.zero_crossing_rate(audio)[0]
            
            # MFCC features
            mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
            mfcc_features = [float(np.mean(mfcc)) for mfcc in mfccs]
            
            # Entropy calculations
            stft = librosa.stft(audio)
            magnitude = np.abs(stft)
            
            # Energy entropy
            frame_energies = np.sum(magnitude ** 2, axis=0)
            normalized_energies = frame_energies / (np.sum(frame_energies) + 1e-10)
            energy_entropy = -np.sum(normalized_energies * np.log(normalized_energies + 1e-10))
            
            # Spectral entropy
            normalized_magnitude = magnitude / (np.sum(magnitude, axis=0) + 1e-10)
            spectral_entropy = -np.sum(normalized_magnitude * np.log(normalized_magnitude + 1e-10), axis=0)
            
            return AudioQualityMetrics(
                snr_db=float(snr_db),
                thd_percent=float(thd_percent),
                dynamic_range_db=float(dynamic_range_db),
                spectral_centroid_hz=float(np.mean(spectral_centroids)),
                spectral_rolloff_hz=float(np.mean(spectral_rolloff)),
                zero_crossing_rate=float(np.mean(zcr)),
                mfcc_features=mfcc_features,
                energy_entropy=float(energy_entropy),
                spectral_entropy=float(np.mean(spectral_entropy))
            )
            
        except Exception as e:
            logger.error(f"Audio quality assessment failed: {e}")
            return AudioQualityMetrics(0, 0, 0, 0, 0, 0, [], 0, 0)

    def detect_voice_activity(self, audio_file: str, method: VADMethod = VADMethod.ENSEMBLE) -> VADResult:
        """Main method to detect voice activity in audio file"""
        start_time = time.time()
        
        try:
            # Load audio
            audio, sr = librosa.load(audio_file, sr=None)
            total_duration = len(audio) / sr
            
            # Perform VAD based on selected method
            if method == VADMethod.WEBRTC:
                segments = self.webrtc_vad_detection(audio, sr)
            elif method == VADMethod.PYAUDIO_ANALYSIS:
                segments = self.pyaudio_analysis_vad(audio_file)
            elif method == VADMethod.ENERGY_BASED:
                segments = self.energy_based_vad(audio, sr)
            elif method == VADMethod.ML_CLASSIFIER:
                segments = self.ml_classifier_vad(audio, sr)
            elif method == VADMethod.ENSEMBLE:
                segments = self.ensemble_vad(audio, sr, audio_file)
            else:
                segments = self.ensemble_vad(audio, sr, audio_file)
            
            # Calculate statistics
            speech_duration = sum(seg.duration for seg in segments if seg.is_speech)
            silence_duration = total_duration - speech_duration
            speech_ratio = speech_duration / total_duration if total_duration > 0 else 0
            
            # Assess audio quality
            quality_metrics = self.assess_audio_quality(audio, sr)
            quality_score = min(100, max(0, quality_metrics.snr_db * 10))  # Simplified quality score
            
            processing_time = time.time() - start_time
            
            result = VADResult(
                segments=segments,
                total_duration=total_duration,
                speech_duration=speech_duration,
                silence_duration=silence_duration,
                speech_ratio=speech_ratio,
                quality_score=quality_score,
                method_used=method.value,
                processing_time=processing_time
            )
            
            # Store results in database
            self.store_vad_result(audio_file, result)
            self.store_quality_metrics(audio_file, quality_metrics)
            
            logger.info(f"VAD completed for {audio_file} using {method.value} method")
            return result
            
        except Exception as e:
            logger.error(f"Voice activity detection failed: {e}")
            return VADResult([], 0, 0, 0, 0, 0, method.value, time.time() - start_time)

    def remove_silence(self, audio_file: str, output_file: str, 
                      method: VADMethod = VADMethod.ENSEMBLE,
                      padding_ms: int = 100) -> str:
        """Remove silence from audio file"""
        try:
            # Detect voice activity
            vad_result = self.detect_voice_activity(audio_file, method)
            
            # Load original audio
            audio, sr = librosa.load(audio_file, sr=None)
            
            # Extract speech segments with padding
            speech_segments = []
            padding_samples = int(padding_ms * sr / 1000)
            
            for segment in vad_result.segments:
                if segment.is_speech:
                    start_sample = max(0, int(segment.start_time * sr) - padding_samples)
                    end_sample = min(len(audio), int(segment.end_time * sr) + padding_samples)
                    speech_segments.append(audio[start_sample:end_sample])
            
            # Concatenate speech segments
            if speech_segments:
                processed_audio = np.concatenate(speech_segments)
            else:
                processed_audio = audio  # Keep original if no speech detected
            
            # Save processed audio
            sf.write(output_file, processed_audio, sr)
            
            logger.info(f"Silence removed from {audio_file}, saved to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Silence removal failed: {e}")
            return audio_file

    def store_vad_result(self, file_path: str, result: VADResult):
        """Store VAD result in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            segments_json = json.dumps([
                {
                    'start_time': seg.start_time,
                    'end_time': seg.end_time,
                    'duration': seg.duration,
                    'is_speech': seg.is_speech,
                    'confidence': seg.confidence,
                    'method': seg.method
                }
                for seg in result.segments
            ])
            
            cursor.execute('''
                INSERT INTO vad_results 
                (file_path, method, total_duration, speech_duration, silence_duration, 
                 speech_ratio, quality_score, processing_time, segments)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                file_path, result.method_used, result.total_duration,
                result.speech_duration, result.silence_duration, result.speech_ratio,
                result.quality_score, result.processing_time, segments_json
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store VAD result: {e}")

    def store_quality_metrics(self, file_path: str, metrics: AudioQualityMetrics):
        """Store audio quality metrics in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO audio_quality 
                (file_path, snr_db, thd_percent, dynamic_range_db, spectral_centroid_hz,
                 spectral_rolloff_hz, zero_crossing_rate, mfcc_features, energy_entropy, spectral_entropy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                file_path, metrics.snr_db, metrics.thd_percent, metrics.dynamic_range_db,
                metrics.spectral_centroid_hz, metrics.spectral_rolloff_hz, metrics.zero_crossing_rate,
                json.dumps(metrics.mfcc_features), metrics.energy_entropy, metrics.spectral_entropy
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store quality metrics: {e}")

    def get_vad_statistics(self) -> Dict[str, Any]:
        """Get VAD system statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get overall statistics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_files,
                    AVG(speech_ratio) as avg_speech_ratio,
                    AVG(quality_score) as avg_quality_score,
                    AVG(processing_time) as avg_processing_time,
                    method
                FROM vad_results 
                GROUP BY method
            ''')
            
            method_stats = cursor.fetchall()
            
            # Get recent activity
            cursor.execute('''
                SELECT file_path, method, speech_ratio, quality_score, created_at
                FROM vad_results 
                ORDER BY created_at DESC 
                LIMIT 10
            ''')
            
            recent_activity = cursor.fetchall()
            
            conn.close()
            
            return {
                'method_statistics': method_stats,
                'recent_activity': recent_activity,
                'total_processed_files': sum(stat[0] for stat in method_stats)
            }
            
        except Exception as e:
            logger.error(f"Failed to get VAD statistics: {e}")
            return {}

    def visualize_vad_result(self, audio_file: str, vad_result: VADResult, 
                           output_file: str = None) -> str:
        """Create visualization of VAD results"""
        try:
            # Load audio for visualization
            audio, sr = librosa.load(audio_file, sr=None)
            
            # Create figure with subplots
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 10))
            
            # Plot waveform
            time_axis = np.linspace(0, len(audio) / sr, len(audio))
            ax1.plot(time_axis, audio, alpha=0.7, color='blue')
            ax1.set_title('Audio Waveform')
            ax1.set_ylabel('Amplitude')
            ax1.grid(True, alpha=0.3)
            
            # Plot VAD segments
            for segment in vad_result.segments:
                color = 'green' if segment.is_speech else 'red'
                alpha = segment.confidence if segment.confidence else 0.5
                ax1.axvspan(segment.start_time, segment.end_time, 
                           color=color, alpha=alpha * 0.3)
            
            # Plot spectrogram
            D = librosa.amplitude_to_db(np.abs(librosa.stft(audio)), ref=np.max)
            img = librosa.display.specshow(D, y_axis='hz', x_axis='time', 
                                         sr=sr, ax=ax2, cmap='viridis')
            ax2.set_title('Spectrogram with VAD Overlay')
            plt.colorbar(img, ax=ax2, format='%+2.0f dB')
            
            # Overlay VAD segments on spectrogram
            for segment in vad_result.segments:
                color = 'white' if segment.is_speech else 'black'
                ax2.axvspan(segment.start_time, segment.end_time, 
                           color=color, alpha=0.2)
            
            # Plot VAD confidence over time
            time_points = []
            confidences = []
            speech_flags = []
            
            for segment in vad_result.segments:
                time_points.extend([segment.start_time, segment.end_time])
                confidences.extend([segment.confidence, segment.confidence])
                speech_flags.extend([segment.is_speech, segment.is_speech])
            
            if time_points:
                colors = ['green' if flag else 'red' for flag in speech_flags]
                ax3.plot(time_points, confidences, marker='o', linestyle='-')
                ax3.scatter(time_points, confidences, c=colors, alpha=0.7)
            
            ax3.set_title('VAD Confidence Over Time')
            ax3.set_xlabel('Time (seconds)')
            ax3.set_ylabel('Confidence')
            ax3.set_ylim(0, 1)
            ax3.grid(True, alpha=0.3)
            
            # Add legend
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor='green', alpha=0.3, label='Speech'),
                Patch(facecolor='red', alpha=0.3, label='Silence')
            ]
            ax1.legend(handles=legend_elements, loc='upper right')
            
            plt.tight_layout()
            
            # Save or show plot
            if output_file:
                plt.savefig(output_file, dpi=300, bbox_inches='tight')
                plt.close()
                return output_file
            else:
                plt.show()
                return "displayed"
                
        except Exception as e:
            logger.error(f"VAD visualization failed: {e}")
            return ""

if __name__ == "__main__":
    # Example usage
    vad = VoiceActivityDetector()
    
    # Example audio file (you would provide a real file)
    audio_file = "test_audio.wav"
    
    if os.path.exists(audio_file):
        # Detect voice activity
        result = vad.detect_voice_activity(audio_file, VADMethod.ENSEMBLE)
        
        print(f"VAD Results for {audio_file}:")
        print(f"Total Duration: {result.total_duration:.2f}s")
        print(f"Speech Duration: {result.speech_duration:.2f}s")
        print(f"Silence Duration: {result.silence_duration:.2f}s")
        print(f"Speech Ratio: {result.speech_ratio:.2%}")
        print(f"Quality Score: {result.quality_score:.1f}")
        print(f"Processing Time: {result.processing_time:.3f}s")
        print(f"Method Used: {result.method_used}")
        
        # Remove silence
        output_file = "processed_audio.wav"
        vad.remove_silence(audio_file, output_file)
        
        # Create visualization
        vad.visualize_vad_result(audio_file, result, "vad_visualization.png")
        
        print(f"\nProcessed audio saved to: {output_file}")
        print(f"Visualization saved to: vad_visualization.png")
    else:
        print(f"Audio file {audio_file} not found. Please provide a valid audio file.")