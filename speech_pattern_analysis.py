"""
Speech Pattern Analysis System

This module provides comprehensive speech pattern analysis including:
- Speech rate analysis and speaking pattern detection
- Pause detection and silence analysis
- Filler word detection and removal
- Speaking confidence and hesitation analysis
- Speech coaching suggestions based on patterns

Requirements: 3.1, 5.1
Tools: Praat, OpenSMILE, Custom Audio Processing
"""

import numpy as np
import librosa
import scipy.signal
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import re
import json
import logging
from pathlib import Path
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings("ignore")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SpeechSegment:
    """Represents a segment of speech with timing and content"""
    start_time: float
    end_time: float
    text: str
    speaker_id: Optional[str] = None
    confidence: float = 1.0
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

@dataclass
class PauseAnalysis:
    """Analysis of pauses in speech"""
    total_pause_time: float
    pause_count: int
    average_pause_duration: float
    longest_pause: float
    pause_locations: List[Tuple[float, float]]  # (start, end) times
    pause_frequency: float  # pauses per minute
    
@dataclass
class SpeechRateAnalysis:
    """Analysis of speech rate and tempo"""
    words_per_minute: float
    syllables_per_minute: float
    characters_per_minute: float
    speaking_time: float
    total_time: float
    speech_rate_variability: float
    tempo_changes: List[Tuple[float, float]]  # (time, rate) pairs

@dataclass
class FillerWordAnalysis:
    """Analysis of filler words and hesitations"""
    filler_words: Dict[str, int]
    total_filler_count: int
    filler_percentage: float
    hesitation_markers: List[Tuple[float, str]]  # (time, filler)
    repetitions: List[Tuple[float, str]]  # (time, repeated_phrase)
    false_starts: List[Tuple[float, str]]  # (time, false_start)

@dataclass
class ConfidenceAnalysis:
    """Analysis of speaking confidence and hesitation patterns"""
    overall_confidence_score: float
    hesitation_frequency: float
    voice_stability: float
    pace_consistency: float
    volume_consistency: float
    confidence_timeline: List[Tuple[float, float]]  # (time, confidence)

@dataclass
class SpeechCoachingSuggestions:
    """Coaching suggestions based on speech pattern analysis"""
    pace_suggestions: List[str]
    pause_suggestions: List[str]
    filler_reduction_tips: List[str]
    confidence_building_tips: List[str]
    overall_rating: str
    priority_areas: List[str]

