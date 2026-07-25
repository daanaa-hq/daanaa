import { useEffect, useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { AlertCircle, CheckCircle2, XCircle, Clock, Users, TrendingUp, RefreshCw } from 'lucide-react'

interface SubmissionQueue {
  id: string
  volunteer_name: string
  volunteer_email: string
  hours: number
  service_date: string
  status: 'pending' | 'approved' | 'rejected'
  submitted_at: string
  rejection_reason?: string
}

interface DashboardStats {
  total_volunteers: number
  pending_submissions: number
  approved_this_month: number
  total_hours_donated: number
  community_value: number
  volunteer_retention: number
}

interface ActionModalState {
  open: boolean
  type: 'approve' | 'reject' | null
  submission: SubmissionQueue | null
  reason: string
}

export default function NonprofitDashboardV2() {
  const { ein } = useParams<{ ein: string }>()
  const { user, getIdToken } = useAuth()

  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [submissions, setSubmissions] = useState<SubmissionQueue[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('pending')
  const [actionModal, setActionModal] = useState<ActionModalState>({
    open: false,
    type: null,
    submission: null,
    reason: '',
  })

  // Fetch dashboard data
  const fetchDashboard = useCallback(async () => {
    if (!ein || !user) return

    const token = await getIdToken()
    if (!token) return

    try {
      const [statsRes, listRes] = await Promise.all([
        fetch(`/api/nonprofit/${ein}/dashboard/overview`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`/api/nonprofit/${ein}/volunteer/list?status=all`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ])

      if (statsRes.ok) {
        const data = await statsRes.json()
        setStats(data.data || data)
      }

      if (listRes.ok) {
        const data = await listRes.json()
        setSubmissions(data.data || data.submissions || [])
      }
    } catch (error) {
      console.error('Dashboard fetch failed:', error)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [ein, user, getIdToken])

  // Initial load + auto-refresh every 30 seconds
  useEffect(() => {
    fetchDashboard()
    const interval = setInterval(fetchDashboard, 30000)
    return () => clearInterval(interval)
  }, [fetchDashboard])

  const handleApprove = async (submission: SubmissionQueue) => {
    setActionModal({
      open: true,
      type: 'approve',
      submission,
      reason: '',
    })
  }

  const handleReject = async (submission: SubmissionQueue) => {
    setActionModal({
      open: true,
      type: 'reject',
      submission,
      reason: '',
    })
  }

  const submitAction = async () => {
    if (!actionModal.submission || !user) return

    const token = await getIdToken()
    if (!token) return

    try {
      const endpoint =
        actionModal.type === 'approve'
          ? `/api/nonprofit/${ein}/volunteer/${actionModal.submission.id}/approve`
          : `/api/nonprofit/${ein}/volunteer/${actionModal.submission.id}/reject`

      const body = actionModal.type === 'reject' ? { reason: actionModal.reason } : {}

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: actionModal.type === 'reject' ? JSON.stringify(body) : undefined,
      })

      if (res.ok) {
        // Optimistic update
        setSubmissions((prev) =>
          prev.map((s) =>
            s.id === actionModal.submission?.id
              ? {
                  ...s,
                  status: actionModal.type === 'approve' ? 'approved' : 'rejected',
                  rejection_reason: actionModal.reason,
                }
              : s
          )
        )
        setActionModal({ open: false, type: null, submission: null, reason: '' })
        // Refetch to get updated stats
        setTimeout(fetchDashboard, 500)
      }
    } catch (error) {
      console.error('Action failed:', error)
    }
  }

  const filteredSubmissions = submissions.filter((s) => {
    if (filter === 'all') return true
    return s.status === filter
  })

  const pendingCount = submissions.filter((s) => s.status === 'pending').length
  const approvedCount = submissions.filter((s) => s.status === 'approved').length

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 rounded-full border-4 border-soft-gold border-t-transparent animate-spin mx-auto mb-4" />
          <p className="text-slate-600">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-slate-900 mb-2">Volunteer Command Center</h1>
            <p className="text-slate-600">Manage submissions, approve hours, track impact</p>
          </div>
          <button
            onClick={() => {
              setRefreshing(true)
              fetchDashboard()
            }}
            disabled={refreshing}
            className="p-3 bg-white rounded-lg border border-slate-200 hover:border-soft-gold text-slate-600 hover:text-soft-gold transition disabled:opacity-50"
          >
            <RefreshCw size={20} className={refreshing ? 'animate-spin' : ''} />
          </button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {/* Pending Submissions */}
          <div className="bg-white rounded-lg border border-slate-200 p-6 hover:shadow-lg transition">
            <div className="flex items-center justify-between mb-3">
              <Clock size={24} className="text-amber-500" />
              <span className="text-sm font-semibold text-amber-600 bg-alert-amber/5 px-2 py-1 rounded">
                Action Needed
              </span>
            </div>
            <p className="text-slate-600 text-sm mb-1">Pending Review</p>
            <p className="text-4xl font-bold text-slate-900">{pendingCount}</p>
            <p className="text-xs text-slate-500 mt-2">submissions awaiting approval</p>
          </div>

          {/* Approved This Month */}
          <div className="bg-white rounded-lg border border-slate-200 p-6 hover:shadow-lg transition">
            <div className="flex items-center justify-between mb-3">
              <CheckCircle2 size={24} className="text-emerald-500" />
              <span className="text-sm font-semibold text-emerald-600 bg-emerald-50 px-2 py-1 rounded">
                This Month
              </span>
            </div>
            <p className="text-slate-600 text-sm mb-1">Approved</p>
            <p className="text-4xl font-bold text-slate-900">{approvedCount}</p>
            <p className="text-xs text-slate-500 mt-2">hours approved and counted</p>
          </div>

          {/* Community Value */}
          <div className="bg-white rounded-lg border border-slate-200 p-6 hover:shadow-lg transition">
            <div className="flex items-center justify-between mb-3">
              <TrendingUp size={24} className="text-blue-500" />
              <span className="text-sm font-semibold text-blue-600 bg-blue-50 px-2 py-1 rounded">
                Impact
              </span>
            </div>
            <p className="text-slate-600 text-sm mb-1">Community Value</p>
            <p className="text-4xl font-bold text-slate-900">
              ${(stats?.community_value || 0).toLocaleString('en-US', { maximumFractionDigits: 0 })}
            </p>
            <p className="text-xs text-slate-500 mt-2">estimated volunteer labor value</p>
          </div>

          {/* Total Volunteers */}
          <div className="bg-white rounded-lg border border-slate-200 p-6 hover:shadow-lg transition">
            <div className="flex items-center justify-between mb-3">
              <Users size={24} className="text-purple-500" />
              <span className="text-sm font-semibold text-purple-600 bg-purple-50 px-2 py-1 rounded">
                Community
              </span>
            </div>
            <p className="text-slate-600 text-sm mb-1">Volunteers Served</p>
            <p className="text-4xl font-bold text-slate-900">{stats?.total_volunteers || 0}</p>
            <p className="text-xs text-slate-500 mt-2">unique contributors this year</p>
          </div>
        </div>

        {/* Submissions Queue */}
        <div className="bg-white rounded-lg border border-slate-200">
          {/* Filters */}
          <div className="border-b border-slate-200 p-6 flex gap-2 flex-wrap">
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                filter === 'all'
                  ? 'bg-soft-gold text-white'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              All ({submissions.length})
            </button>
            <button
              onClick={() => setFilter('pending')}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                filter === 'pending'
                  ? 'bg-alert-amber/50 text-white'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              Pending ({pendingCount})
            </button>
            <button
              onClick={() => setFilter('approved')}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                filter === 'approved'
                  ? 'bg-emerald-500 text-white'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              Approved ({approvedCount})
            </button>
            <button
              onClick={() => setFilter('rejected')}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                filter === 'rejected'
                  ? 'bg-destructive/50 text-white'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              Rejected
            </button>
          </div>

          {/* Submissions List */}
          <div className="divide-y divide-slate-200">
            {filteredSubmissions.length === 0 ? (
              <div className="p-12 text-center">
                <AlertCircle size={48} className="mx-auto text-slate-300 mb-4" />
                <p className="text-slate-600 text-lg font-medium">No submissions to show</p>
                <p className="text-slate-500 text-sm">Great job! All submissions have been reviewed.</p>
              </div>
            ) : (
              filteredSubmissions.map((submission) => (
                <div
                  key={submission.id}
                  className="p-6 hover:bg-slate-50 transition flex items-start justify-between gap-6"
                >
                  {/* Submission Details */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-slate-900 truncate">
                        {submission.volunteer_name}
                      </h3>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap ${
                          submission.status === 'pending'
                            ? 'bg-amber-100 text-amber-800'
                            : submission.status === 'approved'
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {submission.status === 'pending'
                          ? '⏳ Awaiting Review'
                          : submission.status === 'approved'
                            ? '✓ Approved'
                            : '✕ Rejected'}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-slate-500 text-xs font-medium mb-1">HOURS</p>
                        <p className="text-2xl font-bold text-slate-900">{submission.hours}</p>
                      </div>
                      <div>
                        <p className="text-slate-500 text-xs font-medium mb-1">SERVICE DATE</p>
                        <p className="text-slate-900 font-medium">
                          {new Date(submission.service_date).toLocaleDateString()}
                        </p>
                      </div>
                      <div>
                        <p className="text-slate-500 text-xs font-medium mb-1">SUBMITTED</p>
                        <p className="text-slate-900 font-medium">
                          {new Date(submission.submitted_at).toLocaleDateString()}
                        </p>
                      </div>
                      {submission.rejection_reason && (
                        <div>
                          <p className="text-slate-500 text-xs font-medium mb-1">REASON</p>
                          <p className="text-red-900 font-medium text-sm truncate">
                            {submission.rejection_reason}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Action Buttons */}
                  {submission.status === 'pending' && (
                    <div className="flex gap-3 ml-auto">
                      <button
                        onClick={() => handleApprove(submission)}
                        className="px-4 py-2 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition font-medium text-sm whitespace-nowrap"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => handleReject(submission)}
                        className="px-4 py-2 bg-destructive/50 text-white rounded-lg hover:bg-red-600 transition font-medium text-sm whitespace-nowrap"
                      >
                        Reject
                      </button>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Action Modal */}
      {actionModal.open && actionModal.submission && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-xl font-bold text-slate-900">
                {actionModal.type === 'approve' ? 'Approve Hours' : 'Reject Submission'}
              </h2>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <p className="text-sm text-slate-600 mb-1">Volunteer</p>
                <p className="font-medium text-slate-900">{actionModal.submission.volunteer_name}</p>
              </div>
              <div>
                <p className="text-sm text-slate-600 mb-1">Hours</p>
                <p className="font-medium text-slate-900">{actionModal.submission.hours}</p>
              </div>

              {actionModal.type === 'reject' && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Reason for Rejection (optional)
                  </label>
                  <textarea
                    value={actionModal.reason}
                    onChange={(e) =>
                      setActionModal((prev) => ({ ...prev, reason: e.target.value }))
                    }
                    placeholder="e.g., Hours do not match event duration..."
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
                    rows={3}
                  />
                </div>
              )}
            </div>

            <div className="p-6 border-t border-slate-200 flex gap-3">
              <button
                onClick={() =>
                  setActionModal({ open: false, type: null, submission: null, reason: '' })
                }
                className="flex-1 px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition font-medium"
              >
                Cancel
              </button>
              <button
                onClick={submitAction}
                className={`flex-1 px-4 py-2 text-white rounded-lg transition font-medium ${
                  actionModal.type === 'approve'
                    ? 'bg-emerald-500 hover:bg-emerald-600'
                    : 'bg-destructive/50 hover:bg-red-600'
                }`}
              >
                {actionModal.type === 'approve' ? 'Approve' : 'Reject'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
