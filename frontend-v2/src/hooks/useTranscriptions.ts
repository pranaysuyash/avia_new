import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient, API_ENDPOINTS } from '@/lib/api-client';

// Types matching your FastAPI backend
export interface Transcription {
  id: string;
  title: string;
  status: 'processing' | 'completed' | 'failed';
  created_at: string;
  duration?: number;
  text?: string;
  entities?: Record<string, string[]>;
  confidence?: number;
}

export interface TranscriptionUpload {
  title?: string;
  language?: string;
  method?: string;
  team_id?: number;
}

// Hook for managing transcriptions
export function useTranscriptions() {
  const queryClient = useQueryClient();

  // Get transcriptions list
  const {
    data: transcriptions,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['transcriptions'],
    queryFn: async (): Promise<Transcription[]> => {
      const response = await apiClient.get<Transcription[]>(API_ENDPOINTS.TRANSCRIPTIONS.LIST);
      return response;
    },
  });

  // Upload transcription
  const uploadMutation = useMutation({
    mutationFn: async ({
      file,
      options = {},
      onProgress,
    }: {
      file: File;
      options?: TranscriptionUpload;
      onProgress?: (progress: number) => void;
    }): Promise<Transcription> => {
      const response = await apiClient.uploadFile<Transcription>(
        API_ENDPOINTS.TRANSCRIPTIONS.UPLOAD,
        file,
        options,
        onProgress
      );
      return response;
    },
    onSuccess: (newTranscription) => {
      // Update transcriptions list
      queryClient.setQueryData(['transcriptions'], (oldData: Transcription[] | undefined) => {
        if (!oldData) return [newTranscription];
        return [newTranscription, ...oldData];
      });
    },
  });

  // Delete transcription
  const deleteMutation = useMutation({
    mutationFn: async (transcriptionId: string): Promise<void> => {
      await apiClient.delete(API_ENDPOINTS.TRANSCRIPTIONS.DELETE(transcriptionId));
    },
    onSuccess: (_, transcriptionId) => {
      // Remove from list
      queryClient.setQueryData(['transcriptions'], (oldData: Transcription[] | undefined) => {
        if (!oldData) return [];
        return oldData.filter(t => t.id !== transcriptionId);
      });
    },
  });

  // Get single transcription
  const getTranscription = (transcriptionId: string) => {
    return useQuery({
      queryKey: ['transcriptions', transcriptionId],
      queryFn: async (): Promise<Transcription> => {
        const response = await apiClient.get<Transcription>(
          API_ENDPOINTS.TRANSCRIPTIONS.DETAILS(transcriptionId)
        );
        return response;
      },
      enabled: !!transcriptionId,
    });
  };

  return {
    // Data
    transcriptions: transcriptions || [],
    
    // State
    isLoading,
    error,
    isUploading: uploadMutation.isPending,
    isDeleting: deleteMutation.isPending,
    
    // Actions
    uploadTranscription: uploadMutation.mutateAsync,
    deleteTranscription: deleteMutation.mutateAsync,
    refetch,
    getTranscription,
    
    // Errors
    uploadError: uploadMutation.error,
    deleteError: deleteMutation.error,
  };
}

// Hook for storage stats
export function useStorageStats() {
  return useQuery({
    queryKey: ['storage', 'stats'],
    queryFn: async () => {
      const response = await apiClient.get<{
        total_size_bytes: number;
        total_size_mb: number;
        file_count: number;
        files: Array<{
          filename: string;
          size_bytes: number;
          created_at: string;
        }>;
      }>(API_ENDPOINTS.STORAGE.STATS);
      return response;
    },
  });
}