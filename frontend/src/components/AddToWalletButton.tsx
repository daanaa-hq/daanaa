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
        mission: apiOrg.mission || '',
        location: [apiOrg.CITY, apiOrg.STATE].filter(Boolean).join(', ') || '',
        cause: apiOrg.cause_tags || [],
        merit_score_v5: apiOrg.v5_context?.score.percentile ?? 0,
        merit_health_signal_v5: apiOrg.v5_context?.score.health_signal ?? 'STABLE',
        is_hidden_gem: !!(apiOrg as any).is_hidden_gem,
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
        className="inline-flex items-center justify-center gap-2 px-5 py-1.5 rounded-full font-body text-[13px] font-semibold text-soft-gold border border-soft-gold cursor-default"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="#C9A96E" stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/>
        </svg>
        Saved to Wallet
      </button>
    )
  }

  if (state === 'loading') {
    return (
      <button
        type="button"
        disabled
        aria-label={`Adding ${orgName} to wallet`}
        className="inline-flex items-center justify-center gap-2 px-5 py-1.5 rounded-full font-body text-[13px] font-semibold bg-soft-gold/50 text-deep-navy cursor-default"
      >
        <span className="w-3 h-3 border border-deep-navy border-t-transparent rounded-full animate-spin" />
        Adding...
      </button>
    )
  }

  if (state === 'success') {
    return (
      <button
        type="button"
        disabled
        aria-label={`Added ${orgName} to wallet`}
        className="inline-flex items-center justify-center gap-2 px-5 py-1.5 rounded-full font-body text-[13px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 cursor-default"
      >
        Added to Wallet
      </button>
    )
  }

  if (state === 'error') {
    return (
      <div className="flex items-center gap-2">
        <span className="font-body text-[13px] text-red-600">Could not add.</span>
        <button
          type="button"
          onClick={handleRetry}
          aria-label={`Try adding ${orgName} again`}
          className="font-body text-[13px] text-soft-gold hover:text-bright-gold underline transition-colors"
        >
          Try again
        </button>
      </div>
    )
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      aria-label={`Add ${orgName} to wallet`}
      className="inline-flex items-center justify-center gap-2 px-5 py-1.5 rounded-full font-body text-[13px] font-semibold bg-soft-gold text-deep-navy hover:bg-bright-gold transition-colors"
    >
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/>
      </svg>
      Save to Wallet
    </button>
  )
}
