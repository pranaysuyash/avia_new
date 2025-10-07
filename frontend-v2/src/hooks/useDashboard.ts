import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient, API_ENDPOINTS } from '@/lib/api-client';
import { useDevelopmentMode, mockDashboardStats, mockRecentJobs, mockAIEngines, mockSystemStatus } from './useDevelopmentMode';

// Types
export interface DashboardStats {
  totalFiles: number;
  totalProcessingTime: string;
  accuracyRate: number;
  activeJobs: number;
  completedJobs: number;
  failedJobs: number;
  storageUsed: string;
  storageLimit: string;
  creditsUsed: number;
  creditsLimit: number;
  trends: {
    files: { value: number; change: string; trend: 'up' | 'down' };
    accuracy: { value: number; change: string; trend: 'up' | 'down' };
    processing: { value: number; change: string; trend: 'up' | 'down' };
    storage: { value: number; change: string; trend: 'up' | 'down' };
  };
}

export interface ProcessingJob {
  id: string;
  name: string;
  type: 'audio' | 'video' | 'document' | 'image';
  status: 'completed' | 'processing' | 'failed' | 'queued';
  accuracy: number;
  duration: string;
  createdAt: string;
  completedAt?: string;
  aiFeatures: string[];
  fileSize: string;
  progress?: number;
  error?: string;
  results?: {
    transcription?: string;
    summary?: string;
    entities?: Array<{ type: string; value: string; confidence: number }>;
    sentiment?: { score: number; label: string };
  };
}

export interface AIEngine {
  id: string;
  name: string;
  type: 'transcription' | 'summarization' | 'analysis' | 'enhancement' | 'video' | 'audio' | 'medical' | 'legal' | 'emotion' | 'entity' | 'realtime';
  status: 'active' | 'inactive' | 'error' | 'maintenance';
  activeJobs: number;
  totalJobs: number;
  averageProcessingTime: string;
  accuracy: number;
  lastHealthCheck: string;
  version: string;
  capabilities: string[];
}

export interface SystemStatus {
  overall: 'healthy' | 'degraded' | 'down';
  services: Array<{
    name: string;
    status: 'healthy' | 'degraded' | 'down';
    responseTime: number;
    uptime: string;
    lastCheck: string;
  }>;
  resources: {
    cpu: { usage: number; limit: number };
    memory: { usage: number; limit: number };
    storage: { usage: number; limit: number };
    gpu?: { usage: number; limit: number };
  };
}

