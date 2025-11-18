/**
 * Authentication Types
 * Type definitions for authentication-related data structures
 */

export interface User {
  id: number
  email: string
  full_name: string | null
  is_active: boolean
  is_admin: boolean
  created_at: string
  last_login: string | null
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  full_name?: string
}

export interface AuthToken {
  access_token: string
  token_type: string
  expires_in: number
}

export interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

export interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
  clearError: () => void
}
