import { useEffect, useRef, useState, useMemo, useCallback } from 'react'
import { usePageMeta } from '../hooks/usePageMeta'
import { useParams, Link, useNavigate } from 'react-router-dom'
import OrgCard from '../components/OrgCard'
import AnswerCard from '../components/AnswerCard'
import { IrsEligibilityContext } from '../components/IrsEligibilityContext'
import { taxDeductibleToStatus } from '../utils/taxDeductible'
import Breadcrumb from '../components/Breadcrumb'
import DonationReturnPrompt from '../components/DonationReturnPrompt'
import { useDonationReturnPrompt } from '../hooks/useDonationReturnPrompt'
import { getTierSummary, getTierFromOrg } from '../components/TrustBadge'
import BadgeChip from '../components/BadgeChip'
import MistakeRegistry from '../components/MistakeRegistry'
import DonorVoice, { canShowDonorVoice } from '../components/DonorVoice'

import { useApi } from '../hooks/useApi'
import { useFeatureFlag } from '../hooks/useFeatureFlag'
import { useWallet } from '../contexts/WalletContext'
import { getOrganization, getScoreHistory, getFinancials, getSimilarOrgs, getOrgVolunteerEvents, getServiceArea, getMyOrgs, getPortalToken } from '../data/api'
import FinancialContext from '../components/FinancialContext'
import { getNteeLabel } from '../data/ntee'
import type { ApiOrganization, ScoreSnapshot, ApiFinancialRecord, VolunteerEvent, ServiceArea } from '../data/api'
import { formatCurrency, formatNumber, formatEIN } from '../data/organizations'
import { getOrgBadges, getSectorName } from '../utils/badges'
import { getActionRowLinks } from '../utils/actionRow'
import { trackEvent, trackOrgBookmark } from '../utils/analytics'
import OrgWallPanel from '../components/OrgWallPanel'
import AiBadge from '../components/AiBadge'
import { useAuth } from '../contexts/AuthContext'
import { GoogleSignInButton } from '../components/GoogleSignInButton'
import PeerContextBreakdown, { buildPeerContextRows } from '../components/PeerContextBreakdown'
import DonationAttributionBanner from '../components/DonationAttributionBanner'
import ImpactWidget from '../components/ImpactWidget'
import OrgEnrichmentCard from '../components/OrgEnrichmentCard'
import GuildSection from '../components/GuildSection'
import { sentenceCase } from '../utils/sentenceCase'
import VolunteerInterest from '../components/VolunteerInterest'
import OrgInfoHierarchy from '../components/OrgInfoHierarchy'
import RecurringSetup from '../components/RecurringSetup'
import DataContextNote from '../components/DataContextNote'
import { normalizeExternalUrl } from '../utils/externalLink'
import AtAGlance from '../components/AtAGlance'
import ExpenseBreakdown from '../components/ExpenseBreakdown'
import FinancialTrends from '../components/FinancialTrends'
import BoardReviewSimulation from '../components/BoardReviewSimulation'
import PeerMethodologyExplainer from '../components/PeerMethodologyExplainer'
import WhatTheyDo from '../components/WhatTheyDo'
import WhyTrustThem from '../components/WhyTrustThem'
import HowToHelp from '../components/HowToHelp'
import { nonprofitSizeLabel } from '../utils/orgSize'
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
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-soft-gold/15 text-deep-gold font-body text-label font-medium">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
          {yearLabel}
        </span>
      )}
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-navy-mid/10 text-cool-grey font-body text-label">
        Source: {sourceLabel}
      </span>
      {updatedLabel && (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-navy-mid/10 text-cool-grey font-body text-label">
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

// Names the ACTUAL criteria Similar Organizations was matched by, tied to
// the org's own scoring_tier -- added 2026-08-16 after finding the section
// always said "More groups working in this area" regardless of whether
// geography was really part of the match (see DECISIONS.md 2026-08-16 and
// _find_similar_orgs() in droplet_api.py, which now selects by this same
// tier). Keep this in sync with FinancialContext.tsx's own tier language.
function similarOrganizationsHeading(scoringTier?: string | null): string {
  switch (scoringTier) {
    case '1_Full_Context':
      return 'Similar organizations, same field, size, and region'
    case '2_Regional_Context':
      return 'Similar organizations, same field and size, nationally'
    case '3_Broad_Category':
    case '3b_Broad_Category':
      return 'Other organizations in the same broader field'
    case '4_Archetype_Only':
    default:
      return 'Other organizations with a similar funding model'
  }
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
function IrsProgramNarrative({ narratives, prominent = false }: {
  narratives: NonNullable<ApiOrganization['irs_program_narrative']>
  prominent?: boolean
}) {
  const filingYears = [...new Set(narratives.map(({ year }) => year).filter((year): year is number => Number.isFinite(year)))].sort((a, b) => a - b)
  const filingCount = filingYears.length
  const coverage = filingCount > 1 ? `${filingYears[0]} to ${filingYears[filingYears.length - 1]}` : String(filingYears[0] ?? '')
  return (
    <section className={prominent ? 'mt-6 sm:mt-8 max-w-[680px]' : 'mt-6'} aria-labelledby="irs-program-narrative">
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <h2 id="irs-program-narrative" className={`font-display italic text-warm-cream ${prominent ? 'text-title-lg' : 'text-title-sm'}`}>In their own words</h2>
        <span className="inline-flex items-center gap-1.5 rounded-full border border-soft-gold/40 bg-soft-gold/10 px-2.5 py-1 font-body text-micro font-medium text-soft-gold">IRS filing text</span>
      </div>
      <p className="font-body text-caption text-muted-cream mb-3">Program descriptions from {filingCount} IRS {filingCount === 1 ? 'filing' : 'filings'}{coverage ? `, ${coverage}` : ''}</p>
      <div className={`border border-white/10 bg-white/6 rounded-xl ${prominent ? 'px-5 py-4' : 'px-4 py-3'} max-w-[680px]`}>
        <p className={`font-body text-warm-cream/90 leading-[1.7] whitespace-pre-wrap ${prominent ? 'text-body' : 'text-small'}`}>{narratives[0].text}</p>
        <p className="mt-3 font-body text-micro text-muted-cream tracking-[0.01em]">From the organization's {narratives[0].year} IRS filing</p>
        {narratives.length > 1 && (
          <details className="mt-4 border-t border-white/10 pt-3">
            <summary className="cursor-pointer font-body text-small font-medium text-soft-gold hover:text-bright-gold transition-colors">Read {narratives.length - 1} more {narratives.length === 2 ? 'program description' : 'program descriptions'}</summary>
            <div className="mt-4 space-y-5">
              {narratives.slice(1).map((narrative, index) => (
                <div key={`${narrative.year}-${index}`}>
                  <p className="font-body text-small text-warm-cream/85 leading-[1.65] whitespace-pre-wrap">{narrative.text}</p>
                  <p className="mt-2 font-body text-micro text-muted-cream">From the organization's {narrative.year} IRS filing</p>
                </div>
              ))}
            </div>
          </details>
        )}
      </div>
    </section>
  )
}

function ProfileCompletionPrompt({ href, label }: { href: string; label: string }) {
  return (
    <div className="mt-4 max-w-[600px] border border-white/10 rounded-xl px-4 py-3">
      <p className="font-body text-small font-medium text-warm-cream">Help complete this profile</p>
      <p className="mt-1 font-body text-caption text-muted-cream">Learn more about this organization's work using the link below.</p>
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-2 inline-flex items-center gap-1 font-body text-small text-soft-gold hover:text-bright-gold transition-colors"
      >
        {label}
        <span aria-hidden="true">→</span>
      </a>
    </div>
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
      className="inline-flex items-center gap-2 px-4 py-2 rounded-full font-body text-small font-medium transition-all duration-700"
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
  const { entries: walletEntries, isInFunding, isInVolunteering, addToFunding, addToVolunteering,
          removeFromFunding, removeFromVolunteering, setRecurringTemplate } = useWallet()
  const { trackDonateClick, promptState, dismiss: dismissDonationPrompt } = useDonationReturnPrompt()
  const [portalLoading, setPortalLoading] = useState(false)
  const [portalError, setPortalError]     = useState<string | null>(null)
  const [selectedBadge, setSelectedBadge] = useState<string | null>(null)
  // 990 Part VII — public compensation disclosure
  const [ppLeadership, setPpLeadership] = useState<{name:string;title:string;initials:string;compensation?:number}[]>([])
  const [ppFilingYear, setPpFilingYear] = useState<number|null>(null)
  const [enrichmentData, setEnrichmentData] = useState<any>(null)
  const [enrichmentLoading, setEnrichmentLoading] = useState(false)
  const [volunteeringInterestEventId, setVolunteeringInterestEventId] = useState<number | null>(null)
  const [showRecurringSetup, setShowRecurringSetup] = useState(false)
  const [showFinancialHistory, setShowFinancialHistory] = useState(false)
  const [lastDonationAmount, setLastDonationAmount] = useState<number | undefined>()


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

  // Phase 3 measurement: Track bookmarks with org size for small org CTR analysis (Gate A.1)
  const handleAddToFunding = useCallback((ein: string) => {
    addToFunding(ein)
    trackOrgBookmark(apiOrg?.service_scope?.revenue_band)
  }, [addToFunding, apiOrg?.service_scope?.revenue_band])

  const handleAddToVolunteering = useCallback((ein: string) => {
    addToVolunteering(ein)
    trackOrgBookmark(apiOrg?.service_scope?.revenue_band)
  }, [addToVolunteering, apiOrg?.service_scope?.revenue_band])

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
          <h2 className="font-display italic text-deep-navy text-headline-lg">Invalid EIN</h2>
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
          <h2 className="font-display italic text-deep-navy text-headline-lg">Organization not found</h2>
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
  const isSmallOrg = ['Micro', 'Small'].includes(nonprofitSizeLabel(apiOrg!.total_revenue) ?? '')
  const irsProgramNarratives = apiOrg!.irs_program_narrative?.filter(
    (narrative) => Boolean(narrative.text?.trim())
  ) ?? []
  const profileCompletionLink = actionLinks.donateUrl
    ? { href: actionLinks.donateUrl, label: 'Visit donation page' }
    : actionLinks.websiteUrl
      ? { href: actionLinks.websiteUrl, label: 'Visit website' }
      : null

  // FinancialContext already shows "Reserves" (the months_of_reserve figure)
  // for Tier 1/2 orgs, in its own peer-comparison framing. Showing the same
  // number again, plainly, in the Financial Snapshot grid below adds no new
  // information for those orgs (Bug Pattern 2 -- verified live on EIN
  // 391214392, scoring_tier 1_Full_Context, months_of_reserve 3.44: both
  // cards rendered identically). For Tier 3/4/unscored orgs, FinancialContext
  // never shows reserves, so the snapshot card remains the only place this
  // fact appears and stays as-is.
  const reserveShownByFinancialContext =
    apiOrg!.scoring_tier === '1_Full_Context' || apiOrg!.scoring_tier === '2_Regional_Context'
  const showReserveSnapshotCard = apiOrg!.months_of_reserve !== null && !reserveShownByFinancialContext

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
      <div className="bg-deep-navy pt-nav relative overflow-hidden">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 py-8 md:py-12 lg:py-16">
          <div className="flex items-center justify-between gap-2 mb-6">
            <div />
            <div className="flex items-center gap-2">
              {/* Green heart — funding intent */}
              <WalletHeartButton
                kind="funding"
                variant="icon"
                isActive={isInFunding(org.ein)}
                onToggle={() => isInFunding(org.ein) ? removeFromFunding(org.ein) : handleAddToFunding(apiOrg?.EIN ?? org.ein)}
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
                onToggle={() => isInVolunteering(org.ein) ? removeFromVolunteering(org.ein) : handleAddToVolunteering(apiOrg?.EIN ?? org.ein)}
                titleActive="Remove from volunteer list"
                titleInactive="I want to volunteer here"
                ariaActive="Remove from volunteer list"
                ariaInactive="Volunteer here"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[1fr_auto] gap-8 items-start">
            <div>
              {/* ORG NAME */}
              <div className="flex items-start gap-4 sm:gap-5">
                <div className="shrink-0 mt-1.5 w-14 h-14 sm:w-16 sm:h-16 rounded-2xl flex items-center justify-center border border-white/15 bg-white/[0.06]">
                  <span className="font-display text-title-lg sm:text-headline text-soft-gold leading-none tracking-tight">
                    {org.name.split(/\s+/).filter(Boolean).slice(0, 2).map((w: string) => w[0]).join('').toUpperCase()}
                  </span>
                </div>
                <h1 className="font-display italic text-warm-cream leading-[0.95] tracking-[-0.02em]" style={{ fontSize: 'clamp(34px, 5.5vw, 66px)' }}>
                  {org.name}
                </h1>
              </div>

              {isSmallOrg && (irsProgramNarratives.length > 0 ? (
                <IrsProgramNarrative narratives={irsProgramNarratives} prominent />
              ) : profileCompletionLink ? (
                <ProfileCompletionPrompt {...profileCompletionLink} />
              ) : null)}

              {/* Mission statement — all caps, no italics, sits under the name to
                  clarify what's a proper noun and what's descriptive. Simple. */}
              {org.mission && (
                <div className="mt-2 sm:mt-3 flex items-start gap-2">
                  <p className="font-body text-body text-muted-cream/80 leading-[1.6] max-w-[600px] uppercase tracking-wide">
                    {org.mission.replace(/^[""\s]+|[""\s]+$/g, '')}
                  </p>
                  {apiOrg && AI_MISSION_SOURCES.has(apiOrg.data_badges?.mission ?? apiOrg.mission_source ?? '') && (
                    <span className="shrink-0 mt-0.5">
                      <AiBadge />
                    </span>
                  )}
                </div>
              )}

              <div className="flex items-center gap-3 mt-2 sm:mt-4 flex-wrap">
                <div className="flex items-center gap-2">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#A89F94" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
                  </svg>
                  <span className="font-body text-lead text-muted-cream">
                    {apiOrg?.street_address && `${apiOrg.street_address}, `}{org.city}, {org.state}
                  </span>
                </div>
                {apiOrg?.metro && (
                  <span className="font-body text-label text-muted-cream/70">{apiOrg.metro}</span>
                )}
              </div>

              {/* Phase 1: Key Stats Summary — Decision-Grade Header Enhancement
                  Shows revenue size, peer context, financial health, governance at a glance
                  before donor decides to give. Expanded with Priority 1: Governance stats (board + staff).
                  All from existing fields — no new data collection. */}
              {apiOrg && (
                <div className="mt-6 sm:mt-8 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 pb-6 border-b border-white/10">
                  {/* Org Size — Annual Revenue */}
                  {apiOrg.total_revenue !== undefined && apiOrg.total_revenue !== null && (
                    <div className="space-y-1">
                      <p className="font-body text-xs uppercase text-muted-cream/60 tracking-wide">Annual Revenue</p>
                      <p className="font-display text-lead text-soft-gold font-semibold">{formatCurrency(apiOrg.total_revenue)}</p>
                    </div>
                  )}

                  {/* Financial Comparison — removes jargon "percentile" from hero */}
                  {apiOrg.ntee1_percentile !== undefined && apiOrg.ntee1_percentile !== null && (
                    <div className="space-y-1">
                      <p className="font-body text-xs uppercase text-muted-cream/60 tracking-wide">Financial Context</p>
                      <p className="font-display text-lead text-soft-gold font-semibold">Top {Math.round(100 - apiOrg.ntee1_percentile)}%</p>
                    </div>
                  )}

                  {/* Financial Profile — v6 scoring tier.
                      tier_label is the verified-correct human description
                      ("Donation-Funded Programs, Established, national");
                      the raw scoring_tier enum ("3_Broad_Category") is an
                      internal pipeline code and was leaking to donors
                      unexplained. See FinancialContext.tsx, which already
                      uses tier_label for the same reason. */}
                  {apiOrg.scoring_tier && (
                    <div className="space-y-1">
                      <p className="font-body text-xs uppercase text-muted-cream/60 tracking-wide">Financial Profile</p>
                      <p className="font-display text-lead text-soft-gold font-semibold">
                        {apiOrg.tier_label || apiOrg.scoring_tier.replace(/_/g, ' ')}
                      </p>
                    </div>
                  )}

                  {/* Priority 1: Board Size + Independence */}
                  {apiOrg.board_size !== undefined && apiOrg.board_size !== null && (
                    <div className="space-y-1">
                      <p className="font-body text-xs uppercase text-muted-cream/60 tracking-wide">Board</p>
                      <p className="font-display text-lead text-soft-gold font-semibold">
                        {apiOrg.board_size} members
                      </p>
                      {apiOrg.board_independent_count !== undefined && apiOrg.board_independent_count !== null && (
                        <p className="font-body text-label text-muted-cream/70">
                          {Math.round((apiOrg.board_independent_count / apiOrg.board_size) * 100)}% independent
                        </p>
                      )}
                    </div>
                  )}

                  {/* Priority 1: Staff Size */}
                  {apiOrg.employee_count !== undefined && apiOrg.employee_count !== null && (
                    <div className="space-y-1">
                      <p className="font-body text-xs uppercase text-muted-cream/60 tracking-wide">Staff</p>
                      <p className="font-display text-lead text-soft-gold font-semibold">
                        {apiOrg.employee_count} {apiOrg.employee_count === 1 ? 'person' : 'people'}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Phase 1: At-a-Glance Summary — Moved to header for decision-grade flow */}
              {apiOrg && <AtAGlance org={apiOrg} />}

              {/* Primary CTA: Give Now + Visit Website (side by side) */}
              <div className="mt-6 sm:mt-8 flex flex-col sm:flex-row gap-3 items-start sm:items-center">
                {apiOrg! && apiOrg!.tax_deductible !== false && (
                  <a
                    href="#ways-to-give"
                    className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-soft-gold text-deep-navy hover:bg-bright-gold transition-colors font-body text-small font-semibold"
                  >
                    Give now
                    <span aria-hidden="true">↓</span>
                  </a>
                )}
                {apiOrg?.website && (
                  <a
                    href={normalizeExternalUrl(apiOrg.website) || undefined}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-6 py-3 rounded-full border-2 border-soft-gold text-soft-gold hover:bg-soft-gold/10 transition-colors font-body text-small font-semibold"
                  >
                    Visit website
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M7 17 17 7M17 7H8M17 7v9"/></svg>
                  </a>
                )}
                {/* General volunteer signup link (org-level, 6.6% coverage) --
                    distinct from the event-specific "Express interest" flow
                    further down the page, which only appears when the org
                    has specific scheduled volunteer events. */}
                {apiOrg?.volunteer_url && (
                  <a
                    href={normalizeExternalUrl(apiOrg.volunteer_url) || undefined}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-6 py-3 rounded-full border-2 border-soft-gold text-soft-gold hover:bg-soft-gold/10 transition-colors font-body text-small font-semibold"
                  >
                    Volunteer
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M7 17 17 7M17 7H8M17 7v9"/></svg>
                  </a>
                )}
              </div>

              {/* Quick verification: legit/deductible/healthy + IRS status */}
              <div className="mt-6 sm:mt-8 space-y-3">
                {apiOrg! && <AnswerCard org={apiOrg!} />}
                {apiOrg! && <IrsEligibilityContext
                  status={taxDeductibleToStatus(apiOrg!.tax_deductible)}
                  checkedAt={apiOrg!.tax_deductible_checked_at}
                  organizationName={apiOrg!.organization_name}
                />}
                {apiOrg! && <DataContextNote org={apiOrg!} />}
              </div>

              {/* Badge row -- click any badge to see what earned it */}
              <div className="mt-4 flex flex-wrap gap-2">
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
                    <p className="font-body text-small text-warm-cream/85 leading-[1.65]">{b.detail}</p>
                    <p className="mt-2 font-body text-micro text-muted-cream tracking-[0.01em]">{b.source}</p>
                  </div>
                ) : null
              })()}

              {/* Financial stress indicator */}
              {apiOrg!.months_of_reserve !== null && apiOrg!.months_of_reserve < 3 && (
                <div className={`mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded font-body text-caption font-medium border ${
                  apiOrg!.months_of_reserve < 0
                    ? 'bg-destructive/10 text-destructive border-destructive/30'
                    : 'bg-alert-amber/10 text-alert-amber border-alert-amber/30'
                }`}>
                  <span className="w-1.5 h-1.5 rounded-full bg-current flex-shrink-0" />
                  {apiOrg!.months_of_reserve < 0
                    ? 'Negative net assets. This group owes more than it owns.'
                    : `Net assets cover only ${Math.round(apiOrg!.months_of_reserve)} months of costs`}
                </div>
              )}

              {/* Seeking board members */}
              {!!apiOrg!.seeking_board_members && (
                <div className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-full font-body text-caption font-medium bg-blue-50 text-blue-700 border border-blue-200">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                    <circle cx="9" cy="7" r="4"/>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                  </svg>
                  Looking for board members
                </div>
              )}

              {/* Cause tags -- always visible */}
              {Array.isArray(apiOrg!.cause_tags) && apiOrg!.cause_tags.length > 0 && (
                <div className="mt-4">
                  <p className="text-soft-gold text-sm font-medium mb-3">Categories</p>
                  <div className="flex flex-wrap items-center gap-2">
                    {(() => {
                      let tags = (apiOrg!.cause_tags as string[])
                      // Filter out "unknown" if we have NTEE data
                      if (apiOrg!.NTEE1) {
                        tags = tags.filter(t => t.toLowerCase() !== 'unknown')
                        // Add the NTEE sector name if it's not already in the list.
                        // Case-insensitive check: cause_tags can carry a lowercase
                        // variant of the same sector name, which the exact-match
                        // `includes()` this replaced didn't catch, showing
                        // "Education" and "education" as two separate tags.
                        const sectorName = getSectorName(apiOrg!.NTEE1)
                        if (sectorName && !tags.some(t => t.toLowerCase() === sectorName.toLowerCase())) {
                          tags = [sectorName, ...tags]
                        }
                      }
                      return tags.map((tag) => (
                        <span
                          key={tag}
                          className="inline-flex items-center px-2.5 py-1 rounded-full font-body text-label tracking-[0.02em] text-muted-cream/80 border border-white/10 bg-white/6"
                        >
                          {tag}
                        </span>
                      ))
                    })()}
                    {(apiOrg?.data_badges?.tags === 'ai_generated' || apiOrg?.mission_source === 'ai_ntee' || apiOrg?.mission_source === 'ai_generated') && (
                      <AiBadge title="These search tags were suggested by AI from public records. The organization can set its own once it claims this page." />
                    )}
                  </div>
                </div>
              )}

              {/* Large organizations retain the mission as their lead narrative. */}
              {!isSmallOrg && irsProgramNarratives.length > 0 && (
                <IrsProgramNarrative narratives={irsProgramNarratives} />
              )}

              {/* Donor Voice — social proof from people who've supported this org.
                  Gated on the same wallet-entry check DonorVoice uses internally
                  (canShowDonorVoice) so the wrapper never renders an empty mt-6
                  gap -- this section only shows content back to the device/
                  account that logged a gift, volunteered, or left a note here,
                  which is true for a small minority of page loads. */}
              {apiOrg && canShowDonorVoice(walletEntries.find(e => e.ein === apiOrg.EIN)) && (
                <div className="mt-6"><DonorVoice ein={apiOrg.EIN} orgName={apiOrg.organization_name} /></div>
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
                        <span className="block font-body text-label tracking-[0.02em] text-muted-cream">{(stat as any).label}</span>
                        <span className="block font-body text-body font-medium text-warm-cream">{(stat as any).value}</span>
                      </div>
                    </div>
                    {i < arr.length - 1 && <div className="hidden md:block w-[1px] h-8 bg-navy-mid" />}
                  </div>
                ))}
              </div>

              {/* Contact phone */}
              {apiOrg?.phone && (
                <div className="mt-8">
                  <a
                    href={`tel:${apiOrg.phone}`}
                    className="inline-flex items-center gap-2 font-body text-body-lg font-medium text-soft-gold hover:text-bright-gold transition-colors"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
                    {apiOrg.phone}
                  </a>
                  <p className="mt-1.5 font-body text-label text-cool-grey">
                    Contact them to give, volunteer, or learn more.
                  </p>
                </div>
              )}


              {/* Loop-closer: connect the give moment to a private record.
                  Appears under whichever CTA rendered. */}
            </div>

            {!(apiOrg!.source === 'bmf_stub' && apiOrg!.total_revenue == null) &&
             apiOrg!.tax_deductible !== false && (
            <div className="space-y-2">
              {/* Lamp tier retired from donor-facing profiles 2026-07-17
                  (founder-approved): its facts are covered by the plain
                  elements below, and the tier vocabulary read as a grade
                  (P4). Tiers live on in the nonprofit-facing claim flow. */}
              {/* IRS verification -- a real, defensible fact for every org */}
              <div className="space-y-1">
                <p className="font-body text-caption font-medium text-success-green">✓ Registered US Nonprofit</p>
                {apiOrg!.latest_tax_year && (
                  <p className="font-body text-label text-muted-cream">
                    Annual report filed · {apiOrg!.latest_tax_year}
                  </p>
                )}
                {/* Claimed / Unclaimed badge -- Yelp-style */}
                {apiOrg!.claim_status === 'active' ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded border border-soft-gold/50 text-soft-gold font-body text-label font-medium">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
                    Claimed
                  </span>
                ) : (
                  <div className="flex flex-col gap-1">
                    <Link
                      to={`/for-nonprofits?ein=${apiOrg!.EIN}`}
                      title="Is this your nonprofit? Claim your page free."
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded border border-muted-cream/40 text-muted-cream hover:border-soft-gold/60 hover:text-soft-gold font-body text-label transition-colors w-fit"
                    >
                      Unclaimed
                    </Link>
                    <p className="text-xs text-muted-cream">Unclaimed orgs are shown from public IRS records only. Claiming lets an org confirm or correct what's shown.</p>
                  </div>
                )}
              </div>
              <Link
                to="/methodology"
                className="font-body text-label text-muted-cream hover:text-soft-gold transition-colors"
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

      {/* Main Content: Financial Context + Ways to Give */}
      <div className="py-12 md:py-16 bg-warm-cream">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">

          {/* Mockup-aligned narrative flow (2026-08-17): the page now follows a coherent
              donor journey: What → Why → How → Details → Similar orgs. Each section is
              self-contained so donors can skim or dive deep as needed. */}

          {/* SECTION 1: What do they do? Mission + programs in donor-friendly language */}
          {apiOrg && <WhatTheyDo org={apiOrg} />}

          {/* SECTION 2: Why trust them? Unified narrative: financial + governance + verification */}
          {apiOrg && <WhyTrustThem org={apiOrg} />}

          {/* SECTION 3: How to help? Impact story + expense allocation */}
          {apiOrg && <HowToHelp org={apiOrg} />}

          {/* SECTION 4: Ways to Support — Direct giving methods (moved here for narrative flow) */}
          <div className="mb-4">
            <h2 className="font-body text-label font-medium tracking-[0.08em] text-deep-gold uppercase">Ways to Support</h2>
          </div>

          {/* Ways to Give — Mission-aligned giving methods */}
          {apiOrg && (
            <div className="mb-16">
              <OrgInfoHierarchy org={apiOrg} />
            </div>
          )}

          {/* SECTION 5: Deep Dive — Detailed financial context for interested donors */}
          <div className="mt-16 pt-12 border-t border-cool-grey/20 mb-16">
            <h2 className="font-body text-label font-medium tracking-[0.08em] text-deep-gold uppercase mb-8">Deep Dive: Financial Context</h2>

            {/* Peer financial context — the central financial insight. Each tier
                branch in FinancialContext renders its own styled card, so no
                extra wrapper here. */}
            {apiOrg && <FinancialContext org={apiOrg} />}

            {/* Board Review Simulation — P9 Explainability.
                Neutral assessment of how a board/funder would perceive the org
                based on financial data. Not a score or ranking, but an evidence-based
                narrative. Stewardship P3 (evidence-based), P4 (no size bias),
                P5 (no shame framing). */}
            {apiOrg && <BoardReviewSimulation org={apiOrg} />}

            {/* Peer Methodology Explainer — P9 Explainability.
                Shows how the peer group was constructed (NTEE + revenue band +
                region) so donors understand "top 30% of what?" */}
            {apiOrg && <PeerMethodologyExplainer org={apiOrg} />}
          </div>

          {/* Provenance Layer Separation removed 2026-08-15 (donor readability
              pass): every field it showed — EIN, location, revenue, NTEE
              category, financial tier, peer group size, website — already
              appears earlier on this page (hero stats, category pills,
              FinancialContext card), usually in a more readable format (e.g.
              this section showed the raw NTEE letter code "P" where the
              hero already shows human-readable category pills). Its "source
              transparency" framing is real but wasn't adding new facts, just
              re-grouping the same ones a third time — a repeated page reads
              as buggy/bloated to a donor, not more trustworthy. The
              transparency ethos itself is preserved in OrgInfoHierarchy's
              existing "We believe in transparency" copy below. Component
              (ProvenanceLayers.tsx) kept in the tree, unmounted here — easy
              to revert if this reads wrong once more orgs are checked. */}

          {/* Visibility Enhancement: Priority 2 — Expense Breakdown (2026-08-13)
              Shows program vs admin vs fundraising expenses visually.
              Addresses donor question: "Does my $ actually fund the mission?"
              Stewardship P3 (evidence-based) + P5 (no shame language) */}
          {/* No outer sum-gate here on purpose (removed 2026-08-16): the old
              gate only checked program+management+fundraising > 0, which
              stayed true even when those fields don't reconcile with
              total_expenses (see ExpenseBreakdown's own guard) -- leaving a
              bordered, empty-feeling gap on the page whenever the component
              hid itself internally. ExpenseBreakdown now owns its own
              wrapper/spacing and returns null (including the border/margin)
              when it has nothing trustworthy to show. */}
          {apiOrg && <ExpenseBreakdown org={apiOrg} />}

          {/* Visibility Enhancement: Priority 6 — Financial Trends (2026-08-13)
              Shows 5-year revenue history + growth trajectory.
              CauseIQ feature: trend analysis signals stability/growth/decline.
              Addresses donor question: "Is this org stable and growing?"
              Stewardship P3 (evidence-based) + P4 (context for small orgs) */}
          {apiOrg && apiOrg.total_revenue && (
            <div className="mt-16 pt-12 mb-16 border-t border-cool-grey/20">
              <FinancialTrends org={apiOrg} />
            </div>
          )}

          {/* Key financial metrics — supporting data after peer comparison */}
          {(showReserveSnapshotCard || apiOrg!.net_assets !== null || apiOrg!.total_expenses !== null) && (
            <div className="mb-16">
              <h3 className="font-display italic text-deep-navy text-title-sm mb-6">Financial snapshot</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {showReserveSnapshotCard && (
                <div
                  className="rounded-xl p-5 border"
                  style={apiOrg!.months_of_reserve! < 0
                    ? { backgroundColor: 'rgba(139,26,26,0.05)', borderColor: 'rgba(139,26,26,0.20)' }
                    : apiOrg!.months_of_reserve! < 3
                    ? { backgroundColor: '#FFFBF0', borderColor: '#FDE68A' }
                    : { backgroundColor: '#FFFFFF', borderColor: '#E5E0DB' }}
                >
                  <span className="block font-body text-micro tracking-[0.07em] text-cool-grey uppercase font-medium mb-1">Months of reserve</span>
                  <span
                    className="block font-body text-headline font-semibold tracking-[-0.02em]"
                    style={{ color: apiOrg!.months_of_reserve! < 0 ? '#8B1A1A' : apiOrg!.months_of_reserve! < 3 ? '#92400E' : '#0A1628' }}
                  >
                    {apiOrg!.months_of_reserve! > 999 ? '999+' : apiOrg!.months_of_reserve! < 0 ? `(${Math.round(Math.abs(apiOrg!.months_of_reserve!))})` : Math.round(apiOrg!.months_of_reserve!)}
                  </span>
                  <span className="font-body text-label text-cool-grey">
                    {apiOrg!.months_of_reserve! < 0
                      ? 'net assets negative'
                      : 'net assets ÷ monthly costs'}
                  </span>
                </div>
              )}
              {apiOrg!.net_assets !== null && (
                <div className="bg-white border border-light-grey rounded-xl p-5">
                  <span className="block font-body text-micro tracking-[0.07em] text-cool-grey uppercase font-medium mb-1">Net Assets</span>
                  <span className="block font-body text-headline font-semibold tracking-[-0.02em] text-deep-navy">
                    {formatCurrency(apiOrg!.net_assets!)}
                  </span>
                  <span className="font-body text-label text-cool-grey">
                    Assets minus liabilities
                    {apiOrg!.latest_tax_year && <span className="ml-1.5 text-cool-grey">· FY {apiOrg!.latest_tax_year}</span>}
                  </span>
                </div>
              )}
              {apiOrg!.total_expenses !== null && (
                <div className="bg-white border border-light-grey rounded-xl p-5">
                  <span className="block font-body text-micro tracking-[0.07em] text-cool-grey uppercase font-medium mb-1">Annual Expenses</span>
                  <span className="block font-body text-headline font-semibold tracking-[-0.02em] text-deep-navy">
                    {formatCurrency(apiOrg!.total_expenses!)}
                  </span>
                  <span className="font-body text-label text-cool-grey">
                    Total functional expenses
                    {apiOrg!.latest_tax_year && <span className="ml-1.5 text-cool-grey">· FY {apiOrg!.latest_tax_year}</span>}
                  </span>
                </div>
              )}
              {(apiOrg!.employee_count ?? 0) > 0 && (
                <div className="bg-white border border-light-grey rounded-xl p-5">
                  <span className="block font-body text-micro tracking-[0.07em] text-cool-grey uppercase font-medium mb-1">Employees</span>
                  <span className="block font-body text-headline font-semibold tracking-[-0.02em] text-deep-navy">
                    {formatNumber(apiOrg!.employee_count!)}
                  </span>
                  <span className="font-body text-label text-cool-grey">W-3 form headcount (NCCS)</span>
                </div>
              )}
            </div>

            {/* Financial history — compact by default (moved up from below Similar
                Orgs, and folded into the snapshot instead of duplicating it, per the
                2026-08-08 design review). The most recent year's figures already
                appear in the cards above; this is only the multi-year table,
                collapsed unless there's more than one year to show. */}
            {financials.length > 0 && (
              <div className="mt-6 pt-6 border-t border-light-grey">
                {financials.length > 1 ? (
                  <button
                    onClick={() => setShowFinancialHistory(v => !v)}
                    className="inline-flex items-center gap-1.5 font-body text-small text-link-gold hover:text-deep-gold transition-colors"
                    aria-expanded={showFinancialHistory}
                  >
                    {showFinancialHistory ? 'Hide' : 'Show'} {financials.length} years of Form 990 filing history
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className={`transition-transform ${showFinancialHistory ? 'rotate-180' : ''}`}>
                      <polyline points="6 9 12 15 18 9"/>
                    </svg>
                  </button>
                ) : (
                  <p className="font-body text-small text-cool-grey">One year of Form 990 filing history on record.</p>
                )}

                {(showFinancialHistory || financials.length === 1) && (
                  <div className="mt-4 overflow-x-auto max-w-[820px]">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-light-grey">
                          <th className="font-body text-label tracking-[0.06em] text-cool-grey uppercase pb-2 pr-4">Year</th>
                          <th className="font-body text-label tracking-[0.06em] text-cool-grey uppercase pb-2 pr-4">Revenue</th>
                          <th className="font-body text-label tracking-[0.06em] text-cool-grey uppercase pb-2 pr-4">Expenses</th>
                          <th className="font-body text-label tracking-[0.06em] text-cool-grey uppercase pb-2 pr-4">Net Assets</th>
                          <th className="font-body text-label tracking-[0.06em] text-cool-grey uppercase pb-2 pr-4">Contributions</th>
                          <th className="font-body text-label tracking-[0.06em] text-cool-grey uppercase pb-2">Report</th>
                        </tr>
                      </thead>
                      <tbody>
                        {[...financials].reverse().map((f) => (
                          <tr key={f.tax_prd_yr} className="border-b border-light-grey/50 hover:bg-white/50 transition-colors">
                            <td className="font-body text-small font-medium text-deep-navy py-3 pr-4">{f.tax_prd_yr}</td>
                            <td className="font-body text-small text-deep-navy py-3 pr-4">{f.totrevenue != null ? formatCurrency(f.totrevenue) : '--'}</td>
                            <td className="font-body text-small text-cool-grey py-3 pr-4">{f.totfuncexpns != null ? formatCurrency(f.totfuncexpns) : '--'}</td>
                            <td className={`font-body text-small py-3 pr-4 ${(f.totnetassetend ?? 0) < 0 ? 'text-amber-600' : 'text-cool-grey'}`}>
                              {f.totnetassetend != null ? formatCurrency(f.totnetassetend) : '--'}
                            </td>
                            <td className="font-body text-small text-cool-grey py-3 pr-4">{f.totcntrbgfts != null ? formatCurrency(f.totcntrbgfts) : '--'}</td>
                            <td className="py-3">
                              {f.pdf_url ? (
                                <a
                                  href={f.pdf_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1 font-body text-label text-link-gold hover:text-deep-gold transition-colors"
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
                    <p className="mt-4 font-body text-caption text-cool-grey">
                      Source: ProPublica Nonprofit Explorer · Government annual financial reports
                    </p>
                  </div>
                )}
              </div>
            )}
            </div>
          )}

          {/* Multi-dimensional peer context breakdown — shows where the org
              ranks by category, state, revenue size, and financial model. Simple,
              clear format for nonprofits to understand their position.
              Feature flag: peer_context_breakdown at 1% for testing. Gated on
              buildPeerContextRows(apiOrg!).length (the same rows the component
              itself computes) so orgs with no rows to show don't render an
              empty mb-12 wrapper. */}
          {apiOrg! && showPeerContextBreakdown && buildPeerContextRows(apiOrg!).length > 0 && (
            <PeerContextBreakdown org={apiOrg!} />
          )}

          {/* Community Impact. ImpactWidget owns its own mb-12 margin (its
              donation/volunteer data loads async, so this page can't know
              ahead of time whether it will render) -- a wrapper div here
              would leave an empty gap on every org with no logged activity. */}
          {apiOrg && <ImpactWidget orgEin={apiOrg.EIN} size="small" />}

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

          {/* Manage / Claim CTA */}
          <div className="print-hide">
            {apiOrg!.claim_status === 'active' ? (
                /* Claimed — show "Edit this page" for the org rep */
                <div className="rounded-xl border border-soft-gold/30 bg-soft-gold/[0.04] px-5 py-4">
                  <p className="font-body text-small font-medium text-deep-navy mb-1">Is this your organization?</p>
                  {!user ? (
                    <>
                      <p className="font-body text-caption text-cool-grey mb-3">Sign in to edit your page.</p>
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
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-soft-gold text-deep-navy font-body text-small font-semibold hover:bg-bright-gold disabled:opacity-40 transition-colors"
                      >
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                        </svg>
                        {portalLoading ? 'Opening…' : 'Edit this page'}
                      </button>
                      {portalError && <p className="font-body text-caption text-red-500">{portalError}</p>}
                    </div>
                  )}
                </div>
              ) : null}
          </div>
        </div>
      </div>

      {/* Leadership (if available) */}
      {ppLeadership.length > 0 && (
        <div className="border-t border-light-grey py-12 md:py-16 mt-0">
          <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
            <span className="font-body text-label font-medium tracking-[0.08em] text-deep-gold uppercase">Leadership</span>
            <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
              {ppLeadership.map((person) => (
                <div key={person.name}>
                  <p className="font-body text-body font-medium text-deep-navy">{person.name}</p>
                  <p className="font-body text-caption text-cool-grey mt-1">{person.title}</p>
                  {person.compensation && (
                    <p className="font-body text-caption text-cool-grey mt-2">{formatCurrency(person.compensation)}</p>
                  )}
                </div>
              ))}
            </div>
            <p className="font-body text-label text-cool-grey mt-8">
              Source: IRS Form 990{ppFilingYear ? `, ${ppFilingYear} filing` : ''} via ProPublica · public record
            </p>
          </div>
        </div>
      )}

      {/* Accountability Strip */}
      <div className="border-t border-light-grey py-8">
        <div className="space-y-8">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6 sm:gap-12">
            <MistakeRegistry compact />
            <div className="space-y-1">
              <p className="font-body text-small font-semibold text-deep-navy">✓ US Nonprofit · Active</p>
              <p className="font-body text-caption text-cool-grey">IRS nonprofit registration verified</p>
            </div>
            <div className="space-y-1">
              <p className="font-body text-small font-semibold text-deep-navy">✓ EIN {formatEIN(org.ein)}</p>
              <p className="font-body text-caption text-cool-grey">Verified by government records</p>
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
                <span className="block font-body text-label tracking-[0.06em] text-cool-grey uppercase font-medium mb-3">Public records</span>
                <div className="flex flex-col gap-2">
                  <a
                    href="https://apps.irs.gov/app/eos/"
                    target="_blank" rel="noopener noreferrer"
                    className="font-body text-small text-link-gold hover:text-deep-gold transition-colors"
                  >IRS Tax Exempt Search →</a>
                  <a
                    href={propublicaOrgUrl(org.ein)}
                    target="_blank" rel="noopener noreferrer"
                    className="font-body text-small text-link-gold hover:text-deep-gold transition-colors"
                  >ProPublica Nonprofit Explorer →</a>
                  <a
                    href="https://www.nasconet.org/resources/state-government/"
                    target="_blank" rel="noopener noreferrer"
                    className="font-body text-small text-link-gold hover:text-deep-gold transition-colors"
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
            <p className="font-body text-label font-medium tracking-[0.08em] text-deep-gold uppercase mb-2">
              Where they serve
            </p>
            <p className="font-body text-body-lg text-deep-navy">
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
            <p className="font-body text-label text-cool-grey mt-1">Self-reported by the organization</p>
          </div>
        </div>
      )}

      {/* Volunteer opportunities */}
      {volunteerEvents.length > 0 && (
        <div className="bg-warm-cream py-12 border-t border-light-grey">
          <div className="max-w-[900px] mx-auto px-6 lg:px-12">
            <p className="font-body text-label font-medium tracking-[0.08em] text-deep-gold uppercase mb-4">
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
                      <span className={`inline-block px-2 py-0.5 rounded-full font-body text-micro font-semibold tracking-[0.06em] uppercase mb-1 ${
                        ev.is_virtual ? 'bg-blue-50 text-blue-600' : 'bg-soft-gold/15 text-deep-gold'
                      }`}>
                        {ev.is_virtual ? 'Virtual' : 'In Person'}
                      </span>
                      <h3 className="font-display italic text-deep-navy text-title-sm leading-tight">{ev.title}</h3>
                      <p className="font-body text-caption text-cool-grey mt-0.5">
                        {dateStr}{location ? ` · ${location}` : ''}
                      </p>
                    </div>
                    {ev.description && (
                      <p className="font-body text-small text-cool-grey leading-[1.6] line-clamp-2">{ev.description}</p>
                    )}
                    <div className="mt-auto flex flex-col gap-2">
                      {ev.signup_url && (
                        <a
                          href={ev.signup_url} target="_blank" rel="noopener noreferrer"
                          className="inline-flex items-center justify-center gap-1.5 px-3 py-2 bg-soft-gold text-deep-navy rounded-lg font-body text-small font-semibold hover:bg-bright-gold transition-colors"
                        >
                          Sign up
                          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M7 17 17 7M17 7H8M17 7v9"/>
                          </svg>
                        </a>
                      )}
                      <button
                        onClick={() => setVolunteeringInterestEventId(ev.id)}
                        className="inline-flex items-center justify-center gap-1.5 px-3 py-2 border border-soft-gold text-soft-gold rounded-lg font-body text-small font-semibold hover:bg-soft-gold/10 transition-colors"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                        </svg>
                        Express interest
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
            <p className="mt-6 font-body text-caption text-muted-cream">
              Sign-ups are handled by the organization directly. Daanaa does not collect volunteer information.
            </p>
          </div>
        </div>
      )}

      {/* Volunteer Interest Modal — Event-Specific */}
      {volunteeringInterestEventId && volunteerEvents.length > 0 && (() => {
        const selectedEvent = volunteerEvents.find(e => e.id === volunteeringInterestEventId)
        return selectedEvent ? (
          <VolunteerInterest
            orgName={apiOrg?.organization_name || org.name}
            website={apiOrg?.website}
            contactEmail={selectedEvent.contact_email}
            onClose={() => setVolunteeringInterestEventId(null)}
          />
        ) : null
      })()}

      {/* Similar Organizations */}
      {similarOrgs.length > 0 ? (
        <div className="print-hide bg-deep-navy py-16 md:py-24">
          <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
            <span className="font-body text-label font-medium tracking-[0.08em] text-pale-gold uppercase">
              MORE LIKE THIS
            </span>
            <h2 className="font-display italic text-warm-cream mt-3 leading-[1.05] tracking-[-0.01em]">
              {similarOrganizationsHeading(apiOrg?.scoring_tier)}
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
                  className="font-body text-body text-pale-gold hover:text-soft-gold transition-colors"
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
            <span className="font-body text-label font-medium tracking-[0.08em] text-pale-gold uppercase">
              EXPLORE MORE
            </span>
            <p className="font-display italic text-warm-cream mt-3 text-title-lg leading-snug">
              Find more {getNteeLabel(apiOrg.NTEE1).toLowerCase()} organizations
            </p>
            <div className="mt-4 flex flex-wrap gap-4">
              <Link
                to={`/category/${apiOrg.NTEE1}`}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-white/10 border border-white/20 font-body text-body text-warm-cream hover:bg-white/15 transition-colors"
              >
                Browse {getNteeLabel(apiOrg.NTEE1)} →
              </Link>
              <Link
                to="/directory"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-white/10 border border-white/20 font-body text-body text-warm-cream hover:bg-white/15 transition-colors"
              >
                Full directory →
              </Link>
            </div>
          </div>
        </div>
      ) : null}

      {promptState && (
        <DonationReturnPrompt
          state={promptState}
          onDismiss={dismissDonationPrompt}
          onLogged={(amount?: number) => {
            if (amount) {
              setLastDonationAmount(amount)
              setShowRecurringSetup(true)
            } else {
              dismissDonationPrompt()
            }
          }}
        />
      )}

      {/* Recurring Setup Modal */}
      {showRecurringSetup && apiOrg && (
        <RecurringSetup
          orgName={apiOrg.organization_name}
          lastDonationAmount={lastDonationAmount}
          onSetup={(template) => {
            setRecurringTemplate(apiOrg.EIN, template)
            setShowRecurringSetup(false)
            dismissDonationPrompt()
          }}
          onClose={() => {
            setShowRecurringSetup(false)
            dismissDonationPrompt()
          }}
        />
      )}
    </div>
  )
}
