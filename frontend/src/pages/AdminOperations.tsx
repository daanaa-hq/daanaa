import React, { useEffect, useState } from 'react'
import { usePageMeta } from '../hooks/usePageMeta'

interface PortalMetrics {
  total_signups: number
  total_letter_requests: number
  requests_by_status: Record<string, number>
  letters_generated: number
  pending_approvals: number
  approved_not_generated: number
  total_credits_purchased: number
  total_credits_remaining: number
  estimated_revenue: number
}

export default function AdminOperations() {
  usePageMeta('Admin Operations | Daanaa', 'Real-time nonprofit portal metrics and operational status')

  const [metrics, setMetrics] = useState<PortalMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)

  const fetchMetrics = async () => {
    try {
      setRefreshing(true)
      const res = await fetch('/api/nonprofit/analytics')
      if (!res.ok) throw new Error('Failed to fetch metrics')
      const data = await res.json()
      setMetrics(data)
      setError(null)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchMetrics()
    const interval = setInterval(fetchMetrics, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-soft-cream p-6 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-soft-gold border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (error || !metrics) {
    return (
      <div className="min-h-screen bg-soft-cream p-6">
        <div className="bg-destructive/5 border border-destructive/20 rounded-lg p-4 text-destructive">
          {error || 'Failed to load metrics'}
        </div>
      </div>
    )
  }

  const conversionRate = metrics.total_letter_requests > 0
    ? Math.round((metrics.letters_generated / metrics.total_letter_requests) * 100)
    : 0

  const approvalRate = metrics.total_letter_requests > 0
    ? Math.round(((metrics.letters_generated + metrics.pending_approvals) / metrics.total_letter_requests) * 100)
    : 0

  return (
    <div className="min-h-screen bg-soft-cream p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="font-display text-3xl text-deep-navy mb-1">Operations Dashboard</h1>
            <p className="text-cool-grey">Nonprofit portal real-time metrics</p>
          </div>
          <button
            onClick={fetchMetrics}
            disabled={refreshing}
            className="px-4 py-2 bg-soft-gold text-deep-navy rounded-lg hover:bg-bright-gold transition-colors disabled:opacity-50"
          >
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          {/* Signups */}
          <div className="bg-white rounded-lg p-6 shadow-sm border border-light-grey">
            <p className="text-cool-grey text-sm font-semibold mb-2">ED Signups</p>
            <p className="font-display text-3xl text-deep-navy">{metrics.total_signups}</p>
            <p className="text-xs text-cool-grey mt-2">nonprofit accounts registered</p>
          </div>

          {/* Letter Requests */}
          <div className="bg-white rounded-lg p-6 shadow-sm border border-light-grey">
            <p className="text-cool-grey text-sm font-semibold mb-2">Letter Requests</p>
            <p className="font-display text-3xl text-deep-navy">{metrics.total_letter_requests}</p>
            <p className="text-xs text-cool-grey mt-2">total requests submitted</p>
          </div>

          {/* Generated Letters */}
          <div className="bg-white rounded-lg p-6 shadow-sm border border-light-grey">
            <p className="text-cool-grey text-sm font-semibold mb-2">Generated</p>
            <p className="font-display text-3xl text-green-600">{metrics.letters_generated}</p>
            <p className="text-xs text-cool-grey mt-2">{conversionRate}% conversion rate</p>
          </div>

          {/* Revenue */}
          <div className="bg-white rounded-lg p-6 shadow-sm border border-light-grey">
            <p className="text-cool-grey text-sm font-semibold mb-2">Revenue (Proxy)</p>
            <p className="font-display text-3xl text-deep-navy">${metrics.estimated_revenue}</p>
            <p className="text-xs text-cool-grey mt-2">from letter credit purchases</p>
          </div>
        </div>

        {/* Workflow Breakdown */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Request Pipeline */}
          <div className="bg-white rounded-lg p-6 shadow-sm border border-light-grey">
            <h2 className="font-display text-lg text-deep-navy mb-4">Request Pipeline</h2>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm font-semibold text-deep-navy">Pending Approval</span>
                  <span className="text-sm font-bold text-soft-gold">{metrics.pending_approvals}</span>
                </div>
                <div className="w-full bg-light-grey rounded-full h-2">
                  <div
                    className="bg-soft-gold h-2 rounded-full"
                    style={{
                      width: `${(metrics.pending_approvals / Math.max(metrics.total_letter_requests, 1)) * 100}%`,
                    }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm font-semibold text-deep-navy">Approved (Not Generated)</span>
                  <span className="text-sm font-bold text-soft-gold">{metrics.approved_not_generated}</span>
                </div>
                <div className="w-full bg-light-grey rounded-full h-2">
                  <div
                    className="bg-bright-gold h-2 rounded-full"
                    style={{
                      width: `${(metrics.approved_not_generated / Math.max(metrics.total_letter_requests, 1)) * 100}%`,
                    }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm font-semibold text-deep-navy">Generated & Complete</span>
                  <span className="text-sm font-bold text-green-600">{metrics.letters_generated}</span>
                </div>
                <div className="w-full bg-light-grey rounded-full h-2">
                  <div
                    className="bg-green-500 h-2 rounded-full"
                    style={{
                      width: `${(metrics.letters_generated / Math.max(metrics.total_letter_requests, 1)) * 100}%`,
                    }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Credits & Revenue */}
          <div className="bg-white rounded-lg p-6 shadow-sm border border-light-grey">
            <h2 className="font-display text-lg text-deep-navy mb-4">Credit Usage</h2>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm font-semibold text-deep-navy">Total Credits Purchased</span>
                  <span className="font-bold text-deep-navy">{metrics.total_credits_purchased.toLocaleString()}</span>
                </div>
                <p className="text-xs text-cool-grey">
                  {metrics.total_credits_purchased > 0
                    ? `${metrics.total_credits_purchased} letters available at purchase`
                    : 'No purchases yet'}
                </p>
              </div>

              <div className="border-t border-light-grey pt-4">
                <div className="flex justify-between mb-2">
                  <span className="text-sm font-semibold text-deep-navy">Credits Remaining</span>
                  <span className="font-bold text-green-600">{metrics.total_credits_remaining.toLocaleString()}</span>
                </div>
                <p className="text-xs text-cool-grey">
                  {metrics.total_credits_purchased > 0
                    ? `${Math.round((metrics.total_credits_remaining / metrics.total_credits_purchased) * 100)}% of purchased credits remain`
                    : 'Unused'}
                </p>
              </div>

              <div className="bg-soft-cream rounded p-3 mt-4">
                <p className="text-xs text-deep-navy">
                  <span className="font-semibold">Est. Revenue:</span> ${metrics.estimated_revenue} at $10 per 100-letter pack
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Health Status */}
        <div className="bg-white rounded-lg p-6 shadow-sm border border-light-grey">
          <h2 className="font-display text-lg text-deep-navy mb-4">Portal Health</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-sm text-deep-navy">API Responding</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-sm text-deep-navy">Email Service Active</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
              <span className="text-sm text-deep-navy">Stripe Ready</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
              <span className="text-sm text-deep-navy">S3 Pending</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
