import { useEffect, useState } from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'

interface ResearchLampTiersProps {
  sessionToken: string
  metadata: any
}

const TIER_COLORS: Record<string, string> = {
  Beacon: '#B8902F',
  Torch: '#D4B968',
  Candle: '#E8C896',
  Spark: '#F0D8B0',
}

const TIER_DESCRIPTIONS: Record<string, string> = {
  Beacon:
    'Complete public data: financial reports, mission, website, and current Form 990 on file.',
  Torch: 'Strong public data: financial context available, recent filings, organizational information on record.',
  Candle:
    'Moderate public data: some financial information and basic organizational records available.',
  Spark: 'Recognized nonprofit with minimal public information available.',
}

export default function ResearchLampTiers({
  sessionToken,
  metadata,
}: ResearchLampTiersProps) {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [fullScreen, setFullScreen] = useState(false)

  useEffect(() => {
    const fetchData = async () => {
      try {
        console.log('Fetching lamp tiers with token:', sessionToken)
        const response = await fetch('/api/research/summary/lamp-tiers', {
          headers: { 'X-Research-Session': sessionToken },
        })
        console.log('Lamp tiers response status:', response.status)
        if (response.ok) {
          const result = await response.json()
          console.log('Lamp tiers data:', result.data)
          setData(result.data || [])
        } else {
          const error = await response.text()
          console.error('Lamp tiers error:', response.status, error)
        }
      } catch (error) {
        console.error('Failed to load lamp tiers data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [sessionToken])

  const chartContent = (
    <ResponsiveContainer width="100%" height={400}>
      <PieChart>
        <Pie
          data={data}
          dataKey="count"
          nameKey="merit_tier"
          cx="50%"
          cy="50%"
          outerRadius={150}
          label
        >
          {data.map((entry) => (
            <Cell key={`cell-${entry.merit_tier}`} fill={TIER_COLORS[entry.merit_tier]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  )

  if (fullScreen) {
    return (
      <div className="fixed inset-0 z-50 bg-deep-navy p-8">
        <button
          onClick={() => setFullScreen(false)}
          className="absolute top-4 right-4 text-warm-cream hover:text-soft-gold text-2xl"
        >
          ✕
        </button>
        <h2 className="text-2xl font-display text-warm-cream mb-4">
          Lamp Tier Distribution
        </h2>
        {chartContent}
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-display text-deep-navy">Lamp Tiers</h2>
        <button
          onClick={() => setFullScreen(true)}
          className="px-3 py-1 text-xs bg-soft-gold text-deep-navy rounded hover:bg-bright-gold"
        >
          Full Screen ⛶
        </button>
      </div>

      <p className="text-cool-grey mb-6 max-w-2xl">
        Lamp Tiers (Beacon, Torch, Candle, Spark) are a visibility journey, not a quality
        verdict. They indicate how much public data backs an organization's profile, enabling
        you to understand what we know and what we don't.
      </p>

      {loading ? (
        <div className="h-96 flex items-center justify-center text-cool-grey">
          Loading...
        </div>
      ) : (
        <div className="space-y-8">
          {/* Interactive slider bar */}
          <div className="bg-white rounded-lg p-6 border border-light-grey">
            <p className="text-sm font-semibold text-deep-navy mb-4">Distribution across lamp tiers</p>
            <div className="flex gap-0 h-12 rounded-lg overflow-hidden">
              {data.map((item) => (
                <div
                  key={item.merit_tier}
                  className="flex items-center justify-center text-xs font-bold text-white"
                  style={{
                    width: `${item.pct_of_total}%`,
                    backgroundColor: TIER_COLORS[item.merit_tier],
                  }}
                  title={`${item.merit_tier}: ${(item.pct_of_total || 0).toFixed(1)}%`}
                >
                  {(item.pct_of_total || 0) > 10 && (
                    <span>{(item.pct_of_total || 0).toFixed(0)}%</span>
                  )}
                </div>
              ))}
            </div>
            <div className="mt-4 flex justify-between text-xs text-cool-grey">
              {data.map((item) => (
                <div key={item.merit_tier} className="text-center">
                  <p className="font-semibold text-deep-navy">{item.merit_tier}</p>
                  <p>{(item.pct_of_total || 0).toFixed(1)}%</p>
                  <p className="text-cool-grey/60">{item.count.toLocaleString()} orgs</p>
                </div>
              ))}
            </div>
          </div>

          {/* Chart */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-white rounded-lg p-6 border border-light-grey">
              {chartContent}
            </div>

            <div className="space-y-4">
            {['Beacon', 'Torch', 'Candle', 'Spark'].map((tier) => {
              const tierData = data.find((d) => d.merit_tier === tier)
              return (
                <div key={tier} className="rounded-lg p-4 border-l-4 bg-white" style={{
                  borderLeftColor: TIER_COLORS[tier],
                }}>
                  <div className="flex items-center gap-3 mb-2">
                    <div
                      className="w-6 h-6 rounded-full"
                      style={{ backgroundColor: TIER_COLORS[tier] }}
                    />
                    <h4 className="font-semibold text-deep-navy">{tier}</h4>
                  </div>
                  <p className="text-sm text-cool-grey mb-2">{TIER_DESCRIPTIONS[tier]}</p>
                  {tierData && (
                    <p className="text-xs text-cool-grey/60">
                      {tierData.count.toLocaleString()} organizations (
                      {tierData.pct_of_total?.toFixed(1)}%)
                    </p>
                  )}
                </div>
              )
            })}
            </div>
          </div>
        </div>
      )}

      <div className="mt-8 bg-soft-gold/10 rounded-lg p-4">
        <p className="text-sm font-semibold text-deep-navy mb-2">
          💡 The Lamp Metaphor
        </p>
        <p className="text-sm text-cool-grey">
          In traditional philanthropy, donor visibility depends on marketing budgets and
          foundation relationships. Our lamp tiers measure something different: public data
          completeness. A "Spark" organization isn't weak—it's simply less visible due to
          limited public records, not organizational capacity.
        </p>
      </div>
    </div>
  )
}
