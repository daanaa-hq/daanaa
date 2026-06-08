import { useState } from 'react'

interface ResearchAccessProps {
  onSuccess: (token: string) => void
}

export default function ResearchAccess({ onSuccess }: ResearchAccessProps) {
  const [passcode, setPasscode] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await fetch('/api/research/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ passcode })
      })

      if (!response.ok) {
        setError('That access code did not work. Please try again.')
        setLoading(false)
        return
      }

      const data = await response.json()
      localStorage.setItem('research_session_token', data.session_token)
      localStorage.setItem('research_session_expiry', String(Date.now() + data.expires_in * 1000))
      onSuccess(data.session_token)
    } catch {
      setError('Connection error. Please try again.')
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[100] bg-deep-navy/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-warm-cream rounded-2xl shadow-xl p-8 max-w-md w-full">
        {/* Logo */}
        <div className="mb-8 flex justify-center">
          <svg width="120" height="32" viewBox="0 0 120 32" fill="none">
            <text x="0" y="24" font-family="Georgia, serif" font-size="24" fill="#0d1628" font-weight="bold">
              Daanaa
            </text>
          </svg>
        </div>

        <h1 className="font-display text-2xl text-deep-navy mb-2 text-center">
          Research Access
        </h1>
        <p className="text-center text-cool-grey text-sm mb-8">
          Enter the research access code to view Daanaa Methodology v1.0 — May 2026.
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <input
              type="password"
              placeholder="Access code"
              value={passcode}
              onChange={(e) => setPasscode(e.target.value)}
              disabled={loading}
              className="w-full px-4 py-3 rounded-lg border border-light-grey focus:outline-none focus:ring-2 focus:ring-soft-gold/50 text-cool-grey placeholder-cool-grey/50 disabled:bg-warm-cream/50"
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !passcode}
            className="w-full px-6 py-3 rounded-full bg-soft-gold text-deep-navy font-body font-semibold hover:bg-bright-gold disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Unlocking...' : 'Unlock Research Notes'}
          </button>
        </form>

        <p className="text-center text-xs text-cool-grey/60 mt-6">
          This area is intended for advisor, academic, nonprofit, and foundation review.
        </p>
      </div>
    </div>
  )
}
