import { useState } from 'react'
import { useLocation, useNavigate, Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { formatEIN } from '../data/organizations'

interface ClaimState {
  ein: string
  pin: string
  org_name: string
  current_mission: string | null
  current_donate_url: string | null
  irs_address: string
}

export default function OrgClaimEditor() {
  usePageMeta('Update your profile', 'Edit your organization\'s mission and giving link on Daanaa.')
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as ClaimState | null

  const [mission, setMission] = useState(state?.current_mission || '')
  const [description, setDescription] = useState('')
  const [donateConfirmed, setDonateConfirmed] = useState(false)
  const [processorAuth, setProcessorAuth] = useState(false)
  const [attested, setAttested] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState(false)

  if (!state?.ein || !state?.pin) {
    return (
      <div className="min-h-[100dvh] bg-warm-cream pt-[72px] flex items-center justify-center">
        <div className="max-w-[480px] px-6 text-center">
          <p className="font-body text-[16px] text-cool-grey mb-4">
            This page requires a verified claim. Please start from your verification letter.
          </p>
          <Link to="/claim/verify" className="font-body text-[14px] text-soft-gold hover:text-bright-gold transition-colors">
            Enter my PIN →
          </Link>
        </div>
      </div>
    )
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const res = await fetch('/api/claim/profile', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ein: state!.ein,
          pin: state!.pin,
          custom_mission: mission.trim() || undefined,
          custom_description: description.trim() || undefined,
          donate_confirmed: donateConfirmed ? 1 : 0,
          processor_auth: processorAuth ? 1 : 0,
        }),
      })
      const body = await res.json()
      if (!res.ok) {
        setError(body.error || 'Save failed. Please try again.')
        setSubmitting(false)
        return
      }
      setDone(true)
    } catch {
      setError('Could not reach the server. Please try again.')
      setSubmitting(false)
    }
  }

  if (done) {
    return (
      <div className="min-h-[100dvh] bg-warm-cream pt-[72px]">
        <div className="max-w-[600px] mx-auto px-6 py-16">
          <div className="w-12 h-12 rounded-full bg-soft-gold/20 flex items-center justify-center mb-6">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <h1 className="font-display italic text-deep-navy text-[32px] leading-[1.1] mb-3">
            Your page is live
            <span className="block text-soft-gold text-[22px] mt-1">{state.org_name}</span>
          </h1>
          <p className="font-body text-[15px] text-cool-grey leading-[1.6] mb-8">
            Your organization's page now shows the <strong>Claimed ✓</strong> badge. Share it with your donors and supporters.
          </p>

          {/* Share moment */}
          <div className="bg-white border border-light-grey rounded-xl p-6 mb-8 space-y-3">
            <p className="font-body text-[13px] font-medium text-deep-navy">Share your page</p>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => navigator.clipboard?.writeText(`https://daanaa.org/org/${state.ein}`)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg border border-light-grey text-deep-navy font-body text-[13px] hover:border-soft-gold/50 transition-colors"
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                Copy link
              </button>
              <a
                href={`https://www.linkedin.com/sharing/share-offsite/?url=https://daanaa.org/org/${state.ein}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-4 py-2 rounded-lg border border-light-grey text-deep-navy font-body text-[13px] hover:border-soft-gold/50 transition-colors"
              >
                Share on LinkedIn
              </a>
            </div>
          </div>

          <Link
            to={`/org/${state.ein}`}
            className="inline-flex items-center gap-2 font-body text-[14px] text-soft-gold hover:text-bright-gold transition-colors"
          >
            View your profile →
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-[100dvh] bg-warm-cream pt-[72px]">
      <div className="max-w-[640px] mx-auto px-6 py-16">
        <div className="flex items-center gap-2 mb-8">
          <Link to="/" className="font-body text-[12px] text-cool-grey hover:text-deep-navy transition-colors">Home</Link>
          <span className="text-cool-grey/40">/</span>
          <span className="font-body text-[12px] text-cool-grey">Claim editor</span>
        </div>

        <h1 className="font-display italic text-deep-navy text-[32px] leading-[1.1] mb-1">
          {state.org_name}
        </h1>
        <p className="font-body text-[13px] text-cool-grey mb-8">EIN {formatEIN(state.ein)} · {state.irs_address}</p>

        <form onSubmit={handleSave} className="space-y-6">
          {/* Mission */}
          <div>
            <label className="block font-body text-[12px] font-medium text-deep-navy mb-1.5">
              Mission statement
              <span className="ml-2 border border-cool-grey/30 text-cool-grey rounded text-[10px] px-1.5 py-0.5 font-normal">
                {state.current_mission ? 'β ai-generated — update it' : 'optional'}
              </span>
            </label>
            <textarea
              value={mission}
              onChange={e => setMission(e.target.value)}
              placeholder={state.current_mission || 'Describe what your organization does in one or two sentences…'}
              rows={4}
              maxLength={1000}
              className="w-full bg-white border border-light-grey text-deep-navy px-4 py-3 rounded-xl font-body text-[14px] leading-[1.6] outline-none focus:border-soft-gold transition-colors resize-none placeholder:text-cool-grey"
            />
            <p className="mt-1 font-body text-[11px] text-cool-grey/60">{mission.length}/1000</p>
          </div>

          {/* Description */}
          <div>
            <label className="block font-body text-[12px] font-medium text-deep-navy mb-1.5">
              About your organization <span className="font-normal text-cool-grey">(optional)</span>
            </label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Who you serve, how you operate, what makes your work distinctive…"
              rows={4}
              maxLength={2000}
              className="w-full bg-white border border-light-grey text-deep-navy px-4 py-3 rounded-xl font-body text-[14px] leading-[1.6] outline-none focus:border-soft-gold transition-colors resize-none placeholder:text-cool-grey"
            />
          </div>

          {/* Donate link confirmation */}
          {state.current_donate_url && (
            <div className="p-4 rounded-xl bg-white border border-light-grey">
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={donateConfirmed}
                  onChange={e => setDonateConfirmed(e.target.checked)}
                  className="mt-0.5 h-4 w-4 rounded border-light-grey text-soft-gold focus:ring-soft-gold"
                />
                <div>
                  <p className="font-body text-[13px] font-medium text-deep-navy">
                    Confirm our donation link
                  </p>
                  <p className="font-body text-[12px] text-cool-grey mt-0.5 break-all">
                    {state.current_donate_url}
                  </p>
                  <p className="font-body text-[11px] text-cool-grey/60 mt-1">
                    We auto-discovered this link. Checking this removes the "β auto-discovered" label and upgrades it to confirmed.
                  </p>
                </div>
              </label>
            </div>
          )}

          {/* Payment processor auth */}
          <div className="p-4 rounded-xl bg-white border border-light-grey">
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={processorAuth}
                onChange={e => setProcessorAuth(e.target.checked)}
                className="mt-0.5 h-4 w-4 rounded border-light-grey text-soft-gold focus:ring-soft-gold"
              />
              <div>
                <p className="font-body text-[13px] font-medium text-deep-navy">
                  Authorize payment processor verification <span className="font-normal text-cool-grey">(optional)</span>
                </p>
                <p className="font-body text-[11px] text-cool-grey/60 mt-1">
                  Allow Daanaa to contact payment processors (PayPal Giving Fund, Stripe, etc.) to confirm your giving link. This upgrades your badge to Certified ✓ when we have a partnership in place.
                </p>
              </div>
            </label>
          </div>

          {/* Attestation */}
          <div className="p-4 rounded-xl bg-white border border-light-grey">
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                required
                checked={attested}
                onChange={e => setAttested(e.target.checked)}
                className="mt-0.5 h-4 w-4 rounded border-light-grey text-soft-gold focus:ring-soft-gold shrink-0"
              />
              <span className="font-body text-[12px] text-cool-grey leading-[1.65]">
                I confirm that I am an authorized representative of {state.org_name} and that the information I am submitting is truthful and accurate. I understand that false statements may constitute fraud under 18 U.S.C. § 1001 and may result in permanent removal from Daanaa and referral to the IRS.
              </span>
            </label>
          </div>

          {error && (
            <p className="font-body text-[13px] text-red-600 leading-[1.5]">{error}</p>
          )}

          <div className="flex items-center gap-4">
            <button
              type="submit"
              disabled={submitting || !attested}
              className="flex-1 h-[48px] bg-soft-gold text-deep-navy font-body text-[14px] font-semibold rounded-full hover:bg-bright-gold transition-colors disabled:opacity-60"
            >
              {submitting ? 'Saving…' : 'Save and publish'}
            </button>
            <Link
              to={`/org/${state.ein}`}
              className="font-body text-[13px] text-cool-grey hover:text-deep-navy transition-colors"
            >
              Skip for now
            </Link>
          </div>

          <p className="font-body text-[11px] text-cool-grey/50 leading-[1.5]">
            IRS public record data (name, EIN, address, financials) is never modified. Only the fields above are organization-submitted.
          </p>
        </form>
      </div>
    </div>
  )
}
