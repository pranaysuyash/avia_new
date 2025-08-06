/**
 * Transcription API JavaScript/TypeScript SDK
 * 
 * A comprehensive SDK for the Audio/Video Transcription Platform API.
 * Provides easy-to-use interfaces for transcription, analysis, and team management.
 */

export { TranscriptionClient } from './client';
export { AsyncTranscriptionClient } from './async-client';

// Types and interfaces
export type {
  Transcript,
  TranscriptStatus,
  Team,
  TeamMember,
  TeamRole,
  User,
  UserRole,
  TranscriptionOptions,
  AnalysisOptions,
  WebhookEvent,
  APIKey,
  UsageStats,
  SearchResult,
  AnalysisResult,
  ClientConfig,
  PaginationOptions,
  ListResponse
} from './types';

// Exceptions
export {
  TranscriptionAPIError,
  AuthenticationError,
  AuthorizationError,
  ValidationError,
  NotFoundError,
  RateLimitError,
  QuotaExceededError,
  ServerError,
  TimeoutError,
  ConnectionError,
  FileError,
  UnsupportedFileTypeError,
  FileSizeError,
  TranscriptionError,
  AnalysisError,
  WebhookError,
  TeamError,
  ConfigurationError
} from './exceptions';

// Utilities
export { validateApiKey, isValidFileType, formatFileSize } from './utils';

// Constants
export const SDK_VERSION = '1.0.0';
export const DEFAULT_BASE_URL = 'https://api.transcriptionplatform.com/v1';
export const SUPPORTED_FILE_TYPES = [
  'audio/mpeg',
  'audio/wav',
  'audio/mp4',
  'audio/m4a',
  'audio/ogg',
  'audio/webm',
  'video/mp4',
  'video/mov',
  'video/avi',
  'video/webm'
];

// Default export
export default TranscriptionClient;