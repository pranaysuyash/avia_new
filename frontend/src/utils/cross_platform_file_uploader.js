/**
 * Cross-Platform File Upload Handler
 * Handles file uploads for web, desktop, and mobile platforms
 */

import { Platform } from 'react-native'; // For mobile detection
import { apiClient } from './cross_platform_api';

// File Upload Configuration
export const FILE_UPLOAD_CONFIG = {
  MAX_FILE_SIZE: 2 * 1024 * 1024 * 1024, // 2GB
  CHUNK_SIZE: 50 * 1024 * 1024, // 50MB chunks
  SUPPORTED_FORMATS: [
    'audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/flac', 'audio/aac',
    'video/mp4', 'video/avi', 'video/mov', 'video/wmv', 'video/flv',
    'video/webm', 'video/mkv'
  ],
  SUPPORTED_EXTENSIONS: [
    '.wav', '.mp3', '.m4a', '.flac', '.aac',
    '.mp4', '.avi', '.mov', '.wmv', '.flv',
    '.webm', '.mkv'
  ],
  TIMEOUT: 300000, // 5 minutes
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 2000, // 2 seconds
};

// Cross-Platform File Upload Manager
class CrossPlatformFileUploader {
  constructor() {
    this.uploadProgressCallbacks = new Map();
    this.uploadCancelTokens = new Map();
  }

  // Validate file before upload
  validateFile(file) {
    // Check if file exists
    if (!file) {
      throw new Error('No file provided');
    }

    // Check file size
    if (file.size > FILE_UPLOAD_CONFIG.MAX_FILE_SIZE) {
      throw new Error(`File size exceeds maximum limit of ${FILE_UPLOAD_CONFIG.MAX_FILE_SIZE / (1024 * 1024 * 1024)} GB`);
    }

    // Check file type/extension
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    const fileType = file.type.toLowerCase();
    
    const isValidExtension = FILE_UPLOAD_CONFIG.SUPPORTED_EXTENSIONS.includes(fileExtension);
    const isValidType = FILE_UPLOAD_CONFIG.SUPPORTED_FORMATS.some(format => 
      fileType.includes(format) || format.includes(fileType)
    );
    
    if (!isValidExtension && !isValidType) {
      throw new Error(`Unsupported file type. Supported formats: ${FILE_UPLOAD_CONFIG.SUPPORTED_EXTENSIONS.join(', ')}`);
    }

    return true;
  }

