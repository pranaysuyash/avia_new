# PostHog Analytics Setup

This guide explains how to use PostHog for funnel tracking and user analytics across the platform.

## Overview

PostHog is configured to track:
- **Conversion Funnels**: User journey from signup to paid subscription
- **Feature Adoption**: How users discover and use features
- **Engagement Metrics**: Time spent, actions taken, retention
- **A/B Testing**: Feature flags and experiments
- **Session Recording**: User behavior replay (privacy-compliant)

## Configuration

### 1. Environment Variables

Set these in your `.env` file:

```env
# PostHog Configuration
REACT_APP_POSTHOG_KEY=your-project-api-key
REACT_APP_POSTHOG_HOST=https://app.posthog.com  # or your self-hosted instance
VITE_POSTHOG_KEY=your-project-api-key  # For Vite projects
```

### 2. Key Funnels Tracked

#### Onboarding Funnel
1. `signup_started` → User begins registration
2. `signup_completed` → Account created
3. `onboarding_started` → Welcome flow begins
4. `onboarding_step_completed` → Each step completion
5. `onboarding_completed` → User ready to use app

#### Upload → Transcription Funnel
1. `upload_initiated` → User visits upload page
2. `upload_file_selected` → File chosen
3. `upload_started` → Upload begins
4. `upload_completed` → File uploaded successfully
5. `transcription_started` → Processing begins
6. `transcription_completed` → Results ready
7. `transcription_viewed` → User views results

#### Engagement Funnel
1. `transcript_edited` → User edits transcript
2. `segment_played` → Audio segment played
3. `transcript_searched` → Search used
4. `transcript_exported` → Export initiated
5. `speaker_renamed` → Speaker management used

#### Conversion Funnel
1. `pricing_viewed` → Pricing page visited
2. `plan_selected` → Plan chosen
3. `checkout_started` → Payment flow begins
4. `payment_entered` → Card details added
5. `subscription_completed` → Paid customer

## Implementation

### Basic Event Tracking

```typescript
import { trackFunnelEvent } from '@/utils/posthog';

// Track a simple event
trackFunnelEvent('feature_used', {
  feature: 'speaker_detection',
  success: true
});

// Track with the predefined events
trackFunnelEvent('UPLOAD_COMPLETED', {
  file_size: file.size,
  file_type: file.type,
  duration_ms: uploadTime
});
```

### User Identification

```typescript
import { identifyUser, setUserProperties } from '@/utils/posthog';

// After login/signup
identifyUser(user.id, {
  email: user.email,
  name: user.name,
  plan: user.subscription_tier,
  created_at: user.created_at
});

// Update user properties
setUserProperties({
  total_transcriptions: 42,
  preferred_language: 'en',
  team_size: 5
});
```

### Feature Flags

```typescript
import { getFeatureFlag } from '@/utils/posthog';

// Check if feature is enabled for user
const showNewEditor = getFeatureFlag('new_editor_ui');

if (showNewEditor) {
  // Show new UI
}
```

### Conversion Tracking

```typescript
import { trackConversionStep } from '@/utils/posthog';

// Track each step of the conversion funnel
trackConversionStep('pricing_viewed');

trackConversionStep('plan_selected', {
  plan: 'professional',
  price: 49,
  currency: 'USD'
});

trackConversionStep('subscription_completed', {
  plan: 'professional',
  payment_method: 'card',
  mrr: 49
});
```

### Custom Funnel Components

Use the pre-built tracking components:

```typescript
// Automatically tracked file uploader
import { TrackedFileUploader } from '@/components/upload/TrackedFileUploader';

<TrackedFileUploader
  onUploadComplete={(fileKey) => {
    // Your logic here
  }}
/>

// Automatically tracked transcript viewer
import { TrackedInteractiveTranscript } from '@/components/transcription/TrackedInteractiveTranscript';

<TrackedInteractiveTranscript
  segments={segments}
  audioUrl={audioUrl}
  transcriptionId={transcriptionId}
/>
```

## Dashboard Setup

### Key Metrics to Monitor

1. **Conversion Rate**: Visitors → Signups → Paid
2. **Feature Adoption**: % of users using each feature
3. **Retention**: Daily/Weekly/Monthly active users
4. **Time to Value**: Signup → First transcription completed
5. **Engagement**: Actions per session, session duration

### Recommended Dashboards

1. **Onboarding Funnel**
   - Drop-off points
   - Time to complete
   - Skip rates

2. **Product Usage**
   - Feature adoption rates
   - Most used features
   - Power user identification

3. **Revenue Analytics**
   - Conversion funnel
   - Churn prediction
   - LTV by cohort

## Privacy & Compliance

### Data Collection Settings

```typescript
// Configure privacy settings
initPostHog({
  apiKey: 'your-key',
  sessionRecording: {
    enabled: true,
    maskAllInputs: true,  // Mask sensitive inputs
    maskAllText: false,   // Don't mask all text
  },
  // Respect Do Not Track
  respect_dnt: true,
  // IP anonymization
  ip: false,
});
```

### User Consent

```typescript
// Check for user consent before enabling recording
const hasConsent = getUserConsent();

if (hasConsent) {
  posthog.startSessionRecording();
} else {
  posthog.stopSessionRecording();
}
```

### Data Retention

- Session recordings: 21 days (configurable)
- Event data: 7 years
- User profiles: Until deletion requested

## Testing

### Local Development

```typescript
// Disable in development
if (process.env.NODE_ENV === 'development') {
  posthog.debug(); // Enable debug logging
  posthog.disable(); // Or disable completely
}
```

### Event Validation

```typescript
// Test events are being sent
window.posthog = posthog; // Expose for debugging

// In console:
posthog.capture('test_event', { test: true });
posthog.get_distinct_id(); // Check user ID
```

## Best Practices

1. **Event Naming**: Use consistent snake_case naming
2. **Properties**: Include relevant context but avoid PII
3. **Batching**: Events are automatically batched
4. **Error Handling**: PostHog handles offline/errors gracefully
5. **Performance**: Minimal impact (<10ms per event)

## Alerts & Automation

Set up alerts in PostHog for:
- Conversion rate drops
- Feature adoption changes
- Error spikes
- User churn signals

## Integration with Other Tools

PostHog can export to:
- Slack (alerts)
- Webhooks (custom integrations)
- Data warehouses (BigQuery, Snowflake)
- Customer.io (messaging)

## Support

- PostHog Docs: https://posthog.com/docs
- Support: support@posthog.com
- Status: https://status.posthog.com