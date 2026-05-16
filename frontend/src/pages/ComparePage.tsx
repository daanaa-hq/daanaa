import React from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { getOrganization } from '../data/api'
import type { ApiOrganization } from '../data/api'
import { getTierFromOrg, TIER_COLORS } from '../components/TrustBadge'
import LampMark from '../components/LampMark'
import { NTEE_CATEGORIES } from '../data/ntee'

function formatCurrency(n: number | null): string {
  if (!n) return '—'
  if (n >= 1_000_000_000) return `$${(n / 1_000_000_000).toFixed(1)}B`
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`
  return `$${n.toLocaleString()}`
}

function ScoreGauge({ score, size = 80 }: { score: number; size?: number }) {
  const r = (size / 2) - 6
  const circ = 2 * Math.PI * r
  const fill = (score / 100) * circ
  const color = score >= 75 ? '#4ADE80' : score >= 50 ? '#C9A96E' : score >= 25 ? '#F59E0B' : '#6B7280'

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#E5E0DB" strokeWidth="5" />
        <circle
          cx={size/2} cy={size/2} r={r}
          fill="none" stroke={color} strokeWidth="5"
          strokeDasharray={`${fill} ${circ}`}
          strokeLinecap="round"
          transform={`rotate(-90 ${size/2} ${size/2})`}
        />
        <text x={size/2} y={size/2 + 1} textAnchor="middle" dominantBaseline="middle" fontSize="16" fontWeight="700" fill="#0A1628">
          {score}
        </text>
      </svg>
      <span className="font-body text-[10px] text-cool-grey uppercase tracking-[0.05em]">MERIT Score</span>
    </div>
  )
}

function OrgColumn({ ein }: { ein: string }) {
  const { data: org, loading, error } = useApi(() => getOrganization(ein), [ein])

  if (loading) {
    return (
      <div className="flex-1 min-w-0 animate-pulse">
        <div className="h-6 w-3/4 bg-light-grey rounded mb-3" />
        <div className="h-4 w-1/2 bg-light-grey rounded mb-6" />
        <div className="h-20 bg-light-grey rounded-xl mb-4" />
        <div className="space-y-2">
          {[1,2,3,4].map(i => <div key={i} className="h-10 bg-light-grey rounded-lg" />)}
        </div>
      </div>
    )
  }

  if (error || !org) {
    return (
      <div className="flex-1 min-w-0 text-center py-8">
        <p className="font-body text-[14px] text-cool-grey">Failed to load org</p>
      </div>
    )
  }

  const lampTier = getTierFromOrg(org)
  const score = Math.round(org.peer_percentile ?? org.ntee1_percentile ?? 0)
  const hasScore = (org.data_source === 'propublica' || org.data_source === 'irs_soi') && score > 0
  const cat = NTEE_CATEGORIES.find(c => c.id === org.NTEE1)

  const rows: { label: string; value: React.ReactNode }[] = [
    { label: 'EIN', value: org.EIN },
    { label: 'Location', value: [org.CITY, org.STATE].filter(Boolean).join(', ') || '—' },
    { label: 'Category', value: cat?.name ?? org.NTEE1 ?? '—' },
    { label: 'Subcategory', value: org.NTEECC ?? '—' },
    { label: 'Revenue', value: formatCurrency(org.total_revenue) },
    {
      label: 'Trust tier',
      value: (
        <span className="inline-flex items-center gap-1.5">
          <LampMark tier={lampTier} size="xs" />
          <span style={{ color: TIER_COLORS[lampTier] }}>{lampTier}</span>
        </span>
      ),
    },
    { label: 'Tax Year', value: org.latest_tax_year ? String(org.latest_tax_year) : '—' },
    { label: 'Data Source', value: org.data_source ?? '—' },
  ]

  return (
    <div className="flex-1 min-w-0">
      <Link to={`/organization/${ein}`} className="block group mb-5">
        <h2 className="font-display text-[18px] text-deep-navy group-hover:text-soft-gold transition-colors leading-snug">
          {org.organization_name}
        </h2>
        <p className="font-body text-[13px] text-cool-grey mt-1">
          {[org.CITY, org.STATE].filter(Boolean).join(', ')}
        </p>
      </Link>

      {hasScore && (
        <div className="flex justify-center mb-6">
          <ScoreGauge score={score} />
        </div>
      )}

      <div className="space-y-2">
        {rows.map(row => (
          <div key={row.label} className="flex items-start justify-between gap-3 py-2.5 border-b border-light-grey last:border-0">
            <span className="font-body text-[12px] text-cool-grey shrink-0">{row.label}</span>
            <span className="font-body text-[13px] text-deep-navy font-medium text-right">{row.value}</span>
          </div>
        ))}
      </div>

      <Link
        to={`/organization/${ein}`}
        className="mt-5 block w-full py-2.5 rounded-full border border-soft-gold/40 text-soft-gold font-body text-[13px] font-semibold text-center hover:bg-soft-gold/10 transition-colors"
      >
        View full profile →
      </Link>
    </div>
  )
}

export default function ComparePage() {
  const [searchParams] = useSearchParams()
  const einsParam = searchParams.get('eins') || ''
  const eins = einsParam.split(',').filter(Boolean).slice(0, 4)

  if (eins.length < 2) {
    return (
      <div className="min-h-[100dvh] pt-[72px] flex flex-col items-center justify-center bg-warm-cream px-6">
        <p className="font-body text-[16px] text-cool-grey">Select at least 2 nonprofits to compare.</p>
        <Link to="/directory" className="mt-4 font-body text-[14px] text-soft-gold hover:text-bright-gold transition-colors">
          ← Back to Directory
        </Link>
      </div>
    )
  }

  return (
    <div className="min-h-[100dvh] pt-[72px] bg-warm-cream">
      {/* Header */}
      <div className="bg-white border-b border-light-grey px-6 lg:px-12 py-8">
        <div className="max-w-[1200px] mx-auto">
          <Link to="/directory" className="font-body text-[12px] text-cool-grey hover:text-deep-navy transition-colors inline-flex items-center gap-1">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="15 18 9 12 15 6"/>
            </svg>
            Back to Directory
          </Link>
          <h1 className="font-display italic text-deep-navy mt-3" style={{ fontSize: 'clamp(26px, 4vw, 40px)' }}>
            Compare Nonprofits
          </h1>
          <p className="mt-2 font-body text-[14px] text-cool-grey">
            Side-by-side comparison of {eins.length} organizations
          </p>
        </div>
      </div>

      {/* Comparison grid */}
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12 py-10">
        <div className="flex gap-6 md:gap-8 overflow-x-auto">
          {eins.map(ein => (
            <div key={ein} className="min-w-[260px] flex-1 bg-white rounded-2xl border border-light-grey p-6">
              <OrgColumn ein={ein} />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
