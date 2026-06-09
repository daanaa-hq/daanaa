import { useEffect, useRef, useState, useMemo } from 'react'
import { usePageMeta } from '../hooks/usePageMeta'
import { useParams, Link } from 'react-router-dom'
import OrgCard from '../components/OrgCard'
import { getTierSummary, getTierFromOrg, getV4FinancialHealth, TIER_COLORS } from '../components/TrustBadge'
import BadgeChip from '../components/BadgeChip'
import ScoreBreakdown from '../components/ScoreBreakdown'
import LampMark from '../components/LampMark'
import TierBreakdown from '../components/TierBreakdown'
import MistakeRegistry from '../components/MistakeRegistry'
import VolunteerInterest from '../components/VolunteerInterest'
import { useApi } from '../hooks/useApi'
import { useSavedOrgs } from '../hooks/useSavedOrgs'
import { useGivingList } from '../hooks/useGivingList'
import { getOrganization, getScoreHistory, getFinancials, getSimilarOrgs } from '../data/api'
import type { ApiOrganization, ScoreSnapshot, ApiFinancialRecord } from '../data/api'
import { formatCurrency, formatNumber, formatEIN } from '../data/organizations'
import { getOrgBadges } from '../utils/badges'
import OrgWallPanel from '../components/OrgWallPanel'
import AiBadge from '../components/AiBadge'
import FinancialContext from '../components/FinancialContext'

// ---- Revenue Bar Chart ----
function RevenueChart({ data }: { data: { year: number; amount: number }[] }) {
  const [hoveredBar, setHoveredBar] = useState<number | null>(null)
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 })
  const prefersReducedMotion = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const [revealed, setRevealed] = useState(prefersReducedMotion)
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (prefersReducedMotion) return
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setRevealed(true)
          observer.disconnect()
        }
      },
      { threshold: 0.3 }
    )
    if (svgRef.current) observer.observe(svgRef.current)
    return () => observer.disconnect()
  }, [])

  const maxAmount = Math.max(...data.map(d => d.amount))
  const chartW = 680
  const chartH = 350
  const margin = { top: 40, right: 40, bottom: 60, left: 80 }
  const innerW = chartW - margin.left - margin.right
  const innerH = chartH - margin.top - margin.bottom

  const barWidth = 80
  const gap = (innerW - barWidth * data.length) / (data.length + 1)

  const yTicks = [0, maxAmount * 0.25, maxAmount * 0.5, maxAmount * 0.75, maxAmount]

  const handleMouseMove = (e: React.MouseEvent, index: number) => {
    const rect = svgRef.current?.getBoundingClientRect()
    if (rect) {
      setTooltipPos({ x: e.clientX - rect.left, y: e.clientY - rect.top })
    }
    setHoveredBar(index)
  }

  return (
    <div className="bg-white border border-light-grey rounded-xl p-6 relative">
      <h4 className="font-display text-deep-navy text-[20px] mb-4">Revenue Trend (5 Years)</h4>
      <svg
        ref={svgRef}
        viewBox={`0 0 ${chartW} ${chartH}`}
        className="w-full"
        style={{ aspectRatio: '16/9' }}
      >
        {yTicks.map((tick, i) => {
          const y = margin.top + innerH - (tick / maxAmount) * innerH
          return (
            <g key={i}>
              <line x1={margin.left} y1={y} x2={chartW - margin.right} y2={y} stroke="#E5E0DB" strokeWidth={1} />
              <text x={margin.left - 12} y={y + 4} textAnchor="end" fill="#6B7280" fontSize="12" fontFamily="Inter, sans-serif">
                {formatCurrency(tick)}
              </text>
            </g>
          )
        })}

        <line x1={margin.left} y1={margin.top + innerH} x2={chartW - margin.right} y2={margin.top + innerH} stroke="#E5E0DB" strokeWidth={1} />

        {/* Vertical grid lines between bars */}
        {data.slice(0, -1).map((_, i) => {
          const x = margin.left + gap + i * (barWidth + gap) + barWidth + gap / 2
          return (
            <line key={`vgrid-${i}`} x1={x} y1={margin.top} x2={x} y2={margin.top + innerH} stroke="#E5E0DB" strokeWidth={1} strokeDasharray="3 3" />
          )
        })}

        {data.map((d, i) => {
          const barH = (d.amount / maxAmount) * innerH
          const x = margin.left + gap + i * (barWidth + gap)
          const y = margin.top + innerH - barH
          const targetY = y
          const startY = margin.top + innerH

          return (
            <g key={d.year} onMouseMove={(e) => handleMouseMove(e, i)} onMouseLeave={() => setHoveredBar(null)} style={{ cursor: 'pointer' }}>
              <rect
                x={x} y={revealed ? targetY : startY}
                width={barWidth} height={revealed ? barH : 0}
                rx={8}
                fill={hoveredBar === i ? '#D4B87A' : '#C9A96E'}
                style={{ transition: prefersReducedMotion ? 'none' : `all 1s ease-out ${i * 0.1}s` }}
              />
              <text x={x + barWidth / 2} y={margin.top + innerH + 24} textAnchor="middle" fill="#6B7280" fontSize="12" fontFamily="Inter, sans-serif">
                {d.year}
              </text>
            </g>
          )
        })}
      </svg>

      {hoveredBar !== null && (
        <div className="absolute pointer-events-none bg-white rounded-lg shadow-lg px-3 py-2 z-10" style={{ left: tooltipPos.x, top: tooltipPos.y - 50, transform: 'translateX(-50%)' }}>
          <p className="font-body text-[13px] font-medium text-deep-navy whitespace-nowrap">
            {data[hoveredBar].year}: {formatCurrency(data[hoveredBar].amount)}
          </p>
        </div>
      )}
    </div>
  )
}

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
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-soft-gold/10 text-soft-gold font-body text-[11px] font-medium">
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
    return `They carry about ${m} months of savings -- ${feel}.`
  }
  return `Ranked within a peer group of ${org.peer_total ?? '--'} similar nonprofits.`
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
    mission: apiOrg.mission || '',
    website: apiOrg.website || '',
    programs: [] as string[],
    leadership: [] as { name: string; title: string; initials: string }[],
    boardSize: 0,
    revenueTrend: [] as { year: number; amount: number }[],
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

