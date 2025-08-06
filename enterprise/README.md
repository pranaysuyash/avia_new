# Enterprise Sales and Onboarding System

A comprehensive enterprise customer lifecycle management system that handles pricing, demos, trials, white-labeling, and customer success.

## Features

### 1. **Enterprise Pricing Calculator**
- Dynamic pricing based on users, usage, and features
- Volume discounts and contract duration incentives
- Support for multiple tiers and customization levels
- Detailed pricing breakdowns and quote generation
- Export quotes in multiple formats

### 2. **Demo Scheduling**
- Automated demo appointment scheduling
- Multiple demo types (Discovery, Technical, Executive)
- Calendar integration and availability management
- Automated reminders and follow-ups
- Demo notes and outcome tracking

### 3. **Trial Management**
- Configurable trial accounts with usage limits
- Trial activation and expiration tracking
- Usage monitoring and limit enforcement
- Engagement scoring and conversion tracking
- Automated trial extension workflows

### 4. **White-Label Customization**
- Complete brand customization (logos, colors, typography)
- Multiple customization levels (Basic to Enterprise)
- Custom domain support with SSL
- Email template customization
- UI/UX customization with custom CSS/JS
- Preview generation and configuration export

### 5. **Customer Success Tracking**
- Comprehensive health score calculation
- Multi-factor scoring (usage, adoption, engagement, support, contract)
- Risk factor identification and alerts
- Actionable recommendations
- Historical tracking and trend analysis
- Executive dashboards and reporting

### 6. **Onboarding Workflows**
- Customizable onboarding steps
- Progress tracking and completion metrics
- Required vs optional steps
- Time estimates and milestone tracking
- Automated reminders and escalations

## Installation

```bash
# The enterprise package is included with the main application
# Ensure all dependencies are installed
pip install -r requirements.txt
```

## Usage

### Pricing Calculator

```python
from enterprise import EnterprisePricingCalculator, PricingRequest, EnterpriseFeatures

calculator = EnterprisePricingCalculator()

# Create pricing request
request = PricingRequest(
    company_name="Acme Corporation",
    contact_email="enterprise@acme.com",
    user_count=150,
    monthly_hours=5000,
    storage_gb=500,
    support_level="premium",
    feature_tier="enterprise",
    contract_duration="annual",
    features=EnterpriseFeatures(
        speaker_diarization=True,
        multi_language=True,
        api_access=True,
        white_label=True,
        sso_integration=True
    )
)

# Generate quote
quote = calculator.generate_quote(request)
print(f"Monthly Price: ${quote.breakdown.monthly_price:,.2f}")
print(f"Annual Price: ${quote.breakdown.annual_price:,.2f}")
```

### Demo Scheduling

```python
from enterprise import DemoScheduler, DemoRequest
from datetime import date, timedelta

scheduler = DemoScheduler()

# Check available slots
slots = scheduler.get_available_slots(
    start_date=date.today(),
    end_date=date.today() + timedelta(days=7),
    timezone="America/New_York"
)

# Schedule demo
demo_request = DemoRequest(
    company_name="Acme Corp",
    contact_name="John Doe",
    contact_email="john@acme.com",
    demo_type="technical",
    preferred_dates=[date.today() + timedelta(days=2)],
    timezone="America/New_York",
    use_case="Automated transcription for customer calls"
)

appointment = await scheduler.schedule_demo(demo_request, slots[0])
```

### Trial Management

```python
from enterprise import TrialManager

trial_manager = TrialManager()

# Create trial
trial = await trial_manager.create_trial(
    organization_id="org_123",
    duration_days=14,
    custom_limits={
        "user_limit": 10,
        "processing_hours_limit": 20.0,
        "storage_gb_limit": 10.0
    }
)

# Activate trial
await trial_manager.activate_trial(trial.id)

# Check usage
usage = await trial_manager.check_trial_limits(trial.id)
print(f"Processing hours used: {usage['processing_hours']['percentage']:.1f}%")
```

### White-Label Customization

```python
from enterprise import WhiteLabelManager, CustomizationLevel, ColorScheme

manager = WhiteLabelManager()

# Create white-label configuration
config = manager.create_config(
    organization_id="acme_corp",
    brand_name="Acme Transcription",
    customization_level=CustomizationLevel.ADVANCED,
    colors=ColorScheme(
        primary="#1a73e8",
        secondary="#5f6368",
        accent="#34a853",
        background="#ffffff",
        text="#202124"
    ),
    custom_domain={
        "domain": "acme.com",
        "subdomain": "transcribe"
    }
)

# Generate CSS
css = manager.generate_css(config)

# Generate preview
preview_html = WhiteLabelPreview.generate_preview_html(config)
```

### Customer Success Tracking

```python
from enterprise import CustomerSuccessMetrics, CustomerMetadata, UsageMetrics

cs_metrics = CustomerSuccessMetrics()

# Add usage metrics
usage = UsageMetrics(
    period_start=datetime.now() - timedelta(days=30),
    period_end=datetime.now(),
    total_users=50,
    active_users=35,
    processing_hours=250.5,
    features_used={
        "transcription": 1200,
        "entity_extraction": 800,
        "api_access": 5000
    }
)

# Calculate health score
health_score = cs_metrics.calculate_health_score(
    organization_id="acme_corp",
    metadata=customer_metadata,
    current_metrics=usage,
    support_metrics=support_metrics
)

print(f"Health Score: {health_score.overall_score:.1f} ({health_score.status})")
print(f"Risk Factors: {health_score.risk_factors}")
```

