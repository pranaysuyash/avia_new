#!/usr/bin/env python3
"""
Subscription and Payment System (Task 47)
Enterprise-grade subscription management with Stripe integration
"""

import os
import json
import logging
import secrets
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import hmac

# Mock Stripe for development - replace with actual stripe import in production
class MockStripe:
    """Mock Stripe API for development and testing"""
    
    class Customer:
        @staticmethod
        def create(**kwargs):
            return {
                'id': f"cus_{secrets.token_urlsafe(16)}",
                'email': kwargs.get('email'),
                'name': kwargs.get('name'),
                'created': int(datetime.now().timestamp())
            }
        
        @staticmethod
        def retrieve(customer_id):
            return {
                'id': customer_id,
                'email': 'test@example.com',
                'name': 'Test Customer'
            }
        
        @staticmethod
        def modify(customer_id, **kwargs):
            return {
                'id': customer_id,
                **kwargs
            }
    
    class Subscription:
        @staticmethod
        def create(**kwargs):
            return {
                'id': f"sub_{secrets.token_urlsafe(16)}",
                'customer': kwargs.get('customer'),
                'items': kwargs.get('items', []),
                'status': 'active',
                'current_period_start': int(datetime.now().timestamp()),
                'current_period_end': int((datetime.now() + timedelta(days=30)).timestamp()),
                'created': int(datetime.now().timestamp())
            }
        
        @staticmethod
        def retrieve(subscription_id):
            return {
                'id': subscription_id,
                'status': 'active',
                'current_period_start': int(datetime.now().timestamp()),
                'current_period_end': int((datetime.now() + timedelta(days=30)).timestamp())
            }
        
        @staticmethod
        def modify(subscription_id, **kwargs):
            return {
                'id': subscription_id,
                'status': kwargs.get('status', 'active'),
                **kwargs
            }
        
        @staticmethod
        def cancel(subscription_id, **kwargs):
            return {
                'id': subscription_id,
                'status': 'canceled',
                'canceled_at': int(datetime.now().timestamp())
            }
    
    class PaymentMethod:
        @staticmethod
        def create(**kwargs):
            return {
                'id': f"pm_{secrets.token_urlsafe(16)}",
                'type': kwargs.get('type', 'card'),
                'customer': kwargs.get('customer')
            }
        
        @staticmethod
        def attach(payment_method_id, **kwargs):
            return {
                'id': payment_method_id,
                'customer': kwargs.get('customer')
            }
    
    class Invoice:
        @staticmethod
        def create(**kwargs):
            return {
                'id': f"in_{secrets.token_urlsafe(16)}",
                'customer': kwargs.get('customer'),
                'amount_due': kwargs.get('amount_due', 0),
                'status': 'draft',
                'created': int(datetime.now().timestamp())
            }
        
        @staticmethod
        def finalize_invoice(invoice_id, **kwargs):
            return {
                'id': invoice_id,
                'status': 'open',
                'finalized_at': int(datetime.now().timestamp())
            }
        
        @staticmethod
        def pay(invoice_id, **kwargs):
            return {
                'id': invoice_id,
                'status': 'paid',
                'paid_at': int(datetime.now().timestamp())
            }

# Use mock Stripe for development
stripe = MockStripe()

logger = logging.getLogger(__name__)

