import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { useApi } from '../hooks/useApi'
import { getSectorHealth } from '../data/api'
import type { ApiSectorHealth } from '../data/api'
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '../components/ui/tooltip'

type SortKey = 'name' | 'total_orgs' | 'at_risk_pct' | 'avg_months_reserve' | 'avg_program_pct'
type GroupFilter = 'all' | 'direct_service' | 'mission_infrastructure' | 'research_academia' | 'foundations' | 'membership_advocacy' | 'religion_spiritual' | 'international_development' | 'asset_stewards'

// NTEE major code → operating model group
const NTEE_GROUP: Record<string, GroupFilter> = {
  D: 'direct_service',   // Animal-Related
  F: 'direct_service',   // Mental Health
  I: 'direct_service',   // Crime & Legal
  J: 'direct_service',   // Employment
  K: 'direct_service',   // Food, Agriculture
  N: 'direct_service',   // Recreation, Sports
  O: 'direct_service',   // Youth Development
  P: 'direct_service',   // Human Services
  Q: 'international_development', // International
  R: 'direct_service',   // Civil Rights
  A: 'mission_infrastructure', // Arts, Culture
  B: 'mission_infrastructure', // Education
  C: 'mission_infrastructure', // Environment
  E: 'mission_infrastructure', // Health Care
  S: 'mission_infrastructure', // Community Improvement
  U: 'research_academia', // Science & Technology
  V: 'research_academia', // Social Science
  W: 'mission_infrastructure', // Public Benefit
  L: 'asset_stewards',   // Housing, Shelter
  M: 'asset_stewards',   // Public Safety
  Y: 'asset_stewards',   // Mutual Benefit
  G: 'research_academia', // Disease Research
  H: 'research_academia', // Medical Research
  T: 'foundations', // Philanthropy, Voluntarism
  X: 'religion_spiritual', // Religion
}

const GROUP_META: Record<GroupFilter, { label: string; color: string; dot: string; bg: string; border: string; badge: string }> = {
  all:                      { label: 'All sectors', color: 'text-deep-navy', dot: '#0A1628', bg: '', border: '', badge: 'bg-deep-navy/10 text-deep-navy' },
  direct_service:           { label: 'Direct Service', color: 'text-emerald-700', dot: '#059669', bg: 'bg-emerald-50/40', border: 'border-l-4 border-l-emerald-400', badge: 'bg-emerald-100 text-emerald-700' },
  mission_infrastructure:   { label: 'Mission Infrastructure', color: 'text-blue-700', dot: '#2563EB', bg: 'bg-blue-50/40', border: 'border-l-4 border-l-blue-400', badge: 'bg-blue-100 text-blue-700' },
  research_academia:        { label: 'Research & Academia', color: 'text-indigo-700', dot: '#4F46E5', bg: 'bg-indigo-50/40', border: 'border-l-4 border-l-indigo-400', badge: 'bg-indigo-100 text-indigo-700' },
  foundations:              { label: 'Foundations', color: 'text-purple-700', dot: '#7C3AED', bg: 'bg-purple-50/40', border: 'border-l-4 border-l-purple-400', badge: 'bg-purple-100 text-purple-700' },
  membership_advocacy:      { label: 'Membership & Advocacy', color: 'text-rose-700', dot: '#E11D48', bg: 'bg-rose-50/40', border: 'border-l-4 border-l-rose-400', badge: 'bg-rose-100 text-rose-700' },
  religion_spiritual:       { label: 'Religion & Spiritual', color: 'text-amber-700', dot: '#B45309', bg: 'bg-amber-50/40', border: 'border-l-4 border-l-amber-400', badge: 'bg-amber-100 text-amber-700' },
  international_development: { label: 'International Development', color: 'text-cyan-700', dot: '#0891B2', bg: 'bg-cyan-50/40', border: 'border-l-4 border-l-cyan-400', badge: 'bg-cyan-100 text-cyan-700' },
  asset_stewards:           { label: 'Asset Stewards', color: 'text-orange-700', dot: '#EA580C', bg: 'bg-orange-50/40', border: 'border-l-4 border-l-orange-400', badge: 'bg-orange-100 text-orange-700' },
}

