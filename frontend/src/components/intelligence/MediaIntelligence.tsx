/**
 * Media Intelligence Component
 * Video and image analysis with scene detection and highlights
 */

import React, { useState, useCallback, useRef } from 'react';
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
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { Timeline, TimelineItem, TimelineSeparator, TimelineConnector, TimelineContent, TimelineDot } from '@mui/lab';

// Styled components
const UploadArea = styled(Paper)(({ theme, isDragging }: any) => ({
  padding: theme.spacing(4),
  textAlign: 'center',
  border: `2px dashed ${isDragging ? theme.palette.primary.main : theme.palette.divider}`,
  backgroundColor: isDragging ? theme.palette.action.hover : theme.palette.background.paper,
  cursor: 'pointer',
  transition: 'all 0.3s',
  '&:hover': {
    borderColor: theme.palette.primary.main,
    backgroundColor: theme.palette.action.hover,
  },
}));

const SceneCard = styled(Card)(({ theme, isHighlight }: any) => ({
  marginBottom: theme.spacing(2),
  border: isHighlight ? `2px solid ${theme.palette.secondary.main}` : 'none',
  background: isHighlight 
    ? `linear-gradient(135deg, ${theme.palette.secondary.light}20 0%, ${theme.palette.secondary.main}20 100%)`
    : theme.palette.background.paper,
}));

const QualityIndicator = styled(Box)(({ theme, quality }: any) => ({
  width: 60,
  height: 60,
  borderRadius: '50%',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: '1.2rem',
  fontWeight: 'bold',
  color: 'white',
  background: quality > 0.8 
    ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
    : quality > 0.6
    ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
    : 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
}));

