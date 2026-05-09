import { NetworkError } from '../errors';

export interface RetryOptions {
  maxAttempts?: number;
  baseDelayMs?: number;
  maxDelayMs?: number;
}

/**
 * Exponential backoff retry wrapper.
 * Retries on NetworkError or fetch failures. Does not retry on validation errors.
 */
export async function withRetry<T>(
  fn: () => Promise<T>,
  opts: RetryOptions = {}
): Promise<T> {
  const { maxAttempts = 3, baseDelayMs = 500, maxDelayMs = 8000 } = opts;
  let lastError: Error | undefined;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (err: any) {
      lastError = err;
      if (attempt === maxAttempts) break;
      // Only retry on network-level errors
      if (err?.code === 'VALIDATION_ERROR' || err?.code === 'NOT_FOUND') throw err;
      const delay = Math.min(baseDelayMs * 2 ** (attempt - 1), maxDelayMs);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw lastError ?? new NetworkError('Request failed after retries');
}
