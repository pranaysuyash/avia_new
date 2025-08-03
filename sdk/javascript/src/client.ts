/**
 * Transcription Platform Client
 * Main client class for interacting with the API
 */

import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';
import FormData from 'form-data';
import {
  TranscriptionError,
  AuthenticationError,
  RateLimitError,
  ValidationError,
  NotFoundError,
  ServerError,
} from './exceptions';
import {
  Transcript,
  Team,
  Usage,
  Webhook,
  TranscriptCreateOptions,
  TranscriptListOptions,
  TranscriptExportOptions,
  TranscriptExportFormat,
  WebhookCreateOptions,
  PaginatedResponse,
  ClientOptions,
} from './types';

export class TranscriptionClient {
  private client: AxiosInstance;
  private apiKey: string;

  constructor(apiKey: string, options: ClientOptions = {}) {
    if (!apiKey) {
      throw new Error('API key is required');
    }

    this.apiKey = apiKey;

    // Create axios instance with defaults
    this.client = axios.create({
      baseURL: options.baseURL || 'https://api.example.com/v1',
      timeout: options.timeout || 30000,
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'User-Agent': `transcription-platform-js/1.0.0`,
        'Content-Type': 'application/json',
      },
    });

    // Add retry interceptor
    this.setupRetryInterceptor(options.maxRetries || 3);

