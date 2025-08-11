import React, { useState, useCallback, useRef } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  FormControl,
  FormControlLabel,
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
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  CloudUpload,
  Download,
  Analytics,
  Palette,
  PhotoCamera,
  Assessment,
  Psychology,
  Settings,
  ExpandMore,
  Compare,
  Refresh,
  Close,
  Insights,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
} from 'chart.js';
import { Pie, Bar, Radar } from 'react-chartjs-2';
import apiService from '../../services/api';

ChartJS.register(
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler
);

interface AnalysisOptions {
  include_sections: string[];
  detailed_analysis: boolean;
  use_gpu: boolean;
}

interface AnalysisResults {
  task_id: string;
  status: string;
  file_info?: any;
  color_analysis?: any;
  composition_analysis?: any;
  content_analysis?: any;
  quality_metrics?: any;
  semantic_insights?: any;
  confidence_scores?: { [key: string]: number };
  processing_time: number;
  analysis_timestamp?: string;
}

const ImageAnalysisInsights: React.FC = () => {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [showSettings, setShowSettings] = useState(false);
  const [showComparison, setShowComparison] = useState(false);
  const [analysisOptions, setAnalysisOptions] = useState<AnalysisOptions>({
    include_sections: ['all'],
    detailed_analysis: true,
    use_gpu: false,
  });

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file && file.type.startsWith('image/')) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setSelectedImage(e.target?.result as string);
        setResults(null);
        setError(null);
      };
      reader.readAsDataURL(file);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.bmp', '.tiff'],
    },
    multiple: false,
  });

  const analyzeImage = async () => {
    if (!selectedImage || !imageFile) return;

    try {
      setAnalyzing(true);
      setError(null);

      const formData = new FormData();
      formData.append('file', imageFile);
      formData.append('analysis_options', JSON.stringify(analysisOptions));
      formData.append('include_sections', JSON.stringify(analysisOptions.include_sections));

      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/image-analysis/analyze/upload`, {
        method: 'POST',
        body: formData,
      }).then(res => res.json());

      const taskId = response.task_id;
      pollForResults(taskId);

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Analysis failed');
      setAnalyzing(false);
    }
  };

  const pollForResults = (taskId: string) => {
    pollIntervalRef.current = setInterval(async () => {
      try {
        const response = await apiService.get(`/api/v1/image-analysis/status/${taskId}`);
        const result: AnalysisResults = response.data;

        if (result.status === 'completed') {
          setResults(result);
          setAnalyzing(false);
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
          }
        } else if (result.status === 'failed') {
          setError('Analysis failed');
          setAnalyzing(false);
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
          }
        }
      } catch (err: any) {
        setError('Failed to get analysis status');
        setAnalyzing(false);
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
        }
      }
    }, 1000);
  };

  const resetAnalysis = () => {
    setSelectedImage(null);
    setImageFile(null);
    setResults(null);
    setError(null);
    setAnalyzing(false);
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }
  };

  const handleOptionChange = (key: keyof AnalysisOptions, value: any) => {
    setAnalysisOptions({ ...analysisOptions, [key]: value });
  };

  const createColorChart = () => {
    if (!results?.color_analysis?.dominant_colors) return null;

    const colors = results.color_analysis.dominant_colors.slice(0, 5);
    const data = {
      labels: colors.map((_: any, i: number) => `Color ${i + 1}`),
      datasets: [
        {
          data: colors.map(() => 1),
          backgroundColor: colors.map((color: number[]) => `rgb(${color[0]}, ${color[1]}, ${color[2]})`),
          borderWidth: 2,
          borderColor: '#fff',
        },
      ],
    };

    return (
      <Box sx={{ width: 300, height: 300 }}>
        <Pie
          data={data}
          options={{
            responsive: true,
            plugins: {
              legend: {
                position: 'bottom' as const,
              },
              title: {
                display: true,
                text: 'Dominant Colors',
              },
            },
          }}
        />
      </Box>
    );
  };

  const createQualityRadar = () => {
    if (!results?.quality_metrics) return null;

    const data = {
      labels: ['Sharpness', 'Exposure', 'White Balance', 'Resolution', 'Overall'],
      datasets: [
        {
          label: 'Quality Scores',
          data: [
            results.quality_metrics.sharpness_score / 100,
            results.quality_metrics.exposure_quality === 'optimal' ? 1 : 0.5,
            results.quality_metrics.white_balance === 'good' ? 1 : results.quality_metrics.white_balance === 'fair' ? 0.7 : 0.3,
            results.quality_metrics.resolution_quality === 'high' ? 1 : results.quality_metrics.resolution_quality === 'medium' ? 0.8 : 0.5,
            results.quality_metrics.technical_score / 100,
          ],
          fill: true,
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          borderColor: 'rgb(54, 162, 235)',
          pointBackgroundColor: 'rgb(54, 162, 235)',
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: 'rgb(54, 162, 235)',
        },
      ],
    };

    return (
      <Box sx={{ width: 400, height: 400 }}>
        <Radar
          data={data}
          options={{
            responsive: true,
            plugins: {
              title: {
                display: true,
                text: 'Quality Assessment',
              },
            },
            scales: {
              r: {
                angleLines: {
                  display: true,
                },
                suggestedMin: 0,
                suggestedMax: 1,
              },
            },
          }}
        />
      </Box>
    );
  };

  const createCompositionChart = () => {
    if (!results?.composition_analysis) return null;

    const data = {
      labels: ['Rule of Thirds', 'Symmetry', 'Balance'],
      datasets: [
        {
          label: 'Composition Scores',
          data: [
            results.composition_analysis.rule_of_thirds_alignment,
            results.composition_analysis.symmetry_score,
            results.composition_analysis.balance_score,
          ],
          backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56'],
          borderWidth: 1,
        },
      ],
    };

    return (
      <Box sx={{ width: 400, height: 300 }}>
        <Bar
          data={data}
          options={{
            responsive: true,
            plugins: {
              title: {
                display: true,
                text: 'Composition Analysis',
              },
            },
            scales: {
              y: {
                beginAtZero: true,
                max: 1,
              },
            },
          }}
        />
      </Box>
    );
  };

  const renderSummaryCards = () => {
    if (!results) return null;

    return (
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 3, mb: 3 }}>
        <Box>
          <Card sx={{ textAlign: 'center', bgcolor: getQualityColor(results.quality_metrics?.overall_quality) }}>
            <CardContent>
              <Assessment sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h6" component="div">
                Overall Quality
              </Typography>
              <Typography variant="h4" component="div">
                {results.quality_metrics?.overall_quality || 'N/A'}
              </Typography>
              <Typography variant="body2">
                Score: {results.quality_metrics?.technical_score?.toFixed(1) || 0}/100
              </Typography>
            </CardContent>
          </Card>
        </Box>

        <Box>
          <Card sx={{ textAlign: 'center', bgcolor: '#e3f2fd' }}>
            <CardContent>
              <PhotoCamera sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h6" component="div">
                Scene Type
              </Typography>
              <Typography variant="h4" component="div">
                {results.content_analysis?.scene_type || 'Unknown'}
              </Typography>
              <Typography variant="body2">
                Complexity: {results.content_analysis?.scene_complexity || 'N/A'}
              </Typography>
            </CardContent>
          </Card>
        </Box>

        <Box>
          <Card sx={{ textAlign: 'center', bgcolor: '#f3e5f5' }}>
            <CardContent>
              <Psychology sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h6" component="div">
                Commercial Potential
              </Typography>
              <Typography variant="h4" component="div">
                {results.semantic_insights?.commercial_potential || 'Unknown'}
              </Typography>
              <Typography variant="body2">
                Confidence: {results.confidence_scores?.overall?.toFixed(2) || 0}
              </Typography>
            </CardContent>
          </Card>
        </Box>

        <Box>
          <Card sx={{ textAlign: 'center', bgcolor: '#e8f5e8' }}>
            <CardContent>
              <Analytics sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h6" component="div">
                Processing Time
              </Typography>
              <Typography variant="h4" component="div">
                {results.processing_time?.toFixed(2) || 0}s
              </Typography>
              <Typography variant="body2">
                {results.analysis_timestamp?.slice(0, 19) || 'N/A'}
              </Typography>
            </CardContent>
          </Card>
        </Box>
      </Box>
    );
  };

  const getQualityColor = (quality: string) => {
    switch (quality) {
      case 'excellent': return '#e8f5e8';
      case 'good': return '#e3f2fd';
      case 'fair': return '#fff3e0';
      case 'poor': return '#ffebee';
      default: return '#f5f5f5';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Insights color="primary" />
        Image Analysis & Insights
      </Typography>

      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 3 }}>
        {/* Upload Section */}
        <Box>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Upload Image
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
                    ? 'Drop the image here...'
                    : 'Drag & drop an image here, or click to select'}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Supports: JPG, PNG, BMP, TIFF (Max 10MB)
                </Typography>
              </Box>

              {selectedImage && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Selected Image:
                  </Typography>
                  <img
                    src={selectedImage}
                    alt="Selected"
                    style={{
                      width: '100%',
                      maxHeight: 300,
                      objectFit: 'contain',
                      border: '1px solid #ccc',
                      borderRadius: 4,
                    }}
                  />
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>

        {/* Controls Section */}
        <Box>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Analysis Controls
              </Typography>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Analysis Sections</InputLabel>
                <Select
                  multiple
                  value={analysisOptions.include_sections}
                  onChange={(e) => handleOptionChange('include_sections', e.target.value)}
                  label="Analysis Sections"
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {(selected as string[]).map((value) => (
                        <Chip key={value} label={value} size="small" />
                      ))}
                    </Box>
                  )}
                >
                  <MenuItem value="all">All Sections</MenuItem>
                  <MenuItem value="color">Color Analysis</MenuItem>
                  <MenuItem value="composition">Composition</MenuItem>
                  <MenuItem value="content">Content</MenuItem>
                  <MenuItem value="quality">Quality</MenuItem>
                  <MenuItem value="semantic">Semantic Insights</MenuItem>
                </Select>
              </FormControl>

              <FormControlLabel
                control={
                  <Switch
                    checked={analysisOptions.detailed_analysis}
                    onChange={(e) => handleOptionChange('detailed_analysis', e.target.checked)}
                  />
                }
                label="Detailed Analysis"
                sx={{ mb: 1 }}
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={analysisOptions.use_gpu}
                    onChange={(e) => handleOptionChange('use_gpu', e.target.checked)}
                  />
                }
                label="Use GPU Acceleration"
                sx={{ mb: 2 }}
              />

              <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                <Button
                  startIcon={<Settings />}
                  onClick={() => setShowSettings(true)}
                  variant="outlined"
                >
                  Settings
                </Button>
                <Button
                  startIcon={<Refresh />}
                  onClick={resetAnalysis}
                  variant="outlined"
                >
                  Reset
                </Button>
              </Box>

              <Button
                variant="contained"
                size="large"
                fullWidth
                onClick={analyzeImage}
                disabled={!selectedImage || analyzing}
                startIcon={analyzing ? <CircularProgress size={20} /> : <Analytics />}
              >
                {analyzing ? 'Analyzing...' : 'Analyze Image'}
              </Button>

              {error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {error}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Box>

        {/* Results Section */}
        {results && (
          <Box>
            <Card>
              <CardContent>
                <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Assessment color="primary" />
                  Analysis Results
                  <Box sx={{ ml: 'auto', display: 'flex', gap: 1 }}>
                    <IconButton onClick={() => setShowComparison(true)}>
                      <Compare />
                    </IconButton>
                    <IconButton>
                      <Download />
                    </IconButton>
                  </Box>
                </Typography>

                {renderSummaryCards()}

                <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
                  <Tab label="Color Analysis" icon={<Palette />} />
                  <Tab label="Composition" icon={<PhotoCamera />} />
                  <Tab label="Content" icon={<Assessment />} />
                  <Tab label="Quality" icon={<Settings />} />
                  <Tab label="Insights" icon={<Psychology />} />
                </Tabs>

                {/* Color Analysis Tab */}
                {tabValue === 0 && results.color_analysis && (
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      Color Analysis
                    </Typography>
                    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 3 }}>
                      <Box>
                        {createColorChart()}
                      </Box>
                      <Box>
                        <Paper sx={{ p: 2 }}>
                          <Typography variant="h6" gutterBottom>
                            Color Properties
                          </Typography>
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                            <Chip label={`Temperature: ${results.color_analysis.color_temperature}`} />
                            <Chip label={`Brightness: ${results.color_analysis.brightness_level}`} />
                            <Chip label={`Contrast: ${results.color_analysis.contrast_level}`} />
                            <Chip label={`Saturation: ${results.color_analysis.saturation_level}`} />
                            <Chip label={`Diversity: ${results.color_analysis.color_diversity?.toFixed(2)}`} />
                          </Box>
                        </Paper>
                      </Box>
                    </Box>
                  </Box>
                )}

                {/* Composition Analysis Tab */}
                {tabValue === 1 && results.composition_analysis && (
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      Composition Analysis
                    </Typography>
                    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 3 }}>
                      <Box>
                        {createCompositionChart()}
                      </Box>
                      <Box>
                        <Paper sx={{ p: 2 }}>
                          <Typography variant="h6" gutterBottom>
                            Composition Details
                          </Typography>
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                            <Typography>Aspect Ratio: {results.composition_analysis.aspect_ratio?.toFixed(2)}</Typography>
                            <Typography>Orientation: {results.composition_analysis.orientation}</Typography>
                            <Typography>Focal Points: {results.composition_analysis.focal_points?.length || 0}</Typography>
                            <Typography>Leading Lines: {results.composition_analysis.leading_lines_detected ? 'Yes' : 'No'}</Typography>
                            <Typography>Depth of Field: {results.composition_analysis.depth_of_field_estimate}</Typography>
                          </Box>
                        </Paper>
                      </Box>
                    </Box>
                  </Box>
                )}

                {/* Content Analysis Tab */}
                {tabValue === 2 && results.content_analysis && (
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      Content Analysis
                    </Typography>
                    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 3 }}>
                      <Box>
                        <Paper sx={{ p: 2 }}>
                          <Typography variant="h6" gutterBottom>
                            Scene Information
                          </Typography>
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                            <Typography>Scene Type: {results.content_analysis.scene_type}</Typography>
                            <Typography>Complexity: {results.content_analysis.scene_complexity}</Typography>
                            <Typography>Faces Detected: {results.content_analysis.faces_detected}</Typography>
                            <Typography>Text Regions: {results.content_analysis.text_regions?.length || 0}</Typography>
                            <Typography>Emotional Tone: {results.content_analysis.emotional_tone}</Typography>
                          </Box>
                        </Paper>
                      </Box>
                      <Box>
                        <Paper sx={{ p: 2 }}>
                          <Typography variant="h6" gutterBottom>
                            Detected Objects
                          </Typography>
                          {results.content_analysis.primary_subjects?.map((subject: string, index: number) => (
                            <Chip key={index} label={subject} sx={{ mr: 1, mb: 1 }} />
                          ))}
                        </Paper>
                      </Box>
                    </Box>
                  </Box>
                )}

                {/* Quality Analysis Tab */}
                {tabValue === 3 && results.quality_metrics && (
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      Quality Assessment
                    </Typography>
                    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 3 }}>
                      <Box>
                        {createQualityRadar()}
                      </Box>
                      <Box>
                        <Paper sx={{ p: 2 }}>
                          <Typography variant="h6" gutterBottom>
                            Quality Metrics
                          </Typography>
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                            <Box>
                              <Typography>Sharpness: {results.quality_metrics.sharpness_score?.toFixed(1)}/100</Typography>
                              <LinearProgress 
                                variant="determinate" 
                                value={results.quality_metrics.sharpness_score || 0} 
                                sx={{ mt: 0.5 }}
                              />
                            </Box>
                            <Typography>Exposure: {results.quality_metrics.exposure_quality}</Typography>
                            <Typography>White Balance: {results.quality_metrics.white_balance}</Typography>
                            <Typography>Noise Level: {results.quality_metrics.noise_level}</Typography>
                            <Typography>Resolution: {results.quality_metrics.resolution_quality}</Typography>
                            {results.quality_metrics.compression_artifacts && (
                              <Alert severity="warning">Compression artifacts detected</Alert>
                            )}
                          </Box>
                        </Paper>
                      </Box>
                    </Box>
                  </Box>
                )}

                {/* Semantic Insights Tab */}
                {tabValue === 4 && results.semantic_insights && (
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      Semantic Insights
                    </Typography>
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Typography>Scene Description</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Typography>{results.semantic_insights.scene_description}</Typography>
                      </AccordionDetails>
                    </Accordion>
                    
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Typography>Key Themes & Categories</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="subtitle2" gutterBottom>Key Themes:</Typography>
                          {results.semantic_insights.key_themes?.map((theme: string, index: number) => (
                            <Chip key={index} label={theme} sx={{ mr: 1, mb: 1 }} />
                          ))}
                        </Box>
                        <Box>
                          <Typography variant="subtitle2" gutterBottom>Content Categories:</Typography>
                          {results.semantic_insights.content_categories?.map((category: string, index: number) => (
                            <Chip key={index} label={category} sx={{ mr: 1, mb: 1 }} />
                          ))}
                        </Box>
                      </AccordionDetails>
                    </Accordion>

                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Typography>Commercial Insights</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Typography>Commercial Potential: {results.semantic_insights.commercial_potential}</Typography>
                        <Typography>Emotional Impact: {results.semantic_insights.emotional_impact}</Typography>
                        <Typography>Target Audience: {results.semantic_insights.target_audience?.join(', ')}</Typography>
                      </AccordionDetails>
                    </Accordion>

                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Typography>Accessibility & Tags</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Typography paragraph>{results.semantic_insights.accessibility_description}</Typography>
                        <Typography variant="subtitle2" gutterBottom>Suggested Stock Tags:</Typography>
                        {results.semantic_insights.similar_stock_tags?.map((tag: string, index: number) => (
                          <Chip key={index} label={tag} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                        ))}
                      </AccordionDetails>
                    </Accordion>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Box>
        )}
      </Box>

      {/* Settings Dialog */}
      <Dialog open={showSettings} onClose={() => setShowSettings(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Advanced Settings
          <IconButton
            sx={{ position: 'absolute', right: 8, top: 8 }}
            onClick={() => setShowSettings(false)}
          >
            <Close />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Configure advanced analysis options for more precise results.
          </Typography>
          
          <FormControlLabel
            control={
              <Switch
                checked={analysisOptions.detailed_analysis}
                onChange={(e) => handleOptionChange('detailed_analysis', e.target.checked)}
              />
            }
            label="Enable detailed analysis (slower but more accurate)"
          />
          
          <FormControlLabel
            control={
              <Switch
                checked={analysisOptions.use_gpu}
                onChange={(e) => handleOptionChange('use_gpu', e.target.checked)}
              />
            }
            label="Use GPU acceleration (if available)"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSettings(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ImageAnalysisInsights;