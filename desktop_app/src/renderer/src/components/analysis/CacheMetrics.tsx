import React, { useState, useEffect, useCallback } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js'
import { Bar, Pie } from 'react-chartjs-2'
import { 
  Activity, 
  Database, 
  Zap, 
  Users, 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle,
  TrendingUp,
  HardDrive,
  Settings
} from 'lucide-react'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
)

interface CacheStats {
  connected: boolean
  uptime_seconds: number
  memory: {
    used_bytes: number
    used_human: string
    peak_bytes: number
    peak_human: string
    rss_bytes: number
    fragmentation_ratio: number
  }
  stats: {
    total_requests: number
    hits: number
    misses: number
    hit_rate: number
    evicted_keys: number
    expired_keys: number
    ops_per_sec: number
  }
  clients: {
    connected: number
    blocked: number
    max_clients: number
  }
  keyspace: {
    total_keys: number
    databases: Record<string, {
      count: number
      sample_keys: string[]
    }>
  }
}

interface CacheMetricsProps {
  className?: string
}

export const CacheMetrics: React.FC<CacheMetricsProps> = ({ className = '' }) => {
  const [stats, setStats] = useState<CacheStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null)

  const fetchCacheStats = useCallback(async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:8000/api/v1/transcription/cached/cache-stats', {
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        throw new Error(`Failed to fetch cache stats: ${response.status}`)
      }
      
      const data = await response.json()
      setStats(data)
      setError(null)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred'
      setError(errorMessage)
      setStats(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchCacheStats()
  }, [fetchCacheStats])

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchCacheStats, 5000)
      setRefreshInterval(interval)
      return () => {
        clearInterval(interval)
        setRefreshInterval(null)
      }
    } else if (refreshInterval) {
      clearInterval(refreshInterval)
      setRefreshInterval(null)
    }
  }, [autoRefresh, fetchCacheStats])

  const formatUptime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${hours}h ${minutes}m`
  }

  const formatBytes = (bytes: number): string => {
    const sizes = ['B', 'KB', 'MB', 'GB']
    if (bytes === 0) return '0 B'
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i]
  }

  const handleWarmCache = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/transcription/cached/warm-cache', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ transcript_ids: [] }),
      })
      
      if (!response.ok) throw new Error('Failed to warm cache')
      
      // Refresh stats after warming
      setTimeout(fetchCacheStats, 1000)
    } catch (err) {
      console.error('Cache warming failed:', err)
    }
  }

  const handleInvalidateCache = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/transcription/cached/invalidate-cache', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) throw new Error('Failed to invalidate cache')
      
      // Refresh stats after invalidation
      setTimeout(fetchCacheStats, 1000)
    } catch (err) {
      console.error('Cache invalidation failed:', err)
    }
  }

  if (loading) {
    return (
      <div className={`p-6 bg-white rounded-lg shadow-lg ${className}`}>
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center space-x-3">
            <RefreshCw className="h-6 w-6 animate-spin text-blue-500" />
            <span className="text-gray-600">Loading cache metrics...</span>
          </div>
        </div>
      </div>
    )
  }

  if (error || !stats) {
    return (
      <div className={`p-6 bg-white rounded-lg shadow-lg ${className}`}>
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center space-x-3 text-red-500">
            <AlertTriangle className="h-6 w-6" />
            <span>Error: {error || 'Failed to load cache stats'}</span>
          </div>
        </div>
      </div>
    )
  }

  // Prepare chart data
  const memoryChartData = {
    labels: ['Used', 'Peak', 'RSS'],
    datasets: [
      {
        label: 'Memory (MB)',
        data: [
          Math.round(stats.memory.used_bytes / (1024 * 1024)),
          Math.round(stats.memory.peak_bytes / (1024 * 1024)),
          Math.round(stats.memory.rss_bytes / (1024 * 1024)),
        ],
        backgroundColor: ['#3B82F6', '#F59E0B', '#10B981'],
        borderColor: ['#2563EB', '#D97706', '#059669'],
        borderWidth: 1,
      },
    ],
  }

  const keyDistributionData = Object.entries(stats.keyspace.databases)
    .filter(([, data]) => data.count > 0)
    .reduce((acc, [name, data]) => {
      acc.labels.push(name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()))
      acc.datasets[0].data.push(data.count)
      return acc
    }, {
      labels: [] as string[],
      datasets: [{
        data: [] as number[],
        backgroundColor: [
          '#3B82F6', '#10B981', '#F59E0B', '#EF4444', 
          '#8B5CF6', '#06B6D4', '#84CC16'
        ],
        borderWidth: 2,
      }]
    })

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
    },
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <Database className="h-6 w-6 text-blue-500" />
            <h2 className="text-xl font-semibold text-gray-900">Redis Cache Metrics</h2>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                autoRefresh 
                  ? 'bg-green-100 text-green-700 hover:bg-green-200' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Activity className="h-4 w-4 mr-2" />
              {autoRefresh ? 'Auto-refreshing' : 'Auto-refresh'}
            </button>
            <button
              onClick={fetchCacheStats}
              className="flex items-center px-3 py-2 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </button>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
            <span className="text-green-600 font-medium">Connected</span>
          </div>
          <div className="px-2 py-1 bg-gray-100 rounded text-sm">
            Uptime: {formatUptime(stats.uptime_seconds)}
          </div>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Keys</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats.keyspace.total_keys.toLocaleString()}
              </p>
              <p className="text-xs text-gray-500">
                {stats.stats.evicted_keys} evicted
              </p>
            </div>
            <Database className="h-8 w-8 text-gray-400" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Hit Rate</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats.stats.hit_rate.toFixed(1)}%
              </p>
              <p className="text-xs text-gray-500">
                {stats.stats.hits.toLocaleString()} hits
              </p>
            </div>
            <TrendingUp className="h-8 w-8 text-gray-400" />
          </div>
          <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full" 
              style={{ width: `${Math.min(stats.stats.hit_rate, 100)}%` }}
            ></div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Memory Used</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats.memory.used_human}
              </p>
              <p className="text-xs text-gray-500">
                Peak: {stats.memory.peak_human}
              </p>
            </div>
            <HardDrive className="h-8 w-8 text-gray-400" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Operations/sec</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats.stats.ops_per_sec}
              </p>
              <p className="text-xs text-gray-500">
                {stats.clients.connected} clients
              </p>
            </div>
            <Zap className="h-8 w-8 text-gray-400" />
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Memory Usage</h3>
          <div style={{ height: '300px' }}>
            <Bar data={memoryChartData} options={chartOptions} />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Key Distribution</h3>
          <div style={{ height: '300px' }}>
            {keyDistributionData.labels.length > 0 ? (
              <Pie data={keyDistributionData} options={chartOptions} />
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                No cache keys found
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Actions and Detailed Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Cache Actions</h3>
          <div className="space-y-3">
            <button
              onClick={handleWarmCache}
              className="w-full flex items-center justify-center px-4 py-2 bg-green-100 text-green-700 rounded-md hover:bg-green-200 transition-colors"
            >
              <Zap className="h-4 w-4 mr-2" />
              Warm Cache
            </button>
            <button
              onClick={handleInvalidateCache}
              className="w-full flex items-center justify-center px-4 py-2 bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors"
            >
              <AlertTriangle className="h-4 w-4 mr-2" />
              Invalidate Cache
            </button>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance</h3>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Total Requests</span>
              <span className="font-medium">{stats.stats.total_requests.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Cache Hits</span>
              <span className="font-medium text-green-600">{stats.stats.hits.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Cache Misses</span>
              <span className="font-medium text-red-600">{stats.stats.misses.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Evicted Keys</span>
              <span className="font-medium">{stats.stats.evicted_keys.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Expired Keys</span>
              <span className="font-medium">{stats.stats.expired_keys.toLocaleString()}</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">System Info</h3>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Connected Clients</span>
              <span className="font-medium">{stats.clients.connected}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Blocked Clients</span>
              <span className="font-medium">{stats.clients.blocked}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Max Clients</span>
              <span className="font-medium">{stats.clients.max_clients.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Memory Fragmentation</span>
              <span className="font-medium">{stats.memory.fragmentation_ratio.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">RSS Memory</span>
              <span className="font-medium">{formatBytes(stats.memory.rss_bytes)}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CacheMetrics