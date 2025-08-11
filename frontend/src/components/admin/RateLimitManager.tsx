import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import {
  Shield,
  Settings,
  Activity,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Zap,
  Users,
  Globe,
  Key,
  Gauge,
  RotateCcw,
  TestTube,
  TrendingUp,
} from 'lucide-react';

interface RateLimitConfig {
  scope: string;
  endpoint?: string;
  requests_per_second: number;
  burst_capacity: number;
  window_size: number;
  algorithm: string;
  enabled: boolean;
}

interface RateLimitStats {
  global_stats: {
    algorithm_usage: Record<string, number>;
    scope_usage: Record<string, number>;
    total_buckets: number;
    total_windows: number;
    redis_connected: boolean;
  };
  top_limited_ips: Array<{
    ip: string;
    violations: number;
    last_violation: string;
  }>;
  top_limited_users: Array<{
    user_id: number;
    violations: number;
    last_violation: string;
  }>;
  algorithm_distribution: Record<string, number>;
  recent_violations: Array<{
    timestamp: string;
    identifier: string;
    scope: string;
    endpoint: string;
    violation_type: string;
  }>;
}

interface RateLimitHealth {
  status: string;
  redis_connected: boolean;
  rate_limiting_functional: boolean;
  active_buckets: number;
  active_windows: number;
  timestamp: string;
}

interface RateLimitManagerProps {
  className?: string;
}

