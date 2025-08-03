/**
 * Utility functions for the SDK
 */

import { createHmac } from 'crypto';

/**
 * Verify webhook signature
 * @param payload Webhook payload as string or Buffer
 * @param signature Signature from X-Webhook-Signature header
 * @param secret Webhook secret
 * @returns True if signature is valid
 */
export function verifyWebhookSignature(
  payload: string | Buffer,
  signature: string,
  secret: string
): boolean {
  if (!payload || !signature || !secret) {
    return false;
  }

  const payloadBuffer = typeof payload === 'string' ? Buffer.from(payload, 'utf-8') : payload;
  
  const expectedSignature = createHmac('sha256', secret)
    .update(payloadBuffer)
    .digest('hex');

  // Use timing-safe comparison
  if (signature.length !== expectedSignature.length) {
    return false;
  }

  return timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expectedSignature)
  );
}

/**
 * Timing-safe buffer comparison
 */
function timingSafeEqual(a: Buffer, b: Buffer): boolean {
  if (a.length !== b.length) {
    return false;
  }

  let result = 0;
  for (let i = 0; i < a.length; i++) {
    result |= a[i] ^ b[i];
  }

  return result === 0;
}

/**
 * Format duration in seconds to human-readable string
 * @param seconds Duration in seconds
 * @returns Formatted string (e.g., "5m 30s")
 */
export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  const parts: string[] = [];
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0) parts.push(`${minutes}m`);
  if (secs > 0 || parts.length === 0) parts.push(`${secs}s`);

  return parts.join(' ');
}

/**
 * Parse webhook event from request body
 * @param body Request body
 * @returns Parsed webhook event
 */
export function parseWebhookEvent(body: string | Buffer | any): any {
  if (typeof body === 'string') {
    return JSON.parse(body);
  } else if (Buffer.isBuffer(body)) {
    return JSON.parse(body.toString('utf-8'));
  } else {
    return body;
  }
}