/**
 * Exception classes for the Transcription API JavaScript/TypeScript SDK
 */

/**
 * Base exception for all API errors
 */
export class TranscriptionAPIError extends Error {
  public statusCode?: number;
  public responseData?: Record<string, any>;
  public code?: string;

  constructor(
    message: string,
    statusCode?: number,
    responseData?: Record<string, any>,
    code?: string
  ) {
    super(message);
    this.name = 'TranscriptionAPIError';
    this.statusCode = statusCode;
    this.responseData = responseData || {};
    this.code = code;

    // Maintains proper stack trace for where our error was thrown (only available on V8)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, TranscriptionAPIError);
    }
  }

  toString(): string {
    if (this.statusCode) {
      return `[${this.statusCode}] ${this.message}`;
    }
    return this.message;
  }
}

/**
 * Raised when authentication fails
 */
export class AuthenticationError extends TranscriptionAPIError {
  constructor(message: string = 'Authentication failed') {
    super(message, 401);
    this.name = 'AuthenticationError';
  }
}

/**
 * Raised when user doesn't have permission for the requested action
 */
export class AuthorizationError extends TranscriptionAPIError {
  constructor(message: string = 'Access denied') {
    super(message, 403);
    this.name = 'AuthorizationError';
  }
}

/**
 * Raised when request validation fails
 */
export class ValidationError extends TranscriptionAPIError {
  public errors?: string[];

  constructor(message: string = 'Validation error', errors?: string[]) {
    super(message, 400);
    this.name = 'ValidationError';
    this.errors = errors || [];
  }
}

/**
 * Raised when a resource is not found
 */
export class NotFoundError extends TranscriptionAPIError {
  constructor(message: string = 'Resource not found') {
    super(message, 404);
    this.name = 'NotFoundError';
  }
}

/**
 * Raised when rate limit is exceeded
 */
export class RateLimitError extends TranscriptionAPIError {
  public retryAfter?: number;

  constructor(message: string = 'Rate limit exceeded', retryAfter?: number) {
    super(message, 429);
    this.name = 'RateLimitError';
    this.retryAfter = retryAfter;
  }
}

/**
 * Raised when usage quota is exceeded
 */
export class QuotaExceededError extends TranscriptionAPIError {
  constructor(message: string = 'Usage quota exceeded') {
    super(message, 402);
    this.name = 'QuotaExceededError';
  }
}

/**
 * Raised when server returns 5xx error
 */
export class ServerError extends TranscriptionAPIError {
  constructor(message: string = 'Internal server error', statusCode: number = 500) {
    super(message, statusCode);
    this.name = 'ServerError';
  }
}

/**
 * Raised when request times out
 */
export class TimeoutError extends TranscriptionAPIError {
  constructor(message: string = 'Request timed out') {
    super(message);
    this.name = 'TimeoutError';
  }
}

/**
 * Raised when connection to API fails
 */
export class ConnectionError extends TranscriptionAPIError {
  constructor(message: string = 'Connection failed') {
    super(message);
    this.name = 'ConnectionError';
  }
}

/**
 * Raised when there's an issue with file handling
 */
export class FileError extends TranscriptionAPIError {
  constructor(message: string = 'File error') {
    super(message);
    this.name = 'FileError';
  }
}

/**
 * Raised when file type is not supported
 */
export class UnsupportedFileTypeError extends FileError {
  public fileType?: string;

  constructor(fileType?: string) {
    const message = fileType 
      ? `Unsupported file type: ${fileType}` 
      : 'Unsupported file type';
    super(message);
    this.name = 'UnsupportedFileTypeError';
    this.fileType = fileType;
  }
}

/**
 * Raised when file is too large
 */
export class FileSizeError extends FileError {
  public size?: number;
  public maxSize?: number;

  constructor(size?: number, maxSize?: number) {
    let message = 'File too large';
    if (size && maxSize) {
      message = `File size ${size} bytes exceeds maximum ${maxSize} bytes`;
    }
    super(message);
    this.name = 'FileSizeError';
    this.size = size;
    this.maxSize = maxSize;
  }
}

/**
 * Raised when transcription processing fails
 */
export class TranscriptionError extends TranscriptionAPIError {
  public transcriptId?: string;

  constructor(message: string = 'Transcription failed', transcriptId?: string) {
    super(message);
    this.name = 'TranscriptionError';
    this.transcriptId = transcriptId;
  }
}

/**
 * Raised when content analysis fails
 */
export class AnalysisError extends TranscriptionAPIError {
  public transcriptId?: string;

  constructor(message: string = 'Analysis failed', transcriptId?: string) {
    super(message);
    this.name = 'AnalysisError';
    this.transcriptId = transcriptId;
  }
}

/**
 * Raised when webhook operations fail
 */
export class WebhookError extends TranscriptionAPIError {
  constructor(message: string = 'Webhook error') {
    super(message);
    this.name = 'WebhookError';
  }
}

/**
 * Raised when team operations fail
 */
export class TeamError extends TranscriptionAPIError {
  constructor(message: string = 'Team operation failed') {
    super(message);
    this.name = 'TeamError';
  }
}

/**
 * Raised when SDK configuration is invalid
 */
export class ConfigurationError extends TranscriptionAPIError {
  constructor(message: string = 'Configuration error') {
    super(message);
    this.name = 'ConfigurationError';
  }
}

/**
 * Raised when GraphQL query fails
 */
export class GraphQLError extends TranscriptionAPIError {
  public graphqlErrors?: Array<{
    message: string;
    locations?: Array<{ line: number; column: number }>;
    path?: string[];
  }>;

  constructor(
    message: string = 'GraphQL error',
    graphqlErrors?: Array<{
      message: string;
      locations?: Array<{ line: number; column: number }>;
      path?: string[];
    }>
  ) {
    super(message);
    this.name = 'GraphQLError';
    this.graphqlErrors = graphqlErrors;
  }
}

/**
 * Raised when WebSocket connection fails
 */
export class WebSocketError extends TranscriptionAPIError {
  constructor(message: string = 'WebSocket error') {
    super(message);
    this.name = 'WebSocketError';
  }
}

/**
 * Type guard to check if error is a TranscriptionAPIError
 */
export function isTranscriptionAPIError(error: any): error is TranscriptionAPIError {
  return error instanceof TranscriptionAPIError;
}

/**
 * Type guard to check if error is a specific error type
 */
export function isErrorType<T extends TranscriptionAPIError>(
  error: any,
  ErrorClass: new (...args: any[]) => T
): error is T {
  return error instanceof ErrorClass;
}