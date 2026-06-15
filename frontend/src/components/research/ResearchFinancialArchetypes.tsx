import { useEffect, useState } from 'react'
import { loadResearchSnapshot } from '../../data/researchSnapshot'

interface ResearchFinancialArchetypesProps {
  sessionToken: string
  metadata: any
}

const ARCHETYPE_COLORS = {
  'Donation-Funded Programs': '#D4B968',
  'Fee-for-Service Operators': '#8B7355',
  'Endowment-Funded Grantmakers': '#B8902F',
}

const BAND_LABELS = {
  'Micro (<$150K)': '0',
  'Professional ($150K–$700K)': '1',
  'Established (>$700K)': '2',
}

const ARCHETYPE_DESCRIPTIONS: Record<string, string> = {
  'Donation-Funded Programs': 'Nonprofits that rely on community donations, grants, and fundraised revenue. These are typically direct-service organizations like food banks, schools, and clinics.',
  'Fee-for-Service Operators': 'Nonprofits that generate revenue by providing services, including memberships, program fees, and contracted work. Examples: consulting firms, training providers, event organizers.',
  'Endowment-Funded Grantmakers': 'Nonprofits funded primarily by endowment returns or large unrestricted reserves, often grantmakers. Examples: community foundations, family foundations, research institutes.',
}

function formatPercent(value: number | null): string {
  if (value === null || value === undefined) return '—'
  return `${value.toFixed(1)}%`
}

function formatScore(value: number | null): string {
  if (value === null || value === undefined) return '—'
  return value.toFixed(1)
}

function formatMonths(value: number | null): string {
  if (value === null || value === undefined) return '—'
  return `${value.toFixed(1)}mo`
}

