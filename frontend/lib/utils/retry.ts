/**
 * Retry Utility
 * Implements exponential backoff for failed API requests
 */

export interface RetryOptions {
  maxRetries?: number
  initialDelay?: number
  maxDelay?: number
  backoffFactor?: number
  retryableStatuses?: number[]
  onRetry?: (attempt: number, error: Error) => void
}

const DEFAULT_OPTIONS: Required<RetryOptions> = {
  maxRetries: 3,
  initialDelay: 1000, // 1 second
  maxDelay: 10000, // 10 seconds
  backoffFactor: 2,
  retryableStatuses: [408, 429, 500, 502, 503, 504],
  onRetry: () => {},
}

/**
 * Sleep for specified milliseconds
 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * Calculate delay for next retry using exponential backoff
 */
function calculateDelay(attempt: number, options: Required<RetryOptions>): number {
  const delay = options.initialDelay * Math.pow(options.backoffFactor, attempt)
  return Math.min(delay, options.maxDelay)
}

/**
 * Check if error is retryable
 */
function isRetryable(error: any, options: Required<RetryOptions>): boolean {
  // Network errors are always retryable
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return true
  }

  // Check HTTP status codes
  if (error.status && options.retryableStatuses.includes(error.status)) {
    return true
  }

  return false
}

/**
 * Retry a function with exponential backoff
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  const opts = { ...DEFAULT_OPTIONS, ...options }
  let lastError: Error

  for (let attempt = 0; attempt <= opts.maxRetries; attempt++) {
    try {
      return await fn()
    } catch (error: any) {
      lastError = error

      // Don't retry if we've exhausted attempts
      if (attempt >= opts.maxRetries) {
        throw error
      }

      // Don't retry if error is not retryable
      if (!isRetryable(error, opts)) {
        throw error
      }

      // Calculate delay and notify
      const delay = calculateDelay(attempt, opts)
      opts.onRetry(attempt + 1, error)

      // Wait before retrying
      await sleep(delay)
    }
  }

  throw lastError!
}

/**
 * Fetch with retry
 * Wrapper around fetch that automatically retries on failure
 */
export async function fetchWithRetry(
  url: string,
  options?: RequestInit,
  retryOptions?: RetryOptions
): Promise<Response> {
  return retryWithBackoff(async () => {
    const response = await fetch(url, options)

    // Throw error for retryable status codes
    if (
      retryOptions?.retryableStatuses?.includes(response.status) ||
      DEFAULT_OPTIONS.retryableStatuses.includes(response.status)
    ) {
      const error: any = new Error(`HTTP ${response.status}`)
      error.status = response.status
      throw error
    }

    return response
  }, retryOptions)
}
