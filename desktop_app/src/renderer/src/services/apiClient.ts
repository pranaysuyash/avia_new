/**
 * Enhanced API Client for Desktop App
 * Connects to FastAPI backend with all new enterprise features
 */

import axios, { AxiosInstance } from 'axios';

// API Response Types
export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
}

// Auth Types
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

// Enterprise Sales Types
export interface Lead {
  id: string;
  company_name: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  status: LeadStatus;
  score: number;
  priority: 'low' | 'medium' | 'high';
  assigned_to?: string;
  created_at: string;
  updated_at: string;
}

export enum LeadStatus {
  NEW = 'new',
  CONTACTED = 'contacted',
  QUALIFIED = 'qualified',
  PROPOSAL = 'proposal',
  NEGOTIATION = 'negotiation',
  CLOSED_WON = 'closed_won',
  CLOSED_LOST = 'closed_lost'
}

export interface SalesActivity {
  id: string;
  lead_id: string;
  activity_type: string;
  subject: string;
  notes?: string;
  created_by: string;
  created_at: string;
}

export interface PipelineMetrics {
  total_leads: number;
  qualified_leads: number;
  total_pipeline_value: number;
  win_rate: number;
  sales_velocity: {
    avg_deal_size: number;
    win_rate: number;
    avg_sales_cycle: number;
    velocity: number;
  };
  forecast: {
    current_month: number;
    next_month: number;
    current_quarter: number;
  };
  opportunities_by_stage?: Record<string, number>;
  average_deal_size?: number;
  conversion_rate?: number;
}

// Customer Support Types
export interface SupportTicket {
  id: string;
  ticket_number: string;
  customer_name: string;
  subject: string;
  description: string;
  status: TicketStatus;
  priority: 'low' | 'medium' | 'high' | 'critical';
  assigned_to?: string;
  created_at: string;
  updated_at: string;
  sla_deadline?: string;
}

export enum TicketStatus {
  NEW = 'new',
  OPEN = 'open',
  IN_PROGRESS = 'in_progress',
  WAITING_CUSTOMER = 'waiting_customer',
  RESOLVED = 'resolved',
  CLOSED = 'closed'
}

export interface KnowledgeArticle {
  id: string;
  title: string;
  content: string;
  category: string;
  tags: string[];
  helpful_count: number;
  view_count: number;
}

// Marketing Types
export interface Campaign {
  id: string;
  name: string;
  type: 'email' | 'social' | 'content' | 'referral';
  status: 'draft' | 'scheduled' | 'running' | 'paused' | 'completed';
  budget: number;
  spent: number;
  metrics: {
    impressions: number;
    clicks: number;
    conversions: number;
    roi: number;
  };
  start_date: string;
  end_date?: string;
}

export interface ReferralProgram {
  id: string;
  name: string;
  reward_type: string;
  referrer_reward: any;
  referee_reward: any;
  is_active: boolean;
  valid_until: string;
}

// API Platform Types
export interface ApiKey {
  key_id: string;
  name: string;
  scopes: string[];
  rate_limit: number;
  last_used_at?: string;
  created_at: string;
  expires_at?: string;
}

export interface Webhook {
  webhook_id: string;
  url: string;
  events: string[];
  is_active: boolean;
  last_triggered_at?: string;
  failure_count: number;
}

// Compliance Types
export interface ConsentRecord {
  id: string;
  purpose: string;
  data_categories: string[];
  is_given: boolean;
  is_withdrawn: boolean;
  given_at: string;
  valid_until: string;
}

