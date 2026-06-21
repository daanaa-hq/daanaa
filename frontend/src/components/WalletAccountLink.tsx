import React, { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useWallet } from '../contexts/WalletContext'

export default function WalletAccountLink() {
  const { user, sendMagicLink, signInWithGoogle } = useAuth()
  const { entries } = useWallet()
  const [linking, setLinking] = useState(false)
  const [email, setEmail] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const handleEmailLink = async () => {
    if (!email) {
      setError('Email required')
      return
    }
    setLinking(true)
    setError(null)
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
    setLinking(true)
    setError(null)
    try {
      await signInWithGoogle()
      setSuccess(true)
      setTimeout(() => setSuccess(false), 5000)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLinking(false)
    }
  }

  const handleBackupWallet = async () => {
    if (!user) {
      setError('Sign in first to backup')
      return
    }

    setLinking(true)
    try {
      const token = await user.getIdToken()
      const response = await fetch('/api/wallet/backup', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ entries }),
      })

      if (!response.ok) throw new Error('Backup failed')
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
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-deep-navy">Account Linked</p>
            <p className="text-xs text-cool-grey mt-1">{user.email}</p>
          </div>
          <button
            onClick={handleBackupWallet}
            disabled={linking}
            className="px-3 py-1.5 rounded-lg bg-soft-gold text-deep-navy text-xs font-semibold hover:bg-bright-gold transition-colors disabled:opacity-50"
          >
            {linking ? 'Backing up...' : 'Backup Now'}
          </button>
        </div>
        {success && <p className="text-xs text-green-600 mt-2">✓ Wallet backed up securely</p>}
      </div>
    )
  }

  return (
    <div className="bg-blue-50 rounded-lg p-4 border border-blue-200/50">
      <p className="text-sm font-semibold text-deep-navy mb-3">Link Account for Recovery</p>
      <p className="text-xs text-cool-grey mb-4">
        Sign in with email or Google to backup your wallet. If you lose access, you can recover by signing back in.
      </p>

      {error && <p className="text-xs text-red-600 mb-3">{error}</p>}
      {success && <p className="text-xs text-green-600 mb-3">✓ Signed in successfully</p>}

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
            {linking ? 'Sending...' : 'Email Link'}
          </button>
        </div>

        <button
          onClick={handleGoogleAuth}
          disabled={linking}
          className="w-full px-4 py-2 rounded-lg border border-light-grey text-sm font-semibold hover:bg-light-grey/50 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <span>🔵</span> Sign in with Google
        </button>
      </div>
    </div>
  )
}
