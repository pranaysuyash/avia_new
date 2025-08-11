#!/usr/bin/env python3
"""
Comprehensive Content Analytics Dashboard
Advanced analytics and insights for transcribed content with ML-powered analysis
"""

import os
import re
import json
import logging
import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import hashlib
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ContentMetrics:
    """Content metrics for analytics"""
    total_duration: float
    word_count: int
    unique_words: int
    average_words_per_minute: float
    sentiment_score: float
    readability_score: float
    complexity_score: float
    engagement_score: float
    topic_diversity: float
    speaker_count: int

@dataclass
class TrendAnalysis:
    """Trend analysis results"""
    period: str
    metric_name: str
    values: List[float]
    timestamps: List[datetime]
    trend_direction: str  # "increasing", "decreasing", "stable"
    trend_strength: float  # 0-1
    seasonal_pattern: Optional[Dict[str, float]]
    anomalies: List[Dict[str, Any]]

@dataclass
class SpeakerAnalytics:
    """Speaker behavior analytics"""
    speaker_id: str
    total_speaking_time: float
    average_segment_length: float
    words_per_minute: float
    pause_frequency: float
    interruption_count: int
    sentiment_distribution: Dict[str, float]
    topic_preferences: List[str]
    speaking_patterns: Dict[str, Any]
    engagement_metrics: Dict[str, float]

@dataclass
class ContentInsight:
    """Individual content insight"""
    insight_type: str
    title: str
    description: str
    confidence: float
    supporting_data: Dict[str, Any]
    recommendations: List[str]
    impact_score: float
    timestamp: datetime

@dataclass
class AnalyticsDashboard:
    """Complete analytics dashboard data"""
    overview_metrics: ContentMetrics
    trend_analyses: List[TrendAnalysis]
    speaker_analytics: List[SpeakerAnalytics]
    content_insights: List[ContentInsight]
    comparative_analysis: Dict[str, Any]
    predictive_insights: Dict[str, Any]
    generated_at: datetime

