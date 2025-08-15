/**
 * File Upload Component
 * Accessible, drag-and-drop file upload with preview
 * Follows WCAG 2.1 AA guidelines and unified design system
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FiUpload,
  FiFile,
  FiImage,
  FiVideo,
  FiMusic,
  FiX,
  FiCheck,
  FiAlertCircle,
  FiDownload,
  FiEye,
  FiTrash2,
  FiRotateCcw,
  FiPlay,
  FiPause
} from 'react-icons/fi';
import { ThemeProvider } from '../../shared/theme';

// Interfaces
interface UploadedFile {
  id: string;
  file: File;
  name: string;
  size: number;
  type: string;
  status: 'uploading' | 'completed' | 'error' | 'processing';
  progress: number;
  preview?: string;
  error?: string;
  url?: string;
}

interface FileUploadProps {
  // Upload configuration
  accept?: string;
  multiple?: boolean;
  maxFiles?: number;
  maxSize?: number; // in bytes
  minSize?: number;
  
  // UI configuration
  variant?: 'default' | 'compact' | 'minimal' | 'gallery';
  disabled?: boolean;
  required?: boolean;
  
  // Upload behavior
  autoUpload?: boolean;
  showPreview?: boolean;
  allowRetry?: boolean;
  
  // Callbacks
  onFileSelect?: (files: File[]) => void;
  onUpload?: (file: File) => Promise<{ url: string; id: string }>;
  onRemove?: (fileId: string) => void;
  onError?: (error: string, file?: File) => void;
  
  // Labels and content
  title?: string;
  description?: string;
  dragText?: string;
  browseText?: string;
  className?: string;
  
  // Initial files
  initialFiles?: UploadedFile[];
}

// File type detection helpers
const getFileIcon = (type: string) => {
  if (type.startsWith('image/')) return FiImage;
  if (type.startsWith('video/')) return FiVideo;
  if (type.startsWith('audio/')) return FiMusic;
  return FiFile;
};

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const isImageFile = (type: string) => type.startsWith('image/');
const isVideoFile = (type: string) => type.startsWith('video/');
const isAudioFile = (type: string) => type.startsWith('audio/');

// Generate preview for supported file types
const generatePreview = (file: File): Promise<string | null> => {
  return new Promise((resolve) => {
    if (!isImageFile(file.type) && !isVideoFile(file.type)) {
      resolve(null);
      return;
    }
    
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target?.result as string);
    reader.onerror = () => resolve(null);
    reader.readAsDataURL(file);
  });
};

// Accessibility helpers
const announceToScreenReader = (message: string) => {
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', 'polite');
  announcement.setAttribute('aria-atomic', 'true');
  announcement.className = 'sr-only';
  announcement.textContent = message;
  document.body.appendChild(announcement);
  
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
};

export const FileUpload: React.FC<FileUploadProps> = ({
  accept = '*/*',
  multiple = true,
  maxFiles = 10,
  maxSize = 500 * 1024 * 1024, // 500MB
  minSize = 0,
  
  variant = 'default',
  disabled = false,
  required = false,
  
  autoUpload = false,
  showPreview = true,
  allowRetry = true,
  
  onFileSelect,
  onUpload,
  onRemove,
  onError,
  
  title = 'Upload Files',
  description = 'Drag and drop files here or click to browse',
  dragText = 'Drop files here',
  browseText = 'Choose Files',
  className = '',
  
  initialFiles = []
}) => {
  // State
  const [files, setFiles] = useState<UploadedFile[]>(initialFiles);
  const [isDragging, setIsDragging] = useState(false);
  const [dragCounter, setDragCounter] = useState(0);
  
  // Refs
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropZoneRef = useRef<HTMLDivElement>(null);
  
  // Theme
  const theme = ThemeProvider.web;
  const prefersReducedMotion = ThemeProvider.prefersReducedMotion();
  
  // File validation
  const validateFile = useCallback((file: File): string | null => {
    if (file.size > maxSize) {
      return `File size must be less than ${formatFileSize(maxSize)}`;
    }
    
    if (file.size < minSize) {
      return `File size must be at least ${formatFileSize(minSize)}`;
    }
    
    // Check accept pattern
    if (accept !== '*/*') {
      const acceptTypes = accept.split(',').map(type => type.trim());
      const fileType = file.type;
      const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
      
      const isAccepted = acceptTypes.some(acceptType => {
        if (acceptType.startsWith('.')) {
          return acceptType === fileExtension;
        }
        if (acceptType.endsWith('/*')) {
          return fileType.startsWith(acceptType.slice(0, -1));
        }
        return acceptType === fileType;
      });
      
      if (!isAccepted) {
        return `File type not accepted. Allowed types: ${accept}`;
      }
    }
    
    return null;
  }, [accept, maxSize, minSize]);
  
  // Handle file selection
  const handleFiles = useCallback(async (selectedFiles: FileList | File[]) => {
    const fileArray = Array.from(selectedFiles);
    
    // Check max files limit
    if (files.length + fileArray.length > maxFiles) {
      const message = `Cannot upload more than ${maxFiles} files`;
      onError?.(message);
      announceToScreenReader(message);
      return;
    }
    
    // Process each file
    const newFiles: UploadedFile[] = [];
    
    for (const file of fileArray) {
      const error = validateFile(file);
      
      if (error) {
        onError?.(error, file);
        continue;
      }
      
      const uploadedFile: UploadedFile = {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        file,
        name: file.name,
        size: file.size,
        type: file.type,
        status: autoUpload ? 'uploading' : 'completed',
        progress: autoUpload ? 0 : 100
      };
      
      // Generate preview if needed
      if (showPreview) {
        uploadedFile.preview = await generatePreview(file);
      }
      
      newFiles.push(uploadedFile);
    }
    
    setFiles(prev => [...prev, ...newFiles]);
    onFileSelect?.(fileArray);
    
    // Auto-upload if enabled
    if (autoUpload && onUpload) {
      newFiles.forEach(uploadedFile => {
        handleUpload(uploadedFile);
      });
    }
    
    announceToScreenReader(`${newFiles.length} file(s) added`);
  }, [files.length, maxFiles, validateFile, autoUpload, showPreview, onFileSelect, onUpload]);
  
  // Handle file upload
  const handleUpload = useCallback(async (uploadedFile: UploadedFile) => {
    if (!onUpload) return;
    
    setFiles(prev => prev.map(f => 
      f.id === uploadedFile.id 
        ? { ...f, status: 'uploading', progress: 0 }
        : f
    ));
    
    try {
      // Simulate progress (in real implementation, this would come from upload API)
      const progressInterval = setInterval(() => {
        setFiles(prev => prev.map(f => {
          if (f.id === uploadedFile.id && f.progress < 90) {
            return { ...f, progress: f.progress + 10 };
          }
          return f;
        }));
      }, 200);
      
      const result = await onUpload(uploadedFile.file);
      
      clearInterval(progressInterval);
      
      setFiles(prev => prev.map(f => 
        f.id === uploadedFile.id 
          ? { ...f, status: 'completed', progress: 100, url: result.url }
          : f
      ));
      
      announceToScreenReader(`${uploadedFile.name} uploaded successfully`);
    } catch (error) {
      setFiles(prev => prev.map(f => 
        f.id === uploadedFile.id 
          ? { ...f, status: 'error', error: error instanceof Error ? error.message : 'Upload failed' }
          : f
      ));
      
      onError?.(error instanceof Error ? error.message : 'Upload failed', uploadedFile.file);
      announceToScreenReader(`Upload failed for ${uploadedFile.name}`);
    }
  }, [onUpload, onError]);
  
  // Handle file removal
  const handleRemove = useCallback((fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
    onRemove?.(fileId);
    announceToScreenReader('File removed');
  }, [onRemove]);
  
  // Handle retry upload
  const handleRetry = useCallback((uploadedFile: UploadedFile) => {
    if (onUpload) {
      handleUpload(uploadedFile);
    }
  }, [handleUpload, onUpload]);
  
  // Drag and drop handlers
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragCounter(prev => prev + 1);
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  }, []);
  
  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragCounter(prev => prev - 1);
    if (dragCounter <= 1) {
      setIsDragging(false);
    }
  }, [dragCounter]);
  
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);
  
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    setDragCounter(0);
    
    if (disabled) return;
    
    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length > 0) {
      handleFiles(droppedFiles);
    }
  }, [disabled, handleFiles]);
  
  // Handle file input change
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files;
    if (selectedFiles && selectedFiles.length > 0) {
      handleFiles(selectedFiles);
    }
    // Reset input value to allow selecting the same file again
    e.target.value = '';
  }, [handleFiles]);
  
  // Handle browse button click
  const handleBrowseClick = useCallback(() => {
    if (!disabled) {
      fileInputRef.current?.click();
    }
  }, [disabled]);
  
  // Keyboard handlers
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleBrowseClick();
    }
  }, [handleBrowseClick]);
  
  // Get variant-specific classes
  const getDropZoneClasses = () => {
    const base = 'relative transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:ring-offset-2 rounded-lg';
    
    switch (variant) {
      case 'compact':
        return `${base} border-2 border-dashed p-4 ${
          isDragging 
            ? 'border-primary-DEFAULT bg-primary-DEFAULT/5' 
            : 'border-border-DEFAULT hover:border-primary-DEFAULT hover:bg-background-secondary'
        }`;
      case 'minimal':
        return `${base} border border-border-DEFAULT p-3 ${
          isDragging 
            ? 'border-primary-DEFAULT bg-primary-DEFAULT/5' 
            : 'hover:border-primary-DEFAULT hover:bg-background-secondary'
        }`;
      case 'gallery':
        return `${base} border-2 border-dashed p-6 ${
          isDragging 
            ? 'border-primary-DEFAULT bg-primary-DEFAULT/5' 
            : 'border-border-DEFAULT hover:border-primary-DEFAULT hover:bg-background-secondary'
        }`;
      default:
        return `${base} border-2 border-dashed p-8 ${
          isDragging 
            ? 'border-primary-DEFAULT bg-primary-DEFAULT/5' 
            : 'border-border-DEFAULT hover:border-primary-DEFAULT hover:bg-background-secondary'
        }`;
    }
  };
  
  // Render file preview
  const renderFilePreview = (uploadedFile: UploadedFile) => {
    const IconComponent = getFileIcon(uploadedFile.type);
    
    return (
      <motion.div
        key={uploadedFile.id}
        initial={prefersReducedMotion ? {} : { opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={prefersReducedMotion ? {} : { opacity: 0, scale: 0.9 }}
        className={`
          relative bg-background-secondary border border-border-DEFAULT rounded-lg overflow-hidden
          ${variant === 'compact' ? 'p-3' : 'p-4'}
        `}
      >
        {/* Preview/Icon */}
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            {uploadedFile.preview && showPreview ? (
              <div className="relative">
                <img
                  src={uploadedFile.preview}
                  alt={uploadedFile.name}
                  className="w-12 h-12 object-cover rounded border border-border-DEFAULT"
                />
                {isVideoFile(uploadedFile.type) && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <FiPlay className="h-4 w-4 text-background-primary bg-text-primary/80 rounded-full p-1" />
                  </div>
                )}
              </div>
            ) : (
              <div className="w-12 h-12 bg-background-primary border border-border-DEFAULT rounded flex items-center justify-center">
                <IconComponent className="h-6 w-6 text-text-secondary" />
              </div>
            )}
          </div>
          
          {/* File info */}
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-medium text-text-primary truncate">
              {uploadedFile.name}
            </h4>
            <p className="text-xs text-text-secondary">
              {formatFileSize(uploadedFile.size)}
            </p>
            
            {/* Progress bar */}
            {uploadedFile.status === 'uploading' && (
              <div className="mt-2">
                <div className="w-full bg-background-primary rounded-full h-1.5">
                  <motion.div
                    className="bg-primary-DEFAULT h-1.5 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${uploadedFile.progress}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
                <p className="text-xs text-text-secondary mt-1">
                  {uploadedFile.progress}% uploaded
                </p>
              </div>
            )}
            
            {/* Error message */}
            {uploadedFile.status === 'error' && uploadedFile.error && (
              <p className="text-xs text-error-DEFAULT mt-1 flex items-center">
                <FiAlertCircle className="h-3 w-3 mr-1" />
                {uploadedFile.error}
              </p>
            )}
          </div>
          
          {/* Actions */}
          <div className="flex items-center space-x-1">
            {/* Status indicator */}
            {uploadedFile.status === 'completed' && (
              <FiCheck className="h-4 w-4 text-success-DEFAULT" />
            )}
            {uploadedFile.status === 'error' && allowRetry && (
              <button
                onClick={() => handleRetry(uploadedFile)}
                className="p-1 text-text-secondary hover:text-primary-DEFAULT focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT rounded"
                aria-label="Retry upload"
              >
                <FiRotateCcw className="h-4 w-4" />
              </button>
            )}
            
            {/* Preview button */}
            {uploadedFile.url && (
              <button
                onClick={() => window.open(uploadedFile.url, '_blank')}
                className="p-1 text-text-secondary hover:text-primary-DEFAULT focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT rounded"
                aria-label="Preview file"
              >
                <FiEye className="h-4 w-4" />
              </button>
            )}
            
            {/* Remove button */}
            <button
              onClick={() => handleRemove(uploadedFile.id)}
              className="p-1 text-text-secondary hover:text-error-DEFAULT focus:outline-none focus:ring-2 focus:ring-error-DEFAULT rounded"
              aria-label="Remove file"
            >
              <FiX className="h-4 w-4" />
            </button>
          </div>
        </div>
      </motion.div>
    );
  };
  
  return (
    <div className={`w-full ${className}`}>
      {/* Upload area */}
      <div
        ref={dropZoneRef}
        className={getDropZoneClasses()}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={handleBrowseClick}
        onKeyDown={handleKeyDown}
        tabIndex={disabled ? -1 : 0}
        role="button"
        aria-label={`${title}. ${description}`}
        aria-disabled={disabled}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={handleInputChange}
          className="sr-only"
          disabled={disabled}
          required={required}
        />
        
        <div className="text-center">
          {/* Upload icon */}
          <motion.div
            animate={isDragging ? { scale: 1.1 } : { scale: 1 }}
            transition={{ duration: 0.2 }}
            className="mx-auto mb-4"
          >
            <div className={`
              mx-auto rounded-full flex items-center justify-center
              ${variant === 'compact' ? 'w-8 h-8' : variant === 'minimal' ? 'w-10 h-10' : 'w-12 h-12'}
              ${isDragging ? 'bg-primary-DEFAULT text-primary-contrast' : 'bg-background-primary text-text-secondary'}
            `}>
              <FiUpload className={`${variant === 'compact' ? 'h-4 w-4' : 'h-6 w-6'}`} />
            </div>
          </motion.div>
          
          {/* Title and description */}
          <div className="space-y-1">
            <h3 className={`font-medium text-text-primary ${variant === 'compact' ? 'text-sm' : 'text-base'}`}>
              {isDragging ? dragText : title}
            </h3>
            {variant !== 'minimal' && (
              <p className={`text-text-secondary ${variant === 'compact' ? 'text-xs' : 'text-sm'}`}>
                {description}
              </p>
            )}
          </div>
          
          {/* Browse button */}
          {variant !== 'minimal' && (
            <motion.button
              type="button"
              whileHover={prefersReducedMotion ? {} : { scale: 1.02 }}
              whileTap={prefersReducedMotion ? {} : { scale: 0.98 }}
              className={`
                mt-4 px-4 py-2 bg-primary-DEFAULT text-primary-contrast rounded-md
                hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-DEFAULT focus:ring-offset-2
                disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200
                ${variant === 'compact' ? 'text-sm' : 'text-base'}
              `}
              disabled={disabled}
            >
              {browseText}
            </motion.button>
          )}
          
          {/* File constraints */}
          {variant === 'default' && (
            <div className="mt-4 text-xs text-text-tertiary space-y-1">
              {accept !== '*/*' && <p>Accepted types: {accept}</p>}
              <p>Max size: {formatFileSize(maxSize)}</p>
              {multiple && <p>Max files: {maxFiles}</p>}
            </div>
          )}
        </div>
      </div>
      
      {/* File list */}
      {files.length > 0 && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-medium text-text-primary">
              Uploaded Files ({files.length}/{maxFiles})
            </h4>
            {files.length > 1 && (
              <button
                onClick={() => {
                  setFiles([]);
                  announceToScreenReader('All files removed');
                }}
                className="text-xs text-text-secondary hover:text-error-DEFAULT focus:outline-none focus:ring-2 focus:ring-error-DEFAULT rounded px-2 py-1"
              >
                Clear All
              </button>
            )}
          </div>
          
          <div className="space-y-3">
            <AnimatePresence>
              {files.map(renderFilePreview)}
            </AnimatePresence>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUpload;