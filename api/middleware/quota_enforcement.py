"""
Usage Quota Enforcement Middleware
Enforces subscription limits across all API endpoints
"""

import logging
from functools import wraps
from typing import Dict, Any, Optional, Callable
from fastapi import HTTPException, Request, Depends
from datetime import datetime

from api.auth_middleware import get_current_user
from services.subscription_service import SubscriptionService
from database.connection import get_db_session_factory

logger = logging.getLogger(__name__)

# Initialize subscription service
db_session_factory = get_db_session_factory()
subscription_service = SubscriptionService(db_session_factory)

class QuotaError(HTTPException):
    """Custom exception for quota-related errors"""
    def __init__(self, detail: str, usage_info: Dict[str, Any]):
        super().__init__(
            status_code=402,  # Payment Required
            detail=detail,
            headers={"X-Usage-Info": str(usage_info)}
        )
        self.usage_info = usage_info

def require_quota(usage_type: str, amount: int = 1, feature: Optional[str] = None):
    """
    Decorator to enforce usage quotas on API endpoints
    
    Args:
        usage_type: Type of usage (transcripts, minutes, storage, api_calls)
        amount: Amount of usage this endpoint consumes
        feature: Optional feature name to check access for
    
    Usage:
        @require_quota('transcripts', 1)
        async def create_transcription(...)
        
        @require_quota('api_calls', 1, 'advanced_analytics')
        async def advanced_analytics(...)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs (injected by get_current_user)
            current_user = None
            for key, value in kwargs.items():
                if key == 'current_user' and isinstance(value, dict):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required for quota checking"
                )
            
            user_id = current_user.get('id')
            if not user_id:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid user in authentication token"
                )
            
            # Check feature access if specified
            if feature:
                has_access = subscription_service.check_feature_access(user_id, feature)
                if not has_access:
                    user_plan = subscription_service.get_user_plan(user_id)
                    raise HTTPException(
                        status_code=403,
                        detail=f"Your {user_plan.name if user_plan else 'current'} plan does not include access to {feature}. Please upgrade your subscription.",
                        headers={"X-Required-Feature": feature}
                    )
            
            # Check usage limits
            allowed, error_message, usage_info = subscription_service.check_usage_limit(
                user_id, usage_type, amount
            )
            
            if not allowed:
                # Log quota violation
                logger.warning(
                    f"Quota exceeded for user {user_id}: {usage_type} "
                    f"(requested: {amount}, current: {usage_info.get('current', 0)}, "
                    f"limit: {usage_info.get('limit', 0)})"
                )
                
                # Create helpful error message with upgrade suggestion
                user_plan = subscription_service.get_user_plan(user_id)
                plan_name = user_plan.name if user_plan else "current plan"
                
                detail = (
                    f"You have exceeded your {usage_type} limit for the {plan_name}. "
                    f"Current usage: {usage_info.get('current', 0)}/"
                    f"{usage_info.get('limit', 0)}. "
                    f"Please upgrade your subscription to continue using this feature."
                )
                
                raise QuotaError(detail, usage_info)
            
            # Execute the original function
            try:
                result = await func(*args, **kwargs)
                
                # Track the successful usage after execution
                subscription_service.track_usage(
                    user_id=user_id,
                    usage_type=usage_type,
                    quantity=amount,
                    metadata={
                        'endpoint': func.__name__,
                        'timestamp': datetime.utcnow().isoformat(),
                        'method': 'API'
                    }
                )
                
                return result
                
            except Exception as e:
                # Don't track usage if the operation failed
                logger.error(f"Operation failed, not tracking usage: {str(e)}")
                raise
        
        return wrapper
    return decorator

async def check_quota_middleware(
    request: Request,
    user_id: int,
    usage_type: str,
    amount: int = 1
) -> Dict[str, Any]:
    """
    Middleware function for checking quotas
    Can be used in dependency injection
    """
    allowed, error_message, usage_info = subscription_service.check_usage_limit(
        user_id, usage_type, amount
    )
    
    if not allowed:
        raise QuotaError(error_message, usage_info)
    
    return usage_info

def get_user_usage_info(current_user: dict = Depends(get_current_user)):
    """
    Dependency to get current user's usage information
    """
    user_id = current_user.get('id')
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user")
    
    # Get usage for all types
    usage_types = ['transcripts', 'minutes', 'storage', 'api_calls']
    usage_summary = {}
    
    for usage_type in usage_types:
        allowed, _, usage_info = subscription_service.check_usage_limit(
            user_id, usage_type, 0  # Check current usage without consuming
        )
        usage_summary[usage_type] = usage_info
    
    # Get plan information
    plan = subscription_service.get_user_plan(user_id)
    
    return {
        'plan': {
            'name': plan.name if plan else 'Unknown',
            'tier': plan.tier.value if plan else 'unknown'
        },
        'usage': usage_summary
    }

def get_quota_limits(user_id: int) -> Dict[str, Any]:
    """
    Get all quota limits for a user
    """
    plan = subscription_service.get_user_plan(user_id)
    
    if not plan:
        return {}
    
    return {
        'transcripts_per_month': plan.max_transcripts_per_month,
        'minutes_per_month': plan.max_minutes_per_month,
        'storage_gb': plan.max_storage_gb,
        'api_calls_per_month': plan.max_api_calls_per_month,
        'features': {
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
    }

# Usage tracking helpers
def track_transcription_usage(user_id: int, duration_minutes: float):
    """Track transcription usage"""
    subscription_service.track_usage(
        user_id=user_id,
        usage_type='transcripts',
        quantity=1,
        metadata={'duration_minutes': duration_minutes}
    )
    
    subscription_service.track_usage(
        user_id=user_id,
        usage_type='minutes',
        quantity=duration_minutes,
        metadata={'type': 'transcription'}
    )

def track_tts_usage(user_id: int, character_count: int):
    """Track TTS usage"""
    subscription_service.track_usage(
        user_id=user_id,
        usage_type='api_calls',
        quantity=1,
        metadata={'type': 'tts', 'characters': character_count}
    )

def track_api_call(user_id: int, endpoint: str, metadata: Dict[str, Any] = None):
    """Track general API call"""
    subscription_service.track_usage(
        user_id=user_id,
        usage_type='api_calls',
        quantity=1,
        metadata={'endpoint': endpoint, **(metadata or {})}
    )