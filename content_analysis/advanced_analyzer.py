"""
Advanced AI-Powered Content Analysis
Implements emotion detection, speaking pattern analysis, complexity scoring, and bias detection
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import re
from collections import Counter
import librosa
import textstat
from textblob import TextBlob
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
import spacy

# Download required NLTK data
try:
    nltk.download('vader_lexicon', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
except:
    pass

logger = logging.getLogger(__name__)


@dataclass
class EmotionAnalysis:
    """Results of emotion detection"""
    dominant_emotion: str
    emotion_scores: Dict[str, float]
    emotion_timeline: List[Dict[str, Any]]
    overall_sentiment: str
    sentiment_score: float
    mood_changes: List[Dict[str, Any]]


@dataclass
class SpeakingPatternAnalysis:
    """Results of speaking pattern analysis"""
    speaking_rate: float  # words per minute
    pace_variation: float
    pause_frequency: float
    pause_duration_avg: float
    filler_word_count: int
    filler_word_ratio: float
    emphasis_patterns: List[Dict[str, Any]]
    fluency_score: float


@dataclass
class ComplexityAnalysis:
    """Results of content complexity analysis"""
    readability_score: float
    grade_level: float
    vocabulary_diversity: float
    sentence_complexity: float
    technical_term_ratio: float
    jargon_score: float
    clarity_score: float


@dataclass
class BiasAnalysis:
    """Results of bias detection"""
    bias_detected: bool
    bias_types: List[str]
    bias_instances: List[Dict[str, Any]]
    inclusivity_score: float
    suggestions: List[str]
    gender_balance: Dict[str, float]
    
    
@dataclass
class ContentAnalysisResult:
    """Complete content analysis result"""
    transcript_id: str
    emotion_analysis: EmotionAnalysis
    speaking_patterns: SpeakingPatternAnalysis
    complexity_analysis: ComplexityAnalysis
    bias_analysis: BiasAnalysis
    key_insights: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any]


class AdvancedContentAnalyzer:
    """Advanced AI-powered content analysis engine"""
    
    def __init__(self):
        # Initialize sentiment analyzer
        self.sia = SentimentIntensityAnalyzer()
        
        # Initialize spaCy for advanced NLP
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            logger.warning("spaCy model not found. Some features may be limited.")
            self.nlp = None
        
        # Emotion keywords mapping
        self.emotion_keywords = {
            'joy': ['happy', 'joyful', 'excited', 'pleased', 'delighted', 'cheerful', 'elated'],
            'sadness': ['sad', 'unhappy', 'depressed', 'miserable', 'sorrowful', 'melancholy'],
            'anger': ['angry', 'furious', 'mad', 'irritated', 'annoyed', 'outraged', 'hostile'],
            'fear': ['afraid', 'scared', 'terrified', 'anxious', 'worried', 'fearful', 'nervous'],
            'surprise': ['surprised', 'amazed', 'astonished', 'shocked', 'startled', 'stunned'],
            'disgust': ['disgusted', 'revolted', 'repulsed', 'sickened', 'appalled']
        }
        
        # Filler words
        self.filler_words = {
            'um', 'uh', 'er', 'ah', 'like', 'you know', 'I mean', 'actually', 
            'basically', 'literally', 'right', 'so', 'well', 'okay'
        }
        
        # Bias indicators
        self.bias_indicators = {
            'gender': {
                'male_terms': ['he', 'him', 'his', 'man', 'men', 'boy', 'boys', 'male', 'gentleman'],
                'female_terms': ['she', 'her', 'hers', 'woman', 'women', 'girl', 'girls', 'female', 'lady'],
                'neutral_terms': ['they', 'them', 'their', 'person', 'people', 'individual']
            },
            'age': ['young', 'old', 'elderly', 'millennial', 'boomer', 'kid'],
            'ability': ['disabled', 'handicapped', 'able-bodied', 'normal', 'special needs'],
            'stereotypes': ['aggressive', 'emotional', 'weak', 'strong', 'sensitive']
        }
    
    def analyze_content(self, 
                       transcript_id: str,
                       text: str,
                       audio_path: Optional[str] = None,
                       timestamps: Optional[List[Tuple[float, float, str]]] = None) -> ContentAnalysisResult:
        """
        Perform comprehensive content analysis
        
        Args:
            transcript_id: Unique identifier for the transcript
            text: Full transcript text
            audio_path: Optional path to audio file for audio analysis
            timestamps: Optional list of (start_time, end_time, text) tuples
            
        Returns:
            Complete content analysis results
        """
        try:
            # Perform emotion analysis
            emotion_analysis = self._analyze_emotions(text, timestamps)
            
            # Analyze speaking patterns
            speaking_patterns = self._analyze_speaking_patterns(text, audio_path, timestamps)
            
            # Analyze complexity
            complexity_analysis = self._analyze_complexity(text)
            
            # Detect bias
            bias_analysis = self._analyze_bias(text)
            
            # Generate insights and recommendations
            insights = self._generate_insights(
                emotion_analysis, speaking_patterns, complexity_analysis, bias_analysis
            )
            
            recommendations = self._generate_recommendations(
                emotion_analysis, speaking_patterns, complexity_analysis, bias_analysis
            )
            
            return ContentAnalysisResult(
                transcript_id=transcript_id,
                emotion_analysis=emotion_analysis,
                speaking_patterns=speaking_patterns,
                complexity_analysis=complexity_analysis,
                bias_analysis=bias_analysis,
                key_insights=insights,
                recommendations=recommendations,
                metadata={
                    'analyzed_at': datetime.now().isoformat(),
                    'text_length': len(text),
                    'word_count': len(text.split()),
                    'has_audio': audio_path is not None,
                    'has_timestamps': timestamps is not None
                }
            )
            
        except Exception as e:
            logger.error(f"Error in content analysis: {e}")
            raise
    
    def _analyze_emotions(self, text: str, timestamps: Optional[List[Tuple[float, float, str]]]) -> EmotionAnalysis:
        """Analyze emotions in the content"""
        # Overall sentiment analysis
        sentiment_scores = self.sia.polarity_scores(text)
        overall_sentiment = 'neutral'
        if sentiment_scores['compound'] >= 0.05:
            overall_sentiment = 'positive'
        elif sentiment_scores['compound'] <= -0.05:
            overall_sentiment = 'negative'
        
        # Emotion detection
        emotion_scores = self._detect_emotions(text)
        dominant_emotion = max(emotion_scores, key=emotion_scores.get)
        
        # Timeline analysis if timestamps available
        emotion_timeline = []
        mood_changes = []
        
        if timestamps:
            previous_sentiment = None
            for start, end, segment_text in timestamps:
                segment_sentiment = self.sia.polarity_scores(segment_text)
                segment_emotions = self._detect_emotions(segment_text)
                
                timeline_entry = {
                    'start_time': start,
                    'end_time': end,
                    'sentiment': segment_sentiment['compound'],
                    'dominant_emotion': max(segment_emotions, key=segment_emotions.get),
                    'emotion_scores': segment_emotions
                }
                emotion_timeline.append(timeline_entry)
                
                # Detect mood changes
                current_sentiment = 'positive' if segment_sentiment['compound'] > 0.1 else (
                    'negative' if segment_sentiment['compound'] < -0.1 else 'neutral'
                )
                
                if previous_sentiment and current_sentiment != previous_sentiment:
                    mood_changes.append({
                        'time': start,
                        'from': previous_sentiment,
                        'to': current_sentiment,
                        'intensity': abs(segment_sentiment['compound'])
                    })
                
                previous_sentiment = current_sentiment
        
        return EmotionAnalysis(
            dominant_emotion=dominant_emotion,
            emotion_scores=emotion_scores,
            emotion_timeline=emotion_timeline,
            overall_sentiment=overall_sentiment,
            sentiment_score=sentiment_scores['compound'],
            mood_changes=mood_changes
        )
    
    def _analyze_speaking_patterns(self, 
                                 text: str,
                                 audio_path: Optional[str],
                                 timestamps: Optional[List[Tuple[float, float, str]]]) -> SpeakingPatternAnalysis:
        """Analyze speaking patterns"""
        words = text.split()
        sentences = sent_tokenize(text)
        
        # Calculate speaking rate if we have timestamps
        speaking_rate = 0
        if timestamps and len(timestamps) > 0:
            total_duration = timestamps[-1][1] - timestamps[0][0]
            if total_duration > 0:
                speaking_rate = (len(words) / total_duration) * 60  # words per minute
        
        # Detect filler words
        text_lower = text.lower()
        filler_count = sum(text_lower.count(filler) for filler in self.filler_words)
        filler_ratio = filler_count / len(words) if words else 0
        
        # Analyze pauses if audio available
        pause_frequency = 0
        pause_duration_avg = 0
        pace_variation = 0
        
        if audio_path and timestamps:
            pause_data = self._analyze_pauses(audio_path, timestamps)
            pause_frequency = pause_data['frequency']
            pause_duration_avg = pause_data['avg_duration']
            pace_variation = pause_data['pace_variation']
        
        # Detect emphasis patterns
        emphasis_patterns = self._detect_emphasis(text)
        
        # Calculate fluency score
        fluency_score = self._calculate_fluency(
            filler_ratio, pause_frequency, speaking_rate, len(sentences)
        )
        
        return SpeakingPatternAnalysis(
            speaking_rate=speaking_rate,
            pace_variation=pace_variation,
            pause_frequency=pause_frequency,
            pause_duration_avg=pause_duration_avg,
            filler_word_count=filler_count,
            filler_word_ratio=filler_ratio,
            emphasis_patterns=emphasis_patterns,
            fluency_score=fluency_score
        )
    
    def _analyze_complexity(self, text: str) -> ComplexityAnalysis:
        """Analyze content complexity and readability"""
        # Basic readability metrics
        readability_score = textstat.flesch_reading_ease(text)
        grade_level = textstat.flesch_kincaid_grade(text)
        
        # Vocabulary diversity
        words = [word.lower() for word in word_tokenize(text) if word.isalpha()]
        unique_words = set(words)
        vocabulary_diversity = len(unique_words) / len(words) if words else 0
        
        # Sentence complexity
        sentences = sent_tokenize(text)
        avg_sentence_length = np.mean([len(sent.split()) for sent in sentences]) if sentences else 0
        sentence_complexity = min(avg_sentence_length / 20, 1.0)  # Normalize to 0-1
        
        # Technical terms and jargon
        technical_ratio, jargon_score = self._analyze_technical_content(text)
        
        # Clarity score (inverse of complexity)
        clarity_score = (readability_score / 100) * (1 - jargon_score) * (1 - sentence_complexity)
        
        return ComplexityAnalysis(
            readability_score=readability_score,
            grade_level=grade_level,
            vocabulary_diversity=vocabulary_diversity,
            sentence_complexity=sentence_complexity,
            technical_term_ratio=technical_ratio,
            jargon_score=jargon_score,
            clarity_score=max(0, min(1, clarity_score))
        )
    
    def _analyze_bias(self, text: str) -> BiasAnalysis:
        """Detect bias and suggest inclusive language"""
        bias_instances = []
        bias_types = set()
        suggestions = []
        
        text_lower = text.lower()
        words = word_tokenize(text_lower)
        
        # Gender bias analysis
        gender_analysis = self._analyze_gender_bias(text_lower, words)
        if gender_analysis['bias_detected']:
            bias_types.add('gender')
            bias_instances.extend(gender_analysis['instances'])
            suggestions.extend(gender_analysis['suggestions'])
        
        # Age bias
        age_bias = self._detect_age_bias(text_lower)
        if age_bias:
            bias_types.add('age')
            bias_instances.extend(age_bias)
        
        # Ability bias
        ability_bias = self._detect_ability_bias(text_lower)
        if ability_bias:
            bias_types.add('ability')
            bias_instances.extend(ability_bias)
        
        # Stereotype detection
        stereotypes = self._detect_stereotypes(text)
        if stereotypes:
            bias_types.add('stereotype')
            bias_instances.extend(stereotypes)
        
        # Calculate inclusivity score
        inclusivity_score = self._calculate_inclusivity_score(
            len(bias_instances), len(words), gender_analysis['balance']
        )
        
        return BiasAnalysis(
            bias_detected=len(bias_instances) > 0,
            bias_types=list(bias_types),
            bias_instances=bias_instances,
            inclusivity_score=inclusivity_score,
            suggestions=suggestions,
            gender_balance=gender_analysis['balance']
        )
    
    def _detect_emotions(self, text: str) -> Dict[str, float]:
        """Detect emotions in text"""
        emotion_scores = {emotion: 0.0 for emotion in self.emotion_keywords}
        
        text_lower = text.lower()
        total_keywords = 0
        
        for emotion, keywords in self.emotion_keywords.items():
            for keyword in keywords:
                count = text_lower.count(keyword)
                emotion_scores[emotion] += count
                total_keywords += count
        
        # Normalize scores
        if total_keywords > 0:
            for emotion in emotion_scores:
                emotion_scores[emotion] /= total_keywords
        
        # Add sentiment-based emotion inference
        sentiment = self.sia.polarity_scores(text)
        if sentiment['pos'] > 0.5:
            emotion_scores['joy'] += 0.3
        elif sentiment['neg'] > 0.5:
            emotion_scores['sadness'] += 0.2
            emotion_scores['anger'] += 0.1
        
        # Normalize again
        total = sum(emotion_scores.values())
        if total > 0:
            for emotion in emotion_scores:
                emotion_scores[emotion] /= total
        
        return emotion_scores
    
    def _analyze_pauses(self, audio_path: str, timestamps: List[Tuple[float, float, str]]) -> Dict[str, float]:
        """Analyze pauses in audio"""
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=16000)
            
            # Detect silent periods
            frame_length = int(0.025 * sr)
            hop_length = int(0.010 * sr)
            energy = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
            
            # Threshold for silence
            silence_threshold = np.mean(energy) * 0.1
            silent_frames = energy < silence_threshold
            
            # Count pauses and calculate durations
            pauses = []
            in_pause = False
            pause_start = 0
            
            for i, is_silent in enumerate(silent_frames):
                time = i * hop_length / sr
                
                if is_silent and not in_pause:
                    in_pause = True
                    pause_start = time
                elif not is_silent and in_pause:
                    in_pause = False
                    pause_duration = time - pause_start
                    if pause_duration > 0.2:  # Only count pauses > 200ms
                        pauses.append(pause_duration)
            
            # Calculate metrics
            total_duration = len(y) / sr
            pause_frequency = len(pauses) / (total_duration / 60) if total_duration > 0 else 0
            pause_duration_avg = np.mean(pauses) if pauses else 0
            
            # Calculate pace variation
            if timestamps:
                segment_rates = []
                for i in range(1, len(timestamps)):
                    duration = timestamps[i][0] - timestamps[i-1][1]
                    words = len(timestamps[i][2].split())
                    if duration > 0:
                        rate = words / duration
                        segment_rates.append(rate)
                
                pace_variation = np.std(segment_rates) if segment_rates else 0
            else:
                pace_variation = 0
            
            return {
                'frequency': pause_frequency,
                'avg_duration': pause_duration_avg,
                'pace_variation': pace_variation
            }
            
        except Exception as e:
            logger.error(f"Error analyzing pauses: {e}")
            return {'frequency': 0, 'avg_duration': 0, 'pace_variation': 0}
    
    def _detect_emphasis(self, text: str) -> List[Dict[str, Any]]:
        """Detect emphasis patterns in text"""
        emphasis_patterns = []
        
        # Detect ALL CAPS words
        words = text.split()
        for i, word in enumerate(words):
            if word.isupper() and len(word) > 1:
                emphasis_patterns.append({
                    'type': 'capitalization',
                    'word': word,
                    'position': i,
                    'context': ' '.join(words[max(0, i-3):min(len(words), i+4)])
                })
        
        # Detect repeated punctuation
        exclamation_pattern = re.finditer(r'!+', text)
        for match in exclamation_pattern:
            if len(match.group()) > 1:
                emphasis_patterns.append({
                    'type': 'exclamation',
                    'count': len(match.group()),
                    'position': match.start(),
                    'context': text[max(0, match.start()-20):match.end()+20]
                })
        
        # Detect repeated words
        for i in range(len(words) - 1):
            if words[i].lower() == words[i+1].lower() and len(words[i]) > 2:
                emphasis_patterns.append({
                    'type': 'repetition',
                    'word': words[i],
                    'position': i,
                    'context': ' '.join(words[max(0, i-3):min(len(words), i+5)])
                })
        
        return emphasis_patterns
    
    def _calculate_fluency(self, filler_ratio: float, pause_frequency: float, 
                          speaking_rate: float, sentence_count: int) -> float:
        """Calculate overall fluency score"""
        # Ideal ranges
        ideal_filler_ratio = 0.02  # 2% filler words
        ideal_pause_frequency = 2.0  # 2 pauses per minute
        ideal_speaking_rate = 150  # 150 words per minute
        
        # Calculate component scores
        filler_score = max(0, 1 - (filler_ratio / ideal_filler_ratio))
        pause_score = max(0, 1 - abs(pause_frequency - ideal_pause_frequency) / ideal_pause_frequency)
        
        if speaking_rate > 0:
            rate_score = max(0, 1 - abs(speaking_rate - ideal_speaking_rate) / ideal_speaking_rate)
        else:
            rate_score = 0.5  # Default if no rate available
        
        # Weighted average
        fluency_score = (filler_score * 0.3 + pause_score * 0.3 + rate_score * 0.4)
        
        return max(0, min(1, fluency_score))
    
    def _analyze_technical_content(self, text: str) -> Tuple[float, float]:
        """Analyze technical terms and jargon"""
        words = [word.lower() for word in word_tokenize(text) if word.isalpha()]
        
        # Simple heuristic: longer words and words with specific patterns
        technical_words = []
        for word in words:
            if (len(word) > 10 or  # Long words
                word.endswith(('tion', 'ment', 'ization', 'ology', 'ometry')) or
                '-' in word or '_' in word):  # Compound terms
                technical_words.append(word)
        
        technical_ratio = len(technical_words) / len(words) if words else 0
        
        # Jargon score based on word frequency
        if self.nlp:
            doc = self.nlp(text)
            rare_words = [token.text for token in doc if token.is_alpha and token.is_lower and 
                         not token.is_stop and len(token.text) > 5]
            jargon_score = len(rare_words) / len(words) if words else 0
        else:
            jargon_score = technical_ratio  # Fallback
        
        return technical_ratio, min(1.0, jargon_score)
    
    def _analyze_gender_bias(self, text_lower: str, words: List[str]) -> Dict[str, Any]:
        """Analyze gender bias in text"""
        gender_counts = {
            'male': 0,
            'female': 0,
            'neutral': 0
        }
        
        instances = []
        suggestions = []
        
        # Count gendered terms
        for term in self.bias_indicators['gender']['male_terms']:
            count = words.count(term)
            gender_counts['male'] += count
            if count > 0:
                instances.append({
                    'type': 'gender',
                    'term': term,
                    'count': count,
                    'category': 'male-specific'
                })
        
        for term in self.bias_indicators['gender']['female_terms']:
            count = words.count(term)
            gender_counts['female'] += count
            if count > 0:
                instances.append({
                    'type': 'gender',
                    'term': term,
                    'count': count,
                    'category': 'female-specific'
                })
        
        for term in self.bias_indicators['gender']['neutral_terms']:
            gender_counts['neutral'] += words.count(term)
        
        # Calculate balance
        total_gendered = gender_counts['male'] + gender_counts['female']
        if total_gendered > 0:
            balance = {
                'male': gender_counts['male'] / total_gendered,
                'female': gender_counts['female'] / total_gendered,
                'neutral_ratio': gender_counts['neutral'] / (total_gendered + gender_counts['neutral'])
            }
            
            # Detect imbalance
            if abs(balance['male'] - balance['female']) > 0.3:
                suggestions.append("Consider using more gender-neutral language (they/them) instead of he/she")
                suggestions.append("Balance gender representation in examples and references")
        else:
            balance = {'male': 0, 'female': 0, 'neutral_ratio': 1}
        
        return {
            'bias_detected': len(instances) > 0 and balance['neutral_ratio'] < 0.5,
            'instances': instances,
            'suggestions': suggestions,
            'balance': balance
        }
    
    def _detect_age_bias(self, text_lower: str) -> List[Dict[str, Any]]:
        """Detect age-related bias"""
        instances = []
        
        for term in self.bias_indicators['age']:
            if term in text_lower:
                # Find context
                index = text_lower.find(term)
                context = text_lower[max(0, index-50):index+50+len(term)]
                
                instances.append({
                    'type': 'age',
                    'term': term,
                    'context': context,
                    'suggestion': f"Consider using age-neutral terms instead of '{term}'"
                })
        
        return instances
    
    def _detect_ability_bias(self, text_lower: str) -> List[Dict[str, Any]]:
        """Detect ability-related bias"""
        instances = []
        
        problematic_terms = {
            'disabled': 'person with disabilities',
            'handicapped': 'person with disabilities',
            'normal': 'typical',
            'special needs': 'specific needs'
        }
        
        for term, alternative in problematic_terms.items():
            if term in text_lower:
                instances.append({
                    'type': 'ability',
                    'term': term,
                    'suggestion': f"Consider using '{alternative}' instead of '{term}'"
                })
        
        return instances
    
    def _detect_stereotypes(self, text: str) -> List[Dict[str, Any]]:
        """Detect potential stereotypes"""
        instances = []
        
        # Simple pattern matching for common stereotypes
        stereotype_patterns = [
            (r'all\s+(\w+)\s+are', 'Avoid generalizations about groups'),
            (r'(\w+)\s+always', 'Avoid absolute statements about groups'),
            (r'(\w+)\s+never', 'Avoid absolute negative statements'),
            (r'typical\s+(\w+)', 'Avoid stereotypical characterizations')
        ]
        
        for pattern, suggestion in stereotype_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                instances.append({
                    'type': 'stereotype',
                    'text': match.group(),
                    'suggestion': suggestion
                })
        
        return instances
    
    def _calculate_inclusivity_score(self, bias_count: int, word_count: int, 
                                   gender_balance: Dict[str, float]) -> float:
        """Calculate overall inclusivity score"""
        # Base score
        bias_ratio = bias_count / word_count if word_count > 0 else 0
        base_score = max(0, 1 - (bias_ratio * 10))  # Penalize bias heavily
        
        # Gender balance score
        gender_score = gender_balance.get('neutral_ratio', 0) * 0.5 + (
            1 - abs(gender_balance.get('male', 0.5) - 0.5) * 2
        ) * 0.5
        
        # Combined score
        inclusivity_score = base_score * 0.7 + gender_score * 0.3
        
        return max(0, min(1, inclusivity_score))
    
    def _generate_insights(self, emotion: EmotionAnalysis, speaking: SpeakingPatternAnalysis,
                         complexity: ComplexityAnalysis, bias: BiasAnalysis) -> List[str]:
        """Generate key insights from analysis"""
        insights = []
        
        # Emotion insights
        if emotion.sentiment_score > 0.5:
            insights.append(f"Content has a strongly positive tone ({emotion.dominant_emotion})")
        elif emotion.sentiment_score < -0.5:
            insights.append(f"Content has a negative tone ({emotion.dominant_emotion})")
        
        if len(emotion.mood_changes) > 2:
            insights.append(f"Detected {len(emotion.mood_changes)} significant mood shifts")
        
        # Speaking pattern insights
        if speaking.speaking_rate > 180:
            insights.append("Very fast speaking pace detected - may impact comprehension")
        elif speaking.speaking_rate < 120 and speaking.speaking_rate > 0:
            insights.append("Slow speaking pace - good for complex topics")
        
        if speaking.filler_word_ratio > 0.05:
            insights.append(f"High filler word usage ({speaking.filler_word_count} instances)")
        
        # Complexity insights
        if complexity.grade_level > 12:
            insights.append(f"Content requires college-level comprehension (grade {complexity.grade_level:.1f})")
        elif complexity.grade_level < 8:
            insights.append("Content is easily accessible to general audience")
        
        if complexity.jargon_score > 0.3:
            insights.append("High technical jargon detected - may need simplification")
        
        # Bias insights
        if bias.bias_detected:
            insights.append(f"Detected {len(bias.bias_types)} types of potential bias")
        
        if bias.inclusivity_score > 0.8:
            insights.append("Content demonstrates good inclusive language practices")
        
        return insights
    
    def _generate_recommendations(self, emotion: EmotionAnalysis, speaking: SpeakingPatternAnalysis,
                                complexity: ComplexityAnalysis, bias: BiasAnalysis) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Emotion recommendations
        if emotion.sentiment_score < -0.3:
            recommendations.append("Consider adding more positive examples or solutions")
        
        if len(emotion.mood_changes) > 5:
            recommendations.append("Maintain more consistent emotional tone throughout")
        
        # Speaking recommendations
        if speaking.filler_word_ratio > 0.05:
            recommendations.append("Reduce filler words for more professional delivery")
        
        if speaking.fluency_score < 0.6:
            recommendations.append("Practice smoother delivery with fewer pauses and fillers")
        
        if speaking.speaking_rate > 180:
            recommendations.append("Slow down speaking pace for better comprehension")
        
        # Complexity recommendations
        if complexity.readability_score < 30:
            recommendations.append("Simplify language - current content is very difficult to read")
        
        if complexity.vocabulary_diversity < 0.3:
            recommendations.append("Use more varied vocabulary to maintain engagement")
        
        if complexity.jargon_score > 0.3:
            recommendations.append("Define technical terms or use simpler alternatives")
        
        # Bias recommendations
        if bias.bias_detected:
            recommendations.extend(bias.suggestions[:3])  # Top 3 bias suggestions
        
        if bias.gender_balance['neutral_ratio'] < 0.3:
            recommendations.append("Increase use of gender-neutral pronouns (they/them)")
        
        return recommendations