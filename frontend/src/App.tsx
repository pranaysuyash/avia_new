/**
 * Main App Component with Analytics Integration
 */

import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { PostHogProvider } from 'posthog-js/react';
import { initPostHog } from './utils/posthog';
import { initSentry } from './utils/sentry';
import { FunnelTracker } from './components/analytics/FunnelTracker';
import { PerformanceDashboard } from './components/performance/PerformanceDashboard';

// Import your app components here
// import { HomePage } from './pages/HomePage';
// import { UploadPage } from './pages/UploadPage';
// import { TranscriptionPage } from './pages/TranscriptionPage';
// import { PricingPage } from './pages/PricingPage';

// Initialize analytics and monitoring
initPostHog({
  apiKey: process.env.REACT_APP_POSTHOG_KEY || '',
  apiHost: process.env.REACT_APP_POSTHOG_HOST,
  autocapture: true,
  sessionRecording: {
    enabled: process.env.NODE_ENV === 'production',
    maskAllInputs: true,
  },
});

initSentry();

interface AppProps {
  userId?: string;
  userEmail?: string;
  userName?: string;
}

export const App: React.FC<AppProps> = ({ userId, userEmail, userName }) => {
  // Set user properties when they change
  useEffect(() => {
    if (userId) {
      // Update analytics user context
      const userProperties = {
        email: userEmail,
        name: userName,
      };
      
      // This would be imported from your auth context
      // identifyUser(userId, userProperties);
    }
  }, [userId, userEmail, userName]);

  return (
    <PostHogProvider>
      <Router>
        {/* Funnel tracking component */}
        <FunnelTracker 
          userId={userId}
          userProperties={{
            email: userEmail,
            name: userName,
          }}
        />
        
        {/* Performance monitoring in development */}
        {process.env.NODE_ENV === 'development' && (
          <PerformanceDashboard position="bottom-right" />
        )}
        
        {/* Your app routes */}
        <Routes>
          {/* Example routes - replace with your actual routes */}
          <Route path="/" element={<div>Home Page</div>} />
          <Route path="/upload" element={<div>Upload Page</div>} />
          <Route path="/transcription/:id" element={<div>Transcription Page</div>} />
          <Route path="/pricing" element={<div>Pricing Page</div>} />
          <Route path="/onboarding/*" element={<div>Onboarding Flow</div>} />
          <Route path="/signup" element={<div>Signup Page</div>} />
          <Route path="/share/:id" element={<div>Share Page</div>} />
        </Routes>
      </Router>
    </PostHogProvider>
  );
};