@dataclass
class ComprehensiveSpeechAnalysis:
    """Complete speech pattern analysis results"""
    speech_rate: SpeechRateAnalysis
    pause_analysis: PauseAnalysis
    filler_analysis: FillerWordAnalysis
    confidence_analysis: ConfidenceAnalysis
    coaching_suggestions: SpeechCoachingSuggestions
    analysis_timestamp: datetime
    audio_duration: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis to dictionary format"""
        return asdict(self)

class AudioFeatureExtractor:
    """Extract acoustic features from audio for speech analysis"""
    
    def __init__(self):
        self.sample_rate = 16000
        
    def extract_features(self, audio_path: str) -> Dict[str, np.ndarray]:
        """Extract comprehensive audio features"""
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            features = {}
            
            # Basic features
            features['audio'] = y
            features['sample_rate'] = sr
            features['duration'] = len(y) / sr
            
            # Spectral features
            features['mfcc'] = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            features['spectral_centroid'] = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            features['spectral_rolloff'] = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            features['zero_crossing_rate'] = librosa.feature.zero_crossing_rate(y)[0]
            
            # Energy and volume features
            features['rms_energy'] = librosa.feature.rms(y=y)[0]
            features['volume_envelope'] = np.abs(y)
            
            # Pitch features
            features['pitch'] = librosa.yin(y, fmin=50, fmax=400)
            
            # Tempo and rhythm
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            features['tempo'] = tempo
            features['beats'] = beats
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting audio features: {e}")
            return {}

class SpeechRateAnalyzer:
    """Analyze speech rate and tempo patterns"""
    
    def __init__(self):
        self.syllable_patterns = [
            r'[aeiouAEIOU]+',  # Simple vowel-based syllable counting
        ]
    
    def count_syllables(self, text: str) -> int:
        """Estimate syllable count in text"""
        # Simple syllable counting based on vowel groups
        text = re.sub(r'[^a-zA-Z\s]', '', text.lower())
        syllables = 0
        
        for word in text.split():
            word_syllables = len(re.findall(r'[aeiou]+', word))
            if word_syllables == 0 and len(word) > 0:
                word_syllables = 1  # Every word has at least one syllable
            syllables += word_syllables
            
        return max(1, syllables)
    
    def analyze_speech_rate(self, segments: List[SpeechSegment], 
                          audio_features: Dict[str, np.ndarray]) -> SpeechRateAnalysis:
        """Analyze speech rate patterns"""
        try:
            # Calculate basic metrics
            total_words = sum(len(seg.text.split()) for seg in segments)
            total_characters = sum(len(seg.text) for seg in segments)
            total_syllables = sum(self.count_syllables(seg.text) for seg in segments)
            
            speaking_time = sum(seg.duration for seg in segments)
            total_time = audio_features.get('duration', speaking_time)
            
            # Calculate rates
            words_per_minute = (total_words / speaking_time) * 60 if speaking_time > 0 else 0
            syllables_per_minute = (total_syllables / speaking_time) * 60 if speaking_time > 0 else 0
            characters_per_minute = (total_characters / speaking_time) * 60 if speaking_time > 0 else 0
            
            # Calculate rate variability
            segment_rates = []
            for seg in segments:
                if seg.duration > 0:
                    seg_words = len(seg.text.split())
                    seg_rate = (seg_words / seg.duration) * 60
                    segment_rates.append(seg_rate)
            
            rate_variability = np.std(segment_rates) if segment_rates else 0
            
            # Detect tempo changes
            tempo_changes = self._detect_tempo_changes(segments)
            
            return SpeechRateAnalysis(
                words_per_minute=words_per_minute,
                syllables_per_minute=syllables_per_minute,
                characters_per_minute=characters_per_minute,
                speaking_time=speaking_time,
                total_time=total_time,
                speech_rate_variability=rate_variability,
                tempo_changes=tempo_changes
            )
            
        except Exception as e:
            logger.error(f"Error analyzing speech rate: {e}")
            return SpeechRateAnalysis(0, 0, 0, 0, 0, 0, [])
    
    def _detect_tempo_changes(self, segments: List[SpeechSegment]) -> List[Tuple[float, float]]:
        """Detect significant tempo changes in speech"""
        tempo_changes = []
        
        if len(segments) < 2:
            return tempo_changes
        
        # Calculate rate for each segment
        rates = []
        times = []
        
        for seg in segments:
            if seg.duration > 0:
                words = len(seg.text.split())
                rate = (words / seg.duration) * 60
                rates.append(rate)
                times.append(seg.start_time)
        
        if len(rates) < 2:
            return tempo_changes
        
        # Find significant changes (>20% change)
        for i in range(1, len(rates)):
            if rates[i-1] > 0:
                change_percent = abs(rates[i] - rates[i-1]) / rates[i-1]
                if change_percent > 0.2:  # 20% change threshold
                    tempo_changes.append((times[i], rates[i]))
        
        return tempo_changes

class PauseDetector:
    """Detect and analyze pauses in speech"""
    
    def __init__(self, min_pause_duration: float = 0.3):
        self.min_pause_duration = min_pause_duration
        self.silence_threshold = 0.01  # RMS threshold for silence
    
    def detect_pauses(self, audio_features: Dict[str, np.ndarray], 
                     segments: List[SpeechSegment]) -> PauseAnalysis:
        """Detect and analyze pauses in audio"""
        try:
            audio = audio_features.get('audio', np.array([]))
            sample_rate = audio_features.get('sample_rate', 16000)
            rms_energy = audio_features.get('rms_energy', np.array([]))
            
            if len(audio) == 0 or len(rms_energy) == 0:
                return PauseAnalysis(0, 0, 0, 0, [], 0)
            
            # Detect silence regions based on RMS energy
            silence_mask = rms_energy < self.silence_threshold
            
            # Convert to time-based silence detection
            hop_length = 512  # Default librosa hop length
            time_per_frame = hop_length / sample_rate
            
            pause_locations = []
            current_pause_start = None
            
            for i, is_silent in enumerate(silence_mask):
                time = i * time_per_frame
                
                if is_silent and current_pause_start is None:
                    current_pause_start = time
                elif not is_silent and current_pause_start is not None:
                    pause_duration = time - current_pause_start
                    if pause_duration >= self.min_pause_duration:
                        pause_locations.append((current_pause_start, time))
                    current_pause_start = None
            
            # Handle pause at end of audio
            if current_pause_start is not None:
                total_duration = len(audio) / sample_rate
                pause_duration = total_duration - current_pause_start
                if pause_duration >= self.min_pause_duration:
                    pause_locations.append((current_pause_start, total_duration))
            
            # Calculate pause statistics
            total_pause_time = sum(end - start for start, end in pause_locations)
            pause_count = len(pause_locations)
            average_pause_duration = total_pause_time / pause_count if pause_count > 0 else 0
            longest_pause = max((end - start for start, end in pause_locations), default=0)
            
            # Calculate pause frequency (pauses per minute)
            total_duration = audio_features.get('duration', 0)
            pause_frequency = (pause_count / total_duration) * 60 if total_duration > 0 else 0
            
            return PauseAnalysis(
                total_pause_time=total_pause_time,
                pause_count=pause_count,
                average_pause_duration=average_pause_duration,
                longest_pause=longest_pause,
                pause_locations=pause_locations,
                pause_frequency=pause_frequency
            )
            
        except Exception as e:
            logger.error(f"Error detecting pauses: {e}")
            return PauseAnalysis(0, 0, 0, 0, [], 0)

class FillerWordDetector:
    """Detect and analyze filler words and hesitations"""
    
    def __init__(self):
        self.filler_words = {
            'um', 'uh', 'er', 'ah', 'like', 'you know', 'so', 'well',
            'actually', 'basically', 'literally', 'right', 'okay', 'ok',
            'hmm', 'uhm', 'erm', 'sort of', 'kind of', 'i mean'
        }
        
        self.hesitation_patterns = [
            r'\b(um+|uh+|er+|ah+)\b',
            r'\b(like)\b(?=\s+\w)',
            r'\b(you know)\b',
            r'\b(i mean)\b',
            r'\b(sort of|kind of)\b'
        ]
        
        self.repetition_pattern = r'\b(\w+)\s+\1\b'  # Word repetition
        self.false_start_pattern = r'\b\w+\s*-\s*\w+'  # False starts with dashes
    
    def detect_filler_words(self, segments: List[SpeechSegment]) -> FillerWordAnalysis:
        """Detect and analyze filler words in speech"""
        try:
            filler_words = {}
            hesitation_markers = []
            repetitions = []
            false_starts = []
            total_words = 0
            
            for seg in segments:
                text = seg.text.lower()
                words = text.split()
                total_words += len(words)
                
                # Count filler words
                for word in words:
                    clean_word = word.strip('.,!?;:').lower()
                    if clean_word in self.filler_words:
                        filler_words[clean_word] = filler_words.get(clean_word, 0) + 1
                        # Estimate time within segment
                        word_time = seg.start_time + (seg.duration * 0.5)
                        hesitation_markers.append((word_time, clean_word))
                
                # Detect hesitation patterns
                for pattern in self.hesitation_patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        word_time = seg.start_time + (seg.duration * match.start() / len(text))
                        hesitation_markers.append((word_time, match.group()))
                
                # Detect repetitions
                rep_matches = re.finditer(self.repetition_pattern, text, re.IGNORECASE)
                for match in rep_matches:
                    word_time = seg.start_time + (seg.duration * match.start() / len(text))
                    repetitions.append((word_time, match.group()))
                
                # Detect false starts
                fs_matches = re.finditer(self.false_start_pattern, text, re.IGNORECASE)
                for match in fs_matches:
                    word_time = seg.start_time + (seg.duration * match.start() / len(text))
                    false_starts.append((word_time, match.group()))
            
            total_filler_count = sum(filler_words.values())
            filler_percentage = (total_filler_count / total_words) * 100 if total_words > 0 else 0
            
            return FillerWordAnalysis(
                filler_words=filler_words,
                total_filler_count=total_filler_count,
                filler_percentage=filler_percentage,
                hesitation_markers=hesitation_markers,
                repetitions=repetitions,
                false_starts=false_starts
            )
            
        except Exception as e:
            logger.error(f"Error detecting filler words: {e}")
            return FillerWordAnalysis({}, 0, 0, [], [], [])

class ConfidenceAnalyzer:
    """Analyze speaking confidence and hesitation patterns"""
    
    def __init__(self):
        self.confidence_factors = {
            'pace_consistency': 0.25,
            'volume_stability': 0.25,
            'filler_frequency': 0.25,
            'pause_patterns': 0.25
        }
    
    def analyze_confidence(self, segments: List[SpeechSegment],
                          audio_features: Dict[str, np.ndarray],
                          filler_analysis: FillerWordAnalysis,
                          pause_analysis: PauseAnalysis) -> ConfidenceAnalysis:
        """Analyze speaking confidence patterns"""
        try:
            # Calculate pace consistency
            pace_consistency = self._calculate_pace_consistency(segments)
            
            # Calculate volume consistency
            volume_consistency = self._calculate_volume_consistency(audio_features)
            
            # Calculate voice stability (pitch variation)
            voice_stability = self._calculate_voice_stability(audio_features)
            
            # Calculate hesitation frequency
            total_duration = sum(seg.duration for seg in segments)
            hesitation_frequency = len(filler_analysis.hesitation_markers) / total_duration if total_duration > 0 else 0
            
            # Calculate overall confidence score
            confidence_factors = {
                'pace_consistency': min(pace_consistency, 1.0),
                'volume_consistency': min(volume_consistency, 1.0),
                'voice_stability': min(voice_stability, 1.0),
                'low_hesitation': max(0, 1.0 - (hesitation_frequency * 10))  # Penalize high hesitation
            }
            
            overall_confidence = sum(
                score * self.confidence_factors.get(factor, 0.25)
                for factor, score in confidence_factors.items()
            )
            
            # Generate confidence timeline
            confidence_timeline = self._generate_confidence_timeline(segments, audio_features)
            
            return ConfidenceAnalysis(
                overall_confidence_score=overall_confidence,
                hesitation_frequency=hesitation_frequency,
                voice_stability=voice_stability,
                pace_consistency=pace_consistency,
                volume_consistency=volume_consistency,
                confidence_timeline=confidence_timeline
            )
            
        except Exception as e:
            logger.error(f"Error analyzing confidence: {e}")
            return ConfidenceAnalysis(0.5, 0, 0.5, 0.5, 0.5, [])
    
    def _calculate_pace_consistency(self, segments: List[SpeechSegment]) -> float:
        """Calculate consistency of speaking pace"""
        if len(segments) < 2:
            return 1.0
        
        rates = []
        for seg in segments:
            if seg.duration > 0:
                words = len(seg.text.split())
                rate = words / seg.duration
                rates.append(rate)
        
        if len(rates) < 2:
            return 1.0
        
        # Lower coefficient of variation = higher consistency
        mean_rate = np.mean(rates)
        std_rate = np.std(rates)
        cv = std_rate / mean_rate if mean_rate > 0 else 1.0
        
        # Convert to 0-1 scale (lower CV = higher score)
        consistency = max(0, 1.0 - cv)
        return consistency
    
    def _calculate_volume_consistency(self, audio_features: Dict[str, np.ndarray]) -> float:
        """Calculate consistency of volume/energy"""
        rms_energy = audio_features.get('rms_energy', np.array([]))
        
        if len(rms_energy) == 0:
            return 0.5
        
        # Remove silence periods
        non_silent = rms_energy[rms_energy > 0.01]
        
        if len(non_silent) < 2:
            return 0.5
        
        # Calculate coefficient of variation
        mean_energy = np.mean(non_silent)
        std_energy = np.std(non_silent)
        cv = std_energy / mean_energy if mean_energy > 0 else 1.0
        
        # Convert to 0-1 scale
        consistency = max(0, 1.0 - cv)
        return consistency
    
    def _calculate_voice_stability(self, audio_features: Dict[str, np.ndarray]) -> float:
        """Calculate voice pitch stability"""
        pitch = audio_features.get('pitch', np.array([]))
        
        if len(pitch) == 0:
            return 0.5
        
        # Remove unvoiced frames (pitch = 0)
        voiced_pitch = pitch[pitch > 0]
        
        if len(voiced_pitch) < 2:
            return 0.5
        
        # Calculate pitch stability (lower variation = higher stability)
        mean_pitch = np.mean(voiced_pitch)
        std_pitch = np.std(voiced_pitch)
        cv = std_pitch / mean_pitch if mean_pitch > 0 else 1.0
        
        # Convert to 0-1 scale
        stability = max(0, 1.0 - (cv * 0.5))  # Scale factor for pitch variation
        return stability
    
    def _generate_confidence_timeline(self, segments: List[SpeechSegment],
                                    audio_features: Dict[str, np.ndarray]) -> List[Tuple[float, float]]:
        """Generate confidence score timeline"""
        timeline = []
        
        for seg in segments:
            # Simple confidence estimation based on segment characteristics
            words = len(seg.text.split())
            duration = seg.duration
            
            if duration > 0:
                rate = words / duration
                # Normalize rate (assuming 2-3 words/second is optimal)
                rate_score = 1.0 - abs(rate - 2.5) / 2.5
                rate_score = max(0, min(1, rate_score))
                
                # Use segment confidence if available, otherwise use rate-based estimate
                confidence = getattr(seg, 'confidence', rate_score)
                timeline.append((seg.start_time, confidence))
        
        return timeline

class SpeechCoach:
    """Generate coaching suggestions based on speech analysis"""
    
    def __init__(self):
        self.optimal_wpm = (140, 180)  # Optimal words per minute range
        self.optimal_pause_frequency = (8, 15)  # Pauses per minute
        self.max_filler_percentage = 5.0  # Maximum acceptable filler percentage
    
    def generate_suggestions(self, analysis: ComprehensiveSpeechAnalysis) -> SpeechCoachingSuggestions:
        """Generate comprehensive coaching suggestions"""
        try:
            pace_suggestions = self._generate_pace_suggestions(analysis.speech_rate)
            pause_suggestions = self._generate_pause_suggestions(analysis.pause_analysis)
            filler_tips = self._generate_filler_reduction_tips(analysis.filler_analysis)
            confidence_tips = self._generate_confidence_tips(analysis.confidence_analysis)
            
            # Determine overall rating
            overall_rating = self._calculate_overall_rating(analysis)
            
            # Identify priority areas for improvement
            priority_areas = self._identify_priority_areas(analysis)
            
            return SpeechCoachingSuggestions(
                pace_suggestions=pace_suggestions,
                pause_suggestions=pause_suggestions,
                filler_reduction_tips=filler_tips,
                confidence_building_tips=confidence_tips,
                overall_rating=overall_rating,
                priority_areas=priority_areas
            )
            
        except Exception as e:
            logger.error(f"Error generating coaching suggestions: {e}")
            return SpeechCoachingSuggestions([], [], [], [], "Unknown", [])
    
    def _generate_pace_suggestions(self, speech_rate: SpeechRateAnalysis) -> List[str]:
        """Generate pace-related suggestions"""
        suggestions = []
        wpm = speech_rate.words_per_minute
        
        if wpm < self.optimal_wpm[0]:
            suggestions.append(f"Your speaking pace is {wpm:.0f} WPM, which is slower than optimal. Try to speak a bit faster to maintain audience engagement.")
            suggestions.append("Practice reading aloud to increase your natural speaking pace.")
        elif wpm > self.optimal_wpm[1]:
            suggestions.append(f"Your speaking pace is {wpm:.0f} WPM, which is faster than optimal. Try to slow down for better clarity.")
            suggestions.append("Take deliberate pauses between sentences to give your audience time to process.")
        else:
            suggestions.append(f"Your speaking pace of {wpm:.0f} WPM is in the optimal range. Great job!")
        
        if speech_rate.speech_rate_variability > 50:
            suggestions.append("Your speaking pace varies significantly. Try to maintain more consistent pacing throughout your speech.")
        
        if len(speech_rate.tempo_changes) > 5:
            suggestions.append("You have frequent tempo changes. While some variation is good, try to maintain steadier pacing.")
        
        return suggestions
    
    def _generate_pause_suggestions(self, pause_analysis: PauseAnalysis) -> List[str]:
        """Generate pause-related suggestions"""
        suggestions = []
        
        if pause_analysis.pause_frequency < self.optimal_pause_frequency[0]:
            suggestions.append("You're not pausing enough. Strategic pauses help emphasize key points and give your audience time to absorb information.")
            suggestions.append("Try adding pauses after important statements and between major topics.")
        elif pause_analysis.pause_frequency > self.optimal_pause_frequency[1]:
            suggestions.append("You're pausing quite frequently. While pauses are important, too many can disrupt the flow of your speech.")
        else:
            suggestions.append("Your pause frequency is well-balanced. Good use of strategic pauses!")
        
        if pause_analysis.longest_pause > 3.0:
            suggestions.append(f"Your longest pause was {pause_analysis.longest_pause:.1f} seconds. Very long pauses can lose audience attention.")
        
        if pause_analysis.average_pause_duration > 1.5:
            suggestions.append("Your average pause duration is quite long. Try to keep most pauses under 1.5 seconds.")
        
        return suggestions
    
    def _generate_filler_reduction_tips(self, filler_analysis: FillerWordAnalysis) -> List[str]:
        """Generate filler word reduction tips"""
        tips = []
        
        if filler_analysis.filler_percentage > self.max_filler_percentage:
            tips.append(f"You used filler words {filler_analysis.filler_percentage:.1f}% of the time. Try to reduce this to under 5%.")
            tips.append("Practice replacing filler words with brief pauses instead.")
            
            # Specific filler word advice
            most_common = max(filler_analysis.filler_words.items(), key=lambda x: x[1], default=('', 0))
            if most_common[1] > 0:
                tips.append(f"Your most common filler word is '{most_common[0]}' ({most_common[1]} times). Be especially mindful of this word.")
        else:
            tips.append("Your filler word usage is within acceptable limits. Well done!")
        
        if len(filler_analysis.repetitions) > 3:
            tips.append("You have several word repetitions. Practice your content to reduce unintentional repetitions.")
        
        if len(filler_analysis.false_starts) > 2:
            tips.append("You have some false starts. Take a moment to organize your thoughts before speaking.")
        
        return tips
    
    def _generate_confidence_tips(self, confidence_analysis: ConfidenceAnalysis) -> List[str]:
        """Generate confidence-building tips"""
        tips = []
        
        if confidence_analysis.overall_confidence_score < 0.6:
            tips.append("Your overall speaking confidence could be improved. Practice and preparation are key to building confidence.")
            tips.append("Try recording yourself speaking and listening back to identify areas for improvement.")
        
        if confidence_analysis.voice_stability < 0.6:
            tips.append("Your voice shows some instability. Practice breathing exercises and vocal warm-ups before speaking.")
        
        if confidence_analysis.pace_consistency < 0.6:
            tips.append("Work on maintaining consistent pacing. Practice with a metronome or recorded speech to develop rhythm.")
        
        if confidence_analysis.volume_consistency < 0.6:
            tips.append("Your volume varies significantly. Practice projecting your voice consistently throughout your speech.")
        
        if confidence_analysis.hesitation_frequency > 0.5:
            tips.append("You show frequent hesitation patterns. Thorough preparation and practice can help reduce hesitations.")
        
        return tips
    
    def _calculate_overall_rating(self, analysis: ComprehensiveSpeechAnalysis) -> str:
        """Calculate overall speech performance rating"""
        scores = []
        
        # Pace score
        wpm = analysis.speech_rate.words_per_minute
        if self.optimal_wpm[0] <= wpm <= self.optimal_wpm[1]:
            scores.append(0.9)
        elif abs(wpm - np.mean(self.optimal_wpm)) < 30:
            scores.append(0.7)
        else:
            scores.append(0.5)
        
        # Filler score
        if analysis.filler_analysis.filler_percentage <= self.max_filler_percentage:
            scores.append(0.9)
        elif analysis.filler_analysis.filler_percentage <= 10:
            scores.append(0.7)
        else:
            scores.append(0.5)
        
        # Confidence score
        scores.append(analysis.confidence_analysis.overall_confidence_score)
        
        # Pause score
        pf = analysis.pause_analysis.pause_frequency
        if self.optimal_pause_frequency[0] <= pf <= self.optimal_pause_frequency[1]:
            scores.append(0.9)
        else:
            scores.append(0.6)
        
        overall_score = np.mean(scores)
        
        if overall_score >= 0.85:
            return "Excellent"
        elif overall_score >= 0.75:
            return "Good"
        elif overall_score >= 0.65:
            return "Fair"
        else:
            return "Needs Improvement"
    
    def _identify_priority_areas(self, analysis: ComprehensiveSpeechAnalysis) -> List[str]:
        """Identify priority areas for improvement"""
        priority_areas = []
        
        # Check pace
        wpm = analysis.speech_rate.words_per_minute
        if wpm < self.optimal_wpm[0] or wpm > self.optimal_wpm[1]:
            priority_areas.append("Speaking Pace")
        
        # Check filler words
        if analysis.filler_analysis.filler_percentage > self.max_filler_percentage:
            priority_areas.append("Filler Word Reduction")
        
        # Check confidence
        if analysis.confidence_analysis.overall_confidence_score < 0.6:
            priority_areas.append("Speaking Confidence")
        
        # Check pauses
        pf = analysis.pause_analysis.pause_frequency
        if pf < self.optimal_pause_frequency[0] or pf > self.optimal_pause_frequency[1]:
            priority_areas.append("Pause Management")
        
        return priority_areas

class SpeechPatternAnalysisSystem:
    """Main system for comprehensive speech pattern analysis"""
    
    def __init__(self, db_path: str = "speech_analysis.db"):
        self.db_path = db_path
        self.feature_extractor = AudioFeatureExtractor()
        self.speech_rate_analyzer = SpeechRateAnalyzer()
        self.pause_detector = PauseDetector()
        self.filler_detector = FillerWordDetector()
        self.confidence_analyzer = ConfidenceAnalyzer()
        self.speech_coach = SpeechCoach()
        
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for storing analysis results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS speech_analyses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        audio_path TEXT NOT NULL,
                        analysis_data TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def analyze_speech_patterns(self, audio_path: str, 
                              segments: List[SpeechSegment]) -> ComprehensiveSpeechAnalysis:
        """Perform comprehensive speech pattern analysis"""
        try:
            logger.info(f"Starting speech pattern analysis for: {audio_path}")
            
            # Extract audio features
            audio_features = self.feature_extractor.extract_features(audio_path)
            if not audio_features:
                raise ValueError("Failed to extract audio features")
            
            # Perform individual analyses
            speech_rate = self.speech_rate_analyzer.analyze_speech_rate(segments, audio_features)
            pause_analysis = self.pause_detector.detect_pauses(audio_features, segments)
            filler_analysis = self.filler_detector.detect_filler_words(segments)
            confidence_analysis = self.confidence_analyzer.analyze_confidence(
                segments, audio_features, filler_analysis, pause_analysis
            )
            
            # Create comprehensive analysis
            comprehensive_analysis = ComprehensiveSpeechAnalysis(
                speech_rate=speech_rate,
                pause_analysis=pause_analysis,
                filler_analysis=filler_analysis,
                confidence_analysis=confidence_analysis,
                coaching_suggestions=SpeechCoachingSuggestions([], [], [], [], "Unknown", []),
                analysis_timestamp=datetime.now(),
                audio_duration=audio_features.get('duration', 0)
            )
            
            # Generate coaching suggestions
            comprehensive_analysis.coaching_suggestions = self.speech_coach.generate_suggestions(
                comprehensive_analysis
            )
            
            # Save to database
            self._save_analysis(audio_path, comprehensive_analysis)
            
            logger.info("Speech pattern analysis completed successfully")
            return comprehensive_analysis
            
        except Exception as e:
            logger.error(f"Error in speech pattern analysis: {e}")
            raise
    
    def _save_analysis(self, audio_path: str, analysis: ComprehensiveSpeechAnalysis):
        """Save analysis results to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                analysis_json = json.dumps(analysis.to_dict(), default=str)
                conn.execute(
                    "INSERT INTO speech_analyses (audio_path, analysis_data) VALUES (?, ?)",
                    (audio_path, analysis_json)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error saving analysis to database: {e}")
    
    def get_analysis_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent analysis history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT audio_path, analysis_data, created_at FROM speech_analyses ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                )
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'audio_path': row[0],
                        'analysis_data': json.loads(row[1]),
                        'created_at': row[2]
                    })
                return results
        except Exception as e:
            logger.error(f"Error retrieving analysis history: {e}")
            return []
    
    def analyze_batch(self, audio_files: List[Tuple[str, List[SpeechSegment]]]) -> List[ComprehensiveSpeechAnalysis]:
        """Analyze multiple audio files in batch"""
        results = []
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for audio_path, segments in audio_files:
                future = executor.submit(self.analyze_speech_patterns, audio_path, segments)
                futures.append(future)
            
            for future in futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error in batch analysis: {e}")
                    # Add placeholder result for failed analysis
                    results.append(None)
        
        return results

