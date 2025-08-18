import React, { useState, useCallback, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Dimensions,
  RefreshControl,
  Modal,
  FlatList
} from 'react-native';
import {
  Card,
  Button,
  Chip,
  ProgressBar,
  Title,
  Subheading,
  Caption,
  Surface,
  Portal,
  Dialog,
  Paragraph,
  List,
  Divider,
  IconButton,
  Switch,
  Menu,
  Provider as PaperProvider,
  Appbar,
  FAB,
  Snackbar
} from 'react-native-paper';
import DocumentPicker from 'react-native-document-picker';
import { launchImageLibrary } from 'react-native-image-picker';

const { width: screenWidth } = Dimensions.get('window');

// Types (same as React component)
interface VideoMetadata {
  duration: number;
  fps: number;
  width: number;
  height: number;
  total_frames: number;
  codec: string;
  bitrate?: number;
  file_size: number;
  aspect_ratio: string;
  has_audio: boolean;
  quality_score: number;
  complexity_score: number;
}

interface SceneInfo {
  start_time: number;
  end_time: number;
  start_frame: number;
  end_frame: number;
  confidence: number;
  scene_type: string;
  description: string;
  motion_intensity: number;
  visual_complexity: number;
}

interface KeyFrame {
  frame_number: number;
  timestamp: number;
  confidence: number;
  frame_path?: string;
  visual_hash: string;
  objects_detected: string[];
}

interface ObjectDetection {
  class_name: string;
  category: string;
  confidence: number;
  bbox: [number, number, number, number];
  timestamp: number;
  frame_number: number;
  tracking_id?: string;
}

interface BRollSuggestion {
  timestamp: number;
  duration: number;
  suggestion_type: string;
  description: string;
  confidence: number;
  keywords: string[];
  priority: number;
}

interface ProcessingResult {
  job_id: string;
  success: boolean;
  processing_time: number;
  processing_strategy: string;
  metadata: VideoMetadata;
  keyframes: KeyFrame[];
  scenes: SceneInfo[];
  objects: ObjectDetection[];
  broll_suggestions: BRollSuggestion[];
  errors: string[];
}

interface ProcessingJob {
  job_id: string;
  status: string;
  progress: number;
  message: string;
  started_at: string;
  completed_at?: string;
  result?: ProcessingResult;
}

