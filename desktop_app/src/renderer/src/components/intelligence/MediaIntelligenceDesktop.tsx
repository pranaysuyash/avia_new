/**
 * Media Intelligence Component - Electron Desktop
 * Video and image analysis with scene detection and highlights
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Paper,
  Chip,
  CircularProgress,
  Alert,
  LinearProgress,
  IconButton,
  Tooltip,
  Slider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stepper,
  Step,
  StepLabel,
  ImageList,
  ImageListItem,
  ImageListItemBar,
  Fab,
  Badge,
  Drawer,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  SpeedDial,
  SpeedDialAction,
  SpeedDialIcon,
  Snackbar,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Movie as MovieIcon,
  Image as ImageIcon,
  Timeline as TimelineIcon,
  AutoAwesome as HighlightIcon,
  Face as FaceIcon,
  Label as LabelIcon,
  ColorLens as ColorIcon,
  Assessment as AssessmentIcon,
  Download as DownloadIcon,
  ThumbUp as ThumbUpIcon,
  Visibility as VisibilityIcon,
  Edit as EditIcon,
  Share as ShareIcon,
  FolderOpen as OpenIcon,
  Save as SaveIcon,
  Settings as SettingsIcon,
  VideoLibrary as VideoLibraryIcon,
  PhotoLibrary as PhotoLibraryIcon,
  Analytics as AnalyticsIcon,
  Speed as SpeedIcon,
  SkipNext as SkipNextIcon,
  SkipPrevious as SkipPreviousIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { Timeline, TimelineItem, TimelineSeparator, TimelineConnector, TimelineContent, TimelineDot } from '@mui/lab';
import { ipcRenderer } from 'electron';

// Desktop-specific styled components
const DesktopUploadArea = styled(Paper)(({ theme, isDragging }: any) => ({
  padding: theme.spacing(6),
  textAlign: 'center',
  border: `3px dashed ${isDragging ? theme.palette.primary.main : theme.palette.divider}`,
  backgroundColor: isDragging ? theme.palette.action.hover : theme.palette.background.paper,
  cursor: 'pointer',
  transition: 'all 0.3s',
  minHeight: 300,
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  '&:hover': {
    borderColor: theme.palette.primary.main,
    backgroundColor: theme.palette.action.hover,
    transform: 'scale(1.02)',
  },
}));

const VideoPlayer = styled('video')({
  width: '100%',
  maxHeight: 500,
  borderRadius: 8,
  boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
});

const SceneCard = styled(Card)(({ theme, isHighlight }: any) => ({
  marginBottom: theme.spacing(2),
  border: isHighlight ? `2px solid ${theme.palette.secondary.main}` : 'none',
  background: isHighlight 
    ? `linear-gradient(135deg, ${theme.palette.secondary.light}20 0%, ${theme.palette.secondary.main}20 100%)`
    : theme.palette.background.paper,
  transition: 'all 0.3s',
  cursor: 'pointer',
  '&:hover': {
    transform: 'translateX(10px)',
    boxShadow: theme.shadows[6],
  },
}));

const QualityIndicator = styled(Box)(({ theme, quality }: any) => ({
  width: 80,
  height: 80,
  borderRadius: '50%',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: '1.5rem',
  fontWeight: 'bold',
  color: 'white',
  background: quality > 0.8 
    ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
    : quality > 0.6
    ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
    : 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
  boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
}));

const ThumbnailContainer = styled(Box)({
  position: 'relative',
  cursor: 'pointer',
  overflow: 'hidden',
  borderRadius: 8,
  '&:hover .overlay': {
    opacity: 1,
  },
  '&:hover img': {
    transform: 'scale(1.1)',
  },
});

const ThumbnailOverlay = styled(Box)(({ theme }) => ({
  position: 'absolute',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: 'rgba(0, 0, 0, 0.7)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  opacity: 0,
  transition: 'opacity 0.3s',
}));

interface Scene {
  id: string;
  type: string;
  start: number;
  end: number;
  confidence: number;
  thumbnail?: string;
  objects?: string[];
  dominantColors?: string[];
}

interface Highlight {
  id: string;
  start: number;
  end: number;
  score: number;
  reason: string;
  thumbnail?: string;
  tags?: string[];
}

interface MediaAnalysis {
  assetId: string;
  mediaType: string;
  duration: number;
  resolution: string;
  fps: number;
  qualityScore: number;
  scenes: Scene[];
  highlights: Highlight[];
  detectedObjects: Record<string, number>;
  detectedBrands: string[];
  uniqueFaces: number;
  viralPotential: number;
  colorPalette: string[];
  audioAnalysis?: {
    hasMusic: boolean;
    hasSpeech: boolean;
    loudness: number;
    tempo?: number;
  };
  autoChapters: Array<{
    title: string;
    start: number;
    end: number;
    thumbnail?: string;
  }>;
  technicalMetrics: {
    bitrate: string;
    codec: string;
    fileSize: string;
  };
}

interface MediaIntelligenceDesktopProps {
  apiEndpoint?: string;
  onAnalysisComplete?: (analysis: MediaAnalysis) => void;
}

const MediaIntelligenceDesktop: React.FC<MediaIntelligenceDesktopProps> = ({
  apiEndpoint = '/api/intelligence/media/analyze',
  onAnalysisComplete,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<MediaAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [selectedScene, setSelectedScene] = useState<Scene | null>(null);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [currentTime, setCurrentTime] = useState(0);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [exportFormat, setExportFormat] = useState('mp4');
  const [enableAIEnhancement, setEnableAIEnhancement] = useState(true);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [mediaHistory, setMediaHistory] = useState<MediaAnalysis[]>([]);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    // Set up IPC listeners for desktop-specific features
    ipcRenderer.on('media-file-selected', (event, filePath) => {
      loadMediaFile(filePath);
    });

    ipcRenderer.on('analysis-progress', (event, progress) => {
      setActiveStep(progress.step);
    });

    ipcRenderer.on('gpu-acceleration-status', (event, status) => {
      console.log('GPU Acceleration:', status);
    });

    // Load saved analyses
    loadMediaHistory();

    return () => {
      ipcRenderer.removeAllListeners('media-file-selected');
      ipcRenderer.removeAllListeners('analysis-progress');
      ipcRenderer.removeAllListeners('gpu-acceleration-status');
    };
  }, []);

  const loadMediaHistory = async () => {
    try {
      const history = await ipcRenderer.invoke('load-media-history');
      if (history) {
        setMediaHistory(history);
      }
    } catch (err) {
      console.error('Failed to load media history:', err);
    }
  };

  const loadMediaFile = async (filePath: string) => {
    try {
      const fileData = await ipcRenderer.invoke('load-media-file', filePath);
      if (fileData) {
        const blob = new Blob([fileData.buffer], { type: fileData.mimeType });
        const file = new File([blob], fileData.name, { type: fileData.mimeType });
        setFile(file);
      }
    } catch (err) {
      console.error('Failed to load media file:', err);
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
      if (file.type.startsWith('video/') || file.type.startsWith('image/')) {
        setFile(file);
        setError(null);
      } else {
        setError('Please upload a valid video or image file');
      }
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      setFile(files[0]);
      setError(null);
    }
  }, []);

  const openFileDialog = async () => {
    try {
      const result = await ipcRenderer.invoke('open-media-dialog');
      if (result.filePath) {
        loadMediaFile(result.filePath);
      }
    } catch (err) {
      console.error('Failed to open file dialog:', err);
    }
  };

  const analyzeMedia = useCallback(async () => {
    if (!file) {
      setError('Please select a media file to analyze');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setActiveStep(0);

    try {
      // Check for GPU acceleration
      const gpuAvailable = await ipcRenderer.invoke('check-gpu-acceleration');
      
      // Mock analysis for demonstration
      const mockAnalysis: MediaAnalysis = {
        assetId: `media_${Date.now()}`,
        mediaType: file.type.startsWith('video/') ? 'video' : 'image',
        duration: 180.5,
        resolution: '1920x1080',
        fps: 30,
        qualityScore: 0.88,
        scenes: [
          { 
            id: 's1', 
            type: 'intro', 
            start: 0, 
            end: 10, 
            confidence: 0.92,
            objects: ['logo', 'text'],
            dominantColors: ['#FF6B6B', '#4ECDC4']
          },
          { 
            id: 's2', 
            type: 'content', 
            start: 10, 
            end: 60, 
            confidence: 0.88,
            objects: ['person', 'background'],
            dominantColors: ['#45B7D1', '#96CEB4']
          },
          { 
            id: 's3', 
            type: 'interview', 
            start: 60, 
            end: 120, 
            confidence: 0.95,
            objects: ['person', 'microphone'],
            dominantColors: ['#FFEAA7', '#DFE6E9']
          },
          { 
            id: 's4', 
            type: 'action', 
            start: 120, 
            end: 170, 
            confidence: 0.85,
            objects: ['car', 'road', 'person'],
            dominantColors: ['#74B9FF', '#A29BFE']
          },
          { 
            id: 's5', 
            type: 'outro', 
            start: 170, 
            end: 180.5, 
            confidence: 0.90,
            objects: ['logo', 'credits'],
            dominantColors: ['#6C5CE7', '#FDCB6E']
          },
        ],
        highlights: [
          { 
            id: 'h1', 
            start: 15, 
            end: 25, 
            score: 0.92, 
            reason: 'High engagement moment',
            tags: ['engaging', 'emotional']
          },
          { 
            id: 'h2', 
            start: 75, 
            end: 85, 
            score: 0.88, 
            reason: 'Key dialogue',
            tags: ['important', 'quotable']
          },
          { 
            id: 'h3', 
            start: 125, 
            end: 135, 
            score: 0.95, 
            reason: 'Peak action',
            tags: ['exciting', 'climax']
          },
        ],
        detectedObjects: {
          'person': 15,
          'car': 3,
          'building': 8,
          'tree': 12,
          'text': 20,
          'logo': 5,
        },
        detectedBrands: ['Apple', 'Nike', 'Google', 'Microsoft'],
        uniqueFaces: 4,
        viralPotential: 0.72,
        colorPalette: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'],
        audioAnalysis: {
          hasMusic: true,
          hasSpeech: true,
          loudness: -16,
          tempo: 120,
        },
        autoChapters: [
          { title: 'Introduction', start: 0, end: 10 },
          { title: 'Main Content', start: 10, end: 60 },
          { title: 'Interview Segment', start: 60, end: 120 },
          { title: 'Action Sequence', start: 120, end: 170 },
          { title: 'Conclusion', start: 170, end: 180.5 },
        ],
        technicalMetrics: {
          bitrate: '8 Mbps',
          codec: 'H.264',
          fileSize: '256 MB',
        },
      };

      // Simulate processing steps
      const steps = ['Upload', 'Scene Detection', 'Object Analysis', 'Audio Analysis', 'Highlight Extraction'];
      for (let i = 0; i < steps.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        setActiveStep(i + 1);
      }

      setAnalysis(mockAnalysis);
      setMediaHistory(prev => [...prev, mockAnalysis]);
      
      // Save to local storage
      await ipcRenderer.invoke('save-media-analysis', mockAnalysis);
      
      if (onAnalysisComplete) {
        onAnalysisComplete(mockAnalysis);
      }

      setSnackbarMessage('Analysis complete! GPU acceleration: ' + (gpuAvailable ? 'Enabled' : 'Disabled'));
      setSnackbarOpen(true);
    } catch (err) {
      setError('Failed to analyze media. Please try again.');
      console.error('Analysis error:', err);
    } finally {
      setIsAnalyzing(false);
    }
  }, [file, onAnalysisComplete]);

  const exportAnalysis = useCallback(async () => {
    if (!analysis) return;

    try {
      await ipcRenderer.invoke('export-media-analysis', {
        analysis,
        format: exportFormat,
        includeMedia: true,
      });
      
      setSnackbarMessage(`Analysis exported as ${exportFormat.toUpperCase()}`);
      setSnackbarOpen(true);
    } catch (err) {
      console.error('Export error:', err);
    }
  }, [analysis, exportFormat]);

  const generateHighlightReel = useCallback(async () => {
    if (!analysis) return;

    try {
      await ipcRenderer.invoke('generate-highlight-reel', {
        highlights: analysis.highlights,
        outputFormat: exportFormat,
      });
      
      setSnackbarMessage('Highlight reel generated successfully');
      setSnackbarOpen(true);
    } catch (err) {
      console.error('Failed to generate highlight reel:', err);
    }
  }, [analysis, exportFormat]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const seekToTime = (time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const steps = ['Upload', 'Scene Detection', 'Object Analysis', 'Audio Analysis', 'Highlight Extraction'];

  const speedDialActions = [
    { icon: <DownloadIcon />, name: 'Export Analysis', action: exportAnalysis },
    { icon: <EditIcon />, name: 'Generate Highlights', action: generateHighlightReel },
    { icon: <ShareIcon />, name: 'Share Results', action: () => console.log('Share') },
    { icon: <SaveIcon />, name: 'Save Project', action: () => console.log('Save') },
  ];

  return (
    <Box sx={{ height: '100vh', display: 'flex' }}>
      {/* Main Content */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <Card sx={{ mb: 3, background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box>
                <Typography variant="h4" gutterBottom sx={{ color: 'white' }}>
                  <MovieIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Media Intelligence Desktop
                </Typography>
                <Typography variant="body1" sx={{ color: 'white' }}>
                  Professional media analysis with GPU acceleration
                </Typography>
              </Box>
              <Box>
                <Tooltip title="Open Media File">
                  <IconButton color="inherit" onClick={openFileDialog}>
                    <OpenIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Settings">
                  <IconButton color="inherit" onClick={() => setSettingsOpen(!settingsOpen)}>
                    <SettingsIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>
          </CardContent>
        </Card>

        {!analysis && (
          <Card sx={{ flex: 1 }}>
            <CardContent sx={{ height: '100%' }}>
              <DesktopUploadArea
                isDragging={isDragging}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="video/*,image/*"
                  style={{ display: 'none' }}
                  onChange={handleFileSelect}
                />
                <UploadIcon sx={{ fontSize: 80, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h5" gutterBottom>
                  Drop your media file here
                </Typography>
                <Typography variant="body1" color="textSecondary">
                  or click to browse files
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
                  Supports MP4, AVI, MOV, MKV, JPG, PNG, WEBP (Max 2GB)
                </Typography>
                {file && (
                  <Box mt={3}>
                    <Chip
                      icon={file.type.startsWith('video/') ? <MovieIcon /> : <ImageIcon />}
                      label={file.name}
                      onDelete={() => setFile(null)}
                      color="primary"
                      size="large"
                    />
                  </Box>
                )}
              </DesktopUploadArea>

              {file && (
                <Box mt={3}>
                  <Button
                    fullWidth
                    variant="contained"
                    color="primary"
                    size="large"
                    onClick={analyzeMedia}
                    disabled={isAnalyzing}
                    startIcon={isAnalyzing ? <CircularProgress size={20} /> : <AssessmentIcon />}
                  >
                    {isAnalyzing ? 'Analyzing Media...' : 'Analyze Media'}
                  </Button>
                </Box>
              )}

              {isAnalyzing && (
                <Box mt={3}>
                  <Stepper activeStep={activeStep}>
                    {steps.map((label) => (
                      <Step key={label}>
                        <StepLabel>{label}</StepLabel>
                      </Step>
                    ))}
                  </Stepper>
                </Box>
              )}

              {error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {error}
                </Alert>
              )}
            </CardContent>
          </Card>
        )}

        {analysis && (
          <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
            {/* Video Player */}
            {analysis.mediaType === 'video' && file && (
              <Paper sx={{ mb: 3, p: 2 }}>
                <VideoPlayer
                  ref={videoRef}
                  src={URL.createObjectURL(file)}
                  controls
                  onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
                />
                <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
                  <IconButton onClick={() => seekToTime(Math.max(0, currentTime - 10))}>
                    <SkipPreviousIcon />
                  </IconButton>
                  <IconButton onClick={() => videoRef.current?.paused ? videoRef.current?.play() : videoRef.current?.pause()}>
                    {videoRef.current?.paused ? <PlayIcon /> : <PauseIcon />}
                  </IconButton>
                  <IconButton onClick={() => seekToTime(Math.min(analysis.duration, currentTime + 10))}>
                    <SkipNextIcon />
                  </IconButton>
                  <Typography variant="body2">
                    {formatTime(currentTime)} / {formatTime(analysis.duration)}
                  </Typography>
                  <Box sx={{ flex: 1 }} />
                  <FormControl size="small">
                    <Select
                      value={playbackRate}
                      onChange={(e) => {
                        setPlaybackRate(e.target.value as number);
                        if (videoRef.current) {
                          videoRef.current.playbackRate = e.target.value as number;
                        }
                      }}
                    >
                      <MenuItem value={0.5}>0.5x</MenuItem>
                      <MenuItem value={1}>1x</MenuItem>
                      <MenuItem value={1.5}>1.5x</MenuItem>
                      <MenuItem value={2}>2x</MenuItem>
                    </Select>
                  </FormControl>
                </Box>
              </Paper>
            )}

            {/* Quality Metrics */}
            <Grid container spacing={3} sx={{ mb: 3 }}>
              <Grid item xs={12} md={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <QualityIndicator quality={analysis.qualityScore}>
                    {(analysis.qualityScore * 100).toFixed(0)}%
                  </QualityIndicator>
                  <Typography variant="h6" sx={{ mt: 1 }}>
                    Quality Score
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    {analysis.resolution} @ {analysis.fps}fps
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} md={3}>
                <Paper sx={{ p: 2 }}>
                  <Badge badgeContent={analysis.scenes.length} color="primary">
                    <TimelineIcon sx={{ fontSize: 40 }} />
                  </Badge>
                  <Typography variant="h6">Scenes</Typography>
                  <Typography variant="body2" color="textSecondary">
                    {analysis.duration}s duration
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} md={3}>
                <Paper sx={{ p: 2 }}>
                  <Badge badgeContent={analysis.highlights.length} color="secondary">
                    <HighlightIcon sx={{ fontSize: 40 }} />
                  </Badge>
                  <Typography variant="h6">Highlights</Typography>
                  <Typography variant="body2" color="textSecondary">
                    Key moments detected
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} md={3}>
                <Paper sx={{ p: 2 }}>
                  <ThumbUpIcon sx={{ fontSize: 40, color: 'success.main' }} />
                  <Typography variant="h6">Viral Potential</Typography>
                  <LinearProgress
                    variant="determinate"
                    value={analysis.viralPotential * 100}
                    sx={{ mt: 1 }}
                  />
                </Paper>
              </Grid>
            </Grid>

            {/* Scene Timeline */}
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      <TimelineIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                      Scene Timeline
                    </Typography>
                    <Timeline>
                      {analysis.scenes.map((scene, index) => (
                        <TimelineItem key={scene.id}>
                          <TimelineSeparator>
                            <TimelineDot color={scene.type === 'action' ? 'secondary' : 'primary'} />
                            {index < analysis.scenes.length - 1 && <TimelineConnector />}
                          </TimelineSeparator>
                          <TimelineContent>
                            <SceneCard 
                              isHighlight={analysis.highlights.some(h => 
                                h.start >= scene.start && h.end <= scene.end
                              )}
                              onClick={() => seekToTime(scene.start)}
                            >
                              <CardContent>
                                <Typography variant="subtitle1">
                                  {scene.type.charAt(0).toUpperCase() + scene.type.slice(1)}
                                </Typography>
                                <Typography variant="body2" color="textSecondary">
                                  {formatTime(scene.start)} - {formatTime(scene.end)}
                                </Typography>
                                <Box sx={{ mt: 1 }}>
                                  {scene.objects?.map((obj, i) => (
                                    <Chip
                                      key={i}
                                      label={obj}
                                      size="small"
                                      sx={{ mr: 0.5 }}
                                    />
                                  ))}
                                </Box>
                                <Box sx={{ display: 'flex', mt: 1 }}>
                                  {scene.dominantColors?.map((color, i) => (
                                    <Box
                                      key={i}
                                      sx={{
                                        width: 20,
                                        height: 20,
                                        backgroundColor: color,
                                        borderRadius: 1,
                                        mr: 0.5,
                                      }}
                                    />
                                  ))}
                                </Box>
                              </CardContent>
                            </SceneCard>
                          </TimelineContent>
                        </TimelineItem>
                      ))}
                    </Timeline>
                  </CardContent>
                </Card>
              </Grid>

              {/* Highlights and Analysis */}
              <Grid item xs={12} md={6}>
                <Card sx={{ mb: 2 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      <HighlightIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                      Key Highlights
                    </Typography>
                    <List>
                      {analysis.highlights.map((highlight) => (
                        <ListItem key={highlight.id}>
                          <ListItemIcon>
                            <Badge badgeContent={`${(highlight.score * 100).toFixed(0)}%`} color="secondary">
                              <PlayIcon />
                            </Badge>
                          </ListItemIcon>
                          <ListItemText
                            primary={highlight.reason}
                            secondary={
                              <>
                                {formatTime(highlight.start)} - {formatTime(highlight.end)}
                                <Box component="span" sx={{ ml: 2 }}>
                                  {highlight.tags?.map((tag, i) => (
                                    <Chip key={i} label={tag} size="small" sx={{ ml: 0.5 }} />
                                  ))}
                                </Box>
                              </>
                            }
                          />
                          <IconButton onClick={() => seekToTime(highlight.start)}>
                            <VisibilityIcon />
                          </IconButton>
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>

                {/* Technical Metrics */}
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Technical Details
                    </Typography>
                    <List dense>
                      <ListItem>
                        <ListItemText primary="Bitrate" secondary={analysis.technicalMetrics.bitrate} />
                      </ListItem>
                      <ListItem>
                        <ListItemText primary="Codec" secondary={analysis.technicalMetrics.codec} />
                      </ListItem>
                      <ListItem>
                        <ListItemText primary="File Size" secondary={analysis.technicalMetrics.fileSize} />
                      </ListItem>
                      {analysis.audioAnalysis && (
                        <>
                          <ListItem>
                            <ListItemText 
                              primary="Audio" 
                              secondary={`Music: ${analysis.audioAnalysis.hasMusic ? 'Yes' : 'No'}, Speech: ${analysis.audioAnalysis.hasSpeech ? 'Yes' : 'No'}`} 
                            />
                          </ListItem>
                          <ListItem>
                            <ListItemText 
                              primary="Loudness" 
                              secondary={`${analysis.audioAnalysis.loudness} LUFS`} 
                            />
                          </ListItem>
                        </>
                      )}
                    </List>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        )}
      </Box>

      {/* Settings Drawer */}
      <Drawer
        anchor="right"
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
      >
        <Box sx={{ width: 300, p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Analysis Settings
          </Typography>
          
          <FormControl fullWidth margin="normal">
            <InputLabel>Export Format</InputLabel>
            <Select
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value)}
              label="Export Format"
            >
              <MenuItem value="mp4">MP4</MenuItem>
              <MenuItem value="mov">MOV</MenuItem>
              <MenuItem value="avi">AVI</MenuItem>
              <MenuItem value="webm">WEBM</MenuItem>
            </Select>
          </FormControl>

          <FormControlLabel
            control={
              <Switch
                checked={enableAIEnhancement}
                onChange={(e) => setEnableAIEnhancement(e.target.checked)}
              />
            }
            label="AI Enhancement"
          />

          <Typography variant="subtitle2" sx={{ mt: 2 }}>
            GPU Acceleration
          </Typography>
          <Chip 
            label="Enabled" 
            color="success" 
            size="small" 
            icon={<SpeedIcon />}
            sx={{ mt: 1 }}
          />
        </Box>
      </Drawer>

      {/* Speed Dial Actions */}
      {analysis && (
        <SpeedDial
          ariaLabel="Media Actions"
          sx={{ position: 'fixed', bottom: 16, right: 16 }}
          icon={<SpeedDialIcon />}
        >
          {speedDialActions.map((action) => (
            <SpeedDialAction
              key={action.name}
              icon={action.icon}
              tooltipTitle={action.name}
              onClick={action.action}
            />
          ))}
        </SpeedDial>
      )}

      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMessage}
      />
    </Box>
  );
};

export default MediaIntelligenceDesktop;