const ThumbnailContainer = styled(Box)({
  position: 'relative',
  cursor: 'pointer',
  '&:hover .overlay': {
    opacity: 1,
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
}

interface Highlight {
  id: string;
  start: number;
  end: number;
  score: number;
  reason: string;
  thumbnail?: string;
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
  autoChapters: Array<{
    title: string;
    start: number;
    end: number;
  }>;
}

interface MediaIntelligenceProps {
  apiEndpoint?: string;
  onAnalysisComplete?: (analysis: MediaAnalysis) => void;
}

const MediaIntelligence: React.FC<MediaIntelligenceProps> = ({
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
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const analyzeMedia = useCallback(async () => {
    if (!file) {
      setError('Please select a media file to analyze');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setActiveStep(0);

    try {
      // Mock analysis for demonstration
      const mockAnalysis: MediaAnalysis = {
        assetId: `media_${Date.now()}`,
        mediaType: file.type.startsWith('video/') ? 'video' : 'image',
        duration: 180.5,
        resolution: '1920x1080',
        fps: 30,
        qualityScore: 0.88,
        scenes: [
          { id: 's1', type: 'intro', start: 0, end: 10, confidence: 0.92 },
          { id: 's2', type: 'content', start: 10, end: 60, confidence: 0.88 },
          { id: 's3', type: 'interview', start: 60, end: 120, confidence: 0.95 },
          { id: 's4', type: 'action', start: 120, end: 170, confidence: 0.85 },
          { id: 's5', type: 'outro', start: 170, end: 180.5, confidence: 0.90 },
        ],
        highlights: [
          { id: 'h1', start: 15, end: 25, score: 0.92, reason: 'High engagement moment' },
          { id: 'h2', start: 75, end: 85, score: 0.88, reason: 'Key dialogue' },
          { id: 'h3', start: 125, end: 135, score: 0.95, reason: 'Peak action' },
        ],
        detectedObjects: {
          'person': 15,
          'car': 3,
          'building': 8,
          'tree': 12,
        },
        detectedBrands: ['Apple', 'Nike', 'Google'],
        uniqueFaces: 4,
        viralPotential: 0.72,
        colorPalette: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'],
        autoChapters: [
          { title: 'Introduction', start: 0, end: 10 },
          { title: 'Main Content', start: 10, end: 60 },
          { title: 'Interview Segment', start: 60, end: 120 },
          { title: 'Action Sequence', start: 120, end: 170 },
          { title: 'Conclusion', start: 170, end: 180.5 },
        ],
      };

      // Simulate processing steps
      for (let i = 0; i < 4; i++) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        setActiveStep(i + 1);
      }

      setAnalysis(mockAnalysis);
      
      if (onAnalysisComplete) {
        onAnalysisComplete(mockAnalysis);
      }
    } catch (err) {
      setError('Failed to analyze media. Please try again.');
      console.error('Analysis error:', err);
    } finally {
      setIsAnalyzing(false);
    }
  }, [file, onAnalysisComplete]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const exportAnalysis = useCallback(() => {
    if (!analysis) return;

    const dataStr = JSON.stringify(analysis, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `media_analysis_${analysis.assetId}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  }, [analysis]);

  const steps = ['Upload', 'Scene Detection', 'Object Analysis', 'Highlight Extraction', 'Complete'];

  return (
    <Box>
      <Card sx={{ mb: 3, background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
        <CardContent>
          <Typography variant="h4" gutterBottom sx={{ color: 'white' }}>
            <MovieIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Media Intelligence
          </Typography>
          <Typography variant="body1" sx={{ color: 'white' }}>
            Analyze videos and images to detect scenes, extract highlights, and identify objects
          </Typography>
        </CardContent>
      </Card>

      {!analysis && (
        <Card>
          <CardContent>
            <UploadArea
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
              <UploadIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Drop your media file here or click to browse
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Supports MP4, AVI, MOV, JPG, PNG (Max 500MB)
              </Typography>
              {file && (
                <Box mt={2}>
                  <Chip
                    icon={file.type.startsWith('video/') ? <MovieIcon /> : <ImageIcon />}
                    label={file.name}
                    onDelete={() => setFile(null)}
                    color="primary"
                  />
                </Box>
              )}
            </UploadArea>

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
        <>
          <Grid container spacing={3}>
            <Grid item xs={12} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <QualityIndicator quality={analysis.qualityScore}>
                  {(analysis.qualityScore * 100).toFixed(0)}%
                </QualityIndicator>
                <Typography variant="h6" sx={{ mt: 1 }}>
                  Quality Score
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

          <Grid container spacing={3} sx={{ mt: 2 }}>
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
                          >
                            <CardContent>
                              <Typography variant="subtitle1">
                                {scene.type.charAt(0).toUpperCase() + scene.type.slice(1)}
                              </Typography>
                              <Typography variant="body2" color="textSecondary">
                                {formatTime(scene.start)} - {formatTime(scene.end)}
                              </Typography>
                              <Chip
                                size="small"
                                label={`${(scene.confidence * 100).toFixed(0)}% confidence`}
                                sx={{ mt: 1 }}
                              />
                            </CardContent>
                          </SceneCard>
                        </TimelineContent>
                      </TimelineItem>
                    ))}
                  </Timeline>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
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
                          secondary={`${formatTime(highlight.start)} - ${formatTime(highlight.end)}`}
                        />
                        <IconButton onClick={() => setPreviewDialogOpen(true)}>
                          <VisibilityIcon />
                        </IconButton>
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Grid container spacing={3} sx={{ mt: 2 }}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    <FaceIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Detected Objects
                  </Typography>
                  {Object.entries(analysis.detectedObjects).map(([object, count]) => (
                    <Box key={object} sx={{ mb: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">{object}</Typography>
                        <Typography variant="body2" fontWeight="bold">{count}</Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={(count / Math.max(...Object.values(analysis.detectedObjects))) * 100}
                      />
                    </Box>
                  ))}
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    <LabelIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Brands Detected
                  </Typography>
                  <Box sx={{ mt: 2 }}>
                    {analysis.detectedBrands.map((brand) => (
                      <Chip
                        key={brand}
                        label={brand}
                        sx={{ mr: 1, mb: 1 }}
                        variant="outlined"
                      />
                    ))}
                  </Box>
                  <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
                    {analysis.uniqueFaces} unique faces detected
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    <ColorIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Color Palette
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 2 }}>
                    {analysis.colorPalette.map((color, index) => (
                      <Box
                        key={index}
                        sx={{
                          width: 40,
                          height: 40,
                          backgroundColor: color,
                          borderRadius: 1,
                          border: '2px solid #fff',
                          boxShadow: 1,
                        }}
                      />
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
            <Button
              variant="contained"
              startIcon={<DownloadIcon />}
              onClick={exportAnalysis}
            >
              Export Analysis
            </Button>
            <Button
              variant="outlined"
              startIcon={<EditIcon />}
            >
              Generate Summary Video
            </Button>
            <Button
              variant="outlined"
              startIcon={<ShareIcon />}
            >
              Share Results
            </Button>
          </Box>
        </>
      )}
    </Box>
  );
};

export default MediaIntelligence;