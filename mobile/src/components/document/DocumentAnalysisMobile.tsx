import React, { useState, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
  Platform,
  Dimensions,
  Modal,
  FlatList,
  Share,
  ProgressBarAndroid,
  ProgressViewIOS,
} from 'react-native';
import DocumentPicker from 'react-native-document-picker';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { apiClient } from '../../services/api';
import { theme } from '../../theme';

const { width: screenWidth } = Dimensions.get('window');

interface DocumentMetadata {
  filename: string;
  file_type: string;
  file_size: number;
  page_count?: number;
  language?: string;
}

interface Entity {
  text: string;
  type: string;
  confidence?: number;
}

interface Topic {
  name: string;
  score: number;
  keywords: string[];
}

interface AnalysisConfig {
  enable_ocr: boolean;
  enable_nlp: boolean;
  enable_entity_extraction: boolean;
  enable_summarization: boolean;
  enable_sentiment_analysis: boolean;
  enable_key_phrases: boolean;
  enable_language_detection: boolean;
}

interface AnalysisResults {
  task_id: string;
  status: string;
  metadata?: DocumentMetadata;
  text_content?: string;
  summary?: string;
  entities?: Entity[];
  key_phrases?: string[];
  sentiment?: Record<string, number>;
  language?: string;
  topics?: Topic[];
  processing_time?: number;
  timestamp?: string;
  error?: string;
}

const ProgressBar = ({ progress }: { progress: number }) => {
  if (Platform.OS === 'android') {
    return (
      <ProgressBarAndroid
        styleAttr="Horizontal"
        indeterminate={false}
        progress={progress}
        color={theme.colors.primary}
      />
    );
  } else {
    return (
      <ProgressViewIOS
        progress={progress}
        progressTintColor={theme.colors.primary}
      />
    );
  }
};

