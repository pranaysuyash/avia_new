import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Label } from '../ui/label';
import { Switch } from '../ui/switch';
import { Progress } from '../ui/progress';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';
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
} from 'recharts';
import {
  Activity,
  Users,
  Server,
  HardDrive,
  Cpu,
  MemoryStick,
  Wifi,
  AlertTriangle,
  Settings,
  Download,
  RefreshCw,
  Search,
  Filter,
  MoreVertical,
  Shield,
  Clock,
  TrendingUp,
  TrendingDown,
  DollarSign,
  UserCheck,
  UserX,
  Ban,
  CheckCircle,
  XCircle,
  Bell,
  Wrench,
} from 'lucide-react';
import { format } from 'date-fns';

// Types
interface SystemMetrics {
  timestamp: string;
  cpu_percent: number;
  memory_percent: number;
  memory_used_mb: number;
  memory_total_mb: number;
  disk_percent: number;
  disk_used_gb: number;
  disk_total_gb: number;
  active_users: number;
  total_api_calls: number;
  error_count: number;
  avg_response_time_ms: number;
  cache_hit_rate: number;
  websocket_connections: number;
  transcription_minutes_today: number;
  system_health: string;
}

interface UserMetrics {
  user_id: number;
  username: string;
  email: string;
  status: string;
  created_at: string;
  last_login: string | null;
  total_transcriptions: number;
  total_minutes_transcribed: number;
  storage_used_mb: number;
  api_calls_today: number;
  subscription_tier: string;
  team_name: string | null;
  is_team_admin: boolean;
}

interface DashboardData {
  system_metrics: SystemMetrics;
  user_stats: {
    total_users: number;
    active_users: number;
    suspended_users: number;
    users_by_tier: Record<string, number>;
    new_users_this_month: number;
    total_teams: number;
    growth_rate: number;
  };
  usage_trends: {
    daily_users: Array<{ date: string; value: number }>;
    daily_transcriptions: Array<{ date: string; value: number }>;
    daily_api_calls: Array<{ date: string; value: number }>;
    daily_errors: Array<{ date: string; value: number }>;
  };
  active_sessions: Array<{
    user_id: number;
    username: string;
    ip_address: string;
    user_agent: string;
    created_at: string;
    last_activity: string;
    session_id: string;
  }>;
  recent_errors: Array<{
    id: number;
    timestamp: string;
    user_id: number;
    action: string;
    details: any;
    ip_address: string;
  }>;
  subscription_summary: {
    revenue_by_tier: Record<string, number>;
    monthly_recurring_revenue: number;
    annual_recurring_revenue: number;
    churn_rate: number;
    paying_users: number;
    conversion_rate: number;
  };
  storage_summary: {
    total_storage_gb: number;
    storage_by_tier: Record<string, number>;
    top_storage_users: Array<{
      user_id: number;
      username: string;
      storage_gb: number;
    }>;
    average_file_size_mb: number;
  };
  api_usage_summary: {
    top_endpoints: Array<{ endpoint: string; calls: number }>;
    top_api_keys: Array<{ key_name: string; usage: number }>;
    total_api_calls_week: number;
  };
}

interface SystemSettings {
  maintenance_mode: boolean;
  allow_registrations: boolean;
  require_email_verification: boolean;
  max_upload_size_mb: number;
  max_transcription_length_minutes: number;
  rate_limit_per_minute: number;
  session_timeout_minutes: number;
  password_min_length: number;
  password_require_special: boolean;
  enable_api_access: boolean;
  enable_webhooks: boolean;
  backup_enabled: boolean;
  backup_interval_hours: number;
}

interface AdminDashboardProps {
  className?: string;
}

const CHART_COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

