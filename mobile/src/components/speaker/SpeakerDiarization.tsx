import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  Modal,
  Dimensions,
  Platform,
} from 'react-native';
import {
  LineChart,
  BarChart,
  PieChart,
} from 'react-native-chart-kit';
import Slider from '@react-native-community/slider';
import { Audio } from 'expo-av';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Feather } from '@expo/vector-icons';

interface SpeakerSegment {
  start: number;
  end: number;
  speaker: string;
  confidence: number;
  text?: string;
  embedding?: number[];
}

interface SpeakerProfile {
  id: string;
  name: string;
  color: string;
  totalDuration: number;
  segmentCount: number;
  averageConfidence: number;
  voiceCharacteristics?: {
    pitch: number;
    energy: number;
    spectralCentroid: number;
  };
}

interface DiarizationResult {
  speakers: SpeakerProfile[];
  segments: SpeakerSegment[];
  totalDuration: number;
  confidence: number;
  method: string;
}

interface SpeakerDiarizationProps {
  audioUrl?: string;
  transcriptData?: any;
  onSpeakerUpdate?: (speakers: SpeakerProfile[]) => void;
  onSegmentClick?: (segment: SpeakerSegment) => void;
}

const { width: screenWidth } = Dimensions.get('window');

const SPEAKER_COLORS = [
  '#3b82f6', '#ef4444', '#10b981', '#f59e0b', 
  '#8b5cf6', '#06b6d4', '#f97316', '#84cc16',
  '#ec4899', '#14b8a6', '#f43f5e', '#6366f1'
];

