/**
 * Content Intelligence Component
 * Advanced content analysis with NLP and ML insights
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Grid,
  Paper,
  Chip,
  CircularProgress,
  Alert,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Tooltip,
  Divider,
  Tab,
  Tabs,
  List,
  ListItem,
  ListItemText,
  Badge,
  Avatar,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Analytics as AnalyticsIcon,
  Psychology as PsychologyIcon,
  TrendingUp as TrendingUpIcon,
  Lightbulb as LightbulbIcon,
  CloudUpload as CloudUploadIcon,
  Assessment as AssessmentIcon,
  Category as CategoryIcon,
  SentimentSatisfied as SentimentIcon,
  Label as LabelIcon,
  Group as GroupIcon,
  Share as ShareIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as ChartTooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

// Styled components
const StyledCard = styled(Card)(({ theme }) => ({
  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  color: 'white',
  marginBottom: theme.spacing(2),
}));

const MetricCard = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  textAlign: 'center',
  background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
  borderRadius: theme.spacing(2),
  transition: 'transform 0.3s',
  '&:hover': {
    transform: 'translateY(-5px)',
    boxShadow: theme.shadows[8],
  },
}));

const QualityBadge = styled(Badge)(({ theme, quality }: any) => ({
  '& .MuiBadge-badge': {
    backgroundColor: quality > 80 ? '#4caf50' : quality > 60 ? '#ff9800' : '#f44336',
    color: 'white',
    padding: '0 8px',
    height: '24px',
    borderRadius: '12px',
  },
}));

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
  const [contentType, setContentType] = useState('transcript');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<ContentAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [compareMode, setCompareMode] = useState(false);
  const [contentHistory, setContentHistory] = useState<ContentAnalysis[]>([]);

  const analyzeContent = useCallback(async () => {
    if (!content.trim()) {
      setError('Please enter content to analyze');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      // Mock analysis for demonstration
      // In production, this would call the actual API
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
      
      if (onAnalysisComplete) {
        onAnalysisComplete(mockAnalysis);
      }
    } catch (err) {
      setError('Failed to analyze content. Please try again.');
      console.error('Analysis error:', err);
    } finally {
      setIsAnalyzing(false);
    }
  }, [content, title, contentType, onAnalysisComplete]);

  const exportAnalysis = useCallback(() => {
    if (!analysis) return;

    const dataStr = JSON.stringify(analysis, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `content_analysis_${analysis.contentId}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  }, [analysis]);

  const renderMetrics = () => {
    if (!analysis) return null;

    return (
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard elevation={3}>
            <QualityBadge quality={analysis.qualityScore * 100} badgeContent={`${(analysis.qualityScore * 100).toFixed(0)}%`}>
              <AssessmentIcon style={{ fontSize: 40, color: '#667eea' }} />
            </QualityBadge>
            <Typography variant="h6" style={{ marginTop: 8 }}>
              Quality Score
            </Typography>
          </MetricCard>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard elevation={3}>
            <CircularProgress
              variant="determinate"
              value={analysis.readabilityScore * 100}
              size={60}
              thickness={4}
              style={{ color: '#764ba2' }}
            />
            <Typography variant="h6" style={{ marginTop: 8 }}>
              Readability
            </Typography>
            <Typography variant="body2" color="textSecondary">
              {(analysis.readabilityScore * 100).toFixed(0)}%
            </Typography>
          </MetricCard>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard elevation={3}>
            <TrendingUpIcon style={{ fontSize: 40, color: '#f093fb' }} />
            <Typography variant="h6">
              Engagement
            </Typography>
            <Typography variant="h4" color="primary">
              {(analysis.engagementPrediction * 100).toFixed(0)}%
            </Typography>
          </MetricCard>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard elevation={3}>
            <LightbulbIcon style={{ fontSize: 40, color: '#f5576c' }} />
            <Typography variant="h6">
              Viral Potential
            </Typography>
            <LinearProgress
              variant="determinate"
              value={analysis.viralityScore * 100}
              style={{ marginTop: 8, height: 8, borderRadius: 4 }}
            />
          </MetricCard>
        </Grid>
      </Grid>
    );
  };

  const renderSentimentChart = () => {
    if (!analysis) return null;

    const data = [
      { name: 'Positive', value: analysis.sentiment.positive * 100, color: '#4caf50' },
      { name: 'Negative', value: analysis.sentiment.negative * 100, color: '#f44336' },
      { name: 'Neutral', value: analysis.sentiment.neutral * 100, color: '#9e9e9e' },
    ];

    return (
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, value }) => `${name}: ${value.toFixed(0)}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <ChartTooltip />
        </PieChart>
      </ResponsiveContainer>
    );
  };

  const renderKeywordsChart = () => {
    if (!analysis) return null;

    const data = analysis.keywords.map(k => ({
      keyword: k.keyword,
      score: k.score * 100,
    }));

    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="keyword" angle={-45} textAnchor="end" height={100} />
          <YAxis />
          <ChartTooltip />
          <Bar dataKey="score" fill="#667eea" />
        </BarChart>
      </ResponsiveContainer>
    );
  };

  return (
    <Box>
      <StyledCard>
        <CardContent>
          <Typography variant="h4" gutterBottom>
            <PsychologyIcon style={{ marginRight: 8, verticalAlign: 'middle' }} />
            Content Intelligence
          </Typography>
          <Typography variant="body1">
            Analyze content with advanced NLP and ML to extract insights, sentiment, and recommendations
          </Typography>
        </CardContent>
      </StyledCard>

      <Card>
        <CardContent>
          <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
            <Tab label="Analyze" icon={<AnalyticsIcon />} />
            <Tab label="Compare" icon={<AssessmentIcon />} />
            <Tab label="History" icon={<CloudUploadIcon />} />
          </Tabs>

          {tabValue === 0 && (
            <Box mt={3}>
              <Grid container spacing={3}>
                <Grid item xs={12} md={8}>
                  <TextField
                    fullWidth
                    label="Title"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    variant="outlined"
                    margin="normal"
                  />
                  <TextField
                    fullWidth
                    multiline
                    rows={8}
                    label="Content to Analyze"
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    variant="outlined"
                    margin="normal"
                    placeholder="Paste your content here for analysis..."
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <Paper elevation={2} style={{ padding: 16, marginTop: 16 }}>
                    <Typography variant="h6" gutterBottom>
                      Analysis Options
                    </Typography>
                    <Button
                      fullWidth
                      variant="contained"
                      color="primary"
                      onClick={analyzeContent}
                      disabled={isAnalyzing}
                      startIcon={isAnalyzing ? <CircularProgress size={20} /> : <AnalyticsIcon />}
                      style={{ marginTop: 16 }}
                    >
                      {isAnalyzing ? 'Analyzing...' : 'Analyze Content'}
                    </Button>
                    {analysis && (
                      <Button
                        fullWidth
                        variant="outlined"
                        onClick={exportAnalysis}
                        startIcon={<DownloadIcon />}
                        style={{ marginTop: 8 }}
                      >
                        Export Results
                      </Button>
                    )}
                  </Paper>
                </Grid>
              </Grid>

              {error && (
                <Alert severity="error" style={{ marginTop: 16 }}>
                  {error}
                </Alert>
              )}

              {analysis && (
                <Box mt={4}>
                  <Typography variant="h5" gutterBottom>
                    Analysis Results
                  </Typography>
                  
                  {renderMetrics()}

                  <Grid container spacing={3} style={{ marginTop: 16 }}>
                    <Grid item xs={12} md={6}>
                      <Paper elevation={2} style={{ padding: 16 }}>
                        <Typography variant="h6" gutterBottom>
                          <CategoryIcon style={{ marginRight: 8, verticalAlign: 'middle' }} />
                          Category & Tags
                        </Typography>
                        {analysis.category && (
                          <Chip
                            label={analysis.category.toUpperCase()}
                            color="primary"
                            style={{ marginRight: 8, marginBottom: 8 }}
                          />
                        )}
                        {analysis.tags.map((tag, index) => (
                          <Chip
                            key={index}
                            label={tag}
                            variant="outlined"
                            style={{ marginRight: 8, marginBottom: 8 }}
                          />
                        ))}
                      </Paper>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Paper elevation={2} style={{ padding: 16 }}>
                        <Typography variant="h6" gutterBottom>
                          <GroupIcon style={{ marginRight: 8, verticalAlign: 'middle' }} />
                          Target Audience
                        </Typography>
                        <List dense>
                          {analysis.targetAudience.map((audience, index) => (
                            <ListItem key={index}>
                              <ListItemText primary={audience} />
                            </ListItem>
                          ))}
                        </List>
                      </Paper>
                    </Grid>
                  </Grid>

                  <Grid container spacing={3} style={{ marginTop: 16 }}>
                    <Grid item xs={12} md={6}>
                      <Paper elevation={2} style={{ padding: 16 }}>
                        <Typography variant="h6" gutterBottom>
                          <SentimentIcon style={{ marginRight: 8, verticalAlign: 'middle' }} />
                          Sentiment Analysis
                        </Typography>
                        {renderSentimentChart()}
                      </Paper>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Paper elevation={2} style={{ padding: 16 }}>
                        <Typography variant="h6" gutterBottom>
                          <LabelIcon style={{ marginRight: 8, verticalAlign: 'middle' }} />
                          Top Keywords
                        </Typography>
                        {renderKeywordsChart()}
                      </Paper>
                    </Grid>
                  </Grid>

                  {analysis.summary && (
                    <Paper elevation={2} style={{ padding: 16, marginTop: 24 }}>
                      <Typography variant="h6" gutterBottom>
                        Summary
                      </Typography>
                      <Typography variant="body1" style={{ whiteSpace: 'pre-line' }}>
                        {analysis.summary}
                      </Typography>
                    </Paper>
                  )}
                </Box>
              )}
            </Box>
          )}

          {tabValue === 1 && (
            <Box mt={3}>
              <Alert severity="info">
                Content comparison feature coming soon! Upload multiple documents to compare their metrics.
              </Alert>
            </Box>
          )}

          {tabValue === 2 && (
            <Box mt={3}>
              <Typography variant="h6" gutterBottom>
                Analysis History
              </Typography>
              {contentHistory.length === 0 ? (
                <Alert severity="info">
                  No analysis history yet. Start analyzing content to build your history.
                </Alert>
              ) : (
                <List>
                  {contentHistory.map((item, index) => (
                    <ListItem key={index} button>
                      <ListItemText
                        primary={item.title}
                        secondary={`Quality: ${(item.qualityScore * 100).toFixed(0)}% | Engagement: ${(item.engagementPrediction * 100).toFixed(0)}%`}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default ContentIntelligence;