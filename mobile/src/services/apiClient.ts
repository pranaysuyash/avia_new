/**
 * API Client for React Native Mobile App
 * Connects to FastAPI backend with all enterprise features
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

// API Configuration
const API_BASE_URL = Platform.select({
  ios: 'http://localhost:8000',
  android: 'http://10.0.2.2:8000', // Android emulator localhost
  default: 'http://localhost:8000'
});

// Types
export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserInfo;
}

export interface UserInfo {
  id: string;
  email: string;
  name: string;
  role: string;
  organization_id?: string;
}

// Enterprise Types
export interface Lead {
  id: string;
  company_name: string;
  contact_name?: string;
  contact_email?: string;
  status: string;
  score: number;
  priority: string;
  created_at: string;
}

export interface SupportTicket {
  id: string;
  ticket_number: string;
  subject: string;
  description: string;
  status: string;
  priority: string;
  created_at: string;
}

export interface Campaign {
  id: string;
  name: string;
  type: string;
  status: string;
  budget: number;
  spent: number;
  metrics: {
    impressions: number;
    clicks: number;
    conversions: number;
    roi: number;
  };
}

// Usage and Subscription Types
export interface UsageInfo {
  current: number;
  limit: number | string;
  remaining: number | string;
  percentage_used: number;
}

export interface PlanInfo {
  name: string;
  tier: string;
  is_trial: boolean;
  expires_at?: string;
}

export interface UsageResponse {
  plan: PlanInfo;
  usage: {
    transcripts: UsageInfo;
    minutes: UsageInfo;
    storage: UsageInfo;
    api_calls: UsageInfo;
  };
  features: {
    api_access: boolean;
    advanced_analytics: boolean;
    custom_models: boolean;
    priority_support: boolean;
    white_label: boolean;
    sso: boolean;
    audit_logs: boolean;
    batch_processing: boolean;
    real_time_collab: boolean;
  };
  can_upgrade: boolean;
}

// Audio and TTS Types
export interface AudioEnhancementOptions {
  noise_reduction?: boolean;
  normalize?: boolean;
  remove_silence?: boolean;
  enhance_voice?: boolean;
  target_loudness?: number;
}

export interface TTSRequest {
  text: string;
  voice?: string;
  language?: string;
  speed?: number;
  pitch?: number;
  format?: string;
}

export interface Voice {
  id: string;
  name: string;
  language: string;
  gender?: string;
  description?: string;
  sample_url?: string;
}

class ApiClient {
  private authToken: string | null = null;

  constructor() {
    this.loadAuthToken();
  }

  private async loadAuthToken() {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (token) {
        this.authToken = token;
      }
    } catch (error) {
      console.error('Failed to load auth token:', error);
    }
  }

  private async saveAuthToken(token: string) {
    try {
      await AsyncStorage.setItem('auth_token', token);
      this.authToken = token;
    } catch (error) {
      console.error('Failed to save auth token:', error);
    }
  }

  private async clearAuthToken() {
    try {
      await AsyncStorage.removeItem('auth_token');
      this.authToken = null;
    } catch (error) {
      console.error('Failed to clear auth token:', error);
    }
  }

  private async makeRequest<T>(
    method: string,
    endpoint: string,
    data?: any,
    params?: any
  ): Promise<T> {
    const url = new URL(`${API_BASE_URL}${endpoint}`);
    
    if (params) {
      Object.keys(params).forEach(key => {
        if (params[key] !== undefined && params[key] !== null) {
          url.searchParams.append(key, params[key]);
        }
      });
    }

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }

    try {
      const response = await fetch(url.toString(), {
        method,
        headers,
        body: data ? JSON.stringify(data) : undefined,
      });

      if (response.status === 401) {
        // Unauthorized - clear token
        await this.clearAuthToken();
        throw new Error('Unauthorized');
      }

      if (response.status === 402) {
        // Quota exceeded - Payment Required
        const errorData = await response.json().catch(() => ({}));
        const quotaError = new Error(errorData.detail || 'Usage quota exceeded');
        (quotaError as any).isQuotaError = true;
        (quotaError as any).usageInfo = response.headers.get('x-usage-info');
        throw quotaError;
      }

      if (response.status === 403) {
        // Feature access denied
        const errorData = await response.json().catch(() => ({}));
        const featureError = new Error(errorData.detail || 'Feature access denied');
        (featureError as any).isFeatureError = true;
        (featureError as any).requiredFeature = response.headers.get('x-required-feature');
        throw featureError;
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || errorData.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API Error (${method} ${endpoint}):`, error);
      throw error;
    }
  }

  // Auth Methods
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await this.makeRequest<AuthResponse>(
      'POST',
      '/api/v1/auth/login',
      credentials
    );
    
    if (response.access_token) {
      await this.saveAuthToken(response.access_token);
    }
    
    return response;
  }

  async logout(): Promise<void> {
    await this.clearAuthToken();
  }

  async getCurrentUser(): Promise<UserInfo> {
    return this.makeRequest<UserInfo>('GET', '/api/v1/auth/me');
  }

  async register(data: {
    email: string;
    password: string;
    name: string;
  }): Promise<AuthResponse> {
    const response = await this.makeRequest<AuthResponse>(
      'POST',
      '/api/v1/auth/register',
      data
    );
    
    if (response.access_token) {
      await this.saveAuthToken(response.access_token);
    }
    
    return response;
  }

  // Transcription Methods
  async getTranscriptions(filters?: {
    status?: string;
    date_from?: string;
    date_to?: string;
  }): Promise<any[]> {
    return this.makeRequest<any[]>('GET', '/api/v1/transcriptions', null, filters);
  }

  async createTranscription(formData: FormData): Promise<any> {
    const headers: HeadersInit = {};
    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/transcriptions`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
  }

  async getTranscription(id: string): Promise<any> {
    return this.makeRequest<any>('GET', `/api/v1/transcriptions/${id}`);
  }

  // Sales Methods
  async getLeads(filters?: { status?: string; priority?: string }): Promise<Lead[]> {
    return this.makeRequest<Lead[]>('GET', '/api/v1/sales/leads', null, filters);
  }

  async createLead(leadData: any): Promise<Lead> {
    return this.makeRequest<Lead>('POST', '/api/v1/sales/leads', leadData);
  }

  async updateLead(leadId: string, updates: any): Promise<Lead> {
    return this.makeRequest<Lead>('PUT', `/api/v1/sales/leads/${leadId}`, updates);
  }

  async getSalesPipeline(): Promise<any> {
    return this.makeRequest<any>('GET', '/api/v1/sales/metrics/pipeline');
  }

  // Support Methods
  async getTickets(filters?: { status?: string; priority?: string }): Promise<SupportTicket[]> {
    return this.makeRequest<SupportTicket[]>('GET', '/api/v1/support/tickets', null, filters);
  }

  async createTicket(ticketData: any): Promise<SupportTicket> {
    return this.makeRequest<SupportTicket>('POST', '/api/v1/support/tickets', ticketData);
  }

  async addTicketMessage(ticketId: string, message: any): Promise<any> {
    return this.makeRequest<any>(
      'POST',
      `/api/v1/support/tickets/${ticketId}/messages`,
      message
    );
  }

  async searchKnowledgeBase(query: string): Promise<any[]> {
    return this.makeRequest<any[]>('GET', '/api/v1/support/kb/search', null, { q: query });
  }

  // Marketing Methods
  async getCampaigns(filters?: { status?: string; type?: string }): Promise<Campaign[]> {
    return this.makeRequest<Campaign[]>('GET', '/api/v1/marketing/campaigns', null, filters);
  }

  async createCampaign(campaignData: any): Promise<Campaign> {
    return this.makeRequest<Campaign>('POST', '/api/v1/marketing/campaigns', campaignData);
  }

  async getReferralStats(): Promise<any> {
    return this.makeRequest<any>('GET', '/api/v1/marketing/referrals/stats');
  }

  async generateReferralCode(programId: string): Promise<any> {
    return this.makeRequest<any>('POST', '/api/v1/marketing/referrals/generate', {
      program_id: programId
    });
  }

  // Analytics Methods
  async getUsageStats(): Promise<any> {
    return this.makeRequest<any>('GET', '/api/v1/analytics/usage');
  }

  async getPerformanceMetrics(): Promise<any> {
    return this.makeRequest<any>('GET', '/api/v1/analytics/performance');
  }

  // Settings Methods
  async getSettings(): Promise<any> {
    return this.makeRequest<any>('GET', '/api/v1/settings');
  }

  async updateSettings(settings: any): Promise<any> {
    return this.makeRequest<any>('PUT', '/api/v1/settings', settings);
  }

  // Team Methods
  async getTeam(): Promise<any> {
    return this.makeRequest<any>('GET', '/api/v1/teams/current');
  }

  async inviteTeamMember(email: string, role: string): Promise<any> {
    return this.makeRequest<any>('POST', '/api/v1/teams/invite', { email, role });
  }

  // Export Methods
  async exportData(format: string, data: any): Promise<Blob> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/export/${format}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return response.blob();
  }

  // Usage and Subscription Methods
  async getUsageDashboard(): Promise<UsageResponse> {
    return this.makeRequest<UsageResponse>('GET', '/api/v1/usage/dashboard');
  }

  async getUsageAlerts(): Promise<any> {
    return this.makeRequest<any>('GET', '/api/v1/usage/alerts');
  }

  async getUsageHistory(usageType?: string, days = 30): Promise<any> {
    const params: any = { days };
    if (usageType) params.usage_type = usageType;
    return this.makeRequest<any>('GET', '/api/v1/usage/history', null, params);
  }

  // Audio Enhancement Methods
  async enhanceAudio(audioData: string, options: AudioEnhancementOptions): Promise<any> {
    return this.makeRequest<any>('POST', '/api/v1/audio/enhance', {
      audio_data: audioData,
      enhancement_options: options
    });
  }

  async getAudioPresets(): Promise<any> {
    return this.makeRequest<any>('GET', '/api/v1/audio/presets');
  }

  async analyzeAudioQuality(audioData: string): Promise<any> {
    return this.makeRequest<any>('POST', '/api/v1/audio/analyze/quality', { audio_data: audioData });
  }

  // TTS Methods
  async synthesizeSpeech(ttsRequest: TTSRequest): Promise<any> {
    return this.makeRequest<any>('POST', '/api/v1/tts/synthesize', ttsRequest);
  }

  async getVoices(language?: string): Promise<Voice[]> {
    const params = language ? { language } : {};
    return this.makeRequest<Voice[]>('GET', '/api/v1/tts/voices', null, params);
  }

  async getSupportedLanguages(): Promise<any> {
    return this.makeRequest<any>('GET', '/api/v1/tts/languages');
  }

  async searchVoices(query: string, language?: string, gender?: string): Promise<Voice[]> {
    const params: any = { query };
    if (language) params.language = language;
    if (gender) params.gender = gender;
    return this.makeRequest<Voice[]>('GET', '/api/v1/tts/voices/search', null, params);
  }

  // Collaboration Methods
  async createComment(commentData: {
    transcript_id: string;
    text: string;
    timestamp_start?: string;
    timestamp_end?: string;
    parent_id?: string;
  }): Promise<any> {
    return this.makeRequest<any>('POST', '/api/v1/collaboration/comments', commentData);
  }

  async getTranscriptComments(transcriptId: string): Promise<any[]> {
    return this.makeRequest<any[]>('GET', `/api/v1/collaboration/comments/${transcriptId}`);
  }

  async updateComment(commentId: string, updates: { text?: string; resolved?: boolean }): Promise<any> {
    return this.makeRequest<any>('PUT', `/api/v1/collaboration/comments/${commentId}`, updates);
  }

  async createAnnotation(annotationData: {
    transcript_id: string;
    type: string;
    text?: string;
    data?: any;
    timestamp_start?: string;
    timestamp_end?: string;
  }): Promise<any> {
    return this.makeRequest<any>('POST', '/api/v1/collaboration/annotations', annotationData);
  }

  async getTranscriptAnnotations(transcriptId: string, annotationType?: string): Promise<any[]> {
    const params = annotationType ? { annotation_type: annotationType } : {};
    return this.makeRequest<any[]>('GET', `/api/v1/collaboration/annotations/${transcriptId}`, null, params);
  }

  // AI Customization Methods
  async getModelConfigs(modelType?: string, includePublic = true): Promise<any[]> {
    const params: any = { include_public: includePublic };
    if (modelType) params.model_type = modelType;
    return this.makeRequest<any[]>('GET', '/api/v1/ai/models/config', null, params);
  }

  async createModelConfig(configData: {
    name: string;
    description?: string;
    model_type: string;
    base_model: string;
    parameters: any;
    is_public?: boolean;
  }): Promise<any> {
    return this.makeRequest<any>('POST', '/api/v1/ai/models/config', configData);
  }

  async getAvailableModels(): Promise<any> {
    return this.makeRequest<any>('GET', '/api/v1/ai/models/available');
  }

  async getModelPresets(): Promise<any> {
    return this.makeRequest<any>('GET', '/api/v1/ai/models/presets');
  }

  // WebSocket connection for real-time features
  connectWebSocket(endpoint: string): WebSocket {
    const wsUrl = API_BASE_URL.replace('http', 'ws');
    const ws = new WebSocket(`${wsUrl}${endpoint}`);
    
    if (this.authToken) {
      ws.addEventListener('open', () => {
        ws.send(JSON.stringify({ type: 'auth', token: this.authToken }));
      });
    }
    
    return ws;
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    return !!this.authToken;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export types
export type { ApiClient };