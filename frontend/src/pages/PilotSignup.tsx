import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import Breadcrumb from '../components/Breadcrumb'

interface InvitationDetails {
  valid: boolean
  ein: string
  organization_name: string
  invitation_id: string
}

export default function PilotSignup() {
  usePageMeta(
    'Daanaa Nonprofit Pilot',
    'Join the pilot program for nonprofit leaders.'
  )

  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [invitation, setInvitation] = useState<InvitationDetails | null>(null)
  const [email, setEmail] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  const inviteCode = searchParams.get('code')

  useEffect(() => {
    if (!inviteCode) {
      setError('No invitation code provided. Please check your invite link.')
      setLoading(false)
      return
    }

    // Verify the invite code
    const verifyInvite = async () => {
      try {
        const res = await fetch('/api/pilot/verify-invite', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code: inviteCode }),
        })

        if (!res.ok) {
          const data = await res.json()
          throw new Error(data.error || 'Invalid invitation code')
        }

        const data: InvitationDetails = await res.json()
        setInvitation(data)
        setLoading(false)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to verify invitation')
        setLoading(false)
      }
    }

    verifyInvite()
  }, [inviteCode])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim() || !invitation) return

    setSubmitting(true)
    try {
      const res = await fetch('/api/claim/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ein: invitation.ein,
          email: email.trim(),
          pilot_invitation_id: invitation.invitation_id,
          attested_authority: true,
          attested_legal: true,
        }),
      })

      const data = await res.json()
      if (!res.ok) {
        setError(data.error || 'Something went wrong')
        setSubmitting(false)
        return
      }

      setSubmitted(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit')
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-warm-cream">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-deep-navy mx-auto mb-4"></div>
          <p className="font-body text-deep-navy">Verifying your invitation...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-warm-cream">
        <div className="max-w-md text-center bg-white p-8 rounded-lg shadow-sm">
          <h1 className="font-display text-2xl text-deep-navy mb-4">Invitation Issue</h1>
          <p className="font-body text-deep-navy mb-6">{error}</p>
          <a
            href="/for-nonprofits"
            className="inline-block px-6 py-3 bg-soft-gold text-deep-navy font-body font-semibold rounded-full hover:bg-bright-gold transition-colors"
          >
            Go to Nonprofits Page
          </a>
        </div>
      </div>
    )
  }

  if (!invitation) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-warm-cream">
        <div className="text-center">
          <p className="font-body text-deep-navy">Invalid invitation</p>
        </div>
      </div>
    )
  }

  if (submitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-warm-cream">
        <div className="max-w-md text-center bg-white p-8 rounded-lg shadow-sm">
          <div className="mb-6">
            <div className="text-5xl mb-4">✓</div>
            <h1 className="font-display text-2xl text-deep-navy mb-2">Check your email</h1>
            <p className="font-body text-[15px] text-gray-700">
              We sent a verification code to <strong>{email}</strong>. Check your inbox and complete the claim process.
            </p>
          </div>
          <a
            href="/for-nonprofits"
            className="inline-block px-6 py-3 bg-soft-gold text-deep-navy font-body font-semibold rounded-full hover:bg-bright-gold transition-colors"
          >
            Done
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-warm-cream">
      {/* Header */}
      <div className="bg-deep-navy py-8 px-6">
        <div className="max-w-[600px] mx-auto">
          <Breadcrumb items={[{ label: 'Home', href: '/' }, { label: 'Nonprofit Pilot' }]} />
          <h1 className="font-display italic text-warm-cream mt-4 text-[42px] leading-tight">
            Join the Daanaa pilot
          </h1>
          <p className="font-body text-muted-cream mt-3 text-[16px]">
            We're inviting 25 nonprofit leaders to shape Daanaa before launch.
            Welcome.
          </p>
        </div>
      </div>

      {/* Main form */}
      <div className="py-12 px-6">
        <div className="max-w-[600px] mx-auto bg-white rounded-lg shadow-sm p-8">
          {/* Organization info */}
          <div className="mb-8 p-6 bg-blue-50 rounded-lg border border-blue-100">
            <p className="font-body text-[13px] text-gray-600 uppercase tracking-wide mb-2">
              Your Organization
            </p>
            <p className="font-display text-2xl text-deep-navy">
              {invitation.organization_name}
            </p>
            <p className="font-body text-[14px] text-gray-600 mt-2">
              EIN: {invitation.ein}
            </p>
          </div>

          {/* What you get */}
          <div className="mb-8">
            <h2 className="font-body text-[14px] font-semibold text-deep-navy uppercase tracking-wide mb-4">
              What you'll get
            </h2>
            <ul className="space-y-3">
              {[
                'A private dashboard showing how your organization compares to peers',
                'Visibility into who\'s discovering you on Daanaa',
                'Ability to correct information about your organization',
                'Early feedback from 24 other nonprofit leaders in the pilot',
              ].map((item, i) => (
                <li key={i} className="flex gap-3 font-body text-[14px] text-deep-navy">
                  <span className="shrink-0 text-link-gold mt-0.5">✓</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Signup form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded text-red-700 font-body text-[14px]">
                {error}
              </div>
            )}

            <div>
              <label className="block font-body text-[13px] font-semibold text-deep-navy mb-2">
                Your email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@organization.org"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg font-body text-[15px] focus:outline-none focus:ring-2 focus:ring-link-gold focus:border-transparent"
                required
              />
              <p className="font-body text-[12px] text-gray-600 mt-2">
                We'll send a verification code to confirm your identity.
              </p>
            </div>

            <button
              type="submit"
              disabled={submitting || !email.trim()}
              className="w-full py-3 bg-soft-gold text-deep-navy font-body font-semibold rounded-lg hover:bg-bright-gold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? 'Sending...' : 'Get started'}
            </button>

            <p className="font-body text-[12px] text-gray-600 text-center">
              By continuing, you agree to Daanaa's{' '}
              <a href="/charter" className="text-link-gold hover:underline">
                charter
              </a>
              . No charges, ever.
            </p>
          </form>
        </div>

        {/* Trust note */}
        <div className="max-w-[600px] mx-auto mt-8 p-6 bg-blue-50 rounded-lg border border-blue-100">
          <p className="font-body text-[13px] text-gray-700 leading-relaxed">
            <strong>This is a pilot.</strong> You're helping us understand how nonprofit leaders want to see their data. Your feedback shapes the platform. Everything you share is covered by Daanaa's <a href="/charter" className="text-link-gold hover:underline">public charter</a> — we don't sell data, use it for marketing, or take a cut of donations.
          </p>
        </div>
      </div>
    </div>
  )
}
