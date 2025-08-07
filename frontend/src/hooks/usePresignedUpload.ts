/**
 * React Hook for Presigned URL File Uploads
 * Handles direct uploads to S3 with progress tracking
 */

import { useState, useCallback, useRef } from 'react';
import axios, { AxiosProgressEvent, CancelTokenSource } from 'axios';

interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

interface PresignedUploadResponse {
  upload_id: string;
  upload_url: string;
  upload_fields: Record<string, string>;
  file_key: string;
  expires_at: string;
}

interface MultipartUploadResponse {
  upload_id: string;
  file_key: string;
  part_urls: Array<{
    part_number: number;
    url: string;
    size: number;
  }>;
  part_size: number;
}

interface UsePresignedUploadOptions {
  onProgress?: (progress: UploadProgress) => void;
  onSuccess?: (fileKey: string, uploadId: string) => void;
  onError?: (error: Error) => void;
  multipartThreshold?: number; // Default 100MB
  partSize?: number; // Default 10MB
}

export function usePresignedUpload(options: UsePresignedUploadOptions = {}) {
  const {
    onProgress,
    onSuccess,
    onError,
    multipartThreshold = 104857600, // 100MB
    partSize = 10485760, // 10MB
  } = options;

  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState<UploadProgress>({ loaded: 0, total: 0, percentage: 0 });
  const [error, setError] = useState<Error | null>(null);
  
  const cancelTokenRef = useRef<CancelTokenSource | null>(null);
  const uploadIdRef = useRef<string | null>(null);

  /**
   * Request presigned URL from backend
   */
  const getPresignedUrl = async (
    file: File,
    metadata?: Record<string, string>
  ): Promise<PresignedUploadResponse> => {
    const response = await axios.post('/api/v1/uploads/presigned', {
      filename: file.name,
      content_type: file.type || 'application/octet-stream',
      file_size: file.size,
      metadata,
    });
    
    return response.data;
  };

  /**
   * Request multipart upload URLs from backend
   */
  const getMultipartUrls = async (
    file: File,
    partSize: number
  ): Promise<MultipartUploadResponse> => {
    const response = await axios.post('/api/v1/uploads/multipart', {
      filename: file.name,
      content_type: file.type || 'application/octet-stream',
      file_size: file.size,
      part_size: partSize,
    });
    
    return response.data;
  };

  /**
   * Upload file using presigned POST (single upload)
   */
  const uploadWithPresignedPost = async (
    file: File,
    presignedData: PresignedUploadResponse
  ): Promise<void> => {
    const formData = new FormData();
    
    // Add all fields from presigned response
    Object.entries(presignedData.upload_fields).forEach(([key, value]) => {
      formData.append(key, value);
    });
    
    // File must be added last
    formData.append('file', file);
    
    // Create cancel token
    cancelTokenRef.current = axios.CancelToken.source();
    
    // Upload directly to S3
    await axios.post(presignedData.upload_url, formData, {
      cancelToken: cancelTokenRef.current.token,
      onUploadProgress: (progressEvent: AxiosProgressEvent) => {
        const loaded = progressEvent.loaded || 0;
        const total = progressEvent.total || file.size;
        const percentage = Math.round((loaded * 100) / total);
        
        const progress = { loaded, total, percentage };
        setProgress(progress);
        onProgress?.(progress);
      },
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  };

  /**
   * Upload file using multipart upload (for large files)
   */
  const uploadWithMultipart = async (
    file: File,
    multipartData: MultipartUploadResponse
  ): Promise<void> => {
    const parts: Array<{ PartNumber: number; ETag: string }> = [];
    let totalUploaded = 0;
    
    // Create cancel token
    cancelTokenRef.current = axios.CancelToken.source();
    
    // Upload each part
    for (const partInfo of multipartData.part_urls) {
      const start = (partInfo.part_number - 1) * multipartData.part_size;
      const end = Math.min(start + partInfo.size, file.size);
      const blob = file.slice(start, end);
      
      try {
        const response = await axios.put(partInfo.url, blob, {
          cancelToken: cancelTokenRef.current.token,
          onUploadProgress: (progressEvent: AxiosProgressEvent) => {
            const partLoaded = progressEvent.loaded || 0;
            const loaded = totalUploaded + partLoaded;
            const total = file.size;
            const percentage = Math.round((loaded * 100) / total);
            
            const progress = { loaded, total, percentage };
            setProgress(progress);
            onProgress?.(progress);
          },
          headers: {
            'Content-Type': file.type || 'application/octet-stream',
          },
        });
        
        // Extract ETag from response headers
        const etag = response.headers.etag?.replace(/"/g, '');
        if (etag) {
          parts.push({
            PartNumber: partInfo.part_number,
            ETag: etag,
          });
        }
        
        totalUploaded += partInfo.size;
      } catch (error) {
        // Abort the multipart upload on error
        if (uploadIdRef.current) {
          await axios.post('/api/v1/uploads/multipart/abort', {
            upload_id: multipartData.upload_id,
            file_key: multipartData.file_key,
          }).catch(() => {}); // Ignore abort errors
        }
        throw error;
      }
    }
    
    // Complete the multipart upload
    await axios.post('/api/v1/uploads/multipart/complete', {
      upload_id: multipartData.upload_id,
      file_key: multipartData.file_key,
      parts,
    });
  };

  /**
   * Verify upload completion
   */
  const verifyUpload = async (uploadId: string): Promise<boolean> => {
    try {
      const response = await axios.post(`/api/v1/uploads/verify/${uploadId}`);
      return response.data.exists;
    } catch {
      return false;
    }
  };

  /**
   * Main upload function
   */
  const upload = useCallback(async (
    file: File,
    metadata?: Record<string, string>
  ): Promise<{ fileKey: string; uploadId: string }> => {
    setIsUploading(true);
    setError(null);
    setProgress({ loaded: 0, total: file.size, percentage: 0 });
    
    try {
      let fileKey: string;
      let uploadId: string;
      
      if (file.size > multipartThreshold) {
        // Use multipart upload for large files
        const multipartData = await getMultipartUrls(file, partSize);
        uploadId = multipartData.upload_id;
        fileKey = multipartData.file_key;
        uploadIdRef.current = uploadId;
        
        await uploadWithMultipart(file, multipartData);
      } else {
        // Use presigned POST for smaller files
        const presignedData = await getPresignedUrl(file, metadata);
        uploadId = presignedData.upload_id;
        fileKey = presignedData.file_key;
        uploadIdRef.current = uploadId;
        
        await uploadWithPresignedPost(file, presignedData);
      }
      
      // Verify upload
      const verified = await verifyUpload(uploadId);
      if (!verified) {
        throw new Error('Upload verification failed');
      }
      
      onSuccess?.(fileKey, uploadId);
      return { fileKey, uploadId };
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Upload failed');
      setError(error);
      onError?.(error);
      throw error;
    } finally {
      setIsUploading(false);
      cancelTokenRef.current = null;
      uploadIdRef.current = null;
    }
  }, [multipartThreshold, partSize, onSuccess, onError, onProgress]);

  /**
   * Cancel ongoing upload
   */
  const cancel = useCallback(() => {
    if (cancelTokenRef.current) {
      cancelTokenRef.current.cancel('Upload cancelled by user');
      
      // Abort multipart upload if in progress
      if (uploadIdRef.current) {
        axios.post('/api/v1/uploads/multipart/abort', {
          upload_id: uploadIdRef.current,
        }).catch(() => {}); // Ignore abort errors
      }
    }
  }, []);

  /**
   * Generate download URL for uploaded file
   */
  const getDownloadUrl = useCallback(async (
    fileKey: string,
    filename?: string,
    expiresIn: number = 3600
  ): Promise<string> => {
    const response = await axios.get(`/api/v1/uploads/download/${fileKey}`, {
      params: { filename, expires_in: expiresIn },
    });
    
    return response.data.download_url;
  }, []);

  return {
    upload,
    cancel,
    getDownloadUrl,
    isUploading,
    progress,
    error,
  };
}