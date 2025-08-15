#!/usr/bin/env python3
"""
Market Research and Competitive Intelligence System
Task 147: Comprehensive system for analyzing market trends, competitor mentions,
customer feedback, and business intelligence from transcribed content.
"""

import asyncio
import json
import re
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set
import hashlib
import logging
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntelligenceType(Enum):
    """Types of intelligence gathering."""
    COMPETITIVE = "competitive"
    MARKET_TRENDS = "market_trends"
    CUSTOMER_SENTIMENT = "customer_sentiment"
    PRODUCT_FEEDBACK = "product_feedback"
    BRAND_PERCEPTION = "brand_perception"
    PRICING_INTELLIGENCE = "pricing_intelligence"
    FEATURE_ANALYSIS = "feature_analysis"
    MARKET_OPPORTUNITY = "market_opportunity"

class CompetitorMention(Enum):
    """Types of competitor mentions."""
    DIRECT_COMPARISON = "direct_comparison"
    SWITCHING_INTENT = "switching_intent"
    FEATURE_COMPARISON = "feature_comparison"
    PRICING_COMPARISON = "pricing_comparison"
    SERVICE_COMPARISON = "service_comparison"
    GENERAL_MENTION = "general_mention"

class SentimentTrend(Enum):
    """Sentiment trend directions."""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    VOLATILE = "volatile"

class MarketOpportunity(Enum):
    """Market opportunity types."""
    PRODUCT_GAP = "product_gap"
    SERVICE_IMPROVEMENT = "service_improvement"
    PRICING_ADVANTAGE = "pricing_advantage"
    MARKET_EXPANSION = "market_expansion"
    CUSTOMER_RETENTION = "customer_retention"

