import { useState, useMemo, useEffect } from 'react'
import { usePageMeta } from '../hooks/usePageMeta'
import { useJsonLd, websiteSchema } from '../hooks/useJsonLd'
import { Link, useNavigate } from 'react-router-dom'
import SearchBar from '../components/SearchBar'
import { useApi } from '../hooks/useApi'
import { getStats, getCategories } from '../data/api'
import { NTEE_CATEGORIES } from '../data/ntee'


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

// ─── Get Started (Batch 1: discovery clarity) ────────────────────────────────
// Explicit intent paths for first-time visitors. Track A work: clarifies
// existing paths (give, volunteer, research, compare, find local) without
// adding new features. Design system compliant (headline typography).
function GetStartedSection() {
  const paths = [
    {
      title: 'Search by cause or place',
      description: 'Find organizations working on what matters to you',
      icon: '🔍',
      to: '/directory',
      cta: 'Browse directory'
    },
    {
      title: 'I want to volunteer',
      description: 'Discover nonprofits and volunteer opportunities near you',
      icon: '🤝',
      to: '/volunteer',
      cta: 'Find volunteer roles'
    },
    {
      title: 'Compare and research',
      description: 'Review financials, track your giving, and compare orgs',
      icon: '📊',
      to: '/wallet',
      cta: 'Open Giving Wallet'
    },
  ]

  return (
    <section className="bg-light-cream border-b border-light-grey py-14 md:py-20">
      <div className="max-w-[1000px] mx-auto px-6 md:px-12">
        <div className="text-center mb-10">
          <p className="font-body text-caption font-semibold tracking-[0.08em] text-deep-gold uppercase mb-2">
            Choose your path
          </p>
          <h2 className="font-display italic text-deep-navy leading-tight tracking-[-0.015em]" style={{ fontSize: 'clamp(1.5rem, 4vw, 2rem)' }}>
            How do you want to explore?
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {paths.map(path => (
            <Link
              key={path.to}
              to={path.to}
              className="group flex flex-col rounded-2xl bg-white border border-light-grey p-6 transition-all hover:shadow-lg hover:-translate-y-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-soft-gold"
            >
              <div className="text-4xl mb-3">{path.icon}</div>
              <h3 className="font-body text-body-lg font-semibold text-deep-navy mb-2 group-hover:text-soft-gold transition-colors">
                {path.title}
              </h3>
              <p className="font-body text-body text-cool-grey leading-relaxed flex-1 mb-4">
                {path.description}
              </p>
              <span className="inline-flex items-center gap-2 text-link-gold group-hover:text-deep-gold font-semibold text-small transition-colors">
                {path.cta}
                <span aria-hidden="true" className="group-hover:translate-x-1 transition-transform">→</span>
              </span>
            </Link>
          ))}
        </div>
      </div>
    </section>
  )
}

// ─── Trust beat ──────────────────────────────────────────────────────────────
// Short and specific on purpose: per the 2026-08-08 design review, a single
// hero-level trust claim reads as hype; three concrete, sourced facts read as
// evidence. Placed second (right after the hero) so a skeptical first-time
// visitor meets it before deciding whether to keep scrolling. Semantic
// tokens only (bg-warm-cream/text-deep-navy/text-deep-gold) — no hardcoded
// hex, per DESIGN.md.
function TrustBeat() {
  const facts = [
    'Every organization comes from IRS, NCCS, and ProPublica public filings, not a private database.',
    'No paid placement, no sponsored results, no ranking by who pays.',
    "Daanaa points you to the organization's own site or a verified giving path. Your donation never passes through us.",
  ]

  return (
    <section className="bg-warm-cream py-10 md:py-14 border-b border-light-grey">
      <div className="max-w-[900px] mx-auto px-6 md:px-12">
        <ul className="space-y-3">
          {facts.map(fact => (
            <li key={fact} className="flex items-start gap-3">
              <svg
                width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
                className="shrink-0 mt-1 text-deep-gold"
              >
                <polyline points="20 6 9 17 4 12" />
              </svg>
              <p className="font-body text-body-lg text-deep-navy leading-[1.5]">{fact}</p>
            </li>
          ))}
        </ul>
        <Link
          to="/methodology"
          className="mt-6 inline-flex items-center gap-2 font-body text-body font-medium text-link-gold hover:text-deep-gold transition-colors"
        >
          Read our methodology →
        </Link>
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
    <section id="causes" className="scroll-mt-anchor bg-light-cream border-t border-light-grey py-14 md:py-20">
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

// ─── Final CTA ────────────────────────────────────────────────────────────────
// Carries the two links that used to be full marketing sections (Giving
// Wallet, Hidden Gems) as short secondary links instead — both destinations
// already exist (/wallet, /directory?hidden_gem=1); this just points to
// them rather than re-pitching them. See TODOS.md for the wallet explainer
// video that will eventually replace the wallet line.
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
        <div className="mt-8 flex items-center justify-center gap-6 flex-wrap font-body text-body">
          <Link
            to="/wallet"
            className="text-link-gold hover:text-deep-gold transition-colors underline underline-offset-2"
          >
            Save what matters as you browse
          </Link>
          <span className="text-cool-grey" aria-hidden="true">·</span>
          <Link
            to="/directory?hidden_gem=1"
            className="text-link-gold hover:text-deep-gold transition-colors underline underline-offset-2"
          >
            Browse hidden gems
          </Link>
        </div>
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
      <GetStartedSection />
      <TrustBeat />
      <BrowseCauses />
      <FinalCTA />
    </div>
  )
}
