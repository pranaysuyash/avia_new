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
  Accordion,
  AccordionSummary,
  AccordionDetails,
  ToggleButton,
  ToggleButtonGroup,
  Badge,
  Avatar,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  FormHelperText,
  Slider,
  Stack,
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
  ContentCopy,
  OpenInNew,
  Help,
  Info,
  Download,
  Upload,
  RestartAlt,
  Analytics,
  Memory,
  Timer,
  DataUsage,
  Cached,
  SyncAlt,
  Psychology,
  SmartToy,
  ModelTraining,
  Api,
  Key,
  Lock,
  LockOpen,
} from '@mui/icons-material';
import { apiClient } from '../../services/api';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  ChartTooltip,
  Legend,
  ArcElement
);

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

interface BenchmarkResult {
  provider: string;
  average_response_time: number;
  success_rate: number;
  quality_score: number;
  cost_per_1k_tokens: number;
  test_results: Array<{
    test_case: string;
    response_time: number;
    success: boolean;
    score: number;
  }>;
}

const providerInfo: Record<string, { logo: string; color: string; description: string }> = {
  openai: { 
    logo: '🤖', 
    color: '#00A67E',
    description: 'Industry-leading AI models including GPT-4' 
  },
  anthropic: { 
    logo: '🧠', 
    color: '#6B46C1',
    description: 'Claude AI with strong reasoning capabilities' 
  },
  google: { 
    logo: '🔍', 
    color: '#4285F4',
    description: 'Gemini models with multimodal capabilities' 
  },
  cohere: { 
    logo: '🌊', 
    color: '#39A0CA',
    description: 'Specialized in enterprise NLP tasks' 
  },
  huggingface: { 
    logo: '🤗', 
    color: '#FFD21E',
    description: 'Open-source model hub and inference' 
  },
  azure_openai: { 
    logo: '☁️', 
    color: '#0078D4',
    description: 'Enterprise-grade OpenAI models on Azure' 
  },
  aws_bedrock: { 
    logo: '🏛️', 
    color: '#FF9900',
    description: 'Managed foundation models on AWS' 
  },
  local: { 
    logo: '💻', 
    color: '#424242',
    description: 'Self-hosted models for privacy' 
  },
  custom: { 
    logo: '⚙️', 
    color: '#757575',
    description: 'Custom API endpoints' 
  },
};

const modelTypes = ['chat', 'completion', 'embedding', 'transcription', 'translation', 'summarization'];

