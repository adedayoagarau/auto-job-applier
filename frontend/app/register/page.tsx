"use client"

/**
 * Register Page
 */

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/contexts/auth.context'
import { RegisterForm } from '@/components/auth/register-form'

export default function RegisterPage() {
  const router = useRouter()
  const { isAuthenticated, isLoading } = useAuth()

  // Redirect to dashboard if already authenticated
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push('/')
    }
  }, [isAuthenticated, isLoading, router])

  // Show loading while checking authentication
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent motion-reduce:animate-[spin_1.5s_linear_infinite]" />
          <p className="mt-4 text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  // Don't render register form if already authenticated
  if (isAuthenticated) {
    return null
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold tracking-tight">AutoJobApplier</h1>
          <p className="mt-2 text-muted-foreground">
            Create an account to start automating your job applications
          </p>
        </div>
        <RegisterForm />
      </div>
    </div>
  )
}
