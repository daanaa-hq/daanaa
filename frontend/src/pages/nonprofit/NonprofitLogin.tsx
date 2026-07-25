import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { GoogleSignInButton, MagicLinkForm } from '../../components/GoogleSignInButton'
import { linkFirebaseToClaim } from '../../data/api'

type Mode = 'options' | 'magic-link' | 'portal-token'

export default function NonprofitLogin() {
  const navigate = useNavigate()
  const { user, getIdToken } = useAuth()

  const [mode, setMode] = useState<Mode>('options')
  const [ein, setEin] = useState('')
  const [token, setToken] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [magicLinkSent, setMagicLinkSent] = useState(false)

  // If already signed in via Firebase, go straight to my-orgs
  useEffect(() => {
    if (user) {
      navigate('/nonprofit/my-orgs', { replace: true })
    }
  }, [user, navigate])

  async function handlePortalToken(e: React.FormEvent) {
    e.preventDefault()
    const cleanEin = ein.replace(/\D/g, '').slice(0, 9)
    const cleanToken = token.trim()
    if (!cleanEin || !cleanToken) {
      setError('Both EIN and token are required.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      // Verify the token first
      const res = await fetch('/api/claim/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ein: cleanEin, token: cleanToken }),
      })
      const body = await res.json()
      if (!res.ok) {
        setError(body.error || 'Invalid or expired token. Please try again.')
        setLoading(false)
        return
      }
      const verifiedToken: string = body.verification_token || cleanToken

      // Try to link Firebase if already signed in (shouldn't happen here but guard anyway)
      const idToken = await getIdToken()
      if (idToken) {
        try {
          await linkFirebaseToClaim(cleanEin, verifiedToken, idToken)
        } catch { /* non-fatal */ }
        navigate(`/nonprofit/dashboard/${cleanEin}`)
      } else {
        // No Firebase session — go directly to the editor with the token
        navigate(`/claim/edit?ein=${encodeURIComponent(cleanEin)}&token=${encodeURIComponent(verifiedToken)}`)
      }
    } catch {
      setError('Could not reach the server. Please try again.')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[100dvh] bg-warm-cream flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-[440px]">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-soft-gold/20 mb-4">
            <span className="text-2xl">🏢</span>
          </div>
          <h1 className="font-display italic text-deep-navy text-[28px] mb-2">
            Nonprofit Portal
          </h1>
          <p className="font-body text-[15px] text-cool-grey">
            Sign in to manage your organization on Daanaa
          </p>
        </div>

        {/* Main card */}
        <div className="bg-white rounded-2xl shadow-sm border border-light-grey p-7">
          {error && (
            <div className="mb-5 p-4 bg-destructive/5 border border-destructive/20 rounded-xl">
              <p className="font-body text-[14px] text-destructive">{error}</p>
            </div>
          )}

          {mode === 'options' && (
            <div className="space-y-5">
              {/* Google OAuth */}
              <div>
                <p className="font-body text-[12px] font-medium text-cool-grey uppercase tracking-wide mb-3">
                  Recommended
                </p>
                <GoogleSignInButton onSuccess={() => navigate('/nonprofit/my-orgs')} />
              </div>

              {/* Divider */}
              <div className="flex items-center gap-3">
                <div className="flex-1 h-px bg-light-grey" />
                <span className="font-body text-[12px] text-muted-cream">or</span>
                <div className="flex-1 h-px bg-light-grey" />
              </div>

              {/* Email magic link */}
              <button
                onClick={() => setMode('magic-link')}
                className="w-full px-5 py-3 rounded-xl border border-light-grey bg-white font-body text-[14px] font-medium text-deep-navy hover:border-soft-gold/40 hover:bg-warm-cream/30 transition-colors text-left flex items-center gap-3"
              >
                <span className="text-lg">✉️</span>
                <span>Send me a sign-in link</span>
              </button>

              {/* Portal token option */}
              <button
                onClick={() => setMode('portal-token')}
                className="w-full px-5 py-3 rounded-xl border border-light-grey bg-white font-body text-[14px] font-medium text-cool-grey hover:border-soft-gold/40 hover:text-deep-navy transition-colors text-left flex items-center gap-3"
              >
                <span className="text-lg">🔑</span>
                <span>I have a portal token</span>
              </button>
            </div>
          )}

          {mode === 'magic-link' && (
            <div>
              <button
                onClick={() => { setMode('options'); setMagicLinkSent(false) }}
                className="flex items-center gap-1 font-body text-[13px] text-cool-grey hover:text-deep-navy mb-5 transition-colors"
              >
                ← Back
              </button>
              {magicLinkSent ? (
                <div className="text-center py-4">
                  <div className="text-3xl mb-3">📬</div>
                  <p className="font-body text-[15px] font-medium text-deep-navy mb-2">
                    Check your inbox
                  </p>
                  <p className="font-body text-[14px] text-cool-grey">
                    We sent a sign-in link to your email. Click it to access your portal.
                  </p>
                </div>
              ) : (
                <>
                  <p className="font-body text-[14px] font-medium text-deep-navy mb-1">
                    Sign in with email
                  </p>
                  <p className="font-body text-[13px] text-cool-grey mb-4">
                    We'll send a one-click sign-in link to your inbox.
                  </p>
                  <MagicLinkForm onSent={() => setMagicLinkSent(true)} />
                </>
              )}
            </div>
          )}

          {mode === 'portal-token' && (
            <div>
              <button
                onClick={() => { setMode('options'); setError(null) }}
                className="flex items-center gap-1 font-body text-[13px] text-cool-grey hover:text-deep-navy mb-5 transition-colors"
              >
                ← Back
              </button>
              <p className="font-body text-[14px] font-medium text-deep-navy mb-1">
                Access with portal token
              </p>
              <p className="font-body text-[13px] text-cool-grey mb-5">
                Use the EIN and token from your verification email or PIN verification page.
              </p>
              <form onSubmit={handlePortalToken} className="space-y-4">
                <div>
                  <label className="block font-body text-[12px] font-medium text-deep-navy mb-1.5">
                    EIN
                  </label>
                  <input
                    type="text"
                    value={ein}
                    onChange={e => setEin(e.target.value)}
                    placeholder="12-3456789"
                    className="w-full border border-light-grey rounded-xl px-4 py-2.5 font-body text-[14px] text-deep-navy bg-white outline-none focus:border-soft-gold transition-colors"
                    disabled={loading}
                  />
                </div>
                <div>
                  <label className="block font-body text-[12px] font-medium text-deep-navy mb-1.5">
                    Portal token
                  </label>
                  <input
                    type="text"
                    value={token}
                    onChange={e => setToken(e.target.value)}
                    placeholder="Paste your token here"
                    className="w-full border border-light-grey rounded-xl px-4 py-2.5 font-mono text-[13px] text-deep-navy bg-white outline-none focus:border-soft-gold transition-colors"
                    disabled={loading}
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading || !ein.trim() || !token.trim()}
                  className="w-full px-4 py-3 bg-soft-gold text-deep-navy font-body text-[14px] font-semibold rounded-xl hover:bg-bright-gold disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? 'Verifying…' : 'Access portal'}
                </button>
              </form>
            </div>
          )}
        </div>

        {/* Footer */}
        <p className="text-center font-body text-[13px] text-cool-grey mt-6">
          New to Daanaa?{' '}
          <Link to="/for-nonprofits" className="text-soft-gold hover:underline font-medium">
            Claim your organization
          </Link>
        </p>
      </div>
    </div>
  )
}
