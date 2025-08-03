#!/usr/bin/env python3
"""
Subscription API Endpoints
Handles pricing, subscriptions, and payment operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import logging

from database.models import User
from database.subscription_models import PricingTier, BillingInterval
from services.subscription_service import SubscriptionService
from services.stripe_service import StripeService
from api.auth_routes_enhanced import get_current_user
from database.connection import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])

# Initialize services
subscription_service = SubscriptionService(get_db)
stripe_service = StripeService(get_db)

# Request/Response Models

class CreateSubscriptionRequest(BaseModel):
    plan_tier: PricingTier
    billing_interval: BillingInterval
    payment_method_id: Optional[str] = None
    coupon_code: Optional[str] = None

class UpdateSubscriptionRequest(BaseModel):
    plan_tier: Optional[PricingTier] = None
    billing_interval: Optional[BillingInterval] = None
    cancel_at_period_end: Optional[bool] = None

class CheckoutSessionRequest(BaseModel):
    plan_tier: PricingTier
    billing_interval: BillingInterval
    success_url: str
    cancel_url: str

class AddPaymentMethodRequest(BaseModel):
    payment_method_id: str
    set_as_default: bool = False

class CheckUsageRequest(BaseModel):
    usage_type: str = Field(..., description="transcripts, minutes, storage, or api_calls")
    amount: int = Field(1, description="Amount to check")

class TrackUsageRequest(BaseModel):
    usage_type: str
    quantity: float
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    description: Optional[str] = None

# Endpoints

@router.get("/plans", response_model=List[Dict[str, Any]])
async def get_pricing_plans():
    """Get all available pricing plans"""
    plans = subscription_service.get_available_plans()
    return plans

@router.get("/current", response_model=Dict[str, Any])
async def get_current_subscription(current_user: User = Depends(get_current_user)):
    """Get current user's subscription details"""
    subscription = subscription_service.get_user_subscription(current_user.id)
    
    if not subscription:
        # Return free plan info
        plan = subscription_service.get_user_plan(current_user.id)
        return {
            'status': 'none',
            'plan': {
                'tier': plan.tier.value,
                'name': plan.name,
                'description': plan.description
            }
        }
    
    return {
        'status': subscription.status.value,
        'plan': {
            'tier': subscription.plan.tier.value,
            'name': subscription.plan.name,
            'description': subscription.plan.description
        },
        'billing_interval': subscription.billing_interval.value,
        'current_period_end': subscription.current_period_end.isoformat(),
        'canceled_at': subscription.canceled_at.isoformat() if subscription.canceled_at else None,
        'trial_end': subscription.trial_end.isoformat() if subscription.trial_end else None
    }

