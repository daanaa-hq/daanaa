import React from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { getOrganization } from '../data/api'
import type { ApiOrganization } from '../data/api'
import { getTierFromOrg, TIER_COLORS } from '../components/TrustBadge'
import LampMark from '../components/LampMark'
import { NTEE_CATEGORIES } from '../data/ntee'
import { formatEIN } from '../data/organizations'
import { getPrimaryExternalLink } from '../utils/externalLink'

function formatCurrency(n: number | null): string {
  if (!n) return '—'
  if (n >= 1_000_000_000) return `$${(n / 1_000_000_000).toFixed(1)}B`
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`
  return `$${n.toLocaleString()}`
}

// Turn an NTEECC subcategory code (e.g. "A82") into human words. Prefer the IRS
// description's specific part (after the "—", since Category already shows the
// major group), then an exact code match, then the raw code.
function subcategoryName(org: ApiOrganization): string {
  const code = org.NTEECC
  const desc = (org as { ntee_description?: string | null }).ntee_description
  if (desc) {
    const parts = desc.split('—')
    return parts[parts.length - 1].trim()
  }
  if (!code) return '—'
  for (const cat of NTEE_CATEGORIES) {
    const exact = cat.subs.find(s => s.code === code)
    if (exact) return exact.name
  }
  return code
}

// Colors for the peer Financial Health tier. Inspiring is framed as positive
// (remarkable work within constraints) — never a penalty.
const HEALTH_COLORS: Record<string, string> = {
  Strong: '#2F855A',
  Stable: '#B7791F',
  Inspiring: '#9C6BC9',
}

function rulingYear(ruling: string | null): string {
  if (!ruling) return '—'
  const m = ruling.match(/\d{4}/)
  return m ? m[0] : '—'
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
  const cat = NTEE_CATEGORIES.find(c => c.id === org.NTEE1)
  const health = org.financial_health
  const reserve = org.months_of_reserve
  const externalLink = (org.website_status === 'ok' || org.website_status === 'beta')
    ? getPrimaryExternalLink(org)
    : { url: null, label: null, type: null }

  const rows: { label: string; value: React.ReactNode }[] = [
    { label: 'EIN', value: formatEIN(org.EIN) },
    { label: 'Location', value: [org.CITY, org.STATE].filter(Boolean).join(', ') || '—' },
    { label: 'Category', value: cat?.name ?? org.NTEE1 ?? '—' },
    { label: 'Focus area', value: subcategoryName(org) },
    { label: 'Revenue', value: formatCurrency(org.total_revenue) },
    {
      label: 'Financial health',
      value: health ? (
        <span className="font-semibold" style={{ color: HEALTH_COLORS[health] }}>{health}</span>
      ) : (
        <span className="text-cool-grey font-normal">Not yet scored</span>
      ),
    },
    {
      label: 'Reserves',
      value: reserve == null ? '—'
        : reserve >= 120 ? '120+ mo'
        : `${reserve % 1 === 0 ? reserve.toFixed(0) : reserve.toFixed(1)} mo`,
    },
    {
      label: 'Visibility',
      value: (
        <span className="inline-flex items-center gap-1.5">
          <LampMark tier={lampTier} size="xs" />
          <span style={{ color: TIER_COLORS[lampTier] }}>{lampTier}</span>
        </span>
      ),
    },
    { label: 'Founded', value: rulingYear(org.ruling_date) },
    { label: 'Tax Year', value: org.latest_tax_year ? String(org.latest_tax_year) : '—' },
    { label: 'Data Source', value: org.data_source ?? '—' },
  ]

  return (
    <div className="flex-1 min-w-0">
      <Link to={`/org/${ein}`} className="block group mb-3">
        <h2 className="font-display text-[18px] text-deep-navy group-hover:text-soft-gold transition-colors leading-snug">
          {org.organization_name}
        </h2>
        <p className="font-body text-[13px] text-cool-grey mt-1">
          {[org.CITY, org.STATE].filter(Boolean).join(', ')}
        </p>
      </Link>

      {org.mission && (
        <div className="mb-5">
          <p className="font-body text-[12.5px] text-cool-grey/90 leading-[1.5] line-clamp-3">
            {org.mission.replace(/^[“"\s]+|[”"\s]+$/g, '')}
          </p>
          {(org.mission_source || '').startsWith('ai') && (
            <span
              className="mt-1.5 inline-flex items-center gap-1 text-[10px] font-body text-cool-grey/55"
              title="AI-generated from public records — not confirmed by the organization"
            >
              <span className="w-1 h-1 rounded-full bg-cool-grey/40" />
              AI generated
            </span>
          )}
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

      {/* Single official external link — the org's own website when we have it */}
      {externalLink.url && (
        <div className="mt-5 flex flex-wrap gap-2">
          <a
            href={externalLink.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 min-w-[100px] py-2.5 rounded-full bg-soft-gold text-deep-navy font-body text-[13px] font-semibold text-center hover:bg-bright-gold transition-colors"
          >
            {externalLink.label} ↗
          </a>
        </div>
      )}

      <Link
        to={`/org/${ein}`}
        className="mt-2.5 block w-full py-2.5 rounded-full border border-light-grey text-cool-grey font-body text-[13px] font-semibold text-center hover:border-soft-gold/40 hover:text-soft-gold transition-colors"
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