class SubscriptionTier(Enum):
    """Subscription tier definitions"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(Enum):
    """Subscription status definitions"""
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"

class BillingInterval(Enum):
    """Billing interval definitions"""
    MONTHLY = "month"
    YEARLY = "year"

@dataclass
class PricingPlan:
    """Pricing plan configuration"""
    tier: str
    name: str
    description: str
    monthly_price: int  # in cents
    yearly_price: int   # in cents
    features: List[str]
    limits: Dict[str, Any]
    stripe_monthly_price_id: Optional[str] = None
    stripe_yearly_price_id: Optional[str] = None

@dataclass
class Subscription:
    """Subscription data model"""
    subscription_id: str
    user_id: str
    team_id: Optional[str]
    stripe_customer_id: str
    stripe_subscription_id: str
    tier: str
    status: str
    billing_interval: str
    current_period_start: str
    current_period_end: str
    created_at: str
    updated_at: str
    canceled_at: Optional[str] = None
    trial_end: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class PaymentMethod:
    """Payment method data model"""
    payment_method_id: str
    user_id: str
    stripe_payment_method_id: str
    type: str  # card, bank_account, etc.
    last_four: str
    brand: str
    exp_month: int
    exp_year: int
    is_default: bool
    created_at: str

@dataclass
class Invoice:
    """Invoice data model"""
    invoice_id: str
    subscription_id: str
    user_id: str
    stripe_invoice_id: str
    amount_due: int  # in cents
    amount_paid: int  # in cents
    status: str
    billing_period_start: str
    billing_period_end: str
    created_at: str
    paid_at: Optional[str] = None
    due_date: Optional[str] = None

@dataclass
class UsageRecord:
    """Usage tracking record"""
    usage_id: str
    user_id: str
    team_id: Optional[str]
    subscription_id: str
    metric_name: str  # api_calls, processing_minutes, storage_gb
    quantity: float
    timestamp: str
    metadata: Dict[str, Any] = None

class PricingManager:
    """Manages pricing plans and feature limits"""
    
    def __init__(self):
        self.plans = self._initialize_pricing_plans()
    
    def _initialize_pricing_plans(self) -> Dict[str, PricingPlan]:
        """Initialize pricing plan configurations"""
        return {
            SubscriptionTier.FREE.value: PricingPlan(
                tier=SubscriptionTier.FREE.value,
                name="Free",
                description="Perfect for individuals getting started",
                monthly_price=0,
                yearly_price=0,
                features=[
                    "5 hours of transcription per month",
                    "Basic entity extraction",
                    "Standard support",
                    "1 team member",
                    "1GB storage"
                ],
                limits={
                    "transcription_hours": 5,
                    "api_calls": 1000,
                    "team_members": 1,
                    "storage_gb": 1,
                    "workspaces": 3,
                    "advanced_features": False
                }
            ),
            SubscriptionTier.PRO.value: PricingPlan(
                tier=SubscriptionTier.PRO.value,
                name="Pro",
                description="For professionals and small teams",
                monthly_price=2900,  # $29.00
                yearly_price=29000,  # $290.00 (2 months free)
                features=[
                    "50 hours of transcription per month",
                    "Advanced AI analysis",
                    "Priority support",
                    "Up to 10 team members",
                    "50GB storage",
                    "Advanced export options",
                    "API access"
                ],
                limits={
                    "transcription_hours": 50,
                    "api_calls": 10000,
                    "team_members": 10,
                    "storage_gb": 50,
                    "workspaces": 25,
                    "advanced_features": True
                },
                stripe_monthly_price_id="price_pro_monthly",
                stripe_yearly_price_id="price_pro_yearly"
            ),
            SubscriptionTier.ENTERPRISE.value: PricingPlan(
                tier=SubscriptionTier.ENTERPRISE.value,
                name="Enterprise",
                description="For large organizations with advanced needs",
                monthly_price=9900,  # $99.00
                yearly_price=99000,  # $990.00 (2 months free)
                features=[
                    "Unlimited transcription",
                    "Advanced AI analysis",
                    "24/7 priority support",
                    "Unlimited team members",
                    "500GB storage",
                    "Custom integrations",
                    "Advanced API access",
                    "SSO integration",
                    "Compliance features"
                ],
                limits={
                    "transcription_hours": -1,  # unlimited
                    "api_calls": -1,  # unlimited
                    "team_members": -1,  # unlimited
                    "storage_gb": 500,
                    "workspaces": -1,  # unlimited
                    "advanced_features": True,
                    "enterprise_features": True
                },
                stripe_monthly_price_id="price_enterprise_monthly",
                stripe_yearly_price_id="price_enterprise_yearly"
            )
        }
    
    def get_plan(self, tier: str) -> Optional[PricingPlan]:
        """Get pricing plan by tier"""
        return self.plans.get(tier)
    
    def get_all_plans(self) -> List[PricingPlan]:
        """Get all pricing plans"""
        return list(self.plans.values())
    
    def check_feature_access(self, tier: str, feature: str) -> bool:
        """Check if tier has access to specific feature"""
        plan = self.get_plan(tier)
        if not plan:
            return False
        
        return plan.limits.get(feature, False)
    
    def get_usage_limit(self, tier: str, metric: str) -> int:
        """Get usage limit for specific metric"""
        plan = self.get_plan(tier)
        if not plan:
            return 0
        
        limit = plan.limits.get(metric, 0)
        return limit if limit != -1 else float('inf')
    
    def calculate_overage_cost(self, tier: str, metric: str, usage: float) -> int:
        """Calculate overage costs in cents"""
        limit = self.get_usage_limit(tier, metric)
        if limit == float('inf') or usage <= limit:
            return 0
        
        overage = usage - limit
        
        # Overage pricing (in cents)
        overage_rates = {
            "transcription_hours": 500,  # $5.00 per hour
            "api_calls": 1,  # $0.01 per 100 calls
            "storage_gb": 200  # $2.00 per GB
        }
        
        rate = overage_rates.get(metric, 0)
        if metric == "api_calls":
            return int((overage / 100) * rate)
        
        return int(overage * rate)

class SubscriptionDatabase:
    """Database manager for subscription and payment data"""
    
    def __init__(self, db_path: str = "subscriptions.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Subscriptions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS subscriptions (
                        subscription_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        team_id TEXT,
                        stripe_customer_id TEXT NOT NULL,
                        stripe_subscription_id TEXT NOT NULL,
                        tier TEXT NOT NULL,
                        status TEXT NOT NULL,
                        billing_interval TEXT NOT NULL,
                        current_period_start TEXT NOT NULL,
                        current_period_end TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        canceled_at TEXT,
                        trial_end TEXT,
                        metadata TEXT DEFAULT '{}'
                    )
                """)
                
                # Payment methods table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS payment_methods (
                        payment_method_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        stripe_payment_method_id TEXT NOT NULL,
                        type TEXT NOT NULL,
                        last_four TEXT NOT NULL,
                        brand TEXT NOT NULL,
                        exp_month INTEGER NOT NULL,
                        exp_year INTEGER NOT NULL,
                        is_default BOOLEAN DEFAULT 0,
                        created_at TEXT NOT NULL
                    )
                """)
                
                # Invoices table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS invoices (
                        invoice_id TEXT PRIMARY KEY,
                        subscription_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        stripe_invoice_id TEXT NOT NULL,
                        amount_due INTEGER NOT NULL,
                        amount_paid INTEGER DEFAULT 0,
                        status TEXT NOT NULL,
                        billing_period_start TEXT NOT NULL,
                        billing_period_end TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        paid_at TEXT,
                        due_date TEXT,
                        FOREIGN KEY (subscription_id) REFERENCES subscriptions (subscription_id)
                    )
                """)
                
                # Usage records table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS usage_records (
                        usage_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        team_id TEXT,
                        subscription_id TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        quantity REAL NOT NULL,
                        timestamp TEXT NOT NULL,
                        metadata TEXT DEFAULT '{}',
                        FOREIGN KEY (subscription_id) REFERENCES subscriptions (subscription_id)
                    )
                """)
                
                # Webhook events table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS webhook_events (
                        event_id TEXT PRIMARY KEY,
                        stripe_event_id TEXT UNIQUE NOT NULL,
                        event_type TEXT NOT NULL,
                        processed BOOLEAN DEFAULT 0,
                        created_at TEXT NOT NULL,
                        data TEXT NOT NULL
                    )
                """)
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error initializing subscription database: {e}")
            raise
    
    def create_subscription(self, subscription: Subscription) -> bool:
        """Create a new subscription"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO subscriptions (
                        subscription_id, user_id, team_id, stripe_customer_id,
                        stripe_subscription_id, tier, status, billing_interval,
                        current_period_start, current_period_end, created_at,
                        updated_at, canceled_at, trial_end, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    subscription.subscription_id, subscription.user_id, subscription.team_id,
                    subscription.stripe_customer_id, subscription.stripe_subscription_id,
                    subscription.tier, subscription.status, subscription.billing_interval,
                    subscription.current_period_start, subscription.current_period_end,
                    subscription.created_at, subscription.updated_at, subscription.canceled_at,
                    subscription.trial_end, json.dumps(subscription.metadata or {})
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            return False
    
    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Get subscription by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM subscriptions WHERE subscription_id = ?", (subscription_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_subscription(row)
                return None
        except Exception as e:
            logger.error(f"Error getting subscription: {e}")
            return None
    
    def get_user_subscription(self, user_id: str) -> Optional[Subscription]:
        """Get active subscription for user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM subscriptions 
                    WHERE user_id = ? AND status IN ('active', 'trialing', 'past_due')
                    ORDER BY created_at DESC LIMIT 1
                """, (user_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_subscription(row)
                return None
        except Exception as e:
            logger.error(f"Error getting user subscription: {e}")
            return None
    
    def update_subscription(self, subscription_id: str, **kwargs) -> bool:
        """Update subscription"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query
                set_clauses = []
                values = []
                
                for key, value in kwargs.items():
                    if key in ['tier', 'status', 'billing_interval', 'current_period_start', 
                              'current_period_end', 'updated_at', 'canceled_at', 'trial_end']:
                        set_clauses.append(f"{key} = ?")
                        values.append(value)
                    elif key == 'metadata':
                        set_clauses.append("metadata = ?")
                        values.append(json.dumps(value))
                
                if not set_clauses:
                    return False
                
                values.append(subscription_id)
                query = f"UPDATE subscriptions SET {', '.join(set_clauses)} WHERE subscription_id = ?"
                
                cursor.execute(query, values)
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating subscription: {e}")
            return False
    
    def record_usage(self, usage: UsageRecord) -> bool:
        """Record usage data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO usage_records (
                        usage_id, user_id, team_id, subscription_id,
                        metric_name, quantity, timestamp, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    usage.usage_id, usage.user_id, usage.team_id,
                    usage.subscription_id, usage.metric_name, usage.quantity,
                    usage.timestamp, json.dumps(usage.metadata or {})
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error recording usage: {e}")
            return False
    
    def get_usage_summary(self, user_id: str, start_date: str, end_date: str) -> Dict[str, float]:
        """Get usage summary for date range"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT metric_name, SUM(quantity) as total
                    FROM usage_records
                    WHERE user_id = ? AND timestamp BETWEEN ? AND ?
                    GROUP BY metric_name
                """, (user_id, start_date, end_date))
                
                results = cursor.fetchall()
                return {metric: total for metric, total in results}
        except Exception as e:
            logger.error(f"Error getting usage summary: {e}")
            return {}
    
    def _row_to_subscription(self, row) -> Subscription:
        """Convert database row to Subscription object"""
        return Subscription(
            subscription_id=row[0],
            user_id=row[1],
            team_id=row[2],
            stripe_customer_id=row[3],
            stripe_subscription_id=row[4],
            tier=row[5],
            status=row[6],
            billing_interval=row[7],
            current_period_start=row[8],
            current_period_end=row[9],
            created_at=row[10],
            updated_at=row[11],
            canceled_at=row[12],
            trial_end=row[13],
            metadata=json.loads(row[14]) if row[14] else {}
        )

class SubscriptionManager:
    """Main subscription and payment management system"""
    
    def __init__(self):
        self.db = SubscriptionDatabase()
        self.pricing = PricingManager()
    
    def create_customer(self, user_id: str, email: str, name: str) -> Tuple[bool, str, Optional[str]]:
        """Create Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={'user_id': user_id}
            )
            
            return True, "Customer created successfully", customer['id']
            
        except Exception as e:
            logger.error(f"Error creating customer: {e}")
            return False, "Failed to create customer", None
    
    def create_subscription(self, user_id: str, tier: str, billing_interval: str,
                          payment_method_id: str, team_id: Optional[str] = None) -> Tuple[bool, str, Optional[Subscription]]:
        """Create new subscription"""
        try:
            # Validate tier and billing interval
            if tier not in [t.value for t in SubscriptionTier]:
                return False, "Invalid subscription tier", None
            
            if billing_interval not in [i.value for i in BillingInterval]:
                return False, "Invalid billing interval", None
            
            # Get pricing plan
            plan = self.pricing.get_plan(tier)
            if not plan:
                return False, "Pricing plan not found", None
            
            # Free tier doesn't need Stripe subscription
            if tier == SubscriptionTier.FREE.value:
                return self._create_free_subscription(user_id, team_id)
            
            # Create or get Stripe customer
            # In real implementation, you'd store customer_id in user database
            customer_id = f"cus_{secrets.token_urlsafe(16)}"  # Mock customer ID
            
            # Get price ID based on billing interval
            price_id = (plan.stripe_monthly_price_id if billing_interval == BillingInterval.MONTHLY.value
                       else plan.stripe_yearly_price_id)
            
            if not price_id:
                return False, "Price ID not configured for this plan", None
            
            # Create Stripe subscription
            stripe_subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': price_id}],
                payment_behavior='default_incomplete',
                expand=['latest_invoice.payment_intent']
            )
            
            # Create subscription record
            subscription_id = f"sub_{secrets.token_urlsafe(16)}"
            subscription = Subscription(
                subscription_id=subscription_id,
                user_id=user_id,
                team_id=team_id,
                stripe_customer_id=customer_id,
                stripe_subscription_id=stripe_subscription['id'],
                tier=tier,
                status=stripe_subscription['status'],
                billing_interval=billing_interval,
                current_period_start=datetime.fromtimestamp(stripe_subscription['current_period_start']).isoformat(),
                current_period_end=datetime.fromtimestamp(stripe_subscription['current_period_end']).isoformat(),
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                metadata={'plan_name': plan.name}
            )
            
            if self.db.create_subscription(subscription):
                return True, "Subscription created successfully", subscription
            else:
                return False, "Failed to save subscription", None
                
        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            return False, "Subscription creation failed", None
    
    def _create_free_subscription(self, user_id: str, team_id: Optional[str] = None) -> Tuple[bool, str, Optional[Subscription]]:
        """Create free tier subscription"""
        try:
            subscription_id = f"sub_{secrets.token_urlsafe(16)}"
            subscription = Subscription(
                subscription_id=subscription_id,
                user_id=user_id,
                team_id=team_id,
                stripe_customer_id="",  # No Stripe customer for free tier
                stripe_subscription_id="",  # No Stripe subscription for free tier
                tier=SubscriptionTier.FREE.value,
                status=SubscriptionStatus.ACTIVE.value,
                billing_interval=BillingInterval.MONTHLY.value,
                current_period_start=datetime.now().isoformat(),
                current_period_end=(datetime.now() + timedelta(days=30)).isoformat(),
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                metadata={'plan_name': 'Free'}
            )
            
            if self.db.create_subscription(subscription):
                return True, "Free subscription created successfully", subscription
            else:
                return False, "Failed to create free subscription", None
                
        except Exception as e:
            logger.error(f"Error creating free subscription: {e}")
            return False, "Free subscription creation failed", None
    
    def upgrade_subscription(self, user_id: str, new_tier: str, billing_interval: str) -> Tuple[bool, str]:
        """Upgrade user subscription"""
        try:
            # Get current subscription
            current_subscription = self.db.get_user_subscription(user_id)
            if not current_subscription:
                return False, "No active subscription found"
            
            # Validate new tier
            if new_tier not in [t.value for t in SubscriptionTier]:
                return False, "Invalid subscription tier"
            
            # Check if it's actually an upgrade
            tier_hierarchy = {
                SubscriptionTier.FREE.value: 0,
                SubscriptionTier.PRO.value: 1,
                SubscriptionTier.ENTERPRISE.value: 2
            }
            
            current_level = tier_hierarchy.get(current_subscription.tier, 0)
            new_level = tier_hierarchy.get(new_tier, 0)
            
            if new_level <= current_level:
                return False, "This is not an upgrade"
            
            # Handle upgrade from free tier
            if current_subscription.tier == SubscriptionTier.FREE.value:
                # Create new paid subscription
                success, message, new_subscription = self.create_subscription(
                    user_id, new_tier, billing_interval, "pm_mock_payment_method"
                )
                
                if success:
                    # Cancel free subscription
                    self.db.update_subscription(
                        current_subscription.subscription_id,
                        status=SubscriptionStatus.CANCELED.value,
                        canceled_at=datetime.now().isoformat(),
                        updated_at=datetime.now().isoformat()
                    )
                
                if success:
                    new_plan = self.pricing.get_plan(new_tier)
                    plan_name = new_plan.name if new_plan else new_tier.title()
                    return True, f"Successfully upgraded to {plan_name}"
                return success, message
            
            # Handle upgrade between paid tiers
            new_plan = self.pricing.get_plan(new_tier)
            if not new_plan:
                return False, "New pricing plan not found"
            
            # Update Stripe subscription
            price_id = (new_plan.stripe_monthly_price_id if billing_interval == BillingInterval.MONTHLY.value
                       else new_plan.stripe_yearly_price_id)
            
            stripe.Subscription.modify(
                current_subscription.stripe_subscription_id,
                items=[{
                    'id': current_subscription.stripe_subscription_id,
                    'price': price_id
                }],
                proration_behavior='create_prorations'
            )
            
            # Update local subscription
            self.db.update_subscription(
                current_subscription.subscription_id,
                tier=new_tier,
                billing_interval=billing_interval,
                updated_at=datetime.now().isoformat(),
                metadata={'plan_name': new_plan.name, 'upgraded_from': current_subscription.tier}
            )
            
            return True, f"Successfully upgraded to {new_plan.name}"
            
        except Exception as e:
            logger.error(f"Error upgrading subscription: {e}")
            return False, "Subscription upgrade failed"
    
    def cancel_subscription(self, user_id: str, immediate: bool = False) -> Tuple[bool, str]:
        """Cancel user subscription"""
        try:
            subscription = self.db.get_user_subscription(user_id)
            if not subscription:
                return False, "No active subscription found"
            
            # Can't cancel free tier
            if subscription.tier == SubscriptionTier.FREE.value:
                return False, "Cannot cancel free tier subscription"
            
            # Cancel Stripe subscription
            if immediate:
                stripe.Subscription.cancel(subscription.stripe_subscription_id)
                status = SubscriptionStatus.CANCELED.value
                canceled_at = datetime.now().isoformat()
            else:
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                status = subscription.status  # Keep current status until period end
                canceled_at = subscription.current_period_end
            
            # Update local subscription
            self.db.update_subscription(
                subscription.subscription_id,
                status=status,
                canceled_at=canceled_at,
                updated_at=datetime.now().isoformat()
            )
            
            message = ("Subscription canceled immediately" if immediate 
                      else "Subscription will cancel at the end of current billing period")
            
            return True, message
            
        except Exception as e:
            logger.error(f"Error canceling subscription: {e}")
            return False, "Subscription cancellation failed"
    
    def check_usage_limits(self, user_id: str, metric: str, requested_usage: float) -> Tuple[bool, str, Dict[str, Any]]:
        """Check if usage is within subscription limits"""
        try:
            subscription = self.db.get_user_subscription(user_id)
            if not subscription:
                return False, "No active subscription found", {}
            
            # Get current period usage
            current_usage = self.db.get_usage_summary(
                user_id,
                subscription.current_period_start,
                subscription.current_period_end
            )
            
            current_metric_usage = current_usage.get(metric, 0)
            total_usage = current_metric_usage + requested_usage
            
            # Get limit for this tier
            limit = self.pricing.get_usage_limit(subscription.tier, metric)
            
            # Check if within limits
            if limit == float('inf') or total_usage <= limit:
                return True, "Usage within limits", {
                    'current_usage': current_metric_usage,
                    'requested_usage': requested_usage,
                    'total_usage': total_usage,
                    'limit': limit,
                    'remaining': limit - total_usage if limit != float('inf') else float('inf')
                }
            
            # Calculate overage cost
            overage_cost = self.pricing.calculate_overage_cost(subscription.tier, metric, total_usage)
            
            return False, f"Usage would exceed limit. Overage cost: ${overage_cost/100:.2f}", {
                'current_usage': current_metric_usage,
                'requested_usage': requested_usage,
                'total_usage': total_usage,
                'limit': limit,
                'overage': total_usage - limit,
                'overage_cost_cents': overage_cost
            }
            
        except Exception as e:
            logger.error(f"Error checking usage limits: {e}")
            return False, "Usage limit check failed", {}
    
    def record_usage(self, user_id: str, metric: str, quantity: float, 
                    team_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Record usage for billing"""
        try:
            subscription = self.db.get_user_subscription(user_id)
            if not subscription:
                logger.warning(f"No subscription found for user {user_id}, skipping usage recording")
                return False
            
            usage_record = UsageRecord(
                usage_id=f"usage_{secrets.token_urlsafe(16)}",
                user_id=user_id,
                team_id=team_id,
                subscription_id=subscription.subscription_id,
                metric_name=metric,
                quantity=quantity,
                timestamp=datetime.now().isoformat(),
                metadata=metadata
            )
            
            return self.db.record_usage(usage_record)
            
        except Exception as e:
            logger.error(f"Error recording usage: {e}")
            return False
    
    def get_subscription_status(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive subscription status"""
        try:
            subscription = self.db.get_user_subscription(user_id)
            if not subscription:
                # Return free tier defaults
                free_plan = self.pricing.get_plan(SubscriptionTier.FREE.value)
                return {
                    'has_subscription': False,
                    'tier': SubscriptionTier.FREE.value,
                    'status': SubscriptionStatus.ACTIVE.value,
                    'plan': asdict(free_plan) if free_plan else {},
                    'limits': free_plan.limits if free_plan else {},
                    'usage': {},
                    'billing_info': {}
                }
            
            # Get plan details
            plan = self.pricing.get_plan(subscription.tier)
            
            # Get current usage
            usage = self.db.get_usage_summary(
                user_id,
                subscription.current_period_start,
                subscription.current_period_end
            )
            
            # Calculate usage percentages
            usage_percentages = {}
            if plan:
                for metric, limit in plan.limits.items():
                    if isinstance(limit, (int, float)) and limit > 0:
                        current = usage.get(metric, 0)
                        usage_percentages[metric] = min((current / limit) * 100, 100)
            
            return {
                'has_subscription': True,
                'subscription_id': subscription.subscription_id,
                'tier': subscription.tier,
                'status': subscription.status,
                'billing_interval': subscription.billing_interval,
                'current_period_start': subscription.current_period_start,
                'current_period_end': subscription.current_period_end,
                'canceled_at': subscription.canceled_at,
                'plan': asdict(plan) if plan else {},
                'limits': plan.limits if plan else {},
                'usage': usage,
                'usage_percentages': usage_percentages,
                'billing_info': {
                    'stripe_customer_id': subscription.stripe_customer_id,
                    'stripe_subscription_id': subscription.stripe_subscription_id
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting subscription status: {e}")
            return {'error': 'Failed to get subscription status'}

class WebhookHandler:
    """Handle Stripe webhook events"""
    
    def __init__(self, subscription_manager: SubscriptionManager, webhook_secret: str):
        self.subscription_manager = subscription_manager
        self.webhook_secret = webhook_secret
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Stripe webhook signature"""
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(f"sha256={expected_signature}", signature)
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    def handle_webhook(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """Handle webhook event"""
        try:
            handlers = {
                'customer.subscription.created': self._handle_subscription_created,
                'customer.subscription.updated': self._handle_subscription_updated,
                'customer.subscription.deleted': self._handle_subscription_deleted,
                'invoice.payment_succeeded': self._handle_payment_succeeded,
                'invoice.payment_failed': self._handle_payment_failed,
            }
            
            handler = handlers.get(event_type)
            if handler:
                return handler(event_data)
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
                return True
                
        except Exception as e:
            logger.error(f"Error handling webhook event {event_type}: {e}")
            return False
    
    def _handle_subscription_created(self, data: Dict[str, Any]) -> bool:
        """Handle subscription created event"""
        # Implementation would sync Stripe subscription with local database
        return True
    
    def _handle_subscription_updated(self, data: Dict[str, Any]) -> bool:
        """Handle subscription updated event"""
        # Implementation would update local subscription status
        return True
    
    def _handle_subscription_deleted(self, data: Dict[str, Any]) -> bool:
        """Handle subscription deleted event"""
        # Implementation would mark subscription as canceled
        return True
    
    def _handle_payment_succeeded(self, data: Dict[str, Any]) -> bool:
        """Handle successful payment"""
        # Implementation would update invoice status and reset usage counters
        return True
    
    def _handle_payment_failed(self, data: Dict[str, Any]) -> bool:
        """Handle failed payment"""
        # Implementation would mark subscription as past due and send notifications
        return True

def main():
    """Demo function"""
    print("🚀 Subscription and Payment System Demo")
    print("=" * 50)
    
    # Initialize system
    subscription_manager = SubscriptionManager()
    
    # Demo user
    user_id = "user_demo_123"
    
    print(f"\n1. Creating free subscription for user {user_id}")
    success, message, subscription = subscription_manager.create_subscription(
        user_id=user_id,
        tier=SubscriptionTier.FREE.value,
        billing_interval=BillingInterval.MONTHLY.value,
        payment_method_id=""
    )
    print(f"   Result: {message}")
    
    if success:
        print(f"\n2. Checking subscription status")
        status = subscription_manager.get_subscription_status(user_id)
        print(f"   Tier: {status['tier']}")
        print(f"   Status: {status['status']}")
        print(f"   Limits: {status['limits']}")
        
        print(f"\n3. Recording usage")
        subscription_manager.record_usage(user_id, "transcription_hours", 2.5)
        subscription_manager.record_usage(user_id, "api_calls", 150)
        
        print(f"\n4. Checking usage limits")
        can_use, limit_message, usage_info = subscription_manager.check_usage_limits(
            user_id, "transcription_hours", 3.0
        )
        print(f"   Can use 3 more hours: {can_use}")
        print(f"   Message: {limit_message}")
        print(f"   Usage info: {usage_info}")
        
        print(f"\n5. Attempting upgrade to Pro")
        success, upgrade_message = subscription_manager.upgrade_subscription(
            user_id, SubscriptionTier.PRO.value, BillingInterval.MONTHLY.value
        )
        print(f"   Result: {upgrade_message}")
        
        if success:
            print(f"\n6. Updated subscription status")
            status = subscription_manager.get_subscription_status(user_id)
            print(f"   New tier: {status['tier']}")
            print(f"   New limits: {status['limits']}")
    
    print(f"\n7. Available pricing plans:")
    for plan in subscription_manager.pricing.get_all_plans():
        monthly_price = plan.monthly_price / 100
        yearly_price = plan.yearly_price / 100
        print(f"   {plan.name}: ${monthly_price:.2f}/month, ${yearly_price:.2f}/year")
        print(f"      Features: {', '.join(plan.features[:3])}...")
    
    print(f"\n✅ Demo completed successfully!")

if __name__ == "__main__":
    main()