"""
AI-Powered Content Recommendations and Discovery System
Task 204: Implement intelligent content recommendations using AI/ML
"""

import os
import json
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import hashlib
from dataclasses import dataclass, field
from enum import Enum
import logging
from functools import lru_cache
import pickle

from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, JSON, Boolean, ForeignKey, Table, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.sql import func

# ML Libraries
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import pandas as pd

# NLP Libraries
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Deep Learning (optional - for advanced recommendations)
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

Base = declarative_base()
logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
except:
    pass

class RecommendationType(Enum):
    CONTENT_BASED = "content_based"
    COLLABORATIVE = "collaborative"
    HYBRID = "hybrid"
    TRENDING = "trending"
    PERSONALIZED = "personalized"
    SIMILAR = "similar"
    DISCOVERY = "discovery"

class ContentType(Enum):
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    TRANSCRIPT = "transcript"
    MEETING = "meeting"
    WEBINAR = "webinar"
    PODCAST = "podcast"

@dataclass
class UserProfile:
    user_id: str
    interests: List[str] = field(default_factory=list)
    preferred_categories: List[str] = field(default_factory=list)
    viewing_history: List[str] = field(default_factory=list)
    interaction_scores: Dict[str, float] = field(default_factory=dict)
    content_preferences: Dict[str, Any] = field(default_factory=dict)
    language_preferences: List[str] = field(default_factory=list)
    expertise_level: str = "intermediate"
    active_times: List[int] = field(default_factory=list)  # Hours of day
    
@dataclass
class ContentFeatures:
    content_id: str
    title: str
    description: str
    transcript: str
    tags: List[str]
    categories: List[str]
    duration: int
    quality_score: float
    engagement_score: float
    created_at: datetime
    view_count: int
    share_count: int
    language: str
    difficulty_level: str
    topics: List[str]
    entities: List[str]
    sentiment_score: float
    
@dataclass
class Recommendation:
    content_id: str
    score: float
    reason: str
    recommendation_type: RecommendationType
    explanation: Dict[str, Any]
    confidence: float
    
# Database Models
class UserInteraction(Base):
    __tablename__ = 'user_interactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), index=True)
    content_id = Column(String(100), index=True)
    interaction_type = Column(String(50))  # view, like, share, download, bookmark
    duration = Column(Integer)  # Time spent in seconds
    completion_rate = Column(Float)
    rating = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    context = Column(JSON)  # Device, location, referrer, etc.
    
    __table_args__ = (
        Index('ix_user_content', 'user_id', 'content_id'),
        Index('ix_timestamp', 'timestamp'),
    )

class ContentEmbedding(Base):
    __tablename__ = 'content_embeddings'
    
    id = Column(Integer, primary_key=True)
    content_id = Column(String(100), unique=True, index=True)
    text_embedding = Column(Text)  # Serialized numpy array
    topic_embedding = Column(Text)  # LDA topic distribution
    semantic_embedding = Column(Text)  # Advanced semantic embedding
    feature_vector = Column(Text)  # Combined feature vector
    updated_at = Column(DateTime, default=datetime.utcnow)

class RecommendationCache(Base):
    __tablename__ = 'recommendation_cache'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), index=True)
    recommendation_type = Column(String(50))
    recommendations = Column(Text)  # Serialized recommendations
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
class TrendingContent(Base):
    __tablename__ = 'trending_content'
    
    id = Column(Integer, primary_key=True)
    content_id = Column(String(100), index=True)
    trend_score = Column(Float)
    velocity = Column(Float)  # Rate of change
    timeframe = Column(String(20))  # hourly, daily, weekly
    category = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow)

