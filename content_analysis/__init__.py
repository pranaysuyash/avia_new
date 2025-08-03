# Content Analysis Module
from .advanced_analyzer import AdvancedContentAnalyzer

# Create a simple ContentAnalyzer wrapper with async support
import asyncio
from typing import Dict, Any, Optional

class ContentAnalyzer:
    """Wrapper for AdvancedContentAnalyzer with async support"""
    
    def __init__(self):
        self.analyzer = AdvancedContentAnalyzer()
    
    async def analyze_content_async(self, text: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Async wrapper for content analysis"""
        # Run synchronous analysis in executor
        loop = asyncio.get_event_loop()
        
        # Perform analysis
        analysis = await loop.run_in_executor(
            None, 
            self._analyze_sync, 
            text,
            options
        )
        
        return analysis
    
    def _analyze_sync(self, text: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Synchronous analysis wrapper"""
        # Initialize result
        result = {
            "summary": "",
            "sentiment": {
                "overall": "neutral",
                "score": 0.5,
                "distribution": {
                    "positive": 33,
                    "neutral": 34,
                    "negative": 33
                }
            },
            "topics": [],
            "entities": {
                "people": [],
                "organizations": [],
                "locations": [],
                "dates": [],
                "products": []
            },
            "keyPhrases": [],
            "statistics": {
                "wordCount": 0,
                "uniqueWords": 0,
                "averageSentenceLength": 0,
                "readabilityScore": 0
            },
            "recommendations": []
        }
        
        if not text:
            return result
        
        # Basic analysis using the advanced analyzer
        try:
            # Get emotion analysis
            emotion_result = self.analyzer.analyze_emotions(text, {})
            
            # Update sentiment based on emotion analysis
            result["sentiment"]["overall"] = emotion_result.overall_sentiment
            result["sentiment"]["score"] = emotion_result.sentiment_score
            
            # Get complexity analysis
            complexity_result = self.analyzer.analyze_complexity(text, {})
            result["statistics"]["readabilityScore"] = int(complexity_result.flesch_reading_ease)
            
            # Basic text statistics
            words = text.split()
            sentences = text.split('.')
            result["statistics"]["wordCount"] = len(words)
            result["statistics"]["uniqueWords"] = len(set(words))
            result["statistics"]["averageSentenceLength"] = len(words) / max(1, len(sentences))
            
            # Extract key phrases (simple approach)
            result["keyPhrases"] = self._extract_key_phrases(text)
            
            # Extract entities (simple approach)
            result["entities"] = self._extract_entities(text)
            
            # Generate summary
            result["summary"] = self._generate_summary(text)
            
            # Extract topics
            result["topics"] = self._extract_topics(text)
            
            # Generate recommendations
            result["recommendations"] = self._generate_recommendations(result)
            
        except Exception as e:
            # Return partial result on error
            pass
        
        return result
    
    def _extract_key_phrases(self, text: str) -> list:
        """Extract key phrases from text"""
        # Simple extraction based on frequency
        words = text.lower().split()
        # Filter out common words
        filtered = [w for w in words if len(w) > 4]
        word_freq = {}
        for word in filtered:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top phrases
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [{"phrase": word, "score": count/len(words)} for word, count in sorted_words[:10]]
    
    def _extract_entities(self, text: str) -> dict:
        """Extract named entities from text"""
        entities = {
            "people": [],
            "organizations": [],
            "locations": [],
            "dates": [],
            "products": []
        }
        
        # Simple pattern matching for demonstration
        # In production, use spaCy or similar NLP library
        
        # Extract potential dates
        import re
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b\d{4}\b',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
        ]
        for pattern in date_patterns:
            entities["dates"].extend(re.findall(pattern, text, re.IGNORECASE))
        
        return entities
    
    def _generate_summary(self, text: str) -> str:
        """Generate a simple summary"""
        sentences = text.split('.')[:3]  # First 3 sentences
        return '. '.join(sentences).strip() + '.' if sentences else text[:200] + '...'
    
    def _extract_topics(self, text: str) -> list:
        """Extract main topics from text"""
        # Simple keyword-based topic extraction
        topics = []
        
        # Common topic keywords
        topic_keywords = {
            "technology": ["software", "computer", "digital", "internet", "app", "system"],
            "business": ["company", "market", "sales", "revenue", "customer", "product"],
            "education": ["learning", "student", "teacher", "school", "course", "education"],
            "health": ["health", "medical", "patient", "doctor", "treatment", "care"]
        }
        
        text_lower = text.lower()
        for topic, keywords in topic_keywords.items():
            relevance = sum(1 for keyword in keywords if keyword in text_lower) / len(keywords)
            if relevance > 0.1:
                topics.append({
                    "topic": topic.title(),
                    "relevance": relevance,
                    "keywords": [k for k in keywords if k in text_lower]
                })
        
        return sorted(topics, key=lambda x: x["relevance"], reverse=True)[:3]
    
    def _generate_recommendations(self, analysis: dict) -> list:
        """Generate content recommendations based on analysis"""
        recommendations = []
        
        # Based on readability
        if analysis["statistics"]["readabilityScore"] < 30:
            recommendations.append("Consider simplifying the language for better readability")
        elif analysis["statistics"]["readabilityScore"] > 80:
            recommendations.append("Content is very easy to read, consider adding more depth")
        
        # Based on sentiment
        if analysis["sentiment"]["distribution"]["negative"] > 50:
            recommendations.append("Content has negative sentiment, consider balancing with positive points")
        
        # Based on length
        if analysis["statistics"]["wordCount"] < 100:
            recommendations.append("Content is quite short, consider expanding key points")
        elif analysis["statistics"]["wordCount"] > 2000:
            recommendations.append("Content is lengthy, consider breaking into sections")
        
        return recommendations

__all__ = ['ContentAnalyzer', 'AdvancedContentAnalyzer']