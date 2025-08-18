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
  Snackbar
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
  Visibility
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { Line, Pie, Bar } from 'react-chartjs-2';
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

// Types
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

const ProcessingRouterWorkflowEngine: React.FC = () => {
  // State management
  const [activeTab, setActiveTab] = useState(0);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [contentAnalysis, setContentAnalysis] = useState<ContentAnalysis | null>(null);
  const [processingRoutes, setProcessingRoutes] = useState<ProcessingRoute[]>([]);
  const [activeJobs, setActiveJobs] = useState<ProcessingJob[]>([]);
  const [jobHistory, setJobHistory] = useState<ProcessingJob[]>([]);
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics | null>(null);
  const [selectedRoute, setSelectedRoute] = useState<string>('auto');
  const [priority, setPriority] = useState<string>('normal');
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' as 'success' | 'error' | 'warning' | 'info' });
  const [jobDetailsDialog, setJobDetailsDialog] = useState<{ open: boolean; job: ProcessingJob | null }>({
    open: false,
    job: null
  });

  // File upload handling
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      setUploadedFile(file);
      await analyzeContent(file);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.mp3', '.wav', '.m4a', '.flac', '.aac'],
      'video/*': ['.mp4', '.avi', '.mov', '.mkv', '.webm'],
      'image/*': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
      'application/pdf': ['.pdf']
    },
    multiple: false
  });

  // API calls
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
        setContentAnalysis(analysis);
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

  const startProcessing = async () => {
    if (!uploadedFile) return;

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', uploadedFile);
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
        setSnackbar({
          open: true,
          message: `Processing started! Job ID: ${result.job_id}`,
          severity: 'success'
        });
        setActiveTab(1); // Switch to job monitor
        fetchActiveJobs();
      } else {
        throw new Error('Processing failed to start');
      }
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to start processing',
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

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
      const response = await fetch('/api/v1/processing/jobs?status=completed,failed,cancelled&limit=20');
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

  const cancelJob = async (jobId: string) => {
    try {
      const response = await fetch(`/api/v1/processing/jobs/${jobId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setSnackbar({
          open: true,
          message: 'Job cancelled successfully',
          severity: 'success'
        });
        fetchActiveJobs();
      }
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to cancel job',
        severity: 'error'
      });
    }
  };

  // Effects
  useEffect(() => {
    fetchProcessingRoutes();
    fetchActiveJobs();
    fetchJobHistory();
    fetchPerformanceMetrics();
  }, []);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (autoRefresh) {
      interval = setInterval(() => {
        fetchActiveJobs();
        fetchPerformanceMetrics();
      }, 2000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle />;
      case 'failed': return <Error />;
      case 'running': return <PlayArrow />;
      case 'pending': return <Warning />;
      case 'cancelled': return <Stop />;
      default: return <Info />;
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Tab panels
  const ProcessMediaPanel = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={8}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Upload Media File
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
              <Upload sx={{ fontSize: 48, color: '#ccc', mb: 2 }} />
              {uploadedFile ? (
                <Typography variant="body1">
                  Selected: {uploadedFile.name} ({(uploadedFile.size / 1024 / 1024).toFixed(2)} MB)
                </Typography>
              ) : (
                <Typography variant="body1">
                  {isDragActive ? 'Drop the file here...' : 'Drag & drop a media file here, or click to select'}
                </Typography>
              )}
            </Box>

            {uploadedFile && (
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
                  onClick={startProcessing}
                  disabled={loading}
                  sx={{ mt: 2 }}
                  size="large"
                >
                  {loading ? 'Starting...' : 'Start Processing'}
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
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <CircularProgress size={20} />
                <Typography>Analyzing content...</Typography>
              </Box>
            )}

            {contentAnalysis && (
              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Media Type: <strong>{contentAnalysis.media_type.toUpperCase()}</strong>
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Complexity: <strong>{contentAnalysis.complexity.toUpperCase()}</strong>
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Quality Score: <strong>{contentAnalysis.quality_score.toFixed(2)}</strong>
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Est. Processing Time: <strong>{formatDuration(contentAnalysis.estimated_processing_time)}</strong>
                </Typography>
                
                <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
                  Processing Requirements:
                </Typography>
                {contentAnalysis.processing_requirements.map((req, index) => (
                  <Chip
                    key={index}
                    label={req.replace('_', ' ')}
                    size="small"
                    sx={{ mr: 0.5, mb: 0.5 }}
                  />
                ))}

                <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
                  Resource Requirements:
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  CPU: {contentAnalysis.resource_requirements.cpu} cores
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Memory: {contentAnalysis.resource_requirements.memory} MB
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Disk: {contentAnalysis.resource_requirements.disk} MB
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const JobMonitorPanel = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6">Job Monitor</Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
            }
            label="Auto Refresh"
          />
          <Button
            startIcon={<Refresh />}
            onClick={() => {
              fetchActiveJobs();
              fetchJobHistory();
            }}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Active Jobs */}
      <Typography variant="h6" gutterBottom>
        Active Jobs ({activeJobs.length})
      </Typography>
      
      {activeJobs.length > 0 ? (
        <Grid container spacing={2} sx={{ mb: 4 }}>
          {activeJobs.map((job) => (
            <Grid item xs={12} key={job.job_id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'between', alignItems: 'center' }}>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="subtitle1">
                        {job.filename || `Job ${job.job_id.substring(0, 8)}`}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Route: {job.route}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                        <Chip
                          icon={getStatusIcon(job.status)}
                          label={job.status.toUpperCase()}
                          color={getStatusColor(job.status) as any}
                          size="small"
                        />
                        <Typography variant="body2" color="text.secondary">
                          {(job.progress * 100).toFixed(1)}%
                        </Typography>
                      </Box>
                    </Box>
                    
                    <Box sx={{ width: 200, mr: 2 }}>
                      <LinearProgress
                        variant="determinate"
                        value={job.progress * 100}
                        sx={{ height: 8, borderRadius: 4 }}
                      />
                    </Box>
                    
                    <Box>
                      <Tooltip title="View Details">
                        <IconButton
                          onClick={() => setJobDetailsDialog({ open: true, job })}
                        >
                          <Visibility />
                        </IconButton>
                      </Tooltip>
                      {job.status === 'running' && (
                        <Tooltip title="Cancel Job">
                          <IconButton
                            onClick={() => cancelJob(job.job_id)}
                            color="error"
                          >
                            <Stop />
                          </IconButton>
                        </Tooltip>
                      )}
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      ) : (
        <Alert severity="info" sx={{ mb: 4 }}>
          No active jobs
        </Alert>
      )}

      {/* Job History */}
      <Typography variant="h6" gutterBottom>
        Recent Jobs
      </Typography>
      
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Job ID</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Route</TableCell>
              <TableCell>Progress</TableCell>
              <TableCell>Started</TableCell>
              <TableCell>Completed</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {jobHistory.map((job) => (
              <TableRow key={job.job_id}>
                <TableCell>{job.job_id.substring(0, 8)}...</TableCell>
                <TableCell>
                  <Chip
                    icon={getStatusIcon(job.status)}
                    label={job.status.toUpperCase()}
                    color={getStatusColor(job.status) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>{job.route}</TableCell>
                <TableCell>{(job.progress * 100).toFixed(1)}%</TableCell>
                <TableCell>
                  {job.started_at ? new Date(job.started_at).toLocaleTimeString() : '-'}
                </TableCell>
                <TableCell>
                  {job.completed_at ? new Date(job.completed_at).toLocaleTimeString() : '-'}
                </TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={() => setJobDetailsDialog({ open: true, job })}
                  >
                    <Visibility />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );

  const RouteManagerPanel = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        Processing Routes ({processingRoutes.length})
      </Typography>
      
      <Grid container spacing={3}>
        {processingRoutes.map((route) => (
          <Grid item xs={12} md={6} key={route.route_id}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {route.name}
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  {route.description}
                </Typography>
                
                <Box sx={{ mb: 2 }}>
                  <Chip label={route.strategy.toUpperCase()} size="small" sx={{ mr: 1 }} />
                  <Chip label={route.mode.toUpperCase()} size="small" sx={{ mr: 1 }} />
                  <Chip label={route.priority.toUpperCase()} size="small" />
                </Box>
                
                <Typography variant="body2" gutterBottom>
                  <strong>Media Types:</strong> {route.media_types.join(', ')}
                </Typography>
                <Typography variant="body2" gutterBottom>
                  <strong>Complexity:</strong> {route.complexity_levels.join(', ')}
                </Typography>
                <Typography variant="body2" gutterBottom>
                  <strong>Duration:</strong> {formatDuration(route.estimated_duration)}
                </Typography>
                <Typography variant="body2" gutterBottom>
                  <strong>Resource Cost:</strong> {route.resource_cost}
                </Typography>
                
                <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
                  Processing Steps:
                </Typography>
                {route.processing_steps.map((step, index) => (
                  <Typography key={index} variant="body2" color="text.secondary">
                    {index + 1}. {step.replace('_', ' ')}
                  </Typography>
                ))}
                
                {route.fallback_routes.length > 0 && (
                  <>
                    <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
                      Fallback Routes:
                    </Typography>
                    {route.fallback_routes.map((fallback, index) => (
                      <Chip
                        key={index}
                        label={fallback}
                        size="small"
                        variant="outlined"
                        sx={{ mr: 0.5, mb: 0.5 }}
                      />
                    ))}
                  </>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );

  const AnalyticsPanel = () => {
    if (!performanceMetrics) {
      return <CircularProgress />;
    }

    const successRate = performanceMetrics.total_jobs > 0 
      ? (performanceMetrics.successful_jobs / performanceMetrics.total_jobs) * 100 
      : 0;

    const pieData = {
      labels: ['Successful', 'Failed'],
      datasets: [{
        data: [performanceMetrics.successful_jobs, performanceMetrics.failed_jobs],
        backgroundColor: ['#4caf50', '#f44336'],
      }]
    };

    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          Performance Analytics
        </Typography>
        
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h4" color="primary">
                  {performanceMetrics.total_jobs}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Jobs
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h4" color="success.main">
                  {successRate.toFixed(1)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Success Rate
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h4" color="info.main">
                  {formatDuration(performanceMetrics.average_processing_time)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Avg Processing Time
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h4" color="warning.main">
                  {performanceMetrics.active_jobs}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Active Jobs
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Job Success Rate
                </Typography>
                <Box sx={{ height: 300 }}>
                  <Pie data={pieData} options={{ maintainAspectRatio: false }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  System Resources
                </Typography>
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" gutterBottom>
                    Available Routes: {performanceMetrics.available_routes}
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    Queued Jobs: {performanceMetrics.queued_jobs}
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    Resource Utilization: {performanceMetrics.resource_utilization}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={performanceMetrics.resource_utilization}
                    sx={{ mt: 1 }}
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    );
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h4" gutterBottom>
        Processing Router & Workflow Engine
      </Typography>
      
      <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
        <Tab icon={<Upload />} label="Process Media" />
        <Tab icon={<Monitor />} label="Job Monitor" />
        <Tab icon={<Route />} label="Routes" />
        <Tab icon={<Analytics />} label="Analytics" />
      </Tabs>

      {activeTab === 0 && <ProcessMediaPanel />}
      {activeTab === 1 && <JobMonitorPanel />}
      {activeTab === 2 && <RouteManagerPanel />}
      {activeTab === 3 && <AnalyticsPanel />}

      {/* Job Details Dialog */}
      <Dialog
        open={jobDetailsDialog.open}
        onClose={() => setJobDetailsDialog({ open: false, job: null })}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Job Details: {jobDetailsDialog.job?.job_id.substring(0, 8)}
        </DialogTitle>
        <DialogContent>
          {jobDetailsDialog.job && (
            <Box>
              <Typography variant="body1" gutterBottom>
                <strong>Status:</strong> {jobDetailsDialog.job.status}
              </Typography>
              <Typography variant="body1" gutterBottom>
                <strong>Progress:</strong> {(jobDetailsDialog.job.progress * 100).toFixed(1)}%
              </Typography>
              <Typography variant="body1" gutterBottom>
                <strong>Route:</strong> {jobDetailsDialog.job.route}
              </Typography>
              <Typography variant="body1" gutterBottom>
                <strong>Created:</strong> {new Date(jobDetailsDialog.job.created_at).toLocaleString()}
              </Typography>
              
              {jobDetailsDialog.job.errors.length > 0 && (
                <>
                  <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
                    Errors:
                  </Typography>
                  {jobDetailsDialog.job.errors.map((error, index) => (
                    <Alert key={index} severity="error" sx={{ mb: 1 }}>
                      {error}
                    </Alert>
                  ))}
                </>
              )}
              
              {Object.keys(jobDetailsDialog.job.results).length > 0 && (
                <>
                  <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
                    Results:
                  </Typography>
                  <pre style={{ fontSize: '12px', overflow: 'auto' }}>
                    {JSON.stringify(jobDetailsDialog.job.results, null, 2)}
                  </pre>
                </>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setJobDetailsDialog({ open: false, job: null })}>
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
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

export default ProcessingRouterWorkflowEngine;