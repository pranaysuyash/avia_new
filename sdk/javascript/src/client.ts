/**
 * Main client for the Transcription API JavaScript/TypeScript SDK
 */

import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import FormData from 'form-data';
import {
  Transcript,
  Team,
  User,
  TranscriptionOptions,
  ClientConfig,
  PaginationOptions,
  ListResponse,
  APIKey,
  UsageStats,
  WebhookEvent
} from './types';
import {
  TranscriptionAPIError,
  AuthenticationError,
  RateLimitError,
  ValidationError,
  NotFoundError,
  ServerError,
  TimeoutError,
  ConnectionError
} from './exceptions';
import { validateApiKey, isValidFileType } from './utils';

/**
 * Main client for interacting with the Transcription API
 * 
 * @example
 * ```typescript
 * const client = new TranscriptionClient({ apiKey: 'your_api_key' });
 * 
 * // Upload and transcribe a file
 * const file = new File([audioBlob], 'recording.mp3');
 * const transcript = await client.transcribeFile(file, { title: 'My Recording' });
 * 
 * // Wait for completion
 * const completed = await client.waitForCompletion(transcript.id);
 * console.log(completed.text);
 * ```
 */
export class TranscriptionClient {
  private client: AxiosInstance;
  private apiKey: string;
  private baseUrl: string;

  constructor(config: ClientConfig) {
    this.apiKey = config.apiKey || process.env.TRANSCRIPTION_API_KEY || '';
    
    if (!this.apiKey) {
      throw new AuthenticationError(
        'API key is required. Provide it in config or set TRANSCRIPTION_API_KEY environment variable.'
      );
    }

    if (!validateApiKey(this.apiKey)) {
      throw new AuthenticationError('Invalid API key format.');
    }

    this.baseUrl = config.baseUrl || 'https://api.transcriptionplatform.com/v1';

    // Create axios instance
    this.client = axios.create({
      baseURL: this.baseUrl,
      timeout: config.timeout || 30000,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'User-Agent': `transcription-api-js/1.0.0`,
        'Accept': 'application/json'
      }
    });