const SpeakerDiarization: React.FC<SpeakerDiarizationProps> = ({
  audioUrl,
  transcriptData,
  onSpeakerUpdate,
  onSegmentClick,
}) => {
  const [diarizationResult, setDiarizationResult] = useState<DiarizationResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [selectedSpeaker, setSelectedSpeaker] = useState<SpeakerProfile | null>(null);
  const [newSpeakerName, setNewSpeakerName] = useState('');
  const [diarizationMethod, setDiarizationMethod] = useState('whisperx');
  const [minSpeakers, setMinSpeakers] = useState(2);
  const [maxSpeakers, setMaxSpeakers] = useState(10);
  const [sound, setSound] = useState<Audio.Sound | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [settingsModalVisible, setSettingsModalVisible] = useState(false);

  const processDiarization = async () => {
    if (!audioUrl) {
      Alert.alert('Error', 'No audio URL provided');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      const token = await AsyncStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/api/speaker-diarization/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          audio_url: audioUrl,
          method: diarizationMethod,
          min_speakers: minSpeakers,
          max_speakers: maxSpeakers,
          transcript_data: transcriptData,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to process speaker diarization');
      }

      const result = await response.json();
      setDiarizationResult(result);
      onSpeakerUpdate?.(result.speakers);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Diarization failed';
      setError(errorMessage);
      Alert.alert('Error', errorMessage);
    } finally {
      setIsProcessing(false);
    }
  };

  const updateSpeakerName = async (speakerId: string, newName: string) => {
    if (!diarizationResult) return;

    try {
      const token = await AsyncStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/api/speaker-diarization/update-speaker', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          speaker_id: speakerId,
          new_name: newName,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to update speaker name');
      }

      // Update local state
      const updatedResult = {
        ...diarizationResult,
        speakers: diarizationResult.speakers.map(speaker =>
          speaker.id === speakerId ? { ...speaker, name: newName } : speaker
        ),
        segments: diarizationResult.segments.map(segment =>
          segment.speaker === speakerId ? { ...segment, speaker: newName } : segment
        ),
      };

      setDiarizationResult(updatedResult);
      onSpeakerUpdate?.(updatedResult.speakers);
      Alert.alert('Success', 'Speaker name updated');
    } catch (err) {
      Alert.alert('Error', err instanceof Error ? err.message : 'Failed to update speaker');
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    if (mins > 0) {
      return `${mins}m ${secs}s`;
    }
    return `${secs}s`;
  };

  const getSpeakerStats = () => {
    if (!diarizationResult) return [];

    return diarizationResult.speakers.map(speaker => ({
      name: speaker.name,
      duration: speaker.totalDuration,
      percentage: (speaker.totalDuration / diarizationResult.totalDuration) * 100,
      segments: speaker.segmentCount,
      color: speaker.color,
    }));
  };

  const handleEditSpeaker = (speaker: SpeakerProfile) => {
    setSelectedSpeaker(speaker);
    setNewSpeakerName(speaker.name);
    setEditModalVisible(true);
  };

  const handleSaveEdit = () => {
    if (selectedSpeaker && newSpeakerName.trim()) {
      updateSpeakerName(selectedSpeaker.id, newSpeakerName.trim());
      setEditModalVisible(false);
      setSelectedSpeaker(null);
      setNewSpeakerName('');
    }
  };

  const exportDiarization = async () => {
    if (!diarizationResult) return;

    const exportData = {
      speakers: diarizationResult.speakers,
      segments: diarizationResult.segments,
      metadata: {
        totalDuration: diarizationResult.totalDuration,
        confidence: diarizationResult.confidence,
        method: diarizationResult.method,
        exportedAt: new Date().toISOString(),
      },
    };

    try {
      await AsyncStorage.setItem(
        `diarization_export_${Date.now()}`,
        JSON.stringify(exportData)
      );
      Alert.alert('Success', 'Diarization data exported successfully');
    } catch (err) {
      Alert.alert('Error', 'Failed to export diarization data');
    }
  };

  const playPauseAudio = async () => {
    if (!sound) return;

    if (isPlaying) {
      await sound.pauseAsync();
      setIsPlaying(false);
    } else {
      await sound.playAsync();
      setIsPlaying(true);
    }
  };

  const loadAudio = async () => {
    if (!audioUrl) return;

    try {
      const { sound } = await Audio.Sound.createAsync(
        { uri: audioUrl },
        { shouldPlay: false }
      );
      setSound(sound);

      sound.setOnPlaybackStatusUpdate((status) => {
        if (status.isLoaded) {
          setCurrentTime(status.positionMillis / 1000);
          if (status.didJustFinish) {
            setIsPlaying(false);
          }
        }
      });
    } catch (err) {
      Alert.alert('Error', 'Failed to load audio');
    }
  };

  useEffect(() => {
    if (audioUrl && !diarizationResult && !isProcessing) {
      processDiarization();
    }
  }, [audioUrl]);

  useEffect(() => {
    loadAudio();

    return () => {
      if (sound) {
        sound.unloadAsync();
      }
    };
  }, [audioUrl]);

  const renderSettings = () => (
    <Modal
      animationType="slide"
      transparent={true}
      visible={settingsModalVisible}
      onRequestClose={() => setSettingsModalVisible(false)}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          <Text style={styles.modalTitle}>Diarization Settings</Text>
          
          <Text style={styles.label}>Method</Text>
          <View style={styles.methodSelector}>
            {['whisperx', 'pyannote', 'resemblyzer'].map((method) => (
              <TouchableOpacity
                key={method}
                style={[
                  styles.methodOption,
                  diarizationMethod === method && styles.methodOptionActive
                ]}
                onPress={() => setDiarizationMethod(method)}
              >
                <Text style={[
                  styles.methodOptionText,
                  diarizationMethod === method && styles.methodOptionTextActive
                ]}>
                  {method === 'whisperx' ? 'WhisperX' : method === 'pyannote' ? 'PyAnnote' : 'Resemblyzer'}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={styles.label}>Min Speakers: {minSpeakers}</Text>
          <Slider
            style={styles.slider}
            minimumValue={1}
            maximumValue={20}
            step={1}
            value={minSpeakers}
            onValueChange={setMinSpeakers}
            minimumTrackTintColor="#3b82f6"
            maximumTrackTintColor="#d1d5db"
          />

          <Text style={styles.label}>Max Speakers: {maxSpeakers}</Text>
          <Slider
            style={styles.slider}
            minimumValue={1}
            maximumValue={20}
            step={1}
            value={maxSpeakers}
            onValueChange={setMaxSpeakers}
            minimumTrackTintColor="#3b82f6"
            maximumTrackTintColor="#d1d5db"
          />

          <View style={styles.modalButtons}>
            <TouchableOpacity
              style={[styles.modalButton, styles.modalButtonCancel]}
              onPress={() => setSettingsModalVisible(false)}
            >
              <Text style={styles.modalButtonText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.modalButton, styles.modalButtonConfirm]}
              onPress={() => {
                setSettingsModalVisible(false);
                processDiarization();
              }}
            >
              <Text style={styles.modalButtonTextLight}>Apply & Process</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );

  const renderEditModal = () => (
    <Modal
      animationType="slide"
      transparent={true}
      visible={editModalVisible}
      onRequestClose={() => setEditModalVisible(false)}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          <Text style={styles.modalTitle}>Edit Speaker Name</Text>
          <TextInput
            style={styles.input}
            value={newSpeakerName}
            onChangeText={setNewSpeakerName}
            placeholder="Enter speaker name"
            autoFocus
          />
          <View style={styles.modalButtons}>
            <TouchableOpacity
              style={[styles.modalButton, styles.modalButtonCancel]}
              onPress={() => setEditModalVisible(false)}
            >
              <Text style={styles.modalButtonText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.modalButton, styles.modalButtonConfirm]}
              onPress={handleSaveEdit}
            >
              <Text style={styles.modalButtonTextLight}>Save</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );

  if (error) {
    return (
      <View style={styles.errorContainer}>
        <Feather name="alert-circle" size={48} color="#ef4444" />
        <Text style={styles.errorTitle}>Speaker Diarization Failed</Text>
        <Text style={styles.errorMessage}>{error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={processDiarization}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Feather name="mic" size={24} color="#3b82f6" />
          <Text style={styles.title}>Speaker Diarization</Text>
        </View>
        <View style={styles.headerRight}>
          <TouchableOpacity
            style={styles.iconButton}
            onPress={() => setSettingsModalVisible(true)}
          >
            <Feather name="settings" size={20} color="#6b7280" />
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.iconButton}
            onPress={processDiarization}
            disabled={isProcessing}
          >
            <Feather
              name="refresh-cw"
              size={20}
              color="#6b7280"
              style={isProcessing ? styles.rotating : null}
            />
          </TouchableOpacity>
          {diarizationResult && (
            <TouchableOpacity style={styles.iconButton} onPress={exportDiarization}>
              <Feather name="download" size={20} color="#6b7280" />
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Processing Status */}
      {isProcessing && (
        <View style={styles.processingContainer}>
          <ActivityIndicator size="large" color="#3b82f6" />
          <Text style={styles.processingText}>Processing Speaker Diarization...</Text>
          <Text style={styles.processingSubtext}>
            Analyzing audio for speaker identification using {diarizationMethod}
          </Text>
        </View>
      )}

      {/* Configuration */}
      {!diarizationResult && !isProcessing && (
        <View style={styles.configContainer}>
          <Text style={styles.sectionTitle}>Diarization Settings</Text>
          <TouchableOpacity
            style={styles.configButton}
            onPress={() => setSettingsModalVisible(true)}
          >
            <Text style={styles.configButtonText}>Configure Settings</Text>
            <Feather name="chevron-right" size={20} color="#3b82f6" />
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.primaryButton, !audioUrl && styles.disabledButton]}
            onPress={processDiarization}
            disabled={!audioUrl}
          >
            <Text style={styles.primaryButtonText}>Start Diarization</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Results */}
      {diarizationResult && (
        <>
          {/* Overview Stats */}
          <View style={styles.statsGrid}>
            <View style={styles.statCard}>
              <Feather name="users" size={24} color="#3b82f6" />
              <Text style={styles.statValue}>{diarizationResult.speakers.length}</Text>
              <Text style={styles.statLabel}>Speakers</Text>
            </View>
            <View style={styles.statCard}>
              <Feather name="clock" size={24} color="#10b981" />
              <Text style={styles.statValue}>{formatDuration(diarizationResult.totalDuration)}</Text>
              <Text style={styles.statLabel}>Duration</Text>
            </View>
            <View style={styles.statCard}>
              <Feather name="activity" size={24} color="#8b5cf6" />
              <Text style={styles.statValue}>{diarizationResult.segments.length}</Text>
              <Text style={styles.statLabel}>Segments</Text>
            </View>
            <View style={styles.statCard}>
              <Feather name="trending-up" size={24} color="#f59e0b" />
              <Text style={styles.statValue}>{(diarizationResult.confidence * 100).toFixed(0)}%</Text>
              <Text style={styles.statLabel}>Confidence</Text>
            </View>
          </View>

          {/* Audio Controls */}
          {audioUrl && sound && (
            <View style={styles.audioControls}>
              <TouchableOpacity style={styles.playButton} onPress={playPauseAudio}>
                <Feather name={isPlaying ? 'pause' : 'play'} size={24} color="white" />
              </TouchableOpacity>
              <View style={styles.progressContainer}>
                <Text style={styles.timeText}>{formatTime(currentTime)}</Text>
                <View style={styles.progressBar}>
                  <View
                    style={[
                      styles.progressFill,
                      { width: `${(currentTime / diarizationResult.totalDuration) * 100}%` }
                    ]}
                  />
                </View>
                <Text style={styles.timeText}>{formatTime(diarizationResult.totalDuration)}</Text>
              </View>
            </View>
          )}

          {/* Speaker Timeline */}
          <View style={styles.timelineContainer}>
            <Text style={styles.sectionTitle}>Speaker Timeline</Text>
            <View style={styles.timeline}>
              {diarizationResult.segments.map((segment, index) => {
                const speaker = diarizationResult.speakers.find(s => s.name === segment.speaker);
                const left = (segment.start / diarizationResult.totalDuration) * 100;
                const width = ((segment.end - segment.start) / diarizationResult.totalDuration) * 100;

                return (
                  <TouchableOpacity
                    key={index}
                    style={[
                      styles.timelineSegment,
                      {
                        left: `${left}%`,
                        width: `${width}%`,
                        backgroundColor: speaker?.color || '#gray',
                      }
                    ]}
                    onPress={() => onSegmentClick?.(segment)}
                  />
                );
              })}
            </View>
            <View style={styles.timelineLabels}>
              <Text style={styles.timelineLabel}>0:00</Text>
              <Text style={styles.timelineLabel}>{formatTime(diarizationResult.totalDuration)}</Text>
            </View>
          </View>

          {/* Speaker Distribution Chart */}
          <View style={styles.chartContainer}>
            <Text style={styles.sectionTitle}>Speaking Time Distribution</Text>
            <PieChart
              data={getSpeakerStats().map(stat => ({
                name: stat.name,
                population: stat.duration,
                color: stat.color,
                legendFontColor: '#7F7F7F',
                legendFontSize: 12,
              }))}
              width={screenWidth - 32}
              height={200}
              chartConfig={{
                backgroundColor: '#ffffff',
                backgroundGradientFrom: '#ffffff',
                backgroundGradientTo: '#ffffff',
                color: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
              }}
              accessor="population"
              backgroundColor="transparent"
              paddingLeft="15"
            />
          </View>

          {/* Speaker Profiles */}
          <View style={styles.profilesContainer}>
            <Text style={styles.sectionTitle}>Speaker Profiles</Text>
            {diarizationResult.speakers.map((speaker, index) => (
              <View key={speaker.id} style={styles.profileCard}>
                <View style={styles.profileHeader}>
                  <View style={[styles.profileAvatar, { backgroundColor: speaker.color }]}>
                    <Text style={styles.profileAvatarText}>
                      {speaker.name.charAt(0).toUpperCase()}
                    </Text>
                  </View>
                  <View style={styles.profileInfo}>
                    <Text style={styles.profileName}>{speaker.name}</Text>
                    <View style={styles.profileStats}>
                      <Text style={styles.profileStat}>
                        {formatDuration(speaker.totalDuration)}
                      </Text>
                      <Text style={styles.profileStatSeparator}>•</Text>
                      <Text style={styles.profileStat}>
                        {speaker.segmentCount} segments
                      </Text>
                      <Text style={styles.profileStatSeparator}>•</Text>
                      <Text style={styles.profileStat}>
                        {(speaker.averageConfidence * 100).toFixed(0)}% conf.
                      </Text>
                    </View>
                    {speaker.voiceCharacteristics && (
                      <View style={styles.voiceChars}>
                        <View style={styles.voiceCharChip}>
                          <Text style={styles.voiceCharText}>
                            Pitch: {speaker.voiceCharacteristics.pitch.toFixed(0)}Hz
                          </Text>
                        </View>
                        <View style={styles.voiceCharChip}>
                          <Text style={styles.voiceCharText}>
                            Energy: {speaker.voiceCharacteristics.energy.toFixed(1)}
                          </Text>
                        </View>
                      </View>
                    )}
                  </View>
                  <TouchableOpacity
                    style={styles.editButton}
                    onPress={() => handleEditSpeaker(speaker)}
                  >
                    <Feather name="edit-2" size={18} color="#6b7280" />
                  </TouchableOpacity>
                </View>
              </View>
            ))}
          </View>
        </>
      )}

      {renderSettings()}
      {renderEditModal()}
    </ScrollView>
  );
};

const styles = {
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
    marginLeft: 8,
    color: '#111827',
  },
  iconButton: {
    padding: 8,
    marginLeft: 8,
  },
  rotating: {
    transform: [{ rotate: '360deg' }],
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginTop: 16,
    marginBottom: 8,
  },
  errorMessage: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
    marginBottom: 24,
  },
  retryButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: '#ef4444',
    borderRadius: 8,
  },
  retryButtonText: {
    color: 'white',
    fontWeight: '600',
  },
  processingContainer: {
    padding: 32,
    alignItems: 'center',
  },
  processingText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginTop: 16,
  },
  processingSubtext: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 8,
    textAlign: 'center',
  },
  configContainer: {
    padding: 16,
    backgroundColor: 'white',
    margin: 16,
    borderRadius: 12,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
  },
  configButton: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: '#f3f4f6',
    borderRadius: 8,
    marginBottom: 16,
  },
  configButtonText: {
    fontSize: 14,
    color: '#3b82f6',
    fontWeight: '500',
  },
  primaryButton: {
    backgroundColor: '#3b82f6',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  primaryButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  disabledButton: {
    opacity: 0.5,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 8,
    marginTop: 8,
  },
  statCard: {
    width: (screenWidth - 48) / 2,
    backgroundColor: 'white',
    padding: 16,
    margin: 8,
    borderRadius: 12,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: '700',
    color: '#111827',
    marginTop: 8,
  },
  statLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 4,
  },
  audioControls: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: 'white',
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: 12,
  },
  playButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#3b82f6',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  progressContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  progressBar: {
    flex: 1,
    height: 4,
    backgroundColor: '#e5e7eb',
    borderRadius: 2,
    marginHorizontal: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#3b82f6',
    borderRadius: 2,
  },
  timeText: {
    fontSize: 12,
    color: '#6b7280',
  },
  timelineContainer: {
    padding: 16,
    backgroundColor: 'white',
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: 12,
  },
  timeline: {
    height: 60,
    backgroundColor: '#f3f4f6',
    borderRadius: 8,
    position: 'relative',
    overflow: 'hidden',
  },
  timelineSegment: {
    position: 'absolute',
    height: '100%',
    opacity: 0.8,
  },
  timelineLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  timelineLabel: {
    fontSize: 12,
    color: '#6b7280',
  },
  chartContainer: {
    padding: 16,
    backgroundColor: 'white',
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: 12,
  },
  profilesContainer: {
    padding: 16,
  },
  profileCard: {
    backgroundColor: 'white',
    padding: 16,
    marginBottom: 12,
    borderRadius: 12,
  },
  profileHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  profileAvatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  profileAvatarText: {
    color: 'white',
    fontSize: 20,
    fontWeight: '600',
  },
  profileInfo: {
    flex: 1,
  },
  profileName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  profileStats: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  profileStat: {
    fontSize: 12,
    color: '#6b7280',
  },
  profileStatSeparator: {
    fontSize: 12,
    color: '#d1d5db',
    marginHorizontal: 6,
  },
  voiceChars: {
    flexDirection: 'row',
    marginTop: 8,
  },
  voiceCharChip: {
    backgroundColor: '#f3f4f6',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    marginRight: 8,
  },
  voiceCharText: {
    fontSize: 11,
    color: '#6b7280',
  },
  editButton: {
    padding: 8,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 24,
    width: screenWidth - 48,
    maxWidth: 400,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16,
  },
  input: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    fontSize: 16,
    marginBottom: 16,
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
  },
  modalButton: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    marginLeft: 12,
  },
  modalButtonCancel: {
    backgroundColor: '#f3f4f6',
  },
  modalButtonConfirm: {
    backgroundColor: '#3b82f6',
  },
  modalButtonText: {
    color: '#6b7280',
    fontWeight: '500',
  },
  modalButtonTextLight: {
    color: 'white',
    fontWeight: '500',
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    marginBottom: 8,
    marginTop: 16,
  },
  methodSelector: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  methodOption: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    backgroundColor: '#f3f4f6',
    marginHorizontal: 4,
    borderRadius: 8,
  },
  methodOptionActive: {
    backgroundColor: '#3b82f6',
  },
  methodOptionText: {
    fontSize: 14,
    color: '#6b7280',
  },
  methodOptionTextActive: {
    color: 'white',
    fontWeight: '500',
  },
  slider: {
    width: '100%',
    height: 40,
  },
};

export default SpeakerDiarization;