import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Share,
  Dimensions,
  ActivityIndicator,
  Modal,
  TextInput,
  Animated,
} from 'react-native';
import { MaterialIcons } from '@expo/vector-icons';
import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';
import TranscriptionService from '../services/TranscriptionService';

const { width, height } = Dimensions.get('window');

export default function TranscriptionScreen({ route, navigation }) {
  const { file, transcriptionId, transcriptionData, source } = route.params;
  
  const [transcription, setTranscription] = useState(transcriptionData || null);
  const [loading, setLoading] = useState(!transcriptionData);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [sound, setSound] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1.0);
  const [showTranscript, setShowTranscript] = useState(true);
  const [showSpeakers, setShowSpeakers] = useState(false);
  const [showTimestamps, setShowTimestamps] = useState(false);
  const [selectedSegment, setSelectedSegment] = useState(null);
  const [searchVisible, setSearchVisible] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [currentSearchIndex, setCurrentSearchIndex] = useState(0);
  const progressBarWidth = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (file && !transcriptionData) {
      startTranscription();
    } else if (transcriptionId && !transcriptionData) {
      loadTranscription();
    }
    
    return () => {
      if (sound) {
        sound.unloadAsync();
      }
    };
  }, []);

  useEffect(() => {
    if (transcription?.audio_file_url) {
      setupAudio();
    }
  }, [transcription]);

  useEffect(() => {
    searchInTranscript();
  }, [searchQuery, transcription]);

  const startTranscription = async () => {
    setProcessing(true);
    setProgress(0);
    
    try {
      const result = await TranscriptionService.startTranscription(
        file,
        'advanced', // Default to advanced mode
        (progressValue) => {
          setProgress(progressValue);
          Animated.timing(progressBarWidth, {
            toValue: progressValue * (width - 32),
            duration: 200,
            useNativeDriver: false,
          }).start();
        }
      );
      
      if (result) {
        const transcriptionData = await TranscriptionService.getTranscriptionResult(result);
        setTranscription(transcriptionData);
        setProgress(1);
      }
    } catch (error) {
      console.error('Transcription failed:', error);
      Alert.alert('Error', error.message || 'Transcription failed');
      navigation.goBack();
    } finally {
      setProcessing(false);
    }
  };

  const loadTranscription = async () => {
    setLoading(true);
    
    try {
      const data = await TranscriptionService.getTranscriptionResult(transcriptionId);
      setTranscription(data);
    } catch (error) {
      console.error('Failed to load transcription:', error);
      Alert.alert('Error', 'Failed to load transcription');
      navigation.goBack();
    } finally {
      setLoading(false);
    }
  };

  const setupAudio = async () => {
    try {
      const { sound: newSound } = await Audio.Sound.createAsync(
        { uri: transcription.audio_file_url },
        { shouldPlay: false, isLooping: false },
        onPlaybackStatusUpdate
      );
      setSound(newSound);
    } catch (error) {
      console.warn('Failed to setup audio playback:', error);
    }
  };

  const onPlaybackStatusUpdate = (status) => {
    if (status.isLoaded) {
      setCurrentTime(status.positionMillis / 1000);
      setDuration(status.durationMillis / 1000);
      setIsPlaying(status.isPlaying);
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
    } catch (error) {
      console.error('Playback error:', error);
    }
  };

  const seekTo = async (time) => {
    if (!sound) return;

    try {
      await sound.setPositionAsync(time * 1000);
      setCurrentTime(time);
    } catch (error) {
      console.error('Seek error:', error);
    }
  };

  const changePlaybackRate = async (rate) => {
    if (!sound) return;

    try {
      await sound.setRateAsync(rate, true);
      setPlaybackRate(rate);
    } catch (error) {
      console.error('Rate change error:', error);
    }
  };

  const jumpToSegment = (segment) => {
    if (segment.start_time !== undefined) {
      seekTo(segment.start_time);
      setSelectedSegment(segment);
    }
  };

  const searchInTranscript = () => {
    if (!searchQuery.trim() || !transcription?.transcript) {
      setSearchResults([]);
      return;
    }

    const query = searchQuery.toLowerCase();
    const transcript = transcription.transcript.toLowerCase();
    const results = [];
    let index = 0;

    while (index < transcript.length) {
      const foundIndex = transcript.indexOf(query, index);
      if (foundIndex === -1) break;
      
      results.push({
        index: foundIndex,
        text: transcription.transcript.substr(foundIndex - 20, query.length + 40)
      });
      
      index = foundIndex + 1;
    }

    setSearchResults(results);
    setCurrentSearchIndex(0);
  };

  const navigateSearchResults = (direction) => {
    if (searchResults.length === 0) return;

    let newIndex = currentSearchIndex + direction;
    if (newIndex < 0) newIndex = searchResults.length - 1;
    if (newIndex >= searchResults.length) newIndex = 0;
    
    setCurrentSearchIndex(newIndex);
  };

  const exportTranscription = async () => {
    try {
      const formats = ['txt', 'json', 'srt'];
      
      Alert.alert(
        'Export Format',
        'Choose export format:',
        formats.map(format => ({
          text: format.toUpperCase(),
          onPress: () => performExport(format)
        })).concat([{ text: 'Cancel', style: 'cancel' }])
      );
    } catch (error) {
      console.error('Export failed:', error);
      Alert.alert('Error', 'Failed to export transcription');
    }
  };

  const performExport = async (format) => {
    try {
      const fileUri = await TranscriptionService.exportTranscription(
        transcription.id,
        format
      );
      
      await Share.share({
        url: fileUri,
        title: `Transcription.${format}`,
      });
    } catch (error) {
      console.error('Export failed:', error);
      Alert.alert('Error', 'Failed to export transcription');
    }
  };

  const shareTranscription = async () => {
    try {
      await Share.share({
        message: transcription.transcript || 'No transcript available',
        title: transcription.filename || 'Transcription',
      });
    } catch (error) {
      console.error('Share failed:', error);
    }
  };

  const formatTime = (seconds) => {
    if (!seconds) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const renderProgressBar = () => (
    <View style={styles.progressContainer}>
      <Text style={styles.timeText}>{formatTime(currentTime)}</Text>
      <View style={styles.progressBar}>
        <View style={styles.progressTrack} />
        <Animated.View 
          style={[
            styles.progressFill,
            { width: progressBarWidth }
          ]} 
        />
        <TouchableOpacity
          style={[
            styles.progressThumb,
            { left: (currentTime / duration) * (width - 80) - 10 }
          ]}
          onPress={() => {}}
        />
      </View>
      <Text style={styles.timeText}>{formatTime(duration)}</Text>
    </View>
  );

  const renderPlaybackControls = () => (
    <View style={styles.playbackControls}>
      <TouchableOpacity 
        style={styles.controlButton}
        onPress={() => seekTo(Math.max(0, currentTime - 10))}
      >
        <MaterialIcons name="replay-10" size={24} color="#333" />
      </TouchableOpacity>

      <TouchableOpacity 
        style={styles.playButton}
        onPress={togglePlayback}
      >
        <MaterialIcons 
          name={isPlaying ? "pause" : "play-arrow"} 
          size={32} 
          color="#fff" 
        />
      </TouchableOpacity>

      <TouchableOpacity 
        style={styles.controlButton}
        onPress={() => seekTo(Math.min(duration, currentTime + 10))}
      >
        <MaterialIcons name="forward-10" size={24} color="#333" />
      </TouchableOpacity>

      <TouchableOpacity 
        style={styles.controlButton}
        onPress={() => {
          const rates = [0.75, 1.0, 1.25, 1.5, 2.0];
          const currentIndex = rates.indexOf(playbackRate);
          const nextIndex = (currentIndex + 1) % rates.length;
          changePlaybackRate(rates[nextIndex]);
        }}
      >
        <Text style={styles.rateText}>{playbackRate}x</Text>
      </TouchableOpacity>
    </View>
  );

  const renderTranscriptSegment = (segment, index) => {
    const isSelected = selectedSegment === segment;
    const hasTimestamp = segment.start_time !== undefined;
    
    return (
      <TouchableOpacity
        key={index}
        style={[
          styles.transcriptSegment,
          isSelected && styles.selectedSegment
        ]}
        onPress={() => hasTimestamp ? jumpToSegment(segment) : null}
        disabled={!hasTimestamp}
      >
        {showTimestamps && hasTimestamp && (
          <Text style={styles.timestamp}>
            {formatTime(segment.start_time)}
          </Text>
        )}
        
        {showSpeakers && segment.speaker && (
          <Text style={styles.speaker}>Speaker {segment.speaker}:</Text>
        )}
        
        <Text style={styles.segmentText}>{segment.text}</Text>
      </TouchableOpacity>
    );
  };

  const renderSearchModal = () => (
    <Modal
      visible={searchVisible}
      animationType="slide"
      transparent={true}
      onRequestClose={() => setSearchVisible(false)}
    >
      <View style={styles.searchModalOverlay}>
        <View style={styles.searchModalContent}>
          <View style={styles.searchHeader}>
            <TextInput
              style={styles.searchInput}
              placeholder="Search in transcript..."
              value={searchQuery}
              onChangeText={setSearchQuery}
              autoFocus={true}
            />
            <TouchableOpacity 
              style={styles.searchCloseButton}
              onPress={() => setSearchVisible(false)}
            >
              <MaterialIcons name="close" size={24} color="#333" />
            </TouchableOpacity>
          </View>
          
          {searchResults.length > 0 && (
            <View style={styles.searchResults}>
              <View style={styles.searchNavigation}>
                <TouchableOpacity onPress={() => navigateSearchResults(-1)}>
                  <MaterialIcons name="keyboard-arrow-up" size={24} color="#333" />
                </TouchableOpacity>
                <Text style={styles.searchCounter}>
                  {currentSearchIndex + 1} of {searchResults.length}
                </Text>
                <TouchableOpacity onPress={() => navigateSearchResults(1)}>
                  <MaterialIcons name="keyboard-arrow-down" size={24} color="#333" />
                </TouchableOpacity>
              </View>
              
              <ScrollView style={styles.searchResultsList}>
                {searchResults.map((result, index) => (
                  <TouchableOpacity
                    key={index}
                    style={[
                      styles.searchResultItem,
                      index === currentSearchIndex && styles.activeSearchResult
                    ]}
                    onPress={() => setCurrentSearchIndex(index)}
                  >
                    <Text style={styles.searchResultText}>{result.text}</Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>
          )}
        </View>
      </View>
    </Modal>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2196F3" />
        <Text style={styles.loadingText}>Loading transcription...</Text>
      </View>
    );
  }

  if (processing) {
    return (
      <View style={styles.processingContainer}>
        <Text style={styles.processingTitle}>Processing Audio</Text>
        <Text style={styles.processingSubtitle}>
          {source === 'recording' ? 'Analyzing your recording...' : 'Transcribing audio file...'}
        </Text>
        
        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <View style={styles.progressTrack} />
            <Animated.View 
              style={[styles.progressFill, { width: progressBarWidth }]} 
            />
          </View>
          <Text style={styles.progressText}>{Math.round(progress * 100)}%</Text>
        </View>
        
        <Text style={styles.processingNote}>
          This may take a few minutes depending on the audio length
        </Text>
      </View>
    );
  }

  if (!transcription) {
    return (
      <View style={styles.errorContainer}>
        <MaterialIcons name="error-outline" size={64} color="#f44336" />
        <Text style={styles.errorTitle}>Transcription Failed</Text>
        <Text style={styles.errorText}>
          Unable to process the audio file. Please try again.
        </Text>
        <TouchableOpacity 
          style={styles.retryButton}
          onPress={() => navigation.goBack()}
        >
          <Text style={styles.retryButtonText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity 
          style={styles.headerButton}
          onPress={() => navigation.goBack()}
        >
          <MaterialIcons name="arrow-back" size={24} color="#333" />
        </TouchableOpacity>
        
        <Text style={styles.headerTitle} numberOfLines={1}>
          {transcription.filename || 'Transcription'}
        </Text>
        
        <View style={styles.headerActions}>
          <TouchableOpacity 
            style={styles.headerButton}
            onPress={() => setSearchVisible(true)}
          >
            <MaterialIcons name="search" size={24} color="#333" />
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.headerButton}
            onPress={shareTranscription}
          >
            <MaterialIcons name="share" size={24} color="#333" />
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.headerButton}
            onPress={exportTranscription}
          >
            <MaterialIcons name="download" size={24} color="#333" />
          </TouchableOpacity>
        </View>
      </View>

      {sound && (
        <View style={styles.audioPlayer}>
          {renderProgressBar()}
          {renderPlaybackControls()}
        </View>
      )}

      <View style={styles.viewControls}>
        <TouchableOpacity 
          style={[styles.viewButton, showTranscript && styles.activeViewButton]}
          onPress={() => setShowTranscript(!showTranscript)}
        >
          <Text style={styles.viewButtonText}>Transcript</Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={[styles.viewButton, showSpeakers && styles.activeViewButton]}
          onPress={() => setShowSpeakers(!showSpeakers)}
        >
          <Text style={styles.viewButtonText}>Speakers</Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={[styles.viewButton, showTimestamps && styles.activeViewButton]}
          onPress={() => setShowTimestamps(!showTimestamps)}
        >
          <Text style={styles.viewButtonText}>Times</Text>
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.transcriptContainer}>
        {showTranscript && transcription.segments ? (
          transcription.segments.map((segment, index) => 
            renderTranscriptSegment(segment, index)
          )
        ) : showTranscript && transcription.transcript ? (
          <View style={styles.transcriptSegment}>
            <Text style={styles.segmentText}>{transcription.transcript}</Text>
          </View>
        ) : (
          <View style={styles.noTranscriptContainer}>
            <Text style={styles.noTranscriptText}>
              No transcript available
            </Text>
          </View>
        )}
      </ScrollView>

      {renderSearchModal()}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#fff',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  headerButton: {
    padding: 8,
  },
  headerTitle: {
    flex: 1,
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginHorizontal: 16,
  },
  headerActions: {
    flexDirection: 'row',
  },
  audioPlayer: {
    backgroundColor: '#fff',
    padding: 16,
    elevation: 1,
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  timeText: {
    fontSize: 12,
    color: '#666',
    fontFamily: 'monospace',
    minWidth: 40,
  },
  progressBar: {
    flex: 1,
    height: 4,
    backgroundColor: '#e0e0e0',
    borderRadius: 2,
    marginHorizontal: 12,
    position: 'relative',
  },
  progressTrack: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: '#e0e0e0',
    borderRadius: 2,
  },
  progressFill: {
    height: 4,
    backgroundColor: '#2196F3',
    borderRadius: 2,
  },
  progressThumb: {
    position: 'absolute',
    top: -6,
    width: 16,
    height: 16,
    backgroundColor: '#2196F3',
    borderRadius: 8,
    elevation: 2,
  },
  playbackControls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 20,
  },
  controlButton: {
    padding: 12,
  },
  playButton: {
    backgroundColor: '#2196F3',
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 4,
  },
  rateText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
  },
  viewControls: {
    backgroundColor: '#fff',
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  viewButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 16,
    marginRight: 8,
  },
  activeViewButton: {
    backgroundColor: '#e3f2fd',
  },
  viewButtonText: {
    fontSize: 14,
    color: '#333',
  },
  transcriptContainer: {
    flex: 1,
    padding: 16,
  },
  transcriptSegment: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 8,
    marginBottom: 8,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 1,
  },
  selectedSegment: {
    backgroundColor: '#e3f2fd',
    borderColor: '#2196F3',
    borderWidth: 1,
  },
  timestamp: {
    fontSize: 12,
    color: '#2196F3',
    fontWeight: 'bold',
    marginBottom: 4,
  },
  speaker: {
    fontSize: 14,
    color: '#ff9800',
    fontWeight: 'bold',
    marginBottom: 4,
  },
  segmentText: {
    fontSize: 16,
    color: '#333',
    lineHeight: 24,
  },
  noTranscriptContainer: {
    alignItems: 'center',
    padding: 32,
  },
  noTranscriptText: {
    fontSize: 16,
    color: '#666',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  processingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    paddingHorizontal: 32,
  },
  processingTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  processingSubtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 32,
  },
  progressText: {
    fontSize: 14,
    color: '#666',
    marginTop: 8,
  },
  processingNote: {
    fontSize: 12,
    color: '#999',
    textAlign: 'center',
    marginTop: 32,
    fontStyle: 'italic',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    paddingHorizontal: 32,
  },
  errorTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#f44336',
    marginTop: 16,
    marginBottom: 8,
  },
  errorText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 32,
  },
  retryButton: {
    backgroundColor: '#2196F3',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 24,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  searchModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-start',
    paddingTop: 60,
  },
  searchModalContent: {
    backgroundColor: '#fff',
    margin: 16,
    borderRadius: 12,
    maxHeight: height * 0.8,
  },
  searchHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    paddingVertical: 8,
  },
  searchCloseButton: {
    padding: 8,
  },
  searchResults: {
    maxHeight: 400,
  },
  searchNavigation: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  searchCounter: {
    fontSize: 14,
    color: '#666',
  },
  searchResultsList: {
    maxHeight: 300,
  },
  searchResultItem: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  activeSearchResult: {
    backgroundColor: '#e3f2fd',
  },
  searchResultText: {
    fontSize: 14,
    color: '#333',
    lineHeight: 20,
  },
});