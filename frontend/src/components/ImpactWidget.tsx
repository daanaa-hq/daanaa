import { useEffect, useState } from 'react'

interface ImpactData {
  period: string
  donation_attributed: number
  donation_count: number
  volunteer_hours: number
  volunteer_reports: number
  volunteer_value: number
  partnership_savings: number
  unique_orgs: number
  last_updated?: string
}

interface ImpactWidgetProps {
  period?: 'day' | 'month' | 'year' | 'all'
  orgEin?: string
  size?: 'small' | 'large'
}

export default function ImpactWidget({ period = 'month', orgEin, size = 'large' }: ImpactWidgetProps) {
  const [data, setData] = useState<ImpactData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchImpact = async () => {
      try {
        const params = new URLSearchParams()
        params.append('period', period)
        if (orgEin) params.append('org_ein', orgEin)

        const response = await fetch(`/api/impact/summary?${params}`)
        if (response.ok) {
          const result = await response.json()
          setData(result)
        } else {
          setError('Unable to load impact data')
        }
      } catch (err) {
        console.error('Error fetching impact data:', err)
        setError('Unable to load impact data')
      } finally {
        setLoading(false)
      }
    }

    fetchImpact()
  }, [period, orgEin])

  if (loading) {
    return (
      <div className={`${size === 'small' ? 'p-4' : 'p-6'} bg-slate-50 rounded-lg animate-pulse`}>
        <div className="h-4 bg-slate-200 rounded w-1/3 mb-2"></div>
      </div>
    )
  }

  if (error || !data) {
    return null
  }

  if (size === 'small') {
    return (
      <div className="bg-soft-gold/5 border border-soft-gold/20 rounded-lg p-4 text-sm">
        <div className="text-xs text-cool-grey uppercase tracking-wide font-medium mb-3">
          Impact ({period})
        </div>
        <div className="space-y-2 text-sm">
          {data.donation_count > 0 && (
            <div className="flex justify-between">
              <span className="text-cool-grey">Donors helped find us:</span>
              <span className="font-semibold text-deep-navy">{data.donation_count}</span>
            </div>
          )}
          {data.volunteer_hours > 0 && (
            <div className="flex justify-between">
              <span className="text-cool-grey">Volunteer hours:</span>
              <span className="font-semibold text-deep-navy">{Math.round(data.volunteer_hours)}</span>
            </div>
          )}
          {data.volunteer_value > 0 && (
            <div className="flex justify-between">
              <span className="text-cool-grey">Volunteer value:</span>
              <span className="font-semibold text-deep-navy">${Math.round(data.volunteer_value).toLocaleString()}</span>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white border border-light-grey rounded-xl p-6">
      <div className="mb-6">
        <div className="text-xs text-soft-gold uppercase tracking-wider font-semibold mb-2">
          Daanaa Impact
        </div>
        <h3 className="text-2xl font-display text-deep-navy">
          {period === 'month' ? 'Last 30 Days' : period === 'year' ? 'Past Year' : period === 'day' ? 'Today' : 'All Time'}
        </h3>
      </div>

      <div className="space-y-5">
        {data.donation_count > 0 && (
          <div className="pb-5 border-b border-light-grey">
            <div className="text-3xl font-display text-deep-navy mb-2">
              {data.donation_count.toLocaleString()}
            </div>
            <p className="text-sm text-cool-grey">
              donor{data.donation_count !== 1 ? 's' : ''} confirmed Daanaa helped
            </p>
          </div>
        )}

        {data.volunteer_hours > 0 && (
          <div className="pb-5 border-b border-light-grey">
            <div className="text-3xl font-display text-deep-navy mb-2">
              {Math.round(data.volunteer_hours).toLocaleString()} hours
            </div>
            <p className="text-sm text-cool-grey">
              volunteer hours logged ({data.volunteer_reports} report{data.volunteer_reports !== 1 ? 's' : ''})
            </p>
            <p className="text-xs text-slate-500 mt-2">
              ≈ ${Math.round(data.volunteer_value).toLocaleString()} equivalent value
            </p>
          </div>
        )}

        {!orgEin && data.unique_orgs > 0 && (
          <div>
            <div className="text-3xl font-display text-deep-navy mb-2">
              {data.unique_orgs.toLocaleString()}
            </div>
            <p className="text-sm text-cool-grey">
              nonprofit{data.unique_orgs !== 1 ? 's' : ''} served
            </p>
          </div>
        )}

        {data.last_updated && (
          <p className="text-xs text-slate-400 pt-2">
            Updated {new Date(data.last_updated).toLocaleDateString()}
          </p>
        )}
      </div>

      <div className="mt-6 text-xs text-slate-500 leading-relaxed">
        <p>
          ℹ️ <strong>Methodology:</strong> Donations are self-reported by donors. Volunteer hours are reported by nonprofits, valued at $28.50/hour (BLS avg service rate).
        </p>
      </div>
    </div>
  )
}
