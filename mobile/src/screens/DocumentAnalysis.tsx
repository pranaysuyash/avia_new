import React, { useState, useCallback, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  Platform,
  Modal,
  FlatList,
  Dimensions,
} from 'react-native';
import DocumentPicker from 'react-native-document-picker';
import RNFS from 'react-native-fs';
import { 
  FileText, 
  Upload, 
  Download, 
  Scan, 
  Eye, 
  Table,
  Type,
  Grid,
  FileSearch,
  Languages,
  Brain,
  Sparkles,
  AlertCircle,
  CheckCircle,
  Clock,
  TrendingUp,
  BarChart,
  PieChart,
  Hash,
  User,
  Calendar,
  MapPin,
  DollarSign,
  Mail,
  Phone,
  Link,
  ChevronRight,
  X
} from 'lucide-react-native';

const { width, height } = Dimensions.get('window');

interface DocumentMetadata {
  type: string;
  pages: number;
  language: string;
  confidence: number;
  processing_time: number;
}

interface ExtractedEntity {
  type: string;
  value: string;
  confidence: number;
  page?: number;
  bbox?: [number, number, number, number];
}

interface LayoutElement {
  type: string;
  content: string;
  confidence: number;
  bbox: [number, number, number, number];
  page: number;
}

interface TableData {
  headers: string[];
  rows: string[][];
  confidence: number;
  page: number;
}

interface AnalysisResult {
  document_id: string;
  metadata: DocumentMetadata;
  text_content: string;
  entities: ExtractedEntity[];
  layout_elements: LayoutElement[];
  tables: TableData[];
  summary?: string;
  key_phrases?: string[];
  sentiment?: {
    overall: string;
    score: number;
  };
}

interface AnalysisSettings {
  enable_ocr: boolean;
  enable_nlp: boolean;
  enable_entity_extraction: boolean;
  enable_summarization: boolean;
  enable_sentiment_analysis: boolean;
  enable_key_phrases: boolean;
  enable_language_detection: boolean;
  enable_table_extraction: boolean;
  enable_form_extraction: boolean;
  enable_layout_analysis: boolean;
  max_pages?: number;
  languages: string[];
}

