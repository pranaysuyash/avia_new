/**
 * Media Intelligence Screen - React Native
 * Video and image analysis with scene detection and highlights
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
  Alert,
  Dimensions,
  Image,
  FlatList,
} from 'react-native';
import {
  Card,
  ProgressBar,
  Chip,
  List,
  Avatar,
  IconButton,
  Surface,
  Badge,
  FAB,
  Portal,
  Modal,
  Button,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import DocumentPicker from 'react-native-document-picker';
import Video from 'react-native-video';
import Share from 'react-native-share';
import { LineChart, ProgressChart } from 'react-native-chart-kit';

const { width: screenWidth } = Dimensions.get('window');

interface Scene {
  id: string;
  type: string;
  start: number;
  end: number;
  confidence: number;
  thumbnail?: string;
}

interface Highlight {
  id: string;
  start: number;
  end: number;
  score: number;
  reason: string;
  thumbnail?: string;
}

interface MediaAnalysis {
  assetId: string;
  mediaType: string;
  duration: number;
  resolution: string;
  fps: number;
  qualityScore: number;
  scenes: Scene[];
  highlights: Highlight[];
  detectedObjects: Record<string, number>;
  detectedBrands: string[];
  uniqueFaces: number;
  viralPotential: number;
  colorPalette: string[];
  autoChapters: Array<{
    title: string;
    start: number;
    end: number;
  }>;
}

interface MediaIntelligenceProps {
  apiEndpoint?: string;
  onAnalysisComplete?: (analysis: MediaAnalysis) => void;
}

const MediaIntelligence: React.FC<MediaIntelligenceProps> = ({
  apiEndpoint = '/api/intelligence/media/analyze',
  onAnalysisComplete,
}) => {
  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<MediaAnalysis | null>(null);
  const [selectedScene, setSelectedScene] = useState<Scene | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [activeStep, setActiveStep] = useState(0);

  const selectFile = useCallback(async () => {
    try {
      const result = await DocumentPicker.pick({
        type: [DocumentPicker.types.video, DocumentPicker.types.images],
      });
      
      setSelectedFile(result[0]);
    } catch (err) {
      if (!DocumentPicker.isCancel(err)) {
        Alert.alert('Error', 'Failed to select file');
        console.error('File selection error:', err);
      }
    }
  }, []);

  const analyzeMedia = useCallback(async () => {
    if (!selectedFile) {
      Alert.alert('Error', 'Please select a media file to analyze');
      return;
    }

    setIsAnalyzing(true);
    setActiveStep(0);

    try {
      // Mock analysis for demonstration
      const mockAnalysis: MediaAnalysis = {
        assetId: `media_${Date.now()}`,
        mediaType: selectedFile.type?.includes('video') ? 'video' : 'image',
        duration: 180.5,
        resolution: '1920x1080',
        fps: 30,
        qualityScore: 0.88,
        scenes: [
          { id: 's1', type: 'intro', start: 0, end: 10, confidence: 0.92 },
          { id: 's2', type: 'content', start: 10, end: 60, confidence: 0.88 },
          { id: 's3', type: 'interview', start: 60, end: 120, confidence: 0.95 },
          { id: 's4', type: 'action', start: 120, end: 170, confidence: 0.85 },
          { id: 's5', type: 'outro', start: 170, end: 180.5, confidence: 0.90 },
        ],
        highlights: [
          { id: 'h1', start: 15, end: 25, score: 0.92, reason: 'High engagement moment' },
          { id: 'h2', start: 75, end: 85, score: 0.88, reason: 'Key dialogue' },
          { id: 'h3', start: 125, end: 135, score: 0.95, reason: 'Peak action' },
        ],
        detectedObjects: {
          'person': 15,
          'car': 3,
          'building': 8,
          'tree': 12,
        },
        detectedBrands: ['Apple', 'Nike', 'Google'],
        uniqueFaces: 4,
        viralPotential: 0.72,
        colorPalette: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'],
        autoChapters: [
          { title: 'Introduction', start: 0, end: 10 },
          { title: 'Main Content', start: 10, end: 60 },
          { title: 'Interview Segment', start: 60, end: 120 },
          { title: 'Action Sequence', start: 120, end: 170 },
          { title: 'Conclusion', start: 170, end: 180.5 },
        ],
      };

      // Simulate processing steps
      const steps = ['Upload', 'Scene Detection', 'Object Analysis', 'Highlight Extraction'];
      for (let i = 0; i < steps.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        setActiveStep(i + 1);
      }

      setAnalysis(mockAnalysis);
      
      if (onAnalysisComplete) {
        onAnalysisComplete(mockAnalysis);
      }
    } catch (err) {
      Alert.alert('Error', 'Failed to analyze media. Please try again.');
      console.error('Analysis error:', err);
    } finally {
      setIsAnalyzing(false);
    }
  }, [selectedFile, onAnalysisComplete]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const exportAnalysis = useCallback(async () => {
    if (!analysis) return;

    try {
      const shareOptions = {
        title: 'Media Analysis Results',
        message: `Media Analysis Report
        
Asset ID: ${analysis.assetId}
Type: ${analysis.mediaType}
Duration: ${analysis.duration}s
Resolution: ${analysis.resolution}
Quality Score: ${(analysis.qualityScore * 100).toFixed(0)}%
Viral Potential: ${(analysis.viralPotential * 100).toFixed(0)}%

Scenes Detected: ${analysis.scenes.length}
Highlights Found: ${analysis.highlights.length}
Unique Faces: ${analysis.uniqueFaces}
Brands Detected: ${analysis.detectedBrands.join(', ')}`,
      };

      await Share.open(shareOptions);
    } catch (error) {
      console.log('Share error:', error);
    }
  }, [analysis]);

  const renderUploadSection = () => (
    <Card style={styles.uploadCard}>
      <Card.Content>
        <TouchableOpacity style={styles.uploadButton} onPress={selectFile}>
          <Icon name="cloud-upload" size={48} color="#667eea" />
          <Text style={styles.uploadText}>Tap to select media file</Text>
          <Text style={styles.uploadSubtext}>Supports MP4, AVI, MOV, JPG, PNG</Text>
        </TouchableOpacity>
        
        {selectedFile && (
          <View style={styles.selectedFileContainer}>
            <Chip icon="file" mode="outlined" style={styles.fileChip}>
              {selectedFile.name}
            </Chip>
            <IconButton
              icon="close"
              size={20}
              onPress={() => setSelectedFile(null)}
            />
          </View>
        )}

        {selectedFile && (
          <Button
            mode="contained"
            onPress={analyzeMedia}
            loading={isAnalyzing}
            disabled={isAnalyzing}
            style={styles.analyzeButton}
            icon="brain"
          >
            {isAnalyzing ? 'Analyzing Media...' : 'Analyze Media'}
          </Button>
        )}

        {isAnalyzing && (
          <View style={styles.progressContainer}>
            <Text style={styles.progressText}>
              {['Uploading', 'Detecting Scenes', 'Analyzing Objects', 'Extracting Highlights'][activeStep] || 'Processing...'}
            </Text>
            <ProgressBar progress={(activeStep + 1) / 4} color="#667eea" style={styles.progressBar} />
          </View>
        )}
      </Card.Content>
    </Card>
  );

  const renderQualityMetrics = () => {
    if (!analysis) return null;

    const data = {
      labels: ['Quality'],
      data: [analysis.qualityScore],
    };

    return (
      <View style={styles.metricsRow}>
        <Surface style={styles.metricCard} elevation={2}>
          <View style={styles.qualityIndicator}>
            <Text style={styles.qualityScore}>{(analysis.qualityScore * 100).toFixed(0)}%</Text>
          </View>
          <Text style={styles.metricLabel}>Quality Score</Text>
        </Surface>

        <Surface style={styles.metricCard} elevation={2}>
          <Badge size={40} style={styles.badge}>{analysis.scenes.length}</Badge>
          <Icon name="movie-open-outline" size={32} color="#764ba2" />
          <Text style={styles.metricLabel}>Scenes</Text>
        </Surface>

        <Surface style={styles.metricCard} elevation={2}>
          <Badge size={40} style={[styles.badge, { backgroundColor: '#f093fb' }]}>
            {analysis.highlights.length}
          </Badge>
          <Icon name="auto-awesome" size={32} color="#f093fb" />
          <Text style={styles.metricLabel}>Highlights</Text>
        </Surface>
      </View>
    );
  };

  const renderSceneTimeline = () => {
    if (!analysis) return null;

    return (
      <Card style={styles.card}>
        <Card.Title 
          title="Scene Timeline" 
          left={(props) => <Avatar.Icon {...props} icon="timeline" />}
        />
        <Card.Content>
          <FlatList
            data={analysis.scenes}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => {
              const hasHighlight = analysis.highlights.some(
                h => h.start >= item.start && h.end <= item.end
              );
              
              return (
                <TouchableOpacity 
                  style={[styles.sceneItem, hasHighlight && styles.sceneHighlight]}
                  onPress={() => {
                    setSelectedScene(item);
                    setModalVisible(true);
                  }}
                >
                  <View style={styles.sceneContent}>
                    <Icon 
                      name={item.type === 'action' ? 'run-fast' : 'play-circle-outline'} 
                      size={24} 
                      color={hasHighlight ? '#f093fb' : '#667eea'} 
                    />
                    <View style={styles.sceneDetails}>
                      <Text style={styles.sceneTitle}>
                        {item.type.charAt(0).toUpperCase() + item.type.slice(1)}
                      </Text>
                      <Text style={styles.sceneTime}>
                        {formatTime(item.start)} - {formatTime(item.end)}
                      </Text>
                    </View>
                    <Chip mode="flat" style={styles.confidenceChip}>
                      {(item.confidence * 100).toFixed(0)}%
                    </Chip>
                  </View>
                </TouchableOpacity>
              );
            }}
          />
        </Card.Content>
      </Card>
    );
  };

  const renderHighlights = () => {
    if (!analysis) return null;

    return (
      <Card style={styles.card}>
        <Card.Title 
          title="Key Highlights" 
          left={(props) => <Avatar.Icon {...props} icon="star" style={{ backgroundColor: '#f093fb' }} />}
        />
        <Card.Content>
          {analysis.highlights.map((highlight) => (
            <View key={highlight.id} style={styles.highlightItem}>
              <View style={styles.highlightScore}>
                <Text style={styles.highlightScoreText}>
                  {(highlight.score * 100).toFixed(0)}%
                </Text>
              </View>
              <View style={styles.highlightDetails}>
                <Text style={styles.highlightReason}>{highlight.reason}</Text>
                <Text style={styles.highlightTime}>
                  {formatTime(highlight.start)} - {formatTime(highlight.end)}
                </Text>
              </View>
              <IconButton icon="play" onPress={() => Alert.alert('Preview', 'Preview not available in demo')} />
            </View>
          ))}
        </Card.Content>
      </Card>
    );
  };

  const renderObjectsAndBrands = () => {
    if (!analysis) return null;

    return (
      <View style={styles.row}>
        <Card style={[styles.card, styles.halfCard]}>
          <Card.Title title="Detected Objects" titleStyle={styles.smallTitle} />
          <Card.Content>
            {Object.entries(analysis.detectedObjects).slice(0, 4).map(([object, count]) => (
              <View key={object} style={styles.objectItem}>
                <Text style={styles.objectName}>{object}</Text>
                <Text style={styles.objectCount}>{count}</Text>
              </View>
            ))}
          </Card.Content>
        </Card>

        <Card style={[styles.card, styles.halfCard]}>
          <Card.Title title="Brands & Info" titleStyle={styles.smallTitle} />
          <Card.Content>
            {analysis.detectedBrands.map((brand) => (
              <Chip key={brand} style={styles.brandChip} mode="outlined">
                {brand}
              </Chip>
            ))}
            <Text style={styles.infoText}>
              {analysis.uniqueFaces} unique faces detected
            </Text>
          </Card.Content>
        </Card>
      </View>
    );
  };

  const renderColorPalette = () => {
    if (!analysis) return null;

    return (
      <Card style={styles.card}>
        <Card.Title 
          title="Color Palette" 
          left={(props) => <Avatar.Icon {...props} icon="palette" />}
        />
        <Card.Content>
          <View style={styles.colorPalette}>
            {analysis.colorPalette.map((color, index) => (
              <View
                key={index}
                style={[styles.colorSwatch, { backgroundColor: color }]}
              />
            ))}
          </View>
          <View style={styles.viralContainer}>
            <Text style={styles.viralLabel}>Viral Potential</Text>
            <ProgressBar 
              progress={analysis.viralPotential} 
              color="#4caf50" 
              style={styles.viralBar}
            />
            <Text style={styles.viralScore}>
              {(analysis.viralPotential * 100).toFixed(0)}%
            </Text>
          </View>
        </Card.Content>
      </Card>
    );
  };

  return (
    <View style={styles.container}>
      <Surface style={styles.header} elevation={4}>
        <View style={styles.headerContent}>
          <Icon name="movie" size={32} color="white" />
          <View style={styles.headerText}>
            <Text style={styles.headerTitle}>Media Intelligence</Text>
            <Text style={styles.headerSubtitle}>
              Analyze videos and images with AI
            </Text>
          </View>
        </View>
      </Surface>

      <ScrollView style={styles.content}>
        {!analysis && renderUploadSection()}
        
        {analysis && (
          <>
            {renderQualityMetrics()}
            {renderSceneTimeline()}
            {renderHighlights()}
            {renderObjectsAndBrands()}
            {renderColorPalette()}
            
            <Button
              mode="contained"
              onPress={exportAnalysis}
              style={styles.exportButton}
              icon="share-variant"
            >
              Share Analysis
            </Button>
          </>
        )}
      </ScrollView>

      <Portal>
        <Modal
          visible={modalVisible}
          onDismiss={() => setModalVisible(false)}
          contentContainerStyle={styles.modal}
        >
          {selectedScene && (
            <>
              <Text style={styles.modalTitle}>Scene Details</Text>
              <Text style={styles.modalText}>Type: {selectedScene.type}</Text>
              <Text style={styles.modalText}>
                Duration: {formatTime(selectedScene.start)} - {formatTime(selectedScene.end)}
              </Text>
              <Text style={styles.modalText}>
                Confidence: {(selectedScene.confidence * 100).toFixed(0)}%
              </Text>
              <Button onPress={() => setModalVisible(false)}>Close</Button>
            </>
          )}
        </Modal>
      </Portal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#f093fb',
    paddingVertical: 20,
    paddingHorizontal: 16,
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerText: {
    marginLeft: 12,
    flex: 1,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
  },
  headerSubtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.9)',
    marginTop: 2,
  },
  content: {
    flex: 1,
    padding: 16,
  },
  uploadCard: {
    marginBottom: 16,
  },
  uploadButton: {
    alignItems: 'center',
    paddingVertical: 32,
    borderWidth: 2,
    borderColor: '#e0e0e0',
    borderRadius: 12,
    borderStyle: 'dashed',
  },
  uploadText: {
    fontSize: 16,
    fontWeight: 'bold',
    marginTop: 12,
    color: '#333',
  },
  uploadSubtext: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  selectedFileContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 16,
  },
  fileChip: {
    flex: 1,
  },
  analyzeButton: {
    marginTop: 16,
  },
  progressContainer: {
    marginTop: 16,
  },
  progressText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  progressBar: {
    height: 8,
    borderRadius: 4,
  },
  metricsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  metricCard: {
    flex: 1,
    padding: 16,
    marginHorizontal: 4,
    borderRadius: 12,
    alignItems: 'center',
  },
  qualityIndicator: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#4caf50',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  qualityScore: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  metricLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  badge: {
    position: 'absolute',
    top: -8,
    right: -8,
    backgroundColor: '#667eea',
  },
  card: {
    marginBottom: 16,
  },
  sceneItem: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginBottom: 8,
    backgroundColor: 'white',
  },
  sceneHighlight: {
    backgroundColor: '#fce4ec',
    borderWidth: 1,
    borderColor: '#f093fb',
  },
  sceneContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  sceneDetails: {
    flex: 1,
    marginLeft: 12,
  },
  sceneTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
  },
  sceneTime: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  confidenceChip: {
    height: 24,
  },
  highlightItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  highlightScore: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#f093fb',
    alignItems: 'center',
    justifyContent: 'center',
  },
  highlightScoreText: {
    color: 'white',
    fontWeight: 'bold',
  },
  highlightDetails: {
    flex: 1,
    marginLeft: 12,
  },
  highlightReason: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
  },
  highlightTime: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  halfCard: {
    flex: 1,
    marginHorizontal: 4,
  },
  smallTitle: {
    fontSize: 16,
  },
  objectItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 4,
  },
  objectName: {
    fontSize: 14,
    color: '#333',
  },
  objectCount: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#667eea',
  },
  brandChip: {
    marginRight: 8,
    marginBottom: 8,
  },
  infoText: {
    fontSize: 12,
    color: '#666',
    marginTop: 8,
  },
  colorPalette: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
  },
  colorSwatch: {
    width: 40,
    height: 40,
    borderRadius: 8,
    borderWidth: 2,
    borderColor: 'white',
    elevation: 2,
  },
  viralContainer: {
    marginTop: 8,
  },
  viralLabel: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  viralBar: {
    height: 8,
    borderRadius: 4,
  },
  viralScore: {
    fontSize: 12,
    color: '#4caf50',
    marginTop: 4,
    textAlign: 'right',
  },
  exportButton: {
    marginBottom: 24,
  },
  modal: {
    backgroundColor: 'white',
    padding: 20,
    margin: 20,
    borderRadius: 8,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  modalText: {
    fontSize: 14,
    marginBottom: 8,
  },
});

export default MediaIntelligence;