import { useState, useMemo, type ReactNode } from 'react'
import { usePageMeta } from '../hooks/usePageMeta'
import { Link, useNavigate } from 'react-router-dom'
import SearchBar from '../components/SearchBar'
import LampMark from '../components/LampMark'
import { useApi } from '../hooks/useApi'
import { getStats, getCategories } from '../data/api'
import { TIER_COLORS } from '../components/TrustBadge'
import type { TierName } from '../components/TrustBadge'
import { NTEE_CATEGORIES } from '../data/ntee'
import { getFeaturedCategory } from '../data/featuredCategory'
import ImpactWidget from '../components/ImpactWidget'

const TIER_STRIP: { name: TierName; pct: string; blurb: string }[] = [
  { name: 'Beacon',  pct: '0.6%',  blurb: 'Complete public data: financial reports, mission statement, website, and current Form 990' },
  { name: 'Torch',   pct: '15.6%', blurb: 'Strong public data: financial context available, recent filings, organizational information' },
  { name: 'Candle',  pct: '28.7%', blurb: 'Moderate public data: some financial information, basic organizational records' },
  { name: 'Spark',   pct: '55.1%', blurb: 'Recognized nonprofit with minimal public information available' },
]

// Returns the week number anchored to Monday so all users see the same shuffle each week
function weekSeed(): number {
  const now = new Date()
  const dayOfWeek = (now.getUTCDay() + 6) % 7 // 0=Mon … 6=Sun
  const mondayMs = now.getTime() - dayOfWeek * 86_400_000
  return Math.floor(mondayMs / (7 * 86_400_000))
}

function seededShuffle<T>(arr: T[], seed: number): T[] {
  let s = seed
  const rand = () => {
    s ^= s << 13; s ^= s >> 17; s ^= s << 5
    return (s >>> 0) / 0x100000000
  }
  const result = [...arr]
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1))
    ;[result[i], result[j]] = [result[j], result[i]]
  }
  return result
}

// ─── Hero ────────────────────────────────────────────────────────────────────
function HeroSection() {
  const { data: stats } = useApi(() => getStats(), [])
  const orgCount = stats?.total_organizations ?? 1_800_000
  const [query, setQuery] = useState('')
  const navigate = useNavigate()

  const handleSearch = (q: string) => {
    navigate(q.trim() ? `/directory?q=${encodeURIComponent(q)}` : '/directory')
  }

  return (
    <section className="bg-deep-navy pt-[72px]">
      <div className="max-w-[760px] mx-auto px-6 pt-24 pb-20 md:pt-32 md:pb-28 text-center">

        {/* Headline */}
        <h1
          className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.025em]"
          style={{ fontSize: 'clamp(48px, 7vw, 80px)' }}
        >
          See the overlooked. Give with heart.
        </h1>

        {/* Subheadline */}
        <p className="mt-8 font-body text-[18px] leading-[1.65] max-w-[720px] mx-auto" style={{ color: 'rgba(245,240,235,0.80)' }}>
          Daanaa helps you explore U.S. nonprofits using public records, presented with context and respect. No ads, no rankings, no pressure to give.
        </p>

        {/* CTAs */}
        <div className="mt-10 flex items-center justify-center gap-3 flex-wrap">
          <Link
            to="/directory"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-full bg-soft-gold text-deep-navy font-body text-[15px] font-bold hover:bg-bright-gold transition-colors shadow-lg"
          >
            Start Discovering
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="9 18 15 12 9 6"/>
            </svg>
          </Link>
          <Link
            to="/methodology"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-full border-2 border-soft-gold text-soft-gold font-body text-[15px] font-medium hover:bg-soft-gold/10 transition-colors"
          >
            See Methodology
          </Link>
        </div>

        {/* Trust line */}
        <p className="mt-8 font-body text-[14px]" style={{ color: 'rgba(245,240,235,0.60)' }}>
          Independent. Built on public records. Not a rating agency.
        </p>
      </div>
    </section>
  )
}

