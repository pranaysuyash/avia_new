/**
 * Quality Assessment Panel - Electron Desktop Implementation
 * Comprehensive quality analysis with native desktop features and medical schema integration
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Alert,
  Tabs,
  Tab,
  LinearProgress,
  Chip,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  Assessment,
  TrendingUp,
  TrendingDown,
  TrendingFlat,
  Security,
  LocalHospital,
  Psychology,
  HealthAndSafety,
  Warning,
  CheckCircle,
  Info,
  Download,
  Print,
  Share,
  Fullscreen,
  Minimize,
  Close,
  Settings,
  Refresh
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
  AreaChart,
  Area
} from 'recharts';
import { format, parseISO } from 'date-fns';

// Desktop-specific types and interfaces
interface DesktopQualityAssessment {
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
  file_path?: string;
}

interface DesktopQualityMetrics {
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

interface QualityAssessmentPanelProps {
  assessments: DesktopQualityAssessment[];
  metrics?: DesktopQualityMetrics;
  currentTranscript?: {
    id: string;
    title: string;
    content: string;
    type: 'medical' | 'general';
  };
  onExportReport?: (format: 'pdf' | 'docx' | 'html') => void;
  onPrintReport?: () => void;
  onShareResults?: (method: 'email' | 'clipboard' | 'file') => void;
  onOpenSettings?: () => void;
  showMedicalFeatures?: boolean;
  compactMode?: boolean;
  onWindowAction?: (action: 'minimize' | 'maximize' | 'close') => void;
}

const QualityAssessmentPanel: React.FC<QualityAssessmentPanelProps> = ({
  assessments = [],
  metrics,
  currentTranscript,
  onExportReport,
  onPrintReport,
  onShareResults,
  onOpenSettings,
  showMedicalFeatures = false,
  compactMode = false,
  onWindowAction
}) => {
  const [selectedTab, setSelectedTab] = useState(0);
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false);
  const [selectedAssessment, setSelectedAssessment] = useState<DesktopQualityAssessment | null>(null);
  const [fullscreenMode, setFullscreenMode] = useState(false);
  const [realTimeUpdates, setRealTimeUpdates] = useState(true);
  const [loading, setLoading] = useState(false);

  // Desktop-specific hooks for native integration
  useEffect(() => {
    // Register keyboard shortcuts
    const handleKeyPress = (event: KeyboardEvent) => {
      if (event.ctrlKey) {
        switch (event.key) {
          case 'e':
            event.preventDefault();
            onExportReport?.('pdf');
            break;
          case 'p':
            event.preventDefault();
            onPrintReport?.();
            break;
          case 's':
            event.preventDefault();
            onShareResults?.('file');
            break;
          case 'r':
            event.preventDefault();
            handleRefreshData();
            break;
        }
      }
      
      if (event.key === 'F11') {
        event.preventDefault();
        setFullscreenMode(!fullscreenMode);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [fullscreenMode, onExportReport, onPrintReport, onShareResults]);

  // Native notification support
  const showNotification = useCallback((title: string, body: string, type: 'info' | 'warning' | 'error' = 'info') => {
    if (window.electronAPI?.showNotification) {
      window.electronAPI.showNotification({
        title,
        body,
        type
      });
    }
  }, []);

  // Handle refresh data
  const handleRefreshData = useCallback(async () => {
    setLoading(true);
    try {
      if (window.electronAPI?.refreshQualityData) {
        await window.electronAPI.refreshQualityData();
        showNotification('Quality Data Updated', 'Quality assessment data has been refreshed');
      }
    } catch (error) {
      showNotification('Update Failed', 'Failed to refresh quality data', 'error');
    } finally {
      setLoading(false);
    }
  }, [showNotification]);

  // Get the latest assessment
  const latestAssessment = assessments.length > 0 ? 
    assessments.sort((a, b) => new Date(b.assessment_timestamp).getTime() - new Date(a.assessment_timestamp).getTime())[0] :
    null;

  // Prepare chart data for desktop visualization
  const chartData = assessments.map(assessment => ({
    timestamp: format(parseISO(assessment.assessment_timestamp), 'MMM dd HH:mm'),
    overall_score: assessment.overall_score,
    accuracy: assessment.dimension_scores.accuracy?.score || 0,
    completeness: assessment.dimension_scores.completeness?.score || 0,
    medical_accuracy: assessment.dimension_scores.medical_accuracy?.score || 0,
    consistency: assessment.dimension_scores.consistency?.score || 0,
    processing_time: assessment.processing_time
  })).slice(-20); // Show last 20 assessments

  // Medical schema coverage visualization
  const MedicalSchemaCoverage: React.FC<{ coverage: DesktopQualityAssessment['medical_schema_coverage'] }> = ({ coverage }) => {
    const coverageItems = Object.entries(coverage).map(([key, covered]) => ({
      label: key.replace('_', ' ').toUpperCase(),
      covered,
      icon: covered ? <CheckCircle color="success" /> : <Warning color="warning" />
    }));

    return (
      <Box>
        <Typography variant="h6" sx={{ mb: 2 }}>Medical Schema Coverage</Typography>
        <List dense>
          {coverageItems.map((item, index) => (
            <ListItem key={index}>
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText 
                primary={item.label}
                secondary={item.covered ? 'Documented' : 'Missing or incomplete'}
              />
            </ListItem>
          ))}
        </List>
      </Box>
    );
  };

  // Quality Score Card Component
  const QualityScoreCard: React.FC<{ 
    title: string; 
    score: number; 
    level: string; 
    icon: React.ReactNode;
    color: string;
  }> = ({ title, score, level, icon, color }) => (
    <Card sx={{ height: '100%', cursor: 'pointer' }} onClick={() => setDetailsDialogOpen(true)}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          {icon}
          <Typography variant="h6" sx={{ ml: 1 }}>{title}</Typography>
        </Box>
        
        <Typography variant="h3" sx={{ color, mb: 1 }}>
          {score.toFixed(1)}%
        </Typography>
        
        <Chip 
          label={level}
          color={score >= 90 ? 'success' : score >= 75 ? 'warning' : 'error'}
          size="small"
        />
        
        <LinearProgress 
          variant="determinate" 
          value={score} 
          sx={{ mt: 2 }}
          color={score >= 90 ? 'success' : score >= 75 ? 'warning' : 'error'}
        />
      </CardContent>
    </Card>
  );

  // Desktop Window Controls
  const WindowControls: React.FC = () => (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Tooltip title="Minimize (Ctrl+M)">
        <IconButton size="small" onClick={() => onWindowAction?.('minimize')}>
          <Minimize fontSize="small" />
        </IconButton>
      </Tooltip>
      
      <Tooltip title="Toggle Fullscreen (F11)">
        <IconButton size="small" onClick={() => setFullscreenMode(!fullscreenMode)}>
          <Fullscreen fontSize="small" />
        </IconButton>
      </Tooltip>
      
      <Tooltip title="Close">
        <IconButton size="small" onClick={() => onWindowAction?.('close')}>
          <Close fontSize="small" />
        </IconButton>
      </Tooltip>
    </Box>
  );

  // Overview Tab
  const OverviewTab: React.FC = () => (
    <Grid container spacing={2}>
      {/* Main Quality Metrics */}
      <Grid item xs={12} md={3}>
        <QualityScoreCard
          title="Overall Quality"
          score={latestAssessment?.overall_score || 0}
          level={latestAssessment?.overall_level || 'UNKNOWN'}
          icon={<Assessment color="primary" />}
          color="#2196f3"
        />
      </Grid>

      <Grid item xs={12} md={3}>
        <QualityScoreCard
          title="Accuracy"
          score={latestAssessment?.dimension_scores.accuracy?.score || 0}
          level={latestAssessment?.dimension_scores.accuracy?.level || 'UNKNOWN'}
          icon={<CheckCircle color="success" />}
          color="#4caf50"
        />
      </Grid>

      {showMedicalFeatures && (
        <Grid item xs={12} md={3}>
          <QualityScoreCard
            title="Medical Accuracy"
            score={latestAssessment?.dimension_scores.medical_accuracy?.score || 0}
            level={latestAssessment?.dimension_scores.medical_accuracy?.level || 'UNKNOWN'}
            icon={<LocalHospital color="error" />}
            color="#f44336"
          />
        </Grid>
      )}

      {showMedicalFeatures && (
        <Grid item xs={12} md={3}>
          <QualityScoreCard
            title="HIPAA Compliance"
            score={latestAssessment?.dimension_scores.hipaa_compliance?.score || 0}
            level={latestAssessment?.dimension_scores.hipaa_compliance?.level || 'UNKNOWN'}
            icon={<Security color="secondary" />}
            color="#9c27b0"
          />
        </Grid>
      )}

      {/* Quality Trends Chart */}
      <Grid item xs={12} md={8}>
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>Quality Trends</Typography>
            
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" />
                <YAxis domain={[0, 100]} />
                <RechartsTooltip />
                <Area 
                  type="monotone" 
                  dataKey="overall_score" 
                  stackId="1"
                  stroke="#2196f3" 
                  fill="#2196f3"
                  fillOpacity={0.6}
                />
                <Area 
                  type="monotone" 
                  dataKey="accuracy" 
                  stackId="2"
                  stroke="#4caf50" 
                  fill="#4caf50"
                  fillOpacity={0.3}
                />
                {showMedicalFeatures && (
                  <Area 
                    type="monotone" 
                    dataKey="medical_accuracy" 
                    stackId="3"
                    stroke="#f44336" 
                    fill="#f44336"
                    fillOpacity={0.3}
                  />
                )}
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </Grid>

      {/* Quick Stats */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>Quick Stats</Typography>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Total Assessments: {assessments.length}
              </Typography>
            </Box>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Avg Processing Time: {
                  assessments.length > 0 
                    ? (assessments.reduce((sum, a) => sum + a.processing_time, 0) / assessments.length / 1000).toFixed(2) + 's'
                    : 'N/A'
                }
              </Typography>
            </Box>
            
            {metrics && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Reliability Score: {metrics.assessment_reliability.toFixed(1)}%
                </Typography>
              </Box>
            )}
            
            {currentTranscript && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Current Transcript: {currentTranscript.title}
                </Typography>
                <Chip 
                  label={currentTranscript.type.toUpperCase()}
                  size="small"
                  color={currentTranscript.type === 'medical' ? 'error' : 'default'}
                />
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Medical Schema Coverage */}
      {showMedicalFeatures && latestAssessment?.medical_schema_coverage && (
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <MedicalSchemaCoverage coverage={latestAssessment.medical_schema_coverage} />
            </CardContent>
          </Card>
        </Grid>
      )}
    </Grid>
  );

  // Detailed Analysis Tab
  const DetailedAnalysisTab: React.FC = () => (
    <Grid container spacing={2}>
      {/* Dimension Breakdown */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>Quality Dimensions</Typography>
            
            {latestAssessment && Object.entries(latestAssessment.dimension_scores).map(([dimension, data]) => (
              <Box key={dimension} sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">
                    {dimension.replace('_', ' ').toUpperCase()}
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                    {data.score.toFixed(1)}%
                  </Typography>
                </Box>
                
                <LinearProgress 
                  variant="determinate" 
                  value={data.score} 
                  color={data.score >= 90 ? 'success' : data.score >= 75 ? 'warning' : 'error'}
                />
                
                <Typography variant="caption" color="text.secondary">
                  {data.details}
                </Typography>
              </Box>
            ))}
          </CardContent>
        </Card>
      </Grid>

      {/* Recommendations */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>Recommendations</Typography>
            
            {latestAssessment?.recommendations.map((rec, index) => (
              <Alert key={index} severity="info" sx={{ mb: 1 }}>
                {rec}
              </Alert>
            ))}
            
            {metrics?.improvement_opportunities && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                  Improvement Opportunities:
                </Typography>
                {metrics.improvement_opportunities.slice(0, 3).map((opp, index) => (
                  <Typography key={index} variant="body2" sx={{ ml: 2, mb: 0.5 }}>
                    • {opp}
                  </Typography>
                ))}
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Trend Analysis */}
      {metrics?.trend_analysis && (
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Trend Analysis</Typography>
              
              <Grid container spacing={2}>
                {metrics.trend_analysis.map((trend, index) => (
                  <Grid key={index} item xs={12} md={4}>
                    <Box sx={{ p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <Typography variant="subtitle1">
                          {trend.dimension.replace('_', ' ').toUpperCase()}
                        </Typography>
                        {trend.trend_direction === 'IMPROVING' && <TrendingUp color="success" />}
                        {trend.trend_direction === 'DECLINING' && <TrendingDown color="error" />}
                        {trend.trend_direction === 'STABLE' && <TrendingFlat color="info" />}
                        {trend.trend_direction === 'VOLATILE' && <Warning color="warning" />}
                      </Box>
                      
                      <Typography variant="body2" color="text.secondary">
                        Projection: {trend.projected_score.toFixed(1)}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Confidence: {(trend.confidence * 100).toFixed(1)}%
                      </Typography>
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      )}
    </Grid>
  );

  return (
    <Box sx={{ 
      height: fullscreenMode ? '100vh' : 'auto',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Header with Desktop Controls */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        p: 2,
        borderBottom: 1,
        borderColor: 'divider'
      }}>
        <Typography variant="h5">Quality Assessment</Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {/* Real-time Updates Toggle */}
          <FormControlLabel
            control={
              <Switch 
                checked={realTimeUpdates} 
                onChange={(e) => setRealTimeUpdates(e.target.checked)}
                size="small"
              />
            }
            label="Real-time"
          />

          {/* Action Buttons */}
          <Tooltip title="Refresh (Ctrl+R)">
            <IconButton onClick={handleRefreshData} disabled={loading}>
              <Refresh />
            </IconButton>
          </Tooltip>

          <Tooltip title="Export Report (Ctrl+E)">
            <IconButton onClick={() => onExportReport?.('pdf')}>
              <Download />
            </IconButton>
          </Tooltip>

          <Tooltip title="Print (Ctrl+P)">
            <IconButton onClick={onPrintReport}>
              <Print />
            </IconButton>
          </Tooltip>

          <Tooltip title="Share (Ctrl+S)">
            <IconButton onClick={() => onShareResults?.('file')}>
              <Share />
            </IconButton>
          </Tooltip>

          <Tooltip title="Settings">
            <IconButton onClick={onOpenSettings}>
              <Settings />
            </IconButton>
          </Tooltip>

          <Divider orientation="vertical" flexItem />

          <WindowControls />
        </Box>
      </Box>

      {/* Loading Indicator */}
      {loading && <LinearProgress />}

      {/* Main Content */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        {/* Tabs */}
        <Tabs 
          value={selectedTab} 
          onChange={(_, newValue) => setSelectedTab(newValue)} 
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Overview" />
          <Tab label="Detailed Analysis" />
          {showMedicalFeatures && <Tab label="Medical Insights" />}
        </Tabs>

        {/* Tab Content */}
        <Box sx={{ p: 2 }}>
          {selectedTab === 0 && <OverviewTab />}
          {selectedTab === 1 && <DetailedAnalysisTab />}
          {selectedTab === 2 && showMedicalFeatures && (
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" sx={{ mb: 2 }}>Medical Quality Insights</Typography>
                    <Typography variant="body2">
                      Medical-specific quality analysis will be displayed here.
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </Box>
      </Box>

      {/* Details Dialog */}
      <Dialog 
        open={detailsDialogOpen} 
        onClose={() => setDetailsDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Quality Assessment Details</DialogTitle>
        <DialogContent>
          {selectedAssessment && (
            <Box>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Overall Score: {selectedAssessment.overall_score.toFixed(1)}%
              </Typography>
              
              <Typography variant="body1" sx={{ mb: 2 }}>
                {selectedAssessment.summary}
              </Typography>
              
              <Typography variant="h6" sx={{ mb: 1 }}>Strengths:</Typography>
              {selectedAssessment.strengths.map((strength, index) => (
                <Typography key={index} variant="body2" sx={{ ml: 2, mb: 0.5 }}>
                  • {strength}
                </Typography>
              ))}
              
              <Typography variant="h6" sx={{ mt: 2, mb: 1 }}>Areas for Improvement:</Typography>
              {selectedAssessment.weaknesses.map((weakness, index) => (
                <Typography key={index} variant="body2" sx={{ ml: 2, mb: 0.5 }}>
                  • {weakness}
                </Typography>
              ))}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default QualityAssessmentPanel;