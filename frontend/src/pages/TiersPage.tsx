import { Link } from 'react-router-dom'
import LampMark from '../components/LampMark'
import { TIER_COLORS, TIER_MICROCOPY, getNextTierPath } from '../components/TrustBadge'
import type { TierName } from '../components/TrustBadge'
import { usePageMeta } from '../hooks/usePageMeta'

const TIERS: {
  name: TierName
  pct: string
  count: string
  criteria: { label: string; met: boolean }[]
}[] = [
  {
    name: 'Beacon',
    pct: '0.7%',
    count: '~13,500',
    criteria: [
      { label: 'Recognized as a nonprofit by the IRS', met: true },
      { label: 'Annual financial report on file (2022 or later)', met: true },
      { label: 'Top-quartile financial context score (≥75th percentile)', met: true },
      { label: 'Mission statement on public record', met: true },
      { label: 'Active website on record', met: true },
    ],
  },
  {
    name: 'Lantern',
    pct: '1.5%',
    count: '~28,000',
    criteria: [
      { label: 'Recognized as a nonprofit by the IRS', met: true },
      { label: 'Annual financial report on file (2022 or later)', met: true },
      { label: 'Financial context score assigned', met: true },
      { label: 'Mission statement on public record', met: true },
      { label: 'Active website on record', met: true },
    ],
  },
  {
    name: 'Flame',
    pct: '26.9%',
    count: '~487,000',
    criteria: [
      { label: 'Recognized as a nonprofit by the IRS', met: true },
      { label: 'Annual financial report on file (2022 or later)', met: true },
      { label: 'Financial context score assigned', met: true },
      { label: 'Mission statement on public record', met: false },
      { label: 'Active website on record', met: false },
    ],
  },
  {
    name: 'Glow',
    pct: '40.6%',
    count: '~736,000',
    criteria: [
      { label: 'Recognized as a nonprofit by the IRS', met: true },
      { label: 'Annual financial report on file (2022 or later) or revenue on record', met: true },
      { label: 'Financial context score assigned', met: false },
      { label: 'Mission statement on public record', met: false },
      { label: 'Active website on record', met: false },
    ],
  },
  {
    name: 'Seed',
    pct: '30.2%',
    count: '~546,000',
    criteria: [
      { label: 'Recognized as a nonprofit by the IRS', met: true },
      { label: 'Annual financial report on file (2022 or later)', met: false },
      { label: 'Revenue data on record', met: false },
      { label: 'Financial context score assigned', met: false },
      { label: 'Mission statement on public record', met: false },
      { label: 'Active website on record', met: false },
    ],
  },
]

const CRITERIA_ICON_MET = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#B8902F" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
)
const CRITERIA_ICON_UNMET = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#D1D5DB" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="5" y1="12" x2="19" y2="12"/>
  </svg>
)