export interface AuditLog {
  id: string;
  event_type: string;
  description: string;
  actor_id: string;
  timestamp: string;
  risk_score: number;
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

// Collaboration Types
export interface Comment {
  id: string;
  transcript_id: string;
  user_id: string;
  user_name: string;
  text: string;
  timestamp_start?: string;
  timestamp_end?: string;
  parent_id?: string;
  resolved: boolean;
  created_at: string;
  updated_at: string;
  replies: Comment[];
}

export interface Annotation {
  id: string;
  transcript_id: string;
  user_id: string;
  user_name: string;
  type: string;
  text?: string;
  data?: any;
  timestamp_start?: string;
  timestamp_end?: string;
  created_at: string;
  updated_at: string;
}

// AI Customization Types
export interface ModelConfig {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  model_type: string;
  base_model: string;
  parameters: any;
  is_active: boolean;
  is_public: boolean;
  created_at: string;
  updated_at: string;
  performance_metrics?: {
    accuracy?: number;
    speed?: number;
    cost_per_request?: number;
    usage_count?: number;
    feedback_score?: number;
  };
}

// Audio Enhancement Types
export interface AudioEnhancementOptions {
  noise_reduction?: boolean;
  normalize?: boolean;
  remove_silence?: boolean;
  enhance_voice?: boolean;
  compress_dynamics?: boolean;
  target_loudness?: number;
  noise_reduction_strength?: number;
}

export interface AudioEnhancementResponse {
  enhanced_audio: string;
  original_metadata: {
    duration: number;
    sample_rate: number;
    channels: number;
    format: string;
    size_bytes: number;
  };
  enhanced_metadata: {
    duration: number;
    sample_rate: number;
    channels: number;
    format: string;
    size_bytes: number;
  };
  processing_time: number;
  enhancements_applied: string[];
}

// TTS Types
export interface TTSRequest {
  text: string;
  voice?: string;
  language?: string;
  speed?: number;
  pitch?: number;
  format?: string;
}

export interface TTSResponse {
  audio_data: string;
  format: string;
  duration: number;
  size_bytes: number;
  synthesis_time: number;
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
  private client: AxiosInstance;
  private authToken: string | null = null;

