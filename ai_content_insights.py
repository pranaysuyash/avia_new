#!/usr/bin/env python3
"""
AI-Powered Content Insights Module
Implements Task 31: AI-powered content insights

This module provides advanced AI-powered analysis of transcribed content including:
- Automatic meeting minutes generation
- Action item extraction and task identification
- Sentiment analysis timeline
- Topic clustering and content categorization
- Automatic summary generation with key highlights
"""

import os
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import openai
import spacy
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import LatentDirichletAllocation
import numpy as np
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)

# Load spaCy model for NLP processing
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
    nlp = None


class ContentType(Enum):
    """Types of content for analysis"""
    MEETING = "meeting"
    INTERVIEW = "interview"
    LECTURE = "lecture"
    PRESENTATION = "presentation"
    CONVERSATION = "conversation"
    PODCAST = "podcast"


class SentimentType(Enum):
    """Sentiment classification types"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class ActionItemPriority(Enum):
    """Priority levels for action items"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ActionItem:
    """Represents an extracted action item"""
    id: str
    text: str
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    priority: ActionItemPriority = ActionItemPriority.MEDIUM
    context: str = ""
    timestamp: float = 0.0
    confidence: float = 0.0
    status: str = "pending"


@dataclass
class SentimentPoint:
    """Represents a sentiment analysis point in time"""
    timestamp: float
    sentiment: SentimentType
    score: float  # -1 to 1 scale
    confidence: float
    text_segment: str
    keywords: List[str] = field(default_factory=list)


@dataclass
class TopicCluster:
    """Represents a topic cluster"""
    id: str
    name: str
    keywords: List[str]
    segments: List[str]
    timestamps: List[float]
    confidence: float
    summary: str = ""


@dataclass
class MeetingMinutes:
    """Structured meeting minutes"""
    title: str
    date: str
    duration: float
    participants: List[str]
    agenda_items: List[str]
    key_decisions: List[str]
    action_items: List[ActionItem]
    next_steps: List[str]
    summary: str
    topics_discussed: List[str]


@dataclass
class ContentSummary:
    """Comprehensive content summary"""
    executive_summary: str
    key_points: List[str]
    main_topics: List[str]
    sentiment_overview: str
    duration: float
    word_count: int
    speaker_insights: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0


