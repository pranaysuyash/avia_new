"""
Advanced AI-Powered Content Analysis Module
Implements Task 39: Create advanced AI-powered content analysis
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
import re
import time
from collections import defaultdict, Counter
import json
import streamlit as st
from textstat import flesch_reading_ease, flesch_kincaid_grade, automated_readability_index
from textblob import TextBlob
import openai
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class EmotionAnalysis:
    """Emotion analysis results"""
    dominant_emotion: str
    emotion_scores: Dict[str, float]
    emotion_timeline: List[Dict[str, Any]]
    confidence: float
    emotional_intensity: float


@dataclass
class SpeakingPatternAnalysis:
    """Speaking pattern analysis results"""
    average_pace: float  # words per minute
    pace_variation: float
    pause_frequency: float
    emphasis_points: List[Dict[str, Any]]
    speaking_rhythm: str  # "steady", "varied", "irregular"
    confidence_indicators: List[str]


@dataclass
class ContentComplexityAnalysis:
    """Content complexity analysis results"""
    readability_score: float
    grade_level: float
    complexity_rating: str  # "simple", "moderate", "complex", "advanced"
    vocabulary_diversity: float
    sentence_complexity: float
    technical_density: float
    recommendations: List[str]


@dataclass
class BiasDetectionAnalysis:
    """Bias detection analysis results"""
    bias_score: float
    detected_biases: List[Dict[str, Any]]
    inclusive_language_score: float
    problematic_phrases: List[Dict[str, Any]]
    suggestions: List[str]
    bias_categories: Dict[str, float]


@dataclass
class PlagiarismAnalysis:
    """Plagiarism detection analysis results"""
    similarity_score: float
    potential_matches: List[Dict[str, Any]]
    originality_score: float
    flagged_segments: List[Dict[str, Any]]
    confidence: float


class EmotionDetector:
    """Advanced emotion detection and mood tracking"""
    
    def __init__(self):
        self.emotion_keywords = self._load_emotion_keywords()
        self.openai_client = self._initialize_openai()
    
    def _initialize_openai(self):
        """Initialize OpenAI client if available"""
        try:
            import os
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                return openai.OpenAI(api_key=api_key)
        except Exception as e:
            logger.warning(f"OpenAI client not available: {e}")
        return None
    
    def _load_emotion_keywords(self) -> Dict[str, List[str]]:
        """Load emotion keyword mappings"""
        return {
            'joy': ['happy', 'excited', 'pleased', 'delighted', 'thrilled', 'cheerful', 'optimistic'],
            'sadness': ['sad', 'disappointed', 'upset', 'depressed', 'melancholy', 'sorrowful'],
            'anger': ['angry', 'frustrated', 'irritated', 'furious', 'annoyed', 'outraged'],
            'fear': ['afraid', 'worried', 'anxious', 'nervous', 'scared', 'concerned', 'apprehensive'],
            'surprise': ['surprised', 'amazed', 'astonished', 'shocked', 'stunned', 'bewildered'],
            'disgust': ['disgusted', 'revolted', 'repulsed', 'sickened', 'appalled'],
            'trust': ['confident', 'secure', 'assured', 'certain', 'convinced', 'trusting'],
            'anticipation': ['eager', 'expectant', 'hopeful', 'anticipating', 'looking forward']
        }
    
    def analyze_emotions(self, text: str, timestamps: Optional[List[Dict]] = None) -> EmotionAnalysis:
        """Analyze emotions in text with optional timeline"""
        
        # Basic emotion analysis using keywords and TextBlob
        basic_emotions = self._analyze_basic_emotions(text)
        
        # Advanced emotion analysis using OpenAI if available
        if self.openai_client:
            advanced_emotions = self._analyze_advanced_emotions(text)
            # Combine basic and advanced results
            emotion_scores = self._combine_emotion_scores(basic_emotions, advanced_emotions)
        else:
            emotion_scores = basic_emotions
        
        # Create emotion timeline if timestamps available
        emotion_timeline = []
        if timestamps:
            emotion_timeline = self._create_emotion_timeline(text, timestamps)
        
        # Determine dominant emotion
        dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
        
        # Calculate overall confidence and intensity
        confidence = max(emotion_scores.values())
        emotional_intensity = sum(emotion_scores.values()) / len(emotion_scores)
        
        return EmotionAnalysis(
            dominant_emotion=dominant_emotion,
            emotion_scores=emotion_scores,
            emotion_timeline=emotion_timeline,
            confidence=confidence,
            emotional_intensity=emotional_intensity
        )
    
    def _analyze_basic_emotions(self, text: str) -> Dict[str, float]:
        """Basic emotion analysis using keywords and sentiment"""
        text_lower = text.lower()
        emotion_scores = {}
        
        # Keyword-based emotion detection
        for emotion, keywords in self.emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            emotion_scores[emotion] = score / len(keywords)  # Normalize
        
        # Enhance with TextBlob sentiment
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Map sentiment to emotions
        if polarity > 0.1:
            emotion_scores['joy'] += polarity * 0.5
        elif polarity < -0.1:
            emotion_scores['sadness'] += abs(polarity) * 0.5
        
        # Normalize scores
        max_score = max(emotion_scores.values()) if emotion_scores.values() else 1
        if max_score > 0:
            emotion_scores = {k: v / max_score for k, v in emotion_scores.items()}
        
        return emotion_scores
    
    def _analyze_advanced_emotions(self, text: str) -> Dict[str, float]:
        """Advanced emotion analysis using OpenAI"""
        try:
            prompt = f"""
            Analyze the emotional content of the following text and provide scores (0-1) for each emotion:
            - Joy/Happiness
            - Sadness
            - Anger
            - Fear/Anxiety
            - Surprise
            - Disgust
            - Trust/Confidence
            - Anticipation
            
            Text: "{text[:1000]}"
            
            Respond with JSON format: {{"joy": 0.0, "sadness": 0.0, ...}}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"Advanced emotion analysis failed: {e}")
            return {}
    
    def _combine_emotion_scores(self, basic: Dict[str, float], advanced: Dict[str, float]) -> Dict[str, float]:
        """Combine basic and advanced emotion scores"""
        combined = basic.copy()
        
        for emotion, score in advanced.items():
            if emotion in combined:
                # Weighted average: 60% advanced, 40% basic
                combined[emotion] = 0.6 * score + 0.4 * combined[emotion]
            else:
                combined[emotion] = score
        
        return combined
    
    def _create_emotion_timeline(self, text: str, timestamps: List[Dict]) -> List[Dict[str, Any]]:
        """Create emotion timeline based on timestamps"""
        timeline = []
        
        # Split text into segments based on timestamps
        sentences = text.split('.')
        segment_size = len(sentences) // min(len(timestamps), 10)  # Max 10 segments
        
        for i in range(0, len(sentences), max(1, segment_size)):
            segment_text = '. '.join(sentences[i:i+segment_size])
            if segment_text.strip():
                segment_emotions = self._analyze_basic_emotions(segment_text)
                dominant = max(segment_emotions.items(), key=lambda x: x[1])[0]
                
                timeline.append({
                    'timestamp': i * segment_size,  # Approximate timestamp
                    'text_segment': segment_text[:100] + "...",
                    'dominant_emotion': dominant,
                    'emotion_scores': segment_emotions
                })
        
        return timeline


