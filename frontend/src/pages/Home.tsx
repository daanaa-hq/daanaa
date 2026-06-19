import { useState, useMemo, useEffect, useRef, type ReactNode } from 'react'
import { useInView } from '../hooks/useInView'
import { usePageMeta } from '../hooks/usePageMeta'
import { useJsonLd, websiteSchema } from '../hooks/useJsonLd'
import { Link, useNavigate } from 'react-router-dom'
import SearchBar from '../components/SearchBar'
import LampMark from '../components/LampMark'
import { useApi } from '../hooks/useApi'
import { getStats, getCategories, getOrganizations, type ApiOrganization } from '../data/api'
import { TIER_COLORS } from '../components/TrustBadge'
import type { TierName } from '../components/TrustBadge'
import { NTEE_CATEGORIES } from '../data/ntee'
import { getFeaturedCategory } from '../data/featuredCategory'
import ImpactWidget from '../components/ImpactWidget'
import AddToWalletButton from '../components/AddToWalletButton'

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
  const [mounted, setMounted] = useState(false)
  const navigate = useNavigate()

  useEffect(() => { setMounted(true) }, [])

  const handleSearch = (q: string) => {
    navigate(q.trim() ? `/directory?q=${encodeURIComponent(q)}` : '/directory')
  }

  return (
    <section className="bg-deep-navy pt-[72px]">
      <div className="max-w-[760px] mx-auto px-6 pt-24 pb-20 md:pt-32 md:pb-28 text-center">

        <h1
          className={`font-display italic text-warm-cream leading-[1.05] tracking-[-0.025em] transition-all duration-700 ease-out ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-5'}`}
          style={{ fontSize: 'clamp(48px, 7vw, 80px)' }}
        >
          See the overlooked. Give with heart.
        </h1>

        <p
          className={`mt-6 font-body text-[18px] leading-[1.65] max-w-[620px] mx-auto transition-all duration-700 ease-out delay-150 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-5'}`}
          style={{ color: 'rgba(245,240,235,0.80)' }}
        >
          {orgCount.toLocaleString()}+ U.S. nonprofits, public records, peer context. No ads, no rankings, no pressure.
        </p>

        <div className={`mt-8 max-w-[560px] mx-auto transition-all duration-700 ease-out delay-300 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-5'}`}>
          <SearchBar
            value={query}
            onChange={setQuery}
            onSearch={handleSearch}
            dark
            placeholder="Search by name, cause, or city…"
          />
        </div>

        <p
          className={`mt-5 font-body text-[14px] transition-all duration-700 ease-out ${mounted ? 'opacity-100' : 'opacity-0'}`}
          style={{ color: 'rgba(245,240,235,0.55)', transitionDelay: '450ms' }}
        >
          or{' '}
          <Link to="/directory" className="text-soft-gold hover:text-bright-gold transition-colors underline underline-offset-2">browse the directory</Link>
          {' · '}
          <Link to="/causes" className="text-soft-gold hover:text-bright-gold transition-colors underline underline-offset-2">explore causes</Link>
        </p>

        <p
          className={`mt-6 font-body text-[13px] transition-opacity duration-700 ease-out ${mounted ? 'opacity-100' : 'opacity-0'}`}
          style={{ color: 'rgba(245,240,235,0.40)', transitionDelay: '600ms' }}
        >
          Independent · Built on public records · Not a rating agency
        </p>
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
          <h2 className={`font-display italic text-deep-navy text-[32px] md:text-[40px] leading-[1.15] tracking-[-0.01em] transition-all duration-700 ease-out ${inView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}>
            What Daanaa does
          </h2>
          <p className={`mt-6 font-body text-[16px] text-cool-grey leading-[1.65] max-w-[720px] transition-all duration-700 ease-out delay-100 ${inView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}>
            Daanaa organizes public nonprofit information so people can discover organizations with more context. It does not rank nonprofits, process donations, or tell people where they must give.
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
const CAUSE_ACCENT: Record<string, { bg: string; emoji_bg: string; border: string; text: string }> = {
  A: { bg: 'bg-amber-50',   emoji_bg: 'bg-amber-100',  border: 'border-amber-200',   text: 'text-amber-700'  },
  B: { bg: 'bg-blue-50',    emoji_bg: 'bg-blue-100',   border: 'border-blue-200',    text: 'text-blue-700'   },
  C: { bg: 'bg-green-50',   emoji_bg: 'bg-green-100',  border: 'border-green-200',   text: 'text-green-700'  },
  D: { bg: 'bg-orange-50',  emoji_bg: 'bg-orange-100', border: 'border-orange-200',  text: 'text-orange-700' },
  E: { bg: 'bg-rose-50',    emoji_bg: 'bg-rose-100',   border: 'border-rose-200',    text: 'text-rose-700'   },
  F: { bg: 'bg-purple-50',  emoji_bg: 'bg-purple-100', border: 'border-purple-200',  text: 'text-purple-700' },
  G: { bg: 'bg-pink-50',    emoji_bg: 'bg-pink-100',   border: 'border-pink-200',    text: 'text-pink-700'   },
  H: { bg: 'bg-cyan-50',    emoji_bg: 'bg-cyan-100',   border: 'border-cyan-200',    text: 'text-cyan-700'   },
  I: { bg: 'bg-slate-50',   emoji_bg: 'bg-slate-100',  border: 'border-slate-200',   text: 'text-slate-700'  },
  J: { bg: 'bg-indigo-50',  emoji_bg: 'bg-indigo-100', border: 'border-indigo-200',  text: 'text-indigo-700' },
  K: { bg: 'bg-lime-50',    emoji_bg: 'bg-lime-100',   border: 'border-lime-200',    text: 'text-lime-700'   },
  L: { bg: 'bg-yellow-50',  emoji_bg: 'bg-yellow-100', border: 'border-yellow-200',  text: 'text-yellow-700' },
  M: { bg: 'bg-red-50',     emoji_bg: 'bg-red-100',    border: 'border-red-200',     text: 'text-red-700'    },
  N: { bg: 'bg-teal-50',    emoji_bg: 'bg-teal-100',   border: 'border-teal-200',    text: 'text-teal-700'   },
  O: { bg: 'bg-violet-50',  emoji_bg: 'bg-violet-100', border: 'border-violet-200',  text: 'text-violet-700' },
  P: { bg: 'bg-sky-50',     emoji_bg: 'bg-sky-100',    border: 'border-sky-200',     text: 'text-sky-700'    },
  Q: { bg: 'bg-emerald-50', emoji_bg: 'bg-emerald-100',border: 'border-emerald-200', text: 'text-emerald-700'},
  R: { bg: 'bg-fuchsia-50', emoji_bg: 'bg-fuchsia-100',border: 'border-fuchsia-200', text: 'text-fuchsia-700'},
  S: { bg: 'bg-stone-50',   emoji_bg: 'bg-stone-100',  border: 'border-stone-200',   text: 'text-stone-700'  },
  T: { bg: 'bg-amber-50',   emoji_bg: 'bg-amber-100',  border: 'border-amber-200',   text: 'text-amber-700'  },
  U: { bg: 'bg-blue-50',    emoji_bg: 'bg-blue-100',   border: 'border-blue-200',    text: 'text-blue-700'   },
  V: { bg: 'bg-slate-50',   emoji_bg: 'bg-slate-100',  border: 'border-slate-200',   text: 'text-slate-700'  },
  W: { bg: 'bg-indigo-50',  emoji_bg: 'bg-indigo-100', border: 'border-indigo-200',  text: 'text-indigo-700' },
  X: { bg: 'bg-yellow-50',  emoji_bg: 'bg-yellow-100', border: 'border-yellow-200',  text: 'text-yellow-700' },
  Y: { bg: 'bg-teal-50',    emoji_bg: 'bg-teal-100',   border: 'border-teal-200',    text: 'text-teal-700'   },
  Z: { bg: 'bg-gray-50',    emoji_bg: 'bg-gray-100',   border: 'border-gray-200',    text: 'text-gray-600'   },
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
    <section className="bg-[#F8F5F0] border-t border-light-grey py-14 md:py-20">
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12">

        {/* Section header */}
        <div className="mb-10">
          <p className="font-body text-[12px] font-semibold tracking-[0.08em] text-soft-gold uppercase mb-2">
            Find by Cause
          </p>
          <h2
            className="font-display italic text-deep-navy leading-tight tracking-[-0.015em]"
            style={{ fontSize: 'clamp(32px, 4vw, 48px)' }}
          >
            What do you care about?
          </h2>
          <p className="mt-4 font-body text-[16px] text-cool-grey leading-[1.6] max-w-[580px]">
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
                <div className={`w-11 h-11 rounded-xl flex items-center justify-center text-[22px] ${accent.emoji_bg}`}>
                  {cat.emoji}
                </div>

                {/* Name */}
                <div className="flex-1">
                  <p className={`font-body text-[15px] font-semibold leading-snug group-hover:opacity-80 transition-opacity ${accent.text}`}>
                    {cat.name}
                  </p>
                  <p className="font-body text-[12px] text-cool-grey mt-1 leading-relaxed line-clamp-2">
                    {tagline}
                  </p>
                </div>

                {/* Count + arrow */}
                <div className="flex items-center justify-between pt-2 border-t border-black/5">
                  <span className="font-body text-[12px] text-cool-grey">
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
                <div className={`w-9 h-9 rounded-lg flex items-center justify-center text-[18px] ${accent.emoji_bg}`}>
                  {cat.emoji}
                </div>
                <p className="font-body text-[11px] font-medium text-deep-navy/70 group-hover:text-deep-navy leading-tight transition-colors">
                  {cat.name}
                </p>
                {count != null && (
                  <p className="font-body text-[10px] text-cool-grey/70">{count.toLocaleString()}</p>
                )}
              </Link>
            )
          })}
        </div>

        {/* Link to see all */}
        <div className="mt-8 text-center">
          <Link
            to="/directory"
            className="inline-flex items-center gap-2 font-body text-[14px] text-soft-gold hover:text-bright-gold transition-colors"
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
            <h2
              className="mt-3 font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em]"
              style={{ fontSize: 'clamp(30px, 4vw, 50px)' }}
            >
              Save the ones<br />that matter to you
            </h2>
            <p className="mt-5 font-body text-[16px] leading-[1.7]" style={{ color: 'rgba(245,240,235,0.65)' }}>
              Your Giving Wallet holds the nonprofits you want to support.
              Track your intent for each one. Everything stays private — your account, your list, no one else's.
            </p>
            <ul className="mt-7 space-y-3.5">
              {[
                'Save nonprofits as you discover them across Daanaa',
                'Set your giving intent — amount, volunteering, or board interest',
                'Sync across devices with your Google account',
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
              <div className="flex items-center justify-between mb-5">
                <span className="font-display italic text-[18px] text-warm-cream">Your Giving Wallet</span>
                <span className="font-body text-[11px] tracking-[0.04em]" style={{ color: 'rgba(168,159,148,0.55)' }}>3 saved</span>
              </div>
              <div className="space-y-3">
                {[
                  { org: 'Houston Food Bank', location: 'Houston, TX', health: 'Financially healthy', intent: 'Giving · $500/yr', gem: false },
                  { org: 'Literacy Coalition', location: 'Austin, TX', health: 'Financially stable', intent: 'Volunteering · 4 hrs/wk', gem: true },
                  { org: 'Houston SPCA', location: 'Houston, TX', health: 'Financially healthy', intent: null, gem: false },
                ].map(d => (
                  <div key={d.org} className="bg-white/5 rounded-xl px-4 py-3.5">
                    <div className="flex items-start justify-between gap-2 mb-1.5">
                      <p className="font-body text-[13px] text-warm-cream font-semibold leading-snug">{d.org}</p>
                      {d.gem && (
                        <span className="font-body text-[10px] px-1.5 py-0.5 rounded-full bg-violet-500/20 text-violet-300 shrink-0">Hidden gem</span>
                      )}
                    </div>
                    <p className="font-body text-[11px] text-cool-grey mb-2">{d.location}</p>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-body text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300">{d.health}</span>
                      {d.intent && (
                        <span className="font-body text-[10px] text-soft-gold/80">{d.intent}</span>
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
  STABLE:  'bg-amber-50 text-amber-700 border-amber-200',
  CAUTION: 'bg-orange-50 text-orange-700 border-orange-200',
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
            <span className="font-body text-[11px] font-semibold tracking-[0.1em] text-soft-gold uppercase">
              Worth discovering
            </span>
            <h2 className="mt-2 font-display italic text-deep-navy leading-[1.05]" style={{ fontSize: 'clamp(26px, 3.5vw, 38px)' }}>
              The ones doing quiet, steady work
            </h2>
            <p className="mt-3 font-body text-[15px] text-cool-grey max-w-xl leading-[1.6]">
              Small nonprofits — under $500K in revenue — that rank near the top of their peer group.
              Starting points for your own research, not verdicts.
            </p>
          </div>
          <Link
            to="/directory?hidden_gem=1"
            className="shrink-0 font-body text-[13px] text-soft-gold hover:text-bright-gold transition-colors flex items-center gap-1.5"
          >
            See more
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {gems.map((org, i) => {
            const signal = org.v5_context?.score?.health_signal ?? 'STABLE'
            const causes = (org.cause_tags ?? []).slice(0, 2)
            return (
              <div
                key={org.EIN}
                className={`bg-white rounded-2xl border border-light-grey p-5 flex flex-col hover:border-soft-gold/40 hover:shadow-sm transition-all duration-700 ease-out ${inView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
                style={{ transitionDelay: inView ? `${100 + i * 80}ms` : '0ms' }}
              >
                <Link
                  to={`/org/${org.EIN}`}
                  className="font-body text-[14px] font-semibold text-deep-navy hover:text-soft-gold transition-colors leading-snug mb-1"
                >
                  {org.organization_name}
                </Link>
                <p className="font-body text-[12px] text-cool-grey mb-3">
                  {[org.CITY, org.STATE].filter(Boolean).join(', ')}
                  {causes.length > 0 && ` · ${causes.join(', ')}`}
                </p>
                <div className="flex flex-wrap gap-1.5 mb-4">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold border font-body ${HEALTH_CLASSES[signal] ?? HEALTH_CLASSES.STABLE}`}>
                    {HEALTH_LABEL[signal] ?? 'Financially stable'}
                  </span>
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold border bg-violet-50 text-violet-700 border-violet-200 font-body">
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
      <WhatDaanaaDoesSection />
      <HowDiscoveryWorks />
      <FeaturedCause />
      <HiddenGemsSection />
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
      <WalletSection />
      <TiersStrip />
      <StewardshipSection />
      <FinalCTA />
    </div>
  )
}
