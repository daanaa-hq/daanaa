import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { getOrganization, getPortalToken, type ApiOrganization } from '../../data/api'
import { getNteeLabel } from '../../data/ntee'
import { formatEIN } from '../../data/organizations'

// ── Completeness helpers ───────────────────────────────────────────────────────

interface CompletenessField {
  key: string
  label: string
  present: boolean
  fixPath?: string
}

function profileFields(org: ApiOrganization, editPath: string): CompletenessField[] {
  return [
    {
      key: 'mission',
      label: 'Mission statement',
      present: !!org.mission,
      fixPath: editPath,
    },
    {
      key: 'website',
      label: 'Website',
      present: !!(org.website && org.website_status === 'ok'),
      fixPath: editPath,
    },
    {
      key: 'cause_tags',
      label: 'Cause tags',
      present: !!(org.cause_tags && org.cause_tags.length > 0),
      fixPath: editPath,
    },
    {
      key: 'donate_url',
      label: 'Donation link',
      // donate_url not in the public ApiOrganization type, so we check via cast
      present: !!((org as unknown as Record<string, unknown>).donate_url),
      fixPath: editPath,
    },
  ]
}

function completenessPercent(fields: CompletenessField[]): number {
  const done = fields.filter(f => f.present).length
  return Math.round((done / fields.length) * 100)
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function ProfileCompletenessPanel({ org, editPath }: { org: ApiOrganization; editPath: string }) {
  const fields = profileFields(org, editPath)
  const pct = completenessPercent(fields)
  return (
    <div className="bg-white rounded-2xl border border-light-grey p-6 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="font-body text-[15px] font-semibold text-deep-navy">Profile</h2>
        <span className="font-body text-[12px] font-medium text-cool-grey">{pct}% complete</span>
      </div>
      {/* Progress bar */}
      <div className="h-1.5 rounded-full bg-light-grey overflow-hidden">
        <div
          className="h-full rounded-full bg-soft-gold transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      {/* Field checklist */}
      <ul className="space-y-2">
        {fields.map(f => (
          <li key={f.key} className="flex items-center gap-2.5">
            <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[11px] shrink-0 ${
              f.present ? 'bg-emerald-100 text-emerald-700' : 'bg-red-50 text-red-500'
            }`}>
              {f.present ? '✓' : '✗'}
            </span>
            <span className={`font-body text-[13px] ${f.present ? 'text-deep-navy' : 'text-cool-grey'}`}>
              {f.label}
            </span>
            {!f.present && f.fixPath && (
              <Link
                to={f.fixPath}
                className="ml-auto font-body text-[11px] text-soft-gold hover:underline"
              >
                Add →
              </Link>
            )}
          </li>
        ))}
      </ul>
      <Link
        to={editPath}
        className="w-full mt-1 px-4 py-2.5 rounded-xl bg-soft-gold text-deep-navy text-center font-body text-[13px] font-semibold hover:bg-bright-gold transition-colors"
      >
        Edit profile
      </Link>
    </div>
  )
}

function VolunteerHoursPanel({ ein, pendingCount }: { ein: string; pendingCount: number | null }) {
  return (
    <div className="bg-white rounded-2xl border border-light-grey p-6 flex flex-col gap-4">
      <h2 className="font-body text-[15px] font-semibold text-deep-navy">Volunteer hours</h2>
      {pendingCount === null ? (
        <div className="h-8 bg-light-grey rounded animate-pulse" />
      ) : (
        <div className="flex items-baseline gap-2">
          <span className="font-display italic text-deep-navy text-[32px]">{pendingCount}</span>
          <span className="font-body text-[14px] text-cool-grey">pending review</span>
        </div>
      )}
      {pendingCount !== null && pendingCount > 0 && (
        <p className="font-body text-[13px] text-amber-700 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
          {pendingCount} volunteer{pendingCount !== 1 ? 's' : ''} logged hours and need your confirmation.
        </p>
      )}
      <Link
        to={`/nonprofit/verify-hours`}
        className="w-full px-4 py-2.5 rounded-xl border border-light-grey text-deep-navy text-center font-body text-[13px] font-medium hover:border-soft-gold/40 transition-colors"
      >
        Review hours
      </Link>
    </div>
  )
}

function PublicProfilePanel({ org }: { org: ApiOrganization }) {
  const healthSignal = (org.v5_context?.score?.health_signal) ?? null
  const score = org.v5_context?.score?.percentile ?? org.merit_score ?? null

  const healthMap: Record<string, { label: string; classes: string }> = {
    HEALTHY: { label: 'Financially healthy',  classes: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
    STABLE:  { label: 'Financially stable',   classes: 'bg-blue-50 text-blue-700 border-blue-200' },
    CAUTION: { label: 'Needs community support', classes: 'bg-amber-50 text-amber-700 border-amber-200' },
  }
  const healthCfg = healthSignal ? (healthMap[healthSignal] ?? null) : null

  return (
    <div className="bg-white rounded-2xl border border-light-grey p-6">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <h2 className="font-body text-[15px] font-semibold text-deep-navy">Public profile</h2>
          <p className="font-body text-[13px] text-cool-grey mt-0.5">
            How donors see your organization
          </p>
        </div>
        <Link
          to={`/org/${org.EIN}`}
          target="_blank"
          rel="noopener noreferrer"
          className="shrink-0 px-3 py-1.5 rounded-xl border border-light-grey text-cool-grey font-body text-[12px] font-medium hover:border-soft-gold/40 hover:text-deep-navy transition-colors"
        >
          View ↗
        </Link>
      </div>

      <div className="flex flex-wrap gap-2 items-center">
        {healthCfg && (
          <span className={`inline-flex items-center px-3 py-1 rounded-full font-body text-[12px] font-semibold border ${healthCfg.classes}`}>
            {healthCfg.label}
          </span>
        )}
        {score !== null && (
          <span className="inline-flex items-center px-3 py-1 rounded-full bg-soft-gold/15 border border-soft-gold/30 font-body text-[12px] font-semibold text-deep-navy">
            Score: {Math.round(score)}/100
          </span>
        )}
        {!healthCfg && !score && (
          <span className="font-body text-[13px] text-cool-grey">
            Financial context pending — add your latest 990 filing to unlock.
          </span>
        )}
      </div>
    </div>
  )
}

// ── Page ───────────────────────────────────────────────────────────────────────

interface ViewStats {
  views_total: number
  views_30d: number
  views_7d: number
  wallet_saves: number
}

function AnalyticsPanel({ stats }: { stats: ViewStats | null }) {
  const metrics = [
    { label: 'Page views this week', value: stats?.views_7d ?? null },
    { label: 'Page views this month', value: stats?.views_30d ?? null },
    { label: 'Donors who saved your page', value: stats?.wallet_saves ?? null },
  ]
  return (
    <div className="bg-white rounded-2xl border border-light-grey p-6">
      <h2 className="font-body text-[15px] font-semibold text-deep-navy mb-4">Your reach</h2>
      <div className="grid grid-cols-3 gap-4">
        {metrics.map(m => (
          <div key={m.label} className="text-center">
            {m.value === null ? (
              <div className="h-8 bg-light-grey rounded animate-pulse mx-auto w-12" />
            ) : (
              <p className="font-display italic text-deep-navy text-[28px] leading-none">{m.value.toLocaleString()}</p>
            )}
            <p className="font-body text-[11px] text-cool-grey mt-1.5 leading-snug">{m.label}</p>
          </div>
        ))}
      </div>
      {stats && stats.views_30d === 0 && stats.wallet_saves === 0 && (
        <p className="font-body text-[12px] text-cool-grey mt-4 text-center">
          Numbers build as donors discover your page. A complete profile helps you show up in more searches.
        </p>
      )}
    </div>
  )
}

export default function NonprofitDashboardPage() {
  const { ein } = useParams<{ ein: string }>()
  const navigate = useNavigate()
  const { getIdToken, signOut } = useAuth()

  const [org, setOrg] = useState<ApiOrganization | null>(null)
  const [editToken, setEditToken] = useState<string | null>(null)
  const [pendingHours, setPendingHours] = useState<number | null>(null)
  const [viewStats, setViewStats] = useState<ViewStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!ein) return

    async function load() {
      try {
        const idToken = await getIdToken()
        if (!idToken) {
          navigate('/nonprofit/login', { replace: true })
          return
        }

        const base = import.meta.env.VITE_API_URL || 'http://localhost:5000'

        // Load in parallel: org data + portal token + pending hours + view stats
        const [orgData, token, hoursRes, statsRes] = await Promise.allSettled([
          getOrganization(ein!),
          getPortalToken(ein!, idToken),
          fetch(`${base}/api/nonprofit/hours-pending`, {
            headers: { Authorization: `Bearer ${idToken}` },
          }).then(r => r.json()),
          fetch(`${base}/api/org/${ein}/view-stats`, {
            headers: { Authorization: `Bearer ${idToken}` },
          }).then(r => r.ok ? r.json() : null),
        ])

        if (orgData.status === 'fulfilled') {
          setOrg(orgData.value)
        } else {
          setError('Organization not found.')
          setLoading(false)
          return
        }

        if (token.status === 'fulfilled') {
          setEditToken(token.value)
        }
        // token failure is non-fatal — edit button will be disabled

        if (hoursRes.status === 'fulfilled') {
          const data = hoursRes.value
          const count = typeof data.total === 'number'
            ? data.total
            : (Array.isArray(data.hours) ? data.hours.length : 0)
          setPendingHours(count)
        } else {
          setPendingHours(0)
        }

        if (statsRes.status === 'fulfilled' && statsRes.value) {
          setViewStats(statsRes.value as ViewStats)
        } else {
          setViewStats({ views_total: 0, views_30d: 0, views_7d: 0, wallet_saves: 0 })
        }
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : ''
        if (msg.includes('401')) {
          await signOut()
          navigate('/nonprofit/login', { replace: true })
        } else {
          setError('Something went wrong. Please try again.')
        }
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [ein, getIdToken, navigate, signOut])

  const editPath = editToken && ein
    ? `/claim/edit?ein=${encodeURIComponent(ein)}&token=${encodeURIComponent(editToken)}`
    : `/claim/edit?ein=${encodeURIComponent(ein ?? '')}`

  if (loading) {
    return (
      <div className="min-h-[100dvh] bg-warm-cream flex items-center justify-center">
        <div className="w-6 h-6 rounded-full border-2 border-soft-gold border-t-transparent animate-spin" />
      </div>
    )
  }

  if (error || !org) {
    return (
      <div className="min-h-[100dvh] bg-warm-cream flex items-center justify-center px-6">
        <div className="text-center">
          <div className="text-4xl mb-4">🏢</div>
          <h1 className="font-display italic text-deep-navy text-[22px] mb-3">
            {error ?? 'Organization not found'}
          </h1>
          <Link
            to="/nonprofit/my-orgs"
            className="font-body text-[14px] text-soft-gold hover:underline"
          >
            ← Back to my organizations
          </Link>
        </div>
      </div>
    )
  }

  const location = [org.CITY, org.STATE].filter(Boolean).join(', ')
  const nteeLabel = org.NTEECC ? getNteeLabel(org.NTEECC) : null

  return (
    <div className="min-h-[100dvh] bg-warm-cream">
      {/* Top bar */}
      <div className="border-b border-light-grey bg-white">
        <div className="max-w-[760px] mx-auto px-6 py-4 flex items-center justify-between">
          <Link
            to="/nonprofit/my-orgs"
            className="flex items-center gap-1.5 font-body text-[13px] text-cool-grey hover:text-deep-navy transition-colors"
          >
            ← My organizations
          </Link>
          <Link to="/" className="font-display italic text-deep-navy text-[15px]">Daanaa</Link>
        </div>
      </div>

      {/* Page content */}
      <div className="max-w-[760px] mx-auto px-6 py-10">
        {/* Org header */}
        <div className="mb-8">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-12 h-12 rounded-full bg-soft-gold/15 flex items-center justify-center text-2xl">
              🏢
            </div>
            <div className="min-w-0">
              <h1 className="font-display italic text-deep-navy text-[26px] leading-tight">
                {org.organization_name}
              </h1>
              <p className="font-body text-[14px] text-cool-grey mt-1">
                {[location, nteeLabel, org.EIN ? `EIN: ${formatEIN(org.EIN)}` : null]
                  .filter(Boolean)
                  .join(' · ')}
              </p>
            </div>
          </div>

          {/* Status badge */}
          {org.claim_status && (
            <div className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-50 border border-emerald-200">
              <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" />
              <span className="font-body text-[12px] font-semibold text-emerald-700 capitalize">
                {org.claim_status === 'active' ? 'Active' : org.claim_status}
              </span>
            </div>
          )}
        </div>

        {/* Two-column panels */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
          <ProfileCompletenessPanel org={org} editPath={editPath} />
          <VolunteerHoursPanel ein={org.EIN} pendingCount={pendingHours} />
        </div>

        {/* Public profile panel — full width */}
        <PublicProfilePanel org={org} />

        {/* Analytics panel */}
        <div className="mt-4">
          <AnalyticsPanel stats={viewStats} />
        </div>

        {/* Quick actions */}
        <div className="mt-4 bg-white rounded-2xl border border-light-grey p-6">
          <h2 className="font-body text-[15px] font-semibold text-deep-navy mb-4">Quick actions</h2>
          <div className="flex flex-wrap gap-3">
            <Link
              to={editPath}
              className="px-4 py-2.5 rounded-xl bg-soft-gold text-deep-navy font-body text-[13px] font-semibold hover:bg-bright-gold transition-colors"
            >
              Edit profile
            </Link>
            <Link
              to="/nonprofit/verify-hours"
              className="px-4 py-2.5 rounded-xl border border-light-grey text-deep-navy font-body text-[13px] font-medium hover:border-soft-gold/40 transition-colors"
            >
              Review volunteer hours
            </Link>
            <Link
              to={`/org/${org.EIN}`}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2.5 rounded-xl border border-light-grey text-cool-grey font-body text-[13px] font-medium hover:border-soft-gold/40 hover:text-deep-navy transition-colors"
            >
              View on Daanaa ↗
            </Link>
            <button
              disabled
              title="Coming soon"
              className="px-4 py-2.5 rounded-xl border border-light-grey text-muted-cream font-body text-[13px] font-medium cursor-not-allowed opacity-50"
            >
              Share profile
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
