import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { ClaimProgressBar } from '../components/ClaimProgressBar'
import { useAuth } from '../contexts/AuthContext'
import { linkFirebaseToClaim } from '../data/api'
import { GoogleSignInButton } from '../components/GoogleSignInButton'

export default function ClaimVerify() {
  usePageMeta('Verify Claim', 'Enter the PIN we gave you over the phone to claim your nonprofit page.')
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { user, getIdToken } = useAuth()
  const [pin, setPin] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [linkInput, setLinkInput] = useState('')
  const [linkSent, setLinkSent] = useState(false)
  const [linkSending, setLinkSending] = useState(false)

  const ein = searchParams.get('ein') || ''

  async function handleEmailLink(e: React.FormEvent) {
    e.preventDefault()
    if (!linkInput.trim()) return
    setLinkSending(true)
    try {
      await fetch('/api/claim/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ein_or_email: linkInput.trim() }),
      })
    } catch { /* neutral confirmation either way — never reveal claim state */ }
    setLinkSent(true)
    setLinkSending(false)
  }

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

      // If signed in with Firebase, link the UID to this claim silently
      if (user) {
        try {
          const idToken = await getIdToken()
          if (idToken) await linkFirebaseToClaim(ein, token, idToken)
        } catch { /* non-fatal — claim still proceeds */ }
      }

      navigate(`/claim/edit?ein=${encodeURIComponent(ein)}&token=${encodeURIComponent(token)}`)
    } catch {
      setError('Could not reach the server. Please try again.')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[100dvh] bg-warm-cream pt-nav">
      <div className="max-w-[520px] mx-auto px-6 py-12">
        <ClaimProgressBar currentStep="verify" />
        <div className="text-center mb-8">
          <h1 className="font-display italic text-deep-navy mb-3">
            Enter your PIN
          </h1>
          <p className="font-body text-lead text-cool-grey">
            A member of the Daanaa team gives you a 6-digit PIN when we call to verify your claim.
            Enter it below to finish.
          </p>
        </div>

        {/* Optional: sign in to save access for return visits */}
        {!user && (
          <div className="mb-4 bg-white rounded-2xl border border-light-cream p-5">
            <p className="font-body text-small font-medium text-deep-navy mb-1">
              Sign in to save your access
            </p>
            <p className="font-body text-caption text-cool-grey mb-3">
              Optional. Sign in once and return to edit your page anytime without a PIN.
            </p>
            <GoogleSignInButton />
          </div>
        )}

        {user && (
          <div className="mb-4 bg-soft-gold/10 border border-soft-gold/30 rounded-2xl px-5 py-3 flex items-center gap-3">
            <span className="text-lg">✓</span>
            <div>
              <p className="font-body text-small font-medium text-deep-navy">Signed in as {user.email}</p>
              <p className="font-body text-caption text-cool-grey">Your access will be saved after verification.</p>
            </div>
          </div>
        )}

        <form onSubmit={handleVerify} className="bg-white rounded-2xl shadow-sm border border-light-cream p-8">
          {error && (
            <div className="mb-5 p-4 bg-destructive/5 border border-destructive/20 rounded-xl">
              <p className="font-body text-body text-destructive">{error}</p>
            </div>
          )}
          <label className="block mb-6">
            <span className="block font-body text-small font-medium text-deep-navy mb-2">Enter your 6-digit PIN</span>
            <input
              type="text"
              inputMode="numeric"
              maxLength={6}
              value={pin}
              onChange={e => setPin(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder="000000"
              className="w-full px-4 py-3 border border-light-cream rounded-xl font-mono text-title text-center tracking-[0.3em] placeholder-muted-cream focus:outline-none focus:ring-2 focus:ring-soft-gold"
              disabled={loading}
              autoFocus
            />
          </label>
          <button
            type="submit"
            disabled={pin.length !== 6 || loading}
            className="w-full px-4 py-3 bg-soft-gold text-deep-navy font-body text-body-lg font-semibold rounded-xl hover:bg-bright-gold disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Verifying...' : 'Verify PIN'}
          </button>
          <p className="mt-5 font-body text-small text-muted-cream text-center">
            Haven't heard from us yet? We call within a few business days, or{' '}
            <button type="button" onClick={() => navigate('/for-nonprofits')} className="text-soft-gold hover:underline">
              start over
            </button>
          </p>
        </form>

        {/* Re-entry for verified claimants who lost their edit link */}
        <div className="mt-6 bg-white rounded-2xl shadow-sm border border-light-cream p-6">
          {linkSent ? (
            <p className="font-body text-body text-cool-grey text-center">
              If that matches a claimed page, the edit link is on its way to the email on file.
            </p>
          ) : (
            <form onSubmit={handleEmailLink}>
              <p className="font-body text-body font-medium text-deep-navy mb-1">
                Already verified your page?
              </p>
              <p className="font-body text-small text-cool-grey mb-3">
                Enter your EIN or the email you claimed with and we will send your edit link.
              </p>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={linkInput}
                  onChange={e => setLinkInput(e.target.value)}
                  placeholder="EIN or email"
                  className="flex-1 px-4 py-2.5 border border-light-cream rounded-xl font-body text-body text-deep-navy placeholder-muted-cream focus:outline-none focus:ring-2 focus:ring-soft-gold"
                />
                <button
                  type="submit"
                  disabled={linkSending || !linkInput.trim()}
                  className="px-4 py-2.5 border border-soft-gold/40 text-deep-navy font-body text-small font-semibold rounded-xl hover:bg-soft-gold/10 disabled:opacity-40 transition-colors"
                >
                  {linkSending ? 'Sending…' : 'Email my link'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
