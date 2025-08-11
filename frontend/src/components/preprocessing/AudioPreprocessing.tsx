import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  FormControl,
  FormControlLabel,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Slider,
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
} from '@mui/material';
import {
  CloudUpload,
  Download,
  PlayArrow,
  Pause,
  Stop,
  VolumeUp,
  GraphicEq,
  Settings,
  AutoFixHigh,
  AudioFile,
  Close,
  Refresh,
  Analytics,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import apiService from '../../services/api';

interface AudioPreprocessingConfig {
  target_sample_rate: number;
  enable_noise_reduction: boolean;
  noise_reduction_strength: number;
  enable_normalization: boolean;
  normalization_method: string;
  remove_silence: boolean;
  silence_threshold: number;
  enable_high_pass_filter: boolean;
  high_pass_cutoff: number;
  enable_low_pass_filter: boolean;
  low_pass_cutoff: number;
  output_format: string;
}

interface AudioAnalysis {
  duration: number;
  sample_rate: number;
  channels: number;
  quality_metrics: {
    snr: number;
    dynamic_range: number;
    energy: number;
    peak_level: number;
  };
  recommendations: string[];
}

interface ProcessingResult {
  task_id: string;
  status: string;
  processed_audio?: string;
  original_audio?: string;
  operations_applied: string[];
  quality_metrics: Record<string, number>;
  processing_time: number;
  sample_rate: number;
  duration: {
    original: number;
    processed: number;
  };
  metadata: Record<string, any>;
  message?: string;
}

const AudioPreprocessing: React.FC = () => {
  const [selectedAudio, setSelectedAudio] = useState<string | null>(null);
  const [processedAudio, setProcessedAudio] = useState<string | null>(null);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [config, setConfig] = useState<AudioPreprocessingConfig>({
    target_sample_rate: 16000,
    enable_noise_reduction: true,
    noise_reduction_strength: 0.7,
    enable_normalization: true,
    normalization_method: 'peak',
    remove_silence: true,
    silence_threshold: -40,
    enable_high_pass_filter: true,
    high_pass_cutoff: 80,
    enable_low_pass_filter: true,
    low_pass_cutoff: 8000,
    output_format: 'wav',
  });
  const [processing, setProcessing] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<ProcessingResult | null>(null);
  const [analysis, setAnalysis] = useState<AudioAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [presets, setPresets] = useState<Record<string, any>>({});
  const [selectedPreset, setSelectedPreset] = useState<string>('transcription_optimized');
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentAudio, setCurrentAudio] = useState<'original' | 'processed'>('original');

  const audioRef = useRef<HTMLAudioElement>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    loadPresets();
  }, []);

  const loadPresets = async () => {
    try {
      const response = await apiService.get('/api/v1/audio/presets');
      setPresets(response.data.presets);
    } catch (err) {
      console.error('Failed to load presets:', err);
    }
  };

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file && file.type.startsWith('audio/')) {
      setAudioFile(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setSelectedAudio(e.target?.result as string);
        setProcessedAudio(null);
        setResult(null);
        setAnalysis(null);
        setError(null);
      };
      reader.readAsDataURL(file);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.wav', '.mp3', '.flac', '.m4a', '.ogg'],
    },
    multiple: false,
  });

  const handlePresetChange = (preset: string) => {
    setSelectedPreset(preset);
    if (presets[preset]) {
      setConfig({ ...config, ...presets[preset] });
    }
  };

  const handleConfigChange = (key: keyof AudioPreprocessingConfig, value: any) => {
    setConfig({ ...config, [key]: value });
  };

  const analyzeAudio = async () => {
    if (!selectedAudio) return;

    try {
      setAnalyzing(true);
      setError(null);

      const base64Data = selectedAudio.split(',')[1];
      const response = await apiService.post('/api/v1/audio/analyze', {
        audio_data: base64Data,
        analysis_type: 'quality',
      });

      setAnalysis(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const processAudio = async () => {
    if (!selectedAudio) return;

    try {
      setProcessing(true);
      setError(null);

      const base64Data = selectedAudio.split(',')[1];
      const response = await apiService.post('/api/v1/audio/preprocess', {
        audio_data: base64Data,
        config: config,
      });

      const taskId = response.data.task_id;
      pollForResult(taskId);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Processing failed');
      setProcessing(false);
    }
  };

  const pollForResult = (taskId: string) => {
    pollIntervalRef.current = setInterval(async () => {
      try {
        const response = await apiService.get(`/api/v1/audio/status/${taskId}`);
        const result: ProcessingResult = response.data;

        if (result.status === 'completed') {
          setResult(result);
          setProcessedAudio(`data:audio/wav;base64,${result.processed_audio}`);
          setProcessing(false);
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
          }
        } else if (result.status === 'failed') {
          setError(result.message || 'Processing failed');
          setProcessing(false);
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
          }
        }
      } catch (err: any) {
        setError('Failed to get processing status');
        setProcessing(false);
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
        }
      }
    }, 1000);
  };

  const playAudio = (audioType: 'original' | 'processed') => {
    if (audioRef.current) {
      audioRef.current.pause();
    }

    const audioSrc = audioType === 'original' ? selectedAudio : processedAudio;
    if (audioSrc && audioRef.current) {
      audioRef.current.src = audioSrc;
      audioRef.current.play();
      setIsPlaying(true);
      setCurrentAudio(audioType);
    }
  };

  const pauseAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
    }
  };

  const stopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
    }
  };

  const downloadAudio = () => {
    if (processedAudio) {
      const link = document.createElement('a');
      link.href = processedAudio;
      link.download = 'processed_audio.wav';
      link.click();
    }
  };

  const resetProcess = () => {
    setSelectedAudio(null);
    setProcessedAudio(null);
    setAudioFile(null);
    setResult(null);
    setAnalysis(null);
    setError(null);
    setProcessing(false);
    setAnalyzing(false);
    stopAudio();
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(1);
    return `${mins}:${secs.padStart(4, '0')}`;
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Advanced Audio Preprocessing
      </Typography>

      <audio ref={audioRef} onEnded={() => setIsPlaying(false)} style={{ display: 'none' }} />

      <Grid container spacing={3}>
        {/* Upload Section */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Upload Audio
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
                <AudioFile sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
                <Typography>
                  {isDragActive
                    ? 'Drop the audio file here...'
                    : 'Drag & drop an audio file here, or click to select'}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Supports: WAV, MP3, FLAC, M4A, OGG (Max 50MB)
                </Typography>
              </Box>

              {audioFile && (
                <Box>
                  <Paper sx={{ p: 2, mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      {audioFile.name}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Size: {(audioFile.size / 1024 / 1024).toFixed(1)} MB
                    </Typography>
                    
                    <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                      <Button
                        size="small"
                        startIcon={isPlaying && currentAudio === 'original' ? <Pause /> : <PlayArrow />}
                        onClick={() => isPlaying && currentAudio === 'original' ? pauseAudio() : playAudio('original')}
                        disabled={!selectedAudio}
                      >
                        {isPlaying && currentAudio === 'original' ? 'Pause' : 'Play Original'}
                      </Button>
                      <Button
                        size="small"
                        startIcon={<Stop />}
                        onClick={stopAudio}
                        disabled={!isPlaying}
                      >
                        Stop
                      </Button>
                      <Button
                        size="small"
                        startIcon={analyzing ? <CircularProgress size={16} /> : <Analytics />}
                        onClick={analyzeAudio}
                        disabled={!selectedAudio || analyzing}
                      >
                        Analyze
                      </Button>
                    </Box>
                  </Paper>

                  {/* Audio Analysis Results */}
                  {analysis && (
                    <Paper sx={{ p: 2, mb: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Audio Analysis
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <Typography variant="body2">
                            Duration: {formatDuration(analysis.duration)}
                          </Typography>
                          <Typography variant="body2">
                            Sample Rate: {analysis.sample_rate} Hz
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2">
                            SNR: {analysis.quality_metrics.snr.toFixed(1)} dB
                          </Typography>
                          <Typography variant="body2">
                            Dynamic Range: {analysis.quality_metrics.dynamic_range.toFixed(1)} dB
                          </Typography>
                        </Grid>
                      </Grid>
                      
                      {analysis.recommendations.length > 0 && (
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="caption" display="block" gutterBottom>
                            Recommendations:
                          </Typography>
                          {analysis.recommendations.map((rec, index) => (
                            <Chip key={index} label={rec} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                          ))}
                        </Box>
                      )}
                    </Paper>
                  )}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Configuration Section */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Processing Configuration
              </Typography>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Preset</InputLabel>
                <Select
                  value={selectedPreset}
                  onChange={(e) => handlePresetChange(e.target.value)}
                  label="Preset"
                >
                  <MenuItem value="transcription_optimized">Transcription Optimized</MenuItem>
                  <MenuItem value="podcast_quality">Podcast Quality</MenuItem>
                  <MenuItem value="phone_quality">Phone Quality</MenuItem>
                  <MenuItem value="fast_processing">Fast Processing</MenuItem>
                </Select>
              </FormControl>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Target Sample Rate</InputLabel>
                <Select
                  value={config.target_sample_rate}
                  onChange={(e) => handleConfigChange('target_sample_rate', Number(e.target.value))}
                  label="Target Sample Rate"
                >
                  <MenuItem value={8000}>8 kHz (Phone Quality)</MenuItem>
                  <MenuItem value={16000}>16 kHz (Speech Recognition)</MenuItem>
                  <MenuItem value={22050}>22 kHz (Standard)</MenuItem>
                  <MenuItem value={44100}>44 kHz (CD Quality)</MenuItem>
                </Select>
              </FormControl>

              <FormControlLabel
                control={
                  <Switch
                    checked={config.enable_noise_reduction}
                    onChange={(e) => handleConfigChange('enable_noise_reduction', e.target.checked)}
                  />
                }
                label="Enable Noise Reduction"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={config.enable_normalization}
                    onChange={(e) => handleConfigChange('enable_normalization', e.target.checked)}
                  />
                }
                label="Enable Normalization"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={config.remove_silence}
                    onChange={(e) => handleConfigChange('remove_silence', e.target.checked)}
                  />
                }
                label="Remove Silence"
              />

              {config.enable_noise_reduction && (
                <Box sx={{ mt: 2 }}>
                  <Typography gutterBottom>
                    Noise Reduction Strength: {config.noise_reduction_strength}
                  </Typography>
                  <Slider
                    value={config.noise_reduction_strength}
                    onChange={(_, value) => handleConfigChange('noise_reduction_strength', value)}
                    min={0.0}
                    max={1.0}
                    step={0.1}
                    marks
                  />
                </Box>
              )}

              {config.remove_silence && (
                <Box sx={{ mt: 2 }}>
                  <Typography gutterBottom>
                    Silence Threshold: {config.silence_threshold} dB
                  </Typography>
                  <Slider
                    value={config.silence_threshold}
                    onChange={(_, value) => handleConfigChange('silence_threshold', value)}
                    min={-60}
                    max={-10}
                    step={5}
                    marks
                  />
                </Box>
              )}

              <Button
                startIcon={<Settings />}
                onClick={() => setShowAdvancedSettings(true)}
                sx={{ mt: 2 }}
              >
                Advanced Settings
              </Button>

              <Box sx={{ mt: 3 }}>
                <Button
                  variant="contained"
                  size="large"
                  fullWidth
                  onClick={processAudio}
                  disabled={!selectedAudio || processing}
                  startIcon={processing ? <CircularProgress size={20} /> : <AutoFixHigh />}
                >
                  {processing ? 'Processing...' : 'Process Audio'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Results Section */}
        {(processedAudio || error) && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">Results</Typography>
                  <Box>
                    <IconButton onClick={downloadAudio} disabled={!processedAudio}>
                      <Download />
                    </IconButton>
                    <IconButton onClick={resetProcess}>
                      <Refresh />
                    </IconButton>
                  </Box>
                </Box>

                {error && (
                  <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                  </Alert>
                )}

                {processedAudio && result && (
                  <>
                    <Paper sx={{ p: 2, mb: 2 }}>
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <Typography variant="subtitle2" gutterBottom>
                            Original Audio
                          </Typography>
                          <Typography variant="body2">
                            Duration: {formatDuration(result.duration.original)}
                          </Typography>
                          <Box sx={{ mt: 1 }}>
                            <Button
                              size="small"
                              startIcon={isPlaying && currentAudio === 'original' ? <Pause /> : <PlayArrow />}
                              onClick={() => isPlaying && currentAudio === 'original' ? pauseAudio() : playAudio('original')}
                            >
                              {isPlaying && currentAudio === 'original' ? 'Pause' : 'Play Original'}
                            </Button>
                          </Box>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="subtitle2" gutterBottom>
                            Processed Audio
                          </Typography>
                          <Typography variant="body2">
                            Duration: {formatDuration(result.duration.processed)}
                          </Typography>
                          <Typography variant="body2" color="primary">
                            Reduction: {((result.duration.original - result.duration.processed) / result.duration.original * 100).toFixed(1)}%
                          </Typography>
                          <Box sx={{ mt: 1 }}>
                            <Button
                              size="small"
                              startIcon={isPlaying && currentAudio === 'processed' ? <Pause /> : <PlayArrow />}
                              onClick={() => isPlaying && currentAudio === 'processed' ? pauseAudio() : playAudio('processed')}
                            >
                              {isPlaying && currentAudio === 'processed' ? 'Pause' : 'Play Processed'}
                            </Button>
                          </Box>
                        </Grid>
                      </Grid>
                    </Paper>

                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Processing Information:
                      </Typography>
                      <Typography variant="body2">
                        Processing Time: {result.processing_time.toFixed(2)}s
                      </Typography>
                      <Typography variant="body2">
                        Sample Rate: {result.sample_rate} Hz
                      </Typography>
                    </Box>

                    <Box sx={{ mb: 2 }}>
                      {result.operations_applied.map((op, index) => (
                        <Chip
                          key={index}
                          label={op.replace('_', ' ')}
                          size="small"
                          sx={{ mr: 0.5, mb: 0.5 }}
                        />
                      ))}
                    </Box>

                    {Object.keys(result.quality_metrics).length > 0 && (
                      <>
                        <Typography variant="subtitle2" gutterBottom>
                          Quality Metrics:
                        </Typography>
                        <Grid container spacing={1}>
                          {Object.entries(result.quality_metrics).map(([key, value]) => (
                            <Grid item xs={6} key={key}>
                              <Typography variant="body2">
                                {key.replace('_', ' ')}: {typeof value === 'number' ? value.toFixed(2) : value}
                              </Typography>
                            </Grid>
                          ))}
                        </Grid>
                      </>
                    )}
                  </>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* Advanced Settings Dialog */}
      <Dialog
        open={showAdvancedSettings}
        onClose={() => setShowAdvancedSettings(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Advanced Audio Processing Settings
          <IconButton
            sx={{ position: 'absolute', right: 8, top: 8 }}
            onClick={() => setShowAdvancedSettings(false)}
          >
            <Close />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Normalization Method</InputLabel>
                <Select
                  value={config.normalization_method}
                  onChange={(e) => handleConfigChange('normalization_method', e.target.value)}
                  label="Normalization Method"
                >
                  <MenuItem value="peak">Peak Normalization</MenuItem>
                  <MenuItem value="rms">RMS Normalization</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Output Format</InputLabel>
                <Select
                  value={config.output_format}
                  onChange={(e) => handleConfigChange('output_format', e.target.value)}
                  label="Output Format"
                >
                  <MenuItem value="wav">WAV</MenuItem>
                  <MenuItem value="flac">FLAC</MenuItem>
                  <MenuItem value="mp3">MP3</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={config.enable_high_pass_filter}
                    onChange={(e) => handleConfigChange('enable_high_pass_filter', e.target.checked)}
                  />
                }
                label="Enable High-Pass Filter"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={config.enable_low_pass_filter}
                    onChange={(e) => handleConfigChange('enable_low_pass_filter', e.target.checked)}
                  />
                }
                label="Enable Low-Pass Filter"
              />
            </Grid>

            {config.enable_high_pass_filter && (
              <Grid item xs={6}>
                <Typography gutterBottom>
                  High-Pass Cutoff: {config.high_pass_cutoff} Hz
                </Typography>
                <Slider
                  value={config.high_pass_cutoff}
                  onChange={(_, value) => handleConfigChange('high_pass_cutoff', value)}
                  min={50}
                  max={500}
                  step={10}
                />
              </Grid>
            )}

            {config.enable_low_pass_filter && (
              <Grid item xs={6}>
                <Typography gutterBottom>
                  Low-Pass Cutoff: {config.low_pass_cutoff} Hz
                </Typography>
                <Slider
                  value={config.low_pass_cutoff}
                  onChange={(_, value) => handleConfigChange('low_pass_cutoff', value)}
                  min={4000}
                  max={20000}
                  step={500}
                />
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowAdvancedSettings(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AudioPreprocessing;