const LLMProviderSettings: React.FC = () => {
  const [providers, setProviders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const [configDialog, setConfigDialog] = useState(false);
  const [testDialog, setTestDialog] = useState(false);
  const [benchmarkDialog, setBenchmarkDialog] = useState(false);
  const [importExportDialog, setImportExportDialog] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [showApiKey, setShowApiKey] = useState<Record<string, boolean>>({});
  const [expandedProvider, setExpandedProvider] = useState<string | null>(null);
  const [providerStats, setProviderStats] = useState<ProviderUsageStats[]>([]);
  const [benchmarkResults, setBenchmarkResults] = useState<BenchmarkResult[]>([]);
  const [testResults, setTestResults] = useState<any>(null);
  const [activeStep, setActiveStep] = useState(0);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>(
    {
      open: false,
      message: '',
      severity: 'success',
    }
  );

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

  useEffect(() => {
    if (tabValue === 2) {
      loadBenchmarkHistory();
    }
  }, [tabValue]);

  const loadProviders = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/api/v1/llm-providers/');
      setProviders(response.data);
    } catch (error) {
      console.error('Failed to load providers:', error);
      setSnackbar({ open: true, message: 'Failed to load providers', severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const loadProviderStats = async () => {
    try {
      const response = await apiClient.get('/api/v1/llm-providers/usage/stats');
      setProviderStats(response.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const loadBenchmarkHistory = async () => {
    try {
      // In a real implementation, this would load historical benchmark data
      const mockData: BenchmarkResult[] = [
        {
          provider: 'openai',
          average_response_time: 0.523,
          success_rate: 99.8,
          quality_score: 95,
          cost_per_1k_tokens: 0.03,
          test_results: [],
        },
        {
          provider: 'anthropic',
          average_response_time: 0.612,
          success_rate: 99.5,
          quality_score: 93,
          cost_per_1k_tokens: 0.025,
          test_results: [],
        },
      ];
      setBenchmarkResults(mockData);
    } catch (error) {
      console.error('Failed to load benchmark history:', error);
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
    setActiveStep(0);
    setConfigDialog(true);
  };

  const saveConfiguration = async () => {
    try {
      await apiClient.post('/api/v1/llm-providers/configure', editConfig);
      setSnackbar({ open: true, message: 'Provider configured successfully', severity: 'success' });
      setConfigDialog(false);
      loadProviders();
    } catch (error) {
      setSnackbar({ open: true, message: 'Failed to configure provider', severity: 'error' });
    }
  };

  const testProvider = async (provider: string, fullTest: boolean = false) => {
    try {
      setTestResults(null);
      const config = providers.find(p => p.provider === provider);
      const response = await apiClient.post('/api/v1/llm-providers/test', {
        provider,
        config: editConfig.provider === provider ? editConfig : config,
        test_prompt: fullTest ? 'Explain quantum computing in simple terms.' : 'Hello, can you respond?',
      });

      setTestResults(response.data);
      
      if (response.data.success) {
        setSnackbar({ open: true, message: 'Provider test successful', severity: 'success' });
      } else {
        setSnackbar({ open: true, message: `Test failed: ${response.data.error}`, severity: 'error' });
      }
    } catch (error) {
      setSnackbar({ open: true, message: 'Provider test failed', severity: 'error' });
      setTestResults({ success: false, error: 'Connection failed' });
    }
  };

  const switchProvider = async (provider: string, modelType?: string) => {
    try {
      await apiClient.put('/api/v1/llm-providers/switch', {
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
      await apiClient.delete(`/api/v1/llm-providers/${provider}`);
      setSnackbar({ open: true, message: 'Provider deleted successfully', severity: 'success' });
      loadProviders();
    } catch (error) {
      setSnackbar({ open: true, message: 'Failed to delete provider', severity: 'error' });
    }
  };

  const runBenchmark = async () => {
    try {
      const enabledProviders = providers.filter(p => p.enabled).map(p => p.provider);
      const response = await apiClient.post('/api/v1/llm-providers/benchmark', {
        providers: enabledProviders,
        iterations: 3,
      });

      setSnackbar({ open: true, message: 'Benchmark started', severity: 'success' });
      setBenchmarkDialog(false);

      // Poll for results
      setTimeout(async () => {
        const results = await apiClient.get(`/api/v1/llm-providers/benchmark/${response.data.benchmark_id}`);
        loadBenchmarkHistory();
      }, 5000);
    } catch (error) {
      setSnackbar({ open: true, message: 'Failed to start benchmark', severity: 'error' });
    }
  };

  const exportConfiguration = () => {
    const config = {
      providers: providers.map(p => ({
        ...p,
        api_key: undefined, // Don't export API keys
      })),
      timestamp: new Date().toISOString(),
    };
    
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'llm-providers-config.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  const importConfiguration = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          const config = JSON.parse(e.target?.result as string);
          // Process and validate imported config
          setSnackbar({ open: true, message: 'Configuration imported successfully', severity: 'success' });
          setImportExportDialog(false);
          loadProviders();
        } catch (error) {
          setSnackbar({ open: true, message: 'Invalid configuration file', severity: 'error' });
        }
      };
      reader.readAsText(file);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      case 'testing':
        return <Cached color="warning" />;
      case 'rate_limited':
        return <Timer color="warning" />;
      default:
        return <Close color="disabled" />;
    }
  };

  const getHealthColor = (score: number) => {
    if (score >= 90) return '#4caf50';
    if (score >= 70) return '#ff9800';
    return '#f44336';
  };

  const renderProviderCard = (provider: any) => {
    const providerDetails = providerInfo[provider.provider] || providerInfo.custom;
    const stats = providerStats.find(s => s.provider === provider.provider);

    return (
      <Card key={provider.provider} sx={{ mb: 2, border: provider.is_active ? '2px solid' : '1px solid', borderColor: provider.is_active ? 'primary.main' : 'divider' }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Avatar sx={{ bgcolor: providerDetails.color, width: 56, height: 56 }}>
                <Typography variant="h5">{providerDetails.logo}</Typography>
              </Avatar>
              <Box>
                <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {provider.provider.toUpperCase()}
                  {provider.is_active && (
                    <Chip label="Active" color="primary" size="small" icon={<Check />} />
                  )}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  {providerDetails.description}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                  {getStatusIcon(provider.status)}
                  <Typography variant="caption" color="textSecondary">
                    Status: {provider.status}
                  </Typography>
                  <Chip
                    label={`Priority: ${provider.priority}`}
                    size="small"
                    variant="outlined"
                  />
                </Box>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Tooltip title="Test Connection">
                <IconButton onClick={() => testProvider(provider.provider)}>
                  <PlayArrow />
                </IconButton>
              </Tooltip>
              <Tooltip title="Configure">
                <IconButton onClick={() => handleConfigProvider(provider)}>
                  <Edit />
                </IconButton>
              </Tooltip>
              <Tooltip title="Make Active">
                <IconButton
                  onClick={() => switchProvider(provider.provider)}
                  disabled={!provider.enabled}
                  color={provider.is_active ? 'primary' : 'default'}
                >
                  <SwapHoriz />
                </IconButton>
              </Tooltip>
              <Tooltip title="Delete">
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
                <ExpandMore
                  sx={{
                    transform: expandedProvider === provider.provider ? 'rotate(180deg)' : 'rotate(0deg)',
                    transition: 'transform 0.3s',
                  }}
                />
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
            {stats && (
              <>
                <Box>
                  <Typography variant="caption" color="textSecondary">Requests Today</Typography>
                  <Typography variant="body1">{stats.total_requests}</Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="textSecondary">Avg Response</Typography>
                  <Typography variant="body1">{stats.average_response_time.toFixed(2)}s</Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="textSecondary">Success Rate</Typography>
                  <Typography variant="body1">
                    {((stats.successful_requests / stats.total_requests) * 100).toFixed(1)}%
                  </Typography>
                </Box>
              </>
            )}
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
                      {Object.entries(provider.models || {}).map(([type, model]) => (
                        <TableRow key={type}>
                          <TableCell>{type}</TableCell>
                          <TableCell>
                            <Chip label={model as string} size="small" variant="outlined" />
                          </TableCell>
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
                    <ListItemText 
                      primary="Enabled" 
                      secondary={provider.enabled ? 'Yes' : 'No'} 
                    />
                    <ListItemSecondaryAction>
                      <Switch checked={provider.enabled} disabled />
                    </ListItemSecondaryAction>
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Rate Limit" 
                      secondary={provider.rate_limit ? `${provider.rate_limit} req/min` : 'Unlimited'} 
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Timeout" 
                      secondary={`${provider.timeout || 30} seconds`} 
                    />
                  </ListItem>
                </List>
                {stats && (
                  <>
                    <Divider sx={{ my: 1 }} />
                    <Typography variant="subtitle2" gutterBottom>Usage Stats</Typography>
                    <Box sx={{ height: 150 }}>
                      <Line
                        data={{
                          labels: stats.last_7_days.map(d => d.date.split('-').pop()),
                          datasets: [{
                            label: 'Daily Requests',
                            data: stats.last_7_days.map(d => d.requests),
                            borderColor: providerDetails.color,
                            backgroundColor: `${providerDetails.color}20`,
                            tension: 0.1,
                          }],
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            legend: { display: false },
                          },
                          scales: {
                            y: { beginAtZero: true },
                          },
                        }}
                      />
                    </Box>
                  </>
                )}
              </Grid>
            </Grid>
          </Collapse>
        </CardContent>
      </Card>
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <CloudQueue color="primary" />
        LLM Provider Settings
      </Typography>

      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="body1" color="textSecondary">
          Configure and manage multiple LLM providers for optimal performance and cost
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Download />}
            onClick={() => setImportExportDialog(true)}
          >
            Import/Export
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => handleConfigProvider()}
          >
            Add Provider
          </Button>
        </Box>
      </Box>

      <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
        <Tab label="Providers" icon={<CloudQueue />} iconPosition="start" />
        <Tab label="Usage Analytics" icon={<Analytics />} iconPosition="start" />
        <Tab label="Benchmarks" icon={<Speed />} iconPosition="start" />
        <Tab label="Advanced" icon={<Settings />} iconPosition="start" />
      </Tabs>

      {/* Providers Tab */}
      {tabValue === 0 && (
        <Box>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : providers.length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <SmartToy sx={{ fontSize: 64, color: 'text.secondary' }} />
              <Typography variant="h6" sx={{ mt: 2 }}>
                No providers configured
              </Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mt: 1, mb: 3 }}>
                Add your first LLM provider to get started
              </Typography>
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={() => handleConfigProvider()}
              >
                Add Provider
              </Button>
            </Paper>
          ) : (
            <>
              <Box sx={{ mb: 3, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
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
              {providers.map(provider => renderProviderCard(provider))}
            </>
          )}
        </Box>
      )}

      {/* Usage Analytics Tab */}
      {tabValue === 1 && (
        <Grid container spacing={3}>
          {providerStats.length === 0 ? (
            <Grid item xs={12}>
              <Paper sx={{ p: 4, textAlign: 'center' }}>
                <DataUsage sx={{ fontSize: 64, color: 'text.secondary' }} />
                <Typography variant="h6" sx={{ mt: 2 }}>
                  No usage data available
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                  Start using providers to see analytics
                </Typography>
              </Paper>
            </Grid>
          ) : (
            <>
              {/* Summary Cards */}
              <Grid item xs={12}>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Paper sx={{ p: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Box>
                          <Typography variant="h4">
                            {providerStats.reduce((sum, stat) => sum + stat.total_requests, 0)}
                          </Typography>
                          <Typography variant="body2" color="textSecondary">
                            Total Requests
                          </Typography>
                        </Box>
                        <DataUsage color="primary" sx={{ fontSize: 40 }} />
                      </Box>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Paper sx={{ p: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Box>
                          <Typography variant="h4">
                            {(providerStats.reduce((sum, stat) => sum + stat.total_tokens, 0) / 1000).toFixed(1)}k
                          </Typography>
                          <Typography variant="body2" color="textSecondary">
                            Total Tokens
                          </Typography>
                        </Box>
                        <Memory color="secondary" sx={{ fontSize: 40 }} />
                      </Box>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Paper sx={{ p: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Box>
                          <Typography variant="h4">
                            ${providerStats.reduce((sum, stat) => sum + stat.total_cost, 0).toFixed(2)}
                          </Typography>
                          <Typography variant="body2" color="textSecondary">
                            Total Cost
                          </Typography>
                        </Box>
                        <AttachMoney color="success" sx={{ fontSize: 40 }} />
                      </Box>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Paper sx={{ p: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Box>
                          <Typography variant="h4">
                            {(providerStats.reduce((sum, stat) => sum + stat.uptime_percentage, 0) / providerStats.length).toFixed(1)}%
                          </Typography>
                          <Typography variant="body2" color="textSecondary">
                            Avg Uptime
                          </Typography>
                        </Box>
                        <TrendingUp color="info" sx={{ fontSize: 40 }} />
                      </Box>
                    </Paper>
                  </Grid>
                </Grid>
              </Grid>

              {/* Provider Usage Details */}
              {providerStats.map((stat) => {
                const providerDetails = providerInfo[stat.provider] || providerInfo.custom;
                return (
                  <Grid item xs={12} key={stat.provider}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Avatar sx={{ bgcolor: providerDetails.color, width: 32, height: 32 }}>
                            <Typography variant="body1">{providerDetails.logo}</Typography>
                          </Avatar>
                          {stat.provider.toUpperCase()} Usage
                        </Typography>

                        <Grid container spacing={2}>
                          <Grid item xs={12} md={8}>
                            <Box sx={{ height: 200 }}>
                              <Line
                                data={{
                                  labels: stat.last_7_days.map(d => d.date.split('-').pop()),
                                  datasets: [{
                                    label: 'Requests',
                                    data: stat.last_7_days.map(d => d.requests),
                                    borderColor: providerDetails.color,
                                    backgroundColor: `${providerDetails.color}20`,
                                    yAxisID: 'y',
                                  }, {
                                    label: 'Tokens (k)',
                                    data: stat.last_7_days.map(d => d.tokens / 1000),
                                    borderColor: '#ff9800',
                                    backgroundColor: '#ff980020',
                                    yAxisID: 'y1',
                                  }],
                                }}
                                options={{
                                  responsive: true,
                                  maintainAspectRatio: false,
                                  interaction: {
                                    mode: 'index',
                                    intersect: false,
                                  },
                                  scales: {
                                    y: {
                                      type: 'linear',
                                      display: true,
                                      position: 'left',
                                    },
                                    y1: {
                                      type: 'linear',
                                      display: true,
                                      position: 'right',
                                      grid: {
                                        drawOnChartArea: false,
                                      },
                                    },
                                  },
                                }}
                              />
                            </Box>
                          </Grid>
                          <Grid item xs={12} md={4}>
                            <Box sx={{ height: 200 }}>
                              <Doughnut
                                data={{
                                  labels: Object.keys(stat.by_model_type),
                                  datasets: [{
                                    data: Object.values(stat.by_model_type).map((v: any) => v.requests),
                                    backgroundColor: [
                                      '#4caf50',
                                      '#2196f3',
                                      '#ff9800',
                                      '#f44336',
                                      '#9c27b0',
                                      '#00bcd4',
                                    ],
                                  }],
                                }}
                                options={{
                                  responsive: true,
                                  maintainAspectRatio: false,
                                  plugins: {
                                    legend: {
                                      position: 'right',
                                    },
                                  },
                                }}
                              />
                            </Box>
                          </Grid>
                        </Grid>

                        <Box sx={{ mt: 3, display: 'flex', gap: 4 }}>
                          <Box>
                            <Typography variant="body2" color="textSecondary">Success Rate</Typography>
                            <Typography variant="h6" color="success.main">
                              {((stat.successful_requests / stat.total_requests) * 100).toFixed(1)}%
                            </Typography>
                          </Box>
                          <Box>
                            <Typography variant="body2" color="textSecondary">Avg Response Time</Typography>
                            <Typography variant="h6">
                              {stat.average_response_time.toFixed(2)}s
                            </Typography>
                          </Box>
                          <Box>
                            <Typography variant="body2" color="textSecondary">Cost per 1K Tokens</Typography>
                            <Typography variant="h6">
                              ${(stat.total_cost / (stat.total_tokens / 1000)).toFixed(3)}
                            </Typography>
                          </Box>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                );
              })}
            </>
          )}
        </Grid>
      )}

      {/* Benchmarks Tab */}
      {tabValue === 2 && (
        <Box>
          <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">Provider Performance Comparison</Typography>
            <Button
              variant="contained"
              startIcon={<Speed />}
              onClick={() => setBenchmarkDialog(true)}
            >
              Run New Benchmark
            </Button>
          </Box>

          {benchmarkResults.length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Speed sx={{ fontSize: 64, color: 'text.secondary' }} />
              <Typography variant="h6" sx={{ mt: 2 }}>
                No benchmark data available
              </Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mt: 1, mb: 3 }}>
                Run a benchmark to compare provider performance
              </Typography>
              <Button
                variant="contained"
                startIcon={<Speed />}
                onClick={() => setBenchmarkDialog(true)}
              >
                Run Benchmark
              </Button>
            </Paper>
          ) : (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Provider</TableCell>
                        <TableCell align="right">Avg Response Time</TableCell>
                        <TableCell align="right">Success Rate</TableCell>
                        <TableCell align="right">Quality Score</TableCell>
                        <TableCell align="right">Cost per 1K Tokens</TableCell>
                        <TableCell align="right">Overall Score</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {benchmarkResults.map((result) => {
                        const providerDetails = providerInfo[result.provider] || providerInfo.custom;
                        const overallScore = (
                          (100 - result.average_response_time * 50) * 0.25 +
                          result.success_rate * 0.25 +
                          result.quality_score * 0.35 +
                          (100 - result.cost_per_1k_tokens * 100) * 0.15
                        ).toFixed(1);

                        return (
                          <TableRow key={result.provider}>
                            <TableCell>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Avatar sx={{ bgcolor: providerDetails.color, width: 32, height: 32 }}>
                                  <Typography variant="body2">{providerDetails.logo}</Typography>
                                </Avatar>
                                {result.provider.toUpperCase()}
                              </Box>
                            </TableCell>
                            <TableCell align="right">
                              <Chip 
                                label={`${result.average_response_time.toFixed(3)}s`}
                                color={result.average_response_time < 0.5 ? 'success' : result.average_response_time < 1 ? 'warning' : 'error'}
                                size="small"
                              />
                            </TableCell>
                            <TableCell align="right">
                              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 1 }}>
                                <LinearProgress
                                  variant="determinate"
                                  value={result.success_rate}
                                  sx={{ width: 60, height: 6, borderRadius: 3 }}
                                />
                                <Typography variant="body2">{result.success_rate}%</Typography>
                              </Box>
                            </TableCell>
                            <TableCell align="right">
                              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 1 }}>
                                <LinearProgress
                                  variant="determinate"
                                  value={result.quality_score}
                                  sx={{ 
                                    width: 60, 
                                    height: 6, 
                                    borderRadius: 3,
                                    backgroundColor: 'grey.200',
                                    '& .MuiLinearProgress-bar': {
                                      backgroundColor: getHealthColor(result.quality_score),
                                    }
                                  }}
                                />
                                <Typography variant="body2">{result.quality_score}/100</Typography>
                              </Box>
                            </TableCell>
                            <TableCell align="right">${result.cost_per_1k_tokens}</TableCell>
                            <TableCell align="right">
                              <Chip
                                label={overallScore}
                                color={parseFloat(overallScore) > 80 ? 'success' : parseFloat(overallScore) > 60 ? 'warning' : 'error'}
                                variant="outlined"
                              />
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Performance Comparison</Typography>
                    <Box sx={{ height: 300 }}>
                      <Bar
                        data={{
                          labels: benchmarkResults.map(r => r.provider),
                          datasets: [
                            {
                              label: 'Response Time (s)',
                              data: benchmarkResults.map(r => r.average_response_time),
                              backgroundColor: '#2196f3',
                            },
                            {
                              label: 'Quality Score (/100)',
                              data: benchmarkResults.map(r => r.quality_score / 100),
                              backgroundColor: '#4caf50',
                            },
                            {
                              label: 'Cost ($/1k)',
                              data: benchmarkResults.map(r => r.cost_per_1k_tokens),
                              backgroundColor: '#ff9800',
                            },
                          ],
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                        }}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Recommendations</Typography>
                    <List>
                      <ListItem>
                        <ListItemIcon>
                          <TrendingUp color="primary" />
                        </ListItemIcon>
                        <ListItemText
                          primary="Best Overall Performance"
                          secondary={`${benchmarkResults[0]?.provider.toUpperCase()} offers the best balance of speed and quality`}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemIcon>
                          <AttachMoney color="success" />
                        </ListItemIcon>
                        <ListItemText
                          primary="Most Cost Effective"
                          secondary={`Consider using ${benchmarkResults.sort((a, b) => a.cost_per_1k_tokens - b.cost_per_1k_tokens)[0]?.provider.toUpperCase()} for cost-sensitive tasks`}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemIcon>
                          <Speed color="secondary" />
                        </ListItemIcon>
                        <ListItemText
                          primary="Fastest Response"
                          secondary={`${benchmarkResults.sort((a, b) => a.average_response_time - b.average_response_time)[0]?.provider.toUpperCase()} provides the quickest responses`}
                        />
                      </ListItem>
                    </List>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </Box>
      )}

      {/* Advanced Tab */}
      {tabValue === 3 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <SyncAlt />
                  Fallback Configuration
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                  Configure automatic fallback when a provider fails
                </Typography>
                <List>
                  {providers
                    .sort((a, b) => b.priority - a.priority)
                    .map((provider, index) => (
                      <ListItem key={provider.provider}>
                        <ListItemIcon>
                          <Typography variant="h6">{index + 1}</Typography>
                        </ListItemIcon>
                        <ListItemText
                          primary={provider.provider.toUpperCase()}
                          secondary={`Priority: ${provider.priority}`}
                        />
                        <ListItemSecondaryAction>
                          <IconButton size="small" disabled={index === 0}>
                            <ExpandLess />
                          </IconButton>
                          <IconButton size="small" disabled={index === providers.length - 1}>
                            <ExpandMore />
                          </IconButton>
                        </ListItemSecondaryAction>
                      </ListItem>
                    ))}
                </List>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Psychology />
                  Model Selection Strategy
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                  Configure how models are selected for different tasks
                </Typography>
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Selection Strategy</InputLabel>
                  <Select defaultValue="cost_optimized" label="Selection Strategy">
                    <MenuItem value="performance">Performance First</MenuItem>
                    <MenuItem value="cost_optimized">Cost Optimized</MenuItem>
                    <MenuItem value="balanced">Balanced</MenuItem>
                    <MenuItem value="manual">Manual Selection</MenuItem>
                  </Select>
                </FormControl>
                <Typography variant="subtitle2" gutterBottom>Task-Specific Preferences</Typography>
                {modelTypes.map((type) => (
                  <Box key={type} sx={{ mb: 1 }}>
                    <Typography variant="body2">{type.charAt(0).toUpperCase() + type.slice(1)}</Typography>
                    <Slider
                      defaultValue={50}
                      marks={[
                        { value: 0, label: 'Cost' },
                        { value: 100, label: 'Quality' },
                      ]}
                      sx={{ mt: 1 }}
                    />
                  </Box>
                ))}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Api />
                  API Configuration
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={4}>
                    <TextField
                      fullWidth
                      label="Global Timeout (seconds)"
                      type="number"
                      defaultValue={30}
                      helperText="Maximum time to wait for any API response"
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      fullWidth
                      label="Retry Attempts"
                      type="number"
                      defaultValue={3}
                      helperText="Number of retries on failure"
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      fullWidth
                      label="Retry Delay (ms)"
                      type="number"
                      defaultValue={1000}
                      helperText="Delay between retry attempts"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Enable request caching"
                    />
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Enable automatic rate limiting"
                    />
                    <FormControlLabel
                      control={<Switch />}
                      label="Log all API requests (verbose)"
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Configuration Dialog */}
      <Dialog open={configDialog} onClose={() => setConfigDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Configure {editConfig.provider.toUpperCase()} Provider
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Stepper activeStep={activeStep} orientation="vertical">
              {/* Step 1: Basic Configuration */}
              <Step>
                <StepLabel>Basic Configuration</StepLabel>
                <StepContent>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <FormControl fullWidth>
                        <InputLabel>Provider</InputLabel>
                        <Select
                          value={editConfig.provider}
                          onChange={(e) => setEditConfig({ ...editConfig, provider: e.target.value })}
                          label="Provider"
                        >
                          {Object.entries(providerInfo).map(([key, info]) => (
                            <MenuItem key={key} value={key}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Typography>{info.logo}</Typography>
                                {key.toUpperCase()}
                              </Box>
                            </MenuItem>
                          ))}
                        </Select>
                        <FormHelperText>{providerInfo[editConfig.provider]?.description}</FormHelperText>
                      </FormControl>
                    </Grid>

                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="API Key"
                        type={showApiKey[editConfig.provider] ? 'text' : 'password'}
                        value={editConfig.api_key || ''}
                        onChange={(e) => setEditConfig({ ...editConfig, api_key: e.target.value })}
                        required
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
                        helperText="Your API key is encrypted and stored securely"
                      />
                    </Grid>

                    {editConfig.provider === 'custom' && (
                      <Grid item xs={12}>
                        <TextField
                          fullWidth
                          label="API Endpoint"
                          value={editConfig.api_endpoint || ''}
                          onChange={(e) => setEditConfig({ ...editConfig, api_endpoint: e.target.value })}
                          helperText="Custom API endpoint URL"
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

                    {editConfig.provider === 'google' && (
                      <Grid item xs={12}>
                        <TextField
                          fullWidth
                          label="Project ID"
                          value={editConfig.project_id || ''}
                          onChange={(e) => setEditConfig({ ...editConfig, project_id: e.target.value })}
                        />
                      </Grid>
                    )}

                    {(editConfig.provider === 'azure_openai' || editConfig.provider === 'aws_bedrock') && (
                      <Grid item xs={12}>
                        <TextField
                          fullWidth
                          label="Region"
                          value={editConfig.region || ''}
                          onChange={(e) => setEditConfig({ ...editConfig, region: e.target.value })}
                          helperText="Cloud provider region"
                        />
                      </Grid>
                    )}

                    <Grid item xs={12}>
                      <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                        <Button onClick={() => setConfigDialog(false)}>Cancel</Button>
                        <Button 
                          variant="contained" 
                          onClick={() => setActiveStep(1)}
                          disabled={!editConfig.api_key && editConfig.provider !== 'local'}
                        >
                          Next
                        </Button>
                      </Box>
                    </Grid>
                  </Grid>
                </StepContent>
              </Step>

              {/* Step 2: Model Configuration */}
              <Step>
                <StepLabel>Model Configuration</StepLabel>
                <StepContent>
                  <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                    Map model types to specific models for this provider
                  </Typography>
                  <Grid container spacing={2}>
                    {modelTypes.map((type) => (
                      <Grid item xs={12} sm={6} key={type}>
                        <TextField
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
                          size="small"
                          helperText={`Model for ${type} tasks`}
                        />
                      </Grid>
                    ))}
                    <Grid item xs={12}>
                      <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                        <Button onClick={() => setActiveStep(0)}>Back</Button>
                        <Button variant="contained" onClick={() => setActiveStep(2)}>
                          Next
                        </Button>
                      </Box>
                    </Grid>
                  </Grid>
                </StepContent>
              </Step>

              {/* Step 3: Advanced Settings */}
              <Step>
                <StepLabel>Advanced Settings</StepLabel>
                <StepContent>
                  <Grid container spacing={2}>
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
                      <Box>
                        <Typography variant="body2" gutterBottom>
                          Temperature: {editConfig.temperature || 0.7}
                        </Typography>
                        <Slider
                          value={editConfig.temperature || 0.7}
                          onChange={(e, value) => setEditConfig({ ...editConfig, temperature: value as number })}
                          min={0}
                          max={2}
                          step={0.1}
                          marks={[
                            { value: 0, label: 'Precise' },
                            { value: 1, label: 'Balanced' },
                            { value: 2, label: 'Creative' },
                          ]}
                        />
                      </Box>
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
                      <TextField
                        fullWidth
                        label="Timeout (seconds)"
                        type="number"
                        value={editConfig.timeout || 30}
                        onChange={(e) => setEditConfig({ ...editConfig, timeout: parseInt(e.target.value) })}
                      />
                    </Grid>

                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="Rate Limit (req/min)"
                        type="number"
                        value={editConfig.rate_limit || ''}
                        onChange={(e) => setEditConfig({ ...editConfig, rate_limit: parseInt(e.target.value) })}
                        helperText="Leave empty for unlimited"
                      />
                    </Grid>

                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="Retry Attempts"
                        type="number"
                        value={editConfig.retry_attempts || 3}
                        onChange={(e) => setEditConfig({ ...editConfig, retry_attempts: parseInt(e.target.value) })}
                      />
                    </Grid>

                    <Grid item xs={12}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={editConfig.enabled}
                            onChange={(e) => setEditConfig({ ...editConfig, enabled: e.target.checked })}
                          />
                        }
                        label="Enable this provider"
                      />
                    </Grid>

                    <Grid item xs={12}>
                      <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                        <Button onClick={() => setActiveStep(1)}>Back</Button>
                        <Button onClick={() => testProvider(editConfig.provider, true)} startIcon={<PlayArrow />}>
                          Test Connection
                        </Button>
                        <Button onClick={saveConfiguration} variant="contained">
                          Save Configuration
                        </Button>
                      </Box>
                    </Grid>
                  </Grid>
                </StepContent>
              </Step>
            </Stepper>

            {testResults && (
              <Alert 
                severity={testResults.success ? 'success' : 'error'} 
                sx={{ mt: 2 }}
                action={
                  <IconButton size="small" onClick={() => setTestResults(null)}>
                    <Close />
                  </IconButton>
                }
              >
                {testResults.success ? (
                  <>
                    Connection successful! Response time: {testResults.response_time.toFixed(3)}s
                    {testResults.model_info && (
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="body2">
                          Model: {testResults.model_info.model}
                        </Typography>
                      </Box>
                    )}
                  </>
                ) : (
                  <>Test failed: {testResults.error}</>
                )}
              </Alert>
            )}
          </Box>
        </DialogContent>
      </Dialog>

      {/* Benchmark Dialog */}
      <Dialog open={benchmarkDialog} onClose={() => setBenchmarkDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Run Provider Benchmark</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            Compare performance, quality, and cost across your enabled providers
          </Typography>
          <Alert severity="info" sx={{ mb: 2 }}>
            This will send test prompts to all enabled providers and may incur API costs
          </Alert>
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Test Type</InputLabel>
            <Select defaultValue="standard" label="Test Type">
              <MenuItem value="quick">Quick (3 tests)</MenuItem>
              <MenuItem value="standard">Standard (10 tests)</MenuItem>
              <MenuItem value="comprehensive">Comprehensive (25 tests)</MenuItem>
            </Select>
          </FormControl>
          <FormControlLabel
            control={<Switch defaultChecked />}
            label="Include quality assessment"
          />
          <FormControlLabel
            control={<Switch defaultChecked />}
            label="Test all model types"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBenchmarkDialog(false)}>Cancel</Button>
          <Button onClick={runBenchmark} variant="contained" startIcon={<Speed />}>
            Start Benchmark
          </Button>
        </DialogActions>
      </Dialog>

      {/* Import/Export Dialog */}
      <Dialog open={importExportDialog} onClose={() => setImportExportDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Import/Export Configuration</DialogTitle>
        <DialogContent>
          <Box sx={{ textAlign: 'center', py: 2 }}>
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={exportConfiguration}
              fullWidth
              sx={{ mb: 2 }}
            >
              Export Current Configuration
            </Button>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
              OR
            </Typography>
            <Button
              variant="outlined"
              component="label"
              startIcon={<Upload />}
              fullWidth
            >
              Import Configuration
              <input
                type="file"
                accept=".json"
                hidden
                onChange={importConfiguration}
              />
            </Button>
          </Box>
          <Alert severity="warning" sx={{ mt: 2 }}>
            API keys are not included in exports for security. You'll need to re-enter them after import.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setImportExportDialog(false)}>Close</Button>
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

export default LLMProviderSettings;