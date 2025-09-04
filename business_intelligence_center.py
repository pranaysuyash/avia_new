#!/usr/bin/env python3
"""
Business Intelligence Center - Intent-First Transformation
Transforms admin dashboard into actionable business intelligence platform
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics
import json
import sqlite3

# Import existing admin dashboard system
try:
    from admin_dashboard import (
        AdminDashboardSystem, AdminUser, RevenueRecord, UserActivity, 
        SystemMetric, SupportTicket, UserStatus, SubscriptionTier
    )
    ADMIN_SYSTEM_AVAILABLE = True
except ImportError:
    ADMIN_SYSTEM_AVAILABLE = False
    logging.warning("Admin dashboard system not available")

logger = logging.getLogger(__name__)

class InsightType(Enum):
    """Types of business insights"""
    USER_SUCCESS = "user_success"
    REVENUE_OPPORTUNITY = "revenue_opportunity"
    OPERATIONAL_EFFICIENCY = "operational_efficiency"
    CHURN_RISK = "churn_risk"
    GROWTH_OPPORTUNITY = "growth_opportunity"

class RiskLevel(Enum):
    """Risk levels for business alerts"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ActionPriority(Enum):
    """Priority levels for recommended actions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class BusinessInsight:
    """Actionable business insight"""
    insight_id: str
    insight_type: InsightType
    title: str
    description: str
    impact_score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    supporting_data: Dict[str, Any]
    recommended_actions: List[str]
    potential_impact: str
    timeline: str
    generated_at: datetime = field(default_factory=datetime.now)

@dataclass
class RevenueOpportunity:
    """Revenue optimization opportunity"""
    opportunity_id: str
    title: str
    description: str
    potential_revenue: float
    confidence: float
    target_segment: str
    recommended_action: str
    implementation_effort: str  # low, medium, high
    timeline: str
    success_probability: float

@dataclass
class ChurnRiskAlert:
    """User churn risk alert"""
    user_id: str
    risk_score: float  # 0.0 to 1.0
    risk_level: RiskLevel
    risk_factors: List[str]
    recommended_interventions: List[str]
    potential_revenue_at_risk: float
    intervention_success_probability: float
    days_until_likely_churn: int

@dataclass
class UserSuccessIntervention:
    """User success intervention recommendation"""
    user_segment: str
    intervention_type: str
    description: str
    expected_impact: str
    implementation_cost: float
    success_probability: float
    target_metric: str

@dataclass
class OperationalAlert:
    """Operational efficiency alert"""
    alert_type: str
    message: str
    impact: str
    recommended_action: str
    priority: ActionPriority
    estimated_savings: Optional[float] = None

@dataclass
class BusinessIntelligence:
    """Comprehensive business intelligence overview"""
    user_success_score: float
    key_insights: List[str]
    revenue_opportunities: List[RevenueOpportunity]
    operational_alerts: List[OperationalAlert]
    user_success_interventions: List[UserSuccessIntervention]
    churn_risk_alerts: List[ChurnRiskAlert]
    growth_metrics: Dict[str, Any]
    generated_at: datetime = field(default_factory=datetime.now)

class BusinessIntelligenceCenter:
    """
    Intent-First transformation of admin dashboard
    Focuses on actionable business insights and user success optimization
    """
    
    def __init__(self, db_path: str = "business_intelligence.db"):
        self.db_path = db_path
        self.admin_system = AdminDashboardSystem() if ADMIN_SYSTEM_AVAILABLE else None
        
        # Initialize BI database
        self._initialize_bi_database()
        
        # User success patterns
        self.success_patterns = {}
        self.churn_indicators = {}
        
        # Revenue optimization models
        self.revenue_models = {}
        
        # Initialize baseline patterns
        self._initialize_success_patterns()
        self._initialize_churn_indicators()
    
    def _initialize_bi_database(self):
        """Initialize business intelligence database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Business insights table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS business_insights (
                        insight_id TEXT PRIMARY KEY,
                        insight_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        impact_score REAL NOT NULL,
                        confidence REAL NOT NULL,
                        supporting_data TEXT,
                        recommended_actions TEXT,
                        potential_impact TEXT,
                        timeline TEXT,
                        generated_at TEXT NOT NULL,
                        status TEXT DEFAULT 'active'
                    )
                """)
                
                # User success tracking
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_success_metrics (
                        user_id TEXT,
                        metric_name TEXT,
                        metric_value REAL,
                        timestamp TEXT,
                        PRIMARY KEY (user_id, metric_name, timestamp)
                    )
                """)
                
                # Revenue opportunities tracking
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS revenue_opportunities (
                        opportunity_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        potential_revenue REAL NOT NULL,
                        confidence REAL NOT NULL,
                        target_segment TEXT,
                        status TEXT DEFAULT 'identified',
                        created_at TEXT NOT NULL
                    )
                """)
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error initializing BI database: {e}")
    
    async def get_business_intelligence_overview(self) -> BusinessIntelligence:
        """Get comprehensive business intelligence overview"""
        
        # Analyze user success patterns
        user_success_score = await self._calculate_user_success_score()
        
        # Generate key insights
        key_insights = await self._generate_key_insights()
        
        # Identify revenue opportunities
        revenue_opportunities = await self._identify_revenue_opportunities()
        
        # Generate operational alerts
        operational_alerts = await self._generate_operational_alerts()
        
        # Identify user success interventions
        success_interventions = await self._identify_success_interventions()
        
        # Analyze churn risks
        churn_risks = await self._analyze_churn_risks()
        
        # Calculate growth metrics
        growth_metrics = await self._calculate_growth_metrics()
        
        return BusinessIntelligence(
            user_success_score=user_success_score,
            key_insights=key_insights,
            revenue_opportunities=revenue_opportunities,
            operational_alerts=operational_alerts,
            user_success_interventions=success_interventions,
            churn_risk_alerts=churn_risks,
            growth_metrics=growth_metrics
        )
    
    async def _calculate_user_success_score(self) -> float:
        """Calculate overall user success score"""
        
        if not self.admin_system:
            return 0.85  # Default good score
        
        try:
            # Get user overview data
            user_overview = self.admin_system.user_management.get_user_overview()
            
            # Calculate success factors
            activity_rate = user_overview.get('activity_rate', 70) / 100
            retention_rate = self._calculate_retention_rate()
            engagement_score = self._calculate_engagement_score()
            satisfaction_score = self._calculate_satisfaction_score()
            
            # Weighted success score
            success_score = (
                activity_rate * 0.3 +
                retention_rate * 0.3 +
                engagement_score * 0.2 +
                satisfaction_score * 0.2
            )
            
            return min(1.0, max(0.0, success_score))
            
        except Exception as e:
            logger.error(f"Error calculating user success score: {e}")
            return 0.75  # Conservative fallback
    
    async def _generate_key_insights(self) -> List[str]:
        """Generate key actionable business insights"""
        
        insights = []
        
        # User onboarding insights
        onboarding_completion_rate = await self._analyze_onboarding_completion()
        if onboarding_completion_rate < 0.7:
            insights.append(
                f"Onboarding completion rate is {onboarding_completion_rate:.1%} - "
                f"users who complete onboarding have 3x higher retention. "
                f"Prioritize onboarding optimization."
            )
        else:
            insights.append(
                f"Strong onboarding performance ({onboarding_completion_rate:.1%} completion) - "
                f"maintain current onboarding experience quality."
            )
        
        # Usage pattern insights
        peak_usage_analysis = await self._analyze_peak_usage_patterns()
        if peak_usage_analysis['peak_hour_load'] > 0.8:
            insights.append(
                f"Peak usage at {peak_usage_analysis['peak_hour']} creates {peak_usage_analysis['delay_impact']} delays - "
                f"consider auto-scaling or load balancing improvements."
            )
        
        # Feature adoption insights
        feature_adoption = await self._analyze_feature_adoption()
        underused_features = [f for f, rate in feature_adoption.items() if rate < 0.3]
        if underused_features:
            insights.append(
                f"Features {', '.join(underused_features[:2])} have low adoption (<30%) - "
                f"consider user education or UX improvements."
            )
        
        # Quality correlation insights
        quality_impact = await self._analyze_quality_impact_on_retention()
        if quality_impact['correlation'] > 0.7:
            insights.append(
                f"Transcription quality strongly correlates with retention (r={quality_impact['correlation']:.2f}) - "
                f"quality improvements could increase retention by {quality_impact['potential_improvement']:.1%}."
            )
        
        # Support ticket insights
        support_patterns = await self._analyze_support_patterns()
        if support_patterns['common_issues']:
            top_issue = support_patterns['common_issues'][0]
            insights.append(
                f"Most common support issue: '{top_issue['category']}' ({top_issue['percentage']:.1%} of tickets) - "
                f"addressing this could reduce support load by {top_issue['reduction_potential']:.1%}."
            )
        
        return insights[:5]  # Top 5 insights
    
    async def _identify_revenue_opportunities(self) -> List[RevenueOpportunity]:
        """Identify revenue optimization opportunities"""
        
        opportunities = []
        
        # Upgrade opportunity analysis
        upgrade_candidates = await self._identify_upgrade_candidates()
        if upgrade_candidates:
            opportunities.append(RevenueOpportunity(
                opportunity_id="upgrade_power_users",
                title="Upgrade Power Users to Pro",
                description=f"Target {len(upgrade_candidates)} users with >50 transcriptions/month for Pro upgrade",
                potential_revenue=len(upgrade_candidates) * 29.99,  # Assuming $29.99/month Pro plan
                confidence=0.85,
                target_segment="power_users",
                recommended_action="Send personalized upgrade offers highlighting advanced features",
                implementation_effort="low",
                timeline="2 weeks",
                success_probability=0.25
            ))
        
        # Enterprise opportunity analysis
        enterprise_candidates = await self._identify_enterprise_candidates()
        if enterprise_candidates:
            opportunities.append(RevenueOpportunity(
                opportunity_id="enterprise_expansion",
                title="Enterprise Plan Expansion",
                description=f"Target {len(enterprise_candidates)} high-usage teams for Enterprise plans",
                potential_revenue=len(enterprise_candidates) * 299.99,  # Assuming $299.99/month Enterprise
                confidence=0.75,
                target_segment="high_usage_teams",
                recommended_action="Reach out with enterprise feature demos and custom pricing",
                implementation_effort="medium",
                timeline="1 month",
                success_probability=0.15
            ))
        
        # Feature monetization opportunities
        feature_monetization = await self._analyze_feature_monetization()
        if feature_monetization['premium_feature_interest'] > 0.6:
            opportunities.append(RevenueOpportunity(
                opportunity_id="premium_features",
                title="Premium Feature Monetization",
                description="High interest in advanced features suggests premium tier opportunity",
                potential_revenue=feature_monetization['estimated_revenue'],
                confidence=0.70,
                target_segment="engaged_users",
                recommended_action="Create premium feature tier with advanced AI capabilities",
                implementation_effort="high",
                timeline="3 months",
                success_probability=0.35
            ))
        
        return opportunities
    
    async def _generate_operational_alerts(self) -> List[OperationalAlert]:
        """Generate operational efficiency alerts"""
        
        alerts = []
        
        # Processing efficiency alert
        processing_efficiency = await self._analyze_processing_efficiency()
        if processing_efficiency['efficiency_score'] < 0.8:
            alerts.append(OperationalAlert(
                alert_type="processing_efficiency",
                message=f"Processing efficiency at {processing_efficiency['efficiency_score']:.1%} - optimization opportunity identified",
                impact=f"Could reduce processing costs by {processing_efficiency['cost_reduction_potential']:.1%}",
                recommended_action="Implement intelligent load balancing and resource optimization",
                priority=ActionPriority.HIGH,
                estimated_savings=processing_efficiency['estimated_monthly_savings']
            ))
        
        # Support efficiency alert
        support_efficiency = await self._analyze_support_efficiency()
        if support_efficiency['resolution_time'] > 24:  # hours
            alerts.append(OperationalAlert(
                alert_type="support_efficiency",
                message=f"Average support resolution time is {support_efficiency['resolution_time']:.1f} hours",
                impact="User satisfaction and retention impact",
                recommended_action="Implement automated support triage and knowledge base improvements",
                priority=ActionPriority.MEDIUM
            ))
        
        # Resource utilization alert
        resource_utilization = await self._analyze_resource_utilization()
        if resource_utilization['peak_utilization'] > 0.9:
            alerts.append(OperationalAlert(
                alert_type="resource_utilization",
                message="Peak resource utilization exceeds 90% - scaling opportunity",
                impact="User experience degradation during peak hours",
                recommended_action="Implement auto-scaling for peak hour demand",
                priority=ActionPriority.HIGH
            ))
        
        return alerts
    
    async def _identify_success_interventions(self) -> List[UserSuccessIntervention]:
        """Identify user success intervention opportunities"""
        
        interventions = []
        
        # Trial user conversion intervention
        trial_analysis = await self._analyze_trial_conversion()
        if trial_analysis['conversion_rate'] < 0.3:
            interventions.append(UserSuccessIntervention(
                user_segment="trial_users_day_5",
                intervention_type="personalized_coaching",
                description="Provide personalized success coaching for trial users on day 5",
                expected_impact=f"Increase trial-to-paid conversion by {trial_analysis['improvement_potential']:.1%}",
                implementation_cost=50.0,  # per user
                success_probability=0.65,
                target_metric="trial_conversion_rate"
            ))
        
        # New user activation intervention
        activation_analysis = await self._analyze_user_activation()
        if activation_analysis['activation_rate'] < 0.6:
            interventions.append(UserSuccessIntervention(
                user_segment="new_users_week_1",
                intervention_type="guided_onboarding",
                description="Enhanced guided onboarding for first-week users",
                expected_impact=f"Increase activation rate by {activation_analysis['improvement_potential']:.1%}",
                implementation_cost=25.0,
                success_probability=0.75,
                target_metric="user_activation_rate"
            ))
        
        # Power user retention intervention
        power_user_analysis = await self._analyze_power_user_retention()
        if power_user_analysis['retention_risk'] > 0.2:
            interventions.append(UserSuccessIntervention(
                user_segment="power_users",
                intervention_type="advanced_features_training",
                description="Provide advanced features training for power users",
                expected_impact="Reduce power user churn by 40%",
                implementation_cost=100.0,
                success_probability=0.80,
                target_metric="power_user_retention"
            ))
        
        return interventions
    
    async def _analyze_churn_risks(self) -> List[ChurnRiskAlert]:
        """Analyze user churn risks with intervention recommendations"""
        
        churn_alerts = []
        
        # Identify at-risk users using behavioral patterns
        at_risk_users = await self._identify_churn_risk_users()
        
        for user_data in at_risk_users:
            risk_factors = self._analyze_user_risk_factors(user_data)
            interventions = self._recommend_churn_interventions(risk_factors)
            
            churn_alerts.append(ChurnRiskAlert(
                user_id=user_data['user_id'],
                risk_score=user_data['churn_probability'],
                risk_level=self._determine_risk_level(user_data['churn_probability']),
                risk_factors=risk_factors,
                recommended_interventions=interventions,
                potential_revenue_at_risk=user_data['lifetime_value'],
                intervention_success_probability=0.6,
                days_until_likely_churn=user_data['days_until_churn']
            ))
        
        return churn_alerts[:10]  # Top 10 at-risk users
    
    async def _calculate_growth_metrics(self) -> Dict[str, Any]:
        """Calculate growth and performance metrics"""
        
        # User growth metrics
        user_growth = await self._analyze_user_growth()
        
        # Revenue growth metrics
        revenue_growth = await self._analyze_revenue_growth()
        
        # Engagement metrics
        engagement_metrics = await self._analyze_engagement_metrics()
        
        # Conversion funnel metrics
        funnel_metrics = await self._analyze_conversion_funnel()
        
        return {
            'user_growth': user_growth,
            'revenue_growth': revenue_growth,
            'engagement': engagement_metrics,
            'conversion_funnel': funnel_metrics,
            'calculated_at': datetime.now().isoformat()
        }
    
    def _initialize_success_patterns(self):
        """Initialize user success patterns"""
        self.success_patterns = {
            'onboarding_completion': {
                'threshold': 0.7,
                'retention_multiplier': 3.0,
                'indicators': ['profile_completed', 'first_transcription', 'feature_exploration']
            },
            'engagement_patterns': {
                'daily_active_threshold': 0.3,
                'weekly_active_threshold': 0.6,
                'feature_adoption_threshold': 0.4
            },
            'quality_correlation': {
                'accuracy_retention_correlation': 0.75,
                'speed_satisfaction_correlation': 0.65
            }
        }
    
    def _initialize_churn_indicators(self):
        """Initialize churn risk indicators"""
        self.churn_indicators = {
            'behavioral_signals': [
                'decreased_usage_frequency',
                'support_ticket_increase',
                'feature_abandonment',
                'quality_complaints'
            ],
            'risk_thresholds': {
                'usage_decline': 0.5,  # 50% usage decline
                'support_frequency': 3,  # 3+ tickets in 30 days
                'satisfaction_drop': 0.3  # 30% satisfaction decline
            }
        }
    
    # Placeholder implementations for demo methods
    def _calculate_retention_rate(self) -> float:
        """Calculate user retention rate"""
        return 0.75  # 75% retention rate
    
    def _calculate_engagement_score(self) -> float:
        """Calculate user engagement score"""
        return 0.82  # 82% engagement score
    
    def _calculate_satisfaction_score(self) -> float:
        """Calculate user satisfaction score"""
        return 0.88  # 88% satisfaction score
    
    async def _analyze_onboarding_completion(self) -> float:
        """Analyze onboarding completion rate"""
        return 0.68  # 68% completion rate
    
    async def _analyze_peak_usage_patterns(self) -> Dict[str, Any]:
        """Analyze peak usage patterns"""
        return {
            'peak_hour': '2 PM',
            'peak_hour_load': 0.85,
            'delay_impact': '40% longer processing times'
        }
    
    async def _analyze_feature_adoption(self) -> Dict[str, float]:
        """Analyze feature adoption rates"""
        return {
            'advanced_analysis': 0.25,
            'export_features': 0.45,
            'collaboration_tools': 0.28,
            'api_access': 0.15
        }
    
    async def _analyze_quality_impact_on_retention(self) -> Dict[str, Any]:
        """Analyze quality impact on retention"""
        return {
            'correlation': 0.78,
            'potential_improvement': 0.15  # 15% potential improvement
        }
    
    async def _analyze_support_patterns(self) -> Dict[str, Any]:
        """Analyze support ticket patterns"""
        return {
            'common_issues': [
                {
                    'category': 'transcription_quality',
                    'percentage': 0.35,
                    'reduction_potential': 0.25
                },
                {
                    'category': 'processing_speed',
                    'percentage': 0.28,
                    'reduction_potential': 0.20
                }
            ]
        }
    
    async def _identify_upgrade_candidates(self) -> List[Dict[str, Any]]:
        """Identify users who are candidates for upgrade"""
        return [
            {'user_id': 'user_001', 'usage_score': 0.85},
            {'user_id': 'user_002', 'usage_score': 0.92},
            {'user_id': 'user_003', 'usage_score': 0.78}
        ]
    
    async def _identify_enterprise_candidates(self) -> List[Dict[str, Any]]:
        """Identify teams who are candidates for enterprise"""
        return [
            {'team_id': 'team_001', 'usage_score': 0.95},
            {'team_id': 'team_002', 'usage_score': 0.88}
        ]
    
    async def _analyze_feature_monetization(self) -> Dict[str, Any]:
        """Analyze feature monetization opportunities"""
        return {
            'premium_feature_interest': 0.65,
            'estimated_revenue': 15000
        }
    
    async def _analyze_processing_efficiency(self) -> Dict[str, Any]:
        """Analyze processing efficiency"""
        return {
            'efficiency_score': 0.75,
            'cost_reduction_potential': 0.20,
            'estimated_monthly_savings': 5000
        }
    
    async def _analyze_support_efficiency(self) -> Dict[str, Any]:
        """Analyze support efficiency"""
        return {
            'resolution_time': 28.5  # hours
        }
    
    async def _analyze_resource_utilization(self) -> Dict[str, Any]:
        """Analyze resource utilization"""
        return {
            'peak_utilization': 0.92
        }
    
    async def _analyze_trial_conversion(self) -> Dict[str, Any]:
        """Analyze trial conversion rates"""
        return {
            'conversion_rate': 0.25,
            'improvement_potential': 0.10
        }
    
    async def _analyze_user_activation(self) -> Dict[str, Any]:
        """Analyze user activation rates"""
        return {
            'activation_rate': 0.55,
            'improvement_potential': 0.15
        }
    
    async def _analyze_power_user_retention(self) -> Dict[str, Any]:
        """Analyze power user retention"""
        return {
            'retention_risk': 0.25
        }
    
    async def _identify_churn_risk_users(self) -> List[Dict[str, Any]]:
        """Identify users at risk of churning"""
        return [
            {
                'user_id': 'user_at_risk_001',
                'churn_probability': 0.75,
                'lifetime_value': 299.99,
                'days_until_churn': 14
            },
            {
                'user_id': 'user_at_risk_002', 
                'churn_probability': 0.68,
                'lifetime_value': 149.99,
                'days_until_churn': 21
            }
        ]
    
    def _analyze_user_risk_factors(self, user_data: Dict[str, Any]) -> List[str]:
        """Analyze risk factors for a specific user"""
        return [
            'Decreased usage frequency (50% decline)',
            'Multiple support tickets (3 in last 30 days)',
            'Low feature adoption (only using basic features)'
        ]
    
    def _recommend_churn_interventions(self, risk_factors: List[str]) -> List[str]:
        """Recommend interventions for churn prevention"""
        return [
            'Send personalized tutorial for advanced features',
            'Offer 1-on-1 success session',
            'Provide use case specific templates'
        ]
    
    def _determine_risk_level(self, churn_probability: float) -> RiskLevel:
        """Determine risk level from churn probability"""
        if churn_probability >= 0.8:
            return RiskLevel.CRITICAL
        elif churn_probability >= 0.6:
            return RiskLevel.HIGH
        elif churn_probability >= 0.4:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    async def _analyze_user_growth(self) -> Dict[str, Any]:
        """Analyze user growth metrics"""
        return {
            'monthly_growth_rate': 0.15,
            'new_user_acquisition': 250,
            'growth_trend': 'increasing'
        }
    
    async def _analyze_revenue_growth(self) -> Dict[str, Any]:
        """Analyze revenue growth metrics"""
        return {
            'monthly_revenue_growth': 0.22,
            'revenue_per_user_trend': 'increasing',
            'subscription_upgrade_rate': 0.18
        }
    
    async def _analyze_engagement_metrics(self) -> Dict[str, Any]:
        """Analyze user engagement metrics"""
        return {
            'daily_active_users': 0.35,
            'weekly_active_users': 0.68,
            'session_duration_avg': 25.5  # minutes
        }
    
    async def _analyze_conversion_funnel(self) -> Dict[str, Any]:
        """Analyze conversion funnel metrics"""
        return {
            'signup_to_activation': 0.72,
            'activation_to_trial': 0.45,
            'trial_to_paid': 0.28,
            'overall_conversion': 0.09
        }