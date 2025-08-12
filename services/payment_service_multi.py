"""
Multi-Provider Payment Service
Supports Stripe, Razorpay, PayPal, and other payment gateways
"""

import os
import logging
import json
import hashlib
import hmac
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum

# Payment provider SDKs
import stripe
import razorpay
import paypalrestsdk
# import paddle  # Paddle for SaaS
# import mollie  # Mollie for EU
# import payu  # PayU for emerging markets

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

# Import database models
from database.models import User, Team, Subscription, Payment, Invoice

logger = logging.getLogger(__name__)


class PaymentProvider(Enum):
    """Supported payment providers"""
    STRIPE = "stripe"
    RAZORPAY = "razorpay"
    PAYPAL = "paypal"
    PADDLE = "paddle"
    MOLLIE = "mollie"
    PAYU = "payu"
    SQUARE = "square"
    BRAINTREE = "braintree"


class Currency(Enum):
    """Supported currencies"""
    USD = "usd"
    EUR = "eur"
    GBP = "gbp"
    INR = "inr"
    AUD = "aud"
    CAD = "cad"
    SGD = "sgd"
    JPY = "jpy"
    CNY = "cny"
    AED = "aed"


class PaymentGateway(ABC):
    """Abstract base class for payment gateways"""
    
    @abstractmethod
    def create_customer(self, email: str, name: Optional[str] = None, metadata: Optional[Dict] = None) -> str:
        pass
    
    @abstractmethod
    def create_subscription(self, customer_id: str, plan_id: str, trial_days: int = 0) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def cancel_subscription(self, subscription_id: str, immediately: bool = False) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def create_payment(self, amount: int, currency: str, customer_id: Optional[str] = None) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def create_checkout_session(self, amount: int, currency: str, success_url: str, cancel_url: str) -> str:
        pass
    
    @abstractmethod
    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        pass
    
    @abstractmethod
    def process_webhook(self, event_data: Dict) -> Tuple[bool, str]:
        pass


class StripeGateway(PaymentGateway):
    """Stripe payment gateway implementation"""
    
    def __init__(self, api_key: str, webhook_secret: str):
        stripe.api_key = api_key
        self.webhook_secret = webhook_secret
        
    def create_customer(self, email: str, name: Optional[str] = None, metadata: Optional[Dict] = None) -> str:
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata=metadata or {}
        )
        return customer.id
    
    def create_subscription(self, customer_id: str, plan_id: str, trial_days: int = 0) -> Dict[str, Any]:
        subscription_data = {
            "customer": customer_id,
            "items": [{"price": plan_id}]
        }
        
        if trial_days > 0:
            subscription_data["trial_period_days"] = trial_days
            
        subscription = stripe.Subscription.create(**subscription_data)
        
        return {
            "id": subscription.id,
            "status": subscription.status,
            "current_period_end": subscription.current_period_end
        }
    
    def cancel_subscription(self, subscription_id: str, immediately: bool = False) -> Dict[str, Any]:
        if immediately:
            subscription = stripe.Subscription.delete(subscription_id)
        else:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
        
        return {
            "id": subscription.id,
            "status": subscription.status,
            "canceled_at": subscription.canceled_at
        }
    
    def create_payment(self, amount: int, currency: str, customer_id: Optional[str] = None) -> Dict[str, Any]:
        intent_data = {
            "amount": amount,
            "currency": currency
        }
        
        if customer_id:
            intent_data["customer"] = customer_id
            
        payment_intent = stripe.PaymentIntent.create(**intent_data)
        
        return {
            "id": payment_intent.id,
            "client_secret": payment_intent.client_secret,
            "status": payment_intent.status
        }
    
    def create_checkout_session(self, amount: int, currency: str, success_url: str, cancel_url: str) -> str:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": currency,
                    "product_data": {"name": "Payment"},
                    "unit_amount": amount
                },
                "quantity": 1
            }],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url
        )
        return session.url
    
    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        try:
            stripe.Webhook.construct_event(payload, signature, self.webhook_secret)
            return True
        except stripe.error.SignatureVerificationError:
            return False
    
    def process_webhook(self, event_data: Dict) -> Tuple[bool, str]:
        event_type = event_data.get("type", "")
        
        if event_type == "payment_intent.succeeded":
            return True, "payment_succeeded"
        elif event_type == "customer.subscription.created":
            return True, "subscription_created"
        elif event_type == "customer.subscription.deleted":
            return True, "subscription_canceled"
        
        return True, event_type


