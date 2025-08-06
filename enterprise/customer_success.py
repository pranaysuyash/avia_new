"""
Customer Success Tracking and Health Score System

Monitors customer health, usage patterns, and success metrics
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, date
from enum import Enum
from pydantic import BaseModel, Field, validator
import statistics
from collections import defaultdict

class HealthStatus(str, Enum):
    """Customer health status levels"""
    EXCELLENT = "excellent"  # 80-100
    GOOD = "good"           # 60-79
    FAIR = "fair"           # 40-59
    AT_RISK = "at_risk"     # 20-39
    CRITICAL = "critical"   # 0-19

class RiskFactor(str, Enum):
    """Types of risk factors"""
    LOW_USAGE = "low_usage"
    DECLINING_USAGE = "declining_usage"
    NO_RECENT_LOGIN = "no_recent_login"
    LOW_FEATURE_ADOPTION = "low_feature_adoption"
    SUPPORT_ISSUES = "support_issues"
    PAYMENT_ISSUES = "payment_issues"
    LOW_USER_ADOPTION = "low_user_adoption"
    API_ERRORS = "api_errors"

class EngagementMetric(str, Enum):
    """Types of engagement metrics"""
    DAILY_ACTIVE_USERS = "daily_active_users"
    WEEKLY_ACTIVE_USERS = "weekly_active_users"
    MONTHLY_ACTIVE_USERS = "monthly_active_users"
    FEATURE_ADOPTION = "feature_adoption"
    API_USAGE = "api_usage"
    PROCESSING_VOLUME = "processing_volume"
    STORAGE_USAGE = "storage_usage"

class UsageMetrics(BaseModel):
    """Customer usage metrics"""
    period_start: datetime
    period_end: datetime
    
    # User metrics
    total_users: int = 0
    active_users: int = 0
    new_users: int = 0
    
    # Processing metrics
    processing_hours: float = 0.0
    transcription_count: int = 0
    average_file_duration: float = 0.0
    
    # Storage metrics
    storage_gb_used: float = 0.0
    total_files: int = 0
    
    # API metrics
    api_calls: int = 0
    api_errors: int = 0
    api_error_rate: float = 0.0
    
    # Feature usage
    features_used: Dict[str, int] = Field(default_factory=dict)
    
    @validator('api_error_rate', always=True)
    def calculate_error_rate(cls, v, values):
        if values.get('api_calls', 0) > 0:
            return values.get('api_errors', 0) / values['api_calls']
        return 0.0

class SupportMetrics(BaseModel):
    """Customer support interaction metrics"""
    total_tickets: int = 0
    open_tickets: int = 0
    resolved_tickets: int = 0
    average_resolution_hours: float = 0.0
    satisfaction_score: Optional[float] = None  # 1-5 scale
    
    # Ticket categories
    ticket_categories: Dict[str, int] = Field(default_factory=dict)
    
    # Escalations
    escalated_tickets: int = 0
    critical_issues: int = 0

class CustomerMetadata(BaseModel):
    """Customer account metadata"""
    organization_id: str
    organization_name: str
    industry: Optional[str]
    company_size: Optional[str]
    
    # Contract details
    contract_value: float
    contract_start_date: datetime
    contract_end_date: datetime
    renewal_date: datetime
    
    # Account team
    account_manager: Optional[str]
    customer_success_manager: Optional[str]
    technical_contact: Optional[str]

class HealthScoreWeights(BaseModel):
    """Configurable weights for health score calculation"""
    usage_weight: float = 0.30
    adoption_weight: float = 0.25
    engagement_weight: float = 0.20
    support_weight: float = 0.15
    contract_weight: float = 0.10
    
    @validator('usage_weight', 'adoption_weight', 'engagement_weight', 'support_weight', 'contract_weight')
    def validate_weight(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Weight must be between 0 and 1")
        return v
    
    @validator('contract_weight', always=True)
    def validate_total_weight(cls, v, values):
        total = sum([
            values.get('usage_weight', 0),
            values.get('adoption_weight', 0),
            values.get('engagement_weight', 0),
            values.get('support_weight', 0),
            v
        ])
        if not 0.99 <= total <= 1.01:  # Allow small floating point errors
            raise ValueError(f"Total weights must equal 1.0, got {total}")
        return v

class HealthScore(BaseModel):
    """Customer health score details"""
    organization_id: str
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Overall score
    overall_score: float = Field(ge=0, le=100)
    status: HealthStatus
    trend: str  # "improving", "stable", "declining"
    
    # Component scores
    usage_score: float = Field(ge=0, le=100)
    adoption_score: float = Field(ge=0, le=100)
    engagement_score: float = Field(ge=0, le=100)
    support_score: float = Field(ge=0, le=100)
    contract_score: float = Field(ge=0, le=100)
    
    # Risk factors
    risk_factors: List[RiskFactor] = []
    
    # Recommendations
    recommendations: List[str] = []
    
    # Historical comparison
    previous_score: Optional[float] = None
    score_change: Optional[float] = None

class CustomerSuccessMetrics:
    """Tracks and calculates customer success metrics"""
    
    def __init__(self, weights: Optional[HealthScoreWeights] = None):
        self.weights = weights or HealthScoreWeights()
        self.metrics_history: Dict[str, List[UsageMetrics]] = defaultdict(list)
        self.support_history: Dict[str, List[SupportMetrics]] = defaultdict(list)
        self.health_scores: Dict[str, List[HealthScore]] = defaultdict(list)
    
    def calculate_health_score(
        self,
        organization_id: str,
        metadata: CustomerMetadata,
        current_metrics: UsageMetrics,
        support_metrics: SupportMetrics,
        historical_days: int = 30
    ) -> HealthScore:
        """Calculate comprehensive health score"""
        # Get historical data
        historical_metrics = self._get_historical_metrics(
            organization_id, 
            historical_days
        )
        
        # Calculate component scores
        usage_score = self._calculate_usage_score(current_metrics, historical_metrics)
        adoption_score = self._calculate_adoption_score(current_metrics, metadata)
        engagement_score = self._calculate_engagement_score(current_metrics, historical_metrics)
        support_score = self._calculate_support_score(support_metrics)
        contract_score = self._calculate_contract_score(metadata, current_metrics)
        
        # Calculate weighted overall score
        overall_score = (
            usage_score * self.weights.usage_weight +
            adoption_score * self.weights.adoption_weight +
            engagement_score * self.weights.engagement_weight +
            support_score * self.weights.support_weight +
            contract_score * self.weights.contract_weight
        )
        
        # Determine status
        status = self._get_health_status(overall_score)
        
        # Analyze trend
        trend = self._analyze_trend(organization_id, overall_score)
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(
            current_metrics,
            support_metrics,
            metadata,
            overall_score
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            risk_factors,
            current_metrics,
            support_metrics
        )
        
        # Get previous score
        previous_score = None
        score_change = None
        if organization_id in self.health_scores and self.health_scores[organization_id]:
            previous_score = self.health_scores[organization_id][-1].overall_score
            score_change = overall_score - previous_score
        
        # Create health score
        health_score = HealthScore(
            organization_id=organization_id,
            overall_score=overall_score,
            status=status,
            trend=trend,
            usage_score=usage_score,
            adoption_score=adoption_score,
            engagement_score=engagement_score,
            support_score=support_score,
            contract_score=contract_score,
            risk_factors=risk_factors,
            recommendations=recommendations,
            previous_score=previous_score,
            score_change=score_change
        )
        
        # Store score
        self.health_scores[organization_id].append(health_score)
        
        return health_score
    
    def _calculate_usage_score(
        self,
        current: UsageMetrics,
        historical: List[UsageMetrics]
    ) -> float:
        """Calculate usage component score"""
        score = 0.0
        
        # Current usage level (40 points)
        if current.processing_hours > 0:
            # Normalize based on expected usage (e.g., 100 hours/month is good)
            usage_ratio = min(current.processing_hours / 100, 1.0)
            score += usage_ratio * 40
        
        # Usage growth (30 points)
        if historical:
            avg_historical = statistics.mean([m.processing_hours for m in historical])
            if avg_historical > 0:
                growth_ratio = current.processing_hours / avg_historical
                if growth_ratio >= 1.1:  # 10% growth
                    score += 30
                elif growth_ratio >= 0.9:  # Stable
                    score += 20
                else:  # Declining
                    score += 10
        
        # Consistency (30 points)
        if len(historical) >= 4:
            usage_values = [m.processing_hours for m in historical[-4:]]
            if all(v > 0 for v in usage_values):
                cv = statistics.stdev(usage_values) / statistics.mean(usage_values) if statistics.mean(usage_values) > 0 else 1
                consistency_score = max(0, 30 * (1 - cv))
                score += consistency_score
        
        return min(score, 100)
    
    def _calculate_adoption_score(
        self,
        current: UsageMetrics,
        metadata: CustomerMetadata
    ) -> float:
        """Calculate feature adoption score"""
        score = 0.0
        
        # User adoption (40 points)
        if current.total_users > 0:
            adoption_rate = current.active_users / current.total_users
            score += adoption_rate * 40
        
        # Feature adoption (40 points)
        core_features = [
            "transcription", "entity_extraction", "summarization",
            "export", "api_access", "team_collaboration"
        ]
        adopted_features = sum(1 for f in core_features if f in current.features_used)
        feature_adoption_rate = adopted_features / len(core_features)
        score += feature_adoption_rate * 40
        
        # Advanced feature usage (20 points)
        advanced_features = ["custom_vocabulary", "white_label", "integrations"]
        advanced_adopted = sum(1 for f in advanced_features if f in current.features_used)
        if advanced_adopted > 0:
            score += min(advanced_adopted * 10, 20)
        
        return min(score, 100)
    
    def _calculate_engagement_score(
        self,
        current: UsageMetrics,
        historical: List[UsageMetrics]
    ) -> float:
        """Calculate user engagement score"""
        score = 0.0
        
        # Active user ratio (40 points)
        if current.total_users > 0:
            active_ratio = current.active_users / current.total_users
            score += active_ratio * 40
        
        # API usage (30 points)
        if current.api_calls > 0:
            # Good API usage is 1000+ calls per month
            api_score = min(current.api_calls / 1000, 1.0) * 30
            # Penalize for high error rate
            if current.api_error_rate > 0.05:  # >5% errors
                api_score *= 0.5
            score += api_score
        
        # Regular usage pattern (30 points)
        if historical:
            active_periods = sum(1 for m in historical if m.active_users > 0)
            regularity_score = (active_periods / len(historical)) * 30
            score += regularity_score
        
        return min(score, 100)
    
    def _calculate_support_score(self, support: SupportMetrics) -> float:
        """Calculate support health score"""
        score = 100.0  # Start with perfect score and deduct
        
        # Ticket volume (deduct up to 30 points)
        if support.total_tickets > 10:  # High ticket volume
            score -= min((support.total_tickets - 10) * 2, 30)
        
        # Open tickets ratio (deduct up to 20 points)
        if support.total_tickets > 0:
            open_ratio = support.open_tickets / support.total_tickets
            if open_ratio > 0.2:  # >20% open
                score -= min(open_ratio * 40, 20)
        
        # Resolution time (deduct up to 20 points)
        if support.average_resolution_hours > 24:  # >24 hours
            score -= min((support.average_resolution_hours - 24) / 24 * 20, 20)
        
        # Escalations (deduct up to 20 points)
        if support.escalated_tickets > 0:
            score -= min(support.escalated_tickets * 5, 20)
        
        # Satisfaction bonus (add up to 10 points)
        if support.satisfaction_score and support.satisfaction_score >= 4.0:
            score += (support.satisfaction_score - 4.0) * 10
        
        return max(score, 0)
    
    def _calculate_contract_score(
        self,
        metadata: CustomerMetadata,
        current: UsageMetrics
    ) -> float:
        """Calculate contract health score"""
        score = 0.0
        
        # Time to renewal (40 points)
        days_to_renewal = (metadata.renewal_date - datetime.utcnow()).days
        if days_to_renewal > 180:  # >6 months
            score += 40
        elif days_to_renewal > 90:  # 3-6 months
            score += 30
        elif days_to_renewal > 30:  # 1-3 months
            score += 20
        else:  # <1 month
            score += 10
        
        # Contract utilization (40 points)
        # Assume contract includes certain usage limits
        # This is simplified - would need actual contract details
        utilization_score = 40  # Default good utilization
        score += utilization_score
        
        # Growth potential (20 points)
        if current.active_users > 0 and current.processing_hours > 0:
            # Signs of growth = good for renewal
            score += 20
        
        return min(score, 100)
    
    def _get_health_status(self, score: float) -> HealthStatus:
        """Determine health status from score"""
        if score >= 80:
            return HealthStatus.EXCELLENT
        elif score >= 60:
            return HealthStatus.GOOD
        elif score >= 40:
            return HealthStatus.FAIR
        elif score >= 20:
            return HealthStatus.AT_RISK
        else:
            return HealthStatus.CRITICAL
    
    def _analyze_trend(self, organization_id: str, current_score: float) -> str:
        """Analyze score trend"""
        if organization_id not in self.health_scores or len(self.health_scores[organization_id]) < 2:
            return "stable"
        
        recent_scores = [s.overall_score for s in self.health_scores[organization_id][-3:]]
        recent_scores.append(current_score)
        
        # Calculate trend
        if len(recent_scores) >= 2:
            avg_change = statistics.mean([
                recent_scores[i] - recent_scores[i-1] 
                for i in range(1, len(recent_scores))
            ])
            
            if avg_change > 5:
                return "improving"
            elif avg_change < -5:
                return "declining"
        
        return "stable"
    
    def _identify_risk_factors(
        self,
        metrics: UsageMetrics,
        support: SupportMetrics,
        metadata: CustomerMetadata,
        overall_score: float
    ) -> List[RiskFactor]:
        """Identify risk factors"""
        risks = []
        
        # Low usage
        if metrics.processing_hours < 10:  # <10 hours/month
            risks.append(RiskFactor.LOW_USAGE)
        
        # No recent activity
        if metrics.active_users == 0:
            risks.append(RiskFactor.NO_RECENT_LOGIN)
        
        # Low feature adoption
        if len(metrics.features_used) < 3:
            risks.append(RiskFactor.LOW_FEATURE_ADOPTION)
        
        # Support issues
        if support.escalated_tickets > 2 or support.critical_issues > 0:
            risks.append(RiskFactor.SUPPORT_ISSUES)
        
        # Low user adoption
        if metrics.total_users > 0 and metrics.active_users / metrics.total_users < 0.5:
            risks.append(RiskFactor.LOW_USER_ADOPTION)
        
        # API errors
        if metrics.api_error_rate > 0.1:  # >10% error rate
            risks.append(RiskFactor.API_ERRORS)
        
        return risks
    
    def _generate_recommendations(
        self,
        risk_factors: List[RiskFactor],
        metrics: UsageMetrics,
        support: SupportMetrics
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if RiskFactor.LOW_USAGE in risk_factors:
            recommendations.append(
                "Schedule a training session to increase platform adoption"
            )
        
        if RiskFactor.NO_RECENT_LOGIN in risk_factors:
            recommendations.append(
                "Reach out to customer to understand usage barriers"
            )
        
        if RiskFactor.LOW_FEATURE_ADOPTION in risk_factors:
            recommendations.append(
                "Provide feature discovery workshop to showcase advanced capabilities"
            )
        
        if RiskFactor.SUPPORT_ISSUES in risk_factors:
            recommendations.append(
                "Schedule technical review to address recurring issues"
            )
        
        if RiskFactor.LOW_USER_ADOPTION in risk_factors:
            recommendations.append(
                "Implement user onboarding program to increase adoption"
            )
        
        if RiskFactor.API_ERRORS in risk_factors:
            recommendations.append(
                "Provide API integration support and best practices review"
            )
        
        # Positive recommendations for high performers
        if not risk_factors and metrics.processing_hours > 100:
            recommendations.append(
                "Consider upsell opportunity for additional features or capacity"
            )
        
        return recommendations
    
    def _get_historical_metrics(
        self,
        organization_id: str,
        days: int
    ) -> List[UsageMetrics]:
        """Get historical metrics for analysis"""
        if organization_id not in self.metrics_history:
            return []
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return [
            m for m in self.metrics_history[organization_id]
            if m.period_end >= cutoff_date
        ]
    
    def add_usage_metrics(self, organization_id: str, metrics: UsageMetrics):
        """Add usage metrics to history"""
        self.metrics_history[organization_id].append(metrics)
    
    def add_support_metrics(self, organization_id: str, metrics: SupportMetrics):
        """Add support metrics to history"""
        self.support_history[organization_id].append(metrics)
    
    def get_health_history(
        self,
        organization_id: str,
        days: Optional[int] = None
    ) -> List[HealthScore]:
        """Get health score history"""
        scores = self.health_scores.get(organization_id, [])
        
        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            scores = [s for s in scores if s.calculated_at >= cutoff_date]
        
        return scores
    
    def get_at_risk_customers(self) -> List[Tuple[str, HealthScore]]:
        """Get list of at-risk customers"""
        at_risk = []
        
        for org_id, scores in self.health_scores.items():
            if scores:
                latest_score = scores[-1]
                if latest_score.status in [HealthStatus.AT_RISK, HealthStatus.CRITICAL]:
                    at_risk.append((org_id, latest_score))
        
        # Sort by score (lowest first)
        at_risk.sort(key=lambda x: x[1].overall_score)
        
        return at_risk
    
    def generate_executive_summary(
        self,
        organization_id: str
    ) -> Dict[str, Any]:
        """Generate executive summary for customer"""
        if organization_id not in self.health_scores or not self.health_scores[organization_id]:
            return {"error": "No health score data available"}
        
        latest_score = self.health_scores[organization_id][-1]
        historical_scores = self.get_health_history(organization_id, days=90)
        
        # Calculate averages
        avg_score = statistics.mean([s.overall_score for s in historical_scores]) if historical_scores else 0
        
        # Trend analysis
        score_changes = []
        for i in range(1, len(historical_scores)):
            score_changes.append(
                historical_scores[i].overall_score - historical_scores[i-1].overall_score
            )
        
        trend_direction = "stable"
        if score_changes:
            avg_change = statistics.mean(score_changes)
            if avg_change > 2:
                trend_direction = "positive"
            elif avg_change < -2:
                trend_direction = "negative"
        
        return {
            "current_score": latest_score.overall_score,
            "status": latest_score.status,
            "trend": trend_direction,
            "average_score_90d": round(avg_score, 1),
            "risk_factors": latest_score.risk_factors,
            "top_recommendations": latest_score.recommendations[:3],
            "component_scores": {
                "usage": latest_score.usage_score,
                "adoption": latest_score.adoption_score,
                "engagement": latest_score.engagement_score,
                "support": latest_score.support_score,
                "contract": latest_score.contract_score
            }
        }

# Example usage
if __name__ == "__main__":
    # Initialize customer success metrics
    cs_metrics = CustomerSuccessMetrics()
    
    # Sample customer metadata
    metadata = CustomerMetadata(
        organization_id="acme_corp",
        organization_name="Acme Corporation",
        industry="Technology",
        company_size="500-1000",
        contract_value=50000,
        contract_start_date=datetime.utcnow() - timedelta(days=180),
        contract_end_date=datetime.utcnow() + timedelta(days=185),
        renewal_date=datetime.utcnow() + timedelta(days=185)
    )
    
    # Sample usage metrics
    usage = UsageMetrics(
        period_start=datetime.utcnow() - timedelta(days=30),
        period_end=datetime.utcnow(),
        total_users=50,
        active_users=35,
        new_users=5,
        processing_hours=250.5,
        transcription_count=1200,
        storage_gb_used=45.2,
        api_calls=5000,
        api_errors=50,
        features_used={
            "transcription": 1200,
            "entity_extraction": 800,
            "summarization": 600,
            "api_access": 5000,
            "team_collaboration": 200
        }
    )
    
    # Sample support metrics
    support = SupportMetrics(
        total_tickets=5,
        open_tickets=1,
        resolved_tickets=4,
        average_resolution_hours=12.5,
        satisfaction_score=4.5,
        ticket_categories={
            "technical": 3,
            "billing": 1,
            "feature_request": 1
        }
    )
    
    # Calculate health score
    health_score = cs_metrics.calculate_health_score(
        organization_id="acme_corp",
        metadata=metadata,
        current_metrics=usage,
        support_metrics=support
    )
    
    print(f"Health Score: {health_score.overall_score:.1f}")
    print(f"Status: {health_score.status}")
    print(f"Trend: {health_score.trend}")
    print(f"Risk Factors: {health_score.risk_factors}")
    print(f"Recommendations: {health_score.recommendations}")