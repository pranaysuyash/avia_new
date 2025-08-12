/**
 * Business Intelligence Screen - React Native
 * ROI calculations, revenue forecasting, and business metrics
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
  Alert,
  Dimensions,
  TextInput,
} from 'react-native';
import {
  Card,
  ProgressBar,
  Chip,
  List,
  Avatar,
  IconButton,
  Surface,
  Badge,
  SegmentedButtons,
  DataTable,
  Button,
  Portal,
  Modal,
  RadioButton,
  Switch,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { LineChart, BarChart, ProgressChart, ContributionGraph } from 'react-native-chart-kit';
import Slider from '@react-native-community/slider';
import Share from 'react-native-share';

const { width: screenWidth } = Dimensions.get('window');

const chartConfig = {
  backgroundColor: '#ffffff',
  backgroundGradientFrom: '#ffffff',
  backgroundGradientTo: '#ffffff',
  decimalPlaces: 0,
  color: (opacity = 1) => `rgba(58, 123, 213, ${opacity})`,
  labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
  style: {
    borderRadius: 16,
  },
  propsForDots: {
    r: '6',
    strokeWidth: '2',
    stroke: '#3a7bd5',
  },
};

interface BusinessMetrics {
  mrr: number;
  mrrGrowth: number;
  activeUsers: number;
  userGrowth: number;
  churnRate: number;
  ltvCacRatio: number;
  revenue: number;
  costs: number;
  profit: number;
  roi: number;
}

interface ChurnPrediction {
  userId: number;
  probability: number;
  riskLevel: 'high' | 'medium' | 'low';
  revenueAtRisk: number;
}

interface RevenueForecast {
  date: string;
  predicted: number;
  lowerBound: number;
  upperBound: number;
}

interface BusinessIntelligenceProps {
  apiEndpoint?: string;
  onMetricsUpdate?: (metrics: BusinessMetrics) => void;
}

const BusinessIntelligence: React.FC<BusinessIntelligenceProps> = ({
  apiEndpoint = '/api/intelligence/business',
  onMetricsUpdate,
}) => {
  const [metrics, setMetrics] = useState<BusinessMetrics | null>(null);
  const [forecast, setForecast] = useState<RevenueForecast[]>([]);
  const [churnPredictions, setChurnPredictions] = useState<ChurnPrediction[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedTab, setSelectedTab] = useState('overview');
  const [forecastMonths, setForecastMonths] = useState(12);
  const [includeSeasonality, setIncludeSeasonality] = useState(true);
  const [scenario, setScenario] = useState<'most_likely' | 'best_case' | 'worst_case'>('most_likely');
  const [roiModalVisible, setRoiModalVisible] = useState(false);
  const [roiInputs, setRoiInputs] = useState({
    acquisition: '50000',
    operational: '30000',
    marketing: '20000',
    subscription: '150000',
    transaction: '30000',
    addon: '10000',
  });

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = useCallback(async () => {
    setIsLoading(true);

    try {
      // Mock data for demonstration
      const mockMetrics: BusinessMetrics = {
        mrr: 125000,
        mrrGrowth: 8.5,
        activeUsers: 1250,
        userGrowth: 6.8,
        churnRate: 4.5,
        ltvCacRatio: 3.2,
        revenue: 150000,
        costs: 100000,
        profit: 50000,
        roi: 50,
      };

      setMetrics(mockMetrics);
      
      if (onMetricsUpdate) {
        onMetricsUpdate(mockMetrics);
      }
    } catch (err) {
      Alert.alert('Error', 'Failed to load business metrics');
      console.error('Metrics error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [onMetricsUpdate]);

  const generateForecast = useCallback(async () => {
    setIsLoading(true);
    try {
      // Mock forecast data
      const mockForecast: RevenueForecast[] = [];
      const baseRevenue = metrics?.mrr || 125000;
      const growthRate = scenario === 'best_case' ? 0.10 : scenario === 'worst_case' ? 0.02 : 0.05;

      for (let i = 1; i <= forecastMonths; i++) {
        const date = new Date();
        date.setMonth(date.getMonth() + i);
        
        let predicted = baseRevenue * Math.pow(1 + growthRate, i);
        if (includeSeasonality) {
          const month = date.getMonth();
          if (month === 11 || month === 0) predicted *= 1.2; // Holiday boost
          if (month === 6 || month === 7) predicted *= 0.9; // Summer dip
        }
        
        mockForecast.push({
          date: date.toISOString().split('T')[0],
          predicted,
          lowerBound: predicted * 0.85,
          upperBound: predicted * 1.15,
        });
      }

      setForecast(mockForecast);
    } catch (err) {
      console.error('Forecast error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [metrics, forecastMonths, includeSeasonality, scenario]);

  const predictChurn = useCallback(async () => {
    setIsLoading(true);
    try {
      // Mock churn predictions
      const mockPredictions: ChurnPrediction[] = [
        { userId: 101, probability: 0.85, riskLevel: 'high', revenueAtRisk: 500 },
        { userId: 102, probability: 0.72, riskLevel: 'high', revenueAtRisk: 450 },
        { userId: 103, probability: 0.45, riskLevel: 'medium', revenueAtRisk: 300 },
        { userId: 104, probability: 0.38, riskLevel: 'medium', revenueAtRisk: 250 },
        { userId: 105, probability: 0.15, riskLevel: 'low', revenueAtRisk: 100 },
      ];

      setChurnPredictions(mockPredictions);
    } catch (err) {
      console.error('Churn prediction error:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const calculateROI = useCallback(() => {
    const totalInvestment = 
      parseFloat(roiInputs.acquisition) + 
      parseFloat(roiInputs.operational) + 
      parseFloat(roiInputs.marketing);
    
    const totalRevenue = 
      parseFloat(roiInputs.subscription) + 
      parseFloat(roiInputs.transaction) + 
      parseFloat(roiInputs.addon);
    
    const profit = totalRevenue - totalInvestment;
    const roi = (profit / totalInvestment) * 100;
    
    Alert.alert(
      'ROI Calculation',
      `Total Investment: $${totalInvestment.toLocaleString()}\n` +
      `Total Revenue: $${totalRevenue.toLocaleString()}\n` +
      `Profit: $${profit.toLocaleString()}\n` +
      `ROI: ${roi.toFixed(1)}%`
    );
    
    setRoiModalVisible(false);
  }, [roiInputs]);

  const exportMetrics = useCallback(async () => {
    if (!metrics) return;

    try {
      const shareOptions = {
        title: 'Business Intelligence Report',
        message: `Business Intelligence Report
        
KPIs:
MRR: $${(metrics.mrr / 1000).toFixed(0)}K (${metrics.mrrGrowth > 0 ? '+' : ''}${metrics.mrrGrowth}%)
Active Users: ${metrics.activeUsers.toLocaleString()} (${metrics.userGrowth > 0 ? '+' : ''}${metrics.userGrowth}%)
Churn Rate: ${metrics.churnRate}%
LTV:CAC Ratio: ${metrics.ltvCacRatio}x

Financial:
Revenue: $${(metrics.revenue / 1000).toFixed(0)}K
Costs: $${(metrics.costs / 1000).toFixed(0)}K
Profit: $${(metrics.profit / 1000).toFixed(0)}K
ROI: ${metrics.roi}%`,
      };

      await Share.open(shareOptions);
    } catch (error) {
      console.log('Share error:', error);
    }
  }, [metrics]);

  const renderKPICard = (
    icon: string,
    title: string,
    value: string,
    change: number,
    trend: 'up' | 'down' | 'neutral',
    color: string
  ) => (
    <Surface style={styles.kpiCard} elevation={2}>
      <View style={styles.kpiHeader}>
        <Icon name={icon} size={24} color={color} />
        {trend === 'up' && <Icon name="trending-up" size={20} color="#4caf50" />}
        {trend === 'down' && <Icon name="trending-down" size={20} color="#f44336" />}
      </View>
      <Text style={[styles.kpiValue, { color }]}>{value}</Text>
      <Text style={styles.kpiTitle}>{title}</Text>
      <Text style={[styles.kpiChange, { color: change > 0 ? '#4caf50' : '#f44336' }]}>
        {change > 0 ? '+' : ''}{change}% MoM
      </Text>
    </Surface>
  );

  const renderOverviewTab = () => {
    if (!metrics) return null;

    const healthScores = [
      { name: 'Revenue', score: 85, color: '#4caf50' },
      { name: 'Users', score: 78, color: '#2196f3' },
      { name: 'Product', score: 82, color: '#ff9800' },
      { name: 'Financial', score: 79, color: '#9c27b0' },
    ];

    const revenueData = {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
      datasets: [
        {
          data: [95000, 98000, 105000, 112000, 118000, 125000],
        },
      ],
    };

    return (
      <ScrollView style={styles.tabContent}>
        <View style={styles.kpiGrid}>
          {renderKPICard(
            'cash',
            'Monthly Recurring Revenue',
            `$${(metrics.mrr / 1000).toFixed(0)}K`,
            metrics.mrrGrowth,
            metrics.mrrGrowth > 0 ? 'up' : 'down',
            '#3a7bd5'
          )}
          {renderKPICard(
            'account-group',
            'Active Users',
            metrics.activeUsers.toLocaleString(),
            metrics.userGrowth,
            metrics.userGrowth > 0 ? 'up' : 'down',
            '#00d2ff'
          )}
          {renderKPICard(
            'account-remove',
            'Churn Rate',
            `${metrics.churnRate}%`,
            -0.3,
            metrics.churnRate < 5 ? 'up' : 'down',
            metrics.churnRate < 5 ? '#4caf50' : '#f44336'
          )}
          {renderKPICard(
            'chart-line',
            'LTV:CAC Ratio',
            `${metrics.ltvCacRatio}x`,
            0.2,
            metrics.ltvCacRatio > 3 ? 'up' : 'neutral',
            '#764ba2'
          )}
        </View>

        <Card style={styles.card}>
          <Card.Title title="Health Scores" left={(props) => <Avatar.Icon {...props} icon="heart-pulse" />} />
          <Card.Content>
            <View style={styles.healthGrid}>
              {healthScores.map((health) => (
                <View key={health.name} style={styles.healthItem}>
                  <ProgressChart
                    data={{
                      labels: [health.name],
                      data: [health.score / 100],
                    }}
                    width={80}
                    height={80}
                    strokeWidth={8}
                    radius={28}
                    chartConfig={{
                      ...chartConfig,
                      color: () => health.color,
                    }}
                    hideLegend
                  />
                  <Text style={styles.healthScore}>{health.score}</Text>
                  <Text style={styles.healthName}>{health.name}</Text>
                </View>
              ))}
            </View>
          </Card.Content>
        </Card>

        <Card style={styles.card}>
          <Card.Title title="Revenue Trend" left={(props) => <Avatar.Icon {...props} icon="chart-line" />} />
          <Card.Content>
            <LineChart
              data={revenueData}
              width={screenWidth - 64}
              height={220}
              yAxisLabel="$"
              yAxisSuffix="K"
              chartConfig={chartConfig}
              bezier
              style={styles.chart}
            />
          </Card.Content>
        </Card>
      </ScrollView>
    );
  };

  const renderForecastTab = () => (
    <ScrollView style={styles.tabContent}>
      <Card style={styles.card}>
        <Card.Title title="Revenue Forecast" left={(props) => <Avatar.Icon {...props} icon="chart-timeline-variant" />} />
        <Card.Content>
          <View style={styles.forecastControls}>
            <Text style={styles.controlLabel}>Scenario</Text>
            <RadioButton.Group onValueChange={value => setScenario(value as any)} value={scenario}>
              <View style={styles.radioRow}>
                <RadioButton.Item label="Most Likely" value="most_likely" />
                <RadioButton.Item label="Best Case" value="best_case" />
                <RadioButton.Item label="Worst Case" value="worst_case" />
              </View>
            </RadioButton.Group>

            <Text style={styles.controlLabel}>Forecast Months: {forecastMonths}</Text>
            <Slider
              style={styles.slider}
              minimumValue={3}
              maximumValue={24}
              step={3}
              value={forecastMonths}
              onValueChange={setForecastMonths}
              minimumTrackTintColor="#3a7bd5"
              maximumTrackTintColor="#e0e0e0"
            />

            <View style={styles.switchRow}>
              <Text style={styles.controlLabel}>Include Seasonality</Text>
              <Switch value={includeSeasonality} onValueChange={setIncludeSeasonality} />
            </View>

            <Button
              mode="contained"
              onPress={generateForecast}
              loading={isLoading}
              disabled={isLoading}
              style={styles.generateButton}
              icon="chart-line"
            >
              Generate Forecast
            </Button>
          </View>

          {forecast.length > 0 && (
            <LineChart
              data={{
                labels: forecast.slice(0, 6).map((f, i) => `M${i + 1}`),
                datasets: [
                  {
                    data: forecast.slice(0, 6).map(f => f.predicted),
                    color: () => '#3a7bd5',
                  },
                  {
                    data: forecast.slice(0, 6).map(f => f.upperBound),
                    color: () => '#4caf50',
                    withDots: false,
                  },
                  {
                    data: forecast.slice(0, 6).map(f => f.lowerBound),
                    color: () => '#f44336',
                    withDots: false,
                  },
                ],
                legend: ['Predicted', 'Upper', 'Lower'],
              }}
              width={screenWidth - 64}
              height={250}
              yAxisLabel="$"
              yAxisSuffix="K"
              chartConfig={chartConfig}
              style={styles.chart}
            />
          )}
        </Card.Content>
      </Card>
    </ScrollView>
  );

  const renderChurnTab = () => (
    <ScrollView style={styles.tabContent}>
      <Card style={styles.card}>
        <Card.Title 
          title="Churn Risk Analysis" 
          left={(props) => <Avatar.Icon {...props} icon="alert" style={{ backgroundColor: '#f44336' }} />}
        />
        <Card.Content>
          <Button
            mode="contained"
            onPress={predictChurn}
            loading={isLoading}
            disabled={isLoading}
            style={styles.analyzeButton}
            icon="account-alert"
          >
            Analyze Churn Risk
          </Button>

          {churnPredictions.length > 0 && (
            <DataTable style={styles.table}>
              <DataTable.Header>
                <DataTable.Title>User ID</DataTable.Title>
                <DataTable.Title numeric>Risk</DataTable.Title>
                <DataTable.Title>Level</DataTable.Title>
                <DataTable.Title numeric>Revenue</DataTable.Title>
              </DataTable.Header>

              {churnPredictions.map((prediction) => (
                <DataTable.Row key={prediction.userId}>
                  <DataTable.Cell>{prediction.userId}</DataTable.Cell>
                  <DataTable.Cell numeric>
                    {(prediction.probability * 100).toFixed(0)}%
                  </DataTable.Cell>
                  <DataTable.Cell>
                    <Chip
                      mode="flat"
                      style={[
                        styles.riskChip,
                        prediction.riskLevel === 'high' && styles.highRisk,
                        prediction.riskLevel === 'medium' && styles.mediumRisk,
                        prediction.riskLevel === 'low' && styles.lowRisk,
                      ]}
                    >
                      {prediction.riskLevel.toUpperCase()}
                    </Chip>
                  </DataTable.Cell>
                  <DataTable.Cell numeric>${prediction.revenueAtRisk}</DataTable.Cell>
                </DataTable.Row>
              ))}
            </DataTable>
          )}

          <Card style={[styles.card, styles.alertCard]}>
            <Card.Content>
              <Text style={styles.alertTitle}>Action Items</Text>
              <Text style={styles.alertText}>• Contact high-risk users immediately</Text>
              <Text style={styles.alertText}>• Offer retention incentives</Text>
              <Text style={styles.alertText}>• Schedule follow-up calls</Text>
            </Card.Content>
          </Card>
        </Card.Content>
      </Card>
    </ScrollView>
  );

  const renderROITab = () => (
    <ScrollView style={styles.tabContent}>
      <Card style={styles.card}>
        <Card.Title 
          title="ROI Calculator" 
          left={(props) => <Avatar.Icon {...props} icon="calculator" />}
        />
        <Card.Content>
          <Button
            mode="contained"
            onPress={() => setRoiModalVisible(true)}
            style={styles.calculateButton}
            icon="calculator"
          >
            Open ROI Calculator
          </Button>

          <View style={styles.opportunitiesSection}>
            <Text style={styles.sectionTitle}>Growth Opportunities</Text>
            
            <Surface style={[styles.opportunityCard, { backgroundColor: '#e8f5e9' }]} elevation={1}>
              <Icon name="trending-up" size={32} color="#4caf50" />
              <View style={styles.opportunityContent}>
                <Text style={styles.opportunityTitle}>Upsell Opportunities</Text>
                <Text style={styles.opportunityValue}>23 users</Text>
                <Text style={styles.opportunityRevenue}>$12,500/month potential</Text>
              </View>
            </Surface>

            <Surface style={[styles.opportunityCard, { backgroundColor: '#fce4ec' }]} elevation={1}>
              <Icon name="account-reactivate" size={32} color="#e91e63" />
              <View style={styles.opportunityContent}>
                <Text style={styles.opportunityTitle}>Win-Back Campaign</Text>
                <Text style={styles.opportunityValue}>45 users</Text>
                <Text style={styles.opportunityRevenue}>$8,200/month recovery</Text>
              </View>
            </Surface>

            <Surface style={[styles.opportunityCard, { backgroundColor: '#e3f2fd' }]} elevation={1}>
              <Icon name="account-multiple-plus" size={32} color="#2196f3" />
              <View style={styles.opportunityContent}>
                <Text style={styles.opportunityTitle}>New Market Segment</Text>
                <Text style={styles.opportunityValue}>Enterprise tier</Text>
                <Text style={styles.opportunityRevenue}>$50K+ MRR potential</Text>
              </View>
            </Surface>
          </View>
        </Card.Content>
      </Card>
    </ScrollView>
  );

  return (
    <View style={styles.container}>
      <Surface style={styles.header} elevation={4}>
        <View style={styles.headerContent}>
          <Icon name="chart-pie" size={32} color="white" />
          <View style={styles.headerText}>
            <Text style={styles.headerTitle}>Business Intelligence</Text>
            <Text style={styles.headerSubtitle}>
              KPIs, forecasting, and ROI analytics
            </Text>
          </View>
        </View>
      </Surface>

      <SegmentedButtons
        value={selectedTab}
        onValueChange={setSelectedTab}
        buttons={[
          { value: 'overview', label: 'Overview', icon: 'view-dashboard' },
          { value: 'forecast', label: 'Forecast', icon: 'chart-line' },
          { value: 'churn', label: 'Churn', icon: 'alert' },
          { value: 'roi', label: 'ROI', icon: 'calculator' },
        ]}
        style={styles.tabs}
      />

      {isLoading && !metrics ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#3a7bd5" />
        </View>
      ) : (
        <>
          {selectedTab === 'overview' && renderOverviewTab()}
          {selectedTab === 'forecast' && renderForecastTab()}
          {selectedTab === 'churn' && renderChurnTab()}
          {selectedTab === 'roi' && renderROITab()}
        </>
      )}

      <Portal>
        <Modal
          visible={roiModalVisible}
          onDismiss={() => setRoiModalVisible(false)}
          contentContainerStyle={styles.modal}
        >
          <Text style={styles.modalTitle}>ROI Calculator</Text>
          
          <Text style={styles.modalSection}>Investment</Text>
          <TextInput
            style={styles.modalInput}
            placeholder="Customer Acquisition"
            value={roiInputs.acquisition}
            onChangeText={(text) => setRoiInputs({ ...roiInputs, acquisition: text })}
            keyboardType="numeric"
          />
          <TextInput
            style={styles.modalInput}
            placeholder="Operational Costs"
            value={roiInputs.operational}
            onChangeText={(text) => setRoiInputs({ ...roiInputs, operational: text })}
            keyboardType="numeric"
          />
          <TextInput
            style={styles.modalInput}
            placeholder="Marketing Spend"
            value={roiInputs.marketing}
            onChangeText={(text) => setRoiInputs({ ...roiInputs, marketing: text })}
            keyboardType="numeric"
          />
          
          <Text style={styles.modalSection}>Revenue</Text>
          <TextInput
            style={styles.modalInput}
            placeholder="Subscription Revenue"
            value={roiInputs.subscription}
            onChangeText={(text) => setRoiInputs({ ...roiInputs, subscription: text })}
            keyboardType="numeric"
          />
          <TextInput
            style={styles.modalInput}
            placeholder="Transaction Revenue"
            value={roiInputs.transaction}
            onChangeText={(text) => setRoiInputs({ ...roiInputs, transaction: text })}
            keyboardType="numeric"
          />
          <TextInput
            style={styles.modalInput}
            placeholder="Add-on Revenue"
            value={roiInputs.addon}
            onChangeText={(text) => setRoiInputs({ ...roiInputs, addon: text })}
            keyboardType="numeric"
          />
          
          <View style={styles.modalButtons}>
            <Button mode="outlined" onPress={() => setRoiModalVisible(false)}>
              Cancel
            </Button>
            <Button mode="contained" onPress={calculateROI}>
              Calculate
            </Button>
          </View>
        </Modal>
      </Portal>

      <Button
        mode="contained"
        onPress={exportMetrics}
        style={styles.exportButton}
        icon="share-variant"
      >
        Export Report
      </Button>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#3a7bd5',
    paddingVertical: 20,
    paddingHorizontal: 16,
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerText: {
    marginLeft: 12,
    flex: 1,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
  },
  headerSubtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.9)',
    marginTop: 2,
  },
  tabs: {
    margin: 16,
  },
  tabContent: {
    flex: 1,
    paddingHorizontal: 16,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  kpiGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  kpiCard: {
    width: '48%',
    padding: 16,
    marginBottom: 12,
    borderRadius: 12,
  },
  kpiHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  kpiValue: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  kpiTitle: {
    fontSize: 12,
    color: '#666',
  },
  kpiChange: {
    fontSize: 12,
    fontWeight: 'bold',
    marginTop: 4,
  },
  card: {
    marginBottom: 16,
  },
  healthGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 16,
  },
  healthItem: {
    alignItems: 'center',
  },
  healthScore: {
    position: 'absolute',
    top: 28,
    fontSize: 18,
    fontWeight: 'bold',
  },
  healthName: {
    fontSize: 12,
    marginTop: 4,
    color: '#666',
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  forecastControls: {
    marginBottom: 16,
  },
  controlLabel: {
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 8,
    color: '#333',
  },
  radioRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 16,
  },
  slider: {
    height: 40,
    marginBottom: 16,
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  generateButton: {
    marginBottom: 16,
  },
  analyzeButton: {
    marginBottom: 16,
  },
  table: {
    marginTop: 16,
  },
  riskChip: {
    height: 24,
  },
  highRisk: {
    backgroundColor: '#ffebee',
  },
  mediumRisk: {
    backgroundColor: '#fff3e0',
  },
  lowRisk: {
    backgroundColor: '#e8f5e9',
  },
  alertCard: {
    marginTop: 16,
    backgroundColor: '#fff3e0',
  },
  alertTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  alertText: {
    fontSize: 14,
    marginBottom: 4,
    color: '#333',
  },
  calculateButton: {
    marginBottom: 24,
  },
  opportunitiesSection: {
    marginTop: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  opportunityCard: {
    flexDirection: 'row',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    alignItems: 'center',
  },
  opportunityContent: {
    marginLeft: 16,
    flex: 1,
  },
  opportunityTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
  },
  opportunityValue: {
    fontSize: 18,
    fontWeight: 'bold',
    marginVertical: 4,
  },
  opportunityRevenue: {
    fontSize: 14,
    color: '#666',
  },
  exportButton: {
    position: 'absolute',
    bottom: 16,
    left: 16,
    right: 16,
  },
  modal: {
    backgroundColor: 'white',
    padding: 20,
    margin: 20,
    borderRadius: 8,
    maxHeight: '80%',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  modalSection: {
    fontSize: 16,
    fontWeight: 'bold',
    marginTop: 16,
    marginBottom: 8,
  },
  modalInput: {
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    fontSize: 14,
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 16,
  },
});

export default BusinessIntelligence;