class SpeakingPatternAnalyzer:
    """Analyze speaking patterns, pace, and emphasis"""
    
    def __init__(self):
        self.confidence_indicators = [
            'definitely', 'certainly', 'absolutely', 'clearly', 'obviously',
            'without doubt', 'I believe', 'I think', 'in my opinion'
        ]
    
    def analyze_speaking_patterns(self, text: str, audio_duration: float = None, 
                                timestamps: Optional[List[Dict]] = None) -> SpeakingPatternAnalysis:
        """Analyze speaking patterns from text and optional audio data"""
        
        # Calculate speaking pace
        word_count = len(text.split())
        if audio_duration and audio_duration > 0:
            average_pace = (word_count / audio_duration) * 60  # words per minute
        else:
            # Estimate based on average speaking speed
            average_pace = 150  # Default assumption
        
        # Analyze pace variation
        pace_variation = self._analyze_pace_variation(text, timestamps)
        
        # Analyze pauses (based on punctuation and sentence structure)
        pause_frequency = self._analyze_pause_frequency(text)
        
        # Detect emphasis points
        emphasis_points = self._detect_emphasis_points(text)
        
        # Determine speaking rhythm
        speaking_rhythm = self._determine_speaking_rhythm(pace_variation, pause_frequency)
        
        # Find confidence indicators
        confidence_indicators = self._find_confidence_indicators(text)
        
        return SpeakingPatternAnalysis(
            average_pace=average_pace,
            pace_variation=pace_variation,
            pause_frequency=pause_frequency,
            emphasis_points=emphasis_points,
            speaking_rhythm=speaking_rhythm,
            confidence_indicators=confidence_indicators
        )
    
    def _analyze_pace_variation(self, text: str, timestamps: Optional[List[Dict]]) -> float:
        """Analyze variation in speaking pace"""
        sentences = text.split('.')
        sentence_lengths = [len(sentence.split()) for sentence in sentences if sentence.strip()]
        
        if len(sentence_lengths) < 2:
            return 0.0
        
        # Calculate coefficient of variation
        mean_length = np.mean(sentence_lengths)
        std_length = np.std(sentence_lengths)
        
        return std_length / mean_length if mean_length > 0 else 0.0
    
    def _analyze_pause_frequency(self, text: str) -> float:
        """Analyze frequency of pauses based on punctuation"""
        pause_indicators = [',', ';', '...', '--', '—']
        total_pauses = sum(text.count(indicator) for indicator in pause_indicators)
        word_count = len(text.split())
        
        return total_pauses / word_count if word_count > 0 else 0.0
    
    def _detect_emphasis_points(self, text: str) -> List[Dict[str, Any]]:
        """Detect points of emphasis in speech"""
        emphasis_points = []
        
        # Look for capitalized words (excluding proper nouns)
        words = text.split()
        for i, word in enumerate(words):
            if word.isupper() and len(word) > 2:
                emphasis_points.append({
                    'position': i,
                    'word': word,
                    'type': 'capitalization',
                    'context': ' '.join(words[max(0, i-2):i+3])
                })
        
        # Look for repeated words or phrases
        word_counts = Counter(word.lower() for word in words if len(word) > 3)
        for word, count in word_counts.items():
            if count > 2:
                emphasis_points.append({
                    'word': word,
                    'type': 'repetition',
                    'frequency': count
                })
        
        # Look for exclamation marks
        exclamation_sentences = [s.strip() for s in text.split('!') if s.strip()]
        for sentence in exclamation_sentences:
            if sentence:
                emphasis_points.append({
                    'text': sentence,
                    'type': 'exclamation',
                    'context': sentence
                })
        
        return emphasis_points
    
    def _determine_speaking_rhythm(self, pace_variation: float, pause_frequency: float) -> str:
        """Determine overall speaking rhythm"""
        if pace_variation < 0.3 and pause_frequency < 0.05:
            return "steady"
        elif pace_variation < 0.6 and pause_frequency < 0.1:
            return "varied"
        else:
            return "irregular"
    
    def _find_confidence_indicators(self, text: str) -> List[str]:
        """Find indicators of confidence or uncertainty in speech"""
        text_lower = text.lower()
        found_indicators = []
        
        for indicator in self.confidence_indicators:
            if indicator in text_lower:
                found_indicators.append(indicator)
        
        # Add uncertainty indicators
        uncertainty_indicators = ['maybe', 'perhaps', 'I guess', 'sort of', 'kind of', 'um', 'uh']
        for indicator in uncertainty_indicators:
            if indicator in text_lower:
                found_indicators.append(f"uncertainty: {indicator}")
        
        return found_indicators


