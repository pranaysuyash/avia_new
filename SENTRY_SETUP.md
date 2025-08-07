# Sentry Setup Guide

This guide explains how to configure Sentry for error tracking and performance monitoring across all platforms (Web, Desktop, and API).

## Overview

Sentry has been configured for:
- **Frontend (React)**: Browser SDK with performance monitoring and replay
- **Desktop (Electron)**: Electron SDK with native crash reporting
- **Backend (Python/FastAPI)**: Python SDK with async support

## Configuration

### 1. Environment Variables

Set these environment variables in your `.env` file:

```env
# Sentry Configuration
SENTRY_DSN=https://your-dsn@sentry.io/project-id
SENTRY_ORG=your-organization
SENTRY_PROJECT=your-project
SENTRY_AUTH_TOKEN=your-auth-token
SENTRY_ENVIRONMENT=production
SENTRY_RELEASE=1.0.0
```

### 2. Source Map Upload

Source maps are automatically uploaded during production builds:

```bash
# Frontend build with source maps
cd frontend
npm run build:sentry

# Desktop build with source maps
cd desktop_app
npm run build:sentry

# Upload source maps manually
npm run sentry:sourcemaps
```

### 3. Performance Budgets

Performance budgets are enforced via Lighthouse CI:

- **First Contentful Paint**: < 1.8s
- **Largest Contentful Paint**: < 2.5s
- **Cumulative Layout Shift**: < 0.1
- **Total Blocking Time**: < 300ms
- **Time to Interactive**: < 3.8s

### 4. Error Filtering

The following errors are automatically filtered:
- Browser extension errors
- Network timeout errors
- User cancellation errors
- Non-actionable third-party errors

## Usage

### Frontend (React)

```typescript
import { captureError, addBreadcrumb, performance } from '@/utils/sentry';

// Capture an error with context
captureError(error, {
  tags: { component: 'TranscriptionView' },
  extra: { transcriptionId: '123' },
  level: 'error'
});

// Add breadcrumb for context
addBreadcrumb('User started transcription', 'user', 'info', {
  fileSize: file.size,
  fileType: file.type
});

// Track performance
const transaction = performance.startTransaction('transcription-upload');
// ... do work
transaction.finish();
```

### Backend (Python)

```python
from api.utils.sentry_config import (
    capture_exception,
    capture_message,
    add_breadcrumb,
    set_user_context
)

# Capture exception with context
capture_exception(
    error,
    transcription_id=transcription_id,
    user_id=user_id
)

# Set user context
set_user_context(
    user_id=str(user.id),
    email=user.email,
    subscription_tier=user.subscription_tier
)

# Add breadcrumb
add_breadcrumb(
    "Transcription started",
    category="transcription",
    level="info",
    data={"file_size": file_size}
)
```

## Monitoring

### Performance Dashboard

In development, the Performance Dashboard component shows real-time metrics:

```typescript
import { PerformanceDashboard } from '@/components/performance/PerformanceDashboard';

// Add to your app layout
<PerformanceDashboard position="bottom-right" />
```

### CI/CD Integration

1. **GitHub Actions**: Automatically creates releases and uploads source maps
2. **Lighthouse CI**: Runs performance checks on every PR
3. **Bundle Analysis**: Check bundle sizes with `npm run analyze:all`

## Debugging

### View Source Maps Locally

```bash
# Start local server with source maps
npm run dev:sourcemaps

# Check if source maps are correctly generated
ls -la frontend/build/*.map
ls -la desktop_app/dist/*.map
```

### Test Sentry Integration

```javascript
// Frontend
Sentry.captureException(new Error('Test error'));

// Backend
capture_exception(Exception("Test error"))
```

### Common Issues

1. **Source maps not uploading**: Check `SENTRY_AUTH_TOKEN` is set
2. **Missing user context**: Ensure `setSentryUser` is called after login
3. **Performance metrics not showing**: Check `tracesSampleRate` is > 0

## Security

- Source maps are deleted after upload in production
- Sensitive data is scrubbed before sending to Sentry
- User passwords and tokens are never sent
- PII is masked in session replays

## Alerts

Configure alerts in Sentry dashboard for:
- Error rate spikes
- Performance degradation
- New error types
- User feedback

## Best Practices

1. **Use breadcrumbs liberally** to provide context
2. **Set user context** after authentication
3. **Tag errors** with relevant metadata
4. **Use transactions** for performance monitoring
5. **Review errors weekly** and fix or filter noise