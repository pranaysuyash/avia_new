import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  LinearProgress,
  Chip,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Tabs,
  Tab,
  CircularProgress,
  Tooltip,
  IconButton,
  Snackbar,
  Paper,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  FormControlLabel,
  Switch,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Slider
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  Stop,
  VideoLibrary,
  Movie,
  PhotoCamera,
  Timeline,
  SmartDisplay,
  AutoAwesome,
  ExpandMore,
  Visibility,
  Download,
  Share,
  Settings,
  Analytics,
  Speed,
  HighQuality,
  Psychology,
  TrendingUp,
  Schedule,
  CheckCircle,
  Error,
  Warning,
  Info
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';

// Types
interface VideoMetadata {
  duration: number;
  fps: number;
  width: number;
  height: number;
  total_frames: number;
  codec: string;
  bitrate?: number;
  file_size: number;
  aspect_ratio: string;
  has_audio: boolean;
  quality_score: number;
  complexity_score: number;
}

interface SceneInfo {
  start_time: number;
  end_time: number;
  start_frame: number;
  end_frame: number;
  confidence: number;
  scene_type: string;
  description: string;
  motion_intensity: number;
  visual_complexity: number;
}

interface KeyFrame {
  frame_number: number;
  timestamp: number;
  confidence: number;
  frame_path?: string;
  visual_hash: string;
  objects_detected: string[];
}

interface ObjectDetection {
  class_name: string;
  category: string;
  confidence: number;
  bbox: [number, number, number, number];
  timestamp: number;
  frame_number: number;
  tracking_id?: string;
}

interface BRollSuggestion {
  timestamp: number;
  duration: number;
  suggestion_type: string;
  description: string;
  confidence: number;
  keywords: string[];
  priority: number;
}

interface ProcessingResult {
  job_id: string;
  success: boolean;
  processing_time: number;
  processing_strategy: string;
  metadata: VideoMetadata;
  keyframes: KeyFrame[];
  scenes: SceneInfo[];
  objects: ObjectDetection[];
  broll_suggestions: BRollSuggestion[];
  errors: string[];
}

interface ProcessingJob {
  job_id: string;
  status: string;
  progress: number;
  message: string;
  started_at: string;
  completed_at?: string;
  result?: ProcessingResult;
}

