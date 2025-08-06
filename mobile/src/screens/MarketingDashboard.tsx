import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
  ActivityIndicator,
  FlatList,
  Alert,
  Dimensions,
} from 'react-native';
import { Card, Button, Badge, ProgressBar, ListItem } from 'react-native-elements';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { apiClient, Campaign } from '../services/apiClient';
import { LineChart, BarChart } from 'react-native-chart-kit';

const { width: screenWidth } = Dimensions.get('window');

const MarketingDashboard: React.FC = () => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [growthMetrics, setGrowthMetrics] = useState<any>(null);
  const [referralStats, setReferralStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedTab, setSelectedTab] = useState<'campaigns' | 'analytics' | 'referrals'>('campaigns');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [campaignsData, growthData, referralData] = await Promise.all([
        apiClient.getCampaigns(),
        apiClient.getGrowthMetrics(),
        apiClient.getReferralStats(),
      ]);
      setCampaigns(campaignsData);
      setGrowthMetrics(growthData);
      setReferralStats(referralData);
    } catch (error) {
      Alert.alert('Error', 'Failed to load marketing data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      draft: '#95a5a6',
      scheduled: '#3498db',
      running: '#2ecc71',
      paused: '#f39c12',
      completed: '#27ae60',
    };
    return colors[status] || '#95a5a6';
  };

  const renderMetricsCard = () => (
    <Card containerStyle={styles.metricsCard}>
      <Text style={styles.cardTitle}>Marketing Overview</Text>
      {growthMetrics && (
        <View>
          <View style={styles.metricsRow}>
            <View style={styles.metric}>
              <Text style={styles.metricValue}>
                ${(growthMetrics.summary?.total_spent / 1000).toFixed(0)}k
              </Text>
              <Text style={styles.metricLabel}>Total Spend</Text>
            </View>
            <View style={styles.metric}>
              <Text style={styles.metricValue}>
                ${(growthMetrics.summary?.total_revenue / 1000).toFixed(0)}k
              </Text>
              <Text style={styles.metricLabel}>Revenue</Text>
            </View>
          </View>
          <View style={styles.metricsRow}>
            <View style={styles.metric}>
              <Text style={styles.metricValue}>
                {growthMetrics.summary?.overall_roi?.toFixed(0)}%
              </Text>
              <Text style={styles.metricLabel}>ROI</Text>
            </View>
            <View style={styles.metric}>
              <Text style={styles.metricValue}>
                {campaigns.filter(c => c.status === 'running').length}
              </Text>
              <Text style={styles.metricLabel}>Active Campaigns</Text>
            </View>
          </View>
        </View>
      )}
    </Card>
  );

  const renderCampaignItem = ({ item }: { item: Campaign }) => {
    const spentPercentage = (item.spent / item.budget) * 100;
    const ctr = item.metrics.impressions > 0 
      ? ((item.metrics.clicks / item.metrics.impressions) * 100).toFixed(2)
      : '0';

    return (
      <Card containerStyle={styles.campaignCard}>
        <View style={styles.campaignHeader}>
          <View style={{ flex: 1 }}>
            <Text style={styles.campaignName}>{item.name}</Text>
            <View style={styles.campaignMeta}>
              <Badge
                value={item.type}
                textStyle={styles.typeBadgeText}
                badgeStyle={styles.typeBadge}
              />
              <Badge
                value={item.status}
                badgeStyle={[styles.statusBadge, { backgroundColor: getStatusColor(item.status) }]}
                textStyle={styles.statusBadgeText}
              />
            </View>
          </View>
          <View style={styles.roiContainer}>
            <Text style={[styles.roi, { color: item.metrics.roi > 0 ? '#27ae60' : '#e74c3c' }]}>
              {item.metrics.roi > 0 ? '+' : ''}{item.metrics.roi}%
            </Text>
            <Text style={styles.roiLabel}>ROI</Text>
          </View>
        </View>

        <View style={styles.campaignMetrics}>
          <View style={styles.metricItem}>
            <Icon name="visibility" size={16} color="#7f8c8d" />
            <Text style={styles.metricText}>{item.metrics.impressions}</Text>
          </View>
          <View style={styles.metricItem}>
            <Icon name="touch-app" size={16} color="#7f8c8d" />
            <Text style={styles.metricText}>{item.metrics.clicks} ({ctr}%)</Text>
          </View>
          <View style={styles.metricItem}>
            <Icon name="trending-up" size={16} color="#7f8c8d" />
            <Text style={styles.metricText}>{item.metrics.conversions}</Text>
          </View>
        </View>

        <View style={styles.budgetSection}>
          <View style={styles.budgetHeader}>
            <Text style={styles.budgetLabel}>Budget Usage</Text>
            <Text style={styles.budgetText}>
              ${item.spent} / ${item.budget}
            </Text>
          </View>
          <ProgressBar
            progress={spentPercentage / 100}
            color={spentPercentage > 90 ? '#e74c3c' : '#3498db'}
            style={styles.progressBar}
          />
        </View>
      </Card>
    );
  };

  const renderAnalytics = () => {
    if (!growthMetrics?.by_channel) return null;

    const channelData = Object.entries(growthMetrics.by_channel);
    const chartData = {
      labels: channelData.map(([channel]) => channel),
      datasets: [{
        data: channelData.map(([, data]: [string, any]) => data.revenue / 1000),
      }],
    };

    return (
      <ScrollView style={styles.analyticsContainer}>
        <Card containerStyle={styles.chartCard}>
          <Text style={styles.chartTitle}>Revenue by Channel (in $K)</Text>
          <BarChart
            data={chartData}
            width={screenWidth - 60}
            height={220}
            yAxisLabel="$"
            yAxisSuffix="k"
            chartConfig={{
              backgroundColor: '#ffffff',
              backgroundGradientFrom: '#ffffff',
              backgroundGradientTo: '#ffffff',
              decimalPlaces: 0,
              color: (opacity = 1) => `rgba(52, 152, 219, ${opacity})`,
              labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
              style: {
                borderRadius: 16,
              },
            }}
            style={styles.chart}
          />
        </Card>
      </ScrollView>
    );
  };

  const renderReferrals = () => (
    <ScrollView style={styles.referralsContainer}>
      <Card containerStyle={styles.referralStatsCard}>
        <Text style={styles.cardTitle}>Referral Program</Text>
        <View style={styles.referralStats}>
          <View style={styles.referralMetric}>
            <Text style={styles.referralValue}>{referralStats?.total_referrals || 0}</Text>
            <Text style={styles.referralLabel}>Total Referrals</Text>
          </View>
          <View style={styles.referralMetric}>
            <Text style={[styles.referralValue, { color: '#27ae60' }]}>
              {referralStats?.successful_referrals || 0}
            </Text>
            <Text style={styles.referralLabel}>Successful</Text>
          </View>
          <View style={styles.referralMetric}>
            <Text style={[styles.referralValue, { color: '#3498db' }]}>
              ${referralStats?.total_rewards?.credits || 0}
            </Text>
            <Text style={styles.referralLabel}>Rewards Earned</Text>
          </View>
        </View>
      </Card>

      <Card containerStyle={styles.referralActionsCard}>
        <Button
          title="Generate Referral Code"
          icon={<Icon name="share" size={20} color="white" style={{ marginRight: 10 }} />}
          buttonStyle={styles.referralButton}
          onPress={() => Alert.alert('Referral Code', 'Your referral code: REF2024XYZ')}
        />
        <Button
          title="View My Referrals"
          type="outline"
          buttonStyle={styles.referralOutlineButton}
          onPress={() => Alert.alert('My Referrals', 'Referral history coming soon!')}
        />
      </Card>
    </ScrollView>
  );

  const renderTabs = () => (
    <View style={styles.tabContainer}>
      <TouchableOpacity
        style={[styles.tab, selectedTab === 'campaigns' && styles.activeTab]}
        onPress={() => setSelectedTab('campaigns')}
      >
        <Text style={[styles.tabText, selectedTab === 'campaigns' && styles.activeTabText]}>
          Campaigns
        </Text>
      </TouchableOpacity>
      
      <TouchableOpacity
        style={[styles.tab, selectedTab === 'analytics' && styles.activeTab]}
        onPress={() => setSelectedTab('analytics')}
      >
        <Text style={[styles.tabText, selectedTab === 'analytics' && styles.activeTabText]}>
          Analytics
        </Text>
      </TouchableOpacity>
      
      <TouchableOpacity
        style={[styles.tab, selectedTab === 'referrals' && styles.activeTab]}
        onPress={() => setSelectedTab('referrals')}
      >
        <Text style={[styles.tabText, selectedTab === 'referrals' && styles.activeTabText]}>
          Referrals
        </Text>
      </TouchableOpacity>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#3498db" />
        <Text style={styles.loadingText}>Loading marketing data...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
      >
        {renderMetricsCard()}
        {renderTabs()}
        
        {selectedTab === 'campaigns' && (
          <FlatList
            data={campaigns}
            renderItem={renderCampaignItem}
            keyExtractor={item => item.id}
            scrollEnabled={false}
            contentContainerStyle={styles.campaignsList}
          />
        )}
        
        {selectedTab === 'analytics' && renderAnalytics()}
        {selectedTab === 'referrals' && renderReferrals()}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  metricsCard: {
    margin: 15,
    borderRadius: 10,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
    color: '#2c3e50',
  },
  metricsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 15,
  },
  metric: {
    alignItems: 'center',
  },
  metricValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#3498db',
  },
  metricLabel: {
    fontSize: 12,
    color: '#7f8c8d',
    marginTop: 5,
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: 'white',
    marginHorizontal: 15,
    borderRadius: 10,
    marginBottom: 15,
    elevation: 2,
  },
  tab: {
    flex: 1,
    paddingVertical: 15,
    alignItems: 'center',
  },
  activeTab: {
    borderBottomWidth: 3,
    borderBottomColor: '#3498db',
  },
  tabText: {
    fontSize: 14,
    color: '#95a5a6',
  },
  activeTabText: {
    color: '#3498db',
    fontWeight: '600',
  },
  campaignsList: {
    paddingHorizontal: 15,
    paddingBottom: 20,
  },
  campaignCard: {
    marginBottom: 15,
    borderRadius: 10,
    elevation: 2,
  },
  campaignHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 15,
  },
  campaignName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 5,
  },
  campaignMeta: {
    flexDirection: 'row',
    gap: 5,
  },
  typeBadge: {
    backgroundColor: '#ecf0f1',
  },
  typeBadgeText: {
    color: '#7f8c8d',
    fontSize: 12,
  },
  statusBadge: {
    paddingHorizontal: 10,
  },
  statusBadgeText: {
    fontSize: 12,
    textTransform: 'capitalize',
  },
  roiContainer: {
    alignItems: 'center',
  },
  roi: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  roiLabel: {
    fontSize: 12,
    color: '#7f8c8d',
  },
  campaignMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 15,
    paddingVertical: 10,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: '#ecf0f1',
  },
  metricItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  metricText: {
    fontSize: 14,
    color: '#7f8c8d',
  },
  budgetSection: {
    marginTop: 10,
  },
  budgetHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  budgetLabel: {
    fontSize: 14,
    color: '#7f8c8d',
  },
  budgetText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2c3e50',
  },
  progressBar: {
    height: 8,
    borderRadius: 4,
  },
  analyticsContainer: {
    flex: 1,
  },
  chartCard: {
    margin: 15,
    borderRadius: 10,
  },
  chartTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 15,
    color: '#2c3e50',
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  referralsContainer: {
    flex: 1,
  },
  referralStatsCard: {
    margin: 15,
    borderRadius: 10,
  },
  referralStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  referralMetric: {
    alignItems: 'center',
  },
  referralValue: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#3498db',
  },
  referralLabel: {
    fontSize: 12,
    color: '#7f8c8d',
    marginTop: 5,
  },
  referralActionsCard: {
    marginHorizontal: 15,
    marginBottom: 15,
    borderRadius: 10,
  },
  referralButton: {
    backgroundColor: '#3498db',
    borderRadius: 25,
    paddingVertical: 12,
    marginBottom: 10,
  },
  referralOutlineButton: {
    borderRadius: 25,
    paddingVertical: 12,
    borderColor: '#3498db',
  },
});

export default MarketingDashboard;