  // Upload file with progress tracking
  async uploadFile(file, onProgress = null, options = {}) {
    try {
      // Validate file
      this.validateFile(file);
      
      // Generate unique upload ID
      const uploadId = `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      // Store progress callback
      if (onProgress) {
        this.uploadProgressCallbacks.set(uploadId, onProgress);
      }
      
      // Determine platform and upload method
      if (this._isWebPlatform()) {
        return await this._uploadFileWeb(file, uploadId, onProgress, options);
      } else if (this._isElectronPlatform()) {
        return await this._uploadFileElectron(file, uploadId, onProgress, options);
      } else if (this._isReactNativePlatform()) {
        return await this._uploadFileReactNative(file, uploadId, onProgress, options);
      } else {
        // Fallback to web upload
        return await this._uploadFileWeb(file, uploadId, onProgress, options);
      }
      
    } catch (error) {
      console.error('File upload error:', error);
      throw error;
    }
  }

  // Upload file using web browser method
  async _uploadFileWeb(file, uploadId, onProgress, options) {
    try {
      // For large files, use chunked upload
      if (file.size > FILE_UPLOAD_CONFIG.CHUNK_SIZE) {
        return await this._uploadFileChunked(file, uploadId, onProgress, options);
      }
      
      // For smaller files, use direct upload
      const formData = new FormData();
      formData.append('file', file);
      
      // Add any additional options
      if (options.metadata) {
        formData.append('metadata', JSON.stringify(options.metadata));
      }
      
      // Create upload request
      const response = await apiClient.uploadFile('/api/upload', file, onProgress);
      
      // Clean up
      this.uploadProgressCallbacks.delete(uploadId);
      
      return response;
      
    } catch (error) {
      // Clean up on error
      this.uploadProgressCallbacks.delete(uploadId);
      throw error;
    }
  }

  // Upload file using Electron method
  async _uploadFileElectron(file, uploadId, onProgress, options) {
    try {
      // Check if we have access to Electron APIs
      if (window.electronAPI && window.electronAPI.uploadFile) {
        // Use Electron's optimized file upload
        const result = await window.electronAPI.uploadFile({
          filePath: file.path, // Electron can access file path directly
          options: options
        });
        
        // Clean up
        this.uploadProgressCallbacks.delete(uploadId);
        
        return result;
      } else {
        // Fallback to web upload
        return await this._uploadFileWeb(file, uploadId, onProgress, options);
      }
      
    } catch (error) {
      // Clean up on error
      this.uploadProgressCallbacks.delete(uploadId);
      throw error;
    }
  }

  // Upload file using React Native method
  async _uploadFileReactNative(file, uploadId, onProgress, options) {
    try {
      // For React Native, we need to handle file URIs
      if (file.uri) {
        // Use React Native specific upload method
        return await this._uploadFileReactNativeURI(file, uploadId, onProgress, options);
      } else {
        // Convert to React Native compatible format
        return await this._uploadFileReactNativeBlob(file, uploadId, onProgress, options);
      }
      
    } catch (error) {
      // Clean up on error
      this.uploadProgressCallbacks.delete(uploadId);
      throw error;
    }
  }

  // Upload file with URI in React Native
  async _uploadFileReactNativeURI(file, uploadId, onProgress, options) {
    try {
      // Use React Native's fetch API with file URI
      const formData = new FormData();
      formData.append('file', {
        uri: file.uri,
        type: file.type || 'audio/wav',
        name: file.name || `recording_${Date.now()}.wav`,
      });
      
      // Add metadata
      if (options.metadata) {
        formData.append('metadata', JSON.stringify(options.metadata));
      }
      
      // Create request
      const response = await apiClient.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress) {
            const progress = (progressEvent.loaded / progressEvent.total) * 100;
            onProgress(progress);
          }
        }
      });
      
      // Clean up
      this.uploadProgressCallbacks.delete(uploadId);
      
      return response;
      
    } catch (error) {
      throw error;
    }
  }

  // Upload file as blob in React Native
  async _uploadFileReactNativeBlob(file, uploadId, onProgress, options) {
    try {
      // Convert file to blob for React Native upload
      const response = await fetch(file.uri || file.path);
      const blob = await response.blob();
      
      // Create React Native compatible file object
      const rnFile = {
        uri: URL.createObjectURL(blob),
        type: file.type || blob.type || 'audio/wav',
        name: file.name || `file_${Date.now()}.wav`,
      };
      
      // Upload using URI method
      return await this._uploadFileReactNativeURI(rnFile, uploadId, onProgress, options);
      
    } catch (error) {
      throw error;
    }
  }

  // Chunked file upload for large files
  async _uploadFileChunked(file, uploadId, onProgress, options) {
    try {
      const fileSize = file.size;
      const chunkSize = FILE_UPLOAD_CONFIG.CHUNK_SIZE;
      const totalChunks = Math.ceil(fileSize / chunkSize);
      
      // Initialize chunked upload
      const initResponse = await apiClient.post('/api/upload/init', {
        fileName: file.name,
        fileSize: fileSize,
        chunkSize: chunkSize,
        totalChunks: totalChunks,
        ...options.metadata
      });
      
      const uploadId = initResponse.uploadId;
      let uploadedChunks = 0;
      
      // Upload chunks
      for (let i = 0; i < totalChunks; i++) {
        const start = i * chunkSize;
        const end = Math.min(start + chunkSize, fileSize);
        const chunk = file.slice(start, end);
        
        // Create chunk upload request
        const formData = new FormData();
        formData.append('chunk', chunk);
        formData.append('uploadId', uploadId);
        formData.append('chunkIndex', i);
        formData.append('fileName', file.name);
        
        // Upload chunk with retry logic
        let chunkUploaded = false;
        let attempts = 0;
        
        while (!chunkUploaded && attempts < FILE_UPLOAD_CONFIG.RETRY_ATTEMPTS) {
          try {
            await apiClient.post('/api/upload/chunk', formData, {
              headers: {
                'Content-Type': 'multipart/form-data',
              }
            });
            
            chunkUploaded = true;
            uploadedChunks++;
            
            // Update progress
            if (onProgress) {
              const progress = (uploadedChunks / totalChunks) * 100;
              onProgress(progress);
            }
            
          } catch (error) {
            attempts++;
            console.warn(`Chunk ${i} upload failed (attempt ${attempts}):`, error);
            
            if (attempts >= FILE_UPLOAD_CONFIG.RETRY_ATTEMPTS) {
              throw new Error(`Failed to upload chunk ${i} after ${FILE_UPLOAD_CONFIG.RETRY_ATTEMPTS} attempts`);
            }
            
            // Wait before retry
            await new Promise(resolve => setTimeout(resolve, FILE_UPLOAD_CONFIG.RETRY_DELAY * attempts));
          }
        }
      }
      
      // Complete upload
      const completeResponse = await apiClient.post('/api/upload/complete', {
        uploadId: uploadId,
        fileName: file.name
      });
      
      // Clean up
      this.uploadProgressCallbacks.delete(uploadId);
      
      return completeResponse;
      
    } catch (error) {
      // Clean up on error
      this.uploadProgressCallbacks.delete(uploadId);
      throw error;
    }
  }

  // Cancel upload
  async cancelUpload(uploadId) {
    try {
      // Cancel any ongoing requests
      if (this.uploadCancelTokens.has(uploadId)) {
        const cancelToken = this.uploadCancelTokens.get(uploadId);
        if (cancelToken && cancelToken.cancel) {
          cancelToken.cancel('Upload cancelled by user');
        }
        this.uploadCancelTokens.delete(uploadId);
      }
      
      // Notify server to clean up
      await apiClient.post('/api/upload/cancel', { uploadId });
      
      // Remove progress callback
      this.uploadProgressCallbacks.delete(uploadId);
      
      return { success: true };
      
    } catch (error) {
      console.error('Cancel upload error:', error);
      return { success: false, error: error.message };
    }
  }

  // Get platform detection
  _isWebPlatform() {
    return typeof window !== 'undefined' && !window.process;
  }

  _isElectronPlatform() {
    return typeof window !== 'undefined' && window.process && window.process.type === 'renderer';
  }

  _isReactNativePlatform() {
    return typeof navigator !== 'undefined' && navigator.product === 'ReactNative';
  }

  // Get file information
  getFileInfo(file) {
    return {
      name: file.name,
      size: file.size,
      type: file.type,
      lastModified: file.lastModified,
      extension: file.name ? file.name.split('.').pop().toLowerCase() : '',
    };
  }

  // Format file size for display
  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
}

// Create singleton instance
export const fileUploader = new CrossPlatformFileUploader();

// Export convenience functions
export const upload = {
  file: fileUploader.uploadFile.bind(fileUploader),
  cancel: fileUploader.cancelUpload.bind(fileUploader),
  validate: fileUploader.validateFile.bind(fileUploader),
  getInfo: fileUploader.getFileInfo.bind(fileUploader),
  formatSize: fileUploader.formatFileSize.bind(fileUploader),
};

export default fileUploader;