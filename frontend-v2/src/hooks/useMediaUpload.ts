import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient, API_ENDPOINTS } from '@/lib/api-client';

// Types
export interface MediaFile {
  id: string;
  name: string;
  originalName: string;
  size: number;
  type: string;
  mimeType: string;
  duration?: number;
  dimensions?: { width: number; height: number };
  uploadedAt: string;
  status: 'uploaded' | 'processing' | 'completed' | 'failed';
  url?: string;
  thumbnailUrl?: string;
  metadata: {
    format?: string;
    bitrate?: number;
    sampleRate?: number;
    channels?: number;
    codec?: string;
  };
  processingJobs: string[];
}

export interface UploadProgress {
  fileId: string;
  fileName: string;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  error?: string;
}

export interface UploadOptions {
  enableTranscription?: boolean;
  enableSummarization?: boolean;
  enableSentimentAnalysis?: boolean;
  enableSpeakerDiarization?: boolean;
  language?: string;
  customVocabulary?: string[];
  processingPriority?: 'low' | 'normal' | 'high';
}

// Media upload hook
export function useMediaUpload() {
  const queryClient = useQueryClient();

  // Upload mutation - using your transcription upload endpoint
  const uploadMutation = useMutation({
    mutationFn: async ({
      file,
      options = {},
    }: {
      file: File;
      options?: UploadOptions;
      onProgress?: (progress: number) => void;
    }): Promise<MediaFile> => {
      // Note: onProgress not implemented for this endpoint yet
      // Use your actual transcription upload endpoint
      const formData = new FormData();
      formData.append('file', file);
      if (options.enableTranscription !== false) {
        formData.append('title', file.name);
        formData.append('language', options.language || 'auto');
        formData.append('method', 'advanced');
      }
      
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.TRANSCRIPTIONS.UPLOAD}`, {
        method: 'POST',
        headers: {
          ...(apiClient.authToken && { Authorization: `Bearer ${apiClient.authToken}` }),
        },
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error('Upload failed');
      }
      
      const transcription = await response.json();
      
      // Transform transcription response to MediaFile format
      return {
        id: transcription.id,
        name: transcription.title,
        originalName: file.name,
        size: file.size,
        type: file.type.startsWith('video/') ? 'video' : 'audio',
        mimeType: file.type,
        uploadedAt: transcription.created_at,
        status: transcription.status === 'processing' ? 'processing' : 'completed',
        metadata: {
          format: file.name.split('.').pop() || 'unknown',
        },
        processingJobs: [transcription.id],
      };
    },
    onSuccess: (uploadedFile) => {
      // Update media list cache
      queryClient.setQueryData(['media', 'list'], (oldData: any) => {
        if (!oldData) return { files: [uploadedFile] };
        return {
          ...oldData,
          files: [uploadedFile, ...oldData.files],
        };
      });

      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'stats'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'recent-jobs'] });
    },
  });

  // Multiple files upload - using transcription endpoint
  const uploadMultipleMutation = useMutation({
    mutationFn: async ({
      files,
      options = {},
    }: {
      files: File[];
      options?: UploadOptions;
      onProgress?: (fileId: string, progress: number) => void;
    }): Promise<MediaFile[]> => {
      // Note: onProgress not implemented for batch upload yet
      const uploadPromises = files.map(async (file, _index) => {
        try {
          // Use the same upload logic as single file
          const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
          const formData = new FormData();
          formData.append('file', file);
          formData.append('title', file.name);
          formData.append('language', options.language || 'auto');
          formData.append('method', 'advanced');
          
          const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.TRANSCRIPTIONS.UPLOAD}`, {
            method: 'POST',
            headers: {
              ...(apiClient.authToken && { Authorization: `Bearer ${apiClient.authToken}` }),
            },
            body: formData,
          });
          
          if (!response.ok) {
            throw new Error('Upload failed');
          }
          
          const transcription = await response.json();
          
          return {
            id: transcription.id,
            name: transcription.title,
            originalName: file.name,
            size: file.size,
            type: file.type.startsWith('video/') ? 'video' : 'audio',
            mimeType: file.type,
            uploadedAt: transcription.created_at,
            status: transcription.status === 'processing' ? 'processing' : 'completed',
            metadata: {
              format: file.name.split('.').pop() || 'unknown',
            },
            processingJobs: [transcription.id],
          } as MediaFile;
        } catch (error) {
          console.error(`Failed to upload ${file.name}:`, error);
          throw error;
        }
      });

      return Promise.all(uploadPromises);
    },
    onSuccess: (uploadedFiles) => {
      // Update media list cache
      queryClient.setQueryData(['media', 'list'], (oldData: any) => {
        if (!oldData) return { files: uploadedFiles };
        return {
          ...oldData,
          files: [...uploadedFiles, ...oldData.files],
        };
      });

      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });

  // Helper functions
  const uploadFile = (
    file: File,
    options?: UploadOptions,
    onProgress?: (progress: number) => void
  ) => {
    return uploadMutation.mutateAsync({ file, options, onProgress });
  };

  const uploadMultipleFiles = (
    files: File[],
    options?: UploadOptions,
    onProgress?: (fileId: string, progress: number) => void
  ) => {
    return uploadMultipleMutation.mutateAsync({ files, options, onProgress });
  };

  // Validation functions
  const validateFile = (file: File): { valid: boolean; error?: string } => {
    const maxSize = 500 * 1024 * 1024; // 500MB
    const allowedTypes = [
      'audio/mpeg',
      'audio/wav',
      'audio/mp4',
      'audio/webm',
      'video/mp4',
      'video/webm',
      'video/quicktime',
      'video/x-msvideo',
      'application/pdf',
      'text/plain',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ];

    if (file.size > maxSize) {
      return {
        valid: false,
        error: `File size must be less than ${maxSize / (1024 * 1024)}MB`,
      };
    }

    if (!allowedTypes.includes(file.type)) {
      return {
        valid: false,
        error: 'File type not supported',
      };
    }

    return { valid: true };
  };

  const validateFiles = (files: File[]): { valid: boolean; errors: string[] } => {
    const errors: string[] = [];
    
    files.forEach((file, index) => {
      const validation = validateFile(file);
      if (!validation.valid) {
        errors.push(`File ${index + 1} (${file.name}): ${validation.error}`);
      }
    });

    return {
      valid: errors.length === 0,
      errors,
    };
  };

  return {
    // Actions
    uploadFile,
    uploadMultipleFiles,
    
    // Validation
    validateFile,
    validateFiles,
    
    // State
    isUploading: uploadMutation.isPending || uploadMultipleMutation.isPending,
    uploadError: uploadMutation.error || uploadMultipleMutation.error,
    
    // Single file upload state
    isSingleUploading: uploadMutation.isPending,
    singleUploadError: uploadMutation.error,
    
    // Multiple files upload state
    isMultipleUploading: uploadMultipleMutation.isPending,
    multipleUploadError: uploadMultipleMutation.error,
  };
}