// Dashboard hook
export function useDashboard() {
  const { isDevelopmentMode } = useDevelopmentMode();
  const queryClient = useQueryClient();

  // Get real transcriptions data
  const {
    data: transcriptions,
    isLoading: isLoadingTranscriptions,
    error: transcriptionsError,
  } = useQuery({
    queryKey: ['transcriptions'],
    queryFn: async (): Promise<ProcessingJob[]> => {
      if (isDevelopmentMode) {
        await new Promise(resolve => setTimeout(resolve, 300));
        return mockRecentJobs;
      }

      const response = await apiClient.get<{ jobs: ProcessingJob[] }>('/api/dashboard/recent-jobs');
      return response.jobs;
    },
    refetchInterval: isDevelopmentMode ? false : 10000,
  });

  // Get storage stats for dashboard
  const {
    data: storageStats,
    isLoading: isLoadingStorage,
    error: storageError,
  } = useQuery({
    queryKey: ['storage', 'stats'],
    queryFn: async () => {
      if (isDevelopmentMode) {
        await new Promise(resolve => setTimeout(resolve, 200));
        return mockDashboardStats;
      }

      const response = await apiClient.get<{ stats: DashboardStats }>('/api/dashboard/stats');
      return response.stats;
    },
    refetchInterval: isDevelopmentMode ? false : 30000,
  });

  // Use transcriptions as recent jobs
  const recentJobs = transcriptions || [];
  const isLoadingJobs = isLoadingTranscriptions;
  const jobsError = transcriptionsError;

  // System status from health endpoint
  const {
    data: systemStatus,
    isLoading: isLoadingStatus,
    error: statusError,
    refetch: refetchStatus,
  } = useQuery({
    queryKey: ['system', 'health'],
    queryFn: async (): Promise<SystemStatus> => {
      if (isDevelopmentMode) {
        await new Promise(resolve => setTimeout(resolve, 200));
        return mockSystemStatus;
      }

      const response = await apiClient.get<{ status: SystemStatus }>('/api/dashboard/system-status');
      return response.status;
    },
    refetchInterval: isDevelopmentMode ? false : 15000,
  });

  // AI engines status
  const {
    data: aiEngines,
    isLoading: isLoadingEngines,
    error: enginesError,
    refetch: refetchEngines,
  } = useQuery({
    queryKey: ['dashboard', 'ai-engines'],
    queryFn: async (): Promise<AIEngine[]> => {
      if (isDevelopmentMode) {
        await new Promise(resolve => setTimeout(resolve, 400));
        return mockAIEngines;
      }
      const response = await apiClient.get<{ engines: AIEngine[] }>(
        '/api/ai/engines/status'
      );
      return response.engines;
    },
    refetchInterval: isDevelopmentMode ? false : 20000,
  });

  // Helper functions
  const getJobsByStatus = (status: ProcessingJob['status']) => {
    return recentJobs?.filter(job => job.status === status) || [];
  };

  const getEnginesByStatus = (status: AIEngine['status']) => {
    return aiEngines?.filter(engine => engine.status === status) || [];
  };

  const getProcessingProgress = () => {
    if (!recentJobs) return 0;
    const processingJobs = getJobsByStatus('processing');
    if (processingJobs.length === 0) return 0;

    const totalProgress = processingJobs.reduce((sum, job) => sum + (job.progress || 0), 0);
    return totalProgress / processingJobs.length;
  };

  const getSystemHealthScore = () => {
    if (!systemStatus) return 0;

    const serviceHealth = systemStatus.services.reduce((score, service) => {
      switch (service.status) {
        case 'healthy': return score + 1;
        case 'degraded': return score + 0.5;
        case 'down': return score + 0;
        default: return score;
      }
    }, 0) / systemStatus.services.length;

    const resourceHealth = Object.values(systemStatus.resources).reduce((score, resource) => {
      const usage = resource.usage / resource.limit;
      if (usage < 0.7) return score + 1;
      if (usage < 0.9) return score + 0.5;
      return score + 0;
    }, 0) / Object.keys(systemStatus.resources).length;

    return (serviceHealth + resourceHealth) / 2;
  };

  // Remove the old refreshDashboard function since we're redefining it below

  return {
    // Data
    stats: storageStats,
    recentJobs,
    systemStatus,
    aiEngines: aiEngines || [],

    // Loading states
    isLoading: isLoadingStorage || isLoadingJobs || isLoadingStatus || isLoadingEngines,
    isLoadingStats: isLoadingStorage,
    isLoadingJobs,
    isLoadingStatus,
    isLoadingEngines,

    // Errors
    error: storageError || jobsError || statusError || enginesError,
    statsError: storageError,
    jobsError,
    statusError,
    enginesError,

    // Helper functions
    getJobsByStatus,
    getEnginesByStatus,
    getProcessingProgress,
    getSystemHealthScore,

    // Actions
    refreshDashboard: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['storage', 'stats'] }),
        queryClient.invalidateQueries({ queryKey: ['transcriptions'] }),
        refetchStatus(),
        refetchEngines(),
      ]);
    },
    refetchStats: () => queryClient.invalidateQueries({ queryKey: ['storage', 'stats'] }),
    refetchJobs: () => queryClient.invalidateQueries({ queryKey: ['transcriptions'] }),
    refetchStatus,
    refetchEngines,
  };
}

// Hook for real-time job updates - using transcription endpoint
export function useJobUpdates(jobId?: string) {
  return useQuery({
    queryKey: ['transcriptions', jobId],
    queryFn: async () => {
      if (!jobId) return null;
      const response = await apiClient.get<ProcessingJob>(
        API_ENDPOINTS.TRANSCRIPTIONS.DETAILS(jobId)
      );
      return response;
    },
    enabled: !!jobId,
    refetchInterval: (query) => {
      // Refetch more frequently for active jobs
      const data = query.state.data;
      if (data?.status === 'processing') {
        return 2000; // 2 seconds
      }
      return 10000; // 10 seconds for completed/failed jobs
    },
  });
}

// Hook for processing statistics
export function useProcessingStats(timeRange: '24h' | '7d' | '30d' = '24h') {
  return useQuery({
    queryKey: ['dashboard', 'processing-stats', timeRange],
    queryFn: async () => {
      const response = await apiClient.get<{
        stats: {
          totalJobs: number;
          completedJobs: number;
          failedJobs: number;
          averageProcessingTime: number;
          averageAccuracy: number;
          jobsByType: Record<string, number>;
          jobsByHour: Array<{ hour: string; count: number }>;
        };
      }>('/api/dashboard/processing-stats', { timeRange });
      return response.stats;
    },
    refetchInterval: 60000, // Refetch every minute
  });
}