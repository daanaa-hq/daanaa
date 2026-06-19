import { useState, useEffect } from 'react'
import { usePageMeta } from '../hooks/usePageMeta'
import { useAuth } from '../contexts/AuthContext'

interface VolunteerHourRecord {
  id: string
  volunteer_uid: string
  volunteer_email: string
  nonprofit_ein: string
  nonprofit_name: string
  service_date: string
  hours_logged: number
  notes: string
  status: 'pending' | 'verified' | 'rejected'
  verified_at?: string | null
  verified_by?: string | null
  rejection_reason?: string
  created_at: string
}

export default function NonprofitVerification() {
  usePageMeta(
    'Verify Volunteer Hours | Daanaa',
    'Review and verify volunteer hours logged for your nonprofit.'
  )

  const { user, loading: authLoading, getIdToken } = useAuth()
  const [hours, setHours] = useState<VolunteerHourRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [fetchError, setFetchError] = useState<string | null>(null)
  const [selectedHours, setSelectedHours] = useState<string | null>(null)
  const [verificationMessage, setVerificationMessage] = useState('')
  const [rejectionReason, setRejectionReason] = useState('')
  const [rejectFormFor, setRejectFormFor] = useState<string | null>(null)
  const [verifying, setVerifying] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [filterStatus, setFilterStatus] = useState<'all' | 'pending' | 'verified' | 'rejected'>('pending')

  useEffect(() => {
    if (!user || authLoading) return

    const fetchHours = async () => {
      try {
        setLoading(true)
        setFetchError(null)
        const token = await getIdToken()
        const headers: Record<string, string> = { 'Content-Type': 'application/json' }
        if (token) headers['Authorization'] = `Bearer ${token}`
        const response = await fetch('/api/nonprofit/hours-pending', { headers })
        if (!response.ok) throw new Error('Failed to fetch hours')
        const data = await response.json()
        setHours(data.hours || [])
      } catch (err) {
        setFetchError(err instanceof Error ? err.message : 'Failed to load hours')
      } finally {
        setLoading(false)
      }
    }

    fetchHours()
  }, [user, authLoading, getIdToken])

  const filteredHours = hours.filter((h) => {
    if (filterStatus === 'all') return true
    return h.status === filterStatus
  })

  const handleVerify = async (recordId: string) => {
    if (!verificationMessage.trim()) {
      setActionError('Please add a verification note before confirming.')
      return
    }

    setVerifying(true)
    setActionError(null)
    try {
      const token = await getIdToken()
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      if (token) headers['Authorization'] = `Bearer ${token}`

      const response = await fetch('/api/nonprofit/verify-hours', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          record_id: recordId,
          action: 'verify',
          message: verificationMessage,
        }),
      })

      if (!response.ok) throw new Error('Failed to verify hours')

      setHours((prev) =>
        prev.map((h) =>
          h.id === recordId
            ? { ...h, status: 'verified', verified_at: new Date().toISOString(), verified_by: user?.email || undefined }
            : h
        )
      )
      setSelectedHours(null)
      setVerificationMessage('')
    } catch (err) {
      setActionError('Could not verify hours. Please try again.')
    } finally {
      setVerifying(false)
    }
  }

  const handleReject = async (recordId: string) => {
    if (!rejectionReason.trim()) {
      setActionError('Please provide a reason for rejection.')
      return
    }

    setVerifying(true)
    setActionError(null)
    try {
      const token = await getIdToken()
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      if (token) headers['Authorization'] = `Bearer ${token}`

      const response = await fetch('/api/nonprofit/verify-hours', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          record_id: recordId,
          action: 'reject',
          reason: rejectionReason,
        }),
      })

      if (!response.ok) throw new Error('Failed to reject hours')

      setHours((prev) =>
        prev.map((h) =>
          h.id === recordId
            ? { ...h, status: 'rejected', rejection_reason: rejectionReason }
            : h
        )
      )
      setSelectedHours(null)
      setRejectFormFor(null)
      setRejectionReason('')
    } catch (err) {
      setActionError('Could not reject hours. Please try again.')
    } finally {
      setVerifying(false)
    }
  }

  if (authLoading || loading) {
    return (
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12 py-12">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-slate-200 rounded w-1/3"></div>
          <div className="h-40 bg-slate-100 rounded"></div>
        </div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="bg-warm-cream min-h-screen py-12 md:py-16">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
          <div className="text-center py-20">
            <h1 className="text-4xl font-display text-deep-navy mb-4">Hour Verification</h1>
            <p className="text-lg text-cool-grey mb-8">Sign in to verify volunteer hours logged for your nonprofit</p>
            <p className="text-sm text-cool-grey">This feature is for nonprofit staff only.</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-warm-cream min-h-screen py-12 md:py-16">
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-display text-deep-navy mb-3">Hour Verification</h1>
          <p className="text-lg text-cool-grey max-w-2xl">
            Review and verify volunteer hours logged for your organization.
          </p>
        </div>

        {fetchError && (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-4 mb-6">
            <p className="text-red-700">{fetchError}</p>
          </div>
        )}

        {/* Filter Tabs */}
        <div className="flex gap-2 mb-8 flex-wrap">
          {(['all', 'pending', 'verified', 'rejected'] as const).map((status) => (
            <button
              key={status}
              onClick={() => setFilterStatus(status)}
              className={`px-4 py-2 rounded-full font-body text-sm font-medium transition-colors ${
                filterStatus === status
                  ? 'bg-soft-gold text-deep-navy'
                  : 'bg-white border border-light-grey text-cool-grey hover:border-soft-gold'
              }`}
            >
              {status === 'all' ? 'All' : status === 'pending' ? 'Pending' : status === 'verified' ? 'Verified' : 'Rejected'}
              {' '}
              <span className="opacity-70">({hours.filter((h) => status === 'all' || h.status === status).length})</span>
            </button>
          ))}
        </div>

        {/* Hours List */}
        <div className="space-y-4">
          {filteredHours.length === 0 ? (
            <div className="bg-white border border-light-grey rounded-2xl p-8 text-center">
              <p className="text-cool-grey font-body">
                {filterStatus === 'pending'
                  ? 'No pending hours to verify.'
                  : 'No hours in this category.'}
              </p>
            </div>
          ) : (
            filteredHours.map((record) => (
              <div
                key={record.id}
                className="bg-white border border-light-grey rounded-2xl p-6 hover:shadow-md transition-shadow"
              >
                <div
                  className="flex items-start justify-between cursor-pointer"
                  onClick={() => {
                    setSelectedHours(record.id === selectedHours ? null : record.id)
                    setActionError(null)
                    if (record.id !== selectedHours) {
                      setRejectFormFor(null)
                      setRejectionReason('')
                      setVerificationMessage('')
                    }
                  }}
                >
                  <div className="flex-1">
                    <p className="font-semibold text-deep-navy font-body mb-1">{record.volunteer_email}</p>
                    <p className="text-sm text-cool-grey font-body mb-2">{record.service_date}</p>
                    <div className="flex gap-4 text-sm">
                      <span className="font-medium text-deep-navy font-body">{record.hours_logged} hours</span>
                      {record.notes && <span className="text-cool-grey italic font-body">"{record.notes}"</span>}
                    </div>
                  </div>
                  <div className="text-right ml-4">
                    <span
                      className={`inline-block px-3 py-1 rounded-full text-xs font-medium font-body ${
                        record.status === 'pending'
                          ? 'bg-amber-50 text-amber-700 border border-amber-200'
                          : record.status === 'verified'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-red-50 text-red-700 border border-red-200'
                      }`}
                    >
                      {record.status === 'pending' ? 'Pending' : record.status === 'verified' ? 'Verified' : 'Rejected'}
                    </span>
                  </div>
                </div>

                {/* Expansion details */}
                {selectedHours === record.id && (
                  <div className="mt-6 pt-6 border-t border-light-grey space-y-4">
                    {actionError && (
                      <div className="bg-red-50 border border-red-200 rounded-xl p-3">
                        <p className="text-sm text-red-700 font-body">{actionError}</p>
                      </div>
                    )}

                    {record.status === 'pending' && (
                      <>
                        {rejectFormFor !== record.id ? (
                          <>
                            <div>
                              <label className="block text-sm font-medium text-deep-navy font-body mb-2">
                                Verification Notes
                              </label>
                              <textarea
                                value={verificationMessage}
                                onChange={(e) => setVerificationMessage(e.target.value)}
                                placeholder="Add details about verification (optional)"
                                className="w-full px-3 py-2 border border-light-grey rounded-xl text-sm font-body focus:outline-none focus:ring-2 focus:ring-soft-gold/30"
                                rows={3}
                              />
                            </div>
                            <div className="flex gap-3">
                              <button
                                onClick={(e) => { e.stopPropagation(); handleVerify(record.id) }}
                                disabled={verifying}
                                className="flex-1 px-4 py-2 bg-emerald-600 text-white rounded-xl font-body font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors"
                              >
                                {verifying ? 'Verifying...' : 'Verify Hours'}
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  setRejectFormFor(record.id)
                                  setActionError(null)
                                }}
                                disabled={verifying}
                                className="flex-1 px-4 py-2 bg-red-50 text-red-700 border border-red-200 rounded-xl font-body font-medium hover:bg-red-100 disabled:opacity-50 transition-colors"
                              >
                                Reject
                              </button>
                            </div>
                          </>
                        ) : (
                          <div className="space-y-3">
                            <div>
                              <label className="block text-sm font-medium text-deep-navy font-body mb-2">
                                Reason for Rejection
                              </label>
                              <textarea
                                value={rejectionReason}
                                onChange={(e) => setRejectionReason(e.target.value)}
                                placeholder="Explain why these hours are being rejected"
                                className="w-full px-3 py-2 border border-red-200 rounded-xl text-sm font-body focus:outline-none focus:ring-2 focus:ring-red-200"
                                rows={3}
                                autoFocus
                              />
                            </div>
                            <div className="flex gap-3">
                              <button
                                onClick={(e) => { e.stopPropagation(); handleReject(record.id) }}
                                disabled={verifying}
                                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-xl font-body font-medium hover:bg-red-700 disabled:opacity-50 transition-colors"
                              >
                                {verifying ? 'Rejecting...' : 'Confirm Rejection'}
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  setRejectFormFor(null)
                                  setRejectionReason('')
                                  setActionError(null)
                                }}
                                disabled={verifying}
                                className="px-4 py-2 bg-white border border-light-grey text-cool-grey rounded-xl font-body font-medium hover:border-soft-gold transition-colors"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        )}
                      </>
                    )}

                    {record.status === 'verified' && (
                      <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl">
                        <p className="text-sm text-emerald-800 font-body">
                          Verified by {record.verified_by} on {record.verified_at ? new Date(record.verified_at).toLocaleDateString() : ''}
                        </p>
                      </div>
                    )}

                    {record.status === 'rejected' && (
                      <div className="p-3 bg-red-50 border border-red-200 rounded-xl">
                        <p className="text-sm text-red-800 font-body font-medium mb-1">Rejection Reason:</p>
                        <p className="text-sm text-red-700 font-body">{record.rejection_reason}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Stats */}
        {hours.length > 0 && (
          <div className="mt-12 grid grid-cols-3 gap-4">
            <div className="bg-white border border-light-grey rounded-2xl p-4 text-center">
              <p className="text-sm text-cool-grey font-body mb-1">Pending</p>
              <p className="text-2xl font-display text-deep-navy">{hours.filter((h) => h.status === 'pending').length}</p>
            </div>
            <div className="bg-white border border-light-grey rounded-2xl p-4 text-center">
              <p className="text-sm text-cool-grey font-body mb-1">Verified</p>
              <p className="text-2xl font-display text-emerald-600">{hours.filter((h) => h.status === 'verified').length}</p>
            </div>
            <div className="bg-white border border-light-grey rounded-2xl p-4 text-center">
              <p className="text-sm text-cool-grey font-body mb-1">Rejected</p>
              <p className="text-2xl font-display text-red-600">{hours.filter((h) => h.status === 'rejected').length}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
