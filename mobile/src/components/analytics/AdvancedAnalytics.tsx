/**
 * Advanced Analytics Component for React Native
 * Mobile-optimized analytics with touch gestures and native features
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
  ActivityIndicator,
  Dimensions,
  Platform,
  Alert,
  Share,
  Vibration,
  StatusBar,
  SafeAreaView,
  FlatList,
  SectionList,
  Modal,
  TextInput,
  Switch,
  Animated,
  PanResponder,
  LayoutAnimation,
  UIManager,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import * as FileSystem from 'expo-file-system';
import * as Sharing from 'expo-sharing';
import * as Notifications from 'expo-notifications';
import * as Haptics from 'expo-haptics';
import {
  LineChart,
  BarChart,
  PieChart,
  ProgressChart,
  ContributionGraph,
  StackedBarChart,
} from 'react-native-chart-kit';
import { MaterialIcons, Ionicons, FontAwesome5 } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import DateTimePicker from '@react-native-community/datetimepicker';
import { Picker } from '@react-native-picker/picker';
import Carousel from 'react-native-snap-carousel';
import { PinchGestureHandler, State } from 'react-native-gesture-handler';

// Enable LayoutAnimation on Android
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

// Types
interface AnalyticsData {
  query: {
    report_type: string;
    start_date: string;
    end_date: string;
    granularity: string;
    filters: Record<string, any>;
    group_by: string[];
    metrics: string[];
  };
  data: any[];
  summary: Record<string, any>;
  insights: string[];
  visualizations: Record<string, string>;
  export_formats: string[];
  generated_at: string;
}

interface ReportType {
  id: string;
  name: string;
  description: string;
  metrics: string[];
}

// Constants
const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');
const CHART_CONFIG = {
  backgroundColor: '#ffffff',
  backgroundGradientFrom: '#ffffff',
  backgroundGradientTo: '#ffffff',
  decimalPlaces: 0,
  color: (opacity = 1) => `rgba(99, 102, 241, ${opacity})`,
  labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
  style: {
    borderRadius: 16,
  },
  propsForDots: {
    r: '6',
    strokeWidth: '2',
    stroke: '#6366f1',
  },
  propsForBackgroundLines: {
    strokeDasharray: '',
  },
};

const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6'];

const AdvancedAnalytics: React.FC = () => {
  const insets = useSafeAreaInsets();
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [reportTypes, setReportTypes] = useState<Record<string, ReportType>>({});
  const [selectedReportType, setSelectedReportType] = useState('user_activity');
  const [startDate, setStartDate] = useState(new Date(Date.now() - 7 * 24 * 60 * 60 * 1000));
  const [endDate, setEndDate] = useState(new Date());
  const [showStartDatePicker, setShowStartDatePicker] = useState(false);
  const [showEndDatePicker, setShowEndDatePicker] = useState(false);
  const [granularity, setGranularity] = useState('daily');
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>([]);
  const [currentView, setCurrentView] = useState<'dashboard' | 'config' | 'insights'>('dashboard');
  const [showExportModal, setShowExportModal] = useState(false);
  const [selectedChartIndex, setSelectedChartIndex] = useState(0);
  const [chartScale, setChartScale] = useState(1);
  const [isOffline, setIsOffline] = useState(false);
  const [cachedData, setCachedData] = useState<AnalyticsData | null>(null);
  const scrollY = useRef(new Animated.Value(0)).current;
  const chartScaleAnim = useRef(new Animated.Value(1)).current;
  const carouselRef = useRef<any>(null);

  // Setup notifications
  useEffect(() => {
    const setupNotifications = async () => {
      const { status } = await Notifications.requestPermissionsAsync();
      if (status === 'granted') {
        Notifications.setNotificationHandler({
          handleNotification: async () => ({
            shouldShowAlert: true,
            shouldPlaySound: false,
            shouldSetBadge: false,
          }),
        });
      }
    };
    setupNotifications();
  }, []);

  // Network monitoring
  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((state) => {
      setIsOffline(!state.isConnected);
      if (!state.isConnected) {
        loadCachedData();
      }
    });
    return () => unsubscribe();
  }, []);

  // Load cached data
  const loadCachedData = async () => {
    try {
      const cached = await AsyncStorage.getItem('analytics_cache');
      if (cached) {
        setCachedData(JSON.parse(cached));
      }
    } catch (error) {
      console.error('Failed to load cached data:', error);
    }
  };

  // Fetch report types
  const fetchReportTypes = async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${process.env.API_URL}/api/v1/analytics/report-types`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) throw new Error('Failed to fetch report types');

      const data = await response.json();
      setReportTypes(data.report_types);
      
      // Set default metrics
      if (data.report_types[selectedReportType]) {
        setSelectedMetrics(data.report_types[selectedReportType].metrics);
      }
    } catch (error) {
      console.error('Failed to fetch report types:', error);
      Alert.alert('Error', 'Failed to load report types');
    }
  };

  // Generate analytics
  const generateAnalytics = async () => {
    if (isOffline) {
      Alert.alert('Offline', 'Cannot generate analytics while offline');
      return;
    }

    setLoading(true);
    try {
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${process.env.API_URL}/api/v1/analytics/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          report_type: selectedReportType,
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString(),
          granularity,
          filters: {},
          group_by: [],
          metrics: selectedMetrics,
          include_predictions: false,
          include_benchmarks: false,
        }),
      });

      if (!response.ok) throw new Error('Failed to generate analytics');

      const data = await response.json();
      setAnalyticsData(data);
      
      // Cache data for offline access
      await AsyncStorage.setItem('analytics_cache', JSON.stringify(data));
      
      // Show notification
      await Notifications.scheduleNotificationAsync({
        content: {
          title: 'Analytics Ready',
          body: `Found ${data.insights.length} insights in your data`,
        },
        trigger: null,
      });
      
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setCurrentView('dashboard');
      
    } catch (error) {
      console.error('Failed to generate analytics:', error);
      Alert.alert('Error', 'Failed to generate analytics');
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Export analytics
  const exportAnalytics = async (format: string) => {
    if (!analyticsData) return;

    try {
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(
        `${process.env.API_URL}/api/v1/analytics/export/current`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            format,
            include_visualizations: true,
          }),
        }
      );

      if (!response.ok) throw new Error('Failed to export analytics');

      const data = await response.text();
      
      // Save to device
      const fileUri = `${FileSystem.documentDirectory}analytics_${Date.now()}.${format}`;
      await FileSystem.writeAsStringAsync(fileUri, data);
      
      // Share file
      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(fileUri);
      } else {
        Alert.alert('Success', `File saved: ${fileUri}`);
      }
      
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      setShowExportModal(false);
      
    } catch (error) {
      console.error('Failed to export analytics:', error);
      Alert.alert('Error', 'Failed to export analytics');
    }
  };

  // Handle refresh
  const handleRefresh = useCallback(() => {
    setRefreshing(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    generateAnalytics();
  }, []);

  // Initial load
  useEffect(() => {
    fetchReportTypes();
    loadCachedData();
  }, []);

  // Pinch to zoom gesture for charts
  const onPinchGestureEvent = Animated.event(
    [{ nativeEvent: { scale: chartScaleAnim } }],
    { useNativeDriver: true }
  );

  const onPinchHandlerStateChange = (event: any) => {
    if (event.nativeEvent.oldState === State.ACTIVE) {
      const scale = Math.min(Math.max(event.nativeEvent.scale, 0.8), 2);
      setChartScale(scale);
      Animated.spring(chartScaleAnim, {
        toValue: scale,
        useNativeDriver: true,
      }).start();
    }
  };

  // Render summary card
  const renderSummaryCard = ({ item }: { item: [string, any] }) => {
    const [key, value] = item;
    const formattedKey = key.replace(/_/g, ' ').toUpperCase();
    const formattedValue = typeof value === 'number' ? value.toLocaleString() : value;

    return (
      <TouchableOpacity
        style={styles.summaryCard}
        onPress={() => {
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          Alert.alert(formattedKey, `Current value: ${formattedValue}`);
        }}
      >
        <LinearGradient
          colors={['#6366f1', '#8b5cf6']}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.summaryCardGradient}
        >
          <Text style={styles.summaryCardLabel}>{formattedKey}</Text>
          <Text style={styles.summaryCardValue}>{formattedValue}</Text>
        </LinearGradient>
      </TouchableOpacity>
    );
  };

  // Render chart carousel
  const renderChartCarousel = () => {
    if (!analyticsData || analyticsData.data.length === 0) return null;

    const charts = [
      {
        type: 'line',
        title: 'Trend Analysis',
        component: (
          <LineChart
            data={{
              labels: analyticsData.data.slice(0, 7).map((d: any) => 
                new Date(d.time || d.date).toLocaleDateString('en', { day: 'numeric', month: 'short' })
              ),
              datasets: selectedMetrics.map((metric, index) => ({
                data: analyticsData.data.slice(0, 7).map((d: any) => d[metric] || 0),
                color: (opacity = 1) => COLORS[index % COLORS.length],
                strokeWidth: 2,
              })),
            }}
            width={SCREEN_WIDTH - 32}
            height={220}
            chartConfig={CHART_CONFIG}
            bezier
            style={styles.chart}
          />
        ),
      },
      {
        type: 'bar',
        title: 'Distribution',
        component: (
          <BarChart
            data={{
              labels: analyticsData.data.slice(0, 5).map((d: any) => 
                d.name || new Date(d.time || d.date).toLocaleDateString('en', { day: 'numeric' })
              ),
              datasets: [{
                data: analyticsData.data.slice(0, 5).map((d: any) => 
                  d[selectedMetrics[0]] || d.value || 0
                ),
              }],
            }}
            width={SCREEN_WIDTH - 32}
            height={220}
            chartConfig={CHART_CONFIG}
            style={styles.chart}
            showValuesOnTopOfBars
          />
        ),
      },
      {
        type: 'pie',
        title: 'Breakdown',
        component: (
          <PieChart
            data={selectedMetrics.slice(0, 4).map((metric, index) => ({
              name: metric,
              population: analyticsData.summary[`${metric}_total`] || Math.random() * 100,
              color: COLORS[index % COLORS.length],
              legendFontColor: '#7F7F7F',
              legendFontSize: 12,
            }))}
            width={SCREEN_WIDTH - 32}
            height={220}
            chartConfig={CHART_CONFIG}
            accessor="population"
            backgroundColor="transparent"
            paddingLeft="15"
            absolute
          />
        ),
      },
    ];

    return (
      <PinchGestureHandler
        onGestureEvent={onPinchGestureEvent}
        onHandlerStateChange={onPinchHandlerStateChange}
      >
        <Animated.View style={{ transform: [{ scale: chartScaleAnim }] }}>
          <Carousel
            ref={carouselRef}
            data={charts}
            renderItem={({ item }) => (
              <View style={styles.chartContainer}>
                <Text style={styles.chartTitle}>{item.title}</Text>
                {item.component}
              </View>
            )}
            sliderWidth={SCREEN_WIDTH}
            itemWidth={SCREEN_WIDTH - 20}
            onSnapToItem={(index) => setSelectedChartIndex(index)}
          />
          <View style={styles.chartIndicators}>
            {charts.map((_, index) => (
              <View
                key={index}
                style={[
                  styles.chartIndicator,
                  index === selectedChartIndex && styles.chartIndicatorActive,
                ]}
              />
            ))}
          </View>
        </Animated.View>
      </PinchGestureHandler>
    );
  };

  // Render insights
  const renderInsights = () => {
    if (!analyticsData || analyticsData.insights.length === 0) {
      return (
        <View style={styles.emptyInsights}>
          <MaterialIcons name="lightbulb-outline" size={48} color="#9ca3af" />
          <Text style={styles.emptyInsightsText}>No insights available</Text>
        </View>
      );
    }

    return (
      <FlatList
        data={analyticsData.insights}
        keyExtractor={(_, index) => `insight-${index}`}
        renderItem={({ item, index }) => (
          <TouchableOpacity
            style={styles.insightCard}
            onPress={() => {
              Share.share({
                message: item,
                title: 'Analytics Insight',
              });
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
            }}
          >
            <View style={styles.insightCardHeader}>
              <MaterialIcons name="lightbulb" size={24} color="#f59e0b" />
              <Text style={styles.insightCardNumber}>Insight #{index + 1}</Text>
            </View>
            <Text style={styles.insightCardText}>{item}</Text>
            <TouchableOpacity style={styles.insightShareButton}>
              <MaterialIcons name="share" size={20} color="#6366f1" />
            </TouchableOpacity>
          </TouchableOpacity>
        )}
        contentContainerStyle={styles.insightsList}
      />
    );
  };

  // Render configuration
  const renderConfiguration = () => {
    return (
      <ScrollView style={styles.configContainer} showsVerticalScrollIndicator={false}>
        <View style={styles.configSection}>
          <Text style={styles.configSectionTitle}>Report Type</Text>
          <View style={styles.pickerContainer}>
            <Picker
              selectedValue={selectedReportType}
              onValueChange={(value) => {
                setSelectedReportType(value);
                setSelectedMetrics(reportTypes[value]?.metrics || []);
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
              }}
              style={styles.picker}
            >
              {Object.entries(reportTypes).map(([id, report]) => (
                <Picker.Item key={id} label={report.name} value={id} />
              ))}
            </Picker>
          </View>
        </View>

        <View style={styles.configSection}>
          <Text style={styles.configSectionTitle}>Date Range</Text>
          <TouchableOpacity
            style={styles.dateButton}
            onPress={() => setShowStartDatePicker(true)}
          >
            <MaterialIcons name="date-range" size={20} color="#6366f1" />
            <Text style={styles.dateButtonText}>
              Start: {startDate.toLocaleDateString()}
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.dateButton}
            onPress={() => setShowEndDatePicker(true)}
          >
            <MaterialIcons name="date-range" size={20} color="#6366f1" />
            <Text style={styles.dateButtonText}>
              End: {endDate.toLocaleDateString()}
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.configSection}>
          <Text style={styles.configSectionTitle}>Granularity</Text>
          <View style={styles.granularityOptions}>
            {['hourly', 'daily', 'weekly', 'monthly'].map((option) => (
              <TouchableOpacity
                key={option}
                style={[
                  styles.granularityOption,
                  granularity === option && styles.granularityOptionActive,
                ]}
                onPress={() => {
                  setGranularity(option);
                  Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                }}
              >
                <Text
                  style={[
                    styles.granularityOptionText,
                    granularity === option && styles.granularityOptionTextActive,
                  ]}
                >
                  {option.charAt(0).toUpperCase() + option.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <View style={styles.configSection}>
          <Text style={styles.configSectionTitle}>Metrics</Text>
          <View style={styles.metricsContainer}>
            {reportTypes[selectedReportType]?.metrics.map((metric) => (
              <TouchableOpacity
                key={metric}
                style={[
                  styles.metricChip,
                  selectedMetrics.includes(metric) && styles.metricChipActive,
                ]}
                onPress={() => {
                  if (selectedMetrics.includes(metric)) {
                    setSelectedMetrics(selectedMetrics.filter((m) => m !== metric));
                  } else {
                    setSelectedMetrics([...selectedMetrics, metric]);
                  }
                  Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                }}
              >
                <Text
                  style={[
                    styles.metricChipText,
                    selectedMetrics.includes(metric) && styles.metricChipTextActive,
                  ]}
                >
                  {metric.replace(/_/g, ' ')}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <TouchableOpacity
          style={[styles.generateButton, loading && styles.generateButtonDisabled]}
          onPress={generateAnalytics}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <>
              <MaterialIcons name="analytics" size={24} color="#ffffff" />
              <Text style={styles.generateButtonText}>Generate Analytics</Text>
            </>
          )}
        </TouchableOpacity>
      </ScrollView>
    );
  };

  // Render dashboard
  const renderDashboard = () => {
    const data = isOffline && cachedData ? cachedData : analyticsData;
    
    if (!data) {
      return (
        <View style={styles.emptyState}>
          <MaterialIcons name="analytics" size={64} color="#9ca3af" />
          <Text style={styles.emptyStateTitle}>No Analytics Data</Text>
          <Text style={styles.emptyStateText}>
            Configure your report and tap "Generate Analytics"
          </Text>
          <TouchableOpacity
            style={styles.emptyStateButton}
            onPress={() => setCurrentView('config')}
          >
            <Text style={styles.emptyStateButtonText}>Configure Report</Text>
          </TouchableOpacity>
        </View>
      );
    }

    return (
      <Animated.ScrollView
        style={styles.dashboard}
        onScroll={Animated.event(
          [{ nativeEvent: { contentOffset: { y: scrollY } } }],
          { useNativeDriver: true }
        )}
        scrollEventThrottle={16}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
      >
        {isOffline && (
          <View style={styles.offlineBanner}>
            <MaterialIcons name="cloud-off" size={16} color="#ef4444" />
            <Text style={styles.offlineBannerText}>Showing cached data</Text>
          </View>
        )}

        {/* Summary Cards */}
        <View style={styles.summarySection}>
          <Text style={styles.sectionTitle}>Summary</Text>
          <FlatList
            data={Object.entries(data.summary).slice(0, 4)}
            renderItem={renderSummaryCard}
            keyExtractor={([key]) => key}
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.summaryList}
          />
        </View>

        {/* Charts */}
        <View style={styles.chartSection}>
          <Text style={styles.sectionTitle}>Visualizations</Text>
          {renderChartCarousel()}
        </View>

        {/* Quick Stats */}
        <View style={styles.quickStatsSection}>
          <Text style={styles.sectionTitle}>Quick Stats</Text>
          <View style={styles.quickStatsGrid}>
            {Object.entries(data.summary).slice(4, 8).map(([key, value]) => (
              <View key={key} style={styles.quickStatItem}>
                <Text style={styles.quickStatLabel}>{key.replace(/_/g, ' ')}</Text>
                <Text style={styles.quickStatValue}>
                  {typeof value === 'number' ? value.toFixed(1) : value}
                </Text>
              </View>
            ))}
          </View>
        </View>

        {/* Data Table Preview */}
        <View style={styles.dataTableSection}>
          <Text style={styles.sectionTitle}>Data Preview</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View>
              <View style={styles.dataTableHeader}>
                {data.data.length > 0 &&
                  Object.keys(data.data[0]).slice(0, 4).map((key) => (
                    <Text key={key} style={styles.dataTableHeaderCell}>
                      {key}
                    </Text>
                  ))}
              </View>
              {data.data.slice(0, 5).map((row, index) => (
                <View key={index} style={styles.dataTableRow}>
                  {Object.values(row).slice(0, 4).map((value: any, i) => (
                    <Text key={i} style={styles.dataTableCell}>
                      {typeof value === 'number' ? value.toFixed(2) : value}
                    </Text>
                  ))}
                </View>
              ))}
            </View>
          </ScrollView>
          {data.data.length > 5 && (
            <Text style={styles.dataTableFooter}>
              Showing 5 of {data.data.length} rows
            </Text>
          )}
        </View>
      </Animated.ScrollView>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#ffffff" />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Advanced Analytics</Text>
        <View style={styles.headerActions}>
          {analyticsData && (
            <TouchableOpacity
              style={styles.headerButton}
              onPress={() => setShowExportModal(true)}
            >
              <MaterialIcons name="file-download" size={24} color="#6366f1" />
            </TouchableOpacity>
          )}
          <TouchableOpacity
            style={styles.headerButton}
            onPress={() => {
              Alert.alert(
                'Analytics Help',
                'Generate comprehensive reports with insights and visualizations. Choose report type, date range, and metrics to analyze your data.',
                [{ text: 'OK' }]
              );
            }}
          >
            <MaterialIcons name="help-outline" size={24} color="#6366f1" />
          </TouchableOpacity>
        </View>
      </View>

      {/* Navigation Tabs */}
      <View style={styles.navTabs}>
        <TouchableOpacity
          style={[styles.navTab, currentView === 'dashboard' && styles.navTabActive]}
          onPress={() => {
            setCurrentView('dashboard');
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          }}
        >
          <MaterialIcons
            name="dashboard"
            size={24}
            color={currentView === 'dashboard' ? '#6366f1' : '#6b7280'}
          />
          <Text style={[styles.navTabText, currentView === 'dashboard' && styles.navTabTextActive]}>
            Dashboard
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.navTab, currentView === 'config' && styles.navTabActive]}
          onPress={() => {
            setCurrentView('config');
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          }}
        >
          <MaterialIcons
            name="settings"
            size={24}
            color={currentView === 'config' ? '#6366f1' : '#6b7280'}
          />
          <Text style={[styles.navTabText, currentView === 'config' && styles.navTabTextActive]}>
            Configure
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.navTab, currentView === 'insights' && styles.navTabActive]}
          onPress={() => {
            setCurrentView('insights');
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          }}
        >
          <MaterialIcons
            name="lightbulb"
            size={24}
            color={currentView === 'insights' ? '#6366f1' : '#6b7280'}
          />
          <Text style={[styles.navTabText, currentView === 'insights' && styles.navTabTextActive]}>
            Insights
          </Text>
        </TouchableOpacity>
      </View>

      {/* Content */}
      {currentView === 'dashboard' && renderDashboard()}
      {currentView === 'config' && renderConfiguration()}
      {currentView === 'insights' && renderInsights()}

      {/* Date Pickers */}
      {showStartDatePicker && (
        <DateTimePicker
          value={startDate}
          mode="date"
          display="default"
          onChange={(event, date) => {
            setShowStartDatePicker(false);
            if (date) setStartDate(date);
          }}
        />
      )}
      {showEndDatePicker && (
        <DateTimePicker
          value={endDate}
          mode="date"
          display="default"
          onChange={(event, date) => {
            setShowEndDatePicker(false);
            if (date) setEndDate(date);
          }}
        />
      )}

      {/* Export Modal */}
      <Modal
        visible={showExportModal}
        animationType="slide"
        transparent
        onRequestClose={() => setShowExportModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Export Analytics</Text>
              <TouchableOpacity onPress={() => setShowExportModal(false)}>
                <MaterialIcons name="close" size={24} color="#6b7280" />
              </TouchableOpacity>
            </View>

            <View style={styles.exportOptions}>
              <TouchableOpacity
                style={styles.exportOption}
                onPress={() => exportAnalytics('csv')}
              >
                <MaterialIcons name="table-chart" size={32} color="#6366f1" />
                <Text style={styles.exportOptionText}>CSV</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.exportOption}
                onPress={() => exportAnalytics('json')}
              >
                <MaterialIcons name="code" size={32} color="#6366f1" />
                <Text style={styles.exportOptionText}>JSON</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.exportOption}
                onPress={() => exportAnalytics('excel')}
              >
                <MaterialIcons name="grid-on" size={32} color="#6366f1" />
                <Text style={styles.exportOptionText}>Excel</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.exportOption, { opacity: 0.5 }]}
                disabled
              >
                <MaterialIcons name="picture-as-pdf" size={32} color="#6366f1" />
                <Text style={styles.exportOptionText}>PDF</Text>
                <Text style={styles.exportOptionSubtext}>Enterprise</Text>
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
    backgroundColor: '#f3f4f6',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1f2937',
  },
  headerActions: {
    flexDirection: 'row',
  },
  headerButton: {
    marginLeft: 16,
  },
  navTabs: {
    flexDirection: 'row',
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  navTab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
  },
  navTabActive: {
    borderBottomWidth: 2,
    borderBottomColor: '#6366f1',
  },
  navTabText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#6b7280',
    fontWeight: '500',
  },
  navTabTextActive: {
    color: '#6366f1',
  },
  dashboard: {
    flex: 1,
  },
  offlineBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fee2e2',
    paddingVertical: 8,
  },
  offlineBannerText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#ef4444',
  },
  summarySection: {
    paddingTop: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1f2937',
    marginBottom: 12,
    paddingHorizontal: 16,
  },
  summaryList: {
    paddingHorizontal: 16,
  },
  summaryCard: {
    marginRight: 12,
    borderRadius: 12,
    overflow: 'hidden',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  summaryCardGradient: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    minWidth: 140,
  },
  summaryCardLabel: {
    fontSize: 12,
    color: '#ffffff',
    opacity: 0.9,
    marginBottom: 4,
  },
  summaryCardValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  chartSection: {
    marginTop: 24,
  },
  chartContainer: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 10,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
  },
  chartTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
    marginBottom: 12,
  },
  chart: {
    borderRadius: 12,
  },
  chartIndicators: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 12,
  },
  chartIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#d1d5db',
    marginHorizontal: 4,
  },
  chartIndicatorActive: {
    backgroundColor: '#6366f1',
  },
  quickStatsSection: {
    marginTop: 24,
    paddingHorizontal: 16,
  },
  quickStatsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -8,
  },
  quickStatItem: {
    width: '50%',
    paddingHorizontal: 8,
    marginBottom: 16,
  },
  quickStatLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 4,
  },
  quickStatValue: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1f2937',
  },
  dataTableSection: {
    marginTop: 24,
    paddingHorizontal: 16,
    marginBottom: 24,
  },
  dataTableHeader: {
    flexDirection: 'row',
    backgroundColor: '#f3f4f6',
    paddingVertical: 8,
  },
  dataTableHeaderCell: {
    width: 100,
    paddingHorizontal: 12,
    fontSize: 12,
    fontWeight: '600',
    color: '#4b5563',
  },
  dataTableRow: {
    flexDirection: 'row',
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
    paddingVertical: 8,
  },
  dataTableCell: {
    width: 100,
    paddingHorizontal: 12,
    fontSize: 14,
    color: '#1f2937',
  },
  dataTableFooter: {
    marginTop: 8,
    fontSize: 12,
    color: '#6b7280',
    textAlign: 'center',
  },
  configContainer: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  configSection: {
    paddingHorizontal: 16,
    paddingVertical: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  configSectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
    marginBottom: 12,
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    overflow: 'hidden',
  },
  picker: {
    height: 50,
  },
  dateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    marginBottom: 8,
  },
  dateButtonText: {
    marginLeft: 12,
    fontSize: 16,
    color: '#1f2937',
  },
  granularityOptions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -4,
  },
  granularityOption: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: '#f3f4f6',
    borderRadius: 20,
    margin: 4,
  },
  granularityOptionActive: {
    backgroundColor: '#6366f1',
  },
  granularityOptionText: {
    fontSize: 14,
    color: '#4b5563',
  },
  granularityOptionTextActive: {
    color: '#ffffff',
  },
  metricsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -4,
  },
  metricChip: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: '#f3f4f6',
    borderRadius: 20,
    margin: 4,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  metricChipActive: {
    backgroundColor: '#ede9fe',
    borderColor: '#6366f1',
  },
  metricChipText: {
    fontSize: 14,
    color: '#4b5563',
  },
  metricChipTextActive: {
    color: '#6366f1',
    fontWeight: '500',
  },
  generateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#6366f1',
    paddingVertical: 16,
    marginHorizontal: 16,
    marginVertical: 24,
    borderRadius: 8,
  },
  generateButtonDisabled: {
    opacity: 0.6,
  },
  generateButtonText: {
    marginLeft: 8,
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  emptyStateTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1f2937',
    marginTop: 16,
  },
  emptyStateText: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 8,
    textAlign: 'center',
  },
  emptyStateButton: {
    marginTop: 24,
    paddingVertical: 12,
    paddingHorizontal: 24,
    backgroundColor: '#6366f1',
    borderRadius: 8,
  },
  emptyStateButtonText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#ffffff',
  },
  insightsList: {
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  insightCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
  },
  insightCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  insightCardNumber: {
    marginLeft: 8,
    fontSize: 14,
    fontWeight: '600',
    color: '#4b5563',
  },
  insightCardText: {
    fontSize: 14,
    color: '#1f2937',
    lineHeight: 20,
  },
  insightShareButton: {
    position: 'absolute',
    top: 16,
    right: 16,
  },
  emptyInsights: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 48,
  },
  emptyInsightsText: {
    marginTop: 12,
    fontSize: 16,
    color: '#6b7280',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#ffffff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingBottom: 32,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1f2937',
  },
  exportOptions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 20,
  },
  exportOption: {
    width: '50%',
    alignItems: 'center',
    paddingVertical: 20,
  },
  exportOptionText: {
    marginTop: 8,
    fontSize: 14,
    fontWeight: '500',
    color: '#1f2937',
  },
  exportOptionSubtext: {
    fontSize: 12,
    color: '#6b7280',
  },
});

export default AdvancedAnalytics;