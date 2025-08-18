import React, { useState, useEffect, useCallback } from 'react';
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Switch,
  FormControlLabel,
  Tabs,
  Tab,
  CircularProgress,
  Tooltip,
  IconButton,
  Snackbar,
  AppBar,
  Toolbar,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Badge,
  Menu,
  MenuList,
  ClickAwayListener,
  Popper,
  Grow,
  Paper as MenuPaper
} from '@mui/material';
import {
  Upload,
  PlayArrow,
  Pause,
  Stop,
  Refresh,
  Settings,
  Analytics,
  Route,
  Monitor,
  CheckCircle,
  Error,
  Warning,
  Info,
  Delete,
  Visibility,
  Dashboard,
  FolderOpen,
  CloudUpload,
  Timeline,
  Speed,
  Memory,
  Storage,
  Computer,
  Notifications,
  MoreVert
} from '@mui/icons-material';
import { Line, Pie, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement,
  BarElement
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  ChartTooltip,
  Legend,
  ArcElement,
  BarElement
);

// Types (same as React component but with additional desktop-specific features)
interface ContentAnalysis {
  media_type: string;
  file_size_mb: number;
  duration_seconds: number;
  complexity: string;
  quality_score: number;
  processing_requirements: string[];
  estimated_processing_time: number;
  resource_requirements: {
    cpu: number;
    memory: number;
    disk: number;
    gpu?: number;
  };
  content_features: Record<string, any>;
}

interface ProcessingRoute {
  route_id: string;
  name: string;
  description: string;
  media_types: string[];
  complexity_levels: string[];
  processing_steps: string[];
  strategy: string;
  mode: string;
  priority: string;
  estimated_duration: number;
  resource_cost: number;
  fallback_routes: string[];
}

interface ProcessingJob {
  job_id: string;
  status: string;
  progress: number;
  route: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  errors: string[];
  results: Record<string, any>;
  filename?: string;
}

interface PerformanceMetrics {
  total_jobs: number;
  successful_jobs: number;
  failed_jobs: number;
  average_processing_time: number;
  active_jobs: number;
  queued_jobs: number;
  available_routes: number;
  resource_utilization: number;
}

interface SystemResources {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  gpu_usage?: number;
  network_usage: number;
}

