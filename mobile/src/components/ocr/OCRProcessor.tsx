/**
 * OCR Processor Component for React Native
 * Mobile-optimized OCR processing with camera integration and document scanning
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Modal,
  TextInput,
  ActivityIndicator,
  Dimensions,
  Platform,
  Share,
  Clipboard
} from 'react-native';
import {
  launchImageLibrary,
  launchCamera,
  ImagePickerResponse,
  MediaType
} from 'react-native-image-picker';
import DocumentPicker, {
  DocumentPickerResponse
} from 'react-native-document-picker';
import RNFS from 'react-native-fs';
import { Picker } from '@react-native-picker/picker';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { Card, Button, Switch, ProgressBar } from 'react-native-elements';
import { showMessage } from 'react-native-flash-message';

// Types
interface OCRResult {
  text: string;
  confidence: number;
  language: string;
  processing_time: number;
  word_count: number;
  line_count: number;
  bounding_boxes: BoundingBox[];
  metadata: Record<string, any>;
}

interface BoundingBox {
  text: string;
  confidence: number;
  bbox: [number, number, number, number];
}

interface DocumentResult {
  filename: string;
  total_pages: number;
  pages: DocumentPage[];
  combined_text: string;
  processing_time: number;
  metadata: Record<string, any>;
}

interface DocumentPage {
  page_number: number;
  text: string;
  confidence: number;
  tables?: any[];
}

interface ProcessingJob {
  id: string;
  filename: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  progress: number;
  result?: OCRResult | DocumentResult;
  error?: string;
  timestamp: Date;
  localPath?: string;
}

interface Language {
  code: string;
  name: string;
}

const SUPPORTED_LANGUAGES: Language[] = [
  { code: 'en', name: 'English' },
  { code: 'es', name: 'Spanish' },
  { code: 'fr', name: 'French' },
  { code: 'de', name: 'German' },
  { code: 'it', name: 'Italian' },
  { code: 'pt', name: 'Portuguese' },
  { code: 'ru', name: 'Russian' },
  { code: 'zh', name: 'Chinese (Simplified)' },
  { code: 'ja', name: 'Japanese' },
  { code: 'ko', name: 'Korean' },
  { code: 'ar', name: 'Arabic' },
  { code: 'hi', name: 'Hindi' },
  { code: 'auto', name: 'Auto-detect' }
];

const { width, height } = Dimensions.get('window');

const OCRProcessor: React.FC = () => {
  // State management
  const [jobs, setJobs] = useState<ProcessingJob[]>([]);
  const [selectedLanguage, setSelectedLanguage] = useState<string>('en');
  const [extractTables, setExtractTables] = useState<boolean>(true);
  const [enhanceContrast, setEnhanceContrast] = useState<boolean>(true);
  const [denoiseImage, setDenoiseImage] = useState<boolean>(true);
  const [deskewImage, setDeskewImage] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<number>(0);
  const [previewModal, setPreviewModal] = useState<{
    visible: boolean;
    job?: ProcessingJob;
  }>({ visible: false });
  const [settingsModal, setSettingsModal] = useState<boolean>(false);
  const [cameraModal, setCameraModal] = useState<boolean>(false);

  // Camera and document picker options
  const imagePickerOptions = {
    mediaType: 'photo' as MediaType,
    quality: 0.8,
    maxWidth: 2048,
    maxHeight: 2048,
  };

  // Add processing job
  const addProcessingJob = (filename: string, localPath: string) => {
    const job: ProcessingJob = {
      id: `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      filename,
      status: 'pending',
      progress: 0,
      timestamp: new Date(),
      localPath
    };

    setJobs(prev => [...prev, job]);
    processFile(job);
  };

  // Process file with OCR
  const processFile = async (job: ProcessingJob) => {
    try {
      // Update job status
      setJobs(prev => prev.map(j => 
        j.id === job.id ? { ...j, status: 'processing', progress: 10 } : j
      ));

      // Read file as base64
      const fileData = await RNFS.readFile(job.localPath!, 'base64');

      // Create request payload
      const payload = {
        file_data: fileData,
        filename: job.filename,
        language: selectedLanguage,
        extract_tables: extractTables,
        enhance_contrast: enhanceContrast,
        denoise_image: denoiseImage,
        deskew_image: deskewImage
      };

      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setJobs(prev => prev.map(j => 
          j.id === job.id && j.progress < 90 
            ? { ...j, progress: j.progress + 10 } 
            : j
        ));
      }, 500);

      // Make API call to backend
      const response = await fetch('/api/ocr/process-mobile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });

      clearInterval(progressInterval);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      // Update job with result
      setJobs(prev => prev.map(j => 
        j.id === job.id 
          ? { 
              ...j, 
              status: 'completed', 
              progress: 100, 
              result: result.data 
            } 
          : j
      ));

      showMessage({
        message: 'OCR Completed',
        description: `Successfully processed ${job.filename}`,
        type: 'success',
      });

    } catch (error) {
      console.error('OCR processing error:', error);
      
      setJobs(prev => prev.map(j => 
        j.id === job.id 
          ? { 
              ...j, 
              status: 'error', 
              progress: 0, 
              error: error instanceof Error ? error.message : 'Unknown error'
            } 
          : j
      ));

      showMessage({
        message: 'OCR Failed',
        description: `Failed to process ${job.filename}`,
        type: 'danger',
      });
    }
  };

  // Handle camera capture
  const handleCameraCapture = () => {
    setCameraModal(false);
    
    launchCamera(imagePickerOptions, (response: ImagePickerResponse) => {
      if (response.didCancel || response.errorMessage) {
        return;
      }

      if (response.assets && response.assets[0]) {
        const asset = response.assets[0];
        if (asset.uri && asset.fileName) {
          addProcessingJob(asset.fileName, asset.uri);
        }
      }
    });
  };

  // Handle gallery selection
  const handleGallerySelection = () => {
    setCameraModal(false);
    
    launchImageLibrary(imagePickerOptions, (response: ImagePickerResponse) => {
      if (response.didCancel || response.errorMessage) {
        return;
      }

      if (response.assets && response.assets[0]) {
        const asset = response.assets[0];
        if (asset.uri && asset.fileName) {
          addProcessingJob(asset.fileName, asset.uri);
        }
      }
    });
  };

  // Handle document selection
  const handleDocumentSelection = async () => {
    setCameraModal(false);
    
    try {
      const result = await DocumentPicker.pick({
        type: [DocumentPicker.types.pdf, DocumentPicker.types.images],
        allowMultiSelection: true,
      });

      result.forEach((doc: DocumentPickerResponse) => {
        if (doc.uri && doc.name) {
          addProcessingJob(doc.name, doc.uri);
        }
      });
    } catch (error) {
      if (!DocumentPicker.isCancel(error)) {
        showMessage({
          message: 'Error',
          description: 'Failed to select document',
          type: 'danger',
        });
      }
    }
  };

  // Share result
  const shareResult = async (job: ProcessingJob) => {
    if (!job.result) return;

    const text = 'text' in job.result ? job.result.text : job.result.combined_text;
    
    try {
      await Share.share({
        message: text,
        title: `OCR Result - ${job.filename}`,
      });
    } catch (error) {
      showMessage({
        message: 'Error',
        description: 'Failed to share result',
        type: 'danger',
      });
    }
  };

  // Copy to clipboard
  const copyToClipboard = async (job: ProcessingJob) => {
    if (!job.result) return;

    const text = 'text' in job.result ? job.result.text : job.result.combined_text;
    
    try {
      await Clipboard.setString(text);
      showMessage({
        message: 'Copied',
        description: 'Text copied to clipboard',
        type: 'success',
      });
    } catch (error) {
      showMessage({
        message: 'Error',
        description: 'Failed to copy text',
        type: 'danger',
      });
    }
  };

  // Delete job
  const deleteJob = (jobId: string) => {
    Alert.alert(
      'Delete Job',
      'Are you sure you want to delete this job?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => {
            setJobs(prev => prev.filter(j => j.id !== jobId));
          }
        }
      ]
    );
  };

  // Clear all jobs
  const clearAllJobs = () => {
    Alert.alert(
      'Clear All Jobs',
      'Are you sure you want to clear all jobs?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear All',
          style: 'destructive',
          onPress: () => setJobs([])
        }
      ]
    );
  };

  // Get job statistics
  const getJobStats = () => {
    const total = jobs.length;
    const completed = jobs.filter(j => j.status === 'completed').length;
    const processing = jobs.filter(j => j.status === 'processing').length;
    const errors = jobs.filter(j => j.status === 'error').length;
    
    return { total, completed, processing, errors };
  };

  // Render tab bar
  const renderTabBar = () => (
    <View style={styles.tabBar}>
      <TouchableOpacity
        style={[styles.tab, activeTab === 0 && styles.activeTab]}
        onPress={() => setActiveTab(0)}
      >
        <Icon name="camera-alt" size={24} color={activeTab === 0 ? '#007AFF' : '#666'} />
        <Text style={[styles.tabText, activeTab === 0 && styles.activeTabText]}>
          Capture
        </Text>
      </TouchableOpacity>
      
      <TouchableOpacity
        style={[styles.tab, activeTab === 1 && styles.activeTab]}
        onPress={() => setActiveTab(1)}
      >
        <Icon name="list" size={24} color={activeTab === 1 ? '#007AFF' : '#666'} />
        <Text style={[styles.tabText, activeTab === 1 && styles.activeTabText]}>
          Results
        </Text>
      </TouchableOpacity>
      
      <TouchableOpacity
        style={[styles.tab, activeTab === 2 && styles.activeTab]}
        onPress={() => setActiveTab(2)}
      >
        <Icon name="settings" size={24} color={activeTab === 2 ? '#007AFF' : '#666'} />
        <Text style={[styles.tabText, activeTab === 2 && styles.activeTabText]}>
          Settings
        </Text>
      </TouchableOpacity>
    </View>
  );

  // Render capture tab
  const renderCaptureTab = () => (
    <ScrollView style={styles.container}>
      <Card containerStyle={styles.card}>
        <Text style={styles.cardTitle}>📄 OCR Document Processing</Text>
        <Text style={styles.cardSubtitle}>
          Extract text from images and documents using your camera or gallery
        </Text>
        
        <View style={styles.buttonContainer}>
          <TouchableOpacity
            style={styles.primaryButton}
            onPress={() => setCameraModal(true)}
          >
            <Icon name="add-a-photo" size={24} color="white" />
            <Text style={styles.buttonText}>Add Document</Text>
          </TouchableOpacity>
        </View>
      </Card>

      {/* Processing Options */}
      <Card containerStyle={styles.card}>
        <Text style={styles.cardTitle}>⚙️ Processing Options</Text>
        
        <View style={styles.optionRow}>
          <Text style={styles.optionLabel}>Language:</Text>
          <View style={styles.pickerContainer}>
            <Picker
              selectedValue={selectedLanguage}
              onValueChange={setSelectedLanguage}
              style={styles.picker}
            >
              {SUPPORTED_LANGUAGES.map((lang) => (
                <Picker.Item
                  key={lang.code}
                  label={lang.name}
                  value={lang.code}
                />
              ))}
            </Picker>
          </View>
        </View>

        <View style={styles.switchRow}>
          <Text style={styles.switchLabel}>Extract Tables</Text>
          <Switch
            value={extractTables}
            onValueChange={setExtractTables}
            trackColor={{ false: '#767577', true: '#81b0ff' }}
            thumbColor={extractTables ? '#007AFF' : '#f4f3f4'}
          />
        </View>

        <View style={styles.switchRow}>
          <Text style={styles.switchLabel}>Enhance Contrast</Text>
          <Switch
            value={enhanceContrast}
            onValueChange={setEnhanceContrast}
            trackColor={{ false: '#767577', true: '#81b0ff' }}
            thumbColor={enhanceContrast ? '#007AFF' : '#f4f3f4'}
          />
        </View>

        <View style={styles.switchRow}>
          <Text style={styles.switchLabel}>Denoise Image</Text>
          <Switch
            value={denoiseImage}
            onValueChange={setDenoiseImage}
            trackColor={{ false: '#767577', true: '#81b0ff' }}
            thumbColor={denoiseImage ? '#007AFF' : '#f4f3f4'}
          />
        </View>

        <View style={styles.switchRow}>
          <Text style={styles.switchLabel}>Auto-correct Skew</Text>
          <Switch
            value={deskewImage}
            onValueChange={setDeskewImage}
            trackColor={{ false: '#767577', true: '#81b0ff' }}
            thumbColor={deskewImage ? '#007AFF' : '#f4f3f4'}
          />
        </View>
      </Card>
    </ScrollView>
  );

  // Render results tab
  const renderResultsTab = () => {
    const stats = getJobStats();
    
    return (
      <ScrollView style={styles.container}>
        {/* Statistics */}
        <Card containerStyle={styles.card}>
          <Text style={styles.cardTitle}>📊 Statistics</Text>
          <View style={styles.statsContainer}>
            <View style={styles.statItem}>
              <Text style={styles.statNumber}>{stats.total}</Text>
              <Text style={styles.statLabel}>Total</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={[styles.statNumber, { color: '#4CAF50' }]}>{stats.completed}</Text>
              <Text style={styles.statLabel}>Completed</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={[styles.statNumber, { color: '#FF9800' }]}>{stats.processing}</Text>
              <Text style={styles.statLabel}>Processing</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={[styles.statNumber, { color: '#F44336' }]}>{stats.errors}</Text>
              <Text style={styles.statLabel}>Errors</Text>
            </View>
          </View>
        </Card>

        {/* Job list */}
        {jobs.length === 0 ? (
          <Card containerStyle={styles.card}>
            <Text style={styles.emptyText}>
              No files processed yet. Use the Capture tab to get started.
            </Text>
          </Card>
        ) : (
          <View>
            <View style={styles.listHeader}>
              <Text style={styles.cardTitle}>Processing Queue</Text>
              <TouchableOpacity onPress={clearAllJobs}>
                <Text style={styles.clearButton}>Clear All</Text>
              </TouchableOpacity>
            </View>
            
            {jobs.map((job) => (
              <Card key={job.id} containerStyle={styles.jobCard}>
                <View style={styles.jobHeader}>
                  <View style={styles.jobInfo}>
                    <Icon
                      name={job.filename.toLowerCase().endsWith('.pdf') ? 'description' : 'image'}
                      size={24}
                      color="#666"
                    />
                    <Text style={styles.jobFilename}>{job.filename}</Text>
                  </View>
                  
                  <View style={styles.jobStatus}>
                    {job.status === 'completed' && (
                      <Icon name="check-circle" size={20} color="#4CAF50" />
                    )}
                    {job.status === 'processing' && (
                      <ActivityIndicator size="small" color="#FF9800" />
                    )}
                    {job.status === 'error' && (
                      <Icon name="error" size={20} color="#F44336" />
                    )}
                    {job.status === 'pending' && (
                      <Icon name="schedule" size={20} color="#666" />
                    )}
                  </View>
                </View>

                {job.status === 'processing' && (
                  <View style={styles.progressContainer}>
                    <ProgressBar
                      progress={job.progress / 100}
                      color="#007AFF"
                      style={styles.progressBar}
                    />
                    <Text style={styles.progressText}>{job.progress}%</Text>
                  </View>
                )}

                {job.status === 'error' && (
                  <Text style={styles.errorText}>{job.error}</Text>
                )}

                {job.status === 'completed' && job.result && (
                  <View>
                    <View style={styles.resultStats}>
                      <View style={styles.resultStat}>
                        <Text style={styles.resultStatLabel}>Confidence</Text>
                        <Text style={styles.resultStatValue}>
                          {'confidence' in job.result 
                            ? `${(job.result.confidence * 100).toFixed(1)}%`
                            : 'N/A'
                          }
                        </Text>
                      </View>
                      <View style={styles.resultStat}>
                        <Text style={styles.resultStatLabel}>Words</Text>
                        <Text style={styles.resultStatValue}>
                          {'word_count' in job.result 
                            ? job.result.word_count.toLocaleString()
                            : job.result.combined_text.split(' ').length.toLocaleString()
                          }
                        </Text>
                      </View>
                      <View style={styles.resultStat}>
                        <Text style={styles.resultStatLabel}>Time</Text>
                        <Text style={styles.resultStatValue}>
                          {job.result.processing_time.toFixed(2)}s
                        </Text>
                      </View>
                    </View>

                    <View style={styles.jobActions}>
                      <TouchableOpacity
                        style={styles.actionButton}
                        onPress={() => setPreviewModal({ visible: true, job })}
                      >
                        <Icon name="visibility" size={20} color="#007AFF" />
                        <Text style={styles.actionButtonText}>Preview</Text>
                      </TouchableOpacity>
                      
                      <TouchableOpacity
                        style={styles.actionButton}
                        onPress={() => shareResult(job)}
                      >
                        <Icon name="share" size={20} color="#007AFF" />
                        <Text style={styles.actionButtonText}>Share</Text>
                      </TouchableOpacity>
                      
                      <TouchableOpacity
                        style={styles.actionButton}
                        onPress={() => copyToClipboard(job)}
                      >
                        <Icon name="content-copy" size={20} color="#007AFF" />
                        <Text style={styles.actionButtonText}>Copy</Text>
                      </TouchableOpacity>
                      
                      <TouchableOpacity
                        style={styles.actionButton}
                        onPress={() => deleteJob(job.id)}
                      >
                        <Icon name="delete" size={20} color="#F44336" />
                        <Text style={[styles.actionButtonText, { color: '#F44336' }]}>Delete</Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                )}
              </Card>
            ))}
          </View>
        )}
      </ScrollView>
    );
  };

  // Render settings tab
  const renderSettingsTab = () => (
    <ScrollView style={styles.container}>
      <Card containerStyle={styles.card}>
        <Text style={styles.cardTitle}>⚙️ App Settings</Text>
        
        <View style={styles.settingRow}>
          <Text style={styles.settingLabel}>App Version</Text>
          <Text style={styles.settingValue}>1.0.0</Text>
        </View>
        
        <View style={styles.settingRow}>
          <Text style={styles.settingLabel}>OCR Engine</Text>
          <Text style={styles.settingValue}>Hybrid (Tesseract + EasyOCR)</Text>
        </View>
        
        <View style={styles.settingRow}>
          <Text style={styles.settingLabel}>Supported Languages</Text>
          <Text style={styles.settingValue}>{SUPPORTED_LANGUAGES.length}</Text>
        </View>
        
        <TouchableOpacity style={styles.settingButton}>
          <Text style={styles.settingButtonText}>Clear Cache</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.settingButton}>
          <Text style={styles.settingButtonText}>About</Text>
        </TouchableOpacity>
      </Card>
    </ScrollView>
  );

  // Render camera modal
  const renderCameraModal = () => (
    <Modal
      visible={cameraModal}
      transparent={true}
      animationType="slide"
      onRequestClose={() => setCameraModal(false)}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          <Text style={styles.modalTitle}>Add Document</Text>
          
          <TouchableOpacity
            style={styles.modalButton}
            onPress={handleCameraCapture}
          >
            <Icon name="camera-alt" size={24} color="#007AFF" />
            <Text style={styles.modalButtonText}>Take Photo</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.modalButton}
            onPress={handleGallerySelection}
          >
            <Icon name="photo-library" size={24} color="#007AFF" />
            <Text style={styles.modalButtonText}>Choose from Gallery</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.modalButton}
            onPress={handleDocumentSelection}
          >
            <Icon name="description" size={24} color="#007AFF" />
            <Text style={styles.modalButtonText}>Select Document</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.modalCancelButton}
            onPress={() => setCameraModal(false)}
          >
            <Text style={styles.modalCancelText}>Cancel</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );

  // Render preview modal
  const renderPreviewModal = () => (
    <Modal
      visible={previewModal.visible}
      animationType="slide"
      onRequestClose={() => setPreviewModal({ visible: false })}
    >
      <View style={styles.previewContainer}>
        <View style={styles.previewHeader}>
          <Text style={styles.previewTitle}>
            {previewModal.job?.filename}
          </Text>
          <TouchableOpacity
            onPress={() => setPreviewModal({ visible: false })}
          >
            <Icon name="close" size={24} color="#666" />
          </TouchableOpacity>
        </View>
        
        <ScrollView style={styles.previewContent}>
          <Text style={styles.previewText}>
            {previewModal.job?.result && (
              'text' in previewModal.job.result 
                ? previewModal.job.result.text 
                : previewModal.job.result.combined_text
            )}
          </Text>
        </ScrollView>
        
        <View style={styles.previewActions}>
          <TouchableOpacity
            style={styles.previewActionButton}
            onPress={() => previewModal.job && copyToClipboard(previewModal.job)}
          >
            <Icon name="content-copy" size={20} color="white" />
            <Text style={styles.previewActionText}>Copy</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.previewActionButton}
            onPress={() => previewModal.job && shareResult(previewModal.job)}
          >
            <Icon name="share" size={20} color="white" />
            <Text style={styles.previewActionText}>Share</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );

  return (
    <View style={styles.container}>
      {renderTabBar()}
      
      {activeTab === 0 && renderCaptureTab()}
      {activeTab === 1 && renderResultsTab()}
      {activeTab === 2 && renderSettingsTab()}
      
      {renderCameraModal()}
      {renderPreviewModal()}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 12,
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#007AFF',
  },
  tabText: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  activeTabText: {
    color: '#007AFF',
    fontWeight: '600',
  },
  card: {
    borderRadius: 8,
    marginBottom: 16,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
    color: '#333',
  },
  cardSubtitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 16,
  },
  buttonContainer: {
    alignItems: 'center',
  },
  primaryButton: {
    backgroundColor: '#007AFF',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    minWidth: 200,
    justifyContent: 'center',
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  optionRow: {
    marginBottom: 16,
  },
  optionLabel: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 8,
    color: '#333',
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    backgroundColor: 'white',
  },
  picker: {
    height: 50,
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  switchLabel: {
    fontSize: 16,
    color: '#333',
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  listHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  clearButton: {
    color: '#F44336',
    fontSize: 14,
    fontWeight: '500',
  },
  emptyText: {
    textAlign: 'center',
    color: '#666',
    fontSize: 16,
    paddingVertical: 32,
  },
  jobCard: {
    borderRadius: 8,
    marginBottom: 8,
  },
  jobHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  jobInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  jobFilename: {
    fontSize: 16,
    fontWeight: '500',
    marginLeft: 8,
    flex: 1,
    color: '#333',
  },
  jobStatus: {
    marginLeft: 8,
  },
  progressContainer: {
    marginVertical: 8,
  },
  progressBar: {
    height: 4,
    borderRadius: 2,
  },
  progressText: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
    marginTop: 4,
  },
  errorText: {
    color: '#F44336',
    fontSize: 14,
    marginTop: 8,
  },
  resultStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginVertical: 12,
    paddingVertical: 12,
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
  },
  resultStat: {
    alignItems: 'center',
  },
  resultStatLabel: {
    fontSize: 12,
    color: '#666',
  },
  resultStatValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginTop: 2,
  },
  jobActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 12,
  },
  actionButton: {
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  actionButtonText: {
    fontSize: 12,
    color: '#007AFF',
    marginTop: 2,
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  settingLabel: {
    fontSize: 16,
    color: '#333',
  },
  settingValue: {
    fontSize: 16,
    color: '#666',
  },
  settingButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    marginTop: 16,
    alignItems: 'center',
  },
  settingButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '500',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: 'white',
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    paddingHorizontal: 24,
    paddingVertical: 32,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 24,
    color: '#333',
  },
  modalButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  modalButtonText: {
    fontSize: 16,
    color: '#007AFF',
    marginLeft: 16,
  },
  modalCancelButton: {
    alignItems: 'center',
    paddingVertical: 16,
    marginTop: 16,
  },
  modalCancelText: {
    fontSize: 16,
    color: '#666',
  },
  previewContainer: {
    flex: 1,
    backgroundColor: 'white',
  },
  previewHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
    paddingTop: Platform.OS === 'ios' ? 44 : 12,
  },
  previewTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    flex: 1,
  },
  previewContent: {
    flex: 1,
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  previewText: {
    fontSize: 16,
    lineHeight: 24,
    color: '#333',
  },
  previewActions: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 16,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
    gap: 12,
  },
  previewActionButton: {
    flex: 1,
    backgroundColor: '#007AFF',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderRadius: 8,
  },
  previewActionText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '500',
    marginLeft: 8,
  },
});

export default OCRProcessor;