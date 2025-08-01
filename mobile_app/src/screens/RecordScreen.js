import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Dimensions,
  Animated,
  Platform
} from 'react-native';
import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';
import { MaterialIcons } from '@expo/vector-icons';
import TranscriptionService from '../services/TranscriptionService';

const { width, height } = Dimensions.get('window');

export default function RecordScreen({ navigation }) {
  const [recording, setRecording] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [duration, setDuration] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingUri, setRecordingUri] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const durationInterval = useRef(null);
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const recordButtonScale = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    setupAudio();
    return () => {
      if (durationInterval.current) {
        clearInterval(durationInterval.current);
      }
      if (recording) {
        recording.stopAndUnloadAsync();
      }
    };
  }, []);

  useEffect(() => {
    if (isRecording && !isPaused) {
      // Start pulsing animation
      const pulseAnimation = Animated.loop(
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
      pulseAnimation.start();

      return () => pulseAnimation.stop();
    }
  }, [isRecording, isPaused, pulseAnim]);

  const setupAudio = async () => {
    try {
      const permission = await Audio.requestPermissionsAsync();
      if (!permission.granted) {
        Alert.alert('Permission Required', 'Please grant microphone permission to record audio.');
        return;
      }

      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
        playThroughEarpieceAndroid: false,
        staysActiveInBackground: true,
      });
    } catch (error) {
      console.error('Failed to setup audio:', error);
      Alert.alert('Error', 'Failed to setup audio recording. Please try again.');
    }
  };

  const startRecording = async () => {
    try {
      const { recording: newRecording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY,
        (status) => {
          if (status.isRecording) {
            setDuration(Math.floor(status.durationMillis / 1000));
          }
        },
        100
      );

      setRecording(newRecording);
      setIsRecording(true);
      setDuration(0);

      // Animate record button
      Animated.spring(recordButtonScale, {
        toValue: 1.1,
        useNativeDriver: true,
      }).start();

    } catch (error) {
      console.error('Failed to start recording:', error);
      Alert.alert('Error', 'Failed to start recording. Please check your microphone permissions.');
    }
  };

  const pauseRecording = async () => {
    if (recording) {
      try {
        await recording.pauseAsync();
        setIsPaused(true);
      } catch (error) {
        console.error('Failed to pause recording:', error);
      }
    }
  };

  const resumeRecording = async () => {
    if (recording) {
      try {
        await recording.startAsync();
        setIsPaused(false);
      } catch (error) {
        console.error('Failed to resume recording:', error);
      }
    }
  };

  const stopRecording = async () => {
    if (!recording) return;

    try {
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();
      setRecordingUri(uri);
      setIsRecording(false);
      setIsPaused(false);

      // Reset record button animation
      Animated.spring(recordButtonScale, {
        toValue: 1,
        useNativeDriver: true,
      }).start();

      // Show processing options
      showProcessingOptions(uri);

    } catch (error) {
      console.error('Failed to stop recording:', error);
      Alert.alert('Error', 'Failed to stop recording. Please try again.');
    }
  };

  const showProcessingOptions = (uri) => {
    Alert.alert(
      'Recording Complete',
      `Duration: ${formatDuration(duration)}`,
      [
        { text: 'Discard', style: 'destructive', onPress: discardRecording },
        { text: 'Save Only', onPress: () => saveRecording(uri) },
        { text: 'Process', onPress: () => processRecording(uri) },
      ]
    );
  };

  const discardRecording = async () => {
    if (recordingUri) {
      try {
        await FileSystem.deleteAsync(recordingUri, { idempotent: true });
      } catch (error) {
        console.warn('Failed to delete recording file:', error);
      }
    }
    resetRecording();
  };

  const saveRecording = async (uri) => {
    try {
      const filename = `recording_${Date.now()}.m4a`;
      const documentsDir = FileSystem.documentDirectory;
      const newUri = `${documentsDir}${filename}`;
      
      await FileSystem.moveAsync({
        from: uri,
        to: newUri,
      });

      Alert.alert('Saved', `Recording saved as ${filename}`);
      resetRecording();
    } catch (error) {
      console.error('Failed to save recording:', error);
      Alert.alert('Error', 'Failed to save recording.');
    }
  };

  const processRecording = async (uri) => {
    setIsProcessing(true);
    resetRecording();

    try {
      const fileInfo = await FileSystem.getInfoAsync(uri);
      const file = {
        uri,
        name: `recording_${Date.now()}.m4a`,
        size: fileInfo.size,
        mimeType: 'audio/m4a',
      };

      // Navigate to transcription with file
      navigation.navigate('Transcription', { 
        file,
        source: 'recording' 
      });

    } catch (error) {
      console.error('Failed to process recording:', error);
      Alert.alert('Error', 'Failed to process recording. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const resetRecording = () => {
    setRecording(null);
    setIsRecording(false);
    setIsPaused(false);
    setDuration(0);
    setRecordingUri(null);
  };

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const recordButtonSize = 120;
  const recordButtonColor = isRecording ? '#ff4757' : '#2ed573';

  return (
    <View style={styles.container}>
      <View style={styles.statusContainer}>
        <Text style={styles.statusText}>
          {isRecording ? (isPaused ? 'Paused' : 'Recording') : 'Ready to Record'}
        </Text>
        <Text style={styles.durationText}>{formatDuration(duration)}</Text>
      </View>

      <View style={styles.recordContainer}>
        <Animated.View 
          style={[
            styles.recordButtonContainer,
            {
              transform: [
                { scale: recordButtonScale },
                { scale: isRecording && !isPaused ? pulseAnim : 1 }
              ]
            }
          ]}
        >
          <TouchableOpacity
            style={[
              styles.recordButton,
              {
                backgroundColor: recordButtonColor,
                width: recordButtonSize,
                height: recordButtonSize,
                borderRadius: recordButtonSize / 2,
              }
            ]}
            onPress={isRecording ? stopRecording : startRecording}
            disabled={isProcessing}
          >
            <MaterialIcons 
              name={isRecording ? "stop" : "mic"} 
              size={50} 
              color="white" 
            />
          </TouchableOpacity>
        </Animated.View>

        {isRecording && (
          <TouchableOpacity
            style={styles.pauseButton}
            onPress={isPaused ? resumeRecording : pauseRecording}
          >
            <MaterialIcons 
              name={isPaused ? "play-arrow" : "pause"} 
              size={30} 
              color="#333" 
            />
          </TouchableOpacity>
        )}
      </View>

      <View style={styles.controlsContainer}>
        <TouchableOpacity 
          style={styles.controlButton}
          onPress={() => navigation.navigate('Settings')}
        >
          <MaterialIcons name="settings" size={24} color="#666" />
          <Text style={styles.controlButtonText}>Settings</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.controlButton}
          onPress={() => navigation.navigate('History')}
        >
          <MaterialIcons name="history" size={24} color="#666" />
          <Text style={styles.controlButtonText}>History</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.tipsContainer}>
        <Text style={styles.tipsTitle}>Recording Tips:</Text>
        <Text style={styles.tipText}>• Hold device 6-12 inches from your mouth</Text>
        <Text style={styles.tipText}>• Record in a quiet environment</Text>
        <Text style={styles.tipText}>• Speak clearly and at normal pace</Text>
        <Text style={styles.tipText}>• Max recording time: 30 minutes</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    alignItems: 'center',
    paddingTop: 60,
  },
  statusContainer: {
    alignItems: 'center',
    marginBottom: 60,
  },
  statusText: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  durationText: {
    fontSize: 48,
    fontWeight: '300',
    color: '#666',
    fontFamily: Platform.OS === 'ios' ? 'Courier New' : 'monospace',
  },
  recordContainer: {
    alignItems: 'center',
    marginBottom: 80,
  },
  recordButtonContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  recordButton: {
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  pauseButton: {
    marginTop: 30,
    backgroundColor: '#fff',
    width: 60,
    height: 60,
    borderRadius: 30,
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
  },
  controlsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: width - 80,
    marginBottom: 40,
  },
  controlButton: {
    alignItems: 'center',
    padding: 20,
  },
  controlButtonText: {
    marginTop: 8,
    fontSize: 14,
    color: '#666',
  },
  tipsContainer: {
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 12,
    width: width - 40,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  tipsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  tipText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 6,
    lineHeight: 20,
  },
});