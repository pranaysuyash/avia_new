import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Platform,
  Switch,
} from 'react-native';
import DocumentPicker from 'react-native-document-picker';
import RNFS from 'react-native-fs';
import Slider from '@react-native-community/slider';
import Icon from 'react-native-vector-icons/MaterialIcons';
import LinearGradient from 'react-native-linear-gradient';
import { API_BASE_URL } from '../config';

interface AudioQualityMetrics {
  snr_db: number;
  thd_percent: number;
  dynamic_range_db: number;
  spectral_centroid: number;
  spectral_rolloff: number;
  zero_crossing_rate: number;
  rms_energy: number;
  peak_level_db: number;
  loudness_lufs: number;
  quality_score: number;
  recommendations: string[];
}

interface EnhancementSettings {
  enable_noise_reduction: boolean;
  noise_reduction_strength: number;
  enable_normalization: boolean;
  target_loudness_lufs: number;
  enable_compression: boolean;
  compression_ratio: number;
  enable_eq: boolean;
  eq_preset: string;
  enable_declick: boolean;
  enable_dehum: boolean;
  output_format: string;
  output_sample_rate: number;
}

interface EnhancementTask {
  task_id: string;
  status: string;
  original_metrics?: AudioQualityMetrics;
  enhanced_metrics?: AudioQualityMetrics;
  processing_time?: number;
  enhancements_applied: string[];
  improvement_score?: number;
  download_url?: string;
}

