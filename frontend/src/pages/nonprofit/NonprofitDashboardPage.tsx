import React, { useState, useEffect } from 'react'
import { usePageMeta } from '../../hooks/usePageMeta'
import { useParams, useNavigate, Link } from 'react-router-dom'
import OnboardingChecklist from '../../components/OnboardingChecklist'
import VolunteerInsightsCard from '../../components/VolunteerInsightsCard'
import DonorCommunicationCard from '../../components/DonorCommunicationCard'
import ImpactForecast from '../../components/ImpactForecast'
import DonorMessagesCard from '../../components/DonorMessagesCard'
import CreditPurchaseModal from '../../components/CreditPurchaseModal'
import { Button } from '../../components/ui/button'

interface LetterRequest {
  id: string
  donor_name: string
  amount: number
  donation_date: string
  status: 'pending' | 'approved' | 'generated'
}

interface ActivityFeedItem {
  timestamp: string
  title: string
  description: string
  type: 'link_verified' | 'donor_interest' | 'data_refresh' | 'volunteer_activity'
  icon: string
}

interface DashboardData {
  nonprofit_ein: string
  name: string
  pending_letters: LetterRequest[]
  letters_remaining: number
}

export default function NonprofitDashboardPage() {
  const { ein } = useParams<{ ein: string }>()
  const navigate = useNavigate()
  usePageMeta('Nonprofit Dashboard | Daanaa', 'Manage donation letter requests, approvals, and credits')

  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [activityFeed, setActivityFeed] = useState<ActivityFeedItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [approving, setApproving] = useState<string | null>(null)
  const [showCreditModal, setShowCreditModal] = useState(false)

  const getAuthToken = () => {
    return localStorage.getItem('nonprofit_account_id') || localStorage.getItem('nonprofit_auth_token') || ein || ''
  }

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const authToken = getAuthToken()
        if (!authToken) {
          navigate('/nonprofit/letters/signup')
          return
        }

        const res = await fetch('/api/nonprofit/dashboard', {
          headers: { Authorization: `Bearer ${authToken}` },
        })
        if (!res.ok) throw new Error('Failed to load dashboard')
        const data = await res.json()
        setDashboard(data)

        // Fetch activity feed
        const feedRes = await fetch('/api/nonprofit/activity-feed', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${authToken}`,
          },
          body: JSON.stringify({ ein, verification_token: authToken }),
        })
        if (feedRes.ok) {
          const feedData = await feedRes.json()
          setActivityFeed(feedData.feed || [])
        }
      } catch (err) {
        setError((err as Error).message)
      } finally {
        setLoading(false)
      }
    }
    fetchDashboard()
  }, [ein, navigate])

  const handleApprove = async (letterId: string) => {
    setApproving(letterId)
    try {
      const authToken = getAuthToken()
      const res = await fetch(`/api/nonprofit/letter/${letterId}/approve`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${authToken}` },
      })
      if (!res.ok) throw new Error('Failed to approve letter')
      setDashboard(prev => prev ? {
        ...prev,
        pending_letters: prev.pending_letters.map(l =>
          l.id === letterId ? { ...l, status: 'approved' } : l
        )
      } : null)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setApproving(null)
    }
  }

  const handleGenerateLetter = async (letterId: string) => {
    try {
      const authToken = getAuthToken()
      const res = await fetch(`/api/nonprofit/letter/${letterId}/generate`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${authToken}` },
      })
      if (!res.ok) throw new Error('Failed to generate letter')

      // Handle PDF download
      const contentType = res.headers.get('content-type')
      if (contentType?.includes('application/pdf')) {
        const blob = await res.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `donation_letter_${letterId}.pdf`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      } else {
        const data = await res.json()
        if (data.pdf_url) window.open(data.pdf_url, '_blank')
      }

      setDashboard(prev => prev ? {
        ...prev,
        pending_letters: prev.pending_letters.map(l =>
          l.id === letterId ? { ...l, status: 'generated' } : l
        ),
        letters_remaining: prev.letters_remaining - 1
      } : null)
    } catch (err) {
      setError((err as Error).message)
    }
  }

  if (loading) return <div className="p-8 text-center">Loading...</div>
  if (error) return <div className="p-8 text-center text-red-600">{error}</div>
  if (!dashboard) return <div className="p-8 text-center">No data</div>

  return (
    <div className="min-h-screen bg-soft-cream p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="font-display text-4xl italic text-deep-navy mb-2">{dashboard.name}</h1>
          <p className="text-cool-grey">EIN: {dashboard.nonprofit_ein}</p>
        </div>

        <OnboardingChecklist ein={dashboard.nonprofit_ein} />

        {/* Feature cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6 mb-8">
          {/* Donation Letters */}
          <div className="bg-gradient-to-br from-soft-gold/20 to-bright-gold/10 rounded-2xl p-6 border border-soft-gold/30">
            <div className="mb-4">
              <h3 className="font-display text-xl text-deep-navy">Donation Letters</h3>
            </div>
            <p className="text-sm text-cool-grey mb-4">
              Approve and generate tax-compliant donation letters for your donors.
            </p>
            <div className="mb-4">
              <p className="text-xs text-cool-grey font-semibold mb-1">Credits Available</p>
              <p className="text-3xl font-display italic text-soft-gold">{dashboard.letters_remaining}</p>
            </div>
            <Link
              to={`#pending`}
              className="inline-block px-4 py-2 bg-soft-gold text-deep-navy rounded-lg font-semibold text-sm hover:bg-bright-gold transition-colors"
            >
              Manage Letters
            </Link>
          </div>

          {/* Volunteer Hours */}
          <div className="bg-gradient-to-br from-green-100/30 to-emerald-100/10 rounded-2xl p-6 border border-green-200/30">
            <div className="mb-4">
              <h3 className="font-display text-xl text-deep-navy">Volunteer Hours</h3>
            </div>
            <p className="text-sm text-cool-grey mb-4">
              Track and verify volunteer service hours contributed by your supporters.
            </p>
            <p className="text-xs text-cool-grey font-semibold mb-4">Set up tracking for your team</p>
            <Link
              to={`/nonprofit/volunteer-approval/${dashboard.nonprofit_ein}`}
              className="inline-block px-4 py-2 bg-green-600 text-white rounded-lg font-semibold text-sm hover:bg-green-700 transition-colors"
            >
              Manage Hours
            </Link>
          </div>

          {/* Daanaa Profile */}
          <div className="bg-gradient-to-br from-blue-100/30 to-cyan-100/10 rounded-2xl p-6 border border-blue-200/30">
            <div className="flex items-start justify-between mb-4">
              <h3 className="font-display text-xl text-deep-navy">Daanaa Profile</h3>
              <span className="text-2xl">🏢</span>
            </div>
            <p className="text-sm text-cool-grey mb-4">
              View your nonprofit's profile on Daanaa and update key information.
            </p>
            <p className="text-xs text-cool-grey font-semibold mb-4">Help donors discover you</p>
            <a
              href={`/org/${dashboard.nonprofit_ein}`}
              className="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg font-semibold text-sm hover:bg-blue-700 transition-colors"
            >
              View Profile
            </a>
          </div>

          {/* Volunteer Insights - NEW */}
          <VolunteerInsightsCard
            nonprofitEin={dashboard.nonprofit_ein}
            authToken={getAuthToken()}
          />

          {/* Donor Communication - NEW */}
          <DonorCommunicationCard
            nonprofitEin={dashboard.nonprofit_ein}
            nonprofitName={dashboard.name}
            authToken={getAuthToken()}
          />
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm mb-8 border-l-4 border-soft-gold">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm text-cool-grey font-semibold mb-1">Letter Credits</p>
              <p className="font-display text-4xl italic text-deep-navy">{dashboard.letters_remaining}</p>
              <p className="text-xs text-cool-grey mt-2">letters remaining</p>
            </div>
            <Button onClick={() => setShowCreditModal(true)} variant="default" size="default">
              Buy More
            </Button>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm" id="pending">
          <h2 className="font-display text-2xl italic text-deep-navy mb-2">
            Letter Requests
          </h2>
          <p className="text-sm text-cool-grey mb-6">
            {dashboard.pending_letters.length === 0
              ? 'No pending requests. Donors will see your profile on Daanaa and can request donation letters.'
              : `${dashboard.pending_letters.filter(l => l.status === 'pending').length} pending · ${dashboard.pending_letters.filter(l => l.status === 'approved').length} approved · ${dashboard.pending_letters.filter(l => l.status === 'generated').length} generated`}
          </p>

          {dashboard.pending_letters.length === 0 ? (
            <p className="text-center text-cool-grey py-8">No pending requests</p>
          ) : (
            <div className="space-y-4">
              {dashboard.pending_letters.map(letter => (
                <div key={letter.id} className="border border-light-grey rounded-lg p-4 hover:bg-soft-cream">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <p className="font-semibold text-deep-navy">{letter.donor_name}</p>
                      <p className="text-sm text-cool-grey">${letter.amount.toFixed(2)}</p>
                      <p className="text-xs text-cool-grey">{letter.donation_date}</p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      letter.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      letter.status === 'approved' ? 'bg-blue-100 text-blue-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {letter.status}
                    </span>
                  </div>

                  {letter.status === 'pending' && (
                    <div className="flex gap-2">
                      <Button onClick={() => handleApprove(letter.id)} disabled={approving === letter.id}
                        variant="default" size="default" className="flex-1">
                        {approving === letter.id ? 'Approving...' : 'Approve'}
                      </Button>
                      <Button variant="secondary" size="default" className="flex-1">
                        Reject
                      </Button>
                    </div>
                  )}

                  {letter.status === 'approved' && (
                    <Button onClick={() => handleGenerateLetter(letter.id)}
                      variant="default" size="default" className="w-full">
                      Generate Letter
                    </Button>
                  )}

                  {letter.status === 'generated' && (
                    <p className="text-sm text-green-700 font-semibold">✓ Generated</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Activity Feed */}
        <div className="bg-white rounded-2xl p-6 shadow-sm mb-8 border-l-4 border-blue-300">
          <h2 className="font-display text-2xl italic text-deep-navy mb-4">What Changed</h2>
          {activityFeed.length === 0 ? (
            <p className="text-sm text-cool-grey text-center py-8">No recent activity</p>
          ) : (
            <div className="space-y-3">
              {activityFeed.map((item, idx) => (
                <div key={idx} className="flex gap-4 pb-3 border-b border-light-grey last:border-0">
                  <div className="text-2xl flex-shrink-0">{item.icon}</div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-deep-navy text-sm">{item.title}</p>
                    <p className="text-xs text-cool-grey">{item.description}</p>
                    <p className="text-xs text-cool-grey mt-1">
                      {new Date(item.timestamp).toLocaleDateString()} at {new Date(item.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Phase 3: Impact & Communication */}
        <div className="mb-8">
          <h2 className="font-display text-2xl italic text-deep-navy mb-4">Impact & Communication</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Impact Forecast */}
            <div className="bg-white rounded-2xl p-6 shadow-sm">
              <h3 className="font-display text-xl text-deep-navy mb-4">Impact Summary</h3>
              <ImpactForecast nonprofitEin={dashboard.nonprofit_ein} authToken={getAuthToken()} />
            </div>

            {/* Donor Communication */}
            <div>
              <DonorMessagesCard nonprofitEin={dashboard.nonprofit_ein} authToken={getAuthToken()} />
            </div>
          </div>
        </div>

        {/* Credit Purchase Modal */}
        {showCreditModal && (
          <CreditPurchaseModal
            nonprofitEin={dashboard?.nonprofit_ein || ''}
            currentBalance={dashboard?.letters_remaining || 0}
            onClose={() => setShowCreditModal(false)}
            onSuccess={(creditsAdded) => {
              setShowCreditModal(false)
              if (dashboard) {
                setDashboard({
                  ...dashboard,
                  letters_remaining: dashboard.letters_remaining + creditsAdded,
                })
              }
            }}
          />
        )}
      </div>
    </div>
  )
}