// ---- Main Page ----
export default function OrganizationDetail() {
  const { id } = useParams<{ id: string }>()
  const { isSaved, toggle: toggleSave } = useSavedOrgs()
  const [showBreakdown, setShowBreakdown] = useState(false)
  const [showTierBreakdown, setShowTierBreakdown] = useState(false)
  const [selectedBadge, setSelectedBadge] = useState<string | null>(null)
  const [showScoreExplainer, setShowScoreExplainer] = useState(false)
  const [showVolunteer, setShowVolunteer] = useState(false)
  const [showResources, setShowResources] = useState(false)
  const { isInList, items: givingItems, addItem, removeItem, markPending } = useGivingList()

  const { data: apiOrg, loading: orgLoading, error: orgError } = useApi(
    () => getOrganization(id || ''),
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
  const similarApiOrgs: ApiOrganization[] = (similarData?.results ?? []) as ApiOrganization[]
  const revenueTrend = financials
    .filter(f => f.totrevenue !== null && f.totrevenue > 0)
    .map(f => ({ year: f.tax_prd_yr, amount: f.totrevenue! }))

  useEffect(() => {
    window.scrollTo(0, 0)
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

  const inList = isInList(org?.ein || '')
  const hasGiven = givingItems.some(i => i.ein === (org?.ein || '') && i.status === 'given')

  const metaTitle = apiOrg?.organization_name ?? ''
  const metaDesc = apiOrg
    ? `${apiOrg.organization_name} is a registered US nonprofit${apiOrg.CITY ? ` in ${apiOrg.CITY}, ${apiOrg.STATE}` : ''}. Tier: ${apiOrg.merit_tier ?? 'Flame'}. Financial scale: ${apiOrg.peer_percentile != null ? `${Math.round(apiOrg.peer_percentile)}/100` : 'pending'}.`
    : ''
  usePageMeta(metaTitle, metaDesc)

  if (orgLoading) {
    return (
      <div className="min-h-[100dvh] flex items-center justify-center bg-deep-navy">
        <div className="w-8 h-8 border-2 border-soft-gold border-t-transparent rounded-full animate-spin" />
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

  const lampTier     = getTierFromOrg(apiOrg!)
  const trustSummary = getTierSummary(lampTier, apiOrg!)
  const v4Health     = getV4FinancialHealth(apiOrg!)
  const badges = getOrgBadges(apiOrg!)

  const givePayload = {
    ein: org.ein,
    orgName: org.name,
    city: org.city || undefined,
    state: org.state || undefined,
    ntee1: org.category || undefined,
    amount: 0,
    trustTier: lampTier,
    trustSummary,
    donateUrl: (apiOrg?.donate_url_status !== 'dead' && apiOrg?.donate_url) ? apiOrg.donate_url : undefined,
  }

  const handleGiveToggle = () => {
    if (inList) {
      removeItem(org.ein)
    } else {
      addItem(givePayload)
    }
  }

  // Donor clicked an external give link -- track it and ask "did you give?"
  // when they return (LinkedIn-jobs pattern).
  const handleGiveClick = () => {
    // Anonymous realized-impact ping: records only that a give hand-off happened
    // (EIN + a count). No identity, no amount, no wallet link. sendBeacon survives
    // the navigation to the org's giving page.
    try {
      const body = JSON.stringify({ ein: apiOrg!.EIN })
      if (navigator.sendBeacon) {
        navigator.sendBeacon('/api/handoff', new Blob([body], { type: 'application/json' }))
      } else {
        fetch('/api/handoff', { method: 'POST', body, headers: { 'Content-Type': 'application/json' }, keepalive: true }).catch(() => {})
      }
    } catch { /* ignore */ }
    markPending(givePayload)
  }

  // The always-available certain path. A verified website is not the same as
  // a findable donate page, so this is shown under every CTA, not just on
  // failure. No org setup, no third party, no funds through MERIT.
  const mailingAddress = apiOrg!.address
    ? `${apiOrg!.address}${apiOrg!.CITY ? `, ${apiOrg!.CITY}` : ''}${apiOrg!.STATE ? `, ${apiOrg!.STATE}` : ''}${apiOrg!.zipcode ? ` ${apiOrg!.zipcode}` : ''}`
    : null
  const certainPath = (
    <p className="mt-2 font-body text-[12px] text-muted-cream/55 leading-[1.5] max-w-[360px]">
      Can&rsquo;t find their donate page? Give using EIN{' '}
      <span className="text-muted-cream/80 font-medium">{formatEIN(org.ein)}</span> through your bank or donor-advised fund{mailingAddress ? <>, or mail a check to <span className="text-muted-cream/80">{mailingAddress}</span></> : ''}.
    </p>
  )

  return (
    <div className="min-h-[100dvh]">
      {/* Profile Header */}
      <div className="bg-deep-navy pt-[72px] relative overflow-hidden" style={{ background: 'linear-gradient(to bottom, #0A1628 70%, transparent)' }}>
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 py-8 md:py-12 lg:py-16">
          <div className="flex items-center justify-between gap-2 mb-6">
            <div className="flex items-center gap-2">
              <Link to="/" className="font-body text-[12px] tracking-[0.02em] text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
              <span className="text-muted-cream/50">/</span>
              <Link to="/directory" className="font-body text-[12px] tracking-[0.02em] text-muted-cream hover:text-warm-cream transition-colors">Directory</Link>
              <span className="text-muted-cream/50">/</span>
              <span className="font-body text-[12px] tracking-[0.02em] text-muted-cream truncate max-w-[200px]">{org.name}</span>
            </div>
            <button
              onClick={() => toggleSave(org.ein, { name: org.name, city: org.city || undefined, state: org.state || undefined, ntee1: org.category || undefined })}
              title={isSaved(org.ein) ? 'Remove from saved' : 'Save organization'}
              className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border transition-all duration-150 font-body text-[12px] font-medium"
              style={{
                borderColor: isSaved(org.ein) ? '#C9A96E' : 'rgba(201,169,110,0.3)',
                color: isSaved(org.ein) ? '#C9A96E' : '#A89F94',
                background: isSaved(org.ein) ? 'rgba(201,169,110,0.1)' : 'transparent',
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill={isSaved(org.ein) ? '#C9A96E' : 'none'} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
              </svg>
              {isSaved(org.ein) ? 'Saved' : 'Save'}
            </button>

            {/* Desktop Give button */}
            <button
              onClick={handleGiveToggle}
              className="hidden md:inline-flex items-center gap-2 px-5 py-1.5 rounded-full font-body text-[13px] font-semibold transition-all duration-150"
              style={{
                backgroundColor: inList ? 'transparent' : '#C9A96E',
                color: inList ? '#C9A96E' : '#0A1628',
                border: inList ? '1px solid #C9A96E' : '1px solid transparent',
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24"
                fill="none"
                stroke={inList ? '#C9A96E' : '#0A1628'}
                strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
              >
                <path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>
              </svg>
              {inList ? 'Saved to Wallet' : 'Save to Wallet'}
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[1fr_auto] gap-8 items-start">
            <div>
              <div className="flex items-start gap-4 sm:gap-5">
                {/* Logo slot -- placeholder (org initials) until the organization uploads
                    its logo on claim (B4). Reserves a clean, defined identity space. */}
                <div className="shrink-0 mt-1.5 w-14 h-14 sm:w-16 sm:h-16 rounded-2xl flex items-center justify-center border border-white/15 bg-white/[0.06]">
                  <span className="font-display text-[22px] sm:text-[26px] text-soft-gold leading-none tracking-tight">
                    {org.name.split(/\s+/).filter(Boolean).slice(0, 2).map((w: string) => w[0]).join('').toUpperCase()}
                  </span>
                </div>
                <h1 className="font-display italic text-warm-cream leading-[0.95] tracking-[-0.02em]" style={{ fontSize: 'clamp(34px, 5.5vw, 66px)' }}>
                  {org.name}
                </h1>
              </div>
              <div className="flex items-center gap-3 mt-4 flex-wrap">
                <div className="flex items-center gap-2">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#A89F94" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
                  </svg>
                  <span className="font-body text-[16px] text-muted-cream">{org.city}, {org.state}</span>
                </div>
              </div>

              {/* Stub banner -- shown when org is IRS-registered but has no 990 data */}
              {apiOrg!.source === 'bmf_stub' && apiOrg!.total_revenue == null && (
                <div className="mt-4 flex items-start gap-3 px-4 py-3 rounded-xl bg-white/8 border border-white/12">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#A89F94" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mt-0.5 shrink-0">
                    <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                  </svg>
                  <p className="font-body text-[13px] text-muted-cream/70 leading-[1.55]">
                    This is a registered US nonprofit. No annual financial report is on file yet, so detailed data and a score aren't available.
                  </p>
                </div>
              )}

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
                    <p className="font-body text-[13px] text-warm-cream/85 leading-[1.65]">{b.detail}</p>
                    <p className="mt-2 font-body text-[10px] text-muted-cream/40 tracking-[0.01em]">{b.source}</p>
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
                    : `Net assets cover only ${apiOrg!.months_of_reserve.toFixed(1)} months of costs`}
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
                  org.founded > 0 && { icon: (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>), label: 'Founded', value: String(org.founded) },
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

              {/* Giving hand-off. Priority:
                  1. donate_url -- a direct giving page found on the org's site (Donorbox, etc.)
                     No hunting needed; skips straight to the form.
                  2. website_status=ok -- org's own homepage, verified live and on-domain.
                  3. EIN fallback -- unspoofable ProPublica/IRS record, works for every org. */}
              {(() => {
                const donateUrlStatus = apiOrg?.donate_url_status;
                const donateUrl  = donateUrlStatus === 'dead' ? null : apiOrg?.donate_url;
                const donatePlatform = apiOrg?.donate_platform;
                const platformLabel: Record<string, string> = {
                  donorbox:       'Donorbox',
                  givelively:     'Give Lively',
                  givebutter:     'Givebutter',
                  zeffy:          'Zeffy',
                  stripe:         'Stripe',
                  square:         'Square',
                  classy:         'Classy',
                  mightycause:    'Mightycause',
                  gofundme:       'GoFundMe',
                  fundly:         'Fundly',
                  causevox:       'CauseVox',
                  every_org:      'Every.org',
                  networkforgood: 'Network for Good',
                  justgiving:     'JustGiving',
                  idonate:        'iDonate',
                  flipcause:      'Flipcause',
                  qgiv:           'Qgiv',
                  anedot:         'Anedot',
                  paypal:         'PayPal',
                  venmo:          'Venmo',
                  cashapp:        'Cash App',
                };
                const label = donatePlatform ? (platformLabel[donatePlatform] ?? donatePlatform) : null;

                if (donateUrl) {
                  return (
                    <div className="mt-5">
                      <a
                        href={donateUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={handleGiveClick}
                        className="inline-flex items-center gap-2 font-body text-[15px] font-semibold bg-soft-gold text-deep-navy px-7 py-3 rounded-full hover:bg-bright-gold transition-colors"
                      >
                        Give directly
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                      </a>
                      {label && (
                        <span className="ml-3 font-body text-[11px] text-muted-cream/50 align-middle">
                          via {label}
                        </span>
                      )}
                      <p className="mt-2.5 font-body text-[12px] text-muted-cream/60 leading-[1.5] max-w-[360px]">
                        Takes you straight to their giving page. You give directly to the nonprofit. Daanaa never receives, holds, or processes your money.
                      </p>
                      {(org as any).website && (
                        <button
                          onClick={() => setShowVolunteer(true)}
                          className="mt-3 inline-flex items-center gap-1.5 font-body text-[13px] text-muted-cream/80 underline underline-offset-2 hover:text-warm-cream transition-colors"
                        >
                          Or volunteer your time
                        </button>
                      )}
                      {apiOrg?.data_badges?.donate === 'beta' && (
                        <p className="mt-1.5 font-body text-[11px] text-cool-grey/70 flex items-center gap-1.5">
                          <AiBadge title="Donate link auto-discovered — not confirmed by the organization" />
                          <span>·</span>
                          <span>Not confirmed by the organization.</span>
                          <Link to={`/for-nonprofits?ein=${apiOrg!.EIN}`} className="underline underline-offset-2 hover:text-cool-grey transition-colors">Is this your org?</Link>
                        </p>
                      )}
                      {(org as any).website && apiOrg!.website_status === 'ok' && (
                        <p className="mt-1.5 font-body text-[12px] text-muted-cream/40">
                          Or{' '}
                          <a
                            href={(org as any).website.startsWith('http') ? (org as any).website : `https://${(org as any).website}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="underline underline-offset-2 hover:text-muted-cream/70 transition-colors"
                          >
                            visit their website
                          </a>
                        </p>
                      )}
                      {certainPath}
                    </div>
                  );
                }

                if ((org as any).website && apiOrg!.website_status === 'beta') {
                  return (
                    <div className="mt-5">
                      <a
                        href={(org as any).website.startsWith('http') ? (org as any).website : `https://${(org as any).website}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={handleGiveClick}
                        className="inline-flex items-center gap-2 font-body text-[15px] font-semibold bg-soft-gold text-deep-navy px-7 py-3 rounded-full hover:bg-bright-gold transition-colors"
                      >
                        Visit website
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                      </a>
                      <p className="mt-1.5 font-body text-[11px] text-cool-grey/70 flex items-center gap-1.5">
                        <span className="border border-cool-grey/30 text-cool-grey rounded text-[10px] px-1.5 py-0.5">⚠️ discovered</span>
                        <span>·</span>
                        <span>Not confirmed by the organization.</span>
                        <Link to={`/for-nonprofits?ein=${apiOrg!.EIN}`} className="underline underline-offset-2 hover:text-cool-grey transition-colors">Verify</Link>
                      </p>
                      <p className="mt-2.5 font-body text-[12px] text-muted-cream/60 leading-[1.5] max-w-[360px]">
                        Always confirm on their official channels before donating. You give directly to the nonprofit. Daanaa never receives, holds, or processes your money.
                      </p>
                      {certainPath}
                    </div>
                  );
                }

                if ((org as any).website && apiOrg!.website_status === 'ok') {
                  return (
                    <div className="mt-5">
                      <a
                        href={(org as any).website.startsWith('http') ? (org as any).website : `https://${(org as any).website}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={handleGiveClick}
                        className="inline-flex items-center gap-2 font-body text-[15px] font-semibold bg-soft-gold text-deep-navy px-7 py-3 rounded-full hover:bg-bright-gold transition-colors"
                      >
                        Support this organization
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                      </a>
                      <p className="mt-2.5 font-body text-[12px] text-muted-cream/60 leading-[1.5] max-w-[360px]">
                        Opens their own website. Look for &ldquo;Donate&rdquo; or &ldquo;Give&rdquo;, usually in the top menu. You give directly to the nonprofit. Daanaa never receives, holds, or processes your money.
                      </p>
                      {certainPath}
                    </div>
                  );
                }

                return (
                  <div className="mt-5">
                    <a
                      href={`https://projects.propublica.org/nonprofits/organizations/${org.ein.replace(/-/g, '')}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={handleGiveClick}
                      className="inline-flex items-center gap-2 font-body text-[15px] font-semibold bg-soft-gold text-deep-navy px-7 py-3 rounded-full hover:bg-bright-gold transition-colors"
                    >
                      View public record
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                    </a>
                    <p className="mt-2.5 font-body text-[12px] text-muted-cream/60 leading-[1.5] max-w-[360px]">
                      We could not verify this organization&rsquo;s own website, so we link its IRS-backed record instead. You give directly to the nonprofit. Daanaa never receives, holds, or processes your money.
                    </p>
                    {certainPath}
                  </div>
                );
              })()}

              {/* Loop-closer: connect the give moment to a private record.
                  Appears under whichever CTA rendered. */}
              <div className="mt-4">
                {hasGiven ? (
                  <span className="inline-flex items-center gap-2 font-body text-[13px] text-emerald-400">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
                    In your Giving Wallet
                    <Link to="/wallet" className="text-soft-gold hover:text-bright-gold transition-colors underline underline-offset-2">View</Link>
                  </span>
                ) : (
                  <button
                    onClick={handleGiveToggle}
                    className="inline-flex items-center gap-1.5 font-body text-[13px] text-soft-gold hover:text-bright-gold transition-colors"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                    Keep a private record of this gift
                  </button>
                )}
                <p className="mt-1.5 font-body text-[11px] text-muted-cream/40 leading-[1.5] max-w-[340px]">
                  Saved on your device only, for your tax records. Never shared, never tracked.
                </p>
              </div>
            </div>

            {!(apiOrg!.source === 'bmf_stub' && apiOrg!.total_revenue == null) && (
            <div className="flex flex-col items-center gap-3 lg:pt-4">
              {/* LampMark lg -- tappable, opens TierBreakdown inline */}
              <LampMark
                tier={lampTier}
                size="lg"
                onClick={() => setShowTierBreakdown(s => !s)}
              />
              {/* Tier name + plain subtitle */}
              <div className="flex flex-col items-center gap-0.5">
                <Link
                  to="/tiers"
                  className="font-body text-[12px] tracking-[0.04em] uppercase hover:text-bright-gold transition-colors"
                  style={{ color: TIER_COLORS[lampTier] }}
                >
                  {lampTier}
                </Link>
                <span className="font-body text-[10px] text-muted-cream/50">
                  {({'Beacon':'Fully documented','Torch':'Well documented','Candle':'Financials on record','Ember':'IRS registered','Spark':'IRS registered','Glow':'IRS registered'} as Record<string,string>)[lampTier] ?? 'IRS registered'}
                </span>
              </div>
              {/* IRS verification -- a real, defensible fact for every org */}
              <div className="flex flex-col items-center gap-2 text-center">
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/15 text-emerald-400 font-body text-[12px] font-medium">
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
                  Registered US Nonprofit
                </span>
                {apiOrg!.latest_tax_year && (
                  <span className="font-body text-[11px] text-muted-cream/60">
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
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded border border-cool-grey/30 text-cool-grey font-body text-[11px]">
                    Unclaimed
                  </span>
                )}
              </div>
              {/* v4.0 Financial Health — model-specific peer comparison (when available) */}
              {v4Health && (
                <div className="flex flex-col items-center gap-0.5 px-3 py-2 rounded-lg border border-soft-gold/40 bg-soft-gold/8">
                  <span className="font-body text-[10px] tracking-[0.06em] uppercase text-muted-cream/60">
                    Financial health
                  </span>
                  <span className="font-body text-[14px] font-semibold text-soft-gold">
                    {v4Health.tier}
                  </span>
                  {v4Health.operatingModel && (
                    <span className="font-body text-[10px] text-muted-cream/70 text-center leading-[1.4]">
                      Among {v4Health.operatingModel?.replace(/_/g, ' ')} nonprofits
                    </span>
                  )}
                  {v4Health.peerCellSize && (
                    <span className="font-body text-[9px] text-muted-cream/50">
                      Peer group: {v4Health.peerCellSize.toLocaleString()} orgs
                    </span>
                  )}
                </div>
              )}
              <button
                onClick={() => setShowScoreExplainer(s => !s)}
                className="font-body text-[11px] text-muted-cream/40 hover:text-soft-gold transition-colors"
              >
                How is this scored? {showScoreExplainer ? '↑' : '→'}
              </button>
              {showScoreExplainer && (
                <div className="w-full px-3 py-3 rounded-lg bg-white/5 border border-white/10 text-left space-y-2">
                  <p className="font-body text-[11px] text-muted-cream/70 leading-[1.5]">
                    We compare reserves, program spending, and revenue stability against nonprofits in the same cause area and revenue range. The 0-100 score shows where they stand within that group of {apiOrg!.peer_total ? apiOrg!.peer_total.toLocaleString() : 'similar'} orgs.
                  </p>
                  <p className="font-body text-[10px] text-muted-cream/50 leading-[1.5]">
                    Source: Annual financial reports via ProPublica Nonprofit Explorer
                    {apiOrg!.latest_tax_year ? ` · FY${apiOrg!.latest_tax_year}` : ''}.
                  </p>
                  <Link
                    to="/methodology"
                    className="font-body text-[10px] text-soft-gold hover:text-bright-gold transition-colors block"
                  >
                    Full methodology →
                  </Link>
                </div>
              )}
            </div>
            )}{/* end stub score conditional */}
          </div>
        </div>
      </div>

      {/* Tier Breakdown -- inline, no navigation */}
      {showTierBreakdown && (
        <div className="bg-deep-navy border-t border-white/8 py-8">
          <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
            <TierBreakdown
              org={apiOrg!}
              tier={lampTier}
              onClose={() => setShowTierBreakdown(false)}
            />
          </div>
        </div>
      )}

      {/* Body: 70/30 grid -- main content left, org wall right */}
      <div className="bg-warm-cream">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 py-12 md:py-16">
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-8 items-start">

            {/* LEFT COLUMN -- main content */}
            <div className="min-w-0">

      {/* Financial Overview */}
      <div className="py-0">
        <div>

          {/* Key financial metrics row -- shown when ProPublica data is available */}
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
                  <span className="block font-body text-[10px] tracking-[0.07em] text-cool-grey uppercase font-medium mb-1">Savings runway</span>
                  <span
                    className="block font-body text-[26px] font-semibold tracking-[-0.02em]"
                    style={{ color: apiOrg!.months_of_reserve < 0 ? '#8B1A1A' : apiOrg!.months_of_reserve < 3 ? '#92400E' : '#0A1628' }}
                  >
                    {apiOrg!.months_of_reserve! > 999 ? '999+' : apiOrg!.months_of_reserve! < 0 ? `(${Math.abs(apiOrg!.months_of_reserve!).toFixed(1)})` : apiOrg!.months_of_reserve!.toFixed(1)}
                  </span>
                  <span className="font-body text-[11px] text-cool-grey">
                    {apiOrg!.months_of_reserve < 0
                      ? 'months, negative net assets'
                      : apiOrg!.months_of_reserve < 3
                      ? 'months net assets cover costs'
                      : 'months net assets cover costs'}
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
                    {apiOrg!.latest_tax_year && <span className="ml-1.5 text-cool-grey/50">· FY {apiOrg!.latest_tax_year}</span>}
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
                    {apiOrg!.latest_tax_year && <span className="ml-1.5 text-cool-grey/50">· FY {apiOrg!.latest_tax_year}</span>}
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

          {/* Financial Context Assessment — stewardship-aligned (P3, P4, P5, P6, P9) */}
          {apiOrg! && (
            <div className="mb-8">
              <FinancialContext org={apiOrg!} />
            </div>
          )}

          {/* How They Manage Resources -- financial health context, collapsed by default */}
          {apiOrg!.financial_health && (
            <div className="mb-8">
              <button
                onClick={() => setShowResources(s => !s)}
                className="w-full flex items-center justify-between px-5 py-4 bg-white border border-light-grey rounded-xl hover:border-soft-gold/50 transition-colors group"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span className="font-body text-[11px] tracking-[0.06em] text-cool-grey uppercase font-medium shrink-0">How they manage resources</span>
                  <span className={`shrink-0 inline-block px-2.5 py-0.5 rounded font-body text-[11px] font-semibold ${
                    apiOrg!.financial_health === 'Strong'
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      : apiOrg!.financial_health === 'Stable'
                      ? 'bg-blue-50 text-blue-700 border border-blue-200'
                      : 'bg-amber-50 text-amber-700 border border-amber-200'
                  }`}>
                    {apiOrg!.financial_health}
                  </span>
                  {!showResources && apiOrg!.peer_total && (
                    <span className="font-body text-[12px] text-cool-grey truncate hidden md:block">
                      among {apiOrg!.peer_total.toLocaleString()} similar organizations
                    </span>
                  )}
                </div>
                <svg
                  width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                  className={`shrink-0 text-cool-grey group-hover:text-soft-gold transition-transform duration-200 ${showResources ? 'rotate-180' : ''}`}
                >
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </button>

              {showResources && (
                <div className="mt-1 bg-white border border-light-grey border-t-0 rounded-b-xl px-5 pb-5 pt-4 space-y-4">
                  {(() => {
                    const HEALTH_MEANINGS: Record<string, Record<string, string>> = {
                      Clinical_Reimbursement: { Strong: 'Strong reimbursement coverage and healthy operating reserves', Stable: 'Consistent patient revenue, steady program delivery', Inspiring: 'Committed to care within tight reimbursement margins' },
                      Direct_Delivery: { Strong: 'Solid program efficiency and financial runway for the mission', Stable: 'Reliable service delivery with predictable funding', Inspiring: 'High-impact direct service within resource constraints' },
                      Activity_Programming: { Strong: 'Broad programming reach, strong participation-driven revenue', Stable: 'Consistent activity base, steady community engagement', Inspiring: 'Vibrant programming with lean operational means' },
                      Community_Human_Services: { Strong: 'Program efficiency, financial resilience across service lines', Stable: 'Reliable community delivery, predictable operational base', Inspiring: 'Remarkable community service within tight constraints' },
                      Emergency_Logistics: { Strong: 'Strong surge capacity and reserve depth for response cycles', Stable: 'Reliable response readiness, steady logistics funding', Inspiring: 'Committed frontline response with limited reserves' },
                      Cause_Advocacy_Research: { Strong: 'Well-resourced mission and strong organizational staying power', Stable: 'Consistent advocacy funding, steady research operations', Inspiring: 'Impactful advocacy and research within lean resources' },
                      Intermediary_Public_Benefit: { Strong: 'Effective grant deployment with strong organizational reserves', Stable: 'Consistent intermediary function, reliable grant flow', Inspiring: 'High-leverage public benefit work with constrained capital' },
                      Faith_Community: { Strong: 'Mission vitality supported by sustained congregational giving', Stable: 'Steady congregational support, predictable ministry funding', Inspiring: 'Growing faith mission within meaningful financial constraints' },
                      Membership_Mutual_Benefit: { Strong: 'Active member-driven revenue and long-term reserve depth', Stable: 'Stable membership base, consistent mutual support model', Inspiring: 'Growing member community building toward long-term stability' },
                    }
                    const model = apiOrg!.operating_model as string | null
                    const tier = apiOrg!.financial_health as string
                    const meaning = model ? (HEALTH_MEANINGS[model]?.[tier] ?? '') : ''
                    const modelLabel = model ? model.replace(/_/g, ' ') : null

                    return (
                      <>
                        {meaning && (
                          <p className="font-body text-[14px] text-deep-navy leading-[1.6]">{meaning}</p>
                        )}

                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                          {apiOrg!.program_expense_pct != null && apiOrg!.program_expense_pct > 0 && (
                            <div className="rounded-lg bg-warm-cream px-4 py-3">
                              <span className="block font-body text-[10px] tracking-[0.06em] text-cool-grey uppercase font-medium mb-1">Programs</span>
                              <span className="block font-body text-[22px] font-semibold text-deep-navy tracking-[-0.02em]">
                                {apiOrg!.program_expense_pct.toFixed(0)}¢
                              </span>
                              <span className="block font-body text-[11px] text-cool-grey">of every dollar spent on programs</span>
                            </div>
                          )}
                          {apiOrg!.months_of_reserve != null && (
                            <div className="rounded-lg bg-warm-cream px-4 py-3">
                              <span className="block font-body text-[10px] tracking-[0.06em] text-cool-grey uppercase font-medium mb-1">Savings runway</span>
                              <span className="block font-body text-[22px] font-semibold text-deep-navy tracking-[-0.02em]">
                                {apiOrg!.months_of_reserve > 999 ? '99+' : apiOrg!.months_of_reserve.toFixed(0)} mo
                              </span>
                              <span className="block font-body text-[11px] text-cool-grey">months net assets cover costs</span>
                            </div>
                          )}
                          {apiOrg!.total_revenue != null && apiOrg!.total_expenses != null && apiOrg!.total_expenses > 0 && (
                            <div className="rounded-lg bg-warm-cream px-4 py-3">
                              <span className="block font-body text-[10px] tracking-[0.06em] text-cool-grey uppercase font-medium mb-1">Revenue vs costs</span>
                              <span className="block font-body text-[22px] font-semibold text-deep-navy tracking-[-0.02em]">
                                {apiOrg!.total_revenue >= apiOrg!.total_expenses ? '+' : ''}
                                {(((apiOrg!.revenue_3yr_avg ?? apiOrg!.total_revenue) - apiOrg!.total_expenses) / apiOrg!.total_expenses * 100).toFixed(0)}%
                              </span>
                              <span className="block font-body text-[11px] text-cool-grey">
                                {apiOrg!.revenue_3yr_avg ? '3-year average vs costs' : 'revenue vs costs'}
                              </span>
                            </div>
                          )}
                        </div>

                        <div className="flex items-center justify-between pt-1">
                          <p className="font-body text-[11px] text-cool-grey">
                            Compared to {apiOrg!.peer_total?.toLocaleString() ?? 'similar'} {modelLabel ?? 'similar'} organizations
                            {apiOrg!.peer_rank && apiOrg!.peer_total ? ` · ranked #${apiOrg!.peer_rank.toLocaleString()} of ${apiOrg!.peer_total.toLocaleString()}` : ''}
                          </p>
                          <Link to="/methodology" className="font-body text-[11px] text-soft-gold hover:text-bright-gold transition-colors shrink-0 ml-3">
                            How we score →
                          </Link>
                        </div>
                      </>
                    )
                  })()}
                </div>
              )}
            </div>
          )}

          {/* About this listing + the org's claimable spaces get the full width
              and are clearly defined. The wide revenue trend chart moves to its
              own full-width block below this (see "Revenue Trend" section). */}
          <div>
            <div className="flex flex-col gap-4">
              {/* About this listing -- informational only */}
              <div className="bg-white border border-light-grey rounded-xl px-6 py-5">
                <span className="font-body text-[11px] tracking-[0.06em] text-cool-grey uppercase font-medium">About this listing</span>
                {lampTier === 'Beacon' ? (
                  <p className="mt-2 font-body text-[15px] text-deep-navy leading-[1.6]">
                    {apiOrg!.organization_name} is a registered US nonprofit with an annual report, mission, website, and top-quartile financial context all on public record.
                  </p>
                ) : lampTier === 'Torch' ? (
                  <p className="mt-2 font-body text-[15px] text-deep-navy leading-[1.6]">
                    {apiOrg!.organization_name} is a federally recognized nonprofit with financial filings on public record. They hold federal tax-exempt status as a charitable organization. This profile will grow as more data becomes available.
                  </p>
                ) : (
                  <>
                    <p className="mt-2 font-body text-[15px] text-deep-navy leading-[1.6]">
                      {apiOrg!.organization_name} is a federally recognized nonprofit holding federal tax-exempt status. The IRS has recognized them as a charitable organization.
                    </p>
                    <p className="mt-2 font-body text-[13px] text-cool-grey leading-[1.6]">
                      Financial data isn't on public record yet for this organization. That's a data availability question, not a reflection of their work. Donors often learn about organizations like this through their community, the people behind them, and what they actually do.
                    </p>
                  </>
                )}
                {apiOrg!.claim_status === 'active' && (
                  <p className="mt-3 font-body text-[12px] text-cool-grey">This page is managed by the organization.</p>
                )}
                {apiOrg!.claim_status === 'letter_sent' && (
                  <p className="mt-3 font-body text-[12px] text-cool-grey">Claim in progress -- verification letter sent.</p>
                )}
                {apiOrg!.irs_status_verified_at && (
                  <p className="mt-3 font-body text-[11px] text-cool-grey/70">
                    IRS status verified {new Date(apiOrg!.irs_status_verified_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                  </p>
                )}
              </div>

              {/* Claim CTA + spaces preview -- only for unclaimed pages */}
              {apiOrg!.claim_status !== 'active' && apiOrg!.claim_status !== 'letter_sent' && (
                <div className="rounded-xl border border-dashed border-soft-gold/30 bg-soft-gold/[0.03] px-6 py-5">
                  <div className="flex items-center justify-between gap-4 flex-wrap">
                    <div>
                      <p className="font-body text-[13px] font-medium text-deep-navy">Is this your nonprofit?</p>
                      <p className="font-body text-[12px] text-cool-grey mt-0.5">Add your mission, donation link, and updates -- free.</p>
                    </div>
                    <Link
                      to={`/for-nonprofits?ein=${apiOrg!.EIN}`}
                      className="shrink-0 inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-soft-gold/50 text-soft-gold font-body text-[13px] font-medium hover:bg-soft-gold/10 transition-colors"
                    >
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                      </svg>
                      Claim this page
                    </Link>
                  </div>
                  <div className="mt-4 grid grid-cols-2 gap-2">
                    {[
                      { t: 'Ways to help', d: 'Donate, volunteer, and in-kind needs' },
                      { t: 'What we need now', d: 'A specific ask donors can act on' },
                      { t: 'In our words', d: "Mission in the org's own voice" },
                      { t: 'Updates & events', d: 'Short, dated notes from the org' },
                    ].map(s => (
                      <div key={s.t} className="rounded-lg border border-dashed border-light-grey bg-white/60 px-3 py-2">
                        <p className="font-body text-[12px] font-medium text-deep-navy">{s.t}</p>
                        <p className="font-body text-[11px] text-cool-grey/70">{s.d}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Revenue Trend -- its own full-width block, below the About / claim space.
          Wide and clearly defined so it's easy to read for anyone learning more. */}
      {revenueTrend.length >= 2 && (() => {
        const first = revenueTrend[0].amount
        const last = revenueTrend[revenueTrend.length - 1].amount
        const trendWindow = revenueTrend.slice(-5)
        const trendFirst  = trendWindow[0].amount
        const trendYears  = trendWindow.length - 1
        const pct = (first === 0 || trendFirst === 0) ? 0 : Math.round(((last - trendFirst) / trendFirst) * 100)
        const isFlat = Math.abs(pct) < 2
        return (
          <div className="border-t border-light-grey pt-12 md:pt-16 mt-0">
            <div className="flex items-center gap-3 mb-5 flex-wrap">
              <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">Revenue over time</span>
              {first !== 0 && (
                <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full font-body text-[12px] font-medium border"
                  style={isFlat
                    ? { background: '#F5F4F2', borderColor: '#D9D4CE', color: '#6B7280' }
                    : pct > 0
                    ? { background: '#ECFDF5', borderColor: '#A7F3D0', color: '#065F46' }
                    : { background: '#FEF2F2', borderColor: '#FECACA', color: '#991B1B' }}
                >
                  <span>{isFlat ? '→' : pct > 0 ? '↗' : '↘'}</span>
                  <span>{isFlat ? 'Flat' : `${pct > 0 ? '+' : ''}${pct}%`} over {trendYears} year{trendYears !== 1 ? 's' : ''}</span>
                </span>
              )}
            </div>
            <RevenueChart data={revenueTrend} />
          </div>
        )
      })()}

      {/* Mission & Programs */}
      <div className="border-t border-light-grey pt-12 md:pt-16 mt-0">
        <div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">MISSION</span>
                {['ai_ntee', 'ai_haiku', 'ai_web', 'ai_generated'].includes(
                  apiOrg?.data_badges?.mission ?? apiOrg?.mission_source ?? '') && (
                  <AiBadge />
                )}
                {apiOrg?.data_badges?.mission === 'lucido' && (
                  <span
                    className="border border-cool-grey/30 text-cool-grey rounded text-[10px] px-1.5 py-0.5"
                    title="Sourced from public IRS filings -- not confirmed by the organization"
                  >
                    from public records
                  </span>
                )}
                {apiOrg?.data_badges?.mission === 'claimed' && (
                  <span className="border border-soft-gold/30 text-soft-gold rounded text-[10px] px-1.5 py-0.5">
                    ✓ by organization
                  </span>
                )}
              </div>
              {org.mission ? (
                <p className="mt-3 font-display italic text-deep-navy text-[18px] leading-[1.6]">&ldquo;{org.mission.replace(/^["\s]+|["\s]+$/g, '')}&rdquo;</p>
              ) : (
                <p className="mt-3 font-body text-cool-grey text-[15px]">Mission statement sourced from public records. Extended narrative not yet available for this organization.</p>
              )}
              {org.programs.length > 0 && (
                <>
                  <span className="block mt-8 font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">PROGRAMS</span>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {org.programs.map((program) => (
                      <span key={program} className="px-3 py-1.5 rounded-full bg-navy-mid/10 text-deep-navy font-body text-[13px]">{program}</span>
                    ))}
                  </div>
                </>
              )}
            </div>
            <div>
              {org.leadership.length > 0 ? (
                <>
                  <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">LEADERSHIP</span>
                  <div className="mt-4 space-y-4">
                    {org.leadership.map((person) => (
                      <div key={person.name} className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-full bg-soft-gold/20 flex items-center justify-center">
                          <span className="font-body text-[14px] font-semibold text-soft-gold">{person.initials}</span>
                        </div>
                        <div>
                          <p className="font-body text-[14px] font-medium text-deep-navy">{person.name}</p>
                          <p className="font-body text-[12px] text-cool-grey">{person.title}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div className="pt-2">
                  <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">DATA SOURCE</span>
                  <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 font-body text-[13px] text-cool-grey">
                    <div>
                      <p className="text-[10px] uppercase tracking-[0.07em] text-cool-grey/60 mb-0.5">Type</p>
                      <p className="text-deep-navy font-medium">Registered US nonprofit</p>
                    </div>
                    <div>
                      <p className="text-[10px] uppercase tracking-[0.07em] text-cool-grey/60 mb-0.5">EIN</p>
                      <p className="text-deep-navy font-medium">{formatEIN(org.ein)}</p>
                    </div>
                    <div>
                      <p className="text-[10px] uppercase tracking-[0.07em] text-cool-grey/60 mb-0.5">NTEE Category</p>
                      <p className="text-deep-navy font-medium">{(org as any).nteecc || org.category || '--'}</p>
                    </div>
                    {(org as any).revenueBand && (
                      <div>
                        <p className="text-[10px] uppercase tracking-[0.07em] text-cool-grey/60 mb-0.5">Size</p>
                        <p className="text-deep-navy font-medium">{(org as any).revenueBand} nonprofit</p>
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
                    <a href={`https://projects.propublica.org/nonprofits/organizations/${org.ein.replace(/-/g, '')}`}
                       target="_blank" rel="noopener noreferrer"
                       className="font-body text-[13px] text-soft-gold hover:text-bright-gold transition-colors">
                      View on ProPublica Nonprofit Explorer →
                    </a>
                  </p>
                </div>
              )}
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
                <p className="font-body text-[12px] text-cool-grey">Donations are tax-deductible</p>
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
            <button
              onClick={() => setShowBreakdown(s => !s)}
              className="ml-auto shrink-0 font-body text-[12px] text-soft-gold hover:text-bright-gold transition-colors flex items-center gap-1"
            >
              {showBreakdown ? 'Hide breakdown' : 'See full breakdown'}
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                {showBreakdown
                  ? <polyline points="18 15 12 9 6 15"/>
                  : <polyline points="6 9 12 15 18 9"/>
                }
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Score Breakdown (inline, toggled by TrustBadge click or accountability strip) */}
      {showBreakdown && apiOrg && (
        <div className="border-t border-light-grey py-8">
          <div>
            <ScoreBreakdown org={apiOrg} onClose={() => setShowBreakdown(false)} mode="inline" />
          </div>
        </div>
      )}

            </div>{/* end left column */}

            {/* RIGHT COLUMN -- organization wall */}
            <div className="lg:sticky lg:top-24">
              <OrgWallPanel orgName={org.name} ein={org.ein} />
            </div>

          </div>{/* end grid */}
        </div>{/* end max-w container */}
      </div>{/* end bg-warm-cream */}

      {/* Verify This Listing */}
      <div className="bg-warm-cream border-t border-light-grey py-6">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
          <span className="font-body text-[11px] text-cool-grey">Verify this listing: </span>
          <a
            href="https://apps.irs.gov/app/eos/"
            target="_blank" rel="noopener noreferrer"
            className="font-body text-[11px] text-soft-gold hover:text-bright-gold transition-colors"
          >IRS Tax Exempt Search</a>
          <span className="font-body text-[11px] text-cool-grey mx-2">·</span>
          <a
            href={`https://projects.propublica.org/nonprofits/organizations/${org.ein.replace(/-/g, '')}`}
            target="_blank" rel="noopener noreferrer"
            className="font-body text-[11px] text-soft-gold hover:text-bright-gold transition-colors"
          >ProPublica Nonprofit Explorer</a>
          <span className="font-body text-[11px] text-cool-grey mx-2">·</span>
          <a
            href="https://www.nasconet.org/resources/state-government/"
            target="_blank" rel="noopener noreferrer"
            className="font-body text-[11px] text-soft-gold hover:text-bright-gold transition-colors"
          >State Charity Registry</a>
        </div>
      </div>

      {/* Similar Organizations */}
      {similarOrgs.length > 0 && (
        <div className="bg-deep-navy py-16 md:py-24">
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
                    isSaved={isSaved(o.ein)}
                    onToggleSave={(_e, ein, meta) => toggleSave(ein, meta)}
                    apiOrg={raw}
                    trustSummary={simSummary}
                  />
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* Score History */}
      {scoreHistory.length > 1 && (
        <div className="bg-warm-cream border-t border-light-grey py-12 md:py-16">
          <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">Financial scale history</span>
            <h2 className="font-display italic text-deep-navy mt-3 text-[28px] leading-[1.1] mb-6">
              Score over time
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-light-grey">
                    <th className="font-body text-[11px] tracking-[0.06em] text-cool-grey uppercase pb-2 pr-6">Date</th>
                    <th className="font-body text-[11px] tracking-[0.06em] text-cool-grey uppercase pb-2 pr-6">Score</th>
                    <th className="font-body text-[11px] tracking-[0.06em] text-cool-grey uppercase pb-2 pr-6">Revenue rank</th>
                    <th className="font-body text-[11px] tracking-[0.06em] text-cool-grey uppercase pb-2 pr-6">Reserve rank</th>
                    <th className="font-body text-[11px] tracking-[0.06em] text-cool-grey uppercase pb-2">Peer group</th>
                  </tr>
                </thead>
                <tbody>
                  {scoreHistory.map((snap, i) => {
                    const prev = scoreHistory[i - 1]
                    const delta = prev ? Math.round(snap.peer_percentile - prev.peer_percentile) : null
                    return (
                      <tr key={snap.snapshot_date} className="border-b border-light-grey/50">
                        <td className="font-body text-[13px] text-deep-navy py-3 pr-6">{snap.snapshot_date}</td>
                        <td className="py-3 pr-6">
                          <span className="font-body text-[15px] font-semibold text-deep-navy">
                            {Math.round(snap.peer_percentile)}
                          </span>
                          {delta !== null && delta !== 0 && (
                            <span className={`ml-2 font-body text-[11px] font-medium ${delta > 0 ? 'text-emerald-600' : 'text-amber-600'}`}>
                              {delta > 0 ? '+' : ''}{delta}
                            </span>
                          )}
                        </td>
                        <td className="font-body text-[13px] text-cool-grey py-3 pr-6">{formatOrdinal(snap.rev_pct)} pct</td>
                        <td className="font-body text-[13px] text-cool-grey py-3 pr-6">{formatOrdinal(snap.rsv_pct)} pct</td>
                        <td className="font-body text-[12px] text-cool-grey py-3 font-mono">{snap.group_key ?? snap.peer_group ?? '--'}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
            <p className="mt-4 font-body text-[12px] text-cool-grey leading-[1.5]">
              Scores are recomputed as new annual reports are filed. Each row represents a snapshot of raw financial inputs alongside the resulting score.{' '}
              <Link to="/methodology" className="text-soft-gold hover:text-bright-gold transition-colors">
                Methodology →
              </Link>
            </p>
          </div>
        </div>
      )}

      {/* Multi-year Financial History (ProPublica 990 data) */}
      {financials.length > 0 && (
        <div className="bg-warm-cream border-t border-light-grey py-12 md:py-16">
          <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">Annual filings</span>
            <h2 className="font-display italic text-deep-navy mt-3 text-[28px] leading-[1.1] mb-6">
              Financial history
            </h2>
            <div className="overflow-x-auto">
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
                            className="inline-flex items-center gap-1 font-body text-[11px] text-soft-gold hover:text-bright-gold transition-colors"
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

      {/* Mobile sticky Give CTA */}
      <div className="md:hidden fixed bottom-[60px] left-0 right-0 z-40 px-4 pb-2">
        <button
          onClick={handleGiveToggle}
          className="w-full py-4 rounded-full font-body text-[15px] font-semibold transition-all duration-200 flex items-center justify-center gap-2 shadow-lg"
          style={{
            backgroundColor: inList ? '#0A1628' : '#C9A96E',
            color: inList ? '#C9A96E' : '#0A1628',
            border: inList ? '1px solid #C9A96E' : 'none',
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24"
            fill="none"
            stroke={inList ? '#C9A96E' : '#0A1628'}
            strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
          >
            <path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>
          </svg>
          {inList ? 'Remove from Wallet' : 'Save to Wallet'}
        </button>
      </div>

      {showVolunteer && apiOrg && (
        <VolunteerInterest
          orgName={apiOrg.organization_name}
          website={(org as any).website}
          onClose={() => setShowVolunteer(false)}
        />
      )}
    </div>
  )
}
