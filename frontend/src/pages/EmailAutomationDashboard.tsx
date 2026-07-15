import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { CheckCircle, XCircle, Mail, AlertCircle, TrendingUp } from 'lucide-react'

interface PendingEmail {
  id: number
  recipient_email: string
  subject: string
  confidence_score: number
  status: string
  created_at: string
}

interface EmailStats {
  trigger_stats: {
    total: number
    queued: number
    sent: number
    rejected: number
  }
  delivery_stats: {
    total_sent: number
    delivered: number
    bounced: number
    delivery_rate_pct: number
  }
  pending_approvals: number
}

export function EmailAutomationDashboard() {
  const [pending, setPending] = useState<PendingEmail[]>([])
  const [stats, setStats] = useState<EmailStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [approving, setApproving] = useState<number | null>(null)

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    try {
      const [pendingRes, statsRes] = await Promise.all([
        fetch('/api/email/pending'),
        fetch('/api/email/stats')
      ])

      if (pendingRes.ok) {
        const data = await pendingRes.json()
        setPending(data.all_pending || [])
      }
      if (statsRes.ok) {
        setStats(await statsRes.json())
      }
    } catch (error) {
      console.error('Failed to fetch email data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (emailId: number) => {
    setApproving(emailId)
    try {
      const res = await fetch(`/api/email/${emailId}/approve`, { method: 'POST' })
      if (res.ok) {
        setPending(pending.filter(e => e.id !== emailId))
        await fetchData() // Refresh stats
      }
    } catch (error) {
      console.error('Failed to approve email:', error)
    } finally {
      setApproving(null)
    }
  }

  const handleReject = async (emailId: number) => {
    try {
      const res = await fetch(`/api/email/${emailId}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: 'rejected_by_founder' })
      })
      if (res.ok) {
        setPending(pending.filter(e => e.id !== emailId))
        await fetchData() // Refresh stats
      }
    } catch (error) {
      console.error('Failed to reject email:', error)
    }
  }

  if (loading) {
    return (
      <div className="w-full max-w-6xl mx-auto p-6">
        <div className="text-center text-gray-500">Loading email dashboard...</div>
      </div>
    )
  }

  const highConfidence = pending.filter(e => e.confidence_score >= 0.75)
  const autoSendReady = pending.filter(e => e.confidence_score >= 0.9)

  return (
    <div className="w-full max-w-6xl mx-auto p-6 space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Email Automation Hub</h1>
        <p className="text-gray-600">Intelligent email triggers with safe governance — approve or auto-send</p>
      </div>

      {/* Safe Governance Alert */}
      <Alert className="border-blue-200 bg-blue-50 dark:bg-blue-950">
        <AlertCircle className="h-4 w-4 text-blue-600" />
        <AlertDescription className="text-blue-800 dark:text-blue-200 text-sm">
          ✓ Safe defaults: Auto-send emails with {'>'}90% confidence only. Medium confidence (70-90%) require your approval. Low confidence {'<'}70% are logged but not sent.
        </AlertDescription>
      </Alert>

      {/* Stats Grid */}
      {stats && (
        <div className="grid md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Total Triggers</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{stats.trigger_stats.total}</p>
              <p className="text-xs text-gray-500 mt-1">Last 30 days</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Sent</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-green-600">{stats.trigger_stats.sent}</p>
              <p className="text-xs text-gray-500 mt-1">{stats.delivery_stats.delivery_rate_pct}% delivered</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Rejected</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-amber-600">{stats.trigger_stats.rejected}</p>
              <p className="text-xs text-gray-500 mt-1">By founder review</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Pending</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-blue-600">{stats.pending_approvals}</p>
              <p className="text-xs text-gray-500 mt-1">Await your decision</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Auto-Send Ready Alert */}
      {autoSendReady.length > 0 && (
        <Card className="border-green-200 bg-green-50 dark:bg-green-950">
          <CardHeader>
            <CardTitle className="text-green-900 dark:text-green-100 flex items-center gap-2">
              <CheckCircle className="text-green-600" size={20} />
              Auto-Send Ready: {autoSendReady.length}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {autoSendReady.map(email => (
              <div key={email.id} className="flex justify-between items-center p-3 bg-white dark:bg-green-900 rounded border border-green-200 dark:border-green-800">
                <div className="flex-1">
                  <div className="font-semibold text-sm">{email.subject}</div>
                  <div className="text-xs text-gray-600 dark:text-gray-400">{email.recipient_email}</div>
                </div>
                <Badge className="bg-green-600">{(email.confidence_score * 100).toFixed(0)}%</Badge>
              </div>
            ))}
            <Button className="w-full bg-green-600 hover:bg-green-700">
              Send All Ready Emails ({autoSendReady.length})
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Pending Approval Emails */}
      {pending.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail size={20} className="text-blue-600" />
              {pending.length} Pending Your Decision
            </CardTitle>
            <CardDescription>Review and approve or reject each email</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {pending.map(email => (
              <div key={email.id} className={`p-4 rounded-lg border-l-4 ${
                email.confidence_score >= 0.75
                  ? 'border-l-green-500 bg-green-50 dark:bg-green-950'
                  : email.confidence_score >= 0.5
                  ? 'border-l-amber-500 bg-amber-50 dark:bg-amber-950'
                  : 'border-l-red-500 bg-red-50 dark:bg-red-950'
              }`}>
                <div className="space-y-3">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="font-semibold">{email.subject}</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        To: {email.recipient_email}
                      </div>
                    </div>
                    <Badge variant="outline" className="ml-2">
                      {(email.confidence_score * 100).toFixed(0)}% confident
                    </Badge>
                  </div>

                  {email.confidence_score >= 0.75 && (
                    <p className="text-xs text-gray-600 dark:text-gray-400">
                      ✓ High confidence — safe to send automatically
                    </p>
                  )}

                  <div className="flex gap-2">
                    <Button
                      onClick={() => handleApprove(email.id)}
                      disabled={approving === email.id}
                      className="bg-green-600 hover:bg-green-700 gap-2 flex-1"
                    >
                      <CheckCircle size={16} />
                      Approve & Send
                    </Button>
                    <Button
                      onClick={() => handleReject(email.id)}
                      variant="outline"
                      className="text-red-600 hover:text-red-700 flex-1"
                    >
                      <XCircle size={16} />
                      Reject
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {pending.length === 0 && (
        <Card>
          <CardContent className="pt-12 pb-12 text-center">
            <p className="text-gray-500">No emails pending approval</p>
            <p className="text-sm text-gray-400 mt-2">All high-confidence emails have been auto-sent</p>
          </CardContent>
        </Card>
      )}

      {/* Footer */}
      <div className="text-center text-sm text-gray-500">
        <p>⚡ Dashboard auto-refreshes every 30 seconds</p>
      </div>
    </div>
  )
}
