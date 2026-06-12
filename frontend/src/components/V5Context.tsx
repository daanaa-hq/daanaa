import type { ApiOrganization } from '../data/api'
import V5FeedbackForm from './V5FeedbackForm'

interface V5ContextData {
  archetype: {
    key: string
    label: string
  }
  band: {
    key: string
    label: string
  }
  peer_group: {
    label: string
    org_count: number
  }
  score: {
    percentile: number
    health_signal: 'HEALTHY' | 'STABLE' | 'CAUTION'
  }
  benchmarks: {
    reserves_months: {
      p25: number
      p50: number
      p75: number
      your_value: number | null
    }
    healthy_rate_peer: number
  }
  donor_explanation: string
}

interface V5ContextProps {
  org: ApiOrganization
}

export default function V5Context({ org }: V5ContextProps) {
  const v5 = (org as any).v5_context as V5ContextData | null
  if (!v5 || !v5.archetype) return null

  const healthColor = {
    'HEALTHY': { text: 'text-green-700', bg: 'bg-green-50', badge: 'bg-green-100 text-green-700' },
    'STABLE': { text: 'text-blue-700', bg: 'bg-blue-50', badge: 'bg-blue-100 text-blue-700' },
    'CAUTION': { text: 'text-amber-700', bg: 'bg-amber-50', badge: 'bg-amber-100 text-amber-700' },
  }

  const colors = healthColor[v5.score.health_signal]

  return (
    <div className={`rounded-lg border p-6 ${colors.bg}`}>
      <div className="space-y-5">
        {/* Header with beta badge */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="font-body text-xs tracking-widest uppercase font-semibold opacity-70">
              Financial Context (Beta)
            </h3>
            <p className={`font-body text-lg font-semibold mt-2 ${colors.text}`}>
              {v5.archetype.label}
            </p>
          </div>
          <span className={`inline-block px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap ${colors.badge}`}>
            {v5.score.health_signal}
          </span>
        </div>

        {/* Peer group info */}
        <div className="space-y-2">
          <div className="text-sm">
            <span className="opacity-70">Compared to </span>
            <span className="font-semibold">{v5.peer_group.label}</span>
            <span className="opacity-70"> ({v5.peer_group.org_count.toLocaleString()} organizations)</span>
          </div>
        </div>

        {/* Percentile rank */}
        <div className="grid grid-cols-2 gap-6">
          <div className="text-center">
            <span className="block text-xs opacity-60 mb-1.5">Percentile Rank</span>
            <span className={`block font-body text-3xl font-bold ${colors.text}`}>
              {v5.score.percentile}
            </span>
            <span className="text-xs opacity-60">among similar orgs</span>
          </div>
          <div className="text-center">
            <span className="block text-xs opacity-60 mb-1.5">Peer Typical</span>
            <span className={`block font-body text-3xl font-bold ${colors.text}`}>
              {v5.benchmarks.reserves_months.p50.toFixed(0)}
            </span>
            <span className="text-xs opacity-60">months reserve</span>
          </div>
        </div>

        {/* Reserve comparison if available */}
        {v5.benchmarks.reserves_months.your_value !== null && (
          <div className="pt-3 space-y-2">
            <div className="text-xs opacity-70">Your organization: <span className="font-semibold">{v5.benchmarks.reserves_months.your_value.toFixed(1)} months</span></div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${colors.badge.split(' ')[0]}`}
                style={{
                  width: `${Math.min(100, (v5.benchmarks.reserves_months.your_value / v5.benchmarks.reserves_months.p75) * 100)}%`
                }}
              />
            </div>
            <div className="flex justify-between text-xs opacity-60">
              <span>P25: {v5.benchmarks.reserves_months.p25.toFixed(0)}</span>
              <span>P50: {v5.benchmarks.reserves_months.p50.toFixed(0)}</span>
              <span>P75: {v5.benchmarks.reserves_months.p75.toFixed(0)}</span>
            </div>
          </div>
        )}

        {/* Donor explanation */}
        <p className={`font-body text-sm leading-relaxed ${colors.text}`}>
          {v5.donor_explanation}
        </p>

        {/* Beta note */}
        <div className="pt-3 border-t border-current/20">
          <p className="text-xs opacity-70 italic">
            This is a new peer-based financial comparison system. We're testing it with a small group and would appreciate your feedback.
          </p>
        </div>
      </div>

      {/* Feedback form */}
      <div className="mt-6">
        <V5FeedbackForm org={org} archetype={v5.archetype.label} />
      </div>
    </div>
  )
}
