"""
Test suite for Marketing and Growth Features System
Tests referral programs, affiliate marketing, social sharing, A/B testing, and analytics
"""

import pytest
import os
import tempfile
import json
from datetime import datetime, timedelta
from marketing_growth_system import MarketingGrowthSystem, CampaignType, ABTestStatus

class TestMarketingGrowthSystem:
    
    @pytest.fixture
    def marketing_system(self):
        """Create a temporary marketing system for testing"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
            db_path = tmp_file.name
        
        system = MarketingGrowthSystem(db_path)
        yield system
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_database_initialization(self, marketing_system):
        """Test that the database is properly initialized"""
        # Database should be created and accessible
        assert os.path.exists(marketing_system.db_path)
        
        # Should be able to get analytics without errors
        analytics = marketing_system.get_referral_analytics()
        assert isinstance(analytics, dict)
        assert "total_referrals" in analytics
    
    def test_referral_program_creation(self, marketing_system):
        """Test creating referral programs"""
        program_id = marketing_system.create_referral_program(
            name="Test Referral Program",
            reward_type="credit",
            reward_amount=25.0,
            referrer_reward=25.0,
            referee_reward=25.0,
            minimum_spend=50.0,
            expiry_days=30,
            terms_conditions="Test terms"
        )
        
        assert program_id is not None
        assert len(program_id) > 0
        
        # Verify analytics reflect the new program
        analytics = marketing_system.get_referral_analytics()
        # Should have 0 referrals initially
        assert analytics["total_referrals"] == 0
    
    def test_referral_code_generation(self, marketing_system):
        """Test generating referral codes"""
        # First create a program
        program_id = marketing_system.create_referral_program(
            name="Test Program",
            reward_type="credit",
            reward_amount=25.0,
            referrer_reward=25.0,
            referee_reward=25.0
        )
        
        # Generate referral code
        referral_code = marketing_system.generate_referral_code(program_id, "user123")
        
        assert referral_code is not None
        assert len(referral_code) == 8  # Should be 8 characters
        assert referral_code.isupper()  # Should be uppercase
        
        # Generate another code for same user - should be different
        referral_code2 = marketing_system.generate_referral_code(program_id, "user123")
        assert referral_code != referral_code2
    
    def test_referral_tracking(self, marketing_system):
        """Test tracking referral signups"""
        # Create program and generate code
        program_id = marketing_system.create_referral_program(
            name="Test Program",
            reward_type="credit",
            reward_amount=25.0,
            referrer_reward=25.0,
            referee_reward=25.0
        )
        
        referral_code = marketing_system.generate_referral_code(program_id, "referrer123")
        
        # Track referral signup
        success = marketing_system.track_referral_signup(referral_code, "referee456")
        assert success is True
        
        # Verify analytics updated
        analytics = marketing_system.get_referral_analytics(program_id)
        assert analytics["total_referrals"] == 1
        assert analytics["completed_referrals"] == 1
        assert analytics["conversion_rate"] == 100.0
        
        # Try to track same referral again - should fail
        success2 = marketing_system.track_referral_signup(referral_code, "referee789")
        assert success2 is False
    
    def test_affiliate_partner_creation(self, marketing_system):
        """Test creating affiliate partners"""
        partner_id = marketing_system.create_affiliate_partner(
            name="Test Partner",
            email="partner@example.com",
            commission_rate=15.0,
            payment_method="paypal"
        )
        
        assert partner_id is not None
        assert len(partner_id) > 0
        
        # Verify analytics
        analytics = marketing_system.get_affiliate_analytics()
        assert analytics["total_partners"] == 1
        assert analytics["active_partners"] == 0  # Not approved yet
        
        # Try to create duplicate - should fail
        duplicate_id = marketing_system.create_affiliate_partner(
            name="Duplicate Partner",
            email="partner@example.com",  # Same email
            commission_rate=20.0
        )
        assert duplicate_id == ""  # Should return empty string on failure
    
    def test_affiliate_conversion_tracking(self, marketing_system):
        """Test tracking affiliate conversions"""
        # Create affiliate partner
        partner_id = marketing_system.create_affiliate_partner(
            name="Test Partner",
            email="partner@example.com",
            commission_rate=15.0
        )
        
        # Manually approve partner for testing
        import sqlite3
        conn = sqlite3.connect(marketing_system.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE affiliate_partners SET status = 'approved' WHERE id = ?", (partner_id,))
        cursor.execute("SELECT tracking_code FROM affiliate_partners WHERE id = ?", (partner_id,))
        tracking_code = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        
        # Track conversion
        success = marketing_system.track_affiliate_conversion(tracking_code, 100.0, "user123")
        assert success is True
        
        # Verify earnings updated
        analytics = marketing_system.get_affiliate_analytics()
        assert analytics["total_earnings"] == 15.0  # 15% of $100
        
        # Track with invalid code - should fail
        success2 = marketing_system.track_affiliate_conversion("INVALID", 50.0, "user456")
        assert success2 is False
    
    def test_social_share_template_creation(self, marketing_system):
        """Test creating social share templates"""
        template_id = marketing_system.create_social_share_template(
            platform="twitter",
            template_text="Check out this amazing transcription!",
            hashtags=["transcription", "AI", "productivity"],
            call_to_action="Try it yourself!",
            image_url="https://example.com/image.jpg"
        )
        
        assert template_id is not None
        assert len(template_id) > 0
    
    def test_share_url_generation(self, marketing_system):
        """Test generating share URLs"""
        # Create template
        template_id = marketing_system.create_social_share_template(
            platform="twitter",
            template_text="Check out this amazing transcription!",
            hashtags=["transcription", "AI"],
            call_to_action="Try it yourself!"
        )
        
        # Generate share URLs
        urls = marketing_system.generate_share_url(template_id, "user123", "content456")
        
        assert isinstance(urls, dict)
        assert "twitter" in urls
        assert "twitter.com/intent/tweet" in urls["twitter"]
        assert "transcription" in urls["twitter"]
        
        # Test with invalid template ID
        empty_urls = marketing_system.generate_share_url("invalid_id", "user123", "content456")
        assert empty_urls == {}
    
    def test_ab_test_creation(self, marketing_system):
        """Test creating A/B tests"""
        variants = [
            {
                "name": "Variant A",
                "description": "Original headline",
                "config": {"headline": "Original Headline"},
                "traffic_percentage": 50
            },
            {
                "name": "Variant B", 
                "description": "New headline",
                "config": {"headline": "New Improved Headline"},
                "traffic_percentage": 50
            }
        ]
        
        test_id = marketing_system.create_ab_test(
            name="Headline Test",
            description="Testing different headlines",
            variants=variants
        )
        
        assert test_id is not None
        assert len(test_id) > 0
    
    def test_ab_test_variant_assignment(self, marketing_system):
        """Test A/B test variant assignment"""
        # Create test
        variants = [
            {
                "name": "Variant A",
                "config": {"color": "blue"},
                "traffic_percentage": 60
            },
            {
                "name": "Variant B",
                "config": {"color": "red"}, 
                "traffic_percentage": 40
            }
        ]
        
        test_id = marketing_system.create_ab_test("Color Test", "Testing colors", variants)
        
        # Get variant for user
        variant = marketing_system.get_ab_test_variant(test_id, "user123")
        
        assert variant is not None
        assert "id" in variant
        assert "name" in variant
        assert "config" in variant
        assert variant["name"] in ["Variant A", "Variant B"]
        
        # Same user should get same variant consistently
        variant2 = marketing_system.get_ab_test_variant(test_id, "user123")
        assert variant["id"] == variant2["id"]
        
        # Different user might get different variant
        variant3 = marketing_system.get_ab_test_variant(test_id, "user456")
        assert variant3 is not None
        
        # Invalid test ID should return None
        invalid_variant = marketing_system.get_ab_test_variant("invalid_id", "user123")
        assert invalid_variant is None
    
    def test_ab_test_conversion_tracking(self, marketing_system):
        """Test tracking A/B test conversions"""
        # Create test and get variant
        variants = [{"name": "Variant A", "config": {}, "traffic_percentage": 100}]
        test_id = marketing_system.create_ab_test("Conversion Test", "Testing conversions", variants)
        variant = marketing_system.get_ab_test_variant(test_id, "user123")
        
        # Track conversion
        marketing_system.track_ab_test_conversion(variant["id"], "user123", 50.0)
        
        # Verify conversion was recorded
        conversion_analytics = marketing_system.get_conversion_analytics(1)
        ab_conversions = [c for c in conversion_analytics["by_type"] if c["type"] == "ab_test_conversion"]
        assert len(ab_conversions) > 0
        assert ab_conversions[0]["count"] == 1
        assert ab_conversions[0]["total_value"] == 50.0
    
    def test_landing_page_tracking(self, marketing_system):
        """Test landing page visit and conversion tracking"""
        # Track visit
        visit_id = marketing_system.track_landing_page_visit(
            page_url="https://example.com/landing",
            visitor_id="visitor123",
            session_id="session456",
            source="google",
            medium="cpc",
            campaign="test_campaign"
        )
        
        assert visit_id is not None
        assert len(visit_id) > 0
        
        # Track conversion
        marketing_system.track_landing_page_conversion(visit_id, 75.0)
        
        # Should not raise any errors
        assert True
    
    def test_conversion_analytics(self, marketing_system):
        """Test conversion analytics"""
        # Create some test conversions
        import sqlite3
        conn = sqlite3.connect(marketing_system.db_path)
        cursor = conn.cursor()
        
        # Insert test conversion events
        test_events = [
            ("event1", "user1", "signup", 0, "organic", None),
            ("event2", "user2", "subscription", 99, "referral", "ref123"),
            ("event3", "user3", "upgrade", 199, "affiliate", "aff456")
        ]
        
        for event_id, user_id, event_type, value, source, campaign_id in test_events:
            cursor.execute('''
                INSERT INTO conversion_events 
                (id, user_id, event_type, value, source, campaign_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (event_id, user_id, event_type, value, source, campaign_id))
        
        conn.commit()
        conn.close()
        
        # Get analytics
        analytics = marketing_system.get_conversion_analytics(30)
        
        assert "by_type" in analytics
        assert "by_source" in analytics
        assert len(analytics["by_type"]) > 0
        assert len(analytics["by_source"]) > 0
        
        # Verify data
        signup_events = [e for e in analytics["by_type"] if e["type"] == "signup"]
        assert len(signup_events) == 1
        assert signup_events[0]["count"] == 1
        
        referral_events = [e for e in analytics["by_source"] if e["source"] == "referral"]
        assert len(referral_events) == 1
        assert referral_events[0]["total_value"] == 99
    
    def test_referral_analytics_with_program_filter(self, marketing_system):
        """Test referral analytics with program-specific filtering"""
        # Create two programs
        program1_id = marketing_system.create_referral_program(
            name="Program 1", reward_type="credit", reward_amount=25.0,
            referrer_reward=25.0, referee_reward=25.0
        )
        
        program2_id = marketing_system.create_referral_program(
            name="Program 2", reward_type="credit", reward_amount=50.0,
            referrer_reward=50.0, referee_reward=50.0
        )
        
        # Generate referrals for each program
        code1 = marketing_system.generate_referral_code(program1_id, "user1")
        code2 = marketing_system.generate_referral_code(program2_id, "user2")
        
        marketing_system.track_referral_signup(code1, "referee1")
        marketing_system.track_referral_signup(code2, "referee2")
        
        # Test overall analytics
        overall_analytics = marketing_system.get_referral_analytics()
        assert overall_analytics["total_referrals"] == 2
        assert overall_analytics["completed_referrals"] == 2
        
        # Test program-specific analytics
        program1_analytics = marketing_system.get_referral_analytics(program1_id)
        assert program1_analytics["total_referrals"] == 1
        assert program1_analytics["completed_referrals"] == 1
        
        program2_analytics = marketing_system.get_referral_analytics(program2_id)
        assert program2_analytics["total_referrals"] == 1
        assert program2_analytics["completed_referrals"] == 1

def test_marketing_system_integration():
    """Integration test for the complete marketing system"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
        db_path = tmp_file.name
    
    try:
        marketing = MarketingGrowthSystem(db_path)
        
        # Create referral program
        program_id = marketing.create_referral_program(
            name="Integration Test Program",
            reward_type="credit",
            reward_amount=25.0,
            referrer_reward=25.0,
            referee_reward=25.0
        )
        
        # Generate referral code and track signup
        referral_code = marketing.generate_referral_code(program_id, "referrer123")
        marketing.track_referral_signup(referral_code, "referee456")
        
        # Create affiliate partner and track conversion
        partner_id = marketing.create_affiliate_partner(
            name="Integration Partner",
            email="integration@example.com",
            commission_rate=20.0
        )
        
        # Manually approve partner
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE affiliate_partners SET status = 'approved' WHERE id = ?", (partner_id,))
        cursor.execute("SELECT tracking_code FROM affiliate_partners WHERE id = ?", (partner_id,))
        tracking_code = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        
        marketing.track_affiliate_conversion(tracking_code, 200.0, "customer789")
        
        # Create social share template and generate URLs
        template_id = marketing.create_social_share_template(
            platform="twitter",
            template_text="Amazing integration test!",
            hashtags=["test", "integration"],
            call_to_action="Check it out!"
        )
        
        urls = marketing.generate_share_url(template_id, "user123", "content456")
        
        # Create A/B test and get variant
        variants = [
            {"name": "Control", "config": {"version": "original"}, "traffic_percentage": 50},
            {"name": "Treatment", "config": {"version": "new"}, "traffic_percentage": 50}
        ]
        test_id = marketing.create_ab_test("Integration Test", "Testing integration", variants)
        variant = marketing.get_ab_test_variant(test_id, "testuser")
        
        # Get all analytics
        referral_analytics = marketing.get_referral_analytics()
        affiliate_analytics = marketing.get_affiliate_analytics()
        conversion_analytics = marketing.get_conversion_analytics()
        
        # Verify everything worked
        assert referral_analytics["total_referrals"] == 1
        assert affiliate_analytics["total_partners"] == 1
        assert affiliate_analytics["total_earnings"] == 40.0  # 20% of $200
        assert len(urls) > 0
        assert variant is not None
        
        print("✅ Integration test passed successfully!")
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)

if __name__ == "__main__":
    # Run integration test
    test_marketing_system_integration()
    
    # Run pytest if available
    try:
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not available, running basic integration test only")
        print("Install pytest to run full test suite: pip install pytest")