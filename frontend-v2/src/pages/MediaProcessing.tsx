import { useState } from 'react';
import { AppShell, PageContainer } from '@/components/layout';
import { FileUploadZone } from '@/components/media/FileUploadZone';
import { BatchProcessingManager } from '@/components/media/BatchProcessingManager';
import { MediaProcessingInterface } from '@/components/media/MediaProcessingInterface';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Upload,
  Settings,
  Activity,
  FileText,
  Zap,
  Brain,
  Mic,
  Video,
  Image,
  FileAudio,
  Play,
  List
} from 'lucide-react';

interface ProcessingJob {
  id: string;
  fileName: string;
  fileSize: number;
  fileType: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'paused';
  progress: number;
  estimatedTime?: number;
  startTime?: Date;
  endTime?: Date;
  aiEngines: string[];
  error?: string;
  url?: string;
  duration?: number;
  transcript?: {
    id: string;
    text: string;
    segments: TranscriptSegment[];
    speakers: Speaker[];
    confidence: number;
    language: string;
    processingTime: number;
  };
  waveformData?: number[];
}

interface TranscriptSegment {
  id: string;
  startTime: number;
  endTime: number;
  text: string;
  speakerId?: string;
  confidence: number;
  words?: Word[];
}

interface Word {
  text: string;
  startTime: number;
  endTime: number;
  confidence: number;
}

interface Speaker {
  id: string;
  name: string;
  color: string;
  segments: number;
  totalDuration: number;
}

interface MediaFile {
  id: string;
  name: string;
  type: 'audio' | 'video';
  url: string;
  duration: number;
  size: number;
  uploadedAt: string;
  status: 'processing' | 'completed' | 'error';
  transcript?: {
    id: string;
    text: string;
    segments: TranscriptSegment[];
    speakers: Speaker[];
    confidence: number;
    language: string;
    processingTime: number;
  };
  waveformData?: number[];
}

const mockJobs: ProcessingJob[] = [
  {
    id: '1',
    fileName: 'board-meeting-q4-2024.mp4',
    fileSize: 156 * 1024 * 1024, // 156MB
    fileType: 'video/mp4',
    priority: 'high',
    status: 'processing',
    progress: 67,
    estimatedTime: 180,
    startTime: new Date(Date.now() - 120000), // 2 minutes ago
    aiEngines: ['Speech-to-Text', 'Speaker Diarization', 'Sentiment Analysis', 'Entity Extraction']
  },
  {
    id: '2',
    fileName: 'client-interview-audio.wav',
    fileSize: 45 * 1024 * 1024, // 45MB
    fileType: 'audio/wav',
    priority: 'normal',
    status: 'queued',
    progress: 0,
    estimatedTime: 90,
    aiEngines: ['Speech-to-Text', 'Emotion Detection', 'Topic Modeling']
  },
  {
    id: '3',
    fileName: 'medical-consultation.m4a',
    fileSize: 23 * 1024 * 1024, // 23MB
    fileType: 'audio/m4a',
    priority: 'urgent',
    status: 'queued',
    progress: 0,
    estimatedTime: 60,
    aiEngines: ['Medical AI', 'HIPAA Transcription', 'Medical NER']
  },
  {
    id: '4',
    fileName: 'presentation-slides.pdf',
    fileSize: 12 * 1024 * 1024, // 12MB
    fileType: 'application/pdf',
    priority: 'low',
    status: 'completed',
    progress: 100,
    endTime: new Date(Date.now() - 300000), // 5 minutes ago
    aiEngines: ['OCR', 'Document Analysis', 'Entity Extraction']
  }
];

