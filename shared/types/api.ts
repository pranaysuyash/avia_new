/**
 * Shared API Type Definitions
 * 
 * This file contains all shared type definitions used across the platform
 * for API requests, responses, and data models.
 */

// ===========================
// Base API Types
// ===========================

export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  errors?: string[];
  metadata?: Record<string, any>;
  timestamp: string;
}

export interface PaginatedResponse<T = any> extends APIResponse<T[]> {
  pagination: PaginationInfo;
}

export interface PaginationInfo {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

// ===========================
// Error Types
// ===========================

export enum ErrorCode {
  // Authentication errors
  AUTHENTICATION_FAILED = 'AUTHENTICATION_FAILED',
  INSUFFICIENT_PERMISSIONS = 'INSUFFICIENT_PERMISSIONS',
  TOKEN_EXPIRED = 'TOKEN_EXPIRED',
  
  // Validation errors
  INVALID_INPUT = 'INVALID_INPUT',
  MISSING_REQUIRED_FIELD = 'MISSING_REQUIRED_FIELD',
  INVALID_FILE_FORMAT = 'INVALID_FILE_FORMAT',
  FILE_TOO_LARGE = 'FILE_TOO_LARGE',
  
  // Business logic errors
  RESOURCE_NOT_FOUND = 'RESOURCE_NOT_FOUND',
  RESOURCE_ALREADY_EXISTS = 'RESOURCE_ALREADY_EXISTS',
  OPERATION_NOT_ALLOWED = 'OPERATION_NOT_ALLOWED',
  QUOTA_EXCEEDED = 'QUOTA_EXCEEDED',
  
  // System errors
  INTERNAL_SERVER_ERROR = 'INTERNAL_SERVER_ERROR',
  SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE',
  RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED',
  
