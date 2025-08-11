import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
  Share,
  Dimensions,
  Animated,
} from 'react-native';
import { Picker } from '@react-native-picker/picker';
import { Switch } from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { styles } from './styles';

interface TranscriptionSegment {
  text: string;
  start_time: number;
  end_time: number;
  confidence: number;
  is_final: boolean;
  speaker_id?: string;
  language?: string;
  engine?: string;
}

interface StreamingStats {
  total_audio_duration: number;
  total_processing_time: number;
  segments_processed: number;
  average_latency: number;
  confidence_scores: number[];
  error_count: number;
}

interface StreamingConfig {
  engine: string;
  language: string;
  sample_rate: number;
  chunk_duration: number;
  buffer_duration: number;
  overlap_duration: number;
  confidence_threshold: number;
  enable_vad: boolean;
  enable_speaker_diarization: boolean;
  streaming_mode: string;
}

const { width } = Dimensions.get('window');

const RealTimeTranscriptionMobile: React.FC = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [segments, setSegments] = useState<TranscriptionSegment[]>([]);
  const [currentSegment, setCurrentSegment] = useState<TranscriptionSegment | null>(null);
  const [stats, setStats] = useState<StreamingStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Configuration state
  const [config, setConfig] = useState<StreamingConfig>({
    engine: 'whisper_api',
    language: 'en',
    sample_rate: 16000,
    chunk_duration: 1.0,
    buffer_duration: 5.0,
    overlap_duration: 0.5,
    confidence_threshold: 0.7,
    enable_vad: true,
    enable_speaker_diarization: false,
    streaming_mode: 'continuous'
  });
  
  // Audio state
  const [audioLevel, setAudioLevel] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  
  // Animation
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const audioLevelAnim = useRef(new Animated.Value(0)).current;
  
  // Refs
  const websocketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    return () => {
      cleanup();
    };
  }, []);

  // Pulse animation for recording button
  useEffect(() => {
    if (isRecording) {
      const pulse = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.2,
            duration: 1000,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 1000,
            useNativeDriver: true,
          }),
        ])
      );
      pulse.start();
      return () => pulse.stop();
    } else {
      pulseAnim.setValue(1);
    }
  }, [isRecording]);

  // Audio level animation
  useEffect(() => {
    Animated.timing(audioLevelAnim, {
      toValue: audioLevel / 100,
      duration: 100,
      useNativeDriver: false,
    }).start();
  }, [audioLevel]);

  const cleanup = () => {
    if (websocketRef.current) {
      websocketRef.current.close();
    }
  };

  const createSession = async () => {
    try {
      const response = await fetch('/api/v1/realtime-transcription/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          config: config,
          session_name: `Mobile Session ${new Date().toLocaleTimeString()}`
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create session');
      }

      const data = await response.json();
      setSessionId(data.data.session_id);
      return data.data.session_id;
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to create session');
      throw error;
    }
  };

  const connectWebSocket = (sessionId: string) => {
    const wsUrl = `ws://localhost:8000/api/v1/realtime-transcription/ws/${sessionId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setIsConnected(true);
      setError(null);
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      switch (message.type) {
        case 'connected':
          console.log('Session connected:', message.session_id);
          break;
          
        case 'transcription':
          const segment = message.data as TranscriptionSegment;
          if (segment.is_final) {
            setSegments(prev => [...prev, segment]);
            setCurrentSegment(null);
          } else {
            setCurrentSegment(segment);
          }
          break;
          
        case 'stats':
          setStats(message.data as StreamingStats);
          break;
          
        case 'error':
          setError(message.message);
          break;
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
    };

    ws.onerror = (error) => {
      setError('WebSocket connection error');
      console.error('WebSocket error:', error);
    };

    websocketRef.current = ws;
  };

  const startRecording = async () => {
    try {
      // Create session if not exists
      let currentSessionId = sessionId;
      if (!currentSessionId) {
        currentSessionId = await createSession();
      }

      // Connect WebSocket
      if (!isConnected) {
        connectWebSocket(currentSessionId);
      }

      // Note: In a real implementation, you would need to use a React Native
      // audio recording library like react-native-audio-recorder-player
      // or react-native-sound-recorder for actual audio capture

      setIsRecording(true);
      setError(null);

      // Simulate audio level for demo
      const audioLevelInterval = setInterval(() => {
        setAudioLevel(Math.random() * 100);
      }, 100);

      // Send start recording signal
      websocketRef.current?.send(JSON.stringify({
        type: 'start_recording'
      }));

    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to start recording');
      console.error('Error starting recording:', error);
    }
  };

  const stopRecording = () => {
    // Send stop recording signal
    websocketRef.current?.send(JSON.stringify({
      type: 'stop_recording'
    }));

    setIsRecording(false);
    setAudioLevel(0);
  };

  const toggleMute = () => {
    setIsMuted(!isMuted);
  };

  const clearTranscription = () => {
    setSegments([]);
    setCurrentSegment(null);
    setStats(null);
  };

  const shareTranscription = async () => {
    const fullText = segments.map(segment => segment.text).join(' ');
    if (fullText) {
      try {
        await Share.share({
          message: `Real-time Transcript:\n\n${fullText}`,
          title: 'Transcription'
        });
      } catch (error) {
        console.error('Error sharing:', error);
      }
    }
  };

  const getFullTranscript = () => {
    const allText = segments.map(segment => segment.text).join(' ');
    if (currentSegment) {
      return allText + ' ' + currentSegment.text;
    }
    return allText;
  };

  const getAverageConfidence = () => {
    if (segments.length === 0) return 0;
    const total = segments.reduce((sum, segment) => sum + segment.confidence, 0);
    return total / segments.length;
  };

  const renderAudioLevelIndicator = () => {
    return (
      <View style={styles.audioLevelContainer}>
        <Text style={styles.audioLevelLabel}>Audio Level</Text>
        <View style={styles.audioLevelBar}>
          <Animated.View 
            style={[
              styles.audioLevelFill,
              {
                width: audioLevelAnim.interpolate({
                  inputRange: [0, 1],
                  outputRange: ['0%', '100%'],
                }),
                backgroundColor: audioLevel > 70 ? '#EF4444' : audioLevel > 40 ? '#F59E0B' : '#10B981'
              }
            ]} 
          />
        </View>
        <Text style={styles.audioLevelValue}>{Math.round(audioLevel)}%</Text>
      </View>
    );
  };

  const renderConnectionStatus = () => {
    return (
      <View style={[styles.connectionStatus, isConnected ? styles.connected : styles.disconnected]}>
        <Icon 
          name={isConnected ? "wifi" : "wifi-off"} 
          size={16} 
          color={isConnected ? "#10B981" : "#EF4444"} 
        />
        <Text style={[styles.connectionText, { color: isConnected ? "#10B981" : "#EF4444" }]}>
          {isConnected ? 'Connected' : 'Disconnected'}
        </Text>
      </View>
    );
  };

  const renderRecordingButton = () => {
    return (
      <View style={styles.recordingButtonContainer}>
        <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
          <TouchableOpacity
            style={[
              styles.recordingButton,
              isRecording ? styles.recordingButtonActive : styles.recordingButtonInactive
            ]}
            onPress={isRecording ? stopRecording : startRecording}
            disabled={!isConnected && !sessionId}
          >
            <Icon 
              name={isRecording ? "stop" : "mic"} 
              size={32} 
              color="#fff" 
            />
          </TouchableOpacity>
        </Animated.View>
        
        <TouchableOpacity
          style={styles.muteButton}
          onPress={toggleMute}
          disabled={!isRecording}
        >
          <Icon 
            name={isMuted ? "volume-off" : "volume-up"} 
            size={24} 
            color={!isRecording ? "#9CA3AF" : "#374151"} 
          />
        </TouchableOpacity>
      </View>
    );
  };

  const renderTranscriptionSegment = (segment: TranscriptionSegment, index: number) => {
    return (
      <View key={index} style={styles.segmentContainer}>
        {segment.speaker_id && (
          <View style={styles.speakerBadge}>
            <Text style={styles.speakerText}>{segment.speaker_id}</Text>
          </View>
        )}
        <Text style={styles.segmentText}>{segment.text}</Text>
        <View style={styles.segmentMeta}>
          <Text style={styles.segmentTime}>
            {segment.start_time.toFixed(1)}s - {segment.end_time.toFixed(1)}s
          </Text>
          <Text style={styles.segmentConfidence}>
            {(segment.confidence * 100).toFixed(1)}% confidence
          </Text>
          {segment.engine && (
            <Text style={styles.segmentEngine}>{segment.engine}</Text>
          )}
        </View>
      </View>
    );
  };

  const renderStats = () => {
    if (!stats) return null;

    return (
      <View style={styles.statsContainer}>
        <View style={styles.statsGrid}>
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>{stats.segments_processed}</Text>
            <Text style={styles.statLabel}>Segments</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>{stats.average_latency.toFixed(1)}ms</Text>
            <Text style={styles.statLabel}>Avg Latency</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>{(getAverageConfidence() * 100).toFixed(1)}%</Text>
            <Text style={styles.statLabel}>Confidence</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>{stats.total_audio_duration.toFixed(1)}s</Text>
            <Text style={styles.statLabel}>Duration</Text>
          </View>
        </View>
      </View>
    );
  };

  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Icon name="record-voice-over" size={24} color="#EF4444" />
          <Text style={styles.title}>Real-Time Transcription</Text>
        </View>
        {renderConnectionStatus()}
      </View>

      {/* Main Content */}
      <View style={styles.mainContent}>
        {/* Recording Controls */}
        <View style={styles.controlsCard}>
          {renderRecordingButton()}
          {renderAudioLevelIndicator()}
          
          <View style={styles.actionButtons}>
            <TouchableOpacity 
              style={styles.actionButton} 
              onPress={() => setShowSettings(!showSettings)}
            >
              <Icon name="settings" size={20} color="#6B7280" />
              <Text style={styles.actionButtonText}>Settings</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.actionButton} 
              onPress={clearTranscription}
            >
              <Icon name="clear" size={20} color="#6B7280" />
              <Text style={styles.actionButtonText}>Clear</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.actionButton} 
              onPress={shareTranscription}
              disabled={segments.length === 0}
            >
              <Icon name="share" size={20} color={segments.length === 0 ? "#9CA3AF" : "#6B7280"} />
              <Text style={[styles.actionButtonText, segments.length === 0 && styles.disabledText]}>
                Share
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Settings Panel */}
        {showSettings && (
          <View style={styles.settingsCard}>
            <Text style={styles.settingsTitle}>Configuration</Text>
            
            <View style={styles.settingItem}>
              <Text style={styles.settingLabel}>Engine</Text>
              <Picker
                selectedValue={config.engine}
                onValueChange={(value) => setConfig(prev => ({ ...prev, engine: value }))}
                style={styles.picker}
                enabled={!isRecording}
              >
                <Picker.Item label="Whisper API" value="whisper_api" />
                <Picker.Item label="Whisper Local" value="whisper_local" />
                <Picker.Item label="Vosk" value="vosk" />
                <Picker.Item label="Google Speech" value="google_speech" />
                <Picker.Item label="Azure Speech" value="azure_speech" />
              </Picker>
            </View>

            <View style={styles.settingItem}>
              <Text style={styles.settingLabel}>Language</Text>
              <Picker
                selectedValue={config.language}
                onValueChange={(value) => setConfig(prev => ({ ...prev, language: value }))}
                style={styles.picker}
                enabled={!isRecording}
              >
                <Picker.Item label="English" value="en" />
                <Picker.Item label="Spanish" value="es" />
                <Picker.Item label="French" value="fr" />
                <Picker.Item label="German" value="de" />
                <Picker.Item label="Italian" value="it" />
                <Picker.Item label="Portuguese" value="pt" />
                <Picker.Item label="Russian" value="ru" />
                <Picker.Item label="Japanese" value="ja" />
                <Picker.Item label="Korean" value="ko" />
                <Picker.Item label="Chinese" value="zh" />
              </Picker>
            </View>

            <View style={styles.switchContainer}>
              <View style={styles.switchRow}>
                <Text style={styles.switchLabel}>Voice Activity Detection</Text>
                <Switch
                  value={config.enable_vad}
                  onValueChange={(value) => setConfig(prev => ({ ...prev, enable_vad: value }))}
                  disabled={isRecording}
                  trackColor={{ false: '#767577', true: '#3B82F6' }}
                  thumbColor={config.enable_vad ? '#fff' : '#f4f3f4'}
                />
              </View>

              <View style={styles.switchRow}>
                <Text style={styles.switchLabel}>Speaker Diarization</Text>
                <Switch
                  value={config.enable_speaker_diarization}
                  onValueChange={(value) => setConfig(prev => ({ ...prev, enable_speaker_diarization: value }))}
                  disabled={isRecording}
                  trackColor={{ false: '#767577', true: '#3B82F6' }}
                  thumbColor={config.enable_speaker_diarization ? '#fff' : '#f4f3f4'}
                />
              </View>
            </View>
          </View>
        )}

        {/* Transcription Display */}
        <View style={styles.transcriptionCard}>
          <View style={styles.transcriptionHeader}>
            <Text style={styles.transcriptionTitle}>Live Transcription</Text>
            <View style={styles.transcriptionStats}>
              <Text style={styles.transcriptionStatsText}>
                {segments.length} segments • {getFullTranscript().split(' ').length} words
              </Text>
            </View>
          </View>

          <ScrollView style={styles.transcriptionContent}>
            {segments.length === 0 && !currentSegment ? (
              <View style={styles.emptyState}>
                <Icon name="mic" size={48} color="#9CA3AF" />
                <Text style={styles.emptyStateText}>Start recording to see live transcription</Text>
              </View>
            ) : (
              <View style={styles.segmentsContainer}>
                {segments.map((segment, index) => renderTranscriptionSegment(segment, index))}
                
                {currentSegment && (
                  <View style={[styles.segmentContainer, styles.liveSegment]}>
                    <View style={styles.liveBadge}>
                      <Text style={styles.liveText}>Live</Text>
                    </View>
                    <Text style={[styles.segmentText, styles.liveSegmentText]}>
                      {currentSegment.text}
                    </Text>
                  </View>
                )}
              </View>
            )}
          </ScrollView>

          {renderStats()}
        </View>

        {/* Error Display */}
        {error && (
          <View style={styles.errorContainer}>
            <Icon name="error" size={20} color="#EF4444" />
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}
      </View>
    </ScrollView>
  );
};

export default RealTimeTranscriptionMobile;