import { retryWithBackoff, fetchWithRetry } from '../retry'

describe('retryWithBackoff', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should succeed on first attempt', async () => {
    const fn = jest.fn().mockResolvedValue('success')

    const result = await retryWithBackoff(fn)

    expect(result).toBe('success')
    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('should retry on network errors', async () => {
    const fn = jest.fn()
      .mockRejectedValueOnce(new TypeError('fetch failed'))
      .mockResolvedValueOnce('success')

    const result = await retryWithBackoff(fn, { maxRetries: 3, initialDelay: 10 })

    expect(result).toBe('success')
    expect(fn).toHaveBeenCalledTimes(2)
  })

  it('should retry on retryable status codes', async () => {
    const error: any = new Error('HTTP 503')
    error.status = 503

    const fn = jest.fn()
      .mockRejectedValueOnce(error)
      .mockResolvedValueOnce('success')

    const result = await retryWithBackoff(fn, { maxRetries: 3, initialDelay: 10 })

    expect(result).toBe('success')
    expect(fn).toHaveBeenCalledTimes(2)
  })

  it('should not retry on non-retryable errors', async () => {
    const error = new Error('Not retryable')

    const fn = jest.fn().mockRejectedValue(error)

    await expect(retryWithBackoff(fn, { maxRetries: 3 })).rejects.toThrow('Not retryable')
    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('should exhaust retries and throw last error', async () => {
    const error: any = new Error('HTTP 500')
    error.status = 500

    const fn = jest.fn().mockRejectedValue(error)

    await expect(retryWithBackoff(fn, { maxRetries: 2, initialDelay: 10 })).rejects.toThrow('HTTP 500')
    expect(fn).toHaveBeenCalledTimes(3) // Initial + 2 retries
  })

  it('should call onRetry callback', async () => {
    const error: any = new Error('HTTP 503')
    error.status = 503

    const onRetry = jest.fn()
    const fn = jest.fn()
      .mockRejectedValueOnce(error)
      .mockResolvedValueOnce('success')

    await retryWithBackoff(fn, { maxRetries: 3, initialDelay: 10, onRetry })

    expect(onRetry).toHaveBeenCalledWith(1, error)
  })

  it('should use exponential backoff', async () => {
    const error: any = new Error('HTTP 503')
    error.status = 503

    const fn = jest.fn()
      .mockRejectedValueOnce(error)
      .mockRejectedValueOnce(error)
      .mockResolvedValueOnce('success')

    const startTime = Date.now()

    await retryWithBackoff(fn, {
      maxRetries: 3,
      initialDelay: 100,
      backoffFactor: 2,
    })

    const duration = Date.now() - startTime

    // Should wait at least 100ms + 200ms = 300ms
    expect(duration).toBeGreaterThanOrEqual(250)
    expect(fn).toHaveBeenCalledTimes(3)
  })
})

describe('fetchWithRetry', () => {
  beforeEach(() => {
    global.fetch = jest.fn()
  })

  it('should retry on 503 status', async () => {
    const mockFetch = global.fetch as jest.Mock

    mockFetch
      .mockResolvedValueOnce({ status: 503 } as Response)
      .mockResolvedValueOnce({ status: 200 } as Response)

    const response = await fetchWithRetry('http://example.com', {}, { initialDelay: 10 })

    expect(response.status).toBe(200)
    expect(mockFetch).toHaveBeenCalledTimes(2)
  })

  it('should not retry on 404', async () => {
    const mockFetch = global.fetch as jest.Mock

    mockFetch.mockResolvedValueOnce({ status: 404 } as Response)

    const response = await fetchWithRetry('http://example.com')

    expect(response.status).toBe(404)
    expect(mockFetch).toHaveBeenCalledTimes(1)
  })
})
