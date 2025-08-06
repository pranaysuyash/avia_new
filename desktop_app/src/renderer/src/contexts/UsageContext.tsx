/**
 * Usage and Subscription Context
 * Provides global state management for user usage, quotas, and subscription info
 */

import React, { createContext, useContext, useReducer, useEffect, useCallback } from 'react';
import { apiClient, UsageResponse, UsageInfo } from '../services/apiClient';

// Types
interface UsageState {
  loading: boolean;
  error: string | null;
  usage: UsageResponse | null;
  alerts: any[] | null;
  lastUpdated: Date | null;
  quotaExceeded: boolean;
  featureBlocked: string | null;
}

type UsageAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_USAGE'; payload: UsageResponse }
  | { type: 'SET_ALERTS'; payload: any[] }
  | { type: 'SET_QUOTA_EXCEEDED'; payload: boolean }
  | { type: 'SET_FEATURE_BLOCKED'; payload: string | null }
  | { type: 'UPDATE_USAGE_ITEM'; payload: { type: string; usage: UsageInfo } }
  | { type: 'RESET' };

// Initial state
const initialState: UsageState = {
  loading: false,
  error: null,
  usage: null,
  alerts: null,
  lastUpdated: null,
  quotaExceeded: false,
  featureBlocked: null,
};

// Reducer
function usageReducer(state: UsageState, action: UsageAction): UsageState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };
    
    case 'SET_USAGE':
      return {
        ...state,
        usage: action.payload,
        loading: false,
        error: null,
        lastUpdated: new Date(),
      };
    
    case 'SET_ALERTS':
      return { ...state, alerts: action.payload };
    
    case 'SET_QUOTA_EXCEEDED':
      return { ...state, quotaExceeded: action.payload };
    
    case 'SET_FEATURE_BLOCKED':
      return { ...state, featureBlocked: action.payload };
    
    case 'UPDATE_USAGE_ITEM':
      if (!state.usage) return state;
      return {
        ...state,
        usage: {
          ...state.usage,
          usage: {
            ...state.usage.usage,
            [action.payload.type]: action.payload.usage,
          },
        },
        lastUpdated: new Date(),
      };
    
    case 'RESET':
      return initialState;
    
    default:
      return state;
  }
}

// Context
interface UsageContextType {
  state: UsageState;
  refreshUsage: () => Promise<void>;
  refreshAlerts: () => Promise<void>;
  checkFeature: (featureName: string) => boolean;
  getUsagePercentage: (usageType: string) => number;
  isNearLimit: (usageType: string, threshold?: number) => boolean;
  canUpgrade: () => boolean;
  clearError: () => void;
  handleQuotaError: (error: any) => void;
  handleFeatureError: (error: any) => void;
}

const UsageContext = createContext<UsageContextType | undefined>(undefined);

