/**
 * Mobile API client for Real-Time Transcription endpoints
 */

export interface StreamingConfig {
  engine: string;
  language: string;
  sample_rate: number;
  chunk_duration: number;
  buffer_duration: number;
  overlap_duration: number;
  confidence_threshold: number;
  enable_vad: boolean;
  enable_speaker_diarization: boolean;
  streaming_mode: string;
}

export interface SessionCreateRequest {
  config: StreamingConfig;
  session_name?: string;
}

export interface TranscriptionSegment {
  text: string;
  start_time: number;
  end_time: number;
  confidence: number;
  is_final: boolean;
  speaker_id?: string;
  language?: string;
  engine?: string;
}

export interface StreamingStats {
  total_audio_duration: number;
  total_processing_time: number;
  segments_processed: number;
  average_latency: number;
  confidence_scores: number[];
  error_count: number;
}

export interface SessionResponse {
  session_id: string;
  status: string;
  config: StreamingConfig;
  created_at: string;
  stats?: StreamingStats;
}

export interface EngineOption {
  value: string;
  label: string;
  description: string;
  supports_streaming: boolean;
  languages: string[];
}

export interface ApiResponse<T> {
  data: T;
  message: string;
  success: boolean;
}

class RealTimeTranscriptionAPI {
  private baseUrl = '/api/v1/realtime-transcription';

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const defaultHeaders = {
      'Content-Type': 'application/json',
    };

    const config: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${url}`, error);
      throw error;
    }
  }

  /**
   * Create a new streaming session
   */
  async createSession(request: SessionCreateRequest): Promise<SessionResponse> {
    const response = await this.request<SessionResponse>('/sessions', {
      method: 'POST',
      body: JSON.stringify(request),
    });
    return response.data;
  }

  /**
   * Get session details
   */
  async getSession(sessionId: string): Promise<SessionResponse> {
    const response = await this.request<SessionResponse>(`/sessions/${sessionId}`);
    return response.data;
  }

  /**
   * Delete a session
   */
  async deleteSession(sessionId: string): Promise<{ session_id: string }> {
    const response = await this.request<{ session_id: string }>(`/sessions/${sessionId}`, {
      method: 'DELETE',
    });
    return response.data;
  }

  /**
   * List user's sessions
   */
  async listSessions(): Promise<{ sessions: SessionResponse[]; total: number }> {
    const response = await this.request<{ sessions: SessionResponse[]; total: number }>('/sessions');
    return response.data;
  }

  /**
   * Get available engines and streaming modes
   */
  async getEngines(): Promise<{
    engines: EngineOption[];
    streaming_modes: any[];
  }> {
    const response = await this.request<{
      engines: EngineOption[];
      streaming_modes: any[];
    }>('/engines');
    return response.data;
  }

  /**
   * Health check for the real-time transcription service
   */
  async healthCheck(): Promise<{
    status: string;
    components: Record<string, string>;
    active_sessions: number;
    active_connections: number;
    supported_engines: number;
  }> {
    const response = await this.request<{
      status: string;
      components: Record<string, string>;
      active_sessions: number;
      active_connections: number;
      supported_engines: number;
    }>('/health');
    return response.data;
  }
}

// Export singleton instance
export const realTimeTranscriptionAPI = new RealTimeTranscriptionAPI();

// Export utility functions
export const transcriptionUtils = {
  /**
   * Format duration in seconds to human readable format
   */
  formatDuration(seconds: number): string {
    if (seconds < 60) {
      return `${seconds.toFixed(1)}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  },

  /**
   * Calculate words per minute from segments
   */
  calculateWPM(segments: TranscriptionSegment[]): number {
    if (segments.length === 0) return 0;
    
    const totalWords = segments.reduce((sum, segment) => {
      return sum + segment.text.split(/\s+/).filter(w => w.length > 0).length;
    }, 0);
    
    const totalDuration = segments.reduce((max, segment) => {
      return Math.max(max, segment.end_time);
    }, 0);
    
    if (totalDuration === 0) return 0;
    return Math.round((totalWords / totalDuration) * 60);
  },

  /**
   * Get confidence level description
   */
  getConfidenceDescription(confidence: number): string {
    if (confidence >= 0.9) return 'Excellent';
    if (confidence >= 0.8) return 'Very Good';
    if (confidence >= 0.7) return 'Good';
    if (confidence >= 0.6) return 'Fair';
    return 'Poor';
  },

  /**
   * Validate streaming configuration
   */
  validateConfig(config: StreamingConfig): string[] {
    const errors: string[] = [];

    if (config.sample_rate < 8000 || config.sample_rate > 48000) {
      errors.push('Sample rate must be between 8000 and 48000 Hz');
    }

    if (config.chunk_duration < 0.1 || config.chunk_duration > 5.0) {
      errors.push('Chunk duration must be between 0.1 and 5.0 seconds');
    }

    if (config.buffer_duration < 1.0 || config.buffer_duration > 30.0) {
      errors.push('Buffer duration must be between 1.0 and 30.0 seconds');
    }

    if (config.overlap_duration < 0.0 || config.overlap_duration > 2.0) {
      errors.push('Overlap duration must be between 0.0 and 2.0 seconds');
    }

    if (config.confidence_threshold < 0.0 || config.confidence_threshold > 1.0) {
      errors.push('Confidence threshold must be between 0.0 and 1.0');
    }

    return errors;
  }
};

export default realTimeTranscriptionAPI;