#!/usr/bin/env python3
"""
Smart Content Recommendations System (Task 42)
Provides personalized content suggestions, similar content recommendations, 
trending topics, content gap analysis, and smart tagging
"""

import streamlit as st
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from collections import defaultdict, Counter
import hashlib
from dataclasses import dataclass, asdict
from pathlib import Path
import pickle
import re

logger = logging.getLogger(__name__)

@dataclass
class ContentItem:
    """Represents a piece of content for recommendations"""
    id: str
    title: str
    transcript: str
    entities: List[Dict]
    topics: List[str]
    tags: List[str]
    duration: float
    language: str
    confidence: float
    created_at: str
    user_id: str
    file_info: Dict
    embedding: Optional[List[float]] = None
    view_count: int = 0
    last_accessed: Optional[str] = None

@dataclass
class UserProfile:
    """User profile for personalized recommendations"""
    user_id: str
    interests: Dict[str, float]  # topic -> interest score
    viewing_history: List[str]  # content IDs
    search_history: List[str]
    preferred_languages: List[str]
    preferred_duration_range: Tuple[float, float]
    created_at: str
    last_updated: str

class ContentEmbedding:
    """Generate embeddings for content similarity"""
    
    def __init__(self):
        self.vocabulary = {}
        self.idf_scores = {}
        self.embedding_dim = 100
    
    def build_vocabulary(self, content_items: List[ContentItem]):
        """Build vocabulary from all content items"""
        word_counts = Counter()
        doc_counts = Counter()
        total_docs = len(content_items)
        
        for item in content_items:
            # Combine transcript and topics for embedding
            text = f"{item.transcript} {' '.join(item.topics)} {' '.join(item.tags)}"
            words = self._preprocess_text(text)
            
            # Count words and document frequency
            word_counts.update(words)
            doc_counts.update(set(words))
        
        # Build vocabulary with most common words
        self.vocabulary = {word: idx for idx, (word, _) in enumerate(word_counts.most_common(self.embedding_dim))}
        
        # Calculate IDF scores
        for word, doc_freq in doc_counts.items():
            if word in self.vocabulary:
                self.idf_scores[word] = np.log(total_docs / (doc_freq + 1))
    
    def _preprocess_text(self, text: str) -> List[str]:
        """Preprocess text for embedding generation"""
        # Convert to lowercase and remove special characters
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())
        words = text.split()
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        words = [word for word in words if word not in stop_words and len(word) > 2]
        
        return words
    
    def generate_embedding(self, content_item: ContentItem) -> List[float]:
        """Generate TF-IDF embedding for content item"""
        text = f"{content_item.transcript} {' '.join(content_item.topics)} {' '.join(content_item.tags)}"
        words = self._preprocess_text(text)
        
        # Create TF-IDF vector
        embedding = np.zeros(len(self.vocabulary))
        word_counts = Counter(words)
        total_words = len(words)
        
        for word, count in word_counts.items():
            if word in self.vocabulary:
                tf = count / total_words
                idf = self.idf_scores.get(word, 0)
                embedding[self.vocabulary[word]] = tf * idf
        
        # Normalize embedding
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding.tolist()
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)

