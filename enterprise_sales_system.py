"""
Enterprise Sales and Onboarding System
Handles custom pricing, demo scheduling, trials, white-label customization, 
onboarding workflows, and customer success tracking.
"""

import streamlit as st
import pandas as pd
import json
import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
# Email imports (for production use)
# import smtplib
# from email.mime.text import MimeText
# from email.mime.multipart import MimeMultipart
import plotly.express as px
import plotly.graph_objects as go

class PricingTier(Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"

class TrialStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    CONVERTED = "converted"
    CANCELLED = "cancelled"

class OnboardingStage(Enum):
    WELCOME = "welcome"
    SETUP = "setup"
    INTEGRATION = "integration"
    TRAINING = "training"
    LAUNCH = "launch"
    COMPLETE = "complete"

class HealthScore(Enum):
    EXCELLENT = "excellent"  # 90-100
    GOOD = "good"           # 70-89
    FAIR = "fair"           # 50-69
    POOR = "poor"           # 30-49
    CRITICAL = "critical"   # 0-29

@dataclass
class PricingConfiguration:
    """Custom pricing configuration for enterprise clients"""
    base_price: float
    per_user_price: float
    per_hour_transcription: float
    per_gb_storage: float
    api_calls_included: int
    additional_api_cost: float
    support_level: str
    custom_features: List[str]
    volume_discounts: Dict[str, float]
    contract_length_discount: Dict[str, float]

@dataclass
class DemoRequest:
    """Demo scheduling request"""
    id: str
    company_name: str
    contact_name: str
    email: str
    phone: str
    company_size: str
    use_case: str
    preferred_date: datetime.datetime
    preferred_time: str
    demo_type: str  # "live", "recorded", "self-guided"
    status: str
    notes: str
    created_at: datetime.datetime
    assigned_rep: Optional[str] = None

@dataclass
class TrialAccount:
    """Trial account management"""
    id: str
    company_name: str
    contact_email: str
    trial_type: str  # "standard", "extended", "poc"
    start_date: datetime.datetime
    end_date: datetime.datetime
    status: TrialStatus
    usage_stats: Dict[str, Any]
    conversion_probability: float
    assigned_success_manager: str
    trial_goals: List[str]
    progress_metrics: Dict[str, float]

@dataclass
class WhiteLabelConfig:
    """White-label customization configuration"""
    client_id: str
    brand_name: str
    logo_url: str
    primary_color: str
    secondary_color: str
    custom_domain: str
    custom_css: str
    feature_toggles: Dict[str, bool]
    custom_integrations: List[str]
    support_contact: str
    terms_url: str
    privacy_url: str

@dataclass
class OnboardingWorkflow:
    """Customer onboarding workflow tracking"""
    client_id: str
    current_stage: OnboardingStage
    stages_completed: List[str]
    stage_progress: Dict[str, float]
    assigned_specialist: str
    start_date: datetime.datetime
    target_completion: datetime.datetime
    custom_requirements: List[str]
    training_sessions: List[Dict[str, Any]]
    integration_status: Dict[str, str]

@dataclass
class CustomerHealthMetrics:
    """Customer success tracking and health scoring"""
    client_id: str
    health_score: float
    health_category: HealthScore
    usage_metrics: Dict[str, float]
    engagement_score: float
    support_tickets: int
    feature_adoption: Dict[str, bool]
    last_login: datetime.datetime
    contract_renewal_date: datetime.datetime
    risk_factors: List[str]
    success_milestones: List[str]
    expansion_opportunities: List[str]

class EnterpriseSalesSystem:
    """Main enterprise sales and onboarding system"""
    
    def __init__(self):
        self.pricing_configs = {}
        self.demo_requests = {}
        self.trial_accounts = {}
        self.whitelabel_configs = {}
        self.onboarding_workflows = {}
        self.customer_health = {}
        self.load_data()
    
    def load_data(self):
        """Load existing data from storage"""
        try:
            # In production, this would load from database
            # For demo, we'll use session state
            if 'enterprise_data' not in st.session_state:
                st.session_state.enterprise_data = {
                    'pricing_configs': {},
                    'demo_requests': {},
                    'trial_accounts': {},
                    'whitelabel_configs': {},
                    'onboarding_workflows': {},
                    'customer_health': {}
                }
            
            data = st.session_state.enterprise_data
            self.pricing_configs = data.get('pricing_configs', {})
            self.demo_requests = data.get('demo_requests', {})
            self.trial_accounts = data.get('trial_accounts', {})
            self.whitelabel_configs = data.get('whitelabel_configs', {})
            self.onboarding_workflows = data.get('onboarding_workflows', {})
            self.customer_health = data.get('customer_health', {})
        except Exception as e:
            st.error(f"Error loading enterprise data: {e}")
    
    def save_data(self):
        """Save data to storage"""
        try:
            st.session_state.enterprise_data = {
                'pricing_configs': self.pricing_configs,
                'demo_requests': self.demo_requests,
                'trial_accounts': self.trial_accounts,
                'whitelabel_configs': self.whitelabel_configs,
                'onboarding_workflows': self.onboarding_workflows,
                'customer_health': self.customer_health
            }
        except Exception as e:
            st.error(f"Error saving enterprise data: {e}")
    
    def create_custom_pricing(self, client_name: str, requirements: Dict[str, Any]) -> PricingConfiguration:
        """Create custom pricing configuration for enterprise client"""
        
        # Base pricing tiers
        base_pricing = {
            PricingTier.STARTER: {
                'base_price': 99,
                'per_user_price': 25,
                'per_hour_transcription': 2.0,
                'per_gb_storage': 5.0,
                'api_calls_included': 10000,
                'additional_api_cost': 0.01
            },
            PricingTier.PROFESSIONAL: {
                'base_price': 299,
                'per_user_price': 45,
                'per_hour_transcription': 1.5,
                'per_gb_storage': 3.0,
                'api_calls_included': 50000,
                'additional_api_cost': 0.008
            },
            PricingTier.ENTERPRISE: {
                'base_price': 999,
                'per_user_price': 75,
                'per_hour_transcription': 1.0,
                'per_gb_storage': 2.0,
                'api_calls_included': 200000,
                'additional_api_cost': 0.005
            }
        }
        
        # Calculate custom pricing based on requirements
        tier = PricingTier(requirements.get('tier', 'enterprise'))
        base = base_pricing[tier]
        
        # Volume discounts
        user_count = requirements.get('user_count', 1)
        volume_discount = 0
        if user_count >= 1000:
            volume_discount = 0.25
        elif user_count >= 500:
            volume_discount = 0.20
        elif user_count >= 100:
            volume_discount = 0.15
        elif user_count >= 50:
            volume_discount = 0.10
        
        # Contract length discounts
        contract_length = requirements.get('contract_length', 12)
        contract_discount = 0
        if contract_length >= 36:
            contract_discount = 0.20
        elif contract_length >= 24:
            contract_discount = 0.15
        elif contract_length >= 12:
            contract_discount = 0.10
        
        # Apply discounts
        total_discount = volume_discount + contract_discount
        
        config = PricingConfiguration(
            base_price=base['base_price'] * (1 - total_discount),
            per_user_price=base['per_user_price'] * (1 - total_discount),
            per_hour_transcription=base['per_hour_transcription'] * (1 - total_discount),
            per_gb_storage=base['per_gb_storage'] * (1 - total_discount),
            api_calls_included=base['api_calls_included'],
            additional_api_cost=base['additional_api_cost'],
            support_level=requirements.get('support_level', 'premium'),
            custom_features=requirements.get('custom_features', []),
            volume_discounts={'50+': 0.10, '100+': 0.15, '500+': 0.20, '1000+': 0.25},
            contract_length_discount={'12m': 0.10, '24m': 0.15, '36m': 0.20}
        )
        
        self.pricing_configs[client_name] = config
        self.save_data()
        return config
    
    def schedule_demo(self, demo_request: DemoRequest) -> str:
        """Schedule a demo for potential client"""
        demo_id = str(uuid.uuid4())
        demo_request.id = demo_id
        demo_request.created_at = datetime.datetime.now()
        demo_request.status = "scheduled"
        
        self.demo_requests[demo_id] = demo_request
        self.save_data()
        
        # Send confirmation email (in production)
        self._send_demo_confirmation(demo_request)
        
        return demo_id
    
    def create_trial_account(self, company_name: str, contact_email: str, 
                           trial_type: str = "standard") -> TrialAccount:
        """Create and manage trial accounts"""
        trial_id = str(uuid.uuid4())
        
        # Trial duration based on type
        duration_days = {
            "standard": 14,
            "extended": 30,
            "poc": 60
        }
        
        start_date = datetime.datetime.now()
        end_date = start_date + datetime.timedelta(days=duration_days[trial_type])
        
        trial = TrialAccount(
            id=trial_id,
            company_name=company_name,
            contact_email=contact_email,
            trial_type=trial_type,
            start_date=start_date,
            end_date=end_date,
            status=TrialStatus.ACTIVE,
            usage_stats={
                'transcription_hours': 0,
                'api_calls': 0,
                'storage_gb': 0,
                'active_users': 0
            },
            conversion_probability=0.5,
            assigned_success_manager="",
            trial_goals=[
                "Complete initial setup",
                "Process first batch of content",
                "Integrate with existing workflow",
                "Train team members"
            ],
            progress_metrics={
                'setup_completion': 0.0,
                'feature_adoption': 0.0,
                'user_engagement': 0.0,
                'integration_progress': 0.0
            }
        )
        
        self.trial_accounts[trial_id] = trial
        self.save_data()
        
        # Initialize onboarding workflow
        self._create_onboarding_workflow(trial_id, company_name)
        
        return trial
    
    def create_whitelabel_config(self, client_id: str, config_data: Dict[str, Any]) -> WhiteLabelConfig:
        """Create white-label customization configuration"""
        config = WhiteLabelConfig(
            client_id=client_id,
            brand_name=config_data.get('brand_name', 'Custom Platform'),
            logo_url=config_data.get('logo_url', ''),
            primary_color=config_data.get('primary_color', '#1f77b4'),
            secondary_color=config_data.get('secondary_color', '#ff7f0e'),
            custom_domain=config_data.get('custom_domain', ''),
            custom_css=config_data.get('custom_css', ''),
            feature_toggles=config_data.get('feature_toggles', {}),
            custom_integrations=config_data.get('custom_integrations', []),
            support_contact=config_data.get('support_contact', ''),
            terms_url=config_data.get('terms_url', ''),
            privacy_url=config_data.get('privacy_url', '')
        )
        
        self.whitelabel_configs[client_id] = config
        self.save_data()
        return config
    
    def _create_onboarding_workflow(self, client_id: str, company_name: str):
        """Create onboarding workflow for new client"""
        workflow = OnboardingWorkflow(
            client_id=client_id,
            current_stage=OnboardingStage.WELCOME,
            stages_completed=[],
            stage_progress={
                'welcome': 0.0,
                'setup': 0.0,
                'integration': 0.0,
                'training': 0.0,
                'launch': 0.0
            },
            assigned_specialist="",
            start_date=datetime.datetime.now(),
            target_completion=datetime.datetime.now() + datetime.timedelta(days=30),
            custom_requirements=[],
            training_sessions=[],
            integration_status={}
        )
        
        self.onboarding_workflows[client_id] = workflow
        self.save_data()
    
    def update_onboarding_progress(self, client_id: str, stage: str, progress: float):
        """Update onboarding progress for a client"""
        if client_id in self.onboarding_workflows:
            workflow = self.onboarding_workflows[client_id]
            workflow.stage_progress[stage] = progress
            
            # Update current stage based on progress
            if progress >= 1.0 and stage not in workflow.stages_completed:
                workflow.stages_completed.append(stage)
                
                # Move to next stage
                stages = list(OnboardingStage)
                current_index = stages.index(workflow.current_stage)
                if current_index < len(stages) - 1:
                    workflow.current_stage = stages[current_index + 1]
            
            self.save_data()
    
    def calculate_customer_health(self, client_id: str) -> CustomerHealthMetrics:
        """Calculate customer health score and metrics"""
        # In production, this would pull real usage data
        # For demo, we'll simulate metrics
        
        usage_metrics = {
            'daily_active_users': 85,
            'feature_adoption_rate': 72,
            'api_usage_trend': 15,  # % increase
            'support_ticket_resolution': 95,
            'login_frequency': 4.2  # days per week
        }
        
        # Calculate health score (0-100)
        health_score = (
            usage_metrics['daily_active_users'] * 0.3 +
            usage_metrics['feature_adoption_rate'] * 0.25 +
            min(usage_metrics['api_usage_trend'] * 2, 20) * 0.2 +
            usage_metrics['support_ticket_resolution'] * 0.15 +
            min(usage_metrics['login_frequency'] * 15, 20) * 0.1
        )
        
        # Determine health category
        if health_score >= 90:
            health_category = HealthScore.EXCELLENT
        elif health_score >= 70:
            health_category = HealthScore.GOOD
        elif health_score >= 50:
            health_category = HealthScore.FAIR
        elif health_score >= 30:
            health_category = HealthScore.POOR
        else:
            health_category = HealthScore.CRITICAL
        
        metrics = CustomerHealthMetrics(
            client_id=client_id,
            health_score=health_score,
            health_category=health_category,
            usage_metrics=usage_metrics,
            engagement_score=75.5,
            support_tickets=2,
            feature_adoption={
                'transcription': True,
                'entity_extraction': True,
                'real_time_collaboration': False,
                'api_integration': True,
                'advanced_analytics': False
            },
            last_login=datetime.datetime.now() - datetime.timedelta(days=1),
            contract_renewal_date=datetime.datetime.now() + datetime.timedelta(days=180),
            risk_factors=[
                "Low feature adoption in advanced analytics",
                "Decreased API usage last month"
            ] if health_score < 70 else [],
            success_milestones=[
                "Completed initial integration",
                "Processed 1000+ hours of content",
                "Achieved 90% user adoption"
            ],
            expansion_opportunities=[
                "Advanced analytics package",
                "Additional user licenses",
                "Custom integration development"
            ]
        )
        
        self.customer_health[client_id] = metrics
        self.save_data()
        return metrics
    
    def _send_demo_confirmation(self, demo_request: DemoRequest):
        """Send demo confirmation email"""
        # In production, this would send actual emails
        # For demo, we'll just log the action
        print(f"Demo confirmation sent to {demo_request.email}")
        print(f"Demo scheduled for {demo_request.preferred_date}")
    
    def get_sales_analytics(self) -> Dict[str, Any]:
        """Get sales and customer analytics"""
        total_demos = len(self.demo_requests)
        active_trials = len([t for t in self.trial_accounts.values() 
                           if t.status == TrialStatus.ACTIVE])
        
        # Calculate conversion rates
        converted_trials = len([t for t in self.trial_accounts.values() 
                              if t.status == TrialStatus.CONVERTED])
        conversion_rate = (converted_trials / len(self.trial_accounts) * 100) if self.trial_accounts else 0
        
        return {
            'total_demos_scheduled': total_demos,
            'active_trials': active_trials,
            'trial_conversion_rate': conversion_rate,
            'total_enterprise_clients': len(self.pricing_configs),
            'whitelabel_deployments': len(self.whitelabel_configs),
            'average_health_score': sum(h.health_score for h in self.customer_health.values()) / len(self.customer_health) if self.customer_health else 0
        }