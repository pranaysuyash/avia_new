import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { AppShell, PageContainer } from '@/components/layout';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ThemeProvider } from '@/lib/theme-provider';
import { queryClient } from '@/lib/api-client';
import { useDashboard } from '@/hooks/useDashboard';
import { useAuth } from '@/hooks/useAuth';
import { 
  Upload, Brain, Mic, Video, Stethoscope, Scale, TrendingUp,
  FileText, Briefcase, Target, Eye, Headphones, FileSearch,
  AudioLines, CheckCircle2, Sparkles, Activity, ArrowRight,
  Zap, Play, Loader2, AlertCircle
} from 'lucide-react';

function DashboardContent() {
  const { isAuthenticated, isLoading: authLoading, isDevelopmentMode } = useAuth();
  const { 
    stats, 
    recentJobs, 
    aiEngines, 
    systemStatus,
    isLoading: dashboardLoading,
    error: dashboardError 
  } = useDashboard();

  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="p-8 max-w-md">
          <div className="text-center">
            <AlertCircle className="w-12 h-12 text-warning mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Authentication Required</h2>
            <p className="text-muted-foreground mb-4">Please log in to access the dashboard.</p>
            <Button onClick={() => window.location.href = '/login'}>
              Go to Login
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  // Use real data from backend or fallback to loading state
  const platformStats = stats ? [
    { 
      label: 'Media Files Processed', 
      value: stats.totalFiles.toLocaleString(), 
      change: stats.trends.files.change, 
      trend: stats.trends.files.trend,
      icon: FileText, 
      color: 'blue' 
    },
    { 
      label: 'AI Processing Time', 
      value: stats.totalProcessingTime, 
      change: stats.trends.processing.change, 
      trend: stats.trends.processing.trend,
      icon: Brain, 
      color: 'purple' 
    },
    { 
      label: 'System Accuracy', 
      value: `${stats.accuracyRate}%`, 
      change: stats.trends.accuracy.change, 
      trend: stats.trends.accuracy.trend,
      icon: Target, 
      color: 'green' 
    },
    { 
      label: 'Storage Used', 
      value: stats.storageUsed, 
      change: stats.trends.storage.change, 
      trend: stats.trends.storage.trend,
      icon: Briefcase, 
      color: 'orange' 
    }
  ] : [];

  // Map AI engines to display format
  const engineIcons: Record<string, any> = {
    'transcription': Mic,
    'video': Video,
    'medical': Stethoscope,
    'legal': Scale,
    'audio': Headphones,
    'emotion': Eye,
    'entity': FileSearch,
    'realtime': AudioLines,
  };

  const engineColors = ['blue', 'purple', 'green', 'orange', 'cyan', 'pink', 'indigo', 'teal'];
  
  const displayEngines = aiEngines?.map((engine, index) => ({
    name: engine.name,
    icon: engineIcons[engine.type] || Brain,
    status: engine.status,
    jobs: engine.activeJobs,
    color: engineColors[index % engineColors.length],
  })) || [];

  // Map job types to icons and colors
  const jobTypeIcons: Record<string, any> = {
    'audio': Headphones,
    'video': Video,
    'document': FileText,
    'image': Eye,
  };

  const jobTypeColors: Record<string, string> = {
    'audio': 'blue',
    'video': 'purple',
    'document': 'green',
    'image': 'orange',
  };

  const displayJobs = recentJobs?.map(job => ({
    name: job.name,
    type: job.type.charAt(0).toUpperCase() + job.type.slice(1),
    status: job.status,
    accuracy: job.accuracy,
    duration: job.duration,
    aiFeatures: job.aiFeatures,
    icon: jobTypeIcons[job.type] || FileText,
    color: jobTypeColors[job.type] || 'blue',
  })) || [];

  const getColorClasses = (color: string) => {
    const colors: Record<string, string> = {
      blue: 'from-blue-500 to-blue-600',
      purple: 'from-purple-500 to-purple-600',
      green: 'from-green-500 to-green-600',
      orange: 'from-orange-500 to-orange-600',
      cyan: 'from-cyan-500 to-cyan-600',
      pink: 'from-pink-500 to-pink-600',
      indigo: 'from-indigo-500 to-indigo-600',
      teal: 'from-teal-500 to-teal-600'
    };
    return colors[color] || colors.blue;
  };

  if (dashboardError) {
    return (
      <AppShell>
        <PageContainer title="Dashboard">
          <Card className="p-8">
            <div className="text-center">
              <AlertCircle className="w-12 h-12 text-destructive mx-auto mb-4" />
              <h2 className="text-xl font-semibold mb-2">Failed to Load Dashboard</h2>
              <p className="text-muted-foreground mb-4">
                {dashboardError instanceof Error ? dashboardError.message : 'An error occurred'}
              </p>
              <Button onClick={() => window.location.reload()}>
                Retry
              </Button>
            </div>
          </Card>
        </PageContainer>
      </AppShell>
    );
  }

  return (
    <AppShell>
        <PageContainer
        title="Dashboard"
        description="Enterprise AI Media Processing & Management Platform"
        breadcrumbs={[{ label: 'Dashboard' }]}
        actions={
          <div className="flex items-center gap-2">
            {isDevelopmentMode && (
              <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">
                Development Mode
              </Badge>
            )}
            <Badge variant={systemStatus?.overall === 'healthy' ? 'default' : 'destructive'}>
              {systemStatus?.overall === 'healthy' ? 'All Systems Online' : 
               systemStatus?.overall === 'degraded' ? 'System Degraded' :
               systemStatus?.overall === 'down' ? 'System Down' : 'Checking...'}
            </Badge>
            <Badge variant="secondary">
              {stats?.activeJobs || 0} Active Jobs
            </Badge>
            {dashboardLoading && (
              <Badge variant="outline">
                <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                Loading...
              </Badge>
            )}
          </div>
        }
      >
        {/* Platform Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {dashboardLoading ? (
            // Loading skeleton
            Array.from({ length: 4 }).map((_, idx) => (
              <Card key={idx} className="p-6">
                <div className="animate-pulse">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 bg-muted rounded-xl"></div>
                    <div className="w-16 h-4 bg-muted rounded"></div>
                  </div>
                  <div className="w-20 h-8 bg-muted rounded mb-2"></div>
                  <div className="w-32 h-4 bg-muted rounded"></div>
                </div>
              </Card>
            ))
          ) : (
            platformStats.map((stat, idx) => (
              <Card key={idx} className="p-6 hover:shadow-lg transition-all">
                <div className="flex items-center justify-between mb-4">
                  <div className={`p-3 rounded-xl bg-gradient-to-r ${getColorClasses(stat.color)}`}>
                    <stat.icon className="w-6 h-6 text-white" />
                  </div>
                  <div className={`flex items-center space-x-1 text-sm font-semibold ${
                    stat.trend === 'up' ? 'text-success' : 'text-destructive'
                  }`}>
                    {stat.trend === 'up' ? (
                      <TrendingUp className="w-3 h-3" />
                    ) : (
                      <TrendingUp className="w-3 h-3 rotate-180" />
                    )}
                    <span>{stat.change}</span>
                  </div>
                </div>
                <div className="text-3xl font-bold mb-2">{stat.value}</div>
                <div className="text-sm text-muted-foreground">{stat.label}</div>
              </Card>
            ))
          )}
        </div>

        {/* AI Processing Engines */}
        <Card className="mb-8">
          <div className="p-6 border-b border-border">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold flex items-center">
                  <Sparkles className="w-5 h-5 mr-2 text-purple-600" />
                  AI Processing Engines
                </h3>
                <p className="text-sm text-muted-foreground mt-1">Real-time status of all AI capabilities</p>
              </div>
              <Button variant="outline" size="sm">
                View All Models
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
          
          <div className="p-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {dashboardLoading ? (
                // Loading skeleton for AI engines
                Array.from({ length: 8 }).map((_, idx) => (
                  <div key={idx} className="p-4 rounded-lg border border-border">
                    <div className="animate-pulse">
                      <div className="flex items-center justify-between mb-3">
                        <div className="w-8 h-8 bg-muted rounded-lg"></div>
                        <div className="w-16 h-4 bg-muted rounded"></div>
                      </div>
                      <div className="w-24 h-4 bg-muted rounded mb-1"></div>
                      <div className="w-20 h-3 bg-muted rounded"></div>
                    </div>
                  </div>
                ))
              ) : (
                displayEngines.map((engine, idx) => (
                  <div key={idx} className="p-4 rounded-lg border border-border hover:border-primary/50 transition-colors hover:shadow-md">
                    <div className="flex items-center justify-between mb-3">
                      <div className={`p-2 rounded-lg bg-gradient-to-r ${getColorClasses(engine.color)}`}>
                        <engine.icon className="w-5 h-5 text-white" />
                      </div>
                      <div className="flex items-center space-x-1">
                        {engine.status === 'active' ? (
                          <CheckCircle2 className="w-4 h-4 text-success" />
                        ) : engine.status === 'error' ? (
                          <AlertCircle className="w-4 h-4 text-destructive" />
                        ) : (
                          <div className="w-4 h-4 rounded-full bg-warning"></div>
                        )}
                        <span className={`text-xs font-medium ${
                          engine.status === 'active' ? 'text-success' :
                          engine.status === 'error' ? 'text-destructive' : 'text-warning'
                        }`}>
                          {engine.status}
                        </span>
                      </div>
                    </div>
                    <div className="text-sm font-semibold mb-1">{engine.name}</div>
                    <div className="text-xs text-muted-foreground">{engine.jobs} active jobs</div>
                  </div>
                ))
              )}
            </div>
          </div>
        </Card>

        {/* Quick Actions */}
        <Card className="p-6 mb-8">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <Zap className="w-5 h-5 mr-2 text-primary" />
            Quick Actions
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Button className="h-20 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 flex-col">
              <Upload className="w-6 h-6 mb-2" />
              <span className="text-sm">Media Ingestion</span>
            </Button>
            
            <Button variant="outline" className="h-20 border-2 flex-col hover:bg-purple-50 hover:border-purple-300">
              <Mic className="w-6 h-6 mb-2 text-purple-600" />
              <span className="text-sm">Live AI Processing</span>
            </Button>
            
            <Button variant="outline" className="h-20 border-2 flex-col hover:bg-green-50 hover:border-green-300">
              <Brain className="w-6 h-6 mb-2 text-green-600" />
              <span className="text-sm">AI Model Hub</span>
            </Button>
            
            <Button variant="outline" className="h-20 border-2 flex-col hover:bg-orange-50 hover:border-orange-300">
              <TrendingUp className="w-6 h-6 mb-2 text-orange-600" />
              <span className="text-sm">Analytics</span>
            </Button>
          </div>
        </Card>

        {/* Recent AI Processing */}
        <Card>
          <div className="p-6 border-b border-border">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold flex items-center">
                  <Activity className="w-5 h-5 mr-2 text-primary" />
                  Recent AI Processing
                </h3>
                <p className="text-sm text-muted-foreground mt-1">Enterprise-grade AI processing with advanced capabilities</p>
              </div>
              <Button variant="outline" size="sm">
                View Processing Queue
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
          
          <div className="divide-y divide-border">
            {dashboardLoading ? (
              // Loading skeleton for recent processing
              Array.from({ length: 3 }).map((_, idx) => (
                <div key={idx} className="p-6">
                  <div className="animate-pulse">
                    <div className="flex items-start space-x-4">
                      <div className="w-12 h-12 bg-muted rounded-xl"></div>
                      <div className="flex-1">
                        <div className="w-48 h-4 bg-muted rounded mb-2"></div>
                        <div className="w-32 h-3 bg-muted rounded mb-2"></div>
                        <div className="flex gap-2">
                          <div className="w-20 h-6 bg-muted rounded"></div>
                          <div className="w-24 h-6 bg-muted rounded"></div>
                          <div className="w-16 h-6 bg-muted rounded"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            ) : displayJobs.length === 0 ? (
              <div className="p-8 text-center">
                <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Recent Processing</h3>
                <p className="text-muted-foreground">Upload media files to start AI processing.</p>
              </div>
            ) : (
              displayJobs.map((item, idx) => (
              <div key={idx} className="p-6 hover:bg-muted/50 transition-colors">
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  <div className="flex items-start space-x-4 flex-1">
                    <div className={`p-3 rounded-xl bg-gradient-to-r ${getColorClasses(item.color)} flex-shrink-0`}>
                      <item.icon className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-3 mb-1 flex-wrap">
                        <div className="font-semibold truncate">{item.name}</div>
                        <Badge variant="secondary">{item.type}</Badge>
                      </div>
                      <div className="text-sm text-muted-foreground mb-2">{item.duration} • {item.status}</div>
                      <div className="flex flex-wrap gap-1">
                        {item.aiFeatures.map((feature, featureIdx) => (
                          <Badge key={featureIdx} variant="outline" className="text-xs">
                            {feature}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-6 flex-shrink-0">
                    {item.accuracy > 0 && (
                      <div className="flex items-center space-x-3">
                        <div className="text-right">
                          <div className="text-sm font-semibold">Accuracy</div>
                          <div className="text-xs text-muted-foreground">AI Confidence</div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <div className="w-24 bg-muted rounded-full h-2">
                            <div 
                              className={`h-2 rounded-full ${
                                item.accuracy > 98 ? 'bg-success' :
                                item.accuracy > 95 ? 'bg-primary' : 'bg-warning'
                              }`}
                              style={{ width: `${item.accuracy}%` }}
                            ></div>
                          </div>
                          <span className={`text-sm font-bold ${
                            item.accuracy > 98 ? 'text-success' :
                            item.accuracy > 95 ? 'text-primary' : 'text-warning'
                          }`}>{item.accuracy}%</span>
                        </div>
                      </div>
                    )}
                    
                    {item.status === 'processing' && (
                      <Loader2 className="w-5 h-5 text-primary animate-spin" />
                    )}
                    
                    <div className="flex space-x-2">
                      <Button size="sm" variant="outline">
                        <Play className="w-3 h-3" />
                      </Button>
                      <Button size="sm" variant="outline">
                        <Eye className="w-3 h-3" />
                      </Button>
                      <Button size="sm" variant="outline">
                        <FileText className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
              ))
            )}
          </div>
        </Card>
      </PageContainer>
    </AppShell>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="system" storageKey="frontend-v2-theme">
        <DashboardContent />
        <ReactQueryDevtools initialIsOpen={false} />
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
