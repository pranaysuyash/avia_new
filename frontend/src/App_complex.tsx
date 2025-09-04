import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import { QueryProvider } from './providers/QueryProvider';
import { AuthProvider } from './contexts/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Badge } from './components/ui/badge';
import { Alert, AlertDescription } from './components/ui/alert';

// Import all components
import InternationalizationProvider from './components/i18n/InternationalizationProvider';
import TranslationManager from './components/i18n/TranslationManager';
import { FileUploader } from './components/upload/FileUploader';
import { InteractiveTranscript } from './components/transcription/InteractiveTranscript';
import { ComprehensiveSearch } from './components/search/ComprehensiveSearch';
import AIAssistant from './components/ai/AIAssistant';
import { CollaborativeEditor } from './components/collaboration/CollaborativeEditor';
import AdvancedAnalytics from './components/analytics/AdvancedAnalytics';
import { AdminDashboard } from './components/admin/AdminDashboard';
import { GDPRPrivacyDashboard } from './components/privacy/GDPRPrivacyDashboard';
import { GraphQLSubscriptionManager } from './components/graphql/GraphQLSubscriptionManager';
import { CacheMetrics } from './components/analysis/CacheMetrics';
import { EnhancedAudioPlayer } from './components/audio/EnhancedAudioPlayer';
import TelemetryViewer from '../../components/shared/TelemetryViewer';
import { logUxEvent } from '../../components/shared/uxTelemetry';
import ShareViewButton from '../../components/shared/ShareViewButton';
import UserEngagementAnalytics from './components/UserEngagementAnalytics';
import ContentManagement from './components/ContentManagement';
import RealtimeTranslation from './components/translation/RealtimeTranslation';
import DistributedProcessingMonitor from './components/distributed/DistributedProcessingMonitor';

// Icons
import { 
  Upload, 
  FileText, 
  Search, 
  Globe, 
  Users, 
  BarChart3, 
  Shield, 
  Cpu,
  Settings,
  Headphones,
  Languages,
  Activity,
  Folder,
  TrendingUp
} from 'lucide-react';

interface AppState {
  currentLanguage: string;
  userId?: number;
  isAdmin: boolean;
  transcriptions: any[];
  selectedTranscription: any;
}

