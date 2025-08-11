/**
 * Advanced Analytics Component
 * Provides comprehensive analytics, reporting, and data visualization
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  IconButton,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Tab,
  Tabs,
  CircularProgress,
  Alert,
  Snackbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Autocomplete,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  LinearProgress,
  Skeleton,
  Divider,
  Stack,
  Switch,
  FormControlLabel,
  Badge,
  SpeedDial,
  SpeedDialAction,
  SpeedDialIcon,
} from '@mui/material';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import {
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
  Download as DownloadIcon,
  Share as ShareIcon,
  FilterList as FilterListIcon,
  Schedule as ScheduleIcon,
  Insights as InsightsIcon,
  ShowChart as ShowChartIcon,
  BarChart as BarChartIcon,
  PieChart as PieChartIcon,
  Timeline as TimelineIcon,
  Speed as SpeedIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Refresh as RefreshIcon,
  Save as SaveIcon,
  Email as EmailIcon,
  PictureAsPdf as PictureAsPdfIcon,
  TableChart as TableChartIcon,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  ScatterChart,
  Scatter,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
} from 'recharts';
import { useAuth } from '../../contexts/AuthContext';
import { analyticsAPI } from '../../services/api';

// Types
interface AnalyticsData {
  query: {
    report_type: string;
    start_date: string;
    end_date: string;
    granularity: string;
    filters: Record<string, any>;
    group_by: string[];
    metrics: string[];
  };
  data: any[];
  summary: Record<string, any>;
  insights: string[];
  visualizations: Record<string, string>;
  export_formats: string[];
  generated_at: string;
}

interface ReportType {
  id: string;
  name: string;
  description: string;
  metrics: string[];
}

interface CustomReport {
  id: string;
  name: string;
  description: string;
  report_type: string;
  schedule?: string;
  recipients: string[];
  filters: Record<string, any>;
  visualizations: any[];
  created_at: string;
  last_run?: string;
}

// Constants
const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6'];
const REFRESH_INTERVAL = 30000; // 30 seconds for real-time updates

const AdvancedAnalytics: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [reportTypes, setReportTypes] = useState<Record<string, ReportType>>({});
  const [selectedReportType, setSelectedReportType] = useState('user_activity');
  const [startDate, setStartDate] = useState(new Date(Date.now() - 7 * 24 * 60 * 60 * 1000));
  const [endDate, setEndDate] = useState(new Date());
  const [granularity, setGranularity] = useState('daily');
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>([]);
  const [filters, setFilters] = useState<Record<string, any>>({});
  const [groupBy, setGroupBy] = useState<string[]>([]);
  const [includePredictions, setIncludePredictions] = useState(false);
  const [includeBenchmarks, setIncludeBenchmarks] = useState(false);
  const [selectedTab, setSelectedTab] = useState(0);
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [showCustomReportDialog, setShowCustomReportDialog] = useState(false);
  const [customReports, setCustomReports] = useState<CustomReport[]>([]);
  const [realtimeMetrics, setRealtimeMetrics] = useState<Record<string, any>>({});
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as any });
  const refreshInterval = useRef<NodeJS.Timeout>();

  // Fetch available report types
  useEffect(() => {
    fetchReportTypes();
    fetchCustomReports();
    return () => {
      if (refreshInterval.current) {
        clearInterval(refreshInterval.current);
      }
    };
  }, []);

  // Setup real-time updates
  useEffect(() => {
    if (selectedTab === 3) { // Real-time tab
      fetchRealtimeMetrics();
      refreshInterval.current = setInterval(fetchRealtimeMetrics, REFRESH_INTERVAL);
    } else {
      if (refreshInterval.current) {
        clearInterval(refreshInterval.current);
      }
    }
    return () => {
      if (refreshInterval.current) {
        clearInterval(refreshInterval.current);
      }
    };
  }, [selectedTab]);

  const fetchReportTypes = async () => {
    try {
      const response = await analyticsAPI.getReportTypes();
      setReportTypes(response.report_types);
      
      // Set default metrics for selected report type
      if (response.report_types[selectedReportType]) {
        setSelectedMetrics(response.report_types[selectedReportType].metrics);
      }
    } catch (error) {
      console.error('Failed to fetch report types:', error);
      showSnackbar('Failed to load report types', 'error');
    }
  };

  const fetchCustomReports = async () => {
    try {
      const reports = await analyticsAPI.getCustomReports();
      setCustomReports(reports);
    } catch (error) {
      console.error('Failed to fetch custom reports:', error);
    }
  };

  const generateAnalytics = async () => {
    setLoading(true);
    try {
      const response = await analyticsAPI.generateAnalytics({
        report_type: selectedReportType,
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
        granularity,
        filters,
        group_by: groupBy,
        metrics: selectedMetrics,
        include_predictions: includePredictions,
        include_benchmarks: includeBenchmarks,
      });
      
      setAnalyticsData(response);
      showSnackbar('Analytics generated successfully', 'success');
    } catch (error: any) {
      console.error('Failed to generate analytics:', error);
      showSnackbar(error.response?.data?.detail || 'Failed to generate analytics', 'error');
    } finally {
      setLoading(false);
    }
  };

  const exportAnalytics = async (format: string) => {
    if (!analyticsData) return;
    
    try {
      const response = await analyticsAPI.exportAnalytics('current', {
        format,
        include_visualizations: true,
      });
      
      // Handle download based on format
      if (format === 'csv' || format === 'json') {
        const blob = new Blob([response.data], { 
          type: format === 'csv' ? 'text/csv' : 'application/json' 
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `analytics_export_${Date.now()}.${format}`;
        a.click();
        URL.revokeObjectURL(url);
      } else {
        // For Excel and PDF, show download link
        showSnackbar(`${format.toUpperCase()} export generated`, 'success');
      }
      
      setShowExportDialog(false);
    } catch (error) {
      console.error('Failed to export analytics:', error);
      showSnackbar('Failed to export analytics', 'error');
    }
  };

  const fetchRealtimeMetrics = async () => {
    const metrics = ['active_users', 'api_calls_per_minute', 'error_rate', 'avg_response_time'];
    
    try {
      const promises = metrics.map(metric => analyticsAPI.getRealtimeMetric(metric));
      const results = await Promise.all(promises);
      
      const metricsData = results.reduce((acc, result) => {
        acc[result.metric] = result;
        return acc;
      }, {} as Record<string, any>);
      
      setRealtimeMetrics(metricsData);
    } catch (error) {
      console.error('Failed to fetch real-time metrics:', error);
    }
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'warning' | 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  // Render chart based on type and data
  const renderChart = (chartType: string, data: any[], config: any) => {
    const chartHeight = 300;
    
    switch (chartType) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={chartHeight}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={config.xAxis} />
              <YAxis />
              <RechartsTooltip />
              <Legend />
              {config.lines.map((line: any, index: number) => (
                <Line
                  key={line.dataKey}
                  type="monotone"
                  dataKey={line.dataKey}
                  stroke={COLORS[index % COLORS.length]}
                  name={line.name || line.dataKey}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );
      
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={chartHeight}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={config.xAxis} />
              <YAxis />
              <RechartsTooltip />
              <Legend />
              {config.bars.map((bar: any, index: number) => (
                <Bar
                  key={bar.dataKey}
                  dataKey={bar.dataKey}
                  fill={COLORS[index % COLORS.length]}
                  name={bar.name || bar.dataKey}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );
      
      case 'pie':
        return (
          <ResponsiveContainer width="100%" height={chartHeight}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey={config.valueKey}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <RechartsTooltip />
            </PieChart>
          </ResponsiveContainer>
        );
      
      case 'area':
        return (
          <ResponsiveContainer width="100%" height={chartHeight}>
            <AreaChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={config.xAxis} />
              <YAxis />
              <RechartsTooltip />
              <Legend />
              {config.areas.map((area: any, index: number) => (
                <Area
                  key={area.dataKey}
                  type="monotone"
                  dataKey={area.dataKey}
                  stackId={area.stackId || '1'}
                  stroke={COLORS[index % COLORS.length]}
                  fill={COLORS[index % COLORS.length]}
                  name={area.name || area.dataKey}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        );
      
      default:
        return null;
    }
  };

  // Render analytics dashboard
  const renderAnalyticsDashboard = () => {
    if (!analyticsData) {
      return (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <AssessmentIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            No analytics data available
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Configure your report parameters and click "Generate Analytics"
          </Typography>
        </Box>
      );
    }

    return (
      <Grid container spacing={3}>
        {/* Summary Cards */}
        <Grid item xs={12}>
          <Grid container spacing={2}>
            {Object.entries(analyticsData.summary).slice(0, 4).map(([key, value]) => (
              <Grid item xs={12} sm={6} md={3} key={key}>
                <Card>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom>
                      {key.replace(/_/g, ' ').toUpperCase()}
                    </Typography>
                    <Typography variant="h4">
                      {typeof value === 'number' ? value.toLocaleString() : value}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Grid>

        {/* Charts */}
        {analyticsData.data.length > 0 && (
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Data Visualization
              </Typography>
              {renderChart('line', analyticsData.data, {
                xAxis: 'time',
                lines: selectedMetrics.map(metric => ({ dataKey: metric }))
              })}
            </Paper>
          </Grid>
        )}

        {/* Insights */}
        {analyticsData.insights.length > 0 && (
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" gutterBottom>
                <InsightsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Key Insights
              </Typography>
              <Stack spacing={2}>
                {analyticsData.insights.map((insight, index) => (
                  <Alert key={index} severity="info" icon={<InsightsIcon />}>
                    {insight}
                  </Alert>
                ))}
              </Stack>
            </Paper>
          </Grid>
        )}

        {/* Data Table Preview */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              <TableChartIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Data Preview
            </Typography>
            <Box sx={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    {analyticsData.data.length > 0 &&
                      Object.keys(analyticsData.data[0]).slice(0, 5).map(key => (
                        <th key={key} style={{ padding: 8, borderBottom: '1px solid #ddd' }}>
                          {key}
                        </th>
                      ))}
                  </tr>
                </thead>
                <tbody>
                  {analyticsData.data.slice(0, 5).map((row, index) => (
                    <tr key={index}>
                      {Object.values(row).slice(0, 5).map((value: any, i) => (
                        <td key={i} style={{ padding: 8, borderBottom: '1px solid #ddd' }}>
                          {typeof value === 'number' ? value.toFixed(2) : value}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              {analyticsData.data.length > 5 && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                  Showing 5 of {analyticsData.data.length} rows
                </Typography>
              )}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    );
  };

  // Render real-time metrics
  const renderRealtimeMetrics = () => {
    return (
      <Grid container spacing={3}>
        {Object.entries(realtimeMetrics).map(([metric, data]) => (
          <Grid item xs={12} sm={6} md={3} key={metric}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  {metric.replace(/_/g, ' ').toUpperCase()}
                </Typography>
                <Typography variant="h3">
                  {typeof data.value === 'number' ? data.value.toFixed(1) : data.value}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {data.unit}
                </Typography>
                <Box sx={{ mt: 2 }}>
                  <LinearProgress
                    variant="determinate"
                    value={Math.min((data.value / 500) * 100, 100)}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
        
        <Grid item xs={12}>
          <Alert severity="info">
            Real-time metrics update every {REFRESH_INTERVAL / 1000} seconds
          </Alert>
        </Grid>
      </Grid>
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4">
          <AssessmentIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Advanced Analytics
        </Typography>
        
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={generateAnalytics}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<DownloadIcon />}
            onClick={() => setShowExportDialog(true)}
            disabled={!analyticsData}
          >
            Export
          </Button>
        </Stack>
      </Box>

      <Tabs value={selectedTab} onChange={(_, tab) => setSelectedTab(tab)} sx={{ mb: 3 }}>
        <Tab label="Analytics" icon={<BarChartIcon />} />
        <Tab label="Configuration" icon={<FilterListIcon />} />
        <Tab label="Custom Reports" icon={<SaveIcon />} />
        <Tab label="Real-time" icon={<SpeedIcon />} />
      </Tabs>

      {/* Configuration Tab */}
      {selectedTab === 1 && (
        <Paper sx={{ p: 3 }}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Report Type</InputLabel>
                <Select
                  value={selectedReportType}
                  onChange={(e) => {
                    setSelectedReportType(e.target.value);
                    setSelectedMetrics(reportTypes[e.target.value]?.metrics || []);
                  }}
                  label="Report Type"
                >
                  {Object.entries(reportTypes).map(([id, report]) => (
                    <MenuItem key={id} value={id}>
                      {report.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <DateTimePicker
                  label="Start Date"
                  value={startDate}
                  onChange={(date) => date && setStartDate(date)}
                  renderInput={(params) => <TextField {...params} fullWidth />}
                />
              </LocalizationProvider>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <DateTimePicker
                  label="End Date"
                  value={endDate}
                  onChange={(date) => date && setEndDate(date)}
                  renderInput={(params) => <TextField {...params} fullWidth />}
                />
              </LocalizationProvider>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Granularity</InputLabel>
                <Select
                  value={granularity}
                  onChange={(e) => setGranularity(e.target.value)}
                  label="Granularity"
                >
                  <MenuItem value="hourly">Hourly</MenuItem>
                  <MenuItem value="daily">Daily</MenuItem>
                  <MenuItem value="weekly">Weekly</MenuItem>
                  <MenuItem value="monthly">Monthly</MenuItem>
                  <MenuItem value="quarterly">Quarterly</MenuItem>
                  <MenuItem value="yearly">Yearly</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={8}>
              <Autocomplete
                multiple
                options={reportTypes[selectedReportType]?.metrics || []}
                value={selectedMetrics}
                onChange={(_, values) => setSelectedMetrics(values)}
                renderInput={(params) => (
                  <TextField {...params} label="Metrics" placeholder="Select metrics" />
                )}
                renderTags={(value, getTagProps) =>
                  value.map((option, index) => (
                    <Chip
                      variant="outlined"
                      label={option}
                      {...getTagProps({ index })}
                    />
                  ))
                }
              />
            </Grid>
            
            <Grid item xs={12}>
              <Stack direction="row" spacing={2}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={includePredictions}
                      onChange={(e) => setIncludePredictions(e.target.checked)}
                      disabled={!['pro', 'enterprise'].includes(user?.subscription_tier || '')}
                    />
                  }
                  label="Include Predictions"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={includeBenchmarks}
                      onChange={(e) => setIncludeBenchmarks(e.target.checked)}
                      disabled={user?.subscription_tier !== 'enterprise'}
                    />
                  }
                  label="Include Benchmarks"
                />
              </Stack>
            </Grid>
            
            <Grid item xs={12}>
              <Button
                variant="contained"
                size="large"
                startIcon={<AssessmentIcon />}
                onClick={generateAnalytics}
                disabled={loading}
                fullWidth
              >
                {loading ? 'Generating...' : 'Generate Analytics'}
              </Button>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Analytics Tab */}
      {selectedTab === 0 && renderAnalyticsDashboard()}

      {/* Custom Reports Tab */}
      {selectedTab === 2 && (
        <Box>
          <Box sx={{ mb: 3, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={() => setShowCustomReportDialog(true)}
            >
              Create Custom Report
            </Button>
          </Box>
          
          <Grid container spacing={3}>
            {customReports.length === 0 ? (
              <Grid item xs={12}>
                <Paper sx={{ p: 4, textAlign: 'center' }}>
                  <Typography variant="h6" color="text.secondary">
                    No custom reports yet
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Create your first custom report to save your analytics configuration
                  </Typography>
                </Paper>
              </Grid>
            ) : (
              customReports.map((report) => (
                <Grid item xs={12} md={6} lg={4} key={report.id}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6">{report.name}</Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {report.description}
                      </Typography>
                      <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
                        <Chip label={report.report_type} size="small" />
                        {report.schedule && (
                          <Chip
                            label="Scheduled"
                            size="small"
                            icon={<ScheduleIcon />}
                            color="primary"
                          />
                        )}
                      </Stack>
                      <Button size="small" variant="outlined">
                        Run Report
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>
              ))
            )}
          </Grid>
        </Box>
      )}

      {/* Real-time Tab */}
      {selectedTab === 3 && renderRealtimeMetrics()}

      {/* Export Dialog */}
      <Dialog open={showExportDialog} onClose={() => setShowExportDialog(false)}>
        <DialogTitle>Export Analytics</DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            Select export format:
          </Typography>
          <Stack spacing={2} sx={{ mt: 2 }}>
            <Button
              variant="outlined"
              startIcon={<TableChartIcon />}
              onClick={() => exportAnalytics('csv')}
              fullWidth
            >
              CSV
            </Button>
            <Button
              variant="outlined"
              startIcon={<TableChartIcon />}
              onClick={() => exportAnalytics('excel')}
              fullWidth
            >
              Excel
            </Button>
            <Button
              variant="outlined"
              startIcon={<TableChartIcon />}
              onClick={() => exportAnalytics('json')}
              fullWidth
            >
              JSON
            </Button>
            <Button
              variant="outlined"
              startIcon={<PictureAsPdfIcon />}
              onClick={() => exportAnalytics('pdf')}
              disabled={user?.subscription_tier !== 'enterprise'}
              fullWidth
            >
              PDF {user?.subscription_tier !== 'enterprise' && '(Enterprise only)'}
            </Button>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowExportDialog(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>

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

export default AdvancedAnalytics;