// Provider component
export function UsageProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(usageReducer, initialState);

  // Refresh usage data
  const refreshUsage = useCallback(async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const usage = await apiClient.getUsageDashboard();
      dispatch({ type: 'SET_USAGE', payload: usage });
    } catch (error: any) {
      console.error('Failed to refresh usage:', error);
      dispatch({ type: 'SET_ERROR', payload: error.message });
    }
  }, []);

  // Refresh alerts
  const refreshAlerts = useCallback(async () => {
    try {
      const alertsResponse = await apiClient.getUsageAlerts();
      dispatch({ type: 'SET_ALERTS', payload: alertsResponse.alerts || [] });
    } catch (error: any) {
      console.error('Failed to refresh alerts:', error);
    }
  }, []);

  // Check if user has access to a feature
  const checkFeature = useCallback((featureName: string): boolean => {
    if (!state.usage?.features) return false;
    return state.usage.features[featureName as keyof typeof state.usage.features] || false;
  }, [state.usage]);

  // Get usage percentage for a specific type
  const getUsagePercentage = useCallback((usageType: string): number => {
    const usage = state.usage?.usage[usageType as keyof typeof state.usage.usage];
    if (!usage) return 0;
    
    if (typeof usage.limit === 'string' && usage.limit === 'unlimited') return 0;
    if (typeof usage.limit === 'number' && usage.limit === -1) return 0;
    
    return usage.percentage_used || 0;
  }, [state.usage]);

  // Check if user is near usage limit
  const isNearLimit = useCallback((usageType: string, threshold = 80): boolean => {
    const percentage = getUsagePercentage(usageType);
    return percentage >= threshold;
  }, [getUsagePercentage]);

  // Check if user can upgrade
  const canUpgrade = useCallback((): boolean => {
    return state.usage?.can_upgrade || false;
  }, [state.usage]);

  // Clear error state
  const clearError = useCallback(() => {
    dispatch({ type: 'SET_ERROR', payload: null });
  }, []);

  // Handle quota exceeded errors
  const handleQuotaError = useCallback((error: any) => {
    dispatch({ type: 'SET_QUOTA_EXCEEDED', payload: true });
    dispatch({ type: 'SET_ERROR', payload: error.message });
    // Refresh usage to get updated numbers
    refreshUsage();
  }, [refreshUsage]);

  // Handle feature access denied errors
  const handleFeatureError = useCallback((error: any) => {
    dispatch({ type: 'SET_FEATURE_BLOCKED', payload: error.requiredFeature });
    dispatch({ type: 'SET_ERROR', payload: error.message });
  }, []);

  // Auto-refresh usage data periodically
  useEffect(() => {
    // Initial load
    refreshUsage();
    refreshAlerts();

    // Set up periodic refresh (every 5 minutes)
    const interval = setInterval(() => {
      refreshUsage();
      refreshAlerts();
    }, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, [refreshUsage, refreshAlerts]);

  // Listen for quota and feature errors from API client
  useEffect(() => {
    const handleQuotaExceeded = (event: CustomEvent) => {
      handleQuotaError(event.detail);
    };

    const handleFeatureAccessDenied = (event: CustomEvent) => {
      handleFeatureError(event.detail);
    };

    const handleAuthLogout = () => {
      dispatch({ type: 'RESET' });
    };

    window.addEventListener('quota:exceeded' as any, handleQuotaExceeded);
    window.addEventListener('feature:access_denied' as any, handleFeatureAccessDenied);
    window.addEventListener('auth:logout' as any, handleAuthLogout);

    return () => {
      window.removeEventListener('quota:exceeded' as any, handleQuotaExceeded);
      window.removeEventListener('feature:access_denied' as any, handleFeatureAccessDenied);
      window.removeEventListener('auth:logout' as any, handleAuthLogout);
    };
  }, [handleQuotaError, handleFeatureError]);

  const contextValue: UsageContextType = {
    state,
    refreshUsage,
    refreshAlerts,
    checkFeature,
    getUsagePercentage,
    isNearLimit,
    canUpgrade,
    clearError,
    handleQuotaError,
    handleFeatureError,
  };

  return (
    <UsageContext.Provider value={contextValue}>
      {children}
    </UsageContext.Provider>
  );
}

// Hook to use the context
export function useUsage() {
  const context = useContext(UsageContext);
  if (context === undefined) {
    throw new Error('useUsage must be used within a UsageProvider');
  }
  return context;
}

// Utility hook for checking feature access
export function useFeatureAccess(featureName: string) {
  const { checkFeature, state } = useUsage();
  
  return {
    hasAccess: checkFeature(featureName),
    isLoading: state.loading,
    planName: state.usage?.plan.name,
    planTier: state.usage?.plan.tier,
    canUpgrade: state.usage?.can_upgrade || false,
  };
}

// Utility hook for usage monitoring
export function useUsageMonitor(usageType: string) {
  const { state, getUsagePercentage, isNearLimit } = useUsage();
  
  const usage = state.usage?.usage[usageType as keyof typeof state.usage.usage];
  
  return {
    current: usage?.current || 0,
    limit: usage?.limit || 0,
    remaining: usage?.remaining || 0,
    percentage: getUsagePercentage(usageType),
    isNearLimit: isNearLimit(usageType),
    isCritical: isNearLimit(usageType, 95),
    isUnlimited: typeof usage?.limit === 'string' && usage.limit === 'unlimited',
  };
}