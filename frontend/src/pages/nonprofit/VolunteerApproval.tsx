import React, { useState, useEffect } from 'react'
import { usePageMeta } from '../../hooks/usePageMeta'

interface VolunteerRecord {
  id: string
  volunteer_name: string
  volunteer_email: string
  hours: number
  service_date: string
  activity_description: string
  status: 'pending' | 'verified' | 'rejected'
  submitted_at: string
}

export default function VolunteerApproval() {
  usePageMeta('Volunteer Hours Approval | Daanaa', 'Review and verify volunteer hours for your organization')

  const [records, setRecords] = useState<VolunteerRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<'all' | 'pending' | 'verified' | 'rejected'>('pending')
  const [approving, setApproving] = useState<string | null>(null)
  const [rejecting, setRejecting] = useState<string | null>(null)
  const [rejectionReason, setRejectionReason] = useState<Record<string, string>>({})

  useEffect(() => {
    fetchRecords()
  }, [filter])

  const fetchRecords = async () => {
    try {
      setLoading(true)
      const accountId = localStorage.getItem('nonprofit_account_id')
      const authToken = accountId || localStorage.getItem('nonprofit_auth_token')

      if (!authToken) {
        setError('Not authenticated. Please sign in.')
        return
      }

      // Mock data since API endpoint doesn't exist yet
      const mockRecords: VolunteerRecord[] = [
        {
          id: 'vol-1',
          volunteer_name: 'Sarah Johnson',
          volunteer_email: 'sarah@example.com',
          hours: 8,
          service_date: '2026-06-20',
          activity_description: 'Community outreach event at local park',
          status: 'pending',
          submitted_at: '2026-06-21T10:00:00Z',
        },
        {
          id: 'vol-2',
          volunteer_name: 'Michael Chen',
          volunteer_email: 'michael@example.com',
          hours: 4,
          service_date: '2026-06-19',
          activity_description: 'Data entry and database management',
          status: 'pending',
          submitted_at: '2026-06-21T09:30:00Z',
        },
        {
          id: 'vol-3',
          volunteer_name: 'Lisa Martinez',
          volunteer_email: 'lisa@example.com',
          hours: 6,
          service_date: '2026-06-18',
          activity_description: 'Fundraiser setup and coordination',
          status: 'verified',
          submitted_at: '2026-06-20T14:00:00Z',
        },
      ]

      const filtered = filter === 'all' ? mockRecords : mockRecords.filter(r => r.status === filter)
      setRecords(filtered)
      setError(null)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (recordId: string) => {
    setApproving(recordId)
    try {
      // Update local state (actual API call would go here)
      setRecords(prev =>
        prev.map(r => (r.id === recordId ? { ...r, status: 'verified' } : r))
      )
      setError(null)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setApproving(null)
    }
  }

  const handleReject = async (recordId: string) => {
    if (!rejectionReason[recordId]) {
      alert('Please provide a reason for rejection')
      return
    }

    setRejecting(recordId)
    try {
      // Update local state (actual API call would go here)
      setRecords(prev =>
        prev.map(r => (r.id === recordId ? { ...r, status: 'rejected' } : r))
      )
      setRejectionReason(prev => {
        const next = { ...prev }
        delete next[recordId]
        return next
      })
      setError(null)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setRejecting(null)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-soft-cream p-6 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-soft-gold border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  const pendingCount = records.filter(r => r.status === 'pending').length

  return (
    <div className="min-h-screen bg-soft-cream p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="font-display text-3xl text-deep-navy mb-2">Volunteer Hours Approval</h1>
          <p className="text-cool-grey">Review and verify volunteer contributions</p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-700">
            {error}
          </div>
        )}

        {/* Filter Tabs */}
        <div className="bg-white rounded-lg p-4 mb-6 border border-light-grey flex gap-4 flex-wrap">
          {(['all', 'pending', 'verified', 'rejected'] as const).map(status => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2 rounded-lg font-semibold text-sm transition-colors ${
                filter === status
                  ? 'bg-soft-gold text-deep-navy'
                  : 'bg-light-grey text-cool-grey hover:bg-light-grey/70'
              }`}
            >
              {status === 'all' ? 'All Submissions' : status === 'pending' ? `Pending (${pendingCount})` : status === 'verified' ? 'Verified' : 'Rejected'}
            </button>
          ))}
        </div>

        {/* Records List */}
        <div className="space-y-4">
          {records.length === 0 ? (
            <div className="bg-white rounded-lg p-8 text-center border border-light-grey">
              <p className="text-cool-grey">No volunteer submissions yet</p>
            </div>
          ) : (
            records.map(record => (
              <div key={record.id} className="bg-white rounded-lg p-6 border border-light-grey">
                <div className="mb-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-display text-lg text-deep-navy">{record.volunteer_name}</h3>
                      <p className="text-sm text-cool-grey">{record.volunteer_email}</p>
                    </div>
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        record.status === 'pending'
                          ? 'bg-yellow-100 text-yellow-800'
                          : record.status === 'verified'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {record.status.charAt(0).toUpperCase() + record.status.slice(1)}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-cool-grey">Hours</span>
                      <p className="font-bold text-deep-navy text-lg">{record.hours}h</p>
                    </div>
                    <div>
                      <span className="text-cool-grey">Service Date</span>
                      <p className="font-semibold text-deep-navy">
                        {new Date(record.service_date).toLocaleDateString()}
                      </p>
                    </div>
                    <div>
                      <span className="text-cool-grey">Submitted</span>
                      <p className="font-semibold text-deep-navy">
                        {new Date(record.submitted_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>

                  <div className="mt-4">
                    <span className="text-cool-grey text-sm block mb-1">Activity</span>
                    <p className="text-deep-navy bg-soft-cream rounded p-3">{record.activity_description}</p>
                  </div>
                </div>

                {record.status === 'pending' && (
                  <div className="border-t border-light-grey pt-4">
                    <div className="mb-3">
                      <label className="block text-sm font-semibold text-deep-navy mb-2">
                        Rejection Reason (if applicable)
                      </label>
                      <textarea
                        value={rejectionReason[record.id] || ''}
                        onChange={e => setRejectionReason(prev => ({ ...prev, [record.id]: e.target.value }))}
                        placeholder="Optional: explain why you're rejecting this submission"
                        maxLength={200}
                        rows={2}
                        className="w-full px-3 py-2 border border-light-grey rounded-lg font-body text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/50 resize-none"
                      />
                    </div>

                    <div className="flex gap-3">
                      <button
                        onClick={() => handleApprove(record.id)}
                        disabled={approving === record.id}
                        className="flex-1 py-2.5 rounded-lg bg-green-500 text-white font-semibold hover:bg-green-600 transition-colors disabled:opacity-50"
                      >
                        {approving === record.id ? 'Approving...' : '✓ Approve'}
                      </button>
                      <button
                        onClick={() => handleReject(record.id)}
                        disabled={rejecting === record.id}
                        className="flex-1 py-2.5 rounded-lg bg-red-500 text-white font-semibold hover:bg-red-600 transition-colors disabled:opacity-50"
                      >
                        {rejecting === record.id ? 'Rejecting...' : '✕ Reject'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
