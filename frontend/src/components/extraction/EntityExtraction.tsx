import React, { useState, useCallback } from 'react';
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
  ListItemSecondaryAction,
  Divider,
} from '@mui/material';
import {
  CloudUpload,
  Download,
  Refresh,
  Close,
  AccountTree,
  Label,
  Category,
  Visibility,
  Delete,
  FilterList,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import apiService from '../../services/api';

interface Entity {
  id: string;
  type: string;
  label: string;
  confidence: number;
  bbox: number[];
  attributes: Record<string, any>;
}

interface Relationship {
  source: string;
  target: string;
  type: string;
  confidence: number;
}

interface ExtractionConfig {
  confidence_threshold: number;
  max_entities: number;
  entity_types: string[];
}

interface ExtractionResults {
  task_id: string;
  status: string;
  entities: Entity[];
  entity_count: number;
  relationships: Relationship[];
  visualization_url?: string;
  processing_time?: number;
  timestamp?: string;
}

const EntityExtraction: React.FC = () => {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [extracting, setExtracting] = useState(false);
  const [results, setResults] = useState<ExtractionResults | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [showVisualization, setShowVisualization] = useState(false);
  const [filterType, setFilterType] = useState<string>('all');
  const [extractionConfig, setExtractionConfig] = useState<ExtractionConfig>({
    confidence_threshold: 0.5,
    max_entities: 100,
    entity_types: ['all'],
  });

  const pollIntervalRef = React.useRef<NodeJS.Timeout | null>(null);

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

  const extractEntities = async () => {
    if (!selectedImage || !imageFile) return;

    try {
      setExtracting(true);
      setError(null);

      const formData = new FormData();
      formData.append('file', imageFile);
      formData.append('extraction_config', JSON.stringify(extractionConfig));
      formData.append('include_visualization', 'true');

      const response = await apiService.post('/api/v1/entity-extraction/extract/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const taskId = response.data.task_id;
      pollForResults(taskId);

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Extraction failed');
      setExtracting(false);
    }
  };

  const pollForResults = (taskId: string) => {
    pollIntervalRef.current = setInterval(async () => {
      try {
        const response = await apiService.get(`/api/v1/entity-extraction/status/${taskId}`);
        const data = response.data;

        if (data.status === 'completed' && data.result) {
          setResults(data.result);
          setExtracting(false);
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
          }
        } else if (data.status === 'failed') {
          setError(data.message || 'Extraction failed');
          setExtracting(false);
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
          }
        }
      } catch (err) {
        setError('Failed to get extraction status');
        setExtracting(false);
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
        }
      }
    }, 1000);
  };

  const resetExtraction = () => {
    setSelectedImage(null);
    setImageFile(null);
    setResults(null);
    setError(null);
    setExtracting(false);
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }
  };

  const handleConfigChange = (key: keyof ExtractionConfig, value: any) => {
    setExtractionConfig({ ...extractionConfig, [key]: value });
  };

  const downloadResults = async (format: 'json' | 'csv') => {
    if (!results?.task_id) return;

    try {
      const response = await apiService.get(
        `/api/v1/entity-extraction/results/${results.task_id}?format=${format}`
      );
      
      const data = format === 'json' 
        ? JSON.stringify(response.data.data, null, 2)
        : response.data.data;
      
      const blob = new Blob([data], { 
        type: format === 'json' ? 'application/json' : 'text/csv' 
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `entities_${results.task_id}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError('Failed to download results');
    }
  };

  const getEntityColor = (type: string): string => {
    const colors: Record<string, string> = {
      person: '#2196F3',
      object: '#4CAF50',
      text: '#FF9800',
      logo: '#9C27B0',
      location: '#F44336',
      default: '#757575',
    };
    return colors[type.toLowerCase()] || colors.default;
  };

  const filteredEntities = results?.entities.filter(entity => 
    filterType === 'all' || entity.type === filterType
  ) || [];

  const entityTypes = Array.from(new Set(results?.entities?.map(e => e.type) || []));

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <AccountTree color="primary" />
        Entity Extraction
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
        </Grid>

        {/* Controls Section */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Extraction Settings
              </Typography>

              <Box sx={{ mb: 2 }}>
                <Typography gutterBottom>
                  Confidence Threshold: {extractionConfig.confidence_threshold}
                </Typography>
                <TextField
                  type="range"
                  fullWidth
                  value={extractionConfig.confidence_threshold}
                  onChange={(e) => handleConfigChange('confidence_threshold', parseFloat(e.target.value))}
                  inputProps={{
                    min: 0,
                    max: 1,
                    step: 0.1,
                  }}
                />
              </Box>

              <TextField
                fullWidth
                label="Max Entities"
                type="number"
                value={extractionConfig.max_entities}
                onChange={(e) => handleConfigChange('max_entities', parseInt(e.target.value))}
                sx={{ mb: 2 }}
              />

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Entity Types</InputLabel>
                <Select
                  multiple
                  value={extractionConfig.entity_types}
                  onChange={(e) => handleConfigChange('entity_types', e.target.value)}
                  label="Entity Types"
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {(selected as string[]).map((value) => (
                        <Chip key={value} label={value} size="small" />
                      ))}
                    </Box>
                  )}
                >
                  <MenuItem value="all">All Types</MenuItem>
                  <MenuItem value="person">Person</MenuItem>
                  <MenuItem value="object">Object</MenuItem>
                  <MenuItem value="text">Text</MenuItem>
                  <MenuItem value="logo">Logo</MenuItem>
                  <MenuItem value="location">Location</MenuItem>
                </Select>
              </FormControl>

              <FormControlLabel
                control={
                  <Switch
                    checked={showVisualization}
                    onChange={(e) => setShowVisualization(e.target.checked)}
                  />
                }
                label="Show Visualization"
                sx={{ mb: 2 }}
              />

              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  size="large"
                  fullWidth
                  onClick={extractEntities}
                  disabled={!selectedImage || extracting}
                  startIcon={extracting ? <CircularProgress size={20} /> : <Label />}
                >
                  {extracting ? 'Extracting...' : 'Extract Entities'}
                </Button>
                <Button
                  variant="outlined"
                  onClick={resetExtraction}
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
            </CardContent>
          </Card>
        </Grid>

        {/* Results Section */}
        {results && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Category color="primary" />
                  Extraction Results
                  <Box sx={{ ml: 'auto', display: 'flex', gap: 1 }}>
                    <Button
                      size="small"
                      startIcon={<Download />}
                      onClick={() => downloadResults('json')}
                    >
                      JSON
                    </Button>
                    <Button
                      size="small"
                      startIcon={<Download />}
                      onClick={() => downloadResults('csv')}
                    >
                      CSV
                    </Button>
                  </Box>
                </Typography>

                <Grid container spacing={2} sx={{ mb: 2 }}>
                  <Grid item xs={12} sm={3}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h4">{results.entity_count}</Typography>
                      <Typography variant="body2" color="textSecondary">
                        Total Entities
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} sm={3}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h4">{results.relationships?.length || 0}</Typography>
                      <Typography variant="body2" color="textSecondary">
                        Relationships
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} sm={3}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h4">{entityTypes.length}</Typography>
                      <Typography variant="body2" color="textSecondary">
                        Entity Types
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} sm={3}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h4">
                        {results.processing_time?.toFixed(2) || 0}s
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Processing Time
                      </Typography>
                    </Paper>
                  </Grid>
                </Grid>

                <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} sx={{ mb: 2 }}>
                  <Tab label="Entities" />
                  <Tab label="Relationships" />
                  {showVisualization && <Tab label="Visualization" />}
                </Tabs>

                {/* Entities Tab */}
                {tabValue === 0 && (
                  <Box>
                    <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
                      <FormControl size="small" sx={{ minWidth: 200 }}>
                        <InputLabel>Filter by Type</InputLabel>
                        <Select
                          value={filterType}
                          onChange={(e) => setFilterType(e.target.value)}
                          label="Filter by Type"
                          startAdornment={<FilterList sx={{ mr: 1, color: 'action.active' }} />}
                        >
                          <MenuItem value="all">All Types</MenuItem>
                          {entityTypes.map(type => (
                            <MenuItem key={type} value={type}>{type}</MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                      <Typography variant="body2" color="textSecondary">
                        Showing {filteredEntities.length} of {results.entity_count} entities
                      </Typography>
                    </Box>

                    <List>
                      {filteredEntities.map((entity, index) => (
                        <React.Fragment key={entity.id}>
                          <ListItem>
                            <ListItemText
                              primary={
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <Chip
                                    label={entity.type}
                                    size="small"
                                    sx={{
                                      backgroundColor: getEntityColor(entity.type),
                                      color: 'white',
                                    }}
                                  />
                                  <Typography variant="body1">{entity.label}</Typography>
                                </Box>
                              }
                              secondary={
                                <Box>
                                  <Typography variant="body2" color="textSecondary">
                                    Confidence: {(entity.confidence * 100).toFixed(1)}%
                                  </Typography>
                                  {entity.bbox && (
                                    <Typography variant="caption" color="textSecondary">
                                      Position: [{entity.bbox.map(v => v.toFixed(0)).join(', ')}]
                                    </Typography>
                                  )}
                                </Box>
                              }
                            />
                            <ListItemSecondaryAction>
                              <IconButton edge="end" size="small">
                                <Visibility />
                              </IconButton>
                            </ListItemSecondaryAction>
                          </ListItem>
                          {index < filteredEntities.length - 1 && <Divider />}
                        </React.Fragment>
                      ))}
                    </List>
                  </Box>
                )}

                {/* Relationships Tab */}
                {tabValue === 1 && (
                  <Box>
                    {results.relationships && results.relationships.length > 0 ? (
                      <List>
                        {results.relationships.map((rel, index) => (
                          <React.Fragment key={index}>
                            <ListItem>
                              <ListItemText
                                primary={
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <Typography variant="body1">{rel.source}</Typography>
                                    <Typography variant="body2" color="primary">
                                      →{rel.type}→
                                    </Typography>
                                    <Typography variant="body1">{rel.target}</Typography>
                                  </Box>
                                }
                                secondary={
                                  <Typography variant="body2" color="textSecondary">
                                    Confidence: {(rel.confidence * 100).toFixed(1)}%
                                  </Typography>
                                }
                              />
                            </ListItem>
                            {index < results.relationships.length - 1 && <Divider />}
                          </React.Fragment>
                        ))}
                      </List>
                    ) : (
                      <Typography variant="body2" color="textSecondary" align="center" sx={{ py: 4 }}>
                        No relationships detected
                      </Typography>
                    )}
                  </Box>
                )}

                {/* Visualization Tab */}
                {tabValue === 2 && showVisualization && results.visualization_url && (
                  <Box sx={{ textAlign: 'center' }}>
                    <img
                      src={results.visualization_url}
                      alt="Entity Visualization"
                      style={{
                        maxWidth: '100%',
                        maxHeight: 600,
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
        )}
      </Grid>
    </Box>
  );
};

export default EntityExtraction;