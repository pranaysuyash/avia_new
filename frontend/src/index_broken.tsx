import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css';
import * as serviceWorkerRegistration from './serviceWorkerRegistration';
import { initSentry } from './utils/sentry';
import { initWebVitals, observeLongTasks } from './utils/performance';

// Initialize Sentry before rendering app
try {
  initSentry();
} catch (error) {
  console.warn('Sentry initialization failed:', error);
}

// Initialize performance monitoring
try {
  initWebVitals();
  observeLongTasks((duration) => {
    console.warn(`Long task detected: ${duration}ms`);
  });
} catch (error) {
  console.warn('Performance monitoring initialization failed:', error);
}

const container = document.getElementById('root');
const root = createRoot(container!);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Register service worker for PWA support
serviceWorkerRegistration.register({
  onSuccess: () => {
    console.log('PWA: Service Worker registered successfully');
  },
  onUpdate: (registration) => {
    console.log('PWA: New content available, please refresh');
    // You can show a notification to the user here
  }
});