const AdvancedVideoProcessingEngineMobile: React.FC = () => {
  // State management
  const [activeTab, setActiveTab] = useState<'upload' | 'results' | 'scenes' | 'broll' | 'jobs'>('upload');
  const [selectedVideo, setSelectedVideo] = useState<any>(null);
  const [processing, setProcessing] = useState(false);
  const [processingResult, setProcessingResult] = useState<ProcessingResult | null>(null);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [processingJobs, setProcessingJobs] = useState<ProcessingJob[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  // Processing options
  const [extractKeyframes, setExtractKeyframes] = useState(true);
  const [detectScenes, setDetectScenes] = useState(true);
  const [detectObjects, setDetectObjects] = useState(true);
  const [suggestBroll, setSuggestBroll] = useState(true);
  const [enhanceQuality, setEnhanceQuality] = useState(false);
  const [processingStrategy, setProcessingStrategy] = useState('auto');

  // UI state
  const [snackbarVisible, setSnackbarVisible] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [jobDetailsVisible, setJobDetailsVisible] = useState(false);
  const [selectedJob, setSelectedJob] = useState<ProcessingJob | null>(null);
  const [strategyMenuVisible, setStrategyMenuVisible] = useState(false);

  // Load processing jobs on component mount
  useEffect(() => {
    loadProcessingJobs();
  }, []);

  // Video selection
  const selectVideo = useCallback(() => {
    Alert.alert(
      'Select Video',
      'Choose how you want to select your video',
      [
        { text: 'Gallery', onPress: selectFromGallery },
        { text: 'Files', onPress: selectFromFiles },
        { text: 'Cancel', style: 'cancel' }
      ]
    );
  }, []);

  const selectFromGallery = useCallback(() => {
    launchImageLibrary(
      {
        mediaType: 'video',
        quality: 0.8,
      },
      (response) => {
        if (response.assets && response.assets[0]) {
          const asset = response.assets[0];
          setSelectedVideo({
            uri: asset.uri,
            name: asset.fileName || 'video_selection',
            type: asset.type,
            size: asset.fileSize
          });
        }
      }
    );
  }, []);

  const selectFromFiles = useCallback(async () => {
    try {
      const result = await DocumentPicker.pick({
        type: [DocumentPicker.types.video],
      });

      if (result && result[0]) {
        const file = result[0];
        setSelectedVideo(file);
      }
    } catch (err) {
      if (!DocumentPicker.isCancel(err)) {
        Alert.alert('Error', 'Failed to select video file');
      }
    }
  }, []);

  // Video processing
  const processVideo = async () => {
    if (!selectedVideo) return;

    setProcessing(true);
    try {
      const formData = new FormData();
      formData.append('video', {
        uri: selectedVideo.uri,
        name: selectedVideo.name,
        type: selectedVideo.type
      } as any);
      formData.append('extract_keyframes', extractKeyframes.toString());
      formData.append('detect_scenes', detectScenes.toString());
      formData.append('detect_objects', detectObjects.toString());
      formData.append('suggest_broll', suggestBroll.toString());
      formData.append('enhance_quality', enhanceQuality.toString());
      
      if (processingStrategy !== 'auto') {
        formData.append('processing_strategy', processingStrategy);
      }

      const response = await fetch('/api/v1/video/process', {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.status === 202) {
        const result = await response.json();
        setCurrentJobId(result.job_id);
        
        setSnackbarMessage(`Processing started! Job ID: ${result.job_id.substring(0, 8)}...`);
        setSnackbarVisible(true);

        // Start polling for status
        pollJobStatus(result.job_id);
        setActiveTab('jobs');
      } else {
        throw new Error('Video processing failed');
      }
    } catch (error) {
      Alert.alert('Error', 'Video processing failed');
    } finally {
      setProcessing(false);
    }
  };

  // Poll job status
  const pollJobStatus = async (jobId: string) => {
    const maxAttempts = 300; // 5 minutes max
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await fetch(`/api/v1/video/status/${jobId}`);
        if (response.ok) {
          const job: ProcessingJob = await response.json();
          
          // Update jobs list
          setProcessingJobs(prev => {
            const updated = prev.filter(j => j.job_id !== jobId);
            return [...updated, job];
          });

          if (job.status === 'completed') {
            // Get result
            const resultResponse = await fetch(`/api/v1/video/result/${jobId}`);
            if (resultResponse.ok) {
              const result = await resultResponse.json();
              setProcessingResult(result);
              setActiveTab('results');
              
              setSnackbarMessage('Video processing completed successfully!');
              setSnackbarVisible(true);
            }
            return;
          } else if (job.status === 'failed') {
            Alert.alert('Processing Failed', job.message);
            return;
          }

          // Continue polling if still processing
          if (job.status === 'processing' && attempts < maxAttempts) {
            attempts++;
            setTimeout(poll, 2000);
          }
        }
      } catch (error) {
        console.error('Status polling error:', error);
      }
    };

    poll();
  };

  // Load processing jobs
  const loadProcessingJobs = async () => {
    try {
      const response = await fetch('/api/v1/video/jobs');
      if (response.ok) {
        const jobs = await response.json();
        setProcessingJobs(jobs);
      }
    } catch (error) {
      console.error('Failed to load jobs:', error);
    }
  };

  // Refresh handler
  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadProcessingJobs();
    setRefreshing(false);
  }, []);

  // Helper functions
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatFileSize = (bytes: number) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#4CAF50';
      case 'failed': return '#F44336';
      case 'processing': return '#2196F3';
      default: return '#9E9E9E';
    }
  };

  // Tab content components
  const UploadTab = () => (
    <ScrollView style={styles.container}>
      <Card style={styles.card}>
        <Card.Content>
          <Title>Upload Video</Title>
          <Paragraph>Select a video file for advanced processing</Paragraph>
          
          {selectedVideo ? (
            <View style={styles.selectedVideo}>
              <Text style={styles.videoName}>{selectedVideo.name}</Text>
              <Text style={styles.videoSize}>
                {selectedVideo.size ? formatFileSize(selectedVideo.size) : 'Unknown size'}
              </Text>
            </View>
          ) : (
            <Surface style={styles.uploadArea}>
              <Text style={styles.uploadText}>No video selected</Text>
            </Surface>
          )}
          
          <Button
            mode="outlined"
            onPress={selectVideo}
            style={styles.selectButton}
            icon="video"
          >
            Select Video
          </Button>
        </Card.Content>
      </Card>

      <Card style={styles.card}>
        <Card.Content>
          <Title>Processing Options</Title>
          
          <View style={styles.optionRow}>
            <Text style={styles.optionLabel}>Extract Keyframes</Text>
            <Switch
              value={extractKeyframes}
              onValueChange={setExtractKeyframes}
            />
          </View>
          
          <View style={styles.optionRow}>
            <Text style={styles.optionLabel}>Detect Scenes</Text>
            <Switch
              value={detectScenes}
              onValueChange={setDetectScenes}
            />
          </View>
          
          <View style={styles.optionRow}>
            <Text style={styles.optionLabel}>Detect Objects</Text>
            <Switch
              value={detectObjects}
              onValueChange={setDetectObjects}
            />
          </View>
          
          <View style={styles.optionRow}>
            <Text style={styles.optionLabel}>B-roll Suggestions</Text>
            <Switch
              value={suggestBroll}
              onValueChange={setSuggestBroll}
            />
          </View>
          
          <View style={styles.optionRow}>
            <Text style={styles.optionLabel}>Enhance Quality</Text>
            <Switch
              value={enhanceQuality}
              onValueChange={setEnhanceQuality}
            />
          </View>

          <View style={styles.optionRow}>
            <Text style={styles.optionLabel}>Strategy: {processingStrategy}</Text>
            <Menu
              visible={strategyMenuVisible}
              onDismiss={() => setStrategyMenuVisible(false)}
              anchor={
                <IconButton
                  icon="chevron-down"
                  onPress={() => setStrategyMenuVisible(true)}
                />
              }
            >
              {['auto', 'basic', 'enhanced', 'professional', 'enterprise'].map((strategy) => (
                <Menu.Item
                  key={strategy}
                  onPress={() => {
                    setProcessingStrategy(strategy);
                    setStrategyMenuVisible(false);
                  }}
                  title={strategy.charAt(0).toUpperCase() + strategy.slice(1)}
                />
              ))}
            </Menu>
          </View>
        </Card.Content>
      </Card>

      {selectedVideo && (
        <Button
          mode="contained"
          onPress={processVideo}
          disabled={processing}
          loading={processing}
          style={styles.processButton}
          icon="play"
        >
          {processing ? 'Processing...' : 'Start Processing'}
        </Button>
      )}
    </ScrollView>
  );

  const ResultsTab = () => {
    if (!processingResult) {
      return (
        <View style={styles.centerContainer}>
          <Text style={styles.infoText}>
            No processing results available. Upload and process a video first.
          </Text>
        </View>
      );
    }

    return (
      <ScrollView style={styles.container}>
        {/* Summary Cards */}
        <View style={styles.summaryGrid}>
          <Surface style={styles.summaryCard}>
            <Text style={styles.summaryNumber}>
              {formatDuration(processingResult.processing_time)}
            </Text>
            <Text style={styles.summaryLabel}>Processing Time</Text>
          </Surface>
          
          <Surface style={styles.summaryCard}>
            <Text style={styles.summaryNumber}>
              {processingResult.keyframes.length}
            </Text>
            <Text style={styles.summaryLabel}>Keyframes</Text>
          </Surface>
          
          <Surface style={styles.summaryCard}>
            <Text style={styles.summaryNumber}>
              {processingResult.scenes.length}
            </Text>
            <Text style={styles.summaryLabel}>Scenes</Text>
          </Surface>
          
          <Surface style={styles.summaryCard}>
            <Text style={styles.summaryNumber}>
              {processingResult.objects.length}
            </Text>
            <Text style={styles.summaryLabel}>Objects</Text>
          </Surface>
        </View>

        {/* Video Information */}
        <Card style={styles.card}>
          <Card.Content>
            <Title>Video Information</Title>
            
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Duration:</Text>
              <Text style={styles.infoValue}>
                {formatDuration(processingResult.metadata.duration)}
              </Text>
            </View>
            
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Resolution:</Text>
              <Text style={styles.infoValue}>
                {processingResult.metadata.width}x{processingResult.metadata.height}
              </Text>
            </View>
            
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>FPS:</Text>
              <Text style={styles.infoValue}>
                {processingResult.metadata.fps.toFixed(2)}
              </Text>
            </View>
            
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>File Size:</Text>
              <Text style={styles.infoValue}>
                {formatFileSize(processingResult.metadata.file_size)}
              </Text>
            </View>
            
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Quality Score:</Text>
              <View style={styles.progressContainer}>
                <ProgressBar
                  progress={processingResult.metadata.quality_score}
                  color="#4CAF50"
                  style={styles.progressBar}
                />
                <Text style={styles.progressText}>
                  {(processingResult.metadata.quality_score * 100).toFixed(0)}%
                </Text>
              </View>
            </View>
            
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Strategy Used:</Text>
              <Chip mode="outlined">
                {processingResult.processing_strategy}
              </Chip>
            </View>
          </Card.Content>
        </Card>

        {/* Errors */}
        {processingResult.errors.length > 0 && (
          <Card style={[styles.card, styles.warningCard]}>
            <Card.Content>
              <Title>Processing Warnings</Title>
              {processingResult.errors.map((error, index) => (
                <Text key={index} style={styles.errorText}>
                  • {error}
                </Text>
              ))}
            </Card.Content>
          </Card>
        )}
      </ScrollView>
    );
  };

  const ScenesTab = () => {
    if (!processingResult || processingResult.scenes.length === 0) {
      return (
        <View style={styles.centerContainer}>
          <Text style={styles.infoText}>
            No scenes detected. Process a video to see scene analysis.
          </Text>
        </View>
      );
    }

    return (
      <ScrollView style={styles.container}>
        <Title style={styles.sectionTitle}>
          Scene Analysis ({processingResult.scenes.length} scenes)
        </Title>
        
        {processingResult.scenes.map((scene, index) => (
          <Card key={index} style={styles.card}>
            <Card.Content>
              <View style={styles.sceneHeader}>
                <Text style={styles.sceneTitle}>Scene {index + 1}</Text>
                <Chip mode="outlined" compact>
                  {scene.scene_type}
                </Chip>
              </View>
              
              <Text style={styles.sceneTime}>
                {formatDuration(scene.start_time)} - {formatDuration(scene.end_time)}
                ({formatDuration(scene.end_time - scene.start_time)})
              </Text>
              
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>Confidence:</Text>
                <View style={styles.progressContainer}>
                  <ProgressBar
                    progress={scene.confidence}
                    color="#2196F3"
                    style={styles.progressBar}
                  />
                  <Text style={styles.progressText}>
                    {(scene.confidence * 100).toFixed(0)}%
                  </Text>
                </View>
              </View>
              
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>Motion:</Text>
                <View style={styles.progressContainer}>
                  <ProgressBar
                    progress={scene.motion_intensity}
                    color="#FF9800"
                    style={styles.progressBar}
                  />
                  <Text style={styles.progressText}>
                    {(scene.motion_intensity * 100).toFixed(0)}%
                  </Text>
                </View>
              </View>
              
              <View style={styles.metricRow}>
                <Text style={styles.metricLabel}>Complexity:</Text>
                <View style={styles.progressContainer}>
                  <ProgressBar
                    progress={scene.visual_complexity}
                    color="#9C27B0"
                    style={styles.progressBar}
                  />
                  <Text style={styles.progressText}>
                    {(scene.visual_complexity * 100).toFixed(0)}%
                  </Text>
                </View>
              </View>
              
              {scene.description && (
                <Text style={styles.sceneDescription}>
                  {scene.description}
                </Text>
              )}
            </Card.Content>
          </Card>
        ))}
      </ScrollView>
    );
  };

  const BRollTab = () => {
    if (!processingResult || processingResult.broll_suggestions.length === 0) {
      return (
        <View style={styles.centerContainer}>
          <Text style={styles.infoText}>
            No B-roll suggestions available. Process a video to get recommendations.
          </Text>
        </View>
      );
    }

    // Group by priority
    const suggestionsByPriority = processingResult.broll_suggestions.reduce((acc, suggestion) => {
      const priority = suggestion.priority;
      if (!acc[priority]) acc[priority] = [];
      acc[priority].push(suggestion);
      return acc;
    }, {} as Record<number, BRollSuggestion[]>);

    return (
      <ScrollView style={styles.container}>
        <Title style={styles.sectionTitle}>
          B-roll Suggestions ({processingResult.broll_suggestions.length})
        </Title>
        
        {Object.entries(suggestionsByPriority)
          .sort(([a], [b]) => parseInt(b) - parseInt(a))
          .map(([priority, suggestions]) => (
            <View key={priority}>
              <Subheading style={styles.priorityTitle}>
                Priority {priority} ({suggestions.length} suggestions)
              </Subheading>
              
              {suggestions.map((suggestion, index) => (
                <Card key={index} style={styles.card}>
                  <Card.Content>
                    <View style={styles.suggestionHeader}>
                      <Text style={styles.suggestionType}>
                        {suggestion.suggestion_type.replace('_', ' ').toUpperCase()}
                      </Text>
                      <Chip mode="outlined" compact>
                        {(suggestion.confidence * 100).toFixed(0)}%
                      </Chip>
                    </View>
                    
                    <Text style={styles.suggestionTime}>
                      At {formatDuration(suggestion.timestamp)} for {formatDuration(suggestion.duration)}
                    </Text>
                    
                    <Text style={styles.suggestionDescription}>
                      {suggestion.description}
                    </Text>
                    
                    {suggestion.keywords.length > 0 && (
                      <View style={styles.keywordsContainer}>
                        <Text style={styles.keywordsLabel}>Keywords:</Text>
                        <View style={styles.keywordsRow}>
                          {suggestion.keywords.map((keyword, keywordIndex) => (
                            <Chip
                              key={keywordIndex}
                              mode="outlined"
                              compact
                              style={styles.keywordChip}
                            >
                              {keyword}
                            </Chip>
                          ))}
                        </View>
                      </View>
                    )}
                  </Card.Content>
                </Card>
              ))}
            </View>
          ))}
      </ScrollView>
    );
  };

  const JobsTab = () => (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.jobsHeader}>
        <Title>Processing Jobs ({processingJobs.length})</Title>
        <IconButton
          icon="refresh"
          onPress={onRefresh}
        />
      </View>
      
      {processingJobs.length === 0 ? (
        <View style={styles.centerContainer}>
          <Text style={styles.infoText}>No processing jobs found.</Text>
        </View>
      ) : (
        processingJobs.map((job) => (
          <Card key={job.job_id} style={styles.card}>
            <Card.Content>
              <View style={styles.jobHeader}>
                <Text style={styles.jobId}>
                  Job {job.job_id.substring(0, 8)}...
                </Text>
                <Chip
                  mode="outlined"
                  textStyle={{ color: getStatusColor(job.status) }}
                >
                  {job.status}
                </Chip>
              </View>
              
              {job.status === 'processing' && (
                <View style={styles.progressSection}>
                  <ProgressBar
                    progress={job.progress}
                    color="#2196F3"
                    style={styles.jobProgressBar}
                  />
                  <Text style={styles.progressMessage}>
                    {(job.progress * 100).toFixed(0)}% - {job.message}
                  </Text>
                </View>
              )}
              
              <Text style={styles.jobTime}>
                Started: {new Date(job.started_at).toLocaleString()}
              </Text>
              
              {job.completed_at && (
                <Text style={styles.jobTime}>
                  Completed: {new Date(job.completed_at).toLocaleString()}
                </Text>
              )}
              
              <View style={styles.jobActions}>
                <Button
                  mode="outlined"
                  compact
                  onPress={() => {
                    setSelectedJob(job);
                    setJobDetailsVisible(true);
                  }}
                >
                  Details
                </Button>
                
                {job.status === 'completed' && job.result && (
                  <Button
                    mode="contained"
                    compact
                    onPress={() => {
                      setProcessingResult(job.result!);
                      setActiveTab('results');
                    }}
                    style={styles.loadButton}
                  >
                    Load Result
                  </Button>
                )}
              </View>
            </Card.Content>
          </Card>
        ))
      )}
    </ScrollView>
  );

  // Tab navigation
  const TabBar = () => (
    <Surface style={styles.tabBar}>
      {[
        { key: 'upload', label: 'Upload', icon: 'upload' },
        { key: 'results', label: 'Results', icon: 'chart-line' },
        { key: 'scenes', label: 'Scenes', icon: 'movie' },
        { key: 'broll', label: 'B-roll', icon: 'auto-fix' },
        { key: 'jobs', label: 'Jobs', icon: 'clock' }
      ].map((tab) => (
        <TouchableOpacity
          key={tab.key}
          style={[
            styles.tabButton,
            activeTab === tab.key && styles.activeTabButton
          ]}
          onPress={() => setActiveTab(tab.key as any)}
          disabled={tab.key !== 'upload' && tab.key !== 'jobs' && !processingResult}
        >
          <Text
            style={[
              styles.tabLabel,
              activeTab === tab.key && styles.activeTabLabel,
              tab.key !== 'upload' && tab.key !== 'jobs' && !processingResult && styles.disabledTabLabel
            ]}
          >
            {tab.label}
          </Text>
        </TouchableOpacity>
      ))}
    </Surface>
  );

  return (
    <PaperProvider>
      <View style={styles.container}>
        <Appbar.Header>
          <Appbar.Content title="Advanced Video Processing" />
        </Appbar.Header>
        
        {/* Tab Content */}
        <View style={styles.content}>
          {activeTab === 'upload' && <UploadTab />}
          {activeTab === 'results' && <ResultsTab />}
          {activeTab === 'scenes' && <ScenesTab />}
          {activeTab === 'broll' && <BRollTab />}
          {activeTab === 'jobs' && <JobsTab />}
        </View>
        
        {/* Tab Bar */}
        <TabBar />
        
        {/* Job Details Modal */}
        <Portal>
          <Dialog
            visible={jobDetailsVisible}
            onDismiss={() => setJobDetailsVisible(false)}
          >
            <Dialog.Title>
              Job Details: {selectedJob?.job_id.substring(0, 8)}...
            </Dialog.Title>
            <Dialog.Content>
              {selectedJob && (
                <View>
                  <Paragraph>Status: {selectedJob.status}</Paragraph>
                  <Paragraph>Progress: {(selectedJob.progress * 100).toFixed(0)}%</Paragraph>
                  <Paragraph>Message: {selectedJob.message}</Paragraph>
                  <Paragraph>Started: {new Date(selectedJob.started_at).toLocaleString()}</Paragraph>
                  {selectedJob.completed_at && (
                    <Paragraph>Completed: {new Date(selectedJob.completed_at).toLocaleString()}</Paragraph>
                  )}
                  
                  {selectedJob.status === 'processing' && (
                    <ProgressBar
                      progress={selectedJob.progress}
                      color="#2196F3"
                      style={styles.dialogProgressBar}
                    />
                  )}
                </View>
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
    </PaperProvider>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  content: {
    flex: 1,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  infoText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
  card: {
    margin: 8,
    elevation: 2,
  },
  warningCard: {
    backgroundColor: '#fff3cd',
  },
  selectedVideo: {
    padding: 16,
    backgroundColor: '#e3f2fd',
    borderRadius: 8,
    marginVertical: 8,
  },
  videoName: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  videoSize: {
    fontSize: 14,
    color: '#666',
  },
  uploadArea: {
    padding: 32,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fafafa',
    borderRadius: 8,
    marginVertical: 8,
  },
  uploadText: {
    fontSize: 16,
    color: '#999',
  },
  selectButton: {
    marginTop: 16,
  },
  processButton: {
    margin: 16,
  },
  optionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
  },
  optionLabel: {
    fontSize: 16,
  },
  summaryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 8,
  },
  summaryCard: {
    width: (screenWidth - 32) / 2,
    margin: 4,
    padding: 16,
    alignItems: 'center',
    elevation: 2,
  },
  summaryNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2196F3',
  },
  summaryLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 4,
  },
  infoLabel: {
    fontSize: 14,
    color: '#666',
    flex: 1,
  },
  infoValue: {
    fontSize: 14,
    fontWeight: '500',
    flex: 1,
    textAlign: 'right',
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    marginLeft: 8,
  },
  progressBar: {
    flex: 1,
    height: 6,
  },
  progressText: {
    fontSize: 12,
    marginLeft: 8,
    minWidth: 35,
  },
  errorText: {
    fontSize: 14,
    color: '#d32f2f',
    marginVertical: 2,
  },
  sectionTitle: {
    margin: 16,
    marginBottom: 8,
  },
  priorityTitle: {
    margin: 16,
    marginBottom: 8,
    color: '#666',
  },
  sceneHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  sceneTitle: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  sceneTime: {
    fontSize: 14,
    color: '#666',
    marginBottom: 12,
  },
  metricRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 4,
  },
  metricLabel: {
    fontSize: 14,
    color: '#666',
    width: 80,
  },
  sceneDescription: {
    fontSize: 14,
    marginTop: 8,
    fontStyle: 'italic',
  },
  suggestionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  suggestionType: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2196F3',
  },
  suggestionTime: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  suggestionDescription: {
    fontSize: 14,
    marginBottom: 8,
  },
  keywordsContainer: {
    marginTop: 8,
  },
  keywordsLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  keywordsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  keywordChip: {
    marginRight: 4,
    marginBottom: 4,
  },
  jobsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 16,
  },
  jobHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  jobId: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  progressSection: {
    marginVertical: 8,
  },
  jobProgressBar: {
    height: 6,
    marginBottom: 4,
  },
  progressMessage: {
    fontSize: 12,
    color: '#666',
  },
  jobTime: {
    fontSize: 12,
    color: '#666',
    marginVertical: 2,
  },
  jobActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 12,
  },
  loadButton: {
    marginLeft: 8,
  },
  tabBar: {
    flexDirection: 'row',
    elevation: 4,
  },
  tabButton: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
  },
  activeTabButton: {
    backgroundColor: '#e3f2fd',
  },
  tabLabel: {
    fontSize: 12,
    color: '#666',
  },
  activeTabLabel: {
    color: '#2196F3',
    fontWeight: 'bold',
  },
  disabledTabLabel: {
    color: '#ccc',
  },
  dialogProgressBar: {
    marginTop: 8,
    height: 6,
  },
});

export default AdvancedVideoProcessingEngineMobile;