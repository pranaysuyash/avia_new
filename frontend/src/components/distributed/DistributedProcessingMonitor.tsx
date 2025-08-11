import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  IconButton,
  Chip,
  Alert,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Tooltip,
  Badge,
  Tab,
  Tabs,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Slider,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Dashboard,
  CloudQueue,
  Memory,
  Speed,
  Storage,
  Computer,
  CheckCircle,
  Error,
  Warning,
  Schedule,
  PlayArrow,
  Pause,
  Stop,
  Refresh,
  Settings,
  Delete,
  Add,
  Remove,
  TrendingUp,
  TrendingDown,
  Cached,
  AutorenewOutlined,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import apiService from '../../services/api';

interface SystemMetrics {
  jobs_submitted: number;
  jobs_completed: number;
  jobs_failed: number;
  avg_processing_time: number;
  queue_sizes: Record<string, number>;
  active_workers: number;
  idle_workers: number;
  cache_hit_rate: number;
  memory_usage_mb: number;
}

interface WorkerStatus {
  worker_id: string;
  hostname: string;
  status: string;
  current_job?: string;
  jobs_completed: number;
  jobs_failed: number;
  load_average: number;
  last_heartbeat: string;
}

interface JobStatus {
  job_id: string;
  status: string;
  progress?: number;
  result?: any;
  error?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  worker_id?: string;
}

interface QueueStatus {
  queues: Record<string, number>;
  total_pending: number;
  total_running: number;
  total_completed: number;
  total_failed: number;
}

