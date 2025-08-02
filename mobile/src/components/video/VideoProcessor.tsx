import React, { useState, useRef, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Image,
  Alert,
  Modal,
  Switch,
  ActivityIndicator,
  Dimensions,
  FlatList,
  Share,
} from 'react-native';

// Video processing dependencies
import Video from 'react-native-video';
import type { VideoRef } from 'react-native-video';
import DocumentPicker from 'react-native-document-picker';
import RNFS from 'react-native-fs';
import { Slider } from '@react-native-community/slider';
import Icon from 'react-native-vector-icons/MaterialIcons';

const { width: screenWidth } = Dimensions.get('window');

interface VideoMetadata {
  duration: number;
  width: number;
  height: number;
  fps: number;
  bitrate: number;
  codec: string;
  format: string;
  size_bytes: number;
  aspect_ratio: string;
  has_audio: boolean;
}

interface VideoThumbnail {
  timestamp: number;
  image_path: string;
  width: number;
  height: number;
  quality_score: number;
  is_keyframe: boolean;
}

interface VideoChapter {
  start_time: number;
  end_time: number;
  title: string;
  description: string;
  confidence: number;
  keywords?: string[];
}

interface VideoQualityMetrics {
  resolution_score: number;
  bitrate_score: number;
  fps_score: number;
  compression_score: number;
  overall_score: number;
  recommendations: string[];
  technical_details: Record<string, any>;
}

interface ProcessingState {
  isProcessing: boolean;
  currentStep: string;
  progress: number;
  error?: string;
}

