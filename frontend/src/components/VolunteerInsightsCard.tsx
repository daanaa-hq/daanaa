import React, { useState, useEffect } from 'react'
import { VolunteerInsightsSchema, type VolunteerInsights } from '../lib/schemas'

interface VolunteerInsightsCardProps {
  nonprofitEin: string
  authToken: string
}

/**
 * VolunteerInsightsCard
 *
 * Displays impact summary for the nonprofit dashboard:
 * - Total volunteer hours (this month vs last month)
 * - Trend indicator (↑ up, ↓ down, → flat)
 * - Top 3 volunteers by hours
 * - Period toggle: "This Month" / "All Time"
 *
 * Fetches from GET /api/nonprofit/volunteer-hours/summary?period=month|all
 */
export default function VolunteerInsightsCard({ nonprofitEin, authToken }: VolunteerInsightsCardProps) {
  const [period, setPeriod] = useState<'month' | 'all'>('month')
  const [insights, setInsights] = useState<VolunteerInsights | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchInsights()
  }, [period])

  const fetchInsights = async () => {
    try {
      setLoading(true)
      const response = await fetch(`/api/nonprofit/volunteer-hours/summary?period=${period}`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) throw new Error('Failed to load volunteer insights')

      const data = await response.json()
      const validated = VolunteerInsightsSchema.parse(data)
      setInsights(validated)
      setError(null)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  const getTrendColor = (direction: string): string => {
    if (direction === 'up') return 'text-green-600'
    if (direction === 'down') return 'text-red-600'
    return 'text-gray-500'
  }

  const getTrendIcon = (direction: string): string => {
    if (direction === 'up') return '↑'
    if (direction === 'down') return '↓'
    return '→'
  }

  if (loading) {
    return (
      <div className="bg-gradient-to-br from-emerald-100/30 to-teal-100/10 rounded-2xl p-6 border border-emerald-200/30 flex items-center justify-center min-h-40">
        <div className="w-8 h-8 border-4 border-soft-gold border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (error || !insights) {
    return (
      <div className="bg-gradient-to-br from-emerald-100/30 to-teal-100/10 rounded-2xl p-6 border border-emerald-200/30">
        <div className="flex items-start justify-between mb-4">
          <h3 className="font-display text-xl text-deep-navy">Volunteer Insights</h3>
          <span className="text-2xl">📊</span>
        </div>
        <p className="text-sm text-red-600">{error || 'Failed to load insights'}</p>
      </div>
    )
  }

  return (
    <div className="bg-gradient-to-br from-emerald-100/30 to-teal-100/10 rounded-2xl p-6 border border-emerald-200/30">
      <div className="flex items-start justify-between mb-4">
        <h3 className="font-display text-xl text-deep-navy">Volunteer Insights</h3>
        <span className="text-2xl">📊</span>
      </div>

      {/* Period Toggle */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setPeriod('month')}
          className={`px-3 py-1 rounded text-xs font-semibold transition-colors ${
            period === 'month'
              ? 'bg-emerald-500 text-white'
              : 'bg-light-grey text-cool-grey hover:bg-light-grey/70'
          }`}
        >
          This Month
        </button>
        <button
          onClick={() => setPeriod('all')}
          className={`px-3 py-1 rounded text-xs font-semibold transition-colors ${
            period === 'all'
              ? 'bg-emerald-500 text-white'
              : 'bg-light-grey text-cool-grey hover:bg-light-grey/70'
          }`}
        >
          All Time
        </button>
      </div>

      {/* Hours + Trend */}
      <div className="mb-6">
        <div className="flex items-baseline gap-2 mb-2">
          <p className="font-display text-4xl italic text-emerald-600">{insights.total_hours_period}</p>
          <p className="text-cool-grey text-sm">hours</p>
        </div>

        {period === 'month' && insights.total_hours_previous_period > 0 && (
          <div className={`flex items-center gap-1 text-sm font-semibold ${getTrendColor(insights.trend_direction)}`}>
            <span>{getTrendIcon(insights.trend_direction)}</span>
            <span>
              {Math.abs(insights.trend_percent)}% vs last month
            </span>
          </div>
        )}
      </div>

      {/* Top Volunteers */}
      <div className="border-t border-emerald-200/30 pt-4">
        <p className="text-xs text-cool-grey font-semibold mb-3 uppercase">Top Contributors</p>
        {insights.top_volunteers.length > 0 ? (
          <div className="space-y-2">
            {insights.top_volunteers.map((vol, idx) => (
              <div key={idx} className="flex justify-between items-center text-sm">
                <span className="text-deep-navy font-medium">{vol.name}</span>
                <span className="text-emerald-600 font-semibold">{vol.hours}h</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-cool-grey italic">No approved hours yet</p>
        )}
      </div>

      {/* Stats Footer */}
      <div className="border-t border-emerald-200/30 mt-4 pt-3 grid grid-cols-3 gap-2 text-center text-xs">
        <div>
          <p className="text-cool-grey">Approved</p>
          <p className="font-semibold text-deep-navy">{insights.approved_count}</p>
        </div>
        <div>
          <p className="text-cool-grey">Pending</p>
          <p className="font-semibold text-yellow-600">{insights.pending_count}</p>
        </div>
        <div>
          <p className="text-cool-grey">Rejected</p>
          <p className="font-semibold text-red-600">{insights.rejected_count}</p>
        </div>
      </div>
    </div>
  )
}
