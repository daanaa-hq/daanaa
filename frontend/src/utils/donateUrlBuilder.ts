/**
 * Donate URL Builder — Pre-fill Donor Data (Phase 3A)
 *
 * Builds "Donate Now" links with donor data from wallet:
 * - Donor email (from Google sign-in or manual entry)
 * - Donor name (from wallet)
 * - Suggested amount (from giving intent or recent donation)
 *
 * Stewardship P2: Only sends data to org's own donate processor
 * Stewardship P3: Evidence-based (shows effectiveness of pre-fill)
 *
 * Usage:
 *   const url = buildDonateUrl(org, donorData)
 *   window.location.href = url
 */

export interface DonorData {
  email?: string
  name?: string
  suggestedAmount?: number
  trackingId?: string  // From completion tracking
}

export interface DonateUrlOptions {
  source?: 'directory' | 'wallet' | 'search' | 'org_detail'
  addTracking?: boolean
}

/**
 * Build a donate URL with pre-filled donor data
 *
 * Handles different processor formats:
 * - Stripe: ?email=X&name=Y&amount=Z
 * - PayPal: ?email=X&amount=Z
 * - Custom Givebutter: ?donor_email=X&donor_name=Y
 * - GiveWP: ?email=X
 */
export function buildDonateUrl(
  donateUrl: string,
  donorData: DonorData,
  options: DonateUrlOptions = {}
): string {
  if (!donateUrl) return ''

  const params = new URLSearchParams()

  // Add donor data to URL
  if (donorData.email) {
    // Most processors expect one of these keys
    params.append('email', donorData.email)
    params.append('donor_email', donorData.email)
  }

  if (donorData.name) {
    params.append('name', donorData.name)
    params.append('donor_name', donorData.name)
  }

  if (donorData.suggestedAmount && donorData.suggestedAmount > 0) {
    params.append('amount', donorData.suggestedAmount.toString())
    params.append('suggested_amount', donorData.suggestedAmount.toString())
  }

  // Add tracking ID for completion measurement (Phase 3A)
  if (options.addTracking && donorData.trackingId) {
    params.append('tracking_id', donorData.trackingId)
  }

  // Add source for analytics (Phase 3A measurement)
  if (options.source) {
    params.append('source', options.source)
  }

  // Build final URL
  const separator = donateUrl.includes('?') ? '&' : '?'
  const paramString = params.toString()

  return paramString ? `${donateUrl}${separator}${paramString}` : donateUrl
}

/**
 * Generate suggested donation amounts based on giving history
 *
 * Returns: [low, medium, high] suggestions
 */
export function suggestedAmounts(
  previousDonations: number[] = [],
  defaultSuggestions: number[] = [25, 50, 100]
): number[] {
  if (previousDonations.length === 0) {
    return defaultSuggestions
  }

  const avg = previousDonations.reduce((a, b) => a + b, 0) / previousDonations.length
  const max = Math.max(...previousDonations)

  return [
    Math.round(avg * 0.5),
    Math.round(avg),
    Math.round(max * 1.25)
  ]
}

/**
 * Extract donor data from wallet context
 *
 * Priority: Wallet data > Google sign-in > empty
 */
export function extractDonorDataFromWallet(wallet: any): DonorData {
  return {
    email: wallet?.email || undefined,
    name: wallet?.donor_name || undefined,
    suggestedAmount: wallet?.suggested_amount || undefined
  }
}

/**
 * Privacy-safe: log donation attempt for completion tracking
 *
 * This fires BEFORE redirecting to prevent cookie/data leakage
 */
export async function logDonationAttempt(
  ein: string,
  donorData: DonorData,
  source: string
): Promise<string | null> {
  try {
    const response = await fetch('/api/donate/track', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ein,
        donor_email: donorData.email,
        donor_name: donorData.name,
        suggested_amount: donorData.suggestedAmount,
        traffic_source: source
      })
    })

    if (response.ok) {
      const data = await response.json()
      return data.tracking_id
    }
  } catch (error) {
    console.error('Failed to log donation attempt:', error)
  }

  return null
}

/**
 * Complete donate flow: log → build URL → redirect
 *
 * Usage (in OrgInfoHierarchy.tsx or donate button):
 *
 *   const handleDonate = async (org, donorData) => {
 *     const trackingId = await logDonationAttempt(org.ein, donorData, 'org_detail')
 *     const url = buildDonateUrl(org.donate_url, donorData, {
 *       addTracking: !!trackingId,
 *       source: 'org_detail'
 *     })
 *     if (trackingId) {
 *       donorData.trackingId = trackingId
 *     }
 *     window.location.href = url
 *   }
 */
export async function completeDonateFlow(
  ein: string,
  donateUrl: string,
  donorData: DonorData,
  source: 'directory' | 'wallet' | 'search' | 'org_detail' = 'org_detail'
): Promise<void> {
  // 1. Log the attempt (for completion tracking)
  const trackingId = await logDonationAttempt(ein, donorData, source)

  // 2. Build URL with donor data + tracking
  const urlWithTracking: DonorData = {
    ...donorData,
    trackingId: trackingId || undefined
  }

  const finalUrl = buildDonateUrl(donateUrl, urlWithTracking, {
    addTracking: !!trackingId,
    source
  })

  // 3. Redirect
  window.location.href = finalUrl
}

/**
 * Example: Using in a React component
 *
 * ```tsx
 * import { buildDonateUrl, completeDonateFlow } from '../utils/donateUrlBuilder'
 *
 * export function DonateButton({ org, walletData }) {
 *   const handleClick = async () => {
 *     await completeDonateFlow(
 *       org.ein,
 *       org.donate_url,
 *       {
 *         email: walletData?.email,
 *         name: walletData?.donor_name,
 *         suggestedAmount: 50
 *       },
 *       'org_detail'
 *     )
 *   }
 *
 *   return (
 *     <button onClick={handleClick}>
 *       Donate Now
 *     </button>
 *   )
 * }
 * ```
 */
