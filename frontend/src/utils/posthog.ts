/**
 * PostHog Analytics Integration
 * Handles event tracking, funnel analysis, and user insights
 */

import posthog from 'posthog-js';
import { PostHogProvider as PHProvider } from 'posthog-js/react';

interface PostHogConfig {
  apiKey: string;
  apiHost?: string;
  autocapture?: boolean;
  capturePageview?: boolean;
  capturePageleave?: boolean;
  sessionRecording?: {
    enabled: boolean;
    maskAllInputs?: boolean;
    maskAllText?: boolean;
  };
}

/**
 * Initialize PostHog
 */
export function initPostHog(config: PostHogConfig) {
  if (!config.apiKey) {
    console.warn('PostHog API key not configured, analytics disabled');
    return;
  }

  posthog.init(config.apiKey, {
    api_host: config.apiHost || 'https://app.posthog.com',
    autocapture: config.autocapture ?? true,
    capture_pageview: config.capturePageview ?? true,
    capture_pageleave: config.capturePageleave ?? true,
    
    // Session recording disabled for now
    disable_session_recording: true,
    
    // Privacy settings
    cross_subdomain_cookie: true,
    persistence: 'localStorage+cookie',
    
    // Performance settings for development
    
    // Feature flags
    bootstrap: {
      featureFlags: {},
    },
  });
}

/**
 * Funnel Events - Critical user journey tracking
 */
export const FunnelEvents = {
  // Onboarding Funnel
  SIGNUP_STARTED: 'signup_started',
  SIGNUP_COMPLETED: 'signup_completed',
  ONBOARDING_STARTED: 'onboarding_started',
  ONBOARDING_STEP_COMPLETED: 'onboarding_step_completed',
  ONBOARDING_COMPLETED: 'onboarding_completed',
  
  // Upload Funnel
  UPLOAD_INITIATED: 'upload_initiated',
  UPLOAD_FILE_SELECTED: 'upload_file_selected',
  UPLOAD_STARTED: 'upload_started',
  UPLOAD_PROGRESS: 'upload_progress',
  UPLOAD_COMPLETED: 'upload_completed',
  UPLOAD_FAILED: 'upload_failed',
  
  // Transcription Funnel
  TRANSCRIPTION_STARTED: 'transcription_started',
  TRANSCRIPTION_PROGRESS: 'transcription_progress',
  TRANSCRIPTION_COMPLETED: 'transcription_completed',
  TRANSCRIPTION_FAILED: 'transcription_failed',
  TRANSCRIPTION_VIEWED: 'transcription_viewed',
  
  // Engagement Funnel
  TRANSCRIPT_EDITED: 'transcript_edited',
  TRANSCRIPT_SEARCHED: 'transcript_searched',
  TRANSCRIPT_EXPORTED: 'transcript_exported',
  SEGMENT_PLAYED: 'segment_played',
  SPEAKER_RENAMED: 'speaker_renamed',
  
  // Collaboration Funnel
  SHARE_INITIATED: 'share_initiated',
  SHARE_LINK_CREATED: 'share_link_created',
  SHARE_LINK_ACCESSED: 'share_link_accessed',
  COLLABORATION_STARTED: 'collaboration_started',
  
  // Conversion Funnel
  PRICING_VIEWED: 'pricing_viewed',
  PLAN_SELECTED: 'plan_selected',
  CHECKOUT_STARTED: 'checkout_started',
  PAYMENT_ENTERED: 'payment_entered',
  SUBSCRIPTION_COMPLETED: 'subscription_completed',
  
  // Feature Adoption
  FEATURE_DISCOVERED: 'feature_discovered',
  FEATURE_TRIED: 'feature_tried',
  FEATURE_ADOPTED: 'feature_adopted',
} as const;

/**
 * Track funnel event with properties
 */
export function trackFunnelEvent(
  event: keyof typeof FunnelEvents | string,
  properties?: Record<string, any>
) {
  const eventName = typeof event === 'string' && event in FunnelEvents 
    ? FunnelEvents[event as keyof typeof FunnelEvents]
    : event;
    
  posthog.capture(eventName, {
    ...properties,
    timestamp: new Date().toISOString(),
    session_id: posthog.get_session_id(),
  });
}

/**
 * Identify user for tracking
 */
export function identifyUser(
  userId: string,
  properties?: {
    email?: string;
    name?: string;
    plan?: string;
    created_at?: string;
    organization?: string;
    [key: string]: any;
  }
) {
  posthog.identify(userId, properties);
}

/**
 * Track page view with custom properties
 */
export function trackPageView(properties?: Record<string, any>) {
  posthog.capture('$pageview', properties);
}

/**
 * Set user properties
 */
export function setUserProperties(properties: Record<string, any>) {
  posthog.setPersonProperties(properties);
}

/**
 * Track user engagement time
 */
let engagementStartTime: number | null = null;
let engagementInterval: NodeJS.Timeout | null = null;

export function startEngagementTracking() {
  engagementStartTime = Date.now();
  
  // Track engagement every 30 seconds
  engagementInterval = setInterval(() => {
    if (engagementStartTime) {
      const engagementDuration = Math.floor((Date.now() - engagementStartTime) / 1000);
      trackFunnelEvent('user_engaged', { duration_seconds: engagementDuration });
    }
  }, 30000);
}

export function stopEngagementTracking() {
  if (engagementInterval) {
    clearInterval(engagementInterval);
    engagementInterval = null;
  }
  
  if (engagementStartTime) {
    const totalEngagement = Math.floor((Date.now() - engagementStartTime) / 1000);
    trackFunnelEvent('session_ended', { total_duration_seconds: totalEngagement });
    engagementStartTime = null;
  }
}

/**
 * Track feature usage
 */
export function trackFeatureUsage(
  featureName: string,
  action: 'discovered' | 'tried' | 'adopted',
  metadata?: Record<string, any>
) {
  trackFunnelEvent(FunnelEvents.FEATURE_DISCOVERED, {
    feature: featureName,
    action,
    ...metadata,
  });
}

/**
 * Track conversion funnel step
 */
export function trackConversionStep(
  step: 'pricing_viewed' | 'plan_selected' | 'checkout_started' | 'payment_entered' | 'subscription_completed',
  properties?: {
    plan?: string;
    price?: number;
    currency?: string;
    payment_method?: string;
    [key: string]: any;
  }
) {
  const eventMap = {
    pricing_viewed: FunnelEvents.PRICING_VIEWED,
    plan_selected: FunnelEvents.PLAN_SELECTED,
    checkout_started: FunnelEvents.CHECKOUT_STARTED,
    payment_entered: FunnelEvents.PAYMENT_ENTERED,
    subscription_completed: FunnelEvents.SUBSCRIPTION_COMPLETED,
  };
  
  trackFunnelEvent(eventMap[step], properties);
}

/**
 * Get feature flag value
 */
export function getFeatureFlag(flagName: string): boolean | string | undefined {
  return posthog.getFeatureFlag(flagName);
}

/**
 * Track experiment exposure
 */
export function trackExperiment(experimentName: string, variant: string) {
  posthog.capture('$experiment_exposure', {
    experiment: experimentName,
    variant,
  });
}

/**
 * React hook for PostHog
 */
export function usePostHog() {
  return {
    trackEvent: trackFunnelEvent,
    identifyUser,
    trackPageView,
    setUserProperties,
    trackFeatureUsage,
    trackConversionStep,
    getFeatureFlag,
    trackExperiment,
  };
}

/**
 * PostHog React Provider
 */
export const PostHogProvider = PHProvider;