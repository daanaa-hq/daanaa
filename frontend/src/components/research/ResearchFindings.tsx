import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { loadResearchSnapshot } from '../../data/researchSnapshot'

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
    loadResearchSnapshot()
      .then((snap) => {
        setStateData(snap.states || [])
        setCategoryData(snap.categories || [])
      })
      .catch((error) => console.error('Failed to load findings data:', error))
      .finally(() => setLoading(false))
  }, [])

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
            Organizations grouped by primary cause category.
          </p>
          {loading ? (
            <div className="text-cool-grey">Loading...</div>
          ) : (
            <div className="space-y-2">
              {categoryData.slice(0, 8).map((item) => (
                <div key={item.ntee1} className="flex items-center justify-between">
                  <span className="text-cool-grey">{item.ntee_label}</span>
                  <span className="flex items-center gap-3">
                    <span className="text-deep-navy font-semibold">
                      {item.count.toLocaleString()}
                    </span>
                    <Link
                      to={`/directory?ntee=${item.ntee1}`}
                      className="text-xs text-soft-gold hover:text-deep-navy transition-colors"
                    >
                      See all →
                    </Link>
                  </span>
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
            ✓ <strong>Data completeness varies:</strong> Organizations with a longer public
            filing history tend to have more complete peer financial context available.
          </li>
          <li>
            ✓ <strong>Small-org data gap:</strong> Smaller nonprofits more often have limited
            peer financial context, reflecting less public data on file, not less impact.
          </li>
        </ul>
      </div>
    </div>
  )
}
