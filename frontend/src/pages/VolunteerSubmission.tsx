import React, { useState, useEffect } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

export default function VolunteerSubmission() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const code = searchParams.get('code') || ''

  usePageMeta('Claim Volunteer Hours | Daanaa', 'Submit your volunteer hours for nonprofit approval.')

  const [email, setEmail] = useState('')
  const [confirming, setConfirming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    if (!code) {
      setError('No claim code provided. Ask your nonprofit for a claim code.')
    }
  }, [code])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setConfirming(true)

    try {
      const res = await fetch('http://localhost:5000/api/volunteer/claim', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, email }),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.error || 'Failed to claim hours')
      }

      setSuccess(true)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setConfirming(false)
    }
  }

  if (!code) {
    return (
      <div className="min-h-screen bg-warm-cream flex items-center justify-center px-4 py-16">
        <div className="max-w-md w-full text-center">
          <h1 className="font-display italic text-deep-navy text-[28px] mb-3">No claim code</h1>
          <p className="font-body text-cool-grey mb-6">
            Ask your nonprofit for a claim code. It should look like: VOL-ABC123DEF456
          </p>
          <Link to="/" className="text-soft-gold font-semibold hover:underline">Back to home</Link>
        </div>
      </div>
    )
  }

  if (success) {
    return (
      <div className="min-h-screen bg-warm-cream flex items-center justify-center px-4 py-16">
        <div className="max-w-md w-full text-center">
          <h1 className="font-display italic text-deep-navy text-[28px] mb-3">Hours claimed!</h1>
          <p className="font-body text-cool-grey mb-6">
            Your nonprofit will review and approve your volunteer hours. You'll receive an email when they take action.
          </p>
          <Link to="/" className="inline-block px-6 py-2 bg-soft-gold text-deep-navy rounded-lg font-semibold hover:bg-bright-gold">
            Back to home
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-warm-cream flex items-center justify-center px-4 py-16">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-2xl p-8 border border-light-grey">
          <h1 className="font-display italic text-deep-navy text-[28px] mb-2">Claim Your Hours</h1>
          <p className="text-cool-grey text-[14px] mb-6">
            Code: <span className="font-mono text-deep-navy">{code}</span>
          </p>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl">
              <p className="text-red-700 text-[14px]">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-[13px] font-semibold text-deep-navy mb-2">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-2 border border-light-grey rounded-lg focus:outline-none focus:ring-2 focus:ring-soft-gold"
                placeholder="your@email.com"
              />
              <p className="text-[12px] text-cool-grey mt-1">Must match what you gave your nonprofit</p>
            </div>

            <button
              type="submit"
              disabled={confirming || !email}
              className="w-full px-6 py-3 bg-soft-gold text-deep-navy rounded-lg font-semibold hover:bg-bright-gold disabled:opacity-50 transition-colors"
            >
              {confirming ? 'Submitting...' : 'Claim Hours'}
            </button>
          </form>

          <p className="text-[12px] text-cool-grey text-center mt-6">
            Your nonprofit will review and approve these hours.
          </p>
        </div>
      </div>
    </div>
  )
}
