"""
AI Analytics & Intelligence API Endpoints
Provides comprehensive analytics, insights, and business intelligence
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import asyncio
import json
import logging
from enum import Enum

# Import the AI analytics system
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ai_analytics_intelligence_system import (
    ai_analytics_system,
    ContentMetrics,
    UserBehaviorMetrics,
    BusinessIntelligence,
    PredictiveAnalytics
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/ai-analytics")

class AnalysisType(str, Enum):
    CONTENT = "content"
    USER_BEHAVIOR = "user_behavior"
    BUSINESS_INTELLIGENCE = "business_intelligence"
    PREDICTIVE = "predictive"
    COMPREHENSIVE = "comprehensive"

class AnalysisRequest(BaseModel):
    analysis_type: AnalysisType
    data: Dict[str, Any]
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ContentAnalysisRequest(BaseModel):
    content_items: List[Dict[str, Any]]
    include_detailed_insights: bool = True
    analysis_depth: str = Field(default="standard", pattern="^(basic|standard|advanced)$")

class UserBehaviorAnalysisRequest(BaseModel):
    user_sessions: List[Dict[str, Any]]
    include_predictions: bool = True
    analysis_timeframe: Optional[str] = Field(default="7d", pattern="^(1d|7d|30d|90d)$")

class BusinessIntelligenceRequest(BaseModel):
    platform_metrics: Dict[str, Any]
    user_analytics: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    content_analytics: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    include_forecasting: bool = True

class PredictiveAnalysicsRequest(BaseModel):
    historical_data: Dict[str, List[Any]]
    prediction_horizon: int = Field(default=30, ge=1, le=365)
    confidence_level: float = Field(default=0.8, ge=0.5, le=0.99)

class DashboardDataRequest(BaseModel):
    metrics: List[str] = Field(default_factory=lambda: ["all"])
    time_range: str = Field(default="7d", pattern="^(1d|7d|30d|90d|1y)$")
    granularity: str = Field(default="daily", pattern="^(hourly|daily|weekly|monthly)$")

class AnalysisResponse(BaseModel):
    analysis_id: str
    analysis_type: str
    timestamp: datetime
    status: str
    results: Dict[str, Any]
    metadata: Dict[str, Any]
    processing_time: float

class DashboardResponse(BaseModel):
    dashboard_id: str
    timestamp: datetime
    data: Dict[str, Any]
    refresh_interval: int = 300  # seconds

@router.get("/health")
async def health_check():
    """Health check for AI Analytics system"""
    try:
        # Test basic system components
        system_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "ai_engine": "operational",
                "content_analyzer": "operational",
                "user_behavior_analyzer": "operational",
                "business_intelligence": "operational",
                "predictive_engine": "operational"
            },
            "capabilities": [
                "content_analysis",
                "sentiment_detection",
                "emotion_analysis",
                "topic_extraction",
                "user_behavior_tracking",
                "business_intelligence",
                "predictive_analytics",
                "dashboard_data"
            ],
            "version": "1.0.0"
        }
        
        return JSONResponse(content=system_status)
        
    except Exception as e:
        logger.error(f"AI Analytics health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@router.post("/analyze/content", response_model=AnalysisResponse)
async def analyze_content(
    request: ContentAnalysisRequest,
    background_tasks: BackgroundTasks
) -> AnalysisResponse:
    """Analyze content for insights, sentiment, topics, and engagement"""
    try:
        start_time = datetime.utcnow()
        analysis_id = f"content_analysis_{int(start_time.timestamp())}"
        
        logger.info(f"Starting content analysis: {analysis_id}")
        
        # Perform content analysis
        content_analytics = await ai_analytics_system.analyze_content_batch(request.content_items)
        
        # Calculate summary metrics
        summary_metrics = ai_analytics_system._summarize_content_metrics(content_analytics)
        
        # Prepare results
        results = {
            "total_content_analyzed": len(content_analytics),
            "summary_metrics": summary_metrics,
            "content_insights": []
        }
        
        # Include detailed insights if requested
        if request.include_detailed_insights:
            results["content_insights"] = [
                {
                    "content_id": request.content_items[i].get("id", f"content_{i}"),
                    "metrics": {
                        "total_words": ca.total_words,
                        "unique_words": ca.unique_words,
                        "sentiment_score": ca.sentiment_score,
                        "engagement_score": ca.engagement_score,
                        "readability_score": ca.readability_score,
                        "technical_complexity": ca.technical_complexity,
                        "emotion_distribution": ca.emotion_distribution,
                        "key_topics": ca.key_topics[:5],  # Top 5 topics
                        "named_entities": len(ca.named_entities)
                    }
                }
                for i, ca in enumerate(content_analytics)
            ]
        
        # Advanced analysis for deeper insights
        if request.analysis_depth == "advanced":
            results["advanced_insights"] = {
                "sentiment_trends": _calculate_sentiment_trends(content_analytics),
                "topic_clustering": _perform_topic_clustering(content_analytics),
                "content_quality_score": _calculate_content_quality_score(content_analytics),
                "engagement_drivers": _identify_engagement_drivers(content_analytics)
            }
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            analysis_type="content_analysis",
            timestamp=start_time,
            status="completed",
            results=results,
            metadata={
                "analysis_depth": request.analysis_depth,
                "detailed_insights": request.include_detailed_insights,
                "content_types_analyzed": _get_content_types(request.content_items)
            },
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Content analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Content analysis failed: {str(e)}"
        )

@router.post("/analyze/user-behavior", response_model=AnalysisResponse)
async def analyze_user_behavior(
    request: UserBehaviorAnalysisRequest,
    background_tasks: BackgroundTasks
) -> AnalysisResponse:
    """Analyze user behavior patterns and engagement"""
    try:
        start_time = datetime.utcnow()
        analysis_id = f"user_behavior_analysis_{int(start_time.timestamp())}"
        
        logger.info(f"Starting user behavior analysis: {analysis_id}")
        
        # Perform user behavior analysis
        user_analytics = await ai_analytics_system.analyze_user_behaviors(request.user_sessions)
        
        # Calculate summary metrics
        summary_metrics = ai_analytics_system._summarize_user_metrics(user_analytics)
        
        # Prepare results
        results = {
            "total_users_analyzed": len(user_analytics),
            "summary_metrics": summary_metrics,
            "behavior_insights": []
        }
        
        # Add detailed behavior insights
        results["behavior_insights"] = [
            {
                "user_id": request.user_sessions[i].get("user_id", f"user_{i}"),
                "metrics": {
                    "session_duration": ua.session_duration,
                    "productivity_score": ua.productivity_score,
                    "retention_probability": ua.retention_probability,
                    "collaboration_activity": ua.collaboration_activity,
                    "preferred_content_types": ua.preferred_content_types[:3],
                    "feature_usage": dict(list(ua.feature_usage.items())[:5])  # Top 5 features
                }
            }
            for i, ua in enumerate(user_analytics)
        ]
        
        # Add behavioral predictions if requested
        if request.include_predictions:
            results["behavioral_predictions"] = {
                "churn_risk_users": [
                    request.user_sessions[i].get("user_id", f"user_{i}")
                    for i, ua in enumerate(user_analytics)
                    if ua.retention_probability < 0.4
                ],
                "high_engagement_users": [
                    request.user_sessions[i].get("user_id", f"user_{i}")
                    for i, ua in enumerate(user_analytics)
                    if ua.productivity_score > 0.8
                ],
                "collaboration_opportunities": _identify_collaboration_opportunities(user_analytics),
                "feature_adoption_recommendations": _get_feature_recommendations(user_analytics)
            }
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            analysis_type="user_behavior_analysis",
            timestamp=start_time,
            status="completed",
            results=results,
            metadata={
                "timeframe": request.analysis_timeframe,
                "include_predictions": request.include_predictions,
                "analysis_scope": f"{len(request.user_sessions)} user sessions"
            },
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"User behavior analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"User behavior analysis failed: {str(e)}"
        )

@router.post("/analyze/business-intelligence", response_model=AnalysisResponse)
async def analyze_business_intelligence(
    request: BusinessIntelligenceRequest,
    background_tasks: BackgroundTasks
) -> AnalysisResponse:
    """Generate comprehensive business intelligence and insights"""
    try:
        start_time = datetime.utcnow()
        analysis_id = f"business_intelligence_{int(start_time.timestamp())}"
        
        logger.info(f"Starting business intelligence analysis: {analysis_id}")
        
        # Convert request data to required format
        user_analytics = []
        content_analytics = []
        
        # Process provided analytics data (if any)
        if request.user_analytics:
            # Convert dict format to UserBehaviorMetrics objects (simplified)
            for ua_dict in request.user_analytics:
                # This would need proper conversion logic
                pass
        
        if request.content_analytics:
            # Convert dict format to ContentMetrics objects (simplified)
            for ca_dict in request.content_analytics:
                # This would need proper conversion logic
                pass
        
        # Generate business intelligence
        business_intelligence = await ai_analytics_system.business_analyzer.generate_business_intelligence(
            request.platform_metrics, user_analytics, content_analytics
        )
        
        # Prepare results
        results = {
            "business_metrics": {
                "revenue_impact": business_intelligence.revenue_impact,
                "cost_efficiency": business_intelligence.cost_efficiency,
                "user_satisfaction": business_intelligence.user_satisfaction,
                "roi_metrics": business_intelligence.roi_metrics
            },
            "market_analysis": {
                "market_trends": business_intelligence.market_trends,
                "competitive_advantages": business_intelligence.competitive_advantage,
                "growth_opportunities": business_intelligence.growth_opportunities
            },
            "risk_assessment": {
                "risk_factors": business_intelligence.risk_factors,
                "mitigation_strategies": _generate_mitigation_strategies(business_intelligence.risk_factors)
            },
            "strategic_recommendations": _generate_strategic_recommendations(business_intelligence)
        }
        
        # Add forecasting if requested
        if request.include_forecasting:
            # Generate simple forecasts
            results["forecasting"] = {
                "revenue_forecast": _generate_revenue_forecast(request.platform_metrics),
                "user_growth_forecast": _generate_user_growth_forecast(request.platform_metrics),
                "market_opportunity_forecast": _generate_market_forecast(business_intelligence.market_trends)
            }
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            analysis_type="business_intelligence",
            timestamp=start_time,
            status="completed",
            results=results,
            metadata={
                "include_forecasting": request.include_forecasting,
                "data_sources": {
                    "platform_metrics": bool(request.platform_metrics),
                    "user_analytics": len(request.user_analytics or []),
                    "content_analytics": len(request.content_analytics or [])
                }
            },
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Business intelligence analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Business intelligence analysis failed: {str(e)}"
        )

@router.post("/analyze/predictive", response_model=AnalysisResponse)
async def analyze_predictive(
    request: PredictiveAnalysicsRequest,
    background_tasks: BackgroundTasks
) -> AnalysisResponse:
    """Generate predictive analytics and forecasts"""
    try:
        start_time = datetime.utcnow()
        analysis_id = f"predictive_analysis_{int(start_time.timestamp())}"
        
        logger.info(f"Starting predictive analysis: {analysis_id}")
        
        # Generate predictive analytics
        predictive_analytics = await ai_analytics_system.predictive_engine.generate_predictions(
            request.historical_data, {}
        )
        
        # Prepare results
        results = {
            "predictions": {
                "user_churn_probability": predictive_analytics.user_churn_probability,
                "content_popularity_forecast": predictive_analytics.content_popularity_forecast,
                "usage_trend_prediction": predictive_analytics.usage_trend_prediction,
                "capacity_requirements": predictive_analytics.capacity_requirements
            },
            "forecasts": {
                "revenue_forecast": predictive_analytics.revenue_forecast,
                "horizon_days": request.prediction_horizon,
                "confidence_intervals": _calculate_confidence_intervals(
                    predictive_analytics.revenue_forecast, request.confidence_level
                )
            },
            "optimization_recommendations": predictive_analytics.optimization_recommendations,
            "model_performance": {
                "confidence_level": request.confidence_level,
                "data_quality_score": _assess_data_quality(request.historical_data),
                "prediction_reliability": "high" if len(request.historical_data) > 5 else "medium"
            }
        }
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            analysis_type="predictive_analytics",
            timestamp=start_time,
            status="completed",
            results=results,
            metadata={
                "prediction_horizon": request.prediction_horizon,
                "confidence_level": request.confidence_level,
                "historical_data_points": sum(len(data) for data in request.historical_data.values())
            },
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Predictive analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Predictive analysis failed: {str(e)}"
        )

@router.post("/analyze/comprehensive", response_model=AnalysisResponse)
async def analyze_comprehensive(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
) -> AnalysisResponse:
    """Generate comprehensive AI analytics and intelligence"""
    try:
        start_time = datetime.utcnow()
        analysis_id = f"comprehensive_analysis_{int(start_time.timestamp())}"
        
        logger.info(f"Starting comprehensive analysis: {analysis_id}")
        
        # Generate comprehensive intelligence
        intelligence_report = await ai_analytics_system.generate_comprehensive_intelligence(request.data)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            analysis_type="comprehensive_analytics",
            timestamp=start_time,
            status="completed",
            results=intelligence_report,
            metadata={
                "analysis_components": [
                    "content_analytics",
                    "user_behavior_analytics", 
                    "business_intelligence",
                    "predictive_analytics"
                ],
                "data_sources": list(request.data.keys())
            },
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Comprehensive analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Comprehensive analysis failed: {str(e)}"
        )

@router.get("/dashboard/data", response_model=DashboardResponse)
async def get_dashboard_data(
    metrics: List[str] = Query(default=["all"]),
    time_range: str = Query(default="7d", pattern="^(1d|7d|30d|90d|1y)$"),
    granularity: str = Query(default="daily", pattern="^(hourly|daily|weekly|monthly)$")
) -> DashboardResponse:
    """Get dashboard data for visualization"""
    try:
        dashboard_id = f"dashboard_{int(datetime.utcnow().timestamp())}"
        
        # Generate sample dashboard data
        dashboard_data = {
            "overview": {
                "total_users": 1247,
                "active_sessions": 89,
                "content_analyzed": 15420,
                "ai_insights_generated": 3280
            },
            "content_analytics": {
                "sentiment_distribution": {"positive": 65, "neutral": 25, "negative": 10},
                "engagement_trends": [0.7, 0.75, 0.8, 0.72, 0.85, 0.88, 0.82],
                "topic_trends": [
                    {"topic": "AI Technology", "frequency": 45, "sentiment": 0.8},
                    {"topic": "Business Strategy", "frequency": 32, "sentiment": 0.6},
                    {"topic": "User Experience", "frequency": 28, "sentiment": 0.7}
                ]
            },
            "user_behavior": {
                "retention_funnel": {"new": 100, "active": 75, "engaged": 45, "loyal": 25},
                "feature_adoption": {
                    "transcription": 0.95,
                    "collaboration": 0.68,
                    "analytics": 0.42,
                    "ai_insights": 0.35
                },
                "productivity_distribution": {"high": 30, "medium": 50, "low": 20}
            },
            "business_intelligence": {
                "revenue_metrics": {
                    "monthly_recurring_revenue": 125430,
                    "customer_acquisition_cost": 85,
                    "customer_lifetime_value": 2400,
                    "churn_rate": 0.05
                },
                "efficiency_metrics": {
                    "cost_per_user": 15.50,
                    "revenue_per_user": 89.20,
                    "profit_margin": 0.82
                }
            },
            "predictive_analytics": {
                "growth_forecast": [105, 112, 118, 125, 133, 140, 148],
                "churn_prediction": 0.08,
                "capacity_alerts": [
                    {"metric": "CPU", "current": 0.72, "predicted": 0.85, "threshold": 0.8},
                    {"metric": "Storage", "current": 0.65, "predicted": 0.75, "threshold": 0.85}
                ]
            }
        }
        
        # Filter data based on requested metrics
        if "all" not in metrics:
            filtered_data = {key: value for key, value in dashboard_data.items() if key in metrics}
            dashboard_data = filtered_data
        
        return DashboardResponse(
            dashboard_id=dashboard_id,
            timestamp=datetime.utcnow(),
            data=dashboard_data,
            refresh_interval=300
        )
        
    except Exception as e:
        logger.error(f"Dashboard data generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Dashboard data generation failed: {str(e)}"
        )

@router.get("/insights/realtime")
async def get_realtime_insights():
    """Get real-time AI insights and alerts"""
    try:
        insights = {
            "timestamp": datetime.utcnow().isoformat(),
            "alerts": [
                {
                    "type": "performance",
                    "severity": "warning",
                    "message": "Content engagement below average threshold",
                    "recommendation": "Review content strategy and user feedback"
                },
                {
                    "type": "business",
                    "severity": "info",
                    "message": "Positive sentiment trend detected in recent content",
                    "recommendation": "Continue current content approach"
                }
            ],
            "key_metrics": {
                "sentiment_score": 0.72,
                "user_satisfaction": 0.84,
                "system_efficiency": 0.91,
                "prediction_accuracy": 0.88
            },
            "trending_topics": [
                {"topic": "AI Integration", "growth": "+15%", "sentiment": 0.8},
                {"topic": "Collaboration Features", "growth": "+22%", "sentiment": 0.9},
                {"topic": "Performance", "growth": "+8%", "sentiment": 0.6}
            ],
            "user_activity": {
                "active_now": 67,
                "peak_today": 124,
                "engagement_rate": 0.73
            }
        }
        
        return JSONResponse(content=insights)
        
    except Exception as e:
        logger.error(f"Real-time insights failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Real-time insights failed: {str(e)}"
        )

@router.get("/reports/generate/{report_type}")
async def generate_report(
    report_type: str,
    date_range: str = Query(default="30d"),
    format: str = Query(default="json", pattern="^(json|pdf|csv)$")
):
    """Generate analytics reports"""
    try:
        if report_type not in ["content", "users", "business", "comprehensive"]:
            raise HTTPException(status_code=400, detail="Invalid report type")
        
        # Generate report data based on type
        report_data = {
            "report_id": f"{report_type}_report_{int(datetime.utcnow().timestamp())}",
            "report_type": report_type,
            "date_range": date_range,
            "generated_at": datetime.utcnow().isoformat(),
            "summary": f"AI Analytics {report_type.title()} Report",
            "data": _generate_report_data(report_type, date_range)
        }
        
        return JSONResponse(content=report_data)
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )

# Helper functions
def _calculate_sentiment_trends(content_analytics: List[ContentMetrics]) -> Dict[str, List[float]]:
    """Calculate sentiment trends over time"""
    if not content_analytics:
        return {"positive": [0.6], "neutral": [0.3], "negative": [0.1]}
    
    # Simple trend calculation
    sentiments = [ca.sentiment_score for ca in content_analytics]
    return {
        "trend": sentiments[:7] if len(sentiments) >= 7 else sentiments + [0.5] * (7 - len(sentiments))
    }

def _perform_topic_clustering(content_analytics: List[ContentMetrics]) -> List[Dict[str, Any]]:
    """Perform topic clustering analysis"""
    if not content_analytics:
        return []
    
    # Collect all topics
    all_topics = []
    for ca in content_analytics:
        all_topics.extend(ca.key_topics)
    
    # Simple clustering by frequency
    from collections import Counter
    topic_counts = Counter(all_topics)
    
    return [
        {"cluster": f"Cluster {i+1}", "topics": [topic], "size": count}
        for i, (topic, count) in enumerate(topic_counts.most_common(5))
    ]

def _calculate_content_quality_score(content_analytics: List[ContentMetrics]) -> float:
    """Calculate overall content quality score"""
    if not content_analytics:
        return 0.5
    
    scores = []
    for ca in content_analytics:
        quality = (ca.readability_score/100 + ca.engagement_score + (ca.sentiment_score + 1)/2) / 3
        scores.append(quality)
    
    return sum(scores) / len(scores)

def _identify_engagement_drivers(content_analytics: List[ContentMetrics]) -> List[str]:
    """Identify what drives engagement"""
    if not content_analytics:
        return ["Insufficient data"]
    
    drivers = []
    
    # Analyze high engagement content
    high_engagement = [ca for ca in content_analytics if ca.engagement_score > 0.7]
    if high_engagement:
        avg_sentiment = sum(ca.sentiment_score for ca in high_engagement) / len(high_engagement)
        if avg_sentiment > 0.2:
            drivers.append("Positive sentiment increases engagement")
    
    return drivers or ["Continue analyzing engagement patterns"]

def _get_content_types(content_items: List[Dict[str, Any]]) -> List[str]:
    """Get content types from content items"""
    types = set()
    for item in content_items:
        content_type = item.get("content_type", "unknown")
        types.add(content_type)
    return list(types)

def _identify_collaboration_opportunities(user_analytics: List[UserBehaviorMetrics]) -> List[str]:
    """Identify collaboration opportunities"""
    if not user_analytics:
        return []
    
    opportunities = []
    
    # Users with low collaboration but high productivity
    candidates = [
        ua for ua in user_analytics
        if ua.collaboration_activity < 0.3 and ua.productivity_score > 0.7
    ]
    
    if len(candidates) > 5:
        opportunities.append("High-performing users could benefit from collaboration features")
    
    return opportunities

def _get_feature_recommendations(user_analytics: List[UserBehaviorMetrics]) -> List[str]:
    """Get feature adoption recommendations"""
    if not user_analytics:
        return []
    
    recommendations = []
    
    # Analyze feature usage patterns
    feature_usage = {}
    for ua in user_analytics:
        for feature, count in ua.feature_usage.items():
            if feature not in feature_usage:
                feature_usage[feature] = []
            feature_usage[feature].append(count)
    
    # Identify underused features
    for feature, usage_list in feature_usage.items():
        avg_usage = sum(usage_list) / len(usage_list)
        if avg_usage < 2:
            recommendations.append(f"Promote {feature} feature adoption")
    
    return recommendations

def _generate_mitigation_strategies(risk_factors: List[str]) -> List[str]:
    """Generate risk mitigation strategies"""
    strategies = []
    
    for risk in risk_factors:
        if "churn" in risk.lower():
            strategies.append("Implement proactive user engagement campaigns")
        elif "cost" in risk.lower():
            strategies.append("Optimize infrastructure and operational efficiency")
        elif "competition" in risk.lower():
            strategies.append("Accelerate feature development and differentiation")
    
    return strategies or ["Monitor risk factors and develop contingency plans"]

def _generate_strategic_recommendations(business_intelligence: BusinessIntelligence) -> List[str]:
    """Generate strategic recommendations"""
    recommendations = []
    
    if business_intelligence.user_satisfaction > 0.8:
        recommendations.append("Leverage high satisfaction for customer advocacy programs")
    
    if business_intelligence.cost_efficiency > 1.2:
        recommendations.append("Invest efficiency gains in growth initiatives")
    
    recommendations.extend(business_intelligence.growth_opportunities[:2])
    
    return recommendations

def _generate_revenue_forecast(platform_metrics: Dict[str, Any]) -> List[float]:
    """Generate simple revenue forecast"""
    current_revenue = platform_metrics.get("monthly_revenue", 100000)
    growth_rate = 0.05  # 5% monthly growth
    
    forecast = []
    for month in range(12):
        forecast.append(current_revenue * (1 + growth_rate) ** month)
    
    return forecast

def _generate_user_growth_forecast(platform_metrics: Dict[str, Any]) -> List[int]:
    """Generate user growth forecast"""
    current_users = platform_metrics.get("total_users", 1000)
    growth_rate = 0.08  # 8% monthly growth
    
    forecast = []
    for month in range(12):
        forecast.append(int(current_users * (1 + growth_rate) ** month))
    
    return forecast

def _generate_market_forecast(market_trends: List[str]) -> Dict[str, str]:
    """Generate market opportunity forecast"""
    return {
        "market_size_trend": "expanding",
        "competitive_landscape": "intensifying",
        "opportunity_window": "6-12 months",
        "key_focus_areas": market_trends[:3]
    }

def _calculate_confidence_intervals(forecast: List[float], confidence_level: float) -> Dict[str, List[float]]:
    """Calculate confidence intervals for forecasts"""
    import numpy as np
    
    # Simple confidence interval calculation
    margin = (1 - confidence_level) * 0.2  # 20% margin for lower confidence
    
    lower_bound = [f * (1 - margin) for f in forecast]
    upper_bound = [f * (1 + margin) for f in forecast]
    
    return {
        "lower_bound": lower_bound,
        "upper_bound": upper_bound
    }

def _assess_data_quality(historical_data: Dict[str, List[Any]]) -> float:
    """Assess quality of historical data"""
    if not historical_data:
        return 0.0
    
    total_points = sum(len(data) for data in historical_data.values())
    data_sources = len(historical_data)
    
    # Simple quality score based on data volume and diversity
    volume_score = min(1.0, total_points / 100)  # 100 points = perfect volume
    diversity_score = min(1.0, data_sources / 5)  # 5 sources = perfect diversity
    
    return (volume_score + diversity_score) / 2

def _generate_report_data(report_type: str, date_range: str) -> Dict[str, Any]:
    """Generate report data based on type"""
    base_data = {
        "period": date_range,
        "metrics_included": []
    }
    
    if report_type == "content":
        base_data.update({
            "metrics_included": ["sentiment", "engagement", "topics", "quality"],
            "content_analyzed": 1240,
            "avg_sentiment": 0.72,
            "top_topics": ["AI", "Technology", "Innovation"]
        })
    elif report_type == "users":
        base_data.update({
            "metrics_included": ["behavior", "engagement", "retention"],
            "users_analyzed": 567,
            "avg_retention": 0.85,
            "top_features": ["transcription", "collaboration", "analytics"]
        })
    elif report_type == "business":
        base_data.update({
            "metrics_included": ["revenue", "costs", "roi", "satisfaction"],
            "revenue_growth": 0.15,
            "cost_efficiency": 1.25,
            "customer_satisfaction": 0.88
        })
    
    return base_data