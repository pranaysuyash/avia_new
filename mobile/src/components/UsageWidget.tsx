/**
 * Usage Widget Component for React Native
 * Compact display of user's current usage and subscription status
 */

import React from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, ScrollView } from 'react-native';
import { useUsage, useUsageMonitor, formatUsage, getUsageColor } from '../contexts/UsageContext';

interface UsageBarProps {
  label: string;
  current: number;
  limit: number | string;
  percentage: number;
  isUnlimited: boolean;
  unit?: string;
}

function UsageBar({ label, current, limit, percentage, isUnlimited, unit = '' }: UsageBarProps) {
  const barColor = getUsageColor(percentage);
  
  return (
    <View style={{ marginBottom: 16, backgroundColor: 'white', padding: 12, borderRadius: 8, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.1, shadowRadius: 2, elevation: 2 }}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <Text style={{ fontSize: 14, fontWeight: '500', color: '#374151' }}>{label}</Text>
        <Text style={{ fontSize: 14, fontWeight: '600', color: barColor }}>
          {formatUsage(current)}{unit} / {formatUsage(limit)}{unit}
        </Text>
      </View>
      
      <View style={{ width: '100%', height: 6, backgroundColor: '#E5E7EB', borderRadius: 3, marginBottom: 8 }}>
        <View
          style={{
            height: 6,
            borderRadius: 3,
            backgroundColor: barColor,
            width: isUnlimited ? '20%' : `${Math.min(percentage, 100)}%`,
          }}
        />
      </View>
      
      <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
        <Text style={{ fontSize: 12, color: '#6B7280' }}>
          {isUnlimited ? 'Unlimited' : `${percentage.toFixed(1)}% used`}
        </Text>
        {!isUnlimited && (
          <Text style={{ fontSize: 12, color: '#6B7280' }}>
            {formatUsage(typeof limit === 'number' ? limit - current : 0)}{unit} remaining
          </Text>
        )}
      </View>
    </View>
  );
}

