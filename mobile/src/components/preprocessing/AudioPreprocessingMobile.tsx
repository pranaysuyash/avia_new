import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  ScrollView,
  Text,
  StyleSheet,
  Alert,
  Modal,
  TouchableOpacity,
  Dimensions,
  SafeAreaView,
  StatusBar,
  ActivityIndicator,
  FlatList,
  Platform,
  PermissionsAndroid,
} from 'react-native';
import {
  Card,
  Button,
  IconButton,
  ProgressBar,
  Chip,
  FAB,
  Portal,
  Dialog,
  Paragraph,
  Title,
  Subheading,
  Caption,
  Surface,
  Divider,
  List,
  Switch,
  Slider,
  Provider as PaperProvider,
  DefaultTheme,
  DarkTheme,
  useTheme,
  Snackbar,
  Menu,
  Badge,
} from 'react-native-paper';
import MaterialIcons from 'react-native-vector-icons/MaterialIcons';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';
import DocumentPicker from 'react-native-document-picker';
import AudioRecorderPlayer, {
  AVEncoderAudioQualityIOSType,
  AVEncodingOption,
  AudioEncoderAndroidType,
  AudioSourceAndroidType,
  OutputFormatAndroidType,
} from 'react-native-audio-recorder-player';
import RNFS from 'react-native-fs';
import Sound from 'react-native-sound';
import WaveForm from 'react-native-audiowaveform';
import { LineChart, BarChart } from 'react-native-chart-kit';
import { GestureHandlerRootView, PanGestureHandler, State } from 'react-native-gesture-handler';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
  runOnJS,
} from 'react-native-reanimated';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

interface AudioFile {
  id: string;
  name: string;
  path: string;
  size: number;
  duration: number;
  format: string;
  processed: boolean;
  processing: boolean;
  waveform?: number[];
  metadata?: AudioMetadata;
}

interface AudioMetadata {
  sampleRate: number;
  bitRate: number;
  channels: number;
  codec: string;
}

interface ProcessingSettings {
  noiseReduction: boolean;
  noiseReductionLevel: number;
  normalization: boolean;
  trimSilence: boolean;
  silenceThreshold: number;
  compression: boolean;
  compressionRatio: number;
  equalization: boolean;
  eqPreset: string;
  outputFormat: string;
  outputQuality: string;
}

