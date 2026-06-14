import React, { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

export function GoogleSignInButton({ onSuccess, compact }: { onSuccess?: () => void; compact?: boolean }) {
  const { signInWithGoogle } = useAuth()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleClick = async () => {
    setLoading(true)
    setError(null)
    try {
      await signInWithGoogle()
      onSuccess?.()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Sign-in failed'
      // User closed the popup — not an error worth showing
      if (!msg.includes('popup-closed')) setError('Could not sign in. Try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <button
        onClick={handleClick}
        disabled={loading}
        className={compact
          ? "inline-flex items-center gap-2 rounded-lg border border-light-grey bg-white px-4 py-2 font-body text-[13px] font-medium text-deep-navy hover:border-soft-gold/40 transition-colors disabled:opacity-50"
          : "inline-flex items-center gap-3 rounded-xl border border-light-grey bg-white px-5 py-3 font-body text-[14px] font-medium text-deep-navy shadow-sm hover:border-soft-gold/40 hover:bg-warm-cream/30 transition-colors disabled:opacity-50"
        }
      >
        {/* Google G logo */}
        <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
          <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/>
          <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.909-2.259c-.806.54-1.837.86-3.047.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" fill="#34A853"/>
          <path d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05"/>
          <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
        </svg>
        {loading ? 'Signing in…' : 'Continue with Google'}
      </button>
      {error && <p className="mt-2 font-body text-[12px] text-alert-amber">{error}</p>}
    </div>
  )
}

export function MagicLinkForm({ onSent }: { onSent: (email: string) => void }) {
  const { sendMagicLink } = useAuth()
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim()) return
    setLoading(true)
    setError(null)
    try {
      await sendMagicLink(email.trim())
      onSent(email.trim())
    } catch {
      setError('Could not send the link. Check your email address and try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-2">
      <input
        type="email"
        value={email}
        onChange={e => setEmail(e.target.value)}
        placeholder="your@email.com"
        required
        className="w-full border border-light-grey rounded-lg px-3 py-2 font-body text-[14px] text-deep-navy bg-white outline-none focus:border-soft-gold transition-colors"
      />
      <button
        type="submit"
        disabled={loading}
        className="px-5 py-2 rounded-lg bg-deep-navy text-warm-cream font-body text-[13px] font-semibold hover:bg-navy-mid transition-colors disabled:opacity-50"
      >
        {loading ? 'Sending…' : 'Send sign-in link'}
      </button>
      {error && <p className="mt-1 font-body text-[12px] text-alert-amber">{error}</p>}
    </form>
  )
}
