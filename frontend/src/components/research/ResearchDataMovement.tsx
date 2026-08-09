import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, Legend,
} from 'recharts'
import { loadResearchSnapshot } from '../../data/researchSnapshot'

interface ResearchDataMovementProps {
  sessionToken: string
  metadata: any
}

export default function ResearchDataMovement({
  sessionToken,
  metadata,
}: ResearchDataMovementProps) {
  const [loading, setLoading] = useState(true)
  const [monthlyData, setMonthlyData] = useState<any[]>([])
  const [historicalTotal, setHistoricalTotal] = useState<number>(0)

  useEffect(() => {
    loadResearchSnapshot()
      .then((snap) => {
        setMonthlyData(snap.monthly_changes ?? [])
        setHistoricalTotal(snap.v6?.total_placed ?? 0)
      })
      .catch((error) => console.error('Failed to load snapshot:', error))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div>
        <h2 className="text-3xl font-display text-deep-navy mb-4">Data and version history</h2>
        <p className="text-sm text-cool-grey">Loading…</p>
      </div>
    )
  }

  const lastUpdate = metadata?.data_period
    ? new Date(metadata.data_period).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    : 'Unknown'

  const totalOrgs = metadata?.total_organizations || 1729314
  const revokedCount = 192896
  const fullRegistry = totalOrgs + revokedCount

  // IRS SOI annual 990 filer data — sourced from IRS Statistics of Income extracts
  const irsData = [
    {
      period: 'Tax year 2022',
      filers501c3: 251206,
      combinedRevenue: '$2.93T',
      source: 'IRS SOI Extract 2022',
    },
    {
      period: 'Tax year 2023',
      filers501c3: 261146,
      combinedRevenue: '$3.03T',
      source: 'IRS SOI Extract 2023',
    },
    {
      period: 'Tax year 2024',
      filers501c3: 269686,
      combinedRevenue: '$3.16T',
      source: 'IRS SOI Extract 2024',
    },
  ]

  const filerGrowth = irsData[2].filers501c3 - irsData[0].filers501c3
  const revenueNote = 'Revenue figures represent 501(c)(3) full-990 filers only. Organizations below the filing threshold are not included.'

  return (
    <div>
      <h2 className="text-3xl font-display text-deep-navy mb-4">Data and version history</h2>

      <p className="text-lg text-cool-grey mb-6 max-w-2xl">
        We monitor nonprofit data continuously. Here's what the most recent IRS data
        reveals: observations without conclusions. We're all learning how to read this
        data responsibly.
      </p>

      <div className="space-y-8 max-w-2xl">

        {/* Current Registry State */}
        <div className="bg-deep-navy/[0.02] rounded-lg p-6 border border-light-grey">
          <div className="flex justify-between items-baseline mb-1">
            <h3 className="text-lg font-semibold text-deep-navy">Daanaa Index</h3>
            <span className="text-xs text-cool-grey">As of {lastUpdate}</span>
          </div>
          <div className="space-y-4 mt-4">
            <div className="flex justify-between items-baseline">
              <span className="text-cool-grey">Active, tax-deductible 501(c)(3)s indexed:</span>
              <span className="font-display text-2xl text-deep-navy">{totalOrgs.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-baseline">
              <span className="text-cool-grey">Revoked or removed from active status:</span>
              <span className="font-display text-2xl text-deep-navy">{revokedCount.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-baseline border-t border-light-grey pt-3">
              <span className="text-cool-grey text-sm">Full registry including inactive:</span>
              <span className="text-sm text-cool-grey">{fullRegistry.toLocaleString()}</span>
            </div>
          </div>
        </div>

        {/* Month-over-Month Activity Chart */}
        {monthlyData.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-deep-navy mb-2">
              Month-over-month activity
            </h3>
            <p className="text-sm text-cool-grey mb-4">
              New IRS registrations and revocations over the past 24 months. Bars show
              both flows. Taller bars mean more activity, not necessarily growth.
            </p>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart
                data={monthlyData.map((m) => ({
                  ...m,
                  label: m.month.slice(2).replace('-', '/'),
                }))}
                barGap={0}
                barCategoryGap="15%"
                margin={{ top: 4, right: 0, left: 0, bottom: 4 }}
              >
                <XAxis
                  dataKey="label"
                  tick={{ fontSize: 10, fill: '#A0AFC3' }}
                  axisLine={false}
                  tickLine={false}
                  interval={3}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: '#A0AFC3' }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v) => v >= 1000 ? `${(v / 1000).toFixed(0)}K` : v}
                  width={32}
                />
                <Tooltip
                  cursor={{ fill: 'rgba(212,185,104,0.08)' }}
                  content={({ active, payload, label }) => {
                    if (!active || !payload?.length) return null
                    const d = payload[0]?.payload
                    return (
                      <div className="bg-deep-navy text-warm-cream p-3 rounded shadow-lg text-xs border border-soft-gold/30">
                        <p className="font-semibold text-soft-gold mb-1">{d?.month}</p>
                        <p>New registrations: {d?.new_registrations?.toLocaleString()}</p>
                        <p>Revocations: {d?.revocations?.toLocaleString()}{d?.is_batch_revocation ? ' ⚠ IRS batch' : ''}</p>
                        <p className={`mt-1 font-medium ${d?.net >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          Net: {d?.net >= 0 ? '+' : ''}{d?.net?.toLocaleString()}
                        </p>
                      </div>
                    )
                  }}
                />
                <Bar dataKey="new_registrations" name="New registrations" stackId="a" fill="#D4B968" radius={[0,0,0,0]} />
                <Bar dataKey="revocations" name="Revocations" stackId="a" fill="transparent" stroke="transparent">
                  {monthlyData.map((m, i) => (
                    <Cell
                      key={i}
                      fill={m.is_batch_revocation ? 'rgba(239,68,68,0.55)' : 'rgba(239,68,68,0.25)'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="flex gap-6 mt-2 text-xs text-cool-grey">
              <span className="flex items-center gap-1.5">
                <span className="inline-block w-3 h-2 rounded-sm" style={{ background: '#D4B968' }} />
                New registrations
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block w-3 h-2 rounded-sm" style={{ background: 'rgba(239,68,68,0.4)' }} />
                Revocations
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block w-3 h-2 rounded-sm" style={{ background: 'rgba(239,68,68,0.55)' }} />
                IRS batch revocation
              </span>
            </div>
            <p className="text-xs text-cool-grey mt-2 leading-relaxed">
              Revocations overlay within each bar shows how much of that month's activity was
              removals. IRS auto-revocation batches (typically May each year) are shown at higher
              opacity. Hover for exact counts.
            </p>
          </div>
        )}

        {/* Year-over-Year IRS Data */}
        <div>
          <h3 className="text-lg font-semibold text-deep-navy mb-2">Sector growth: 990 filers</h3>
          <p className="text-sm text-cool-grey mb-4">
            Based on IRS Statistics of Income annual extracts, organizations that file a full Form 990.
          </p>
          <div className="overflow-x-auto" tabIndex={0} role="region" aria-label="Scrollable data table">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-light-grey">
                  <th className="text-left py-2 pr-4 font-semibold text-deep-navy">Period</th>
                  <th className="text-right py-2 pr-4 font-semibold text-deep-navy">501(c)(3) filers</th>
                  <th className="text-right py-2 font-semibold text-deep-navy">Combined revenue</th>
                </tr>
              </thead>
              <tbody>
                {irsData.map((row) => (
                  <tr key={row.period} className="border-b border-light-grey/50">
                    <td className="py-3 pr-4 text-cool-grey">{row.period}</td>
                    <td className="py-3 pr-4 text-right font-mono text-deep-navy">{row.filers501c3.toLocaleString()}</td>
                    <td className="py-3 text-right font-mono text-deep-navy">{row.combinedRevenue}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-cool-grey mt-3 leading-relaxed">
            {filerGrowth.toLocaleString()} more organizations filed a 990 in tax year 2024 versus 2022, a {((filerGrowth / irsData[0].filers501c3) * 100).toFixed(1)}% increase over two years. {revenueNote}
          </p>
        </div>

        {/* Data Freshness */}
        <div className="bg-soft-gold/10 rounded-lg p-6 border border-soft-gold/30">
          <h3 className="text-lg font-semibold text-deep-navy mb-3">Data freshness</h3>
          <p className="text-cool-grey text-sm mb-3">
            Our last sync with IRS data occurred on <strong>{lastUpdate}</strong>. The
            active nonprofit census is updated by the IRS Business Master File, and we
            sync those updates automatically.
          </p>
          <p className="text-sm text-slate leading-relaxed">
            The {revokedCount.toLocaleString()} revoked organizations represent a mix of
            mergers, closures, and status changes over time. We exclude them from our
            public count to keep it accurate: {totalOrgs.toLocaleString()} active
            501(c)(3)s, not {(fullRegistry / 1_000_000).toFixed(2)}M.
          </p>
        </div>

        {/* Coverage */}
        <div>
          <h3 className="text-lg font-semibold text-deep-navy mb-4">Coverage</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between items-baseline">
                <p className="font-semibold text-deep-navy">Mission statements</p>
                <span className="text-xs text-cool-grey">As of {lastUpdate}</span>
              </div>
              <p className="text-sm text-slate mt-1">
                We have mission information for all {(totalOrgs / 1_000_000).toFixed(1)}M active
                nonprofits, drawn from IRS 990 forms and NTEE classification. Where no public
                description exists, we generate an AI-assisted summary from the organization's
                public filing data so the organization is still findable. These are clearly
                labeled, and a nonprofit can replace its summary with its own words when it claims
                its page, which also improves how it surfaces in search and cause tags.
              </p>
            </div>
            <div>
              <div className="flex justify-between items-baseline">
                <p className="font-semibold text-deep-navy">Peer context coverage</p>
                <span className="text-xs text-cool-grey">As of {lastUpdate}</span>
              </div>
              <p className="text-sm text-slate mt-1">
                {historicalTotal.toLocaleString()} active organizations are placed into one of
                the four V6 context tiers. Three of the four tiers include an actual peer
                comparison; the fourth, Archetype Only, means the public record does not yet
                support one. See "Peer Context Coverage" above for the full breakdown.
              </p>
            </div>
          </div>
        </div>

        {/* Learning Note */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-deep-navy leading-relaxed">
            <strong>Why we show this:</strong> We believe transparency about what we know,
            what we don't, and what we're still learning makes our data more credible. If
            you notice something inconsistent, please let us know via the Correction form
            on any organization's detail page.
          </p>
        </div>

      </div>
    </div>
  )
}
