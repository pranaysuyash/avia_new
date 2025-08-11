import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Stepper,
  Step,
  StepLabel,
  LinearProgress,
  Typography,
  Button,
  Container,
  Divider,
  Chip,
  IconButton,
  Alert,
  Tooltip,
  Card,
  CardContent,
  useTheme,
  alpha,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  Assessment as AssessmentIcon,
  Tune as TuneIcon,
  Transcribe as TranscribeIcon,
  Analytics as AnalyticsIcon,
  PlayArrow as PlayArrowIcon,
  Stop as StopIcon,
  Pause as PauseIcon,
  GetApp as DownloadIcon,
  Share as ShareIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { WaveformVisualizer } from './WaveformVisualizer';
import { ProcessingMetrics } from './ProcessingMetrics';
import { QualityAssessment } from './QualityAssessment';
import { FileUploadZone } from './FileUploadZone';
import { ProcessingOptions } from './ProcessingOptions';
import { ResultsSummary } from './ResultsSummary';
import { ExportOptions } from './ExportOptions';
import { useAudioProcessing } from '../../hooks/useAudioProcessing';
import { useWebSocket } from '../../hooks/useWebSocket';
import { ProcessingStatus, AudioFile, ProcessingResult } from '../../types';

interface AudioProcessingHubProps {
  onProcessComplete?: (result: ProcessingResult) => void;
  brandConfig?: any;
}

