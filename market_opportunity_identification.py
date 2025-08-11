"""
Market Opportunity Identification System

This module provides comprehensive market opportunity analysis through content data mining,
trend analysis, and intelligent opportunity scoring. It helps identify untapped content
opportunities and provides actionable market intelligence.

Requirements addressed:
- 5.2: AI-powered content intelligence with advanced analytics and insights generation
- 8.1: Comprehensive monitoring, security, and reliability features
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import requests
from textblob import TextBlob

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MarketOpportunity:
    """Represents a market opportunity with scoring and metadata"""
    id: str
    title: str
    description: str
    category: str
    opportunity_score: float
    market_size_estimate: float
    competition_level: str
    trend_direction: str
    confidence_score: float
    keywords: List[str]
    target_audience: List[str]
    content_gaps: List[str]
    recommended_actions: List[str]
    data_sources: List[str]
    created_at: datetime
    priority_level: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data

@dataclass
class TrendAnalysis:
    """Represents trend analysis results"""
    trend_name: str
    trend_strength: float
    growth_rate: float
    time_period: str
    related_keywords: List[str]
    market_impact: str
    opportunity_areas: List[str]
    confidence_level: float

@dataclass
class AudienceInsight:
    """Represents audience analysis insights"""
    segment_name: str
    size_estimate: int
    engagement_level: float
    content_preferences: List[str]
    unmet_needs: List[str]
    demographic_profile: Dict[str, Any]
    behavioral_patterns: List[str]

class MarketDataCollector:
    """Collects and processes market data from various sources"""
    
    def __init__(self):
        self.db_path = "market_intelligence.db"
        self.init_database()
    
    def init_database(self):
        """Initialize the market intelligence database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Market opportunities table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_opportunities (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    opportunity_score REAL,
                    market_size_estimate REAL,
                    competition_level TEXT,
                    trend_direction TEXT,
                    confidence_score REAL,
                    keywords TEXT,
                    target_audience TEXT,
                    content_gaps TEXT,
                    recommended_actions TEXT,
                    data_sources TEXT,
                    created_at TIMESTAMP,
                    priority_level TEXT
                )
            ''')
            
            # Market trends table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_trends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trend_name TEXT NOT NULL,
                    trend_strength REAL,
                    growth_rate REAL,
                    time_period TEXT,
                    related_keywords TEXT,
                    market_impact TEXT,
                    opportunity_areas TEXT,
                    confidence_level REAL,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Content analysis table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS content_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_id TEXT,
                    content_type TEXT,
                    keywords TEXT,
                    topics TEXT,
                    sentiment_score REAL,
                    engagement_metrics TEXT,
                    audience_segments TEXT,
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Market intelligence database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def collect_content_data(self, content_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Collect and analyze content data for opportunity identification"""
        analyzed_content = []
        
        try:
            for item in content_items:
                analysis = {
                    'content_id': item.get('id', ''),
                    'content_type': item.get('type', 'unknown'),
                    'text_content': item.get('transcript', '') or item.get('text', ''),
                    'metadata': item.get('metadata', {}),
                    'engagement_data': item.get('engagement', {}),
                    'timestamp': item.get('created_at', datetime.now())
                }
                
                # Extract keywords and topics
                if analysis['text_content']:
                    keywords = self._extract_keywords(analysis['text_content'])
                    topics = self._extract_topics(analysis['text_content'])
                    sentiment = self._analyze_sentiment(analysis['text_content'])
                    
                    analysis.update({
                        'keywords': keywords,
                        'topics': topics,
                        'sentiment_score': sentiment,
                        'word_count': len(analysis['text_content'].split()),
                        'language': self._detect_language(analysis['text_content'])
                    })
                
                analyzed_content.append(analysis)
            
            # Store in database
            self._store_content_analysis(analyzed_content)
            logger.info(f"Analyzed {len(analyzed_content)} content items")
            
            return analyzed_content
            
        except Exception as e:
            logger.error(f"Error collecting content data: {str(e)}")
            return []
    
    def _extract_keywords(self, text: str, max_keywords: int = 20) -> List[str]:
        """Extract important keywords from text"""
        try:
            # Use TF-IDF for keyword extraction
            vectorizer = TfidfVectorizer(
                max_features=max_keywords,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=1
            )
            
            tfidf_matrix = vectorizer.fit_transform([text])
            feature_names = vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]
            
            # Get top keywords with scores
            keyword_scores = list(zip(feature_names, scores))
            keyword_scores.sort(key=lambda x: x[1], reverse=True)
            
            return [kw for kw, score in keyword_scores if score > 0]
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            return []
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract main topics from text using simple clustering"""
        try:
            # Simple topic extraction based on noun phrases
            blob = TextBlob(text)
            noun_phrases = [str(phrase).lower() for phrase in blob.noun_phrases]
            
            # Count and return most common phrases, but also include single occurrences for short texts
            phrase_counts = Counter(noun_phrases)
            min_count = 1 if len(text.split()) < 50 else 2  # Lower threshold for short texts
            return [phrase for phrase, count in phrase_counts.most_common(10) if count >= min_count]
            
        except Exception as e:
            logger.error(f"Error extracting topics: {str(e)}")
            # Fallback: extract simple noun phrases manually
            words = text.lower().split()
            topics = []
            for i in range(len(words) - 1):
                if len(words[i]) > 3 and len(words[i+1]) > 3:
                    topics.append(f"{words[i]} {words[i+1]}")
            return topics[:5]
    
    def _analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of text content"""
        try:
            blob = TextBlob(text)
            return blob.sentiment.polarity
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return 0.0
    
    def _detect_language(self, text: str) -> str:
        """Detect language of text content"""
        try:
            blob = TextBlob(text)
            return blob.detect_language()
        except Exception as e:
            return 'en'  # Default to English
    
    def _store_content_analysis(self, analyzed_content: List[Dict[str, Any]]):
        """Store content analysis results in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for analysis in analyzed_content:
                cursor.execute('''
                    INSERT OR REPLACE INTO content_analysis 
                    (content_id, content_type, keywords, topics, sentiment_score, 
                     engagement_metrics, audience_segments)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    analysis['content_id'],
                    analysis['content_type'],
                    json.dumps(analysis.get('keywords', [])),
                    json.dumps(analysis.get('topics', [])),
                    analysis.get('sentiment_score', 0.0),
                    json.dumps(analysis.get('engagement_data', {})),
                    json.dumps(analysis.get('audience_segments', []))
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing content analysis: {str(e)}")

