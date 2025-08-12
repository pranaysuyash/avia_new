"""
Payment Service
Production implementation with Stripe integration
"""

import os
import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
import hashlib
import hmac

import stripe
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

# Import database models
from database.models import User, Team, Subscription, Payment, Invoice

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
stripe.api_version = "2023-10-16"  # Use specific API version for consistency


class PaymentStatus(Enum):
    """Payment status types"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    REFUNDED = "refunded"
    REQUIRES_ACTION = "requires_action"


class SubscriptionStatus(Enum):
    """Subscription status types"""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    UNPAID = "unpaid"
    PAUSED = "paused"


class SubscriptionTier(Enum):
    """Subscription tiers"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class PaymentService:
    """Production payment service with Stripe integration"""
    
    # Pricing configuration (cents)
    TIER_PRICING = {
        SubscriptionTier.FREE: {
            "price": 0,
            "price_id": None,
            "features": {
                "transcription_minutes": 60,
                "team_members": 1,
                "api_calls": 100,
                "storage_gb": 1
            }
        },
        SubscriptionTier.STARTER: {
            "price": 2900,  # $29.00
            "price_id": os.getenv("STRIPE_STARTER_PRICE_ID"),
            "features": {
                "transcription_minutes": 500,
                "team_members": 3,
                "api_calls": 1000,
                "storage_gb": 10
            }
        },
        SubscriptionTier.PROFESSIONAL: {
            "price": 9900,  # $99.00
            "price_id": os.getenv("STRIPE_PRO_PRICE_ID"),
            "features": {
                "transcription_minutes": 2000,
                "team_members": 10,
                "api_calls": 10000,
                "storage_gb": 50
            }
        },
        SubscriptionTier.ENTERPRISE: {
            "price": 29900,  # $299.00
            "price_id": os.getenv("STRIPE_ENTERPRISE_PRICE_ID"),
            "features": {
                "transcription_minutes": -1,  # Unlimited
                "team_members": -1,  # Unlimited
                "api_calls": -1,  # Unlimited
                "storage_gb": 500
            }
        }
    }
    
    def __init__(self, db: Session, webhook_secret: Optional[str] = None):
        self.db = db
        self.webhook_secret = webhook_secret or os.getenv("STRIPE_WEBHOOK_SECRET")
        
    def create_customer(
        self,
        user_id: int,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create Stripe customer for user"""
        
        try:
            # Check if customer already exists
            user = self.db.query(User).filter_by(id=user_id).first()
            if user and user.stripe_customer_id:
                return user.stripe_customer_id
            
            # Create Stripe customer
            customer_data = {
                "email": email,
                "metadata": {
                    "user_id": str(user_id),
                    **(metadata or {})
                }
            }
            
            if name:
                customer_data["name"] = name
            
            customer = stripe.Customer.create(**customer_data)
            
            # Update user record
            if user:
                user.stripe_customer_id = customer.id
                self.db.commit()
            
            logger.info(f"Created Stripe customer {customer.id} for user {user_id}")
            return customer.id
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create customer: {e}")
            raise
    
    def create_subscription(
        self,
        user_id: int,
        tier: SubscriptionTier,
        payment_method_id: Optional[str] = None,
        trial_days: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create subscription for user"""
        
        try:
            # Get user and ensure customer exists
            user = self.db.query(User).filter_by(id=user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            if not user.stripe_customer_id:
                self.create_customer(user_id, user.email, user.name)
                self.db.refresh(user)
            
            # Get pricing info
            tier_info = self.TIER_PRICING[tier]
            if tier == SubscriptionTier.FREE:
                # Handle free tier without Stripe
                return self._create_free_subscription(user_id)
            
            if not tier_info["price_id"]:
                raise ValueError(f"No Stripe price ID configured for {tier.value}")
            
            # Attach payment method if provided
            if payment_method_id:
                stripe.PaymentMethod.attach(
                    payment_method_id,
                    customer=user.stripe_customer_id
                )
                
                # Set as default payment method
                stripe.Customer.modify(
                    user.stripe_customer_id,
                    invoice_settings={"default_payment_method": payment_method_id}
                )
            
            # Create subscription
            subscription_data = {
                "customer": user.stripe_customer_id,
                "items": [{"price": tier_info["price_id"]}],
                "metadata": {
                    "user_id": str(user_id),
                    "tier": tier.value,
                    **(metadata or {})
                }
            }
            
            if trial_days > 0:
                subscription_data["trial_period_days"] = trial_days
            
            if payment_method_id:
                subscription_data["default_payment_method"] = payment_method_id
            
            stripe_subscription = stripe.Subscription.create(**subscription_data)
            
            # Save to database
            subscription = Subscription(
                user_id=user_id,
                stripe_subscription_id=stripe_subscription.id,
                tier=tier.value,
                status=stripe_subscription.status,
                current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end),
                trial_end=datetime.fromtimestamp(stripe_subscription.trial_end) if stripe_subscription.trial_end else None,
                metadata=stripe_subscription.metadata
            )
            
            self.db.add(subscription)
            self.db.commit()
            
            logger.info(f"Created subscription {stripe_subscription.id} for user {user_id}")
            
            return {
                "subscription_id": stripe_subscription.id,
                "status": stripe_subscription.status,
                "tier": tier.value,
                "current_period_end": subscription.current_period_end.isoformat(),
                "trial_end": subscription.trial_end.isoformat() if subscription.trial_end else None,
                "features": tier_info["features"]
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create subscription: {e}")
            raise
    
    def _create_free_subscription(self, user_id: int) -> Dict[str, Any]:
        """Create free tier subscription (no Stripe required)"""
        
        subscription = Subscription(
            user_id=user_id,
            stripe_subscription_id=f"free_{user_id}",
            tier=SubscriptionTier.FREE.value,
            status=SubscriptionStatus.ACTIVE.value,
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30),
            metadata={"free_tier": True}
        )
        
        self.db.add(subscription)
        self.db.commit()
        
        return {
            "subscription_id": subscription.stripe_subscription_id,
            "status": subscription.status,
            "tier": subscription.tier,
            "current_period_end": subscription.current_period_end.isoformat(),
            "features": self.TIER_PRICING[SubscriptionTier.FREE]["features"]
        }
    
    def update_subscription(
        self,
        subscription_id: str,
        new_tier: Optional[SubscriptionTier] = None,
        cancel_at_period_end: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update subscription"""
        
        try:
            # Handle free tier
            if subscription_id.startswith("free_"):
                if new_tier and new_tier != SubscriptionTier.FREE:
                    # Upgrade from free tier
                    user_id = int(subscription_id.replace("free_", ""))
                    return self.create_subscription(user_id, new_tier)
                return {"message": "Free tier cannot be modified"}
            
            # Get current subscription
            stripe_subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Update tier if specified
            if new_tier:
                tier_info = self.TIER_PRICING[new_tier]
                if tier_info["price_id"]:
                    # Update subscription items
                    stripe.Subscription.modify(
                        subscription_id,
                        items=[{
                            "id": stripe_subscription["items"]["data"][0].id,
                            "price": tier_info["price_id"]
                        }],
                        proration_behavior="create_prorations"
                    )
            
            # Update cancellation status
            if cancel_at_period_end is not None:
                stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=cancel_at_period_end
                )
            
            # Update metadata
            if metadata:
                stripe.Subscription.modify(
                    subscription_id,
                    metadata=metadata
                )
            
            # Update database
            subscription = self.db.query(Subscription).filter_by(
                stripe_subscription_id=subscription_id
            ).first()
            
            if subscription:
                if new_tier:
                    subscription.tier = new_tier.value
                subscription.status = stripe_subscription.status
                subscription.updated_at = datetime.utcnow()
                self.db.commit()
            
            logger.info(f"Updated subscription {subscription_id}")
            
            return {
                "subscription_id": subscription_id,
                "status": stripe_subscription.status,
                "tier": new_tier.value if new_tier else subscription.tier,
                "cancel_at_period_end": stripe_subscription.cancel_at_period_end
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update subscription: {e}")
            raise
    
    def cancel_subscription(
        self,
        subscription_id: str,
        immediately: bool = False
    ) -> Dict[str, Any]:
        """Cancel subscription"""
        
        try:
            # Handle free tier
            if subscription_id.startswith("free_"):
                subscription = self.db.query(Subscription).filter_by(
                    stripe_subscription_id=subscription_id
                ).first()
                if subscription:
                    subscription.status = SubscriptionStatus.CANCELED.value
                    subscription.canceled_at = datetime.utcnow()
                    self.db.commit()
                return {"message": "Free tier canceled"}
            
            # Cancel Stripe subscription
            if immediately:
                stripe_subscription = stripe.Subscription.delete(subscription_id)
            else:
                stripe_subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            
            # Update database
            subscription = self.db.query(Subscription).filter_by(
                stripe_subscription_id=subscription_id
            ).first()
            
            if subscription:
                subscription.status = stripe_subscription.status
                subscription.canceled_at = datetime.utcnow()
                self.db.commit()
            
            logger.info(f"Canceled subscription {subscription_id}")
            
            return {
                "subscription_id": subscription_id,
                "status": stripe_subscription.status,
                "canceled_at": datetime.utcnow().isoformat(),
                "immediately": immediately
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription: {e}")
            raise
    
    def create_payment_intent(
        self,
        amount: int,  # in cents
        currency: str = "usd",
        user_id: Optional[int] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create one-time payment intent"""
        
        try:
            intent_data = {
                "amount": amount,
                "currency": currency,
                "metadata": metadata or {}
            }
            
            if user_id:
                user = self.db.query(User).filter_by(id=user_id).first()
                if user and user.stripe_customer_id:
                    intent_data["customer"] = user.stripe_customer_id
                intent_data["metadata"]["user_id"] = str(user_id)
            
            if description:
                intent_data["description"] = description
            
            payment_intent = stripe.PaymentIntent.create(**intent_data)
            
            # Save to database
            payment = Payment(
                user_id=user_id,
                stripe_payment_intent_id=payment_intent.id,
                amount=amount,
                currency=currency,
                status=payment_intent.status,
                description=description,
                metadata=metadata
            )
            
            self.db.add(payment)
            self.db.commit()
            
            logger.info(f"Created payment intent {payment_intent.id}")
            
            return {
                "payment_intent_id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "amount": amount,
                "currency": currency,
                "status": payment_intent.status
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create payment intent: {e}")
            raise
    
    def create_checkout_session(
        self,
        user_id: int,
        tier: SubscriptionTier,
        success_url: str,
        cancel_url: str,
        trial_days: int = 0
    ) -> str:
        """Create Stripe Checkout session"""
        
        try:
            # Get user
            user = self.db.query(User).filter_by(id=user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Get pricing info
            tier_info = self.TIER_PRICING[tier]
            if not tier_info["price_id"]:
                raise ValueError(f"No price configured for {tier.value}")
            
            # Create checkout session
            session_data = {
                "payment_method_types": ["card"],
                "line_items": [{
                    "price": tier_info["price_id"],
                    "quantity": 1
                }],
                "mode": "subscription",
                "success_url": success_url,
                "cancel_url": cancel_url,
                "metadata": {
                    "user_id": str(user_id),
                    "tier": tier.value
                }
            }
            
            # Add customer if exists
            if user.stripe_customer_id:
                session_data["customer"] = user.stripe_customer_id
            else:
                session_data["customer_email"] = user.email
            
            # Add trial period
            if trial_days > 0:
                session_data["subscription_data"] = {
                    "trial_period_days": trial_days
                }
            
            session = stripe.checkout.Session.create(**session_data)
            
            logger.info(f"Created checkout session {session.id} for user {user_id}")
            
            return session.url
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create checkout session: {e}")
            raise
    
    def create_customer_portal_session(
        self,
        user_id: int,
        return_url: str
    ) -> str:
        """Create customer portal session for billing management"""
        
        try:
            # Get user's Stripe customer ID
            user = self.db.query(User).filter_by(id=user_id).first()
            if not user or not user.stripe_customer_id:
                raise ValueError(f"No Stripe customer for user {user_id}")
            
            # Create portal session
            session = stripe.billing_portal.Session.create(
                customer=user.stripe_customer_id,
                return_url=return_url
            )
            
            logger.info(f"Created portal session for user {user_id}")
            
            return session.url
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create portal session: {e}")
            raise
    
    def process_webhook(
        self,
        payload: bytes,
        signature: str
    ) -> Tuple[bool, str]:
        """Process Stripe webhook"""
        
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                self.webhook_secret
            )
            
            # Handle different event types
            if event.type == "payment_intent.succeeded":
                self._handle_payment_succeeded(event.data.object)
                
            elif event.type == "payment_intent.payment_failed":
                self._handle_payment_failed(event.data.object)
                
            elif event.type == "customer.subscription.created":
                self._handle_subscription_created(event.data.object)
                
            elif event.type == "customer.subscription.updated":
                self._handle_subscription_updated(event.data.object)
                
            elif event.type == "customer.subscription.deleted":
                self._handle_subscription_deleted(event.data.object)
                
            elif event.type == "invoice.payment_succeeded":
                self._handle_invoice_paid(event.data.object)
                
            elif event.type == "invoice.payment_failed":
                self._handle_invoice_failed(event.data.object)
                
            else:
                logger.info(f"Unhandled webhook event type: {event.type}")
            
            return True, event.type
            
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            return False, "Invalid signature"
            
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            return False, str(e)
    
    def _handle_payment_succeeded(self, payment_intent):
        """Handle successful payment"""
        
        payment = self.db.query(Payment).filter_by(
            stripe_payment_intent_id=payment_intent.id
        ).first()
        
        if payment:
            payment.status = PaymentStatus.SUCCEEDED.value
            payment.paid_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"Payment {payment_intent.id} succeeded")
    
    def _handle_payment_failed(self, payment_intent):
        """Handle failed payment"""
        
        payment = self.db.query(Payment).filter_by(
            stripe_payment_intent_id=payment_intent.id
        ).first()
        
        if payment:
            payment.status = PaymentStatus.FAILED.value
            payment.failure_message = payment_intent.last_payment_error.message if payment_intent.last_payment_error else None
            self.db.commit()
            logger.info(f"Payment {payment_intent.id} failed")
    
    def _handle_subscription_created(self, subscription):
        """Handle new subscription"""
        
        user_id = int(subscription.metadata.get("user_id", 0))
        if not user_id:
            return
        
        # Check if subscription already exists
        existing = self.db.query(Subscription).filter_by(
            stripe_subscription_id=subscription.id
        ).first()
        
        if not existing:
            new_subscription = Subscription(
                user_id=user_id,
                stripe_subscription_id=subscription.id,
                tier=subscription.metadata.get("tier", SubscriptionTier.STARTER.value),
                status=subscription.status,
                current_period_start=datetime.fromtimestamp(subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(subscription.current_period_end),
                trial_end=datetime.fromtimestamp(subscription.trial_end) if subscription.trial_end else None
            )
            self.db.add(new_subscription)
            self.db.commit()
            logger.info(f"Subscription {subscription.id} created")
    
    def _handle_subscription_updated(self, subscription):
        """Handle subscription update"""
        
        db_subscription = self.db.query(Subscription).filter_by(
            stripe_subscription_id=subscription.id
        ).first()
        
        if db_subscription:
            db_subscription.status = subscription.status
            db_subscription.current_period_start = datetime.fromtimestamp(subscription.current_period_start)
            db_subscription.current_period_end = datetime.fromtimestamp(subscription.current_period_end)
            db_subscription.updated_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"Subscription {subscription.id} updated")
    
    def _handle_subscription_deleted(self, subscription):
        """Handle subscription cancellation"""
        
        db_subscription = self.db.query(Subscription).filter_by(
            stripe_subscription_id=subscription.id
        ).first()
        
        if db_subscription:
            db_subscription.status = SubscriptionStatus.CANCELED.value
            db_subscription.canceled_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"Subscription {subscription.id} canceled")
    
    def _handle_invoice_paid(self, invoice):
        """Handle paid invoice"""
        
        # Create or update invoice record
        db_invoice = self.db.query(Invoice).filter_by(
            stripe_invoice_id=invoice.id
        ).first()
        
        if not db_invoice:
            user_id = None
            if invoice.subscription:
                subscription = self.db.query(Subscription).filter_by(
                    stripe_subscription_id=invoice.subscription
                ).first()
                if subscription:
                    user_id = subscription.user_id
            
            db_invoice = Invoice(
                user_id=user_id,
                stripe_invoice_id=invoice.id,
                amount_paid=invoice.amount_paid,
                amount_due=invoice.amount_due,
                currency=invoice.currency,
                status="paid",
                paid_at=datetime.fromtimestamp(invoice.status_transitions.paid_at) if invoice.status_transitions.paid_at else None
            )
            self.db.add(db_invoice)
        else:
            db_invoice.status = "paid"
            db_invoice.amount_paid = invoice.amount_paid
            db_invoice.paid_at = datetime.fromtimestamp(invoice.status_transitions.paid_at) if invoice.status_transitions.paid_at else None
        
        self.db.commit()
        logger.info(f"Invoice {invoice.id} paid")
    
    def _handle_invoice_failed(self, invoice):
        """Handle failed invoice payment"""
        
        # Update subscription status if needed
        if invoice.subscription:
            subscription = self.db.query(Subscription).filter_by(
                stripe_subscription_id=invoice.subscription
            ).first()
            
            if subscription:
                subscription.status = SubscriptionStatus.PAST_DUE.value
                self.db.commit()
                logger.info(f"Subscription {invoice.subscription} marked as past due")
    
    def get_subscription_usage(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """Get current usage for user's subscription"""
        
        # Get active subscription
        subscription = self.db.query(Subscription).filter(
            and_(
                Subscription.user_id == user_id,
                Subscription.status.in_([
                    SubscriptionStatus.ACTIVE.value,
                    SubscriptionStatus.TRIALING.value
                ])
            )
        ).first()
        
        if not subscription:
            # Return free tier limits
            return self.TIER_PRICING[SubscriptionTier.FREE]["features"]
        
        # Get tier features
        tier = SubscriptionTier(subscription.tier)
        features = self.TIER_PRICING[tier]["features"].copy()
        
        # TODO: Add actual usage tracking from database
        # This would query actual usage tables
        
        return features
    
    def list_payment_methods(
        self,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """List user's payment methods"""
        
        try:
            user = self.db.query(User).filter_by(id=user_id).first()
            if not user or not user.stripe_customer_id:
                return []
            
            payment_methods = stripe.PaymentMethod.list(
                customer=user.stripe_customer_id,
                type="card"
            )
            
            return [
                {
                    "id": pm.id,
                    "brand": pm.card.brand,
                    "last4": pm.card.last4,
                    "exp_month": pm.card.exp_month,
                    "exp_year": pm.card.exp_year
                }
                for pm in payment_methods.data
            ]
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to list payment methods: {e}")
            return []
    
    def add_payment_method(
        self,
        user_id: int,
        payment_method_id: str,
        set_default: bool = True
    ) -> bool:
        """Add payment method to user"""
        
        try:
            user = self.db.query(User).filter_by(id=user_id).first()
            if not user:
                return False
            
            # Ensure customer exists
            if not user.stripe_customer_id:
                self.create_customer(user_id, user.email, user.name)
                self.db.refresh(user)
            
            # Attach payment method
            stripe.PaymentMethod.attach(
                payment_method_id,
                customer=user.stripe_customer_id
            )
            
            # Set as default if requested
            if set_default:
                stripe.Customer.modify(
                    user.stripe_customer_id,
                    invoice_settings={"default_payment_method": payment_method_id}
                )
            
            logger.info(f"Added payment method {payment_method_id} for user {user_id}")
            return True
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to add payment method: {e}")
            return False
    
    def remove_payment_method(
        self,
        payment_method_id: str
    ) -> bool:
        """Remove payment method"""
        
        try:
            stripe.PaymentMethod.detach(payment_method_id)
            logger.info(f"Removed payment method {payment_method_id}")
            return True
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to remove payment method: {e}")
            return False