"""
Task 202: Advanced User Engagement Analytics System
Comprehensive system for tracking user behavior, engagement patterns,
and providing predictive analytics for user retention and experience optimization
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd
from sqlalchemy import (
    Boolean, Column, DateTime, Float, Integer, JSON, String, Text,
    create_engine, ForeignKey, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

Base = declarative_base()

# Enums
class EventType(Enum):
    """User event types"""
    PAGE_VIEW = "page_view"
    CLICK = "click"
    FORM_SUBMIT = "form_submit"
    DOWNLOAD = "download"
    SEARCH = "search"
    UPLOAD = "upload"
    TRANSCRIPTION_START = "transcription_start"
    TRANSCRIPTION_COMPLETE = "transcription_complete"
    FEATURE_USE = "feature_use"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    ERROR = "error"
    HELP_VIEW = "help_view"

class EngagementLevel(Enum):
    """User engagement levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INACTIVE = "inactive"

class UserSegment(Enum):
    """User behavior segments"""
    POWER_USER = "power_user"
    REGULAR_USER = "regular_user"
    OCCASIONAL_USER = "occasional_user"
    NEW_USER = "new_user"
    CHURNING_USER = "churning_user"

# Database Models
class UserEvent(Base):
    """User behavior events tracking"""
    __tablename__ = "user_events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    session_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    event_category = Column(String, nullable=True)
    event_action = Column(String, nullable=True)
    event_label = Column(String, nullable=True)
    page_url = Column(String, nullable=True)
    page_title = Column(String, nullable=True)
    referrer = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    properties = Column(JSON, nullable=True)
    duration = Column(Float, nullable=True)  # Event duration in seconds
    value = Column(Float, nullable=True)  # Event value/score
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_event_type_timestamp', 'event_type', 'timestamp'),
        Index('idx_session_timestamp', 'session_id', 'timestamp'),
    )

class UserSession(Base):
    """User session tracking"""
    __tablename__ = "user_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    session_id = Column(String, nullable=False, unique=True, index=True)
    start_time = Column(DateTime, default=datetime.utcnow, index=True)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)  # Session duration in seconds
    page_views = Column(Integer, default=0)
    events_count = Column(Integer, default=0)
    bounce_rate = Column(Float, nullable=True)
    entry_page = Column(String, nullable=True)
    exit_page = Column(String, nullable=True)
    referrer = Column(String, nullable=True)
    device_type = Column(String, nullable=True)
    browser = Column(String, nullable=True)
    os = Column(String, nullable=True)
    location = Column(JSON, nullable=True)  # Geographic data
    engagement_score = Column(Float, default=0.0)

class UserBehaviorProfile(Base):
    """User behavior analysis profile"""
    __tablename__ = "user_behavior_profiles"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Engagement metrics
    total_sessions = Column(Integer, default=0)
    total_events = Column(Integer, default=0)
    total_time_spent = Column(Float, default=0.0)  # Total time in seconds
    avg_session_duration = Column(Float, default=0.0)
    avg_events_per_session = Column(Float, default=0.0)
    last_activity = Column(DateTime, nullable=True)
    days_since_signup = Column(Integer, default=0)
    days_since_last_activity = Column(Integer, default=0)
    
    # Feature usage
    features_used = Column(JSON, default=list)
    most_used_features = Column(JSON, default=list)
    transcription_minutes = Column(Float, default=0.0)
    uploads_count = Column(Integer, default=0)
    downloads_count = Column(Integer, default=0)
    searches_count = Column(Integer, default=0)
    
    # Behavior patterns
    preferred_time_of_day = Column(String, nullable=True)  # morning, afternoon, evening
    preferred_days = Column(JSON, default=list)  # List of preferred weekdays
    user_segment = Column(String, default=UserSegment.NEW_USER.value)
    engagement_level = Column(String, default=EngagementLevel.LOW.value)
    churn_risk_score = Column(Float, default=0.0)  # 0-1 probability of churning
    
    # Predictive scores
    retention_score = Column(Float, default=0.5)
    growth_potential = Column(Float, default=0.5)
    feature_adoption_rate = Column(Float, default=0.0)

class UserJourney(Base):
    """User journey mapping"""
    __tablename__ = "user_journeys"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    journey_id = Column(String, nullable=False, index=True)
    journey_type = Column(String, nullable=False)  # onboarding, feature_discovery, etc.
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    completed = Column(Boolean, default=False)
    steps_completed = Column(Integer, default=0)
    total_steps = Column(Integer, nullable=False)
    completion_rate = Column(Float, default=0.0)
    time_to_complete = Column(Float, nullable=True)
    drop_off_point = Column(String, nullable=True)
    journey_data = Column(JSON, default=dict)

@dataclass
class EngagementInsight:
    """User engagement insight"""
    insight_type: str
    title: str
    description: str
    metric_value: float
    trend: str  # increasing, decreasing, stable
    confidence: float
    recommendations: List[str]
    data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UserSegmentAnalysis:
    """User segment analysis result"""
    segment: str
    user_count: int
    avg_engagement_score: float
    retention_rate: float
    avg_session_duration: float
    top_features: List[str]
    characteristics: List[str]
    recommendations: List[str]

