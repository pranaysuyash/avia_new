console.log('index.tsx: Starting React app initialization');

import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { enterpriseTheme } from './theme';
import './index.css';

console.log('index.tsx: Imports completed');

interface ErrorBoundaryState { hasError: boolean; error?: Error }

class ErrorBoundary extends React.Component<React.PropsWithChildren<unknown>, ErrorBoundaryState> {
  constructor(props: React.PropsWithChildren<unknown>) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    console.error('ErrorBoundary caught error:', error);
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary componentDidCatch:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 24, fontFamily: 'system-ui' }}>
          <h1 style={{ color: '#b91c1c' }}>Something went wrong.</h1>
          <pre style={{ whiteSpace: 'pre-wrap', background: '#fef2f2', padding: 12, borderRadius: 8, color: '#7f1d1d' }}>
            {this.state.error?.message || 'Unknown error'}
            {'\n\n'}
            {this.state.error?.stack || 'No stack trace available'}
          </pre>
        </div>
      );
    }
    return this.props.children as React.ReactNode;
  }
}

console.log('index.tsx: Looking for root element');
const container = document.getElementById('root');
console.log('index.tsx: Root element found:', container);

if (!container) {
  console.error('FATAL: Root container with id="root" not found');
  document.body.innerHTML = '<h1 style="color: red;">FATAL: Root container not found</h1>';
  throw new Error('Root container with id="root" not found');
}

try {
  console.log('index.tsx: Creating React root');
  const root = createRoot(container);
  
  console.log('index.tsx: Rendering React app');
  root.render(
    <React.StrictMode>
      <ThemeProvider theme={enterpriseTheme}>
        <CssBaseline />
        <ErrorBoundary>
          <App />
        </ErrorBoundary>
      </ThemeProvider>
    </React.StrictMode>
  );
  console.log('index.tsx: React render call completed');
} catch (error) {
  console.error('FATAL: Failed to render React app:', error);
  container.innerHTML = `<h1 style="color: red;">Failed to render app: ${error}</h1>`;
  throw error;
}