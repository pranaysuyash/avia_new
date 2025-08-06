"""
Test suite for Enterprise Sales and Onboarding System
Tests all components including pricing calculator, demo scheduling,
trial management, white-label customization, and customer success tracking.
"""

import pytest
import datetime
from unittest.mock import Mock, patch
import json

from enterprise_sales_system import (
    EnterpriseSalesSystem, PricingTier, TrialStatus, OnboardingStage, 
    HealthScore, DemoRequest, TrialAccount, WhiteLabelConfig,
    PricingConfiguration, OnboardingWorkflow, CustomerHealthMetrics
)

class TestEnterpriseSalesSystem:
    """Test cases for EnterpriseSalesSystem"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.system = EnterpriseSalesSystem()
        
        # Mock streamlit session state
        with patch('streamlit.session_state', {}):
            self.system.load_data()
    
    def test_create_custom_pricing_starter_tier(self):
        """Test custom pricing creation for starter tier"""
        requirements = {
            'tier': 'starter',
            'user_count': 25,
            'contract_length': 12,
            'support_level': 'standard',
            'custom_features': ['Advanced Analytics Dashboard'],
            'transcription_hours': 50
        }
        
        config = self.system.create_custom_pricing("TestCorp", requirements)
        
        assert isinstance(config, PricingConfiguration)
        assert abs(config.base_price - 89.1) < 0.01  # 99 * (1 - 0.10 contract discount)
        assert config.per_user_price == 22.5  # 25 * (1 - 0.10)
        assert config.support_level == 'standard'
        assert 'Advanced Analytics Dashboard' in config.custom_features
        assert config.api_calls_included == 10000
    
    def test_create_custom_pricing_enterprise_tier_volume_discount(self):
        """Test custom pricing with volume discounts"""
        requirements = {
            'tier': 'enterprise',
            'user_count': 500,
            'contract_length': 36,
            'support_level': 'premium',
            'custom_features': ['Custom Integrations', 'Dedicated Success Manager'],
            'transcription_hours': 200
        }
        
        config = self.system.create_custom_pricing("BigCorp", requirements)
        
        # Should have both volume (20%) and contract (20%) discounts = 40% total
        expected_base_price = 999 * (1 - 0.40)
        expected_per_user_price = 75 * (1 - 0.40)
        
        assert config.base_price == expected_base_price
        assert config.per_user_price == expected_per_user_price
        assert config.support_level == 'premium'
        assert len(config.custom_features) == 2
    
    def test_schedule_demo(self):
        """Test demo scheduling functionality"""
        demo_request = DemoRequest(
            id="",
            company_name="TechStart Inc",
            contact_name="John Doe",
            email="john@techstart.com",
            phone="+1-555-0123",
            company_size="11-50",
            use_case="Meeting transcription and analysis",
            preferred_date=datetime.datetime(2024, 2, 15, 14, 0),
            preferred_time="2:00 PM",
            demo_type="live",
            status="pending",
            notes="Interested in enterprise features",
            created_at=datetime.datetime.now()
        )
        
        demo_id = self.system.schedule_demo(demo_request)
        
        assert demo_id is not None
        assert len(demo_id) > 0
        assert demo_id in self.system.demo_requests
        
        scheduled_demo = self.system.demo_requests[demo_id]
        assert scheduled_demo.company_name == "TechStart Inc"
        assert scheduled_demo.status == "scheduled"
        assert scheduled_demo.demo_type == "live"
    
    def test_create_trial_account_standard(self):
        """Test standard trial account creation"""
        trial = self.system.create_trial_account(
            "TestCompany", 
            "test@company.com", 
            "standard"
        )
        
        assert isinstance(trial, TrialAccount)
        assert trial.company_name == "TestCompany"
        assert trial.contact_email == "test@company.com"
        assert trial.trial_type == "standard"
        assert trial.status == TrialStatus.ACTIVE
        
        # Check trial duration (14 days for standard)
        duration = (trial.end_date - trial.start_date).days
        assert duration == 14
        
        # Check initial usage stats
        assert trial.usage_stats['transcription_hours'] == 0
        assert trial.usage_stats['api_calls'] == 0
        assert trial.usage_stats['storage_gb'] == 0
        assert trial.usage_stats['active_users'] == 0
        
        # Check trial goals
        assert len(trial.trial_goals) == 4
        assert "Complete initial setup" in trial.trial_goals
    
    def test_create_trial_account_extended(self):
        """Test extended trial account creation"""
        trial = self.system.create_trial_account(
            "ExtendedTestCorp", 
            "extended@test.com", 
            "extended"
        )
        
        # Check trial duration (30 days for extended)
        duration = (trial.end_date - trial.start_date).days
        assert duration == 30
        assert trial.trial_type == "extended"
    
    def test_create_trial_account_poc(self):
        """Test POC trial account creation"""
        trial = self.system.create_trial_account(
            "POCCompany", 
            "poc@company.com", 
            "poc"
        )
        
        # Check trial duration (60 days for POC)
        duration = (trial.end_date - trial.start_date).days
        assert duration == 60
        assert trial.trial_type == "poc"
    
    def test_create_whitelabel_config(self):
        """Test white-label configuration creation"""
        config_data = {
            'brand_name': 'CustomPlatform Pro',
            'logo_url': 'https://example.com/logo.png',
            'primary_color': '#2E8B57',
            'secondary_color': '#FF6347',
            'custom_domain': 'platform.customcorp.com',
            'custom_css': '.header { background: #2E8B57; }',
            'feature_toggles': {
                'transcription': True,
                'entity_extraction': True,
                'real_time_collaboration': True,
                'api_access': True,
                'advanced_analytics': False
            },
            'custom_integrations': ['Salesforce CRM', 'Microsoft Teams'],
            'support_contact': 'support@customcorp.com',
            'terms_url': 'https://customcorp.com/terms',
            'privacy_url': 'https://customcorp.com/privacy'
        }
        
        config = self.system.create_whitelabel_config("custom_client_001", config_data)
        
        assert isinstance(config, WhiteLabelConfig)
        assert config.client_id == "custom_client_001"
        assert config.brand_name == "CustomPlatform Pro"
        assert config.primary_color == "#2E8B57"
        assert config.custom_domain == "platform.customcorp.com"
        assert len(config.custom_integrations) == 2
        assert "Salesforce CRM" in config.custom_integrations
    
    def test_onboarding_workflow_creation(self):
        """Test onboarding workflow creation"""
        # Create trial account (which should create onboarding workflow)
        trial = self.system.create_trial_account("OnboardingTest", "test@onboarding.com")
        
        assert trial.id in self.system.onboarding_workflows
        
        workflow = self.system.onboarding_workflows[trial.id]
        assert isinstance(workflow, OnboardingWorkflow)
        assert workflow.client_id == trial.id
        assert workflow.current_stage == OnboardingStage.WELCOME
        assert len(workflow.stages_completed) == 0
        assert len(workflow.stage_progress) == 5  # 5 stages
    
    def test_update_onboarding_progress(self):
        """Test onboarding progress updates"""
        # Create trial and workflow
        trial = self.system.create_trial_account("ProgressTest", "progress@test.com")
        client_id = trial.id
        
        # Update welcome stage progress
        self.system.update_onboarding_progress(client_id, "welcome", 1.0)
        
        workflow = self.system.onboarding_workflows[client_id]
        assert workflow.stage_progress["welcome"] == 1.0
        assert "welcome" in workflow.stages_completed
        assert workflow.current_stage == OnboardingStage.SETUP
        
        # Update setup stage progress
        self.system.update_onboarding_progress(client_id, "setup", 0.5)
        
        workflow = self.system.onboarding_workflows[client_id]
        assert workflow.stage_progress["setup"] == 0.5
        assert "setup" not in workflow.stages_completed
        assert workflow.current_stage == OnboardingStage.SETUP
    
    def test_calculate_customer_health_excellent(self):
        """Test customer health calculation"""
        metrics = self.system.calculate_customer_health("excellent_client")
        
        assert isinstance(metrics, CustomerHealthMetrics)
        assert metrics.client_id == "excellent_client"
        assert metrics.health_score > 0  # Health score should be calculated
        assert isinstance(metrics.health_category, HealthScore)  # Should be a valid health category
        assert isinstance(metrics.usage_metrics, dict)
        assert len(metrics.feature_adoption) > 0
        assert isinstance(metrics.expansion_opportunities, list)
    
    def test_get_sales_analytics(self):
        """Test sales analytics generation"""
        # Add some test data
        demo_request = DemoRequest(
            id="", company_name="Test", contact_name="Test", email="test@test.com",
            phone="123", company_size="1-10", use_case="test", 
            preferred_date=datetime.datetime.now(), preferred_time="10:00 AM",
            demo_type="live", status="scheduled", notes="", created_at=datetime.datetime.now()
        )
        self.system.schedule_demo(demo_request)
        
        trial = self.system.create_trial_account("AnalyticsTest", "analytics@test.com")
        
        analytics = self.system.get_sales_analytics()
        
        assert isinstance(analytics, dict)
        assert 'total_demos_scheduled' in analytics
        assert 'active_trials' in analytics
        assert 'trial_conversion_rate' in analytics
        assert 'total_enterprise_clients' in analytics
        assert 'whitelabel_deployments' in analytics
        assert 'average_health_score' in analytics
        
        assert analytics['total_demos_scheduled'] >= 1
        assert analytics['active_trials'] >= 1
    
    def test_pricing_configuration_serialization(self):
        """Test that pricing configurations can be serialized"""
        requirements = {
            'tier': 'professional',
            'user_count': 100,
            'contract_length': 24,
            'support_level': 'premium',
            'custom_features': ['Custom Integrations'],
            'transcription_hours': 150
        }
        
        config = self.system.create_custom_pricing("SerializationTest", requirements)
        
        # Test that the config can be converted to dict (for JSON serialization)
        config_dict = {
            'base_price': config.base_price,
            'per_user_price': config.per_user_price,
            'per_hour_transcription': config.per_hour_transcription,
            'per_gb_storage': config.per_gb_storage,
            'api_calls_included': config.api_calls_included,
            'additional_api_cost': config.additional_api_cost,
            'support_level': config.support_level,
            'custom_features': config.custom_features
        }
        
        # Should be JSON serializable
        json_str = json.dumps(config_dict)
        assert len(json_str) > 0
        
        # Should be deserializable
        parsed = json.loads(json_str)
        assert parsed['support_level'] == 'premium'
        assert 'Custom Integrations' in parsed['custom_features']

class TestPricingCalculations:
    """Test pricing calculation logic"""
    
    def test_volume_discount_tiers(self):
        """Test volume discount calculations"""
        system = EnterpriseSalesSystem()
        
        # Test different user count tiers
        test_cases = [
            (25, 0.0),    # No discount
            (75, 0.10),   # 50+ discount
            (150, 0.15),  # 100+ discount
            (750, 0.20),  # 500+ discount
            (1500, 0.25)  # 1000+ discount
        ]
        
        for user_count, expected_volume_discount in test_cases:
            requirements = {
                'tier': 'enterprise',
                'user_count': user_count,
                'contract_length': 12,  # 10% contract discount
                'support_level': 'standard',
                'custom_features': [],
                'transcription_hours': 100
            }
            
            config = system.create_custom_pricing(f"test_{user_count}", requirements)
            
            # Calculate expected price with both volume and contract discounts
            base_enterprise_price = 999
            contract_discount = 0.10  # 12 month contract
            total_discount = expected_volume_discount + contract_discount
            expected_price = base_enterprise_price * (1 - total_discount)
            
            assert abs(config.base_price - expected_price) < 0.01, \
                f"User count {user_count}: expected {expected_price}, got {config.base_price}"
    
    def test_contract_length_discounts(self):
        """Test contract length discount calculations"""
        system = EnterpriseSalesSystem()
        
        test_cases = [
            (12, 0.10),   # 12 month discount
            (24, 0.15),   # 24 month discount
            (36, 0.20)    # 36 month discount
        ]
        
        for contract_length, expected_discount in test_cases:
            requirements = {
                'tier': 'professional',
                'user_count': 25,  # No volume discount
                'contract_length': contract_length,
                'support_level': 'standard',
                'custom_features': [],
                'transcription_hours': 100
            }
            
            config = system.create_custom_pricing(f"contract_{contract_length}", requirements)
            
            # Calculate expected price with discount
            base_professional_price = 299
            expected_price = base_professional_price * (1 - expected_discount)
            
            assert abs(config.base_price - expected_price) < 0.01, \
                f"Contract {contract_length}: expected {expected_price}, got {config.base_price}"
    
    def test_combined_discounts(self):
        """Test combined volume and contract discounts"""
        system = EnterpriseSalesSystem()
        
        requirements = {
            'tier': 'enterprise',
            'user_count': 500,    # 20% volume discount
            'contract_length': 36, # 20% contract discount
            'support_level': 'premium',
            'custom_features': ['Custom Integrations', 'Dedicated Success Manager'],
            'transcription_hours': 300
        }
        
        config = system.create_custom_pricing("combined_discount_test", requirements)
        
        # Should have 40% total discount (20% + 20%)
        base_enterprise_price = 999
        expected_price = base_enterprise_price * (1 - 0.40)
        
        assert abs(config.base_price - expected_price) < 0.01
        assert config.support_level == 'premium'
        assert len(config.custom_features) == 2

class TestHealthScoreCalculation:
    """Test customer health score calculation logic"""
    
    def test_health_score_categories(self):
        """Test health score category assignment"""
        system = EnterpriseSalesSystem()
        
        # The calculate_customer_health method uses simulated data
        # In a real implementation, we would test with actual usage data
        metrics = system.calculate_customer_health("test_client")
        
        assert isinstance(metrics.health_score, float)
        assert 0 <= metrics.health_score <= 100
        assert isinstance(metrics.health_category, HealthScore)
        
        # Test category boundaries
        if metrics.health_score >= 90:
            assert metrics.health_category == HealthScore.EXCELLENT
        elif metrics.health_score >= 70:
            assert metrics.health_category == HealthScore.GOOD
        elif metrics.health_score >= 50:
            assert metrics.health_category == HealthScore.FAIR
        elif metrics.health_score >= 30:
            assert metrics.health_category == HealthScore.POOR
        else:
            assert metrics.health_category == HealthScore.CRITICAL

if __name__ == "__main__":
    pytest.main([__file__, "-v"])