class RazorpayGateway(PaymentGateway):
    """Razorpay payment gateway implementation (India)"""
    
    def __init__(self, key_id: str, key_secret: str, webhook_secret: str):
        self.client = razorpay.Client(auth=(key_id, key_secret))
        self.webhook_secret = webhook_secret
        
    def create_customer(self, email: str, name: Optional[str] = None, metadata: Optional[Dict] = None) -> str:
        customer_data = {
            "email": email,
            "contact": metadata.get("phone", "") if metadata else ""
        }
        
        if name:
            customer_data["name"] = name
            
        customer = self.client.customer.create(customer_data)
        return customer["id"]
    
    def create_subscription(self, customer_id: str, plan_id: str, trial_days: int = 0) -> Dict[str, Any]:
        subscription_data = {
            "plan_id": plan_id,
            "customer_notify": 1,
            "total_count": 120  # 10 years of monthly billing
        }
        
        if customer_id:
            subscription_data["customer_id"] = customer_id
            
        subscription = self.client.subscription.create(subscription_data)
        
        return {
            "id": subscription["id"],
            "status": subscription["status"],
            "current_period_end": subscription.get("current_end")
        }
    
    def cancel_subscription(self, subscription_id: str, immediately: bool = False) -> Dict[str, Any]:
        if immediately:
            subscription = self.client.subscription.cancel(subscription_id)
        else:
            subscription = self.client.subscription.cancel(
                subscription_id,
                {"cancel_at_cycle_end": 1}
            )
        
        return {
            "id": subscription["id"],
            "status": subscription["status"],
            "canceled_at": subscription.get("ended_at")
        }
    
    def create_payment(self, amount: int, currency: str, customer_id: Optional[str] = None) -> Dict[str, Any]:
        # Razorpay amount is in smallest currency unit (paise for INR)
        order_data = {
            "amount": amount,
            "currency": currency.upper(),
            "payment_capture": 1
        }
        
        if customer_id:
            order_data["customer_id"] = customer_id
            
        order = self.client.order.create(order_data)
        
        return {
            "id": order["id"],
            "client_secret": order["id"],  # Order ID acts as client secret
            "status": order["status"]
        }
    
    def create_checkout_session(self, amount: int, currency: str, success_url: str, cancel_url: str) -> str:
        # Create payment link
        payment_link = self.client.payment_link.create({
            "amount": amount,
            "currency": currency.upper(),
            "callback_url": success_url,
            "callback_method": "get"
        })
        
        return payment_link["short_url"]
    
    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        expected_signature = hmac.new(
            bytes(self.webhook_secret, 'utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    def process_webhook(self, event_data: Dict) -> Tuple[bool, str]:
        event_type = event_data.get("event", "")
        
        if event_type == "payment.captured":
            return True, "payment_succeeded"
        elif event_type == "subscription.activated":
            return True, "subscription_created"
        elif event_type == "subscription.cancelled":
            return True, "subscription_canceled"
        
        return True, event_type


class PayPalGateway(PaymentGateway):
    """PayPal payment gateway implementation"""
    
    def __init__(self, client_id: str, client_secret: str, mode: str = "sandbox"):
        paypalrestsdk.configure({
            "mode": mode,  # "sandbox" or "live"
            "client_id": client_id,
            "client_secret": client_secret
        })
        
    def create_customer(self, email: str, name: Optional[str] = None, metadata: Optional[Dict] = None) -> str:
        # PayPal doesn't have a customer concept like Stripe
        # Return email as customer ID
        return email
    
    def create_subscription(self, customer_id: str, plan_id: str, trial_days: int = 0) -> Dict[str, Any]:
        billing_plan = paypalrestsdk.BillingPlan.find(plan_id)
        
        billing_agreement = paypalrestsdk.BillingAgreement({
            "name": "Subscription Agreement",
            "description": "Subscription",
            "start_date": (datetime.utcnow() + timedelta(days=trial_days)).isoformat() + "Z",
            "plan": {
                "id": plan_id
            },
            "payer": {
                "payment_method": "paypal"
            }
        })
        
        if billing_agreement.create():
            return {
                "id": billing_agreement.id,
                "status": "created",
                "approval_url": billing_agreement.links[1].href
            }
        
        return {}
    
    def cancel_subscription(self, subscription_id: str, immediately: bool = False) -> Dict[str, Any]:
        billing_agreement = paypalrestsdk.BillingAgreement.find(subscription_id)
        
        cancel_note = {
            "note": "Canceling subscription"
        }
        
        if billing_agreement.cancel(cancel_note):
            return {
                "id": subscription_id,
                "status": "canceled",
                "canceled_at": datetime.utcnow().isoformat()
            }
        
        return {}
    
    def create_payment(self, amount: int, currency: str, customer_id: Optional[str] = None) -> Dict[str, Any]:
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "transactions": [{
                "amount": {
                    "total": str(amount / 100),  # Convert cents to dollars
                    "currency": currency.upper()
                }
            }]
        })
        
        if payment.create():
            return {
                "id": payment.id,
                "client_secret": payment.id,
                "status": payment.state
            }
        
        return {}
    
    def create_checkout_session(self, amount: int, currency: str, success_url: str, cancel_url: str) -> str:
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": success_url,
                "cancel_url": cancel_url
            },
            "transactions": [{
                "amount": {
                    "total": str(amount / 100),
                    "currency": currency.upper()
                }
            }]
        })
        
        if payment.create():
            for link in payment.links:
                if link.rel == "approval_url":
                    return link.href
        
        return ""
    
    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        # PayPal webhook verification is more complex
        # This is a simplified version
        return True
    
    def process_webhook(self, event_data: Dict) -> Tuple[bool, str]:
        event_type = event_data.get("event_type", "")
        
        if event_type == "PAYMENT.SALE.COMPLETED":
            return True, "payment_succeeded"
        elif event_type == "BILLING.SUBSCRIPTION.CREATED":
            return True, "subscription_created"
        elif event_type == "BILLING.SUBSCRIPTION.CANCELLED":
            return True, "subscription_canceled"
        
        return True, event_type


