#!/usr/bin/env python3
"""
Test Suite for Subscription and Payment System
Comprehensive testing of subscription management, billing, and Stripe integration
"""

import pytest
import tempfile
import os
import json
from datetime import datetime, timedelta
from subscription_payment_system import (
    SubscriptionManager, SubscriptionDatabase, PricingManager, WebhookHandler,
    SubscriptionTier, SubscriptionStatus, BillingInterval,
    Subscription, UsageRecord, PricingPlan
)

class TestPricingManager:
    """Test pricing and plan management"""
    
    def setup_method(self):
        """Setup test environment"""
        self.pricing = PricingManager()
    
    def test_plan_initialization(self):
        """Test pricing plan initialization"""
        plans = self.pricing.get_all_plans()
        assert len(plans) == 3
        
        # Test free plan
        free_plan = self.pricing.get_plan(SubscriptionTier.FREE.value)
        assert free_plan is not None
        assert free_plan.monthly_price == 0
        assert free_plan.yearly_price == 0
        assert free_plan.limits['transcription_hours'] == 5
        assert free_plan.limits['team_members'] == 1
        
        # Test pro plan
        pro_plan = self.pricing.get_plan(SubscriptionTier.PRO.value)
        assert pro_plan is not None
        assert pro_plan.monthly_price == 2900  # $29.00
        assert pro_plan.yearly_price == 29000  # $290.00
        assert pro_plan.limits['transcription_hours'] == 50
        assert pro_plan.limits['team_members'] == 10
        
        # Test enterprise plan
        enterprise_plan = self.pricing.get_plan(SubscriptionTier.ENTERPRISE.value)
        assert enterprise_plan is not None
        assert enterprise_plan.monthly_price == 9900  # $99.00
        assert enterprise_plan.limits['transcription_hours'] == -1  # unlimited
        assert enterprise_plan.limits['team_members'] == -1  # unlimited
    
    def test_feature_access_checking(self):
        """Test feature access validation"""
        # Free tier should not have advanced features
        assert not self.pricing.check_feature_access(SubscriptionTier.FREE.value, 'advanced_features')
        
        # Pro tier should have advanced features
        assert self.pricing.check_feature_access(SubscriptionTier.PRO.value, 'advanced_features')
        
        # Enterprise tier should have enterprise features
        assert self.pricing.check_feature_access(SubscriptionTier.ENTERPRISE.value, 'enterprise_features')
    
    def test_usage_limits(self):
        """Test usage limit calculations"""
        # Free tier limits
        assert self.pricing.get_usage_limit(SubscriptionTier.FREE.value, 'transcription_hours') == 5
        assert self.pricing.get_usage_limit(SubscriptionTier.FREE.value, 'api_calls') == 1000
        
        # Pro tier limits
        assert self.pricing.get_usage_limit(SubscriptionTier.PRO.value, 'transcription_hours') == 50
        assert self.pricing.get_usage_limit(SubscriptionTier.PRO.value, 'api_calls') == 10000
        
        # Enterprise tier unlimited
        assert self.pricing.get_usage_limit(SubscriptionTier.ENTERPRISE.value, 'transcription_hours') == float('inf')
        assert self.pricing.get_usage_limit(SubscriptionTier.ENTERPRISE.value, 'api_calls') == float('inf')
    
    def test_overage_calculations(self):
        """Test overage cost calculations"""
        # No overage within limits
        assert self.pricing.calculate_overage_cost(SubscriptionTier.FREE.value, 'transcription_hours', 3) == 0
        
        # Overage calculation
        overage_cost = self.pricing.calculate_overage_cost(SubscriptionTier.FREE.value, 'transcription_hours', 7)
        assert overage_cost == 1000  # 2 hours * $5.00 = $10.00 = 1000 cents
        
        # API calls overage
        api_overage = self.pricing.calculate_overage_cost(SubscriptionTier.FREE.value, 'api_calls', 1200)
        assert api_overage == 2  # 200 calls / 100 * $0.01 = $0.02 = 2 cents
        
        # No overage for unlimited plans
        assert self.pricing.calculate_overage_cost(SubscriptionTier.ENTERPRISE.value, 'transcription_hours', 1000) == 0

