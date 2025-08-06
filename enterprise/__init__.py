"""
Enterprise Sales and Onboarding Package

Comprehensive enterprise customer lifecycle management including:
- Custom pricing calculator
- Demo scheduling and management
- Trial account management
- White-label customization
- Customer success tracking and health scores
- Onboarding workflows
"""

from .pricing_calculator import (
    EnterprisePricingCalculator,
    PricingRequest,
    PricingQuote,
    PricingBreakdown,
    EnterpriseFeatures,
    SupportLevel,
    FeatureTier,
    ContractDuration
)

from .demo_scheduler import (
    DemoScheduler,
    DemoRequest,
    DemoAppointment,
    DemoStatus,
    DemoType,
    TrialManager,
    TrialAccount,
    TrialStatus,
    OnboardingManager,
    OnboardingWorkflow,
    OnboardingStep,
    TimeSlot
)

from .white_label import (
    WhiteLabelManager,
    WhiteLabelConfig,
    WhiteLabelPreview,
    CustomizationLevel,
    ColorScheme,
    Typography,
    LogoAssets,
    CustomDomain,
    EmailCustomization,
    UICustomization
)

from .customer_success import (
    CustomerSuccessMetrics,
    CustomerMetadata,
    UsageMetrics,
    SupportMetrics,
    HealthScore,
    HealthStatus,
    HealthScoreWeights,
    RiskFactor,
    EngagementMetric
)

__version__ = "1.0.0"

__all__ = [
    # Pricing Calculator
    "EnterprisePricingCalculator",
    "PricingRequest",
    "PricingQuote",
    "PricingBreakdown",
    "EnterpriseFeatures",
    "SupportLevel",
    "FeatureTier",
    "ContractDuration",
    
    # Demo Scheduler
    "DemoScheduler",
    "DemoRequest",
    "DemoAppointment",
    "DemoStatus",
    "DemoType",
    "TimeSlot",
    
    # Trial Management
    "TrialManager",
    "TrialAccount",
    "TrialStatus",
    
    # Onboarding
    "OnboardingManager",
    "OnboardingWorkflow",
    "OnboardingStep",
    
    # White Label
    "WhiteLabelManager",
    "WhiteLabelConfig",
    "WhiteLabelPreview",
    "CustomizationLevel",
    "ColorScheme",
    "Typography",
    "LogoAssets",
    "CustomDomain",
    "EmailCustomization",
    "UICustomization",
    
    # Customer Success
    "CustomerSuccessMetrics",
    "CustomerMetadata",
    "UsageMetrics",
    "SupportMetrics",
    "HealthScore",
    "HealthStatus",
    "HealthScoreWeights",
    "RiskFactor",
    "EngagementMetric"
]