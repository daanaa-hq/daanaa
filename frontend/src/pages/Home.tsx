import { useState, useMemo, useEffect, useRef, type ReactNode } from 'react'
import { useInView } from '../hooks/useInView'
import { usePageMeta } from '../hooks/usePageMeta'
import { useJsonLd, websiteSchema } from '../hooks/useJsonLd'
import { Link, useNavigate } from 'react-router-dom'
import SearchBar from '../components/SearchBar'
import { useApi } from '../hooks/useApi'
import { getStats, getCategories, getOrganizations, type ApiOrganization } from '../data/api'
import { NTEE_CATEGORIES } from '../data/ntee'
import { getFeaturedCategory } from '../data/featuredCategory'
import AddToWalletButton from '../components/AddToWalletButton'


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
  const [mounted, setMounted] = useState(false)
  const navigate = useNavigate()

  useEffect(() => { setMounted(true) }, [])

  const handleSearch = (q: string) => {
    navigate(q.trim() ? `/directory?q=${encodeURIComponent(q)}` : '/directory')
  }

  return (
    <section className="bg-deep-navy pt-nav">
      <div className="max-w-[760px] mx-auto px-6 pt-24 pb-20 md:pt-32 md:pb-28 text-center">

        <h1
          className={`font-display italic text-warm-cream leading-[1.05] tracking-[-0.025em] transition-all duration-700 ease-out ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-5'}`}
          style={{ fontSize: 'clamp(48px, 7vw, 80px)' }}
        >
          See the overlooked. Give with heart.
        </h1>

        <p
          className={`mt-6 font-body text-title-sm leading-[1.65] max-w-[620px] mx-auto transition-all duration-700 ease-out delay-150 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-5'}`}
          style={{ color: 'rgb(var(--warm-cream-rgb) / 0.80)' }}
        >
          {orgCount.toLocaleString()}+ U.S. nonprofits, public records, peer context. No ads, no paid placement, no pressure.
        </p>

        <div className={`mt-8 max-w-[560px] mx-auto transition-all duration-700 ease-out delay-300 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-5'}`}>
          <p className="text-soft-gold text-sm mb-3 font-semibold">Search by name, cause, city, or ZIP code</p>
          <SearchBar
            value={query}
            onChange={setQuery}
            onSearch={handleSearch}
            dark
            placeholder="Search the directory…"
          />
        </div>

        <div className={`mt-10 max-w-[560px] mx-auto transition-all duration-700 ease-out delay-300 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-5'}`}>
          <p className="text-soft-gold text-sm mb-3 font-semibold">Not sure where to begin?</p>
          <p
            className="font-body text-body leading-relaxed mb-4 transition-all duration-700 ease-out"
            style={{ color: 'rgb(var(--warm-cream-rgb) / 0.80)' }}
          >
            Answer a few simple questions to find a short list of organizations to explore.
          </p>
          <Link
            to="/directory"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full border border-soft-gold/60 text-soft-gold hover:bg-soft-gold hover:text-deep-navy transition-colors font-body text-small font-semibold"
          >
            Browse causes and organizations
            <span aria-hidden="true">→</span>
          </Link>
        </div>

        <p
          className={`mt-8 font-body text-body transition-all duration-700 ease-out ${mounted ? 'opacity-100' : 'opacity-0'}`}
          style={{ color: 'rgb(var(--warm-cream-rgb) / 0.55)', transitionDelay: '450ms' }}
        >
          or{' '}
          <Link to="/directory" className="text-soft-gold hover:text-bright-gold transition-colors underline underline-offset-2">browse the directory</Link>
          {' · '}
          <a
            href="#causes"
            onClick={(e) => {
              e.preventDefault()
              document.getElementById('causes')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
            }}
            className="text-soft-gold hover:text-bright-gold transition-colors underline underline-offset-2"
          >explore causes</a>
        </p>

        <p
          className={`mt-6 font-body text-small transition-opacity duration-700 ease-out ${mounted ? 'opacity-100' : 'opacity-0'}`}
          style={{ color: 'rgb(var(--warm-cream-rgb) / 0.65)', transitionDelay: '600ms' }}
        >
          Independent · Built on public records · Not a rating agency
        </p>
      </div>
    </section>
  )
}

