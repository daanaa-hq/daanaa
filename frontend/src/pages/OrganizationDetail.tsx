import { useEffect, useRef, useState, useMemo } from 'react'
import { usePageMeta } from '../hooks/usePageMeta'
import { useParams, Link, useNavigate } from 'react-router-dom'
import OrgCard from '../components/OrgCard'
import AnswerCard from '../components/AnswerCard'
import Breadcrumb from '../components/Breadcrumb'
import DonationReturnPrompt from '../components/DonationReturnPrompt'
import { useDonationReturnPrompt } from '../hooks/useDonationReturnPrompt'
import { getTierSummary, getTierFromOrg } from '../components/TrustBadge'
import BadgeChip from '../components/BadgeChip'
import MistakeRegistry from '../components/MistakeRegistry'

import { useApi } from '../hooks/useApi'
import { useFeatureFlag } from '../hooks/useFeatureFlag'
import { useWallet } from '../contexts/WalletContext'
import { getOrganization, getScoreHistory, getFinancials, getSimilarOrgs, getOrgVolunteerEvents, getServiceArea, getMyOrgs, getPortalToken } from '../data/api'
import { getNteeLabel } from '../data/ntee'
import type { ApiOrganization, ScoreSnapshot, ApiFinancialRecord, VolunteerEvent, ServiceArea } from '../data/api'
import { formatCurrency, formatNumber, formatEIN } from '../data/organizations'
import { getOrgBadges } from '../utils/badges'
import { getActionRowLinks } from '../utils/actionRow'
import { trackEvent } from '../utils/analytics'
import OrgWallPanel from '../components/OrgWallPanel'
import AiBadge from '../components/AiBadge'
import { useAuth } from '../contexts/AuthContext'
import { GoogleSignInButton } from '../components/GoogleSignInButton'
import V5Context from '../components/V5Context'
import CohortContext from '../components/CohortContext'
import PeerContextBreakdown from '../components/PeerContextBreakdown'
import DonationAttributionBanner from '../components/DonationAttributionBanner'
import ImpactWidget from '../components/ImpactWidget'
import OrgEnrichmentCard from '../components/OrgEnrichmentCard'
import GuildSection from '../components/GuildSection'
import { sentenceCase } from '../utils/sentenceCase'
import GiveYourWayRouter from '../components/GiveYourWayRouter'
// ---- Metric Card ----
// ---- Data freshness badge ----
function DataFreshnessBadge({ taxYear, dataSource, updatedAt }: {
  taxYear: number | null;
  dataSource: string | null;
  updatedAt: string | null;
}) {
  const sourceLabel = dataSource === 'propublica' ? 'ProPublica'
    : dataSource === 'nccs' ? 'NCCS'
    : 'IRS';

  const yearLabel = taxYear ? `FY ${taxYear}` : null;

  const updatedLabel = (() => {
    if (!updatedAt) return null;
    try {
      const d = new Date(updatedAt);
      return `Updated ${d.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}`;
    } catch { return null; }
  })();

  return (
    <div className="mt-4 flex flex-wrap gap-2">
      {yearLabel && (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-soft-gold/15 text-deep-gold font-body text-[11px] font-medium">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
          {yearLabel}
        </span>
      )}
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-navy-mid/10 text-cool-grey font-body text-[11px]">
        Source: {sourceLabel}
      </span>
      {updatedLabel && (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-navy-mid/10 text-cool-grey font-body text-[11px]">
          {updatedLabel}
        </span>
      )}
    </div>
  );
}

function hasKnownDataSource(src: string | null) {
  return src === 'propublica' || src === 'irs_soi'
}

function formatOrdinal(n: number): string {
  const r = Math.round(n)
  const mod100 = r % 100
  if (mod100 >= 11 && mod100 <= 13) return `${r}th`
  const mod10 = r % 10
  if (mod10 === 1) return `${r}st`
  if (mod10 === 2) return `${r}nd`
  if (mod10 === 3) return `${r}rd`
  return `${r}th`
}

// Decode a peer_group string like "B24:Medium" into a readable label
// Plain-English size for the "Size" field. The stored revenue_band is a
// model-specific scoring tier (0-7) — meaningless to a reader — so we derive a
// universal size from actual annual revenue instead. Null when revenue is
// unknown, so we hide the field rather than guess.
function nonprofitSizeLabel(revenue: number | null | undefined): string | null {
  if (revenue == null || revenue <= 0) return null
  if (revenue < 250_000) return 'Micro'
  if (revenue < 1_000_000) return 'Small'
  if (revenue < 10_000_000) return 'Mid-size'
  if (revenue < 100_000_000) return 'Large'
  return 'Major'
}

// Single source of truth for the ProPublica Nonprofit Explorer org URL.
// Was hand-built inline in 3 places; centralized so the path never drifts.
function propublicaOrgUrl(ein: string): string {
  return `https://projects.propublica.org/nonprofits/organizations/${ein.replace(/-/g, '')}`
}

function peerGroupLabel(peerGroup: string | null, revenueBand: string | null): string {
  if (!peerGroup) return ''
  if (peerGroup.includes(':')) {
    const [code, band] = peerGroup.split(':', 2)
    return `${band}-sized ${code} nonprofits`
  }
  const band = revenueBand ? `${revenueBand}-sized ` : ''
  return `${band}${peerGroup} category nonprofits`
}

function scoreSignals(org: ApiOrganization): { label: string; ok: boolean; warn: boolean }[] {
  const signals: { label: string; ok: boolean; warn: boolean }[] = []

  if (org.months_of_reserve != null) {
    const m = org.months_of_reserve
    signals.push({
      label: m >= 3 ? 'Healthy financial cushion'
           : m >= 1 ? 'Thin reserves'
           : 'Little financial safety net',
      ok: m >= 3,
      warn: m < 1,
    })
  }

  if (org.total_revenue != null && org.total_expenses != null && org.total_expenses > 0) {
    const ratio = org.total_revenue / org.total_expenses
    signals.push({
      label: ratio >= 1.05 ? 'Bringing in more than they spend'
           : ratio >= 0.95 ? 'Roughly breaking even'
           : 'Spending more than they raise',
      ok: ratio >= 0.95,
      warn: ratio < 0.95,
    })
  }

  return signals
}

function summaryLine(org: ApiOrganization): string {
  if (org.months_of_reserve != null) {
    const m = Math.round(org.months_of_reserve)
    const feel = m >= 6 ? 'a strong cushion' : m >= 3 ? 'a healthy buffer' : 'limited runway'
    return `They carry about ${m} months of savings, ${feel}.`
  }
  return `Ranked within a peer group of ${org.peer_total ? org.peer_total.toLocaleString() : 'similar'} nonprofits.`
}

// ---- Convert API org to local format ----
function adaptOrg(apiOrg: ApiOrganization) {
  const scored = hasKnownDataSource(apiOrg.data_source) &&
    (apiOrg.peer_percentile ?? apiOrg.ntee1_percentile) !== null
  const meritScore = Math.round(apiOrg.peer_percentile ?? apiOrg.ntee1_percentile ?? 0)
  return {
    id: apiOrg.EIN,
    name: apiOrg.organization_name,
    ein: apiOrg.EIN,
    city: apiOrg.CITY || '',
    state: apiOrg.STATE || '',
    category: apiOrg.NTEE1 || '',
    nteecc: apiOrg.NTEECC || '',
    subcategory: apiOrg.NTEECC || apiOrg.NTEE1 || '',
    meritScore,
    hasScore: scored,
    revenue: apiOrg.total_revenue ?? 0,
    assets: 0,
    employees: 0,
    founded: 0,
    // Missions harvested from Form 990 arrive in the filing's all-caps. Case is
    // fixed here, at the single point the page's org object is built, so every
    // consumer below gets readable text. The filing itself stays verbatim in the
    // database; this is presentation only, and mixed-case text passes through.
    mission: sentenceCase(apiOrg.mission),
    website: apiOrg.website || '',
    programs: [] as string[],
    leadership: [] as { name: string; title: string; initials: string }[],
    boardSize: 0,
    programEfficiency: meritScore,
    fundraisingRatio: 0,
    operatingReserve: 0,
    transparencyScore: meritScore,
    categoryRank: apiOrg.category_rank,
    categoryTotal: apiOrg.category_total,
    stateCategoryRank: apiOrg.state_category_rank,
    stateCategoryTotal: apiOrg.state_category_total,
    latestTaxYear: apiOrg.latest_tax_year ?? null,
    dataSource: apiOrg.data_source ?? null,
    updatedAt: apiOrg.updated_at ?? null,
    peerPercentile: apiOrg.peer_percentile,
    peerRank: apiOrg.peer_rank,
    peerTotal: apiOrg.peer_total,
    peerGroup: apiOrg.peer_group,
    revenueBand: apiOrg.revenue_band,
    peerGroupLabel: peerGroupLabel(apiOrg.peer_group, apiOrg.revenue_band),
    hasMission: !!(apiOrg.mission && apiOrg.mission.length > 0),
    hasWebsite: !!(apiOrg.website && apiOrg.website.length > 0),
  }
}

