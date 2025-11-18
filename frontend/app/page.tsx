"use client"

import * as React from "react"
import { useState, useEffect } from "react"
import {
  LayoutDashboard,
  Search,
  FileText,
  Settings,
  Play,
  Square,
  Download,
  Upload,
  Filter,
  X
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ThemeToggle } from "@/components/theme-toggle"
import { ProtectedRoute } from "@/components/auth/protected-route"
import { UserNav } from "@/components/auth/user-nav"
import { useAuth } from "@/lib/contexts/auth.context"
import { authService } from "@/lib/services/auth.service"
import { LoadingSpinner, LoadingOverlay } from "@/components/ui/loading-spinner"
import { ApplicationListSkeleton } from "@/components/ui/application-skeleton"
import { Application, Statistics, Config, ActivityLogEntry, WebSocketMessage } from "@/lib/types/api"
import { Users } from "lucide-react"
import { useRouter } from 'next/navigation'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

function DashboardContent() {
  const router = useRouter()
  const { user } = useAuth()
  const [currentView, setCurrentView] = useState<"dashboard" | "search" | "applications" | "config">("dashboard")
  const [stats, setStats] = useState<Statistics>({
    total_applications: 0,
    applications_today: 0,
    success_rate: 0,
    average_match_score: 0
  })
  const [activityLog, setActivityLog] = useState<ActivityLogEntry[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [applications, setApplications] = useState<Application[]>([])
  const [config, setConfig] = useState<Config | null>(null)
  const [ws, setWs] = useState<WebSocket | null>(null)
  const reconnectTimeoutRef = React.useRef<NodeJS.Timeout | null>(null)
  const [isLoadingStats, setIsLoadingStats] = useState(true)
  const [isLoadingApps, setIsLoadingApps] = useState(true)
  const [isLoadingConfig, setIsLoadingConfig] = useState(true)

  // Application filters and search
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [platformFilter, setPlatformFilter] = useState<string>("all")

  // Filtered applications based on search and filters
  const filteredApplications = React.useMemo(() => {
    return applications.filter(app => {
      // Search filter
      const matchesSearch = searchQuery === "" ||
        app.job_title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        app.company.toLowerCase().includes(searchQuery.toLowerCase()) ||
        app.location?.toLowerCase().includes(searchQuery.toLowerCase())

      // Status filter
      const matchesStatus = statusFilter === "all" || app.status === statusFilter

      // Platform filter
      const matchesPlatform = platformFilter === "all" || app.platform === platformFilter

      return matchesSearch && matchesStatus && matchesPlatform
    })
  }, [applications, searchQuery, statusFilter, platformFilter])

  // Get unique platforms for filter dropdown
  const availablePlatforms = React.useMemo(() => {
    const platforms = new Set(applications.map(app => app.platform).filter(Boolean))
    return Array.from(platforms).sort()
  }, [applications])

  // Chart data - Applications by status
  const statusChartData = React.useMemo(() => {
    const statusCounts: Record<string, number> = {}
    applications.forEach(app => {
      statusCounts[app.status] = (statusCounts[app.status] || 0) + 1
    })
    return Object.entries(statusCounts).map(([status, count]) => ({
      name: status.charAt(0).toUpperCase() + status.slice(1),
      value: count
    }))
  }, [applications])

  // Chart data - Applications by platform
  const platformChartData = React.useMemo(() => {
    const platformCounts: Record<string, number> = {}
    applications.forEach(app => {
      if (app.platform) {
        platformCounts[app.platform] = (platformCounts[app.platform] || 0) + 1
      }
    })
    return Object.entries(platformCounts)
      .map(([platform, count]) => ({
        name: platform,
        applications: count
      }))
      .sort((a, b) => b.applications - a.applications)
      .slice(0, 8) // Top 8 platforms
  }, [applications])

  // Colors for pie chart
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D']

  // Load stats on mount
  useEffect(() => {
    loadStatistics()
    loadApplications()
    loadConfig()

    const websocket = setupWebSocket()

    return () => {
      // Clear any pending reconnection attempts
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      // Close the websocket
      if (websocket) {
        websocket.close()
      }
    }
  }, [])

  const setupWebSocket = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws`

    const websocket = new WebSocket(wsUrl)

    websocket.onopen = () => {
      console.log('WebSocket connected')
      addActivityLog("Connected to server", "success")
    }

    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data)
      handleWebSocketMessage(message)
    }

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    websocket.onclose = () => {
      console.log('WebSocket disconnected')
      addActivityLog("Disconnected from server", "warning")

      // Attempt to reconnect after 3 seconds (only if not manually closed)
      reconnectTimeoutRef.current = setTimeout(() => {
        const newWebsocket = setupWebSocket()
        setWs(newWebsocket)
      }, 3000)
    }

    setWs(websocket)
    return websocket
  }

  const handleWebSocketMessage = (message: WebSocketMessage) => {
    const { type, data } = message

    switch (type) {
      case 'search_started':
      case 'application_started':
        setIsProcessing(true)
        addActivityLog(data.message || 'Process started...', 'info')
        break
      case 'job_found':
        addActivityLog(`Found: ${data.job.title} at ${data.job.company}`, 'success')
        break
      case 'application_success':
        addActivityLog(`Applied successfully! Total today: ${data.applications_today}`, 'success')
        loadStatistics()
        loadApplications()
        break
      case 'search_completed':
      case 'application_completed':
        setIsProcessing(false)
        addActivityLog(data.message, 'success')
        loadStatistics()
        break
      case 'error':
        addActivityLog(`Error: ${data.message}`, 'error')
        setIsProcessing(false)
        break
      default:
        if (data.message) {
          addActivityLog(data.message, 'info')
        }
    }
  }

  const loadStatistics = async () => {
    try {
      setIsLoadingStats(true)
      const response = await authService.fetchWithAuth('/api/statistics')
      const data: Statistics = await response.json()
      setStats(data)
    } catch (error) {
      console.error('Failed to load statistics:', error)
    } finally {
      setIsLoadingStats(false)
    }
  }

  const loadApplications = async () => {
    try {
      setIsLoadingApps(true)
      const response = await authService.fetchWithAuth('/api/applications?limit=50')
      const data: Application[] = await response.json()
      // Ensure data is an array before setting
      setApplications(Array.isArray(data) ? data : [])
    } catch (error) {
      console.error('Failed to load applications:', error)
      setApplications([]) // Set to empty array on error
    } finally {
      setIsLoadingApps(false)
    }
  }

  const loadConfig = async () => {
    try {
      setIsLoadingConfig(true)
      const response = await authService.fetchWithAuth('/api/config')
      const data: Config = await response.json()
      setConfig(data)
    } catch (error) {
      console.error('Failed to load config:', error)
    } finally {
      setIsLoadingConfig(false)
    }
  }

  const addActivityLog = (message: string, type: 'info' | 'success' | 'warning' | 'error') => {
    const time = new Date().toLocaleTimeString()
    setActivityLog(prev => [{ time, message, type }, ...prev].slice(0, 50))
  }

  const startSearch = async () => {
    try {
      await authService.fetchWithAuth('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_titles: config?.job_titles || ["Software Engineer"],
          locations: config?.locations || ["Remote"],
          platforms: config?.platforms || ["indeed"]
        })
      })
      addActivityLog('Job search started...', 'info')
    } catch (error) {
      addActivityLog('Failed to start search', 'error')
    }
  }

  const startApply = async () => {
    try {
      await authService.fetchWithAuth('/api/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          auto_submit: config?.auto_submit || false,
          max_applications: config?.max_applications_per_day || 20,
          application_delay: 30
        })
      })
      addActivityLog('Application process started...', 'info')
    } catch (error) {
      addActivityLog('Failed to start application process', 'error')
    }
  }

  const stopProcess = async () => {
    try {
      await authService.fetchWithAuth('/api/stop', { method: 'POST' })
      setIsProcessing(false)
      addActivityLog('Stop signal sent', 'warning')
    } catch (error) {
      addActivityLog('Failed to stop process', 'error')
    }
  }

  const exportData = () => {
    window.open('/api/export?format=csv', '_blank')
    addActivityLog('Exporting data...', 'info')
  }

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-64 border-r bg-card">
        <div className="flex h-full flex-col">
          <div className="flex h-16 items-center justify-between border-b px-6">
            <h1 className="text-xl font-bold">AutoJobApplier</h1>
            <UserNav />
          </div>
          <nav className="flex-1 space-y-1 p-4">
            <Button
              variant={currentView === "dashboard" ? "secondary" : "ghost"}
              className="w-full justify-start"
              onClick={() => setCurrentView("dashboard")}
            >
              <LayoutDashboard className="mr-2 h-4 w-4" />
              Dashboard
            </Button>
            <Button
              variant={currentView === "search" ? "secondary" : "ghost"}
              className="w-full justify-start"
              onClick={() => setCurrentView("search")}
            >
              <Search className="mr-2 h-4 w-4" />
              Job Search
            </Button>
            <Button
              variant={currentView === "applications" ? "secondary" : "ghost"}
              className="w-full justify-start"
              onClick={() => setCurrentView("applications")}
            >
              <FileText className="mr-2 h-4 w-4" />
              Applications
            </Button>
            <Button
              variant={currentView === "config" ? "secondary" : "ghost"}
              className="w-full justify-start"
              onClick={() => setCurrentView("config")}
            >
              <Settings className="mr-2 h-4 w-4" />
              Configuration
            </Button>
            {user?.is_admin && (
              <Button
                variant="ghost"
                className="w-full justify-start"
                onClick={() => router.push('/admin/users')}
              >
                <Users className="mr-2 h-4 w-4" />
                Admin Users
              </Button>
            )}
          </nav>
          <div className="border-t p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Theme</span>
              <ThemeToggle />
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="container mx-auto p-6 space-y-6">
          {/* Dashboard View */}
          {currentView === "dashboard" && (
            <>
              <div>
                <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
                <p className="text-muted-foreground">
                  AI-Powered Automated Job Application System
                </p>
              </div>

              {/* Stats Grid */}
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Total Applications
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{stats.total_applications}</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Today's Applications
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{stats.applications_today}</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Success Rate
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{stats.success_rate}%</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Avg. Match Score
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {stats.average_match_score ? stats.average_match_score.toFixed(1) : 0}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Charts */}
              {applications.length > 0 && (
                <div className="grid gap-4 md:grid-cols-2">
                  {/* Applications by Status - Pie Chart */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Applications by Status</CardTitle>
                      <CardDescription>Distribution of application statuses</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                          <Pie
                            data={statusChartData}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="value"
                          >
                            {statusChartData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  {/* Applications by Platform - Bar Chart */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Top Platforms</CardTitle>
                      <CardDescription>Applications per platform</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={platformChartData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis
                            dataKey="name"
                            angle={-45}
                            textAnchor="end"
                            height={80}
                            interval={0}
                          />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="applications" fill="#8884d8" />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-4">
                {!isProcessing ? (
                  <>
                    <Button onClick={startSearch}>
                      <Search className="mr-2 h-4 w-4" />
                      Search Jobs
                    </Button>
                    <Button onClick={startApply} variant="default">
                      <Play className="mr-2 h-4 w-4" />
                      Start Applying
                    </Button>
                    <Button onClick={exportData} variant="outline">
                      <Download className="mr-2 h-4 w-4" />
                      Export Data
                    </Button>
                  </>
                ) : (
                  <Button onClick={stopProcess} variant="destructive">
                    <Square className="mr-2 h-4 w-4" />
                    Stop Process
                  </Button>
                )}
              </div>

              {/* Activity Log */}
              <Card>
                <CardHeader>
                  <CardTitle>Activity Log</CardTitle>
                  <CardDescription>Real-time updates on job applications</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="max-h-96 space-y-2 overflow-y-auto">
                    {activityLog.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No activity yet</p>
                    ) : (
                      activityLog.map((log, idx) => (
                        <div key={idx} className="flex items-start gap-2 border-l-2 border-primary pl-3 py-1">
                          <span className="text-xs text-muted-foreground">{log.time}</span>
                          <span className="text-sm">{log.message}</span>
                        </div>
                      ))
                    )}
                  </div>
                </CardContent>
              </Card>
            </>
          )}

          {/* Applications View */}
          {currentView === "applications" && (
            <>
              <div>
                <h2 className="text-3xl font-bold tracking-tight">Applications</h2>
                <p className="text-muted-foreground">View and manage your job applications</p>
              </div>

              {/* Search and Filters */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Filter className="h-5 w-5" />
                    Search & Filters
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 md:grid-cols-3">
                    <div className="space-y-2">
                      <Label>Search</Label>
                      <div className="relative">
                        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                          placeholder="Search by title, company, or location..."
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          className="pl-8"
                        />
                        {searchQuery && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="absolute right-1 top-1 h-7 w-7 p-0"
                            onClick={() => setSearchQuery("")}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Status</Label>
                      <Select value={statusFilter} onValueChange={setStatusFilter}>
                        <SelectTrigger>
                          <SelectValue placeholder="All statuses" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All statuses</SelectItem>
                          <SelectItem value="pending">Pending</SelectItem>
                          <SelectItem value="applied">Applied</SelectItem>
                          <SelectItem value="interview">Interview</SelectItem>
                          <SelectItem value="offer">Offer</SelectItem>
                          <SelectItem value="rejected">Rejected</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label>Platform</Label>
                      <Select value={platformFilter} onValueChange={setPlatformFilter}>
                        <SelectTrigger>
                          <SelectValue placeholder="All platforms" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All platforms</SelectItem>
                          {availablePlatforms.map(platform => (
                            <SelectItem key={platform} value={platform}>
                              {platform}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {(searchQuery || statusFilter !== "all" || platformFilter !== "all") && (
                    <div className="mt-4 flex items-center gap-2">
                      <Badge variant="secondary">
                        {filteredApplications.length} of {applications.length} applications
                      </Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setSearchQuery("")
                          setStatusFilter("all")
                          setPlatformFilter("all")
                        }}
                      >
                        Clear filters
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Application History</CardTitle>
                  <CardDescription>
                    {filteredApplications.length === 0 && applications.length > 0
                      ? "No applications match your filters"
                      : "All your submitted applications"}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {isLoadingApps ? (
                    <ApplicationListSkeleton count={5} />
                  ) : (
                    <div className="space-y-4">
                      {!filteredApplications || filteredApplications.length === 0 ? (
                        <p className="text-sm text-muted-foreground">
                          {applications.length === 0 ? "No applications yet" : "No applications match your filters"}
                        </p>
                      ) : (
                        filteredApplications.map((app) => (
                          <div key={app.id} className="flex items-center justify-between border-b pb-4 last:border-0">
                            <div className="space-y-1">
                              <h4 className="text-sm font-semibold">{app.job_title}</h4>
                              <p className="text-sm text-muted-foreground">{app.company} • {app.location}</p>
                              <p className="text-xs text-muted-foreground">
                                Applied: {app.applied_at ? new Date(app.applied_at).toLocaleDateString() : 'N/A'}
                              </p>
                            </div>
                            <div className="flex items-center gap-2">
                              {app.match_score && (
                                <Badge variant="secondary">{app.match_score}/100</Badge>
                              )}
                              <Badge variant={
                                app.status === 'applied' ? 'default' :
                                app.status === 'interview' ? 'default' :
                                app.status === 'rejected' ? 'destructive' : 'secondary'
                              }>
                                {app.status}
                              </Badge>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          )}

          {/* Config View */}
          {currentView === "config" && config && (
            <>
              <div>
                <h2 className="text-3xl font-bold tracking-tight">Configuration</h2>
                <p className="text-muted-foreground">Manage your application settings</p>
              </div>

              <div className="grid gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Application Settings</CardTitle>
                    <CardDescription>Configure how the system applies to jobs</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label>Max Applications Per Day</Label>
                      <Input
                        type="number"
                        defaultValue={config.max_applications_per_day}
                        min="1"
                        max="100"
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Auto-submit Applications</Label>
                        <p className="text-sm text-muted-foreground">
                          Submit applications without manual approval
                        </p>
                      </div>
                      <Switch defaultChecked={config.auto_submit} />
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Headless Mode</Label>
                        <p className="text-sm text-muted-foreground">
                          Run browser invisibly in the background
                        </p>
                      </div>
                      <Switch defaultChecked={config.headless} />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Personal Information</CardTitle>
                    <CardDescription>Your details for job applications</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label>Full Name</Label>
                      <Input defaultValue={config.personal_info?.name || ''} />
                    </div>
                    <div className="space-y-2">
                      <Label>Email</Label>
                      <Input type="email" defaultValue={config.personal_info?.email || ''} />
                    </div>
                    <div className="space-y-2">
                      <Label>Phone</Label>
                      <Input type="tel" defaultValue={config.personal_info?.phone || ''} />
                    </div>
                  </CardContent>
                </Card>

                <Button>Save Configuration</Button>
              </div>
            </>
          )}

          {/* Search View */}
          {currentView === "search" && (
            <>
              <div>
                <h2 className="text-3xl font-bold tracking-tight">Job Search</h2>
                <p className="text-muted-foreground">Find relevant job opportunities</p>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>Search Parameters</CardTitle>
                  <CardDescription>Configure your job search criteria</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Job Titles (comma-separated)</Label>
                    <Input placeholder="Software Engineer, Full Stack Developer" />
                  </div>
                  <div className="space-y-2">
                    <Label>Locations (comma-separated)</Label>
                    <Input placeholder="Remote, New York, San Francisco" />
                  </div>
                  <div className="space-y-2">
                    <Label>Include Keywords (optional)</Label>
                    <Input placeholder="Python, React, AWS" />
                  </div>
                  <div className="space-y-2">
                    <Label>Exclude Keywords (optional)</Label>
                    <Input placeholder="Senior, Manager" />
                  </div>
                  <Button onClick={startSearch}>
                    <Search className="mr-2 h-4 w-4" />
                    Search Jobs
                  </Button>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </main>
    </div>
  )
}

export default function Dashboard() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  )
}
