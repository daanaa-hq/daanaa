import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { ClaimProgressBar } from '../components/ClaimProgressBar'

export default function ClaimVerify() {
  usePageMeta('Verify Claim', 'Enter the PIN from your verification email to claim your nonprofit profile.')
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [pin, setPin] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const ein = searchParams.get('ein') || ''
  const email = searchParams.get('email') || ''

  useEffect(() => {
    if (!ein || !email) navigate('/for-nonprofits', { replace: true })
  }, [ein, email, navigate])

  async function handleVerify(e: React.FormEvent) {
    e.preventDefault()
    if (pin.length !== 6) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/claim/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ein, pin }),
      })
      const body = await res.json()
      if (!res.ok) {
        setError(body.error || 'Verification failed. Please check your PIN.')
        setLoading(false)
        return
      }
      const token = body.verification_token || pin
      navigate(`/claim/edit?ein=${encodeURIComponent(ein)}&token=${encodeURIComponent(token)}`)
    } catch {
      setError('Could not reach the server. Please try again.')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[100dvh] bg-warm-cream pt-[72px]">
      <div className="max-w-[520px] mx-auto px-6 py-12">
        <ClaimProgressBar currentStep="verify" />
        <div className="text-center mb-8">
          <h1 className="font-display italic text-deep-navy mb-3" style={{ fontSize: 'clamp(28px, 4vw, 40px)' }}>
            Check your email
          </h1>
          <p className="font-body text-[16px] text-cool-grey">
            We sent a 6-digit PIN to <strong className="text-deep-navy">{email}</strong>
          </p>
        </div>
        <form onSubmit={handleVerify} className="bg-white rounded-2xl shadow-sm border border-light-cream p-8">
          {error && (
            <div className="mb-5 p-4 bg-red-50 border border-red-200 rounded-xl">
              <p className="font-body text-[14px] text-red-700">{error}</p>
            </div>
          )}
          <label className="block mb-6">
            <span className="block font-body text-[13px] font-medium text-deep-navy mb-2">Enter your 6-digit PIN</span>
            <input
              type="text"
              inputMode="numeric"
              maxLength={6}
              value={pin}
              onChange={e => setPin(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder="000000"
              className="w-full px-4 py-3 border border-light-cream rounded-xl font-mono text-[20px] text-center tracking-[0.3em] placeholder-muted-cream focus:outline-none focus:ring-2 focus:ring-soft-gold"
              disabled={loading}
              autoFocus
            />
          </label>
          <button
            type="submit"
            disabled={pin.length !== 6 || loading}
            className="w-full px-4 py-3 bg-soft-gold text-deep-navy font-body text-[15px] font-semibold rounded-xl hover:bg-bright-gold disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Verifying...' : 'Verify PIN'}
          </button>
          <p className="mt-5 font-body text-[13px] text-muted-cream text-center">
            Didn't get it? Check spam or{' '}
            <button type="button" onClick={() => navigate('/for-nonprofits')} className="text-soft-gold hover:underline">
              try again
            </button>
          </p>
        </form>
      </div>
    </div>
  )
}
