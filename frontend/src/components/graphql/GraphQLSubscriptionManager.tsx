import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Client, createClient, subscriptionExchange, fetchExchange, cacheExchange } from 'urql';
import { createClient as createWSClient } from 'graphql-ws';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';
import {
  Activity,
  Bell,
  Database,
  Gauge,
  Globe,
  RefreshCw,
  Zap,
  AlertTriangle,
  CheckCircle,
  Users,
} from 'lucide-react';

// GraphQL query definitions
const SUBSCRIPTION_STATS_QUERY = `
  query GetSubscriptionStats {
    subscriptionStats {
      totalSubscriptions
      byType
      byUserCount
      redisConnected
    }
  }
`;

const SYSTEM_METRICS_SUBSCRIPTION = `
  subscription SystemMetrics {
    systemMetrics {
      timestamp
      cpuUsage
      memoryUsage
      diskUsage
      activeConnections
      requestRate
      errorRate
    }
  }
`;

const TRANSCRIPTION_STATUS_SUBSCRIPTION = `
  subscription TranscriptionStatus($jobIds: [String!], $userId: Int) {
    transcriptionStatus(jobIds: $jobIds, userId: $userId) {
      id
      userId
      status
      progress
      fileUrl
      createdAt
      updatedAt
      errorMessage
    }
  }
`;

const USER_NOTIFICATIONS_SUBSCRIPTION = `
  subscription UserNotifications($userId: Int!) {
    userNotifications(userId: $userId) {
      id
      userId
      title
      message
      type
      priority
      read
      createdAt
    }
  }
`;

const CACHE_UPDATES_SUBSCRIPTION = `
  subscription CacheUpdates {
    cacheUpdates {
      connected
      uptimeSeconds
      memoryUsed
      memoryPeak
      hitRate
      totalRequests
      hits
      misses
      totalKeys
    }
  }
`;

interface SubscriptionStats {
  totalSubscriptions: number;
  byType: Record<string, number>;
  byUserCount: number;
  redisConnected: boolean;
}

interface SystemMetrics {
  timestamp: string;
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  activeConnections: number;
  requestRate: number;
  errorRate: number;
}

interface TranscriptionJob {
  id: string;
  userId: number;
  status: string;
  progress: number;
  fileUrl: string;
  createdAt: string;
  updatedAt: string;
  errorMessage?: string;
}

interface NotificationMessage {
  id: string;
  userId: number;
  title: string;
  message: string;
  type: string;
  priority: string;
  read: boolean;
  createdAt: string;
}

interface CacheStats {
  connected: boolean;
  uptimeSeconds: number;
  memoryUsed: number;
  memoryPeak: number;
  hitRate: number;
  totalRequests: number;
  hits: number;
  misses: number;
  totalKeys: number;
}

interface GraphQLSubscriptionManagerProps {
  className?: string;
  userId?: number;
}