class TestSubscriptionDatabase:
    """Test database operations"""
    
    def setup_method(self):
        """Setup test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = SubscriptionDatabase(self.temp_db.name)
    
    def teardown_method(self):
        """Cleanup test database"""
        os.unlink(self.temp_db.name)
    
    def test_subscription_creation_and_retrieval(self):
        """Test subscription database operations"""
        # Create test subscription
        subscription = Subscription(
            subscription_id="sub_test_123",
            user_id="user_123",
            team_id="team_456",
            stripe_customer_id="cus_stripe_123",
            stripe_subscription_id="sub_stripe_456",
            tier=SubscriptionTier.PRO.value,
            status=SubscriptionStatus.ACTIVE.value,
            billing_interval=BillingInterval.MONTHLY.value,
            current_period_start=datetime.now().isoformat(),
            current_period_end=(datetime.now() + timedelta(days=30)).isoformat(),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            metadata={"plan_name": "Pro"}
        )
        
        # Test creation
        assert self.db.create_subscription(subscription)
        
        # Test retrieval by ID
        retrieved = self.db.get_subscription("sub_test_123")
        assert retrieved is not None
        assert retrieved.user_id == "user_123"
        assert retrieved.tier == SubscriptionTier.PRO.value
        assert retrieved.metadata["plan_name"] == "Pro"
        
        # Test retrieval by user ID
        user_subscription = self.db.get_user_subscription("user_123")
        assert user_subscription is not None
        assert user_subscription.subscription_id == "sub_test_123"
    
    def test_subscription_updates(self):
        """Test subscription update operations"""
        # Create initial subscription
        subscription = Subscription(
            subscription_id="sub_update_test",
            user_id="user_update",
            team_id=None,
            stripe_customer_id="cus_update",
            stripe_subscription_id="sub_update",
            tier=SubscriptionTier.FREE.value,
            status=SubscriptionStatus.ACTIVE.value,
            billing_interval=BillingInterval.MONTHLY.value,
            current_period_start=datetime.now().isoformat(),
            current_period_end=(datetime.now() + timedelta(days=30)).isoformat(),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.db.create_subscription(subscription)
        
        # Test update
        updated_time = datetime.now().isoformat()
        success = self.db.update_subscription(
            "sub_update_test",
            tier=SubscriptionTier.PRO.value,
            status=SubscriptionStatus.ACTIVE.value,
            updated_at=updated_time,
            metadata={"upgraded": True}
        )
        
        assert success
        
        # Verify update
        updated_subscription = self.db.get_subscription("sub_update_test")
        assert updated_subscription.tier == SubscriptionTier.PRO.value
        assert updated_subscription.updated_at == updated_time
        assert updated_subscription.metadata["upgraded"] is True
    
    def test_usage_recording_and_summary(self):
        """Test usage tracking operations"""
        # Create subscription first
        subscription = Subscription(
            subscription_id="sub_usage_test",
            user_id="user_usage",
            team_id=None,
            stripe_customer_id="cus_usage",
            stripe_subscription_id="sub_usage",
            tier=SubscriptionTier.PRO.value,
            status=SubscriptionStatus.ACTIVE.value,
            billing_interval=BillingInterval.MONTHLY.value,
            current_period_start=datetime.now().isoformat(),
            current_period_end=(datetime.now() + timedelta(days=30)).isoformat(),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.db.create_subscription(subscription)
        
        # Record usage
        usage1 = UsageRecord(
            usage_id="usage_1",
            user_id="user_usage",
            team_id=None,
            subscription_id="sub_usage_test",
            metric_name="transcription_hours",
            quantity=2.5,
            timestamp=datetime.now().isoformat(),
            metadata={"source": "api"}
        )
        
        usage2 = UsageRecord(
            usage_id="usage_2",
            user_id="user_usage",
            team_id=None,
            subscription_id="sub_usage_test",
            metric_name="transcription_hours",
            quantity=1.5,
            timestamp=datetime.now().isoformat(),
            metadata={"source": "web"}
        )
        
        usage3 = UsageRecord(
            usage_id="usage_3",
            user_id="user_usage",
            team_id=None,
            subscription_id="sub_usage_test",
            metric_name="api_calls",
            quantity=500,
            timestamp=datetime.now().isoformat()
        )
        
        assert self.db.record_usage(usage1)
        assert self.db.record_usage(usage2)
        assert self.db.record_usage(usage3)
        
        # Test usage summary
        start_date = (datetime.now() - timedelta(days=1)).isoformat()
        end_date = (datetime.now() + timedelta(days=1)).isoformat()
        
        summary = self.db.get_usage_summary("user_usage", start_date, end_date)
        
        assert summary["transcription_hours"] == 4.0  # 2.5 + 1.5
        assert summary["api_calls"] == 500

class TestSubscriptionManager:
    """Test high-level subscription management"""
    
    def setup_method(self):
        """Setup test manager"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.manager = SubscriptionManager()
        self.manager.db = SubscriptionDatabase(self.temp_db.name)
    
    def teardown_method(self):
        """Cleanup test database"""
        os.unlink(self.temp_db.name)
    
    def test_free_subscription_creation(self):
        """Test free tier subscription creation"""
        success, message, subscription = self.manager.create_subscription(
            user_id="user_free",
            tier=SubscriptionTier.FREE.value,
            billing_interval=BillingInterval.MONTHLY.value,
            payment_method_id=""
        )
        
        assert success
        assert "successfully" in message.lower()
        assert subscription is not None
        assert subscription.tier == SubscriptionTier.FREE.value
        assert subscription.status == SubscriptionStatus.ACTIVE.value
        assert subscription.stripe_customer_id == ""  # No Stripe for free tier
        assert subscription.stripe_subscription_id == ""
    
    def test_paid_subscription_creation(self):
        """Test paid subscription creation"""
        success, message, subscription = self.manager.create_subscription(
            user_id="user_pro",
            tier=SubscriptionTier.PRO.value,
            billing_interval=BillingInterval.MONTHLY.value,
            payment_method_id="pm_test_123"
        )
        
        assert success
        assert "successfully" in message.lower()
        assert subscription is not None
        assert subscription.tier == SubscriptionTier.PRO.value
        assert subscription.status == SubscriptionStatus.ACTIVE.value
        assert subscription.stripe_customer_id != ""
        assert subscription.stripe_subscription_id != ""
    
    def test_subscription_upgrade(self):
        """Test subscription upgrade workflow"""
        # Create free subscription
        success, message, free_sub = self.manager.create_subscription(
            user_id="user_upgrade",
            tier=SubscriptionTier.FREE.value,
            billing_interval=BillingInterval.MONTHLY.value,
            payment_method_id=""
        )
        assert success
        
        # Upgrade to Pro
        success, upgrade_message = self.manager.upgrade_subscription(
            user_id="user_upgrade",
            new_tier=SubscriptionTier.PRO.value,
            billing_interval=BillingInterval.MONTHLY.value
        )
        
        assert success
        assert "upgraded" in upgrade_message.lower()
        
        # Verify upgrade
        status = self.manager.get_subscription_status("user_upgrade")
        assert status['tier'] == SubscriptionTier.PRO.value
        assert status['has_subscription'] is True
    
    def test_subscription_cancellation(self):
        """Test subscription cancellation"""
        # Create paid subscription
        success, message, subscription = self.manager.create_subscription(
            user_id="user_cancel",
            tier=SubscriptionTier.PRO.value,
            billing_interval=BillingInterval.MONTHLY.value,
            payment_method_id="pm_test_cancel"
        )
        assert success
        
        # Cancel subscription
        success, cancel_message = self.manager.cancel_subscription("user_cancel", immediate=True)
        
        assert success
        assert "canceled" in cancel_message.lower()
        
        # Verify cancellation
        updated_subscription = self.manager.db.get_subscription(subscription.subscription_id)
        assert updated_subscription.status == SubscriptionStatus.CANCELED.value
        assert updated_subscription.canceled_at is not None
    
    def test_usage_limit_checking(self):
        """Test usage limit validation"""
        # Create free subscription
        self.manager.create_subscription(
            user_id="user_limits",
            tier=SubscriptionTier.FREE.value,
            billing_interval=BillingInterval.MONTHLY.value,
            payment_method_id=""
        )
        
        # Record some usage
        self.manager.record_usage("user_limits", "transcription_hours", 3.0)
        
        # Check if can use more (within limits)
        can_use, message, info = self.manager.check_usage_limits(
            "user_limits", "transcription_hours", 1.0
        )
        
        assert can_use
        assert "within limits" in message.lower()
        assert info['current_usage'] == 3.0
        assert info['total_usage'] == 4.0
        assert info['limit'] == 5.0
        assert info['remaining'] == 1.0
        
        # Check if exceeds limits
        can_use, message, info = self.manager.check_usage_limits(
            "user_limits", "transcription_hours", 3.0
        )
        
        assert not can_use
        assert "exceed limit" in message.lower()
        assert info['overage'] == 1.0  # 6.0 - 5.0
        assert info['overage_cost_cents'] > 0
    
    def test_usage_recording(self):
        """Test usage recording functionality"""
        # Create subscription
        self.manager.create_subscription(
            user_id="user_usage_record",
            tier=SubscriptionTier.PRO.value,
            billing_interval=BillingInterval.MONTHLY.value,
            payment_method_id="pm_test_usage"
        )
        
        # Record usage with metadata
        success = self.manager.record_usage(
            user_id="user_usage_record",
            metric="transcription_hours",
            quantity=2.5,
            team_id="team_123",
            metadata={"file_name": "meeting.mp4", "duration": 150}
        )
        
        assert success
        
        # Verify usage was recorded
        subscription = self.manager.db.get_user_subscription("user_usage_record")
        usage_summary = self.manager.db.get_usage_summary(
            "user_usage_record",
            subscription.current_period_start,
            subscription.current_period_end
        )
        
        assert usage_summary["transcription_hours"] == 2.5
    
    def test_subscription_status_retrieval(self):
        """Test comprehensive subscription status"""
        # Test user without subscription (should get free tier defaults)
        status = self.manager.get_subscription_status("user_no_sub")
        
        assert status['has_subscription'] is False
        assert status['tier'] == SubscriptionTier.FREE.value
        assert status['status'] == SubscriptionStatus.ACTIVE.value
        assert 'limits' in status
        assert 'usage' in status
        
        # Create subscription and test status
        self.manager.create_subscription(
            user_id="user_status",
            tier=SubscriptionTier.PRO.value,
            billing_interval=BillingInterval.MONTHLY.value,
            payment_method_id="pm_test_status"
        )
        
        # Record some usage
        self.manager.record_usage("user_status", "transcription_hours", 10.0)
        self.manager.record_usage("user_status", "api_calls", 2000)
        
        status = self.manager.get_subscription_status("user_status")
        
        assert status['has_subscription'] is True
        assert status['tier'] == SubscriptionTier.PRO.value
        assert status['billing_interval'] == BillingInterval.MONTHLY.value
        assert 'subscription_id' in status
        assert 'current_period_start' in status
        assert 'current_period_end' in status
        assert status['usage']['transcription_hours'] == 10.0
        assert status['usage']['api_calls'] == 2000
        assert 'usage_percentages' in status
        assert status['usage_percentages']['transcription_hours'] == 20.0  # 10/50 * 100
    
    def test_invalid_operations(self):
        """Test error handling for invalid operations"""
        # Test invalid tier
        success, message, subscription = self.manager.create_subscription(
            user_id="user_invalid",
            tier="invalid_tier",
            billing_interval=BillingInterval.MONTHLY.value,
            payment_method_id=""
        )
        
        assert not success
        assert "invalid" in message.lower()
        
        # Test upgrade without subscription
        success, message = self.manager.upgrade_subscription(
            user_id="user_no_sub",
            new_tier=SubscriptionTier.PRO.value,
            billing_interval=BillingInterval.MONTHLY.value
        )
        
        assert not success
        assert "no active subscription" in message.lower()
        
        # Test cancel free subscription
        self.manager.create_subscription(
            user_id="user_free_cancel",
            tier=SubscriptionTier.FREE.value,
            billing_interval=BillingInterval.MONTHLY.value,
            payment_method_id=""
        )
        
        success, message = self.manager.cancel_subscription("user_free_cancel")
        
        assert not success
        assert "cannot cancel free" in message.lower()