const DistributedProcessingMonitor: React.FC = () => {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [workers, setWorkers] = useState<WorkerStatus[]>([]);
  const [queueStatus, setQueueStatus] = useState<QueueStatus | null>(null);
  const [recentJobs, setRecentJobs] = useState<JobStatus[]>([]);
  const [metricsHistory, setMetricsHistory] = useState<any[]>([]);
  const [tabValue, setTabValue] = useState(0);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000);
  const [showJobDialog, setShowJobDialog] = useState(false);
  const [showScalingDialog, setShowScalingDialog] = useState(false);
  const [showCacheDialog, setShowCacheDialog] = useState(false);
  const [loading, setLoading] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // Job submission form
  const [jobForm, setJobForm] = useState({
    task_name: '',
    payload: '{}',
    priority: 'NORMAL',
    timeout: 300,
    max_retries: 3,
  });

  // Scaling configuration
  const [scalingConfig, setScalingConfig] = useState({
    min_workers: 1,
    max_workers: 10,
    target_utilization: 0.7,
  });

  // Cache configuration
  const [cacheConfig, setCacheConfig] = useState({
    tier: 'L1_MEMORY',
    ttl: 3600,
    compression_enabled: true,
    auto_warmup: false,
  });

  useEffect(() => {
    fetchInitialData();
    if (autoRefresh) {
      connectWebSocket();
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [autoRefresh]);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchInitialData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const fetchInitialData = async () => {
    try {
      const [metricsRes, workersRes, queueRes] = await Promise.all([
        apiService.get('/api/distributed/metrics'),
        apiService.get('/api/distributed/workers/status'),
        apiService.get('/api/distributed/queue/status'),
      ]);

      setMetrics(metricsRes.data);
      setWorkers(workersRes.data);
      setQueueStatus(queueRes.data);

      // Update metrics history
      setMetricsHistory(prev => {
        const newHistory = [...prev, {
          timestamp: new Date().toLocaleTimeString(),
          ...metricsRes.data,
        }];
        return newHistory.slice(-20); // Keep last 20 data points
      });
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  const connectWebSocket = () => {
    const ws = new WebSocket('ws://localhost:8000/api/distributed/monitor');
    
    ws.onopen = () => {
      console.log('Monitoring WebSocket connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (!data.error) {
        setMetrics(prev => ({
          ...prev,
          ...data,
        }));
        
        setMetricsHistory(prev => {
          const newHistory = [...prev, {
            timestamp: new Date().toLocaleTimeString(),
            ...data,
          }];
          return newHistory.slice(-20);
        });
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };

    wsRef.current = ws;
  };

  const handleSubmitJob = async () => {
    try {
      setLoading(true);
      const response = await apiService.post('/api/distributed/submit-job', {
        ...jobForm,
        payload: JSON.parse(jobForm.payload),
      });
      
      setShowJobDialog(false);
      fetchInitialData();
    } catch (error) {
      console.error('Error submitting job:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConfigureScaling = async () => {
    try {
      setLoading(true);
      await apiService.post('/api/distributed/scaling/configure', scalingConfig);
      setShowScalingDialog(false);
    } catch (error) {
      console.error('Error configuring scaling:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConfigureCache = async () => {
    try {
      setLoading(true);
      await apiService.post('/api/distributed/cache/configure', cacheConfig);
      setShowCacheDialog(false);
    } catch (error) {
      console.error('Error configuring cache:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleClearCache = async (pattern?: string) => {
    try {
      await apiService.post('/api/distributed/cache/clear', { pattern });
      fetchInitialData();
    } catch (error) {
      console.error('Error clearing cache:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'primary';
      case 'pending': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const getWorkerStatusIcon = (status: string) => {
    switch (status) {
      case 'idle': return <CheckCircle color="success" />;
      case 'busy': return <AutorenewOutlined color="primary" />;
      case 'offline': return <Error color="error" />;
      default: return <Warning color="warning" />;
    }
  };

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={3}>
        <Dashboard sx={{ mr: 1 }} />
        <Typography variant="h4">Distributed Processing Monitor</Typography>
        <Box sx={{ flexGrow: 1 }} />
        <FormControlLabel
          control={
            <Switch
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
          }
          label="Auto-refresh"
        />
        <IconButton onClick={fetchInitialData}>
          <Refresh />
        </IconButton>
      </Box>

      {/* Metrics Overview */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <CloudQueue color="primary" sx={{ mr: 1 }} />
                <Typography variant="subtitle2">Jobs Submitted</Typography>
              </Box>
              <Typography variant="h4">{metrics?.jobs_submitted || 0}</Typography>
              <LinearProgress
                variant="determinate"
                value={(metrics?.jobs_completed || 0) / Math.max(metrics?.jobs_submitted || 1, 1) * 100}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Computer color="primary" sx={{ mr: 1 }} />
                <Typography variant="subtitle2">Active Workers</Typography>
              </Box>
              <Typography variant="h4">
                {metrics?.active_workers || 0} / {(metrics?.active_workers || 0) + (metrics?.idle_workers || 0)}
              </Typography>
              <Chip
                label={`${metrics?.idle_workers || 0} idle`}
                size="small"
                color="success"
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Cached color="primary" sx={{ mr: 1 }} />
                <Typography variant="subtitle2">Cache Hit Rate</Typography>
              </Box>
              <Typography variant="h4">
                {((metrics?.cache_hit_rate || 0) * 100).toFixed(1)}%
              </Typography>
              <Chip
                label={`${metrics?.memory_usage_mb?.toFixed(1) || 0} MB`}
                size="small"
                variant="outlined"
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Speed color="primary" sx={{ mr: 1 }} />
                <Typography variant="subtitle2">Avg Processing Time</Typography>
              </Box>
              <Typography variant="h4">
                {(metrics?.avg_processing_time || 0).toFixed(2)}s
              </Typography>
              <Chip
                label={metrics?.jobs_failed ? `${metrics.jobs_failed} failed` : 'All successful'}
                size="small"
                color={metrics?.jobs_failed ? 'error' : 'success'}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} sx={{ mb: 2 }}>
        <Tab label="Queue Status" />
        <Tab label="Workers" />
        <Tab label="Performance" />
        <Tab label="Cache" />
      </Tabs>

      {tabValue === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Queue Distribution
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={Object.entries(queueStatus?.queues || {}).map(([key, value]) => ({
                        name: key,
                        value,
                      }))}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {Object.entries(queueStatus?.queues || {}).map((_, index) => (
                        <Cell key={`cell-${index}`} fill={['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'][index % 5]} />
                      ))}
                    </Pie>
                    <RechartsTooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Job Status Summary
                </Typography>
                <List>
                  <ListItem>
                    <ListItemIcon>
                      <Schedule color="warning" />
                    </ListItemIcon>
                    <ListItemText primary="Pending" />
                    <ListItemSecondaryAction>
                      <Chip label={queueStatus?.total_pending || 0} />
                    </ListItemSecondaryAction>
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <PlayArrow color="primary" />
                    </ListItemIcon>
                    <ListItemText primary="Running" />
                    <ListItemSecondaryAction>
                      <Chip label={queueStatus?.total_running || 0} color="primary" />
                    </ListItemSecondaryAction>
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <CheckCircle color="success" />
                    </ListItemIcon>
                    <ListItemText primary="Completed" />
                    <ListItemSecondaryAction>
                      <Chip label={queueStatus?.total_completed || 0} color="success" />
                    </ListItemSecondaryAction>
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <Error color="error" />
                    </ListItemIcon>
                    <ListItemText primary="Failed" />
                    <ListItemSecondaryAction>
                      <Chip label={queueStatus?.total_failed || 0} color="error" />
                    </ListItemSecondaryAction>
                  </ListItem>
                </List>
                <Box display="flex" justifyContent="center" mt={2}>
                  <Button
                    variant="contained"
                    startIcon={<Add />}
                    onClick={() => setShowJobDialog(true)}
                  >
                    Submit Job
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {tabValue === 1 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Worker Nodes
            </Typography>
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Status</TableCell>
                    <TableCell>Worker ID</TableCell>
                    <TableCell>Hostname</TableCell>
                    <TableCell>Current Job</TableCell>
                    <TableCell>Completed</TableCell>
                    <TableCell>Failed</TableCell>
                    <TableCell>Load</TableCell>
                    <TableCell>Last Heartbeat</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {workers.map((worker) => (
                    <TableRow key={worker.worker_id}>
                      <TableCell>{getWorkerStatusIcon(worker.status)}</TableCell>
                      <TableCell>{worker.worker_id.slice(0, 8)}...</TableCell>
                      <TableCell>{worker.hostname}</TableCell>
                      <TableCell>
                        {worker.current_job ? (
                          <Chip label={worker.current_job.slice(0, 8) + '...'} size="small" />
                        ) : (
                          '-'
                        )}
                      </TableCell>
                      <TableCell>{worker.jobs_completed}</TableCell>
                      <TableCell>{worker.jobs_failed}</TableCell>
                      <TableCell>
                        <LinearProgress
                          variant="determinate"
                          value={worker.load_average * 100}
                          sx={{ width: 100 }}
                        />
                      </TableCell>
                      <TableCell>{new Date(worker.last_heartbeat).toLocaleTimeString()}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            <Box display="flex" justifyContent="center" mt={2}>
              <Button
                variant="outlined"
                startIcon={<Settings />}
                onClick={() => setShowScalingDialog(true)}
              >
                Configure Scaling
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {tabValue === 2 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Performance Metrics
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={metricsHistory}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <RechartsTooltip />
                    <Legend />
                    <Line type="monotone" dataKey="active_workers" stroke="#8884d8" name="Active Workers" />
                    <Line type="monotone" dataKey="idle_workers" stroke="#82ca9d" name="Idle Workers" />
                    <Line type="monotone" dataKey="jobs_submitted" stroke="#ffc658" name="Jobs Submitted" />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Queue Sizes Over Time
                </Typography>
                <ResponsiveContainer width="100%" height={250}>
                  <AreaChart data={metricsHistory}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <RechartsTooltip />
                    <Area type="monotone" dataKey="queue_sizes.CRITICAL" stackId="1" stroke="#ff4444" fill="#ff4444" />
                    <Area type="monotone" dataKey="queue_sizes.HIGH" stackId="1" stroke="#ff8844" fill="#ff8844" />
                    <Area type="monotone" dataKey="queue_sizes.NORMAL" stackId="1" stroke="#44ff44" fill="#44ff44" />
                    <Area type="monotone" dataKey="queue_sizes.LOW" stackId="1" stroke="#4444ff" fill="#4444ff" />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Cache Performance
                </Typography>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={metricsHistory}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <RechartsTooltip />
                    <Legend />
                    <Line type="monotone" dataKey="cache_stats.hit_rate" stroke="#00C49F" name="Hit Rate" />
                    <Line type="monotone" dataKey="cache_stats.avg_response_time_ms" stroke="#FF8042" name="Avg Response (ms)" />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {tabValue === 3 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Cache Management
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Alert severity="info" sx={{ mb: 2 }}>
                  Cache Hit Rate: {((metrics?.cache_hit_rate || 0) * 100).toFixed(1)}%
                </Alert>
                <Button
                  variant="outlined"
                  startIcon={<Delete />}
                  onClick={() => handleClearCache()}
                  fullWidth
                  sx={{ mb: 1 }}
                >
                  Clear All Cache
                </Button>
                <TextField
                  fullWidth
                  label="Clear by Pattern"
                  placeholder="e.g., user:*"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleClearCache((e.target as HTMLInputElement).value);
                    }
                  }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <Button
                  variant="contained"
                  startIcon={<Settings />}
                  onClick={() => setShowCacheDialog(true)}
                  fullWidth
                >
                  Configure Cache
                </Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Job Submission Dialog */}
      <Dialog open={showJobDialog} onClose={() => setShowJobDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Submit New Job</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Task Name"
            value={jobForm.task_name}
            onChange={(e) => setJobForm({ ...jobForm, task_name: e.target.value })}
            sx={{ mt: 2, mb: 2 }}
          />
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Payload (JSON)"
            value={jobForm.payload}
            onChange={(e) => setJobForm({ ...jobForm, payload: e.target.value })}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Priority</InputLabel>
            <Select
              value={jobForm.priority}
              onChange={(e) => setJobForm({ ...jobForm, priority: e.target.value })}
              label="Priority"
            >
              <MenuItem value="CRITICAL">Critical</MenuItem>
              <MenuItem value="HIGH">High</MenuItem>
              <MenuItem value="NORMAL">Normal</MenuItem>
              <MenuItem value="LOW">Low</MenuItem>
              <MenuItem value="BATCH">Batch</MenuItem>
            </Select>
          </FormControl>
          <TextField
            fullWidth
            type="number"
            label="Timeout (seconds)"
            value={jobForm.timeout}
            onChange={(e) => setJobForm({ ...jobForm, timeout: parseInt(e.target.value) })}
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            type="number"
            label="Max Retries"
            value={jobForm.max_retries}
            onChange={(e) => setJobForm({ ...jobForm, max_retries: parseInt(e.target.value) })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowJobDialog(false)}>Cancel</Button>
          <Button onClick={handleSubmitJob} variant="contained" disabled={loading}>
            Submit
          </Button>
        </DialogActions>
      </Dialog>

      {/* Scaling Configuration Dialog */}
      <Dialog open={showScalingDialog} onClose={() => setShowScalingDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Configure Auto-Scaling</DialogTitle>
        <DialogContent>
          <Typography gutterBottom>Minimum Workers</Typography>
          <Slider
            value={scalingConfig.min_workers}
            onChange={(_, value) => setScalingConfig({ ...scalingConfig, min_workers: value as number })}
            min={1}
            max={20}
            marks
            valueLabelDisplay="auto"
          />
          <Typography gutterBottom>Maximum Workers</Typography>
          <Slider
            value={scalingConfig.max_workers}
            onChange={(_, value) => setScalingConfig({ ...scalingConfig, max_workers: value as number })}
            min={1}
            max={100}
            marks
            valueLabelDisplay="auto"
          />
          <Typography gutterBottom>Target Utilization</Typography>
          <Slider
            value={scalingConfig.target_utilization}
            onChange={(_, value) => setScalingConfig({ ...scalingConfig, target_utilization: value as number })}
            min={0.1}
            max={1.0}
            step={0.1}
            marks
            valueLabelDisplay="auto"
            valueLabelFormat={(value) => `${(value * 100).toFixed(0)}%`}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowScalingDialog(false)}>Cancel</Button>
          <Button onClick={handleConfigureScaling} variant="contained" disabled={loading}>
            Apply
          </Button>
        </DialogActions>
      </Dialog>

      {/* Cache Configuration Dialog */}
      <Dialog open={showCacheDialog} onClose={() => setShowCacheDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Configure Cache</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2, mb: 2 }}>
            <InputLabel>Cache Tier</InputLabel>
            <Select
              value={cacheConfig.tier}
              onChange={(e) => setCacheConfig({ ...cacheConfig, tier: e.target.value })}
              label="Cache Tier"
            >
              <MenuItem value="L1_MEMORY">L1 Memory</MenuItem>
              <MenuItem value="L2_DISTRIBUTED">L2 Distributed</MenuItem>
              <MenuItem value="L3_PERSISTENT">L3 Persistent</MenuItem>
              <MenuItem value="L4_DISK">L4 Disk</MenuItem>
            </Select>
          </FormControl>
          <TextField
            fullWidth
            type="number"
            label="TTL (seconds)"
            value={cacheConfig.ttl}
            onChange={(e) => setCacheConfig({ ...cacheConfig, ttl: parseInt(e.target.value) })}
            sx={{ mb: 2 }}
          />
          <FormControlLabel
            control={
              <Switch
                checked={cacheConfig.compression_enabled}
                onChange={(e) => setCacheConfig({ ...cacheConfig, compression_enabled: e.target.checked })}
              />
            }
            label="Enable Compression"
          />
          <FormControlLabel
            control={
              <Switch
                checked={cacheConfig.auto_warmup}
                onChange={(e) => setCacheConfig({ ...cacheConfig, auto_warmup: e.target.checked })}
              />
            }
            label="Auto Warmup"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCacheDialog(false)}>Cancel</Button>
          <Button onClick={handleConfigureCache} variant="contained" disabled={loading}>
            Apply
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DistributedProcessingMonitor;