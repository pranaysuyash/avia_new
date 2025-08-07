/**
 * Advanced Analytics Desktop Component
 * Desktop-optimized analytics with native features and enhanced visualizations
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
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Collapse,
  Menu,
  Slider,
  Checkbox,
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
  FullscreenIcon,
  FullscreenExitIcon,
  DashboardCustomizeIcon,
  NotificationsIcon,
  FolderOpenIcon,
  PrintIcon,
  CompareIcon,
  TuneIcon,
  ViewModuleIcon,
  ViewListIcon,
  DataUsageIcon,
  BubbleChartIcon,
  DonutLargeIcon,
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
  Treemap,
  Sankey,
  Funnel,
  FunnelChart,
  RadialBarChart,
  RadialBar,
} from 'recharts';
import { useAuth } from '../../contexts/AuthContext';
import { analyticsAPI } from '../../services/api';

const { ipcRenderer } = window.require('electron');

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

interface DashboardLayout {
  id: string;
  name: string;
  widgets: Widget[];
}

interface Widget {
  id: string;
  type: 'chart' | 'metric' | 'insight' | 'table';
  position: { x: number; y: number; w: number; h: number };
  config: any;
}

// Constants
const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6'];
const CHART_THEMES = {
  default: { background: '#ffffff', text: '#000000' },
  dark: { background: '#1a1a1a', text: '#ffffff' },
  midnight: { background: '#0f172a', text: '#e2e8f0' },
};

const AdvancedAnalyticsDesktop: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [reportTypes, setReportTypes] = useState<Record<string, any>>({});
  const [selectedReportType, setSelectedReportType] = useState('user_activity');
  const [startDate, setStartDate] = useState(new Date(Date.now() - 7 * 24 * 60 * 60 * 1000));
  const [endDate, setEndDate] = useState(new Date());
  const [granularity, setGranularity] = useState('daily');
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>([]);
  const [filters, setFilters] = useState<Record<string, any>>({});
  const [groupBy, setGroupBy] = useState<string[]>([]);
  const [selectedTab, setSelectedTab] = useState(0);
  const [fullscreen, setFullscreen] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [chartTheme, setChartTheme] = useState('default');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [comparisonMode, setComparisonMode] = useState(false);
  const [comparisonData, setComparisonData] = useState<AnalyticsData | null>(null);
  const [dashboardLayouts, setDashboardLayouts] = useState<DashboardLayout[]>([]);
  const [activeDashboard, setActiveDashboard] = useState<string>('default');
  const [showExportMenu, setShowExportMenu] = useState<null | HTMLElement>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(60); // seconds
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as any });
  const autoRefreshTimer = useRef<NodeJS.Timeout>();

  // Desktop-specific initialization
  useEffect(() => {
    // Load saved preferences
    ipcRenderer.invoke('get-analytics-preferences').then(prefs => {
      if (prefs) {
        setChartTheme(prefs.chartTheme || 'default');
        setShowSidebar(prefs.showSidebar !== false);
        setViewMode(prefs.viewMode || 'grid');
      }
    });

    // Load saved dashboard layouts
    ipcRenderer.invoke('get-dashboard-layouts').then(layouts => {
      setDashboardLayouts(layouts || []);
    });

    // Setup IPC listeners
    ipcRenderer.on('analytics-export-complete', (_, filePath) => {
      showSnackbar(`Export saved to ${filePath}`, 'success');
    });

    ipcRenderer.on('analytics-print-complete', () => {
      showSnackbar('Report printed successfully', 'success');
    });

    return () => {
      ipcRenderer.removeAllListeners('analytics-export-complete');
      ipcRenderer.removeAllListeners('analytics-print-complete');
      if (autoRefreshTimer.current) {
        clearInterval(autoRefreshTimer.current);
      }
    };
  }, []);

  // Auto-refresh logic
  useEffect(() => {
    if (autoRefresh && analyticsData) {
      autoRefreshTimer.current = setInterval(() => {
        generateAnalytics();
      }, refreshInterval * 1000);
    } else {
      if (autoRefreshTimer.current) {
        clearInterval(autoRefreshTimer.current);
      }
    }
    return () => {
      if (autoRefreshTimer.current) {
        clearInterval(autoRefreshTimer.current);
      }
    };
  }, [autoRefresh, refreshInterval, analyticsData]);

  // Fullscreen handling
  useEffect(() => {
    const handleFullscreenChange = () => {
      setFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);

  const toggleFullscreen = () => {
    if (!fullscreen) {
      document.documentElement.requestFullscreen();
    } else {
      document.exitFullscreen();
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
        include_predictions: true,
        include_benchmarks: user?.subscription_tier === 'enterprise',
      });
      
      setAnalyticsData(response);
      
      // Desktop notification
      ipcRenderer.invoke('show-notification', {
        title: 'Analytics Generated',
        body: `${response.insights.length} insights discovered`,
      });
      
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
      // Use native file dialog
      const savePath = await ipcRenderer.invoke('show-save-dialog', {
        defaultPath: `analytics_${Date.now()}.${format}`,
        filters: [
          { name: format.toUpperCase(), extensions: [format] },
          { name: 'All Files', extensions: ['*'] }
        ]
      });
      
      if (savePath) {
        const response = await analyticsAPI.exportAnalytics('current', {
          format,
          include_visualizations: true,
        });
        
        // Save file using native file system
        await ipcRenderer.invoke('save-analytics-export', {
          path: savePath,
          data: response.data,
          format
        });
      }
    } catch (error) {
      console.error('Failed to export analytics:', error);
      showSnackbar('Failed to export analytics', 'error');
    }
  };

  const printReport = async () => {
    if (!analyticsData) return;
    
    try {
      // Generate print-friendly HTML
      const printHtml = generatePrintHtml(analyticsData);
      await ipcRenderer.invoke('print-analytics-report', printHtml);
    } catch (error) {
      console.error('Failed to print report:', error);
      showSnackbar('Failed to print report', 'error');
    }
  };

  const generatePrintHtml = (data: AnalyticsData): string => {
    return `
      <html>
        <head>
          <title>Analytics Report - ${new Date().toLocaleDateString()}</title>
          <style>
            body { font-family: Arial, sans-serif; }
            h1, h2 { color: #333; }
            .summary { background: #f5f5f5; padding: 10px; margin: 10px 0; }
            .insights { margin: 20px 0; }
            .insight { padding: 5px 0; }
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background: #f5f5f5; }
          </style>
        </head>
        <body>
          <h1>Analytics Report</h1>
          <p>Generated: ${new Date().toLocaleString()}</p>
          <div class="summary">
            <h2>Summary</h2>
            ${Object.entries(data.summary).map(([key, value]) => 
              `<p><strong>${key}:</strong> ${value}</p>`
            ).join('')}
          </div>
          <div class="insights">
            <h2>Key Insights</h2>
            ${data.insights.map(insight => 
              `<div class="insight">• ${insight}</div>`
            ).join('')}
          </div>
        </body>
      </html>
    `;
  };

  const savePreferences = async () => {
    await ipcRenderer.invoke('save-analytics-preferences', {
      chartTheme,
      showSidebar,
      viewMode,
      autoRefresh,
      refreshInterval,
    });
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'warning' | 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  // Enhanced chart rendering with themes
  const renderEnhancedChart = (chartType: string, data: any[], config: any) => {
    const theme = CHART_THEMES[chartTheme as keyof typeof CHART_THEMES];
    const chartHeight = fullscreen ? 500 : 350;
    
    // Common chart props
    const commonProps = {
      margin: { top: 20, right: 30, left: 20, bottom: 20 },
    };

    switch (chartType) {
      case 'composed':
        return (
          <ResponsiveContainer width="100%" height={chartHeight}>
            <ComposedChart data={data} {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" stroke={theme.text} opacity={0.2} />
              <XAxis dataKey={config.xAxis} stroke={theme.text} />
              <YAxis stroke={theme.text} />
              <RechartsTooltip
                contentStyle={{ backgroundColor: theme.background, border: `1px solid ${theme.text}` }}
                labelStyle={{ color: theme.text }}
              />
              <Legend wrapperStyle={{ color: theme.text }} />
              {config.bars?.map((bar: any, index: number) => (
                <Bar
                  key={bar.dataKey}
                  dataKey={bar.dataKey}
                  fill={COLORS[index % COLORS.length]}
                  name={bar.name || bar.dataKey}
                />
              ))}
              {config.lines?.map((line: any, index: number) => (
                <Line
                  key={line.dataKey}
                  type="monotone"
                  dataKey={line.dataKey}
                  stroke={COLORS[(index + 2) % COLORS.length]}
                  name={line.name || line.dataKey}
                />
              ))}
            </ComposedChart>
          </ResponsiveContainer>
        );

      case 'radialBar':
        return (
          <ResponsiveContainer width="100%" height={chartHeight}>
            <RadialBarChart cx="50%" cy="50%" innerRadius="10%" outerRadius="90%" data={data}>
              <RadialBar
                minAngle={15}
                label={{ position: 'insideStart', fill: theme.text }}
                background
                clockWise
                dataKey={config.valueKey}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </RadialBar>
              <Legend
                iconSize={10}
                layout="vertical"
                verticalAlign="middle"
                align="right"
                wrapperStyle={{ color: theme.text }}
              />
            </RadialBarChart>
          </ResponsiveContainer>
        );

      case 'treemap':
        return (
          <ResponsiveContainer width="100%" height={chartHeight}>
            <Treemap
              data={data}
              dataKey={config.valueKey}
              aspectRatio={4 / 3}
              stroke={theme.text}
              fill={COLORS[0]}
            >
              <RechartsTooltip
                contentStyle={{ backgroundColor: theme.background, border: `1px solid ${theme.text}` }}
                labelStyle={{ color: theme.text }}
              />
            </Treemap>
          </ResponsiveContainer>
        );

      default:
        // Fallback to standard charts
        return null;
    }
  };

  // Render analytics dashboard with desktop enhancements
  const renderDesktopDashboard = () => {
    if (!analyticsData) {
      return (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <DataUsageIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            No analytics data available
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Configure your report parameters and generate analytics
          </Typography>
        </Box>
      );
    }

    return (
      <Box sx={{ display: 'flex', height: '100%' }}>
        {/* Sidebar */}
        <Drawer
          variant="persistent"
          anchor="left"
          open={showSidebar}
          sx={{
            width: showSidebar ? 300 : 0,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: 300,
              boxSizing: 'border-box',
              position: 'relative',
              height: '100%',
            },
          }}
        >
          <Box sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Stack spacing={1}>
              <Button
                variant="outlined"
                startIcon={<CompareIcon />}
                onClick={() => setComparisonMode(!comparisonMode)}
                fullWidth
              >
                {comparisonMode ? 'Exit Comparison' : 'Compare Periods'}
              </Button>
              <Button
                variant="outlined"
                startIcon={<DashboardCustomizeIcon />}
                onClick={() => {/* Open dashboard customization */}}
                fullWidth
              >
                Customize Dashboard
              </Button>
              <Button
                variant="outlined"
                startIcon={<PrintIcon />}
                onClick={printReport}
                fullWidth
              >
                Print Report
              </Button>
            </Stack>

            <Divider sx={{ my: 3 }} />

            <Typography variant="h6" gutterBottom>
              View Options
            </Typography>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Chart Theme</InputLabel>
              <Select
                value={chartTheme}
                onChange={(e) => {
                  setChartTheme(e.target.value);
                  savePreferences();
                }}
                label="Chart Theme"
              >
                <MenuItem value="default">Default</MenuItem>
                <MenuItem value="dark">Dark</MenuItem>
                <MenuItem value="midnight">Midnight</MenuItem>
              </Select>
            </FormControl>

            <ToggleButtonGroup
              value={viewMode}
              exclusive
              onChange={(_, mode) => mode && setViewMode(mode)}
              fullWidth
              size="small"
            >
              <ToggleButton value="grid">
                <ViewModuleIcon />
              </ToggleButton>
              <ToggleButton value="list">
                <ViewListIcon />
              </ToggleButton>
            </ToggleButtonGroup>

            <Divider sx={{ my: 3 }} />

            <Typography variant="h6" gutterBottom>
              Auto Refresh
            </Typography>
            <FormControlLabel
              control={
                <Switch
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                />
              }
              label="Enable Auto Refresh"
            />
            {autoRefresh && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" gutterBottom>
                  Refresh Interval: {refreshInterval}s
                </Typography>
                <Slider
                  value={refreshInterval}
                  onChange={(_, value) => setRefreshInterval(value as number)}
                  min={30}
                  max={300}
                  step={30}
                  marks
                  valueLabelDisplay="auto"
                />
              </Box>
            )}
          </Box>
        </Drawer>

        {/* Main Content */}
        <Box sx={{ flexGrow: 1, overflow: 'auto', p: 3 }}>
          {/* Toolbar */}
          <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Stack direction="row" spacing={2} alignItems="center">
              <IconButton onClick={() => setShowSidebar(!showSidebar)}>
                <TuneIcon />
              </IconButton>
              <Typography variant="h5">
                {reportTypes[selectedReportType]?.name || 'Analytics'} Report
              </Typography>
            </Stack>
            
            <Stack direction="row" spacing={2}>
              <IconButton onClick={toggleFullscreen}>
                {fullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
              </IconButton>
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
                onClick={(e) => setShowExportMenu(e.currentTarget)}
              >
                Export
              </Button>
            </Stack>
          </Box>

          {/* Dashboard Grid */}
          {viewMode === 'grid' ? (
            <Grid container spacing={3}>
              {/* Summary Cards with animations */}
              <Grid item xs={12}>
                <Grid container spacing={2}>
                  {Object.entries(analyticsData.summary).slice(0, 4).map(([key, value], index) => (
                    <Grid item xs={12} sm={6} md={3} key={key}>
                      <Card
                        sx={{
                          transition: 'transform 0.2s',
                          '&:hover': { transform: 'translateY(-4px)' },
                        }}
                      >
                        <CardContent>
                          <Typography color="text.secondary" gutterBottom>
                            {key.replace(/_/g, ' ').toUpperCase()}
                          </Typography>
                          <Typography variant="h4">
                            {typeof value === 'number' ? value.toLocaleString() : value}
                          </Typography>
                          {index === 0 && (
                            <LinearProgress
                              variant="determinate"
                              value={75}
                              sx={{ mt: 2, height: 6, borderRadius: 3 }}
                            />
                          )}
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </Grid>

              {/* Main Chart */}
              <Grid item xs={12} lg={comparisonMode ? 6 : 12}>
                <Paper sx={{ p: 3, height: fullscreen ? 600 : 400 }}>
                  <Typography variant="h6" gutterBottom>
                    Data Visualization
                  </Typography>
                  {renderEnhancedChart('composed', analyticsData.data, {
                    xAxis: 'time',
                    lines: selectedMetrics.map(metric => ({ dataKey: metric })),
                    bars: groupBy.length > 0 ? [{ dataKey: 'count' }] : []
                  })}
                </Paper>
              </Grid>

              {/* Comparison Chart */}
              {comparisonMode && comparisonData && (
                <Grid item xs={12} lg={6}>
                  <Paper sx={{ p: 3, height: fullscreen ? 600 : 400 }}>
                    <Typography variant="h6" gutterBottom>
                      Comparison Period
                    </Typography>
                    {renderEnhancedChart('composed', comparisonData.data, {
                      xAxis: 'time',
                      lines: selectedMetrics.map(metric => ({ dataKey: metric })),
                      bars: groupBy.length > 0 ? [{ dataKey: 'count' }] : []
                    })}
                  </Paper>
                </Grid>
              )}

              {/* Additional Visualizations */}
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Distribution Analysis
                  </Typography>
                  {renderEnhancedChart('radialBar', 
                    selectedMetrics.map(metric => ({
                      name: metric,
                      value: analyticsData.summary[`${metric}_total`] || 0
                    })),
                    { valueKey: 'value' }
                  )}
                </Paper>
              </Grid>

              {/* Insights with AI suggestions */}
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 3, height: '100%' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">
                      <InsightsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                      AI-Powered Insights
                    </Typography>
                    <Chip
                      label={`${analyticsData.insights.length} insights`}
                      color="primary"
                      size="small"
                    />
                  </Box>
                  <Stack spacing={2}>
                    {analyticsData.insights.map((insight, index) => (
                      <Alert
                        key={index}
                        severity="info"
                        icon={<InsightsIcon />}
                        action={
                          <IconButton
                            size="small"
                            onClick={() => {
                              // Copy insight to clipboard
                              navigator.clipboard.writeText(insight);
                              showSnackbar('Insight copied to clipboard', 'success');
                            }}
                          >
                            <ShareIcon fontSize="small" />
                          </IconButton>
                        }
                      >
                        {insight}
                      </Alert>
                    ))}
                  </Stack>
                </Paper>
              </Grid>
            </Grid>
          ) : (
            // List View
            <Stack spacing={3}>
              {analyticsData.data.map((row, index) => (
                <Paper key={index} sx={{ p: 2 }}>
                  <Grid container spacing={2}>
                    {Object.entries(row).map(([key, value]) => (
                      <Grid item xs={12} sm={6} md={3} key={key}>
                        <Typography variant="caption" color="text.secondary">
                          {key}
                        </Typography>
                        <Typography variant="body1">
                          {typeof value === 'number' ? value.toFixed(2) : value}
                        </Typography>
                      </Grid>
                    ))}
                  </Grid>
                </Paper>
              ))}
            </Stack>
          )}
        </Box>
      </Box>
    );
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Tabs value={selectedTab} onChange={(_, tab) => setSelectedTab(tab)} sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tab label="Dashboard" icon={<DashboardCustomizeIcon />} />
        <Tab label="Configuration" icon={<FilterListIcon />} />
        <Tab label="Comparison" icon={<CompareIcon />} />
        <Tab label="Real-time" icon={<SpeedIcon />} />
      </Tabs>

      <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
        {selectedTab === 0 && renderDesktopDashboard()}
        
        {/* Other tabs content... */}
      </Box>

      {/* Export Menu */}
      <Menu
        anchorEl={showExportMenu}
        open={Boolean(showExportMenu)}
        onClose={() => setShowExportMenu(null)}
      >
        <MenuItem onClick={() => { exportAnalytics('csv'); setShowExportMenu(null); }}>
          <ListItemIcon><TableChartIcon fontSize="small" /></ListItemIcon>
          <ListItemText>Export as CSV</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => { exportAnalytics('excel'); setShowExportMenu(null); }}>
          <ListItemIcon><TableChartIcon fontSize="small" /></ListItemIcon>
          <ListItemText>Export as Excel</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => { exportAnalytics('json'); setShowExportMenu(null); }}>
          <ListItemIcon><TableChartIcon fontSize="small" /></ListItemIcon>
          <ListItemText>Export as JSON</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => { exportAnalytics('pdf'); setShowExportMenu(null); }}>
          <ListItemIcon><PictureAsPdfIcon fontSize="small" /></ListItemIcon>
          <ListItemText>Export as PDF</ListItemText>
        </MenuItem>
        <Divider />
        <MenuItem onClick={() => { printReport(); setShowExportMenu(null); }}>
          <ListItemIcon><PrintIcon fontSize="small" /></ListItemIcon>
          <ListItemText>Print Report</ListItemText>
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

export default AdvancedAnalyticsDesktop;