import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';
import * as FileSystem from 'expo-file-system';

class TranscriptionService {
  constructor() {
    this.baseURL = __DEV__ 
      ? 'http://localhost:8000' // Development server
      : 'https://your-api-server.com'; // Production server
    
    this.apiClient = axios.create({
      baseURL: this.baseURL,
      timeout: 300000, // 5 minutes for large file uploads
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    this.setupInterceptors();
  }

  setupInterceptors() {
    // Request interceptor to add auth token
    this.apiClient.interceptors.request.use(
      async (config) => {
        const token = await AsyncStorage.getItem('authToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.apiClient.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Token expired, clear storage and redirect to login
          await AsyncStorage.multiRemove(['authToken', 'userInfo']);
        }
        return Promise.reject(error);
      }
    );
  }

  async startTranscription(file, analysisMode = 'basic', progressCallback) {
    try {
      // Validate file
      if (!file || !file.uri) {
        throw new Error('Invalid file provided');
      }

      // Check file size (mobile limit: 100MB)
      if (file.size > 100 * 1024 * 1024) {
        throw new Error('File size exceeds 100MB limit for mobile processing');
      }

      progressCallback?.(0.1);

      // Prepare form data
      const formData = new FormData();
      
      // Add file to form data
      formData.append('file', {
        uri: Platform.OS === 'ios' ? file.uri.replace('file://', '') : file.uri,
        type: file.mimeType || 'audio/wav',
        name: file.name || 'recording.wav',
      });

      formData.append('analysis_mode', analysisMode);
      formData.append('platform', 'mobile');
      formData.append('device_info', JSON.stringify({
        platform: Platform.OS,
        version: Platform.Version,
      }));

      progressCallback?.(0.2);

      // Start transcription
      const response = await this.apiClient.post('/api/transcribe', formData, {
        onUploadProgress: (progressEvent) => {
          const uploadProgress = progressEvent.loaded / progressEvent.total;
          progressCallback?.(0.2 + (uploadProgress * 0.3)); // 20-50% for upload
        },
      });

      const { transcription_id } = response.data;
      
      if (!transcription_id) {
        throw new Error('No transcription ID received from server');
      }

      progressCallback?.(0.5);

      // Poll for completion
      const result = await this.pollTranscriptionStatus(
        transcription_id, 
        (pollProgress) => {
          progressCallback?.(0.5 + (pollProgress * 0.5)); // 50-100% for processing
        }
      );

      // Cache result locally
      await this.cacheTranscriptionResult(transcription_id, result);

      return transcription_id;

    } catch (error) {
      console.error('Transcription failed:', error);
      
      // Enhanced error messages for mobile
      if (error.code === 'NETWORK_ERROR' || error.message.includes('timeout')) {
        throw new Error('Network connection failed. Please check your internet connection and try again.');
      } else if (error.response?.status === 413) {
        throw new Error('File too large. Please select a smaller file (max 100MB).');
      } else if (error.response?.status === 415) {
        throw new Error('Unsupported file format. Please use MP3, WAV, MP4, or M4A files.');
      } else {
        throw new Error(error.message || 'Transcription failed. Please try again.');
      }
    }
  }

  async pollTranscriptionStatus(transcriptionId, progressCallback) {
    const maxAttempts = 60; // 5 minutes max
    let attempts = 0;

    while (attempts < maxAttempts) {
      try {
        const response = await this.apiClient.get(`/api/transcription/${transcriptionId}/status`);
        const { status, progress, result, error } = response.data;

        progressCallback?.(progress || 0);

        switch (status) {
          case 'completed':
            return result;
          
          case 'failed':
            throw new Error(error || 'Transcription processing failed');
          
          case 'processing':
          case 'queued':
            // Continue polling
            break;
          
          default:
            throw new Error(`Unknown status: ${status}`);
        }

        // Wait before next poll
        await this.delay(5000); // 5 seconds
        attempts++;

      } catch (error) {
        if (error.response?.status === 404) {
          throw new Error('Transcription not found. It may have expired.');
        }
        throw error;
      }
    }

    throw new Error('Transcription timed out. Please try again with a shorter file.');
  }

  async getTranscriptionResult(transcriptionId) {
    try {
      // Check cache first
      const cached = await this.getCachedTranscriptionResult(transcriptionId);
      if (cached) {
        return cached;
      }

      // Fetch from server
      const response = await this.apiClient.get(`/api/transcription/${transcriptionId}`);
      const result = response.data;

      // Cache for offline access
      await this.cacheTranscriptionResult(transcriptionId, result);

      return result;

    } catch (error) {
      console.error('Failed to get transcription result:', error);
      throw new Error('Failed to load transcription. Please check your connection.');
    }
  }

  async cacheTranscriptionResult(transcriptionId, result) {
    try {
      const cacheKey = `transcription_${transcriptionId}`;
      const cacheData = {
        ...result,
        cached_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days
      };

      await AsyncStorage.setItem(cacheKey, JSON.stringify(cacheData));
      
      // Add to index for cleanup
      const index = await AsyncStorage.getItem('transcription_cache_index');
      const cacheIndex = index ? JSON.parse(index) : [];
      
      if (!cacheIndex.includes(cacheKey)) {
        cacheIndex.push(cacheKey);
        await AsyncStorage.setItem('transcription_cache_index', JSON.stringify(cacheIndex));
      }

    } catch (error) {
      console.warn('Failed to cache transcription result:', error);
    }
  }

  async getCachedTranscriptionResult(transcriptionId) {
    try {
      const cacheKey = `transcription_${transcriptionId}`;
      const cached = await AsyncStorage.getItem(cacheKey);
      
      if (!cached) {
        return null;
      }

      const cacheData = JSON.parse(cached);
      
      // Check if expired
      if (new Date() > new Date(cacheData.expires_at)) {
        await AsyncStorage.removeItem(cacheKey);
        return null;
      }

      return cacheData;

    } catch (error) {
      console.warn('Failed to get cached result:', error);
      return null;
    }
  }

  async getTranscriptionHistory(limit = 20, offset = 0) {
    try {
      const response = await this.apiClient.get('/api/transcriptions', {
        params: { limit, offset }
      });

      return response.data;

    } catch (error) {
      console.error('Failed to get history:', error);
      
      // Return cached results if network fails
      return await this.getCachedHistory();
    }
  }

  async getCachedHistory() {
    try {
      const index = await AsyncStorage.getItem('transcription_cache_index');
      if (!index) {
        return { transcriptions: [], total: 0 };
      }

      const cacheKeys = JSON.parse(index);
      const transcriptions = [];

      for (const key of cacheKeys) {
        const cached = await AsyncStorage.getItem(key);
        if (cached) {
          const data = JSON.parse(cached);
          if (new Date() <= new Date(data.expires_at)) {
            transcriptions.push({
              id: data.id,
              filename: data.filename,
              duration: data.duration,
              created_at: data.created_at,
              status: 'completed',
              cached: true,
            });
          }
        }
      }

      return {
        transcriptions: transcriptions.sort((a, b) => 
          new Date(b.created_at) - new Date(a.created_at)
        ),
        total: transcriptions.length,
      };

    } catch (error) {
      console.warn('Failed to get cached history:', error);
      return { transcriptions: [], total: 0 };
    }
  }

  async cleanupExpiredCache() {
    try {
      const index = await AsyncStorage.getItem('transcription_cache_index');
      if (!index) {
        return;
      }

      const cacheKeys = JSON.parse(index);
      const activeKeys = [];

      for (const key of cacheKeys) {
        const cached = await AsyncStorage.getItem(key);
        if (cached) {
          const data = JSON.parse(cached);
          if (new Date() <= new Date(data.expires_at)) {
            activeKeys.push(key);
          } else {
            await AsyncStorage.removeItem(key);
          }
        }
      }

      await AsyncStorage.setItem('transcription_cache_index', JSON.stringify(activeKeys));

    } catch (error) {
      console.warn('Failed to cleanup cache:', error);
    }
  }

  async deleteTranscription(transcriptionId) {
    try {
      await this.apiClient.delete(`/api/transcription/${transcriptionId}`);
      
      // Remove from cache
      const cacheKey = `transcription_${transcriptionId}`;
      await AsyncStorage.removeItem(cacheKey);
      
      // Update cache index
      const index = await AsyncStorage.getItem('transcription_cache_index');
      if (index) {
        const cacheIndex = JSON.parse(index);
        const updatedIndex = cacheIndex.filter(key => key !== cacheKey);
        await AsyncStorage.setItem('transcription_cache_index', JSON.stringify(updatedIndex));
      }

    } catch (error) {
      console.error('Failed to delete transcription:', error);
      throw new Error('Failed to delete transcription. Please try again.');
    }
  }

  async exportTranscription(transcriptionId, format = 'txt') {
    try {
      const response = await this.apiClient.get(
        `/api/transcription/${transcriptionId}/export`,
        {
          params: { format },
          responseType: 'blob'
        }
      );

      // Save to device
      const filename = `transcription_${transcriptionId}.${format}`;
      const documentDirectory = FileSystem.documentDirectory;
      const fileUri = `${documentDirectory}${filename}`;

      await FileSystem.writeAsStringAsync(fileUri, response.data, {
        encoding: FileSystem.EncodingType.UTF8,
      });

      return fileUri;

    } catch (error) {
      console.error('Export failed:', error);
      throw new Error('Failed to export transcription. Please try again.');
    }
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Offline mode methods
  async isOnline() {
    try {
      const response = await fetch(this.baseURL + '/api/health', {
        method: 'HEAD',
        timeout: 5000,
      });
      return response.ok;
    } catch (error) {
      return false;
    }
  }

  async enableOfflineMode() {
    // In a full implementation, this would download necessary models
    // and enable local processing capabilities
    console.log('Offline mode enabled');
  }
}

export default new TranscriptionService();