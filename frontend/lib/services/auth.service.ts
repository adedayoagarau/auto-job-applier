/**
 * Authentication Service
 * Handles authentication API calls and token management
 */

import { User, LoginCredentials, RegisterData, AuthToken } from '@/lib/types/auth'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class AuthService {
  private tokenKey = 'auth_token'
  private tokenExpiryKey = 'auth_token_expiry'

  /**
   * Get stored authentication token
   */
  getToken(): string | null {
    if (typeof window === 'undefined') return null

    const token = localStorage.getItem(this.tokenKey)
    const expiry = localStorage.getItem(this.tokenExpiryKey)

    // Check if token is expired
    if (token && expiry) {
      const expiryTime = parseInt(expiry, 10)
      if (Date.now() >= expiryTime) {
        this.clearToken()
        return null
      }
    }

    return token
  }

  /**
   * Store authentication token
   */
  setToken(token: string, expiresIn: number): void {
    if (typeof window === 'undefined') return

    localStorage.setItem(this.tokenKey, token)

    // Calculate expiry time (current time + expires_in seconds - 60s buffer)
    const expiryTime = Date.now() + (expiresIn - 60) * 1000
    localStorage.setItem(this.tokenExpiryKey, expiryTime.toString())
  }

  /**
   * Clear stored token
   */
  clearToken(): void {
    if (typeof window === 'undefined') return

    localStorage.removeItem(this.tokenKey)
    localStorage.removeItem(this.tokenExpiryKey)
  }

  /**
   * Login with email and password
   */
  async login(credentials: LoginCredentials): Promise<{ user: User; token: string }> {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Login failed')
    }

    const authToken: AuthToken = await response.json()

    // Store token
    this.setToken(authToken.access_token, authToken.expires_in)

    // Fetch user profile
    const user = await this.getCurrentUser(authToken.access_token)

    return { user, token: authToken.access_token }
  }

  /**
   * Register a new user
   */
  async register(data: RegisterData): Promise<{ user: User; token: string }> {
    const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Registration failed')
    }

    const authToken: AuthToken = await response.json()

    // Store token
    this.setToken(authToken.access_token, authToken.expires_in)

    // Fetch user profile
    const user = await this.getCurrentUser(authToken.access_token)

    return { user, token: authToken.access_token }
  }

  /**
   * Get current user profile
   */
  async getCurrentUser(token?: string): Promise<User> {
    const authToken = token || this.getToken()

    if (!authToken) {
      throw new Error('Not authenticated')
    }

    const response = await fetch(`${API_BASE_URL}/api/users/me`, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
      },
    })

    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        this.clearToken()
        throw new Error('Session expired')
      }
      throw new Error('Failed to fetch user profile')
    }

    return response.json()
  }

  /**
   * Logout - clear token
   */
  logout(): void {
    this.clearToken()
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return this.getToken() !== null
  }

  /**
   * Make authenticated API request
   */
  async fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
    const token = this.getToken()

    if (!token) {
      throw new Error('Not authenticated')
    }

    const headers = {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
    }

    const response = await fetch(url, {
      ...options,
      headers,
    })

    // If unauthorized, clear token and throw
    if (response.status === 401 || response.status === 403) {
      this.clearToken()
      throw new Error('Session expired')
    }

    return response
  }
}

// Export singleton instance
export const authService = new AuthService()
