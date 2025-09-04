import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Modal,
  TextInput,
  Switch,
  ActivityIndicator,
  PermissionsAndroid,
  Platform,
  Share
} from 'react-native';
import DocumentPicker from 'react-native-document-picker';
import AudioRecorderPlayer from 'react-native-audio-recorder-player';
import { Picker } from '@react-native-picker/picker';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as Progress from 'react-native-progress';
import { buildLink } from '../../utils/deeplink';
import { logUxEvent } from '../../utils/uxTelemetry';

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: 'audio' | 'video';
  uri: string;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  duration?: number;
  error?: string;
}

interface ProcessingOptions {
  language: string;
  analysisMode: 'basic' | 'advanced' | 'advanced_plus';
  enableSpeakerDiarization: boolean;
  enableStructuredAnalysis: boolean;
  customPrompt?: string;
  outputFormat: 'json' | 'text' | 'srt' | 'vtt';
}

export const MediaUpload: React.FC = () => {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState('00:00');
  const [showSettings, setShowSettings] = useState(false);
  const [processingOptions, setProcessingOptions] = useState<ProcessingOptions>({
    language: 'auto',
    analysisMode: 'advanced',
    enableSpeakerDiarization: true,
    enableStructuredAnalysis: false,
    outputFormat: 'json'
  });

  const audioRecorderPlayer = useRef(new AudioRecorderPlayer()).current;

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
          return true;
        } else {
          Alert.alert('Permissions required', 'Please grant all permissions to use this feature');
          return false;
        }
      } catch (err) {
        console.warn(err);
        return false;
      }
    }
    return true;
  };

  const pickDocument = async () => {
    try {
      const results = await DocumentPicker.pick({
        type: [
          DocumentPicker.types.audio,
          DocumentPicker.types.video,
        ],
        allowMultiSelection: true,
      });

      const newFiles: UploadedFile[] = results.map(result => ({
        id: Math.random().toString(36).substr(2, 9),
        name: result.name || 'Unknown',
        size: result.size || 0,
        type: result.type?.startsWith('video/') ? 'video' : 'audio',
        uri: result.uri,
        status: 'pending',
        progress: 0
      }));

      setFiles(prev => [...prev, ...newFiles]);
    } catch (err) {
      if (!DocumentPicker.isCancel(err)) {
        Alert.alert('Error', 'Failed to pick files');
      }
    }
  };

  const startRecording = async () => {
    const hasPermission = await requestPermissions();
    if (!hasPermission) return;

    try {
      const path = `recording-${Date.now()}.m4a`;
      await audioRecorderPlayer.startRecorder(path);
      
      audioRecorderPlayer.addRecordBackListener((e) => {
        setRecordingTime(audioRecorderPlayer.mmssss(Math.floor(e.currentPosition)));
      });

      setIsRecording(true);
    } catch (error) {
      Alert.alert('Error', 'Failed to start recording');
    }
  };

  const stopRecording = async () => {
    try {
      const result = await audioRecorderPlayer.stopRecorder();
      audioRecorderPlayer.removeRecordBackListener();
      
      const newFile: UploadedFile = {
        id: Math.random().toString(36).substr(2, 9),
        name: `Recording ${new Date().toLocaleTimeString()}.m4a`,
        size: 0, // Size will be determined later
        type: 'audio',
        uri: result,
        status: 'pending',
        progress: 0
      };

      setFiles(prev => [...prev, newFile]);
      setIsRecording(false);
      setRecordingTime('00:00');
    } catch (error) {
      Alert.alert('Error', 'Failed to stop recording');
    }
  };

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(file => file.id !== id));
  };

  const processFiles = async () => {
    const pendingFiles = files.filter(file => file.status === 'pending');
    
    for (const file of pendingFiles) {
      await processFile(file);
    }
  };

  const processFile = async (file: UploadedFile) => {
    // Update status to uploading
    setFiles(prev => prev.map(f => 
      f.id === file.id ? { ...f, status: 'uploading' } : f
    ));

    try {
      // Simulate file upload with progress
      for (let progress = 0; progress <= 100; progress += 10) {
        await new Promise(resolve => setTimeout(resolve, 200));
        setFiles(prev => prev.map(f => 
          f.id === file.id ? { ...f, progress } : f
        ));
      }

      // Update status to processing
      setFiles(prev => prev.map(f => 
        f.id === file.id ? { ...f, status: 'processing', progress: 0 } : f
      ));

      // Simulate processing
      await new Promise(resolve => setTimeout(resolve, 3000));

      // Update status to completed
      setFiles(prev => prev.map(f => 
        f.id === file.id ? { 
          ...f, 
          status: 'completed', 
          progress: 100,
          duration: Math.floor(Math.random() * 300) + 60 // Mock duration
        } : f
      ));

    } catch (error) {
      setFiles(prev => prev.map(f => 
        f.id === file.id ? { 
          ...f, 
          status: 'error', 
          error: 'Processing failed. Please try again.'
        } : f
      ));
    }
  };

  const retryFile = (file: UploadedFile) => {
    setFiles(prev => prev.map(f => 
      f.id === file.id ? { ...f, status: 'pending', progress: 0, error: undefined } : f
    ));
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#34C759';
      case 'error': return '#FF3B30';
      case 'processing': case 'uploading': return '#FF9500';
      default: return '#007AFF';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return 'check-circle';
      case 'error': return 'error';
      case 'processing': case 'uploading': return 'hourglass-empty';
      default: return 'info';
    }
  };

  const renderUploadSection = () => (
    <View style={styles.uploadSection}>
      <TouchableOpacity style={styles.uploadButton} onPress={pickDocument}>
        <Icon name="cloud-upload" size={48} color="#007AFF" />
        <Text style={styles.uploadButtonText}>Upload Files</Text>
        <Text style={styles.uploadButtonSubtext}>
          Tap to select audio or video files
        </Text>
      </TouchableOpacity>
    </View>
  );

  const renderRecordingSection = () => (
    <View style={styles.recordingSection}>
      <Text style={styles.sectionTitle}>Audio Recording</Text>
      <View style={styles.recordingControls}>
        {!isRecording ? (
          <TouchableOpacity style={styles.recordButton} onPress={startRecording}>
            <Icon name="mic" size={32} color="#fff" />
            <Text style={styles.recordButtonText}>Start Recording</Text>
          </TouchableOpacity>
        ) : (
          <View style={styles.recordingActive}>
            <TouchableOpacity style={styles.stopButton} onPress={stopRecording}>
              <Icon name="stop" size={32} color="#fff" />
              <Text style={styles.stopButtonText}>Stop Recording</Text>
            </TouchableOpacity>
            <Text style={styles.recordingTime}>Recording: {recordingTime}</Text>
          </View>
        )}
      </View>
    </View>
  );

  const renderFilesList = () => (
    <View style={styles.filesSection}>
      <View style={styles.filesSectionHeader}>
        <Text style={styles.sectionTitle}>Files ({files.length})</Text>
        <View style={styles.filesActions}>
          <TouchableOpacity
            style={styles.settingsButton}
            onPress={() => setShowSettings(true)}
          >
            <Icon name="settings" size={24} color="#007AFF" />
          </TouchableOpacity>
          <TouchableOpacity
            style={[
              styles.processButton,
              files.filter(f => f.status === 'pending').length === 0 && styles.processButtonDisabled
            ]}
            onPress={processFiles}
            disabled={files.filter(f => f.status === 'pending').length === 0}
          >
            <Text style={styles.processButtonText}>Process</Text>
          </TouchableOpacity>
        </View>
      </View>

      {files.map((file) => (
        <View key={file.id} style={styles.fileItem}>
          <View style={styles.fileIcon}>
            <Icon
              name={file.type === 'video' ? 'videocam' : 'audiotrack'}
              size={24}
              color="#007AFF"
            />
          </View>
          <View style={styles.fileInfo}>
            <Text style={styles.fileName} numberOfLines={1}>
              {file.name}
            </Text>
            <Text style={styles.fileSize}>
              {formatFileSize(file.size)}
              {file.duration && ` • ${Math.floor(file.duration / 60)}:${(file.duration % 60).toString().padStart(2, '0')}`}
            </Text>
            {file.error && (
              <Text style={styles.fileError}>{file.error}</Text>
            )}
            {(file.status === 'uploading' || file.status === 'processing') && (
              <Progress.Bar
                progress={file.progress / 100}
                width={null}
                height={4}
                color="#007AFF"
                unfilledColor="#E5E5EA"
                borderWidth={0}
                style={styles.progressBar}
              />
            )}
          </View>
          <View style={styles.fileActions}>
            <View style={[styles.statusBadge, { backgroundColor: getStatusColor(file.status) }]}>
              <Icon
                name={getStatusIcon(file.status)}
                size={16}
                color="#fff"
              />
            </View>
            {file.status === 'error' && (
              <TouchableOpacity
                style={styles.retryButton}
                onPress={() => retryFile(file)}
              >
                <Icon name="refresh" size={20} color="#007AFF" />
              </TouchableOpacity>
            )}
            <TouchableOpacity
              style={styles.deleteButton}
              onPress={() => removeFile(file.id)}
            >
              <Icon name="delete" size={20} color="#FF3B30" />
            </TouchableOpacity>
          </View>
        </View>
      ))}

      {files.length === 0 && (
        <View style={styles.emptyState}>
          <Text style={styles.emptyStateText}>No files uploaded yet</Text>
        </View>
      )}
    </View>
  );

  const renderSettingsModal = () => (
    <Modal
      visible={showSettings}
      animationType="slide"
      presentationStyle="pageSheet"
    >
      <SafeAreaView style={styles.modalContainer}>
        <View style={styles.modalHeader}>
          <TouchableOpacity onPress={() => setShowSettings(false)}>
            <Icon name="close" size={24} color="#007AFF" />
          </TouchableOpacity>
          <Text style={styles.modalTitle}>Processing Settings</Text>
          <TouchableOpacity onPress={() => setShowSettings(false)}>
            <Text style={styles.doneButton}>Done</Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.modalContent}>
          <View style={styles.settingGroup}>
            <Text style={styles.settingLabel}>Language</Text>
            <View style={styles.pickerContainer}>
              <Picker
                selectedValue={processingOptions.language}
                onValueChange={(value) => setProcessingOptions(prev => ({ ...prev, language: value }))}
              >
                <Picker.Item label="Auto-detect" value="auto" />
                <Picker.Item label="English" value="en" />
                <Picker.Item label="Spanish" value="es" />
                <Picker.Item label="French" value="fr" />
                <Picker.Item label="German" value="de" />
                <Picker.Item label="Italian" value="it" />
                <Picker.Item label="Portuguese" value="pt" />
              </Picker>
            </View>
          </View>

          <View style={styles.settingGroup}>
            <Text style={styles.settingLabel}>Analysis Mode</Text>
            <View style={styles.pickerContainer}>
              <Picker
                selectedValue={processingOptions.analysisMode}
                onValueChange={(value) => setProcessingOptions(prev => ({ ...prev, analysisMode: value as any }))}
              >
                <Picker.Item label="Basic (spaCy)" value="basic" />
                <Picker.Item label="Advanced (OpenAI)" value="advanced" />
                <Picker.Item label="Advanced+ (Speaker Diarization)" value="advanced_plus" />
              </Picker>
            </View>
          </View>

          <View style={styles.settingGroup}>
            <Text style={styles.settingLabel}>Output Format</Text>
            <View style={styles.pickerContainer}>
              <Picker
                selectedValue={processingOptions.outputFormat}
                onValueChange={(value) => setProcessingOptions(prev => ({ ...prev, outputFormat: value as any }))}
              >
                <Picker.Item label="JSON" value="json" />
                <Picker.Item label="Plain Text" value="text" />
                <Picker.Item label="SRT Subtitles" value="srt" />
                <Picker.Item label="VTT Subtitles" value="vtt" />
              </Picker>
            </View>
          </View>

          <View style={styles.switchGroup}>
            <Text style={styles.settingLabel}>Enable Speaker Diarization</Text>
            <Switch
              value={processingOptions.enableSpeakerDiarization}
              onValueChange={(value) => setProcessingOptions(prev => ({ ...prev, enableSpeakerDiarization: value }))}
            />
          </View>

          <View style={styles.switchGroup}>
            <Text style={styles.settingLabel}>Enable Structured Analysis</Text>
            <Switch
              value={processingOptions.enableStructuredAnalysis}
              onValueChange={(value) => setProcessingOptions(prev => ({ ...prev, enableStructuredAnalysis: value }))}
            />
          </View>

          {processingOptions.enableStructuredAnalysis && (
            <View style={styles.settingGroup}>
              <Text style={styles.settingLabel}>Custom Analysis Prompt</Text>
              <TextInput
                style={styles.textInput}
                multiline
                numberOfLines={4}
                value={processingOptions.customPrompt || ''}
                onChangeText={(text) => setProcessingOptions(prev => ({ ...prev, customPrompt: text }))}
                placeholder="Enter custom instructions for structured analysis..."
              />
            </View>
          )}
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Media Upload</Text>
        <TouchableOpacity 
          onPress={async () => { const url = buildLink('media-upload'); try { await Share.share({ message: url }); await logUxEvent('share_media_upload_view', { url }); } catch (_) {} }}
          accessibilityLabel="Share media upload view"
          style={{ position: 'absolute', right: 20, top: 12 }}
        >
          <Icon name="ios-share" size={22} color="#007AFF" />
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.content}>
        {renderUploadSection()}
        {renderRecordingSection()}
        {renderFilesList()}
      </ScrollView>

      {renderSettingsModal()}

      {files.some(f => f.status === 'processing') && (
        <View style={styles.processingAlert}>
          <ActivityIndicator color="#007AFF" />
          <Text style={styles.processingText}>
            Processing files... This may take a few minutes.
          </Text>
        </View>
      )}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  content: {
    flex: 1,
    padding: 20,
  },
  uploadSection: {
    marginBottom: 20,
  },
  uploadButton: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 40,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#007AFF',
    borderStyle: 'dashed',
  },
  uploadButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#007AFF',
    marginTop: 10,
  },
  uploadButtonSubtext: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },
  recordingSection: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  recordingControls: {
    alignItems: 'center',
  },
  recordButton: {
    backgroundColor: '#FF3B30',
    borderRadius: 50,
    width: 100,
    height: 100,
    alignItems: 'center',
    justifyContent: 'center',
  },
  recordButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
    marginTop: 5,
  },
  recordingActive: {
    alignItems: 'center',
  },
  stopButton: {
    backgroundColor: '#007AFF',
    borderRadius: 50,
    width: 100,
    height: 100,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stopButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
    marginTop: 5,
  },
  recordingTime: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 15,
  },
  filesSection: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
  },
  filesSectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  filesActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  settingsButton: {
    padding: 8,
    marginRight: 10,
  },
  processButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  processButtonDisabled: {
    backgroundColor: '#ccc',
  },
  processButtonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  fileItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  fileIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#007AFF15',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 15,
  },
  fileInfo: {
    flex: 1,
  },
  fileName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  fileSize: {
    fontSize: 14,
    color: '#666',
  },
  fileError: {
    fontSize: 12,
    color: '#FF3B30',
    marginTop: 4,
  },
  progressBar: {
    marginTop: 8,
  },
  fileActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusBadge: {
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
  },
  retryButton: {
    padding: 4,
    marginRight: 8,
  },
  deleteButton: {
    padding: 4,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyStateText: {
    fontSize: 16,
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
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  doneButton: {
    fontSize: 16,
    color: '#007AFF',
    fontWeight: '600',
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  settingGroup: {
    marginBottom: 20,
  },
  settingLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 10,
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    backgroundColor: '#f8f8f8',
  },
  switchGroup: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  textInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 15,
    fontSize: 16,
    backgroundColor: '#f8f8f8',
    textAlignVertical: 'top',
  },
  processingAlert: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#007AFF15',
    padding: 15,
    margin: 20,
    borderRadius: 8,
  },
  processingText: {
    marginLeft: 10,
    fontSize: 14,
    color: '#007AFF',
  },
});

export default MediaUpload;
