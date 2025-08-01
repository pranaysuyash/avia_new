import React, { useState, useEffect } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  Alert,
  Dimensions,
  Platform,
} from 'react-native';
import {
  Card,
  Title,
  Paragraph,
  Button,
  FAB,
  Chip,
  ProgressBar,
  Snackbar,
} from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as DocumentPicker from 'expo-document-picker';
import * as FileSystem from 'expo-file-system';

// Import services
import { TranscriptionService } from '../services/TranscriptionService';
import { FileManager } from '../services/FileManager';
import { AppStateManager } from '../services/AppStateManager';

const { width } = Dimensions.get('window');

const HomeScreen = ({ navigation }) => {
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [recentFiles, setRecentFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [snackbarVisible, setSnackbarVisible] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [analysisMode, setAnalysisMode] = useState('basic');

  useEffect(() => {
    loadRecentFiles();
  }, []);

  const loadRecentFiles = async () => {
    try {
      const files = await AppStateManager.getRecentFiles();
      setRecentFiles(files.slice(0, 5)); // Show last 5 files
    } catch (error) {
      console.error('Failed to load recent files:', error);
    }
  };

  const pickFile = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['audio/*', 'video/*'],
        copyToCacheDirectory: true,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const file = result.assets[0];
        
        // Validate file size (100MB limit for mobile)
        if (file.size > 100 * 1024 * 1024) {
          Alert.alert(
            'File Too Large',
            'Please select a file smaller than 100MB for mobile processing.',
            [{ text: 'OK' }]
          );
          return;
        }

        setSelectedFile(file);
        showSnackbar(`Selected: ${file.name}`);
      }
    } catch (error) {
      console.error('File picking failed:', error);
      Alert.alert('Error', 'Failed to select file. Please try again.');
    }
  };

  const processFile = async () => {
    if (!selectedFile) {
      Alert.alert('No File Selected', 'Please select an audio or video file first.');
      return;
    }

    setProcessing(true);
    setProgress(0);

    try {
      // Start transcription process
      const transcriptionId = await TranscriptionService.startTranscription(
        selectedFile,
        analysisMode,
        (progressUpdate) => {
          setProgress(progressUpdate);
        }
      );

      // Navigate to transcription screen with results
      navigation.navigate('Transcription', {
        transcriptionId,
        fileName: selectedFile.name,
      });

      // Add to recent files
      await AppStateManager.addRecentFile({
        name: selectedFile.name,
        size: selectedFile.size,
        uri: selectedFile.uri,
        type: selectedFile.mimeType,
        processedAt: new Date().toISOString(),
      });

      loadRecentFiles();
      setSelectedFile(null);
      showSnackbar('Processing completed successfully!');

    } catch (error) {
      console.error('Processing failed:', error);
      Alert.alert(
        'Processing Failed',
        error.message || 'An error occurred during processing. Please try again.',
        [{ text: 'OK' }]
      );
    } finally {
      setProcessing(false);
      setProgress(0);
    }
  };

  const openRecentFile = async (file) => {
    try {
      // Check if file still exists
      const fileInfo = await FileSystem.getInfoAsync(file.uri);
      if (!fileInfo.exists) {
        Alert.alert(
          'File Not Found',
          'This file is no longer available on your device.',
          [{ text: 'OK' }]
        );
        return;
      }

      setSelectedFile(file);
      showSnackbar(`Selected: ${file.name}`);
    } catch (error) {
      console.error('Failed to open recent file:', error);
    }
  };

  const showSnackbar = (message) => {
    setSnackbarMessage(message);
    setSnackbarVisible(true);
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <Card style={styles.headerCard}>
          <Card.Content>
            <Title style={styles.headerTitle}>Audio/Video Transcription</Title>
            <Paragraph style={styles.headerSubtitle}>
              Upload files or record audio for intelligent transcription and analysis
            </Paragraph>
          </Card.Content>
        </Card>

        {/* Analysis Mode Selection */}
        <Card style={styles.card}>
          <Card.Content>
            <Title style={styles.sectionTitle}>Analysis Mode</Title>
            <View style={styles.chipContainer}>
              <Chip
                selected={analysisMode === 'basic'}
                onPress={() => setAnalysisMode('basic')}
                style={[styles.chip, analysisMode === 'basic' && styles.selectedChip]}
              >
                Basic (Fast)
              </Chip>
              <Chip
                selected={analysisMode === 'advanced'}
                onPress={() => setAnalysisMode('advanced')}
                style={[styles.chip, analysisMode === 'advanced' && styles.selectedChip]}
              >
                Advanced (AI)
              </Chip>
              <Chip
                selected={analysisMode === 'premium'}
                onPress={() => setAnalysisMode('premium')}
                style={[styles.chip, analysisMode === 'premium' && styles.selectedChip]}
              >
                Premium (Full)
              </Chip>
            </View>
          </Card.Content>
        </Card>

        {/* File Selection */}
        <Card style={styles.card}>
          <Card.Content>
            <Title style={styles.sectionTitle}>File Input</Title>
            {selectedFile ? (
              <View style={styles.selectedFileContainer}>
                <Paragraph style={styles.selectedFileName}>
                  📁 {selectedFile.name}
                </Paragraph>
                <Paragraph style={styles.selectedFileDetails}>
                  Size: {formatFileSize(selectedFile.size)}
                </Paragraph>
                <Button
                  mode="outlined"
                  onPress={() => setSelectedFile(null)}
                  style={styles.clearButton}
                >
                  Clear Selection
                </Button>
              </View>
            ) : (
              <Button
                mode="contained"
                onPress={pickFile}
                style={styles.selectButton}
                icon="file-upload"
              >
                Select Audio/Video File
              </Button>
            )}
          </Card.Content>
        </Card>

        {/* Processing Status */}
        {processing && (
          <Card style={styles.card}>
            <Card.Content>
              <Title style={styles.sectionTitle}>Processing...</Title>
              <ProgressBar progress={progress} style={styles.progressBar} />
              <Paragraph style={styles.progressText}>
                {Math.round(progress * 100)}% Complete
              </Paragraph>
            </Card.Content>
          </Card>
        )}

        {/* Recent Files */}
        {recentFiles.length > 0 && (
          <Card style={styles.card}>
            <Card.Content>
              <Title style={styles.sectionTitle}>Recent Files</Title>
              {recentFiles.map((file, index) => (
                <Card key={index} style={styles.recentFileCard}>
                  <Card.Content style={styles.recentFileContent}>
                    <View style={styles.recentFileInfo}>
                      <Paragraph style={styles.recentFileName}>
                        📄 {file.name}
                      </Paragraph>
                      <Paragraph style={styles.recentFileDetails}>
                        {formatFileSize(file.size)} • {new Date(file.processedAt).toLocaleDateString()}
                      </Paragraph>
                    </View>
                    <Button
                      mode="outlined"
                      compact
                      onPress={() => openRecentFile(file)}
                    >
                      Select
                    </Button>
                  </Card.Content>
                </Card>
              ))}
            </Card.Content>
          </Card>
        )}

        {/* Quick Actions */}
        <Card style={styles.card}>
          <Card.Content>
            <Title style={styles.sectionTitle}>Quick Actions</Title>
            <View style={styles.actionButtonsContainer}>
              <Button
                mode="outlined"
                onPress={() => navigation.navigate('Record')}
                style={styles.actionButton}
                icon="microphone"
              >
                Record Audio
              </Button>
              <Button
                mode="outlined"
                onPress={() => navigation.navigate('Customization')}
                style={styles.actionButton}
                icon="settings"
              >
                AI Settings
              </Button>
            </View>
          </Card.Content>
        </Card>
      </ScrollView>

      {/* Floating Action Button */}
      <FAB
        style={styles.fab}
        icon={processing ? "stop" : "play"}
        onPress={processing ? () => {} : processFile}
        disabled={!selectedFile || processing}
        label={processing ? "Processing..." : "Start"}
      />

      {/* Snackbar */}
      <Snackbar
        visible={snackbarVisible}
        onDismiss={() => setSnackbarVisible(false)}
        duration={3000}
      >
        {snackbarMessage}
      </Snackbar>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollView: {
    flex: 1,
    paddingHorizontal: 16,
  },
  headerCard: {
    marginVertical: 8,
    elevation: 2,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#6200EE',
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#666',
    marginTop: 4,
  },
  card: {
    marginVertical: 8,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
  },
  chipContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  chip: {
    marginRight: 8,
    marginBottom: 8,
  },
  selectedChip: {
    backgroundColor: '#6200EE',
  },
  selectedFileContainer: {
    backgroundColor: '#f0f0f0',
    padding: 12,
    borderRadius: 8,
  },
  selectedFileName: {
    fontSize: 16,
    fontWeight: '500',
  },
  selectedFileDetails: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  clearButton: {
    marginTop: 8,
    alignSelf: 'flex-start',
  },
  selectButton: {
    marginTop: 8,
  },
  progressBar: {
    marginVertical: 8,
    height: 8,
  },
  progressText: {
    textAlign: 'center',
    fontSize: 14,
    color: '#666',
  },
  recentFileCard: {
    marginVertical: 4,
    elevation: 1,
  },
  recentFileContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  recentFileInfo: {
    flex: 1,
  },
  recentFileName: {
    fontSize: 14,
    fontWeight: '500',
  },
  recentFileDetails: {
    fontSize: 12,
    color: '#666',
  },
  actionButtonsContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    flex: 1,
  },
  fab: {
    position: 'absolute',
    margin: 16,
    right: 0,
    bottom: 0,
    backgroundColor: '#6200EE',
  },
});

export default HomeScreen;