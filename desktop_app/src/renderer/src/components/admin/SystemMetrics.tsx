import React, { useState, useEffect } from 'react';
import {
  Activity,
  Cpu,
  HardDrive,
  MemoryStick,
  Network,
  Server,
  Thermometer,
  Clock,
  TrendingUp,
  TrendingDown,
  AlertTriangle
} from 'lucide-react';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface Metric {
  name: string;
  value: number;
  unit: string;
  status: 'normal' | 'warning' | 'critical';
  trend: 'up' | 'down' | 'stable';
}

export const SystemMetrics: React.FC = () => {
  const [metrics, setMetrics] = useState<Metric[]>([
    { name: 'CPU Usage', value: 45, unit: '%', status: 'normal', trend: 'stable' },
    { name: 'Memory Usage', value: 72, unit: '%', status: 'warning', trend: 'up' },
    { name: 'Disk Usage', value: 65, unit: '%', status: 'normal', trend: 'up' },
    { name: 'Network I/O', value: 125, unit: 'MB/s', status: 'normal', trend: 'down' },
    { name: 'Temperature', value: 68, unit: '°C', status: 'normal', trend: 'stable' },
    { name: 'Active Connections', value: 234, unit: '', status: 'normal', trend: 'up' }
  ]);

  const [timeRange, setTimeRange] = useState('1h');

  // Simulated real-time data
  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(prev => prev.map(metric => ({
        ...metric,
        value: metric.value + (Math.random() - 0.5) * 10,
        trend: Math.random() > 0.5 ? 'up' : Math.random() > 0.5 ? 'down' : 'stable'
      })));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const cpuChartData = {
    labels: Array.from({ length: 20 }, (_, i) => `${20 - i}m`),
    datasets: [
      {
        label: 'CPU Usage',
        data: Array.from({ length: 20 }, () => Math.random() * 100),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4
      }
    ]
  };

  const memoryChartData = {
    labels: ['Used', 'Cached', 'Free'],
    datasets: [
      {
        label: 'Memory Distribution',
        data: [72, 15, 13],
        backgroundColor: [
          'rgba(239, 68, 68, 0.8)',
          'rgba(251, 191, 36, 0.8)',
          'rgba(34, 197, 94, 0.8)'
        ]
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      }
    },
    scales: {
      x: {
        grid: {
          color: 'rgba(255, 255, 255, 0.1)'
        },
        ticks: {
          color: 'rgba(255, 255, 255, 0.6)'
        }
      },
      y: {
        grid: {
          color: 'rgba(255, 255, 255, 0.1)'
        },
        ticks: {
          color: 'rgba(255, 255, 255, 0.6)'
        }
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'normal':
        return 'text-green-500';
      case 'warning':
        return 'text-yellow-500';
      case 'critical':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  const getMetricIcon = (name: string) => {
    switch (name) {
      case 'CPU Usage':
        return Cpu;
      case 'Memory Usage':
        return MemoryStick;
      case 'Disk Usage':
        return HardDrive;
      case 'Network I/O':
        return Network;
      case 'Temperature':
        return Thermometer;
      case 'Active Connections':
        return Server;
      default:
        return Activity;
    }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-semibold">System Metrics</h2>
        <div className="flex items-center gap-4">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-2 bg-gray-800 border border-gray-700 rounded focus:outline-none focus:border-blue-500"
          >
            <option value="5m">Last 5 minutes</option>
            <option value="1h">Last hour</option>
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
          </select>
          <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
            Export Report
          </button>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        {metrics.map((metric) => {
          const Icon = getMetricIcon(metric.name);
          return (
            <div key={metric.name} className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-gray-700 rounded">
                    <Icon className="w-5 h-5 text-gray-400" />
                  </div>
                  <div>
                    <div className="text-sm text-gray-400">{metric.name}</div>
                    <div className="text-2xl font-bold">
                      {metric.value.toFixed(0)}{metric.unit}
                    </div>
                  </div>
                </div>
                <div className="flex flex-col items-end">
                  <span className={`text-sm font-medium ${getStatusColor(metric.status)}`}>
                    {metric.status.toUpperCase()}
                  </span>
                  {metric.trend === 'up' && <TrendingUp className="w-4 h-4 text-green-500 mt-1" />}
                  {metric.trend === 'down' && <TrendingDown className="w-4 h-4 text-red-500 mt-1" />}
                </div>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    metric.status === 'critical' ? 'bg-red-500' :
                    metric.status === 'warning' ? 'bg-yellow-500' :
                    'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(metric.value, 100)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2 gap-6 mb-8">
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">CPU Usage Over Time</h3>
          <div className="h-64">
            <Line data={cpuChartData} options={chartOptions} />
          </div>
        </div>
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Memory Distribution</h3>
          <div className="h-64">
            <Bar data={memoryChartData} options={chartOptions} />
          </div>
        </div>
      </div>

      {/* Alerts */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-yellow-500" />
          Active Alerts
        </h3>
        <div className="space-y-3">
          <AlertItem
            severity="warning"
            message="Memory usage is above 70% threshold"
            time="Active for 15 minutes"
          />
          <AlertItem
            severity="info"
            message="Scheduled maintenance window in 2 hours"
            time="Reminder"
          />
        </div>
      </div>
    </div>
  );
};

interface AlertItemProps {
  severity: 'info' | 'warning' | 'error';
  message: string;
  time: string;
}

const AlertItem: React.FC<AlertItemProps> = ({ severity, message, time }) => {
  const getSeverityColor = () => {
    switch (severity) {
      case 'info':
        return 'bg-blue-900/50 border-blue-700 text-blue-400';
      case 'warning':
        return 'bg-yellow-900/50 border-yellow-700 text-yellow-400';
      case 'error':
        return 'bg-red-900/50 border-red-700 text-red-400';
    }
  };

  return (
    <div className={`p-3 rounded border ${getSeverityColor()}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="font-medium">{message}</p>
          <p className="text-xs mt-1 opacity-75">{time}</p>
        </div>
        <button className="text-xs hover:underline">Dismiss</button>
      </div>
    </div>
  );
};

export default SystemMetrics;