class ContentRecommendationEngine:
    def __init__(self, db_url: str = "sqlite:///recommendations.db"):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        # Initialize ML components
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 3)
        )
        self.lda_model = LatentDirichletAllocation(
            n_components=50,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.lemmatizer = WordNetLemmatizer()
        
        # Cache for embeddings and models
        self.embedding_cache = {}
        self.model_cache = {}
        
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for analysis"""
        if not text:
            return ""
            
        # Convert to lowercase
        text = text.lower()
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords and lemmatize
        stop_words = set(stopwords.words('english'))
        tokens = [
            self.lemmatizer.lemmatize(token)
            for token in tokens
            if token.isalnum() and token not in stop_words
        ]
        
        return ' '.join(tokens)
    
    def extract_content_features(self, content: Dict[str, Any]) -> ContentFeatures:
        """Extract features from content for recommendation"""
        return ContentFeatures(
            content_id=content['id'],
            title=content.get('title', ''),
            description=content.get('description', ''),
            transcript=content.get('transcript', ''),
            tags=content.get('tags', []),
            categories=content.get('categories', []),
            duration=content.get('duration', 0),
            quality_score=content.get('quality_score', 0.5),
            engagement_score=content.get('engagement_score', 0.5),
            created_at=content.get('created_at', datetime.utcnow()),
            view_count=content.get('view_count', 0),
            share_count=content.get('share_count', 0),
            language=content.get('language', 'en'),
            difficulty_level=content.get('difficulty_level', 'intermediate'),
            topics=content.get('topics', []),
            entities=content.get('entities', []),
            sentiment_score=content.get('sentiment_score', 0.0)
        )
    
    def create_content_embedding(self, features: ContentFeatures) -> np.ndarray:
        """Create embedding vector for content"""
        # Combine text features
        text = f"{features.title} {features.description} {features.transcript}"
        processed_text = self.preprocess_text(text)
        
        # TF-IDF embedding
        if not hasattr(self.tfidf_vectorizer, 'vocabulary_'):
            # Fit on first use
            self.tfidf_vectorizer.fit([processed_text])
        
        tfidf_embedding = self.tfidf_vectorizer.transform([processed_text]).toarray()[0]
        
        # Numerical features
        numerical_features = np.array([
            features.duration / 3600.0,  # Normalize to hours
            features.quality_score,
            features.engagement_score,
            np.log1p(features.view_count),
            np.log1p(features.share_count),
            features.sentiment_score,
            len(features.tags) / 10.0,  # Normalize tag count
            len(features.categories) / 5.0  # Normalize category count
        ])
        
        # Combine embeddings
        combined_embedding = np.concatenate([
            tfidf_embedding * 0.7,  # Weight text features
            numerical_features * 0.3  # Weight numerical features
        ])
        
        return combined_embedding
    
    def calculate_content_similarity(
        self,
        content_id: str,
        candidate_ids: List[str],
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """Calculate similarity between content items"""
        session = self.Session()
        
        try:
            # Get embeddings
            base_embedding = self._get_or_create_embedding(session, content_id)
            
            similarities = []
            for candidate_id in candidate_ids:
                if candidate_id == content_id:
                    continue
                    
                candidate_embedding = self._get_or_create_embedding(session, candidate_id)
                
                # Calculate cosine similarity
                similarity = cosine_similarity(
                    base_embedding.reshape(1, -1),
                    candidate_embedding.reshape(1, -1)
                )[0][0]
                
                similarities.append((candidate_id, float(similarity)))
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            return similarities[:top_k]
            
        finally:
            session.close()
    
    def _get_or_create_embedding(self, session: Session, content_id: str) -> np.ndarray:
        """Get or create content embedding"""
        # Check cache
        if content_id in self.embedding_cache:
            return self.embedding_cache[content_id]
        
        # Check database
        embedding_record = session.query(ContentEmbedding).filter_by(
            content_id=content_id
        ).first()
        
        if embedding_record and embedding_record.feature_vector:
            embedding = pickle.loads(embedding_record.feature_vector.encode('latin1'))
            self.embedding_cache[content_id] = embedding
            return embedding
        
        # Create new embedding (would need actual content data)
        # This is a placeholder - in production, fetch actual content
        embedding = np.random.randn(5000 + 8)  # TF-IDF + numerical features
        
        # Store in database
        if not embedding_record:
            embedding_record = ContentEmbedding(content_id=content_id)
            session.add(embedding_record)
        
        embedding_record.feature_vector = pickle.dumps(embedding).decode('latin1')
        embedding_record.updated_at = datetime.utcnow()
        session.commit()
        
        # Cache
        self.embedding_cache[content_id] = embedding
        
        return embedding
    
    def get_user_profile(self, user_id: str) -> UserProfile:
        """Build user profile from interactions"""
        session = self.Session()
        
        try:
            # Get user interactions
            interactions = session.query(UserInteraction).filter_by(
                user_id=user_id
            ).order_by(UserInteraction.timestamp.desc()).limit(100).all()
            
            profile = UserProfile(user_id=user_id)
            
            # Analyze interactions
            for interaction in interactions:
                # Track viewing history
                profile.viewing_history.append(interaction.content_id)
                
                # Calculate interaction scores
                score = self._calculate_interaction_score(interaction)
                profile.interaction_scores[interaction.content_id] = score
                
                # Extract active times
                hour = interaction.timestamp.hour
                profile.active_times.append(hour)
            
            # Determine preferences from history
            profile.interests = self._extract_user_interests(interactions)
            profile.preferred_categories = self._extract_preferred_categories(interactions)
            
            return profile
            
        finally:
            session.close()
    
    def _calculate_interaction_score(self, interaction: UserInteraction) -> float:
        """Calculate score based on interaction type and engagement"""
        base_scores = {
            'view': 1.0,
            'like': 3.0,
            'share': 5.0,
            'download': 4.0,
            'bookmark': 3.5
        }
        
        score = base_scores.get(interaction.interaction_type, 1.0)
        
        # Adjust by completion rate
        if interaction.completion_rate:
            score *= (0.5 + interaction.completion_rate * 0.5)
        
        # Adjust by rating
        if interaction.rating:
            score *= (interaction.rating / 5.0)
        
        # Time decay
        days_old = (datetime.utcnow() - interaction.timestamp).days
        decay_factor = np.exp(-days_old / 30.0)  # 30-day half-life
        score *= decay_factor
        
        return score
    
    def _extract_user_interests(self, interactions: List[UserInteraction]) -> List[str]:
        """Extract user interests from interaction history"""
        # This would analyze content metadata to determine interests
        # Placeholder implementation
        interests = ['technology', 'business', 'productivity']
        return interests
    
    def _extract_preferred_categories(self, interactions: List[UserInteraction]) -> List[str]:
        """Extract preferred categories from interaction history"""
        # Placeholder implementation
        categories = ['meetings', 'webinars', 'tutorials']
        return categories
    
    def recommend_content_based(
        self,
        user_id: str,
        content_pool: List[str],
        top_k: int = 10
    ) -> List[Recommendation]:
        """Content-based filtering recommendations"""
        profile = self.get_user_profile(user_id)
        
        if not profile.viewing_history:
            return self.recommend_popular(content_pool, top_k)
        
        # Get embeddings for user's recent content
        recent_content = profile.viewing_history[:10]
        user_embedding = self._create_user_embedding(recent_content)
        
        recommendations = []
        for content_id in content_pool:
            if content_id in profile.viewing_history:
                continue
            
            content_embedding = self._get_or_create_embedding(self.Session(), content_id)
            
            # Calculate similarity
            similarity = cosine_similarity(
                user_embedding.reshape(1, -1),
                content_embedding.reshape(1, -1)
            )[0][0]
            
            # Weight by interaction scores
            weight = profile.interaction_scores.get(content_id, 1.0)
            score = similarity * weight
            
            rec = Recommendation(
                content_id=content_id,
                score=float(score),
                reason="Based on your viewing history",
                recommendation_type=RecommendationType.CONTENT_BASED,
                explanation={
                    'similarity': float(similarity),
                    'based_on': recent_content[:3]
                },
                confidence=min(0.9, similarity + 0.3)
            )
            recommendations.append(rec)
        
        # Sort and return top k
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:top_k]
    
    def _create_user_embedding(self, content_ids: List[str]) -> np.ndarray:
        """Create user embedding from content history"""
        session = self.Session()
        
        embeddings = []
        for content_id in content_ids:
            embedding = self._get_or_create_embedding(session, content_id)
            embeddings.append(embedding)
        
        session.close()
        
        # Average embeddings (could use weighted average)
        if embeddings:
            return np.mean(embeddings, axis=0)
        else:
            return np.zeros(5000 + 8)
    
    def recommend_collaborative(
        self,
        user_id: str,
        content_pool: List[str],
        top_k: int = 10
    ) -> List[Recommendation]:
        """Collaborative filtering recommendations"""
        session = self.Session()
        
        try:
            # Find similar users
            similar_users = self._find_similar_users(session, user_id, limit=20)
            
            if not similar_users:
                return self.recommend_popular(content_pool, top_k)
            
            # Get content liked by similar users
            recommendations = []
            user_history = set(self.get_user_profile(user_id).viewing_history)
            
            for similar_user_id, similarity in similar_users:
                # Get their interactions
                interactions = session.query(UserInteraction).filter_by(
                    user_id=similar_user_id
                ).filter(
                    UserInteraction.interaction_type.in_(['like', 'share', 'bookmark'])
                ).all()
                
                for interaction in interactions:
                    if interaction.content_id not in user_history and \
                       interaction.content_id in content_pool:
                        
                        score = similarity * self._calculate_interaction_score(interaction)
                        
                        rec = Recommendation(
                            content_id=interaction.content_id,
                            score=score,
                            reason="Users with similar interests also liked this",
                            recommendation_type=RecommendationType.COLLABORATIVE,
                            explanation={
                                'similar_users': [similar_user_id],
                                'user_similarity': similarity
                            },
                            confidence=min(0.85, similarity + 0.2)
                        )
                        recommendations.append(rec)
            
            # Aggregate recommendations
            content_scores = defaultdict(float)
            content_recs = defaultdict(list)
            
            for rec in recommendations:
                content_scores[rec.content_id] += rec.score
                content_recs[rec.content_id].append(rec)
            
            # Create final recommendations
            final_recs = []
            for content_id, total_score in content_scores.items():
                recs = content_recs[content_id]
                final_recs.append(Recommendation(
                    content_id=content_id,
                    score=total_score / len(recs),
                    reason=recs[0].reason,
                    recommendation_type=RecommendationType.COLLABORATIVE,
                    explanation={
                        'based_on_users': len(recs),
                        'avg_similarity': np.mean([r.explanation['user_similarity'] for r in recs])
                    },
                    confidence=min(0.9, total_score / len(recs))
                ))
            
            final_recs.sort(key=lambda x: x.score, reverse=True)
            return final_recs[:top_k]
            
        finally:
            session.close()
    
    def _find_similar_users(
        self,
        session: Session,
        user_id: str,
        limit: int = 10
    ) -> List[Tuple[str, float]]:
        """Find users with similar interaction patterns"""
        # Get user's interactions
        user_interactions = session.query(UserInteraction).filter_by(
            user_id=user_id
        ).all()
        
        if not user_interactions:
            return []
        
        user_content = set(i.content_id for i in user_interactions)
        user_scores = {i.content_id: self._calculate_interaction_score(i) 
                      for i in user_interactions}
        
        # Find other users who interacted with same content
        other_users = session.query(UserInteraction.user_id).filter(
            UserInteraction.content_id.in_(list(user_content)),
            UserInteraction.user_id != user_id
        ).distinct().all()
        
        similarities = []
        for (other_user_id,) in other_users:
            # Get their interactions
            other_interactions = session.query(UserInteraction).filter_by(
                user_id=other_user_id
            ).filter(
                UserInteraction.content_id.in_(list(user_content))
            ).all()
            
            # Calculate similarity
            other_scores = {i.content_id: self._calculate_interaction_score(i)
                          for i in other_interactions}
            
            # Jaccard similarity with score weighting
            intersection = user_content.intersection(set(other_scores.keys()))
            union = user_content.union(set(other_scores.keys()))
            
            if union:
                # Weighted Jaccard
                intersection_score = sum(
                    min(user_scores.get(c, 0), other_scores.get(c, 0))
                    for c in intersection
                )
                union_score = sum(
                    max(user_scores.get(c, 0), other_scores.get(c, 0))
                    for c in union
                )
                
                similarity = intersection_score / union_score if union_score > 0 else 0
                similarities.append((other_user_id, similarity))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]
    
    def recommend_trending(
        self,
        content_pool: List[str],
        timeframe: str = 'daily',
        top_k: int = 10
    ) -> List[Recommendation]:
        """Get trending content recommendations"""
        session = self.Session()
        
        try:
            # Get trending content
            trending = session.query(TrendingContent).filter_by(
                timeframe=timeframe
            ).filter(
                TrendingContent.content_id.in_(content_pool)
            ).order_by(
                TrendingContent.trend_score.desc()
            ).limit(top_k).all()
            
            recommendations = []
            for item in trending:
                rec = Recommendation(
                    content_id=item.content_id,
                    score=item.trend_score,
                    reason=f"Trending {timeframe}",
                    recommendation_type=RecommendationType.TRENDING,
                    explanation={
                        'velocity': item.velocity,
                        'category': item.category,
                        'timeframe': timeframe
                    },
                    confidence=0.95
                )
                recommendations.append(rec)
            
            return recommendations
            
        finally:
            session.close()
    
    def recommend_popular(
        self,
        content_pool: List[str],
        top_k: int = 10
    ) -> List[Recommendation]:
        """Get popular content recommendations"""
        session = self.Session()
        
        try:
            # Get interaction counts
            popular = session.query(
                UserInteraction.content_id,
                func.count(UserInteraction.id).label('interaction_count'),
                func.avg(UserInteraction.rating).label('avg_rating')
            ).filter(
                UserInteraction.content_id.in_(content_pool)
            ).group_by(
                UserInteraction.content_id
            ).order_by(
                func.count(UserInteraction.id).desc()
            ).limit(top_k).all()
            
            recommendations = []
            for content_id, count, avg_rating in popular:
                # Calculate popularity score
                score = np.log1p(count) * (avg_rating or 3.0) / 5.0
                
                rec = Recommendation(
                    content_id=content_id,
                    score=float(score),
                    reason="Popular content",
                    recommendation_type=RecommendationType.TRENDING,
                    explanation={
                        'interaction_count': count,
                        'average_rating': float(avg_rating) if avg_rating else None
                    },
                    confidence=0.8
                )
                recommendations.append(rec)
            
            return recommendations
            
        finally:
            session.close()
    
    def recommend_hybrid(
        self,
        user_id: str,
        content_pool: List[str],
        top_k: int = 10,
        weights: Dict[str, float] = None
    ) -> List[Recommendation]:
        """Hybrid recommendation combining multiple strategies"""
        if weights is None:
            weights = {
                'content': 0.4,
                'collaborative': 0.3,
                'trending': 0.2,
                'discovery': 0.1
            }
        
        all_recommendations = []
        
        # Content-based recommendations
        if weights.get('content', 0) > 0:
            content_recs = self.recommend_content_based(user_id, content_pool, top_k * 2)
            for rec in content_recs:
                rec.score *= weights['content']
                all_recommendations.append(rec)
        
        # Collaborative filtering
        if weights.get('collaborative', 0) > 0:
            collab_recs = self.recommend_collaborative(user_id, content_pool, top_k * 2)
            for rec in collab_recs:
                rec.score *= weights['collaborative']
                all_recommendations.append(rec)
        
        # Trending content
        if weights.get('trending', 0) > 0:
            trending_recs = self.recommend_trending(content_pool, 'daily', top_k)
            for rec in trending_recs:
                rec.score *= weights['trending']
                all_recommendations.append(rec)
        
        # Discovery (random exploration)
        if weights.get('discovery', 0) > 0:
            discovery_recs = self.recommend_discovery(user_id, content_pool, top_k // 2)
            for rec in discovery_recs:
                rec.score *= weights['discovery']
                all_recommendations.append(rec)
        
        # Aggregate by content_id
        content_scores = defaultdict(float)
        content_recs = defaultdict(list)
        
        for rec in all_recommendations:
            content_scores[rec.content_id] += rec.score
            content_recs[rec.content_id].append(rec)
        
        # Create final hybrid recommendations
        final_recommendations = []
        for content_id, total_score in content_scores.items():
            recs = content_recs[content_id]
            
            # Combine explanations
            combined_explanation = {
                'strategies': [r.recommendation_type.value for r in recs],
                'weights_used': weights
            }
            
            final_rec = Recommendation(
                content_id=content_id,
                score=total_score,
                reason="Recommended for you",
                recommendation_type=RecommendationType.HYBRID,
                explanation=combined_explanation,
                confidence=min(0.95, total_score)
            )
            final_recommendations.append(final_rec)
        
        # Sort and return top k
        final_recommendations.sort(key=lambda x: x.score, reverse=True)
        return final_recommendations[:top_k]
    
    def recommend_discovery(
        self,
        user_id: str,
        content_pool: List[str],
        top_k: int = 5
    ) -> List[Recommendation]:
        """Recommend content for discovery/exploration"""
        profile = self.get_user_profile(user_id)
        
        # Filter out already viewed content
        unseen_content = [c for c in content_pool if c not in profile.viewing_history]
        
        # Random selection with slight bias towards quality
        if len(unseen_content) <= top_k:
            selected = unseen_content
        else:
            # Could add quality scoring here
            selected = np.random.choice(unseen_content, top_k, replace=False).tolist()
        
        recommendations = []
        for content_id in selected:
            rec = Recommendation(
                content_id=content_id,
                score=np.random.uniform(0.3, 0.7),  # Random discovery score
                reason="Discover something new",
                recommendation_type=RecommendationType.DISCOVERY,
                explanation={
                    'exploration_bonus': 0.2,
                    'diversity_score': np.random.uniform(0.5, 1.0)
                },
                confidence=0.5
            )
            recommendations.append(rec)
        
        return recommendations
    
    def update_trending_content(self, timeframe: str = 'daily'):
        """Update trending content scores"""
        session = self.Session()
        
        try:
            # Calculate time window
            if timeframe == 'hourly':
                time_window = datetime.utcnow() - timedelta(hours=1)
            elif timeframe == 'daily':
                time_window = datetime.utcnow() - timedelta(days=1)
            elif timeframe == 'weekly':
                time_window = datetime.utcnow() - timedelta(weeks=1)
            else:
                time_window = datetime.utcnow() - timedelta(days=1)
            
            # Get recent interactions
            recent_interactions = session.query(
                UserInteraction.content_id,
                func.count(UserInteraction.id).label('count'),
                func.avg(UserInteraction.rating).label('avg_rating')
            ).filter(
                UserInteraction.timestamp >= time_window
            ).group_by(
                UserInteraction.content_id
            ).all()
            
            # Calculate trend scores
            for content_id, count, avg_rating in recent_interactions:
                # Get previous period for velocity calculation
                prev_window = time_window - (datetime.utcnow() - time_window)
                prev_count = session.query(func.count(UserInteraction.id)).filter(
                    UserInteraction.content_id == content_id,
                    UserInteraction.timestamp >= prev_window,
                    UserInteraction.timestamp < time_window
                ).scalar() or 0
                
                # Calculate velocity (rate of change)
                velocity = (count - prev_count) / max(prev_count, 1)
                
                # Calculate trend score
                trend_score = count * (1 + velocity) * (avg_rating or 3.0) / 5.0
                
                # Update or create trending record
                trending = session.query(TrendingContent).filter_by(
                    content_id=content_id,
                    timeframe=timeframe
                ).first()
                
                if trending:
                    trending.trend_score = trend_score
                    trending.velocity = velocity
                    trending.updated_at = datetime.utcnow()
                else:
                    trending = TrendingContent(
                        content_id=content_id,
                        trend_score=trend_score,
                        velocity=velocity,
                        timeframe=timeframe,
                        category='general'  # Would extract from content
                    )
                    session.add(trending)
            
            session.commit()
            
        finally:
            session.close()
    
    def record_interaction(
        self,
        user_id: str,
        content_id: str,
        interaction_type: str,
        **kwargs
    ):
        """Record user interaction for learning"""
        session = self.Session()
        
        try:
            interaction = UserInteraction(
                user_id=user_id,
                content_id=content_id,
                interaction_type=interaction_type,
                duration=kwargs.get('duration'),
                completion_rate=kwargs.get('completion_rate'),
                rating=kwargs.get('rating'),
                context=kwargs.get('context', {})
            )
            session.add(interaction)
            session.commit()
            
            # Invalidate recommendation cache
            session.query(RecommendationCache).filter_by(
                user_id=user_id
            ).delete()
            session.commit()
            
        finally:
            session.close()
    
    def get_cached_recommendations(
        self,
        user_id: str,
        recommendation_type: str
    ) -> Optional[List[Recommendation]]:
        """Get cached recommendations if available"""
        session = self.Session()
        
        try:
            cache = session.query(RecommendationCache).filter_by(
                user_id=user_id,
                recommendation_type=recommendation_type
            ).filter(
                RecommendationCache.expires_at > datetime.utcnow()
            ).first()
            
            if cache:
                return pickle.loads(cache.recommendations.encode('latin1'))
            
            return None
            
        finally:
            session.close()
    
    def cache_recommendations(
        self,
        user_id: str,
        recommendation_type: str,
        recommendations: List[Recommendation],
        ttl_hours: int = 1
    ):
        """Cache recommendations for faster retrieval"""
        session = self.Session()
        
        try:
            cache = RecommendationCache(
                user_id=user_id,
                recommendation_type=recommendation_type,
                recommendations=pickle.dumps(recommendations).decode('latin1'),
                expires_at=datetime.utcnow() + timedelta(hours=ttl_hours)
            )
            session.add(cache)
            session.commit()
            
        finally:
            session.close()

# Neural Collaborative Filtering (if PyTorch available)
if TORCH_AVAILABLE:
    class NeuralCollaborativeFiltering(nn.Module):
        def __init__(self, n_users: int, n_items: int, embedding_dim: int = 50):
            super().__init__()
            self.user_embedding = nn.Embedding(n_users, embedding_dim)
            self.item_embedding = nn.Embedding(n_items, embedding_dim)
            
            # MLP layers
            self.fc1 = nn.Linear(embedding_dim * 2, 64)
            self.fc2 = nn.Linear(64, 32)
            self.fc3 = nn.Linear(32, 16)
            self.output = nn.Linear(16, 1)
            
            self.dropout = nn.Dropout(0.2)
            
        def forward(self, user_ids, item_ids):
            user_embeds = self.user_embedding(user_ids)
            item_embeds = self.item_embedding(item_ids)
            
            # Concatenate embeddings
            x = torch.cat([user_embeds, item_embeds], dim=1)
            
            # MLP
            x = F.relu(self.fc1(x))
            x = self.dropout(x)
            x = F.relu(self.fc2(x))
            x = self.dropout(x)
            x = F.relu(self.fc3(x))
            x = torch.sigmoid(self.output(x))
            
            return x.squeeze()

# Usage example
async def main():
    # Initialize recommendation engine
    engine = ContentRecommendationEngine()
    
    # Sample content pool
    content_pool = [f"content_{i}" for i in range(100)]
    
    # Record some interactions
    engine.record_interaction(
        user_id="user123",
        content_id="content_1",
        interaction_type="view",
        duration=1800,
        completion_rate=0.75,
        rating=4.0
    )
    
    # Get recommendations
    recommendations = engine.recommend_hybrid(
        user_id="user123",
        content_pool=content_pool,
        top_k=10
    )
    
    print("Recommendations for user123:")
    for rec in recommendations:
        print(f"- {rec.content_id}: {rec.score:.3f} ({rec.reason})")
    
    # Update trending content
    engine.update_trending_content('daily')
    
    # Get trending recommendations
    trending = engine.recommend_trending(content_pool, 'daily', 5)
    print("\nTrending content:")
    for rec in trending:
        print(f"- {rec.content_id}: {rec.score:.3f}")

if __name__ == "__main__":
    asyncio.run(main())