const DocumentAnalysisScreen: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [showSettings, setShowSettings] = useState(false);
  
  const [settings, setSettings] = useState<AnalysisSettings>({
    enable_ocr: true,
    enable_nlp: true,
    enable_entity_extraction: true,
    enable_summarization: true,
    enable_sentiment_analysis: true,
    enable_key_phrases: true,
    enable_language_detection: true,
    enable_table_extraction: true,
    enable_form_extraction: true,
    enable_layout_analysis: true,
    languages: ['en'],
  });

  const pickDocument = async () => {
    try {
      const result = await DocumentPicker.pick({
        type: [
          DocumentPicker.types.pdf,
          DocumentPicker.types.images,
          DocumentPicker.types.doc,
          DocumentPicker.types.docx,
          DocumentPicker.types.plainText,
        ],
      });
      
      setSelectedFile(result[0]);
      setError(null);
      setAnalysisResult(null);
    } catch (err) {
      if (!DocumentPicker.isCancel(err)) {
        setError('Failed to pick document');
      }
    }
  };

  const analyzeDocument = async () => {
    if (!selectedFile) return;

    setIsProcessing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', {
        uri: selectedFile.uri,
        type: selectedFile.type,
        name: selectedFile.name,
      } as any);
      formData.append('settings', JSON.stringify(settings));

      const response = await fetch('http://localhost:8000/api/v1/document-analysis/analyze', {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (!response.ok) {
        throw new Error('Document analysis failed');
      }

      const result = await response.json();
      setAnalysisResult(result.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze document');
    } finally {
      setIsProcessing(false);
    }
  };

  const downloadResults = async () => {
    if (!analysisResult) return;

    try {
      const path = `${RNFS.DocumentDirectoryPath}/analysis_${analysisResult.document_id}.json`;
      await RNFS.writeFile(path, JSON.stringify(analysisResult, null, 2), 'utf8');
      Alert.alert('Success', 'Results saved to documents');
    } catch (err) {
      Alert.alert('Error', 'Failed to save results');
    }
  };

  const getEntityIcon = (type: string) => {
    const iconProps = { size: 16, color: '#666' };
    const iconMap: { [key: string]: React.ReactElement } = {
      'PERSON': <User {...iconProps} />,
      'DATE': <Calendar {...iconProps} />,
      'LOCATION': <MapPin {...iconProps} />,
      'MONEY': <DollarSign {...iconProps} />,
      'EMAIL': <Mail {...iconProps} />,
      'PHONE': <Phone {...iconProps} />,
      'URL': <Link {...iconProps} />,
      'NUMBER': <Hash {...iconProps} />,
    };
    return iconMap[type] || <FileText {...iconProps} />;
  };

  const getLayoutColor = (type: string) => {
    const colorMap: { [key: string]: string } = {
      'title': '#9333EA',
      'header': '#2563EB',
      'paragraph': '#6B7280',
      'table': '#10B981',
      'figure': '#F59E0B',
      'list': '#6366F1',
    };
    return colorMap[type.toLowerCase()] || '#6B7280';
  };

  const renderSettingsModal = () => (
    <Modal
      visible={showSettings}
      animationType="slide"
      transparent={true}
      onRequestClose={() => setShowSettings(false)}
    >
      <View style={styles.modalContainer}>
        <View style={styles.modalContent}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Analysis Settings</Text>
            <TouchableOpacity onPress={() => setShowSettings(false)}>
              <X size={24} color="#666" />
            </TouchableOpacity>
          </View>
          
          <ScrollView style={styles.modalBody}>
            {Object.entries({
              enable_ocr: 'OCR Text Extraction',
              enable_entity_extraction: 'Entity Recognition',
              enable_table_extraction: 'Table Extraction',
              enable_layout_analysis: 'Layout Analysis',
              enable_summarization: 'Summarization',
              enable_sentiment_analysis: 'Sentiment Analysis',
            }).map(([key, label]) => (
              <TouchableOpacity
                key={key}
                style={styles.settingRow}
                onPress={() => setSettings(prev => ({ 
                  ...prev, 
                  [key]: !prev[key as keyof AnalysisSettings] 
                }))}
              >
                <Text style={styles.settingLabel}>{label}</Text>
                <View style={[
                  styles.settingSwitch,
                  settings[key as keyof AnalysisSettings] && styles.settingSwitchActive
                ]}>
                  <View style={[
                    styles.settingSwitchThumb,
                    settings[key as keyof AnalysisSettings] && styles.settingSwitchThumbActive
                  ]} />
                </View>
              </TouchableOpacity>
            ))}
          </ScrollView>
          
          <TouchableOpacity
            style={styles.modalButton}
            onPress={() => setShowSettings(false)}
          >
            <Text style={styles.modalButtonText}>Done</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );

  const renderOverviewTab = () => {
    if (!analysisResult) return null;

    return (
      <View style={styles.tabContent}>
        <View style={styles.statsGrid}>
          <View style={styles.statCard}>
            <Text style={styles.statLabel}>Document Type</Text>
            <Text style={styles.statValue}>{analysisResult.metadata.type}</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statLabel}>Pages</Text>
            <Text style={styles.statValue}>{analysisResult.metadata.pages}</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statLabel}>Language</Text>
            <Text style={styles.statValue}>{analysisResult.metadata.language.toUpperCase()}</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statLabel}>Confidence</Text>
            <Text style={styles.statValue}>
              {(analysisResult.metadata.confidence * 100).toFixed(1)}%
            </Text>
          </View>
        </View>

        {analysisResult.summary && (
          <View style={styles.summaryCard}>
            <Text style={styles.summaryTitle}>Summary</Text>
            <Text style={styles.summaryText}>{analysisResult.summary}</Text>
          </View>
        )}

        {analysisResult.key_phrases && analysisResult.key_phrases.length > 0 && (
          <View style={styles.phrasesContainer}>
            <Text style={styles.phrasesTitle}>Key Phrases</Text>
            <View style={styles.phrasesGrid}>
              {analysisResult.key_phrases.map((phrase, idx) => (
                <View key={idx} style={styles.phraseChip}>
                  <Text style={styles.phraseText}>{phrase}</Text>
                </View>
              ))}
            </View>
          </View>
        )}
      </View>
    );
  };

  const renderEntitiesTab = () => {
    if (!analysisResult || !analysisResult.entities) return null;

    const groupedEntities = analysisResult.entities.reduce((acc, entity) => {
      if (!acc[entity.type]) acc[entity.type] = [];
      acc[entity.type].push(entity);
      return acc;
    }, {} as Record<string, ExtractedEntity[]>);

    return (
      <ScrollView style={styles.tabContent}>
        {Object.entries(groupedEntities).map(([type, entities]) => (
          <View key={type} style={styles.entityGroup}>
            <View style={styles.entityHeader}>
              {getEntityIcon(type)}
              <Text style={styles.entityType}>{type}</Text>
              <View style={styles.entityCount}>
                <Text style={styles.entityCountText}>{entities.length}</Text>
              </View>
            </View>
            {entities.slice(0, 5).map((entity, idx) => (
              <View key={idx} style={styles.entityItem}>
                <Text style={styles.entityValue}>{entity.value}</Text>
                <Text style={styles.entityConfidence}>
                  {(entity.confidence * 100).toFixed(0)}%
                </Text>
              </View>
            ))}
            {entities.length > 5 && (
              <Text style={styles.moreText}>+{entities.length - 5} more</Text>
            )}
          </View>
        ))}
      </ScrollView>
    );
  };

  const renderTablesTab = () => {
    if (!analysisResult || !analysisResult.tables || analysisResult.tables.length === 0) {
      return (
        <View style={styles.emptyState}>
          <Table size={48} color="#9CA3AF" />
          <Text style={styles.emptyText}>No tables detected</Text>
        </View>
      );
    }

    return (
      <ScrollView style={styles.tabContent}>
        {analysisResult.tables.map((table, idx) => (
          <View key={idx} style={styles.tableCard}>
            <View style={styles.tableHeader}>
              <Text style={styles.tableTitle}>Table {idx + 1}</Text>
              <Text style={styles.tablePage}>Page {table.page}</Text>
            </View>
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              <View>
                <View style={styles.tableRow}>
                  {table.headers.map((header, i) => (
                    <Text key={i} style={styles.tableHeaderCell}>{header}</Text>
                  ))}
                </View>
                {table.rows.slice(0, 5).map((row, i) => (
                  <View key={i} style={styles.tableRow}>
                    {row.map((cell, j) => (
                      <Text key={j} style={styles.tableCell}>{cell}</Text>
                    ))}
                  </View>
                ))}
              </View>
            </ScrollView>
            {table.rows.length > 5 && (
              <Text style={styles.moreText}>Showing 5 of {table.rows.length} rows</Text>
            )}
          </View>
        ))}
      </ScrollView>
    );
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return renderOverviewTab();
      case 'entities':
        return renderEntitiesTab();
      case 'tables':
        return renderTablesTab();
      default:
        return null;
    }
  };

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <FileSearch size={24} color="#2563EB" />
          <Text style={styles.headerTitle}>Document Analysis</Text>
        </View>

        {/* Upload Section */}
        <View style={styles.uploadSection}>
          <TouchableOpacity
            style={styles.uploadButton}
            onPress={pickDocument}
            disabled={isProcessing}
          >
            <Upload size={32} color="#9CA3AF" />
            <Text style={styles.uploadText}>
              {selectedFile ? selectedFile.name : 'Tap to select document'}
            </Text>
            {selectedFile && (
              <Text style={styles.uploadSubtext}>
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </Text>
            )}
          </TouchableOpacity>

          <View style={styles.actionButtons}>
            <TouchableOpacity
              style={styles.settingsButton}
              onPress={() => setShowSettings(true)}
            >
              <Brain size={20} color="#666" />
              <Text style={styles.settingsButtonText}>Settings</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.analyzeButton, !selectedFile && styles.analyzeButtonDisabled]}
              onPress={analyzeDocument}
              disabled={!selectedFile || isProcessing}
            >
              {isProcessing ? (
                <ActivityIndicator color="white" />
              ) : (
                <>
                  <Scan size={20} color="white" />
                  <Text style={styles.analyzeButtonText}>Analyze</Text>
                </>
              )}
            </TouchableOpacity>
          </View>
        </View>

        {/* Error Display */}
        {error && (
          <View style={styles.errorContainer}>
            <AlertCircle size={20} color="#EF4444" />
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {/* Results Section */}
        {analysisResult && (
          <View style={styles.resultsSection}>
            <View style={styles.resultsHeader}>
              <View style={styles.successBadge}>
                <CheckCircle size={16} color="#10B981" />
                <Text style={styles.successText}>Complete</Text>
              </View>
              <TouchableOpacity onPress={downloadResults}>
                <Download size={20} color="#2563EB" />
              </TouchableOpacity>
            </View>

            {/* Tabs */}
            <View style={styles.tabs}>
              {['overview', 'entities', 'tables'].map((tab) => (
                <TouchableOpacity
                  key={tab}
                  style={[styles.tab, activeTab === tab && styles.activeTab]}
                  onPress={() => setActiveTab(tab)}
                >
                  <Text style={[styles.tabText, activeTab === tab && styles.activeTabText]}>
                    {tab.charAt(0).toUpperCase() + tab.slice(1)}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            {/* Tab Content */}
            {renderContent()}
          </View>
        )}
      </ScrollView>

      {renderSettingsModal()}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  scrollContent: {
    paddingBottom: 100,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginLeft: 10,
    color: '#111827',
  },
  uploadSection: {
    padding: 20,
    backgroundColor: 'white',
    margin: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  uploadButton: {
    borderWidth: 2,
    borderColor: '#E5E7EB',
    borderStyle: 'dashed',
    borderRadius: 8,
    padding: 32,
    alignItems: 'center',
    marginBottom: 16,
  },
  uploadText: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 8,
    textAlign: 'center',
  },
  uploadSubtext: {
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 4,
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  settingsButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    gap: 8,
  },
  settingsButtonText: {
    fontSize: 14,
    color: '#666',
  },
  analyzeButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    borderRadius: 8,
    backgroundColor: '#2563EB',
    gap: 8,
  },
  analyzeButtonDisabled: {
    backgroundColor: '#9CA3AF',
  },
  analyzeButtonText: {
    fontSize: 14,
    color: 'white',
    fontWeight: '600',
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEE2E2',
    padding: 12,
    margin: 16,
    borderRadius: 8,
    gap: 8,
  },
  errorText: {
    flex: 1,
    color: '#EF4444',
    fontSize: 14,
  },
  resultsSection: {
    margin: 16,
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  resultsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  successBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#D1FAE5',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    gap: 6,
  },
  successText: {
    color: '#10B981',
    fontSize: 12,
    fontWeight: '600',
  },
  tabs: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
    marginBottom: 16,
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#2563EB',
  },
  tabText: {
    fontSize: 14,
    color: '#6B7280',
  },
  activeTabText: {
    color: '#2563EB',
    fontWeight: '600',
  },
  tabContent: {
    minHeight: 200,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 16,
  },
  statCard: {
    flex: 1,
    minWidth: '45%',
    padding: 12,
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
  },
  statLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  statValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  summaryCard: {
    backgroundColor: '#EFF6FF',
    padding: 16,
    borderRadius: 8,
    marginBottom: 16,
  },
  summaryTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1E40AF',
    marginBottom: 8,
  },
  summaryText: {
    fontSize: 14,
    color: '#3B82F6',
    lineHeight: 20,
  },
  phrasesContainer: {
    marginTop: 16,
  },
  phrasesTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 8,
  },
  phrasesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  phraseChip: {
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  phraseText: {
    fontSize: 12,
    color: '#4B5563',
  },
  entityGroup: {
    marginBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
    paddingBottom: 16,
  },
  entityHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 8,
  },
  entityType: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
    flex: 1,
  },
  entityCount: {
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  entityCountText: {
    fontSize: 12,
    color: '#6B7280',
  },
  entityItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  entityValue: {
    flex: 1,
    fontSize: 14,
    color: '#374151',
  },
  entityConfidence: {
    fontSize: 12,
    color: '#9CA3AF',
  },
  moreText: {
    fontSize: 12,
    color: '#6B7280',
    fontStyle: 'italic',
    marginTop: 8,
    paddingHorizontal: 12,
  },
  tableCard: {
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 8,
    padding: 16,
  },
  tableHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  tableTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  tablePage: {
    fontSize: 12,
    color: '#6B7280',
  },
  tableRow: {
    flexDirection: 'row',
  },
  tableHeaderCell: {
    width: 120,
    padding: 8,
    backgroundColor: '#F3F4F6',
    fontSize: 12,
    fontWeight: '600',
    color: '#374151',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  tableCell: {
    width: 120,
    padding: 8,
    fontSize: 12,
    color: '#6B7280',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 48,
  },
  emptyText: {
    marginTop: 12,
    fontSize: 14,
    color: '#9CA3AF',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: 'white',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: height * 0.8,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  modalBody: {
    padding: 20,
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
  },
  settingLabel: {
    fontSize: 14,
    color: '#374151',
  },
  settingSwitch: {
    width: 44,
    height: 24,
    backgroundColor: '#E5E7EB',
    borderRadius: 12,
    padding: 2,
  },
  settingSwitchActive: {
    backgroundColor: '#3B82F6',
  },
  settingSwitchThumb: {
    width: 20,
    height: 20,
    backgroundColor: 'white',
    borderRadius: 10,
  },
  settingSwitchThumbActive: {
    transform: [{ translateX: 20 }],
  },
  modalButton: {
    backgroundColor: '#2563EB',
    margin: 20,
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  modalButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default DocumentAnalysisScreen;