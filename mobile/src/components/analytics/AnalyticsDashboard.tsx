import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  ActivityIndicator,
  Alert,
  Modal,
  TextInput,
  Switch,
  FlatList,
  RefreshControl
} from 'react-native';
import {
  LineChart,
  BarChart,
  PieChart,
  ProgressChart
} from 'react-native-chart-kit';
import { Picker } from '@react-native-picker/picker';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { SafeAreaView } from 'react-native-safe-area-context';

const { width: screenWidth } = Dimensions.get('window');

interface TrendData {
  time_bucket: string;
  keywords?: Array<{
    keyword: string;
    score: number;
    frequency: number;
    growth_rate?: number;
  }>;
  entities?: Array<{
    entity: string;
    count: number;
  }>;
  sentiment?: {
    average_sentiment: number;
    sentiment_distribution: {
      positive: number;
      neutral: number;
      negative: number;
    };
  };
}

interface TopicModel {
  topics: Array<{
    topic_id: string;
    keywords: string[];
    weight: number;
    description: string;
  }>;
  coherence_score: number;
  num_topics: number;
}

interface ComparisonResult {
  source_a: string;
  source_b: string;
  similarities: {
    keyword_similarity: number;
    length_similarity: number;
    entity_similarity: number;
    overall_similarity: number;
  };
  common_themes: string[];
  unique_themes: {
    source_a_unique: string[];
    source_b_unique: string[];
  };
}

const chartConfig = {
  backgroundColor: '#ffffff',
  backgroundGradientFrom: '#ffffff',
  backgroundGradientTo: '#ffffff',
  decimalPlaces: 2,
  color: (opacity = 1) => `rgba(0, 122, 255, ${opacity})`,
  labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
  style: {
    borderRadius: 16,
  },
  propsForDots: {
    r: '6',
    strokeWidth: '2',
    stroke: '#007AFF',
  },
};

