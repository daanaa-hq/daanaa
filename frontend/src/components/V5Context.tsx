import type { ApiOrganization } from '../data/api'

interface V5ContextData {
  archetype: { key: string; label: string }
  band: { key: string; label: string }
  peer_group: { label: string; org_count: number }
  score: { percentile: number; health_signal: 'HEALTHY' | 'STABLE' | 'CAUTION' }
  benchmarks: {
    reserves_months: { p25: number; p50: number; p75: number; your_value: number | null }
    healthy_rate_peer: number
  }
  donor_explanation: string
}

const SIGNAL_STYLE = {
  HEALTHY: { border: 'border-emerald-200', bg: 'bg-emerald-50', badge: 'bg-emerald-100 text-emerald-800 border-emerald-200', bar: 'bg-emerald-400', text: 'text-emerald-700' },
  STABLE:  { border: 'border-blue-200',    bg: 'bg-blue-50',    badge: 'bg-blue-100 text-blue-800 border-blue-200',           bar: 'bg-blue-400',    text: 'text-blue-700'   },
  CAUTION: { border: 'border-amber-200',   bg: 'bg-amber-50',   badge: 'bg-amber-100 text-amber-800 border-amber-200',         bar: 'bg-amber-400',   text: 'text-amber-700'  },
} as const

const SIGNAL_LABEL = {
  HEALTHY: 'Financially healthy',
  STABLE:  'Financially stable',
  CAUTION: 'Needs support',
} as const

export default function V5Context({ org }: { org: ApiOrganization }) {
  const v5 = (org as any).v5_context as V5ContextData | null
  if (!v5?.archetype) return null

  const style = SIGNAL_STYLE[v5.score.health_signal]
  const label = SIGNAL_LABEL[v5.score.health_signal]

  // "Top X% of peers" is more intuitive than a raw percentile number
  const topPct = Math.max(1, Math.round(100 - v5.score.percentile))

  const reserves = v5.benchmarks.reserves_months
  const hasOwnReserves = reserves.your_value !== null
  const barPct = hasOwnReserves
    ? Math.min(100, Math.round((reserves.your_value! / Math.max(reserves.p75, 1)) * 100))
    : 0

  return (
    <div className={`rounded-xl border ${style.border} ${style.bg} p-6`}>
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-5">
        <div>
          <p className="font-body text-[11px] font-semibold tracking-[0.08em] text-cool-grey uppercase mb-1">
            Financial Context
          </p>
          <p className="font-body text-[16px] font-semibold text-deep-navy leading-snug">
            {v5.archetype.label}
          </p>
          <p className="font-body text-[12px] text-cool-grey mt-0.5">
            Compared to {v5.peer_group.org_count.toLocaleString()} similar organizations
          </p>
        </div>
        <span className={`shrink-0 inline-flex items-center px-3 py-1 rounded-full text-[12px] font-semibold border ${style.badge}`}>
          {label}
        </span>
      </div>

      {/* Key stat */}
      <div className="flex items-baseline gap-2 mb-5">
        <span className={`font-display text-[32px] font-bold leading-none ${style.text}`}>
          Top {topPct}%
        </span>
        <span className="font-body text-[13px] text-cool-grey">of {v5.peer_group.label}</span>
      </div>

      {/* Reserves bar — only when we have the org's own value */}
      {hasOwnReserves && (
        <div className="mb-5">
          <div className="flex items-center justify-between mb-1.5">
            <span className="font-body text-[12px] font-medium text-deep-navy">Months of reserve</span>
            <span className={`font-body text-[13px] font-semibold ${style.text}`}>
              {Number.isInteger(reserves.your_value!) ? reserves.your_value! : reserves.your_value!.toFixed(1)} months
            </span>
          </div>
          <div className="w-full bg-deep-navy/8 rounded-full h-2 mb-1.5">
            <div className={`h-2 rounded-full ${style.bar}`} style={{ width: `${barPct}%` }} />
          </div>
          <div className="flex justify-between font-body text-[11px] text-cool-grey">
            <span>Typical low: {Math.round(reserves.p25)} mo</span>
            <span>Typical: {Math.round(reserves.p50)} mo</span>
            <span>Strong: {Math.round(reserves.p75)} mo</span>
          </div>
        </div>
      )}

      {/* Donor explanation */}
      <p className="font-body text-[14px] leading-relaxed text-deep-navy/80">
        {v5.donor_explanation.replace(/\b(\d+)\.0\b/g, '$1')}
      </p>

      {/* Disclosure */}
      <p className="mt-4 font-body text-[11px] text-cool-grey italic border-t border-deep-navy/10 pt-3">
        Context from public IRS data, compared to financially similar peers. Not a rating or recommendation.
      </p>
    </div>
  )
}
