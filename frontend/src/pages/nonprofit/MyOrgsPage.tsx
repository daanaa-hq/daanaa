import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { getMyOrgs, getPortalToken, type ClaimedOrg } from '../../data/api'
import { formatEIN } from '../../data/organizations'

// ── Status badge ───────────────────────────────────────────────────────────────

type ClaimStatus = ClaimedOrg['claim_status']

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; classes: string }> = {
    active:      { label: 'Active',           classes: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
    verified:    { label: 'Active',            classes: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
    pending:     { label: 'Waiting for PIN',   classes: 'bg-amber-50 text-amber-700 border-amber-200' },
    letter_sent: { label: 'Waiting for PIN',   classes: 'bg-amber-50 text-amber-700 border-amber-200' },
    revoked:     { label: 'Revoked',           classes: 'bg-red-50 text-red-700 border-red-200' },
  }
  const cfg = map[status] ?? { label: status, classes: 'bg-light-grey text-cool-grey border-light-grey' }
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full font-body text-[11px] font-semibold border ${cfg.classes}`}>
      {cfg.label}
    </span>
  )
}

// ── Skeleton card ──────────────────────────────────────────────────────────────

function SkeletonCard() {
  return (
    <div className="bg-white rounded-2xl border border-light-grey p-6 animate-pulse">
      <div className="flex items-start gap-4">
        <div className="shrink-0 w-10 h-10 rounded-full bg-light-grey" />
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-light-grey rounded w-2/3" />
          <div className="h-3 bg-light-grey rounded w-1/2" />
          <div className="h-3 bg-light-grey rounded w-1/3" />
        </div>
      </div>
    </div>
  )
}

// ── Org card ───────────────────────────────────────────────────────────────────

function OrgCard({ org, onDashboard, onEditProfile, loadingEin }: {
  org: ClaimedOrg
  onDashboard: (ein: string) => void
  onEditProfile: (ein: string) => void
  loadingEin: string | null
}) {
  const navigate = useNavigate()
  const isLoading = loadingEin === org.ein
  const location = [org.city, org.state].filter(Boolean).join(', ')
  const einFormatted = org.ein ? formatEIN(org.ein) : ''
  const status = org.claim_status as ClaimStatus

  return (
    <div className="bg-white rounded-2xl border border-light-grey p-6 hover:border-soft-gold/40 transition-colors">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="flex items-start gap-3 min-w-0">
          <div className="shrink-0 w-10 h-10 rounded-full bg-soft-gold/15 flex items-center justify-center text-lg">
            🏢
          </div>
          <div className="min-w-0">
            <h3 className="font-body text-[15px] font-semibold text-deep-navy truncate">
              {org.organization_name || 'Unnamed Organization'}
            </h3>
            <p className="font-body text-[13px] text-cool-grey mt-0.5">
              {[location, einFormatted ? `EIN: ${einFormatted}` : null].filter(Boolean).join(' · ')}
            </p>
          </div>
        </div>
        <StatusBadge status={org.claim_status} />
      </div>

      {/* Action buttons by status */}
      <div className="flex flex-wrap gap-2">
        {(status === 'pending' || status === 'letter_sent') && (
          <button
            onClick={() => navigate(`/claim/verify?ein=${org.ein}`)}
            className="px-4 py-2 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 font-body text-[13px] font-semibold hover:bg-amber-100 transition-colors"
          >
            Enter PIN
          </button>
        )}

        {(status === 'verified' || status === 'active') && (
          <>
            <button
              onClick={() => onDashboard(org.ein)}
              disabled={isLoading}
              className="px-4 py-2 rounded-xl bg-soft-gold text-deep-navy font-body text-[13px] font-semibold hover:bg-bright-gold disabled:opacity-50 transition-colors"
            >
              Dashboard
            </button>
            <button
              onClick={() => onEditProfile(org.ein)}
              disabled={isLoading}
              className="px-4 py-2 rounded-xl border border-light-grey text-deep-navy font-body text-[13px] font-medium hover:border-soft-gold/40 disabled:opacity-50 transition-colors"
            >
              Edit profile
            </button>
            <Link
              to={`/nonprofit/events/${org.ein}`}
              className="px-4 py-2 rounded-xl border border-light-grey text-deep-navy font-body text-[13px] font-medium hover:border-soft-gold/40 transition-colors"
            >
              Volunteer events
            </Link>
          </>
        )}

        {status !== 'revoked' && (
          <Link
            to={`/org/${org.ein}`}
            className="px-4 py-2 rounded-xl border border-light-grey text-cool-grey font-body text-[13px] font-medium hover:border-soft-gold/40 hover:text-deep-navy transition-colors"
          >
            View on Daanaa
          </Link>
        )}
      </div>
    </div>
  )
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function MyOrgsPage() {
  const navigate = useNavigate()
  const { user, getIdToken, signOut } = useAuth()

  const [orgs, setOrgs] = useState<ClaimedOrg[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [loadingEin, setLoadingEin] = useState<string | null>(null)

  useEffect(() => {
    async function fetchOrgs() {
      try {
        const idToken = await getIdToken()
        if (!idToken) {
          navigate('/nonprofit/login', { replace: true })
          return
        }
        const data = await getMyOrgs(idToken)
        setOrgs(data)
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Unknown error'
        if (msg.includes('401') || msg.includes('my-orgs failed')) {
          await signOut()
          navigate('/nonprofit/login', { replace: true })
        } else {
          setError('Something went wrong loading your organizations. Try again.')
        }
      } finally {
        setLoading(false)
      }
    }
    fetchOrgs()
  }, [getIdToken, navigate, signOut])

  async function navigateWithToken(ein: string, destination: 'dashboard' | 'edit' = 'edit') {
    setLoadingEin(ein)
    try {
      const idToken = await getIdToken()
      if (!idToken) {
        navigate('/nonprofit/login', { replace: true })
        return
      }
      const token = await getPortalToken(ein, idToken)
      const path = destination === 'dashboard'
        ? `/nonprofit/dashboard/${encodeURIComponent(ein)}`
        : `/claim/edit?ein=${encodeURIComponent(ein)}&token=${encodeURIComponent(token)}`
      navigate(path)
    } catch {
      setError('Could not load portal access. Please try again.')
    } finally {
      setLoadingEin(null)
    }
  }

  async function handleSignOut() {
    await signOut()
    navigate('/nonprofit/login', { replace: true })
  }

  return (
    <div className="min-h-[100dvh] bg-warm-cream">
      {/* Top bar */}
      <div className="border-b border-light-grey bg-white">
        <div className="max-w-[720px] mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/" className="font-display italic text-deep-navy text-[17px]">Daanaa</Link>
            <span className="text-light-grey">·</span>
            <span className="font-body text-[13px] text-cool-grey">Nonprofit Portal</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="font-body text-[12px] text-cool-grey hidden sm:block">
              {user?.email}
            </span>
            <button
              onClick={handleSignOut}
              className="font-body text-[13px] text-cool-grey hover:text-deep-navy transition-colors"
            >
              Sign out
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-[720px] mx-auto px-6 py-10">
        <div className="flex items-center justify-between mb-6">
          <h1 className="font-display italic text-deep-navy text-[28px]">
            Your organizations
          </h1>
          <Link
            to="/for-nonprofits"
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-soft-gold text-deep-navy font-body text-[13px] font-semibold hover:bg-bright-gold transition-colors"
          >
            <span>+</span>
            <span>Claim new</span>
          </Link>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl">
            <p className="font-body text-[14px] text-red-700">{error}</p>
          </div>
        )}

        {loading ? (
          <div className="space-y-4">
            <SkeletonCard />
            <SkeletonCard />
          </div>
        ) : orgs.length === 0 ? (
          <div className="bg-white rounded-2xl border border-light-grey p-12 text-center">
            <div className="text-4xl mb-4">🏢</div>
            <h2 className="font-display italic text-deep-navy text-[20px] mb-2">
              No organizations yet
            </h2>
            <p className="font-body text-[15px] text-cool-grey mb-6">
              Claim your nonprofit's page on Daanaa to manage your profile and connect with donors.
            </p>
            <Link
              to="/for-nonprofits"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-soft-gold text-deep-navy font-body text-[14px] font-semibold hover:bg-bright-gold transition-colors"
            >
              Claim your organization →
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {orgs.map(org => (
              <OrgCard
                key={org.ein}
                org={org}
                onDashboard={ein => navigateWithToken(ein, 'dashboard')}
                onEditProfile={ein => navigateWithToken(ein)}
                loadingEin={loadingEin}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
