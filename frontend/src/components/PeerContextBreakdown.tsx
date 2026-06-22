import type { ApiOrganization } from '../data/api'
import { getNteeLabel } from '../data/ntee'

interface ContextRow {
  dimension: string
  comparison: string
  rank?: { current: number; total: number }
  bracket?: string
}

// Convert percentile (0-100) to readable bracket
function percentileToBracket(percentile: number): string {
  if (percentile >= 75) return 'Top 25%'
  if (percentile >= 50) return 'Upper 50%'
  if (percentile >= 25) return 'Middle 50%'
  return 'Lower 25%'
}

// Convert rank/total to percentile, then to bracket
function rankToBracket(rank: number, total: number): string {
  if (total < 10) return 'small peer group'
  const percentile = (rank / total) * 100
  return percentileToBracket(percentile)
}

export default function PeerContextBreakdown({ org }: { org: ApiOrganization }) {
  const rows: ContextRow[] = []

  // 1. NTEE Category context
  if (org.NTEE1 && org.ntee1_total_orgs) {
    const nteeLabel = getNteeLabel(org.NTEE1)
    rows.push({
      dimension: '🏛️ Your Category',
      comparison: `${nteeLabel} organizations`,
      bracket: org.ntee1_percentile ? percentileToBracket(org.ntee1_percentile) : undefined,
    })
  }

  // 2. State context
  if (org.STATE && org.state_category_total && org.state_category_total > 1) {
    rows.push({
      dimension: '📍 Your State',
      comparison: `${org.STATE} orgs in your category`,
      rank: org.state_category_rank ? {
        current: org.state_category_rank,
        total: org.state_category_total || 0
      } : undefined,
    })
  }

  // 3. Revenue band context
  if ((org as any).v5_context?.band?.label) {
    const v5 = (org as any).v5_context
    rows.push({
      dimension: '💰 Your Size',
      comparison: `${v5.band.label} nonprofits nationally`,
      bracket: v5.score?.percentile ? percentileToBracket(v5.score.percentile) : undefined,
    })
  }

  // 4. Financial model context
  if ((org as any).v5_context?.archetype?.label) {
    const v5 = (org as any).v5_context
    const signal = v5.score?.health_signal
    const signalLabel = signal === 'HEALTHY' ? '✓ Financially healthy'
      : signal === 'STABLE' ? '◐ Financially stable'
      : '⚠ Needs support'

    rows.push({
      dimension: '🎯 Your Model',
      comparison: `${v5.archetype.label} nonprofits`,
      bracket: signalLabel,
    })
  }

  if (rows.length === 0) return null

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-6">
      <h3 className="font-display text-[18px] font-semibold text-deep-navy mb-5">
        Where You Stand
      </h3>

      <div className="space-y-4">
        {rows.map((row, i) => (
          <div key={i} className="flex items-start gap-4 pb-4 last:pb-0 last:border-b-0 border-b border-slate-100">
            <div className="flex-1 min-w-0">
              <p className="font-body text-[13px] font-semibold text-cool-grey mb-1">
                {row.dimension}
              </p>
              <p className="font-body text-[15px] text-deep-navy">
                {row.comparison}
              </p>
            </div>

            <div className="flex-shrink-0 text-right">
              {row.rank && (
                <div>
                  <p className="font-display text-[18px] font-bold text-soft-gold">
                    #{row.rank.current}
                  </p>
                  <p className="font-body text-[11px] text-cool-grey mt-0.5">
                    of {row.rank.total.toLocaleString()}
                  </p>
                </div>
              )}
              {row.bracket && (
                <div>
                  <p className="font-body text-[13px] font-semibold text-deep-navy">
                    {row.bracket}
                  </p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <p className="font-body text-[12px] text-cool-grey italic mt-6 pt-6 border-t border-slate-200">
        Peer context is based on public IRS data. This shows where you stand among similar organizations—not a judgment, just financial context.
      </p>
    </div>
  )
}
