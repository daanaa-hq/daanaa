import React, { useState, useEffect } from 'react'

interface MetricCard {
  title: string
  value: string | number
  subtitle: string
  trend?: 'up' | 'down' | 'stable'
}

interface ImpactForecastProps {
  nonprofitEin: string
  authToken: string
}

export default function ImpactForecast({
  nonprofitEin,
  authToken,
}: ImpactForecastProps) {
  const [metrics, setMetrics] = useState<MetricCard[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const res = await fetch('/api/nonprofit/dashboard/impact', {
          headers: { 'Authorization': `Bearer ${authToken}` },
        })
        if (!res.ok) throw new Error('Failed to load metrics')
        const data = await res.json()

        const cards: MetricCard[] = [
          {
            title: 'Letter Credits Used',
            value: data.credit_utilization?.used || 0,
            subtitle: `of ${data.credit_utilization?.total || 0} available`,
            trend: 'up',
          },
          {
            title: 'Donor Engagement',
            value: `${data.donor_engagement?.avg_open_rate || 0}%`,
            subtitle: 'avg open rate',
            trend: 'up',
          },
          {
            title: 'Volunteer Hours',
            value: data.volunteer_impact?.total_hours || 0,
            subtitle: 'hours logged',
            trend: 'up',
          },
          {
            title: 'Revenue Equivalent',
            value: `$${(data.revenue_equivalent?.total_cents || 0) / 100}`,
            subtitle: 'estimated value',
            trend: 'up',
          },
        ]

        setMetrics(cards)
      } catch (err) {
        setError((err as Error).message)
      } finally {
        setLoading(false)
      }
    }

    fetchMetrics()
  }, [authToken])

  if (loading) return <div className="text-center">Loading impact metrics...</div>
  if (error) return <div className="text-red-600 text-sm">{error}</div>

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {metrics.map((card, idx) => (
        <div
          key={idx}
          className="bg-white rounded-lg p-4 border border-light-grey hover:shadow-md transition-shadow"
        >
          <p className="text-xs text-cool-grey font-semibold mb-1">{card.title}</p>
          <p className="font-display text-2xl text-deep-navy mb-1">{card.value}</p>
          <p className="text-xs text-cool-grey">{card.subtitle}</p>
          {card.trend && (
            <p className="text-xs mt-2">
              {card.trend === 'up' && '📈'}
              {card.trend === 'down' && '📉'}
              {card.trend === 'stable' && '➡️'}
            </p>
          )}
        </div>
      ))}
    </div>
  )
}