const VideoProcessor: React.FC = () => {
  const [videoUri, setVideoUri] = useState<string>('');
  const [videoFile, setVideoFile] = useState<any>(null);
  const [metadata, setMetadata] = useState<VideoMetadata | null>(null);
  const [thumbnails, setThumbnails] = useState<VideoThumbnail[]>([]);
  const [chapters, setChapters] = useState<VideoChapter[]>([]);
  const [qualityMetrics, setQualityMetrics] = useState<VideoQualityMetrics | null>(null);
  const [subtitleUrls, setSubtitleUrls] = useState<{ srt?: string; vtt?: string }>({});
  const [processingState, setProcessingState] = useState<ProcessingState>({
    isProcessing: false,
    currentStep: '',
    progress: 0
  });

  // Video player state
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [showControls, setShowControls] = useState(true);

  // UI state
  const [activeTab, setActiveTab] = useState<'upload' | 'thumbnails' | 'subtitles' | 'chapters' | 'quality' | 'player'>('upload');
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);

  const videoRef = useRef<VideoRef>(null);

  const pickVideo = useCallback(async () => {
    try {
      const result = await DocumentPicker.pick({
        type: [DocumentPicker.types.video],
      });

      if (result && result[0]) {
        const file = result[0];
        setVideoFile(file);
        setVideoUri(file.uri);

        // Reset previous results
        setMetadata(null);
        setThumbnails([]);
        setChapters([]);
        setQualityMetrics(null);
        setSubtitleUrls({});

        Alert.alert('Success', `Video selected: ${file.name}`);
      }
    } catch (error) {
      if (!DocumentPicker.isCancel(error)) {
        Alert.alert('Error', 'Failed to pick video file');
      }
    }
  }, []);

  const extractMetadata = useCallback(async () => {
    if (!videoFile) return;

    setProcessingState({
      isProcessing: true,
      currentStep: 'Extracting video metadata...',
      progress: 10
    });

    try {
      const formData = new FormData();
      formData.append('video', {
        uri: videoFile.uri,
        type: videoFile.type,
        name: videoFile.name,
      } as any);

      const response = await fetch('/api/video/metadata', {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (!response.ok) throw new Error('Failed to extract metadata');

      const data = await response.json();
      setMetadata(data.metadata);

      setProcessingState({
        isProcessing: false,
        currentStep: 'Metadata extracted successfully',
        progress: 100
      });
    } catch (error) {
      setProcessingState({
        isProcessing: false,
        currentStep: '',
        progress: 0,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }, [videoFile]);

  const generateThumbnails = useCallback(async (count: number = 6, qualityThreshold: number = 0.5) => {
    if (!videoFile) return;

    setProcessingState({
      isProcessing: true,
      currentStep: 'Generating video thumbnails...',
      progress: 20
    });

    try {
      const formData = new FormData();
      formData.append('video', {
        uri: videoFile.uri,
        type: videoFile.type,
        name: videoFile.name,
      } as any);
      formData.append('count', count.toString());
      formData.append('quality_threshold', qualityThreshold.toString());

      const response = await fetch('/api/video/thumbnails', {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (!response.ok) throw new Error('Failed to generate thumbnails');

      const data = await response.json();
      setThumbnails(data.thumbnails);

      setProcessingState({
        isProcessing: false,
        currentStep: 'Thumbnails generated successfully',
        progress: 100
      });
    } catch (error) {
      setProcessingState({
        isProcessing: false,
        currentStep: '',
        progress: 0,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }, [videoFile]);

  const generateSubtitles = useCallback(async (format: 'srt' | 'vtt' = 'srt') => {
    setProcessingState({
      isProcessing: true,
      currentStep: `Generating ${format.toUpperCase()} subtitles...`,
      progress: 30
    });

    try {
      const response = await fetch('/api/video/subtitles', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          transcript_data: {}, // Would come from transcription
          format: format,
          max_chars_per_line: 42,
          max_lines: 2
        })
      });

      if (!response.ok) throw new Error('Failed to generate subtitles');

      const text = await response.text();

      // Save subtitle file to device storage
      const fileName = `subtitles_${Date.now()}.${format}`;
      const filePath = `${RNFS.DocumentDirectoryPath}/${fileName}`;

      await RNFS.writeFile(filePath, text, 'utf8');

      setSubtitleUrls(prev => ({
        ...prev,
        [format]: `file://${filePath}`
      }));

      setProcessingState({
        isProcessing: false,
        currentStep: 'Subtitles generated successfully',
        progress: 100
      });
    } catch (error) {
      setProcessingState({
        isProcessing: false,
        currentStep: '',
        progress: 0,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }, []);

  const detectChapters = useCallback(async () => {
    if (!videoFile) return;

    setProcessingState({
      isProcessing: true,
      currentStep: 'Detecting video chapters...',
      progress: 40
    });

    try {
      const formData = new FormData();
      formData.append('video', {
        uri: videoFile.uri,
        type: videoFile.type,
        name: videoFile.name,
      } as any);
      formData.append('transcript_data', JSON.stringify({}));
      formData.append('min_chapter_length', '30');
      formData.append('scene_threshold', '0.3');

      const response = await fetch('/api/video/chapters', {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (!response.ok) throw new Error('Failed to detect chapters');

      const data = await response.json();
      setChapters(data.chapters);

      setProcessingState({
        isProcessing: false,
        currentStep: 'Chapters detected successfully',
        progress: 100
      });
    } catch (error) {
      setProcessingState({
        isProcessing: false,
        currentStep: '',
        progress: 0,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }, [videoFile]);

  const analyzeQuality = useCallback(async () => {
    if (!videoFile) return;

    setProcessingState({
      isProcessing: true,
      currentStep: 'Analyzing video quality...',
      progress: 50
    });

    try {
      const formData = new FormData();
      formData.append('video', {
        uri: videoFile.uri,
        type: videoFile.type,
        name: videoFile.name,
      } as any);

      const response = await fetch('/api/video/quality', {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (!response.ok) throw new Error('Failed to analyze quality');

      const data = await response.json();
      setQualityMetrics(data.quality_metrics);

      setProcessingState({
        isProcessing: false,
        currentStep: 'Quality analysis completed',
        progress: 100
      });
    } catch (error) {
      setProcessingState({
        isProcessing: false,
        currentStep: '',
        progress: 0,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }, [videoFile]);

  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getQualityColor = (score: number): string => {
    if (score >= 0.8) return '#4CAF50';
    if (score >= 0.6) return '#FF9800';
    return '#F44336';
  };

  const shareVideo = async () => {
    if (!videoUri) return;

    try {
      await Share.share({
        url: videoUri,
        title: 'Processed Video',
        message: 'Check out this processed video!',
      });
    } catch (error) {
      Alert.alert('Error', 'Failed to share video');
    }
  };

  const renderTabBar = () => (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.tabBar}>
      {[
        { id: 'upload', label: 'Upload', icon: 'cloud-upload' },
        { id: 'thumbnails', label: 'Thumbnails', icon: 'photo-library' },
        { id: 'subtitles', label: 'Subtitles', icon: 'subtitles' },
        { id: 'chapters', label: 'Chapters', icon: 'bookmark' },
        { id: 'quality', label: 'Quality', icon: 'analytics' },
        { id: 'player', label: 'Player', icon: 'play-circle-filled' }
      ].map(({ id, label, icon }) => (
        <TouchableOpacity
          key={id}
          style={[
            styles.tab,
            activeTab === id && styles.activeTab
          ]}
          onPress={() => setActiveTab(id as any)}
        >
          <Icon name={icon} size={20} color={activeTab === id ? '#fff' : '#666'} />
          <Text style={[
            styles.tabText,
            activeTab === id && styles.activeTabText
          ]}>
            {label}
          </Text>
        </TouchableOpacity>
      ))}
    </ScrollView>
  );

  const renderProcessingStatus = () => {
    if (!processingState.isProcessing && !processingState.error) return null;

    return (
      <View style={styles.processingContainer}>
        {processingState.isProcessing ? (
          <>
            <ActivityIndicator size="small" color="#2196F3" />
            <Text style={styles.processingText}>{processingState.currentStep}</Text>
            <View style={styles.progressBar}>
              <View
                style={[
                  styles.progressFill,
                  { width: `${processingState.progress}%` }
                ]}
              />
            </View>
          </>
        ) : (
          <View style={styles.errorContainer}>
            <Icon name="error" size={20} color="#F44336" />
            <Text style={styles.errorText}>{processingState.error}</Text>
          </View>
        )}
      </View>
    );
  };

  const renderUploadTab = () => (
    <View style={styles.tabContent}>
      <TouchableOpacity style={styles.uploadButton} onPress={pickVideo}>
        <Icon name="cloud-upload" size={48} color="#2196F3" />
        <Text style={styles.uploadText}>Select Video File</Text>
        <Text style={styles.uploadSubtext}>
          Supports MP4, AVI, MOV, MKV and other formats
        </Text>
      </TouchableOpacity>

      {videoFile && (
        <View style={styles.fileInfo}>
          <Text style={styles.fileName}>{videoFile.name}</Text>
          <Text style={styles.fileSize}>
            Size: {(videoFile.size / (1024 * 1024)).toFixed(1)} MB
          </Text>

          <TouchableOpacity
            style={styles.actionButton}
            onPress={extractMetadata}
            disabled={processingState.isProcessing}
          >
            <Text style={styles.actionButtonText}>Extract Metadata</Text>
          </TouchableOpacity>
        </View>
      )}

      {metadata && (
        <View style={styles.metadataContainer}>
          <Text style={styles.sectionTitle}>Video Information</Text>
          <View style={styles.metadataGrid}>
            <View style={styles.metadataItem}>
              <Text style={styles.metadataLabel}>Duration</Text>
              <Text style={styles.metadataValue}>{formatTime(metadata.duration)}</Text>
            </View>
            <View style={styles.metadataItem}>
              <Text style={styles.metadataLabel}>Resolution</Text>
              <Text style={styles.metadataValue}>{metadata.width}×{metadata.height}</Text>
            </View>
            <View style={styles.metadataItem}>
              <Text style={styles.metadataLabel}>Frame Rate</Text>
              <Text style={styles.metadataValue}>{metadata.fps} FPS</Text>
            </View>
            <View style={styles.metadataItem}>
              <Text style={styles.metadataLabel}>Bitrate</Text>
              <Text style={styles.metadataValue}>{(metadata.bitrate / 1000000).toFixed(1)} Mbps</Text>
            </View>
            <View style={styles.metadataItem}>
              <Text style={styles.metadataLabel}>Codec</Text>
              <Text style={styles.metadataValue}>{metadata.codec}</Text>
            </View>
            <View style={styles.metadataItem}>
              <Text style={styles.metadataLabel}>Audio</Text>
              <Text style={styles.metadataValue}>{metadata.has_audio ? 'Yes' : 'No'}</Text>
            </View>
          </View>
        </View>
      )}
    </View>
  );

  const renderThumbnailsTab = () => (
    <View style={styles.tabContent}>
      <View style={styles.actionRow}>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => generateThumbnails(6, 0.5)}
          disabled={!videoFile || processingState.isProcessing}
        >
          <Text style={styles.actionButtonText}>Generate Thumbnails</Text>
        </TouchableOpacity>
      </View>

      {thumbnails.length > 0 && (
        <FlatList
          data={thumbnails}
          numColumns={2}
          keyExtractor={(item, index) => index.toString()}
          renderItem={({ item, index }) => (
            <View style={styles.thumbnailItem}>
              <Image
                source={{ uri: item.image_path }}
                style={styles.thumbnailImage}
                resizeMode="cover"
              />
              <View style={styles.thumbnailInfo}>
                <Text style={styles.thumbnailTime}>{formatTime(item.timestamp)}</Text>
                <View style={styles.qualityRow}>
                  <Icon
                    name="star"
                    size={12}
                    color={getQualityColor(item.quality_score)}
                  />
                  <Text style={[
                    styles.qualityText,
                    { color: getQualityColor(item.quality_score) }
                  ]}>
                    {item.quality_score.toFixed(2)}
                  </Text>
                </View>
              </View>
            </View>
          )}
        />
      )}
    </View>
  );

  const renderSubtitlesTab = () => (
    <View style={styles.tabContent}>
      <View style={styles.actionRow}>
        <TouchableOpacity
          style={[styles.actionButton, { marginRight: 10 }]}
          onPress={() => generateSubtitles('srt')}
          disabled={processingState.isProcessing}
        >
          <Text style={styles.actionButtonText}>Generate SRT</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => generateSubtitles('vtt')}
          disabled={processingState.isProcessing}
        >
          <Text style={styles.actionButtonText}>Generate VTT</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.subtitleResults}>
        {subtitleUrls.srt && (
          <View style={styles.subtitleItem}>
            <Text style={styles.subtitleFormat}>SRT Subtitles</Text>
            <TouchableOpacity style={styles.downloadButton}>
              <Icon name="download" size={16} color="#fff" />
              <Text style={styles.downloadText}>Download SRT</Text>
            </TouchableOpacity>
          </View>
        )}

        {subtitleUrls.vtt && (
          <View style={styles.subtitleItem}>
            <Text style={styles.subtitleFormat}>VTT Subtitles</Text>
            <TouchableOpacity style={styles.downloadButton}>
              <Icon name="download" size={16} color="#fff" />
              <Text style={styles.downloadText}>Download VTT</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
    </View>
  );

  const renderChaptersTab = () => (
    <View style={styles.tabContent}>
      <TouchableOpacity
        style={styles.actionButton}
        onPress={detectChapters}
        disabled={!videoFile || processingState.isProcessing}
      >
        <Text style={styles.actionButtonText}>Detect Chapters</Text>
      </TouchableOpacity>

      {chapters.length > 0 && (
        <FlatList
          data={chapters}
          keyExtractor={(item, index) => index.toString()}
          renderItem={({ item, index }) => (
            <View style={styles.chapterItem}>
              <View style={styles.chapterHeader}>
                <Text style={styles.chapterTitle}>{item.title}</Text>
                <Text style={styles.chapterTime}>
                  {formatTime(item.start_time)} - {formatTime(item.end_time)}
                </Text>
              </View>
              <Text style={styles.chapterDescription}>{item.description}</Text>
              <View style={styles.chapterFooter}>
                <Text style={styles.chapterConfidence}>
                  Confidence: {(item.confidence * 100).toFixed(0)}%
                </Text>
                {item.keywords && (
                  <Text style={styles.chapterKeywords}>
                    Keywords: {item.keywords.slice(0, 3).join(', ')}
                  </Text>
                )}
              </View>
            </View>
          )}
        />
      )}
    </View>
  );

  const renderQualityTab = () => (
    <View style={styles.tabContent}>
      <TouchableOpacity
        style={styles.actionButton}
        onPress={analyzeQuality}
        disabled={!videoFile || processingState.isProcessing}
      >
        <Text style={styles.actionButtonText}>Analyze Quality</Text>
      </TouchableOpacity>

      {qualityMetrics && (
        <View style={styles.qualityResults}>
          <View style={styles.overallScore}>
            <Text style={styles.scoreLabel}>Overall Quality Score</Text>
            <Text style={[
              styles.scoreValue,
              { color: getQualityColor(qualityMetrics.overall_score) }
            ]}>
              {(qualityMetrics.overall_score * 100).toFixed(0)}%
            </Text>
          </View>

          <View style={styles.qualityGrid}>
            {[
              { label: 'Resolution', score: qualityMetrics.resolution_score },
              { label: 'Bitrate', score: qualityMetrics.bitrate_score },
              { label: 'Frame Rate', score: qualityMetrics.fps_score },
              { label: 'Compression', score: qualityMetrics.compression_score }
            ].map(({ label, score }) => (
              <View key={label} style={styles.qualityItem}>
                <Text style={styles.qualityLabel}>{label}</Text>
                <Text style={[
                  styles.qualityScore,
                  { color: getQualityColor(score) }
                ]}>
                  {(score * 100).toFixed(0)}%
                </Text>
              </View>
            ))}
          </View>

          {qualityMetrics.recommendations.length > 0 && (
            <View style={styles.recommendations}>
              <Text style={styles.recommendationsTitle}>Recommendations</Text>
              {qualityMetrics.recommendations.map((rec, index) => (
                <Text key={index} style={styles.recommendationItem}>
                  • {rec}
                </Text>
              ))}
            </View>
          )}
        </View>
      )}
    </View>
  );

  const renderPlayerTab = () => (
    <View style={styles.tabContent}>
      {videoUri && (
        <View style={styles.videoContainer}>
          <Video
            ref={videoRef}
            source={{ uri: videoUri }}
            style={styles.video}
            controls={showControls}
            paused={!isPlaying}
            volume={volume}
            rate={playbackRate}
            onLoad={(data) => {
              setDuration(data.duration);
            }}
            onProgress={(data) => {
              setCurrentTime(data.currentTime);
            }}
            onEnd={() => setIsPlaying(false)}
            resizeMode="contain"
          />

          <View style={styles.playerControls}>
            <TouchableOpacity
              style={styles.controlButton}
              onPress={() => setIsPlaying(!isPlaying)}
            >
              <Icon name={isPlaying ? 'pause' : 'play-arrow'} size={24} color="#fff" />
            </TouchableOpacity>

            <View style={styles.timeContainer}>
              <Text style={styles.timeText}>
                {formatTime(currentTime)} / {formatTime(duration)}
              </Text>
            </View>

            <TouchableOpacity
              style={styles.controlButton}
              onPress={shareVideo}
            >
              <Icon name="share" size={20} color="#fff" />
            </TouchableOpacity>
          </View>

          {chapters.length > 0 && (
            <View style={styles.chaptersContainer}>
              <Text style={styles.chaptersTitle}>Chapters</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                {chapters.map((chapter, index) => (
                  <TouchableOpacity
                    key={index}
                    style={styles.chapterButton}
                    onPress={() => {
                      if (videoRef.current) {
                        videoRef.current.seek(chapter.start_time);
                      }
                    }}
                  >
                    <Text style={styles.chapterButtonText}>{chapter.title}</Text>
                    <Text style={styles.chapterButtonTime}>
                      {formatTime(chapter.start_time)}
                    </Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>
          )}
        </View>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Video Processing Studio</Text>
        <TouchableOpacity
          style={styles.settingsButton}
          onPress={() => setShowSettingsModal(true)}
        >
          <Icon name="settings" size={24} color="#666" />
        </TouchableOpacity>
      </View>

      {renderTabBar()}
      {renderProcessingStatus()}

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {activeTab === 'upload' && renderUploadTab()}
        {activeTab === 'thumbnails' && renderThumbnailsTab()}
        {activeTab === 'subtitles' && renderSubtitlesTab()}
        {activeTab === 'chapters' && renderChaptersTab()}
        {activeTab === 'quality' && renderQualityTab()}
        {activeTab === 'player' && renderPlayerTab()}
      </ScrollView>

      {/* Settings Modal */}
      <Modal
        visible={showSettingsModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowSettingsModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Settings</Text>
              <TouchableOpacity onPress={() => setShowSettingsModal(false)}>
                <Icon name="close" size={24} color="#666" />
              </TouchableOpacity>
            </View>

            <View style={styles.settingItem}>
              <Text style={styles.settingLabel}>Show Video Controls</Text>
              <Switch
                value={showControls}
                onValueChange={setShowControls}
                trackColor={{ false: '#ccc', true: '#2196F3' }}
                thumbColor="#fff"
              />
            </View>

            <View style={styles.settingItem}>
              <Text style={styles.settingLabel}>Volume</Text>
              <Slider
                style={styles.slider}
                value={volume}
                onValueChange={setVolume}
                minimumValue={0}
                maximumValue={1}
                minimumTrackTintColor="#2196F3"
                maximumTrackTintColor="#ccc"
                thumbTintColor="#2196F3"
              />
            </View>

            <View style={styles.settingItem}>
              <Text style={styles.settingLabel}>Playback Speed</Text>
              <View style={styles.speedButtons}>
                {[0.5, 0.75, 1, 1.25, 1.5, 2].map((speed) => (
                  <TouchableOpacity
                    key={speed}
                    style={[
                      styles.speedButton,
                      playbackRate === speed && styles.activeSpeedButton
                    ]}
                    onPress={() => setPlaybackRate(speed)}
                  >
                    <Text style={[
                      styles.speedButtonText,
                      playbackRate === speed && styles.activeSpeedButtonText
                    ]}>
                      {speed}x
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  settingsButton: {
    padding: 8,
  },
  tabBar: {
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  tab: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    marginHorizontal: 4,
    borderRadius: 20,
  },
  activeTab: {
    backgroundColor: '#2196F3',
  },
  tabText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#666',
  },
  activeTabText: {
    color: '#fff',
  },
  content: {
    flex: 1,
  },
  tabContent: {
    padding: 16,
  },
  processingContainer: {
    backgroundColor: '#e3f2fd',
    padding: 16,
    margin: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  processingText: {
    marginTop: 8,
    fontSize: 14,
    color: '#1976d2',
    textAlign: 'center',
  },
  progressBar: {
    width: '100%',
    height: 4,
    backgroundColor: '#bbdefb',
    borderRadius: 2,
    marginTop: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#2196F3',
    borderRadius: 2,
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffebee',
    padding: 16,
    margin: 16,
    borderRadius: 8,
  },
  errorText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#c62828',
    flex: 1,
  },
  uploadButton: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 32,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#e0e0e0',
    borderStyle: 'dashed',
  },
  uploadText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginTop: 16,
  },
  uploadSubtext: {
    fontSize: 14,
    color: '#666',
    marginTop: 8,
    textAlign: 'center',
  },
  fileInfo: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    marginTop: 16,
  },
  fileName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  fileSize: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  actionButton: {
    backgroundColor: '#2196F3',
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 24,
    alignItems: 'center',
    marginTop: 16,
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  actionRow: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  metadataContainer: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    marginTop: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 16,
  },
  metadataGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  metadataItem: {
    width: '48%',
    marginBottom: 16,
  },
  metadataLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  metadataValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  thumbnailItem: {
    flex: 1,
    margin: 8,
    backgroundColor: '#fff',
    borderRadius: 8,
    overflow: 'hidden',
  },
  thumbnailImage: {
    width: '100%',
    height: 120,
  },
  thumbnailInfo: {
    padding: 8,
  },
  thumbnailTime: {
    fontSize: 12,
    color: '#666',
  },
  qualityRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  qualityText: {
    fontSize: 12,
    marginLeft: 4,
    fontWeight: '600',
  },
  subtitleResults: {
    marginTop: 16,
  },
  subtitleItem: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
  },
  subtitleFormat: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  downloadButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#4CAF50',
    borderRadius: 6,
    paddingVertical: 8,
    paddingHorizontal: 16,
    alignSelf: 'flex-start',
  },
  downloadText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 4,
  },
  chapterItem: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
  },
  chapterHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  chapterTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    flex: 1,
  },
  chapterTime: {
    fontSize: 12,
    color: '#666',
  },
  chapterDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  chapterFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  chapterConfidence: {
    fontSize: 12,
    color: '#666',
  },
  chapterKeywords: {
    fontSize: 12,
    color: '#666',
  },
  qualityResults: {
    marginTop: 16,
  },
  overallScore: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 24,
    alignItems: 'center',
    marginBottom: 16,
  },
  scoreLabel: {
    fontSize: 16,
    color: '#666',
    marginBottom: 8,
  },
  scoreValue: {
    fontSize: 32,
    fontWeight: 'bold',
  },
  qualityGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  qualityItem: {
    width: '48%',
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    marginBottom: 8,
  },
  qualityLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  qualityScore: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  recommendations: {
    backgroundColor: '#fff3cd',
    borderRadius: 8,
    padding: 16,
  },
  recommendationsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#856404',
    marginBottom: 8,
  },
  recommendationItem: {
    fontSize: 14,
    color: '#856404',
    marginBottom: 4,
  },
  videoContainer: {
    backgroundColor: '#000',
    borderRadius: 8,
    overflow: 'hidden',
  },
  video: {
    width: '100%',
    height: 200,
  },
  playerControls: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: 'rgba(0,0,0,0.8)',
  },
  controlButton: {
    padding: 8,
  },
  timeContainer: {
    flex: 1,
    alignItems: 'center',
  },
  timeText: {
    color: '#fff',
    fontSize: 14,
  },
  chaptersContainer: {
    backgroundColor: '#fff',
    padding: 16,
  },
  chaptersTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  chapterButton: {
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    padding: 12,
    marginRight: 12,
    minWidth: 120,
  },
  chapterButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  chapterButtonTime: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  settingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  settingLabel: {
    fontSize: 16,
    color: '#333',
  },
  slider: {
    width: 120,
    height: 40,
  },
  speedButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  speedButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#f5f5f5',
    marginLeft: 8,
    marginBottom: 8,
  },
  activeSpeedButton: {
    backgroundColor: '#2196F3',
  },
  speedButtonText: {
    fontSize: 14,
    color: '#666',
  },
  activeSpeedButtonText: {
    color: '#fff',
  },
});

export default VideoProcessor;