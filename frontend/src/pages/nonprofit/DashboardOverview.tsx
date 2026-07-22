import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { usePageMeta } from '../../hooks/usePageMeta'
import { API_BASE } from '../../data/api'

interface DashboardData {
  organization: {
    ein: string
    name: string
    mission?: string
    website?: string
    last_profile_update?: string
    days_since_update: number
  }
  attention: {
    pending_approvals: number
    profile_gaps: number
    missing_fields: string[]
    needs_review: boolean
  }
  volunteer_summary: {
    this_month_hours: number
    last_month_hours: number
    trend_percent: number
    pending_count: number
    approved_count: number
    rejected_count: number
    top_volunteers: Array<{ name: string; hours: number }>
    labor_value_this_month: number
  }
  profile_health: {
    completeness_percent: number
    missing_fields: string[]
  }
  upcoming_events: Array<{
    event_id: number
    title: string
    date: string
    days_until: number
  }>
  recent_activity: {
    has_events: boolean
  }
}

export default function DashboardOverview() {
  const { ein } = useParams<{ ein: string }>()
  const navigate = useNavigate()
  const { user, loading: authLoading } = useAuth()
  usePageMeta(
    'Nonprofit Dashboard | Daanaa',
    'Manage your organization, approve volunteer hours, and track impact.'
  )

  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (authLoading || !user) return
    if (!ein) {
      navigate('/nonprofit/my-orgs', { replace: true })
      return
    }

    fetch(`${API_BASE}/api/nonprofit/${ein}/dashboard/overview`)
      .then(async res => {
        if (!res.ok) {
          const body = await res.json().catch(() => ({}))
          throw new Error(body.error || 'Failed to load dashboard')
        }
        return res.json()
      })
      .then(setDashboard)
      .catch(err => setError(err instanceof Error ? err.message : 'Could not load dashboard'))
      .finally(() => setLoading(false))
  }, [ein, user, authLoading, navigate])

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-warm-cream">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-deep-navy" />
      </div>
    )
  }

  if (error || !dashboard) {
    return (
      <div className="min-h-screen bg-warm-cream px-6 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-red-700">
            <h2 className="font-display text-lg mb-2">Could not load dashboard</h2>
            <p className="font-body text-[14px] mb-4">{error}</p>
            <button
              onClick={() => navigate('/nonprofit/my-orgs')}
              className="px-4 py-2 bg-red-100 hover:bg-red-200 rounded-lg font-body text-[14px] font-semibold transition"
            >
              Back to Organizations
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-warm-cream px-6 py-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="font-display text-3xl text-deep-navy mb-1">{dashboard.organization.name}</h1>
          <p className="font-body text-[14px] text-cool-grey">EIN: {dashboard.organization.ein}</p>
        </div>

        {/* Attention Alert */}
        {(dashboard.attention.pending_approvals > 0 || dashboard.attention.profile_gaps > 0) && (
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6">
            <div className="flex items-start gap-3">
              <span className="text-2xl">⚠️</span>
              <div className="flex-1">
                <h2 className="font-display text-lg text-amber-900 mb-3">Items needing attention</h2>
                <div className="space-y-2">
                  {dashboard.attention.pending_approvals > 0 && (
                    <div className="flex items-center justify-between bg-white/50 p-3 rounded-lg">
                      <span className="font-body text-[14px] text-deep-navy">
                        🕐 {dashboard.attention.pending_approvals} volunteer hour{dashboard.attention.pending_approvals !== 1 ? 's' : ''} awaiting approval
                      </span>
                      <button
                        onClick={() => navigate(`/nonprofit/volunteer-approval/${ein}`)}
                        className="text-[12px] font-semibold text-amber-700 hover:text-amber-900 transition"
                      >
                        Review Now →
                      </button>
                    </div>
                  )}
                  {dashboard.attention.profile_gaps > 0 && (
                    <div className="flex items-center justify-between bg-white/50 p-3 rounded-lg">
                      <span className="font-body text-[14px] text-deep-navy">
                        📝 {dashboard.attention.profile_gaps} profile field{dashboard.attention.profile_gaps !== 1 ? 's' : ''} to complete
                      </span>
                      <button
                        onClick={() => navigate(`/nonprofit/profile/${ein}`)}
                        className="text-[12px] font-semibold text-amber-700 hover:text-amber-900 transition"
                      >
                        Edit Profile →
                      </button>
                    </div>
                  )}
                  {dashboard.attention.needs_review && (
                    <div className="flex items-center justify-between bg-white/50 p-3 rounded-lg">
                      <span className="font-body text-[14px] text-deep-navy">
                        ⏰ Profile last updated {dashboard.organization.days_since_update} days ago
                      </span>
                      <button
                        onClick={() => navigate(`/nonprofit/profile/${ein}`)}
                        className="text-[12px] font-semibold text-amber-700 hover:text-amber-900 transition"
                      >
                        Review →
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Main Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Volunteer Summary */}
          <div className="bg-white rounded-2xl shadow-sm p-6">
            <h2 className="font-body text-[12px] font-semibold text-deep-navy uppercase tracking-wide mb-4">
              This Month's Volunteer Hours
            </h2>
            <div className="space-y-4">
              <div>
                <div className="flex items-baseline justify-between mb-1">
                  <span className="font-display text-3xl text-deep-navy">
                    {dashboard.volunteer_summary.this_month_hours}
                  </span>
                  <span className="font-body text-[12px] text-cool-grey">hours</span>
                </div>
                <span className="font-body text-[12px] text-cool-grey">
                  Value: ${dashboard.volunteer_summary.labor_value_this_month.toLocaleString()}
                </span>
              </div>

              {dashboard.volunteer_summary.last_month_hours > 0 && (
                <div className="pt-3 border-t border-light-grey">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">
                      {dashboard.volunteer_summary.trend_percent > 0 ? '📈' : dashboard.volunteer_summary.trend_percent < 0 ? '📉' : '➡️'}
                    </span>
                    <span className="font-body text-[13px]">
                      {dashboard.volunteer_summary.trend_percent > 0 ? '+' : ''}
                      {dashboard.volunteer_summary.trend_percent}% vs last month
                    </span>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-3 gap-2 pt-3 border-t border-light-grey">
                <div className="text-center">
                  <div className="font-display text-xl text-deep-navy">
                    {dashboard.volunteer_summary.pending_count}
                  </div>
                  <div className="font-body text-[11px] text-cool-grey">Pending</div>
                </div>
                <div className="text-center">
                  <div className="font-display text-xl text-emerald-600">
                    {dashboard.volunteer_summary.approved_count}
                  </div>
                  <div className="font-body text-[11px] text-cool-grey">Approved</div>
                </div>
                <div className="text-center">
                  <div className="font-display text-xl text-red-600">
                    {dashboard.volunteer_summary.rejected_count}
                  </div>
                  <div className="font-body text-[11px] text-cool-grey">Rejected</div>
                </div>
              </div>

              {dashboard.volunteer_summary.top_volunteers.length > 0 && (
                <div className="pt-3 border-t border-light-grey">
                  <div className="font-body text-[11px] font-semibold text-cool-grey uppercase mb-2">Top Volunteers</div>
                  <div className="space-y-1">
                    {dashboard.volunteer_summary.top_volunteers.map(vol => (
                      <div key={vol.name} className="flex justify-between items-center">
                        <span className="font-body text-[13px] text-deep-navy">{vol.name}</span>
                        <span className="font-body text-[12px] text-cool-grey">{vol.hours}h</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <button
                onClick={() => navigate(`/nonprofit/volunteer-approval/${ein}`)}
                className="w-full mt-3 py-2 rounded-lg bg-soft-gold text-deep-navy font-body text-[13px] font-semibold hover:bg-bright-gold transition"
              >
                Manage Approvals
              </button>
            </div>
          </div>

          {/* Profile Health */}
          <div className="bg-white rounded-2xl shadow-sm p-6">
            <h2 className="font-body text-[12px] font-semibold text-deep-navy uppercase tracking-wide mb-4">
              Profile Completeness
            </h2>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-display text-3xl text-deep-navy">
                    {dashboard.profile_health.completeness_percent}%
                  </span>
                  <span className="font-body text-[12px] text-cool-grey">complete</span>
                </div>
                <div className="w-full bg-light-grey rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-soft-gold to-bright-gold h-2 rounded-full transition-all"
                    style={{ width: `${dashboard.profile_health.completeness_percent}%` }}
                  />
                </div>
              </div>

              {dashboard.profile_health.missing_fields.length > 0 && (
                <div className="pt-3 border-t border-light-grey">
                  <div className="font-body text-[11px] font-semibold text-cool-grey uppercase mb-2">Missing or Incomplete</div>
                  <div className="space-y-1">
                    {dashboard.profile_health.missing_fields.map(field => (
                      <div key={field} className="flex items-center gap-2">
                        <span className="text-amber-600">◆</span>
                        <span className="font-body text-[13px] text-deep-navy capitalize">{field.replace('_', ' ')}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <button
                onClick={() => navigate(`/nonprofit/profile/${ein}`)}
                className="w-full mt-3 py-2 rounded-lg bg-soft-gold text-deep-navy font-body text-[13px] font-semibold hover:bg-bright-gold transition"
              >
                Edit Profile
              </button>
            </div>
          </div>
        </div>

        {/* Upcoming Events */}
        {dashboard.upcoming_events.length > 0 && (
          <div className="bg-white rounded-2xl shadow-sm p-6">
            <h2 className="font-body text-[12px] font-semibold text-deep-navy uppercase tracking-wide mb-4">
              Upcoming Events (Next 30 Days)
            </h2>
            <div className="space-y-3">
              {dashboard.upcoming_events.map(evt => (
                <div key={evt.event_id} className="flex items-center justify-between p-3 bg-light-grey/30 rounded-xl">
                  <div>
                    <div className="font-body text-[14px] font-semibold text-deep-navy">{evt.title}</div>
                    <div className="font-body text-[12px] text-cool-grey">
                      {new Date(evt.date).toLocaleDateString()} ({evt.days_until} days)
                    </div>
                  </div>
                  <button
                    onClick={() => navigate(`/nonprofit/volunteer-events/${ein}`)}
                    className="text-[12px] font-semibold text-soft-gold hover:text-bright-gold transition"
                  >
                    View →
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4">
          <button
            onClick={() => navigate(`/nonprofit/profile/${ein}`)}
            className="p-4 rounded-xl bg-deep-navy text-warm-cream font-body text-[14px] font-semibold hover:bg-opacity-90 transition text-left"
          >
            📝 Edit Profile
          </button>
          <button
            onClick={() => navigate(`/nonprofit/volunteer-approval/${ein}`)}
            className="p-4 rounded-xl bg-deep-navy text-warm-cream font-body text-[14px] font-semibold hover:bg-opacity-90 transition text-left"
          >
            ✓ Approve Hours
          </button>
          <button
            onClick={() => navigate(`/nonprofit/volunteer-events/${ein}`)}
            className="p-4 rounded-xl bg-deep-navy text-warm-cream font-body text-[14px] font-semibold hover:bg-opacity-90 transition text-left"
          >
            📅 Create Event
          </button>
        </div>
      </div>
    </div>
  )
}