function formatMonths(v: number | null) {
  if (v === null) return '—'
  if (v > 999) return '999+'
  return v.toFixed(1)
}

function ReserveBar({ months }: { months: number | null }) {
  if (months === null) return <div className="w-full h-1 bg-light-grey rounded-full" />
  const pct = Math.min(100, (months / 120) * 100)
  const color = months < 3 ? '#EF4444' : months < 12 ? '#F59E0B' : months < 36 ? '#4ADE80' : '#60A5FA'
  return (
    <div className="w-full h-1.5 bg-light-grey rounded-full overflow-hidden">
      <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: color }} />
    </div>
  )
}

function SortIcon({ active, asc }: { active: boolean; asc: boolean }) {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none" className={`inline ml-1 ${active ? 'opacity-100' : 'opacity-30'}`}>
      {asc ? (
        <path d="M5 2L9 8H1L5 2Z" fill="currentColor" />
      ) : (
        <path d="M5 8L1 2H9L5 8Z" fill="currentColor" />
      )}
    </svg>
  )
}

export default function SectorHealth() {
  usePageMeta(
    'Peer financial context by sector',
    'Understand public financial patterns across operating models and cause areas. How organizations in different sectors compare to their peers, based on available public records and financial filings.'
  )

  const navigate = useNavigate()
  const { data, loading } = useApi(() => getSectorHealth(), [])
  const [sortKey, setSortKey] = useState<SortKey>('at_risk_pct')
  const [sortAsc, setSortAsc] = useState(false)
  const [groupFilter, setGroupFilter] = useState<GroupFilter>('all')

  const sectors: ApiSectorHealth[] = data?.sectors ?? []

  const filtered = groupFilter === 'all'
    ? sectors
    : sectors.filter(s => NTEE_GROUP[s.code] === groupFilter)

  const sorted = [...filtered].sort((a, b) => {
    const av = a[sortKey] ?? (sortKey === 'name' ? '' : 0)
    const bv = b[sortKey] ?? (sortKey === 'name' ? '' : 0)
    if (typeof av === 'string' && typeof bv === 'string') {
      return sortAsc ? av.localeCompare(bv) : bv.localeCompare(av)
    }
    return sortAsc ? (av as number) - (bv as number) : (bv as number) - (av as number)
  })

  function handleSort(key: SortKey) {
    if (key === sortKey) setSortAsc(a => !a)
    else { setSortKey(key); setSortAsc(false) }
  }

  const totalAtRisk = sectors.reduce((s, r) => s + r.insolvent + r.at_risk, 0)
  const totalOrgs   = sectors.reduce((s, r) => s + r.total_orgs, 0)

  const Th = ({ label, sortBy, right, tip }: { label: string; sortBy: SortKey; right?: boolean; tip?: string }) => (
    <th
      className={`text-[11px] font-medium tracking-[0.06em] text-cool-grey uppercase pb-3 select-none ${right ? 'text-right' : 'text-left'}`}
    >
      <span className={`inline-flex items-center gap-1 ${right ? 'flex-row-reverse' : ''}`}>
        <span className="cursor-pointer hover:text-deep-navy" onClick={() => handleSort(sortBy)}>
          {label}
          <SortIcon active={sortKey === sortBy} asc={sortAsc} />
        </span>
        {tip && (
          <Tooltip>
            <TooltipTrigger asChild>
              <button type="button" aria-label={`What ${label} means`} className="text-cool-grey hover:text-soft-gold transition-colors leading-none">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
              </button>
            </TooltipTrigger>
            <TooltipContent className="max-w-[260px] font-body text-[12px] leading-[1.5] normal-case tracking-normal">
              {tip}
            </TooltipContent>
          </Tooltip>
        )}
      </span>
    </th>
  )

  return (
    <TooltipProvider delayDuration={150}>
    <div className="min-h-[100dvh]">
      {/* Hero */}
      <div className="bg-deep-navy pt-[72px]" style={{ background: 'linear-gradient(to bottom, #0A1628 80%, #F5F0E8)' }}>
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 py-16 md:py-24">
          <div className="flex items-center gap-2 mb-8">
            <Link to="/" className="font-body text-[12px] tracking-[0.02em] text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream">/</span>
            <span className="font-body text-[12px] tracking-[0.02em] text-muted-cream">Sector Health</span>
          </div>

          <div className="flex items-center gap-3 mb-4">
            <div className="w-6 h-px bg-soft-gold/50" />
            <span className="font-body text-[11px] font-medium tracking-[0.10em] text-soft-gold uppercase">Data analysis</span>
          </div>

          <h1 className="font-display italic text-warm-cream leading-[1.0] tracking-[-0.02em] mb-6"
            style={{ fontSize: 'clamp(40px, 6vw, 72px)' }}>
            Where the sector stands
          </h1>
          <p className="font-body text-[18px] text-muted-cream/80 max-w-[580px] leading-[1.65]">
            How nonprofit sectors compare by operating model. Peer financial context: reserve levels, expense ratios, and filing frequency. Many small or simplified filers don't report full financials, so this reflects patterns in available public records, not every organization.
          </p>
          {data?.generated_at && (
            <p className="font-body text-[13px] text-muted-cream/60 mt-4">
              As of {new Date(data.generated_at).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
              })}
            </p>
          </p>

          {/* Key stat chips */}
          <div className="mt-10 flex flex-wrap gap-4">
            {[
              { value: `${Math.round(totalAtRisk / 1000)}K`, label: 'organizations with limited reserve cushion in public filings', color: '#F59E0B' },
              { value: `${Math.round(totalAtRisk / totalOrgs * 100)}%`, label: 'of indexed 501(c)(3)s with limited savings', color: '#F59E0B' },
              { value: '84%', label: 'of all orgs have reserve data', color: '#60A5FA' },
            ].map(stat => (
              <div key={stat.label} className="flex items-baseline gap-2 px-4 py-3 rounded-xl bg-white/5 border border-white/10">
                <span className="font-display text-[28px] font-medium" style={{ color: stat.color }}>{stat.value}</span>
                <span className="font-body text-[13px] text-muted-cream">{stat.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="bg-warm-cream">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 py-16">

          {/* Operating Model Groups */}
          <div className="mb-10">
            <h2 className="font-display italic text-deep-navy leading-tight mb-2" style={{ fontSize: 'clamp(22px, 2.8vw, 32px)' }}>
              Eight operating models, eight different peer contexts
            </h2>
            <p className="font-body text-[15px] text-cool-grey leading-[1.7] mb-6 max-w-[680px]">
              Peer financial context means different things depending on how an organization operates. A food bank with thin reserves may be deploying every dollar into direct service. A foundation holding capital deploys strategically over years. We compare organizations within their operating model to show meaningful peer context, not across all nonprofits.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                {
                  name: 'Direct Service',
                  orgs: '22,916',
                  reserve: '10.3 mo',
                  prog: '37.3%',
                  desc: 'Food banks, job training, animal rescue, emergency response, mental health',
                  color: 'border-emerald-200 bg-emerald-50',
                  badge: 'text-emerald-700 bg-emerald-100',
                  note: 'Lean by design, high program efficiency',
                },
                {
                  name: 'Mission Infrastructure',
                  orgs: '26,413',
                  reserve: '13.4 mo',
                  prog: '40.4%',
                  desc: 'Schools, hospitals, health systems, arts organizations, libraries',
                  color: 'border-blue-200 bg-blue-50',
                  badge: 'text-blue-700 bg-blue-100',
                  note: 'Assets support program delivery',
                },
                {
                  name: 'Research & Academia',
                  orgs: '10,729',
                  reserve: '8.8 mo',
                  prog: '66.1%',
                  desc: 'Universities, medical research, scientific institutions',
                  color: 'border-indigo-200 bg-indigo-50',
                  badge: 'text-indigo-700 bg-indigo-100',
                  note: 'Program-heavy with grant passthrough',
                },
                {
                  name: 'Foundations',
                  orgs: '3,266',
                  reserve: '34.3 mo',
                  prog: '34.2%',
                  desc: 'Grantmakers, endowments, philanthropies',
                  color: 'border-purple-200 bg-purple-50',
                  badge: 'text-purple-700 bg-purple-100',
                  note: 'Hold and deploy capital strategically',
                },
                {
                  name: 'Membership & Advocacy',
                  orgs: '2,940',
                  reserve: '8.4 mo',
                  prog: '33.1%',
                  desc: 'Member organizations, advocacy networks, voluntarism centers',
                  color: 'border-rose-200 bg-rose-50',
                  badge: 'text-rose-700 bg-rose-100',
                  note: 'Revenue driven by membership support',
                },
                {
                  name: 'Religion & Spiritual',
                  orgs: '3,764',
                  reserve: '20.2 mo',
                  prog: '14.2%',
                  desc: 'Faith communities, congregations, spiritual organizations',
                  color: 'border-amber-200 bg-amber-50',
                  badge: 'text-amber-700 bg-amber-100',
                  note: 'Often volunteer-heavy with community focus',
                },
                {
                  name: 'International Development',
                  orgs: '601',
                  reserve: '9.5 mo',
                  prog: '27.2%',
                  desc: 'Cross-border development, humanitarian aid, international relief',
                  color: 'border-cyan-200 bg-cyan-50',
                  badge: 'text-cyan-700 bg-cyan-100',
                  note: 'Efficient cross-border operations',
                },
                {
                  name: 'Asset Stewards',
                  orgs: '844',
                  reserve: '11.4 mo',
                  prog: '42.3%',
                  desc: 'Nursing homes, hospitals, facilities with physical infrastructure',
                  color: 'border-orange-200 bg-orange-50',
                  badge: 'text-orange-700 bg-orange-100',
                  note: 'Physical assets central to mission',
                },
              ].map(g => (
                <div key={g.name} className={`p-4 rounded-xl border ${g.color}`}>
                  <span className={`inline-block font-body text-[11px] font-semibold px-2 py-0.5 rounded-full mb-2 ${g.badge}`}>{g.name}</span>
                  <p className="font-body text-[12px] text-cool-grey leading-[1.5] mb-3">{g.desc}</p>
                  <p className="font-body text-[10px] font-medium text-cool-grey italic mb-2">{g.note}</p>
                  <div className="flex gap-3 flex-wrap">
                    <div>
                      <p className="font-body text-[9px] font-semibold tracking-[0.08em] text-cool-grey uppercase">Orgs</p>
                      <p className="font-body text-[13px] font-semibold text-deep-navy">{g.orgs}</p>
                    </div>
                    <div>
                      <p className="font-body text-[9px] font-semibold tracking-[0.08em] text-cool-grey uppercase">Med reserve</p>
                      <p className="font-body text-[13px] font-semibold text-deep-navy">{g.reserve}</p>
                    </div>
                    <div>
                      <p className="font-body text-[9px] font-semibold tracking-[0.08em] text-cool-grey uppercase">Prog spend</p>
                      <p className="font-body text-[13px] font-semibold text-deep-navy">{g.prog}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Lead finding */}
          <div className="mb-12 p-6 rounded-2xl bg-amber-50 border border-amber-200/80">
            <p className="font-body text-[15px] text-deep-navy leading-[1.7]">
              <strong>Financial patterns differ dramatically by operating model.</strong>{' '}
              Direct Service organizations average 10.3 months of reserves. Research & Academia averages 8.8 months, since they're grant-heavy and spend the money on programs. Foundations average 34.3 months because they hold capital for strategic deployment. Religion & Spiritual organizations average 20.2 months. These differences reflect how organizations are structured, not how well they're managed.
            </p>
            <p className="mt-3 font-body text-[13px] text-cool-grey">
              Reserve levels that look thin for one type of organization may be entirely appropriate for another. A food bank spending every dollar on direct service operates under completely different financial logic than a foundation deploying endowment. The operating model patterns above are drawn from 71,473 organizations with sufficiently detailed filings to classify by model — a subset of the 356,000 organizations with complete financial data used for the sector benchmarks below. The remaining 79% of indexed nonprofits file simplified returns or are exempt from filing; they are visible in the directory but not scored.
            </p>
          </div>

          {/* Group filter tabs */}
          <div className="mb-6 flex flex-wrap gap-2">
            {(Object.keys(GROUP_META) as GroupFilter[]).map(g => {
              const meta = GROUP_META[g]
              const active = groupFilter === g
              return (
                <button
                  key={g}
                  onClick={() => setGroupFilter(g)}
                  className={`inline-flex items-center gap-2 px-4 py-2 rounded-full font-body text-[13px] font-medium border transition-all ${
                    active
                      ? `${meta.badge} border-transparent shadow-sm`
                      : 'bg-white text-cool-grey border-light-grey hover:border-cool-grey/40'
                  }`}
                >
                  {g !== 'all' && (
                    <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: meta.dot }} />
                  )}
                  {meta.label}
                  {g !== 'all' && (
                    <span className="text-[11px] opacity-60">
                      {sectors.filter(s => NTEE_GROUP[s.code] === g).length}
                    </span>
                  )}
                </button>
              )
            })}
          </div>

          {/* Table */}
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="w-6 h-6 rounded-full border-2 border-soft-gold border-t-transparent animate-spin" />
            </div>
          ) : (
            <div className="overflow-x-auto" tabIndex={0} role="region" aria-label="Scrollable data table">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-light-grey">
                    <Th label="Sector" sortBy="name" tip="A broad category the IRS assigns to every 501(c)(3). Click a row to see the organizations in it." />
                    <Th label="Orgs" sortBy="total_orgs" right tip="How many active nonprofits the IRS recognizes in this category." />
                    <Th label="Low-reserve %" sortBy="at_risk_pct" right tip="Share of organizations showing fewer than 3 months of operating reserves in their most recent public filing. The 3-month threshold follows the Nonprofit Finance Fund standard for operating reserve adequacy. Filings may be 1 to 3 years old. This is an indicator from available data, not a judgment of organizational health." />
                    <Th label="Avg reserves (mo)" sortBy="avg_months_reserve" right tip="On average, how many months an organization in this category could keep operating if revenue stopped, among those with reserve data." />
                    <Th label="Avg program %" sortBy="avg_program_pct" right tip="On average, the share of spending that goes directly to programs and services." />
                  </tr>
                </thead>
                <tbody>
                  {sorted.map(sector => {
                    const stressed = sector.at_risk_pct >= 20
                    const elevated = !stressed && sector.at_risk_pct >= 15
                    const thinReserves = (sector.avg_months_reserve ?? 999) < 36
                    const sectorGroup = NTEE_GROUP[sector.code] ?? 'direct_service'
                    const groupMeta = GROUP_META[sectorGroup]
                    return (
                      <tr
                        key={sector.code}
                        role="link"
                        tabIndex={0}
                        onClick={() => navigate(`/directory?category=${sector.code}`)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault()
                            navigate(`/directory?category=${sector.code}`)
                          }
                        }}
                        aria-label={`See ${sector.name} organizations`}
                        title={`See ${sector.name} organizations`}
                        className={`group border-b border-light-grey/60 hover:bg-soft-gold/4 focus:outline-none focus-visible:ring-2 focus-visible:ring-soft-gold focus-visible:ring-inset transition-colors cursor-pointer ${groupMeta.bg}`}
                      >
                        <td className={`py-4 pr-6 ${groupMeta.border}`}>
                          <div className="flex items-center gap-3">
                            <div className="flex flex-col">
                              <div className="font-body text-[14px] font-medium text-deep-navy group-hover:text-soft-gold transition-colors inline-flex items-center gap-1.5">
                                {stressed && <span className="w-1.5 h-1.5 rounded-full bg-amber-500 flex-shrink-0" />}
                                {sector.name}
                                <span className="opacity-0 group-hover:opacity-100 transition-opacity text-soft-gold" aria-hidden="true">→</span>
                              </div>
                              <div className="flex items-center gap-2 mt-0.5">
                                <span className={`inline-flex items-center gap-1 font-body text-[10px] font-medium px-1.5 py-0.5 rounded-full ${groupMeta.badge}`}>
                                  <span className="w-1.5 h-1.5 rounded-full" style={{ background: groupMeta.dot }} />
                                  {groupMeta.label}
                                </span>
                                <span className="font-body text-[11px] text-cool-grey">{sector.total_orgs.toLocaleString()} total · {sector.has_reserve.toLocaleString()} with reserve data</span>
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="py-4 px-4 text-right">
                          <span className="font-body text-[14px] text-cool-grey">{sector.total_orgs.toLocaleString()}</span>
                        </td>
                        <td className="py-4 px-4 text-right">
                          <span className={`font-body text-[14px] font-semibold ${
                            stressed ? 'text-amber-600' : elevated ? 'text-amber-500' : 'text-cool-grey'
                          }`}>
                            {sector.at_risk_pct.toFixed(1)}%
                          </span>
                        </td>
                        <td className="py-4 px-4">
                          <div className="flex flex-col items-end gap-1.5 min-w-[120px]">
                            <span className={`font-body text-[14px] font-medium ${thinReserves ? 'text-amber-600' : 'text-cool-grey'}`}>
                              {formatMonths(sector.avg_months_reserve)} mo
                            </span>
                            <ReserveBar months={sector.avg_months_reserve} />
                          </div>
                        </td>
                        <td className="py-4 pl-4 text-right">
                          <span className="font-body text-[14px] text-cool-grey">
                            {sector.avg_program_pct !== null ? `${sector.avg_program_pct.toFixed(1)}%` : '—'}
                          </span>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Reserve breakdown legend */}
          <div className="mt-8 flex flex-wrap gap-4">
            {[
              { color: '#EF4444', label: 'Limited (<3 mo)' },
              { color: '#F59E0B', label: 'Moderate (3 to 12 mo)' },
              { color: '#4ADE80', label: 'Adequate (12 to 36 mo)' },
              { color: '#60A5FA', label: 'Strong (36+ mo)' },
            ].map(item => (
              <div key={item.label} className="flex items-center gap-2">
                <div className="w-3 h-1.5 rounded-full" style={{ background: item.color }} />
                <span className="font-body text-[12px] text-cool-grey">{item.label}</span>
              </div>
            ))}
          </div>

          {/* Methodology note */}
          <div className="mt-12 pt-8 border-t border-light-grey">
            <p className="font-body text-[13px] text-cool-grey leading-[1.6] max-w-[680px]">
              <strong className="text-cool-grey">How this is calculated.</strong> Reserves = (net assets ÷ total expenses) × 12. At-risk means fewer than 3 months of reserves. All data comes from IRS Form 990 filings for the most recent year on file. Only donation eligible 501(c)(3) organizations are included. Sector benchmarks reflect 356,000 organizations with complete filing data, approximately 21% of the 1.7 million donation eligible nonprofits Daanaa indexes. The remaining 79% file simplified returns or are exempt from filing; they are indexed and visible but not scored.
            </p>
            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2">
              <span className="inline-flex items-center gap-1.5 font-body text-[12px] text-cool-grey">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                IRS Statistics of Income · FY 2019–2024
              </span>
              <a
                href="https://projects.propublica.org/nonprofits/"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 font-body text-[12px] text-cool-grey hover:text-soft-gold transition-colors"
              >
                ProPublica Nonprofit Explorer
                <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15,3 21,3 21,9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
              </a>
              <span className="font-body text-[12px] text-cool-grey">NCCS</span>
            </div>
            <div className="mt-4 flex items-center gap-4">
              <Link to="/methodology" className="font-body text-[13px] text-soft-gold hover:text-bright-gold transition-colors">
                Full methodology →
              </Link>
              <Link to="/directory" className="font-body text-[13px] text-soft-gold hover:text-bright-gold transition-colors">
                Search organizations →
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
    </TooltipProvider>
  )
}
