import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
  Modal,
  FlatList,
  Switch,
  RefreshControl,
  Dimensions,
  Animated,
  PanResponder,
  TextInput,
  Pressable,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { apiClient } from '../../services/api';
import { theme } from '../../theme';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { LineChart, BarChart, PieChart } from 'react-native-chart-kit';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

interface ProviderConfig {
  provider: string;
  api_key?: string;
  api_endpoint?: string;
  organization_id?: string;
  project_id?: string;
  region?: string;
  model_mappings: Record<string, string>;
  max_tokens?: number;
  temperature?: number;
  timeout?: number;
  retry_attempts?: number;
  rate_limit?: number;
  custom_headers?: Record<string, string>;
  enabled: boolean;
  priority: number;
}

interface ProviderStatus {
  provider: string;
  status: 'active' | 'inactive' | 'error' | 'testing' | 'rate_limited';
  health_score: number;
  response_time_avg?: number;
  error_rate?: number;
  requests_today: number;
  last_used?: string;
  last_error?: string;
  models_available: string[];
}

interface ProviderUsageStats {
  provider: string;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  total_tokens: number;
  total_cost: number;
  average_response_time: number;
  uptime_percentage: number;
  last_7_days: Array<{ date: string; requests: number; tokens: number }>;
  by_model_type: Record<string, { requests: number; tokens: number }>;
}

const providerInfo: Record<string, { logo: string; color: string; description: string }> = {
  openai: { 
    logo: '🤖', 
    color: '#00A67E',
    description: 'Industry-leading AI models' 
  },
  anthropic: { 
    logo: '🧠', 
    color: '#6B46C1',
    description: 'Claude AI with reasoning' 
  },
  google: { 
    logo: '🔍', 
    color: '#4285F4',
    description: 'Gemini multimodal models' 
  },
  cohere: { 
    logo: '🌊', 
    color: '#39A0CA',
    description: 'Enterprise NLP tasks' 
  },
  huggingface: { 
    logo: '🤗', 
    color: '#FFD21E',
    description: 'Open-source models' 
  },
  azure_openai: { 
    logo: '☁️', 
    color: '#0078D4',
    description: 'Enterprise OpenAI' 
  },
  aws_bedrock: { 
    logo: '🏛️', 
    color: '#FF9900',
    description: 'AWS foundation models' 
  },
  local: { 
    logo: '💻', 
    color: '#424242',
    description: 'Self-hosted models' 
  },
  custom: { 
    logo: '⚙️', 
    color: '#757575',
    description: 'Custom endpoints' 
  },
};

const modelTypes = ['chat', 'completion', 'embedding', 'transcription', 'translation', 'summarization'];

