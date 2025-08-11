import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  RefreshControl,
  ActivityIndicator,
  Alert,
  Modal,
  FlatList
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
  interpolate,
  withDelay,
  runOnJS,
  FadeInUp,
  FadeInRight
} from 'react-native-reanimated';
import { BlurView } from '@react-native-community/blur';
import LinearGradient from 'react-native-linear-gradient';
import { PieChart, LineChart, BarChart } from 'react-native-chart-kit';

const { width, height } = Dimensions.get('window');

// Types
interface AnalyticsData {
  overview: {
    total_users: number;
    active_sessions: number;
    content_analyzed: number;
    ai_insights_generated: number;
  };
  content_analytics: {
    sentiment_distribution: { positive: number; neutral: number; negative: number };
    engagement_trends: number[];
    topic_trends: Array<{
      topic: string;
      frequency: number;
      sentiment: number;
    }>;
  };
  user_behavior: {
    retention_funnel: { new: number; active: number; engaged: number; loyal: number };
    feature_adoption: Record<string, number>;
    productivity_distribution: { high: number; medium: number; low: number };
  };
  business_intelligence: {
    revenue_metrics: {
      monthly_recurring_revenue: number;
      customer_acquisition_cost: number;
      customer_lifetime_value: number;
      churn_rate: number;
    };
  };
  predictive_analytics: {
    growth_forecast: number[];
    churn_prediction: number;
    capacity_alerts: Array<{
      metric: string;
      current: number;
      predicted: number;
      threshold: number;
    }>;
  };
}

interface RealtimeInsights {
  alerts: Array<{
    type: string;
    severity: 'info' | 'warning' | 'error';
    message: string;
    recommendation: string;
  }>;
  key_metrics: {
    sentiment_score: number;
    user_satisfaction: number;
    system_efficiency: number;
    prediction_accuracy: number;
  };
  trending_topics: Array<{
    topic: string;
    growth: string;
    sentiment: number;
  }>;
  user_activity: {
    active_now: number;
    peak_today: number;
    engagement_rate: number;
  };
}

interface AIAnalyticsMobileProps {
  refreshInterval?: number;
  enableRealtime?: boolean;
}

