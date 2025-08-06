"""
Enterprise Pricing Calculator

Calculates custom pricing for enterprise clients based on:
- Number of users
- Processing volume (hours/month)
- Features required
- Support level
- Contract duration
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, validator
import json

class SupportLevel(str, Enum):
    """Support level tiers"""
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class FeatureTier(str, Enum):
    """Feature access tiers"""
    ESSENTIAL = "essential"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"

class ContractDuration(str, Enum):
    """Contract duration options"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    BIANNUAL = "biannual"
    CUSTOM = "custom"

class EnterpriseFeatures(BaseModel):
    """Available enterprise features"""
    # Core features
    transcription: bool = True
    entity_extraction: bool = True
    summarization: bool = True
    
    # Advanced features
    speaker_diarization: bool = False
    multi_language: bool = False
    custom_vocabulary: bool = False
    
    # Enterprise features
    api_access: bool = False
    white_label: bool = False
    sso_integration: bool = False
    custom_integrations: bool = False
    dedicated_support: bool = False
    sla_guarantee: bool = False
    
    # Compliance features
    hipaa_compliance: bool = False
    gdpr_compliance: bool = False
    soc2_compliance: bool = False
    data_residency: bool = False

class PricingRequest(BaseModel):
    """Enterprise pricing calculation request"""
    company_name: str
    contact_email: str
    
    # Usage parameters
    user_count: int = Field(ge=1, description="Number of users")
    monthly_hours: float = Field(ge=0, description="Processing hours per month")
    storage_gb: float = Field(ge=0, description="Storage required in GB")
    
    # Service parameters
    support_level: SupportLevel = SupportLevel.STANDARD
    feature_tier: FeatureTier = FeatureTier.PROFESSIONAL
    contract_duration: ContractDuration = ContractDuration.ANNUAL
    
    # Custom features
    features: EnterpriseFeatures = Field(default_factory=EnterpriseFeatures)
    
    # Additional requirements
    custom_requirements: Optional[str] = None
    
    @validator('user_count')
    def validate_enterprise_users(cls, v):
        if v < 10:
            raise ValueError("Enterprise plans require minimum 10 users")
        return v

class PricingBreakdown(BaseModel):
    """Detailed pricing breakdown"""
    base_price: float
    user_price: float
    usage_price: float
    storage_price: float
    feature_price: float
    support_price: float
    
    subtotal: float
    discount_percentage: float
    discount_amount: float
    
    monthly_price: float
    annual_price: float
    total_contract_value: float

class PricingQuote(BaseModel):
    """Enterprise pricing quote"""
    quote_id: str
    created_at: datetime
    valid_until: datetime
    
    request: PricingRequest
    breakdown: PricingBreakdown
    
    # Payment terms
    payment_terms: str
    billing_frequency: str
    
    # Special conditions
    notes: Optional[str] = None
    custom_terms: Optional[List[str]] = None