// ─── What Daanaa Does ────────────────────────────────────────────────────────
function WhatDaanaaDoesSection() {
  return (
    <section className="bg-warm-cream py-16 md:py-20">
      <div className="max-w-[1120px] mx-auto px-6 md:px-12">
        <div className="mb-12">
          <h2 className="font-display italic text-deep-navy text-[32px] md:text-[40px] leading-[1.15] tracking-[-0.01em]">
            What Daanaa does
          </h2>
          <p className="mt-6 font-body text-[16px] text-cool-grey leading-[1.65] max-w-[720px]">
            Daanaa organizes public nonprofit information so people can discover organizations with more context. It does not rank nonprofits, process donations, or tell people where they must give.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { title: 'Discover causes', body: 'Search by cause, place, or community need.' },
            { title: 'Understand context', body: 'View public information with peer context, not a one size fits all rating.' },
            { title: 'Connect directly', body: 'When available, Daanaa points you to the organization\'s own official website.' },
          ].map(card => (
            <div key={card.title} className="bg-white border border-light-grey rounded-2xl p-6 md:p-8">
              <h3 className="font-display text-deep-navy text-[20px] md:text-[22px]">{card.title}</h3>
              <p className="mt-3 font-body text-[15px] text-cool-grey leading-[1.6]">{card.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ─── How Discovery Works ──────────────────────────────────────────────────────
function HowDiscoveryWorks() {
  return (
    <section className="bg-white py-16 md:py-20 border-b border-light-grey">
      <div className="max-w-[1120px] mx-auto px-6 md:px-12">
        <div className="max-w-[720px]">
          <h2 className="font-display italic text-deep-navy text-[28px] md:text-[32px] leading-[1.15] tracking-[-0.01em]">
            Discovery works when you have context
          </h2>
          <p className="mt-6 font-body text-[16px] text-cool-grey leading-[1.65]">
            The same financial information means something different depending on the organization's size, mission, and peer group. Daanaa shows you that context instead of a single global score.
          </p>
        </div>
      </div>
    </section>
  )
}

// ─── Peer Financial Context ───────────────────────────────────────────────────
function PeerFinancialContextSection() {
  return (
    <section className="bg-[#F8F5F0] py-16 md:py-20">
      <div className="max-w-[1120px] mx-auto px-6 md:px-12">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="font-display italic text-deep-navy text-[32px] md:text-[40px] leading-[1.15] tracking-[-0.01em]">
              Peer Financial Context
            </h2>
            <p className="mt-6 font-body text-[16px] text-cool-grey leading-[1.65]">
              Peer Financial Context shows public financial information within comparable peer groups. It is designed to add context, not to rate, rank, or recommend organizations.
            </p>
            <p className="mt-4 font-body text-[16px] text-cool-grey leading-[1.65]">
              This approach respects the fact that a small community organization and a large national nonprofit may both be thriving—they just have different financial profiles.
            </p>
            <Link
              to="/methodology"
              className="mt-6 inline-flex items-center gap-2 font-body text-[14px] font-medium text-soft-gold hover:text-bright-gold transition-colors"
            >
              Learn more about methodology →
            </Link>
          </div>
          <div className="bg-white border border-light-grey rounded-2xl p-8">
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="shrink-0 mt-0.5">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                <div>
                  <p className="font-body text-[14px] font-semibold text-deep-navy">Based on public records</p>
                  <p className="font-body text-[13px] text-cool-grey mt-1">IRS, NCCS, and ProPublica data only</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="shrink-0 mt-0.5">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                <div>
                  <p className="font-body text-[14px] font-semibold text-deep-navy">Peer-group based</p>
                  <p className="font-body text-[13px] text-cool-grey mt-1">Compared within similar organizations</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="shrink-0 mt-0.5">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                <div>
                  <p className="font-body text-[14px] font-semibold text-deep-navy">Not a rating</p>
                  <p className="font-body text-[13px] text-cool-grey mt-1">Context, not judgment or endorsement</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

// ─── Stewardship ─────────────────────────────────────────────────────────────
function StewardshipSection() {
  return (
    <section className="bg-deep-navy py-16 md:py-20">
      <div className="max-w-[1120px] mx-auto px-6 md:px-12">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="font-display italic text-warm-cream text-[32px] md:text-[40px] leading-[1.15] tracking-[-0.01em]">
              Built on stewardship
            </h2>
            <p className="mt-6 font-body text-[16px] leading-[1.65]" style={{ color: 'rgba(245,240,235,0.80)' }}>
              Stewardship means caring for donors, organizations, and the public record at the same time.
            </p>
            <p className="mt-4 font-body text-[16px] leading-[1.65]" style={{ color: 'rgba(245,240,235,0.75)' }}>
              Daanaa is built to support discovery without turning giving into judgment. We avoid ranking language, welcome corrections, protect privacy, and remain independent.
            </p>
            <Link
              to="/stewardship"
              className="mt-6 inline-flex items-center gap-2 font-body text-[14px] font-medium text-soft-gold hover:text-bright-gold transition-colors"
            >
              See our stewardship principles →
            </Link>
          </div>
          <div className="space-y-4">
            {[
              'We do not rank nonprofits',
              'We do not process donations',
              'We do not sell donor data',
              'We remain independent',
              'We welcome corrections',
              'We protect privacy',
            ].map(principle => (
              <div key={principle} className="flex items-start gap-3">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="shrink-0 mt-0.5">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                <p className="font-body text-[16px] text-warm-cream leading-[1.5]">{principle}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

// ─── Final CTA ────────────────────────────────────────────────────────────────
function FinalCTA() {
  const { data: stats } = useApi(() => getStats(), [])
  const countLabel = stats?.total_organizations
    ? `${(Math.floor(stats.total_organizations / 1000) * 1000).toLocaleString()}+`
    : '1,800,000+'

  return (
    <section className="bg-white border-t border-light-grey py-12 md:py-16">
      <div className="max-w-[1120px] mx-auto px-6 md:px-12 text-center">
        <h2
          className="font-display italic text-deep-navy leading-[1.15] tracking-[-0.01em]"
          style={{ fontSize: 'clamp(28px, 4vw, 44px)' }}
        >
          Ready to discover?
        </h2>
        <p className="mt-6 font-body text-[16px] text-cool-grey max-w-[720px] mx-auto leading-[1.65]">
          Search {countLabel} organizations by cause, place, or public information. Start with something you care about.
        </p>
        <div className="mt-8 flex items-center justify-center gap-3 flex-wrap">
          <Link
            to="/directory"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-full bg-soft-gold text-deep-navy font-body text-[15px] font-bold hover:bg-bright-gold transition-colors shadow-md"
          >
            Start Discovering
          </Link>
          <Link
            to="/guides"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-full border-2 border-deep-navy/20 text-deep-navy font-body text-[15px] font-medium hover:border-deep-navy/40 hover:bg-deep-navy/5 transition-all"
          >
            See Guides
          </Link>
        </div>
      </div>
    </section>
  )
}

// ─── Featured cause banner (bi-weekly rotation) ───────────────────────────────
function FeaturedCause() {
  const featured = useMemo(() => getFeaturedCategory(), [])
  const cat = NTEE_CATEGORIES.find(c => c.id === featured.id)
  if (!cat) return null
  return (
    <section className="bg-deep-navy border-b border-white/10">
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12 py-9 md:py-12">
        <div className="flex flex-col md:flex-row items-center gap-7 md:gap-11">
          {/* Diamond logo */}
          <Link to={`/causes/${cat.id}`} className="shrink-0">
            <img
              src={featured.logo}
              alt={`${cat.name} cause`}
              className="w-24 h-24 md:w-32 md:h-32 object-contain drop-shadow-[0_6px_24px_rgba(201,169,110,0.28)]"
            />
          </Link>

          {/* Copy */}
          <div className="flex-1 min-w-0 text-center md:text-left">
            <p className="font-body text-[12px] font-semibold tracking-[0.12em] text-soft-gold uppercase mb-2">
              Featured cause
            </p>
            <h2
              className="font-display italic text-warm-cream leading-tight tracking-[-0.015em]"
              style={{ fontSize: 'clamp(26px, 3.2vw, 40px)' }}
            >
              {cat.name}
            </h2>
            <p className="font-display italic text-pale-gold/90 mt-2 text-[17px] md:text-[19px]">
              {featured.tagline}
            </p>
            {featured.focus && (
              <div className="flex flex-wrap justify-center md:justify-start gap-2 mt-4">
                {featured.focus.map(f => (
                  <span
                    key={f}
                    className="font-body text-[12px] px-3 py-1 rounded-full bg-soft-gold/10 border border-soft-gold/25 text-pale-gold"
                  >
                    {f}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* CTA */}
          <Link
            to={`/causes/${cat.id}`}
            className="shrink-0 inline-flex items-center gap-2.5 px-7 py-3.5 rounded-full bg-soft-gold text-deep-navy font-body text-[14px] font-bold hover:bg-bright-gold transition-colors shadow-lg"
          >
            Explore {cat.name}
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </Link>
        </div>
      </div>
    </section>
  )
}

// ─── Find Causes ──────────────────────────────────────────────────────────────
function BrowseCauses() {
  const cats = useMemo(() => seededShuffle(NTEE_CATEGORIES, weekSeed()), [])
  const { data: catData } = useApi(() => getCategories(), [])
  const orgCountByCode = useMemo(() => {
    const map: Record<string, number> = {}
    catData?.categories.forEach(c => { map[c.code] = c.count })
    return map
  }, [catData])

  return (
    <section className="bg-[#F8F5F0] border-t border-light-grey py-14 md:py-20">
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12">

        {/* Section header */}
        <div className="mb-12">
          <p className="font-body text-[12px] font-semibold tracking-[0.08em] text-soft-gold uppercase mb-2">
            Find by Cause
          </p>
          <h2
            className="font-display italic text-deep-navy leading-tight tracking-[-0.015em]"
            style={{ fontSize: 'clamp(32px, 4vw, 48px)' }}
          >
            Organizations making change
          </h2>
          <p className="mt-4 font-body text-[16px] text-cool-grey leading-[1.6] max-w-[640px]">
            Choose a cause that matters to you. See the nonprofits working on it, explore their public record, and visit their official website.
          </p>
        </div>

        {/* Cause grid — 2 cols mobile · 3 cols tablet · 4 cols desktop */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 md:gap-4">
          {cats.map(cat => {
            const count = orgCountByCode[cat.id]
            return (
              <Link
                key={cat.id}
                to={`/category/${cat.id}`}
                className="group flex flex-col justify-between bg-white border border-light-grey rounded-xl px-5 py-5 hover:border-soft-gold/40 hover:shadow-md transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-soft-gold"
                style={{ minHeight: '100px' }}
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="font-body text-[15px] font-semibold text-deep-navy leading-snug tracking-[0.01em] group-hover:text-soft-gold transition-colors duration-150">
                    {cat.name}
                  </span>
                  <svg
                    width="8" height="12" viewBox="0 0 8 12"
                    className="shrink-0 mt-[3px] opacity-25 group-hover:opacity-100 transition-opacity duration-200"
                  >
                    <polygon points="4,0 8,6 4,12 0,6" fill="#C9A96E"/>
                  </svg>
                </div>
                <span className="font-body text-[13px] text-cool-grey mt-3">
                  {count != null ? `${count.toLocaleString()} organizations` : `${cat.subs.length} subcategories`}
                </span>
              </Link>
            )
          })}
        </div>

        {/* Link to see all */}
        <div className="mt-10 text-center">
          <Link
            to="/directory"
            className="inline-flex items-center gap-2 font-body text-[14px] text-soft-gold hover:text-bright-gold transition-colors"
          >
            See all causes and search organizations
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="9 18 15 12 9 6"/>
            </svg>
          </Link>
        </div>
      </div>
    </section>
  )
}

// ─── Stats bar ────────────────────────────────────────────────────────────────
function StatsBar() {
  const { data: stats } = useApi(() => getStats(), [])
  const count = stats?.total_organizations ?? 1_600_000
  const finRecords = stats?.financial_records ?? 1_785_000
  // at_risk bucket in stats API now covers 0–6 months (matches the directory filter threshold)
  const needsFundingSoon = (stats?.reserve_health?.insolvent ?? 0) + (stats?.reserve_health?.at_risk ?? 0)

  const items: { icon: ReactNode; value: string; label: string; to?: string }[] = [
    {
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4ADE80" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
      ),
      value: `${count.toLocaleString()}+`,
      label: 'recognized nonprofits',
    },
    {
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
        </svg>
      ),
      value: `${(finRecords / 1_000_000).toFixed(1)}M+`,
      label: 'financial records indexed',
    },
    {
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
      ),
      value: needsFundingSoon > 0 ? `${Math.round(needsFundingSoon / 1000)}K` : '127K',
      label: 'orgs that may need funding soon',
      to: '/sector-health',
    },
    {
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.3"/>
        </svg>
      ),
      value: 'Monthly',
      label: 'IRS registry updates',
    },
  ]

  return (
    <div className="bg-white border-b border-light-grey py-6">
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12 flex flex-wrap items-center justify-center gap-8 md:gap-12">
        {items.map((item, i) => {
          const inner = (
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-light-grey/60 flex items-center justify-center shrink-0">
                {item.icon}
              </div>
              <div>
                <p className="font-body text-[16px] font-bold text-deep-navy leading-none">{item.value}</p>
                <p className="font-body text-[13px] text-cool-grey mt-0.5">{item.label}</p>
              </div>
            </div>
          )
          return item.to ? (
            <Link key={i} to={item.to} className="hover:opacity-80 transition-opacity">
              {inner}
            </Link>
          ) : (
            <div key={i}>{inner}</div>
          )
        })}
      </div>
    </div>
  )
}

// ─── Trust Tiers strip ────────────────────────────────────────────────────────
function TiersStrip() {
  return (
    <section className="bg-white border-t border-b border-light-grey py-9">
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
        <div className="flex flex-col md:flex-row md:items-center gap-6 md:gap-0">

          {/* Label column */}
          <div className="md:w-[200px] shrink-0">
            <p className="font-body text-[11px] font-semibold tracking-[0.08em] text-soft-gold uppercase mb-1">
              Public Data Completeness
            </p>
            <p className="font-body text-[14px] text-cool-grey leading-[1.5]">
              Some organizations have published websites and Form 990s. Others are small, local, or online-only. Each tier reflects what public records are available.
            </p>
            <Link
              to="/tiers"
              className="mt-2 inline-block font-body text-[13px] text-soft-gold hover:text-bright-gold transition-colors"
            >
              How tiers work →
            </Link>
          </div>

          {/* Five tier cells — horizontal scroll on mobile, fixed 5-col grid on md+ */}
          <div className="flex-1 md:border-l md:border-light-grey md:ml-10 md:pl-10">
            <div className="flex overflow-x-auto md:grid md:grid-cols-5 snap-x snap-mandatory scrollbar-none -mx-6 px-6 md:mx-0 md:px-0 gap-0">
            {TIER_STRIP.map(({ name, pct, blurb }) => (
              <Link
                key={name}
                to={name === 'Spark' ? '/directory' : `/directory?min_tier=${name}`}
                className="snap-start shrink-0 w-[88px] md:w-auto flex flex-col items-center gap-1.5 px-2 py-3 border-r border-light-grey last:border-r-0 hover:bg-warm-cream/60 transition-colors group"
              >
                <LampMark tier={name} size="sm" />
                <span
                  className="font-body text-[11px] font-semibold tracking-[0.03em] text-center"
                  style={{ fontFamily: 'Cinzel, serif', color: TIER_COLORS[name] }}
                >
                  {name}
                </span>
                <span className="font-body text-[10px] text-cool-grey text-center leading-tight hidden lg:block">
                  {pct}
                </span>
                <span className="font-body text-[10px] text-cool-grey text-center leading-tight hidden xl:block">
                  {blurb}
                </span>
              </Link>
            ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

// ─── Giving Wallet ────────────────────────────────────────────────────────────
function WalletSection() {
  return (
    <section className="bg-deep-navy py-12 md:py-20 lg:py-28">
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-14 items-center">

          <div>
            <span className="font-body text-[11px] font-semibold tracking-[0.1em] text-soft-gold uppercase">
              Your giving, kept private
            </span>
            <div className="mt-3 flex items-center gap-2 flex-wrap">
              <h2
                className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em]"
                style={{ fontSize: 'clamp(30px, 4vw, 50px)' }}
              >
                Your giving history,<br />private by design
              </h2>
              <span className="inline-flex items-center self-start mt-2 px-2 py-0.5 rounded-full bg-soft-gold/15 border border-soft-gold/30 font-body text-[10px] font-semibold tracking-[0.06em] text-soft-gold uppercase">beta</span>
            </div>
            <p className="mt-5 font-body text-[16px] leading-[1.7]" style={{ color: 'rgba(245,240,235,0.65)' }}>
              Log every donation you make, through any channel, to any nonprofit.
              Records stay on your device only, never our servers.
            </p>
            <ul className="mt-7 space-y-3.5">
              {[
                'Search 1.8M+ tax-deductible nonprofits and autofill the details',
                'Request an acknowledgment letter for gifts of $250+',
                'Export by year, ready for your accountant',
              ].map(item => (
                <li key={item} className="flex items-start gap-3 font-body text-[15px]" style={{ color: 'rgba(245,240,235,0.75)' }}>
                  <svg className="shrink-0 mt-0.5" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  {item}
                </li>
              ))}
            </ul>
            <Link
              to="/wallet"
              className="mt-9 inline-flex items-center gap-2.5 px-8 py-4 rounded-full bg-soft-gold text-deep-navy font-body text-[15px] font-bold hover:bg-bright-gold transition-colors shadow-lg"
            >
              Open your wallet
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="9 18 15 12 9 6"/>
              </svg>
            </Link>
          </div>

          {/* Wallet mockup */}
          <div>
            <div className="bg-[#0F1F38] border border-white/8 rounded-2xl p-6 shadow-2xl">
              <div className="flex items-center gap-2 mb-4">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#A89F94" strokeWidth="2">
                  <rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
                <span className="font-body text-[11px] tracking-[0.04em]" style={{ color: 'rgba(168,159,148,0.55)' }}>
                  Private · stored on this device
                </span>
              </div>
              <div className="grid grid-cols-3 gap-3 mb-4">
                {[
                  { label: 'Given all-time', value: '$1,249.95' },
                  { label: `This year`, value: '$999.98' },
                  { label: 'Orgs', value: '6' },
                ].map(s => (
                  <div key={s.label} className="bg-white/5 rounded-xl p-3.5">
                    <p className="font-body text-[10px] text-cool-grey uppercase tracking-[0.05em] mb-1.5">{s.label}</p>
                    <p className="font-display text-[20px] text-warm-cream leading-none">{s.value}</p>
                  </div>
                ))}
              </div>
              <div className="space-y-2">
                {[
                  { org: 'Houston Food Bank', amount: '$500.00', date: 'Dec 15', badge: 'Letter pending' },
                  { org: 'Literacy Coalition', amount: '$249.99', date: 'Nov 28', badge: null },
                  { org: 'Houston SPCA',       amount: '$249.99', date: 'Oct 3',  badge: null },
                ].map(d => (
                  <div key={d.org} className="flex items-center justify-between bg-white/4 rounded-xl px-4 py-3">
                    <div className="flex-1 min-w-0">
                      <p className="font-body text-[13px] text-warm-cream font-medium">{d.org}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <p className="font-body text-[11px] text-cool-grey">{d.date}</p>
                        {d.badge && (
                          <span className="font-body text-[10px] px-1.5 py-0.5 rounded-full bg-soft-gold/15 text-soft-gold">
                            {d.badge}
                          </span>
                        )}
                      </div>
                    </div>
                    <span className="font-display text-[15px] text-soft-gold ml-3">{d.amount}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

// ─── Advisor teaser ───────────────────────────────────────────────────────────
function AdvisorTeaser() {
  return (
    <section style={{ background: '#F2EDE8' }} className="border-t border-light-grey py-10 md:py-16">
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
        <div className="flex flex-col md:flex-row md:items-center gap-8 md:gap-16">

          {/* Dim lamp mark */}
          <div
            className="shrink-0 w-16 h-16 rounded-full flex items-center justify-center mx-auto md:mx-0"
            style={{ background: 'rgba(201,168,76,0.08)' }}
          >
            <svg viewBox="0 0 24 24" width={32} height={32} aria-hidden="true" style={{ display: 'block' }}>
              <path
                d="M 12,1.5 C 12.4,1.6 13.8,7.2 13.9,7.4 C 14.6,8.0 19.8,11.5 20,12 C 19.8,12.5 14.6,16.0 13.9,16.6 C 13.7,16.8 12.6,20.5 12,22.5 C 11.4,20.5 10.3,16.8 10.1,16.6 C 9.4,16.0 4.2,12.5 4,12 C 4.2,11.5 9.4,8.0 10.1,7.4 C 10.2,7.2 11.6,1.6 12,1.5 Z"
                fill="rgba(201,168,76,0.25)"
              />
            </svg>
          </div>

          <div className="flex-1 text-center md:text-left">
            <p className="font-body text-[11px] font-semibold tracking-[0.1em] text-soft-gold uppercase mb-2">
              Cause Finder
            </p>
            <h2
              className="font-display italic text-deep-navy leading-tight tracking-[-0.01em]"
              style={{ fontSize: 'clamp(24px, 3vw, 38px)' }}
            >
              Not sure where to give?
            </h2>
            <p className="mt-3 font-body text-[15px] text-cool-grey leading-[1.65] max-w-[480px]">
              Describe what you care about. We'll find recognized nonprofits that
              match, by cause, location, giving path, and available public data.
            </p>
          </div>

          <div className="shrink-0 text-center md:text-right">
            <Link
              to="/directory"
              className="inline-flex items-center gap-2.5 px-8 py-4 rounded-full bg-deep-navy text-warm-cream font-body text-[14px] font-bold hover:bg-deep-navy/85 transition-colors"
            >
              Start Exploring
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="9 18 15 12 9 6"/>
              </svg>
            </Link>
            <p className="mt-2 font-body text-[11px] text-cool-grey">
              Free · no account
            </p>
          </div>

        </div>
      </div>
    </section>
  )
}

// ─── Footer CTA ───────────────────────────────────────────────────────────────
function FooterCTA() {
  const { data: stats } = useApi(() => getStats(), [])
  const orgCount = stats?.total_organizations
  const countLabel = orgCount != null
    ? `${(Math.floor(orgCount / 1000) * 1000).toLocaleString()}+`
    : '1,800,000+'

  return (
    <section className="bg-white border-t border-light-grey py-10 md:py-16">
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12 text-center">
        <h2
          className="font-display italic text-deep-navy leading-tight tracking-[-0.01em]"
          style={{ fontSize: 'clamp(28px, 4vw, 46px)' }}
        >
          Ready to give with intention?
        </h2>
        <p className="mt-4 font-body text-[16px] text-cool-grey">
          Browse {countLabel} nonprofits, keep a private record of your giving, and find the quiet, essential organizations nobody else puts in front of you.
        </p>
        <div className="mt-8 flex items-center justify-center gap-4 flex-wrap">
          <Link
            to="/directory"
            className="bg-soft-gold text-deep-navy font-body text-[15px] font-bold px-9 py-4 rounded-full hover:bg-bright-gold transition-colors shadow-md"
          >
            Search Directory
          </Link>
          <Link
            to="/how-it-works"
            className="border-2 border-deep-navy/20 text-deep-navy font-body text-[15px] font-medium px-9 py-4 rounded-full hover:border-deep-navy/40 hover:bg-deep-navy/5 transition-all"
          >
            How Daanaa works
          </Link>
        </div>
        <p className="mt-6 font-body text-[13px] text-cool-grey">
          Free forever · No account required · Data updated monthly
        </p>
        <p className="mt-5 font-body text-[14px]">
          <Link
            to="/the-invisible-97"
            className="text-soft-gold hover:text-bright-gold transition-colors"
          >
            See the invisible 97% →
          </Link>
        </p>
      </div>
    </section>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────
export default function Home() {
  usePageMeta('Daanaa — Independent Nonprofit Discovery Platform', 'Discover causes and organizations using public nonprofit information presented with context, stewardship, and respect.')
  return (
    <div>
      <HeroSection />
      <WhatDaanaaDoesSection />
      <HowDiscoveryWorks />
      <FeaturedCause />
      <BrowseCauses />

      {/* Impact Section */}
      <div className="bg-warm-cream py-12 md:py-16">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
          <div className="mb-8">
            <div className="text-xs text-soft-gold uppercase tracking-wider font-semibold mb-3">
              Impact
            </div>
            <h2 className="text-3xl font-display text-deep-navy mb-4">
              How Daanaa is making a difference
            </h2>
            <p className="text-lg text-cool-grey max-w-2xl">
              Donors tell us when we helped them find a nonprofit. Nonprofits report their volunteers. Together, we measure real impact.
            </p>
          </div>
          <ImpactWidget period="month" size="large" />
        </div>
      </div>

      <PeerFinancialContextSection />
      <TiersStrip />
      <StewardshipSection />
      <FinalCTA />
    </div>
  )
}
