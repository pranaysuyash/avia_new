#!/usr/bin/env python3
"""
Stripe Webhook Setup Script
Configures webhook endpoint for Stripe events
"""

import os
import stripe
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_webhook_endpoint(webhook_url: str, events: List[str]) -> Dict:
    """
    Create or update Stripe webhook endpoint
    
    Args:
        webhook_url: Full URL for webhook endpoint
        events: List of event types to listen for
    
    Returns:
        Webhook endpoint details
    """
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    
    if not stripe.api_key:
        raise ValueError("STRIPE_SECRET_KEY environment variable not set")
    
    try:
        # Check for existing webhook endpoints
        existing_endpoints = stripe.WebhookEndpoint.list(limit=100)
        
        for endpoint in existing_endpoints:
            if endpoint.url == webhook_url:
                logger.info(f"Found existing webhook endpoint: {endpoint.id}")
                
                # Update events if needed
                if set(endpoint.enabled_events) != set(events):
                    endpoint = stripe.WebhookEndpoint.modify(
                        endpoint.id,
                        enabled_events=events
                    )
                    logger.info("Updated webhook events")
                
                return {
                    'id': endpoint.id,
                    'url': endpoint.url,
                    'secret': endpoint.secret,
                    'enabled_events': endpoint.enabled_events
                }
        
        # Create new webhook endpoint
        endpoint = stripe.WebhookEndpoint.create(
            url=webhook_url,
            enabled_events=events
        )
        
        logger.info(f"Created new webhook endpoint: {endpoint.id}")
        
        return {
            'id': endpoint.id,
            'url': endpoint.url,
            'secret': endpoint.secret,
            'enabled_events': endpoint.enabled_events
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise

def main():
    """
    Main setup function
    """
    # Configuration
    base_url = os.getenv('API_BASE_URL', 'https://api.yourdomain.com')
    webhook_url = f"{base_url}/api/subscriptions/webhook"
    
    # Events to listen for
    events = [
        'checkout.session.completed',
        'customer.subscription.created',
        'customer.subscription.updated',
        'customer.subscription.deleted',
        'invoice.payment_succeeded',
        'invoice.payment_failed',
        'payment_method.attached',
        'payment_method.detached'
    ]
    
    logger.info("Setting up Stripe webhook endpoint...")
    logger.info(f"Webhook URL: {webhook_url}")
    logger.info(f"Events: {', '.join(events)}")
    
    try:
        result = setup_webhook_endpoint(webhook_url, events)
        
        logger.info("\n" + "=" * 60)
        logger.info("Webhook endpoint configured successfully!")
        logger.info("=" * 60)
        logger.info(f"\nEndpoint ID: {result['id']}")
        logger.info(f"Endpoint URL: {result['url']}")
        logger.info(f"\nIMPORTANT: Add this webhook secret to your environment:")
        logger.info(f"STRIPE_WEBHOOK_SECRET={result['secret']}")
        logger.info("\nEnabled events:")
        for event in result['enabled_events']:
            logger.info(f"  - {event}")
        
        # Save to .env file if it exists
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        if os.path.exists(env_file):
            with open(env_file, 'a') as f:
                f.write(f"\n# Stripe Webhook Secret (auto-generated)\n")
                f.write(f"STRIPE_WEBHOOK_SECRET={result['secret']}\n")
            logger.info(f"\nWebhook secret saved to {env_file}")
        
    except Exception as e:
        logger.error(f"Failed to setup webhook: {e}")
        raise

if __name__ == "__main__":
    main()