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
      <div className={`${size === 'small' ? 'p-4' : 'p-6'} bg-light-grey/30 rounded-xl animate-pulse`}>
        <div className="h-4 bg-light-grey rounded w-1/3 mb-2"></div>
      </div>
    )
  }

  if (error || !data) {
    return null
  }

  const hasContent = data.donation_count > 0 || data.volunteer_hours > 0 || data.unique_orgs > 0
  if (!hasContent) return null

  if (size === 'small') {
    return (
      <div className="bg-soft-gold/5 border border-soft-gold/20 rounded-xl p-4">
        <div className="font-body text-[10px] tracking-[0.06em] text-cool-grey uppercase font-semibold mb-3">
          Community impact
        </div>
        <div className="space-y-2">
          {data.donation_count > 0 && (
            <div className="flex justify-between">
              <span className="font-body text-[13px] text-cool-grey">Donors helped here:</span>
              <span className="font-body text-[13px] font-semibold text-deep-navy">{data.donation_count}</span>
            </div>
          )}
          {data.volunteer_hours > 0 && (
            <div className="flex justify-between">
              <span className="font-body text-[13px] text-cool-grey">Volunteer hours:</span>
              <span className="font-body text-[13px] font-semibold text-deep-navy">{Math.round(data.volunteer_hours).toLocaleString()}</span>
            </div>
          )}
          {data.volunteer_value > 0 && (
            <div className="flex justify-between">
              <span className="font-body text-[13px] text-cool-grey">Volunteer value:</span>
              <span className="font-body text-[13px] font-semibold text-deep-navy">${Math.round(data.volunteer_value).toLocaleString()}</span>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white border border-light-grey rounded-xl p-6">
      <div className="mb-6">
        <div className="font-body text-[11px] tracking-[0.06em] text-soft-gold uppercase font-semibold mb-2">
          Daanaa Impact
        </div>
        <h3 className="font-display text-[28px] text-deep-navy">
          {period === 'month' ? 'Last 30 Days' : period === 'year' ? 'Past Year' : period === 'day' ? 'Today' : 'All Time'}
        </h3>
      </div>

      <div className="space-y-5">
        {data.donation_count > 0 && (
          <div className="pb-5 border-b border-light-grey">
            <div className="font-display text-[40px] text-deep-navy mb-1 leading-none">
              {data.donation_count.toLocaleString()}
            </div>
            <p className="font-body text-[13px] text-cool-grey">
              donor{data.donation_count !== 1 ? 's' : ''} confirmed Daanaa helped
            </p>
          </div>
        )}

        {data.volunteer_hours > 0 && (
          <div className="pb-5 border-b border-light-grey">
            <div className="font-display text-[40px] text-deep-navy mb-1 leading-none">
              {Math.round(data.volunteer_hours).toLocaleString()} hrs
            </div>
            <p className="font-body text-[13px] text-cool-grey">
              volunteer hours logged ({data.volunteer_reports} report{data.volunteer_reports !== 1 ? 's' : ''})
            </p>
            <p className="font-body text-[12px] text-cool-grey mt-1">
              About ${Math.round(data.volunteer_value).toLocaleString()} in equivalent value
            </p>
          </div>
        )}

        {!orgEin && data.unique_orgs > 0 && (
          <div>
            <div className="font-display text-[40px] text-deep-navy mb-1 leading-none">
              {data.unique_orgs.toLocaleString()}
            </div>
            <p className="font-body text-[13px] text-cool-grey">
              nonprofit{data.unique_orgs !== 1 ? 's' : ''} served
            </p>
          </div>
        )}

        {data.last_updated && (
          <p className="font-body text-[11px] text-cool-grey pt-2">
            Updated {new Date(data.last_updated).toLocaleDateString()}
          </p>
        )}
      </div>

      <div className="mt-6 font-body text-[11px] text-cool-grey leading-relaxed border-t border-light-grey pt-4">
        Donations are self-reported by donors. Volunteer hours are reported by nonprofits and valued at $28.50/hour (BLS average service rate).
      </div>
    </div>
  )
}
