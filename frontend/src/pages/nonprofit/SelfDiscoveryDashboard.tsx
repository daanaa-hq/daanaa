import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePageMeta } from '../../hooks/usePageMeta'

interface DashboardData {
  ein: string
  organization_name: string
  financial_context: {
    health_signal: string
    archetype: string
    band: string
    peer_count: number
    is_hidden_gem: boolean
    narrative: string
  }
  peer_context: {
    peers: Array<{
      name: string
      city: string
      state: string
      revenue: number
      health_signal: string
      website: string
    }>
    note: string
  }
  donor_interest: {
    bookmarks_this_month: number
    bookmarks_last_month: number
    note: string
  }
  profile: {
    checks: {
      mission: boolean
      website_verified: boolean
      donate_link_verified: boolean
    }
    narrative: string
  }
  derived_data: string
}

export default function SelfDiscoveryDashboard() {
  const navigate = useNavigate()
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [token, setToken] = useState('')

  usePageMeta(
    'Your Organization Dashboard',
    'Financial context, peer comparison, and discovery metrics for your nonprofit.'
  )

  useEffect(() => {
    // Get token from URL or localStorage (set by claim flow)
    const urlParams = new URLSearchParams(window.location.search)
    const urlToken = urlParams.get('token')
    const ein = urlParams.get('ein')

    if (urlToken && ein) {
      setToken(urlToken)
      fetchDashboard(ein, urlToken)
    } else {
      setError('No authorization token. Please claim your organization first.')
      setLoading(false)
    }
  }, [])

  async function fetchDashboard(ein: string, verificationToken: string) {
    try {
      const res = await fetch('/api/nonprofit/dashboard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ein, verification_token: verificationToken }),
      })
      if (!res.ok) {
        throw new Error(`${res.status}: ${res.statusText}`)
      }
      const body = await res.json()
      setData(body)
    } catch (err) {
      setError((err as Error).message || 'Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="w-6 h-6 rounded-full border-2 border-soft-gold border-t-transparent animate-spin" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="min-h-[60vh] bg-warm-cream pt-[72px]">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 py-16">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-red-700">
            <h2 className="font-body text-lg font-semibold mb-2">Unable to Load Dashboard</h2>
            <p className="font-body text-sm mb-4">{error}</p>
            <button
              onClick={() => navigate('/for-nonprofits')}
              className="font-body text-sm text-red-700 underline underline-offset-2 hover:text-red-800"
            >
              Return to claim your organization
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-[100dvh]">
      {/* Hero */}
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 pt-12 pb-16">
          <h1 className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(32px, 4vw, 48px)' }}>
            {data.organization_name}
          </h1>
          <p className="mt-3 font-body text-[16px] text-muted-cream">Your discovery dashboard on Daanaa</p>
        </div>
      </div>

      {/* Main content */}
      <div className="bg-warm-cream py-16 md:py-20">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 space-y-16">

          {/* Financial Context */}
          <section>
            <h2 className="font-display italic text-deep-navy leading-[1.1] text-[32px] md:text-[40px] tracking-[-0.01em] mb-6">
              Your Financial Context
            </h2>
            <div className="bg-white rounded-2xl p-8 border border-light-grey shadow-md">
              <div className="grid md:grid-cols-2 gap-8 mb-8">
                <div>
                  <p className="font-body text-[12px] font-medium tracking-[0.08em] text-cool-grey uppercase mb-2">Health Signal</p>
                  <p className="font-display italic text-[28px] text-soft-gold">{data.financial_context.health_signal}</p>
                </div>
                <div>
                  <p className="font-body text-[12px] font-medium tracking-[0.08em] text-cool-grey uppercase mb-2">Your Category</p>
                  <p className="font-body text-[16px] font-semibold text-deep-navy">{data.financial_context.archetype}</p>
                  <p className="font-body text-[14px] text-cool-grey">{data.financial_context.band}</p>
                </div>
              </div>
              <div className="border-t border-light-grey pt-6">
                <p className="font-body text-[16px] text-cool-grey leading-[1.7]">
                  {data.financial_context.narrative}
                </p>
                <p className="font-body text-[12px] text-cool-grey mt-4">
                  Peer group: {data.financial_context.peer_count} organizations with your funding model and size
                </p>
              </div>
            </div>
          </section>

          {/* Peer Context */}
          <section>
            <h2 className="font-display italic text-deep-navy leading-[1.1] text-[32px] md:text-[40px] tracking-[-0.01em] mb-6">
              Organizations Like Yours
            </h2>
            <div className="space-y-4 mb-6">
              {data.peer_context.peers.map((peer, i) => (
                <div key={i} className="bg-white rounded-lg p-6 border border-light-grey">
                  <div className="flex justify-between items-start gap-4 mb-2">
                    <div>
                      <p className="font-body font-semibold text-deep-navy">{peer.name}</p>
                      <p className="font-body text-[14px] text-cool-grey">
                        {peer.city}, {peer.state}
                      </p>
                    </div>
                    <span className="font-body text-[12px] font-medium text-soft-gold uppercase">
                      {peer.health_signal}
                    </span>
                  </div>
                  {peer.website && (
                    <a
                      href={peer.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-body text-[12px] text-deep-navy underline underline-offset-2 hover:text-navy-mid"
                    >
                      Visit their site
                    </a>
                  )}
                </div>
              ))}
            </div>
            <p className="font-body text-[14px] text-cool-grey leading-[1.6]">
              {data.peer_context.note}
            </p>
          </section>

          {/* Donor Interest */}
          <section>
            <h2 className="font-display italic text-deep-navy leading-[1.1] text-[32px] md:text-[40px] tracking-[-0.01em] mb-6">
              Discovery Interest
            </h2>
            <div className="bg-white rounded-2xl p-8 border border-light-grey shadow-md">
              <div className="grid md:grid-cols-2 gap-8 mb-8">
                <div>
                  <p className="font-body text-[12px] font-medium tracking-[0.08em] text-cool-grey uppercase mb-2">This Month</p>
                  <p className="font-display italic text-[32px] text-soft-gold">{data.donor_interest.bookmarks_this_month}</p>
                  <p className="font-body text-[12px] text-cool-grey">people saved your org</p>
                </div>
                <div>
                  <p className="font-body text-[12px] font-medium tracking-[0.08em] text-cool-grey uppercase mb-2">Last Month</p>
                  <p className="font-display italic text-[32px] text-soft-gold">{data.donor_interest.bookmarks_last_month}</p>
                </div>
              </div>
              <div className="border-t border-light-grey pt-6">
                <p className="font-body text-[14px] text-cool-grey leading-[1.6]">
                  {data.donor_interest.note}
                </p>
              </div>
            </div>
          </section>

          {/* Profile Completeness */}
          <section>
            <h2 className="font-display italic text-deep-navy leading-[1.1] text-[32px] md:text-[40px] tracking-[-0.01em] mb-6">
              Your Public Profile
            </h2>
            <div className="bg-white rounded-2xl p-8 border border-light-grey shadow-md">
              <div className="space-y-4 mb-8">
                {Object.entries(data.profile.checks).map(([key, complete]) => (
                  <div key={key} className="flex items-center gap-3">
                    <div className={`w-5 h-5 rounded ${complete ? 'bg-success-green' : 'bg-light-grey'}`} />
                    <p className="font-body text-[16px] text-deep-navy capitalize">
                      {key.replace(/_/g, ' ')}
                    </p>
                  </div>
                ))}
              </div>
              <div className="border-t border-light-grey pt-6">
                <p className="font-body text-[16px] text-cool-grey leading-[1.7]">
                  {data.profile.narrative}
                </p>
              </div>
            </div>
          </section>

          {/* Help Section */}
          <section className="bg-soft-cream rounded-lg p-6 md:p-8">
            <h3 className="font-body text-[16px] font-semibold text-deep-navy mb-3">Need Help?</h3>
            <p className="font-body text-[14px] text-cool-grey mb-4">
              {data.derived_data}
            </p>
            <a
              href="/claim/edit"
              className="font-body text-[14px] text-deep-navy underline underline-offset-2 hover:text-navy-mid"
            >
              Edit your profile →
            </a>
          </section>

        </div>
      </div>
    </div>
  )
}
