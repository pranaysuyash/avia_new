/**
 * Content Intelligence Screen - React Native
 * Advanced content analysis with NLP and ML insights
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
  Alert,
  Dimensions,
  Platform,
} from 'react-native';
import {
  Card,
  ProgressBar,
  Chip,
  List,
  Avatar,
  IconButton,
  Divider,
  Surface,
  Badge,
  SegmentedButtons,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { PieChart, BarChart } from 'react-native-chart-kit';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Share from 'react-native-share';

const { width: screenWidth } = Dimensions.get('window');
const chartConfig = {
  backgroundColor: '#ffffff',
  backgroundGradientFrom: '#ffffff',
  backgroundGradientTo: '#ffffff',
  decimalPlaces: 0,
  color: (opacity = 1) => `rgba(103, 126, 234, ${opacity})`,
  labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
  style: {
    borderRadius: 16,
  },
};

interface ContentAnalysis {
  contentId: string;
  title: string;
  category: string | null;
  tags: string[];
  keywords: Array<{ keyword: string; score: number }>;
  sentiment: {
    positive: number;
    negative: number;
    neutral: number;
  };
  qualityScore: number;
  readabilityScore: number;
  engagementPrediction: number;
  viralityScore: number;
  targetAudience: string[];
  summary: string | null;
}

interface ContentIntelligenceProps {
  apiEndpoint?: string;
  onAnalysisComplete?: (analysis: ContentAnalysis) => void;
}

const ContentIntelligence: React.FC<ContentIntelligenceProps> = ({
  apiEndpoint = '/api/intelligence/content/analyze',
  onAnalysisComplete,
}) => {
  const [content, setContent] = useState('');
  const [title, setTitle] = useState('');
  const [selectedTab, setSelectedTab] = useState('analyze');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<ContentAnalysis | null>(null);
  const [contentHistory, setContentHistory] = useState<ContentAnalysis[]>([]);

  const analyzeContent = useCallback(async () => {
    if (!content.trim()) {
      Alert.alert('Error', 'Please enter content to analyze');
      return;
    }

    setIsAnalyzing(true);

    try {
      // Mock analysis for demonstration
      const mockAnalysis: ContentAnalysis = {
        contentId: `content_${Date.now()}`,
        title: title || 'Untitled',
        category: 'technology',
        tags: ['AI', 'machine learning', 'innovation', 'future', 'technology'],
        keywords: [
          { keyword: 'artificial intelligence', score: 0.95 },
          { keyword: 'machine learning', score: 0.87 },
          { keyword: 'deep learning', score: 0.76 },
          { keyword: 'neural networks', score: 0.72 },
          { keyword: 'automation', score: 0.68 },
        ],
        sentiment: {
          positive: 0.72,
          negative: 0.08,
          neutral: 0.20,
        },
        qualityScore: 0.85,
        readabilityScore: 0.78,
        engagementPrediction: 0.82,
        viralityScore: 0.65,
        targetAudience: ['tech professionals', 'students', 'researchers'],
        summary: '• Discusses latest AI advancements\n• Explores practical applications\n• Highlights future possibilities',
      };

      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 2000));

      setAnalysis(mockAnalysis);
      setContentHistory(prev => [...prev, mockAnalysis]);
      
      // Save to AsyncStorage
      await AsyncStorage.setItem(
        `analysis_${mockAnalysis.contentId}`,
        JSON.stringify(mockAnalysis)
      );
      
      if (onAnalysisComplete) {
        onAnalysisComplete(mockAnalysis);
      }
    } catch (err) {
      Alert.alert('Error', 'Failed to analyze content. Please try again.');
      console.error('Analysis error:', err);
    } finally {
      setIsAnalyzing(false);
    }
  }, [content, title, onAnalysisComplete]);

  const exportAnalysis = useCallback(async () => {
    if (!analysis) return;

    try {
      const shareOptions = {
        title: 'Content Analysis Results',
        message: `Content Analysis for "${analysis.title}"
        
Quality Score: ${(analysis.qualityScore * 100).toFixed(0)}%
Readability: ${(analysis.readabilityScore * 100).toFixed(0)}%
Engagement Prediction: ${(analysis.engagementPrediction * 100).toFixed(0)}%
Viral Potential: ${(analysis.viralityScore * 100).toFixed(0)}%

Category: ${analysis.category}
Tags: ${analysis.tags.join(', ')}

${analysis.summary || ''}`,
      };

      await Share.open(shareOptions);
    } catch (error) {
      console.log('Share error:', error);
    }
  }, [analysis]);

  const renderMetricCard = (
    icon: string,
    label: string,
    value: number,
    color: string
  ) => (
    <Surface style={styles.metricCard} elevation={2}>
      <Icon name={icon} size={32} color={color} />
      <Text style={styles.metricValue}>{(value * 100).toFixed(0)}%</Text>
      <Text style={styles.metricLabel}>{label}</Text>
    </Surface>
  );

  const renderSentimentChart = () => {
    if (!analysis) return null;

    const data = [
      {
        name: 'Positive',
        population: analysis.sentiment.positive * 100,
        color: '#4caf50',
        legendFontColor: '#7F7F7F',
        legendFontSize: 12,
      },
      {
        name: 'Negative',
        population: analysis.sentiment.negative * 100,
        color: '#f44336',
        legendFontColor: '#7F7F7F',
        legendFontSize: 12,
      },
      {
        name: 'Neutral',
        population: analysis.sentiment.neutral * 100,
        color: '#9e9e9e',
        legendFontColor: '#7F7F7F',
        legendFontSize: 12,
      },
    ];

    return (
      <Card style={styles.chartCard}>
        <Card.Title title="Sentiment Analysis" left={(props) => <Avatar.Icon {...props} icon="emoticon" />} />
        <Card.Content>
          <PieChart
            data={data}
            width={screenWidth - 80}
            height={200}
            chartConfig={chartConfig}
            accessor="population"
            backgroundColor="transparent"
            paddingLeft="15"
            absolute
          />
        </Card.Content>
      </Card>
    );
  };

  const renderKeywordsChart = () => {
    if (!analysis) return null;

    const data = {
      labels: analysis.keywords.slice(0, 4).map(k => k.keyword.split(' ')[0]),
      datasets: [
        {
          data: analysis.keywords.slice(0, 4).map(k => k.score * 100),
        },
      ],
    };

    return (
      <Card style={styles.chartCard}>
        <Card.Title title="Top Keywords" left={(props) => <Avatar.Icon {...props} icon="tag-multiple" />} />
        <Card.Content>
          <BarChart
            data={data}
            width={screenWidth - 80}
            height={200}
            yAxisLabel=""
            yAxisSuffix="%"
            chartConfig={chartConfig}
            verticalLabelRotation={30}
          />
        </Card.Content>
      </Card>
    );
  };

  const renderAnalysisTab = () => (
    <ScrollView style={styles.tabContent}>
      <Card style={styles.inputCard}>
        <Card.Content>
          <TextInput
            style={styles.titleInput}
            placeholder="Title (optional)"
            value={title}
            onChangeText={setTitle}
            placeholderTextColor="#999"
          />
          <TextInput
            style={styles.contentInput}
            placeholder="Paste your content here for analysis..."
            value={content}
            onChangeText={setContent}
            multiline
            numberOfLines={8}
            textAlignVertical="top"
            placeholderTextColor="#999"
          />
          <TouchableOpacity
            style={[
              styles.analyzeButton,
              isAnalyzing && styles.analyzeButtonDisabled,
            ]}
            onPress={analyzeContent}
            disabled={isAnalyzing}
          >
            {isAnalyzing ? (
              <ActivityIndicator color="white" />
            ) : (
              <>
                <Icon name="brain" size={20} color="white" />
                <Text style={styles.analyzeButtonText}>Analyze Content</Text>
              </>
            )}
          </TouchableOpacity>
        </Card.Content>
      </Card>

      {analysis && (
        <>
          <View style={styles.metricsContainer}>
            {renderMetricCard('quality-high', 'Quality', analysis.qualityScore, '#667eea')}
            {renderMetricCard('book-open-variant', 'Readability', analysis.readabilityScore, '#764ba2')}
            {renderMetricCard('trending-up', 'Engagement', analysis.engagementPrediction, '#f093fb')}
            {renderMetricCard('fire', 'Viral Potential', analysis.viralityScore, '#f5576c')}
          </View>

          <Card style={styles.card}>
            <Card.Title title="Category & Tags" left={(props) => <Avatar.Icon {...props} icon="tag" />} />
            <Card.Content>
              {analysis.category && (
                <Chip style={styles.categoryChip} mode="flat">
                  {analysis.category.toUpperCase()}
                </Chip>
              )}
              <View style={styles.tagsContainer}>
                {analysis.tags.map((tag, index) => (
                  <Chip key={index} style={styles.tag} mode="outlined">
                    {tag}
                  </Chip>
                ))}
              </View>
            </Card.Content>
          </Card>

          <Card style={styles.card}>
            <Card.Title title="Target Audience" left={(props) => <Avatar.Icon {...props} icon="account-group" />} />
            <Card.Content>
              <List.Section>
                {analysis.targetAudience.map((audience, index) => (
                  <List.Item
                    key={index}
                    title={audience}
                    left={(props) => <List.Icon {...props} icon="account" />}
                  />
                ))}
              </List.Section>
            </Card.Content>
          </Card>

          {renderSentimentChart()}
          {renderKeywordsChart()}

          {analysis.summary && (
            <Card style={styles.card}>
              <Card.Title title="Summary" left={(props) => <Avatar.Icon {...props} icon="text-box-outline" />} />
              <Card.Content>
                <Text style={styles.summaryText}>{analysis.summary}</Text>
              </Card.Content>
            </Card>
          )}

          <TouchableOpacity style={styles.exportButton} onPress={exportAnalysis}>
            <Icon name="share-variant" size={20} color="white" />
            <Text style={styles.exportButtonText}>Share Results</Text>
          </TouchableOpacity>
        </>
      )}
    </ScrollView>
  );

  const renderHistoryTab = () => (
    <ScrollView style={styles.tabContent}>
      {contentHistory.length === 0 ? (
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.emptyText}>
              No analysis history yet. Start analyzing content to build your history.
            </Text>
          </Card.Content>
        </Card>
      ) : (
        contentHistory.map((item, index) => (
          <Card key={index} style={styles.historyCard}>
            <Card.Title
              title={item.title}
              subtitle={`Quality: ${(item.qualityScore * 100).toFixed(0)}% | Engagement: ${(item.engagementPrediction * 100).toFixed(0)}%`}
              left={(props) => <Avatar.Icon {...props} icon="file-document" />}
            />
          </Card>
        ))
      )}
    </ScrollView>
  );

  return (
    <View style={styles.container}>
      <Surface style={styles.header} elevation={4}>
        <View style={styles.headerContent}>
          <Icon name="brain" size={32} color="white" />
          <View style={styles.headerText}>
            <Text style={styles.headerTitle}>Content Intelligence</Text>
            <Text style={styles.headerSubtitle}>
              AI-powered content analysis and insights
            </Text>
          </View>
        </View>
      </Surface>

      <SegmentedButtons
        value={selectedTab}
        onValueChange={setSelectedTab}
        buttons={[
          { value: 'analyze', label: 'Analyze', icon: 'analytics' },
          { value: 'history', label: 'History', icon: 'history' },
        ]}
        style={styles.tabs}
      />

      {selectedTab === 'analyze' ? renderAnalysisTab() : renderHistoryTab()}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
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
  tabs: {
    margin: 16,
  },
  tabContent: {
    flex: 1,
    paddingHorizontal: 16,
  },
  inputCard: {
    marginBottom: 16,
  },
  titleInput: {
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
    fontSize: 16,
  },
  contentInput: {
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
    fontSize: 14,
    minHeight: 150,
  },
  analyzeButton: {
    backgroundColor: '#667eea',
    borderRadius: 8,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  analyzeButtonDisabled: {
    opacity: 0.6,
  },
  analyzeButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  metricsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  metricCard: {
    width: '48%',
    padding: 16,
    marginBottom: 12,
    borderRadius: 12,
    alignItems: 'center',
  },
  metricValue: {
    fontSize: 24,
    fontWeight: 'bold',
    marginVertical: 8,
  },
  metricLabel: {
    fontSize: 12,
    color: '#666',
  },
  card: {
    marginBottom: 16,
  },
  categoryChip: {
    alignSelf: 'flex-start',
    marginBottom: 8,
  },
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 8,
  },
  tag: {
    marginRight: 8,
    marginBottom: 8,
  },
  chartCard: {
    marginBottom: 16,
    paddingBottom: 16,
  },
  summaryText: {
    fontSize: 14,
    lineHeight: 20,
    color: '#333',
  },
  exportButton: {
    backgroundColor: '#764ba2',
    borderRadius: 8,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  exportButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  historyCard: {
    marginBottom: 12,
  },
  emptyText: {
    textAlign: 'center',
    color: '#666',
    fontSize: 14,
  },
});

export default ContentIntelligence;