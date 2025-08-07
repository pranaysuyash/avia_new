/**
 * Admin Dashboard Component for React Native
 * Provides comprehensive admin functionality optimized for mobile devices
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
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import * as FileSystem from 'expo-file-system';
import * as DocumentPicker from 'expo-document-picker';
import * as Notifications from 'expo-notifications';
import * as Haptics from 'expo-haptics';
import { LineChart, BarChart, PieChart } from 'react-native-chart-kit';
import { MaterialIcons, Ionicons, FontAwesome5 } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

// Types
interface SystemMetrics {
  timestamp: string;
  cpu_percent: number;
  memory_percent: number;
  memory_used_mb: number;
  memory_total_mb: number;
  disk_percent: number;
  disk_used_gb: number;
  disk_total_gb: number;
  active_users: number;
  total_api_calls: number;
  error_count: number;
  avg_response_time_ms: number;
  cache_hit_rate: number;
  websocket_connections: number;
  transcription_minutes_today: number;
  system_health: string;
}

interface UserMetrics {
  user_id: number;
  username: string;
  email: string;
  status: string;
  created_at: string;
  last_login: string | null;
  total_transcriptions: number;
  total_minutes_transcribed: number;
  storage_used_mb: number;
  api_calls_today: number;
  subscription_tier: string;
  team_name: string | null;
  is_team_admin: boolean;
}

interface DashboardData {
  system_metrics: SystemMetrics;
  user_stats: any;
  usage_trends: any;
  active_sessions: any[];
  recent_errors: any[];
  subscription_summary: any;
  storage_summary: any;
  api_usage_summary: any;
}

// Constants
const REFRESH_INTERVAL = 30000; // 30 seconds
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
};

const AdminDashboard: React.FC = () => {
  const insets = useSafeAreaInsets();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [users, setUsers] = useState<UserMetrics[]>([]);
  const [selectedTab, setSelectedTab] = useState<'overview' | 'users' | 'analytics' | 'settings'>('overview');
  const [searchQuery, setSearchQuery] = useState('');
  const [isOffline, setIsOffline] = useState(false);
  const [showUserModal, setShowUserModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserMetrics | null>(null);
  const [systemSettings, setSystemSettings] = useState<any>({});
  const refreshInterval = useRef<NodeJS.Timer>();
  const scrollY = useRef(new Animated.Value(0)).current;
  const [expandedSections, setExpandedSections] = useState<string[]>(['metrics']);

  // Setup notifications
  useEffect(() => {
    const setupNotifications = async () => {
      const { status } = await Notifications.requestPermissionsAsync();
      if (status === 'granted') {
        Notifications.setNotificationHandler({
          handleNotification: async () => ({
            shouldShowAlert: true,
            shouldPlaySound: true,
            shouldSetBadge: true,
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
    });
    return () => unsubscribe();
  }, []);

  // Fetch dashboard data
  const fetchDashboardData = useCallback(async () => {
    try {
      const token = await AsyncStorage.getItem('adminToken');
      const response = await fetch(`${process.env.API_URL}/api/v1/admin/dashboard`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) throw new Error('Failed to fetch dashboard data');

      const data = await response.json();
      setDashboardData(data);

      // Check for critical alerts
      if (data.system_metrics.system_health === 'critical') {
        await Notifications.scheduleNotificationAsync({
          content: {
            title: 'System Alert',
            body: 'System health is critical. Please check the dashboard.',
            data: { type: 'system_alert' },
          },
          trigger: null,
        });
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      }
    } catch (error) {
      console.error('Dashboard fetch error:', error);
      Alert.alert('Error', 'Failed to load dashboard data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  // Fetch users
  const fetchUsers = useCallback(async (search?: string) => {
    try {
      const token = await AsyncStorage.getItem('adminToken');
      const params = new URLSearchParams({
        page: '1',
        per_page: '50',
        ...(search && { search }),
      });

      const response = await fetch(`${process.env.API_URL}/api/v1/admin/users?${params}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) throw new Error('Failed to fetch users');

      const data = await response.json();
      setUsers(data.users);
    } catch (error) {
      console.error('Users fetch error:', error);
    }
  }, []);

  // Load system settings
  const loadSystemSettings = useCallback(async () => {
    try {
      const token = await AsyncStorage.getItem('adminToken');
      const response = await fetch(`${process.env.API_URL}/api/v1/admin/settings`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) throw new Error('Failed to fetch settings');

      const settings = await response.json();
      setSystemSettings(settings);
    } catch (error) {
      console.error('Settings fetch error:', error);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchDashboardData();
    fetchUsers();
    loadSystemSettings();

    // Set up refresh interval
    refreshInterval.current = setInterval(() => {
      if (!isOffline) {
        fetchDashboardData();
      }
    }, REFRESH_INTERVAL);

    return () => {
      if (refreshInterval.current) {
        clearInterval(refreshInterval.current);
      }
    };
  }, [fetchDashboardData, fetchUsers, loadSystemSettings, isOffline]);

  // Handle refresh
  const handleRefresh = useCallback(() => {
    setRefreshing(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    fetchDashboardData();
    if (selectedTab === 'users') {
      fetchUsers(searchQuery);
    }
  }, [fetchDashboardData, fetchUsers, selectedTab, searchQuery]);

  // Handle user status update
  const handleUserStatusUpdate = async (userId: number, newStatus: string, reason?: string) => {
    try {
      const token = await AsyncStorage.getItem('adminToken');
      const response = await fetch(`${process.env.API_URL}/api/v1/admin/users/${userId}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ status: newStatus, reason }),
      });

      if (!response.ok) throw new Error('Failed to update user status');

      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      Alert.alert('Success', 'User status updated');
      fetchUsers();
      setShowUserModal(false);
    } catch (error) {
      console.error('Status update error:', error);
      Alert.alert('Error', 'Failed to update user status');
    }
  };

  // Handle settings update
  const handleSettingsUpdate = async (key: string, value: any) => {
    try {
      const token = await AsyncStorage.getItem('adminToken');
      const response = await fetch(`${process.env.API_URL}/api/v1/admin/settings`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ [key]: value }),
      });

      if (!response.ok) throw new Error('Failed to update settings');

      setSystemSettings((prev: any) => ({ ...prev, [key]: value }));
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    } catch (error) {
      console.error('Settings update error:', error);
      Alert.alert('Error', 'Failed to update settings');
    }
  };

  // Export analytics
  const handleExport = async (type: string) => {
    try {
      const token = await AsyncStorage.getItem('adminToken');
      const response = await fetch(
        `${process.env.API_URL}/api/v1/admin/analytics/export?export_type=${type}&format=json`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) throw new Error('Failed to export data');

      const data = await response.json();
      const jsonString = JSON.stringify(data, null, 2);

      // Save to device
      const fileUri = `${FileSystem.documentDirectory}${type}_export_${Date.now()}.json`;
      await FileSystem.writeAsStringAsync(fileUri, jsonString);

      // Share file
      await Share.share({
        url: fileUri,
        title: `${type} Export`,
      });

      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (error) {
      console.error('Export error:', error);
      Alert.alert('Error', 'Failed to export data');
    }
  };

  // Toggle section expansion
  const toggleSection = (section: string) => {
    setExpandedSections((prev) =>
      prev.includes(section) ? prev.filter((s) => s !== section) : [...prev, section]
    );
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  };

  // Render system metrics card
  const renderMetricsCard = () => {
    if (!dashboardData) return null;

    const { system_metrics } = dashboardData;
    const healthColor = {
      healthy: '#10b981',
      good: '#22c55e',
      warning: '#f59e0b',
      critical: '#ef4444',
    }[system_metrics.system_health] || '#6b7280';

    return (
      <View style={styles.card}>
        <TouchableOpacity
          style={styles.sectionHeader}
          onPress={() => toggleSection('metrics')}
        >
          <View style={styles.sectionHeaderLeft}>
            <MaterialIcons name="dashboard" size={24} color="#6366f1" />
            <Text style={styles.sectionTitle}>System Metrics</Text>
          </View>
          <MaterialIcons
            name={expandedSections.includes('metrics') ? 'expand-less' : 'expand-more'}
            size={24}
            color="#6b7280"
          />
        </TouchableOpacity>

        {expandedSections.includes('metrics') && (
          <View>
            <View style={[styles.healthIndicator, { backgroundColor: healthColor }]}>
              <Text style={styles.healthText}>
                System Health: {system_metrics.system_health.toUpperCase()}
              </Text>
            </View>

            <View style={styles.metricsGrid}>
              <View style={styles.metricItem}>
                <MaterialIcons name="memory" size={20} color="#6366f1" />
                <Text style={styles.metricValue}>{system_metrics.cpu_percent.toFixed(1)}%</Text>
                <Text style={styles.metricLabel}>CPU</Text>
              </View>

              <View style={styles.metricItem}>
                <MaterialIcons name="storage" size={20} color="#6366f1" />
                <Text style={styles.metricValue}>{system_metrics.memory_percent.toFixed(1)}%</Text>
                <Text style={styles.metricLabel}>Memory</Text>
              </View>

              <View style={styles.metricItem}>
                <MaterialIcons name="folder" size={20} color="#6366f1" />
                <Text style={styles.metricValue}>{system_metrics.disk_percent.toFixed(1)}%</Text>
                <Text style={styles.metricLabel}>Disk</Text>
              </View>

              <View style={styles.metricItem}>
                <MaterialIcons name="people" size={20} color="#6366f1" />
                <Text style={styles.metricValue}>{system_metrics.active_users}</Text>
                <Text style={styles.metricLabel}>Active Users</Text>
              </View>
            </View>

            <View style={styles.additionalMetrics}>
              <View style={styles.metricRow}>
                <Text style={styles.metricRowLabel}>API Calls Today</Text>
                <Text style={styles.metricRowValue}>{system_metrics.total_api_calls}</Text>
              </View>
              <View style={styles.metricRow}>
                <Text style={styles.metricRowLabel}>Avg Response Time</Text>
                <Text style={styles.metricRowValue}>{system_metrics.avg_response_time_ms.toFixed(0)}ms</Text>
              </View>
              <View style={styles.metricRow}>
                <Text style={styles.metricRowLabel}>Cache Hit Rate</Text>
                <Text style={styles.metricRowValue}>{(system_metrics.cache_hit_rate * 100).toFixed(1)}%</Text>
              </View>
              <View style={styles.metricRow}>
                <Text style={styles.metricRowLabel}>Transcription Minutes</Text>
                <Text style={styles.metricRowValue}>{system_metrics.transcription_minutes_today.toFixed(0)}</Text>
              </View>
            </View>
          </View>
        )}
      </View>
    );
  };

  // Render user stats
  const renderUserStats = () => {
    if (!dashboardData) return null;

    const { user_stats } = dashboardData;

    return (
      <View style={styles.card}>
        <TouchableOpacity
          style={styles.sectionHeader}
          onPress={() => toggleSection('userStats')}
        >
          <View style={styles.sectionHeaderLeft}>
            <MaterialIcons name="group" size={24} color="#6366f1" />
            <Text style={styles.sectionTitle}>User Statistics</Text>
          </View>
          <MaterialIcons
            name={expandedSections.includes('userStats') ? 'expand-less' : 'expand-more'}
            size={24}
            color="#6b7280"
          />
        </TouchableOpacity>

        {expandedSections.includes('userStats') && (
          <View>
            <View style={styles.statsGrid}>
              <View style={styles.statCard}>
                <Text style={styles.statValue}>{user_stats.total_users}</Text>
                <Text style={styles.statLabel}>Total Users</Text>
              </View>
              <View style={styles.statCard}>
                <Text style={styles.statValue}>{user_stats.active_users}</Text>
                <Text style={styles.statLabel}>Active Users</Text>
              </View>
              <View style={styles.statCard}>
                <Text style={styles.statValue}>{user_stats.new_users_this_month}</Text>
                <Text style={styles.statLabel}>New This Month</Text>
              </View>
              <View style={styles.statCard}>
                <Text style={styles.statValue}>{user_stats.growth_rate.toFixed(1)}%</Text>
                <Text style={styles.statLabel}>Growth Rate</Text>
              </View>
            </View>

            {/* User tier distribution pie chart */}
            {Object.keys(user_stats.users_by_tier).length > 0 && (
              <View style={styles.chartContainer}>
                <Text style={styles.chartTitle}>Users by Tier</Text>
                <PieChart
                  data={Object.entries(user_stats.users_by_tier).map(([tier, count], index) => ({
                    name: tier,
                    population: count as number,
                    color: ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b'][index % 4],
                    legendFontColor: '#7F7F7F',
                    legendFontSize: 12,
                  }))}
                  width={SCREEN_WIDTH - 64}
                  height={200}
                  chartConfig={CHART_CONFIG}
                  accessor="population"
                  backgroundColor="transparent"
                  paddingLeft="15"
                  absolute
                />
              </View>
            )}
          </View>
        )}
      </View>
    );
  };

  // Render usage trends
  const renderUsageTrends = () => {
    if (!dashboardData || !dashboardData.usage_trends) return null;

    const { daily_users, daily_transcriptions } = dashboardData.usage_trends;
    if (!daily_users.length) return null;

    // Prepare data for charts
    const labels = daily_users.slice(-7).map((item: any) => {
      const date = new Date(item.date);
      return `${date.getMonth() + 1}/${date.getDate()}`;
    });

    const userValues = daily_users.slice(-7).map((item: any) => item.value);
    const transcriptionValues = daily_transcriptions.slice(-7).map((item: any) => item.value);

    return (
      <View style={styles.card}>
        <TouchableOpacity
          style={styles.sectionHeader}
          onPress={() => toggleSection('trends')}
        >
          <View style={styles.sectionHeaderLeft}>
            <MaterialIcons name="trending-up" size={24} color="#6366f1" />
            <Text style={styles.sectionTitle}>Usage Trends (7 Days)</Text>
          </View>
          <MaterialIcons
            name={expandedSections.includes('trends') ? 'expand-less' : 'expand-more'}
            size={24}
            color="#6b7280"
          />
        </TouchableOpacity>

        {expandedSections.includes('trends') && (
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View style={styles.chartsRow}>
              <View style={styles.chartWrapper}>
                <Text style={styles.chartTitle}>Daily Active Users</Text>
                <LineChart
                  data={{
                    labels,
                    datasets: [{ data: userValues }],
                  }}
                  width={SCREEN_WIDTH - 80}
                  height={180}
                  chartConfig={CHART_CONFIG}
                  bezier
                  style={styles.chart}
                />
              </View>

              <View style={styles.chartWrapper}>
                <Text style={styles.chartTitle}>Daily Transcriptions</Text>
                <BarChart
                  data={{
                    labels,
                    datasets: [{ data: transcriptionValues }],
                  }}
                  width={SCREEN_WIDTH - 80}
                  height={180}
                  chartConfig={CHART_CONFIG}
                  style={styles.chart}
                  showValuesOnTopOfBars
                />
              </View>
            </View>
          </ScrollView>
        )}
      </View>
    );
  };

  // Render user item
  const renderUserItem = ({ item }: { item: UserMetrics }) => {
    const statusColor = {
      active: '#10b981',
      suspended: '#f59e0b',
      deleted: '#ef4444',
      pending: '#6b7280',
    }[item.status] || '#6b7280';

    return (
      <TouchableOpacity
        style={styles.userItem}
        onPress={() => {
          setSelectedUser(item);
          setShowUserModal(true);
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
        }}
      >
        <View style={styles.userItemLeft}>
          <View style={[styles.userStatusDot, { backgroundColor: statusColor }]} />
          <View>
            <Text style={styles.userName}>{item.username}</Text>
            <Text style={styles.userEmail}>{item.email}</Text>
            <View style={styles.userMetadata}>
              <Text style={styles.userMetaText}>{item.subscription_tier}</Text>
              {item.team_name && (
                <>
                  <Text style={styles.userMetaSeparator}>•</Text>
                  <Text style={styles.userMetaText}>{item.team_name}</Text>
                </>
              )}
            </View>
          </View>
        </View>
        <MaterialIcons name="chevron-right" size={24} color="#9ca3af" />
      </TouchableOpacity>
    );
  };

  // Render settings
  const renderSettings = () => {
    return (
      <ScrollView style={styles.settingsContainer}>
        <View style={styles.settingsSection}>
          <Text style={styles.settingsSectionTitle}>General Settings</Text>
          
          <View style={styles.settingItem}>
            <Text style={styles.settingLabel}>Maintenance Mode</Text>
            <Switch
              value={systemSettings.maintenance_mode}
              onValueChange={(value) => handleSettingsUpdate('maintenance_mode', value)}
              trackColor={{ false: '#d1d5db', true: '#6366f1' }}
              thumbColor="#ffffff"
            />
          </View>

          <View style={styles.settingItem}>
            <Text style={styles.settingLabel}>Allow Registrations</Text>
            <Switch
              value={systemSettings.allow_registrations}
              onValueChange={(value) => handleSettingsUpdate('allow_registrations', value)}
              trackColor={{ false: '#d1d5db', true: '#6366f1' }}
              thumbColor="#ffffff"
            />
          </View>

          <View style={styles.settingItem}>
            <Text style={styles.settingLabel}>Email Verification Required</Text>
            <Switch
              value={systemSettings.require_email_verification}
              onValueChange={(value) => handleSettingsUpdate('require_email_verification', value)}
              trackColor={{ false: '#d1d5db', true: '#6366f1' }}
              thumbColor="#ffffff"
            />
          </View>
        </View>

        <View style={styles.settingsSection}>
          <Text style={styles.settingsSectionTitle}>Export Data</Text>
          
          <TouchableOpacity
            style={styles.exportButton}
            onPress={() => handleExport('users')}
          >
            <MaterialIcons name="file-download" size={20} color="#6366f1" />
            <Text style={styles.exportButtonText}>Export Users</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.exportButton}
            onPress={() => handleExport('usage')}
          >
            <MaterialIcons name="file-download" size={20} color="#6366f1" />
            <Text style={styles.exportButtonText}>Export Usage Data</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.exportButton}
            onPress={() => handleExport('revenue')}
          >
            <MaterialIcons name="file-download" size={20} color="#6366f1" />
            <Text style={styles.exportButtonText}>Export Revenue</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.settingsSection}>
          <Text style={styles.settingsSectionTitle}>System Actions</Text>
          
          <TouchableOpacity
            style={[styles.actionButton, styles.warningButton]}
            onPress={() => {
              Alert.alert(
                'Clear Cache',
                'Are you sure you want to clear the system cache?',
                [
                  { text: 'Cancel', style: 'cancel' },
                  {
                    text: 'Clear',
                    style: 'destructive',
                    onPress: async () => {
                      // Implement cache clear
                      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
                    },
                  },
                ]
              );
            }}
          >
            <MaterialIcons name="cached" size={20} color="#f59e0b" />
            <Text style={[styles.actionButtonText, styles.warningText]}>Clear Cache</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    );
  };

  // Render user modal
  const renderUserModal = () => {
    if (!selectedUser) return null;

    return (
      <Modal
        visible={showUserModal}
        animationType="slide"
        transparent
        onRequestClose={() => setShowUserModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>User Details</Text>
              <TouchableOpacity onPress={() => setShowUserModal(false)}>
                <MaterialIcons name="close" size={24} color="#6b7280" />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalBody}>
              <View style={styles.userDetailSection}>
                <Text style={styles.userDetailLabel}>Username</Text>
                <Text style={styles.userDetailValue}>{selectedUser.username}</Text>
              </View>

              <View style={styles.userDetailSection}>
                <Text style={styles.userDetailLabel}>Email</Text>
                <Text style={styles.userDetailValue}>{selectedUser.email}</Text>
              </View>

              <View style={styles.userDetailSection}>
                <Text style={styles.userDetailLabel}>Status</Text>
                <Text style={styles.userDetailValue}>{selectedUser.status}</Text>
              </View>

              <View style={styles.userDetailSection}>
                <Text style={styles.userDetailLabel}>Subscription</Text>
                <Text style={styles.userDetailValue}>{selectedUser.subscription_tier}</Text>
              </View>

              <View style={styles.userDetailSection}>
                <Text style={styles.userDetailLabel}>Total Transcriptions</Text>
                <Text style={styles.userDetailValue}>{selectedUser.total_transcriptions}</Text>
              </View>

              <View style={styles.userDetailSection}>
                <Text style={styles.userDetailLabel}>Storage Used</Text>
                <Text style={styles.userDetailValue}>
                  {(selectedUser.storage_used_mb / 1024).toFixed(2)} GB
                </Text>
              </View>

              <View style={styles.modalActions}>
                {selectedUser.status === 'active' && (
                  <TouchableOpacity
                    style={[styles.modalActionButton, styles.suspendButton]}
                    onPress={() => {
                      Alert.alert(
                        'Suspend User',
                        'Are you sure you want to suspend this user?',
                        [
                          { text: 'Cancel', style: 'cancel' },
                          {
                            text: 'Suspend',
                            style: 'destructive',
                            onPress: () => handleUserStatusUpdate(selectedUser.user_id, 'suspended'),
                          },
                        ]
                      );
                    }}
                  >
                    <Text style={styles.modalActionButtonText}>Suspend User</Text>
                  </TouchableOpacity>
                )}

                {selectedUser.status === 'suspended' && (
                  <TouchableOpacity
                    style={[styles.modalActionButton, styles.activateButton]}
                    onPress={() => handleUserStatusUpdate(selectedUser.user_id, 'active')}
                  >
                    <Text style={styles.modalActionButtonText}>Activate User</Text>
                  </TouchableOpacity>
                )}
              </View>
            </ScrollView>
          </View>
        </View>
      </Modal>
    );
  };

  // Render content based on selected tab
  const renderContent = () => {
    switch (selectedTab) {
      case 'overview':
        return (
          <ScrollView
            style={styles.content}
            refreshControl={
              <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
            }
            showsVerticalScrollIndicator={false}
          >
            {renderMetricsCard()}
            {renderUserStats()}
            {renderUsageTrends()}
          </ScrollView>
        );

      case 'users':
        return (
          <View style={styles.content}>
            <View style={styles.searchContainer}>
              <MaterialIcons name="search" size={20} color="#6b7280" />
              <TextInput
                style={styles.searchInput}
                placeholder="Search users..."
                value={searchQuery}
                onChangeText={(text) => {
                  setSearchQuery(text);
                  fetchUsers(text);
                }}
                placeholderTextColor="#9ca3af"
              />
            </View>
            <FlatList
              data={users}
              keyExtractor={(item) => item.user_id.toString()}
              renderItem={renderUserItem}
              refreshControl={
                <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
              }
              contentContainerStyle={styles.usersList}
            />
          </View>
        );

      case 'analytics':
        return (
          <ScrollView
            style={styles.content}
            refreshControl={
              <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
            }
            showsVerticalScrollIndicator={false}
          >
            {renderUsageTrends()}
            {dashboardData && (
              <View style={styles.card}>
                <Text style={styles.sectionTitle}>Revenue Summary</Text>
                <View style={styles.revenueGrid}>
                  <View style={styles.revenueItem}>
                    <Text style={styles.revenueValue}>
                      ${dashboardData.subscription_summary.monthly_recurring_revenue.toFixed(2)}
                    </Text>
                    <Text style={styles.revenueLabel}>MRR</Text>
                  </View>
                  <View style={styles.revenueItem}>
                    <Text style={styles.revenueValue}>
                      ${dashboardData.subscription_summary.annual_recurring_revenue.toFixed(2)}
                    </Text>
                    <Text style={styles.revenueLabel}>ARR</Text>
                  </View>
                  <View style={styles.revenueItem}>
                    <Text style={styles.revenueValue}>
                      {dashboardData.subscription_summary.churn_rate.toFixed(1)}%
                    </Text>
                    <Text style={styles.revenueLabel}>Churn Rate</Text>
                  </View>
                </View>
              </View>
            )}
          </ScrollView>
        );

      case 'settings':
        return renderSettings();

      default:
        return null;
    }
  };

  if (loading && !dashboardData) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#6366f1" />
        <Text style={styles.loadingText}>Loading dashboard...</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#ffffff" />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Admin Dashboard</Text>
        {isOffline && (
          <View style={styles.offlineIndicator}>
            <MaterialIcons name="cloud-off" size={16} color="#ef4444" />
            <Text style={styles.offlineText}>Offline</Text>
          </View>
        )}
      </View>

      {/* Tab Bar */}
      <View style={styles.tabBar}>
        <TouchableOpacity
          style={[styles.tab, selectedTab === 'overview' && styles.activeTab]}
          onPress={() => {
            setSelectedTab('overview');
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          }}
        >
          <MaterialIcons
            name="dashboard"
            size={24}
            color={selectedTab === 'overview' ? '#6366f1' : '#6b7280'}
          />
          <Text style={[styles.tabText, selectedTab === 'overview' && styles.activeTabText]}>
            Overview
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tab, selectedTab === 'users' && styles.activeTab]}
          onPress={() => {
            setSelectedTab('users');
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          }}
        >
          <MaterialIcons
            name="people"
            size={24}
            color={selectedTab === 'users' ? '#6366f1' : '#6b7280'}
          />
          <Text style={[styles.tabText, selectedTab === 'users' && styles.activeTabText]}>
            Users
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tab, selectedTab === 'analytics' && styles.activeTab]}
          onPress={() => {
            setSelectedTab('analytics');
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          }}
        >
          <MaterialIcons
            name="analytics"
            size={24}
            color={selectedTab === 'analytics' ? '#6366f1' : '#6b7280'}
          />
          <Text style={[styles.tabText, selectedTab === 'analytics' && styles.activeTabText]}>
            Analytics
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tab, selectedTab === 'settings' && styles.activeTab]}
          onPress={() => {
            setSelectedTab('settings');
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          }}
        >
          <MaterialIcons
            name="settings"
            size={24}
            color={selectedTab === 'settings' ? '#6366f1' : '#6b7280'}
          />
          <Text style={[styles.tabText, selectedTab === 'settings' && styles.activeTabText]}>
            Settings
          </Text>
        </TouchableOpacity>
      </View>

      {/* Content */}
      {renderContent()}

      {/* User Modal */}
      {renderUserModal()}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f3f4f6',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f3f4f6',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#6b7280',
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
  offlineIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fee2e2',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  offlineText: {
    marginLeft: 4,
    fontSize: 12,
    color: '#ef4444',
    fontWeight: '500',
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
    paddingTop: 8,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 12,
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#6366f1',
  },
  tabText: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 4,
  },
  activeTabText: {
    color: '#6366f1',
    fontWeight: '500',
  },
  content: {
    flex: 1,
  },
  card: {
    backgroundColor: '#ffffff',
    margin: 16,
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1f2937',
    marginLeft: 8,
  },
  healthIndicator: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    marginBottom: 16,
  },
  healthText: {
    color: '#ffffff',
    fontWeight: '600',
    textAlign: 'center',
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -8,
  },
  metricItem: {
    width: '50%',
    paddingHorizontal: 8,
    marginBottom: 16,
    alignItems: 'center',
  },
  metricValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1f2937',
    marginTop: 8,
  },
  metricLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 4,
  },
  additionalMetrics: {
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
    paddingTop: 16,
  },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  metricRowLabel: {
    fontSize: 14,
    color: '#6b7280',
  },
  metricRowValue: {
    fontSize: 14,
    fontWeight: '500',
    color: '#1f2937',
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -8,
  },
  statCard: {
    width: '50%',
    paddingHorizontal: 8,
    marginBottom: 16,
  },
  statValue: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#6366f1',
  },
  statLabel: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 4,
  },
  chartContainer: {
    marginTop: 16,
  },
  chartTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
    marginBottom: 12,
  },
  chartsRow: {
    flexDirection: 'row',
    paddingRight: 16,
  },
  chartWrapper: {
    marginRight: 16,
  },
  chart: {
    borderRadius: 16,
    marginTop: 8,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    margin: 16,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  searchInput: {
    flex: 1,
    marginLeft: 8,
    fontSize: 16,
    color: '#1f2937',
  },
  usersList: {
    paddingBottom: 20,
  },
  userItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    marginHorizontal: 16,
    marginVertical: 4,
    padding: 16,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  userItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  userStatusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 12,
  },
  userName: {
    fontSize: 16,
    fontWeight: '500',
    color: '#1f2937',
  },
  userEmail: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 2,
  },
  userMetadata: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  userMetaText: {
    fontSize: 12,
    color: '#9ca3af',
  },
  userMetaSeparator: {
    marginHorizontal: 6,
    fontSize: 12,
    color: '#d1d5db',
  },
  settingsContainer: {
    flex: 1,
    backgroundColor: '#f3f4f6',
  },
  settingsSection: {
    backgroundColor: '#ffffff',
    marginTop: 16,
    paddingVertical: 8,
  },
  settingsSectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  settingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  settingLabel: {
    fontSize: 16,
    color: '#1f2937',
  },
  exportButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    marginHorizontal: 16,
    marginVertical: 4,
    backgroundColor: '#ede9fe',
    borderRadius: 8,
  },
  exportButtonText: {
    marginLeft: 8,
    fontSize: 16,
    color: '#6366f1',
    fontWeight: '500',
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    marginHorizontal: 16,
    marginVertical: 4,
    borderRadius: 8,
  },
  warningButton: {
    backgroundColor: '#fef3c7',
  },
  actionButtonText: {
    marginLeft: 8,
    fontSize: 16,
    fontWeight: '500',
  },
  warningText: {
    color: '#f59e0b',
  },
  revenueGrid: {
    flexDirection: 'row',
    marginTop: 16,
  },
  revenueItem: {
    flex: 1,
    alignItems: 'center',
  },
  revenueValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#10b981',
  },
  revenueLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 4,
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
    maxHeight: SCREEN_HEIGHT * 0.8,
    paddingBottom: 40,
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
  modalBody: {
    paddingHorizontal: 20,
    paddingTop: 20,
  },
  userDetailSection: {
    marginBottom: 20,
  },
  userDetailLabel: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 4,
  },
  userDetailValue: {
    fontSize: 16,
    color: '#1f2937',
    fontWeight: '500',
  },
  modalActions: {
    marginTop: 32,
    paddingBottom: 20,
  },
  modalActionButton: {
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 12,
  },
  suspendButton: {
    backgroundColor: '#fef3c7',
  },
  activateButton: {
    backgroundColor: '#d1fae5',
  },
  modalActionButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
  },
});

export default AdminDashboard;