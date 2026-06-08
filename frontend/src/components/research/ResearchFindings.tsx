import { useEffect, useState } from 'react'

interface ResearchFindingsProps {
  sessionToken: string
  metadata: any
}

export default function ResearchFindings({
  sessionToken,
  metadata,
}: ResearchFindingsProps) {
  const [stateData, setStateData] = useState<any[]>([])
  const [categoryData, setCategoryData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [stateRes, catRes] = await Promise.all([
          fetch('/api/research/summary/states', {
            headers: { 'X-Research-Session': sessionToken },
          }),
          fetch('/api/research/summary/categories', {
            headers: { 'X-Research-Session': sessionToken },
          }),
        ])

        if (stateRes.ok) {
          const result = await stateRes.json()
          setStateData(result.data || [])
        }
        if (catRes.ok) {
          const result = await catRes.json()
          setCategoryData(result.data || [])
        }
      } catch (error) {
        console.error('Failed to load findings data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [sessionToken])

  return (
    <div>
      <h2 className="text-3xl font-display text-deep-navy mb-6">Research Findings</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div>
          <h3 className="text-xl font-semibold text-deep-navy mb-4">
            Geographic Distribution
          </h3>
          <p className="text-sm text-cool-grey mb-6">
            Top 10 states by nonprofit count. This reflects both population distribution and
            state-specific nonprofit registration patterns.
          </p>
          {loading ? (
            <div className="text-cool-grey">Loading...</div>
          ) : (
            <div className="space-y-2">
              {stateData.slice(0, 10).map((item, idx) => (
                <div key={item.state} className="flex items-center justify-between">
                  <span className="text-cool-grey">
                    <span className="font-semibold">{idx + 1}.</span> {item.state}
                  </span>
                  <span className="text-deep-navy font-semibold">
                    {item.count.toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          <h3 className="text-xl font-semibold text-deep-navy mb-4">
            Top Cause Areas (NTEE1)
          </h3>
          <p className="text-sm text-cool-grey mb-6">
            Organizations grouped by primary cause category. Beacon/Torch/Candle/Spark
            percentages show data completeness distribution.
          </p>
          {loading ? (
            <div className="text-cool-grey">Loading...</div>
          ) : (
            <div className="space-y-3">
              {categoryData.slice(0, 8).map((item) => (
                <div key={item.ntee1} className="bg-soft-gold/5 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-deep-navy text-sm">
                      {item.ntee_label}
                    </span>
                    <span className="text-xs text-cool-grey">
                      {item.count.toLocaleString()} orgs
                    </span>
                  </div>
                  <div className="flex gap-1 text-xs">
                    {[
                      { pct: item.pct_beacon, color: '#B8902F', label: 'Beacon' },
                      { pct: item.pct_torch, color: '#D4B968', label: 'Torch' },
                      { pct: item.pct_candle, color: '#E8C896', label: 'Candle' },
                      { pct: item.pct_spark, color: '#F0D8B0', label: 'Spark' },
                    ].map((tier) => (
                      <div
                        key={tier.label}
                        style={{
                          width: `${tier.pct || 0}%`,
                          backgroundColor: tier.color,
                          height: '20px',
                          borderRadius: '2px',
                        }}
                        title={`${tier.label}: ${(tier.pct || 0).toFixed(1)}%`}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="mt-12 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-deep-navy mb-3">
          Key Insights & Patterns
        </h3>
        <ul className="space-y-2 text-sm text-cool-grey">
          <li>
            ✓ <strong>Regional variation:</strong> Nonprofit density varies by state,
            reflecting regulatory differences and population distribution.
          </li>
          <li>
            ✓ <strong>Cause concentration:</strong> Human services, health, and education
            dominate the nonprofit landscape.
          </li>
          <li>
            ✓ <strong>Data completeness inequality:</strong> Beacon organizations
            (full-data) are more common in established service areas.
          </li>
          <li>
            ✓ <strong>Small-org underrepresentation:</strong> Smaller nonprofits have lower
            tier placement due to reduced public data, not reduced impact.
          </li>
        </ul>
      </div>
    </div>
  )
}
