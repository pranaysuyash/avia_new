"""
Usage and Quota Management API Endpoints
Shows users their current usage, limits, and subscription information
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta

from api.auth_middleware import get_current_user
from api.middleware.quota_enforcement import get_user_usage_info, get_quota_limits
from services.subscription_service import SubscriptionService
from database.connection import get_db_session_factory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/usage")

# Initialize subscription service
db_session_factory = get_db_session_factory()
subscription_service = SubscriptionService(db_session_factory)

class UsageInfo(BaseModel):
    current: int
    limit: int
    remaining: int
    percentage_used: float

class PlanInfo(BaseModel):
    name: str
    tier: str
    is_trial: bool
    expires_at: Optional[str]

class UsageResponse(BaseModel):
    plan: PlanInfo
    usage: Dict[str, UsageInfo]
    features: Dict[str, bool]
    can_upgrade: bool

@router.get("/dashboard", response_model=UsageResponse)
async def get_usage_dashboard(
    current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive usage dashboard for current user
    
    Returns current usage, limits, plan info, and feature access
    """
    try:
        user_id = current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid user")
        
        # Get subscription and plan info
        subscription = subscription_service.get_user_subscription(user_id)
        plan = subscription_service.get_user_plan(user_id)
        
        if not plan:
            raise HTTPException(status_code=404, detail="No plan found for user")
        
        # Get usage information
        usage_types = ['transcripts', 'minutes', 'storage', 'api_calls']
        usage_summary = {}
        
        for usage_type in usage_types:
            allowed, error_msg, usage_info = subscription_service.check_usage_limit(
                user_id, usage_type, 0  # Check without consuming
            )
            
            current = usage_info.get('current', 0)
            limit = usage_info.get('limit', 0)
            
            # Handle unlimited plans
            if limit == -1 or limit == 'unlimited':
                percentage_used = 0.0
                remaining = -1
            else:
                remaining = max(0, limit - current)
                percentage_used = (current / limit * 100) if limit > 0 else 0.0
            
            usage_summary[usage_type] = UsageInfo(
                current=current,
                limit=limit if limit != -1 else -1,
                remaining=remaining,
                percentage_used=percentage_used
            )
        
        # Get feature access
        features = {
            'api_access': plan.has_api_access,
            'advanced_analytics': plan.has_advanced_analytics,
            'custom_models': plan.has_custom_models,
            'priority_support': plan.has_priority_support,
            'white_label': plan.has_white_label,
            'sso': plan.has_sso,
            'audit_logs': plan.has_audit_logs,
            'batch_processing': plan.has_batch_processing,
            'real_time_collab': plan.has_real_time_collab
        }
        
        # Plan information
        plan_info = PlanInfo(
            name=plan.name,
            tier=plan.tier.value,
            is_trial=subscription.status.value == 'trialing' if subscription else False,
            expires_at=subscription.end_date.isoformat() if subscription and subscription.end_date else None
        )
        
        return UsageResponse(
            plan=plan_info,
            usage=usage_summary,
            features=features,
            can_upgrade=plan.tier.value != 'enterprise'  # Can always upgrade unless already enterprise
        )
        
    except Exception as e:
        logger.error(f"Usage dashboard error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get usage dashboard: {str(e)}"
        )

@router.get("/limits")
async def get_usage_limits(
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed usage limits for current user's plan
    """
    try:
        user_id = current_user.get('id')
        limits = get_quota_limits(user_id)
        return limits
        
    except Exception as e:
        logger.error(f"Get limits error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get usage limits: {str(e)}"
        )

class UsageHistoryItem(BaseModel):
    date: str
    usage_type: str
    quantity: float
    endpoint: Optional[str]
    metadata: Optional[Dict[str, Any]]

@router.get("/history")
async def get_usage_history(
    usage_type: Optional[str] = None,
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """
    Get usage history for the current user
    
    Args:
        usage_type: Filter by specific usage type
        days: Number of days to look back (default 30)
    """
    try:
        user_id = current_user.get('id')
        
        # Get usage history from subscription service
        # This is a placeholder - you'd need to implement the actual history retrieval
        history = subscription_service.get_usage_history(
            user_id=user_id,
            usage_type=usage_type,
            days_back=days
        )
        
        return {
            "user_id": user_id,
            "period_days": days,
            "usage_type_filter": usage_type,
            "total_records": len(history),
            "history": history
        }
        
    except Exception as e:
        logger.error(f"Usage history error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get usage history: {str(e)}"
        )

@router.get("/alerts")
async def get_usage_alerts(
    current_user: dict = Depends(get_current_user)
):
    """
    Get usage alerts and warnings for the current user
    
    Returns alerts when users are approaching their limits
    """
    try:
        user_id = current_user.get('id')
        alerts = []
        
        # Check each usage type for approaching limits
        usage_types = ['transcripts', 'minutes', 'storage', 'api_calls']
        
        for usage_type in usage_types:
            allowed, error_msg, usage_info = subscription_service.check_usage_limit(
                user_id, usage_type, 0
            )
            
            current = usage_info.get('current', 0)
            limit = usage_info.get('limit', 0)
            
            # Skip unlimited plans
            if limit == -1:
                continue
            
            percentage_used = (current / limit * 100) if limit > 0 else 0
            
            # Create alerts for different thresholds
            if percentage_used >= 95:
                alerts.append({
                    "type": "critical",
                    "usage_type": usage_type,
                    "message": f"You have used {percentage_used:.1f}% of your {usage_type} quota",
                    "action": "upgrade_required",
                    "current": current,
                    "limit": limit
                })
            elif percentage_used >= 80:
                alerts.append({
                    "type": "warning",
                    "usage_type": usage_type,
                    "message": f"You have used {percentage_used:.1f}% of your {usage_type} quota",
                    "action": "consider_upgrade",
                    "current": current,
                    "limit": limit
                })
            elif percentage_used >= 50:
                alerts.append({
                    "type": "info",
                    "usage_type": usage_type,
                    "message": f"You have used {percentage_used:.1f}% of your {usage_type} quota",
                    "action": "monitor",
                    "current": current,
                    "limit": limit
                })
        
        return {
            "user_id": user_id,
            "alert_count": len(alerts),
            "alerts": alerts
        }
        
    except Exception as e:
        logger.error(f"Usage alerts error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get usage alerts: {str(e)}"
        )

@router.post("/reset")
async def reset_usage(
    usage_type: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Reset usage counters (admin only)
    
    Only available for admin users to reset quotas in emergency situations
    """
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        user_id = current_user.get('id')
        
        # This would need to be implemented in the subscription service
        success = subscription_service.reset_usage_counter(user_id, usage_type)
        
        if success:
            return {"message": f"Usage counter reset for {usage_type}"}
        else:
            raise HTTPException(status_code=400, detail="Failed to reset usage")
            
    except Exception as e:
        logger.error(f"Usage reset error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset usage: {str(e)}"
        )