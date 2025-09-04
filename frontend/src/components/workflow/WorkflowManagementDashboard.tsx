/**
 * Workflow Management Dashboard
 * Comprehensive React dashboard for managing enterprise workflows
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import ShareViewButton from '../../../components/shared/ShareViewButton';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Calendar, dateFnsLocalizer } from 'react-big-calendar';
import { format, parse, startOfWeek, getDay } from 'date-fns';
import { enUS } from 'date-fns/locale';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
} from 'chart.js';
import { Line, Pie } from 'react-chartjs-2';
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
  Zap
} from 'lucide-react';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

// Calendar localizer
const locales = {
  'en-US': enUS,
};

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales,
});

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
}

interface WorkflowSchedule {
  id: string;
  workflowId: string;
  workflowName: string;
  cronExpression: string;
  timezone: string;
  nextRunTime: string;
  lastRunTime?: string;
  isActive: boolean;
}

interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  estimatedTime: string;
  popularity: number;
  tags: string[];
}

export const WorkflowManagementDashboard: React.FC = () => {
  const [workflows, setWorkflows] = useState<WorkflowDefinition[]>([]);
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [schedules, setSchedules] = useState<WorkflowSchedule[]>([]);
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [activeTab, setActiveTab] = useState('overview');

  // Sample data for demonstration
  useEffect(() => {
    const sampleWorkflows: WorkflowDefinition[] = [
      {
        id: 'wf_001',
        name: 'Medical Consultation Processing',
        description: 'Process medical consultation transcripts with clinical analysis',
        category: 'medical',
        version: '2.1.0',
        status: 'active',
        nodeCount: 8,
        triggerCount: 2,
        lastExecuted: '2024-01-15T14:30:00Z',
        executionCount: 142,
        successRate: 94.5,
        averageDuration: 4200
      },
      {
        id: 'wf_002',
        name: 'Quality Monitoring Pipeline',
        description: 'Continuous quality assessment and alerting',
        category: 'quality',
        version: '1.5.0',
        status: 'active',
        nodeCount: 12,
        triggerCount: 3,
        lastExecuted: '2024-01-15T15:45:00Z',
        executionCount: 87,
        successRate: 98.2,
        averageDuration: 2800
      },
      {
        id: 'wf_003',
        name: 'Meeting Minutes Automation',
        description: 'Extract action items and generate meeting summaries',
        category: 'business',
        version: '1.0.0',
        status: 'draft',
        nodeCount: 6,
        triggerCount: 1,
        executionCount: 23,
        successRate: 87.0,
        averageDuration: 3200
      }
    ];

    const sampleExecutions: WorkflowExecution[] = [
      {
        id: 'exec_001',
        workflowId: 'wf_001',
        name: 'Medical Consultation Processing',
        status: 'running',
        startedAt: '2024-01-15T16:00:00Z',
        progress: 65,
        nodeStates: {
          'input': 'completed',
          'transcribe': 'completed',
          'clinical_ner': 'running',
          'quality_check': 'pending'
        },
        results: {},
        errors: [],
        metrics: {
          totalDuration: 2100,
          completedNodes: 3,
          failedNodes: 0,
          successRate: 100
        }
      },
      {
        id: 'exec_002',
        workflowId: 'wf_002',
        name: 'Quality Monitoring Pipeline',
        status: 'completed',
        startedAt: '2024-01-15T15:30:00Z',
        completedAt: '2024-01-15T15:47:00Z',
        duration: 1020,
        progress: 100,
        nodeStates: {
          'monitor': 'completed',
          'assess': 'completed',
          'alert': 'completed'
        },
        results: {
          qualityScore: 92.3,
          alertsTriggered: 0,
          recommendationsGenerated: 3
        },
        errors: [],
        metrics: {
          totalDuration: 1020,
          completedNodes: 3,
          failedNodes: 0,
          successRate: 100
        }
      }
    ];

    setWorkflows(sampleWorkflows);
    setExecutions(sampleExecutions);

    const sampleSchedules: WorkflowSchedule[] = [
      {
        id: 'sched_001',
        workflowId: 'wf_002',
        workflowName: 'Quality Monitoring Pipeline',
        cronExpression: '0 */6 * * *',
        timezone: 'UTC',
        nextRunTime: '2024-01-15T18:00:00Z',
        lastRunTime: '2024-01-15T12:00:00Z',
        isActive: true
      }
    ];

    setSchedules(sampleSchedules);

    const sampleTemplates: WorkflowTemplate[] = [
      {
        id: 'tmpl_001',
        name: 'Basic Audio Processing',
        description: 'Simple audio transcription and enhancement pipeline',
        category: 'audio',
        difficulty: 'beginner',
        estimatedTime: '5-10 minutes',
        popularity: 89,
        tags: ['audio', 'transcription', 'basic']
      },
      {
        id: 'tmpl_002',
        name: 'Medical Transcript Analysis',
        description: 'Advanced medical transcript processing with clinical insights',
        category: 'medical',
        difficulty: 'advanced',
        estimatedTime: '15-30 minutes',
        popularity: 76,
        tags: ['medical', 'clinical', 'hipaa', 'advanced']
      }
    ];

    setTemplates(sampleTemplates);
  }, []);

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'completed':
        return 'default';
      case 'running':
        return 'secondary';
      case 'failed':
        return 'destructive';
      case 'paused':
        return 'outline';
      default:
        return 'secondary';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4" />;
      case 'running':
        return <Play className="h-4 w-4" />;
      case 'failed':
        return <XCircle className="h-4 w-4" />;
      case 'paused':
        return <Pause className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  const formatDuration = (milliseconds: number): string => {
    const seconds = Math.floor(milliseconds / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  };

  const executionMetricsChartData = {
    labels: ['Jan 10', 'Jan 11', 'Jan 12', 'Jan 13', 'Jan 14', 'Jan 15'],
    datasets: [
      {
        label: 'Successful Executions',
        data: [12, 15, 8, 20, 18, 25],
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        tension: 0.4
      },
      {
        label: 'Failed Executions',
        data: [1, 2, 0, 3, 1, 2],
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        tension: 0.4
      }
    ]
  };

  const workflowDistributionData = {
    labels: ['Medical', 'Quality', 'Business', 'Audio', 'Research'],
    datasets: [{
      data: [35, 25, 20, 15, 5],
      backgroundColor: [
        'rgba(59, 130, 246, 0.8)',
        'rgba(34, 197, 94, 0.8)',
        'rgba(251, 191, 36, 0.8)',
        'rgba(168, 85, 247, 0.8)',
        'rgba(239, 68, 68, 0.8)'
      ],
      borderWidth: 2
    }]
  };

  const filteredWorkflows = workflows.filter(workflow => {
    const matchesSearch = workflow.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         workflow.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = filterStatus === 'all' || workflow.status === filterStatus;
    const matchesCategory = filterCategory === 'all' || workflow.category === filterCategory;
    
    return matchesSearch && matchesStatus && matchesCategory;
  });

  const filteredExecutions = executions.filter(execution => {
    const matchesSearch = execution.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = filterStatus === 'all' || execution.status === filterStatus;
    
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Workflow Management</h1>
          <p className="text-muted-foreground">Monitor and manage enterprise workflows</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => {/* Export workflows */}}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <ShareViewButton className="px-3 py-2 rounded border" />
          <Dialog>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Create Workflow
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create New Workflow</DialogTitle>
              </DialogHeader>
              <div className="grid grid-cols-2 gap-4">
                {templates.map(template => (
                  <Card key={template.id} className="cursor-pointer hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-2">
                        <h3 className="font-semibold">{template.name}</h3>
                        <Badge variant={template.difficulty === 'beginner' ? 'default' : 
                                      template.difficulty === 'intermediate' ? 'secondary' : 'destructive'}>
                          {template.difficulty}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">{template.description}</p>
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>{template.estimatedTime}</span>
                        <span>{template.popularity}% popular</span>
                      </div>
                      <div className="flex flex-wrap gap-1 mt-2">
                        {template.tags.slice(0, 3).map(tag => (
                          <Badge key={tag} variant="outline" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Active Workflows</p>
                <p className="text-2xl font-bold">{workflows.filter(w => w.status === 'active').length}</p>
              </div>
              <Activity className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Running Executions</p>
                <p className="text-2xl font-bold">{executions.filter(e => e.status === 'running').length}</p>
              </div>
              <Play className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Success Rate</p>
                <p className="text-2xl font-bold">94.2%</p>
              </div>
              <TrendingUp className="h-8 w-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Scheduled Jobs</p>
                <p className="text-2xl font-bold">{schedules.filter(s => s.isActive).length}</p>
              </div>
              <Clock className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <div className="flex items-center justify-between">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="workflows">Workflows</TabsTrigger>
            <TabsTrigger value="executions">Executions</TabsTrigger>
            <TabsTrigger value="schedules">Schedules</TabsTrigger>
            <TabsTrigger value="monitoring">Monitoring</TabsTrigger>
          </TabsList>

          {/* Search and Filters */}
          <div className="flex items-center gap-2">
            <Input
              placeholder="Search workflows..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-64"
            />
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="running">Running</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filterCategory} onValueChange={setFilterCategory}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="medical">Medical</SelectItem>
                <SelectItem value="quality">Quality</SelectItem>
                <SelectItem value="business">Business</SelectItem>
                <SelectItem value="audio">Audio</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Execution Metrics Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Execution Trends</CardTitle>
              </CardHeader>
              <CardContent>
                <Line 
                  data={executionMetricsChartData}
                  options={{
                    responsive: true,
                    plugins: {
                      legend: {
                        position: 'top' as const,
                      }
                    },
                    scales: {
                      y: {
                        beginAtZero: true
                      }
                    }
                  }}
                />
              </CardContent>
            </Card>

            {/* Workflow Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Workflow Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <Pie 
                    data={workflowDistributionData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'bottom' as const,
                        }
                      }
                    }}
                  />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Recent Activities */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Activities</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {executions.slice(0, 5).map(execution => (
                  <div key={execution.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(execution.status)}
                      <div>
                        <p className="font-medium">{execution.name}</p>
                        <p className="text-sm text-muted-foreground">
                          Started {new Date(execution.startedAt).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <Badge variant={getStatusBadgeVariant(execution.status)}>
                        {execution.status}
                      </Badge>
                      {execution.status === 'running' && (
                        <Progress value={execution.progress} className="w-24" />
                      )}
                      <Button variant="ghost" size="sm">
                        <Eye className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="workflows" className="space-y-4">
          <div className="grid gap-4">
            {filteredWorkflows.map(workflow => (
              <Card key={workflow.id}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold">{workflow.name}</h3>
                        <Badge variant={workflow.status === 'active' ? 'default' : 'secondary'}>
                          {workflow.status}
                        </Badge>
                        <Badge variant="outline">{workflow.category}</Badge>
                      </div>
                      <p className="text-muted-foreground mb-4">{workflow.description}</p>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-muted-foreground">Nodes:</span>
                          <span className="ml-2 font-medium">{workflow.nodeCount}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Executions:</span>
                          <span className="ml-2 font-medium">{workflow.executionCount}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Success Rate:</span>
                          <span className="ml-2 font-medium">{workflow.successRate}%</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Avg Duration:</span>
                          <span className="ml-2 font-medium">{formatDuration(workflow.averageDuration)}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm">
                        <Play className="h-4 w-4 mr-2" />
                        Execute
                      </Button>
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
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="executions" className="space-y-4">
          <div className="grid gap-4">
            {filteredExecutions.map(execution => (
              <Card key={execution.id}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(execution.status)}
                      <div>
                        <h3 className="font-semibold">{execution.name}</h3>
                        <p className="text-sm text-muted-foreground">
                          ID: {execution.id}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={getStatusBadgeVariant(execution.status)}>
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
                    </div>
                  )}

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Started:</span>
                      <p className="font-medium">{new Date(execution.startedAt).toLocaleString()}</p>
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
            ))}
          </div>
        </TabsContent>

        <TabsContent value="schedules" className="space-y-4">
          <div className="grid gap-4">
            {schedules.map(schedule => (
              <Card key={schedule.id}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold">{schedule.workflowName}</h3>
                        <Badge variant={schedule.isActive ? 'default' : 'secondary'}>
                          {schedule.isActive ? 'Active' : 'Inactive'}
                        </Badge>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-muted-foreground">Schedule:</span>
                          <p className="font-medium font-mono">{schedule.cronExpression}</p>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Timezone:</span>
                          <p className="font-medium">{schedule.timezone}</p>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Next Run:</span>
                          <p className="font-medium">{new Date(schedule.nextRunTime).toLocaleString()}</p>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Last Run:</span>
                          <p className="font-medium">
                            {schedule.lastRunTime ? new Date(schedule.lastRunTime).toLocaleString() : 'Never'}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm">
                        <Edit3 className="h-4 w-4" />
                      </Button>
                      <Button variant="outline" size="sm">
                        {schedule.isActive ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="monitoring" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* System Health */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  System Health
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm">CPU Usage</span>
                  <span className="text-sm font-medium">34%</span>
                </div>
                <Progress value={34} />
                
                <div className="flex items-center justify-between">
                  <span className="text-sm">Memory Usage</span>
                  <span className="text-sm font-medium">67%</span>
                </div>
                <Progress value={67} />
                
                <div className="flex items-center justify-between">
                  <span className="text-sm">Queue Length</span>
                  <span className="text-sm font-medium">12</span>
                </div>
                <Progress value={24} />
              </CardContent>
            </Card>

            {/* Error Logs */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5" />
                  Recent Errors
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-start gap-3 p-3 bg-red-50 rounded-lg">
                    <XCircle className="h-4 w-4 text-red-500 mt-0.5" />
                    <div className="flex-1">
                      <p className="text-sm font-medium">Workflow execution failed</p>
                      <p className="text-xs text-muted-foreground">Medical Consultation Processing - Node: clinical_ner</p>
                      <p className="text-xs text-muted-foreground">2 minutes ago</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 p-3 bg-yellow-50 rounded-lg">
                    <AlertTriangle className="h-4 w-4 text-yellow-500 mt-0.5" />
                    <div className="flex-1">
                      <p className="text-sm font-medium">Performance degradation detected</p>
                      <p className="text-xs text-muted-foreground">Average execution time increased by 25%</p>
                      <p className="text-xs text-muted-foreground">15 minutes ago</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Performance Metrics */}
          <Card>
            <CardHeader>
              <CardTitle>Performance Metrics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <p className="text-2xl font-bold text-green-600">2.4s</p>
                  <p className="text-sm text-muted-foreground">Average Response Time</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-blue-600">99.2%</p>
                  <p className="text-sm text-muted-foreground">Uptime</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-purple-600">847</p>
                  <p className="text-sm text-muted-foreground">Executions Today</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
