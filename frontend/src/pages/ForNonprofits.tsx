import { useState } from 'react'
import { Link } from 'react-router-dom'
import { submitWaitlist } from '../data/api'
import { usePageMeta } from '../hooks/usePageMeta'
import LampMark from '../components/LampMark'
import { TIER_COLORS } from '../components/TrustBadge'
import type { TierName } from '../components/TrustBadge'

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
  usePageMeta('For Nonprofits', 'Claim your free MERIT profile. Nonprofits that add mission, website, and current financials rise through the visibility tiers.')
  const [email, setEmail] = useState('')
  const [ein, setEin] = useState('')
  const [submitted, setSubmitted] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!email.trim()) return
    try {
      await submitWaitlist(email.trim(), 'claiming', ein.trim() || undefined)
    } catch {
      const requests = JSON.parse(localStorage.getItem('merit_claim_requests') || '[]')
      requests.push({ email: email.trim(), ein: ein.trim(), requestedAt: new Date().toISOString() })
      localStorage.setItem('merit_claim_requests', JSON.stringify(requests))
    }
    setSubmitted(true)
  }

  return (
    <div className="min-h-[100dvh]">
      {/* Header */}
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 pt-12 pb-20">
          <div className="flex items-center gap-2 mb-6">
            <Link to="/" className="font-body text-[12px] tracking-[0.02em] text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream/50">/</span>
            <span className="font-body text-[12px] text-muted-cream">For Nonprofits</span>
          </div>

          <div className="max-w-[680px]">
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">For organizations</span>
            <h1 className="font-display italic text-warm-cream mt-3 leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(32px, 5vw, 60px)' }}>
              Your public record may already be listed. Add the story only you can tell.
            </h1>
            <p className="mt-5 font-body text-[18px] leading-[1.65] text-muted-cream">
              MERIT helps donors find public nonprofit records and giving paths. Claim your page for free to add your mission, programs, service area, leadership, impact notes, events, volunteer opportunities, and official giving links.
            </p>
            <a href="#claim" className="mt-8 inline-flex items-center gap-2 px-8 py-[14px] rounded-full bg-soft-gold text-deep-navy font-body text-[14px] font-semibold hover:bg-bright-gold transition-colors">
              Join the waitlist
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
            </a>
          </div>
        </div>
      </div>

      {/* What you get */}
      <div className="bg-warm-cream py-16 md:py-20">
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
                description: 'Add your mission statement, program descriptions, and the people you serve — in your words, clearly marked as written by you and separate from government records.',
              },
              {
                n: 2,
                title: 'Leadership team',
                description: 'Introduce your executive director and board. Donors and volunteers want to know who leads the organization — and that\'s not in public IRS records.',
              },
              {
                n: 3,
                title: 'Impact metrics',
                description: 'Share the numbers that matter to you — meals served, families housed, students tutored. Context that no government report can provide.',
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
                description: 'Access vetted vendors — software, printing, supplies — negotiated at nonprofit rates. Lower your costs so more goes to your mission.',
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
      <div className="bg-white py-16 border-t border-light-grey">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
          <div className="max-w-[680px]">
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">Trust by design</span>
            <h2 className="font-display italic text-deep-navy mt-3 text-[32px] leading-[1.1] mb-6">
              Government records and your story, clearly separated
            </h2>
            <p className="font-body text-[16px] text-cool-grey leading-[1.7] mb-4">
              MERIT keeps two distinct layers on every profile. The IRS layer, which covers revenue, category, and tax status, is public data we display but you cannot edit. Your claimed layer, which covers mission, programs, impact, and leadership, is your own voice, clearly labeled.
            </p>
            <p className="font-body text-[16px] text-cool-grey leading-[1.7]">
              Donors can always tell which is which. Keeping these two layers separate is how they trust what they read — and how you stay in control of your own story.
            </p>
          </div>

          <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 gap-6 max-w-[680px]">
            <div className="p-5 bg-warm-cream rounded-xl border border-light-grey">
              <p className="font-body text-[11px] tracking-[0.06em] text-soft-gold uppercase font-medium mb-3">IRS public data</p>
              <ul className="space-y-2 font-body text-[13px] text-cool-grey">
                {['Legal name', 'Nonprofit category', 'Revenue from IRS filings', 'MERIT financial ranking', 'Year & data source'].map(i => (
                  <li key={i} className="flex items-center gap-2">
                    <span className="w-1 h-1 rounded-full bg-cool-grey/40 shrink-0" />{i}
                  </li>
                ))}
              </ul>
              <p className="mt-3 font-body text-[11px] text-cool-grey/60">Not editable · Always shown</p>
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
              <p className="mt-3 font-body text-[11px] text-cool-grey/60">Labeled "written by you" · Controlled by you</p>
            </div>
          </div>
        </div>
      </div>

      {/* How it works steps */}
      <div className="bg-warm-cream py-16 border-t border-light-grey">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
          <div className="max-w-[520px]">
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">How claiming works</span>
            <h2 className="font-display italic text-deep-navy mt-3 text-[32px] leading-[1.1] mb-8">
              Simple. No cost. No middleman.
            </h2>
            <div className="space-y-5">
              <StepDot n={1} label="Search for your organization in the directory" />
              <StepDot n={2} label="Click 'Claim this page' on your profile" />
              <StepDot n={3} label="Verify via your organization's tax ID number and email domain" />
              <StepDot n={4} label="Edit your profile directly. Changes go live immediately" />
            </div>
            <p className="mt-8 font-body text-[14px] text-cool-grey leading-[1.6]">
              Claiming is free. MERIT does not charge organizations to be listed, to claim a page, or to update their information. Ever.
            </p>
          </div>
        </div>
      </div>

      {/* Raise Your Flame — visibility journey */}
      {(() => {
        const STEPS: { tier: TierName; pct: string; description: string; nextStep: string | null }[] = [
          {
            tier: 'Spark',
            pct: '0.4% of all nonprofits',
            description: "The IRS recognizes you. You're already in our index.",
            nextStep: 'To reach Glow: file a full annual report with the government. Required for nonprofits earning over $50,000 a year.',
          },
          {
            tier: 'Glow',
            pct: '21% of all nonprofits',
            description: 'Financial data is on record, but we need a recent one to rank you among peers.',
            nextStep: 'To reach Flame: file an annual report dated 2022 or later. This happens automatically once the IRS publishes it — nothing to do with us.',
          },
          {
            tier: 'Flame',
            pct: '75% of all nonprofits',
            description: "You have a current annual report and a financial ranking among similar nonprofits. A mission statement or website isn't yet on the public record.",
            nextStep: 'To reach Lantern: get your mission statement and website into the public record. Claiming your MERIT page is the fastest way.',
          },
          {
            tier: 'Lantern',
            pct: '2% of all nonprofits',
            description: 'Your current annual report, mission, and website are all on the public record. A strong, complete picture.',
            nextStep: 'To reach Beacon: add mission, service area, programs, leadership, and giving path. Visibility improves as your profile becomes more complete.',
          },
          {
            tier: 'Beacon',
            pct: '1% of all nonprofits',
            description: 'Complete profile. Mission, giving path, service area, programs, and leadership all on public record. The most complete picture donors can see.',
            nextStep: null,
          },
        ]
        return (
          <div className="bg-white py-16 border-t border-light-grey">
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
                        <span className="font-body text-[12px] text-cool-grey/50">{step.pct}</span>
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

      {/* Claim interest form */}
      <div id="claim" className="bg-deep-navy py-16 md:py-20">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
          <div className="max-w-[520px]">
            {submitted ? (
              <div className="text-center py-8">
                <div className="w-12 h-12 rounded-full bg-soft-gold/20 flex items-center justify-center mx-auto mb-4">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </div>
                <h3 className="font-display italic text-warm-cream text-[24px] mb-2">You're on the list</h3>
                <p className="font-body text-[15px] text-muted-cream leading-[1.6]">
                  We'll email you as soon as claiming opens. In the meantime, find your organization in the directory.
                </p>
                <Link to="/directory" className="mt-6 inline-block font-body text-[14px] text-soft-gold hover:text-bright-gold transition-colors">
                  Browse the directory →
                </Link>
              </div>
            ) : (
              <>
                <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">Get early access</span>
                <h2 className="font-display italic text-warm-cream mt-3 text-[32px] leading-[1.1] mb-3">
                  Claiming opens soon
                </h2>
                <p className="font-body text-[16px] text-muted-cream leading-[1.65] mb-8">
                  We're rolling out organization accounts in phases. Leave your email and we'll notify you when your organization can claim its page.
                </p>
                <form onSubmit={handleSubmit} className="space-y-3">
                  <div>
                    <label className="block font-body text-[12px] text-muted-cream/70 mb-1.5">Work email <span className="text-soft-gold">*</span></label>
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      placeholder="you@organization.org"
                      className="w-full h-[48px] bg-navy-mid border border-soft-gold/20 text-warm-cream px-4 rounded-xl font-body text-[15px] outline-none focus:border-soft-gold transition-colors placeholder:text-cool-grey"
                    />
                  </div>
                  <div>
                    <label className="block font-body text-[12px] text-muted-cream/70 mb-1.5">Organization tax ID — EIN (optional)</label>
                    <input
                      type="text"
                      value={ein}
                      onChange={e => setEin(e.target.value)}
                      placeholder="XX-XXXXXXX"
                      className="w-full h-[48px] bg-navy-mid border border-soft-gold/20 text-warm-cream px-4 rounded-xl font-body text-[15px] outline-none focus:border-soft-gold transition-colors placeholder:text-cool-grey"
                    />
                  </div>
                  <button
                    type="submit"
                    className="w-full h-[48px] bg-soft-gold text-deep-navy font-body text-[14px] font-semibold rounded-full hover:bg-bright-gold transition-colors"
                  >
                    Notify me when claiming opens
                  </button>
                </form>
                <p className="mt-4 font-body text-[11px] text-muted-cream/40 leading-[1.5]">
                  We'll only use your email to notify you when claiming opens. No marketing.
                </p>
              </>
            )}
          </div>
        </div>
      </div>

    </div>
  )
}
