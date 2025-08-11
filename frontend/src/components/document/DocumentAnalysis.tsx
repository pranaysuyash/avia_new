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
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
  Badge,
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
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import apiService from '../../services/api';

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
  max_pages?: number;
  languages: string[];
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

const DocumentAnalysis: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [templates, setTemplates] = useState<any[]>([]);
  const [analysisConfig, setAnalysisConfig] = useState<AnalysisConfig>({
    enable_ocr: true,
    enable_nlp: true,
    enable_entity_extraction: true,
    enable_summarization: true,
    enable_sentiment_analysis: true,
    enable_key_phrases: true,
    enable_language_detection: true,
    languages: ['en'],
  });

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  React.useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await apiService.get('/api/v1/document-analysis/templates');
      setTemplates(response.data.templates);
    } catch (err) {
      console.error('Failed to load templates:', err);
    }
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

  const analyzeDocument = async () => {
    if (!selectedFile) return;

    try {
      setAnalyzing(true);
      setError(null);

      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('analysis_config', JSON.stringify(analysisConfig));
      formData.append('output_format', 'json');

      const response = await apiService.post('/api/v1/document-analysis/analyze/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const taskId = response.data.task_id;
      pollForResults(taskId);

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Analysis failed');
      setAnalyzing(false);
    }
  };

  const pollForResults = (taskId: string) => {
    pollIntervalRef.current = setInterval(async () => {
      try {
        const response = await apiService.get(`/api/v1/document-analysis/status/${taskId}`);
        const data = response.data;

        if (data.status === 'completed' && data.result) {
          setResults(data.result);
          setAnalyzing(false);
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
          }
        } else if (data.status === 'failed') {
          setError(data.message || 'Analysis failed');
          setAnalyzing(false);
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

  const resetAnalysis = () => {
    setSelectedFile(null);
    setResults(null);
    setError(null);
    setAnalyzing(false);
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }
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

  const downloadReport = async (format: 'json' | 'pdf' | 'html') => {
    if (!results?.task_id) return;

    try {
      const response = await apiService.get(
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

  const exportResults = async (sections: string[]) => {
    if (!results?.task_id) return;

    try {
      const response = await apiService.get(
        `/api/v1/document-analysis/export/${results.task_id}?export_format=json&include_sections=${sections.join(',')}`
      );
      
      const data = JSON.stringify(response.data.data, null, 2);
      const blob = new Blob([data], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = response.data.filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError('Failed to export results');
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

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Analytics color="primary" />
        Document Analysis
      </Typography>

      <Grid container spacing={3}>
        {/* Upload Section */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Upload Document
              </Typography>
              
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
              <Typography variant="h6" gutterBottom>
                Analysis Templates
              </Typography>
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
              <Typography variant="h6" gutterBottom>
                Analysis Configuration
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={analysisConfig.enable_ocr}
                        onChange={(e) => handleConfigChange('enable_ocr', e.target.checked)}
                      />
                    }
                    label="Enable OCR (Text Extraction)"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={analysisConfig.enable_nlp}
                        onChange={(e) => handleConfigChange('enable_nlp', e.target.checked)}
                      />
                    }
                    label="Enable NLP Analysis"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={analysisConfig.enable_entity_extraction}
                        onChange={(e) => handleConfigChange('enable_entity_extraction', e.target.checked)}
                      />
                    }
                    label="Extract Named Entities"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={analysisConfig.enable_summarization}
                        onChange={(e) => handleConfigChange('enable_summarization', e.target.checked)}
                      />
                    }
                    label="Generate Summary"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={analysisConfig.enable_sentiment_analysis}
                        onChange={(e) => handleConfigChange('enable_sentiment_analysis', e.target.checked)}
                      />
                    }
                    label="Analyze Sentiment"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={analysisConfig.enable_key_phrases}
                        onChange={(e) => handleConfigChange('enable_key_phrases', e.target.checked)}
                      />
                    }
                    label="Extract Key Phrases"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={analysisConfig.enable_language_detection}
                        onChange={(e) => handleConfigChange('enable_language_detection', e.target.checked)}
                      />
                    }
                    label="Detect Language"
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
                      JSON Report
                    </Button>
                    <Button
                      size="small"
                      startIcon={<Download />}
                      onClick={() => downloadReport('html')}
                    >
                      HTML Report
                    </Button>
                    <Button
                      size="small"
                      startIcon={<Download />}
                      onClick={() => exportResults(['all'])}
                    >
                      Export All
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
                        <Typography variant="body2">{results.language || 'Unknown'}</Typography>
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
                  <Tab label="Full Text" />
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
                      
                      {results.processing_time && (
                        <Typography variant="caption" color="textSecondary">
                          Analysis completed in {results.processing_time.toFixed(2)} seconds
                        </Typography>
                      )}
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
                        
                        <List>
                          {results.entities.map((entity, index) => (
                            <React.Fragment key={index}>
                              <ListItem>
                                <ListItemIcon>
                                  <Chip
                                    label={entity.type}
                                    size="small"
                                    sx={{
                                      backgroundColor: getEntityColor(entity.type),
                                      color: 'white',
                                    }}
                                  />
                                </ListItemIcon>
                                <ListItemText
                                  primary={entity.text}
                                  secondary={entity.confidence ? `Confidence: ${(entity.confidence * 100).toFixed(1)}%` : undefined}
                                />
                              </ListItem>
                              {index < (results.entities?.length ?? 0) - 1 && <Divider />}
                            </React.Fragment>
                          ))}
                        </List>
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
                        {Object.entries(results.sentiment).map(([sentiment, score]) => (
                          <Grid item xs={12} sm={4} key={sentiment}>
                            <Paper sx={{ p: 2, textAlign: 'center' }}>
                              <Typography variant="h4" color={
                                sentiment === 'positive' ? 'success.main' :
                                sentiment === 'negative' ? 'error.main' : 'text.secondary'
                              }>
                                {(score * 100).toFixed(1)}%
                              </Typography>
                              <Typography variant="subtitle1" sx={{ textTransform: 'capitalize' }}>
                                {sentiment}
                              </Typography>
                            </Paper>
                          </Grid>
                        ))}
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

                {/* Full Text Tab */}
                {tabValue === 5 && (
                  <Box>
                    <Paper sx={{ p: 2, maxHeight: 400, overflow: 'auto', backgroundColor: 'grey.50' }}>
                      <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                        {results.text_content || 'No text content available'}
                      </Typography>
                    </Paper>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default DocumentAnalysis;