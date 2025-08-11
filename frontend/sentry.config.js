/**
 * Sentry Configuration
 * Configure your Sentry DSN and options here
 */

const sentryConfig = {
  // Get DSN from environment variable or leave empty to disable
  dsn: process.env.REACT_APP_SENTRY_DSN || '',
  
  // Environment (development, staging, production)
  environment: process.env.REACT_APP_ENV || process.env.NODE_ENV || 'development',
  
  // Release version
  release: process.env.REACT_APP_VERSION || '1.0.0',
  
  // Performance Monitoring
  tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.1 : 1.0,
  
  // Session Replay
  replaysSessionSampleRate: process.env.NODE_ENV === 'production' ? 0.1 : 0,
  replaysOnErrorSampleRate: process.env.NODE_ENV === 'production' ? 1.0 : 0,
  
  // Additional tracing options
  tracingOptions: {
    // Trace idle transactions
    idleTimeout: 3000,
    
    // Track specific origins
    tracePropagationTargets: [
      'localhost',
      /^https:\/\/yourserver\.io\/api/,
      /^http:\/\/localhost:\d+\/api/
    ],
    
    // Track child spans
    trackComponents: true,
  },
  
  // Error filtering
  ignoreErrors: [
    // Browser extensions
    'top.GLOBALS',
    'ResizeObserver loop limit exceeded',
    'Non-Error promise rejection captured',
    
    // Network errors
    'Network request failed',
    'NetworkError',
    'Failed to fetch',
    
    // Script errors
    'Script error',
    'Script error.',
  ],
  
  // Before send hook for filtering
  beforeSend(event, hint) {
    // Filter out errors from browser extensions
    if (event.exception) {
      const error = hint.originalException;
      
      // Filter Chrome extension errors
      if (error && error.stack && error.stack.includes('chrome-extension://')) {
        return null;
      }
      
      // Filter Firefox extension errors
      if (error && error.stack && error.stack.includes('moz-extension://')) {
        return null;
      }
    }
    
    // Filter sensitive data from URLs
    if (event.request?.url) {
      event.request.url = event.request.url.replace(/\/api\/auth\/.*/, '/api/auth/[FILTERED]');
    }
    
    return event;
  },
  
  // User context
  initialScope: {
    tags: {
      component: 'frontend',
    },
  },
};

module.exports = sentryConfig;