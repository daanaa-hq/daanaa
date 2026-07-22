import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { usePageMeta } from '../../hooks/usePageMeta'
import { API_BASE } from '../../data/api'
import VolunteerExportButton from '../../components/VolunteerExportButton'

interface ImpactData {
  ein: string
  year: number
  total_hours_approved: number
  volunteer_count: number
  event_count: number
  labor_value_estimate: number
  hours_by_task_type: Record<string, number>
  hours_by_month: Record<string, number>
  is_public: boolean
}

const MONTH_LABELS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

export default function VolunteerImpactPage() {
  const { ein } = useParams<{ ein: string }>()
  const navigate = useNavigate()
  const { getIdToken } = useAuth()
  const [year] = useState(new Date().getFullYear())
  usePageMeta('Volunteer Impact | Daanaa', 'Your organization\'s yearly volunteer hours and impact.')

  const [data, setData] = useState<ImpactData | null>(null)
  const [idToken, setIdToken] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [updatingVisibility, setUpdatingVisibility] = useState(false)

  const fetchImpact = useCallback(async () => {
    if (!ein) return
    try {
      const token = await getIdToken()
      if (!token) {
        navigate('/nonprofit/login', { replace: true })
        return
      }
      setIdToken(token)
      const res = await fetch(`${API_BASE}/api/nonprofit/${ein}/volunteer/impact/${year}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('Failed to load impact data')
      setData(await res.json())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }, [ein, year, getIdToken, navigate])

  useEffect(() => { fetchImpact() }, [fetchImpact])

  async function toggleVisibility() {
    if (!data || !ein) return
    setUpdatingVisibility(true)
    try {
      const res = await fetch(`${API_BASE}/api/nonprofit/${ein}/volunteer/impact/${year}/visibility`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${idToken}` },
        body: JSON.stringify({ is_public: !data.is_public }),
      })
      if (!res.ok) throw new Error('Failed to update visibility')
      setData(prev => (prev ? { ...prev, is_public: !prev.is_public } : prev))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update visibility')
    } finally {
      setUpdatingVisibility(false)
    }
  }

  if (!ein) return null

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-warm-cream">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-deep-navy" />
      </div>
    )
  }

  const maxMonthHours = data ? Math.max(1, ...Object.values(data.hours_by_month)) : 1

  return (
    <div className="min-h-screen bg-warm-cream">
      <div className="bg-deep-navy py-8 px-6">
        <div className="max-w-[900px] mx-auto">
          <Link to={`/nonprofit/events/${ein}`} className="font-body text-[13px] text-muted-cream hover:text-warm-cream">← Volunteer events</Link>
          <h1 className="font-display italic text-warm-cream mt-3 text-[36px]">Volunteer Impact — {year}</h1>
        </div>
      </div>

      <div className="max-w-[900px] mx-auto px-6 py-10 space-y-6">
        {error && <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 font-body text-[14px]">{error}</div>}

        {data && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Total Hours', value: data.total_hours_approved.toLocaleString() },
                { label: 'Volunteers', value: data.volunteer_count.toLocaleString() },
                { label: 'Events', value: data.event_count.toLocaleString() },
                { label: 'Labor Value', value: `$${data.labor_value_estimate.toLocaleString()}` },
              ].map(stat => (
                <div key={stat.label} className="bg-white rounded-2xl border border-light-grey p-5 text-center">
                  <p className="font-display text-[28px] text-deep-navy">{stat.value}</p>
                  <p className="font-body text-[12px] text-cool-grey mt-1">{stat.label}</p>
                </div>
              ))}
            </div>

            <div className="bg-white rounded-2xl border border-light-grey p-6">
              <h2 className="font-body text-[14px] font-semibold text-deep-navy uppercase tracking-wide mb-4">Hours by month</h2>
              <div className="flex items-end gap-2 h-32">
                {MONTH_LABELS.map((label, i) => {
                  const monthKey = String(i + 1).padStart(2, '0')
                  const hours = data.hours_by_month[monthKey] || 0
                  const heightPct = Math.max(2, (hours / maxMonthHours) * 100)
                  return (
                    <div key={label} className="flex-1 flex flex-col items-center gap-1">
                      <div className="w-full bg-soft-gold/70 rounded-t" style={{ height: `${heightPct}%` }} title={`${hours}h`} />
                      <span className="font-body text-[10px] text-cool-grey">{label}</span>
                    </div>
                  )
                })}
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-light-grey p-6">
              <h2 className="font-body text-[14px] font-semibold text-deep-navy uppercase tracking-wide mb-4">By role</h2>
              <div className="space-y-2">
                {Object.entries(data.hours_by_task_type).sort((a, b) => b[1] - a[1]).map(([task, hours]) => (
                  <div key={task} className="flex items-center justify-between">
                    <span className="font-body text-[13px] text-deep-navy capitalize">{task.replace('_', ' ')}</span>
                    <span className="font-body text-[13px] font-semibold text-deep-navy">{hours}h</span>
                  </div>
                ))}
                {Object.keys(data.hours_by_task_type).length === 0 && (
                  <p className="font-body text-[13px] text-cool-grey">No approved hours yet this year.</p>
                )}
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-light-grey p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h2 className="font-body text-[14px] font-semibold text-deep-navy">Show on your public Daanaa page?</h2>
                <p className="font-body text-[13px] text-cool-grey mt-1 max-w-md">
                  Only your total hours and volunteer count would show — never individual names or emails.
                </p>
              </div>
              <button
                onClick={toggleVisibility}
                disabled={updatingVisibility}
                className={`px-5 py-2.5 rounded-xl font-body text-[14px] font-semibold transition-colors disabled:opacity-50 ${
                  data.is_public ? 'bg-emerald-100 text-emerald-700' : 'bg-light-grey text-deep-navy'
                }`}
              >
                {data.is_public ? 'Public ✓' : 'Private'}
              </button>
            </div>

            <div className="bg-white rounded-2xl border border-light-grey p-6">
              <h2 className="font-body text-[14px] font-semibold text-deep-navy uppercase tracking-wide mb-3">Export for your records</h2>
              <p className="font-body text-[12px] text-cool-grey mb-4">
                These hours were approved by your staff. Daanaa does not independently verify volunteer hours — exports are labeled accordingly for tax and grant filings.
              </p>
              <div className="flex gap-3">
                <VolunteerExportButton nonprofitEin={ein} idToken={idToken} format="csv" year={year} />
                <VolunteerExportButton nonprofitEin={ein} idToken={idToken} format="pdf" year={year} />
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
