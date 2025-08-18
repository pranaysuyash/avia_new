import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Modal,
  RefreshControl,
  ActivityIndicator,
  Dimensions,
  Platform
} from 'react-native';
import {
  Card,
  Button,
  Chip,
  ProgressBar,
  Switch,
  TextInput,
  Portal,
  Dialog,
  Paragraph,
  Title,
  Subheading,
  Caption,
  Surface,
  FAB,
  Snackbar,
  List,
  Avatar,
  Badge,
  IconButton
} from 'react-native-paper';
import { LineChart, PieChart } from 'react-native-chart-kit';
import DocumentPicker from 'react-native-document-picker';
import { launchImageLibrary, launchCamera } from 'react-native-image-picker';
import AsyncStorage from '@react-native-async-storage/async-storage';

const { width: screenWidth } = Dimensions.get('window');

// Types (same as React component)
interface ContentAnalysis {
  media_type: string;
  file_size_mb: number;
  duration_seconds: number;
  complexity: string;
  quality_score: number;
  processing_requirements: string[];
  estimated_processing_time: number;
  resource_requirements: {
    cpu: number;
    memory: number;
    disk: number;
    gpu?: number;
  };
  content_features: Record<string, any>;
}

interface ProcessingRoute {
  route_id: string;
  name: string;
  description: string;
  media_types: string[];
  complexity_levels: string[];
  processing_steps: string[];
  strategy: string;
  mode: string;
  priority: string;
  estimated_duration: number;
  resource_cost: number;
  fallback_routes: string[];
}

interface ProcessingJob {
  job_id: string;
  status: string;
  progress: number;
  route: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  errors: string[];
  results: Record<string, any>;
  filename?: string;
}

interface PerformanceMetrics {
  total_jobs: number;
  successful_jobs: number;
  failed_jobs: number;
  average_processing_time: number;
  active_jobs: number;
  queued_jobs: number;
  available_routes: number;
  resource_utilization: number;
}

const ProcessingRouterWorkflowEngineMobile: React.FC = () => {
  // State management
  const [activeTab, setActiveTab] = useState<'process' | 'monitor' | 'routes' | 'analytics'>('process');
  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [contentAnalysis, setContentAnalysis] = useState<ContentAnalysis | null>(null);
  const [processingRoutes, setProcessingRoutes] = useState<ProcessingRoute[]>([]);
  const [activeJobs, setActiveJobs] = useState<ProcessingJob[]>([]);
  const [jobHistory, setJobHistory] = useState<ProcessingJob[]>([]);
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics | null>(null);
  const [selectedRoute, setSelectedRoute] = useState<string>('auto');
  const [priority, setPriority] = useState<string>('normal');
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [snackbarVisible, setSnackbarVisible] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [jobDetailsVisible, setJobDetailsVisible] = useState(false);
  const [selectedJobDetails, setSelectedJobDetails] = useState<ProcessingJob | null>(null);
  const [routeSelectionVisible, setRouteSelectionVisible] = useState(false);

  // File selection handling
  const selectFile = useCallback(() => {
    Alert.alert(
      'Select Media File',
      'Choose how you want to select your media file',
      [
        { text: 'Camera', onPress: selectFromCamera },
        { text: 'Gallery', onPress: selectFromGallery },
        { text: 'Documents', onPress: selectFromDocuments },
        { text: 'Cancel', style: 'cancel' }
      ]
    );
  }, []);

  const selectFromCamera = useCallback(() => {
    launchCamera(
      {
        mediaType: 'mixed',
        quality: 0.8,
      },
      (response) => {
        if (response.assets && response.assets[0]) {
          const asset = response.assets[0];
          setSelectedFile({
            uri: asset.uri,
            name: asset.fileName || 'camera_capture',
            type: asset.type,
            size: asset.fileSize
          });
          analyzeContent(asset);
        }
      }
    );
  }, []);

  const selectFromGallery = useCallback(() => {
    launchImageLibrary(
      {
        mediaType: 'mixed',
        quality: 0.8,
      },
      (response) => {
        if (response.assets && response.assets[0]) {
          const asset = response.assets[0];
          setSelectedFile({
            uri: asset.uri,
            name: asset.fileName || 'gallery_selection',
            type: asset.type,
            size: asset.fileSize
          });
          analyzeContent(asset);
        }
      }
    );
  }, []);

  const selectFromDocuments = useCallback(async () => {
    try {
      const result = await DocumentPicker.pick({
        type: [
          DocumentPicker.types.audio,
          DocumentPicker.types.video,
          DocumentPicker.types.images,
          DocumentPicker.types.pdf
        ],
      });

      if (result && result[0]) {
        const file = result[0];
        setSelectedFile(file);
        analyzeContent(file);
      }
    } catch (err) {
      if (!DocumentPicker.isCancel(err)) {
        showSnackbar('Failed to select file');
      }
    }
  }, []);

  // API calls
  const analyzeContent = async (file: any) => {
    setAnalyzing(true);
    try {
      const formData = new FormData();
      formData.append('file', {
        uri: file.uri,
        name: file.name,
        type: file.type
      } as any);

      const response = await fetch('/api/v1/processing/analyze', {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.ok) {
        const analysis = await response.json();
        setContentAnalysis(analysis);
      } else {
        throw new Error('Analysis failed');
      }
    } catch (error) {
      showSnackbar('Content analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const startProcessing = async () => {
    if (!selectedFile) return;

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', {
        uri: selectedFile.uri,
        name: selectedFile.name,
        type: selectedFile.type
      } as any);
      formData.append('priority', priority);
      if (selectedRoute !== 'auto') {
        formData.append('custom_route', selectedRoute);
      }

      const response = await fetch('/api/v1/processing/process', {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.ok) {
        const result = await response.json();
        showSnackbar(`Processing started! Job ID: ${result.job_id.substring(0, 8)}`);
        setActiveTab('monitor');
        fetchActiveJobs();
      } else {
        throw new Error('Processing failed to start');
      }
    } catch (error) {
      showSnackbar('Failed to start processing');
    } finally {
      setLoading(false);
    }
  };

  const fetchProcessingRoutes = async () => {
    try {
      const response = await fetch('/api/v1/processing/routes');
      if (response.ok) {
        const routes = await response.json();
        setProcessingRoutes(routes);
      }
    } catch (error) {
      console.error('Failed to fetch routes:', error);
    }
  };

  const fetchActiveJobs = async () => {
    try {
      const response = await fetch('/api/v1/processing/jobs?status=running,pending');
      if (response.ok) {
        const data = await response.json();
        setActiveJobs(data.jobs || []);
      }
    } catch (error) {
      console.error('Failed to fetch active jobs:', error);
    }
  };

  const fetchJobHistory = async () => {
    try {
      const response = await fetch('/api/v1/processing/jobs?status=completed,failed,cancelled&limit=20');
      if (response.ok) {
        const data = await response.json();
        setJobHistory(data.jobs || []);
      }
    } catch (error) {
      console.error('Failed to fetch job history:', error);
    }
  };

  const fetchPerformanceMetrics = async () => {
    try {
      const response = await fetch('/api/v1/processing/metrics');
      if (response.ok) {
        const metrics = await response.json();
        setPerformanceMetrics(metrics);
      }
    } catch (error) {
      console.error('Failed to fetch performance metrics:', error);
    }
  };

  const cancelJob = async (jobId: string) => {
    try {
      const response = await fetch(`/api/v1/processing/jobs/${jobId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        showSnackbar('Job cancelled successfully');
        fetchActiveJobs();
      }
    } catch (error) {
      showSnackbar('Failed to cancel job');
    }
  };

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await Promise.all([
      fetchActiveJobs(),
      fetchJobHistory(),
      fetchPerformanceMetrics(),
      fetchProcessingRoutes()
    ]);
    setRefreshing(false);
  }, []);

  // Effects
  useEffect(() => {
    fetchProcessingRoutes();
    fetchActiveJobs();
    fetchJobHistory();
    fetchPerformanceMetrics();
  }, []);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (autoRefresh && activeTab === 'monitor') {
      interval = setInterval(() => {
        fetchActiveJobs();
        fetchPerformanceMetrics();
      }, 3000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh, activeTab]);

  // Helper functions
  const showSnackbar = (message: string) => {
    setSnackbarMessage(message);
    setSnackbarVisible(true);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#4caf50';
      case 'failed': return '#f44336';
      case 'running': return '#2196f3';
      case 'pending': return '#ff9800';
      case 'cancelled': return '#9e9e9e';
      default: return '#9e9e9e';
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatFileSize = (bytes: number) => {
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  };

  // Tab content components
  const ProcessMediaTab = () => (
    <ScrollView style={styles.tabContent} refreshControl={
      <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
    }>
      <Card style={styles.card}>
        <Card.Content>
          <Title>Upload Media File</Title>
          
          {selectedFile ? (
            <View style={styles.fileInfo}>
              <Text style={styles.fileName}>{selectedFile.name}</Text>
              <Caption>{formatFileSize(selectedFile.size || 0)}</Caption>
            </View>
          ) : (
            <Paragraph>No file selected</Paragraph>
          )}

          <Button
            mode="outlined"
            onPress={selectFile}
            style={styles.button}
            icon="file-upload"
          >
            Select Media File
          </Button>

          {selectedFile && (
            <View style={styles.processingOptions}>
              <Subheading>Processing Options</Subheading>
              
              <View style={styles.optionRow}>
                <Text>Priority:</Text>
                <Button
                  mode="outlined"
                  onPress={() => {
                    Alert.alert(
                      'Select Priority',
                      '',
                      [
                        { text: 'Low', onPress: () => setPriority('low') },
                        { text: 'Normal', onPress: () => setPriority('normal') },
                        { text: 'High', onPress: () => setPriority('high') },
                        { text: 'Critical', onPress: () => setPriority('critical') }
                      ]
                    );
                  }}
                  compact
                >
                  {priority.toUpperCase()}
                </Button>
              </View>

              <View style={styles.optionRow}>
                <Text>Route:</Text>
                <Button
                  mode="outlined"
                  onPress={() => setRouteSelectionVisible(true)}
                  compact
                >
                  {selectedRoute === 'auto' ? 'Auto-select' : 
                   processingRoutes.find(r => r.route_id === selectedRoute)?.name || 'Unknown'}
                </Button>
              </View>

              <Button
                mode="contained"
                onPress={startProcessing}
                loading={loading}
                disabled={loading}
                style={styles.button}
                icon="play"
              >
                {loading ? 'Starting...' : 'Start Processing'}
              </Button>
            </View>
          )}
        </Card.Content>
      </Card>

      {analyzing && (
        <Card style={styles.card}>
          <Card.Content>
            <View style={styles.analyzingContainer}>
              <ActivityIndicator size="small" />
              <Text style={styles.analyzingText}>Analyzing content...</Text>
            </View>
          </Card.Content>
        </Card>
      )}

      {contentAnalysis && (
        <Card style={styles.card}>
          <Card.Content>
            <Title>Content Analysis</Title>
            
            <View style={styles.analysisGrid}>
              <View style={styles.analysisItem}>
                <Caption>Media Type</Caption>
                <Text style={styles.analysisValue}>{contentAnalysis.media_type.toUpperCase()}</Text>
              </View>
              
              <View style={styles.analysisItem}>
                <Caption>Complexity</Caption>
                <Text style={styles.analysisValue}>{contentAnalysis.complexity.toUpperCase()}</Text>
              </View>
              
              <View style={styles.analysisItem}>
                <Caption>Quality Score</Caption>
                <Text style={styles.analysisValue}>{contentAnalysis.quality_score.toFixed(2)}</Text>
              </View>
              
              <View style={styles.analysisItem}>
                <Caption>Est. Processing Time</Caption>
                <Text style={styles.analysisValue}>
                  {formatDuration(contentAnalysis.estimated_processing_time)}
                </Text>
              </View>
            </View>

            <Subheading style={styles.sectionTitle}>Processing Requirements</Subheading>
            <View style={styles.chipContainer}>
              {contentAnalysis.processing_requirements.map((req, index) => (
                <Chip key={index} style={styles.chip}>
                  {req.replace('_', ' ')}
                </Chip>
              ))}
            </View>

            <Subheading style={styles.sectionTitle}>Resource Requirements</Subheading>
            <Text>CPU: {contentAnalysis.resource_requirements.cpu} cores</Text>
            <Text>Memory: {contentAnalysis.resource_requirements.memory} MB</Text>
            <Text>Disk: {contentAnalysis.resource_requirements.disk} MB</Text>
          </Card.Content>
        </Card>
      )}
    </ScrollView>
  );

  const JobMonitorTab = () => (
    <ScrollView style={styles.tabContent} refreshControl={
      <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
    }>
      <Card style={styles.card}>
        <Card.Content>
          <View style={styles.monitorHeader}>
            <Title>Job Monitor</Title>
            <View style={styles.autoRefreshContainer}>
              <Text>Auto Refresh</Text>
              <Switch
                value={autoRefresh}
                onValueChange={setAutoRefresh}
              />
            </View>
          </View>
        </Card.Content>
      </Card>

      <Card style={styles.card}>
        <Card.Content>
          <Subheading>Active Jobs ({activeJobs.length})</Subheading>
          
          {activeJobs.length > 0 ? (
            activeJobs.map((job) => (
              <Surface key={job.job_id} style={styles.jobCard}>
                <View style={styles.jobHeader}>
                  <View style={styles.jobInfo}>
                    <Text style={styles.jobTitle}>
                      {job.filename || `Job ${job.job_id.substring(0, 8)}`}
                    </Text>
                    <Caption>Route: {job.route}</Caption>
                  </View>
                  
                  <View style={styles.jobActions}>
                    <Chip
                      style={[styles.statusChip, { backgroundColor: getStatusColor(job.status) }]}
                      textStyle={{ color: 'white' }}
                    >
                      {job.status.toUpperCase()}
                    </Chip>
                  </View>
                </View>
                
                <View style={styles.progressContainer}>
                  <ProgressBar
                    progress={job.progress}
                    color={getStatusColor(job.status)}
                    style={styles.progressBar}
                  />
                  <Text style={styles.progressText}>{(job.progress * 100).toFixed(1)}%</Text>
                </View>
                
                <View style={styles.jobFooter}>
                  <Button
                    mode="outlined"
                    onPress={() => {
                      setSelectedJobDetails(job);
                      setJobDetailsVisible(true);
                    }}
                    compact
                  >
                    Details
                  </Button>
                  
                  {job.status === 'running' && (
                    <Button
                      mode="outlined"
                      onPress={() => {
                        Alert.alert(
                          'Cancel Job',
                          'Are you sure you want to cancel this job?',
                          [
                            { text: 'No', style: 'cancel' },
                            { text: 'Yes', onPress: () => cancelJob(job.job_id) }
                          ]
                        );
                      }}
                      compact
                      buttonColor="#f44336"
                    >
                      Cancel
                    </Button>
                  )}
                </View>
              </Surface>
            ))
          ) : (
            <Text style={styles.emptyText}>No active jobs</Text>
          )}
        </Card.Content>
      </Card>

      <Card style={styles.card}>
        <Card.Content>
          <Subheading>Recent Jobs</Subheading>
          
          {jobHistory.slice(0, 10).map((job) => (
            <List.Item
              key={job.job_id}
              title={job.filename || `Job ${job.job_id.substring(0, 8)}`}
              description={`${job.status} • ${job.route}`}
              left={() => (
                <Avatar.Icon
                  size={40}
                  icon={job.status === 'completed' ? 'check' : 
                        job.status === 'failed' ? 'close' : 'clock'}
                  style={{ backgroundColor: getStatusColor(job.status) }}
                />
              )}
              right={() => (
                <IconButton
                  icon="eye"
                  onPress={() => {
                    setSelectedJobDetails(job);
                    setJobDetailsVisible(true);
                  }}
                />
              )}
            />
          ))}
        </Card.Content>
      </Card>
    </ScrollView>
  );

  const RoutesTab = () => (
    <ScrollView style={styles.tabContent} refreshControl={
      <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
    }>
      <Card style={styles.card}>
        <Card.Content>
          <Title>Processing Routes ({processingRoutes.length})</Title>
        </Card.Content>
      </Card>

      {processingRoutes.map((route) => (
        <Card key={route.route_id} style={styles.card}>
          <Card.Content>
            <Title>{route.name}</Title>
            <Paragraph>{route.description}</Paragraph>
            
            <View style={styles.chipContainer}>
              <Chip style={styles.chip}>{route.strategy.toUpperCase()}</Chip>
              <Chip style={styles.chip}>{route.mode.toUpperCase()}</Chip>
              <Chip style={styles.chip}>{route.priority.toUpperCase()}</Chip>
            </View>
            
            <View style={styles.routeDetails}>
              <Text><Text style={styles.bold}>Media Types:</Text> {route.media_types.join(', ')}</Text>
              <Text><Text style={styles.bold}>Complexity:</Text> {route.complexity_levels.join(', ')}</Text>
              <Text><Text style={styles.bold}>Duration:</Text> {formatDuration(route.estimated_duration)}</Text>
              <Text><Text style={styles.bold}>Resource Cost:</Text> {route.resource_cost}</Text>
            </View>
            
            <Subheading style={styles.sectionTitle}>Processing Steps</Subheading>
            {route.processing_steps.map((step, index) => (
              <Text key={index} style={styles.stepText}>
                {index + 1}. {step.replace('_', ' ')}
              </Text>
            ))}
            
            {route.fallback_routes.length > 0 && (
              <>
                <Subheading style={styles.sectionTitle}>Fallback Routes</Subheading>
                <View style={styles.chipContainer}>
                  {route.fallback_routes.map((fallback, index) => (
                    <Chip key={index} style={styles.chip} mode="outlined">
                      {fallback}
                    </Chip>
                  ))}
                </View>
              </>
            )}
          </Card.Content>
        </Card>
      ))}
    </ScrollView>
  );

  const AnalyticsTab = () => {
    if (!performanceMetrics) {
      return (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" />
          <Text>Loading analytics...</Text>
        </View>
      );
    }

    const successRate = performanceMetrics.total_jobs > 0 
      ? (performanceMetrics.successful_jobs / performanceMetrics.total_jobs) * 100 
      : 0;

    const pieData = [
      {
        name: 'Successful',
        population: performanceMetrics.successful_jobs,
        color: '#4caf50',
        legendFontColor: '#7F7F7F',
        legendFontSize: 15,
      },
      {
        name: 'Failed',
        population: performanceMetrics.failed_jobs,
        color: '#f44336',
        legendFontColor: '#7F7F7F',
        legendFontSize: 15,
      },
    ];

    return (
      <ScrollView style={styles.tabContent} refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }>
        <Card style={styles.card}>
          <Card.Content>
            <Title>Performance Analytics</Title>
          </Card.Content>
        </Card>

        <View style={styles.metricsGrid}>
          <Card style={styles.metricCard}>
            <Card.Content>
              <Text style={styles.metricValue}>{performanceMetrics.total_jobs}</Text>
              <Caption>Total Jobs</Caption>
            </Card.Content>
          </Card>
          
          <Card style={styles.metricCard}>
            <Card.Content>
              <Text style={[styles.metricValue, { color: '#4caf50' }]}>
                {successRate.toFixed(1)}%
              </Text>
              <Caption>Success Rate</Caption>
            </Card.Content>
          </Card>
          
          <Card style={styles.metricCard}>
            <Card.Content>
              <Text style={[styles.metricValue, { color: '#2196f3' }]}>
                {formatDuration(performanceMetrics.average_processing_time)}
              </Text>
              <Caption>Avg Time</Caption>
            </Card.Content>
          </Card>
          
          <Card style={styles.metricCard}>
            <Card.Content>
              <Text style={[styles.metricValue, { color: '#ff9800' }]}>
                {performanceMetrics.active_jobs}
              </Text>
              <Caption>Active Jobs</Caption>
            </Card.Content>
          </Card>
        </View>

        {performanceMetrics.total_jobs > 0 && (
          <Card style={styles.card}>
            <Card.Content>
              <Subheading>Job Success Rate</Subheading>
              <PieChart
                data={pieData}
                width={screenWidth - 60}
                height={220}
                chartConfig={{
                  backgroundColor: '#ffffff',
                  backgroundGradientFrom: '#ffffff',
                  backgroundGradientTo: '#ffffff',
                  color: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                }}
                accessor="population"
                backgroundColor="transparent"
                paddingLeft="15"
                absolute
              />
            </Card.Content>
          </Card>
        )}

        <Card style={styles.card}>
          <Card.Content>
            <Subheading>System Resources</Subheading>
            <View style={styles.resourceInfo}>
              <Text>Available Routes: {performanceMetrics.available_routes}</Text>
              <Text>Queued Jobs: {performanceMetrics.queued_jobs}</Text>
              <Text>Resource Utilization: {performanceMetrics.resource_utilization}%</Text>
              <ProgressBar
                progress={performanceMetrics.resource_utilization / 100}
                color="#2196f3"
                style={styles.resourceProgressBar}
              />
            </View>
          </Card.Content>
        </Card>
      </ScrollView>
    );
  };

  return (
    <View style={styles.container}>
      {/* Tab Navigation */}
      <Surface style={styles.tabBar}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'process' && styles.activeTab]}
          onPress={() => setActiveTab('process')}
        >
          <Text style={[styles.tabText, activeTab === 'process' && styles.activeTabText]}>
            Process
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.tab, activeTab === 'monitor' && styles.activeTab]}
          onPress={() => setActiveTab('monitor')}
        >
          <Text style={[styles.tabText, activeTab === 'monitor' && styles.activeTabText]}>
            Monitor
          </Text>
          {activeJobs.length > 0 && (
            <Badge style={styles.badge}>{activeJobs.length}</Badge>
          )}
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.tab, activeTab === 'routes' && styles.activeTab]}
          onPress={() => setActiveTab('routes')}
        >
          <Text style={[styles.tabText, activeTab === 'routes' && styles.activeTabText]}>
            Routes
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.tab, activeTab === 'analytics' && styles.activeTab]}
          onPress={() => setActiveTab('analytics')}
        >
          <Text style={[styles.tabText, activeTab === 'analytics' && styles.activeTabText]}>
            Analytics
          </Text>
        </TouchableOpacity>
      </Surface>

      {/* Tab Content */}
      {activeTab === 'process' && <ProcessMediaTab />}
      {activeTab === 'monitor' && <JobMonitorTab />}
      {activeTab === 'routes' && <RoutesTab />}
      {activeTab === 'analytics' && <AnalyticsTab />}

      {/* Route Selection Dialog */}
      <Portal>
        <Dialog visible={routeSelectionVisible} onDismiss={() => setRouteSelectionVisible(false)}>
          <Dialog.Title>Select Processing Route</Dialog.Title>
          <Dialog.Content>
            <TouchableOpacity
              style={styles.routeOption}
              onPress={() => {
                setSelectedRoute('auto');
                setRouteSelectionVisible(false);
              }}
            >
              <Text style={selectedRoute === 'auto' ? styles.selectedRouteText : styles.routeText}>
                Auto-select (Recommended)
              </Text>
            </TouchableOpacity>
            
            {processingRoutes.map((route) => (
              <TouchableOpacity
                key={route.route_id}
                style={styles.routeOption}
                onPress={() => {
                  setSelectedRoute(route.route_id);
                  setRouteSelectionVisible(false);
                }}
              >
                <Text style={selectedRoute === route.route_id ? styles.selectedRouteText : styles.routeText}>
                  {route.name}
                </Text>
                <Caption>{route.description}</Caption>
              </TouchableOpacity>
            ))}
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setRouteSelectionVisible(false)}>Cancel</Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>

      {/* Job Details Dialog */}
      <Portal>
        <Dialog visible={jobDetailsVisible} onDismiss={() => setJobDetailsVisible(false)}>
          <Dialog.Title>
            Job Details: {selectedJobDetails?.job_id.substring(0, 8)}
          </Dialog.Title>
          <Dialog.Content>
            {selectedJobDetails && (
              <ScrollView>
                <Text><Text style={styles.bold}>Status:</Text> {selectedJobDetails.status}</Text>
                <Text><Text style={styles.bold}>Progress:</Text> {(selectedJobDetails.progress * 100).toFixed(1)}%</Text>
                <Text><Text style={styles.bold}>Route:</Text> {selectedJobDetails.route}</Text>
                <Text><Text style={styles.bold}>Created:</Text> {new Date(selectedJobDetails.created_at).toLocaleString()}</Text>
                
                {selectedJobDetails.errors.length > 0 && (
                  <>
                    <Subheading style={styles.sectionTitle}>Errors</Subheading>
                    {selectedJobDetails.errors.map((error, index) => (
                      <Text key={index} style={styles.errorText}>{error}</Text>
                    ))}
                  </>
                )}
                
                {Object.keys(selectedJobDetails.results).length > 0 && (
                  <>
                    <Subheading style={styles.sectionTitle}>Results</Subheading>
                    <Text style={styles.resultsText}>
                      {JSON.stringify(selectedJobDetails.results, null, 2)}
                    </Text>
                  </>
                )}
              </ScrollView>
            )}
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setJobDetailsVisible(false)}>Close</Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>

      {/* Snackbar */}
      <Snackbar
        visible={snackbarVisible}
        onDismiss={() => setSnackbarVisible(false)}
        duration={4000}
      >
        {snackbarMessage}
      </Snackbar>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  tabBar: {
    flexDirection: 'row',
    elevation: 4,
    backgroundColor: 'white',
  },
  tab: {
    flex: 1,
    paddingVertical: 16,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#2196f3',
  },
  tabText: {
    fontSize: 14,
    color: '#666',
  },
  activeTabText: {
    color: '#2196f3',
    fontWeight: 'bold',
  },
  badge: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: '#f44336',
  },
  tabContent: {
    flex: 1,
    padding: 16,
  },
  card: {
    marginBottom: 16,
    elevation: 2,
  },
  button: {
    marginTop: 16,
  },
  fileInfo: {
    marginVertical: 16,
    padding: 16,
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
  },
  fileName: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  processingOptions: {
    marginTop: 16,
  },
  optionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginVertical: 8,
  },
  analyzingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  analyzingText: {
    marginLeft: 8,
  },
  analysisGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  analysisItem: {
    width: '48%',
    marginBottom: 16,
  },
  analysisValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2196f3',
  },
  sectionTitle: {
    marginTop: 16,
    marginBottom: 8,
  },
  chipContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginVertical: 8,
  },
  chip: {
    marginRight: 8,
    marginBottom: 8,
  },
  monitorHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  autoRefreshContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  jobCard: {
    marginVertical: 8,
    padding: 16,
    borderRadius: 8,
    elevation: 1,
  },
  jobHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  jobInfo: {
    flex: 1,
  },
  jobTitle: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  jobActions: {
    alignItems: 'flex-end',
  },
  statusChip: {
    marginBottom: 8,
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  progressBar: {
    flex: 1,
    marginRight: 8,
  },
  progressText: {
    fontSize: 12,
    minWidth: 40,
    textAlign: 'right',
  },
  jobFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  emptyText: {
    textAlign: 'center',
    color: '#666',
    fontStyle: 'italic',
    marginVertical: 16,
  },
  routeDetails: {
    marginVertical: 8,
  },
  bold: {
    fontWeight: 'bold',
  },
  stepText: {
    marginLeft: 8,
    marginBottom: 4,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  metricCard: {
    width: '48%',
    marginBottom: 8,
  },
  metricValue: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  resourceInfo: {
    marginTop: 8,
  },
  resourceProgressBar: {
    marginTop: 8,
  },
  routeOption: {
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  routeText: {
    fontSize: 16,
  },
  selectedRouteText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2196f3',
  },
  errorText: {
    color: '#f44336',
    marginBottom: 4,
  },
  resultsText: {
    fontSize: 12,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
    backgroundColor: '#f5f5f5',
    padding: 8,
    borderRadius: 4,
  },
});

export default ProcessingRouterWorkflowEngineMobile;