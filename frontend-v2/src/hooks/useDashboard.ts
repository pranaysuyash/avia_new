import { useQuery } from '@tanstack/react-query';
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

  // Dashboard stats
  const {
    data: stats,
    isLoading: isLoadingStats,
    error: statsError,
    refetch: refetchStats,
  } = useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: async (): Promise<DashboardStats> => {
      if (isDevelopmentMode) {
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 500));
        return mockDashboardStats;
      }
      const response = await apiClient.get<{ stats: DashboardStats }>(
        API_ENDPOINTS.DASHBOARD.STATS
      );
      return response.stats;
    },
    refetchInterval: isDevelopmentMode ? false : 30000, // Don't refetch in dev mode
  });

  // Recent processing jobs
  const {
    data: recentJobs,
    isLoading: isLoadingJobs,
    error: jobsError,
    refetch: refetchJobs,
  } = useQuery({
    queryKey: ['dashboard', 'recent-jobs'],
    queryFn: async (): Promise<ProcessingJob[]> => {
      if (isDevelopmentMode) {
        await new Promise(resolve => setTimeout(resolve, 300));
        return mockRecentJobs;
      }
      const response = await apiClient.get<{ jobs: ProcessingJob[] }>(
        API_ENDPOINTS.DASHBOARD.RECENT_JOBS,
        { limit: 10 }
      );
      return response.jobs;
    },
    refetchInterval: isDevelopmentMode ? false : 10000,
  });

  // System status
  const {
    data: systemStatus,
    isLoading: isLoadingStatus,
    error: statusError,
    refetch: refetchStatus,
  } = useQuery({
    queryKey: ['dashboard', 'system-status'],
    queryFn: async (): Promise<SystemStatus> => {
      if (isDevelopmentMode) {
        await new Promise(resolve => setTimeout(resolve, 200));
        return mockSystemStatus;
      }
      const response = await apiClient.get<{ status: SystemStatus }>(
        API_ENDPOINTS.DASHBOARD.SYSTEM_STATUS
      );
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

  // Refresh all dashboard data
  const refreshDashboard = async () => {
    await Promise.all([
      refetchStats(),
      refetchJobs(),
      refetchStatus(),
      refetchEngines(),
    ]);
  };

  return {
    // Data
    stats,
    recentJobs,
    systemStatus,
    aiEngines,
    
    // Loading states
    isLoading: isLoadingStats || isLoadingJobs || isLoadingStatus || isLoadingEngines,
    isLoadingStats,
    isLoadingJobs,
    isLoadingStatus,
    isLoadingEngines,
    
    // Errors
    error: statsError || jobsError || statusError || enginesError,
    statsError,
    jobsError,
    statusError,
    enginesError,
    
    // Helper functions
    getJobsByStatus,
    getEnginesByStatus,
    getProcessingProgress,
    getSystemHealthScore,
    
    // Actions
    refreshDashboard,
    refetchStats,
    refetchJobs,
    refetchStatus,
    refetchEngines,
  };
}

// Hook for real-time job updates
export function useJobUpdates(jobId?: string) {
  return useQuery({
    queryKey: ['jobs', 'updates', jobId],
    queryFn: async () => {
      if (!jobId) return null;
      const response = await apiClient.get<{ job: ProcessingJob }>(
        API_ENDPOINTS.JOBS.STATUS(jobId)
      );
      return response.job;
    },
    enabled: !!jobId,
    refetchInterval: (query) => {
      // Refetch more frequently for active jobs
      const data = query.state.data;
      if (data?.status === 'processing' || data?.status === 'queued') {
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