export const GraphQLSubscriptionManager: React.FC<GraphQLSubscriptionManagerProps> = ({ 
  className, 
  userId 
}) => {
  // State
  const [subscriptionStats, setSubscriptionStats] = useState<SubscriptionStats | null>(null);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [transcriptionJobs, setTranscriptionJobs] = useState<TranscriptionJob[]>([]);
  const [notifications, setNotifications] = useState<NotificationMessage[]>([]);
  const [cacheStats, setCacheStats] = useState<CacheStats | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [error, setError] = useState<string | null>(null);

  // Refs
  const clientRef = useRef<Client | null>(null);
  const wsClientRef = useRef<any>(null);

  // Initialize GraphQL client with subscriptions
  const initializeGraphQLClient = useCallback(() => {
    try {
      // Create WebSocket client for subscriptions
      wsClientRef.current = createWSClient({
        url: 'ws://localhost:8000/api/graphql/ws',
        connectionParams: () => ({
          // Add auth token if available
          authToken: localStorage.getItem('auth_token') || undefined,
        }),
        on: {
          opened: () => {
            console.log('GraphQL WebSocket connected');
            setConnectionStatus('connected');
            setError(null);
          },
          closed: () => {
            console.log('GraphQL WebSocket disconnected');
            setConnectionStatus('disconnected');
          },
          error: (error) => {
            console.error('GraphQL WebSocket error:', error);
            setConnectionStatus('disconnected');
            setError('WebSocket connection failed');
          },
        },
      });

      // Create urql client
      clientRef.current = createClient({
        url: 'http://localhost:8000/api/graphql',
        exchanges: [
          cacheExchange,
          fetchExchange,
          subscriptionExchange({
            forwardSubscription: (request) => ({
              subscribe: (sink) => ({
                unsubscribe: wsClientRef.current.subscribe(request, sink),
              }),
            }),
          }),
        ],
        fetchOptions: () => {
          const token = localStorage.getItem('auth_token');
          return {
            headers: {
              authorization: token ? `Bearer ${token}` : '',
            },
          };
        },
      });

      setConnectionStatus('connecting');
    } catch (err) {
      console.error('Failed to initialize GraphQL client:', err);
      setError('Failed to initialize GraphQL client');
    }
  }, []);

  // Fetch subscription stats
  const fetchSubscriptionStats = useCallback(async () => {
    if (!clientRef.current) return;

    try {
      const result = await clientRef.current.query(SUBSCRIPTION_STATS_QUERY, {}).toPromise();
      if (result.error) {
        throw new Error(result.error.message);
      }
      setSubscriptionStats(result.data?.subscriptionStats || null);
    } catch (err) {
      console.error('Failed to fetch subscription stats:', err);
      setError('Failed to fetch subscription stats');
    }
  }, []);

  // Subscribe to system metrics
  const subscribeToSystemMetrics = useCallback(() => {
    if (!clientRef.current) return;

    const subscription = clientRef.current
      .subscription(SYSTEM_METRICS_SUBSCRIPTION, {})
      .subscribe((result) => {
        if (result.error) {
          console.error('System metrics subscription error:', result.error);
          return;
        }
        
        if (result.data?.systemMetrics) {
          setSystemMetrics(result.data.systemMetrics);
        }
      });

    return () => subscription.unsubscribe();
  }, []);

  // Subscribe to transcription status
  const subscribeToTranscriptionStatus = useCallback(() => {
    if (!clientRef.current) return;

    const subscription = clientRef.current
      .subscription(TRANSCRIPTION_STATUS_SUBSCRIPTION, { userId })
      .subscribe((result) => {
        if (result.error) {
          console.error('Transcription status subscription error:', result.error);
          return;
        }
        
        if (result.data?.transcriptionStatus) {
          const job = result.data.transcriptionStatus;
          setTranscriptionJobs(prev => {
            const existing = prev.findIndex(j => j.id === job.id);
            if (existing >= 0) {
              const updated = [...prev];
              updated[existing] = job;
              return updated;
            }
            return [...prev, job];
          });
        }
      });

    return () => subscription.unsubscribe();
  }, [userId]);

  // Subscribe to user notifications
  const subscribeToUserNotifications = useCallback(() => {
    if (!clientRef.current || !userId) return;

    const subscription = clientRef.current
      .subscription(USER_NOTIFICATIONS_SUBSCRIPTION, { userId })
      .subscribe((result) => {
        if (result.error) {
          console.error('User notifications subscription error:', result.error);
          return;
        }
        
        if (result.data?.userNotifications) {
          const notification = result.data.userNotifications;
          setNotifications(prev => [notification, ...prev.slice(0, 9)]); // Keep last 10
        }
      });

    return () => subscription.unsubscribe();
  }, [userId]);

  // Subscribe to cache updates
  const subscribeToCacheUpdates = useCallback(() => {
    if (!clientRef.current) return;

    const subscription = clientRef.current
      .subscription(CACHE_UPDATES_SUBSCRIPTION, {})
      .subscribe((result) => {
        if (result.error) {
          console.error('Cache updates subscription error:', result.error);
          return;
        }
        
        if (result.data?.cacheUpdates) {
          setCacheStats(result.data.cacheUpdates);
        }
      });

    return () => subscription.unsubscribe();
  }, []);

  // Initialize and setup subscriptions
  useEffect(() => {
    initializeGraphQLClient();

    return () => {
      if (wsClientRef.current) {
        wsClientRef.current.dispose();
      }
    };
  }, [initializeGraphQLClient]);

  useEffect(() => {
    if (connectionStatus === 'connected' && clientRef.current) {
      // Fetch initial data
      fetchSubscriptionStats();

      // Setup subscriptions
      const unsubscribers = [
        subscribeToSystemMetrics(),
        subscribeToTranscriptionStatus(),
        subscribeToUserNotifications(),
        subscribeToCacheUpdates(),
      ].filter(Boolean);

      return () => {
        unsubscribers.forEach(unsub => unsub?.());
      };
    }
  }, [
    connectionStatus,
    fetchSubscriptionStats,
    subscribeToSystemMetrics,
    subscribeToTranscriptionStatus,
    subscribeToUserNotifications,
    subscribeToCacheUpdates,
  ]);

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-500';
      case 'connecting': return 'text-yellow-500';
      default: return 'text-red-500';
    }
  };

  const getConnectionStatusIcon = () => {
    switch (connectionStatus) {
      case 'connected': return <CheckCircle className="h-4 w-4" />;
      case 'connecting': return <RefreshCw className="h-4 w-4 animate-spin" />;
      default: return <AlertTriangle className="h-4 w-4" />;
    }
  };

  const formatBytes = (bytes: number): string => {
    const sizes = ['B', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const getNotificationTypeColor = (type: string) => {
    switch (type) {
      case 'success': return 'text-green-500';
      case 'warning': return 'text-yellow-500';
      case 'error': return 'text-red-500';
      default: return 'text-blue-500';
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              GraphQL Subscriptions
            </div>
            <div className={`flex items-center gap-2 ${getConnectionStatusColor()}`}>
              {getConnectionStatusIcon()}
              <span className="text-sm font-medium">
                {connectionStatus.charAt(0).toUpperCase() + connectionStatus.slice(1)}
              </span>
            </div>
          </CardTitle>
          <CardDescription>
            Real-time GraphQL subscriptions and data updates
          </CardDescription>
        </CardHeader>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Subscription Stats */}
      {subscriptionStats && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Subscription Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-blue-500" />
                <div>
                  <div className="text-2xl font-bold">{subscriptionStats.totalSubscriptions}</div>
                  <div className="text-xs text-muted-foreground">Total Subscriptions</div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-green-500" />
                <div>
                  <div className="text-2xl font-bold">{subscriptionStats.byUserCount}</div>
                  <div className="text-xs text-muted-foreground">Active Users</div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Database className="h-4 w-4 text-purple-500" />
                <div>
                  <div className="text-sm">
                    <Badge variant={subscriptionStats.redisConnected ? 'default' : 'destructive'}>
                      {subscriptionStats.redisConnected ? 'Connected' : 'Disconnected'}
                    </Badge>
                  </div>
                  <div className="text-xs text-muted-foreground">Redis Status</div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Zap className="h-4 w-4 text-yellow-500" />
                <div>
                  <div className="text-2xl font-bold">
                    {Object.values(subscriptionStats.byType).length}
                  </div>
                  <div className="text-xs text-muted-foreground">Subscription Types</div>
                </div>
              </div>
            </div>

            <div className="mt-4">
              <div className="text-sm font-medium mb-2">By Type:</div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(subscriptionStats.byType).map(([type, count]) => (
                  <Badge key={type} variant="outline">
                    {type}: {count}
                  </Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="metrics" className="space-y-4">
        <TabsList>
          <TabsTrigger value="metrics">System Metrics</TabsTrigger>
          <TabsTrigger value="transcriptions">Transcriptions</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="cache">Cache Stats</TabsTrigger>
        </TabsList>

        <TabsContent value="metrics">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Real-time System Metrics</CardTitle>
            </CardHeader>
            <CardContent>
              {systemMetrics ? (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-500">
                      {systemMetrics.cpuUsage.toFixed(1)}%
                    </div>
                    <div className="text-xs text-muted-foreground">CPU Usage</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-500">
                      {systemMetrics.memoryUsage.toFixed(1)}%
                    </div>
                    <div className="text-xs text-muted-foreground">Memory Usage</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-500">
                      {systemMetrics.requestRate.toFixed(1)}
                    </div>
                    <div className="text-xs text-muted-foreground">Requests/sec</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-500">
                      {(systemMetrics.errorRate * 100).toFixed(2)}%
                    </div>
                    <div className="text-xs text-muted-foreground">Error Rate</div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  Waiting for system metrics...
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="transcriptions">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Active Transcription Jobs</CardTitle>
            </CardHeader>
            <CardContent>
              {transcriptionJobs.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Job ID</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Progress</TableHead>
                      <TableHead>Updated</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {transcriptionJobs.map((job) => (
                      <TableRow key={job.id}>
                        <TableCell className="font-mono text-sm">{job.id}</TableCell>
                        <TableCell>
                          <Badge variant={
                            job.status === 'completed' ? 'default' :
                            job.status === 'failed' ? 'destructive' :
                            job.status === 'processing' ? 'secondary' : 'outline'
                          }>
                            {job.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div className="w-24 bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                                style={{ width: `${job.progress}%` }}
                              />
                            </div>
                            <span className="text-sm">{job.progress.toFixed(0)}%</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-sm">
                          {new Date(job.updatedAt).toLocaleTimeString()}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No active transcription jobs
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Bell className="h-4 w-4" />
                Real-time Notifications
              </CardTitle>
            </CardHeader>
            <CardContent>
              {notifications.length > 0 ? (
                <div className="space-y-3">
                  {notifications.map((notification) => (
                    <div
                      key={notification.id}
                      className={`p-3 rounded-lg border ${
                        notification.read ? 'bg-muted/50' : 'bg-background'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <div className={getNotificationTypeColor(notification.type)}>
                              <Bell className="h-4 w-4" />
                            </div>
                            <span className="font-medium text-sm">{notification.title}</span>
                            <Badge variant="outline" className="text-xs">
                              {notification.priority}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {notification.message}
                          </p>
                          <div className="text-xs text-muted-foreground mt-1">
                            {new Date(notification.createdAt).toLocaleString()}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No notifications received
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="cache">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Cache Statistics</CardTitle>
            </CardHeader>
            <CardContent>
              {cacheStats ? (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-500">
                      {(cacheStats.hitRate * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-muted-foreground">Hit Rate</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-500">
                      {formatBytes(cacheStats.memoryUsed)}
                    </div>
                    <div className="text-xs text-muted-foreground">Memory Used</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-500">
                      {cacheStats.totalKeys}
                    </div>
                    <div className="text-xs text-muted-foreground">Total Keys</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-500">
                      {cacheStats.totalRequests}
                    </div>
                    <div className="text-xs text-muted-foreground">Total Requests</div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  Waiting for cache statistics...
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default GraphQLSubscriptionManager;