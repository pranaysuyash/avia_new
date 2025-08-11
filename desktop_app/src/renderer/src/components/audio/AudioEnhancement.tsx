import React, { useState, useCallback, useRef } from 'react';
import { 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  Button, 
  Grid, 
  LinearProgress,
  Slider,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Alert,
  Tabs,
  Tab,
  Paper,
  Divider,
  IconButton,
  Tooltip,
  Badge,
  CircularProgress
} from '@mui/material';
import {
  CloudUpload,
  Mic,
  VolumeUp,
  GraphicEq,
  Download,
  Analytics,
  AutoAwesome,
  Settings,
  TrendingUp,
  Warning,
  CheckCircle,
  Error,
  Info,
  PlayArrow,
  Stop,
  Refresh
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { useDropzone } from 'react-dropzone';

const StyledCard = styled(Card)(({ theme }) => ({
  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  color: 'white',
  marginBottom: theme.spacing(3),
  borderRadius: theme.spacing(2),
}));

const UploadBox = styled(Box)(({ theme }) => ({
  border: '2px dashed #667eea',
  borderRadius: theme.spacing(2),
  padding: theme.spacing(4),
  textAlign: 'center',
  cursor: 'pointer',
  transition: 'all 0.3s',
  '&:hover': {
    borderColor: '#764ba2',
    backgroundColor: 'rgba(102, 126, 234, 0.05)',
  },
}));

const MetricCard = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  borderRadius: theme.spacing(1),
  textAlign: 'center',
  transition: 'transform 0.2s',
  '&:hover': {
    transform: 'translateY(-4px)',
    boxShadow: theme.shadows[4],
  },
}));

interface AudioQualityMetrics {
  snr_db: number;
  thd_percent: number;
  dynamic_range_db: number;
  spectral_centroid: number;
  spectral_rolloff: number;
  zero_crossing_rate: number;
  rms_energy: number;
  peak_level_db: number;
  loudness_lufs: number;
  quality_score: number;
  recommendations: string[];
}

interface EnhancementSettings {
  enable_noise_reduction: boolean;
  noise_reduction_strength: number;
  enable_normalization: boolean;
  target_loudness_lufs: number;
  enable_compression: boolean;
  compression_ratio: number;
  enable_eq: boolean;
  eq_preset: string;
  enable_declick: boolean;
  enable_dehum: boolean;
  output_format: string;
  output_sample_rate: number;
}