@router.post("/create", response_model=Dict[str, Any])
async def create_subscription(
    request: CreateSubscriptionRequest,
    current_user: User = Depends(get_current_user)
):
    """Create new subscription"""
    # Check for trial eligibility (first subscription gets 14 days trial)
    from database.subscription_models import Subscription
    db = next(get_db())
    has_previous_subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).count() > 0
    
    trial_days = 0 if has_previous_subscription else 14
    
    success, message, data = stripe_service.create_subscription(
        user_id=current_user.id,
        plan_tier=request.plan_tier,
        billing_interval=request.billing_interval,
        payment_method_id=request.payment_method_id,
        coupon_code=request.coupon_code,
        trial_days=trial_days
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {
        'message': message,
        'subscription': data
    }

@router.put("/update", response_model=Dict[str, Any])
async def update_subscription(
    request: UpdateSubscriptionRequest,
    current_user: User = Depends(get_current_user)
):
    """Update existing subscription"""
    subscription = subscription_service.get_user_subscription(current_user.id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    success, message, data = stripe_service.update_subscription(
        subscription_id=subscription.id,
        new_plan_tier=request.plan_tier,
        new_billing_interval=request.billing_interval,
        cancel_at_period_end=request.cancel_at_period_end
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {
        'message': message,
        'subscription': data
    }

@router.post("/cancel", response_model=Dict[str, Any])
async def cancel_subscription(
    immediately: bool = False,
    current_user: User = Depends(get_current_user)
):
    """Cancel subscription"""
    subscription = subscription_service.get_user_subscription(current_user.id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    success, message, data = stripe_service.cancel_subscription(
        subscription_id=subscription.id,
        immediately=immediately
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {
        'message': message,
        'subscription': data
    }

@router.post("/checkout-session", response_model=Dict[str, Any])
async def create_checkout_session(
    request: CheckoutSessionRequest,
    current_user: User = Depends(get_current_user)
):
    """Create Stripe checkout session"""
    # Check for trial eligibility
    from database.subscription_models import Subscription
    db = next(get_db())
    has_previous_subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).count() > 0
    
    trial_days = 0 if has_previous_subscription else 14
    
    success, message, checkout_url = stripe_service.create_checkout_session(
        user_id=current_user.id,
        plan_tier=request.plan_tier,
        billing_interval=request.billing_interval,
        success_url=request.success_url,
        cancel_url=request.cancel_url,
        trial_days=trial_days
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {
        'checkout_url': checkout_url
    }

@router.get("/customer-portal", response_model=Dict[str, Any])
async def get_customer_portal(
    return_url: str,
    current_user: User = Depends(get_current_user)
):
    """Get Stripe customer portal URL"""
    success, message, portal_url = stripe_service.get_customer_portal_url(
        user_id=current_user.id,
        return_url=return_url
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {
        'portal_url': portal_url
    }

@router.get("/usage", response_model=Dict[str, Any])
async def get_usage_summary(current_user: User = Depends(get_current_user)):
    """Get usage summary for current user"""
    summary = subscription_service.get_usage_summary(current_user.id)
    return summary

@router.post("/usage/check", response_model=Dict[str, Any])
async def check_usage_limit(
    request: CheckUsageRequest,
    current_user: User = Depends(get_current_user)
):
    """Check if usage is within limits"""
    allowed, message, usage_info = subscription_service.check_usage_limit(
        user_id=current_user.id,
        usage_type=request.usage_type,
        amount=request.amount
    )
    
    return {
        'allowed': allowed,
        'message': message,
        'usage': usage_info
    }

@router.post("/usage/track", response_model=Dict[str, Any])
async def track_usage(
    request: TrackUsageRequest,
    current_user: User = Depends(get_current_user)
):
    """Track usage (internal use)"""
    # This endpoint should be protected and only used internally
    # Add additional security checks here
    
    success = subscription_service.track_usage(
        user_id=current_user.id,
        usage_type=request.usage_type,
        quantity=request.quantity,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        description=request.description
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track usage"
        )
    
    return {'success': True}

@router.post("/payment-methods", response_model=Dict[str, Any])
async def add_payment_method(
    request: AddPaymentMethodRequest,
    current_user: User = Depends(get_current_user)
):
    """Add payment method"""
    success, message, data = stripe_service.add_payment_method(
        user_id=current_user.id,
        payment_method_id=request.payment_method_id,
        set_as_default=request.set_as_default
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {
        'message': message,
        'payment_method': data
    }

@router.get("/payment-methods", response_model=List[Dict[str, Any]])
async def list_payment_methods(current_user: User = Depends(get_current_user)):
    """List user's payment methods"""
    from database.subscription_models import PaymentMethod
    db = next(get_db())
    
    payment_methods = db.query(PaymentMethod).filter(
        PaymentMethod.user_id == current_user.id,
        PaymentMethod.is_active == True
    ).all()
    
    result = []
    for pm in payment_methods:
        result.append({
            'id': pm.id,
            'type': pm.type,
            'brand': pm.brand,
            'last_four': pm.last_four,
            'exp_month': pm.exp_month,
            'exp_year': pm.exp_year,
            'is_default': pm.is_default
        })
    
    return result

@router.delete("/payment-methods/{payment_method_id}")
async def remove_payment_method(
    payment_method_id: int,
    current_user: User = Depends(get_current_user)
):
    """Remove payment method"""
    from database.subscription_models import PaymentMethod
    db = next(get_db())
    
    payment_method = db.query(PaymentMethod).filter(
        PaymentMethod.id == payment_method_id,
        PaymentMethod.user_id == current_user.id
    ).first()
    
    if not payment_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment method not found"
        )
    
    payment_method.is_active = False
    db.commit()
    
    return {'message': 'Payment method removed'}

@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None)
):
    """Handle Stripe webhooks"""
    payload = await request.body()
    
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe signature"
        )
    
    success, message = stripe_service.process_webhook(payload, stripe_signature)
    
    if not success:
        logger.error(f"Webhook processing failed: {message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {'received': True}