  constructor(baseURL: string = 'http://localhost:8001') {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        if (this.authToken) {
          config.headers.Authorization = `Bearer ${this.authToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized
          this.authToken = null;
          window.dispatchEvent(new CustomEvent('auth:logout'));
        } else if (error.response?.status === 402) {
          // Handle quota exceeded (Payment Required)
          const usageInfo = error.response.headers['x-usage-info'];
          window.dispatchEvent(new CustomEvent('quota:exceeded', {
            detail: {
              message: error.response.data?.detail || 'Usage quota exceeded',
              usageInfo: usageInfo ? JSON.parse(usageInfo) : null
            }
          }));
        } else if (error.response?.status === 403) {
          // Handle feature access denied
          const requiredFeature = error.response.headers['x-required-feature'];
          if (requiredFeature) {
            window.dispatchEvent(new CustomEvent('feature:access_denied', {
              detail: {
                message: error.response.data?.detail || 'Feature access required',
                requiredFeature
              }
            }));
          }
        }
        return Promise.reject(error);
      }
    );

    // Load saved token
    const savedToken = localStorage.getItem('auth_token');
    if (savedToken) {
      this.authToken = savedToken;
    }
  }

  // Auth Methods
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/api/v1/auth/login', credentials);
    if (response.data.access_token) {
      this.authToken = response.data.access_token;
      localStorage.setItem('auth_token', this.authToken);
    }
    return response.data;
  }

  async logout(): Promise<void> {
    this.authToken = null;
    localStorage.removeItem('auth_token');
  }

  async getCurrentUser(): Promise<UserInfo> {
    const response = await this.client.get<UserInfo>('/api/v1/auth/me');
    return response.data;
  }

  // Enterprise Sales Methods
  async getLeads(filters?: { status?: string; priority?: string }): Promise<Lead[]> {
    const response = await this.client.get<Lead[]>('/api/v1/sales/leads', { params: filters });
    return response.data;
  }

  async createLead(leadData: Partial<Lead>): Promise<Lead> {
    const response = await this.client.post<Lead>('/api/v1/sales/leads', leadData);
    return response.data;
  }

  async updateLead(leadId: string, updates: Partial<Lead>): Promise<Lead> {
    const response = await this.client.put<Lead>(`/api/v1/sales/leads/${leadId}`, updates);
    return response.data;
  }

  async getLeadActivities(leadId: string): Promise<SalesActivity[]> {
    const response = await this.client.get<SalesActivity[]>(`/api/v1/sales/leads/${leadId}/activities`);
    return response.data;
  }

  async createActivity(leadId: string, activity: Partial<SalesActivity>): Promise<SalesActivity> {
    const response = await this.client.post<SalesActivity>(
      `/api/v1/sales/leads/${leadId}/activities`,
      activity
    );
    return response.data;
  }

  async getPipelineMetrics(dateFrom?: string): Promise<PipelineMetrics> {
    const params = dateFrom ? { date_from: dateFrom } : {};
    const response = await this.client.get<PipelineMetrics>('/api/v1/sales/metrics/pipeline', { params });
    return response.data;
  }

  async calculatePricing(pricingData: any): Promise<any> {
    const response = await this.client.post('/api/v1/sales/pricing/calculate', pricingData);
    return response.data;
  }

  async scheduleDemo(demoData: any): Promise<any> {
    const response = await this.client.post('/api/v1/sales/demos', demoData);
    return response.data;
  }

  async createTrial(trialData: any): Promise<any> {
    const response = await this.client.post('/api/v1/sales/trials', trialData);
    return response.data;
  }

  // Customer Support Methods
  async getTickets(filters?: { status?: string; priority?: string }): Promise<SupportTicket[]> {
    const response = await this.client.get<SupportTicket[]>('/api/v1/support/tickets', { params: filters });
    return response.data;
  }

  async createTicket(ticketData: any): Promise<SupportTicket> {
    const response = await this.client.post<SupportTicket>('/api/v1/support/tickets', ticketData);
    return response.data;
  }

  async updateTicket(ticketId: string, updates: any): Promise<SupportTicket> {
    const response = await this.client.put<SupportTicket>(`/api/v1/support/tickets/${ticketId}`, updates);
    return response.data;
  }

  async addTicketMessage(ticketId: string, message: any): Promise<any> {
    const response = await this.client.post(`/api/v1/support/tickets/${ticketId}/messages`, message);
    return response.data;
  }

  async searchKnowledgeBase(query: string, category?: string): Promise<KnowledgeArticle[]> {
    const params = { q: query, ...(category && { category }) };
    const response = await this.client.get<KnowledgeArticle[]>('/api/v1/support/kb/search', { params });
    return response.data;
  }

  async startLiveChat(chatData: any): Promise<any> {
    const response = await this.client.post('/api/v1/support/chat/start', chatData);
    return response.data;
  }

  async getSupportMetrics(): Promise<any> {
    const response = await this.client.get('/api/v1/support/metrics');
    return response.data;
  }

  // Marketing Methods
  async getCampaigns(filters?: { status?: string; type?: string }): Promise<Campaign[]> {
    const response = await this.client.get<Campaign[]>('/api/v1/marketing/campaigns', { params: filters });
    return response.data;
  }

  async createCampaign(campaignData: any): Promise<Campaign> {
    const response = await this.client.post<Campaign>('/api/v1/marketing/campaigns', campaignData);
    return response.data;
  }

  async updateCampaignStatus(campaignId: string, status: string): Promise<any> {
    const response = await this.client.put(`/api/v1/marketing/campaigns/${campaignId}/status`, { status });
    return response.data;
  }

  async createEmailCampaign(campaignId: string, emailData: any): Promise<any> {
    const response = await this.client.post('/api/v1/marketing/email-campaigns', {
      ...emailData,
      campaign_id: campaignId
    });
    return response.data;
  }

  async getReferralPrograms(): Promise<ReferralProgram[]> {
    const response = await this.client.get<ReferralProgram[]>('/api/v1/marketing/referral-programs');
    return response.data;
  }

  async generateReferralCode(programId: string): Promise<any> {
    const response = await this.client.post('/api/v1/marketing/referrals/generate', { program_id: programId });
    return response.data;
  }

  async getReferralStats(): Promise<any> {
    const response = await this.client.get('/api/v1/marketing/referrals/stats');
    return response.data;
  }

  async getGrowthMetrics(dateFrom?: string): Promise<any> {
    const params = dateFrom ? { date_from: dateFrom } : {};
    const response = await this.client.get('/api/v1/marketing/analytics/growth', { params });
    return response.data;
  }

  // API Platform Methods
  async getApiKeys(): Promise<ApiKey[]> {
    const response = await this.client.get<ApiKey[]>('/api/v1/developer/api-keys');
    return response.data;
  }

  async createApiKey(keyConfig: any): Promise<any> {
    const response = await this.client.post('/api/v1/developer/api-keys', keyConfig);
    return response.data;
  }

  async revokeApiKey(keyId: string): Promise<void> {
    await this.client.delete(`/api/v1/developer/api-keys/${keyId}`);
  }

  async getWebhooks(): Promise<Webhook[]> {
    const response = await this.client.get<Webhook[]>('/api/v1/developer/webhooks');
    return response.data;
  }

  async createWebhook(webhookData: any): Promise<any> {
    const response = await this.client.post('/api/v1/developer/webhooks', webhookData);
    return response.data;
  }

  async getApiUsage(dateFrom?: string): Promise<any> {
    const params = dateFrom ? { date_from: dateFrom } : {};
    const response = await this.client.get('/api/v1/developer/usage', { params });
    return response.data;
  }

  async getSdks(): Promise<any[]> {
    const response = await this.client.get<any[]>('/api/v1/developer/sdks');
    return response.data;
  }

  // Compliance Methods
  async getMyConsents(activeOnly = true): Promise<ConsentRecord[]> {
    const response = await this.client.get<ConsentRecord[]>('/api/v1/compliance/consent', {
      params: { active_only: activeOnly }
    });
    return response.data;
  }

  async recordConsent(consentData: any): Promise<any> {
    const response = await this.client.post('/api/v1/compliance/consent', consentData);
    return response.data;
  }

  async withdrawConsent(consentId: string, reason?: string): Promise<void> {
    await this.client.delete(`/api/v1/compliance/consent/${consentId}`, {
      data: reason ? { reason } : {}
    });
  }

  async exportMyData(format: 'json' | 'csv' | 'pdf' = 'json'): Promise<any> {
    const response = await this.client.get('/api/v1/compliance/my-data', {
      params: { format },
      responseType: format === 'json' ? 'json' : 'blob'
    });
    return response.data;
  }

  async getAuditLogs(filters: any): Promise<{ total: number; logs: AuditLog[] }> {
    const response = await this.client.get<{ total: number; logs: AuditLog[] }>(
      '/api/v1/compliance/audit-logs',
      { params: filters }
    );
    return response.data;
  }

  async getSecurityPosture(): Promise<any> {
    const response = await this.client.get('/api/v1/compliance/security-posture');
    return response.data;
  }

  // Usage and Subscription Methods
  async getUsageDashboard(): Promise<UsageResponse> {
    const response = await this.client.get<UsageResponse>('/api/v1/usage/dashboard');
    return response.data;
  }

  async getUsageLimits(): Promise<any> {
    const response = await this.client.get('/api/v1/usage/limits');
    return response.data;
  }

  async getUsageHistory(usageType?: string, days = 30): Promise<any> {
    const params: any = { days };
    if (usageType) params.usage_type = usageType;
    const response = await this.client.get('/api/v1/usage/history', { params });
    return response.data;
  }

  async getUsageAlerts(): Promise<any> {
    const response = await this.client.get('/api/v1/usage/alerts');
    return response.data;
  }

  // Collaboration Methods
  async createComment(commentData: {
    transcript_id: string;
    text: string;
    timestamp_start?: string;
    timestamp_end?: string;
    parent_id?: string;
  }): Promise<Comment> {
    const response = await this.client.post<Comment>('/api/v1/collaboration/comments', commentData);
    return response.data;
  }

  async getTranscriptComments(transcriptId: string): Promise<Comment[]> {
    const response = await this.client.get<Comment[]>(`/api/v1/collaboration/comments/${transcriptId}`);
    return response.data;
  }

  async updateComment(commentId: string, updates: { text?: string; resolved?: boolean }): Promise<Comment> {
    const response = await this.client.put<Comment>(`/api/v1/collaboration/comments/${commentId}`, updates);
    return response.data;
  }

  async deleteComment(commentId: string): Promise<void> {
    await this.client.delete(`/api/v1/collaboration/comments/${commentId}`);
  }

  async createAnnotation(annotationData: {
    transcript_id: string;
    type: string;
    text?: string;
    data?: any;
    timestamp_start?: string;
    timestamp_end?: string;
  }): Promise<Annotation> {
    const response = await this.client.post<Annotation>('/api/v1/collaboration/annotations', annotationData);
    return response.data;
  }

  async getTranscriptAnnotations(transcriptId: string, annotationType?: string): Promise<Annotation[]> {
    const params = annotationType ? { annotation_type: annotationType } : {};
    const response = await this.client.get<Annotation[]>(`/api/v1/collaboration/annotations/${transcriptId}`, { params });
    return response.data;
  }

  async createCollaborationSession(transcriptId: string): Promise<any> {
    const response = await this.client.post('/api/v1/collaboration/sessions', { transcript_id: transcriptId });
    return response.data;
  }

  async getActiveCollaborationSession(transcriptId: string): Promise<any> {
    const response = await this.client.get(`/api/v1/collaboration/sessions/${transcriptId}/active`);
    return response.data;
  }

  // AI Customization Methods
  async createModelConfig(configData: {
    name: string;
    description?: string;
    model_type: string;
    base_model: string;
    parameters: any;
    is_public?: boolean;
  }): Promise<ModelConfig> {
    const response = await this.client.post<ModelConfig>('/api/v1/ai/models/config', configData);
    return response.data;
  }

  async getModelConfigs(modelType?: string, includePublic = true): Promise<ModelConfig[]> {
    const params: any = { include_public: includePublic };
    if (modelType) params.model_type = modelType;
    const response = await this.client.get<ModelConfig[]>('/api/v1/ai/models/config', { params });
    return response.data;
  }

  async getModelConfig(configId: string): Promise<ModelConfig> {
    const response = await this.client.get<ModelConfig>(`/api/v1/ai/models/config/${configId}`);
    return response.data;
  }

  async updateModelConfig(configId: string, updates: any): Promise<any> {
    const response = await this.client.put(`/api/v1/ai/models/config/${configId}`, updates);
    return response.data;
  }

  async deleteModelConfig(configId: string): Promise<any> {
    const response = await this.client.delete(`/api/v1/ai/models/config/${configId}`);
    return response.data;
  }

  async testModelConfig(configId: string, testInput: any): Promise<any> {
    const response = await this.client.post('/api/v1/ai/models/test', {
      config_id: configId,
      test_input: testInput
    });
    return response.data;
  }

  async getAvailableModels(): Promise<any> {
    const response = await this.client.get('/api/v1/ai/models/available');
    return response.data;
  }

  async getModelPresets(): Promise<any> {
    const response = await this.client.get('/api/v1/ai/models/presets');
    return response.data;
  }

  async submitModelFeedback(configId: string, score: number, feedback?: string): Promise<any> {
    const response = await this.client.post('/api/v1/ai/models/feedback', {
      config_id: configId,
      score,
      feedback
    });
    return response.data;
  }

  // Audio Enhancement Methods
  async enhanceAudio(audioData: string, options: AudioEnhancementOptions): Promise<AudioEnhancementResponse> {
    const response = await this.client.post<AudioEnhancementResponse>('/api/v1/audio/enhance', {
      audio_data: audioData,
      enhancement_options: options
    });
    return response.data;
  }

  async analyzeAudio(audioData: string): Promise<any> {
    const response = await this.client.post('/api/v1/audio/analyze', { audio_data: audioData });
    return response.data;
  }

  async getAudioPresets(): Promise<any> {
    const response = await this.client.get('/api/v1/audio/presets');
    return response.data;
  }

  async analyzeAudioQuality(audioData: string): Promise<any> {
    const response = await this.client.post('/api/v1/audio/analyze/quality', { audio_data: audioData });
    return response.data;
  }

  async extractAudioSegment(audioData: string, startTime: number, endTime: number): Promise<any> {
    const response = await this.client.post('/api/v1/audio/segment/extract', {
      audio_data: audioData,
      start_time: startTime,
      end_time: endTime
    });
    return response.data;
  }

  async detectSilenceSegments(audioData: string, silenceThreshold = -40, minSilenceDuration = 500): Promise<any> {
    const response = await this.client.post('/api/v1/audio/analyze/silence', {
      audio_data: audioData,
      silence_threshold: silenceThreshold,
      min_silence_duration: minSilenceDuration
    });
    return response.data;
  }

  // TTS Methods
  async synthesizeSpeech(ttsRequest: TTSRequest): Promise<TTSResponse> {
    const response = await this.client.post<TTSResponse>('/api/v1/tts/synthesize', ttsRequest);
    return response.data;
  }

  async synthesizeSpeechAdvanced(text: string, voiceId: string, voiceSettings?: any, outputFormat = 'mp3'): Promise<TTSResponse> {
    const request: any = {
      text,
      voice_id: voiceId,
      output_format: outputFormat
    };
    if (voiceSettings) {
      request.voice_settings = voiceSettings;
    }
    const response = await this.client.post<TTSResponse>('/api/v1/tts/synthesize/advanced', request);
    return response.data;
  }

  async getVoices(language?: string): Promise<Voice[]> {
    const params = language ? { language } : {};
    const response = await this.client.get<Voice[]>('/api/v1/tts/voices', { params });
    return response.data;
  }

  async getSupportedLanguages(): Promise<any> {
    const response = await this.client.get('/api/v1/tts/languages');
    return response.data;
  }

  async searchVoices(query: string, language?: string, gender?: string): Promise<Voice[]> {
    const params: any = { query };
    if (language) params.language = language;
    if (gender) params.gender = gender;
    const response = await this.client.get<Voice[]>('/api/v1/tts/voices/search', { params });
    return response.data;
  }

  async getVoiceDetails(voiceId: string): Promise<Voice> {
    const response = await this.client.get<Voice>(`/api/v1/tts/voice/${voiceId}`);
    return response.data;
  }

  async estimateTTSCost(text: string): Promise<any> {
    const response = await this.client.post('/api/v1/tts/estimate-cost', { text });
    return response.data;
  }

  async getTTSSynthesisHistory(limit = 20): Promise<any> {
    const response = await this.client.get('/api/v1/tts/synthesis-history', { params: { limit } });
    return response.data;
  }

  // WebSocket connection for real-time features
  connectWebSocket(endpoint: string): WebSocket {
    const wsUrl = this.client.defaults.baseURL!.replace('http', 'ws');
    const ws = new WebSocket(`${wsUrl}${endpoint}`);
    
    if (this.authToken) {
      ws.addEventListener('open', () => {
        ws.send(JSON.stringify({ type: 'auth', token: this.authToken }));
      });
    }
    
    return ws;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export types
export type { ApiClient };