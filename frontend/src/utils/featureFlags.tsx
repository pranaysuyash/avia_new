/**
 * Feature Flags Management System
 * Controls feature visibility and rollout
 */

import React from 'react';
import { config } from '../config';

// Feature flag types
export interface FeatureFlag {
  name: string;
  enabled: boolean;
  description?: string;
  rolloutPercentage?: number;
  enabledForUsers?: string[];
  enabledForRoles?: string[];
  metadata?: Record<string, any>;
}

// Feature flag names as constants
export const FEATURES = {
  AI_ASSISTANT: 'ai_assistant',
  COLLABORATION: 'collaboration',
  ADMIN_PANEL: 'admin_panel',
  ANALYTICS: 'analytics',
  PRIVACY_DASHBOARD: 'privacy_dashboard',
  GRAPHQL: 'graphql',
  REAL_TIME_TRANSCRIPTION: 'real_time_transcription',
  MULTI_LANGUAGE: 'multi_language',
  EXPORT_FEATURES: 'export_features',
  ADVANCED_SEARCH: 'advanced_search',
  CUSTOM_MODELS: 'custom_models',
  BATCH_PROCESSING: 'batch_processing',
  API_ACCESS: 'api_access',
  WEBHOOKS: 'webhooks',
  SSO: 'sso',
} as const;

export type FeatureName = typeof FEATURES[keyof typeof FEATURES];

class FeatureFlagService {
  private flags: Map<string, FeatureFlag> = new Map();
  private userContext: { id?: string; role?: string; email?: string } = {};
  private initialized = false;

  constructor() {
    this.initializeFlags();
  }

  /**
   * Initialize feature flags from config and remote source
   */
  private async initializeFlags() {
    // Load from environment config
    this.loadFromConfig();

    // Load from remote source (if configured)
    if (config.services.featureFlagEndpoint) {
      await this.loadFromRemote();
    }

    // Load from localStorage (for overrides)
    this.loadFromLocalStorage();

    this.initialized = true;
  }

  /**
   * Load flags from environment config
   */
  private loadFromConfig() {
    // Map config features to flags
    Object.entries(config.features).forEach(([key, enabled]) => {
      const flagName = key.replace(/([A-Z])/g, '_$1').toLowerCase();
      this.flags.set(flagName, {
        name: flagName,
        enabled: enabled as boolean,
        description: `Feature flag for ${flagName}`,
      });
    });
  }

  /**
   * Load flags from remote service
   */
  private async loadFromRemote() {
    try {
      const response = await fetch(`${config.api.baseUrl}/api/feature-flags`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        },
      });

      if (response.ok) {
        const remoteFlags: FeatureFlag[] = await response.json();
        remoteFlags.forEach(flag => {
          this.flags.set(flag.name, flag);
        });
      }
    } catch (error) {
      console.error('Failed to load remote feature flags:', error);
    }
  }

  /**
   * Load flag overrides from localStorage
   */
  private loadFromLocalStorage() {
    const stored = localStorage.getItem('feature_flag_overrides');
    if (stored) {
      try {
        const overrides = JSON.parse(stored);
        Object.entries(overrides).forEach(([name, enabled]) => {
          const flag = this.flags.get(name);
          if (flag) {
            flag.enabled = enabled as boolean;
          }
        });
      } catch (error) {
        console.error('Failed to parse feature flag overrides:', error);
      }
    }
  }

  /**
   * Set user context for flag evaluation
   */
  setUserContext(context: { id?: string; role?: string; email?: string }) {
    this.userContext = context;
  }

  /**
   * Check if a feature is enabled
   */
  isEnabled(featureName: FeatureName): boolean {
    const flag = this.flags.get(featureName);
    if (!flag) {
      return false;
    }

    // Check if globally enabled
    if (!flag.enabled) {
      return false;
    }

    // Check user-specific enablement
    if (flag.enabledForUsers && this.userContext.id) {
      if (!flag.enabledForUsers.includes(this.userContext.id)) {
        return false;
      }
    }

    // Check role-specific enablement
    if (flag.enabledForRoles && this.userContext.role) {
      if (!flag.enabledForRoles.includes(this.userContext.role)) {
        return false;
      }
    }

    // Check rollout percentage
    if (flag.rolloutPercentage !== undefined && flag.rolloutPercentage < 100) {
      const hash = this.hashString(this.userContext.id || 'anonymous');
      const bucket = hash % 100;
      return bucket < flag.rolloutPercentage;
    }

    return true;
  }

  /**
   * Get all enabled features
   */
  getEnabledFeatures(): FeatureName[] {
    return Array.from(this.flags.keys()).filter(name => 
      this.isEnabled(name as FeatureName)
    ) as FeatureName[];
  }

  /**
   * Get feature metadata
   */
  getFeatureMetadata(featureName: FeatureName): Record<string, any> | undefined {
    return this.flags.get(featureName)?.metadata;
  }

  /**
   * Override a feature flag (for testing)
   */
  override(featureName: FeatureName, enabled: boolean) {
    const flag = this.flags.get(featureName);
    if (flag) {
      flag.enabled = enabled;
      this.saveOverride(featureName, enabled);
    }
  }

  /**
   * Clear all overrides
   */
  clearOverrides() {
    localStorage.removeItem('feature_flag_overrides');
    this.loadFromConfig();
  }

  /**
   * Save override to localStorage
   */
  private saveOverride(name: string, enabled: boolean) {
    const stored = localStorage.getItem('feature_flag_overrides');
    const overrides = stored ? JSON.parse(stored) : {};
    overrides[name] = enabled;
    localStorage.setItem('feature_flag_overrides', JSON.stringify(overrides));
  }

  /**
   * Simple hash function for rollout percentage
   */
  private hashString(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    return Math.abs(hash);
  }

  /**
   * Wait for initialization
   */
  async waitForInit(): Promise<void> {
    if (this.initialized) return;
    
    return new Promise((resolve) => {
      const checkInterval = setInterval(() => {
        if (this.initialized) {
          clearInterval(checkInterval);
          resolve();
        }
      }, 100);
    });
  }
}

