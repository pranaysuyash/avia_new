/**
 * Business Intelligence Component
 * ROI calculations, revenue forecasting, and business metrics
 */

import React, { useState, useEffect, useCallback } from 'react';
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
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip,
  Tab,
  Tabs,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  ListItemSecondaryAction,
  Slider,
  Switch,
  FormControlLabel,
  SpeedDial,
  SpeedDialAction,
  SpeedDialIcon,
  Divider,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  AttachMoney as MoneyIcon,
  People as PeopleIcon,
  Timeline as TimelineIcon,
  Assessment as AssessmentIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
  Lightbulb as LightbulbIcon,
  Calculate as CalculateIcon,
  PieChart as PieChartIcon,
  ShowChart as ShowChartIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  NotificationsActive as AlertIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
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
  Tooltip as ChartTooltip,
  Legend,
  ResponsiveContainer,
  RadialBarChart,
  RadialBar,
  Treemap,
} from 'recharts';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

// Styled components
const MetricCard = styled(Card)(({ theme, trend }: any) => ({
  height: '100%',
  position: 'relative',
  overflow: 'visible',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 4,
    background: trend === 'up' 
      ? 'linear-gradient(90deg, #4caf50 0%, #8bc34a 100%)'
      : trend === 'down'
      ? 'linear-gradient(90deg, #f44336 0%, #ff9800 100%)'
      : 'linear-gradient(90deg, #2196f3 0%, #00bcd4 100%)',
  },
}));

const KPIValue = styled(Typography)(({ theme, trend }: any) => ({
  fontSize: '2.5rem',
  fontWeight: 'bold',
  color: trend === 'up' ? theme.palette.success.main : trend === 'down' ? theme.palette.error.main : theme.palette.primary.main,
}));

const HealthScore = styled(Box)(({ score }: { score: number }) => ({
  width: 120,
  height: 120,
  borderRadius: '50%',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: '2rem',
  fontWeight: 'bold',
  color: 'white',
  background: score >= 80 
    ? 'linear-gradient(135deg, #4caf50 0%, #8bc34a 100%)'
    : score >= 60
    ? 'linear-gradient(135deg, #ff9800 0%, #ffc107 100%)'
    : 'linear-gradient(135deg, #f44336 0%, #e91e63 100%)',
  boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
}));

const ChurnRiskChip = styled(Chip)(({ risk }: { risk: string }) => ({
  fontWeight: 'bold',
  ...(risk === 'high' && {
    backgroundColor: '#ffebee',
    color: '#c62828',
    borderColor: '#ef5350',
  }),
  ...(risk === 'medium' && {
    backgroundColor: '#fff3e0',
    color: '#e65100',
    borderColor: '#ff9800',
  }),
  ...(risk === 'low' && {
    backgroundColor: '#e8f5e9',
    color: '#2e7d32',
    borderColor: '#66bb6a',
  }),
}));

interface BusinessMetrics {
  mrr: number;
  mrrGrowth: number;
  activeUsers: number;
  userGrowth: number;
  churnRate: number;
  ltvCacRatio: number;
  revenue: number;
  costs: number;
  profit: number;
  roi: number;
}

interface ChurnPrediction {
  userId: number;
  probability: number;
  riskLevel: 'high' | 'medium' | 'low';
  revenueAtRisk: number;
}

interface RevenueForcast {
  date: string;
  predicted: number;
  lowerBound: number;
  upperBound: number;
}

interface BusinessIntelligenceProps {
  apiEndpoint?: string;
  onMetricsUpdate?: (metrics: BusinessMetrics) => void;
}

