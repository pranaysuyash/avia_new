/**
 * Workflow Management Screen for React Native Mobile App
 * Mobile-optimized interface for enterprise workflow monitoring
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  Alert,
  Share,
  Dimensions,
  Platform,
  StatusBar,
  SafeAreaView,
  FlatList
} from 'react-native';
import {
  Card,
  Button,
  Badge,
  Input,
  Progress,
  Switch,
  Modal,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  ActionSheet,
  SearchBar,
  FloatingActionButton,
  PullToRefresh,
  SwipeableRow,
  LoadingSpinner,
  ErrorBoundary
} from '@/components/mobile';
import {
  MaterialCommunityIcons,
  Ionicons,
  FontAwesome5
} from '@expo/vector-icons';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  withRepeat,
  Easing,
  FadeIn,
  FadeOut,
  SlideInRight,
  SlideOutLeft
} from 'react-native-reanimated';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { BlurView } from 'expo-blur';
import { LinearGradient } from 'expo-linear-gradient';
import { Haptics } from 'expo-haptics';
import * as Notifications from 'expo-notifications';
import NetInfo from '@react-native-community/netinfo';
import AsyncStorage from '@react-native-async-storage/async-storage';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

interface WorkflowExecution {
  id: string;
  workflowId: string;
  name: string;
  status: 'running' | 'completed' | 'failed' | 'paused' | 'cancelled';
  startedAt: string;
  completedAt?: string;
  duration?: number;
  progress: number;
  nodeStates: Record<string, string>;
  results: Record<string, any>;
  errors: Array<{ nodeId: string; error: string; timestamp: string }>;
  metrics: {
    totalDuration: number;
    completedNodes: number;
    failedNodes: number;
    successRate: number;
  };
}

interface WorkflowDefinition {
  id: string;
  name: string;
  description: string;
  category: string;
  version: string;
  status: 'active' | 'draft' | 'deprecated';
  nodeCount: number;
  triggerCount: number;
  lastExecuted?: string;
  executionCount: number;
  successRate: number;
  averageDuration: number;
  tags: string[];
  priority: 'low' | 'medium' | 'high' | 'critical';
}

interface SystemMetrics {
  cpuUsage: number;
  memoryUsage: number;
  queueLength: number;
  activeConnections: number;
  networkStatus: 'online' | 'offline' | 'poor';
}

export const WorkflowManagementScreen: React.FC = () => {
  const insets = useSafeAreaInsets();
  const [workflows, setWorkflows] = useState<WorkflowDefinition[]>([]);
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics>({
    cpuUsage: 0,
    memoryUsage: 0,
    queueLength: 0,
    activeConnections: 0,
    networkStatus: 'online'
  });
  
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTab, setSelectedTab] = useState('overview');
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'name' | 'status' | 'lastExecuted'>('lastExecuted');
  
  // Animation values
  const pulseAnimation = useSharedValue(1);
  const slideAnimation = useSharedValue(0);
  
  useEffect(() => {
    // Pulse animation for active executions
    pulseAnimation.value = withRepeat(
      withTiming(1.1, { duration: 1000, easing: Easing.inOut(Easing.ease) }),
      -1,
      true
    );
  }, []);

  // Network status monitoring
  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener(state => {
      setSystemMetrics(prev => ({
        ...prev,
        networkStatus: state.isConnected ? 
          (state.details?.strength && state.details.strength > 50 ? 'online' : 'poor') : 
          'offline'
      }));
    });

    return unsubscribe;
  }, []);

  // Load data from API
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      
      // Simulate API calls with real-world delays
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const sampleWorkflows: WorkflowDefinition[] = [
        {
          id: 'wf_001',
          name: 'Medical Consultation Analysis',
          description: 'Advanced medical transcript processing with clinical insights and HIPAA compliance',
          category: 'medical',
          version: '2.3.1',
          status: 'active',
          nodeCount: 12,
          triggerCount: 3,
          lastExecuted: '2024-01-15T14:30:00Z',
          executionCount: 342,
          successRate: 96.8,
          averageDuration: 4800,
          tags: ['medical', 'hipaa', 'clinical', 'ner', 'compliance'],
          priority: 'high'
        },
        {
          id: 'wf_002',
          name: 'Quality Monitor',
          description: 'Real-time quality assessment with automated alerts',
          category: 'quality',
          version: '1.8.0',
          status: 'active',
          nodeCount: 8,
          triggerCount: 5,
          lastExecuted: '2024-01-15T15:45:00Z',
          executionCount: 1247,
          successRate: 99.1,
          averageDuration: 2200,
          tags: ['quality', 'monitoring', 'alerts'],
          priority: 'critical'
        },
        {
          id: 'wf_003',
          name: 'Legal Processing',
          description: 'Legal document analysis with privilege detection',
          category: 'legal',
          version: '1.5.2',
          status: 'active',
          nodeCount: 15,
          triggerCount: 2,
          lastExecuted: '2024-01-15T13:20:00Z',
          executionCount: 89,
          successRate: 94.4,
          averageDuration: 7200,
          tags: ['legal', 'privilege', 'compliance'],
          priority: 'medium'
        },
        {
          id: 'wf_004',
          name: 'Meeting Minutes',
          description: 'Extract action items and generate summaries',
          category: 'business',
          version: '1.2.0',
          status: 'draft',
          nodeCount: 6,
          triggerCount: 1,
          executionCount: 23,
          successRate: 87.0,
          averageDuration: 3200,
          tags: ['business', 'meetings', 'action-items'],
          priority: 'low'
        }
      ];

      const sampleExecutions: WorkflowExecution[] = [
        {
          id: 'exec_001',
          workflowId: 'wf_001',
          name: 'Medical Consultation Analysis',
          status: 'running',
          startedAt: '2024-01-15T16:00:00Z',
          progress: 73,
          nodeStates: {
            'input': 'completed',
            'transcribe': 'completed',
            'clinical_ner': 'running',
            'quality_check': 'pending',
            'hipaa_compliance': 'pending'
          },
          results: {},
          errors: [],
          metrics: {
            totalDuration: 3200,
            completedNodes: 3,
            failedNodes: 0,
            successRate: 100
          }
        },
        {
          id: 'exec_002',
          workflowId: 'wf_002',
          name: 'Quality Monitor',
          status: 'completed',
          startedAt: '2024-01-15T15:30:00Z',
          completedAt: '2024-01-15T15:37:00Z',
          duration: 420,
          progress: 100,
          nodeStates: {
            'monitor': 'completed',
            'assess': 'completed',
            'alert': 'completed',
            'report': 'completed'
          },
          results: {
            qualityScore: 94.7,
            alertsTriggered: 1,
            improvementSuggestions: 4
          },
          errors: [],
          metrics: {
            totalDuration: 420,
            completedNodes: 4,
            failedNodes: 0,
            successRate: 100
          }
        },
        {
          id: 'exec_003',
          workflowId: 'wf_003',
          name: 'Legal Processing',
          status: 'failed',
          startedAt: '2024-01-15T14:15:00Z',
          completedAt: '2024-01-15T14:18:00Z',
          duration: 180,
          progress: 25,
          nodeStates: {
            'input': 'completed',
            'analyze': 'failed',
            'privilege_check': 'cancelled'
          },
          results: {},
          errors: [
            { nodeId: 'analyze', error: 'Failed to connect to legal database', timestamp: '2024-01-15T14:17:00Z' }
          ],
          metrics: {
            totalDuration: 180,
            completedNodes: 1,
            failedNodes: 1,
            successRate: 50
          }
        }
      ];

      setWorkflows(sampleWorkflows);
      setExecutions(sampleExecutions);

      // Update system metrics
      setSystemMetrics(prev => ({
        ...prev,
        cpuUsage: 35 + Math.random() * 30,
        memoryUsage: 45 + Math.random() * 25,
        queueLength: Math.floor(Math.random() * 15),
        activeConnections: 8 + Math.floor(Math.random() * 12)
      }));

    } catch (error) {
      console.error('Failed to load workflow data:', error);
      Alert.alert('Error', 'Failed to load workflow data. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    // Set up periodic refresh
    const interval = setInterval(() => {
      if (selectedTab === 'overview') {
        loadData();
      }
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [loadData, selectedTab]);

  // Filtered and sorted workflows
  const filteredWorkflows = useMemo(() => {
    let filtered = workflows.filter(workflow => {
      const matchesSearch = workflow.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           workflow.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           workflow.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
      const matchesStatus = filterStatus === 'all' || workflow.status === filterStatus;
      const matchesCategory = filterCategory === 'all' || workflow.category === filterCategory;
      return matchesSearch && matchesStatus && matchesCategory;
    });

    // Sort workflows
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'status':
          return a.status.localeCompare(b.status);
        case 'lastExecuted':
        default:
          return new Date(b.lastExecuted || 0).getTime() - new Date(a.lastExecuted || 0).getTime();
      }
    });

    return filtered;
  }, [workflows, searchQuery, filterStatus, filterCategory, sortBy]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    loadData();
  }, [loadData]);

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'running': return '#3B82F6';
      case 'completed': return '#10B981';
      case 'failed': return '#EF4444';
      case 'paused': return '#F59E0B';
      case 'active': return '#10B981';
      case 'draft': return '#6B7280';
      default: return '#6B7280';
    }
  };

  const getPriorityColor = (priority: string): string => {
    switch (priority) {
      case 'critical': return '#DC2626';
      case 'high': return '#EA580C';
      case 'medium': return '#D97706';
      case 'low': return '#059669';
      default: return '#6B7280';
    }
  };

  const getStatusIcon = (status: string): string => {
    switch (status) {
      case 'running': return 'play';
      case 'completed': return 'checkmark-circle';
      case 'failed': return 'close-circle';
      case 'paused': return 'pause';
      case 'active': return 'checkmark-circle';
      case 'draft': return 'create';
      default: return 'time';
    }
  };

  const formatDuration = (ms: number): string => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    return hours > 0 ? `${hours}h ${minutes % 60}m` : `${minutes}m ${seconds % 60}s`;
  };

  const formatTimeAgo = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    
    if (diffHours > 0) {
      return `${diffHours}h ago`;
    } else if (diffMinutes > 0) {
      return `${diffMinutes}m ago`;
    } else {
      return 'Just now';
    }
  };

  const executeWorkflow = async (workflowId: string) => {
    try {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      // Simulate workflow execution
      Alert.alert('Workflow Started', 'The workflow has been queued for execution.');
      
      // Schedule local notification
      await Notifications.scheduleNotificationAsync({
        content: {
          title: 'Workflow Execution Started',
          body: `${workflows.find(w => w.id === workflowId)?.name} is now running`,
          data: { workflowId }
        },
        trigger: { seconds: 1 }
      });
    } catch (error) {
      Alert.alert('Error', 'Failed to start workflow execution.');
    }
  };

  const shareWorkflowResults = async (execution: WorkflowExecution) => {
    try {
      const shareContent = `Workflow Execution Report\n\nName: ${execution.name}\nStatus: ${execution.status}\nSuccess Rate: ${execution.metrics.successRate}%\nDuration: ${execution.duration ? formatDuration(execution.duration) : 'N/A'}\n\nGenerated by Workflow Management App`;
      
      await Share.share({
        message: shareContent,
        title: 'Workflow Execution Report'
      });
    } catch (error) {
      console.error('Failed to share:', error);
    }
  };

  const renderWorkflowCard = ({ item: workflow }: { item: WorkflowDefinition }) => (
    <Animated.View
      entering={FadeIn.delay(100)}
      style={styles.workflowCard}
    >
      <TouchableOpacity
        onPress={() => setSelectedWorkflow(workflow.id)}
        onLongPress={() => {
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
          // Show action sheet
        }}
        activeOpacity={0.7}
      >
        <LinearGradient
          colors={['#FFFFFF', '#F9FAFB']}
          style={styles.cardGradient}
        >
          <View style={styles.cardHeader}>
            <View style={styles.cardTitleRow}>
              <View style={[styles.statusIndicator, { backgroundColor: getStatusColor(workflow.status) }]} />
              <Text style={styles.workflowTitle} numberOfLines={1}>{workflow.name}</Text>
              <Badge
                text={workflow.priority}
                backgroundColor={getPriorityColor(workflow.priority)}
                textColor="#FFFFFF"
                size="small"
              />
            </View>
            <View style={styles.cardMetaRow}>
              <Text style={styles.versionText}>v{workflow.version}</Text>
              <Badge
                text={workflow.category}
                backgroundColor="#E5E7EB"
                textColor="#374151"
                size="small"
              />
            </View>
          </View>

          <Text style={styles.workflowDescription} numberOfLines={2}>
            {workflow.description}
          </Text>

          <View style={styles.metricsGrid}>
            <View style={styles.metricItem}>
              <MaterialCommunityIcons name="sitemap" size={16} color="#6B7280" />
              <Text style={styles.metricLabel}>Nodes</Text>
              <Text style={styles.metricValue}>{workflow.nodeCount}</Text>
            </View>
            <View style={styles.metricItem}>
              <Ionicons name="bar-chart" size={16} color="#6B7280" />
              <Text style={styles.metricLabel}>Executions</Text>
              <Text style={styles.metricValue}>{workflow.executionCount}</Text>
            </View>
            <View style={styles.metricItem}>
              <MaterialCommunityIcons name="trending-up" size={16} color="#6B7280" />
              <Text style={styles.metricLabel}>Success</Text>
              <Text style={styles.metricValue}>{workflow.successRate.toFixed(1)}%</Text>
            </View>
            <View style={styles.metricItem}>
              <Ionicons name="time" size={16} color="#6B7280" />
              <Text style={styles.metricLabel}>Avg Duration</Text>
              <Text style={styles.metricValue}>{formatDuration(workflow.averageDuration)}</Text>
            </View>
          </View>

          <View style={styles.tagsContainer}>
            {workflow.tags.slice(0, 3).map(tag => (
              <Badge
                key={tag}
                text={tag}
                backgroundColor="#EEF2FF"
                textColor="#3730A3"
                size="small"
              />
            ))}
            {workflow.tags.length > 3 && (
              <Text style={styles.moreTagsText}>+{workflow.tags.length - 3} more</Text>
            )}
          </View>

          <View style={styles.cardActions}>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => executeWorkflow(workflow.id)}
            >
              <Ionicons name="play" size={16} color="#3B82F6" />
              <Text style={styles.actionButtonText}>Execute</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => {/* Navigate to edit */}}
            >
              <Ionicons name="create" size={16} color="#6B7280" />
              <Text style={styles.actionButtonText}>Edit</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => {/* Show more options */}}
            >
              <Ionicons name="ellipsis-horizontal" size={16} color="#6B7280" />
            </TouchableOpacity>
          </View>

          {workflow.lastExecuted && (
            <Text style={styles.lastExecutedText}>
              Last executed {formatTimeAgo(workflow.lastExecuted)}
            </Text>
          )}
        </LinearGradient>
      </TouchableOpacity>
    </Animated.View>
  );

  const renderExecutionCard = ({ item: execution }: { item: WorkflowExecution }) => (
    <Animated.View
      entering={SlideInRight.delay(100)}
      style={styles.executionCard}
    >
      <TouchableOpacity
        onPress={() => {/* Navigate to execution details */}}
        onLongPress={() => shareWorkflowResults(execution)}
        activeOpacity={0.7}
      >
        <View style={styles.executionHeader}>
          <View style={styles.executionTitleRow}>
            <Ionicons 
              name={getStatusIcon(execution.status)} 
              size={20} 
              color={getStatusColor(execution.status)} 
            />
            <Text style={styles.executionTitle} numberOfLines={1}>{execution.name}</Text>
            <Badge
              text={execution.status}
              backgroundColor={getStatusColor(execution.status)}
              textColor="#FFFFFF"
              size="small"
            />
          </View>
          <Text style={styles.executionId}>ID: {execution.id}</Text>
        </View>

        {execution.status === 'running' && (
          <Animated.View style={[styles.progressContainer, useAnimatedStyle(() => ({
            transform: [{ scale: pulseAnimation.value }]
          }))]}>
            <View style={styles.progressHeader}>
              <Text style={styles.progressLabel}>Progress</Text>
              <Text style={styles.progressPercentage}>{execution.progress}%</Text>
            </View>
            <Progress
              progress={execution.progress / 100}
              height={6}
              backgroundColor="#E5E7EB"
              fillColor="#3B82F6"
              animated={true}
            />
            <Text style={styles.progressSubtext}>
              {execution.metrics.completedNodes} of {Object.keys(execution.nodeStates).length} nodes completed
            </Text>
          </Animated.View>
        )}

        <View style={styles.executionMetrics}>
          <View style={styles.executionMetricItem}>
            <Text style={styles.executionMetricLabel}>Started</Text>
            <Text style={styles.executionMetricValue}>
              {new Date(execution.startedAt).toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
              })}
            </Text>
          </View>
          <View style={styles.executionMetricItem}>
            <Text style={styles.executionMetricLabel}>Duration</Text>
            <Text style={styles.executionMetricValue}>
              {execution.duration ? 
                formatDuration(execution.duration) : 
                formatDuration(Date.now() - new Date(execution.startedAt).getTime())
              }
            </Text>
          </View>
          <View style={styles.executionMetricItem}>
            <Text style={styles.executionMetricLabel}>Success Rate</Text>
            <Text style={styles.executionMetricValue}>{execution.metrics.successRate}%</Text>
          </View>
        </View>

        {execution.errors.length > 0 && (
          <View style={styles.errorContainer}>
            <MaterialCommunityIcons name="alert-circle" size={16} color="#EF4444" />
            <Text style={styles.errorText}>
              {execution.errors.length} error{execution.errors.length > 1 ? 's' : ''} occurred
            </Text>
          </View>
        )}
      </TouchableOpacity>
    </Animated.View>
  );

  const OverviewTab = () => (
    <ScrollView
      style={styles.tabContent}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
      showsVerticalScrollIndicator={false}
    >
      {/* System Status */}
      <View style={styles.systemStatusContainer}>
        <Text style={styles.sectionTitle}>System Status</Text>
        <View style={styles.systemMetricsGrid}>
          <View style={[styles.systemMetricCard, { borderLeftColor: '#3B82F6' }]}>
            <Ionicons name="hardware-chip" size={20} color="#3B82F6" />
            <Text style={styles.systemMetricValue}>{Math.round(systemMetrics.cpuUsage)}%</Text>
            <Text style={styles.systemMetricLabel}>CPU Usage</Text>
          </View>
          <View style={[styles.systemMetricCard, { borderLeftColor: '#10B981' }]}>
            <MaterialCommunityIcons name="memory" size={20} color="#10B981" />
            <Text style={styles.systemMetricValue}>{Math.round(systemMetrics.memoryUsage)}%</Text>
            <Text style={styles.systemMetricLabel}>Memory</Text>
          </View>
          <View style={[styles.systemMetricCard, { borderLeftColor: '#F59E0B' }]}>
            <MaterialCommunityIcons name="playlist-check" size={20} color="#F59E0B" />
            <Text style={styles.systemMetricValue}>{systemMetrics.queueLength}</Text>
            <Text style={styles.systemMetricLabel}>Queue</Text>
          </View>
          <View style={[styles.systemMetricCard, { borderLeftColor: '#8B5CF6' }]}>
            <MaterialCommunityIcons name="wifi" size={20} color="#8B5CF6" />
            <Text style={styles.systemMetricValue}>{systemMetrics.activeConnections}</Text>
            <Text style={styles.systemMetricLabel}>Connections</Text>
          </View>
        </View>
      </View>

      {/* Quick Stats */}
      <View style={styles.quickStatsContainer}>
        <Text style={styles.sectionTitle}>Quick Stats</Text>
        <View style={styles.quickStatsGrid}>
          <LinearGradient
            colors={['#10B981', '#059669']}
            style={styles.quickStatCard}
          >
            <MaterialCommunityIcons name="check-circle" size={24} color="#FFFFFF" />
            <Text style={styles.quickStatValue}>96.8%</Text>
            <Text style={styles.quickStatLabel}>Success Rate</Text>
          </LinearGradient>
          <LinearGradient
            colors={['#3B82F6', '#2563EB']}
            style={styles.quickStatCard}
          >
            <Ionicons name="time" size={24} color="#FFFFFF" />
            <Text style={styles.quickStatValue}>4.2min</Text>
            <Text style={styles.quickStatLabel}>Avg Duration</Text>
          </LinearGradient>
          <LinearGradient
            colors={['#F59E0B', '#D97706']}
            style={styles.quickStatCard}
          >
            <MaterialCommunityIcons name="lightning-bolt" size={24} color="#FFFFFF" />
            <Text style={styles.quickStatValue}>{executions.length}</Text>
            <Text style={styles.quickStatLabel}>Active Executions</Text>
          </LinearGradient>
        </View>
      </View>

      {/* Recent Activities */}
      <View style={styles.recentActivitiesContainer}>
        <Text style={styles.sectionTitle}>Recent Executions</Text>
        {executions.slice(0, 3).map(execution => (
          <View key={execution.id} style={styles.recentActivityItem}>
            <View style={styles.activityIconContainer}>
              <Ionicons 
                name={getStatusIcon(execution.status)} 
                size={16} 
                color={getStatusColor(execution.status)} 
              />
            </View>
            <View style={styles.activityContent}>
              <Text style={styles.activityTitle} numberOfLines={1}>{execution.name}</Text>
              <Text style={styles.activitySubtitle}>
                {execution.status === 'running' ? 
                  `Running • ${execution.progress}% complete` : 
                  `${execution.status} • ${formatTimeAgo(execution.startedAt)}`
                }
              </Text>
            </View>
            <TouchableOpacity style={styles.activityAction}>
              <Ionicons name="chevron-forward" size={16} color="#9CA3AF" />
            </TouchableOpacity>
          </View>
        ))}
      </View>
    </ScrollView>
  );

  return (
    <ErrorBoundary>
      <SafeAreaView style={[styles.container, { paddingTop: insets.top }]}>
        <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />
        
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerTitle}>
            <MaterialCommunityIcons name="sitemap" size={28} color="#1F2937" />
            <View style={styles.headerTextContainer}>
              <Text style={styles.headerTitleText}>Workflows</Text>
              <View style={styles.headerSubtitle}>
                <View style={[styles.networkIndicator, { 
                  backgroundColor: systemMetrics.networkStatus === 'online' ? '#10B981' : 
                                   systemMetrics.networkStatus === 'poor' ? '#F59E0B' : '#EF4444'
                }]} />
                <Text style={styles.headerSubtitleText}>
                  {executions.filter(e => e.status === 'running').length} running
                </Text>
              </View>
            </View>
          </View>
          
          <TouchableOpacity 
            style={styles.headerAction}
            onPress={() => {/* Show notifications */}}
          >
            <Ionicons name="notifications" size={24} color="#6B7280" />
          </TouchableOpacity>
        </View>

        {/* Search Bar */}
        <View style={styles.searchContainer}>
          <SearchBar
            placeholder="Search workflows, tags..."
            value={searchQuery}
            onChangeText={setSearchQuery}
            style={styles.searchBar}
          />
          <TouchableOpacity
            style={styles.filterButton}
            onPress={() => setShowFilters(!showFilters)}
          >
            <MaterialCommunityIcons name="filter-variant" size={20} color="#6B7280" />
          </TouchableOpacity>
        </View>

        {/* Filters (collapsible) */}
        {showFilters && (
          <Animated.View
            entering={FadeIn}
            exiting={FadeOut}
            style={styles.filtersContainer}
          >
            <View style={styles.filterRow}>
              <Text style={styles.filterLabel}>Status:</Text>
              <View style={styles.filterOptions}>
                {['all', 'active', 'draft', 'deprecated'].map(status => (
                  <TouchableOpacity
                    key={status}
                    style={[
                      styles.filterOption,
                      filterStatus === status && styles.filterOptionActive
                    ]}
                    onPress={() => setFilterStatus(status)}
                  >
                    <Text style={[
                      styles.filterOptionText,
                      filterStatus === status && styles.filterOptionTextActive
                    ]}>
                      {status.charAt(0).toUpperCase() + status.slice(1)}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </Animated.View>
        )}

        {/* Tabs */}
        <Tabs
          selectedTab={selectedTab}
          onTabChange={setSelectedTab}
          tabs={[
            { id: 'overview', label: 'Overview' },
            { id: 'workflows', label: `Workflows (${filteredWorkflows.length})` },
            { id: 'executions', label: `Executions (${executions.length})` }
          ]}
          style={styles.tabs}
        />

        {/* Tab Content */}
        <View style={styles.tabContentContainer}>
          {selectedTab === 'overview' && <OverviewTab />}
          
          {selectedTab === 'workflows' && (
            <FlatList
              data={filteredWorkflows}
              renderItem={renderWorkflowCard}
              keyExtractor={item => item.id}
              contentContainerStyle={styles.listContainer}
              showsVerticalScrollIndicator={false}
              refreshControl={
                <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
              }
              ListEmptyComponent={() => (
                <View style={styles.emptyState}>
                  <MaterialCommunityIcons name="sitemap" size={64} color="#D1D5DB" />
                  <Text style={styles.emptyStateText}>No workflows found</Text>
                  <Text style={styles.emptyStateSubtext}>
                    {searchQuery ? 'Try adjusting your search criteria' : 'Create your first workflow to get started'}
                  </Text>
                </View>
              )}
            />
          )}
          
          {selectedTab === 'executions' && (
            <FlatList
              data={executions}
              renderItem={renderExecutionCard}
              keyExtractor={item => item.id}
              contentContainerStyle={styles.listContainer}
              showsVerticalScrollIndicator={false}
              refreshControl={
                <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
              }
              ListEmptyComponent={() => (
                <View style={styles.emptyState}>
                  <Ionicons name="play-circle" size={64} color="#D1D5DB" />
                  <Text style={styles.emptyStateText}>No executions</Text>
                  <Text style={styles.emptyStateSubtext}>Execute a workflow to see results here</Text>
                </View>
              )}
            />
          )}
        </View>

        {/* Floating Action Button */}
        <FloatingActionButton
          icon="plus"
          onPress={() => {/* Create new workflow */}}
          style={styles.fab}
        />

        {/* Loading Overlay */}
        {loading && (
          <BlurView intensity={50} style={styles.loadingOverlay}>
            <LoadingSpinner size="large" color="#3B82F6" />
            <Text style={styles.loadingText}>Loading workflows...</Text>
          </BlurView>
        )}
      </SafeAreaView>
    </ErrorBoundary>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB'
  },
  
  // Header Styles
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB'
  },
  headerTitle: {
    flexDirection: 'row',
    alignItems: 'center'
  },
  headerTextContainer: {
    marginLeft: 12
  },
  headerTitleText: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1F2937'
  },
  headerSubtitle: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 2
  },
  networkIndicator: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 6
  },
  headerSubtitleText: {
    fontSize: 12,
    color: '#6B7280'
  },
  headerAction: {
    padding: 8,
    borderRadius: 8,
    backgroundColor: '#F3F4F6'
  },
  
  // Search and Filter Styles
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB'
  },
  searchBar: {
    flex: 1,
    marginRight: 12
  },
  filterButton: {
    padding: 8,
    borderRadius: 8,
    backgroundColor: '#F3F4F6'
  },
  filtersContainer: {
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB'
  },
  filterRow: {
    flexDirection: 'row',
    alignItems: 'center'
  },
  filterLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    marginRight: 12,
    minWidth: 50
  },
  filterOptions: {
    flexDirection: 'row',
    flex: 1
  },
  filterOption: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginRight: 8,
    borderRadius: 16,
    backgroundColor: '#F3F4F6'
  },
  filterOptionActive: {
    backgroundColor: '#3B82F6'
  },
  filterOptionText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#6B7280'
  },
  filterOptionTextActive: {
    color: '#FFFFFF'
  },
  
  // Tab Styles
  tabs: {
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB'
  },
  tabContentContainer: {
    flex: 1
  },
  tabContent: {
    flex: 1
  },
  
  // Overview Tab Styles
  systemStatusContainer: {
    padding: 20
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 16
  },
  systemMetricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -6
  },
  systemMetricCard: {
    width: '48%',
    margin: '1%',
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2
  },
  systemMetricValue: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1F2937',
    marginVertical: 4
  },
  systemMetricLabel: {
    fontSize: 12,
    color: '#6B7280'
  },
  
  quickStatsContainer: {
    paddingHorizontal: 20,
    paddingBottom: 20
  },
  quickStatsGrid: {
    flexDirection: 'row',
    marginHorizontal: -8
  },
  quickStatCard: {
    flex: 1,
    margin: 8,
    padding: 20,
    borderRadius: 12,
    alignItems: 'center'
  },
  quickStatValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
    marginVertical: 4
  },
  quickStatLabel: {
    fontSize: 12,
    color: '#FFFFFF',
    opacity: 0.9
  },
  
  recentActivitiesContainer: {
    paddingHorizontal: 20,
    paddingBottom: 20
  },
  recentActivityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    marginBottom: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2
  },
  activityIconContainer: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12
  },
  activityContent: {
    flex: 1
  },
  activityTitle: {
    fontSize: 14,
    fontWeight: '500',
    color: '#1F2937'
  },
  activitySubtitle: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2
  },
  activityAction: {
    padding: 4
  },
  
  // Workflow Card Styles
  listContainer: {
    padding: 20,
    paddingBottom: 100
  },
  workflowCard: {
    marginBottom: 16,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4
  },
  cardGradient: {
    padding: 20,
    borderRadius: 16
  },
  cardHeader: {
    marginBottom: 12
  },
  cardTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4
  },
  statusIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8
  },
  workflowTitle: {
    flex: 1,
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
    marginRight: 8
  },
  cardMetaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between'
  },
  versionText: {
    fontSize: 12,
    color: '#6B7280'
  },
  workflowDescription: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
    marginBottom: 16
  },
  metricsGrid: {
    flexDirection: 'row',
    marginBottom: 16
  },
  metricItem: {
    flex: 1,
    alignItems: 'center'
  },
  metricLabel: {
    fontSize: 10,
    color: '#9CA3AF',
    marginTop: 2,
    marginBottom: 2
  },
  metricValue: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1F2937'
  },
  tagsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    flexWrap: 'wrap'
  },
  moreTagsText: {
    fontSize: 12,
    color: '#6B7280',
    marginLeft: 8
  },
  cardActions: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginRight: 8,
    borderRadius: 8,
    backgroundColor: '#F3F4F6'
  },
  actionButtonText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#374151',
    marginLeft: 4
  },
  lastExecutedText: {
    fontSize: 11,
    color: '#9CA3AF'
  },
  
  // Execution Card Styles
  executionCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4
  },
  executionHeader: {
    marginBottom: 16
  },
  executionTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4
  },
  executionTitle: {
    flex: 1,
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
    marginHorizontal: 8
  },
  executionId: {
    fontSize: 12,
    color: '#6B7280'
  },
  progressContainer: {
    marginBottom: 16
  },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8
  },
  progressLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151'
  },
  progressPercentage: {
    fontSize: 14,
    fontWeight: '600',
    color: '#3B82F6'
  },
  progressSubtext: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 4
  },
  executionMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16
  },
  executionMetricItem: {
    flex: 1,
    alignItems: 'center'
  },
  executionMetricLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4
  },
  executionMetricValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937'
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#FEF2F2',
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#EF4444'
  },
  errorText: {
    fontSize: 12,
    color: '#DC2626',
    marginLeft: 8
  },
  
  // Empty State Styles
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60
  },
  emptyStateText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#9CA3AF',
    marginTop: 16
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#D1D5DB',
    marginTop: 8,
    textAlign: 'center',
    paddingHorizontal: 40
  },
  
  // Floating Action Button
  fab: {
    position: 'absolute',
    bottom: 20,
    right: 20
  },
  
  // Loading Overlay
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.9)'
  },
  loadingText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#6B7280',
    marginTop: 16
  }
});

export default WorkflowManagementScreen;