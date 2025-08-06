/**
 * Usage Dashboard Component
 * Displays user's current usage, limits, and subscription information
 */

import React from 'react';
import { useUsage, useUsageMonitor } from '../../contexts/UsageContext';

interface UsageBarProps {
  label: string;
  current: number;
  limit: number | string;
  percentage: number;
  isUnlimited: boolean;
  unit?: string;
}

function UsageBar({ label, current, limit, percentage, isUnlimited, unit = '' }: UsageBarProps) {
  const getBarColor = () => {
    if (isUnlimited) return 'bg-blue-500';
    if (percentage >= 95) return 'bg-red-500';
    if (percentage >= 80) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getTextColor = () => {
    if (isUnlimited) return 'text-blue-700';
    if (percentage >= 95) return 'text-red-700';
    if (percentage >= 80) return 'text-yellow-700';
    return 'text-green-700';
  };

  const formatNumber = (num: number | string) => {
    if (typeof num === 'string') return num;
    if (num === -1) return '∞';
    
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  return (
    <div className="bg-white rounded-lg p-4 shadow-sm border">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm font-medium text-gray-700">{label}</h3>
        <span className={`text-sm font-semibold ${getTextColor()}`}>
          {formatNumber(current)}{unit} / {formatNumber(limit)}{unit}
        </span>
      </div>
      
      <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
        <div
          className={`h-2 rounded-full transition-all duration-300 ${getBarColor()}`}
          style={{ width: isUnlimited ? '20%' : `${Math.min(percentage, 100)}%` }}
        />
      </div>
      
      <div className="flex justify-between text-xs text-gray-500">
        <span>{isUnlimited ? 'Unlimited' : `${percentage.toFixed(1)}% used`}</span>
        {!isUnlimited && (
          <span>
            {formatNumber(typeof limit === 'number' ? limit - current : 0)}{unit} remaining
          </span>
        )}
      </div>
    </div>
  );
}

function AlertCard({ alert }: { alert: any }) {
  const getAlertStyle = () => {
    switch (alert.type) {
      case 'critical':
        return 'border-red-200 bg-red-50 text-red-800';
      case 'warning':
        return 'border-yellow-200 bg-yellow-50 text-yellow-800';
      default:
        return 'border-blue-200 bg-blue-50 text-blue-800';
    }
  };

  const getIcon = () => {
    switch (alert.type) {
      case 'critical':
        return '⚠️';
      case 'warning':
        return '⚡';
      default:
        return 'ℹ️';
    }
  };

  return (
    <div className={`rounded-lg p-3 border ${getAlertStyle()}`}>
      <div className="flex items-start">
        <span className="text-lg mr-2">{getIcon()}</span>
        <div className="flex-1">
          <p className="text-sm font-medium">{alert.message}</p>
          {alert.action && (
            <p className="text-xs mt-1 opacity-75">
              Action: {alert.action.replace('_', ' ')}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export function UsageDashboard() {
  const { state, refreshUsage, canUpgrade, clearError } = useUsage();
  
  const transcriptsUsage = useUsageMonitor('transcripts');
  const minutesUsage = useUsageMonitor('minutes');
  const storageUsage = useUsageMonitor('storage');
  const apiCallsUsage = useUsageMonitor('api_calls');

  if (state.loading && !state.usage) {
    return (
      <div className="p-6 space-y-4">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-gray-200 h-24 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (state.error && !state.usage) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <span className="text-red-400">⚠️</span>
            </div>
            <div className="ml-3 flex-1">
              <h3 className="text-sm font-medium text-red-800">
                Failed to load usage data
              </h3>
              <p className="mt-1 text-sm text-red-700">{state.error}</p>
              <div className="mt-4">
                <button
                  onClick={() => {
                    clearError();
                    refreshUsage();
                  }}
                  className="bg-red-100 hover:bg-red-200 text-red-800 px-3 py-1 rounded text-sm font-medium transition-colors"
                >
                  Retry
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!state.usage) {
    return (
      <div className="p-6 text-center text-gray-500">
        <p>No usage data available</p>
      </div>
    );
  }

  const { usage, plan, features } = state.usage;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Usage Dashboard</h2>
          <p className="text-gray-600 mt-1">
            Current Plan: <span className="font-semibold text-blue-600">{plan.name}</span>
            {plan.is_trial && (
              <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                Trial
              </span>
            )}
          </p>
          {plan.expires_at && (
            <p className="text-sm text-gray-500 mt-1">
              {plan.is_trial ? 'Trial expires' : 'Renews'}: {new Date(plan.expires_at).toLocaleDateString()}
            </p>
          )}
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={refreshUsage}
            disabled={state.loading}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {state.loading ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Refreshing...
              </>
            ) : (
              <>
                <svg className="-ml-1 mr-2 h-4 w-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Refresh
              </>
            )}
          </button>
          
          {canUpgrade() && (
            <button className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
              Upgrade Plan
            </button>
          )}
        </div>
      </div>

      {/* Usage Bars */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <UsageBar
          label="Transcripts"
          current={transcriptsUsage.current}
          limit={transcriptsUsage.limit}
          percentage={transcriptsUsage.percentage}
          isUnlimited={transcriptsUsage.isUnlimited}
        />
        
        <UsageBar
          label="Minutes Processed"
          current={minutesUsage.current}
          limit={minutesUsage.limit}
          percentage={minutesUsage.percentage}
          isUnlimited={minutesUsage.isUnlimited}
          unit=" min"
        />
        
        <UsageBar
          label="Storage Used"
          current={storageUsage.current}
          limit={storageUsage.limit}
          percentage={storageUsage.percentage}
          isUnlimited={storageUsage.isUnlimited}
          unit=" GB"
        />
        
        <UsageBar
          label="API Calls"
          current={apiCallsUsage.current}
          limit={apiCallsUsage.limit}
          percentage={apiCallsUsage.percentage}
          isUnlimited={apiCallsUsage.isUnlimited}
        />
      </div>

      {/* Alerts */}
      {state.alerts && state.alerts.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-lg font-medium text-gray-900">Usage Alerts</h3>
          <div className="space-y-2">
            {state.alerts.map((alert, index) => (
              <AlertCard key={index} alert={alert} />
            ))}
          </div>
        </div>
      )}

      {/* Features */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="text-lg font-medium text-gray-900 mb-3">Available Features</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {Object.entries(features).map(([feature, enabled]) => (
            <div
              key={feature}
              className={`flex items-center p-2 rounded text-sm ${
                enabled ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-500'
              }`}
            >
              <span className="mr-2">{enabled ? '✅' : '❌'}</span>
              <span className="font-medium">
                {feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Last Updated */}
      {state.lastUpdated && (
        <p className="text-xs text-gray-500 text-center">
          Last updated: {state.lastUpdated.toLocaleString()}
        </p>
      )}
    </div>
  );
}