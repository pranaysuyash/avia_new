/**
 * User Engagement Analytics Screen - React Native
 * Task 202: Advanced User Engagement Analytics
 * Mobile app screen for viewing user behavior analytics
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  Dimensions,
  ActivityIndicator,
  FlatList,
  SafeAreaView,
} from 'react-native';
import {
  LineChart,
  BarChart,
  PieChart,
  ProgressChart,
} from 'react-native-chart-kit';
import Icon from 'react-native-vector-icons/MaterialIcons';

const { width: screenWidth } = Dimensions.get('window');

interface MetricCard {
  title: string;
  value: string | number;
  change: string;
  icon: string;
  color: string;
}

interface ChurnRiskUser {
  id: string;
  name: string;
  risk: number;
  lastSeen: string;
  reason: string;
}

const UserEngagementAnalytics: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState<'overview' | 'behavior' | 'churn'>('overview');
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState('7d');
  const [metrics, setMetrics] = useState({
    totalUsers: 1432,
    activeUsers: 892,
    avgSession: 12.5,
    retentionRate: 76.8,
  });

  // Chart configuration
  const chartConfig = {
    backgroundGradientFrom: '#ffffff',
    backgroundGradientTo: '#ffffff',
    color: (opacity = 1) => `rgba(59, 130, 246, ${opacity})`,
    strokeWidth: 2,
    barPercentage: 0.5,
    decimalPlaces: 0,
  };

  // Mock data
  const dailyActiveUsersData = {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [
      {
        data: [1250, 1380, 1420, 1390, 1490, 1120, 980],
      },
    ],
  };

  const engagementPieData = [
    {
      name: 'High',
      population: 35,
      color: '#10b981',
      legendFontColor: '#7F7F7F',
      legendFontSize: 12,
    },
    {
      name: 'Medium',
      population: 45,
      color: '#3b82f6',
      legendFontColor: '#7F7F7F',
      legendFontSize: 12,
    },
    {
      name: 'Low',
      population: 15,
      color: '#f59e0b',
      legendFontColor: '#7F7F7F',
      legendFontSize: 12,
    },
    {
      name: 'Inactive',
      population: 5,
      color: '#ef4444',
      legendFontColor: '#7F7F7F',
      legendFontSize: 12,
    },
  ];

  const featureUsageData = {
    labels: ['Transcription', 'Translation', 'Summary', 'Search', 'Export'],
    data: [0.89, 0.67, 0.78, 0.92, 0.45],
  };

  const churnRiskUsers: ChurnRiskUser[] = [
    {
      id: '1',
      name: 'John Doe',
      risk: 85,
      lastSeen: '7 days ago',
      reason: 'Decreased activity',
    },
    {
      id: '2',
      name: 'Jane Smith',
      risk: 72,
      lastSeen: '5 days ago',
      reason: 'Feature usage decline',
    },
    {
      id: '3',
      name: 'Bob Johnson',
      risk: 68,
      lastSeen: '4 days ago',
      reason: 'Support tickets',
    },
  ];

  const onRefresh = React.useCallback(() => {
    setRefreshing(true);
    // Fetch new data
    setTimeout(() => {
      setRefreshing(false);
    }, 2000);
  }, []);

  const renderMetricCard = ({ title, value, change, icon, color }: MetricCard) => (
    <View style={[styles.metricCard, { borderLeftColor: color }]}>
      <View style={styles.metricCardContent}>
        <Text style={styles.metricTitle}>{title}</Text>
        <Text style={styles.metricValue}>{value}</Text>
        <Text style={[styles.metricChange, { color: change.startsWith('+') ? '#10b981' : '#ef4444' }]}>
          {change}
        </Text>
      </View>
      <Icon name={icon} size={24} color={color} />
    </View>
  );

  const renderOverview = () => (
    <ScrollView
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Metrics Grid */}
      <View style={styles.metricsGrid}>
        {renderMetricCard({
          title: 'Total Users',
          value: metrics.totalUsers,
          change: '+12%',
          icon: 'people',
          color: '#3b82f6',
        })}
        {renderMetricCard({
          title: 'Active Users',
          value: metrics.activeUsers,
          change: '+8%',
          icon: 'trending-up',
          color: '#10b981',
        })}
        {renderMetricCard({
          title: 'Avg Session',
          value: `${metrics.avgSession}m`,
          change: '+5%',
          icon: 'timer',
          color: '#8b5cf6',
        })}
        {renderMetricCard({
          title: 'Retention',
          value: `${metrics.retentionRate}%`,
          change: '+3%',
          icon: 'cached',
          color: '#f59e0b',
        })}
      </View>

      {/* Daily Active Users Chart */}
      <View style={styles.chartContainer}>
        <Text style={styles.chartTitle}>Daily Active Users</Text>
        <LineChart
          data={dailyActiveUsersData}
          width={screenWidth - 40}
          height={220}
          chartConfig={chartConfig}
          bezier
          style={styles.chart}
        />
      </View>

      {/* Engagement Distribution */}
      <View style={styles.chartContainer}>
        <Text style={styles.chartTitle}>Engagement Distribution</Text>
        <PieChart
          data={engagementPieData}
          width={screenWidth - 40}
          height={220}
          chartConfig={chartConfig}
          accessor="population"
          backgroundColor="transparent"
          paddingLeft="15"
          absolute
        />
      </View>
    </ScrollView>
  );

  const renderBehavior = () => (
    <ScrollView
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Feature Usage */}
      <View style={styles.chartContainer}>
        <Text style={styles.chartTitle}>Feature Usage</Text>
        <ProgressChart
          data={featureUsageData}
          width={screenWidth - 40}
          height={220}
          strokeWidth={16}
          radius={32}
          chartConfig={chartConfig}
          hideLegend={false}
        />
      </View>

      {/* User Journey Funnel */}
      <View style={styles.chartContainer}>
        <Text style={styles.chartTitle}>User Journey Funnel</Text>
        <View style={styles.funnelContainer}>
          {[
            { stage: 'Sign Up', users: 1000, width: 100 },
            { stage: 'First Upload', users: 850, width: 85 },
            { stage: 'First Transcription', users: 720, width: 72 },
            { stage: 'Regular Usage', users: 540, width: 54 },
            { stage: 'Power User', users: 180, width: 18 },
          ].map((stage, index) => (
            <View key={stage.stage} style={styles.funnelStage}>
              <View
                style={[
                  styles.funnelBar,
                  {
                    width: `${stage.width}%`,
                    backgroundColor: index < 3 ? '#3b82f6' : '#10b981',
                  },
                ]}
              >
                <Text style={styles.funnelLabel}>{stage.stage}</Text>
                <Text style={styles.funnelValue}>{stage.users}</Text>
              </View>
            </View>
          ))}
        </View>
      </View>

      {/* Session Patterns */}
      <View style={styles.chartContainer}>
        <Text style={styles.chartTitle}>Session Distribution by Hour</Text>
        <BarChart
          data={{
            labels: ['00', '06', '12', '18', '24'],
            datasets: [{ data: [120, 150, 420, 340, 280] }],
          }}
          width={screenWidth - 40}
          height={220}
          chartConfig={chartConfig}
          style={styles.chart}
          yAxisLabel=""
          yAxisSuffix=""
        />
      </View>
    </ScrollView>
  );

  const renderChurnRiskUser = ({ item }: { item: ChurnRiskUser }) => (
    <TouchableOpacity style={styles.churnUserCard}>
      <View style={styles.churnUserInfo}>
        <Text style={styles.churnUserName}>{item.name}</Text>
        <Text style={styles.churnUserLastSeen}>{item.lastSeen}</Text>
        <Text style={styles.churnUserReason}>{item.reason}</Text>
      </View>
      <View style={styles.churnUserRiskContainer}>
        <Text
          style={[
            styles.churnUserRisk,
            {
              color: item.risk >= 80 ? '#ef4444' : item.risk >= 60 ? '#f59e0b' : '#10b981',
            },
          ]}
        >
          {item.risk}%
        </Text>
        <View style={styles.riskBar}>
          <View
            style={[
              styles.riskBarFill,
              {
                width: `${item.risk}%`,
                backgroundColor:
                  item.risk >= 80 ? '#ef4444' : item.risk >= 60 ? '#f59e0b' : '#10b981',
              },
            ]}
          />
        </View>
      </View>
      <TouchableOpacity style={styles.contactButton}>
        <Icon name="message" size={20} color="#3b82f6" />
      </TouchableOpacity>
    </TouchableOpacity>
  );

  const renderChurn = () => (
    <View style={styles.container}>
      {/* Churn Risk Summary */}
      <View style={styles.churnSummary}>
        <View style={styles.churnSummaryCard}>
          <Text style={styles.churnSummaryValue}>23</Text>
          <Text style={styles.churnSummaryLabel}>High Risk Users</Text>
        </View>
        <View style={styles.churnSummaryCard}>
          <Text style={styles.churnSummaryValue}>45</Text>
          <Text style={styles.churnSummaryLabel}>Medium Risk</Text>
        </View>
        <View style={styles.churnSummaryCard}>
          <Text style={styles.churnSummaryValue}>12%</Text>
          <Text style={styles.churnSummaryLabel}>Churn Rate</Text>
        </View>
      </View>

      {/* At-Risk Users List */}
      <Text style={styles.sectionTitle}>Users at Risk</Text>
      <FlatList
        data={churnRiskUsers}
        renderItem={renderChurnRiskUser}
        keyExtractor={(item) => item.id}
        showsVerticalScrollIndicator={false}
      />

      {/* Prevention Actions */}
      <View style={styles.preventionActions}>
        <Text style={styles.sectionTitle}>Prevention Actions</Text>
        <TouchableOpacity style={styles.actionButton}>
          <Icon name="email" size={20} color="#fff" />
          <Text style={styles.actionButtonText}>Send Re-engagement Campaign</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.actionButton, styles.secondaryButton]}>
          <Icon name="school" size={20} color="#3b82f6" />
          <Text style={[styles.actionButtonText, { color: '#3b82f6' }]}>
            Launch Tutorial Program
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Engagement Analytics</Text>
        <TouchableOpacity style={styles.dateRangeButton}>
          <Text style={styles.dateRangeText}>Last 7 Days</Text>
          <Icon name="arrow-drop-down" size={20} color="#666" />
        </TouchableOpacity>
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabContainer}>
        {(['overview', 'behavior', 'churn'] as const).map((tab) => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, selectedTab === tab && styles.activeTab]}
            onPress={() => setSelectedTab(tab)}
          >
            <Text style={[styles.tabText, selectedTab === tab && styles.activeTabText]}>
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Content */}
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#3b82f6" />
        </View>
      ) : (
        <>
          {selectedTab === 'overview' && renderOverview()}
          {selectedTab === 'behavior' && renderBehavior()}
          {selectedTab === 'churn' && renderChurn()}
        </>
      )}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  dateRangeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 8,
  },
  dateRangeText: {
    fontSize: 14,
    color: '#666',
    marginRight: 4,
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#3b82f6',
  },
  tabText: {
    fontSize: 14,
    color: '#666',
  },
  activeTabText: {
    color: '#3b82f6',
    fontWeight: '600',
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 10,
  },
  metricCard: {
    width: '48%',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 15,
    margin: '1%',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderLeftWidth: 3,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  metricCardContent: {
    flex: 1,
  },
  metricTitle: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 2,
  },
  metricChange: {
    fontSize: 12,
    fontWeight: '600',
  },
  chartContainer: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 15,
    margin: 10,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  chartTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 10,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  funnelContainer: {
    paddingVertical: 10,
  },
  funnelStage: {
    marginVertical: 5,
  },
  funnelBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
  },
  funnelLabel: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 14,
  },
  funnelValue: {
    color: '#fff',
    fontSize: 12,
  },
  churnSummary: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: 15,
    backgroundColor: '#fff',
    marginBottom: 10,
  },
  churnSummaryCard: {
    alignItems: 'center',
  },
  churnSummaryValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  churnSummaryLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    paddingHorizontal: 20,
    paddingVertical: 10,
  },
  churnUserCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    marginHorizontal: 20,
    marginVertical: 5,
    padding: 15,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  churnUserInfo: {
    flex: 1,
  },
  churnUserName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  churnUserLastSeen: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  churnUserReason: {
    fontSize: 12,
    color: '#999',
    marginTop: 2,
  },
  churnUserRiskContainer: {
    alignItems: 'center',
    marginHorizontal: 15,
  },
  churnUserRisk: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  riskBar: {
    width: 60,
    height: 4,
    backgroundColor: '#e0e0e0',
    borderRadius: 2,
  },
  riskBarFill: {
    height: '100%',
    borderRadius: 2,
  },
  contactButton: {
    padding: 8,
  },
  preventionActions: {
    padding: 20,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#3b82f6',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    marginBottom: 10,
  },
  secondaryButton: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#3b82f6',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 8,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
});

export default UserEngagementAnalytics;