import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { useApi } from '../hooks/useApi'
import { getSectorHealth } from '../data/api'
import type { ApiSectorHealth } from '../data/api'
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '../components/ui/tooltip'

type SortKey = 'name' | 'total_orgs' | 'at_risk_pct' | 'avg_months_reserve' | 'avg_program_pct'

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
    'What public filings suggest about the sector',
    'A look at available public financial filings across 26 nonprofit sectors. Reserve levels, filing rates, and program spending for 1.6 million+ organizations the IRS recognizes.'
  )

  const navigate = useNavigate()
  const { data, loading } = useApi(() => getSectorHealth(), [])
  const [sortKey, setSortKey] = useState<SortKey>('at_risk_pct')
  const [sortAsc, setSortAsc] = useState(false)

  const sectors: ApiSectorHealth[] = data?.sectors ?? []

  const sorted = [...sectors].sort((a, b) => {
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
              <button type="button" aria-label={`What ${label} means`} className="text-cool-grey/50 hover:text-soft-gold transition-colors leading-none">
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
            <span className="text-muted-cream/50">/</span>
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
            A look at available public financial filings across 26 sectors. Many small or simplified filers do not report detailed financials, so this view reflects patterns in available data, not a complete picture of every group.
          </p>

          {/* Key stat chips */}
          <div className="mt-10 flex flex-wrap gap-4">
            {[
              { value: `${Math.round(totalAtRisk / 1000)}K`, label: 'organizations with limited reserve cushion in public filings', color: '#F59E0B' },
              { value: `${Math.round(totalAtRisk / totalOrgs * 100)}%`, label: 'of all nonprofits with limited savings', color: '#F59E0B' },
              { value: '84%', label: 'of all orgs have reserve data', color: '#60A5FA' },
            ].map(stat => (
              <div key={stat.label} className="flex items-baseline gap-2 px-4 py-3 rounded-xl bg-white/5 border border-white/10">
                <span className="font-display text-[28px] font-medium" style={{ color: stat.color }}>{stat.value}</span>
                <span className="font-body text-[13px] text-muted-cream/60">{stat.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="bg-warm-cream">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 py-16">

          {/* Lead finding */}
          <div className="mb-12 p-6 rounded-2xl bg-amber-50 border border-amber-200/80">
            <p className="font-body text-[15px] text-deep-navy leading-[1.7]">
              <strong>The sectors doing the most critical social safety-net work carry the least financial cushion.</strong>{' '}
              Housing & Shelter has the highest at risk rate of any sector. Nearly 1 in 3 organizations operates with fewer than 3 months of reserves.
              Mental Health has the lowest average reserves of any major sector at just 27.8 months,
              while Human Services, the largest sector by organization count, has 18% of its organizations at risk.
            </p>
            <p className="mt-3 font-body text-[13px] text-cool-grey">
              By contrast, Philanthropy (110 months avg) and Mutual Benefit (113 months avg) sectors hold the largest savings,
              reflecting long-term investment fund support rather than hands-on community delivery.
            </p>
          </div>

          {/* Table */}
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="w-6 h-6 rounded-full border-2 border-soft-gold border-t-transparent animate-spin" />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-light-grey">
                    <Th label="Sector" sortBy="name" tip="A broad category the IRS assigns to every nonprofit. Click a row to see the organizations in it." />
                    <Th label="Orgs" sortBy="total_orgs" right tip="How many active nonprofits the IRS recognizes in this category." />
                    <Th label="At risk %" sortBy="at_risk_pct" right tip="Share of organizations with fewer than 3 months of savings if revenue stopped. Based on the most recent 990 on file, which may be 1 to 3 years old." />
                    <Th label="Avg reserves (mo)" sortBy="avg_months_reserve" right tip="On average, how many months an organization in this category could keep operating if revenue stopped, among those with reserve data." />
                    <Th label="Avg program %" sortBy="avg_program_pct" right tip="On average, the share of spending that goes directly to the mission rather than overhead." />
                  </tr>
                </thead>
                <tbody>
                  {sorted.map(sector => {
                    const stressed = sector.at_risk_pct >= 20
                    const elevated = !stressed && sector.at_risk_pct >= 15
                    const thinReserves = (sector.avg_months_reserve ?? 999) < 36
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
                        className={`group border-b border-light-grey/60 hover:bg-soft-gold/4 focus:outline-none focus-visible:ring-2 focus-visible:ring-soft-gold focus-visible:ring-inset transition-colors cursor-pointer ${
                          stressed ? 'bg-amber-50/60' : elevated ? 'bg-amber-50/30' : ''
                        }`}
                      >
                        <td className="py-4 pr-6">
                          <div className="flex items-center gap-2">
                            {stressed && (
                              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 flex-shrink-0" />
                            )}
                            <div>
                              <div className="font-body text-[14px] font-medium text-deep-navy group-hover:text-soft-gold transition-colors inline-flex items-center gap-1.5">
                                {sector.name}
                                <span className="opacity-0 group-hover:opacity-100 transition-opacity text-soft-gold" aria-hidden="true">→</span>
                              </div>
                              <div className="font-body text-[11px] text-cool-grey/60 mt-0.5">{sector.total_orgs.toLocaleString()} total · {sector.has_reserve.toLocaleString()} with reserve data</div>
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
              { color: '#EF4444', label: 'Critical (<3 mo)' },
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
            <p className="font-body text-[13px] text-cool-grey/70 leading-[1.6] max-w-[680px]">
              <strong className="text-cool-grey">How this is calculated.</strong> Reserves = (net assets ÷ total expenses) × 12, the same formula Charity Navigator uses.
              At-risk means fewer than 3 months of reserves. Average program % may be lower for sectors with many pass-through or foundation-style organizations.
            </p>
            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2">
              <span className="inline-flex items-center gap-1.5 font-body text-[12px] text-cool-grey/60">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                IRS Statistics of Income · FY 2019–2024
              </span>
              <a
                href="https://projects.propublica.org/nonprofits/"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 font-body text-[12px] text-cool-grey/60 hover:text-soft-gold transition-colors"
              >
                ProPublica Nonprofit Explorer
                <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15,3 21,3 21,9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
              </a>
              <span className="font-body text-[12px] text-cool-grey/60">NCCS</span>
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
