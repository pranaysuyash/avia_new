import React, { useState, useEffect } from 'react';
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
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Area,
  AreaChart,
  Treemap
} from 'recharts';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../ui/card';
import { Button } from '../ui/button';
import { Progress } from '../ui/progress';
import { Alert, AlertDescription } from '../ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Users,
  FileText,
  Clock,
  Target,
  Award,
  AlertCircle,
  Download,
  RefreshCw,
  Filter,
  Calendar,
  Brain,
  Zap,
  Globe,
  Shield,
  Database,
  Cpu
} from 'lucide-react';

interface AIAnalyticsDesktopProps {
  userId?: string;
  teamId?: string;
  dateRange?: { start: Date; end: Date };
}

interface AnalyticsData {
  transcriptionMetrics: {
    total: number;
    trend: number;
    accuracy: number;
    avgDuration: number;
    languages: { name: string; value: number }[];
  };
  usagePatterns: {
    hourly: { hour: string; usage: number }[];
    daily: { date: string; usage: number }[];
    weekly: { week: string; usage: number }[];
  };
  aiInsights: {
    topTopics: { topic: string; frequency: number; sentiment: number }[];
    sentimentTrends: { date: string; positive: number; negative: number; neutral: number }[];
    keyEntities: { entity: string; count: number; type: string }[];
  };
  performanceMetrics: {
    processingSpeed: number;
    errorRate: number;
    uptime: number;
    latency: { time: string; value: number }[];
  };
  predictions: {
    nextWeekUsage: number;
    peakHours: string[];
    recommendedActions: string[];
  };
  teamAnalytics?: {
    memberActivity: { member: string; transcriptions: number; accuracy: number }[];
    collaboration: { date: string; sessions: number }[];
    productivity: number;
  };
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

export const AIAnalyticsDesktop: React.FC<AIAnalyticsDesktopProps> = ({
  userId,
  teamId,
  dateRange
}) => {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedMetric, setSelectedMetric] = useState('transcription');
  const [refreshing, setRefreshing] = useState(false);
  const [exportFormat, setExportFormat] = useState<'pdf' | 'csv' | 'json'>('pdf');

  useEffect(() => {
    fetchAnalytics();
  }, [userId, teamId, dateRange]);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (userId) params.append('user_id', userId);
      if (teamId) params.append('team_id', teamId);
      if (dateRange) {
        params.append('start_date', dateRange.start.toISOString());
        params.append('end_date', dateRange.end.toISOString());
      }

