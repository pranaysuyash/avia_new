import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  RefreshControl,
  ActivityIndicator,
  Alert
} from 'react-native';
import {
  LineChart,
  BarChart,
  PieChart,
  ProgressChart
} from 'react-native-chart-kit';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { SafeAreaView } from 'react-native-safe-area-context';

const { width: screenWidth } = Dimensions.get('window');

interface DashboardStats {
  totalTranscripts: number;
  totalDuration: number;
  recentActivity: number;
  processingQueue: number;
  storageUsed: number;
  storageLimit: number;
}

interface RecentTranscript {
  id: string;
  title: string;
  duration: number;
  createdAt: string;
  status: 'completed' | 'processing' | 'failed';
  type: 'audio' | 'video';
  confidence?: number;
}

interface QuickAction {
  id: string;
  label: string;
  icon: string;
  color: string;
  action: () => void;
}

const chartConfig = {
  backgroundColor: '#ffffff',
  backgroundGradientFrom: '#ffffff',
  backgroundGradientTo: '#ffffff',
  decimalPlaces: 0,
  color: (opacity = 1) => `rgba(0, 122, 255, ${opacity})`,
  labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
  style: {
    borderRadius: 16,
  },
  propsForDots: {
    r: '6',
    strokeWidth: '2',
    stroke: '#007AFF',
  },
};