class TestWebhookHandler:
    """Test webhook event handling"""
    
    def setup_method(self):
        """Setup webhook handler"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.subscription_manager = SubscriptionManager()
        self.subscription_manager.db = SubscriptionDatabase(self.temp_db.name)
        self.webhook_handler = WebhookHandler(self.subscription_manager, "test_webhook_secret")
    
    def teardown_method(self):
        """Cleanup test database"""
        os.unlink(self.temp_db.name)
    
    def test_webhook_signature_verification(self):
        """Test webhook signature verification"""
        payload = b'{"test": "data"}'
        
        # Test with correct signature
        import hmac
        import hashlib
        expected_signature = hmac.new(
            "test_webhook_secret".encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        assert self.webhook_handler.verify_webhook_signature(
            payload, f"sha256={expected_signature}"
        )
        
        # Test with incorrect signature
        assert not self.webhook_handler.verify_webhook_signature(
            payload, "sha256=invalid_signature"
        )
    
    def test_webhook_event_handling(self):
        """Test webhook event processing"""
        # Test supported event types
        supported_events = [
            'customer.subscription.created',
            'customer.subscription.updated',
            'customer.subscription.deleted',
            'invoice.payment_succeeded',
            'invoice.payment_failed'
        ]
        
        for event_type in supported_events:
            success = self.webhook_handler.handle_webhook(event_type, {"test": "data"})
            assert success
        
        # Test unsupported event type
        success = self.webhook_handler.handle_webhook('unsupported.event', {"test": "data"})
        assert success  # Should still return True but log as unhandled

def test_integration_workflow():
    """Test complete subscription workflow"""
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        manager = SubscriptionManager()
        manager.db = SubscriptionDatabase(temp_db.name)
        
        # 1. Create free subscription
        success, message, free_sub = manager.create_subscription(
            user_id="integration_user",
            tier=SubscriptionTier.FREE.value,
            billing_interval=BillingInterval.MONTHLY.value,
            payment_method_id=""
        )
        assert success
        
        # 2. Record usage
        manager.record_usage("integration_user", "transcription_hours", 3.0)
        manager.record_usage("integration_user", "api_calls", 800)
        
        # 3. Check limits
        can_use, message, info = manager.check_usage_limits(
            "integration_user", "transcription_hours", 1.5
        )
        assert can_use  # 3.0 + 1.5 = 4.5, limit is 5.0
        
        # 4. Upgrade subscription
        success, upgrade_message = manager.upgrade_subscription(
            "integration_user", SubscriptionTier.PRO.value, BillingInterval.MONTHLY.value
        )
        assert success
        
        # 5. Verify upgrade
        status = manager.get_subscription_status("integration_user")
        assert status['tier'] == SubscriptionTier.PRO.value
        assert status['limits']['transcription_hours'] == 50
        
        # 6. Record more usage (now within Pro limits)
        manager.record_usage("integration_user", "transcription_hours", 20.0)
        
        # 7. Check new usage totals
        updated_status = manager.get_subscription_status("integration_user")
        assert updated_status['usage']['transcription_hours'] == 23.0  # 3.0 + 20.0
        
        # 8. Test cancellation
        success, cancel_message = manager.cancel_subscription("integration_user")
        assert success
        
        print("✅ Integration workflow test completed successfully!")
        
    finally:
        os.unlink(temp_db.name)

def test_pricing_edge_cases():
    """Test edge cases in pricing calculations"""
    pricing = PricingManager()
    
    # Test zero usage
    assert pricing.calculate_overage_cost(SubscriptionTier.FREE.value, "transcription_hours", 0) == 0
    
    # Test exact limit usage
    assert pricing.calculate_overage_cost(SubscriptionTier.FREE.value, "transcription_hours", 5) == 0
    
    # Test fractional overage
    overage = pricing.calculate_overage_cost(SubscriptionTier.FREE.value, "transcription_hours", 5.5)
    assert overage == 250  # 0.5 hours * $5.00 = $2.50 = 250 cents
    
    # Test unknown metric
    assert pricing.calculate_overage_cost(SubscriptionTier.FREE.value, "unknown_metric", 100) == 0

if __name__ == "__main__":
    # Run integration test
    test_integration_workflow()
    test_pricing_edge_cases()
    
    # Run pytest if available
    try:
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not available, running basic tests...")
        
        # Run basic tests manually
        test_pricing = TestPricingManager()
        test_pricing.setup_method()
        test_pricing.test_plan_initialization()
        test_pricing.test_feature_access_checking()
        test_pricing.test_usage_limits()
        test_pricing.test_overage_calculations()
        print("✅ Pricing manager tests passed!")
        
        test_db = TestSubscriptionDatabase()
        test_db.setup_method()
        test_db.test_subscription_creation_and_retrieval()
        test_db.test_subscription_updates()
        test_db.test_usage_recording_and_summary()
        test_db.teardown_method()
        print("✅ Database tests passed!")
        
        test_manager = TestSubscriptionManager()
        test_manager.setup_method()
        test_manager.test_free_subscription_creation()
        test_manager.test_paid_subscription_creation()
        test_manager.test_subscription_upgrade()
        test_manager.test_usage_limit_checking()
        test_manager.test_subscription_status_retrieval()
        test_manager.teardown_method()
        print("✅ Manager tests passed!")
        
        print("🎉 All tests completed successfully!")