class ContentComplexityAnalyzer:
    """Analyze content complexity and readability"""
    
    def __init__(self):
        self.technical_terms = self._load_technical_terms()
    
    def _load_technical_terms(self) -> List[str]:
        """Load common technical terms for density analysis"""
        return [
            'algorithm', 'implementation', 'optimization', 'architecture', 'framework',
            'methodology', 'analysis', 'synthesis', 'paradigm', 'infrastructure',
            'scalability', 'integration', 'configuration', 'specification', 'protocol'
        ]
    
    def analyze_complexity(self, text: str) -> ContentComplexityAnalysis:
        """Analyze content complexity and readability"""
        
        # Calculate readability scores
        readability_score = flesch_reading_ease(text)
        grade_level = flesch_kincaid_grade(text)
        
        # Determine complexity rating
        complexity_rating = self._determine_complexity_rating(readability_score)
        
        # Calculate vocabulary diversity
        vocabulary_diversity = self._calculate_vocabulary_diversity(text)
        
        # Analyze sentence complexity
        sentence_complexity = self._analyze_sentence_complexity(text)
        
        # Calculate technical density
        technical_density = self._calculate_technical_density(text)
        
        # Generate recommendations
        recommendations = self._generate_complexity_recommendations(
            readability_score, grade_level, vocabulary_diversity, sentence_complexity
        )
        
        return ContentComplexityAnalysis(
            readability_score=readability_score,
            grade_level=grade_level,
            complexity_rating=complexity_rating,
            vocabulary_diversity=vocabulary_diversity,
            sentence_complexity=sentence_complexity,
            technical_density=technical_density,
            recommendations=recommendations
        )
    
    def _determine_complexity_rating(self, readability_score: float) -> str:
        """Determine complexity rating based on readability score"""
        if readability_score >= 80:
            return "simple"
        elif readability_score >= 60:
            return "moderate"
        elif readability_score >= 30:
            return "complex"
        else:
            return "advanced"
    
    def _calculate_vocabulary_diversity(self, text: str) -> float:
        """Calculate vocabulary diversity (type-token ratio)"""
        words = [word.lower() for word in re.findall(r'\b\w+\b', text)]
        if not words:
            return 0.0
        
        unique_words = set(words)
        return len(unique_words) / len(words)
    
    def _analyze_sentence_complexity(self, text: str) -> float:
        """Analyze average sentence complexity"""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        if not sentences:
            return 0.0
        
        complexities = []
        for sentence in sentences:
            # Count subordinate clauses (rough approximation)
            subordinate_indicators = ['because', 'although', 'while', 'since', 'if', 'when', 'that', 'which']
            complexity = sum(1 for indicator in subordinate_indicators if indicator in sentence.lower())
            complexities.append(complexity)
        
        return np.mean(complexities)
    
    def _calculate_technical_density(self, text: str) -> float:
        """Calculate density of technical terms"""
        text_lower = text.lower()
        words = text_lower.split()
        
        if not words:
            return 0.0
        
        technical_count = sum(1 for term in self.technical_terms if term in text_lower)
        return technical_count / len(words)
    
    def _generate_complexity_recommendations(self, readability: float, grade_level: float,
                                           vocab_diversity: float, sentence_complexity: float) -> List[str]:
        """Generate recommendations for improving content accessibility"""
        recommendations = []
        
        if readability < 50:
            recommendations.append("Consider simplifying sentence structure for better readability")
        
        if grade_level > 12:
            recommendations.append("Content may be too advanced for general audiences")
        
        if vocab_diversity < 0.3:
            recommendations.append("Consider using more varied vocabulary")
        elif vocab_diversity > 0.8:
            recommendations.append("High vocabulary diversity - ensure clarity for target audience")
        
        if sentence_complexity > 2:
            recommendations.append("Consider breaking down complex sentences")
        
        return recommendations


