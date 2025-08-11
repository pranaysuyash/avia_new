import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Progress } from '../ui/progress';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  LineChart,
  Line,
} from 'recharts';
import {
  Activity,
  Database,
  Zap,
  Users,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  TrendingUp,
  HardDrive,
} from 'lucide-react';

interface CacheStats {
  connected: boolean;
  uptime_seconds: number;
  memory: {
    used_bytes: number;
    used_human: string;
    peak_bytes: number;
    peak_human: string;
    rss_bytes: number;
    fragmentation_ratio: number;
  };
  stats: {
    total_requests: number;
    hits: number;
    misses: number;
    hit_rate: number;
    evicted_keys: number;
    expired_keys: number;
    ops_per_sec: number;
  };
  clients: {
    connected: number;
    blocked: number;
    max_clients: number;
  };
  keyspace: {
    total_keys: number;
    databases: Record<string, {
      count: number;
      sample_keys: string[];
    }>;
  };
}

interface CacheMetricsProps {
  className?: string;
}

export const CacheMetrics: React.FC<CacheMetricsProps> = ({ className }) => {
  const [stats, setStats] = useState<CacheStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchCacheStats = async () => {
    try {
      const response = await fetch('/api/v1/transcription/cached/cache-stats');
      if (!response.ok) {
        throw new Error('Failed to fetch cache stats');
      }
      const data = await response.json();
      setStats(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setStats(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCacheStats();
  }, []);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchCacheStats, 5000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const formatBytes = (bytes: number) => {
    const sizes = ['B', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Cache Metrics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center p-8">
            <RefreshCw className="h-6 w-6 animate-spin" />
            <span className="ml-2">Loading cache metrics...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || !stats) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Cache Metrics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-red-500">
            <AlertCircle className="h-5 w-5" />
            <span>Error: {error || 'Failed to load cache stats'}</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Prepare charts data
  const keyDistributionData = Object.entries(stats.keyspace.databases)
    .filter(([, data]) => data.count > 0)
    .map(([name, data]) => ({
      name: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      value: data.count,
      count: data.count,
    }));

  const memoryData = [
    {
      name: 'Used',
      value: Math.round(stats.memory.used_bytes / (1024 * 1024)),
      color: '#3B82F6',
    },
    {
      name: 'Peak',
      value: Math.round(stats.memory.peak_bytes / (1024 * 1024)),
      color: '#F59E0B',
    },
    {
      name: 'RSS',
      value: Math.round(stats.memory.rss_bytes / (1024 * 1024)),
      color: '#10B981',
    },
  ];

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#84CC16'];

  return (
    <div className={className}>
      {/* Header */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                Redis Cache Metrics
              </CardTitle>
              <CardDescription>
                Real-time cache performance monitoring
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={autoRefresh ? 'bg-green-50' : ''}
              >
                <Activity className="h-4 w-4 mr-2" />
                {autoRefresh ? 'Auto-refreshing' : 'Auto-refresh'}
              </Button>
              <Button variant="outline" size="sm" onClick={fetchCacheStats}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
            <span className="text-green-600 font-medium">Connected</span>
            <Badge variant="outline">
              Uptime: {formatUptime(stats.uptime_seconds)}
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Keys</p>
                <p className="text-2xl font-bold">{stats.keyspace.total_keys.toLocaleString()}</p>
                <p className="text-xs text-muted-foreground">
                  {stats.stats.evicted_keys} evicted
                </p>
              </div>
              <Database className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Hit Rate</p>
                <p className="text-2xl font-bold">{stats.stats.hit_rate.toFixed(1)}%</p>
                <p className="text-xs text-muted-foreground">
                  {stats.stats.hits.toLocaleString()} hits
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-muted-foreground" />
            </div>
            <Progress value={stats.stats.hit_rate} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Memory Used</p>
                <p className="text-2xl font-bold">{stats.memory.used_human}</p>
                <p className="text-xs text-muted-foreground">
                  Peak: {stats.memory.peak_human}
                </p>
              </div>
              <HardDrive className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Operations/sec</p>
                <p className="text-2xl font-bold">{stats.stats.ops_per_sec}</p>
                <p className="text-xs text-muted-foreground">
                  {stats.clients.connected} clients
                </p>
              </div>
              <Zap className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Memory Usage Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Memory Usage</CardTitle>
            <CardDescription>Memory consumption breakdown</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={memoryData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(value) => [`${value} MB`, 'Memory']} />
                <Bar dataKey="value" fill="#3B82F6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Key Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Key Distribution</CardTitle>
            <CardDescription>Cache keys by category</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={keyDistributionData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={120}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {keyDistributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value, name) => [`${value} keys`, name]} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Performance Stats</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Total Requests</span>
              <span className="font-medium">{stats.stats.total_requests.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Cache Hits</span>
              <span className="font-medium text-green-600">{stats.stats.hits.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Cache Misses</span>
              <span className="font-medium text-red-600">{stats.stats.misses.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Hit Rate</span>
              <span className="font-medium">{stats.stats.hit_rate.toFixed(2)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Evicted Keys</span>
              <span className="font-medium">{stats.stats.evicted_keys.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Expired Keys</span>
              <span className="font-medium">{stats.stats.expired_keys.toLocaleString()}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>System Info</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Connected Clients</span>
              <span className="font-medium">{stats.clients.connected}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Blocked Clients</span>
              <span className="font-medium">{stats.clients.blocked}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Max Clients</span>
              <span className="font-medium">{stats.clients.max_clients.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Memory Fragmentation</span>
              <span className="font-medium">{stats.memory.fragmentation_ratio.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">RSS Memory</span>
              <span className="font-medium">{formatBytes(stats.memory.rss_bytes)}</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default CacheMetrics;