import { useState } from 'react'
import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { useApi } from '../hooks/useApi'
import { getSectorHealth } from '../data/api'
import type { ApiSectorHealth } from '../data/api'

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
    'Sector Financial Health',
    'Financial health across all 26 nonprofit sectors. Reserve levels, at risk rates, and program spending for 430,000+ organizations the IRS recognizes.'
  )

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

  const Th = ({ label, sortBy, right }: { label: string; sortBy: SortKey; right?: boolean }) => (
    <th
      className={`text-[11px] font-medium tracking-[0.06em] text-cool-grey uppercase pb-3 cursor-pointer hover:text-deep-navy select-none ${right ? 'text-right' : 'text-left'}`}
      onClick={() => handleSort(sortBy)}
    >
      {label}
      <SortIcon active={sortKey === sortBy} asc={sortAsc} />
    </th>
  )

  return (
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
            A financial health picture of {totalOrgs.toLocaleString()} nonprofits the IRS recognizes, across 26 sectors. Reserve levels, at risk rates, and program spending.
          </p>

          {/* Key stat chips */}
          <div className="mt-10 flex flex-wrap gap-4">
            {[
              { value: `${Math.round(totalAtRisk / 1000)}K`, label: 'organizations under financial stress', color: '#F59E0B' },
              { value: `${Math.round(totalAtRisk / totalOrgs * 100)}%`, label: 'of all nonprofits financially at risk', color: '#F59E0B' },
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
              By contrast, Philanthropy (110 months avg) and Mutual Benefit (113 months avg) sectors hold the deepest reserves —
              reflecting endowment-funded models rather than direct-service delivery.
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
                    <Th label="Sector" sortBy="name" />
                    <Th label="Orgs" sortBy="total_orgs" right />
                    <Th label="At risk %" sortBy="at_risk_pct" right />
                    <Th label="Avg reserves (mo)" sortBy="avg_months_reserve" right />
                    <Th label="Avg program %" sortBy="avg_program_pct" right />
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
                        className={`border-b border-light-grey/60 hover:bg-soft-gold/4 transition-colors ${
                          stressed ? 'bg-amber-50/60' : elevated ? 'bg-amber-50/30' : ''
                        }`}
                      >
                        <td className="py-4 pr-6">
                          <div className="flex items-center gap-2">
                            {stressed && (
                              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 flex-shrink-0" />
                            )}
                            <div>
                              <div className="font-body text-[14px] font-medium text-deep-navy">{sector.name}</div>
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
              <strong className="text-cool-grey">Methodology note.</strong> Reserve data available for 84% of organizations using months of reserves = (net assets ÷ total expenses) × 12, the Charity Navigator-aligned working capital metric.
              At-risk = fewer than 3 months of operating reserves (insolvent + less than 3 months).
              Average program expense % may be lower for sectors with many pass-through or foundation-style organizations.
              Data sourced from IRS Statistics of Income (FY 2019–2024), ProPublica Nonprofit Explorer, and NCCS.
            </p>
            <div className="mt-4 flex items-center gap-4">
              <Link to="/methodology" className="font-body text-[13px] text-soft-gold hover:text-bright-gold transition-colors">
                Read the full methodology →
              </Link>
              <Link to="/directory" className="font-body text-[13px] text-soft-gold hover:text-bright-gold transition-colors">
                Search organizations →
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