const LLMProviderSelect: React.FC = () => {
  const [modalVisible, setModalVisible] = useState(false);
  const [providers, setProviders] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedTab, setSelectedTab] = useState<'providers' | 'stats' | 'config'>('providers');
  const [activeProvider, setActiveProvider] = useState<string | null>(null);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [showStatsModal, setShowStatsModal] = useState(false);
  const [showTestModal, setShowTestModal] = useState(false);
  const [providerStats, setProviderStats] = useState<ProviderUsageStats[]>([]);
  const [testResults, setTestResults] = useState<any>(null);
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);

  const [editConfig, setEditConfig] = useState<ProviderConfig>({
    provider: 'openai',
    model_mappings: {},
    enabled: true,
    priority: 0,
  });

  const slideAnim = useRef(new Animated.Value(screenHeight)).current;

  useEffect(() => {
    loadProviders();
    loadProviderStats();
  }, []);

  const loadProviders = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/api/v1/llm-providers/');
      setProviders(response.data);
      
      // Find active provider
      const active = response.data.find((p: any) => p.is_active);
      setActiveProvider(active?.provider || null);
    } catch (error) {
      console.error('Failed to load providers:', error);
      Alert.alert('Error', 'Failed to load providers');
    } finally {
      setLoading(false);
    }
  };

  const loadProviderStats = async () => {
    try {
      const response = await apiClient.get('/api/v1/llm-providers/usage/stats');
      setProviderStats(response.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadProviders();
    await loadProviderStats();
    setRefreshing(false);
  };

  const switchProvider = async (provider: string) => {
    try {
      await apiClient.put('/api/v1/llm-providers/switch', { provider });
      setActiveProvider(provider);
      Alert.alert('Success', `Switched to ${provider.toUpperCase()}`);
      loadProviders();
    } catch (error) {
      Alert.alert('Error', 'Failed to switch provider');
    }
  };

  const testProvider = async (provider: string) => {
    try {
      setTestResults(null);
      const response = await apiClient.post('/api/v1/llm-providers/test', {
        provider,
        test_prompt: 'Hello, can you respond?',
      });
      setTestResults(response.data);
      setShowTestModal(true);
    } catch (error) {
      Alert.alert('Error', 'Provider test failed');
    }
  };

  const configureProvider = (provider?: any) => {
    if (provider) {
      setEditConfig({
        provider: provider.provider,
        model_mappings: provider.models || {},
        enabled: provider.enabled,
        priority: provider.priority,
        api_key: '',
      });
    } else {
      setEditConfig({
        provider: 'openai',
        model_mappings: {},
        enabled: true,
        priority: 0,
      });
    }
    setShowConfigModal(true);
  };

  const saveConfiguration = async () => {
    try {
      await apiClient.post('/api/v1/llm-providers/configure', editConfig);
      Alert.alert('Success', 'Provider configured successfully');
      setShowConfigModal(false);
      loadProviders();
    } catch (error) {
      Alert.alert('Error', 'Failed to configure provider');
    }
  };

  const deleteProvider = (provider: string) => {
    Alert.alert(
      'Delete Provider',
      `Are you sure you want to delete ${provider.toUpperCase()}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await apiClient.delete(`/api/v1/llm-providers/${provider}`);
              Alert.alert('Success', 'Provider deleted');
              loadProviders();
            } catch (error) {
              Alert.alert('Error', 'Failed to delete provider');
            }
          },
        },
      ]
    );
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return 'check-circle';
      case 'error':
        return 'error';
      case 'testing':
        return 'sync';
      case 'rate_limited':
        return 'timer';
      default:
        return 'radio-button-unchecked';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return theme.colors.success;
      case 'error':
        return theme.colors.error;
      case 'testing':
        return theme.colors.warning;
      case 'rate_limited':
        return theme.colors.warning;
      default:
        return theme.colors.textSecondary;
    }
  };

  const getHealthColor = (score: number) => {
    if (score >= 90) return theme.colors.success;
    if (score >= 70) return theme.colors.warning;
    return theme.colors.error;
  };

  const renderProviderItem = ({ item }: { item: any }) => {
    const info = providerInfo[item.provider] || providerInfo.custom;
    const stats = providerStats.find(s => s.provider === item.provider);
    const isActive = activeProvider === item.provider;

    return (
      <View style={[styles.providerCard, isActive && styles.activeProviderCard]}>
        <View style={styles.providerHeader}>
          <View style={styles.providerInfo}>
            <View style={[styles.providerLogo, { backgroundColor: info.color + '20' }]}>
              <Text style={styles.providerEmoji}>{info.logo}</Text>
            </View>
            <View style={styles.providerDetails}>
              <View style={styles.providerTitleRow}>
                <Text style={styles.providerName}>{item.provider.toUpperCase()}</Text>
                {isActive && (
                  <View style={styles.activeBadge}>
                    <Icon name="check" size={12} color="#fff" />
                    <Text style={styles.activeBadgeText}>Active</Text>
                  </View>
                )}
              </View>
              <Text style={styles.providerDescription}>{info.description}</Text>
              <View style={styles.statusRow}>
                <Icon
                  name={getStatusIcon(item.status)}
                  size={16}
                  color={getStatusColor(item.status)}
                />
                <Text style={[styles.statusText, { color: getStatusColor(item.status) }]}>
                  {item.status}
                </Text>
                <Text style={styles.priorityText}>Priority: {item.priority}</Text>
              </View>
            </View>
          </View>
          <View style={styles.providerActions}>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => testProvider(item.provider)}
            >
              <Icon name="play-arrow" size={20} color={theme.colors.primary} />
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => configureProvider(item)}
            >
              <Icon name="edit" size={20} color={theme.colors.primary} />
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => deleteProvider(item.provider)}
            >
              <Icon name="delete" size={20} color={theme.colors.error} />
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.providerMetrics}>
          <View style={styles.healthScore}>
            <Text style={styles.metricLabel}>Health Score</Text>
            <View style={styles.healthBar}>
              <View
                style={[
                  styles.healthBarFill,
                  {
                    width: `${item.health_score}%`,
                    backgroundColor: getHealthColor(item.health_score),
                  },
                ]}
              />
            </View>
            <Text style={styles.healthText}>{item.health_score}%</Text>
          </View>

          {stats && (
            <View style={styles.quickStats}>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{stats.total_requests}</Text>
                <Text style={styles.statLabel}>Requests</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{stats.average_response_time.toFixed(2)}s</Text>
                <Text style={styles.statLabel}>Avg Time</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>
                  {((stats.successful_requests / stats.total_requests) * 100).toFixed(1)}%
                </Text>
                <Text style={styles.statLabel}>Success</Text>
              </View>
            </View>
          )}
        </View>

        {!isActive && item.enabled && (
          <TouchableOpacity
            style={styles.switchButton}
            onPress={() => switchProvider(item.provider)}
          >
            <Icon name="swap-horiz" size={16} color="#fff" />
            <Text style={styles.switchButtonText}>Switch to this provider</Text>
          </TouchableOpacity>
        )}
      </View>
    );
  };

  const renderStatsChart = (stats: ProviderUsageStats) => {
    const info = providerInfo[stats.provider] || providerInfo.custom;
    
    return (
      <View key={stats.provider} style={styles.statsCard}>
        <View style={styles.statsHeader}>
          <View style={[styles.statsLogo, { backgroundColor: info.color + '20' }]}>
            <Text style={styles.statsEmoji}>{info.logo}</Text>
          </View>
          <Text style={styles.statsTitle}>{stats.provider.toUpperCase()}</Text>
        </View>

        <View style={styles.statsMetrics}>
          <View style={styles.metricCard}>
            <Text style={styles.metricNumber}>{stats.total_requests}</Text>
            <Text style={styles.metricLabel}>Total Requests</Text>
          </View>
          <View style={styles.metricCard}>
            <Text style={[styles.metricNumber, { color: theme.colors.success }]}>
              {((stats.successful_requests / stats.total_requests) * 100).toFixed(1)}%
            </Text>
            <Text style={styles.metricLabel}>Success Rate</Text>
          </View>
          <View style={styles.metricCard}>
            <Text style={styles.metricNumber}>${stats.total_cost.toFixed(2)}</Text>
            <Text style={styles.metricLabel}>Total Cost</Text>
          </View>
          <View style={styles.metricCard}>
            <Text style={styles.metricNumber}>{stats.average_response_time.toFixed(2)}s</Text>
            <Text style={styles.metricLabel}>Avg Response</Text>
          </View>
        </View>

        <Text style={styles.chartTitle}>Last 7 Days Usage</Text>
        <LineChart
          data={{
            labels: stats.last_7_days.map(d => d.date.split('-').pop() || ''),
            datasets: [{
              data: stats.last_7_days.map(d => d.requests),
              color: () => info.color,
            }],
          }}
          width={screenWidth - 60}
          height={150}
          chartConfig={{
            backgroundColor: theme.colors.surface,
            backgroundGradientFrom: theme.colors.surface,
            backgroundGradientTo: theme.colors.surface,
            decimalPlaces: 0,
            color: () => info.color,
            labelColor: () => theme.colors.text,
            style: { borderRadius: 8 },
            propsForDots: {
              r: '3',
              strokeWidth: '2',
              stroke: info.color,
            },
          }}
          bezier
          style={styles.chart}
        />
      </View>
    );
  };

  return (
    <>
      {/* Main Button */}
      <TouchableOpacity
        style={[styles.mainButton, activeProvider && styles.mainButtonActive]}
        onPress={() => setModalVisible(true)}
      >
        <View style={styles.buttonContent}>
          <Text style={styles.buttonEmoji}>
            {activeProvider ? providerInfo[activeProvider]?.logo : '🤖'}
          </Text>
          <View style={styles.buttonText}>
            <Text style={styles.buttonLabel}>LLM Provider</Text>
            <Text style={styles.buttonValue}>
              {activeProvider ? activeProvider.toUpperCase() : 'Select Provider'}
            </Text>
          </View>
        </View>
        <Icon name="expand-more" size={24} color={theme.colors.text} />
      </TouchableOpacity>

      {/* Main Modal */}
      <Modal
        visible={modalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            {/* Header */}
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>LLM Providers</Text>
              <View style={styles.headerActions}>
                <TouchableOpacity
                  style={styles.headerButton}
                  onPress={() => configureProvider()}
                >
                  <Icon name="add" size={24} color={theme.colors.text} />
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.headerButton}
                  onPress={() => setModalVisible(false)}
                >
                  <Icon name="close" size={24} color={theme.colors.text} />
                </TouchableOpacity>
              </View>
            </View>

            {/* Tabs */}
            <View style={styles.tabs}>
              <TouchableOpacity
                style={[styles.tab, selectedTab === 'providers' && styles.activeTab]}
                onPress={() => setSelectedTab('providers')}
              >
                <Text style={[styles.tabText, selectedTab === 'providers' && styles.activeTabText]}>
                  Providers
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.tab, selectedTab === 'stats' && styles.activeTab]}
                onPress={() => setSelectedTab('stats')}
              >
                <Text style={[styles.tabText, selectedTab === 'stats' && styles.activeTabText]}>
                  Stats
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.tab, selectedTab === 'config' && styles.activeTab]}
                onPress={() => setSelectedTab('config')}
              >
                <Text style={[styles.tabText, selectedTab === 'config' && styles.activeTabText]}>
                  Settings
                </Text>
              </TouchableOpacity>
            </View>

            {/* Content */}
            <View style={styles.tabContent}>
              {selectedTab === 'providers' && (
                <>
                  {loading ? (
                    <View style={styles.centerContainer}>
                      <ActivityIndicator size="large" color={theme.colors.primary} />
                    </View>
                  ) : providers.length === 0 ? (
                    <View style={styles.centerContainer}>
                      <Text style={styles.emptyText}>No providers configured</Text>
                      <TouchableOpacity
                        style={styles.addButton}
                        onPress={() => configureProvider()}
                      >
                        <Icon name="add" size={20} color="#fff" />
                        <Text style={styles.addButtonText}>Add Provider</Text>
                      </TouchableOpacity>
                    </View>
                  ) : (
                    <FlatList
                      data={providers}
                      renderItem={renderProviderItem}
                      keyExtractor={item => item.provider}
                      refreshControl={
                        <RefreshControl
                          refreshing={refreshing}
                          onRefresh={onRefresh}
                          colors={[theme.colors.primary]}
                        />
                      }
                      showsVerticalScrollIndicator={false}
                      contentContainerStyle={styles.providersList}
                    />
                  )}
                </>
              )}

              {selectedTab === 'stats' && (
                <ScrollView
                  style={styles.statsContainer}
                  refreshControl={
                    <RefreshControl
                      refreshing={refreshing}
                      onRefresh={onRefresh}
                      colors={[theme.colors.primary]}
                    />
                  }
                  showsVerticalScrollIndicator={false}
                >
                  {providerStats.length === 0 ? (
                    <View style={styles.centerContainer}>
                      <Icon name="bar-chart" size={64} color={theme.colors.textSecondary} />
                      <Text style={styles.emptyText}>No usage data available</Text>
                      <Text style={styles.emptySubtext}>Start using providers to see analytics</Text>
                    </View>
                  ) : (
                    <>
                      {/* Summary */}
                      <View style={styles.summaryCard}>
                        <Text style={styles.summaryTitle}>Overall Usage</Text>
                        <View style={styles.summaryMetrics}>
                          <View style={styles.summaryItem}>
                            <Text style={styles.summaryNumber}>
                              {providerStats.reduce((sum, stat) => sum + stat.total_requests, 0)}
                            </Text>
                            <Text style={styles.summaryLabel}>Total Requests</Text>
                          </View>
                          <View style={styles.summaryItem}>
                            <Text style={styles.summaryNumber}>
                              {(providerStats.reduce((sum, stat) => sum + stat.total_tokens, 0) / 1000).toFixed(1)}k
                            </Text>
                            <Text style={styles.summaryLabel}>Total Tokens</Text>
                          </View>
                          <View style={styles.summaryItem}>
                            <Text style={[styles.summaryNumber, { color: theme.colors.success }]}>
                              ${providerStats.reduce((sum, stat) => sum + stat.total_cost, 0).toFixed(2)}
                            </Text>
                            <Text style={styles.summaryLabel}>Total Cost</Text>
                          </View>
                        </View>
                      </View>

                      {/* Individual Provider Stats */}
                      {providerStats.map(renderStatsChart)}
                    </>
                  )}
                </ScrollView>
              )}

              {selectedTab === 'config' && (
                <ScrollView style={styles.configContainer} showsVerticalScrollIndicator={false}>
                  <View style={styles.configSection}>
                    <Text style={styles.configTitle}>Global Settings</Text>
                    
                    <View style={styles.configRow}>
                      <Text style={styles.configLabel}>Auto-failover</Text>
                      <Switch
                        value={true}
                        trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
                      />
                    </View>
                    
                    <View style={styles.configRow}>
                      <Text style={styles.configLabel}>Enable caching</Text>
                      <Switch
                        value={true}
                        trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
                      />
                    </View>
                    
                    <View style={styles.configRow}>
                      <Text style={styles.configLabel}>Verbose logging</Text>
                      <Switch
                        value={false}
                        trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
                      />
                    </View>
                  </View>

                  <View style={styles.configSection}>
                    <Text style={styles.configTitle}>Performance</Text>
                    
                    <View style={styles.inputGroup}>
                      <Text style={styles.inputLabel}>Request Timeout (seconds)</Text>
                      <TextInput
                        style={styles.textInput}
                        value="30"
                        keyboardType="numeric"
                        placeholderTextColor={theme.colors.textSecondary}
                      />
                    </View>
                    
                    <View style={styles.inputGroup}>
                      <Text style={styles.inputLabel}>Retry Attempts</Text>
                      <TextInput
                        style={styles.textInput}
                        value="3"
                        keyboardType="numeric"
                        placeholderTextColor={theme.colors.textSecondary}
                      />
                    </View>
                  </View>

                  <View style={styles.configSection}>
                    <Text style={styles.configTitle}>Fallback Order</Text>
                    <Text style={styles.configDescription}>
                      Providers are used in order of priority when the primary provider fails
                    </Text>
                    
                    {providers
                      .sort((a, b) => b.priority - a.priority)
                      .map((provider, index) => {
                        const info = providerInfo[provider.provider] || providerInfo.custom;
                        return (
                          <View key={provider.provider} style={styles.fallbackItem}>
                            <Text style={styles.fallbackRank}>{index + 1}</Text>
                            <View style={[styles.fallbackLogo, { backgroundColor: info.color + '20' }]}>
                              <Text style={styles.fallbackEmoji}>{info.logo}</Text>
                            </View>
                            <View style={styles.fallbackDetails}>
                              <Text style={styles.fallbackName}>{provider.provider.toUpperCase()}</Text>
                              <Text style={styles.fallbackPriority}>Priority: {provider.priority}</Text>
                            </View>
                          </View>
                        );
                      })}
                  </View>
                </ScrollView>
              )}
            </View>
          </View>
        </View>
      </Modal>

      {/* Configuration Modal */}
      <Modal
        visible={showConfigModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowConfigModal(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>
                Configure {editConfig.provider.toUpperCase()}
              </Text>
              <TouchableOpacity onPress={() => setShowConfigModal(false)}>
                <Icon name="close" size={24} color={theme.colors.text} />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.configForm} showsVerticalScrollIndicator={false}>
              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Provider</Text>
                <View style={styles.pickerContainer}>
                  {Object.entries(providerInfo).map(([key, info]) => (
                    <TouchableOpacity
                      key={key}
                      style={[
                        styles.providerOption,
                        editConfig.provider === key && styles.selectedProviderOption,
                      ]}
                      onPress={() => setEditConfig({ ...editConfig, provider: key })}
                    >
                      <Text style={styles.providerOptionEmoji}>{info.logo}</Text>
                      <Text style={styles.providerOptionText}>{key.toUpperCase()}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>API Key *</Text>
                <TextInput
                  style={styles.textInput}
                  value={editConfig.api_key || ''}
                  onChangeText={(text) => setEditConfig({ ...editConfig, api_key: text })}
                  placeholder="Enter your API key"
                  secureTextEntry
                  placeholderTextColor={theme.colors.textSecondary}
                />
              </View>

              {editConfig.provider === 'custom' && (
                <View style={styles.inputGroup}>
                  <Text style={styles.inputLabel}>API Endpoint</Text>
                  <TextInput
                    style={styles.textInput}
                    value={editConfig.api_endpoint || ''}
                    onChangeText={(text) => setEditConfig({ ...editConfig, api_endpoint: text })}
                    placeholder="https://api.example.com/v1"
                    placeholderTextColor={theme.colors.textSecondary}
                  />
                </View>
              )}

              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Priority</Text>
                <TextInput
                  style={styles.textInput}
                  value={editConfig.priority.toString()}
                  onChangeText={(text) => setEditConfig({ ...editConfig, priority: parseInt(text) || 0 })}
                  placeholder="0"
                  keyboardType="numeric"
                  placeholderTextColor={theme.colors.textSecondary}
                />
                <Text style={styles.inputHelp}>Higher numbers have higher priority</Text>
              </View>

              <View style={styles.configRow}>
                <Text style={styles.configLabel}>Enable this provider</Text>
                <Switch
                  value={editConfig.enabled}
                  onValueChange={(value) => setEditConfig({ ...editConfig, enabled: value })}
                  trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
                />
              </View>

              <Text style={styles.sectionTitle}>Model Mappings</Text>
              {modelTypes.map((type) => (
                <View key={type} style={styles.inputGroup}>
                  <Text style={styles.inputLabel}>{type.charAt(0).toUpperCase() + type.slice(1)}</Text>
                  <TextInput
                    style={styles.textInput}
                    value={editConfig.model_mappings[type] || ''}
                    onChangeText={(text) => setEditConfig({
                      ...editConfig,
                      model_mappings: {
                        ...editConfig.model_mappings,
                        [type]: text
                      }
                    })}
                    placeholder={`Model for ${type} tasks`}
                    placeholderTextColor={theme.colors.textSecondary}
                  />
                </View>
              ))}

              <View style={styles.buttonRow}>
                <TouchableOpacity
                  style={styles.testButton}
                  onPress={() => testProvider(editConfig.provider)}
                >
                  <Icon name="play-arrow" size={16} color="#fff" />
                  <Text style={styles.testButtonText}>Test</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.saveButton}
                  onPress={saveConfiguration}
                >
                  <Text style={styles.saveButtonText}>Save</Text>
                </TouchableOpacity>
              </View>
            </ScrollView>
          </View>
        </View>
      </Modal>

      {/* Test Results Modal */}
      <Modal
        visible={showTestModal}
        animationType="fade"
        transparent={true}
        onRequestClose={() => setShowTestModal(false)}
      >
        <View style={styles.testModalContainer}>
          <View style={styles.testModalContent}>
            <View style={styles.testHeader}>
              <Text style={styles.testTitle}>Test Results</Text>
              <TouchableOpacity onPress={() => setShowTestModal(false)}>
                <Icon name="close" size={24} color={theme.colors.text} />
              </TouchableOpacity>
            </View>
            {testResults && (
              <View style={styles.testResultsContainer}>
                <View style={[
                  styles.testResultStatus,
                  { backgroundColor: testResults.success ? theme.colors.success : theme.colors.error }
                ]}>
                  <Icon 
                    name={testResults.success ? "check-circle" : "error"} 
                    size={24} 
                    color="#fff" 
                  />
                  <Text style={styles.testResultText}>
                    {testResults.success ? "Connection Successful" : "Test Failed"}
                  </Text>
                </View>
                {testResults.success && (
                  <View style={styles.testMetrics}>
                    <Text style={styles.testMetric}>
                      Response Time: {testResults.response_time.toFixed(3)}s
                    </Text>
                    {testResults.model_info && (
                      <Text style={styles.testMetric}>
                        Model: {testResults.model_info.model}
                      </Text>
                    )}
                  </View>
                )}
                {testResults.error && (
                  <Text style={styles.errorText}>{testResults.error}</Text>
                )}
              </View>
            )}
          </View>
        </View>
      </Modal>
    </>
  );
};

const styles = StyleSheet.create({
  mainButton: {
    backgroundColor: theme.colors.surface,
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 8,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderWidth: 1,
    borderColor: theme.colors.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  mainButtonActive: {
    borderColor: theme.colors.primary,
    backgroundColor: theme.colors.primary + '10',
  },
  buttonContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  buttonEmoji: {
    fontSize: 24,
    marginRight: 12,
  },
  buttonText: {
    flex: 1,
  },
  buttonLabel: {
    fontSize: 12,
    color: theme.colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  buttonValue: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.text,
    marginTop: 2,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: theme.colors.background,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    height: '90%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: theme.colors.text,
  },
  headerActions: {
    flexDirection: 'row',
    gap: 8,
  },
  headerButton: {
    padding: 8,
  },
  tabs: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  tab: {
    flex: 1,
    paddingVertical: 16,
    alignItems: 'center',
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: theme.colors.primary,
  },
  tabText: {
    fontSize: 14,
    color: theme.colors.textSecondary,
    fontWeight: '500',
  },
  activeTabText: {
    color: theme.colors.primary,
    fontWeight: '600',
  },
  tabContent: {
    flex: 1,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  emptyText: {
    fontSize: 18,
    color: theme.colors.textSecondary,
    marginBottom: 8,
    textAlign: 'center',
  },
  emptySubtext: {
    fontSize: 14,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    marginBottom: 24,
  },
  addButton: {
    backgroundColor: theme.colors.primary,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    gap: 8,
  },
  addButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  providersList: {
    padding: 16,
  },
  providerCard: {
    backgroundColor: theme.colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  activeProviderCard: {
    borderColor: theme.colors.primary,
    backgroundColor: theme.colors.primary + '08',
  },
  providerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  providerInfo: {
    flexDirection: 'row',
    flex: 1,
  },
  providerLogo: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  providerEmoji: {
    fontSize: 24,
  },
  providerDetails: {
    flex: 1,
  },
  providerTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  providerName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: theme.colors.text,
    marginRight: 8,
  },
  activeBadge: {
    backgroundColor: theme.colors.primary,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 10,
    gap: 4,
  },
  activeBadgeText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  providerDescription: {
    fontSize: 13,
    color: theme.colors.textSecondary,
    marginBottom: 6,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '500',
    textTransform: 'capitalize',
  },
  priorityText: {
    fontSize: 12,
    color: theme.colors.textSecondary,
  },
  providerActions: {
    flexDirection: 'row',
    gap: 8,
  },
  actionButton: {
    padding: 8,
    borderRadius: 8,
    backgroundColor: theme.colors.background,
  },
  providerMetrics: {
    marginBottom: 12,
  },
  healthScore: {
    marginBottom: 12,
  },
  metricLabel: {
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginBottom: 4,
  },
  healthBar: {
    height: 6,
    backgroundColor: theme.colors.border,
    borderRadius: 3,
    overflow: 'hidden',
    marginBottom: 4,
  },
  healthBarFill: {
    height: '100%',
  },
  healthText: {
    fontSize: 12,
    fontWeight: '500',
    color: theme.colors.text,
  },
  quickStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: theme.colors.text,
  },
  statLabel: {
    fontSize: 10,
    color: theme.colors.textSecondary,
    marginTop: 2,
  },
  switchButton: {
    backgroundColor: theme.colors.primary,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderRadius: 8,
    gap: 8,
  },
  switchButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  statsContainer: {
    flex: 1,
    padding: 16,
  },
  summaryCard: {
    backgroundColor: theme.colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  summaryTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: theme.colors.text,
    marginBottom: 12,
  },
  summaryMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  summaryItem: {
    alignItems: 'center',
  },
  summaryNumber: {
    fontSize: 20,
    fontWeight: 'bold',
    color: theme.colors.text,
  },
  summaryLabel: {
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginTop: 4,
  },
  statsCard: {
    backgroundColor: theme.colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  statsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  statsLogo: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  statsEmoji: {
    fontSize: 16,
  },
  statsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: theme.colors.text,
  },
  statsMetrics: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 16,
  },
  metricCard: {
    width: '48%',
    backgroundColor: theme.colors.background,
    padding: 12,
    borderRadius: 8,
    margin: '1%',
    alignItems: 'center',
  },
  metricNumber: {
    fontSize: 18,
    fontWeight: 'bold',
    color: theme.colors.text,
  },
  chartTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.text,
    marginBottom: 8,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 8,
  },
  configContainer: {
    flex: 1,
    padding: 16,
  },
  configSection: {
    marginBottom: 24,
  },
  configTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: theme.colors.text,
    marginBottom: 12,
  },
  configDescription: {
    fontSize: 13,
    color: theme.colors.textSecondary,
    marginBottom: 12,
  },
  configRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  configLabel: {
    fontSize: 14,
    color: theme.colors.text,
  },
  inputGroup: {
    marginBottom: 16,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: theme.colors.text,
    marginBottom: 8,
  },
  inputHelp: {
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginTop: 4,
  },
  textInput: {
    backgroundColor: theme.colors.background,
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    color: theme.colors.text,
  },
  fallbackItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: theme.colors.background,
    borderRadius: 8,
    marginBottom: 8,
  },
  fallbackRank: {
    fontSize: 18,
    fontWeight: 'bold',
    color: theme.colors.primary,
    width: 32,
    textAlign: 'center',
  },
  fallbackLogo: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 12,
  },
  fallbackEmoji: {
    fontSize: 16,
  },
  fallbackDetails: {
    flex: 1,
  },
  fallbackName: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.text,
  },
  fallbackPriority: {
    fontSize: 12,
    color: theme.colors.textSecondary,
  },
  configForm: {
    flex: 1,
    padding: 16,
  },
  pickerContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  providerOption: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.colors.background,
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: 8,
    padding: 8,
    minWidth: 80,
  },
  selectedProviderOption: {
    borderColor: theme.colors.primary,
    backgroundColor: theme.colors.primary + '10',
  },
  providerOptionEmoji: {
    fontSize: 16,
    marginRight: 4,
  },
  providerOptionText: {
    fontSize: 12,
    fontWeight: '500',
    color: theme.colors.text,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.text,
    marginTop: 16,
    marginBottom: 12,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 24,
  },
  testButton: {
    backgroundColor: theme.colors.secondary,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    gap: 8,
  },
  testButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  saveButton: {
    flex: 1,
    backgroundColor: theme.colors.primary,
    alignItems: 'center',
    paddingVertical: 12,
    borderRadius: 8,
  },
  saveButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 16,
  },
  testModalContainer: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  testModalContent: {
    backgroundColor: theme.colors.background,
    borderRadius: 16,
    margin: 32,
    maxWidth: screenWidth - 64,
  },
  testHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  testTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: theme.colors.text,
  },
  testResultsContainer: {
    padding: 20,
  },
  testResultStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 8,
    marginBottom: 12,
    gap: 12,
  },
  testResultText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 16,
  },
  testMetrics: {
    backgroundColor: theme.colors.surface,
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
  },
  testMetric: {
    fontSize: 14,
    color: theme.colors.text,
    marginBottom: 4,
  },
  errorText: {
    fontSize: 14,
    color: theme.colors.error,
    fontStyle: 'italic',
  },
});

export default LLMProviderSelect;