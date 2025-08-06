import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
  Modal,
  Switch,
  Dimensions,
  ProgressBarAndroid,
  Platform,
} from 'react-native';
import { launchDocumentPicker } from 'react-native-document-picker';
import { Picker } from '@react-native-picker/picker';
import Slider from '@react-native-community/slider';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { apiClient } from '../services/api';

const { width: screenWidth } = Dimensions.get('window');

interface AudioPreprocessingConfig {
  target_sample_rate: number;
  enable_noise_reduction: boolean;
  noise_reduction_strength: number;
  enable_normalization: boolean;
  normalization_method: string;
  remove_silence: boolean;
  silence_threshold: number;
  enable_high_pass_filter: boolean;
  high_pass_cutoff: number;
  enable_low_pass_filter: boolean;
  low_pass_cutoff: number;
  output_format: string;
}

interface AudioAnalysis {
  duration: number;
  sample_rate: number;
  channels: number;
  quality_metrics: {
    snr: number;
    dynamic_range: number;
    energy: number;
    peak_level: number;
  };
  recommendations: string[];
}

interface ProcessingResult {
  task_id: string;
  status: string;
  processed_audio?: string;
  original_audio?: string;
  operations_applied: string[];
  quality_metrics: Record<string, number>;
  processing_time: number;
  sample_rate: number;
  duration: {
    original: number;
    processed: number;
  };
  metadata: Record<string, any>;
  message?: string;
}

