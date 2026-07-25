import React, { useState } from 'react'
import { usePageMeta } from '../hooks/usePageMeta'
import { CardPattern } from './ui/CardPattern'

interface NonprofitSignupProps {
  onSuccess?: (accountId: string) => void
}

export default function NonprofitSignup({ onSuccess }: NonprofitSignupProps) {
  usePageMeta(
    'Nonprofit Portal | Daanaa',
    'Sign up to manage donation letters and impact reports for your nonprofit.'
  )

  const [ein, setEin] = useState('')
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [accountId, setAccountId] = useState<string | null>(null)

  const handleEinChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let value = e.target.value.replace(/\D/g, '')
    if (value.length <= 9) {
      if (value.length >= 2) {
        value = value.slice(0, 2) + '-' + value.slice(2)
      }
      setEin(value)
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    const cleanEin = ein.replace(/\D/g, '')
    if (cleanEin.length !== 9) {
      setError('EIN must be 9 digits')
      return
    }

    if (!email.trim()) {
      setError('Email is required')
      return
    }

    setLoading(true)

    try {
      const res = await fetch('/api/nonprofit/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ein: cleanEin,
          email: email.trim(),
        }),
      })

      const data = await res.json()

      if (!res.ok) {
        setError(data.error || 'Something went wrong')
        return
      }

      setSuccess(true)
      setAccountId(data.account_id)
      if (onSuccess) {
        onSuccess(data.account_id)
      }
    } catch (err) {
      setError((err as Error).message || 'Network error')
    } finally {
      setLoading(false)
    }
  }

  if (success && accountId) {
    return (
      <div className="min-h-screen bg-soft-cream flex items-center justify-center p-4">
        <CardPattern variant="elevated" className="max-w-md w-full text-center">
          <div className="mb-4 text-4xl">✓</div>
          <h2 className="font-display text-2xl italic text-deep-navy mb-2">Check your email</h2>
          <p className="font-body text-sm text-deep-navy mb-4">
            We've sent a verification link to <strong>{email}</strong>. Click it to complete your signup and access the letter portal.
          </p>
          <p className="font-body text-xs text-cool-grey">
            The link will expire in 24 hours. If you don't see it, check your spam folder.
          </p>
        </CardPattern>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-soft-cream to-white py-12 px-4">
      <div className="max-w-md mx-auto">
        <CardPattern variant="elevated">
          <div className="mb-6 text-center">
            <h1 className="font-display text-4xl italic text-deep-navy mb-2">
              Letter Portal
            </h1>
            <p className="font-body text-sm text-cool-grey">
              Manage donation letters and volunteer tracking
            </p>
          </div>

          {/* Info banner */}
          <CardPattern variant="subtle" className="mb-6">
            <p className="text-xs text-deep-navy">
              <strong>✓ Free for nonprofits</strong> · Approve and generate tax-compliant donation letters for your supporters.
            </p>
          </CardPattern>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Error message */}
          {error && (
            <div className="bg-destructive/5 border border-destructive/20 rounded-lg p-4">
              <p className="text-sm text-destructive"><strong>Error:</strong> {error}</p>
            </div>
          )}

          {/* EIN Input */}
          <div>
            <label className="block font-body text-sm font-semibold text-deep-navy mb-2">
              Organization EIN *
            </label>
            <input
              type="text"
              value={ein}
              onChange={handleEinChange}
              placeholder="XX-XXXXXXX"
              maxLength={11}
              className={`w-full px-4 py-3 border rounded-lg font-mono text-sm focus:outline-none focus:ring-2 transition-colors ${
                error && ein.replace(/\D/g, '').length !== 9
                  ? 'border-red-300 focus:ring-red-200'
                  : 'border-light-grey focus:ring-soft-gold/50'
              }`}
              autoFocus
            />
            <p className="font-body text-xs text-cool-grey mt-2">
              Found on your IRS 501(c)(3) determination letter. Example: 12-3456789
            </p>
          </div>

          {/* Email Input */}
          <div>
            <label className="block font-body text-sm font-semibold text-deep-navy mb-2">
              Email Address *
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="director@nonprofit.org"
              className="w-full px-4 py-3 border border-light-grey rounded-lg font-body text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/50"
              required
            />
            <p className="font-body text-xs text-cool-grey mt-2">
              We'll send a verification link to this address. Use your organizational email if possible.
            </p>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading || ein.replace(/\D/g, '').length !== 9 || !email.trim()}
            className="w-full py-3 rounded-lg bg-soft-gold text-deep-navy font-body text-sm font-semibold hover:bg-bright-gold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? '⏳ Sending link…' : '📧 Get verification link'}
          </button>
        </form>

        <p className="font-body text-xs text-cool-grey text-center mt-6">
          Your organization must be registered with the IRS as a 501(c)(3) nonprofit.
        </p>
        </CardPattern>
      </div>
    </div>
  )
}
