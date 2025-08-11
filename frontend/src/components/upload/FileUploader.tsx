/**
 * File Uploader Component
 * Handles file selection and upload with progress tracking
 */

import React, { useState, useRef, useCallback } from 'react';
import { usePresignedUpload } from '../../hooks/usePresignedUpload';
import { webTheme } from '../../shared/theme';
import { formatFileSize, formatDuration } from '../../utils/formatters';

interface FileUploaderProps {
  accept?: string;
  maxSize?: number; // in bytes
  onUploadComplete?: (fileKey: string, uploadId: string, file: File) => void;
  onUploadError?: (error: Error) => void;
  className?: string;
}

export const FileUploader: React.FC<FileUploaderProps> = ({
  accept = 'audio/*,video/*',
  maxSize = 5368709120, // 5GB default
  onUploadComplete,
  onUploadError,
  className = '',
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadStartTime, setUploadStartTime] = useState<number | null>(null);
  const [uploadSpeed, setUploadSpeed] = useState<number>(0);
  const [timeRemaining, setTimeRemaining] = useState<number | null>(null);

  const {
    upload,
    cancel,
    isUploading,
    progress,
    error,
  } = usePresignedUpload({
    onProgress: (progress) => {
      // Calculate upload speed and time remaining
      if (uploadStartTime) {
        const elapsedSeconds = (Date.now() - uploadStartTime) / 1000;
        const bytesPerSecond = progress.loaded / elapsedSeconds;
        setUploadSpeed(bytesPerSecond);
        
        const remainingBytes = progress.total - progress.loaded;
        const remainingSeconds = remainingBytes / bytesPerSecond;
        setTimeRemaining(Math.ceil(remainingSeconds));
      }
    },
    onSuccess: (fileKey, uploadId) => {
      if (selectedFile) {
        onUploadComplete?.(fileKey, uploadId, selectedFile);
      }
      setSelectedFile(null);
      setUploadStartTime(null);
      setUploadSpeed(0);
      setTimeRemaining(null);
    },
    onError: (error) => {
      onUploadError?.(error);
      setUploadStartTime(null);
      setUploadSpeed(0);
      setTimeRemaining(null);
    },
  });

  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file size
    if (file.size > maxSize) {
      const error = new Error(`File size exceeds maximum of ${formatFileSize(maxSize)}`);
      onUploadError?.(error);
      return;
    }

    setSelectedFile(file);
  }, [maxSize, onUploadError]);

  const handleUpload = useCallback(async () => {
    if (!selectedFile) return;

    setUploadStartTime(Date.now());
    try {
      await upload(selectedFile);
    } catch (error) {
      // Error is handled by the hook
    }
  }, [selectedFile, upload]);

  const handleCancel = useCallback(() => {
    cancel();
    setSelectedFile(null);
    setUploadStartTime(null);
    setUploadSpeed(0);
    setTimeRemaining(null);
  }, [cancel]);

  const handleDrop = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();

    const file = event.dataTransfer.files[0];
    if (file) {
      // Validate file size
      if (file.size > maxSize) {
        const error = new Error(`File size exceeds maximum of ${formatFileSize(maxSize)}`);
        onUploadError?.(error);
        return;
      }
      setSelectedFile(file);
    }
  }, [maxSize, onUploadError]);

  const handleDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
  }, []);

  return (
    <div className={`file-uploader ${className}`}>
      {/* File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        onChange={handleFileSelect}
        style={{ display: 'none' }}
      />

      {/* Upload Area */}
      {!selectedFile && !isUploading && (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onClick={() => fileInputRef.current?.click()}
          style={{
            border: `2px dashed ${webTheme.colors.border.DEFAULT}`,
            borderRadius: webTheme.borderRadius.lg,
            padding: webTheme.spacing['8'],
            textAlign: 'center',
            cursor: 'pointer',
            backgroundColor: webTheme.colors.background.secondary,
            transition: 'all 200ms',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = webTheme.colors.primary.DEFAULT;
            e.currentTarget.style.backgroundColor = webTheme.colors.primary['50'];
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = webTheme.colors.border.DEFAULT;
            e.currentTarget.style.backgroundColor = webTheme.colors.background.secondary;
          }}
        >
          <div style={{ marginBottom: webTheme.spacing['4'] }}>
            <svg
              width="48"
              height="48"
              viewBox="0 0 24 24"
              fill="none"
              style={{ margin: '0 auto' }}
            >
              <path
                d="M7 10V9C7 6.23858 9.23858 4 12 4C14.7614 4 17 6.23858 17 9V10M7 10C4.23858 10 2 12.2386 2 15C2 17.7614 4.23858 20 7 20H17C19.7614 20 22 17.7614 22 15C22 12.2386 19.7614 10 17 10M7 10H17"
                stroke={webTheme.colors.primary.DEFAULT}
                strokeWidth="2"
                strokeLinecap="round"
              />
              <path
                d="M12 10V16M12 10L9 13M12 10L15 13"
                stroke={webTheme.colors.primary.DEFAULT}
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <p
            style={{
              fontSize: webTheme.typography.fontSize.lg,
              fontWeight: webTheme.typography.fontWeight.medium,
              color: webTheme.colors.text.primary,
              marginBottom: webTheme.spacing['2'],
            }}
          >
            Drop your file here or click to browse
          </p>
          <p
            style={{
              fontSize: webTheme.typography.fontSize.sm,
              color: webTheme.colors.text.secondary,
            }}
          >
            Supports audio and video files up to {formatFileSize(maxSize)}
          </p>
        </div>
      )}

      {/* Selected File */}
      {selectedFile && !isUploading && (
        <div
          style={{
            border: `1px solid ${webTheme.colors.border.DEFAULT}`,
            borderRadius: webTheme.borderRadius.lg,
            padding: webTheme.spacing['4'],
            backgroundColor: webTheme.colors.background.primary,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <p
                style={{
                  fontSize: webTheme.typography.fontSize.base,
                  fontWeight: webTheme.typography.fontWeight.medium,
                  color: webTheme.colors.text.primary,
                  marginBottom: webTheme.spacing['1'],
                }}
              >
                {selectedFile.name}
              </p>
              <p
                style={{
                  fontSize: webTheme.typography.fontSize.sm,
                  color: webTheme.colors.text.secondary,
                }}
              >
                {formatFileSize(selectedFile.size)} • {selectedFile.type || 'Unknown type'}
              </p>
            </div>
            <div style={{ display: 'flex', gap: webTheme.spacing['2'] }}>
              <button
                onClick={() => setSelectedFile(null)}
                style={{
                  padding: `${webTheme.spacing['2']} ${webTheme.spacing['4']}`,
                  borderRadius: webTheme.borderRadius.md,
                  border: `1px solid ${webTheme.colors.border.DEFAULT}`,
                  backgroundColor: webTheme.colors.background.primary,
                  color: webTheme.colors.text.primary,
                  fontSize: webTheme.typography.fontSize.sm,
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleUpload}
                style={{
                  padding: `${webTheme.spacing['2']} ${webTheme.spacing['4']}`,
                  borderRadius: webTheme.borderRadius.md,
                  backgroundColor: webTheme.colors.primary.DEFAULT,
                  color: webTheme.colors.text.inverse,
                  fontSize: webTheme.typography.fontSize.sm,
                  fontWeight: webTheme.typography.fontWeight.medium,
                  cursor: 'pointer',
                  border: 'none',
                }}
              >
                Upload
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Upload Progress */}
      {isUploading && (
        <div
          style={{
            border: `1px solid ${webTheme.colors.border.DEFAULT}`,
            borderRadius: webTheme.borderRadius.lg,
            padding: webTheme.spacing['4'],
            backgroundColor: webTheme.colors.background.primary,
          }}
        >
          <div style={{ marginBottom: webTheme.spacing['3'] }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: webTheme.spacing['2'] }}>
              <span
                style={{
                  fontSize: webTheme.typography.fontSize.sm,
                  color: webTheme.colors.text.primary,
                }}
              >
                Uploading {selectedFile?.name}
              </span>
              <span
                style={{
                  fontSize: webTheme.typography.fontSize.sm,
                  color: webTheme.colors.text.secondary,
                }}
              >
                {progress.percentage}%
              </span>
            </div>
            <div
              style={{
                height: '8px',
                backgroundColor: webTheme.colors.gray['200'],
                borderRadius: webTheme.borderRadius.full,
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  height: '100%',
                  backgroundColor: webTheme.colors.primary.DEFAULT,
                  width: `${progress.percentage}%`,
                  transition: 'width 300ms ease',
                }}
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div
              style={{
                fontSize: webTheme.typography.fontSize.xs,
                color: webTheme.colors.text.secondary,
              }}
            >
              <span>{formatFileSize(progress.loaded)} of {formatFileSize(progress.total)}</span>
              {uploadSpeed > 0 && (
                <>
                  <span> • </span>
                  <span>{formatFileSize(uploadSpeed)}/s</span>
                </>
              )}
              {timeRemaining !== null && (
                <>
                  <span> • </span>
                  <span>{formatDuration(timeRemaining)} remaining</span>
                </>
              )}
            </div>
            <button
              onClick={handleCancel}
              style={{
                padding: `${webTheme.spacing['1']} ${webTheme.spacing['3']}`,
                borderRadius: webTheme.borderRadius.md,
                backgroundColor: webTheme.colors.error['50'],
                color: webTheme.colors.error.DEFAULT,
                fontSize: webTheme.typography.fontSize.sm,
                cursor: 'pointer',
                border: 'none',
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div
          style={{
            marginTop: webTheme.spacing['3'],
            padding: webTheme.spacing['3'],
            backgroundColor: webTheme.colors.error['50'],
            borderRadius: webTheme.borderRadius.md,
            border: `1px solid ${webTheme.colors.error['200']}`,
          }}
        >
          <p
            style={{
              fontSize: webTheme.typography.fontSize.sm,
              color: webTheme.colors.error['700'],
            }}
          >
            {error.message}
          </p>
        </div>
      )}
    </div>
  );
};