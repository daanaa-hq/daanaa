import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePageMeta } from '../../hooks/usePageMeta'
import { normalizeExternalUrl } from '../../utils/externalLink'

interface PageHealth {
  public_page_url: string
  mission: { shown: boolean; text: string | null; source: string | null }
  website: { url: string | null; shown_to_donors: boolean; status: string | null }
  donate_link: { url: string | null; shown_to_donors: boolean; status: string | null; note: string }
}

interface DashboardData {
  ein: string
  organization_name: string
  page_health?: PageHealth
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
    bookmarks_this_month: number | null
    bookmarks_last_month: number | null
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
      <div className="min-h-[60vh] bg-warm-cream pt-nav">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 py-16">
          <div className="bg-destructive/5 border border-destructive/20 rounded-lg p-6 text-destructive">
            <h2 className="font-body text-lg font-semibold mb-2">Unable to Load Dashboard</h2>
            <p className="font-body text-sm mb-4">{error}</p>
            <button
              onClick={() => navigate('/for-nonprofits')}
              className="font-body text-sm text-destructive underline underline-offset-2 hover:text-red-800"
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
      <div className="bg-deep-navy pt-nav">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 pt-12 pb-16">
          <h1 className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(32px, 4vw, 48px)' }}>
            {data.organization_name}
          </h1>
          <p className="mt-3 font-body text-lead text-muted-cream">Your discovery dashboard on Daanaa</p>
        </div>
      </div>

      {/* Main content */}
      <div className="bg-warm-cream py-16 md:py-20">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 space-y-16">

          {/* Page Health — what donors actually see, and whether it works */}
          {data.page_health && (
            <section>
              <div className="flex flex-wrap items-end justify-between gap-4 mb-6">
                <h2 className="font-display italic text-deep-navy leading-[1.1] text-headline-lg md:text-display tracking-[-0.01em]">
                  What Donors See
                </h2>
                <a
                  href={data.page_health.public_page_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-deep-navy text-warm-cream font-body text-body font-semibold hover:bg-deep-navy/90 transition-colors"
                >
                  View your public page
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M7 17 17 7M7 7h10v10"/></svg>
                </a>
              </div>
              <div className="grid md:grid-cols-3 gap-4">
                {/* Mission */}
                <div className="bg-white rounded-2xl p-6 border border-light-grey shadow-md">
                  <div className="flex items-center justify-between mb-3">
                    <p className="font-body text-caption font-medium tracking-[0.08em] text-cool-grey uppercase">Mission</p>
                    <span className={`font-body text-label font-semibold px-2 py-0.5 rounded-full ${data.page_health.mission.shown ? 'bg-success-green/15 text-success-green' : 'bg-light-grey text-cool-grey'}`}>
                      {data.page_health.mission.shown ? 'Live' : 'Not shown'}
                    </span>
                  </div>
                  {data.page_health.mission.text ? (
                    <>
                      <p className="font-body text-body text-deep-navy leading-[1.6] line-clamp-4">{data.page_health.mission.text}</p>
                      <p className="font-body text-caption text-cool-grey mt-3">Source: {data.page_health.mission.source}</p>
                    </>
                  ) : (
                    <p className="font-body text-body text-cool-grey leading-[1.6]">
                      Donors see no mission yet. Adding one in your own words is the single biggest upgrade to your page.
                    </p>
                  )}
                </div>
                {/* Website */}
                <div className="bg-white rounded-2xl p-6 border border-light-grey shadow-md">
                  <div className="flex items-center justify-between mb-3">
                    <p className="font-body text-caption font-medium tracking-[0.08em] text-cool-grey uppercase">Website</p>
                    <span className={`font-body text-label font-semibold px-2 py-0.5 rounded-full ${data.page_health.website.shown_to_donors ? 'bg-success-green/15 text-success-green' : 'bg-light-grey text-cool-grey'}`}>
                      {data.page_health.website.shown_to_donors ? 'Live' : 'Not shown'}
                    </span>
                  </div>
                  {data.page_health.website.url ? (
                    <p className="font-body text-body text-deep-navy break-all">{data.page_health.website.url}</p>
                  ) : (
                    <p className="font-body text-body text-cool-grey leading-[1.6]">No website on file yet.</p>
                  )}
                </div>
                {/* Donate link */}
                <div className="bg-white rounded-2xl p-6 border border-light-grey shadow-md">
                  <div className="flex items-center justify-between mb-3">
                    <p className="font-body text-caption font-medium tracking-[0.08em] text-cool-grey uppercase">Donate Button</p>
                    <span className={`font-body text-label font-semibold px-2 py-0.5 rounded-full ${data.page_health.donate_link.shown_to_donors ? 'bg-success-green/15 text-success-green' : 'bg-light-grey text-cool-grey'}`}>
                      {data.page_health.donate_link.shown_to_donors ? 'Live' : 'Not shown'}
                    </span>
                  </div>
                  {data.page_health.donate_link.url && data.page_health.donate_link.shown_to_donors && (
                    <p className="font-body text-body text-deep-navy break-all mb-3">{data.page_health.donate_link.url}</p>
                  )}
                  <p className="font-body text-small text-cool-grey leading-[1.6]">{data.page_health.donate_link.note}</p>
                </div>
              </div>
            </section>
          )}

          {/* Financial Context */}
          <section>
            <h2 className="font-display italic text-deep-navy leading-[1.1] text-headline-lg md:text-display tracking-[-0.01em] mb-6">
              Your Financial Context
            </h2>
            <div className="bg-white rounded-2xl p-8 border border-light-grey shadow-md">
              <div className="grid md:grid-cols-2 gap-8 mb-8">
                <div>
                  <p className="font-body text-caption font-medium tracking-[0.08em] text-cool-grey uppercase mb-2">Health Signal</p>
                  <p className="font-display italic text-headline text-soft-gold">{data.financial_context.health_signal}</p>
                </div>
                <div>
                  <p className="font-body text-caption font-medium tracking-[0.08em] text-cool-grey uppercase mb-2">Your Category</p>
                  <p className="font-body text-lead font-semibold text-deep-navy">{data.financial_context.archetype}</p>
                  <p className="font-body text-body text-cool-grey">{data.financial_context.band}</p>
                </div>
              </div>
              <div className="border-t border-light-grey pt-6">
                <p className="font-body text-lead text-cool-grey leading-[1.7]">
                  {data.financial_context.narrative}
                </p>
                <p className="font-body text-caption text-cool-grey mt-4">
                  Peer group: {data.financial_context.peer_count} organizations with your funding model and size
                </p>
              </div>
            </div>
          </section>

          {/* Peer Context */}
          <section>
            <h2 className="font-display italic text-deep-navy leading-[1.1] text-headline-lg md:text-display tracking-[-0.01em] mb-6">
              Organizations Like Yours
            </h2>
            <div className="space-y-4 mb-6">
              {data.peer_context.peers.map((peer, i) => (
                <div key={i} className="bg-white rounded-lg p-6 border border-light-grey">
                  <div className="flex justify-between items-start gap-4 mb-2">
                    <div>
                      <p className="font-body font-semibold text-deep-navy">{peer.name}</p>
                      <p className="font-body text-body text-cool-grey">
                        {peer.city}, {peer.state}
                      </p>
                    </div>
                    <span className="font-body text-caption font-medium text-soft-gold uppercase">
                      {peer.health_signal}
                    </span>
                  </div>
                  {peer.website && (
                    <a
                      href={normalizeExternalUrl(peer.website) || undefined}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-body text-caption text-deep-navy underline underline-offset-2 hover:text-navy-mid"
                    >
                      Visit their site
                    </a>
                  )}
                </div>
              ))}
            </div>
            <p className="font-body text-body text-cool-grey leading-[1.6]">
              {data.peer_context.note}
            </p>
          </section>

          {/* Donor Interest */}
          <section>
            <h2 className="font-display italic text-deep-navy leading-[1.1] text-headline-lg md:text-display tracking-[-0.01em] mb-6">
              Discovery Interest
            </h2>
            <div className="bg-white rounded-2xl p-8 border border-light-grey shadow-md">
              <div className="grid md:grid-cols-2 gap-8 mb-8">
                {data.donor_interest.bookmarks_this_month !== null && (
                  <div>
                    <p className="font-body text-caption font-medium tracking-[0.08em] text-cool-grey uppercase mb-2">This Month</p>
                    <p className="font-display italic text-headline-lg text-soft-gold">{data.donor_interest.bookmarks_this_month}</p>
                    <p className="font-body text-caption text-cool-grey">people saved your org</p>
                  </div>
                )}
                {data.donor_interest.bookmarks_last_month !== null && (
                  <div>
                    <p className="font-body text-caption font-medium tracking-[0.08em] text-cool-grey uppercase mb-2">Last Month</p>
                    <p className="font-display italic text-headline-lg text-soft-gold">{data.donor_interest.bookmarks_last_month}</p>
                  </div>
                )}
              </div>
              <div className="border-t border-light-grey pt-6">
                <p className="font-body text-body text-cool-grey leading-[1.6]">
                  {data.donor_interest.note}
                </p>
              </div>
            </div>
          </section>

          {/* Profile Completeness */}
          <section>
            <h2 className="font-display italic text-deep-navy leading-[1.1] text-headline-lg md:text-display tracking-[-0.01em] mb-6">
              Your Public Profile
            </h2>
            <div className="bg-white rounded-2xl p-8 border border-light-grey shadow-md">
              <div className="space-y-4 mb-8">
                {Object.entries(data.profile.checks).map(([key, complete]) => (
                  <div key={key} className="flex items-center gap-3">
                    <div className={`w-5 h-5 rounded ${complete ? 'bg-success-green' : 'bg-light-grey'}`} />
                    <p className="font-body text-lead text-deep-navy capitalize">
                      {key.replace(/_/g, ' ')}
                    </p>
                  </div>
                ))}
              </div>
              <div className="border-t border-light-grey pt-6">
                <p className="font-body text-lead text-cool-grey leading-[1.7]">
                  {data.profile.narrative}
                </p>
              </div>
            </div>
          </section>

          {/* Help Section */}
          <section className="bg-soft-cream rounded-lg p-6 md:p-8">
            <h3 className="font-body text-lead font-semibold text-deep-navy mb-3">Need Help?</h3>
            <p className="font-body text-body text-cool-grey mb-4">
              {data.derived_data}
            </p>
            <a
              href="/claim/edit"
              className="font-body text-body text-deep-navy underline underline-offset-2 hover:text-navy-mid"
            >
              Edit your profile →
            </a>
          </section>

        </div>
      </div>
    </div>
  )
}
