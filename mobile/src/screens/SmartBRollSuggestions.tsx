import React, { useState, useCallback, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  TextInput,
  Modal,
  FlatList,
  Dimensions,
  Share,
} from 'react-native';
import { 
  Lightbulb,
  Video,
  Target,
  Settings,
  ShoppingCart,
  BookOpen,
  RefreshCw,
  Search,
  Filter,
  Eye,
  CheckCircle,
  AlertCircle,
  Clock,
  DollarSign,
  TrendingUp,
  FileVideo,
  Image as ImageIcon,
  BarChart,
  Map,
  Users,
  Zap,
  Layers,
  X,
  ExternalLink,
  Star,
  ChevronRight,
  Play,
  Pause,
  Volume2
} from 'lucide-react-native';

const { width, height } = Dimensions.get('window');

interface TranscriptSegment {
  text: string;
  timestamp_start: number;
  timestamp_end: number;
  speaker?: string;
  emotion?: string;
  topics?: string[];
}

interface BRollSuggestion {
  suggestion_id: string;
  timestamp_start: number;
  timestamp_end: number;
  content_type: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  keywords: string[];
  description: string;
  rationale: string;
  search_query: string;
  duration: number;
  transition_type?: string;
  mood?: string;
  color_scheme?: string[];
  alternatives?: string[];
  confidence: number;
}

interface AnalysisSettings {
  enable_context_analysis: boolean;
  enable_emotion_detection: boolean;
  enable_topic_modeling: boolean;
  enable_visual_metaphors: boolean;
  enable_pacing_analysis: boolean;
  min_suggestion_duration: number;
  max_suggestion_duration: number;
  suggestion_density: 'low' | 'medium' | 'high';
  target_audience?: string;
  content_style?: string;
  budget_tier?: 'free' | 'budget' | 'premium';
}

interface BRollAnalysisResponse {
  analysis_id: string;
  suggestions: BRollSuggestion[];
  summary: {
    total_suggestions: number;
    coverage_percentage: number;
    priority_breakdown: Record<string, number>;
    content_type_distribution: Record<string, number>;
    estimated_enhancement_score: number;
    key_moments: Array<{
      timestamp: number;
      duration: number;
      type: string;
      description: string;
    }>;
  };
  timeline: Array<{
    start: number;
    end: number;
    type: string;
    priority: string;
    label: string;
  }>;
  estimated_cost?: {
    per_clip: number;
    total: number;
    currency: string;
  };
  processing_time: number;
  created_at: string;
}

