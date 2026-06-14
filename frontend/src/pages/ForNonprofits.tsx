import { useState, useEffect } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { submitWaitlist, getOrganization, getMyOrgs, getPortalToken } from '../data/api'
import { usePageMeta } from '../hooks/usePageMeta'
import { useAuth } from '../contexts/AuthContext'
import { GoogleSignInButton } from '../components/GoogleSignInButton'
import LampMark from '../components/LampMark'
import { TIER_COLORS } from '../components/TrustBadge'
import type { TierName } from '../components/TrustBadge'
import { formatEINInput } from '../data/organizations'

function StepDot({ n, label }: { n: number; label: string }) {
  return (
    <div className="flex items-center gap-4">
      <div className="shrink-0 w-8 h-8 rounded-full bg-soft-gold text-deep-navy font-body text-[13px] font-bold flex items-center justify-center">
        {n}
      </div>
      <span className="font-body text-[15px] text-deep-navy">{label}</span>
    </div>
  )
}

export default function ForNonprofits() {
  usePageMeta('For Nonprofits', 'Claim your free Daanaa page. Nonprofits that add mission, website, and current financials rise through the visibility tiers.')
  const navigate = useNavigate()
  const { user, getIdToken } = useAuth()
  const [searchParams] = useSearchParams()
  const [portalLoading, setPortalLoading] = useState(false)
  const [portalError, setPortalError]     = useState<string | null>(null)
  const [email, setEmail] = useState('')
  const [ein, setEin] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [orgName, setOrgName] = useState<string | null>(null)
  const [irsAddress, setIrsAddress] = useState<string | null>(null)
  const [attested, setAttested] = useState(false)
  const [attestedLegal, setAttestedLegal] = useState(false)
  const [phone, setPhone] = useState('')
  const [repName, setRepName] = useState('')
  const [title, setTitle] = useState('')

  // Prefill EIN from URL param and look up org info
  useEffect(() => {
    const einParam = (searchParams.get('ein') || '').replace(/\D/g, '').slice(0, 9)
    if (!einParam) return
    setEin(formatEINInput(einParam))
    getOrganization(einParam).then(org => {
      setOrgName(org.organization_name)
      const addr = [org.street_address, org.CITY, org.STATE, org.zipcode].filter(Boolean).join(', ')
      setIrsAddress(addr || null)
    }).catch(() => {})
  }, [searchParams])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    if (!email.trim() || !ein.trim()) return
    setSubmitting(true)
    try {
      const res = await fetch('/api/claim/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ein: ein.replace(/\D/g, '').slice(0, 9),
          email: email.trim(),
          phone: phone.trim(),
          name: repName.trim(),
          title: title.trim(),
          attested_authority: attested,
          attested_legal: attestedLegal,
        }),
      })
      const body = await res.json()
      if (!res.ok) {
        setError(body.error || 'Something went wrong. Please try again.')
        setSubmitting(false)
        return
      }
      if (body.org_name) setOrgName(body.org_name)
      // Stay on the confirmation: the PIN arrives later, on the verification
      // call, so routing to the PIN page now would dead-end the user.
      setSubmitted(true)
    } catch {
      // Fallback: log locally so we don't lose the lead
      try { await submitWaitlist(email.trim(), 'claiming', ein.replace(/\D/g, '') || undefined) } catch {}
      setError('Could not reach the server. Your request has been saved, and we will follow up.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-[100dvh]">
      {/* Header */}
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 pt-8 pb-12 md:pt-12 md:pb-20">
          <div className="flex items-center gap-2 mb-6">
            <Link to="/" className="font-body text-[12px] tracking-[0.02em] text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream">/</span>
            <span className="font-body text-[12px] text-muted-cream">For Nonprofits</span>
          </div>

          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-10 md:gap-16">
            <div className="max-w-[680px]">
              <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">For organizations</span>
              <h1 className="font-display italic text-warm-cream mt-3 leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(32px, 5vw, 60px)' }}>
                Your public record may already be listed. Add the story only you can tell.
              </h1>
              <p className="mt-5 font-body text-[18px] leading-[1.65] text-muted-cream">
                Daanaa helps donors find public nonprofit records and giving paths. Claim your page for free to add your mission, programs, service area, leadership, impact notes, events, volunteer opportunities, and official giving links.
              </p>
              <a href="#claim" className="mt-8 inline-flex items-center gap-2 px-8 py-[14px] rounded-full bg-soft-gold text-deep-navy font-body text-[14px] font-semibold hover:bg-bright-gold transition-colors">
                Claim your page free
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
              </a>
            </div>
            <div className="shrink-0 hidden md:flex justify-end">
              <img src="/logo.png" alt="Daanaa" className="w-48 h-48 lg:w-56 lg:h-56 object-contain drop-shadow-[0_12px_48px_rgba(201,169,110,0.22)]" />
            </div>
          </div>
        </div>
      </div>

      {/* What you get */}
      <div className="bg-warm-cream py-10 md:py-16 lg:py-20">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
          <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">What you can add for free</span>
          <h2 className="font-display italic text-deep-navy mt-3 text-[32px] leading-[1.1] mb-10">
            Tell your story in your own words
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-8 max-w-[900px]">
            {[
              {
                n: 1,
                title: 'Mission & programs',
                description: 'Add your mission statement, program descriptions, and the people you serve, in your words, clearly marked as written by you and separate from government records.',
              },
              {
                n: 2,
                title: 'Leadership team',
                description: 'Introduce your executive director and board. Donors and volunteers want to know who leads the organization, and that\'s not in public IRS records.',
              },
              {
                n: 3,
                title: 'Impact metrics',
                description: 'Share the numbers that matter to you: meals served, families housed, students tutored. Context that no government report can provide.',
              },
              {
                n: 4,
                title: 'Annual reports & documents',
                description: 'Link your latest annual report, impact summary, or external evaluations. Give donors the documents they\'re already searching for, directly on your listing.',
              },
              {
                n: 5,
                title: 'Events & volunteer opportunities',
                description: 'Post upcoming events and volunteer shifts visible to donors in your region.',
                phase2: true,
              },
              {
                n: 6,
                title: 'Regional connections',
                description: 'Discover nonprofits doing complementary work nearby. Collaboration, not competition, is how communities thrive.',
                phase2: true,
              },
              {
                n: 7,
                title: 'Supplier network',
                description: 'Access vetted vendors for software, printing, and supplies, negotiated at nonprofit rates. Lower your costs so more goes to your mission.',
                phase2: true,
              },
            ].map(({ n, title, description, phase2 }) => (
              <div key={n} className={`flex gap-5 ${phase2 ? 'opacity-55' : ''}`}>
                <div className="shrink-0 w-8 h-8 rounded-full bg-soft-gold/15 border border-soft-gold/30 text-soft-gold font-body text-[13px] font-semibold flex items-center justify-center mt-0.5">
                  {n}
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-1.5">
                    <h3 className="font-body text-[16px] font-semibold text-deep-navy">{title}</h3>
                    {phase2 && (
                      <span className="px-2 py-0.5 rounded-full bg-cool-grey/10 border border-cool-grey/20 font-body text-[10px] text-cool-grey font-medium">Coming soon</span>
                    )}
                  </div>
                  <p className="font-body text-[14px] text-cool-grey leading-[1.65]">{description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Two-layer model explainer */}
      <div className="bg-white py-10 md:py-16 border-t border-light-grey">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
          <div className="max-w-[680px]">
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">Trust by design</span>
            <h2 className="font-display italic text-deep-navy mt-3 text-[32px] leading-[1.1] mb-6">
              Government records and your story, clearly separated
            </h2>
            <p className="font-body text-[16px] text-cool-grey leading-[1.7] mb-4">
              Daanaa keeps two distinct layers on every page. The IRS layer, which covers revenue, category, and tax status, is public data we display but you cannot edit. Your claimed layer, which covers mission, programs, impact, and leadership, is your own voice, clearly labeled.
            </p>
            <p className="font-body text-[16px] text-cool-grey leading-[1.7]">
              Donors can always tell which is which. Keeping these two layers separate is how they trust what they read, and how you stay in control of your own story.
            </p>
          </div>

          <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 gap-6 max-w-[680px]">
            <div className="p-5 bg-warm-cream rounded-xl border border-light-grey">
              <p className="font-body text-[11px] tracking-[0.06em] text-soft-gold uppercase font-medium mb-3">IRS public data</p>
              <ul className="space-y-2 font-body text-[13px] text-cool-grey">
                {['Legal name', 'Nonprofit category', 'Revenue from IRS filings', 'Daanaa financial ranking', 'Year & data source'].map(i => (
                  <li key={i} className="flex items-center gap-2">
                    <span className="w-1 h-1 rounded-full bg-cool-grey/40 shrink-0" />{i}
                  </li>
                ))}
              </ul>
              <p className="mt-3 font-body text-[11px] text-cool-grey">Not editable · Always shown</p>
            </div>
            <div className="p-5 rounded-xl border-2 border-dashed border-soft-gold/30">
              <p className="font-body text-[11px] tracking-[0.06em] text-soft-gold uppercase font-medium mb-3">Your claimed content</p>
              <ul className="space-y-2 font-body text-[13px] text-cool-grey">
                {['Mission & programs', 'Leadership team', 'Impact metrics', 'Events & opportunities', 'Photos & reports'].map(i => (
                  <li key={i} className="flex items-center gap-2">
                    <span className="w-1 h-1 rounded-full bg-soft-gold/50 shrink-0" />{i}
                  </li>
                ))}
              </ul>
              <p className="mt-3 font-body text-[11px] text-cool-grey">Labeled "written by you" · Controlled by you</p>
            </div>
          </div>

          {/* Beta label explainer */}
          <div className="mt-10 max-w-[680px] p-6 rounded-xl bg-warm-cream border border-light-grey">
            <div className="flex items-start gap-4">
              <div className="shrink-0 mt-0.5">
                <span className="inline-block border border-cool-grey/30 text-cool-grey rounded text-[10px] px-1.5 py-0.5 font-body">beta</span>
              </div>
              <div>
                <p className="font-body text-[14px] font-semibold text-deep-navy mb-1">What the β label means on your page</p>
                <p className="font-body text-[13px] text-cool-grey leading-[1.65]">
                  Before you claim your page, Daanaa shows a best-guess mission statement inferred from your sector and location.
                  It is marked <span className="border border-cool-grey/30 text-cool-grey rounded text-[10px] px-1 py-0.5">beta</span> so donors know it is a starting point, not your own words.
                  When you claim your page, you replace it with the mission statement you actually want donors to see, and the label is removed.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* How it works steps */}
      <div className="bg-warm-cream py-10 md:py-16 border-t border-light-grey">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
          <div className="max-w-[520px]">
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">How claiming works</span>
            <h2 className="font-display italic text-deep-navy mt-3 text-[32px] leading-[1.1] mb-8">
              Simple. No cost. No middleman.
            </h2>
            <div className="space-y-5">
              <StepDot n={1} label="Find your organization in the directory and click 'Claim your page'" />
              <StepDot n={2} label="Submit the claim form with your name, role, email, and phone number" />
              <StepDot n={3} label="A member of the Daanaa team calls you to verify your identity" />
              <StepDot n={4} label="Enter the 6-digit PIN we give you on the call to unlock your page" />
            </div>
            <p className="mt-8 font-body text-[14px] text-cool-grey leading-[1.6]">
              Claiming is free and open now. Daanaa does not charge organizations to be listed, to claim a page, or to update their information. Ever.
            </p>
          </div>
        </div>
      </div>

      {/* Raise Your Flame — visibility journey */}
      {(() => {
        const STEPS: { tier: TierName; pct: string; description: string; nextStep: string | null }[] = [
          {
            tier: 'Spark',
            pct: '~55% of tax-deductible 501(c)(3)s',
            description: "The IRS recognizes you. You're already in our index.",
            nextStep: 'To reach Candle: file a full annual report with the government. Required for nonprofits earning over $50,000 a year.',
          },
          {
            tier: 'Candle',
            pct: '~27% of tax-deductible 501(c)(3)s',
            description: 'Financial data is on record, but we need a recent one to rank you among peers.',
            nextStep: 'To reach Torch: file an annual report dated 2022 or later. This happens automatically once the IRS publishes it. Nothing for you to do.',
          },
          {
            tier: 'Torch',
            pct: '~17.5% of tax-deductible 501(c)(3)s',
            description: 'You have a current annual report and a financial ranking among similar nonprofits. Add a mission statement and website to your public record for greater visibility.',
            nextStep: 'To reach Beacon: achieve a top-quartile financial score within your peer group and ensure mission, website, and current annual report are all on the public record.',
          },
          {
            tier: 'Beacon',
            pct: '~0.6% of tax-deductible 501(c)(3)s',
            description: 'Complete page. Top-quartile financial score, current annual report, mission, and website all on public record. The most complete picture donors can see.',
            nextStep: null,
          },
        ]
        return (
          <div className="bg-white py-10 md:py-16 border-t border-light-grey">
            <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
              <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">Your visibility journey</span>
              <h2 className="font-display italic text-deep-navy mt-3 text-[32px] leading-[1.1] mb-3">
                Improve your visibility
              </h2>
              <p className="font-body text-[16px] text-cool-grey leading-[1.7] mb-10 max-w-[580px]">
                Visibility is not a grade. It shows how much helpful information a donor can see today. Every group can improve visibility for free, regardless of size, revenue, staffing, or filing type.
              </p>
              <div className="max-w-[640px] space-y-0">
                {STEPS.map((step, i) => (
                  <div key={step.tier} className="flex gap-6">
                    <div className="flex flex-col items-center shrink-0">
                      <div className="mt-1">
                        <LampMark tier={step.tier} size="sm" />
                      </div>
                      {i < STEPS.length - 1 && (
                        <div className="w-px bg-light-grey mt-2 mb-0" style={{ minHeight: '44px' }} />
                      )}
                    </div>
                    <div className="pb-8 last:pb-0 flex-1">
                      <div className="flex items-center gap-2.5 mb-1.5">
                        <span className="font-body text-[16px] font-semibold" style={{ fontFamily: 'Cinzel, serif', color: TIER_COLORS[step.tier] }}>
                          {step.tier}
                        </span>
                        <span className="font-body text-[12px] text-cool-grey">{step.pct}</span>
                      </div>
                      <p className="font-body text-[14px] text-cool-grey leading-[1.6]">{step.description}</p>
                      {step.nextStep && (
                        <p className="mt-2 font-body text-[13px] text-deep-navy/70 leading-[1.5]">
                          {step.nextStep}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )
      })()}

      {/* Claim form */}
      {/* Return portal — signed-in nonprofits jump straight to their editor */}
      <div className="bg-warm-cream border-t border-light-grey py-10">
        <div className="max-w-[520px] mx-auto px-6">
          <p className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase mb-3">
            Already claimed your page?
          </p>
          {!user ? (
            <div className="space-y-2">
              <p className="font-body text-[15px] text-deep-navy mb-3">
                Sign in to go straight to your editor — no PIN needed.
              </p>
              <GoogleSignInButton />
            </div>
          ) : (
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <p className="font-body text-[14px] text-deep-navy font-medium">{user.email}</p>
                <p className="font-body text-[13px] text-cool-grey">Signed in</p>
              </div>
              <button
                onClick={async () => {
                  setPortalLoading(true); setPortalError(null)
                  try {
                    const idToken = await getIdToken()
                    if (!idToken) throw new Error('no token')
                    const orgs = await getMyOrgs(idToken)
                    if (orgs.length === 0) {
                      setPortalError("We don't have a claimed page linked to this account yet. Use the form below to claim your page.")
                      return
                    }
                    const org = orgs[0]
                    const token = await getPortalToken(org.ein, idToken)
                    navigate(`/claim/edit?ein=${encodeURIComponent(org.ein)}&token=${encodeURIComponent(token)}`)
                  } catch {
                    setPortalError('Could not load your page. Please try again.')
                  } finally {
                    setPortalLoading(false)
                  }
                }}
                disabled={portalLoading}
                className="px-5 py-2.5 bg-soft-gold text-deep-navy font-body text-[14px] font-semibold rounded-xl hover:bg-bright-gold disabled:opacity-40 transition-colors"
              >
                {portalLoading ? 'Loading…' : 'Go to my page'}
              </button>
            </div>
          )}
          {portalError && (
            <p className="mt-3 font-body text-[13px] text-red-600">{portalError}</p>
          )}
        </div>
      </div>

      <div id="claim" className="bg-deep-navy py-10 md:py-16 lg:py-20">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
          <div className="max-w-[520px]">
            {submitted ? (
              <div className="py-8">
                <div className="w-12 h-12 rounded-full bg-soft-gold/20 flex items-center justify-center mb-4">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                  </svg>
                </div>
                <h3 className="font-display italic text-warm-cream text-[28px] mb-3">
                  Claim received — we'll call you
                  {orgName && <span className="block text-soft-gold text-[20px] mt-1">{orgName}</span>}
                </h3>
                <p className="font-body text-[15px] text-muted-cream leading-[1.6] mb-4">
                  A member of the Daanaa team will call the number you provided, usually within a few business days, to verify your identity.
                </p>
                <p className="font-body text-[14px] text-muted-cream leading-[1.6] mb-6">
                  On the call we give you a 6-digit PIN. Enter it at{' '}
                  <span className="text-soft-gold">daanaa.org/claim/verify</span>{' '}
                  to unlock your page.
                </p>
                <Link to="/directory" className="inline-block font-body text-[14px] text-soft-gold hover:text-bright-gold transition-colors">
                  Browse the directory →
                </Link>
              </div>
            ) : (
              <>
                <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">
                  Claim your page
                </span>
                <h2 className="font-display italic text-warm-cream mt-3 text-[32px] leading-[1.1] mb-3">
                  {orgName ? orgName : 'Is this your nonprofit?'}
                </h2>
                <p className="font-body text-[16px] text-muted-cream leading-[1.65] mb-6">
                  Submit the form below and a member of the Daanaa team will call you to verify your identity. Once confirmed, your page is yours to update.
                </p>

                {irsAddress && (
                  <div className="mb-6 p-4 rounded-xl border border-soft-gold/20 bg-navy-mid/50">
                    <p className="font-body text-[11px] text-muted-cream uppercase tracking-[0.06em] mb-1">IRS-registered address on file</p>
                    <p className="font-body text-[14px] text-warm-cream">{irsAddress}</p>
                    <p className="font-body text-[11px] text-muted-cream mt-1">IRS-registered address · public record</p>
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-3">
                  <div>
                    <label className="block font-body text-[12px] text-muted-cream mb-1.5">
                      Organization tax ID (EIN) <span className="text-soft-gold">*</span>
                    </label>
                    <input
                      type="text"
                      required
                      value={ein}
                      onChange={e => {
                        const formatted = formatEINInput(e.target.value)
                        setEin(formatted)
                        setOrgName(null)
                        setIrsAddress(null)
                        const digits = formatted.replace(/\D/g, '')
                        if (digits.length === 9) {
                          getOrganization(digits).then(org => {
                            setOrgName(org.organization_name)
                            const addr = [org.street_address, org.CITY, org.STATE, org.zipcode].filter(Boolean).join(', ')
                            setIrsAddress(addr || null)
                          }).catch(() => {})
                        }
                      }}
                      placeholder="12-3456789"
                      className="w-full h-[48px] bg-navy-mid border border-soft-gold/20 text-warm-cream px-4 rounded-xl font-body text-[15px] outline-none focus:border-soft-gold transition-colors placeholder:text-cool-grey"
                    />
                  </div>

                  <div>
                    <label className="block font-body text-[12px] text-muted-cream mb-1.5">
                      Your name <span className="text-soft-gold">*</span>
                    </label>
                    <input
                      type="text"
                      required
                      value={repName}
                      onChange={e => setRepName(e.target.value)}
                      placeholder="First and last name"
                      className="w-full h-[48px] bg-navy-mid border border-soft-gold/20 text-warm-cream px-4 rounded-xl font-body text-[15px] outline-none focus:border-soft-gold transition-colors placeholder:text-cool-grey"
                    />
                  </div>

                  <div>
                    <label className="block font-body text-[12px] text-muted-cream mb-1.5">
                      Your title / role <span className="text-soft-gold">*</span>
                    </label>
                    <input
                      type="text"
                      required
                      value={title}
                      onChange={e => setTitle(e.target.value)}
                      placeholder="Executive Director, President, Board Chair…"
                      className="w-full h-[48px] bg-navy-mid border border-soft-gold/20 text-warm-cream px-4 rounded-xl font-body text-[15px] outline-none focus:border-soft-gold transition-colors placeholder:text-cool-grey"
                    />
                  </div>

                  <div>
                    <label className="block font-body text-[12px] text-muted-cream mb-1.5">
                      Your email <span className="text-soft-gold">*</span>
                    </label>
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      placeholder="you@yourorg.org"
                      className="w-full h-[48px] bg-navy-mid border border-soft-gold/20 text-warm-cream px-4 rounded-xl font-body text-[15px] outline-none focus:border-soft-gold transition-colors placeholder:text-cool-grey"
                    />
                  </div>

                  <div>
                    <label className="block font-body text-[12px] text-muted-cream mb-1.5">
                      Phone number <span className="text-soft-gold">*</span>
                    </label>
                    <input
                      type="tel"
                      required
                      value={phone}
                      onChange={e => setPhone(e.target.value)}
                      placeholder="(555) 000-0000"
                      className="w-full h-[48px] bg-navy-mid border border-soft-gold/20 text-warm-cream px-4 rounded-xl font-body text-[15px] outline-none focus:border-soft-gold transition-colors placeholder:text-cool-grey"
                    />
                    <p className="mt-1.5 font-body text-[11px] text-muted-cream">
                      We will call this number to verify your identity before activating your page. Not shared publicly.
                    </p>
                  </div>

                  {/* Disclosure — who we are and what happens with this form.
                      Text is versioned in docs/CLAIM-ATTESTATIONS.md; if it
                      changes, bump CLAIM_ATTESTATION_VERSION in daanaa_api.py. */}
                  <div className="mt-2 p-4 rounded-xl border border-soft-gold/20 bg-navy-mid/50 space-y-2.5">
                    <p className="font-body text-[12px] font-semibold text-warm-cream">
                      Before you sign, here is who we are and what happens with this form.
                    </p>
                    <p className="font-body text-[12px] text-muted-cream leading-[1.6]">
                      Daanaa is a free public directory of nonprofits built from IRS records.
                      We are not affiliated with the IRS or any government agency. We never
                      handle donations and we never charge organizations for anything.
                    </p>
                    <p className="font-body text-[12px] text-muted-cream leading-[1.6]">
                      We use your phone number and email only to verify that you represent
                      this organization. A member of our team calls you, confirms your role,
                      and gives you a PIN that unlocks your page. Neither is shown publicly.
                    </p>
                    <p className="font-body text-[12px] text-muted-cream leading-[1.6]">
                      We keep a record of this submission, including the statements you check
                      below and the time you checked them, so our verification process can
                      stand up to review. Claiming a page gives you control over how this
                      organization appears to donors, which is why we ask you to confirm the
                      two statements below before submitting.
                    </p>
                  </div>

                  {/* Attestation 1 — authority */}
                  <label className="flex items-start gap-3 cursor-pointer pt-2">
                    <input
                      type="checkbox"
                      required
                      checked={attested}
                      onChange={e => setAttested(e.target.checked)}
                      className="mt-0.5 h-4 w-4 rounded border-soft-gold/30 text-soft-gold focus:ring-soft-gold shrink-0"
                    />
                    <span className="font-body text-[12px] text-muted-cream leading-[1.6]">
                      I am an authorized representative of <strong className="text-warm-cream">{orgName || 'this organization'}</strong> and have the authority to manage its public presence on third-party platforms.
                    </span>
                  </label>

                  {/* Attestation 2 — legal weight */}
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      required
                      checked={attestedLegal}
                      onChange={e => setAttestedLegal(e.target.checked)}
                      className="mt-0.5 h-4 w-4 rounded border-soft-gold/30 text-soft-gold focus:ring-soft-gold shrink-0"
                    />
                    <span className="font-body text-[12px] text-muted-cream leading-[1.6]">
                      I understand that submitting false or misleading information is a federal offense under{' '}
                      <strong className="text-warm-cream">18 U.S.C. § 1001</strong> and may result in permanent removal from Daanaa and referral to relevant authorities.
                    </span>
                  </label>

                  {error && (
                    <p className="font-body text-[13px] text-red-400 leading-[1.5]">{error}</p>
                  )}

                  <button
                    type="submit"
                    disabled={submitting || !attested || !attestedLegal}
                    className="w-full h-[48px] bg-soft-gold text-deep-navy font-body text-[14px] font-semibold rounded-full hover:bg-bright-gold transition-colors disabled:opacity-60"
                  >
                    {submitting ? 'Submitting…' : 'Submit claim request'}
                  </button>
                </form>
                <p className="mt-4 font-body text-[11px] text-muted-cream leading-[1.5]">
                  A member of the Daanaa team will call the number you provided to verify your identity. Once confirmed, your page goes live. No cost to you.
                </p>
              </>
            )}
          </div>
        </div>
      </div>

    </div>
  )
}
