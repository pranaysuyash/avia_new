"""
AI-Powered Content Insights Module
Provides intelligent analysis and insights for transcribed content
"""

import os
import re
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from collections import Counter, defaultdict
import statistics

import openai
from openai import OpenAI
import spacy
import numpy as np

from config import Config
from errors import APIError, NERError, ErrorCode

logger = logging.getLogger(__name__)


@dataclass
class ContentSentiment:
    """Sentiment analysis results"""
    overall_sentiment: str  # positive, negative, neutral
    confidence: float
    positive_score: float
    negative_score: float
    neutral_score: float
    emotions: Dict[str, float] = field(default_factory=dict)


@dataclass
class TopicInsight:
    """Topic analysis insight"""
    topic: str
    confidence: float
    keywords: List[str]
    description: str
    relevance_score: float


@dataclass
class ContentSummary:
    """Content summary with different lengths"""
    brief: str  # 1-2 sentences
    standard: str  # 1 paragraph
    detailed: str  # multiple paragraphs
    key_points: List[str]
    action_items: List[str] = field(default_factory=list)


@dataclass
class SpeakerInsight:
    """Insights about individual speakers"""
    speaker_id: str
    speaking_time: float
    word_count: int
    avg_speaking_pace: float  # words per minute
    sentiment: ContentSentiment
    key_topics: List[str]
    communication_style: str  # formal, casual, technical, etc.


@dataclass
class ContentInsights:
    """Complete content insights analysis"""
    transcript_id: str
    analyzed_at: datetime
    summary: ContentSummary
    sentiment: ContentSentiment
    topics: List[TopicInsight]
    speaker_insights: List[SpeakerInsight] = field(default_factory=list)
    key_moments: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'transcript_id': self.transcript_id,
            'analyzed_at': self.analyzed_at.isoformat(),
            'summary': {
                'brief': self.summary.brief,
                'standard': self.summary.standard,
                'detailed': self.summary.detailed,
                'key_points': self.summary.key_points,
                'action_items': self.summary.action_items
            },
            'sentiment': {
                'overall_sentiment': self.sentiment.overall_sentiment,
                'confidence': self.sentiment.confidence,
                'positive_score': self.sentiment.positive_score,
                'negative_score': self.sentiment.negative_score,
                'neutral_score': self.sentiment.neutral_score,
                'emotions': self.sentiment.emotions
            },
            'topics': [
                {
                    'topic': topic.topic,
                    'confidence': topic.confidence,
                    'keywords': topic.keywords,
                    'description': topic.description,
                    'relevance_score': topic.relevance_score
                }
                for topic in self.topics
            ],
            'speaker_insights': [
                {
                    'speaker_id': speaker.speaker_id,
                    'speaking_time': speaker.speaking_time,
                    'word_count': speaker.word_count,
                    'avg_speaking_pace': speaker.avg_speaking_pace,
                    'sentiment': {
                        'overall_sentiment': speaker.sentiment.overall_sentiment,
                        'confidence': speaker.sentiment.confidence,
                        'positive_score': speaker.sentiment.positive_score,
                        'negative_score': speaker.sentiment.negative_score,
                        'neutral_score': speaker.sentiment.neutral_score
                    },
                    'key_topics': speaker.key_topics,
                    'communication_style': speaker.communication_style
                }
                for speaker in self.speaker_insights
            ],
            'key_moments': self.key_moments,
            'metadata': self.metadata
        }


