import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  StyleSheet,
  Dimensions,
} from 'react-native';
import { LineChart, PieChart, BarChart } from 'react-native-chart-kit';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { useTheme } from '../../../theme';

const { width: screenWidth } = Dimensions.get('window');

interface CacheStats {
  connected: boolean;
  uptime_seconds: number;
  memory: {
    used_bytes: number;
    used_human: string;
    peak_bytes: number;
    peak_human: string;
    rss_bytes: number;
    fragmentation_ratio: number;
  };
  stats: {
    total_requests: number;
    hits: number;
    misses: number;
    hit_rate: number;
    evicted_keys: number;
    expired_keys: number;
    ops_per_sec: number;
  };
  clients: {
    connected: number;
    blocked: number;
    max_clients: number;
  };
  keyspace: {
    total_keys: number;
    databases: Record<string, {
      count: number;
      sample_keys: string[];
    }>;
  };
}

interface CacheMetricsProps {
  apiBaseUrl?: string;
}

export const CacheMetrics: React.FC<CacheMetricsProps> = ({ 
  apiBaseUrl = 'http://localhost:8000' 
}) => {
  const theme = useTheme();
  const [stats, setStats] = useState<CacheStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchCacheStats = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      const response = await fetch(`${apiBaseUrl}/api/v1/transcription/cached/cache-stats`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch cache stats: ${response.status}`);
      }

      const data = await response.json();
      setStats(data);
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      setStats(null);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [apiBaseUrl]);

  useEffect(() => {
    fetchCacheStats();
  }, [fetchCacheStats]);

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    
    if (autoRefresh) {
      interval = setInterval(() => {
        fetchCacheStats(true);
      }, 5000);
    }

    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [autoRefresh, fetchCacheStats]);

  const formatUptime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const formatBytes = (bytes: number): string => {
    const sizes = ['B', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const handleWarmCache = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/transcription/cached/warm-cache`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ transcript_ids: [] }),
      });

      if (!response.ok) throw new Error('Failed to warm cache');

      Alert.alert('Success', 'Cache warming initiated');
      setTimeout(() => fetchCacheStats(true), 1000);
    } catch (err) {
      Alert.alert('Error', 'Failed to warm cache');
    }
  };

  const handleInvalidateCache = () => {
    Alert.alert(
      'Confirm',
      'Are you sure you want to invalidate the cache?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Invalidate', 
          style: 'destructive',
          onPress: async () => {
            try {
              const response = await fetch(`${apiBaseUrl}/api/v1/transcription/cached/invalidate-cache`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
              });

              if (!response.ok) throw new Error('Failed to invalidate cache');

              Alert.alert('Success', 'Cache invalidated');
              setTimeout(() => fetchCacheStats(true), 1000);
            } catch (err) {
              Alert.alert('Error', 'Failed to invalidate cache');
            }
          }
        },
      ]
    );
  };

  const onRefresh = useCallback(() => {
    fetchCacheStats(true);
  }, [fetchCacheStats]);

  if (loading) {
    return (
      <View style={[styles.container, styles.centered, { backgroundColor: theme.colors.background }]}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
        <Text style={[styles.loadingText, { color: theme.colors.text }]}>
          Loading cache metrics...
        </Text>
      </View>
    );
  }

  if (error || !stats) {
    return (
      <View style={[styles.container, styles.centered, { backgroundColor: theme.colors.background }]}>
        <Icon name="error-outline" size={48} color={theme.colors.error} />
        <Text style={[styles.errorText, { color: theme.colors.error }]}>
          {error || 'Failed to load cache stats'}
        </Text>
        <TouchableOpacity
          style={[styles.retryButton, { backgroundColor: theme.colors.primary }]}
          onPress={() => fetchCacheStats()}
        >
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Prepare chart data
  const memoryChartData = {
    labels: ['Used', 'Peak', 'RSS'],
    datasets: [
      {
        data: [
          Math.round(stats.memory.used_bytes / (1024 * 1024)),
          Math.round(stats.memory.peak_bytes / (1024 * 1024)),
          Math.round(stats.memory.rss_bytes / (1024 * 1024)),
        ],
      },
    ],
  };

  const keyDistributionData = Object.entries(stats.keyspace.databases)
    .filter(([, data]) => data.count > 0)
    .map(([name, data], index) => ({
      name: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      population: data.count,
      color: [
        '#3B82F6', '#10B981', '#F59E0B', '#EF4444', 
        '#8B5CF6', '#06B6D4', '#84CC16'
      ][index % 7],
      legendFontColor: theme.colors.text,
      legendFontSize: 12,
    }));

  const chartConfig = {
    backgroundColor: theme.colors.background,
    backgroundGradientFrom: theme.colors.background,
    backgroundGradientTo: theme.colors.background,
    decimalPlaces: 0,
    color: (opacity = 1) => `rgba(59, 130, 246, ${opacity})`,
    labelColor: (opacity = 1) => theme.colors.text,
    style: {
      borderRadius: 16,
    },
    propsForDots: {
      r: '6',
      strokeWidth: '2',
      stroke: theme.colors.primary,
    },
  };

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Header */}
      <View style={[styles.header, { backgroundColor: theme.colors.card }]}>
        <View style={styles.headerTop}>
          <View style={styles.headerLeft}>
            <Icon name="storage" size={24} color={theme.colors.primary} />
            <Text style={[styles.headerTitle, { color: theme.colors.text }]}>
              Cache Metrics
            </Text>
          </View>
          <TouchableOpacity
            style={[
              styles.autoRefreshButton, 
              { 
                backgroundColor: autoRefresh ? theme.colors.primary + '20' : theme.colors.surface,
                borderColor: autoRefresh ? theme.colors.primary : theme.colors.border,
              }
            ]}
            onPress={() => setAutoRefresh(!autoRefresh)}
          >
            <Icon 
              name="autorenew" 
              size={16} 
              color={autoRefresh ? theme.colors.primary : theme.colors.text} 
            />
            <Text 
              style={[
                styles.autoRefreshText, 
                { color: autoRefresh ? theme.colors.primary : theme.colors.text }
              ]}
            >
              Auto
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.statusRow}>
          <Icon name="check-circle" size={16} color={theme.colors.success} />
          <Text style={[styles.statusText, { color: theme.colors.success }]}>
            Connected
          </Text>
          <Text style={[styles.uptimeText, { color: theme.colors.textSecondary }]}>
            Uptime: {formatUptime(stats.uptime_seconds)}
          </Text>
        </View>
      </View>

      {/* Key Metrics */}
      <View style={styles.metricsGrid}>
        <View style={[styles.metricCard, { backgroundColor: theme.colors.card }]}>
          <Icon name="storage" size={24} color={theme.colors.primary} />
          <Text style={[styles.metricValue, { color: theme.colors.text }]}>
            {stats.keyspace.total_keys.toLocaleString()}
          </Text>
          <Text style={[styles.metricLabel, { color: theme.colors.textSecondary }]}>
            Total Keys
          </Text>
          <Text style={[styles.metricSubtext, { color: theme.colors.textSecondary }]}>
            {stats.stats.evicted_keys} evicted
          </Text>
        </View>

        <View style={[styles.metricCard, { backgroundColor: theme.colors.card }]}>
          <Icon name="trending-up" size={24} color={theme.colors.success} />
          <Text style={[styles.metricValue, { color: theme.colors.text }]}>
            {stats.stats.hit_rate.toFixed(1)}%
          </Text>
          <Text style={[styles.metricLabel, { color: theme.colors.textSecondary }]}>
            Hit Rate
          </Text>
          <View style={styles.progressBar}>
            <View 
              style={[
                styles.progressFill, 
                { 
                  width: `${Math.min(stats.stats.hit_rate, 100)}%`,
                  backgroundColor: theme.colors.success,
                }
              ]} 
            />
          </View>
        </View>

        <View style={[styles.metricCard, { backgroundColor: theme.colors.card }]}>
          <Icon name="memory" size={24} color={theme.colors.warning} />
          <Text style={[styles.metricValue, { color: theme.colors.text }]}>
            {stats.memory.used_human}
          </Text>
          <Text style={[styles.metricLabel, { color: theme.colors.textSecondary }]}>
            Memory Used
          </Text>
          <Text style={[styles.metricSubtext, { color: theme.colors.textSecondary }]}>
            Peak: {stats.memory.peak_human}
          </Text>
        </View>

        <View style={[styles.metricCard, { backgroundColor: theme.colors.card }]}>
          <Icon name="flash-on" size={24} color={theme.colors.info} />
          <Text style={[styles.metricValue, { color: theme.colors.text }]}>
            {stats.stats.ops_per_sec}
          </Text>
          <Text style={[styles.metricLabel, { color: theme.colors.textSecondary }]}>
            Ops/sec
          </Text>
          <Text style={[styles.metricSubtext, { color: theme.colors.textSecondary }]}>
            {stats.clients.connected} clients
          </Text>
        </View>
      </View>

      {/* Memory Chart */}
      <View style={[styles.chartCard, { backgroundColor: theme.colors.card }]}>
        <Text style={[styles.chartTitle, { color: theme.colors.text }]}>
          Memory Usage (MB)
        </Text>
        <BarChart
          data={memoryChartData}
          width={screenWidth - 40}
          height={200}
          chartConfig={chartConfig}
          style={styles.chart}
          showBarTops={true}
          fromZero={true}
        />
      </View>

      {/* Key Distribution Chart */}
      {keyDistributionData.length > 0 && (
        <View style={[styles.chartCard, { backgroundColor: theme.colors.card }]}>
          <Text style={[styles.chartTitle, { color: theme.colors.text }]}>
            Key Distribution
          </Text>
          <PieChart
            data={keyDistributionData}
            width={screenWidth - 40}
            height={200}
            chartConfig={chartConfig}
            accessor="population"
            backgroundColor="transparent"
            paddingLeft="15"
            absolute
          />
        </View>
      )}

      {/* Action Buttons */}
      <View style={styles.actionSection}>
        <TouchableOpacity
          style={[styles.actionButton, { backgroundColor: theme.colors.success }]}
          onPress={handleWarmCache}
        >
          <Icon name="whatshot" size={20} color="white" />
          <Text style={styles.actionButtonText}>Warm Cache</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, { backgroundColor: theme.colors.error }]}
          onPress={handleInvalidateCache}
        >
          <Icon name="clear-all" size={20} color="white" />
          <Text style={styles.actionButtonText}>Clear Cache</Text>
        </TouchableOpacity>
      </View>

      {/* Detailed Stats */}
      <View style={[styles.statsSection, { backgroundColor: theme.colors.card }]}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
          Detailed Statistics
        </Text>
        
        <View style={styles.statsGrid}>
          <View style={styles.statItem}>
            <Text style={[styles.statLabel, { color: theme.colors.textSecondary }]}>
              Total Requests
            </Text>
            <Text style={[styles.statValue, { color: theme.colors.text }]}>
              {stats.stats.total_requests.toLocaleString()}
            </Text>
          </View>

          <View style={styles.statItem}>
            <Text style={[styles.statLabel, { color: theme.colors.textSecondary }]}>
              Cache Hits
            </Text>
            <Text style={[styles.statValue, { color: theme.colors.success }]}>
              {stats.stats.hits.toLocaleString()}
            </Text>
          </View>

          <View style={styles.statItem}>
            <Text style={[styles.statLabel, { color: theme.colors.textSecondary }]}>
              Cache Misses
            </Text>
            <Text style={[styles.statValue, { color: theme.colors.error }]}>
              {stats.stats.misses.toLocaleString()}
            </Text>
          </View>

          <View style={styles.statItem}>
            <Text style={[styles.statLabel, { color: theme.colors.textSecondary }]}>
              Evicted Keys
            </Text>
            <Text style={[styles.statValue, { color: theme.colors.text }]}>
              {stats.stats.evicted_keys.toLocaleString()}
            </Text>
          </View>

          <View style={styles.statItem}>
            <Text style={[styles.statLabel, { color: theme.colors.textSecondary }]}>
              Expired Keys
            </Text>
            <Text style={[styles.statValue, { color: theme.colors.text }]}>
              {stats.stats.expired_keys.toLocaleString()}
            </Text>
          </View>

          <View style={styles.statItem}>
            <Text style={[styles.statLabel, { color: theme.colors.textSecondary }]}>
              Memory Fragmentation
            </Text>
            <Text style={[styles.statValue, { color: theme.colors.text }]}>
              {stats.memory.fragmentation_ratio.toFixed(2)}
            </Text>
          </View>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  centered: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
  },
  errorText: {
    marginTop: 16,
    fontSize: 16,
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 16,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    color: 'white',
    fontWeight: '600',
  },
  header: {
    padding: 16,
    marginBottom: 16,
    borderRadius: 8,
    margin: 16,
    marginBottom: 8,
  },
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginLeft: 8,
  },
  autoRefreshButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
  },
  autoRefreshText: {
    fontSize: 12,
    fontWeight: '500',
    marginLeft: 4,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusText: {
    fontSize: 14,
    fontWeight: '500',
    marginLeft: 4,
    marginRight: 12,
  },
  uptimeText: {
    fontSize: 12,
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 8,
    marginBottom: 16,
  },
  metricCard: {
    width: '47%',
    padding: 16,
    borderRadius: 8,
    margin: 8,
    alignItems: 'center',
  },
  metricValue: {
    fontSize: 24,
    fontWeight: '700',
    marginTop: 8,
  },
  metricLabel: {
    fontSize: 12,
    marginTop: 4,
  },
  metricSubtext: {
    fontSize: 10,
    marginTop: 2,
  },
  progressBar: {
    width: '100%',
    height: 4,
    backgroundColor: '#E5E7EB',
    borderRadius: 2,
    marginTop: 8,
  },
  progressFill: {
    height: '100%',
    borderRadius: 2,
  },
  chartCard: {
    margin: 16,
    marginVertical: 8,
    padding: 16,
    borderRadius: 8,
  },
  chartTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 16,
    textAlign: 'center',
  },
  chart: {
    borderRadius: 8,
  },
  actionSection: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: 16,
    marginVertical: 16,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    flex: 0.45,
    justifyContent: 'center',
  },
  actionButtonText: {
    color: 'white',
    fontWeight: '600',
    marginLeft: 8,
  },
  statsSection: {
    margin: 16,
    marginTop: 8,
    padding: 16,
    borderRadius: 8,
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 16,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  statItem: {
    width: '50%',
    marginBottom: 16,
  },
  statLabel: {
    fontSize: 12,
    marginBottom: 4,
  },
  statValue: {
    fontSize: 16,
    fontWeight: '600',
  },
});

export default CacheMetrics;