const DocumentAnalysisMobile: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState<'summary' | 'entities' | 'phrases' | 'sentiment'>('summary');
  const [showSettings, setShowSettings] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [expandedTopic, setExpandedTopic] = useState<number | null>(null);
  const [analysisConfig, setAnalysisConfig] = useState<AnalysisConfig>({
    enable_ocr: true,
    enable_nlp: true,
    enable_entity_extraction: true,
    enable_summarization: true,
    enable_sentiment_analysis: true,
    enable_key_phrases: true,
    enable_language_detection: true,
  });

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const templates = [
    { id: 'legal_contract', name: 'Legal Contract', description: 'Analyze contracts for key terms' },
    { id: 'research_paper', name: 'Research Paper', description: 'Extract findings and citations' },
    { id: 'financial_report', name: 'Financial Report', description: 'Analyze financial metrics' },
    { id: 'resume', name: 'Resume', description: 'Extract skills and experience' },
  ];

  const pickDocument = async () => {
    try {
      const res = await DocumentPicker.pick({
        type: [
          DocumentPicker.types.pdf,
          DocumentPicker.types.docx,
          DocumentPicker.types.doc,
          DocumentPicker.types.plainText,
          DocumentPicker.types.xlsx,
          DocumentPicker.types.xls,
        ],
      });

      setSelectedFile(res[0]);
      setResults(null);
      setError(null);
    } catch (err) {
      if (DocumentPicker.isCancel(err)) {
        // User cancelled
      } else {
        setError('Failed to pick document');
      }
    }
  };

  const analyzeDocument = async () => {
    if (!selectedFile) return;

    try {
      setAnalyzing(true);
      setError(null);

      const formData = new FormData();
      formData.append('file', {
        uri: selectedFile.uri,
        type: selectedFile.type,
        name: selectedFile.name,
      } as any);
      formData.append('analysis_config', JSON.stringify(analysisConfig));
      formData.append('output_format', 'json');

      const response = await apiClient.post('/api/v1/document-analysis/analyze/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
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
        const response = await apiClient.get(`/api/v1/document-analysis/status/${taskId}`);
        const data = response.data;

        if (data.status === 'completed' && data.result) {
          setResults(data.result);
          setAnalyzing(false);
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
          }
        } else if (data.status === 'failed') {
          setError(data.message || 'Analysis failed');
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
    setSelectedFile(null);
    setResults(null);
    setError(null);
    setAnalyzing(false);
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }
  };

  const shareResults = async () => {
    if (!results) return;

    try {
      const message = `Document Analysis Results for ${results.metadata?.filename}:\n\n` +
        `Summary: ${results.summary?.substring(0, 200)}...\n\n` +
        `Entities: ${results.entities?.length || 0}\n` +
        `Key Phrases: ${results.key_phrases?.length || 0}\n` +
        `Language: ${results.language || 'Unknown'}`;

      await Share.share({
        message,
        title: 'Document Analysis Results',
      });
    } catch (error) {
      Alert.alert('Error', 'Failed to share results');
    }
  };

  const applyTemplate = (templateId: string) => {
    const template = templates.find(t => t.id === templateId);
    if (template) {
      // Apply template-specific configuration
      if (templateId === 'legal_contract') {
        setAnalysisConfig({
          ...analysisConfig,
          enable_entity_extraction: true,
          enable_key_phrases: true,
          enable_sentiment_analysis: false,
        });
      }
      // Add more template configurations as needed
      setSelectedTemplate(templateId);
    }
  };

  const getFileIcon = (fileType?: string) => {
    if (!fileType) return 'description';
    if (fileType.includes('pdf')) return 'picture-as-pdf';
    if (fileType.includes('word')) return 'article';
    if (fileType.includes('excel')) return 'table-chart';
    return 'description';
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return theme.colors.success;
      case 'negative':
        return theme.colors.error;
      default:
        return theme.colors.warning;
    }
  };

  const getEntityColor = (type: string): string => {
    const colors: Record<string, string> = {
      person: '#2196F3',
      organization: '#4CAF50',
      location: '#FF9800',
      date: '#9C27B0',
      money: '#F44336',
      default: '#757575',
    };
    return colors[type.toLowerCase()] || colors.default;
  };

  const renderEntity = ({ item }: { item: Entity }) => (
    <View style={styles.entityItem}>
      <View
        style={[
          styles.entityTypeChip,
          { backgroundColor: getEntityColor(item.type) }
        ]}
      >
        <Text style={styles.entityTypeText}>{item.type}</Text>
      </View>
      <Text style={styles.entityText}>{item.text}</Text>
    </View>
  );

  const renderKeyPhrase = ({ item }: { item: string }) => (
    <TouchableOpacity
      style={styles.keyPhraseChip}
      onPress={() => {
        // Copy to clipboard
        Alert.alert('Copied', `"${item}" copied to clipboard`);
      }}
    >
      <Text style={styles.keyPhraseText}>{item}</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            <Icon name="analytics" size={24} color={theme.colors.primary} />
            <Text style={styles.title}>Document Analysis</Text>
          </View>
          <TouchableOpacity onPress={() => setShowSettings(true)}>
            <Icon name="settings" size={24} color={theme.colors.text} />
          </TouchableOpacity>
        </View>

        {/* File Selection */}
        {!selectedFile ? (
          <TouchableOpacity style={styles.uploadCard} onPress={pickDocument}>
            <Icon name="cloud-upload" size={48} color={theme.colors.textSecondary} />
            <Text style={styles.uploadText}>Tap to select a document</Text>
            <Text style={styles.uploadSubtext}>
              Supports PDF, DOCX, TXT, XLSX
            </Text>
          </TouchableOpacity>
        ) : (
          <View style={styles.selectedFileCard}>
            <Icon
              name={getFileIcon(selectedFile.type)}
              size={40}
              color={theme.colors.primary}
            />
            <View style={styles.fileInfo}>
              <Text style={styles.fileName} numberOfLines={1}>
                {selectedFile.name}
              </Text>
              <Text style={styles.fileSize}>
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </Text>
            </View>
            <TouchableOpacity onPress={resetAnalysis}>
              <Icon name="close" size={24} color={theme.colors.textSecondary} />
            </TouchableOpacity>
          </View>
        )}

        {/* Templates */}
        <View style={styles.templatesSection}>
          <Text style={styles.sectionTitle}>Quick Templates</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {templates.map(template => (
              <TouchableOpacity
                key={template.id}
                style={[
                  styles.templateCard,
                  selectedTemplate === template.id && styles.templateCardActive
                ]}
                onPress={() => applyTemplate(template.id)}
              >
                <Text style={[
                  styles.templateName,
                  selectedTemplate === template.id && styles.templateNameActive
                ]}>
                  {template.name}
                </Text>
                <Text style={styles.templateDescription}>
                  {template.description}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        {/* Analyze Button */}
        {selectedFile && !results && (
          <TouchableOpacity
            style={[styles.analyzeButton, analyzing && styles.analyzeButtonDisabled]}
            onPress={analyzeDocument}
            disabled={analyzing}
          >
            {analyzing ? (
              <>
                <ActivityIndicator color="#fff" size="small" />
                <Text style={styles.analyzeButtonText}>Analyzing...</Text>
              </>
            ) : (
              <>
                <Icon name="analytics" size={20} color="#fff" />
                <Text style={styles.analyzeButtonText}>Analyze Document</Text>
              </>
            )}
          </TouchableOpacity>
        )}

        {/* Error Message */}
        {error && (
          <View style={styles.errorContainer}>
            <Icon name="error" size={20} color={theme.colors.error} />
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {/* Results */}
        {results && (
          <>
            {/* Metadata */}
            <View style={styles.metadataCard}>
              <View style={styles.metadataRow}>
                <Text style={styles.metadataLabel}>Document:</Text>
                <Text style={styles.metadataValue} numberOfLines={1}>
                  {results.metadata?.filename}
                </Text>
              </View>
              <View style={styles.metadataRow}>
                <Text style={styles.metadataLabel}>Pages:</Text>
                <Text style={styles.metadataValue}>
                  {results.metadata?.page_count || 'N/A'}
                </Text>
              </View>
              <View style={styles.metadataRow}>
                <Text style={styles.metadataLabel}>Language:</Text>
                <Text style={styles.metadataValue}>
                  {results.language || 'Unknown'}
                </Text>
              </View>
              <View style={styles.metadataRow}>
                <Text style={styles.metadataLabel}>Processing:</Text>
                <Text style={styles.metadataValue}>
                  {results.processing_time?.toFixed(1)}s
                </Text>
              </View>
            </View>

            {/* Stats */}
            <View style={styles.statsContainer}>
              <View style={styles.statBox}>
                <Text style={styles.statValue}>{results.entities?.length || 0}</Text>
                <Text style={styles.statLabel}>Entities</Text>
              </View>
              <View style={styles.statBox}>
                <Text style={styles.statValue}>{results.key_phrases?.length || 0}</Text>
                <Text style={styles.statLabel}>Key Phrases</Text>
              </View>
              <View style={styles.statBox}>
                <Text style={styles.statValue}>{results.topics?.length || 0}</Text>
                <Text style={styles.statLabel}>Topics</Text>
              </View>
            </View>

            {/* Tabs */}
            <View style={styles.tabs}>
              <TouchableOpacity
                style={[styles.tab, selectedTab === 'summary' && styles.activeTab]}
                onPress={() => setSelectedTab('summary')}
              >
                <Text style={[styles.tabText, selectedTab === 'summary' && styles.activeTabText]}>
                  Summary
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.tab, selectedTab === 'entities' && styles.activeTab]}
                onPress={() => setSelectedTab('entities')}
              >
                <Text style={[styles.tabText, selectedTab === 'entities' && styles.activeTabText]}>
                  Entities
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.tab, selectedTab === 'phrases' && styles.activeTab]}
                onPress={() => setSelectedTab('phrases')}
              >
                <Text style={[styles.tabText, selectedTab === 'phrases' && styles.activeTabText]}>
                  Phrases
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.tab, selectedTab === 'sentiment' && styles.activeTab]}
                onPress={() => setSelectedTab('sentiment')}
              >
                <Text style={[styles.tabText, selectedTab === 'sentiment' && styles.activeTabText]}>
                  Sentiment
                </Text>
              </TouchableOpacity>
            </View>

            {/* Tab Content */}
            <View style={styles.tabContent}>
              {selectedTab === 'summary' && (
                <View style={styles.summaryContainer}>
                  <Text style={styles.summaryText}>
                    {results.summary || 'No summary available'}
                  </Text>
                  {results.topics && results.topics.length > 0 && (
                    <View style={styles.topicsSection}>
                      <Text style={styles.topicsSectionTitle}>Topics</Text>
                      {results.topics.map((topic, index) => (
                        <TouchableOpacity
                          key={index}
                          style={styles.topicItem}
                          onPress={() => setExpandedTopic(expandedTopic === index ? null : index)}
                        >
                          <View style={styles.topicHeader}>
                            <Text style={styles.topicName}>{topic.name}</Text>
                            <Text style={styles.topicScore}>
                              {(topic.score * 100).toFixed(0)}%
                            </Text>
                            <Icon
                              name={expandedTopic === index ? 'expand-less' : 'expand-more'}
                              size={20}
                              color={theme.colors.textSecondary}
                            />
                          </View>
                          {expandedTopic === index && (
                            <View style={styles.topicKeywords}>
                              {topic.keywords.map((keyword, i) => (
                                <Text key={i} style={styles.keyword}>
                                  • {keyword}
                                </Text>
                              ))}
                            </View>
                          )}
                        </TouchableOpacity>
                      ))}
                    </View>
                  )}
                </View>
              )}

              {selectedTab === 'entities' && (
                <FlatList
                  data={results.entities || []}
                  renderItem={renderEntity}
                  keyExtractor={(item, index) => `${item.type}-${index}`}
                  contentContainerStyle={styles.entitiesList}
                  ListEmptyComponent={
                    <Text style={styles.emptyText}>No entities found</Text>
                  }
                />
              )}

              {selectedTab === 'phrases' && (
                <FlatList
                  data={results.key_phrases || []}
                  renderItem={renderKeyPhrase}
                  keyExtractor={(item, index) => `phrase-${index}`}
                  numColumns={2}
                  columnWrapperStyle={styles.phrasesRow}
                  contentContainerStyle={styles.phrasesList}
                  ListEmptyComponent={
                    <Text style={styles.emptyText}>No key phrases found</Text>
                  }
                />
              )}

              {selectedTab === 'sentiment' && (
                <View style={styles.sentimentContainer}>
                  {results.sentiment ? (
                    Object.entries(results.sentiment).map(([sentiment, score]) => (
                      <View key={sentiment} style={styles.sentimentItem}>
                        <View style={styles.sentimentHeader}>
                          <Icon
                            name={
                              sentiment === 'positive' ? 'sentiment-satisfied' :
                              sentiment === 'negative' ? 'sentiment-dissatisfied' :
                              'sentiment-neutral'
                            }
                            size={24}
                            color={getSentimentColor(sentiment)}
                          />
                          <Text style={styles.sentimentLabel}>
                            {sentiment.charAt(0).toUpperCase() + sentiment.slice(1)}
                          </Text>
                          <Text style={styles.sentimentScore}>
                            {(score * 100).toFixed(1)}%
                          </Text>
                        </View>
                        <View style={styles.sentimentBar}>
                          <View
                            style={[
                              styles.sentimentProgress,
                              {
                                width: `${score * 100}%`,
                                backgroundColor: getSentimentColor(sentiment),
                              }
                            ]}
                          />
                        </View>
                      </View>
                    ))
                  ) : (
                    <Text style={styles.emptyText}>No sentiment analysis available</Text>
                  )}
                </View>
              )}
            </View>

            {/* Actions */}
            <View style={styles.actions}>
              <TouchableOpacity style={styles.actionButton} onPress={shareResults}>
                <Icon name="share" size={20} color={theme.colors.primary} />
                <Text style={styles.actionButtonText}>Share</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.actionButton} onPress={resetAnalysis}>
                <Icon name="refresh" size={20} color={theme.colors.primary} />
                <Text style={styles.actionButtonText}>New Analysis</Text>
              </TouchableOpacity>
            </View>
          </>
        )}
      </ScrollView>

      {/* Settings Modal */}
      <Modal
        visible={showSettings}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowSettings(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Analysis Settings</Text>
              <TouchableOpacity onPress={() => setShowSettings(false)}>
                <Icon name="close" size={24} color={theme.colors.text} />
              </TouchableOpacity>
            </View>

            <ScrollView>
              <View style={styles.settingItem}>
                <Text style={styles.settingLabel}>OCR Processing</Text>
                <TouchableOpacity
                  style={[styles.toggle, analysisConfig.enable_ocr && styles.toggleActive]}
                  onPress={() => setAnalysisConfig({ ...analysisConfig, enable_ocr: !analysisConfig.enable_ocr })}
                >
                  <View style={[styles.toggleHandle, analysisConfig.enable_ocr && styles.toggleHandleActive]} />
                </TouchableOpacity>
              </View>

              <View style={styles.settingItem}>
                <Text style={styles.settingLabel}>Entity Extraction</Text>
                <TouchableOpacity
                  style={[styles.toggle, analysisConfig.enable_entity_extraction && styles.toggleActive]}
                  onPress={() => setAnalysisConfig({ ...analysisConfig, enable_entity_extraction: !analysisConfig.enable_entity_extraction })}
                >
                  <View style={[styles.toggleHandle, analysisConfig.enable_entity_extraction && styles.toggleHandleActive]} />
                </TouchableOpacity>
              </View>

              <View style={styles.settingItem}>
                <Text style={styles.settingLabel}>Summarization</Text>
                <TouchableOpacity
                  style={[styles.toggle, analysisConfig.enable_summarization && styles.toggleActive]}
                  onPress={() => setAnalysisConfig({ ...analysisConfig, enable_summarization: !analysisConfig.enable_summarization })}
                >
                  <View style={[styles.toggleHandle, analysisConfig.enable_summarization && styles.toggleHandleActive]} />
                </TouchableOpacity>
              </View>

              <View style={styles.settingItem}>
                <Text style={styles.settingLabel}>Sentiment Analysis</Text>
                <TouchableOpacity
                  style={[styles.toggle, analysisConfig.enable_sentiment_analysis && styles.toggleActive]}
                  onPress={() => setAnalysisConfig({ ...analysisConfig, enable_sentiment_analysis: !analysisConfig.enable_sentiment_analysis })}
                >
                  <View style={[styles.toggleHandle, analysisConfig.enable_sentiment_analysis && styles.toggleHandleActive]} />
                </TouchableOpacity>
              </View>

              <View style={styles.settingItem}>
                <Text style={styles.settingLabel}>Key Phrases</Text>
                <TouchableOpacity
                  style={[styles.toggle, analysisConfig.enable_key_phrases && styles.toggleActive]}
                  onPress={() => setAnalysisConfig({ ...analysisConfig, enable_key_phrases: !analysisConfig.enable_key_phrases })}
                >
                  <View style={[styles.toggleHandle, analysisConfig.enable_key_phrases && styles.toggleHandleActive]} />
                </TouchableOpacity>
              </View>
            </ScrollView>

            <TouchableOpacity
              style={styles.saveSettingsButton}
              onPress={() => setShowSettings(false)}
            >
              <Text style={styles.saveSettingsButtonText}>Save Settings</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: theme.colors.text,
  },
  uploadCard: {
    margin: 16,
    padding: 40,
    backgroundColor: theme.colors.surface,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: theme.colors.border,
    borderStyle: 'dashed',
    alignItems: 'center',
    justifyContent: 'center',
  },
  uploadText: {
    fontSize: 16,
    color: theme.colors.text,
    marginTop: 16,
  },
  uploadSubtext: {
    fontSize: 14,
    color: theme.colors.textSecondary,
    marginTop: 8,
  },
  selectedFileCard: {
    flexDirection: 'row',
    alignItems: 'center',
    margin: 16,
    padding: 16,
    backgroundColor: theme.colors.surface,
    borderRadius: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  fileInfo: {
    flex: 1,
    marginLeft: 12,
  },
  fileName: {
    fontSize: 16,
    fontWeight: '500',
    color: theme.colors.text,
  },
  fileSize: {
    fontSize: 14,
    color: theme.colors.textSecondary,
    marginTop: 2,
  },
  templatesSection: {
    marginTop: 8,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.colors.text,
    marginLeft: 16,
    marginBottom: 12,
  },
  templateCard: {
    width: 150,
    padding: 16,
    marginLeft: 16,
    backgroundColor: theme.colors.surface,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  templateCardActive: {
    borderColor: theme.colors.primary,
    backgroundColor: theme.colors.primary + '10',
  },
  templateName: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.text,
  },
  templateNameActive: {
    color: theme.colors.primary,
  },
  templateDescription: {
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginTop: 4,
  },
  analyzeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: theme.colors.primary,
    marginHorizontal: 16,
    marginVertical: 8,
    paddingVertical: 16,
    borderRadius: 8,
  },
  analyzeButtonDisabled: {
    opacity: 0.7,
  },
  analyzeButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    margin: 16,
    padding: 12,
    backgroundColor: theme.colors.errorBackground,
    borderRadius: 8,
  },
  errorText: {
    flex: 1,
    color: theme.colors.error,
    fontSize: 14,
  },
  metadataCard: {
    margin: 16,
    padding: 16,
    backgroundColor: theme.colors.surface,
    borderRadius: 8,
  },
  metadataRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  metadataLabel: {
    fontSize: 14,
    color: theme.colors.textSecondary,
  },
  metadataValue: {
    fontSize: 14,
    fontWeight: '500',
    color: theme.colors.text,
    flex: 1,
    textAlign: 'right',
  },
  statsContainer: {
    flexDirection: 'row',
    marginHorizontal: 16,
    gap: 8,
  },
  statBox: {
    flex: 1,
    alignItems: 'center',
    padding: 16,
    backgroundColor: theme.colors.surface,
    borderRadius: 8,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: theme.colors.text,
  },
  statLabel: {
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginTop: 4,
  },
  tabs: {
    flexDirection: 'row',
    marginHorizontal: 16,
    marginTop: 16,
    backgroundColor: theme.colors.surface,
    borderRadius: 8,
    padding: 4,
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    borderRadius: 6,
  },
  activeTab: {
    backgroundColor: theme.colors.primary,
  },
  tabText: {
    fontSize: 14,
    fontWeight: '500',
    color: theme.colors.textSecondary,
  },
  activeTabText: {
    color: '#fff',
  },
  tabContent: {
    margin: 16,
    minHeight: 200,
  },
  summaryContainer: {
    backgroundColor: theme.colors.surface,
    padding: 16,
    borderRadius: 8,
  },
  summaryText: {
    fontSize: 14,
    lineHeight: 20,
    color: theme.colors.text,
  },
  topicsSection: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: theme.colors.border,
  },
  topicsSectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.text,
    marginBottom: 12,
  },
  topicItem: {
    marginBottom: 8,
  },
  topicHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.colors.background,
    padding: 12,
    borderRadius: 6,
  },
  topicName: {
    flex: 1,
    fontSize: 14,
    fontWeight: '500',
    color: theme.colors.text,
  },
  topicScore: {
    fontSize: 14,
    color: theme.colors.primary,
    marginRight: 8,
  },
  topicKeywords: {
    paddingLeft: 16,
    paddingTop: 8,
  },
  keyword: {
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginBottom: 4,
  },
  entitiesList: {
    paddingBottom: 16,
  },
  entityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    padding: 12,
    backgroundColor: theme.colors.surface,
    borderRadius: 8,
    marginBottom: 8,
  },
  entityTypeChip: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  entityTypeText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '500',
  },
  entityText: {
    flex: 1,
    fontSize: 14,
    color: theme.colors.text,
  },
  phrasesList: {
    paddingBottom: 16,
  },
  phrasesRow: {
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  keyPhraseChip: {
    width: (screenWidth - 48) / 2,
    padding: 12,
    backgroundColor: theme.colors.surface,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: theme.colors.primary,
  },
  keyPhraseText: {
    fontSize: 14,
    color: theme.colors.primary,
    textAlign: 'center',
  },
  sentimentContainer: {
    backgroundColor: theme.colors.surface,
    padding: 16,
    borderRadius: 8,
  },
  sentimentItem: {
    marginBottom: 16,
  },
  sentimentHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  sentimentLabel: {
    flex: 1,
    fontSize: 14,
    fontWeight: '500',
    color: theme.colors.text,
    marginLeft: 8,
  },
  sentimentScore: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.text,
  },
  sentimentBar: {
    height: 8,
    backgroundColor: theme.colors.border,
    borderRadius: 4,
    overflow: 'hidden',
  },
  sentimentProgress: {
    height: '100%',
    borderRadius: 4,
  },
  emptyText: {
    textAlign: 'center',
    color: theme.colors.textSecondary,
    fontSize: 14,
    padding: 32,
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 16,
    margin: 16,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: theme.colors.primary,
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: theme.colors.primary,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: theme.colors.background,
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
    color: theme.colors.text,
  },
  settingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  settingLabel: {
    fontSize: 16,
    color: theme.colors.text,
  },
  toggle: {
    width: 50,
    height: 30,
    borderRadius: 15,
    backgroundColor: theme.colors.border,
    padding: 2,
  },
  toggleActive: {
    backgroundColor: theme.colors.primary,
  },
  toggleHandle: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: '#fff',
  },
  toggleHandleActive: {
    transform: [{ translateX: 20 }],
  },
  saveSettingsButton: {
    backgroundColor: theme.colors.primary,
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 20,
  },
  saveSettingsButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default DocumentAnalysisMobile;