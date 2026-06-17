import { useEffect, useState } from 'react'
import { usePageMeta } from '../hooks/usePageMeta'
import { useAuth } from '../contexts/AuthContext'

interface PendingVerification {
  id: string
  volunteer_user_id: string
  nonprofit_ein: string
  nonprofit_name: string
  service_date: string
  hours_logged: number
  notes?: string
  created_at: string
}

interface VerificationState {
  ein: string
  token: string
  authenticated: boolean
  loading: boolean
  pending: PendingVerification[]
  error: string | null
}

export default function NonprofitDashboard() {
  usePageMeta(
    'Volunteer Verification | Daanaa',
    'Verify volunteer hours contributed to your nonprofit.'
  )

  const [state, setState] = useState<VerificationState>({
    ein: '',
    token: '',
    authenticated: false,
    loading: false,
    pending: [],
    error: null,
  })

  const [verifying, setVerifying] = useState<Record<string, boolean>>({})

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!state.ein.trim() || !state.token.trim()) {
      setState(prev => ({ ...prev, error: 'EIN and verification token required' }))
      return
    }

    setState(prev => ({ ...prev, loading: true, error: null }))
    try {
      const response = await fetch(
        `/api/nonprofit/${state.ein}/pending-verifications?verification_token=${encodeURIComponent(state.token)}`,
        { method: 'GET' }
      )

      if (!response.ok) {
        throw new Error(`Auth failed: ${response.statusText}`)
      }

      const data = await response.json()
      setState(prev => ({
        ...prev,
        authenticated: true,
        pending: data.pending_verifications || [],
        loading: false,
      }))
    } catch (err) {
      setState(prev => ({
        ...prev,
        error: err instanceof Error ? err.message : 'Failed to authenticate',
        loading: false,
      }))
    }
  }

  const handleVerify = async (logId: string, hoursLogged: number) => {
    setVerifying(prev => ({ ...prev, [logId]: true }))
    try {
      const response = await fetch(
        `/api/nonprofit/${state.ein}/verify-hours/${logId}?verification_token=${encodeURIComponent(state.token)}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            hours_confirmed: hoursLogged,
            notes: `Verified by ${state.ein}`,
          }),
        }
      )

      if (!response.ok) {
        throw new Error(`Verification failed: ${response.statusText}`)
      }

      // Remove verified item from list
      setState(prev => ({
        ...prev,
        pending: prev.pending.filter(p => p.id !== logId),
      }))
    } catch (err) {
      setState(prev => ({
        ...prev,
        error: err instanceof Error ? err.message : 'Failed to verify hours',
      }))
    } finally {
      setVerifying(prev => ({ ...prev, [logId]: false }))
    }
  }

  const handleLogout = () => {
    setState({
      ein: '',
      token: '',
      authenticated: false,
      loading: false,
      pending: [],
      error: null,
    })
  }

  if (!state.authenticated) {
    return (
      <div className="bg-warm-cream min-h-screen py-12">
        <div className="max-w-[600px] mx-auto px-6">
          <div className="bg-white border border-light-grey rounded-xl p-8">
            <h1 className="text-3xl font-display text-deep-navy mb-2">Verify Volunteer Hours</h1>
            <p className="text-cool-grey mb-8">
              Use your nonprofit's EIN and verification token from your nonprofit profile.
            </p>

            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-deep-navy mb-2">
                  Nonprofit EIN
                </label>
                <input
                  type="text"
                  placeholder="e.g., 12-3456789"
                  value={state.ein}
                  onChange={e => setState(prev => ({ ...prev, ein: e.target.value }))}
                  className="w-full px-3 py-2 border border-light-grey rounded-lg font-body text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/30"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-deep-navy mb-2">
                  Verification Token
                </label>
                <input
                  type="password"
                  placeholder="Paste your verification token here"
                  value={state.token}
                  onChange={e => setState(prev => ({ ...prev, token: e.target.value }))}
                  className="w-full px-3 py-2 border border-light-grey rounded-lg font-body text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/30"
                />
              </div>

              {state.error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-red-800 text-sm">{state.error}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={state.loading}
                className="w-full px-4 py-3 bg-soft-gold text-white rounded-lg font-medium hover:bg-soft-gold/90 disabled:opacity-50 transition-colors"
              >
                {state.loading ? 'Authenticating...' : 'Access Dashboard'}
              </button>
            </form>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-warm-cream min-h-screen py-12">
      <div className="max-w-[1000px] mx-auto px-6 lg:px-12">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-display text-deep-navy mb-2">Pending Hour Verifications</h1>
            <p className="text-cool-grey">
              EIN: <span className="font-semibold">{state.ein}</span>
            </p>
          </div>
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-light-grey text-deep-navy rounded-lg font-medium hover:bg-light-grey/70 transition-colors"
          >
            Logout
          </button>
        </div>

        {state.error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{state.error}</p>
          </div>
        )}

        {state.pending.length === 0 ? (
          <div className="bg-white border border-light-grey rounded-xl p-12 text-center">
            <p className="text-cool-grey text-lg mb-2">No pending verifications</p>
            <p className="text-sm text-slate-500">
              Volunteers haven't logged any hours at your organization yet.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {state.pending.map(pending => (
              <div
                key={pending.id}
                className="bg-white border border-light-grey rounded-xl p-6 flex items-center justify-between"
              >
                <div>
                  <h3 className="font-semibold text-deep-navy mb-1">Volunteer Hours Logged</h3>
                  <p className="text-sm text-cool-grey">
                    Date: {pending.service_date} • Hours: {pending.hours_logged.toFixed(1)}
                  </p>
                  {pending.notes && (
                    <p className="text-xs text-slate-600 mt-2 italic">{pending.notes}</p>
                  )}
                </div>
                <button
                  onClick={() => handleVerify(pending.id, pending.hours_logged)}
                  disabled={verifying[pending.id]}
                  className="px-6 py-2 bg-soft-gold text-white rounded-lg font-medium hover:bg-soft-gold/90 disabled:opacity-50 transition-colors whitespace-nowrap ml-4"
                >
                  {verifying[pending.id] ? 'Verifying...' : 'Verify'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
