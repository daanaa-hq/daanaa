import { Link } from 'react-router-dom'
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
  if (!v5?.archetype || !v5.score.health_signal) return null

  const style = SIGNAL_STYLE[v5.score.health_signal]
  const label = SIGNAL_LABEL[v5.score.health_signal]

  // Only show "Top X%" for healthy/stable orgs — for CAUTION orgs the
  // health badge is the signal; the percentile number creates a mixed message
  const showTopPct = v5.score.health_signal !== 'CAUTION'
  const topPct = Math.max(1, Math.round(100 - v5.score.percentile))

  const reserves = v5.benchmarks.reserves_months
  const hasOwnReserves = reserves.your_value !== null
  // Only show the peer bar when benchmark data is meaningful:
  // p75 must be non-zero AND the three benchmarks must not all be the same value
  // (flat benchmarks = data cap artifact, bar conveys no information)
  const hasPeerBench = reserves.p75 > 0 && !(reserves.p25 === reserves.p50 && reserves.p50 === reserves.p75)
  const barPct = (hasOwnReserves && hasPeerBench)
    ? Math.min(100, Math.round((reserves.your_value! / reserves.p75) * 100))
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

      {/* Key stat — percentile for healthy/stable; supportive note for CAUTION */}
      <div className="flex items-baseline gap-2 mb-5">
        {showTopPct ? (
          <>
            <span className={`font-display text-[32px] font-bold leading-none ${style.text}`}>
              Top {topPct}%
            </span>
            <span className="font-body text-[13px] text-cool-grey">of {v5.peer_group.label}</span>
          </>
        ) : (
          <p className={`font-body text-[14px] font-medium leading-snug ${style.text}`}>
            Compared to {v5.peer_group.org_count.toLocaleString()} similar organizations
          </p>
        )}
      </div>

      {/* Reserves bar — only when we have the org's own value and peer percentile data */}
      {hasOwnReserves && hasPeerBench && (
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
            <span>Low end: {Math.round(reserves.p25)} mo</span>
            <span>Typical: {Math.round(reserves.p50)} mo</span>
            <span>Strong: {Math.round(reserves.p75)} mo</span>
          </div>
        </div>
      )}
      {/* Show reserve value only (no bar) when peer benchmark data is unavailable */}
      {hasOwnReserves && !hasPeerBench && (
        <div className="mb-5 flex items-center justify-between">
          <span className="font-body text-[12px] font-medium text-deep-navy">Months of reserve</span>
          <span className={`font-body text-[13px] font-semibold ${style.text}`}>
            {Number.isInteger(reserves.your_value!) ? reserves.your_value! : reserves.your_value!.toFixed(1)} months
          </span>
        </div>
      )}

      {/* Donor explanation — clean precomputed text, reframe critical phrases */}
      <p className="font-body text-[14px] leading-relaxed text-deep-navy/80">
        {v5.donor_explanation
          .replace(/\b(\d+)\.0\b/g, '$1')
          .replace(/\s*This organization may be in a growth phase or operating lean by design\./g, '')
          .replace(/\bBelow the typical level for similar organizations\./g, 'Many nonprofits actively invest their resources into their work rather than building large reserves.')
          .replace(/\bBelow the typical level\b/g, 'investing actively in their mission')
          .replace(/\bThis organization is a ([A-Z])/g, (_, c) => `This is a ${c}`)
          .replace(/\ba ([A-Z][a-z-]+-[A-Z])/g, (_, w) => `an ${w}`)
          .replace(/\.\s*\./g, '.')
          .trim()
        }
      </p>
      {v5.score.health_signal === 'CAUTION' && (
        <p className="mt-3 font-body text-[13px] leading-relaxed text-deep-navy/60 italic">
          Nonprofits with fewer reserves are often putting most of their resources directly into their programs. Lower reserves don't reflect the quality or importance of their work.
        </p>
      )}

      {/* Disclosure + methodology link */}
      <div className="mt-4 border-t border-deep-navy/10 pt-3 flex items-center justify-between gap-4">
        <p className="font-body text-[11px] text-cool-grey italic">
          Context from public IRS data, compared to financially similar peers. Not a rating or recommendation.
        </p>
        <Link to="/methodology" className="shrink-0 font-body text-[11px] text-cool-grey hover:text-deep-navy underline underline-offset-2 transition-colors">
          How we score →
        </Link>
      </div>
    </div>
  )
}
