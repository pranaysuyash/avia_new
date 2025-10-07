import { useState, useEffect } from 'react';

// Development mode hook to provide fallback data when backend is not available
export function useDevelopmentMode() {
  const [isDevelopmentMode, setIsDevelopmentMode] = useState(false);
  const [backendAvailable, setBackendAvailable] = useState<boolean | null>(null);

  useEffect(() => {
    const checkBackendAvailability = async () => {
      try {
        // Create AbortController for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000);
        
        const response = await fetch('http://localhost:8000/api/health', {
          method: 'GET',
          signal: controller.signal,
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
          console.log('✅ Backend connected - using real data');
          setBackendAvailable(true);
          setIsDevelopmentMode(false);
        } else {
          console.warn('❌ Backend responded with error - using mock data');
          setBackendAvailable(false);
          setIsDevelopmentMode(true);
        }
      } catch (error) {
        console.warn('❌ Backend not available - using mock data:', error);
        setBackendAvailable(false);
        setIsDevelopmentMode(true);
      }
    };

    checkBackendAvailability();
    
    // Check every 30 seconds if backend becomes available
    const interval = setInterval(checkBackendAvailability, 30000);
    
    return () => clearInterval(interval);
  }, []);

  return {
    isDevelopmentMode,
    backendAvailable,
    isChecking: backendAvailable === null,
  };
}

// Mock data for development mode
export const mockUser = {
  id: 'dev-user-1',
  name: 'Development User',
  email: 'dev@example.com',
  initials: 'DU',
  role: 'admin' as const,
  preferences: {
    theme: 'system' as const,
    language: 'en',
    notifications: true,
  },
  subscription: {
    plan: 'enterprise' as const,
    status: 'active' as const,
  },
};

export const mockDashboardStats = {
  totalFiles: 47234,
  totalProcessingTime: '12,847 hrs',
  accuracyRate: 99.3,
  activeJobs: 23,
  completedJobs: 1847,
  failedJobs: 12,
  storageUsed: '2.4 TB',
  storageLimit: '10 TB',
  creditsUsed: 8750,
  creditsLimit: 10000,
  trends: {
    files: { value: 47234, change: '+23%', trend: 'up' as const },
    accuracy: { value: 99.3, change: '+1.2%', trend: 'up' as const },
    processing: { value: 12847, change: '+18%', trend: 'up' as const },
    storage: { value: 2.4, change: '+15%', trend: 'up' as const },
  },
};

export const mockRecentJobs = [
  {
    id: 'job-1',
    name: 'Board_Meeting_Q4_2024.mp4',
    type: 'video' as const,
    status: 'completed' as const,
    accuracy: 99.1,
    duration: '1:23:45',
    createdAt: '2024-01-15T10:30:00Z',
    completedAt: '2024-01-15T11:53:45Z',
    aiFeatures: ['Sentiment Analysis', 'Action Items', 'Key Insights', 'Speaker Diarization'],
    fileSize: '1.2 GB',
  },
  {
    id: 'job-2',
    name: 'Medical_Consultation_Case_447.wav',
    type: 'audio' as const,
    status: 'processing' as const,
    accuracy: 0,
    duration: '45:32',
    createdAt: '2024-01-15T11:00:00Z',
    aiFeatures: ['Clinical NER', 'HIPAA Compliance', 'Medical Terminology'],
    fileSize: '156 MB',
    progress: 67,
  },
  {
    id: 'job-3',
    name: 'Legal_Deposition_2024_03.mp4',
    type: 'video' as const,
    status: 'completed' as const,
    accuracy: 98.7,
    duration: '2:18:45',
    createdAt: '2024-01-15T09:15:00Z',
    completedAt: '2024-01-15T11:33:45Z',
    aiFeatures: ['Legal Entity Extraction', 'Compliance Check', 'Redaction'],
    fileSize: '2.8 GB',
  },
  {
    id: 'job-4',
    name: 'Multi_Speaker_Conference.wav',
    type: 'audio' as const,
    status: 'completed' as const,
    accuracy: 97.9,
    duration: '56:42',
    createdAt: '2024-01-15T08:30:00Z',
    completedAt: '2024-01-15T09:26:42Z',
    aiFeatures: ['8-Channel Processing', 'Spatial Audio', 'Voice Profiling'],
    fileSize: '234 MB',
  },
];

export const mockAIEngines = [
  {
    id: 'engine-1',
    name: 'Speech-to-Text Engine',
    type: 'transcription' as const,
    status: 'active' as const,
    activeJobs: 45,
    totalJobs: 2847,
    averageProcessingTime: '2.3 min',
    accuracy: 99.2,
    lastHealthCheck: '2024-01-15T12:00:00Z',
    version: '2.1.0',
    capabilities: ['Multi-language', 'Real-time', 'Batch processing'],
  },
  {
    id: 'engine-2',
    name: 'Video Intelligence',
    type: 'video' as const,
    status: 'active' as const,
    activeJobs: 23,
    totalJobs: 1456,
    averageProcessingTime: '8.7 min',
    accuracy: 98.8,
    lastHealthCheck: '2024-01-15T12:00:00Z',
    version: '1.8.2',
    capabilities: ['Object detection', 'Scene analysis', 'OCR'],
  },
  {
    id: 'engine-3',
    name: 'Medical AI (HIPAA)',
    type: 'medical' as const,
    status: 'active' as const,
    activeJobs: 18,
    totalJobs: 892,
    averageProcessingTime: '4.1 min',
    accuracy: 99.7,
    lastHealthCheck: '2024-01-15T12:00:00Z',
    version: '3.0.1',
    capabilities: ['Clinical NER', 'HIPAA compliance', 'Medical terminology'],
  },
  {
    id: 'engine-4',
    name: 'Legal AI',
    type: 'legal' as const,
    status: 'active' as const,
    activeJobs: 12,
    totalJobs: 634,
    averageProcessingTime: '6.2 min',
    accuracy: 98.9,
    lastHealthCheck: '2024-01-15T12:00:00Z',
    version: '2.3.0',
    capabilities: ['Legal entity extraction', 'Compliance check', 'Redaction'],
  },
  {
    id: 'engine-5',
    name: 'Multi-Channel Audio',
    type: 'audio' as const,
    status: 'active' as const,
    activeJobs: 34,
    totalJobs: 1923,
    averageProcessingTime: '3.8 min',
    accuracy: 98.1,
    lastHealthCheck: '2024-01-15T12:00:00Z',
    version: '1.9.3',
    capabilities: ['8-channel processing', 'Spatial audio', 'Voice profiling'],
  },
  {
    id: 'engine-6',
    name: 'Emotion Detection',
    type: 'emotion' as const,
    status: 'active' as const,
    activeJobs: 28,
    totalJobs: 2156,
    averageProcessingTime: '1.9 min',
    accuracy: 97.3,
    lastHealthCheck: '2024-01-15T12:00:00Z',
    version: '2.0.4',
    capabilities: ['Sentiment analysis', 'Emotion recognition', 'Tone analysis'],
  },
  {
    id: 'engine-7',
    name: 'Entity Extraction',
    type: 'entity' as const,
    status: 'active' as const,
    activeJobs: 56,
    totalJobs: 3421,
    averageProcessingTime: '1.2 min',
    accuracy: 99.0,
    lastHealthCheck: '2024-01-15T12:00:00Z',
    version: '2.2.1',
    capabilities: ['Named entity recognition', 'Relationship extraction', 'Knowledge graphs'],
  },
  {
    id: 'engine-8',
    name: 'Real-time Transcription',
    type: 'realtime' as const,
    status: 'active' as const,
    activeJobs: 15,
    totalJobs: 987,
    averageProcessingTime: 'Live',
    accuracy: 98.5,
    lastHealthCheck: '2024-01-15T12:00:00Z',
    version: '1.7.0',
    capabilities: ['Live streaming', 'Low latency', 'Multi-speaker'],
  },
];

export const mockSystemStatus = {
  overall: 'healthy' as const,
  services: [
    {
      name: 'API Gateway',
      status: 'healthy' as const,
      responseTime: 45,
      uptime: '99.9%',
      lastCheck: '2024-01-15T12:00:00Z',
    },
    {
      name: 'Transcription Service',
      status: 'healthy' as const,
      responseTime: 120,
      uptime: '99.8%',
      lastCheck: '2024-01-15T12:00:00Z',
    },
    {
      name: 'Video Processing',
      status: 'healthy' as const,
      responseTime: 230,
      uptime: '99.7%',
      lastCheck: '2024-01-15T12:00:00Z',
    },
    {
      name: 'Database',
      status: 'healthy' as const,
      responseTime: 15,
      uptime: '99.9%',
      lastCheck: '2024-01-15T12:00:00Z',
    },
  ],
  resources: {
    cpu: { usage: 45, limit: 100 },
    memory: { usage: 62, limit: 100 },
    storage: { usage: 24, limit: 100 },
    gpu: { usage: 78, limit: 100 },
  },
};