class UserEngagementAnalytics:
    """Main user engagement analytics service"""
    
    def __init__(self, database_url: str = "sqlite:///user_engagement.db"):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    async def track_event(
        self, 
        user_id: str, 
        session_id: str,
        event_type: EventType,
        properties: Dict[str, Any] = None,
        duration: float = None,
        value: float = None
    ) -> str:
        """Track a user event"""
        db = self.SessionLocal()
        try:
            event = UserEvent(
                user_id=user_id,
                session_id=session_id,
                event_type=event_type.value,
                event_category=properties.get('category') if properties else None,
                event_action=properties.get('action') if properties else None,
                event_label=properties.get('label') if properties else None,
                page_url=properties.get('page_url') if properties else None,
                page_title=properties.get('page_title') if properties else None,
                referrer=properties.get('referrer') if properties else None,
                user_agent=properties.get('user_agent') if properties else None,
                ip_address=properties.get('ip_address') if properties else None,
                properties=properties or {},
                duration=duration,
                value=value
            )
            
            db.add(event)
            db.commit()
            
            # Update session
            await self._update_session(session_id, user_id, db)
            
            # Update user profile asynchronously
            asyncio.create_task(self._update_user_profile(user_id))
            
            return event.id
        finally:
            db.close()
    
    async def start_session(
        self, 
        user_id: str, 
        session_id: str,
        properties: Dict[str, Any] = None
    ) -> None:
        """Start a new user session"""
        db = self.SessionLocal()
        try:
            session = UserSession(
                user_id=user_id,
                session_id=session_id,
                entry_page=properties.get('entry_page') if properties else None,
                referrer=properties.get('referrer') if properties else None,
                device_type=properties.get('device_type') if properties else None,
                browser=properties.get('browser') if properties else None,
                os=properties.get('os') if properties else None,
                location=properties.get('location') if properties else None
            )
            
            db.add(session)
            db.commit()
            
            # Track session start event
            await self.track_event(
                user_id=user_id,
                session_id=session_id,
                event_type=EventType.SESSION_START,
                properties=properties
            )
        finally:
            db.close()
    
    async def end_session(self, session_id: str) -> None:
        """End a user session"""
        db = self.SessionLocal()
        try:
            session = db.query(UserSession).filter(
                UserSession.session_id == session_id
            ).first()
            
            if session:
                session.end_time = datetime.utcnow()
                if session.start_time:
                    session.duration = (session.end_time - session.start_time).total_seconds()
                
                # Calculate engagement score
                session.engagement_score = self._calculate_session_engagement(session, db)
                
                db.commit()
                
                # Track session end event
                await self.track_event(
                    user_id=session.user_id,
                    session_id=session_id,
                    event_type=EventType.SESSION_END,
                    duration=session.duration,
                    value=session.engagement_score
                )
        finally:
            db.close()
    
    async def analyze_user_behavior(self, user_id: str) -> Dict[str, Any]:
        """Comprehensive user behavior analysis"""
        db = self.SessionLocal()
        try:
            # Get user events and sessions
            events = db.query(UserEvent).filter(
                UserEvent.user_id == user_id
            ).order_by(UserEvent.timestamp.desc()).limit(1000).all()
            
            sessions = db.query(UserSession).filter(
                UserSession.user_id == user_id
            ).order_by(UserSession.start_time.desc()).limit(100).all()
            
            # Analyze patterns
            analysis = {
                'user_id': user_id,
                'total_events': len(events),
                'total_sessions': len(sessions),
                'event_patterns': self._analyze_event_patterns(events),
                'session_patterns': self._analyze_session_patterns(sessions),
                'feature_usage': self._analyze_feature_usage(events),
                'engagement_trends': self._analyze_engagement_trends(events, sessions),
                'behavioral_insights': self._generate_behavioral_insights(events, sessions),
                'recommendations': self._generate_user_recommendations(events, sessions)
            }
            
            return analysis
        finally:
            db.close()
    
    async def get_user_segment_analysis(self, date_range: int = 30) -> List[UserSegmentAnalysis]:
        """Analyze user segments and their characteristics"""
        db = self.SessionLocal()
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=date_range)
            
            # Get active users in the date range
            active_users = db.query(UserBehaviorProfile).filter(
                UserBehaviorProfile.last_activity >= start_date
            ).all()
            
            # Group by segments
            segments = {}
            for user in active_users:
                segment = user.user_segment
                if segment not in segments:
                    segments[segment] = []
                segments[segment].append(user)
            
            # Analyze each segment
            segment_analyses = []
            for segment, users in segments.items():
                analysis = self._analyze_user_segment(segment, users, db)
                segment_analyses.append(analysis)
            
            return segment_analyses
        finally:
            db.close()
    
    async def generate_engagement_insights(self, time_period: str = "30d") -> List[EngagementInsight]:
        """Generate actionable engagement insights"""
        db = self.SessionLocal()
        try:
            days = int(time_period.replace('d', ''))
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            insights = []
            
            # 1. Overall engagement trend
            engagement_trend = await self._analyze_engagement_trend(start_date, end_date, db)
            insights.append(engagement_trend)
            
            # 2. Feature adoption insights
            feature_insights = await self._analyze_feature_adoption(start_date, end_date, db)
            insights.extend(feature_insights)
            
            # 3. User retention insights
            retention_insight = await self._analyze_user_retention(start_date, end_date, db)
            insights.append(retention_insight)
            
            # 4. Churn risk insights
            churn_insight = await self._analyze_churn_risk(db)
            insights.append(churn_insight)
            
            # 5. User journey insights
            journey_insights = await self._analyze_user_journeys(start_date, end_date, db)
            insights.extend(journey_insights)
            
            return insights
        finally:
            db.close()
    
    async def predict_user_churn(self, user_id: str) -> Dict[str, Any]:
        """Predict user churn probability"""
        db = self.SessionLocal()
        try:
            profile = db.query(UserBehaviorProfile).filter(
                UserBehaviorProfile.user_id == user_id
            ).first()
            
            if not profile:
                return {"error": "User profile not found"}
            
            # Calculate churn risk factors
            factors = {
                'days_since_last_activity': profile.days_since_last_activity,
                'engagement_level': profile.engagement_level,
                'session_frequency_decline': self._calculate_session_frequency_decline(user_id, db),
                'feature_usage_decline': self._calculate_feature_usage_decline(user_id, db),
                'support_interactions': self._count_support_interactions(user_id, db)
            }
            
            # Simple churn prediction model
            churn_score = self._calculate_churn_score(factors)
            
            # Generate recommendations
            recommendations = self._generate_churn_prevention_recommendations(factors)
            
            return {
                'user_id': user_id,
                'churn_probability': churn_score,
                'risk_level': self._get_risk_level(churn_score),
                'risk_factors': factors,
                'recommendations': recommendations,
                'last_updated': datetime.utcnow().isoformat()
            }
        finally:
            db.close()
    
    async def get_real_time_analytics(self) -> Dict[str, Any]:
        """Get real-time engagement analytics"""
        db = self.SessionLocal()
        try:
            now = datetime.utcnow()
            last_hour = now - timedelta(hours=1)
            last_24h = now - timedelta(hours=24)
            
            # Real-time metrics
            metrics = {
                'timestamp': now.isoformat(),
                'active_users_last_hour': self._count_active_users(last_hour, now, db),
                'active_users_last_24h': self._count_active_users(last_24h, now, db),
                'events_last_hour': self._count_events(last_hour, now, db),
                'avg_session_duration_last_24h': self._avg_session_duration(last_24h, now, db),
                'top_pages_last_hour': self._get_top_pages(last_hour, now, db),
                'top_events_last_hour': self._get_top_events(last_hour, now, db),
                'real_time_users': self._count_real_time_users(db),
                'bounce_rate_last_24h': self._calculate_bounce_rate(last_24h, now, db)
            }
            
            return metrics
        finally:
            db.close()
    
    def _update_session(self, session_id: str, user_id: str, db) -> None:
        """Update session statistics"""
        session = db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()
        
        if session:
            # Count events in this session
            events_count = db.query(UserEvent).filter(
                UserEvent.session_id == session_id
            ).count()
            
            # Count page views
            page_views = db.query(UserEvent).filter(
                UserEvent.session_id == session_id,
                UserEvent.event_type == EventType.PAGE_VIEW.value
            ).count()
            
            session.events_count = events_count
            session.page_views = page_views
            db.commit()
    
    async def _update_user_profile(self, user_id: str) -> None:
        """Update user behavior profile"""
        db = self.SessionLocal()
        try:
            profile = db.query(UserBehaviorProfile).filter(
                UserBehaviorProfile.user_id == user_id
            ).first()
            
            if not profile:
                profile = UserBehaviorProfile(user_id=user_id)
                db.add(profile)
            
            # Update profile metrics
            await self._calculate_profile_metrics(profile, db)
            
            # Update engagement level and segment
            profile.engagement_level = self._determine_engagement_level(profile)
            profile.user_segment = self._determine_user_segment(profile)
            profile.churn_risk_score = self._calculate_churn_risk_score(profile, db)
            
            profile.updated_at = datetime.utcnow()
            db.commit()
        finally:
            db.close()
    
    def _calculate_session_engagement(self, session: UserSession, db) -> float:
        """Calculate session engagement score"""
        score = 0.0
        
        # Duration score (max 30 points)
        if session.duration:
            duration_minutes = session.duration / 60
            score += min(duration_minutes / 30 * 30, 30)
        
        # Page views score (max 25 points)
        score += min(session.page_views * 2, 25)
        
        # Events score (max 25 points)
        score += min(session.events_count * 1.5, 25)
        
        # Bounce rate penalty (max -20 points)
        if session.page_views <= 1:
            score -= 20
        
        return max(0, min(100, score))
    
    def _analyze_event_patterns(self, events: List[UserEvent]) -> Dict[str, Any]:
        """Analyze user event patterns"""
        if not events:
            return {}
        
        event_types = [e.event_type for e in events]
        event_counts = {}
        for event_type in event_types:
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        # Time-based patterns
        hourly_pattern = {}
        daily_pattern = {}
        
        for event in events:
            hour = event.timestamp.hour
            day = event.timestamp.strftime('%A')
            hourly_pattern[hour] = hourly_pattern.get(hour, 0) + 1
            daily_pattern[day] = daily_pattern.get(day, 0) + 1
        
        return {
            'event_counts': event_counts,
            'hourly_pattern': hourly_pattern,
            'daily_pattern': daily_pattern,
            'most_active_hour': max(hourly_pattern, key=hourly_pattern.get) if hourly_pattern else None,
            'most_active_day': max(daily_pattern, key=daily_pattern.get) if daily_pattern else None
        }
    
    def _analyze_session_patterns(self, sessions: List[UserSession]) -> Dict[str, Any]:
        """Analyze user session patterns"""
        if not sessions:
            return {}
        
        durations = [s.duration for s in sessions if s.duration]
        page_views = [s.page_views for s in sessions]
        
        return {
            'avg_duration': np.mean(durations) if durations else 0,
            'avg_page_views': np.mean(page_views) if page_views else 0,
            'total_sessions': len(sessions),
            'avg_engagement_score': np.mean([s.engagement_score for s in sessions if s.engagement_score]),
            'bounce_rate': len([s for s in sessions if s.page_views <= 1]) / len(sessions) if sessions else 0
        }
    
    def _analyze_feature_usage(self, events: List[UserEvent]) -> Dict[str, Any]:
        """Analyze feature usage patterns"""
        feature_events = [e for e in events if e.event_type == EventType.FEATURE_USE.value]
        
        feature_counts = {}
        for event in feature_events:
            feature = event.properties.get('feature_name') if event.properties else 'unknown'
            feature_counts[feature] = feature_counts.get(feature, 0) + 1
        
        return {
            'total_feature_uses': len(feature_events),
            'unique_features_used': len(feature_counts),
            'feature_usage_distribution': feature_counts,
            'most_used_feature': max(feature_counts, key=feature_counts.get) if feature_counts else None
        }
    
    def _analyze_engagement_trends(self, events: List[UserEvent], sessions: List[UserSession]) -> Dict[str, Any]:
        """Analyze engagement trends over time"""
        # Group events by date
        daily_events = {}
        for event in events:
            date = event.timestamp.date()
            daily_events[date] = daily_events.get(date, 0) + 1
        
        # Group sessions by date
        daily_sessions = {}
        for session in sessions:
            date = session.start_time.date()
            daily_sessions[date] = daily_sessions.get(date, 0) + 1
        
        # Calculate trend
        dates = sorted(daily_events.keys())
        if len(dates) >= 2:
            recent_avg = np.mean([daily_events[d] for d in dates[-7:]])
            older_avg = np.mean([daily_events[d] for d in dates[-14:-7]]) if len(dates) >= 14 else recent_avg
            trend = "increasing" if recent_avg > older_avg else "decreasing" if recent_avg < older_avg else "stable"
        else:
            trend = "insufficient_data"
        
        return {
            'daily_events': daily_events,
            'daily_sessions': daily_sessions,
            'trend': trend,
            'avg_events_per_day': np.mean(list(daily_events.values())) if daily_events else 0
        }
    
    def _generate_behavioral_insights(self, events: List[UserEvent], sessions: List[UserSession]) -> List[str]:
        """Generate behavioral insights for a user"""
        insights = []
        
        if not events:
            return ["No activity data available"]
        
        # Session frequency insight
        if len(sessions) > 0:
            avg_duration = np.mean([s.duration for s in sessions if s.duration])
            if avg_duration > 1800:  # 30 minutes
                insights.append("User has high engagement with long session durations")
            elif avg_duration < 300:  # 5 minutes
                insights.append("User sessions are short - may need better onboarding")
        
        # Feature usage insight
        feature_events = [e for e in events if e.event_type == EventType.FEATURE_USE.value]
        if len(feature_events) > 20:
            insights.append("Power user - frequently uses various features")
        elif len(feature_events) < 5:
            insights.append("Low feature adoption - may need feature discovery help")
        
        # Time pattern insight
        hours = [e.timestamp.hour for e in events]
        if hours:
            most_active_hour = max(set(hours), key=hours.count)
            if 9 <= most_active_hour <= 17:
                insights.append("Most active during business hours")
            elif 18 <= most_active_hour <= 23:
                insights.append("Most active during evening hours")
        
        return insights
    
    def _generate_user_recommendations(self, events: List[UserEvent], sessions: List[UserSession]) -> List[str]:
        """Generate recommendations for improving user experience"""
        recommendations = []
        
        if not events:
            return ["Encourage initial engagement with onboarding flow"]
        
        # Check for help-seeking behavior
        help_events = [e for e in events if e.event_type == EventType.HELP_VIEW.value]
        if len(help_events) > 3:
            recommendations.append("Provide proactive help or improved documentation")
        
        # Check for error events
        error_events = [e for e in events if e.event_type == EventType.ERROR.value]
        if len(error_events) > 5:
            recommendations.append("Investigate and fix common user errors")
        
        # Check for feature usage
        feature_events = [e for e in events if e.event_type == EventType.FEATURE_USE.value]
        if len(feature_events) < 10 and len(events) > 50:
            recommendations.append("Introduce feature discovery tutorials")
        
        # Check session patterns
        if sessions:
            bounce_rate = len([s for s in sessions if s.page_views <= 1]) / len(sessions)
            if bounce_rate > 0.7:
                recommendations.append("Improve landing page engagement and navigation")
        
        return recommendations
    
    def _analyze_user_segment(self, segment: str, users: List[UserBehaviorProfile], db) -> UserSegmentAnalysis:
        """Analyze characteristics of a user segment"""
        if not users:
            return UserSegmentAnalysis(
                segment=segment,
                user_count=0,
                avg_engagement_score=0,
                retention_rate=0,
                avg_session_duration=0,
                top_features=[],
                characteristics=[],
                recommendations=[]
            )
        
        # Calculate segment metrics
        avg_engagement = np.mean([u.total_events / max(u.total_sessions, 1) for u in users])
        avg_duration = np.mean([u.avg_session_duration for u in users])
        
        # Retention calculation (users active in last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        active_users = len([u for u in users if u.last_activity and u.last_activity >= week_ago])
        retention_rate = active_users / len(users) if users else 0
        
        # Top features used by this segment
        all_features = []
        for user in users:
            if user.most_used_features:
                all_features.extend(user.most_used_features)
        
        feature_counts = {}
        for feature in all_features:
            feature_counts[feature] = feature_counts.get(feature, 0) + 1
        
        top_features = sorted(feature_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_features = [f[0] for f in top_features]
        
        # Generate characteristics and recommendations
        characteristics = self._generate_segment_characteristics(segment, users)
        recommendations = self._generate_segment_recommendations(segment, users, retention_rate)
        
        return UserSegmentAnalysis(
            segment=segment,
            user_count=len(users),
            avg_engagement_score=avg_engagement,
            retention_rate=retention_rate,
            avg_session_duration=avg_duration,
            top_features=top_features,
            characteristics=characteristics,
            recommendations=recommendations
        )
    
    def _generate_segment_characteristics(self, segment: str, users: List[UserBehaviorProfile]) -> List[str]:
        """Generate characteristics for a user segment"""
        characteristics = []
        
        if segment == UserSegment.POWER_USER.value:
            avg_features = np.mean([len(u.most_used_features or []) for u in users])
            characteristics.append(f"Uses average of {avg_features:.1f} different features")
            characteristics.append("High session frequency and duration")
            characteristics.append("Low churn risk")
        
        elif segment == UserSegment.CHURNING_USER.value:
            avg_days_inactive = np.mean([u.days_since_last_activity for u in users])
            characteristics.append(f"Average {avg_days_inactive:.1f} days since last activity")
            characteristics.append("Declining engagement patterns")
            characteristics.append("High churn risk")
        
        return characteristics
    
    def _generate_segment_recommendations(self, segment: str, users: List[UserBehaviorProfile], retention_rate: float) -> List[str]:
        """Generate recommendations for a user segment"""
        recommendations = []
        
        if segment == UserSegment.POWER_USER.value:
            recommendations.append("Provide advanced features and beta access")
            recommendations.append("Leverage for user feedback and testimonials")
            recommendations.append("Offer referral incentives")
        
        elif segment == UserSegment.CHURNING_USER.value:
            recommendations.append("Implement re-engagement campaigns")
            recommendations.append("Provide personalized feature recommendations")
            recommendations.append("Offer customer success outreach")
        
        elif segment == UserSegment.NEW_USER.value:
            recommendations.append("Improve onboarding experience")
            recommendations.append("Provide guided feature tours")
            recommendations.append("Monitor early engagement patterns")
        
        return recommendations

    async def _analyze_engagement_trend(self, start_date: datetime, end_date: datetime, db) -> EngagementInsight:
        """Analyze overall engagement trends"""
        # Get events in date range
        events = db.query(UserEvent).filter(
            UserEvent.timestamp.between(start_date, end_date)
        ).all()
        
        # Calculate daily engagement
        daily_events = {}
        for event in events:
            date = event.timestamp.date()
            daily_events[date] = daily_events.get(date, 0) + 1
        
        # Determine trend
        if len(daily_events) >= 7:
            recent_avg = np.mean(list(daily_events.values())[-7:])
            older_avg = np.mean(list(daily_events.values())[:-7]) if len(daily_events) > 7 else recent_avg
            
            if recent_avg > older_avg * 1.1:
                trend = "increasing"
            elif recent_avg < older_avg * 0.9:
                trend = "decreasing"  
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        recommendations = []
        if trend == "decreasing":
            recommendations.extend([
                "Investigate causes of engagement decline",
                "Launch user re-engagement campaigns",
                "Review recent product changes"
            ])
        elif trend == "increasing":
            recommendations.extend([
                "Analyze successful engagement drivers",
                "Scale effective strategies",
                "Monitor for sustainability"
            ])
        
        return EngagementInsight(
            insight_type="engagement_trend",
            title="Overall Engagement Trend",
            description=f"User engagement is {trend} over the selected time period",
            metric_value=np.mean(list(daily_events.values())) if daily_events else 0,
            trend=trend,
            confidence=0.8,
            recommendations=recommendations,
            data={'daily_events': daily_events}
        )
    
    async def _analyze_feature_adoption(self, start_date: datetime, end_date: datetime, db) -> List[EngagementInsight]:
        """Analyze feature adoption patterns"""
        feature_events = db.query(UserEvent).filter(
            UserEvent.timestamp.between(start_date, end_date),
            UserEvent.event_type == EventType.FEATURE_USE.value
        ).all()
        
        # Count feature usage
        feature_counts = {}
        for event in feature_events:
            feature = event.properties.get('feature_name', 'unknown') if event.properties else 'unknown'
            feature_counts[feature] = feature_counts.get(feature, 0) + 1
        
        insights = []
        
        # Top features insight
        if feature_counts:
            top_feature = max(feature_counts, key=feature_counts.get)
            insights.append(EngagementInsight(
                insight_type="top_feature",
                title="Most Popular Feature",
                description=f"{top_feature} is the most used feature",
                metric_value=feature_counts[top_feature],
                trend="stable",
                confidence=0.9,
                recommendations=[
                    f"Promote similar features to {top_feature}",
                    "Study {top_feature} success patterns",
                    "Optimize {top_feature} experience further"
                ],
                data={'feature_counts': feature_counts}
            ))
        
        return insights
    
    async def _analyze_user_retention(self, start_date: datetime, end_date: datetime, db) -> EngagementInsight:
        """Analyze user retention patterns"""
        # Get users who were active at start of period
        initial_users = db.query(UserBehaviorProfile).filter(
            UserBehaviorProfile.last_activity >= start_date - timedelta(days=7)
        ).all()
        
        # Check how many are still active at end of period
        retained_users = [u for u in initial_users if u.last_activity >= end_date - timedelta(days=7)]
        
        retention_rate = len(retained_users) / len(initial_users) if initial_users else 0
        
        recommendations = []
        if retention_rate < 0.3:
            recommendations.extend([
                "Critical: Implement user retention strategy",
                "Analyze churn reasons",
                "Improve onboarding experience"
            ])
        elif retention_rate < 0.6:
            recommendations.extend([
                "Focus on user engagement improvements", 
                "Implement re-engagement campaigns",
                "Gather user feedback"
            ])
        
        return EngagementInsight(
            insight_type="user_retention",
            title="User Retention Analysis",
            description=f"User retention rate is {retention_rate:.1%}",
            metric_value=retention_rate,
            trend="stable",
            confidence=0.85,
            recommendations=recommendations,
            data={
                'initial_users': len(initial_users),
                'retained_users': len(retained_users)
            }
        )
    
    async def _analyze_churn_risk(self, db) -> EngagementInsight:
        """Analyze users at risk of churning"""
        high_risk_users = db.query(UserBehaviorProfile).filter(
            UserBehaviorProfile.churn_risk_score >= 0.7
        ).count()
        
        total_users = db.query(UserBehaviorProfile).count()
        risk_percentage = high_risk_users / total_users if total_users else 0
        
        recommendations = [
            "Implement targeted retention campaigns for high-risk users",
            "Analyze common patterns among at-risk users", 
            "Provide proactive customer success outreach"
        ]
        
        return EngagementInsight(
            insight_type="churn_risk",
            title="Churn Risk Analysis",
            description=f"{risk_percentage:.1%} of users are at high risk of churning",
            metric_value=risk_percentage,
            trend="stable",
            confidence=0.75,
            recommendations=recommendations,
            data={
                'high_risk_users': high_risk_users,
                'total_users': total_users
            }
        )
    
    async def _analyze_user_journeys(self, start_date: datetime, end_date: datetime, db) -> List[EngagementInsight]:
        """Analyze user journey completion patterns"""
        journeys = db.query(UserJourney).filter(
            UserJourney.start_time.between(start_date, end_date)
        ).all()
        
        insights = []
        
        if journeys:
            # Journey completion rates
            completed_journeys = [j for j in journeys if j.completed]
            completion_rate = len(completed_journeys) / len(journeys)
            
            insights.append(EngagementInsight(
                insight_type="journey_completion",
                title="User Journey Completion",
                description=f"{completion_rate:.1%} of user journeys are completed",
                metric_value=completion_rate,
                trend="stable",
                confidence=0.8,
                recommendations=[
                    "Identify and fix journey drop-off points",
                    "Simplify complex journey steps",
                    "Provide better guidance during journeys"
                ],
                data={
                    'total_journeys': len(journeys),
                    'completed_journeys': len(completed_journeys)
                }
            ))
        
        return insights
    
    def _calculate_churn_score(self, factors: Dict[str, Any]) -> float:
        """Calculate churn probability based on risk factors"""
        score = 0.0
        
        # Days since last activity (0-0.4)
        days_inactive = factors.get('days_since_last_activity', 0)
        if days_inactive > 30:
            score += 0.4
        elif days_inactive > 14:
            score += 0.3
        elif days_inactive > 7:
            score += 0.2
        elif days_inactive > 3:
            score += 0.1
        
        # Engagement level (0-0.3)
        engagement = factors.get('engagement_level', 'medium')
        if engagement == 'inactive':
            score += 0.3
        elif engagement == 'low':
            score += 0.2
        elif engagement == 'medium':
            score += 0.1
        
        # Session frequency decline (0-0.2)
        session_decline = factors.get('session_frequency_decline', 0)
        score += min(session_decline / 100 * 0.2, 0.2)
        
        # Feature usage decline (0-0.1) 
        feature_decline = factors.get('feature_usage_decline', 0)
        score += min(feature_decline / 100 * 0.1, 0.1)
        
        return min(1.0, score)
    
    def _get_risk_level(self, churn_score: float) -> str:
        """Determine risk level from churn score"""
        if churn_score >= 0.7:
            return "high"
        elif churn_score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _generate_churn_prevention_recommendations(self, factors: Dict[str, Any]) -> List[str]:
        """Generate recommendations to prevent churn"""
        recommendations = []
        
        if factors.get('days_since_last_activity', 0) > 7:
            recommendations.append("Send re-engagement email campaign")
        
        if factors.get('engagement_level') in ['low', 'inactive']:
            recommendations.append("Provide personalized onboarding or feature tutorial")
        
        if factors.get('session_frequency_decline', 0) > 50:
            recommendations.append("Offer customer success consultation")
        
        if factors.get('feature_usage_decline', 0) > 30:
            recommendations.append("Showcase underutilized features relevant to user")
        
        if factors.get('support_interactions', 0) > 3:
            recommendations.append("Proactive support outreach to resolve issues")
        
        return recommendations
    
    def _count_active_users(self, start: datetime, end: datetime, db) -> int:
        """Count active users in time range"""
        return db.query(UserEvent.user_id).filter(
            UserEvent.timestamp.between(start, end)
        ).distinct().count()
    
    def _count_events(self, start: datetime, end: datetime, db) -> int:
        """Count events in time range"""
        return db.query(UserEvent).filter(
            UserEvent.timestamp.between(start, end)
        ).count()
    
    def _avg_session_duration(self, start: datetime, end: datetime, db) -> float:
        """Calculate average session duration"""
        sessions = db.query(UserSession.duration).filter(
            UserSession.start_time.between(start, end),
            UserSession.duration.isnot(None)
        ).all()
        
        durations = [s.duration for s in sessions if s.duration]
        return np.mean(durations) if durations else 0
    
    def _get_top_pages(self, start: datetime, end: datetime, db) -> List[Tuple[str, int]]:
        """Get top pages by views"""
        page_views = db.query(UserEvent.page_url).filter(
            UserEvent.timestamp.between(start, end),
            UserEvent.event_type == EventType.PAGE_VIEW.value,
            UserEvent.page_url.isnot(None)
        ).all()
        
        page_counts = {}
        for pv in page_views:
            page = pv.page_url
            page_counts[page] = page_counts.get(page, 0) + 1
        
        return sorted(page_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    def _get_top_events(self, start: datetime, end: datetime, db) -> List[Tuple[str, int]]:
        """Get top event types"""
        events = db.query(UserEvent.event_type).filter(
            UserEvent.timestamp.between(start, end)
        ).all()
        
        event_counts = {}
        for event in events:
            event_type = event.event_type
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return sorted(event_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    def _count_real_time_users(self, db) -> int:
        """Count users active in last 5 minutes"""
        five_min_ago = datetime.utcnow() - timedelta(minutes=5)
        return db.query(UserEvent.user_id).filter(
            UserEvent.timestamp >= five_min_ago
        ).distinct().count()
    
    def _calculate_bounce_rate(self, start: datetime, end: datetime, db) -> float:
        """Calculate bounce rate"""
        sessions = db.query(UserSession).filter(
            UserSession.start_time.between(start, end)
        ).all()
        
        if not sessions:
            return 0
        
        bounce_sessions = [s for s in sessions if s.page_views <= 1]
        return len(bounce_sessions) / len(sessions)
    
    async def _calculate_profile_metrics(self, profile: UserBehaviorProfile, db) -> None:
        """Calculate and update user profile metrics"""
        # Get user sessions
        sessions = db.query(UserSession).filter(
            UserSession.user_id == profile.user_id
        ).all()
        
        # Get user events
        events = db.query(UserEvent).filter(
            UserEvent.user_id == profile.user_id
        ).all()
        
        # Update basic metrics
        profile.total_sessions = len(sessions)
        profile.total_events = len(events)
        
        # Calculate time metrics
        if sessions:
            durations = [s.duration for s in sessions if s.duration]
            profile.total_time_spent = sum(durations) if durations else 0
            profile.avg_session_duration = np.mean(durations) if durations else 0
            profile.avg_events_per_session = len(events) / len(sessions)
            profile.last_activity = max(s.start_time for s in sessions)
            
            # Days since last activity
            if profile.last_activity:
                profile.days_since_last_activity = (datetime.utcnow() - profile.last_activity).days
        
        # Feature usage analysis
        feature_events = [e for e in events if e.event_type == EventType.FEATURE_USE.value]
        features_used = set()
        feature_counts = {}
        
        for event in feature_events:
            if event.properties and 'feature_name' in event.properties:
                feature = event.properties['feature_name']
                features_used.add(feature)
                feature_counts[feature] = feature_counts.get(feature, 0) + 1
        
        profile.features_used = list(features_used)
        profile.most_used_features = sorted(feature_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        profile.most_used_features = [f[0] for f in profile.most_used_features]
        
        # Specific feature metrics
        transcription_events = [e for e in events if e.event_type in [EventType.TRANSCRIPTION_START.value, EventType.TRANSCRIPTION_COMPLETE.value]]
        profile.transcription_minutes = sum(e.duration or 0 for e in transcription_events) / 60
        
        upload_events = [e for e in events if e.event_type == EventType.UPLOAD.value]
        profile.uploads_count = len(upload_events)
        
        download_events = [e for e in events if e.event_type == EventType.DOWNLOAD.value]
        profile.downloads_count = len(download_events)
        
        search_events = [e for e in events if e.event_type == EventType.SEARCH.value]
        profile.searches_count = len(search_events)
        
        # Time patterns
        if events:
            hours = [e.timestamp.hour for e in events]
            hour_counts = {}
            for hour in hours:
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            
            most_active_hour = max(hour_counts, key=hour_counts.get) if hour_counts else 12
            
            if 6 <= most_active_hour <= 11:
                profile.preferred_time_of_day = "morning"
            elif 12 <= most_active_hour <= 17:
                profile.preferred_time_of_day = "afternoon"  
            else:
                profile.preferred_time_of_day = "evening"
            
            # Preferred days
            days = [e.timestamp.strftime('%A') for e in events]
            day_counts = {}
            for day in days:
                day_counts[day] = day_counts.get(day, 0) + 1
            
            profile.preferred_days = sorted(day_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            profile.preferred_days = [d[0] for d in profile.preferred_days]
    
    def _determine_engagement_level(self, profile: UserBehaviorProfile) -> str:
        """Determine user engagement level"""
        if profile.days_since_last_activity > 30:
            return EngagementLevel.INACTIVE.value
        elif profile.days_since_last_activity > 7:
            return EngagementLevel.LOW.value
        elif profile.avg_events_per_session > 10 and profile.avg_session_duration > 600:
            return EngagementLevel.HIGH.value
        else:
            return EngagementLevel.MEDIUM.value
    
    def _determine_user_segment(self, profile: UserBehaviorProfile) -> str:
        """Determine user segment"""
        if profile.days_since_signup < 7:
            return UserSegment.NEW_USER.value
        elif profile.churn_risk_score > 0.7:
            return UserSegment.CHURNING_USER.value
        elif len(profile.features_used) > 5 and profile.avg_events_per_session > 15:
            return UserSegment.POWER_USER.value
        elif profile.total_sessions > 10:
            return UserSegment.REGULAR_USER.value
        else:
            return UserSegment.OCCASIONAL_USER.value
    
    def _calculate_churn_risk_score(self, profile: UserBehaviorProfile, db) -> float:
        """Calculate churn risk score for profile"""
        factors = {
            'days_since_last_activity': profile.days_since_last_activity,
            'engagement_level': profile.engagement_level,
            'session_frequency_decline': self._calculate_session_frequency_decline(profile.user_id, db),
            'feature_usage_decline': self._calculate_feature_usage_decline(profile.user_id, db),
            'support_interactions': self._count_support_interactions(profile.user_id, db)
        }
        
        return self._calculate_churn_score(factors)
    
    def _calculate_session_frequency_decline(self, user_id: str, db) -> float:
        """Calculate session frequency decline percentage"""
        # Get sessions from last 30 days vs previous 30 days
        now = datetime.utcnow()
        last_30_days = now - timedelta(days=30)
        previous_30_days = now - timedelta(days=60)
        
        recent_sessions = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.start_time >= last_30_days
        ).count()
        
        previous_sessions = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.start_time.between(previous_30_days, last_30_days)
        ).count()
        
        if previous_sessions == 0:
            return 0
        
        decline = ((previous_sessions - recent_sessions) / previous_sessions) * 100
        return max(0, decline)
    
    def _calculate_feature_usage_decline(self, user_id: str, db) -> float:
        """Calculate feature usage decline percentage"""
        now = datetime.utcnow()
        last_30_days = now - timedelta(days=30)
        previous_30_days = now - timedelta(days=60)
        
        recent_features = db.query(UserEvent).filter(
            UserEvent.user_id == user_id,
            UserEvent.event_type == EventType.FEATURE_USE.value,
            UserEvent.timestamp >= last_30_days
        ).count()
        
        previous_features = db.query(UserEvent).filter(
            UserEvent.user_id == user_id,
            UserEvent.event_type == EventType.FEATURE_USE.value,
            UserEvent.timestamp.between(previous_30_days, last_30_days)
        ).count()
        
        if previous_features == 0:
            return 0
        
        decline = ((previous_features - recent_features) / previous_features) * 100
        return max(0, decline)
    
    def _count_support_interactions(self, user_id: str, db) -> int:
        """Count support interactions (help views, error events)"""
        help_count = db.query(UserEvent).filter(
            UserEvent.user_id == user_id,
            UserEvent.event_type == EventType.HELP_VIEW.value,
            UserEvent.timestamp >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        error_count = db.query(UserEvent).filter(
            UserEvent.user_id == user_id,
            UserEvent.event_type == EventType.ERROR.value,
            UserEvent.timestamp >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        return help_count + error_count
    
    async def create_user_profile(self, user_id: str, initial_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create or update user behavior profile"""
        db = self.SessionLocal()
        try:
            # Check if profile already exists
            existing_profile = db.query(UserBehaviorProfile).filter(
                UserBehaviorProfile.user_id == user_id
            ).first()
            
            if existing_profile:
                return {
                    "status": "exists",
                    "user_id": user_id,
                    "profile_id": existing_profile.id,
                    "created_at": existing_profile.created_at.isoformat()
                }
            
            # Create new profile
            profile = UserBehaviorProfile(
                user_id=user_id,
                total_sessions=0,
                total_events=0,
                avg_session_duration=0,
                engagement_level=EngagementLevel.MEDIUM.value,
                user_segment="new_user",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Add initial data if provided
            if initial_data:
                for key, value in initial_data.items():
                    if hasattr(profile, key):
                        setattr(profile, key, value)
            
            db.add(profile)
            db.commit()
            db.refresh(profile)
            
            return {
                "status": "created",
                "user_id": user_id,
                "profile_id": profile.id,
                "created_at": profile.created_at.isoformat()
            }
        finally:
            db.close()
    
    async def get_user_behavior(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive user behavior data"""
        db = self.SessionLocal()
        try:
            profile = db.query(UserBehaviorProfile).filter(
                UserBehaviorProfile.user_id == user_id
            ).first()
            
            if not profile:
                return {"error": "User profile not found"}
            
            # Get recent events
            since_date = datetime.utcnow() - timedelta(days=days)
            recent_events = db.query(UserEvent).filter(
                UserEvent.user_id == user_id,
                UserEvent.timestamp >= since_date
            ).order_by(UserEvent.timestamp.desc()).all()
            
            # Get recent sessions
            recent_sessions = db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.start_time >= since_date
            ).order_by(UserSession.start_time.desc()).all()
            
            # Analyze behavior patterns
            event_patterns = self._analyze_event_patterns(recent_events)
            session_patterns = self._analyze_session_patterns(recent_sessions)
            
            return {
                "user_id": user_id,
                "profile": {
                    "engagement_level": profile.engagement_level,
                    "user_segment": profile.user_segment,
                    "total_sessions": profile.total_sessions,
                    "total_events": profile.total_events,
                    "avg_session_duration": profile.avg_session_duration,
                    "last_activity": profile.last_activity.isoformat() if profile.last_activity else None
                },
                "recent_activity": {
                    "events_count": len(recent_events),
                    "sessions_count": len(recent_sessions),
                    "event_patterns": event_patterns,
                    "session_patterns": session_patterns,
                    "most_active_days": self._get_most_active_days(recent_events),
                    "preferred_features": self._get_preferred_features(recent_events)
                },
                "analysis_period_days": days,
                "generated_at": datetime.utcnow().isoformat()
            }
        finally:
            db.close()
    
    async def get_engagement_metrics(self, date_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """Get comprehensive engagement metrics"""
        db = self.SessionLocal()
        try:
            if not date_range:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=30)
            else:
                start_date, end_date = date_range
            
            # Basic metrics
            total_users = db.query(UserEvent.user_id).filter(
                UserEvent.timestamp.between(start_date, end_date)
            ).distinct().count()
            
            total_events = db.query(UserEvent).filter(
                UserEvent.timestamp.between(start_date, end_date)
            ).count()
            
            total_sessions = db.query(UserSession).filter(
                UserSession.start_time.between(start_date, end_date)
            ).count()
            
            # Engagement distribution
            engagement_distribution = db.query(UserBehaviorProfile.engagement_level).all()
            engagement_counts = {}
            for level in EngagementLevel:
                engagement_counts[level.value] = sum(1 for e in engagement_distribution if e[0] == level.value)
            
            # Daily active users trend
            daily_active_users = self._calculate_daily_active_users(start_date, end_date, db)
            
            # Feature usage metrics
            feature_usage = self._calculate_feature_usage_metrics(start_date, end_date, db)
            
            # Session metrics
            session_metrics = self._calculate_session_metrics(start_date, end_date, db)
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": (end_date - start_date).days
                },
                "overview": {
                    "total_users": total_users,
                    "total_events": total_events,
                    "total_sessions": total_sessions,
                    "events_per_user": total_events / total_users if total_users > 0 else 0,
                    "sessions_per_user": total_sessions / total_users if total_users > 0 else 0
                },
                "engagement_distribution": engagement_counts,
                "daily_active_users": daily_active_users,
                "feature_usage": feature_usage,
                "session_metrics": session_metrics,
                "generated_at": datetime.utcnow().isoformat()
            }
        finally:
            db.close()
    
    async def analyze_user_journey(self, user_id: str, session_limit: int = 10) -> Dict[str, Any]:
        """Analyze user journey and behavior flow"""
        db = self.SessionLocal()
        try:
            # Get user's journey data
            journey = db.query(UserJourney).filter(
                UserJourney.user_id == user_id
            ).first()
            
            if not journey:
                return {"error": "User journey not found"}
            
            # Get recent sessions with events
            recent_sessions = db.query(UserSession).filter(
                UserSession.user_id == user_id
            ).order_by(UserSession.start_time.desc()).limit(session_limit).all()
            
            journey_analysis = {
                "user_id": user_id,
                "journey_summary": {
                    "total_sessions": journey.total_sessions,
                    "total_page_views": journey.total_page_views,
                    "conversion_events": journey.conversion_events,
                    "funnel_progress": journey.funnel_progress,
                    "journey_stage": journey.journey_stage
                },
                "session_flow": [],
                "behavioral_patterns": self._analyze_behavioral_patterns(recent_sessions, db),
                "conversion_funnel": self._analyze_conversion_funnel(user_id, db),
                "recommendations": self._generate_journey_recommendations(journey, recent_sessions)
            }
            
            # Analyze each session
            for session in recent_sessions:
                session_events = db.query(UserEvent).filter(
                    UserEvent.session_id == session.session_id
                ).order_by(UserEvent.timestamp).all()
                
                session_flow = {
                    "session_id": session.session_id,
                    "start_time": session.start_time.isoformat(),
                    "duration": session.duration,
                    "events_count": len(session_events),
                    "event_sequence": [
                        {
                            "event_type": event.event_type,
                            "page_url": event.page_url,
                            "timestamp": event.timestamp.isoformat()
                        }
                        for event in session_events[:20]  # Limit to first 20 events
                    ]
                }
                journey_analysis["session_flow"].append(session_flow)
            
            return journey_analysis
        finally:
            db.close()
    
    async def get_feature_usage(self, feature_name: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
        """Get feature usage analytics"""
        db = self.SessionLocal()
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            if feature_name:
                # Specific feature analysis
                events = db.query(UserEvent).filter(
                    UserEvent.event_type == EventType.FEATURE_USE.value,
                    UserEvent.timestamp >= since_date,
                    UserEvent.metadata.isnot(None)
                ).all()
                
                # Filter events for specific feature
                feature_events = [
                    event for event in events 
                    if isinstance(event.metadata, dict) and 
                    event.metadata.get('feature') == feature_name
                ]
                
                # Analyze usage patterns
                usage_by_day = self._group_events_by_day(feature_events)
                usage_by_user = self._group_events_by_user(feature_events)
                
                return {
                    "feature_name": feature_name,
                    "period_days": days,
                    "total_usage_events": len(feature_events),
                    "unique_users": len(usage_by_user),
                    "usage_by_day": usage_by_day,
                    "top_users": sorted(usage_by_user.items(), key=lambda x: x[1], reverse=True)[:10],
                    "generated_at": datetime.utcnow().isoformat()
                }
            else:
                # All features analysis
                events = db.query(UserEvent).filter(
                    UserEvent.event_type == EventType.FEATURE_USE.value,
                    UserEvent.timestamp >= since_date
                ).all()
                
                # Extract feature names from metadata
                feature_usage = {}
                for event in events:
                    if isinstance(event.metadata, dict) and 'feature' in event.metadata:
                        feature = event.metadata['feature']
                        if feature not in feature_usage:
                            feature_usage[feature] = {
                                'usage_count': 0,
                                'unique_users': set(),
                                'recent_events': []
                            }
                        feature_usage[feature]['usage_count'] += 1
                        feature_usage[feature]['unique_users'].add(event.user_id)
                        feature_usage[feature]['recent_events'].append(event.timestamp)
                
                # Format results
                feature_stats = {}
                for feature, data in feature_usage.items():
                    feature_stats[feature] = {
                        'usage_count': data['usage_count'],
                        'unique_users': len(data['unique_users']),
                        'avg_usage_per_user': data['usage_count'] / len(data['unique_users']) if data['unique_users'] else 0,
                        'last_used': max(data['recent_events']).isoformat() if data['recent_events'] else None
                    }
                
                return {
                    "period_days": days,
                    "total_features": len(feature_stats),
                    "feature_usage": feature_stats,
                    "most_popular_features": sorted(
                        feature_stats.items(), 
                        key=lambda x: x[1]['usage_count'], 
                        reverse=True
                    )[:10],
                    "generated_at": datetime.utcnow().isoformat()
                }
        finally:
            db.close()
    
    def _analyze_event_patterns(self, events: List[UserEvent]) -> Dict[str, Any]:
        """Analyze patterns in user events"""
        if not events:
            return {}
        
        event_types = {}
        hourly_distribution = [0] * 24
        
        for event in events:
            # Count event types
            event_type = event.event_type
            event_types[event_type] = event_types.get(event_type, 0) + 1
            
            # Hour distribution
            hour = event.timestamp.hour
            hourly_distribution[hour] += 1
        
        return {
            "event_types": event_types,
            "hourly_distribution": hourly_distribution,
            "most_active_hour": hourly_distribution.index(max(hourly_distribution)),
            "total_events": len(events)
        }
    
    def _analyze_session_patterns(self, sessions: List[UserSession]) -> Dict[str, Any]:
        """Analyze patterns in user sessions"""
        if not sessions:
            return {}
        
        durations = [s.duration for s in sessions if s.duration]
        session_counts_by_day = {}
        
        for session in sessions:
            day = session.start_time.strftime('%A')
            session_counts_by_day[day] = session_counts_by_day.get(day, 0) + 1
        
        return {
            "total_sessions": len(sessions),
            "avg_duration": np.mean(durations) if durations else 0,
            "session_counts_by_day": session_counts_by_day,
            "most_active_day": max(session_counts_by_day.items(), key=lambda x: x[1])[0] if session_counts_by_day else None
        }
    
    def _get_most_active_days(self, events: List[UserEvent]) -> List[str]:
        """Get most active days from events"""
        if not events:
            return []
        
        day_counts = {}
        for event in events:
            day = event.timestamp.strftime('%A')
            day_counts[day] = day_counts.get(day, 0) + 1
        
        return sorted(day_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    
    def _get_preferred_features(self, events: List[UserEvent]) -> List[str]:
        """Get most used features from events"""
        feature_events = [
            e for e in events 
            if e.event_type == EventType.FEATURE_USE.value and 
            isinstance(e.metadata, dict) and 'feature' in e.metadata
        ]
        
        feature_counts = {}
        for event in feature_events:
            feature = event.metadata['feature']
            feature_counts[feature] = feature_counts.get(feature, 0) + 1
        
        return sorted(feature_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    def _calculate_daily_active_users(self, start_date: datetime, end_date: datetime, db) -> List[Dict[str, Any]]:
        """Calculate daily active users for the period"""
        daily_users = []
        current_date = start_date
        
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            active_users = db.query(UserEvent.user_id).filter(
                UserEvent.timestamp.between(current_date, next_date)
            ).distinct().count()
            
            daily_users.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "active_users": active_users
            })
            current_date = next_date
        
        return daily_users
    
    def _calculate_feature_usage_metrics(self, start_date: datetime, end_date: datetime, db) -> Dict[str, Any]:
        """Calculate feature usage metrics for the period"""
        feature_events = db.query(UserEvent).filter(
            UserEvent.event_type == EventType.FEATURE_USE.value,
            UserEvent.timestamp.between(start_date, end_date)
        ).all()
        
        feature_stats = {}
        for event in feature_events:
            if isinstance(event.metadata, dict) and 'feature' in event.metadata:
                feature = event.metadata['feature']
                if feature not in feature_stats:
                    feature_stats[feature] = {'count': 0, 'users': set()}
                feature_stats[feature]['count'] += 1
                feature_stats[feature]['users'].add(event.user_id)
        
        # Convert to serializable format
        for feature in feature_stats:
            feature_stats[feature]['unique_users'] = len(feature_stats[feature]['users'])
            del feature_stats[feature]['users']  # Remove set (not serializable)
        
        return feature_stats
    
    def _calculate_session_metrics(self, start_date: datetime, end_date: datetime, db) -> Dict[str, Any]:
        """Calculate session metrics for the period"""
        sessions = db.query(UserSession).filter(
            UserSession.start_time.between(start_date, end_date)
        ).all()
        
        if not sessions:
            return {"avg_duration": 0, "total_sessions": 0, "avg_events_per_session": 0}
        
        durations = [s.duration for s in sessions if s.duration]
        events_counts = [s.events_count for s in sessions if s.events_count]
        
        return {
            "total_sessions": len(sessions),
            "avg_duration": np.mean(durations) if durations else 0,
            "avg_events_per_session": np.mean(events_counts) if events_counts else 0,
            "median_duration": np.median(durations) if durations else 0
        }
    
    def _analyze_behavioral_patterns(self, sessions: List[UserSession], db) -> Dict[str, Any]:
        """Analyze behavioral patterns from sessions"""
        if not sessions:
            return {}
        
        # Analyze session timing patterns
        session_hours = [s.start_time.hour for s in sessions]
        session_days = [s.start_time.strftime('%A') for s in sessions]
        
        # Most common patterns
        from collections import Counter
        hour_distribution = Counter(session_hours)
        day_distribution = Counter(session_days)
        
        return {
            "preferred_hours": hour_distribution.most_common(3),
            "preferred_days": day_distribution.most_common(3),
            "total_sessions_analyzed": len(sessions)
        }
    
    def _analyze_conversion_funnel(self, user_id: str, db) -> Dict[str, Any]:
        """Analyze user's conversion funnel progress"""
        # Define funnel stages
        funnel_stages = [
            ("signup", EventType.SESSION_START.value),
            ("first_upload", EventType.UPLOAD.value), 
            ("first_transcription", EventType.TRANSCRIPTION_START.value),
            ("transcription_complete", EventType.TRANSCRIPTION_COMPLETE.value),
            ("download", EventType.DOWNLOAD.value)
        ]
        
        funnel_progress = {}
        for stage_name, event_type in funnel_stages:
            event_exists = db.query(UserEvent).filter(
                UserEvent.user_id == user_id,
                UserEvent.event_type == event_type
            ).first() is not None
            
            funnel_progress[stage_name] = event_exists
        
        return funnel_progress
    
    def _generate_journey_recommendations(self, journey: UserJourney, recent_sessions: List[UserSession]) -> List[str]:
        """Generate recommendations based on user journey"""
        recommendations = []
        
        if journey.total_sessions < 3:
            recommendations.append("Encourage user to explore more features")
        
        if not recent_sessions:
            recommendations.append("Send re-engagement email")
        elif len(recent_sessions) < 2:
            recommendations.append("Provide usage tips and tutorials")
        
        if journey.conversion_events == 0:
            recommendations.append("Highlight key conversion features")
        
        if journey.funnel_progress < 0.5:
            recommendations.append("Provide onboarding assistance")
        
        return recommendations
    
    def _group_events_by_day(self, events: List[UserEvent]) -> Dict[str, int]:
        """Group events by day"""
        day_counts = {}
        for event in events:
            day = event.timestamp.strftime("%Y-%m-%d")
            day_counts[day] = day_counts.get(day, 0) + 1
        return day_counts
    
    def _group_events_by_user(self, events: List[UserEvent]) -> Dict[str, int]:
        """Group events by user"""
        user_counts = {}
        for event in events:
            user_counts[event.user_id] = user_counts.get(event.user_id, 0) + 1
        return user_counts
    
    async def predict_churn(self, user_id: str) -> Dict[str, Any]:
        """Predict user churn probability (alias for predict_user_churn)"""
        return await self.predict_user_churn(user_id)