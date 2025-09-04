import React, { useState, useMemo } from 'react';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { SnackbarProvider } from 'notistack';

// Theme
import { createEnterpriseTheme } from './theme/enterprise.theme';

// Layout Components
import { EnterpriseLayout } from './components/layout/EnterpriseLayout';
import { PrivateRoute } from './components/auth/PrivateRoute';

// Enterprise Components
import { AudioProcessingHub } from './components/enterprise/AudioProcessingHub';
import { AnalyticsDashboard } from './components/enterprise/AnalyticsDashboard';
import { TranscriptViewer } from './components/enterprise/TranscriptViewer';

// Contexts
import { AuthProvider } from './contexts/AuthContext';
import { WebSocketProvider } from './contexts/WebSocketContext';
import { BrandingProvider } from './contexts/BrandingContext';

// Pages
import { LoginPage } from './pages/LoginPage';
import { TranscriptionsPage } from './pages/TranscriptionsPage';
import { SettingsPage } from './pages/SettingsPage';
import { TeamPage } from './pages/TeamPage';
import { BillingPage } from './pages/BillingPage';
import { ApiDocumentationPage } from './pages/ApiDocumentationPage';
import TelemetryPanel from '../../components/dev/TelemetryPanel';

// Create a query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      cacheTime: 1000 * 60 * 10, // 10 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function EnterpriseApp() {
  const [themeMode, setThemeMode] = useState<'light' | 'dark'>('light');
  const [brandConfig, setBrandConfig] = useState({
    primaryColor: '#1976d2',
    secondaryColor: '#dc004e',
    companyName: 'Enterprise Audio Intelligence',
    logo: '/logo.png',
  });

  const theme = useMemo(
    () => createEnterpriseTheme(themeMode, brandConfig),
    [themeMode, brandConfig]
  );

  const toggleTheme = () => {
    setThemeMode(prev => prev === 'light' ? 'dark' : 'light');
  };

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <SnackbarProvider 
          maxSnack={3}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'right',
          }}
          autoHideDuration={5000}
        >
          <BrandingProvider brandConfig={brandConfig} setBrandConfig={setBrandConfig}>
            <AuthProvider>
              <WebSocketProvider>
                <Router>
                  <Routes>
                    {/* Public Routes */}
                    <Route path="/login" element={<LoginPage />} />
                    
                    {/* Private Routes */}
                    <Route element={<PrivateRoute />}>
                      <Route element={<EnterpriseLayout onThemeToggle={toggleTheme} />}>
                        <Route path="/" element={<Navigate to="/dashboard" replace />} />
                        <Route path="/dashboard" element={<AnalyticsDashboard />} />
                        <Route path="/processing" element={<AudioProcessingHub />} />
                        <Route path="/transcriptions" element={<TranscriptionsPage />} />
                        <Route path="/transcriptions/:id" element={<TranscriptViewer transcript={null as any} />} />
                        <Route path="/team" element={<TeamPage />} />
                        <Route path="/settings" element={<SettingsPage />} />
                        <Route path="/billing" element={<BillingPage />} />
                        <Route path="/api-docs" element={<ApiDocumentationPage />} />
                        {/* Dev: UX Telemetry viewer */}
                        <Route path="/dev/telemetry" element={<TelemetryPanel />} />
                      </Route>
                    </Route>
                  </Routes>
                </Router>
              </WebSocketProvider>
            </AuthProvider>
          </BrandingProvider>
        </SnackbarProvider>
        <ReactQueryDevtools initialIsOpen={false} />
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default EnterpriseApp;
