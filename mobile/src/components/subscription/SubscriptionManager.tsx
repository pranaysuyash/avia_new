import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Modal,
  Alert,
  Linking,
  StyleSheet,
  SafeAreaView,
  Platform,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useAuth } from '../../contexts/AuthContext';
import { api } from '../../services/api';

interface PricingPlan {
  tier: string;
  name: string;
  description: string;
  monthly_price: number;
  yearly_price: number;
  currency: string;
  limits: {
    transcripts_per_month: number;
    minutes_per_month: number;
    storage_gb: number;
    team_members: number;
    api_calls_per_month: number;
  };
  features: any;
  highlights: string[];
}

interface CurrentSubscription {
  status: string;
  plan: {
    tier: string;
    name: string;
    description: string;
  };
  billing_interval?: string;
  current_period_end?: string;
  canceled_at?: string;
  trial_end?: string;
}

interface UsageSummary {
  plan: {
    tier: string;
    name: string;
    billing_interval: string;
  };
  usage: {
    transcripts: { used: number; limit: number; percentage: number };
    minutes: { used: number; limit: number; percentage: number };
    storage: { used_gb: number; limit_gb: number; percentage: number };
    api_calls: { used: number; limit: number; percentage: number };
  };
  features: {
    [key: string]: boolean;
  };
}