export const AudioProcessingHub: React.FC<AudioProcessingHubProps> = ({
  onProcessComplete,
  brandConfig,
}) => {
  const theme = useTheme();
  const [activeStep, setActiveStep] = useState(0);
  const [selectedFiles, setSelectedFiles] = useState<AudioFile[]>([]);
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus>({
    stage: 'idle',
    progress: 0,
    metrics: {},
  });
  const [results, setResults] = useState<ProcessingResult | null>(null);
  const [processingOptions, setProcessingOptions] = useState({
    enhance: true,
    transcribe: true,
    extractEntities: true,
    generateSummary: true,
    detectSpeakers: true,
  });

  const { processAudio, isProcessing } = useAudioProcessing();
  const { data: realtimeData } = useWebSocket('/ws/processing');

  const steps = [
    { label: 'Upload', icon: <CloudUploadIcon /> },
    { label: 'Quality Check', icon: <AssessmentIcon /> },
    { label: 'Enhancement', icon: <TuneIcon /> },
    { label: 'Transcription', icon: <TranscribeIcon /> },
    { label: 'Analysis', icon: <AnalyticsIcon /> },
  ];

  useEffect(() => {
    if (realtimeData) {
      setProcessingStatus(realtimeData);
      
      // Update active step based on processing stage
      const stageToStep: Record<string, number> = {
        'uploading': 0,
        'quality_check': 1,
        'enhancing': 2,
        'transcribing': 3,
        'analyzing': 4,
      };
      
      if (realtimeData.stage in stageToStep) {
        setActiveStep(stageToStep[realtimeData.stage]);
      }
    }
  }, [realtimeData]);

  const handleFileSelect = useCallback((files: File[]) => {
    const audioFiles = files.map(file => ({
      id: `file-${Date.now()}-${Math.random()}`,
      file,
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'pending' as const,
    }));
    setSelectedFiles(audioFiles);
  }, []);

  const startProcessing = async () => {
    if (selectedFiles.length === 0) return;

    for (const audioFile of selectedFiles) {
      try {
        const result = await processAudio(audioFile.file, processingOptions);
        setResults(result);
        if (onProcessComplete) {
          onProcessComplete(result);
        }
      } catch (error) {
        console.error('Processing error:', error);
      }
    }
  };

  const getScoreColor = (score: number): string => {
    if (score >= 80) return theme.palette.success.main;
    if (score >= 60) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    }
    return `${minutes}m ${secs}s`;
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: `linear-gradient(180deg, ${alpha(theme.palette.primary.light, 0.05)} 0%, ${alpha(
          theme.palette.primary.main,
          0.02
        )} 100%)`,
      }}
    >
      {/* Enterprise Header */}
      <Paper
        elevation={0}
        sx={{
          borderRadius: 0,
          background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
          color: 'white',
          p: 3,
        }}
      >
        <Grid container alignItems="center" spacing={3}>
          <Grid item xs={12} md={8}>
            <Typography variant="h4" fontWeight="bold">
              Audio Intelligence Suite
            </Typography>
            <Typography variant="subtitle1" sx={{ opacity: 0.9, mt: 1 }}>
              Enterprise-Grade Audio Processing Pipeline
            </Typography>
          </Grid>
          <Grid item xs={12} md={4}>
            {processingStatus.metrics && (
              <ProcessingMetrics metrics={processingStatus.metrics} compact />
            )}
          </Grid>
        </Grid>
      </Paper>

      {/* Main Processing Area */}
      <Container maxWidth="xl" sx={{ mt: 4, pb: 4 }}>
        <Grid container spacing={3}>
          {/* Left Panel - Upload and Controls */}
          <Grid item xs={12} lg={3}>
            <Paper 
              elevation={2}
              sx={{ 
                p: 3, 
                height: '100%',
                background: theme.palette.background.paper,
                borderRadius: 2,
              }}
            >
              <Typography variant="h6" gutterBottom>
                File Upload
              </Typography>
              
              <FileUploadZone
                onFileSelect={handleFileSelect}
                accept="audio/*,video/*"
                maxSize={5000000000} // 5GB
                multiple
                dragDropEnabled
              />

              <Divider sx={{ my: 3 }} />

              <Typography variant="h6" gutterBottom>
                Processing Options
              </Typography>
              
              <ProcessingOptions
                options={processingOptions}
                onChange={setProcessingOptions}
              />

              <Box sx={{ mt: 3 }}>
                <Button
                  fullWidth
                  variant="contained"
                  size="large"
                  startIcon={<PlayArrowIcon />}
                  onClick={startProcessing}
                  disabled={!selectedFiles.length || isProcessing}
                  sx={{
                    background: `linear-gradient(45deg, ${theme.palette.primary.main} 30%, ${theme.palette.primary.light} 90%)`,
                    boxShadow: '0 3px 5px 2px rgba(33, 203, 243, .3)',
                    '&:hover': {
                      background: `linear-gradient(45deg, ${theme.palette.primary.dark} 30%, ${theme.palette.primary.main} 90%)`,
                    },
                  }}
                >
                  Start Processing
                </Button>
              </Box>
            </Paper>
          </Grid>

          {/* Center Panel - Visualization and Progress */}
          <Grid item xs={12} lg={6}>
            <Paper 
              elevation={2}
              sx={{ 
                p: 3, 
                minHeight: 600,
                background: theme.palette.background.paper,
                borderRadius: 2,
              }}
            >
              {/* Progress Stepper */}
              <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 4 }}>
                {steps.map((step, index) => (
                  <Step key={step.label}>
                    <StepLabel
                      StepIconProps={{
                        icon: step.icon,
                      }}
                    >
                      {step.label}
                    </StepLabel>
                  </Step>
                ))}
              </Stepper>

              {/* Waveform Visualization */}
              {selectedFiles.length > 0 && (
                <Box sx={{ mt: 4, position: 'relative' }}>
                  <WaveformVisualizer
                    audioUrl={selectedFiles[0]?.file ? URL.createObjectURL(selectedFiles[0].file) : ''}
                    progress={processingStatus.progress}
                    height={200}
                    responsive
                  />

                  {isProcessing && (
                    <LinearProgress
                      variant="determinate"
                      value={processingStatus.progress}
                      sx={{
                        position: 'absolute',
                        bottom: 0,
                        left: 0,
                        right: 0,
                        height: 6,
                        borderRadius: 3,
                      }}
                    />
                  )}
                </Box>
              )}

              {/* Quality Metrics Dashboard */}
              {processingStatus.metrics && (
                <Grid container spacing={2} sx={{ mt: 3 }}>
                  <Grid item xs={6} md={3}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography color="textSecondary" gutterBottom variant="caption">
                          Audio Quality
                        </Typography>
                        <Typography variant="h5" component="div">
                          {processingStatus.metrics.quality?.overall || 0}%
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography color="textSecondary" gutterBottom variant="caption">
                          Clarity Score
                        </Typography>
                        <Typography 
                          variant="h5" 
                          component="div"
                          sx={{ color: getScoreColor(processingStatus.metrics.quality?.clarity || 0) }}
                        >
                          {processingStatus.metrics.quality?.clarity || 0}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography color="textSecondary" gutterBottom variant="caption">
                          Noise Level
                        </Typography>
                        <Typography variant="h5" component="div">
                          {processingStatus.metrics.quality?.noise || 0} dB
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography color="textSecondary" gutterBottom variant="caption">
                          Duration
                        </Typography>
                        <Typography variant="h5" component="div">
                          {formatDuration(processingStatus.metrics.duration || 0)}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              )}

              {/* Processing Status Messages */}
              {isProcessing && (
                <Alert severity="info" sx={{ mt: 3 }}>
                  {processingStatus.message || 'Processing audio file...'}
                </Alert>
              )}
            </Paper>
          </Grid>

          {/* Right Panel - Results and Analytics */}
          <Grid item xs={12} lg={3}>
            <Paper 
              elevation={2}
              sx={{ 
                p: 3, 
                height: '100%',
                background: theme.palette.background.paper,
                borderRadius: 2,
              }}
            >
              <Typography variant="h6" gutterBottom>
                Processing Results
              </Typography>

              {results ? (
                <>
                  <ResultsSummary
                    transcription={results.transcription}
                    entities={results.entities}
                    sentiment={results.sentiment}
                    keywords={results.keywords}
                    summary={results.summary}
                  />

                  <Divider sx={{ my: 2 }} />

                  <ExportOptions
                    results={results}
                    formats={['JSON', 'CSV', 'PDF', 'DOCX']}
                    onExport={(format) => console.log('Export to', format)}
                  />
                </>
              ) : (
                <Typography variant="body2" color="textSecondary">
                  Results will appear here after processing
                </Typography>
              )}
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};