// Mock completed media files with transcripts
const mockCompletedFiles: MediaFile[] = [
  {
    id: 'media-1',
    name: 'team-standup-monday.mp3',
    type: 'audio',
    url: '/api/media/team-standup-monday.mp3',
    duration: 1847, // 30:47
    size: 42 * 1024 * 1024,
    uploadedAt: '2024-01-15T09:30:00Z',
    status: 'completed',
    transcript: {
      id: 'transcript-1',
      text: 'Good morning everyone. Let\'s start with our daily standup. Sarah, would you like to go first?',
      confidence: 0.94,
      language: 'en',
      processingTime: 45,
      speakers: [
        { id: 'speaker-1', name: 'John (Manager)', color: '#3b82f6', segments: 12, totalDuration: 420 },
        { id: 'speaker-2', name: 'Sarah (Developer)', color: '#ef4444', segments: 8, totalDuration: 380 },
        { id: 'speaker-3', name: 'Mike (Designer)', color: '#10b981', segments: 6, totalDuration: 290 },
        { id: 'speaker-4', name: 'Lisa (QA)', color: '#f59e0b', segments: 5, totalDuration: 240 }
      ],
      segments: [
        {
          id: 'seg-1',
          startTime: 0,
          endTime: 4.2,
          text: 'Good morning everyone. Let\'s start with our daily standup.',
          speakerId: 'speaker-1',
          confidence: 0.96
        },
        {
          id: 'seg-2',
          startTime: 4.5,
          endTime: 7.8,
          text: 'Sarah, would you like to go first?',
          speakerId: 'speaker-1',
          confidence: 0.94
        },
        {
          id: 'seg-3',
          startTime: 8.1,
          endTime: 15.3,
          text: 'Sure! Yesterday I finished the user authentication module and started working on the dashboard components.',
          speakerId: 'speaker-2',
          confidence: 0.92
        },
        {
          id: 'seg-4',
          startTime: 15.6,
          endTime: 22.4,
          text: 'Today I plan to complete the responsive design for the dashboard and begin integration testing.',
          speakerId: 'speaker-2',
          confidence: 0.95
        },
        {
          id: 'seg-5',
          startTime: 22.7,
          endTime: 26.1,
          text: 'No blockers at the moment. Mike, your turn.',
          speakerId: 'speaker-2',
          confidence: 0.93
        }
      ]
    },
    waveformData: Array.from({ length: 1000 }, () => Math.random() * 0.8 + 0.1)
  },
  {
    id: 'media-2',
    name: 'client-presentation-demo.mp4',
    type: 'video',
    url: '/api/media/client-presentation-demo.mp4',
    duration: 2156, // 35:56
    size: 187 * 1024 * 1024,
    uploadedAt: '2024-01-14T14:15:00Z',
    status: 'completed',
    transcript: {
      id: 'transcript-2',
      text: 'Welcome to our product demonstration. Today I\'ll be showing you the key features of our new platform.',
      confidence: 0.97,
      language: 'en',
      processingTime: 78,
      speakers: [
        { id: 'speaker-5', name: 'Alex (Presenter)', color: '#8b5cf6', segments: 25, totalDuration: 1890 },
        { id: 'speaker-6', name: 'Client Questions', color: '#06b6d4', segments: 8, totalDuration: 266 }
      ],
      segments: [
        {
          id: 'seg-6',
          startTime: 0,
          endTime: 6.8,
          text: 'Welcome to our product demonstration. Today I\'ll be showing you the key features of our new platform.',
          speakerId: 'speaker-5',
          confidence: 0.97
        },
        {
          id: 'seg-7',
          startTime: 7.2,
          endTime: 14.5,
          text: 'Let\'s start with the dashboard where you can see all your media processing jobs in real-time.',
          speakerId: 'speaker-5',
          confidence: 0.95
        }
      ]
    },
    waveformData: Array.from({ length: 1000 }, () => Math.random() * 0.9 + 0.05)
  }
];

const aiEngineStats = [
  { name: 'Speech-to-Text', active: 12, icon: Mic, color: 'bg-blue-500' },
  { name: 'Video Intelligence', active: 8, icon: Video, color: 'bg-purple-500' },
  { name: 'Medical AI', active: 5, icon: Brain, color: 'bg-green-500' },
  { name: 'Document OCR', active: 15, icon: FileText, color: 'bg-orange-500' },
  { name: 'Audio Enhancement', active: 7, icon: FileAudio, color: 'bg-cyan-500' },
  { name: 'Image Analysis', active: 3, icon: Image, color: 'bg-pink-500' }
];

