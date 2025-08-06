/**
 * Type definitions for the Transcription API JavaScript/TypeScript SDK
 */

// Enums
export type TranscriptStatus = 'processing' | 'completed' | 'failed' | 'queued';
export type TeamRole = 'owner' | 'admin' | 'member' | 'viewer';
export type UserRole = 'user' | 'admin' | 'enterprise';

// Configuration
export interface ClientConfig {
  apiKey?: string;
  baseUrl?: string;
  timeout?: number;
  maxRetries?: number;
}

// Transcription related types
export interface TranscriptionOptions {
  language?: string;
  method?: 'basic' | 'advanced';
  teamId?: number;
  speakerDetection?: boolean;
  sentimentAnalysis?: boolean;
  entityExtraction?: boolean;
}

export interface AnalysisOptions {
  extractEntities?: boolean;
  sentimentAnalysis?: boolean;
  topicModeling?: boolean;
  summarization?: boolean;
  actionItems?: boolean;
}

export interface Transcript {
  id: string;
  title: string;
  status: TranscriptStatus;
  createdAt: string;
  duration?: number;
  text?: string;
  entities?: Record<string, string[]>;
  confidence?: number;
  language?: string;
  fileName?: string;
  fileSize?: number;
  teamId?: number;
  summary?: string;
  sentiment?: Record<string, any>;
  speakers?: Array<{
    id: string;
    name?: string;
    segments: Array<{
      start: number;
      end: number;
      text: string;
    }>;
  }>;
}

// User and team types
export interface User {
  id: number;
  email: string;
  name: string;
  role: UserRole;
  createdAt: string;
}

export interface TeamMember {
  id: number;
  userId: number;
  teamId: number;
  role: TeamRole;
  joinedAt: string;
  userEmail?: string;
  userName?: string;
}

export interface Team {
  id: number;
  name: string;
  description?: string;
  ownerId: number;
  createdAt: string;
  memberCount: number;
  members?: TeamMember[];
}

// API Key types
export interface APIKey {
  id: number;
  name: string;
  keyPrefix: string;
  createdAt: string;
  expiresAt?: string;
  lastUsedAt?: string;
  isActive: boolean;
}

// Webhook types
export interface WebhookEvent {
  eventType: string;
  timestamp: string;
  data: Record<string, any>;
}

// Usage and analytics types
export interface UsageStats {
  totalRequests: number;
  totalTranscriptionMinutes: number;
  currentMonthRequests: number;
  currentMonthMinutes: number;
  rateLimitRemaining: number;
  quotaRemaining?: number;
}

export interface SearchResult {
  transcriptId: string;
  title: string;
  snippet: string;
  score: number;
  createdAt: string;
}

export interface AnalysisResult {
  transcriptId: string;
  entities: Record<string, string[]>;
  sentiment: Record<string, any>;
  topics: string[];
  summary: string;
  actionItems: string[];
  confidence: number;
}

// Pagination types
export interface PaginationOptions {
  skip?: number;
  limit?: number;
}

export interface ListResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

// GraphQL types
export interface GraphQLQuery {
  query: string;
  variables?: Record<string, any>;
  operationName?: string;
}

export interface GraphQLResponse<T = any> {
  data?: T;
  errors?: Array<{
    message: string;
    locations?: Array<{
      line: number;
      column: number;
    }>;
    path?: string[];
    extensions?: Record<string, any>;
  }>;
}

// Webhook configuration types
export interface WebhookConfig {
  url: string;
  events: string[];
  secret?: string;
  headers?: Record<string, string>;
  maxRetries?: number;
  timeoutSeconds?: number;
}

export interface Webhook {
  id: number;
  name: string;
  url: string;
  events: string[];
  status: 'active' | 'inactive';
  lastTriggeredAt?: string;
  successCount: number;
  failureCount: number;
  createdAt: string;
}

// File upload types
export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export interface PresignedUpload {
  uploadUrl: string;
  objectKey: string;
  expiresIn: number;
}

// Error types
export interface APIError {
  message: string;
  statusCode?: number;
  code?: string;
  details?: Record<string, any>;
}

// Real-time types
export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export interface RealtimeTranscription {
  sessionId: string;
  text: string;
  isFinal: boolean;
  confidence: number;
  timestamp: number;
}

// Advanced features
export interface SpeakerDiarization {
  speakers: Array<{
    id: string;
    name?: string;
    confidence: number;
    segments: Array<{
      start: number;
      end: number;
      text: string;
    }>;
  }>;
}

export interface EntityExtraction {
  entities: Array<{
    text: string;
    label: string;
    start: number;
    end: number;
    confidence: number;
  }>;
  relationships: Array<{
    source: string;
    target: string;
    type: string;
    confidence: number;
  }>;
}

export interface SentimentAnalysis {
  overall: {
    sentiment: 'positive' | 'negative' | 'neutral';
    confidence: number;
  };
  timeline: Array<{
    timestamp: number;
    sentiment: 'positive' | 'negative' | 'neutral';
    confidence: number;
  }>;
}

// Export configuration
export interface ExportOptions {
  format: 'json' | 'csv' | 'txt' | 'srt' | 'vtt' | 'docx' | 'pdf';
  includeTimestamps?: boolean;
  includeSpeakers?: boolean;
  includeEntities?: boolean;
  includeSentiment?: boolean;
}

export interface ExportResult {
  downloadUrl: string;
  filename: string;
  format: string;
  expiresAt: string;
}