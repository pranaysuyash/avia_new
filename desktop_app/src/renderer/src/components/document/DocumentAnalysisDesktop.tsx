import React, { useState, useCallback, useRef } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  FormControl,
  FormControlLabel,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Switch,
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
  Breadcrumbs,
  Link,
  SpeedDial,
  SpeedDialAction,
  SpeedDialIcon,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  CloudUpload,
  Download,
  Refresh,
  Close,
  Description,
  Analytics,
  Language,
  SentimentSatisfied,
  SentimentDissatisfied,
  SentimentNeutral,
  Label,
  ExpandMore,
  FileCopy,
  PictureAsPdf,
  Article,
  TableChart,
  Image as ImageIcon,
  CheckCircle,
  Error,
  Info,
  FolderOpen,
  Save,
  Share,
  Print,
  MoreVert,
  Settings,
  History,
  CompareArrows,
  Insights,
  AutoAwesome,
  NavigateNext,
  Cloud,
  Computer,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { apiClient } from '../../services/api';
import { Line, Bar, Doughnut } from 'react-chartjs-2';

interface DocumentMetadata {
  filename: string;
  file_type: string;
  file_size: number;
  page_count?: number;
  creation_date?: string;
  modification_date?: string;
  author?: string;
  title?: string;
}

interface Entity {
  text: string;
  type: string;
  confidence?: number;
  start?: number;
  end?: number;
}

interface Topic {
  name: string;
  score: number;
  keywords: string[];
}

interface AnalysisConfig {
  enable_ocr: boolean;
  enable_nlp: boolean;
  enable_entity_extraction: boolean;
  enable_summarization: boolean;
  enable_sentiment_analysis: boolean;
  enable_key_phrases: boolean;
  enable_language_detection: boolean;
  enable_table_extraction: boolean;
  enable_image_extraction: boolean;
  max_pages?: number;
  languages: string[];
  custom_entities?: string[];
}

interface AnalysisResults {
  task_id: string;
  status: string;
  metadata?: DocumentMetadata;
  text_content?: string;
  summary?: string;
  entities?: Entity[];
  key_phrases?: string[];
  sentiment?: Record<string, number>;
  language?: string;
  topics?: Topic[];
  tables?: any[];
  images?: any[];
  processing_time?: number;
  timestamp?: string;
  error?: string;
}

interface AnalysisHistory {
  task_id: string;
  filename: string;
  timestamp: string;
  status: string;
}