export default function ResearchFinancialArchetypes({
  sessionToken,
  metadata,
}: ResearchFinancialArchetypesProps) {
  const [v5Data, setV5Data] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadResearchSnapshot()
      .then((snap) => setV5Data(snap.v5 ?? null))
      .catch((error) => console.error('Failed to load v5 data:', error))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div>
        <h2 className="text-3xl font-display text-deep-navy mb-6">
          Financial Archetypes & Revenue Bands
        </h2>
        <p className="text-sm text-cool-grey">Loading…</p>
      </div>
    )
  }

  if (!v5Data) {
    return (
      <div>
        <h2 className="text-3xl font-display text-deep-navy mb-6">
          Financial Archetypes & Revenue Bands
        </h2>
        <p className="text-sm text-cool-grey">Data not available.</p>
      </div>
    )
  }

  const archetypes = v5Data.archetypes || []
  const cells = v5Data.cells || []
  const healthTotals = v5Data.health_totals || { healthy: 0, stable: 0, caution: 0 }
  const totalScored = v5Data.total_scored || 0

  // Composition bar
  const archetypeCompositionRows = archetypes.map((a: any) => ({
    key: a.archetype,
    label: a.archetype,
    pct: a.pct,
    color: ARCHETYPE_COLORS[a.archetype as keyof typeof ARCHETYPE_COLORS] || '#999',
    count: a.count,
  }))

  // Health signal percentages
  const healthTotal = healthTotals.healthy + healthTotals.stable + healthTotals.caution
  const healthPcts = {
    healthy: healthTotal > 0 ? ((healthTotals.healthy / healthTotal) * 100).toFixed(1) : '0',
    stable: healthTotal > 0 ? ((healthTotals.stable / healthTotal) * 100).toFixed(1) : '0',
    caution: healthTotal > 0 ? ((healthTotals.caution / healthTotal) * 100).toFixed(1) : '0',
  }

  return (
    <div>
      <h2 className="text-3xl font-display text-deep-navy mb-4">
        Financial Archetypes & Revenue Bands
      </h2>
      <p className="text-lg text-cool-grey mb-6 max-w-2xl">
        We categorize nonprofit organizations by their primary funding model and revenue scale.
        Each archetype represents a fundamentally different financial strategy and risk profile.
      </p>

      {/* Archetype Composition */}
      <div className="mb-12">
        <h3 className="text-xl font-semibold text-deep-navy mb-4">Composition</h3>
        <p className="text-sm text-cool-grey mb-4">
          Among {totalScored.toLocaleString()} organizations with complete financial data:
        </p>

        {/* Composition bar */}
        <div className="flex h-3 w-full max-w-2xl overflow-hidden rounded-full mb-6 border border-light-grey">
          {archetypeCompositionRows.map((r: any) => (
            <div
              key={r.key}
              style={{ width: `${r.pct}%`, backgroundColor: r.color }}
              title={`${r.label}: ${r.pct}%`}
            />
          ))}
        </div>

        {/* Archetype rows */}
        <div className="space-y-6 max-w-2xl">
          {archetypeCompositionRows.map((r: any) => (
            <div key={r.key}>
              <div className="flex items-baseline gap-3 mb-2">
                <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: r.color }} />
                <span className="font-display text-2xl text-deep-navy">{r.pct}%</span>
                <span className="text-sm font-medium text-deep-navy">{r.label}</span>
                <span className="text-xs text-cool-grey">({r.count.toLocaleString()})</span>
              </div>
              <p className="text-sm text-slate ml-6 leading-relaxed max-w-xl">
                {ARCHETYPE_DESCRIPTIONS[r.label]}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Peer Cells Grid */}
      <div className="mb-12">
        <h3 className="text-xl font-semibold text-deep-navy mb-4">Peer Groups</h3>
        <p className="text-sm text-cool-grey mb-6">
          A peer group is formed by combining archetype and revenue band. Organizations within the
          same peer group are benchmarked against each other. Score is a percentile rank (0–100)
          within that peer group.
        </p>

        <div className="overflow-x-auto" tabIndex={0} role="region" aria-label="Scrollable data table">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-light-grey bg-deep-navy/[0.02]">
                <th className="text-left px-4 py-3 font-semibold text-deep-navy">Archetype</th>
                <th className="text-left px-4 py-3 font-semibold text-deep-navy">Revenue Band</th>
                <th className="text-right px-4 py-3 font-semibold text-deep-navy">Count</th>
                <th className="text-right px-4 py-3 font-semibold text-cool-grey">Avg Score</th>
                <th className="text-right px-4 py-3 font-semibold text-cool-grey">Avg Program %</th>
                <th className="text-right px-4 py-3 font-semibold text-cool-grey">Avg Reserves</th>
              </tr>
            </thead>
            <tbody>
              {cells.map((cell: any, idx: number) => (
                <tr key={idx} className="border-b border-light-grey hover:bg-deep-navy/[0.02]">
                  <td className="px-4 py-3 text-deep-navy font-medium">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-2 h-2 rounded-full"
                        style={{
                          backgroundColor:
                            ARCHETYPE_COLORS[
                              cell.archetype as keyof typeof ARCHETYPE_COLORS
                            ] || '#999',
                        }}
                      />
                      <span>{cell.archetype}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-slate">{cell.band}</td>
                  <td className="px-4 py-3 text-right font-mono text-deep-navy">
                    {cell.count.toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-cool-grey">
                    {formatScore(cell.avg_score)}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-cool-grey">
                    {formatPercent(cell.avg_program_pct)}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-cool-grey">
                    {formatMonths(cell.avg_months_reserve)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Health Signals */}
      <div className="mb-12">
        <h3 className="text-xl font-semibold text-deep-navy mb-4">Financial Health Distribution</h3>
        <p className="text-sm text-cool-grey mb-6">
          We assess organizations using three financial health signals based on their revenue
          stability, reserve adequacy, and spending patterns. These assessments are computed for
          each organization and reported as aggregates across peer groups.
        </p>

        <div className="flex h-4 w-full max-w-2xl overflow-hidden rounded-full mb-6 border border-light-grey">
          <div
            style={{
              width: `${healthPcts.healthy}%`,
              backgroundColor: '#10B981',
            }}
            title={`HEALTHY: ${healthPcts.healthy}%`}
          />
          <div
            style={{
              width: `${healthPcts.stable}%`,
              backgroundColor: '#F59E0B',
            }}
            title={`STABLE: ${healthPcts.stable}%`}
          />
          <div
            style={{
              width: `${healthPcts.caution}%`,
              backgroundColor: '#EF4444',
            }}
            title={`CAUTION: ${healthPcts.caution}%`}
          />
        </div>

        <div className="space-y-4 max-w-2xl">
          <div className="flex gap-4">
            <div className="w-3 h-3 rounded-full flex-shrink-0 mt-1" style={{ backgroundColor: '#10B981' }} />
            <div>
              <div className="font-semibold text-deep-navy">
                Healthy ({healthPcts.healthy}%)
              </div>
              <p className="text-sm text-slate mt-1">
                Reserves above the peer median for this archetype and revenue band. The organization
                has a financial cushion relative to similar nonprofits.
              </p>
            </div>
          </div>

          <div className="flex gap-4">
            <div className="w-3 h-3 rounded-full flex-shrink-0 mt-1" style={{ backgroundColor: '#F59E0B' }} />
            <div>
              <div className="font-semibold text-deep-navy">
                Stable ({healthPcts.stable}%)
              </div>
              <p className="text-sm text-slate mt-1">
                Reserves near the peer median. The organization operates within the typical range
                for its peers.
              </p>
            </div>
          </div>

          <div className="flex gap-4">
            <div className="w-3 h-3 rounded-full flex-shrink-0 mt-1" style={{ backgroundColor: '#F59E0B' }} />
            <div>
              <div className="font-semibold text-deep-navy">
                Needs support ({healthPcts.caution}%)
              </div>
              <p className="text-sm text-slate mt-1">
                Reserves below the peer median. This does not reflect the quality of the work —
                many of the highest-impact organizations in a community operate lean by design,
                or because demand for their services outpaces available funding. Donors
                who give here often make the most difference.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-warm-cream/40 border border-soft-gold/30 rounded-lg p-5 max-w-2xl">
        <p className="text-sm text-deep-navy font-semibold mb-2">A note on how to use this</p>
        <p className="text-sm text-slate leading-relaxed">
          Financial context is a starting point, not a score card. A lower reserves number can
          mean many things: rapid growth, recent investment in programs, a community that depends
          heavily on the organization, or simply that unrestricted funding is hard to come by.
          Daanaa does not recommend giving to some organizations over others. We provide
          context so donors can ask better questions and give with more confidence — wherever
          they choose to give.
        </p>
      </div>
    </div>
  )
}