const AudioEnhancementScreen: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentTask, setCurrentTask] = useState<EnhancementTask | null>(null);
  const [originalMetrics, setOriginalMetrics] = useState<AudioQualityMetrics | null>(null);
  const [enhancedMetrics, setEnhancedMetrics] = useState<AudioQualityMetrics | null>(null);
  const [selectedPreset, setSelectedPreset] = useState<string>('custom');
  const [showSettings, setShowSettings] = useState(false);

  const [settings, setSettings] = useState<EnhancementSettings>({
    enable_noise_reduction: true,
    noise_reduction_strength: 0.7,
    enable_normalization: true,
    target_loudness_lufs: -16.0,
    enable_compression: false,
    compression_ratio: 4.0,
    enable_eq: false,
    eq_preset: 'speech',
    enable_declick: true,
    enable_dehum: true,
    output_format: 'wav',
    output_sample_rate: 44100,
  });

  const presets = {
    podcast: {
      name: 'Podcast',
      icon: 'mic',
      color: ['#667eea', '#764ba2'],
      settings: {
        enable_noise_reduction: true,
        noise_reduction_strength: 0.8,
        enable_normalization: true,
        target_loudness_lufs: -16.0,
        enable_compression: true,
        compression_ratio: 3.0,
      },
    },
    music: {
      name: 'Music',
      icon: 'music-note',
      color: ['#f093fb', '#f5576c'],
      settings: {
        enable_noise_reduction: false,
        enable_normalization: true,
        target_loudness_lufs: -14.0,
        enable_compression: false,
      },
    },
    interview: {
      name: 'Interview',
      icon: 'people',
      color: ['#4facfe', '#00f2fe'],
      settings: {
        enable_noise_reduction: true,
        noise_reduction_strength: 0.6,
        enable_normalization: true,
        target_loudness_lufs: -18.0,
      },
    },
    restoration: {
      name: 'Restore',
      icon: 'healing',
      color: ['#43e97b', '#38f9d7'],
      settings: {
        enable_noise_reduction: true,
        noise_reduction_strength: 0.9,
        enable_normalization: true,
        target_loudness_lufs: -20.0,
        enable_declick: true,
        enable_dehum: true,
      },
    },
  };

  const pickAudioFile = useCallback(async () => {
    try {
      const result = await DocumentPicker.pick({
        type: [DocumentPicker.types.audio],
      });
      setSelectedFile(result[0]);
      setOriginalMetrics(null);
      setEnhancedMetrics(null);
      setCurrentTask(null);
    } catch (err) {
      if (!DocumentPicker.isCancel(err)) {
        Alert.alert('Error', 'Failed to pick audio file');
      }
    }
  }, []);

  const applyPreset = (presetId: string) => {
    if (presetId === 'custom') {
      setSelectedPreset('custom');
      return;
    }

    const preset = presets[presetId as keyof typeof presets];
    if (preset) {
      setSettings((prev) => ({ ...prev, ...preset.settings }));
      setSelectedPreset(presetId);
    }
  };

  const analyzeAudio = async () => {
    if (!selectedFile) return;

    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append('file', {
        uri: selectedFile.uri,
        type: selectedFile.type || 'audio/wav',
        name: selectedFile.name,
      } as any);

      const response = await fetch(`${API_BASE_URL}/api/v1/audio-enhancement/analyze`, {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.ok) {
        const result = await response.json();
        setOriginalMetrics(result.data.metrics);
        Alert.alert('Success', 'Audio analysis complete!');
      } else {
        throw new Error('Analysis failed');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to analyze audio');
    } finally {
      setIsProcessing(false);
    }
  };

  const enhanceAudio = async () => {
    if (!selectedFile) return;

    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append('file', {
        uri: selectedFile.uri,
        type: selectedFile.type || 'audio/wav',
        name: selectedFile.name,
      } as any);
      formData.append('settings', JSON.stringify(settings));

      const response = await fetch(`${API_BASE_URL}/api/v1/audio-enhancement/enhance`, {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.ok) {
        const result = await response.json();
        setCurrentTask(result.data);
        setOriginalMetrics(result.data.original_metrics);
        setEnhancedMetrics(result.data.enhanced_metrics);
        Alert.alert('Success', 'Audio enhancement complete!');
      } else {
        throw new Error('Enhancement failed');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to enhance audio');
    } finally {
      setIsProcessing(false);
    }
  };

  const downloadEnhanced = async () => {
    if (!currentTask?.task_id) return;

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/audio-enhancement/download/${currentTask.task_id}`
      );

      if (response.ok) {
        const blob = await response.blob();
        // In a real app, you would save this to the device
        Alert.alert('Success', 'Enhanced audio ready for download');
      } else {
        throw new Error('Download failed');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to download enhanced audio');
    }
  };

  const renderMetricCard = (label: string, value: number, unit: string, improved?: boolean) => (
    <View style={styles.metricCard}>
      <Text style={styles.metricLabel}>{label}</Text>
      <View style={styles.metricValueContainer}>
        <Text style={styles.metricValue}>
          {value.toFixed(1)} {unit}
        </Text>
        {improved !== undefined && (
          <Icon
            name={improved ? 'trending-up' : 'trending-down'}
            size={16}
            color={improved ? '#4CAF50' : '#F44336'}
          />
        )}
      </View>
    </View>
  );

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      <LinearGradient
        colors={['#667eea', '#764ba2']}
        style={styles.header}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}>
        <Text style={styles.headerTitle}>Audio Enhancement</Text>
        <Text style={styles.headerSubtitle}>AI-Powered Audio Processing</Text>
      </LinearGradient>

      {/* File Selection */}
      <View style={styles.section}>
        <TouchableOpacity style={styles.uploadButton} onPress={pickAudioFile}>
          <Icon name="cloud-upload" size={48} color="#667eea" />
          <Text style={styles.uploadText}>
            {selectedFile ? selectedFile.name : 'Tap to select audio file'}
          </Text>
          {selectedFile && (
            <Text style={styles.uploadSubtext}>
              {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
            </Text>
          )}
        </TouchableOpacity>
      </View>

      {/* Presets */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Enhancement Presets</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {Object.entries(presets).map(([key, preset]) => (
            <TouchableOpacity
              key={key}
              onPress={() => applyPreset(key)}
              style={[
                styles.presetCard,
                selectedPreset === key && styles.presetCardActive,
              ]}>
              <LinearGradient
                colors={preset.color}
                style={styles.presetGradient}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}>
                <Icon name={preset.icon} size={24} color="white" />
              </LinearGradient>
              <Text style={styles.presetName}>{preset.name}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Settings Toggle */}
      <TouchableOpacity
        style={styles.settingsToggle}
        onPress={() => setShowSettings(!showSettings)}>
        <Text style={styles.settingsToggleText}>Advanced Settings</Text>
        <Icon name={showSettings ? 'expand-less' : 'expand-more'} size={24} color="#667eea" />
      </TouchableOpacity>

      {/* Advanced Settings */}
      {showSettings && (
        <View style={styles.section}>
          <View style={styles.settingItem}>
            <Text style={styles.settingLabel}>Noise Reduction</Text>
            <Switch
              value={settings.enable_noise_reduction}
              onValueChange={(value) =>
                setSettings((prev) => ({ ...prev, enable_noise_reduction: value }))
              }
              trackColor={{ false: '#767577', true: '#667eea' }}
              thumbColor={settings.enable_noise_reduction ? '#764ba2' : '#f4f3f4'}
            />
          </View>

          {settings.enable_noise_reduction && (
            <View style={styles.sliderContainer}>
              <Text style={styles.sliderLabel}>
                Strength: {(settings.noise_reduction_strength * 100).toFixed(0)}%
              </Text>
              <Slider
                style={styles.slider}
                minimumValue={0}
                maximumValue={1}
                value={settings.noise_reduction_strength}
                onValueChange={(value) =>
                  setSettings((prev) => ({ ...prev, noise_reduction_strength: value }))
                }
                minimumTrackTintColor="#667eea"
                maximumTrackTintColor="#CCC"
              />
            </View>
          )}

          <View style={styles.settingItem}>
            <Text style={styles.settingLabel}>Normalize Audio</Text>
            <Switch
              value={settings.enable_normalization}
              onValueChange={(value) =>
                setSettings((prev) => ({ ...prev, enable_normalization: value }))
              }
              trackColor={{ false: '#767577', true: '#667eea' }}
              thumbColor={settings.enable_normalization ? '#764ba2' : '#f4f3f4'}
            />
          </View>

          <View style={styles.settingItem}>
            <Text style={styles.settingLabel}>Remove Clicks</Text>
            <Switch
              value={settings.enable_declick}
              onValueChange={(value) =>
                setSettings((prev) => ({ ...prev, enable_declick: value }))
              }
              trackColor={{ false: '#767577', true: '#667eea' }}
              thumbColor={settings.enable_declick ? '#764ba2' : '#f4f3f4'}
            />
          </View>

          <View style={styles.settingItem}>
            <Text style={styles.settingLabel}>Remove Hum</Text>
            <Switch
              value={settings.enable_dehum}
              onValueChange={(value) =>
                setSettings((prev) => ({ ...prev, enable_dehum: value }))
              }
              trackColor={{ false: '#767577', true: '#667eea' }}
              thumbColor={settings.enable_dehum ? '#764ba2' : '#f4f3f4'}
            />
          </View>
        </View>
      )}

      {/* Action Buttons */}
      <View style={styles.actionButtons}>
        <TouchableOpacity
          style={[styles.actionButton, styles.analyzeButton]}
          onPress={analyzeAudio}
          disabled={!selectedFile || isProcessing}>
          <Icon name="analytics" size={20} color="white" />
          <Text style={styles.actionButtonText}>Analyze</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, styles.enhanceButton]}
          onPress={enhanceAudio}
          disabled={!selectedFile || isProcessing}>
          <Icon name="auto-awesome" size={20} color="white" />
          <Text style={styles.actionButtonText}>Enhance</Text>
        </TouchableOpacity>

        {currentTask && (
          <TouchableOpacity
            style={[styles.actionButton, styles.downloadButton]}
            onPress={downloadEnhanced}>
            <Icon name="download" size={20} color="white" />
            <Text style={styles.actionButtonText}>Download</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Processing Indicator */}
      {isProcessing && (
        <View style={styles.processingContainer}>
          <ActivityIndicator size="large" color="#667eea" />
          <Text style={styles.processingText}>Processing audio...</Text>
        </View>
      )}

      {/* Metrics Display */}
      {(originalMetrics || enhancedMetrics) && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Quality Metrics</Text>

          {enhancedMetrics ? (
            <>
              <View style={styles.metricsComparison}>
                <View style={styles.metricsColumn}>
                  <Text style={styles.metricsColumnTitle}>Original</Text>
                  {renderMetricCard('Quality', originalMetrics!.quality_score, '/100')}
                  {renderMetricCard('SNR', originalMetrics!.snr_db, 'dB')}
                  {renderMetricCard('Loudness', originalMetrics!.loudness_lufs, 'LUFS')}
                </View>

                <View style={styles.metricsColumn}>
                  <Text style={styles.metricsColumnTitle}>Enhanced</Text>
                  {renderMetricCard(
                    'Quality',
                    enhancedMetrics.quality_score,
                    '/100',
                    enhancedMetrics.quality_score > originalMetrics!.quality_score
                  )}
                  {renderMetricCard(
                    'SNR',
                    enhancedMetrics.snr_db,
                    'dB',
                    enhancedMetrics.snr_db > originalMetrics!.snr_db
                  )}
                  {renderMetricCard('Loudness', enhancedMetrics.loudness_lufs, 'LUFS')}
                </View>
              </View>

              {currentTask && currentTask.improvement_score !== undefined && (
                <View style={styles.improvementCard}>
                  <Text style={styles.improvementLabel}>Overall Improvement</Text>
                  <Text style={styles.improvementValue}>
                    {currentTask.improvement_score > 0 ? '+' : ''}
                    {currentTask.improvement_score.toFixed(1)}%
                  </Text>
                </View>
              )}
            </>
          ) : originalMetrics ? (
            <View style={styles.metricsGrid}>
              {renderMetricCard('Quality', originalMetrics.quality_score, '/100')}
              {renderMetricCard('SNR', originalMetrics.snr_db, 'dB')}
              {renderMetricCard('Loudness', originalMetrics.loudness_lufs, 'LUFS')}
              {renderMetricCard('Dynamic Range', originalMetrics.dynamic_range_db, 'dB')}
            </View>
          ) : null}

          {originalMetrics?.recommendations && originalMetrics.recommendations.length > 0 && (
            <View style={styles.recommendationsContainer}>
              <Text style={styles.recommendationsTitle}>Recommendations</Text>
              {originalMetrics.recommendations.map((rec, index) => (
                <View key={index} style={styles.recommendationItem}>
                  <Icon name="lightbulb" size={16} color="#FFA500" />
                  <Text style={styles.recommendationText}>{rec}</Text>
                </View>
              ))}
            </View>
          )}
        </View>
      )}

      {/* Processing Details */}
      {currentTask && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Processing Details</Text>
          <View style={styles.detailsCard}>
            <Text style={styles.detailItem}>
              Status: <Text style={styles.detailValue}>{currentTask.status}</Text>
            </Text>
            {currentTask.processing_time && (
              <Text style={styles.detailItem}>
                Processing Time:{' '}
                <Text style={styles.detailValue}>{currentTask.processing_time.toFixed(2)}s</Text>
              </Text>
            )}
            <Text style={styles.detailItem}>Enhancements Applied:</Text>
            <View style={styles.enhancementsList}>
              {currentTask.enhancements_applied.map((enhancement, index) => (
                <View key={index} style={styles.enhancementChip}>
                  <Text style={styles.enhancementChipText}>{enhancement}</Text>
                </View>
              ))}
            </View>
          </View>
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F7FA',
  },
  header: {
    padding: 30,
    paddingTop: 50,
    borderBottomLeftRadius: 30,
    borderBottomRightRadius: 30,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 5,
  },
  headerSubtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.9)',
  },
  section: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  uploadButton: {
    backgroundColor: 'white',
    borderRadius: 20,
    padding: 30,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  uploadText: {
    fontSize: 16,
    color: '#333',
    marginTop: 10,
    fontWeight: '500',
  },
  uploadSubtext: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },
  presetCard: {
    alignItems: 'center',
    marginRight: 15,
    opacity: 0.7,
  },
  presetCardActive: {
    opacity: 1,
  },
  presetGradient: {
    width: 70,
    height: 70,
    borderRadius: 35,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  presetName: {
    fontSize: 12,
    color: '#333',
    fontWeight: '500',
  },
  settingsToggle: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: 'white',
    marginHorizontal: 20,
    borderRadius: 15,
  },
  settingsToggleText: {
    fontSize: 16,
    color: '#333',
    fontWeight: '500',
  },
  settingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  settingLabel: {
    fontSize: 16,
    color: '#333',
  },
  sliderContainer: {
    paddingVertical: 10,
  },
  sliderLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 10,
  },
  slider: {
    width: '100%',
    height: 40,
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 25,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 5,
    elevation: 3,
  },
  analyzeButton: {
    backgroundColor: '#4facfe',
  },
  enhanceButton: {
    backgroundColor: '#667eea',
  },
  downloadButton: {
    backgroundColor: '#43e97b',
  },
  actionButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  processingContainer: {
    alignItems: 'center',
    padding: 30,
  },
  processingText: {
    marginTop: 15,
    fontSize: 16,
    color: '#667eea',
  },
  metricsComparison: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metricsColumn: {
    flex: 1,
    marginHorizontal: 5,
  },
  metricsColumnTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
    textAlign: 'center',
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  metricCard: {
    backgroundColor: 'white',
    borderRadius: 15,
    padding: 15,
    marginBottom: 10,
    width: '48%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  metricLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 5,
  },
  metricValueContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  metricValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  improvementCard: {
    backgroundColor: '#E8F5E9',
    borderRadius: 15,
    padding: 20,
    marginTop: 15,
    alignItems: 'center',
  },
  improvementLabel: {
    fontSize: 14,
    color: '#4CAF50',
    marginBottom: 5,
  },
  improvementValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#4CAF50',
  },
  recommendationsContainer: {
    marginTop: 20,
  },
  recommendationsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  recommendationItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  recommendationText: {
    fontSize: 14,
    color: '#666',
    marginLeft: 8,
    flex: 1,
  },
  detailsCard: {
    backgroundColor: 'white',
    borderRadius: 15,
    padding: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  detailItem: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  detailValue: {
    fontWeight: 'bold',
    color: '#333',
  },
  enhancementsList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 10,
  },
  enhancementChip: {
    backgroundColor: '#E3F2FD',
    borderRadius: 15,
    paddingVertical: 5,
    paddingHorizontal: 12,
    marginRight: 8,
    marginBottom: 8,
  },
  enhancementChipText: {
    fontSize: 12,
    color: '#1976D2',
  },
});

export default AudioEnhancementScreen;