const SmartBRollSuggestionsScreen: React.FC = () => {
  const [transcriptText, setTranscriptText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<BRollAnalysisResponse | null>(null);
  const [selectedSuggestions, setSelectedSuggestions] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('suggestions');
  const [showSettings, setShowSettings] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [previewSuggestion, setPreviewSuggestion] = useState<BRollSuggestion | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterPriority, setFilterPriority] = useState('all');
  
  const [settings, setSettings] = useState<AnalysisSettings>({
    enable_context_analysis: true,
    enable_emotion_detection: true,
    enable_topic_modeling: true,
    enable_visual_metaphors: true,
    enable_pacing_analysis: true,
    min_suggestion_duration: 2.0,
    max_suggestion_duration: 10.0,
    suggestion_density: 'medium',
    target_audience: 'general',
    content_style: 'educational',
    budget_tier: 'budget'
  });

  const analyzeTranscript = async () => {
    if (!transcriptText.trim()) {
      setError('Please provide transcript text');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      // Parse transcript into segments (simplified)
      const segments: TranscriptSegment[] = transcriptText
        .split('\n')
        .filter(line => line.trim())
        .map((line, index) => ({
          text: line.trim(),
          timestamp_start: index * 10,
          timestamp_end: (index + 1) * 10,
          speaker: `Speaker ${index % 2 + 1}`
        }));

      const requestBody = {
        transcript_segments: segments,
        video_duration: segments.length * 10,
        settings,
        metadata: {
          title: 'Mobile Video Analysis',
          created_at: new Date().toISOString()
        }
      };

      const response = await fetch('http://localhost:8000/api/v1/smart-broll/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const result = await response.json();
      setAnalysisResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze transcript');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const toggleSuggestion = (suggestionId: string) => {
    const newSelected = new Set(selectedSuggestions);
    if (newSelected.has(suggestionId)) {
      newSelected.delete(suggestionId);
    } else {
      newSelected.add(suggestionId);
    }
    setSelectedSuggestions(newSelected);
  };

  const generateShoppingList = async () => {
    if (!analysisResult) return;

    const selectedSuggestionObjs = analysisResult.suggestions.filter(s => 
      selectedSuggestions.has(s.suggestion_id)
    );

    try {
      const response = await fetch('http://localhost:8000/api/v1/smart-broll/generate-shopping-list', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          suggestions: selectedSuggestionObjs,
          budget: settings.budget_tier === 'free' ? 0 : 500,
          preferred_sources: ['pexels', 'unsplash']
        }),
      });

      const shoppingList = await response.json();
      Alert.alert('Shopping List Generated', `Generated list for ${selectedSuggestionObjs.length} items`);
    } catch (err) {
      Alert.alert('Error', 'Failed to generate shopping list');
    }
  };

  const shareResults = async () => {
    if (!analysisResult) return;

    const summary = `Smart B-Roll Analysis Results:
• ${analysisResult.suggestions.length} suggestions generated
• ${analysisResult.summary.coverage_percentage.toFixed(1)}% video coverage
• Enhancement score: ${analysisResult.summary.estimated_enhancement_score.toFixed(0)}%
${analysisResult.estimated_cost ? `• Estimated cost: $${analysisResult.estimated_cost.total}` : ''}`;

    try {
      await Share.share({
        message: summary,
        title: 'B-Roll Analysis Results'
      });
    } catch (error) {
      console.error('Error sharing:', error);
    }
  };

  const getPriorityColor = (priority: string) => {
    const colors = {
      critical: '#EF4444',
      high: '#F97316',
      medium: '#EAB308',
      low: '#6B7280'
    };
    return colors[priority as keyof typeof colors] || colors.low;
  };

  const getContentTypeIcon = (contentType: string) => {
    const iconProps = { size: 20, color: '#6B7280' };
    const iconMap: Record<string, React.ReactElement> = {
      stock_video: <Video {...iconProps} />,
      stock_image: <ImageIcon {...iconProps} />,
      animation: <Zap {...iconProps} />,
      infographic: <BarChart {...iconProps} />,
      map: <Map {...iconProps} />,
      chart: <BarChart {...iconProps} />,
      people: <Users {...iconProps} />,
      technology: <Layers {...iconProps} />
    };
    return iconMap[contentType] || <FileVideo {...iconProps} />;
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const filteredSuggestions = analysisResult?.suggestions.filter(suggestion => {
    const matchesSearch = searchQuery === '' || 
      suggestion.keywords.some(k => k.toLowerCase().includes(searchQuery.toLowerCase())) ||
      suggestion.description.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesPriority = filterPriority === 'all' || suggestion.priority === filterPriority;
    
    return matchesSearch && matchesPriority;
  }) || [];

  const renderSuggestion = ({ item: suggestion }: { item: BRollSuggestion }) => (
    <View style={[
      styles.suggestionCard,
      selectedSuggestions.has(suggestion.suggestion_id) && styles.suggestionCardSelected
    ]}>
      <View style={styles.suggestionHeader}>
        <TouchableOpacity
          style={styles.checkbox}
          onPress={() => toggleSuggestion(suggestion.suggestion_id)}
        >
          {selectedSuggestions.has(suggestion.suggestion_id) && (
            <CheckCircle size={20} color="#3B82F6" />
          )}
        </TouchableOpacity>
        
        <View style={styles.suggestionMeta}>
          {getContentTypeIcon(suggestion.content_type)}
          <View style={[styles.priorityBadge, { backgroundColor: getPriorityColor(suggestion.priority) }]}>
            <Text style={styles.priorityText}>{suggestion.priority}</Text>
          </View>
          <Text style={styles.timeText}>
            {formatTime(suggestion.timestamp_start)} - {formatTime(suggestion.timestamp_end)}
          </Text>
        </View>
      </View>
      
      <Text style={styles.suggestionTitle}>{suggestion.description}</Text>
      <Text style={styles.suggestionRationale}>{suggestion.rationale}</Text>
      
      <View style={styles.keywordsContainer}>
        {suggestion.keywords.slice(0, 3).map((keyword, idx) => (
          <View key={idx} style={styles.keywordChip}>
            <Text style={styles.keywordText}>{keyword}</Text>
          </View>
        ))}
      </View>
      
      <View style={styles.suggestionFooter}>
        <Text style={styles.confidenceText}>
          {(suggestion.confidence * 100).toFixed(0)}% confidence
        </Text>
        <TouchableOpacity
          style={styles.previewButton}
          onPress={() => {
            setPreviewSuggestion(suggestion);
            setShowPreview(true);
          }}
        >
          <Eye size={16} color="#3B82F6" />
          <Text style={styles.previewButtonText}>Preview</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

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
            <View style={styles.settingSection}>
              <Text style={styles.settingLabel}>Suggestion Density</Text>
              <View style={styles.densityButtons}>
                {['low', 'medium', 'high'].map(density => (
                  <TouchableOpacity
                    key={density}
                    style={[
                      styles.densityButton,
                      settings.suggestion_density === density && styles.densityButtonActive
                    ]}
                    onPress={() => setSettings({...settings, suggestion_density: density as any})}
                  >
                    <Text style={[
                      styles.densityButtonText,
                      settings.suggestion_density === density && styles.densityButtonTextActive
                    ]}>
                      {density.charAt(0).toUpperCase() + density.slice(1)}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <View style={styles.settingSection}>
              <Text style={styles.settingLabel}>Budget Tier</Text>
              <View style={styles.densityButtons}>
                {['free', 'budget', 'premium'].map(tier => (
                  <TouchableOpacity
                    key={tier}
                    style={[
                      styles.densityButton,
                      settings.budget_tier === tier && styles.densityButtonActive
                    ]}
                    onPress={() => setSettings({...settings, budget_tier: tier as any})}
                  >
                    <Text style={[
                      styles.densityButtonText,
                      settings.budget_tier === tier && styles.densityButtonTextActive
                    ]}>
                      {tier.charAt(0).toUpperCase() + tier.slice(1)}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            {Object.entries({
              enable_context_analysis: 'Context Analysis',
              enable_emotion_detection: 'Emotion Detection',
              enable_visual_metaphors: 'Visual Metaphors',
              enable_pacing_analysis: 'Pacing Analysis',
            }).map(([key, label]) => (
              <TouchableOpacity
                key={key}
                style={styles.switchSetting}
                onPress={() => setSettings(prev => ({ 
                  ...prev, 
                  [key]: !prev[key as keyof AnalysisSettings] 
                }))}
              >
                <Text style={styles.switchLabel}>{label}</Text>
                <View style={[
                  styles.switch,
                  settings[key as keyof AnalysisSettings] && styles.switchActive
                ]}>
                  <View style={[
                    styles.switchThumb,
                    settings[key as keyof AnalysisSettings] && styles.switchThumbActive
                  ]} />
                </View>
              </TouchableOpacity>
            ))}
          </ScrollView>
          
          <TouchableOpacity
            style={styles.modalButton}
            onPress={() => setShowSettings(false)}
          >
            <Text style={styles.modalButtonText}>Save Settings</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );

  const renderPreviewModal = () => (
    <Modal
      visible={showPreview}
      animationType="slide"
      transparent={true}
      onRequestClose={() => setShowPreview(false)}
    >
      <View style={styles.modalContainer}>
        <View style={styles.modalContent}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>B-Roll Preview</Text>
            <TouchableOpacity onPress={() => setShowPreview(false)}>
              <X size={24} color="#666" />
            </TouchableOpacity>
          </View>
          
          {previewSuggestion && (
            <ScrollView style={styles.modalBody}>
              <View style={styles.previewSection}>
                <Text style={styles.previewTitle}>{previewSuggestion.description}</Text>
                <Text style={styles.previewRationale}>{previewSuggestion.rationale}</Text>
              </View>
              
              <View style={styles.previewSection}>
                <Text style={styles.previewLabel}>Search Query:</Text>
                <Text style={styles.previewValue}>"{previewSuggestion.search_query}"</Text>
              </View>
              
              <View style={styles.previewSection}>
                <Text style={styles.previewLabel}>Keywords:</Text>
                <View style={styles.keywordsContainer}>
                  {previewSuggestion.keywords.map((keyword, idx) => (
                    <View key={idx} style={styles.keywordChip}>
                      <Text style={styles.keywordText}>{keyword}</Text>
                    </View>
                  ))}
                </View>
              </View>
              
              <View style={styles.previewSection}>
                <Text style={styles.previewLabel}>Details:</Text>
                <Text style={styles.previewValue}>
                  Duration: {previewSuggestion.duration.toFixed(1)}s{'\n'}
                  Confidence: {(previewSuggestion.confidence * 100).toFixed(0)}%{'\n'}
                  {previewSuggestion.mood && `Mood: ${previewSuggestion.mood}\n`}
                  {previewSuggestion.transition_type && `Transition: ${previewSuggestion.transition_type}`}
                </Text>
              </View>
            </ScrollView>
          )}
          
          <View style={styles.previewButtons}>
            <TouchableOpacity
              style={styles.previewButtonSecondary}
              onPress={() => setShowPreview(false)}
            >
              <Text style={styles.previewButtonSecondaryText}>Close</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.previewButtonPrimary}>
              <ExternalLink size={16} color="white" />
              <Text style={styles.previewButtonPrimaryText}>Search Stock</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            <Lightbulb size={24} color="#3B82F6" />
            <Text style={styles.headerTitle}>Smart B-Roll</Text>
          </View>
          <View style={styles.headerRight}>
            <TouchableOpacity
              style={styles.headerButton}
              onPress={() => setShowSettings(true)}
            >
              <Settings size={20} color="#666" />
            </TouchableOpacity>
            {analysisResult && (
              <TouchableOpacity
                style={styles.headerButton}
                onPress={generateShoppingList}
              >
                <ShoppingCart size={20} color="#666" />
              </TouchableOpacity>
            )}
          </View>
        </View>

        {/* Input Section */}
        <View style={styles.inputCard}>
          <View style={styles.inputHeader}>
            <BookOpen size={20} color="#666" />
            <Text style={styles.inputTitle}>Transcript Input</Text>
          </View>
          
          <TextInput
            style={styles.transcriptInput}
            placeholder="Paste your video transcript here..."
            value={transcriptText}
            onChangeText={setTranscriptText}
            multiline
            textAlignVertical="top"
          />
          
          <TouchableOpacity
            style={[styles.analyzeButton, !transcriptText.trim() && styles.analyzeButtonDisabled]}
            onPress={analyzeTranscript}
            disabled={!transcriptText.trim() || isAnalyzing}
          >
            {isAnalyzing ? (
              <>
                <ActivityIndicator color="white" size="small" />
                <Text style={styles.analyzeButtonText}>Analyzing...</Text>
              </>
            ) : (
              <>
                <Target size={20} color="white" />
                <Text style={styles.analyzeButtonText}>Generate Suggestions</Text>
              </>
            )}
          </TouchableOpacity>
          
          {error && (
            <View style={styles.errorContainer}>
              <AlertCircle size={20} color="#EF4444" />
              <Text style={styles.errorText}>{error}</Text>
            </View>
          )}
        </View>

        {/* Results */}
        {analysisResult && (
          <View style={styles.resultsSection}>
            {/* Summary Stats */}
            <View style={styles.statsGrid}>
              <View style={styles.statCard}>
                <Text style={styles.statValue}>{analysisResult.suggestions.length}</Text>
                <Text style={styles.statLabel}>Suggestions</Text>
              </View>
              <View style={styles.statCard}>
                <Text style={styles.statValue}>
                  {analysisResult.summary.coverage_percentage.toFixed(0)}%
                </Text>
                <Text style={styles.statLabel}>Coverage</Text>
              </View>
              <View style={styles.statCard}>
                <Text style={styles.statValue}>
                  {analysisResult.summary.estimated_enhancement_score.toFixed(0)}%
                </Text>
                <Text style={styles.statLabel}>Enhancement</Text>
              </View>
              {analysisResult.estimated_cost && (
                <View style={styles.statCard}>
                  <Text style={styles.statValue}>${analysisResult.estimated_cost.total}</Text>
                  <Text style={styles.statLabel}>Est. Cost</Text>
                </View>
              )}
            </View>

            {/* Search and Filter */}
            <View style={styles.filterSection}>
              <View style={styles.searchContainer}>
                <Search size={16} color="#666" />
                <TextInput
                  style={styles.searchInput}
                  placeholder="Search suggestions..."
                  value={searchQuery}
                  onChangeText={setSearchQuery}
                />
              </View>
              
              <View style={styles.priorityFilter}>
                {['all', 'critical', 'high', 'medium', 'low'].map(priority => (
                  <TouchableOpacity
                    key={priority}
                    style={[
                      styles.filterChip,
                      filterPriority === priority && styles.filterChipActive
                    ]}
                    onPress={() => setFilterPriority(priority)}
                  >
                    <Text style={[
                      styles.filterChipText,
                      filterPriority === priority && styles.filterChipTextActive
                    ]}>
                      {priority.charAt(0).toUpperCase() + priority.slice(1)}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            {/* Suggestions List */}
            <FlatList
              data={filteredSuggestions}
              renderItem={renderSuggestion}
              keyExtractor={item => item.suggestion_id}
              style={styles.suggestionsList}
              scrollEnabled={false}
            />

            {/* Action Buttons */}
            <View style={styles.actionButtons}>
              <TouchableOpacity
                style={styles.actionButtonSecondary}
                onPress={shareResults}
              >
                <Text style={styles.actionButtonSecondaryText}>Share Results</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.actionButtonPrimary,
                  selectedSuggestions.size === 0 && styles.actionButtonDisabled
                ]}
                onPress={generateShoppingList}
                disabled={selectedSuggestions.size === 0}
              >
                <ShoppingCart size={16} color="white" />
                <Text style={styles.actionButtonPrimaryText}>
                  Shopping List ({selectedSuggestions.size})
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {!analysisResult && !isAnalyzing && (
          <View style={styles.emptyState}>
            <Video size={48} color="#9CA3AF" />
            <Text style={styles.emptyStateText}>
              Enter your transcript to generate smart B-roll suggestions
            </Text>
          </View>
        )}
      </ScrollView>

      {renderSettingsModal()}
      {renderPreviewModal()}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 100,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginLeft: 10,
    color: '#111827',
  },
  headerRight: {
    flexDirection: 'row',
    gap: 12,
  },
  headerButton: {
    padding: 8,
    borderRadius: 8,
    backgroundColor: '#F3F4F6',
  },
  inputCard: {
    backgroundColor: 'white',
    margin: 16,
    borderRadius: 12,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  inputHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  inputTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
    color: '#111827',
  },
  transcriptInput: {
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 8,
    padding: 12,
    height: 120,
    fontSize: 14,
    color: '#374151',
    marginBottom: 16,
  },
  analyzeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#3B82F6',
    padding: 14,
    borderRadius: 8,
    gap: 8,
  },
  analyzeButtonDisabled: {
    backgroundColor: '#9CA3AF',
  },
  analyzeButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEE2E2',
    padding: 12,
    borderRadius: 8,
    marginTop: 12,
    gap: 8,
  },
  errorText: {
    flex: 1,
    color: '#EF4444',
    fontSize: 14,
  },
  resultsSection: {
    margin: 16,
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  statCard: {
    flex: 1,
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginHorizontal: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
  },
  statLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 4,
  },
  filterSection: {
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
    gap: 8,
  },
  searchInput: {
    flex: 1,
    fontSize: 14,
    color: '#374151',
  },
  priorityFilter: {
    flexDirection: 'row',
    gap: 8,
  },
  filterChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    backgroundColor: 'white',
  },
  filterChipActive: {
    backgroundColor: '#3B82F6',
    borderColor: '#3B82F6',
  },
  filterChipText: {
    fontSize: 12,
    color: '#6B7280',
  },
  filterChipTextActive: {
    color: 'white',
  },
  suggestionsList: {
    marginBottom: 20,
  },
  suggestionCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  suggestionCardSelected: {
    borderColor: '#3B82F6',
    backgroundColor: '#EFF6FF',
  },
  suggestionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 4,
    borderWidth: 2,
    borderColor: '#E5E7EB',
    marginRight: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  suggestionMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  priorityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 12,
  },
  priorityText: {
    color: 'white',
    fontSize: 10,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  timeText: {
    fontSize: 12,
    color: '#6B7280',
  },
  suggestionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  suggestionRationale: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 12,
  },
  keywordsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginBottom: 12,
  },
  keywordChip: {
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  keywordText: {
    fontSize: 12,
    color: '#4B5563',
  },
  suggestionFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  confidenceText: {
    fontSize: 12,
    color: '#6B7280',
  },
  previewButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    backgroundColor: '#EFF6FF',
    gap: 4,
  },
  previewButtonText: {
    fontSize: 12,
    color: '#3B82F6',
    fontWeight: '500',
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButtonSecondary: {
    flex: 1,
    padding: 14,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    backgroundColor: 'white',
    alignItems: 'center',
  },
  actionButtonSecondaryText: {
    fontSize: 14,
    color: '#6B7280',
    fontWeight: '500',
  },
  actionButtonPrimary: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#3B82F6',
    padding: 14,
    borderRadius: 8,
    gap: 6,
  },
  actionButtonDisabled: {
    backgroundColor: '#9CA3AF',
  },
  actionButtonPrimaryText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
    paddingHorizontal: 40,
  },
  emptyStateText: {
    marginTop: 16,
    fontSize: 16,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 24,
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
    maxHeight: height * 0.6,
  },
  settingSection: {
    marginBottom: 20,
  },
  settingLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
  },
  densityButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  densityButton: {
    flex: 1,
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    backgroundColor: 'white',
    alignItems: 'center',
  },
  densityButtonActive: {
    backgroundColor: '#3B82F6',
    borderColor: '#3B82F6',
  },
  densityButtonText: {
    fontSize: 14,
    color: '#6B7280',
  },
  densityButtonTextActive: {
    color: 'white',
  },
  switchSetting: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
  },
  switchLabel: {
    fontSize: 14,
    color: '#374151',
  },
  switch: {
    width: 44,
    height: 24,
    backgroundColor: '#E5E7EB',
    borderRadius: 12,
    padding: 2,
  },
  switchActive: {
    backgroundColor: '#3B82F6',
  },
  switchThumb: {
    width: 20,
    height: 20,
    backgroundColor: 'white',
    borderRadius: 10,
  },
  switchThumbActive: {
    transform: [{ translateX: 20 }],
  },
  modalButton: {
    backgroundColor: '#3B82F6',
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
  previewSection: {
    marginBottom: 20,
  },
  previewTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 8,
  },
  previewRationale: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
  },
  previewLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 4,
  },
  previewValue: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
  },
  previewButtons: {
    flexDirection: 'row',
    padding: 20,
    gap: 12,
  },
  previewButtonSecondary: {
    flex: 1,
    padding: 14,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    backgroundColor: 'white',
    alignItems: 'center',
  },
  previewButtonSecondaryText: {
    fontSize: 14,
    color: '#6B7280',
  },
  previewButtonPrimary: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#3B82F6',
    padding: 14,
    borderRadius: 8,
    gap: 6,
  },
  previewButtonPrimaryText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
});

export default SmartBRollSuggestionsScreen;