/**
 * FinancialTrends — real multi-year revenue history, when we have it.
 *
 * Rebuilt 2026-08-16. The previous version claimed "5-year history available"
 * unconditionally, with a placeholder instead of a real chart -- a real gap
 * between what was said and what was shown (see DECISIONS.md 2026-08-16).
 * This version only speaks to data it actually has: a plain chart backed by
 * org_revenue_history (migration 023), or nothing at all.
 *
 * No extra "we don't have this" notice when history is empty -- the rest of
 * the page (FinancialContext, DataContextNote) already covers data gaps
 * honestly; stacking another disclaimer here is exactly the pattern this
 * session removed elsewhere. Silence is the honest choice here.
 *
 * Interpretation copy is framed by the org's funding archetype (how it's
 * set up and funded), not a verdict on the number -- a donation-funded org's
 * year-to-year swing means something different than a fee-for-service org's.
 * Plain language throughout; no jargon, no shame framing (Stewardship P4/P5).
 */

import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from 'recharts'
import type { ApiOrganization } from '../data/api'

interface FinancialTrendsProps {
  org: ApiOrganization
}

const MIN_YEARS_FOR_CHART = 3

function formatShort(n: number): string {
  if (Math.abs(n) >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`
  if (Math.abs(n) >= 1_000) return `$${(n / 1_000).toFixed(0)}K`
  return `$${n.toFixed(0)}`
}

// One plain-language line, grounded in the actual numbers -- never invents
// a reason, just describes the shape and, when useful, adds a one-line note
// about how this type of organization is typically funded.
function describeShape(values: number[], archetypeLabel: string | null): string {
  const first = values[0]
  const last = values[values.length - 1]
  if (first <= 0) return 'Revenue over the years this organization has on file.'

  const change = (last - first) / first
  let shape: string
  if (change > 0.15) shape = 'Revenue has grown over this period.'
  else if (change < -0.15) shape = 'Revenue has come down over this period.'
  else shape = 'Revenue has stayed fairly steady over this period.'

  if (archetypeLabel === 'Donation-Funded Programs') {
    return `${shape} Donation-funded organizations often see swings year to year tied to major gifts and grants -- that's normal, not a warning sign.`
  }
  if (archetypeLabel === 'Fee-for-Service Operators') {
    return `${shape} This organization earns much of its revenue through fees for services, so its numbers tend to track program volume.`
  }
  if (archetypeLabel === 'Endowment-Funded Grantmakers') {
    return `${shape} Endowment-funded organizations' revenue often reflects investment performance as much as new giving.`
  }
  return shape
}

export default function FinancialTrends({ org }: FinancialTrendsProps) {
  const history = org.revenue_history ?? []
  const withRevenue = history.filter(h => h.total_revenue !== null && h.total_revenue > 0)

  if (withRevenue.length < MIN_YEARS_FOR_CHART) {
    return null
  }

  const chartData = withRevenue.map(h => ({
    year: String(h.tax_year),
    revenue: h.total_revenue as number,
  }))
  const values = chartData.map(d => d.revenue)
  const archetypeLabel = org.merit_archetype_v5_label ?? null
  const summary = describeShape(values, archetypeLabel)
  const yearsSpan = `${chartData[0].year}–${chartData[chartData.length - 1].year}`

  return (
    <div className="space-y-4">
      <div>
        <h3 className="font-display italic text-deep-navy text-title-sm mb-1">Revenue over time</h3>
        <p className="text-body text-cool-grey">{summary}</p>
      </div>

      <div className="bg-white border border-cool-grey/20 rounded-lg p-4" style={{ height: 220 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E0DB" />
            <XAxis dataKey="year" tick={{ fontSize: 12, fill: '#A0AFC3' }} axisLine={{ stroke: '#E5E0DB' }} tickLine={false} />
            <YAxis tickFormatter={formatShort} tick={{ fontSize: 12, fill: '#A0AFC3' }} axisLine={false} tickLine={false} width={56} />
            <Tooltip formatter={(v: number) => formatShort(v)} labelFormatter={(l) => `${l} revenue`} />
            <Bar dataKey="revenue" fill="#C9A96E" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <p className="text-xs text-cool-grey/70">
        {yearsSpan} · from this organization's IRS Form 990 filings.
      </p>
    </div>
  )
}
