import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  IconButton,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Switch,
  FormControlLabel,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  Grid,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Collapse,
  Divider,
  Tooltip,
  LinearProgress,
  Tab,
  Tabs,
  Snackbar,
  InputAdornment,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  Add,
  Delete,
  Edit,
  Check,
  Close,
  CloudQueue,
  Speed,
  AttachMoney,
  Security,
  ExpandMore,
  ExpandLess,
  PlayArrow,
  Refresh,
  CompareArrows,
  TrendingUp,
  Warning,
  Error as ErrorIcon,
  CheckCircle,
  SwapHoriz,
  Settings,
  Code,
  Visibility,
  VisibilityOff,
} from '@mui/icons-material';
import apiService from '../../services/api';
import { Line, Bar, Doughnut } from 'react-chartjs-2';

interface ProviderConfig {
  provider: string;
  api_key?: string;
  api_endpoint?: string;
  organization_id?: string;
  project_id?: string;
  region?: string;
  model_mappings: Record<string, string>;
  max_tokens?: number;
  temperature?: number;
  timeout?: number;
  retry_attempts?: number;
  rate_limit?: number;
  custom_headers?: Record<string, string>;
  enabled: boolean;
  priority: number;
}

interface ProviderStatus {
  provider: string;
  status: 'active' | 'inactive' | 'error' | 'testing' | 'rate_limited';
  health_score: number;
  response_time_avg?: number;
  error_rate?: number;
  requests_today: number;
  last_used?: string;
  last_error?: string;
  models_available: string[];
}

interface ProviderUsageStats {
  provider: string;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  total_tokens: number;
  total_cost: number;
  average_response_time: number;
  uptime_percentage: number;
  last_7_days: Array<{ date: string; requests: number; tokens: number }>;
  by_model_type: Record<string, { requests: number; tokens: number }>;
}

const providerLogos: Record<string, string> = {
  openai: '🤖',
  anthropic: '🧠',
  google: '🔍',
  cohere: '🌊',
  huggingface: '🤗',
  azure_openai: '☁️',
  aws_bedrock: '🏛️',
  local: '💻',
  custom: '⚙️',
};

const modelTypes = ['chat', 'completion', 'embedding', 'transcription', 'translation', 'summarization'];