    // Add error interceptor
    this.setupErrorInterceptor();
  }

  private setupRetryInterceptor(maxRetries: number): void {
    let retryCount = 0;

    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const config = error.config;

        // Only retry on specific status codes
        if (!config || retryCount >= maxRetries) {
          return Promise.reject(error);
        }

        const shouldRetry = 
          error.response?.status === 429 || // Rate limit
          error.response?.status >= 500 || // Server errors
          error.code === 'ECONNABORTED' || // Timeout
          error.code === 'ENOTFOUND'; // DNS issues

        if (!shouldRetry) {
          return Promise.reject(error);
        }

        retryCount++;

        // Calculate delay
        let delay = 1000 * Math.pow(2, retryCount); // Exponential backoff

        // Use Retry-After header if available
        if (error.response?.status === 429) {
          const retryAfter = error.response.headers['retry-after'];
          if (retryAfter) {
            delay = parseInt(retryAfter) * 1000;
          }
        }

        await new Promise(resolve => setTimeout(resolve, delay));

        return this.client(config);
      }
    );
  }

  private setupErrorInterceptor(): void {
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (!error.response) {
          throw new TranscriptionError('Network error occurred');
        }

        const status = error.response.status;
        const data = error.response.data as any;
        const message = data?.message || error.message;

        switch (status) {
          case 401:
            throw new AuthenticationError(message);
          case 404:
            throw new NotFoundError(message);
          case 400:
          case 422:
            throw new ValidationError(message);
          case 429:
            const retryAfter = parseInt(error.response.headers['retry-after'] || '60');
            const resetTime = parseInt(error.response.headers['x-ratelimit-reset'] || '0');
            throw new RateLimitError(message, retryAfter, resetTime);
          default:
            if (status >= 500) {
              throw new ServerError(message);
            }
            throw new TranscriptionError(message);
        }
      }
    );
  }

  // Transcript methods

  async createTranscript(options: TranscriptCreateOptions): Promise<Transcript> {
    if ('audioFile' in options && options.audioFile) {
      // File upload
      const formData = new FormData();
      formData.append('file', options.audioFile);
      formData.append('language', options.language || 'en');
      formData.append('enable_diarization', String(options.enableDiarization || false));
      
      if (options.maxSpeakers) {
        formData.append('max_speakers', String(options.maxSpeakers));
      }
      if (options.webhookUrl) {
        formData.append('webhook_url', options.webhookUrl);
      }
      if (options.metadata) {
        formData.append('metadata', JSON.stringify(options.metadata));
      }

      const response = await this.client.post<Transcript>('/transcripts/upload', formData, {
        headers: {
          ...formData.getHeaders(),
        },
      });

      return response.data;
    } else if ('audioUrl' in options && options.audioUrl) {
      // URL submission
      const response = await this.client.post<Transcript>('/transcripts', {
        audio_url: options.audioUrl,
        language: options.language || 'en',
        enable_diarization: options.enableDiarization || false,
        max_speakers: options.maxSpeakers,
        webhook_url: options.webhookUrl,
        metadata: options.metadata,
      });

      return response.data;
    } else {
      throw new ValidationError('Either audioUrl or audioFile must be provided');
    }
  }

  async getTranscript(transcriptId: string): Promise<Transcript> {
    const response = await this.client.get<Transcript>(`/transcripts/${transcriptId}`);
    return response.data;
  }

  async listTranscripts(options: TranscriptListOptions = {}): Promise<PaginatedResponse<Transcript>> {
    const params: any = {
      page: options.page || 1,
      per_page: Math.min(options.perPage || 20, 100),
    };

    if (options.status) params.status = options.status;
    if (options.language) params.language = options.language;
    if (options.teamId) params.team_id = options.teamId;

    const response = await this.client.get<PaginatedResponse<Transcript>>('/transcripts', { params });
    return response.data;
  }

  async updateTranscript(
    transcriptId: string,
    updates: { title?: string; metadata?: Record<string, any> }
  ): Promise<Transcript> {
    const response = await this.client.put<Transcript>(`/transcripts/${transcriptId}`, updates);
    return response.data;
  }

  async deleteTranscript(transcriptId: string): Promise<{ message: string }> {
    const response = await this.client.delete<{ message: string }>(`/transcripts/${transcriptId}`);
    return response.data;
  }

  async exportTranscript(
    transcriptId: string,
    options: TranscriptExportOptions = {}
  ): Promise<string | Record<string, any>> {
    const params: any = {
      format: options.format || 'txt',
      include_timestamps: options.includeTimestamps || false,
      include_speakers: options.includeSpeakers !== false,
    };

    const response = await this.client.get(`/transcripts/${transcriptId}/export`, { params });

    if (options.format === 'json') {
      return response.data;
    } else {
      return response.data.content || '';
    }
  }

  // Team methods

  async listTeams(): Promise<Team[]> {
    const response = await this.client.get<{ data: Team[] }>('/teams');
    return response.data.data;
  }

  async getTeam(teamId: number): Promise<Team> {
    const response = await this.client.get<Team>(`/teams/${teamId}`);
    return response.data;
  }

  async createTeam(name: string, description?: string): Promise<Team> {
    const response = await this.client.post<Team>('/teams', { name, description });
    return response.data;
  }

  // Analytics methods

  async getUsage(options: {
    startDate?: string;
    endDate?: string;
    usageType?: string;
  } = {}): Promise<Usage> {
    const params: any = {};
    if (options.startDate) params.start_date = options.startDate;
    if (options.endDate) params.end_date = options.endDate;
    if (options.usageType) params.usage_type = options.usageType;

    const response = await this.client.get<Usage>('/analytics/usage', { params });
    return response.data;
  }

  // Webhook methods

  async listWebhooks(): Promise<Webhook[]> {
    const response = await this.client.get<Webhook[]>('/developers/webhooks');
    return response.data;
  }

  async createWebhook(options: WebhookCreateOptions): Promise<Webhook> {
    const response = await this.client.post<Webhook>('/developers/webhooks', {
      name: options.name,
      url: options.url,
      events: options.events,
      secret: options.secret,
    });
    return response.data;
  }

  async deleteWebhook(webhookId: number): Promise<{ message: string }> {
    const response = await this.client.delete<{ message: string }>(`/developers/webhooks/${webhookId}`);
    return response.data;
  }

  // Utility methods

  async getSupportedLanguages(): Promise<Array<{ code: string; name: string }>> {
    const response = await this.client.get<{ languages: Array<{ code: string; name: string }> }>('/languages');
    return response.data.languages;
  }

  /**
   * Wait for a transcript to complete
   * @param transcriptId Transcript ID
   * @param options Polling options
   * @returns Completed transcript
   */
  async waitForCompletion(
    transcriptId: string,
    options: {
      pollInterval?: number;
      maxAttempts?: number;
      onProgress?: (transcript: Transcript) => void;
    } = {}
  ): Promise<Transcript> {
    const pollInterval = options.pollInterval || 5000;
    const maxAttempts = options.maxAttempts || 360; // 30 minutes with 5s interval
    let attempts = 0;

    while (attempts < maxAttempts) {
      const transcript = await this.getTranscript(transcriptId);

      if (options.onProgress) {
        options.onProgress(transcript);
      }

      if (transcript.status === 'completed' || transcript.status === 'failed') {
        return transcript;
      }

      attempts++;
      await new Promise(resolve => setTimeout(resolve, pollInterval));
    }

    throw new TranscriptionError('Transcript processing timed out');
  }
}