export const AnalyticsDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  
  // Trend Analysis State
  const [trendData, setTrendData] = useState<TrendData[]>([]);
  const [trendPeriod, setTrendPeriod] = useState('30d');
  const [analysisType, setAnalysisType] = useState('keywords');
  const [showTrendFilters, setShowTrendFilters] = useState(false);
  
  // Topic Modeling State
  const [topicModel, setTopicModel] = useState<TopicModel | null>(null);
  const [numTopics, setNumTopics] = useState(5);
  const [topicMethod, setTopicMethod] = useState('keyword_clustering');
  
  // Comparative Analysis State
  const [comparisonResult, setComparisonResult] = useState<ComparisonResult | null>(null);
  const [sourceA, setSourceA] = useState('');
  const [sourceB, setSourceB] = useState('');
  const [showComparisonModal, setShowComparisonModal] = useState(false);

  const tabs = [
    { id: 0, title: 'Trends', icon: 'trending-up' },
    { id: 1, title: 'Topics', icon: 'topic' },
    { id: 2, title: 'Compare', icon: 'compare' },
    { id: 3, title: 'Search', icon: 'search' }
  ];

  const analyzeTrends = async () => {
    setLoading(true);
    
    try {
      const response = await fetch('/api/analytics/trends', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          time_period: trendPeriod,
          analysis_type: analysisType,
          filters: {}
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to analyze trends');
      }

      const result = await response.json();
      setTrendData(result.trends || []);
    } catch (error) {
      Alert.alert('Error', 'Failed to analyze trends');
    } finally {
      setLoading(false);
    }
  };

  const extractTopics = async () => {
    setLoading(true);
    
    try {
      const response = await fetch('/api/analytics/topics', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          num_topics: numTopics,
          method: topicMethod
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to extract topics');
      }

      const result = await response.json();
      setTopicModel(result);
    } catch (error) {
      Alert.alert('Error', 'Failed to extract topics');
    } finally {
      setLoading(false);
    }
  };

  const compareSources = async () => {
    if (!sourceA || !sourceB) {
      Alert.alert('Error', 'Please specify both sources for comparison');
      return;
    }

    setLoading(true);
    
    try {
      const response = await fetch('/api/analytics/compare', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          source_a: sourceA,
          source_b: sourceB,
          comparison_type: 'comprehensive'
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to compare sources');
      }

      const result = await response.json();
      setComparisonResult(result);
      setShowComparisonModal(false);
    } catch (error) {
      Alert.alert('Error', 'Failed to compare sources');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    
    switch (activeTab) {
      case 0:
        await analyzeTrends();
        break;
      case 1:
        await extractTopics();
        break;
      case 2:
        // Refresh comparison if we have sources
        if (sourceA && sourceB) {
          await compareSources();
        }
        break;
    }
    
    setRefreshing(false);
  };

  const renderTabBar = () => (
    <View style={styles.tabBar}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        {tabs.map((tab) => (
          <TouchableOpacity
            key={tab.id}
            style={[
              styles.tab,
              activeTab === tab.id && styles.activeTab
            ]}
            onPress={() => setActiveTab(tab.id)}
          >
            <Icon
              name={tab.icon}
              size={20}
              color={activeTab === tab.id ? '#007AFF' : '#666'}
            />
            <Text style={[
              styles.tabText,
              activeTab === tab.id && styles.activeTabText
            ]}>
              {tab.title}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );

  const renderTrendAnalysis = () => {
    const prepareChartData = () => {
      if (!trendData.length) return null;

      if (analysisType === 'keywords') {
        const labels = trendData.map(d => d.time_bucket.split('-').slice(1).join('/'));
        const datasets = [];
        
        // Get top 3 keywords across all periods
        const allKeywords = new Set<string>();
        trendData.forEach(trend => {
          trend.keywords?.slice(0, 3).forEach(kw => allKeywords.add(kw.keyword));
        });

        Array.from(allKeywords).slice(0, 3).forEach((keyword, index) => {
          const data = trendData.map(trend => {
            const kw = trend.keywords?.find(k => k.keyword === keyword);
            return kw ? kw.score : 0;
          });
          
          datasets.push({
            data,
            color: (opacity = 1) => `rgba(${index * 80 + 50}, ${100 + index * 50}, 255, ${opacity})`,
            strokeWidth: 2
          });
        });

        return { labels, datasets };
      }

      if (analysisType === 'sentiment') {
        const labels = trendData.map(d => d.time_bucket.split('-').slice(1).join('/'));
        const data = trendData.map(d => d.sentiment?.average_sentiment || 0);
        
        return {
          labels,
          datasets: [{
            data,
            color: (opacity = 1) => `rgba(0, 122, 255, ${opacity})`,
            strokeWidth: 3
          }]
        };
      }

      return null;
    };

    const chartData = prepareChartData();

    return (
      <ScrollView
        style={styles.tabContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Trend Analysis Configuration</Text>
          
          <View style={styles.configRow}>
            <Text style={styles.label}>Time Period:</Text>
            <View style={styles.pickerContainer}>
              <Picker
                selectedValue={trendPeriod}
                onValueChange={setTrendPeriod}
                style={styles.picker}
              >
                <Picker.Item label="Last 7 days" value="7d" />
                <Picker.Item label="Last 30 days" value="30d" />
                <Picker.Item label="Last 90 days" value="90d" />
                <Picker.Item label="Last year" value="1y" />
              </Picker>
            </View>
          </View>

          <View style={styles.configRow}>
            <Text style={styles.label}>Analysis Type:</Text>
            <View style={styles.pickerContainer}>
              <Picker
                selectedValue={analysisType}
                onValueChange={setAnalysisType}
                style={styles.picker}
              >
                <Picker.Item label="Keywords" value="keywords" />
                <Picker.Item label="Topics" value="topics" />
                <Picker.Item label="Entities" value="entities" />
                <Picker.Item label="Sentiment" value="sentiment" />
              </Picker>
            </View>
          </View>

          <TouchableOpacity
            style={styles.analyzeButton}
            onPress={analyzeTrends}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <>
                <Icon name="analytics" size={20} color="#fff" />
                <Text style={styles.buttonText}>Analyze Trends</Text>
              </>
            )}
          </TouchableOpacity>
        </View>

        {chartData && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>
              {analysisType.charAt(0).toUpperCase() + analysisType.slice(1)} Trends
            </Text>
            
            <LineChart
              data={chartData}
              width={screenWidth - 60}
              height={220}
              chartConfig={chartConfig}
              bezier
              style={styles.chart}
            />

            <View style={styles.statsContainer}>
              <View style={styles.stat}>
                <Text style={styles.statValue}>{trendData.length}</Text>
                <Text style={styles.statLabel}>Time Periods</Text>
              </View>
              <View style={styles.stat}>
                <Text style={styles.statValue}>
                  {analysisType === 'keywords' 
                    ? trendData.reduce((sum, t) => sum + (t.keywords?.length || 0), 0)
                    : trendData.reduce((sum, t) => sum + (t.entities?.length || 0), 0)
                  }
                </Text>
                <Text style={styles.statLabel}>
                  {analysisType === 'keywords' ? 'Keywords' : 'Items'}
                </Text>
              </View>
            </View>
          </View>
        )}

        {analysisType === 'keywords' && trendData.length > 0 && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Top Keywords</Text>
            <FlatList
              data={trendData[trendData.length - 1]?.keywords?.slice(0, 10) || []}
              keyExtractor={(item, index) => index.toString()}
              renderItem={({ item }) => (
                <View style={styles.keywordItem}>
                  <Text style={styles.keywordText}>{item.keyword}</Text>
                  <View style={styles.keywordStats}>
                    <Text style={styles.keywordScore}>
                      Score: {item.score.toFixed(2)}
                    </Text>
                    <Text style={styles.keywordFreq}>
                      Freq: {item.frequency}
                    </Text>
                    {item.growth_rate !== undefined && (
                      <Text style={[
                        styles.keywordGrowth,
                        { color: item.growth_rate > 0 ? '#4CAF50' : '#F44336' }
                      ]}>
                        {item.growth_rate > 0 ? '+' : ''}{item.growth_rate.toFixed(1)}%
                      </Text>
                    )}
                  </View>
                </View>
              )}
              scrollEnabled={false}
            />
          </View>
        )}
      </ScrollView>
    );
  };

  const renderTopicModeling = () => (
    <ScrollView
      style={styles.tabContent}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Topic Modeling Configuration</Text>
        
        <View style={styles.configRow}>
          <Text style={styles.label}>Number of Topics:</Text>
          <View style={styles.pickerContainer}>
            <Picker
              selectedValue={numTopics}
              onValueChange={setNumTopics}
              style={styles.picker}
            >
              {[2, 3, 4, 5, 6, 7, 8, 9, 10].map(num => (
                <Picker.Item key={num} label={num.toString()} value={num} />
              ))}
            </Picker>
          </View>
        </View>

        <View style={styles.configRow}>
          <Text style={styles.label}>Method:</Text>
          <View style={styles.pickerContainer}>
            <Picker
              selectedValue={topicMethod}
              onValueChange={setTopicMethod}
              style={styles.picker}
            >
              <Picker.Item label="Keyword Clustering" value="keyword_clustering" />
              <Picker.Item label="Semantic Clustering" value="semantic_clustering" />
            </Picker>
          </View>
        </View>

        <TouchableOpacity
          style={styles.analyzeButton}
          onPress={extractTopics}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <>
              <Icon name="psychology" size={20} color="#fff" />
              <Text style={styles.buttonText}>Extract Topics</Text>
            </>
          )}
        </TouchableOpacity>
      </View>

      {topicModel && (
        <>
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Topic Model Results</Text>
            
            <View style={styles.statsContainer}>
              <View style={styles.stat}>
                <Text style={styles.statValue}>{topicModel.num_topics}</Text>
                <Text style={styles.statLabel}>Topics</Text>
              </View>
              <View style={styles.stat}>
                <Text style={styles.statValue}>
                  {topicModel.coherence_score.toFixed(3)}
                </Text>
                <Text style={styles.statLabel}>Coherence</Text>
              </View>
            </View>

            {topicModel.topics.length > 0 && (
              <BarChart
                data={{
                  labels: topicModel.topics.map(t => t.topic_id.replace('topic_', 'T')),
                  datasets: [{
                    data: topicModel.topics.map(t => t.weight)
                  }]
                }}
                width={screenWidth - 60}
                height={220}
                chartConfig={chartConfig}
                style={styles.chart}
              />
            )}
          </View>

          <View style={styles.card}>
            <Text style={styles.cardTitle}>Topic Details</Text>
            <FlatList
              data={topicModel.topics}
              keyExtractor={(item) => item.topic_id}
              renderItem={({ item, index }) => (
                <View style={styles.topicItem}>
                  <Text style={styles.topicTitle}>
                    Topic {index + 1}: {item.description}
                  </Text>
                  <Text style={styles.topicWeight}>
                    Weight: {item.weight.toFixed(3)}
                  </Text>
                  <View style={styles.keywordsContainer}>
                    {item.keywords.slice(0, 5).map((keyword, idx) => (
                      <View key={idx} style={styles.keywordChip}>
                        <Text style={styles.keywordChipText}>{keyword}</Text>
                      </View>
                    ))}
                  </View>
                </View>
              )}
              scrollEnabled={false}
            />
          </View>
        </>
      )}
    </ScrollView>
  );

  const renderComparativeAnalysis = () => (
    <ScrollView
      style={styles.tabContent}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Source Comparison</Text>
        
        <TouchableOpacity
          style={styles.configButton}
          onPress={() => setShowComparisonModal(true)}
        >
          <Icon name="settings" size={20} color="#007AFF" />
          <Text style={styles.configButtonText}>Configure Sources</Text>
        </TouchableOpacity>

        {sourceA && sourceB && (
          <View style={styles.sourceInfo}>
            <Text style={styles.sourceText}>Source A: {sourceA}</Text>
            <Text style={styles.sourceText}>Source B: {sourceB}</Text>
            
            <TouchableOpacity
              style={styles.analyzeButton}
              onPress={compareSources}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <>
                  <Icon name="compare" size={20} color="#fff" />
                  <Text style={styles.buttonText}>Compare Sources</Text>
                </>
              )}
            </TouchableOpacity>
          </View>
        )}
      </View>

      {comparisonResult && (
        <>
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Similarity Metrics</Text>
            
            {Object.entries(comparisonResult.similarities).map(([metric, value]) => (
              <View key={metric} style={styles.similarityItem}>
                <Text style={styles.similarityLabel}>
                  {metric.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </Text>
                <View style={styles.progressBar}>
                  <View
                    style={[
                      styles.progressFill,
                      {
                        width: `${value * 100}%`,
                        backgroundColor: value > 0.7 ? '#4CAF50' : value > 0.4 ? '#FF9800' : '#F44336'
                      }
                    ]}
                  />
                </View>
                <Text style={styles.similarityValue}>
                  {(value * 100).toFixed(1)}%
                </Text>
              </View>
            ))}
          </View>

          {comparisonResult.common_themes.length > 0 && (
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Common Themes</Text>
              <View style={styles.themesContainer}>
                {comparisonResult.common_themes.map((theme, index) => (
                  <View key={index} style={[styles.themeChip, styles.commonTheme]}>
                    <Text style={styles.themeChipText}>{theme}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}

          <View style={styles.card}>
            <Text style={styles.cardTitle}>Unique Themes</Text>
            
            <Text style={styles.uniqueTitle}>Unique to {comparisonResult.source_a}:</Text>
            <View style={styles.themesContainer}>
              {comparisonResult.unique_themes.source_a_unique.map((theme, index) => (
                <View key={index} style={[styles.themeChip, styles.uniqueThemeA]}>
                  <Text style={styles.themeChipText}>{theme}</Text>
                </View>
              ))}
            </View>

            <Text style={styles.uniqueTitle}>Unique to {comparisonResult.source_b}:</Text>
            <View style={styles.themesContainer}>
              {comparisonResult.unique_themes.source_b_unique.map((theme, index) => (
                <View key={index} style={[styles.themeChip, styles.uniqueThemeB]}>
                  <Text style={styles.themeChipText}>{theme}</Text>
                </View>
              ))}
            </View>
          </View>
        </>
      )}

      {/* Comparison Configuration Modal */}
      <Modal
        visible={showComparisonModal}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setShowComparisonModal(false)}>
              <Icon name="close" size={24} color="#007AFF" />
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Configure Comparison</Text>
            <TouchableOpacity onPress={() => setShowComparisonModal(false)}>
              <Text style={styles.doneButton}>Done</Text>
            </TouchableOpacity>
          </View>
          
          <View style={styles.modalContent}>
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Source A:</Text>
              <TextInput
                style={styles.textInput}
                value={sourceA}
                onChangeText={setSourceA}
                placeholder="Enter transcript ID or collection name"
              />
            </View>
            
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Source B:</Text>
              <TextInput
                style={styles.textInput}
                value={sourceB}
                onChangeText={setSourceB}
                placeholder="Enter transcript ID or collection name"
              />
            </View>
          </View>
        </SafeAreaView>
      </Modal>
    </ScrollView>
  );

  const renderSearchAnalytics = () => (
    <ScrollView style={styles.tabContent}>
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Search Analytics</Text>
        <Text style={styles.comingSoon}>
          🚧 Search analytics coming soon!
        </Text>
        <Text style={styles.featureList}>
          This will show:{'\n'}
          • Popular search terms{'\n'}
          • Search success rates{'\n'}
          • Query performance metrics{'\n'}
          • User search behavior patterns{'\n'}
          • Result click-through rates
        </Text>
      </View>

      {/* Sample Charts */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Popular Search Terms (Sample)</Text>
        <BarChart
          data={{
            labels: ['meeting', 'project', 'discussion', 'presentation'],
            datasets: [{
              data: [45, 32, 28, 21]
            }]
          }}
          width={screenWidth - 60}
          height={220}
          chartConfig={chartConfig}
          style={styles.chart}
        />
      </View>
    </ScrollView>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Analytics Dashboard</Text>
      </View>
      
      {renderTabBar()}
      
      <View style={styles.content}>
        {activeTab === 0 && renderTrendAnalysis()}
        {activeTab === 1 && renderTopicModeling()}
        {activeTab === 2 && renderComparativeAnalysis()}
        {activeTab === 3 && renderSearchAnalytics()}
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  tabBar: {
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  tab: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    marginRight: 10,
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#007AFF',
  },
  tabText: {
    marginLeft: 8,
    fontSize: 16,
    color: '#666',
  },
  activeTabText: {
    color: '#007AFF',
    fontWeight: '600',
  },
  content: {
    flex: 1,
  },
  tabContent: {
    flex: 1,
    padding: 15,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  configRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 15,
  },
  label: {
    fontSize: 16,
    color: '#333',
    flex: 1,
  },
  pickerContainer: {
    flex: 2,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
  },
  picker: {
    height: 50,
  },
  analyzeButton: {
    backgroundColor: '#007AFF',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 15,
    borderRadius: 8,
    marginTop: 10,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 15,
  },
  stat: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  statLabel: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  keywordItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  keywordText: {
    fontSize: 16,
    color: '#333',
    flex: 1,
  },
  keywordStats: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  keywordScore: {
    fontSize: 12,
    color: '#666',
    marginRight: 10,
  },
  keywordFreq: {
    fontSize: 12,
    color: '#666',
    marginRight: 10,
  },
  keywordGrowth: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  topicItem: {
    marginBottom: 20,
    paddingBottom: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  topicTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  topicWeight: {
    fontSize: 14,
    color: '#666',
    marginBottom: 10,
  },
  keywordsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  keywordChip: {
    backgroundColor: '#e3f2fd',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 8,
    marginBottom: 8,
  },
  keywordChipText: {
    fontSize: 12,
    color: '#1976d2',
  },
  configButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: '#007AFF',
    borderRadius: 8,
    marginBottom: 15,
  },
  configButtonText: {
    color: '#007AFF',
    fontSize: 16,
    marginLeft: 8,
  },
  sourceInfo: {
    marginTop: 10,
  },
  sourceText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
  similarityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 15,
  },
  similarityLabel: {
    fontSize: 14,
    color: '#333',
    flex: 1,
  },
  progressBar: {
    flex: 2,
    height: 8,
    backgroundColor: '#f0f0f0',
    borderRadius: 4,
    marginHorizontal: 10,
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
  },
  similarityValue: {
    fontSize: 14,
    color: '#333',
    minWidth: 50,
    textAlign: 'right',
  },
  themesContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 10,
  },
  themeChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 8,
    marginBottom: 8,
  },
  commonTheme: {
    backgroundColor: '#e8f5e8',
  },
  uniqueThemeA: {
    backgroundColor: '#fff3e0',
  },
  uniqueThemeB: {
    backgroundColor: '#e3f2fd',
  },
  themeChipText: {
    fontSize: 12,
    color: '#333',
  },
  uniqueTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 15,
    marginBottom: 5,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#fff',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  doneButton: {
    fontSize: 16,
    color: '#007AFF',
    fontWeight: '600',
  },
  modalContent: {
    padding: 20,
  },
  inputGroup: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 16,
    color: '#333',
    marginBottom: 8,
  },
  textInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingHorizontal: 15,
    paddingVertical: 12,
    fontSize: 16,
  },
  comingSoon: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 15,
  },
  featureList: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
});

export default AnalyticsDashboard;