const AI_MISSION_SOURCES = new Set(['ai_ntee', 'ai_haiku', 'ai_web', 'ai_generated'])
function HeroMission({ mission, missionSrc }: { mission: string; missionSrc: string }) {
  const cleaned = mission.replace(/^[""\s]+|[""\s]+$/g, '')
  return (
    <div className="mt-4 flex items-start gap-2">
      <p className="font-body text-[15px] text-muted-cream/90 leading-[1.7] max-w-[600px] italic">
        &ldquo;{cleaned}&rdquo;
      </p>
      {AI_MISSION_SOURCES.has(missionSrc) && (
        <span className="shrink-0 mt-1">
          <AiBadge />
        </span>
      )}
    </div>
  )
}

function EinCopyButton({ ein }: { ein: string }) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(ein)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      setCopied(false)
    }
  }

  return (
    <button
      onClick={handleCopy}
      className={`shrink-0 px-2 py-1 rounded-md font-body text-[11px] font-semibold transition-all ${
        copied ? 'bg-emerald-500/20 text-emerald-300' : 'bg-soft-gold/15 text-soft-gold hover:bg-soft-gold/25'
      }`}
    >
      {copied ? 'Copied!' : 'Copy'}
    </button>
  )
}

// One shared control for the funding (green) and volunteering (red) intent
// hearts. Both live on the page in two placements each (compact icon in the
// header, labeled pill lower down) — this renders all four from one place so
// the toggle logic is never duplicated. The hearts capture private wallet
// intent; the org sees only anonymized aggregate signals (Stewardship P2/P5).
function WalletHeartButton({
  kind, variant, isActive, onToggle,
  titleActive, titleInactive, ariaActive, ariaInactive, labelActive, labelInactive,
}: {
  kind: 'funding' | 'volunteering'
  variant: 'icon' | 'pill'
  isActive: boolean
  onToggle: () => void
  titleActive: string
  titleInactive: string
  ariaActive?: string
  ariaInactive?: string
  labelActive?: string
  labelInactive?: string
}) {
  const color = kind === 'funding' ? '#22c55e' : '#ef4444'
  const bg = isActive ? `${color}20` : 'rgb(var(--warm-cream-rgb) / 0.08)'
  const borderColor = isActive ? color : 'rgb(var(--warm-cream-rgb) / 0.2)'
  const heart = (size: number) => (
    <svg width={size} height={size} viewBox="0 0 24 24"
      fill={isActive ? color : 'none'}
      stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
    </svg>
  )

  if (variant === 'icon') {
    return (
      <button
        onClick={onToggle}
        title={isActive ? titleActive : titleInactive}
        aria-label={isActive ? ariaActive : ariaInactive}
        className="w-9 h-9 rounded-full flex items-center justify-center transition-all duration-700"
        style={{ background: bg, border: `1px solid ${borderColor}` }}
      >
        {heart(16)}
      </button>
    )
  }

  return (
    <button
      onClick={onToggle}
      title={isActive ? titleActive : titleInactive}
      className="inline-flex items-center gap-2 px-4 py-2 rounded-full font-body text-[13px] font-medium transition-all duration-700"
      style={{ background: bg, border: `1px solid ${borderColor}`, color: isActive ? color : 'var(--warm-cream)' }}
    >
      {heart(14)}
      {isActive ? labelActive : labelInactive}
    </button>
  )
}