# Utility functions for integration
def create_sample_segments(text: str, duration: float) -> List[SpeechSegment]:
    """Create sample speech segments for testing"""
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    segments = []
    time_per_sentence = duration / len(sentences) if sentences else duration
    
    for i, sentence in enumerate(sentences):
        start_time = i * time_per_sentence
        end_time = (i + 1) * time_per_sentence
        segments.append(SpeechSegment(
            start_time=start_time,
            end_time=end_time,
            text=sentence,
            confidence=0.9
        ))
    
    return segments

def format_analysis_report(analysis: ComprehensiveSpeechAnalysis) -> str:
    """Format analysis results into a readable report"""
    report = []
    report.append("=== SPEECH PATTERN ANALYSIS REPORT ===\n")
    
    # Speech Rate Analysis
    report.append("SPEECH RATE ANALYSIS:")
    report.append(f"  Words per minute: {analysis.speech_rate.words_per_minute:.1f}")
    report.append(f"  Syllables per minute: {analysis.speech_rate.syllables_per_minute:.1f}")
    report.append(f"  Speaking time: {analysis.speech_rate.speaking_time:.1f}s")
    report.append(f"  Rate variability: {analysis.speech_rate.speech_rate_variability:.2f}")
    report.append("")
    
    # Pause Analysis
    report.append("PAUSE ANALYSIS:")
    report.append(f"  Total pause time: {analysis.pause_analysis.total_pause_time:.1f}s")
    report.append(f"  Number of pauses: {analysis.pause_analysis.pause_count}")
    report.append(f"  Average pause duration: {analysis.pause_analysis.average_pause_duration:.2f}s")
    report.append(f"  Pause frequency: {analysis.pause_analysis.pause_frequency:.1f} per minute")
    report.append("")
    
    # Filler Word Analysis
    report.append("FILLER WORD ANALYSIS:")
    report.append(f"  Total filler words: {analysis.filler_analysis.total_filler_count}")
    report.append(f"  Filler percentage: {analysis.filler_analysis.filler_percentage:.1f}%")
    if analysis.filler_analysis.filler_words:
        report.append("  Most common fillers:")
        for word, count in sorted(analysis.filler_analysis.filler_words.items(), 
                                key=lambda x: x[1], reverse=True)[:5]:
            report.append(f"    {word}: {count}")
    report.append("")
    
    # Confidence Analysis
    report.append("CONFIDENCE ANALYSIS:")
    report.append(f"  Overall confidence: {analysis.confidence_analysis.overall_confidence_score:.2f}")
    report.append(f"  Voice stability: {analysis.confidence_analysis.voice_stability:.2f}")
    report.append(f"  Pace consistency: {analysis.confidence_analysis.pace_consistency:.2f}")
    report.append(f"  Volume consistency: {analysis.confidence_analysis.volume_consistency:.2f}")
    report.append("")
    
    # Coaching Suggestions
    report.append("COACHING SUGGESTIONS:")
    report.append(f"  Overall Rating: {analysis.coaching_suggestions.overall_rating}")
    
    if analysis.coaching_suggestions.priority_areas:
        report.append("  Priority Areas:")
        for area in analysis.coaching_suggestions.priority_areas:
            report.append(f"    - {area}")
    
    if analysis.coaching_suggestions.pace_suggestions:
        report.append("  Pace Suggestions:")
        for suggestion in analysis.coaching_suggestions.pace_suggestions:
            report.append(f"    - {suggestion}")
    
    if analysis.coaching_suggestions.filler_reduction_tips:
        report.append("  Filler Reduction Tips:")
        for tip in analysis.coaching_suggestions.filler_reduction_tips:
            report.append(f"    - {tip}")
    
    return "\n".join(report)

if __name__ == "__main__":
    # Example usage
    system = SpeechPatternAnalysisSystem()
    
    # Create sample data for testing
    sample_text = """
    Hello everyone. Um, today I want to talk about, uh, speech analysis. 
    It's really important to, like, understand how we speak. You know, 
    there are many factors that, er, affect our communication. So, let's dive in.
    """
    
    segments = create_sample_segments(sample_text, 15.0)  # 15 second duration
    
    print("Speech Pattern Analysis System initialized successfully!")
    print(f"Sample segments created: {len(segments)}")
    print("\nSample segment:")
    if segments:
        seg = segments[0]
        print(f"  Time: {seg.start_time:.1f}s - {seg.end_time:.1f}s")
        print(f"  Text: {seg.text}")
        print(f"  Duration: {seg.duration:.1f}s")