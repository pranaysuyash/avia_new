/**
 * Quality Assessment Screen - React Native Mobile Implementation
 * Comprehensive quality analysis optimized for mobile with full medical schema integration
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  Alert,
  Dimensions,
  TouchableOpacity,
  Modal,
  Switch,
  Share,
  Platform
} from 'react-native';
import {
  LineChart,
  BarChart,
  PieChart,
  ContributionGraph
} from 'react-native-chart-kit';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { format, parseISO, subDays } from 'date-fns';
import AsyncStorage from '@react-native-async-storage/async-storage';

const { width: screenWidth } = Dimensions.get('window');

// Mobile-optimized types for quality assessment
interface MobileQualityAssessment {
  id: string;
  transcript_id: string;
  overall_score: number;
  overall_level: string;
  dimension_scores: Record<string, {
    score: number;
    level: string;
    details: string;
    suggestions: string[];
    evidence: Record<string, any>;
    confidence: number;
  }>;
  summary: string;
  recommendations: string[];
  strengths: string[];
  weaknesses: string[];
  medical_schema_coverage: {
    patient_information: boolean;
    clinical_data: boolean;
    social_determinants: boolean;
    preventive_care: boolean;
    medication_management: boolean;
    care_quality_assessment: boolean;
  };
  assessment_timestamp: string;
  processing_time: number;
}

interface MobileQualityMetrics {
  overall_quality_index: number;
  dimension_averages: Record<string, number>;
  trend_analysis: Array<{
    dimension: string;
    trend_direction: 'IMPROVING' | 'STABLE' | 'DECLINING' | 'VOLATILE';
    slope: number;
    projected_score: number;
    confidence: number;
  }>;
  benchmark_comparisons: Array<{
    dimension: string;
    current_score: number;
    industry_benchmark: number;
    gap: number;
    percentile_rank: number;
  }>;
  risk_indicators: Record<string, number>;
  improvement_opportunities: string[];
  assessment_reliability: number;
  data_completeness: number;
}

interface QualityAssessmentScreenProps {
  route: {
    params: {
      transcriptId?: string;
      assessments?: MobileQualityAssessment[];
      metrics?: MobileQualityMetrics;
      showMedicalFeatures?: boolean;
    };
  };
  navigation: any;
}

const QualityAssessmentScreen: React.FC<QualityAssessmentScreenProps> = ({
  route,
  navigation
}) => {
  const { 
    transcriptId,
    assessments = [],
    metrics,
    showMedicalFeatures = false
  } = route.params || {};

  const [selectedTab, setSelectedTab] = useState(0);
  const [timeRange, setTimeRange] = useState('7d');
  const [refreshing, setRefreshing] = useState(false);
  const [detailsModalVisible, setDetailsModalVisible] = useState(false);
  const [selectedAssessment, setSelectedAssessment] = useState<MobileQualityAssessment | null>(null);
  const [medicalFeaturesEnabled, setMedicalFeaturesEnabled] = useState(showMedicalFeatures);
  const [loading, setLoading] = useState(false);

  // Mobile-optimized color schemes
  const colors = {
    primary: '#2196F3',
    success: '#4CAF50',
    warning: '#FF9800',
    error: '#F44336',
    secondary: '#9C27B0',
    background: '#FFFFFF',
    surface: '#F5F5F5',
    text: '#212121',
    textSecondary: '#757575',
    border: '#E0E0E0'
  };

  const qualityColors = {
    EXCELLENT: colors.success,
    VERY_GOOD: '#8BC34A',
    GOOD: colors.warning,
    FAIR: '#FF7043',
    POOR: colors.error
  };

  // Filter assessments based on time range
  const filteredAssessments = useMemo(() => {
    if (!timeRange || !assessments) return assessments;
    
    const days = parseInt(timeRange.replace('d', ''));
    const cutoffDate = subDays(new Date(), days);
    
    return assessments.filter(assessment => 
      parseISO(assessment.assessment_timestamp) >= cutoffDate
    );
  }, [assessments, timeRange]);

  // Get latest assessment
  const latestAssessment = useMemo(() => {
    if (!filteredAssessments.length) return null;
    return filteredAssessments.sort((a, b) => 
      new Date(b.assessment_timestamp).getTime() - new Date(a.assessment_timestamp).getTime()
    )[0];
  }, [filteredAssessments]);

  // Prepare chart data for mobile visualization
  const chartData = useMemo(() => {
    const data = filteredAssessments.slice(-7).map(assessment => ({
      day: format(parseISO(assessment.assessment_timestamp), 'MM/dd'),
      overall_score: assessment.overall_score,
      accuracy: assessment.dimension_scores.accuracy?.score || 0,
      completeness: assessment.dimension_scores.completeness?.score || 0,
      medical_accuracy: assessment.dimension_scores.medical_accuracy?.score || 0,
      consistency: assessment.dimension_scores.consistency?.score || 0
    }));

    return {
      labels: data.map(d => d.day),
      datasets: [
        {
          data: data.map(d => d.overall_score),
          color: (opacity = 1) => `rgba(33, 150, 243, ${opacity})`,
          strokeWidth: 2
        },
        ...(medicalFeaturesEnabled ? [{
          data: data.map(d => d.medical_accuracy),
          color: (opacity = 1) => `rgba(244, 67, 54, ${opacity})`,
          strokeWidth: 1
        }] : [])
      ]
    };
  }, [filteredAssessments, medicalFeaturesEnabled]);

  // Refresh data
  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      // In real app, would fetch updated data here
    } catch (error) {
      Alert.alert('Error', 'Failed to refresh quality data');
    } finally {
      setRefreshing(false);
    }
  }, []);

  // Share quality report
  const handleShare = useCallback(async () => {
    if (!latestAssessment) return;

    const shareContent = `Quality Assessment Report

Overall Score: ${latestAssessment.overall_score.toFixed(1)}%
Quality Level: ${latestAssessment.overall_level}

Summary: ${latestAssessment.summary}

Generated by Medical Transcription Platform`;

    try {
      await Share.share({
        message: shareContent,
        title: 'Quality Assessment Report'
      });
    } catch (error) {
      Alert.alert('Error', 'Failed to share report');
    }
  }, [latestAssessment]);

  // Save settings
  const saveSettings = useCallback(async () => {
    try {
      await AsyncStorage.setItem('quality_medical_features', medicalFeaturesEnabled.toString());
      await AsyncStorage.setItem('quality_time_range', timeRange);
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  }, [medicalFeaturesEnabled, timeRange]);

  useEffect(() => {
    saveSettings();
  }, [medicalFeaturesEnabled, timeRange, saveSettings]);

  // Quality Score Card Component
  const QualityScoreCard: React.FC<{
    title: string;
    score: number;
    level: string;
    icon: string;
    onPress?: () => void;
  }> = ({ title, score, level, icon, onPress }) => (
    <TouchableOpacity
      style={[styles.scoreCard, { borderLeftColor: qualityColors[level as keyof typeof qualityColors] || colors.primary }]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <View style={styles.scoreCardHeader}>
        <Icon name={icon} size={24} color={colors.primary} />
        <Text style={styles.scoreCardTitle}>{title}</Text>
      </View>
      
      <Text style={[styles.scoreValue, { color: qualityColors[level as keyof typeof qualityColors] || colors.primary }]}>
        {score.toFixed(1)}%
      </Text>
      
      <View style={styles.scoreLevel}>
        <Text style={[styles.levelText, { backgroundColor: qualityColors[level as keyof typeof qualityColors] || colors.primary }]}>
          {level}
        </Text>
      </View>
      
      <View style={[styles.progressBar, { backgroundColor: colors.surface }]}>
        <View 
          style={[
            styles.progressFill, 
            { 
              width: `${score}%`, 
              backgroundColor: qualityColors[level as keyof typeof qualityColors] || colors.primary 
            }
          ]} 
        />
      </View>
    </TouchableOpacity>
  );

  // Medical Schema Coverage Component
  const MedicalSchemaCoverage: React.FC<{ 
    coverage: MobileQualityAssessment['medical_schema_coverage'] 
  }> = ({ coverage }) => {
    const coverageItems = Object.entries(coverage).map(([key, covered]) => ({
      label: key.replace(/_/g, ' ').toUpperCase(),
      covered,
      icon: covered ? 'check-circle' : 'warning'
    }));

    return (
      <View style={styles.schemaCoverage}>
        <Text style={styles.sectionTitle}>Medical Schema Coverage</Text>
        {coverageItems.map((item, index) => (
          <View key={index} style={styles.coverageItem}>
            <Icon 
              name={item.icon} 
              size={20} 
              color={item.covered ? colors.success : colors.warning} 
            />
            <View style={styles.coverageText}>
              <Text style={styles.coverageLabel}>{item.label}</Text>
              <Text style={[styles.coverageStatus, { color: item.covered ? colors.success : colors.warning }]}>
                {item.covered ? 'Documented' : 'Missing or incomplete'}
              </Text>
            </View>
          </View>
        ))}
      </View>
    );
  };

  // Risk Indicator Component
  const RiskIndicator: React.FC<{ risk: number; label: string }> = ({ risk, label }) => {
    const getRiskColor = (risk: number) => {
      if (risk < 0.3) return colors.success;
      if (risk < 0.7) return colors.warning;
      return colors.error;
    };

    const getRiskLabel = (risk: number) => {
      if (risk < 0.3) return 'Low';
      if (risk < 0.7) return 'Medium';
      return 'High';
    };

    return (
      <View style={styles.riskIndicator}>
        <View style={styles.riskHeader}>
          <Text style={styles.riskLabel}>{label}</Text>
          <Text style={[styles.riskLevel, { color: getRiskColor(risk) }]}>
            {getRiskLabel(risk)}
          </Text>
        </View>
        <View style={[styles.riskBar, { backgroundColor: colors.surface }]}>
          <View 
            style={[
              styles.riskFill, 
              { 
                width: `${risk * 100}%`, 
                backgroundColor: getRiskColor(risk) 
              }
            ]} 
          />
        </View>
      </View>
    );
  };

  // Tab Navigation
  const renderTabNavigation = () => (
    <View style={styles.tabNavigation}>
      {['Overview', 'Analysis', 'Recommendations'].map((tab, index) => (
        <TouchableOpacity
          key={index}
          style={[
            styles.tabItem,
            selectedTab === index && styles.tabItemActive
          ]}
          onPress={() => setSelectedTab(index)}
        >
          <Text style={[
            styles.tabText,
            selectedTab === index && styles.tabTextActive
          ]}>
            {tab}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );

  // Overview Tab Content
  const renderOverviewTab = () => (
    <ScrollView style={styles.tabContent}>
      {/* Main Quality Metrics */}
      <View style={styles.metricsGrid}>
        <QualityScoreCard
          title="Overall Quality"
          score={latestAssessment?.overall_score || 0}
          level={latestAssessment?.overall_level || 'UNKNOWN'}
          icon="assessment"
          onPress={() => {
            setSelectedAssessment(latestAssessment);
            setDetailsModalVisible(true);
          }}
        />
        
        <QualityScoreCard
          title="Accuracy"
          score={latestAssessment?.dimension_scores.accuracy?.score || 0}
          level={latestAssessment?.dimension_scores.accuracy?.level || 'UNKNOWN'}
          icon="check-circle"
        />
        
        {medicalFeaturesEnabled && (
          <>
            <QualityScoreCard
              title="Medical Accuracy"
              score={latestAssessment?.dimension_scores.medical_accuracy?.score || 0}
              level={latestAssessment?.dimension_scores.medical_accuracy?.level || 'UNKNOWN'}
              icon="local-hospital"
            />
            
            <QualityScoreCard
              title="HIPAA Compliance"
              score={latestAssessment?.dimension_scores.hipaa_compliance?.score || 0}
              level={latestAssessment?.dimension_scores.hipaa_compliance?.level || 'UNKNOWN'}
              icon="security"
            />
          </>
        )}
      </View>

      {/* Quality Trends Chart */}
      {chartData.labels.length > 1 && (
        <View style={styles.chartContainer}>
          <Text style={styles.chartTitle}>Quality Trends (Last 7 Days)</Text>
          <LineChart
            data={chartData}
            width={screenWidth - 40}
            height={220}
            chartConfig={{
              backgroundColor: colors.background,
              backgroundGradientFrom: colors.background,
              backgroundGradientTo: colors.surface,
              decimalPlaces: 1,
              color: (opacity = 1) => `rgba(33, 150, 243, ${opacity})`,
              labelColor: (opacity = 1) => `rgba(117, 117, 117, ${opacity})`,
              style: {
                borderRadius: 16,
              },
              propsForDots: {
                r: "4",
                strokeWidth: "2",
              }
            }}
            style={styles.chart}
          />
        </View>
      )}

      {/* Medical Schema Coverage */}
      {medicalFeaturesEnabled && latestAssessment?.medical_schema_coverage && (
        <View style={styles.section}>
          <MedicalSchemaCoverage coverage={latestAssessment.medical_schema_coverage} />
        </View>
      )}

      {/* Risk Indicators */}
      {metrics?.risk_indicators && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Risk Indicators</Text>
          {Object.entries(metrics.risk_indicators).map(([risk, value]) => (
            <RiskIndicator 
              key={risk}
              risk={value}
              label={risk.replace(/_/g, ' ').toUpperCase()}
            />
          ))}
        </View>
      )}

      {/* Quick Stats */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Quick Stats</Text>
        <View style={styles.statsGrid}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{filteredAssessments.length}</Text>
            <Text style={styles.statLabel}>Total Assessments</Text>
          </View>
          
          <View style={styles.statItem}>
            <Text style={styles.statValue}>
              {filteredAssessments.length > 0 
                ? (filteredAssessments.reduce((sum, a) => sum + a.processing_time, 0) / filteredAssessments.length / 1000).toFixed(1) + 's'
                : 'N/A'
              }
            </Text>
            <Text style={styles.statLabel}>Avg Processing Time</Text>
          </View>
          
          {metrics && (
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{metrics.assessment_reliability.toFixed(1)}%</Text>
              <Text style={styles.statLabel}>Reliability Score</Text>
            </View>
          )}
        </View>
      </View>
    </ScrollView>
  );

  // Analysis Tab Content
  const renderAnalysisTab = () => (
    <ScrollView style={styles.tabContent}>
      {/* Dimension Breakdown */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Quality Dimensions</Text>
        {latestAssessment && Object.entries(latestAssessment.dimension_scores).map(([dimension, data]) => (
          <View key={dimension} style={styles.dimensionItem}>
            <View style={styles.dimensionHeader}>
              <Text style={styles.dimensionName}>
                {dimension.replace(/_/g, ' ').toUpperCase()}
              </Text>
              <Text style={styles.dimensionScore}>
                {data.score.toFixed(1)}%
              </Text>
            </View>
            
            <View style={[styles.progressBar, { backgroundColor: colors.surface }]}>
              <View 
                style={[
                  styles.progressFill, 
                  { 
                    width: `${data.score}%`, 
                    backgroundColor: data.score >= 90 ? colors.success : data.score >= 75 ? colors.warning : colors.error 
                  }
                ]} 
              />
            </View>
            
            <Text style={styles.dimensionDetails}>{data.details}</Text>
          </View>
        ))}
      </View>

      {/* Trend Analysis */}
      {metrics?.trend_analysis && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Trend Analysis</Text>
          {metrics.trend_analysis.map((trend, index) => {
            const getTrendIcon = () => {
              switch (trend.trend_direction) {
                case 'IMPROVING': return 'trending-up';
                case 'DECLINING': return 'trending-down';
                case 'VOLATILE': return 'warning';
                default: return 'trending-flat';
              }
            };

            const getTrendColor = () => {
              switch (trend.trend_direction) {
                case 'IMPROVING': return colors.success;
                case 'DECLINING': return colors.error;
                case 'VOLATILE': return colors.warning;
                default: return colors.primary;
              }
            };

            return (
              <View key={index} style={styles.trendItem}>
                <View style={styles.trendHeader}>
                  <Text style={styles.trendDimension}>
                    {trend.dimension.replace(/_/g, ' ').toUpperCase()}
                  </Text>
                  <Icon name={getTrendIcon()} size={20} color={getTrendColor()} />
                </View>
                
                <Text style={styles.trendDetail}>
                  Trend: {trend.trend_direction}
                </Text>
                <Text style={styles.trendDetail}>
                  Projection: {trend.projected_score.toFixed(1)}%
                </Text>
                <Text style={styles.trendDetail}>
                  Confidence: {(trend.confidence * 100).toFixed(1)}%
                </Text>
              </View>
            );
          })}
        </View>
      )}

      {/* Benchmark Comparisons */}
      {metrics?.benchmark_comparisons && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Industry Benchmarks</Text>
          {metrics.benchmark_comparisons.map((comparison, index) => (
            <View key={index} style={styles.benchmarkItem}>
              <Text style={styles.benchmarkDimension}>
                {comparison.dimension.replace(/_/g, ' ').toUpperCase()}
              </Text>
              
              <View style={styles.benchmarkScores}>
                <View style={styles.benchmarkScore}>
                  <Text style={styles.benchmarkLabel}>Current</Text>
                  <Text style={[styles.benchmarkValue, { color: colors.primary }]}>
                    {comparison.current_score.toFixed(1)}%
                  </Text>
                </View>
                
                <View style={styles.benchmarkScore}>
                  <Text style={styles.benchmarkLabel}>Industry</Text>
                  <Text style={[styles.benchmarkValue, { color: colors.textSecondary }]}>
                    {comparison.industry_benchmark.toFixed(1)}%
                  </Text>
                </View>
                
                <View style={styles.benchmarkScore}>
                  <Text style={styles.benchmarkLabel}>Gap</Text>
                  <Text style={[
                    styles.benchmarkValue, 
                    { color: comparison.gap >= 0 ? colors.success : colors.error }
                  ]}>
                    {comparison.gap > 0 ? '+' : ''}{comparison.gap.toFixed(1)}%
                  </Text>
                </View>
              </View>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );

  // Recommendations Tab Content
  const renderRecommendationsTab = () => (
    <ScrollView style={styles.tabContent}>
      {/* Recommendations */}
      {latestAssessment?.recommendations && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recommendations</Text>
          {latestAssessment.recommendations.map((rec, index) => (
            <View key={index} style={styles.recommendationItem}>
              <Icon name="lightbulb-outline" size={20} color={colors.warning} />
              <Text style={styles.recommendationText}>{rec}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Improvement Opportunities */}
      {metrics?.improvement_opportunities && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Improvement Opportunities</Text>
          {metrics.improvement_opportunities.slice(0, 5).map((opportunity, index) => (
            <View key={index} style={styles.opportunityItem}>
              <Icon name="trending-up" size={20} color={colors.success} />
              <Text style={styles.opportunityText}>{opportunity}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Strengths and Weaknesses */}
      {latestAssessment && (
        <View style={styles.section}>
          <View style={styles.strengthsWeaknesses}>
            <View style={styles.strengthsColumn}>
              <Text style={[styles.sectionTitle, { color: colors.success }]}>Strengths</Text>
              {latestAssessment.strengths.map((strength, index) => (
                <View key={index} style={styles.strengthItem}>
                  <Icon name="check" size={16} color={colors.success} />
                  <Text style={styles.strengthText}>{strength}</Text>
                </View>
              ))}
            </View>
            
            <View style={styles.weaknessesColumn}>
              <Text style={[styles.sectionTitle, { color: colors.error }]}>Areas for Improvement</Text>
              {latestAssessment.weaknesses.map((weakness, index) => (
                <View key={index} style={styles.weaknessItem}>
                  <Icon name="close" size={16} color={colors.error} />
                  <Text style={styles.weaknessText}>{weakness}</Text>
                </View>
              ))}
            </View>
          </View>
        </View>
      )}
    </ScrollView>
  );

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Icon name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        
        <Text style={styles.headerTitle}>Quality Assessment</Text>
        
        <View style={styles.headerActions}>
          <TouchableOpacity onPress={handleShare} style={styles.headerAction}>
            <Icon name="share" size={24} color={colors.primary} />
          </TouchableOpacity>
          
          <TouchableOpacity 
            onPress={() => setMedicalFeaturesEnabled(!medicalFeaturesEnabled)} 
            style={styles.headerAction}
          >
            <Icon 
              name="local-hospital" 
              size={24} 
              color={medicalFeaturesEnabled ? colors.error : colors.textSecondary} 
            />
          </TouchableOpacity>
        </View>
      </View>

      {/* Tab Navigation */}
      {renderTabNavigation()}

      {/* Content */}
      <View style={styles.content}>
        {selectedTab === 0 && renderOverviewTab()}
        {selectedTab === 1 && renderAnalysisTab()}
        {selectedTab === 2 && renderRecommendationsTab()}
      </View>

      {/* Details Modal */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={detailsModalVisible}
        onRequestClose={() => setDetailsModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Assessment Details</Text>
              <TouchableOpacity onPress={() => setDetailsModalVisible(false)}>
                <Icon name="close" size={24} color={colors.text} />
              </TouchableOpacity>
            </View>
            
            <ScrollView style={styles.modalBody}>
              {selectedAssessment && (
                <>
                  <Text style={styles.modalScore}>
                    Overall Score: {selectedAssessment.overall_score.toFixed(1)}%
                  </Text>
                  
                  <Text style={styles.modalSummary}>
                    {selectedAssessment.summary}
                  </Text>
                  
                  <Text style={styles.modalSectionTitle}>Processing Details:</Text>
                  <Text style={styles.modalDetail}>
                    Processing Time: {(selectedAssessment.processing_time / 1000).toFixed(2)}s
                  </Text>
                  <Text style={styles.modalDetail}>
                    Assessment Time: {format(parseISO(selectedAssessment.assessment_timestamp), 'PPpp')}
                  </Text>
                </>
              )}
            </ScrollView>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
    backgroundColor: '#FFFFFF',
    ...Platform.select({
      ios: {
        paddingTop: 50,
      },
      android: {
        paddingTop: 25,
      },
    }),
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#212121',
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerAction: {
    marginLeft: 15,
  },
  tabNavigation: {
    flexDirection: 'row',
    backgroundColor: '#F5F5F5',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  tabItem: {
    flex: 1,
    paddingVertical: 15,
    alignItems: 'center',
  },
  tabItemActive: {
    borderBottomWidth: 2,
    borderBottomColor: '#2196F3',
    backgroundColor: '#FFFFFF',
  },
  tabText: {
    fontSize: 14,
    color: '#757575',
    fontWeight: '500',
  },
  tabTextActive: {
    color: '#2196F3',
    fontWeight: 'bold',
  },
  content: {
    flex: 1,
  },
  tabContent: {
    flex: 1,
    padding: 20,
  },
  metricsGrid: {
    marginBottom: 20,
  },
  scoreCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    marginBottom: 15,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  scoreCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  scoreCardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#212121',
    marginLeft: 8,
  },
  scoreValue: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  scoreLevel: {
    marginBottom: 12,
  },
  levelText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: 'bold',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    alignSelf: 'flex-start',
  },
  progressBar: {
    height: 6,
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 3,
  },
  chartContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 15,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  chartTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#212121',
    marginBottom: 15,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  section: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#212121',
    marginBottom: 15,
  },
  schemaCoverage: {},
  coverageItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
  },
  coverageText: {
    marginLeft: 12,
    flex: 1,
  },
  coverageLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#212121',
  },
  coverageStatus: {
    fontSize: 12,
    marginTop: 2,
  },
  riskIndicator: {
    marginBottom: 15,
  },
  riskHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  riskLabel: {
    fontSize: 14,
    color: '#212121',
  },
  riskLevel: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  riskBar: {
    height: 4,
    borderRadius: 2,
    overflow: 'hidden',
  },
  riskFill: {
    height: '100%',
    borderRadius: 2,
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  statItem: {
    alignItems: 'center',
    flex: 1,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2196F3',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#757575',
    textAlign: 'center',
  },
  dimensionItem: {
    marginBottom: 20,
  },
  dimensionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  dimensionName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#212121',
  },
  dimensionScore: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#2196F3',
  },
  dimensionDetails: {
    fontSize: 12,
    color: '#757575',
    marginTop: 8,
  },
  trendItem: {
    borderWidth: 1,
    borderColor: '#E0E0E0',
    borderRadius: 8,
    padding: 15,
    marginBottom: 12,
  },
  trendHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  trendDimension: {
    fontSize: 14,
    fontWeight: '600',
    color: '#212121',
  },
  trendDetail: {
    fontSize: 12,
    color: '#757575',
    marginBottom: 2,
  },
  benchmarkItem: {
    borderWidth: 1,
    borderColor: '#E0E0E0',
    borderRadius: 8,
    padding: 15,
    marginBottom: 12,
  },
  benchmarkDimension: {
    fontSize: 14,
    fontWeight: '600',
    color: '#212121',
    marginBottom: 12,
  },
  benchmarkScores: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  benchmarkScore: {
    alignItems: 'center',
  },
  benchmarkLabel: {
    fontSize: 10,
    color: '#757575',
    marginBottom: 4,
  },
  benchmarkValue: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  recommendationItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingVertical: 8,
    marginBottom: 8,
  },
  recommendationText: {
    fontSize: 14,
    color: '#212121',
    marginLeft: 12,
    flex: 1,
    lineHeight: 20,
  },
  opportunityItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingVertical: 8,
    marginBottom: 8,
  },
  opportunityText: {
    fontSize: 14,
    color: '#212121',
    marginLeft: 12,
    flex: 1,
    lineHeight: 20,
  },
  strengthsWeaknesses: {
    flexDirection: 'row',
  },
  strengthsColumn: {
    flex: 1,
    marginRight: 10,
  },
  weaknessesColumn: {
    flex: 1,
    marginLeft: 10,
  },
  strengthItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  strengthText: {
    fontSize: 12,
    color: '#212121',
    marginLeft: 8,
    flex: 1,
    lineHeight: 16,
  },
  weaknessItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  weaknessText: {
    fontSize: 12,
    color: '#212121',
    marginLeft: 8,
    flex: 1,
    lineHeight: 16,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#212121',
  },
  modalBody: {
    padding: 20,
  },
  modalScore: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#2196F3',
    marginBottom: 15,
  },
  modalSummary: {
    fontSize: 16,
    color: '#212121',
    lineHeight: 24,
    marginBottom: 20,
  },
  modalSectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#212121',
    marginBottom: 10,
  },
  modalDetail: {
    fontSize: 14,
    color: '#757575',
    marginBottom: 5,
  },
});

export default QualityAssessmentScreen;