// Hook for media file management - using transcriptions
export function useMediaFiles() {
  const queryClient = useQueryClient();

  // Get transcriptions as media files
  const {
    data: mediaFiles,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['transcriptions'],
    queryFn: async (): Promise<{ files: MediaFile[]; total: number }> => {
      const response = await apiClient.get<Array<{
        id: string;
        title: string;
        status: string;
        created_at: string;
        duration?: number;
      }>>(API_ENDPOINTS.TRANSCRIPTIONS.LIST);
      
      const files = response.map(t => ({
        id: t.id,
        name: t.title,
        originalName: t.title,
        size: 0, // Not available from transcription API
        type: 'audio' as const,
        mimeType: 'audio/mpeg',
        uploadedAt: t.created_at,
        status: t.status as 'processing' | 'completed' | 'failed',
        metadata: {},
        processingJobs: [t.id],
      })) as MediaFile[];
      
      return { files, total: files.length };
    },
  });

  // Delete transcription mutation
  const deleteMutation = useMutation({
    mutationFn: async (fileId: string): Promise<void> => {
      await apiClient.delete(API_ENDPOINTS.TRANSCRIPTIONS.DELETE(fileId));
    },
    onSuccess: (_, fileId) => {
      // Remove from cache
      queryClient.setQueryData(['media', 'list'], (oldData: any) => {
        if (!oldData) return oldData;
        return {
          ...oldData,
          files: oldData.files.filter((file: MediaFile) => file.id !== fileId),
          total: oldData.total - 1,
        };
      });

      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'stats'] });
    },
  });

  // Get transcription details
  const getFileDetails = (fileId: string) => {
    return useQuery({
      queryKey: ['transcriptions', fileId],
      queryFn: async (): Promise<MediaFile> => {
        const response = await apiClient.get<{
          id: string;
          title: string;
          status: string;
          created_at: string;
          text?: string;
        }>(API_ENDPOINTS.TRANSCRIPTIONS.DETAILS(fileId));
        
        return {
          id: response.id,
          name: response.title,
          originalName: response.title,
          size: 0,
          type: 'audio' as const,
          mimeType: 'audio/mpeg',
          uploadedAt: response.created_at,
          status: response.status as 'processing' | 'completed' | 'failed',
          metadata: {},
          processingJobs: [response.id],
        };
      },
      enabled: !!fileId,
    });
  };

  const deleteFile = (fileId: string) => {
    return deleteMutation.mutateAsync(fileId);
  };

  return {
    // Data
    mediaFiles: mediaFiles?.files || [],
    totalFiles: mediaFiles?.total || 0,
    
    // State
    isLoading,
    error,
    isDeleting: deleteMutation.isPending,
    deleteError: deleteMutation.error,
    
    // Actions
    deleteFile,
    refetch,
    getFileDetails,
  };
}

// Hook for supported file formats
export function useSupportedFormats() {
  return useQuery({
    queryKey: ['media', 'supported-formats'],
    queryFn: async () => {
      const response = await apiClient.get<{
        formats: {
          audio: string[];
          video: string[];
          document: string[];
          image: string[];
        };
        limits: {
          maxFileSize: number;
          maxDuration: number;
          maxFiles: number;
        };
      }>('/api/media/supported-formats');
      return response;
    },
    staleTime: 24 * 60 * 60 * 1000, // 24 hours
  });
}