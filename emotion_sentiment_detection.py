"""
Comprehensive Emotion and Sentiment Detection System

This module provides advanced emotion detection from voice characteristics,
sentiment analysis combining text and audio features, mood tracking throughout
long recordings, stress and fatigue detection, and emotional timeline visualization.

Features:
- Voice-based emotion detection using acoustic features
- Multi-modal sentiment analysis (text + audio)
- Continuous mood tracking for long recordings
- Stress and fatigue detection from voice patterns
- Emotional timeline visualization and analysis
- Real-time emotion monitoring
- Batch processing for historical analysis
"""

import os
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

# Audio processing
import librosa
import soundfile as sf
from scipy import signal
from scipy.stats import zscore

# Machine learning
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

# Text analysis
import openai
from textblob import TextBlob
import spacy

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
class EmotionResult:
    """Result of emotion detection analysis"""
    timestamp: float
    duration: float
    primary_emotion: str
    emotion_scores: Dict[str, float]
    confidence: float
    arousal: float  # Energy level (0-1)
    valence: float  # Positive/negative (0-1)
    intensity: float  # Emotion strength (0-1)

@dataclass
class SentimentResult:
    """Result of sentiment analysis"""
    timestamp: float
    duration: float
    sentiment: str  # positive, negative, neutral
    polarity: float  # -1 to 1
    subjectivity: float  # 0 to 1
    confidence: float
    text_sentiment: float
    audio_sentiment: float

@dataclass
class MoodState:
    """Mood state tracking"""
    timestamp: float
    mood: str
    energy_level: float
    stress_level: float
    fatigue_level: float
    engagement_level: float
    emotional_stability: float

@dataclass
class StressFatigueResult:
    """Stress and fatigue detection result"""
    timestamp: float
    stress_level: float  # 0-1
    fatigue_level: float  # 0-1
    cognitive_load: float  # 0-1
    vocal_strain: float  # 0-1
    speaking_rate_deviation: float
    pause_frequency: float

