#!/usr/bin/env python3
"""
User Learning Profile System
Comprehensive system for managing user preferences, learning patterns, and personalized NLP experiences
"""

import uuid
import logging
from typing import Dict, List, Optional, Any, Union, Tuple, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
import json
import sqlite3
import hashlib
from pathlib import Path
import threading
from contextlib import contextmanager
import statistics
from collections import defaultdict, Counter

# Import our data models
from feedback_data_models import (
    FeedbackStorage, Feedback, Rating, Correction, FeedbackContext,
    FeedbackType, RatingType, FeedbackStatus, ContentType
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelPreference(Enum):
    """User preferences for model selection"""
    SPEED_OPTIMIZED = "speed_optimized"
    ACCURACY_OPTIMIZED = "accuracy_optimized"
    BALANCED = "balanced"
    CUSTOM = "custom"

class DomainExpertise(Enum):
    """User domain expertise areas"""
    GENERAL = "general"
    TECHNICAL = "technical"
    MEDICAL = "medical"
    LEGAL = "legal"
    ACADEMIC = "academic"
    BUSINESS = "business"
    CREATIVE = "creative"

class LearningGoal(Enum):
    """User learning and improvement goals"""
    ACCURACY_IMPROVEMENT = "accuracy_improvement"
    SPEED_IMPROVEMENT = "speed_improvement"
    DOMAIN_ADAPTATION = "domain_adaptation"
    FEATURE_EXPLORATION = "feature_exploration"
    WORKFLOW_OPTIMIZATION = "workflow_optimization"

@dataclass
class CorrectionPattern:
    """Pattern identified from user corrections"""
    pattern_id: str
    pattern_type: str  # word_replacement, punctuation, capitalization, etc.
    original_pattern: str
    corrected_pattern: str
    frequency: int
    confidence: float
    context_tags: List[str] = field(default_factory=list)
    last_seen: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'pattern_id': self.pattern_id,
            'pattern_type': self.pattern_type,
            'original_pattern': self.original_pattern,
            'corrected_pattern': self.corrected_pattern,
            'frequency': self.frequency,
            'confidence': self.confidence,
            'context_tags': self.context_tags,
            'last_seen': self.last_seen.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CorrectionPattern':
        """Create from dictionary"""
        data['last_seen'] = datetime.fromisoformat(data['last_seen'])
        return cls(**data)

@dataclass
class QualityThreshold:
    """Quality thresholds for different content types"""
    content_type: ContentType
    minimum_confidence: float
    preferred_confidence: float
    acceptable_error_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'content_type': self.content_type.value,
            'minimum_confidence': self.minimum_confidence,
            'preferred_confidence': self.preferred_confidence,
            'acceptable_error_rate': self.acceptable_error_rate
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QualityThreshold':
        """Create from dictionary"""
        data['content_type'] = ContentType(data['content_type'])
        return cls(**data)

@dataclass
class FeedbackHistory:
    """Summary of user's feedback history"""
    total_feedback_count: int = 0
    rating_distribution: Dict[str, int] = field(default_factory=dict)
    correction_count: int = 0
    suggestion_count: int = 0
    average_rating: float = 0.0
    most_common_corrections: List[str] = field(default_factory=list)
    feedback_frequency: float = 0.0  # feedback per session
    last_feedback_date: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'total_feedback_count': self.total_feedback_count,
            'rating_distribution': self.rating_distribution,
            'correction_count': self.correction_count,
            'suggestion_count': self.suggestion_count,
            'average_rating': self.average_rating,
            'most_common_corrections': self.most_common_corrections,
            'feedback_frequency': self.feedback_frequency,
            'last_feedback_date': self.last_feedback_date.isoformat() if self.last_feedback_date else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeedbackHistory':
        """Create from dictionary"""
        if data.get('last_feedback_date'):
            data['last_feedback_date'] = datetime.fromisoformat(data['last_feedback_date'])
        return cls(**data)

@dataclass
class UserLearningProfile:
    """Comprehensive user learning profile"""
    user_id: str
    profile_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Model preferences
    preferred_models: List[str] = field(default_factory=list)
    model_preference_type: ModelPreference = ModelPreference.BALANCED
    custom_model_config: Dict[str, Any] = field(default_factory=dict)
    
    # Learning patterns
    correction_patterns: List[CorrectionPattern] = field(default_factory=list)
    quality_thresholds: List[QualityThreshold] = field(default_factory=list)
    
    # Domain expertise
    domain_expertise: List[DomainExpertise] = field(default_factory=lambda: [DomainExpertise.GENERAL])
    specialized_vocabulary: List[str] = field(default_factory=list)
    
    # Learning goals and progress
    learning_goals: List[LearningGoal] = field(default_factory=list)
    feedback_history: FeedbackHistory = field(default_factory=FeedbackHistory)
    
    # Personalization settings
    auto_apply_corrections: bool = True
    feedback_frequency_preference: str = "moderate"  # low, moderate, high
    notification_preferences: Dict[str, bool] = field(default_factory=dict)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'user_id': self.user_id,
            'profile_id': self.profile_id,
            'preferred_models': self.preferred_models,
            'model_preference_type': self.model_preference_type.value,
            'custom_model_config': self.custom_model_config,
            'correction_patterns': [p.to_dict() for p in self.correction_patterns],
            'quality_thresholds': [q.to_dict() for q in self.quality_thresholds],
            'domain_expertise': [d.value for d in self.domain_expertise],
            'specialized_vocabulary': self.specialized_vocabulary,
            'learning_goals': [g.value for g in self.learning_goals],
            'feedback_history': self.feedback_history.to_dict(),
            'auto_apply_corrections': self.auto_apply_corrections,
            'feedback_frequency_preference': self.feedback_frequency_preference,
            'notification_preferences': self.notification_preferences,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'version': self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserLearningProfile':
        """Create from dictionary"""
        # Convert enums and complex objects
        data['model_preference_type'] = ModelPreference(data['model_preference_type'])
        data['correction_patterns'] = [CorrectionPattern.from_dict(p) for p in data['correction_patterns']]
        data['quality_thresholds'] = [QualityThreshold.from_dict(q) for q in data['quality_thresholds']]
        data['domain_expertise'] = [DomainExpertise(d) for d in data['domain_expertise']]
        data['learning_goals'] = [LearningGoal(g) for g in data['learning_goals']]
        data['feedback_history'] = FeedbackHistory.from_dict(data['feedback_history'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        
        return cls(**data)

class UserProfileStorage:
    """Storage system for user learning profiles"""
    
    def __init__(self, db_path: str = "user_profiles.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize the database schema"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    profile_id TEXT UNIQUE NOT NULL,
                    profile_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    version TEXT DEFAULT '1.0'
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_profiles_updated 
                ON user_profiles(last_updated)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_profiles_profile_id 
                ON user_profiles(profile_id)
            """)
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper cleanup"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def store_profile(self, profile: UserLearningProfile) -> bool:
        """Store user learning profile"""
        try:
            with self._lock:
                profile.last_updated = datetime.now()
                profile_json = json.dumps(profile.to_dict(), indent=2)
                
                with self._get_connection() as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO user_profiles 
                        (user_id, profile_id, profile_data, last_updated, version)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        profile.user_id,
                        profile.profile_id,
                        profile_json,
                        profile.last_updated.isoformat(),
                        profile.version
                    ))
                
                logger.info(f"Stored profile for user: {profile.user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error storing profile for user {profile.user_id}: {e}")
            return False
    
    def retrieve_profile(self, user_id: str) -> Optional[UserLearningProfile]:
        """Retrieve user learning profile"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT profile_data FROM user_profiles 
                    WHERE user_id = ?
                """, (user_id,))
                
                row = cursor.fetchone()
                if row:
                    profile_data = json.loads(row['profile_data'])
                    return UserLearningProfile.from_dict(profile_data)
                
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving profile for user {user_id}: {e}")
            return None
    
    def delete_profile(self, user_id: str) -> bool:
        """Delete user learning profile"""
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.execute("""
                        DELETE FROM user_profiles WHERE user_id = ?
                    """, (user_id,))
                    
                    deleted = cursor.rowcount > 0
                    if deleted:
                        logger.info(f"Deleted profile for user: {user_id}")
                    
                    return deleted
                    
        except Exception as e:
            logger.error(f"Error deleting profile for user {user_id}: {e}")
            return False
    
    def list_profiles(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List user profiles with basic information"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT user_id, profile_id, created_at, last_updated, version
                    FROM user_profiles 
                    ORDER BY last_updated DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error listing profiles: {e}")
            return []
    
    def get_profile_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored profiles"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_profiles,
                        COUNT(CASE WHEN last_updated > datetime('now', '-7 days') THEN 1 END) as active_week,
                        COUNT(CASE WHEN last_updated > datetime('now', '-30 days') THEN 1 END) as active_month,
                        MIN(created_at) as oldest_profile,
                        MAX(last_updated) as most_recent_update
                    FROM user_profiles
                """)
                
                row = cursor.fetchone()
                return dict(row) if row else {}
                
        except Exception as e:
            logger.error(f"Error getting profile statistics: {e}")
            return {}

class PersonalizationEngine:
    """Engine for personalizing user experience based on learning profiles"""
    
    def __init__(self, profile_storage: UserProfileStorage, feedback_storage: FeedbackStorage):
        self.profile_storage = profile_storage
        self.feedback_storage = feedback_storage
    
    def get_or_create_profile(self, user_id: str) -> UserLearningProfile:
        """Get existing profile or create new one"""
        profile = self.profile_storage.retrieve_profile(user_id)
        
        if not profile:
            profile = UserLearningProfile(user_id=user_id)
            # Set default quality thresholds
            default_thresholds = [
                QualityThreshold(ContentType.TRANSCRIPTION, 0.7, 0.9, 0.1),
                QualityThreshold(ContentType.MEETING_ELEMENT, 0.6, 0.8, 0.15),
                QualityThreshold(ContentType.ACTION_ITEM, 0.8, 0.95, 0.05),
                QualityThreshold(ContentType.MOM_DOCUMENT, 0.75, 0.9, 0.1)
            ]
            profile.quality_thresholds = default_thresholds
            
            self.profile_storage.store_profile(profile)
            logger.info(f"Created new profile for user: {user_id}")
        
        return profile
    
    def update_profile_from_feedback(self, user_id: str, feedback: Feedback) -> bool:
        """Update user profile based on new feedback"""
        try:
            profile = self.get_or_create_profile(user_id)
            
            # Update feedback history
            self._update_feedback_history(profile, feedback)
            
            # Extract and update correction patterns
            if feedback.correction:
                self._update_correction_patterns(profile, feedback.correction)
            
            # Update quality thresholds based on ratings
            if feedback.rating:
                self._update_quality_thresholds(profile, feedback)
            
            # Save updated profile
            return self.profile_storage.store_profile(profile)
            
        except Exception as e:
            logger.error(f"Error updating profile from feedback: {e}")
            return False
    
    def _update_feedback_history(self, profile: UserLearningProfile, feedback: Feedback):
        """Update feedback history statistics"""
        history = profile.feedback_history
        
        history.total_feedback_count += 1
        history.last_feedback_date = datetime.now()
        
        if feedback.rating:
            rating_key = f"{feedback.rating.rating_type.value}_{feedback.rating.value}"
            history.rating_distribution[rating_key] = history.rating_distribution.get(rating_key, 0) + 1
            
            # Update average rating
            normalized_rating = feedback.rating.normalize_rating()
            if history.total_feedback_count == 1:
                history.average_rating = normalized_rating
            else:
                # Running average
                history.average_rating = (
                    (history.average_rating * (history.total_feedback_count - 1) + normalized_rating) 
                    / history.total_feedback_count
                )
        
        if feedback.correction:
            history.correction_count += 1
        
        if feedback.feedback_type == FeedbackType.SUGGESTION:
            history.suggestion_count += 1
    
    def _update_correction_patterns(self, profile: UserLearningProfile, correction: Correction):
        """Update correction patterns from new correction"""
        # Find existing pattern or create new one
        pattern_key = f"{correction.correction_type}_{correction.original_text}_{correction.corrected_text}"
        pattern_id = hashlib.md5(pattern_key.encode()).hexdigest()[:12]
        
        existing_pattern = None
        for pattern in profile.correction_patterns:
            if pattern.pattern_id == pattern_id:
                existing_pattern = pattern
                break
        
        if existing_pattern:
            existing_pattern.frequency += 1
            existing_pattern.last_seen = datetime.now()
            # Update confidence based on frequency
            existing_pattern.confidence = min(0.95, existing_pattern.frequency * 0.1)
        else:
            new_pattern = CorrectionPattern(
                pattern_id=pattern_id,
                pattern_type=correction.correction_type,
                original_pattern=correction.original_text,
                corrected_pattern=correction.corrected_text,
                frequency=1,
                confidence=0.1
            )
            profile.correction_patterns.append(new_pattern)
        
        # Keep only top 50 patterns to prevent unbounded growth
        profile.correction_patterns.sort(key=lambda p: (p.frequency, p.confidence), reverse=True)
        profile.correction_patterns = profile.correction_patterns[:50]
    
    def _update_quality_thresholds(self, profile: UserLearningProfile, feedback: Feedback):
        """Update quality thresholds based on user ratings"""
        if not feedback.context or not feedback.rating:
            return
        
        content_type = feedback.context.content_type
        confidence_score = feedback.context.confidence_score
        
        if confidence_score is None:
            return
        
        # Find existing threshold for content type
        threshold = None
        for qt in profile.quality_thresholds:
            if qt.content_type == content_type:
                threshold = qt
                break
        
        if not threshold:
            threshold = QualityThreshold(content_type, 0.7, 0.9, 0.1)
            profile.quality_thresholds.append(threshold)
        
        # Adjust thresholds based on rating
        normalized_rating = feedback.rating.normalize_rating()
        
        if normalized_rating >= 0.8:  # High rating
            # User is satisfied, we can lower minimum threshold slightly
            threshold.minimum_confidence = max(0.5, threshold.minimum_confidence - 0.02)
        elif normalized_rating <= 0.4:  # Low rating
            # User is unsatisfied, raise minimum threshold
            threshold.minimum_confidence = min(0.95, threshold.minimum_confidence + 0.05)
    
    def recommend_model_selection(self, user_id: str, content_type: ContentType, 
                                content_complexity: float = 0.5) -> Dict[str, Any]:
        """Recommend optimal model selection for user"""
        profile = self.get_or_create_profile(user_id)
        
        # Get quality threshold for content type
        threshold = None
        for qt in profile.quality_thresholds:
            if qt.content_type == content_type:
                threshold = qt
                break
        
        if not threshold:
            threshold = QualityThreshold(content_type, 0.7, 0.9, 0.1)
        
        # Base recommendation on user preference type
        if profile.model_preference_type == ModelPreference.SPEED_OPTIMIZED:
            recommended_models = ["spacy_sm", "distilbert"]
            priority = "speed"
        elif profile.model_preference_type == ModelPreference.ACCURACY_OPTIMIZED:
            recommended_models = ["spacy_lg", "roberta_large", "bert_large"]
            priority = "accuracy"
        else:  # BALANCED or CUSTOM
            recommended_models = ["spacy_md", "bert_base", "roberta_base"]
            priority = "balanced"
        
        # Adjust based on content complexity
        if content_complexity > 0.7 and priority != "speed":
            recommended_models = ["spacy_lg", "roberta_large"] + recommended_models
        elif content_complexity < 0.3 and priority != "accuracy":
            recommended_models = ["spacy_sm"] + recommended_models
        
        # Include user's preferred models if specified
        if profile.preferred_models:
            recommended_models = profile.preferred_models + recommended_models
        
        # Remove duplicates while preserving order
        seen = set()
        unique_models = []
        for model in recommended_models:
            if model not in seen:
                seen.add(model)
                unique_models.append(model)
        
        return {
            'recommended_models': unique_models[:5],  # Top 5 recommendations
            'priority': priority,
            'quality_threshold': threshold.preferred_confidence,
            'minimum_threshold': threshold.minimum_confidence,
            'reasoning': f"Based on {profile.model_preference_type.value} preference and content complexity {content_complexity:.2f}"
        }
    
    def get_personalized_settings(self, user_id: str) -> Dict[str, Any]:
        """Get personalized settings for user"""
        profile = self.get_or_create_profile(user_id)
        
        return {
            'auto_apply_corrections': profile.auto_apply_corrections,
            'feedback_frequency': profile.feedback_frequency_preference,
            'notification_preferences': profile.notification_preferences,
            'domain_expertise': [d.value for d in profile.domain_expertise],
            'specialized_vocabulary': profile.specialized_vocabulary,
            'learning_goals': [g.value for g in profile.learning_goals],
            'correction_patterns_count': len(profile.correction_patterns),
            'average_rating': profile.feedback_history.average_rating,
            'total_feedback': profile.feedback_history.total_feedback_count
        }
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        try:
            profile = self.get_or_create_profile(user_id)
            
            # Update model preferences
            if 'model_preference_type' in preferences:
                profile.model_preference_type = ModelPreference(preferences['model_preference_type'])
            
            if 'preferred_models' in preferences:
                profile.preferred_models = preferences['preferred_models']
            
            if 'custom_model_config' in preferences:
                profile.custom_model_config.update(preferences['custom_model_config'])
            
            # Update domain expertise
            if 'domain_expertise' in preferences:
                profile.domain_expertise = [DomainExpertise(d) for d in preferences['domain_expertise']]
            
            if 'specialized_vocabulary' in preferences:
                profile.specialized_vocabulary = preferences['specialized_vocabulary']
            
            # Update learning goals
            if 'learning_goals' in preferences:
                profile.learning_goals = [LearningGoal(g) for g in preferences['learning_goals']]
            
            # Update personalization settings
            if 'auto_apply_corrections' in preferences:
                profile.auto_apply_corrections = preferences['auto_apply_corrections']
            
            if 'feedback_frequency_preference' in preferences:
                profile.feedback_frequency_preference = preferences['feedback_frequency_preference']
            
            if 'notification_preferences' in preferences:
                profile.notification_preferences.update(preferences['notification_preferences'])
            
            return self.profile_storage.store_profile(profile)
            
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return False
    
    def analyze_user_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze user patterns and provide insights"""
        profile = self.get_or_create_profile(user_id)
        
        # Analyze correction patterns
        pattern_analysis = self._analyze_correction_patterns(profile.correction_patterns)
        
        # Analyze feedback trends
        feedback_analysis = self._analyze_feedback_trends(profile.feedback_history)
        
        # Generate recommendations
        recommendations = self._generate_improvement_recommendations(profile)
        
        return {
            'user_id': user_id,
            'profile_age_days': (datetime.now() - profile.created_at).days,
            'pattern_analysis': pattern_analysis,
            'feedback_analysis': feedback_analysis,
            'recommendations': recommendations,
            'learning_progress': self._calculate_learning_progress(profile)
        }
    
    def _analyze_correction_patterns(self, patterns: List[CorrectionPattern]) -> Dict[str, Any]:
        """Analyze correction patterns for insights"""
        if not patterns:
            return {'total_patterns': 0, 'insights': []}
        
        # Group by pattern type
        type_counts = Counter(p.pattern_type for p in patterns)
        
        # Find most frequent corrections
        frequent_patterns = sorted(patterns, key=lambda p: p.frequency, reverse=True)[:5]
        
        # Calculate pattern confidence distribution
        confidences = [p.confidence for p in patterns]
        avg_confidence = statistics.mean(confidences) if confidences else 0
        
        insights = []
        
        # Generate insights based on patterns
        if type_counts.get('capitalization', 0) > 3:
            insights.append("User frequently corrects capitalization - consider enabling auto-capitalization")
        
        if type_counts.get('punctuation', 0) > 3:
            insights.append("User frequently corrects punctuation - consider punctuation enhancement models")
        
        if type_counts.get('word_replacement', 0) > 5:
            insights.append("User frequently replaces words - consider domain-specific vocabulary training")
        
        return {
            'total_patterns': len(patterns),
            'pattern_types': dict(type_counts),
            'most_frequent': [
                {
                    'type': p.pattern_type,
                    'original': p.original_pattern,
                    'corrected': p.corrected_pattern,
                    'frequency': p.frequency
                } for p in frequent_patterns
            ],
            'average_confidence': avg_confidence,
            'insights': insights
        }
    
    def _analyze_feedback_trends(self, history: FeedbackHistory) -> Dict[str, Any]:
        """Analyze feedback trends"""
        return {
            'total_feedback': history.total_feedback_count,
            'average_rating': history.average_rating,
            'correction_ratio': history.correction_count / max(1, history.total_feedback_count),
            'suggestion_ratio': history.suggestion_count / max(1, history.total_feedback_count),
            'engagement_level': self._calculate_engagement_level(history),
            'rating_distribution': history.rating_distribution
        }
    
    def _calculate_engagement_level(self, history: FeedbackHistory) -> str:
        """Calculate user engagement level"""
        if history.total_feedback_count == 0:
            return "new"
        elif history.total_feedback_count < 10:
            return "low"
        elif history.total_feedback_count < 50:
            return "moderate"
        elif history.total_feedback_count < 200:
            return "high"
        else:
            return "very_high"
    
    def _generate_improvement_recommendations(self, profile: UserLearningProfile) -> List[str]:
        """Generate improvement recommendations for user"""
        recommendations = []
        
        # Based on correction patterns
        if len(profile.correction_patterns) > 10:
            recommendations.append("Consider enabling auto-correction for your most common patterns")
        
        # Based on feedback history
        if profile.feedback_history.average_rating < 0.6:
            recommendations.append("Try accuracy-optimized models for better results")
        elif profile.feedback_history.average_rating > 0.9:
            recommendations.append("You might benefit from speed-optimized models")
        
        # Based on domain expertise
        if DomainExpertise.GENERAL in profile.domain_expertise and len(profile.domain_expertise) == 1:
            recommendations.append("Consider specifying your domain expertise for better model selection")
        
        # Based on learning goals
        if not profile.learning_goals:
            recommendations.append("Set learning goals to get personalized improvement suggestions")
        
        return recommendations
    
    def _calculate_learning_progress(self, profile: UserLearningProfile) -> Dict[str, Any]:
        """Calculate learning progress metrics"""
        days_active = (datetime.now() - profile.created_at).days
        
        return {
            'days_active': days_active,
            'feedback_per_day': profile.feedback_history.total_feedback_count / max(1, days_active),
            'pattern_learning_rate': len(profile.correction_patterns) / max(1, days_active),
            'improvement_trend': self._calculate_improvement_trend(profile),
            'expertise_development': len(profile.domain_expertise) > 1
        }
    
    def _calculate_improvement_trend(self, profile: UserLearningProfile) -> str:
        """Calculate improvement trend based on feedback history"""
        # This is a simplified calculation - in a real system, you'd analyze
        # feedback over time to determine if ratings are improving
        avg_rating = profile.feedback_history.average_rating
        
        if avg_rating >= 0.8:
            return "excellent"
        elif avg_rating >= 0.7:
            return "good"
        elif avg_rating >= 0.6:
            return "improving"
        else:
            return "needs_attention"

# Utility functions
def create_user_profile_storage(db_path: str = "user_profiles.db") -> UserProfileStorage:
    """Create a user profile storage instance"""
    return UserProfileStorage(db_path)

def create_personalization_engine(profile_storage: UserProfileStorage, 
                                feedback_storage: FeedbackStorage) -> PersonalizationEngine:
    """Create a personalization engine instance"""
    return PersonalizationEngine(profile_storage, feedback_storage)

# Example usage and testing
def example_usage():
    """Example usage of user learning profile system"""
    from feedback_data_models import create_feedback_storage
    
    # Create storage systems
    profile_storage = create_user_profile_storage("example_profiles.db")
    feedback_storage = create_feedback_storage("example_feedback.db")
    
    # Create personalization engine
    engine = create_personalization_engine(profile_storage, feedback_storage)
    
    # Create or get user profile
    user_id = "user_123"
    profile = engine.get_or_create_profile(user_id)
    print(f"Created profile for user: {user_id}")
    
    # Update user preferences
    preferences = {
        'model_preference_type': 'accuracy_optimized',
        'domain_expertise': ['technical', 'business'],
        'learning_goals': ['accuracy_improvement', 'domain_adaptation'],
        'auto_apply_corrections': True
    }
    
    success = engine.update_user_preferences(user_id, preferences)
    print(f"Updated preferences: {success}")
    
    # Get model recommendations
    recommendations = engine.recommend_model_selection(
        user_id, ContentType.TRANSCRIPTION, content_complexity=0.7
    )
    print(f"Model recommendations: {recommendations}")
    
    # Get personalized settings
    settings = engine.get_personalized_settings(user_id)
    print(f"Personalized settings: {settings}")
    
    # Analyze user patterns
    analysis = engine.analyze_user_patterns(user_id)
    print(f"User analysis: {analysis}")

if __name__ == "__main__":
    example_usage()