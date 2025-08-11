/**
 * Whisper Advanced API Service for React Native
 * Handles API communication with offline support and error handling
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-netinfo/netinfo';

// Types
export interface WhisperConfig {
  model: string;
  language?: string;
  temperature: number;
  enable_language_detection: boolean;
  enable_confidence_analysis: boolean;
  enable_word_timestamps: boolean;
  enable_speaker_detection: boolean;
  confidence_threshold: number;
}

export interface TranscriptionResult {
  text: string;
  language?: string;
  language_confidence?: number;
  segments: Array<{
    id: number;
    start: number;
    end: number;
    text: string;
    confidence?: number;
    speaker_id?: string;
  }>;
  words?: Array<{
    word: string;
    start: number;
    end: number;
    confidence: number;
  }>;
  confidence_analysis?: {
    overall_confidence: number;
    preprocessing_quality: number;
    quality_improvement: number;
  };
  processing_time: number;
  model_used: string;
}

export interface LanguageDetectionResult {
  detected_language: string;
  confidence: number;
  alternative_languages: Array<{[key: string]: number}>;
}

export interface BatchTranscriptionResult {
  results: Array<{
    index: number;
    filename: string;
    status: 'success' | 'error';
    result?: any;
    error?: string;
  }>;
  summary: {
    total_files: number;
    successful: number;
    failed: number;
    total_words: number;
    average_processing_time: number;
    total_processing_time: number;
  };
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
}

// Configuration
const API_BASE_URL = __DEV__ 
  ? 'http://localhost:8000/api/v1' 
  : 'https://your-production-api.com/api/v1';

const CACHE_KEYS = {
  TRANSCRIPTION_CACHE: 'whisper_transcription_cache',
  LANGUAGE_CACHE: 'whisper_language_cache',
  CONFIG_CACHE: 'whisper_config_cache',
  OFFLINE_QUEUE: 'whisper_offline_queue',
};

class WhisperAdvancedAPI {
  private baseURL: string;
  private authToken: string | null = null;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
    this.loadAuthToken();
  }

  // Authentication
  private async loadAuthToken(): Promise<void> {
    try {
      this.authToken = await AsyncStorage.getItem('auth_token');
    } catch (error) {
      console.error('Failed to load auth token:', error);
    }
  }

  public async setAuthToken(token: string): Promise<void> {
    this.authToken = token;
    try {
      await AsyncStorage.setItem('auth_token', token);
    } catch (error) {
      console.error('Failed to save auth token:', error);
    }
  }

  // Network status check
  private async isOnline(): Promise<boolean> {
    const netInfo = await NetInfo.fetch();
    return netInfo.isConnected ?? false;
  }

  // Generic API request method
  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        timeout: 30000, // 30 second timeout
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  // File upload request method
  private async makeFileRequest<T>(
    endpoint: string,
    formData: FormData,
    onProgress?: (progress: number) => void
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    
    const headers: HeadersInit = {};
    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }

    try {
      // Create XMLHttpRequest for progress tracking
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable && onProgress) {
            const progress = (event.loaded / event.total) * 100;
            onProgress(progress);
          }
        });

        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const data = JSON.parse(xhr.responseText);
              resolve(data);
            } catch (error) {
              reject(new Error('Invalid JSON response'));
            }
          } else {
            try {
              const errorData = JSON.parse(xhr.responseText);
              reject(new Error(errorData.detail || `HTTP ${xhr.status}: ${xhr.statusText}`));
            } catch {
              reject(new Error(`HTTP ${xhr.status}: ${xhr.statusText}`));
            }
          }
        });

        xhr.addEventListener('error', () => {
          reject(new Error('Network error'));
        });

        xhr.addEventListener('timeout', () => {
          reject(new Error('Request timeout'));
        });

        xhr.open('POST', url);
        xhr.timeout = 60000; // 60 second timeout for file uploads
        
        // Set headers
        Object.entries(headers).forEach(([key, value]) => {
          xhr.setRequestHeader(key, value);
        });

        xhr.send(formData);
      });
    } catch (error) {
      console.error(`File upload failed for ${endpoint}:`, error);
      throw error;
    }
  }

  // Cache management
  private async getCachedData<T>(key: string): Promise<T | null> {
    try {
      const cached = await AsyncStorage.getItem(key);
      return cached ? JSON.parse(cached) : null;
    } catch (error) {
      console.error('Failed to get cached data:', error);
      return null;
    }
  }

  private async setCachedData<T>(key: string, data: T): Promise<void> {
    try {
      await AsyncStorage.setItem(key, JSON.stringify(data));
    } catch (error) {
      console.error('Failed to cache data:', error);
    }
  }

  // Offline queue management
  private async addToOfflineQueue(request: any): Promise<void> {
    try {
      const queue = await this.getCachedData<any[]>(CACHE_KEYS.OFFLINE_QUEUE) || [];
      queue.push({
        ...request,
        timestamp: Date.now(),
      });
      await this.setCachedData(CACHE_KEYS.OFFLINE_QUEUE, queue);
    } catch (error) {
      console.error('Failed to add to offline queue:', error);
    }
  }

  public async processOfflineQueue(): Promise<void> {
    const online = await this.isOnline();
    if (!online) return;

    try {
      const queue = await this.getCachedData<any[]>(CACHE_KEYS.OFFLINE_QUEUE) || [];
      const processedItems: any[] = [];

      for (const item of queue) {
        try {
          // Process queued request based on type
          switch (item.type) {
            case 'transcribe':
              await this.transcribeAudio(item.file, item.config);
              break;
            case 'detect_language':
              await this.detectLanguage(item.file);
              break;
            // Add more cases as needed
          }
          processedItems.push(item);
        } catch (error) {
          console.error('Failed to process offline queue item:', error);
          // Keep failed items in queue for retry
        }
      }

      // Remove processed items from queue
      const remainingQueue = queue.filter(item => !processedItems.includes(item));
      await this.setCachedData(CACHE_KEYS.OFFLINE_QUEUE, remainingQueue);
    } catch (error) {
      console.error('Failed to process offline queue:', error);
    }
  }

  // API Methods

  /**
   * Transcribe audio file
   */
  public async transcribeAudio(
    file: {
      uri: string;
      name: string;
      type: string;
    },
    config: WhisperConfig,
    customVocabulary?: any,
    promptConfig?: any,
    onProgress?: (progress: number) => void
  ): Promise<TranscriptionResult> {
    const online = await this.isOnline();
    
    if (!online) {
      // Add to offline queue
      await this.addToOfflineQueue({
        type: 'transcribe',
        file,
        config,
        customVocabulary,
        promptConfig,
      });
      throw new Error('No internet connection. Request queued for when online.');
    }

    const formData = new FormData();
    formData.append('audio_file', {
      uri: file.uri,
      type: file.type,
      name: file.name,
    } as any);
    formData.append('config', JSON.stringify(config));
    
    if (customVocabulary) {
      formData.append('custom_vocabulary', JSON.stringify(customVocabulary));
    }
    
    if (promptConfig) {
      formData.append('prompt_config', JSON.stringify(promptConfig));
    }

    try {
      const response = await this.makeFileRequest<TranscriptionResult>(
        '/whisper-advanced/transcribe',
        formData,
        onProgress
      );

      // Cache successful result
      await this.setCachedData(
        `${CACHE_KEYS.TRANSCRIPTION_CACHE}_${Date.now()}`,
        response.data
      );

      return response.data;
    } catch (error) {
      console.error('Transcription failed:', error);
      throw error;
    }
  }

  /**
   * Detect language from audio file
   */
  public async detectLanguage(
    file: {
      uri: string;
      name: string;
      type: string;
    },
    onProgress?: (progress: number) => void
  ): Promise<LanguageDetectionResult> {
    const online = await this.isOnline();
    
    if (!online) {
      // Check cache first
      const cached = await this.getCachedData<LanguageDetectionResult>(
        `${CACHE_KEYS.LANGUAGE_CACHE}_${file.name}`
      );
      if (cached) {
        return cached;
      }

      // Add to offline queue
      await this.addToOfflineQueue({
        type: 'detect_language',
        file,
      });
      throw new Error('No internet connection. Request queued for when online.');
    }

    const formData = new FormData();
    formData.append('audio_file', {
      uri: file.uri,
      type: file.type,
      name: file.name,
    } as any);

    try {
      const response = await this.makeFileRequest<LanguageDetectionResult>(
        '/whisper-advanced/detect-language',
        formData,
        onProgress
      );

      // Cache successful result
      await this.setCachedData(
        `${CACHE_KEYS.LANGUAGE_CACHE}_${file.name}`,
        response.data
      );

      return response.data;
    } catch (error) {
      console.error('Language detection failed:', error);
      throw error;
    }
  }

  /**
   * Batch transcribe multiple files
   */
  public async batchTranscribe(
    files: Array<{
      uri: string;
      name: string;
      type: string;
    }>,
    config: WhisperConfig,
    onProgress?: (progress: number) => void
  ): Promise<BatchTranscriptionResult> {
    const online = await this.isOnline();
    
    if (!online) {
      throw new Error('Batch transcription requires internet connection');
    }

    if (files.length > 10) {
      throw new Error('Maximum 10 files allowed for batch processing');
    }

    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', {
        uri: file.uri,
        type: file.type,
        name: file.name,
      } as any);
    });
    formData.append('config', JSON.stringify(config));

    try {
      const response = await this.makeFileRequest<BatchTranscriptionResult>(
        '/whisper-advanced/batch-transcribe',
        formData,
        onProgress
      );

      return response.data;
    } catch (error) {
      console.error('Batch transcription failed:', error);
      throw error;
    }
  }

  /**
   * Get available models
   */
  public async getModels(): Promise<any> {
    try {
      const response = await this.makeRequest<any>('/whisper-advanced/models');
      return response.data;
    } catch (error) {
      console.error('Failed to get models:', error);
      throw error;
    }
  }

  /**
   * Get transcription presets
   */
  public async getPresets(): Promise<any> {
    try {
      const response = await this.makeRequest<any>('/whisper-advanced/presets');
      return response.data;
    } catch (error) {
      console.error('Failed to get presets:', error);
      throw error;
    }
  }

  /**
   * Health check
   */
  public async healthCheck(): Promise<any> {
    try {
      const response = await this.makeRequest<any>('/whisper-advanced/health');
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }

  // Utility methods

  /**
   * Clear all cached data
   */
  public async clearCache(): Promise<void> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const whisperKeys = keys.filter(key => 
        key.startsWith('whisper_') || 
        Object.values(CACHE_KEYS).includes(key)
      );
      await AsyncStorage.multiRemove(whisperKeys);
    } catch (error) {
      console.error('Failed to clear cache:', error);
    }
  }

  /**
   * Get cache size
   */
  public async getCacheSize(): Promise<number> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const whisperKeys = keys.filter(key => 
        key.startsWith('whisper_') || 
        Object.values(CACHE_KEYS).includes(key)
      );
      
      let totalSize = 0;
      for (const key of whisperKeys) {
        const value = await AsyncStorage.getItem(key);
        if (value) {
          totalSize += value.length;
        }
      }
      
      return totalSize;
    } catch (error) {
      console.error('Failed to calculate cache size:', error);
      return 0;
    }
  }

  /**
   * Get cached transcriptions
   */
  public async getCachedTranscriptions(): Promise<TranscriptionResult[]> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const transcriptionKeys = keys.filter(key => 
        key.startsWith(CACHE_KEYS.TRANSCRIPTION_CACHE)
      );
      
      const transcriptions: TranscriptionResult[] = [];
      for (const key of transcriptionKeys) {
        const cached = await this.getCachedData<TranscriptionResult>(key);
        if (cached) {
          transcriptions.push(cached);
        }
      }
      
      return transcriptions.sort((a, b) => b.processing_time - a.processing_time);
    } catch (error) {
      console.error('Failed to get cached transcriptions:', error);
      return [];
    }
  }

  /**
   * Export transcription result
   */
  public async exportTranscription(
    result: TranscriptionResult,
    format: 'txt' | 'json' | 'srt' | 'vtt' = 'txt'
  ): Promise<string> {
    switch (format) {
      case 'txt':
        return result.text;
      
      case 'json':
        return JSON.stringify(result, null, 2);
      
      case 'srt':
        return this.convertToSRT(result);
      
      case 'vtt':
        return this.convertToVTT(result);
      
      default:
        return result.text;
    }
  }

  private convertToSRT(result: TranscriptionResult): string {
    if (!result.segments || result.segments.length === 0) {
      return result.text;
    }

    return result.segments
      .map((segment, index) => {
        const startTime = this.formatSRTTime(segment.start);
        const endTime = this.formatSRTTime(segment.end);
        return `${index + 1}\n${startTime} --> ${endTime}\n${segment.text}\n`;
      })
      .join('\n');
  }

  private convertToVTT(result: TranscriptionResult): string {
    if (!result.segments || result.segments.length === 0) {
      return `WEBVTT\n\n${result.text}`;
    }

    const vttContent = result.segments
      .map(segment => {
        const startTime = this.formatVTTTime(segment.start);
        const endTime = this.formatVTTTime(segment.end);
        return `${startTime} --> ${endTime}\n${segment.text}`;
      })
      .join('\n\n');

    return `WEBVTT\n\n${vttContent}`;
  }

  private formatSRTTime(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 1000);
    
    return `${hours.toString().padStart(2, '0')}:${minutes
      .toString()
      .padStart(2, '0')}:${secs.toString().padStart(2, '0')},${ms
      .toString()
      .padStart(3, '0')}`;
  }

  private formatVTTTime(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 1000);
    
    return `${hours.toString().padStart(2, '0')}:${minutes
      .toString()
      .padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms
      .toString()
      .padStart(3, '0')}`;
  }
}

// Create singleton instance
export const whisperAPI = new WhisperAdvancedAPI();

// Export default
export default whisperAPI;