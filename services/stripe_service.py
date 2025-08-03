#!/usr/bin/env python3
"""
Stripe Payment Service
Handles all Stripe operations including subscriptions, payments, and webhooks
"""

import stripe
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import os
from decimal import Decimal

from database.subscription_models import (
    PricingPlan, Subscription, Payment, PaymentMethod,
    Invoice, PricingTier, SubscriptionStatus, PaymentStatus,
    BillingInterval, Coupon
)
from database.models import User
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class StripeService:
    """Service for handling Stripe operations"""
    
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.stripe_api_key = os.getenv('STRIPE_SECRET_KEY')
        self.stripe_webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        self.stripe_publishable_key = os.getenv('STRIPE_PUBLISHABLE_KEY')
        
        if not self.stripe_api_key:
            logger.warning("Stripe API key not configured")
        else:
            stripe.api_key = self.stripe_api_key
    
    def _get_db(self) -> Session:
        """Get database session"""
        return self.db_session_factory()
    
    def create_customer(self, user: User, payment_method_id: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Create Stripe customer for user
        
        Returns:
            Tuple of (success, message, stripe_customer_id)
        """
        try:
            # Check if user already has a Stripe customer ID
            db = self._get_db()
            existing_sub = db.query(Subscription).filter(
                Subscription.user_id == user.id,
                Subscription.stripe_customer_id.isnot(None)
            ).first()
            
            if existing_sub and existing_sub.stripe_customer_id:
                return True, "Customer already exists", existing_sub.stripe_customer_id
            
            # Create Stripe customer
            customer_data = {
                'email': user.email,
                'name': user.full_name or user.username,
                'metadata': {
                    'user_id': str(user.id),
                    'username': user.username
                }
            }
            
            if payment_method_id:
                customer_data['payment_method'] = payment_method_id
                customer_data['invoice_settings'] = {
                    'default_payment_method': payment_method_id
                }
            
            customer = stripe.Customer.create(**customer_data)
            
            return True, "Customer created successfully", customer.id
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating customer: {e}")
            return False, str(e), None
        except Exception as e:
            logger.error(f"Error creating customer: {e}")
            return False, "Failed to create customer", None
        finally:
            db.close()
    
    def create_subscription(
        self,
        user_id: int,
        plan_tier: PricingTier,
        billing_interval: BillingInterval,
        payment_method_id: Optional[str] = None,
        coupon_code: Optional[str] = None,
        trial_days: int = 0
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Create subscription for user
        
        Returns:
            Tuple of (success, message, subscription_data)
        """
        db = self._get_db()
        try:
            # Get user and pricing plan
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, "User not found", None
            
            plan = db.query(PricingPlan).filter(PricingPlan.tier == plan_tier).first()
            if not plan:
                return False, "Pricing plan not found", None
            
            # Check for existing active subscription
            existing_sub = db.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.status.in_([
                    SubscriptionStatus.ACTIVE,
                    SubscriptionStatus.TRIALING
                ])
            ).first()
            
            if existing_sub:
                return False, "User already has an active subscription", None
            
            # Create or get Stripe customer
            if not user.stripe_customer_id:
                success, message, customer_id = self.create_customer(user, payment_method_id)
                if not success:
                    return False, message, None
            else:
                customer_id = user.stripe_customer_id
            
            # Get Stripe price ID
            if billing_interval == BillingInterval.MONTHLY:
                price_id = plan.stripe_monthly_price_id
                amount = plan.monthly_price
            else:
                price_id = plan.stripe_yearly_price_id
                amount = plan.yearly_price
            
            if not price_id:
                return False, "Stripe price not configured for this plan", None
            
            # Create subscription data
            subscription_data = {
                'customer': customer_id,
                'items': [{'price': price_id}],
                'metadata': {
                    'user_id': str(user_id),
                    'plan_tier': plan_tier.value
                }
            }
            
            # Add payment method if provided
            if payment_method_id and not user.stripe_customer_id:
                subscription_data['default_payment_method'] = payment_method_id
            
            # Add trial period
            if trial_days > 0:
                subscription_data['trial_period_days'] = trial_days
            
            # Apply coupon if provided
            if coupon_code:
                coupon = db.query(Coupon).filter(
                    Coupon.code == coupon_code,
                    Coupon.is_active == True
                ).first()
                
                if coupon and coupon.stripe_coupon_id:
                    subscription_data['coupon'] = coupon.stripe_coupon_id
            
            # Create Stripe subscription
            stripe_sub = stripe.Subscription.create(**subscription_data)
            
            # Create database subscription record
            subscription = Subscription(
                user_id=user_id,
                plan_id=plan.id,
                stripe_subscription_id=stripe_sub.id,
                stripe_customer_id=customer_id,
                status=self._map_stripe_status(stripe_sub.status),
                billing_interval=billing_interval,
                current_period_start=datetime.fromtimestamp(stripe_sub.current_period_start),
                current_period_end=datetime.fromtimestamp(stripe_sub.current_period_end),
                amount=amount,
                currency=plan.currency
            )
            
            if stripe_sub.trial_start:
                subscription.trial_start = datetime.fromtimestamp(stripe_sub.trial_start)
            if stripe_sub.trial_end:
                subscription.trial_end = datetime.fromtimestamp(stripe_sub.trial_end)
            
            db.add(subscription)
            db.commit()
            
            return True, "Subscription created successfully", {
                'subscription_id': subscription.id,
                'stripe_subscription_id': stripe_sub.id,
                'status': subscription.status.value,
                'trial_end': subscription.trial_end.isoformat() if subscription.trial_end else None
            }
            
        except stripe.error.CardError as e:
            logger.error(f"Card error: {e}")
            return False, "Card was declined", None
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            return False, str(e), None
        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            db.rollback()
            return False, "Failed to create subscription", None
        finally:
            db.close()
    
    def update_subscription(
        self,
        subscription_id: int,
        new_plan_tier: Optional[PricingTier] = None,
        new_billing_interval: Optional[BillingInterval] = None,
        cancel_at_period_end: Optional[bool] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Update existing subscription"""
        db = self._get_db()
        try:
            # Get subscription
            subscription = db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return False, "Subscription not found", None
            
            update_data = {}
            
            # Handle plan change
            if new_plan_tier or new_billing_interval:
                new_plan = db.query(PricingPlan).filter(
                    PricingPlan.tier == (new_plan_tier or subscription.plan.tier)
                ).first()
                
                if not new_plan:
                    return False, "New plan not found", None
                
                billing_interval = new_billing_interval or subscription.billing_interval
                
                if billing_interval == BillingInterval.MONTHLY:
                    price_id = new_plan.stripe_monthly_price_id
                else:
                    price_id = new_plan.stripe_yearly_price_id
                
                if not price_id:
                    return False, "Stripe price not configured for new plan", None
                
                # Update Stripe subscription
                stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    items=[{
                        'id': stripe_sub['items']['data'][0].id,
                        'price': price_id
                    }],
                    proration_behavior='create_prorations'
                )
                
                subscription.plan_id = new_plan.id
                subscription.billing_interval = billing_interval
            
            # Handle cancellation
            if cancel_at_period_end is not None:
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=cancel_at_period_end
                )
                
                if cancel_at_period_end:
                    subscription.canceled_at = datetime.utcnow()
                else:
                    subscription.canceled_at = None
            
            db.commit()
            
            return True, "Subscription updated successfully", {
                'subscription_id': subscription.id,
                'status': subscription.status.value,
                'canceled_at': subscription.canceled_at.isoformat() if subscription.canceled_at else None
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error updating subscription: {e}")
            return False, str(e), None
        except Exception as e:
            logger.error(f"Error updating subscription: {e}")
            db.rollback()
            return False, "Failed to update subscription", None
        finally:
            db.close()
    
    def cancel_subscription(
        self,
        subscription_id: int,
        immediately: bool = False
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Cancel subscription"""
        db = self._get_db()
        try:
            subscription = db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return False, "Subscription not found", None
            
            # Cancel in Stripe
            if immediately:
                stripe_sub = stripe.Subscription.delete(subscription.stripe_subscription_id)
                subscription.status = SubscriptionStatus.CANCELED
                subscription.ended_at = datetime.utcnow()
            else:
                stripe_sub = stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                subscription.canceled_at = datetime.utcnow()
            
            db.commit()
            
            return True, "Subscription canceled successfully", {
                'subscription_id': subscription.id,
                'status': subscription.status.value,
                'ends_at': subscription.current_period_end.isoformat()
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error canceling subscription: {e}")
            return False, str(e), None
        except Exception as e:
            logger.error(f"Error canceling subscription: {e}")
            db.rollback()
            return False, "Failed to cancel subscription", None
        finally:
            db.close()
    
    def add_payment_method(
        self,
        user_id: int,
        payment_method_id: str,
        set_as_default: bool = False
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Add payment method for user"""
        db = self._get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, "User not found", None
            
            # Get or create Stripe customer
            if not user.stripe_customer_id:
                success, message, customer_id = self.create_customer(user)
                if not success:
                    return False, message, None
            else:
                customer_id = user.stripe_customer_id
            
            # Attach payment method to customer
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id
            )
            
            # Set as default if requested
            if set_as_default:
                stripe.Customer.modify(
                    customer_id,
                    invoice_settings={
                        'default_payment_method': payment_method_id
                    }
                )
                
                # Update other payment methods to not be default
                db.query(PaymentMethod).filter(
                    PaymentMethod.user_id == user_id
                ).update({'is_default': False})
            
            # Save payment method to database
            db_payment_method = PaymentMethod(
                user_id=user_id,
                stripe_payment_method_id=payment_method_id,
                type=payment_method.type,
                brand=payment_method.card.brand if payment_method.type == 'card' else None,
                last_four=payment_method.card.last4 if payment_method.type == 'card' else None,
                exp_month=payment_method.card.exp_month if payment_method.type == 'card' else None,
                exp_year=payment_method.card.exp_year if payment_method.type == 'card' else None,
                is_default=set_as_default
            )
            
            db.add(db_payment_method)
            db.commit()
            
            return True, "Payment method added successfully", {
                'payment_method_id': db_payment_method.id,
                'last_four': db_payment_method.last_four,
                'brand': db_payment_method.brand
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error adding payment method: {e}")
            return False, str(e), None
        except Exception as e:
            logger.error(f"Error adding payment method: {e}")
            db.rollback()
            return False, "Failed to add payment method", None
        finally:
            db.close()
    
    def process_webhook(self, payload: bytes, sig_header: str) -> Tuple[bool, str]:
        """Process Stripe webhook"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.stripe_webhook_secret
            )
        except ValueError:
            logger.error("Invalid webhook payload")
            return False, "Invalid payload"
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            return False, "Invalid signature"
        
        # Handle different event types
        event_type = event['type']
        event_data = event['data']['object']
        
        logger.info(f"Processing webhook event: {event_type}")
        
        if event_type == 'checkout.session.completed':
            return self._handle_checkout_completed(event_data)
        
        elif event_type == 'customer.subscription.created':
            return self._handle_subscription_created(event_data)
        
        elif event_type == 'customer.subscription.updated':
            return self._handle_subscription_updated(event_data)
        
        elif event_type == 'customer.subscription.deleted':
            return self._handle_subscription_deleted(event_data)
        
        elif event_type == 'invoice.payment_succeeded':
            return self._handle_payment_succeeded(event_data)
        
        elif event_type == 'invoice.payment_failed':
            return self._handle_payment_failed(event_data)
        
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
            return True, "Event type not handled"
    
    def _handle_subscription_updated(self, stripe_sub: Dict) -> Tuple[bool, str]:
        """Handle subscription update webhook"""
        db = self._get_db()
        try:
            subscription = db.query(Subscription).filter(
                Subscription.stripe_subscription_id == stripe_sub['id']
            ).first()
            
            if not subscription:
                logger.warning(f"Subscription not found: {stripe_sub['id']}")
                return True, "Subscription not found"
            
            # Update subscription status
            subscription.status = self._map_stripe_status(stripe_sub['status'])
            subscription.current_period_start = datetime.fromtimestamp(stripe_sub['current_period_start'])
            subscription.current_period_end = datetime.fromtimestamp(stripe_sub['current_period_end'])
            
            if stripe_sub.get('canceled_at'):
                subscription.canceled_at = datetime.fromtimestamp(stripe_sub['canceled_at'])
            
            db.commit()
            return True, "Subscription updated"
            
        except Exception as e:
            logger.error(f"Error handling subscription update: {e}")
            db.rollback()
            return False, str(e)
        finally:
            db.close()
    
    def _handle_payment_succeeded(self, invoice: Dict) -> Tuple[bool, str]:
        """Handle successful payment webhook"""
        db = self._get_db()
        try:
            # Find subscription
            subscription = db.query(Subscription).filter(
                Subscription.stripe_subscription_id == invoice['subscription']
            ).first()
            
            if not subscription:
                logger.warning(f"Subscription not found for invoice: {invoice['id']}")
                return True, "Subscription not found"
            
            # Create payment record
            payment = Payment(
                subscription_id=subscription.id,
                user_id=subscription.user_id,
                stripe_invoice_id=invoice['id'],
                stripe_payment_intent_id=invoice.get('payment_intent'),
                amount=Decimal(invoice['amount_paid']) / 100,
                currency=invoice['currency'],
                status=PaymentStatus.SUCCEEDED,
                paid_at=datetime.fromtimestamp(invoice['status_transitions']['paid_at']),
                description=f"Payment for {subscription.plan.name} subscription"
            )
            
            db.add(payment)
            
            # Reset usage counters for new billing period
            subscription.transcripts_used = 0
            subscription.minutes_used = 0
            subscription.api_calls_used = 0
            
            db.commit()
            return True, "Payment recorded"
            
        except Exception as e:
            logger.error(f"Error handling payment success: {e}")
            db.rollback()
            return False, str(e)
        finally:
            db.close()
    
    def _map_stripe_status(self, stripe_status: str) -> SubscriptionStatus:
        """Map Stripe subscription status to our enum"""
        status_map = {
            'active': SubscriptionStatus.ACTIVE,
            'past_due': SubscriptionStatus.PAST_DUE,
            'canceled': SubscriptionStatus.CANCELED,
            'incomplete': SubscriptionStatus.INCOMPLETE,
            'incomplete_expired': SubscriptionStatus.INCOMPLETE_EXPIRED,
            'trialing': SubscriptionStatus.TRIALING,
            'unpaid': SubscriptionStatus.UNPAID,
            'paused': SubscriptionStatus.PAUSED
        }
        return status_map.get(stripe_status, SubscriptionStatus.INCOMPLETE)
    
    def create_checkout_session(
        self,
        user_id: int,
        plan_tier: PricingTier,
        billing_interval: BillingInterval,
        success_url: str,
        cancel_url: str,
        trial_days: int = 0
    ) -> Tuple[bool, str, Optional[str]]:
        """Create Stripe checkout session for subscription"""
        db = self._get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, "User not found", None
            
            plan = db.query(PricingPlan).filter(PricingPlan.tier == plan_tier).first()
            if not plan:
                return False, "Pricing plan not found", None
            
            # Get price ID
            if billing_interval == BillingInterval.MONTHLY:
                price_id = plan.stripe_monthly_price_id
            else:
                price_id = plan.stripe_yearly_price_id
            
            if not price_id:
                return False, "Stripe price not configured", None
            
            # Create checkout session
            session_data = {
                'payment_method_types': ['card'],
                'line_items': [{
                    'price': price_id,
                    'quantity': 1
                }],
                'mode': 'subscription',
                'success_url': success_url,
                'cancel_url': cancel_url,
                'customer_email': user.email,
                'metadata': {
                    'user_id': str(user_id),
                    'plan_tier': plan_tier.value
                }
            }
            
            if trial_days > 0:
                session_data['subscription_data'] = {
                    'trial_period_days': trial_days
                }
            
            session = stripe.checkout.Session.create(**session_data)
            
            return True, "Checkout session created", session.url
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout session: {e}")
            return False, str(e), None
        except Exception as e:
            logger.error(f"Error creating checkout session: {e}")
            return False, "Failed to create checkout session", None
        finally:
            db.close()
    
    def get_customer_portal_url(self, user_id: int, return_url: str) -> Tuple[bool, str, Optional[str]]:
        """Get Stripe customer portal URL"""
        db = self._get_db()
        try:
            # Get user's Stripe customer ID
            subscription = db.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.stripe_customer_id.isnot(None)
            ).first()
            
            if not subscription:
                return False, "No subscription found", None
            
            # Create portal session
            session = stripe.billing_portal.Session.create(
                customer=subscription.stripe_customer_id,
                return_url=return_url
            )
            
            return True, "Portal session created", session.url
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating portal session: {e}")
            return False, str(e), None
        except Exception as e:
            logger.error(f"Error creating portal session: {e}")
            return False, "Failed to create portal session", None
        finally:
            db.close()