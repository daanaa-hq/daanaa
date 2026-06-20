import { useState, useEffect } from 'react'
import type { ApiOrganization } from '../data/api'

interface DonationAttributionBannerProps {
  org: ApiOrganization
}

export default function DonationAttributionBanner({ org }: DonationAttributionBannerProps) {
  const [dismissed, setDismissed] = useState(false)
  const [loading, setLoading] = useState(false)

  // Check if already dismissed in this session (24h window via localStorage)
  useEffect(() => {
    const storageKey = `daanaa_donation_banner_${org.EIN}`
    const dismissedAt = localStorage.getItem(storageKey)
    if (dismissedAt) {
      const dismissTime = parseInt(dismissedAt, 10)
      const hoursSinceDismiss = (Date.now() - dismissTime) / (1000 * 60 * 60)
      if (hoursSinceDismiss < 24) {
        setDismissed(true)
      } else {
        localStorage.removeItem(storageKey)
      }
    }
  }, [org.EIN])

  const handleConfirm = () => {
    // Dismiss immediately for good UX, then fire API in background
    const storageKey = `daanaa_donation_banner_${org.EIN}`
    localStorage.setItem(storageKey, Date.now().toString())
    setDismissed(true)
    setLoading(false)

    fetch('/api/impact/log-donation-attribution', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ein: org.EIN }),
    }).catch(() => {/* endpoint not yet live, ignore */})
  }

  if (dismissed) return null

  return (
    <div className="bg-soft-gold/5 border border-soft-gold/20 rounded-xl p-4 mb-6">
      <div className="flex items-center justify-between gap-4">
        <p className="font-body text-[13px] text-deep-navy flex-1">
          Did Daanaa help you find {org.organization_name}? Let us know — it helps us measure our reach.
        </p>
        <button
          onClick={handleConfirm}
          disabled={loading}
          className="shrink-0 px-4 py-2 bg-soft-gold text-deep-navy rounded-xl font-body text-[13px] font-semibold hover:bg-bright-gold disabled:opacity-50 transition-colors"
        >
          {loading ? 'Saving...' : 'Yes, it did'}
        </button>
      </div>
    </div>
  )
}
