/**
 * Centralized configuration management
 * All environment variables and app config in one place
 */

// Helper to get environment variable with fallback
const getEnvVar = (key: string, fallback: string = ''): string => {
  return process.env[key] || fallback;
};

// Helper to get boolean environment variable
const getBoolEnvVar = (key: string, fallback: boolean = false): boolean => {
  const value = process.env[key];
  if (!value) return fallback;
  return value.toLowerCase() === 'true';
};

// Helper to get number environment variable
const getNumberEnvVar = (key: string, fallback: number = 0): number => {
  const value = process.env[key];
  if (!value) return fallback;
  const parsed = parseInt(value, 10);
  return isNaN(parsed) ? fallback : parsed;
};

export const config = {
  // Application
  app: {
    name: getEnvVar('REACT_APP_NAME', 'Transcription Platform'),
    version: getEnvVar('REACT_APP_VERSION', '1.0.0'),
    env: getEnvVar('REACT_APP_ENV', process.env.NODE_ENV || 'development'),
    isDevelopment: process.env.NODE_ENV === 'development',
    isProduction: process.env.NODE_ENV === 'production',
    isTest: process.env.NODE_ENV === 'test',
  },

  // API
  api: {
    baseUrl: getEnvVar('REACT_APP_API_URL', 'http://localhost:8000'),
    timeout: getNumberEnvVar('REACT_APP_API_TIMEOUT', 30000),
    retryCount: getNumberEnvVar('REACT_APP_API_RETRY_COUNT', 3),
  },

  // Authentication
  auth: {
    tokenKey: getEnvVar('REACT_APP_AUTH_TOKEN_KEY', 'auth_tokens'),
    userKey: getEnvVar('REACT_APP_AUTH_USER_KEY', 'auth_user'),
    refreshInterval: getNumberEnvVar('REACT_APP_AUTH_REFRESH_INTERVAL', 300000),
  },

  // Sentry
  sentry: {
    dsn: getEnvVar('REACT_APP_SENTRY_DSN'),
    environment: getEnvVar('REACT_APP_SENTRY_ENVIRONMENT', 'development'),
    tracesSampleRate: parseFloat(getEnvVar('REACT_APP_SENTRY_TRACES_SAMPLE_RATE', '1.0')),
    replaySampleRate: parseFloat(getEnvVar('REACT_APP_SENTRY_REPLAY_SAMPLE_RATE', '0.1')),
  },

  // Feature Flags
  features: {
    aiAssistant: getBoolEnvVar('REACT_APP_FEATURE_AI_ASSISTANT', true),
    collaboration: getBoolEnvVar('REACT_APP_FEATURE_COLLABORATION', true),
    adminPanel: getBoolEnvVar('REACT_APP_FEATURE_ADMIN_PANEL', true),
    analytics: getBoolEnvVar('REACT_APP_FEATURE_ANALYTICS', true),
    privacyDashboard: getBoolEnvVar('REACT_APP_FEATURE_PRIVACY_DASHBOARD', true),
    graphql: getBoolEnvVar('REACT_APP_FEATURE_GRAPHQL', true),
  },

  // Third-party Services
  services: {
    googleAnalyticsId: getEnvVar('REACT_APP_GOOGLE_ANALYTICS_ID'),
    hotjarId: getEnvVar('REACT_APP_HOTJAR_ID'),
    intercomAppId: getEnvVar('REACT_APP_INTERCOM_APP_ID'),
    featureFlagEndpoint: getEnvVar('REACT_APP_FEATURE_FLAG_ENDPOINT'),
    posthog: {
      key: getEnvVar('REACT_APP_POSTHOG_KEY'),
      host: getEnvVar('REACT_APP_POSTHOG_HOST', 'https://app.posthog.com'),
    },
  },

  // WebSocket
  websocket: {
    url: getEnvVar('REACT_APP_WS_URL', 'ws://localhost:8000/ws'),
    reconnectInterval: getNumberEnvVar('REACT_APP_WS_RECONNECT_INTERVAL', 5000),
    maxReconnectAttempts: getNumberEnvVar('REACT_APP_WS_MAX_RECONNECT_ATTEMPTS', 5),
  },

  // Storage
  storage: {
    maxFileSize: getNumberEnvVar('REACT_APP_MAX_FILE_SIZE', 524288000), // 500MB
    allowedFileTypes: getEnvVar('REACT_APP_ALLOWED_FILE_TYPES', 'audio/*,video/*').split(','),
    prefix: getEnvVar('REACT_APP_STORAGE_PREFIX', 'transcription_app_'),
  },

  // UI
  ui: {
    theme: getEnvVar('REACT_APP_THEME', 'light') as 'light' | 'dark',
    primaryColor: getEnvVar('REACT_APP_PRIMARY_COLOR', '#3B82F6'),
    itemsPerPage: getNumberEnvVar('REACT_APP_ITEMS_PER_PAGE', 20),
    defaultLanguage: getEnvVar('REACT_APP_DEFAULT_LANGUAGE', 'en'),
  },

  // Development
  dev: {
    enableDevtools: getBoolEnvVar('REACT_APP_ENABLE_DEVTOOLS', true),
    enableReduxLogger: getBoolEnvVar('REACT_APP_ENABLE_REDUX_LOGGER', false),
    enableReactQueryDevtools: getBoolEnvVar('REACT_APP_ENABLE_REACT_QUERY_DEVTOOLS', true),
  },

  // Security
  security: {
    cspEnabled: getBoolEnvVar('REACT_APP_CSP_ENABLED', true),
    cspReportUri: getEnvVar('REACT_APP_CSP_REPORT_URI', '/api/csp-report'),
    requireHttps: getBoolEnvVar('REACT_APP_REQUIRE_HTTPS', false),
  },

  // Performance
  performance: {
    enablePWA: getBoolEnvVar('REACT_APP_ENABLE_PWA', true),
    enableCodeSplitting: getBoolEnvVar('REACT_APP_ENABLE_CODE_SPLITTING', true),
    enableLazyLoading: getBoolEnvVar('REACT_APP_ENABLE_LAZY_LOADING', true),
    imageOptimization: getBoolEnvVar('REACT_APP_IMAGE_OPTIMIZATION', true),
  },

  // Public URLs
  urls: {
    public: getEnvVar('REACT_APP_PUBLIC_URL', 'http://localhost:3000'),
    docs: getEnvVar('REACT_APP_DOCS_URL', 'https://docs.example.com'),
    support: getEnvVar('REACT_APP_SUPPORT_URL', 'https://support.example.com'),
    statusPage: getEnvVar('REACT_APP_STATUS_PAGE_URL', 'https://status.example.com'),
  },
};

// Validate required configuration
export const validateConfig = (): string[] => {
  const errors: string[] = [];

  // Add validation rules
  if (!config.api.baseUrl) {
    errors.push('API base URL is required');
  }

  if (config.app.isProduction) {
    if (!config.sentry.dsn) {
      errors.push('Sentry DSN is required for production');
    }
    if (!config.security.requireHttps) {
      errors.push('HTTPS should be required in production');
    }
  }

  return errors;
};

// Export individual configs for convenience
export const appConfig = config.app;
export const apiConfig = config.api;
export const authConfig = config.auth;
export const featureFlags = config.features;
export const uiConfig = config.ui;

export default config;