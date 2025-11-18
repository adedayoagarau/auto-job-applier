import { authService } from '../auth.service'

describe('AuthService', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear()
    jest.clearAllMocks()
  })

  describe('Token Management', () => {
    it('should store and retrieve token', () => {
      authService.setToken('test-token', 3600)

      const token = authService.getToken()
      expect(token).toBe('test-token')
    })

    it('should clear token', () => {
      authService.setToken('test-token', 3600)
      authService.clearToken()

      const token = authService.getToken()
      expect(token).toBeNull()
    })

    it('should return null for expired token', () => {
      // Set token with -1 second expiry (already expired)
      authService.setToken('test-token', -1)

      const token = authService.getToken()
      expect(token).toBeNull()
    })

    it('should check if user is authenticated', () => {
      expect(authService.isAuthenticated()).toBe(false)

      authService.setToken('test-token', 3600)
      expect(authService.isAuthenticated()).toBe(true)

      authService.clearToken()
      expect(authService.isAuthenticated()).toBe(false)
    })
  })

  describe('Token Expiry', () => {
    it('should calculate expiry time with buffer', () => {
      const expiresIn = 3600 // 1 hour
      authService.setToken('test-token', expiresIn)

      const expiryTime = localStorage.getItem('auth_token_expiry')
      expect(expiryTime).toBeTruthy()

      // Expiry should be less than full hour due to 60s buffer
      const actualExpiry = parseInt(expiryTime!, 10)
      const expectedExpiry = Date.now() + (expiresIn - 60) * 1000

      // Allow 1 second tolerance for test execution time
      expect(Math.abs(actualExpiry - expectedExpiry)).toBeLessThan(1000)
    })
  })

  describe('fetchWithAuth', () => {
    beforeEach(() => {
      global.fetch = jest.fn()
    })

    it('should throw error if not authenticated', async () => {
      await expect(authService.fetchWithAuth('/api/test'))
        .rejects
        .toThrow('Not authenticated')
    })

    it('should include Authorization header', async () => {
      authService.setToken('test-token', 3600)

      const mockFetch = global.fetch as jest.Mock
      mockFetch.mockResolvedValueOnce({
        status: 200,
        json: async () => ({ data: 'test' }),
      })

      await authService.fetchWithAuth('/api/test')

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/test',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
          }),
        })
      )
    })

    it('should clear token on 401 response', async () => {
      authService.setToken('test-token', 3600)

      const mockFetch = global.fetch as jest.Mock
      mockFetch.mockResolvedValueOnce({
        status: 401,
      })

      await expect(authService.fetchWithAuth('/api/test'))
        .rejects
        .toThrow('Session expired')

      expect(authService.getToken()).toBeNull()
    })

    it('should clear token on 403 response', async () => {
      authService.setToken('test-token', 3600)

      const mockFetch = global.fetch as jest.Mock
      mockFetch.mockResolvedValueOnce({
        status: 403,
      })

      await expect(authService.fetchWithAuth('/api/test'))
        .rejects
        .toThrow('Session expired')

      expect(authService.getToken()).toBeNull()
    })
  })
})