@dataclass
class CompetitorIntelligence:
    """Intelligence about competitors."""
    competitor_name: str
    mention_type: CompetitorMention
    context: str
    sentiment: str  # positive, negative, neutral
    source_segment: str
    timestamp: str
    confidence: float
    mentioned_features: List[str] = field(default_factory=list)
    pricing_info: Optional[str] = None
    switching_likelihood: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MarketTrend:
    """Identified market trend."""
    trend_id: str
    trend_category: str
    trend_description: str
    strength: float  # 0-1
    direction: str  # increasing, decreasing, stable
    supporting_evidence: List[str]
    time_period: str
    affected_segments: List[str]
    business_impact: str  # high, medium, low
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProductInsight:
    """Product-related market insight."""
    insight_id: str
    product_category: str
    insight_type: str  # feature_request, bug_report, usage_pattern, etc.
    description: str
    frequency: int  # how often mentioned
    sentiment: str
    priority: str  # high, medium, low
    customer_segments: List[str]
    competitive_implications: str
    recommended_actions: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BrandPerception:
    """Brand perception analysis."""
    brand_name: str
    overall_sentiment: str
    reputation_score: float  # 0-1
    key_attributes: Dict[str, float]  # attribute -> score
    comparison_to_competitors: Dict[str, float]  # competitor -> relative score
    perception_trends: List[Dict[str, Any]]
    customer_testimonials: List[str]
    areas_for_improvement: List[str]
    competitive_advantages: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MarketOpportunityInsight:
    """Market opportunity analysis."""
    opportunity_id: str
    opportunity_type: MarketOpportunity
    description: str
    market_size_estimate: Optional[str] = None
    revenue_potential: Optional[str] = None
    implementation_complexity: str = "medium"  # low, medium, high
    time_to_market: Optional[str] = None
    competitive_advantage: float = 0.0  # 0-1
    customer_demand_level: str = "medium"
    supporting_data: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    success_probability: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MarketIntelligenceReport:
    """Complete market intelligence analysis."""
    report_id: str
    intelligence_type: IntelligenceType
    analysis_period: str
    data_sources: List[str]
    competitor_intelligence: List[CompetitorIntelligence]
    market_trends: List[MarketTrend]
    product_insights: List[ProductInsight]
    brand_perception: Optional[BrandPerception]
    market_opportunities: List[MarketOpportunityInsight]
    key_findings: List[str]
    strategic_recommendations: List[str]
    executive_summary: str
    confidence_score: float
    processing_metadata: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class CompetitorAnalyzer:
    """Analyzes competitor mentions and competitive intelligence."""
    
    def __init__(self):
        self.competitor_patterns = self._initialize_competitor_patterns()
        self.comparison_indicators = self._initialize_comparison_indicators()
    
    def _initialize_competitor_patterns(self) -> Dict[str, List[str]]:
        """Initialize competitor detection patterns."""
        return {
            'direct_competitors': [
                'Microsoft', 'Google', 'Amazon', 'Apple', 'Meta', 'Salesforce',
                'Oracle', 'IBM', 'Adobe', 'Zoom', 'Slack', 'Dropbox'
            ],
            'industry_terms': [
                'competitor', 'competition', 'rival', 'alternative',
                'versus', 'compared to', 'better than', 'worse than'
            ],
            'switching_indicators': [
                'switch to', 'moving to', 'considering', 'looking at',
                'migrating to', 'replacing with', 'instead of'
            ]
        }
    
    def _initialize_comparison_indicators(self) -> Dict[str, List[str]]:
        """Initialize comparison indicator patterns."""
        return {
            'feature_comparison': [
                'features', 'functionality', 'capabilities', 'tools',
                'interface', 'usability', 'performance'
            ],
            'pricing_comparison': [
                'price', 'cost', 'expensive', 'cheaper', 'affordable',
                'pricing', 'subscription', 'fee', 'budget'
            ],
            'service_comparison': [
                'support', 'service', 'customer service', 'help',
                'response time', 'reliability', 'uptime'
            ]
        }
    
    def analyze_competitive_mentions(self, text: str, source_info: Dict[str, Any]) -> List[CompetitorIntelligence]:
        """Analyze text for competitive intelligence."""
        competitive_mentions = []
        text_lower = text.lower()
        
        # Find competitor mentions
        for competitor in self.competitor_patterns['direct_competitors']:
            if competitor.lower() in text_lower:
                mention_type = self._classify_mention_type(text, competitor)
                sentiment = self._analyze_competitor_sentiment(text, competitor)
                
                # Extract context around mention
                context = self._extract_context(text, competitor)
                
                mention = CompetitorIntelligence(
                    competitor_name=competitor,
                    mention_type=mention_type,
                    context=context,
                    sentiment=sentiment,
                    source_segment=text[:200] + "..." if len(text) > 200 else text,
                    timestamp=datetime.now().isoformat(),
                    confidence=self._calculate_mention_confidence(text, competitor),
                    mentioned_features=self._extract_mentioned_features(text),
                    pricing_info=self._extract_pricing_info(text),
                    switching_likelihood=self._calculate_switching_likelihood(text, competitor)
                )
                competitive_mentions.append(mention)
        
        return competitive_mentions
    
    def _classify_mention_type(self, text: str, competitor: str) -> CompetitorMention:
        """Classify the type of competitor mention."""
        text_lower = text.lower()
        
        # Check for switching intent
        if any(indicator in text_lower for indicator in self.competitor_patterns['switching_indicators']):
            return CompetitorMention.SWITCHING_INTENT
        
        # Check for comparison types
        if any(term in text_lower for term in self.comparison_indicators['feature_comparison']):
            return CompetitorMention.FEATURE_COMPARISON
        elif any(term in text_lower for term in self.comparison_indicators['pricing_comparison']):
            return CompetitorMention.PRICING_COMPARISON
        elif any(term in text_lower for term in self.comparison_indicators['service_comparison']):
            return CompetitorMention.SERVICE_COMPARISON
        
        # Check for direct comparison
        if any(term in text_lower for term in ['vs', 'versus', 'compared to', 'better than']):
            return CompetitorMention.DIRECT_COMPARISON
        
        return CompetitorMention.GENERAL_MENTION
    
    def _analyze_competitor_sentiment(self, text: str, competitor: str) -> str:
        """Analyze sentiment toward competitor mention."""
        text_lower = text.lower()
        
        positive_indicators = ['better', 'superior', 'excellent', 'great', 'love', 'prefer']
        negative_indicators = ['worse', 'terrible', 'awful', 'hate', 'disappointing', 'inferior']
        
        # Get context around competitor mention
        competitor_index = text_lower.find(competitor.lower())
        if competitor_index == -1:
            return 'neutral'
        
        context_start = max(0, competitor_index - 100)
        context_end = min(len(text), competitor_index + 100)
        context = text[context_start:context_end].lower()
        
        positive_score = sum(1 for indicator in positive_indicators if indicator in context)
        negative_score = sum(1 for indicator in negative_indicators if indicator in context)
        
        if positive_score > negative_score:
            return 'positive'
        elif negative_score > positive_score:
            return 'negative'
        else:
            return 'neutral'
    
    def _extract_context(self, text: str, competitor: str, context_length: int = 150) -> str:
        """Extract context around competitor mention."""
        competitor_index = text.lower().find(competitor.lower())
        if competitor_index == -1:
            return text[:context_length]
        
        start = max(0, competitor_index - context_length//2)
        end = min(len(text), competitor_index + context_length//2)
        return text[start:end].strip()
    
    def _calculate_mention_confidence(self, text: str, competitor: str) -> float:
        """Calculate confidence score for competitor mention."""
        # Base confidence
        confidence = 0.7
        
        # Increase if explicit comparison
        if any(term in text.lower() for term in ['vs', 'versus', 'compared to']):
            confidence += 0.2
        
        # Increase if detailed context
        if len(text.split()) > 20:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _extract_mentioned_features(self, text: str) -> List[str]:
        """Extract product features mentioned in context."""
        feature_patterns = [
            'interface', 'dashboard', 'reporting', 'analytics', 'integration',
            'security', 'performance', 'scalability', 'mobile app', 'API'
        ]
        
        mentioned_features = []
        text_lower = text.lower()
        
        for feature in feature_patterns:
            if feature in text_lower:
                mentioned_features.append(feature)
        
        return mentioned_features
    
    def _extract_pricing_info(self, text: str) -> Optional[str]:
        """Extract pricing information if mentioned."""
        pricing_pattern = r'\$[\d,]+(?:\.\d{2})?'
        matches = re.findall(pricing_pattern, text)
        
        if matches:
            return matches[0]
        
        # Look for pricing terms
        pricing_terms = ['expensive', 'cheap', 'affordable', 'overpriced', 'good value']
        text_lower = text.lower()
        
        for term in pricing_terms:
            if term in text_lower:
                return term
        
        return None
    
    def _calculate_switching_likelihood(self, text: str, competitor: str) -> Optional[float]:
        """Calculate likelihood of switching to competitor."""
        text_lower = text.lower()
        
        high_likelihood_indicators = ['switching to', 'moving to', 'migrating to', 'definitely going with']
        medium_likelihood_indicators = ['considering', 'looking at', 'thinking about', 'evaluating']
        low_likelihood_indicators = ['might try', 'heard good things', 'curious about']
        
        if any(indicator in text_lower for indicator in high_likelihood_indicators):
            return 0.8
        elif any(indicator in text_lower for indicator in medium_likelihood_indicators):
            return 0.5
        elif any(indicator in text_lower for indicator in low_likelihood_indicators):
            return 0.2
        
        return None

class TrendAnalyzer:
    """Analyzes market trends from transcribed content."""
    
    def __init__(self):
        self.trend_patterns = self._initialize_trend_patterns()
    
    def _initialize_trend_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize trend detection patterns."""
        return {
            'technology_adoption': {
                'keywords': ['AI', 'machine learning', 'automation', 'cloud', 'digital transformation'],
                'growth_indicators': ['growing', 'increasing', 'expanding', 'rising', 'trending'],
                'decline_indicators': ['declining', 'decreasing', 'falling', 'shrinking']
            },
            'remote_work': {
                'keywords': ['remote work', 'work from home', 'hybrid', 'distributed team'],
                'growth_indicators': ['more common', 'standard practice', 'new normal'],
                'decline_indicators': ['back to office', 'returning to workplace']
            },
            'sustainability': {
                'keywords': ['green', 'sustainable', 'eco-friendly', 'carbon neutral', 'environmental'],
                'growth_indicators': ['important', 'priority', 'focus on'],
                'decline_indicators': ['less concern', 'not a priority']
            },
            'security_privacy': {
                'keywords': ['security', 'privacy', 'data protection', 'cybersecurity', 'compliance'],
                'growth_indicators': ['increased concern', 'more important', 'higher priority'],
                'decline_indicators': ['less worried', 'not as important']
            }
        }
    
    def identify_trends(self, text_segments: List[str], time_period: str = "current") -> List[MarketTrend]:
        """Identify market trends from text segments."""
        trends = []
        
        for trend_category, patterns in self.trend_patterns.items():
            trend_mentions = 0
            supporting_evidence = []
            direction_score = 0
            
            for segment in text_segments:
                segment_lower = segment.lower()
                
                # Check if trend keywords are mentioned
                if any(keyword in segment_lower for keyword in patterns['keywords']):
                    trend_mentions += 1
                    supporting_evidence.append(segment[:100] + "..." if len(segment) > 100 else segment)
                    
                    # Analyze direction
                    if any(indicator in segment_lower for indicator in patterns['growth_indicators']):
                        direction_score += 1
                    elif any(indicator in segment_lower for indicator in patterns['decline_indicators']):
                        direction_score -= 1
            
            if trend_mentions > 0:
                # Determine trend direction
                if direction_score > 0:
                    direction = "increasing"
                elif direction_score < 0:
                    direction = "decreasing"
                else:
                    direction = "stable"
                
                # Calculate trend strength
                strength = min(trend_mentions / len(text_segments) * 2, 1.0)
                
                trend = MarketTrend(
                    trend_id=str(uuid.uuid4()),
                    trend_category=trend_category,
                    trend_description=self._generate_trend_description(trend_category, direction, trend_mentions),
                    strength=strength,
                    direction=direction,
                    supporting_evidence=supporting_evidence[:5],  # Top 5 examples
                    time_period=time_period,
                    affected_segments=self._identify_affected_segments(supporting_evidence),
                    business_impact=self._assess_business_impact(trend_category, strength),
                    confidence=min(strength * 0.8 + 0.2, 1.0)
                )
                trends.append(trend)
        
        return trends
    
    def _generate_trend_description(self, category: str, direction: str, mentions: int) -> str:
        """Generate human-readable trend description."""
        direction_text = {
            "increasing": "growing in importance",
            "decreasing": "becoming less significant",
            "stable": "maintaining steady relevance"
        }
        
        return f"{category.replace('_', ' ').title()} is {direction_text[direction]} with {mentions} mentions in analyzed content."
    
    def _identify_affected_segments(self, evidence: List[str]) -> List[str]:
        """Identify customer/market segments affected by trend."""
        segments = []
        
        segment_indicators = {
            'enterprise': ['enterprise', 'large company', 'corporation', 'big business'],
            'smb': ['small business', 'medium business', 'startup', 'SMB'],
            'consumer': ['consumer', 'individual', 'personal use', 'home user'],
            'healthcare': ['healthcare', 'medical', 'hospital', 'clinic'],
            'education': ['education', 'school', 'university', 'academic'],
            'government': ['government', 'public sector', 'federal', 'state']
        }
        
        evidence_text = ' '.join(evidence).lower()
        
        for segment, indicators in segment_indicators.items():
            if any(indicator in evidence_text for indicator in indicators):
                segments.append(segment)
        
        return segments or ['general_market']
    
    def _assess_business_impact(self, category: str, strength: float) -> str:
        """Assess business impact level of trend."""
        # High impact categories
        high_impact_categories = ['technology_adoption', 'security_privacy']
        
        if category in high_impact_categories and strength > 0.6:
            return 'high'
        elif strength > 0.4:
            return 'medium'
        else:
            return 'low'

class ProductFeedbackAnalyzer:
    """Analyzes product feedback and feature requests."""
    
    def __init__(self):
        self.feedback_patterns = self._initialize_feedback_patterns()
    
    def _initialize_feedback_patterns(self) -> Dict[str, List[str]]:
        """Initialize feedback detection patterns."""
        return {
            'feature_requests': [
                'would like to see', 'wish it had', 'missing feature',
                'please add', 'request', 'enhancement', 'improvement'
            ],
            'bug_reports': [
                'bug', 'error', 'broken', 'not working', 'issue',
                'problem', 'glitch', 'crash', 'freeze'
            ],
            'usability_issues': [
                'confusing', 'hard to use', 'difficult', 'complicated',
                'user-friendly', 'intuitive', 'easy to use'
            ],
            'performance_feedback': [
                'slow', 'fast', 'performance', 'speed', 'responsive',
                'lag', 'quick', 'efficient'
            ]
        }
    
    def analyze_product_feedback(self, text_segments: List[str]) -> List[ProductInsight]:
        """Analyze product feedback from text segments."""
        insights = []
        
        # Track feedback by category
        feedback_categories = {}
        
        for segment in text_segments:
            segment_lower = segment.lower()
            
            for category, patterns in self.feedback_patterns.items():
                for pattern in patterns:
                    if pattern in segment_lower:
                        if category not in feedback_categories:
                            feedback_categories[category] = {
                                'mentions': [],
                                'sentiment': [],
                                'frequency': 0
                            }
                        
                        feedback_categories[category]['mentions'].append(segment)
                        feedback_categories[category]['sentiment'].append(
                            self._analyze_feedback_sentiment(segment, pattern)
                        )
                        feedback_categories[category]['frequency'] += 1
        
        # Generate insights for each category
        for category, data in feedback_categories.items():
            if data['frequency'] > 0:
                # Calculate overall sentiment
                sentiment_scores = data['sentiment']
                avg_sentiment = statistics.mean(sentiment_scores) if sentiment_scores else 0
                
                if avg_sentiment > 0.2:
                    sentiment = 'positive'
                elif avg_sentiment < -0.2:
                    sentiment = 'negative'
                else:
                    sentiment = 'neutral'
                
                # Determine priority based on frequency and sentiment
                priority = self._determine_feedback_priority(data['frequency'], avg_sentiment)
                
                insight = ProductInsight(
                    insight_id=str(uuid.uuid4()),
                    product_category=category,
                    insight_type=category,
                    description=self._generate_feedback_description(category, data['frequency'], sentiment),
                    frequency=data['frequency'],
                    sentiment=sentiment,
                    priority=priority,
                    customer_segments=['general'],  # Could be enhanced with segment analysis
                    competitive_implications=self._assess_competitive_implications(category, sentiment),
                    recommended_actions=self._generate_feedback_actions(category, priority, sentiment)
                )
                insights.append(insight)
        
        return insights
    
    def _analyze_feedback_sentiment(self, text: str, pattern: str) -> float:
        """Analyze sentiment of feedback mention."""
        text_lower = text.lower()
        
        # Find context around pattern
        pattern_index = text_lower.find(pattern)
        if pattern_index == -1:
            return 0.0
        
        context_start = max(0, pattern_index - 50)
        context_end = min(len(text), pattern_index + 50)
        context = text[context_start:context_end].lower()
        
        # Positive indicators
        positive_words = ['great', 'good', 'excellent', 'love', 'amazing', 'perfect']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'horrible', 'frustrating']
        
        positive_score = sum(1 for word in positive_words if word in context)
        negative_score = sum(1 for word in negative_words if word in context)
        
        # Normalize to -1 to 1 range
        total_score = positive_score - negative_score
        return max(-1.0, min(1.0, total_score / 3.0))
    
    def _determine_feedback_priority(self, frequency: int, sentiment: float) -> str:
        """Determine priority level for feedback."""
        # High priority: frequent mentions with negative sentiment (bugs/issues)
        if frequency >= 3 and sentiment < -0.3:
            return 'high'
        # Medium priority: moderate frequency or neutral sentiment
        elif frequency >= 2 or abs(sentiment) > 0.1:
            return 'medium'
        else:
            return 'low'
    
    def _generate_feedback_description(self, category: str, frequency: int, sentiment: str) -> str:
        """Generate description for feedback insight."""
        category_name = category.replace('_', ' ').title()
        return f"{category_name} mentioned {frequency} times with {sentiment} sentiment"
    
    def _assess_competitive_implications(self, category: str, sentiment: str) -> str:
        """Assess competitive implications of feedback."""
        if category == 'feature_requests' and sentiment == 'negative':
            return "Missing features may drive customers to competitors"
        elif category == 'bug_reports' and sentiment == 'negative':
            return "Quality issues may impact customer retention"
        elif category == 'usability_issues' and sentiment == 'negative':
            return "Usability problems may create competitive disadvantage"
        else:
            return "Monitor for competitive impact"
    
    def _generate_feedback_actions(self, category: str, priority: str, sentiment: str) -> List[str]:
        """Generate recommended actions for feedback."""
        actions = []
        
        if category == 'feature_requests':
            actions.append("Evaluate feature requests for product roadmap")
            if priority == 'high':
                actions.append("Consider rapid prototyping of most requested features")
        
        elif category == 'bug_reports':
            actions.append("Prioritize bug fixes in development queue")
            if priority == 'high':
                actions.append("Implement immediate hotfix if possible")
        
        elif category == 'usability_issues':
            actions.append("Conduct UX research to address usability concerns")
            actions.append("Consider interface redesign for problem areas")
        
        elif category == 'performance_feedback':
            if sentiment == 'negative':
                actions.append("Investigate performance bottlenecks")
                actions.append("Optimize system performance")
        
        return actions

class MarketResearchSystem:
    """Main system for market research and competitive intelligence."""
    
    def __init__(self, db_path: str = "market_intelligence.db"):
        self.competitor_analyzer = CompetitorAnalyzer()
        self.trend_analyzer = TrendAnalyzer()
        self.product_analyzer = ProductFeedbackAnalyzer()
        self.db_path = db_path
        self.init_database()
        
        logger.info("Market Research and Competitive Intelligence System initialized")
    
    def init_database(self):
        """Initialize SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Market intelligence reports table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS intelligence_reports (
                    report_id TEXT PRIMARY KEY,
                    intelligence_type TEXT,
                    analysis_period TEXT,
                    executive_summary TEXT,
                    confidence_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Competitor intelligence table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS competitor_mentions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id TEXT,
                    competitor_name TEXT,
                    mention_type TEXT,
                    sentiment TEXT,
                    confidence REAL,
                    switching_likelihood REAL,
                    FOREIGN KEY (report_id) REFERENCES intelligence_reports (report_id)
                )
            """)
            
            # Market trends table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_trends (
                    trend_id TEXT PRIMARY KEY,
                    report_id TEXT,
                    trend_category TEXT,
                    direction TEXT,
                    strength REAL,
                    business_impact TEXT,
                    confidence REAL,
                    FOREIGN KEY (report_id) REFERENCES intelligence_reports (report_id)
                )
            """)
            
            # Product insights table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS product_insights (
                    insight_id TEXT PRIMARY KEY,
                    report_id TEXT,
                    product_category TEXT,
                    insight_type TEXT,
                    frequency INTEGER,
                    sentiment TEXT,
                    priority TEXT,
                    FOREIGN KEY (report_id) REFERENCES intelligence_reports (report_id)
                )
            """)
            
            conn.commit()
    
    async def generate_market_intelligence(self, 
                                         transcripts: List[str], 
                                         intelligence_type: IntelligenceType,
                                         analysis_period: str = "current") -> MarketIntelligenceReport:
        """Generate comprehensive market intelligence report."""
        try:
            report_id = str(uuid.uuid4())
            logger.info(f"Generating market intelligence report: {report_id}")
            
            # 1. Competitive intelligence analysis
            all_competitive_mentions = []
            for transcript in transcripts:
                mentions = self.competitor_analyzer.analyze_competitive_mentions(transcript, {})
                all_competitive_mentions.extend(mentions)
            
            # 2. Market trend analysis
            market_trends = self.trend_analyzer.identify_trends(transcripts, analysis_period)
            
            # 3. Product feedback analysis
            product_insights = self.product_analyzer.analyze_product_feedback(transcripts)
            
            # 4. Brand perception analysis (simplified)
            brand_perception = self._analyze_brand_perception(transcripts)
            
            # 5. Market opportunity identification
            market_opportunities = self._identify_market_opportunities(
                all_competitive_mentions, market_trends, product_insights
            )
            
            # 6. Generate key findings
            key_findings = self._generate_key_findings(
                all_competitive_mentions, market_trends, product_insights
            )
            
            # 7. Generate strategic recommendations
            recommendations = self._generate_strategic_recommendations(
                intelligence_type, market_trends, product_insights, market_opportunities
            )
            
            # 8. Generate executive summary
            executive_summary = self._generate_executive_summary(
                intelligence_type, key_findings, recommendations
            )
            
            # 9. Calculate confidence score
            confidence_score = self._calculate_report_confidence(
                all_competitive_mentions, market_trends, product_insights
            )
            
            # 10. Create report
            report = MarketIntelligenceReport(
                report_id=report_id,
                intelligence_type=intelligence_type,
                analysis_period=analysis_period,
                data_sources=[f"transcript_{i+1}" for i in range(len(transcripts))],
                competitor_intelligence=all_competitive_mentions,
                market_trends=market_trends,
                product_insights=product_insights,
                brand_perception=brand_perception,
                market_opportunities=market_opportunities,
                key_findings=key_findings,
                strategic_recommendations=recommendations,
                executive_summary=executive_summary,
                confidence_score=confidence_score,
                processing_metadata={
                    'transcripts_analyzed': len(transcripts),
                    'competitive_mentions': len(all_competitive_mentions),
                    'trends_identified': len(market_trends),
                    'product_insights': len(product_insights),
                    'opportunities_identified': len(market_opportunities)
                }
            )
            
            # 11. Store in database
            self._store_report(report)
            
            logger.info("Market intelligence report generated successfully")
            return report
            
        except Exception as e:
            logger.error(f"Error generating market intelligence: {str(e)}")
            # Return minimal report with error
            return MarketIntelligenceReport(
                report_id=str(uuid.uuid4()),
                intelligence_type=intelligence_type,
                analysis_period=analysis_period,
                data_sources=[],
                competitor_intelligence=[],
                market_trends=[],
                product_insights=[],
                brand_perception=None,
                market_opportunities=[],
                key_findings=[],
                strategic_recommendations=[],
                executive_summary="Report generation failed due to error.",
                confidence_score=0.0,
                processing_metadata={'error': str(e)}
            )
    
    def _analyze_brand_perception(self, transcripts: List[str]) -> Optional[BrandPerception]:
        """Analyze brand perception from transcripts."""
        brand_mentions = 0
        positive_mentions = 0
        negative_mentions = 0
        testimonials = []
        
        for transcript in transcripts:
            transcript_lower = transcript.lower()
            
            # Look for brand-related terms
            brand_terms = ['our company', 'your company', 'this service', 'your product', 'brand']
            if any(term in transcript_lower for term in brand_terms):
                brand_mentions += 1
                
                # Analyze sentiment
                positive_words = ['great', 'excellent', 'love', 'amazing', 'perfect', 'satisfied']
                negative_words = ['terrible', 'awful', 'hate', 'frustrated', 'disappointed']
                
                positive_count = sum(1 for word in positive_words if word in transcript_lower)
                negative_count = sum(1 for word in negative_words if word in transcript_lower)
                
                if positive_count > negative_count:
                    positive_mentions += 1
                    if len(transcript) < 200:  # Short positive comments as testimonials
                        testimonials.append(transcript.strip())
                elif negative_count > positive_count:
                    negative_mentions += 1
        
        if brand_mentions == 0:
            return None
        
        # Calculate reputation score
        total_sentiment_mentions = positive_mentions + negative_mentions
        if total_sentiment_mentions > 0:
            reputation_score = positive_mentions / total_sentiment_mentions
        else:
            reputation_score = 0.5
        
        overall_sentiment = 'positive' if reputation_score > 0.6 else 'negative' if reputation_score < 0.4 else 'neutral'
        
        return BrandPerception(
            brand_name="Company",  # Generic - could be enhanced
            overall_sentiment=overall_sentiment,
            reputation_score=reputation_score,
            key_attributes={'customer_service': reputation_score},
            comparison_to_competitors={},
            perception_trends=[],
            customer_testimonials=testimonials[:5],
            areas_for_improvement=self._identify_improvement_areas(transcripts),
            competitive_advantages=self._identify_competitive_advantages(transcripts)
        )
    
    def _identify_improvement_areas(self, transcripts: List[str]) -> List[str]:
        """Identify areas for improvement from transcripts."""
        improvement_areas = []
        
        improvement_indicators = {
            'Customer Service': ['support', 'help', 'service', 'response time'],
            'Product Quality': ['quality', 'reliability', 'bugs', 'issues'],
            'Pricing': ['expensive', 'cost', 'price', 'affordable'],
            'Features': ['missing', 'need', 'want', 'feature'],
            'Usability': ['confusing', 'difficult', 'hard to use', 'complicated']
        }
        
        combined_text = ' '.join(transcripts).lower()
        
        for area, indicators in improvement_indicators.items():
            negative_context = ['problem', 'issue', 'bad', 'poor', 'terrible']
            
            for indicator in indicators:
                if indicator in combined_text:
                    # Check if mentioned in negative context
                    for negative in negative_context:
                        if f"{negative} {indicator}" in combined_text or f"{indicator} {negative}" in combined_text:
                            improvement_areas.append(area)
                            break
        
        return list(set(improvement_areas))
    
    def _identify_competitive_advantages(self, transcripts: List[str]) -> List[str]:
        """Identify competitive advantages from transcripts."""
        advantages = []
        
        advantage_indicators = {
            'Superior Customer Service': ['excellent support', 'great service', 'helpful staff'],
            'Better Pricing': ['affordable', 'good value', 'competitive price'],
            'Advanced Features': ['innovative', 'cutting edge', 'unique feature'],
            'Reliability': ['reliable', 'stable', 'dependable', 'uptime'],
            'Ease of Use': ['easy to use', 'intuitive', 'user-friendly']
        }
        
        combined_text = ' '.join(transcripts).lower()
        
        for advantage, indicators in advantage_indicators.items():
            if any(indicator in combined_text for indicator in indicators):
                advantages.append(advantage)
        
        return advantages
    
    def _identify_market_opportunities(self, 
                                     competitive_mentions: List[CompetitorIntelligence],
                                     market_trends: List[MarketTrend],
                                     product_insights: List[ProductInsight]) -> List[MarketOpportunityInsight]:
        """Identify market opportunities from analysis."""
        opportunities = []
        
        # Opportunity from competitor switching intent
        high_switch_mentions = [m for m in competitive_mentions if m.switching_likelihood and m.switching_likelihood > 0.6]
        if high_switch_mentions:
            opportunity = MarketOpportunityInsight(
                opportunity_id=str(uuid.uuid4()),
                opportunity_type=MarketOpportunity.CUSTOMER_RETENTION,
                description=f"High switching intent detected for {len(high_switch_mentions)} competitor mentions",
                customer_demand_level='high',
                competitive_advantage=0.7,
                success_probability=0.6,
                supporting_data=[f"Switching intent toward {m.competitor_name}" for m in high_switch_mentions[:3]],
                risks=["Competitive response", "Customer acquisition cost"]
            )
            opportunities.append(opportunity)
        
        # Opportunity from market trends
        high_impact_trends = [t for t in market_trends if t.business_impact == 'high' and t.direction == 'increasing']
        for trend in high_impact_trends:
            opportunity = MarketOpportunityInsight(
                opportunity_id=str(uuid.uuid4()),
                opportunity_type=MarketOpportunity.MARKET_EXPANSION,
                description=f"Market expansion opportunity in {trend.trend_category}",
                customer_demand_level='medium',
                competitive_advantage=trend.strength,
                success_probability=trend.confidence,
                supporting_data=trend.supporting_evidence[:2],
                risks=["Market saturation", "Technology obsolescence"]
            )
            opportunities.append(opportunity)
        
        # Opportunity from product feedback
        high_priority_features = [p for p in product_insights if p.priority == 'high' and p.insight_type == 'feature_requests']
        if high_priority_features:
            opportunity = MarketOpportunityInsight(
                opportunity_id=str(uuid.uuid4()),
                opportunity_type=MarketOpportunity.PRODUCT_GAP,
                description=f"Product development opportunity: {len(high_priority_features)} high-priority feature requests",
                customer_demand_level='high',
                competitive_advantage=0.6,
                success_probability=0.7,
                supporting_data=[f"{p.product_category} improvements needed" for p in high_priority_features],
                risks=["Development complexity", "Time to market"]
            )
            opportunities.append(opportunity)
        
        return opportunities
    
    def _generate_key_findings(self, 
                              competitive_mentions: List[CompetitorIntelligence],
                              market_trends: List[MarketTrend],
                              product_insights: List[ProductInsight]) -> List[str]:
        """Generate key findings from analysis."""
        findings = []
        
        # Competitive findings
        if competitive_mentions:
            competitor_counts = {}
            for mention in competitive_mentions:
                competitor_counts[mention.competitor_name] = competitor_counts.get(mention.competitor_name, 0) + 1
            
            top_competitor = max(competitor_counts, key=competitor_counts.get)
            findings.append(f"Most mentioned competitor: {top_competitor} ({competitor_counts[top_competitor]} mentions)")
            
            switching_mentions = [m for m in competitive_mentions if m.mention_type == CompetitorMention.SWITCHING_INTENT]
            if switching_mentions:
                findings.append(f"Customer switching intent detected in {len(switching_mentions)} mentions")
        
        # Trend findings
        strong_trends = [t for t in market_trends if t.strength > 0.6]
        if strong_trends:
            trend_categories = [t.trend_category for t in strong_trends]
            findings.append(f"Strong market trends identified: {', '.join(set(trend_categories))}")
        
        # Product findings
        high_priority_issues = [p for p in product_insights if p.priority == 'high']
        if high_priority_issues:
            findings.append(f"High-priority product issues identified: {len(high_priority_issues)} areas need attention")
        
        negative_feedback = [p for p in product_insights if p.sentiment == 'negative']
        if negative_feedback:
            findings.append(f"Negative product feedback in {len(negative_feedback)} categories requires immediate attention")
        
        if not findings:
            findings.append("Analysis completed with standard market conditions observed")
        
        return findings
    
    def _generate_strategic_recommendations(self, 
                                          intelligence_type: IntelligenceType,
                                          market_trends: List[MarketTrend],
                                          product_insights: List[ProductInsight],
                                          opportunities: List[MarketOpportunityInsight]) -> List[str]:
        """Generate strategic recommendations."""
        recommendations = []
        
        # Trend-based recommendations
        high_impact_trends = [t for t in market_trends if t.business_impact == 'high']
        for trend in high_impact_trends:
            if trend.direction == 'increasing':
                recommendations.append(f"Invest in {trend.trend_category.replace('_', ' ')} capabilities to capitalize on growing trend")
        
        # Product-based recommendations
        high_priority_products = [p for p in product_insights if p.priority == 'high']
        for insight in high_priority_products:
            if insight.sentiment == 'negative':
                recommendations.append(f"Address {insight.product_category} issues to improve customer satisfaction")
        
        # Opportunity-based recommendations
        high_value_opportunities = [o for o in opportunities if o.success_probability > 0.6]
        for opp in high_value_opportunities:
            recommendations.append(f"Pursue {opp.opportunity_type.value.replace('_', ' ')} opportunity: {opp.description}")
        
        # Intelligence-type specific recommendations
        if intelligence_type == IntelligenceType.COMPETITIVE:
            recommendations.append("Monitor competitor activities and prepare competitive response strategies")
        elif intelligence_type == IntelligenceType.CUSTOMER_SENTIMENT:
            recommendations.append("Implement customer feedback loop to continuously monitor satisfaction")
        
        if not recommendations:
            recommendations.append("Continue monitoring market conditions and customer feedback")
        
        return recommendations
    
    def _generate_executive_summary(self, 
                                   intelligence_type: IntelligenceType,
                                   key_findings: List[str],
                                   recommendations: List[str]) -> str:
        """Generate executive summary."""
        summary_parts = [
            f"Market Intelligence Report - {intelligence_type.value.replace('_', ' ').title()}",
            "",
            "Key Findings:",
            *[f"• {finding}" for finding in key_findings[:3]],
            "",
            "Strategic Recommendations:",
            *[f"• {rec}" for rec in recommendations[:3]],
            "",
            f"This analysis provides actionable insights for strategic decision-making based on {intelligence_type.value.replace('_', ' ')} intelligence."
        ]
        
        return "\n".join(summary_parts)
    
    def _calculate_report_confidence(self, 
                                    competitive_mentions: List[CompetitorIntelligence],
                                    market_trends: List[MarketTrend],
                                    product_insights: List[ProductInsight]) -> float:
        """Calculate overall confidence score for the report."""
        confidence_scores = []
        
        # Competitive intelligence confidence
        if competitive_mentions:
            comp_confidence = statistics.mean([m.confidence for m in competitive_mentions])
            confidence_scores.append(comp_confidence)
        
        # Market trends confidence
        if market_trends:
            trend_confidence = statistics.mean([t.confidence for t in market_trends])
            confidence_scores.append(trend_confidence)
        
        # Product insights confidence (estimated)
        if product_insights:
            # Estimate confidence based on frequency and priority
            product_confidence = 0.7  # Base confidence
            high_priority_count = len([p for p in product_insights if p.priority == 'high'])
            if high_priority_count > 0:
                product_confidence += 0.1
            confidence_scores.append(product_confidence)
        
        # Calculate overall confidence
        if confidence_scores:
            overall_confidence = statistics.mean(confidence_scores)
        else:
            overall_confidence = 0.5  # Default medium confidence
        
        return min(overall_confidence, 1.0)
    
    def _store_report(self, report: MarketIntelligenceReport):
        """Store report in database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Store main report
            cursor.execute("""
                INSERT INTO intelligence_reports 
                (report_id, intelligence_type, analysis_period, executive_summary, confidence_score)
                VALUES (?, ?, ?, ?, ?)
            """, (
                report.report_id,
                report.intelligence_type.value,
                report.analysis_period,
                report.executive_summary,
                report.confidence_score
            ))
            
            # Store competitor mentions
            for mention in report.competitor_intelligence:
                cursor.execute("""
                    INSERT INTO competitor_mentions 
                    (report_id, competitor_name, mention_type, sentiment, confidence, switching_likelihood)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    report.report_id,
                    mention.competitor_name,
                    mention.mention_type.value,
                    mention.sentiment,
                    mention.confidence,
                    mention.switching_likelihood
                ))
            
            # Store market trends
            for trend in report.market_trends:
                cursor.execute("""
                    INSERT INTO market_trends 
                    (trend_id, report_id, trend_category, direction, strength, business_impact, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    trend.trend_id,
                    report.report_id,
                    trend.trend_category,
                    trend.direction,
                    trend.strength,
                    trend.business_impact,
                    trend.confidence
                ))
            
            # Store product insights
            for insight in report.product_insights:
                cursor.execute("""
                    INSERT INTO product_insights 
                    (insight_id, report_id, product_category, insight_type, frequency, sentiment, priority)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    insight.insight_id,
                    report.report_id,
                    insight.product_category,
                    insight.insight_type,
                    insight.frequency,
                    insight.sentiment,
                    insight.priority
                ))
            
            conn.commit()
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get system statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total reports
                cursor.execute("SELECT COUNT(*) FROM intelligence_reports")
                total_reports = cursor.fetchone()[0]
                
                # Intelligence type distribution
                cursor.execute("""
                    SELECT intelligence_type, COUNT(*) 
                    FROM intelligence_reports 
                    GROUP BY intelligence_type
                """)
                intelligence_types = cursor.fetchall()
                
                # Competitor mention statistics
                cursor.execute("SELECT COUNT(*) FROM competitor_mentions")
                total_mentions = cursor.fetchone()[0]
                
                return {
                    'total_reports': total_reports,
                    'intelligence_type_distribution': intelligence_types,
                    'total_competitor_mentions': total_mentions,
                    'system_status': 'operational'
                }
        except Exception as e:
            return {
                'error': str(e),
                'system_status': 'error'
            }

# Demo function
async def demo_market_intelligence():
    """Demonstrate market research and competitive intelligence capabilities."""
    system = MarketResearchSystem()
    
    print("📊 Market Research & Competitive Intelligence Demo")
    print("=" * 55)
    
    # Sample transcripts for analysis
    test_transcripts = [
        """
        We've been looking at Microsoft Teams as an alternative to our current solution. 
        The integration features look really good, and their pricing seems more competitive. 
        Several team members have mentioned that Zoom's interface is getting outdated compared to newer platforms.
        """,
        
        """
        The remote work trend is definitely here to stay. More clients are asking about 
        cloud-based solutions and digital transformation initiatives. We're seeing increased 
        demand for AI-powered features and automation tools. Security and privacy are becoming 
        top priorities for enterprise customers.
        """,
        
        """
        Customers keep requesting better mobile app functionality and improved dashboard analytics. 
        There have been several bug reports about the reporting feature not working properly. 
        The performance has been slower than expected, especially during peak usage times.
        Users love the new collaboration features but find the interface confusing.
        """,
        
        """
        Our main competitor Google Workspace is gaining market share with their recent updates. 
        Some customers are considering switching because of their better integration with 
        third-party tools. We need to improve our API capabilities and add more automation features 
        to stay competitive. The pricing pressure is intense in this market.
        """
    ]
    
    # Test different intelligence types
    intelligence_types = [
        IntelligenceType.COMPETITIVE,
        IntelligenceType.MARKET_TRENDS,
        IntelligenceType.PRODUCT_FEEDBACK
    ]
    
    for intel_type in intelligence_types:
        print(f"\n📋 {intel_type.value.replace('_', ' ').title()} Intelligence Analysis:")
        print("-" * 50)
        
        # Generate report
        report = await system.generate_market_intelligence(
            test_transcripts, 
            intel_type,
            "Q1 2024"
        )
        
        # Display results
        print(f"Report ID: {report.report_id}")
        print(f"Analysis Period: {report.analysis_period}")
        print(f"Confidence Score: {report.confidence_score:.2f}")
        
        # Key findings
        print(f"\n🔍 Key Findings:")
        for finding in report.key_findings:
            print(f"  • {finding}")
        
        # Competitive intelligence
        if report.competitor_intelligence:
            print(f"\n🏢 Competitor Intelligence ({len(report.competitor_intelligence)} mentions):")
            competitor_counts = {}
            for mention in report.competitor_intelligence:
                competitor_counts[mention.competitor_name] = competitor_counts.get(mention.competitor_name, 0) + 1
            
            for competitor, count in list(competitor_counts.items())[:3]:
                mentions = [m for m in report.competitor_intelligence if m.competitor_name == competitor]
                sentiment_dist = {}
                for m in mentions:
                    sentiment_dist[m.sentiment] = sentiment_dist.get(m.sentiment, 0) + 1
                print(f"  • {competitor}: {count} mentions, sentiment: {dict(sentiment_dist)}")
        
        # Market trends
        if report.market_trends:
            print(f"\n📈 Market Trends ({len(report.market_trends)} identified):")
            for trend in report.market_trends:
                print(f"  • {trend.trend_category}: {trend.direction} (strength: {trend.strength:.2f}, impact: {trend.business_impact})")
        
        # Product insights
        if report.product_insights:
            print(f"\n💡 Product Insights ({len(report.product_insights)} areas):")
            for insight in report.product_insights:
                print(f"  • {insight.product_category}: {insight.sentiment} feedback, {insight.priority} priority (freq: {insight.frequency})")
        
        # Market opportunities
        if report.market_opportunities:
            print(f"\n🎯 Market Opportunities ({len(report.market_opportunities)} identified):")
            for opp in report.market_opportunities:
                print(f"  • {opp.opportunity_type.value}: {opp.description[:80]}...")
        
        # Strategic recommendations
        print(f"\n📋 Strategic Recommendations:")
        for rec in report.strategic_recommendations[:3]:
            print(f"  • {rec}")
        
        print(f"\n📄 Executive Summary Preview:")
        print(report.executive_summary.split('\n')[0])
    
    # System statistics
    print(f"\n📊 System Statistics:")
    stats = system.get_system_statistics()
    print(f"Total Reports Generated: {stats.get('total_reports', 0)}")
    print(f"Total Competitor Mentions: {stats.get('total_competitor_mentions', 0)}")
    print(f"System Status: {stats.get('system_status', 'unknown')}")
    
    print(f"\n✅ Market intelligence demo completed!")

if __name__ == "__main__":
    asyncio.run(demo_market_intelligence())