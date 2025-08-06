import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Image,
  Alert,
  StyleSheet,
  Dimensions,
  ActivityIndicator,
} from 'react-native';
import {
  VictoryChart,
  VictoryBar,
  VictoryPie,
  VictoryArea,
  VictoryTheme,
  VictoryLabel,
  VictoryAxis,
} from 'victory-native';
import DocumentPicker from 'react-native-document-picker';
import RNFS from 'react-native-fs';
import { Svg, G, Circle, Text as SvgText } from 'react-native-svg';
import { apiClient } from '../../services/api';

interface AnalysisOptions {
  include_sections: string[];
  detailed_analysis: boolean;
  use_gpu: boolean;
}

interface AnalysisResults {
  task_id: string;
  status: string;
  file_info?: any;
  color_analysis?: any;
  composition_analysis?: any;
  content_analysis?: any;
  quality_metrics?: any;
  semantic_insights?: any;
  confidence_scores?: { [key: string]: number };
  processing_time: number;
  analysis_timestamp?: string;
}

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

const ImageAnalysisInsights: React.FC = () => {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [analysisOptions, setAnalysisOptions] = useState<AnalysisOptions>({
    include_sections: ['all'],
    detailed_analysis: true,
    use_gpu: false,
  });

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const pickImage = async () => {
    try {
      const result = await DocumentPicker.pickSingle({
        type: [DocumentPicker.types.images],
      });

      if (result.uri) {
        setSelectedImage(result.uri);
        setResults(null);
        setError(null);
      }
    } catch (error) {
      if (DocumentPicker.isCancel(error)) {
        return;
      }
      Alert.alert('Error', 'Failed to pick image');
    }
  };

  const analyzeImage = async () => {
    if (!selectedImage) return;

    try {
      setAnalyzing(true);
      setError(null);

      // Read file as base64
      const imageBase64 = await RNFS.readFile(selectedImage, 'base64');
      
      const response = await apiClient.post('/api/v1/image-analysis/analyze', {
        image_data: imageBase64,
        analysis_options: analysisOptions,
        include_sections: analysisOptions.include_sections,
      });

      const taskId = response.data.task_id;
      pollForResults(taskId);

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Analysis failed');
      setAnalyzing(false);
    }
  };

  const pollForResults = (taskId: string) => {
    pollIntervalRef.current = setInterval(async () => {
      try {
        const response = await apiClient.get(`/api/v1/image-analysis/status/${taskId}`);
        const result: AnalysisResults = response.data;

        if (result.status === 'completed') {
          setResults(result);
          setAnalyzing(false);
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
          }
        } else if (result.status === 'failed') {
          setError('Analysis failed');
          setAnalyzing(false);
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
          }
        }
      } catch (err) {
        setError('Failed to get analysis status');
        setAnalyzing(false);
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
        }
      }
    }, 1000);
  };

  const resetAnalysis = () => {
    setSelectedImage(null);
    setResults(null);
    setError(null);
    setAnalyzing(false);
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }
  };

  const renderColorChart = () => {
    if (!results?.color_analysis?.dominant_colors) return null;

    const colors = results.color_analysis.dominant_colors.slice(0, 5);
    const data = colors.map((color: number[], index: number) => ({
      x: index + 1,
      y: 1,
      fill: `rgb(${color[0]}, ${color[1]}, ${color[2]})`,
    }));

    return (
      <View style={styles.chartContainer}>
        <Text style={styles.chartTitle}>Dominant Colors</Text>
        <VictoryPie
          data={data}
          x="x"
          y="y"
          colorScale={colors.map(color => `rgb(${color[0]}, ${color[1]}, ${color[2]})`)}
          width={screenWidth - 60}
          height={200}
          innerRadius={30}
        />
      </View>
    );
  };

  const renderQualityChart = () => {
    if (!results?.quality_metrics) return null;

    const data = [
      { category: 'Sharpness', score: results.quality_metrics.sharpness_score / 100 },
      { category: 'Exposure', score: results.quality_metrics.exposure_quality === 'optimal' ? 1 : 0.5 },
      { category: 'Balance', score: results.quality_metrics.white_balance === 'good' ? 1 : 0.5 },
      { category: 'Resolution', score: results.quality_metrics.resolution_quality === 'high' ? 1 : 0.8 },
    ];

    return (
      <View style={styles.chartContainer}>
        <Text style={styles.chartTitle}>Quality Assessment</Text>
        <VictoryChart
          theme={VictoryTheme.material}
          width={screenWidth - 60}
          height={250}
          domainPadding={20}
        >
          <VictoryAxis dependentAxis tickFormat={(t) => `${Math.round(t * 100)}%`} />
          <VictoryAxis />
          <VictoryBar
            data={data}
            x="category"
            y="score"
            style={{
              data: { fill: "#4A90E2" }
            }}
          />
        </VictoryChart>
      </View>
    );
  };

  const renderCompositionChart = () => {
    if (!results?.composition_analysis) return null;

    const data = [
      { metric: 'Rule of Thirds', value: results.composition_analysis.rule_of_thirds_alignment },
      { metric: 'Symmetry', value: results.composition_analysis.symmetry_score },
      { metric: 'Balance', value: results.composition_analysis.balance_score },
    ];

    return (
      <View style={styles.chartContainer}>
        <Text style={styles.chartTitle}>Composition Analysis</Text>
        <VictoryChart
          theme={VictoryTheme.material}
          width={screenWidth - 60}
          height={250}
          domainPadding={20}
        >
          <VictoryAxis dependentAxis tickFormat={(t) => `${Math.round(t * 100)}%`} />
          <VictoryAxis />
          <VictoryBar
            data={data}
            x="metric"
            y="value"
            style={{
              data: { fill: ["#FF6384", "#36A2EB", "#FFCE56"] }
            }}
          />
        </VictoryChart>
      </View>
    );
  };

  const renderSummaryCards = () => {
    if (!results) return null;

    return (
      <View style={styles.summaryContainer}>
        <View style={styles.row}>
          <View style={[styles.summaryCard, styles.qualityCard]}>
            <Text style={styles.cardTitle}>Overall Quality</Text>
            <Text style={styles.cardValue}>{results.quality_metrics?.overall_quality || 'N/A'}</Text>
            <Text style={styles.cardSubtext}>
              Score: {results.quality_metrics?.technical_score?.toFixed(1) || 0}/100
            </Text>
          </View>

          <View style={[styles.summaryCard, styles.sceneCard]}>
            <Text style={styles.cardTitle}>Scene Type</Text>
            <Text style={styles.cardValue}>{results.content_analysis?.scene_type || 'Unknown'}</Text>
            <Text style={styles.cardSubtext}>
              Complexity: {results.content_analysis?.scene_complexity || 'N/A'}
            </Text>
          </View>
        </View>

        <View style={styles.row}>
          <View style={[styles.summaryCard, styles.commercialCard]}>
            <Text style={styles.cardTitle}>Commercial Potential</Text>
            <Text style={styles.cardValue}>
              {results.semantic_insights?.commercial_potential || 'Unknown'}
            </Text>
            <Text style={styles.cardSubtext}>
              Confidence: {results.confidence_scores?.overall?.toFixed(2) || 0}
            </Text>
          </View>

          <View style={[styles.summaryCard, styles.timeCard]}>
            <Text style={styles.cardTitle}>Processing Time</Text>
            <Text style={styles.cardValue}>{results.processing_time?.toFixed(2) || 0}s</Text>
            <Text style={styles.cardSubtext}>
              {results.analysis_timestamp?.slice(0, 19) || 'N/A'}
            </Text>
          </View>
        </View>
      </View>
    );
  };

  const renderTabContent = () => {
    if (!results) return null;

    switch (activeTab) {
      case 0: // Color Analysis
        return (
          <ScrollView style={styles.tabContent}>
            {renderColorChart()}
            <View style={styles.propertiesContainer}>
              <Text style={styles.sectionTitle}>Color Properties</Text>
              <Text style={styles.property}>Temperature: {results.color_analysis?.color_temperature}</Text>
              <Text style={styles.property}>Brightness: {results.color_analysis?.brightness_level}</Text>
              <Text style={styles.property}>Contrast: {results.color_analysis?.contrast_level}</Text>
              <Text style={styles.property}>Saturation: {results.color_analysis?.saturation_level}</Text>
              <Text style={styles.property}>
                Diversity: {results.color_analysis?.color_diversity?.toFixed(2)}
              </Text>
            </View>
          </ScrollView>
        );

      case 1: // Composition
        return (
          <ScrollView style={styles.tabContent}>
            {renderCompositionChart()}
            <View style={styles.propertiesContainer}>
              <Text style={styles.sectionTitle}>Composition Details</Text>
              <Text style={styles.property}>
                Aspect Ratio: {results.composition_analysis?.aspect_ratio?.toFixed(2)}
              </Text>
              <Text style={styles.property}>Orientation: {results.composition_analysis?.orientation}</Text>
              <Text style={styles.property}>
                Focal Points: {results.composition_analysis?.focal_points?.length || 0}
              </Text>
              <Text style={styles.property}>
                Leading Lines: {results.composition_analysis?.leading_lines_detected ? 'Yes' : 'No'}
              </Text>
              <Text style={styles.property}>
                Depth of Field: {results.composition_analysis?.depth_of_field_estimate}
              </Text>
            </View>
          </ScrollView>
        );

      case 2: // Quality
        return (
          <ScrollView style={styles.tabContent}>
            {renderQualityChart()}
            <View style={styles.propertiesContainer}>
              <Text style={styles.sectionTitle}>Quality Metrics</Text>
              <Text style={styles.property}>
                Sharpness: {results.quality_metrics?.sharpness_score?.toFixed(1)}/100
              </Text>
              <Text style={styles.property}>Exposure: {results.quality_metrics?.exposure_quality}</Text>
              <Text style={styles.property}>White Balance: {results.quality_metrics?.white_balance}</Text>
              <Text style={styles.property}>Noise Level: {results.quality_metrics?.noise_level}</Text>
              <Text style={styles.property}>Resolution: {results.quality_metrics?.resolution_quality}</Text>
            </View>
          </ScrollView>
        );

      case 3: // Insights
        return (
          <ScrollView style={styles.tabContent}>
            <View style={styles.insightContainer}>
              <Text style={styles.sectionTitle}>Scene Description</Text>
              <Text style={styles.insightText}>
                {results.semantic_insights?.scene_description || 'No description available'}
              </Text>
            </View>
            
            <View style={styles.insightContainer}>
              <Text style={styles.sectionTitle}>Key Themes</Text>
              {results.semantic_insights?.key_themes?.map((theme: string, index: number) => (
                <Text key={index} style={styles.tagText}>• {theme}</Text>
              ))}
            </View>

            <View style={styles.insightContainer}>
              <Text style={styles.sectionTitle}>Commercial Insights</Text>
              <Text style={styles.property}>
                Commercial Potential: {results.semantic_insights?.commercial_potential}
              </Text>
              <Text style={styles.property}>
                Emotional Impact: {results.semantic_insights?.emotional_impact}
              </Text>
              <Text style={styles.property}>
                Target Audience: {results.semantic_insights?.target_audience?.join(', ')}
              </Text>
            </View>

            <View style={styles.insightContainer}>
              <Text style={styles.sectionTitle}>Accessibility Description</Text>
              <Text style={styles.insightText}>
                {results.semantic_insights?.accessibility_description || 'No description available'}
              </Text>
            </View>
          </ScrollView>
        );

      default:
        return null;
    }
  };

  const tabs = ['Color', 'Composition', 'Quality', 'Insights'];

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Image Analysis & Insights</Text>
      </View>

      <ScrollView style={styles.content}>
        {/* Upload Section */}
        <View style={styles.uploadSection}>
          <TouchableOpacity style={styles.uploadButton} onPress={pickImage}>
            <Text style={styles.uploadButtonText}>Select Image</Text>
          </TouchableOpacity>

          {selectedImage && (
            <View style={styles.imagePreview}>
              <Image source={{ uri: selectedImage }} style={styles.previewImage} />
            </View>
          )}
        </View>

        {/* Controls */}
        {selectedImage && (
          <View style={styles.controlsSection}>
            <TouchableOpacity
              style={[styles.analyzeButton, analyzing && styles.disabledButton]}
              onPress={analyzeImage}
              disabled={analyzing}
            >
              {analyzing ? (
                <ActivityIndicator color="white" />
              ) : (
                <Text style={styles.analyzeButtonText}>Analyze Image</Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity style={styles.resetButton} onPress={resetAnalysis}>
              <Text style={styles.resetButtonText}>Reset</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Error Display */}
        {error && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {/* Results Section */}
        {results && (
          <View style={styles.resultsSection}>
            <Text style={styles.resultsTitle}>Analysis Results</Text>
            
            {renderSummaryCards()}

            {/* Tabs */}
            <View style={styles.tabsContainer}>
              <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                {tabs.map((tab, index) => (
                  <TouchableOpacity
                    key={index}
                    style={[styles.tab, activeTab === index && styles.activeTab]}
                    onPress={() => setActiveTab(index)}
                  >
                    <Text style={[styles.tabText, activeTab === index && styles.activeTabText]}>
                      {tab}
                    </Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>

            {renderTabContent()}
          </View>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#4A90E2',
    padding: 20,
    paddingTop: 40,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    textAlign: 'center',
  },
  content: {
    flex: 1,
    padding: 20,
  },
  uploadSection: {
    marginBottom: 20,
  },
  uploadButton: {
    backgroundColor: '#4A90E2',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
  },
  uploadButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  imagePreview: {
    marginTop: 15,
    alignItems: 'center',
  },
  previewImage: {
    width: screenWidth - 40,
    height: 200,
    resizeMode: 'contain',
    borderRadius: 8,
  },
  controlsSection: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
    gap: 10,
  },
  analyzeButton: {
    backgroundColor: '#2ECC71',
    padding: 15,
    borderRadius: 8,
    flex: 1,
    alignItems: 'center',
  },
  analyzeButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  disabledButton: {
    backgroundColor: '#95a5a6',
  },
  resetButton: {
    backgroundColor: '#E74C3C',
    padding: 15,
    borderRadius: 8,
    flex: 1,
    alignItems: 'center',
  },
  resetButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  errorContainer: {
    backgroundColor: '#ffebee',
    padding: 15,
    borderRadius: 8,
    marginBottom: 20,
  },
  errorText: {
    color: '#c62828',
    textAlign: 'center',
  },
  resultsSection: {
    marginTop: 20,
  },
  resultsTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 15,
    color: '#333',
  },
  summaryContainer: {
    marginBottom: 20,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
    gap: 10,
  },
  summaryCard: {
    flex: 1,
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  qualityCard: {
    borderLeftWidth: 4,
    borderLeftColor: '#2ECC71',
  },
  sceneCard: {
    borderLeftWidth: 4,
    borderLeftColor: '#3498DB',
  },
  commercialCard: {
    borderLeftWidth: 4,
    borderLeftColor: '#9B59B6',
  },
  timeCard: {
    borderLeftWidth: 4,
    borderLeftColor: '#F39C12',
  },
  cardTitle: {
    fontSize: 12,
    color: '#666',
    marginBottom: 5,
  },
  cardValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  cardSubtext: {
    fontSize: 12,
    color: '#888',
  },
  tabsContainer: {
    marginBottom: 20,
  },
  tab: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    backgroundColor: '#e0e0e0',
    borderRadius: 20,
    marginRight: 10,
  },
  activeTab: {
    backgroundColor: '#4A90E2',
  },
  tabText: {
    color: '#666',
    fontWeight: '500',
  },
  activeTabText: {
    color: 'white',
  },
  tabContent: {
    flex: 1,
  },
  chartContainer: {
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 15,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  chartTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
    textAlign: 'center',
    color: '#333',
  },
  propertiesContainer: {
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 15,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#4A90E2',
  },
  property: {
    fontSize: 14,
    color: '#333',
    marginBottom: 5,
  },
  insightContainer: {
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 15,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  insightText: {
    fontSize: 14,
    color: '#333',
    lineHeight: 20,
  },
  tagText: {
    fontSize: 14,
    color: '#333',
    marginBottom: 3,
  },
});

export default ImageAnalysisInsights;