import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'

export default function VendorLoginPage() {
  const { user, signInWithGoogle, sendMagicLink, loading } = useAuth()
  const navigate = useNavigate()
  const [mode, setMode] = useState<'options' | 'magic'>('options')
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (user && !loading) navigate('/vendor/dashboard')
  }, [user, loading, navigate])

  const handleGoogle = async () => {
    setBusy(true)
    setError('')
    try {
      await signInWithGoogle()
    } catch {
      setError('Google sign-in failed. Try again or use email.')
    } finally {
      setBusy(false)
    }
  }

  const handleMagicLink = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim()) return
    setBusy(true)
    setError('')
    try {
      await sendMagicLink(email.trim())
      setSent(true)
    } catch {
      setError('Could not send link. Check the email address.')
    } finally {
      setBusy(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-warm-cream flex items-center justify-center">
        <div className="text-deep-navy">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-warm-cream flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <a href="/" className="text-2xl font-display text-deep-navy font-bold tracking-tight">
            daanaa
          </a>
          <p className="mt-2 text-sm text-slate-500">Vendor Portal</p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-light-grey p-8">
          {mode === 'options' && !sent && (
            <>
              <h1 className="text-xl font-semibold text-deep-navy mb-1">
                Sign in to your vendor account
              </h1>
              <p className="text-sm text-slate-500 mb-6">
                Manage your listing, view ratings, and track nonprofit engagement.
              </p>

              <button
                onClick={handleGoogle}
                disabled={busy}
                className="w-full flex items-center justify-center gap-3 px-4 py-3 border border-light-grey rounded-xl text-deep-navy font-medium hover:bg-slate-50 transition-colors disabled:opacity-50 mb-3"
              >
                <svg width="18" height="18" viewBox="0 0 18 18">
                  <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/>
                  <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" fill="#34A853"/>
                  <path d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05"/>
                  <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 6.29C4.672 4.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
                </svg>
                Continue with Google
              </button>

              <div className="relative my-4">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-light-grey" />
                </div>
                <div className="relative flex justify-center text-xs text-slate-400">
                  <span className="bg-white px-2">or</span>
                </div>
              </div>

              <button
                onClick={() => setMode('magic')}
                className="w-full px-4 py-3 border border-light-grey rounded-xl text-deep-navy font-medium hover:bg-slate-50 transition-colors"
              >
                Sign in with email
              </button>

              {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

              <p className="mt-6 text-center text-xs text-slate-400">
                New vendor?{' '}
                <a href="/for-vendors" className="text-soft-gold hover:underline">
                  Apply to join the network
                </a>
              </p>
            </>
          )}

          {mode === 'magic' && !sent && (
            <>
              <button
                onClick={() => setMode('options')}
                className="text-sm text-slate-500 hover:text-deep-navy mb-4 flex items-center gap-1"
              >
                ← Back
              </button>
              <h1 className="text-xl font-semibold text-deep-navy mb-1">
                Sign in with email
              </h1>
              <p className="text-sm text-slate-500 mb-6">
                We'll send a sign-in link to your inbox.
              </p>
              <form onSubmit={handleMagicLink} className="space-y-3">
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="you@yourcompany.com"
                  className="w-full px-4 py-3 border border-light-grey rounded-xl text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold/40"
                  required
                />
                <button
                  type="submit"
                  disabled={busy || !email.trim()}
                  className="w-full px-4 py-3 bg-soft-gold text-white font-medium rounded-xl hover:bg-soft-gold/90 disabled:opacity-50 transition-colors"
                >
                  {busy ? 'Sending...' : 'Send sign-in link'}
                </button>
              </form>
              {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
            </>
          )}

          {sent && (
            <div className="text-center">
              <div className="text-4xl mb-4">✉️</div>
              <h1 className="text-xl font-semibold text-deep-navy mb-2">Check your inbox</h1>
              <p className="text-sm text-slate-500">
                We sent a sign-in link to <strong>{email}</strong>. Click it to access your
                vendor dashboard.
              </p>
              <p className="mt-4 text-xs text-slate-400">
                Didn't get it?{' '}
                <button onClick={() => setSent(false)} className="text-soft-gold hover:underline">
                  Try again
                </button>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
