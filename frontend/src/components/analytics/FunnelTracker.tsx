/**
 * Funnel Tracker Component
 * Automatically tracks user progress through conversion funnels
 */

import React, { useEffect, useRef } from 'react';
import { useLocation, useParams } from 'react-router-dom';
import { usePostHog, trackFunnelEvent, startEngagementTracking, stopEngagementTracking } from '../../utils/posthog';

interface FunnelTrackerProps {
  userId?: string;
  userProperties?: Record<string, any>;
}

export const FunnelTracker: React.FC<FunnelTrackerProps> = ({ userId, userProperties }) => {
  const location = useLocation();
  const params = useParams();
  const { identifyUser, trackPageView } = usePostHog();
  const previousPath = useRef<string>('');

  // Identify user when component mounts or user changes
  useEffect(() => {
    if (userId) {
      identifyUser(userId, userProperties);
    }
  }, [userId, userProperties, identifyUser]);

  // Track page views and route changes
  useEffect(() => {
    // Only track if path actually changed
    if (location.pathname !== previousPath.current) {
      previousPath.current = location.pathname;
      
      // Track page view
      trackPageView({
        path: location.pathname,
        search: location.search,
        hash: location.hash,
        ...params,
      });

      // Track specific funnel events based on route
      trackRouteBasedEvents(location.pathname, params);
    }
  }, [location, params, trackPageView]);

  // Track engagement time
  useEffect(() => {
    startEngagementTracking();
    
    return () => {
      stopEngagementTracking();
    };
  }, []);

  // Track visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        trackFunnelEvent('app_backgrounded', { path: location.pathname });
        stopEngagementTracking();
      } else {
        trackFunnelEvent('app_foregrounded', { path: location.pathname });
        startEngagementTracking();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [location.pathname]);

  return null; // This component doesn't render anything
};

/**
 * Track events based on current route
 */
function trackRouteBasedEvents(pathname: string, params: Record<string, any>) {
  // Upload page
  if (pathname === '/upload') {
    trackFunnelEvent('UPLOAD_INITIATED');
  }
  
  // Transcription view
  else if (pathname.startsWith('/transcription/') && params.id) {
    trackFunnelEvent('TRANSCRIPTION_VIEWED', {
      transcription_id: params.id,
    });
  }
  
  // Pricing page
  else if (pathname === '/pricing') {
    trackFunnelEvent('PRICING_VIEWED');
  }
  
  // Onboarding flow
  else if (pathname.startsWith('/onboarding')) {
    const step = pathname.split('/')[2] || 'start';
    if (step === 'start') {
      trackFunnelEvent('ONBOARDING_STARTED');
    } else {
      trackFunnelEvent('ONBOARDING_STEP_COMPLETED', { step });
    }
  }
  
  // Signup/Login
  else if (pathname === '/signup') {
    trackFunnelEvent('SIGNUP_STARTED');
  }
  
  // Share page
  else if (pathname.startsWith('/share/')) {
    trackFunnelEvent('SHARE_LINK_ACCESSED', {
      share_id: params.id,
    });
  }
}