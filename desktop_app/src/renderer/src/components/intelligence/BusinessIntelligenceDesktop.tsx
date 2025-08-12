/**
 * Business Intelligence Component - Electron Desktop
 * ROI calculations, revenue forecasting, and business metrics
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Paper,
  Chip,
  CircularProgress,
  Alert,
  LinearProgress,
  IconButton,
  Tooltip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tab,
  Tabs,
  Badge,
  Avatar,
  Divider,
  ToggleButton,
  ToggleButtonGroup,
  Slider,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  SpeedDial,
  SpeedDialAction,
  SpeedDialIcon,
  Fab,
  Snackbar,
  Menu,
  Drawer,
  Autocomplete,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  AttachMoney as MoneyIcon,
  Assessment as AssessmentIcon,
  PieChart as PieChartIcon,
  ShowChart as ChartIcon,
  Timeline as TimelineIcon,
  Groups as GroupsIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Download as DownloadIcon,
  Share as ShareIcon,
  Save as SaveIcon,
  Settings as SettingsIcon,
  Calculate as CalculateIcon,
  Analytics as AnalyticsIcon,
  Speed as SpeedIcon,
  DateRange as DateRangeIcon,
  Print as PrintIcon,
  Email as EmailIcon,
  Refresh as RefreshIcon,
  ArrowUpward as ArrowUpIcon,
  ArrowDownward as ArrowDownIcon,
  Dashboard as DashboardIcon,
  AccountBalance as AccountIcon,
  ShoppingCart as CartIcon,
  Insights as InsightsIcon,
  AutoGraph as AutoGraphIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Treemap,
  Sankey,
  FunnelChart,
  Funnel,
  LabelList,
} from 'recharts';
import { ipcRenderer } from 'electron';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

// Desktop-specific styled components
const ExecutiveCard = styled(Card)(({ theme }) => ({
  background: 'linear-gradient(135deg, #3a7bd5 0%, #00d2ff 100%)',
  color: 'white',
  marginBottom: theme.spacing(2),
  boxShadow: '0 8px 32px rgba(58, 123, 213, 0.25)',
}));

const KPICard = styled(Paper)(({ theme, trend }: any) => ({
  padding: theme.spacing(3),
  position: 'relative',
  overflow: 'hidden',
  transition: 'all 0.3s',
  cursor: 'pointer',
  '&:hover': {
    transform: 'translateY(-5px)',
    boxShadow: theme.shadows[12],
  },
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    right: 0,
    width: '100px',
    height: '100px',
    background: trend === 'up' 
      ? 'radial-gradient(circle, rgba(76, 175, 80, 0.1) 0%, transparent 70%)'
      : trend === 'down'
      ? 'radial-gradient(circle, rgba(244, 67, 54, 0.1) 0%, transparent 70%)'
      : 'radial-gradient(circle, rgba(158, 158, 158, 0.1) 0%, transparent 70%)',
    borderRadius: '50%',
    transform: 'translate(30%, -30%)',
  },
}));

const MetricDisplay = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'baseline',
  gap: theme.spacing(1),
}));

const ChurnRiskCard = styled(Card)(({ theme, risk }: any) => ({
  marginBottom: theme.spacing(2),
  borderLeft: `4px solid ${
    risk === 'high' ? theme.palette.error.main :
    risk === 'medium' ? theme.palette.warning.main :
    theme.palette.success.main
  }`,
  transition: 'all 0.3s',
  '&:hover': {
    boxShadow: theme.shadows[6],
  },
}));

const OpportunityCard = styled(Paper)(({ theme, type }: any) => ({
  padding: theme.spacing(2),
  background: 
    type === 'upsell' ? 'linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%)' :
    type === 'winback' ? 'linear-gradient(135deg, #fce4ec 0%, #f8bbd0 100%)' :
    type === 'expansion' ? 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)' :
    theme.palette.background.paper,
  cursor: 'pointer',
  transition: 'all 0.3s',
  '&:hover': {
    transform: 'scale(1.02)',
    boxShadow: theme.shadows[4],
  },
}));

const StyledSpeedDial = styled(SpeedDial)(({ theme }) => ({
  position: 'fixed',
  bottom: theme.spacing(2),
  right: theme.spacing(2),
}));

interface BusinessMetrics {
  mrr: number;
  mrrGrowth: number;
  arr: number;
  activeUsers: number;
  userGrowth: number;
  churnRate: number;
  ltvCacRatio: number;
  revenue: number;
  costs: number;
  profit: number;
  roi: number;
  grossMargin: number;
  netMargin: number;
  cashFlow: number;
  runwayMonths: number;
}

interface ChurnPrediction {
  userId: string;
  userName: string;
  probability: number;
  riskLevel: 'high' | 'medium' | 'low';
  revenueAtRisk: number;
  lastActivity: Date;
  accountAge: number;
  recommendedAction: string;
}

interface RevenueForecast {
  date: string;
  predicted: number;
  lowerBound: number;
  upperBound: number;
  confidence: number;
}

interface GrowthOpportunity {
  id: string;
  type: 'upsell' | 'winback' | 'expansion';
  title: string;
  description: string;
  potentialRevenue: number;
  probability: number;
  effort: 'low' | 'medium' | 'high';
  timeline: string;
}

interface BusinessIntelligenceDesktopProps {
  apiEndpoint?: string;
  onMetricsUpdate?: (metrics: BusinessMetrics) => void;
}

const BusinessIntelligenceDesktop: React.FC<BusinessIntelligenceDesktopProps> = ({
  apiEndpoint = '/api/intelligence/business',
  onMetricsUpdate,
}) => {
  const [metrics, setMetrics] = useState<BusinessMetrics | null>(null);
  const [forecast, setForecast] = useState<RevenueForecast[]>([]);
  const [churnPredictions, setChurnPredictions] = useState<ChurnPrediction[]>([]);
  const [opportunities, setOpportunities] = useState<GrowthOpportunity[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [dateRange, setDateRange] = useState<[Date | null, Date | null]>([
    new Date(new Date().setMonth(new Date().getMonth() - 1)),
    new Date(),
  ]);
  const [forecastMonths, setForecastMonths] = useState(12);
  const [scenario, setScenario] = useState<'conservative' | 'most_likely' | 'optimistic'>('most_likely');
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [roiCalculatorOpen, setRoiCalculatorOpen] = useState(false);
  const [exportMenuAnchor, setExportMenuAnchor] = useState<null | HTMLElement>(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(60);
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null);
  const [comparisonMode, setComparisonMode] = useState(false);
  const [roiInputs, setRoiInputs] = useState({
    customerAcquisition: 50000,
    operational: 30000,
    marketing: 20000,
    technology: 15000,
    subscriptionRevenue: 150000,
    transactionRevenue: 30000,
    addonRevenue: 10000,
  });

  useEffect(() => {
    // Set up IPC listeners for desktop-specific features
    ipcRenderer.on('metrics-updated', (event, newMetrics) => {
      setMetrics(newMetrics);
      if (onMetricsUpdate) {
        onMetricsUpdate(newMetrics);
      }
    });

    ipcRenderer.on('export-complete', (event, result) => {
      setSnackbarMessage(`Export complete: ${result.filename}`);
      setSnackbarOpen(true);
    });

    ipcRenderer.on('realtime-update', (event, update) => {
      // Handle real-time updates
      console.log('Real-time update:', update);
    });

    // Load initial data
    loadMetrics();
    loadOpportunities();

    // Set up auto-refresh
    let intervalId: NodeJS.Timeout;
    if (autoRefresh) {
      intervalId = setInterval(() => {
        loadMetrics();
      }, refreshInterval * 1000);
    }

    return () => {
      ipcRenderer.removeAllListeners('metrics-updated');
      ipcRenderer.removeAllListeners('export-complete');
      ipcRenderer.removeAllListeners('realtime-update');
      if (intervalId) clearInterval(intervalId);
    };
  }, [autoRefresh, refreshInterval, onMetricsUpdate]);

  const loadMetrics = useCallback(async () => {
    setIsLoading(true);

    try {
      // Mock data for demonstration
      const mockMetrics: BusinessMetrics = {
        mrr: 125000,
        mrrGrowth: 8.5,
        arr: 1500000,
        activeUsers: 1250,
        userGrowth: 6.8,
        churnRate: 4.5,
        ltvCacRatio: 3.2,
        revenue: 150000,
        costs: 100000,
        profit: 50000,
        roi: 50,
        grossMargin: 65,
        netMargin: 33,
        cashFlow: 45000,
        runwayMonths: 18,
      };

      setMetrics(mockMetrics);
      
      // Connect to desktop data sources
      const desktopData = await ipcRenderer.invoke('fetch-business-metrics', {
        dateRange,
        includeForecasts: true,
      });
      
      if (desktopData) {
        setMetrics(desktopData.metrics);
      }
      
      if (onMetricsUpdate) {
        onMetricsUpdate(mockMetrics);
      }
    } catch (err) {
      console.error('Failed to load metrics:', err);
    } finally {
      setIsLoading(false);
    }
  }, [dateRange, onMetricsUpdate]);

  const loadOpportunities = useCallback(async () => {
    try {
      const mockOpportunities: GrowthOpportunity[] = [
        {
          id: 'opp1',
          type: 'upsell',
          title: 'Enterprise Tier Upsell',
          description: '23 customers ready for enterprise features',
          potentialRevenue: 45000,
          probability: 0.75,
          effort: 'low',
          timeline: '30 days',
        },
        {
          id: 'opp2',
          type: 'winback',
          title: 'Win-Back Campaign',
          description: '45 churned customers with high engagement history',
          potentialRevenue: 28000,
          probability: 0.45,
          effort: 'medium',
          timeline: '60 days',
        },
        {
          id: 'opp3',
          type: 'expansion',
          title: 'New Market Expansion',
          description: 'APAC market showing strong demand signals',
          potentialRevenue: 150000,
          probability: 0.60,
          effort: 'high',
          timeline: '90 days',
        },
      ];

      setOpportunities(mockOpportunities);
    } catch (err) {
      console.error('Failed to load opportunities:', err);
    }
  }, []);

  const generateForecast = useCallback(async () => {
    setIsLoading(true);
    try {
      // Request forecast from desktop ML engine
      const forecastData = await ipcRenderer.invoke('generate-forecast', {
        months: forecastMonths,
        scenario,
        includeSeasonality: true,
        currentMRR: metrics?.mrr || 125000,
      });

      // Mock forecast for demonstration
      const mockForecast: RevenueForecast[] = [];
      const baseRevenue = metrics?.mrr || 125000;
      const growthRate = scenario === 'optimistic' ? 0.12 : scenario === 'conservative' ? 0.03 : 0.07;

      for (let i = 1; i <= forecastMonths; i++) {
        const date = new Date();
        date.setMonth(date.getMonth() + i);
        
        const predicted = baseRevenue * Math.pow(1 + growthRate, i);
        const confidence = Math.max(0.5, 1 - (i * 0.02));
        
        mockForecast.push({
          date: date.toISOString().split('T')[0],
          predicted,
          lowerBound: predicted * (1 - (1 - confidence) * 0.3),
          upperBound: predicted * (1 + (1 - confidence) * 0.3),
          confidence,
        });
      }

      setForecast(forecastData || mockForecast);
    } catch (err) {
      console.error('Forecast error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [metrics, forecastMonths, scenario]);

  const predictChurn = useCallback(async () => {
    setIsLoading(true);
    try {
      // Request churn predictions from desktop ML engine
      const predictions = await ipcRenderer.invoke('predict-churn', {
        threshold: 0.3,
        includeRecommendations: true,
      });

      // Mock predictions for demonstration
      const mockPredictions: ChurnPrediction[] = [
        {
          userId: 'usr_001',
          userName: 'Acme Corp',
          probability: 0.85,
          riskLevel: 'high',
          revenueAtRisk: 5000,
          lastActivity: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000),
          accountAge: 18,
          recommendedAction: 'Immediate outreach with retention offer',
        },
        {
          userId: 'usr_002',
          userName: 'TechStart Inc',
          probability: 0.72,
          riskLevel: 'high',
          revenueAtRisk: 3500,
          lastActivity: new Date(Date.now() - 20 * 24 * 60 * 60 * 1000),
          accountAge: 12,
          recommendedAction: 'Schedule product demo for new features',
        },
        {
          userId: 'usr_003',
          userName: 'Global Solutions',
          probability: 0.45,
          riskLevel: 'medium',
          revenueAtRisk: 2500,
          lastActivity: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
          accountAge: 24,
          recommendedAction: 'Send satisfaction survey',
        },
      ];

      setChurnPredictions(predictions || mockPredictions);
    } catch (err) {
      console.error('Churn prediction error:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const calculateROI = useCallback(() => {
    const totalInvestment = 
      roiInputs.customerAcquisition + 
      roiInputs.operational + 
      roiInputs.marketing +
      roiInputs.technology;
    
    const totalRevenue = 
      roiInputs.subscriptionRevenue + 
      roiInputs.transactionRevenue + 
      roiInputs.addonRevenue;
    
    const profit = totalRevenue - totalInvestment;
    const roi = (profit / totalInvestment) * 100;
    const paybackPeriod = totalInvestment / (totalRevenue / 12);
    
    return { totalInvestment, totalRevenue, profit, roi, paybackPeriod };
  }, [roiInputs]);

  const exportData = useCallback(async (format: string) => {
    try {
      const result = await ipcRenderer.invoke('export-business-data', {
        format,
        data: {
          metrics,
          forecast,
          churnPredictions,
          opportunities,
        },
        dateRange,
      });
      
      setSnackbarMessage(`Data exported as ${format.toUpperCase()}`);
      setSnackbarOpen(true);
    } catch (err) {
      console.error('Export error:', err);
    }
  }, [metrics, forecast, churnPredictions, opportunities, dateRange]);

  const generateReport = useCallback(async () => {
    try {
      await ipcRenderer.invoke('generate-executive-report', {
        metrics,
        forecast,
        format: 'pdf',
        recipient: 'executive@company.com',
      });
      
      setSnackbarMessage('Executive report generated and sent');
      setSnackbarOpen(true);
    } catch (err) {
      console.error('Report generation error:', err);
    }
  }, [metrics, forecast]);

  const renderKPIGrid = () => {
    if (!metrics) return null;

    const kpis = [
      {
        title: 'Monthly Recurring Revenue',
        value: `$${(metrics.mrr / 1000).toFixed(0)}K`,
        change: metrics.mrrGrowth,
        trend: metrics.mrrGrowth > 0 ? 'up' : 'down',
        icon: <MoneyIcon />,
        color: '#3a7bd5',
      },
      {
        title: 'Annual Recurring Revenue',
        value: `$${(metrics.arr / 1000000).toFixed(1)}M`,
        change: metrics.mrrGrowth * 12,
        trend: metrics.mrrGrowth > 0 ? 'up' : 'down',
        icon: <AccountIcon />,
        color: '#00d2ff',
      },
      {
        title: 'Active Users',
        value: metrics.activeUsers.toLocaleString(),
        change: metrics.userGrowth,
        trend: metrics.userGrowth > 0 ? 'up' : 'down',
        icon: <GroupsIcon />,
        color: '#764ba2',
      },
      {
        title: 'Churn Rate',
        value: `${metrics.churnRate}%`,
        change: -0.3,
        trend: metrics.churnRate < 5 ? 'up' : 'down',
        icon: <WarningIcon />,
        color: metrics.churnRate < 5 ? '#4caf50' : '#f44336',
      },
      {
        title: 'LTV:CAC Ratio',
        value: `${metrics.ltvCacRatio}x`,
        change: 0.2,
        trend: metrics.ltvCacRatio > 3 ? 'up' : 'neutral',
        icon: <ChartIcon />,
        color: '#f093fb',
      },
      {
        title: 'Gross Margin',
        value: `${metrics.grossMargin}%`,
        change: 2.1,
        trend: 'up',
        icon: <PieChartIcon />,
        color: '#4caf50',
      },
      {
        title: 'Cash Flow',
        value: `$${(metrics.cashFlow / 1000).toFixed(0)}K`,
        change: 5.5,
        trend: 'up',
        icon: <TimelineIcon />,
        color: '#ff9800',
      },
      {
        title: 'Runway',
        value: `${metrics.runwayMonths} mo`,
        change: 0,
        trend: 'neutral',
        icon: <SpeedIcon />,
        color: metrics.runwayMonths > 12 ? '#4caf50' : '#ff9800',
      },
    ];

    return (
      <Grid container spacing={3}>
        {kpis.map((kpi, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <KPICard
              trend={kpi.trend}
              onClick={() => setSelectedMetric(kpi.title)}
              elevation={selectedMetric === kpi.title ? 6 : 2}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Avatar sx={{ bgcolor: kpi.color }}>
                  {kpi.icon}
                </Avatar>
                {kpi.trend === 'up' && <TrendingUpIcon color="success" />}
                {kpi.trend === 'down' && <TrendingDownIcon color="error" />}
              </Box>
              <MetricDisplay>
                <Typography variant="h4" component="div">
                  {kpi.value}
                </Typography>
              </MetricDisplay>
              <Typography variant="body2" color="textSecondary">
                {kpi.title}
              </Typography>
              <Typography
                variant="caption"
                sx={{
                  color: kpi.change > 0 ? 'success.main' : 'error.main',
                  fontWeight: 'bold',
                }}
              >
                {kpi.change > 0 ? '+' : ''}{kpi.change}% MoM
              </Typography>
            </KPICard>
          </Grid>
        ))}
      </Grid>
    );
  };

  const renderForecastChart = () => {
    if (forecast.length === 0) return null;

    const chartData = forecast.map(f => ({
      date: new Date(f.date).toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
      predicted: Math.round(f.predicted),
      upperBound: Math.round(f.upperBound),
      lowerBound: Math.round(f.lowerBound),
      confidence: (f.confidence * 100).toFixed(0),
    }));

    return (
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">
              <TimelineIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Revenue Forecast
            </Typography>
            <ToggleButtonGroup
              value={scenario}
              exclusive
              onChange={(e, v) => v && setScenario(v)}
              size="small"
            >
              <ToggleButton value="conservative">Conservative</ToggleButton>
              <ToggleButton value="most_likely">Most Likely</ToggleButton>
              <ToggleButton value="optimistic">Optimistic</ToggleButton>
            </ToggleButtonGroup>
          </Box>
          
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <ChartTooltip />
              <Legend />
              <Area
                type="monotone"
                dataKey="upperBound"
                stackId="1"
                stroke="#82ca9d"
                fill="#82ca9d"
                fillOpacity={0.3}
                name="Upper Bound"
              />
              <Area
                type="monotone"
                dataKey="predicted"
                stackId="2"
                stroke="#3a7bd5"
                fill="#3a7bd5"
                fillOpacity={0.6}
                name="Predicted"
              />
              <Area
                type="monotone"
                dataKey="lowerBound"
                stackId="3"
                stroke="#ffc658"
                fill="#ffc658"
                fillOpacity={0.3}
                name="Lower Bound"
              />
            </AreaChart>
          </ResponsiveContainer>

          <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2">
              Forecast Months: {forecastMonths}
            </Typography>
            <Slider
              value={forecastMonths}
              onChange={(e, v) => setForecastMonths(v as number)}
              min={3}
              max={24}
              step={3}
              marks
              sx={{ flex: 1 }}
            />
            <Button
              variant="contained"
              onClick={generateForecast}
              disabled={isLoading}
              startIcon={isLoading ? <CircularProgress size={20} /> : <AutoGraphIcon />}
            >
              Generate
            </Button>
          </Box>
        </CardContent>
      </Card>
    );
  };

  const renderChurnAnalysis = () => {
    if (churnPredictions.length === 0) {
      return (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <WarningIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Churn Risk Analysis
            </Typography>
            <Button
              variant="contained"
              onClick={predictChurn}
              disabled={isLoading}
              startIcon={isLoading ? <CircularProgress size={20} /> : <AnalyticsIcon />}
            >
              Analyze Churn Risk
            </Button>
          </CardContent>
        </Card>
      );
    }

    const totalAtRisk = churnPredictions.reduce((sum, p) => sum + p.revenueAtRisk, 0);

    return (
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">
              <WarningIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Churn Risk Analysis
            </Typography>
            <Chip
              label={`$${(totalAtRisk / 1000).toFixed(0)}K at risk`}
              color="error"
              icon={<ErrorIcon />}
            />
          </Box>

          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Customer</TableCell>
                  <TableCell align="right">Risk</TableCell>
                  <TableCell>Level</TableCell>
                  <TableCell align="right">Revenue</TableCell>
                  <TableCell>Action</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {churnPredictions.map((prediction) => (
                  <TableRow key={prediction.userId}>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Avatar sx={{ width: 32, height: 32 }}>
                          {prediction.userName.charAt(0)}
                        </Avatar>
                        <Box>
                          <Typography variant="body2">{prediction.userName}</Typography>
                          <Typography variant="caption" color="textSecondary">
                            {prediction.accountAge} months
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Typography
                        variant="body2"
                        sx={{
                          fontWeight: 'bold',
                          color: prediction.probability > 0.7 ? 'error.main' : 
                                prediction.probability > 0.4 ? 'warning.main' : 
                                'success.main',
                        }}
                      >
                        {(prediction.probability * 100).toFixed(0)}%
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={prediction.riskLevel.toUpperCase()}
                        size="small"
                        color={
                          prediction.riskLevel === 'high' ? 'error' :
                          prediction.riskLevel === 'medium' ? 'warning' :
                          'success'
                        }
                      />
                    </TableCell>
                    <TableCell align="right">
                      ${prediction.revenueAtRisk.toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <Tooltip title={prediction.recommendedAction}>
                        <IconButton size="small">
                          <InfoIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          <Alert severity="warning" sx={{ mt: 2 }}>
            <Typography variant="subtitle2">Recommended Actions:</Typography>
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              <li>Contact high-risk customers within 24 hours</li>
              <li>Prepare retention offers for at-risk accounts</li>
              <li>Schedule executive calls for enterprise accounts</li>
            </ul>
          </Alert>
        </CardContent>
      </Card>
    );
  };

  const renderOpportunities = () => {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <InsightsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Growth Opportunities
          </Typography>
          
          <Grid container spacing={2}>
            {opportunities.map((opp) => (
              <Grid item xs={12} md={4} key={opp.id}>
                <OpportunityCard type={opp.type} elevation={2}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Chip
                      label={opp.type.toUpperCase()}
                      size="small"
                      color={
                        opp.type === 'upsell' ? 'success' :
                        opp.type === 'winback' ? 'secondary' :
                        'primary'
                      }
                    />
                    <Typography variant="caption" color="textSecondary">
                      {opp.timeline}
                    </Typography>
                  </Box>
                  
                  <Typography variant="subtitle1" gutterBottom>
                    {opp.title}
                  </Typography>
                  
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    {opp.description}
                  </Typography>
                  
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="h5" color="primary">
                      ${(opp.potentialRevenue / 1000).toFixed(0)}K
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={opp.probability * 100}
                      sx={{ mt: 1, mb: 0.5 }}
                    />
                    <Typography variant="caption">
                      {(opp.probability * 100).toFixed(0)}% probability • {opp.effort} effort
                    </Typography>
                  </Box>
                </OpportunityCard>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>
    );
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
        <ExecutiveCard>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box>
                <Typography variant="h4" gutterBottom>
                  <DashboardIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Business Intelligence Dashboard
                </Typography>
                <Typography variant="body1">
                  Real-time business metrics and predictive analytics
                </Typography>
              </Box>
              <Box>
                <Tooltip title="Refresh Data">
                  <IconButton color="inherit" onClick={loadMetrics}>
                    <RefreshIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Export">
                  <IconButton
                    color="inherit"
                    onClick={(e) => setExportMenuAnchor(e.currentTarget)}
                  >
                    <DownloadIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Generate Report">
                  <IconButton color="inherit" onClick={generateReport}>
                    <EmailIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Print">
                  <IconButton color="inherit" onClick={() => window.print()}>
                    <PrintIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Settings">
                  <IconButton color="inherit" onClick={() => setSettingsOpen(!settingsOpen)}>
                    <SettingsIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>
          </CardContent>
        </ExecutiveCard>

        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
            <Tab label="Overview" icon={<DashboardIcon />} />
            <Tab label="Forecast" icon={<TimelineIcon />} />
            <Tab label="Churn Analysis" icon={<WarningIcon />} />
            <Tab label="Opportunities" icon={<InsightsIcon />} />
            <Tab label="ROI Calculator" icon={<CalculateIcon />} />
          </Tabs>
        </Box>

        <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
          {tabValue === 0 && (
            <Box>
              {isLoading && !metrics ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
                  <CircularProgress />
                </Box>
              ) : (
                <>
                  {renderKPIGrid()}
                  <Box sx={{ mt: 3 }}>
                    <Grid container spacing={3}>
                      <Grid item xs={12} lg={8}>
                        {renderForecastChart()}
                      </Grid>
                      <Grid item xs={12} lg={4}>
                        {renderOpportunities()}
                      </Grid>
                    </Grid>
                  </Box>
                </>
              )}
            </Box>
          )}

          {tabValue === 1 && (
            <Box>
              {renderForecastChart()}
            </Box>
          )}

          {tabValue === 2 && (
            <Box>
              {renderChurnAnalysis()}
            </Box>
          )}

          {tabValue === 3 && (
            <Box>
              {renderOpportunities()}
            </Box>
          )}

          {tabValue === 4 && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <CalculateIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  ROI Calculator
                </Typography>
                
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle1" gutterBottom>
                      Investment
                    </Typography>
                    <TextField
                      fullWidth
                      label="Customer Acquisition"
                      type="number"
                      value={roiInputs.customerAcquisition}
                      onChange={(e) => setRoiInputs({
                        ...roiInputs,
                        customerAcquisition: parseInt(e.target.value) || 0,
                      })}
                      margin="normal"
                    />
                    <TextField
                      fullWidth
                      label="Operational Costs"
                      type="number"
                      value={roiInputs.operational}
                      onChange={(e) => setRoiInputs({
                        ...roiInputs,
                        operational: parseInt(e.target.value) || 0,
                      })}
                      margin="normal"
                    />
                    <TextField
                      fullWidth
                      label="Marketing Spend"
                      type="number"
                      value={roiInputs.marketing}
                      onChange={(e) => setRoiInputs({
                        ...roiInputs,
                        marketing: parseInt(e.target.value) || 0,
                      })}
                      margin="normal"
                    />
                    <TextField
                      fullWidth
                      label="Technology Investment"
                      type="number"
                      value={roiInputs.technology}
                      onChange={(e) => setRoiInputs({
                        ...roiInputs,
                        technology: parseInt(e.target.value) || 0,
                      })}
                      margin="normal"
                    />
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle1" gutterBottom>
                      Revenue
                    </Typography>
                    <TextField
                      fullWidth
                      label="Subscription Revenue"
                      type="number"
                      value={roiInputs.subscriptionRevenue}
                      onChange={(e) => setRoiInputs({
                        ...roiInputs,
                        subscriptionRevenue: parseInt(e.target.value) || 0,
                      })}
                      margin="normal"
                    />
                    <TextField
                      fullWidth
                      label="Transaction Revenue"
                      type="number"
                      value={roiInputs.transactionRevenue}
                      onChange={(e) => setRoiInputs({
                        ...roiInputs,
                        transactionRevenue: parseInt(e.target.value) || 0,
                      })}
                      margin="normal"
                    />
                    <TextField
                      fullWidth
                      label="Add-on Revenue"
                      type="number"
                      value={roiInputs.addonRevenue}
                      onChange={(e) => setRoiInputs({
                        ...roiInputs,
                        addonRevenue: parseInt(e.target.value) || 0,
                      })}
                      margin="normal"
                    />
                  </Grid>
                </Grid>

                <Box sx={{ mt: 3 }}>
                  <Button
                    variant="contained"
                    size="large"
                    onClick={() => {
                      const result = calculateROI();
                      setSnackbarMessage(
                        `ROI: ${result.roi.toFixed(1)}% | Payback: ${result.paybackPeriod.toFixed(1)} months`
                      );
                      setSnackbarOpen(true);
                    }}
                    startIcon={<CalculateIcon />}
                  >
                    Calculate ROI
                  </Button>
                </Box>

                {(() => {
                  const result = calculateROI();
                  return (
                    <Box sx={{ mt: 3 }}>
                      <Grid container spacing={2}>
                        <Grid item xs={6} md={3}>
                          <Paper sx={{ p: 2, textAlign: 'center' }}>
                            <Typography variant="h6">
                              ${(result.totalInvestment / 1000).toFixed(0)}K
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                              Total Investment
                            </Typography>
                          </Paper>
                        </Grid>
                        <Grid item xs={6} md={3}>
                          <Paper sx={{ p: 2, textAlign: 'center' }}>
                            <Typography variant="h6">
                              ${(result.totalRevenue / 1000).toFixed(0)}K
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                              Total Revenue
                            </Typography>
                          </Paper>
                        </Grid>
                        <Grid item xs={6} md={3}>
                          <Paper sx={{ p: 2, textAlign: 'center' }}>
                            <Typography variant="h6" color={result.profit > 0 ? 'success.main' : 'error.main'}>
                              ${(result.profit / 1000).toFixed(0)}K
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                              Net Profit
                            </Typography>
                          </Paper>
                        </Grid>
                        <Grid item xs={6} md={3}>
                          <Paper sx={{ p: 2, textAlign: 'center' }}>
                            <Typography variant="h6" color="primary">
                              {result.roi.toFixed(1)}%
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                              Return on Investment
                            </Typography>
                          </Paper>
                        </Grid>
                      </Grid>
                    </Box>
                  );
                })()}
              </CardContent>
            </Card>
          )}
        </Box>

        {/* Export Menu */}
        <Menu
          anchorEl={exportMenuAnchor}
          open={Boolean(exportMenuAnchor)}
          onClose={() => setExportMenuAnchor(null)}
        >
          <MenuItem onClick={() => { exportData('pdf'); setExportMenuAnchor(null); }}>
            Export as PDF
          </MenuItem>
          <MenuItem onClick={() => { exportData('excel'); setExportMenuAnchor(null); }}>
            Export as Excel
          </MenuItem>
          <MenuItem onClick={() => { exportData('csv'); setExportMenuAnchor(null); }}>
            Export as CSV
          </MenuItem>
          <MenuItem onClick={() => { exportData('json'); setExportMenuAnchor(null); }}>
            Export as JSON
          </MenuItem>
        </Menu>

        {/* Settings Drawer */}
        <Drawer
          anchor="right"
          open={settingsOpen}
          onClose={() => setSettingsOpen(false)}
        >
          <Box sx={{ width: 350, p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Dashboard Settings
            </Typography>
            
            <Divider sx={{ my: 2 }} />
            
            <Typography variant="subtitle2" gutterBottom>
              Auto Refresh
            </Typography>
            <FormControlLabel
              control={
                <Switch
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                />
              }
              label="Enable auto refresh"
            />
            
            {autoRefresh && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" gutterBottom>
                  Refresh Interval: {refreshInterval}s
                </Typography>
                <Slider
                  value={refreshInterval}
                  onChange={(e, v) => setRefreshInterval(v as number)}
                  min={30}
                  max={300}
                  step={30}
                  marks
                />
              </Box>
            )}

            <Divider sx={{ my: 2 }} />
            
            <Typography variant="subtitle2" gutterBottom>
              Comparison Mode
            </Typography>
            <FormControlLabel
              control={
                <Switch
                  checked={comparisonMode}
                  onChange={(e) => setComparisonMode(e.target.checked)}
                />
              }
              label="Enable period comparison"
            />

            <Divider sx={{ my: 2 }} />
            
            <Typography variant="subtitle2" gutterBottom>
              Date Range
            </Typography>
            <Box sx={{ mt: 2 }}>
              <DatePicker
                label="Start Date"
                value={dateRange[0]}
                onChange={(date) => setDateRange([date, dateRange[1]])}
                renderInput={(params) => <TextField {...params} fullWidth margin="normal" />}
              />
              <DatePicker
                label="End Date"
                value={dateRange[1]}
                onChange={(date) => setDateRange([dateRange[0], date])}
                renderInput={(params) => <TextField {...params} fullWidth margin="normal" />}
              />
            </Box>

            <Box sx={{ mt: 3 }}>
              <Button
                fullWidth
                variant="contained"
                onClick={() => {
                  loadMetrics();
                  setSettingsOpen(false);
                }}
              >
                Apply Settings
              </Button>
            </Box>
          </Box>
        </Drawer>

        {/* Speed Dial for Quick Actions */}
        <StyledSpeedDial
          ariaLabel="Quick Actions"
          icon={<SpeedDialIcon />}
        >
          <SpeedDialAction
            icon={<CalculateIcon />}
            tooltipTitle="ROI Calculator"
            onClick={() => setRoiCalculatorOpen(true)}
          />
          <SpeedDialAction
            icon={<AutoGraphIcon />}
            tooltipTitle="Generate Forecast"
            onClick={generateForecast}
          />
          <SpeedDialAction
            icon={<WarningIcon />}
            tooltipTitle="Analyze Churn"
            onClick={predictChurn}
          />
          <SpeedDialAction
            icon={<EmailIcon />}
            tooltipTitle="Send Report"
            onClick={generateReport}
          />
        </StyledSpeedDial>

        <Snackbar
          open={snackbarOpen}
          autoHideDuration={6000}
          onClose={() => setSnackbarOpen(false)}
          message={snackbarMessage}
        />
      </Box>
    </LocalizationProvider>
  );
};

export default BusinessIntelligenceDesktop;