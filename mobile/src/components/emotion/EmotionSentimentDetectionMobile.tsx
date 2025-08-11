import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  StyleSheet,
  Dimensions,
  Platform
} from 'react-native';
import { Audio } from 'expo-av';
import * as DocumentPicker from 'expo-document-picker';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import Slider from '@react-native-community/slider';

interface EmotionResult {
  timestamp: number;
  duration: number;
  primary_emotion: string;
  emotion_scores: Record<string, number>;
  confidence: number;
  intensity: number;
  speaker_id?: string;
  audio_features?: Record<string, number>;
  text_content?: string;
}

interface SentimentResult {
  timestamp: number;
  duration: number;
  polarity: string;
  sentiment_score: number;
  confidence: number;
  subjectivity: number;
  speaker_id?: string;
  text_content?: string;
  keywords: string[];
}

interface AnalysisResult {
  emotions: EmotionResult[];
  sentiments: SentimentResult[];
  overall_emotion: string;
  overall_sentiment: string;
  emotion_timeline: any[];
  sentiment_timeline: any[];
  statistics: Record<string, any>;
  processing_time: number;
  total_duration: number;
  config_used: any;
}

interface EmotionConfig {
  detection_mode: string;
  model_type: string;
  language: string;
  confidence_threshold: number;
  enable_audio_analysis: boolean;
  enable_text_analysis: boolean;
  enable_temporal_analysis: boolean;
  segment_duration: number;
  overlap_duration: number;
  enable_speaker_emotion: boolean;
}

const { width } = Dimensions.get('window');

