"""
Intelligence Systems API Endpoints
Endpoints for Content, Media Asset, and Business Intelligence
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import json

from api.database import get_db
from api.dependencies import get_current_user
from api.cache.redis_cache import redis_cache
from database.models import User

# Import intelligence systems
from advanced_content_intelligence import (
    AdvancedContentIntelligence,
    ContentType,
    ContentCategory
)
from media_asset_intelligence import (
    MediaAssetIntelligence,
    MediaType
)
from business_intelligence_roi import (
    BusinessIntelligenceSystem,
    MetricType,
    PredictionType
)

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


# Request/Response Models

class ContentAnalysisRequest(BaseModel):
    content: str
    content_id: str
    title: Optional[str] = ""
    content_type: str = "transcript"
    deep_analysis: bool = True


class ContentAnalysisResponse(BaseModel):
    content_id: str
    title: str
    category: Optional[str]
    tags: List[str]
    keywords: List[Dict[str, float]]
    sentiment: Dict[str, float]
    quality_score: float
    readability_score: float
    engagement_prediction: float
    virality_score: float
    target_audience: List[str]
    summary: Optional[str]


class MediaAnalysisRequest(BaseModel):
    asset_id: str
    media_type: str = "video"
    deep_analysis: bool = True
    extract_highlights: bool = True


class MediaAnalysisResponse(BaseModel):
    asset_id: str
    media_type: str
    duration: Optional[float]
    quality_score: float
    scenes_count: int
    highlights_count: int
    unique_faces: int
    detected_objects: Dict[str, int]
    detected_brands: List[str]
    viral_potential: float
    hero_thumbnail: Optional[str]
    suggested_edits: List[Dict[str, Any]]
    auto_chapters: List[Dict[str, Any]]


class ROICalculationRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    investment_breakdown: Optional[Dict[str, float]] = None


class ROICalculationResponse(BaseModel):
    investment: float
    revenue: float
    profit: float
    roi_percentage: float
    payback_period: float
    break_even_date: Optional[datetime]
    ltv_cac_ratio: float


class RevenueForecastRequest(BaseModel):
    horizon_months: int = 12
    include_seasonality: bool = True
    scenario: str = "most_likely"  # best_case, worst_case, most_likely


class ChurnPredictionRequest(BaseModel):
    user_ids: Optional[List[int]] = None
    threshold: float = 0.5


class BusinessMetricsRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    metrics: Optional[List[str]] = None


# Content Intelligence Endpoints

@router.post("/content/analyze", response_model=ContentAnalysisResponse)
async def analyze_content(
    request: ContentAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyze content using advanced NLP and ML models
    """
    try:
        # Check cache first
        cache_key = f"content_analysis:{request.content_id}"
        cached_result = await redis_cache.get(cache_key)
        if cached_result:
            return JSONResponse(content=json.loads(cached_result))
        
        # Initialize content intelligence
        content_intel = AdvancedContentIntelligence(db)
        
        # Perform analysis
        content_type = ContentType[request.content_type.upper()]
        result = await content_intel.analyze_content(
            content=request.content,
            content_id=request.content_id,
            title=request.title,
            content_type=content_type,
            deep_analysis=request.deep_analysis
        )
        
        # Generate summary if deep analysis
        summary = None
        if request.deep_analysis:
            summary = await content_intel.generate_summary(
                request.content,
                max_length=150,
                style="bullets"
            )
        
        response = ContentAnalysisResponse(
            content_id=result.content_id,
            title=result.title,
            category=result.category.value if result.category else None,
            tags=result.tags,
            keywords=[{"keyword": k, "score": s} for k, s in result.keywords],
            sentiment=result.sentiment,
            quality_score=result.quality_score,
            readability_score=result.readability_score,
            engagement_prediction=result.predicted_engagement,
            virality_score=result.virality_score,
            target_audience=result.target_audience,
            summary=summary
        )
        
        # Cache result
        await redis_cache.set(
            cache_key,
            json.dumps(response.dict()),
            ttl=3600  # 1 hour
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/content/extract-insights")
async def extract_content_insights(
    content_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Extract key insights from analyzed content
    """
    try:
        content_intel = AdvancedContentIntelligence(db)
        
        # Get content from cache or database
        cache_key = f"content_analysis:{content_id}"
        cached_data = await redis_cache.get(cache_key)
        
        if not cached_data:
            raise HTTPException(status_code=404, detail="Content analysis not found")
        
        metadata = json.loads(cached_data)
        
        # Extract insights
        # This would normally use the stored content
        insights = {
            "key_points": metadata.get("keywords", [])[:5],
            "sentiment_summary": metadata.get("sentiment", {}),
            "recommendations": metadata.get("recommended_next", []),
            "engagement_factors": {
                "quality": metadata.get("quality_score", 0),
                "readability": metadata.get("readability_score", 0),
                "virality": metadata.get("virality_score", 0)
            }
        }
        
        return insights
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/content/cluster")
async def cluster_content(
    content_ids: List[str],
    num_clusters: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cluster multiple content pieces into groups
    """
    try:
        content_intel = AdvancedContentIntelligence(db)
        
        clusters = await content_intel.cluster_content(
            content_ids=content_ids,
            num_clusters=num_clusters
        )
        
        return {"clusters": clusters}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Media Asset Intelligence Endpoints

@router.post("/media/analyze", response_model=MediaAnalysisResponse)
async def analyze_media_asset(
    file: UploadFile = File(...),
    asset_id: str = Field(...),
    media_type: str = "video",
    deep_analysis: bool = True,
    extract_highlights: bool = True,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyze media asset (video/image) for intelligence extraction
    """
    try:
        # Save uploaded file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Initialize media intelligence
        media_intel = MediaAssetIntelligence(db)
        
        # Perform analysis
        media_type_enum = MediaType[media_type.upper()]
        result = await media_intel.analyze_media_asset(
            file_path=tmp_path,
            asset_id=asset_id,
            media_type=media_type_enum,
            deep_analysis=deep_analysis,
            extract_highlights=extract_highlights
        )
        
        # Clean up temp file
        background_tasks.add_task(os.unlink, tmp_path)
        
        response = MediaAnalysisResponse(
            asset_id=result.asset_id,
            media_type=result.media_type.value,
            duration=result.duration,
            quality_score=result.quality_score,
            scenes_count=len(result.scenes),
            highlights_count=len(result.highlights),
            unique_faces=result.unique_faces,
            detected_objects=result.detected_objects,
            detected_brands=result.detected_brands,
            viral_potential=result.viral_potential,
            hero_thumbnail=result.hero_thumbnail,
            suggested_edits=result.suggested_edits,
            auto_chapters=result.auto_chapters
        )
        
        # Cache result
        cache_key = f"media_analysis:{asset_id}"
        await redis_cache.set(
            cache_key,
            json.dumps(response.dict(), default=str),
            ttl=3600
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/media/{asset_id}/highlights")
async def get_media_highlights(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get highlights for a media asset
    """
    try:
        # Get from cache
        cache_key = f"media_analysis:{asset_id}"
        cached_data = await redis_cache.get(cache_key)
        
        if not cached_data:
            raise HTTPException(status_code=404, detail="Media analysis not found")
        
        data = json.loads(cached_data)
        
        # Extract highlights info
        highlights = {
            "count": data.get("highlights_count", 0),
            "viral_potential": data.get("viral_potential", 0),
            "hero_thumbnail": data.get("hero_thumbnail"),
            "suggested_clips": data.get("suggested_edits", [])
        }
        
        return highlights
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/media/generate-summary")
async def generate_video_summary(
    asset_id: str,
    duration: int = 60,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a video summary/trailer
    """
    try:
        media_intel = MediaAssetIntelligence(db)
        
        # Get original video path from database
        # This is placeholder - would get from actual storage
        video_path = f"/storage/videos/{asset_id}.mp4"
        output_path = f"/storage/summaries/{asset_id}_summary.mp4"
        
        success = await media_intel.generate_video_summary(
            video_path=video_path,
            output_path=output_path,
            duration=duration
        )
        
        if success:
            return {
                "status": "success",
                "summary_path": output_path,
                "duration": duration
            }
        else:
            raise HTTPException(status_code=500, detail="Summary generation failed")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Business Intelligence Endpoints

@router.post("/business/roi", response_model=ROICalculationResponse)
async def calculate_roi(
    request: ROICalculationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate ROI metrics for a given period
    """
    try:
        # Check admin permission
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        business_intel = BusinessIntelligenceSystem(db)
        
        result = await business_intel.calculate_roi(
            start_date=request.start_date,
            end_date=request.end_date,
            investment_breakdown=request.investment_breakdown
        )
        
        return ROICalculationResponse(
            investment=result.investment,
            revenue=result.revenue,
            profit=result.profit,
            roi_percentage=result.roi_percentage,
            payback_period=result.payback_period,
            break_even_date=result.break_even_date,
            ltv_cac_ratio=result.ltv_cac_ratio
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/business/forecast/revenue")
async def forecast_revenue(
    request: RevenueForecastRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Forecast future revenue with ML models
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        business_intel = BusinessIntelligenceSystem(db)
        
        forecasts = await business_intel.predict_revenue(
            horizon_months=request.horizon_months,
            include_seasonality=request.include_seasonality,
            scenario=request.scenario
        )
        
        # Convert to JSON-serializable format
        forecast_data = [
            {
                "date": f.forecast_date.isoformat(),
                "predicted_revenue": f.predicted_revenue,
                "confidence_lower": f.confidence_interval[0],
                "confidence_upper": f.confidence_interval[1],
                "growth_rate": f.growth_rate,
                "seasonality_factor": f.seasonality_factor,
                "best_case": f.best_case,
                "worst_case": f.worst_case,
                "most_likely": f.most_likely
            }
            for f in forecasts
        ]
        
        return {"forecasts": forecast_data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/business/predict/churn")
async def predict_churn(
    request: ChurnPredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Predict user churn probability
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        business_intel = BusinessIntelligenceSystem(db)
        
        predictions = await business_intel.predict_churn(
            user_ids=request.user_ids,
            threshold=request.threshold
        )
        
        # Convert to JSON-serializable format
        prediction_data = [
            {
                "user_id": p.user_id,
                "churn_probability": p.churn_probability,
                "risk_level": p.risk_level,
                "churn_reasons": p.churn_reasons,
                "retention_actions": p.retention_actions,
                "expected_churn_date": p.expected_churn_date.isoformat() if p.expected_churn_date else None,
                "preventable": p.preventable,
                "recovery_probability": p.recovery_probability
            }
            for p in predictions
        ]
        
        # Summary statistics
        summary = {
            "total_users": len(predictions),
            "high_risk": len([p for p in predictions if p.risk_level == "high"]),
            "medium_risk": len([p for p in predictions if p.risk_level == "medium"]),
            "low_risk": len([p for p in predictions if p.risk_level == "low"]),
            "average_churn_probability": sum(p.churn_probability for p in predictions) / len(predictions) if predictions else 0
        }
        
        return {
            "predictions": prediction_data,
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/business/metrics")
async def get_business_metrics(
    request: BusinessMetricsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive business metrics
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        business_intel = BusinessIntelligenceSystem(db)
        
        metrics = await business_intel.get_business_metrics(
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        return {
            "period": {
                "start": request.start_date.isoformat(),
                "end": request.end_date.isoformat()
            },
            "financial": {
                "total_revenue": metrics.total_revenue,
                "recurring_revenue": metrics.recurring_revenue,
                "gross_margin": metrics.gross_margin,
                "net_margin": metrics.net_margin
            },
            "users": {
                "total": metrics.total_users,
                "active": metrics.active_users,
                "new": metrics.new_users,
                "churned": metrics.churned_users
            },
            "engagement": {
                "avg_session_duration": metrics.avg_session_duration,
                "sessions_per_user": metrics.sessions_per_user,
                "feature_adoption_rate": metrics.feature_adoption_rate
            },
            "growth": {
                "growth_rate": metrics.growth_rate,
                "viral_coefficient": metrics.viral_coefficient,
                "retention_rate": metrics.retention_rate
            },
            "efficiency": {
                "burn_rate": metrics.burn_rate,
                "runway_months": metrics.runway_months,
                "unit_economics": metrics.unit_economics
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/business/dashboard")
async def get_executive_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get executive dashboard with key metrics and insights
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Check cache first
        cache_key = "executive_dashboard"
        cached_data = await redis_cache.get(cache_key)
        if cached_data:
            return JSONResponse(content=json.loads(cached_data))
        
        business_intel = BusinessIntelligenceSystem(db)
        
        dashboard = await business_intel.generate_executive_dashboard()
        
        # Cache for 15 minutes
        await redis_cache.set(
            cache_key,
            json.dumps(dashboard, default=str),
            ttl=900
        )
        
        return dashboard
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/business/opportunities")
async def get_growth_opportunities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Identify business growth opportunities
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        business_intel = BusinessIntelligenceSystem(db)
        
        opportunities = await business_intel.identify_growth_opportunities()
        
        return opportunities
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/business/ltv/{user_id}")
async def calculate_user_ltv(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate lifetime value for a specific user
    """
    try:
        if not current_user.is_admin and current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        business_intel = BusinessIntelligenceSystem(db)
        
        ltv = await business_intel.calculate_ltv(user_id=user_id)
        
        return {
            "user_id": user_id,
            "lifetime_value": ltv,
            "currency": "USD"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Composite Intelligence Endpoints

@router.post("/analyze/complete")
async def complete_analysis(
    content: str,
    title: str,
    file: Optional[UploadFile] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform complete analysis combining content and media intelligence
    """
    try:
        results = {}
        
        # Content analysis
        content_intel = AdvancedContentIntelligence(db)
        content_result = await content_intel.analyze_content(
            content=content,
            content_id=f"complete_{current_user.id}_{datetime.now().timestamp()}",
            title=title,
            deep_analysis=True
        )
        
        results["content"] = {
            "category": content_result.category.value if content_result.category else None,
            "sentiment": content_result.sentiment,
            "quality_score": content_result.quality_score,
            "engagement_prediction": content_result.predicted_engagement,
            "virality_score": content_result.virality_score,
            "tags": content_result.tags[:10]
        }
        
        # Media analysis if file provided
        if file:
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                file_content = await file.read()
                tmp_file.write(file_content)
                tmp_path = tmp_file.name
            
            media_intel = MediaAssetIntelligence(db)
            media_result = await media_intel.analyze_media_asset(
                file_path=tmp_path,
                asset_id=f"media_{current_user.id}_{datetime.now().timestamp()}",
                media_type=MediaType.VIDEO if file.filename.endswith(('.mp4', '.avi', '.mov')) else MediaType.IMAGE
            )
            
            results["media"] = {
                "quality_score": media_result.quality_score,
                "viral_potential": media_result.viral_potential,
                "scenes": len(media_result.scenes),
                "highlights": len(media_result.highlights),
                "detected_objects": list(media_result.detected_objects.keys())[:10]
            }
            
            # Clean up
            background_tasks.add_task(os.unlink, tmp_path)
        
        # Combined insights
        results["insights"] = {
            "overall_quality": (results["content"]["quality_score"] + 
                               results.get("media", {}).get("quality_score", results["content"]["quality_score"])) / 2,
            "viral_potential": max(
                results["content"]["virality_score"],
                results.get("media", {}).get("viral_potential", 0)
            ),
            "recommended_actions": []
        }
        
        # Generate recommendations
        if results["insights"]["overall_quality"] < 0.5:
            results["insights"]["recommended_actions"].append("Improve content quality")
        if results["insights"]["viral_potential"] > 0.7:
            results["insights"]["recommended_actions"].append("Optimize for social sharing")
        if results["content"]["sentiment"].get("negative", 0) > 0.5:
            results["insights"]["recommended_actions"].append("Consider tone adjustment")
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@router.get("/health")
async def intelligence_health_check():
    """
    Check health of intelligence systems
    """
    return {
        "status": "healthy",
        "systems": {
            "content_intelligence": "operational",
            "media_intelligence": "operational",
            "business_intelligence": "operational"
        },
        "timestamp": datetime.now().isoformat()
    }