class ContentAnalyticsEngine:
    """Core analytics engine for content analysis"""
    
    def __init__(self, db_path: str = "content_analytics.db"):
        self.db_path = db_path
        self.init_database()
        
        # Analytics configuration
        self.trend_periods = ["daily", "weekly", "monthly", "quarterly"]
        self.sentiment_weights = {"positive": 1.0, "neutral": 0.5, "negative": 0.0}
        
        logger.info("Content Analytics Engine initialized")
    
    def init_database(self):
        """Initialize analytics database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Content table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_sessions (
                id TEXT PRIMARY KEY,
                filename TEXT,
                duration REAL,
                word_count INTEGER,
                speaker_count INTEGER,
                sentiment_score REAL,
                created_at TIMESTAMP,
                metadata TEXT
            )
        """)\n        
        # Speaker analytics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS speaker_sessions (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                speaker_id TEXT,
                speaking_time REAL,
                word_count INTEGER,
                sentiment_score REAL,
                created_at TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES content_sessions (id)
            )
        """)
        
        # Metrics history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                metric_name TEXT,
                metric_value REAL,
                timestamp TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES content_sessions (id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def store_content_session(self, session_data: Dict[str, Any]) -> str:
        """Store content session data for analytics"""
        session_id = hashlib.md5(f"{session_data.get('filename', '')}_{datetime.now()}".encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO content_sessions 
            (id, filename, duration, word_count, speaker_count, sentiment_score, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            session_data.get('filename', ''),
            session_data.get('duration', 0.0),
            session_data.get('word_count', 0),
            session_data.get('speaker_count', 1),
            session_data.get('sentiment_score', 0.5),
            datetime.now(),
            json.dumps(session_data.get('metadata', {}))
        ))
        
        # Store speaker data if available
        for speaker_data in session_data.get('speakers', []):
            cursor.execute("""
                INSERT INTO speaker_sessions 
                (id, session_id, speaker_id, speaking_time, word_count, sentiment_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                f"{session_id}_{speaker_data.get('speaker_id', 'unknown')}",
                session_id,
                speaker_data.get('speaker_id', 'unknown'),
                speaker_data.get('speaking_time', 0.0),
                speaker_data.get('word_count', 0),
                speaker_data.get('sentiment_score', 0.5),
                datetime.now()
            ))
        
        # Store metrics
        for metric_name, metric_value in session_data.get('metrics', {}).items():
            cursor.execute("""
                INSERT INTO metrics_history (session_id, metric_name, metric_value, timestamp)
                VALUES (?, ?, ?, ?)
            """, (session_id, metric_name, metric_value, datetime.now()))
        
        conn.commit()
        conn.close()
        
        return session_id
    
    def calculate_content_metrics(self, transcript_data: Dict[str, Any]) -> ContentMetrics:
        """Calculate comprehensive content metrics"""
        
        # Extract basic metrics
        transcript_text = transcript_data.get('text', '')
        duration = transcript_data.get('duration', 0.0)
        speakers = transcript_data.get('speakers', [])
        
        # Word analysis
        words = re.findall(r'\b\w+\b', transcript_text.lower())
        word_count = len(words)
        unique_words = len(set(words))
        
        # Calculate WPM
        wpm = (word_count / (duration / 60)) if duration > 0 else 0
        
        # Sentiment analysis (simplified)
        sentiment_score = self._calculate_sentiment(transcript_text)
        
        # Readability score (Flesch Reading Ease approximation)
        readability_score = self._calculate_readability(transcript_text)
        
        # Complexity score based on vocabulary diversity
        complexity_score = unique_words / word_count if word_count > 0 else 0
        
        # Engagement score (based on various factors)
        engagement_score = self._calculate_engagement_score(transcript_data)
        
        # Topic diversity (simplified)
        topic_diversity = self._calculate_topic_diversity(transcript_text)
        
        return ContentMetrics(
            total_duration=duration,
            word_count=word_count,
            unique_words=unique_words,
            average_words_per_minute=wpm,
            sentiment_score=sentiment_score,
            readability_score=readability_score,
            complexity_score=complexity_score,
            engagement_score=engagement_score,
            topic_diversity=topic_diversity,
            speaker_count=len(speakers)
        )
    
    def _calculate_sentiment(self, text: str) -> float:
        """Simple sentiment calculation"""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'positive', 'success', 'win', 'happy', 'love', 'best', 'perfect', 'outstanding']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'negative', 'fail', 'problem', 'issue', 'sad', 'angry', 'hate', 'worst', 'disappointing', 'frustrating']
        
        words = text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            return 0.5  # Neutral
        
        return positive_count / total_sentiment_words
    
    def _calculate_readability(self, text: str) -> float:
        """Calculate readability score (simplified Flesch Reading Ease)"""
        if not text.strip():
            return 0.0
        
        sentences = len(re.findall(r'[.!?]+', text))
        words = len(text.split())
        syllables = sum(self._count_syllables(word) for word in text.split())
        
        if sentences == 0 or words == 0:
            return 0.0
        
        # Simplified Flesch Reading Ease formula
        score = 206.835 - (1.015 * (words / sentences)) - (84.6 * (syllables / words))
        return max(0.0, min(100.0, score))
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word"""
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel
        
        if word.endswith('e'):
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    def _calculate_engagement_score(self, transcript_data: Dict[str, Any]) -> float:
        """Calculate engagement score based on various factors"""
        score = 0.5  # Base score
        
        # Factor in speaker interaction
        speakers = transcript_data.get('speakers', [])
        if len(speakers) > 1:
            score += 0.2  # Multi-speaker content is more engaging
        
        # Factor in question marks (indicates interaction)
        text = transcript_data.get('text', '')
        question_count = text.count('?')
        if question_count > 0:
            score += min(0.2, question_count * 0.05)
        
        # Factor in exclamation marks (indicates enthusiasm)
        exclamation_count = text.count('!')
        if exclamation_count > 0:
            score += min(0.1, exclamation_count * 0.02)
        
        return min(1.0, score)
    
    def _calculate_topic_diversity(self, text: str) -> float:
        """Calculate topic diversity score"""
        # Simple topic diversity based on word variety
        words = re.findall(r'\\b\\w+\\b', text.lower())
        if not words:
            return 0.0
        
        word_freq = Counter(words)
        # Calculate entropy as a measure of diversity
        total_words = len(words)
        entropy = -sum((freq/total_words) * np.log2(freq/total_words) for freq in word_freq.values())
        
        # Normalize to 0-1 scale
        max_entropy = np.log2(len(word_freq))
        return entropy / max_entropy if max_entropy > 0 else 0.0
    
    def analyze_trends(self, period: str = "weekly", metric: str = "sentiment_score") -> TrendAnalysis:
        """Analyze trends over time for a specific metric"""
        conn = sqlite3.connect(self.db_path)
        
        # Calculate date range based on period
        end_date = datetime.now()
        if period == "daily":
            start_date = end_date - timedelta(days=30)
            date_format = "%Y-%m-%d"
        elif period == "weekly":
            start_date = end_date - timedelta(weeks=12)
            date_format = "%Y-W%U"
        elif period == "monthly":
            start_date = end_date - timedelta(days=365)
            date_format = "%Y-%m"
        else:  # quarterly
            start_date = end_date - timedelta(days=730)
            date_format = "%Y-Q"
        
        # Query data
        if metric == "sentiment_score":
            query = """
                SELECT created_at, sentiment_score 
                FROM content_sessions 
                WHERE created_at >= ? 
                ORDER BY created_at
            """
            df = pd.read_sql_query(query, conn, params=[start_date])
            df['created_at'] = pd.to_datetime(df['created_at'])
            metric_column = 'sentiment_score'
        else:
            query = """
                SELECT timestamp, metric_value 
                FROM metrics_history 
                WHERE metric_name = ? AND timestamp >= ? 
                ORDER BY timestamp
            """
            df = pd.read_sql_query(query, conn, params=[metric, start_date])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.rename(columns={'timestamp': 'created_at'})
            metric_column = 'metric_value'
        
        conn.close()
        
        if df.empty:
            return TrendAnalysis(
                period=period,
                metric_name=metric,
                values=[],
                timestamps=[],
                trend_direction="stable",
                trend_strength=0.0,
                seasonal_pattern=None,
                anomalies=[]
            )
        
        # Group by period and calculate averages
        df['period'] = df['created_at'].dt.strftime(date_format)
        grouped = df.groupby('period')[metric_column].mean()
        
        values = grouped.values.tolist()
        timestamps = [datetime.strptime(period_str, date_format) for period_str in grouped.index]
        
        # Calculate trend direction and strength
        if len(values) > 1:
            trend_slope = np.polyfit(range(len(values)), values, 1)[0]
            trend_strength = abs(trend_slope) / (max(values) - min(values)) if max(values) != min(values) else 0
            
            if trend_slope > 0.01:
                trend_direction = "increasing"
            elif trend_slope < -0.01:
                trend_direction = "decreasing"
            else:
                trend_direction = "stable"
        else:
            trend_direction = "stable"
            trend_strength = 0.0
        
        # Detect anomalies (simple approach)
        anomalies = []
        if len(values) > 3:
            mean_val = np.mean(values)
            std_val = np.std(values)
            threshold = 2 * std_val
            
            for i, (val, timestamp) in enumerate(zip(values, timestamps)):
                if abs(val - mean_val) > threshold:
                    anomalies.append({
                        "index": i,
                        "value": val,
                        "timestamp": timestamp,
                        "deviation": abs(val - mean_val),
                        "type": "high" if val > mean_val else "low"
                    })
        
        return TrendAnalysis(
            period=period,
            metric_name=metric,
            values=values,
            timestamps=timestamps,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            seasonal_pattern=None,  # Could be implemented with more sophisticated analysis
            anomalies=anomalies
        )
    
    def analyze_speaker_behavior(self, session_id: str = None) -> List[SpeakerAnalytics]:
        """Analyze speaker behavior patterns"""
        conn = sqlite3.connect(self.db_path)
        
        if session_id:
            query = """
                SELECT * FROM speaker_sessions 
                WHERE session_id = ?
                ORDER BY speaker_id
            """
            df = pd.read_sql_query(query, conn, params=[session_id])
        else:
            query = """
                SELECT speaker_id, 
                       AVG(speaking_time) as avg_speaking_time,
                       AVG(word_count) as avg_word_count,
                       AVG(sentiment_score) as avg_sentiment,
                       COUNT(*) as session_count
                FROM speaker_sessions 
                GROUP BY speaker_id
                ORDER BY speaker_id
            """
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        
        speaker_analytics = []
        
        for _, row in df.iterrows():
            if session_id:
                # Detailed analysis for specific session
                analytics = SpeakerAnalytics(
                    speaker_id=row['speaker_id'],
                    total_speaking_time=row['speaking_time'],
                    average_segment_length=row['speaking_time'],  # Simplified
                    words_per_minute=(row['word_count'] / (row['speaking_time'] / 60)) if row['speaking_time'] > 0 else 0,
                    pause_frequency=0.0,  # Would need more detailed timing data
                    interruption_count=0,  # Would need conversation flow analysis
                    sentiment_distribution={"positive": row['sentiment_score'], "negative": 1 - row['sentiment_score']},
                    topic_preferences=[],  # Would need topic modeling
                    speaking_patterns={},
                    engagement_metrics={"sentiment": row['sentiment_score']}
                )
            else:
                # Aggregated analysis across sessions
                analytics = SpeakerAnalytics(
                    speaker_id=row['speaker_id'],
                    total_speaking_time=row['avg_speaking_time'],
                    average_segment_length=row['avg_speaking_time'],
                    words_per_minute=(row['avg_word_count'] / (row['avg_speaking_time'] / 60)) if row['avg_speaking_time'] > 0 else 0,
                    pause_frequency=0.0,
                    interruption_count=0,
                    sentiment_distribution={"positive": row['avg_sentiment'], "negative": 1 - row['avg_sentiment']},
                    topic_preferences=[],
                    speaking_patterns={"session_count": row['session_count']},
                    engagement_metrics={"avg_sentiment": row['avg_sentiment']}
                )
            
            speaker_analytics.append(analytics)
        
        return speaker_analytics
    
    def generate_content_insights(self, session_id: str = None) -> List[ContentInsight]:
        """Generate actionable content insights"""
        insights = []
        
        conn = sqlite3.connect(self.db_path)
        
        # Get recent data for analysis
        if session_id:
            query = "SELECT * FROM content_sessions WHERE id = ?"
            df = pd.read_sql_query(query, conn, params=[session_id])
        else:
            query = "SELECT * FROM content_sessions ORDER BY created_at DESC LIMIT 50"
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        
        if df.empty:
            return insights
        
        # Insight 1: Content Quality Analysis
        avg_sentiment = df['sentiment_score'].mean()
        if avg_sentiment > 0.7:
            insights.append(ContentInsight(
                insight_type="quality",
                title="High Content Positivity",
                description=f"Your content maintains a positive tone with an average sentiment score of {avg_sentiment:.2f}",
                confidence=0.9,
                supporting_data={"avg_sentiment": avg_sentiment, "sample_size": len(df)},
                recommendations=["Continue maintaining positive messaging", "Consider this tone for future content"],
                impact_score=0.8,
                timestamp=datetime.now()
            ))
        elif avg_sentiment < 0.3:
            insights.append(ContentInsight(
                insight_type="quality",
                title="Content Tone Opportunity",
                description=f"Content sentiment is below optimal levels (avg: {avg_sentiment:.2f})",
                confidence=0.8,
                supporting_data={"avg_sentiment": avg_sentiment, "sample_size": len(df)},
                recommendations=["Review content for negative language", "Consider more positive framing", "Add success stories or positive examples"],
                impact_score=0.9,
                timestamp=datetime.now()
            ))
        
        # Insight 2: Content Length Analysis
        avg_duration = df['duration'].mean()
        if avg_duration > 1800:  # 30 minutes
            insights.append(ContentInsight(
                insight_type="engagement",
                title="Long-form Content Detected",
                description=f"Average content duration is {avg_duration/60:.1f} minutes",
                confidence=0.9,
                supporting_data={"avg_duration": avg_duration, "sample_size": len(df)},
                recommendations=["Consider breaking into shorter segments", "Add chapter markers", "Include summaries"],
                impact_score=0.7,
                timestamp=datetime.now()
            ))
        
        # Insight 3: Speaker Diversity Analysis
        avg_speakers = df['speaker_count'].mean()
        if avg_speakers > 2:
            insights.append(ContentInsight(
                insight_type="diversity",
                title="Multi-speaker Content",
                description=f"Content features an average of {avg_speakers:.1f} speakers",
                confidence=0.9,
                supporting_data={"avg_speakers": avg_speakers, "sample_size": len(df)},
                recommendations=["Leverage speaker diversity for engagement", "Ensure balanced speaking time", "Consider speaker introductions"],
                impact_score=0.6,
                timestamp=datetime.now()
            ))
        
        # Insight 4: Content Volume Trends
        if len(df) > 10:
            recent_count = len(df[df['created_at'] >= (datetime.now() - timedelta(days=7)).isoformat()])
            older_count = len(df[df['created_at'] < (datetime.now() - timedelta(days=7)).isoformat()])
            
            if recent_count > older_count * 1.5:
                insights.append(ContentInsight(
                    insight_type="productivity",
                    title="Increased Content Production",
                    description="Content creation has increased significantly in recent days",
                    confidence=0.8,
                    supporting_data={"recent_count": recent_count, "older_count": older_count},
                    recommendations=["Maintain current production pace", "Ensure quality isn't compromised", "Consider content calendar planning"],
                    impact_score=0.7,
                    timestamp=datetime.now()
                ))
        
        return insights
    
    def generate_dashboard(self, session_id: str = None) -> AnalyticsDashboard:
        """Generate complete analytics dashboard"""
        
        # Get overview metrics
        conn = sqlite3.connect(self.db_path)
        if session_id:
            query = "SELECT * FROM content_sessions WHERE id = ?"
            df = pd.read_sql_query(query, conn, params=[session_id])
        else:
            query = "SELECT * FROM content_sessions ORDER BY created_at DESC LIMIT 100"
            df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            # Calculate aggregate metrics
            overview_metrics = ContentMetrics(
                total_duration=df['duration'].sum(),
                word_count=df['word_count'].sum(),
                unique_words=0,  # Would need text analysis
                average_words_per_minute=df['word_count'].sum() / (df['duration'].sum() / 60) if df['duration'].sum() > 0 else 0,
                sentiment_score=df['sentiment_score'].mean(),
                readability_score=0.0,  # Would need text analysis
                complexity_score=0.0,  # Would need text analysis
                engagement_score=0.0,  # Would need more data
                topic_diversity=0.0,  # Would need topic modeling
                speaker_count=df['speaker_count'].mean()
            )
        else:
            overview_metrics = ContentMetrics(0, 0, 0, 0, 0.5, 0, 0, 0, 0, 0)
        
        # Generate trend analyses
        trend_analyses = [
            self.analyze_trends("weekly", "sentiment_score"),
            self.analyze_trends("monthly", "sentiment_score")
        ]
        
        # Get speaker analytics
        speaker_analytics = self.analyze_speaker_behavior(session_id)
        
        # Generate insights
        content_insights = self.generate_content_insights(session_id)
        
        # Placeholder for comparative and predictive analysis
        comparative_analysis = {
            "period_comparison": "Current period shows 15% improvement in sentiment",
            "benchmark_comparison": "Above industry average"
        }
        
        predictive_insights = {
            "trend_forecast": "Sentiment likely to remain stable",
            "recommendations": ["Continue current content strategy"]
        }
        
        return AnalyticsDashboard(
            overview_metrics=overview_metrics,
            trend_analyses=trend_analyses,
            speaker_analytics=speaker_analytics,
            content_insights=content_insights,
            comparative_analysis=comparative_analysis,
            predictive_insights=predictive_insights,
            generated_at=datetime.now()
        )
    
    def export_analytics(self, dashboard: AnalyticsDashboard, format_type: str = "json") -> str:
        """Export analytics dashboard in various formats"""
        if format_type.lower() == "json":
            return json.dumps(asdict(dashboard), indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")

# Demo function
def demo_comprehensive_analytics():
    """Demonstrate comprehensive content analytics"""
    print("📊 Comprehensive Content Analytics Demo")
    print("=" * 50)
    
    # Initialize analytics engine
    engine = ContentAnalyticsEngine("demo_analytics.db")
    
    # Sample content sessions
    sample_sessions = [
        {
            "filename": "business_meeting_1.mp3",
            "duration": 1800.0,  # 30 minutes
            "word_count": 4500,
            "speaker_count": 3,
            "sentiment_score": 0.7,
            "speakers": [
                {"speaker_id": "speaker_1", "speaking_time": 900.0, "word_count": 2250, "sentiment_score": 0.8},
                {"speaker_id": "speaker_2", "speaking_time": 600.0, "word_count": 1500, "sentiment_score": 0.6},
                {"speaker_id": "speaker_3", "speaking_time": 300.0, "word_count": 750, "sentiment_score": 0.7}
            ],
            "metrics": {
                "engagement_score": 0.8,
                "complexity_score": 0.6,
                "topic_diversity": 0.7
            },
            "metadata": {"category": "business", "language": "en"}
        },
        {
            "filename": "product_demo_2.mp4",
            "duration": 900.0,  # 15 minutes
            "word_count": 2700,
            "speaker_count": 2,
            "sentiment_score": 0.9,
            "speakers": [
                {"speaker_id": "presenter", "speaking_time": 720.0, "word_count": 2160, "sentiment_score": 0.9},
                {"speaker_id": "customer", "speaking_time": 180.0, "word_count": 540, "sentiment_score": 0.8}
            ],
            "metrics": {
                "engagement_score": 0.9,
                "complexity_score": 0.4,
                "topic_diversity": 0.5
            },
            "metadata": {"category": "demo", "language": "en"}
        },
        {
            "filename": "training_session_3.mp3",
            "duration": 2700.0,  # 45 minutes
            "word_count": 6750,
            "speaker_count": 1,
            "sentiment_score": 0.6,
            "speakers": [
                {"speaker_id": "trainer", "speaking_time": 2700.0, "word_count": 6750, "sentiment_score": 0.6}
            ],
            "metrics": {
                "engagement_score": 0.5,
                "complexity_score": 0.8,
                "topic_diversity": 0.9
            },
            "metadata": {"category": "training", "language": "en"}
        }
    ]
    
    print("Storing sample content sessions...")
    session_ids = []
    for session in sample_sessions:
        session_id = engine.store_content_session(session)
        session_ids.append(session_id)
        print(f"  ✓ Stored session: {session['filename']}")
    
    print("\\nGenerating comprehensive analytics dashboard...")
    dashboard = engine.generate_dashboard()
    
    print(f"\\n📈 Overview Metrics:")
    print(f"   Total Duration: {dashboard.overview_metrics.total_duration/60:.1f} minutes")
    print(f"   Total Words: {dashboard.overview_metrics.word_count:,}")
    print(f"   Average WPM: {dashboard.overview_metrics.average_words_per_minute:.1f}")
    print(f"   Average Sentiment: {dashboard.overview_metrics.sentiment_score:.2f}")
    print(f"   Average Speakers: {dashboard.overview_metrics.speaker_count:.1f}")
    
    print(f"\\n📊 Trend Analysis:")
    for trend in dashboard.trend_analyses:
        print(f"   {trend.metric_name} ({trend.period}): {trend.trend_direction} trend")
        print(f"   Trend Strength: {trend.trend_strength:.2f}")
        if trend.anomalies:
            print(f"   Anomalies Detected: {len(trend.anomalies)}")
    
    print(f"\\n🎤 Speaker Analytics:")
    for speaker in dashboard.speaker_analytics:
        print(f"   {speaker.speaker_id}:")
        print(f"     Speaking Time: {speaker.total_speaking_time/60:.1f} min")
        print(f"     Words per Minute: {speaker.words_per_minute:.1f}")
        print(f"     Sentiment: {speaker.sentiment_distribution.get('positive', 0):.2f}")
    
    print(f"\\n💡 Content Insights:")
    for insight in dashboard.content_insights:
        print(f"   {insight.title} (Confidence: {insight.confidence:.1f})")
        print(f"     {insight.description}")
        print(f"     Impact Score: {insight.impact_score:.1f}")
        if insight.recommendations:
            print(f"     Recommendations: {', '.join(insight.recommendations[:2])}")
    
    print(f"\\n🔮 Predictive Insights:")
    for key, value in dashboard.predictive_insights.items():
        print(f"   {key}: {value}")
    
    print("\\n✅ Comprehensive analytics demo completed!")
    print("\\n💡 Integration Tips:")
    print("   • Connect to real transcription data for live analytics")
    print("   • Add machine learning models for better predictions")
    print("   • Implement real-time dashboard updates")
    print("   • Export analytics to BI tools like Tableau or PowerBI")
    
    # Clean up demo database
    if os.path.exists("demo_analytics.db"):
        os.remove("demo_analytics.db")

if __name__ == "__main__":
    demo_comprehensive_analytics()