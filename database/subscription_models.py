#!/usr/bin/env python3
"""
Subscription and Payment Models
Handles pricing tiers, subscriptions, payments, and usage tracking
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Enum, Text, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.models import Base
from datetime import datetime
import enum

class PricingTier(enum.Enum):
    """Available pricing tiers"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class PaymentStatus(enum.Enum):
    """Payment status"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELED = "canceled"

class SubscriptionStatus(enum.Enum):
    """Subscription status"""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    UNPAID = "unpaid"
    PAUSED = "paused"

class BillingInterval(enum.Enum):
    """Billing interval"""
    MONTHLY = "monthly"
    YEARLY = "yearly"

class PricingPlan(Base):
    """Pricing plans and tiers"""
    __tablename__ = 'pricing_plans'
    
    id = Column(Integer, primary_key=True)
    tier = Column(Enum(PricingTier), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Pricing
    monthly_price = Column(DECIMAL(10, 2), nullable=False, default=0)
    yearly_price = Column(DECIMAL(10, 2), nullable=False, default=0)
    currency = Column(String(3), default='USD')
    
    # Features and limits
    features = Column(JSON, nullable=False, default={})
    max_transcripts_per_month = Column(Integer, nullable=False)
    max_minutes_per_month = Column(Integer, nullable=False)
    max_storage_gb = Column(Integer, nullable=False)
    max_team_members = Column(Integer, nullable=False)
    max_api_calls_per_month = Column(Integer, nullable=False)
    
    # Feature flags
    has_api_access = Column(Boolean, default=False)
    has_advanced_analytics = Column(Boolean, default=False)
    has_custom_models = Column(Boolean, default=False)
    has_priority_support = Column(Boolean, default=False)
    has_white_label = Column(Boolean, default=False)
    has_sso = Column(Boolean, default=False)
    has_audit_logs = Column(Boolean, default=False)
    has_batch_processing = Column(Boolean, default=False)
    has_real_time_collab = Column(Boolean, default=False)
    
    # Stripe IDs
    stripe_monthly_price_id = Column(String(255))
    stripe_yearly_price_id = Column(String(255))
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan")

class Subscription(Base):
    """User subscriptions"""
    __tablename__ = 'subscriptions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    plan_id = Column(Integer, ForeignKey('pricing_plans.id'), nullable=False)
    
    # Stripe subscription info
    stripe_subscription_id = Column(String(255), unique=True, index=True)
    stripe_customer_id = Column(String(255), index=True)
    
    # Subscription details
    status = Column(Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.INCOMPLETE)
    billing_interval = Column(Enum(BillingInterval), nullable=False, default=BillingInterval.MONTHLY)
    
    # Dates
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    trial_start = Column(DateTime)
    trial_end = Column(DateTime)
    canceled_at = Column(DateTime)
    ended_at = Column(DateTime)
    
    # Billing
    amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), default='USD')
    
    # Usage tracking for current period
    transcripts_used = Column(Integer, default=0)
    minutes_used = Column(Integer, default=0)
    storage_used_gb = Column(Float, default=0)
    api_calls_used = Column(Integer, default=0)
    
    # Metadata
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="subscriptions")
    plan = relationship("PricingPlan", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription")
    usage_records = relationship("UsageRecord", back_populates="subscription")

class Payment(Base):
    """Payment records"""
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Stripe payment info
    stripe_payment_intent_id = Column(String(255), unique=True, index=True)
    stripe_invoice_id = Column(String(255), unique=True, index=True)
    
    # Payment details
    amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), default='USD')
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    
    # Payment method
    payment_method_type = Column(String(50))  # card, bank_transfer, etc.
    last_four = Column(String(4))  # Last 4 digits of card
    
    # Dates
    paid_at = Column(DateTime)
    failed_at = Column(DateTime)
    refunded_at = Column(DateTime)
    
    # Error handling
    failure_code = Column(String(100))
    failure_message = Column(Text)
    
    # Metadata
    description = Column(String(500))
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    subscription = relationship("Subscription", back_populates="payments")
    user = relationship("User", backref="payments")

class UsageRecord(Base):
    """Usage tracking records"""
    __tablename__ = 'usage_records'
    
    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Usage type
    usage_type = Column(String(50), nullable=False)  # transcript, minutes, storage, api_call
    quantity = Column(Float, nullable=False)
    unit = Column(String(20))  # count, minutes, gb, calls
    
    # Resource reference
    resource_type = Column(String(50))  # transcript, team, api_key
    resource_id = Column(Integer)
    
    # Period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Metadata
    description = Column(String(500))
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    subscription = relationship("Subscription", back_populates="usage_records")
    user = relationship("User", backref="usage_records")

class Coupon(Base):
    """Discount coupons"""
    __tablename__ = 'coupons'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    stripe_coupon_id = Column(String(255), unique=True)
    
    # Discount details
    percent_off = Column(Integer)  # Percentage discount (0-100)
    amount_off = Column(DECIMAL(10, 2))  # Fixed amount discount
    currency = Column(String(3), default='USD')
    
    # Validity
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime)
    max_redemptions = Column(Integer)
    times_redeemed = Column(Integer, default=0)
    
    # Restrictions
    applicable_tiers = Column(JSON, default=[])  # List of tier names
    minimum_amount = Column(DECIMAL(10, 2))
    first_time_only = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    redemptions = relationship("CouponRedemption", back_populates="coupon")

class CouponRedemption(Base):
    """Coupon redemption tracking"""
    __tablename__ = 'coupon_redemptions'
    
    id = Column(Integer, primary_key=True)
    coupon_id = Column(Integer, ForeignKey('coupons.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'))
    
    # Redemption details
    discount_applied = Column(DECIMAL(10, 2), nullable=False)
    redeemed_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    coupon = relationship("Coupon", back_populates="redemptions")
    user = relationship("User", backref="coupon_redemptions")
    subscription = relationship("Subscription", backref="coupon_redemptions")

class PaymentMethod(Base):
    """Stored payment methods"""
    __tablename__ = 'payment_methods'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Stripe payment method
    stripe_payment_method_id = Column(String(255), unique=True, nullable=False)
    
    # Payment method details
    type = Column(String(50), nullable=False)  # card, bank_account
    brand = Column(String(50))  # visa, mastercard, etc.
    last_four = Column(String(4))
    exp_month = Column(Integer)
    exp_year = Column(Integer)
    
    # Status
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Metadata
    billing_name = Column(String(255))
    billing_email = Column(String(255))
    billing_address = Column(JSON)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="payment_methods")

class Invoice(Base):
    """Invoice records"""
    __tablename__ = 'invoices'
    
    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Stripe invoice
    stripe_invoice_id = Column(String(255), unique=True, index=True)
    invoice_number = Column(String(100), unique=True)
    
    # Invoice details
    amount_due = Column(DECIMAL(10, 2), nullable=False)
    amount_paid = Column(DECIMAL(10, 2), default=0)
    currency = Column(String(3), default='USD')
    
    # Status
    status = Column(String(50), nullable=False)  # draft, open, paid, void, uncollectible
    
    # Dates
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    due_date = Column(DateTime)
    paid_at = Column(DateTime)
    
    # PDF
    invoice_pdf_url = Column(String(500))
    
    # Line items
    line_items = Column(JSON, default=[])
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    subscription = relationship("Subscription", backref="invoices")
    user = relationship("User", backref="invoices")

# Default pricing plans data
DEFAULT_PRICING_PLANS = [
    {
        'tier': PricingTier.FREE,
        'name': 'Free',
        'description': 'Perfect for trying out our service',
        'monthly_price': 0,
        'yearly_price': 0,
        'max_transcripts_per_month': 5,
        'max_minutes_per_month': 30,
        'max_storage_gb': 1,
        'max_team_members': 1,
        'max_api_calls_per_month': 100,
        'features': {
            'transcription_models': ['base'],
            'export_formats': ['txt', 'json'],
            'languages': ['en'],
            'support': 'community'
        },
        'has_api_access': False,
        'has_advanced_analytics': False,
        'has_custom_models': False,
        'has_priority_support': False,
        'has_white_label': False,
        'has_sso': False,
        'has_audit_logs': False,
        'has_batch_processing': False,
        'has_real_time_collab': False
    },
    {
        'tier': PricingTier.BASIC,
        'name': 'Basic',
        'description': 'Great for individuals and small teams',
        'monthly_price': 29,
        'yearly_price': 290,  # 2 months free
        'max_transcripts_per_month': 50,
        'max_minutes_per_month': 300,
        'max_storage_gb': 10,
        'max_team_members': 5,
        'max_api_calls_per_month': 1000,
        'features': {
            'transcription_models': ['base', 'enhanced'],
            'export_formats': ['txt', 'json', 'srt', 'vtt'],
            'languages': ['en', 'es', 'fr', 'de'],
            'support': 'email'
        },
        'has_api_access': True,
        'has_advanced_analytics': False,
        'has_custom_models': False,
        'has_priority_support': False,
        'has_white_label': False,
        'has_sso': False,
        'has_audit_logs': False,
        'has_batch_processing': False,
        'has_real_time_collab': False
    },
    {
        'tier': PricingTier.PRO,
        'name': 'Professional',
        'description': 'Advanced features for growing businesses',
        'monthly_price': 99,
        'yearly_price': 990,  # 2 months free
        'max_transcripts_per_month': 500,
        'max_minutes_per_month': 2000,
        'max_storage_gb': 100,
        'max_team_members': 20,
        'max_api_calls_per_month': 10000,
        'features': {
            'transcription_models': ['base', 'enhanced', 'premium'],
            'export_formats': ['txt', 'json', 'srt', 'vtt', 'docx', 'pdf'],
            'languages': 'all',
            'support': 'priority',
            'custom_vocabulary': True,
            'speaker_diarization': True,
            'sentiment_analysis': True
        },
        'has_api_access': True,
        'has_advanced_analytics': True,
        'has_custom_models': False,
        'has_priority_support': True,
        'has_white_label': False,
        'has_sso': False,
        'has_audit_logs': True,
        'has_batch_processing': True,
        'has_real_time_collab': True
    },
    {
        'tier': PricingTier.ENTERPRISE,
        'name': 'Enterprise',
        'description': 'Custom solutions for large organizations',
        'monthly_price': 499,
        'yearly_price': 4990,  # 2 months free
        'max_transcripts_per_month': -1,  # Unlimited
        'max_minutes_per_month': -1,  # Unlimited
        'max_storage_gb': 1000,
        'max_team_members': -1,  # Unlimited
        'max_api_calls_per_month': -1,  # Unlimited
        'features': {
            'transcription_models': 'all',
            'export_formats': 'all',
            'languages': 'all',
            'support': 'dedicated',
            'custom_vocabulary': True,
            'speaker_diarization': True,
            'sentiment_analysis': True,
            'custom_integrations': True,
            'on_premise_option': True,
            'sla': '99.9%'
        },
        'has_api_access': True,
        'has_advanced_analytics': True,
        'has_custom_models': True,
        'has_priority_support': True,
        'has_white_label': True,
        'has_sso': True,
        'has_audit_logs': True,
        'has_batch_processing': True,
        'has_real_time_collab': True
    }
]