import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  TextField,
  Typography,
  Alert,
  Chip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Tab,
  Tabs,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
  Badge,
  Menu,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Switch,
  FormControlLabel,
  SpeedDial,
  SpeedDialAction,
  SpeedDialIcon,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Checkbox,
  Grid,
  Stepper,
  Step,
  StepLabel,
  StepContent,
} from '@mui/material';
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
  Error,
  Info,
  Close,
  ExpandMore,
  PlayArrow,
  Pause,
  VolumeUp,
  Download,
  Share,
  ExternalLink,
  Star,
  TrendingUp,
  DollarSign,
  BarChart,
  Timeline,
  FileCopy,
  CloudDownload,
  ViewList,
  ViewModule,
  Tune,
  LocalOffer,
  Assessment,
  CompareArrows,
  History,
  Insights,
  AutoAwesome,
  ColorLens,
  Movie,
  Image as ImageIcon,
  Map,
  People,
  Computer,
  Nature,
  Architecture,
  Business
} from '@mui/icons-material';
import { apiClient } from '../../services/api';
import { Line, Bar, Doughnut, Pie } from 'react-chartjs-2';

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

const SmartBRollDesktop: React.FC = () => {
  const [transcriptText, setTranscriptText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<BRollAnalysisResponse | null>(null);
  const [selectedSuggestions, setSelectedSuggestions] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [showSettings, setShowSettings] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [previewSuggestion, setPreviewSuggestion] = useState<BRollSuggestion | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterPriority, setFilterPriority] = useState('all');
  const [filterContentType, setFilterContentType] = useState('all');
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');
  const [speedDialOpen, setSpeedDialOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [shoppingListData, setShoppingListData] = useState<any>(null);
  const [showShoppingList, setShowShoppingList] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  
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
    setCurrentStep(0);

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
          title: 'Desktop Video Analysis',
          created_at: new Date().toISOString()
        }
      };

      setCurrentStep(1); // Analyzing context
      await new Promise(resolve => setTimeout(resolve, 1000));

      setCurrentStep(2); // Generating suggestions
      const response = await apiClient.post('/api/v1/smart-broll/analyze', requestBody);

      setCurrentStep(3); // Processing results
      await new Promise(resolve => setTimeout(resolve, 500));

      setAnalysisResult(response.data);
      setCurrentStep(4); // Complete
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Analysis failed');
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

  const selectAll = () => {
    if (!analysisResult) return;
    const allIds = new Set(analysisResult.suggestions.map(s => s.suggestion_id));
    setSelectedSuggestions(allIds);
  };

  const clearSelection = () => {
    setSelectedSuggestions(new Set());
  };

  const generateShoppingList = async () => {
    if (!analysisResult) return;

    const selectedSuggestionObjs = analysisResult.suggestions.filter(s => 
      selectedSuggestions.has(s.suggestion_id)
    );

    try {
      const response = await apiClient.post('/api/v1/smart-broll/generate-shopping-list', {
        suggestions: selectedSuggestionObjs,
        budget: settings.budget_tier === 'free' ? 0 : 1000,
        preferred_sources: ['pexels', 'unsplash', 'shutterstock']
      });

      setShoppingListData(response.data);
      setShowShoppingList(true);
    } catch (err) {
      setError('Failed to generate shopping list');
    }
  };

  const searchStockLibraries = async (suggestion: BRollSuggestion) => {
    try {
      const response = await apiClient.post('/api/v1/smart-broll/search-stock', {
        query: suggestion.search_query,
        content_type: suggestion.content_type,
        max_results: 20
      });

      console.log('Stock search results:', response.data);
      // Could open results in new window or modal
    } catch (err) {
      console.error('Search failed:', err);
    }
  };

  const exportResults = () => {
    if (!analysisResult) return;

    const exportData = {
      analysis: analysisResult,
      selected_suggestions: Array.from(selectedSuggestions),
      export_timestamp: new Date().toISOString()
    };

    const dataStr = JSON.stringify(exportData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    const exportFileDefaultName = `broll-suggestions-${Date.now()}.json`;

    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const shareResults = async () => {
    if (!analysisResult) return;
    
    const summary = `Smart B-Roll Analysis Results:
• ${analysisResult.suggestions.length} suggestions generated
• ${analysisResult.summary.coverage_percentage.toFixed(1)}% video coverage
• Enhancement score: ${analysisResult.summary.estimated_enhancement_score.toFixed(0)}%
${analysisResult.estimated_cost ? `• Estimated cost: $${analysisResult.estimated_cost.total}` : ''}`;

    try {
      if (navigator.share) {
        await navigator.share({
          title: 'B-Roll Analysis Results',
          text: summary
        });
      } else {
        await navigator.clipboard.writeText(summary);
        setError('Results copied to clipboard!');
        setTimeout(() => setError(null), 3000);
      }
    } catch (err) {
      console.error('Share failed:', err);
    }
  };

  const getPriorityColor = (priority: string) => {
    const colors = {
      critical: 'error',
      high: 'warning',
      medium: 'info',
      low: 'default'
    };
    return colors[priority as keyof typeof colors] || 'default';
  };

  const getContentTypeIcon = (contentType: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      stock_video: <Movie color="primary" />,
      stock_image: <ImageIcon color="secondary" />,
      animation: <AutoAwesome color="success" />,
      infographic: <BarChart color="info" />,
      map: <Map color="warning" />,
      chart: <Assessment color="primary" />,
      people: <People color="secondary" />,
      technology: <Computer color="info" />,
      nature: <Nature color="success" />,
      architecture: <Architecture color="warning" />,
      business: <Business color="primary" />
    };
    return iconMap[contentType] || <Video color="action" />;
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
    const matchesContentType = filterContentType === 'all' || suggestion.content_type === filterContentType;
    
    return matchesSearch && matchesPriority && matchesContentType;
  }) || [];

  // Chart data for visualizations
  const priorityChartData = analysisResult?.summary.priority_breakdown ? {
    labels: Object.keys(analysisResult.summary.priority_breakdown),
    datasets: [{
      label: 'Priority Distribution',
      data: Object.values(analysisResult.summary.priority_breakdown),
      backgroundColor: ['#ef4444', '#f97316', '#eab308', '#6b7280'],
      borderWidth: 2,
    }],
  } : null;

  const contentTypeChartData = analysisResult?.summary.content_type_distribution ? {
    labels: Object.keys(analysisResult.summary.content_type_distribution),
    datasets: [{
      label: 'Content Type Distribution',
      data: Object.values(analysisResult.summary.content_type_distribution),
      backgroundColor: [
        '#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', 
        '#ef4444', '#06b6d4', '#8b5cf6', '#84cc16'
      ],
      borderWidth: 2,
    }],
  } : null;

  const speedDialActions = [
    { icon: <Search />, name: 'Search Stock', action: () => {} },
    { icon: <Download />, name: 'Export Results', action: exportResults },
    { icon: <Share />, name: 'Share Results', action: shareResults },
    { icon: <History />, name: 'View History', action: () => {} },
    { icon: <CompareArrows />, name: 'Compare', action: () => {} },
  ];

  const analysisSteps = [
    'Input Processing',
    'Context Analysis', 
    'Generating Suggestions',
    'Processing Results',
    'Complete'
  ];

  return (
    <Box sx={{ p: 3, maxWidth: '100%', overflow: 'hidden' }}>
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Lightbulb sx={{ fontSize: 28, color: 'primary.main' }} />
            <Typography variant="h4" fontWeight="bold">Smart B-Roll Suggestions</Typography>
            {analysisResult && (
              <Chip 
                label={`${analysisResult.suggestions.length} suggestions`} 
                color="primary" 
                size="small"
              />
            )}
          </Box>
          
          <Box sx={{ display: 'flex', gap: 1 }}>
            <IconButton onClick={(e) => setAnchorEl(e.currentTarget)}>
              <Settings />
            </IconButton>
            <Button
              variant="outlined"
              startIcon={<ViewList />}
              onClick={() => setViewMode(viewMode === 'list' ? 'grid' : 'list')}
            >
              {viewMode === 'list' ? 'Grid View' : 'List View'}
            </Button>
          </Box>
        </Box>

        {/* Quick Stats */}
        {analysisResult && (
          <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <Paper sx={{ p: 2, minWidth: 120, textAlign: 'center' }}>
              <Typography variant="h6" color="primary">{analysisResult.summary.estimated_enhancement_score.toFixed(0)}%</Typography>
              <Typography variant="caption">Enhancement Score</Typography>
            </Paper>
            <Paper sx={{ p: 2, minWidth: 120, textAlign: 'center' }}>
              <Typography variant="h6" color="success.main">{analysisResult.summary.coverage_percentage.toFixed(0)}%</Typography>
              <Typography variant="caption">Coverage</Typography>
            </Paper>
            {analysisResult.estimated_cost && (
              <Paper sx={{ p: 2, minWidth: 120, textAlign: 'center' }}>
                <Typography variant="h6" color="warning.main">${analysisResult.estimated_cost.total}</Typography>
                <Typography variant="caption">Est. Cost</Typography>
              </Paper>
            )}
            <Paper sx={{ p: 2, minWidth: 120, textAlign: 'center' }}>
              <Typography variant="h6">{selectedSuggestions.size}</Typography>
              <Typography variant="caption">Selected</Typography>
            </Paper>
          </Box>
        )}
      </Box>

      <Grid container spacing={3}>
        {/* Input Panel */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: 'fit-content' }}>
            <CardHeader 
              title={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <BookOpen />
                  <Typography variant="h6">Transcript Input</Typography>
                </Box>
              }
            />
            <CardContent>
              <TextField
                fullWidth
                multiline
                rows={12}
                placeholder="Paste your video transcript here..."
                value={transcriptText}
                onChange={(e) => setTranscriptText(e.target.value)}
                variant="outlined"
                sx={{ mb: 2 }}
              />

              {isAnalyzing && (
                <Box sx={{ mb: 2 }}>
                  <Stepper activeStep={currentStep} orientation="vertical">
                    {analysisSteps.map((label, index) => (
                      <Step key={label}>
                        <StepLabel>{label}</StepLabel>
                      </Step>
                    ))}
                  </Stepper>
                </Box>
              )}

              <Button
                fullWidth
                size="large"
                variant="contained"
                startIcon={isAnalyzing ? <RefreshCw className="animate-spin" /> : <Target />}
                onClick={analyzeTranscript}
                disabled={!transcriptText.trim() || isAnalyzing}
                sx={{ mb: 2 }}
              >
                {isAnalyzing ? 'Analyzing...' : 'Generate B-Roll Suggestions'}
              </Button>

              {selectedSuggestions.size > 0 && (
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button
                    variant="outlined"
                    startIcon={<ShoppingCart />}
                    onClick={generateShoppingList}
                    fullWidth
                  >
                    Shopping List ({selectedSuggestions.size})
                  </Button>
                </Box>
              )}

              {error && (
                <Alert severity={error.includes('copied') ? 'success' : 'error'} sx={{ mt: 2 }}>
                  {error}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Results Panel */}
        <Grid item xs={12} md={8}>
          <Card sx={{ height: 'calc(100vh - 200px)', display: 'flex', flexDirection: 'column' }}>
            <CardHeader 
              title={
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Insights />
                    <Typography variant="h6">Analysis Results</Typography>
                  </Box>
                  {analysisResult && selectedSuggestions.size > 0 && (
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Button size="small" onClick={selectAll}>Select All</Button>
                      <Button size="small" onClick={clearSelection}>Clear</Button>
                    </Box>
                  )}
                </Box>
              }
            />
            <CardContent sx={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
              {!analysisResult && !isAnalyzing ? (
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', flex: 1, opacity: 0.5 }}>
                  <Video sx={{ fontSize: 80, mb: 2 }} />
                  <Typography variant="h6" color="text.secondary">
                    Enter your transcript to generate smart B-roll suggestions
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1, maxWidth: 400, textAlign: 'center' }}>
                    Our AI will analyze your content and suggest the perfect B-roll footage to enhance your video
                  </Typography>
                </Box>
              ) : analysisResult ? (
                <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                  <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} sx={{ borderBottom: 1, borderColor: 'divider' }}>
                    <Tab label="Suggestions" />
                    <Tab label="Timeline" />
                    <Tab label="Analytics" />
                    <Tab label="Templates" />
                  </Tabs>

                  <Box sx={{ flex: 1, overflow: 'auto', mt: 2 }}>
                    {/* Suggestions Tab */}
                    {tabValue === 0 && (
                      <Box>
                        {/* Filters */}
                        <Box sx={{ display: 'flex', gap: 2, mb: 3, alignItems: 'center', flexWrap: 'wrap' }}>
                          <TextField
                            size="small"
                            placeholder="Search suggestions..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            InputProps={{
                              startAdornment: <Search sx={{ mr: 1, opacity: 0.5 }} />
                            }}
                            sx={{ minWidth: 200 }}
                          />
                          
                          <FormControl size="small" sx={{ minWidth: 120 }}>
                            <InputLabel>Priority</InputLabel>
                            <Select
                              value={filterPriority}
                              onChange={(e) => setFilterPriority(e.target.value)}
                              label="Priority"
                            >
                              <MenuItem value="all">All Priority</MenuItem>
                              <MenuItem value="critical">Critical</MenuItem>
                              <MenuItem value="high">High</MenuItem>
                              <MenuItem value="medium">Medium</MenuItem>
                              <MenuItem value="low">Low</MenuItem>
                            </Select>
                          </FormControl>

                          <FormControl size="small" sx={{ minWidth: 140 }}>
                            <InputLabel>Content Type</InputLabel>
                            <Select
                              value={filterContentType}
                              onChange={(e) => setFilterContentType(e.target.value)}
                              label="Content Type"
                            >
                              <MenuItem value="all">All Types</MenuItem>
                              <MenuItem value="stock_video">Stock Video</MenuItem>
                              <MenuItem value="stock_image">Stock Image</MenuItem>
                              <MenuItem value="animation">Animation</MenuItem>
                              <MenuItem value="infographic">Infographic</MenuItem>
                            </Select>
                          </FormControl>
                        </Box>

                        {/* Suggestions List */}
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                          {filteredSuggestions.map((suggestion) => (
                            <Paper 
                              key={suggestion.suggestion_id} 
                              sx={{ 
                                p: 2, 
                                border: selectedSuggestions.has(suggestion.suggestion_id) ? 2 : 1,
                                borderColor: selectedSuggestions.has(suggestion.suggestion_id) ? 'primary.main' : 'divider',
                                bgcolor: selectedSuggestions.has(suggestion.suggestion_id) ? 'primary.50' : 'background.paper'
                              }}
                            >
                              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                                <Checkbox
                                  checked={selectedSuggestions.has(suggestion.suggestion_id)}
                                  onChange={() => toggleSuggestion(suggestion.suggestion_id)}
                                />
                                
                                <Box sx={{ flex: 1 }}>
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                                    {getContentTypeIcon(suggestion.content_type)}
                                    <Chip 
                                      label={suggestion.priority} 
                                      color={getPriorityColor(suggestion.priority) as any}
                                      size="small" 
                                    />
                                    <Typography variant="caption" color="text.secondary">
                                      {formatTime(suggestion.timestamp_start)} - {formatTime(suggestion.timestamp_end)}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                      {suggestion.duration.toFixed(1)}s
                                    </Typography>
                                  </Box>
                                  
                                  <Typography variant="h6" gutterBottom>
                                    {suggestion.description}
                                  </Typography>
                                  
                                  <Typography variant="body2" color="text.secondary" paragraph>
                                    {suggestion.rationale}
                                  </Typography>
                                  
                                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 1 }}>
                                    {suggestion.keywords.map((keyword, idx) => (
                                      <Chip key={idx} label={keyword} size="small" variant="outlined" />
                                    ))}
                                  </Box>
                                  
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 1 }}>
                                    <Typography variant="caption">
                                      Confidence: {(suggestion.confidence * 100).toFixed(0)}%
                                    </Typography>
                                    {suggestion.mood && (
                                      <Typography variant="caption">
                                        Mood: {suggestion.mood}
                                      </Typography>
                                    )}
                                    {suggestion.transition_type && (
                                      <Typography variant="caption">
                                        Transition: {suggestion.transition_type}
                                      </Typography>
                                    )}
                                  </Box>
                                </Box>
                                
                                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                                  <Button
                                    size="small"
                                    startIcon={<Search />}
                                    onClick={() => searchStockLibraries(suggestion)}
                                  >
                                    Search
                                  </Button>
                                  <Button
                                    size="small"
                                    startIcon={<Eye />}
                                    onClick={() => {
                                      setPreviewSuggestion(suggestion);
                                      setShowPreview(true);
                                    }}
                                  >
                                    Preview
                                  </Button>
                                </Box>
                              </Box>
                            </Paper>
                          ))}
                        </Box>
                      </Box>
                    )}

                    {/* Timeline Tab */}
                    {tabValue === 1 && (
                      <Box>
                        <Typography variant="h6" gutterBottom>Video Timeline</Typography>
                        <Box sx={{ position: 'relative', height: 60, bgcolor: 'grey.100', borderRadius: 1, mb: 3 }}>
                          {analysisResult.timeline.map((item, idx) => (
                            <Box
                              key={idx}
                              sx={{
                                position: 'absolute',
                                top: 8,
                                height: 44,
                                borderRadius: 1,
                                bgcolor: 
                                  item.priority === 'critical' ? 'error.main' :
                                  item.priority === 'high' ? 'warning.main' :
                                  item.priority === 'medium' ? 'info.main' :
                                  'grey.400',
                                left: `${(item.start / 100) * 100}%`,
                                width: `${((item.end - item.start) / 100) * 100}%`,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                color: 'white',
                                fontSize: '0.75rem',
                                overflow: 'hidden'
                              }}
                            >
                              {item.label}
                            </Box>
                          ))}
                        </Box>
                        
                        <Grid container spacing={2}>
                          <Grid item xs={6} md={3}>
                            <Paper sx={{ p: 2, textAlign: 'center' }}>
                              <Typography variant="h4" color="error.main">
                                {analysisResult.summary.priority_breakdown.critical || 0}
                              </Typography>
                              <Typography variant="caption">Critical</Typography>
                            </Paper>
                          </Grid>
                          <Grid item xs={6} md={3}>
                            <Paper sx={{ p: 2, textAlign: 'center' }}>
                              <Typography variant="h4" color="warning.main">
                                {analysisResult.summary.priority_breakdown.high || 0}
                              </Typography>
                              <Typography variant="caption">High</Typography>
                            </Paper>
                          </Grid>
                          <Grid item xs={6} md={3}>
                            <Paper sx={{ p: 2, textAlign: 'center' }}>
                              <Typography variant="h4" color="info.main">
                                {analysisResult.summary.priority_breakdown.medium || 0}
                              </Typography>
                              <Typography variant="caption">Medium</Typography>
                            </Paper>
                          </Grid>
                          <Grid item xs={6} md={3}>
                            <Paper sx={{ p: 2, textAlign: 'center' }}>
                              <Typography variant="h4" color="grey.600">
                                {analysisResult.summary.priority_breakdown.low || 0}
                              </Typography>
                              <Typography variant="caption">Low</Typography>
                            </Paper>
                          </Grid>
                        </Grid>
                      </Box>
                    )}

                    {/* Analytics Tab */}
                    {tabValue === 2 && (
                      <Grid container spacing={3}>
                        {priorityChartData && (
                          <Grid item xs={12} md={6}>
                            <Paper sx={{ p: 3 }}>
                              <Typography variant="h6" gutterBottom>Priority Distribution</Typography>
                              <Doughnut data={priorityChartData} options={{ maintainAspectRatio: true }} />
                            </Paper>
                          </Grid>
                        )}
                        
                        {contentTypeChartData && (
                          <Grid item xs={12} md={6}>
                            <Paper sx={{ p: 3 }}>
                              <Typography variant="h6" gutterBottom>Content Type Distribution</Typography>
                              <Pie data={contentTypeChartData} options={{ maintainAspectRatio: true }} />
                            </Paper>
                          </Grid>
                        )}

                        <Grid item xs={12}>
                          <Paper sx={{ p: 3 }}>
                            <Typography variant="h6" gutterBottom>Key Moments</Typography>
                            <List>
                              {analysisResult.summary.key_moments.map((moment, idx) => (
                                <ListItem key={idx}>
                                  <ListItemIcon>
                                    <Star color="primary" />
                                  </ListItemIcon>
                                  <ListItemText
                                    primary={moment.description}
                                    secondary={`${formatTime(moment.timestamp)} • ${moment.duration}s • ${moment.type}`}
                                  />
                                </ListItem>
                              ))}
                            </List>
                          </Paper>
                        </Grid>
                      </Grid>
                    )}

                    {/* Templates Tab */}
                    {tabValue === 3 && (
                      <Box>
                        <Typography variant="h6" gutterBottom>B-Roll Templates</Typography>
                        <Grid container spacing={2}>
                          {['Documentary Style', 'Educational Content', 'Corporate Video', 'Social Media'].map((template) => (
                            <Grid item xs={12} sm={6} key={template}>
                              <Paper sx={{ p: 3, textAlign: 'center' }}>
                                <AutoAwesome sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                                <Typography variant="h6" gutterBottom>{template}</Typography>
                                <Typography variant="body2" color="text.secondary" paragraph>
                                  Pre-configured B-roll suggestions optimized for {template.toLowerCase()}
                                </Typography>
                                <Button variant="outlined" fullWidth>Apply Template</Button>
                              </Paper>
                            </Grid>
                          ))}
                        </Grid>
                      </Box>
                    )}
                  </Box>
                </Box>
              ) : (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flex: 1 }}>
                  <LinearProgress sx={{ width: '50%' }} />
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Settings Dialog */}
      <Dialog open={showSettings} onClose={() => setShowSettings(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Analysis Settings</DialogTitle>
        <DialogContent>
          <Grid container spacing={3} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Suggestion Density</InputLabel>
                <Select
                  value={settings.suggestion_density}
                  onChange={(e) => setSettings({...settings, suggestion_density: e.target.value as any})}
                  label="Suggestion Density"
                >
                  <MenuItem value="low">Low</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Budget Tier</InputLabel>
                <Select
                  value={settings.budget_tier || 'budget'}
                  onChange={(e) => setSettings({...settings, budget_tier: e.target.value as any})}
                  label="Budget Tier"
                >
                  <MenuItem value="free">Free Stock Only</MenuItem>
                  <MenuItem value="budget">Budget ($5-20 per clip)</MenuItem>
                  <MenuItem value="premium">Premium ($20-50 per clip)</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            {Object.entries({
              enable_context_analysis: 'Context Analysis',
              enable_emotion_detection: 'Emotion Detection',
              enable_topic_modeling: 'Topic Modeling',
              enable_visual_metaphors: 'Visual Metaphors',
              enable_pacing_analysis: 'Pacing Analysis',
            }).map(([key, label]) => (
              <Grid item xs={12} sm={6} key={key}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings[key as keyof AnalysisSettings] as boolean}
                      onChange={(e) => setSettings(prev => ({ 
                        ...prev, 
                        [key]: e.target.checked 
                      }))}
                    />
                  }
                  label={label}
                />
              </Grid>
            ))}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSettings(false)}>Cancel</Button>
          <Button onClick={() => setShowSettings(false)} variant="contained">Save Settings</Button>
        </DialogActions>
      </Dialog>

      {/* Preview Dialog */}
      {previewSuggestion && (
        <Dialog open={showPreview} onClose={() => setShowPreview(false)} maxWidth="sm" fullWidth>
          <DialogTitle>B-Roll Preview</DialogTitle>
          <DialogContent>
            <Typography variant="h6" gutterBottom>{previewSuggestion.description}</Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              {previewSuggestion.rationale}
            </Typography>
            <Typography variant="subtitle2" gutterBottom>Search Query:</Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', bgcolor: 'grey.100', p: 1, borderRadius: 1, mb: 2 }}>
              "{previewSuggestion.search_query}"
            </Typography>
            <Typography variant="subtitle2" gutterBottom>Keywords:</Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
              {previewSuggestion.keywords.map((keyword, idx) => (
                <Chip key={idx} label={keyword} size="small" />
              ))}
            </Box>
            <Typography variant="subtitle2" gutterBottom>Details:</Typography>
            <Typography variant="body2">
              Duration: {previewSuggestion.duration.toFixed(1)}s<br/>
              Confidence: {(previewSuggestion.confidence * 100).toFixed(0)}%<br/>
              {previewSuggestion.mood && `Mood: ${previewSuggestion.mood}`}<br/>
              {previewSuggestion.transition_type && `Transition: ${previewSuggestion.transition_type}`}
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowPreview(false)}>Close</Button>
            <Button
              startIcon={<ExternalLink />}
              onClick={() => searchStockLibraries(previewSuggestion)}
              variant="contained"
            >
              Search Stock Libraries
            </Button>
          </DialogActions>
        </Dialog>
      )}

      {/* Shopping List Dialog */}
      {shoppingListData && (
        <Dialog 
          open={showShoppingList} 
          onClose={() => setShowShoppingList(false)} 
          maxWidth="md" 
          fullWidth
        >
          <DialogTitle>B-Roll Shopping List</DialogTitle>
          <DialogContent>
            <Typography variant="body1" gutterBottom>
              Generated shopping list for {shoppingListData.total_items} items
            </Typography>
            <Typography variant="h6" color="primary" gutterBottom>
              Estimated Total: ${shoppingListData.estimated_total_cost}
            </Typography>
            
            <TableContainer component={Paper} sx={{ mt: 2 }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Content</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Priority</TableCell>
                    <TableCell>Duration</TableCell>
                    <TableCell align="right">Cost</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {shoppingListData.shopping_list?.map((item: any, index: number) => (
                    <TableRow key={index}>
                      <TableCell>{item.search_query}</TableCell>
                      <TableCell>{item.content_type}</TableCell>
                      <TableCell>
                        <Chip label={item.priority} size="small" color={getPriorityColor(item.priority) as any} />
                      </TableCell>
                      <TableCell>{item.duration.toFixed(1)}s</TableCell>
                      <TableCell align="right">${item.estimated_cost}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowShoppingList(false)}>Close</Button>
            <Button startIcon={<Download />} variant="contained">
              Export List
            </Button>
          </DialogActions>
        </Dialog>
      )}

      {/* Speed Dial */}
      <SpeedDial
        ariaLabel="Quick actions"
        sx={{ position: 'fixed', bottom: 24, right: 24 }}
        icon={<SpeedDialIcon />}
        onClose={() => setSpeedDialOpen(false)}
        onOpen={() => setSpeedDialOpen(true)}
        open={speedDialOpen}
      >
        {speedDialActions.map((action) => (
          <SpeedDialAction
            key={action.name}
            icon={action.icon}
            tooltipTitle={action.name}
            onClick={() => {
              action.action();
              setSpeedDialOpen(false);
            }}
          />
        ))}
      </SpeedDial>

      {/* Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={() => setAnchorEl(null)}
      >
        <MenuItem onClick={() => { setShowSettings(true); setAnchorEl(null); }}>
          <ListItemIcon><Settings fontSize="small" /></ListItemIcon>
          <ListItemText>Settings</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => { exportResults(); setAnchorEl(null); }}>
          <ListItemIcon><Download fontSize="small" /></ListItemIcon>
          <ListItemText>Export Results</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => { shareResults(); setAnchorEl(null); }}>
          <ListItemIcon><Share fontSize="small" /></ListItemIcon>
          <ListItemText>Share Results</ListItemText>
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default SmartBRollDesktop;