const BusinessIntelligence: React.FC<BusinessIntelligenceProps> = ({
  apiEndpoint = '/api/intelligence/business',
  onMetricsUpdate,
}) => {
  const [metrics, setMetrics] = useState<BusinessMetrics | null>(null);
  const [forecast, setForecast] = useState<RevenueForcast[]>([]);
  const [churnPredictions, setChurnPredictions] = useState<ChurnPrediction[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [forecastMonths, setForecastMonths] = useState(12);
  const [includeSeasonality, setIncludeSeasonality] = useState(true);
  const [scenario, setScenario] = useState<'most_likely' | 'best_case' | 'worst_case'>('most_likely');
  const [dateRange, setDateRange] = useState({
    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
    end: new Date(),
  });

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Mock data for demonstration
      const mockMetrics: BusinessMetrics = {
        mrr: 125000,
        mrrGrowth: 8.5,
        activeUsers: 1250,
        userGrowth: 6.8,
        churnRate: 4.5,
        ltvCacRatio: 3.2,
        revenue: 150000,
        costs: 100000,
        profit: 50000,
        roi: 50,
      };

      setMetrics(mockMetrics);
      
      if (onMetricsUpdate) {
        onMetricsUpdate(mockMetrics);
      }
    } catch (err) {
      setError('Failed to load business metrics');
      console.error('Metrics error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [onMetricsUpdate]);

  const generateForecast = useCallback(async () => {
    setIsLoading(true);
    try {
      // Mock forecast data
      const mockForecast: RevenueForcast[] = [];
      const baseRevenue = metrics?.mrr || 125000;
      const growthRate = scenario === 'best_case' ? 0.10 : scenario === 'worst_case' ? 0.02 : 0.05;

      for (let i = 1; i <= forecastMonths; i++) {
        const date = new Date();
        date.setMonth(date.getMonth() + i);
        
        let predicted = baseRevenue * Math.pow(1 + growthRate, i);
        if (includeSeasonality) {
          const month = date.getMonth();
          if (month === 11 || month === 0) predicted *= 1.2; // Holiday boost
          if (month === 6 || month === 7) predicted *= 0.9; // Summer dip
        }
        
        mockForecast.push({
          date: date.toISOString().split('T')[0],
          predicted,
          lowerBound: predicted * 0.85,
          upperBound: predicted * 1.15,
        });
      }

      setForecast(mockForecast);
    } catch (err) {
      console.error('Forecast error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [metrics, forecastMonths, includeSeasonality, scenario]);

  const predictChurn = useCallback(async () => {
    setIsLoading(true);
    try {
      // Mock churn predictions
      const mockPredictions: ChurnPrediction[] = [
        { userId: 101, probability: 0.85, riskLevel: 'high', revenueAtRisk: 500 },
        { userId: 102, probability: 0.72, riskLevel: 'high', revenueAtRisk: 450 },
        { userId: 103, probability: 0.45, riskLevel: 'medium', revenueAtRisk: 300 },
        { userId: 104, probability: 0.38, riskLevel: 'medium', revenueAtRisk: 250 },
        { userId: 105, probability: 0.15, riskLevel: 'low', revenueAtRisk: 100 },
      ];

      setChurnPredictions(mockPredictions);
    } catch (err) {
      console.error('Churn prediction error:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const renderKPICards = () => {
    if (!metrics) return null;

    const kpis = [
      {
        title: 'Monthly Recurring Revenue',
        value: `$${(metrics.mrr / 1000).toFixed(0)}K`,
        change: metrics.mrrGrowth,
        icon: <MoneyIcon />,
        trend: metrics.mrrGrowth > 0 ? 'up' : 'down',
      },
      {
        title: 'Active Users',
        value: metrics.activeUsers.toLocaleString(),
        change: metrics.userGrowth,
        icon: <PeopleIcon />,
        trend: metrics.userGrowth > 0 ? 'up' : 'down',
      },
      {
        title: 'Churn Rate',
        value: `${metrics.churnRate}%`,
        change: -0.3,
        icon: <TrendingDownIcon />,
        trend: metrics.churnRate < 5 ? 'up' : 'down',
      },
      {
        title: 'LTV:CAC Ratio',
        value: `${metrics.ltvCacRatio}x`,
        change: 0.2,
        icon: <AssessmentIcon />,
        trend: metrics.ltvCacRatio > 3 ? 'up' : 'neutral',
      },
    ];

    return (
      <Grid container spacing={3}>
        {kpis.map((kpi, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <MetricCard trend={kpi.trend}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Avatar sx={{ bgcolor: 'primary.main' }}>{kpi.icon}</Avatar>
                  {kpi.trend === 'up' ? (
                    <TrendingUpIcon color="success" />
                  ) : kpi.trend === 'down' ? (
                    <TrendingDownIcon color="error" />
                  ) : null}
                </Box>
                <KPIValue trend={kpi.trend}>{kpi.value}</KPIValue>
                <Typography variant="body2" color="textSecondary">
                  {kpi.title}
                </Typography>
                <Typography
                  variant="body2"
                  sx={{
                    color: kpi.change > 0 ? 'success.main' : 'error.main',
                    fontWeight: 'bold',
                  }}
                >
                  {kpi.change > 0 ? '+' : ''}{kpi.change}% MoM
                </Typography>
              </CardContent>
            </MetricCard>
          </Grid>
        ))}
      </Grid>
    );
  };

  const renderRevenueChart = () => {
    const data = forecast.map(f => ({
      date: new Date(f.date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
      predicted: Math.round(f.predicted),
      lower: Math.round(f.lowerBound),
      upper: Math.round(f.upperBound),
    }));

    return (
      <ResponsiveContainer width="100%" height={400}>
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <ChartTooltip />
          <Legend />
          <Area
            type="monotone"
            dataKey="upper"
            stackId="1"
            stroke="#8884d8"
            fill="#8884d8"
            fillOpacity={0.2}
            name="Upper Bound"
          />
          <Area
            type="monotone"
            dataKey="predicted"
            stackId="2"
            stroke="#82ca9d"
            fill="#82ca9d"
            fillOpacity={0.6}
            name="Predicted"
          />
          <Area
            type="monotone"
            dataKey="lower"
            stackId="3"
            stroke="#ffc658"
            fill="#ffc658"
            fillOpacity={0.2}
            name="Lower Bound"
          />
        </AreaChart>
      </ResponsiveContainer>
    );
  };

  const renderChurnTable = () => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>User ID</TableCell>
            <TableCell>Churn Probability</TableCell>
            <TableCell>Risk Level</TableCell>
            <TableCell>Revenue at Risk</TableCell>
            <TableCell>Action</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {churnPredictions.map((prediction) => (
            <TableRow key={prediction.userId}>
              <TableCell>{prediction.userId}</TableCell>
              <TableCell>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <LinearProgress
                    variant="determinate"
                    value={prediction.probability * 100}
                    sx={{ width: 100, mr: 1 }}
                  />
                  {(prediction.probability * 100).toFixed(0)}%
                </Box>
              </TableCell>
              <TableCell>
                <ChurnRiskChip
                  label={prediction.riskLevel.toUpperCase()}
                  risk={prediction.riskLevel}
                  variant="outlined"
                />
              </TableCell>
              <TableCell>${prediction.revenueAtRisk}</TableCell>
              <TableCell>
                <Tooltip title="Contact Customer">
                  <IconButton size="small" color="primary">
                    <AlertIcon />
                  </IconButton>
                </Tooltip>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

  const renderHealthScores = () => {
    const healthScores = [
      { name: 'Revenue Health', score: 85 },
      { name: 'User Health', score: 78 },
      { name: 'Product Health', score: 82 },
      { name: 'Financial Health', score: 79 },
    ];

    return (
      <Grid container spacing={3}>
        {healthScores.map((health, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <HealthScore score={health.score}>
                {health.score}
              </HealthScore>
              <Typography variant="h6" sx={{ mt: 2 }}>
                {health.name}
              </Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>
    );
  };

  return (
    <Box>
      <Card sx={{ mb: 3, background: 'linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%)' }}>
        <CardContent>
          <Typography variant="h4" gutterBottom sx={{ color: 'white' }}>
            <PieChartIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Business Intelligence
          </Typography>
          <Typography variant="body1" sx={{ color: 'white' }}>
            Track KPIs, predict revenue, analyze churn, and calculate ROI with advanced analytics
          </Typography>
        </CardContent>
      </Card>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {isLoading && !metrics ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          {renderKPICards()}

          <Box sx={{ mt: 3 }}>
            <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
              <Tab label="Executive Overview" icon={<AssessmentIcon />} />
              <Tab label="Revenue Forecast" icon={<ShowChartIcon />} />
              <Tab label="Churn Analysis" icon={<WarningIcon />} />
              <Tab label="ROI Calculator" icon={<CalculateIcon />} />
              <Tab label="Opportunities" icon={<LightbulbIcon />} />
            </Tabs>

            {tabValue === 0 && (
              <Box sx={{ mt: 3 }}>
                {renderHealthScores()}
                
                <Grid container spacing={3} sx={{ mt: 2 }}>
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Revenue Trend
                        </Typography>
                        <ResponsiveContainer width="100%" height={300}>
                          <LineChart
                            data={[
                              { month: 'Jan', revenue: 95000 },
                              { month: 'Feb', revenue: 98000 },
                              { month: 'Mar', revenue: 105000 },
                              { month: 'Apr', revenue: 112000 },
                              { month: 'May', revenue: 118000 },
                              { month: 'Jun', revenue: 125000 },
                            ]}
                          >
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="month" />
                            <YAxis />
                            <ChartTooltip />
                            <Line type="monotone" dataKey="revenue" stroke="#3a7bd5" strokeWidth={2} />
                          </LineChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          User Segments
                        </Typography>
                        <ResponsiveContainer width="100%" height={300}>
                          <PieChart>
                            <Pie
                              data={[
                                { name: 'Power Users', value: 150, color: '#4caf50' },
                                { name: 'Regular', value: 450, color: '#2196f3' },
                                { name: 'Occasional', value: 300, color: '#ff9800' },
                                { name: 'At Risk', value: 200, color: '#f44336' },
                              ]}
                              cx="50%"
                              cy="50%"
                              labelLine={false}
                              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                              outerRadius={80}
                              fill="#8884d8"
                              dataKey="value"
                            >
                              {[
                                { color: '#4caf50' },
                                { color: '#2196f3' },
                                { color: '#ff9800' },
                                { color: '#f44336' },
                              ].map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} />
                              ))}
                            </Pie>
                            <ChartTooltip />
                          </PieChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </Box>
            )}

            {tabValue === 1 && (
              <Box sx={{ mt: 3 }}>
                <Card>
                  <CardContent>
                    <Box sx={{ mb: 3 }}>
                      <Grid container spacing={2} alignItems="center">
                        <Grid item xs={12} md={3}>
                          <FormControl fullWidth>
                            <InputLabel>Scenario</InputLabel>
                            <Select
                              value={scenario}
                              onChange={(e) => setScenario(e.target.value as any)}
                              label="Scenario"
                            >
                              <MenuItem value="most_likely">Most Likely</MenuItem>
                              <MenuItem value="best_case">Best Case</MenuItem>
                              <MenuItem value="worst_case">Worst Case</MenuItem>
                            </Select>
                          </FormControl>
                        </Grid>
                        <Grid item xs={12} md={3}>
                          <Typography gutterBottom>Forecast Months: {forecastMonths}</Typography>
                          <Slider
                            value={forecastMonths}
                            onChange={(e, v) => setForecastMonths(v as number)}
                            min={3}
                            max={24}
                            marks
                            step={3}
                          />
                        </Grid>
                        <Grid item xs={12} md={3}>
                          <FormControlLabel
                            control={
                              <Switch
                                checked={includeSeasonality}
                                onChange={(e) => setIncludeSeasonality(e.target.checked)}
                              />
                            }
                            label="Include Seasonality"
                          />
                        </Grid>
                        <Grid item xs={12} md={3}>
                          <Button
                            fullWidth
                            variant="contained"
                            onClick={generateForecast}
                            disabled={isLoading}
                            startIcon={isLoading ? <CircularProgress size={20} /> : <ShowChartIcon />}
                          >
                            Generate Forecast
                          </Button>
                        </Grid>
                      </Grid>
                    </Box>
                    {forecast.length > 0 && renderRevenueChart()}
                  </CardContent>
                </Card>
              </Box>
            )}

            {tabValue === 2 && (
              <Box sx={{ mt: 3 }}>
                <Card>
                  <CardContent>
                    <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="h6">Churn Risk Analysis</Typography>
                      <Button
                        variant="contained"
                        onClick={predictChurn}
                        disabled={isLoading}
                        startIcon={isLoading ? <CircularProgress size={20} /> : <WarningIcon />}
                      >
                        Analyze Churn Risk
                      </Button>
                    </Box>
                    {churnPredictions.length > 0 && renderChurnTable()}
                  </CardContent>
                </Card>
              </Box>
            )}

            {tabValue === 3 && (
              <Box sx={{ mt: 3 }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
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
                          defaultValue={50000}
                          margin="normal"
                        />
                        <TextField
                          fullWidth
                          label="Operational Costs"
                          type="number"
                          defaultValue={30000}
                          margin="normal"
                        />
                        <TextField
                          fullWidth
                          label="Marketing Spend"
                          type="number"
                          defaultValue={20000}
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
                          defaultValue={150000}
                          margin="normal"
                        />
                        <TextField
                          fullWidth
                          label="Transaction Revenue"
                          type="number"
                          defaultValue={30000}
                          margin="normal"
                        />
                        <TextField
                          fullWidth
                          label="Add-on Revenue"
                          type="number"
                          defaultValue={10000}
                          margin="normal"
                        />
                      </Grid>
                    </Grid>
                    <Box sx={{ mt: 3 }}>
                      <Button variant="contained" size="large" startIcon={<CalculateIcon />}>
                        Calculate ROI
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </Box>
            )}

            {tabValue === 4 && (
              <Box sx={{ mt: 3 }}>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
                      <CardContent sx={{ color: 'white' }}>
                        <Typography variant="h6" gutterBottom>
                          Upsell Opportunities
                        </Typography>
                        <Typography variant="h3">23 users</Typography>
                        <Typography variant="body1">
                          Ready for plan upgrade
                        </Typography>
                        <Typography variant="h5" sx={{ mt: 2 }}>
                          $12,500/month potential
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Card sx={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
                      <CardContent sx={{ color: 'white' }}>
                        <Typography variant="h6" gutterBottom>
                          Win-Back Campaign
                        </Typography>
                        <Typography variant="h3">45 users</Typography>
                        <Typography variant="body1">
                          High win-back potential
                        </Typography>
                        <Typography variant="h5" sx={{ mt: 2 }}>
                          $8,200/month recovery
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </Box>
            )}
          </Box>
        </>
      )}

      <SpeedDial
        ariaLabel="Business Intelligence Actions"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        icon={<SpeedDialIcon />}
      >
        <SpeedDialAction
          icon={<DownloadIcon />}
          tooltipTitle="Export Report"
          onClick={() => console.log('Export')}
        />
        <SpeedDialAction
          icon={<RefreshIcon />}
          tooltipTitle="Refresh Data"
          onClick={loadMetrics}
        />
        <SpeedDialAction
          icon={<SettingsIcon />}
          tooltipTitle="Settings"
          onClick={() => console.log('Settings')}
        />
      </SpeedDial>
    </Box>
  );
};

export default BusinessIntelligence;