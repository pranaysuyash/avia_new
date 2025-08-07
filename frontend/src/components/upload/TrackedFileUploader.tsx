/**
 * Tracked File Uploader Component
 * File uploader with integrated PostHog funnel tracking
 */

import React, { useCallback } from 'react';
import { FileUploader } from './FileUploader';
import { trackFunnelEvent } from '../../utils/posthog';

interface TrackedFileUploaderProps {
  accept?: string;
  maxSize?: number;
  onUploadComplete?: (fileKey: string, uploadId: string, file: File) => void;
  onUploadError?: (error: Error) => void;
  className?: string;
}

export const TrackedFileUploader: React.FC<TrackedFileUploaderProps> = ({
  onUploadComplete,
  onUploadError,
  ...props
}) => {
  const handleUploadComplete = useCallback((fileKey: string, uploadId: string, file: File) => {
    // Track successful upload
    trackFunnelEvent('UPLOAD_COMPLETED', {
      file_key: fileKey,
      upload_id: uploadId,
      file_name: file.name,
      file_size: file.size,
      file_type: file.type,
      duration_ms: performance.now(),
    });
    
    onUploadComplete?.(fileKey, uploadId, file);
  }, [onUploadComplete]);

  const handleUploadError = useCallback((error: Error) => {
    // Track upload failure
    trackFunnelEvent('UPLOAD_FAILED', {
      error_message: error.message,
      error_type: error.name,
    });
    
    onUploadError?.(error);
  }, [onUploadError]);

  return (
    <FileUploader
      {...props}
      onUploadComplete={handleUploadComplete}
      onUploadError={handleUploadError}
    />
  );
};

/**
 * Hook for tracking upload progress
 */
export function useTrackedUpload() {
  const trackFileSelected = useCallback((file: File) => {
    trackFunnelEvent('UPLOAD_FILE_SELECTED', {
      file_name: file.name,
      file_size: file.size,
      file_type: file.type,
    });
  }, []);

  const trackUploadStarted = useCallback((file: File) => {
    trackFunnelEvent('UPLOAD_STARTED', {
      file_name: file.name,
      file_size: file.size,
      file_type: file.type,
    });
  }, []);

  const trackUploadProgress = useCallback((progress: number, file: File) => {
    // Only track at specific milestones to avoid too many events
    const milestones = [25, 50, 75, 90];
    const progressPercentage = Math.round(progress);
    
    if (milestones.includes(progressPercentage)) {
      trackFunnelEvent('UPLOAD_PROGRESS', {
        progress: progressPercentage,
        file_name: file.name,
        file_size: file.size,
      });
    }
  }, []);

  return {
    trackFileSelected,
    trackUploadStarted,
    trackUploadProgress,
  };
}