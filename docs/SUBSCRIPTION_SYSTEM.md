# Subscription & Payment System Documentation

## Overview

The subscription system provides comprehensive billing, usage tracking, and feature gating capabilities integrated with Stripe for payment processing.

## Features

### Pricing Tiers

1. **Free Tier**
   - 10 transcripts/month
   - 100 minutes/month
   - 1GB storage
   - Basic features
   - Community support

2. **Basic Tier** ($29/month or $290/year)
   - 50 transcripts/month
   - 500 minutes/month
   - 10GB storage
   - API access
   - Email support
   - Teams up to 5 members

3. **Pro Tier** ($99/month or $990/year)
   - 200 transcripts/month
   - 2000 minutes/month
   - 50GB storage
   - Advanced analytics
   - Priority support
   - Batch processing
   - Real-time collaboration
   - Teams up to 20 members

4. **Enterprise Tier** ($499/month or $4990/year)
   - Unlimited transcripts
   - Unlimited API calls
   - 500GB storage
   - Custom models
   - White label option
   - SSO & audit logs
   - Dedicated support
   - Unlimited team members

### Usage Tracking

The system tracks:
- Number of transcripts created
- Audio/video minutes processed
- Storage used (GB)
- API calls made

### Components

1. **Database Models** (`database/subscription_models.py`)
   - PricingPlan: Defines subscription tiers and limits
   - Subscription: User subscriptions with Stripe integration
   - Payment: Payment history
   - UsageRecord: Detailed usage tracking
   - Coupon: Discount codes
   - PaymentMethod: Saved payment methods
   - Invoice: Billing invoices

2. **Services**
   - **StripeService** (`services/stripe_service.py`): Handles Stripe integration
   - **SubscriptionService** (`services/subscription_service.py`): Manages subscriptions and usage

3. **API Endpoints** (`api/endpoints/subscription.py`)
   - GET `/api/subscriptions/plans` - Get pricing plans
   - GET `/api/subscriptions/current` - Get current subscription
   - POST `/api/subscriptions/create` - Create subscription
   - PUT `/api/subscriptions/update` - Update subscription
   - POST `/api/subscriptions/cancel` - Cancel subscription
   - POST `/api/subscriptions/checkout-session` - Create Stripe checkout
   - GET `/api/subscriptions/customer-portal` - Get Stripe portal URL
   - GET `/api/subscriptions/usage` - Get usage summary
   - POST `/api/subscriptions/usage/check` - Check usage limits
   - POST `/api/subscriptions/webhook` - Stripe webhook handler

4. **UI Components**
   - **Streamlit** (`streamlit_subscription_ui.py`): Web subscription management
   - **React Desktop** (`desktop_app/src/renderer/src/components/subscription/SubscriptionManager.tsx`)
   - **React Native Mobile** (`mobile/src/components/subscription/SubscriptionManager.tsx`)

5. **Usage Tracking Middleware** (`api/middleware/usage_tracking.py`)
   - Automatic API call tracking
   - Resource usage tracking
   - Usage limit enforcement

## Setup Instructions

### 1. Environment Variables

Add to your `.env` file:

```bash
# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Optional: Stripe Price IDs (if using existing products)
STRIPE_PRICE_BASIC_MONTHLY=price_...
STRIPE_PRICE_BASIC_YEARLY=price_...
STRIPE_PRICE_PRO_MONTHLY=price_...
STRIPE_PRICE_PRO_YEARLY=price_...
STRIPE_PRICE_ENTERPRISE_MONTHLY=price_...
STRIPE_PRICE_ENTERPRISE_YEARLY=price_...
```

### 2. Initialize Database

```bash
# Run database migrations
alembic upgrade head

# Initialize pricing plans
python database/init_pricing_plans.py
```

### 3. Setup Stripe Webhook

```bash
# For development (using Stripe CLI)
stripe listen --forward-to localhost:8000/api/subscriptions/webhook

# For production
python scripts/setup_stripe_webhook.py
```

### 4. Test the System

