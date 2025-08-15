/**
 * Workflow Management Panel for Electron Desktop App
 * Native desktop interface for enterprise workflow orchestration
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Progress,
  Alert,
  AlertDescription,
  AlertTitle,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Switch,
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger
} from '@/components/ui';
import {
  Play,
  Pause,
  Square,
  Eye,
  Settings,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Calendar as CalendarIcon,
  Filter,
  Download,
  Plus,
  Edit3,
  Trash2,
  MoreVertical,
  Activity,
  TrendingUp,
  Users,
  FileText,
  Zap,
  Maximize2,
  Minimize2,
  RefreshCw,
  Search,
  Bell,
  Archive,
  PieChart,
  BarChart3,
  Terminal,
  Workflow,
  Cpu,
  HardDrive,
  Wifi,
  Monitor
} from 'lucide-react';

interface WorkflowExecution {
  id: string;
  workflowId: string;
  name: string;
  status: 'running' | 'completed' | 'failed' | 'paused' | 'cancelled';
  startedAt: string;
  completedAt?: string;
  duration?: number;
  progress: number;
  nodeStates: Record<string, string>;
  results: Record<string, any>;
  errors: Array<{ nodeId: string; error: string; timestamp: string }>;
  metrics: {
    totalDuration: number;
    completedNodes: number;
    failedNodes: number;
    successRate: number;
  };
}

interface WorkflowDefinition {
  id: string;
  name: string;
  description: string;
  category: string;
  version: string;
  status: 'active' | 'draft' | 'deprecated';
  nodeCount: number;
  triggerCount: number;
  lastExecuted?: string;
  executionCount: number;
  successRate: number;
  averageDuration: number;
  tags: string[];
}

interface SystemMetrics {
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  networkLatency: number;
  queueLength: number;
  activeConnections: number;
}

export const WorkflowManagementPanel: React.FC = () => {
  const [workflows, setWorkflows] = useState<WorkflowDefinition[]>([]);
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics>({
    cpuUsage: 0,
    memoryUsage: 0,
    diskUsage: 0,
    networkLatency: 0,
    queueLength: 0,
    activeConnections: 0
  });
  const [loading, setLoading] = useState(false);
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000);
  const [notifications, setNotifications] = useState<Array<{ id: string; type: string; message: string; timestamp: string }>>([]);

  // Native desktop notifications
  const showDesktopNotification = useCallback((title: string, body: string, type: 'info' | 'warning' | 'error' = 'info') => {
    if (window.electronAPI) {
      window.electronAPI.showNotification({
        title,
        body,
        icon: type === 'error' ? 'error' : type === 'warning' ? 'warning' : 'info'
      });
    }
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 'r':
            e.preventDefault();
            loadData();
            break;
          case 'n':
            e.preventDefault();
            // Open new workflow dialog
            break;
          case 'f':
            e.preventDefault();
            document.getElementById('workflow-search')?.focus();
            break;
          case 'F11':
            e.preventDefault();
            setIsFullscreen(!isFullscreen);
            break;
          case 'e':
            e.preventDefault();
            exportData();
            break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isFullscreen]);

  // Auto-refresh system metrics
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      // Simulate system metrics updates
      setSystemMetrics({
        cpuUsage: Math.random() * 100,
        memoryUsage: Math.random() * 100,
        diskUsage: 65 + Math.random() * 10,
        networkLatency: 50 + Math.random() * 100,
        queueLength: Math.floor(Math.random() * 20),
        activeConnections: 5 + Math.floor(Math.random() * 15)
      });
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // Simulate API calls
      const sampleWorkflows: WorkflowDefinition[] = [
        {
          id: 'wf_001',
          name: 'Medical Consultation Analysis',
          description: 'Advanced medical transcript processing with HIPAA compliance',
          category: 'medical',
          version: '2.3.1',
          status: 'active',
          nodeCount: 12,
          triggerCount: 3,
          lastExecuted: '2024-01-15T14:30:00Z',
          executionCount: 342,
          successRate: 96.8,
          averageDuration: 4800,
          tags: ['medical', 'hipaa', 'clinical', 'ner']
        },
        {
          id: 'wf_002',
          name: 'Real-time Quality Monitor',
          description: 'Continuous quality assessment with automated alerts',
          category: 'quality',
          version: '1.8.0',
          status: 'active',
          nodeCount: 8,
          triggerCount: 5,
          lastExecuted: '2024-01-15T15:45:00Z',
          executionCount: 1247,
          successRate: 99.1,
          averageDuration: 2200,
          tags: ['quality', 'monitoring', 'alerts', 'realtime']
        },
        {
          id: 'wf_003',
          name: 'Legal Document Processing',
          description: 'Analyze legal documents with privilege detection',
          category: 'legal',
          version: '1.5.2',
          status: 'active',
          nodeCount: 15,
          triggerCount: 2,
          lastExecuted: '2024-01-15T13:20:00Z',
          executionCount: 89,
          successRate: 94.4,
          averageDuration: 7200,
          tags: ['legal', 'privilege', 'compliance', 'analysis']
        }
      ];

      const sampleExecutions: WorkflowExecution[] = [
        {
          id: 'exec_001',
          workflowId: 'wf_001',
          name: 'Medical Consultation Analysis',
          status: 'running',
          startedAt: '2024-01-15T16:00:00Z',
          progress: 73,
          nodeStates: {
            'input': 'completed',
            'transcribe': 'completed',
            'clinical_ner': 'running',
            'quality_check': 'pending',
            'hipaa_compliance': 'pending'
          },
          results: {},
          errors: [],
          metrics: {
            totalDuration: 3200,
            completedNodes: 3,
            failedNodes: 0,
            successRate: 100
          }
        },
        {
          id: 'exec_002',
          workflowId: 'wf_002',
          name: 'Real-time Quality Monitor',
          status: 'completed',
          startedAt: '2024-01-15T15:30:00Z',
          completedAt: '2024-01-15T15:37:00Z',
          duration: 420,
          progress: 100,
          nodeStates: {
            'monitor': 'completed',
            'assess': 'completed',
            'alert': 'completed',
            'report': 'completed'
          },
          results: {
            qualityScore: 94.7,
            alertsTriggered: 1,
            improvementSuggestions: 4
          },
          errors: [],
          metrics: {
            totalDuration: 420,
            completedNodes: 4,
            failedNodes: 0,
            successRate: 100
          }
        }
      ];

      setWorkflows(sampleWorkflows);
      setExecutions(sampleExecutions);

    } catch (error) {
      console.error('Failed to load workflow data:', error);
      showDesktopNotification('Error', 'Failed to load workflow data', 'error');
    } finally {
      setLoading(false);
    }
  }, [showDesktopNotification]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const exportData = useCallback(() => {
    if (window.electronAPI) {
      const data = {
        workflows: workflows,
        executions: executions,
        exportedAt: new Date().toISOString()
      };
      
      window.electronAPI.exportData('workflow-data.json', JSON.stringify(data, null, 2));
      showDesktopNotification('Export Complete', 'Workflow data exported successfully');
    }
  }, [workflows, executions, showDesktopNotification]);

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'running': return 'text-blue-500';
      case 'completed': return 'text-green-500';
      case 'failed': return 'text-red-500';
      case 'paused': return 'text-yellow-500';
      default: return 'text-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    const className = `h-4 w-4 ${getStatusColor(status)}`;
    switch (status) {
      case 'running': return <Play className={className} />;
      case 'completed': return <CheckCircle className={className} />;
      case 'failed': return <XCircle className={className} />;
      case 'paused': return <Pause className={className} />;
      default: return <Clock className={className} />;
    }
  };

  const formatDuration = (ms: number): string => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    return hours > 0 ? `${hours}h ${minutes % 60}m` : `${minutes}m ${seconds % 60}s`;
  };

  const filteredWorkflows = workflows.filter(workflow => {
    const matchesSearch = workflow.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         workflow.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         workflow.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesStatus = filterStatus === 'all' || workflow.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  const MetricCard = ({ title, value, unit, icon: Icon, color, trend }: any) => (
    <Card className="relative overflow-hidden">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <div className="flex items-baseline gap-1">
              <p className={`text-2xl font-bold ${color}`}>{value}</p>
              <span className="text-sm text-muted-foreground">{unit}</span>
            </div>
            {trend && (
              <div className="flex items-center gap-1 mt-1">
                <TrendingUp className="h-3 w-3 text-green-500" />
                <span className="text-xs text-green-500">+{trend}%</span>
              </div>
            )}
          </div>
          <div className={`p-3 rounded-lg bg-opacity-10 ${color}`}>
            <Icon className={`h-6 w-6 ${color}`} />
          </div>
        </div>
        <Progress 
          value={typeof value === 'number' ? Math.min(value, 100) : 0} 
          className="mt-2 h-1" 
        />
      </CardContent>
    </Card>
  );

  return (
    <TooltipProvider>
      <div className={`flex flex-col h-full ${isFullscreen ? 'fixed inset-0 z-50 bg-background' : ''}`}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Workflow className="h-6 w-6 text-primary" />
              <h1 className="text-xl font-semibold">Workflow Management</h1>
            </div>
            <Badge variant="outline" className="text-xs">
              {executions.filter(e => e.status === 'running').length} running
            </Badge>
          </div>

          <div className="flex items-center gap-2">
            {/* Auto-refresh toggle */}
            <div className="flex items-center gap-2">
              <Switch
                checked={autoRefresh}
                onCheckedChange={setAutoRefresh}
                id="auto-refresh"
              />
              <label htmlFor="auto-refresh" className="text-sm">Auto-refresh</label>
            </div>

            {/* Control buttons */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" size="sm" onClick={loadData} disabled={loading}>
                  <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Refresh data (Ctrl+R)</TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" size="sm" onClick={exportData}>
                  <Download className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Export data (Ctrl+E)</TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" size="sm" onClick={() => setIsFullscreen(!isFullscreen)}>
                  {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
                </Button>
              </TooltipTrigger>
              <TooltipContent>Toggle fullscreen (F11)</TooltipContent>
            </Tooltip>

            <Dialog>
              <DialogTrigger asChild>
                <Button size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  New Workflow
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-4xl">
                <DialogHeader>
                  <DialogTitle>Create New Workflow</DialogTitle>
                </DialogHeader>
                <div className="grid grid-cols-2 gap-4 p-4">
                  <Card className="cursor-pointer hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <h3 className="font-semibold mb-2">Medical Processing Template</h3>
                      <p className="text-sm text-muted-foreground">HIPAA-compliant medical transcript analysis</p>
                      <div className="flex gap-1 mt-2">
                        <Badge variant="outline" className="text-xs">Medical</Badge>
                        <Badge variant="outline" className="text-xs">HIPAA</Badge>
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="cursor-pointer hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <h3 className="font-semibold mb-2">Quality Monitoring Template</h3>
                      <p className="text-sm text-muted-foreground">Real-time quality assessment pipeline</p>
                      <div className="flex gap-1 mt-2">
                        <Badge variant="outline" className="text-xs">Quality</Badge>
                        <Badge variant="outline" className="text-xs">Monitoring</Badge>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Search and Filter Bar */}
        <div className="flex items-center gap-2 p-4 border-b bg-muted/30">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
            <Input
              id="workflow-search"
              placeholder="Search workflows, tags, descriptions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Select value={filterStatus} onValueChange={setFilterStatus}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="deprecated">Deprecated</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm">
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </Button>
        </div>

        {/* Main Content */}
        <div className="flex-1 overflow-hidden">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
            <TabsList className="mx-4 mt-4">
              <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
              <TabsTrigger value="workflows">Workflows ({workflows.length})</TabsTrigger>
              <TabsTrigger value="executions">Executions ({executions.length})</TabsTrigger>
              <TabsTrigger value="monitoring">System</TabsTrigger>
            </TabsList>

            <div className="flex-1 overflow-auto p-4">
              <TabsContent value="dashboard" className="space-y-6 mt-0">
                {/* System Metrics */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                  <MetricCard
                    title="CPU Usage"
                    value={Math.round(systemMetrics.cpuUsage)}
                    unit="%"
                    icon={Cpu}
                    color="text-blue-500"
                  />
                  <MetricCard
                    title="Memory Usage"
                    value={Math.round(systemMetrics.memoryUsage)}
                    unit="%"
                    icon={HardDrive}
                    color="text-green-500"
                  />
                  <MetricCard
                    title="Queue Length"
                    value={systemMetrics.queueLength}
                    unit="jobs"
                    icon={Activity}
                    color="text-purple-500"
                  />
                  <MetricCard
                    title="Active Connections"
                    value={systemMetrics.activeConnections}
                    unit=""
                    icon={Wifi}
                    color="text-orange-500"
                  />
                </div>

                {/* Quick Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Execution Success Rate
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-green-600">96.8%</div>
                      <p className="text-sm text-muted-foreground">Last 24 hours</p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base flex items-center gap-2">
                        <Clock className="h-4 w-4 text-blue-500" />
                        Average Duration
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-blue-600">4.2min</div>
                      <p className="text-sm text-muted-foreground">Per workflow</p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base flex items-center gap-2">
                        <Zap className="h-4 w-4 text-yellow-500" />
                        Throughput
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-yellow-600">247</div>
                      <p className="text-sm text-muted-foreground">Executions today</p>
                    </CardContent>
                  </Card>
                </div>

                {/* Recent Executions */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Activity className="h-5 w-5" />
                      Recent Executions
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <AnimatePresence>
                        {executions.slice(0, 5).map((execution, index) => (
                          <motion.div
                            key={execution.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            transition={{ delay: index * 0.1 }}
                            className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                          >
                            <div className="flex items-center gap-3">
                              {getStatusIcon(execution.status)}
                              <div>
                                <p className="font-medium text-sm">{execution.name}</p>
                                <p className="text-xs text-muted-foreground">
                                  Started {new Date(execution.startedAt).toLocaleTimeString()}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <Badge variant="outline" className="text-xs">
                                {execution.status}
                              </Badge>
                              {execution.status === 'running' && (
                                <Progress value={execution.progress} className="w-20 h-2" />
                              )}
                              <Button variant="ghost" size="sm">
                                <Eye className="h-3 w-3" />
                              </Button>
                            </div>
                          </motion.div>
                        ))}
                      </AnimatePresence>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="workflows" className="space-y-4 mt-0">
                <div className="grid gap-4">
                  <AnimatePresence>
                    {filteredWorkflows.map((workflow, index) => (
                      <motion.div
                        key={workflow.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.05 }}
                      >
                        <Card className="hover:shadow-md transition-shadow">
                          <CardContent className="p-4">
                            <div className="flex items-center justify-between mb-3">
                              <div className="flex items-center gap-3">
                                <div className={`w-3 h-3 rounded-full ${
                                  workflow.status === 'active' ? 'bg-green-500' :
                                  workflow.status === 'draft' ? 'bg-yellow-500' : 'bg-gray-400'
                                }`} />
                                <div>
                                  <h3 className="font-semibold">{workflow.name}</h3>
                                  <p className="text-sm text-muted-foreground">v{workflow.version}</p>
                                </div>
                                <Badge variant="outline" className="text-xs">
                                  {workflow.category}
                                </Badge>
                              </div>
                              <div className="flex items-center gap-1">
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <Button variant="ghost" size="sm">
                                      <Play className="h-4 w-4" />
                                    </Button>
                                  </TooltipTrigger>
                                  <TooltipContent>Execute workflow</TooltipContent>
                                </Tooltip>
                                <Button variant="ghost" size="sm">
                                  <Edit3 className="h-4 w-4" />
                                </Button>
                                <Button variant="ghost" size="sm">
                                  <Settings className="h-4 w-4" />
                                </Button>
                                <Button variant="ghost" size="sm">
                                  <MoreVertical className="h-4 w-4" />
                                </Button>
                              </div>
                            </div>
                            
                            <p className="text-sm text-muted-foreground mb-3">
                              {workflow.description}
                            </p>

                            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm mb-3">
                              <div className="flex items-center gap-2">
                                <Workflow className="h-3 w-3 text-muted-foreground" />
                                <span className="text-muted-foreground">Nodes:</span>
                                <span className="font-medium">{workflow.nodeCount}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <BarChart3 className="h-3 w-3 text-muted-foreground" />
                                <span className="text-muted-foreground">Executions:</span>
                                <span className="font-medium">{workflow.executionCount}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <TrendingUp className="h-3 w-3 text-muted-foreground" />
                                <span className="text-muted-foreground">Success:</span>
                                <span className="font-medium">{workflow.successRate}%</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <Clock className="h-3 w-3 text-muted-foreground" />
                                <span className="text-muted-foreground">Avg Duration:</span>
                                <span className="font-medium">{formatDuration(workflow.averageDuration)}</span>
                              </div>
                            </div>

                            <div className="flex flex-wrap gap-1">
                              {workflow.tags.map(tag => (
                                <Badge key={tag} variant="secondary" className="text-xs">
                                  {tag}
                                </Badge>
                              ))}
                            </div>
                          </CardContent>
                        </Card>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              </TabsContent>

              <TabsContent value="executions" className="space-y-4 mt-0">
                <div className="grid gap-4">
                  <AnimatePresence>
                    {executions.map((execution, index) => (
                      <motion.div
                        key={execution.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                      >
                        <Card className="hover:shadow-md transition-shadow">
                          <CardContent className="p-4">
                            <div className="flex items-center justify-between mb-4">
                              <div className="flex items-center gap-3">
                                {getStatusIcon(execution.status)}
                                <div>
                                  <h3 className="font-semibold">{execution.name}</h3>
                                  <p className="text-sm text-muted-foreground">ID: {execution.id}</p>
                                </div>
                              </div>
                              <div className="flex items-center gap-2">
                                <Badge variant="outline" className={getStatusColor(execution.status)}>
                                  {execution.status}
                                </Badge>
                                {execution.status === 'running' && (
                                  <div className="flex items-center gap-2">
                                    <Button variant="outline" size="sm">
                                      <Pause className="h-4 w-4" />
                                    </Button>
                                    <Button variant="outline" size="sm">
                                      <Square className="h-4 w-4" />
                                    </Button>
                                  </div>
                                )}
                                <Button variant="ghost" size="sm">
                                  <Eye className="h-4 w-4" />
                                </Button>
                              </div>
                            </div>

                            {execution.status === 'running' && (
                              <div className="mb-4">
                                <div className="flex items-center justify-between mb-2">
                                  <span className="text-sm text-muted-foreground">Progress</span>
                                  <span className="text-sm font-medium">{execution.progress}%</span>
                                </div>
                                <Progress value={execution.progress} className="h-2" />
                                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                                  <span>{execution.metrics.completedNodes} nodes completed</span>
                                  <span>Running for {formatDuration(Date.now() - new Date(execution.startedAt).getTime())}</span>
                                </div>
                              </div>
                            )}

                            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                              <div>
                                <span className="text-muted-foreground">Started:</span>
                                <p className="font-medium">
                                  {new Date(execution.startedAt).toLocaleString()}
                                </p>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Duration:</span>
                                <p className="font-medium">
                                  {execution.duration ? formatDuration(execution.duration) : 
                                   formatDuration(Date.now() - new Date(execution.startedAt).getTime())}
                                </p>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Nodes:</span>
                                <p className="font-medium">
                                  {execution.metrics.completedNodes} / {Object.keys(execution.nodeStates).length}
                                </p>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Success Rate:</span>
                                <p className="font-medium">{execution.metrics.successRate}%</p>
                              </div>
                            </div>

                            {execution.errors.length > 0 && (
                              <Alert className="mt-4">
                                <AlertTriangle className="h-4 w-4" />
                                <AlertTitle>Execution Errors</AlertTitle>
                                <AlertDescription>
                                  {execution.errors.length} error(s) occurred during execution
                                </AlertDescription>
                              </Alert>
                            )}
                          </CardContent>
                        </Card>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              </TabsContent>

              <TabsContent value="monitoring" className="space-y-6 mt-0">
                {/* System Health Overview */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <MetricCard
                    title="CPU Usage"
                    value={Math.round(systemMetrics.cpuUsage)}
                    unit="%"
                    icon={Cpu}
                    color="text-blue-500"
                    trend={2.3}
                  />
                  <MetricCard
                    title="Memory Usage"
                    value={Math.round(systemMetrics.memoryUsage)}
                    unit="%"
                    icon={HardDrive}
                    color="text-green-500"
                    trend={-1.2}
                  />
                  <MetricCard
                    title="Network Latency"
                    value={Math.round(systemMetrics.networkLatency)}
                    unit="ms"
                    icon={Wifi}
                    color="text-purple-500"
                  />
                  <MetricCard
                    title="Disk Usage"
                    value={Math.round(systemMetrics.diskUsage)}
                    unit="%"
                    icon={Monitor}
                    color="text-orange-500"
                  />
                </div>

                {/* Performance Alerts */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <AlertTriangle className="h-5 w-5" />
                      System Alerts
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-start gap-3 p-3 bg-yellow-50 dark:bg-yellow-950/20 rounded-lg">
                        <AlertTriangle className="h-4 w-4 text-yellow-500 mt-0.5" />
                        <div className="flex-1">
                          <p className="text-sm font-medium">High Memory Usage Detected</p>
                          <p className="text-xs text-muted-foreground">Memory usage above 85% threshold</p>
                          <p className="text-xs text-muted-foreground">3 minutes ago</p>
                        </div>
                      </div>
                      <div className="flex items-start gap-3 p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
                        <Monitor className="h-4 w-4 text-blue-500 mt-0.5" />
                        <div className="flex-1">
                          <p className="text-sm font-medium">Performance Optimization Complete</p>
                          <p className="text-xs text-muted-foreground">System performance improved by 15%</p>
                          <p className="text-xs text-muted-foreground">1 hour ago</p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Process Monitor */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Terminal className="h-5 w-5" />
                      Active Processes
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between p-2 border rounded">
                        <div className="flex items-center gap-3">
                          <div className="w-2 h-2 bg-green-500 rounded-full" />
                          <span className="font-medium text-sm">workflow-engine</span>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <span>CPU: 12.3%</span>
                          <span>RAM: 256MB</span>
                          <span>PID: 1234</span>
                        </div>
                      </div>
                      <div className="flex items-center justify-between p-2 border rounded">
                        <div className="flex items-center gap-3">
                          <div className="w-2 h-2 bg-green-500 rounded-full" />
                          <span className="font-medium text-sm">quality-monitor</span>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <span>CPU: 5.7%</span>
                          <span>RAM: 128MB</span>
                          <span>PID: 5678</span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </div>
          </Tabs>
        </div>
      </div>
    </TooltipProvider>
  );
};