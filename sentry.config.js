/**
 * Sentry Configuration
 * Handles error tracking and performance monitoring
 */

const environment = process.env.NODE_ENV || 'development';
const release = process.env.SENTRY_RELEASE || `media-platform@${process.env.npm_package_version}`;

module.exports = {
  // Sentry DSN - should be set via environment variable
  dsn: process.env.SENTRY_DSN,
  
  // Environment configuration
  environment,
  release,
  
  // Sample rates
  tracesSampleRate: environment === 'production' ? 0.1 : 1.0,
  replaysSessionSampleRate: environment === 'production' ? 0.1 : 1.0,
  replaysOnErrorSampleRate: 1.0,
  
  // Integration configuration
  integrations: [
    // Browser integrations
    'BrowserTracing',
    'Replay',
    'CaptureConsole',
    'HttpContext',
    'LinkedErrors',
    'Dedupe',
    
    // Custom integrations
    'PerformanceMonitoring',
    'UserFeedback',
  ],
  
  // Performance monitoring
  tracingOptions: {
    trackComponents: true,
    trackUserInteractions: true,
  },
  
  // Error filtering
  ignoreErrors: [
    // Browser extensions
    'top.GLOBALS',
    'ResizeObserver loop limit exceeded',
    'Non-Error promise rejection captured',
    
    // Network errors
    'NetworkError',
    'Failed to fetch',
    'Load failed',
    
    // User cancellations
    'AbortError',
    'cancelled',
  ],
  
  // Data scrubbing
  beforeSend(event, hint) {
    // Remove sensitive data
    if (event.request && event.request.cookies) {
      delete event.request.cookies;
    }
    
    // Filter out non-actionable errors
    if (event.exception) {
      const error = hint.originalException;
      if (error && error.message) {
        // Skip browser extension errors
        if (error.message.includes('extension://')) {
          return null;
        }
        
        // Skip third-party script errors
        if (error.stack && error.stack.includes('chrome-extension://')) {
          return null;
        }
      }
    }
    
    return event;
  },
  
  // User context
  initialScope: {
    tags: {
      platform: 'web',
    },
  },
};