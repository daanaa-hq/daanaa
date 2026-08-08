import React, { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { useApi } from '../hooks/useApi'
import { useAuth } from '../contexts/AuthContext'
import { normalizeExternalUrl } from '../utils/externalLink'

const API_BASE = import.meta.env.VITE_API_URL || ''

interface Vendor {
  vendor_id: string
  name: string
  category: string
  description: string
  contact_email: string
  website: string
  logo_url: string
  discount_code: string
  discount_description: string
  avg_rating: number | null
  rating_count: number
  total_savings: number
}

interface Rating {
  stars: number
  savings_amount: number
  created_at: string
}

async function getVendor(id: string): Promise<Vendor> {
  const resp = await fetch(`${API_BASE}/api/vendors/${id}`)
  if (!resp.ok) throw new Error('Vendor not found')
  return resp.json()
}

async function getVendorRatings(id: string): Promise<{ ratings: Rating[] }> {
  const resp = await fetch(`${API_BASE}/api/vendors/${id}/ratings`)
  if (!resp.ok) throw new Error('Failed to load ratings')
  return resp.json()
}

export default function PartnerDetail() {
  const { vendor_id } = useParams<{ vendor_id: string }>()
  const { user, getIdToken } = useAuth()

  const { data: vendor, loading: vendorLoading } = useApi(() => getVendor(vendor_id!), [vendor_id])
  const { data: ratingsData, loading: ratingsLoading } = useApi(() => getVendorRatings(vendor_id!), [vendor_id])

  usePageMeta(vendor?.name || 'Partner', vendor?.description || '')

  const [stars, setStars] = useState<number>(5)
  const [savings, setSavings] = useState<string>('')
  const [submitting, setSubmitting] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const handleSubmitRating = async () => {
    if (!user) {
      setMessage({ type: 'error', text: 'Please sign in first' })
      return
    }

    setSubmitting(true)
    try {
      const token = await getIdToken()
      const resp = await fetch(`${API_BASE}/api/vendors/${vendor_id}/ratings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          stars,
          savings_amount: savings ? parseInt(savings) : 0
        })
      })

      if (!resp.ok) {
        const err = await resp.json()
        throw new Error(err.error || 'Failed to submit rating')
      }

      setMessage({ type: 'success', text: 'Thank you for your rating!' })
      setStars(5)
      setSavings('')
      setTimeout(() => window.location.reload(), 1500)
    } catch (err) {
      setMessage({ type: 'error', text: err instanceof Error ? err.message : 'Error submitting rating' })
    } finally {
      setSubmitting(false)
    }
  }

  if (vendorLoading) return <div className="min-h-[100dvh] flex items-center justify-center"><div className="text-cool-grey">Loading...</div></div>
  if (!vendor) return <div className="min-h-[100dvh] flex items-center justify-center"><div className="text-destructive">Vendor not found</div></div>

  const ratings = ratingsData?.ratings || []

  return (
    <div className="min-h-[100dvh]">
      <div className="bg-white border-b border-light-grey pt-nav">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 pt-10 pb-10">
          <Link to="/partners" className="font-body text-caption text-cool-grey hover:text-deep-navy mb-5 inline-block">
            ← Back to Partners
          </Link>

          <div className="flex items-start gap-8">
            {vendor.logo_url && (
              <img src={vendor.logo_url} alt={vendor.name} className="w-24 h-24 object-contain" />
            )}
            <div className="flex-1">
              <h1 className="font-display italic text-deep-navy text-3xl mb-2">{vendor.name}</h1>
              <p className="text-cool-grey text-sm mb-4 capitalize">{vendor.category.replace(/_/g, ' ')}</p>
              <p className="text-deep-navy text-base mb-4">{vendor.description}</p>
              
              {vendor.website && (
                <a href={normalizeExternalUrl(vendor.website) || undefined} target="_blank" rel="noopener noreferrer" className="text-soft-gold font-medium hover:underline text-sm">
                  Visit Website →
                </a>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="bg-warm-cream py-12">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div>
              <div className="bg-white rounded-lg border border-light-grey p-6 mb-6">
                <h3 className="font-bold text-deep-navy mb-4">Discount Code</h3>
                <div className="bg-soft-gold/10 rounded p-4 text-center mb-3">
                  <div className="font-mono font-bold text-soft-gold text-lg">{vendor.discount_code}</div>
                </div>
                <p className="text-sm text-cool-grey">{vendor.discount_description}</p>
              </div>

              <div className="bg-white rounded-lg border border-light-grey p-6">
                <h3 className="font-bold text-deep-navy mb-4">Community Impact</h3>
                <div className="space-y-3">
                  <div>
                    <div className="text-2xl font-bold text-soft-gold">
                      {vendor.avg_rating ? vendor.avg_rating.toFixed(1) : '—'}
                    </div>
                    <div className="text-xs text-cool-grey">Average rating ({vendor.rating_count} ratings)</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-deep-navy">
                      ${(vendor.total_savings / 1000).toFixed(1)}K
                    </div>
                    <div className="text-xs text-cool-grey">Collective savings</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="lg:col-span-2">
              {user ? (
                <div className="bg-white rounded-lg border border-light-grey p-6 mb-8">
                  <h3 className="font-bold text-deep-navy mb-4">Share Your Experience</h3>
                  
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-deep-navy mb-2">Rating</label>
                    <div className="flex gap-2">
                      {[1, 2, 3, 4, 5].map((s) => (
                        <button
                          key={s}
                          onClick={() => setStars(s)}
                          className={`text-3xl transition-transform ${s <= stars ? 'text-soft-gold scale-110' : 'text-light-grey'}`}
                        >
                          ★
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="mb-6">
                    <label className="block text-sm font-medium text-deep-navy mb-2">
                      Savings (optional, whole dollars)
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="999999"
                      value={savings}
                      onChange={(e) => setSavings(e.target.value)}
                      placeholder="e.g., 2400"
                      className="w-full px-3 py-2 border border-light-grey rounded-lg focus:ring-2 focus:ring-soft-gold/30 outline-none"
                    />
                    <p className="text-xs text-cool-grey mt-1">How much did you save using this vendor?</p>
                  </div>

                  {message && (
                    <div className={`p-3 rounded mb-4 text-sm ${
                      message.type === 'success' 
                        ? 'bg-green-50 border border-green-200 text-green-800'
                        : 'bg-destructive/5 border border-destructive/20 text-red-800'
                    }`}>
                      {message.text}
                    </div>
                  )}

                  <button
                    onClick={handleSubmitRating}
                    disabled={submitting}
                    className="w-full px-4 py-3 bg-soft-gold text-white rounded-lg font-medium hover:bg-soft-gold/90 disabled:opacity-50 transition-colors"
                  >
                    {submitting ? 'Submitting...' : 'Submit Rating'}
                  </button>
                </div>
              ) : (
                <div className="bg-warm-cream border border-light-grey rounded-lg p-6 mb-8 text-center">
                  <p className="text-cool-grey mb-3">Sign in to rate this partner</p>
                </div>
              )}

              <div className="bg-white rounded-lg border border-light-grey p-6">
                <h3 className="font-bold text-deep-navy mb-4">
                  Member Reviews ({ratings.length})
                </h3>
                {ratingsLoading ? (
                  <p className="text-cool-grey text-sm">Loading reviews...</p>
                ) : ratings.length === 0 ? (
                  <p className="text-cool-grey text-sm">No ratings yet. Be the first!</p>
                ) : (
                  <div className="space-y-4">
                    {ratings.map((r, i) => (
                      <div key={i} className="border-b border-light-grey pb-4 last:border-b-0">
                        <div className="flex justify-between items-start mb-2">
                          <div className="text-soft-gold">{'★'.repeat(r.stars)}{'☆'.repeat(5 - r.stars)}</div>
                          <div className="text-xs text-cool-grey">{new Date(r.created_at).toLocaleDateString()}</div>
                        </div>
                        {r.savings_amount > 0 && (
                          <p className="text-sm text-deep-navy font-medium">Saved ${r.savings_amount}</p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
