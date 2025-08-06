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
  ListItemSecondaryAction,
  Divider,
  Tooltip,
  Menu,
  ListItemIcon,
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
  FolderOpen,
  Save,
  Settings,
  ZoomIn,
  ZoomOut,
  Fullscreen,
  MoreVert,
  ContentCopy,
  Share,
  Print,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { apiClient } from '../../services/api';

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
  enable_ocr: boolean;
  enable_face_detection: boolean;
  enable_object_tracking: boolean;
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
  metadata?: {
    image_resolution: string;
    file_size: number;
    format: string;
  };
}

const EntityExtractionDesktop: React.FC = () => {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [extracting, setExtracting] = useState(false);
  const [results, setResults] = useState<ExtractionResults | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [showVisualization, setShowVisualization] = useState(false);
  const [filterType, setFilterType] = useState<string>('all');
  const [zoomLevel, setZoomLevel] = useState(100);
  const [fullscreenView, setFullscreenView] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);
  const [extractionConfig, setExtractionConfig] = useState<ExtractionConfig>({
    confidence_threshold: 0.5,
    max_entities: 100,
    entity_types: ['all'],
    enable_ocr: true,
    enable_face_detection: true,
    enable_object_tracking: false,
  });

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const imageRef = useRef<HTMLImageElement>(null);

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
      'image/*': ['.jpeg', '.jpg', '.png', '.bmp', '.tiff', '.webp'],
    },
    multiple: false,
  });

  const handleOpenFile = async () => {
    try {
      // Use Electron's file dialog
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/*';
      input.onchange = (e) => {
        const file = (e.target as HTMLInputElement).files?.[0];
        if (file) {
          onDrop([file]);
        }
      };
      input.click();
    } catch (err) {
      setError('Failed to open file dialog');
    }
  };

  const extractEntities = async () => {
    if (!selectedImage || !imageFile) return;

    try {
      setExtracting(true);
      setError(null);

      const formData = new FormData();
      formData.append('file', imageFile);
      formData.append('extraction_config', JSON.stringify(extractionConfig));
      formData.append('include_visualization', 'true');

      const response = await apiClient.post('/api/v1/entity-extraction/extract/upload', formData, {
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
        const response = await apiClient.get(`/api/v1/entity-extraction/status/${taskId}`);
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
    setZoomLevel(100);
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
      const response = await apiClient.get(
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

  const handleZoomIn = () => {
    setZoomLevel(Math.min(zoomLevel + 10, 200));
  };

  const handleZoomOut = () => {
    setZoomLevel(Math.max(zoomLevel - 10, 50));
  };

  const handleMoreOptions = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleCloseMenu = () => {
    setAnchorEl(null);
  };

  const copyEntityToClipboard = (entity: Entity) => {
    navigator.clipboard.writeText(JSON.stringify(entity, null, 2));
    handleCloseMenu();
  };

  const printResults = () => {
    window.print();
    handleCloseMenu();
  };

  const shareResults = async () => {
    if (!results) return;
    
    try {
      await navigator.share({
        title: 'Entity Extraction Results',
        text: `Extracted ${results.entity_count} entities`,
      });
    } catch (err) {
      // Fallback to copy
      navigator.clipboard.writeText(JSON.stringify(results, null, 2));
    }
    handleCloseMenu();
  };

  const getEntityColor = (type: string): string => {
    const colors: Record<string, string> = {
      person: '#2196F3',
      object: '#4CAF50',
      text: '#FF9800',
      logo: '#9C27B0',
      location: '#F44336',
      face: '#00BCD4',
      vehicle: '#795548',
      default: '#757575',
    };
    return colors[type.toLowerCase()] || colors.default;
  };

  const filteredEntities = results?.entities.filter(entity => 
    filterType === 'all' || entity.type === filterType
  ) || [];

  const entityTypes = [...new Set(results?.entities.map(e => e.type) || [])];

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <AccountTree color="primary" />
        Entity Extraction
        <Box sx={{ ml: 'auto' }}>
          <IconButton onClick={handleMoreOptions}>
            <MoreVert />
          </IconButton>
        </Box>
      </Typography>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleCloseMenu}
      >
        <MenuItem onClick={printResults}>
          <ListItemIcon>
            <Print fontSize="small" />
          </ListItemIcon>
          <ListItemText>Print Results</ListItemText>
        </MenuItem>
        <MenuItem onClick={shareResults}>
          <ListItemIcon>
            <Share fontSize="small" />
          </ListItemIcon>
          <ListItemText>Share Results</ListItemText>
        </MenuItem>
      </Menu>

      <Grid container spacing={3}>
        {/* Upload Section */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6">
                  Upload Image
                </Typography>
                <Button
                  startIcon={<FolderOpen />}
                  onClick={handleOpenFile}
                  variant="outlined"
                  size="small"
                >
                  Browse Files
                </Button>
              </Box>
              
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
                  Supports: JPG, PNG, BMP, TIFF, WebP (Max 10MB)
                </Typography>
              </Box>

              {selectedImage && (
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="subtitle2">
                      Selected Image:
                    </Typography>
                    <Box>
                      <IconButton size="small" onClick={handleZoomOut}>
                        <ZoomOut />
                      </IconButton>
                      <Typography variant="caption" sx={{ mx: 1 }}>
                        {zoomLevel}%
                      </Typography>
                      <IconButton size="small" onClick={handleZoomIn}>
                        <ZoomIn />
                      </IconButton>
                      <IconButton size="small" onClick={() => setFullscreenView(true)}>
                        <Fullscreen />
                      </IconButton>
                    </Box>
                  </Box>
                  <Box
                    sx={{
                      overflow: 'auto',
                      maxHeight: 400,
                      border: '1px solid #ccc',
                      borderRadius: 1,
                      backgroundColor: '#f5f5f5',
                    }}
                  >
                    <img
                      ref={imageRef}
                      src={selectedImage}
                      alt="Selected"
                      style={{
                        width: `${zoomLevel}%`,
                        height: 'auto',
                        display: 'block',
                      }}
                    />
                  </Box>
                  {imageFile && (
                    <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                      {imageFile.name} ({(imageFile.size / 1024 / 1024).toFixed(2)} MB)
                    </Typography>
                  )}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Controls Section */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Settings />
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
                  <MenuItem value="face">Face</MenuItem>
                  <MenuItem value="object">Object</MenuItem>
                  <MenuItem value="text">Text</MenuItem>
                  <MenuItem value="logo">Logo</MenuItem>
                  <MenuItem value="location">Location</MenuItem>
                  <MenuItem value="vehicle">Vehicle</MenuItem>
                </Select>
              </FormControl>

              <Box sx={{ mb: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={extractionConfig.enable_ocr}
                      onChange={(e) => handleConfigChange('enable_ocr', e.target.checked)}
                    />
                  }
                  label="Enable OCR Detection"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={extractionConfig.enable_face_detection}
                      onChange={(e) => handleConfigChange('enable_face_detection', e.target.checked)}
                    />
                  }
                  label="Enable Face Detection"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={extractionConfig.enable_object_tracking}
                      onChange={(e) => handleConfigChange('enable_object_tracking', e.target.checked)}
                    />
                  }
                  label="Enable Object Tracking"
                />
              </Box>

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

              {extracting && (
                <Box sx={{ mt: 2 }}>
                  <LinearProgress />
                  <Typography variant="caption" color="textSecondary" align="center" sx={{ mt: 1 }}>
                    Processing image... This may take a few moments.
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
                    <Button
                      size="small"
                      startIcon={<Save />}
                      onClick={() => {/* Save to project */}}
                    >
                      Save to Project
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
                  <Tab label="Raw Data" />
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
                          <ListItem
                            onClick={() => setSelectedEntity(entity)}
                            sx={{ cursor: 'pointer', '&:hover': { backgroundColor: 'action.hover' } }}
                          >
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
                                  {entity.attributes && Object.keys(entity.attributes).length > 0 && (
                                    <Typography variant="caption" color="textSecondary" sx={{ display: 'block' }}>
                                      Attributes: {Object.keys(entity.attributes).join(', ')}
                                    </Typography>
                                  )}
                                </Box>
                              }
                            />
                            <ListItemSecondaryAction>
                              <Tooltip title="View Details">
                                <IconButton edge="end" size="small">
                                  <Visibility />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="Copy">
                                <IconButton 
                                  edge="end" 
                                  size="small"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    copyEntityToClipboard(entity);
                                  }}
                                >
                                  <ContentCopy />
                                </IconButton>
                              </Tooltip>
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

                {/* Raw Data Tab */}
                {tabValue === 3 && (
                  <Box>
                    <Paper sx={{ p: 2, backgroundColor: '#f5f5f5', maxHeight: 400, overflow: 'auto' }}>
                      <pre style={{ margin: 0, fontSize: '0.875rem' }}>
                        {JSON.stringify(results, null, 2)}
                      </pre>
                    </Paper>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* Fullscreen Image Dialog */}
      <Dialog
        open={fullscreenView}
        onClose={() => setFullscreenView(false)}
        maxWidth={false}
        fullWidth
      >
        <DialogTitle>
          Image Preview
          <IconButton
            onClick={() => setFullscreenView(false)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <Close />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          {selectedImage && (
            <img
              src={selectedImage}
              alt="Fullscreen"
              style={{
                width: '100%',
                height: 'auto',
                maxHeight: '80vh',
                objectFit: 'contain',
              }}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Entity Details Dialog */}
      <Dialog
        open={Boolean(selectedEntity)}
        onClose={() => setSelectedEntity(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Entity Details
          <IconButton
            onClick={() => setSelectedEntity(null)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <Close />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          {selectedEntity && (
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                <strong>Type:</strong> {selectedEntity.type}
              </Typography>
              <Typography variant="subtitle1" gutterBottom>
                <strong>Label:</strong> {selectedEntity.label}
              </Typography>
              <Typography variant="subtitle1" gutterBottom>
                <strong>Confidence:</strong> {(selectedEntity.confidence * 100).toFixed(1)}%
              </Typography>
              {selectedEntity.bbox && (
                <Typography variant="subtitle1" gutterBottom>
                  <strong>Bounding Box:</strong> [{selectedEntity.bbox.join(', ')}]
                </Typography>
              )}
              {selectedEntity.attributes && Object.keys(selectedEntity.attributes).length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    <strong>Attributes:</strong>
                  </Typography>
                  <Paper sx={{ p: 1, backgroundColor: '#f5f5f5' }}>
                    <pre style={{ margin: 0, fontSize: '0.875rem' }}>
                      {JSON.stringify(selectedEntity.attributes, null, 2)}
                    </pre>
                  </Paper>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => copyEntityToClipboard(selectedEntity!)}>
            Copy to Clipboard
          </Button>
          <Button onClick={() => setSelectedEntity(null)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default EntityExtractionDesktop;