class TrendAnalyzer:
    """Analyzes market trends and identifies emerging opportunities"""
    
    def __init__(self, data_collector: MarketDataCollector):
        self.data_collector = data_collector
    
    def analyze_content_trends(self, time_period_days: int = 30) -> List[TrendAnalysis]:
        """Analyze content trends over specified time period"""
        try:
            conn = sqlite3.connect(self.data_collector.db_path)
            
            # Get recent content analysis data
            query = '''
                SELECT keywords, topics, sentiment_score, analyzed_at
                FROM content_analysis
                WHERE analyzed_at >= datetime('now', '-{} days')
            '''.format(time_period_days)
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if df.empty:
                logger.warning("No content data available for trend analysis")
                return []
            
            trends = []
            
            # Analyze keyword trends
            all_keywords = []
            for keywords_json in df['keywords']:
                try:
                    keywords = json.loads(keywords_json)
                    all_keywords.extend(keywords)
                except:
                    continue
            
            keyword_counts = Counter(all_keywords)
            
            # Identify trending keywords
            for keyword, count in keyword_counts.most_common(20):
                min_threshold = max(1, len(df) // 10)  # Dynamic threshold based on data size
                if count >= min_threshold:
                    trend_strength = min(count / len(df) * 10, 10.0)  # Normalize to 0-10
                    
                    trend = TrendAnalysis(
                        trend_name=f"Keyword: {keyword}",
                        trend_strength=trend_strength,
                        growth_rate=self._calculate_growth_rate(keyword, df),
                        time_period=f"{time_period_days} days",
                        related_keywords=self._find_related_keywords(keyword, all_keywords),
                        market_impact="Medium" if trend_strength > 5 else "Low",
                        opportunity_areas=self._identify_opportunity_areas(keyword),
                        confidence_level=min(trend_strength / 10, 1.0)
                    )
                    trends.append(trend)
            
            # Analyze topic trends
            all_topics = []
            for topics_json in df['topics']:
                try:
                    topics = json.loads(topics_json)
                    all_topics.extend(topics)
                except:
                    continue
            
            topic_counts = Counter(all_topics)
            
            for topic, count in topic_counts.most_common(10):
                min_threshold = max(1, len(df) // 15)  # Dynamic threshold for topics
                if count >= min_threshold:
                    trend_strength = min(count / len(df) * 8, 10.0)
                    
                    trend = TrendAnalysis(
                        trend_name=f"Topic: {topic}",
                        trend_strength=trend_strength,
                        growth_rate=self._calculate_topic_growth_rate(topic, df),
                        time_period=f"{time_period_days} days",
                        related_keywords=self._extract_topic_keywords(topic, all_keywords),
                        market_impact="High" if trend_strength > 7 else "Medium",
                        opportunity_areas=self._identify_topic_opportunities(topic),
                        confidence_level=min(trend_strength / 10, 1.0)
                    )
                    trends.append(trend)
            
            # Store trends in database
            self._store_trends(trends)
            
            logger.info(f"Identified {len(trends)} market trends")
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing content trends: {str(e)}")
            return []
    
    def _calculate_growth_rate(self, keyword: str, df: pd.DataFrame) -> float:
        """Calculate growth rate for a keyword over time"""
        try:
            # Simple growth calculation based on recent vs older occurrences
            df['date'] = pd.to_datetime(df['analyzed_at'])
            df_sorted = df.sort_values('date')
            
            mid_point = len(df_sorted) // 2
            older_half = df_sorted.iloc[:mid_point]
            recent_half = df_sorted.iloc[mid_point:]
            
            older_count = sum(1 for keywords_json in older_half['keywords'] 
                            if keyword in json.loads(keywords_json))
            recent_count = sum(1 for keywords_json in recent_half['keywords'] 
                             if keyword in json.loads(keywords_json))
            
            if older_count == 0:
                return 100.0 if recent_count > 0 else 0.0
            
            growth_rate = ((recent_count - older_count) / older_count) * 100
            return max(-100, min(growth_rate, 1000))  # Cap between -100% and 1000%
            
        except Exception as e:
            logger.error(f"Error calculating growth rate: {str(e)}")
            return 0.0
    
    def _calculate_topic_growth_rate(self, topic: str, df: pd.DataFrame) -> float:
        """Calculate growth rate for a topic over time"""
        try:
            df['date'] = pd.to_datetime(df['analyzed_at'])
            df_sorted = df.sort_values('date')
            
            mid_point = len(df_sorted) // 2
            older_half = df_sorted.iloc[:mid_point]
            recent_half = df_sorted.iloc[mid_point:]
            
            older_count = sum(1 for topics_json in older_half['topics'] 
                            if topic in json.loads(topics_json))
            recent_count = sum(1 for topics_json in recent_half['topics'] 
                             if topic in json.loads(topics_json))
            
            if older_count == 0:
                return 100.0 if recent_count > 0 else 0.0
            
            growth_rate = ((recent_count - older_count) / older_count) * 100
            return max(-100, min(growth_rate, 500))
            
        except Exception as e:
            return 0.0
    
    def _find_related_keywords(self, keyword: str, all_keywords: List[str]) -> List[str]:
        """Find keywords related to the given keyword"""
        try:
            # Simple co-occurrence based relationship
            related = []
            keyword_lower = keyword.lower()
            
            for kw in set(all_keywords):
                if kw != keyword and (
                    keyword_lower in kw.lower() or 
                    kw.lower() in keyword_lower or
                    len(set(keyword_lower.split()) & set(kw.lower().split())) > 0
                ):
                    related.append(kw)
            
            return related[:5]  # Return top 5 related keywords
            
        except Exception as e:
            return []
    
    def _identify_opportunity_areas(self, keyword: str) -> List[str]:
        """Identify opportunity areas based on keyword"""
        opportunity_mapping = {
            'ai': ['AI Tools', 'Automation', 'Machine Learning'],
            'video': ['Video Content', 'Streaming', 'Video Marketing'],
            'audio': ['Podcasting', 'Audio Content', 'Voice Technology'],
            'education': ['EdTech', 'Online Learning', 'Training'],
            'business': ['B2B Solutions', 'Enterprise Tools', 'Productivity'],
            'health': ['HealthTech', 'Wellness', 'Medical Technology'],
            'finance': ['FinTech', 'Investment', 'Financial Services'],
            'marketing': ['Digital Marketing', 'Content Marketing', 'Social Media'],
            'technology': ['Tech Innovation', 'Software Development', 'IT Solutions']
        }
        
        keyword_lower = keyword.lower()
        opportunities = []
        
        for key, areas in opportunity_mapping.items():
            if key in keyword_lower:
                opportunities.extend(areas)
        
        return opportunities[:3] if opportunities else ['General Market Opportunity']
    
    def _extract_topic_keywords(self, topic: str, all_keywords: List[str]) -> List[str]:
        """Extract keywords related to a topic"""
        topic_words = set(topic.lower().split())
        related_keywords = []
        
        for keyword in set(all_keywords):
            keyword_words = set(keyword.lower().split())
            if topic_words & keyword_words:  # If there's any overlap
                related_keywords.append(keyword)
        
        return related_keywords[:5]
    
    def _identify_topic_opportunities(self, topic: str) -> List[str]:
        """Identify opportunities based on topic analysis"""
        return [
            f"Content creation around '{topic}'",
            f"Educational materials for '{topic}'",
            f"Market analysis of '{topic}' trends"
        ]
    
    def _store_trends(self, trends: List[TrendAnalysis]):
        """Store trend analysis results in database"""
        try:
            conn = sqlite3.connect(self.data_collector.db_path)
            cursor = conn.cursor()
            
            for trend in trends:
                cursor.execute('''
                    INSERT INTO market_trends 
                    (trend_name, trend_strength, growth_rate, time_period, 
                     related_keywords, market_impact, opportunity_areas, confidence_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trend.trend_name,
                    trend.trend_strength,
                    trend.growth_rate,
                    trend.time_period,
                    json.dumps(trend.related_keywords),
                    trend.market_impact,
                    json.dumps(trend.opportunity_areas),
                    trend.confidence_level
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing trends: {str(e)}")

class OpportunityScorer:
    """Scores and prioritizes market opportunities"""
    
    def __init__(self, data_collector: MarketDataCollector):
        self.data_collector = data_collector
    
    def score_opportunities(self, trends: List[TrendAnalysis], 
                          content_analysis: List[Dict[str, Any]]) -> List[MarketOpportunity]:
        """Score and rank market opportunities"""
        opportunities = []
        
        try:
            # Generate opportunities from trends
            for trend in trends:
                opportunity = self._create_opportunity_from_trend(trend, content_analysis)
                if opportunity:
                    opportunities.append(opportunity)
            
            # Generate opportunities from content gaps
            gap_opportunities = self._identify_content_gaps(content_analysis)
            opportunities.extend(gap_opportunities)
            
            # Generate opportunities from audience analysis
            audience_opportunities = self._identify_audience_opportunities(content_analysis)
            opportunities.extend(audience_opportunities)
            
            # Score and rank opportunities
            scored_opportunities = self._score_and_rank_opportunities(opportunities)
            
            # Store opportunities in database
            self._store_opportunities(scored_opportunities)
            
            logger.info(f"Generated and scored {len(scored_opportunities)} market opportunities")
            return scored_opportunities
            
        except Exception as e:
            logger.error(f"Error scoring opportunities: {str(e)}")
            return []
    
    def _create_opportunity_from_trend(self, trend: TrendAnalysis, 
                                     content_analysis: List[Dict[str, Any]]) -> Optional[MarketOpportunity]:
        """Create market opportunity from trend analysis"""
        try:
            # Calculate opportunity score based on trend metrics
            base_score = (trend.trend_strength * 0.4 + 
                         min(abs(trend.growth_rate) / 10, 10) * 0.3 + 
                         trend.confidence_level * 10 * 0.3)
            
            # Adjust score based on competition level
            competition_level = self._assess_competition_level(trend.trend_name, content_analysis)
            competition_multiplier = {'Low': 1.2, 'Medium': 1.0, 'High': 0.8}[competition_level]
            
            opportunity_score = min(base_score * competition_multiplier, 10.0)
            
            # Estimate market size based on trend strength and growth
            market_size_estimate = self._estimate_market_size(trend)
            
            # Generate content gaps and recommendations
            content_gaps = self._identify_trend_content_gaps(trend, content_analysis)
            recommendations = self._generate_trend_recommendations(trend)
            
            opportunity = MarketOpportunity(
                id=f"trend_{hash(trend.trend_name)}_{int(datetime.now().timestamp())}",
                title=f"Market Opportunity: {trend.trend_name}",
                description=f"Emerging opportunity in {trend.trend_name} with {trend.growth_rate:.1f}% growth rate",
                category=self._categorize_trend(trend.trend_name),
                opportunity_score=opportunity_score,
                market_size_estimate=market_size_estimate,
                competition_level=competition_level,
                trend_direction="Up" if trend.growth_rate > 0 else "Down",
                confidence_score=trend.confidence_level,
                keywords=trend.related_keywords,
                target_audience=self._identify_target_audience(trend),
                content_gaps=content_gaps,
                recommended_actions=recommendations,
                data_sources=['Content Analysis', 'Trend Analysis'],
                created_at=datetime.now(),
                priority_level=self._determine_priority_level(opportunity_score)
            )
            
            return opportunity
            
        except Exception as e:
            logger.error(f"Error creating opportunity from trend: {str(e)}")
            return None
    
    def _assess_competition_level(self, trend_name: str, content_analysis: List[Dict[str, Any]]) -> str:
        """Assess competition level for a trend"""
        try:
            # Count content items related to this trend
            related_content_count = 0
            total_content = len(content_analysis)
            
            trend_keywords = trend_name.lower().split()
            
            for content in content_analysis:
                content_text = (content.get('text_content', '') + 
                              ' '.join(content.get('keywords', []))).lower()
                
                if any(keyword in content_text for keyword in trend_keywords):
                    related_content_count += 1
            
            if total_content == 0:
                return 'Low'
            
            competition_ratio = related_content_count / total_content
            
            if competition_ratio > 0.3:
                return 'High'
            elif competition_ratio > 0.1:
                return 'Medium'
            else:
                return 'Low'
                
        except Exception as e:
            return 'Medium'  # Default to medium competition
    
    def _estimate_market_size(self, trend: TrendAnalysis) -> float:
        """Estimate market size based on trend metrics"""
        try:
            # Simple heuristic based on trend strength and growth rate
            base_size = trend.trend_strength * 1000000  # Base in millions
            growth_multiplier = 1 + (trend.growth_rate / 100)
            confidence_multiplier = trend.confidence_level
            
            estimated_size = base_size * growth_multiplier * confidence_multiplier
            return max(100000, min(estimated_size, 1000000000))  # Cap between 100K and 1B
            
        except Exception as e:
            return 1000000  # Default 1M market size
    
    def _identify_trend_content_gaps(self, trend: TrendAnalysis, 
                                   content_analysis: List[Dict[str, Any]]) -> List[str]:
        """Identify content gaps related to a trend"""
        gaps = []
        
        # Common content gap categories
        gap_categories = [
            'Beginner tutorials',
            'Advanced guides',
            'Case studies',
            'Best practices',
            'Tool comparisons',
            'Industry analysis',
            'Future predictions',
            'Implementation guides'
        ]
        
        # Check which categories are underrepresented
        trend_keywords = trend.trend_name.lower().split()
        
        for category in gap_categories:
            category_content_count = 0
            
            for content in content_analysis:
                content_text = content.get('text_content', '').lower()
                category_keywords = category.lower().split()
                
                if (any(tk in content_text for tk in trend_keywords) and 
                    any(ck in content_text for ck in category_keywords)):
                    category_content_count += 1
            
            if category_content_count < 2:  # Threshold for gap identification
                gaps.append(f"{category} for {trend.trend_name}")
        
        return gaps[:5]  # Return top 5 gaps
    
    def _generate_trend_recommendations(self, trend: TrendAnalysis) -> List[str]:
        """Generate actionable recommendations for a trend"""
        recommendations = []
        
        if trend.growth_rate > 50:
            recommendations.append("Prioritize content creation in this rapidly growing area")
        
        if trend.confidence_level > 0.8:
            recommendations.append("High-confidence trend - consider significant investment")
        
        if trend.market_impact == "High":
            recommendations.append("Develop comprehensive content strategy around this trend")
        
        recommendations.extend([
            f"Create educational content about {trend.trend_name}",
            f"Develop tools or services related to {trend.trend_name}",
            f"Build community around {trend.trend_name} topics"
        ])
        
        return recommendations[:5]
    
    def _categorize_trend(self, trend_name: str) -> str:
        """Categorize trend into business category"""
        categories = {
            'Technology': ['ai', 'tech', 'software', 'digital', 'automation'],
            'Business': ['business', 'marketing', 'sales', 'strategy', 'management'],
            'Education': ['education', 'learning', 'training', 'course', 'tutorial'],
            'Health': ['health', 'wellness', 'medical', 'fitness', 'healthcare'],
            'Finance': ['finance', 'money', 'investment', 'crypto', 'fintech'],
            'Entertainment': ['entertainment', 'gaming', 'media', 'content', 'video'],
            'Lifestyle': ['lifestyle', 'travel', 'food', 'fashion', 'home']
        }
        
        trend_lower = trend_name.lower()
        
        for category, keywords in categories.items():
            if any(keyword in trend_lower for keyword in keywords):
                return category
        
        return 'General'
    
    def _identify_target_audience(self, trend: TrendAnalysis) -> List[str]:
        """Identify target audience for a trend"""
        # Simple audience mapping based on trend characteristics
        audiences = []
        
        if trend.trend_strength > 7:
            audiences.append('Early Adopters')
        
        if trend.growth_rate > 30:
            audiences.append('Growth-Oriented Businesses')
        
        if 'education' in trend.trend_name.lower():
            audiences.extend(['Students', 'Educators', 'Professionals'])
        
        if 'business' in trend.trend_name.lower():
            audiences.extend(['Business Owners', 'Entrepreneurs', 'Managers'])
        
        if 'technology' in trend.trend_name.lower():
            audiences.extend(['Tech Professionals', 'Developers', 'IT Managers'])
        
        return audiences[:3] if audiences else ['General Audience']
    
    def _identify_content_gaps(self, content_analysis: List[Dict[str, Any]]) -> List[MarketOpportunity]:
        """Identify opportunities based on content gaps"""
        opportunities = []
        
        try:
            # Analyze content distribution by topics
            all_topics = []
            for content in content_analysis:
                topics = content.get('topics', [])
                all_topics.extend(topics)
            
            topic_counts = Counter(all_topics)
            
            # Identify underrepresented but potentially valuable topics
            max_count = max(topic_counts.values()) if topic_counts else 1
            threshold = max(1, max_count // 3)  # Dynamic threshold
            underrepresented_topics = [
                topic for topic, count in topic_counts.items() 
                if 1 <= count <= threshold and len(topic.split()) >= 2
            ]
            
            for topic in underrepresented_topics[:5]:  # Top 5 gaps
                opportunity = MarketOpportunity(
                    id=f"gap_{hash(topic)}_{int(datetime.now().timestamp())}",
                    title=f"Content Gap Opportunity: {topic.title()}",
                    description=f"Underrepresented topic with potential for content development",
                    category="Content Gap",
                    opportunity_score=6.0,  # Medium opportunity score
                    market_size_estimate=500000,  # Estimated market size
                    competition_level="Low",
                    trend_direction="Stable",
                    confidence_score=0.7,
                    keywords=topic.split(),
                    target_audience=["Content Consumers", "Industry Professionals"],
                    content_gaps=[f"Comprehensive content about {topic}"],
                    recommended_actions=[
                        f"Create detailed content about {topic}",
                        f"Research audience interest in {topic}",
                        f"Develop content series around {topic}"
                    ],
                    data_sources=['Content Gap Analysis'],
                    created_at=datetime.now(),
                    priority_level="Medium"
                )
                opportunities.append(opportunity)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error identifying content gaps: {str(e)}")
            return []
    
    def _identify_audience_opportunities(self, content_analysis: List[Dict[str, Any]]) -> List[MarketOpportunity]:
        """Identify opportunities based on audience analysis"""
        opportunities = []
        
        try:
            # Analyze sentiment patterns to identify audience needs
            positive_content = [c for c in content_analysis if c.get('sentiment_score', 0) > 0.3]
            negative_content = [c for c in content_analysis if c.get('sentiment_score', 0) < -0.3]
            
            if len(negative_content) > len(positive_content) * 0.3:
                # High negative sentiment indicates opportunity for better content
                opportunity = MarketOpportunity(
                    id=f"audience_sentiment_{int(datetime.now().timestamp())}",
                    title="Audience Satisfaction Opportunity",
                    description="High negative sentiment indicates opportunity for improved content",
                    category="Audience Insight",
                    opportunity_score=7.5,
                    market_size_estimate=750000,
                    competition_level="Medium",
                    trend_direction="Up",
                    confidence_score=0.8,
                    keywords=["audience satisfaction", "content quality", "user experience"],
                    target_audience=["Dissatisfied Users", "Quality-Seeking Audience"],
                    content_gaps=["High-quality, engaging content"],
                    recommended_actions=[
                        "Improve content quality and engagement",
                        "Address common pain points in content",
                        "Develop user-centric content strategy"
                    ],
                    data_sources=['Sentiment Analysis'],
                    created_at=datetime.now(),
                    priority_level="High"
                )
                opportunities.append(opportunity)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error identifying audience opportunities: {str(e)}")
            return []
    
    def _score_and_rank_opportunities(self, opportunities: List[MarketOpportunity]) -> List[MarketOpportunity]:
        """Score and rank opportunities by priority"""
        try:
            # Sort by opportunity score (descending)
            sorted_opportunities = sorted(opportunities, 
                                        key=lambda x: x.opportunity_score, 
                                        reverse=True)
            
            # Update priority levels based on ranking and score thresholds
            for i, opp in enumerate(sorted_opportunities):
                if opp.opportunity_score >= 8.0:  # High score threshold
                    opp.priority_level = "High"
                elif opp.opportunity_score >= 6.0:  # Medium score threshold
                    opp.priority_level = "Medium"
                else:  # Low score
                    opp.priority_level = "Low"
            
            return sorted_opportunities
            
        except Exception as e:
            logger.error(f"Error scoring and ranking opportunities: {str(e)}")
            return opportunities
    
    def _determine_priority_level(self, opportunity_score: float) -> str:
        """Determine priority level based on opportunity score"""
        if opportunity_score >= 8.0:
            return "High"
        elif opportunity_score >= 6.0:
            return "Medium"
        else:
            return "Low"
    
    def _store_opportunities(self, opportunities: List[MarketOpportunity]):
        """Store opportunities in database"""
        try:
            conn = sqlite3.connect(self.data_collector.db_path)
            cursor = conn.cursor()
            
            for opp in opportunities:
                cursor.execute('''
                    INSERT OR REPLACE INTO market_opportunities 
                    (id, title, description, category, opportunity_score, market_size_estimate,
                     competition_level, trend_direction, confidence_score, keywords, target_audience,
                     content_gaps, recommended_actions, data_sources, created_at, priority_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    opp.id, opp.title, opp.description, opp.category, opp.opportunity_score,
                    opp.market_size_estimate, opp.competition_level, opp.trend_direction,
                    opp.confidence_score, json.dumps(opp.keywords), json.dumps(opp.target_audience),
                    json.dumps(opp.content_gaps), json.dumps(opp.recommended_actions),
                    json.dumps(opp.data_sources), opp.created_at.isoformat(), opp.priority_level
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing opportunities: {str(e)}")

class MarketOpportunityIdentificationSystem:
    """Main system for market opportunity identification"""
    
    def __init__(self):
        self.data_collector = MarketDataCollector()
        self.trend_analyzer = TrendAnalyzer(self.data_collector)
        self.opportunity_scorer = OpportunityScorer(self.data_collector)
    
    async def identify_opportunities(self, content_items: List[Dict[str, Any]], 
                                   time_period_days: int = 30) -> Dict[str, Any]:
        """Main method to identify market opportunities"""
        try:
            logger.info("Starting market opportunity identification process")
            
            # Step 1: Collect and analyze content data
            logger.info("Collecting and analyzing content data...")
            analyzed_content = self.data_collector.collect_content_data(content_items)
            
            if not analyzed_content:
                logger.warning("No content data available for analysis")
                return {
                    'success': False,
                    'message': 'No content data available for analysis',
                    'opportunities': [],
                    'trends': [],
                    'summary': {}
                }
            
            # Step 2: Analyze trends
            logger.info("Analyzing market trends...")
            trends = self.trend_analyzer.analyze_content_trends(time_period_days)
            
            # Step 3: Score and identify opportunities
            logger.info("Scoring and identifying opportunities...")
            opportunities = self.opportunity_scorer.score_opportunities(trends, analyzed_content)
            
            # Step 4: Generate summary report
            summary = self._generate_summary_report(opportunities, trends, analyzed_content)
            
            logger.info(f"Market opportunity identification completed. Found {len(opportunities)} opportunities")
            
            return {
                'success': True,
                'message': f'Successfully identified {len(opportunities)} market opportunities',
                'opportunities': [opp.to_dict() for opp in opportunities],
                'trends': [asdict(trend) for trend in trends],
                'summary': summary,
                'analysis_metadata': {
                    'content_items_analyzed': len(analyzed_content),
                    'trends_identified': len(trends),
                    'opportunities_found': len(opportunities),
                    'analysis_date': datetime.now().isoformat(),
                    'time_period_days': time_period_days
                }
            }
            
        except Exception as e:
            logger.error(f"Error in market opportunity identification: {str(e)}")
            return {
                'success': False,
                'message': f'Error in analysis: {str(e)}',
                'opportunities': [],
                'trends': [],
                'summary': {}
            }
    
    def get_opportunity_report(self, opportunity_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed report for a specific opportunity"""
        try:
            conn = sqlite3.connect(self.data_collector.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM market_opportunities WHERE id = ?
            ''', (opportunity_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            # Convert row to dictionary
            columns = [desc[0] for desc in cursor.description]
            opportunity_data = dict(zip(columns, row))
            
            # Parse JSON fields
            json_fields = ['keywords', 'target_audience', 'content_gaps', 
                          'recommended_actions', 'data_sources']
            for field in json_fields:
                if opportunity_data.get(field):
                    opportunity_data[field] = json.loads(opportunity_data[field])
            
            return opportunity_data
            
        except Exception as e:
            logger.error(f"Error getting opportunity report: {str(e)}")
            return None
    
    def get_market_intelligence_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive market intelligence dashboard data"""
        try:
            conn = sqlite3.connect(self.data_collector.db_path)
            
            # Get opportunity statistics
            opp_df = pd.read_sql_query('''
                SELECT category, priority_level, opportunity_score, market_size_estimate
                FROM market_opportunities
                ORDER BY created_at DESC
                LIMIT 100
            ''', conn)
            
            # Get trend statistics
            trend_df = pd.read_sql_query('''
                SELECT trend_name, trend_strength, growth_rate, market_impact
                FROM market_trends
                ORDER BY detected_at DESC
                LIMIT 50
            ''', conn)
            
            conn.close()
            
            dashboard_data = {
                'opportunity_summary': {
                    'total_opportunities': len(opp_df),
                    'high_priority_count': len(opp_df[opp_df['priority_level'] == 'High']),
                    'average_opportunity_score': float(opp_df['opportunity_score'].mean()) if not opp_df.empty else 0,
                    'total_market_size': float(opp_df['market_size_estimate'].sum()) if not opp_df.empty else 0,
                    'category_distribution': opp_df['category'].value_counts().to_dict() if not opp_df.empty else {}
                },
                'trend_summary': {
                    'total_trends': len(trend_df),
                    'high_impact_trends': len(trend_df[trend_df['market_impact'] == 'High']),
                    'average_trend_strength': float(trend_df['trend_strength'].mean()) if not trend_df.empty else 0,
                    'average_growth_rate': float(trend_df['growth_rate'].mean()) if not trend_df.empty else 0
                },
                'top_opportunities': opp_df.head(10).to_dict('records') if not opp_df.empty else [],
                'top_trends': trend_df.head(10).to_dict('records') if not trend_df.empty else [],
                'generated_at': datetime.now().isoformat()
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating dashboard data: {str(e)}")
            return {
                'opportunity_summary': {},
                'trend_summary': {},
                'top_opportunities': [],
                'top_trends': [],
                'generated_at': datetime.now().isoformat()
            }
    
    def _generate_summary_report(self, opportunities: List[MarketOpportunity], 
                               trends: List[TrendAnalysis], 
                               analyzed_content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive summary report"""
        try:
            # Opportunity analysis
            high_priority_opps = [opp for opp in opportunities if opp.priority_level == "High"]
            total_market_size = sum(opp.market_size_estimate for opp in opportunities)
            
            # Trend analysis
            high_growth_trends = [trend for trend in trends if trend.growth_rate > 50]
            high_impact_trends = [trend for trend in trends if trend.market_impact == "High"]
            
            # Content analysis
            avg_sentiment = np.mean([c.get('sentiment_score', 0) for c in analyzed_content])
            total_keywords = len(set(kw for c in analyzed_content for kw in c.get('keywords', [])))
            
            summary = {
                'executive_summary': {
                    'total_opportunities_identified': len(opportunities),
                    'high_priority_opportunities': len(high_priority_opps),
                    'estimated_total_market_size': total_market_size,
                    'trends_analyzed': len(trends),
                    'high_growth_trends': len(high_growth_trends),
                    'content_items_analyzed': len(analyzed_content)
                },
                'key_insights': [
                    f"Identified {len(opportunities)} market opportunities with total estimated value of ${total_market_size:,.0f}",
                    f"Found {len(high_priority_opps)} high-priority opportunities requiring immediate attention",
                    f"Detected {len(high_growth_trends)} rapidly growing trends with >50% growth rate",
                    f"Analyzed {total_keywords} unique keywords across {len(analyzed_content)} content items",
                    f"Average content sentiment: {'Positive' if avg_sentiment > 0.1 else 'Negative' if avg_sentiment < -0.1 else 'Neutral'}"
                ],
                'top_categories': self._get_top_categories(opportunities),
                'recommended_actions': self._get_top_recommendations(opportunities),
                'market_outlook': self._generate_market_outlook(trends),
                'risk_assessment': self._assess_market_risks(opportunities, trends)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary report: {str(e)}")
            return {}
    
    def _get_top_categories(self, opportunities: List[MarketOpportunity]) -> List[Dict[str, Any]]:
        """Get top opportunity categories"""
        category_counts = Counter(opp.category for opp in opportunities)
        category_scores = defaultdict(list)
        
        for opp in opportunities:
            category_scores[opp.category].append(opp.opportunity_score)
        
        top_categories = []
        for category, count in category_counts.most_common(5):
            avg_score = np.mean(category_scores[category])
            top_categories.append({
                'category': category,
                'opportunity_count': count,
                'average_score': round(avg_score, 2),
                'total_market_size': sum(opp.market_size_estimate for opp in opportunities if opp.category == category)
            })
        
        return top_categories
    
    def _get_top_recommendations(self, opportunities: List[MarketOpportunity]) -> List[str]:
        """Get top recommended actions across all opportunities"""
        all_recommendations = []
        for opp in opportunities:
            all_recommendations.extend(opp.recommended_actions)
        
        recommendation_counts = Counter(all_recommendations)
        return [rec for rec, count in recommendation_counts.most_common(10)]
    
    def _generate_market_outlook(self, trends: List[TrendAnalysis]) -> Dict[str, Any]:
        """Generate market outlook based on trends"""
        if not trends:
            return {'outlook': 'Neutral', 'confidence': 'Low', 'summary': 'Insufficient data for outlook'}
        
        avg_growth_rate = np.mean([trend.growth_rate for trend in trends])
        avg_confidence = np.mean([trend.confidence_level for trend in trends])
        high_impact_count = len([trend for trend in trends if trend.market_impact == "High"])
        
        if avg_growth_rate > 20 and high_impact_count > len(trends) * 0.3:
            outlook = 'Very Positive'
        elif avg_growth_rate > 10:
            outlook = 'Positive'
        elif avg_growth_rate > -10:
            outlook = 'Neutral'
        else:
            outlook = 'Negative'
        
        confidence = 'High' if avg_confidence > 0.7 else 'Medium' if avg_confidence > 0.5 else 'Low'
        
        return {
            'outlook': outlook,
            'confidence': confidence,
            'average_growth_rate': round(avg_growth_rate, 2),
            'high_impact_trends': high_impact_count,
            'summary': f"Market shows {outlook.lower()} outlook with {confidence.lower()} confidence based on {len(trends)} trends analyzed"
        }
    
    def _assess_market_risks(self, opportunities: List[MarketOpportunity], 
                           trends: List[TrendAnalysis]) -> Dict[str, Any]:
        """Assess market risks based on opportunities and trends"""
        risks = []
        risk_level = 'Low'
        
        # Check for high competition
        high_competition_count = len([opp for opp in opportunities if opp.competition_level == "High"])
        if high_competition_count > len(opportunities) * 0.4:
            risks.append("High competition in multiple opportunity areas")
            risk_level = 'Medium'
        
        # Check for declining trends
        declining_trends = [trend for trend in trends if trend.growth_rate < -20]
        if declining_trends:
            risks.append(f"{len(declining_trends)} trends showing significant decline")
            risk_level = 'High' if len(declining_trends) > 3 else 'Medium'
        
        # Check for low confidence opportunities
        low_confidence_count = len([opp for opp in opportunities if opp.confidence_score < 0.5])
        if low_confidence_count > len(opportunities) * 0.3:
            risks.append("Many opportunities have low confidence scores")
            if risk_level == 'Low':
                risk_level = 'Medium'
        
        if not risks:
            risks.append("No significant risks identified")
        
        return {
            'risk_level': risk_level,
            'identified_risks': risks,
            'mitigation_strategies': [
                "Diversify opportunity portfolio",
                "Monitor trend changes closely",
                "Validate opportunities with additional data",
                "Start with low-risk, high-confidence opportunities"
            ]
        }

# Example usage and testing functions
def create_sample_content_data() -> List[Dict[str, Any]]:
    """Create sample content data for testing"""
    return [
        {
            'id': 'content_1',
            'type': 'audio',
            'transcript': 'This video discusses artificial intelligence and machine learning trends in business automation',
            'metadata': {'duration': 300, 'language': 'en'},
            'engagement': {'views': 1500, 'likes': 120},
            'created_at': datetime.now() - timedelta(days=5)
        },
        {
            'id': 'content_2',
            'type': 'video',
            'transcript': 'Educational content about digital marketing strategies and social media optimization',
            'metadata': {'duration': 450, 'language': 'en'},
            'engagement': {'views': 2300, 'likes': 180},
            'created_at': datetime.now() - timedelta(days=10)
        },
        {
            'id': 'content_3',
            'type': 'audio',
            'transcript': 'Healthcare technology innovations and telemedicine adoption in modern medical practice',
            'metadata': {'duration': 600, 'language': 'en'},
            'engagement': {'views': 800, 'likes': 65},
            'created_at': datetime.now() - timedelta(days=15)
        }
    ]

async def main():
    """Main function for testing the system"""
    try:
        # Initialize the system
        system = MarketOpportunityIdentificationSystem()
        
        # Create sample data
        sample_content = create_sample_content_data()
        
        # Run opportunity identification
        results = await system.identify_opportunities(sample_content, time_period_days=30)
        
        print("Market Opportunity Identification Results:")
        print(f"Success: {results['success']}")
        print(f"Message: {results['message']}")
        print(f"Opportunities found: {len(results['opportunities'])}")
        print(f"Trends identified: {len(results['trends'])}")
        
        # Display top opportunities
        if results['opportunities']:
            print("\nTop Opportunities:")
            for i, opp in enumerate(results['opportunities'][:3], 1):
                print(f"{i}. {opp['title']} (Score: {opp['opportunity_score']:.2f})")
                print(f"   Category: {opp['category']}")
                print(f"   Priority: {opp['priority_level']}")
                print(f"   Market Size: ${opp['market_size_estimate']:,.0f}")
                print()
        
        # Get dashboard data
        dashboard = system.get_market_intelligence_dashboard()
        print("Market Intelligence Dashboard:")
        print(f"Total Opportunities: {dashboard['opportunity_summary'].get('total_opportunities', 0)}")
        print(f"High Priority: {dashboard['opportunity_summary'].get('high_priority_count', 0)}")
        print(f"Average Score: {dashboard['opportunity_summary'].get('average_opportunity_score', 0):.2f}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        return None

if __name__ == "__main__":
    # Run the system
    results = asyncio.run(main())