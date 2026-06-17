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

  const handleConfirm = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/impact/log-donation-attribution', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ein: org.EIN }),
      })

      if (response.ok) {
        // Mark as dismissed for 24h
        const storageKey = `daanaa_donation_banner_${org.EIN}`
        localStorage.setItem(storageKey, Date.now().toString())
        setDismissed(true)
      }
    } catch (error) {
      console.error('Error logging donation attribution:', error)
    } finally {
      setLoading(false)
    }
  }

  if (dismissed) return null

  return (
    <div className="bg-soft-gold/5 border border-soft-gold/20 rounded-lg p-4 mb-6">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <p className="text-sm text-deep-navy font-medium">
            Just donated? 💝 If Daanaa helped you find {org.organization_name}, let us know. It helps us measure our impact.
          </p>
        </div>
        <button
          onClick={handleConfirm}
          disabled={loading}
          className="shrink-0 px-4 py-2 bg-soft-gold text-white rounded-lg font-medium text-sm hover:bg-soft-gold/90 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Confirming...' : 'Yes, helped me'}
        </button>
      </div>
    </div>
  )
}
