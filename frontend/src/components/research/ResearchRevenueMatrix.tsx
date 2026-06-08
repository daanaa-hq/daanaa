import { useEffect, useState } from 'react'

interface ResearchRevenueMatrixProps {
  sessionToken: string
  metadata: any
}

interface MatrixCell {
  operating_model: string
  revenue_band_number: number
  count: number
  pct_of_total: number
  avg_peer_percentile: number
}

export default function ResearchRevenueMatrix({
  sessionToken,
  metadata,
}: ResearchRevenueMatrixProps) {
  const [data, setData] = useState<MatrixCell[]>([])
  const [loading, setLoading] = useState(true)
  const [fullScreen, setFullScreen] = useState(false)
  const [selectedCell, setSelectedCell] = useState<MatrixCell | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/research/summary/revenue-bands', {
          headers: { 'X-Research-Session': sessionToken },
        })
        if (response.ok) {
          const result = await response.json()
          setData(result.data || [])
        }
      } catch (error) {
        console.error('Failed to load revenue bands data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [sessionToken])

  // Group data by operating model
  const operatingModels = Array.from(
    new Set(data.map((d) => d.operating_model))
  ).sort()
  const maxBands = Math.max(...data.map((d) => d.revenue_band_number), 0)

  const getColor = (count: number, maxCount: number) => {
    const ratio = count / maxCount
    if (ratio > 0.75) return 'bg-soft-gold'
    if (ratio > 0.5) return 'bg-soft-gold/70'
    if (ratio > 0.25) return 'bg-soft-gold/40'
    return 'bg-soft-gold/20'
  }

  const maxCount = Math.max(...data.map((d) => d.count), 1)

  const MatrixContent = () => (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr>
            <th className="px-4 py-2 text-left font-semibold text-deep-navy bg-light-grey">
              Model
            </th>
            {Array.from({ length: maxBands }, (_, i) => (
              <th
                key={i}
                className="px-3 py-2 text-center font-semibold text-deep-navy bg-light-grey text-xs"
              >
                Band {i + 1}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {operatingModels.map((model) => (
            <tr key={model}>
              <td className="px-4 py-2 font-semibold text-deep-navy bg-warm-cream border-r border-light-grey">
                {model}
              </td>
              {Array.from({ length: maxBands }, (_, i) => {
                const cell = data.find(
                  (d) =>
                    d.operating_model === model && d.revenue_band_number === i + 1
                )
                return (
                  <td
                    key={i}
                    className={`p-2 text-center cursor-pointer transition-all hover:shadow-md ${
                      cell
                        ? getColor(cell.count, maxCount)
                        : 'bg-white border border-light-grey'
                    }`}
                    onClick={() => cell && setSelectedCell(cell)}
                  >
                    {cell ? (
                      <div className="text-xs">
                        <div className="font-bold text-deep-navy">
                          {cell.count.toLocaleString()}
                        </div>
                        <div className="text-cool-grey/70">
                          ({cell.pct_of_total?.toFixed(1)}%)
                        </div>
                      </div>
                    ) : (
                      <span className="text-cool-grey/30">—</span>
                    )}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )

  if (fullScreen) {
    return (
      <div className="fixed inset-0 z-50 bg-deep-navy p-8 overflow-y-auto">
        <div className="max-w-7xl mx-auto">
          <button
            onClick={() => setFullScreen(false)}
            className="absolute top-4 right-4 text-warm-cream hover:text-soft-gold text-2xl"
          >
            ✕
          </button>
          <h2 className="text-2xl font-display text-warm-cream mb-6">
            Revenue Bands Matrix (Full Screen)
          </h2>
          <div className="bg-warm-cream rounded-lg p-6">
            <MatrixContent />
          </div>
          {selectedCell && (
            <div className="mt-6 bg-soft-gold/10 rounded-lg p-4 text-warm-cream">
              <p className="font-semibold mb-2">
                {selectedCell.operating_model} — Band {selectedCell.revenue_band_number}
              </p>
              <p>Organizations: {selectedCell.count.toLocaleString()}</p>
              <p>Percentage of total: {selectedCell.pct_of_total?.toFixed(2)}%</p>
              <p>
                Avg peer percentile: {selectedCell.avg_peer_percentile?.toFixed(1)}th
              </p>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-display text-deep-navy">
          Revenue Bands Matrix
        </h2>
        <button
          onClick={() => setFullScreen(true)}
          className="px-3 py-1 text-xs bg-soft-gold text-deep-navy rounded hover:bg-bright-gold"
        >
          Full Screen ⛶
        </button>
      </div>

      <p className="text-cool-grey mb-6 max-w-2xl">
        Each operating model has model-specific revenue bands that reflect realistic peer
        groupings. This matrix shows how organizations distribute across bands within each
        model. Click any cell to see details.
      </p>

      {loading ? (
        <div className="h-96 flex items-center justify-center text-cool-grey">
          Loading...
        </div>
      ) : (
        <div className="bg-white rounded-lg p-6 border border-light-grey">
          <MatrixContent />
        </div>
      )}

      {selectedCell && (
        <div className="mt-6 bg-soft-gold/10 rounded-lg p-4">
          <p className="font-semibold text-deep-navy mb-2">
            {selectedCell.operating_model} — Band {selectedCell.revenue_band_number}
          </p>
          <p className="text-sm text-cool-grey">
            Organizations: {selectedCell.count.toLocaleString()} (
            {selectedCell.pct_of_total?.toFixed(2)}%)
          </p>
          <p className="text-sm text-cool-grey">
            Avg peer percentile: {selectedCell.avg_peer_percentile?.toFixed(1)}th
          </p>
        </div>
      )}

      <div className="mt-8">
        <p className="text-xs text-cool-grey/60 mb-2">Color scale:</p>
        <div className="flex gap-4 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-soft-gold rounded" />
            <span>High volume</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-soft-gold/40 rounded" />
            <span>Medium</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-soft-gold/20 rounded" />
            <span>Low volume</span>
          </div>
        </div>
      </div>
    </div>
  )
}
