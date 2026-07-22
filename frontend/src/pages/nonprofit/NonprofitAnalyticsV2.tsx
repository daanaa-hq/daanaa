import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { BarChart, LineChart, PieChart, TrendingUp, Calendar } from 'lucide-react'

interface ChartData {
  label: string
  value: number
}

interface AnalyticsData {
  hours_by_month: ChartData[]
  hours_by_task_type: ChartData[]
  volunteer_growth: ChartData[]
  impact_value_by_month: ChartData[]
  retention_rate: number
  avg_hours_per_volunteer: number
}

export default function NonprofitAnalyticsV2() {
  const { ein } = useParams<{ ein: string }>()
  const { user, getIdToken } = useAuth()
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [timeframe, setTimeframe] = useState<'3m' | '6m' | '1y'>('6m')

  useEffect(() => {
    const fetchAnalytics = async () => {
      if (!ein || !user) return

      const token = await getIdToken()
      if (!token) return

      try {
        const res = await fetch(
          `/api/nonprofit/${ein}/volunteer/analytics?timeframe=${timeframe}`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        )

        if (res.ok) {
          const data = await res.json()
          setAnalytics(data.data || data)
        }
      } catch (error) {
        console.error('Analytics fetch failed:', error)
      } finally {
        setLoading(false)
      }
    }

    setLoading(true)
    fetchAnalytics()
  }, [ein, user, getIdToken, timeframe])

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 rounded-full border-4 border-soft-gold border-t-transparent animate-spin mx-auto mb-4" />
          <p className="text-slate-600">Loading analytics...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-slate-900 mb-2">Volunteer Analytics</h1>
            <p className="text-slate-600">Trends, impact, and growth metrics</p>
          </div>

          {/* Timeframe Selector */}
          <div className="flex gap-2 bg-white rounded-lg border border-slate-200 p-1">
            <button
              onClick={() => setTimeframe('3m')}
              className={`px-4 py-2 rounded-md font-medium transition ${
                timeframe === '3m'
                  ? 'bg-soft-gold text-white'
                  : 'text-slate-700 hover:bg-slate-100'
              }`}
            >
              3 months
            </button>
            <button
              onClick={() => setTimeframe('6m')}
              className={`px-4 py-2 rounded-md font-medium transition ${
                timeframe === '6m'
                  ? 'bg-soft-gold text-white'
                  : 'text-slate-700 hover:bg-slate-100'
              }`}
            >
              6 months
            </button>
            <button
              onClick={() => setTimeframe('1y')}
              className={`px-4 py-2 rounded-md font-medium transition ${
                timeframe === '1y'
                  ? 'bg-soft-gold text-white'
                  : 'text-slate-700 hover:bg-slate-100'
              }`}
            >
              1 year
            </button>
          </div>
        </div>

        {/* Key Metrics */}
        {analytics && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {/* Retention Rate */}
            <div className="bg-white rounded-lg border border-slate-200 p-6">
              <div className="flex items-center gap-3 mb-4">
                <TrendingUp size={24} className="text-blue-500" />
                <h3 className="text-lg font-semibold text-slate-900">Volunteer Retention</h3>
              </div>
              <p className="text-5xl font-bold text-blue-600 mb-2">
                {analytics.retention_rate.toFixed(0)}%
              </p>
              <p className="text-slate-600 text-sm">
                Percentage of volunteers returning for additional service
              </p>
            </div>

            {/* Avg Hours */}
            <div className="bg-white rounded-lg border border-slate-200 p-6">
              <div className="flex items-center gap-3 mb-4">
                <Calendar size={24} className="text-emerald-500" />
                <h3 className="text-lg font-semibold text-slate-900">Avg Hours per Volunteer</h3>
              </div>
              <p className="text-5xl font-bold text-emerald-600 mb-2">
                {analytics.avg_hours_per_volunteer.toFixed(1)}
              </p>
              <p className="text-slate-600 text-sm">
                Average volunteer commitment this period
              </p>
            </div>
          </div>
        )}

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Hours by Month */}
          <div className="bg-white rounded-lg border border-slate-200 p-6">
            <div className="flex items-center gap-3 mb-6">
              <LineChart size={24} className="text-purple-500" />
              <h3 className="text-lg font-semibold text-slate-900">Hours Over Time</h3>
            </div>
            <div className="h-64 flex items-end gap-2">
              {analytics?.hours_by_month.map((point, i) => (
                <div key={i} className="flex-1 flex flex-col items-center">
                  <div
                    className="w-full bg-gradient-to-t from-purple-500 to-purple-400 rounded-t-lg hover:opacity-80 transition"
                    style={{
                      height: `${Math.max(
                        20,
                        (point.value /
                          Math.max(
                            ...((analytics?.hours_by_month || []).map((p) => p.value) as number[])
                          )) *
                          100
                      )}%`,
                    }}
                    title={`${point.label}: ${point.value} hours`}
                  />
                  <p className="text-xs text-slate-600 mt-2 text-center whitespace-nowrap">
                    {point.label}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Hours by Task Type */}
          <div className="bg-white rounded-lg border border-slate-200 p-6">
            <div className="flex items-center gap-3 mb-6">
              <PieChart size={24} className="text-orange-500" />
              <h3 className="text-lg font-semibold text-slate-900">Hours by Activity Type</h3>
            </div>
            <div className="space-y-3">
              {analytics?.hours_by_task_type.map((point, i) => {
                const total = (analytics?.hours_by_task_type || []).reduce(
                  (sum, p) => sum + p.value,
                  0
                )
                const percentage = total > 0 ? (point.value / total) * 100 : 0
                return (
                  <div key={i}>
                    <div className="flex justify-between items-center mb-1">
                      <p className="text-sm font-medium text-slate-700">{point.label}</p>
                      <p className="text-sm font-bold text-slate-900">{percentage.toFixed(0)}%</p>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-orange-400 to-orange-500 h-2 rounded-full transition-all"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* Volunteer Growth Chart */}
        <div className="bg-white rounded-lg border border-slate-200 p-6">
          <div className="flex items-center gap-3 mb-6">
            <BarChart size={24} className="text-teal-500" />
            <h3 className="text-lg font-semibold text-slate-900">New Volunteers Acquired</h3>
          </div>
          <div className="h-80 flex items-end gap-2">
            {analytics?.volunteer_growth.map((point, i) => (
              <div key={i} className="flex-1 flex flex-col items-center">
                <div
                  className="w-full bg-gradient-to-t from-teal-500 to-teal-400 rounded-t-lg hover:opacity-80 transition"
                  style={{
                    height: `${Math.max(
                      20,
                      (point.value /
                        Math.max(
                          ...((analytics?.volunteer_growth || []).map((p) => p.value) as number[])
                        )) *
                        100
                    )}%`,
                  }}
                  title={`${point.label}: ${point.value} volunteers`}
                />
                <p className="text-xs text-slate-600 mt-2 text-center whitespace-nowrap">
                  {point.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