# Global instances
emotion_detector = EmotionDetector()
speaking_pattern_analyzer = SpeakingPatternAnalyzer()
complexity_analyzer = ContentComplexityAnalyzer()

c
lass BiasDetector:
    """Detect bias and analyze inclusive language"""
    
    def __init__(self):
        self.bias_patterns = self._load_bias_patterns()
        self.inclusive_alternatives = self._load_inclusive_alternatives()
        self.openai_client = self._initialize_openai()
    
    def _initialize_openai(self):
        """Initialize OpenAI client if available"""
        try:
            import os
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                return openai.OpenAI(api_key=api_key)
        except Exception as e:
            logger.warning(f"OpenAI client not available: {e}")
        return None
    
    def _load_bias_patterns(self) -> Dict[str, List[str]]:
        """Load bias detection patterns"""
        return {
            'gender': [
                'guys', 'mankind', 'manpower', 'chairman', 'policeman', 'fireman',
                'he/she', 'his/her', 'businessman', 'workman'
            ],
            'age': [
                'young people these days', 'older workers', 'millennials are',
                'boomers are', 'too old', 'too young'
            ],
            'racial': [
                'articulate for a', 'exotic', 'urban', 'inner city',
                'well-spoken for', 'surprisingly intelligent'
            ],
            'ability': [
                'suffers from', 'victim of', 'confined to wheelchair',
                'normal person', 'able-bodied'
            ],
            'cultural': [
                'foreign-sounding name', 'exotic cuisine', 'primitive culture',
                'third world', 'developing nation'
            ]
        }
    
    def _load_inclusive_alternatives(self) -> Dict[str, str]:
        """Load inclusive language alternatives"""
        return {
            'guys': 'everyone/team/folks',
            'mankind': 'humanity/people',
            'manpower': 'workforce/staff',
            'chairman': 'chairperson/chair',
            'policeman': 'police officer',
            'fireman': 'firefighter',
            'businessman': 'businessperson',
            'workman': 'worker',
            'suffers from': 'has/lives with',
            'victim of': 'person with',
            'confined to wheelchair': 'uses a wheelchair',
            'normal person': 'person without disability',
            'third world': 'developing countries'
        }
    
    def analyze_bias(self, text: str) -> BiasDetectionAnalysis:
        """Analyze text for bias and inclusive language"""
        
        # Detect bias patterns
        detected_biases = self._detect_bias_patterns(text)
        
        # Calculate bias scores by category
        bias_categories = self._calculate_bias_categories(detected_biases)
        
        # Overall bias score
        bias_score = sum(bias_categories.values()) / len(bias_categories) if bias_categories else 0.0
        
        # Find problematic phrases
        problematic_phrases = self._find_problematic_phrases(text)
        
        # Calculate inclusive language score
        inclusive_language_score = self._calculate_inclusive_language_score(text, problematic_phrases)
        
        # Generate suggestions
        suggestions = self._generate_bias_suggestions(detected_biases, problematic_phrases)
        
        # Advanced bias analysis using OpenAI if available
        if self.openai_client:
            advanced_analysis = self._analyze_advanced_bias(text)
            suggestions.extend(advanced_analysis.get('suggestions', []))
        
        return BiasDetectionAnalysis(
            bias_score=bias_score,
            detected_biases=detected_biases,
            inclusive_language_score=inclusive_language_score,
            problematic_phrases=problematic_phrases,
            suggestions=suggestions,
            bias_categories=bias_categories
        )
    
    def _detect_bias_patterns(self, text: str) -> List[Dict[str, Any]]:
        """Detect bias patterns in text"""
        text_lower = text.lower()
        detected_biases = []
        
        for category, patterns in self.bias_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    # Find context around the bias
                    start_idx = text_lower.find(pattern)
                    context_start = max(0, start_idx - 50)
                    context_end = min(len(text), start_idx + len(pattern) + 50)
                    context = text[context_start:context_end]
                    
                    detected_biases.append({
                        'category': category,
                        'pattern': pattern,
                        'context': context,
                        'position': start_idx,
                        'severity': self._assess_bias_severity(pattern, context)
                    })
        
        return detected_biases
    
    def _assess_bias_severity(self, pattern: str, context: str) -> str:
        """Assess severity of detected bias"""
        # Simple heuristic - could be enhanced with ML
        high_severity_patterns = ['suffers from', 'victim of', 'primitive', 'exotic']
        
        if pattern in high_severity_patterns:
            return 'high'
        elif len(pattern.split()) > 2:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_bias_categories(self, detected_biases: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate bias scores by category"""
        categories = defaultdict(list)
        
        for bias in detected_biases:
            severity_score = {'low': 0.3, 'medium': 0.6, 'high': 1.0}[bias['severity']]
            categories[bias['category']].append(severity_score)
        
        # Average scores by category
        return {category: np.mean(scores) for category, scores in categories.items()}
    
    def _find_problematic_phrases(self, text: str) -> List[Dict[str, Any]]:
        """Find phrases that could be more inclusive"""
        problematic = []
        text_lower = text.lower()
        
        for phrase, alternative in self.inclusive_alternatives.items():
            if phrase in text_lower:
                start_idx = text_lower.find(phrase)
                context_start = max(0, start_idx - 30)
                context_end = min(len(text), start_idx + len(phrase) + 30)
                context = text[context_start:context_end]
                
                problematic.append({
                    'phrase': phrase,
                    'alternative': alternative,
                    'context': context,
                    'position': start_idx
                })
        
        return problematic
    
    def _calculate_inclusive_language_score(self, text: str, problematic_phrases: List[Dict]) -> float:
        """Calculate inclusive language score (0-1, higher is better)"""
        word_count = len(text.split())
        if word_count == 0:
            return 1.0
        
        # Penalty for problematic phrases
        penalty = len(problematic_phrases) / word_count * 100  # Normalize by text length
        
        # Base score starts at 1.0, reduced by penalties
        score = max(0.0, 1.0 - penalty)
        
        return score
    
    def _generate_bias_suggestions(self, detected_biases: List[Dict], 
                                 problematic_phrases: List[Dict]) -> List[str]:
        """Generate suggestions for reducing bias"""
        suggestions = []
        
        # Suggestions based on detected biases
        bias_categories = set(bias['category'] for bias in detected_biases)
        
        if 'gender' in bias_categories:
            suggestions.append("Consider using gender-neutral language (e.g., 'team' instead of 'guys')")
        
        if 'age' in bias_categories:
            suggestions.append("Avoid age-related generalizations and stereotypes")
        
        if 'racial' in bias_categories:
            suggestions.append("Review language for potential racial bias or stereotypes")
        
        if 'ability' in bias_categories:
            suggestions.append("Use person-first language when discussing disabilities")
        
        # Specific suggestions for problematic phrases
        for phrase_info in problematic_phrases[:3]:  # Limit to top 3
            suggestions.append(f"Consider replacing '{phrase_info['phrase']}' with '{phrase_info['alternative']}'")
        
        return suggestions
    
    def _analyze_advanced_bias(self, text: str) -> Dict[str, Any]:
        """Advanced bias analysis using OpenAI"""
        try:
            prompt = f"""
            Analyze the following text for potential bias and suggest improvements for inclusive language.
            Focus on:
            1. Gender bias
            2. Racial/ethnic bias
            3. Age bias
            4. Ability bias
            5. Cultural bias
            
            Text: "{text[:1500]}"
            
            Provide response in JSON format:
            {{
                "bias_detected": true/false,
                "bias_types": ["type1", "type2"],
                "suggestions": ["suggestion1", "suggestion2"],
                "overall_inclusivity": 0.0-1.0
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Advanced bias analysis failed: {e}")
            return {}


class PlagiarismDetector:
    """Detect potential plagiarism and similarity to known content"""
    
    def __init__(self):
        self.known_content_database = []  # Would be populated with known content
        self.similarity_threshold = 0.7
    
    def analyze_plagiarism(self, text: str, reference_database: List[str] = None) -> PlagiarismAnalysis:
        """Analyze text for potential plagiarism"""
        
        # Use provided database or default
        database = reference_database or self.known_content_database
        
        if not database:
            # No reference content available
            return PlagiarismAnalysis(
                similarity_score=0.0,
                potential_matches=[],
                originality_score=1.0,
                flagged_segments=[],
                confidence=0.5
            )
        
        # Find potential matches
        potential_matches = self._find_potential_matches(text, database)
        
        # Calculate overall similarity score
        similarity_score = max([match['similarity'] for match in potential_matches], default=0.0)
        
        # Find flagged segments
        flagged_segments = self._find_flagged_segments(text, potential_matches)
        
        # Calculate originality score
        originality_score = max(0.0, 1.0 - similarity_score)
        
        # Calculate confidence based on database size and match quality
        confidence = min(1.0, len(database) / 100) * 0.8 + 0.2  # Base confidence of 0.2
        
        return PlagiarismAnalysis(
            similarity_score=similarity_score,
            potential_matches=potential_matches,
            originality_score=originality_score,
            flagged_segments=flagged_segments,
            confidence=confidence
        )
    
    def _find_potential_matches(self, text: str, database: List[str]) -> List[Dict[str, Any]]:
        """Find potential matches in reference database"""
        matches = []
        
        # Simple n-gram based similarity (could be enhanced with embeddings)
        text_ngrams = self._get_ngrams(text, n=5)
        
        for i, reference in enumerate(database):
            ref_ngrams = self._get_ngrams(reference, n=5)
            
            # Calculate Jaccard similarity
            similarity = self._jaccard_similarity(text_ngrams, ref_ngrams)
            
            if similarity > 0.1:  # Only include meaningful similarities
                matches.append({
                    'reference_id': i,
                    'reference_text': reference[:200] + "...",
                    'similarity': similarity,
                    'match_type': 'ngram_similarity'
                })
        
        # Sort by similarity score
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        return matches[:10]  # Return top 10 matches
    
    def _get_ngrams(self, text: str, n: int = 5) -> set:
        """Get n-grams from text"""
        words = text.lower().split()
        ngrams = set()
        
        for i in range(len(words) - n + 1):
            ngram = ' '.join(words[i:i+n])
            ngrams.add(ngram)
        
        return ngrams
    
    def _jaccard_similarity(self, set1: set, set2: set) -> float:
        """Calculate Jaccard similarity between two sets"""
        if not set1 and not set2:
            return 1.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _find_flagged_segments(self, text: str, matches: List[Dict]) -> List[Dict[str, Any]]:
        """Find specific segments that may be plagiarized"""
        flagged = []
        
        # Simple approach: find common phrases with high-similarity matches
        for match in matches[:3]:  # Check top 3 matches
            if match['similarity'] > self.similarity_threshold:
                # Find common segments (simplified)
                text_sentences = text.split('.')
                ref_sentences = match['reference_text'].split('.')
                
                for i, sentence in enumerate(text_sentences):
                    sentence = sentence.strip()
                    if len(sentence) > 20:  # Only check substantial sentences
                        for ref_sentence in ref_sentences:
                            ref_sentence = ref_sentence.strip()
                            if len(ref_sentence) > 20:
                                # Simple similarity check
                                words_similarity = len(set(sentence.lower().split()).intersection(
                                    set(ref_sentence.lower().split())
                                )) / max(len(sentence.split()), len(ref_sentence.split()))
                                
                                if words_similarity > 0.6:
                                    flagged.append({
                                        'segment': sentence,
                                        'reference_segment': ref_sentence,
                                        'similarity': words_similarity,
                                        'position': i
                                    })
        
        return flagged


# Additional global instances
bias_detector = BiasDetector()
plagiarism_detector = PlagiarismDetector()


class AdvancedContentAnalyzer:
    """Main class that orchestrates all advanced content analysis"""
    
    def __init__(self):
        self.emotion_detector = emotion_detector
        self.speaking_pattern_analyzer = speaking_pattern_analyzer
        self.complexity_analyzer = complexity_analyzer
        self.bias_detector = bias_detector
        self.plagiarism_detector = plagiarism_detector
    
    def analyze_content(self, text: str, audio_duration: float = None,
                       timestamps: Optional[List[Dict]] = None,
                       reference_database: List[str] = None) -> Dict[str, Any]:
        """Perform comprehensive content analysis"""
        
        analysis_results = {}
        
        try:
            # Emotion analysis
            analysis_results['emotions'] = self.emotion_detector.analyze_emotions(text, timestamps)
            
            # Speaking pattern analysis
            analysis_results['speaking_patterns'] = self.speaking_pattern_analyzer.analyze_speaking_patterns(
                text, audio_duration, timestamps
            )
            
            # Content complexity analysis
            analysis_results['complexity'] = self.complexity_analyzer.analyze_complexity(text)
            
            # Bias detection
            analysis_results['bias'] = self.bias_detector.analyze_bias(text)
            
            # Plagiarism detection
            analysis_results['plagiarism'] = self.plagiarism_detector.analyze_plagiarism(
                text, reference_database
            )
            
            # Overall content score
            analysis_results['overall_score'] = self._calculate_overall_score(analysis_results)
            
        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
            analysis_results['error'] = str(e)
        
        return analysis_results
    
    def _calculate_overall_score(self, results: Dict[str, Any]) -> Dict[str, float]:
        """Calculate overall content quality scores"""
        scores = {}
        
        try:
            # Emotional engagement score
            emotion_intensity = results['emotions'].emotional_intensity
            scores['emotional_engagement'] = min(1.0, emotion_intensity * 2)
            
            # Communication clarity score
            complexity = results['complexity']
            clarity_score = 1.0 - (complexity.complexity_rating == 'advanced') * 0.3
            scores['communication_clarity'] = clarity_score
            
            # Inclusivity score
            scores['inclusivity'] = results['bias'].inclusive_language_score
            
            # Originality score
            scores['originality'] = results['plagiarism'].originality_score
            
            # Overall quality score (weighted average)
            weights = {'emotional_engagement': 0.2, 'communication_clarity': 0.3, 
                      'inclusivity': 0.3, 'originality': 0.2}
            
            overall = sum(scores[key] * weights[key] for key in weights)
            scores['overall_quality'] = overall
            
        except Exception as e:
            logger.error(f"Score calculation failed: {e}")
            scores = {'overall_quality': 0.5}
        
        return scores


# Global analyzer instance
advanced_content_analyzer = AdvancedContentAnalyzer()