import { AppShell, PageContainer } from '@/components/layout';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ThemeProvider } from '@/lib/theme-provider';
import { 
  Upload, Brain, Mic, Video, Stethoscope, Scale, TrendingUp,
  FileText, Briefcase, Target, Eye, Headphones, FileSearch,
  AudioLines, CheckCircle2, Sparkles, Activity, ArrowRight,
  Zap, Play, Loader2
} from 'lucide-react';
import { useState, useEffect } from 'react';

function App() {
  const [apiStatus, setApiStatus] = useState<'online' | 'offline' | 'checking'>('checking');

  // Check API health on mount
  useEffect(() => {
    const checkApiHealth = async () => {
      try {
        const response = await fetch('/api/health');
        setApiStatus(response.ok ? 'online' : 'offline');
      } catch {
        setApiStatus('offline');
      }
    };
    checkApiHealth();
    const interval = setInterval(checkApiHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const platformStats = [
    { label: 'Media Files Processed', value: '47,234', change: '+23%', icon: FileText, color: 'blue' },
    { label: 'AI Processing Hours', value: '12,847', change: '+18%', icon: Brain, color: 'purple' },
    { label: 'Enterprise Clients', value: '342', change: '+24%', icon: Briefcase, color: 'green' },
    { label: 'System Accuracy', value: '99.3%', change: '+1.2%', icon: Target, color: 'orange' }
  ];

  const aiEngines = [
    { name: 'Speech-to-Text', icon: Mic, status: 'active', jobs: 45, color: 'blue' },
    { name: 'Video Intelligence', icon: Video, status: 'active', jobs: 23, color: 'purple' },
    { name: 'Medical AI (HIPAA)', icon: Stethoscope, status: 'active', jobs: 18, color: 'green' },
    { name: 'Legal AI', icon: Scale, status: 'active', jobs: 12, color: 'orange' },
    { name: 'Multi-Channel Audio', icon: Headphones, status: 'active', jobs: 34, color: 'cyan' },
    { name: 'Emotion Detection', icon: Eye, status: 'active', jobs: 28, color: 'pink' },
    { name: 'Entity Extraction', icon: FileSearch, status: 'active', jobs: 56, color: 'indigo' },
    { name: 'Real-time Transcription', icon: AudioLines, status: 'active', jobs: 15, color: 'teal' }
  ];

  const recentProcessing = [
    { 
      name: 'Board_Meeting_Q4_2024.mp4', 
      type: 'Business Intelligence', 
      status: 'completed', 
      accuracy: 99.1, 
      duration: '1:23:45',
      aiFeatures: ['Sentiment Analysis', 'Action Items', 'Key Insights', 'Speaker Diarization'],
      icon: Briefcase,
      color: 'purple'
    },
    { 
      name: 'Medical_Consultation_Case_447.wav', 
      type: 'Medical AI (HIPAA)', 
      status: 'processing', 
      accuracy: 0, 
      duration: '45:32',
      aiFeatures: ['Clinical NER', 'HIPAA Compliance', 'Medical Terminology'],
      icon: Stethoscope,
      color: 'green'
    },
    { 
      name: 'Legal_Deposition_2024_03.mp4', 
      type: 'Legal AI', 
      status: 'completed', 
      accuracy: 98.7, 
      duration: '2:18:45',
      aiFeatures: ['Legal Entity Extraction', 'Compliance Check', 'Redaction'],
      icon: Scale,
      color: 'blue'
    },
    { 
      name: 'Multi_Speaker_Conference.wav', 
      type: 'Advanced Audio', 
      status: 'completed', 
      accuracy: 97.9, 
      duration: '56:42',
      aiFeatures: ['8-Channel Processing', 'Spatial Audio', 'Voice Profiling'],
      icon: Headphones,
      color: 'orange'
    }
  ];

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

  return (
    <ThemeProvider defaultTheme="system" storageKey="frontend-v2-theme">
      <AppShell>
        <PageContainer
        title="Dashboard"
        description="Enterprise AI Media Processing & Management Platform"
        breadcrumbs={[{ label: 'Dashboard' }]}
        actions={
          <div className="flex items-center gap-2">
            <Badge variant={apiStatus === 'online' ? 'default' : 'destructive'}>
              {apiStatus === 'online' ? 'All Systems Online' : 
               apiStatus === 'offline' ? 'API Offline' : 'Checking...'}
            </Badge>
            <Badge variant="secondary">
              {aiEngines.reduce((sum, eng) => sum + eng.jobs, 0)} AI Jobs
            </Badge>
          </div>
        }
      >
        {/* Platform Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {platformStats.map((stat, idx) => (
            <Card key={idx} className="p-6 hover:shadow-lg transition-all">
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-xl bg-gradient-to-r ${getColorClasses(stat.color)}`}>
                  <stat.icon className="w-6 h-6 text-white" />
                </div>
                <div className="flex items-center space-x-1 text-success text-sm font-semibold">
                  <TrendingUp className="w-3 h-3" />
                  <span>{stat.change}</span>
                </div>
              </div>
              <div className="text-3xl font-bold mb-2">{stat.value}</div>
              <div className="text-sm text-muted-foreground">{stat.label}</div>
            </Card>
          ))}
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
              {aiEngines.map((engine, idx) => (
                <div key={idx} className="p-4 rounded-lg border border-border hover:border-primary/50 transition-colors hover:shadow-md">
                  <div className="flex items-center justify-between mb-3">
                    <div className={`p-2 rounded-lg bg-gradient-to-r ${getColorClasses(engine.color)}`}>
                      <engine.icon className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex items-center space-x-1">
                      <CheckCircle2 className="w-4 h-4 text-success" />
                      <span className="text-xs text-success font-medium">{engine.status}</span>
                    </div>
                  </div>
                  <div className="text-sm font-semibold mb-1">{engine.name}</div>
                  <div className="text-xs text-muted-foreground">{engine.jobs} active jobs</div>
                </div>
              ))}
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
            {recentProcessing.map((item, idx) => (
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
            ))}
          </div>
        </Card>
      </PageContainer>
    </AppShell>
    </ThemeProvider>
  );
}

export default App;
