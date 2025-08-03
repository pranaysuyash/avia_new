#!/usr/bin/env python3
"""
Subscription Management Service
Handles subscription logic, usage tracking, and feature gating
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from database.subscription_models import (
    PricingPlan, Subscription, UsageRecord, PricingTier,
    SubscriptionStatus, DEFAULT_PRICING_PLANS
)
from database.models import User, Team
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

logger = logging.getLogger(__name__)

class SubscriptionService:
    """Service for managing subscriptions and usage"""
    
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
    
    def _get_db(self) -> Session:
        """Get database session"""
        return self.db_session_factory()
    
    def initialize_pricing_plans(self) -> bool:
        """Initialize default pricing plans in database"""
        db = self._get_db()
        try:
            # Check if plans already exist
            existing_plans = db.query(PricingPlan).count()
            if existing_plans > 0:
                logger.info("Pricing plans already initialized")
                return True
            
            # Create default plans
            for plan_data in DEFAULT_PRICING_PLANS:
                plan = PricingPlan(**plan_data)
                db.add(plan)
            
            db.commit()
            logger.info("Pricing plans initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing pricing plans: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def get_user_subscription(self, user_id: int) -> Optional[Subscription]:
        """Get user's active subscription"""
        db = self._get_db()
        try:
            subscription = db.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.status.in_([
                    SubscriptionStatus.ACTIVE,
                    SubscriptionStatus.TRIALING
                ])
            ).first()
            
            return subscription
            
        finally:
            db.close()
    
    def get_user_plan(self, user_id: int) -> PricingPlan:
        """Get user's current pricing plan (or free plan if no subscription)"""
        db = self._get_db()
        try:
            subscription = self.get_user_subscription(user_id)
            
            if subscription:
                return subscription.plan
            
            # Return free plan if no subscription
            free_plan = db.query(PricingPlan).filter(
                PricingPlan.tier == PricingTier.FREE
            ).first()
            
            return free_plan
            
        finally:
            db.close()
    
    def check_feature_access(self, user_id: int, feature: str) -> bool:
        """Check if user has access to a specific feature"""
        plan = self.get_user_plan(user_id)
        if not plan:
            return False
        
        # Map feature names to plan attributes
        feature_map = {
            'api_access': 'has_api_access',
            'advanced_analytics': 'has_advanced_analytics',
            'custom_models': 'has_custom_models',
            'priority_support': 'has_priority_support',
            'white_label': 'has_white_label',
            'sso': 'has_sso',
            'audit_logs': 'has_audit_logs',
            'batch_processing': 'has_batch_processing',
            'real_time_collab': 'has_real_time_collab'
        }
        
        if feature in feature_map:
            return getattr(plan, feature_map[feature], False)
        
        # Check features JSON
        if plan.features and feature in plan.features:
            return True
        
        return False
    
    def check_usage_limit(
        self,
        user_id: int,
        usage_type: str,
        amount: int = 1
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Check if user can perform action within usage limits
        
        Args:
            user_id: User ID
            usage_type: Type of usage (transcripts, minutes, storage, api_calls)
            amount: Amount to check
            
        Returns:
            Tuple of (allowed, error_message, usage_info)
        """
        db = self._get_db()
        try:
            subscription = self.get_user_subscription(user_id)
            
            # Get plan (subscription plan or free plan)
            if subscription:
                plan = subscription.plan
                current_usage = self._get_current_usage(subscription, usage_type)
            else:
                plan = db.query(PricingPlan).filter(
                    PricingPlan.tier == PricingTier.FREE
                ).first()
                
                if not plan:
                    return False, "No pricing plan found", {}
                
                # For free users, calculate usage for current month
                current_usage = self._get_free_user_usage(user_id, usage_type, db)
            
            # Get limit based on usage type
            limit_map = {
                'transcripts': plan.max_transcripts_per_month,
                'minutes': plan.max_minutes_per_month,
                'storage': plan.max_storage_gb,
                'api_calls': plan.max_api_calls_per_month
            }
            
            limit = limit_map.get(usage_type)
            if limit is None:
                return False, f"Unknown usage type: {usage_type}", {}
            
            # Check if unlimited (-1)
            if limit == -1:
                return True, None, {
                    'current': current_usage,
                    'limit': 'unlimited',
                    'remaining': 'unlimited'
                }
            
            # Check if within limit
            if current_usage + amount > limit:
                return False, f"Usage limit exceeded for {usage_type}", {
                    'current': current_usage,
                    'limit': limit,
                    'remaining': max(0, limit - current_usage)
                }
            
            return True, None, {
                'current': current_usage,
                'limit': limit,
                'remaining': limit - current_usage
            }
            
        finally:
            db.close()
    
    def track_usage(
        self,
        user_id: int,
        usage_type: str,
        quantity: float,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        description: Optional[str] = None
    ) -> bool:
        """Track usage for a user"""
        db = self._get_db()
        try:
            subscription = self.get_user_subscription(user_id)
            
            # Create usage record
            usage_record = UsageRecord(
                user_id=user_id,
                subscription_id=subscription.id if subscription else None,
                usage_type=usage_type,
                quantity=quantity,
                resource_type=resource_type,
                resource_id=resource_id,
                description=description,
                period_start=datetime.utcnow().replace(day=1, hour=0, minute=0, second=0),
                period_end=(datetime.utcnow().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
            )
            
            # Map usage type to unit
            unit_map = {
                'transcripts': 'count',
                'minutes': 'minutes',
                'storage': 'gb',
                'api_calls': 'calls'
            }
            usage_record.unit = unit_map.get(usage_type, 'count')
            
            db.add(usage_record)
            
            # Update subscription counters if exists
            if subscription:
                if usage_type == 'transcripts':
                    subscription.transcripts_used += int(quantity)
                elif usage_type == 'minutes':
                    subscription.minutes_used += int(quantity)
                elif usage_type == 'storage':
                    subscription.storage_used_gb = quantity  # Storage is absolute, not additive
                elif usage_type == 'api_calls':
                    subscription.api_calls_used += int(quantity)
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error tracking usage: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def get_usage_summary(self, user_id: int) -> Dict[str, Any]:
        """Get usage summary for user"""
        db = self._get_db()
        try:
            subscription = self.get_user_subscription(user_id)
            plan = self.get_user_plan(user_id)
            
            if not plan:
                return {}
            
            # Get current usage
            if subscription:
                current_usage = {
                    'transcripts': subscription.transcripts_used,
                    'minutes': subscription.minutes_used,
                    'storage': subscription.storage_used_gb,
                    'api_calls': subscription.api_calls_used
                }
            else:
                # For free users, calculate from usage records
                current_usage = {
                    'transcripts': self._get_free_user_usage(user_id, 'transcripts', db),
                    'minutes': self._get_free_user_usage(user_id, 'minutes', db),
                    'storage': self._get_total_storage_usage(user_id, db),
                    'api_calls': self._get_free_user_usage(user_id, 'api_calls', db)
                }
            
            # Build summary
            summary = {
                'plan': {
                    'tier': plan.tier.value,
                    'name': plan.name,
                    'billing_interval': subscription.billing_interval.value if subscription else 'none'
                },
                'usage': {
                    'transcripts': {
                        'used': current_usage['transcripts'],
                        'limit': plan.max_transcripts_per_month,
                        'percentage': self._calculate_percentage(
                            current_usage['transcripts'],
                            plan.max_transcripts_per_month
                        )
                    },
                    'minutes': {
                        'used': current_usage['minutes'],
                        'limit': plan.max_minutes_per_month,
                        'percentage': self._calculate_percentage(
                            current_usage['minutes'],
                            plan.max_minutes_per_month
                        )
                    },
                    'storage': {
                        'used_gb': current_usage['storage'],
                        'limit_gb': plan.max_storage_gb,
                        'percentage': self._calculate_percentage(
                            current_usage['storage'],
                            plan.max_storage_gb
                        )
                    },
                    'api_calls': {
                        'used': current_usage['api_calls'],
                        'limit': plan.max_api_calls_per_month,
                        'percentage': self._calculate_percentage(
                            current_usage['api_calls'],
                            plan.max_api_calls_per_month
                        )
                    }
                },
                'features': {
                    'api_access': plan.has_api_access,
                    'advanced_analytics': plan.has_advanced_analytics,
                    'custom_models': plan.has_custom_models,
                    'priority_support': plan.has_priority_support,
                    'batch_processing': plan.has_batch_processing,
                    'real_time_collab': plan.has_real_time_collab
                }
            }
            
            if subscription:
                summary['subscription'] = {
                    'status': subscription.status.value,
                    'current_period_end': subscription.current_period_end.isoformat(),
                    'canceled_at': subscription.canceled_at.isoformat() if subscription.canceled_at else None
                }
            
            return summary
            
        finally:
            db.close()
    
    def check_team_limits(self, user_id: int, team_id: int) -> Tuple[bool, Optional[str]]:
        """Check if team operations are within plan limits"""
        db = self._get_db()
        try:
            plan = self.get_user_plan(user_id)
            if not plan:
                return False, "No pricing plan found"
            
            # Check team member limit
            team = db.query(Team).filter(Team.id == team_id).first()
            if not team:
                return False, "Team not found"
            
            # Check if user owns the team
            if team.owner_id != user_id:
                return True, None  # Only owner's plan matters for limits
            
            # Check member count
            from database.models import TeamMember
            member_count = db.query(func.count(TeamMember.id)).filter(
                TeamMember.team_id == team_id
            ).scalar()
            
            if plan.max_team_members != -1 and member_count >= plan.max_team_members:
                return False, f"Team member limit reached ({plan.max_team_members})"
            
            return True, None
            
        finally:
            db.close()
    
    def _get_current_usage(self, subscription: Subscription, usage_type: str) -> int:
        """Get current usage from subscription"""
        if usage_type == 'transcripts':
            return subscription.transcripts_used
        elif usage_type == 'minutes':
            return subscription.minutes_used
        elif usage_type == 'storage':
            return int(subscription.storage_used_gb)
        elif usage_type == 'api_calls':
            return subscription.api_calls_used
        return 0
    
    def _get_free_user_usage(self, user_id: int, usage_type: str, db: Session) -> int:
        """Get usage for free tier user in current month"""
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
        
        total = db.query(func.sum(UsageRecord.quantity)).filter(
            UsageRecord.user_id == user_id,
            UsageRecord.usage_type == usage_type,
            UsageRecord.created_at >= start_of_month
        ).scalar()
        
        return int(total or 0)
    
    def _get_total_storage_usage(self, user_id: int, db: Session) -> float:
        """Get total storage usage for user"""
        # This would calculate from actual stored files
        # For now, return from latest usage record
        latest = db.query(UsageRecord).filter(
            UsageRecord.user_id == user_id,
            UsageRecord.usage_type == 'storage'
        ).order_by(UsageRecord.created_at.desc()).first()
        
        return float(latest.quantity if latest else 0)
    
    def _calculate_percentage(self, used: float, limit: float) -> float:
        """Calculate usage percentage"""
        if limit == -1:  # Unlimited
            return 0
        if limit == 0:
            return 100 if used > 0 else 0
        return min(100, (used / limit) * 100)
    
    def get_available_plans(self) -> List[Dict[str, Any]]:
        """Get all available pricing plans"""
        db = self._get_db()
        try:
            plans = db.query(PricingPlan).filter(
                PricingPlan.is_active == True
            ).order_by(PricingPlan.monthly_price).all()
            
            result = []
            for plan in plans:
                result.append({
                    'tier': plan.tier.value,
                    'name': plan.name,
                    'description': plan.description,
                    'monthly_price': float(plan.monthly_price),
                    'yearly_price': float(plan.yearly_price),
                    'currency': plan.currency,
                    'limits': {
                        'transcripts_per_month': plan.max_transcripts_per_month,
                        'minutes_per_month': plan.max_minutes_per_month,
                        'storage_gb': plan.max_storage_gb,
                        'team_members': plan.max_team_members,
                        'api_calls_per_month': plan.max_api_calls_per_month
                    },
                    'features': plan.features,
                    'highlights': self._get_plan_highlights(plan)
                })
            
            return result
            
        finally:
            db.close()
    
    def _get_plan_highlights(self, plan: PricingPlan) -> List[str]:
        """Get highlighted features for a plan"""
        highlights = []
        
        if plan.tier == PricingTier.FREE:
            highlights = [
                f"{plan.max_transcripts_per_month} transcripts/month",
                f"{plan.max_minutes_per_month} minutes/month",
                f"{plan.max_storage_gb}GB storage",
                "Basic transcription",
                "Community support"
            ]
        elif plan.tier == PricingTier.BASIC:
            highlights = [
                f"{plan.max_transcripts_per_month} transcripts/month",
                f"{plan.max_minutes_per_month} minutes/month",
                f"{plan.max_storage_gb}GB storage",
                "API access",
                "Email support",
                "Teams up to 5 members"
            ]
        elif plan.tier == PricingTier.PRO:
            highlights = [
                f"{plan.max_transcripts_per_month} transcripts/month",
                f"{plan.max_minutes_per_month} minutes/month",
                f"{plan.max_storage_gb}GB storage",
                "Advanced analytics",
                "Priority support",
                "Batch processing",
                "Real-time collaboration"
            ]
        elif plan.tier == PricingTier.ENTERPRISE:
            highlights = [
                "Unlimited transcripts",
                "Unlimited API calls",
                f"{plan.max_storage_gb}GB storage",
                "Custom models",
                "White label option",
                "SSO & audit logs",
                "Dedicated support"
            ]
        
        return highlights