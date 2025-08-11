"""
Recommendations API Endpoints
Task 204: AI-Powered Content Recommendations and Discovery
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging

from ...database import get_db
from ...auth.dependencies import get_current_user
from ...models.user import User
from ...ai_content_recommendations import (
    ContentRecommendationEngine,
    RecommendationType,
    UserProfile,
    Recommendation
)

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])
logger = logging.getLogger(__name__)

# Initialize recommendation engine
recommendation_engine = ContentRecommendationEngine()

# Pydantic models
class RecommendationRequest(BaseModel):
    strategy: str = Field(default="hybrid", description="Recommendation strategy")
    count: int = Field(default=10, ge=1, le=100)
    content_pool: Optional[List[str]] = Field(default=None, description="Content IDs to consider")
    filters: Optional[Dict[str, Any]] = Field(default=None)
    weights: Optional[Dict[str, float]] = Field(default=None, description="Weights for hybrid strategy")

class InteractionRecord(BaseModel):
    content_id: str
    interaction_type: str = Field(..., regex="^(view|like|share|download|bookmark)$")
    duration: Optional[int] = Field(default=None, ge=0)
    completion_rate: Optional[float] = Field(default=None, ge=0, le=1)
    rating: Optional[float] = Field(default=None, ge=1, le=5)
    context: Optional[Dict[str, Any]] = Field(default=None)

class UserPreferences(BaseModel):
    interests: List[str] = Field(default_factory=list)
    preferred_categories: List[str] = Field(default_factory=list)
    language_preferences: List[str] = Field(default_factory=list)
    content_types: List[str] = Field(default_factory=list)
    expertise_level: str = Field(default="intermediate")

class ContentFeedback(BaseModel):
    content_id: str
    feedback_type: str = Field(..., regex="^(helpful|not_helpful|inappropriate|outdated)$")
    comments: Optional[str] = Field(default=None, max_length=500)

class ABTestConfig(BaseModel):
    test_name: str
    variant_a: str
    variant_b: str
    test_size: int = Field(ge=10, le=10000)
    duration_days: int = Field(default=7, ge=1, le=30)

@router.get("/")
async def get_recommendations(
    strategy: str = Query("hybrid", description="Recommendation strategy"),
    count: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized content recommendations for the current user
    
    Strategies:
    - hybrid: Combination of multiple strategies
    - content_based: Based on content similarity
    - collaborative: Based on similar users
    - trending: Currently trending content
    - discovery: Explore new content
    - popular: Most popular content
    """
    try:
        # Get content pool (would fetch from database in production)
        content_pool = [f"content_{i}" for i in range(1000)]
        
        # Generate recommendations based on strategy
        if strategy == "hybrid":
            recommendations = recommendation_engine.recommend_hybrid(
                user_id=str(current_user.id),
                content_pool=content_pool,
                top_k=count
            )
        elif strategy == "content_based":
            recommendations = recommendation_engine.recommend_content_based(
                user_id=str(current_user.id),
                content_pool=content_pool,
                top_k=count
            )
        elif strategy == "collaborative":
            recommendations = recommendation_engine.recommend_collaborative(
                user_id=str(current_user.id),
                content_pool=content_pool,
                top_k=count
            )
        elif strategy == "trending":
            recommendations = recommendation_engine.recommend_trending(
                content_pool=content_pool,
                timeframe='daily',
                top_k=count
            )
        elif strategy == "discovery":
            recommendations = recommendation_engine.recommend_discovery(
                user_id=str(current_user.id),
                content_pool=content_pool,
                top_k=count
            )
        elif strategy == "popular":
            recommendations = recommendation_engine.recommend_popular(
                content_pool=content_pool,
                top_k=count
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid recommendation strategy")
        
        # Format response
        return {
            "status": "success",
            "data": {
                "user_id": str(current_user.id),
                "strategy": strategy,
                "recommendations": [
                    {
                        "content_id": rec.content_id,
                        "score": rec.score,
                        "reason": rec.reason,
                        "type": rec.recommendation_type.value,
                        "confidence": rec.confidence,
                        "explanation": rec.explanation
                    }
                    for rec in recommendations
                ],
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def get_custom_recommendations(
    request: RecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get custom recommendations with specific parameters"""
    try:
        # Use provided content pool or default
        content_pool = request.content_pool or [f"content_{i}" for i in range(1000)]
        
        # Generate recommendations
        if request.strategy == "hybrid" and request.weights:
            recommendations = recommendation_engine.recommend_hybrid(
                user_id=str(current_user.id),
                content_pool=content_pool,
                top_k=request.count,
                weights=request.weights
            )
        else:
            # Use GET endpoint logic for other strategies
            return await get_recommendations(
                strategy=request.strategy,
                count=request.count,
                current_user=current_user,
                db=db
            )
        
        return {
            "status": "success",
            "data": {
                "recommendations": [
                    {
                        "content_id": rec.content_id,
                        "score": rec.score,
                        "reason": rec.reason,
                        "type": rec.recommendation_type.value,
                        "confidence": rec.confidence
                    }
                    for rec in recommendations
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating custom recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/interaction")
async def record_interaction(
    interaction: InteractionRecord,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record user interaction with content"""
    try:
        recommendation_engine.record_interaction(
            user_id=str(current_user.id),
            content_id=interaction.content_id,
            interaction_type=interaction.interaction_type,
            duration=interaction.duration,
            completion_rate=interaction.completion_rate,
            rating=interaction.rating,
            context=interaction.context or {}
        )
        
        return {
            "status": "success",
            "message": "Interaction recorded successfully"
        }
        
    except Exception as e:
        logger.error(f"Error recording interaction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile")
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user recommendation profile"""
    try:
        profile = recommendation_engine.get_user_profile(str(current_user.id))
        
        return {
            "status": "success",
            "data": {
                "user_id": profile.user_id,
                "interests": profile.interests,
                "preferred_categories": profile.preferred_categories,
                "viewing_history": profile.viewing_history[:20],  # Last 20 items
                "content_preferences": profile.content_preferences,
                "language_preferences": profile.language_preferences,
                "expertise_level": profile.expertise_level,
                "active_hours": list(set(profile.active_times))[:24]  # Unique hours
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/profile/preferences")
async def update_user_preferences(
    preferences: UserPreferences,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user recommendation preferences"""
    try:
        # In production, this would update user preferences in database
        # For now, return success
        return {
            "status": "success",
            "message": "Preferences updated successfully",
            "data": preferences.dict()
        }
        
    except Exception as e:
        logger.error(f"Error updating preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/similar/{content_id}")
async def get_similar_content(
    content_id: str,
    count: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get content similar to a specific item"""
    try:
        # Get candidate pool
        content_pool = [f"content_{i}" for i in range(1000)]
        
        # Calculate similarities
        similar_items = recommendation_engine.calculate_content_similarity(
            content_id=content_id,
            candidate_ids=content_pool,
            top_k=count
        )
        
        return {
            "status": "success",
            "data": {
                "base_content": content_id,
                "similar_content": [
                    {
                        "content_id": item[0],
                        "similarity_score": item[1]
                    }
                    for item in similar_items
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error finding similar content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trending")
async def get_trending_content(
    timeframe: str = Query("daily", regex="^(hourly|daily|weekly)$"),
    category: Optional[str] = Query(None),
    count: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get trending content"""
    try:
        # Update trending scores
        recommendation_engine.update_trending_content(timeframe)
        
        # Get content pool
        content_pool = [f"content_{i}" for i in range(1000)]
        
        # Get trending recommendations
        recommendations = recommendation_engine.recommend_trending(
            content_pool=content_pool,
            timeframe=timeframe,
            top_k=count
        )
        
        return {
            "status": "success",
            "data": {
                "timeframe": timeframe,
                "category": category,
                "trending": [
                    {
                        "content_id": rec.content_id,
                        "trend_score": rec.score,
                        "velocity": rec.explanation.get('velocity', 0)
                    }
                    for rec in recommendations
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting trending content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback")
async def submit_feedback(
    feedback: ContentFeedback,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit feedback on recommended content"""
    try:
        # Process feedback (would store in database)
        # Negative feedback could be used to improve recommendations
        
        if feedback.feedback_type in ["not_helpful", "inappropriate"]:
            # Record as negative interaction
            recommendation_engine.record_interaction(
                user_id=str(current_user.id),
                content_id=feedback.content_id,
                interaction_type="dislike",
                rating=1.0
            )
        
        return {
            "status": "success",
            "message": "Feedback recorded successfully"
        }
        
    except Exception as e:
        logger.error(f"Error recording feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ab-test")
async def create_ab_test(
    config: ABTestConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create an A/B test for recommendation strategies"""
    try:
        # In production, this would set up an A/B test
        # For now, return mock response
        return {
            "status": "success",
            "data": {
                "test_id": f"test_{datetime.utcnow().timestamp()}",
                "test_name": config.test_name,
                "variant_a": config.variant_a,
                "variant_b": config.variant_b,
                "test_size": config.test_size,
                "start_date": datetime.utcnow().isoformat(),
                "end_date": (datetime.utcnow() + timedelta(days=config.duration_days)).isoformat(),
                "status": "active"
            }
        }
        
    except Exception as e:
        logger.error(f"Error creating A/B test: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ab-test/{test_id}/results")
async def get_ab_test_results(
    test_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get A/B test results"""
    try:
        # Mock A/B test results
        return {
            "status": "success",
            "data": {
                "test_id": test_id,
                "variant_a": {
                    "users": 500,
                    "ctr": 0.15,
                    "engagement_rate": 0.72,
                    "avg_session_duration": 1820,
                    "conversion_rate": 0.08
                },
                "variant_b": {
                    "users": 500,
                    "ctr": 0.18,
                    "engagement_rate": 0.68,
                    "avg_session_duration": 1650,
                    "conversion_rate": 0.10
                },
                "statistical_significance": {
                    "ctr": {"p_value": 0.03, "significant": True},
                    "engagement": {"p_value": 0.12, "significant": False},
                    "conversion": {"p_value": 0.04, "significant": True}
                },
                "winner": "variant_b",
                "confidence": 0.95
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting A/B test results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics")
async def get_recommendation_analytics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recommendation system analytics"""
    try:
        # Default date range
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        # Mock analytics data
        return {
            "status": "success",
            "data": {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "metrics": {
                    "total_recommendations": 15234,
                    "unique_users": 1823,
                    "avg_recommendations_per_user": 8.4,
                    "click_through_rate": 0.16,
                    "engagement_rate": 0.71,
                    "conversion_rate": 0.09
                },
                "strategy_performance": {
                    "hybrid": {"usage": 0.45, "ctr": 0.18, "satisfaction": 4.2},
                    "content_based": {"usage": 0.25, "ctr": 0.15, "satisfaction": 4.0},
                    "collaborative": {"usage": 0.15, "ctr": 0.17, "satisfaction": 4.1},
                    "trending": {"usage": 0.10, "ctr": 0.14, "satisfaction": 3.8},
                    "discovery": {"usage": 0.05, "ctr": 0.12, "satisfaction": 3.9}
                },
                "top_performing_content": [
                    {"content_id": "content_42", "impressions": 523, "clicks": 98, "ctr": 0.19},
                    {"content_id": "content_17", "impressions": 487, "clicks": 85, "ctr": 0.17},
                    {"content_id": "content_93", "impressions": 456, "clicks": 78, "ctr": 0.17}
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cache")
async def clear_recommendation_cache(
    user_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear recommendation cache"""
    try:
        # Clear cache for specific user or all users
        target_user = user_id or str(current_user.id)
        
        # In production, this would clear actual cache
        return {
            "status": "success",
            "message": f"Cache cleared for user {target_user}"
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))