// ---- Main Page ----
export default function OrganizationDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user, getIdToken } = useAuth()
  const { isInFunding, isInVolunteering, addToFunding, addToVolunteering,
          removeFromFunding, removeFromVolunteering } = useWallet()
  const { trackDonateClick, promptState, dismiss: dismissDonationPrompt } = useDonationReturnPrompt()
  const [portalLoading, setPortalLoading] = useState(false)
  const [portalError, setPortalError]     = useState<string | null>(null)
  const [selectedBadge, setSelectedBadge] = useState<string | null>(null)
  // 990 Part VII — public compensation disclosure
  const [ppLeadership, setPpLeadership] = useState<{name:string;title:string;initials:string;compensation?:number}[]>([])
  const [ppFilingYear, setPpFilingYear] = useState<number|null>(null)
  const [enrichmentData, setEnrichmentData] = useState<any>(null)
  const [enrichmentLoading, setEnrichmentLoading] = useState(false)


  // Hook must run unconditionally — keep it above any early return (Rules of Hooks)
  const showPeerContextBreakdown = useFeatureFlag('peer_context_breakdown', 1) // 1% rollout

  const { data: apiOrg, loading: orgLoading, error: orgError } = useApi(
    () => getOrganization(id || '', { includeEnrichment: true }),
    [id]
  )

  const { data: scoreHistoryData } = useApi(
    () => id ? getScoreHistory(id) : Promise.resolve({ ein: '', history: [], total: 0 }),
    [id]
  )
  const scoreHistory: ScoreSnapshot[] = scoreHistoryData?.history ?? []

  const { data: financialsData } = useApi(
    () => id ? getFinancials(id) : Promise.resolve({ ein: '', financials: [], total: 0 }),
    [id]
  )
  const financials: ApiFinancialRecord[] = financialsData?.financials ?? []

  const { data: similarData } = useApi(
    () => id ? getSimilarOrgs(id, { limit: 6 }) : Promise.resolve({ results: [], mode: '', diamonds_only: false }),
    [id]
  )
  const { data: volunteerEventsData } = useApi(
    () => id ? getOrgVolunteerEvents(id) : Promise.resolve({ events: [] }),
    [id]
  )
  const volunteerEvents: VolunteerEvent[] = volunteerEventsData?.events ?? []
  const { data: serviceAreaData } = useApi(
    () => id ? getServiceArea(id) : Promise.resolve({ area_type: null, area_values: [], updated_at: null } as ServiceArea),
    [id]
  )
  const serviceArea = serviceAreaData ?? null
  const similarApiOrgs: ApiOrganization[] = (similarData?.results ?? []) as ApiOrganization[]

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [id])

  // Fetch Phase 2a enrichment data (contact + programs) from S3
  useEffect(() => {
    if (!id || !apiOrg) return

    setEnrichmentLoading(true)
    fetch(`/api/organizations/${id}?include_enrichment=1`)
      .then(r => r.json())
      .then(data => {
        setEnrichmentData({
          contact: data.contact || null,
          programs: data.programs || null
        })
        setEnrichmentLoading(false)
      })
      .catch(err => {
        console.debug('Enrichment fetch failed (expected if S3 unavailable):', err)
        setEnrichmentLoading(false)
      })
  }, [id, apiOrg])

  // Fire anonymous view event (fire-and-forget, never awaited)
  useEffect(() => {
    if (!id) return
    const ein = id.replace(/\D/g, '').slice(0, 9)
    if (ein.length !== 9) return
    const base = import.meta.env.VITE_API_URL || ''
    fetch(`${base}/api/org/${ein}/view`, { method: 'POST' }).catch(() => {})
  }, [id])

  // E6: Pull leadership from ProPublica 990 Part VII — public compensation disclosure
  useEffect(() => {
    if (!id) return
    const ein = id.replace(/\D/g, '').slice(0, 9)
    if (ein.length !== 9) return
    fetch(`https://projects.propublica.org/nonprofits/api/v2/organizations/${ein}.json`)
      .then(r => { if (!r.ok) throw new Error('pp_not_ok'); return r.json() })
      .then((data: {filings_with_data?: Array<{tax_prd_yr?: number; people?: Array<{name:string;title:string;compensation?:number}>}>; filings?: Array<{tax_prd_yr?: number; people?: Array<{name:string;title:string;compensation?:number}>}>}) => {
        const filings = data?.filings_with_data ?? data?.filings ?? []
        if (!filings.length) return
        const filing = filings[0]
        if (filing?.tax_prd_yr) setPpFilingYear(filing.tax_prd_yr)
        const people = filing?.people ?? []
        if (!people.length) return
        const mapped = people.slice(0, 6).map((p) => {
          const parts = (p.name || '').trim().split(/\s+/)
          const initials = parts.length >= 2
            ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
            : (parts[0]?.[0] ?? '?').toUpperCase()
          return {
            name: p.name || '',
            title: p.title || '',
            initials,
            compensation: (p.compensation && p.compensation > 0) ? p.compensation : undefined,
          }
        }).filter(p => p.name)
        setPpLeadership(mapped)
      })
      .catch(() => {})
  }, [id])

  const org = apiOrg ? adaptOrg(apiOrg) : null

  const rawSimilarOrgs = useMemo(() => {
    if (similarApiOrgs.length > 0) return similarApiOrgs.slice(0, 6)
    if (!apiOrg?.similar_organizations) return []
    return (apiOrg.similar_organizations as ApiOrganization[])
      .filter((o) => o.EIN !== apiOrg.EIN)
      .slice(0, 4)
  }, [apiOrg, similarApiOrgs])

  const similarOrgs = useMemo(() => rawSimilarOrgs.map(adaptOrg), [rawSimilarOrgs])

  const metaTitle = apiOrg?.organization_name ?? ''
  const metaDesc = apiOrg
    ? `${apiOrg.organization_name} is a registered US nonprofit${apiOrg.CITY ? ` in ${apiOrg.CITY}, ${apiOrg.STATE}` : ''}. ${apiOrg.mission ? sentenceCase(apiOrg.mission).slice(0, 120).replace(/\s+\S+$/, '') + '.' : 'Public financial context and peer comparison available.'}`
    : ''

  const ogImage = apiOrg && apiOrg.NTEE1
    ? `https://daanaa.org/categories/${apiOrg.NTEE1}.png`
    : 'https://daanaa.org/og-image-v2.png'

  usePageMeta(metaTitle, { description: metaDesc, ogImage })

  // JSON-LD is server-rendered into the initial HTML (_org_jsonld in droplet_api.py,
  // @type NGO) so crawlers see it without executing JS. This client-side hook used to
  // overwrite that correct value with a worse one (@type LocalBusiness, fewer fields,
  // and a wrong URL path -- /organizations/ instead of the real /org/ route) on every
  // page load. Removed 2026-07-10 eng review finding 1A -- do not re-add without also
  // updating droplet_api.py's _org_jsonld to match, or the two will fight again.

  if (orgLoading) {
    return (
      <div className="min-h-[100dvh] flex items-center justify-center bg-deep-navy">
        <div className="w-8 h-8 border-2 border-soft-gold border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  // Check for invalid EIN format
  const ein = id ? id.replace(/\D/g, '') : ''
  if (ein.length !== 9) {
    return (
      <div className="min-h-[100dvh] flex items-center justify-center bg-warm-cream">
        <div className="text-center">
          <h2 className="font-display italic text-deep-navy text-[32px]">Invalid EIN</h2>
          <p className="mt-2 font-body text-cool-grey">EIN must be 9 digits. Please check the URL and try again.</p>
          <Link to="/directory" className="mt-4 inline-block font-body text-soft-gold hover:text-bright-gold transition-colors">
            Back to Directory
          </Link>
        </div>
      </div>
    )
  }

  if (orgError || !org) {
    return (
      <div className="min-h-[100dvh] flex items-center justify-center bg-warm-cream">
        <div className="text-center">
          <h2 className="font-display italic text-deep-navy text-[32px]">Organization not found</h2>
          <p className="mt-2 font-body text-cool-grey">{orgError || 'The requested organization could not be loaded.'}</p>
          <Link to="/directory" className="mt-4 inline-block font-body text-soft-gold hover:text-bright-gold transition-colors">
            Back to Directory
          </Link>
        </div>
      </div>
    )
  }

  const badges = getOrgBadges(apiOrg!)
  // Computed once and reused — the Ways-to-Support card and the public-record
  // fallback both need these links (was called twice). Lean: no repeated work.
  const actionLinks = getActionRowLinks(apiOrg!)

  return (
    <div className="min-h-[100dvh]">
      {/* E7: Print stylesheet — hides chrome, keeps org content */}
      <style media="print">{`
        @media print {
          nav, footer, .print-hide { display: none !important; }
          body { background: white !important; color: #0A1628 !important; }
          .bg-deep-navy { background: white !important; color: #0A1628 !important; }
          .text-warm-cream, .text-muted-cream { color: #0A1628 !important; }
          .text-cool-grey { color: #374151 !important; }
        }
      `}</style>
      <Breadcrumb items={[{ label: 'Home', href: '/' }, { label: 'Directory', href: '/directory' }, { label: org?.name || 'Organization' }]} />
      {/* Profile Header */}
      <div className="bg-deep-navy pt-[72px] relative overflow-hidden" style={{ background: 'linear-gradient(to bottom, rgb(var(--deep-navy-rgb)) 70%, transparent)' }}>
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 py-8 md:py-12 lg:py-16">
          <div className="flex items-center justify-between gap-2 mb-6">
            <div className="flex items-center gap-2">
              <Link to="/" className="font-body text-[12px] tracking-[0.02em] text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
              <span className="text-muted-cream">/</span>
              <Link to="/directory" className="font-body text-[12px] tracking-[0.02em] text-muted-cream hover:text-warm-cream transition-colors">Directory</Link>
              <span className="text-muted-cream">/</span>
              <span className="font-body text-[12px] tracking-[0.02em] text-muted-cream truncate max-w-[200px]">{org.name}</span>
            </div>
            <div className="flex items-center gap-2">
              {/* Green heart — funding intent */}
              <WalletHeartButton
                kind="funding"
                variant="icon"
                isActive={isInFunding(org.ein)}
                onToggle={() => isInFunding(org.ein) ? removeFromFunding(org.ein) : addToFunding(apiOrg?.EIN ?? org.ein)}
                titleActive="Remove from funding list"
                titleInactive="Add to funding list"
                ariaActive="Remove from funding list"
                ariaInactive="Fund this org"
              />
              {/* Red heart — volunteering intent */}
              <WalletHeartButton
                kind="volunteering"
                variant="icon"
                isActive={isInVolunteering(org.ein)}
                onToggle={() => isInVolunteering(org.ein) ? removeFromVolunteering(org.ein) : addToVolunteering(apiOrg?.EIN ?? org.ein)}
                titleActive="Remove from volunteer list"
                titleInactive="I want to volunteer here"
                ariaActive="Remove from volunteer list"
                ariaInactive="Volunteer here"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[1fr_auto] gap-8 items-start">
            <div>
              {/* ORG NAME & LOCATION */}
              <div className="flex items-start gap-4 sm:gap-5">
                <div className="shrink-0 mt-1.5 w-14 h-14 sm:w-16 sm:h-16 rounded-2xl flex items-center justify-center border border-white/15 bg-white/[0.06]">
                  <span className="font-display text-[22px] sm:text-[26px] text-soft-gold leading-none tracking-tight">
                    {org.name.split(/\s+/).filter(Boolean).slice(0, 2).map((w: string) => w[0]).join('').toUpperCase()}
                  </span>
                </div>
                <h1 className="font-display italic text-warm-cream leading-[0.95] tracking-[-0.02em]" style={{ fontSize: 'clamp(34px, 5.5vw, 66px)' }}>
                  {org.name}
                </h1>
              </div>
              <div className="flex items-center gap-3 mt-6 flex-wrap">
                <div className="flex items-center gap-2">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#A89F94" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
                  </svg>
                  <span className="font-body text-[16px] text-muted-cream">{org.city}, {org.state}</span>
                </div>
              </div>

              {org.mission && (
                <div className="mt-8">
                  <HeroMission mission={org.mission} missionSrc={apiOrg?.data_badges?.mission ?? apiOrg?.mission_source ?? ''} />
                </div>
              )}

              {/* Give-your-way router: donor picks the method (DAF, check, etc.)
                  Selection stays client-side. 96% of orgs have address. */}
              {apiOrg! && (
                <GiveYourWayRouter
                  ein={apiOrg.EIN}
                  organizationName={apiOrg.organization_name}
                  streetAddress={apiOrg.street_address}
                  city={apiOrg.CITY}
                  state={apiOrg.STATE}
                  donateUrl={apiOrg.donate_url}
                  donateUrlStatus={apiOrg.donate_url_status}
                  website={apiOrg.website}
                  websiteStatus={apiOrg.website_status}
                />
              )}

              {/* Answer card: legit / deductible / healthy in <10s, for every
                  org including the ~82% with no financial score and revoked
                  orgs reached by direct/stale link. See AnswerCard.tsx. */}
              <div className="mt-8">
                {apiOrg! && <AnswerCard org={apiOrg!} />}
              </div>

              {/* Badge row -- click any badge to see what earned it */}
              <div className="mt-6 flex flex-wrap gap-2">
                {badges.map(badge => (
                  <BadgeChip
                    key={badge.id}
                    badge={badge}
                    size="md"
                    variant="dark"
                    onClick={() => setSelectedBadge(selectedBadge === badge.id ? null : badge.id)}
                    active={selectedBadge === badge.id}
                  />
                ))}
              </div>

              {/* Inline badge detail -- appears below the row when a badge is selected */}
              {selectedBadge && (() => {
                const b = badges.find(x => x.id === selectedBadge)
                return b ? (
                  <div className="mt-3 max-w-[520px] bg-white/8 border border-white/12 rounded-xl px-4 py-3">
                    <p className="font-body text-[13px] text-warm-cream/85 leading-[1.65]">{b.detail}</p>
                    <p className="mt-2 font-body text-[10px] text-muted-cream tracking-[0.01em]">{b.source}</p>
                  </div>
                ) : null
              })()}

              {/* Financial stress indicator */}
              {apiOrg!.months_of_reserve !== null && apiOrg!.months_of_reserve < 3 && (
                <div
                  className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-full font-body text-[12px] font-medium border"
                  style={apiOrg!.months_of_reserve < 0
                    ? { backgroundColor: 'rgba(139,26,26,0.22)', color: '#D07070', borderColor: 'rgba(139,26,26,0.45)' }
                    : { backgroundColor: 'rgba(245,158,11,0.18)', color: '#FCD34D', borderColor: 'rgba(245,158,11,0.38)' }}
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-current flex-shrink-0" />
                  {apiOrg!.months_of_reserve < 0
                    ? 'Negative net assets. This group owes more than it owns.'
                    : `Net assets cover only ${Math.round(apiOrg!.months_of_reserve)} months of costs`}
                </div>
              )}

              {/* Seeking board members */}
              {apiOrg!.seeking_board_members && (
                <div className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-full font-body text-[12px] font-medium bg-blue-50 text-blue-700 border border-blue-200">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                    <circle cx="9" cy="7" r="4"/>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                  </svg>
                  Looking for board members
                </div>
              )}

              {/* Cause tags -- AI-generated (beta) until the organization sets its own */}
              {Array.isArray(apiOrg!.cause_tags) && apiOrg!.cause_tags.length > 0 && (
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  {(apiOrg!.cause_tags as string[]).map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center px-2.5 py-1 rounded-full font-body text-[11px] tracking-[0.02em] text-muted-cream/80 border border-white/10 bg-white/6"
                    >
                      {tag}
                    </span>
                  ))}
                  {(apiOrg?.data_badges?.tags === 'ai_generated' || apiOrg?.mission_source === 'ai_ntee' || apiOrg?.mission_source === 'ai_generated') && (
                    <AiBadge title="These search tags were suggested by AI from public records. The organization can set its own once it claims this page." />
                  )}
                </div>
              )}

              <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-3">
                {[
                  (() => {
                    const calIcon = (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>)
                    if (org.founded > 0) return { icon: calIcon, label: 'Founded', value: String(org.founded) }
                    const rulingYear = apiOrg!.ruling_date?.slice(0, 4)
                    if (rulingYear) return { icon: calIcon, label: 'IRS recognized', value: rulingYear }
                    return null
                  })(),
                  org.revenue > 0 && { icon: (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>), label: `Revenue${(org as any).latestTaxYear ? ` FY ${(org as any).latestTaxYear}` : ''}`, value: formatCurrency(org.revenue) },
                  (apiOrg!.employee_count ?? 0) > 0 && { icon: (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>), label: 'Employees', value: formatNumber(apiOrg!.employee_count!) },
                  { icon: (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>), label: 'EIN', value: formatEIN(org.ein) },
                ].filter(Boolean).map((stat, i, arr) => (
                  <div key={(stat as {label: string}).label} className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      {(stat as any).icon}
                      <div>
                        <span className="block font-body text-[11px] tracking-[0.02em] text-muted-cream">{(stat as any).label}</span>
                        <span className="block font-body text-[14px] font-medium text-warm-cream">{(stat as any).value}</span>
                      </div>
                    </div>
                    {i < arr.length - 1 && <div className="hidden md:block w-[1px] h-8 bg-navy-mid" />}
                  </div>
                ))}
              </div>

              {/* Ways to Support card: dedicated buttons for Website / Donate / Volunteer
                  with verification status and role clarity disclaimer. */}
              {(() => {
                const { websiteUrl, websiteLabel, isWebsiteBeta, donateUrl, isDonateBeta, volunteerUrl, hasAnyLink } = actionLinks

                if (!hasAnyLink) return null;

                return (
                  <div className="mt-8 p-6 rounded-lg border border-white/10 bg-white/[0.03] backdrop-blur-sm">
                    <h3 className="font-body text-[14px] font-semibold text-soft-gold uppercase tracking-[0.05em] mb-4">Ways to Support</h3>

                    {/* Giving-first CTA hierarchy (Stage 1 redesign): Donate is the
                        primary action — first in the row, emerald, larger. Website is
                        secondary. Volunteer is a tertiary link. Mission: make giving easy,
                        so the donate decision is never ambiguous. */}
                    <div className="flex flex-wrap items-center gap-3 mb-4">
                      {donateUrl && (
                        <a
                          href={donateUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={() => { trackEvent('Donate Click'); trackDonateClick(apiOrg!.EIN, apiOrg!.organization_name) }}
                          aria-label={`Donate to ${apiOrg!.organization_name}`}
                          className="inline-flex items-center gap-2 font-body text-[15px] font-semibold bg-emerald-500 text-deep-navy px-6 py-3 rounded-lg hover:bg-emerald-400 transition-colors"
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
                          Donate
                        </a>
                      )}
                      {websiteUrl && (
                        <a
                          href={websiteUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 font-body text-[15px] font-semibold bg-soft-gold text-deep-navy px-6 py-3 rounded-lg hover:bg-bright-gold transition-colors"
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
                          {websiteLabel}
                        </a>
                      )}
                      {volunteerUrl && (
                        <a
                          href={volunteerUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 font-body text-[14px] font-semibold border border-warm-cream/40 text-warm-cream px-5 py-2.5 rounded-lg hover:border-warm-cream/60 hover:bg-warm-cream/5 transition-colors"
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                          Volunteer
                        </a>
                      )}
                    </div>

                    {(isWebsiteBeta || isDonateBeta) && (
                      <div className="flex items-start gap-2 mb-3 p-2 rounded bg-white/5">
                        <AiBadge title="Found by AI from public records. Not yet confirmed by the organization." />
                        <div className="flex-1">
                          <p className="font-body text-[12px] text-muted-cream">
                            {isDonateBeta ? 'Donation link found by AI, not yet confirmed by the organization.' : 'Website found by AI, not yet confirmed by the organization.'}
                            <Link to={`/for-nonprofits?ein=${apiOrg!.EIN}`} className="ml-1.5 underline underline-offset-2 hover:text-warm-cream transition-colors">Verify here.</Link>
                          </p>
                        </div>
                      </div>
                    )}

                    <p className="font-body text-[12px] text-muted-cream leading-[1.6]">
                      All links are direct to the organization. <strong>Daanaa doesn't process donations</strong> — you give directly to them, on their site. External links from public records.
                    </p>
                  </div>
                );
              })()}

              {/* Contact phone */}
              {apiOrg?.phone && (
                <div className="mt-8">
                  <a
                    href={`tel:${apiOrg.phone}`}
                    className="inline-flex items-center gap-2 font-body text-[15px] font-medium text-soft-gold hover:text-bright-gold transition-colors"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
                    {apiOrg.phone}
                  </a>
                  <p className="mt-1.5 font-body text-[11px] text-cool-grey">
                    Contact them to give, volunteer, or learn more.
                  </p>
                </div>
              )}

              {/* Volunteer + public record fallback */}
              {(() => {
                const { websiteUrl } = actionLinks

                return (
                  <>
                    <div className="mt-8 flex flex-wrap items-center gap-3">
                      <WalletHeartButton
                        kind="funding"
                        variant="pill"
                        isActive={isInFunding(org.ein)}
                        onToggle={() => isInFunding(org.ein) ? removeFromFunding(org.ein) : addToFunding(apiOrg?.EIN ?? org.ein)}
                        titleActive="Remove from donation list"
                        titleInactive="Add to donation list"
                        labelActive="In donation list"
                        labelInactive="Add to donation list"
                      />
                      {/* Stage 1 (Time features deferred): interest signal only. No hour
                          logging or commitment promise yet. Maps to the existing wallet
                          volunteering list — no forked data model. */}
                      <WalletHeartButton
                        kind="volunteering"
                        variant="pill"
                        isActive={isInVolunteering(org.ein)}
                        onToggle={() => isInVolunteering(org.ein) ? removeFromVolunteering(org.ein) : addToVolunteering(apiOrg?.EIN ?? org.ein)}
                        titleActive="Remove from your volunteer list"
                        titleInactive="Let them know you are interested in volunteering"
                        labelActive="Interested in volunteering"
                        labelInactive="Interested in volunteering?"
                      />
                      {!websiteUrl && (
                        <a
                          href={propublicaOrgUrl(org.ein)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 font-body text-[13px] text-muted-cream/80 underline underline-offset-2 hover:text-warm-cream transition-colors"
                        >
                          View public record
                          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M7 17 17 7M17 7H8M17 7v9"/></svg>
                        </a>
                      )}
                      {/* E7: Print / Save */}
                      <button
                        onClick={() => window.print()}
                        title="Print or save this page"
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-warm-cream/30 font-body text-[12px] text-warm-cream/70 hover:text-warm-cream hover:border-warm-cream/50 transition-colors"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
                        Print
                      </button>
                    </div>
                    {/* Give by EIN: always present, never blank (design doc
                        "empty action row" requirement) -- previously only
                        shown when there was no website link. */}
                    <div className="mt-5 rounded-xl border border-white/10 bg-white/[0.04] px-5 py-4 max-w-[480px]">
                      <p className="font-body text-[11px] tracking-[0.06em] uppercase font-medium text-muted-cream mb-3">How to give</p>
                      <div className="flex flex-col gap-2.5">
                        <div className="flex items-start gap-2">
                          <span className="font-body text-[12px] text-muted-cream shrink-0 mt-0.5">EIN:</span>
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="font-body text-[13px] font-semibold text-warm-cream">{apiOrg!.EIN}</span>
                              <EinCopyButton ein={apiOrg!.EIN} />
                            </div>
                            <p className="font-body text-[11px] text-muted-cream/70 mt-0.5">Use this for a donor-advised fund gift or when writing a check.</p>
                          </div>
                        </div>
                        {apiOrg!.street_address && (
                          <div className="flex items-start gap-2">
                            <span className="font-body text-[12px] text-muted-cream shrink-0 mt-0.5">Address:</span>
                            <span className="font-body text-[12px] text-warm-cream/90">
                              {[apiOrg!.street_address, apiOrg!.CITY, apiOrg!.STATE, apiOrg!.zipcode].filter(Boolean).join(', ')}
                            </span>
                          </div>
                        )}
                      </div>
                      {!apiOrg!.street_address && (
                        <p className="mt-2.5 font-body text-[11px] text-muted-cream/60">
                          Most donor-advised funds accept gifts to any IRS-recognized nonprofit by EIN alone.
                        </p>
                      )}
                    </div>
                  </>
                );
              })()}

              {/* Loop-closer: connect the give moment to a private record.
                  Appears under whichever CTA rendered. */}
            </div>

            {!(apiOrg!.source === 'bmf_stub' && apiOrg!.total_revenue == null) &&
             apiOrg!.org_status !== 'revoked' && apiOrg!.irs_revoked !== 1 && (
            <div className="flex flex-col items-center gap-3 lg:pt-4">
              {/* Lamp tier retired from donor-facing profiles 2026-07-17
                  (founder-approved): its facts are covered by the plain
                  elements below, and the tier vocabulary read as a grade
                  (P4). Tiers live on in the nonprofit-facing claim flow. */}
              {/* IRS verification -- a real, defensible fact for every org */}
              <div className="flex flex-col items-center gap-2 text-center">
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/15 text-emerald-400 font-body text-[12px] font-medium">
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
                  Registered US Nonprofit
                </span>
                {apiOrg!.latest_tax_year && (
                  <span className="font-body text-[11px] text-muted-cream">
                    Annual report filed · {apiOrg!.latest_tax_year}
                  </span>
                )}
                {/* Claimed / Unclaimed badge -- Yelp-style */}
                {apiOrg!.claim_status === 'active' ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded border border-soft-gold/50 text-soft-gold font-body text-[11px] font-medium">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
                    Claimed
                  </span>
                ) : (
                  <Link
                    to={`/for-nonprofits?ein=${apiOrg!.EIN}`}
                    title="Is this your nonprofit? Claim your page free."
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded border border-muted-cream/40 text-muted-cream hover:border-soft-gold/60 hover:text-soft-gold font-body text-[11px] transition-colors"
                  >
                    Unclaimed
                  </Link>
                )}
              </div>
              <Link
                to="/methodology"
                className="font-body text-[11px] text-muted-cream hover:text-soft-gold transition-colors"
              >
                How we assess nonprofits →
              </Link>
            </div>
            )}{/* end stub score conditional */}
          </div>
        </div>
      </div>

      {/* Body: 70/30 grid -- main content left, org wall right */}
      <div className="bg-warm-cream">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 py-12 md:py-16">
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-8 items-start">

            {/* LEFT COLUMN -- main content */}
            <div className="min-w-0">

      {/* Donation Attribution Banner removed — adds noise, not value */}

      {/* Financial Overview */}
      <div className="py-20">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">

          {/* Giving-first order (Stage 1): lead with the skimmable interpretation
              (health signal + peer standing + reserves-vs-peers), THEN the raw
              numbers. A donor should get "is this org financially sound?" in one
              glance before reading a metrics grid. PDCA: observe whether this
              lifts engagement via stats.daanaa.org before assuming it helps. */}

          {/* v5.0 Peer-based Financial Context — shown whenever the org has a
              peer-based assessment of its own. */}
          {apiOrg! && apiOrg!.v5_context && (
            <div className="mb-12">
              <V5Context org={apiOrg!} />
            </div>
          )}

          {/* Cause-cohort context — UNSCORED orgs only. Backend sets
              cohort_context only when the org has no v5_context of its own, so
              this fills the blank financial section with honest cause-area
              context (P3/P4) without ever competing with real scores. */}
          {apiOrg! && apiOrg!.cohort_context && (
            <div className="mb-12">
              <CohortContext org={apiOrg!} />
            </div>
          )}

          {/* Key financial metrics row -- the raw numbers, after the interpretation above */}
          {(apiOrg!.months_of_reserve !== null || apiOrg!.net_assets !== null || apiOrg!.total_expenses !== null) && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              {apiOrg!.months_of_reserve !== null && (
                <div
                  className="rounded-xl p-5 border"
                  style={apiOrg!.months_of_reserve < 0
                    ? { backgroundColor: 'rgba(139,26,26,0.05)', borderColor: 'rgba(139,26,26,0.20)' }
                    : apiOrg!.months_of_reserve < 3
                    ? { backgroundColor: '#FFFBF0', borderColor: '#FDE68A' }
                    : { backgroundColor: '#FFFFFF', borderColor: '#E5E0DB' }}
                >
                  <span className="block font-body text-[10px] tracking-[0.07em] text-cool-grey uppercase font-medium mb-1">Months of reserve</span>
                  <span
                    className="block font-body text-[26px] font-semibold tracking-[-0.02em]"
                    style={{ color: apiOrg!.months_of_reserve < 0 ? '#8B1A1A' : apiOrg!.months_of_reserve < 3 ? '#92400E' : '#0A1628' }}
                  >
                    {apiOrg!.months_of_reserve! > 999 ? '999+' : apiOrg!.months_of_reserve! < 0 ? `(${Math.round(Math.abs(apiOrg!.months_of_reserve!))})` : Math.round(apiOrg!.months_of_reserve!)}
                  </span>
                  <span className="font-body text-[11px] text-cool-grey">
                    {apiOrg!.months_of_reserve < 0
                      ? 'net assets negative'
                      : 'net assets ÷ monthly costs'}
                  </span>
                </div>
              )}
              {apiOrg!.net_assets !== null && (
                <div className="bg-white border border-light-grey rounded-xl p-5">
                  <span className="block font-body text-[10px] tracking-[0.07em] text-cool-grey uppercase font-medium mb-1">Net Assets</span>
                  <span className="block font-body text-[26px] font-semibold tracking-[-0.02em] text-deep-navy">
                    {formatCurrency(apiOrg!.net_assets!)}
                  </span>
                  <span className="font-body text-[11px] text-cool-grey">
                    Assets minus liabilities
                    {apiOrg!.latest_tax_year && <span className="ml-1.5 text-cool-grey">· FY {apiOrg!.latest_tax_year}</span>}
                  </span>
                </div>
              )}
              {apiOrg!.total_expenses !== null && (
                <div className="bg-white border border-light-grey rounded-xl p-5">
                  <span className="block font-body text-[10px] tracking-[0.07em] text-cool-grey uppercase font-medium mb-1">Annual Expenses</span>
                  <span className="block font-body text-[26px] font-semibold tracking-[-0.02em] text-deep-navy">
                    {formatCurrency(apiOrg!.total_expenses!)}
                  </span>
                  <span className="font-body text-[11px] text-cool-grey">
                    Total functional expenses
                    {apiOrg!.latest_tax_year && <span className="ml-1.5 text-cool-grey">· FY {apiOrg!.latest_tax_year}</span>}
                  </span>
                </div>
              )}
              {(apiOrg!.employee_count ?? 0) > 0 && (
                <div className="bg-white border border-light-grey rounded-xl p-5">
                  <span className="block font-body text-[10px] tracking-[0.07em] text-cool-grey uppercase font-medium mb-1">Employees</span>
                  <span className="block font-body text-[26px] font-semibold tracking-[-0.02em] text-deep-navy">
                    {formatNumber(apiOrg!.employee_count!)}
                  </span>
                  <span className="font-body text-[11px] text-cool-grey">W-3 form headcount (NCCS)</span>
                </div>
              )}
            </div>
          )}

          {/* Multi-dimensional peer context breakdown — shows where the org
              ranks by category, state, revenue size, and financial model. Simple,
              clear format for nonprofits to understand their position.
              Feature flag: peer_context_breakdown at 1% for testing. */}
          {apiOrg! && showPeerContextBreakdown && (
            <div className="mb-12">
              <PeerContextBreakdown org={apiOrg!} />
            </div>
          )}

          {/* Community Impact */}
          {apiOrg && (
            <div className="mb-12">
              <ImpactWidget orgEin={apiOrg.EIN} size="small" />
            </div>
          )}

          {/* Guild/Partner Membership */}
          {apiOrg && <GuildSection ein={apiOrg.EIN} />}

          {/* Enrichment Data: Contact & Programs */}
          {apiOrg && (
            <OrgEnrichmentCard
              contact={apiOrg.contact || null}
              programs={apiOrg.programs || null}
              loading={orgLoading}
            />
          )}

          {/* About this listing + the org's claimable spaces get the full width
              and are clearly defined. The wide revenue trend chart moves to its
              own full-width block below this (see "Revenue Trend" section). */}
          <div>
            <div className="flex flex-col gap-4">
              {/* Contextual handoff links */}
              <div className="flex flex-wrap gap-x-5 gap-y-2 px-1">
                {apiOrg!.NTEE1 && (
                  <Link
                    to={`/category/${apiOrg!.NTEE1}`}
                    className="font-body text-[12px] text-link-gold hover:text-deep-gold transition-colors"
                  >
                    Browse {getNteeLabel(apiOrg!.NTEE1 || '')} orgs →
                  </Link>
                )}
                <Link to="/methodology" className="font-body text-[12px] text-link-gold hover:text-deep-gold transition-colors">
                  How we score →
                </Link>
                <Link to="/research" className="font-body text-[12px] text-link-gold hover:text-deep-gold transition-colors">
                  Sector research →
                </Link>
              </div>

              {/* Manage / Claim CTA */}
              <div className="print-hide">
              {apiOrg!.claim_status === 'active' ? (
                /* Claimed — show "Edit this page" for the org rep */
                <div className="rounded-xl border border-soft-gold/30 bg-soft-gold/[0.04] px-5 py-4">
                  <p className="font-body text-[13px] font-medium text-deep-navy mb-1">Is this your organization?</p>
                  {!user ? (
                    <>
                      <p className="font-body text-[12px] text-cool-grey mb-3">Sign in to edit your page.</p>
                      <GoogleSignInButton compact />
                    </>
                  ) : (
                    <div className="flex items-center gap-3 flex-wrap">
                      <button
                        onClick={async () => {
                          setPortalLoading(true); setPortalError(null)
                          try {
                            const idToken = await getIdToken()
                            if (!idToken) throw new Error('no token')
                            const ein = (apiOrg!.EIN || '').replace(/\D/g, '')
                            const token = await getPortalToken(ein, idToken)
                            navigate(`/claim/edit?ein=${encodeURIComponent(ein)}&token=${encodeURIComponent(token)}`)
                          } catch {
                            setPortalError("Your account isn't linked to this page yet. Go to for-nonprofits to claim it.")
                          } finally {
                            setPortalLoading(false)
                          }
                        }}
                        disabled={portalLoading}
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-soft-gold text-deep-navy font-body text-[13px] font-semibold hover:bg-bright-gold disabled:opacity-40 transition-colors"
                      >
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                        </svg>
                        {portalLoading ? 'Opening…' : 'Edit this page'}
                      </button>
                      {portalError && <p className="font-body text-[12px] text-red-500">{portalError}</p>}
                    </div>
                  )}
                </div>
              ) : apiOrg!.claim_status !== 'letter_sent' && (
                /* Unclaimed — show claim CTA */
                <div className="rounded-xl border border-dashed border-soft-gold/30 bg-soft-gold/[0.03] px-6 py-5">
                  <div className="flex items-start justify-between gap-6 flex-wrap">
                    <div className="flex-1 min-w-0">
                      <p className="font-body text-[14px] font-semibold text-deep-navy">This page belongs to {apiOrg!.organization_name}.</p>
                      <p className="font-body text-[13px] text-cool-grey mt-1.5 leading-relaxed">
                        Right now it shows what's on public record. Claim it to tell your story in your own words — what you do, what you need, and how people can support your work. Free, always.
                      </p>
                    </div>
                    <Link
                      to={`/for-nonprofits?ein=${apiOrg!.EIN}`}
                      className="shrink-0 inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-deep-gold/50 text-deep-gold font-body text-[13px] font-medium hover:bg-soft-gold/10 transition-colors"
                    >
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                      </svg>
                      Claim your page
                    </Link>
                  </div>
                </div>
              )}
              </div>
            </div>
          </div>
        </div>
      </div>


      {/* Mission & Programs */}
      {/* Left column only renders when there is real content: no mission yet (show fallback text) or programs are listed.
          When the mission is already shown in the hero and there are no programs, collapse to a single column. */}
      <div className="border-t border-light-grey pt-12 md:pt-16 mt-0">
        <div>
          <div className={`grid grid-cols-1 gap-12 ${(!org.mission || org.programs.length > 0) ? 'lg:grid-cols-2' : ''}`}>
            {(!org.mission || org.programs.length > 0) && (
              <div>
                {/* Mission fallback — only shown when the hero has no mission to display */}
                {!org.mission && (
                  <p className="mt-3 font-body text-cool-grey text-[15px]">A mission statement for this organization isn't in public records yet. You can often find more about their work by searching their name or calling them directly.</p>
                )}
                {org.programs.length > 0 && (
                  <>
                    <span className="block mt-8 font-body text-[11px] font-medium tracking-[0.08em] text-deep-gold uppercase">PROGRAMS</span>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {org.programs.map((program) => (
                        <span key={program} className="px-3 py-1.5 rounded-full bg-navy-mid/10 text-deep-navy font-body text-[13px]">{program}</span>
                      ))}
                    </div>
                  </>
                )}
              </div>
            )}
            <div>
              {(() => {
                const leaders = ppLeadership.length > 0 ? ppLeadership : org.leadership
                return leaders.length > 0 ? (
                <>
                  <span className="font-body text-[11px] font-medium tracking-[0.08em] text-deep-gold uppercase">LEADERSHIP</span>
                  <div className="mt-4 space-y-4">
                    {leaders.map((person) => (
                      <div key={person.name} className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-full bg-soft-gold/20 flex items-center justify-center">
                          <span className="font-body text-[14px] font-semibold text-deep-gold">{person.initials}</span>
                        </div>
                        <div>
                          <p className="font-body text-[14px] font-medium text-deep-navy">{person.name}</p>
                          <p className="font-body text-[12px] text-cool-grey">{person.title}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                  {ppLeadership.length > 0 && (
                    <p className="font-body text-[11px] text-cool-grey mt-3">
                      Source: IRS Form 990{ppFilingYear ? `, ${ppFilingYear} filing` : ''} via ProPublica · public record
                    </p>
                  )}
                </>
                ) : (
                <div className="pt-2">
                  <span className="font-body text-[11px] font-medium tracking-[0.08em] text-deep-gold uppercase">DATA SOURCE</span>
                  <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 font-body text-[13px] text-cool-grey">
                    <div>
                      <p className="text-[10px] uppercase tracking-[0.07em] text-cool-grey mb-0.5">Type</p>
                      <p className="text-deep-navy font-medium">Registered US nonprofit</p>
                    </div>
                    <div>
                      <p className="text-[10px] uppercase tracking-[0.07em] text-cool-grey mb-0.5">EIN</p>
                      <p className="text-deep-navy font-medium">{formatEIN(org.ein)}</p>
                    </div>
                    {(() => {
                      const nteeCode = (org as any).nteecc || org.category || ''
                      if (!nteeCode) return null
                      const label = getNteeLabel(nteeCode)
                      return (
                        <div>
                          <p className="text-[10px] uppercase tracking-[0.07em] text-cool-grey mb-0.5">NTEE Category</p>
                          <p className="text-deep-navy font-medium">{label}</p>
                          {label.toLowerCase() !== nteeCode.toLowerCase() && (
                            <p className="text-[11px] text-cool-grey mt-0.5">Code {nteeCode}</p>
                          )}
                        </div>
                      )
                    })()}
                    {nonprofitSizeLabel(apiOrg!.total_revenue) && (
                      <div>
                        <p className="text-[10px] uppercase tracking-[0.07em] text-cool-grey mb-0.5">Size</p>
                        <p className="text-deep-navy font-medium">{nonprofitSizeLabel(apiOrg!.total_revenue)} nonprofit</p>
                      </div>
                    )}
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <DataFreshnessBadge
                      taxYear={(org as any).latestTaxYear}
                      dataSource={(org as any).dataSource}
                      updatedAt={(org as any).updatedAt}
                    />
                  </div>
                  <p className="mt-3">
                    <a href={propublicaOrgUrl(org.ein)}
                       target="_blank" rel="noopener noreferrer"
                       className="font-body text-[13px] text-link-gold hover:text-deep-gold transition-colors">
                      View on ProPublica Nonprofit Explorer →
                    </a>
                  </p>
                </div>
                )
              })()}
            </div>
          </div>
        </div>
      </div>

      {/* Accountability Strip */}
      <div className="border-t border-light-grey py-8">
        <div>
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6 sm:gap-12">
            <MistakeRegistry compact />
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-success-green/15 flex items-center justify-center shrink-0">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#4ADE80" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/>
                </svg>
              </div>
              <div>
                <p className="font-body text-[13px] font-semibold text-deep-navy">US Nonprofit · Active</p>
                <p className="font-body text-[12px] text-cool-grey">IRS-listed as eligible to receive tax-deductible contributions</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-soft-gold/15 flex items-center justify-center shrink-0">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
              </div>
              <div>
                <p className="font-body text-[13px] font-semibold text-deep-navy">EIN {formatEIN(org.ein)}</p>
                <p className="font-body text-[12px] text-cool-grey">Verified by government records</p>
              </div>
            </div>
          </div>
        </div>
      </div>

            </div>{/* end left column */}

            {/* RIGHT COLUMN -- organization wall */}
            <div className="lg:sticky lg:top-24 space-y-4">
              <OrgWallPanel orgName={org.name} ein={org.ein} />

              {/* Verify this listing -- external public records. Lives here (not a
                  full-width strip) so it fills the sidebar beside long left content. */}
              <div className="rounded-2xl border border-light-grey bg-white px-5 py-4">
                <span className="block font-body text-[11px] tracking-[0.06em] text-cool-grey uppercase font-medium mb-3">Public records</span>
                <div className="flex flex-col gap-2">
                  <a
                    href="https://apps.irs.gov/app/eos/"
                    target="_blank" rel="noopener noreferrer"
                    className="font-body text-[13px] text-link-gold hover:text-deep-gold transition-colors"
                  >IRS Tax Exempt Search →</a>
                  <a
                    href={propublicaOrgUrl(org.ein)}
                    target="_blank" rel="noopener noreferrer"
                    className="font-body text-[13px] text-link-gold hover:text-deep-gold transition-colors"
                  >ProPublica Nonprofit Explorer →</a>
                  <a
                    href="https://www.nasconet.org/resources/state-government/"
                    target="_blank" rel="noopener noreferrer"
                    className="font-body text-[13px] text-link-gold hover:text-deep-gold transition-colors"
                  >State Charity Registry →</a>
                </div>
              </div>
            </div>

          </div>{/* end grid */}
        </div>{/* end max-w container */}
      </div>{/* end bg-warm-cream */}

      {/* Service area */}
      {serviceArea?.area_type && serviceArea.area_type !== 'local' && (
        <div className="bg-warm-cream py-8 border-t border-light-grey">
          <div className="max-w-[900px] mx-auto px-6 lg:px-12">
            <p className="font-body text-[11px] font-medium tracking-[0.08em] text-deep-gold uppercase mb-2">
              Where they serve
            </p>
            <p className="font-body text-[15px] text-deep-navy">
              {serviceArea.area_type === 'nationwide' && 'Serves communities nationwide across the US'}
              {serviceArea.area_type === 'international' && (
                serviceArea.area_values.length > 0
                  ? `International work in ${serviceArea.area_values.length} ${serviceArea.area_values.length === 1 ? 'country' : 'countries'}`
                  : 'International reach'
              )}
              {serviceArea.area_type === 'statewide' && serviceArea.area_values.length > 0 && (
                `Statewide in ${serviceArea.area_values.slice(0, 5).join(', ')}${serviceArea.area_values.length > 5 ? ` +${serviceArea.area_values.length - 5} more` : ''}`
              )}
              {serviceArea.area_type === 'regional' && serviceArea.area_values.length > 0 && (
                serviceArea.area_values.slice(0, 4).join(' · ')
              )}
            </p>
            <p className="font-body text-[11px] text-cool-grey mt-1">Self-reported by the organization</p>
          </div>
        </div>
      )}

      {/* Volunteer opportunities */}
      {volunteerEvents.length > 0 && (
        <div className="bg-warm-cream py-12 border-t border-light-grey">
          <div className="max-w-[900px] mx-auto px-6 lg:px-12">
            <p className="font-body text-[11px] font-medium tracking-[0.08em] text-deep-gold uppercase mb-4">
              Volunteer opportunities
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {volunteerEvents.map(ev => {
                const parts = ev.event_date?.split('-') ?? []
                const dateStr = parts.length === 3
                  ? new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2])).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
                  : ev.event_date ?? 'Date TBD'
                const location = ev.is_virtual
                  ? 'Virtual'
                  : [ev.location_city, ev.location_state].filter(Boolean).join(', ') || null
                return (
                  <div key={ev.id} className="bg-white rounded-xl border border-light-cream p-5 flex flex-col gap-3">
                    <div>
                      <span className={`inline-block px-2 py-0.5 rounded-full font-body text-[10px] font-semibold tracking-[0.06em] uppercase mb-1 ${
                        ev.is_virtual ? 'bg-blue-50 text-blue-600' : 'bg-soft-gold/15 text-deep-gold'
                      }`}>
                        {ev.is_virtual ? 'Virtual' : 'In Person'}
                      </span>
                      <h3 className="font-display italic text-deep-navy text-[17px] leading-tight">{ev.title}</h3>
                      <p className="font-body text-[12px] text-cool-grey mt-0.5">
                        {dateStr}{location ? ` · ${location}` : ''}
                      </p>
                    </div>
                    {ev.description && (
                      <p className="font-body text-[13px] text-cool-grey leading-[1.6] line-clamp-2">{ev.description}</p>
                    )}
                    <div className="mt-auto">
                      {ev.signup_url ? (
                        <a
                          href={ev.signup_url} target="_blank" rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 font-body text-[13px] text-link-gold font-semibold hover:text-deep-gold transition-colors"
                        >
                          Sign up
                          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M7 17 17 7M17 7H8M17 7v9"/>
                          </svg>
                        </a>
                      ) : ev.contact_email ? (
                        <a
                          href={`mailto:${ev.contact_email}`}
                          className="font-body text-[13px] text-link-gold font-semibold hover:text-deep-gold transition-colors"
                        >
                          Contact to volunteer
                        </a>
                      ) : null}
                    </div>
                  </div>
                )
              })}
            </div>
            <p className="mt-6 font-body text-[12px] text-muted-cream">
              Sign-ups are handled by the organization directly. Daanaa does not collect volunteer information.
            </p>
          </div>
        </div>
      )}

      {/* Similar Organizations */}
      {similarOrgs.length > 0 ? (
        <div className="print-hide bg-deep-navy py-16 md:py-24">
          <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-pale-gold uppercase">
              MORE LIKE THIS
            </span>
            <h2 className="font-display italic text-warm-cream mt-3 leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(28px, 4vw, 48px)' }}>
              More groups working in this area
            </h2>
            <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {similarOrgs.map((o, idx) => {
                const raw = rawSimilarOrgs[idx]
                const simSummary = raw ? getTierSummary(getTierFromOrg(raw), raw) : undefined
                return (
                  <OrgCard
                    key={o.id}
                    org={o}
                    compact
                    apiOrg={raw}
                    trustSummary={simSummary}
                  />
                )
              })}
            </div>
            {apiOrg?.NTEE1 && (
              <div className="mt-10">
                <Link
                  to={`/category/${apiOrg.NTEE1}`}
                  className="font-body text-[14px] text-pale-gold hover:text-soft-gold transition-colors"
                >
                  Browse all {getNteeLabel(apiOrg.NTEE1)} organizations →
                </Link>
              </div>
            )}
          </div>
        </div>
      ) : apiOrg?.NTEE1 ? (
        /* Fallback when no precomputed similar orgs — keep users moving */
        <div className="bg-deep-navy py-12">
          <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-pale-gold uppercase">
              EXPLORE MORE
            </span>
            <p className="font-display italic text-warm-cream mt-3 text-[22px] leading-snug">
              Find more {getNteeLabel(apiOrg.NTEE1).toLowerCase()} organizations
            </p>
            <div className="mt-4 flex flex-wrap gap-4">
              <Link
                to={`/category/${apiOrg.NTEE1}`}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-white/10 border border-white/20 font-body text-[14px] text-warm-cream hover:bg-white/15 transition-colors"
              >
                Browse {getNteeLabel(apiOrg.NTEE1)} →
              </Link>
              <Link
                to="/directory"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-white/10 border border-white/20 font-body text-[14px] text-warm-cream hover:bg-white/15 transition-colors"
              >
                Full directory →
              </Link>
            </div>
          </div>
        </div>
      ) : null}

      {/* Multi-year Financial History (ProPublica 990 data) */}
      {financials.length > 0 && (
        <div className="bg-warm-cream border-t border-light-grey py-12 md:py-16">
          <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-deep-gold uppercase">Annual filings</span>
            <h2 className="font-display italic text-deep-navy mt-3 text-[28px] leading-[1.1] mb-6">
              Financial history
            </h2>
            <div className="overflow-x-auto max-w-[820px]">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-light-grey">
                    <th className="font-body text-[11px] tracking-[0.06em] text-cool-grey uppercase pb-2 pr-4">Year</th>
                    <th className="font-body text-[11px] tracking-[0.06em] text-cool-grey uppercase pb-2 pr-4">Revenue</th>
                    <th className="font-body text-[11px] tracking-[0.06em] text-cool-grey uppercase pb-2 pr-4">Expenses</th>
                    <th className="font-body text-[11px] tracking-[0.06em] text-cool-grey uppercase pb-2 pr-4">Net Assets</th>
                    <th className="font-body text-[11px] tracking-[0.06em] text-cool-grey uppercase pb-2 pr-4">Contributions</th>
                    <th className="font-body text-[11px] tracking-[0.06em] text-cool-grey uppercase pb-2">Report</th>
                  </tr>
                </thead>
                <tbody>
                  {[...financials].reverse().map((f) => (
                    <tr key={f.tax_prd_yr} className="border-b border-light-grey/50 hover:bg-white/50 transition-colors">
                      <td className="font-body text-[13px] font-medium text-deep-navy py-3 pr-4">{f.tax_prd_yr}</td>
                      <td className="font-body text-[13px] text-deep-navy py-3 pr-4">{f.totrevenue != null ? formatCurrency(f.totrevenue) : '--'}</td>
                      <td className="font-body text-[13px] text-cool-grey py-3 pr-4">{f.totfuncexpns != null ? formatCurrency(f.totfuncexpns) : '--'}</td>
                      <td className={`font-body text-[13px] py-3 pr-4 ${(f.totnetassetend ?? 0) < 0 ? 'text-amber-600' : 'text-cool-grey'}`}>
                        {f.totnetassetend != null ? formatCurrency(f.totnetassetend) : '--'}
                      </td>
                      <td className="font-body text-[13px] text-cool-grey py-3 pr-4">{f.totcntrbgfts != null ? formatCurrency(f.totcntrbgfts) : '--'}</td>
                      <td className="py-3">
                        {f.pdf_url ? (
                          <a
                            href={f.pdf_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 font-body text-[11px] text-link-gold hover:text-deep-gold transition-colors"
                          >
                            PDF
                            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                          </a>
                        ) : '--'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-4 font-body text-[12px] text-cool-grey">
              Source: ProPublica Nonprofit Explorer · Government annual financial reports
            </p>
          </div>
        </div>
      )}

      {promptState && (
        <DonationReturnPrompt
          state={promptState}
          onDismiss={dismissDonationPrompt}
          onLogged={dismissDonationPrompt}
        />
      )}
    </div>
  )
}
