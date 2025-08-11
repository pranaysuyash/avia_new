import React, { lazy, Suspense, ComponentType, ReactNode } from 'react';
import { LoadingState } from '../components/ui/skeleton';

// Type for lazy loaded components
type LazyComponent<T extends ComponentType<any>> = React.LazyExoticComponent<T>;

// Options for lazy loading
interface LazyLoadOptions {
  fallback?: ReactNode;
  errorFallback?: ReactNode;
  delay?: number;
  onError?: (error: Error) => void;
}

// Enhanced lazy load with error boundary and loading state
export function lazyLoad<T extends ComponentType<any>>(
  importFunc: () => Promise<{ default: T }>,
  options: LazyLoadOptions = {}
): React.FC<React.ComponentProps<T>> {
  const {
    fallback = <LoadingState />,
    errorFallback,
    delay = 0,
    onError,
  } = options;

  const LazyComponent = lazy(async () => {
    if (delay > 0) {
      // Add artificial delay for testing or to prevent loading flash
      await new Promise(resolve => setTimeout(resolve, delay));
    }
    
    try {
      return await importFunc();
    } catch (error) {
      if (onError) {
        onError(error as Error);
      }
      throw error;
    }
  });

  return (props: React.ComponentProps<T>) => (
    <Suspense fallback={fallback}>
      <LazyComponent {...props} />
    </Suspense>
  );
}

// Preload a lazy component
export function preloadComponent<T extends ComponentType<any>>(
  importFunc: () => Promise<{ default: T }>
): void {
  importFunc();
}

// Lazy load with retry on failure
export function lazyLoadWithRetry<T extends ComponentType<any>>(
  importFunc: () => Promise<{ default: T }>,
  retries = 3,
  retryDelay = 1000
): LazyComponent<T> {
  return lazy(async () => {
    let lastError: Error | null = null;
    
    for (let i = 0; i < retries; i++) {
      try {
        return await importFunc();
      } catch (error) {
        lastError = error as Error;
        
        if (i < retries - 1) {
          await new Promise(resolve => setTimeout(resolve, retryDelay));
        }
      }
    }
    
    throw lastError;
  });
}

// Named exports for common lazy loaded pages
export const LazyAdminDashboard = lazyLoad(
  () => import('../components/admin/AdminDashboard').then(m => ({ default: m.AdminDashboard })),
  { fallback: <LoadingState text="Loading Admin Dashboard..." /> }
);

export const LazyAnalytics = lazyLoad(
  () => import('../components/analytics/AdvancedAnalytics'),
  { fallback: <LoadingState text="Loading Analytics..." /> }
);

export const LazyAIAssistant = lazyLoad(
  () => import('../components/ai/AIAssistant'),
  { fallback: <LoadingState text="Loading AI Assistant..." /> }
);

export const LazyPrivacyDashboard = lazyLoad(
  () => import('../components/privacy/GDPRPrivacyDashboard').then(m => ({ default: m.GDPRPrivacyDashboard })),
  { fallback: <LoadingState text="Loading Privacy Settings..." /> }
);

// Route-based code splitting helper
export const routeConfig = {
  admin: {
    component: LazyAdminDashboard,
    preload: () => preloadComponent(() => import('../components/admin/AdminDashboard').then(m => ({ default: m.AdminDashboard }))),
  },
  analytics: {
    component: LazyAnalytics,
    preload: () => preloadComponent(() => import('../components/analytics/AdvancedAnalytics')),
  },
  ai: {
    component: LazyAIAssistant,
    preload: () => preloadComponent(() => import('../components/ai/AIAssistant')),
  },
  privacy: {
    component: LazyPrivacyDashboard,
    preload: () => preloadComponent(() => import('../components/privacy/GDPRPrivacyDashboard').then(m => ({ default: m.GDPRPrivacyDashboard }))),
  },
};

// Preload on hover/focus
export const PreloadableLink: React.FC<{
  to: string;
  preload: () => void;
  children: ReactNode;
  className?: string;
}> = ({ to, preload, children, className }) => {
  const handleInteraction = () => {
    preload();
  };

  return (
    <a
      href={to}
      className={className}
      onMouseEnter={handleInteraction}
      onFocus={handleInteraction}
      onTouchStart={handleInteraction}
    >
      {children}
    </a>
  );
};