class EnterprisePricingCalculator:
    """Calculate custom enterprise pricing"""
    
    def __init__(self):
        # Base pricing (per user per month)
        self.base_user_prices = {
            FeatureTier.ESSENTIAL: 50,
            FeatureTier.PROFESSIONAL: 100,
            FeatureTier.ENTERPRISE: 200,
            FeatureTier.CUSTOM: 300
        }
        
        # Usage pricing (per hour)
        self.usage_prices = {
            "transcription": 0.50,
            "processing": 0.30,
            "storage_per_gb": 0.10
        }
        
        # Support level multipliers
        self.support_multipliers = {
            SupportLevel.BASIC: 1.0,
            SupportLevel.STANDARD: 1.2,
            SupportLevel.PREMIUM: 1.5,
            SupportLevel.ENTERPRISE: 2.0
        }
        
        # Contract duration discounts
        self.duration_discounts = {
            ContractDuration.MONTHLY: 0.0,
            ContractDuration.QUARTERLY: 0.05,
            ContractDuration.ANNUAL: 0.15,
            ContractDuration.BIANNUAL: 0.25,
            ContractDuration.CUSTOM: 0.20
        }
        
        # Feature prices (monthly)
        self.feature_prices = {
            "speaker_diarization": 500,
            "multi_language": 1000,
            "custom_vocabulary": 800,
            "api_access": 2000,
            "white_label": 5000,
            "sso_integration": 1500,
            "custom_integrations": 3000,
            "dedicated_support": 2500,
            "sla_guarantee": 1000,
            "hipaa_compliance": 3000,
            "gdpr_compliance": 2000,
            "soc2_compliance": 2500,
            "data_residency": 4000
        }
    
    def calculate_base_price(self, request: PricingRequest) -> float:
        """Calculate base price based on users and tier"""
        base_per_user = self.base_user_prices[request.feature_tier]
        
        # Volume discounts for users
        if request.user_count >= 1000:
            base_per_user *= 0.7
        elif request.user_count >= 500:
            base_per_user *= 0.8
        elif request.user_count >= 100:
            base_per_user *= 0.9
        elif request.user_count >= 50:
            base_per_user *= 0.95
        
        return base_per_user * request.user_count
    
    def calculate_usage_price(self, request: PricingRequest) -> float:
        """Calculate usage-based pricing"""
        hourly_rate = self.usage_prices["transcription"]
        
        # Volume discounts for usage
        if request.monthly_hours >= 10000:
            hourly_rate *= 0.6
        elif request.monthly_hours >= 5000:
            hourly_rate *= 0.7
        elif request.monthly_hours >= 1000:
            hourly_rate *= 0.8
        elif request.monthly_hours >= 500:
            hourly_rate *= 0.9
        
        usage_price = request.monthly_hours * hourly_rate
        storage_price = request.storage_gb * self.usage_prices["storage_per_gb"]
        
        return usage_price + storage_price
    
    def calculate_feature_price(self, request: PricingRequest) -> float:
        """Calculate additional feature pricing"""
        total_feature_price = 0
        
        features_dict = request.features.dict()
        for feature, enabled in features_dict.items():
            if enabled and feature in self.feature_prices:
                total_feature_price += self.feature_prices[feature]
        
        return total_feature_price
    
    def calculate_support_price(self, request: PricingRequest) -> float:
        """Calculate support tier pricing"""
        base_support = 500  # Base support cost
        multiplier = self.support_multipliers[request.support_level]
        
        # Scale support cost with user count
        user_factor = 1 + (request.user_count / 100) * 0.1
        
        return base_support * multiplier * user_factor
    
    def apply_discounts(self, subtotal: float, request: PricingRequest) -> tuple[float, float]:
        """Apply contract duration and volume discounts"""
        discount_percentage = self.duration_discounts[request.contract_duration]
        
        # Additional volume discount for large contracts
        if subtotal > 50000:
            discount_percentage += 0.10
        elif subtotal > 25000:
            discount_percentage += 0.05
        
        # Cap maximum discount
        discount_percentage = min(discount_percentage, 0.35)
        
        discount_amount = subtotal * discount_percentage
        
        return discount_percentage, discount_amount
    
    def generate_quote(self, request: PricingRequest) -> PricingQuote:
        """Generate complete pricing quote"""
        # Calculate components
        base_price = self.calculate_base_price(request)
        usage_price = self.calculate_usage_price(request)
        feature_price = self.calculate_feature_price(request)
        support_price = self.calculate_support_price(request)
        
        # User and storage breakdown
        user_price = base_price
        storage_price = request.storage_gb * self.usage_prices["storage_per_gb"]
        
        # Calculate subtotal
        subtotal = base_price + usage_price + feature_price + support_price
        
        # Apply discounts
        discount_percentage, discount_amount = self.apply_discounts(subtotal, request)
        
        # Final pricing
        monthly_price = subtotal - discount_amount
        annual_price = monthly_price * 12
        
        # Contract value
        contract_months = {
            ContractDuration.MONTHLY: 1,
            ContractDuration.QUARTERLY: 3,
            ContractDuration.ANNUAL: 12,
            ContractDuration.BIANNUAL: 24,
            ContractDuration.CUSTOM: 12
        }
        
        total_contract_value = monthly_price * contract_months[request.contract_duration]
        
        # Create breakdown
        breakdown = PricingBreakdown(
            base_price=base_price,
            user_price=user_price,
            usage_price=usage_price - storage_price,
            storage_price=storage_price,
            feature_price=feature_price,
            support_price=support_price,
            subtotal=subtotal,
            discount_percentage=discount_percentage * 100,
            discount_amount=discount_amount,
            monthly_price=monthly_price,
            annual_price=annual_price,
            total_contract_value=total_contract_value
        )
        
        # Generate quote
        quote = PricingQuote(
            quote_id=f"ENT-{datetime.now().strftime('%Y%m%d')}-{request.company_name[:3].upper()}",
            created_at=datetime.now(),
            valid_until=datetime.now() + timedelta(days=30),
            request=request,
            breakdown=breakdown,
            payment_terms=self._get_payment_terms(request),
            billing_frequency=self._get_billing_frequency(request),
            notes=self._generate_notes(request),
            custom_terms=self._get_custom_terms(request)
        )
        
        return quote
    
    def _get_payment_terms(self, request: PricingRequest) -> str:
        """Get payment terms based on contract"""
        if request.contract_duration == ContractDuration.ANNUAL:
            return "Net 30, Annual payment"
        elif request.contract_duration == ContractDuration.BIANNUAL:
            return "Net 30, Annual payment with 2-year commitment"
        else:
            return "Net 30, Monthly payment"
    
    def _get_billing_frequency(self, request: PricingRequest) -> str:
        """Get billing frequency"""
        if request.contract_duration in [ContractDuration.ANNUAL, ContractDuration.BIANNUAL]:
            return "Annual"
        elif request.contract_duration == ContractDuration.QUARTERLY:
            return "Quarterly"
        else:
            return "Monthly"
    
    def _generate_notes(self, request: PricingRequest) -> str:
        """Generate quote notes"""
        notes = []
        
        if request.user_count >= 100:
            notes.append("Volume discount applied for 100+ users")
        
        if request.monthly_hours >= 1000:
            notes.append("Volume discount applied for high usage")
        
        if request.support_level == SupportLevel.ENTERPRISE:
            notes.append("Includes 24/7 dedicated support with 1-hour SLA")
        
        if request.features.white_label:
            notes.append("White-label customization included")
        
        if any([request.features.hipaa_compliance, request.features.gdpr_compliance, request.features.soc2_compliance]):
            notes.append("Compliance certifications included")
        
        return "; ".join(notes) if notes else "Standard enterprise terms apply"
    
    def _get_custom_terms(self, request: PricingRequest) -> List[str]:
        """Get custom terms for the quote"""
        terms = [
            "Price valid for 30 days",
            "Subject to standard enterprise agreement",
            "Professional services available separately"
        ]
        
        if request.features.sla_guarantee:
            terms.append("99.9% uptime SLA included")
        
        if request.features.dedicated_support:
            terms.append("Dedicated customer success manager included")
        
        if request.features.custom_integrations:
            terms.append("Up to 40 hours of custom integration support included")
        
        return terms
    
    def export_quote(self, quote: PricingQuote, format: str = "json") -> str:
        """Export quote in various formats"""
        if format == "json":
            return quote.json(indent=2)
        elif format == "text":
            return self._format_quote_text(quote)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _format_quote_text(self, quote: PricingQuote) -> str:
        """Format quote as readable text"""
        return f"""
ENTERPRISE PRICING QUOTE
========================

Quote ID: {quote.quote_id}
Date: {quote.created_at.strftime('%B %d, %Y')}
Valid Until: {quote.valid_until.strftime('%B %d, %Y')}

Company: {quote.request.company_name}
Contact: {quote.request.contact_email}

PRICING BREAKDOWN
-----------------
Base Price (Users): ${quote.breakdown.base_price:,.2f}
Usage Price: ${quote.breakdown.usage_price:,.2f}
Storage Price: ${quote.breakdown.storage_price:,.2f}
Features: ${quote.breakdown.feature_price:,.2f}
Support: ${quote.breakdown.support_price:,.2f}

Subtotal: ${quote.breakdown.subtotal:,.2f}
Discount ({quote.breakdown.discount_percentage:.0f}%): -${quote.breakdown.discount_amount:,.2f}

TOTAL MONTHLY: ${quote.breakdown.monthly_price:,.2f}
TOTAL ANNUAL: ${quote.breakdown.annual_price:,.2f}

CONTRACT VALUE: ${quote.breakdown.total_contract_value:,.2f}

Payment Terms: {quote.payment_terms}
Billing: {quote.billing_frequency}

Notes: {quote.notes}

Terms & Conditions:
{chr(10).join(f'- {term}' for term in quote.custom_terms)}
"""

# Example usage
if __name__ == "__main__":
    calculator = EnterprisePricingCalculator()
    
    # Example enterprise request
    request = PricingRequest(
        company_name="Acme Corporation",
        contact_email="enterprise@acme.com",
        user_count=150,
        monthly_hours=5000,
        storage_gb=500,
        support_level=SupportLevel.PREMIUM,
        feature_tier=FeatureTier.ENTERPRISE,
        contract_duration=ContractDuration.ANNUAL,
        features=EnterpriseFeatures(
            speaker_diarization=True,
            multi_language=True,
            api_access=True,
            sso_integration=True,
            gdpr_compliance=True
        )
    )
    
    quote = calculator.generate_quote(request)
    print(calculator.export_quote(quote, "text"))