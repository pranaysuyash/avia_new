import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  ScrollView,
  Alert,
  ActivityIndicator,
  Modal,
  Switch,
  Dimensions,
} from 'react-native';
import { launchImageLibrary, ImagePickerResponse } from 'react-native-image-picker';
import { Picker } from '@react-native-picker/picker';
import Slider from '@react-native-community/slider';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { apiClient } from '../services/api';

const { width: screenWidth } = Dimensions.get('window');

interface PreprocessingConfig {
  enable_denoising: boolean;
  denoise_method: string;
  denoise_strength: number;
  auto_contrast: boolean;
  enable_sharpening: boolean;
  auto_deskew: boolean;
  upscale_factor: number;
  remove_borders: boolean;
}

interface ProcessingResult {
  task_id: string;
  status: string;
  processed_image?: string;
  operations_applied: string[];
  quality_metrics: Record<string, number>;
  processing_time: number;
}

const ImagePreprocessingScreen: React.FC = () => {
  const [originalImage, setOriginalImage] = useState<string | null>(null);
  const [processedImage, setProcessedImage] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [config, setConfig] = useState<PreprocessingConfig>({
    enable_denoising: true,
    denoise_method: 'bilateral',
    denoise_strength: 0.5,
    auto_contrast: true,
    enable_sharpening: true,
    auto_deskew: true,
    upscale_factor: 2.0,
    remove_borders: true,
  });
  const [result, setResult] = useState<ProcessingResult | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [showComparison, setShowComparison] = useState(false);

  const selectImage = () => {
    const options = {
      mediaType: 'photo' as const,
      includeBase64: true,
      maxWidth: 2048,
      maxHeight: 2048,
      quality: 0.8,
    };

    launchImageLibrary(options, (response: ImagePickerResponse) => {
      if (response.didCancel || response.errorMessage) {
        return;
      }

      if (response.assets && response.assets[0]) {
        const asset = response.assets[0];
        setOriginalImage(asset.uri || null);
        setProcessedImage(null);
        setResult(null);
      }
    });
  };

  const processImage = async () => {
    if (!originalImage) {
      Alert.alert('Error', 'Please select an image first');
      return;
    }

    try {
      setProcessing(true);

      // Get base64 data
      const response = await fetch(originalImage);
      const blob = await response.blob();
      const base64Data = await blobToBase64(blob);

      const processResponse = await apiClient.post('/api/v1/image/preprocess', {
        image_data: base64Data.split(',')[1],
        config: config,
      });

      const taskId = processResponse.data.task_id;
      pollForResult(taskId);
    } catch (error: any) {
      setProcessing(false);
      Alert.alert('Error', error.response?.data?.detail || 'Processing failed');
    }
  };

  const pollForResult = async (taskId: string) => {
    const maxAttempts = 60; // 1 minute timeout
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await apiClient.get(`/api/v1/image/status/${taskId}`);
        const result: ProcessingResult = response.data;

        if (result.status === 'completed') {
          setResult(result);
          setProcessedImage(`data:image/png;base64,${result.processed_image}`);
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

  const blobToBase64 = (blob: Blob): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  };

  const resetProcess = () => {
    setOriginalImage(null);
    setProcessedImage(null);
    setResult(null);
    setProcessing(false);
  };

  const renderQualityMetrics = () => {
    if (!result || !result.quality_metrics) return null;

    return (
      <View style={styles.metricsContainer}>
        <Text style={styles.sectionTitle}>Quality Improvements</Text>
        {Object.entries(result.quality_metrics).map(([key, value]) => (
          <View key={key} style={styles.metricRow}>
            <Text style={styles.metricLabel}>
              {key.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase())}:
            </Text>
            <Text style={[styles.metricValue, { color: value > 0 ? '#4CAF50' : '#FF9800' }]}>
              {value > 0 ? '+' : ''}{value.toFixed(1)}%
            </Text>
          </View>
        ))}
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
      <Text style={styles.title}>Image Preprocessing</Text>

      {/* Image Selection */}
      <View style={styles.section}>
        <TouchableOpacity style={styles.uploadButton} onPress={selectImage}>
          <Icon name="cloud-upload" size={32} color="#666" />
          <Text style={styles.uploadText}>Select Image</Text>
        </TouchableOpacity>

        {originalImage && (
          <View style={styles.imageContainer}>
            <Text style={styles.imageLabel}>Original Image:</Text>
            <Image source={{ uri: originalImage }} style={styles.image} resizeMode="contain" />
          </View>
        )}
      </View>

      {/* Processing Controls */}
      <View style={styles.section}>
        <View style={styles.controlsRow}>
          <TouchableOpacity
            style={styles.settingsButton}
            onPress={() => setShowSettings(true)}
          >
            <Icon name="settings" size={24} color="#2196F3" />
            <Text style={styles.buttonText}>Settings</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.processButton, processing && styles.processingButton]}
            onPress={processImage}
            disabled={!originalImage || processing}
          >
            {processing ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Icon name="auto-fix-high" size={24} color="#fff" />
            )}
            <Text style={styles.processButtonText}>
              {processing ? 'Processing...' : 'Process Image'}
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Results */}
      {processedImage && (
        <View style={styles.section}>
          <View style={styles.resultsHeader}>
            <Text style={styles.sectionTitle}>Results</Text>
            <View style={styles.resultsControls}>
              <TouchableOpacity
                style={styles.iconButton}
                onPress={() => setShowComparison(true)}
              >
                <Icon name="compare" size={24} color="#2196F3" />
              </TouchableOpacity>
              <TouchableOpacity style={styles.iconButton} onPress={resetProcess}>
                <Icon name="refresh" size={24} color="#2196F3" />
              </TouchableOpacity>
            </View>
          </View>

          <View style={styles.imageContainer}>
            <Text style={styles.imageLabel}>Processed Image:</Text>
            <Image source={{ uri: processedImage }} style={styles.image} resizeMode="contain" />
          </View>

          {result && (
            <View style={styles.resultInfo}>
              <Text style={styles.processingTime}>
                Processing Time: {result.processing_time.toFixed(2)}s
              </Text>
              {renderOperations()}
              {renderQualityMetrics()}
            </View>
          )}
        </View>
      )}

      {/* Settings Modal */}
      <Modal
        visible={showSettings}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Processing Settings</Text>
            <TouchableOpacity onPress={() => setShowSettings(false)}>
              <Icon name="close" size={24} color="#666" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalContent}>
            <View style={styles.settingGroup}>
              <View style={styles.switchRow}>
                <Text style={styles.settingLabel}>Enable Denoising</Text>
                <Switch
                  value={config.enable_denoising}
                  onValueChange={(value) =>
                    setConfig({ ...config, enable_denoising: value })
                  }
                />
              </View>

              <View style={styles.switchRow}>
                <Text style={styles.settingLabel}>Auto Contrast</Text>
                <Switch
                  value={config.auto_contrast}
                  onValueChange={(value) =>
                    setConfig({ ...config, auto_contrast: value })
                  }
                />
              </View>

              <View style={styles.switchRow}>
                <Text style={styles.settingLabel}>Enable Sharpening</Text>
                <Switch
                  value={config.enable_sharpening}
                  onValueChange={(value) =>
                    setConfig({ ...config, enable_sharpening: value })
                  }
                />
              </View>

              <View style={styles.switchRow}>
                <Text style={styles.settingLabel}>Auto Deskew</Text>
                <Switch
                  value={config.auto_deskew}
                  onValueChange={(value) =>
                    setConfig({ ...config, auto_deskew: value })
                  }
                />
              </View>

              <View style={styles.switchRow}>
                <Text style={styles.settingLabel}>Remove Borders</Text>
                <Switch
                  value={config.remove_borders}
                  onValueChange={(value) =>
                    setConfig({ ...config, remove_borders: value })
                  }
                />
              </View>
            </View>

            <View style={styles.settingGroup}>
              <Text style={styles.settingLabel}>Denoise Method</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={config.denoise_method}
                  onValueChange={(value) =>
                    setConfig({ ...config, denoise_method: value })
                  }
                  style={styles.picker}
                >
                  <Picker.Item label="Bilateral" value="bilateral" />
                  <Picker.Item label="Gaussian" value="gaussian" />
                  <Picker.Item label="Median" value="median" />
                  <Picker.Item label="Non-Local Means" value="nlm" />
                </Picker>
              </View>
            </View>

            <View style={styles.settingGroup}>
              <Text style={styles.settingLabel}>
                Denoise Strength: {config.denoise_strength.toFixed(1)}
              </Text>
              <Slider
                style={styles.slider}
                minimumValue={0.0}
                maximumValue={1.0}
                value={config.denoise_strength}
                onValueChange={(value) =>
                  setConfig({ ...config, denoise_strength: value })
                }
                step={0.1}
                minimumTrackTintColor="#2196F3"
                maximumTrackTintColor="#ddd"
                thumbStyle={styles.sliderThumb}
              />
            </View>

            <View style={styles.settingGroup}>
              <Text style={styles.settingLabel}>
                Upscale Factor: {config.upscale_factor.toFixed(1)}x
              </Text>
              <Slider
                style={styles.slider}
                minimumValue={1.0}
                maximumValue={3.0}
                value={config.upscale_factor}
                onValueChange={(value) =>
                  setConfig({ ...config, upscale_factor: value })
                }
                step={0.1}
                minimumTrackTintColor="#2196F3"
                maximumTrackTintColor="#ddd"
                thumbStyle={styles.sliderThumb}
              />
            </View>
          </ScrollView>
        </View>
      </Modal>

      {/* Comparison Modal */}
      <Modal
        visible={showComparison}
        animationType="fade"
        presentationStyle="fullScreen"
      >
        <View style={styles.comparisonContainer}>
          <View style={styles.comparisonHeader}>
            <Text style={styles.comparisonTitle}>Before & After</Text>
            <TouchableOpacity onPress={() => setShowComparison(false)}>
              <Icon name="close" size={24} color="#fff" />
            </TouchableOpacity>
          </View>

          <ScrollView contentContainerStyle={styles.comparisonContent}>
            <View style={styles.comparisonImages}>
              <View style={styles.comparisonImageContainer}>
                <Text style={styles.comparisonLabel}>Original</Text>
                {originalImage && (
                  <Image
                    source={{ uri: originalImage }}
                    style={styles.comparisonImage}
                    resizeMode="contain"
                  />
                )}
              </View>

              <View style={styles.comparisonImageContainer}>
                <Text style={styles.comparisonLabel}>Processed</Text>
                {processedImage && (
                  <Image
                    source={{ uri: processedImage }}
                    style={styles.comparisonImage}
                    resizeMode="contain"
                  />
                )}
              </View>
            </View>
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
  imageContainer: {
    marginTop: 16,
  },
  imageLabel: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
    color: '#333',
  },
  image: {
    width: '100%',
    height: 200,
    borderRadius: 8,
    backgroundColor: '#f0f0f0',
  },
  controlsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  settingsButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#2196F3',
  },
  buttonText: {
    marginLeft: 8,
    color: '#2196F3',
    fontWeight: '600',
  },
  processButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2196F3',
    padding: 12,
    borderRadius: 8,
    flex: 1,
    marginLeft: 12,
    justifyContent: 'center',
  },
  processingButton: {
    backgroundColor: '#999',
  },
  processButtonText: {
    marginLeft: 8,
    color: '#fff',
    fontWeight: '600',
  },
  resultsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  resultsControls: {
    flexDirection: 'row',
  },
  iconButton: {
    padding: 8,
    marginLeft: 8,
  },
  resultInfo: {
    marginTop: 16,
  },
  processingTime: {
    fontSize: 14,
    color: '#666',
    marginBottom: 12,
  },
  operationsContainer: {
    marginBottom: 16,
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
    paddingVertical: 4,
  },
  metricLabel: {
    fontSize: 14,
    color: '#666',
  },
  metricValue: {
    fontSize: 14,
    fontWeight: '600',
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
  settingGroup: {
    marginBottom: 24,
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
  },
  settingLabel: {
    fontSize: 16,
    color: '#333',
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    marginTop: 8,
  },
  picker: {
    height: 50,
  },
  slider: {
    width: '100%',
    height: 40,
    marginTop: 8,
  },
  sliderThumb: {
    backgroundColor: '#2196F3',
  },
  // Comparison modal styles
  comparisonContainer: {
    flex: 1,
    backgroundColor: '#000',
  },
  comparisonHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: 'rgba(0,0,0,0.8)',
  },
  comparisonTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
  },
  comparisonContent: {
    flex: 1,
    justifyContent: 'center',
  },
  comparisonImages: {
    flexDirection: 'row',
  },
  comparisonImageContainer: {
    flex: 1,
    padding: 8,
  },
  comparisonLabel: {
    fontSize: 16,
    color: '#fff',
    textAlign: 'center',
    marginBottom: 8,
  },
  comparisonImage: {
    width: '100%',
    height: 300,
  },
});

export default ImagePreprocessingScreen;