class AudioFeatureExtractor:
    """Extract acoustic features for emotion detection"""
    
    def __init__(self):
        self.sample_rate = 22050
        self.hop_length = 512
        self.n_mels = 128
        
    def extract_prosodic_features(self, audio_path: str) -> Dict[str, float]:
        """Extract prosodic features (pitch, rhythm, intensity)"""
        try:
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Pitch features
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr, hop_length=self.hop_length)
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)
            
            pitch_values = np.array(pitch_values)
            
            # Rhythm features
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            
            # Intensity features
            rms = librosa.feature.rms(y=y, hop_length=self.hop_length)[0]
            
            # Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            zero_crossing_rate = librosa.feature.zero_crossing_rate(y)[0]
            
            # MFCC features
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            
            features = {
                # Pitch features
                'pitch_mean': np.mean(pitch_values) if len(pitch_values) > 0 else 0,
                'pitch_std': np.std(pitch_values) if len(pitch_values) > 0 else 0,
                'pitch_range': np.ptp(pitch_values) if len(pitch_values) > 0 else 0,
                'pitch_median': np.median(pitch_values) if len(pitch_values) > 0 else 0,
                
                # Rhythm features
                'tempo': tempo,
                'rhythm_regularity': np.std(np.diff(beats)) if len(beats) > 1 else 0,
                
                # Intensity features
                'intensity_mean': np.mean(rms),
                'intensity_std': np.std(rms),
                'intensity_range': np.ptp(rms),
                
                # Spectral features
                'spectral_centroid_mean': np.mean(spectral_centroids),
                'spectral_centroid_std': np.std(spectral_centroids),
                'spectral_rolloff_mean': np.mean(spectral_rolloff),
                'zero_crossing_rate_mean': np.mean(zero_crossing_rate),
                
                # MFCC features (first 5 coefficients)
                'mfcc_1_mean': np.mean(mfccs[0]),
                'mfcc_2_mean': np.mean(mfccs[1]),
                'mfcc_3_mean': np.mean(mfccs[2]),
                'mfcc_4_mean': np.mean(mfccs[3]),
                'mfcc_5_mean': np.mean(mfccs[4]),
                
                # Voice quality indicators
                'jitter': self._calculate_jitter(pitch_values),
                'shimmer': self._calculate_shimmer(rms),
                'harmonics_to_noise_ratio': self._calculate_hnr(y, sr),
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting prosodic features: {e}")
            return {}
    
    def _calculate_jitter(self, pitch_values: np.ndarray) -> float:
        """Calculate pitch jitter (pitch variation)"""
        if len(pitch_values) < 2:
            return 0.0
        
        period_diffs = np.abs(np.diff(1.0 / pitch_values))
        return np.mean(period_diffs) if len(period_diffs) > 0 else 0.0
    
    def _calculate_shimmer(self, rms_values: np.ndarray) -> float:
        """Calculate amplitude shimmer (amplitude variation)"""
        if len(rms_values) < 2:
            return 0.0
        
        amplitude_diffs = np.abs(np.diff(rms_values))
        return np.mean(amplitude_diffs) / np.mean(rms_values) if np.mean(rms_values) > 0 else 0.0
    
    def _calculate_hnr(self, y: np.ndarray, sr: int) -> float:
        """Calculate Harmonics-to-Noise Ratio"""
        try:
            # Simple HNR estimation using autocorrelation
            autocorr = np.correlate(y, y, mode='full')
            autocorr = autocorr[autocorr.size // 2:]
            
            # Find the first peak (fundamental frequency)
            peaks = signal.find_peaks(autocorr[1:], height=0.1 * np.max(autocorr))[0]
            
            if len(peaks) > 0:
                fundamental_peak = autocorr[peaks[0] + 1]
                noise_floor = np.mean(autocorr[peaks[0] + 1:])
                hnr = 10 * np.log10(fundamental_peak / noise_floor) if noise_floor > 0 else 0
                return max(0, min(40, hnr))  # Clamp between 0 and 40 dB
            
            return 0.0
            
        except Exception:
            return 0.0

class EmotionDetector:
    """Advanced emotion detection from voice characteristics"""
    
    def __init__(self):
        self.feature_extractor = AudioFeatureExtractor()
        self.emotion_model = None
        self.scaler = StandardScaler()
        self.emotion_labels = [
            'neutral', 'happy', 'sad', 'angry', 'fear', 
            'surprise', 'disgust', 'excited', 'calm', 'stressed'
        ]
        self.model_path = "models/emotion_model.joblib"
        self.scaler_path = "models/emotion_scaler.joblib"
        
        # Load or create model
        self._load_or_create_model()
    
    def _load_or_create_model(self):
        """Load existing model or create a new one"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.emotion_model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                logger.info("Loaded existing emotion detection model")
            else:
                self._create_default_model()
        except Exception as e:
            logger.error(f"Error loading emotion model: {e}")
            self._create_default_model()
    
    def _create_default_model(self):
        """Create a default emotion detection model"""
        try:
            # Create directories
            os.makedirs("models", exist_ok=True)
            
            # Create a simple rule-based model for demonstration
            self.emotion_model = RandomForestClassifier(n_estimators=100, random_state=42)
            
            # Generate synthetic training data for demonstration
            n_samples = 1000
            n_features = 20
            
            X_synthetic = np.random.randn(n_samples, n_features)
            y_synthetic = np.random.choice(len(self.emotion_labels), n_samples)
            
            # Fit the scaler and model
            X_scaled = self.scaler.fit_transform(X_synthetic)
            self.emotion_model.fit(X_scaled, y_synthetic)
            
            # Save the model
            joblib.dump(self.emotion_model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            
            logger.info("Created default emotion detection model")
            
        except Exception as e:
            logger.error(f"Error creating default model: {e}")
    
    def detect_emotion(self, audio_path: str, segment_duration: float = 3.0) -> List[EmotionResult]:
        """Detect emotions from audio file with temporal segmentation"""
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=22050)
            duration = len(y) / sr
            
            results = []
            segment_samples = int(segment_duration * sr)
            
            for start_time in np.arange(0, duration, segment_duration):
                start_sample = int(start_time * sr)
                end_sample = min(start_sample + segment_samples, len(y))
                
                if end_sample - start_sample < sr * 0.5:  # Skip segments shorter than 0.5s
                    continue
                
                # Extract segment
                segment = y[start_sample:end_sample]
                
                # Save temporary segment
                temp_path = "temp_emotion_segment.wav"
                sf.write(temp_path, segment, sr)
                
                # Extract features
                features = self.feature_extractor.extract_prosodic_features(temp_path)
                
                if features:
                    # Predict emotion
                    emotion_result = self._predict_emotion(features, start_time, segment_duration)
                    results.append(emotion_result)
                
                # Clean up
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
            return results
            
        except Exception as e:
            logger.error(f"Error detecting emotions: {e}")
            return []
    
    def _predict_emotion(self, features: Dict[str, float], timestamp: float, duration: float) -> EmotionResult:
        """Predict emotion from extracted features"""
        try:
            # Convert features to array, ensuring all values are scalars
            feature_values = []
            feature_keys = [
                'pitch_mean', 'pitch_std', 'pitch_range', 'tempo',
                'intensity_mean', 'intensity_std', 'spectral_centroid_mean',
                'spectral_rolloff_mean', 'zero_crossing_rate_mean',
                'mfcc_1_mean', 'mfcc_2_mean', 'mfcc_3_mean', 'mfcc_4_mean', 'mfcc_5_mean',
                'jitter', 'shimmer', 'harmonics_to_noise_ratio', 'rhythm_regularity',
                'intensity_range', 'spectral_centroid_std'
            ]
            
            for key in feature_keys:
                value = features.get(key, 0)
                # Ensure value is a scalar
                if isinstance(value, (list, np.ndarray)):
                    value = np.mean(value) if len(value) > 0 else 0
                # Handle NaN and infinite values
                if not np.isfinite(value):
                    value = 0
                feature_values.append(float(value))
            
            feature_vector = np.array(feature_values).reshape(1, -1)
            
            # Scale features
            feature_vector_scaled = self.scaler.transform(feature_vector)
            
            # Predict emotion probabilities
            emotion_probs = self.emotion_model.predict_proba(feature_vector_scaled)[0]
            primary_emotion_idx = np.argmax(emotion_probs)
            primary_emotion = self.emotion_labels[primary_emotion_idx]
            confidence = emotion_probs[primary_emotion_idx]
            
            # Create emotion scores dictionary
            emotion_scores = {
                emotion: float(prob) for emotion, prob in zip(self.emotion_labels, emotion_probs)
            }
            
            # Calculate arousal and valence
            arousal = self._calculate_arousal(features)
            valence = self._calculate_valence(features, emotion_scores)
            intensity = confidence
            
            return EmotionResult(
                timestamp=timestamp,
                duration=duration,
                primary_emotion=primary_emotion,
                emotion_scores=emotion_scores,
                confidence=confidence,
                arousal=arousal,
                valence=valence,
                intensity=intensity
            )
            
        except Exception as e:
            logger.error(f"Error predicting emotion: {e}")
            return EmotionResult(
                timestamp=timestamp,
                duration=duration,
                primary_emotion='neutral',
                emotion_scores={'neutral': 1.0},
                confidence=0.5,
                arousal=0.5,
                valence=0.5,
                intensity=0.5
            )
    
    def _calculate_arousal(self, features: Dict[str, float]) -> float:
        """Calculate arousal (energy level) from features"""
        # High arousal: high intensity, high pitch, fast tempo
        intensity_factor = min(1.0, features.get('intensity_mean', 0) * 10)
        pitch_factor = min(1.0, features.get('pitch_mean', 0) / 500)
        tempo_factor = min(1.0, features.get('tempo', 0) / 200)
        
        arousal = (intensity_factor + pitch_factor + tempo_factor) / 3
        return max(0.0, min(1.0, arousal))
    
    def _calculate_valence(self, features: Dict[str, float], emotion_scores: Dict[str, float]) -> float:
        """Calculate valence (positive/negative) from features and emotions"""
        # Positive emotions contribute to positive valence
        positive_emotions = ['happy', 'excited', 'surprise', 'calm']
        negative_emotions = ['sad', 'angry', 'fear', 'disgust', 'stressed']
        
        positive_score = sum(emotion_scores.get(emotion, 0) for emotion in positive_emotions)
        negative_score = sum(emotion_scores.get(emotion, 0) for emotion in negative_emotions)
        
        if positive_score + negative_score > 0:
            valence = positive_score / (positive_score + negative_score)
        else:
            valence = 0.5  # Neutral
        
        return max(0.0, min(1.0, valence))

class SentimentAnalyzer:
    """Multi-modal sentiment analysis combining text and audio features"""
    
    def __init__(self):
        self.emotion_detector = EmotionDetector()
        
        # Load spaCy model for text processing
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
    
    def analyze_sentiment(self, audio_path: str, transcript: str, 
                         segment_duration: float = 3.0) -> List[SentimentResult]:
        """Analyze sentiment combining audio and text features"""
        try:
            # Get emotion detection results
            emotion_results = self.emotion_detector.detect_emotion(audio_path, segment_duration)
            
            # Analyze text sentiment
            text_sentiments = self._analyze_text_sentiment(transcript, emotion_results)
            
            # Combine audio and text sentiment
            combined_results = []
            
            for i, emotion_result in enumerate(emotion_results):
                text_sentiment = text_sentiments[i] if i < len(text_sentiments) else {'polarity': 0, 'subjectivity': 0.5}
                
                # Calculate combined sentiment
                audio_sentiment = self._emotion_to_sentiment(emotion_result)
                combined_sentiment = self._combine_sentiments(audio_sentiment, text_sentiment['polarity'])
                
                # Determine sentiment label
                if combined_sentiment > 0.1:
                    sentiment_label = 'positive'
                elif combined_sentiment < -0.1:
                    sentiment_label = 'negative'
                else:
                    sentiment_label = 'neutral'
                
                result = SentimentResult(
                    timestamp=emotion_result.timestamp,
                    duration=emotion_result.duration,
                    sentiment=sentiment_label,
                    polarity=combined_sentiment,
                    subjectivity=text_sentiment['subjectivity'],
                    confidence=emotion_result.confidence,
                    text_sentiment=text_sentiment['polarity'],
                    audio_sentiment=audio_sentiment
                )
                
                combined_results.append(result)
            
            return combined_results
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return []
    
    def _analyze_text_sentiment(self, transcript: str, emotion_results: List[EmotionResult]) -> List[Dict[str, float]]:
        """Analyze text sentiment for each time segment"""
        try:
            # Split transcript into segments based on emotion results
            words = transcript.split()
            total_duration = emotion_results[-1].timestamp + emotion_results[-1].duration if emotion_results else 0
            
            text_sentiments = []
            
            for emotion_result in emotion_results:
                # Estimate which words correspond to this time segment
                start_ratio = emotion_result.timestamp / total_duration if total_duration > 0 else 0
                end_ratio = (emotion_result.timestamp + emotion_result.duration) / total_duration if total_duration > 0 else 1
                
                start_word = int(start_ratio * len(words))
                end_word = int(end_ratio * len(words))
                
                segment_text = ' '.join(words[start_word:end_word])
                
                # Analyze sentiment using TextBlob
                if segment_text.strip():
                    blob = TextBlob(segment_text)
                    polarity = blob.sentiment.polarity
                    subjectivity = blob.sentiment.subjectivity
                else:
                    polarity = 0.0
                    subjectivity = 0.5
                
                text_sentiments.append({
                    'polarity': polarity,
                    'subjectivity': subjectivity
                })
            
            return text_sentiments
            
        except Exception as e:
            logger.error(f"Error analyzing text sentiment: {e}")
            return [{'polarity': 0, 'subjectivity': 0.5}] * len(emotion_results)
    
    def _emotion_to_sentiment(self, emotion_result: EmotionResult) -> float:
        """Convert emotion to sentiment score"""
        # Map emotions to sentiment values
        emotion_sentiment_map = {
            'happy': 0.8,
            'excited': 0.7,
            'surprise': 0.3,
            'calm': 0.2,
            'neutral': 0.0,
            'sad': -0.6,
            'angry': -0.8,
            'fear': -0.5,
            'disgust': -0.7,
            'stressed': -0.4
        }
        
        # Calculate weighted sentiment based on emotion scores
        sentiment_score = 0.0
        for emotion, score in emotion_result.emotion_scores.items():
            sentiment_value = emotion_sentiment_map.get(emotion, 0.0)
            sentiment_score += sentiment_value * score
        
        return sentiment_score
    
    def _combine_sentiments(self, audio_sentiment: float, text_sentiment: float, 
                           audio_weight: float = 0.4, text_weight: float = 0.6) -> float:
        """Combine audio and text sentiment scores"""
        combined = (audio_sentiment * audio_weight) + (text_sentiment * text_weight)
        return max(-1.0, min(1.0, combined))

class MoodTracker:
    """Continuous mood tracking throughout long recordings"""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.window_size = 30.0  # 30-second windows for mood analysis
        
    def track_mood(self, audio_path: str, transcript: str) -> List[MoodState]:
        """Track mood changes throughout the recording"""
        try:
            # Get sentiment analysis results
            sentiment_results = self.sentiment_analyzer.analyze_sentiment(
                audio_path, transcript, segment_duration=5.0
            )
            
            if not sentiment_results:
                return []
            
            # Group results into mood windows
            mood_states = []
            current_window_start = 0
            
            while current_window_start < sentiment_results[-1].timestamp:
                window_end = current_window_start + self.window_size
                
                # Get sentiment results in this window
                window_results = [
                    result for result in sentiment_results
                    if current_window_start <= result.timestamp < window_end
                ]
                
                if window_results:
                    mood_state = self._calculate_mood_state(window_results, current_window_start)
                    mood_states.append(mood_state)
                
                current_window_start = window_end
            
            return mood_states
            
        except Exception as e:
            logger.error(f"Error tracking mood: {e}")
            return []
    
    def _calculate_mood_state(self, sentiment_results: List[SentimentResult], timestamp: float) -> MoodState:
        """Calculate mood state from sentiment results in a time window"""
        try:
            # Calculate average sentiment metrics
            avg_polarity = np.mean([r.polarity for r in sentiment_results])
            avg_confidence = np.mean([r.confidence for r in sentiment_results])
            
            # Determine primary mood
            if avg_polarity > 0.3:
                mood = 'positive'
            elif avg_polarity < -0.3:
                mood = 'negative'
            elif avg_confidence < 0.5:
                mood = 'uncertain'
            else:
                mood = 'neutral'
            
            # Calculate energy level (based on arousal from emotion detection)
            energy_level = np.mean([
                0.7 if result.sentiment == 'positive' else 0.3 if result.sentiment == 'negative' else 0.5
                for result in sentiment_results
            ])
            
            # Calculate stress level (based on negative emotions and low confidence)
            confidence_stress = np.mean([1.0 - result.confidence for result in sentiment_results])
            polarity_stress = np.mean([max(0, -result.polarity) for result in sentiment_results])
            subjectivity_stress = np.mean([result.subjectivity for result in sentiment_results])
            
            stress_level = np.mean([confidence_stress, polarity_stress, subjectivity_stress])
            
            # Calculate fatigue level (based on decreasing energy over time)
            fatigue_level = max(0, 1.0 - energy_level - avg_confidence)
            
            # Calculate engagement level
            engagement_level = avg_confidence * (1.0 - abs(avg_polarity - 0.2))
            
            # Calculate emotional stability (consistency of emotions)
            polarity_std = np.std([result.polarity for result in sentiment_results])
            emotional_stability = max(0, 1.0 - polarity_std)
            
            return MoodState(
                timestamp=timestamp,
                mood=mood,
                energy_level=max(0, min(1, energy_level)),
                stress_level=max(0, min(1, stress_level)),
                fatigue_level=max(0, min(1, fatigue_level)),
                engagement_level=max(0, min(1, engagement_level)),
                emotional_stability=max(0, min(1, emotional_stability))
            )
            
        except Exception as e:
            logger.error(f"Error calculating mood state: {e}")
            return MoodState(
                timestamp=timestamp,
                mood='neutral',
                energy_level=0.5,
                stress_level=0.5,
                fatigue_level=0.5,
                engagement_level=0.5,
                emotional_stability=0.5
            )

class StressFatigueDetector:
    """Advanced stress and fatigue detection from voice patterns"""
    
    def __init__(self):
        self.feature_extractor = AudioFeatureExtractor()
        
    def detect_stress_fatigue(self, audio_path: str, segment_duration: float = 10.0) -> List[StressFatigueResult]:
        """Detect stress and fatigue indicators from voice patterns"""
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=22050)
            duration = len(y) / sr
            
            results = []
            segment_samples = int(segment_duration * sr)
            
            for start_time in np.arange(0, duration, segment_duration):
                start_sample = int(start_time * sr)
                end_sample = min(start_sample + segment_samples, len(y))
                
                if end_sample - start_sample < sr * 2.0:  # Skip segments shorter than 2s
                    continue
                
                # Extract segment
                segment = y[start_sample:end_sample]
                
                # Save temporary segment
                temp_path = "temp_stress_segment.wav"
                sf.write(temp_path, segment, sr)
                
                # Analyze stress and fatigue indicators
                stress_fatigue_result = self._analyze_stress_fatigue(temp_path, start_time)
                results.append(stress_fatigue_result)
                
                # Clean up
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
            return results
            
        except Exception as e:
            logger.error(f"Error detecting stress and fatigue: {e}")
            return []
    
    def _analyze_stress_fatigue(self, audio_path: str, timestamp: float) -> StressFatigueResult:
        """Analyze stress and fatigue indicators from audio segment"""
        try:
            # Extract acoustic features
            features = self.feature_extractor.extract_prosodic_features(audio_path)
            
            # Load audio for additional analysis
            y, sr = librosa.load(audio_path, sr=22050)
            
            # Calculate stress indicators
            stress_level = self._calculate_stress_level(features, y, sr)
            
            # Calculate fatigue indicators
            fatigue_level = self._calculate_fatigue_level(features, y, sr)
            
            # Calculate cognitive load
            cognitive_load = self._calculate_cognitive_load(features, y, sr)
            
            # Calculate vocal strain
            vocal_strain = self._calculate_vocal_strain(features)
            
            # Calculate speaking rate deviation
            speaking_rate_deviation = self._calculate_speaking_rate_deviation(y, sr)
            
            # Calculate pause frequency
            pause_frequency = self._calculate_pause_frequency(y, sr)
            
            return StressFatigueResult(
                timestamp=timestamp,
                stress_level=max(0, min(1, stress_level)),
                fatigue_level=max(0, min(1, fatigue_level)),
                cognitive_load=max(0, min(1, cognitive_load)),
                vocal_strain=max(0, min(1, vocal_strain)),
                speaking_rate_deviation=speaking_rate_deviation,
                pause_frequency=pause_frequency
            )
            
        except Exception as e:
            logger.error(f"Error analyzing stress and fatigue: {e}")
            return StressFatigueResult(
                timestamp=timestamp,
                stress_level=0.5,
                fatigue_level=0.5,
                cognitive_load=0.5,
                vocal_strain=0.5,
                speaking_rate_deviation=0.0,
                pause_frequency=0.0
            )
    
    def _calculate_stress_level(self, features: Dict[str, float], y: np.ndarray, sr: int) -> float:
        """Calculate stress level from voice characteristics"""
        stress_indicators = []
        
        # High pitch variation indicates stress
        pitch_std = features.get('pitch_std', 0)
        stress_indicators.append(min(1.0, pitch_std / 50))
        
        # High jitter indicates stress
        jitter = features.get('jitter', 0)
        stress_indicators.append(min(1.0, jitter * 1000))
        
        # High shimmer indicates stress
        shimmer = features.get('shimmer', 0)
        stress_indicators.append(min(1.0, shimmer * 10))
        
        # Low HNR indicates stress
        hnr = features.get('harmonics_to_noise_ratio', 20)
        stress_indicators.append(max(0, (20 - hnr) / 20))
        
        # High spectral centroid indicates stress
        spectral_centroid = features.get('spectral_centroid_mean', 0)
        stress_indicators.append(min(1.0, spectral_centroid / 3000))
        
        return np.mean(stress_indicators)
    
    def _calculate_fatigue_level(self, features: Dict[str, float], y: np.ndarray, sr: int) -> float:
        """Calculate fatigue level from voice characteristics"""
        fatigue_indicators = []
        
        # Low intensity indicates fatigue
        intensity = features.get('intensity_mean', 0)
        fatigue_indicators.append(max(0, (0.1 - intensity) / 0.1))
        
        # Low pitch indicates fatigue
        pitch_mean = features.get('pitch_mean', 0)
        fatigue_indicators.append(max(0, (150 - pitch_mean) / 150))
        
        # Slow tempo indicates fatigue
        tempo = features.get('tempo', 120)
        fatigue_indicators.append(max(0, (100 - tempo) / 100))
        
        # Low spectral rolloff indicates fatigue
        spectral_rolloff = features.get('spectral_rolloff_mean', 0)
        fatigue_indicators.append(max(0, (2000 - spectral_rolloff) / 2000))
        
        return np.mean(fatigue_indicators)
    
    def _calculate_cognitive_load(self, features: Dict[str, float], y: np.ndarray, sr: int) -> float:
        """Calculate cognitive load from speech patterns"""
        cognitive_indicators = []
        
        # High rhythm irregularity indicates cognitive load
        rhythm_regularity = features.get('rhythm_regularity', 0)
        cognitive_indicators.append(min(1.0, rhythm_regularity / 10))
        
        # High pitch range indicates cognitive effort
        pitch_range = features.get('pitch_range', 0)
        cognitive_indicators.append(min(1.0, pitch_range / 200))
        
        # Variable intensity indicates cognitive processing
        intensity_std = features.get('intensity_std', 0)
        cognitive_indicators.append(min(1.0, intensity_std / 0.05))
        
        return np.mean(cognitive_indicators)
    
    def _calculate_vocal_strain(self, features: Dict[str, float]) -> float:
        """Calculate vocal strain indicators"""
        strain_indicators = []
        
        # High jitter indicates vocal strain
        jitter = features.get('jitter', 0)
        strain_indicators.append(min(1.0, jitter * 2000))
        
        # High shimmer indicates vocal strain
        shimmer = features.get('shimmer', 0)
        strain_indicators.append(min(1.0, shimmer * 20))
        
        # Low HNR indicates vocal strain
        hnr = features.get('harmonics_to_noise_ratio', 20)
        strain_indicators.append(max(0, (15 - hnr) / 15))
        
        return np.mean(strain_indicators)
    
    def _calculate_speaking_rate_deviation(self, y: np.ndarray, sr: int) -> float:
        """Calculate deviation from normal speaking rate"""
        try:
            # Detect speech segments
            intervals = librosa.effects.split(y, top_db=20)
            
            if len(intervals) < 2:
                return 0.0
            
            # Calculate speaking rate (syllables per second approximation)
            total_speech_time = sum((end - start) / sr for start, end in intervals)
            
            if total_speech_time == 0:
                return 0.0
            
            # Estimate syllables using zero crossing rate peaks
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            estimated_syllables = len(librosa.util.peak_pick(zcr, pre_max=3, post_max=3, pre_avg=3, post_avg=5, delta=0.1, wait=10))
            
            speaking_rate = estimated_syllables / total_speech_time
            normal_rate = 4.5  # Average syllables per second
            
            deviation = abs(speaking_rate - normal_rate) / normal_rate
            return min(1.0, deviation)
            
        except Exception:
            return 0.0
    
    def _calculate_pause_frequency(self, y: np.ndarray, sr: int) -> float:
        """Calculate frequency of pauses in speech"""
        try:
            # Detect silent segments
            intervals = librosa.effects.split(y, top_db=20)
            
            if len(intervals) < 2:
                return 0.0
            
            # Count pauses (gaps between speech segments)
            pauses = len(intervals) - 1
            total_time = len(y) / sr
            
            pause_frequency = pauses / total_time if total_time > 0 else 0
            return min(1.0, pause_frequency / 2.0)  # Normalize assuming max 2 pauses per second
            
        except Exception:
            return 0.0

class EmotionalTimelineVisualizer:
    """Advanced visualization for emotional timeline and analysis"""
    
    def __init__(self):
        self.colors = {
            'happy': '#FFD700',
            'excited': '#FF6347',
            'surprise': '#FF69B4',
            'calm': '#87CEEB',
            'neutral': '#D3D3D3',
            'sad': '#4169E1',
            'angry': '#DC143C',
            'fear': '#8A2BE2',
            'disgust': '#228B22',
            'stressed': '#B22222'
        }
    
    def create_emotion_timeline(self, emotion_results: List[EmotionResult], 
                              output_path: str = "emotion_timeline.html") -> str:
        """Create interactive emotion timeline visualization"""
        try:
            if not emotion_results:
                return ""
            
            # Prepare data
            timestamps = [r.timestamp for r in emotion_results]
            emotions = [r.primary_emotion for r in emotion_results]
            confidences = [r.confidence for r in emotion_results]
            arousals = [r.arousal for r in emotion_results]
            valences = [r.valence for r in emotion_results]
            
            # Create subplots
            fig = make_subplots(
                rows=4, cols=1,
                subplot_titles=['Primary Emotions', 'Confidence', 'Arousal (Energy)', 'Valence (Positive/Negative)'],
                vertical_spacing=0.08
            )
            
            # Emotion timeline
            emotion_colors = [self.colors.get(emotion, '#D3D3D3') for emotion in emotions]
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=emotions,
                    mode='markers+lines',
                    marker=dict(color=emotion_colors, size=10),
                    name='Primary Emotion',
                    hovertemplate='<b>Time:</b> %{x:.1f}s<br><b>Emotion:</b> %{y}<br><b>Confidence:</b> %{customdata:.2f}<extra></extra>',
                    customdata=confidences
                ),
                row=1, col=1
            )
            
            # Confidence timeline
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=confidences,
                    mode='lines+markers',
                    marker=dict(color='blue', size=6),
                    name='Confidence',
                    hovertemplate='<b>Time:</b> %{x:.1f}s<br><b>Confidence:</b> %{y:.2f}<extra></extra>'
                ),
                row=2, col=1
            )
            
            # Arousal timeline
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=arousals,
                    mode='lines+markers',
                    marker=dict(color='red', size=6),
                    name='Arousal',
                    hovertemplate='<b>Time:</b> %{x:.1f}s<br><b>Arousal:</b> %{y:.2f}<extra></extra>'
                ),
                row=3, col=1
            )
            
            # Valence timeline
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=valences,
                    mode='lines+markers',
                    marker=dict(color='green', size=6),
                    name='Valence',
                    hovertemplate='<b>Time:</b> %{x:.1f}s<br><b>Valence:</b> %{y:.2f}<extra></extra>'
                ),
                row=4, col=1
            )
            
            # Update layout
            fig.update_layout(
                title='Emotional Timeline Analysis',
                height=800,
                showlegend=False
            )
            
            # Update axes
            fig.update_xaxes(title_text="Time (seconds)")
            fig.update_yaxes(title_text="Emotion", row=1, col=1)
            fig.update_yaxes(title_text="Confidence", range=[0, 1], row=2, col=1)
            fig.update_yaxes(title_text="Arousal", range=[0, 1], row=3, col=1)
            fig.update_yaxes(title_text="Valence", range=[0, 1], row=4, col=1)
            
            # Save plot
            fig.write_html(output_path)
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating emotion timeline: {e}")
            return ""
    
    def create_sentiment_heatmap(self, sentiment_results: List[SentimentResult], 
                               output_path: str = "sentiment_heatmap.html") -> str:
        """Create sentiment heatmap visualization"""
        try:
            if not sentiment_results:
                return ""
            
            # Prepare data for heatmap
            timestamps = [r.timestamp for r in sentiment_results]
            polarities = [r.polarity for r in sentiment_results]
            subjectivities = [r.subjectivity for r in sentiment_results]
            
            # Create 2D heatmap data
            time_bins = np.linspace(min(timestamps), max(timestamps), 50)
            polarity_bins = np.linspace(-1, 1, 20)
            
            heatmap_data = np.zeros((len(polarity_bins), len(time_bins)))
            
            for timestamp, polarity in zip(timestamps, polarities):
                time_idx = np.digitize(timestamp, time_bins) - 1
                polarity_idx = np.digitize(polarity, polarity_bins) - 1
                
                if 0 <= time_idx < len(time_bins) and 0 <= polarity_idx < len(polarity_bins):
                    heatmap_data[polarity_idx, time_idx] += 1
            
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=heatmap_data,
                x=time_bins,
                y=polarity_bins,
                colorscale='RdYlBu_r',
                hovertemplate='<b>Time:</b> %{x:.1f}s<br><b>Polarity:</b> %{y:.2f}<br><b>Intensity:</b> %{z}<extra></extra>'
            ))
            
            fig.update_layout(
                title='Sentiment Heatmap Over Time',
                xaxis_title='Time (seconds)',
                yaxis_title='Sentiment Polarity',
                height=500
            )
            
            # Save plot
            fig.write_html(output_path)
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating sentiment heatmap: {e}")
            return ""
    
    def create_mood_dashboard(self, mood_states: List[MoodState], 
                            output_path: str = "mood_dashboard.html") -> str:
        """Create comprehensive mood tracking dashboard"""
        try:
            if not mood_states:
                return ""
            
            timestamps = [m.timestamp for m in mood_states]
            energy_levels = [m.energy_level for m in mood_states]
            stress_levels = [m.stress_level for m in mood_states]
            fatigue_levels = [m.fatigue_level for m in mood_states]
            engagement_levels = [m.engagement_level for m in mood_states]
            stability_levels = [m.emotional_stability for m in mood_states]
            
            # Create subplots
            fig = make_subplots(
                rows=3, cols=2,
                subplot_titles=['Energy Level', 'Stress Level', 'Fatigue Level', 
                              'Engagement Level', 'Emotional Stability', 'Overall Mood'],
                vertical_spacing=0.1,
                horizontal_spacing=0.1
            )
            
            # Energy level
            fig.add_trace(
                go.Scatter(x=timestamps, y=energy_levels, mode='lines+markers', 
                          name='Energy', line=dict(color='orange')),
                row=1, col=1
            )
            
            # Stress level
            fig.add_trace(
                go.Scatter(x=timestamps, y=stress_levels, mode='lines+markers', 
                          name='Stress', line=dict(color='red')),
                row=1, col=2
            )
            
            # Fatigue level
            fig.add_trace(
                go.Scatter(x=timestamps, y=fatigue_levels, mode='lines+markers', 
                          name='Fatigue', line=dict(color='purple')),
                row=2, col=1
            )
            
            # Engagement level
            fig.add_trace(
                go.Scatter(x=timestamps, y=engagement_levels, mode='lines+markers', 
                          name='Engagement', line=dict(color='green')),
                row=2, col=2
            )
            
            # Emotional stability
            fig.add_trace(
                go.Scatter(x=timestamps, y=stability_levels, mode='lines+markers', 
                          name='Stability', line=dict(color='blue')),
                row=3, col=1
            )
            
            # Overall mood radar chart
            moods = [m.mood for m in mood_states]
            mood_counts = pd.Series(moods).value_counts()
            
            fig.add_trace(
                go.Bar(x=list(mood_counts.index), y=list(mood_counts.values), 
                      name='Mood Distribution', marker_color='lightblue'),
                row=3, col=2
            )
            
            # Update layout
            fig.update_layout(
                title='Comprehensive Mood Analysis Dashboard',
                height=900,
                showlegend=False
            )
            
            # Update all y-axes to 0-1 range except mood distribution
            for row in range(1, 4):
                for col in range(1, 3):
                    if not (row == 3 and col == 2):  # Skip mood distribution
                        fig.update_yaxes(range=[0, 1], row=row, col=col)
            
            # Save plot
            fig.write_html(output_path)
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating mood dashboard: {e}")
            return ""
    
    def create_stress_fatigue_analysis(self, stress_fatigue_results: List[StressFatigueResult], 
                                     output_path: str = "stress_fatigue_analysis.html") -> str:
        """Create stress and fatigue analysis visualization"""
        try:
            if not stress_fatigue_results:
                return ""
            
            timestamps = [r.timestamp for r in stress_fatigue_results]
            stress_levels = [r.stress_level for r in stress_fatigue_results]
            fatigue_levels = [r.fatigue_level for r in stress_fatigue_results]
            cognitive_loads = [r.cognitive_load for r in stress_fatigue_results]
            vocal_strains = [r.vocal_strain for r in stress_fatigue_results]
            
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=['Stress & Fatigue Levels', 'Cognitive Load', 
                              'Vocal Strain', 'Speaking Patterns'],
                vertical_spacing=0.15
            )
            
            # Stress and fatigue
            fig.add_trace(
                go.Scatter(x=timestamps, y=stress_levels, mode='lines+markers', 
                          name='Stress', line=dict(color='red')),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=timestamps, y=fatigue_levels, mode='lines+markers', 
                          name='Fatigue', line=dict(color='purple')),
                row=1, col=1
            )
            
            # Cognitive load
            fig.add_trace(
                go.Scatter(x=timestamps, y=cognitive_loads, mode='lines+markers', 
                          name='Cognitive Load', line=dict(color='orange')),
                row=1, col=2
            )
            
            # Vocal strain
            fig.add_trace(
                go.Scatter(x=timestamps, y=vocal_strains, mode='lines+markers', 
                          name='Vocal Strain', line=dict(color='brown')),
                row=2, col=1
            )
            
            # Speaking patterns
            speaking_rates = [r.speaking_rate_deviation for r in stress_fatigue_results]
            pause_frequencies = [r.pause_frequency for r in stress_fatigue_results]
            
            fig.add_trace(
                go.Scatter(x=timestamps, y=speaking_rates, mode='lines+markers', 
                          name='Rate Deviation', line=dict(color='green')),
                row=2, col=2
            )
            fig.add_trace(
                go.Scatter(x=timestamps, y=pause_frequencies, mode='lines+markers', 
                          name='Pause Frequency', line=dict(color='blue')),
                row=2, col=2
            )
            
            # Update layout
            fig.update_layout(
                title='Stress and Fatigue Analysis',
                height=700,
                showlegend=True
            )
            
            # Update y-axes
            fig.update_yaxes(range=[0, 1], row=1, col=1)
            fig.update_yaxes(range=[0, 1], row=1, col=2)
            fig.update_yaxes(range=[0, 1], row=2, col=1)
            
            # Save plot
            fig.write_html(output_path)
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating stress fatigue analysis: {e}")
            return ""

class EmotionSentimentSystem:
    """Main system for comprehensive emotion and sentiment detection"""
    
    def __init__(self):
        self.emotion_detector = EmotionDetector()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.mood_tracker = MoodTracker()
        self.stress_fatigue_detector = StressFatigueDetector()
        self.visualizer = EmotionalTimelineVisualizer()
    
    def analyze_complete(self, audio_path: str, transcript: str = "") -> Dict[str, Any]:
        """Perform complete emotion and sentiment analysis"""
        try:
            logger.info(f"Starting comprehensive emotion analysis for: {audio_path}")
            
            results = {
                'audio_path': audio_path,
                'transcript': transcript,
                'analysis_timestamp': datetime.now().isoformat(),
                'emotions': [],
                'sentiments': [],
                'mood_states': [],
                'stress_fatigue': [],
                'visualizations': {},
                'summary': {}
            }
            
            # Emotion detection
            logger.info("Detecting emotions...")
            emotion_results = self.emotion_detector.detect_emotion(audio_path)
            results['emotions'] = [asdict(r) for r in emotion_results]
            
            # Sentiment analysis (if transcript provided)
            if transcript:
                logger.info("Analyzing sentiment...")
                sentiment_results = self.sentiment_analyzer.analyze_sentiment(audio_path, transcript)
                results['sentiments'] = [asdict(r) for r in sentiment_results]
                
                # Mood tracking
                logger.info("Tracking mood...")
                mood_states = self.mood_tracker.track_mood(audio_path, transcript)
                results['mood_states'] = [asdict(m) for m in mood_states]
            
            # Stress and fatigue detection
            logger.info("Detecting stress and fatigue...")
            stress_fatigue_results = self.stress_fatigue_detector.detect_stress_fatigue(audio_path)
            results['stress_fatigue'] = [asdict(r) for r in stress_fatigue_results]
            
            # Generate visualizations
            logger.info("Creating visualizations...")
            if emotion_results:
                emotion_timeline = self.visualizer.create_emotion_timeline(emotion_results)
                results['visualizations']['emotion_timeline'] = emotion_timeline
            
            if transcript and sentiment_results:
                sentiment_heatmap = self.visualizer.create_sentiment_heatmap(sentiment_results)
                results['visualizations']['sentiment_heatmap'] = sentiment_heatmap
                
                if mood_states:
                    mood_dashboard = self.visualizer.create_mood_dashboard(mood_states)
                    results['visualizations']['mood_dashboard'] = mood_dashboard
            
            if stress_fatigue_results:
                stress_analysis = self.visualizer.create_stress_fatigue_analysis(stress_fatigue_results)
                results['visualizations']['stress_fatigue_analysis'] = stress_analysis
            
            # Generate summary
            results['summary'] = self._generate_summary(
                emotion_results, sentiment_results if transcript else [], 
                mood_states if transcript else [], stress_fatigue_results
            )
            
            logger.info("Emotion and sentiment analysis completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Error in complete analysis: {e}")
            return {'error': str(e)}
    
    def _generate_summary(self, emotion_results: List[EmotionResult], 
                         sentiment_results: List[SentimentResult],
                         mood_states: List[MoodState], 
                         stress_fatigue_results: List[StressFatigueResult]) -> Dict[str, Any]:
        """Generate analysis summary"""
        try:
            summary = {
                'duration_analyzed': 0,
                'dominant_emotion': 'neutral',
                'average_sentiment': 0.0,
                'emotional_stability': 0.5,
                'stress_indicators': {},
                'key_insights': []
            }
            
            if emotion_results:
                # Calculate duration
                summary['duration_analyzed'] = max(r.timestamp + r.duration for r in emotion_results)
                
                # Find dominant emotion
                emotion_counts = {}
                for result in emotion_results:
                    emotion = result.primary_emotion
                    emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                
                summary['dominant_emotion'] = max(emotion_counts, key=emotion_counts.get)
                
                # Calculate emotional stability
                confidences = [r.confidence for r in emotion_results]
                summary['emotional_stability'] = np.mean(confidences)
            
            if sentiment_results:
                # Calculate average sentiment
                polarities = [r.polarity for r in sentiment_results]
                summary['average_sentiment'] = np.mean(polarities)
            
            if stress_fatigue_results:
                # Stress indicators
                avg_stress = np.mean([r.stress_level for r in stress_fatigue_results])
                avg_fatigue = np.mean([r.fatigue_level for r in stress_fatigue_results])
                avg_cognitive_load = np.mean([r.cognitive_load for r in stress_fatigue_results])
                
                summary['stress_indicators'] = {
                    'average_stress_level': avg_stress,
                    'average_fatigue_level': avg_fatigue,
                    'average_cognitive_load': avg_cognitive_load,
                    'high_stress_periods': sum(1 for r in stress_fatigue_results if r.stress_level > 0.7),
                    'high_fatigue_periods': sum(1 for r in stress_fatigue_results if r.fatigue_level > 0.7)
                }
            
            # Generate key insights
            insights = []
            
            if summary['emotional_stability'] > 0.8:
                insights.append("High emotional stability detected throughout the recording")
            elif summary['emotional_stability'] < 0.4:
                insights.append("Low emotional stability - significant emotional fluctuations detected")
            
            if summary['average_sentiment'] > 0.3:
                insights.append("Overall positive sentiment detected")
            elif summary['average_sentiment'] < -0.3:
                insights.append("Overall negative sentiment detected")
            
            if 'stress_indicators' in summary:
                if summary['stress_indicators']['average_stress_level'] > 0.6:
                    insights.append("Elevated stress levels detected")
                if summary['stress_indicators']['average_fatigue_level'] > 0.6:
                    insights.append("Signs of fatigue detected")
                if summary['stress_indicators']['high_stress_periods'] > 0:
                    insights.append(f"{summary['stress_indicators']['high_stress_periods']} high-stress periods identified")
            
            summary['key_insights'] = insights
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {'error': str(e)}
    
    def save_results(self, results: Dict[str, Any], output_path: str = "emotion_analysis_results.json"):
        """Save analysis results to file"""
        try:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Results saved to: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return ""

# Example usage and testing
if __name__ == "__main__":
    # Initialize the system
    emotion_system = EmotionSentimentSystem()
    
    # Example analysis (would need actual audio file)
    # results = emotion_system.analyze_complete("sample_audio.wav", "This is a sample transcript")
    # emotion_system.save_results(results)
    
    print("Emotion and Sentiment Detection System initialized successfully!")
    print("Available features:")
    print("- Voice-based emotion detection")
    print("- Multi-modal sentiment analysis")
    print("- Continuous mood tracking")
    print("- Stress and fatigue detection")
    print("- Interactive timeline visualizations")