const AudioPreprocessingScreen: React.FC = () => {
  const [selectedAudio, setSelectedAudio] = useState<string | null>(null);
  const [processedAudio, setProcessedAudio] = useState<string | null>(null);
  const [audioFile, setAudioFile] = useState<any>(null);
  const [processing, setProcessing] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [config, setConfig] = useState<AudioPreprocessingConfig>({
    target_sample_rate: 16000,
    enable_noise_reduction: true,
    noise_reduction_strength: 0.7,
    enable_normalization: true,
    normalization_method: 'peak',
    remove_silence: true,
    silence_threshold: -40,
    enable_high_pass_filter: true,
    high_pass_cutoff: 80,
    enable_low_pass_filter: true,
    low_pass_cutoff: 8000,
    output_format: 'wav',
  });
  const [result, setResult] = useState<ProcessingResult | null>(null);
  const [analysis, setAnalysis] = useState<AudioAnalysis | null>(null);
  const [presets, setPresets] = useState<Record<string, any>>({});
  const [selectedPreset, setSelectedPreset] = useState<string>('transcription_optimized');
  const [showSettings, setShowSettings] = useState(false);
  const [showAnalysis, setShowAnalysis] = useState(false);

  useEffect(() => {
    loadPresets();
  }, []);

  const loadPresets = async () => {
    try {
      const response = await apiClient.get('/api/v1/audio/presets');
      setPresets(response.data.presets);
    } catch (err) {
      console.error('Failed to load presets:', err);
    }
  };

  const selectAudioFile = async () => {
    try {
      const response = await launchDocumentPicker({
        type: ['audio/*'],
        allowMultiSelection: false,
      });

      if (response && response[0]) {
        const file = response[0];
        setAudioFile(file);
        
        // Convert file to base64
        const reader = new FileReader();
        reader.onload = (e) => {
          setSelectedAudio(e.target?.result as string);
          setProcessedAudio(null);
          setResult(null);
          setAnalysis(null);
        };
        reader.readAsDataURL(file);
      }
    } catch (err) {
      if (!err.userCancel) {
        Alert.alert('Error', 'Failed to select audio file');
      }
    }
  };

  const handlePresetChange = (preset: string) => {
    setSelectedPreset(preset);
    if (presets[preset]) {
      setConfig({ ...config, ...presets[preset] });
    }
  };

  const handleConfigChange = (key: keyof AudioPreprocessingConfig, value: any) => {
    setConfig({ ...config, [key]: value });
  };

  const analyzeAudio = async () => {
    if (!selectedAudio) {
      Alert.alert('Error', 'Please select an audio file first');
      return;
    }

    try {
      setAnalyzing(true);

      const base64Data = selectedAudio.split(',')[1];
      const response = await apiClient.post('/api/v1/audio/analyze', {
        audio_data: base64Data,
        analysis_type: 'quality',
      });

      setAnalysis(response.data);
      setShowAnalysis(true);
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const processAudio = async () => {
    if (!selectedAudio) {
      Alert.alert('Error', 'Please select an audio file first');
      return;
    }

    try {
      setProcessing(true);

      const base64Data = selectedAudio.split(',')[1];
      const response = await apiClient.post('/api/v1/audio/preprocess', {
        audio_data: base64Data,
        config: config,
      });

      const taskId = response.data.task_id;
      pollForResult(taskId);
    } catch (error: any) {
      setProcessing(false);
      Alert.alert('Error', error.response?.data?.detail || 'Processing failed');
    }
  };

  const pollForResult = async (taskId: string) => {
    const maxAttempts = 120; // 2 minutes timeout
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await apiClient.get(`/api/v1/audio/status/${taskId}`);
        const result: ProcessingResult = response.data;

        if (result.status === 'completed') {
          setResult(result);
          setProcessedAudio(`data:audio/wav;base64,${result.processed_audio}`);
          setProcessing(false);
        } else if (result.status === 'failed') {
          Alert.alert('Error', result.message || 'Processing failed');
          setProcessing(false);
        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 1000);
        } else {
          Alert.alert('Error', 'Processing timeout');
          setProcessing(false);
        }
      } catch (error: any) {
        Alert.alert('Error', 'Failed to get processing status');
        setProcessing(false);
      }
    };

    poll();
  };

  const resetProcess = () => {
    setSelectedAudio(null);
    setProcessedAudio(null);
    setAudioFile(null);
    setResult(null);
    setAnalysis(null);
    setProcessing(false);
    setAnalyzing(false);
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(1);
    return `${mins}:${secs.padStart(4, '0')}`;
  };

  const renderQualityMetrics = () => {
    if (!analysis || !analysis.quality_metrics) return null;

    return (
      <View style={styles.metricsContainer}>
        <Text style={styles.sectionTitle}>Audio Analysis</Text>
        <View style={styles.metricRow}>
          <Text style={styles.metricLabel}>Duration:</Text>
          <Text style={styles.metricValue}>{formatDuration(analysis.duration)}</Text>
        </View>
        <View style={styles.metricRow}>
          <Text style={styles.metricLabel}>Sample Rate:</Text>
          <Text style={styles.metricValue}>{analysis.sample_rate} Hz</Text>
        </View>
        <View style={styles.metricRow}>
          <Text style={styles.metricLabel}>SNR:</Text>
          <Text style={[styles.metricValue, { color: analysis.quality_metrics.snr > 10 ? '#4CAF50' : '#FF9800' }]}>
            {analysis.quality_metrics.snr.toFixed(1)} dB
          </Text>
        </View>
        <View style={styles.metricRow}>
          <Text style={styles.metricLabel}>Dynamic Range:</Text>
          <Text style={styles.metricValue}>
            {analysis.quality_metrics.dynamic_range.toFixed(1)} dB
          </Text>
        </View>
        
        {analysis.recommendations.length > 0 && (
          <View style={styles.recommendationsContainer}>
            <Text style={styles.recommendationsTitle}>Recommendations:</Text>
            {analysis.recommendations.map((rec, index) => (
              <View key={index} style={styles.recommendationChip}>
                <Text style={styles.recommendationText}>{rec}</Text>
              </View>
            ))}
          </View>
        )}
      </View>
    );
  };

  const renderOperations = () => {
    if (!result || !result.operations_applied.length) return null;

    return (
      <View style={styles.operationsContainer}>
        <Text style={styles.sectionTitle}>Applied Operations</Text>
        <View style={styles.operationsGrid}>
          {result.operations_applied.map((operation, index) => (
            <View key={index} style={styles.operationChip}>
              <Text style={styles.operationText}>
                {operation.replace('_', ' ')}
              </Text>
            </View>
          ))}
        </View>
      </View>
    );
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <Text style={styles.title}>Audio Preprocessing</Text>

      {/* File Selection */}
      <View style={styles.section}>
        <TouchableOpacity style={styles.uploadButton} onPress={selectAudioFile}>
          <Icon name="audiotrack" size={32} color="#666" />
          <Text style={styles.uploadText}>Select Audio File</Text>
        </TouchableOpacity>

        {audioFile && (
          <View style={styles.fileInfo}>
            <Text style={styles.fileName}>{audioFile.name}</Text>
            <Text style={styles.fileSize}>
              Size: {((audioFile.size || 0) / 1024 / 1024).toFixed(1)} MB
            </Text>
            
            <View style={styles.fileControls}>
              <TouchableOpacity
                style={styles.analyzeButton}
                onPress={analyzeAudio}
                disabled={!selectedAudio || analyzing}
              >
                {analyzing ? (
                  <ActivityIndicator color="#2196F3" size="small" />
                ) : (
                  <Icon name="analytics" size={20} color="#2196F3" />
                )}
                <Text style={styles.analyzeButtonText}>
                  {analyzing ? 'Analyzing...' : 'Analyze'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
      </View>

      {/* Configuration */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Processing Configuration</Text>
        
        <View style={styles.presetContainer}>
          <Text style={styles.settingLabel}>Preset:</Text>
          <View style={styles.pickerContainer}>
            <Picker
              selectedValue={selectedPreset}
              onValueChange={(value) => handlePresetChange(value)}
              style={styles.picker}
            >
              <Picker.Item label="Transcription Optimized" value="transcription_optimized" />
              <Picker.Item label="Podcast Quality" value="podcast_quality" />
              <Picker.Item label="Phone Quality" value="phone_quality" />
              <Picker.Item label="Fast Processing" value="fast_processing" />
            </Picker>
          </View>
        </View>

        <View style={styles.presetContainer}>
          <Text style={styles.settingLabel}>Sample Rate:</Text>
          <View style={styles.pickerContainer}>
            <Picker
              selectedValue={config.target_sample_rate}
              onValueChange={(value) => handleConfigChange('target_sample_rate', Number(value))}
              style={styles.picker}
            >
              <Picker.Item label="8 kHz (Phone)" value={8000} />
              <Picker.Item label="16 kHz (Speech)" value={16000} />
              <Picker.Item label="22 kHz (Standard)" value={22050} />
              <Picker.Item label="44 kHz (CD Quality)" value={44100} />
            </Picker>
          </View>
        </View>

        <View style={styles.switchRow}>
          <Text style={styles.settingLabel}>Enable Noise Reduction</Text>
          <Switch
            value={config.enable_noise_reduction}
            onValueChange={(value) => handleConfigChange('enable_noise_reduction', value)}
          />
        </View>

        <View style={styles.switchRow}>
          <Text style={styles.settingLabel}>Enable Normalization</Text>
          <Switch
            value={config.enable_normalization}
            onValueChange={(value) => handleConfigChange('enable_normalization', value)}
          />
        </View>

        <View style={styles.switchRow}>
          <Text style={styles.settingLabel}>Remove Silence</Text>
          <Switch
            value={config.remove_silence}
            onValueChange={(value) => handleConfigChange('remove_silence', value)}
          />
        </View>

        {config.enable_noise_reduction && (
          <View style={styles.sliderContainer}>
            <Text style={styles.settingLabel}>
              Noise Reduction: {config.noise_reduction_strength.toFixed(1)}
            </Text>
            <Slider
              style={styles.slider}
              minimumValue={0.0}
              maximumValue={1.0}
              value={config.noise_reduction_strength}
              onValueChange={(value) => handleConfigChange('noise_reduction_strength', value)}
              step={0.1}
              minimumTrackTintColor="#2196F3"
              maximumTrackTintColor="#ddd"
              thumbStyle={styles.sliderThumb}
            />
          </View>
        )}

        <TouchableOpacity
          style={styles.settingsButton}
          onPress={() => setShowSettings(true)}
        >
          <Icon name="settings" size={24} color="#2196F3" />
          <Text style={styles.settingsButtonText}>Advanced Settings</Text>
        </TouchableOpacity>
      </View>

      {/* Process Button */}
      <View style={styles.section}>
        <TouchableOpacity
          style={[styles.processButton, processing && styles.processingButton]}
          onPress={processAudio}
          disabled={!selectedAudio || processing}
        >
          {processing ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Icon name="auto-fix-high" size={24} color="#fff" />
          )}
          <Text style={styles.processButtonText}>
            {processing ? 'Processing...' : 'Process Audio'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Results */}
      {result && (
        <View style={styles.section}>
          <View style={styles.resultsHeader}>
            <Text style={styles.sectionTitle}>Results</Text>
            <TouchableOpacity style={styles.iconButton} onPress={resetProcess}>
              <Icon name="refresh" size={24} color="#2196F3" />
            </TouchableOpacity>
          </View>

          <View style={styles.durationComparison}>
            <View style={styles.durationItem}>
              <Text style={styles.durationLabel}>Original:</Text>
              <Text style={styles.durationValue}>
                {formatDuration(result.duration.original)}
              </Text>
            </View>
            <View style={styles.durationItem}>
              <Text style={styles.durationLabel}>Processed:</Text>
              <Text style={styles.durationValue}>
                {formatDuration(result.duration.processed)}
              </Text>
            </View>
            <View style={styles.durationItem}>
              <Text style={styles.durationLabel}>Reduction:</Text>
              <Text style={[styles.durationValue, styles.reductionValue]}>
                {((result.duration.original - result.duration.processed) / result.duration.original * 100).toFixed(1)}%
              </Text>
            </View>
          </View>

          <View style={styles.processingInfo}>
            <Text style={styles.processingTime}>
              Processing Time: {result.processing_time.toFixed(2)}s
            </Text>
            <Text style={styles.sampleRate}>
              Output Sample Rate: {result.sample_rate} Hz
            </Text>
          </View>

          {renderOperations()}
        </View>
      )}

      {/* Advanced Settings Modal */}
      <Modal
        visible={showSettings}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Advanced Settings</Text>
            <TouchableOpacity onPress={() => setShowSettings(false)}>
              <Icon name="close" size={24} color="#666" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalContent}>
            <View style={styles.settingGroup}>
              <Text style={styles.settingLabel}>Normalization Method:</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={config.normalization_method}
                  onValueChange={(value) => handleConfigChange('normalization_method', value)}
                  style={styles.picker}
                >
                  <Picker.Item label="Peak Normalization" value="peak" />
                  <Picker.Item label="RMS Normalization" value="rms" />
                </Picker>
              </View>
            </View>

            <View style={styles.switchRow}>
              <Text style={styles.settingLabel}>High-Pass Filter</Text>
              <Switch
                value={config.enable_high_pass_filter}
                onValueChange={(value) => handleConfigChange('enable_high_pass_filter', value)}
              />
            </View>

            <View style={styles.switchRow}>
              <Text style={styles.settingLabel}>Low-Pass Filter</Text>
              <Switch
                value={config.enable_low_pass_filter}
                onValueChange={(value) => handleConfigChange('enable_low_pass_filter', value)}
              />
            </View>

            {config.enable_high_pass_filter && (
              <View style={styles.sliderContainer}>
                <Text style={styles.settingLabel}>
                  High-Pass Cutoff: {config.high_pass_cutoff} Hz
                </Text>
                <Slider
                  style={styles.slider}
                  minimumValue={50}
                  maximumValue={500}
                  value={config.high_pass_cutoff}
                  onValueChange={(value) => handleConfigChange('high_pass_cutoff', value)}
                  step={10}
                  minimumTrackTintColor="#2196F3"
                  maximumTrackTintColor="#ddd"
                />
              </View>
            )}

            {config.enable_low_pass_filter && (
              <View style={styles.sliderContainer}>
                <Text style={styles.settingLabel}>
                  Low-Pass Cutoff: {config.low_pass_cutoff} Hz
                </Text>
                <Slider
                  style={styles.slider}
                  minimumValue={4000}
                  maximumValue={20000}
                  value={config.low_pass_cutoff}
                  onValueChange={(value) => handleConfigChange('low_pass_cutoff', value)}
                  step={500}
                  minimumTrackTintColor="#2196F3"
                  maximumTrackTintColor="#ddd"
                />
              </View>
            )}

            {config.remove_silence && (
              <View style={styles.sliderContainer}>
                <Text style={styles.settingLabel}>
                  Silence Threshold: {config.silence_threshold} dB
                </Text>
                <Slider
                  style={styles.slider}
                  minimumValue={-60}
                  maximumValue={-10}
                  value={config.silence_threshold}
                  onValueChange={(value) => handleConfigChange('silence_threshold', value)}
                  step={5}
                  minimumTrackTintColor="#2196F3"
                  maximumTrackTintColor="#ddd"
                />
              </View>
            )}
          </ScrollView>
        </View>
      </Modal>

      {/* Analysis Modal */}
      <Modal
        visible={showAnalysis}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Audio Analysis</Text>
            <TouchableOpacity onPress={() => setShowAnalysis(false)}>
              <Icon name="close" size={24} color="#666" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalContent}>
            {renderQualityMetrics()}
          </ScrollView>
        </View>
      </Modal>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  contentContainer: {
    padding: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
    color: '#333',
  },
  section: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  uploadButton: {
    borderWidth: 2,
    borderColor: '#ddd',
    borderStyle: 'dashed',
    borderRadius: 8,
    padding: 32,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fafafa',
  },
  uploadText: {
    marginTop: 8,
    fontSize: 16,
    color: '#666',
  },
  fileInfo: {
    marginTop: 16,
    padding: 12,
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
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
    marginBottom: 12,
  },
  fileControls: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  analyzeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 8,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#2196F3',
  },
  analyzeButtonText: {
    marginLeft: 8,
    color: '#2196F3',
    fontWeight: '600',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
    color: '#333',
  },
  presetContainer: {
    marginBottom: 16,
  },
  settingLabel: {
    fontSize: 16,
    color: '#333',
    marginBottom: 8,
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
  },
  picker: {
    height: 50,
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
  },
  sliderContainer: {
    marginVertical: 16,
  },
  slider: {
    width: '100%',
    height: 40,
    marginTop: 8,
  },
  sliderThumb: {
    backgroundColor: '#2196F3',
  },
  settingsButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#2196F3',
    marginTop: 16,
  },
  settingsButtonText: {
    marginLeft: 8,
    color: '#2196F3',
    fontWeight: '600',
  },
  processButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2196F3',
    padding: 16,
    borderRadius: 8,
    justifyContent: 'center',
  },
  processingButton: {
    backgroundColor: '#999',
  },
  processButtonText: {
    marginLeft: 8,
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  resultsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  iconButton: {
    padding: 8,
  },
  durationComparison: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
    padding: 12,
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
  },
  durationItem: {
    alignItems: 'center',
  },
  durationLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  durationValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  reductionValue: {
    color: '#4CAF50',
  },
  processingInfo: {
    marginBottom: 16,
  },
  processingTime: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  sampleRate: {
    fontSize: 14,
    color: '#666',
  },
  operationsContainer: {
    marginTop: 16,
  },
  operationsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 8,
  },
  operationChip: {
    backgroundColor: '#e3f2fd',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    margin: 2,
  },
  operationText: {
    fontSize: 12,
    color: '#1976d2',
  },
  metricsContainer: {
    marginTop: 8,
  },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 6,
  },
  metricLabel: {
    fontSize: 14,
    color: '#666',
  },
  metricValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  recommendationsContainer: {
    marginTop: 16,
  },
  recommendationsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  recommendationChip: {
    backgroundColor: '#fff3cd',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginBottom: 6,
  },
  recommendationText: {
    fontSize: 12,
    color: '#856404',
  },
  settingGroup: {
    marginBottom: 24,
  },
  // Modal styles
  modalContainer: {
    flex: 1,
    backgroundColor: '#fff',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  modalContent: {
    flex: 1,
    padding: 16,
  },
});

export default AudioPreprocessingScreen;