export const AdminDashboard: React.FC<AdminDashboardProps> = ({ className }) => {
  // State
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [systemSettings, setSystemSettings] = useState<SystemSettings | null>(null);
  const [users, setUsers] = useState<UserMetrics[]>([]);
  const [selectedUser, setSelectedUser] = useState<UserMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  
  // UI state
  const [activeTab, setActiveTab] = useState('overview');
  const [userSearchQuery, setUserSearchQuery] = useState('');
  const [userStatusFilter, setUserStatusFilter] = useState('all');
  const [showUserDetailsDialog, setShowUserDetailsDialog] = useState(false);
  const [showSettingsDialog, setShowSettingsDialog] = useState(false);
  const [showAnnouncementDialog, setShowAnnouncementDialog] = useState(false);
  const [showMaintenanceDialog, setShowMaintenanceDialog] = useState(false);
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Load dashboard data
  const loadDashboardData = useCallback(async () => {
    try {
      setError(null);
      const response = await fetch('/api/v1/admin/dashboard');
      
      if (!response.ok) {
        throw new Error('Failed to load dashboard data');
      }
      
      const data = await response.json();
      setDashboardData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
      console.error('Dashboard load error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Load system settings
  const loadSystemSettings = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/admin/settings');
      
      if (!response.ok) {
        throw new Error('Failed to load system settings');
      }
      
      const settings = await response.json();
      setSystemSettings(settings);
    } catch (err) {
      console.error('Settings load error:', err);
    }
  }, []);

  // Load users
  const loadUsers = useCallback(async (page: number = 1) => {
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: '20',
        ...(userSearchQuery && { search: userSearchQuery }),
        ...(userStatusFilter !== 'all' && { status: userStatusFilter }),
      });
      
      const response = await fetch(`/api/v1/admin/users?${params}`);
      
      if (!response.ok) {
        throw new Error('Failed to load users');
      }
      
      const data = await response.json();
      setUsers(data.users);
      setTotalPages(data.pagination.pages);
      setCurrentPage(page);
    } catch (err) {
      console.error('Users load error:', err);
    }
  }, [userSearchQuery, userStatusFilter]);

  // Update user status
  const updateUserStatus = async (userId: number, newStatus: string, reason?: string) => {
    try {
      const response = await fetch(`/api/v1/admin/users/${userId}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus, reason }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to update user status');
      }
      
      // Reload users
      await loadUsers(currentPage);
      setShowUserDetailsDialog(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update user');
    }
  };

  // Update system settings
  const updateSystemSettings = async (settings: Partial<SystemSettings>) => {
    try {
      const response = await fetch('/api/v1/admin/settings', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      });
      
      if (!response.ok) {
        throw new Error('Failed to update settings');
      }
      
      await loadSystemSettings();
      setShowSettingsDialog(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update settings');
    }
  };

  // Refresh dashboard
  const refreshDashboard = async () => {
    setRefreshing(true);
    await Promise.all([loadDashboardData(), loadUsers(currentPage)]);
    setRefreshing(false);
  };

  // Initial load
  useEffect(() => {
    loadDashboardData();
    loadSystemSettings();
    loadUsers();
  }, [loadDashboardData, loadSystemSettings]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      if (!document.hidden) {
        loadDashboardData();
      }
    }, 30000);
    
    return () => clearInterval(interval);
  }, [loadDashboardData]);

  // Search users on input change
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      loadUsers(1);
    }, 300);
    
    return () => clearTimeout(debounceTimer);
  }, [userSearchQuery, userStatusFilter, loadUsers]);

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'healthy': return 'text-green-500';
      case 'good': return 'text-blue-500';
      case 'warning': return 'text-yellow-500';
      case 'critical': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'suspended': return 'bg-yellow-100 text-yellow-800';
      case 'deleted': return 'bg-red-100 text-red-800';
      case 'pending': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'free': return 'bg-gray-100 text-gray-800';
      case 'basic': return 'bg-blue-100 text-blue-800';
      case 'pro': return 'bg-purple-100 text-purple-800';
      case 'enterprise': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p>Loading admin dashboard...</p>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>Failed to load dashboard data</AlertDescription>
      </Alert>
    );
  }

  const { system_metrics, user_stats, usage_trends, subscription_summary, storage_summary } = dashboardData;

  return (
    <div className={`space-y-6 p-6 ${className}`}>
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Admin Dashboard</h1>
          <p className="text-muted-foreground">System monitoring and user management</p>
        </div>
        
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={refreshDashboard}
            disabled={refreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          
          <Button
            variant="outline"
            onClick={() => setShowSettingsDialog(true)}
          >
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </Button>
          
          <Button
            variant="outline"
            onClick={() => setShowAnnouncementDialog(true)}
          >
            <Bell className="h-4 w-4 mr-2" />
            Announce
          </Button>
          
          <Button
            variant="outline"
            onClick={() => setShowMaintenanceDialog(true)}
          >
            <Wrench className="h-4 w-4 mr-2" />
            Maintenance
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* System Health Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">System Health</p>
                <p className={`text-2xl font-bold ${getHealthColor(system_metrics.system_health)}`}>
                  {system_metrics.system_health.toUpperCase()}
                </p>
              </div>
              <Activity className={`h-8 w-8 ${getHealthColor(system_metrics.system_health)}`} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Active Users</p>
                <p className="text-2xl font-bold">{system_metrics.active_users}</p>
                <p className="text-xs text-muted-foreground">Last 15 minutes</p>
              </div>
              <Users className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">API Calls Today</p>
                <p className="text-2xl font-bold">{system_metrics.total_api_calls.toLocaleString()}</p>
                <p className="text-xs text-muted-foreground">
                  {system_metrics.error_count} errors
                </p>
              </div>
              <Server className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Monthly Revenue</p>
                <p className="text-2xl font-bold">
                  ${subscription_summary.monthly_recurring_revenue.toFixed(2)}
                </p>
                <p className="text-xs text-muted-foreground">
                  {subscription_summary.paying_users} paying users
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          {/* System Resources */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Cpu className="h-5 w-5" />
                  CPU Usage
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Current</span>
                    <span className="font-bold">{system_metrics.cpu_percent.toFixed(1)}%</span>
                  </div>
                  <Progress value={system_metrics.cpu_percent} className="h-2" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MemoryStick className="h-5 w-5" />
                  Memory Usage
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>
                      {(system_metrics.memory_used_mb / 1024).toFixed(1)} GB
                    </span>
                    <span className="font-bold">{system_metrics.memory_percent.toFixed(1)}%</span>
                  </div>
                  <Progress value={system_metrics.memory_percent} className="h-2" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <HardDrive className="h-5 w-5" />
                  Disk Usage
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>
                      {system_metrics.disk_used_gb.toFixed(1)} GB
                    </span>
                    <span className="font-bold">{system_metrics.disk_percent.toFixed(1)}%</span>
                  </div>
                  <Progress value={system_metrics.disk_percent} className="h-2" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Usage Trends */}
          <Card>
            <CardHeader>
              <CardTitle>Usage Trends (30 Days)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={usage_trends.daily_users}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke="#3B82F6"
                      name="Daily Active Users"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Total Users</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{user_stats.total_users}</div>
                <p className="text-xs text-muted-foreground">
                  <span className={user_stats.growth_rate >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {user_stats.growth_rate >= 0 ? '+' : ''}{user_stats.growth_rate.toFixed(1)}%
                  </span>
                  {' '}vs last month
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Response Time</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {system_metrics.avg_response_time_ms.toFixed(0)}ms
                </div>
                <p className="text-xs text-muted-foreground">Average</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Cache Hit Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {(system_metrics.cache_hit_rate * 100).toFixed(1)}%
                </div>
                <p className="text-xs text-muted-foreground">Efficiency</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Storage Used</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {storage_summary.total_storage_gb.toFixed(1)} GB
                </div>
                <p className="text-xs text-muted-foreground">
                  Avg {storage_summary.average_file_size_mb.toFixed(1)} MB/file
                </p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Users Tab */}
        <TabsContent value="users" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>User Management</CardTitle>
                <div className="flex gap-2">
                  <div className="relative">
                    <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search users..."
                      value={userSearchQuery}
                      onChange={(e) => setUserSearchQuery(e.target.value)}
                      className="pl-10 w-64"
                    />
                  </div>
                  <Select value={userStatusFilter} onChange={(e) => setUserStatusFilter(e.target.value)}>
                    <option value="all">All Status</option>
                    <option value="active">Active</option>
                    <option value="suspended">Suspended</option>
                    <option value="pending">Pending</option>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>User</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Tier</TableHead>
                    <TableHead>Last Login</TableHead>
                    <TableHead>Usage</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((user) => (
                    <TableRow key={user.user_id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{user.username}</div>
                          <div className="text-sm text-muted-foreground">{user.email}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge className={getStatusColor(user.status)}>
                          {user.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={getTierColor(user.subscription_tier)}>
                          {user.subscription_tier}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {user.last_login
                          ? format(new Date(user.last_login), 'MMM dd, yyyy')
                          : 'Never'}
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          <div>{user.total_transcriptions} transcripts</div>
                          <div className="text-muted-foreground">
                            {user.total_minutes_transcribed.toFixed(1)} min
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSelectedUser(user);
                            setShowUserDetailsDialog(true);
                          }}
                        >
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              
              {/* Pagination */}
              <div className="flex justify-between items-center mt-4">
                <div className="text-sm text-muted-foreground">
                  Page {currentPage} of {totalPages}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => loadUsers(currentPage - 1)}
                    disabled={currentPage === 1}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => loadUsers(currentPage + 1)}
                    disabled={currentPage === totalPages}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>API Response Times</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={usage_trends.daily_api_calls}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke="#10B981"
                        name="API Calls"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Error Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={usage_trends.daily_errors}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke="#EF4444"
                        name="Errors"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Top API Endpoints</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {dashboardData.api_usage_summary.top_endpoints.map((endpoint, index) => (
                  <div key={index} className="flex justify-between items-center">
                    <span className="text-sm font-medium">{endpoint.endpoint}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-muted-foreground">
                        {endpoint.calls.toLocaleString()} calls
                      </span>
                      <Progress
                        value={(endpoint.calls / dashboardData.api_usage_summary.total_api_calls_week) * 100}
                        className="w-24 h-2"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Revenue by Tier</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={Object.entries(subscription_summary.revenue_by_tier).map(([tier, count]) => ({
                          name: tier,
                          value: count,
                        }))}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={(entry) => `${entry.name}: ${entry.value}`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {Object.entries(subscription_summary.revenue_by_tier).map((_, index) => (
                          <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>User Growth</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={usage_trends.daily_transcriptions}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="value" fill="#8B5CF6" name="Transcriptions" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Conversion Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {subscription_summary.conversion_rate.toFixed(1)}%
                </div>
                <p className="text-xs text-muted-foreground">Free to paid</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Churn Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {subscription_summary.churn_rate.toFixed(1)}%
                </div>
                <p className="text-xs text-muted-foreground">Last 30 days</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">ARR</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  ${subscription_summary.annual_recurring_revenue.toLocaleString()}
                </div>
                <p className="text-xs text-muted-foreground">Annual recurring</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Logs Tab */}
        <TabsContent value="logs" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Errors</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {dashboardData.recent_errors.map((error) => (
                  <div
                    key={error.id}
                    className="p-3 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <AlertTriangle className="h-4 w-4 text-red-500" />
                          <span className="font-medium">{error.action}</span>
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">
                          {JSON.stringify(error.details)}
                        </p>
                      </div>
                      <div className="text-right text-sm text-muted-foreground">
                        <div>{format(new Date(error.timestamp), 'MMM dd, HH:mm')}</div>
                        <div>User: {error.user_id}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Active Sessions</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>User</TableHead>
                    <TableHead>IP Address</TableHead>
                    <TableHead>User Agent</TableHead>
                    <TableHead>Last Activity</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {dashboardData.active_sessions.slice(0, 10).map((session) => (
                    <TableRow key={session.session_id}>
                      <TableCell>{session.username}</TableCell>
                      <TableCell>
                        <code className="text-xs">{session.ip_address}</code>
                      </TableCell>
                      <TableCell className="max-w-xs truncate">
                        {session.user_agent}
                      </TableCell>
                      <TableCell>
                        {format(new Date(session.last_activity), 'HH:mm:ss')}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* User Details Dialog */}
      <Dialog open={showUserDetailsDialog} onOpenChange={setShowUserDetailsDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>User Details</DialogTitle>
            <DialogDescription>
              Manage user account and view detailed information
            </DialogDescription>
          </DialogHeader>
          
          {selectedUser && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Username</Label>
                  <p className="font-medium">{selectedUser.username}</p>
                </div>
                <div>
                  <Label>Email</Label>
                  <p className="font-medium">{selectedUser.email}</p>
                </div>
                <div>
                  <Label>Status</Label>
                  <Badge className={getStatusColor(selectedUser.status)}>
                    {selectedUser.status}
                  </Badge>
                </div>
                <div>
                  <Label>Subscription</Label>
                  <Badge className={getTierColor(selectedUser.subscription_tier)}>
                    {selectedUser.subscription_tier}
                  </Badge>
                </div>
                <div>
                  <Label>Created</Label>
                  <p>{format(new Date(selectedUser.created_at), 'MMM dd, yyyy')}</p>
                </div>
                <div>
                  <Label>Last Login</Label>
                  <p>
                    {selectedUser.last_login
                      ? format(new Date(selectedUser.last_login), 'MMM dd, yyyy HH:mm')
                      : 'Never'}
                  </p>
                </div>
              </div>

              <div className="border-t pt-4">
                <Label>Usage Statistics</Label>
                <div className="grid grid-cols-3 gap-4 mt-2">
                  <div className="text-center">
                    <p className="text-2xl font-bold">{selectedUser.total_transcriptions}</p>
                    <p className="text-sm text-muted-foreground">Transcriptions</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold">
                      {selectedUser.total_minutes_transcribed.toFixed(1)}
                    </p>
                    <p className="text-sm text-muted-foreground">Minutes</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold">
                      {(selectedUser.storage_used_mb / 1024).toFixed(2)}
                    </p>
                    <p className="text-sm text-muted-foreground">GB Storage</p>
                  </div>
                </div>
              </div>

              <div className="border-t pt-4">
                <Label>Account Actions</Label>
                <div className="flex gap-2 mt-2">
                  {selectedUser.status === 'active' && (
                    <Button
                      variant="outline"
                      onClick={() => updateUserStatus(selectedUser.user_id, 'suspended')}
                    >
                      <Ban className="h-4 w-4 mr-2" />
                      Suspend User
                    </Button>
                  )}
                  {selectedUser.status === 'suspended' && (
                    <Button
                      variant="outline"
                      onClick={() => updateUserStatus(selectedUser.user_id, 'active')}
                    >
                      <UserCheck className="h-4 w-4 mr-2" />
                      Activate User
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    className="text-red-600"
                    onClick={() => updateUserStatus(selectedUser.user_id, 'deleted')}
                  >
                    <UserX className="h-4 w-4 mr-2" />
                    Delete User
                  </Button>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Settings Dialog */}
      <Dialog open={showSettingsDialog} onOpenChange={setShowSettingsDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>System Settings</DialogTitle>
            <DialogDescription>
              Configure system-wide settings and preferences
            </DialogDescription>
          </DialogHeader>
          
          {systemSettings && (
            <div className="space-y-4 max-h-96 overflow-y-auto">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Maintenance Mode</Label>
                  <p className="text-sm text-muted-foreground">
                    Disable all services for maintenance
                  </p>
                </div>
                <Switch
                  checked={systemSettings.maintenance_mode}
                  onCheckedChange={(checked) =>
                    updateSystemSettings({ maintenance_mode: checked })
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Allow Registrations</Label>
                  <p className="text-sm text-muted-foreground">
                    Allow new users to register
                  </p>
                </div>
                <Switch
                  checked={systemSettings.allow_registrations}
                  onCheckedChange={(checked) =>
                    updateSystemSettings({ allow_registrations: checked })
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Email Verification</Label>
                  <p className="text-sm text-muted-foreground">
                    Require email verification for new accounts
                  </p>
                </div>
                <Switch
                  checked={systemSettings.require_email_verification}
                  onCheckedChange={(checked) =>
                    updateSystemSettings({ require_email_verification: checked })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label>Max Upload Size (MB)</Label>
                <Input
                  type="number"
                  value={systemSettings.max_upload_size_mb}
                  onChange={(e) =>
                    updateSystemSettings({ max_upload_size_mb: parseInt(e.target.value) })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label>Max Transcription Length (minutes)</Label>
                <Input
                  type="number"
                  value={systemSettings.max_transcription_length_minutes}
                  onChange={(e) =>
                    updateSystemSettings({
                      max_transcription_length_minutes: parseInt(e.target.value),
                    })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label>Rate Limit (requests per minute)</Label>
                <Input
                  type="number"
                  value={systemSettings.rate_limit_per_minute}
                  onChange={(e) =>
                    updateSystemSettings({ rate_limit_per_minute: parseInt(e.target.value) })
                  }
                />
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button onClick={() => setShowSettingsDialog(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminDashboard;