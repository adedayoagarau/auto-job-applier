"use client"

/**
 * Authentication Context
 * Provides authentication state and methods throughout the app
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import { User, LoginCredentials, RegisterData, AuthContextType, AuthState } from '@/lib/types/auth'
import { authService } from '@/lib/services/auth.service'

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const router = useRouter()
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,
  })

  // Initialize auth state from stored token
  useEffect(() => {
    const initializeAuth = async () => {
      const token = authService.getToken()

      if (!token) {
        setState(prev => ({ ...prev, isLoading: false }))
        return
      }

      try {
        const user = await authService.getCurrentUser(token)
        setState({
          user,
          token,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        })
      } catch (error) {
        // Token invalid or expired
        authService.clearToken()
        setState({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        })
      }
    }

    initializeAuth()
  }, [])

  /**
   * Login with credentials
   */
  const login = async (credentials: LoginCredentials): Promise<void> => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }))

      const { user, token } = await authService.login(credentials)

      setState({
        user,
        token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      })

      // Redirect to dashboard
      router.push('/')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed'
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }))
      throw error
    }
  }

  /**
   * Register new user
   */
  const register = async (data: RegisterData): Promise<void> => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }))

      const { user, token } = await authService.register(data)

      setState({
        user,
        token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      })

      // Redirect to dashboard
      router.push('/')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Registration failed'
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }))
      throw error
    }
  }

  /**
   * Logout user
   */
  const logout = (): void => {
    authService.logout()
    setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    })
    router.push('/login')
  }

  /**
   * Refresh user data
   */
  const refreshUser = async (): Promise<void> => {
    try {
      const user = await authService.getCurrentUser()
      setState(prev => ({ ...prev, user }))
    } catch (error) {
      // If refresh fails, log out
      logout()
    }
  }

  /**
   * Clear error
   */
  const clearError = (): void => {
    setState(prev => ({ ...prev, error: null }))
  }

  const value: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    refreshUser,
    clearError,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

/**
 * Hook to use auth context
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