```bash
# Run the test script
python test_subscription_system.py
```

## Usage Examples

### Check Usage Before Creating Transcript

```python
# In transcription endpoint
allowed, message, usage_info = subscription_service.check_usage_limit(
    user_id=current_user.id,
    usage_type='transcripts',
    amount=1
)

if not allowed:
    raise HTTPException(
        status_code=402,  # Payment Required
        detail={
            'error': 'usage_limit_exceeded',
            'message': message,
            'usage': usage_info,
            'upgrade_url': '/subscription'
        }
    )
```

### Track Usage After Operation

```python
# After successful transcription
subscription_service.track_usage(
    user_id=current_user.id,
    usage_type='transcripts',
    quantity=1,
    resource_type='transcript',
    resource_id=transcript.id,
    description=f"Transcription: {transcript.title}"
)

# Track minutes
minutes = duration / 60.0
subscription_service.track_usage(
    user_id=current_user.id,
    usage_type='minutes',
    quantity=minutes,
    resource_type='transcript',
    resource_id=transcript.id
)
```

### Check Feature Access

```python
# Check if user has access to feature
has_api_access = subscription_service.check_feature_access(
    user_id=current_user.id,
    feature='api_access'
)

if not has_api_access:
    raise HTTPException(
        status_code=403,
        detail="API access requires Basic plan or higher"
    )
```

## Stripe Integration

### Webhook Events Handled

- `checkout.session.completed` - New subscription created
- `customer.subscription.created` - Subscription confirmed
- `customer.subscription.updated` - Plan changes
- `customer.subscription.deleted` - Cancellations
- `invoice.payment_succeeded` - Successful payments
- `invoice.payment_failed` - Failed payments
- `payment_method.attached` - New payment method
- `payment_method.detached` - Removed payment method

### Testing with Stripe

Use test card numbers:
- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`
- Authentication Required: `4000 0025 0000 3155`

## Frontend Integration

### Streamlit

```python
from streamlit_subscription_ui import SubscriptionUI

# In your app
subscription_ui = SubscriptionUI()
subscription_ui.render_main()
```

### React/React Native

```typescript
import SubscriptionManager from './components/subscription/SubscriptionManager';

// In your app
<SubscriptionManager />
```

## Monitoring & Analytics

### Usage Metrics

- Track usage patterns
- Monitor limit approaching
- Identify upgrade opportunities
- Analyze feature adoption

### Business Metrics

- MRR (Monthly Recurring Revenue)
- Churn rate
- Upgrade/downgrade patterns
- Popular plans

## Security Considerations

1. **Webhook Verification**: Always verify Stripe webhook signatures
2. **Payment Data**: Never store credit card details - use Stripe tokens
3. **Usage Limits**: Enforce limits before resource-intensive operations
4. **Feature Gating**: Check permissions at API level, not just UI
5. **Audit Trail**: Log all subscription changes and payment events

## Troubleshooting

### Common Issues

1. **Webhook not receiving events**
   - Check webhook secret is correct
   - Verify endpoint is accessible
   - Check Stripe dashboard for failed webhooks

2. **Usage not tracking**
   - Ensure subscription service is initialized
   - Check database connections
   - Verify usage types match expected values

3. **Payment failures**
   - Check Stripe logs
   - Verify API keys are correct
   - Test with Stripe test cards

### Debug Commands

```bash
# Check pricing plans
curl http://localhost:8000/api/subscriptions/plans

# Check user's subscription (with auth)
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/subscriptions/current

# Check usage
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/subscriptions/usage
```

## Future Enhancements

1. **Metered Billing**: Pay-as-you-go option
2. **Team Billing**: Consolidated billing for teams
3. **Usage Alerts**: Email notifications for usage thresholds
4. **Custom Plans**: Enterprise custom pricing
5. **Multiple Currencies**: International pricing
6. **Referral Program**: Discount codes for referrals
7. **Usage Analytics**: Detailed usage reports
8. **Billing Portal**: Self-service billing management