const App: React.FC = () => {
  const [state, setState] = useState<AppState>({
    currentLanguage: 'en',
    userId: 1, // Mock user ID
    isAdmin: true, // Mock admin status
    transcriptions: [],
    selectedTranscription: null
  });

  const [activeTab, setActiveTab] = useState('upload');
  const [showTelemetry, setShowTelemetry] = useState(false);

  useEffect(() => {
    const check = () => {
      try {
        const url = new URL(window.location.href);
        setShowTelemetry(url.searchParams.get('dev_telemetry') === '1');
        const tab = url.searchParams.get('tab');
        if (tab) setActiveTab(tab);
      } catch {}
    };
    check();
    window.addEventListener('dev_telemetry_toggle', check as any);
    return () => window.removeEventListener('dev_telemetry_toggle', check as any);
  }, []);

  // Mock function to simulate file upload completion
  const handleUploadComplete = (fileUrl: string) => {
    const newTranscription = {
      id: Date.now().toString(),
      file_url: fileUrl,
      status: 'processing',
      created_at: new Date().toISOString(),
      language: state.currentLanguage,
      content: ''
    };
    
    setState(prev => ({
      ...prev,
      transcriptions: [...prev.transcriptions, newTranscription],
      selectedTranscription: newTranscription
    }));
    
    // Simulate transcription completion
    setTimeout(() => {
      setState(prev => ({
        ...prev,
        transcriptions: prev.transcriptions.map(t => 
          t.id === newTranscription.id 
            ? { ...t, status: 'completed', content: 'This is a sample transcription content...' }
            : t
        )
      }));
    }, 3000);
    
    setActiveTab('transcriptions');
  };

  return (
    <QueryProvider>
      <AuthProvider>
        <InternationalizationProvider>
          <Router>
            <div className="min-h-screen bg-gray-50">
            {/* Header */}
          <header className="bg-white border-b">
            <div className="container mx-auto px-4 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <h1 className="text-2xl font-bold">Transcription Platform</h1>
                  <Badge variant="secondary">i18n Enabled</Badge>
                </div>
                
            <div className="flex items-center space-x-2">
              <TranslationManager />
              <Button variant="outline" size="sm">
                <Globe className="h-4 w-4 mr-2" />
                {state.currentLanguage.toUpperCase()}
              </Button>
              <ShareViewButton
                className="px-3 py-2 rounded-lg border hover:bg-gray-50 dark:hover:bg-gray-700"
                extraParams={{ tab: activeTab }}
              />
              <Button
                variant="outline"
                size="sm"
                aria-label="Toggle dev telemetry"
                onClick={() => {
                  try {
                    const url = new URL(window.location.href);
                    const isOn = url.searchParams.get('dev_telemetry') === '1';
                    if (isOn) url.searchParams.delete('dev_telemetry');
                    else url.searchParams.set('dev_telemetry', '1');
                    window.history.replaceState({}, '', url.toString());
                    window.dispatchEvent(new Event('dev_telemetry_toggle'));
                    try { logUxEvent('dev_telemetry_toggled', { enabled: !isOn }); } catch {}
                  } catch {}
                }}
              >
                Dev Tools
              </Button>
            </div>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="container mx-auto px-4 py-8">
            <Tabs
              value={activeTab}
              onValueChange={(val) => {
                setActiveTab(val);
                try {
                  const url = new URL(window.location.href);
                  if (val) url.searchParams.set('tab', val);
                  else url.searchParams.delete('tab');
                  window.history.replaceState({}, '', url.toString());
                  try { logUxEvent('tab_change', { tab: val }); } catch {}
                } catch {}
              }}
              className="space-y-4"
            >
              <TabsList className="grid grid-cols-7 lg:grid-cols-14 gap-2">
                <TabsTrigger value="upload" className="flex items-center gap-1">
                  <Upload className="h-4 w-4" />
                  <span className="hidden lg:inline">Upload</span>
                </TabsTrigger>
                <TabsTrigger value="transcriptions" className="flex items-center gap-1">
                  <FileText className="h-4 w-4" />
                  <span className="hidden lg:inline">Transcripts</span>
                </TabsTrigger>
                <TabsTrigger value="search" className="flex items-center gap-1">
                  <Search className="h-4 w-4" />
                  <span className="hidden lg:inline">Search</span>
                </TabsTrigger>
                <TabsTrigger value="ai" className="flex items-center gap-1">
                  <Cpu className="h-4 w-4" />
                  <span className="hidden lg:inline">AI</span>
                </TabsTrigger>
                <TabsTrigger value="collab" className="flex items-center gap-1">
                  <Users className="h-4 w-4" />
                  <span className="hidden lg:inline">Collaborate</span>
                </TabsTrigger>
                <TabsTrigger value="audio" className="flex items-center gap-1">
                  <Headphones className="h-4 w-4" />
                  <span className="hidden lg:inline">Audio</span>
                </TabsTrigger>
                <TabsTrigger value="analytics" className="flex items-center gap-1">
                  <BarChart3 className="h-4 w-4" />
                  <span className="hidden lg:inline">Analytics</span>
                </TabsTrigger>
                <TabsTrigger value="i18n" className="flex items-center gap-1">
                  <Languages className="h-4 w-4" />
                  <span className="hidden lg:inline">Languages</span>
                </TabsTrigger>
                <TabsTrigger value="privacy" className="flex items-center gap-1">
                  <Shield className="h-4 w-4" />
                  <span className="hidden lg:inline">Privacy</span>
                </TabsTrigger>
                <TabsTrigger value="graphql" className="flex items-center gap-1">
                  <Activity className="h-4 w-4" />
                  <span className="hidden lg:inline">GraphQL</span>
                </TabsTrigger>
                <TabsTrigger value="cache" className="flex items-center gap-1">
                  <Cpu className="h-4 w-4" />
                  <span className="hidden lg:inline">Cache</span>
                </TabsTrigger>
                <TabsTrigger value="engagement" className="flex items-center gap-1">
                  <TrendingUp className="h-4 w-4" />
                  <span className="hidden lg:inline">Engagement</span>
                </TabsTrigger>
                <TabsTrigger value="content" className="flex items-center gap-1">
                  <Folder className="h-4 w-4" />
                  <span className="hidden lg:inline">Content</span>
                </TabsTrigger>
                <TabsTrigger value="translation" className="flex items-center gap-1">
                  <Globe className="h-4 w-4" />
                  <span className="hidden lg:inline">Translation</span>
                </TabsTrigger>
                <TabsTrigger value="distributed" className="flex items-center gap-1">
                  <Activity className="h-4 w-4" />
                  <span className="hidden lg:inline">Processing</span>
                </TabsTrigger>
                {state.isAdmin && (
                  <TabsTrigger value="admin" className="flex items-center gap-1">
                    <Settings className="h-4 w-4" />
                    <span className="hidden lg:inline">Admin</span>
                  </TabsTrigger>
                )}
              </TabsList>

              <TabsContent value="upload" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Upload Files</CardTitle>
                    <CardDescription>
                      Upload audio or video files for transcription. Supports multiple languages and formats.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <FileUploader onUploadComplete={handleUploadComplete} />
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="transcriptions" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Transcriptions</CardTitle>
                    <CardDescription>
                      View and interact with your transcriptions
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {state.transcriptions.length === 0 ? (
                      <Alert>
                        <AlertDescription>
                          No transcriptions yet. Upload a file to get started.
                        </AlertDescription>
                      </Alert>
                    ) : (
                      <div className="space-y-4">
                        {state.transcriptions.map(transcription => (
                          <div key={transcription.id} className="border rounded-lg p-4">
                            <div className="flex items-center justify-between mb-2">
                              <h3 className="font-medium">Transcription {transcription.id}</h3>
                              <Badge variant={transcription.status === 'completed' ? 'default' : 'secondary'}>
                                {transcription.status}
                              </Badge>
                            </div>
                            {transcription.status === 'completed' && (
                              <InteractiveTranscript
                                segments={[
                                  { id: '1', start_time: 0, end_time: 5, text: transcription.content }
                                ]}
                                audioUrl=""
                              />
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="search" className="space-y-4">
                <ComprehensiveSearch />
              </TabsContent>

              <TabsContent value="ai" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>AI Assistant</CardTitle>
                    <CardDescription>
                      Get AI-powered assistance with your content
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <AIAssistant 
                      value=""
                      onChange={(value) => console.log('AI Assistant:', value)}
                      context="transcript"
                      placeholder="Ask AI for help..."
                    />
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="collab" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Collaborative Editing</CardTitle>
                    <CardDescription>
                      Work together on transcriptions in real-time
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <CollaborativeEditor
                      documentId="demo-doc-1"
                      sessionId="demo-session"
                    />
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="audio" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Enhanced Audio Player</CardTitle>
                    <CardDescription>
                      Advanced audio playback with waveform visualization
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <EnhancedAudioPlayer
                      audioUrl="/demo-audio.mp3"
                    />
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="analytics" className="space-y-4">
                <AdvancedAnalytics />
              </TabsContent>

              <TabsContent value="i18n" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Language Settings</CardTitle>
                    <CardDescription>
                      Configure language preferences and translations
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Translation Manager</h3>
                      <TranslationManager />
                    </div>
                    
                    <div className="pt-4 border-t">
                      <h3 className="text-lg font-semibold mb-2">Supported Languages</h3>
                      <p className="text-sm text-gray-600 mb-4">
                        This platform supports 15 languages including RTL languages like Arabic, Hebrew, and Persian.
                      </p>
                      <div className="grid grid-cols-3 gap-2">
                        {['English', 'Spanish', 'French', 'German', 'Chinese', 'Japanese', 
                          'Korean', 'Arabic', 'Hebrew', 'Portuguese', 'Russian', 'Hindi',
                          'Italian', 'Dutch', 'Persian'].map(lang => (
                          <Badge key={lang} variant="outline">{lang}</Badge>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="privacy" className="space-y-4">
                <GDPRPrivacyDashboard />
              </TabsContent>

              <TabsContent value="graphql" className="space-y-4">
                <GraphQLSubscriptionManager />
              </TabsContent>

              <TabsContent value="cache" className="space-y-4">
                <CacheMetrics />
              </TabsContent>

              <TabsContent value="engagement" className="space-y-4">
                <UserEngagementAnalytics />
              </TabsContent>

              <TabsContent value="content" className="space-y-4">
                <ContentManagement />
              </TabsContent>

              <TabsContent value="translation" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Real-time Translation</CardTitle>
                    <CardDescription>
                      Translate transcriptions to multiple languages in real-time
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <RealtimeTranslation 
                      transcript={state.selectedTranscription?.segments || []}
                      enableStreaming={true}
                      defaultTargetLanguage="es"
                    />
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="distributed" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Distributed Processing Monitor</CardTitle>
                    <CardDescription>
                      Monitor and manage distributed processing tasks
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <DistributedProcessingMonitor />
                  </CardContent>
                </Card>
              </TabsContent>

              {state.isAdmin && (
                <TabsContent value="admin" className="space-y-4">
                  <AdminDashboard />
                </TabsContent>
              )}
            </Tabs>
          </main>
        </div>
          </Router>
          {showTelemetry && (
            <div style={{ position: 'fixed', bottom: 8, right: 8, width: 420, maxHeight: '60vh', overflow: 'auto', background: 'white', border: '1px solid #e5e7eb', borderRadius: 8, boxShadow: '0 4px 14px rgba(0,0,0,0.12)', zIndex: 50 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 8, borderBottom: '1px solid #eee' }}>
                <strong style={{ paddingLeft: 8 }}>UX Telemetry</strong>
                <button onClick={() => setShowTelemetry(false)} className="px-2 py-1 text-sm border rounded">Close</button>
              </div>
              <div style={{ padding: 8 }}>
                <TelemetryViewer />
              </div>
            </div>
          )}
        </InternationalizationProvider>
      </AuthProvider>
    </QueryProvider>
  );
};

export default App;