    // Setup request/response interceptors
    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add timestamp to prevent caching
        if (config.params) {
          config.params._t = Date.now();
        } else {
          config.params = { _t: Date.now() };
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error: AxiosError) => {
        return Promise.reject(this.handleError(error));
      }
    );
  }

  private handleError(error: AxiosError): TranscriptionAPIError {
    if (error.code === 'ECONNABORTED') {
      return new TimeoutError('Request timed out');
    }

    if (error.code === 'ECONNREFUSED' || error.code === 'ENOTFOUND') {
      return new ConnectionError('Connection failed');
    }

    if (!error.response) {
      return new TranscriptionAPIError('Network error occurred');
    }

    const { status, data } = error.response;
    const message = (data as any)?.detail || error.message;

    switch (status) {
      case 401:
        return new AuthenticationError('Invalid API key or authentication failed');
      case 400:
        return new ValidationError(message);
      case 404:
        return new NotFoundError('Resource not found');
      case 429:
        const retryAfter = error.response.headers['retry-after'];
        return new RateLimitError(
          `Rate limit exceeded. Retry after ${retryAfter || 60} seconds.`,
          retryAfter ? parseInt(retryAfter) : undefined
        );
      case 500:
      case 502:
      case 503:
      case 504:
        return new ServerError(`Server error: ${status}`);
      default:
        return new TranscriptionAPIError(`HTTP ${status}: ${message}`);
    }
  }

  // Transcription methods

  /**
   * Upload and transcribe an audio/video file
   */
  async transcribeFile(
    file: File | Blob,
    options: {
      title?: string;
      transcriptionOptions?: TranscriptionOptions;
    } = {}
  ): Promise<Transcript> {
    const { title, transcriptionOptions = {} } = options;

    // Validate file type
    if (file instanceof File && !isValidFileType(file.type)) {
      throw new ValidationError(`Unsupported file type: ${file.type}`);
    }

    // Create form data
    const formData = new FormData();
    formData.append('file', file, title || 'audio_file');
    formData.append('title', title || 'Untitled');
    formData.append('language', transcriptionOptions.language || 'auto');
    formData.append('method', transcriptionOptions.method || 'basic');
    
    if (transcriptionOptions.teamId) {
      formData.append('team_id', transcriptionOptions.teamId.toString());
    }

    const response = await this.client.post('/transcriptions/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });

    return response.data;
  }

  /**
   * Get a transcript by ID
   */
  async getTranscript(transcriptId: string): Promise<Transcript> {
    const response = await this.client.get(`/transcriptions/${transcriptId}`);
    return response.data;
  }

  /**
   * List user's transcripts
   */
  async listTranscripts(options: PaginationOptions & {
    teamId?: number;
  } = {}): Promise<ListResponse<Transcript>> {
    const params: any = {
      skip: options.skip || 0,
      limit: options.limit || 20
    };

    if (options.teamId) {
      params.team_id = options.teamId;
    }

    const response = await this.client.get('/transcriptions', { params });
    
    return {
      items: response.data,
      total: response.headers['x-total-count'] ? parseInt(response.headers['x-total-count']) : response.data.length,
      skip: params.skip,
      limit: params.limit
    };
  }

  /**
   * Delete a transcript
   */
  async deleteTranscript(transcriptId: string): Promise<void> {
    await this.client.delete(`/transcriptions/${transcriptId}`);
  }

  /**
   * Wait for a transcript to complete processing
   */
  async waitForCompletion(
    transcriptId: string,
    options: {
      timeout?: number;
      pollInterval?: number;
    } = {}
  ): Promise<Transcript> {
    const { timeout = 300000, pollInterval = 5000 } = options; // 5 minutes default timeout
    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
      const transcript = await this.getTranscript(transcriptId);

      if (transcript.status === 'completed') {
        return transcript;
      } else if (transcript.status === 'failed') {
        throw new TranscriptionAPIError('Transcription failed');
      }

      // Wait before next poll
      await new Promise(resolve => setTimeout(resolve, pollInterval));
    }

    throw new TimeoutError('Transcription timed out');
  }

  // Team methods

  /**
   * Create a new team
   */
  async createTeam(name: string, description?: string): Promise<Team> {
    const data: any = { name };
    if (description) {
      data.description = description;
    }

    const response = await this.client.post('/teams', data);
    return response.data;
  }

  /**
   * List user's teams
   */
  async listTeams(): Promise<Team[]> {
    const response = await this.client.get('/teams');
    return response.data;
  }

  /**
   * Get team details
   */
  async getTeam(teamId: number): Promise<Team> {
    const response = await this.client.get(`/teams/${teamId}`);
    return response.data;
  }

  /**
   * Invite a member to a team
   */
  async inviteTeamMember(
    teamId: number,
    email: string,
    role: string = 'member'
  ): Promise<{ message: string; user_id: number; email: string; role: string }> {
    const response = await this.client.post(`/teams/${teamId}/members`, {
      email,
      role
    });
    return response.data;
  }

  /**
   * Remove a member from a team
   */
  async removeTeamMember(teamId: number, userId: number): Promise<void> {
    await this.client.delete(`/teams/${teamId}/members/${userId}`);
  }

  // User methods

  /**
   * Get current user profile
   */
  async getProfile(): Promise<User> {
    const response = await this.client.get('/users/profile');
    return response.data;
  }

  /**
   * Update user profile
   */
  async updateProfile(name?: string): Promise<User> {
    const data: any = {};
    if (name) {
      data.name = name;
    }

    const response = await this.client.put('/users/profile', data);
    return response.data;
  }

  // API Key methods

  /**
   * Create a new API key
   */
  async createApiKey(
    name: string,
    expiresInDays?: number
  ): Promise<APIKey & { key: string }> {
    const data: any = { name };
    if (expiresInDays) {
      data.expires_in_days = expiresInDays;
    }

    const response = await this.client.post('/users/api-keys', data);
    return response.data;
  }

  /**
   * List user's API keys
   */
  async listApiKeys(): Promise<APIKey[]> {
    const response = await this.client.get('/users/api-keys');
    return response.data;
  }

  /**
   * Delete an API key
   */
  async deleteApiKey(keyId: number): Promise<void> {
    await this.client.delete(`/users/api-keys/${keyId}`);
  }

  // Utility methods

  /**
   * Check API health
   */
  async healthCheck(): Promise<{
    status: string;
    timestamp: string;
    version: string;
    environment: string;
  }> {
    const response = await this.client.get('/health');
    return response.data;
  }

  /**
   * Get usage statistics
   */
  async getUsageStats(): Promise<UsageStats> {
    const response = await this.client.get('/usage');
    return response.data;
  }

  /**
   * Search transcripts
   */
  async searchTranscripts(
    query: string,
    options: PaginationOptions = {}
  ): Promise<ListResponse<Transcript>> {
    const params = {
      q: query,
      skip: options.skip || 0,
      limit: options.limit || 20
    };

    const response = await this.client.get('/search/transcripts', { params });
    
    return {
      items: response.data.results || response.data,
      total: response.data.total || response.data.length,
      skip: params.skip,
      limit: params.limit
    };
  }

  /**
   * Get presigned upload URL for direct file upload
   */
  async getPresignedUploadUrl(
    filename: string,
    contentType?: string
  ): Promise<{
    uploadUrl: string;
    objectKey: string;
    expiresIn: number;
  }> {
    const params: any = { filename };
    if (contentType) {
      params.content_type = contentType;
    }

    const response = await this.client.get('/storage/presigned-upload', { params });
    return response.data;
  }

  /**
   * Get download URL for a transcription file
   */
  async getDownloadUrl(transcriptionId: string): Promise<{
    downloadUrl: string;
    filename: string;
    expiresIn: number;
  }> {
    const response = await this.client.get(`/storage/download/${transcriptionId}`);
    return response.data;
  }
}