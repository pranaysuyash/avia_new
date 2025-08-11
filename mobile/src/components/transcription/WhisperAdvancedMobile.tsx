/**
 * WhisperAdvancedMobile - React Native component for Whisper Advanced Integration
 * Optimized for mobile devices with touch-friendly interface and offline capabilities
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  Alert,
  StyleSheet,
  Dimensions,
  Platform,
  PermissionsAndroid,
  ActivityIndicator,
  Modal,
  TextInput,
  Switch,
  Animated,
  PanResponder,
} from 'react-native';
import DocumentPicker from 'react-native-document-picker';
import AudioRecorderPlayer from 'react-native-audio-recorder-player';
import RNFS from 'react-native-fs';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-netinfo/netinfo';
import { Slider } from '@react-native-community/slider';
import Icon from 'react-native-vector-icons/MaterialIcons';

// Types
interface TranscriptionResult {
  text: string;
  language?: string;
  language_confidence?: number;
  segments: Array<{
    id: number;
    start: number;
    end: number;
    text: string;
    confidence?: number;
    speaker_id?: string;
  }>;
  words?: Array<{
    word: string;
    start: number;
    end: number;
    confidence: number;
  }>;
  confidence_analysis?: {
    overall_confidence: number;
    preprocessing_quality: number;
    quality_improvement: number;
  };
  processing_time: number;
  model_used: string;
}

interface WhisperConfig {
  model: string;
  language?: string;
  temperature: number;
  enable_language_detection: boolean;
  enable_confidence_analysis: boolean;
  enable_word_timestamps: boolean;
  enable_speaker_detection: boolean;
  confidence_threshold: number;
}

interface LanguageDetectionResult {
  detected_language: string;
  confidence: number;
  alternative_languages: Array<{[key: string]: number}>;
}

const { width, height } = Dimensions.get('window');

const WhisperAdvancedMobile: React.FC = () => {
  // State management
  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isDetectingLanguage, setIsDetectingLanguage] = useState(false);
  const [result, setResult] = useState<TranscriptionResult | null>(null);
  const [languageResult, setLanguageResult] = useState<LanguageDetectionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isOnline, setIsOnline] = useState(true);
  const [processingMode, setProcessingMode] = useState<'record' | 'upload' | 'language'>('record');
  const [showSettings, setShowSettings] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [playbackTime, setPlaybackTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);

  // Configuration state
  const [config, setConfig] = useState<WhisperConfig>({
    model: 'whisper-1',
    language: undefined,
    temperature: 0.0,
    enable_language_detection: true,
    enable_confidence_analysis: true,
    enable_word_timestamps: true,
    enable_speaker_detection: false,
    confidence_threshold: 0.8,
  });

  // Refs
  const audioRecorderPlayer = useRef(new AudioRecorderPlayer()).current;
  const recordingTimer = useRef<NodeJS.Timeout | null>(null);
  const fadeAnim = useRef(new Animated.Value(0)).current;

  // Effects
  useEffect(() => {
    checkNetworkStatus();
    loadSavedConfig();
    requestPermissions();
    
    const unsubscribe = NetInfo.addEventListener(state => {
      setIsOnline(state.isConnected ?? false);
    });

    return () => {
      unsubscribe();
      if (recordingTimer.current) {
        clearInterval(recordingTimer.current);
      }
      audioRecorderPlayer.stopRecorder();
      audioRecorderPlayer.stopPlayer();
    };
  }, []);

  // Fade in animation
  useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 1000,
      useNativeDriver: true,
    }).start();
  }, []);

  // Network status check
  const checkNetworkStatus = async () => {
    const netInfo = await NetInfo.fetch();
    setIsOnline(netInfo.isConnected ?? false);
  };

  // Load saved configuration
  const loadSavedConfig = async () => {
    try {
      const savedConfig = await AsyncStorage.getItem('whisper_config');
      if (savedConfig) {
        setConfig(JSON.parse(savedConfig));
      }
    } catch (error) {
      console.log('Error loading saved config:', error);
    }
  };

  // Save configuration
  const saveConfig = async (newConfig: WhisperConfig) => {
    try {
      await AsyncStorage.setItem('whisper_config', JSON.stringify(newConfig));
      setConfig(newConfig);
    } catch (error) {
      console.log('Error saving config:', error);
    }
  };

  // Request permissions
  const requestPermissions = async () => {
    if (Platform.OS === 'android') {
      try {
        const grants = await PermissionsAndroid.requestMultiple([
          PermissionsAndroid.PERMISSIONS.WRITE_EXTERNAL_STORAGE,
          PermissionsAndroid.PERMISSIONS.READ_EXTERNAL_STORAGE,
          PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
        ]);

        if (
          grants['android.permission.WRITE_EXTERNAL_STORAGE'] === PermissionsAndroid.RESULTS.GRANTED &&
          grants['android.permission.READ_EXTERNAL_STORAGE'] === PermissionsAndroid.RESULTS.GRANTED &&
          grants['android.permission.RECORD_AUDIO'] === PermissionsAndroid.RESULTS.GRANTED
        ) {
          console.log('Permissions granted');
        } else {
          Alert.alert('Permissions required', 'Please grant all permissions to use this feature');
        }
      } catch (err) {
        console.warn(err);
      }
    }
  };

  // Start recording
  const startRecording = async () => {
    try {
      setError(null);
      const path = Platform.select({
        ios: 'whisper_recording.m4a',
        android: `${RNFS.CachesDirectoryPath}/whisper_recording.mp3`,
      });

      const audioSet = {
        AudioEncoderAndroid: 'aac',
        AudioSourceAndroid: 'mic',
        AVEncoderAudioQualityKeyIOS: 'high',
        AVNumberOfChannelsKeyIOS: 1,
        AVFormatIDKeyIOS: 'mp4a',
      };

      await audioRecorderPlayer.startRecorder(path, audioSet);
      setIsRecording(true);
      setRecordingTime(0);

      recordingTimer.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

      audioRecorderPlayer.addRecordBackListener((e) => {
        setRecordingTime(Math.floor(e.currentPosition / 1000));
      });

    } catch (error) {
      console.error('Recording error:', error);
      setError('Failed to start recording');
    }
  };

  // Stop recording
  const stopRecording = async () => {
    try {
      const result = await audioRecorderPlayer.stopRecorder();
      audioRecorderPlayer.removeRecordBackListener();
      setIsRecording(false);
      
      if (recordingTimer.current) {
        clearInterval(recordingTimer.current);
      }

      // Set the recorded file
      setSelectedFile({
        uri: result,
        name: 'recording.mp3',
        type: 'audio/mp3',
        size: 0, // Will be calculated if needed
      });

      Alert.alert('Recording Complete', 'Your recording is ready for transcription');
    } catch (error) {
      console.error('Stop recording error:', error);
      setError('Failed to stop recording');
    }
  };

  // File picker
  const pickFile = async () => {
    try {
      const res = await DocumentPicker.pick({
        type: [DocumentPicker.types.audio],
      });

      if (res && res.length > 0) {
        const file = res[0];
        
        // Check file size (25MB limit)
        if (file.size && file.size > 25 * 1024 * 1024) {
          Alert.alert('File Too Large', 'Please select a file smaller than 25MB');
          return;
        }

        setSelectedFile(file);
        setError(null);
      }
    } catch (err) {
      if (DocumentPicker.isCancel(err)) {
        // User cancelled
      } else {
        setError('Failed to select file');
      }
    }
  };

  // Play/pause audio
  const togglePlayback = async () => {
    if (!selectedFile) return;

    try {
      if (isPlaying) {
        await audioRecorderPlayer.pausePlayer();
        setIsPlaying(false);
      } else {
        await audioRecorderPlayer.startPlayer(selectedFile.uri);
        setIsPlaying(true);

        audioRecorderPlayer.addPlayBackListener((e) => {
          setPlaybackTime(Math.floor(e.currentPosition / 1000));
          setProgress(e.currentPosition / e.duration);
        });
      }
    } catch (error) {
      console.error('Playback error:', error);
    }
  };

  // Transcribe audio
  const handleTranscribe = async () => {
    if (!selectedFile) {
      Alert.alert('No File Selected', 'Please record or select an audio file');
      return;
    }

    if (!isOnline) {
      Alert.alert('Offline Mode', 'Transcription requires internet connection');
      return;
    }

    setIsTranscribing(true);
    setError(null);
    setProgress(0);

    try {
      const formData = new FormData();
      formData.append('audio_file', {
        uri: selectedFile.uri,
        type: selectedFile.type || 'audio/mp3',
        name: selectedFile.name || 'audio.mp3',
      } as any);
      formData.append('config', JSON.stringify(config));

      const response = await fetch('/api/v1/whisper-advanced/transcribe', {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to transcribe audio');
      }

      const data = await response.json();
      setResult(data.data);
      
      // Save result to local storage for offline access
      await AsyncStorage.setItem('last_transcription', JSON.stringify(data.data));
      
    } catch (error) {
      console.error('Transcription error:', error);
      setError(error instanceof Error ? error.message : 'An error occurred');
    } finally {
      setIsTranscribing(false);
    }
  };

  // Detect language
  const handleLanguageDetection = async () => {
    if (!selectedFile) {
      Alert.alert('No File Selected', 'Please record or select an audio file');
      return;
    }

    if (!isOnline) {
      Alert.alert('Offline Mode', 'Language detection requires internet connection');
      return;
    }

    setIsDetectingLanguage(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('audio_file', {
        uri: selectedFile.uri,
        type: selectedFile.type || 'audio/mp3',
        name: selectedFile.name || 'audio.mp3',
      } as any);

      const response = await fetch('/api/v1/whisper-advanced/detect-language', {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to detect language');
      }

      const data = await response.json();
      setLanguageResult(data.data);
      
    } catch (error) {
      console.error('Language detection error:', error);
      setError(error instanceof Error ? error.message : 'An error occurred');
    } finally {
      setIsDetectingLanguage(false);
    }
  };

  // Format time
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Copy to clipboard
  const copyToClipboard = (text: string) => {
    // React Native clipboard implementation would go here
    Alert.alert('Copied', 'Text copied to clipboard');
  };

  // Share result
  const shareResult = () => {
    if (result) {
      // React Native share implementation would go here
      Alert.alert('Share', 'Sharing functionality would be implemented here');
    }
  };

  // Render mode tabs
  const renderModeTabs = () => (
    <View style={styles.tabContainer}>
      <TouchableOpacity
        style={[styles.tab, processingMode === 'record' && styles.activeTab]}
        onPress={() => setProcessingMode('record')}
      >
        <Icon name="mic" size={20} color={processingMode === 'record' ? '#fff' : '#666'} />
        <Text style={[styles.tabText, processingMode === 'record' && styles.activeTabText]}>
          Record
        </Text>
      </TouchableOpacity>
      
      <TouchableOpacity
        style={[styles.tab, processingMode === 'upload' && styles.activeTab]}
        onPress={() => setProcessingMode('upload')}
      >
        <Icon name="upload-file" size={20} color={processingMode === 'upload' ? '#fff' : '#666'} />
        <Text style={[styles.tabText, processingMode === 'upload' && styles.activeTabText]}>
          Upload
        </Text>
      </TouchableOpacity>
      
      <TouchableOpacity
        style={[styles.tab, processingMode === 'language' && styles.activeTab]}
        onPress={() => setProcessingMode('language')}
      >
        <Icon name="language" size={20} color={processingMode === 'language' ? '#fff' : '#666'} />
        <Text style={[styles.tabText, processingMode === 'language' && styles.activeTabText]}>
          Language
        </Text>
      </TouchableOpacity>
    </View>
  );

  // Render recording interface
  const renderRecordingInterface = () => (
    <View style={styles.recordingContainer}>
      <View style={styles.recordingVisualizer}>
        <Icon 
          name={isRecording ? "stop" : "mic"} 
          size={60} 
          color={isRecording ? "#ff4444" : "#4CAF50"} 
        />
        {isRecording && (
          <Text style={styles.recordingTime}>
            {formatTime(recordingTime)}
          </Text>
        )}
      </View>
      
      <TouchableOpacity
        style={[styles.recordButton, isRecording && styles.recordingButton]}
        onPress={isRecording ? stopRecording : startRecording}
      >
        <Text style={styles.recordButtonText}>
          {isRecording ? 'Stop Recording' : 'Start Recording'}
        </Text>
      </TouchableOpacity>
      
      {selectedFile && (
        <View style={styles.audioPlayer}>
          <TouchableOpacity onPress={togglePlayback} style={styles.playButton}>
            <Icon name={isPlaying ? "pause" : "play-arrow"} size={30} color="#fff" />
          </TouchableOpacity>
          <Text style={styles.fileName}>{selectedFile.name}</Text>
        </View>
      )}
    </View>
  );

  // Render upload interface
  const renderUploadInterface = () => (
    <View style={styles.uploadContainer}>
      <TouchableOpacity style={styles.uploadButton} onPress={pickFile}>
        <Icon name="cloud-upload" size={40} color="#666" />
        <Text style={styles.uploadText}>Select Audio File</Text>
        <Text style={styles.uploadSubtext}>MP3, WAV, M4A (max 25MB)</Text>
      </TouchableOpacity>
      
      {selectedFile && (
        <View style={styles.selectedFile}>
          <Icon name="audio-file" size={24} color="#4CAF50" />
          <View style={styles.fileInfo}>
            <Text style={styles.fileName}>{selectedFile.name}</Text>
            <Text style={styles.fileSize}>
              {selectedFile.size ? `${(selectedFile.size / 1024 / 1024).toFixed(2)} MB` : 'Unknown size'}
            </Text>
          </View>
          <TouchableOpacity onPress={togglePlayback} style={styles.playButton}>
            <Icon name={isPlaying ? "pause" : "play-arrow"} size={24} color="#fff" />
          </TouchableOpacity>
        </View>
      )}
    </View>
  );

  // Render settings modal
  const renderSettingsModal = () => (
    <Modal
      visible={showSettings}
      animationType="slide"
      presentationStyle="pageSheet"
    >
      <View style={styles.modalContainer}>
        <View style={styles.modalHeader}>
          <Text style={styles.modalTitle}>Settings</Text>
          <TouchableOpacity onPress={() => setShowSettings(false)}>
            <Icon name="close" size={24} color="#666" />
          </TouchableOpacity>
        </View>
        
        <ScrollView style={styles.settingsContent}>
          <View style={styles.settingItem}>
            <Text style={styles.settingLabel}>Temperature: {config.temperature}</Text>
            <Slider
              style={styles.slider}
              minimumValue={0}
              maximumValue={1}
              value={config.temperature}
              onValueChange={(value) => saveConfig({...config, temperature: value})}
              step={0.1}
              minimumTrackTintColor="#4CAF50"
              maximumTrackTintColor="#ddd"
            />
          </View>
          
          <View style={styles.settingItem}>
            <Text style={styles.settingLabel}>Confidence Threshold: {config.confidence_threshold}</Text>
            <Slider
              style={styles.slider}
              minimumValue={0}
              maximumValue={1}
              value={config.confidence_threshold}
              onValueChange={(value) => saveConfig({...config, confidence_threshold: value})}
              step={0.05}
              minimumTrackTintColor="#4CAF50"
              maximumTrackTintColor="#ddd"
            />
          </View>
          
          <View style={styles.switchItem}>
            <Text style={styles.settingLabel}>Language Detection</Text>
            <Switch
              value={config.enable_language_detection}
              onValueChange={(value) => saveConfig({...config, enable_language_detection: value})}
              trackColor={{ false: "#ddd", true: "#4CAF50" }}
            />
          </View>
          
          <View style={styles.switchItem}>
            <Text style={styles.settingLabel}>Confidence Analysis</Text>
            <Switch
              value={config.enable_confidence_analysis}
              onValueChange={(value) => saveConfig({...config, enable_confidence_analysis: value})}
              trackColor={{ false: "#ddd", true: "#4CAF50" }}
            />
          </View>
          
          <View style={styles.switchItem}>
            <Text style={styles.settingLabel}>Word Timestamps</Text>
            <Switch
              value={config.enable_word_timestamps}
              onValueChange={(value) => saveConfig({...config, enable_word_timestamps: value})}
              trackColor={{ false: "#ddd", true: "#4CAF50" }}
            />
          </View>
          
          <View style={styles.switchItem}>
            <Text style={styles.settingLabel}>Speaker Detection</Text>
            <Switch
              value={config.enable_speaker_detection}
              onValueChange={(value) => saveConfig({...config, enable_speaker_detection: value})}
              trackColor={{ false: "#ddd", true: "#4CAF50" }}
            />
          </View>
        </ScrollView>
      </View>
    </Modal>
  );

  // Render results
  const renderResults = () => {
    if (!result) return null;

    return (
      <View style={styles.resultsContainer}>
        <View style={styles.resultsHeader}>
          <Text style={styles.resultsTitle}>Transcription Results</Text>
          <View style={styles.resultsActions}>
            <TouchableOpacity onPress={() => copyToClipboard(result.text)} style={styles.actionButton}>
              <Icon name="content-copy" size={20} color="#666" />
            </TouchableOpacity>
            <TouchableOpacity onPress={shareResult} style={styles.actionButton}>
              <Icon name="share" size={20} color="#666" />
            </TouchableOpacity>
          </View>
        </View>
        
        <View style={styles.metricsContainer}>
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>Processing Time</Text>
            <Text style={styles.metricValue}>{result.processing_time.toFixed(2)}s</Text>
          </View>
          {result.language && (
            <View style={styles.metric}>
              <Text style={styles.metricLabel}>Language</Text>
              <Text style={styles.metricValue}>
                {result.language.toUpperCase()}
                {result.language_confidence && 
                  ` (${(result.language_confidence * 100).toFixed(1)}%)`
                }
              </Text>
            </View>
          )}
          {result.confidence_analysis && (
            <View style={styles.metric}>
              <Text style={styles.metricLabel}>Confidence</Text>
              <Text style={styles.metricValue}>
                {(result.confidence_analysis.overall_confidence * 100).toFixed(1)}%
              </Text>
            </View>
          )}
        </View>
        
        <ScrollView style={styles.transcriptionText}>
          <Text style={styles.transcriptionContent}>{result.text}</Text>
        </ScrollView>
        
        {result.segments && result.segments.length > 0 && (
          <View style={styles.segmentsContainer}>
            <Text style={styles.segmentsTitle}>Segments</Text>
            <ScrollView style={styles.segmentsList}>
              {result.segments.map((segment) => (
                <View key={segment.id} style={styles.segment}>
                  <View style={styles.segmentHeader}>
                    <Text style={styles.segmentTime}>
                      {formatTime(segment.start)} - {formatTime(segment.end)}
                    </Text>
                    {segment.confidence && (
                      <Text style={styles.segmentConfidence}>
                        {(segment.confidence * 100).toFixed(1)}%
                      </Text>
                    )}
                    {segment.speaker_id && (
                      <Text style={styles.speakerId}>{segment.speaker_id}</Text>
                    )}
                  </View>
                  <Text style={styles.segmentText}>{segment.text}</Text>
                </View>
              ))}
            </ScrollView>
          </View>
        )}
      </View>
    );
  };

  // Render language detection results
  const renderLanguageResults = () => {
    if (!languageResult) return null;

    return (
      <View style={styles.languageResultsContainer}>
        <Text style={styles.resultsTitle}>Language Detection Results</Text>
        
        <View style={styles.primaryLanguage}>
          <Text style={styles.primaryLanguageText}>
            {languageResult.detected_language.toUpperCase()}
          </Text>
          <Text style={styles.primaryLanguageConfidence}>
            {(languageResult.confidence * 100).toFixed(1)}% confidence
          </Text>
        </View>
        
        {languageResult.alternative_languages && languageResult.alternative_languages.length > 0 && (
          <View style={styles.alternativeLanguages}>
            <Text style={styles.alternativeTitle}>Alternative Languages</Text>
            {languageResult.alternative_languages.slice(0, 5).map((langObj, index) => {
              const [lang, confidence] = Object.entries(langObj)[0];
              return (
                <View key={index} style={styles.alternativeLanguage}>
                  <Text style={styles.alternativeLanguageText}>{lang.toUpperCase()}</Text>
                  <Text style={styles.alternativeLanguageConfidence}>
                    {(confidence * 100).toFixed(1)}%
                  </Text>
                </View>
              );
            })}
          </View>
        )}
      </View>
    );
  };

  return (
    <Animated.View style={[styles.container, { opacity: fadeAnim }]}>
      <View style={styles.header}>
        <Text style={styles.title}>Whisper Advanced</Text>
        <View style={styles.headerActions}>
          <View style={[styles.statusIndicator, { backgroundColor: isOnline ? '#4CAF50' : '#ff4444' }]} />
          <TouchableOpacity onPress={() => setShowSettings(true)} style={styles.settingsButton}>
            <Icon name="settings" size={24} color="#666" />
          </TouchableOpacity>
        </View>
      </View>

      {renderModeTabs()}

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {processingMode === 'record' && renderRecordingInterface()}
        {processingMode === 'upload' && renderUploadInterface()}
        
        {(processingMode === 'record' || processingMode === 'upload') && (
          <View style={styles.actionContainer}>
            <TouchableOpacity
              style={[styles.transcribeButton, (!selectedFile || isTranscribing) && styles.disabledButton]}
              onPress={handleTranscribe}
              disabled={!selectedFile || isTranscribing}
            >
              {isTranscribing ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Icon name="transcribe" size={20} color="#fff" />
              )}
              <Text style={styles.transcribeButtonText}>
                {isTranscribing ? 'Transcribing...' : 'Transcribe Audio'}
              </Text>
            </TouchableOpacity>
          </View>
        )}

        {processingMode === 'language' && (
          <View style={styles.languageContainer}>
            {renderUploadInterface()}
            <TouchableOpacity
              style={[styles.detectButton, (!selectedFile || isDetectingLanguage) && styles.disabledButton]}
              onPress={handleLanguageDetection}
              disabled={!selectedFile || isDetectingLanguage}
            >
              {isDetectingLanguage ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Icon name="language" size={20} color="#fff" />
              )}
              <Text style={styles.detectButtonText}>
                {isDetectingLanguage ? 'Detecting...' : 'Detect Language'}
              </Text>
            </TouchableOpacity>
          </View>
        )}

        {error && (
          <View style={styles.errorContainer}>
            <Icon name="error" size={20} color="#ff4444" />
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {processingMode === 'language' ? renderLanguageResults() : renderResults()}
      </ScrollView>

      {renderSettingsModal()}
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: Platform.OS === 'ios' ? 50 : 20,
    paddingBottom: 15,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 15,
  },
  settingsButton: {
    padding: 5,
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 15,
    backgroundColor: '#fff',
  },
  activeTab: {
    backgroundColor: '#4CAF50',
  },
  tabText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  activeTabText: {
    color: '#fff',
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  recordingContainer: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  recordingVisualizer: {
    alignItems: 'center',
    marginBottom: 30,
  },
  recordingTime: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ff4444',
    marginTop: 10,
  },
  recordButton: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 25,
    minWidth: 200,
    alignItems: 'center',
  },
  recordingButton: {
    backgroundColor: '#ff4444',
  },
  recordButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  uploadContainer: {
    paddingVertical: 40,
  },
  uploadButton: {
    borderWidth: 2,
    borderColor: '#ddd',
    borderStyle: 'dashed',
    borderRadius: 10,
    paddingVertical: 40,
    alignItems: 'center',
    backgroundColor: '#fafafa',
  },
  uploadText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#666',
    marginTop: 10,
  },
  uploadSubtext: {
    fontSize: 12,
    color: '#999',
    marginTop: 5,
  },
  selectedFile: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 10,
    marginTop: 20,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  fileInfo: {
    flex: 1,
    marginLeft: 10,
  },
  fileName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  fileSize: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  audioPlayer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 10,
    marginTop: 20,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  playButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 20,
    padding: 8,
    marginRight: 10,
  },
  actionContainer: {
    paddingVertical: 20,
  },
  transcribeButton: {
    backgroundColor: '#2196F3',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 15,
    borderRadius: 10,
  },
  transcribeButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  languageContainer: {
    paddingVertical: 20,
  },
  detectButton: {
    backgroundColor: '#FF9800',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 15,
    borderRadius: 10,
    marginTop: 20,
  },
  detectButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  disabledButton: {
    backgroundColor: '#ccc',
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffebee',
    padding: 15,
    borderRadius: 10,
    marginVertical: 10,
    borderLeftWidth: 4,
    borderLeftColor: '#ff4444',
  },
  errorText: {
    color: '#ff4444',
    marginLeft: 10,
    flex: 1,
  },
  resultsContainer: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 20,
    marginVertical: 20,
  },
  resultsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  resultsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  resultsActions: {
    flexDirection: 'row',
  },
  actionButton: {
    padding: 8,
    marginLeft: 10,
  },
  metricsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 20,
    paddingVertical: 15,
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
  },
  metric: {
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
  },
  transcriptionText: {
    maxHeight: 200,
    marginBottom: 20,
  },
  transcriptionContent: {
    fontSize: 16,
    lineHeight: 24,
    color: '#333',
  },
  segmentsContainer: {
    marginTop: 20,
  },
  segmentsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  segmentsList: {
    maxHeight: 300,
  },
  segment: {
    backgroundColor: '#f8f9fa',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
  },
  segmentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 5,
  },
  segmentTime: {
    fontSize: 12,
    color: '#666',
    fontWeight: '500',
  },
  segmentConfidence: {
    fontSize: 12,
    color: '#4CAF50',
    fontWeight: '500',
  },
  speakerId: {
    fontSize: 12,
    color: '#2196F3',
    fontWeight: '500',
  },
  segmentText: {
    fontSize: 14,
    color: '#333',
    lineHeight: 20,
  },
  languageResultsContainer: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 20,
    marginVertical: 20,
  },
  primaryLanguage: {
    alignItems: 'center',
    paddingVertical: 20,
    backgroundColor: '#e8f5e8',
    borderRadius: 10,
    marginBottom: 20,
  },
  primaryLanguageText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#4CAF50',
  },
  primaryLanguageConfidence: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },
  alternativeLanguages: {
    marginTop: 10,
  },
  alternativeTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  alternativeLanguage: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: '#f8f9fa',
    borderRadius: 6,
    marginBottom: 5,
  },
  alternativeLanguageText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#333',
  },
  alternativeLanguageConfidence: {
    fontSize: 12,
    color: '#666',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#fff',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: Platform.OS === 'ios' ? 50 : 20,
    paddingBottom: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  settingsContent: {
    flex: 1,
    paddingHorizontal: 20,
  },
  settingItem: {
    paddingVertical: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  settingLabel: {
    fontSize: 16,
    color: '#333',
    marginBottom: 10,
  },
  slider: {
    width: '100%',
    height: 40,
  },
  switchItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
});

export default WhisperAdvancedMobile;