class AIContentInsights:
    """Main class for AI-powered content analysis"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the AI Content Insights analyzer"""
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        
        # Initialize ML models
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        # Action item detection patterns
        self.action_patterns = [
            r'\b(?:will|should|must|need to|have to|going to)\s+([^.!?]+)',
            r'\b(?:action item|todo|task|assignment):\s*([^.!?]+)',
            r'\b(?:follow up|follow-up)\s+(?:on|with)\s+([^.!?]+)',
            r'\b(?:by|before|due)\s+(?:next week|tomorrow|friday|monday)\s*([^.!?]*)',
            r'\b([A-Z][a-z]+)\s+(?:will|should|needs to)\s+([^.!?]+)',
        ]
        
        # Meeting-specific patterns
        self.meeting_patterns = {
            'decisions': [
                r'\b(?:decided|agreed|concluded|resolved)\s+(?:that|to)\s+([^.!?]+)',
                r'\b(?:decision|agreement|resolution):\s*([^.!?]+)',
            ],
            'next_steps': [
                r'\b(?:next steps?|moving forward|going forward):\s*([^.!?]+)',
                r'\b(?:next|following)\s+(?:meeting|session|call)\s+([^.!?]+)',
            ]
        }
    
    def analyze_content(self, 
                       transcript_data: Dict[str, Any],
                       content_type: ContentType = ContentType.MEETING,
                       speaker_info: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Perform comprehensive AI-powered content analysis
        
        Args:
            transcript_data: Transcript with segments and timing
            content_type: Type of content being analyzed
            speaker_info: Optional speaker identification mapping
            
        Returns:
            Dictionary containing all analysis results
        """
        try:
            logger.info(f"Starting AI content analysis for {content_type.value}")
            
            # Extract text and segments
            segments = transcript_data.get('segments', [])
            full_text = self._extract_full_text(segments)
            
            if not full_text.strip():
                raise ValueError("No text content found in transcript")
            
            # Perform all analyses
            results = {
                'content_type': content_type.value,
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'transcript_stats': self._calculate_transcript_stats(segments),
            }
            
            # Generate summary
            logger.info("Generating content summary...")
            results['summary'] = self._generate_summary(full_text, segments)
            
            # Extract action items
            logger.info("Extracting action items...")
            results['action_items'] = self._extract_action_items(segments, speaker_info)
            
            # Perform sentiment analysis
            logger.info("Analyzing sentiment timeline...")
            results['sentiment_analysis'] = self._analyze_sentiment_timeline(segments)
            
            # Topic clustering
            logger.info("Performing topic clustering...")
            results['topic_clusters'] = self._perform_topic_clustering(segments)
            
            # Generate meeting minutes (if applicable)
            if content_type == ContentType.MEETING:
                logger.info("Generating meeting minutes...")
                results['meeting_minutes'] = self._generate_meeting_minutes(
                    segments, results, speaker_info
                )
            
            # Content categorization
            logger.info("Categorizing content...")
            results['content_categories'] = self._categorize_content(full_text)
            
            # Key insights
            logger.info("Extracting key insights...")
            results['key_insights'] = self._extract_key_insights(results)
            
            logger.info("AI content analysis completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Error in AI content analysis: {e}")
            raise
    
    def _extract_full_text(self, segments: List[Dict[str, Any]]) -> str:
        """Extract full text from transcript segments"""
        return ' '.join([segment.get('text', '').strip() for segment in segments])
    
    def _calculate_transcript_stats(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate basic statistics about the transcript"""
        full_text = self._extract_full_text(segments)
        
        return {
            'total_segments': len(segments),
            'total_duration': segments[-1].get('end', 0) if segments else 0,
            'word_count': len(full_text.split()),
            'character_count': len(full_text),
            'average_segment_length': len(full_text.split()) / len(segments) if segments else 0,
            'speaking_rate': len(full_text.split()) / (segments[-1].get('end', 1) / 60) if segments else 0  # words per minute
        }
    
    def _generate_summary(self, full_text: str, segments: List[Dict[str, Any]]) -> ContentSummary:
        """Generate comprehensive content summary using AI"""
        try:
            # Use OpenAI for advanced summarization
            if self.openai_api_key:
                from openai import OpenAI
                client = OpenAI(api_key=self.openai_api_key)
                
                summary_response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert at analyzing and summarizing meeting transcripts and conversations. Provide clear, actionable summaries."
                        },
                        {
                            "role": "user",
                            "content": f"""
                            Please analyze this transcript and provide:
                            1. A concise executive summary (2-3 sentences)
                            2. 5-7 key points discussed
                            3. Main topics covered
                            4. Overall sentiment assessment
                            
                            Transcript:
                            {full_text[:4000]}  # Limit for API
                            """
                        }
                    ],
                    max_tokens=500,
                    temperature=0.3
                )
                
                ai_summary = summary_response.choices[0].message.content
                
                # Parse AI response
                lines = ai_summary.split('\n')
                executive_summary = ""
                key_points = []
                main_topics = []
                sentiment_overview = "neutral"
                
                current_section = None
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    if "executive summary" in line.lower():
                        current_section = "summary"
                    elif "key points" in line.lower():
                        current_section = "points"
                    elif "main topics" in line.lower() or "topics" in line.lower():
                        current_section = "topics"
                    elif "sentiment" in line.lower():
                        current_section = "sentiment"
                    elif line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '-', '•')):
                        if current_section == "points":
                            key_points.append(line.lstrip('1234567890.-• '))
                        elif current_section == "topics":
                            main_topics.append(line.lstrip('1234567890.-• '))
                    elif current_section == "summary" and not line.startswith(('1.', '2.', '3.')):
                        executive_summary += line + " "
                    elif current_section == "sentiment":
                        sentiment_overview = line.lower()
                
            else:
                # Fallback to basic summarization
                sentences = full_text.split('.')
                executive_summary = '. '.join(sentences[:3]) + '.'
                key_points = sentences[3:8] if len(sentences) > 3 else sentences
                main_topics = self._extract_basic_topics(full_text)
                sentiment_overview = "neutral"
            
            # Calculate additional metrics
            stats = self._calculate_transcript_stats(segments)
            
            return ContentSummary(
                executive_summary=executive_summary.strip(),
                key_points=key_points,
                main_topics=main_topics,
                sentiment_overview=sentiment_overview,
                duration=stats['total_duration'],
                word_count=stats['word_count'],
                confidence_score=0.8 if self.openai_api_key else 0.6
            )
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            # Return basic summary as fallback
            return ContentSummary(
                executive_summary="Summary generation failed",
                key_points=[],
                main_topics=[],
                sentiment_overview="neutral",
                duration=0,
                word_count=len(full_text.split()),
                confidence_score=0.0
            )
    
    def _extract_action_items(self, 
                            segments: List[Dict[str, Any]], 
                            speaker_info: Optional[Dict[str, str]] = None) -> List[ActionItem]:
        """Extract action items from transcript segments"""
        action_items = []
        
        try:
            for i, segment in enumerate(segments):
                text = segment.get('text', '').strip()
                timestamp = segment.get('start', 0)
                speaker = segment.get('speaker', 'Unknown')
                
                # Apply action item patterns
                for pattern in self.action_patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        action_text = match.group(1).strip()
                        if len(action_text) > 10:  # Filter out very short matches
                            
                            # Determine assignee
                            assignee = self._extract_assignee(text, speaker_info)
                            
                            # Determine priority
                            priority = self._determine_priority(text)
                            
                            # Extract due date
                            due_date = self._extract_due_date(text)
                            
                            action_item = ActionItem(
                                id=f"action_{len(action_items) + 1}",
                                text=action_text,
                                assignee=assignee,
                                due_date=due_date,
                                priority=priority,
                                context=text,
                                timestamp=timestamp,
                                confidence=self._calculate_action_confidence(text, action_text)
                            )
                            
                            action_items.append(action_item)
            
            # Remove duplicates and low-confidence items
            action_items = self._deduplicate_action_items(action_items)
            action_items = [item for item in action_items if item.confidence > 0.3]
            
            logger.info(f"Extracted {len(action_items)} action items")
            return action_items
            
        except Exception as e:
            logger.error(f"Error extracting action items: {e}")
            return []
    
    def _analyze_sentiment_timeline(self, segments: List[Dict[str, Any]]) -> List[SentimentPoint]:
        """Analyze sentiment changes over time"""
        sentiment_points = []
        
        try:
            for segment in segments:
                text = segment.get('text', '').strip()
                timestamp = segment.get('start', 0)
                
                if not text:
                    continue
                
                # Use TextBlob for sentiment analysis
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity  # -1 to 1
                subjectivity = blob.sentiment.subjectivity  # 0 to 1
                
                # Classify sentiment
                if polarity > 0.1:
                    sentiment = SentimentType.POSITIVE
                elif polarity < -0.1:
                    sentiment = SentimentType.NEGATIVE
                else:
                    sentiment = SentimentType.NEUTRAL
                
                # Extract keywords for this segment
                keywords = self._extract_segment_keywords(text)
                
                sentiment_point = SentimentPoint(
                    timestamp=timestamp,
                    sentiment=sentiment,
                    score=polarity,
                    confidence=abs(polarity) * (1 - subjectivity),  # Higher confidence for objective statements
                    text_segment=text[:100] + "..." if len(text) > 100 else text,
                    keywords=keywords
                )
                
                sentiment_points.append(sentiment_point)
            
            logger.info(f"Analyzed sentiment for {len(sentiment_points)} segments")
            return sentiment_points
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return []
    
    def _perform_topic_clustering(self, segments: List[Dict[str, Any]]) -> List[TopicCluster]:
        """Perform topic clustering on transcript segments"""
        try:
            if not segments:
                return []
            
            # Prepare text data
            texts = [segment.get('text', '').strip() for segment in segments if segment.get('text', '').strip()]
            timestamps = [segment.get('start', 0) for segment in segments if segment.get('text', '').strip()]
            
            if len(texts) < 3:  # Need minimum segments for clustering
                return []
            
            # Vectorize text
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            
            # Determine optimal number of clusters (max 5)
            n_clusters = min(5, max(2, len(texts) // 3))
            
            # Perform K-means clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(tfidf_matrix)
            
            # Extract topics using LDA
            lda = LatentDirichletAllocation(n_components=n_clusters, random_state=42)
            lda.fit(tfidf_matrix)
            
            # Build topic clusters
            clusters = []
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            
            for cluster_id in range(n_clusters):
                # Get segments in this cluster
                cluster_segments = [texts[i] for i, label in enumerate(cluster_labels) if label == cluster_id]
                cluster_timestamps = [timestamps[i] for i, label in enumerate(cluster_labels) if label == cluster_id]
                
                if not cluster_segments:
                    continue
                
                # Get top keywords for this topic
                topic_words = lda.components_[cluster_id]
                top_indices = topic_words.argsort()[-10:][::-1]
                keywords = [feature_names[i] for i in top_indices]
                
                # Generate topic name
                topic_name = self._generate_topic_name(keywords, cluster_segments)
                
                # Calculate confidence
                confidence = float(np.mean([topic_words[i] for i in top_indices[:5]]))
                
                # Generate summary
                summary = self._generate_cluster_summary(cluster_segments)
                
                cluster = TopicCluster(
                    id=f"topic_{cluster_id + 1}",
                    name=topic_name,
                    keywords=keywords[:5],
                    segments=cluster_segments,
                    timestamps=cluster_timestamps,
                    confidence=confidence,
                    summary=summary
                )
                
                clusters.append(cluster)
            
            # Sort by confidence
            clusters.sort(key=lambda x: x.confidence, reverse=True)
            
            logger.info(f"Generated {len(clusters)} topic clusters")
            return clusters
            
        except Exception as e:
            logger.error(f"Error performing topic clustering: {e}")
            return []    

    def _generate_meeting_minutes(self, 
                                segments: List[Dict[str, Any]], 
                                analysis_results: Dict[str, Any],
                                speaker_info: Optional[Dict[str, str]] = None) -> MeetingMinutes:
        """Generate structured meeting minutes"""
        try:
            full_text = self._extract_full_text(segments)
            
            # Extract participants
            participants = self._extract_participants(segments, speaker_info)
            
            # Extract agenda items
            agenda_items = self._extract_agenda_items(segments)
            
            # Extract key decisions
            key_decisions = self._extract_decisions(segments)
            
            # Get action items from analysis
            action_items = analysis_results.get('action_items', [])
            
            # Extract next steps
            next_steps = self._extract_next_steps(segments)
            
            # Get summary
            summary = analysis_results.get('summary', {})
            executive_summary = summary.get('executive_summary', '') if isinstance(summary, dict) else str(summary)
            
            # Get topics
            topics_discussed = []
            if 'topic_clusters' in analysis_results:
                topics_discussed = [cluster['name'] for cluster in analysis_results['topic_clusters']]
            
            # Generate title
            title = self._generate_meeting_title(full_text, topics_discussed)
            
            # Calculate duration
            duration = segments[-1].get('end', 0) if segments else 0
            
            return MeetingMinutes(
                title=title,
                date=datetime.now().strftime("%Y-%m-%d"),
                duration=duration,
                participants=participants,
                agenda_items=agenda_items,
                key_decisions=key_decisions,
                action_items=action_items,
                next_steps=next_steps,
                summary=executive_summary,
                topics_discussed=topics_discussed
            )
            
        except Exception as e:
            logger.error(f"Error generating meeting minutes: {e}")
            return MeetingMinutes(
                title="Meeting Minutes",
                date=datetime.now().strftime("%Y-%m-%d"),
                duration=0,
                participants=[],
                agenda_items=[],
                key_decisions=[],
                action_items=[],
                next_steps=[],
                summary="",
                topics_discussed=[]
            )
    
    def _categorize_content(self, full_text: str) -> Dict[str, Any]:
        """Categorize content by type and themes"""
        try:
            categories = {
                'content_themes': [],
                'discussion_type': 'general',
                'formality_level': 'medium',
                'technical_level': 'medium',
                'emotional_tone': 'neutral'
            }
            
            # Theme detection patterns
            theme_patterns = {
                'planning': r'\b(?:plan|planning|strategy|roadmap|timeline|schedule)\b',
                'decision_making': r'\b(?:decide|decision|choose|select|approve|reject)\b',
                'problem_solving': r'\b(?:problem|issue|challenge|solution|resolve|fix)\b',
                'brainstorming': r'\b(?:idea|brainstorm|creative|innovative|think|suggest)\b',
                'review': r'\b(?:review|evaluate|assess|analyze|examine|check)\b',
                'update': r'\b(?:update|status|progress|report|inform|share)\b',
                'training': r'\b(?:learn|teach|train|educate|explain|demonstrate)\b',
                'negotiation': r'\b(?:negotiate|deal|agreement|terms|contract|compromise)\b'
            }
            
            # Count theme occurrences
            theme_counts = {}
            for theme, pattern in theme_patterns.items():
                matches = len(re.findall(pattern, full_text, re.IGNORECASE))
                if matches > 0:
                    theme_counts[theme] = matches
            
            # Get top themes
            if theme_counts:
                sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)
                categories['content_themes'] = [theme for theme, count in sorted_themes[:3]]
            
            # Determine discussion type
            if any(word in full_text.lower() for word in ['meeting', 'agenda', 'minutes']):
                categories['discussion_type'] = 'meeting'
            elif any(word in full_text.lower() for word in ['interview', 'question', 'answer']):
                categories['discussion_type'] = 'interview'
            elif any(word in full_text.lower() for word in ['presentation', 'slide', 'demo']):
                categories['discussion_type'] = 'presentation'
            elif any(word in full_text.lower() for word in ['lecture', 'class', 'lesson']):
                categories['discussion_type'] = 'lecture'
            
            # Assess formality level
            formal_indicators = len(re.findall(r'\b(?:shall|furthermore|therefore|consequently|moreover)\b', full_text, re.IGNORECASE))
            informal_indicators = len(re.findall(r'\b(?:yeah|okay|um|uh|like|you know)\b', full_text, re.IGNORECASE))
            
            if formal_indicators > informal_indicators * 2:
                categories['formality_level'] = 'high'
            elif informal_indicators > formal_indicators * 2:
                categories['formality_level'] = 'low'
            
            # Assess technical level
            technical_terms = len(re.findall(r'\b(?:API|database|algorithm|framework|implementation|architecture|deployment)\b', full_text, re.IGNORECASE))
            total_words = len(full_text.split())
            
            if total_words > 0:
                technical_ratio = technical_terms / total_words
                if technical_ratio > 0.05:
                    categories['technical_level'] = 'high'
                elif technical_ratio < 0.01:
                    categories['technical_level'] = 'low'
            
            return categories
            
        except Exception as e:
            logger.error(f"Error categorizing content: {e}")
            return {
                'content_themes': [],
                'discussion_type': 'general',
                'formality_level': 'medium',
                'technical_level': 'medium',
                'emotional_tone': 'neutral'
            }
    
    def _extract_key_insights(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key insights from all analysis results"""
        try:
            insights = {
                'summary_insights': [],
                'action_insights': [],
                'sentiment_insights': [],
                'topic_insights': [],
                'overall_assessment': {}
            }
            
            # Summary insights
            summary = analysis_results.get('summary', {})
            if isinstance(summary, dict):
                if summary.get('key_points'):
                    insights['summary_insights'] = [
                        f"Discussion covered {len(summary['key_points'])} main points",
                        f"Content duration: {summary.get('duration', 0):.1f} minutes",
                        f"Word count: {summary.get('word_count', 0)} words"
                    ]
            
            # Action item insights
            action_items = analysis_results.get('action_items', [])
            if action_items:
                high_priority = len([item for item in action_items if item.get('priority') == 'high'])
                insights['action_insights'] = [
                    f"Total action items identified: {len(action_items)}",
                    f"High priority items: {high_priority}",
                    f"Items with assigned owners: {len([item for item in action_items if item.get('assignee')])}"
                ]
            
            # Sentiment insights
            sentiment_data = analysis_results.get('sentiment_analysis', [])
            if sentiment_data:
                positive_count = len([s for s in sentiment_data if s.get('sentiment') == 'positive'])
                negative_count = len([s for s in sentiment_data if s.get('sentiment') == 'negative'])
                neutral_count = len(sentiment_data) - positive_count - negative_count
                
                insights['sentiment_insights'] = [
                    f"Overall sentiment distribution: {positive_count} positive, {neutral_count} neutral, {negative_count} negative",
                    f"Sentiment trend: {'Positive' if positive_count > negative_count else 'Negative' if negative_count > positive_count else 'Balanced'}"
                ]
            
            # Topic insights
            topics = analysis_results.get('topic_clusters', [])
            if topics:
                insights['topic_insights'] = [
                    f"Main topics identified: {len(topics)}",
                    f"Primary topic: {topics[0].get('name', 'Unknown') if topics else 'None'}",
                    f"Topic coverage: {', '.join([t.get('name', '') for t in topics[:3]])}"
                ]
            
            # Overall assessment
            stats = analysis_results.get('transcript_stats', {})
            insights['overall_assessment'] = {
                'engagement_level': self._assess_engagement(stats, sentiment_data),
                'content_density': self._assess_content_density(stats),
                'action_orientation': self._assess_action_orientation(action_items, stats),
                'discussion_quality': self._assess_discussion_quality(analysis_results)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error extracting key insights: {e}")
            return {
                'summary_insights': [],
                'action_insights': [],
                'sentiment_insights': [],
                'topic_insights': [],
                'overall_assessment': {}
            }
    
    # Helper methods
    def _extract_assignee(self, text: str, speaker_info: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Extract assignee from action item text"""
        # Look for name patterns
        name_patterns = [
            r'\b([A-Z][a-z]+)\s+(?:will|should|needs to)\b',
            r'\b(?:assign|assigned to|give to)\s+([A-Z][a-z]+)\b',
            r'\b([A-Z][a-z]+),?\s+(?:you|please)\b'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def _determine_priority(self, text: str) -> ActionItemPriority:
        """Determine priority level from text context"""
        high_priority_words = ['urgent', 'asap', 'immediately', 'critical', 'important', 'priority']
        low_priority_words = ['eventually', 'sometime', 'when possible', 'nice to have']
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in high_priority_words):
            return ActionItemPriority.HIGH
        elif any(word in text_lower for word in low_priority_words):
            return ActionItemPriority.LOW
        else:
            return ActionItemPriority.MEDIUM
    
    def _extract_due_date(self, text: str) -> Optional[str]:
        """Extract due date from text"""
        date_patterns = [
            r'\b(?:by|before|due)\s+(next week|this week|tomorrow|friday|monday|tuesday|wednesday|thursday|saturday|sunday)\b',
            r'\b(?:by|before|due)\s+(\d{1,2}/\d{1,2})\b',
            r'\b(?:by|before|due)\s+(end of week|end of month)\b'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _calculate_action_confidence(self, full_text: str, action_text: str) -> float:
        """Calculate confidence score for action item"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence for explicit action words
        action_words = ['will', 'should', 'must', 'need to', 'action item', 'todo']
        if any(word in full_text.lower() for word in action_words):
            confidence += 0.2
        
        # Increase confidence for specific assignee
        if re.search(r'\b[A-Z][a-z]+\s+(?:will|should)\b', full_text):
            confidence += 0.2
        
        # Increase confidence for due dates
        if re.search(r'\b(?:by|before|due)\s+\w+', full_text, re.IGNORECASE):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _extract_assignee(self, text: str, speaker_info: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Extract assignee from action item text"""
        # Look for name patterns
        name_patterns = [
            r'\b([A-Z][a-z]+),?\s+(?:will|should|can|needs to)',
            r'(?:assigned to|assign to|give to)\s+([A-Z][a-z]+)',
            r'\b([A-Z][a-z]+)\s+(?:will|should)\s+(?:work on|handle|do|complete)',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def _determine_priority(self, text: str) -> ActionItemPriority:
        """Determine priority level from text context"""
        high_priority_words = ['urgent', 'asap', 'immediately', 'critical', 'important', 'priority']
        low_priority_words = ['eventually', 'when possible', 'nice to have', 'optional', 'later']
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in high_priority_words):
            return ActionItemPriority.HIGH
        elif any(word in text_lower for word in low_priority_words):
            return ActionItemPriority.LOW
        else:
            return ActionItemPriority.MEDIUM
    
    def _extract_due_date(self, text: str) -> Optional[str]:
        """Extract due date from text"""
        date_patterns = [
            r'by\s+(next\s+week|this\s+week|tomorrow|today)',
            r'by\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'due\s+(next\s+week|this\s+week|tomorrow|today)',
            r'before\s+(next\s+week|this\s+week|tomorrow|today)',
            r'by\s+(\d{1,2}/\d{1,2})',
            r'due\s+(\d{1,2}/\d{1,2})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _calculate_action_confidence(self, full_text: str, action_text: str) -> float:
        """Calculate confidence score for action item"""
        confidence = 0.5  # Base confidence
        
        # Higher confidence for specific assignees
        if re.search(r'\b[A-Z][a-z]+\s+(?:will|should)', full_text):
            confidence += 0.2
        
        # Higher confidence for specific timeframes
        if re.search(r'by\s+\w+', full_text, re.IGNORECASE):
            confidence += 0.15
        
        # Higher confidence for action verbs
        action_verbs = ['complete', 'finish', 'implement', 'create', 'develop', 'fix', 'resolve']
        if any(verb in action_text.lower() for verb in action_verbs):
            confidence += 0.1
        
        # Lower confidence for vague language
        vague_words = ['maybe', 'perhaps', 'might', 'could', 'possibly']
        if any(word in full_text.lower() for word in vague_words):
            confidence -= 0.2
        
        return min(1.0, confidence)
    
    def _deduplicate_action_items(self, action_items: List[ActionItem]) -> List[ActionItem]:
        """Remove duplicate action items"""
        seen_texts = set()
        unique_items = []
        
        for item in action_items:
            # Simple deduplication based on text similarity
            item_text = item.text.lower().strip()
            if item_text not in seen_texts:
                seen_texts.add(item_text)
                unique_items.append(item)
        
        return unique_items
    
    def _extract_segment_keywords(self, text: str) -> List[str]:
        """Extract keywords from a text segment"""
        if not nlp:
            # Fallback to simple keyword extraction
            words = text.lower().split()
            return [word for word in words if len(word) > 4 and word.isalpha()][:5]
        
        doc = nlp(text)
        keywords = []
        
        for token in doc:
            if (token.pos_ in ['NOUN', 'ADJ', 'VERB'] and 
                not token.is_stop and 
                not token.is_punct and 
                len(token.text) > 3):
                keywords.append(token.lemma_.lower())
        
        return list(set(keywords))[:5]
    
    def _extract_basic_topics(self, text: str) -> List[str]:
        """Extract basic topics without advanced NLP"""
        # Simple topic extraction based on frequent nouns
        words = re.findall(r'\b[A-Z][a-z]+\b', text)
        word_counts = Counter(words)
        return [word for word, count in word_counts.most_common(5) if count > 1]
    
    def _generate_topic_name(self, keywords: List[str], segments: List[str]) -> str:
        """Generate a meaningful name for a topic cluster"""
        if not keywords:
            return "General Discussion"
        
        # Use top keywords to create topic name
        top_keywords = keywords[:2]
        return ' & '.join([word.title() for word in top_keywords])
    
    def _generate_cluster_summary(self, segments: List[str]) -> str:
        """Generate summary for a topic cluster"""
        if not segments:
            return ""
        
        # Take first sentence from each segment and combine
        sentences = []
        for segment in segments[:3]:  # Limit to first 3 segments
            first_sentence = segment.split('.')[0] + '.'
            if len(first_sentence) > 10:
                sentences.append(first_sentence)
        
        return ' '.join(sentences)[:200] + "..." if len(' '.join(sentences)) > 200 else ' '.join(sentences)
    
    def _extract_participants(self, segments: List[Dict[str, Any]], speaker_info: Optional[Dict[str, str]] = None) -> List[str]:
        """Extract meeting participants"""
        speakers = set()
        
        for segment in segments:
            speaker = segment.get('speaker', 'Unknown')
            if speaker and speaker != 'Unknown':
                speakers.add(speaker)
        
        # Map speaker IDs to names if available
        if speaker_info:
            mapped_speakers = []
            for speaker in speakers:
                mapped_name = speaker_info.get(speaker, speaker)
                mapped_speakers.append(mapped_name)
            return mapped_speakers
        
        return list(speakers)
    
    def _extract_agenda_items(self, segments: List[Dict[str, Any]]) -> List[str]:
        """Extract agenda items from transcript"""
        agenda_items = []
        
        agenda_patterns = [
            r'\b(?:agenda item|topic|discuss|talking about):\s*([^.!?]+)',
            r'\b(?:first|second|third|next|moving on to)\s+(?:topic|item|point):\s*([^.!?]+)',
            r'\b(?:let\'s talk about|let\'s discuss)\s+([^.!?]+)'
        ]
        
        for segment in segments:
            text = segment.get('text', '')
            for pattern in agenda_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    item = match.group(1).strip()
                    if len(item) > 5 and item not in agenda_items:
                        agenda_items.append(item)
        
        return agenda_items[:10]  # Limit to 10 items
    
    def _extract_decisions(self, segments: List[Dict[str, Any]]) -> List[str]:
        """Extract key decisions from transcript"""
        decisions = []
        
        for segment in segments:
            text = segment.get('text', '')
            for pattern in self.meeting_patterns['decisions']:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    decision = match.group(1).strip()
                    if len(decision) > 10 and decision not in decisions:
                        decisions.append(decision)
        
        return decisions[:5]  # Limit to 5 decisions
    
    def _extract_next_steps(self, segments: List[Dict[str, Any]]) -> List[str]:
        """Extract next steps from transcript"""
        next_steps = []
        
        for segment in segments:
            text = segment.get('text', '')
            for pattern in self.meeting_patterns['next_steps']:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    step = match.group(1).strip()
                    if len(step) > 10 and step not in next_steps:
                        next_steps.append(step)
        
        return next_steps[:5]  # Limit to 5 steps
    
    def _generate_meeting_title(self, full_text: str, topics: List[str]) -> str:
        """Generate a title for the meeting"""
        if topics:
            return f"Meeting: {topics[0]}"
        
        # Look for meeting type indicators
        if 'standup' in full_text.lower():
            return "Daily Standup Meeting"
        elif 'retrospective' in full_text.lower():
            return "Retrospective Meeting"
        elif 'planning' in full_text.lower():
            return "Planning Meeting"
        elif 'review' in full_text.lower():
            return "Review Meeting"
        else:
            return f"Meeting - {datetime.now().strftime('%Y-%m-%d')}"
    
    def _assess_engagement(self, stats: Dict[str, Any], sentiment_data: List[Dict[str, Any]]) -> str:
        """Assess engagement level of the discussion"""
        speaking_rate = stats.get('speaking_rate', 0)
        
        if speaking_rate > 150:
            return "high"
        elif speaking_rate > 100:
            return "medium"
        else:
            return "low"
    
    def _assess_content_density(self, stats: Dict[str, Any]) -> str:
        """Assess content density"""
        avg_segment_length = stats.get('average_segment_length', 0)
        
        if avg_segment_length > 20:
            return "high"
        elif avg_segment_length > 10:
            return "medium"
        else:
            return "low"
    
    def _assess_action_orientation(self, action_items: List[Dict[str, Any]], stats: Dict[str, Any]) -> str:
        """Assess how action-oriented the discussion was"""
        total_words = stats.get('word_count', 1)
        action_ratio = len(action_items) / (total_words / 100)  # Actions per 100 words
        
        if action_ratio > 2:
            return "high"
        elif action_ratio > 1:
            return "medium"
        else:
            return "low"
    
    def _assess_discussion_quality(self, analysis_results: Dict[str, Any]) -> str:
        """Assess overall discussion quality"""
        # Simple heuristic based on multiple factors
        factors = []
        
        # Check if there are topics
        topics = analysis_results.get('topic_clusters', [])
        if len(topics) >= 2:
            factors.append(1)
        
        # Check if there are action items
        actions = analysis_results.get('action_items', [])
        if len(actions) >= 1:
            factors.append(1)
        
        # Check sentiment balance
        sentiment_data = analysis_results.get('sentiment_analysis', [])
        if sentiment_data:
            positive_ratio = len([s for s in sentiment_data if s.get('sentiment') == 'positive']) / len(sentiment_data)
            if 0.3 <= positive_ratio <= 0.7:  # Balanced sentiment
                factors.append(1)
        
        quality_score = sum(factors) / 3 if factors else 0
        
        if quality_score >= 0.7:
            return "high"
        elif quality_score >= 0.4:
            return "medium"
        else:
            return "low"


# Example usage and testing functions
if __name__ == "__main__":
    # Example usage
    analyzer = AIContentInsights()
    
    # Sample transcript data
    sample_transcript = {
        "segments": [
            {"start": 0.0, "end": 5.0, "text": "Good morning everyone, let's start our weekly planning meeting.", "speaker": "Alice"},
            {"start": 5.0, "end": 12.0, "text": "First item on the agenda is reviewing last week's progress on the new feature.", "speaker": "Alice"},
            {"start": 12.0, "end": 18.0, "text": "I think we made good progress, but we need to address the performance issues.", "speaker": "Bob"},
            {"start": 18.0, "end": 25.0, "text": "Bob, can you work on optimizing the database queries by Friday?", "speaker": "Alice"},
            {"start": 25.0, "end": 30.0, "text": "Sure, I'll prioritize that. It should be straightforward to fix.", "speaker": "Bob"},
            {"start": 30.0, "end": 38.0, "text": "Great! Next, we need to discuss the upcoming client presentation.", "speaker": "Alice"},
            {"start": 38.0, "end": 45.0, "text": "I'm concerned about the timeline. We might need to push back the deadline.", "speaker": "Charlie"},
            {"start": 45.0, "end": 52.0, "text": "Let's schedule a follow-up meeting to discuss this further. Charlie, can you prepare a revised timeline?", "speaker": "Alice"}
        ]
    }
    
    try:
        # Perform analysis
        results = analyzer.analyze_content(
            transcript_data=sample_transcript,
            content_type=ContentType.MEETING,
            speaker_info={"Alice": "Alice Johnson", "Bob": "Bob Smith", "Charlie": "Charlie Brown"}
        )
        
        print("AI Content Analysis Results:")
        print("=" * 50)
        
        # Print summary
        summary = results.get('summary', {})
        if isinstance(summary, dict):
            print(f"Executive Summary: {summary.get('executive_summary', 'N/A')}")
            print(f"Key Points: {len(summary.get('key_points', []))}")
        
        # Print action items
        action_items = results.get('action_items', [])
        print(f"\nAction Items Found: {len(action_items)}")
        for item in action_items:
            print(f"- {item.text} (Assignee: {item.assignee}, Priority: {item.priority.value})")
        
        # Print topics
        topics = results.get('topic_clusters', [])
        print(f"\nTopics Identified: {len(topics)}")
        for topic in topics:
            print(f"- {topic.name}: {', '.join(topic.keywords[:3])}")
        
        # Print meeting minutes
        if 'meeting_minutes' in results:
            minutes = results['meeting_minutes']
            print(f"\nMeeting: {minutes.title}")
            print(f"Participants: {', '.join(minutes.participants)}")
            print(f"Duration: {minutes.duration:.1f} minutes")
        
        print("\n✅ Analysis completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
    
    def _assess_engagement(self, stats: Dict[str, Any], sentiment_data: List[Dict[str, Any]]) -> str:
        """Assess engagement level of the discussion"""
        speaking_rate = stats.get('speaking_rate', 0)
        positive_sentiment = len([s for s in sentiment_data if s.get('sentiment') == 'positive'])
        total_sentiment = len(sentiment_data)
        
        if speaking_rate > 150 and positive_sentiment / max(total_sentiment, 1) > 0.4:
            return "high"
        elif speaking_rate > 100 or positive_sentiment / max(total_sentiment, 1) > 0.3:
            return "medium"
        else:
            return "low"
    
    def _assess_content_density(self, stats: Dict[str, Any]) -> str:
        """Assess content density"""
        avg_segment_length = stats.get('average_segment_length', 0)
        word_count = stats.get('word_count', 0)
        duration = stats.get('total_duration', 1)
        
        if avg_segment_length > 20 and word_count / duration > 2:
            return "high"
        elif avg_segment_length > 10 or word_count / duration > 1.5:
            return "medium"
        else:
            return "low"
    
    def _assess_action_orientation(self, action_items: List[Dict[str, Any]], stats: Dict[str, Any]) -> str:
        """Assess how action-oriented the discussion was"""
        total_words = stats.get('word_count', 1)
        action_count = len(action_items)
        
        # Calculate action items per 100 words
        action_density = (action_count / total_words) * 100
        
        if action_density > 2:
            return "high"
        elif action_density > 1:
            return "medium"
        else:
            return "low"
    
    def _assess_discussion_quality(self, analysis_results: Dict[str, Any]) -> str:
        """Assess overall discussion quality"""
        # Simple heuristic based on multiple factors
        stats = analysis_results.get('transcript_stats', {})
        action_items = analysis_results.get('action_items', [])
        sentiment_data = analysis_results.get('sentiment_analysis', [])
        topics = analysis_results.get('topic_clusters', [])
        
        quality_score = 0
        
        # Factor in engagement
        engagement = self._assess_engagement(stats, sentiment_data)
        if engagement == "high":
            quality_score += 3
        elif engagement == "medium":
            quality_score += 2
        else:
            quality_score += 1
        
        # Factor in action orientation
        action_orientation = self._assess_action_orientation(action_items, stats)
        if action_orientation == "high":
            quality_score += 3
        elif action_orientation == "medium":
            quality_score += 2
        else:
            quality_score += 1
        
        # Factor in topic diversity
        if len(topics) >= 3:
            quality_score += 2
        elif len(topics) >= 2:
            quality_score += 1
        
        # Determine overall quality
        if quality_score >= 7:
            return "high"
        elif quality_score >= 5:
            return "medium"
        else:
            return "low"