export const MainDashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats>({
    totalTranscripts: 0,
    totalDuration: 0,
    recentActivity: 0,
    processingQueue: 0,
    storageUsed: 0,
    storageLimit: 1000
  });
  const [recentTranscripts, setRecentTranscripts] = useState<RecentTranscript[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const quickActions: QuickAction[] = [
    {
      id: 'upload-audio',
      label: 'Upload Audio',
      icon: 'audiotrack',
      color: '#007AFF',
      action: () => Alert.alert('Upload Audio', 'Audio upload functionality')
    },
    {
      id: 'upload-video',
      label: 'Upload Video',
      icon: 'videocam',
      color: '#FF3B30',
      action: () => Alert.alert('Upload Video', 'Video upload functionality')
    },
    {
      id: 'record-audio',
      label: 'Record',
      icon: 'mic',
      color: '#34C759',
      action: () => Alert.alert('Record Audio', 'Audio recording functionality')
    },
    {
      id: 'search',
      label: 'Search',
      icon: 'search',
      color: '#FF9500',
      action: () => Alert.alert('Search', 'Search functionality')
    }
  ];

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setStats({
        totalTranscripts: 156,
        totalDuration: 2847, // minutes
        recentActivity: 12,
        processingQueue: 3,
        storageUsed: 750,
        storageLimit: 1000
      });

      setRecentTranscripts([
        {
          id: '1',
          title: 'Team Meeting - Q4 Planning',
          duration: 45,
          createdAt: '2024-01-15T10:30:00Z',
          status: 'completed',
          type: 'video',
          confidence: 0.94
        },
        {
          id: '2',
          title: 'Client Interview - Product Feedback',
          duration: 32,
          createdAt: '2024-01-15T09:15:00Z',
          status: 'processing',
          type: 'audio'
        },
        {
          id: '3',
          title: 'Podcast Episode 15',
          duration: 67,
          createdAt: '2024-01-14T16:45:00Z',
          status: 'completed',
          type: 'audio',
          confidence: 0.91
        },
        {
          id: '4',
          title: 'Training Session - New Features',
          duration: 89,
          createdAt: '2024-01-14T14:20:00Z',
          status: 'failed',
          type: 'video'
        }
      ]);
    } catch (error) {
      Alert.alert('Error', 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadDashboardData();
    setRefreshing(false);
  };

  const formatDuration = (minutes: number): string => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  const formatFileSize = (mb: number): string => {
    if (mb >= 1000) {
      return `${(mb / 1000).toFixed(1)} GB`;
    }
    return `${mb} MB`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#34C759';
      case 'processing': return '#FF9500';
      case 'failed': return '#FF3B30';
      default: return '#8E8E93';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return 'check-circle';
      case 'processing': return 'hourglass-empty';
      case 'failed': return 'error';
      default: return 'help';
    }
  };

  const renderHeader = () => (
    <View style={styles.header}>
      <View>
        <Text style={styles.headerTitle}>Dashboard</Text>
        <Text style={styles.headerSubtitle}>Welcome back!</Text>
      </View>
      <TouchableOpacity style={styles.notificationButton}>
        <Icon name="notifications" size={24} color="#007AFF" />
        <View style={styles.notificationBadge}>
          <Text style={styles.notificationBadgeText}>3</Text>
        </View>
      </TouchableOpacity>
    </View>
  );

  const renderStatsCards = () => (
    <View style={styles.statsContainer}>
      <View style={styles.statsRow}>
        <View style={[styles.statCard, { backgroundColor: '#007AFF15' }]}>
          <Icon name="description" size={24} color="#007AFF" />
          <Text style={styles.statValue}>{stats.totalTranscripts}</Text>
          <Text style={styles.statLabel}>Transcripts</Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: '#34C75915' }]}>
          <Icon name="schedule" size={24} color="#34C759" />
          <Text style={styles.statValue}>{formatDuration(stats.totalDuration)}</Text>
          <Text style={styles.statLabel}>Duration</Text>
        </View>
      </View>
      <View style={styles.statsRow}>
        <View style={[styles.statCard, { backgroundColor: '#FF950015' }]}>
          <Icon name="queue" size={24} color="#FF9500" />
          <Text style={styles.statValue}>{stats.processingQueue}</Text>
          <Text style={styles.statLabel}>Processing</Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: '#FF3B3015' }]}>
          <Icon name="storage" size={24} color="#FF3B30" />
          <Text style={styles.statValue}>{formatFileSize(stats.storageUsed)}</Text>
          <Text style={styles.statLabel}>Storage</Text>
        </View>
      </View>
    </View>
  );

  const renderQuickActions = () => (
    <View style={styles.quickActionsContainer}>
      <Text style={styles.sectionTitle}>Quick Actions</Text>
      <View style={styles.quickActionsGrid}>
        {quickActions.map((action) => (
          <TouchableOpacity
            key={action.id}
            style={[styles.quickActionButton, { borderColor: action.color }]}
            onPress={action.action}
          >
            <Icon name={action.icon} size={32} color={action.color} />
            <Text style={[styles.quickActionLabel, { color: action.color }]}>
              {action.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );

  const renderActivityChart = () => {
    const data = {
      labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
      datasets: [{
        data: [12, 19, 8, 15, 22, 7, 14]
      }]
    };

    return (
      <View style={styles.chartContainer}>
        <Text style={styles.sectionTitle}>Weekly Activity</Text>
        <LineChart
          data={data}
          width={screenWidth - 40}
          height={200}
          chartConfig={chartConfig}
          bezier
          style={styles.chart}
        />
      </View>
    );
  };

  const renderRecentTranscripts = () => (
    <View style={styles.recentContainer}>
      <Text style={styles.sectionTitle}>Recent Transcripts</Text>
      {recentTranscripts.map((transcript) => (
        <TouchableOpacity key={transcript.id} style={styles.transcriptItem}>
          <View style={styles.transcriptIcon}>
            <Icon
              name={transcript.type === 'video' ? 'videocam' : 'audiotrack'}
              size={20}
              color="#007AFF"
            />
          </View>
          <View style={styles.transcriptContent}>
            <Text style={styles.transcriptTitle} numberOfLines={1}>
              {transcript.title}
            </Text>
            <Text style={styles.transcriptMeta}>
              {formatDuration(transcript.duration)} • {new Date(transcript.createdAt).toLocaleDateString()}
            </Text>
            {transcript.confidence && (
              <Text style={styles.transcriptConfidence}>
                Confidence: {(transcript.confidence * 100).toFixed(0)}%
              </Text>
            )}
          </View>
          <View style={styles.transcriptStatus}>
            <Icon
              name={getStatusIcon(transcript.status)}
              size={20}
              color={getStatusColor(transcript.status)}
            />
          </View>
        </TouchableOpacity>
      ))}
      <TouchableOpacity style={styles.viewAllButton}>
        <Text style={styles.viewAllText}>View All Transcripts</Text>
        <Icon name="arrow-forward" size={16} color="#007AFF" />
      </TouchableOpacity>
    </View>
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading dashboard...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {renderHeader()}
        {renderStatsCards()}
        {renderQuickActions()}
        {renderActivityChart()}
        {renderRecentTranscripts()}
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollView: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 20,
    backgroundColor: '#fff',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#666',
    marginTop: 4,
  },
  notificationButton: {
    position: 'relative',
    padding: 8,
  },
  notificationBadge: {
    position: 'absolute',
    top: 4,
    right: 4,
    backgroundColor: '#FF3B30',
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  notificationBadgeText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  statsContainer: {
    paddingHorizontal: 20,
    paddingVertical: 10,
  },
  statsRow: {
    flexDirection: 'row',
    marginBottom: 15,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginHorizontal: 5,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 8,
  },
  statLabel: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  quickActionsContainer: {
    paddingHorizontal: 20,
    paddingVertical: 10,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  quickActionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  quickActionButton: {
    width: '48%',
    backgroundColor: '#fff',
    borderRadius: 12,
    borderWidth: 2,
    padding: 20,
    alignItems: 'center',
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  quickActionLabel: {
    fontSize: 14,
    fontWeight: '600',
    marginTop: 8,
  },
  chartContainer: {
    paddingHorizontal: 20,
    paddingVertical: 10,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  recentContainer: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    paddingBottom: 30,
  },
  transcriptItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 15,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  transcriptIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#007AFF15',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 15,
  },
  transcriptContent: {
    flex: 1,
  },
  transcriptTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  transcriptMeta: {
    fontSize: 14,
    color: '#666',
    marginBottom: 2,
  },
  transcriptConfidence: {
    fontSize: 12,
    color: '#999',
  },
  transcriptStatus: {
    marginLeft: 10,
  },
  viewAllButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 15,
    marginTop: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  viewAllText: {
    fontSize: 16,
    color: '#007AFF',
    fontWeight: '600',
    marginRight: 8,
  },
});

export default MainDashboard;