const AudioPreprocessingMobile: React.FC = () => {
  const theme = useTheme();
  const [audioFiles, setAudioFiles] = useState<AudioFile[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState('00:00:00');
  const [playbackTime, setPlaybackTime] = useState('00:00:00');
  const [currentPlayingId, setCurrentPlayingId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [processingQueue, setProcessingQueue] = useState<string[]>([]);
  
  const [settings, setSettings] = useState<ProcessingSettings>({
    noiseReduction: true,
    noiseReductionLevel: 0.5,
    normalization: true,
    trimSilence: true,
    silenceThreshold: 0.1,
    compression: false,
    compressionRatio: 4,
    equalization: false,
    eqPreset: 'flat',
    outputFormat: 'mp3',
    outputQuality: 'high',
  });

  const [settingsModalVisible, setSettingsModalVisible] = useState(false);
  const [waveformModalVisible, setWaveformModalVisible] = useState(false);
  const [selectedFileForWaveform, setSelectedFileForWaveform] = useState<AudioFile | null>(null);
  const [snackbarVisible, setSnackbarVisible] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [menuVisible, setMenuVisible] = useState(false);
  const [expandedView, setExpandedView] = useState(false);
  const [filterMenuVisible, setFilterMenuVisible] = useState(false);
  const [filter, setFilter] = useState<'all' | 'processed' | 'unprocessed'>('all');

  const audioRecorderPlayer = useRef(new AudioRecorderPlayer()).current;
  const soundRef = useRef<Sound | null>(null);
  const recordingPath = useRef<string>('');
  
  // Animation values
  const recordingScale = useSharedValue(1);
  const progressWidth = useSharedValue(0);

  useEffect(() => {
    requestPermissions();
    return () => {
      if (soundRef.current) {
        soundRef.current.release();
      }
    };
  }, []);

  const requestPermissions = async () => {
    if (Platform.OS === 'android') {
      try {
        const grants = await PermissionsAndroid.requestMultiple([
          PermissionsAndroid.PERMISSIONS.WRITE_EXTERNAL_STORAGE,
          PermissionsAndroid.PERMISSIONS.READ_EXTERNAL_STORAGE,
          PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
        ]);
        
        if (
          grants['android.permission.WRITE_EXTERNAL_STORAGE'] !== PermissionsAndroid.RESULTS.GRANTED ||
          grants['android.permission.READ_EXTERNAL_STORAGE'] !== PermissionsAndroid.RESULTS.GRANTED ||
          grants['android.permission.RECORD_AUDIO'] !== PermissionsAndroid.RESULTS.GRANTED
        ) {
          Alert.alert('Permissions required', 'Please grant all permissions to use audio features');
        }
      } catch (err) {
        console.warn(err);
      }
    }
  };

  const pickAudioFiles = async () => {
    try {
      const results = await DocumentPicker.pick({
        type: [DocumentPicker.types.audio],
        allowMultiSelection: true,
      });
      
      const newFiles: AudioFile[] = results.map((file) => ({
        id: `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        name: file.name || 'Unknown',
        path: file.uri,
        size: file.size || 0,
        duration: 0, // Will be calculated
        format: file.name?.split('.').pop() || 'unknown',
        processed: false,
        processing: false,
      }));
      
      setAudioFiles([...audioFiles, ...newFiles]);
      showSnackbar(`Added ${results.length} audio file(s)`);
      
      // Calculate durations in background
      newFiles.forEach(file => calculateAudioDuration(file));
    } catch (error) {
      if (!DocumentPicker.isCancel(error)) {
        Alert.alert('Error', 'Failed to pick audio files');
      }
    }
  };

  const calculateAudioDuration = async (file: AudioFile) => {
    try {
      // Mock duration calculation - in real app, use audio metadata library
      const mockDuration = Math.floor(Math.random() * 300) + 30; // 30s to 5min
      
      setAudioFiles(prev => prev.map(f => 
        f.id === file.id ? { ...f, duration: mockDuration } : f
      ));
    } catch (error) {
      console.error('Failed to calculate duration:', error);
    }
  };

  const startRecording = async () => {
    try {
      const path = Platform.select({
        ios: `${RNFS.DocumentDirectoryPath}/recording_${Date.now()}.m4a`,
        android: `${RNFS.ExternalDirectoryPath}/recording_${Date.now()}.mp3`,
      });
      
      recordingPath.current = path!;
      
      const audioSet = {
        AudioEncoderAndroid: AudioEncoderAndroidType.AAC,
        AudioSourceAndroid: AudioSourceAndroidType.MIC,
        AVEncoderAudioQualityKeyIOS: AVEncoderAudioQualityIOSType.high,
        AVNumberOfChannelsKeyIOS: 2,
        AVFormatIDKeyIOS: AVEncodingOption.aac,
        OutputFormatAndroid: OutputFormatAndroidType.AAC_ADTS,
      };
      
      await audioRecorderPlayer.startRecorder(path, audioSet);
      audioRecorderPlayer.addRecordBackListener((e) => {
        setRecordingTime(audioRecorderPlayer.mmssss(Math.floor(e.currentPosition)));
        return;
      });
      
      setIsRecording(true);
      
      // Start recording animation
      recordingScale.value = withSpring(1.2, {
        damping: 2,
        stiffness: 80,
      });
    } catch (error) {
      Alert.alert('Error', 'Failed to start recording');
      console.error(error);
    }
  };

  const stopRecording = async () => {
    try {
      const result = await audioRecorderPlayer.stopRecorder();
      audioRecorderPlayer.removeRecordBackListener();
      setIsRecording(false);
      setRecordingTime('00:00:00');
      
      // Stop recording animation
      recordingScale.value = withSpring(1);
      
      // Add recorded file to list
      const recordedFile: AudioFile = {
        id: `recording_${Date.now()}`,
        name: `Recording_${new Date().toLocaleTimeString()}`,
        path: result,
        size: 0, // Will be calculated
        duration: 0, // Will be calculated
        format: Platform.OS === 'ios' ? 'm4a' : 'mp3',
        processed: false,
        processing: false,
      };
      
      setAudioFiles([...audioFiles, recordedFile]);
      showSnackbar('Recording saved successfully');
      
      // Get file info
      const stat = await RNFS.stat(result);
      setAudioFiles(prev => prev.map(f => 
        f.id === recordedFile.id ? { ...f, size: stat.size } : f
      ));
    } catch (error) {
      Alert.alert('Error', 'Failed to stop recording');
      console.error(error);
    }
  };

  const playAudio = async (file: AudioFile) => {
    try {
      if (currentPlayingId === file.id) {
        await audioRecorderPlayer.stopPlayer();
        setCurrentPlayingId(null);
        setPlaybackTime('00:00:00');
        return;
      }
      
      if (currentPlayingId) {
        await audioRecorderPlayer.stopPlayer();
      }
      
      await audioRecorderPlayer.startPlayer(file.path);
      audioRecorderPlayer.addPlayBackListener((e) => {
        setPlaybackTime(audioRecorderPlayer.mmssss(Math.floor(e.currentPosition)));
        progressWidth.value = withTiming(
          (e.currentPosition / e.duration) * 100,
          { duration: 100 }
        );
        
        if (e.currentPosition === e.duration) {
          setCurrentPlayingId(null);
          setPlaybackTime('00:00:00');
          progressWidth.value = withTiming(0);
        }
        return;
      });
      
      setCurrentPlayingId(file.id);
    } catch (error) {
      Alert.alert('Error', 'Failed to play audio');
      console.error(error);
    }
  };

  const processSelectedFiles = async () => {
    const filesToProcess = selectedFiles.length > 0 ? selectedFiles : audioFiles.map(f => f.id);
    
    if (filesToProcess.length === 0) {
      Alert.alert('No files', 'Please select audio files to process');
      return;
    }
    
    setProcessingQueue(filesToProcess);
    
    for (const fileId of filesToProcess) {
      await processAudioFile(fileId);
    }
    
    setProcessingQueue([]);
    setSelectedFiles([]);
    showSnackbar('Audio processing completed');
  };

  const processAudioFile = async (fileId: string) => {
    try {
      setAudioFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, processing: true } : f
      ));
      
      // Simulate processing with different stages
      const stages = [
        'Analyzing audio...',
        'Applying noise reduction...',
        'Normalizing levels...',
        'Trimming silence...',
        'Finalizing...',
      ];
      
      for (const stage of stages) {
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
      // Generate mock waveform data
      const waveform = Array.from({ length: 50 }, () => Math.random() * 100);
      
      setAudioFiles(prev => prev.map(f => 
        f.id === fileId ? { 
          ...f, 
          processing: false, 
          processed: true,
          waveform,
          metadata: {
            sampleRate: 44100,
            bitRate: 128000,
            channels: 2,
            codec: 'AAC',
          }
        } : f
      ));
    } catch (error) {
      setAudioFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, processing: false } : f
      ));
      Alert.alert('Error', 'Failed to process audio file');
    }
  };

  const deleteAudioFile = (fileId: string) => {
    Alert.alert(
      'Delete File',
      'Are you sure you want to delete this audio file?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => {
            setAudioFiles(prev => prev.filter(f => f.id !== fileId));
            setSelectedFiles(prev => prev.filter(id => id !== fileId));
            showSnackbar('Audio file deleted');
          },
        },
      ]
    );
  };

  const toggleFileSelection = (fileId: string) => {
    setSelectedFiles(prev => 
      prev.includes(fileId)
        ? prev.filter(id => id !== fileId)
        : [...prev, fileId]
    );
  };

  const showSnackbar = (message: string) => {
    setSnackbarMessage(message);
    setSnackbarVisible(true);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const getFilteredFiles = () => {
    switch (filter) {
      case 'processed':
        return audioFiles.filter(f => f.processed);
      case 'unprocessed':
        return audioFiles.filter(f => !f.processed);
      default:
        return audioFiles;
    }
  };

  const recordingAnimatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: recordingScale.value }],
  }));

  const renderAudioFile = ({ item }: { item: AudioFile }) => {
    const isSelected = selectedFiles.includes(item.id);
    const isPlaying = currentPlayingId === item.id;
    const isProcessing = item.processing || processingQueue.includes(item.id);
    
    return (
      <TouchableOpacity
        onPress={() => toggleFileSelection(item.id)}
        onLongPress={() => {
          setSelectedFileForWaveform(item);
          setWaveformModalVisible(true);
        }}
      >
        <Surface style={[styles.audioCard, isSelected && styles.selectedCard]} elevation={2}>
          <View style={styles.audioCardHeader}>
            <View style={styles.audioIcon}>
              <MaterialIcons 
                name={item.format === 'mp3' ? 'audiotrack' : 'music-note'} 
                size={32} 
                color={theme.colors.primary} 
              />
              {item.processed && (
                <Badge style={styles.processedBadge} size={12} />
              )}
            </View>
            
            <View style={styles.audioInfo}>
              <Text style={[styles.audioName, { color: theme.colors.onSurface }]} numberOfLines={1}>
                {item.name}
              </Text>
              <View style={styles.audioMeta}>
                <Caption>{formatFileSize(item.size)}</Caption>
                <Caption> • </Caption>
                <Caption>{formatDuration(item.duration)}</Caption>
                <Caption> • </Caption>
                <Caption>{item.format.toUpperCase()}</Caption>
              </View>
              
              {isProcessing && (
                <ProgressBar 
                  indeterminate 
                  style={styles.processingProgress}
                  color={theme.colors.primary}
                />
              )}
            </View>
            
            <View style={styles.audioActions}>
              <IconButton
                icon={isPlaying ? 'pause' : 'play-arrow'}
                onPress={() => playAudio(item)}
                disabled={isProcessing}
              />
              <IconButton
                icon="delete"
                onPress={() => deleteAudioFile(item.id)}
              />
            </View>
          </View>
          
          {item.waveform && !isProcessing && (
            <View style={styles.waveformPreview}>
              {item.waveform.map((height, index) => (
                <View
                  key={index}
                  style={[
                    styles.waveformBar,
                    { 
                      height: height * 0.3,
                      backgroundColor: theme.colors.primary,
                      opacity: 0.7,
                    }
                  ]}
                />
              ))}
            </View>
          )}
        </Surface>
      </TouchableOpacity>
    );
  };

  const renderSettingsModal = () => (
    <Modal
      visible={settingsModalVisible}
      onRequestClose={() => setSettingsModalVisible(false)}
      animationType="slide"
    >
      <SafeAreaView style={[styles.modalContainer, { backgroundColor: theme.colors.background }]}>
        <Surface style={styles.modalHeader} elevation={2}>
          <Title>Processing Settings</Title>
          <IconButton
            icon="close"
            onPress={() => setSettingsModalVisible(false)}
          />
        </Surface>
        
        <ScrollView style={styles.modalContent}>
          <List.Section>
            <List.Subheader>Noise Reduction</List.Subheader>
            <List.Item
              title="Enable Noise Reduction"
              right={() => (
                <Switch
                  value={settings.noiseReduction}
                  onValueChange={(value) => setSettings({ ...settings, noiseReduction: value })}
                />
              )}
            />
            {settings.noiseReduction && (
              <View style={styles.sliderContainer}>
                <Text style={[styles.sliderLabel, { color: theme.colors.onSurface }]}>
                  Reduction Level: {Math.round(settings.noiseReductionLevel * 100)}%
                </Text>
                <Slider
                  style={styles.slider}
                  minimumValue={0}
                  maximumValue={1}
                  value={settings.noiseReductionLevel}
                  onValueChange={(value) => setSettings({ ...settings, noiseReductionLevel: value })}
                  thumbStyle={{ backgroundColor: theme.colors.primary }}
                  trackStyle={{ backgroundColor: theme.colors.outline }}
                  minimumTrackTintColor={theme.colors.primary}
                />
              </View>
            )}
          </List.Section>

          <Divider />

          <List.Section>
            <List.Subheader>Audio Enhancement</List.Subheader>
            <List.Item
              title="Normalize Audio Levels"
              right={() => (
                <Switch
                  value={settings.normalization}
                  onValueChange={(value) => setSettings({ ...settings, normalization: value })}
                />
              )}
            />
            <List.Item
              title="Trim Silence"
              right={() => (
                <Switch
                  value={settings.trimSilence}
                  onValueChange={(value) => setSettings({ ...settings, trimSilence: value })}
                />
              )}
            />
            {settings.trimSilence && (
              <View style={styles.sliderContainer}>
                <Text style={[styles.sliderLabel, { color: theme.colors.onSurface }]}>
                  Silence Threshold: {Math.round(settings.silenceThreshold * 100)}%
                </Text>
                <Slider
                  style={styles.slider}
                  minimumValue={0}
                  maximumValue={0.5}
                  value={settings.silenceThreshold}
                  onValueChange={(value) => setSettings({ ...settings, silenceThreshold: value })}
                  thumbStyle={{ backgroundColor: theme.colors.primary }}
                  trackStyle={{ backgroundColor: theme.colors.outline }}
                  minimumTrackTintColor={theme.colors.primary}
                />
              </View>
            )}
          </List.Section>

          <Divider />

          <List.Section>
            <List.Subheader>Compression</List.Subheader>
            <List.Item
              title="Enable Compression"
              right={() => (
                <Switch
                  value={settings.compression}
                  onValueChange={(value) => setSettings({ ...settings, compression: value })}
                />
              )}
            />
            {settings.compression && (
              <View style={styles.sliderContainer}>
                <Text style={[styles.sliderLabel, { color: theme.colors.onSurface }]}>
                  Compression Ratio: {settings.compressionRatio}:1
                </Text>
                <Slider
                  style={styles.slider}
                  minimumValue={2}
                  maximumValue={10}
                  step={1}
                  value={settings.compressionRatio}
                  onValueChange={(value) => setSettings({ ...settings, compressionRatio: value })}
                  thumbStyle={{ backgroundColor: theme.colors.primary }}
                  trackStyle={{ backgroundColor: theme.colors.outline }}
                  minimumTrackTintColor={theme.colors.primary}
                />
              </View>
            )}
          </List.Section>

          <Divider />

          <List.Section>
            <List.Subheader>Output Settings</List.Subheader>
            <List.Item
              title="Output Format"
              description={settings.outputFormat.toUpperCase()}
              onPress={() => {
                // Show format selection dialog
              }}
            />
            <List.Item
              title="Output Quality"
              description={settings.outputQuality.charAt(0).toUpperCase() + settings.outputQuality.slice(1)}
              onPress={() => {
                // Show quality selection dialog
              }}
            />
          </List.Section>
        </ScrollView>
        
        <Surface style={styles.modalFooter} elevation={2}>
          <Button
            mode="contained"
            onPress={() => {
              setSettingsModalVisible(false);
              showSnackbar('Settings saved');
            }}
            style={styles.modalButton}
          >
            Save Settings
          </Button>
        </Surface>
      </SafeAreaView>
    </Modal>
  );

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <PaperProvider>
        <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
          {/* Header */}
          <Surface style={styles.header} elevation={2}>
            <View style={styles.headerContent}>
              <Title>Audio Preprocessing</Title>
              <View style={styles.headerActions}>
                <Badge visible={selectedFiles.length > 0} style={styles.selectionBadge}>
                  {selectedFiles.length}
                </Badge>
                <Menu
                  visible={filterMenuVisible}
                  onDismiss={() => setFilterMenuVisible(false)}
                  anchor={
                    <IconButton
                      icon="filter-list"
                      onPress={() => setFilterMenuVisible(true)}
                    />
                  }
                >
                  <Menu.Item
                    onPress={() => {
                      setFilter('all');
                      setFilterMenuVisible(false);
                    }}
                    title="All Files"
                    icon={filter === 'all' ? 'check' : undefined}
                  />
                  <Menu.Item
                    onPress={() => {
                      setFilter('processed');
                      setFilterMenuVisible(false);
                    }}
                    title="Processed"
                    icon={filter === 'processed' ? 'check' : undefined}
                  />
                  <Menu.Item
                    onPress={() => {
                      setFilter('unprocessed');
                      setFilterMenuVisible(false);
                    }}
                    title="Unprocessed"
                    icon={filter === 'unprocessed' ? 'check' : undefined}
                  />
                </Menu>
                <IconButton
                  icon="settings"
                  onPress={() => setSettingsModalVisible(true)}
                />
              </View>
            </View>
          </Surface>

          {/* Recording Controls */}
          <Surface style={styles.recordingSection} elevation={1}>
            <View style={styles.recordingControls}>
              <Animated.View style={recordingAnimatedStyle}>
                <FAB
                  icon={isRecording ? 'stop' : 'microphone'}
                  onPress={isRecording ? stopRecording : startRecording}
                  style={[
                    styles.recordButton,
                    { backgroundColor: isRecording ? theme.colors.error : theme.colors.primary }
                  ]}
                />
              </Animated.View>
              
              <View style={styles.recordingInfo}>
                <Text style={[styles.recordingTime, { color: theme.colors.onSurface }]}>
                  {isRecording ? recordingTime : 'Tap to record'}
                </Text>
                {isRecording && (
                  <Caption>Recording in progress...</Caption>
                )}
              </View>
              
              <IconButton
                icon="folder-open"
                onPress={pickAudioFiles}
                size={28}
              />
            </View>
          </Surface>

          {/* Audio Files List */}
          <FlatList
            data={getFilteredFiles()}
            renderItem={renderAudioFile}
            keyExtractor={(item) => item.id}
            contentContainerStyle={styles.filesList}
            ListEmptyComponent={
              <View style={styles.emptyState}>
                <MaterialIcons name="library-music" size={64} color={theme.colors.onSurfaceVariant} />
                <Subheading style={{ color: theme.colors.onSurfaceVariant, marginTop: 16 }}>
                  No audio files yet
                </Subheading>
                <Caption>Record audio or import files to get started</Caption>
              </View>
            }
          />

          {/* Action Buttons */}
          {audioFiles.length > 0 && (
            <Surface style={styles.actionBar} elevation={3}>
              <Button
                mode="outlined"
                onPress={() => {
                  if (selectedFiles.length === audioFiles.length) {
                    setSelectedFiles([]);
                  } else {
                    setSelectedFiles(audioFiles.map(f => f.id));
                  }
                }}
                style={styles.actionButton}
              >
                {selectedFiles.length === audioFiles.length ? 'Deselect All' : 'Select All'}
              </Button>
              <Button
                mode="contained"
                onPress={processSelectedFiles}
                loading={processingQueue.length > 0}
                disabled={processingQueue.length > 0}
                style={styles.actionButton}
                icon="auto-fix"
              >
                Process Audio
              </Button>
            </Surface>
          )}

          {/* Settings Modal */}
          {renderSettingsModal()}

          {/* Waveform Modal */}
          <Portal>
            <Dialog
              visible={waveformModalVisible}
              onDismiss={() => setWaveformModalVisible(false)}
              style={styles.waveformDialog}
            >
              <Dialog.Title>Audio Waveform</Dialog.Title>
              <Dialog.Content>
                {selectedFileForWaveform && (
                  <>
                    <Subheading>{selectedFileForWaveform.name}</Subheading>
                    {selectedFileForWaveform.waveform && (
                      <View style={styles.waveformContainer}>
                        <LineChart
                          data={{
                            labels: [],
                            datasets: [{
                              data: selectedFileForWaveform.waveform.slice(0, 20)
                            }]
                          }}
                          width={screenWidth - 80}
                          height={200}
                          chartConfig={{
                            backgroundColor: theme.colors.surface,
                            backgroundGradientFrom: theme.colors.surface,
                            backgroundGradientTo: theme.colors.surface,
                            decimalPlaces: 0,
                            color: (opacity = 1) => theme.colors.primary,
                            style: {
                              borderRadius: 16
                            }
                          }}
                          bezier
                          style={{
                            marginVertical: 8,
                            borderRadius: 16
                          }}
                        />
                      </View>
                    )}
                    {selectedFileForWaveform.metadata && (
                      <View style={styles.metadataContainer}>
                        <View style={styles.metadataRow}>
                          <Caption>Sample Rate:</Caption>
                          <Text style={{ color: theme.colors.onSurface }}>
                            {selectedFileForWaveform.metadata.sampleRate} Hz
                          </Text>
                        </View>
                        <View style={styles.metadataRow}>
                          <Caption>Bit Rate:</Caption>
                          <Text style={{ color: theme.colors.onSurface }}>
                            {selectedFileForWaveform.metadata.bitRate / 1000} kbps
                          </Text>
                        </View>
                        <View style={styles.metadataRow}>
                          <Caption>Channels:</Caption>
                          <Text style={{ color: theme.colors.onSurface }}>
                            {selectedFileForWaveform.metadata.channels === 2 ? 'Stereo' : 'Mono'}
                          </Text>
                        </View>
                        <View style={styles.metadataRow}>
                          <Caption>Codec:</Caption>
                          <Text style={{ color: theme.colors.onSurface }}>
                            {selectedFileForWaveform.metadata.codec}
                          </Text>
                        </View>
                      </View>
                    )}
                  </>
                )}
              </Dialog.Content>
              <Dialog.Actions>
                <Button onPress={() => setWaveformModalVisible(false)}>Close</Button>
              </Dialog.Actions>
            </Dialog>
          </Portal>

          {/* Snackbar */}
          <Snackbar
            visible={snackbarVisible}
            onDismiss={() => setSnackbarVisible(false)}
            duration={3000}
          >
            {snackbarMessage}
          </Snackbar>
        </SafeAreaView>
      </PaperProvider>
    </GestureHandlerRootView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  selectionBadge: {
    position: 'absolute',
    top: -8,
    right: -8,
    zIndex: 1,
  },
  recordingSection: {
    margin: 16,
    padding: 16,
    borderRadius: 12,
  },
  recordingControls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  recordButton: {
    marginRight: 16,
  },
  recordingInfo: {
    flex: 1,
    alignItems: 'center',
  },
  recordingTime: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  filesList: {
    padding: 16,
    paddingBottom: 80,
  },
  audioCard: {
    padding: 16,
    marginBottom: 12,
    borderRadius: 12,
  },
  selectedCard: {
    borderWidth: 2,
    borderColor: '#2196F3',
  },
  audioCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  audioIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#E3F2FD',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  processedBadge: {
    position: 'absolute',
    top: -4,
    right: -4,
    backgroundColor: '#4CAF50',
  },
  audioInfo: {
    flex: 1,
  },
  audioName: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 4,
  },
  audioMeta: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  processingProgress: {
    marginTop: 8,
    height: 2,
  },
  audioActions: {
    flexDirection: 'row',
  },
  waveformPreview: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    height: 40,
    marginTop: 12,
  },
  waveformBar: {
    width: 3,
    backgroundColor: '#2196F3',
    borderRadius: 1.5,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 100,
  },
  actionBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    padding: 16,
    justifyContent: 'space-around',
  },
  actionButton: {
    flex: 1,
    marginHorizontal: 8,
  },
  modalContainer: {
    flex: 1,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  modalContent: {
    flex: 1,
  },
  modalFooter: {
    padding: 16,
  },
  modalButton: {
    paddingVertical: 4,
  },
  sliderContainer: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  sliderLabel: {
    fontSize: 14,
    marginBottom: 8,
  },
  slider: {
    height: 40,
  },
  waveformDialog: {
    maxHeight: '80%',
  },
  waveformContainer: {
    marginVertical: 16,
    alignItems: 'center',
  },
  metadataContainer: {
    marginTop: 16,
  },
  metadataRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 4,
  },
});

export default AudioPreprocessingMobile;