// ─── Persona Tiles ────────────────────────────────────────────────────────────
function PersonaTiles() {
  const { ref, inView } = useInView()

  const tiles: { to: string; label: string; sub: string; icon: ReactNode }[] = [
    {
      to: '/directory',
      label: 'I want to give',
      sub: 'Cause filters · financial health',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
        </svg>
      ),
    },
    {
      to: '/for-nonprofits',
      label: 'I work in nonprofits',
      sub: 'Claim your page · peer data',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
          <polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
      ),
    },
    {
      to: '/research',
      label: "I'm researching",
      sub: 'Methodology · public data',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
      ),
    },
  ]

  const volunteerIcon = (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
      <circle cx="9" cy="7" r="4"/>
      <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
      <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
    </svg>
  )

  return (
    <section className="bg-warm-cream pt-6 md:pt-8">
      <div ref={ref} className="max-w-[1120px] mx-auto px-6 md:px-12 pb-10">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {tiles.map((tile, i) => (
            <Link
              key={tile.label}
              to={tile.to}
              className={`bg-white border border-light-grey rounded-2xl p-5 hover:shadow-md transition-all duration-700 ease-out flex flex-col ${inView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}
              style={{ transitionDelay: inView ? `${i * 80}ms` : '0ms' }}
            >
              <div className="w-10 h-10 rounded-full bg-soft-gold/15 flex items-center justify-center mb-3 shrink-0">
                {tile.icon}
              </div>
              <p className="font-body text-body-lg font-semibold text-deep-navy">{tile.label}</p>
              <p className="font-body text-caption text-cool-grey mt-1">{tile.sub}</p>
            </Link>
          ))}
          {/* Volunteer — coming soon */}
          <div
            title="Volunteer matching is coming soon"
            className={`bg-white border border-dashed border-cool-grey/30 rounded-2xl p-5 flex flex-col cursor-default select-none transition-all duration-700 ease-out ${inView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}
            style={{ transitionDelay: inView ? `${tiles.length * 80}ms` : '0ms' }}
          >
            <div className="w-10 h-10 rounded-full bg-cool-grey/8 flex items-center justify-center mb-3 shrink-0 text-cool-grey/40">
              {volunteerIcon}
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <p className="font-body text-body-lg font-semibold text-cool-grey/70">I want to volunteer</p>
            </div>
            <p className="font-body text-caption text-cool-grey/60 mt-1">Volunteer matching</p>
          </div>
        </div>
      </div>
    </section>
  )
}

// ─── What Daanaa Does ────────────────────────────────────────────────────────
function WhatDaanaaDoesSection() {
  const { ref, inView } = useInView()
  return (
    <section className="bg-warm-cream py-16 md:py-20">
      <div ref={ref} className="max-w-[1120px] mx-auto px-6 md:px-12">
        <div className="mb-12">
          <h2 className={`font-display italic text-deep-navy text-headline-lg md:text-display leading-[1.15] tracking-[-0.01em] transition-all duration-700 ease-out ${inView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}>
            What Daanaa does
          </h2>
          <p className={`mt-6 font-body text-lead text-cool-grey leading-[1.65] max-w-[720px] transition-all duration-700 ease-out delay-100 ${inView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}>
            Daanaa organizes public nonprofit information so people can discover organizations with more context. It does not take paid placement, process donations, or tell people where they must give.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { title: 'Discover causes', body: 'Search by cause, place, or community need.' },
            { title: 'Understand context', body: 'View public information with peer context, not a one size fits all rating.' },
            { title: 'Connect directly', body: "When available, Daanaa points you to the organization's own official website." },
          ].map((card, i) => (
            <div
              key={card.title}
              className={`bg-white border border-light-grey rounded-2xl p-6 md:p-8 transition-all duration-700 ease-out ${inView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}
              style={{ transitionDelay: inView ? `${200 + i * 100}ms` : '0ms' }}
            >
              <h3 className="font-display text-deep-navy text-title md:text-title-lg">{card.title}</h3>
              <p className="mt-3 font-body text-body-lg text-cool-grey leading-[1.6]">{card.body}</p>
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
          <h2 className="font-display italic text-deep-navy text-headline md:text-headline-lg leading-[1.15] tracking-[-0.01em]">
            Discovery works when you have context
          </h2>
          <p className="mt-6 font-body text-lead text-cool-grey leading-[1.65]">
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
            <h2 className="font-display italic text-deep-navy text-headline-lg md:text-display leading-[1.15] tracking-[-0.01em]">
              Peer Financial Context
            </h2>
            <p className="mt-6 font-body text-lead text-cool-grey leading-[1.65]">
              Peer Financial Context shows public financial information within comparable peer groups. It is designed to add context, not to rate, rank, or recommend organizations.
            </p>
            <p className="mt-4 font-body text-lead text-cool-grey leading-[1.65]">
              This approach respects the fact that a small community organization and a large national nonprofit may both be thriving. They just have different financial profiles.
            </p>
            <Link
              to="/methodology"
              className="mt-6 inline-flex items-center gap-2 font-body text-body font-medium text-link-gold hover:text-deep-gold transition-colors"
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
                  <p className="font-body text-body font-semibold text-deep-navy">Based on public records</p>
                  <p className="font-body text-small text-cool-grey mt-1">IRS, NCCS, and ProPublica data only</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="shrink-0 mt-0.5">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                <div>
                  <p className="font-body text-body font-semibold text-deep-navy">Peer-group based</p>
                  <p className="font-body text-small text-cool-grey mt-1">Compared within similar organizations</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="shrink-0 mt-0.5">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                <div>
                  <p className="font-body text-body font-semibold text-deep-navy">Not a rating</p>
                  <p className="font-body text-small text-cool-grey mt-1">Context, not judgment or endorsement</p>
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
            <h2 className="font-display italic text-warm-cream text-headline-lg md:text-display leading-[1.15] tracking-[-0.01em]">
              Built on stewardship
            </h2>
            <p className="mt-6 font-body text-lead leading-[1.65]" style={{ color: 'rgb(var(--warm-cream-rgb) / 0.80)' }}>
              Stewardship means caring for donors, organizations, and the public record at the same time.
            </p>
            <p className="mt-4 font-body text-lead leading-[1.65]" style={{ color: 'rgb(var(--warm-cream-rgb) / 0.75)' }}>
              Daanaa is built to support discovery without turning giving into judgment. We avoid ranking language, welcome corrections, protect privacy, and remain independent.
            </p>
            <Link
              to="/stewardship"
              className="mt-6 inline-flex items-center gap-2 font-body text-body font-medium text-soft-gold hover:text-bright-gold transition-colors"
            >
              See our stewardship principles →
            </Link>
          </div>
          <div className="space-y-4">
            {[
              'We do not take paid placement',
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
                <p className="font-body text-lead text-warm-cream leading-[1.5]">{principle}</p>
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
          className="font-display italic text-deep-navy leading-[1.15] tracking-[-0.01em] h2-display"
        >
          Ready to discover?
        </h2>
        <p className="mt-6 font-body text-lead text-cool-grey max-w-[720px] mx-auto leading-[1.65]">
          Search {countLabel} organizations by cause, place, or public information. Start with something you care about.
        </p>
        <div className="mt-8 flex items-center justify-center gap-3 flex-wrap">
          <Link
            to="/directory"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-full bg-soft-gold text-deep-navy font-body text-body-lg font-bold hover:bg-bright-gold transition-colors shadow-md"
          >
            Start Discovering
          </Link>
          <Link
            to="/methodology"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-full border-2 border-deep-navy/20 text-deep-navy font-body text-body-lg font-medium hover:border-deep-navy/40 hover:bg-deep-navy/5 transition-all"
          >
            How it works
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
    <section className="bg-deep-navy border-b border-white/10 py-14 md:py-20">
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
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
            <p className="font-body text-caption font-semibold tracking-[0.12em] text-soft-gold uppercase mb-2">
              Featured cause
            </p>
            <h2
              className="font-display italic text-warm-cream leading-tight tracking-[-0.015em] h2-display"
            >
              {cat.name}
            </h2>
            <p className="font-display italic text-pale-gold/90 mt-2 text-title-sm md:text-title">
              {featured.tagline}
            </p>
            {featured.focus && (
              <div className="flex flex-wrap justify-center md:justify-start gap-2 mt-4">
                {featured.focus.map(f => (
                  <span
                    key={f}
                    className="font-body text-caption px-3 py-1 rounded-full bg-soft-gold/10 border border-soft-gold/25 text-pale-gold"
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
            className="shrink-0 inline-flex items-center gap-2.5 px-7 py-3.5 rounded-full bg-soft-gold text-deep-navy font-body text-body font-bold hover:bg-bright-gold transition-colors shadow-lg"
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

// One-line plain-English tagline per NTEE major category
const CAUSE_TAGLINES: Record<string, string> = {
  A: 'Museums, theaters, and the arts that make a community whole.',
  B: 'Schools, scholarships, and learning programs for every age.',
  C: 'Land, water, wildlife, and climate work.',
  D: 'Shelters, sanctuaries, and animal welfare programs.',
  E: 'Community clinics, hospitals, and wellness programs.',
  F: 'Counseling, crisis support, and mental health services.',
  G: 'Organizations focused on specific diseases and conditions.',
  H: 'Medical and scientific research institutions.',
  I: 'Legal aid, crime prevention, and access to justice.',
  J: 'Job training, workforce development, and economic opportunity.',
  K: 'Food security, urban farming, and hunger relief.',
  L: 'Affordable housing, emergency shelter, and homelessness prevention.',
  M: 'Public safety, emergency preparedness, and disaster relief.',
  N: 'Parks, sports programs, and outdoor recreation.',
  O: 'After-school programs, mentorship, and youth leadership.',
  P: 'Food banks, shelters, and support for families in need.',
  Q: 'Global development, disaster relief, and international aid.',
  R: 'Advocacy for civil rights, equity, and social justice.',
  S: 'Neighborhood groups, civic organizations, and community builders.',
  T: 'Foundations and grant-making organizations.',
  U: 'Science, technology, and research institutions.',
  V: 'Social research, policy, and knowledge building.',
  W: 'Public affairs, voter engagement, and government policy.',
  X: 'Faith-based organizations serving their communities.',
  Y: 'Mutual benefit and membership organizations.',
  Z: 'Nonprofits with limited public classification data.',
}

// Color accent palette — one per NTEE major group
// Cause colour, one entry per NTEE major group (A-Z).
//
// The 26 groups map onto the 9 official NCCS families rather than each having
// its own colour. Two reasons: categorical colour stops aiding recognition
// past roughly 8 values, and the previous per-letter palette used fixed
// Tailwind shades that were wrong in BOTH themes (chips measured 17:1 against
// the dark page and 1.0:1 against the light page).
//
// Values come from tokens.css, generated by scripts/generate_cause_palette.py,
// so they are theme-aware and contrast-verified. Colour is never the only
// signal: every chip also carries its label (WCAG 1.4.1).
export const CAUSE_ACCENT: Record<string, { bg: string; emoji_bg: string; border: string; text: string }> = {
  A: { bg: 'bg-cause-arts-surface', emoji_bg: 'bg-cause-arts-border', border: 'border-cause-arts-border', text: 'text-cause-arts-text' },
  B: { bg: 'bg-cause-education-surface', emoji_bg: 'bg-cause-education-border', border: 'border-cause-education-border', text: 'text-cause-education-text' },
  C: { bg: 'bg-cause-environment-surface', emoji_bg: 'bg-cause-environment-border', border: 'border-cause-environment-border', text: 'text-cause-environment-text' },
  D: { bg: 'bg-cause-environment-surface', emoji_bg: 'bg-cause-environment-border', border: 'border-cause-environment-border', text: 'text-cause-environment-text' },
  E: { bg: 'bg-cause-health-surface', emoji_bg: 'bg-cause-health-border', border: 'border-cause-health-border', text: 'text-cause-health-text' },
  F: { bg: 'bg-cause-health-surface', emoji_bg: 'bg-cause-health-border', border: 'border-cause-health-border', text: 'text-cause-health-text' },
  G: { bg: 'bg-cause-health-surface', emoji_bg: 'bg-cause-health-border', border: 'border-cause-health-border', text: 'text-cause-health-text' },
  H: { bg: 'bg-cause-health-surface', emoji_bg: 'bg-cause-health-border', border: 'border-cause-health-border', text: 'text-cause-health-text' },
  I: { bg: 'bg-cause-human-surface', emoji_bg: 'bg-cause-human-border', border: 'border-cause-human-border', text: 'text-cause-human-text' },
  J: { bg: 'bg-cause-human-surface', emoji_bg: 'bg-cause-human-border', border: 'border-cause-human-border', text: 'text-cause-human-text' },
  K: { bg: 'bg-cause-human-surface', emoji_bg: 'bg-cause-human-border', border: 'border-cause-human-border', text: 'text-cause-human-text' },
  L: { bg: 'bg-cause-human-surface', emoji_bg: 'bg-cause-human-border', border: 'border-cause-human-border', text: 'text-cause-human-text' },
  M: { bg: 'bg-cause-human-surface', emoji_bg: 'bg-cause-human-border', border: 'border-cause-human-border', text: 'text-cause-human-text' },
  N: { bg: 'bg-cause-human-surface', emoji_bg: 'bg-cause-human-border', border: 'border-cause-human-border', text: 'text-cause-human-text' },
  O: { bg: 'bg-cause-human-surface', emoji_bg: 'bg-cause-human-border', border: 'border-cause-human-border', text: 'text-cause-human-text' },
  P: { bg: 'bg-cause-human-surface', emoji_bg: 'bg-cause-human-border', border: 'border-cause-human-border', text: 'text-cause-human-text' },
  Q: { bg: 'bg-cause-global-surface', emoji_bg: 'bg-cause-global-border', border: 'border-cause-global-border', text: 'text-cause-global-text' },
  R: { bg: 'bg-cause-public-surface', emoji_bg: 'bg-cause-public-border', border: 'border-cause-public-border', text: 'text-cause-public-text' },
  S: { bg: 'bg-cause-public-surface', emoji_bg: 'bg-cause-public-border', border: 'border-cause-public-border', text: 'text-cause-public-text' },
  T: { bg: 'bg-cause-public-surface', emoji_bg: 'bg-cause-public-border', border: 'border-cause-public-border', text: 'text-cause-public-text' },
  U: { bg: 'bg-cause-education-surface', emoji_bg: 'bg-cause-education-border', border: 'border-cause-education-border', text: 'text-cause-education-text' },
  V: { bg: 'bg-cause-education-surface', emoji_bg: 'bg-cause-education-border', border: 'border-cause-education-border', text: 'text-cause-education-text' },
  W: { bg: 'bg-cause-public-surface', emoji_bg: 'bg-cause-public-border', border: 'border-cause-public-border', text: 'text-cause-public-text' },
  X: { bg: 'bg-cause-religion-surface', emoji_bg: 'bg-cause-religion-border', border: 'border-cause-religion-border', text: 'text-cause-religion-text' },
  Y: { bg: 'bg-cause-mutual-surface', emoji_bg: 'bg-cause-mutual-border', border: 'border-cause-mutual-border', text: 'text-cause-mutual-text' },
  Z: { bg: 'bg-cause-unknown-surface', emoji_bg: 'bg-cause-unknown-border', border: 'border-cause-unknown-border', text: 'text-cause-unknown-text' },
}

// The 8 causes donors most commonly explore — pinned at top of the grid
const FEATURED_CAUSE_IDS = ['E', 'B', 'P', 'C', 'D', 'A', 'O', 'S']

function BrowseCauses() {
  const cats = useMemo(() => seededShuffle(NTEE_CATEGORIES, weekSeed()), [])
  const { data: catData } = useApi(() => getCategories(), [])
  const orgCountByCode = useMemo(() => {
    const map: Record<string, number> = {}
    catData?.categories.forEach(c => { map[c.code] = c.count })
    return map
  }, [catData])

  const featuredCats = useMemo(
    () => FEATURED_CAUSE_IDS.map(id => NTEE_CATEGORIES.find(c => c.id === id)!).filter(Boolean),
    []
  )
  const restCats = useMemo(
    () => cats.filter(c => !FEATURED_CAUSE_IDS.includes(c.id)),
    [cats]
  )

  return (
    <section id="causes" className="scroll-mt-anchor bg-[#F8F5F0] border-t border-light-grey py-14 md:py-20">
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12">

        {/* Section header */}
        <div className="mb-10">
          <p className="font-body text-caption font-semibold tracking-[0.08em] text-deep-gold uppercase mb-2">
            Find by Cause
          </p>
          <h2
            className="font-display italic text-deep-navy leading-tight tracking-[-0.015em]"
            style={{ fontSize: 'clamp(32px, 4vw, 48px)' }}
          >
            What do you care about?
          </h2>
          <p className="mt-4 font-body text-lead text-cool-grey leading-[1.6] max-w-[580px]">
            Pick a cause to see the nonprofits working on it, explore their public record, and visit their official website.
          </p>
        </div>

        {/* Featured 8 — larger tiles with icon + tagline */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 mb-4">
          {featuredCats.map(cat => {
            const accent = CAUSE_ACCENT[cat.id] ?? CAUSE_ACCENT.Z
            const count = orgCountByCode[cat.id]
            const tagline = CAUSE_TAGLINES[cat.id] ?? ''
            return (
              <Link
                key={cat.id}
                to={`/category/${cat.id}`}
                className={`group flex flex-col gap-3 rounded-2xl border px-5 py-5 transition-all duration-200 hover:-translate-y-[2px] hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-soft-gold ${accent.bg} ${accent.border}`}
              >
                {/* Emoji bubble */}
                <div className={`w-11 h-11 rounded-xl flex items-center justify-center text-title-lg ${accent.emoji_bg}`}>
                  {cat.emoji}
                </div>

                {/* Name */}
                <div className="flex-1">
                  <p className={`font-body text-body-lg font-semibold leading-snug group-hover:opacity-80 transition-opacity ${accent.text}`}>
                    {cat.name}
                  </p>
                  <p className="font-body text-caption text-cool-grey mt-1 leading-relaxed line-clamp-2">
                    {tagline}
                  </p>
                </div>

                {/* Count + arrow */}
                <div className="flex items-center justify-between pt-2 border-t border-black/5">
                  <span className="font-body text-caption text-cool-grey">
                    {count != null ? `${count.toLocaleString()} orgs` : `${cat.subs.length} types`}
                  </span>
                  <svg
                    width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
                    className={`opacity-40 group-hover:opacity-90 group-hover:translate-x-0.5 transition-all ${accent.text}`}
                  >
                    <polyline points="9 18 15 12 9 6"/>
                  </svg>
                </div>
              </Link>
            )
          })}
        </div>

        {/* Remaining categories — compact 3→6-col grid */}
        <div className="grid grid-cols-3 md:grid-cols-5 lg:grid-cols-6 gap-2">
          {restCats.map(cat => {
            const count = orgCountByCode[cat.id]
            const accent = CAUSE_ACCENT[cat.id] ?? CAUSE_ACCENT.Z
            return (
              <Link
                key={cat.id}
                to={`/category/${cat.id}`}
                className="group flex flex-col items-center gap-1.5 px-3 py-3.5 bg-white rounded-xl border border-light-grey hover:border-soft-gold/40 hover:shadow-sm transition-all duration-150 text-center focus:outline-none focus-visible:ring-2 focus-visible:ring-soft-gold"
              >
                <div className={`w-9 h-9 rounded-lg flex items-center justify-center text-title-sm ${accent.emoji_bg}`}>
                  {cat.emoji}
                </div>
                <p className="font-body text-label font-medium text-deep-navy/70 group-hover:text-deep-navy leading-tight transition-colors">
                  {cat.name}
                </p>
                {count != null && (
                  <p className="font-body text-micro text-cool-grey">{count.toLocaleString()}</p>
                )}
              </Link>
            )
          })}
        </div>

        {/* Link to see all */}
        <div className="mt-8 text-center">
          <Link
            to="/directory"
            className="inline-flex items-center gap-2 font-body text-body text-link-gold hover:text-deep-gold transition-colors"
          >
            Search all organizations
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
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
        </svg>
      ),
      value: needsFundingSoon > 0 ? `${Math.round(needsFundingSoon / 1000)}K` : '127K',
      label: 'smaller orgs where support goes far',
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
                <p className="font-body text-lead font-bold text-deep-navy leading-none">{item.value}</p>
                <p className="font-body text-small text-cool-grey mt-0.5">{item.label}</p>
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

// ─── Giving Wallet ────────────────────────────────────────────────────────────
function WalletSection() {
  return (
    <section className="bg-deep-navy py-12 md:py-20 lg:py-28">
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-14 items-center">

          <div>
            <span className="font-body text-label font-semibold tracking-[0.1em] text-soft-gold uppercase">
              Your giving, kept private
            </span>
            <h2
              className="mt-3 font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em]"
              style={{ fontSize: 'clamp(30px, 4vw, 50px)' }}
            >
              Save the ones<br />that matter to you
            </h2>
            <p className="mt-5 font-body text-lead leading-[1.7]" style={{ color: 'rgb(var(--warm-cream-rgb) / 0.65)' }}>
              Your Giving Wallet holds the nonprofits you want to support.
              Track your intent for each one. Everything stays private: your account, your list, no one else's.
            </p>
            <ul className="mt-7 space-y-3.5">
              {[
                'Save nonprofits as you discover them across Daanaa',
                'Set your giving intent: amount, volunteering, or board interest',
                'Sync across devices with your Google account',
              ].map(item => (
                <li key={item} className="flex items-start gap-3 font-body text-body-lg" style={{ color: 'rgb(var(--warm-cream-rgb) / 0.75)' }}>
                  <svg className="shrink-0 mt-0.5" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  {item}
                </li>
              ))}
            </ul>
            <Link
              to="/wallet"
              className="mt-9 inline-flex items-center gap-2.5 px-8 py-4 rounded-full bg-soft-gold text-deep-navy font-body text-body-lg font-bold hover:bg-bright-gold transition-colors shadow-lg"
            >
              Open your wallet
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="9 18 15 12 9 6"/>
              </svg>
            </Link>
          </div>

          {/* Wallet preview — mirrors the real WalletPage: a light surface with
              funding/volunteering tabs and OrgCardRow-style rows. Keep this in
              step with WalletPage.tsx; a preview that flatters what the page
              does not do is the kind of promise we do not get to make. */}
          <div>
            <div className="bg-warm-cream border border-light-grey rounded-2xl p-6 shadow-2xl">
              <div className="mb-4">
                <p className="font-display italic text-title-sm text-deep-navy">Your Giving Wallet</p>
                <p className="font-body text-label text-cool-grey mt-0.5">3 organizations saved</p>
              </div>

              {/* Funding / Volunteering tabs, funding active (WalletPage default) */}
              <div className="flex items-center gap-2 mb-4">
                <span className="inline-flex items-center px-4 py-1.5 rounded-full bg-green-500 text-white font-body text-caption font-semibold">
                  Funding
                </span>
                <span className="inline-flex items-center px-4 py-1.5 rounded-full bg-white border border-light-grey text-cool-grey font-body text-caption font-semibold">
                  Volunteering
                </span>
              </div>

              <div className="flex flex-col gap-2">
                {[
                  { org: 'Houston Food Bank',  location: 'Houston, TX', log: '2 donations' },
                  { org: 'Literacy Coalition', location: 'Austin, TX',  log: '1 donation' },
                  { org: 'Houston SPCA',       location: 'Houston, TX', log: null },
                ].map(d => (
                  <div key={d.org} className="bg-white border border-light-grey rounded-xl px-5 py-4">
                    <p className="font-display text-lead text-deep-navy leading-snug">{d.org}</p>
                    <p className="font-body text-micro text-cool-grey mt-0.5">{d.location}</p>
                    <div className="flex items-center gap-3 mt-2">
                      <span className="font-body text-caption text-deep-navy font-medium">View log</span>
                      {d.log && (
                        <span className="font-body text-label text-green-600">{d.log}</span>
                      )}
                    </div>
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

// ─── Hidden Gems ─────────────────────────────────────────────────────────────
const HEALTH_LABEL: Record<string, string> = {
  HEALTHY: 'Financially healthy',
  STABLE:  'Financially stable',
  CAUTION: 'Needs support',
}
const HEALTH_CLASSES: Record<string, string> = {
  HEALTHY: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  STABLE:  'bg-blue-50 text-blue-700 border-blue-200',
  CAUTION: 'bg-alert-amber/5 text-amber-700 border-amber-200',
}

function HiddenGemsSection() {
  const [gems, setGems] = useState<ApiOrganization[]>([])
  const { ref, inView } = useInView(0.08)

  useEffect(() => {
    getOrganizations({ hidden_gem: true, per_page: 40 })
      .then(res => {
        const pool = res.organizations
        // Week-stable shuffle: same 4 orgs all week, different each week
        const shuffled = seededShuffle([...pool], weekSeed())
        setGems(shuffled.slice(0, 4))
      })
      .catch(() => {/* silently skip section on error */})
  }, [])

  if (gems.length === 0) return null

  return (
    <section ref={ref} className="bg-warm-cream py-14 md:py-20 border-t border-light-grey">
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
        <div className={`flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-8 transition-all duration-700 ease-out ${inView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}>
          <div>
            <span className="font-body text-label font-semibold tracking-[0.1em] text-deep-gold uppercase">
              Worth discovering
            </span>
            <h2 className="mt-2 font-display italic text-deep-navy leading-[1.05] h2-display">
              The ones doing quiet, steady work
            </h2>
            <p className="mt-3 font-body text-body-lg text-cool-grey max-w-xl leading-[1.6]">
              Small nonprofits under $500K in revenue with strong peer financial context scores relative to similar organizations.
              Starting points for your own research, not verdicts.
            </p>
          </div>
          <Link
            to="/directory?hidden_gem=1"
            className="shrink-0 font-body text-small text-link-gold hover:text-deep-gold transition-colors flex items-center gap-1.5"
          >
            See more
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {gems.map((org, i) => {
            const hasFullContext = org.scoring_tier && (org.scoring_tier === '1_Full_Context' || org.scoring_tier === '2_Regional_Context')
            const causes = (org.cause_tags ?? []).slice(0, 2)
            return (
              <div
                key={org.EIN}
                className={`bg-white rounded-2xl border border-light-grey p-5 flex flex-col hover:border-soft-gold/40 hover:shadow-sm transition-all duration-700 ease-out ${inView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
                style={{ transitionDelay: inView ? `${100 + i * 80}ms` : '0ms' }}
              >
                <Link
                  to={`/org/${org.EIN}`}
                  className="font-body text-body font-semibold text-deep-navy hover:text-soft-gold transition-colors leading-snug mb-1"
                >
                  {org.organization_name}
                </Link>
                <p className="font-body text-label text-cool-grey mb-2">
                  {[org.CITY, org.STATE].filter(Boolean).join(', ')}
                  {causes.length > 0 && ` · ${causes.join(', ')}`}
                </p>
                {(org as any).mission && (
                  <div className="mb-3 flex-1">
                    <p className="font-body text-caption text-cool-grey italic line-clamp-2 leading-relaxed">
                      {(org as any).mission.replace(/^[""\s]+|[""\s]+$/g, '')}
                    </p>
                    {['ai_ntee','ai_haiku','ai_web','ai_generated'].includes((org as any).mission_source ?? '') && (
                      <span
                        title="Generated by AI from public records. Not confirmed by the organization."
                        className="mt-1 inline-block border border-cool-grey/60 text-cool-grey/75 rounded text-micro px-1.5 py-0.5 font-body tracking-[0.04em]"
                      >
                        AI assisted
                      </span>
                    )}
                  </div>
                )}
                <div className="flex flex-wrap gap-1.5 mb-4">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-micro font-semibold border font-body ${hasFullContext ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-amber-50 text-amber-700 border-amber-200'}`}>
                    {hasFullContext ? 'Financial context' : 'Emerging profile'}
                  </span>
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-micro font-semibold border bg-violet-50 text-violet-700 border-violet-200 font-body">
                    Hidden gem
                  </span>
                </div>
                <div className="mt-auto">
                  <AddToWalletButton ein={org.EIN} orgName={org.organization_name} />
                </div>
              </div>
            )
          })}
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
            <p className="font-body text-label font-semibold tracking-[0.1em] text-soft-gold uppercase mb-2">
              Cause Finder
            </p>
            <h2
              className="font-display italic text-deep-navy leading-tight tracking-[-0.01em]"
              style={{ fontSize: 'clamp(24px, 3vw, 38px)' }}
            >
              Not sure where to give?
            </h2>
            <p className="mt-3 font-body text-body-lg text-cool-grey leading-[1.65] max-w-[480px]">
              Describe what you care about. We'll find recognized nonprofits that
              match, by cause, location, giving path, and available public data.
            </p>
          </div>

          <div className="shrink-0 text-center md:text-right">
            <Link
              to="/directory"
              className="inline-flex items-center gap-2.5 px-8 py-4 rounded-full bg-deep-navy text-warm-cream font-body text-body font-bold hover:bg-deep-navy/85 transition-colors"
            >
              Start Exploring
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="9 18 15 12 9 6"/>
              </svg>
            </Link>
            <p className="mt-2 font-body text-label text-cool-grey">
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
          className="font-display italic text-deep-navy leading-tight tracking-[-0.01em] h2-display"
        >
          Ready to give with intention?
        </h2>
        <p className="mt-4 font-body text-lead text-cool-grey">
          Browse {countLabel} nonprofits, keep a private record of your giving, and find the quiet, essential organizations nobody else puts in front of you.
        </p>
        <div className="mt-8 flex items-center justify-center gap-4 flex-wrap">
          <Link
            to="/directory"
            className="bg-soft-gold text-deep-navy font-body text-body-lg font-bold px-9 py-4 rounded-full hover:bg-bright-gold transition-colors shadow-md"
          >
            Search Directory
          </Link>
          <Link
            to="/methodology"
            className="border-2 border-deep-navy/20 text-deep-navy font-body text-body-lg font-medium px-9 py-4 rounded-full hover:border-deep-navy/40 hover:bg-deep-navy/5 transition-all"
          >
            How Daanaa works
          </Link>
        </div>
        <p className="mt-6 font-body text-small text-cool-grey">
          Free forever · No account required · Data updated monthly
        </p>
        <p className="mt-5 font-body text-body">
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
  usePageMeta('Daanaa — Independent Nonprofit Discovery Platform', {
    description: 'Discover causes and organizations using public nonprofit information presented with context, stewardship, and respect.',
    ogImage: 'https://daanaa.org/og-image-v2.png',
  })

  useJsonLd(websiteSchema({
    name: 'Daanaa',
    url: 'https://daanaa.org',
    description: 'Independent nonprofit discovery platform. Search 1.8M US nonprofits with peer financial context, public data, and verified giving paths.',
  }))

  return (
    <div>
      <HeroSection />
      <PersonaTiles />
      <WhatDaanaaDoesSection />
      <HowDiscoveryWorks />
      <FeaturedCause />
      <HiddenGemsSection />
      <BrowseCauses />

      <PeerFinancialContextSection />
      <WalletSection />
      <StewardshipSection />
      <FinalCTA />
    </div>
  )
}