const SubscriptionManager: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'plans' | 'usage'>('plans');
  const [plans, setPlans] = useState<PricingPlan[]>([]);
  const [currentSubscription, setCurrentSubscription] = useState<CurrentSubscription | null>(null);
  const [usageSummary, setUsageSummary] = useState<UsageSummary | null>(null);
  const [billingInterval, setBillingInterval] = useState<'monthly' | 'yearly'>('monthly');
  const [loading, setLoading] = useState(true);
  const [showCancelModal, setShowCancelModal] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [plansRes, subRes, usageRes] = await Promise.all([
        api.get('/subscriptions/plans'),
        api.get('/subscriptions/current'),
        api.get('/subscriptions/usage'),
      ]);

      setPlans(plansRes.data);
      setCurrentSubscription(subRes.data);
      setUsageSummary(usageRes.data);
    } catch (error) {
      console.error('Failed to load subscription data:', error);
      Alert.alert('Error', 'Failed to load subscription information');
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async (planTier: string) => {
    try {
      const response = await api.post('/subscriptions/checkout-session', {
        plan_tier: planTier,
        billing_interval: billingInterval,
        success_url: 'myapp://subscription/success',
        cancel_url: 'myapp://subscription/cancel',
      });

      if (response.data.checkout_url) {
        Linking.openURL(response.data.checkout_url);
      }
    } catch (error) {
      console.error('Failed to create checkout session:', error);
      Alert.alert('Error', 'Failed to start subscription process');
    }
  };

  const handleCancelSubscription = async () => {
    try {
      await api.post('/subscriptions/cancel');
      Alert.alert('Success', 'Your subscription has been canceled');
      setShowCancelModal(false);
      loadData();
    } catch (error) {
      console.error('Failed to cancel subscription:', error);
      Alert.alert('Error', 'Failed to cancel subscription');
    }
  };

  const handleReactivateSubscription = async () => {
    try {
      await api.put('/subscriptions/update', {
        cancel_at_period_end: false,
      });
      Alert.alert('Success', 'Your subscription has been reactivated');
      loadData();
    } catch (error) {
      console.error('Failed to reactivate subscription:', error);
      Alert.alert('Error', 'Failed to reactivate subscription');
    }
  };

  const openCustomerPortal = async () => {
    try {
      const response = await api.get('/subscriptions/customer-portal', {
        params: {
          return_url: 'myapp://subscription',
        },
      });

      if (response.data.portal_url) {
        Linking.openURL(response.data.portal_url);
      }
    } catch (error) {
      console.error('Failed to open customer portal:', error);
      Alert.alert('Error', 'Failed to open billing portal');
    }
  };

  const renderPlanCard = (plan: PricingPlan) => {
    const isCurrentPlan = currentSubscription?.plan.tier === plan.tier;
    const isRecommended = plan.tier === 'pro';
    const price = billingInterval === 'monthly' ? plan.monthly_price : plan.yearly_price;

    return (
      <View
        key={plan.tier}
        style={[
          styles.planCard,
          isRecommended && styles.recommendedCard,
          isCurrentPlan && styles.currentPlanCard,
        ]}
      >
        {isRecommended && (
          <View style={styles.recommendedBadge}>
            <Text style={styles.recommendedText}>RECOMMENDED</Text>
          </View>
        )}

        <Text style={styles.planName}>{plan.name}</Text>
        <Text style={styles.planDescription}>{plan.description}</Text>

        <View style={styles.priceContainer}>
          {price === 0 ? (
            <Text style={styles.price}>Free</Text>
          ) : (
            <Text style={styles.price}>
              ${price}
              <Text style={styles.pricePeriod}>
                /{billingInterval === 'monthly' ? 'mo' : 'yr'}
              </Text>
            </Text>
          )}
        </View>

        <View style={styles.highlights}>
          {plan.highlights.map((highlight, idx) => (
            <View key={idx} style={styles.highlightItem}>
              <Icon name="check" size={16} color="#10B981" />
              <Text style={styles.highlightText}>{highlight}</Text>
            </View>
          ))}
        </View>

        {isCurrentPlan ? (
          <View style={styles.currentPlanButton}>
            <Text style={styles.currentPlanButtonText}>Current Plan</Text>
          </View>
        ) : (
          <TouchableOpacity
            style={[styles.subscribeButton, isRecommended && styles.recommendedButton]}
            onPress={() => handleSubscribe(plan.tier)}
          >
            <Text
              style={[
                styles.subscribeButtonText,
                isRecommended && styles.recommendedButtonText,
              ]}
            >
              {price === 0 ? 'Get Started' : 'Subscribe'}
            </Text>
          </TouchableOpacity>
        )}
      </View>
    );
  };

  const renderUsageBar = (
    name: string,
    used: number,
    limit: number,
    percentage: number,
    icon: string
  ) => {
    const isUnlimited = limit === -1;
    const color = percentage >= 90 ? '#EF4444' : percentage >= 75 ? '#F59E0B' : '#10B981';

    return (
      <View style={styles.usageCard}>
        <View style={styles.usageHeader}>
          <View style={styles.usageTitle}>
            <Icon name={icon} size={20} color="#666" />
            <Text style={styles.usageName}>{name}</Text>
          </View>
          <Text style={styles.usageCount}>
            {isUnlimited ? `${used} used` : `${used} / ${limit}`}
          </Text>
        </View>
        <View style={styles.usageBarContainer}>
          <View
            style={[
              styles.usageBar,
              { width: isUnlimited ? '0%' : `${percentage}%`, backgroundColor: color },
            ]}
          />
        </View>
        {!isUnlimited && (
          <Text style={styles.usageRemaining}>{100 - percentage}% remaining</Text>
        )}
      </View>
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.title}>Subscription & Billing</Text>

        {/* Current Subscription Info */}
        {currentSubscription?.status !== 'none' && (
          <View style={styles.currentSubscriptionCard}>
            <Text style={styles.currentPlanTitle}>
              Current Plan: {currentSubscription?.plan.name}
            </Text>
            <Text style={styles.currentPlanDescription}>
              {currentSubscription?.plan.description}
            </Text>
            {currentSubscription?.current_period_end && (
              <Text style={styles.renewalDate}>
                Renews on {new Date(currentSubscription.current_period_end).toLocaleDateString()}
              </Text>
            )}
            {currentSubscription?.canceled_at && (
              <View style={styles.canceledWarning}>
                <Icon name="alert-circle" size={16} color="#F59E0B" />
                <Text style={styles.canceledWarningText}>
                  Subscription will cancel at end of billing period
                </Text>
              </View>
            )}
            <View style={styles.subscriptionActions}>
              {currentSubscription?.canceled_at ? (
                <TouchableOpacity
                  style={styles.primaryButton}
                  onPress={handleReactivateSubscription}
                >
                  <Text style={styles.primaryButtonText}>Reactivate</Text>
                </TouchableOpacity>
              ) : (
                <>
                  <TouchableOpacity
                    style={styles.secondaryButton}
                    onPress={openCustomerPortal}
                  >
                    <Text style={styles.secondaryButtonText}>Manage Billing</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.dangerButton}
                    onPress={() => setShowCancelModal(true)}
                  >
                    <Text style={styles.dangerButtonText}>Cancel</Text>
                  </TouchableOpacity>
                </>
              )}
            </View>
          </View>
        )}

        {/* Tabs */}
        <View style={styles.tabs}>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'plans' && styles.activeTab]}
            onPress={() => setActiveTab('plans')}
          >
            <Text style={[styles.tabText, activeTab === 'plans' && styles.activeTabText]}>
              Plans
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'usage' && styles.activeTab]}
            onPress={() => setActiveTab('usage')}
          >
            <Text style={[styles.tabText, activeTab === 'usage' && styles.activeTabText]}>
              Usage
            </Text>
          </TouchableOpacity>
        </View>

        {/* Tab Content */}
        {activeTab === 'plans' && (
          <>
            {/* Billing Interval Toggle */}
            <View style={styles.billingToggle}>
              <TouchableOpacity
                style={[
                  styles.toggleOption,
                  billingInterval === 'monthly' && styles.toggleOptionActive,
                ]}
                onPress={() => setBillingInterval('monthly')}
              >
                <Text
                  style={[
                    styles.toggleText,
                    billingInterval === 'monthly' && styles.toggleTextActive,
                  ]}
                >
                  Monthly
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.toggleOption,
                  billingInterval === 'yearly' && styles.toggleOptionActive,
                ]}
                onPress={() => setBillingInterval('yearly')}
              >
                <Text
                  style={[
                    styles.toggleText,
                    billingInterval === 'yearly' && styles.toggleTextActive,
                  ]}
                >
                  Yearly
                </Text>
                <Text style={styles.saveBadge}>Save 17%</Text>
              </TouchableOpacity>
            </View>

            {/* Plans */}
            {plans.map(renderPlanCard)}
          </>
        )}

        {activeTab === 'usage' && usageSummary && (
          <>
            <View style={styles.planSummaryCard}>
              <Text style={styles.planSummaryTitle}>{usageSummary.plan.name} Plan</Text>
              {usageSummary.plan.tier !== 'enterprise' && (
                <TouchableOpacity
                  style={styles.upgradeButton}
                  onPress={() => setActiveTab('plans')}
                >
                  <Text style={styles.upgradeButtonText}>Upgrade Plan</Text>
                </TouchableOpacity>
              )}
            </View>

            {renderUsageBar(
              'Transcripts',
              usageSummary.usage.transcripts.used,
              usageSummary.usage.transcripts.limit,
              usageSummary.usage.transcripts.percentage,
              'file-text'
            )}
            {renderUsageBar(
              'Minutes',
              usageSummary.usage.minutes.used,
              usageSummary.usage.minutes.limit,
              usageSummary.usage.minutes.percentage,
              'clock'
            )}
            {renderUsageBar(
              'Storage',
              parseFloat(usageSummary.usage.storage.used_gb.toFixed(1)),
              usageSummary.usage.storage.limit_gb,
              usageSummary.usage.storage.percentage,
              'hard-drive'
            )}
            {renderUsageBar(
              'API Calls',
              usageSummary.usage.api_calls.used,
              usageSummary.usage.api_calls.limit,
              usageSummary.usage.api_calls.percentage,
              'zap'
            )}

            <View style={styles.featuresCard}>
              <Text style={styles.featuresTitle}>Available Features</Text>
              {Object.entries(usageSummary.features).map(([key, enabled]) => (
                <View key={key} style={styles.featureItem}>
                  <Icon
                    name={enabled ? 'check' : 'x'}
                    size={18}
                    color={enabled ? '#10B981' : '#9CA3AF'}
                  />
                  <Text style={[styles.featureText, !enabled && styles.featureTextDisabled]}>
                    {key
                      .split('_')
                      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                      .join(' ')}
                  </Text>
                </View>
              ))}
            </View>
          </>
        )}
      </ScrollView>

      {/* Cancel Modal */}
      <Modal
        visible={showCancelModal}
        transparent={true}
        animationType="fade"
        onRequestClose={() => setShowCancelModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Cancel Subscription?</Text>
            <Text style={styles.modalText}>
              Your subscription will remain active until the end of the current billing period.
              You can reactivate anytime before it expires.
            </Text>
            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.modalCancelButton}
                onPress={() => setShowCancelModal(false)}
              >
                <Text style={styles.modalCancelButtonText}>Keep Subscription</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.modalConfirmButton}
                onPress={handleCancelSubscription}
              >
                <Text style={styles.modalConfirmButtonText}>Cancel Subscription</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  scrollContent: {
    padding: 16,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 20,
  },
  currentSubscriptionCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  currentPlanTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  currentPlanDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  renewalDate: {
    fontSize: 14,
    color: '#666',
    marginBottom: 12,
  },
  canceledWarning: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEF3C7',
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
  },
  canceledWarningText: {
    fontSize: 14,
    color: '#92400E',
    marginLeft: 8,
  },
  subscriptionActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  tabs: {
    flexDirection: 'row',
    marginBottom: 20,
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    padding: 4,
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 6,
  },
  activeTab: {
    backgroundColor: '#007AFF',
  },
  tabText: {
    fontSize: 16,
    color: '#666',
    fontWeight: '500',
  },
  activeTabText: {
    color: '#FFFFFF',
  },
  billingToggle: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    padding: 4,
    marginBottom: 20,
  },
  toggleOption: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 6,
    flexDirection: 'row',
    justifyContent: 'center',
  },
  toggleOptionActive: {
    backgroundColor: '#007AFF',
  },
  toggleText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  toggleTextActive: {
    color: '#FFFFFF',
  },
  saveBadge: {
    fontSize: 12,
    color: '#10B981',
    marginLeft: 8,
    fontWeight: '600',
  },
  planCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  recommendedCard: {
    borderWidth: 2,
    borderColor: '#007AFF',
  },
  currentPlanCard: {
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  recommendedBadge: {
    position: 'absolute',
    top: -10,
    alignSelf: 'center',
    backgroundColor: '#007AFF',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  recommendedText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  planName: {
    fontSize: 20,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
    textAlign: 'center',
  },
  planDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 16,
    textAlign: 'center',
  },
  priceContainer: {
    alignItems: 'center',
    marginBottom: 20,
  },
  price: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#333',
  },
  pricePeriod: {
    fontSize: 16,
    fontWeight: 'normal',
    color: '#666',
  },
  highlights: {
    marginBottom: 20,
  },
  highlightItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  highlightText: {
    fontSize: 14,
    color: '#666',
    marginLeft: 8,
    flex: 1,
  },
  subscribeButton: {
    backgroundColor: '#F0F0F0',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  recommendedButton: {
    backgroundColor: '#007AFF',
  },
  subscribeButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  recommendedButtonText: {
    color: '#FFFFFF',
  },
  currentPlanButton: {
    backgroundColor: '#E0E0E0',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  currentPlanButtonText: {
    fontSize: 16,
    color: '#666',
  },
  primaryButton: {
    flex: 1,
    backgroundColor: '#007AFF',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
    marginRight: 8,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  secondaryButton: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#007AFF',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
    marginRight: 8,
  },
  secondaryButtonText: {
    color: '#007AFF',
    fontSize: 16,
    fontWeight: '600',
  },
  dangerButton: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
  dangerButtonText: {
    color: '#EF4444',
    fontSize: 16,
    fontWeight: '600',
  },
  planSummaryCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  planSummaryTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  upgradeButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 6,
  },
  upgradeButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  usageCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  usageHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  usageTitle: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  usageName: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
    marginLeft: 8,
  },
  usageCount: {
    fontSize: 14,
    color: '#666',
  },
  usageBarContainer: {
    height: 8,
    backgroundColor: '#E0E0E0',
    borderRadius: 4,
    overflow: 'hidden',
  },
  usageBar: {
    height: '100%',
    borderRadius: 4,
  },
  usageRemaining: {
    fontSize: 12,
    color: '#666',
    marginTop: 8,
  },
  featuresCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
  },
  featuresTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 16,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  featureText: {
    fontSize: 14,
    color: '#333',
    marginLeft: 12,
  },
  featureTextDisabled: {
    color: '#9CA3AF',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 24,
    width: '100%',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  modalText: {
    fontSize: 16,
    color: '#666',
    marginBottom: 24,
    lineHeight: 22,
  },
  modalActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  modalCancelButton: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    marginRight: 8,
  },
  modalCancelButtonText: {
    fontSize: 16,
    color: '#666',
    fontWeight: '600',
  },
  modalConfirmButton: {
    flex: 1,
    backgroundColor: '#EF4444',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginLeft: 8,
  },
  modalConfirmButtonText: {
    fontSize: 16,
    color: '#FFFFFF',
    fontWeight: '600',
  },
});

export default SubscriptionManager;