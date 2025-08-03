/**
 * Type definitions for the Transcription Platform SDK
 */

export interface ClientOptions {
  baseURL?: string;
  timeout?: number;
  maxRetries?: number;
}

export enum TranscriptStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export interface Speaker {
  id: string;
  name?: string;
}

export interface TranscriptSegment {
  start: number;
  end: number;
  text: string;
  speaker?: string;
  confidence?: number;
}

export interface Transcript {
  id: string;
  status: TranscriptStatus | string;
  created_at: string;
  language: string;
  duration?: number;
  completed_at?: string;
  title?: string;
  audio_url?: string;
  text?: string;
  speakers: Speaker[];
  segments: TranscriptSegment[];
  metadata?: Record<string, any>;
  error?: string;
}

export interface TranscriptCreateOptions {
  audioUrl?: string;
  audioFile?: Buffer | File | ReadableStream;
  language?: string;
  enableDiarization?: boolean;
  maxSpeakers?: number;
  webhookUrl?: string;
  metadata?: Record<string, any>;
}

export interface TranscriptListOptions {
  page?: number;
  perPage?: number;
  status?: string;
  language?: string;
  teamId?: number;
}

export enum TranscriptExportFormat {
  TXT = 'txt',
  SRT = 'srt',
  VTT = 'vtt',
  JSON = 'json',
  PDF = 'pdf',
}

export interface TranscriptExportOptions {
  format?: TranscriptExportFormat | string;
  includeTimestamps?: boolean;
  includeSpeakers?: boolean;
}

export interface TeamMember {
  id: number;
  username: string;
  email: string;
  role: string;
  joined_at: string;
}

export interface Team {
  id: number;
  name: string;
  created_at: string;
  description?: string;
  members: TeamMember[];
}

export interface UsageData {
  current: number;
  limit: number;
  period_start: string;
  period_end: string;
}

export interface Usage {
  period: {
    start: string;
    end: string;
  };
  usage: Record<string, UsageData>;
  limits: Record<string, number>;
}

export enum WebhookEventType {
  TRANSCRIPT_CREATED = 'transcript.created',
  TRANSCRIPT_UPDATED = 'transcript.updated',
  TRANSCRIPT_DELETED = 'transcript.deleted',
  TRANSCRIPT_COMPLETED = 'transcript.completed',
  TRANSCRIPT_FAILED = 'transcript.failed',
  TRANSCRIPT_SHARED = 'transcript.shared',
  TEAM_CREATED = 'team.created',
  TEAM_UPDATED = 'team.updated',
  TEAM_DELETED = 'team.deleted',
  TEAM_MEMBER_ADDED = 'team.member.added',
  TEAM_MEMBER_REMOVED = 'team.member.removed',
  USAGE_LIMIT_WARNING = 'usage.limit.warning',
  USAGE_LIMIT_EXCEEDED = 'usage.limit.exceeded',
}

export interface Webhook {
  id: number;
  name: string;
  url: string;
  events: string[];
  status: string;
  created_at: string;
  secret?: string;
  last_triggered_at?: string;
  success_count: number;
  failure_count: number;
}

export interface WebhookCreateOptions {
  name: string;
  url: string;
  events: WebhookEventType[] | string[];
  secret?: string;
}

export interface WebhookEvent {
  id: string;
  type: string;
  created: string;
  data: Record<string, any>;
}

export interface PaginationInfo {
  page: number;
  per_page: number;
  total: number;
  pages: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: PaginationInfo;
}