const LLMProviderConfig: React.FC = () => {
  const [providers, setProviders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const [configDialog, setConfigDialog] = useState(false);
  const [testDialog, setTestDialog] = useState(false);
  const [benchmarkDialog, setBenchmarkDialog] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [showApiKey, setShowApiKey] = useState<Record<string, boolean>>({});
  const [expandedProvider, setExpandedProvider] = useState<string | null>(null);
  const [providerStats, setProviderStats] = useState<ProviderUsageStats[]>([]);
  const [benchmarkResults, setBenchmarkResults] = useState<any>(null);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const [editConfig, setEditConfig] = useState<ProviderConfig>({
    provider: 'openai',
    model_mappings: {},
    enabled: true,
    priority: 0,
  });

  useEffect(() => {
    loadProviders();
    loadProviderStats();
  }, []);

  const loadProviders = async () => {
    try {
      setLoading(true);
      const response = await apiService.get('/api/v1/llm-providers/');
      setProviders(response.data);
    } catch (error) {
      console.error('Failed to load providers:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadProviderStats = async () => {
    try {
      const response = await apiService.get('/api/v1/llm-providers/usage/stats');
      setProviderStats(response.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const handleConfigProvider = (provider?: any) => {
    if (provider) {
      setEditConfig({
        provider: provider.provider,
        model_mappings: provider.models || {},
        enabled: provider.enabled,
        priority: provider.priority,
        api_key: '',
      });
    } else {
      setEditConfig({
        provider: 'openai',
        model_mappings: {},
        enabled: true,
        priority: 0,
      });
    }
    setConfigDialog(true);
  };

  const saveConfiguration = async () => {
    try {
      await apiService.post('/api/v1/llm-providers/configure', editConfig);
      setSnackbar({ open: true, message: 'Provider configured successfully', severity: 'success' });
      setConfigDialog(false);
      loadProviders();
    } catch (error) {
      setSnackbar({ open: true, message: 'Failed to configure provider', severity: 'error' });
    }
  };

  const testProvider = async (provider: string) => {
    try {
      const config = providers.find(p => p.provider === provider);
      const response = await apiService.post('/api/v1/llm-providers/test', {
        provider,
        config: editConfig,
        test_prompt: 'Hello, can you respond to confirm the connection is working?',
      });
      
      if (response.data.success) {
        setSnackbar({ open: true, message: 'Provider test successful', severity: 'success' });
      } else {
        setSnackbar({ open: true, message: `Test failed: ${response.data.error}`, severity: 'error' });
      }
    } catch (error) {
      setSnackbar({ open: true, message: 'Provider test failed', severity: 'error' });
    }
  };

  const switchProvider = async (provider: string, modelType?: string) => {
    try {
      await apiService.put('/api/v1/llm-providers/switch', {
        provider,
        model_type: modelType,
      });
      setSnackbar({ open: true, message: 'Provider switched successfully', severity: 'success' });
      loadProviders();
    } catch (error) {
      setSnackbar({ open: true, message: 'Failed to switch provider', severity: 'error' });
    }
  };

  const deleteProvider = async (provider: string) => {
    try {
      await apiService.delete(`/api/v1/llm-providers/${provider}`);
      setSnackbar({ open: true, message: 'Provider deleted successfully', severity: 'success' });
      loadProviders();
    } catch (error) {
      setSnackbar({ open: true, message: 'Failed to delete provider', severity: 'error' });
    }
  };

  const runBenchmark = async () => {
    try {
      const enabledProviders = providers.filter(p => p.enabled).map(p => p.provider);
      const response = await apiService.post('/api/v1/llm-providers/benchmark', {
        providers: enabledProviders,
        iterations: 3,
      });
      
      // Poll for results
      const benchmarkId = response.data.benchmark_id;
      setTimeout(async () => {
        const results = await apiService.get(`/api/v1/llm-providers/benchmark/${benchmarkId}`);
        setBenchmarkResults(results.data);
      }, 5000);
      
      setSnackbar({ open: true, message: 'Benchmark started', severity: 'success' });
    } catch (error) {
      setSnackbar({ open: true, message: 'Failed to start benchmark', severity: 'error' });
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'error':
        return 'error';
      case 'testing':
        return 'warning';
      case 'rate_limited':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getHealthColor = (score: number) => {
    if (score >= 90) return '#4caf50';
    if (score >= 70) return '#ff9800';
    return '#f44336';
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <CloudQueue color="primary" />
        LLM Provider Configuration
      </Typography>

      <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
        <Tab label="Providers" />
        <Tab label="Usage & Stats" />
        <Tab label="Benchmarks" />
      </Tabs>

      {/* Providers Tab */}
      {tabValue === 0 && (
        <>
          <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between' }}>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => handleConfigProvider()}
            >
              Add Provider
            </Button>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="outlined"
                startIcon={<CompareArrows />}
                onClick={() => setBenchmarkDialog(true)}
              >
                Compare Providers
              </Button>
              <Button
                variant="outlined"
                startIcon={<Refresh />}
                onClick={loadProviders}
              >
                Refresh
              </Button>
            </Box>
          </Box>

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <Grid container spacing={3}>
              {providers.map((provider) => (
                <Grid item xs={12} key={provider.provider}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <Typography variant="h5">
                            {providerLogos[provider.provider]} {provider.provider.toUpperCase()}
                          </Typography>
                          <Chip
                            label={provider.status}
                            color={getStatusColor(provider.status)}
                            size="small"
                          />
                          {provider.is_active && (
                            <Chip label="Active" color="primary" size="small" icon={<Check />} />
                          )}
                        </Box>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Tooltip title="Test Connection">
                            <IconButton onClick={() => testProvider(provider.provider)}>
                              <PlayArrow />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Edit Configuration">
                            <IconButton onClick={() => handleConfigProvider(provider)}>
                              <Edit />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Make Active">
                            <IconButton
                              onClick={() => switchProvider(provider.provider)}
                              disabled={!provider.enabled}
                            >
                              <SwapHoriz />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Delete Provider">
                            <IconButton
                              onClick={() => deleteProvider(provider.provider)}
                              color="error"
                            >
                              <Delete />
                            </IconButton>
                          </Tooltip>
                          <IconButton
                            onClick={() => setExpandedProvider(
                              expandedProvider === provider.provider ? null : provider.provider
                            )}
                          >
                            {expandedProvider === provider.provider ? <ExpandLess /> : <ExpandMore />}
                          </IconButton>
                        </Box>
                      </Box>

                      <Box sx={{ mt: 2, display: 'flex', gap: 4 }}>
                        <Box>
                          <Typography variant="caption" color="textSecondary">Health Score</Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <LinearProgress
                              variant="determinate"
                              value={provider.health_score}
                              sx={{
                                width: 100,
                                height: 8,
                                borderRadius: 4,
                                backgroundColor: 'grey.200',
                                '& .MuiLinearProgress-bar': {
                                  backgroundColor: getHealthColor(provider.health_score),
                                }
                              }}
                            />
                            <Typography variant="body2">{provider.health_score}%</Typography>
                          </Box>
                        </Box>
                        <Box>
                          <Typography variant="caption" color="textSecondary">Priority</Typography>
                          <Typography variant="body1">{provider.priority}</Typography>
                        </Box>
                        <Box>
                          <Typography variant="caption" color="textSecondary">Models</Typography>
                          <Typography variant="body1">{Object.keys(provider.models).length}</Typography>
                        </Box>
                      </Box>

                      <Collapse in={expandedProvider === provider.provider}>
                        <Divider sx={{ my: 2 }} />
                        <Grid container spacing={2}>
                          <Grid item xs={12} md={6}>
                            <Typography variant="subtitle2" gutterBottom>Model Mappings</Typography>
                            <TableContainer component={Paper} variant="outlined">
                              <Table size="small">
                                <TableHead>
                                  <TableRow>
                                    <TableCell>Type</TableCell>
                                    <TableCell>Model</TableCell>
                                  </TableRow>
                                </TableHead>
                                <TableBody>
                                  {Object.entries(provider.models).map(([type, model]) => (
                                    <TableRow key={type}>
                                      <TableCell>{type}</TableCell>
                                      <TableCell>{model as string}</TableCell>
                                    </TableRow>
                                  ))}
                                </TableBody>
                              </Table>
                            </TableContainer>
                          </Grid>
                          <Grid item xs={12} md={6}>
                            <Typography variant="subtitle2" gutterBottom>Configuration</Typography>
                            <List dense>
                              <ListItem>
                                <ListItemText primary="Enabled" secondary={provider.enabled ? 'Yes' : 'No'} />
                              </ListItem>
                              <ListItem>
                                <ListItemText primary="Priority" secondary={provider.priority} />
                              </ListItem>
                              <ListItem>
                                <ListItemText primary="Status" secondary={provider.status} />
                              </ListItem>
                            </List>
                          </Grid>
                        </Grid>
                      </Collapse>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </>
      )}

      {/* Usage & Stats Tab */}
      {tabValue === 1 && (
        <Grid container spacing={3}>
          {providerStats.map((stat) => (
            <Grid item xs={12} key={stat.provider}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {providerLogos[stat.provider]} {stat.provider.toUpperCase()} Usage
                  </Typography>

                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="h4">{stat.total_requests}</Typography>
                        <Typography variant="caption">Total Requests</Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="h4" color="success.main">
                          {((stat.successful_requests / stat.total_requests) * 100).toFixed(1)}%
                        </Typography>
                        <Typography variant="caption">Success Rate</Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="h4">${stat.total_cost.toFixed(2)}</Typography>
                        <Typography variant="caption">Total Cost</Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="h4">{stat.average_response_time.toFixed(2)}s</Typography>
                        <Typography variant="caption">Avg Response Time</Typography>
                      </Paper>
                    </Grid>
                  </Grid>

                  <Box sx={{ mt: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>Last 7 Days</Typography>
                    <Box sx={{ height: 200 }}>
                      <Line
                        data={{
                          labels: stat.last_7_days.map(d => d.date),
                          datasets: [{
                            label: 'Requests',
                            data: stat.last_7_days.map(d => d.requests),
                            borderColor: 'rgb(75, 192, 192)',
                            tension: 0.1,
                          }],
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          scales: {
                            y: {
                              beginAtZero: true,
                            },
                          },
                        }}
                      />
                    </Box>
                  </Box>

                  <Box sx={{ mt: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>Usage by Model Type</Typography>
                    <Grid container spacing={1}>
                      {Object.entries(stat.by_model_type).map(([type, data]) => (
                        <Grid item xs={6} sm={4} md={3} key={type}>
                          <Paper sx={{ p: 1, textAlign: 'center' }}>
                            <Typography variant="body2">{type}</Typography>
                            <Typography variant="caption">
                              {(data as any).requests} requests
                            </Typography>
                          </Paper>
                        </Grid>
                      ))}
                    </Grid>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Benchmarks Tab */}
      {tabValue === 2 && (
        <Box>
          <Button
            variant="contained"
            startIcon={<Speed />}
            onClick={runBenchmark}
            sx={{ mb: 3 }}
          >
            Run Benchmark
          </Button>

          {benchmarkResults && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Benchmark Results</Typography>
                
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Provider</TableCell>
                        <TableCell align="right">Avg Response Time</TableCell>
                        <TableCell align="right">Success Rate</TableCell>
                        <TableCell align="right">Quality Score</TableCell>
                        <TableCell align="right">Cost per 1K Tokens</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {Object.entries(benchmarkResults.results).map(([provider, result]: [string, any]) => (
                        <TableRow key={provider}>
                          <TableCell>
                            {providerLogos[provider]} {provider}
                          </TableCell>
                          <TableCell align="right">{result.average_response_time.toFixed(3)}s</TableCell>
                          <TableCell align="right">{result.success_rate}%</TableCell>
                          <TableCell align="right">{result.quality_score}/100</TableCell>
                          <TableCell align="right">${result.cost_per_1k_tokens}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>

                {benchmarkResults.recommendations && (
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>Recommendations</Typography>
                    <List>
                      {benchmarkResults.recommendations.map((rec: string, index: number) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <TrendingUp color="primary" />
                          </ListItemIcon>
                          <ListItemText primary={rec} />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}
              </CardContent>
            </Card>
          )}
        </Box>
      )}

      {/* Configuration Dialog */}
      <Dialog open={configDialog} onClose={() => setConfigDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Configure {editConfig.provider.toUpperCase()} Provider
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Provider</InputLabel>
                  <Select
                    value={editConfig.provider}
                    onChange={(e) => setEditConfig({ ...editConfig, provider: e.target.value })}
                    label="Provider"
                  >
                    <MenuItem value="openai">OpenAI</MenuItem>
                    <MenuItem value="anthropic">Anthropic</MenuItem>
                    <MenuItem value="google">Google</MenuItem>
                    <MenuItem value="cohere">Cohere</MenuItem>
                    <MenuItem value="huggingface">HuggingFace</MenuItem>
                    <MenuItem value="azure_openai">Azure OpenAI</MenuItem>
                    <MenuItem value="aws_bedrock">AWS Bedrock</MenuItem>
                    <MenuItem value="local">Local</MenuItem>
                    <MenuItem value="custom">Custom</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="API Key"
                  type={showApiKey[editConfig.provider] ? 'text' : 'password'}
                  value={editConfig.api_key || ''}
                  onChange={(e) => setEditConfig({ ...editConfig, api_key: e.target.value })}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowApiKey({
                            ...showApiKey,
                            [editConfig.provider]: !showApiKey[editConfig.provider]
                          })}
                        >
                          {showApiKey[editConfig.provider] ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>

              {editConfig.provider === 'custom' && (
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="API Endpoint"
                    value={editConfig.api_endpoint || ''}
                    onChange={(e) => setEditConfig({ ...editConfig, api_endpoint: e.target.value })}
                  />
                </Grid>
              )}

              {editConfig.provider === 'openai' && (
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Organization ID (Optional)"
                    value={editConfig.organization_id || ''}
                    onChange={(e) => setEditConfig({ ...editConfig, organization_id: e.target.value })}
                  />
                </Grid>
              )}

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Max Tokens"
                  type="number"
                  value={editConfig.max_tokens || 4096}
                  onChange={(e) => setEditConfig({ ...editConfig, max_tokens: parseInt(e.target.value) })}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Temperature"
                  type="number"
                  inputProps={{ step: 0.1, min: 0, max: 2 }}
                  value={editConfig.temperature || 0.7}
                  onChange={(e) => setEditConfig({ ...editConfig, temperature: parseFloat(e.target.value) })}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Priority"
                  type="number"
                  value={editConfig.priority}
                  onChange={(e) => setEditConfig({ ...editConfig, priority: parseInt(e.target.value) })}
                  helperText="Higher priority providers are preferred"
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={editConfig.enabled}
                      onChange={(e) => setEditConfig({ ...editConfig, enabled: e.target.checked })}
                    />
                  }
                  label="Enabled"
                />
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>Model Mappings</Typography>
                {modelTypes.map((type) => (
                  <TextField
                    key={type}
                    fullWidth
                    label={type.charAt(0).toUpperCase() + type.slice(1)}
                    value={editConfig.model_mappings[type] || ''}
                    onChange={(e) => setEditConfig({
                      ...editConfig,
                      model_mappings: {
                        ...editConfig.model_mappings,
                        [type]: e.target.value
                      }
                    })}
                    sx={{ mb: 1 }}
                    size="small"
                  />
                ))}
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfigDialog(false)}>Cancel</Button>
          <Button onClick={() => testProvider(editConfig.provider)} startIcon={<PlayArrow />}>
            Test
          </Button>
          <Button onClick={saveConfiguration} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>

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

export default LLMProviderConfig;