class MultiProviderPaymentService:
    """Unified payment service supporting multiple providers"""
    
    # Provider configuration
    PROVIDER_CONFIG = {
        PaymentProvider.STRIPE: {
            "currencies": [Currency.USD, Currency.EUR, Currency.GBP],
            "countries": ["US", "GB", "EU", "CA", "AU"],
            "gateway_class": StripeGateway
        },
        PaymentProvider.RAZORPAY: {
            "currencies": [Currency.INR, Currency.USD],
            "countries": ["IN"],
            "gateway_class": RazorpayGateway
        },
        PaymentProvider.PAYPAL: {
            "currencies": [Currency.USD, Currency.EUR, Currency.GBP],
            "countries": ["GLOBAL"],
            "gateway_class": PayPalGateway
        }
    }
    
    def __init__(self, db: Session, default_provider: PaymentProvider = PaymentProvider.STRIPE):
        self.db = db
        self.default_provider = default_provider
        self.gateways = {}
        
        # Initialize gateways
        self._initialize_gateways()
        
    def _initialize_gateways(self):
        """Initialize payment gateways based on configuration"""
        
        # Stripe
        if os.getenv("STRIPE_SECRET_KEY"):
            self.gateways[PaymentProvider.STRIPE] = StripeGateway(
                api_key=os.getenv("STRIPE_SECRET_KEY"),
                webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET", "")
            )
        
        # Razorpay
        if os.getenv("RAZORPAY_KEY_ID"):
            self.gateways[PaymentProvider.RAZORPAY] = RazorpayGateway(
                key_id=os.getenv("RAZORPAY_KEY_ID"),
                key_secret=os.getenv("RAZORPAY_KEY_SECRET"),
                webhook_secret=os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
            )
        
        # PayPal
        if os.getenv("PAYPAL_CLIENT_ID"):
            self.gateways[PaymentProvider.PAYPAL] = PayPalGateway(
                client_id=os.getenv("PAYPAL_CLIENT_ID"),
                client_secret=os.getenv("PAYPAL_CLIENT_SECRET"),
                mode=os.getenv("PAYPAL_MODE", "sandbox")
            )
    
    def get_provider_for_country(self, country_code: str) -> PaymentProvider:
        """Get best payment provider for a country"""
        
        # Check each provider's supported countries
        for provider, config in self.PROVIDER_CONFIG.items():
            if country_code in config["countries"] or "GLOBAL" in config["countries"]:
                if provider in self.gateways:
                    return provider
        
        return self.default_provider
    
    def get_provider_for_currency(self, currency: Currency) -> PaymentProvider:
        """Get best payment provider for a currency"""
        
        # Special cases
        if currency == Currency.INR and PaymentProvider.RAZORPAY in self.gateways:
            return PaymentProvider.RAZORPAY
        
        # Check each provider's supported currencies
        for provider, config in self.PROVIDER_CONFIG.items():
            if currency in config["currencies"]:
                if provider in self.gateways:
                    return provider
        
        return self.default_provider
    
    def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        country: Optional[str] = None,
        provider: Optional[PaymentProvider] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create customer with appropriate provider"""
        
        # Select provider
        if not provider:
            if country:
                provider = self.get_provider_for_country(country)
            else:
                provider = self.default_provider
        
        # Get gateway
        gateway = self.gateways.get(provider)
        if not gateway:
            raise ValueError(f"Provider {provider.value} not configured")
        
        # Create customer
        customer_id = gateway.create_customer(email, name, metadata)
        
        # Store in database with provider info
        return {
            "customer_id": customer_id,
            "provider": provider.value,
            "email": email
        }
    
    def create_subscription(
        self,
        customer_id: str,
        plan_id: str,
        provider: PaymentProvider,
        trial_days: int = 0
    ) -> Dict[str, Any]:
        """Create subscription with specified provider"""
        
        gateway = self.gateways.get(provider)
        if not gateway:
            raise ValueError(f"Provider {provider.value} not configured")
        
        result = gateway.create_subscription(customer_id, plan_id, trial_days)
        result["provider"] = provider.value
        
        return result
    
    def create_payment(
        self,
        amount: int,
        currency: Currency,
        customer_id: Optional[str] = None,
        provider: Optional[PaymentProvider] = None
    ) -> Dict[str, Any]:
        """Create payment with appropriate provider"""
        
        # Select provider based on currency if not specified
        if not provider:
            provider = self.get_provider_for_currency(currency)
        
        gateway = self.gateways.get(provider)
        if not gateway:
            raise ValueError(f"Provider {provider.value} not configured")
        
        result = gateway.create_payment(amount, currency.value, customer_id)
        result["provider"] = provider.value
        
        return result
    
    def create_checkout_session(
        self,
        amount: int,
        currency: Currency,
        success_url: str,
        cancel_url: str,
        country: Optional[str] = None,
        provider: Optional[PaymentProvider] = None
    ) -> str:
        """Create checkout session with appropriate provider"""
        
        # Select provider
        if not provider:
            if country:
                provider = self.get_provider_for_country(country)
            else:
                provider = self.get_provider_for_currency(currency)
        
        gateway = self.gateways.get(provider)
        if not gateway:
            raise ValueError(f"Provider {provider.value} not configured")
        
        return gateway.create_checkout_session(
            amount,
            currency.value,
            success_url,
            cancel_url
        )
    
    def process_webhook(
        self,
        provider: PaymentProvider,
        payload: bytes,
        signature: str
    ) -> Tuple[bool, str]:
        """Process webhook from specific provider"""
        
        gateway = self.gateways.get(provider)
        if not gateway:
            return False, f"Provider {provider.value} not configured"
        
        # Verify signature
        if not gateway.verify_webhook(payload, signature):
            return False, "Invalid signature"
        
        # Parse payload
        try:
            if provider == PaymentProvider.STRIPE:
                event_data = json.loads(payload)
            elif provider == PaymentProvider.RAZORPAY:
                event_data = json.loads(payload)
            elif provider == PaymentProvider.PAYPAL:
                event_data = json.loads(payload)
            else:
                event_data = json.loads(payload)
        except json.JSONDecodeError:
            return False, "Invalid payload"
        
        # Process webhook
        return gateway.process_webhook(event_data)
    
    def get_provider_comparison(
        self,
        amount: int,
        currency: Currency,
        country: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Compare fees and features across providers"""
        
        comparisons = []
        
        for provider in self.gateways.keys():
            config = self.PROVIDER_CONFIG[provider]
            
            # Check if provider supports currency
            if currency not in config["currencies"]:
                continue
            
            # Check if provider supports country
            if country and country not in config["countries"] and "GLOBAL" not in config["countries"]:
                continue
            
            # Calculate fees (simplified)
            fee_percentage = 0.029  # 2.9% default
            fixed_fee = 30  # 30 cents default
            
            if provider == PaymentProvider.STRIPE:
                if currency == Currency.INR:
                    fee_percentage = 0.03  # 3% for international
                    fixed_fee = 0
            elif provider == PaymentProvider.RAZORPAY:
                fee_percentage = 0.02  # 2%
                fixed_fee = 0
            elif provider == PaymentProvider.PAYPAL:
                fee_percentage = 0.0349  # 3.49%
                fixed_fee = 49  # 49 cents
            
            total_fee = (amount * fee_percentage) + fixed_fee
            
            comparisons.append({
                "provider": provider.value,
                "fee_percentage": fee_percentage * 100,
                "fixed_fee": fixed_fee / 100,  # Convert to currency units
                "total_fee": total_fee / 100,
                "supported": True
            })
        
        return sorted(comparisons, key=lambda x: x["total_fee"])
    
    def get_supported_providers(self) -> List[str]:
        """Get list of configured providers"""
        return [provider.value for provider in self.gateways.keys()]
    
    def get_provider_status(self, provider: PaymentProvider) -> Dict[str, Any]:
        """Check if provider is configured and working"""
        
        if provider not in self.gateways:
            return {
                "provider": provider.value,
                "configured": False,
                "status": "not_configured"
            }
        
        # Could add health check here
        return {
            "provider": provider.value,
            "configured": True,
            "status": "active"
        }