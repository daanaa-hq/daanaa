import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { useApi } from '../hooks/useApi'

const API_BASE = import.meta.env.VITE_API_URL || ''

interface Vendor {
  vendor_id: string
  name: string
  category: string
  description: string
  website: string
  logo_url: string
  discount_code: string
  discount_description: string
  avg_rating: number | null
  rating_count: number
  total_savings: number
}

async function getVendors(): Promise<{ vendors: Vendor[] }> {
  const resp = await fetch(`${API_BASE}/api/vendors`)
  if (!resp.ok) throw new Error(`API error: ${resp.status}`)
  return resp.json()
}

export default function Partners() {
  usePageMeta('Community Partners', 'Discover vendors rated by nonprofit members.')
  const { data: vendorsData, loading } = useApi(getVendors, [])
  const [sortBy, setSortBy] = useState<'rating' | 'savings'>('rating')

  const vendors = vendorsData?.vendors || []
  const sorted = [...vendors].sort((a, b) => 
    sortBy === 'rating' ? (b.avg_rating || 0) - (a.avg_rating || 0) : b.total_savings - a.total_savings
  )

  return (
    <div className="min-h-[100dvh]">
      <div className="bg-white border-b border-light-grey pt-[72px]">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 pt-10 pb-10">
          <h1 className="font-display italic text-deep-navy" style={{ fontSize: 'clamp(32px, 4vw, 48px)' }}>
            Community Partners
          </h1>
          <p className="mt-3 font-body text-[16px] text-cool-grey max-w-[640px]">
            Services rated by nonprofit members. Use discount codes below.
          </p>
          <p className="mt-4 font-body text-[12px] text-cool-grey bg-warm-cream border border-light-grey rounded p-3">
            Ratings are anonymous. Daanaa does not endorse these services. Ratings reflect real experiences from nonprofit members.
          </p>
        </div>
      </div>

      <div className="bg-warm-cream py-12">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
          <div className="flex gap-3 mb-8">
            {['rating', 'savings'].map((opt) => (
              <button
                key={opt}
                onClick={() => setSortBy(opt as any)}
                className={`px-4 py-2 rounded-full font-body text-sm font-medium ${
                  sortBy === opt ? 'bg-soft-gold text-white' : 'bg-white border border-light-grey'
                }`}
              >
                {opt === 'rating' ? '⭐ Rating' : '💰 Savings'}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="text-center py-12 text-cool-grey">Loading...</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {sorted.map((v) => (
                <Link key={v.vendor_id} to={`/partners/${v.vendor_id}`}
                  className="block bg-white rounded-lg border border-light-grey hover:border-soft-gold p-6"
                >
                  <h3 className="font-bold text-deep-navy mb-2">{v.name}</h3>
                  <p className="text-sm text-cool-grey mb-3">{v.description}</p>
                  <div className="flex justify-between items-center border-t border-light-grey pt-3">
                    <div>
                      {v.avg_rating ? (
                        <div className="text-sm font-medium">{v.avg_rating.toFixed(1)} ⭐ ({v.rating_count})</div>
                      ) : (
                        <div className="text-xs text-cool-grey">No ratings yet</div>
                      )}
                    </div>
                    <div className="text-right">
                      <div className="font-medium">${(v.total_savings / 1000).toFixed(1)}K</div>
                      <div className="text-xs text-cool-grey">saved</div>
                    </div>
                  </div>
                  <div className="mt-3 bg-soft-gold/10 rounded p-2 text-center">
                    <div className="font-mono font-bold text-soft-gold text-sm">{v.discount_code}</div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
