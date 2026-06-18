import { useEffect, useState } from 'react'
import { usePageMeta } from '../hooks/usePageMeta'
import { useAuth } from '../contexts/AuthContext'
import { useSavedOrgs } from '../hooks/useSavedOrgs'
import { Link } from 'react-router-dom'
import LogVolunteerHours from '../components/LogVolunteerHours'
import VerifiedHours from '../components/VerifiedHours'
import { getWalletSummary, getSavedOrganizations, SavedOrganization, WalletSummary, getLoggedHours, VolunteerHourLog } from '../data/api'

export default function ImpactWallet() {
  usePageMeta(
    'Impact Wallet | Daanaa',
    'Track your giving, volunteering, and community impact.'
  )

  const { user, loading: authLoading, getIdToken } = useAuth()
  const { savedOrgs: localSavedOrgs } = useSavedOrgs()
  const [summary, setSummary] = useState<WalletSummary | null>(null)
  const [savedOrgs, setSavedOrgs] = useState<SavedOrganization[]>([])
  const [loading, setLoading] = useState(true)
  const [showLogForm, setShowLogForm] = useState(false)

  useEffect(() => {
    if (authLoading) return
    if (!user) return

    const fetchWalletData = async () => {
      try {
        const idToken = await getIdToken()
        if (!idToken) {
          console.error('No auth token available')
          setLoading(false)
          return
        }

        const [summaryData, savedOrgsData] = await Promise.all([
          getWalletSummary(idToken),
          getSavedOrganizations(idToken),
        ])

        setSummary(summaryData)
        setSavedOrgs(savedOrgsData)
      } catch (err) {
        console.error('Error fetching wallet data:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchWalletData()
  }, [user, authLoading, getIdToken])

  if (authLoading || loading) {
    return (
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12 py-12">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-slate-200 rounded w-1/3"></div>
          <div className="h-40 bg-slate-100 rounded"></div>
        </div>
      </div>
    )
  }

  if (!user) {
    const { signInWithGoogle } = useAuth()
    return (
      <div className="bg-warm-cream min-h-screen py-12 md:py-16">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
          <div className="text-center py-20">
            <h1 className="text-4xl font-display text-deep-navy mb-4">Impact Wallet</h1>
            <p className="text-lg text-cool-grey mb-8">Sign in to track your giving and volunteering</p>
            <button
              onClick={() => signInWithGoogle()}
              className="inline-flex items-center gap-2 px-6 py-3 bg-deep-navy text-white rounded-lg font-medium hover:bg-deep-navy/90 transition-colors"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
              Sign in with Google
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-warm-cream min-h-screen py-12 md:py-16">
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-display text-deep-navy mb-3">Impact Wallet</h1>
          <p className="text-lg text-cool-grey max-w-2xl">
            Your private place to track giving, volunteering, and community impact.
          </p>
        </div>

        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
            <div className="bg-white border border-light-grey rounded-xl p-6">
              <div className="text-xs text-soft-gold uppercase tracking-wider font-semibold mb-2">
                Volunteer Hours
              </div>
              <div className="text-3xl font-display text-deep-navy mb-2">
                {(summary.verified_hours.total_hours + summary.logged_hours.total_hours).toFixed(1)}
              </div>
              <p className="text-sm text-cool-grey">
                {summary.verified_hours.total_hours.toFixed(1)} verified, {summary.logged_hours.total_hours.toFixed(1)} logged
              </p>
            </div>

            <div className="bg-white border border-light-grey rounded-xl p-6">
              <div className="text-xs text-soft-gold uppercase tracking-wider font-semibold mb-2">
                Estimated Community Value
              </div>
              <div className="text-3xl font-display text-deep-navy mb-2">
                ${summary.verified_hours.estimated_value.toFixed(2)}
              </div>
              <p className="text-xs text-slate-500 mt-2">
                Based on verified hours only. For informational purposes.
              </p>
            </div>
          </div>
        )}

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Logged Hours */}
          <div className="lg:col-span-2">
            <div className="bg-white border border-light-grey rounded-xl p-6 mb-8">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-display text-deep-navy">Volunteer Hours I've Logged</h2>
                <button
                  onClick={() => setShowLogForm(!showLogForm)}
                  className="px-4 py-2 bg-soft-gold text-white rounded-lg font-medium text-sm hover:bg-soft-gold/90 transition-colors"
                >
                  {showLogForm ? 'Cancel' : 'Log Hours'}
                </button>
              </div>

              {showLogForm && (
                <div className="mb-8 pb-8 border-b border-light-grey">
                  <LogVolunteerHours onSuccess={() => setShowLogForm(false)} />
                </div>
              )}

              <LoggedHoursList />
            </div>

            {/* Verified Hours */}
            <div className="bg-white border border-light-grey rounded-xl p-6">
              <h2 className="text-xl font-display text-deep-navy mb-6">Hours Confirmed by Nonprofits</h2>
              <VerifiedHours />
            </div>

            {/* Saved Organizations */}
            <div className="bg-white border border-light-grey rounded-xl p-6">
              <h2 className="text-xl font-display text-deep-navy mb-6">Saved Organizations</h2>
              {savedOrgs.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-cool-grey mb-3">No saved organizations yet.</p>
                  <p className="text-sm text-slate-500">
                    Browse the directory and click "Save to Wallet" to bookmark nonprofits you want to remember.
                  </p>
                  <Link to="/directory" className="inline-block mt-4 px-4 py-2 bg-soft-gold text-white rounded-lg font-medium hover:bg-soft-gold/90 transition-colors text-sm">
                    Browse Directory
                  </Link>
                </div>
              ) : (
                <div className="space-y-3">
                  {savedOrgs.map((org) => (
                    <Link
                      key={org.ein}
                      to={`/org/${org.ein}`}
                      className="block p-4 bg-warm-cream rounded-lg border border-light-grey/50 hover:border-soft-gold hover:bg-warm-cream/70 transition-colors"
                    >
                      <p className="font-semibold text-deep-navy">{org.name}</p>
                      {org.city && org.state && (
                        <p className="text-sm text-cool-grey mt-1">{org.city}, {org.state}</p>
                      )}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Sidebar: Actions */}
          <div>
            <div className="bg-white border border-light-grey rounded-xl p-6 sticky top-6">
              <h3 className="text-lg font-display text-deep-navy mb-4">Actions</h3>
              <div className="space-y-3">
                <a
                  href="/wallet/export"
                  className="block w-full px-4 py-3 text-center bg-warm-cream text-deep-navy rounded-lg font-medium hover:bg-warm-cream/70 transition-colors border border-light-grey"
                >
                  Download CSV
                </a>
                <p className="text-xs text-cool-grey">
                  Export your impact wallet for personal records.
                </p>
              </div>

              <div className="mt-8 pt-6 border-t border-light-grey">
                <h4 className="font-semibold text-deep-navy mb-3">Privacy</h4>
                <p className="text-sm text-cool-grey leading-relaxed">
                  Your volunteer logs are private. When you sign up for a nonprofit's opportunities, they will be notified.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function LoggedHoursList() {
  const { getIdToken } = useAuth()
  const [hours, setHours] = useState<VolunteerHourLog[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadHours = async () => {
      try {
        const token = await getIdToken()
        if (!token) {
          console.error('No auth token available')
          setLoading(false)
          return
        }
        const data = await getLoggedHours(token)
        setHours(data)
      } catch (err) {
        console.error('Error fetching hours:', err)
      } finally {
        setLoading(false)
      }
    }
    loadHours()
  }, [getIdToken])

  if (loading) return <div className="text-center text-cool-grey">Loading...</div>
  if (hours.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-cool-grey mb-3">No volunteer hours logged yet.</p>
        <p className="text-sm text-slate-500">Start tracking your volunteer service here.</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {hours.map((h) => (
        <div key={h.id} className="flex items-start justify-between p-4 bg-warm-cream rounded-lg border border-light-grey/50">
          <div>
            <p className="font-semibold text-deep-navy">{h.nonprofit_name}</p>
            <p className="text-sm text-cool-grey">{h.service_date}</p>
            {h.notes && <p className="text-xs text-slate-500 mt-1">{h.notes}</p>}
          </div>
          <p className="font-semibold text-deep-navy text-right whitespace-nowrap ml-4">
            {h.hours_logged.toFixed(1)} hrs
          </p>
        </div>
      ))}
    </div>
  )
}
