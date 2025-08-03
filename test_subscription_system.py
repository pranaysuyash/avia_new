#!/usr/bin/env python3
"""
Test Subscription System
Verify subscription features are working correctly
"""

import requests
import json
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "http://localhost:8000/api"
TEST_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "Test123!@#",
    "full_name": "Test User"
}

class SubscriptionTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.user_id = None
    
    def register_user(self) -> bool:
        """Register test user"""
        try:
            response = self.session.post(
                f"{API_BASE_URL}/auth/register",
                json=TEST_USER
            )
            
            if response.status_code == 200:
                logger.info("✓ User registered successfully")
                return True
            elif response.status_code == 400:
                # User might already exist, try login
                logger.info("User already exists, attempting login")
                return self.login_user()
            else:
                logger.error(f"Registration failed: {response.json()}")
                return False
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False
    
    def login_user(self) -> bool:
        """Login test user"""
        try:
            response = self.session.post(
                f"{API_BASE_URL}/auth/login",
                data={
                    "username": TEST_USER["username"],
                    "password": TEST_USER["password"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}"
                })
                logger.info("✓ Login successful")
                return True
            else:
                logger.error(f"Login failed: {response.json()}")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def test_pricing_plans(self) -> bool:
        """Test getting pricing plans"""
        try:
            response = self.session.get(f"{API_BASE_URL}/subscriptions/plans")
            
            if response.status_code == 200:
                plans = response.json()
                logger.info(f"✓ Retrieved {len(plans)} pricing plans:")
                
                for plan in plans:
                    logger.info(f"  - {plan['name']} ({plan['tier']}): "
                               f"${plan['monthly_price']}/mo, ${plan['yearly_price']}/yr")
                    logger.info(f"    Limits: {plan['limits']['transcripts_per_month']} transcripts, "
                               f"{plan['limits']['minutes_per_month']} minutes")
                
                return True
            else:
                logger.error(f"Failed to get plans: {response.json()}")
                return False
                
        except Exception as e:
            logger.error(f"Error getting plans: {e}")
            return False
    
    def test_current_subscription(self) -> bool:
        """Test getting current subscription"""
        try:
            response = self.session.get(f"{API_BASE_URL}/subscriptions/current")
            
            if response.status_code == 200:
                sub = response.json()
                logger.info(f"✓ Current subscription: {sub['plan']['name']} ({sub['status']})")
                return True
            else:
                logger.error(f"Failed to get subscription: {response.json()}")
                return False
                
        except Exception as e:
            logger.error(f"Error getting subscription: {e}")
            return False
    
    def test_usage_summary(self) -> bool:
        """Test getting usage summary"""
        try:
            response = self.session.get(f"{API_BASE_URL}/subscriptions/usage")
            
            if response.status_code == 200:
                usage = response.json()
                logger.info(f"✓ Usage summary for {usage['plan']['name']} plan:")
                
                for metric, data in usage['usage'].items():
                    if isinstance(data, dict) and 'used' in data:
                        limit = data.get('limit', 'Unlimited')
                        if limit == -1:
                            limit = 'Unlimited'
                        logger.info(f"  - {metric}: {data['used']} / {limit}")
                
                logger.info("\n  Available features:")
                for feature, enabled in usage['features'].items():
                    status = "✓" if enabled else "✗"
                    logger.info(f"  {status} {feature}")
                
                return True
            else:
                logger.error(f"Failed to get usage: {response.json()}")
                return False
                
        except Exception as e:
            logger.error(f"Error getting usage: {e}")
            return False
    
    def test_usage_limits(self) -> bool:
        """Test checking usage limits"""
        try:
            # Test transcript limit
            response = self.session.post(
                f"{API_BASE_URL}/subscriptions/usage/check",
                json={
                    "usage_type": "transcripts",
                    "amount": 1
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✓ Transcript usage check: {'Allowed' if result['allowed'] else 'Blocked'}")
                logger.info(f"  Current: {result['usage']['current']}, "
                           f"Limit: {result['usage']['limit']}, "
                           f"Remaining: {result['usage']['remaining']}")
                return True
            else:
                logger.error(f"Failed to check usage: {response.json()}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking usage: {e}")
            return False
    
    def test_checkout_session(self) -> bool:
        """Test creating checkout session"""
        try:
            response = self.session.post(
                f"{API_BASE_URL}/subscriptions/checkout-session",
                json={
                    "plan_tier": "pro",
                    "billing_interval": "monthly",
                    "success_url": "http://localhost:8501/subscription?success=true",
                    "cancel_url": "http://localhost:8501/subscription"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info("✓ Checkout session created")
                logger.info(f"  URL: {result.get('checkout_url', 'N/A')}")
                return True
            else:
                logger.error(f"Failed to create checkout: {response.json()}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating checkout: {e}")
            return False
    
    def run_all_tests(self):
        """Run all subscription tests"""
        logger.info("Starting subscription system tests...\n")
        
        tests = [
            ("User Registration/Login", self.register_user),
            ("Get Pricing Plans", self.test_pricing_plans),
            ("Get Current Subscription", self.test_current_subscription),
            ("Get Usage Summary", self.test_usage_summary),
            ("Check Usage Limits", self.test_usage_limits),
            ("Create Checkout Session", self.test_checkout_session)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            logger.info(f"\nTesting: {test_name}")
            logger.info("=" * 50)
            
            if test_func():
                passed += 1
            else:
                failed += 1
        
        logger.info("\n" + "=" * 50)
        logger.info(f"Test Results: {passed} passed, {failed} failed")
        logger.info("=" * 50)
        
        if failed == 0:
            logger.info("✅ All tests passed!")
        else:
            logger.warning("❌ Some tests failed")

def main():
    """Main test function"""
    tester = SubscriptionTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()