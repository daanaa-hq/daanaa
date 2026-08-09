import { useEffect, useState } from 'react'
import { loadResearchSnapshot } from '../../data/researchSnapshot'

interface ResearchFinancialArchetypesProps {
  sessionToken: string
  metadata: any
}

const TIER_COLORS: Record<string, string> = {
  '1_Full_Context': '#10B981',
  '2_Regional_Context': '#D4B968',
  '3_Broad_Category': '#8B7355',
  '4_Archetype_Only': '#C9BBA3',
}

function formatPercent(value: number | null): string {
  if (value === null || value === undefined) return '—'
  return `${value.toFixed(1)}%`
}

function formatMonths(value: number | null): string {
  if (value === null || value === undefined) return '—'
  return `${value.toFixed(1)}mo`
}

export default function ResearchFinancialArchetypes({
  sessionToken,
  metadata,
}: ResearchFinancialArchetypesProps) {
  const [v6Data, setV6Data] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadResearchSnapshot()
      .then((snap) => setV6Data(snap.v6 ?? null))
      .catch((error) => console.error('Failed to load v6 data:', error))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div>
        <h2 className="text-3xl font-display text-deep-navy mb-6">
          Peer Context Coverage
        </h2>
        <p className="text-sm text-cool-grey">Loading…</p>
      </div>
    )
  }

  if (!v6Data) {
    return (
      <div>
        <h2 className="text-3xl font-display text-deep-navy mb-6">
          Peer Context Coverage
        </h2>
        <p className="text-sm text-cool-grey">Data not available.</p>
      </div>
    )
  }

  const tiers = v6Data.tiers || []
  const totalActive = v6Data.total_active || 0
  const totalPlaced = v6Data.total_placed || 0
  const placementCoveragePct = v6Data.placement_coverage_pct ?? 0

  return (
    <div>
      <h2 className="text-3xl font-display text-deep-navy mb-4">
        Peer Context Coverage
      </h2>
      <p className="text-lg text-cool-grey mb-6 max-w-2xl">
        Every organization is placed into a context tier that says how specific its peer
        comparison is. When there isn't enough data for a tight comparison, the group widens
        one step at a time: drop region, then drop revenue band. This is the reference-class
        approach: use the narrowest comparable set with enough data, and widen it only when
        there isn't enough.
      </p>

      {/* Coverage summary */}
      <div className="mb-12 bg-soft-gold/10 border border-soft-gold/20 rounded-lg p-5 max-w-2xl">
        <p className="text-sm text-deep-navy">
          <span className="font-display text-2xl text-deep-navy mr-2">{placementCoveragePct}%</span>
          of the {totalActive.toLocaleString()} active, tax-deductible organizations we track
          are placed into one of the four tiers below ({totalPlaced.toLocaleString()} orgs).
          The rest ({(totalActive - totalPlaced).toLocaleString()}) are missing the category or
          location data a tier assignment needs. Three of the four tiers include an actual peer
          comparison; the fourth, Archetype Only, does not.
        </p>
      </div>

      {/* Tier composition */}
      <div className="mb-12">
        <h3 className="text-xl font-semibold text-deep-navy mb-4">How the tiers break down</h3>

        <div className="flex h-3 w-full max-w-2xl overflow-hidden rounded-full mb-6 border border-light-grey">
          {tiers.map((t: any) => (
            <div
              key={t.key}
              style={{ width: `${t.pct}%`, backgroundColor: TIER_COLORS[t.key] || 'rgb(var(--cool-grey-rgb))' }}
              title={`${t.name}: ${t.pct}%`}
            />
          ))}
        </div>

        <div className="space-y-6 max-w-2xl">
          {tiers.map((t: any) => (
            <div key={t.key}>
              <div className="flex items-baseline gap-3 mb-2">
                <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: TIER_COLORS[t.key] }} />
                <span className="font-display text-2xl text-deep-navy">{t.pct}%</span>
                <span className="text-sm font-medium text-deep-navy">{t.name}</span>
                <span className="text-xs text-cool-grey">({t.count.toLocaleString()})</span>
              </div>
              <p className="text-sm text-slate ml-6 leading-relaxed max-w-xl">
                {t.description}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Tier stats table */}
      <div className="mb-12">
        <h3 className="text-xl font-semibold text-deep-navy mb-4">Tier averages</h3>
        <p className="text-sm text-cool-grey mb-6">
          These are descriptive averages of what organizations in each tier actually report, not
          a score. Daanaa does not compute a percentile ranking within V6 tiers; the tier itself
          says how specific the comparison is, and reserves and program spending are shown as
          reference points.
        </p>

        <div className="overflow-x-auto" tabIndex={0} role="region" aria-label="Scrollable data table">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-light-grey bg-deep-navy/[0.02]">
                <th className="text-left px-4 py-3 font-semibold text-deep-navy">Context tier</th>
                <th className="text-right px-4 py-3 font-semibold text-deep-navy">Count</th>
                <th className="text-right px-4 py-3 font-semibold text-cool-grey">Peer comparison</th>
                <th className="text-right px-4 py-3 font-semibold text-cool-grey">Avg peer group size</th>
                <th className="text-right px-4 py-3 font-semibold text-cool-grey">Avg program %</th>
                <th className="text-right px-4 py-3 font-semibold text-cool-grey">Avg reserves</th>
              </tr>
            </thead>
            <tbody>
              {tiers.map((t: any) => (
                <tr key={t.key} className="border-b border-light-grey hover:bg-deep-navy/[0.02]">
                  <td className="px-4 py-3 text-deep-navy font-medium">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: TIER_COLORS[t.key] }} />
                      <span>{t.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-deep-navy">
                    {t.count.toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-right text-cool-grey">
                    {t.has_peer_comparison ? 'Yes' : 'No'}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-cool-grey">
                    {t.avg_peer_group_size ? Math.round(t.avg_peer_group_size).toLocaleString() : '—'}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-cool-grey">
                    {formatPercent(t.avg_program_pct)}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-cool-grey">
                    {formatMonths(t.avg_months_reserve)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-warm-cream/40 border border-soft-gold/30 rounded-lg p-5 max-w-2xl">
        <p className="text-sm text-deep-navy font-semibold mb-2">A note on how to use this</p>
        <p className="text-sm text-slate leading-relaxed">
          Financial context is a starting point, not a score card. A lower reserves number can
          mean many things: rapid growth, recent investment in programs, a community that depends
          heavily on the organization, or simply that unrestricted funding is hard to come by.
          Daanaa does not recommend giving to some organizations over others. We provide
          context so donors can ask better questions and give with more confidence, wherever
          they choose to give.
        </p>
      </div>
    </div>
  )
}
