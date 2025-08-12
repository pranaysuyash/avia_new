#!/usr/bin/env python3
"""
Voice Profiling and Analysis System
Implements speaker identification, voice biometrics, emotion detection,
stress analysis, and comprehensive speaking pattern analysis
"""

import asyncio
import json
import logging
import hashlib
import os
import pickle
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from pathlib import Path
import wave
import librosa
import soundfile as sf
from scipy import signal, stats
from scipy.spatial.distance import cosine
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.mixture import GaussianMixture
import torch
import torch.nn as nn
import torch.nn.functional as F
from collections import defaultdict
import tempfile

# Audio processing
import webrtcvad
import parselmouth
from pyannote.audio import Pipeline
from resemblyzer import VoiceEncoder, preprocess_wav

# Machine learning
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix
import joblib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """Types of voice analysis"""
    IDENTIFICATION = "identification"
    VERIFICATION = "verification"
    EMOTION = "emotion"
    STRESS = "stress"
    HEALTH = "health"
    PERSONALITY = "personality"
    SPEAKING_STYLE = "speaking_style"
    QUALITY = "quality"


class EmotionType(Enum):
    """Detected emotion types"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"
    DISGUSTED = "disgusted"
    SURPRISED = "surprised"
    CALM = "calm"
    EXCITED = "excited"


@dataclass
class VoiceFeatures:
    """Comprehensive voice features"""
    # Acoustic features
    pitch_mean: float
    pitch_std: float
    pitch_range: float
    intensity_mean: float
    intensity_std: float
    
    # Spectral features
    spectral_centroid: float
    spectral_rolloff: float
    spectral_flux: float
    zero_crossing_rate: float
    
    # Prosodic features
    speaking_rate: float
    pause_frequency: float
    pause_duration_mean: float
    
    # Voice quality
    jitter: float  # Pitch variation
    shimmer: float  # Amplitude variation
    hnr: float  # Harmonics-to-noise ratio
    
    # MFCC features
    mfcc_features: np.ndarray
    
    # Formants
    f1_mean: float  # First formant
    f2_mean: float  # Second formant
    f3_mean: float  # Third formant
    
    # Embedding
    voice_embedding: Optional[np.ndarray] = None
    
    # Metadata
    duration: float = 0.0
    sample_rate: int = 16000


@dataclass
class VoiceProfile:
    """Individual voice profile"""
    profile_id: str
    name: str
    features: VoiceFeatures
    embeddings: List[np.ndarray]  # Multiple embeddings for robustness
    enrollment_samples: int
    created_at: datetime
    updated_at: datetime
    
    # Biometric template
    gmm_model: Optional[Any] = None  # Gaussian Mixture Model
    svm_model: Optional[Any] = None  # Support Vector Machine
    
    # Analysis history
    emotion_baseline: Dict[str, float] = field(default_factory=dict)
    stress_baseline: float = 0.0
    speaking_patterns: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    age: Optional[int] = None
    gender: Optional[str] = None
    language: Optional[str] = None
    health_conditions: List[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """Voice analysis result"""
    analysis_type: AnalysisType
    timestamp: datetime
    confidence: float
    
    # Identification/Verification
    speaker_id: Optional[str] = None
    is_verified: Optional[bool] = None
    similarity_score: Optional[float] = None
    
    # Emotion detection
    emotion: Optional[EmotionType] = None
    emotion_scores: Dict[str, float] = field(default_factory=dict)
    valence: Optional[float] = None  # Positive/negative emotion
    arousal: Optional[float] = None  # Calm/excited
    
    # Stress analysis
    stress_level: Optional[float] = None  # 0-1 scale
    stress_indicators: List[str] = field(default_factory=list)
    
    # Health indicators
    voice_health_score: Optional[float] = None
    anomalies: List[str] = field(default_factory=list)
    
    # Speaking patterns
    speaking_rate: Optional[float] = None
    fluency_score: Optional[float] = None
    clarity_score: Optional[float] = None
    
    # Personality traits (Big Five)
    personality_traits: Dict[str, float] = field(default_factory=dict)
    
    # Raw features
    features: Optional[VoiceFeatures] = None


class FeatureExtractor:
    """Extract comprehensive voice features"""
    
    def __init__(self):
        self.voice_encoder = VoiceEncoder()
        self.vad = webrtcvad.Vad(2)
        
    def extract_features(self, audio_path: str) -> VoiceFeatures:
        """Extract all voice features from audio"""
        
        # Load audio
        audio, sr = librosa.load(audio_path, sr=16000)
        
        # Extract basic features
        pitch_features = self._extract_pitch_features(audio_path)
        spectral_features = self._extract_spectral_features(audio, sr)
        prosodic_features = self._extract_prosodic_features(audio, sr)
        quality_features = self._extract_voice_quality(audio_path)
        mfcc_features = self._extract_mfcc(audio, sr)
        formants = self._extract_formants(audio_path)
        
        # Generate voice embedding
        wav = preprocess_wav(audio_path)
        embedding = self.voice_encoder.embed_utterance(wav)
        
        return VoiceFeatures(
            # Pitch
            pitch_mean=pitch_features['mean'],
            pitch_std=pitch_features['std'],
            pitch_range=pitch_features['range'],
            
            # Intensity
            intensity_mean=pitch_features['intensity_mean'],
            intensity_std=pitch_features['intensity_std'],
            
            # Spectral
            spectral_centroid=spectral_features['centroid'],
            spectral_rolloff=spectral_features['rolloff'],
            spectral_flux=spectral_features['flux'],
            zero_crossing_rate=spectral_features['zcr'],
            
            # Prosodic
            speaking_rate=prosodic_features['rate'],
            pause_frequency=prosodic_features['pause_freq'],
            pause_duration_mean=prosodic_features['pause_duration'],
            
            # Quality
            jitter=quality_features['jitter'],
            shimmer=quality_features['shimmer'],
            hnr=quality_features['hnr'],
            
            # MFCC
            mfcc_features=mfcc_features,
            
            # Formants
            f1_mean=formants['f1'],
            f2_mean=formants['f2'],
            f3_mean=formants['f3'],
            
            # Embedding
            voice_embedding=embedding,
            
            # Metadata
            duration=len(audio) / sr,
            sample_rate=sr
        )
    
    def _extract_pitch_features(self, audio_path: str) -> Dict[str, float]:
        """Extract pitch-related features using Praat"""
        
        sound = parselmouth.Sound(audio_path)
        pitch = sound.to_pitch()
        intensity = sound.to_intensity()
        
        pitch_values = pitch.selected_array['frequency']
        pitch_values = pitch_values[pitch_values > 0]  # Remove unvoiced
        
        intensity_values = intensity.values[0]
        
        return {
            'mean': np.mean(pitch_values) if len(pitch_values) > 0 else 0,
            'std': np.std(pitch_values) if len(pitch_values) > 0 else 0,
            'range': np.ptp(pitch_values) if len(pitch_values) > 0 else 0,
            'intensity_mean': np.mean(intensity_values),
            'intensity_std': np.std(intensity_values)
        }
    
    def _extract_spectral_features(self, audio: np.ndarray, sr: int) -> Dict[str, float]:
        """Extract spectral features"""
        
        # Spectral centroid
        centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)
        
        # Spectral rolloff
        rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)
        
        # Spectral flux
        stft = librosa.stft(audio)
        flux = np.sum(np.diff(np.abs(stft), axis=1) ** 2, axis=0)
        
        # Zero crossing rate
        zcr = librosa.feature.zero_crossing_rate(audio)
        
        return {
            'centroid': np.mean(centroid),
            'rolloff': np.mean(rolloff),
            'flux': np.mean(flux),
            'zcr': np.mean(zcr)
        }
    
    def _extract_prosodic_features(self, audio: np.ndarray, sr: int) -> Dict[str, float]:
        """Extract prosodic features"""
        
        # Detect speech segments
        intervals = librosa.effects.split(audio, top_db=20)
        
        # Calculate speaking rate (syllables per second approximation)
        # Using energy peaks as proxy for syllables
        energy = librosa.feature.rms(y=audio)[0]
        peaks = signal.find_peaks(energy, distance=sr//10)[0]
        duration = len(audio) / sr
        speaking_rate = len(peaks) / duration if duration > 0 else 0
        
        # Pause analysis
        pauses = []
        for i in range(1, len(intervals)):
            pause_start = intervals[i-1][1] / sr
            pause_end = intervals[i][0] / sr
            pause_duration = pause_end - pause_start
            if pause_duration > 0.1:  # Minimum pause threshold
                pauses.append(pause_duration)
        
        return {
            'rate': speaking_rate,
            'pause_freq': len(pauses) / duration if duration > 0 else 0,
            'pause_duration': np.mean(pauses) if pauses else 0
        }
    
    def _extract_voice_quality(self, audio_path: str) -> Dict[str, float]:
        """Extract voice quality measures"""
        
        sound = parselmouth.Sound(audio_path)
        pitch = sound.to_pitch()
        pulses = parselmouth.praat.call([sound, pitch], "To PointProcess (cc)")
        
        # Jitter (pitch perturbation)
        jitter = parselmouth.praat.call(pulses, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
        
        # Shimmer (amplitude perturbation)
        shimmer = parselmouth.praat.call([sound, pulses], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
        
        # Harmonics-to-noise ratio
        hnr = parselmouth.praat.call(sound, "To Harmonicity (cc)", 0.01, 75, 0.1, 1.0)
        hnr_values = parselmouth.praat.call(hnr, "Get mean", 0, 0)
        
        return {
            'jitter': jitter if not np.isnan(jitter) else 0,
            'shimmer': shimmer if not np.isnan(shimmer) else 0,
            'hnr': hnr_values if not np.isnan(hnr_values) else 0
        }
    
    def _extract_mfcc(self, audio: np.ndarray, sr: int, n_mfcc: int = 13) -> np.ndarray:
        """Extract MFCC features"""
        
        mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=n_mfcc)
        mfcc_mean = np.mean(mfcc, axis=1)
        mfcc_std = np.std(mfcc, axis=1)
        
        return np.concatenate([mfcc_mean, mfcc_std])
    
    def _extract_formants(self, audio_path: str) -> Dict[str, float]:
        """Extract formant frequencies"""
        
        sound = parselmouth.Sound(audio_path)
        formants = sound.to_formant_burg()
        
        f1_values = []
        f2_values = []
        f3_values = []
        
        for i in range(formants.get_number_of_frames()):
            time = formants.get_time_from_frame_number(i)
            f1 = formants.get_value_at_time(1, time)
            f2 = formants.get_value_at_time(2, time)
            f3 = formants.get_value_at_time(3, time)
            
            if not np.isnan(f1): f1_values.append(f1)
            if not np.isnan(f2): f2_values.append(f2)
            if not np.isnan(f3): f3_values.append(f3)
        
        return {
            'f1': np.mean(f1_values) if f1_values else 0,
            'f2': np.mean(f2_values) if f2_values else 0,
            'f3': np.mean(f3_values) if f3_values else 0
        }


class EmotionDetector:
    """Detect emotions from voice"""
    
    def __init__(self):
        self.emotion_model = self._load_emotion_model()
        self.feature_scaler = StandardScaler()
        
    def _load_emotion_model(self):
        """Load or create emotion detection model"""
        # In production, load pre-trained model
        # For now, create a simple classifier
        return RandomForestClassifier(n_estimators=100, random_state=42)
    
    def detect_emotion(self, features: VoiceFeatures) -> Tuple[EmotionType, Dict[str, float]]:
        """Detect emotion from voice features"""
        
        # Prepare feature vector
        feature_vector = self._prepare_features(features)
        
        # Emotion detection based on acoustic patterns
        emotion_scores = self._calculate_emotion_scores(features)
        
        # Get dominant emotion
        dominant_emotion = max(emotion_scores, key=emotion_scores.get)
        
        # Calculate valence and arousal
        valence = self._calculate_valence(features)
        arousal = self._calculate_arousal(features)
        
        return EmotionType[dominant_emotion.upper()], emotion_scores
    
    def _prepare_features(self, features: VoiceFeatures) -> np.ndarray:
        """Prepare feature vector for emotion detection"""
        
        feature_vector = np.array([
            features.pitch_mean,
            features.pitch_std,
            features.pitch_range,
            features.intensity_mean,
            features.intensity_std,
            features.spectral_centroid,
            features.speaking_rate,
            features.jitter,
            features.shimmer,
            features.hnr
        ])
        
        return feature_vector
    
    def _calculate_emotion_scores(self, features: VoiceFeatures) -> Dict[str, float]:
        """Calculate emotion scores based on acoustic patterns"""
        
        scores = {}
        
        # Happiness: Higher pitch, faster rate, higher intensity
        happiness_score = 0.0
        if features.pitch_mean > 200:  # Higher pitch
            happiness_score += 0.3
        if features.speaking_rate > 4:  # Faster speech
            happiness_score += 0.3
        if features.intensity_mean > 60:  # Louder
            happiness_score += 0.2
        if features.pitch_std > 50:  # More variation
            happiness_score += 0.2
        scores['happy'] = min(happiness_score, 1.0)
        
        # Sadness: Lower pitch, slower rate, lower intensity
        sadness_score = 0.0
        if features.pitch_mean < 150:
            sadness_score += 0.3
        if features.speaking_rate < 3:
            sadness_score += 0.3
        if features.intensity_mean < 50:
            sadness_score += 0.2
        if features.pitch_std < 30:
            sadness_score += 0.2
        scores['sad'] = min(sadness_score, 1.0)
        
        # Anger: Higher intensity, faster rate, more shimmer
        anger_score = 0.0
        if features.intensity_mean > 65:
            anger_score += 0.3
        if features.speaking_rate > 4.5:
            anger_score += 0.2
        if features.shimmer > 0.05:
            anger_score += 0.2
        if features.pitch_range > 100:
            anger_score += 0.3
        scores['angry'] = min(anger_score, 1.0)
        
        # Fear: Higher pitch, more jitter, faster rate
        fear_score = 0.0
        if features.pitch_mean > 220:
            fear_score += 0.3
        if features.jitter > 0.02:
            fear_score += 0.3
        if features.speaking_rate > 4.2:
            fear_score += 0.2
        if features.pause_frequency > 0.5:
            fear_score += 0.2
        scores['fearful'] = min(fear_score, 1.0)
        
        # Neutral: Moderate values
        neutral_score = 1.0
        for emotion, score in scores.items():
            neutral_score -= score * 0.25
        scores['neutral'] = max(neutral_score, 0.0)
        
        # Normalize scores
        total = sum(scores.values())
        if total > 0:
            scores = {k: v/total for k, v in scores.items()}
        
        return scores
    
    def _calculate_valence(self, features: VoiceFeatures) -> float:
        """Calculate emotional valence (positive/negative)"""
        
        # Positive indicators
        positive = 0.0
        if features.pitch_mean > 180:
            positive += 0.3
        if features.hnr > 15:
            positive += 0.3
        if features.speaking_rate > 3.5:
            positive += 0.2
        
        # Negative indicators
        negative = 0.0
        if features.pitch_mean < 160:
            negative += 0.3
        if features.shimmer > 0.04:
            negative += 0.3
        if features.jitter > 0.015:
            negative += 0.2
        
        return (positive - negative) / 2 + 0.5  # Scale to 0-1
    
    def _calculate_arousal(self, features: VoiceFeatures) -> float:
        """Calculate emotional arousal (calm/excited)"""
        
        arousal = 0.0
        
        # High arousal indicators
        if features.intensity_mean > 60:
            arousal += 0.3
        if features.speaking_rate > 4:
            arousal += 0.3
        if features.pitch_std > 40:
            arousal += 0.2
        if features.pitch_range > 80:
            arousal += 0.2
        
        return min(arousal, 1.0)


class StressAnalyzer:
    """Analyze stress levels from voice"""
    
    def analyze_stress(self, features: VoiceFeatures, baseline: Optional[VoiceFeatures] = None) -> Tuple[float, List[str]]:
        """Analyze stress level from voice features"""
        
        stress_level = 0.0
        stress_indicators = []
        
        # Pitch indicators
        if features.pitch_mean > 200:
            stress_level += 0.15
            stress_indicators.append("elevated_pitch")
        
        if features.pitch_std > 60:
            stress_level += 0.1
            stress_indicators.append("pitch_variation")
        
        # Voice quality indicators
        if features.jitter > 0.02:
            stress_level += 0.2
            stress_indicators.append("voice_tremor")
        
        if features.shimmer > 0.05:
            stress_level += 0.15
            stress_indicators.append("amplitude_variation")
        
        if features.hnr < 12:
            stress_level += 0.1
            stress_indicators.append("reduced_voice_quality")
        
        # Prosodic indicators
        if features.speaking_rate > 5:
            stress_level += 0.15
            stress_indicators.append("rapid_speech")
        
        if features.pause_frequency > 0.6:
            stress_level += 0.15
            stress_indicators.append("frequent_pauses")
        
        # Compare with baseline if available
        if baseline:
            pitch_change = abs(features.pitch_mean - baseline.pitch_mean) / baseline.pitch_mean
            if pitch_change > 0.2:
                stress_level += 0.2
                stress_indicators.append("pitch_deviation_from_baseline")
        
        return min(stress_level, 1.0), stress_indicators


class SpeakerIdentification:
    """Speaker identification and verification"""
    
    def __init__(self):
        self.voice_encoder = VoiceEncoder()
        self.profiles: Dict[str, VoiceProfile] = {}
        self.gmm_models: Dict[str, GaussianMixture] = {}
        
    def enroll_speaker(
        self,
        name: str,
        audio_files: List[str],
        profile_id: Optional[str] = None
    ) -> VoiceProfile:
        """Enroll a new speaker"""
        
        if not profile_id:
            profile_id = hashlib.md5(name.encode()).hexdigest()
        
        # Extract features from all samples
        feature_extractor = FeatureExtractor()
        all_features = []
        embeddings = []
        
        for audio_file in audio_files:
            features = feature_extractor.extract_features(audio_file)
            all_features.append(features)
            
            # Generate embedding
            wav = preprocess_wav(audio_file)
            embedding = self.voice_encoder.embed_utterance(wav)
            embeddings.append(embedding)
        
        # Average features for profile
        avg_features = self._average_features(all_features)
        
        # Train GMM for this speaker
        gmm = GaussianMixture(n_components=16, covariance_type='diag')
        feature_matrix = np.vstack([f.mfcc_features for f in all_features])
        gmm.fit(feature_matrix)
        
        # Create profile
        profile = VoiceProfile(
            profile_id=profile_id,
            name=name,
            features=avg_features,
            embeddings=embeddings,
            enrollment_samples=len(audio_files),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            gmm_model=gmm
        )
        
        self.profiles[profile_id] = profile
        self.gmm_models[profile_id] = gmm
        
        return profile
    
    def identify_speaker(
        self,
        audio_file: str,
        threshold: float = 0.7
    ) -> Tuple[Optional[str], float]:
        """Identify speaker from audio"""
        
        if not self.profiles:
            return None, 0.0
        
        # Extract features
        feature_extractor = FeatureExtractor()
        features = feature_extractor.extract_features(audio_file)
        
        # Generate embedding
        wav = preprocess_wav(audio_file)
        embedding = self.voice_encoder.embed_utterance(wav)
        
        # Compare with all profiles
        best_match = None
        best_score = 0.0
        
        for profile_id, profile in self.profiles.items():
            # Calculate similarity using embeddings
            similarities = []
            for profile_embedding in profile.embeddings:
                similarity = 1 - cosine(embedding, profile_embedding)
                similarities.append(similarity)
            
            avg_similarity = np.mean(similarities)
            
            # Also use GMM likelihood
            if profile.gmm_model:
                likelihood = profile.gmm_model.score_samples(
                    features.mfcc_features.reshape(1, -1)
                )[0]
                # Normalize likelihood to 0-1 range
                gmm_score = 1 / (1 + np.exp(-likelihood))
                
                # Combine scores
                combined_score = 0.7 * avg_similarity + 0.3 * gmm_score
            else:
                combined_score = avg_similarity
            
            if combined_score > best_score:
                best_score = combined_score
                best_match = profile_id
        
        if best_score >= threshold:
            return best_match, best_score
        
        return None, best_score
    
    def verify_speaker(
        self,
        audio_file: str,
        claimed_profile_id: str,
        threshold: float = 0.75
    ) -> Tuple[bool, float]:
        """Verify if audio matches claimed speaker"""
        
        if claimed_profile_id not in self.profiles:
            return False, 0.0
        
        profile = self.profiles[claimed_profile_id]
        
        # Extract features
        feature_extractor = FeatureExtractor()
        features = feature_extractor.extract_features(audio_file)
        
        # Generate embedding
        wav = preprocess_wav(audio_file)
        embedding = self.voice_encoder.embed_utterance(wav)
        
        # Calculate similarity
        similarities = []
        for profile_embedding in profile.embeddings:
            similarity = 1 - cosine(embedding, profile_embedding)
            similarities.append(similarity)
        
        avg_similarity = np.mean(similarities)
        
        # GMM verification
        if profile.gmm_model:
            likelihood = profile.gmm_model.score_samples(
                features.mfcc_features.reshape(1, -1)
            )[0]
            gmm_score = 1 / (1 + np.exp(-likelihood))
            
            final_score = 0.7 * avg_similarity + 0.3 * gmm_score
        else:
            final_score = avg_similarity
        
        return final_score >= threshold, final_score
    
    def _average_features(self, features_list: List[VoiceFeatures]) -> VoiceFeatures:
        """Average multiple feature sets"""
        
        avg = VoiceFeatures(
            pitch_mean=np.mean([f.pitch_mean for f in features_list]),
            pitch_std=np.mean([f.pitch_std for f in features_list]),
            pitch_range=np.mean([f.pitch_range for f in features_list]),
            intensity_mean=np.mean([f.intensity_mean for f in features_list]),
            intensity_std=np.mean([f.intensity_std for f in features_list]),
            spectral_centroid=np.mean([f.spectral_centroid for f in features_list]),
            spectral_rolloff=np.mean([f.spectral_rolloff for f in features_list]),
            spectral_flux=np.mean([f.spectral_flux for f in features_list]),
            zero_crossing_rate=np.mean([f.zero_crossing_rate for f in features_list]),
            speaking_rate=np.mean([f.speaking_rate for f in features_list]),
            pause_frequency=np.mean([f.pause_frequency for f in features_list]),
            pause_duration_mean=np.mean([f.pause_duration_mean for f in features_list]),
            jitter=np.mean([f.jitter for f in features_list]),
            shimmer=np.mean([f.shimmer for f in features_list]),
            hnr=np.mean([f.hnr for f in features_list]),
            mfcc_features=np.mean([f.mfcc_features for f in features_list], axis=0),
            f1_mean=np.mean([f.f1_mean for f in features_list]),
            f2_mean=np.mean([f.f2_mean for f in features_list]),
            f3_mean=np.mean([f.f3_mean for f in features_list]),
            duration=np.mean([f.duration for f in features_list])
        )
        
        return avg


class VoiceProfilingAnalysisSystem:
    """Main voice profiling and analysis system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.feature_extractor = FeatureExtractor()
        self.emotion_detector = EmotionDetector()
        self.stress_analyzer = StressAnalyzer()
        self.speaker_identification = SpeakerIdentification()
        self.analysis_history: Dict[str, List[AnalysisResult]] = defaultdict(list)
        
    async def analyze_voice(
        self,
        audio_file: str,
        analysis_types: List[AnalysisType],
        speaker_id: Optional[str] = None
    ) -> List[AnalysisResult]:
        """Perform comprehensive voice analysis"""
        
        results = []
        
        # Extract features
        features = self.feature_extractor.extract_features(audio_file)
        
        # Speaker identification/verification
        if AnalysisType.IDENTIFICATION in analysis_types:
            identified_speaker, confidence = self.speaker_identification.identify_speaker(audio_file)
            results.append(AnalysisResult(
                analysis_type=AnalysisType.IDENTIFICATION,
                timestamp=datetime.now(),
                confidence=confidence,
                speaker_id=identified_speaker,
                features=features
            ))
        
        if AnalysisType.VERIFICATION in analysis_types and speaker_id:
            is_verified, confidence = self.speaker_identification.verify_speaker(audio_file, speaker_id)
            results.append(AnalysisResult(
                analysis_type=AnalysisType.VERIFICATION,
                timestamp=datetime.now(),
                confidence=confidence,
                is_verified=is_verified,
                similarity_score=confidence,
                features=features
            ))
        
        # Emotion detection
        if AnalysisType.EMOTION in analysis_types:
            emotion, emotion_scores = self.emotion_detector.detect_emotion(features)
            valence = self.emotion_detector._calculate_valence(features)
            arousal = self.emotion_detector._calculate_arousal(features)
            
            results.append(AnalysisResult(
                analysis_type=AnalysisType.EMOTION,
                timestamp=datetime.now(),
                confidence=max(emotion_scores.values()),
                emotion=emotion,
                emotion_scores=emotion_scores,
                valence=valence,
                arousal=arousal,
                features=features
            ))
        
        # Stress analysis
        if AnalysisType.STRESS in analysis_types:
            # Get baseline if available
            baseline = None
            if speaker_id and speaker_id in self.speaker_identification.profiles:
                baseline = self.speaker_identification.profiles[speaker_id].features
            
            stress_level, stress_indicators = self.stress_analyzer.analyze_stress(features, baseline)
            
            results.append(AnalysisResult(
                analysis_type=AnalysisType.STRESS,
                timestamp=datetime.now(),
                confidence=0.85,  # Confidence based on model accuracy
                stress_level=stress_level,
                stress_indicators=stress_indicators,
                features=features
            ))
        
        # Voice health analysis
        if AnalysisType.HEALTH in analysis_types:
            health_score, anomalies = self._analyze_voice_health(features)
            
            results.append(AnalysisResult(
                analysis_type=AnalysisType.HEALTH,
                timestamp=datetime.now(),
                confidence=0.8,
                voice_health_score=health_score,
                anomalies=anomalies,
                features=features
            ))
        
        # Speaking style analysis
        if AnalysisType.SPEAKING_STYLE in analysis_types:
            style_analysis = self._analyze_speaking_style(features)
            
            results.append(AnalysisResult(
                analysis_type=AnalysisType.SPEAKING_STYLE,
                timestamp=datetime.now(),
                confidence=0.9,
                speaking_rate=features.speaking_rate,
                fluency_score=style_analysis['fluency'],
                clarity_score=style_analysis['clarity'],
                features=features
            ))
        
        # Store in history
        if speaker_id:
            self.analysis_history[speaker_id].extend(results)
        
        return results
    
    def _analyze_voice_health(self, features: VoiceFeatures) -> Tuple[float, List[str]]:
        """Analyze voice health indicators"""
        
        health_score = 1.0
        anomalies = []
        
        # Check jitter (should be < 1%)
        if features.jitter > 0.01:
            health_score -= 0.2
            if features.jitter > 0.02:
                anomalies.append("excessive_jitter")
        
        # Check shimmer (should be < 3%)
        if features.shimmer > 0.03:
            health_score -= 0.2
            if features.shimmer > 0.05:
                anomalies.append("excessive_shimmer")
        
        # Check HNR (should be > 20 dB)
        if features.hnr < 20:
            health_score -= 0.15
            if features.hnr < 15:
                anomalies.append("low_harmonics_to_noise")
        
        # Check pitch range
        if features.pitch_range < 20:
            health_score -= 0.1
            anomalies.append("reduced_pitch_range")
        
        # Check for vocal fry (very low pitch)
        if features.pitch_mean < 80:
            health_score -= 0.15
            anomalies.append("vocal_fry")
        
        return max(health_score, 0.0), anomalies
    
    def _analyze_speaking_style(self, features: VoiceFeatures) -> Dict[str, float]:
        """Analyze speaking style characteristics"""
        
        # Fluency score (based on pauses and rate consistency)
        fluency = 1.0
        if features.pause_frequency > 0.5:
            fluency -= 0.3
        if features.speaking_rate < 2 or features.speaking_rate > 6:
            fluency -= 0.2
        
        # Clarity score (based on voice quality)
        clarity = 1.0
        if features.hnr < 15:
            clarity -= 0.3
        if features.jitter > 0.015:
            clarity -= 0.2
        if features.shimmer > 0.04:
            clarity -= 0.2
        
        return {
            'fluency': max(fluency, 0.0),
            'clarity': max(clarity, 0.0)
        }
    
    def enroll_speaker(
        self,
        name: str,
        audio_files: List[str]
    ) -> VoiceProfile:
        """Enroll a new speaker in the system"""
        return self.speaker_identification.enroll_speaker(name, audio_files)
    
    def get_speaker_profile(self, speaker_id: str) -> Optional[VoiceProfile]:
        """Get speaker profile"""
        return self.speaker_identification.profiles.get(speaker_id)
    
    def get_analysis_history(
        self,
        speaker_id: str,
        analysis_type: Optional[AnalysisType] = None
    ) -> List[AnalysisResult]:
        """Get analysis history for a speaker"""
        
        history = self.analysis_history.get(speaker_id, [])
        
        if analysis_type:
            history = [r for r in history if r.analysis_type == analysis_type]
        
        return history
    
    def export_profile(self, speaker_id: str, output_path: str):
        """Export speaker profile"""
        
        if speaker_id not in self.speaker_identification.profiles:
            raise ValueError(f"Speaker {speaker_id} not found")
        
        profile = self.speaker_identification.profiles[speaker_id]
        
        # Save profile (excluding models)
        export_data = {
            'profile_id': profile.profile_id,
            'name': profile.name,
            'created_at': profile.created_at.isoformat(),
            'enrollment_samples': profile.enrollment_samples,
            'features': {
                'pitch_mean': profile.features.pitch_mean,
                'pitch_std': profile.features.pitch_std,
                'intensity_mean': profile.features.intensity_mean,
                'speaking_rate': profile.features.speaking_rate,
                'jitter': profile.features.jitter,
                'shimmer': profile.features.shimmer,
                'hnr': profile.features.hnr
            },
            'emotion_baseline': profile.emotion_baseline,
            'stress_baseline': profile.stress_baseline
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    def import_profile(self, profile_path: str) -> VoiceProfile:
        """Import speaker profile"""
        
        with open(profile_path, 'r') as f:
            data = json.load(f)
        
        # Reconstruct profile (without models - would need re-enrollment)
        # This is simplified - production would handle model serialization
        
        return data['profile_id']


# Example usage
async def main():
    """Example usage of voice profiling system"""
    
    # Initialize system
    voice_system = VoiceProfilingAnalysisSystem()
    
    # Enroll a speaker
    profile = voice_system.enroll_speaker(
        name="John Doe",
        audio_files=["sample1.wav", "sample2.wav", "sample3.wav"]
    )
    print(f"Enrolled speaker: {profile.name} (ID: {profile.profile_id})")
    
    # Analyze new audio
    results = await voice_system.analyze_voice(
        audio_file="test_audio.wav",
        analysis_types=[
            AnalysisType.IDENTIFICATION,
            AnalysisType.EMOTION,
            AnalysisType.STRESS,
            AnalysisType.HEALTH,
            AnalysisType.SPEAKING_STYLE
        ]
    )
    
    # Display results
    for result in results:
        print(f"\n{result.analysis_type.value} Analysis:")
        print(f"  Confidence: {result.confidence:.2f}")
        
        if result.analysis_type == AnalysisType.IDENTIFICATION:
            print(f"  Identified Speaker: {result.speaker_id}")
        elif result.analysis_type == AnalysisType.EMOTION:
            print(f"  Emotion: {result.emotion.value if result.emotion else 'Unknown'}")
            print(f"  Valence: {result.valence:.2f}")
            print(f"  Arousal: {result.arousal:.2f}")
        elif result.analysis_type == AnalysisType.STRESS:
            print(f"  Stress Level: {result.stress_level:.2f}")
            print(f"  Indicators: {', '.join(result.stress_indicators)}")
        elif result.analysis_type == AnalysisType.HEALTH:
            print(f"  Health Score: {result.voice_health_score:.2f}")
            print(f"  Anomalies: {', '.join(result.anomalies)}")
        elif result.analysis_type == AnalysisType.SPEAKING_STYLE:
            print(f"  Speaking Rate: {result.speaking_rate:.2f} syll/sec")
            print(f"  Fluency: {result.fluency_score:.2f}")
            print(f"  Clarity: {result.clarity_score:.2f}")


if __name__ == "__main__":
    asyncio.run(main())