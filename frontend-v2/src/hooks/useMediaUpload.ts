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

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async ({
      file,
      options = {},
      onProgress,
    }: {
      file: File;
      options?: UploadOptions;
      onProgress?: (progress: number) => void;
    }): Promise<MediaFile> => {
      const response = await apiClient.uploadFile<{ file: MediaFile }>(
        API_ENDPOINTS.MEDIA.UPLOAD,
        file,
        options,
        onProgress
      );
      return response.file;
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

  // Multiple files upload
  const uploadMultipleMutation = useMutation({
    mutationFn: async ({
      files,
      options = {},
      onProgress,
    }: {
      files: File[];
      options?: UploadOptions;
      onProgress?: (fileId: string, progress: number) => void;
    }): Promise<MediaFile[]> => {
      const uploadPromises = files.map(async (file, index) => {
        const fileId = `temp-${index}-${Date.now()}`;
        try {
          const response = await apiClient.uploadFile<{ file: MediaFile }>(
            API_ENDPOINTS.MEDIA.UPLOAD,
            file,
            options,
            (progress) => onProgress?.(fileId, progress)
          );
          return response.file;
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

// Hook for media file management
export function useMediaFiles() {
  const queryClient = useQueryClient();

  // Get media files list
  const {
    data: mediaFiles,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['media', 'list'],
    queryFn: async (): Promise<{ files: MediaFile[]; total: number }> => {
      const response = await apiClient.get<{
        files: MediaFile[];
        total: number;
      }>(API_ENDPOINTS.MEDIA.LIST);
      return response;
    },
  });

  // Delete file mutation
  const deleteMutation = useMutation({
    mutationFn: async (fileId: string): Promise<void> => {
      await apiClient.delete(API_ENDPOINTS.MEDIA.DELETE(fileId));
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

  // Get file details
  const getFileDetails = (fileId: string) => {
    return useQuery({
      queryKey: ['media', 'details', fileId],
      queryFn: async (): Promise<MediaFile> => {
        const response = await apiClient.get<{ file: MediaFile }>(
          API_ENDPOINTS.MEDIA.DETAILS(fileId)
        );
        return response.file;
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