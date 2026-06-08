import { useEffect, useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

interface ResearchCoverageProps {
  sessionToken: string
  metadata: any
}

export default function ResearchCoverage({
  sessionToken,
  metadata,
}: ResearchCoverageProps) {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [fullScreen, setFullScreen] = useState(false)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/research/summary/data-coverage', {
          headers: { 'X-Research-Session': sessionToken },
        })
        if (response.ok) {
          const result = await response.json()
          setData(result.data || [])
        }
      } catch (error) {
        console.error('Failed to load coverage data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [sessionToken])

  const chartContent = (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="data_type" angle={-45} textAnchor="end" height={100} tick={{ fontSize: 12 }} />
        <YAxis label={{ value: 'Coverage %', angle: -90, position: 'insideLeft' }} />
        <Tooltip formatter={(value) => `${Number(value).toFixed(1)}%`} />
        <Bar dataKey="pct_covered" fill="#B8902F" name="Coverage %" />
      </BarChart>
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
          Data Coverage
        </h2>
        {chartContent}
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-display text-deep-navy">Data Coverage</h2>
        <button
          onClick={() => setFullScreen(true)}
          className="px-3 py-1 text-xs bg-soft-gold text-deep-navy rounded hover:bg-bright-gold"
        >
          Full Screen ⛶
        </button>
      </div>

      <p className="text-cool-grey mb-6 max-w-2xl">
        What percentage of organizations have data for key fields? This transparency helps
        advisors understand gaps in public data availability.
      </p>

      {loading ? (
        <div className="h-96 flex items-center justify-center text-cool-grey">
          Loading...
        </div>
      ) : (
        <div className="bg-white rounded-lg p-6 border border-light-grey">
          {chartContent}
        </div>
      )}

      <div className="mt-8 grid grid-cols-2 gap-4">
        {data.map((item) => (
          <div key={item.data_type} className="bg-soft-gold/5 rounded-lg p-4">
            <div className="text-sm font-semibold text-deep-navy mb-1">
              {item.data_type}
            </div>
            <div className="text-2xl font-display text-soft-gold">
              {item.pct_covered?.toFixed(1)}%
            </div>
            <div className="text-xs text-cool-grey mt-1">
              {item.has_data?.toLocaleString()} of {item.total_orgs?.toLocaleString()} orgs
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
