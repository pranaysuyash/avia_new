/**
 * API client for Real-Time Transcription endpoints
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

export interface StreamingModeOption {
  value: string;
  label: string;
  description: string;
}

export interface ApiResponse<T> {
  data: T;
  message: string;
  success: boolean;
}

export interface WebSocketMessage {
  type: 'connected' | 'transcription' | 'stats' | 'error' | 'recording_started' | 'recording_stopped';
  data?: any;
  message?: string;
  session_id?: string;
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
    streaming_modes: StreamingModeOption[];
  }> {
    const response = await this.request<{
      engines: EngineOption[];
      streaming_modes: StreamingModeOption[];
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

  /**
   * Create WebSocket connection for real-time transcription
   */
  createWebSocketConnection(sessionId: string): WebSocket {
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}${this.baseUrl}/ws/${sessionId}`;
    return new WebSocket(wsUrl);
  }
}

// WebSocket message handlers
export class WebSocketManager {
  private ws: WebSocket | null = null;
  private sessionId: string | null = null;
  private messageHandlers: Map<string, (data: any) => void> = new Map();
  private isConnected = false;

  constructor(private api: RealTimeTranscriptionAPI) {}

  async connect(sessionId: string): Promise<void> {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.disconnect();
    }

    this.sessionId = sessionId;
    this.ws = this.api.createWebSocketConnection(sessionId);

    return new Promise((resolve, reject) => {
      if (!this.ws) {
        reject(new Error('Failed to create WebSocket'));
        return;
      }

      this.ws.onopen = () => {
        this.isConnected = true;
        console.log('WebSocket connected');
        resolve();
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        console.log('WebSocket disconnected');
        this.messageHandlers.get('disconnect')?.(null);
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.messageHandlers.get('error')?.(error);
        reject(error);
      };
    });
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
    this.sessionId = null;
  }

  private handleMessage(message: WebSocketMessage): void {
    const handler = this.messageHandlers.get(message.type);
    if (handler) {
      handler(message.data || message);
    }
  }

  onMessage(type: string, handler: (data: any) => void): void {
    this.messageHandlers.set(type, handler);
  }

  sendMessage(message: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }

  sendAudioData(audioData: string): void {
    this.sendMessage({
      type: 'audio_data',
      data: audioData
    });
  }

  startRecording(): void {
    this.sendMessage({
      type: 'start_recording'
    });
  }

  stopRecording(): void {
    this.sendMessage({
      type: 'stop_recording'
    });
  }

  requestStats(): void {
    this.sendMessage({
      type: 'get_stats'
    });
  }

  getConnectionStatus(): boolean {
    return this.isConnected;
  }

  getSessionId(): string | null {
    return this.sessionId;
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
   * Merge consecutive segments from the same speaker
   */
  mergeConsecutiveSegments(segments: TranscriptionSegment[]): TranscriptionSegment[] {
    if (segments.length === 0) return segments;

    const merged: TranscriptionSegment[] = [];
    let current = { ...segments[0] };

    for (let i = 1; i < segments.length; i++) {
      const segment = segments[i];
      
      // Merge if same speaker and close in time (within 2 seconds)
      if (
        segment.speaker_id === current.speaker_id &&
        segment.start_time - current.end_time <= 2.0
      ) {
        current.text += ' ' + segment.text;
        current.end_time = segment.end_time;
        current.confidence = (current.confidence + segment.confidence) / 2;
      } else {
        merged.push(current);
        current = { ...segment };
      }
    }
    
    merged.push(current);
    return merged;
  },

  /**
   * Export segments to various formats
   */
  exportSegments(segments: TranscriptionSegment[], format: 'txt' | 'srt' | 'vtt' | 'json'): string {
    switch (format) {
      case 'txt':
        return segments.map(s => s.text).join(' ');
      
      case 'srt':
        return segments.map((segment, index) => {
          const startTime = this.formatSRTTime(segment.start_time);
          const endTime = this.formatSRTTime(segment.end_time);
          return `${index + 1}\n${startTime} --> ${endTime}\n${segment.text}\n`;
        }).join('\n');
      
      case 'vtt':
        let vtt = 'WEBVTT\n\n';
        vtt += segments.map(segment => {
          const startTime = this.formatVTTTime(segment.start_time);
          const endTime = this.formatVTTTime(segment.end_time);
          return `${startTime} --> ${endTime}\n${segment.text}\n`;
        }).join('\n');
        return vtt;
      
      case 'json':
        return JSON.stringify(segments, null, 2);
      
      default:
        return segments.map(s => s.text).join(' ');
    }
  },

  /**
   * Format time for SRT format (HH:MM:SS,mmm)
   */
  formatSRTTime(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    const milliseconds = Math.floor((seconds % 1) * 1000);
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')},${milliseconds.toString().padStart(3, '0')}`;
  },

  /**
   * Format time for VTT format (HH:MM:SS.mmm)
   */
  formatVTTTime(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    const milliseconds = Math.floor((seconds % 1) * 1000);
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${milliseconds.toString().padStart(3, '0')}`;
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