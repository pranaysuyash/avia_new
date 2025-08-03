/**
 * Transcription Platform JavaScript/TypeScript SDK
 * Official SDK for the Transcription Platform API
 */

export { TranscriptionClient } from './client';
export {
  TranscriptionError,
  AuthenticationError,
  RateLimitError,
  ValidationError,
  NotFoundError,
  ServerError,
} from './exceptions';
export {
  Transcript,
  TranscriptSegment,
  Speaker,
  Team,
  TeamMember,
  Usage,
  UsageData,
  Webhook,
  WebhookEvent,
  TranscriptStatus,
  TranscriptCreateOptions,
  TranscriptListOptions,
  TranscriptExportOptions,
  TranscriptExportFormat,
  WebhookEventType,
  PaginatedResponse,
} from './types';
export { verifyWebhookSignature } from './utils';