function AlertCard({ alert }: { alert: any }) {
  const getAlertColor = () => {
    switch (alert.type) {
      case 'critical':
        return { backgroundColor: '#FEF2F2', borderColor: '#FECACA', textColor: '#991B1B' };
      case 'warning':
        return { backgroundColor: '#FFFBEB', borderColor: '#FED7AA', textColor: '#92400E' };
      default:
        return { backgroundColor: '#EFF6FF', borderColor: '#DBEAFE', textColor: '#1E40AF' };
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

  const colors = getAlertColor();

  return (
    <View style={{
      borderRadius: 8,
      padding: 12,
      borderWidth: 1,
      backgroundColor: colors.backgroundColor,
      borderColor: colors.borderColor,
      marginBottom: 8,
    }}>
      <View style={{ flexDirection: 'row', alignItems: 'flex-start' }}>
        <Text style={{ fontSize: 16, marginRight: 8 }}>{getIcon()}</Text>
        <View style={{ flex: 1 }}>
          <Text style={{ fontSize: 14, fontWeight: '500', color: colors.textColor }}>
            {alert.message}
          </Text>
          {alert.action && (
            <Text style={{ fontSize: 12, marginTop: 4, color: colors.textColor, opacity: 0.75 }}>
              Action: {alert.action.replace('_', ' ')}
            </Text>
          )}
        </View>
      </View>
    </View>
  );
}

export function UsageWidget() {
  const { state, refreshUsage, canUpgrade, clearError } = useUsage();
  
  const transcriptsUsage = useUsageMonitor('transcripts');
  const minutesUsage = useUsageMonitor('minutes');
  const storageUsage = useUsageMonitor('storage');
  const apiCallsUsage = useUsageMonitor('api_calls');

  if (state.loading && !state.usage) {
    return (
      <View style={{ padding: 16, alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#3B82F6" />
        <Text style={{ marginTop: 8, color: '#6B7280' }}>Loading usage data...</Text>
      </View>
    );
  }

  if (state.error && !state.usage) {
    return (
      <View style={{ padding: 16 }}>
        <View style={{
          backgroundColor: '#FEF2F2',
          borderColor: '#FECACA',
          borderWidth: 1,
          borderRadius: 8,
          padding: 16,
        }}>
          <View style={{ flexDirection: 'row', alignItems: 'flex-start' }}>
            <Text style={{ fontSize: 16, marginRight: 8 }}>⚠️</Text>
            <View style={{ flex: 1 }}>
              <Text style={{ fontSize: 14, fontWeight: '500', color: '#991B1B' }}>
                Failed to load usage data
              </Text>
              <Text style={{ fontSize: 14, marginTop: 4, color: '#B91C1C' }}>
                {state.error}
              </Text>
              <TouchableOpacity
                onPress={() => {
                  clearError();
                  refreshUsage();
                }}
                style={{
                  backgroundColor: '#FEE2E2',
                  paddingHorizontal: 12,
                  paddingVertical: 6,
                  borderRadius: 6,
                  marginTop: 12,
                  alignSelf: 'flex-start',
                }}
              >
                <Text style={{ color: '#991B1B', fontSize: 14, fontWeight: '500' }}>
                  Retry
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </View>
    );
  }

  if (!state.usage) {
    return (
      <View style={{ padding: 16, alignItems: 'center' }}>
        <Text style={{ color: '#6B7280' }}>No usage data available</Text>
      </View>
    );
  }

  const { usage, plan, features } = state.usage;

  return (
    <ScrollView style={{ flex: 1 }} showsVerticalScrollIndicator={false}>
      <View style={{ padding: 16 }}>
        {/* Header */}
        <View style={{ marginBottom: 20 }}>
          <Text style={{ fontSize: 24, fontWeight: 'bold', color: '#111827' }}>
            Usage Dashboard
          </Text>
          <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 4 }}>
            <Text style={{ fontSize: 16, color: '#6B7280' }}>
              Current Plan: 
            </Text>
            <Text style={{ fontSize: 16, fontWeight: '600', color: '#3B82F6', marginLeft: 4 }}>
              {plan.name}
            </Text>
            {plan.is_trial && (
              <View style={{
                backgroundColor: '#FEF3C7',
                borderColor: '#F59E0B',
                borderWidth: 1,
                borderRadius: 12,
                paddingHorizontal: 8,
                paddingVertical: 2,
                marginLeft: 8,
              }}>
                <Text style={{ fontSize: 12, fontWeight: '500', color: '#92400E' }}>
                  Trial
                </Text>
              </View>
            )}
          </View>
          {plan.expires_at && (
            <Text style={{ fontSize: 14, color: '#6B7280', marginTop: 4 }}>
              {plan.is_trial ? 'Trial expires' : 'Renews'}: {new Date(plan.expires_at).toLocaleDateString()}
            </Text>
          )}
        </View>

        {/* Action Buttons */}
        <View style={{ flexDirection: 'row', marginBottom: 20, gap: 12 }}>
          <TouchableOpacity
            onPress={refreshUsage}
            disabled={state.loading}
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              paddingHorizontal: 12,
              paddingVertical: 8,
              borderRadius: 6,
              borderWidth: 1,
              borderColor: '#D1D5DB',
              backgroundColor: 'white',
              opacity: state.loading ? 0.5 : 1,
            }}
          >
            {state.loading ? (
              <ActivityIndicator size="small" color="#6B7280" style={{ marginRight: 8 }} />
            ) : (
              <Text style={{ fontSize: 16, marginRight: 8 }}>🔄</Text>
            )}
            <Text style={{ fontSize: 14, fontWeight: '500', color: '#374151' }}>
              {state.loading ? 'Refreshing...' : 'Refresh'}
            </Text>
          </TouchableOpacity>
          
          {canUpgrade() && (
            <TouchableOpacity
              style={{
                paddingHorizontal: 16,
                paddingVertical: 8,
                borderRadius: 6,
                backgroundColor: '#3B82F6',
              }}
            >
              <Text style={{ fontSize: 14, fontWeight: '500', color: 'white' }}>
                Upgrade Plan
              </Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Usage Bars */}
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

        {/* Alerts */}
        {state.alerts && state.alerts.length > 0 && (
          <View style={{ marginBottom: 20 }}>
            <Text style={{ fontSize: 18, fontWeight: '500', color: '#111827', marginBottom: 12 }}>
              Usage Alerts
            </Text>
            {state.alerts.map((alert, index) => (
              <AlertCard key={index} alert={alert} />
            ))}
          </View>
        )}

        {/* Features Grid */}
        <View style={{
          backgroundColor: '#F9FAFB',
          borderRadius: 8,
          padding: 16,
          marginBottom: 20,
        }}>
          <Text style={{ fontSize: 18, fontWeight: '500', color: '#111827', marginBottom: 12 }}>
            Available Features
          </Text>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
            {Object.entries(features).map(([feature, enabled]) => (
              <View
                key={feature}
                style={{
                  flexDirection: 'row',
                  alignItems: 'center',
                  padding: 8,
                  borderRadius: 6,
                  backgroundColor: enabled ? '#D1FAE5' : '#E5E7EB',
                  minWidth: '45%',
                }}
              >
                <Text style={{ marginRight: 6, fontSize: 14 }}>
                  {enabled ? '✅' : '❌'}
                </Text>
                <Text
                  style={{
                    fontSize: 12,
                    fontWeight: '500',
                    color: enabled ? '#065F46' : '#6B7280',
                    flex: 1,
                  }}
                  numberOfLines={2}
                >
                  {feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </Text>
              </View>
            ))}
          </View>
        </View>

        {/* Last Updated */}
        {state.lastUpdated && (
          <Text style={{
            fontSize: 12,
            color: '#6B7280',
            textAlign: 'center',
            marginBottom: 20,
          }}>
            Last updated: {state.lastUpdated.toLocaleString()}
          </Text>
        )}
      </View>
    </ScrollView>
  );
}