const ProcessingRouterWorkflowEngineDesktop: React.FC = () => {
  // State management (enhanced for desktop)
  const [drawerOpen, setDrawerOpen] = useState(true);
  const [activeView, setActiveView] = useState('dashboard');
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [contentAnalyses, setContentAnalyses] = useState<ContentAnalysis[]>([]);
  const [processingRoutes, setProcessingRoutes] = useState<ProcessingRoute[]>([]);
  const [activeJobs, setActiveJobs] = useState<ProcessingJob[]>([]);
  const [jobHistory, setJobHistory] = useState<ProcessingJob[]>([]);
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics | null>(null);
  const [systemResources, setSystemResources] = useState<SystemResources | null>(null);
  const [selectedRoute, setSelectedRoute] = useState<string>('auto');
  const [priority, setPriority] = useState<string>('normal');
  const [batchProcessing, setBatchProcessing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(2000);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' as 'success' | 'error' | 'warning' | 'info' });
  const [jobDetailsDialog, setJobDetailsDialog] = useState<{ open: boolean; job: ProcessingJob | null }>({
    open: false,
    job: null
  });
  const [settingsDialog, setSettingsDialog] = useState(false);
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);

  // Desktop-specific file handling
  const handleFileDrop = useCallback(async (event: React.DragEvent) => {
    event.preventDefault();
    const files = Array.from(event.dataTransfer.files);
    
    if (batchProcessing) {
      setUploadedFiles(prev => [...prev, ...files]);
      // Analyze all files
      for (const file of files) {
        await analyzeContent(file);
      }
    } else if (files.length > 0) {
      setUploadedFiles([files[0]]);
      await analyzeContent(files[0]);
    }
  }, [batchProcessing]);

  const handleFileSelect = useCallback(async () => {
    // Use Electron's dialog API
    const result = await window.electronAPI?.showOpenDialog({
      properties: ['openFile', batchProcessing ? 'multiSelections' : undefined],
      filters: [
        { name: 'Media Files', extensions: ['mp3', 'wav', 'm4a', 'flac', 'mp4', 'avi', 'mov', 'mkv'] },
        { name: 'Documents', extensions: ['pdf', 'doc', 'docx'] },
        { name: 'Images', extensions: ['jpg', 'jpeg', 'png', 'gif', 'bmp'] },
        { name: 'All Files', extensions: ['*'] }
      ]
    });

    if (result && !result.canceled && result.filePaths.length > 0) {
      const files = result.filePaths.map(path => new File([], path.split('/').pop() || 'unknown'));
      setUploadedFiles(files);
      
      // Analyze files
      for (const file of files) {
        await analyzeContent(file);
      }
    }
  }, [batchProcessing]);

  // Enhanced API calls with desktop features
  const analyzeContent = async (file: File) => {
    setAnalyzing(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/v1/processing/analyze', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const analysis = await response.json();
        setContentAnalyses(prev => [...prev, analysis]);
        
        // Desktop notification
        if (window.electronAPI?.showNotification) {
          window.electronAPI.showNotification({
            title: 'Content Analysis Complete',
            body: `${file.name} analyzed - ${analysis.media_type.toUpperCase()} file`
          });
        }
      } else {
        throw new Error('Analysis failed');
      }
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Content analysis failed',
        severity: 'error'
      });
    } finally {
      setAnalyzing(false);
    }
  };

  const startBatchProcessing = async () => {
    if (uploadedFiles.length === 0) return;

    setLoading(true);
    const jobIds: string[] = [];

    try {
      for (const file of uploadedFiles) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('priority', priority);
        if (selectedRoute !== 'auto') {
          formData.append('custom_route', selectedRoute);
        }

        const response = await fetch('/api/v1/processing/process', {
          method: 'POST',
          body: formData
        });

        if (response.ok) {
          const result = await response.json();
          jobIds.push(result.job_id);
        }
      }

      if (jobIds.length > 0) {
        setSnackbar({
          open: true,
          message: `Batch processing started! ${jobIds.length} jobs submitted`,
          severity: 'success'
        });
        
        // Desktop notification
        if (window.electronAPI?.showNotification) {
          window.electronAPI.showNotification({
            title: 'Batch Processing Started',
            body: `${jobIds.length} files submitted for processing`
          });
        }
        
        setActiveView('monitor');
        fetchActiveJobs();
      }
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to start batch processing',
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  // System resource monitoring (desktop-specific)
  const fetchSystemResources = async () => {
    try {
      // This would integrate with Electron's system monitoring
      const resources = await window.electronAPI?.getSystemResources();
      if (resources) {
        setSystemResources(resources);
      }
    } catch (error) {
      console.error('Failed to fetch system resources:', error);
    }
  };

  // Enhanced data fetching
  const fetchProcessingRoutes = async () => {
    try {
      const response = await fetch('/api/v1/processing/routes');
      if (response.ok) {
        const routes = await response.json();
        setProcessingRoutes(routes);
      }
    } catch (error) {
      console.error('Failed to fetch routes:', error);
    }
  };

  const fetchActiveJobs = async () => {
    try {
      const response = await fetch('/api/v1/processing/jobs?status=running,pending');
      if (response.ok) {
        const data = await response.json();
        setActiveJobs(data.jobs || []);
      }
    } catch (error) {
      console.error('Failed to fetch active jobs:', error);
    }
  };

  const fetchJobHistory = async () => {
    try {
      const response = await fetch('/api/v1/processing/jobs?status=completed,failed,cancelled&limit=50');
      if (response.ok) {
        const data = await response.json();
        setJobHistory(data.jobs || []);
      }
    } catch (error) {
      console.error('Failed to fetch job history:', error);
    }
  };

  const fetchPerformanceMetrics = async () => {
    try {
      const response = await fetch('/api/v1/processing/metrics');
      if (response.ok) {
        const metrics = await response.json();
        setPerformanceMetrics(metrics);
      }
    } catch (error) {
      console.error('Failed to fetch performance metrics:', error);
    }
  };

  // Effects
  useEffect(() => {
    fetchProcessingRoutes();
    fetchActiveJobs();
    fetchJobHistory();
    fetchPerformanceMetrics();
    fetchSystemResources();
  }, []);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (autoRefresh) {
      interval = setInterval(() => {
        fetchActiveJobs();
        fetchPerformanceMetrics();
        fetchSystemResources();
      }, refreshInterval);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh, refreshInterval]);

  // Helper functions
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'running': return 'primary';
      case 'pending': return 'warning';
      case 'cancelled': return 'default';
      default: return 'default';
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatBytes = (bytes: number) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  // Desktop-specific views
  const DashboardView = () => (
    <Grid container spacing={3}>
      {/* Overview Cards */}
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Dashboard sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6">Active Jobs</Typography>
            </Box>
            <Typography variant="h3" color="primary">
              {activeJobs.length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Currently processing
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <CheckCircle sx={{ mr: 1, color: 'success.main' }} />
              <Typography variant="h6">Success Rate</Typography>
            </Box>
            <Typography variant="h3" color="success.main">
              {performanceMetrics ? 
                `${((performanceMetrics.successful_jobs / Math.max(performanceMetrics.total_jobs, 1)) * 100).toFixed(1)}%` : 
                '0%'
              }
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Job completion rate
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Speed sx={{ mr: 1, color: 'info.main' }} />
              <Typography variant="h6">Avg Time</Typography>
            </Box>
            <Typography variant="h3" color="info.main">
              {performanceMetrics ? formatDuration(performanceMetrics.average_processing_time) : '0:00'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Average processing time
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Route sx={{ mr: 1, color: 'warning.main' }} />
              <Typography variant="h6">Routes</Typography>
            </Box>
            <Typography variant="h3" color="warning.main">
              {processingRoutes.length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Available processing routes
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      {/* System Resources */}
      {systemResources && (
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Resources
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">CPU Usage</Typography>
                  <Typography variant="body2">{systemResources.cpu_usage.toFixed(1)}%</Typography>
                </Box>
                <LinearProgress 
                  variant="determinate" 
                  value={systemResources.cpu_usage} 
                  color={systemResources.cpu_usage > 80 ? 'error' : 'primary'}
                />
              </Box>

              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Memory Usage</Typography>
                  <Typography variant="body2">{systemResources.memory_usage.toFixed(1)}%</Typography>
                </Box>
                <LinearProgress 
                  variant="determinate" 
                  value={systemResources.memory_usage} 
                  color={systemResources.memory_usage > 80 ? 'error' : 'primary'}
                />
              </Box>

              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Disk Usage</Typography>
                  <Typography variant="body2">{systemResources.disk_usage.toFixed(1)}%</Typography>
                </Box>
                <LinearProgress 
                  variant="determinate" 
                  value={systemResources.disk_usage} 
                  color={systemResources.disk_usage > 90 ? 'error' : 'primary'}
                />
              </Box>

              {systemResources.gpu_usage !== undefined && (
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2">GPU Usage</Typography>
                    <Typography variant="body2">{systemResources.gpu_usage.toFixed(1)}%</Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={systemResources.gpu_usage} 
                    color={systemResources.gpu_usage > 80 ? 'error' : 'primary'}
                  />
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      )}

      {/* Recent Activity */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            
            {jobHistory.slice(0, 5).map((job) => (
              <Box key={job.job_id} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Chip
                  icon={job.status === 'completed' ? <CheckCircle /> : <Error />}
                  label={job.status.toUpperCase()}
                  color={getStatusColor(job.status) as any}
                  size="small"
                  sx={{ mr: 2, minWidth: 100 }}
                />
                <Typography variant="body2" sx={{ flex: 1 }}>
                  {job.filename || `Job ${job.job_id.substring(0, 8)}`}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {job.completed_at ? new Date(job.completed_at).toLocaleTimeString() : '-'}
                </Typography>
              </Box>
            ))}
          </CardContent>
        </Card>
      </Grid>

      {/* Performance Chart */}
      {performanceMetrics && performanceMetrics.total_jobs > 0 && (
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Processing Performance
              </Typography>
              
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Box sx={{ height: 300 }}>
                    <Doughnut
                      data={{
                        labels: ['Successful', 'Failed'],
                        datasets: [{
                          data: [performanceMetrics.successful_jobs, performanceMetrics.failed_jobs],
                          backgroundColor: ['#4caf50', '#f44336'],
                          borderWidth: 0
                        }]
                      }}
                      options={{
                        maintainAspectRatio: false,
                        plugins: {
                          legend: {
                            position: 'bottom'
                          }
                        }
                      }}
                    />
                  </Box>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Box sx={{ height: 300 }}>
                    <Bar
                      data={{
                        labels: processingRoutes.map(r => r.name),
                        datasets: [{
                          label: 'Usage Count',
                          data: processingRoutes.map(() => Math.floor(Math.random() * 20)), // Mock data
                          backgroundColor: '#2196f3',
                          borderRadius: 4
                        }]
                      }}
                      options={{
                        maintainAspectRatio: false,
                        plugins: {
                          legend: {
                            display: false
                          }
                        },
                        scales: {
                          y: {
                            beginAtZero: true
                          }
                        }
                      }}
                    />
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      )}
    </Grid>
  );

  const ProcessView = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={8}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Media Processing
            </Typography>
            
            {/* Batch Processing Toggle */}
            <FormControlLabel
              control={
                <Switch
                  checked={batchProcessing}
                  onChange={(e) => setBatchProcessing(e.target.checked)}
                />
              }
              label="Batch Processing Mode"
              sx={{ mb: 2 }}
            />
            
            {/* File Drop Zone */}
            <Box
              onDrop={handleFileDrop}
              onDragOver={(e) => e.preventDefault()}
              sx={{
                border: '2px dashed #ccc',
                borderRadius: 2,
                p: 4,
                textAlign: 'center',
                cursor: 'pointer',
                backgroundColor: 'rgba(0,0,0,0.02)',
                '&:hover': { backgroundColor: 'rgba(0,0,0,0.05)' }
              }}
              onClick={handleFileSelect}
            >
              <CloudUpload sx={{ fontSize: 48, color: '#ccc', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                {batchProcessing ? 'Drop multiple files here or click to select' : 'Drop a file here or click to select'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Supported formats: Audio, Video, Images, Documents
              </Typography>
            </Box>

            {/* Selected Files */}
            {uploadedFiles.length > 0 && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Selected Files ({uploadedFiles.length})
                </Typography>
                
                {uploadedFiles.map((file, index) => (
                  <Box key={index} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <FolderOpen sx={{ mr: 1, color: 'primary.main' }} />
                    <Typography variant="body2" sx={{ flex: 1 }}>
                      {file.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {formatBytes(file.size)}
                    </Typography>
                    <IconButton
                      size="small"
                      onClick={() => {
                        setUploadedFiles(prev => prev.filter((_, i) => i !== index));
                        setContentAnalyses(prev => prev.filter((_, i) => i !== index));
                      }}
                    >
                      <Delete />
                    </IconButton>
                  </Box>
                ))}
              </Box>
            )}

            {/* Processing Options */}
            {uploadedFiles.length > 0 && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Processing Options
                </Typography>
                
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <FormControl fullWidth>
                      <InputLabel>Priority</InputLabel>
                      <Select
                        value={priority}
                        onChange={(e) => setPriority(e.target.value)}
                        label="Priority"
                      >
                        <MenuItem value="low">Low</MenuItem>
                        <MenuItem value="normal">Normal</MenuItem>
                        <MenuItem value="high">High</MenuItem>
                        <MenuItem value="critical">Critical</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <FormControl fullWidth>
                      <InputLabel>Processing Route</InputLabel>
                      <Select
                        value={selectedRoute}
                        onChange={(e) => setSelectedRoute(e.target.value)}
                        label="Processing Route"
                      >
                        <MenuItem value="auto">Auto-select</MenuItem>
                        {processingRoutes.map((route) => (
                          <MenuItem key={route.route_id} value={route.route_id}>
                            {route.name}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                </Grid>

                <Button
                  variant="contained"
                  startIcon={<PlayArrow />}
                  onClick={batchProcessing ? startBatchProcessing : () => {/* single file processing */}}
                  disabled={loading || analyzing}
                  sx={{ mt: 2 }}
                  size="large"
                >
                  {loading ? 'Starting...' : 
                   batchProcessing ? `Start Batch Processing (${uploadedFiles.length} files)` : 
                   'Start Processing'}
                </Button>
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Content Analysis
            </Typography>
            
            {analyzing && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <CircularProgress size={20} />
                <Typography>Analyzing content...</Typography>
              </Box>
            )}

            {contentAnalyses.length > 0 && (
              <Box>
                {contentAnalyses.map((analysis, index) => (
                  <Box key={index} sx={{ mb: 3, p: 2, border: '1px solid #eee', borderRadius: 1 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      File {index + 1}
                    </Typography>
                    
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Media Type: <strong>{analysis.media_type.toUpperCase()}</strong>
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Complexity: <strong>{analysis.complexity.toUpperCase()}</strong>
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Quality Score: <strong>{analysis.quality_score.toFixed(2)}</strong>
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Est. Processing Time: <strong>{formatDuration(analysis.estimated_processing_time)}</strong>
                    </Typography>
                    
                    <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
                      Processing Requirements:
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {analysis.processing_requirements.map((req, reqIndex) => (
                        <Chip
                          key={reqIndex}
                          label={req.replace('_', ' ')}
                          size="small"
                        />
                      ))}
                    </Box>
                  </Box>
                ))}
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  // Navigation drawer
  const drawer = (
    <Box sx={{ width: 280 }}>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          Processing Router
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        <ListItem button onClick={() => setActiveView('dashboard')} selected={activeView === 'dashboard'}>
          <ListItemIcon>
            <Dashboard />
          </ListItemIcon>
          <ListItemText primary="Dashboard" />
        </ListItem>
        
        <ListItem button onClick={() => setActiveView('process')} selected={activeView === 'process'}>
          <ListItemIcon>
            <Upload />
          </ListItemIcon>
          <ListItemText primary="Process Media" />
        </ListItem>
        
        <ListItem button onClick={() => setActiveView('monitor')} selected={activeView === 'monitor'}>
          <ListItemIcon>
            <Badge badgeContent={activeJobs.length} color="primary">
              <Monitor />
            </Badge>
          </ListItemIcon>
          <ListItemText primary="Job Monitor" />
        </ListItem>
        
        <ListItem button onClick={() => setActiveView('routes')} selected={activeView === 'routes'}>
          <ListItemIcon>
            <Route />
          </ListItemIcon>
          <ListItemText primary="Routes" />
        </ListItem>
        
        <ListItem button onClick={() => setActiveView('analytics')} selected={activeView === 'analytics'}>
          <ListItemIcon>
            <Analytics />
          </ListItemIcon>
          <ListItemText primary="Analytics" />
        </ListItem>
      </List>
      
      <Divider />
      
      <List>
        <ListItem>
          <ListItemIcon>
            <Computer />
          </ListItemIcon>
          <ListItemText 
            primary="System Status" 
            secondary={systemResources ? `CPU: ${systemResources.cpu_usage.toFixed(1)}%` : 'Loading...'}
          />
        </ListItem>
        
        <ListItem>
          <ListItemIcon>
            <Memory />
          </ListItemIcon>
          <ListItemText 
            primary="Memory" 
            secondary={systemResources ? `${systemResources.memory_usage.toFixed(1)}%` : 'Loading...'}
          />
        </ListItem>
        
        <ListItem>
          <ListItemIcon>
            <Storage />
          </ListItemIcon>
          <ListItemText 
            primary="Storage" 
            secondary={systemResources ? `${systemResources.disk_usage.toFixed(1)}%` : 'Loading...'}
          />
        </ListItem>
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      {/* App Bar */}
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerOpen ? 280 : 0}px)` },
          ml: { sm: `${drawerOpen ? 280 : 0}px` },
        }}
      >
        <Toolbar>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {activeView === 'dashboard' && 'Dashboard'}
            {activeView === 'process' && 'Process Media'}
            {activeView === 'monitor' && 'Job Monitor'}
            {activeView === 'routes' && 'Processing Routes'}
            {activeView === 'analytics' && 'Analytics'}
          </Typography>
          
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                color="default"
              />
            }
            label="Auto Refresh"
            sx={{ color: 'white', mr: 2 }}
          />
          
          <IconButton
            color="inherit"
            onClick={() => {
              fetchActiveJobs();
              fetchJobHistory();
              fetchPerformanceMetrics();
              fetchSystemResources();
            }}
          >
            <Refresh />
          </IconButton>
          
          <IconButton
            color="inherit"
            onClick={(e) => setMenuAnchorEl(e.currentTarget)}
          >
            <MoreVert />
          </IconButton>
        </Toolbar>
      </AppBar>

      {/* Navigation Drawer */}
      <Box
        component="nav"
        sx={{ width: { sm: drawerOpen ? 280 : 0 }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box', 
              width: 280,
              display: drawerOpen ? 'block' : 'none'
            },
          }}
          open={drawerOpen}
        >
          {drawer}
        </Drawer>
      </Box>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerOpen ? 280 : 0}px)` },
        }}
      >
        <Toolbar />
        
        {activeView === 'dashboard' && <DashboardView />}
        {activeView === 'process' && <ProcessView />}
        {/* Add other views here similar to the React component */}
      </Box>

      {/* Menu */}
      <Menu
        anchorEl={menuAnchorEl}
        open={Boolean(menuAnchorEl)}
        onClose={() => setMenuAnchorEl(null)}
      >
        <MenuItem onClick={() => { setSettingsDialog(true); setMenuAnchorEl(null); }}>
          <ListItemIcon>
            <Settings />
          </ListItemIcon>
          Settings
        </MenuItem>
        <MenuItem onClick={() => setMenuAnchorEl(null)}>
          <ListItemIcon>
            <Notifications />
          </ListItemIcon>
          Notifications
        </MenuItem>
      </Menu>

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

export default ProcessingRouterWorkflowEngineDesktop;