export default function TiersPage() {
  usePageMeta('Visibility Levels', 'Understand the five Daanaa visibility levels (Beacon, Lantern, Flame, Glow, and Spark) and what each means for the nonprofits the IRS recognizes.')
  return (
    <div className="min-h-[100dvh]">

      {/* Hero */}
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 pt-12 pb-16">
          <div className="flex items-center gap-2 mb-6">
            <Link to="/" className="font-body text-[12px] text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream/40">/</span>
            <span className="font-body text-[12px] text-muted-cream">Visibility Levels</span>
          </div>
          <div className="flex items-start gap-6">
            <div className="hidden sm:flex flex-col gap-1.5 pt-2 shrink-0">
              {(['Beacon','Lantern','Flame','Glow','Seed'] as TierName[]).map(t => (
                <LampMark key={t} tier={t} size="xs" />
              ))}
            </div>
            <div className="max-w-[640px]">
              <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">How much information is available</span>
              <h1 className="font-display italic text-warm-cream mt-3 leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(32px, 5vw, 60px)' }}>
                Visibility Levels
              </h1>
              <p className="mt-5 font-body text-[17px] leading-[1.65] text-muted-cream">
                Visibility levels show how much helpful information a donor can see today. They are not a grade, endorsement, or measure of impact.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="bg-warm-cream py-16 md:py-20">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">

          {/* Quick explainer */}
          <div className="max-w-[720px] mb-14">
            <p className="font-body text-[16px] leading-[1.7] text-cool-grey">
              The government publishes financial reports from nonprofits, but how much is available varies widely. Some organizations have years of detailed records; others are registered but have nothing else on file. Daanaa's five tiers make that gap visible at a glance, so you know what you're working with before you give.
            </p>
            <p className="font-body text-[16px] leading-[1.7] text-cool-grey mt-4">
              Tiers are calculated automatically from public records and updated monthly. No organization can pay to change its tier.
            </p>
          </div>

          {/* Tier cards */}
          <div className="space-y-6">
            {TIERS.map(({ name, pct, count, criteria }) => {
              const color = TIER_COLORS[name]
              const nextPath = getNextTierPath(name)

              return (
                <div
                  key={name}
                  className="bg-white rounded-2xl border border-light-grey overflow-hidden"
                >
                  {/* Tier header */}
                  <div className="flex items-start gap-5 p-6 md:p-8">
                    <LampMark tier={name} size="lg" className="shrink-0 mt-1" />

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 flex-wrap">
                        <h2
                          className="font-display text-[28px] leading-none"
                          style={{ fontFamily: 'Cinzel, serif', color }}
                        >
                          {name}
                        </h2>
                        <span
                          className="font-body text-[11px] font-semibold px-2.5 py-0.5 rounded-full"
                          style={{ backgroundColor: `${color}15`, color }}
                        >
                          {pct} of indexed 501(c)(3)s · {count}
                        </span>
                      </div>
                      <p className="mt-2.5 font-body text-[15px] leading-[1.6] text-cool-grey max-w-[560px]">
                        {TIER_MICROCOPY[name]}
                      </p>
                    </div>

                    <Link
                      to={name === 'Seed' ? '/directory' : `/directory?min_tier=${name}`}
                      className="hidden md:inline-flex items-center gap-1.5 shrink-0 font-body text-[13px] font-semibold px-4 py-2 rounded-full border transition-all duration-150 hover:bg-soft-gold/10"
                      style={{ borderColor: `${color}50`, color }}
                    >
                      Browse {name}
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="9 18 15 12 9 6"/>
                      </svg>
                    </Link>
                  </div>

                  {/* Criteria + next tier */}
                  <div className="border-t border-light-grey px-6 md:px-8 py-5 flex flex-col md:flex-row gap-6 md:gap-10 bg-warm-cream/40">
                    {/* Criteria list */}
                    <div className="flex-1">
                      <p className="font-body text-[10px] font-semibold tracking-[0.08em] text-cool-grey/50 uppercase mb-3">
                        Criteria at this tier
                      </p>
                      <div className="space-y-2">
                        {criteria.map(c => (
                          <div key={c.label} className="flex items-center gap-2.5">
                            <span className="shrink-0">{c.met ? CRITERIA_ICON_MET : CRITERIA_ICON_UNMET}</span>
                            <span
                              className="font-body text-[13px]"
                              style={{ color: c.met ? '#374151' : '#9CA3AF' }}
                            >
                              {c.label}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Next tier path or top badge */}
                    <div className="md:w-[280px] shrink-0">
                      {nextPath ? (
                        <>
                          <p className="font-body text-[10px] font-semibold tracking-[0.08em] text-cool-grey/50 uppercase mb-3">
                            Path to next tier
                          </p>
                          <p className="font-body text-[13px] leading-[1.6] text-cool-grey">
                            {nextPath}
                          </p>
                        </>
                      ) : (
                        <div className="flex items-start gap-2.5">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0 mt-0.5">
                            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                          </svg>
                          <p className="font-body text-[13px] leading-[1.6]" style={{ color }}>
                            Highest tier. All public data criteria met.
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Mobile browse link */}
                  <div className="md:hidden px-6 pb-5">
                    <Link
                      to={name === 'Seed' ? '/directory' : `/directory?min_tier=${name}`}
                      className="inline-flex items-center gap-1.5 font-body text-[13px] font-semibold"
                      style={{ color }}
                    >
                      Browse {name} organizations →
                    </Link>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Disclaimer section */}
          <div className="mt-16 max-w-[720px]">
            <h2 className="font-display italic text-deep-navy leading-[1.1]" style={{ fontSize: 'clamp(22px, 3vw, 34px)' }}>
              A lower visibility level is not a grade
            </h2>
            <div className="mt-4 space-y-4 font-body text-[16px] text-cool-grey leading-[1.7]">
              <p>
                A tiny organization running an extraordinary neighborhood pantry on a 990-N postcard will show as Seed or Ember. That reflects what the IRS collects. A 990-N reports only that the organization exists, not its financials. It says nothing about their effectiveness, their importance to the communities they serve, or whether they deserve your support.
              </p>
              <p>
                Tiers answer one question: <em>how much public data backs this listing?</em> They are a starting point for research, not a verdict. Use them to calibrate how much additional due diligence to apply, not to rank organizations against each other.
              </p>
            </div>

            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                to="/how-it-works"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-deep-navy text-warm-cream font-body text-[13px] font-semibold hover:bg-navy-mid transition-colors"
              >
                How scoring works
              </Link>
              <Link
                to="/directory"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full border border-soft-gold/40 text-soft-gold font-body text-[13px] font-semibold hover:bg-soft-gold/10 transition-colors"
              >
                Browse the directory
              </Link>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
