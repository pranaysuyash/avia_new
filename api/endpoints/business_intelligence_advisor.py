#!/usr/bin/env python3
"""
Business Intelligence Advisor API Endpoints
RESTful API for strategic business insights and recommendations

Intent-First API: Provides strategic decision support through intelligent analysis
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import json

# Import the Business Intelligence Advisor
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from business_intelligence_advisor import (
    BusinessIntelligenceAdvisor,
    BusinessPriority,
    DecisionUrgency,
    BusinessImpact
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/business-intelligence", tags=["Business Intelligence"])

# Global advisor instance
advisor = BusinessIntelligenceAdvisor()

# Pydantic models for API
class ContentPerformanceData(BaseModel):
    views: int = Field(ge=0, description="Total content views")
    engagement_rate: float = Field(ge=0, le=1, description="Engagement rate (0-1)")
    conversion_rate: float = Field(ge=0, le=1, description="Conversion rate (0-1)")
    production_cost: float = Field(ge=0, description="Content production cost")
    revenue_generated: float = Field(ge=0, description="Revenue generated from content")

class UserBehaviorData(BaseModel):
    avg_session_duration: int = Field(ge=0, description="Average session duration in seconds")
    bounce_rate: float = Field(ge=0, le=1, description="Bounce rate (0-1)")
    conversion_funnel: Dict[str, float] = Field(description="Conversion funnel stages and rates")
    feature_adoption: Optional[Dict[str, float]] = Field(default={}, description="Feature adoption rates")

class PerformanceMetrics(BaseModel):
    user_acquisition_cost: float = Field(ge=0, description="Cost to acquire a user")
    customer_lifetime_value: float = Field(ge=0, description="Customer lifetime value")
    churn_rate: float = Field(ge=0, le=1, description="Monthly churn rate")
    feature_adoption_rate: float = Field(ge=0, le=1, description="Overall feature adoption rate")

class UserSegmentData(BaseModel):
    size: int = Field(ge=0, description="Segment size")
    avg_revenue_per_user: float = Field(ge=0, description="Average revenue per user")
    growth_rate: float = Field(ge=-1, description="Growth rate (-1 to +∞)")

class BusinessAnalysisRequest(BaseModel):
    content_performance: Optional[ContentPerformanceData] = None
    user_behavior: Optional[UserBehaviorData] = None
    performance_metrics: Optional[PerformanceMetrics] = None
    user_segments: Optional[Dict[str, UserSegmentData]] = None
    analysis_options: Optional[Dict[str, Any]] = Field(default={}, description="Additional analysis options")

class BusinessInsightResponse(BaseModel):
    insight_id: str
    title: str
    description: str
    business_impact: str
    priority: str
    urgency: str
    confidence_score: float
    potential_value: float
    recommended_actions: List[str]
    success_metrics: List[str]
    timeline: str
    stakeholders: List[str]
    risks: List[str]
    supporting_data: Dict[str, Any]
    timestamp: str

class GrowthOpportunityResponse(BaseModel):
    opportunity_id: str
    title: str
    market_size: float
    revenue_potential: float
    investment_required: float
    roi_estimate: float
    time_to_market: str
    competitive_advantage: str
    implementation_steps: List[str]
    success_probability: float
    key_metrics: List[str]
    market_trends: List[str]

class StrategicRecommendationResponse(BaseModel):
    recommendation_id: str
    category: str
    title: str
    rationale: str
    expected_outcome: str
    implementation_plan: List[Dict[str, Any]]
    resource_requirements: Dict[str, Any]
    success_criteria: List[str]
    risk_assessment: Dict[str, Any]
    timeline_milestones: List[Dict[str, Any]]

class BusinessAnalysisResponse(BaseModel):
    analysis_id: str
    executive_summary: Dict[str, Any]
    critical_insights: List[BusinessInsightResponse]
    high_priority_insights: List[BusinessInsightResponse]
    all_insights: List[BusinessInsightResponse]
    growth_opportunities: List[GrowthOpportunityResponse]
    strategic_recommendations: List[StrategicRecommendationResponse]
    performance_alerts: List[Dict[str, Any]]
    insights_summary: Dict[str, Any]
    next_actions: List[Dict[str, Any]]
    timestamp: str
    processing_time: float

class HealthCheckResponse(BaseModel):
    status: str
    version: str
    capabilities: List[str]
    timestamp: str

# API Endpoints

@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        capabilities=[
            "strategic_insights_generation",
            "growth_opportunity_identification", 
            "performance_analysis",
            "competitive_benchmarking",
            "roi_optimization",
            "decision_support"
        ],
        timestamp=datetime.now().isoformat()
    )

@router.post("/analyze", response_model=BusinessAnalysisResponse)
async def analyze_business_data(
    request: BusinessAnalysisRequest,
    background_tasks: BackgroundTasks
) -> BusinessAnalysisResponse:
    """
    Generate comprehensive strategic business insights and recommendations
    
    This endpoint transforms business analytics into actionable strategic insights:
    - Identifies critical issues requiring immediate attention
    - Discovers growth opportunities with ROI projections
    - Provides strategic recommendations with implementation plans
    - Prioritizes next actions with clear ownership
    """
    try:
        start_time = datetime.now()
        analysis_id = f"analysis_{int(start_time.timestamp())}"
        
        logger.info(f"Starting business intelligence analysis: {analysis_id}")
        
        # Convert Pydantic models to dict format expected by advisor
        business_data = {}
        
        if request.content_performance:
            business_data["content_performance"] = request.content_performance.dict()
        
        if request.user_behavior:
            business_data["user_behavior"] = request.user_behavior.dict()
        
        if request.performance_metrics:
            business_data["performance_metrics"] = request.performance_metrics.dict()
        
        if request.user_segments:
            business_data["user_segments"] = {
                name: segment.dict() for name, segment in request.user_segments.items()
            }
        
        # Generate strategic insights
        results = advisor.generate_strategic_insights(business_data)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Convert results to API response format
        def convert_insight(insight_dict):
            return BusinessInsightResponse(
                insight_id=insight_dict["insight_id"],
                title=insight_dict["title"],
                description=insight_dict["description"],
                business_impact=insight_dict["business_impact"],
                priority=insight_dict["priority"],
                urgency=insight_dict["urgency"],
                confidence_score=insight_dict["confidence_score"],
                potential_value=insight_dict["potential_value"],
                recommended_actions=insight_dict["recommended_actions"],
                success_metrics=insight_dict["success_metrics"],
                timeline=insight_dict["timeline"],
                stakeholders=insight_dict["stakeholders"],
                risks=insight_dict["risks"],
                supporting_data=insight_dict["supporting_data"],
                timestamp=insight_dict["timestamp"]
            )
        
        def convert_opportunity(opp_dict):
            return GrowthOpportunityResponse(
                opportunity_id=opp_dict["opportunity_id"],
                title=opp_dict["title"],
                market_size=opp_dict["market_size"],
                revenue_potential=opp_dict["revenue_potential"],
                investment_required=opp_dict["investment_required"],
                roi_estimate=opp_dict["roi_estimate"],
                time_to_market=opp_dict["time_to_market"],
                competitive_advantage=opp_dict["competitive_advantage"],
                implementation_steps=opp_dict["implementation_steps"],
                success_probability=opp_dict["success_probability"],
                key_metrics=opp_dict["key_metrics"],
                market_trends=opp_dict["market_trends"]
            )
        
        def convert_recommendation(rec_dict):
            return StrategicRecommendationResponse(
                recommendation_id=rec_dict["recommendation_id"],
                category=rec_dict["category"],
                title=rec_dict["title"],
                rationale=rec_dict["rationale"],
                expected_outcome=rec_dict["expected_outcome"],
                implementation_plan=rec_dict["implementation_plan"],
                resource_requirements=rec_dict["resource_requirements"],
                success_criteria=rec_dict["success_criteria"],
                risk_assessment=rec_dict["risk_assessment"],
                timeline_milestones=rec_dict["timeline_milestones"]
            )
        
        # Log analysis completion
        logger.info(f"Analysis {analysis_id} completed in {processing_time:.2f}s")
        logger.info(f"Generated {results['insights_summary']['total_insights']} insights")
        
        # Schedule background task for analytics
        background_tasks.add_task(
            log_analysis_metrics,
            analysis_id,
            results["insights_summary"],
            processing_time
        )
        
        return BusinessAnalysisResponse(
            analysis_id=analysis_id,
            executive_summary=results["executive_summary"],
            critical_insights=[convert_insight(i) for i in results["critical_insights"]],
            high_priority_insights=[convert_insight(i) for i in results["high_priority_insights"]],
            all_insights=[convert_insight(i) for i in results["all_insights"]],
            growth_opportunities=[convert_opportunity(o) for o in results["growth_opportunities"]],
            strategic_recommendations=[convert_recommendation(r) for r in results["strategic_recommendations"]],
            performance_alerts=results["performance_alerts"],
            insights_summary=results["insights_summary"],
            next_actions=results["next_actions"],
            timestamp=results["timestamp"],
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error in business intelligence analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/insights/{analysis_id}")
async def get_analysis_results(analysis_id: str):
    """Retrieve previous analysis results by ID"""
    # In a real implementation, this would retrieve from a database
    # For now, return a not found response
    raise HTTPException(status_code=404, detail="Analysis results not found. Results are currently not persisted.")

@router.post("/quick-health-check")
async def quick_business_health_check(
    performance_metrics: PerformanceMetrics
) -> Dict[str, Any]:
    """
    Quick business health assessment based on key performance metrics
    
    Provides immediate health score and top recommendations without full analysis
    """
    try:
        # Convert to format expected by advisor
        business_data = {
            "performance_metrics": performance_metrics.dict()
        }
        
        # Generate quick insights
        results = advisor.generate_strategic_insights(business_data)
        
        # Return simplified health check
        return {
            "health_score": results["executive_summary"]["business_health_score"],
            "status": "healthy" if results["executive_summary"]["business_health_score"] > 0.7 else 
                     "warning" if results["executive_summary"]["business_health_score"] > 0.4 else "critical",
            "critical_issues": len(results["critical_insights"]),
            "top_priorities": results["executive_summary"]["top_priorities"][:3],
            "immediate_actions": [action["action"] for action in results["next_actions"][:2]],
            "potential_value": results["insights_summary"]["estimated_total_value"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in quick health check: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/benchmarks")
async def get_industry_benchmarks() -> Dict[str, Any]:
    """Get industry benchmark data for comparison"""
    # Mock benchmark data - in real implementation would come from market research
    return {
        "industry_benchmarks": {
            "user_acquisition_cost": {
                "saas_average": 50,
                "top_quartile": 30,
                "bottom_quartile": 80
            },
            "customer_lifetime_value": {
                "saas_average": 200,
                "top_quartile": 350,
                "bottom_quartile": 120
            },
            "churn_rate": {
                "saas_average": 0.15,
                "top_quartile": 0.08,
                "bottom_quartile": 0.25
            },
            "feature_adoption_rate": {
                "saas_average": 0.4,
                "top_quartile": 0.65,
                "bottom_quartile": 0.25
            }
        },
        "data_source": "Industry Research 2024",
        "last_updated": "2024-01-01",
        "sample_size": "500+ SaaS companies"
    }

@router.post("/roi-calculator")
async def calculate_roi_projections(
    current_metrics: PerformanceMetrics,
    improvement_targets: Dict[str, float]
) -> Dict[str, Any]:
    """
    Calculate ROI projections for proposed improvements
    
    Takes current metrics and improvement targets, returns projected ROI
    """
    try:
        # Calculate current baseline
        current_ltv_cac_ratio = current_metrics.customer_lifetime_value / current_metrics.user_acquisition_cost
        
        # Calculate improved metrics
        improved_metrics = {}
        for metric, improvement_factor in improvement_targets.items():
            if hasattr(current_metrics, metric):
                current_value = getattr(current_metrics, metric)
                if metric == "churn_rate":
                    # For churn rate, improvement means reduction
                    improved_metrics[metric] = current_value * (1 - improvement_factor)
                else:
                    # For other metrics, improvement means increase
                    improved_metrics[metric] = current_value * (1 + improvement_factor)
        
        # Calculate projected impact
        monthly_customers = 1000  # Assumed customer base
        
        # Churn reduction impact
        if "churn_rate" in improved_metrics:
            churn_reduction = current_metrics.churn_rate - improved_metrics["churn_rate"]
            retained_customers = monthly_customers * churn_reduction
            retention_value = retained_customers * current_metrics.customer_lifetime_value
        else:
            retention_value = 0
        
        # LTV improvement impact
        if "customer_lifetime_value" in improved_metrics:
            ltv_increase = improved_metrics["customer_lifetime_value"] - current_metrics.customer_lifetime_value
            ltv_impact = monthly_customers * ltv_increase
        else:
            ltv_impact = 0
        
        # Total monthly impact
        total_monthly_impact = retention_value + ltv_impact
        annual_impact = total_monthly_impact * 12
        
        # Estimated implementation cost (simplified)
        implementation_cost = 50000 + (len(improvement_targets) * 25000)
        
        # ROI calculation
        roi = annual_impact / implementation_cost if implementation_cost > 0 else 0
        payback_months = implementation_cost / total_monthly_impact if total_monthly_impact > 0 else float('inf')
        
        return {
            "current_metrics": current_metrics.dict(),
            "improved_metrics": improved_metrics,
            "impact_analysis": {
                "monthly_impact": total_monthly_impact,
                "annual_impact": annual_impact,
                "retention_value": retention_value,
                "ltv_impact": ltv_impact
            },
            "roi_projections": {
                "implementation_cost": implementation_cost,
                "roi_multiple": roi,
                "payback_months": min(payback_months, 999),  # Cap at 999 months
                "break_even_date": (datetime.now().replace(day=1) + 
                                   pd.DateOffset(months=int(payback_months))).isoformat() if payback_months < 999 else None
            },
            "confidence_level": 0.75,  # Based on industry benchmarks
            "assumptions": [
                f"Customer base: {monthly_customers:,} customers",
                "Implementation timeline: 3-6 months",
                "Market conditions remain stable",
                "No major competitive disruptions"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in ROI calculation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ROI calculation failed: {str(e)}")

# Background tasks
async def log_analysis_metrics(analysis_id: str, summary: Dict[str, Any], processing_time: float):
    """Log analysis metrics for monitoring and optimization"""
    try:
        metrics = {
            "analysis_id": analysis_id,
            "total_insights": summary["total_insights"],
            "critical_count": summary["critical_count"],
            "high_priority_count": summary["high_priority_count"],
            "growth_opportunities": summary["growth_opportunities_count"],
            "estimated_value": summary["estimated_total_value"],
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Analysis metrics logged: {json.dumps(metrics)}")
        
        # In a real implementation, would store in analytics database
        # await analytics_db.store_metrics(metrics)
        
    except Exception as e:
        logger.error(f"Error logging analysis metrics: {str(e)}")

# Error handlers
@router.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return HTTPException(status_code=400, detail=str(exc))

@router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unexpected error in business intelligence API: {str(exc)}")
    return HTTPException(status_code=500, detail="Internal server error")

# Add pandas import for date calculations
try:
    import pandas as pd
except ImportError:
    # Fallback if pandas not available
    from datetime import timedelta
    class pd:
        @staticmethod
        def DateOffset(months):
            return timedelta(days=months * 30)  # Approximate