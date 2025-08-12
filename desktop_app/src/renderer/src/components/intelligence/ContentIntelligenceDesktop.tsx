/**
 * Content Intelligence Component - Electron Desktop
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
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
  Save as SaveIcon,
  FolderOpen as OpenIcon,
  CompareArrows as CompareIcon,
  History as HistoryIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as ChartTooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, WordCloud } from 'recharts';
import { ipcRenderer } from 'electron';

// Desktop-specific styled components
const DesktopCard = styled(Card)(({ theme }) => ({
  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  color: 'white',
  marginBottom: theme.spacing(2),
  boxShadow: '0 8px 32px rgba(102, 126, 234, 0.25)',
}));

const DragDropArea = styled(Paper)(({ theme, isDragging }: any) => ({
  padding: theme.spacing(4),
  textAlign: 'center',
  border: `3px dashed ${isDragging ? theme.palette.primary.main : theme.palette.divider}`,
  backgroundColor: isDragging ? theme.palette.action.hover : theme.palette.background.paper,
  cursor: 'pointer',
  transition: 'all 0.3s',
  minHeight: 200,
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  '&:hover': {
    borderColor: theme.palette.primary.main,
    backgroundColor: theme.palette.action.hover,
  },
}));

const MetricCard = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  textAlign: 'center',
  background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
  borderRadius: theme.spacing(2),
  transition: 'all 0.3s',
  cursor: 'pointer',
  '&:hover': {
    transform: 'translateY(-5px)',
    boxShadow: theme.shadows[12],
  },
}));

const QualityBadge = styled(Badge)(({ theme, quality }: any) => ({
  '& .MuiBadge-badge': {
    backgroundColor: quality > 80 ? '#4caf50' : quality > 60 ? '#ff9800' : '#f44336',
    color: 'white',
    padding: '0 12px',
    height: '28px',
    borderRadius: '14px',
    fontSize: '14px',
    fontWeight: 'bold',
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
  emotions: Record<string, number>;
  qualityScore: number;
  readabilityScore: number;
  engagementPrediction: number;
  viralityScore: number;
  targetAudience: string[];
  summary: string | null;
  recommendations: string[];
  metadata: {
    wordCount: number;
    readingTime: number;
    language: string;
    complexity: string;
  };
}

interface ContentIntelligenceDesktopProps {
  apiEndpoint?: string;
  onAnalysisComplete?: (analysis: ContentAnalysis) => void;
}

const ContentIntelligenceDesktop: React.FC<ContentIntelligenceDesktopProps> = ({
  apiEndpoint = '/api/intelligence/content/analyze',
  onAnalysisComplete,
}) => {
  const [content, setContent] = useState('');
  const [title, setTitle] = useState('');
  const [contentType, setContentType] = useState('transcript');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<ContentAnalysis | null>(null);
  const [contentHistory, setContentHistory] = useState<ContentAnalysis[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [compareMode, setCompareMode] = useState(false);
  const [selectedComparison, setSelectedComparison] = useState<ContentAnalysis[]>([]);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    // Set up IPC listeners for desktop-specific features
    ipcRenderer.on('file-opened', (event, fileContent) => {
      setContent(fileContent);
    });

    ipcRenderer.on('analysis-saved', (event, result) => {
      setSnackbarMessage('Analysis saved successfully');
      setSnackbarOpen(true);
    });

    // Load saved analyses from local storage
    loadSavedAnalyses();

    return () => {
      ipcRenderer.removeAllListeners('file-opened');
      ipcRenderer.removeAllListeners('analysis-saved');
    };
  }, []);

  const loadSavedAnalyses = async () => {
    try {
      const saved = await ipcRenderer.invoke('load-saved-analyses');
      if (saved) {
        setContentHistory(saved);
      }
    } catch (err) {
      console.error('Failed to load saved analyses:', err);
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      const file = files[0];
      const reader = new FileReader();
      reader.onload = (event) => {
        const text = event.target?.result as string;
        setContent(text);
        setTitle(file.name);
      };
      reader.readAsText(file);
    }
  }, []);

  const analyzeContent = useCallback(async () => {
    if (!content.trim()) {
      setError('Please enter content to analyze');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      // Mock analysis for demonstration
      const mockAnalysis: ContentAnalysis = {
        contentId: `content_${Date.now()}`,
        title: title || 'Untitled',
        category: 'technology',
        tags: ['AI', 'machine learning', 'innovation', 'future', 'technology', 'automation'],
        keywords: [
          { keyword: 'artificial intelligence', score: 0.95 },
          { keyword: 'machine learning', score: 0.87 },
          { keyword: 'deep learning', score: 0.76 },
          { keyword: 'neural networks', score: 0.72 },
          { keyword: 'automation', score: 0.68 },
          { keyword: 'data science', score: 0.65 },
        ],
        sentiment: {
          positive: 0.72,
          negative: 0.08,
          neutral: 0.20,
        },
        emotions: {
          joy: 0.65,
          trust: 0.72,
          fear: 0.08,
          surprise: 0.45,
          sadness: 0.05,
          anticipation: 0.78,
        },
        qualityScore: 0.85,
        readabilityScore: 0.78,
        engagementPrediction: 0.82,
        viralityScore: 0.65,
        targetAudience: ['tech professionals', 'students', 'researchers', 'entrepreneurs'],
        summary: '• Discusses latest AI advancements and breakthroughs\n• Explores practical applications in various industries\n• Highlights future possibilities and challenges\n• Addresses ethical considerations',
        recommendations: [
          'Add more concrete examples to increase engagement',
          'Include visual aids to improve comprehension',
          'Consider breaking into smaller sections for better readability',
          'Add call-to-action for higher conversion',
        ],
        metadata: {
          wordCount: 1250,
          readingTime: 5,
          language: 'en',
          complexity: 'intermediate',
        },
      };

      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 2000));

      setAnalysis(mockAnalysis);
      setContentHistory(prev => [...prev, mockAnalysis]);
      
      // Save to local storage
      await ipcRenderer.invoke('save-analysis', mockAnalysis);
      
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

  const openFile = async () => {
    try {
      const result = await ipcRenderer.invoke('open-file-dialog');
      if (result.content) {
        setContent(result.content);
        setTitle(result.filename);
      }
    } catch (err) {
      console.error('Failed to open file:', err);
    }
  };

  const saveAnalysis = async () => {
    if (!analysis) return;

    try {
      await ipcRenderer.invoke('save-analysis-to-file', analysis);
      setSnackbarMessage('Analysis saved to file');
      setSnackbarOpen(true);
    } catch (err) {
      console.error('Failed to save analysis:', err);
    }
  };

  const exportAnalysis = useCallback(() => {
    if (!analysis) return;

    const formats = ['json', 'csv', 'pdf', 'html'];
    // In a real app, this would open a dialog to choose format
    ipcRenderer.invoke('export-analysis', { analysis, format: 'json' });
  }, [analysis]);

  const compareAnalyses = () => {
    setCompareMode(!compareMode);
  };

  const renderMetrics = () => {
    if (!analysis) return null;

    return (
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard elevation={3}>
            <QualityBadge quality={analysis.qualityScore * 100} badgeContent={`${(analysis.qualityScore * 100).toFixed(0)}%`}>
              <AssessmentIcon style={{ fontSize: 48, color: '#667eea' }} />
            </QualityBadge>
            <Typography variant="h6" style={{ marginTop: 12 }}>
              Quality Score
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Overall content quality
            </Typography>
          </MetricCard>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard elevation={3}>
            <CircularProgress
              variant="determinate"
              value={analysis.readabilityScore * 100}
              size={80}
              thickness={4}
              style={{ color: '#764ba2' }}
            />
            <Typography variant="h6" style={{ marginTop: 12 }}>
              Readability
            </Typography>
            <Typography variant="body2">
              {(analysis.readabilityScore * 100).toFixed(0)}%
            </Typography>
          </MetricCard>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard elevation={3}>
            <TrendingUpIcon style={{ fontSize: 48, color: '#f093fb' }} />
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
            <LightbulbIcon style={{ fontSize: 48, color: '#f5576c' }} />
            <Typography variant="h6">
              Viral Potential
            </Typography>
            <LinearProgress
              variant="determinate"
              value={analysis.viralityScore * 100}
              style={{ marginTop: 12, height: 8, borderRadius: 4 }}
            />
          </MetricCard>
        </Grid>
      </Grid>
    );
  };

  const renderAdvancedAnalytics = () => {
    if (!analysis) return null;

    const emotionData = Object.entries(analysis.emotions).map(([emotion, value]) => ({
      emotion,
      value: value * 100,
      fullMark: 100,
    }));

    return (
      <Grid container spacing={3} style={{ marginTop: 16 }}>
        <Grid item xs={12} md={6}>
          <Paper elevation={2} style={{ padding: 16 }}>
            <Typography variant="h6" gutterBottom>
              <SentimentIcon style={{ marginRight: 8, verticalAlign: 'middle' }} />
              Emotion Analysis
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={emotionData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="emotion" />
                <PolarRadiusAxis angle={90} domain={[0, 100]} />
                <Radar name="Emotions" dataKey="value" stroke="#667eea" fill="#667eea" fillOpacity={0.6} />
              </RadarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper elevation={2} style={{ padding: 16 }}>
            <Typography variant="h6" gutterBottom>
              Content Metadata
            </Typography>
            <List>
              <ListItem>
                <ListItemText 
                  primary="Word Count" 
                  secondary={analysis.metadata.wordCount.toLocaleString()} 
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Reading Time" 
                  secondary={`${analysis.metadata.readingTime} minutes`} 
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Language" 
                  secondary={analysis.metadata.language.toUpperCase()} 
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Complexity" 
                  secondary={analysis.metadata.complexity} 
                />
              </ListItem>
            </List>
          </Paper>
        </Grid>
      </Grid>
    );
  };

  const renderRecommendations = () => {
    if (!analysis) return null;

    return (
      <Paper elevation={2} style={{ padding: 16, marginTop: 24 }}>
        <Typography variant="h6" gutterBottom>
          <LightbulbIcon style={{ marginRight: 8, verticalAlign: 'middle' }} />
          Recommendations for Improvement
        </Typography>
        <List>
          {analysis.recommendations.map((rec, index) => (
            <ListItem key={index}>
              <ListItemText primary={rec} />
            </ListItem>
          ))}
        </List>
      </Paper>
    );
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <DesktopCard>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h4" gutterBottom>
                <PsychologyIcon style={{ marginRight: 8, verticalAlign: 'middle' }} />
                Content Intelligence Desktop
              </Typography>
              <Typography variant="body1">
                Advanced NLP and ML analysis for desktop with enhanced features
              </Typography>
            </Box>
            <Box>
              <Tooltip title="Open File">
                <IconButton color="inherit" onClick={openFile}>
                  <OpenIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Save Analysis">
                <IconButton color="inherit" onClick={saveAnalysis} disabled={!analysis}>
                  <SaveIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Compare Analyses">
                <IconButton color="inherit" onClick={compareAnalyses}>
                  <CompareIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="View History">
                <IconButton color="inherit" onClick={() => setTabValue(2)}>
                  <HistoryIcon />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>
        </CardContent>
      </DesktopCard>

      <Card sx={{ flex: 1, overflow: 'auto' }}>
        <CardContent>
          <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
            <Tab label="Analyze" icon={<AnalyticsIcon />} />
            <Tab label="Compare" icon={<CompareIcon />} />
            <Tab label="History" icon={<HistoryIcon />} />
            <Tab label="Settings" icon={<AssessmentIcon />} />
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
                  
                  <DragDropArea
                    isDragging={isDragging}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                  >
                    {content ? (
                      <TextField
                        fullWidth
                        multiline
                        rows={12}
                        label="Content to Analyze"
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                        variant="outlined"
                        margin="normal"
                      />
                    ) : (
                      <>
                        <CloudUploadIcon style={{ fontSize: 64, color: '#999' }} />
                        <Typography variant="h6" style={{ marginTop: 16 }}>
                          Drag & Drop your file here
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          or click to browse files
                        </Typography>
                        <Button
                          variant="outlined"
                          startIcon={<OpenIcon />}
                          onClick={openFile}
                          style={{ marginTop: 16 }}
                        >
                          Open File
                        </Button>
                      </>
                    )}
                  </DragDropArea>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <Paper elevation={2} style={{ padding: 16 }}>
                    <Typography variant="h6" gutterBottom>
                      Analysis Options
                    </Typography>
                    
                    <FormControl fullWidth margin="normal">
                      <InputLabel>Content Type</InputLabel>
                      <Select
                        value={contentType}
                        onChange={(e) => setContentType(e.target.value)}
                        label="Content Type"
                      >
                        <MenuItem value="transcript">Transcript</MenuItem>
                        <MenuItem value="article">Article</MenuItem>
                        <MenuItem value="social">Social Media</MenuItem>
                        <MenuItem value="email">Email</MenuItem>
                        <MenuItem value="document">Document</MenuItem>
                      </Select>
                    </FormControl>
                    
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
                      <>
                        <Button
                          fullWidth
                          variant="outlined"
                          onClick={exportAnalysis}
                          startIcon={<DownloadIcon />}
                          style={{ marginTop: 8 }}
                        >
                          Export Results
                        </Button>
                        <Button
                          fullWidth
                          variant="outlined"
                          onClick={() => setSaveDialogOpen(true)}
                          startIcon={<SaveIcon />}
                          style={{ marginTop: 8 }}
                        >
                          Save Analysis
                        </Button>
                      </>
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
                  {renderAdvancedAnalytics()}

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
                            size="large"
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
                              <Avatar style={{ marginRight: 8 }}>
                                <GroupIcon />
                              </Avatar>
                              <ListItemText primary={audience} />
                            </ListItem>
                          ))}
                        </List>
                      </Paper>
                    </Grid>
                  </Grid>

                  {renderRecommendations()}

                  {analysis.summary && (
                    <Paper elevation={2} style={{ padding: 16, marginTop: 24 }}>
                      <Typography variant="h6" gutterBottom>
                        Executive Summary
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
                Select multiple analyses from history to compare their metrics side by side
              </Alert>
              {/* Comparison view would go here */}
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
                <Grid container spacing={2}>
                  {contentHistory.map((item, index) => (
                    <Grid item xs={12} md={6} key={index}>
                      <Card>
                        <CardContent>
                          <Typography variant="h6">{item.title}</Typography>
                          <Typography variant="body2" color="textSecondary">
                            Quality: {(item.qualityScore * 100).toFixed(0)}% | 
                            Engagement: {(item.engagementPrediction * 100).toFixed(0)}%
                          </Typography>
                          <Button
                            size="small"
                            onClick={() => setAnalysis(item)}
                            style={{ marginTop: 8 }}
                          >
                            View Details
                          </Button>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              )}
            </Box>
          )}

          {tabValue === 3 && (
            <Box mt={3}>
              <Typography variant="h6" gutterBottom>
                Analysis Settings
              </Typography>
              <Paper elevation={2} style={{ padding: 16 }}>
                <Typography variant="subtitle1">Configure analysis parameters</Typography>
                {/* Settings configuration would go here */}
              </Paper>
            </Box>
          )}
        </CardContent>
      </Card>

      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMessage}
      />
    </Box>
  );
};

export default ContentIntelligenceDesktop;