class ContentInsightsAnalyzer:
    """AI-powered content insights analyzer"""
    
    def __init__(self):
        self.client = None
        self.nlp = None
        
        # Initialize OpenAI client if API key is available
        if Config.OPENAI_API_KEY:
            self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Initialize spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy English model not found. Some features may be limited.")
    
    async def analyze_content(self, 
                            transcript: str,
                            transcript_id: str = None,
                            speaker_segments: List[Dict[str, Any]] = None,
                            metadata: Dict[str, Any] = None) -> ContentInsights:
        """
        Perform comprehensive content analysis
        
        Args:
            transcript: Full transcript text
            transcript_id: Unique identifier for the transcript
            speaker_segments: List of speaker segments with timing
            metadata: Additional context information
            
        Returns:
            ContentInsights: Complete analysis results
        """
        try:
            if not transcript or not transcript.strip():
                raise NERError(
                    message="Empty transcript provided for analysis",
                    error_code=ErrorCode.INVALID_INPUT,
                    user_message="Cannot analyze empty content."
                )
            
            logger.info(f"Starting content insights analysis for transcript: {transcript_id}")
            
            # Run analysis tasks concurrently where possible
            summary_task = self._generate_summary(transcript)
            sentiment_task = self._analyze_sentiment(transcript)
            topics_task = self._extract_topics(transcript)
            
            # Await core analysis tasks
            summary = await summary_task
            sentiment = await sentiment_task
            topics = await topics_task
            
            # Analyze speakers if segments provided
            speaker_insights = []
            if speaker_segments:
                speaker_insights = await self._analyze_speakers(speaker_segments, transcript)
            
            # Find key moments
            key_moments = await self._identify_key_moments(transcript, speaker_segments)
            
            # Create insights object
            insights = ContentInsights(
                transcript_id=transcript_id or f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                analyzed_at=datetime.now(),
                summary=summary,
                sentiment=sentiment,
                topics=topics,
                speaker_insights=speaker_insights,
                key_moments=key_moments,
                metadata=metadata or {}
            )
            
            logger.info(f"Content insights analysis completed for transcript: {transcript_id}")
            return insights
            
        except Exception as e:
            logger.error(f"Content insights analysis failed: {str(e)}")
            if isinstance(e, (APIError, NERError)):
                raise
            raise NERError(
                message=f"Content analysis failed: {str(e)}",
                error_code=ErrorCode.PROCESSING_ERROR,
                user_message="Failed to analyze content insights."
            )
    
    async def _generate_summary(self, transcript: str) -> ContentSummary:
        """Generate multi-level content summaries"""
        if not self.client:
            # Fallback to basic extractive summarization
            return self._generate_extractive_summary(transcript)
        
        try:
            # Generate different summary lengths using GPT
            prompts = {
                'brief': f"Summarize this transcript in 1-2 sentences:\n\n{transcript}",
                'standard': f"Summarize this transcript in one paragraph:\n\n{transcript}",
                'detailed': f"Provide a detailed summary of this transcript with key insights:\n\n{transcript}",
                'key_points': f"Extract the main key points from this transcript as a bulleted list:\n\n{transcript}",
                'action_items': f"Identify any action items, decisions, or next steps mentioned in this transcript:\n\n{transcript}"
            }
            
            # Run summary generation tasks
            results = {}
            for summary_type, prompt in prompts.items():
                response = await self._call_openai_async(prompt, max_tokens=500 if summary_type == 'detailed' else 200)
                results[summary_type] = response.strip()
            
            # Parse key points and action items into lists
            key_points = self._parse_bulleted_list(results['key_points'])
            action_items = self._parse_bulleted_list(results['action_items'])
            
            return ContentSummary(
                brief=results['brief'],
                standard=results['standard'],
                detailed=results['detailed'],
                key_points=key_points,
                action_items=action_items
            )
            
        except Exception as e:
            logger.warning(f"AI summary generation failed: {str(e)}, falling back to extractive summary")
            return self._generate_extractive_summary(transcript)
    
    async def _analyze_sentiment(self, transcript: str) -> ContentSentiment:
        """Analyze sentiment and emotions in the content"""
        if not self.client:
            return self._analyze_basic_sentiment(transcript)
        
        try:
            prompt = f"""Analyze the sentiment and emotions in this transcript. 
            Provide scores from 0-1 for positive, negative, and neutral sentiment.
            Also identify specific emotions present (joy, anger, fear, sadness, surprise, etc.) with confidence scores.
            
            Transcript: {transcript}
            
            Respond in JSON format:
            {{
                "overall_sentiment": "positive/negative/neutral",
                "confidence": 0.85,
                "positive_score": 0.7,
                "negative_score": 0.1,
                "neutral_score": 0.2,
                "emotions": {{
                    "joy": 0.6,
                    "excitement": 0.4
                }}
            }}"""
            
            response = await self._call_openai_async(prompt, max_tokens=300)
            
            try:
                sentiment_data = json.loads(response)
                return ContentSentiment(**sentiment_data)
            except json.JSONDecodeError:
                logger.warning("Failed to parse sentiment JSON, using basic analysis")
                return self._analyze_basic_sentiment(transcript)
                
        except Exception as e:
            logger.warning(f"AI sentiment analysis failed: {str(e)}, using basic analysis")
            return self._analyze_basic_sentiment(transcript)
    
    async def _extract_topics(self, transcript: str) -> List[TopicInsight]:
        """Extract and analyze topics in the content"""
        if not self.client:
            return self._extract_basic_topics(transcript)
        
        try:
            prompt = f"""Analyze this transcript and identify the main topics discussed.
            For each topic, provide keywords, description, and relevance score.
            
            Transcript: {transcript}
            
            Respond in JSON format with up to 5 topics:
            {{
                "topics": [
                    {{
                        "topic": "Project Planning",
                        "confidence": 0.9,
                        "keywords": ["planning", "timeline", "milestones"],
                        "description": "Discussion about project planning and timelines",
                        "relevance_score": 0.8
                    }}
                ]
            }}"""
            
            response = await self._call_openai_async(prompt, max_tokens=500)
            
            try:
                topics_data = json.loads(response)
                return [TopicInsight(**topic) for topic in topics_data['topics']]
            except (json.JSONDecodeError, KeyError):
                logger.warning("Failed to parse topics JSON, using basic extraction")
                return self._extract_basic_topics(transcript)
                
        except Exception as e:
            logger.warning(f"AI topic extraction failed: {str(e)}, using basic extraction")
            return self._extract_basic_topics(transcript)
    
    async def _analyze_speakers(self, 
                               speaker_segments: List[Dict[str, Any]], 
                               full_transcript: str) -> List[SpeakerInsight]:
        """Analyze individual speaker characteristics"""
        speaker_insights = []
        
        # Group segments by speaker
        speaker_data = defaultdict(list)
        for segment in speaker_segments:
            speaker_id = segment.get('speaker_id', 'unknown')
            speaker_data[speaker_id].append(segment)
        
        for speaker_id, segments in speaker_data.items():
            # Calculate speaking metrics
            total_time = sum(seg.get('duration', 0) for seg in segments)
            speaker_text = ' '.join(seg.get('text', '') for seg in segments)
            word_count = len(speaker_text.split())
            
            avg_pace = (word_count / (total_time / 60)) if total_time > 0 else 0
            
            # Analyze speaker's sentiment
            speaker_sentiment = await self._analyze_sentiment(speaker_text)
            
            # Extract speaker's key topics
            speaker_topics = await self._extract_topics(speaker_text)
            key_topic_names = [topic.topic for topic in speaker_topics[:3]]
            
            # Determine communication style
            communication_style = self._determine_communication_style(speaker_text)
            
            insight = SpeakerInsight(
                speaker_id=speaker_id,
                speaking_time=total_time,
                word_count=word_count,
                avg_speaking_pace=avg_pace,
                sentiment=speaker_sentiment,
                key_topics=key_topic_names,
                communication_style=communication_style
            )
            
            speaker_insights.append(insight)
        
        return speaker_insights
    
    async def _identify_key_moments(self, 
                                   transcript: str,
                                   speaker_segments: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Identify key moments and highlights in the content"""
        key_moments = []
        
        if not self.client:
            return self._identify_basic_key_moments(transcript, speaker_segments)
        
        try:
            prompt = f"""Identify key moments, important decisions, or highlights from this transcript.
            Include timestamp if available and explain why each moment is significant.
            
            Transcript: {transcript}
            
            Respond in JSON format:
            {{
                "key_moments": [
                    {{
                        "timestamp": 120.5,
                        "description": "Key decision made about project direction",
                        "significance": "Critical turning point in discussion",
                        "type": "decision"
                    }}
                ]
            }}"""
            
            response = await self._call_openai_async(prompt, max_tokens=400)
            
            try:
                moments_data = json.loads(response)
                return moments_data.get('key_moments', [])
            except json.JSONDecodeError:
                return self._identify_basic_key_moments(transcript, speaker_segments)
                
        except Exception as e:
            logger.warning(f"AI key moments identification failed: {str(e)}")
            return self._identify_basic_key_moments(transcript, speaker_segments)
    
    async def _call_openai_async(self, prompt: str, max_tokens: int = 200) -> str:
        """Make async call to OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI assistant specialized in content analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.3
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise APIError(
                message=f"OpenAI API error: {str(e)}",
                error_code=ErrorCode.API_ERROR,
                user_message="AI analysis service is currently unavailable."
            )
    
    def _generate_extractive_summary(self, transcript: str) -> ContentSummary:
        """Generate basic extractive summary without AI"""
        sentences = re.split(r'[.!?]+', transcript)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Simple extractive summary - take first and most "important" sentences
        brief = sentences[0] if sentences else ""
        standard = '. '.join(sentences[:3]) + '.' if len(sentences) >= 3 else brief
        detailed = '. '.join(sentences[:5]) + '.' if len(sentences) >= 5 else standard
        
        # Extract basic key points
        key_points = []
        for sentence in sentences[:5]:
            if any(word in sentence.lower() for word in ['important', 'key', 'main', 'significant']):
                key_points.append(sentence.strip())
        
        return ContentSummary(
            brief=brief,
            standard=standard,
            detailed=detailed,
            key_points=key_points[:3],
            action_items=[]
        )
    
    def _analyze_basic_sentiment(self, transcript: str) -> ContentSentiment:
        """Basic sentiment analysis without AI"""
        positive_words = ['good', 'great', 'excellent', 'positive', 'happy', 'success', 'achieve']
        negative_words = ['bad', 'terrible', 'negative', 'sad', 'fail', 'problem', 'issue']
        
        words = transcript.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            return ContentSentiment(
                overall_sentiment="neutral",
                confidence=0.5,
                positive_score=0.33,
                negative_score=0.33,
                neutral_score=0.34
            )
        
        positive_score = positive_count / len(words)
        negative_score = negative_count / len(words)
        neutral_score = 1 - (positive_score + negative_score)
        
        overall = "positive" if positive_count > negative_count else "negative" if negative_count > positive_count else "neutral"
        confidence = abs(positive_count - negative_count) / total_sentiment_words if total_sentiment_words > 0 else 0.5
        
        return ContentSentiment(
            overall_sentiment=overall,
            confidence=confidence,
            positive_score=positive_score,
            negative_score=negative_score,
            neutral_score=neutral_score
        )
    
    def _extract_basic_topics(self, transcript: str) -> List[TopicInsight]:
        """Basic topic extraction without AI"""
        if not self.nlp:
            return []
        
        doc = self.nlp(transcript)
        
        # Extract noun phrases as potential topics
        noun_phrases = [chunk.text.lower() for chunk in doc.noun_chunks if len(chunk.text.split()) <= 3]
        topic_counts = Counter(noun_phrases)
        
        topics = []
        for phrase, count in topic_counts.most_common(5):
            if count > 1:  # Only include topics mentioned more than once
                topics.append(TopicInsight(
                    topic=phrase.title(),
                    confidence=min(count / 10, 1.0),
                    keywords=[phrase],
                    description=f"Topic mentioned {count} times",
                    relevance_score=count / len(noun_phrases)
                ))
        
        return topics
    
    def _determine_communication_style(self, speaker_text: str) -> str:
        """Determine speaker's communication style"""
        formal_indicators = ['furthermore', 'however', 'therefore', 'consequently']
        casual_indicators = ['yeah', 'okay', 'like', 'you know']
        technical_indicators = ['system', 'process', 'implementation', 'analysis']
        
        text_lower = speaker_text.lower()
        
        formal_count = sum(1 for word in formal_indicators if word in text_lower)
        casual_count = sum(1 for word in casual_indicators if word in text_lower)
        technical_count = sum(1 for word in technical_indicators if word in text_lower)
        
        if technical_count > max(formal_count, casual_count):
            return "technical"
        elif formal_count > casual_count:
            return "formal"
        elif casual_count > formal_count:
            return "casual"
        else:
            return "neutral"
    
    def _identify_basic_key_moments(self, 
                                   transcript: str,
                                   speaker_segments: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Identify basic key moments without AI"""
        key_moments = []
        
        # Look for decision indicators
        decision_patterns = [
            r'(decided|decision|conclude|final|agreed)',
            r'(action item|next step|follow up)',
            r'(important|critical|significant|key)'
        ]
        
        sentences = re.split(r'[.!?]+', transcript)
        
        for i, sentence in enumerate(sentences):
            for pattern in decision_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    key_moments.append({
                        'description': sentence.strip(),
                        'significance': 'Contains decision or important information',
                        'type': 'highlight',
                        'sentence_index': i
                    })
                    break
        
        return key_moments[:5]  # Limit to 5 key moments
    
    def _parse_bulleted_list(self, text: str) -> List[str]:
        """Parse bulleted list from text"""
        lines = text.split('\n')
        items = []
        
        for line in lines:
            line = line.strip()
            # Remove bullet points and numbering
            line = re.sub(r'^[-•*]\s*', '', line)
            line = re.sub(r'^\d+\.\s*', '', line)
            
            if line and len(line) > 5:  # Only include substantial items
                items.append(line)
        
        return items[:10]  # Limit to 10 items