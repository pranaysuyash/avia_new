import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ChartBarIcon,
  ServerIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ClockIcon,
  UsersIcon,
  DocumentTextIcon,
  CpuChipIcon,
  CircleStackIcon,
  SignalIcon
} from '@heroicons/react/24/outline';
import { Line, Pie, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface SystemMetric {
  name: string;
  value: number;
  unit: string;
  status: 'healthy' | 'warning' | 'critical';
  trend: number[];
}

interface ServiceHealth {
  name: string;
  status: 'online' | 'degraded' | 'offline';
  responseTime: number;
  uptime: number;
}

interface Alert {
  id: string;
  type: 'critical' | 'warning' | 'info';
  category: string;
  message: string;
  timestamp: string;
}

const AdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [refreshInterval, setRefreshInterval] = useState(5);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [selectedTimeRange, setSelectedTimeRange] = useState('1h');
  const [activeTab, setActiveTab] = useState<'overview' | 'health' | 'analytics' | 'alerts'>('overview');
  
  // Mock data - in production, these would come from API
  const [metrics, setMetrics] = useState({
    activeUsers: 42,
    transcriptionsToday: 256,
    apiCalls: 5234,
    systemLoad: 0.65
  });

  const [systemMetrics, setSystemMetrics] = useState<SystemMetric[]>([
    { name: 'CPU Usage', value: 45, unit: '%', status: 'healthy', trend: [40, 42, 45, 43, 45] },
    { name: 'Memory Usage', value: 72, unit: '%', status: 'warning', trend: [65, 68, 70, 71, 72] },
    { name: 'Disk Usage', value: 35, unit: '%', status: 'healthy', trend: [34, 34, 35, 35, 35] },
    { name: 'Network I/O', value: 23, unit: 'Mbps', status: 'healthy', trend: [20, 25, 22, 24, 23] }
  ]);

  const [services, setServices] = useState<ServiceHealth[]>([
    { name: 'API Gateway', status: 'online', responseTime: 12, uptime: 99.9 },
    { name: 'Transcription Service', status: 'online', responseTime: 145, uptime: 99.7 },
    { name: 'NER Engine', status: 'online', responseTime: 23, uptime: 99.8 },
    { name: 'Database', status: 'degraded', responseTime: 89, uptime: 98.5 },
    { name: 'Cache', status: 'online', responseTime: 2, uptime: 99.99 },
    { name: 'Queue Worker', status: 'online', responseTime: 0, uptime: 99.6 }
  ]);

  const [alerts, setAlerts] = useState<Alert[]>([
    { id: '1', type: 'critical', category: 'System', message: 'High memory usage detected (>90%)', timestamp: '2 min ago' },
    { id: '2', type: 'warning', category: 'API', message: 'API rate limit approaching threshold', timestamp: '15 min ago' },
    { id: '3', type: 'warning', category: 'Performance', message: 'Slow query detected', timestamp: '1 hour ago' }
  ]);

  // Auto-refresh effect
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      // Simulate data refresh
      setMetrics(prev => ({
        ...prev,
        activeUsers: prev.activeUsers + Math.floor(Math.random() * 5 - 2),
        transcriptionsToday: prev.transcriptionsToday + Math.floor(Math.random() * 3),
        apiCalls: prev.apiCalls + Math.floor(Math.random() * 10),
        systemLoad: Math.min(1, Math.max(0, prev.systemLoad + (Math.random() - 0.5) * 0.1))
      }));

      // Update system metrics
      setSystemMetrics(prev => prev.map(metric => ({
        ...metric,
        value: Math.min(100, Math.max(0, metric.value + (Math.random() - 0.5) * 5)),
        trend: [...metric.trend.slice(1), metric.value]
      })));
    }, refreshInterval * 1000);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);

  const renderMetricCard = (title: string, value: string | number, delta: string, deltaType: 'positive' | 'negative' | 'neutral', icon: React.ReactNode) => (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <div className="p-2 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
          {icon}
        </div>
        <span className={`text-sm flex items-center ${
          deltaType === 'positive' ? 'text-green-600' : 
          deltaType === 'negative' ? 'text-red-600' : 
          'text-gray-600'
        }`}>
          {deltaType === 'positive' && <ArrowTrendingUpIcon className="h-4 w-4 mr-1" />}
          {deltaType === 'negative' && <ArrowTrendingDownIcon className="h-4 w-4 mr-1" />}
          {delta}
        </span>
      </div>
      <h3 className="text-2xl font-bold text-gray-900 dark:text-white">{value}</h3>
      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{title}</p>
    </div>
  );

  const renderServiceStatus = (service: ServiceHealth) => {
    const statusColors = {
      online: 'bg-green-500',
      degraded: 'bg-yellow-500',
      offline: 'bg-red-500'
    };

    return (
      <div key={service.name} className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-medium text-gray-900 dark:text-white">{service.name}</h4>
          <div className={`w-3 h-3 rounded-full ${statusColors[service.status]}`} />
        </div>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <span className="text-gray-500 dark:text-gray-400">Response:</span>
            <span className="ml-1 text-gray-900 dark:text-white">{service.responseTime}ms</span>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">Uptime:</span>
            <span className="ml-1 text-gray-900 dark:text-white">{service.uptime}%</span>
          </div>
        </div>
      </div>
    );
  };

  const renderSystemMetric = (metric: SystemMetric) => {
    const statusColors = {
      healthy: 'text-green-600',
      warning: 'text-yellow-600',
      critical: 'text-red-600'
    };

    // Mini sparkline chart
    const sparklineData = {
      labels: metric.trend.map((_, i) => i),
      datasets: [{
        data: metric.trend,
        borderColor: metric.status === 'healthy' ? '#10b981' : metric.status === 'warning' ? '#f59e0b' : '#ef4444',
        borderWidth: 2,
        pointRadius: 0,
        fill: false,
        tension: 0.4
      }]
    };

    const sparklineOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { enabled: false }
      },
      scales: {
        x: { display: false },
        y: { display: false }
      }
    };

    return (
      <div key={metric.name} className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-medium text-gray-900 dark:text-white">{metric.name}</h4>
          <span className={`text-2xl font-bold ${statusColors[metric.status]}`}>
            {metric.value}{metric.unit}
          </span>
        </div>
        <div className="h-12">
          <Line data={sparklineData} options={sparklineOptions} />
        </div>
      </div>
    );
  };

  const renderAlert = (alert: Alert) => {
    const typeStyles = {
      critical: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800',
      warning: 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800',
      info: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800'
    };

    const typeIcons = {
      critical: <ExclamationTriangleIcon className="h-5 w-5 text-red-600" />,
      warning: <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600" />,
      info: <ExclamationTriangleIcon className="h-5 w-5 text-blue-600" />
    };

    return (
      <div key={alert.id} className={`rounded-lg p-4 border ${typeStyles[alert.type]}`}>
        <div className="flex items-start">
          <div className="flex-shrink-0">
            {typeIcons[alert.type]}
          </div>
          <div className="ml-3 flex-1">
            <p className="text-sm font-medium text-gray-900 dark:text-white">
              {alert.message}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {alert.category} • {alert.timestamp}
            </p>
          </div>
          <button
            onClick={() => setAlerts(alerts.filter(a => a.id !== alert.id))}
            className="ml-3 text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Admin Dashboard</h1>
            
            <div className="flex items-center space-x-4">
              {/* Time range selector */}
              <select
                value={selectedTimeRange}
                onChange={(e) => setSelectedTimeRange(e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="5m">Last 5 minutes</option>
                <option value="15m">Last 15 minutes</option>
                <option value="1h">Last 1 hour</option>
                <option value="6h">Last 6 hours</option>
                <option value="24h">Last 24 hours</option>
              </select>

              {/* Refresh controls */}
              <div className="flex items-center space-x-2">
                <label className="text-sm text-gray-600 dark:text-gray-400">
                  Refresh: {refreshInterval}s
                </label>
                <input
                  type="range"
                  min="1"
                  max="60"
                  value={refreshInterval}
                  onChange={(e) => setRefreshInterval(parseInt(e.target.value))}
                  className="w-24"
                />
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={autoRefresh}
                    onChange={(e) => setAutoRefresh(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-600 dark:text-gray-400">Auto</span>
                </label>
              </div>

              <span className="text-sm text-gray-500 dark:text-gray-400 flex items-center">
                <ClockIcon className="h-4 w-4 mr-1" />
                Last updated: {new Date().toLocaleTimeString()}
              </span>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex space-x-6 mt-4">
            {(['overview', 'health', 'analytics', 'alerts'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`pb-2 px-1 border-b-2 transition-colors ${
                  activeTab === tab
                    ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                    : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Key metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {renderMetricCard(
                'Active Users',
                metrics.activeUsers,
                '+12%',
                'positive',
                <UsersIcon className="h-6 w-6 text-indigo-600" />
              )}
              {renderMetricCard(
                'Transcriptions Today',
                metrics.transcriptionsToday,
                '+28%',
                'positive',
                <DocumentTextIcon className="h-6 w-6 text-indigo-600" />
              )}
              {renderMetricCard(
                'API Calls',
                metrics.apiCalls.toLocaleString(),
                '-5%',
                'negative',
                <ServerIcon className="h-6 w-6 text-indigo-600" />
              )}
              {renderMetricCard(
                'System Load',
                `${(metrics.systemLoad * 100).toFixed(0)}%`,
                'Normal',
                'neutral',
                <CpuChipIcon className="h-6 w-6 text-indigo-600" />
              )}
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Transcription Activity
                </h3>
                <div className="h-64">
                  <Line
                    data={{
                      labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
                      datasets: [{
                        label: 'Transcriptions',
                        data: [12, 19, 35, 45, 52, 38],
                        borderColor: 'rgb(99, 102, 241)',
                        backgroundColor: 'rgba(99, 102, 241, 0.1)',
                        fill: true,
                        tension: 0.4
                      }]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { display: false }
                      }
                    }}
                  />
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Processing Distribution
                </h3>
                <div className="h-64">
                  <Pie
                    data={{
                      labels: ['Basic NER', 'Advanced NER', 'Speaker Diarization', 'WhisperX'],
                      datasets: [{
                        data: [45, 30, 20, 5],
                        backgroundColor: [
                          'rgba(99, 102, 241, 0.8)',
                          'rgba(34, 197, 94, 0.8)',
                          'rgba(251, 146, 60, 0.8)',
                          'rgba(147, 51, 234, 0.8)'
                        ]
                      }]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'health' && (
          <div className="space-y-6">
            {/* Overall health status */}
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  System Health Status
                </h3>
                <div className="flex items-center space-x-2">
                  <CheckCircleIcon className="h-6 w-6 text-green-500" />
                  <span className="text-green-600 font-medium">All Systems Operational</span>
                </div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                <div 
                  className="bg-green-500 h-4 rounded-full"
                  style={{ width: '92%' }}
                />
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                Overall Health Score: 92%
              </p>
            </div>

            {/* System metrics */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                System Metrics
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {systemMetrics.map(renderSystemMetric)}
              </div>
            </div>

            {/* Service status */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Service Status
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {services.map(renderServiceStatus)}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                User Analytics
              </h3>
              <div className="h-64">
                <Bar
                  data={{
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    datasets: [
                      {
                        label: 'New Users',
                        data: [12, 19, 15, 25, 22, 18, 14],
                        backgroundColor: 'rgba(99, 102, 241, 0.8)'
                      },
                      {
                        label: 'Active Users',
                        data: [65, 72, 68, 85, 79, 52, 48],
                        backgroundColor: 'rgba(34, 197, 94, 0.8)'
                      }
                    ]
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false
                  }}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  API Usage by Endpoint
                </h3>
                <div className="space-y-3">
                  {[
                    { endpoint: '/api/transcription', calls: 2345, percentage: 45 },
                    { endpoint: '/api/ner/extract', calls: 1567, percentage: 30 },
                    { endpoint: '/api/search', calls: 892, percentage: 17 },
                    { endpoint: '/api/export', calls: 456, percentage: 8 }
                  ].map((item, index) => (
                    <div key={index}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-600 dark:text-gray-400">{item.endpoint}</span>
                        <span className="text-gray-900 dark:text-white">{item.calls} calls</span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div 
                          className="bg-indigo-500 h-2 rounded-full"
                          style={{ width: `${item.percentage}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Processing Time Distribution
                </h3>
                <div className="h-48">
                  <Bar
                    data={{
                      labels: ['<1s', '1-5s', '5-10s', '10-30s', '>30s'],
                      datasets: [{
                        label: 'Requests',
                        data: [456, 892, 1234, 567, 123],
                        backgroundColor: 'rgba(251, 146, 60, 0.8)'
                      }]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { display: false }
                      }
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'alerts' && (
          <div className="space-y-6">
            {/* Alert filters */}
            <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <select className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                    <option>All Severities</option>
                    <option>Critical</option>
                    <option>Warning</option>
                    <option>Info</option>
                  </select>
                  <select className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                    <option>All Categories</option>
                    <option>System</option>
                    <option>API</option>
                    <option>Performance</option>
                    <option>Security</option>
                  </select>
                </div>
                <button className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors">
                  Clear Resolved
                </button>
              </div>
            </div>

            {/* Active alerts */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Active Alerts ({alerts.length})
              </h3>
              <div className="space-y-3">
                {alerts.map(renderAlert)}
              </div>
            </div>

            {/* Alert history */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Alert History
              </h3>
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
                <table className="min-w-full">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Time
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Severity
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Category
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Message
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {[
                      { time: '10:30 AM', severity: 'Warning', category: 'API', message: 'High latency detected', status: 'Resolved' },
                      { time: '09:45 AM', severity: 'Critical', category: 'System', message: 'Database connection lost', status: 'Resolved' },
                      { time: '08:15 AM', severity: 'Info', category: 'Performance', message: 'Cache cleared successfully', status: 'Acknowledged' }
                    ].map((item, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                          {item.time}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            item.severity === 'Critical' ? 'bg-red-100 text-red-800' :
                            item.severity === 'Warning' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-blue-100 text-blue-800'
                          }`}>
                            {item.severity}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                          {item.category}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">
                          {item.message}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                          {item.status}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;