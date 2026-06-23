import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useWallet } from '../contexts/WalletContext'
import { API_BASE } from '../lib/platform'

export default function WalletAccountLink() {
  const { user, sendMagicLink, signInWithGoogle } = useAuth()
  const { entries, mergeRemoteEntries } = useWallet()
  const [linking, setLinking] = useState(false)
  const [email, setEmail] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [lastSaved, setLastSaved] = useState<string | null>(null)
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const restoredRef = useRef(false)

  // Auto-restore on sign-in (fires once per login)
  useEffect(() => {
    if (!user || restoredRef.current) return
    restoredRef.current = true
    user.getIdToken().then(token => {
      fetch(`${API_BASE}/api/wallet/restore`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then(r => (r.ok ? r.json() : null))
        .then(data => {
          if (data?.entries?.length) mergeRemoteEntries(data.entries)
        })
        .catch(() => {})
    })
  }, [user?.uid])

  // Auto-save on entries change when signed in (debounced 3 s)
  useEffect(() => {
    if (!user || entries.length === 0) return
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current)
    saveTimerRef.current = setTimeout(() => {
      user.getIdToken().then(token => {
        fetch(`${API_BASE}/api/wallet/backup`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ entries }),
        })
          .then(r => (r.ok ? r.json() : null))
          .then(data => {
            if (data?.success) setLastSaved(new Date().toLocaleTimeString())
          })
          .catch(() => {})
      })
    }, 3000)
    return () => { if (saveTimerRef.current) clearTimeout(saveTimerRef.current) }
  }, [user?.uid, entries])

  const handleEmailLink = async () => {
    if (!email) { setError('Email required'); return }
    setLinking(true); setError(null)
    try {
      await sendMagicLink(email)
      setSuccess(true)
      setTimeout(() => setSuccess(false), 5000)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLinking(false)
    }
  }

  const handleGoogleAuth = async () => {
    setLinking(true); setError(null)
    try {
      await signInWithGoogle()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLinking(false)
    }
  }

  const handleBackupNow = async () => {
    if (!user) { setError('Sign in first'); return }
    setLinking(true)
    try {
      const token = await user.getIdToken()
      const r = await fetch(`${API_BASE}/api/wallet/backup`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ entries }),
      })
      if (!r.ok) throw new Error('Backup failed')
      setLastSaved(new Date().toLocaleTimeString())
      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLinking(false)
    }
  }

  if (user) {
    return (
      <div className="bg-soft-cream rounded-lg p-4 border border-soft-gold/30">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-deep-navy">Backup active</p>
            <p className="text-xs text-cool-grey mt-0.5">{user.email}</p>
            {lastSaved && (
              <p className="text-xs text-green-600 mt-0.5">✓ Saved at {lastSaved}</p>
            )}
          </div>
          <button
            onClick={handleBackupNow}
            disabled={linking}
            className="shrink-0 px-3 py-1.5 rounded-lg bg-soft-gold text-deep-navy text-xs font-semibold hover:bg-bright-gold transition-colors disabled:opacity-50"
          >
            {linking ? 'Saving…' : 'Save now'}
          </button>
        </div>
        {error && <p className="text-xs text-red-600 mt-2">{error}</p>}
        {success && <p className="text-xs text-green-600 mt-2">✓ Wallet backed up</p>}
      </div>
    )
  }

  return (
    <div className="bg-blue-50 rounded-lg p-4 border border-blue-200/50">
      <p className="text-sm font-semibold text-deep-navy mb-1">Link account for recovery</p>
      <p className="text-xs text-cool-grey mb-4">
        Sign in to back up your wallet across devices. Your data syncs automatically.
      </p>

      {error && <p className="text-xs text-red-600 mb-3">{error}</p>}
      {success && <p className="text-xs text-green-600 mb-3">✓ Check your email for the sign-in link</p>}

      <div className="space-y-2">
        <div className="flex gap-2">
          <input
            type="email"
            placeholder="your@email.com"
            value={email}
            onChange={e => setEmail(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleEmailLink()}
            className="flex-1 px-3 py-2 border border-light-grey rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/50"
          />
          <button
            onClick={handleEmailLink}
            disabled={linking || !email}
            className="px-4 py-2 rounded-lg bg-soft-gold text-deep-navy text-sm font-semibold hover:bg-bright-gold transition-colors disabled:opacity-50 whitespace-nowrap"
          >
            {linking ? 'Sending…' : 'Email link'}
          </button>
        </div>

        <button
          onClick={handleGoogleAuth}
          disabled={linking}
          className="w-full px-4 py-2 rounded-lg border border-light-grey bg-white text-sm font-semibold hover:bg-light-grey/50 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Sign in with Google
        </button>
      </div>
    </div>
  )
}
