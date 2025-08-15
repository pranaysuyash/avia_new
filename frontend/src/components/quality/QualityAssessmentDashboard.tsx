/**
 * Quality Assessment Dashboard - Comprehensive quality analysis interface
 * Integrates with comprehensive medical schema and advanced metrics engine
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  LinearProgress,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Tooltip,
  IconButton,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  TrendingFlat,
  Assessment,
  Security,
  HealthAndSafety,
  Psychology,
  LocalHospital,
  Warning,
  CheckCircle,
  Info,
  Refresh,
  Download,
  Settings
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter
} from 'recharts';
import { format, parseISO, subDays } from 'date-fns';

// Types for quality assessment data
interface QualityDimension {
  dimension: string;
  score: number;
  level: 'EXCELLENT' | 'VERY_GOOD' | 'GOOD' | 'FAIR' | 'POOR';
  details: string;
  suggestions: string[];
  evidence: Record<string, any>;
  confidence: number;
}

interface QualityAssessment {
  id: string;
  overall_score: number;
  overall_level: string;
  dimension_scores: Record<string, QualityDimension>;
  summary: string;
  recommendations: string[];
  strengths: string[];
  weaknesses: string[];
  metadata: Record<string, any>;
  assessment_timestamp: string;
}

interface QualityTrend {
  dimension: string;
  trend_direction: 'IMPROVING' | 'STABLE' | 'DECLINING' | 'VOLATILE';
  trend_strength: number;
  slope: number;
  projected_score_30_days: number;
  data_points: number;
}

interface BenchmarkComparison {
  dimension: string;
  current_score: number;
  industry_benchmark: number;
  percentile_rank: number;
  gap_analysis: string;
  competitive_position: 'leading' | 'competitive' | 'lagging';
}

interface QualityMetrics {
  overall_quality_index: number;
  dimension_scores: Record<string, number>;
  trend_analysis: QualityTrend[];
  benchmark_comparisons: BenchmarkComparison[];
  risk_indicators: Record<string, number>;
  improvement_opportunities: string[];
  quality_volatility: number;
  metric_reliability_score: number;
  assessment_confidence: number;
}

interface QualityAssessmentDashboardProps {
  transcriptId?: string;
  assessments: QualityAssessment[];
  metrics?: QualityMetrics;
  onRefresh?: () => void;
  onExport?: (format: 'pdf' | 'excel' | 'json') => void;
  showMedicalFeatures?: boolean;
  realTimeMode?: boolean;
}

const QualityAssessmentDashboard: React.FC<QualityAssessmentDashboardProps> = ({
  transcriptId,
  assessments = [],
  metrics,
  onRefresh,
  onExport,
  showMedicalFeatures = false,
  realTimeMode = false
}) => {
  const [selectedTab, setSelectedTab] = useState(0);
  const [timeRange, setTimeRange] = useState('7d');
  const [showDetails, setShowDetails] = useState(false);
  const [selectedDimension, setSelectedDimension] = useState<string>('all');
  const [loading, setLoading] = useState(false);

  // Color schemes for different quality levels
  const qualityColors = {
    EXCELLENT: '#4caf50',
    VERY_GOOD: '#8bc34a',
    GOOD: '#ffc107',
    FAIR: '#ff9800',
    POOR: '#f44336'
  };

  const trendColors = {
    IMPROVING: '#4caf50',
    STABLE: '#2196f3',
    DECLINING: '#f44336',
    VOLATILE: '#ff9800'
  };

  // Filter assessments based on time range
  const filteredAssessments = useMemo(() => {
    if (!timeRange) return assessments;
    
    const days = parseInt(timeRange.replace('d', ''));
    const cutoffDate = subDays(new Date(), days);
    
    return assessments.filter(assessment => 
      parseISO(assessment.assessment_timestamp) >= cutoffDate
    );
  }, [assessments, timeRange]);

  // Prepare chart data
  const chartData = useMemo(() => {
    return filteredAssessments.map(assessment => ({
      timestamp: format(parseISO(assessment.assessment_timestamp), 'MMM dd'),
      overall_score: assessment.overall_score,
      accuracy: assessment.dimension_scores.accuracy?.score || 0,
      completeness: assessment.dimension_scores.completeness?.score || 0,
      medical_accuracy: assessment.dimension_scores.medical_accuracy?.score || 0,
      consistency: assessment.dimension_scores.consistency?.score || 0,
      semantic_coherence: assessment.dimension_scores.semantic_coherence?.score || 0
    }));
  }, [filteredAssessments]);

  // Prepare radar chart data for latest assessment
  const radarData = useMemo(() => {
    if (filteredAssessments.length === 0) return [];
    
    const latest = filteredAssessments[filteredAssessments.length - 1];
    
    return Object.entries(latest.dimension_scores).map(([dimension, data]) => ({
      dimension: dimension.replace('_', ' ').toUpperCase(),
      score: data.score,
      benchmark: metrics?.benchmark_comparisons.find(b => b.dimension === dimension)?.industry_benchmark || 85
    }));
  }, [filteredAssessments, metrics]);

  // Get trend icon
  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'IMPROVING': return <TrendingUp color="success" />;
      case 'DECLINING': return <TrendingDown color="error" />;
      case 'VOLATILE': return <Warning color="warning" />;
      default: return <TrendingFlat color="info" />;
    }
  };

  // Get quality level color
  const getQualityColor = (level: string) => {
    return qualityColors[level as keyof typeof qualityColors] || '#757575';
  };

  // Risk indicator component
  const RiskIndicator: React.FC<{ risk: number; label: string }> = ({ risk, label }) => {
    const getRiskColor = (risk: number) => {
      if (risk < 0.3) return 'success';
      if (risk < 0.7) return 'warning';
      return 'error';
    };

    const getRiskLabel = (risk: number) => {
      if (risk < 0.3) return 'Low';
      if (risk < 0.7) return 'Medium';
      return 'High';
    };

    return (
      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="body2">{label}</Typography>
          <Chip 
            label={getRiskLabel(risk)} 
            color={getRiskColor(risk) as any}
            size="small"
          />
        </Box>
        <LinearProgress 
          variant="determinate" 
          value={risk * 100} 
          color={getRiskColor(risk) as any}
        />
      </Box>
    );
  };

  // Medical-specific insights component
  const MedicalInsights: React.FC = () => {
    if (!showMedicalFeatures) return null;

    const latestAssessment = filteredAssessments[filteredAssessments.length - 1];
    if (!latestAssessment) return null;

    const medicalScore = latestAssessment.dimension_scores.medical_accuracy;
    const hipaaScore = latestAssessments.dimension_scores.hipaa_compliance;

    return (
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <LocalHospital color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Medical Accuracy</Typography>
              </Box>
              
              {medicalScore && (
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                    <Typography variant="h4" color="primary">
                      {medicalScore.score.toFixed(1)}%
                    </Typography>
                    <Chip 
                      label={medicalScore.level}
                      color={medicalScore.score >= 90 ? 'success' : medicalScore.score >= 80 ? 'warning' : 'error'}
                    />
                  </Box>
                  
                  <Typography variant="body2" sx={{ mb: 2 }}>
                    {medicalScore.details}
                  </Typography>
                  
                  {medicalScore.evidence.schema_coverage_ratio && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        Medical Schema Coverage: {(medicalScore.evidence.schema_coverage_ratio * 100).toFixed(1)}%
                      </Typography>
                      <LinearProgress 
                        variant="determinate" 
                        value={medicalScore.evidence.schema_coverage_ratio * 100}
                        color={medicalScore.evidence.schema_coverage_ratio > 0.8 ? 'success' : 'warning'}
                      />
                    </Box>
                  )}
                  
                  {medicalScore.evidence.medications_identified && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        Medications Identified: {medicalScore.evidence.medications_identified.length}
                      </Typography>
                    </Box>
                  )}
                  
                  {medicalScore.evidence.social_determinants_addressed && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        Social Determinants Addressed: {medicalScore.evidence.social_determinants_addressed.length}
                      </Typography>
                    </Box>
                  )}
                  
                  {medicalScore.suggestions.length > 0 && (
                    <Box>
                      <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                        Recommendations:
                      </Typography>
                      {medicalScore.suggestions.slice(0, 3).map((suggestion, index) => (
                        <Typography key={index} variant="body2" sx={{ ml: 2, mb: 0.5 }}>
                          • {suggestion}
                        </Typography>
                      ))}
                    </Box>
                  )}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Security color="secondary" sx={{ mr: 1 }} />
                <Typography variant="h6">HIPAA Compliance</Typography>
              </Box>
              
              {hipaaScore && (
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                    <Typography variant="h4" color="secondary">
                      {hipaaScore.score.toFixed(1)}%
                    </Typography>
                    <Chip 
                      label={hipaaScore.level}
                      color={hipaaScore.score >= 95 ? 'success' : 'error'}
                    />
                  </Box>
                  
                  <Typography variant="body2" sx={{ mb: 2 }}>
                    {hipaaScore.details}
                  </Typography>
                  
                  {hipaaScore.evidence.phi_violations && (
                    <Alert 
                      severity={hipaaScore.evidence.phi_violations.length > 0 ? 'warning' : 'success'}
                      sx={{ mb: 2 }}
                    >
                      {hipaaScore.evidence.phi_violations.length > 0 
                        ? `${hipaaScore.evidence.phi_violations.length} PHI violations detected`
                        : 'No PHI violations detected'
                      }
                    </Alert>
                  )}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  };

  // Overview tab content
  const OverviewTab: React.FC = () => (
    <Grid container spacing={3}>
      {/* Overall Score Card */}
      <Grid item xs={12} md={4}>
        <Card sx={{ height: '100%' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Assessment color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6">Overall Quality</Typography>
            </Box>
            
            {filteredAssessments.length > 0 && (
              <Box>
                <Typography variant="h3" color="primary" sx={{ mb: 1 }}>
                  {metrics?.overall_quality_index.toFixed(1) || filteredAssessments[filteredAssessments.length - 1].overall_score.toFixed(1)}%
                </Typography>
                
                <Chip 
                  label={filteredAssessments[filteredAssessments.length - 1].overall_level}
                  color={filteredAssessments[filteredAssessments.length - 1].overall_score >= 90 ? 'success' : 
                         filteredAssessments[filteredAssessments.length - 1].overall_score >= 75 ? 'warning' : 'error'}
                  sx={{ mb: 2 }}
                />
                
                <Typography variant="body2">
                  {filteredAssessments[filteredAssessments.length - 1].summary}
                </Typography>
              </Box>
            )}
            
            {metrics && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Reliability: {metrics.metric_reliability_score.toFixed(1)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Confidence: {metrics.assessment_confidence.toFixed(1)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Volatility: {metrics.quality_volatility.toFixed(1)}%
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Quality Trends Chart */}
      <Grid item xs={12} md={8}>
        <Card sx={{ height: '100%' }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>Quality Trends</Typography>
            
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" />
                <YAxis domain={[0, 100]} />
                <RechartsTooltip />
                <Line 
                  type="monotone" 
                  dataKey="overall_score" 
                  stroke="#2196f3" 
                  strokeWidth={2}
                  dot={{ fill: '#2196f3' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="accuracy" 
                  stroke="#4caf50" 
                  strokeWidth={1}
                />
                <Line 
                  type="monotone" 
                  dataKey="completeness" 
                  stroke="#ff9800" 
                  strokeWidth={1}
                />
                {showMedicalFeatures && (
                  <Line 
                    type="monotone" 
                    dataKey="medical_accuracy" 
                    stroke="#f44336" 
                    strokeWidth={2}
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </Grid>

      {/* Medical Insights (if enabled) */}
      {showMedicalFeatures && (
        <Grid item xs={12}>
          <MedicalInsights />
        </Grid>
      )}

      {/* Risk Indicators */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>Risk Indicators</Typography>
            
            {metrics?.risk_indicators && Object.entries(metrics.risk_indicators).map(([risk, value]) => (
              <RiskIndicator 
                key={risk}
                risk={value}
                label={risk.replace('_', ' ').toUpperCase()}
              />
            ))}
          </CardContent>
        </Card>
      </Grid>

      {/* Improvement Opportunities */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>Improvement Opportunities</Typography>
            
            {metrics?.improvement_opportunities.slice(0, 5).map((opportunity, index) => (
              <Alert key={index} severity="info" sx={{ mb: 1 }}>
                {opportunity}
              </Alert>
            ))}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  // Detailed analysis tab
  const DetailedAnalysisTab: React.FC = () => (
    <Grid container spacing={3}>
      {/* Dimension Scores Radar Chart */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>Quality Dimensions</Typography>
            
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={radarData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="dimension" />
                <PolarRadiusAxis domain={[0, 100]} />
                <Radar 
                  name="Current Score" 
                  dataKey="score" 
                  stroke="#2196f3" 
                  fill="#2196f3" 
                  fillOpacity={0.3}
                />
                <Radar 
                  name="Benchmark" 
                  dataKey="benchmark" 
                  stroke="#ff9800" 
                  fill="transparent"
                  strokeDasharray="5 5"
                />
              </RadarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </Grid>

      {/* Trend Analysis */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>Trend Analysis</Typography>
            
            {metrics?.trend_analysis.map((trend, index) => (
              <Box key={index} sx={{ mb: 2, p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="subtitle1">
                    {trend.dimension.replace('_', ' ').toUpperCase()}
                  </Typography>
                  {getTrendIcon(trend.trend_direction)}
                </Box>
                
                <Typography variant="body2" color="text.secondary">
                  Trend: {trend.trend_direction} (Strength: {(trend.trend_strength * 100).toFixed(1)}%)
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  30-day projection: {trend.projected_score_30_days.toFixed(1)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Data points: {trend.data_points}
                </Typography>
              </Box>
            ))}
          </CardContent>
        </Card>
      </Grid>

      {/* Benchmark Comparisons */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>Industry Benchmarks</Typography>
            
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={metrics?.benchmark_comparisons || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="dimension" 
                  angle={-45}
                  textAnchor="end"
                  height={100}
                />
                <YAxis domain={[0, 100]} />
                <RechartsTooltip />
                <Bar dataKey="current_score" fill="#2196f3" name="Current Score" />
                <Bar dataKey="industry_benchmark" fill="#ff9800" name="Industry Benchmark" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Quality Assessment Dashboard</Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {/* Time Range Selector */}
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Time Range</InputLabel>
            <Select 
              value={timeRange} 
              onChange={(e) => setTimeRange(e.target.value)}
              label="Time Range"
            >
              <MenuItem value="7d">Last 7 days</MenuItem>
              <MenuItem value="30d">Last 30 days</MenuItem>
              <MenuItem value="90d">Last 90 days</MenuItem>
            </Select>
          </FormControl>

          {/* Medical Features Toggle */}
          <FormControlLabel
            control={
              <Switch 
                checked={showMedicalFeatures} 
                onChange={(e) => setShowMedicalFeatures(e.target.checked)}
              />
            }
            label="Medical Features"
          />

          {/* Actions */}
          <IconButton onClick={onRefresh} disabled={loading}>
            <Refresh />
          </IconButton>
          
          {onExport && (
            <Button 
              variant="outlined" 
              startIcon={<Download />}
              onClick={() => onExport('pdf')}
            >
              Export
            </Button>
          )}
        </Box>
      </Box>

      {/* Loading State */}
      {loading && <CircularProgress sx={{ display: 'block', mx: 'auto', mb: 3 }} />}

      {/* Tabs */}
      <Tabs value={selectedTab} onChange={(_, newValue) => setSelectedTab(newValue)} sx={{ mb: 3 }}>
        <Tab label="Overview" />
        <Tab label="Detailed Analysis" />
        <Tab label="Recommendations" />
        {showMedicalFeatures && <Tab label="Medical Insights" />}
      </Tabs>

      {/* Tab Content */}
      {selectedTab === 0 && <OverviewTab />}
      {selectedTab === 1 && <DetailedAnalysisTab />}
      {selectedTab === 2 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>Recommendations</Typography>
                
                {filteredAssessments.length > 0 && (
                  <Box>
                    {filteredAssessments[filteredAssessments.length - 1].recommendations.map((rec, index) => (
                      <Alert key={index} severity="info" sx={{ mb: 1 }}>
                        {rec}
                      </Alert>
                    ))}
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
      {selectedTab === 3 && showMedicalFeatures && <MedicalInsights />}
    </Box>
  );
};

export default QualityAssessmentDashboard;