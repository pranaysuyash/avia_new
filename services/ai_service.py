"""
AI Service
Provides AI functionality for support and other services
"""

import logging
from typing import Optional, Dict, Any
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger(__name__)


class AIService:
    """
    AI service for content analysis
    Provides sentiment analysis, text similarity, and priority classification
    """
    
    def __init__(self):
        """Initialize AI service"""
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        logger.info("AIService initialized")
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict with sentiment analysis results
        """
        try:
            # Use TextBlob for sentiment analysis
            blob = TextBlob(text)
            
            # Get polarity (-1 to 1) and subjectivity (0 to 1)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            
            # Classify sentiment
            if polarity > 0.1:
                sentiment = "positive"
            elif polarity < -0.1:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            return {
                "sentiment": sentiment,
                "polarity": polarity,
                "subjectivity": subjectivity,
                "confidence": abs(polarity)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {
                "sentiment": "neutral",
                "polarity": 0.0,
                "subjectivity": 0.0,
                "confidence": 0.0
            }
    
    async def calculate_relevance(self, query: str, content: str) -> float:
        """
        Calculate relevance between query and content
        
        Args:
            query: Search query
            content: Content to compare against
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        try:
            if not query.strip() or not content.strip():
                return 0.0
            
            # Use TF-IDF and cosine similarity
            documents = [query, content]
            tfidf_matrix = self.vectorizer.fit_transform(documents)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating relevance: {e}")
            return 0.0
    
    async def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        try:
            if not text1.strip() or not text2.strip():
                return 0.0
            
            # Use TF-IDF and cosine similarity
            documents = [text1, text2]
            tfidf_matrix = self.vectorizer.fit_transform(documents)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    async def classify_priority(self, text: str) -> float:
        """
        Classify priority level of text content
        
        Args:
            text: Text to classify
            
        Returns:
            Priority score (0.0 to 1.0, higher = more urgent)
        """
        try:
            text_lower = text.lower()
            
            # Define urgency keywords with weights
            high_priority_keywords = {
                'urgent': 0.9,
                'critical': 0.95,
                'emergency': 1.0,
                'asap': 0.8,
                'immediately': 0.85,
                'broken': 0.7,
                'down': 0.7,
                'not working': 0.75,
                'error': 0.6,
                'failed': 0.6,
                'crash': 0.8,
                'help': 0.4,
                'issue': 0.3,
                'problem': 0.4
            }
            
            medium_priority_keywords = {
                'soon': 0.4,
                'question': 0.2,
                'slow': 0.3,
                'bug': 0.5,
                'request': 0.2
            }
            
            # Calculate priority score
            priority_score = 0.0
            word_count = len(text.split())
            
            # Check for high priority keywords
            for keyword, weight in high_priority_keywords.items():
                if keyword in text_lower:
                    priority_score = max(priority_score, weight)
            
            # Check for medium priority keywords (if no high priority found)
            if priority_score < 0.5:
                for keyword, weight in medium_priority_keywords.items():
                    if keyword in text_lower:
                        priority_score = max(priority_score, weight)
            
            # Analyze sentiment for additional context
            sentiment_result = await self.analyze_sentiment(text)
            if sentiment_result['sentiment'] == 'negative' and abs(sentiment_result['polarity']) > 0.5:
                priority_score = min(1.0, priority_score + 0.2)
            
            # Consider text length (longer descriptions might be more complex issues)
            if word_count > 100:
                priority_score = min(1.0, priority_score + 0.1)
            
            return priority_score
            
        except Exception as e:
            logger.error(f"Error classifying priority: {e}")
            return 0.5  # Default to medium priority