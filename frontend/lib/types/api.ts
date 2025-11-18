/**
 * API Response Types
 * Type definitions matching backend Pydantic models
 */

export interface Application {
  id: number
  job_title: string
  company: string
  location: string
  platform: string
  job_url: string
  status: 'pending' | 'applied' | 'rejected' | 'interview' | 'offer'
  match_score: number | null
  applied_at: string | null
  response_received: boolean
}

export interface Statistics {
  total_applications: number
  applications_today: number
  success_rate: number
  average_match_score: number
}

export interface Config {
  job_titles: string[]
  locations: string[]
  platforms: string[]
  keywords: string[]
  exclude_keywords: string[]
  max_applications_per_day: number
  auto_submit: boolean
  headless: boolean
  personal_info: Record<string, any>
}

export interface ActivityLogEntry {
  time: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
}

export interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
}

export interface JobSearchRequest {
  job_titles: string[]
  locations: string[]
  platforms: string[]
  keywords?: string[]
  exclude_keywords?: string[]
}

export interface ApplicationConfig {
  auto_submit: boolean
  max_applications: number
  application_delay: number
}

export interface Job {
  title: string
  company: string
  location: string
  platform: string
  job_url: string
  description: string
}