const AIAnalyticsMobile: React.FC<AIAnalyticsMobileProps> = ({
  refreshInterval = 30000,
  enableRealtime = true
}) => {
  // State management
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [realtimeInsights, setRealtimeInsights] = useState<RealtimeInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [selectedTimeRange, setSelectedTimeRange] = useState('7d');
  const [settingsVisible, setSettingsVisible] = useState(false);

  // Animation values
  const fadeAnim = useSharedValue(0);
  const slideAnim = useSharedValue(-width);
  const scaleAnim = useSharedValue(0.8);

  // Chart configuration
  const chartConfig = {
    backgroundGradientFrom: '#1E2139',
    backgroundGradientTo: '#1E2139',
    color: (opacity = 1) => `rgba(81, 150, 244, ${opacity})`,
    strokeWidth: 2,
    barPercentage: 0.5,
    useShadowColorFromDataset: false,
    decimalPlaces: 1,
    style: {
      borderRadius: 16,
    },
    propsForLabels: {
      fontSize: 12,
      fontWeight: 'bold',
      fill: '#FFFFFF'
    }
  };

  // Fetch analytics data
  const fetchAnalyticsData = useCallback(async () => {
    try {
      setError(null);
      const response = await fetch(`/api/v1/ai-analytics/dashboard/data?time_range=${selectedTimeRange}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      setAnalyticsData(data.data);
      
    } catch (err) {
      console.error('Error fetching analytics data:', err);
      setError('Failed to load analytics data');
      
      // Use mock data as fallback
      setAnalyticsData(getMockAnalyticsData());
    }
  }, [selectedTimeRange]);

  // Fetch real-time insights
  const fetchRealtimeInsights = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/ai-analytics/insights/realtime');
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      setRealtimeInsights(data);
      
    } catch (err) {
      console.error('Error fetching real-time insights:', err);
      setRealtimeInsights(getMockRealtimeInsights());
    }
  }, []);

  // Initialize data loading
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchAnalyticsData(),
        enableRealtime ? fetchRealtimeInsights() : Promise.resolve()
      ]);
      setLoading(false);
      
      // Animate in
      fadeAnim.value = withTiming(1, { duration: 800 });
      slideAnim.value = withSpring(0);
      scaleAnim.value = withSpring(1);
    };

    loadData();
  }, [fetchAnalyticsData, fetchRealtimeInsights, enableRealtime, fadeAnim, slideAnim, scaleAnim]);

  // Auto-refresh functionality
  useEffect(() => {
    if (!enableRealtime) return;

    const interval = setInterval(() => {
      fetchAnalyticsData();
      fetchRealtimeInsights();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval, fetchAnalyticsData, fetchRealtimeInsights, enableRealtime]);

  // Handle refresh
  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await Promise.all([
      fetchAnalyticsData(),
      enableRealtime ? fetchRealtimeInsights() : Promise.resolve()
    ]);
    setRefreshing(false);
  }, [fetchAnalyticsData, fetchRealtimeInsights, enableRealtime]);

  // Animated styles
  const containerStyle = useAnimatedStyle(() => ({
    opacity: fadeAnim.value,
    transform: [{ scale: scaleAnim.value }]
  }));

  const slideStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: slideAnim.value }]
  }));

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <LinearGradient
          colors={['#667eea', '#764ba2']}
          style={styles.loadingGradient}
        >
          <ActivityIndicator size="large" color="#FFFFFF" />
          <Text style={styles.loadingText}>Loading AI Analytics...</Text>
        </LinearGradient>
      </View>
    );
  }

  const renderMetricCard = (title: string, value: string, change: string, color: string, index: number) => (
    <Animated.View
      key={title}
      entering={FadeInUp.delay(index * 100)}
      style={[styles.metricCard, { borderLeftColor: color }]}
    >
      <Text style={styles.metricTitle}>{title}</Text>
      <Text style={[styles.metricValue, { color }]}>{value}</Text>
      <View style={styles.metricChangeContainer}>
        <Text style={styles.metricChange}>📈 {change}</Text>
      </View>
    </Animated.View>
  );

  const renderAlertCard = (alert: any, index: number) => (
    <Animated.View
      key={index}
      entering={FadeInRight.delay(index * 150)}
      style={[
        styles.alertCard,
        { 
          borderLeftColor: alert.severity === 'error' ? '#EF4444' : 
                           alert.severity === 'warning' ? '#F59E0B' : '#3B82F6' 
        }
      ]}
    >
      <Text style={styles.alertType}>
        {alert.severity === 'error' ? '🚨' : alert.severity === 'warning' ? '⚠️' : 'ℹ️'} {alert.type.toUpperCase()}
      </Text>
      <Text style={styles.alertMessage}>{alert.message}</Text>
      <Text style={styles.alertRecommendation}>💡 {alert.recommendation}</Text>
    </Animated.View>
  );

  const renderTabButton = (title: string, index: number, icon: string) => (
    <TouchableOpacity
      key={index}
      style={[
        styles.tabButton,
        activeTab === index && styles.activeTabButton
      ]}
      onPress={() => setActiveTab(index)}
    >
      <Text style={styles.tabIcon}>{icon}</Text>
      <Text style={[
        styles.tabTitle,
        activeTab === index && styles.activeTabTitle
      ]}>
        {title}
      </Text>
    </TouchableOpacity>
  );

  const renderContentAnalytics = () => {
    if (!analyticsData) return null;

    const sentimentData = [
      {
        name: 'Positive',
        population: analyticsData.content_analytics.sentiment_distribution.positive,
        color: '#10B981',
        legendFontColor: '#FFFFFF',
        legendFontSize: 12,
      },
      {
        name: 'Neutral',
        population: analyticsData.content_analytics.sentiment_distribution.neutral,
        color: '#6B7280',
        legendFontColor: '#FFFFFF',
        legendFontSize: 12,
      },
      {
        name: 'Negative',
        population: analyticsData.content_analytics.sentiment_distribution.negative,
        color: '#EF4444',
        legendFontColor: '#FFFFFF',
        legendFontSize: 12,
      },
    ];

    const engagementData = {
      labels: ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7'],
      datasets: [{
        data: analyticsData.content_analytics.engagement_trends.map(v => v * 100)
      }]
    };

    return (
      <ScrollView style={styles.tabContent} showsVerticalScrollIndicator={false}>
        <View style={styles.chartContainer}>
          <Text style={styles.chartTitle}>🎯 Sentiment Distribution</Text>
          <PieChart
            data={sentimentData}
            width={width - 60}
            height={220}
            chartConfig={chartConfig}
            accessor="population"
            backgroundColor="transparent"
            paddingLeft="15"
            absolute
          />
        </View>

        <View style={styles.chartContainer}>
          <Text style={styles.chartTitle}>📈 Engagement Trends</Text>
          <LineChart
            data={engagementData}
            width={width - 60}
            height={220}
            chartConfig={chartConfig}
            bezier
            style={styles.chart}
          />
        </View>

        <View style={styles.topicsContainer}>
          <Text style={styles.chartTitle}>🔥 Trending Topics</Text>
          {analyticsData.content_analytics.topic_trends.map((topic, index) => (
            <View key={index} style={styles.topicCard}>
              <View style={styles.topicHeader}>
                <Text style={styles.topicName}>{topic.topic}</Text>
                <Text style={styles.topicFrequency}>#{topic.frequency}</Text>
              </View>
              <View style={styles.sentimentBar}>
                <View
                  style={[
                    styles.sentimentFill,
                    {
                      width: `${topic.sentiment * 100}%`,
                      backgroundColor: topic.sentiment > 0.6 ? '#10B981' : 
                                     topic.sentiment > 0.3 ? '#F59E0B' : '#EF4444'
                    }
                  ]}
                />
              </View>
              <Text style={styles.sentimentScore}>
                Sentiment: {(topic.sentiment * 100).toFixed(1)}%
              </Text>
            </View>
          ))}
        </View>
      </ScrollView>
    );
  };

  const renderUserBehavior = () => {
    if (!analyticsData) return null;

    const retentionData = {
      labels: ['New', 'Active', 'Engaged', 'Loyal'],
      datasets: [{
        data: [
          analyticsData.user_behavior.retention_funnel.new,
          analyticsData.user_behavior.retention_funnel.active,
          analyticsData.user_behavior.retention_funnel.engaged,
          analyticsData.user_behavior.retention_funnel.loyal
        ]
      }]
    };

    return (
      <ScrollView style={styles.tabContent} showsVerticalScrollIndicator={false}>
        <View style={styles.chartContainer}>
          <Text style={styles.chartTitle}>👥 User Retention Funnel</Text>
          <BarChart
            data={retentionData}
            width={width - 60}
            height={220}
            chartConfig={chartConfig}
            style={styles.chart}
            yAxisSuffix=""
            showValuesOnTopOfBars
          />
        </View>

        <View style={styles.featuresContainer}>
          <Text style={styles.chartTitle}>⚡ Feature Adoption</Text>
          {Object.entries(analyticsData.user_behavior.feature_adoption).map(([feature, adoption], index) => (
            <View key={index} style={styles.featureCard}>
              <Text style={styles.featureName}>
                {feature.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </Text>
              <View style={styles.adoptionContainer}>
                <View style={styles.adoptionBar}>
                  <View
                    style={[
                      styles.adoptionFill,
                      {
                        width: `${adoption * 100}%`,
                        backgroundColor: adoption > 0.7 ? '#10B981' : 
                                       adoption > 0.4 ? '#F59E0B' : '#EF4444'
                      }
                    ]}
                  />
                </View>
                <Text style={styles.adoptionPercentage}>
                  {(adoption * 100).toFixed(0)}%
                </Text>
              </View>
            </View>
          ))}
        </View>

        <View style={styles.productivityContainer}>
          <Text style={styles.chartTitle}>🎯 Productivity Distribution</Text>
          <View style={styles.productivityGrid}>
            {[
              { level: 'High', count: analyticsData.user_behavior.productivity_distribution.high, color: '#10B981' },
              { level: 'Medium', count: analyticsData.user_behavior.productivity_distribution.medium, color: '#F59E0B' },
              { level: 'Low', count: analyticsData.user_behavior.productivity_distribution.low, color: '#EF4444' }
            ].map((productivity, index) => (
              <View key={index} style={[styles.productivityCard, { borderColor: productivity.color }]}>
                <Text style={[styles.productivityCount, { color: productivity.color }]}>
                  {productivity.count}
                </Text>
                <Text style={styles.productivityLevel}>{productivity.level}</Text>
              </View>
            ))}
          </View>
        </View>
      </ScrollView>
    );
  };

  const renderBusinessIntelligence = () => {
    if (!analyticsData) return null;

    return (
      <ScrollView style={styles.tabContent} showsVerticalScrollIndicator={false}>
        <View style={styles.revenueContainer}>
          <Text style={styles.chartTitle}>💰 Revenue Metrics</Text>
          <View style={styles.revenueGrid}>
            <View style={[styles.revenueCard, { borderColor: '#3B82F6' }]}>
              <Text style={styles.revenueLabel}>MRR</Text>
              <Text style={[styles.revenueValue, { color: '#3B82F6' }]}>
                ${analyticsData.business_intelligence.revenue_metrics.monthly_recurring_revenue.toLocaleString()}
              </Text>
            </View>
            <View style={[styles.revenueCard, { borderColor: '#F59E0B' }]}>
              <Text style={styles.revenueLabel}>CAC</Text>
              <Text style={[styles.revenueValue, { color: '#F59E0B' }]}>
                ${analyticsData.business_intelligence.revenue_metrics.customer_acquisition_cost}
              </Text>
            </View>
            <View style={[styles.revenueCard, { borderColor: '#10B981' }]}>
              <Text style={styles.revenueLabel}>LTV</Text>
              <Text style={[styles.revenueValue, { color: '#10B981' }]}>
                ${analyticsData.business_intelligence.revenue_metrics.customer_lifetime_value.toLocaleString()}
              </Text>
            </View>
            <View style={[styles.revenueCard, { borderColor: '#EF4444' }]}>
              <Text style={styles.revenueLabel}>Churn</Text>
              <Text style={[styles.revenueValue, { color: '#EF4444' }]}>
                {(analyticsData.business_intelligence.revenue_metrics.churn_rate * 100).toFixed(1)}%
              </Text>
            </View>
          </View>
        </View>
      </ScrollView>
    );
  };

  const renderPredictiveAnalytics = () => {
    if (!analyticsData) return null;

    const forecastData = {
      labels: ['M1', 'M2', 'M3', 'M4', 'M5', 'M6'],
      datasets: [{
        data: analyticsData.predictive_analytics.growth_forecast.slice(0, 6)
      }]
    };

    return (
      <ScrollView style={styles.tabContent} showsVerticalScrollIndicator={false}>
        <View style={styles.chartContainer}>
          <Text style={styles.chartTitle}>🔮 Growth Forecast</Text>
          <LineChart
            data={forecastData}
            width={width - 60}
            height={220}
            chartConfig={chartConfig}
            bezier
            style={styles.chart}
          />
        </View>

        <View style={styles.capacityContainer}>
          <Text style={styles.chartTitle}>⚡ Capacity Alerts</Text>
          {analyticsData.predictive_analytics.capacity_alerts.map((alert, index) => (
            <View key={index} style={[
              styles.capacityCard,
              { borderColor: alert.predicted > alert.threshold ? '#EF4444' : '#10B981' }
            ]}>
              <View style={styles.capacityHeader}>
                <Text style={styles.capacityMetric}>{alert.metric}</Text>
                {alert.predicted > alert.threshold && <Text style={styles.warningIcon}>⚠️</Text>}
              </View>
              <Text style={styles.capacityText}>
                Current: {(alert.current * 100).toFixed(1)}%
              </Text>
              <Text style={styles.capacityText}>
                Predicted: {(alert.predicted * 100).toFixed(1)}%
              </Text>
              <View style={styles.capacityBar}>
                <View
                  style={[
                    styles.capacityFill,
                    {
                      width: `${alert.predicted * 100}%`,
                      backgroundColor: alert.predicted > alert.threshold ? '#EF4444' : '#10B981'
                    }
                  ]}
                />
              </View>
            </View>
          ))}
        </View>
      </ScrollView>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <LinearGradient
        colors={['#667eea', '#764ba2']}
        style={styles.gradient}
      >
        {/* Header */}
        <Animated.View style={[styles.header, slideStyle]}>
          <View style={styles.headerLeft}>
            <Text style={styles.headerTitle}>🤖 AI Analytics</Text>
            <Text style={styles.headerSubtitle}>Advanced Intelligence Dashboard</Text>
          </View>
          <TouchableOpacity
            style={styles.settingsButton}
            onPress={() => setSettingsVisible(true)}
          >
            <Text style={styles.settingsIcon}>⚙️</Text>
          </TouchableOpacity>
        </Animated.View>

        {/* Real-time Alerts */}
        {realtimeInsights && realtimeInsights.alerts.length > 0 && (
          <View style={styles.alertsContainer}>
            <Text style={styles.alertsTitle}>🚨 AI Insights & Alerts</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              {realtimeInsights.alerts.map((alert, index) => renderAlertCard(alert, index))}
            </ScrollView>
          </View>
        )}

        {/* Key Metrics */}
        <Animated.View style={[styles.metricsContainer, containerStyle]}>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.metricsContent}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={handleRefresh}
                tintColor="#FFFFFF"
              />
            }
          >
            {analyticsData && [
              { title: 'Total Users', value: analyticsData.overview.total_users.toLocaleString(), change: '+12%', color: '#3B82F6' },
              { title: 'Active Sessions', value: analyticsData.overview.active_sessions.toString(), change: '+8%', color: '#10B981' },
              { title: 'Content Analyzed', value: analyticsData.overview.content_analyzed.toLocaleString(), change: '+25%', color: '#F59E0B' },
              { title: 'AI Insights', value: analyticsData.overview.ai_insights_generated.toLocaleString(), change: '+18%', color: '#8B5CF6' }
            ].map((metric, index) => renderMetricCard(metric.title, metric.value, metric.change, metric.color, index))}
          </ScrollView>
        </Animated.View>

        {/* Tabs */}
        <View style={styles.tabsContainer}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {renderTabButton('Content', 0, '📝')}
            {renderTabButton('Users', 1, '👥')}
            {renderTabButton('Business', 2, '💼')}
            {renderTabButton('Predictive', 3, '🔮')}
          </ScrollView>
        </View>

        {/* Tab Content */}
        <View style={styles.contentContainer}>
          {activeTab === 0 && renderContentAnalytics()}
          {activeTab === 1 && renderUserBehavior()}
          {activeTab === 2 && renderBusinessIntelligence()}
          {activeTab === 3 && renderPredictiveAnalytics()}
        </View>

        {/* Live Activity */}
        {realtimeInsights && (
          <View style={styles.liveActivity}>
            <BlurView style={styles.liveActivityBlur} blurType="dark" blurAmount={10}>
              <Text style={styles.liveActivityTitle}>📊 Live Activity</Text>
              <View style={styles.liveActivityContent}>
                <View style={styles.liveActivityItem}>
                  <Text style={styles.liveActivityLabel}>Active Now</Text>
                  <Text style={styles.liveActivityValue}>{realtimeInsights.user_activity.active_now}</Text>
                </View>
                <View style={styles.liveActivityItem}>
                  <Text style={styles.liveActivityLabel}>Peak Today</Text>
                  <Text style={styles.liveActivityValue}>{realtimeInsights.user_activity.peak_today}</Text>
                </View>
                <View style={styles.liveActivityItem}>
                  <Text style={styles.liveActivityLabel}>Engagement</Text>
                  <Text style={styles.liveActivityValue}>
                    {(realtimeInsights.user_activity.engagement_rate * 100).toFixed(0)}%
                  </Text>
                </View>
              </View>
            </BlurView>
          </View>
        )}

        {/* Settings Modal */}
        <Modal
          visible={settingsVisible}
          animationType="slide"
          transparent
          onRequestClose={() => setSettingsVisible(false)}
        >
          <View style={styles.modalOverlay}>
            <BlurView style={styles.modalBlur} blurType="dark" blurAmount={10}>
              <View style={styles.settingsModal}>
                <View style={styles.modalHeader}>
                  <Text style={styles.modalTitle}>⚙️ Settings</Text>
                  <TouchableOpacity onPress={() => setSettingsVisible(false)}>
                    <Text style={styles.modalClose}>✕</Text>
                  </TouchableOpacity>
                </View>

                <View style={styles.settingsList}>
                  <TouchableOpacity style={styles.settingsItem}>
                    <Text style={styles.settingsLabel}>Time Range</Text>
                    <Text style={styles.settingsValue}>{selectedTimeRange}</Text>
                  </TouchableOpacity>

                  <TouchableOpacity style={styles.settingsItem}>
                    <Text style={styles.settingsLabel}>Auto Refresh</Text>
                    <Text style={styles.settingsValue}>On</Text>
                  </TouchableOpacity>

                  <TouchableOpacity style={styles.settingsItem}>
                    <Text style={styles.settingsLabel}>Notifications</Text>
                    <Text style={styles.settingsValue}>Enabled</Text>
                  </TouchableOpacity>
                </View>

                <TouchableOpacity
                  style={styles.saveButton}
                  onPress={() => setSettingsVisible(false)}
                >
                  <Text style={styles.saveButtonText}>Save Settings</Text>
                </TouchableOpacity>
              </View>
            </BlurView>
          </View>
        </Modal>
      </LinearGradient>
    </SafeAreaView>
  );
};

// Mock data functions
const getMockAnalyticsData = (): AnalyticsData => ({
  overview: {
    total_users: 1247,
    active_sessions: 89,
    content_analyzed: 15420,
    ai_insights_generated: 3280
  },
  content_analytics: {
    sentiment_distribution: { positive: 65, neutral: 25, negative: 10 },
    engagement_trends: [0.7, 0.75, 0.8, 0.72, 0.85, 0.88, 0.82],
    topic_trends: [
      { topic: "AI Technology", frequency: 45, sentiment: 0.8 },
      { topic: "Business Strategy", frequency: 32, sentiment: 0.6 },
      { topic: "User Experience", frequency: 28, sentiment: 0.7 }
    ]
  },
  user_behavior: {
    retention_funnel: { new: 100, active: 75, engaged: 45, loyal: 25 },
    feature_adoption: {
      transcription: 0.95,
      collaboration: 0.68,
      analytics: 0.42,
      ai_insights: 0.35
    },
    productivity_distribution: { high: 30, medium: 50, low: 20 }
  },
  business_intelligence: {
    revenue_metrics: {
      monthly_recurring_revenue: 125430,
      customer_acquisition_cost: 85,
      customer_lifetime_value: 2400,
      churn_rate: 0.05
    }
  },
  predictive_analytics: {
    growth_forecast: [105, 112, 118, 125, 133, 140, 148],
    churn_prediction: 0.08,
    capacity_alerts: [
      { metric: "CPU", current: 0.72, predicted: 0.85, threshold: 0.8 },
      { metric: "Memory", current: 0.65, predicted: 0.75, threshold: 0.85 }
    ]
  }
});

const getMockRealtimeInsights = (): RealtimeInsights => ({
  alerts: [
    {
      type: "performance",
      severity: "warning",
      message: "Content engagement below threshold",
      recommendation: "Review content strategy"
    }
  ],
  key_metrics: {
    sentiment_score: 0.72,
    user_satisfaction: 0.84,
    system_efficiency: 0.91,
    prediction_accuracy: 0.88
  },
  trending_topics: [
    { topic: "AI Integration", growth: "+15%", sentiment: 0.8 },
    { topic: "Collaboration", growth: "+22%", sentiment: 0.9 }
  ],
  user_activity: {
    active_now: 67,
    peak_today: 124,
    engagement_rate: 0.73
  }
});

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1F2937'
  },
  gradient: {
    flex: 1
  },
  loadingContainer: {
    flex: 1
  },
  loadingGradient: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center'
  },
  loadingText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '600',
    marginTop: 16
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16
  },
  headerLeft: {
    flex: 1
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 4
  },
  headerSubtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.8)'
  },
  settingsButton: {
    padding: 8,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.2)'
  },
  settingsIcon: {
    fontSize: 20
  },
  alertsContainer: {
    paddingHorizontal: 20,
    marginBottom: 16
  },
  alertsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 12
  },
  alertCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    backdropFilter: 'blur(10px)',
    padding: 16,
    borderRadius: 12,
    marginRight: 12,
    minWidth: 280,
    borderLeftWidth: 4
  },
  alertType: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 8
  },
  alertMessage: {
    fontSize: 14,
    color: '#FFFFFF',
    marginBottom: 8
  },
  alertRecommendation: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
    fontStyle: 'italic'
  },
  metricsContainer: {
    marginBottom: 16
  },
  metricsContent: {
    paddingHorizontal: 16
  },
  metricCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    padding: 20,
    borderRadius: 16,
    marginHorizontal: 4,
    minWidth: 160,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8
  },
  metricTitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.8)',
    marginBottom: 8
  },
  metricValue: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 8
  },
  metricChangeContainer: {
    alignItems: 'flex-start'
  },
  metricChange: {
    fontSize: 12,
    color: '#10B981',
    fontWeight: '600'
  },
  tabsContainer: {
    paddingVertical: 16
  },
  tabButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    marginHorizontal: 8,
    borderRadius: 25,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    alignItems: 'center',
    minWidth: 100
  },
  activeTabButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.3)'
  },
  tabIcon: {
    fontSize: 20,
    marginBottom: 4
  },
  tabTitle: {
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: 12,
    fontWeight: '600'
  },
  activeTabTitle: {
    color: '#FFFFFF'
  },
  contentContainer: {
    flex: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    marginHorizontal: 16,
    borderRadius: 16,
    marginBottom: 80
  },
  tabContent: {
    flex: 1,
    padding: 16
  },
  chartContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16
  },
  chartTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 16,
    textAlign: 'center'
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16
  },
  topicsContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 16,
    padding: 16
  },
  topicCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    padding: 12,
    marginBottom: 12
  },
  topicHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8
  },
  topicName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF'
  },
  topicFrequency: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 12
  },
  sentimentBar: {
    height: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 8
  },
  sentimentFill: {
    height: '100%',
    borderRadius: 4
  },
  sentimentScore: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)'
  },
  featuresContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16
  },
  featureCard: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16
  },
  featureName: {
    flex: 1,
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF'
  },
  adoptionContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center'
  },
  adoptionBar: {
    flex: 1,
    height: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 4,
    overflow: 'hidden',
    marginRight: 12
  },
  adoptionFill: {
    height: '100%',
    borderRadius: 4
  },
  adoptionPercentage: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#FFFFFF',
    minWidth: 35
  },
  productivityContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 16,
    padding: 16
  },
  productivityGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around'
  },
  productivityCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    borderWidth: 2,
    minWidth: 80
  },
  productivityCount: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 4
  },
  productivityLevel: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center'
  },
  revenueContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 16,
    padding: 16
  },
  revenueGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between'
  },
  revenueCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    borderWidth: 2,
    width: '48%',
    marginBottom: 12
  },
  revenueLabel: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
    marginBottom: 4
  },
  revenueValue: {
    fontSize: 18,
    fontWeight: 'bold'
  },
  capacityContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 16,
    padding: 16
  },
  capacityCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 2
  },
  capacityHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8
  },
  capacityMetric: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF'
  },
  warningIcon: {
    fontSize: 20
  },
  capacityText: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
    marginBottom: 4
  },
  capacityBar: {
    height: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 4,
    overflow: 'hidden',
    marginTop: 8
  },
  capacityFill: {
    height: '100%',
    borderRadius: 4
  },
  liveActivity: {
    position: 'absolute',
    bottom: 16,
    left: 16,
    right: 16,
    borderRadius: 16,
    overflow: 'hidden'
  },
  liveActivityBlur: {
    padding: 16
  },
  liveActivityTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 12,
    textAlign: 'center'
  },
  liveActivityContent: {
    flexDirection: 'row',
    justifyContent: 'space-around'
  },
  liveActivityItem: {
    alignItems: 'center'
  },
  liveActivityLabel: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
    marginBottom: 4
  },
  liveActivityValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#FFFFFF'
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center'
  },
  modalBlur: {
    width: width * 0.9,
    maxWidth: 400,
    borderRadius: 20,
    overflow: 'hidden'
  },
  settingsModal: {
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
    padding: 24
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF'
  },
  modalClose: {
    fontSize: 24,
    color: '#FFFFFF'
  },
  settingsList: {
    marginBottom: 24
  },
  settingsItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)'
  },
  settingsLabel: {
    fontSize: 16,
    color: '#FFFFFF'
  },
  settingsValue: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)'
  },
  saveButton: {
    backgroundColor: '#3B82F6',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center'
  },
  saveButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#FFFFFF'
  }
});

export default AIAnalyticsMobile;