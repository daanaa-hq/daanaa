import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { CheckCircle, XCircle, Edit2, AlertCircle, Activity, Zap, CheckCheck, Brain, Mail, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { LearningDashboard } from './LearningDashboard'
import { EmailAutomationDashboard } from './EmailAutomationDashboard'
import { SocialManagerDashboard } from './SocialManagerDashboard'

interface LinkItem {
  ein: number
  org_name: string
  website?: string
  donate_url: string
  donate_button_text?: string
  volunteer_url: string
  status: 'pending' | 'approved' | 'rejected'
}

interface Stats {
  pending: number
  approved: number
  rejected: number
  total: number
}

interface DiscoveryStatus {
  status: string
  daemon: { running: boolean; timestamp: string }
  queue: { waiting: number; total_all_time: number; deployed_24h: number }
  deployment: { next_window: string; schedule: string }
}

export default function DashboardHub() {
  const [activeTab, setActiveTab] = useState('verification')

  // Verification state
  const [verificationItems, setVerificationItems] = useState<LinkItem[]>([])
  const [underReviewItems, setUnderReviewItems] = useState<LinkItem[]>([])
  const [verificationStats, setVerificationStats] = useState<Stats>({ pending: 0, approved: 0, rejected: 0, total: 0 })
  const [editingEin, setEditingEin] = useState<number | null>(null)
  const [editValues, setEditValues] = useState<{ donate: string; volunteer: string }>({ donate: '', volunteer: '' })
  const [loading, setLoading] = useState(false)

  // Discovery state
  const [discoveryStatus, setDiscoveryStatus] = useState<DiscoveryStatus | null>(null)
  const [healthStatus, setHealthStatus] = useState<any>(null)

  useEffect(() => {
    const interval = setInterval(() => {
      if (activeTab === 'verification') {
        fetchVerification()
      } else if (activeTab === 'discovery') {
        fetchDiscovery()
      } else if (activeTab === 'health') {
        fetchHealth()
      }
    }, 5000)

    // Initial fetch
    if (activeTab === 'verification') {
      fetchVerification()
    } else if (activeTab === 'discovery') {
      fetchDiscovery()
    } else if (activeTab === 'health') {
      fetchHealth()
    }

    return () => clearInterval(interval)
  }, [activeTab])

  // ============ VERIFICATION ============
  const fetchVerification = async () => {
    try {
      const [pending, underReview, stats] = await Promise.all([
        fetch('/api/verification/pending?limit=20').then(r => r.json()),
        fetch('/api/verification/under-review?limit=20').then(r => r.json()),
        fetch('/api/verification/stats').then(r => r.json())
      ])
      setVerificationItems(pending.items || [])
      setUnderReviewItems(underReview.items || [])
      setVerificationStats(stats)
    } catch (error) {
      console.error('Failed to fetch verification:', error)
    }
  }

  const handleApprove = async (ein: number) => {
    setLoading(true)
    try {
      await fetch('/api/verification/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ein, verified_by: 'akbar' })
      })
      await fetchVerification()
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = async (ein: number) => {
    setLoading(true)
    try {
      await fetch('/api/verification/edit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ein,
          donate_url: editValues.donate,
          volunteer_url: editValues.volunteer
        })
      })
      setEditingEin(null)
      await fetchVerification()
    } finally {
      setLoading(false)
    }
  }

  const handleReject = async (ein: number) => {
    setLoading(true)
    try {
      await fetch('/api/verification/reject', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ein, reason: 'Rejected by user' })
      })
      await fetchVerification()
    } finally {
      setLoading(false)
    }
  }

  const startEdit = (item: LinkItem) => {
    setEditingEin(item.ein)
    setEditValues({ donate: item.donate_url, volunteer: item.volunteer_url })
  }

  // ============ DISCOVERY ============
  const fetchDiscovery = async () => {
    try {
      const response = await fetch('/api/discovery/status')
      setDiscoveryStatus(await response.json())
    } catch (error) {
      console.error('Failed to fetch discovery status:', error)
    }
  }

  // ============ HEALTH ============
  const fetchHealth = async () => {
    try {
      const response = await fetch('/api/discovery/status')
      const data = await response.json()
      setHealthStatus(data)
    } catch (error) {
      console.error('Failed to fetch health:', error)
    }
  }

  return (
    <div className="w-full min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">

        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold">Discovery Control Center</h1>
          <p className="text-gray-600 mt-2">Verify links, monitor daemon, check health — all in one place</p>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-8">
            <TabsTrigger value="verification" className="gap-1">
              <CheckCheck size={14} /> Verify
            </TabsTrigger>
            <TabsTrigger value="discovery" className="gap-1">
              <Activity size={14} /> Discovery
            </TabsTrigger>
            <TabsTrigger value="social" className="gap-1">
              📱 Social
            </TabsTrigger>
            <TabsTrigger value="recommendations" className="gap-1">
              💡 Recommend
            </TabsTrigger>
            <TabsTrigger value="manager" className="gap-1">
              <Sparkles size={14} /> Manager
            </TabsTrigger>
            <TabsTrigger value="learning" className="gap-1">
              <Brain size={14} /> Learning
            </TabsTrigger>
            <TabsTrigger value="email" className="gap-1">
              <Mail size={14} /> Email
            </TabsTrigger>
            <TabsTrigger value="health" className="gap-1">
              <Zap size={14} /> Health
            </TabsTrigger>
          </TabsList>

          {/* ========== VERIFICATION TAB ========== */}
          <TabsContent value="verification" className="space-y-6">
            {/* Stats */}
            <div className="grid grid-cols-4 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-gray-600">Pending</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-yellow-600">{verificationStats.pending}</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-gray-600">Approved</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-green-600">{verificationStats.approved}</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-gray-600">Rejected</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-red-600">{verificationStats.rejected}</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-gray-600">Total</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold">{verificationStats.total}</p>
                </CardContent>
              </Card>
            </div>

            {/* Items */}
            <div className="space-y-4">
              {verificationItems.length === 0 ? (
                <Card>
                  <CardContent className="pt-6 text-center">
                    <p className="text-success-green font-medium">All links verified</p>
                  </CardContent>
                </Card>
              ) : (
                verificationItems.map((item) => (
                  <Card key={item.ein} className="border-l-4 border-l-yellow-500">
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div>
                          <CardTitle>{item.org_name}</CardTitle>
                          <CardDescription>EIN: {item.ein}</CardDescription>
                        </div>
                        <Badge variant="secondary">Pending</Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {editingEin === item.ein ? (
                        <div className="space-y-4 bg-gray-50 p-4 rounded">
                          <div>
                            <label className="text-sm font-medium">Donate Link</label>
                            <Input
                              value={editValues.donate}
                              onChange={(e) => setEditValues({ ...editValues, donate: e.target.value })}
                              className="mt-1"
                            />
                          </div>
                          <div>
                            <label className="text-sm font-medium">Volunteer Link</label>
                            <Input
                              value={editValues.volunteer}
                              onChange={(e) => setEditValues({ ...editValues, volunteer: e.target.value })}
                              className="mt-1"
                            />
                          </div>
                          <div className="flex gap-2">
                            <Button
                              onClick={() => handleEdit(item.ein)}
                              disabled={loading}
                              className="bg-green-600 hover:bg-green-700"
                            >
                              Save & Approve
                            </Button>
                            <Button onClick={() => setEditingEin(null)} variant="outline">
                              Cancel
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          <div className="bg-blue-50 border border-blue-200 p-3 rounded">
                            <p className="text-xs text-blue-700 font-medium">🌐 MAIN WEBSITE</p>
                            {item.website ? (
                              <a href={item.website} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600 break-all mt-1 hover:underline">
                                {item.website}
                              </a>
                            ) : (
                              <p className="text-sm text-gray-400 mt-1">(not found)</p>
                            )}
                          </div>
                          <div className="bg-green-50 border border-green-200 p-3 rounded">
                            <p className="text-xs text-green-700 font-medium">💚 DONATE LINK</p>
                            {item.donate_url ? (
                              <>
                                <a href={item.donate_url} target="_blank" rel="noopener noreferrer" className="text-sm text-green-600 break-all mt-1 hover:underline">
                                  {item.donate_url}
                                </a>
                                {item.donate_button_text && (
                                  <p className="text-xs text-green-600 mt-1">Button: "{item.donate_button_text}"</p>
                                )}
                              </>
                            ) : (
                              <p className="text-sm text-gray-400 mt-1">(not found)</p>
                            )}
                          </div>
                          <div className="bg-purple-50 border border-purple-200 p-3 rounded">
                            <p className="text-xs text-purple-700 font-medium">🤝 VOLUNTEER LINK</p>
                            {item.volunteer_url ? (
                              <a href={item.volunteer_url} target="_blank" rel="noopener noreferrer" className="text-sm text-purple-600 break-all mt-1 hover:underline">
                                {item.volunteer_url}
                              </a>
                            ) : (
                              <p className="text-sm text-gray-400 mt-1">(not found)</p>
                            )}
                          </div>
                          <div className="flex gap-2 pt-2">
                            <Button
                              onClick={() => handleApprove(item.ein)}
                              disabled={loading}
                              className="bg-green-600 hover:bg-green-700 gap-2 flex-1"
                            >
                              <CheckCircle size={16} /> Approve
                            </Button>
                            <Button onClick={() => startEdit(item)} variant="outline" className="gap-2 flex-1">
                              <Edit2 size={16} /> Edit
                            </Button>
                            <Button
                              onClick={() => handleReject(item.ein)}
                              disabled={loading}
                              variant="outline"
                              className="text-red-600 hover:text-red-700 flex-1"
                            >
                              <XCircle size={16} /> Reject
                            </Button>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))
              )}
            </div>

            {/* Under Review Section */}
            {underReviewItems.length > 0 && (
              <div className="space-y-4 border-t pt-6">
                <h3 className="text-lg font-semibold text-gray-700">
                  Under Review ({underReviewItems.length})
                </h3>
                <p className="text-sm text-gray-600">
                  These links scored below 90% confidence. Review manually before approval.
                </p>
                <div className="space-y-3">
                  {underReviewItems.map((item) => (
                    <Card key={item.ein} className="border-l-4 border-l-orange-400 bg-orange-50">
                      <CardHeader>
                        <div className="flex justify-between items-start">
                          <div>
                            <CardTitle className="text-base">{item.org_name}</CardTitle>
                            <CardDescription>EIN: {item.ein}</CardDescription>
                          </div>
                          <Badge variant="secondary" className="bg-orange-200 text-orange-800">Under Review</Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        {item.donate_url && (
                          <div className="text-sm">
                            <p className="font-medium text-gray-700">Donate:</p>
                            <a href={item.donate_url} target="_blank" rel="noopener noreferrer" className="text-orange-600 hover:underline break-all">
                              {item.donate_url}
                            </a>
                          </div>
                        )}
                        {item.volunteer_url && (
                          <div className="text-sm">
                            <p className="font-medium text-gray-700">Volunteer:</p>
                            <a href={item.volunteer_url} target="_blank" rel="noopener noreferrer" className="text-orange-600 hover:underline break-all">
                              {item.volunteer_url}
                            </a>
                          </div>
                        )}
                        <div className="flex gap-2 pt-2">
                          <Button
                            onClick={() => handleApprove(item.ein)}
                            disabled={loading}
                            className="bg-green-600 hover:bg-green-700 text-xs flex-1"
                          >
                            Approve Anyway
                          </Button>
                          <Button
                            onClick={() => handleReject(item.ein)}
                            disabled={loading}
                            variant="outline"
                            className="text-xs flex-1"
                          >
                            Reject
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </TabsContent>

          {/* ========== DISCOVERY TAB ========== */}
          <TabsContent value="discovery" className="space-y-6">
            {discoveryStatus ? (
              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Daemon Status</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-3">
                      <div className={`w-3 h-3 rounded-full ${discoveryStatus.daemon.running ? 'bg-green-500' : 'bg-red-500'}`}></div>
                      <span className="text-lg font-medium">
                        {discoveryStatus.daemon.running ? '🟢 Running' : '🔴 Stopped'}
                      </span>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Queue Depth</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-2xl font-bold">{discoveryStatus.queue.waiting}</p>
                    <p className="text-sm text-gray-600">links waiting for deployment</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Deployed (24h)</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-2xl font-bold">{discoveryStatus.queue.deployed_24h}</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Next Deployment</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm font-mono">{new Date(discoveryStatus.deployment.next_window).toLocaleTimeString()}</p>
                    <p className="text-xs text-gray-600 mt-1">{discoveryStatus.deployment.schedule}</p>
                  </CardContent>
                </Card>
              </div>
            ) : (
              <Card>
                <CardContent className="pt-6">Loading...</CardContent>
              </Card>
            )}
          </TabsContent>

          {/* ========== SOCIAL TAB ========== */}
          <TabsContent value="social" className="space-y-6">
            <Card className="border-0 shadow-sm bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900">
              <CardHeader>
                <CardTitle>LinkedIn Performance</CardTitle>
                <CardDescription>Real-time metrics from posted carousels</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <p className="text-gray-600 dark:text-gray-400">📱 Social Media dashboard embedded</p>
                  <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">Carousel metrics, engagement themes, sentiment analysis</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ========== RECOMMENDATIONS TAB ========== */}
          <TabsContent value="recommendations" className="space-y-6">
            <Card className="border-0 shadow-sm bg-gradient-to-br from-amber-50 to-orange-100 dark:from-amber-950 dark:to-orange-900">
              <CardHeader>
                <CardTitle>AI Recommendations</CardTitle>
                <CardDescription>Next carousel topics + auto-trigger suggestions</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 rounded-lg bg-white dark:bg-slate-800 border-l-4 border-l-amber-500">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-semibold">The Funding Paradox</h3>
                      <span className="text-2xl font-bold text-amber-600">94%</span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">High engagement on financial health content (11.4% rate)</p>
                    <button className="px-3 py-1 bg-amber-600 text-white rounded text-sm">Approve & Auto-Post</button>
                  </div>

                  <div className="p-4 rounded-lg bg-white dark:bg-slate-800 border-l-4 border-l-green-500">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-semibold">Email: Nonprofit Nurture</h3>
                      <span className="text-2xl font-bold text-green-600">87%</span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">Auto-trigger when nonprofit engages with carousel</p>
                    <button className="px-3 py-1 bg-green-600 text-white rounded text-sm">Enable Auto-Trigger</button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ========== SOCIAL MANAGER TAB ========== */}
          <TabsContent value="manager" className="space-y-6">
            <SocialManagerDashboard />
          </TabsContent>

          {/* ========== EMAIL TAB ========== */}
          <TabsContent value="email" className="space-y-6">
            <EmailAutomationDashboard />
          </TabsContent>

          {/* ========== LEARNING TAB ========== */}
          <TabsContent value="learning" className="space-y-6">
            <LearningDashboard />
          </TabsContent>

          {/* ========== HEALTH TAB ========== */}
          <TabsContent value="health" className="space-y-6">
            {healthStatus ? (
              <div className="space-y-4">
                <Alert className={healthStatus.status === 'healthy' ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'}>
                  <AlertCircle className={healthStatus.status === 'healthy' ? 'text-green-600' : 'text-yellow-600'} />
                  <AlertDescription className={healthStatus.status === 'healthy' ? 'text-green-800' : 'text-yellow-800'}>
                    System Status: <strong>{healthStatus.status.toUpperCase()}</strong>
                  </AlertDescription>
                </Alert>

                <Card>
                  <CardHeader>
                    <CardTitle>Daemon</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Status:</span>
                      <Badge className={healthStatus.daemon.running ? 'bg-green-600' : 'bg-red-600'}>
                        {healthStatus.daemon.running ? 'Running' : 'Stopped'}
                      </Badge>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Last check:</span>
                      <span>{new Date(healthStatus.daemon.timestamp).toLocaleTimeString()}</span>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Queue Stats</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex justify-between">
                      <span>Waiting:</span>
                      <strong>{healthStatus.queue.waiting}</strong>
                    </div>
                    <div className="flex justify-between">
                      <span>Deployed (24h):</span>
                      <strong>{healthStatus.queue.deployed_24h}</strong>
                    </div>
                    <div className="flex justify-between">
                      <span>Total all-time:</span>
                      <strong>{healthStatus.queue.total_all_time}</strong>
                    </div>
                  </CardContent>
                </Card>
              </div>
            ) : (
              <Card>
                <CardContent className="pt-6">Loading...</CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>

        {/* Footer */}
        <div className="text-center text-sm text-gray-500 py-4">
          <p>⚡ Dashboards auto-refresh every 5 seconds</p>
        </div>
      </div>
    </div>
  )
}
