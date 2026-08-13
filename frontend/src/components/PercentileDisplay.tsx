import type { ApiOrganization } from '../data/api'

type DisplayVariant = 'hero' | 'metric' | 'detail'

interface PercentileDisplayProps {
  org: ApiOrganization
  variant?: DisplayVariant
}

const confidenceStyles = {
  HIGH: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  MEDIUM: 'border-blue-200 bg-blue-50 text-blue-800',
  LOW: 'border-amber-200 bg-amber-50 text-amber-800',
}

function confidenceLevel(confidence: string | null | undefined): 'HIGH' | 'MEDIUM' | 'LOW' | null {
  switch (confidence?.toLowerCase()) {
    case 'high':
      return 'HIGH'
    case 'good':
      return 'MEDIUM'
    case 'moderate':
    case 'archetype_only':
      return 'LOW'
    default:
      return null
  }
}

export default function PercentileDisplay({
  org,
  variant = 'detail',
}: PercentileDisplayProps) {
  // V6 percentile + confidence from peer context
  const percentile = org.peer_percentile
  const peerCount = org.peer_group_size
  const peerDescription = org.peer_group_description
  const confidence = confidenceLevel(org.confidence)
  const hasPercentile = typeof percentile === 'number' && percentile >= 0 && percentile <= 100
  const hasSmallPeerGroup = typeof peerCount === 'number' && peerCount < 5
  const topPercent = hasPercentile ? Math.max(1, 100 - Math.round(percentile)) : null

  if (!hasPercentile && !peerDescription && peerCount == null && !confidence) {
    return null
  }

  const peerSummary = peerDescription || 'Similar organizations'

  if (variant === 'metric') {
    return (
      <div className="min-w-0 p-6 bg-white border border-cool-grey/10 rounded-lg">
        <p className="text-label text-cool-grey/70 uppercase mb-3">Peer Context</p>
        {hasPercentile && !hasSmallPeerGroup ? (
          <p className="text-3xl sm:text-4xl font-bold text-primary-blue">
            Top {topPercent}%
          </p>
        ) : (
          <p className="text-lg font-semibold text-deep-navy">
            Percentile unavailable
          </p>
        )}
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {confidence && (
            <span className={`inline-flex rounded-full border px-2 py-1 text-xs font-semibold ${confidenceStyles[confidence]}`}>
              {confidence} confidence
            </span>
          )}
          {peerCount != null && !hasSmallPeerGroup && (
            <span className="text-xs text-cool-grey/60">
              {peerCount.toLocaleString()} peers
            </span>
          )}
        </div>
      </div>
    )
  }

  return (
    <section className={`min-w-0 rounded-xl border border-cool-grey/10 bg-white ${
      variant === 'hero' ? 'p-4 sm:p-5' : 'p-5 sm:p-6'
    }`}>
      <div className="flex flex-wrap items-center gap-2">
        <p className="font-semibold text-deep-navy">Peer context</p>
        {confidence && (
          <span className={`inline-flex rounded-full border px-2 py-1 text-xs font-semibold ${confidenceStyles[confidence]}`}>
            {confidence} confidence
          </span>
        )}
      </div>
      <div className="mt-3">
        <p className="text-sm text-cool-grey/70">{peerSummary}</p>
        {peerCount != null && (
          <p className="mt-1 text-xs text-cool-grey/60">
            Compared to {peerCount.toLocaleString()} organizations in this group
          </p>
        )}
        {hasSmallPeerGroup && (
          <p className="mt-2 text-xs text-amber-700 bg-amber-50 p-2 rounded">
            Limited peer data — this organization's context is based on a small comparison group.
          </p>
        )}
      </div>
    </section>
  )
}
