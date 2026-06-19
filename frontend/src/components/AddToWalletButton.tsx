/**
 * AddToWalletButton: CTA button to add org to wallet
 * - Fetches full org data from API
 * - Adds to wallet with loading/success/error states
 * - Automatically resets after 3 seconds on success
 * - Shows disabled state when already in wallet
 *
 * Props:
 *   ein: Organization EIN
 *   orgName: Organization name (for aria-label)
 *   onAdded?: Callback after successful add
 */

import React, { useState } from 'react'
import { useWallet } from '../contexts/WalletContext'
import { getOrganization, type ApiOrganization } from '../data/api'
import type { WalletOrg } from '../types/wallet'

interface AddToWalletButtonProps {
  ein: string
  orgName: string
  onAdded?: (ein: string) => void
}

type ButtonState = 'idle' | 'loading' | 'success' | 'error'

export default function AddToWalletButton({
  ein,
  orgName,
  onAdded,
}: AddToWalletButtonProps) {
  const { isInWallet, addOrg } = useWallet()
  const [state, setState] = useState<ButtonState>('idle')

  const alreadyInWallet = isInWallet(ein)

  const handleClick = async () => {
    try {
      setState('loading')

      // Fetch full org data from API
      const apiOrg = await getOrganization(ein)

      // Convert ApiOrganization to WalletOrg
      const walletOrg: WalletOrg = {
        ein: apiOrg.EIN || ein,
        name: apiOrg.organization_name || orgName,
        mission: '', // Not available from API, will be empty
        location: [apiOrg.CITY, apiOrg.STATE].filter(Boolean).join(', ') || '',
        cause: [], // Not available from API, will be empty
        merit_score_v5: apiOrg.v5_context?.score.percentile || 0,
        merit_health_signal_v5: apiOrg.v5_context?.score.health_signal || 'STABLE',
        is_hidden_gem: false, // Not available from API
        donate_url: undefined,
        bookmarkedAt: Date.now(),
      }

      // Add org to wallet
      addOrg(walletOrg)

      // Show success state
      setState('success')

      // Call optional callback
      if (onAdded) {
        onAdded(ein)
      }

      // Reset after 3 seconds
      setTimeout(() => {
        setState('idle')
      }, 3000)
    } catch (error) {
      console.error('Failed to add org to wallet:', error)
      setState('error')
    }
  }

  const handleRetry = () => {
    setState('idle')
    handleClick()
  }

  // Determine button text and styling
  if (alreadyInWallet) {
    return (
      <button
        type="button"
        disabled
        aria-label={`Already in wallet: ${orgName}`}
        className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium text-gray-700 bg-gray-200 cursor-not-allowed opacity-75 transition-all"
      >
        <span>✓ Already in Wallet</span>
      </button>
    )
  }

  if (state === 'loading') {
    return (
      <button
        type="button"
        disabled
        aria-label={`Adding ${orgName} to wallet`}
        className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium text-gray-700 bg-gray-200 cursor-not-allowed opacity-75 transition-all"
      >
        <span className="animate-spin">⟳</span>
        <span>Adding...</span>
      </button>
    )
  }

  if (state === 'success') {
    return (
      <button
        type="button"
        disabled
        aria-label={`Added ${orgName} to wallet`}
        className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium text-green-700 bg-green-100 cursor-default transition-all"
      >
        <span>✓ Added to Wallet</span>
      </button>
    )
  }

  if (state === 'error') {
    return (
      <div className="flex items-center gap-2">
        <button
          type="button"
          disabled
          aria-label={`Failed to add ${orgName} to wallet`}
          className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium text-red-700 bg-red-100 cursor-default transition-all"
        >
          <span>✗ Failed to add</span>
        </button>
        <button
          type="button"
          onClick={handleRetry}
          aria-label={`Try adding ${orgName} again`}
          className="px-3 py-2 rounded-lg font-medium text-sm text-blue-600 hover:bg-blue-50 transition-colors"
        >
          Try again
        </button>
      </div>
    )
  }

  // Idle state (default)
  return (
    <button
      type="button"
      onClick={handleClick}
      aria-label={`Add ${orgName} to wallet`}
      className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium text-gray-800 bg-orange-100 hover:bg-orange-200 active:bg-orange-300 cursor-pointer transition-colors focus:outline-none focus:ring-2 focus:ring-orange-400 focus:ring-offset-2"
    >
      <span>+ Add to Wallet</span>
    </button>
  )
}
