/**
 * Sentry Initialization and Utilities
 * Sets up error tracking and performance monitoring
 */

import * as Sentry from '@sentry/react';
import { BrowserTracing } from '@sentry/tracing';
import { Replay } from '@sentry/replay';
import sentryConfig from '../../sentry.config';

/**
 * Initialize Sentry
 */
export function initSentry() {
  if (!sentryConfig.dsn) {
    console.warn('Sentry DSN not configured, skipping initialization');
    return;
  }

  Sentry.init({
    dsn: sentryConfig.dsn,
    environment: sentryConfig.environment,
    release: sentryConfig.release,
    
    // Sample rates
    tracesSampleRate: sentryConfig.tracesSampleRate,
    replaysSessionSampleRate: sentryConfig.replaysSessionSampleRate,
    replaysOnErrorSampleRate: sentryConfig.replaysOnErrorSampleRate,
    
    // Integrations
    integrations: [
      new BrowserTracing({
        // Set up automatic route change tracking
        routingInstrumentation: Sentry.reactRouterV6Instrumentation(
          React.useEffect,
          useLocation,
          useNavigationType,
          createRoutesFromChildren,
          matchRoutes
        ),
        
        // Performance monitoring options
        ...sentryConfig.tracingOptions,
      }),
      
      new Replay({
        // Replay configuration
        maskAllText: false,
        maskAllInputs: true,
        blockAllMedia: false,
        
        // Privacy settings
        beforeAddRecordingEvent: (event) => {
          // Remove sensitive data from recordings
          if (event.data && event.data.tag === 'input') {
            const element = event.data.attributes;
            if (element && (element.type === 'password' || element.name?.includes('token'))) {
              return null;
            }
          }
          return event;
        },
      }),
    ],
    
    // Error filtering
    ignoreErrors: sentryConfig.ignoreErrors,
    beforeSend: sentryConfig.beforeSend,
    
    // Initial scope
    initialScope: sentryConfig.initialScope,
  });
}

/**
 * Set user context for Sentry
 */
export function setSentryUser(user: {
  id: string;
  email?: string;
  username?: string;
  subscription?: string;
}) {
  Sentry.setUser({
    id: user.id,
    email: user.email,
    username: user.username,
    subscription_tier: user.subscription,
  });
}

/**
 * Clear user context
 */
export function clearSentryUser() {
  Sentry.setUser(null);
}

/**
 * Add breadcrumb for better error context
 */
export function addBreadcrumb(
  message: string,
  category: string,
  level: Sentry.SeverityLevel = 'info',
  data?: Record<string, any>
) {
  Sentry.addBreadcrumb({
    message,
    category,
    level,
    data,
    timestamp: Date.now() / 1000,
  });
}

/**
 * Capture custom error with context
 */
export function captureError(
  error: Error,
  context?: {
    tags?: Record<string, string>;
    extra?: Record<string, any>;
    level?: Sentry.SeverityLevel;
  }
) {
  Sentry.withScope((scope) => {
    if (context?.tags) {
      Object.entries(context.tags).forEach(([key, value]) => {
        scope.setTag(key, value);
      });
    }
    
    if (context?.extra) {
      Object.entries(context.extra).forEach(([key, value]) => {
        scope.setExtra(key, value);
      });
    }
    
    if (context?.level) {
      scope.setLevel(context.level);
    }
    
    Sentry.captureException(error);
  });
}

/**
 * Performance monitoring utilities
 */
export const performance = {
  /**
   * Start a performance transaction
   */
  startTransaction(name: string, op: string = 'navigation') {
    return Sentry.startTransaction({ name, op });
  },
  
  /**
   * Measure component render performance
   */
  measureComponent(componentName: string) {
    return Sentry.withProfiler(componentName);
  },
  
  /**
   * Track custom performance metric
   */
  trackMetric(name: string, value: number, unit: string = 'ms') {
    const transaction = Sentry.getCurrentHub().getScope()?.getTransaction();
    if (transaction) {
      transaction.setMeasurement(name, value, unit);
    }
  },
};

/**
 * React Error Boundary with Sentry integration
 */
export const SentryErrorBoundary = Sentry.ErrorBoundary;

/**
 * Higher-order component for profiling
 */
export const withSentryProfiler = Sentry.withProfiler;