export const RateLimitManager: React.FC<RateLimitManagerProps> = ({ className }) => {
  const [configs, setConfigs] = useState<RateLimitConfig[]>([]);
  const [stats, setStats] = useState<RateLimitStats | null>(null);
  const [health, setHealth] = useState<RateLimitHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Modal states
  const [showConfigDialog, setShowConfigDialog] = useState(false);
  const [showResetDialog, setShowResetDialog] = useState(false);
  const [showTestDialog, setShowTestDialog] = useState(false);
  
  // Form states
  const [selectedScope, setSelectedScope] = useState<string>('user');
  const [configForm, setConfigForm] = useState({
    requests_per_second: 10,
    burst_capacity: 50,
    window_size: 60,
    algorithm: 'token_bucket',
    enabled: true,
    endpoint: ''
  });
  
  const [resetForm, setResetForm] = useState({
    identifier: '',
    scope: 'user',
    endpoint: ''
  });
  
  const [testForm, setTestForm] = useState({
    identifier: 'test_user',
    scope: 'user',
    requests: 5
  });
  
  const fetchConfigs = async () => {
    try {
      const response = await fetch('/api/v1/rate-limiting/config');
      if (!response.ok) throw new Error('Failed to fetch configs');
      const data = await response.json();
      setConfigs(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };
  
  const fetchStats = async () => {
    try {
      const response = await fetch('/api/v1/rate-limiting/stats');
      if (!response.ok) throw new Error('Failed to fetch stats');
      const data = await response.json();
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };
  
  const fetchHealth = async () => {
    try {
      const response = await fetch('/api/v1/rate-limiting/health');
      if (!response.ok) throw new Error('Failed to fetch health');
      const data = await response.json();
      setHealth(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };
  
  const refreshData = async () => {
    setLoading(true);
    await Promise.all([fetchConfigs(), fetchStats(), fetchHealth()]);
    setLoading(false);
  };
  
  useEffect(() => {
    refreshData();
    
    // Set up auto-refresh
    const interval = setInterval(refreshData, 30000); // 30 seconds
    return () => clearInterval(interval);
  }, []);
  
  const updateConfig = async () => {
    try {
      const endpoint = configForm.endpoint || undefined;
      const url = `/api/v1/rate-limiting/config/${selectedScope}${endpoint ? `?endpoint=${encodeURIComponent(endpoint)}` : ''}`;
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          requests_per_second: configForm.requests_per_second,
          burst_capacity: configForm.burst_capacity,
          window_size: configForm.window_size,
          algorithm: configForm.algorithm,
          enabled: configForm.enabled
        }),
      });
      
      if (!response.ok) throw new Error('Failed to update config');
      
      setShowConfigDialog(false);
      await refreshData();
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update config');
    }
  };
  
  const resetRateLimit = async () => {
    try {
      const response = await fetch('/api/v1/rate-limiting/reset', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          identifier: resetForm.identifier,
          scope: resetForm.scope,
          endpoint: resetForm.endpoint || null
        }),
      });
      
      if (!response.ok) throw new Error('Failed to reset rate limit');
      
      setShowResetDialog(false);
      await refreshData();
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset rate limit');
    }
  };
  
  const testRateLimit = async () => {
    try {
      const response = await fetch(
        `/api/v1/rate-limiting/test/${encodeURIComponent(testForm.identifier)}?requests=${testForm.requests}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            scope: testForm.scope
          }),
        }
      );
      
      if (!response.ok) throw new Error('Failed to test rate limit');
      
      const result = await response.json();
      alert(`Test completed: ${result.total_allowed}/${result.total_requests} requests allowed`);
      
      setShowTestDialog(false);
      await refreshData();
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to test rate limit');
    }
  };
  
  const getAlgorithmBadgeColor = (algorithm: string) => {
    switch (algorithm) {
      case 'token_bucket': return 'default';
      case 'sliding_window': return 'secondary';
      case 'fixed_window': return 'outline';
      case 'leaky_bucket': return 'destructive';
      default: return 'outline';
    }
  };
  
  const getScopeIcon = (scope: string) => {
    switch (scope) {
      case 'global': return <Globe className="h-4 w-4" />;
      case 'user': return <Users className="h-4 w-4" />;
      case 'ip': return <Shield className="h-4 w-4" />;
      case 'api_key': return <Key className="h-4 w-4" />;
      case 'endpoint': return <Zap className="h-4 w-4" />;
      default: return <Activity className="h-4 w-4" />;
    }
  };
  
  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Gauge className="h-5 w-5" />
            Rate Limit Manager
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center p-8">
            <RefreshCw className="h-6 w-6 animate-spin mr-2" />
            Loading rate limiting data...
          </div>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Gauge className="h-5 w-5" />
              Rate Limit Manager
            </div>
            <div className="flex gap-2">
              <Button onClick={() => setShowTestDialog(true)} variant="outline" size="sm">
                <TestTube className="h-4 w-4 mr-2" />
                Test
              </Button>
              <Button onClick={() => setShowResetDialog(true)} variant="outline" size="sm">
                <RotateCcw className="h-4 w-4 mr-2" />
                Reset
              </Button>
              <Button onClick={() => setShowConfigDialog(true)} variant="outline" size="sm">
                <Settings className="h-4 w-4 mr-2" />
                Configure
              </Button>
              <Button onClick={refreshData} variant="outline" size="sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
          </CardTitle>
          <CardDescription>
            Monitor and manage rate limiting across all API endpoints
          </CardDescription>
        </CardHeader>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Health Status */}
      {health && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">System Health</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="flex items-center gap-2">
                {health.status === 'healthy' ? (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-red-500" />
                )}
                <span className="text-sm">Status: {health.status}</span>
              </div>
              
              <div className="flex items-center gap-2">
                <div className={`h-2 w-2 rounded-full ${
                  health.redis_connected ? 'bg-green-500' : 'bg-red-500'
                }`} />
                <span className="text-sm">Redis: {health.redis_connected ? 'Connected' : 'Disconnected'}</span>
              </div>
              
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-blue-500" />
                <span className="text-sm">Buckets: {health.active_buckets}</span>
              </div>
              
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-purple-500" />
                <span className="text-sm">Windows: {health.active_windows}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="configs" className="space-y-4">
        <TabsList>
          <TabsTrigger value="configs">Configurations</TabsTrigger>
          <TabsTrigger value="stats">Statistics</TabsTrigger>
          <TabsTrigger value="violations">Recent Violations</TabsTrigger>
        </TabsList>

        <TabsContent value="configs">
          <Card>
            <CardHeader>
              <CardTitle>Rate Limit Configurations</CardTitle>
              <CardDescription>
                Current rate limiting rules and their settings
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Scope</TableHead>
                    <TableHead>Endpoint</TableHead>
                    <TableHead>Rate (req/s)</TableHead>
                    <TableHead>Burst Capacity</TableHead>
                    <TableHead>Algorithm</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {configs.map((config, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getScopeIcon(config.scope)}
                          {config.scope}
                        </div>
                      </TableCell>
                      <TableCell>
                        <code className="text-sm bg-muted px-1 py-0.5 rounded">
                          {config.endpoint || 'All'}
                        </code>
                      </TableCell>
                      <TableCell>{config.requests_per_second}</TableCell>
                      <TableCell>{config.burst_capacity}</TableCell>
                      <TableCell>
                        <Badge variant={getAlgorithmBadgeColor(config.algorithm)}>
                          {config.algorithm}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={config.enabled ? 'default' : 'secondary'}>
                          {config.enabled ? 'Enabled' : 'Disabled'}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {configs.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  No rate limiting configurations found.
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="stats">
          {stats && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Algorithm Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {Object.entries(stats.algorithm_distribution).map(([algorithm, count]) => (
                      <div key={algorithm} className="flex justify-between items-center">
                        <Badge variant={getAlgorithmBadgeColor(algorithm)}>
                          {algorithm}
                        </Badge>
                        <span className="font-mono">{count}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Top Limited IPs</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {stats.top_limited_ips.map((item, index) => (
                      <div key={index} className="flex justify-between items-center text-sm">
                        <code className="bg-muted px-2 py-1 rounded">{item.ip}</code>
                        <Badge variant="destructive">{item.violations}</Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Top Limited Users</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {stats.top_limited_users.map((item, index) => (
                      <div key={index} className="flex justify-between items-center text-sm">
                        <span>User {item.user_id}</span>
                        <Badge variant="destructive">{item.violations}</Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">System Overview</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Active Buckets:</span>
                      <span className="font-mono">{stats.global_stats.total_buckets}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Active Windows:</span>
                      <span className="font-mono">{stats.global_stats.total_windows}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Redis Status:</span>
                      <Badge variant={stats.global_stats.redis_connected ? 'default' : 'destructive'}>
                        {stats.global_stats.redis_connected ? 'Connected' : 'Disconnected'}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        <TabsContent value="violations">
          <Card>
            <CardHeader>
              <CardTitle>Recent Violations</CardTitle>
              <CardDescription>
                Recent rate limiting violations across all scopes
              </CardDescription>
            </CardHeader>
            <CardContent>
              {stats?.recent_violations && stats.recent_violations.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Timestamp</TableHead>
                      <TableHead>Identifier</TableHead>
                      <TableHead>Scope</TableHead>
                      <TableHead>Endpoint</TableHead>
                      <TableHead>Violation Type</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {stats.recent_violations.map((violation, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          {new Date(violation.timestamp).toLocaleString()}
                        </TableCell>
                        <TableCell>
                          <code className="text-sm bg-muted px-1 py-0.5 rounded">
                            {violation.identifier}
                          </code>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{violation.scope}</Badge>
                        </TableCell>
                        <TableCell>
                          <code className="text-xs">{violation.endpoint}</code>
                        </TableCell>
                        <TableCell>
                          <Badge variant="destructive">{violation.violation_type}</Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No recent violations found.
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Configuration Dialog */}
      <Dialog open={showConfigDialog} onOpenChange={setShowConfigDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Update Rate Limit Configuration</DialogTitle>
            <DialogDescription>
              Configure rate limiting for a specific scope and endpoint
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="scope">Scope</Label>
              <Select value={selectedScope} onChange={(e) => setSelectedScope(e.target.value)}>
                <option value="global">Global</option>
                <option value="user">User</option>
                <option value="ip">IP Address</option>
                <option value="api_key">API Key</option>
                <option value="endpoint">Endpoint</option>
              </Select>
            </div>

            {selectedScope === 'endpoint' && (
              <div className="space-y-2">
                <Label htmlFor="endpoint">Endpoint</Label>
                <Input
                  id="endpoint"
                  value={configForm.endpoint}
                  onChange={(e) => setConfigForm({ ...configForm, endpoint: e.target.value })}
                  placeholder="/api/v1/transcription/transcribe"
                />
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="requests_per_second">Requests per Second</Label>
                <Input
                  id="requests_per_second"
                  type="number"
                  step="0.1"
                  value={configForm.requests_per_second}
                  onChange={(e) => setConfigForm({ ...configForm, requests_per_second: parseFloat(e.target.value) })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="burst_capacity">Burst Capacity</Label>
                <Input
                  id="burst_capacity"
                  type="number"
                  value={configForm.burst_capacity}
                  onChange={(e) => setConfigForm({ ...configForm, burst_capacity: parseInt(e.target.value) })}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="algorithm">Algorithm</Label>
              <Select
                value={configForm.algorithm}
                onChange={(e) => setConfigForm({ ...configForm, algorithm: e.target.value })}
              >
                <option value="token_bucket">Token Bucket</option>
                <option value="sliding_window">Sliding Window</option>
                <option value="fixed_window">Fixed Window</option>
                <option value="leaky_bucket">Leaky Bucket</option>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConfigDialog(false)}>
              Cancel
            </Button>
            <Button onClick={updateConfig}>
              Update Configuration
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reset Dialog */}
      <Dialog open={showResetDialog} onOpenChange={setShowResetDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reset Rate Limit</DialogTitle>
            <DialogDescription>
              Reset rate limiting for a specific identifier. Use with caution.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="reset_identifier">Identifier</Label>
              <Input
                id="reset_identifier"
                value={resetForm.identifier}
                onChange={(e) => setResetForm({ ...resetForm, identifier: e.target.value })}
                placeholder="user_id, IP address, or API key"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="reset_scope">Scope</Label>
              <Select
                value={resetForm.scope}
                onChange={(e) => setResetForm({ ...resetForm, scope: e.target.value })}
              >
                <option value="user">User</option>
                <option value="ip">IP Address</option>
                <option value="api_key">API Key</option>
                <option value="endpoint">Endpoint</option>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowResetDialog(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={resetRateLimit}>
              Reset Rate Limit
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Test Dialog */}
      <Dialog open={showTestDialog} onOpenChange={setShowTestDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Test Rate Limiting</DialogTitle>
            <DialogDescription>
              Simulate requests to test rate limiting behavior
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="test_identifier">Test Identifier</Label>
              <Input
                id="test_identifier"
                value={testForm.identifier}
                onChange={(e) => setTestForm({ ...testForm, identifier: e.target.value })}
                placeholder="test_user_123"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="test_scope">Scope</Label>
                <Select
                  value={testForm.scope}
                  onChange={(e) => setTestForm({ ...testForm, scope: e.target.value })}
                >
                  <option value="user">User</option>
                  <option value="ip">IP Address</option>
                  <option value="api_key">API Key</option>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="test_requests">Number of Requests</Label>
                <Input
                  id="test_requests"
                  type="number"
                  min="1"
                  max="100"
                  value={testForm.requests}
                  onChange={(e) => setTestForm({ ...testForm, requests: parseInt(e.target.value) })}
                />
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowTestDialog(false)}>
              Cancel
            </Button>
            <Button onClick={testRateLimit}>
              Run Test
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default RateLimitManager;