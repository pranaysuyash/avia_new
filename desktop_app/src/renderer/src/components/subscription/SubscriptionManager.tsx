import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FiCreditCard,
  FiCheck,
  FiX,
  FiTrendingUp,
  FiHardDrive,
  FiCpu,
  FiZap,
  FiShield,
  FiClock,
  FiAlertCircle,
  FiChevronRight,
  FiDollarSign,
  FiCalendar,
  FiRefreshCw,
} from 'react-icons/fi';
import { useAuth } from '../../contexts/AuthContext';
import { api } from '../../services/api';
import { loadStripe } from '@stripe/stripe-js';

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
  subscription?: {
    status: string;
    current_period_end: string;
    canceled_at?: string;
  };
}

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY || '');

const SubscriptionManager: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'plans' | 'usage' | 'billing'>('plans');
  const [plans, setPlans] = useState<PricingPlan[]>([]);
  const [currentSubscription, setCurrentSubscription] = useState<CurrentSubscription | null>(null);
  const [usageSummary, setUsageSummary] = useState<UsageSummary | null>(null);
  const [billingInterval, setBillingInterval] = useState<'monthly' | 'yearly'>('monthly');
  const [loading, setLoading] = useState(false);
  const [showCancelDialog, setShowCancelDialog] = useState(false);

  useEffect(() => {
    fetchPlans();
    fetchCurrentSubscription();
    fetchUsageSummary();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await api.get('/subscriptions/plans');
      setPlans(response.data);
    } catch (error) {
      console.error('Failed to fetch plans:', error);
    }
  };

  const fetchCurrentSubscription = async () => {
    try {
      const response = await api.get('/subscriptions/current');
      setCurrentSubscription(response.data);
    } catch (error) {
      console.error('Failed to fetch current subscription:', error);
    }
  };

  const fetchUsageSummary = async () => {
    try {
      const response = await api.get('/subscriptions/usage');
      setUsageSummary(response.data);
    } catch (error) {
      console.error('Failed to fetch usage summary:', error);
    }
  };

  const handleSubscribe = async (planTier: string) => {
    setLoading(true);
    try {
      const response = await api.post('/subscriptions/checkout-session', {
        plan_tier: planTier,
        billing_interval: billingInterval,
        success_url: `${window.location.origin}/subscription?success=true`,
        cancel_url: `${window.location.origin}/subscription`,
      });

      if (response.data.checkout_url) {
        window.location.href = response.data.checkout_url;
      }
    } catch (error) {
      console.error('Failed to create checkout session:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelSubscription = async () => {
    setLoading(true);
    try {
      await api.post('/subscriptions/cancel');
      fetchCurrentSubscription();
      setShowCancelDialog(false);
    } catch (error) {
      console.error('Failed to cancel subscription:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleReactivateSubscription = async () => {
    setLoading(true);
    try {
      await api.put('/subscriptions/update', {
        cancel_at_period_end: false,
      });
      fetchCurrentSubscription();
    } catch (error) {
      console.error('Failed to reactivate subscription:', error);
    } finally {
      setLoading(false);
    }
  };

  const openCustomerPortal = async () => {
    try {
      const returnUrl = encodeURIComponent(window.location.href);
      const response = await api.get(`/subscriptions/customer-portal?return_url=${returnUrl}`);

      if (response.data.portal_url) {
        window.location.href = response.data.portal_url;
      }
    } catch (error) {
      console.error('Failed to open customer portal:', error);
    }
  };

  const renderPlansTab = () => {
    const getRecommendedPlan = () => 'pro';

    return (
      <div className="space-y-8">
        {/* Current Plan Info */}
        {currentSubscription?.status !== 'none' && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  Current Plan: {currentSubscription?.plan.name}
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  {currentSubscription?.plan.description}
                </p>
                {currentSubscription?.current_period_end && (
                  <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                    <FiCalendar className="inline-block w-4 h-4 mr-1" />
                    Renews on {new Date(currentSubscription.current_period_end).toLocaleDateString()}
                  </p>
                )}
                {currentSubscription?.canceled_at && (
                  <div className="mt-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                    <p className="text-yellow-800 dark:text-yellow-200 flex items-center">
                      <FiAlertCircle className="w-4 h-4 mr-2" />
                      Subscription will cancel at end of billing period
                    </p>
                  </div>
                )}
              </div>
              <div className="flex space-x-3">
                {currentSubscription?.canceled_at ? (
                  <button
                    onClick={handleReactivateSubscription}
                    disabled={loading}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                  >
                    Reactivate
                  </button>
                ) : (
                  <>
                    <button
                      onClick={openCustomerPortal}
                      className="px-4 py-2 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                      Manage Billing
                    </button>
                    <button
                      onClick={() => setShowCancelDialog(true)}
                      className="px-4 py-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                    >
                      Cancel
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Billing Interval Toggle */}
        <div className="flex justify-center">
          <div className="bg-gray-100 dark:bg-gray-700 p-1 rounded-lg">
            <button
              onClick={() => setBillingInterval('monthly')}
              className={`px-6 py-2 rounded-md transition-all ${
                billingInterval === 'monthly'
                  ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow'
                  : 'text-gray-600 dark:text-gray-400'
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingInterval('yearly')}
              className={`px-6 py-2 rounded-md transition-all ${
                billingInterval === 'yearly'
                  ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow'
                  : 'text-gray-600 dark:text-gray-400'
              }`}
            >
              Yearly
              <span className="ml-2 text-xs text-green-600 dark:text-green-400">Save 17%</span>
            </button>
          </div>
        </div>

        {/* Pricing Plans */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {plans.map((plan) => {
            const isCurrentPlan = currentSubscription?.plan.tier === plan.tier;
            const isRecommended = plan.tier === getRecommendedPlan();
            const price = billingInterval === 'monthly' ? plan.monthly_price : plan.yearly_price;

            return (
              <motion.div
                key={plan.tier}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className={`relative bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 ${
                  isRecommended ? 'ring-2 ring-blue-600' : ''
                }`}
              >
                {isRecommended && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <span className="bg-blue-600 text-white px-3 py-1 rounded-full text-sm font-semibold">
                      RECOMMENDED
                    </span>
                  </div>
                )}

                <div className="text-center mb-6">
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                    {plan.name}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                    {plan.description}
                  </p>
                  <div className="mb-4">
                    {price === 0 ? (
                      <p className="text-3xl font-bold text-gray-900 dark:text-white">Free</p>
                    ) : (
                      <>
                        <p className="text-3xl font-bold text-gray-900 dark:text-white">
                          ${price}
                          <span className="text-lg font-normal text-gray-600 dark:text-gray-400">
                            /{billingInterval === 'monthly' ? 'mo' : 'yr'}
                          </span>
                        </p>
                      </>
                    )}
                  </div>
                </div>

                <ul className="space-y-3 mb-6">
                  {plan.highlights.map((highlight, idx) => (
                    <li key={idx} className="flex items-start">
                      <FiCheck className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                      <span className="text-sm text-gray-700 dark:text-gray-300">{highlight}</span>
                    </li>
                  ))}
                </ul>

                {isCurrentPlan ? (
                  <button
                    disabled
                    className="w-full py-2 bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 rounded-lg cursor-not-allowed"
                  >
                    Current Plan
                  </button>
                ) : (
                  <button
                    onClick={() => handleSubscribe(plan.tier)}
                    disabled={loading}
                    className={`w-full py-2 rounded-lg transition-colors disabled:opacity-50 ${
                      isRecommended
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-200 dark:hover:bg-gray-600'
                    }`}
                  >
                    {price === 0 ? 'Get Started' : 'Subscribe'}
                  </button>
                )}
              </motion.div>
            );
          })}
        </div>

        {/* Cancel Dialog */}
        <AnimatePresence>
          {showCancelDialog && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
            >
              <motion.div
                initial={{ scale: 0.9 }}
                animate={{ scale: 1 }}
                exit={{ scale: 0.9 }}
                className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full"
              >
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                  Cancel Subscription?
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  Your subscription will remain active until the end of the current billing period.
                  You can reactivate anytime before it expires.
                </p>
                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => setShowCancelDialog(false)}
                    className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
                  >
                    Keep Subscription
                  </button>
                  <button
                    onClick={handleCancelSubscription}
                    disabled={loading}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
                  >
                    Cancel Subscription
                  </button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  };

  const renderUsageTab = () => {
    if (!usageSummary) {
      return (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      );
    }

    const renderUsageBar = (
      name: string,
      used: number,
      limit: number,
      percentage: number,
      icon: React.ReactNode
    ) => {
      const isUnlimited = limit === -1;
      const color = percentage >= 90 ? 'red' : percentage >= 75 ? 'yellow' : 'green';

      return (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              {icon}
              <h4 className="text-lg font-medium text-gray-900 dark:text-white ml-3">{name}</h4>
            </div>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {isUnlimited ? `${used} used` : `${used} / ${limit}`}
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
            <div
              className={`h-3 rounded-full transition-all ${
                color === 'red'
                  ? 'bg-red-500'
                  : color === 'yellow'
                  ? 'bg-yellow-500'
                  : 'bg-green-500'
              }`}
              style={{ width: isUnlimited ? '0%' : `${percentage}%` }}
            ></div>
          </div>
          {!isUnlimited && (
            <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
              {100 - percentage}% remaining
            </p>
          )}
        </div>
      );
    };

    return (
      <div className="space-y-6">
        {/* Plan Summary */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                {usageSummary.plan.name} Plan
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                {usageSummary.plan.billing_interval !== 'none' &&
                  `Billed ${usageSummary.plan.billing_interval}`}
              </p>
            </div>
            {usageSummary.plan.tier !== 'enterprise' && (
              <button
                onClick={() => setActiveTab('plans')}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Upgrade Plan
              </button>
            )}
          </div>
        </div>

        {/* Usage Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {renderUsageBar(
            'Transcripts',
            usageSummary.usage.transcripts.used,
            usageSummary.usage.transcripts.limit,
            usageSummary.usage.transcripts.percentage,
            <FiCpu className="w-5 h-5 text-blue-600" />
          )}
          {renderUsageBar(
            'Minutes',
            usageSummary.usage.minutes.used,
            usageSummary.usage.minutes.limit,
            usageSummary.usage.minutes.percentage,
            <FiClock className="w-5 h-5 text-purple-600" />
          )}
          {renderUsageBar(
            'Storage',
            parseFloat(usageSummary.usage.storage.used_gb.toFixed(1)),
            usageSummary.usage.storage.limit_gb,
            usageSummary.usage.storage.percentage,
            <FiHardDrive className="w-5 h-5 text-green-600" />
          )}
          {renderUsageBar(
            'API Calls',
            usageSummary.usage.api_calls.used,
            usageSummary.usage.api_calls.limit,
            usageSummary.usage.api_calls.percentage,
            <FiZap className="w-5 h-5 text-orange-600" />
          )}
        </div>

        {/* Features */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Available Features
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Object.entries(usageSummary.features).map(([key, enabled]) => (
              <div key={key} className="flex items-center">
                {enabled ? (
                  <FiCheck className="w-5 h-5 text-green-500 mr-2" />
                ) : (
                  <FiX className="w-5 h-5 text-gray-400 mr-2" />
                )}
                <span
                  className={`text-sm ${
                    enabled
                      ? 'text-gray-900 dark:text-white'
                      : 'text-gray-500 dark:text-gray-500'
                  }`}
                >
                  {key
                    .split('_')
                    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                    .join(' ')}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderBillingTab = () => (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Billing Management
        </h3>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          Manage your payment methods, view invoices, and update billing information through our
          secure Stripe portal.
        </p>
        <button
          onClick={openCustomerPortal}
          className="flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <FiCreditCard className="w-5 h-5 mr-2" />
          Open Billing Portal
          <FiChevronRight className="w-5 h-5 ml-2" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <FiShield className="w-8 h-8 text-green-600" />
            <span className="text-sm text-green-600 font-semibold">Secure</span>
          </div>
          <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
            Bank-Level Security
          </h4>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            All payment information is encrypted and securely processed by Stripe.
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <FiRefreshCw className="w-8 h-8 text-blue-600" />
            <span className="text-sm text-blue-600 font-semibold">Flexible</span>
          </div>
          <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
            Change Anytime
          </h4>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Upgrade, downgrade, or cancel your subscription at any time.
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <FiDollarSign className="w-8 h-8 text-purple-600" />
            <span className="text-sm text-purple-600 font-semibold">Transparent</span>
          </div>
          <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
            No Hidden Fees
          </h4>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            What you see is what you pay. No setup fees or hidden charges.
          </p>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Subscription & Billing
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Manage your subscription plan and monitor usage
          </p>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 dark:border-gray-700 mb-8">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('plans')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'plans'
                  ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
              }`}
            >
              <div className="flex items-center space-x-2">
                <FiCreditCard className="w-4 h-4" />
                <span>Plans & Pricing</span>
              </div>
            </button>

            <button
              onClick={() => setActiveTab('usage')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'usage'
                  ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
              }`}
            >
              <div className="flex items-center space-x-2">
                <FiTrendingUp className="w-4 h-4" />
                <span>Usage & Limits</span>
              </div>
            </button>

            <button
              onClick={() => setActiveTab('billing')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'billing'
                  ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
              }`}
            >
              <div className="flex items-center space-x-2">
                <FiDollarSign className="w-4 h-4" />
                <span>Billing</span>
              </div>
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'plans' && renderPlansTab()}
        {activeTab === 'usage' && renderUsageTab()}
        {activeTab === 'billing' && renderBillingTab()}
      </div>
    </div>
  );
};

export default SubscriptionManager;