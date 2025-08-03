/**
 * Custom exceptions for the SDK
 */

export class TranscriptionError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'TranscriptionError';
    Object.setPrototypeOf(this, TranscriptionError.prototype);
  }
}

export class AuthenticationError extends TranscriptionError {
  constructor(message: string) {
    super(message);
    this.name = 'AuthenticationError';
    Object.setPrototypeOf(this, AuthenticationError.prototype);
  }
}

export class RateLimitError extends TranscriptionError {
  public retryAfter: number;
  public resetTime: number;

  constructor(message: string, retryAfter: number = 60, resetTime: number = 0) {
    super(message);
    this.name = 'RateLimitError';
    this.retryAfter = retryAfter;
    this.resetTime = resetTime;
    Object.setPrototypeOf(this, RateLimitError.prototype);
  }
}

export class ValidationError extends TranscriptionError {
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
    Object.setPrototypeOf(this, ValidationError.prototype);
  }
}

export class NotFoundError extends TranscriptionError {
  constructor(message: string) {
    super(message);
    this.name = 'NotFoundError';
    Object.setPrototypeOf(this, NotFoundError.prototype);
  }
}

export class ServerError extends TranscriptionError {
  constructor(message: string) {
    super(message);
    this.name = 'ServerError';
    Object.setPrototypeOf(this, ServerError.prototype);
  }
}