import React, { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { usePageMeta } from '../../hooks/usePageMeta'
import { useAuth } from '../../contexts/AuthContext'
import { API_BASE } from '../../data/api'
import VolunteerExportButton from '../../components/VolunteerExportButton'

interface VolunteerRecord {
  id: string
  volunteer_name: string
  volunteer_email: string
  hours: number
  service_date: string
  activity_description: string
  task_type: string | null
  status: 'pending' | 'confirmed' | 'approved' | 'rejected'
  submitted_at: string
  submitted_via: string
  locked_at: string | null
}

export default function VolunteerApproval() {
  const { ein } = useParams<{ ein: string }>()
  const navigate = useNavigate()
  const { getIdToken } = useAuth()
  usePageMeta('Volunteer Hours Approval | Daanaa', 'Review and approve volunteer hours for your organization')

  const [records, setRecords] = useState<VolunteerRecord[]>([])
  const [idToken, setIdToken] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('pending')
  const [approving, setApproving] = useState<string | null>(null)
  const [rejecting, setRejecting] = useState<string | null>(null)
  const [rejectionReason, setRejectionReason] = useState<Record<string, string>>({})

  const fetchRecords = useCallback(async () => {
    if (!ein) return
    try {
      setLoading(true)
      const token = await getIdToken()
      if (!token) {
        navigate('/nonprofit/login', { replace: true })
        return
      }
      setIdToken(token)

      const statusParam = filter === 'pending' ? 'pending' : filter
      const response = await fetch(`${API_BASE}/api/nonprofit/${ein}/volunteer/list?status=${statusParam}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!response.ok) throw new Error('Failed to load volunteer hours')
      const data = await response.json()
      setRecords(data.records || [])
      setError(null)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }, [ein, filter, getIdToken, navigate])

  useEffect(() => { fetchRecords() }, [fetchRecords])

  const handleApprove = async (recordId: string) => {
    setApproving(recordId)
    try {
      const response = await fetch(`${API_BASE}/api/nonprofit/${ein}/volunteer/${recordId}/approve`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${idToken}` },
      })
      if (!response.ok) throw new Error('Failed to approve volunteer hours')
      setRecords(prev => prev.map(r => (r.id === recordId ? { ...r, status: 'approved' } : r)))
      setError(null)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setApproving(null)
    }
  }

  const handleReject = async (recordId: string) => {
    setRejecting(recordId)
    try {
      const response = await fetch(`${API_BASE}/api/nonprofit/${ein}/volunteer/${recordId}/reject`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${idToken}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: rejectionReason[recordId] || '' }),
      })
      if (!response.ok) throw new Error('Failed to reject volunteer hours')
      setRecords(prev => prev.map(r => (r.id === recordId ? { ...r, status: 'rejected' } : r)))
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

  if (!ein) return null

  if (loading) {
    return (
      <div className="min-h-screen bg-soft-cream p-6 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-soft-gold border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  const pendingCount = records.filter(r => r.status === 'pending' || r.status === 'confirmed').length

  return (
    <div className="min-h-screen bg-soft-cream p-6">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="font-display text-3xl text-deep-navy mb-2">Volunteer Hours Approval</h1>
          <p className="text-cool-grey">Review and approve volunteer contributions. These are nonprofit-approved records, not Daanaa-verified.</p>
        </div>

        {error && (
          <div className="bg-destructive/5 border border-destructive/20 rounded-lg p-4 mb-6 text-destructive">{error}</div>
        )}

        <div className="bg-white rounded-lg p-4 mb-6 border border-light-grey flex gap-4 flex-wrap justify-between items-center">
          <div className="flex gap-4 flex-wrap">
            {(['all', 'pending', 'approved', 'rejected'] as const).map(status => (
              <button
                key={status}
                onClick={() => setFilter(status)}
                className={`px-4 py-2 rounded-lg font-semibold text-sm transition-colors ${
                  filter === status ? 'bg-soft-gold text-deep-navy' : 'bg-light-grey text-cool-grey hover:bg-light-grey/70'
                }`}
              >
                {status === 'all' ? 'All Submissions' : status === 'pending' ? `Pending (${pendingCount})` : status === 'approved' ? 'Approved' : 'Rejected'}
              </button>
            ))}
          </div>
          <div className="w-full md:w-auto">
            <VolunteerExportButton nonprofitEin={ein} idToken={idToken} />
          </div>
        </div>

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
                        record.status === 'pending' || record.status === 'confirmed'
                          ? 'bg-yellow-100 text-yellow-800'
                          : record.status === 'approved'
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
                      <p className="font-semibold text-deep-navy">{new Date(record.service_date).toLocaleDateString()}</p>
                    </div>
                    <div>
                      <span className="text-cool-grey">Role</span>
                      <p className="font-semibold text-deep-navy capitalize">{record.task_type || 'Volunteer'}</p>
                    </div>
                  </div>

                  {record.activity_description && (
                    <div className="mt-4">
                      <span className="text-cool-grey text-sm block mb-1">Notes</span>
                      <p className="text-deep-navy bg-soft-cream rounded p-3">{record.activity_description}</p>
                    </div>
                  )}
                </div>

                {(record.status === 'pending' || record.status === 'confirmed') && (
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
                        className="flex-1 py-2.5 rounded-lg bg-destructive/50 text-white font-semibold hover:bg-red-600 transition-colors disabled:opacity-50"
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
