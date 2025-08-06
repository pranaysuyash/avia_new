/**
 * Quota and Feature Modals for React Native
 * Displays when user exceeds quota or tries to access premium features
 */

import React from 'react';
import {
  View,
  Text,
  Modal,
  TouchableOpacity,
  ScrollView,
  Dimensions,
} from 'react-native';
import { useUsage } from '../../contexts/UsageContext';

const { width } = Dimensions.get('window');

interface QuotaExceededModalProps {
  isVisible: boolean;
  onClose: () => void;
  onUpgrade: () => void;
}

export function QuotaExceededModal({ isVisible, onClose, onUpgrade }: QuotaExceededModalProps) {
  const { state, clearError } = useUsage();

  const handleClose = () => {
    clearError();
    onClose();
  };

  const handleUpgrade = () => {
    onUpgrade();
    handleClose();
  };

  return (
    <Modal
      visible={isVisible}
      transparent
      animationType="fade"
      onRequestClose={handleClose}
    >
      <View style={{
        flex: 1,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        justifyContent: 'center',
        alignItems: 'center',
        padding: 20,
      }}>
        <View style={{
          backgroundColor: 'white',
          borderRadius: 12,
          padding: 24,
          width: width - 40,
          maxWidth: 400,
          shadowColor: '#000',
          shadowOffset: { width: 0, height: 2 },
          shadowOpacity: 0.25,
          shadowRadius: 3.84,
          elevation: 5,
        }}>
          {/* Header */}
          <View style={{ alignItems: 'center', marginBottom: 20 }}>
            <View style={{
              width: 60,
              height: 60,
              borderRadius: 30,
              backgroundColor: '#FEF2F2',
              justifyContent: 'center',
              alignItems: 'center',
              marginBottom: 12,
            }}>
              <Text style={{ fontSize: 24 }}>⚠️</Text>
            </View>
            <Text style={{
              fontSize: 20,
              fontWeight: 'bold',
              color: '#111827',
              textAlign: 'center',
            }}>
              Usage Quota Exceeded
            </Text>
          </View>

          {/* Content */}
          <ScrollView style={{ maxHeight: 300 }}>
            <Text style={{
              fontSize: 16,
              color: '#6B7280',
              textAlign: 'center',
              marginBottom: 16,
              lineHeight: 24,
            }}>
              {state.error || 
                "You've reached your usage limit for your current plan. Upgrade to continue using premium features."
              }
            </Text>

            {state.usage && (
              <View style={{
                backgroundColor: '#F9FAFB',
                borderRadius: 8,
                padding: 16,
                marginBottom: 16,
              }}>
                <Text style={{
                  fontSize: 16,
                  fontWeight: '600',
                  color: '#111827',
                  marginBottom: 12,
                }}>
                  Current Plan: {state.usage.plan.name}
                </Text>
                
                {Object.entries(state.usage.usage).map(([type, usage]) => {
                  if (usage.percentage_used >= 90) {
                    return (
                      <View key={type} style={{
                        flexDirection: 'row',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        paddingVertical: 4,
                      }}>
                        <Text style={{
                          fontSize: 14,
                          color: '#6B7280',
                          textTransform: 'capitalize',
                        }}>
                          {type.replace('_', ' ')}:
                        </Text>
                        <Text style={{
                          fontSize: 14,
                          fontWeight: '500',
                          color: '#DC2626',
                        }}>
                          {usage.current} / {usage.limit} ({usage.percentage_used.toFixed(1)}%)
                        </Text>
                      </View>
                    );
                  }
                  return null;
                })}
              </View>
            )}
          </ScrollView>

          {/* Actions */}
          <View style={{ gap: 12 }}>
            <TouchableOpacity
              onPress={handleUpgrade}
              style={{
                backgroundColor: '#3B82F6',
                borderRadius: 8,
                paddingVertical: 12,
                paddingHorizontal: 24,
                alignItems: 'center',
              }}
            >
              <Text style={{
                color: 'white',
                fontSize: 16,
                fontWeight: '600',
              }}>
                Upgrade Plan
              </Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              onPress={handleClose}
              style={{
                borderWidth: 1,
                borderColor: '#D1D5DB',
                borderRadius: 8,
                paddingVertical: 12,
                paddingHorizontal: 24,
                alignItems: 'center',
                backgroundColor: 'white',
              }}
            >
              <Text style={{
                color: '#374151',
                fontSize: 16,
                fontWeight: '500',
              }}>
                Close
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

interface FeatureBlockedModalProps {
  isVisible: boolean;
  onClose: () => void;
  onUpgrade: () => void;
  featureName?: string;
}

export function FeatureBlockedModal({ isVisible, onClose, onUpgrade, featureName }: FeatureBlockedModalProps) {
  const { state, clearError } = useUsage();

  const handleClose = () => {
    clearError();
    onClose();
  };

  const handleUpgrade = () => {
    onUpgrade();
    handleClose();
  };

  const formatFeatureName = (name: string) => {
    return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  return (
    <Modal
      visible={isVisible}
      transparent
      animationType="slide"
      onRequestClose={handleClose}
    >
      <View style={{
        flex: 1,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        justifyContent: 'center',
        alignItems: 'center',
        padding: 20,
      }}>
        <View style={{
          backgroundColor: 'white',
          borderRadius: 12,
          padding: 24,
          width: width - 40,
          maxWidth: 400,
          shadowColor: '#000',
          shadowOffset: { width: 0, height: 2 },
          shadowOpacity: 0.25,
          shadowRadius: 3.84,
          elevation: 5,
        }}>
          {/* Header */}
          <View style={{ alignItems: 'center', marginBottom: 20 }}>
            <View style={{
              width: 60,
              height: 60,
              borderRadius: 30,
              backgroundColor: '#FEF3C7',
              justifyContent: 'center',
              alignItems: 'center',
              marginBottom: 12,
            }}>
              <Text style={{ fontSize: 24 }}>🔒</Text>
            </View>
            <Text style={{
              fontSize: 20,
              fontWeight: 'bold',
              color: '#111827',
              textAlign: 'center',
            }}>
              Premium Feature Required
            </Text>
          </View>

          {/* Content */}
          <ScrollView style={{ maxHeight: 300 }}>
            <Text style={{
              fontSize: 16,
              color: '#6B7280',
              textAlign: 'center',
              marginBottom: 16,
              lineHeight: 24,
            }}>
              {featureName ? (
                <>
                  The <Text style={{ fontWeight: '600' }}>{formatFeatureName(featureName)}</Text> feature requires a premium subscription.
                </>
              ) : (
                'This feature requires a premium subscription.'
              )}
              {' '}Upgrade your plan to access all premium features.
            </Text>

            {state.usage && (
              <View style={{
                backgroundColor: '#F9FAFB',
                borderRadius: 8,
                padding: 16,
                marginBottom: 16,
              }}>
                <Text style={{
                  fontSize: 16,
                  fontWeight: '600',
                  color: '#111827',
                  marginBottom: 8,
                }}>
                  Current Plan: {state.usage.plan.name}
                </Text>
                
                <Text style={{
                  fontSize: 14,
                  color: '#6B7280',
                  marginBottom: 12,
                }}>
                  Upgrade to unlock premium features including:
                </Text>
                
                <View style={{ gap: 6 }}>
                  {[
                    'Advanced analytics and insights',
                    'Custom AI models and prompts',
                    'Real-time collaboration',
                    'Priority support',
                    'White-label options'
                  ].map((feature, index) => (
                    <View key={index} style={{ flexDirection: 'row', alignItems: 'center' }}>
                      <Text style={{ color: '#10B981', marginRight: 8, fontSize: 14 }}>•</Text>
                      <Text style={{ fontSize: 14, color: '#6B7280', flex: 1 }}>
                        {feature}
                      </Text>
                    </View>
                  ))}
                </View>
              </View>
            )}
          </ScrollView>

          {/* Actions */}
          <View style={{ gap: 12 }}>
            <TouchableOpacity
              onPress={handleUpgrade}
              style={{
                backgroundColor: '#3B82F6',
                borderRadius: 8,
                paddingVertical: 12,
                paddingHorizontal: 24,
                alignItems: 'center',
              }}
            >
              <Text style={{
                color: 'white',
                fontSize: 16,
                fontWeight: '600',
              }}>
                Upgrade Plan
              </Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              onPress={handleClose}
              style={{
                borderWidth: 1,
                borderColor: '#D1D5DB',
                borderRadius: 8,
                paddingVertical: 12,
                paddingHorizontal: 24,
                alignItems: 'center',
                backgroundColor: 'white',
              }}
            >
              <Text style={{
                color: '#374151',
                fontSize: 16,
                fontWeight: '500',
              }}>
                Maybe Later
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}