class ContentRecommendationEngine:
    """Main recommendation engine"""
    
    def __init__(self, data_dir: str = "recommendation_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.content_items: Dict[str, ContentItem] = {}
        self.user_profiles: Dict[str, UserProfile] = {}
        self.embedding_engine = ContentEmbedding()
        
        self.load_data()
    
    def add_content_item(self, content_item: ContentItem):
        """Add a new content item to the system"""
        # Generate embedding
        if not self.embedding_engine.vocabulary:
            # If vocabulary not built yet, build it with current content
            all_items = list(self.content_items.values()) + [content_item]
            self.embedding_engine.build_vocabulary(all_items)
            
            # Regenerate embeddings for existing items
            for item in self.content_items.values():
                item.embedding = self.embedding_engine.generate_embedding(item)
        
        content_item.embedding = self.embedding_engine.generate_embedding(content_item)
        self.content_items[content_item.id] = content_item
        
        # Extract and update topics
        self._extract_topics(content_item)
        
        # Save data
        self.save_data()
    
    def update_user_profile(self, user_id: str, content_id: str, interaction_type: str = "view"):
        """Update user profile based on interaction"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(
                user_id=user_id,
                interests={},
                viewing_history=[],
                search_history=[],
                preferred_languages=["en"],
                preferred_duration_range=(0.0, 3600.0),
                created_at=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat()
            )
        
        profile = self.user_profiles[user_id]
        
        if interaction_type == "view" and content_id in self.content_items:
            content = self.content_items[content_id]
            
            # Update viewing history
            if content_id not in profile.viewing_history:
                profile.viewing_history.append(content_id)
            
            # Update interests based on content topics
            for topic in content.topics:
                current_score = profile.interests.get(topic, 0.0)
                profile.interests[topic] = min(1.0, current_score + 0.1)
            
            # Update content view count
            content.view_count += 1
            content.last_accessed = datetime.now().isoformat()
        
        profile.last_updated = datetime.now().isoformat()
        self.save_data()
    
    def get_similar_content(self, content_id: str, limit: int = 5) -> List[Tuple[ContentItem, float]]:
        """Get similar content based on content similarity"""
        if content_id not in self.content_items:
            return []
        
        target_content = self.content_items[content_id]
        if not target_content.embedding:
            return []
        
        similarities = []
        
        for other_id, other_content in self.content_items.items():
            if other_id == content_id or not other_content.embedding:
                continue
            
            similarity = self.embedding_engine.calculate_similarity(
                target_content.embedding, other_content.embedding
            )
            
            similarities.append((other_content, similarity))
        
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]
    
    def get_personalized_recommendations(self, user_id: str, limit: int = 10) -> List[Tuple[ContentItem, float]]:
        """Get personalized recommendations for a user"""
        if user_id not in self.user_profiles:
            return self.get_trending_content(limit)
        
        profile = self.user_profiles[user_id]
        recommendations = []
        
        for content_id, content in self.content_items.items():
            if content_id in profile.viewing_history:
                continue  # Skip already viewed content
            
            # Calculate recommendation score
            score = self._calculate_recommendation_score(profile, content)
            recommendations.append((content, score))
        
        # Sort by score and return top results
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:limit]
    
    def get_trending_content(self, limit: int = 10, time_window_days: int = 7) -> List[Tuple[ContentItem, float]]:
        """Get trending content based on recent activity"""
        cutoff_date = datetime.now() - timedelta(days=time_window_days)
        trending = []
        
        for content in self.content_items.values():
            # Calculate trending score based on recent views and recency
            recent_score = 0.0
            
            if content.last_accessed:
                last_access = datetime.fromisoformat(content.last_accessed)
                if last_access > cutoff_date:
                    days_ago = (datetime.now() - last_access).days
                    recency_factor = max(0, 1 - (days_ago / time_window_days))
                    recent_score = content.view_count * recency_factor
            
            trending.append((content, recent_score))
        
        # Sort by trending score
        trending.sort(key=lambda x: x[1], reverse=True)
        return trending[:limit]
    
    def analyze_content_gaps(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Analyze content gaps and suggest topics to cover"""
        # Get all topics from existing content
        all_topics = Counter()
        topic_coverage = defaultdict(list)
        
        for content in self.content_items.values():
            for topic in content.topics:
                all_topics[topic] += 1
                topic_coverage[topic].append(content)
        
        # Identify underrepresented topics
        total_content = len(self.content_items)
        underrepresented = []
        
        for topic, count in all_topics.items():
            coverage_ratio = count / total_content
            if coverage_ratio < 0.1:  # Less than 10% coverage
                underrepresented.append({
                    "topic": topic,
                    "current_count": count,
                    "coverage_ratio": coverage_ratio,
                    "suggested_priority": "high" if coverage_ratio < 0.05 else "medium"
                })
        
        # Suggest trending topics not yet covered
        trending_keywords = self._extract_trending_keywords()
        missing_trends = []
        
        for keyword in trending_keywords:
            if keyword not in all_topics:
                missing_trends.append({
                    "keyword": keyword,
                    "trend_score": trending_keywords[keyword],
                    "suggested_priority": "high"
                })
        
        return {
            "underrepresented_topics": sorted(underrepresented, key=lambda x: x["coverage_ratio"]),
            "missing_trending_topics": sorted(missing_trends, key=lambda x: x["trend_score"], reverse=True)[:10],
            "total_topics": len(all_topics),
            "total_content": total_content,
            "average_topics_per_content": sum(len(c.topics) for c in self.content_items.values()) / max(total_content, 1)
        }
    
    def generate_smart_tags(self, content_item: ContentItem) -> List[str]:
        """Generate smart tags for content based on analysis"""
        tags = set()
        
        # Extract tags from transcript using keyword analysis
        transcript_words = self._preprocess_text(content_item.transcript)
        
        # Add entity-based tags
        for entity in content_item.entities:
            entity_text = entity.get('text', '').lower()
            entity_type = entity.get('type', '')
            
            if entity_type == 'PERSON':
                tags.add(f"person:{entity_text}")
            elif entity_type == 'ORG':
                tags.add(f"organization:{entity_text}")
            elif entity_type == 'GPE':
                tags.add(f"location:{entity_text}")
        
        # Add duration-based tags
        if content_item.duration < 300:  # 5 minutes
            tags.add("short-form")
        elif content_item.duration > 3600:  # 1 hour
            tags.add("long-form")
        else:
            tags.add("medium-form")
        
        # Add language tag
        tags.add(f"language:{content_item.language}")
        
        # Add confidence-based tags
        if content_item.confidence > 0.9:
            tags.add("high-quality")
        elif content_item.confidence < 0.7:
            tags.add("needs-review")
        
        # Add topic-based tags
        for topic in content_item.topics:
            tags.add(f"topic:{topic}")
        
        # Add content type tags based on keywords
        content_type_keywords = {
            "meeting": ["meeting", "agenda", "action items", "minutes"],
            "interview": ["interview", "questions", "answers", "discussion"],
            "lecture": ["lecture", "lesson", "education", "learning"],
            "presentation": ["presentation", "slides", "demo", "showcase"],
            "podcast": ["podcast", "episode", "host", "guest"],
            "call": ["call", "phone", "conversation", "discussion"]
        }
        
        transcript_lower = content_item.transcript.lower()
        for content_type, keywords in content_type_keywords.items():
            if any(keyword in transcript_lower for keyword in keywords):
                tags.add(f"type:{content_type}")
        
        return list(tags)[:20]  # Limit to 20 tags
    
    def _calculate_recommendation_score(self, profile: UserProfile, content: ContentItem) -> float:
        """Calculate recommendation score for a user and content item"""
        score = 0.0
        
        # Interest-based scoring
        for topic in content.topics:
            if topic in profile.interests:
                score += profile.interests[topic] * 0.4
        
        # Language preference
        if content.language in profile.preferred_languages:
            score += 0.2
        
        # Duration preference
        min_dur, max_dur = profile.preferred_duration_range
        if min_dur <= content.duration <= max_dur:
            score += 0.1
        
        # Popularity boost
        if content.view_count > 0:
            popularity_score = min(0.2, content.view_count * 0.01)
            score += popularity_score
        
        # Recency boost
        if content.created_at:
            created_date = datetime.fromisoformat(content.created_at)
            days_ago = (datetime.now() - created_date).days
            if days_ago < 7:
                score += 0.1 * (7 - days_ago) / 7
        
        # Quality boost
        score += content.confidence * 0.1
        
        return min(1.0, score)
    
    def _extract_topics(self, content_item: ContentItem):
        """Extract topics from content using simple keyword analysis"""
        if content_item.topics:
            return  # Topics already provided
        
        # Simple topic extraction based on keywords
        topic_keywords = {
            "business": ["business", "company", "revenue", "profit", "sales", "marketing", "strategy"],
            "technology": ["technology", "software", "programming", "AI", "machine learning", "data"],
            "education": ["education", "learning", "teaching", "student", "course", "lesson"],
            "health": ["health", "medical", "doctor", "patient", "treatment", "medicine"],
            "finance": ["finance", "money", "investment", "bank", "financial", "economy"],
            "science": ["science", "research", "study", "experiment", "analysis", "discovery"],
            "entertainment": ["entertainment", "movie", "music", "game", "fun", "comedy"],
            "sports": ["sports", "game", "team", "player", "competition", "athletic"],
            "travel": ["travel", "trip", "vacation", "destination", "tourism", "journey"],
            "food": ["food", "cooking", "recipe", "restaurant", "meal", "cuisine"]
        }
        
        transcript_lower = content_item.transcript.lower()
        detected_topics = []
        
        for topic, keywords in topic_keywords.items():
            keyword_count = sum(1 for keyword in keywords if keyword in transcript_lower)
            if keyword_count >= 2:  # Require at least 2 keyword matches
                detected_topics.append(topic)
        
        content_item.topics = detected_topics[:5]  # Limit to 5 topics
    
    def _extract_trending_keywords(self) -> Dict[str, float]:
        """Extract trending keywords from recent content"""
        recent_content = []
        cutoff_date = datetime.now() - timedelta(days=30)
        
        for content in self.content_items.values():
            if content.created_at:
                created_date = datetime.fromisoformat(content.created_at)
                if created_date > cutoff_date:
                    recent_content.append(content)
        
        # Extract keywords from recent content
        keyword_counts = Counter()
        
        for content in recent_content:
            words = self._preprocess_text(content.transcript)
            keyword_counts.update(words)
        
        # Calculate trending scores
        trending = {}
        total_recent = len(recent_content)
        
        for keyword, count in keyword_counts.most_common(50):
            if len(keyword) > 3:  # Only consider longer keywords
                trending[keyword] = count / total_recent
        
        return trending
    
    def _preprocess_text(self, text: str) -> List[str]:
        """Preprocess text for analysis"""
        return self.embedding_engine._preprocess_text(text)
    
    def save_data(self):
        """Save recommendation data to disk"""
        try:
            # Save content items
            content_file = self.data_dir / "content_items.pkl"
            with open(content_file, 'wb') as f:
                pickle.dump(self.content_items, f)
            
            # Save user profiles
            profiles_file = self.data_dir / "user_profiles.pkl"
            with open(profiles_file, 'wb') as f:
                pickle.dump(self.user_profiles, f)
            
            # Save embedding engine
            embedding_file = self.data_dir / "embedding_engine.pkl"
            with open(embedding_file, 'wb') as f:
                pickle.dump(self.embedding_engine, f)
                
        except Exception as e:
            logger.error(f"Error saving recommendation data: {e}")
    
    def load_data(self):
        """Load recommendation data from disk"""
        try:
            # Load content items
            content_file = self.data_dir / "content_items.pkl"
            if content_file.exists():
                with open(content_file, 'rb') as f:
                    self.content_items = pickle.load(f)
            
            # Load user profiles
            profiles_file = self.data_dir / "user_profiles.pkl"
            if profiles_file.exists():
                with open(profiles_file, 'rb') as f:
                    self.user_profiles = pickle.load(f)
            
            # Load embedding engine
            embedding_file = self.data_dir / "embedding_engine.pkl"
            if embedding_file.exists():
                with open(embedding_file, 'rb') as f:
                    self.embedding_engine = pickle.load(f)
                    
        except Exception as e:
            logger.error(f"Error loading recommendation data: {e}")
    
    def get_content_stats(self) -> Dict[str, Any]:
        """Get statistics about the content library"""
        if not self.content_items:
            return {"total_content": 0}
        
        total_content = len(self.content_items)
        total_duration = sum(item.duration for item in self.content_items.values())
        avg_duration = total_duration / total_content
        
        # Language distribution
        languages = Counter(item.language for item in self.content_items.values())
        
        # Topic distribution
        all_topics = []
        for item in self.content_items.values():
            all_topics.extend(item.topics)
        topic_distribution = Counter(all_topics)
        
        # Quality distribution
        quality_ranges = {"high": 0, "medium": 0, "low": 0}
        for item in self.content_items.values():
            if item.confidence > 0.8:
                quality_ranges["high"] += 1
            elif item.confidence > 0.6:
                quality_ranges["medium"] += 1
            else:
                quality_ranges["low"] += 1
        
        return {
            "total_content": total_content,
            "total_duration_hours": total_duration / 3600,
            "average_duration_minutes": avg_duration / 60,
            "language_distribution": dict(languages.most_common()),
            "top_topics": dict(topic_distribution.most_common(10)),
            "quality_distribution": quality_ranges,
            "total_users": len(self.user_profiles)
        }

# Global recommendation engine instance
recommendation_engine = ContentRecommendationEngine()

def create_content_item_from_session(session_results, user_id: str = "default_user") -> ContentItem:
    """Create a ContentItem from session results"""
    
    # Generate unique ID
    content_id = hashlib.md5(f"{session_results.transcript[:100]}{datetime.now().isoformat()}".encode()).hexdigest()
    
    # Extract basic information
    transcript = getattr(session_results, 'transcript', '')
    entities = getattr(session_results, 'entities', [])
    duration = getattr(session_results, 'duration', 0.0)
    language = getattr(session_results, 'language', 'en')
    confidence = getattr(session_results, 'confidence', 0.0)
    created_at = getattr(session_results, 'created_at', datetime.now()).isoformat()
    
    # File information
    file_info = {
        'original_filename': getattr(session_results, 'original_filename', 'unknown'),
        'file_size': getattr(session_results, 'file_size', 0),
        'processing_time': getattr(session_results, 'processing_time', 0)
    }
    
    # Create title from transcript
    title = transcript[:50] + "..." if len(transcript) > 50 else transcript
    if not title.strip():
        title = f"Transcription {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    content_item = ContentItem(
        id=content_id,
        title=title,
        transcript=transcript,
        entities=entities,
        topics=[],  # Will be extracted automatically
        tags=[],    # Will be generated automatically
        duration=duration,
        language=language,
        confidence=confidence,
        created_at=created_at,
        user_id=user_id,
        file_info=file_info
    )
    
    return content_item