import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { useAuth } from '../contexts/AuthContext'

/**
 * RETIRED legacy volunteer-hours verification dashboard (2026-07-22).
 *
 * This page read from the old volunteer_hour_logs store, which drifted from
 * the canonical volunteer_hours table and could double-count hours. The
 * backend endpoints it used now return 410. The canonical flow is
 * /nonprofit/volunteer-approval/:ein (reached via My Organizations), which
 * carries the audit trail, the 30-day edit lock, and the single approval
 * bridge into public impact totals.
 *
 * Kept as a signpost so old bookmarks land somewhere helpful.
 */
export default function NonprofitVerification() {
  usePageMeta(
    'Volunteer Hours Approval Has Moved | Daanaa',
    'Volunteer hour approval now lives in your organization dashboard.'
  )
  const { user, loading } = useAuth()
  const navigate = useNavigate()

  // Signed-in nonprofits go straight to their orgs list, where each org
  // links to its volunteer approval dashboard.
  useEffect(() => {
    if (!loading && user) navigate('/nonprofit/my-orgs', { replace: true })
  }, [user, loading, navigate])

  return (
    <div className="min-h-screen flex items-center justify-center bg-warm-cream px-6">
      <div className="max-w-md text-center bg-white p-8 rounded-2xl shadow-sm">
        <h1 className="font-display text-2xl text-deep-navy mb-3">This page has moved</h1>
        <p className="font-body text-body text-cool-grey mb-6">
          Volunteer hour approval now lives inside your organization dashboard,
          with a full audit trail and pending, approved, and rejected views.
        </p>
        <Link
          to="/nonprofit/login"
          className="inline-block px-5 py-2.5 rounded-xl bg-soft-gold text-deep-navy font-body text-body font-semibold hover:bg-bright-gold transition-colors"
        >
          Sign in to review hours
        </Link>
      </div>
    </div>
  )
}