  // Processing errors
  MEDIA_PROCESSING_FAILED = 'MEDIA_PROCESSING_FAILED',
  AI_ANALYSIS_FAILED = 'AI_ANALYSIS_FAILED',
  TRANSCRIPTION_FAILED = 'TRANSCRIPTION_FAILED'
}

export interface APIError {
  error_code: ErrorCode;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
}

// ===========================
// User Types
// ===========================

export enum UserRole {
  ADMIN = 'admin',
  USER = 'user',
  VIEWER = 'viewer'
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  avatar_url?: string;
  created_at: string;
  updated_at: string;
  last_login?: string;
  is_active: boolean;
  preferences: UserPreferences;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  language: string;
  timezone: string;
  notifications: NotificationSettings;
  privacy: PrivacySettings;
}

export interface NotificationSettings {
  email_notifications: boolean;
  push_notifications: boolean;
  processing_complete: boolean;
  collaboration_updates: boolean;
  system_updates: boolean;
}

export interface PrivacySettings {
  profile_visibility: 'public' | 'private' | 'team';
  data_sharing: boolean;
  analytics_tracking: boolean;
}

export interface UserCreate {
  email: string;
  password: string;
  name: string;
  company?: string;
}

export interface UserUpdate {
  name?: string;
  avatar_url?: string;
  preferences?: Partial<UserPreferences>;
}

// ===========================
// Authentication Types
// ===========================

export interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface TokenRefreshRequest {
  refresh_token: string;
}

export interface APIKey {
  id: string;
  name: string;
  key?: string; // Only returned on creation
  created_at: string;
  expires_at?: string;
  last_used_at?: string;
  is_active: boolean;
  scopes: string[];
}

export interface APIKeyCreate {
  name: string;
  expires_in_days?: number;
  scopes?: string[];
}

// ===========================
// Media Types
// ===========================

export enum MediaType {
  AUDIO = 'audio',
  VIDEO = 'video',
  IMAGE = 'image',
  DOCUMENT = 'document'
}

export enum ProcessingStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export interface MediaFile {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  media_type: MediaType;
  duration?: number; // For audio/video files
  dimensions?: { width: number; height: number }; // For images/videos
  upload_url?: string;
  download_url?: string;
  thumbnail_url?: string;
  created_at: string;
  updated_at: string;
}

export interface MediaUploadRequest {
  filename: string;
  file_size: number;
  mime_type: string;
  media_type: MediaType;
}

export interface MediaUploadResponse {
  upload_url: string;
  file_id: string;
  expires_at: string;
}

// ===========================
// Transcription Types
// ===========================

export interface TranscriptionJob {
  id: string;
  user_id: string;
  team_id?: string;
  media_file: MediaFile;
  status: ProcessingStatus;
  progress: number; // 0-100
  language: string;
  model_used: string;
  processing_options: TranscriptionOptions;
  result?: TranscriptionResult;
  error_message?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface TranscriptionOptions {
  language: string;
  model: 'basic' | 'advanced' | 'whisper' | 'custom';
  enable_speaker_diarization: boolean;
  enable_punctuation: boolean;
  enable_profanity_filter: boolean;
  custom_vocabulary?: string[];
  output_format: 'text' | 'srt' | 'vtt' | 'json';
}

export interface TranscriptionResult {
  text: string;
  segments: TranscriptionSegment[];
  speakers?: SpeakerInfo[];
  confidence: number;
  language_detected: string;
  processing_time: number;
  word_count: number;
  metadata: TranscriptionMetadata;
}

export interface TranscriptionSegment {
  id: string;
  start_time: number;
  end_time: number;
  text: string;
  confidence: number;
  speaker_id?: string;
  words?: WordInfo[];
}

export interface WordInfo {
  word: string;
  start_time: number;
  end_time: number;
  confidence: number;
}

export interface SpeakerInfo {
  id: string;
  name?: string;
  confidence: number;
  total_speaking_time: number;
  segment_count: number;
  voice_characteristics?: VoiceCharacteristics;
}

export interface VoiceCharacteristics {
  pitch: number;
  energy: number;
  spectral_centroid: number;
  gender_prediction?: 'male' | 'female' | 'unknown';
}

export interface TranscriptionMetadata {
  audio_quality: number;
  noise_level: number;
  speech_rate: number;
  silence_percentage: number;
  processing_model: string;
  model_version: string;
}

// ===========================
// AI Analysis Types
// ===========================

export interface AIAnalysisJob {
  id: string;
  transcription_id: string;
  analysis_type: AnalysisType[];
  status: ProcessingStatus;
  progress: number;
  result?: AIAnalysisResult;
  error_message?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export enum AnalysisType {
  SENTIMENT = 'sentiment',
  EMOTION = 'emotion',
  TOPICS = 'topics',
  ENTITIES = 'entities',
  SUMMARY = 'summary',
  ACTION_ITEMS = 'action_items',
  KEY_PHRASES = 'key_phrases',
  LANGUAGE_DETECTION = 'language_detection'
}

export interface AIAnalysisResult {
  sentiment?: SentimentAnalysis;
  emotion?: EmotionAnalysis;
  topics?: TopicAnalysis[];
  entities?: EntityExtraction[];
  summary?: SummaryResult;
  action_items?: ActionItem[];
  key_phrases?: KeyPhrase[];
  insights?: Insight[];
  confidence: number;
  processing_time: number;
}

export interface SentimentAnalysis {
  overall_sentiment: 'positive' | 'negative' | 'neutral';
  confidence: number;
  sentiment_timeline: SentimentPoint[];
  sentiment_distribution: {
    positive: number;
    negative: number;
    neutral: number;
  };
}

export interface SentimentPoint {
  timestamp: number;
  sentiment: 'positive' | 'negative' | 'neutral';
  score: number;
  confidence: number;
}

export interface EmotionAnalysis {
  dominant_emotion: string;
  confidence: number;
  emotion_timeline: EmotionPoint[];
  emotion_distribution: Record<string, number>;
}

export interface EmotionPoint {
  timestamp: number;
  emotions: Record<string, number>;
  dominant_emotion: string;
  confidence: number;
}

export interface TopicAnalysis {
  id: string;
  name: string;
  keywords: string[];
  confidence: number;
  relevance_score: number;
  time_segments: TimeSegment[];
  summary: string;
}

export interface TimeSegment {
  start_time: number;
  end_time: number;
  relevance_score: number;
}

export interface EntityExtraction {
  id: string;
  text: string;
  type: EntityType;
  confidence: number;
  start_offset: number;
  end_offset: number;
  metadata?: Record<string, any>;
  linked_data?: LinkedData;
}

export enum EntityType {
  PERSON = 'person',
  ORGANIZATION = 'organization',
  LOCATION = 'location',
  DATE = 'date',
  TIME = 'time',
  MONEY = 'money',
  PERCENTAGE = 'percentage',
  PHONE_NUMBER = 'phone_number',
  EMAIL = 'email',
  URL = 'url',
  CUSTOM = 'custom'
}

export interface LinkedData {
  source: string;
  url?: string;
  description?: string;
  additional_info?: Record<string, any>;
}

export interface SummaryResult {
  executive_summary: string;
  key_points: string[];
  main_topics: string[];
  conclusions: string[];
  word_count: number;
  compression_ratio: number;
  confidence: number;
}

export interface ActionItem {
  id: string;
  text: string;
  assignee?: string;
  due_date?: string;
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  confidence: number;
  context: string;
  timestamp: number;
}

export interface KeyPhrase {
  phrase: string;
  frequency: number;
  relevance_score: number;
  context_snippets: string[];
}

export interface Insight {
  id: string;
  type: InsightType;
  title: string;
  description: string;
  confidence: number;
  impact_score: number;
  supporting_evidence: string[];
  recommendations?: string[];
}

export enum InsightType {
  TREND = 'trend',
  ANOMALY = 'anomaly',
  PATTERN = 'pattern',
  OPPORTUNITY = 'opportunity',
  RISK = 'risk',
  RECOMMENDATION = 'recommendation'
}

// ===========================
// Team Types
// ===========================

export enum TeamRole {
  OWNER = 'owner',
  ADMIN = 'admin',
  MEMBER = 'member',
  VIEWER = 'viewer'
}

export interface Team {
  id: string;
  name: string;
  description?: string;
  owner_id: string;
  member_count: number;
  created_at: string;
  updated_at: string;
  settings: TeamSettings;
}

export interface TeamSettings {
  visibility: 'public' | 'private';
  allow_member_invites: boolean;
  default_member_role: TeamRole;
  require_approval: boolean;
  data_retention_days: number;
}

export interface TeamMember {
  id: string;
  user: User;
  team_id: string;
  role: TeamRole;
  joined_at: string;
  invited_by: string;
  last_active?: string;
}

export interface TeamInvite {
  email: string;
  role: TeamRole;
  message?: string;
}

// ===========================
// Collaboration Types
// ===========================

export interface CollaborationSession {
  id: string;
  transcription_id: string;
  participants: SessionParticipant[];
  status: 'active' | 'paused' | 'ended';
  created_at: string;
  updated_at: string;
  settings: CollaborationSettings;
}

export interface SessionParticipant {
  user_id: string;
  user: User;
  role: 'editor' | 'viewer' | 'commenter';
  joined_at: string;
  last_active: string;
  cursor_position?: number;
  selection?: TextSelection;
}

export interface TextSelection {
  start: number;
  end: number;
  text: string;
}

export interface CollaborationSettings {
  allow_anonymous: boolean;
  max_participants: number;
  auto_save_interval: number;
  version_history_enabled: boolean;
  comment_permissions: 'all' | 'editors' | 'none';
}

export interface CollaborativeEdit {
  id: string;
  session_id: string;
  user_id: string;
  operation: EditOperation;
  timestamp: string;
  applied: boolean;
}

export interface EditOperation {
  type: 'insert' | 'delete' | 'replace';
  position: number;
  content?: string;
  length?: number;
}

// ===========================
// Export Types
// ===========================

export enum ExportFormat {
  PDF = 'pdf',
  DOCX = 'docx',
  TXT = 'txt',
  JSON = 'json',
  CSV = 'csv',
  SRT = 'srt',
  VTT = 'vtt',
  HTML = 'html'
}

export interface ExportRequest {
  transcription_ids: string[];
  format: ExportFormat;
  options: ExportOptions;
}

export interface ExportOptions {
  include_metadata: boolean;
  include_timestamps: boolean;
  include_speaker_info: boolean;
  include_confidence_scores: boolean;
  include_analysis_results: boolean;
  custom_template?: string;
  branding?: BrandingOptions;
}

export interface BrandingOptions {
  company_name?: string;
  logo_url?: string;
  colors?: {
    primary: string;
    secondary: string;
  };
  footer_text?: string;
}

export interface ExportJob {
  id: string;
  user_id: string;
  request: ExportRequest;
  status: ProcessingStatus;
  progress: number;
  download_url?: string;
  expires_at?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

// ===========================
// WebSocket Types
// ===========================

export interface WebSocketMessage<T = any> {
  type: string;
  data: T;
  timestamp: string;
  user_id?: string;
  session_id?: string;
}

export interface ProgressUpdate {
  job_id: string;
  progress: number;
  status: ProcessingStatus;
  message?: string;
  eta?: number;
}

export interface CollaborationUpdate {
  session_id: string;
  user_id: string;
  operation: EditOperation;
  cursor_position?: number;
  selection?: TextSelection;
}

export interface NotificationMessage {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  actions?: NotificationAction[];
  expires_at?: string;
}

export interface NotificationAction {
  label: string;
  action: string;
  style?: 'primary' | 'secondary' | 'danger';
}

// ===========================
// Search Types
// ===========================

export interface SearchRequest {
  query: string;
  filters?: SearchFilters;
  sort?: SearchSort;
  pagination?: {
    page: number;
    limit: number;
  };
}

export interface SearchFilters {
  media_type?: MediaType[];
  date_range?: {
    start: string;
    end: string;
  };
  language?: string[];
  user_id?: string[];
  team_id?: string[];
  tags?: string[];
  confidence_min?: number;
  duration_range?: {
    min: number;
    max: number;
  };
}

export interface SearchSort {
  field: 'created_at' | 'updated_at' | 'relevance' | 'duration' | 'confidence';
  direction: 'asc' | 'desc';
}

export interface SearchResult {
  id: string;
  type: 'transcription' | 'analysis' | 'user' | 'team';
  title: string;
  description: string;
  relevance_score: number;
  highlights: SearchHighlight[];
  metadata: Record<string, any>;
  url: string;
}

export interface SearchHighlight {
  field: string;
  fragments: string[];
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  took: number;
  aggregations?: Record<string, any>;
}

// ===========================
// Analytics Types
// ===========================

export interface AnalyticsQuery {
  metrics: string[];
  dimensions?: string[];
  filters?: Record<string, any>;
  date_range: {
    start: string;
    end: string;
  };
  granularity?: 'hour' | 'day' | 'week' | 'month';
}

export interface AnalyticsResult {
  data: AnalyticsDataPoint[];
  metadata: {
    total_records: number;
    query_time: number;
    cache_hit: boolean;
  };
}

export interface AnalyticsDataPoint {
  timestamp?: string;
  dimensions: Record<string, string>;
  metrics: Record<string, number>;
}

// ===========================
// System Types
// ===========================

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'down';
  services: ServiceHealth[];
  timestamp: string;
  version: string;
}

export interface ServiceHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'down';
  response_time?: number;
  error_rate?: number;
  last_check: string;
  details?: Record<string, any>;
}

export interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_io: {
    bytes_in: number;
    bytes_out: number;
  };
  active_connections: number;
  queue_size: number;
  error_rate: number;
  response_time_p95: number;
}