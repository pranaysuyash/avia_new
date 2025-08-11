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
} from '@mui/material';
import {
  CloudUpload,
  Download,
  Compare,
  Settings,
  AutoFixHigh,
  ImageSearch,
  Close,
  Refresh,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import apiService from '../../services/api';

interface PreprocessingConfig {
  enable_denoising: boolean;
  denoise_method: string;
  denoise_strength: number;
  auto_contrast: boolean;
  contrast_factor: number;
  enable_sharpening: boolean;
  sharpen_method: string;
  sharpen_strength: number;
  auto_deskew: boolean;
  auto_rotate: boolean;
  perspective_correction: boolean;
  upscale_factor: number;
  auto_threshold: boolean;
  threshold_method: string;
  remove_borders: boolean;
  output_format: string;
}

interface ProcessingResult {
  task_id: string;
  status: string;
  processed_image?: string;
  original_image?: string;
  operations_applied: string[];
  quality_metrics: Record<string, number>;
  processing_time: number;
  metadata: Record<string, any>;
  message?: string;
}

const ImagePreprocessing: React.FC = () => {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [processedImage, setProcessedImage] = useState<string | null>(null);
  const [config, setConfig] = useState<PreprocessingConfig>({
    enable_denoising: true,
    denoise_method: 'bilateral',
    denoise_strength: 0.5,
    auto_contrast: true,
    contrast_factor: 1.2,
    enable_sharpening: true,
    sharpen_method: 'unsharp_mask',
    sharpen_strength: 0.5,
    auto_deskew: true,
    auto_rotate: true,
    perspective_correction: false,
    upscale_factor: 2.0,
    auto_threshold: true,
    threshold_method: 'otsu',
    remove_borders: true,
    output_format: 'RGB',
  });
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState<ProcessingResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [presets, setPresets] = useState<Record<string, any>>({});
  const [selectedPreset, setSelectedPreset] = useState<string>('default');
  const [showComparison, setShowComparison] = useState(false);
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Load presets on component mount
  React.useEffect(() => {
    loadPresets();
  }, []);

  const loadPresets = async () => {
    try {
      const response = await apiService.get('/api/v1/image/presets');
      setPresets(response.data.presets);
    } catch (err) {
      console.error('Failed to load presets:', err);
    }
  };

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setSelectedImage(e.target?.result as string);
        setProcessedImage(null);
        setResult(null);
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

  const handlePresetChange = (preset: string) => {
    setSelectedPreset(preset);
    if (presets[preset]) {
      setConfig({ ...config, ...presets[preset] });
    }
  };

  const handleConfigChange = (key: keyof PreprocessingConfig, value: any) => {
    setConfig({ ...config, [key]: value });
  };

  const processImage = async () => {
    if (!selectedImage) return;

    try {
      setProcessing(true);
      setError(null);

      // Extract base64 data
      const base64Data = selectedImage.split(',')[1];

      const response = await apiService.post('/api/v1/image/preprocess', {
        image_data: base64Data,
        config: config,
      });

      const taskId = response.data.task_id;
      
      // Start polling for result
      pollForResult(taskId);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Processing failed');
      setProcessing(false);
    }
  };

  const pollForResult = (taskId: string) => {
    pollIntervalRef.current = setInterval(async () => {
      try {
        const response = await apiService.get(`/api/v1/image/status/${taskId}`);
        const result: ProcessingResult = response.data;

        if (result.status === 'completed') {
          setResult(result);
          setProcessedImage(`data:image/png;base64,${result.processed_image}`);
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

  const downloadImage = () => {
    if (processedImage) {
      const link = document.createElement('a');
      link.href = processedImage;
      link.download = 'processed_image.png';
      link.click();
    }
  };

  const resetProcess = () => {
    setSelectedImage(null);
    setProcessedImage(null);
    setResult(null);
    setError(null);
    setProcessing(false);
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Advanced Image Preprocessing
      </Typography>

      <Grid container spacing={3}>
        {/* Upload Section */}
        <Grid item xs={12} md={6}>
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
                    Original Image:
                  </Typography>
                  <img
                    src={selectedImage}
                    alt="Original"
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
                  <MenuItem value="default">Default</MenuItem>
                  <MenuItem value="ocr_optimized">OCR Optimized</MenuItem>
                  <MenuItem value="high_quality">High Quality</MenuItem>
                  <MenuItem value="fast_processing">Fast Processing</MenuItem>
                </Select>
              </FormControl>

              {/* Basic Settings */}
              <FormControlLabel
                control={
                  <Switch
                    checked={config.enable_denoising}
                    onChange={(e) => handleConfigChange('enable_denoising', e.target.checked)}
                  />
                }
                label="Enable Denoising"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={config.auto_contrast}
                    onChange={(e) => handleConfigChange('auto_contrast', e.target.checked)}
                  />
                }
                label="Auto Contrast"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={config.enable_sharpening}
                    onChange={(e) => handleConfigChange('enable_sharpening', e.target.checked)}
                  />
                }
                label="Enable Sharpening"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={config.auto_deskew}
                    onChange={(e) => handleConfigChange('auto_deskew', e.target.checked)}
                  />
                }
                label="Auto Deskew"
              />

              <Box sx={{ mt: 2 }}>
                <Typography gutterBottom>Upscale Factor: {config.upscale_factor}x</Typography>
                <Slider
                  value={config.upscale_factor}
                  onChange={(_, value) => handleConfigChange('upscale_factor', value)}
                  min={1.0}
                  max={3.0}
                  step={0.1}
                  marks
                />
              </Box>

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
                  onClick={processImage}
                  disabled={!selectedImage || processing}
                  startIcon={processing ? <CircularProgress size={20} /> : <AutoFixHigh />}
                >
                  {processing ? 'Processing...' : 'Process Image'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Results Section */}
        {(processedImage || error) && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">Results</Typography>
                  <Box>
                    <IconButton onClick={() => setShowComparison(true)} disabled={!processedImage}>
                      <Compare />
                    </IconButton>
                    <IconButton onClick={downloadImage} disabled={!processedImage}>
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

                {processedImage && (
                  <>
                    <img
                      src={processedImage}
                      alt="Processed"
                      style={{
                        width: '100%',
                        maxHeight: 400,
                        objectFit: 'contain',
                        border: '1px solid #ccc',
                        borderRadius: 4,
                        marginBottom: 16,
                      }}
                    />

                    {result && (
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>
                          Processing Information:
                        </Typography>
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="body2">
                            Processing Time: {result.processing_time.toFixed(2)}s
                          </Typography>
                          <Typography variant="body2">
                            Operations: {result.operations_applied.length}
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
                              Quality Improvements:
                            </Typography>
                            {Object.entries(result.quality_metrics).map(([key, value]) => (
                              <Box key={key} sx={{ mb: 1 }}>
                                <Typography variant="body2">
                                  {key.replace('_', ' ')}: {value > 0 ? '+' : ''}{value.toFixed(1)}%
                                </Typography>
                                <LinearProgress
                                  variant="determinate"
                                  value={Math.min(100, Math.abs(value))}
                                  color={value > 0 ? 'success' : 'warning'}
                                  sx={{ height: 4 }}
                                />
                              </Box>
                            ))}
                          </>
                        )}
                      </Box>
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
          Advanced Preprocessing Settings
          <IconButton
            sx={{ position: 'absolute', right: 8, top: 8 }}
            onClick={() => setShowAdvancedSettings(false)}
          >
            <Close />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Denoise Method</InputLabel>
                <Select
                  value={config.denoise_method}
                  onChange={(e) => handleConfigChange('denoise_method', e.target.value)}
                  label="Denoise Method"
                >
                  <MenuItem value="bilateral">Bilateral</MenuItem>
                  <MenuItem value="gaussian">Gaussian</MenuItem>
                  <MenuItem value="median">Median</MenuItem>
                  <MenuItem value="nlm">Non-Local Means</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Sharpen Method</InputLabel>
                <Select
                  value={config.sharpen_method}
                  onChange={(e) => handleConfigChange('sharpen_method', e.target.value)}
                  label="Sharpen Method"
                >
                  <MenuItem value="unsharp_mask">Unsharp Mask</MenuItem>
                  <MenuItem value="kernel">Kernel</MenuItem>
                  <MenuItem value="adaptive">Adaptive</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <Typography gutterBottom>Denoise Strength: {config.denoise_strength}</Typography>
              <Slider
                value={config.denoise_strength}
                onChange={(_, value) => handleConfigChange('denoise_strength', value)}
                min={0.0}
                max={1.0}
                step={0.1}
              />
            </Grid>
            <Grid item xs={6}>
              <Typography gutterBottom>Sharpen Strength: {config.sharpen_strength}</Typography>
              <Slider
                value={config.sharpen_strength}
                onChange={(_, value) => handleConfigChange('sharpen_strength', value)}
                min={0.0}
                max={1.0}
                step={0.1}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={config.perspective_correction}
                    onChange={(e) => handleConfigChange('perspective_correction', e.target.checked)}
                  />
                }
                label="Perspective Correction"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={config.auto_threshold}
                    onChange={(e) => handleConfigChange('auto_threshold', e.target.checked)}
                  />
                }
                label="Auto Threshold"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={config.remove_borders}
                    onChange={(e) => handleConfigChange('remove_borders', e.target.checked)}
                  />
                }
                label="Remove Borders"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowAdvancedSettings(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Comparison Dialog */}
      <Dialog
        open={showComparison}
        onClose={() => setShowComparison(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Before & After Comparison
          <IconButton
            sx={{ position: 'absolute', right: 8, top: 8 }}
            onClick={() => setShowComparison(false)}
          >
            <Close />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Typography variant="subtitle1" gutterBottom>
                Original
              </Typography>
              {selectedImage && (
                <img
                  src={selectedImage}
                  alt="Original"
                  style={{ width: '100%', maxHeight: 400, objectFit: 'contain' }}
                />
              )}
            </Grid>
            <Grid item xs={6}>
              <Typography variant="subtitle1" gutterBottom>
                Processed
              </Typography>
              {processedImage && (
                <img
                  src={processedImage}
                  alt="Processed"
                  style={{ width: '100%', maxHeight: 400, objectFit: 'contain' }}
                />
              )}
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowComparison(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ImagePreprocessing;