const EmotionSentimentDetectionMobile: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [transcriptText, setTranscriptText] = useState('');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [models, setModels] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('audio');
  
  // Configuration state
  const [config, setConfig] = useState<EmotionConfig>({
    detection_mode: 'both',
    model_type: 'transformer',
    language: 'en',
    confidence_threshold: 0.5,
    enable_audio_analysis: true,
    enable_text_analysis: true,
    enable_temporal_analysis: true,
    segment_duration: 2.0,
    overlap_duration: 0.5,
    enable_speaker_emotion: true
  });
  
  // Audio playback
  const [sound, setSound] = useState<Audio.Sound | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [position, setPosition] = useState(0);
  const [duration, setDuration] = useState(0);
  
  // Text analysis
  const [textInput, setTextInput] = useState('');
  const [textSentiments, setTextSentiments] = useState<SentimentResult[]>([]);

  useEffect(() => {
    loadModels();
    return () => {
      if (sound) {
        sound.unloadAsync();
      }
    };
  }, []);

  const loadModels = async () => {
    try {
      const response = await fetch('/api/v1/emotion-sentiment/models');
      if (response.ok) {
        const data = await response.json();
        setModels(data.data);
      }
    } catch (error) {
      console.error('Failed to load models:', error);
    }
  };

  const pickAudioFile = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: 'audio/*',
        copyToCacheDirectory: true,
      });

      if (!result.canceled && result.assets[0]) {
        setSelectedFile(result.assets[0]);
        setResult(null);
        setError(null);
        
        // Load audio for playback
        const { sound } = await Audio.Sound.createAsync(
          { uri: result.assets[0].uri },
          { shouldPlay: false }
        );
        setSound(sound);
        
        const status = await sound.getStatusAsync();
        if (status.isLoaded) {
          setDuration(status.durationMillis || 0);
        }
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to pick audio file');
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) {
      Alert.alert('Error', 'Please select an audio file');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('audio_file', {
        uri: selectedFile.uri,
        type: selectedFile.mimeType || 'audio/wav',
        name: selectedFile.name || 'audio.wav',
      } as any);
      
      formData.append('config', JSON.stringify(config));
      
      if (transcriptText) {
        formData.append('transcript_text', transcriptText);
      }
      
      formData.append('include_timeline', 'true');
      formData.append('include_statistics', 'true');

      const response = await fetch('/api/v1/emotion-sentiment/analyze', {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to analyze emotion and sentiment');
      }

      const data = await response.json();
      setResult(data.data);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'An error occurred');
      Alert.alert('Error', error instanceof Error ? error.message : 'An error occurred');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const analyzeTextSentiment = async () => {
    if (!textInput.trim()) {
      Alert.alert('Error', 'Please enter text to analyze');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('text', textInput);
      formData.append('language', config.language);
      formData.append('model_type', config.model_type);

      const response = await fetch('/api/v1/emotion-sentiment/analyze-text', {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to analyze text sentiment');
      }

      const data = await response.json();
      setTextSentiments(data.data);
    } catch (error) {
      Alert.alert('Error', error instanceof Error ? error.message : 'An error occurred');
    }
  };

  const togglePlayback = async () => {
    if (!sound) return;

    try {
      if (isPlaying) {
        await sound.pauseAsync();
      } else {
        await sound.playAsync();
      }
      setIsPlaying(!isPlaying);
    } catch (error) {
      console.error('Playback error:', error);
    }
  };

  const formatTime = (milliseconds: number) => {
    const seconds = Math.floor(milliseconds / 1000);
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getEmotionIcon = (emotion: string) => {
    switch (emotion.toLowerCase()) {
      case 'joy':
      case 'happy':
      case 'positive':
        return 'happy-outline';
      case 'sadness':
      case 'sad':
      case 'negative':
        return 'sad-outline';
      case 'anger':
      case 'angry':
        return 'flash-outline';
      case 'fear':
      case 'fearful':
        return 'heart-outline';
      default:
        return 'remove-circle-outline';
    }
  };

  const getSentimentIcon = (polarity: string) => {
    switch (polarity.toLowerCase()) {
      case 'positive':
        return 'trending-up-outline';
      case 'negative':
        return 'trending-down-outline';
      default:
        return 'remove-circle-outline';
    }
  };

  const getEmotionColor = (emotion: string) => {
    switch (emotion.toLowerCase()) {
      case 'joy':
      case 'happy':
        return '#FCD34D';
      case 'sadness':
      case 'sad':
        return '#60A5FA';
      case 'anger':
      case 'angry':
        return '#F87171';
      case 'fear':
      case 'fearful':
        return '#A78BFA';
      case 'surprise':
      case 'surprised':
        return '#FB923C';
      case 'disgust':
      case 'disgusted':
        return '#34D399';
      default:
        return '#9CA3AF';
    }
  };

  const getSentimentColor = (polarity: string) => {
    switch (polarity.toLowerCase()) {
      case 'positive':
        return '#10B981';
      case 'negative':
        return '#EF4444';
      default:
        return '#6B7280';
    }
  };

  const renderTabButton = (tab: string, label: string, icon: string) => (
    <TouchableOpacity
      style={[styles.tabButton, activeTab === tab && styles.activeTab]}
      onPress={() => setActiveTab(tab)}
    >
      <Ionicons 
        name={icon as any} 
        size={20} 
        color={activeTab === tab ? '#3B82F6' : '#6B7280'} 
      />
      <Text style={[styles.tabText, activeTab === tab && styles.activeTabText]}>
        {label}
      </Text>
    </TouchableOpacity>
  );

  const renderAudioAnalysis = () => (
    <ScrollView style={styles.tabContent}>
      {/* File Upload */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Audio File Upload</Text>
        
        <TouchableOpacity style={styles.uploadButton} onPress={pickAudioFile}>
          <Ionicons name="cloud-upload-outline" size={24} color="#3B82F6" />
          <Text style={styles.uploadButtonText}>Select Audio File</Text>
        </TouchableOpacity>

        {selectedFile && (
          <View style={styles.fileInfo}>
            <View style={styles.fileDetails}>
              <Text style={styles.fileName}>{selectedFile.name}</Text>
              <Text style={styles.fileSize}>
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </Text>
            </View>
            <TouchableOpacity
              style={styles.playButton}
              onPress={togglePlayback}
            >
              <Ionicons 
                name={isPlaying ? 'pause' : 'play'} 
                size={20} 
                color="#FFFFFF" 
              />
            </TouchableOpacity>
          </View>
        )}

        {duration > 0 && (
          <View style={styles.audioControls}>
            <View style={styles.timeLabels}>
              <Text style={styles.timeText}>{formatTime(position)}</Text>
              <Text style={styles.timeText}>{formatTime(duration)}</Text>
            </View>
            <View style={styles.progressBar}>
              <View 
                style={[
                  styles.progressFill, 
                  { width: `${(position / duration) * 100}%` }
                ]} 
              />
            </View>
          </View>
        )}

        <TextInput
          style={styles.textArea}
          value={transcriptText}
          onChangeText={setTranscriptText}
          placeholder="Optional transcript for enhanced analysis..."
          multiline
          numberOfLines={4}
          textAlignVertical="top"
        />

        <TouchableOpacity
          style={[styles.analyzeButton, (!selectedFile || isAnalyzing) && styles.disabledButton]}
          onPress={handleAnalyze}
          disabled={!selectedFile || isAnalyzing}
        >
          {isAnalyzing ? (
            <ActivityIndicator color="#FFFFFF" />
          ) : (
            <Ionicons name="brain" size={20} color="#FFFFFF" />
          )}
          <Text style={styles.analyzeButtonText}>
            {isAnalyzing ? 'Analyzing...' : 'Analyze Emotion & Sentiment'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Results */}
      {result && (
        <View style={styles.resultsContainer}>
          {/* Overall Results */}
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Overall Analysis</Text>
            
            <View style={styles.overallResults}>
              <View style={styles.resultItem}>
                <Text style={styles.resultLabel}>Primary Emotion</Text>
                <View style={styles.resultValue}>
                  <Ionicons 
                    name={getEmotionIcon(result.overall_emotion) as any} 
                    size={20} 
                    color={getEmotionColor(result.overall_emotion)} 
                  />
                  <Text style={[styles.resultText, { color: getEmotionColor(result.overall_emotion) }]}>
                    {result.overall_emotion}
                  </Text>
                </View>
              </View>
              
              <View style={styles.resultItem}>
                <Text style={styles.resultLabel}>Overall Sentiment</Text>
                <View style={styles.resultValue}>
                  <Ionicons 
                    name={getSentimentIcon(result.overall_sentiment) as any} 
                    size={20} 
                    color={getSentimentColor(result.overall_sentiment)} 
                  />
                  <Text style={[styles.resultText, { color: getSentimentColor(result.overall_sentiment) }]}>
                    {result.overall_sentiment}
                  </Text>
                </View>
              </View>
            </View>

            <View style={styles.statsGrid}>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{result.emotions.length}</Text>
                <Text style={styles.statLabel}>Emotion Segments</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{result.sentiments.length}</Text>
                <Text style={styles.statLabel}>Sentiment Segments</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{result.processing_time.toFixed(2)}s</Text>
                <Text style={styles.statLabel}>Processing Time</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{result.total_duration.toFixed(1)}s</Text>
                <Text style={styles.statLabel}>Audio Duration</Text>
              </View>
            </View>
          </View>

          {/* Detailed Results */}
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Emotion Analysis Results</Text>
            {result.emotions.map((emotion, index) => (
              <View key={index} style={styles.emotionItem}>
                <View style={styles.emotionHeader}>
                  <View style={styles.emotionInfo}>
                    <Ionicons 
                      name={getEmotionIcon(emotion.primary_emotion) as any} 
                      size={16} 
                      color={getEmotionColor(emotion.primary_emotion)} 
                    />
                    <Text style={[styles.emotionLabel, { color: getEmotionColor(emotion.primary_emotion) }]}>
                      {emotion.primary_emotion}
                    </Text>
                    <Text style={styles.timeStamp}>
                      {formatTime(emotion.timestamp * 1000)} - {formatTime((emotion.timestamp + emotion.duration) * 1000)}
                    </Text>
                  </View>
                  <View style={styles.confidenceInfo}>
                    <Text style={styles.confidenceText}>
                      {(emotion.confidence * 100).toFixed(1)}%
                    </Text>
                  </View>
                </View>
                
                {emotion.text_content && (
                  <View style={styles.textContent}>
                    <Text style={styles.textContentText}>{emotion.text_content}</Text>
                  </View>
                )}
              </View>
            ))}
          </View>

          <View style={styles.card}>
            <Text style={styles.cardTitle}>Sentiment Analysis Results</Text>
            {result.sentiments.map((sentiment, index) => (
              <View key={index} style={styles.sentimentItem}>
                <View style={styles.sentimentHeader}>
                  <View style={styles.sentimentInfo}>
                    <Ionicons 
                      name={getSentimentIcon(sentiment.polarity) as any} 
                      size={16} 
                      color={getSentimentColor(sentiment.polarity)} 
                    />
                    <Text style={[styles.sentimentLabel, { color: getSentimentColor(sentiment.polarity) }]}>
                      {sentiment.polarity}
                    </Text>
                    <Text style={styles.timeStamp}>
                      {formatTime(sentiment.timestamp * 1000)} - {formatTime((sentiment.timestamp + sentiment.duration) * 1000)}
                    </Text>
                  </View>
                  <View style={styles.scoreInfo}>
                    <Text style={styles.scoreText}>
                      {sentiment.sentiment_score.toFixed(2)}
                    </Text>
                  </View>
                </View>
                
                {sentiment.keywords.length > 0 && (
                  <View style={styles.keywords}>
                    {sentiment.keywords.map((keyword, idx) => (
                      <View key={idx} style={styles.keyword}>
                        <Text style={styles.keywordText}>{keyword}</Text>
                      </View>
                    ))}
                  </View>
                )}
                
                {sentiment.text_content && (
                  <View style={styles.textContent}>
                    <Text style={styles.textContentText}>{sentiment.text_content}</Text>
                  </View>
                )}
              </View>
            ))}
          </View>
        </View>
      )}
    </ScrollView>
  );

  const renderTextAnalysis = () => (
    <ScrollView style={styles.tabContent}>
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Text Sentiment Analysis</Text>
        
        <TextInput
          style={styles.textArea}
          value={textInput}
          onChangeText={setTextInput}
          placeholder="Enter text for sentiment analysis..."
          multiline
          numberOfLines={6}
          textAlignVertical="top"
        />

        <TouchableOpacity
          style={[styles.analyzeButton, !textInput.trim() && styles.disabledButton]}
          onPress={analyzeTextSentiment}
          disabled={!textInput.trim()}
        >
          <Ionicons name="brain" size={20} color="#FFFFFF" />
          <Text style={styles.analyzeButtonText}>Analyze Text Sentiment</Text>
        </TouchableOpacity>

        {textSentiments.length > 0 && (
          <View style={styles.textResults}>
            <Text style={styles.resultsTitle}>Text Sentiment Results</Text>
            {textSentiments.map((sentiment, index) => (
              <View key={index} style={styles.sentimentItem}>
                <View style={styles.sentimentHeader}>
                  <View style={styles.sentimentInfo}>
                    <Ionicons 
                      name={getSentimentIcon(sentiment.polarity) as any} 
                      size={16} 
                      color={getSentimentColor(sentiment.polarity)} 
                    />
                    <Text style={[styles.sentimentLabel, { color: getSentimentColor(sentiment.polarity) }]}>
                      {sentiment.polarity}
                    </Text>
                  </View>
                  <View style={styles.scoreInfo}>
                    <Text style={styles.scoreText}>
                      {sentiment.sentiment_score.toFixed(2)}
                    </Text>
                  </View>
                </View>
                
                {sentiment.keywords.length > 0 && (
                  <View style={styles.keywords}>
                    {sentiment.keywords.map((keyword, idx) => (
                      <View key={idx} style={styles.keyword}>
                        <Text style={styles.keywordText}>{keyword}</Text>
                      </View>
                    ))}
                  </View>
                )}
              </View>
            ))}
          </View>
        )}
      </View>
    </ScrollView>
  );

  const renderSettings = () => (
    <ScrollView style={styles.tabContent}>
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Analysis Configuration</Text>
        
        <View style={styles.settingItem}>
          <Text style={styles.settingLabel}>Detection Mode</Text>
          <View style={styles.segmentedControl}>
            {['emotion', 'sentiment', 'both'].map((mode) => (
              <TouchableOpacity
                key={mode}
                style={[
                  styles.segmentButton,
                  config.detection_mode === mode && styles.activeSegment
                ]}
                onPress={() => setConfig({...config, detection_mode: mode})}
              >
                <Text style={[
                  styles.segmentText,
                  config.detection_mode === mode && styles.activeSegmentText
                ]}>
                  {mode.charAt(0).toUpperCase() + mode.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <View style={styles.settingItem}>
          <Text style={styles.settingLabel}>Model Type</Text>
          <View style={styles.segmentedControl}>
            {['transformer', 'cnn', 'svm'].map((model) => (
              <TouchableOpacity
                key={model}
                style={[
                  styles.segmentButton,
                  config.model_type === model && styles.activeSegment
                ]}
                onPress={() => setConfig({...config, model_type: model})}
              >
                <Text style={[
                  styles.segmentText,
                  config.model_type === model && styles.activeSegmentText
                ]}>
                  {model.toUpperCase()}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <View style={styles.settingItem}>
          <Text style={styles.settingLabel}>
            Confidence Threshold: {config.confidence_threshold.toFixed(1)}
          </Text>
          <Slider
            style={styles.slider}
            minimumValue={0}
            maximumValue={1}
            step={0.1}
            value={config.confidence_threshold}
            onValueChange={(value) => setConfig({...config, confidence_threshold: value})}
            minimumTrackTintColor="#3B82F6"
            maximumTrackTintColor="#E5E7EB"
            thumbStyle={styles.sliderThumb}
          />
        </View>

        <View style={styles.settingItem}>
          <Text style={styles.settingLabel}>
            Segment Duration: {config.segment_duration.toFixed(1)}s
          </Text>
          <Slider
            style={styles.slider}
            minimumValue={0.5}
            maximumValue={10}
            step={0.5}
            value={config.segment_duration}
            onValueChange={(value) => setConfig({...config, segment_duration: value})}
            minimumTrackTintColor="#3B82F6"
            maximumTrackTintColor="#E5E7EB"
            thumbStyle={styles.sliderThumb}
          />
        </View>

        <View style={styles.settingItem}>
          <Text style={styles.settingLabel}>
            Overlap Duration: {config.overlap_duration.toFixed(1)}s
          </Text>
          <Slider
            style={styles.slider}
            minimumValue={0}
            maximumValue={2}
            step={0.1}
            value={config.overlap_duration}
            onValueChange={(value) => setConfig({...config, overlap_duration: value})}
            minimumTrackTintColor="#3B82F6"
            maximumTrackTintColor="#E5E7EB"
            thumbStyle={styles.sliderThumb}
          />
        </View>

        <View style={styles.switchContainer}>
          <Text style={styles.cardTitle}>Analysis Options</Text>
          
          {[
            { key: 'enable_audio_analysis', label: 'Enable Audio Analysis' },
            { key: 'enable_text_analysis', label: 'Enable Text Analysis' },
            { key: 'enable_temporal_analysis', label: 'Enable Temporal Analysis' },
            { key: 'enable_speaker_emotion', label: 'Enable Speaker Emotion' },
          ].map((option) => (
            <View key={option.key} style={styles.switchItem}>
              <Text style={styles.switchLabel}>{option.label}</Text>
              <TouchableOpacity
                style={[
                  styles.switch,
                  config[option.key as keyof EmotionConfig] && styles.switchActive
                ]}
                onPress={() => setConfig({
                  ...config,
                  [option.key]: !config[option.key as keyof EmotionConfig]
                })}
              >
                <View style={[
                  styles.switchThumb,
                  config[option.key as keyof EmotionConfig] && styles.switchThumbActive
                ]} />
              </TouchableOpacity>
            </View>
          ))}
        </View>
      </View>
    </ScrollView>
  );

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['#3B82F6', '#1D4ED8']}
        style={styles.header}
      >
        <Text style={styles.headerTitle}>Emotion & Sentiment Detection</Text>
        <Text style={styles.headerSubtitle}>
          Analyze emotions from voice and sentiment from text
        </Text>
      </LinearGradient>

      <View style={styles.tabContainer}>
        {renderTabButton('audio', 'Audio', 'volume-high-outline')}
        {renderTabButton('text', 'Text', 'document-text-outline')}
        {renderTabButton('settings', 'Settings', 'settings-outline')}
      </View>

      {activeTab === 'audio' && renderAudioAnalysis()}
      {activeTab === 'text' && renderTextAnalysis()}
      {activeTab === 'settings' && renderSettings()}

      {error && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    padding: 20,
    paddingTop: Platform.OS === 'ios' ? 60 : 40,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFFFFF',
    textAlign: 'center',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#E5E7EB',
    textAlign: 'center',
    marginTop: 4,
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  tabButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    gap: 8,
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#3B82F6',
  },
  tabText: {
    fontSize: 14,
    color: '#6B7280',
  },
  activeTabText: {
    color: '#3B82F6',
    fontWeight: '600',
  },
  tabContent: {
    flex: 1,
    padding: 16,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 16,
  },
  uploadButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F3F4F6',
    borderWidth: 2,
    borderColor: '#D1D5DB',
    borderStyle: 'dashed',
    borderRadius: 8,
    padding: 20,
    gap: 8,
  },
  uploadButtonText: {
    fontSize: 16,
    color: '#3B82F6',
    fontWeight: '500',
  },
  fileInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#F9FAFB',
    padding: 12,
    borderRadius: 8,
    marginTop: 12,
  },
  fileDetails: {
    flex: 1,
  },
  fileName: {
    fontSize: 14,
    fontWeight: '500',
    color: '#1F2937',
  },
  fileSize: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  playButton: {
    backgroundColor: '#3B82F6',
    borderRadius: 20,
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  audioControls: {
    marginTop: 12,
  },
  timeLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  timeText: {
    fontSize: 12,
    color: '#6B7280',
  },
  progressBar: {
    height: 4,
    backgroundColor: '#E5E7EB',
    borderRadius: 2,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#3B82F6',
    borderRadius: 2,
  },
  textArea: {
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    color: '#1F2937',
    backgroundColor: '#FFFFFF',
    marginTop: 12,
    minHeight: 80,
  },
  analyzeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#3B82F6',
    borderRadius: 8,
    padding: 16,
    marginTop: 16,
    gap: 8,
  },
  disabledButton: {
    backgroundColor: '#9CA3AF',
  },
  analyzeButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  resultsContainer: {
    marginTop: 16,
  },
  overallResults: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  resultItem: {
    flex: 1,
    alignItems: 'center',
  },
  resultLabel: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 8,
  },
  resultValue: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  resultText: {
    fontSize: 16,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statItem: {
    width: '48%',
    alignItems: 'center',
    marginBottom: 12,
  },
  statValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#3B82F6',
  },
  statLabel: {
    fontSize: 12,
    color: '#6B7280',
    textAlign: 'center',
    marginTop: 4,
  },
  emotionItem: {
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  emotionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  emotionInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: 8,
  },
  emotionLabel: {
    fontSize: 14,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  timeStamp: {
    fontSize: 12,
    color: '#6B7280',
  },
  confidenceInfo: {
    alignItems: 'flex-end',
  },
  confidenceText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#1F2937',
  },
  sentimentItem: {
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  sentimentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  sentimentInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: 8,
  },
  sentimentLabel: {
    fontSize: 14,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  scoreInfo: {
    alignItems: 'flex-end',
  },
  scoreText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#1F2937',
  },
  keywords: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: 8,
  },
  keyword: {
    backgroundColor: '#F3F4F6',
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  keywordText: {
    fontSize: 12,
    color: '#4B5563',
  },
  textContent: {
    backgroundColor: '#F9FAFB',
    borderRadius: 6,
    padding: 8,
    marginTop: 8,
  },
  textContentText: {
    fontSize: 12,
    color: '#4B5563',
  },
  textResults: {
    marginTop: 16,
  },
  resultsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 12,
  },
  settingItem: {
    marginBottom: 20,
  },
  settingLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#1F2937',
    marginBottom: 8,
  },
  segmentedControl: {
    flexDirection: 'row',
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    padding: 2,
  },
  segmentButton: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    alignItems: 'center',
  },
  activeSegment: {
    backgroundColor: '#3B82F6',
  },
  segmentText: {
    fontSize: 12,
    color: '#6B7280',
    fontWeight: '500',
  },
  activeSegmentText: {
    color: '#FFFFFF',
  },
  slider: {
    width: '100%',
    height: 40,
  },
  sliderThumb: {
    backgroundColor: '#3B82F6',
    width: 20,
    height: 20,
  },
  switchContainer: {
    marginTop: 20,
  },
  switchItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
  },
  switchLabel: {
    fontSize: 14,
    color: '#1F2937',
    flex: 1,
  },
  switch: {
    width: 50,
    height: 30,
    borderRadius: 15,
    backgroundColor: '#E5E7EB',
    justifyContent: 'center',
    paddingHorizontal: 2,
  },
  switchActive: {
    backgroundColor: '#3B82F6',
  },
  switchThumb: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: '#FFFFFF',
    alignSelf: 'flex-start',
  },
  switchThumbActive: {
    alignSelf: 'flex-end',
  },
  errorContainer: {
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#FECACA',
    borderRadius: 8,
    padding: 12,
    margin: 16,
  },
  errorText: {
    fontSize: 14,
    color: '#DC2626',
    textAlign: 'center',
  },
});

export default EmotionSentimentDetectionMobile;