// Singleton instance
export const featureFlags = new FeatureFlagService();

// React Hook for feature flags
import { useState, useEffect } from 'react';

export function useFeatureFlag(featureName: FeatureName): boolean {
  const [enabled, setEnabled] = useState(false);

  useEffect(() => {
    featureFlags.waitForInit().then(() => {
      setEnabled(featureFlags.isEnabled(featureName));
    });
  }, [featureName]);

  return enabled;
}

// React Component for feature flag gating
interface FeatureGateProps {
  feature: FeatureName;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export const FeatureGate: React.FC<FeatureGateProps> = ({
  feature,
  children,
  fallback = null,
}) => {
  const enabled = useFeatureFlag(feature);
  return <>{enabled ? children : fallback}</>;
};

// HOC for feature flag gating
export function withFeatureFlag<P extends object>(
  Component: React.ComponentType<P>,
  featureName: FeatureName,
  FallbackComponent?: React.ComponentType<P>
): React.FC<P> {
  return (props: P) => {
    const enabled = useFeatureFlag(featureName);
    
    if (enabled) {
      return <Component {...props} />;
    }
    
    if (FallbackComponent) {
      return <FallbackComponent {...props} />;
    }
    
    return null;
  };
}

// Feature flag debug panel (development only)
export const FeatureFlagDebugPanel: React.FC = () => {
  const [flags, setFlags] = useState<[string, boolean][]>([]);

  useEffect(() => {
    featureFlags.waitForInit().then(() => {
      const allFeatures = Object.values(FEATURES);
      const flagStates = allFeatures.map(feature => [
        feature,
        featureFlags.isEnabled(feature),
      ] as [string, boolean]);
      setFlags(flagStates);
    });
  }, []);

  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <div style={{
      position: 'fixed',
      bottom: 10,
      left: 10,
      background: 'white',
      border: '1px solid #ccc',
      padding: 10,
      borderRadius: 5,
      maxHeight: 300,
      overflowY: 'auto',
      fontSize: 12,
      zIndex: 9999,
    }}>
      <h4>Feature Flags</h4>
      {flags.map(([name, enabled]) => (
        <div key={name} style={{ marginBottom: 5 }}>
          <label>
            <input
              type="checkbox"
              checked={enabled}
              onChange={(e) => {
                featureFlags.override(name as FeatureName, e.target.checked);
                setFlags(prev => prev.map(([n, enabled]) => 
                  n === name ? [n, e.target.checked] : [n, enabled]
                ));
              }}
            />
            {' '}{name}
          </label>
        </div>
      ))}
      <button
        onClick={() => {
          featureFlags.clearOverrides();
          window.location.reload();
        }}
        style={{ marginTop: 10 }}
      >
        Clear Overrides
      </button>
    </div>
  );
};