const AudioEnhancementDesktop: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [originalMetrics, setOriginalMetrics] = useState<AudioQualityMetrics | null>(null);
  const [enhancedMetrics, setEnhancedMetrics] = useState<AudioQualityMetrics | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [selectedPreset, setSelectedPreset] = useState('custom');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [settings, setSettings] = useState<EnhancementSettings>({
    enable_noise_reduction: true,
    noise_reduction_strength: 0.7,
    enable_normalization: true,
    target_loudness_lufs: -16.0,
    enable_compression: false,
    compression_ratio: 4.0,
    enable_eq: false,
    eq_preset: 'speech',
    enable_declick: true,
    enable_dehum: true,
    output_format: 'wav',
    output_sample_rate: 44100,
  });

  const presets = {
    podcast: {
      name: 'Podcast Optimization',
      description: 'Optimized for spoken word',
      icon: <Mic />,
      color: '#667eea',
      settings: {
        enable_noise_reduction: true,
        noise_reduction_strength: 0.8,
        enable_normalization: true,
        target_loudness_lufs: -16.0,
        enable_compression: true,
        compression_ratio: 3.0,
      },
    },
    music: {
      name: 'Music Enhancement',
      description: 'Preserve music dynamics',
      icon: <VolumeUp />,
      color: '#f093fb',
      settings: {
        enable_noise_reduction: false,
        enable_normalization: true,
        target_loudness_lufs: -14.0,
        enable_compression: false,
      },
    },
    interview: {
      name: 'Interview Cleanup',
      description: 'Clean dialogue recording',
      icon: <GraphicEq />,
      color: '#4facfe',
      settings: {
        enable_noise_reduction: true,
        noise_reduction_strength: 0.6,
        enable_normalization: true,
        target_loudness_lufs: -18.0,
      },
    },
    restoration: {
      name: 'Audio Restoration',
      description: 'Restore old recordings',
      icon: <AutoAwesome />,
      color: '#43e97b',
      settings: {
        enable_noise_reduction: true,
        noise_reduction_strength: 0.9,
        enable_normalization: true,
        target_loudness_lufs: -20.0,
        enable_declick: true,
        enable_dehum: true,
      },
    },
  };

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0]);
      setOriginalMetrics(null);
      setEnhancedMetrics(null);
      setTaskId(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac'],
    },
    maxFiles: 1,
  });

  const applyPreset = (presetKey: string) => {
    if (presetKey === 'custom') {
      setSelectedPreset('custom');
      return;
    }
    const preset = presets[presetKey as keyof typeof presets];
    if (preset) {
      setSettings((prev) => ({ ...prev, ...preset.settings }));
      setSelectedPreset(presetKey);
    }
  };

  const analyzeAudio = async () => {
    if (!selectedFile) return;

    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch('/api/v1/audio-enhancement/analyze', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        setOriginalMetrics(result.data.metrics);
      }
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const enhanceAudio = async () => {
    if (!selectedFile) return;

    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('settings', JSON.stringify(settings));

      const response = await fetch('/api/v1/audio-enhancement/enhance', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        setTaskId(result.data.task_id);
        setOriginalMetrics(result.data.original_metrics);
        setEnhancedMetrics(result.data.enhanced_metrics);
      }
    } catch (error) {
      console.error('Enhancement failed:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const downloadEnhanced = async () => {
    if (!taskId) return;

    try {
      const response = await fetch(`/api/v1/audio-enhancement/download/${taskId}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `enhanced_${selectedFile?.name || 'audio.wav'}`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const getQualityColor = (score: number) => {
    if (score >= 80) return '#4CAF50';
    if (score >= 60) return '#FFA726';
    if (score >= 40) return '#FF7043';
    return '#F44336';
  };

  return (
    <Box sx={{ p: 3, maxWidth: 1400, mx: 'auto' }}>
      <StyledCard>
        <CardContent>
          <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold' }}>
            🎧 Audio Enhancement Pipeline
          </Typography>
          <Typography variant="subtitle1">
            AI-Powered Audio Processing for Professional Quality
          </Typography>
        </CardContent>
      </StyledCard>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <Settings sx={{ mr: 1, verticalAlign: 'middle' }} />
                Enhancement Settings
              </Typography>

              <UploadBox {...getRootProps()}>
                <input {...getInputProps()} />
                <CloudUpload sx={{ fontSize: 48, color: '#667eea', mb: 2 }} />
                <Typography variant="body1" gutterBottom>
                  {isDragActive
                    ? 'Drop the audio file here...'
                    : selectedFile
                    ? selectedFile.name
                    : 'Drag & drop or click to select audio'}
                </Typography>
                {selectedFile && (
                  <Chip
                    label={`${(selectedFile.size / 1024 / 1024).toFixed(2)} MB`}
                    color="primary"
                    size="small"
                    sx={{ mt: 1 }}
                  />
                )}
              </UploadBox>

              <Divider sx={{ my: 3 }} />

              <Typography variant="subtitle2" gutterBottom>
                Enhancement Presets
              </Typography>
              <Grid container spacing={1} sx={{ mb: 3 }}>
                {Object.entries(presets).map(([key, preset]) => (
                  <Grid item xs={6} key={key}>
                    <Tooltip title={preset.description}>
                      <Button
                        fullWidth
                        variant={selectedPreset === key ? 'contained' : 'outlined'}
                        size="small"
                        startIcon={preset.icon}
                        onClick={() => applyPreset(key)}
                        sx={{
                          borderColor: preset.color,
                          color: selectedPreset === key ? 'white' : preset.color,
                          backgroundColor: selectedPreset === key ? preset.color : 'transparent',
                          '&:hover': {
                            backgroundColor: preset.color,
                            color: 'white',
                          },
                        }}
                      >
                        {preset.name.split(' ')[0]}
                      </Button>
                    </Tooltip>
                  </Grid>
                ))}
              </Grid>

              <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)} sx={{ mb: 2 }}>
                <Tab label="Noise" />
                <Tab label="Dynamics" />
                <Tab label="Output" />
              </Tabs>

              {activeTab === 0 && (
                <Box>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.enable_noise_reduction}
                        onChange={(e) =>
                          setSettings((prev) => ({
                            ...prev,
                            enable_noise_reduction: e.target.checked,
                          }))
                        }
                      />
                    }
                    label="Noise Reduction"
                  />
                  {settings.enable_noise_reduction && (
                    <Box sx={{ px: 2 }}>
                      <Typography variant="caption">
                        Strength: {(settings.noise_reduction_strength * 100).toFixed(0)}%
                      </Typography>
                      <Slider
                        value={settings.noise_reduction_strength}
                        onChange={(e, value) =>
                          setSettings((prev) => ({
                            ...prev,
                            noise_reduction_strength: value as number,
                          }))
                        }
                        min={0}
                        max={1}
                        step={0.1}
                      />
                    </Box>
                  )}
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.enable_declick}
                        onChange={(e) =>
                          setSettings((prev) => ({ ...prev, enable_declick: e.target.checked }))
                        }
                      />
                    }
                    label="Remove Clicks"
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.enable_dehum}
                        onChange={(e) =>
                          setSettings((prev) => ({ ...prev, enable_dehum: e.target.checked }))
                        }
                      />
                    }
                    label="Remove Hum"
                  />
                </Box>
              )}

              {activeTab === 1 && (
                <Box>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.enable_normalization}
                        onChange={(e) =>
                          setSettings((prev) => ({
                            ...prev,
                            enable_normalization: e.target.checked,
                          }))
                        }
                      />
                    }
                    label="Normalize Audio"
                  />
                  {settings.enable_normalization && (
                    <Box sx={{ px: 2 }}>
                      <Typography variant="caption">
                        Target: {settings.target_loudness_lufs.toFixed(1)} LUFS
                      </Typography>
                      <Slider
                        value={settings.target_loudness_lufs}
                        onChange={(e, value) =>
                          setSettings((prev) => ({
                            ...prev,
                            target_loudness_lufs: value as number,
                          }))
                        }
                        min={-30}
                        max={-6}
                        step={0.5}
                      />
                    </Box>
                  )}
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.enable_compression}
                        onChange={(e) =>
                          setSettings((prev) => ({
                            ...prev,
                            enable_compression: e.target.checked,
                          }))
                        }
                      />
                    }
                    label="Dynamic Compression"
                  />
                  {settings.enable_compression && (
                    <Box sx={{ px: 2 }}>
                      <Typography variant="caption">
                        Ratio: {settings.compression_ratio.toFixed(1)}:1
                      </Typography>
                      <Slider
                        value={settings.compression_ratio}
                        onChange={(e, value) =>
                          setSettings((prev) => ({
                            ...prev,
                            compression_ratio: value as number,
                          }))
                        }
                        min={1}
                        max={20}
                        step={0.5}
                      />
                    </Box>
                  )}
                </Box>
              )}

              {activeTab === 2 && (
                <Box>
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Output Format</InputLabel>
                    <Select
                      value={settings.output_format}
                      onChange={(e) =>
                        setSettings((prev) => ({ ...prev, output_format: e.target.value }))
                      }
                      label="Output Format"
                    >
                      <MenuItem value="wav">WAV</MenuItem>
                      <MenuItem value="mp3">MP3</MenuItem>
                      <MenuItem value="flac">FLAC</MenuItem>
                    </Select>
                  </FormControl>
                  <FormControl fullWidth>
                    <InputLabel>Sample Rate</InputLabel>
                    <Select
                      value={settings.output_sample_rate}
                      onChange={(e) =>
                        setSettings((prev) => ({
                          ...prev,
                          output_sample_rate: Number(e.target.value),
                        }))
                      }
                      label="Sample Rate"
                    >
                      <MenuItem value={22050}>22.05 kHz</MenuItem>
                      <MenuItem value={44100}>44.1 kHz</MenuItem>
                      <MenuItem value={48000}>48 kHz</MenuItem>
                    </Select>
                  </FormControl>
                </Box>
              )}

              <Box sx={{ mt: 3, display: 'flex', gap: 1 }}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<Analytics />}
                  onClick={analyzeAudio}
                  disabled={!selectedFile || isProcessing}
                >
                  Analyze
                </Button>
                <Button
                  fullWidth
                  variant="contained"
                  startIcon={isProcessing ? <CircularProgress size={20} /> : <AutoAwesome />}
                  onClick={enhanceAudio}
                  disabled={!selectedFile || isProcessing}
                >
                  Enhance
                </Button>
              </Box>

              {taskId && (
                <Button
                  fullWidth
                  variant="outlined"
                  color="success"
                  startIcon={<Download />}
                  onClick={downloadEnhanced}
                  sx={{ mt: 1 }}
                >
                  Download Enhanced
                </Button>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <GraphicEq sx={{ mr: 1, verticalAlign: 'middle' }} />
                Enhancement Results
              </Typography>

              {!originalMetrics && !enhancedMetrics ? (
                <Box sx={{ textAlign: 'center', py: 8 }}>
                  <VolumeUp sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary">
                    Upload and analyze an audio file to see quality metrics
                  </Typography>
                </Box>
              ) : (
                <>
                  {enhancedMetrics ? (
                    <>
                      <Grid container spacing={2}>
                        <Grid item xs={12} sm={6}>
                          <Typography variant="subtitle2" gutterBottom>
                            Original Audio
                          </Typography>
                          <Grid container spacing={1}>
                            <Grid item xs={6}>
                              <MetricCard elevation={2}>
                                <Typography variant="h4" sx={{ color: getQualityColor(originalMetrics!.quality_score) }}>
                                  {originalMetrics!.quality_score.toFixed(0)}
                                </Typography>
                                <Typography variant="caption">Quality Score</Typography>
                              </MetricCard>
                            </Grid>
                            <Grid item xs={6}>
                              <MetricCard elevation={2}>
                                <Typography variant="h4">{originalMetrics!.snr_db.toFixed(1)}</Typography>
                                <Typography variant="caption">SNR (dB)</Typography>
                              </MetricCard>
                            </Grid>
                            <Grid item xs={6}>
                              <MetricCard elevation={2}>
                                <Typography variant="h4">{originalMetrics!.loudness_lufs.toFixed(1)}</Typography>
                                <Typography variant="caption">Loudness (LUFS)</Typography>
                              </MetricCard>
                            </Grid>
                            <Grid item xs={6}>
                              <MetricCard elevation={2}>
                                <Typography variant="h4">{originalMetrics!.dynamic_range_db.toFixed(1)}</Typography>
                                <Typography variant="caption">Dynamic Range</Typography>
                              </MetricCard>
                            </Grid>
                          </Grid>
                        </Grid>

                        <Grid item xs={12} sm={6}>
                          <Typography variant="subtitle2" gutterBottom>
                            Enhanced Audio
                            <Chip
                              icon={<TrendingUp />}
                              label="Improved"
                              color="success"
                              size="small"
                              sx={{ ml: 1 }}
                            />
                          </Typography>
                          <Grid container spacing={1}>
                            <Grid item xs={6}>
                              <MetricCard elevation={2}>
                                <Typography variant="h4" sx={{ color: getQualityColor(enhancedMetrics.quality_score) }}>
                                  {enhancedMetrics.quality_score.toFixed(0)}
                                  {enhancedMetrics.quality_score > originalMetrics!.quality_score && (
                                    <TrendingUp sx={{ ml: 1, color: '#4CAF50', fontSize: 20 }} />
                                  )}
                                </Typography>
                                <Typography variant="caption">Quality Score</Typography>
                              </MetricCard>
                            </Grid>
                            <Grid item xs={6}>
                              <MetricCard elevation={2}>
                                <Typography variant="h4">
                                  {enhancedMetrics.snr_db.toFixed(1)}
                                  {enhancedMetrics.snr_db > originalMetrics!.snr_db && (
                                    <TrendingUp sx={{ ml: 1, color: '#4CAF50', fontSize: 20 }} />
                                  )}
                                </Typography>
                                <Typography variant="caption">SNR (dB)</Typography>
                              </MetricCard>
                            </Grid>
                            <Grid item xs={6}>
                              <MetricCard elevation={2}>
                                <Typography variant="h4">{enhancedMetrics.loudness_lufs.toFixed(1)}</Typography>
                                <Typography variant="caption">Loudness (LUFS)</Typography>
                              </MetricCard>
                            </Grid>
                            <Grid item xs={6}>
                              <MetricCard elevation={2}>
                                <Typography variant="h4">{enhancedMetrics.dynamic_range_db.toFixed(1)}</Typography>
                                <Typography variant="caption">Dynamic Range</Typography>
                              </MetricCard>
                            </Grid>
                          </Grid>
                        </Grid>
                      </Grid>

                      <Paper sx={{ p: 2, mt: 3, bgcolor: '#E8F5E9' }}>
                        <Typography variant="h6" gutterBottom>
                          Overall Improvement
                        </Typography>
                        <Typography variant="h3" sx={{ color: '#4CAF50' }}>
                          +{(enhancedMetrics.quality_score - originalMetrics!.quality_score).toFixed(1)} points
                        </Typography>
                      </Paper>
                    </>
                  ) : originalMetrics ? (
                    <Grid container spacing={2}>
                      <Grid item xs={12} sm={3}>
                        <MetricCard elevation={2}>
                          <Typography variant="h4" sx={{ color: getQualityColor(originalMetrics.quality_score) }}>
                            {originalMetrics.quality_score.toFixed(0)}
                          </Typography>
                          <Typography variant="caption">Quality Score</Typography>
                        </MetricCard>
                      </Grid>
                      <Grid item xs={12} sm={3}>
                        <MetricCard elevation={2}>
                          <Typography variant="h4">{originalMetrics.snr_db.toFixed(1)}</Typography>
                          <Typography variant="caption">SNR (dB)</Typography>
                        </MetricCard>
                      </Grid>
                      <Grid item xs={12} sm={3}>
                        <MetricCard elevation={2}>
                          <Typography variant="h4">{originalMetrics.loudness_lufs.toFixed(1)}</Typography>
                          <Typography variant="caption">Loudness (LUFS)</Typography>
                        </MetricCard>
                      </Grid>
                      <Grid item xs={12} sm={3}>
                        <MetricCard elevation={2}>
                          <Typography variant="h4">{originalMetrics.dynamic_range_db.toFixed(1)}</Typography>
                          <Typography variant="caption">Dynamic Range</Typography>
                        </MetricCard>
                      </Grid>
                    </Grid>
                  ) : null}

                  {originalMetrics?.recommendations && originalMetrics.recommendations.length > 0 && (
                    <Box sx={{ mt: 3 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        <Info sx={{ mr: 1, verticalAlign: 'middle' }} />
                        Recommendations
                      </Typography>
                      {originalMetrics.recommendations.map((rec, idx) => (
                        <Alert severity="info" sx={{ mb: 1 }} key={idx}>
                          {rec}
                        </Alert>
                      ))}
                    </Box>
                  )}
                </>
              )}

              {isProcessing && (
                <Box sx={{ mt: 3 }}>
                  <LinearProgress />
                  <Typography variant="body2" sx={{ mt: 1, textAlign: 'center' }}>
                    Processing audio... This may take a few moments.
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AudioEnhancementDesktop;