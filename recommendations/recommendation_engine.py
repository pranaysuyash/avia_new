"""
Smart Content Recommendation Engine
Implements multiple recommendation strategies including collaborative filtering,
content-based filtering, and hybrid approaches
"""

import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import sqlite3
from pathlib import Path
from collections import defaultdict, Counter
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class Recommendation:
    """Represents a content recommendation"""
    transcript_id: str
    title: str
    score: float
    recommendation_type: str  # 'content_based', 'collaborative', 'trending', 'personalized'
    reason: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class UserProfile:
    """User profile for personalized recommendations"""
    user_id: str
    viewed_transcripts: List[str]
    favorite_topics: List[str]
    language_preferences: List[str]
    avg_session_duration: float
    last_active: datetime
    interaction_history: List[Dict[str, Any]]


class RecommendationEngine:
    """Main recommendation engine combining multiple strategies"""
    
    def __init__(self, 
                 db_path: str = "recommendations.db",
                 embeddings_manager=None,
                 min_confidence: float = 0.6):
        self.db_path = db_path
        self.embeddings_manager = embeddings_manager
        self.min_confidence = min_confidence
        
        # Initialize database
        self._init_db()
        
    def _init_db(self):
        """Initialize recommendation database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # User interaction history
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    transcript_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,  -- 'view', 'like', 'share', 'complete'
                    duration_seconds INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # User profiles
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    favorite_topics TEXT,  -- JSON array
                    language_preferences TEXT,  -- JSON array
                    avg_session_duration REAL,
                    total_viewed INTEGER DEFAULT 0,
                    last_active TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Content metadata for recommendations
            conn.execute("""
                CREATE TABLE IF NOT EXISTS content_metadata (
                    transcript_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    topics TEXT,  -- JSON array
                    language TEXT,
                    duration_seconds INTEGER,
                    view_count INTEGER DEFAULT 0,
                    like_count INTEGER DEFAULT 0,
                    avg_completion_rate REAL DEFAULT 0.0,
                    entity_types TEXT,  -- JSON array
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Trending topics
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trending_topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    score REAL NOT NULL,
                    transcript_count INTEGER,
                    view_count INTEGER,
                    time_window TEXT,  -- 'daily', 'weekly', 'monthly'
                    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Content gaps
            conn.execute("""
                CREATE TABLE IF NOT EXISTS content_gaps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic_combination TEXT NOT NULL,  -- JSON array of topics
                    gap_score REAL NOT NULL,
                    potential_audience INTEGER,
                    identified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_interactions_user ON user_interactions(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_interactions_transcript ON user_interactions(transcript_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_interactions_timestamp ON user_interactions(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trending_topics_score ON trending_topics(score DESC)")
            
            conn.commit()
    
    def track_interaction(self, 
                         user_id: str,
                         transcript_id: str,
                         action_type: str,
                         duration_seconds: Optional[int] = None,
                         metadata: Optional[Dict[str, Any]] = None):
        """Track user interaction with content"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert interaction
                cursor.execute("""
                    INSERT INTO user_interactions 
                    (user_id, transcript_id, action_type, duration_seconds, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    user_id,
                    transcript_id,
                    action_type,
                    duration_seconds,
                    json.dumps(metadata or {})
                ))
                
                # Update user profile
                self._update_user_profile(cursor, user_id)
                
                # Update content metadata
                self._update_content_metadata(cursor, transcript_id, action_type)
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error tracking interaction: {e}")
    
    def get_recommendations(self,
                          user_id: str,
                          limit: int = 10,
                          recommendation_types: Optional[List[str]] = None) -> List[Recommendation]:
        """Get personalized recommendations for a user"""
        if recommendation_types is None:
            recommendation_types = ['content_based', 'collaborative', 'trending', 'personalized']
        
        all_recommendations = []
        
        # Get user profile
        user_profile = self._get_user_profile(user_id)
        
        # Content-based recommendations
        if 'content_based' in recommendation_types:
            content_recs = self._get_content_based_recommendations(user_profile, limit)
            all_recommendations.extend(content_recs)
        
        # Collaborative filtering recommendations
        if 'collaborative' in recommendation_types:
            collab_recs = self._get_collaborative_recommendations(user_profile, limit)
            all_recommendations.extend(collab_recs)
        
        # Trending content recommendations
        if 'trending' in recommendation_types:
            trending_recs = self._get_trending_recommendations(user_profile, limit)
            all_recommendations.extend(trending_recs)
        
        # Personalized recommendations based on user history
        if 'personalized' in recommendation_types:
            personal_recs = self._get_personalized_recommendations(user_profile, limit)
            all_recommendations.extend(personal_recs)
        
        # Combine and rank recommendations
        final_recommendations = self._rank_recommendations(all_recommendations, limit)
        
        return final_recommendations
    
    def get_similar_content(self,
                          transcript_id: str,
                          limit: int = 5) -> List[Recommendation]:
        """Get content similar to a specific transcript"""
        try:
            # Use embeddings if available
            if self.embeddings_manager:
                similar_transcripts = self.embeddings_manager.find_similar_content(
                    transcript_id, limit=limit, min_similarity=self.min_confidence
                )
                
                recommendations = []
                for similar in similar_transcripts:
                    recommendations.append(Recommendation(
                        transcript_id=similar.transcript_id,
                        title=similar.title,
                        score=similar.similarity_score,
                        recommendation_type='content_based',
                        reason=f'Similar content based on semantic analysis',
                        metadata={'similarity_score': similar.similarity_score}
                    ))
                
                return recommendations
            
            # Fallback to metadata-based similarity
            return self._get_metadata_based_similar_content(transcript_id, limit)
            
        except Exception as e:
            logger.error(f"Error getting similar content: {e}")
            return []
    
    def get_trending_topics(self,
                          time_window: str = 'daily',
                          limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending topics across all content"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Calculate trending topics
                self._calculate_trending_topics(cursor, time_window)
                
                # Retrieve trending topics
                cursor.execute("""
                    SELECT topic, score, transcript_count, view_count
                    FROM trending_topics
                    WHERE time_window = ?
                    ORDER BY score DESC
                    LIMIT ?
                """, (time_window, limit))
                
                topics = []
                for row in cursor.fetchall():
                    topics.append({
                        'topic': row[0],
                        'score': row[1],
                        'transcript_count': row[2],
                        'view_count': row[3],
                        'trend': self._calculate_trend(cursor, row[0], time_window)
                    })
                
                return topics
                
        except Exception as e:
            logger.error(f"Error getting trending topics: {e}")
            return []
    
    def analyze_content_gaps(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Analyze gaps in content coverage"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all topics and their combinations
                cursor.execute("""
                    SELECT topics FROM content_metadata
                    WHERE topics IS NOT NULL
                """)
                
                all_topics = []
                topic_combinations = defaultdict(int)
                
                for row in cursor.fetchall():
                    topics = json.loads(row[0])
                    all_topics.extend(topics)
                    
                    # Generate topic combinations
                    for i in range(len(topics)):
                        for j in range(i + 1, len(topics)):
                            combo = tuple(sorted([topics[i], topics[j]]))
                            topic_combinations[combo] += 1
                
                # Find missing combinations
                topic_counts = Counter(all_topics)
                popular_topics = [topic for topic, _ in topic_counts.most_common(20)]
                
                gaps = []
                for i in range(len(popular_topics)):
                    for j in range(i + 1, len(popular_topics)):
                        combo = tuple(sorted([popular_topics[i], popular_topics[j]]))
                        
                        if topic_combinations[combo] < 2:  # Gap threshold
                            gap_score = (topic_counts[popular_topics[i]] + 
                                       topic_counts[popular_topics[j]]) / 2
                            
                            gaps.append({
                                'topics': list(combo),
                                'gap_score': gap_score,
                                'current_count': topic_combinations[combo],
                                'potential_audience': int(gap_score * 10)  # Estimate
                            })
                
                # Sort by gap score and limit
                gaps.sort(key=lambda x: x['gap_score'], reverse=True)
                
                # Store in database
                cursor.execute("DELETE FROM content_gaps")
                for gap in gaps[:limit]:
                    cursor.execute("""
                        INSERT INTO content_gaps 
                        (topic_combination, gap_score, potential_audience)
                        VALUES (?, ?, ?)
                    """, (
                        json.dumps(gap['topics']),
                        gap['gap_score'],
                        gap['potential_audience']
                    ))
                
                conn.commit()
                
                return gaps[:limit]
                
        except Exception as e:
            logger.error(f"Error analyzing content gaps: {e}")
            return []
    
    def get_smart_tags(self, 
                      transcript_id: str,
                      content: Optional[str] = None,
                      limit: int = 10) -> List[Dict[str, Any]]:
        """Get smart tag suggestions for content"""
        try:
            tags = []
            
            # Get existing tags and topics
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT topics FROM content_metadata
                    WHERE transcript_id = ?
                """, (transcript_id,))
                
                result = cursor.fetchone()
                existing_topics = json.loads(result[0]) if result and result[0] else []
            
            # Analyze content if provided
            if content:
                # Extract entities and topics from content
                content_tags = self._extract_tags_from_content(content)
                tags.extend(content_tags)
            
            # Get related tags from similar content
            similar_content = self.get_similar_content(transcript_id, limit=5)
            for rec in similar_content:
                similar_tags = self._get_content_tags(rec.transcript_id)
                for tag in similar_tags:
                    if tag not in existing_topics:
                        tags.append({
                            'tag': tag,
                            'confidence': rec.score * 0.8,
                            'source': 'similar_content'
                        })
            
            # Get trending tags
            trending_topics = self.get_trending_topics(limit=20)
            for topic in trending_topics:
                if topic['topic'] not in existing_topics:
                    tags.append({
                        'tag': topic['topic'],
                        'confidence': min(topic['score'] / 100, 0.9),
                        'source': 'trending'
                    })
            
            # Deduplicate and sort by confidence
            unique_tags = {}
            for tag in tags:
                if tag['tag'] not in unique_tags or tag['confidence'] > unique_tags[tag['tag']]['confidence']:
                    unique_tags[tag['tag']] = tag
            
            final_tags = list(unique_tags.values())
            final_tags.sort(key=lambda x: x['confidence'], reverse=True)
            
            return final_tags[:limit]
            
        except Exception as e:
            logger.error(f"Error getting smart tags: {e}")
            return []
    
    def _get_content_based_recommendations(self, 
                                         user_profile: UserProfile,
                                         limit: int) -> List[Recommendation]:
        """Get recommendations based on content similarity"""
        recommendations = []
        
        if not user_profile.viewed_transcripts:
            return recommendations
        
        try:
            # Get embeddings-based recommendations if available
            if self.embeddings_manager:
                recs = self.embeddings_manager.get_content_recommendations(
                    user_profile.viewed_transcripts[-10:],  # Last 10 viewed
                    limit=limit
                )
                
                for rec in recs:
                    recommendations.append(Recommendation(
                        transcript_id=rec.transcript_id,
                        title=rec.title,
                        score=rec.similarity_score,
                        recommendation_type='content_based',
                        reason='Based on your viewing history',
                        metadata={'matching_chunks': rec.matching_chunks}
                    ))
            
            else:
                # Fallback to metadata-based recommendations
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Get topics from viewed content
                    viewed_topics = []
                    for transcript_id in user_profile.viewed_transcripts[-5:]:
                        cursor.execute("""
                            SELECT topics FROM content_metadata
                            WHERE transcript_id = ?
                        """, (transcript_id,))
                        
                        result = cursor.fetchone()
                        if result and result[0]:
                            viewed_topics.extend(json.loads(result[0]))
                    
                    # Find content with similar topics
                    topic_counts = Counter(viewed_topics)
                    
                    cursor.execute("""
                        SELECT transcript_id, title, topics
                        FROM content_metadata
                        WHERE transcript_id NOT IN ({})
                    """.format(','.join(['?'] * len(user_profile.viewed_transcripts))),
                    user_profile.viewed_transcripts)
                    
                    for row in cursor.fetchall():
                        if row[2]:
                            content_topics = json.loads(row[2])
                            similarity = sum(topic_counts.get(topic, 0) for topic in content_topics)
                            
                            if similarity > 0:
                                recommendations.append(Recommendation(
                                    transcript_id=row[0],
                                    title=row[1],
                                    score=min(similarity / len(viewed_topics), 1.0),
                                    recommendation_type='content_based',
                                    reason='Similar topics to your recent views',
                                    metadata={'common_topics': list(set(content_topics) & set(viewed_topics))}
                                ))
            
            recommendations.sort(key=lambda x: x.score, reverse=True)
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error getting content-based recommendations: {e}")
            return []
    
    def _get_collaborative_recommendations(self,
                                         user_profile: UserProfile,
                                         limit: int) -> List[Recommendation]:
        """Get recommendations based on similar users' behavior"""
        recommendations = []
        
        if not user_profile.viewed_transcripts:
            return recommendations
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Find users with similar viewing patterns
                cursor.execute("""
                    SELECT user_id, COUNT(*) as common_views
                    FROM user_interactions
                    WHERE transcript_id IN ({})
                    AND user_id != ?
                    GROUP BY user_id
                    ORDER BY common_views DESC
                    LIMIT 10
                """.format(','.join(['?'] * len(user_profile.viewed_transcripts))),
                user_profile.viewed_transcripts + [user_profile.user_id])
                
                similar_users = [row[0] for row in cursor.fetchall()]
                
                if similar_users:
                    # Get content viewed by similar users
                    cursor.execute("""
                        SELECT ui.transcript_id, cm.title, COUNT(*) as view_count
                        FROM user_interactions ui
                        JOIN content_metadata cm ON ui.transcript_id = cm.transcript_id
                        WHERE ui.user_id IN ({})
                        AND ui.transcript_id NOT IN ({})
                        AND ui.action_type IN ('view', 'complete')
                        GROUP BY ui.transcript_id, cm.title
                        ORDER BY view_count DESC
                        LIMIT ?
                    """.format(
                        ','.join(['?'] * len(similar_users)),
                        ','.join(['?'] * len(user_profile.viewed_transcripts))
                    ), similar_users + user_profile.viewed_transcripts + [limit])
                    
                    for row in cursor.fetchall():
                        recommendations.append(Recommendation(
                            transcript_id=row[0],
                            title=row[1],
                            score=min(row[2] / len(similar_users), 1.0),
                            recommendation_type='collaborative',
                            reason='Popular with users like you',
                            metadata={'similar_user_count': row[2]}
                        ))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting collaborative recommendations: {e}")
            return []
    
    def _get_trending_recommendations(self,
                                    user_profile: UserProfile,
                                    limit: int) -> List[Recommendation]:
        """Get recommendations based on trending content"""
        recommendations = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get recently popular content
                time_window = datetime.now() - timedelta(days=7)
                
                cursor.execute("""
                    SELECT ui.transcript_id, cm.title, 
                           COUNT(*) as recent_views,
                           AVG(CASE WHEN ui.action_type = 'complete' THEN 1 ELSE 0 END) as completion_rate
                    FROM user_interactions ui
                    JOIN content_metadata cm ON ui.transcript_id = cm.transcript_id
                    WHERE ui.timestamp > ?
                    AND ui.transcript_id NOT IN ({})
                    GROUP BY ui.transcript_id, cm.title
                    HAVING recent_views > 5
                    ORDER BY recent_views * completion_rate DESC
                    LIMIT ?
                """.format(','.join(['?'] * len(user_profile.viewed_transcripts))),
                [time_window] + user_profile.viewed_transcripts + [limit])
                
                for row in cursor.fetchall():
                    score = min((row[2] / 100) * row[3], 1.0)  # Normalize score
                    
                    recommendations.append(Recommendation(
                        transcript_id=row[0],
                        title=row[1],
                        score=score,
                        recommendation_type='trending',
                        reason='Trending this week',
                        metadata={
                            'recent_views': row[2],
                            'completion_rate': row[3]
                        }
                    ))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting trending recommendations: {e}")
            return []
    
    def _get_personalized_recommendations(self,
                                        user_profile: UserProfile,
                                        limit: int) -> List[Recommendation]:
        """Get personalized recommendations based on user preferences"""
        recommendations = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get content matching user's favorite topics
                if user_profile.favorite_topics:
                    topic_conditions = []
                    params = []
                    
                    for topic in user_profile.favorite_topics:
                        topic_conditions.append("topics LIKE ?")
                        params.append(f'%"{topic}"%')
                    
                    cursor.execute("""
                        SELECT transcript_id, title, topics
                        FROM content_metadata
                        WHERE ({})
                        AND transcript_id NOT IN ({})
                        ORDER BY view_count DESC
                        LIMIT ?
                    """.format(
                        ' OR '.join(topic_conditions),
                        ','.join(['?'] * len(user_profile.viewed_transcripts))
                    ), params + user_profile.viewed_transcripts + [limit])
                    
                    for row in cursor.fetchall():
                        topics = json.loads(row[2]) if row[2] else []
                        matching_topics = [t for t in topics if t in user_profile.favorite_topics]
                        
                        recommendations.append(Recommendation(
                            transcript_id=row[0],
                            title=row[1],
                            score=len(matching_topics) / len(user_profile.favorite_topics),
                            recommendation_type='personalized',
                            reason=f'Matches your interest in {", ".join(matching_topics)}',
                            metadata={'matching_topics': matching_topics}
                        ))
                
                # Get content in user's preferred languages
                if user_profile.language_preferences:
                    cursor.execute("""
                        SELECT transcript_id, title, language
                        FROM content_metadata
                        WHERE language IN ({})
                        AND transcript_id NOT IN ({})
                        ORDER BY created_at DESC
                        LIMIT ?
                    """.format(
                        ','.join(['?'] * len(user_profile.language_preferences)),
                        ','.join(['?'] * len(user_profile.viewed_transcripts))
                    ), user_profile.language_preferences + user_profile.viewed_transcripts + [limit])
                    
                    for row in cursor.fetchall():
                        recommendations.append(Recommendation(
                            transcript_id=row[0],
                            title=row[1],
                            score=0.7,  # Base score for language match
                            recommendation_type='personalized',
                            reason=f'In your preferred language: {row[2]}',
                            metadata={'language': row[2]}
                        ))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting personalized recommendations: {e}")
            return []
    
    def _rank_recommendations(self,
                            recommendations: List[Recommendation],
                            limit: int) -> List[Recommendation]:
        """Rank and deduplicate recommendations"""
        # Deduplicate by transcript_id, keeping highest score
        unique_recs = {}
        for rec in recommendations:
            if rec.transcript_id not in unique_recs or rec.score > unique_recs[rec.transcript_id].score:
                unique_recs[rec.transcript_id] = rec
        
        # Apply diversity bonus to mix recommendation types
        type_counts = defaultdict(int)
        for rec in unique_recs.values():
            diversity_penalty = type_counts[rec.recommendation_type] * 0.1
            rec.score = rec.score * (1 - diversity_penalty)
            type_counts[rec.recommendation_type] += 1
        
        # Sort by score and return top N
        final_recs = list(unique_recs.values())
        final_recs.sort(key=lambda x: x.score, reverse=True)
        
        return final_recs[:limit]
    
    def _get_user_profile(self, user_id: str) -> UserProfile:
        """Get or create user profile"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get user profile
            cursor.execute("""
                SELECT favorite_topics, language_preferences, avg_session_duration, last_active
                FROM user_profiles
                WHERE user_id = ?
            """, (user_id,))
            
            profile_row = cursor.fetchone()
            
            # Get viewed transcripts
            cursor.execute("""
                SELECT DISTINCT transcript_id
                FROM user_interactions
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 50
            """, (user_id,))
            
            viewed_transcripts = [row[0] for row in cursor.fetchall()]
            
            # Get interaction history
            cursor.execute("""
                SELECT transcript_id, action_type, duration_seconds, timestamp
                FROM user_interactions
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 100
            """, (user_id,))
            
            interactions = []
            for row in cursor.fetchall():
                interactions.append({
                    'transcript_id': row[0],
                    'action_type': row[1],
                    'duration_seconds': row[2],
                    'timestamp': row[3]
                })
            
            if profile_row:
                return UserProfile(
                    user_id=user_id,
                    viewed_transcripts=viewed_transcripts,
                    favorite_topics=json.loads(profile_row[0]) if profile_row[0] else [],
                    language_preferences=json.loads(profile_row[1]) if profile_row[1] else [],
                    avg_session_duration=profile_row[2] or 0,
                    last_active=datetime.fromisoformat(profile_row[3]) if profile_row[3] else datetime.now(),
                    interaction_history=interactions
                )
            else:
                # Create default profile
                return UserProfile(
                    user_id=user_id,
                    viewed_transcripts=viewed_transcripts,
                    favorite_topics=[],
                    language_preferences=['en'],
                    avg_session_duration=0,
                    last_active=datetime.now(),
                    interaction_history=interactions
                )
    
    def _update_user_profile(self, cursor, user_id: str):
        """Update user profile based on interactions"""
        # Calculate favorite topics from recent interactions
        cursor.execute("""
            SELECT cm.topics
            FROM user_interactions ui
            JOIN content_metadata cm ON ui.transcript_id = cm.transcript_id
            WHERE ui.user_id = ?
            AND ui.timestamp > datetime('now', '-30 days')
            AND cm.topics IS NOT NULL
        """, (user_id,))
        
        all_topics = []
        for row in cursor.fetchall():
            topics = json.loads(row[0])
            all_topics.extend(topics)
        
        topic_counts = Counter(all_topics)
        favorite_topics = [topic for topic, _ in topic_counts.most_common(5)]
        
        # Calculate average session duration
        cursor.execute("""
            SELECT AVG(duration_seconds)
            FROM user_interactions
            WHERE user_id = ?
            AND action_type = 'complete'
            AND duration_seconds IS NOT NULL
        """, (user_id,))
        
        avg_duration = cursor.fetchone()[0] or 0
        
        # Update profile
        cursor.execute("""
            INSERT OR REPLACE INTO user_profiles
            (user_id, favorite_topics, avg_session_duration, last_active, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, json.dumps(favorite_topics), avg_duration, datetime.now().isoformat()))
    
    def _update_content_metadata(self, cursor, transcript_id: str, action_type: str):
        """Update content metadata based on interaction"""
        if action_type == 'view':
            cursor.execute("""
                UPDATE content_metadata
                SET view_count = view_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE transcript_id = ?
            """, (transcript_id,))
        
        elif action_type == 'like':
            cursor.execute("""
                UPDATE content_metadata
                SET like_count = like_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE transcript_id = ?
            """, (transcript_id,))
        
        elif action_type == 'complete':
            # Update completion rate
            cursor.execute("""
                SELECT COUNT(*) as total_views,
                       SUM(CASE WHEN action_type = 'complete' THEN 1 ELSE 0 END) as completions
                FROM user_interactions
                WHERE transcript_id = ?
            """, (transcript_id,))
            
            result = cursor.fetchone()
            if result and result[0] > 0:
                completion_rate = result[1] / result[0]
                
                cursor.execute("""
                    UPDATE content_metadata
                    SET avg_completion_rate = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE transcript_id = ?
                """, (completion_rate, transcript_id))
    
    def _calculate_trending_topics(self, cursor, time_window: str):
        """Calculate trending topics for the specified time window"""
        # Determine time range
        if time_window == 'daily':
            time_range = datetime.now() - timedelta(days=1)
        elif time_window == 'weekly':
            time_range = datetime.now() - timedelta(days=7)
        else:  # monthly
            time_range = datetime.now() - timedelta(days=30)
        
        # Get topic interactions in time window
        cursor.execute("""
            SELECT cm.topics, COUNT(*) as interaction_count
            FROM user_interactions ui
            JOIN content_metadata cm ON ui.transcript_id = cm.transcript_id
            WHERE ui.timestamp > ?
            AND cm.topics IS NOT NULL
            GROUP BY ui.transcript_id
        """, (time_range,))
        
        topic_scores = defaultdict(float)
        topic_counts = defaultdict(int)
        
        for row in cursor.fetchall():
            topics = json.loads(row[0])
            interaction_count = row[1]
            
            for topic in topics:
                topic_scores[topic] += interaction_count
                topic_counts[topic] += 1
        
        # Clear old trending data
        cursor.execute("DELETE FROM trending_topics WHERE time_window = ?", (time_window,))
        
        # Insert new trending topics
        for topic, score in topic_scores.items():
            cursor.execute("""
                INSERT INTO trending_topics
                (topic, score, transcript_count, view_count, time_window)
                VALUES (?, ?, ?, ?, ?)
            """, (topic, score, topic_counts[topic], int(score), time_window))
    
    def _calculate_trend(self, cursor, topic: str, time_window: str) -> str:
        """Calculate trend direction for a topic"""
        # Compare with previous period
        cursor.execute("""
            SELECT score
            FROM trending_topics
            WHERE topic = ?
            AND time_window = ?
            AND calculated_at < datetime('now', '-1 day')
            ORDER BY calculated_at DESC
            LIMIT 1
        """, (topic, time_window))
        
        previous_score = cursor.fetchone()
        
        if not previous_score:
            return 'new'
        
        cursor.execute("""
            SELECT score
            FROM trending_topics
            WHERE topic = ?
            AND time_window = ?
            ORDER BY calculated_at DESC
            LIMIT 1
        """, (topic, time_window))
        
        current_score = cursor.fetchone()[0]
        
        if current_score > previous_score[0] * 1.1:
            return 'up'
        elif current_score < previous_score[0] * 0.9:
            return 'down'
        else:
            return 'stable'
    
    def _get_metadata_based_similar_content(self, 
                                          transcript_id: str,
                                          limit: int) -> List[Recommendation]:
        """Get similar content based on metadata"""
        recommendations = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get source content metadata
                cursor.execute("""
                    SELECT topics, language, entity_types
                    FROM content_metadata
                    WHERE transcript_id = ?
                """, (transcript_id,))
                
                source_row = cursor.fetchone()
                if not source_row:
                    return recommendations
                
                source_topics = json.loads(source_row[0]) if source_row[0] else []
                source_language = source_row[1]
                source_entities = json.loads(source_row[2]) if source_row[2] else []
                
                # Find similar content
                cursor.execute("""
                    SELECT transcript_id, title, topics, language, entity_types
                    FROM content_metadata
                    WHERE transcript_id != ?
                """, (transcript_id,))
                
                for row in cursor.fetchall():
                    similarity_score = 0
                    reasons = []
                    
                    # Topic similarity
                    if row[2]:
                        topics = json.loads(row[2])
                        common_topics = set(source_topics) & set(topics)
                        if common_topics:
                            similarity_score += len(common_topics) / max(len(source_topics), 1)
                            reasons.append(f"Similar topics: {', '.join(common_topics)}")
                    
                    # Language match
                    if row[3] == source_language:
                        similarity_score += 0.2
                        reasons.append(f"Same language: {source_language}")
                    
                    # Entity type similarity
                    if row[4] and source_entities:
                        entities = json.loads(row[4])
                        common_entities = set(source_entities) & set(entities)
                        if common_entities:
                            similarity_score += 0.1 * len(common_entities)
                            reasons.append(f"Similar entities: {', '.join(common_entities)}")
                    
                    if similarity_score >= self.min_confidence:
                        recommendations.append(Recommendation(
                            transcript_id=row[0],
                            title=row[1],
                            score=min(similarity_score, 1.0),
                            recommendation_type='content_based',
                            reason='; '.join(reasons),
                            metadata={'similarity_components': reasons}
                        ))
                
                recommendations.sort(key=lambda x: x.score, reverse=True)
                return recommendations[:limit]
                
        except Exception as e:
            logger.error(f"Error getting metadata-based similar content: {e}")
            return []
    
    def _extract_tags_from_content(self, content: str) -> List[Dict[str, Any]]:
        """Extract smart tags from content text"""
        tags = []
        
        # Simple keyword extraction (can be enhanced with NLP)
        words = content.lower().split()
        word_freq = Counter(words)
        
        # Filter common words and extract keywords
        common_words = {'the', 'is', 'at', 'in', 'on', 'and', 'a', 'to', 'of', 'for', 'with', 'as', 'by'}
        keywords = [word for word, count in word_freq.most_common(20) 
                   if word not in common_words and len(word) > 3 and count > 1]
        
        for keyword in keywords[:10]:
            tags.append({
                'tag': keyword.title(),
                'confidence': min(word_freq[keyword] / len(words), 0.8),
                'source': 'content_analysis'
            })
        
        return tags
    
    def _get_content_tags(self, transcript_id: str) -> List[str]:
        """Get tags/topics for a transcript"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT topics FROM content_metadata
                    WHERE transcript_id = ?
                """, (transcript_id,))
                
                result = cursor.fetchone()
                if result and result[0]:
                    return json.loads(result[0])
                
                return []
                
        except Exception as e:
            logger.error(f"Error getting content tags: {e}")
            return []
    
    def add_content_metadata(self,
                           transcript_id: str,
                           title: str,
                           topics: List[str],
                           language: str,
                           duration_seconds: Optional[int] = None,
                           entity_types: Optional[List[str]] = None,
                           created_at: Optional[datetime] = None):
        """Add or update content metadata"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO content_metadata
                    (transcript_id, title, topics, language, duration_seconds, 
                     entity_types, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    transcript_id,
                    title,
                    json.dumps(topics),
                    language,
                    duration_seconds,
                    json.dumps(entity_types or []),
                    (created_at or datetime.now()).isoformat()
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error adding content metadata: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get recommendation engine statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # User statistics
                cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_interactions")
                stats['total_users'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM user_interactions")
                stats['total_interactions'] = cursor.fetchone()[0]
                
                # Content statistics  
                cursor.execute("SELECT COUNT(*) FROM content_metadata")
                stats['total_content'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT AVG(view_count) FROM content_metadata")
                stats['avg_views_per_content'] = cursor.fetchone()[0] or 0
                
                # Trending statistics
                cursor.execute("SELECT COUNT(*) FROM trending_topics WHERE time_window = 'daily'")
                stats['daily_trending_topics'] = cursor.fetchone()[0]
                
                # Gap analysis
                cursor.execute("SELECT COUNT(*) FROM content_gaps")
                stats['identified_content_gaps'] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}