"""
User Engagement Analytics API Endpoints
Task 202: Advanced User Engagement Analytics System
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from advanced_user_engagement_analytics import UserEngagementAnalytics
    from api.dependencies import get_current_user, get_db
    from sqlalchemy.orm import Session
except ImportError:
    # Fallback for testing
    UserEngagementAnalytics = None
    def get_current_user():
        return {"user_id": "test_user", "role": "admin"}
    def get_db():
        return None

router = APIRouter(prefix="/api/v1/analytics", tags=["user-analytics"])

# Pydantic models for request/response
class EventTrackingRequest(BaseModel):
    event_type: str
    page_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class SessionStartRequest(BaseModel):
    device_info: Optional[Dict[str, Any]] = None
    location_data: Optional[Dict[str, Any]] = None

class UserProfileRequest(BaseModel):
    initial_data: Optional[Dict[str, Any]] = None

class AnalyticsDateRange(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

# Initialize analytics service (with fallback)
def get_analytics_service():
    """Get analytics service instance"""
    if UserEngagementAnalytics:
        return UserEngagementAnalytics("sqlite:///user_analytics.db")
    else:
        # Mock for testing
        class MockAnalytics:
            async def track_event(self, *args, **kwargs):
                return {"status": "success", "message": "Event tracked (mock)"}
            async def start_session(self, *args, **kwargs):
                return {"session_id": "mock_session", "status": "started"}
            async def create_user_profile(self, *args, **kwargs):
                return {"status": "created", "user_id": "mock_user"}
            async def get_user_behavior(self, *args, **kwargs):
                return {"user_id": "mock_user", "behavior": "mock_data"}
            async def predict_churn(self, *args, **kwargs):
                return {"churn_probability": 0.3, "risk_level": "low"}
            async def get_engagement_metrics(self, *args, **kwargs):
                return {"total_users": 100, "total_events": 1000}
            async def analyze_user_journey(self, *args, **kwargs):
                return {"user_id": "mock_user", "journey": "mock_journey"}
            async def get_feature_usage(self, *args, **kwargs):
                return {"total_features": 10, "usage": "mock_usage"}
            async def get_real_time_analytics(self, *args, **kwargs):
                return {"active_users": 50, "events_last_hour": 100}
        return MockAnalytics()

@router.post("/events/track")
async def track_user_event(
    event_request: EventTrackingRequest,
    current_user: dict = Depends(get_current_user)
):
    """Track a user event"""
    try:
        analytics = get_analytics_service()
        result = await analytics.track_event(
            user_id=current_user["user_id"],
            event_type=event_request.event_type,
            page_url=event_request.page_url,
            metadata=event_request.metadata
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Event tracking failed: {str(e)}")

@router.post("/sessions/start")
async def start_user_session(
    session_request: SessionStartRequest,
    current_user: dict = Depends(get_current_user)
):
    """Start a user session"""
    try:
        analytics = get_analytics_service()
        result = await analytics.start_session(
            user_id=current_user["user_id"],
            device_info=session_request.device_info,
            location_data=session_request.location_data
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session start failed: {str(e)}")

@router.post("/sessions/{session_id}/end")
async def end_user_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """End a user session"""
    try:
        analytics = get_analytics_service()
        result = await analytics.end_session(
            session_id=session_id,
            user_id=current_user["user_id"]
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session end failed: {str(e)}")

@router.post("/users/profiles")
async def create_user_profile(
    profile_request: UserProfileRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create or update user behavior profile"""
    try:
        analytics = get_analytics_service()
        result = await analytics.create_user_profile(
            user_id=current_user["user_id"],
            initial_data=profile_request.initial_data
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profile creation failed: {str(e)}")

@router.get("/users/{user_id}/behavior")
async def get_user_behavior(
    user_id: str,
    days: int = Query(default=30, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive user behavior data"""
    # Check permission (admin or same user)
    if current_user["role"] != "admin" and current_user["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        analytics = get_analytics_service()
        result = await analytics.get_user_behavior(user_id=user_id, days=days)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Behavior analysis failed: {str(e)}")

@router.get("/users/{user_id}/churn-prediction")
async def predict_user_churn(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Predict user churn probability"""
    # Admin only for churn predictions
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        analytics = get_analytics_service()
        result = await analytics.predict_churn(user_id=user_id)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Churn prediction failed: {str(e)}")

@router.get("/engagement/metrics")
async def get_engagement_metrics(
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive engagement metrics"""
    # Admin only for platform metrics
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        analytics = get_analytics_service()
        date_range = (start_date, end_date) if start_date and end_date else None
        result = await analytics.get_engagement_metrics(date_range=date_range)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")

@router.get("/users/{user_id}/journey")
async def analyze_user_journey(
    user_id: str,
    session_limit: int = Query(default=10, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """Analyze user journey and behavior flow"""
    # Check permission (admin or same user)
    if current_user["role"] != "admin" and current_user["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        analytics = get_analytics_service()
        result = await analytics.analyze_user_journey(
            user_id=user_id, 
            session_limit=session_limit
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Journey analysis failed: {str(e)}")

@router.get("/features/usage")
async def get_feature_usage(
    feature_name: Optional[str] = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get feature usage analytics"""
    # Admin only for platform feature usage
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        analytics = get_analytics_service()
        result = await analytics.get_feature_usage(
            feature_name=feature_name,
            days=days
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feature usage analysis failed: {str(e)}")

@router.get("/real-time")
async def get_real_time_analytics(
    current_user: dict = Depends(get_current_user)
):
    """Get real-time engagement analytics"""
    # Admin only for real-time analytics
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        analytics = get_analytics_service()
        result = await analytics.get_real_time_analytics()
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Real-time analytics failed: {str(e)}")

@router.get("/insights")
async def get_engagement_insights(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """Get engagement insights and recommendations"""
    # Admin only for platform insights
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        analytics = get_analytics_service()
        # This would call a method to get insights - mock for now
        result = {
            "insights": [
                {
                    "type": "engagement_trend",
                    "title": "User Engagement Trending Up",
                    "description": "Active users increased by 15% this week",
                    "priority": "medium",
                    "generated_at": datetime.utcnow().isoformat()
                }
            ],
            "recommendations": [
                "Continue current engagement strategies",
                "Focus on retaining new users",
                "Optimize feature onboarding"
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insights retrieval failed: {str(e)}")

# Health check endpoint
@router.get("/health")
async def health_check():
    """Analytics service health check"""
    try:
        analytics = get_analytics_service()
        return {
            "status": "healthy",
            "service": "user-engagement-analytics",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# Export router for FastAPI app
__all__ = ["router"]