## Running the Demo

```bash
streamlit run demo_enterprise_sales.py
```

This will launch the Enterprise Sales & Onboarding Portal with:
- Interactive pricing calculator
- Demo scheduling interface
- Trial management dashboard
- White-label customization preview
- Customer success dashboard
- Onboarding workflow tracker

## Configuration

### Environment Variables

```bash
# Email notifications (for demo scheduling)
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# White-label storage
WHITE_LABEL_STORAGE_PATH=./white_label_configs

# Default trial settings
DEFAULT_TRIAL_DURATION=14
DEFAULT_TRIAL_USER_LIMIT=5
DEFAULT_TRIAL_PROCESSING_HOURS=10.0
```

### Health Score Weights

Customize health score calculation weights:

```python
from enterprise import HealthScoreWeights

custom_weights = HealthScoreWeights(
    usage_weight=0.35,      # Increase usage importance
    adoption_weight=0.25,
    engagement_weight=0.20,
    support_weight=0.10,
    contract_weight=0.10
)

cs_metrics = CustomerSuccessMetrics(weights=custom_weights)
```

## Integration with Main Application

### Pricing Integration

```python
# In your subscription module
from enterprise import EnterprisePricingCalculator

@app.post("/api/enterprise/quote")
async def generate_enterprise_quote(request: PricingRequest):
    calculator = EnterprisePricingCalculator()
    quote = calculator.generate_quote(request)
    
    # Store quote
    save_quote_to_database(quote)
    
    # Send to customer
    await send_quote_email(quote)
    
    return quote
```

### Trial Integration

```python
# In your user registration module
from enterprise import TrialManager

async def create_enterprise_trial(organization: Organization):
    trial_manager = TrialManager()
    
    # Create trial
    trial = await trial_manager.create_trial(
        organization_id=organization.id,
        duration_days=14
    )
    
    # Create trial users
    await create_trial_users(organization, trial)
    
    # Send welcome email
    await send_trial_welcome_email(organization, trial)
    
    return trial
```

### White-Label Integration

```python
# In your application middleware
from enterprise import WhiteLabelManager

@app.middleware("http")
async def white_label_middleware(request: Request, call_next):
    # Get organization from subdomain/header
    org_id = get_organization_id(request)
    
    if org_id:
        manager = WhiteLabelManager()
        config = manager.get_config(org_id)
        
        if config:
            # Inject white-label CSS
            request.state.white_label_css = manager.generate_css(config)
            request.state.white_label_config = config
    
    response = await call_next(request)
    return response
```

## Best Practices

### 1. **Pricing Strategy**
- Review and update pricing tiers quarterly
- Monitor competitor pricing
- A/B test discount strategies
- Track quote-to-close conversion rates

### 2. **Demo Management**
- Keep demo slots to 45 minutes
- Send agenda 24 hours before
- Record demos for training
- Track demo-to-trial conversion

### 3. **Trial Optimization**
- Set appropriate usage limits
- Monitor engagement daily
- Proactive outreach at 50% duration
- Offer extensions for engaged users

### 4. **Customer Success**
- Review health scores weekly
- Act on risk factors immediately
- Schedule quarterly business reviews
- Track NPS and satisfaction scores

### 5. **White-Label Management**
- Test configurations thoroughly
- Version control customizations
- Monitor brand guideline compliance
- Regular security audits for custom domains

## Architecture

```
enterprise/
├── pricing_calculator.py    # Pricing engine and quote generation
├── demo_scheduler.py        # Demo scheduling and management
├── white_label.py          # White-label customization system
├── customer_success.py     # Health scoring and success metrics
├── __init__.py            # Package initialization
└── README.md              # This file

Integration Points:
├── Database Models        # Organization, Trial, Quote tables
├── API Endpoints         # REST APIs for each module
├── Notification System   # Email/SMS for demos and trials
├── Authentication       # SSO and enterprise auth
└── Analytics           # Usage tracking and reporting
```

## Troubleshooting

### Common Issues

1. **Quote Generation Errors**
   - Verify all required fields are provided
   - Check feature compatibility with tier
   - Ensure user count meets minimum (10)

2. **Demo Scheduling Conflicts**
   - Check timezone settings
   - Verify business hours configuration
   - Clear expired appointments

3. **Trial Limit Exceeded**
   - Monitor usage in real-time
   - Set up alerts at 80% usage
   - Implement graceful degradation

4. **White-Label CSS Not Loading**
   - Verify configuration is active
   - Check domain SSL certificate
   - Clear browser cache

5. **Health Score Calculation**
   - Ensure sufficient historical data
   - Verify metric collection is working
   - Check weight configuration totals 1.0

## Future Enhancements

- [ ] Salesforce CRM integration
- [ ] Advanced revenue forecasting
- [ ] Multi-currency support
- [ ] Enterprise onboarding automation
- [ ] Advanced analytics and BI dashboards
- [ ] Contract lifecycle management
- [ ] Partner portal functionality

## License

This enterprise system is part of the NER Video Transcription platform.