      const response = await fetch(`/api/ai-analytics?${params}`);
      const data = await response.json();
      setAnalyticsData(data);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchAnalytics();
    setRefreshing(false);
  };

  const handleExport = async () => {
    try {
      const response = await fetch('/api/ai-analytics/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          format: exportFormat,
          data: analyticsData,
          userId,
          teamId,
          dateRange
        })
      });

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ai-analytics-${new Date().toISOString()}.${exportFormat}`;
      a.click();
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <Cpu className="w-12 h-12 animate-spin mx-auto mb-4 text-blue-500" />
          <p className="text-gray-600">Loading AI Analytics...</p>
        </div>
      </div>
    );
  }

  if (!analyticsData) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          No analytics data available. Start using the platform to see insights.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Brain className="w-8 h-8 text-blue-500" />
            AI Analytics Dashboard
          </h1>
          <p className="text-gray-600 mt-1">
            Intelligent insights powered by machine learning
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={handleExport}>
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Transcriptions
            </CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {analyticsData.transcriptionMetrics.total.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground flex items-center">
              {analyticsData.transcriptionMetrics.trend > 0 ? (
                <TrendingUp className="w-3 h-3 mr-1 text-green-500" />
              ) : (
                <TrendingDown className="w-3 h-3 mr-1 text-red-500" />
              )}
              {Math.abs(analyticsData.transcriptionMetrics.trend)}% from last period
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Accuracy Rate
            </CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {analyticsData.transcriptionMetrics.accuracy}%
            </div>
            <Progress value={analyticsData.transcriptionMetrics.accuracy} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Processing Speed
            </CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {analyticsData.performanceMetrics.processingSpeed}x
            </div>
            <p className="text-xs text-muted-foreground">
              Faster than real-time
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              System Uptime
            </CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {analyticsData.performanceMetrics.uptime}%
            </div>
            <p className="text-xs text-muted-foreground">
              99.9% SLA maintained
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Analytics Tabs */}
      <Tabs defaultValue="usage" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="usage">Usage Patterns</TabsTrigger>
          <TabsTrigger value="insights">AI Insights</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="predictions">Predictions</TabsTrigger>
          {teamId && <TabsTrigger value="team">Team Analytics</TabsTrigger>}
        </TabsList>

        <TabsContent value="usage" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Usage Patterns Over Time</CardTitle>
              <CardDescription>
                Analyze transcription usage trends across different time periods
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={analyticsData.usagePatterns.daily}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Area
                    type="monotone"
                    dataKey="usage"
                    stroke="#8884d8"
                    fill="#8884d8"
                    fillOpacity={0.6}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Hourly Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={analyticsData.usagePatterns.hourly}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="hour" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="usage" fill="#00C49F" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Language Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={analyticsData.transcriptionMetrics.languages}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {analyticsData.transcriptionMetrics.languages.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="insights" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Sentiment Analysis Trends</CardTitle>
              <CardDescription>
                Track sentiment patterns across your transcriptions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={analyticsData.aiInsights.sentimentTrends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="positive"
                    stackId="1"
                    stroke="#00C49F"
                    fill="#00C49F"
                  />
                  <Area
                    type="monotone"
                    dataKey="neutral"
                    stackId="1"
                    stroke="#FFBB28"
                    fill="#FFBB28"
                  />
                  <Area
                    type="monotone"
                    dataKey="negative"
                    stackId="1"
                    stroke="#FF8042"
                    fill="#FF8042"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Top Topics</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <RadarChart data={analyticsData.aiInsights.topTopics}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="topic" />
                    <PolarRadiusAxis />
                    <Radar
                      name="Frequency"
                      dataKey="frequency"
                      stroke="#8884d8"
                      fill="#8884d8"
                      fillOpacity={0.6}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Key Entities</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <Treemap
                    data={analyticsData.aiInsights.keyEntities}
                    dataKey="count"
                    aspectRatio={4 / 3}
                    stroke="#fff"
                    fill="#8884d8"
                  />
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>System Performance Metrics</CardTitle>
              <CardDescription>
                Real-time monitoring of system health and performance
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={analyticsData.performanceMetrics.latency}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#8884d8"
                    name="Latency (ms)"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Error Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {analyticsData.performanceMetrics.errorRate}%
                </div>
                <Progress
                  value={100 - analyticsData.performanceMetrics.errorRate}
                  className="mt-2"
                />
                <p className="text-xs text-muted-foreground mt-2">
                  Below industry average
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Processing Queue</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">12</div>
                <p className="text-xs text-muted-foreground mt-2">
                  Items in queue
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>API Response Time</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">45ms</div>
                <p className="text-xs text-muted-foreground mt-2">
                  Average response time
                </p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="predictions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>AI-Powered Predictions</CardTitle>
              <CardDescription>
                Machine learning insights to optimize your workflow
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <h3 className="font-semibold mb-2">Next Week Usage Forecast</h3>
                <p className="text-2xl font-bold">
                  {analyticsData.predictions.nextWeekUsage.toLocaleString()} transcriptions
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  Based on historical patterns and current trends
                </p>
              </div>

              <div className="p-4 bg-green-50 rounded-lg">
                <h3 className="font-semibold mb-2">Peak Usage Hours</h3>
                <div className="flex flex-wrap gap-2 mt-2">
                  {analyticsData.predictions.peakHours.map((hour, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-green-200 text-green-800 rounded-full text-sm"
                    >
                      {hour}
                    </span>
                  ))}
                </div>
              </div>

              <div className="p-4 bg-purple-50 rounded-lg">
                <h3 className="font-semibold mb-2">Recommended Actions</h3>
                <ul className="space-y-2">
                  {analyticsData.predictions.recommendedActions.map((action, index) => (
                    <li key={index} className="flex items-start">
                      <Award className="w-4 h-4 text-purple-600 mr-2 mt-0.5" />
                      <span className="text-sm">{action}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {teamId && analyticsData.teamAnalytics && (
          <TabsContent value="team" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Team Performance</CardTitle>
                <CardDescription>
                  Track team collaboration and productivity metrics
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={analyticsData.teamAnalytics.memberActivity}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="member" />
                    <YAxis yAxisId="left" orientation="left" stroke="#8884d8" />
                    <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" />
                    <Tooltip />
                    <Legend />
                    <Bar yAxisId="left" dataKey="transcriptions" fill="#8884d8" />
                    <Bar yAxisId="right" dataKey="accuracy" fill="#82ca9d" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Collaboration Sessions</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={analyticsData.teamAnalytics.collaboration}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Line
                        type="monotone"
                        dataKey="sessions"
                        stroke="#8884d8"
                        strokeWidth={2}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Team Productivity Score</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-center h-[150px]">
                    <div className="text-center">
                      <div className="text-4xl font-bold text-green-600">
                        {analyticsData.teamAnalytics.productivity}%
                      </div>
                      <p className="text-sm text-gray-600 mt-2">
                        Above average performance
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        )}
      </Tabs>

      {/* Export Options */}
      <Card>
        <CardHeader>
          <CardTitle>Export Options</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <select
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value as 'pdf' | 'csv' | 'json')}
              className="px-3 py-2 border rounded-md"
            >
              <option value="pdf">PDF Report</option>
              <option value="csv">CSV Data</option>
              <option value="json">JSON Format</option>
            </select>
            <Button onClick={handleExport}>
              <Download className="w-4 h-4 mr-2" />
              Export Analytics
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AIAnalyticsDesktop;