const AdvancedVideoProcessingEngine: React.FC = () => {
  // State management
  const [activeTab, setActiveTab] = useState(0);
  const [uploadedVideo, setUploadedVideo] = useState<File | null>(null);
  const [processing, setProcessing] = useState(false);
  const [processingResult, setProcessingResult] = useState<ProcessingResult | null>(null);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [processingJobs, setProcessingJobs] = useState<ProcessingJob[]>([]);
  const [snackbar, setSnackbar] = useState({ 
    open: false, 
    message: '', 
    severity: 'info' as 'success' | 'error' | 'warning' | 'info' 
  });

  // Processing options
  const [extractKeyframes, setExtractKeyframes] = useState(true);
  const [detectScenes, setDetectScenes] = useState(true);
  const [detectObjects, setDetectObjects] = useState(true);
  const [suggestBroll, setSuggestBroll] = useState(true);
  const [enhanceQuality, setEnhanceQuality] = useState(false);
  const [processingStrategy, setProcessingStrategy] = useState('auto');

  // Dialogs
  const [jobDetailsDialog, setJobDetailsDialog] = useState(false);
  const [selectedJob, setSelectedJob] = useState<ProcessingJob | null>(null);

  // File upload handling
  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file && file.type.startsWith('video/')) {
      setUploadedVideo(file);
      setProcessingResult(null);
    } else {
      setSnackbar({
        open: true,
        message: 'Please upload a valid video file',
        severity: 'error'
      });
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv']
    },
    multiple: false
  });

  // Load processing jobs on component mount
  useEffect(() => {
    loadProcessingJobs();
  }, []);

  // Video processing
  const processVideo = async () => {
    if (!uploadedVideo) return;

    setProcessing(true);
    try {
      const formData = new FormData();
      formData.append('video', uploadedVideo);
      formData.append('extract_keyframes', extractKeyframes.toString());
      formData.append('detect_scenes', detectScenes.toString());
      formData.append('detect_objects', detectObjects.toString());
      formData.append('suggest_broll', suggestBroll.toString());
      formData.append('enhance_quality', enhanceQuality.toString());
      
      if (processingStrategy !== 'auto') {
        formData.append('processing_strategy', processingStrategy);
      }

      const response = await fetch('/api/v1/video/process', {
        method: 'POST',
        body: formData
      });

      if (response.status === 202) {
        const result = await response.json();
        setCurrentJobId(result.job_id);
        
        setSnackbar({
          open: true,
          message: `Processing started! Job ID: ${result.job_id.substring(0, 8)}...`,
          severity: 'success'
        });

        // Start polling for status
        pollJobStatus(result.job_id);
      } else {
        throw new Error('Video processing failed');
      }
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Video processing failed',
        severity: 'error'
      });
    } finally {
      setProcessing(false);
    }
  };

  // Poll job status
  const pollJobStatus = async (jobId: string) => {
    const maxAttempts = 300; // 5 minutes max
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await fetch(`/api/v1/video/status/${jobId}`);
        if (response.ok) {
          const job: ProcessingJob = await response.json();
          
          // Update jobs list
          setProcessingJobs(prev => {
            const updated = prev.filter(j => j.job_id !== jobId);
            return [...updated, job];
          });

          if (job.status === 'completed') {
            // Get result
            const resultResponse = await fetch(`/api/v1/video/result/${jobId}`);
            if (resultResponse.ok) {
              const result = await resultResponse.json();
              setProcessingResult(result);
              setActiveTab(1); // Switch to results tab
              
              setSnackbar({
                open: true,
                message: 'Video processing completed successfully!',
                severity: 'success'
              });
            }
            return;
          } else if (job.status === 'failed') {
            setSnackbar({
              open: true,
              message: `Processing failed: ${job.message}`,
              severity: 'error'
            });
            return;
          }

          // Continue polling if still processing
          if (job.status === 'processing' && attempts < maxAttempts) {
            attempts++;
            setTimeout(poll, 2000);
          }
        }
      } catch (error) {
        console.error('Status polling error:', error);
      }
    };

    poll();
  };

  // Load processing jobs
  const loadProcessingJobs = async () => {
    try {
      const response = await fetch('/api/v1/video/jobs');
      if (response.ok) {
        const jobs = await response.json();
        setProcessingJobs(jobs);
      }
    } catch (error) {
      console.error('Failed to load jobs:', error);
    }
  };

  // Helper functions
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatFileSize = (bytes: number) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle color="success" />;
      case 'failed': return <Error color="error" />;
      case 'processing': return <CircularProgress size={20} />;
      default: return <Schedule color="action" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'processing': return 'primary';
      default: return 'default';
    }
  };

  // Tab panels
  const UploadPanel = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={8}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Upload Video File
            </Typography>
            
            <Box
              {...getRootProps()}
              sx={{
                border: '2px dashed #ccc',
                borderRadius: 2,
                p: 4,
                textAlign: 'center',
                cursor: 'pointer',
                backgroundColor: isDragActive ? '#f5f5f5' : 'transparent',
                '&:hover': { backgroundColor: '#f9f9f9' }
              }}
            >
              <input {...getInputProps()} />
              <VideoLibrary sx={{ fontSize: 48, color: '#ccc', mb: 2 }} />
              {uploadedVideo ? (
                <Box>
                  <Typography variant="body1" gutterBottom>
                    Selected: {uploadedVideo.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Size: {formatFileSize(uploadedVideo.size)}
                  </Typography>
                </Box>
              ) : (
                <Typography variant="body1">
                  {isDragActive ? 'Drop the video here...' : 'Drag & drop a video file here, or click to select'}
                </Typography>
              )}
            </Box>

            {uploadedVideo && (
              <Box sx={{ mt: 3 }}>
                <Button
                  variant="contained"
                  startIcon={<SmartDisplay />}
                  onClick={processVideo}
                  disabled={processing}
                  size="large"
                  fullWidth
                >
                  {processing ? 'Processing...' : 'Start Advanced Processing'}
                </Button>
                
                {processing && (
                  <Box sx={{ mt: 2 }}>
                    <LinearProgress />
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      Analyzing video content...
                    </Typography>
                  </Box>
                )}
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Processing Options
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={extractKeyframes}
                    onChange={(e) => setExtractKeyframes(e.target.checked)}
                  />
                }
                label="Extract Keyframes"
              />
            </Box>
            
            <Box sx={{ mb: 2 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={detectScenes}
                    onChange={(e) => setDetectScenes(e.target.checked)}
                  />
                }
                label="Detect Scenes"
              />
            </Box>
            
            <Box sx={{ mb: 2 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={detectObjects}
                    onChange={(e) => setDetectObjects(e.target.checked)}
                  />
                }
                label="Detect Objects"
              />
            </Box>
            
            <Box sx={{ mb: 2 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={suggestBroll}
                    onChange={(e) => setSuggestBroll(e.target.checked)}
                  />
                }
                label="B-roll Suggestions"
              />
            </Box>
            
            <Box sx={{ mb: 2 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={enhanceQuality}
                    onChange={(e) => setEnhanceQuality(e.target.checked)}
                  />
                }
                label="Enhance Quality"
              />
            </Box>

            <FormControl fullWidth sx={{ mt: 2 }}>
              <InputLabel>Processing Strategy</InputLabel>
              <Select
                value={processingStrategy}
                label="Processing Strategy"
                onChange={(e) => setProcessingStrategy(e.target.value)}
              >
                <MenuItem value="auto">Auto</MenuItem>
                <MenuItem value="basic">Basic</MenuItem>
                <MenuItem value="enhanced">Enhanced</MenuItem>
                <MenuItem value="professional">Professional</MenuItem>
                <MenuItem value="enterprise">Enterprise</MenuItem>
              </Select>
            </FormControl>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const ResultsPanel = () => {
    if (!processingResult) {
      return (
        <Alert severity="info">
          No processing results available. Please upload and process a video first.
        </Alert>
      );
    }

    return (
      <Box>
        {/* Summary metrics */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={6} sm={2.4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="primary">
                {formatDuration(processingResult.processing_time)}
              </Typography>
              <Typography variant="body2">Processing Time</Typography>
            </Paper>
          </Grid>
          
          <Grid item xs={6} sm={2.4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="secondary">
                {processingResult.keyframes.length}
              </Typography>
              <Typography variant="body2">Keyframes</Typography>
            </Paper>
          </Grid>
          
          <Grid item xs={6} sm={2.4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="success.main">
                {processingResult.scenes.length}
              </Typography>
              <Typography variant="body2">Scenes</Typography>
            </Paper>
          </Grid>
          
          <Grid item xs={6} sm={2.4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="warning.main">
                {processingResult.objects.length}
              </Typography>
              <Typography variant="body2">Objects</Typography>
            </Paper>
          </Grid>
          
          <Grid item xs={6} sm={2.4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="info.main">
                {processingResult.broll_suggestions.length}
              </Typography>
              <Typography variant="body2">B-roll Ideas</Typography>
            </Paper>
          </Grid>
        </Grid>

        {/* Video metadata */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Video Information
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TableContainer>
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell>Duration</TableCell>
                        <TableCell>{formatDuration(processingResult.metadata.duration)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Resolution</TableCell>
                        <TableCell>{processingResult.metadata.width}x{processingResult.metadata.height}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>FPS</TableCell>
                        <TableCell>{processingResult.metadata.fps.toFixed(2)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Codec</TableCell>
                        <TableCell>{processingResult.metadata.codec}</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TableContainer>
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell>File Size</TableCell>
                        <TableCell>{formatFileSize(processingResult.metadata.file_size)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Quality Score</TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            {(processingResult.metadata.quality_score * 100).toFixed(0)}%
                            <LinearProgress 
                              variant="determinate" 
                              value={processingResult.metadata.quality_score * 100}
                              sx={{ ml: 1, flex: 1 }}
                            />
                          </Box>
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Complexity</TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            {(processingResult.metadata.complexity_score * 100).toFixed(0)}%
                            <LinearProgress 
                              variant="determinate" 
                              value={processingResult.metadata.complexity_score * 100}
                              sx={{ ml: 1, flex: 1 }}
                            />
                          </Box>
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Strategy Used</TableCell>
                        <TableCell>
                          <Chip 
                            label={processingResult.processing_strategy} 
                            size="small" 
                            color="primary"
                          />
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Errors */}
        {processingResult.errors.length > 0 && (
          <Alert severity="warning" sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Processing Warnings:
            </Typography>
            {processingResult.errors.map((error, index) => (
              <Typography key={index} variant="body2">
                • {error}
              </Typography>
            ))}
          </Alert>
        )}
      </Box>
    );
  };

  const ScenesPanel = () => {
    if (!processingResult || processingResult.scenes.length === 0) {
      return (
        <Alert severity="info">
          No scenes detected. Process a video to see scene analysis.
        </Alert>
      );
    }

    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          Scene Analysis ({processingResult.scenes.length} scenes detected)
        </Typography>
        
        {processingResult.scenes.map((scene, index) => (
          <Accordion key={index}>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                <Timeline sx={{ mr: 2 }} />
                <Box sx={{ flex: 1 }}>
                  <Typography variant="subtitle1">
                    Scene {index + 1}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {formatDuration(scene.start_time)} - {formatDuration(scene.end_time)} 
                    ({formatDuration(scene.end_time - scene.start_time)})
                  </Typography>
                </Box>
                <Chip 
                  label={scene.scene_type} 
                  size="small" 
                  color="primary"
                  sx={{ mr: 1 }}
                />
                <Chip 
                  label={`${(scene.confidence * 100).toFixed(0)}%`} 
                  size="small" 
                  color={scene.confidence > 0.8 ? 'success' : 'default'}
                />
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" gutterBottom>
                    <strong>Motion Intensity:</strong>
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <LinearProgress 
                      variant="determinate" 
                      value={scene.motion_intensity * 100}
                      sx={{ flex: 1, mr: 1 }}
                    />
                    <Typography variant="body2">
                      {(scene.motion_intensity * 100).toFixed(0)}%
                    </Typography>
                  </Box>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" gutterBottom>
                    <strong>Visual Complexity:</strong>
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <LinearProgress 
                      variant="determinate" 
                      value={scene.visual_complexity * 100}
                      sx={{ flex: 1, mr: 1 }}
                    />
                    <Typography variant="body2">
                      {(scene.visual_complexity * 100).toFixed(0)}%
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
              
              {scene.description && (
                <Typography variant="body2">
                  <strong>Description:</strong> {scene.description}
                </Typography>
              )}
            </AccordionDetails>
          </Accordion>
        ))}
      </Box>
    );
  };

  const BRollPanel = () => {
    if (!processingResult || processingResult.broll_suggestions.length === 0) {
      return (
        <Alert severity="info">
          No B-roll suggestions available. Process a video to get intelligent recommendations.
        </Alert>
      );
    }

    // Group suggestions by priority
    const suggestionsByPriority = processingResult.broll_suggestions.reduce((acc, suggestion) => {
      const priority = suggestion.priority;
      if (!acc[priority]) acc[priority] = [];
      acc[priority].push(suggestion);
      return acc;
    }, {} as Record<number, BRollSuggestion[]>);

    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          B-roll Suggestions ({processingResult.broll_suggestions.length} recommendations)
        </Typography>
        
        {Object.entries(suggestionsByPriority)
          .sort(([a], [b]) => parseInt(b) - parseInt(a)) // Sort by priority (high to low)
          .map(([priority, suggestions]) => (
            <Box key={priority} sx={{ mb: 3 }}>
              <Typography variant="subtitle1" gutterBottom>
                Priority {priority} ({suggestions.length} suggestions)
              </Typography>
              
              {suggestions.map((suggestion, index) => (
                <Card key={index} sx={{ mb: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <AutoAwesome sx={{ mr: 2, color: 'primary.main' }} />
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="subtitle2">
                          {suggestion.suggestion_type.replace('_', ' ').toUpperCase()}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          At {formatDuration(suggestion.timestamp)} for {formatDuration(suggestion.duration)}
                        </Typography>
                      </Box>
                      <Chip 
                        label={`${(suggestion.confidence * 100).toFixed(0)}%`} 
                        size="small" 
                        color={suggestion.confidence > 0.7 ? 'success' : 'default'}
                      />
                    </Box>
                    
                    <Typography variant="body1" gutterBottom>
                      {suggestion.description}
                    </Typography>
                    
                    {suggestion.keywords.length > 0 && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Keywords:
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {suggestion.keywords.map((keyword, keywordIndex) => (
                            <Chip
                              key={keywordIndex}
                              label={keyword}
                              size="small"
                              variant="outlined"
                            />
                          ))}
                        </Box>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              ))}
            </Box>
          ))}
      </Box>
    );
  };

  const JobsPanel = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6">
          Processing Jobs ({processingJobs.length})
        </Typography>
        <Button onClick={loadProcessingJobs} startIcon={<Analytics />}>
          Refresh
        </Button>
      </Box>

      {processingJobs.length === 0 ? (
        <Alert severity="info">
          No processing jobs found.
        </Alert>
      ) : (
        <Grid container spacing={2}>
          {processingJobs.map((job) => (
            <Grid item xs={12} md={6} lg={4} key={job.job_id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    {getStatusIcon(job.status)}
                    <Box sx={{ ml: 2, flex: 1 }}>
                      <Typography variant="subtitle2">
                        Job {job.job_id.substring(0, 8)}...
                      </Typography>
                      <Chip 
                        label={job.status} 
                        size="small" 
                        color={getStatusColor(job.status) as any}
                      />
                    </Box>
                  </Box>
                  
                  {job.status === 'processing' && (
                    <Box sx={{ mb: 2 }}>
                      <LinearProgress 
                        variant="determinate" 
                        value={job.progress * 100} 
                      />
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        {(job.progress * 100).toFixed(0)}% - {job.message}
                      </Typography>
                    </Box>
                  )}
                  
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Started: {new Date(job.started_at).toLocaleString()}
                  </Typography>
                  
                  {job.completed_at && (
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Completed: {new Date(job.completed_at).toLocaleString()}
                    </Typography>
                  )}
                  
                  <Box sx={{ mt: 2 }}>
                    <Button
                      size="small"
                      onClick={() => {
                        setSelectedJob(job);
                        setJobDetailsDialog(true);
                      }}
                    >
                      View Details
                    </Button>
                    
                    {job.status === 'completed' && job.result && (
                      <Button
                        size="small"
                        onClick={() => {
                          setProcessingResult(job.result!);
                          setActiveTab(1);
                        }}
                        sx={{ ml: 1 }}
                      >
                        Load Result
                      </Button>
                    )}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h4" gutterBottom>
        Advanced Video Processing Engine
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Task 3: Advanced Media Processing Pipeline
      </Typography>
      
      <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
        <Tab icon={<VideoLibrary />} label="Upload" />
        <Tab icon={<Analytics />} label="Results" disabled={!processingResult} />
        <Tab icon={<Timeline />} label="Scenes" disabled={!processingResult} />
        <Tab icon={<AutoAwesome />} label="B-roll" disabled={!processingResult} />
        <Tab icon={<Schedule />} label="Jobs" />
      </Tabs>

      {activeTab === 0 && <UploadPanel />}
      {activeTab === 1 && <ResultsPanel />}
      {activeTab === 2 && <ScenesPanel />}
      {activeTab === 3 && <BRollPanel />}
      {activeTab === 4 && <JobsPanel />}

      {/* Job Details Dialog */}
      <Dialog
        open={jobDetailsDialog}
        onClose={() => setJobDetailsDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Job Details: {selectedJob?.job_id.substring(0, 8)}...
        </DialogTitle>
        <DialogContent>
          {selectedJob && (
            <Box>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" gutterBottom>
                    <strong>Status:</strong> {selectedJob.status}
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    <strong>Progress:</strong> {(selectedJob.progress * 100).toFixed(0)}%
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    <strong>Started:</strong> {new Date(selectedJob.started_at).toLocaleString()}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" gutterBottom>
                    <strong>Message:</strong> {selectedJob.message}
                  </Typography>
                  {selectedJob.completed_at && (
                    <Typography variant="body2" gutterBottom>
                      <strong>Completed:</strong> {new Date(selectedJob.completed_at).toLocaleString()}
                    </Typography>
                  )}
                </Grid>
              </Grid>
              
              {selectedJob.status === 'processing' && (
                <Box sx={{ mt: 2 }}>
                  <LinearProgress 
                    variant="determinate" 
                    value={selectedJob.progress * 100} 
                  />
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setJobDetailsDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default AdvancedVideoProcessingEngine;