import { useEffect, useRef, useState, useMemo } from 'react'
import { usePageMeta } from '../hooks/usePageMeta'
import { useParams, Link } from 'react-router-dom'
import OrgCard from '../components/OrgCard'
import { getTierSummary, getTierFromOrg, getFinancialHealth, PASSING_BANDS, TIER_COLORS } from '../components/TrustBadge'
import BadgeChip from '../components/BadgeChip'
import ScoreBreakdown from '../components/ScoreBreakdown'
import LampMark from '../components/LampMark'
import TierBreakdown from '../components/TierBreakdown'
import MistakeRegistry from '../components/MistakeRegistry'
import { useApi } from '../hooks/useApi'
import { useSavedOrgs } from '../hooks/useSavedOrgs'
import { useGivingList } from '../hooks/useGivingList'
import { getOrganization, getScoreHistory, getFinancials } from '../data/api'
import type { ApiOrganization, ScoreSnapshot, ApiFinancialRecord } from '../data/api'
import { formatCurrency, formatNumber } from '../data/organizations'
import { getOrgBadges } from '../utils/badges'

// ---- Revenue Bar Chart ----
function RevenueChart({ data }: { data: { year: number; amount: number }[] }) {
  const [hoveredBar, setHoveredBar] = useState<number | null>(null)
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 })
  const [revealed, setRevealed] = useState(false)
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
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
                style={{ transition: `all 1s ease-out ${i * 0.1}s` }}
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
  const { isInList, addItem, removeItem } = useGivingList()

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
  const revenueTrend = financials
    .filter(f => f.totrevenue !== null && f.totrevenue > 0)
    .map(f => ({ year: f.tax_prd_yr, amount: f.totrevenue! }))

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [id])

  const org = apiOrg ? adaptOrg(apiOrg) : null

  // similar_organizations is returned directly by GET /api/organizations/:ein
  const rawSimilarOrgs = useMemo(() => {
    if (!apiOrg?.similar_organizations) return []
    return (apiOrg.similar_organizations as ApiOrganization[])
      .filter((o) => o.EIN !== apiOrg.EIN)
      .slice(0, 4)
  }, [apiOrg])

  const similarOrgs = useMemo(() => rawSimilarOrgs.map(adaptOrg), [rawSimilarOrgs])

  const inList = isInList(org?.ein || '')

  const metaTitle = apiOrg?.organization_name ?? ''
  const metaDesc = apiOrg
    ? `${apiOrg.organization_name} is an IRS-verified 501(c)(3) nonprofit${apiOrg.CITY ? ` in ${apiOrg.CITY}, ${apiOrg.STATE}` : ''}. MERIT tier: ${apiOrg.merit_tier ?? 'Flame'}. Financial scale: ${apiOrg.peer_percentile != null ? `${Math.round(apiOrg.peer_percentile)}/100` : 'pending'}.`
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
  const finHealth    = getFinancialHealth(apiOrg!)
  const badges = getOrgBadges(apiOrg!)

  const handleGiveToggle = () => {
    if (inList) {
      removeItem(org.ein)
    } else {
      addItem({
        ein: org.ein,
        orgName: org.name,
        city: org.city || undefined,
        state: org.state || undefined,
        ntee1: org.category || undefined,
        amount: 0,
        trustTier: lampTier,
        trustSummary,
      })
    }
  }

  return (
    <div className="min-h-[100dvh]">
      {/* Profile Header */}
      <div className="bg-deep-navy pt-[72px] relative overflow-hidden" style={{ background: 'linear-gradient(to bottom, #0A1628 70%, transparent)' }}>
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 py-12 md:py-16">
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
                <path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z" />
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
                fill={inList ? 'none' : '#0A1628'}
                stroke={inList ? '#C9A96E' : '#0A1628'}
                strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
              >
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
              </svg>
              {inList ? 'In giving list' : 'Add to giving list'}
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[1fr_auto] gap-8 items-start">
            <div>
              <h1 className="font-display italic text-warm-cream leading-[0.95] tracking-[-0.02em]" style={{ fontSize: 'clamp(36px, 6vw, 72px)' }}>
                {org.name}
              </h1>
              <div className="flex items-center gap-3 mt-4 flex-wrap">
                <div className="flex items-center gap-2">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#A89F94" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
                  </svg>
                  <span className="font-body text-[16px] text-muted-cream">{org.city}, {org.state}</span>
                </div>
              </div>

              {/* Badge row — click any badge to see what earned it */}
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

              {/* Inline badge detail — appears below the row when a badge is selected */}
              {selectedBadge && (() => {
                const b = badges.find(x => x.id === selectedBadge)
                return b ? (
                  <div className="mt-3 max-w-[520px] bg-white/8 border border-white/12 rounded-xl px-4 py-3">
                    <p className="font-body text-[13px] text-warm-cream/85 leading-[1.65]">{b.detail}</p>
                    <p className="mt-2 font-body text-[10px] text-muted-cream/40 tracking-[0.01em]">{b.source}</p>
                  </div>
                ) : null
              })()}

              <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-3">
                {[
                  org.founded > 0 && { icon: (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>), label: 'Founded', value: String(org.founded) },
                  org.revenue > 0 && { icon: (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>), label: `Revenue${(org as any).latestTaxYear ? ` FY${(org as any).latestTaxYear}` : ''}`, value: formatCurrency(org.revenue) },
                  (apiOrg!.employee_count ?? 0) > 0 && { icon: (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>), label: 'Employees', value: formatNumber(apiOrg!.employee_count!) },
                  { icon: (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>), label: 'EIN', value: org.ein },
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

              {(org as any).website && (
                <a
                  href={(org as any).website.startsWith('http') ? (org as any).website : `https://${(org as any).website}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-4 inline-flex items-center gap-2 font-body text-[13px] text-soft-gold hover:text-bright-gold transition-colors"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>
                  Visit website
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                </a>
              )}
            </div>

            <div className="flex flex-col items-center gap-3 lg:pt-4">
              {/* LampMark lg — tappable, opens TierBreakdown inline */}
              <LampMark
                tier={lampTier}
                size="lg"
                onClick={() => setShowTierBreakdown(s => !s)}
              />
              {/* Tier name — connects lamp mark to the /tiers page */}
              <Link
                to="/tiers"
                className="font-body text-[12px] tracking-[0.04em] uppercase hover:text-bright-gold transition-colors"
                style={{ color: TIER_COLORS[lampTier] }}
              >
                {lampTier} tier
              </Link>
              {/* IRS verification — a real, defensible fact for every org */}
              <div className="flex flex-col items-center gap-2 text-center">
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/15 text-emerald-400 font-body text-[12px] font-medium">
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
                  IRS-verified 501(c)(3)
                </span>
                {apiOrg!.latest_tax_year && (
                  <span className="font-body text-[11px] text-muted-cream/60">
                    Form 990 on file · FY {apiOrg!.latest_tax_year}
                  </span>
                )}
              </div>
              {/* Independently-verified financial health — only where real 990 analysis exists */}
              {finHealth ? (
                <div
                  className="flex flex-col items-center gap-0.5 px-3 py-2 rounded-lg border"
                  style={{
                    borderColor: PASSING_BANDS.includes(finHealth.band) ? 'rgba(74,222,128,0.35)' : 'rgba(245,158,11,0.35)',
                    background:  PASSING_BANDS.includes(finHealth.band) ? 'rgba(74,222,128,0.10)' : 'rgba(245,158,11,0.10)',
                  }}
                >
                  <span className="font-body text-[10px] tracking-[0.06em] uppercase text-muted-cream/60">
                    Financial health · MERIT-verified
                  </span>
                  <span className="font-body text-[14px] font-semibold" style={{ color: PASSING_BANDS.includes(finHealth.band) ? '#4ADE80' : '#F59E0B' }}>
                    {finHealth.band} · {finHealth.score}/100
                  </span>
                  <span className="font-body text-[10px] text-muted-cream/50">
                    Based on FY{apiOrg!.latest_tax_year ?? '—'} Form 990
                  </span>
                </div>
              ) : (
                <span className="font-body text-[11px] text-muted-cream/50 max-w-[180px] text-center leading-[1.45]">
                  Detailed financial analysis not yet available — requires an itemized Form 990.
                </span>
              )}
              <Link
                to="/methodology"
                className="font-body text-[11px] text-muted-cream/40 hover:text-soft-gold transition-colors"
              >
                How is this scored? →
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Tier Breakdown — inline, no navigation */}
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

      {/* Financial Overview */}
      <div className="bg-warm-cream py-12 md:py-16">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">

          {/* Key financial metrics row — shown when ProPublica data is available */}
          {(apiOrg!.months_of_reserve !== null || apiOrg!.net_assets !== null || apiOrg!.total_expenses !== null) && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              {apiOrg!.months_of_reserve !== null && (
                <div className="bg-white border border-light-grey rounded-xl p-5">
                  <span className="block font-body text-[10px] tracking-[0.07em] text-cool-grey uppercase font-medium mb-1">Months of Reserve</span>
                  <span className="block font-body text-[26px] font-semibold tracking-[-0.02em] text-deep-navy">
                    {apiOrg!.months_of_reserve! > 999 ? '999+' : apiOrg!.months_of_reserve! < 0 ? `(${Math.abs(apiOrg!.months_of_reserve!).toFixed(1)})` : apiOrg!.months_of_reserve!.toFixed(1)}
                  </span>
                  <span className="font-body text-[11px] text-cool-grey">Net assets ÷ monthly expenses</span>
                </div>
              )}
              {apiOrg!.net_assets !== null && (
                <div className="bg-white border border-light-grey rounded-xl p-5">
                  <span className="block font-body text-[10px] tracking-[0.07em] text-cool-grey uppercase font-medium mb-1">Net Assets</span>
                  <span className="block font-body text-[26px] font-semibold tracking-[-0.02em] text-deep-navy">
                    {formatCurrency(apiOrg!.net_assets!)}
                  </span>
                  <span className="font-body text-[11px] text-cool-grey">Assets minus liabilities</span>
                </div>
              )}
              {apiOrg!.total_expenses !== null && (
                <div className="bg-white border border-light-grey rounded-xl p-5">
                  <span className="block font-body text-[10px] tracking-[0.07em] text-cool-grey uppercase font-medium mb-1">Annual Expenses</span>
                  <span className="block font-body text-[26px] font-semibold tracking-[-0.02em] text-deep-navy">
                    {formatCurrency(apiOrg!.total_expenses!)}
                  </span>
                  <span className="font-body text-[11px] text-cool-grey">Total functional expenses</span>
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

          <div className="grid grid-cols-1 lg:grid-cols-[3fr_2fr] gap-8">
            {revenueTrend.length > 0 ? (
              <RevenueChart data={revenueTrend} />
            ) : (
              <div className="bg-white border border-light-grey rounded-xl p-6 flex flex-col justify-center">
                <h4 className="font-display text-deep-navy text-[20px] mb-2">Revenue</h4>
                <p className="font-body text-[32px] font-semibold tracking-[-0.02em] text-deep-navy">
                  {org.revenue > 0 ? formatCurrency(org.revenue) : '—'}
                </p>
                <p className="font-body text-[13px] text-cool-grey mt-2">
                  {org.revenue > 0
                    ? 'Latest reported annual revenue from IRS public records.'
                    : 'This organization files a 990-N (postcard return). Full financials are not publicly available.'}
                </p>
              </div>
            )}
            <div className="flex flex-col gap-4">
              <div className="bg-white border border-light-grey rounded-xl p-6 flex flex-col gap-4">
                <div>
                  <span className="font-body text-[11px] tracking-[0.06em] text-cool-grey uppercase font-medium">About this listing</span>
                  {(lampTier === 'Beacon' || lampTier === 'Lantern') ? (
                    <p className="mt-2 font-body text-[15px] text-deep-navy leading-[1.6]">
                      {apiOrg!.organization_name} is a fully verified nonprofit — IRS 501(c)(3), current 990, mission, and website all on public record.
                      {lampTier === 'Lantern' && ' Reaching a top-quartile financial scale (75th percentile) would light the full Beacon.'}
                    </p>
                  ) : (
                    <p className="mt-2 font-body text-[15px] text-deep-navy leading-[1.6]">
                      {apiOrg!.organization_name} is an IRS-verified 501(c)(3). This profile is still lighting up — adding a mission, website, and financial detail brightens its flame. A lower tier reflects the public data we have, not the organization&rsquo;s quality.
                    </p>
                  )}
                </div>
                {lampTier !== 'Beacon' && lampTier !== 'Lantern' && (
                  <div className="border-t border-light-grey pt-4">
                    <p className="font-body text-[13px] text-cool-grey mb-3">
                      Is this your nonprofit?
                    </p>
                    <Link
                      to="/for-nonprofits"
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-soft-gold/40 text-soft-gold font-body text-[13px] font-medium hover:bg-soft-gold/10 transition-colors"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                      </svg>
                      Claim it free &amp; raise your flame
                    </Link>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Mission & Programs */}
      <div className="bg-warm-cream border-t border-light-grey py-12 md:py-16">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            <div>
              <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">MISSION</span>
              {org.mission ? (
                <p className="mt-3 font-display italic text-deep-navy text-[18px] leading-[1.6]">&ldquo;{org.mission}&rdquo;</p>
              ) : (
                <p className="mt-3 font-body text-cool-grey text-[15px]">Mission statement sourced from IRS 990 public records. Extended narrative not yet available for this organization.</p>
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
                  <div className="mt-4 space-y-2 font-body text-[14px] text-cool-grey">
                    <p>IRS 501(c)(3) verified organization</p>
                    <p>EIN: {org.ein}</p>
                    <p>NTEE Category: {(org as any).nteecc || org.category || '—'}</p>
                    {(org as any).revenueBand && (
                      <p>Size: {(org as any).revenueBand} nonprofit</p>
                    )}
                    <DataFreshnessBadge
                      taxYear={(org as any).latestTaxYear}
                      dataSource={(org as any).dataSource}
                      updatedAt={(org as any).updatedAt}
                    />
                    <p className="mt-4">
                      <a href={`https://projects.propublica.org/nonprofits/organizations/${org.ein.replace(/-/g, '')}`}
                         target="_blank" rel="noopener noreferrer"
                         className="text-soft-gold hover:text-bright-gold transition-colors">
                        View on ProPublica Nonprofit Explorer →
                      </a>
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Accountability Strip */}
      <div className="bg-warm-cream border-t border-light-grey py-8">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6 sm:gap-12">
            <MistakeRegistry compact />
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-success-green/15 flex items-center justify-center shrink-0">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#4ADE80" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/>
                </svg>
              </div>
              <div>
                <p className="font-body text-[13px] font-semibold text-deep-navy">IRS 501(c)(3) Active</p>
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
                <p className="font-body text-[13px] font-semibold text-deep-navy">EIN {org.ein}</p>
                <p className="font-body text-[12px] text-cool-grey">Verified against IRS BMF</p>
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
        <div className="bg-warm-cream border-t border-light-grey py-8">
          <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
            <ScoreBreakdown org={apiOrg} onClose={() => setShowBreakdown(false)} mode="inline" />
          </div>
        </div>
      )}

      {/* Similar Organizations */}
      {similarOrgs.length > 0 && (
        <div className="bg-deep-navy py-16 md:py-24">
          <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-pale-gold uppercase">SIMILAR ORGANIZATIONS</span>
            <h2 className="font-display italic text-warm-cream mt-3 leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(28px, 4vw, 48px)' }}>
              Others you might consider
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
                        <td className="font-body text-[13px] text-cool-grey py-3 pr-6">{Math.round(snap.rev_pct)}th pct</td>
                        <td className="font-body text-[13px] text-cool-grey py-3 pr-6">{Math.round(snap.rsv_pct)}th pct</td>
                        <td className="font-body text-[12px] text-cool-grey py-3 font-mono">{snap.group_key ?? snap.peer_group ?? '—'}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
            <p className="mt-4 font-body text-[12px] text-cool-grey leading-[1.5]">
              Scores are recomputed as new IRS 990 filings become available. Each row represents a snapshot of raw financial inputs alongside the resulting score.{' '}
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
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">990 filings</span>
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
                    <th className="font-body text-[11px] tracking-[0.06em] text-cool-grey uppercase pb-2">990</th>
                  </tr>
                </thead>
                <tbody>
                  {[...financials].reverse().map((f) => (
                    <tr key={f.tax_prd_yr} className="border-b border-light-grey/50 hover:bg-white/50 transition-colors">
                      <td className="font-body text-[13px] font-medium text-deep-navy py-3 pr-4">{f.tax_prd_yr}</td>
                      <td className="font-body text-[13px] text-deep-navy py-3 pr-4">{f.totrevenue != null ? formatCurrency(f.totrevenue) : '—'}</td>
                      <td className="font-body text-[13px] text-cool-grey py-3 pr-4">{f.totfuncexpns != null ? formatCurrency(f.totfuncexpns) : '—'}</td>
                      <td className={`font-body text-[13px] py-3 pr-4 ${(f.totnetassetend ?? 0) < 0 ? 'text-amber-600' : 'text-cool-grey'}`}>
                        {f.totnetassetend != null ? formatCurrency(f.totnetassetend) : '—'}
                      </td>
                      <td className="font-body text-[13px] text-cool-grey py-3 pr-4">{f.totcntrbgfts != null ? formatCurrency(f.totcntrbgfts) : '—'}</td>
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
                        ) : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-4 font-body text-[12px] text-cool-grey">
              Source: ProPublica Nonprofit Explorer · IRS Form 990 public filings
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
            fill={inList ? '#C9A96E' : '#0A1628'}
            stroke={inList ? '#C9A96E' : '#0A1628'}
            strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
          >
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
          </svg>
          {inList ? 'Remove from giving list' : 'Add to giving list'}
        </button>
      </div>
    </div>
  )
}