const DocumentAnalysisDesktop: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [templates, setTemplates] = useState<any[]>([]);
  const [history, setHistory] = useState<AnalysisHistory[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [showComparison, setShowComparison] = useState(false);
  const [comparisonResults, setComparisonResults] = useState<AnalysisResults | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [speedDialOpen, setSpeedDialOpen] = useState(false);
  const [analysisConfig, setAnalysisConfig] = useState<AnalysisConfig>({
    enable_ocr: true,
    enable_nlp: true,
    enable_entity_extraction: true,
    enable_summarization: true,
    enable_sentiment_analysis: true,
    enable_key_phrases: true,
    enable_language_detection: true,
    enable_table_extraction: true,
    enable_image_extraction: true,
    languages: ['en'],
  });

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    loadTemplates();
    loadHistory();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await apiClient.get('/api/v1/document-analysis/templates');
      setTemplates(response.data.templates);
    } catch (err) {
      console.error('Failed to load templates:', err);
    }
  };

  const loadHistory = () => {
    // Load from local storage
    const savedHistory = localStorage.getItem('document_analysis_history');
    if (savedHistory) {
      setHistory(JSON.parse(savedHistory));
    }
  };

  const saveToHistory = (taskId: string, filename: string, status: string) => {
    const newEntry: AnalysisHistory = {
      task_id: taskId,
      filename,
      timestamp: new Date().toISOString(),
      status,
    };
    const updatedHistory = [newEntry, ...history.slice(0, 19)]; // Keep last 20
    setHistory(updatedHistory);
    localStorage.setItem('document_analysis_history', JSON.stringify(updatedHistory));
  };

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      setSelectedFile(file);
      setResults(null);
      setError(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
      'text/plain': ['.txt'],
      'text/html': ['.html'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    multiple: false,
  });

  const handleOpenFile = () => {
    fileInputRef.current?.click();
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      onDrop([file]);
    }
  };

  const analyzeDocument = async () => {
    if (!selectedFile) return;

    try {
      setAnalyzing(true);
      setError(null);

      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('analysis_config', JSON.stringify(analysisConfig));
      formData.append('output_format', 'json');

      const response = await apiClient.post('/api/v1/document-analysis/analyze/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const taskId = response.data.task_id;
      saveToHistory(taskId, selectedFile.name, 'processing');
      pollForResults(taskId);

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Analysis failed');
      setAnalyzing(false);
    }
  };

  const pollForResults = (taskId: string) => {
    pollIntervalRef.current = setInterval(async () => {
      try {
        const response = await apiClient.get(`/api/v1/document-analysis/status/${taskId}`);
        const data = response.data;

        if (data.status === 'completed' && data.result) {
          setResults(data.result);
          setAnalyzing(false);
          saveToHistory(taskId, selectedFile?.name || 'document', 'completed');
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
          }
        } else if (data.status === 'failed') {
          setError(data.message || 'Analysis failed');
          setAnalyzing(false);
          saveToHistory(taskId, selectedFile?.name || 'document', 'failed');
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
          }
        }
      } catch (err) {
        setError('Failed to get analysis status');
        setAnalyzing(false);
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
        }
      }
    }, 1000);
  };

  const loadFromHistory = async (entry: AnalysisHistory) => {
    try {
      const response = await apiClient.get(`/api/v1/document-analysis/status/${entry.task_id}`);
      if (response.data.result) {
        setResults(response.data.result);
        setShowHistory(false);
      }
    } catch (err) {
      setError('Failed to load analysis from history');
    }
  };

  const compareWithDocument = async () => {
    // Implementation for document comparison
    setShowComparison(true);
  };

  const handleConfigChange = (key: keyof AnalysisConfig, value: any) => {
    setAnalysisConfig({ ...analysisConfig, [key]: value });
  };

  const applyTemplate = (templateId: string) => {
    const template = templates.find(t => t.id === templateId);
    if (template) {
      setAnalysisConfig({ ...analysisConfig, ...template.config });
      setSelectedTemplate(templateId);
    }
  };

  const resetAnalysis = () => {
    setSelectedFile(null);
    setResults(null);
    setError(null);
    setAnalyzing(false);
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }
  };

  const downloadReport = async (format: 'json' | 'pdf' | 'html') => {
    if (!results?.task_id) return;

    try {
      const response = await apiClient.get(
        `/api/v1/document-analysis/report/${results.task_id}?format=${format}`
      );
      
      if (format === 'json') {
        const data = JSON.stringify(response.data.report, null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `analysis_${results.task_id}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else if (format === 'html') {
        const blob = new Blob([response.data.content], { type: 'text/html' });
        const url = window.URL.createObjectURL(blob);
        window.open(url, '_blank');
      }
    } catch (err) {
      setError('Failed to download report');
    }
  };

  const printReport = () => {
    window.print();
  };

  const shareResults = async () => {
    if (!results) return;
    
    try {
      await navigator.share({
        title: 'Document Analysis Results',
        text: `Analysis of ${results.metadata?.filename}: ${results.entities?.length || 0} entities found, ${results.key_phrases?.length || 0} key phrases extracted.`,
      });
    } catch (err) {
      // Fallback to copy
      const summary = `Document: ${results.metadata?.filename}\nEntities: ${results.entities?.length || 0}\nKey Phrases: ${results.key_phrases?.length || 0}\nSentiment: ${Object.entries(results.sentiment || {}).map(([k, v]) => `${k}: ${(v * 100).toFixed(1)}%`).join(', ')}`;
      navigator.clipboard.writeText(summary);
    }
  };

  const getSentimentIcon = (sentiment: Record<string, number>) => {
    if (!sentiment) return <SentimentNeutral />;
    
    const max = Object.entries(sentiment).reduce((prev, [key, value]) => 
      value > prev.value ? { key, value } : prev, { key: 'neutral', value: 0 });
    
    switch (max.key) {
      case 'positive':
        return <SentimentSatisfied color="success" />;
      case 'negative':
        return <SentimentDissatisfied color="error" />;
      default:
        return <SentimentNeutral color="action" />;
    }
  };

  const getEntityColor = (type: string): string => {
    const colors: Record<string, string> = {
      person: '#2196F3',
      organization: '#4CAF50',
      location: '#FF9800',
      date: '#9C27B0',
      money: '#F44336',
      skill: '#00BCD4',
      education: '#795548',
      default: '#757575',
    };
    return colors[type.toLowerCase()] || colors.default;
  };

  const getFileIcon = (fileType: string) => {
    if (fileType.includes('pdf')) return <PictureAsPdf color="error" />;
    if (fileType.includes('word')) return <Article color="primary" />;
    if (fileType.includes('excel')) return <TableChart color="success" />;
    return <Description color="action" />;
  };

  const speedDialActions = [
    { icon: <History />, name: 'View History', action: () => setShowHistory(true) },
    { icon: <CompareArrows />, name: 'Compare Documents', action: compareWithDocument },
    { icon: <Cloud />, name: 'Import from Cloud', action: () => {} },
    { icon: <Settings />, name: 'Advanced Settings', action: () => {} },
  ];

  // Chart data for visualization
  const entityChartData = results?.entities ? {
    labels: [...new Set(results.entities.map(e => e.type))],
    datasets: [{
      label: 'Entity Count',
      data: Object.values(
        results.entities.reduce((acc, entity) => {
          acc[entity.type] = (acc[entity.type] || 0) + 1;
          return acc;
        }, {} as Record<string, number>)
      ),
      backgroundColor: [...new Set(results.entities.map(e => e.type))].map(type => getEntityColor(type)),
    }],
  } : null;

  const sentimentChartData = results?.sentiment ? {
    labels: Object.keys(results.sentiment),
    datasets: [{
      label: 'Sentiment Distribution',
      data: Object.values(results.sentiment).map(v => v * 100),
      backgroundColor: ['#4caf50', '#f44336', '#ff9800'],
    }],
  } : null;

  return (
    <Box sx={{ p: 3 }}>
      <input
        ref={fileInputRef}
        type="file"
        style={{ display: 'none' }}
        accept=".pdf,.docx,.doc,.txt,.html,.xlsx,.xls"
        onChange={handleFileSelect}
      />

      <Box sx={{ mb: 3 }}>
        <Breadcrumbs separator={<NavigateNext fontSize="small" />}>
          <Link underline="hover" color="inherit" href="#">
            Home
          </Link>
          <Link underline="hover" color="inherit" href="#">
            Analysis
          </Link>
          <Typography color="text.primary">Document Analysis</Typography>
        </Breadcrumbs>
      </Box>

      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Analytics color="primary" />
        Document Analysis
        <Box sx={{ ml: 'auto' }}>
          <IconButton onClick={(e) => setAnchorEl(e.currentTarget)}>
            <MoreVert />
          </IconButton>
        </Box>
      </Typography>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={() => setAnchorEl(null)}
      >
        <MenuItem onClick={() => { printReport(); setAnchorEl(null); }}>
          <ListItemIcon><Print fontSize="small" /></ListItemIcon>
          <ListItemText>Print Report</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => { shareResults(); setAnchorEl(null); }}>
          <ListItemIcon><Share fontSize="small" /></ListItemIcon>
          <ListItemText>Share Results</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => { setShowHistory(true); setAnchorEl(null); }}>
          <ListItemIcon><History fontSize="small" /></ListItemIcon>
          <ListItemText>View History</ListItemText>
        </MenuItem>
      </Menu>

      <Grid container spacing={3}>
        {/* Upload Section */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6">
                  Upload Document
                </Typography>
                <Button
                  startIcon={<FolderOpen />}
                  onClick={handleOpenFile}
                  variant="outlined"
                  size="small"
                >
                  Browse Files
                </Button>
              </Box>
              
              <Box
                {...getRootProps()}
                sx={{
                  border: '2px dashed',
                  borderColor: isDragActive ? 'primary.main' : 'grey.300',
                  borderRadius: 2,
                  p: 4,
                  textAlign: 'center',
                  cursor: 'pointer',
                  backgroundColor: isDragActive ? 'action.hover' : 'transparent',
                  mb: 2,
                  transition: 'all 0.3s ease',
                }}
              >
                <input {...getInputProps()} />
                <CloudUpload sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
                <Typography>
                  {isDragActive
                    ? 'Drop the document here...'
                    : 'Drag & drop a document here, or click to select'}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Supports: PDF, DOCX, DOC, TXT, HTML, XLSX, XLS (Max 50MB)
                </Typography>
              </Box>

              {selectedFile && (
                <Paper sx={{ p: 2, backgroundColor: 'grey.50' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    {getFileIcon(selectedFile.type)}
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="subtitle2">{selectedFile.name}</Typography>
                      <Typography variant="caption" color="textSecondary">
                        {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                      </Typography>
                    </Box>
                    <IconButton size="small" onClick={resetAnalysis}>
                      <Close />
                    </IconButton>
                  </Box>
                </Paper>
              )}
            </CardContent>
          </Card>

          {/* Templates */}
          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <AutoAwesome color="primary" />
                <Typography variant="h6">
                  Analysis Templates
                </Typography>
              </Box>
              <FormControl fullWidth>
                <InputLabel>Select Template</InputLabel>
                <Select
                  value={selectedTemplate}
                  onChange={(e) => applyTemplate(e.target.value)}
                  label="Select Template"
                >
                  <MenuItem value="">Custom Configuration</MenuItem>
                  {templates.map(template => (
                    <MenuItem key={template.id} value={template.id}>
                      {template.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              {selectedTemplate && (
                <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                  {templates.find(t => t.id === selectedTemplate)?.description}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Configuration Section */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Settings />
                Analysis Configuration
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={analysisConfig.enable_ocr}
                        onChange={(e) => handleConfigChange('enable_ocr', e.target.checked)}
                      />
                    }
                    label="OCR Processing"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={analysisConfig.enable_nlp}
                        onChange={(e) => handleConfigChange('enable_nlp', e.target.checked)}
                      />
                    }
                    label="NLP Analysis"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={analysisConfig.enable_entity_extraction}
                        onChange={(e) => handleConfigChange('enable_entity_extraction', e.target.checked)}
                      />
                    }
                    label="Entity Extraction"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={analysisConfig.enable_summarization}
                        onChange={(e) => handleConfigChange('enable_summarization', e.target.checked)}
                      />
                    }
                    label="Summarization"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={analysisConfig.enable_sentiment_analysis}
                        onChange={(e) => handleConfigChange('enable_sentiment_analysis', e.target.checked)}
                      />
                    }
                    label="Sentiment Analysis"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={analysisConfig.enable_key_phrases}
                        onChange={(e) => handleConfigChange('enable_key_phrases', e.target.checked)}
                      />
                    }
                    label="Key Phrases"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={analysisConfig.enable_table_extraction}
                        onChange={(e) => handleConfigChange('enable_table_extraction', e.target.checked)}
                      />
                    }
                    label="Table Extraction"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={analysisConfig.enable_image_extraction}
                        onChange={(e) => handleConfigChange('enable_image_extraction', e.target.checked)}
                      />
                    }
                    label="Image Extraction"
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Max Pages to Analyze"
                    type="number"
                    value={analysisConfig.max_pages || ''}
                    onChange={(e) => handleConfigChange('max_pages', e.target.value ? parseInt(e.target.value) : null)}
                    helperText="Leave empty to analyze all pages"
                    size="small"
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Custom Entity Types"
                    placeholder="Enter comma-separated entity types"
                    value={analysisConfig.custom_entities?.join(', ') || ''}
                    onChange={(e) => handleConfigChange('custom_entities', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
                    helperText="e.g., Product, Feature, Technology"
                    size="small"
                  />
                </Grid>
              </Grid>

              <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  size="large"
                  fullWidth
                  onClick={analyzeDocument}
                  disabled={!selectedFile || analyzing}
                  startIcon={analyzing ? <CircularProgress size={20} /> : <Analytics />}
                >
                  {analyzing ? 'Analyzing...' : 'Analyze Document'}
                </Button>
                <Button
                  variant="outlined"
                  onClick={resetAnalysis}
                  startIcon={<Refresh />}
                >
                  Reset
                </Button>
              </Box>

              {error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {error}
                </Alert>
              )}

              {analyzing && (
                <Box sx={{ mt: 2 }}>
                  <LinearProgress />
                  <Typography variant="caption" color="textSecondary" align="center" sx={{ mt: 1, display: 'block' }}>
                    Analyzing document... This may take a few moments for large files.
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Results Section */}
        {results && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <CheckCircle color="success" />
                  Analysis Results
                  <Box sx={{ ml: 'auto', display: 'flex', gap: 1 }}>
                    <Button
                      size="small"
                      startIcon={<Download />}
                      onClick={() => downloadReport('json')}
                    >
                      JSON
                    </Button>
                    <Button
                      size="small"
                      startIcon={<Download />}
                      onClick={() => downloadReport('html')}
                    >
                      HTML
                    </Button>
                    <Button
                      size="small"
                      startIcon={<Save />}
                      onClick={() => {}}
                    >
                      Save to Project
                    </Button>
                  </Box>
                </Typography>

                {/* Document Info */}
                {results.metadata && (
                  <Paper sx={{ p: 2, mb: 3, backgroundColor: 'grey.50' }}>
                    <Grid container spacing={2}>
                      <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="caption" color="textSecondary">Filename</Typography>
                        <Typography variant="body2">{results.metadata.filename}</Typography>
                      </Grid>
                      <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="caption" color="textSecondary">Type</Typography>
                        <Typography variant="body2">{results.metadata.file_type}</Typography>
                      </Grid>
                      <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="caption" color="textSecondary">Pages</Typography>
                        <Typography variant="body2">{results.metadata.page_count || 'N/A'}</Typography>
                      </Grid>
                      <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="caption" color="textSecondary">Language</Typography>
                        <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Language fontSize="small" />
                          {results.language || 'Unknown'}
                        </Typography>
                      </Grid>
                    </Grid>
                  </Paper>
                )}

                <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} sx={{ mb: 2 }}>
                  <Tab label="Summary" />
                  <Tab label="Entities" icon={<Badge badgeContent={results.entities?.length || 0} color="primary"><Label /></Badge>} />
                  <Tab label="Key Phrases" icon={<Badge badgeContent={results.key_phrases?.length || 0} color="primary"><Label /></Badge>} />
                  <Tab label="Sentiment" />
                  <Tab label="Topics" />
                  <Tab label="Visualizations" />
                  <Tab label="Full Text" />
                  {results.tables && results.tables.length > 0 && <Tab label="Tables" icon={<Badge badgeContent={results.tables.length} color="primary"><TableChart /></Badge>} />}
                  {results.images && results.images.length > 0 && <Tab label="Images" icon={<Badge badgeContent={results.images.length} color="primary"><ImageIcon /></Badge>} />}
                </Tabs>

                {/* Summary Tab */}
                {tabValue === 0 && (
                  <Box>
                    <Paper sx={{ p: 3, backgroundColor: 'grey.50' }}>
                      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Info color="primary" />
                        Document Summary
                      </Typography>
                      <Typography variant="body1" paragraph>
                        {results.summary || 'No summary available'}
                      </Typography>
                      
                      <Divider sx={{ my: 2 }} />
                      
                      <Grid container spacing={2}>
                        <Grid item xs={12} sm={6} md={3}>
                          <Paper sx={{ p: 2, textAlign: 'center' }}>
                            <Typography variant="h4" color="primary">{results.entities?.length || 0}</Typography>
                            <Typography variant="caption">Entities Found</Typography>
                          </Paper>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                          <Paper sx={{ p: 2, textAlign: 'center' }}>
                            <Typography variant="h4" color="secondary">{results.key_phrases?.length || 0}</Typography>
                            <Typography variant="caption">Key Phrases</Typography>
                          </Paper>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                          <Paper sx={{ p: 2, textAlign: 'center' }}>
                            <Typography variant="h4" color="success.main">{results.topics?.length || 0}</Typography>
                            <Typography variant="caption">Topics</Typography>
                          </Paper>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                          <Paper sx={{ p: 2, textAlign: 'center' }}>
                            <Typography variant="h4" color="info.main">{results.processing_time?.toFixed(1)}s</Typography>
                            <Typography variant="caption">Processing Time</Typography>
                          </Paper>
                        </Grid>
                      </Grid>
                    </Paper>
                  </Box>
                )}

                {/* Entities Tab */}
                {tabValue === 1 && (
                  <Box>
                    {results.entities && results.entities.length > 0 ? (
                      <Box>
                        <Box sx={{ mb: 2, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                          {Object.entries(
                            results.entities.reduce((acc, entity) => {
                              acc[entity.type] = (acc[entity.type] || 0) + 1;
                              return acc;
                            }, {} as Record<string, number>)
                          ).map(([type, count]) => (
                            <Chip
                              key={type}
                              label={`${type}: ${count}`}
                              sx={{
                                backgroundColor: getEntityColor(type),
                                color: 'white',
                              }}
                            />
                          ))}
                        </Box>
                        
                        <TableContainer component={Paper}>
                          <Table>
                            <TableHead>
                              <TableRow>
                                <TableCell>Entity</TableCell>
                                <TableCell>Type</TableCell>
                                <TableCell>Confidence</TableCell>
                                <TableCell>Actions</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {results.entities.map((entity, index) => (
                                <TableRow key={index}>
                                  <TableCell>{entity.text}</TableCell>
                                  <TableCell>
                                    <Chip
                                      label={entity.type}
                                      size="small"
                                      sx={{
                                        backgroundColor: getEntityColor(entity.type),
                                        color: 'white',
                                      }}
                                    />
                                  </TableCell>
                                  <TableCell>
                                    {entity.confidence ? `${(entity.confidence * 100).toFixed(1)}%` : 'N/A'}
                                  </TableCell>
                                  <TableCell>
                                    <IconButton size="small">
                                      <FileCopy fontSize="small" />
                                    </IconButton>
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </Box>
                    ) : (
                      <Typography variant="body2" color="textSecondary" align="center" sx={{ py: 4 }}>
                        No entities found
                      </Typography>
                    )}
                  </Box>
                )}

                {/* Key Phrases Tab */}
                {tabValue === 2 && (
                  <Box>
                    {results.key_phrases && results.key_phrases.length > 0 ? (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {results.key_phrases.map((phrase, index) => (
                          <Chip
                            key={index}
                            label={phrase}
                            variant="outlined"
                            color="primary"
                            onClick={() => navigator.clipboard.writeText(phrase)}
                          />
                        ))}
                      </Box>
                    ) : (
                      <Typography variant="body2" color="textSecondary" align="center" sx={{ py: 4 }}>
                        No key phrases found
                      </Typography>
                    )}
                  </Box>
                )}

                {/* Sentiment Tab */}
                {tabValue === 3 && (
                  <Box>
                    {results.sentiment ? (
                      <Grid container spacing={3}>
                        <Grid item xs={12}>
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 2, mb: 3 }}>
                            {getSentimentIcon(results.sentiment)}
                            <Typography variant="h6">
                              Overall Sentiment
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={12} md={6}>
                          <Paper sx={{ p: 3 }}>
                            {sentimentChartData && (
                              <Doughnut data={sentimentChartData} options={{ maintainAspectRatio: true }} />
                            )}
                          </Paper>
                        </Grid>
                        <Grid item xs={12} md={6}>
                          {Object.entries(results.sentiment).map(([sentiment, score]) => (
                            <Box key={sentiment} sx={{ mb: 2 }}>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                <Typography variant="subtitle1" sx={{ textTransform: 'capitalize' }}>
                                  {sentiment}
                                </Typography>
                                <Typography variant="subtitle1">
                                  {(score * 100).toFixed(1)}%
                                </Typography>
                              </Box>
                              <LinearProgress
                                variant="determinate"
                                value={score * 100}
                                sx={{
                                  height: 10,
                                  borderRadius: 5,
                                  backgroundColor: 'grey.200',
                                  '& .MuiLinearProgress-bar': {
                                    backgroundColor: 
                                      sentiment === 'positive' ? 'success.main' :
                                      sentiment === 'negative' ? 'error.main' : 'warning.main'
                                  }
                                }}
                              />
                            </Box>
                          ))}
                        </Grid>
                      </Grid>
                    ) : (
                      <Typography variant="body2" color="textSecondary" align="center" sx={{ py: 4 }}>
                        No sentiment analysis available
                      </Typography>
                    )}
                  </Box>
                )}

                {/* Topics Tab */}
                {tabValue === 4 && (
                  <Box>
                    {results.topics && results.topics.length > 0 ? (
                      results.topics.map((topic, index) => (
                        <Accordion key={index}>
                          <AccordionSummary expandIcon={<ExpandMore />}>
                            <Typography sx={{ flexGrow: 1 }}>
                              {topic.name}
                            </Typography>
                            <Chip
                              label={`${(topic.score * 100).toFixed(1)}%`}
                              size="small"
                              color="primary"
                            />
                          </AccordionSummary>
                          <AccordionDetails>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                              {topic.keywords.map((keyword, i) => (
                                <Chip key={i} label={keyword} size="small" variant="outlined" />
                              ))}
                            </Box>
                          </AccordionDetails>
                        </Accordion>
                      ))
                    ) : (
                      <Typography variant="body2" color="textSecondary" align="center" sx={{ py: 4 }}>
                        No topics found
                      </Typography>
                    )}
                  </Box>
                )}

                {/* Visualizations Tab */}
                {tabValue === 5 && (
                  <Box>
                    <Grid container spacing={3}>
                      {entityChartData && (
                        <Grid item xs={12} md={6}>
                          <Paper sx={{ p: 3 }}>
                            <Typography variant="h6" gutterBottom>Entity Distribution</Typography>
                            <Bar data={entityChartData} options={{ maintainAspectRatio: true }} />
                          </Paper>
                        </Grid>
                      )}
                      {sentimentChartData && (
                        <Grid item xs={12} md={6}>
                          <Paper sx={{ p: 3 }}>
                            <Typography variant="h6" gutterBottom>Sentiment Analysis</Typography>
                            <Doughnut data={sentimentChartData} options={{ maintainAspectRatio: true }} />
                          </Paper>
                        </Grid>
                      )}
                    </Grid>
                  </Box>
                )}

                {/* Full Text Tab */}
                {tabValue === 6 && (
                  <Box>
                    <Paper sx={{ p: 2, maxHeight: 400, overflow: 'auto', backgroundColor: 'grey.50' }}>
                      <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                        {results.text_content || 'No text content available'}
                      </Typography>
                    </Paper>
                  </Box>
                )}

                {/* Tables Tab */}
                {tabValue === 7 && results.tables && results.tables.length > 0 && (
                  <Box>
                    {results.tables.map((table, index) => (
                      <Accordion key={index}>
                        <AccordionSummary expandIcon={<ExpandMore />}>
                          <Typography>Table {index + 1}</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                          <TableContainer>
                            <Table size="small">
                              <TableBody>
                                {table.rows.map((row: any[], rowIndex: number) => (
                                  <TableRow key={rowIndex}>
                                    {row.map((cell, cellIndex) => (
                                      <TableCell key={cellIndex}>{cell}</TableCell>
                                    ))}
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          </TableContainer>
                        </AccordionDetails>
                      </Accordion>
                    ))}
                  </Box>
                )}

                {/* Images Tab */}
                {tabValue === 8 && results.images && results.images.length > 0 && (
                  <Box>
                    <Grid container spacing={2}>
                      {results.images.map((image, index) => (
                        <Grid item xs={12} sm={6} md={4} key={index}>
                          <Paper sx={{ p: 2 }}>
                            <img
                              src={image.url || image.data}
                              alt={`Extracted image ${index + 1}`}
                              style={{ width: '100%', height: 'auto' }}
                            />
                            <Typography variant="caption" sx={{ mt: 1 }}>
                              Image {index + 1}
                            </Typography>
                          </Paper>
                        </Grid>
                      ))}
                    </Grid>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* Speed Dial */}
      <SpeedDial
        ariaLabel="Quick actions"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
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

      {/* History Dialog */}
      <Dialog
        open={showHistory}
        onClose={() => setShowHistory(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Analysis History
          <IconButton
            onClick={() => setShowHistory(false)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <Close />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <List>
            {history.map((entry, index) => (
              <React.Fragment key={entry.task_id}>
                <ListItem
                  button
                  onClick={() => loadFromHistory(entry)}
                >
                  <ListItemIcon>
                    {entry.status === 'completed' ? <CheckCircle color="success" /> :
                     entry.status === 'failed' ? <Error color="error" /> :
                     <CircularProgress size={20} />}
                  </ListItemIcon>
                  <ListItemText
                    primary={entry.filename}
                    secondary={new Date(entry.timestamp).toLocaleString()}
                  />
                  <ListItemSecondaryAction>
                    <Chip
                      label={entry.status}
                      size="small"
                      color={entry.status === 'completed' ? 'success' : entry.status === 'failed' ? 'error' : 'default'}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                {index < history.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default DocumentAnalysisDesktop;