export function MediaProcessingPage() {
  const [jobs, setJobs] = useState<ProcessingJob[]>(mockJobs);
  const [isProcessing, setIsProcessing] = useState(true);
  const [completedFiles] = useState<MediaFile[]>(mockCompletedFiles);
  const [selectedFile, setSelectedFile] = useState<MediaFile | null>(null);
  const [activeTab, setActiveTab] = useState('upload');

  const handleFilesAdded = (files: File[]) => {
    const newJobs: ProcessingJob[] = files.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      fileName: file.name,
      fileSize: file.size,
      fileType: file.type,
      priority: 'normal',
      status: 'queued',
      progress: 0,
      estimatedTime: Math.floor(file.size / (1024 * 1024)) * 30, // Rough estimate: 30s per MB
      aiEngines: getRecommendedEngines(file.type)
    }));

    setJobs(prev => [...prev, ...newJobs]);
  };

  const getRecommendedEngines = (fileType: string): string[] => {
    if (fileType.startsWith('audio/')) {
      return ['Speech-to-Text', 'Speaker Diarization', 'Emotion Detection'];
    }
    if (fileType.startsWith('video/')) {
      return ['Speech-to-Text', 'Video Intelligence', 'Scene Detection', 'Entity Extraction'];
    }
    if (fileType.startsWith('image/')) {
      return ['OCR', 'Image Analysis', 'Entity Extraction'];
    }
    if (fileType.includes('pdf') || fileType.startsWith('text/')) {
      return ['OCR', 'Document Analysis', 'Entity Extraction', 'Topic Modeling'];
    }
    return ['General AI'];
  };

  const handleJobUpdate = (jobId: string, updates: Partial<ProcessingJob>) => {
    setJobs(prev => prev.map(job =>
      job.id === jobId ? { ...job, ...updates } : job
    ));
  };

  const handleStartProcessing = async () => {
    try {
      setIsProcessing(true);

      const queuedJobs = jobs.filter(job => job.status === 'queued');
      if (queuedJobs.length === 0) {
        setIsProcessing(false);
        return;
      }

      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/processing/start-batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(localStorage.getItem('auth_token') && {
            'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
          })
        },
        body: JSON.stringify({
          job_ids: queuedJobs.map(job => job.id)
        })
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Batch processing started:', result);

        // Update job statuses to processing
        queuedJobs.forEach(job => {
          handleJobUpdate(job.id, {
            status: 'processing',
            startTime: new Date()
          });
        });

        // Start progress simulation for demo purposes
        // In real implementation, this would come from WebSocket updates
        queuedJobs.forEach(job => {
          simulateJobProgress(job.id);
        });
      } else {
        console.error('Failed to start batch processing');
        setIsProcessing(false);
      }
    } catch (error) {
      console.error('Error starting batch processing:', error);
      // Fallback to simulation for demo
      const queuedJobs = jobs.filter(job => job.status === 'queued');
      if (queuedJobs.length > 0) {
        queuedJobs.forEach(job => {
          handleJobUpdate(job.id, {
            status: 'processing',
            startTime: new Date()
          });
          simulateJobProgress(job.id);
        });
      }
    }
  };

  const simulateJobProgress = (jobId: string) => {
    const interval = setInterval(() => {
      setJobs(prev => {
        const job = prev.find(j => j.id === jobId);
        if (!job || job.status !== 'processing') {
          clearInterval(interval);
          return prev;
        }

        const newProgress = Math.min(job.progress + Math.random() * 10, 100);
        if (newProgress >= 100) {
          clearInterval(interval);
          return prev.map(j =>
            j.id === jobId
              ? { ...j, progress: 100, status: 'completed', endTime: new Date() }
              : j
          );
        }

        return prev.map(j =>
          j.id === jobId ? { ...j, progress: newProgress } : j
        );
      });
    }, 1000);
  };

  const handlePauseProcessing = async () => {
    try {
      const processingJobs = jobs.filter(job => job.status === 'processing');

      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/processing/pause-batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(localStorage.getItem('auth_token') && {
            'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
          })
        },
        body: JSON.stringify({
          job_ids: processingJobs.map(job => job.id)
        })
      });

      if (response.ok) {
        setIsProcessing(false);
        setJobs(prev => prev.map(job =>
          job.status === 'processing' ? { ...job, status: 'paused' } : job
        ));
      } else {
        console.error('Failed to pause processing');
      }
    } catch (error) {
      console.error('Error pausing processing:', error);
      // Fallback to local update
      setIsProcessing(false);
      setJobs(prev => prev.map(job =>
        job.status === 'processing' ? { ...job, status: 'paused' } : job
      ));
    }
  };

  const handleStopProcessing = async () => {
    try {
      const processingJobs = jobs.filter(job => job.status === 'processing');

      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/processing/stop-batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(localStorage.getItem('auth_token') && {
            'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
          })
        },
        body: JSON.stringify({
          job_ids: processingJobs.map(job => job.id)
        })
      });

      if (response.ok) {
        setIsProcessing(false);
        setJobs(prev => prev.map(job =>
          job.status === 'processing' ? { ...job, status: 'queued', progress: 0 } : job
        ));
      } else {
        console.error('Failed to stop processing');
      }
    } catch (error) {
      console.error('Error stopping processing:', error);
      // Fallback to local update
      setIsProcessing(false);
      setJobs(prev => prev.map(job =>
        job.status === 'processing' ? { ...job, status: 'queued', progress: 0 } : job
      ));
    }
  };

  const processingJobs = jobs.filter(job => job.status === 'processing');
  const queuedJobs = jobs.filter(job => job.status === 'queued');

  return (
    <AppShell>
      <PageContainer
        title="Media Processing"
        description="Upload and process your media files with AI-powered analysis"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Media Processing' }
        ]}
        actions={
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="flex items-center gap-1">
              <Activity className="h-3 w-3" />
              {processingJobs.length} Active
            </Badge>
            <Badge variant="outline" className="flex items-center gap-1">
              <Upload className="h-3 w-3" />
              {queuedJobs.length} Queued
            </Badge>
            <Badge variant="outline" className="flex items-center gap-1">
              <Play className="h-3 w-3" />
              {completedFiles.length} Completed
            </Badge>
          </div>
        }
      >

        {/* Main Content Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="upload" className="flex items-center space-x-2">
              <Upload className="h-4 w-4" />
              <span>Upload & Process</span>
            </TabsTrigger>
            <TabsTrigger value="library" className="flex items-center space-x-2">
              <List className="h-4 w-4" />
              <span>Media Library</span>
            </TabsTrigger>
            <TabsTrigger value="player" className="flex items-center space-x-2" disabled={!selectedFile}>
              <Play className="h-4 w-4" />
              <span>Media Player</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="mt-6 space-y-6">
            {/* AI Engine Status */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5" />
                  AI Processing Engines
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                  {aiEngineStats.map((engine) => {
                    const Icon = engine.icon;
                    return (
                      <div key={engine.name} className="text-center">
                        <div className={`w-12 h-12 rounded-lg ${engine.color} flex items-center justify-center text-white mx-auto mb-2`}>
                          <Icon className="h-6 w-6" />
                        </div>
                        <p className="font-medium text-sm">{engine.name}</p>
                        <p className="text-xs text-gray-500">{engine.active} active</p>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            {/* File Upload Zone */}
            <FileUploadZone
              onFilesAdded={handleFilesAdded}
              maxFiles={20}
              maxSize={500 * 1024 * 1024} // 500MB
            />

            {/* Batch Processing Manager */}
            <BatchProcessingManager
              jobs={jobs}
              onJobUpdate={handleJobUpdate}
              onStartProcessing={handleStartProcessing}
              onPauseProcessing={handlePauseProcessing}
              onStopProcessing={handleStopProcessing}
              isProcessing={isProcessing}
            />

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                        Processing Today
                      </p>
                      <p className="text-2xl font-bold">247</p>
                    </div>
                    <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                      <Activity className="h-6 w-6 text-blue-600" />
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">+12% from yesterday</p>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                        Average Processing Time
                      </p>
                      <p className="text-2xl font-bold">2.3m</p>
                    </div>
                    <div className="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
                      <Zap className="h-6 w-6 text-green-600" />
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">-8% improvement</p>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                        Success Rate
                      </p>
                      <p className="text-2xl font-bold">99.2%</p>
                    </div>
                    <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center">
                      <Settings className="h-6 w-6 text-purple-600" />
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">+0.3% this week</p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="library" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <List className="h-5 w-5" />
                  Completed Media Files
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {completedFiles.map((file) => (
                    <div
                      key={file.id}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
                      onClick={() => {
                        setSelectedFile(file);
                        setActiveTab('player');
                      }}
                    >
                      <div className="flex items-center space-x-4">
                        <div className="p-2 bg-primary/10 rounded-lg">
                          {file.type === 'video' ? (
                            <Video className="h-5 w-5 text-primary" />
                          ) : (
                            <FileAudio className="h-5 w-5 text-primary" />
                          )}
                        </div>

                        <div>
                          <h3 className="font-medium">{file.name}</h3>
                          <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                            <span>{Math.floor(file.duration / 60)}:{(file.duration % 60).toString().padStart(2, '0')}</span>
                            <span>{(file.size / (1024 * 1024)).toFixed(1)} MB</span>
                            <span className="capitalize">{file.type}</span>
                            {file.transcript && (
                              <Badge variant="secondary">
                                {file.transcript.speakers.length} speakers
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        <Badge variant="outline" className="text-green-600 border-green-600">
                          Completed
                        </Badge>
                        <Button variant="ghost" size="sm">
                          <Play className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}

                  {completedFiles.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                      <FileAudio className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No completed media files yet.</p>
                      <p className="text-sm">Upload and process files to see them here.</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="player" className="mt-6">
            {selectedFile ? (
              <MediaProcessingInterface
                file={selectedFile}
                onTimeUpdate={(time) => console.log('Time update:', time)}
                onSegmentClick={(segment) => console.log('Segment clicked:', segment)}
              />
            ) : (
              <Card>
                <CardContent className="p-8 text-center">
                  <Play className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <h3 className="text-lg font-medium mb-2">No Media Selected</h3>
                  <p className="text-muted-foreground mb-4">
                    Select a completed media file from the library to view and interact with it.
                  </p>
                  <Button onClick={() => setActiveTab('library')}>
                    Browse Media Library
                  </Button>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </PageContainer>
    </AppShell>
  );
}