import React, { useState } from 'react'
import { Link } from 'react-router-dom'
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
  const { isInWallet, addOrg, getIntent } = useWallet()
  const [state, setState] = useState<ButtonState>('idle')
  const [savedWebsite, setSavedWebsite] = useState<string | undefined>(undefined)

  const alreadyInWallet = isInWallet(ein)

  const handleClick = async () => {
    try {
      setState('loading')

      const apiOrg = await getOrganization(ein)

      const websiteUrl = (apiOrg.website_status === 'ok' && apiOrg.website) ? apiOrg.website : undefined
      const walletOrg: WalletOrg = {
        ein: apiOrg.EIN || ein,
        name: apiOrg.organization_name || orgName,
        mission: apiOrg.mission || '',
        location: [apiOrg.CITY, apiOrg.STATE].filter(Boolean).join(', ') || '',
        cause: apiOrg.cause_tags || [],
        merit_score_v5: apiOrg.v5_context?.score.percentile ?? 0,
        merit_health_signal_v5: apiOrg.v5_context?.score.health_signal ?? 'STABLE',
        is_hidden_gem: !!(apiOrg.is_hidden_gem),
        website: websiteUrl,
        bookmarkedAt: Date.now(),
      }

      addOrg(walletOrg)
      setSavedWebsite(websiteUrl)
      setState('success')

      if (onAdded) onAdded(ein)

      // Extend to 10s so the intent prompt is visible (implementation intentions window)
      setTimeout(() => setState('idle'), 10000)
    } catch {
      setState('error')
    }
  }

  const handleRetry = () => {
    setState('idle')
    handleClick()
  }

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
    const intentAlreadySet = getIntent(ein)
    return (
      <div className="flex flex-col gap-1.5">
        <button
          type="button"
          disabled
          aria-label={`Added ${orgName} to wallet`}
          className="inline-flex items-center justify-center gap-2 px-5 py-1.5 rounded-full font-body text-[13px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 cursor-default"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          Saved
        </button>
        {savedWebsite && (
          <a
            href={savedWebsite}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center gap-1.5 font-body text-[12px] text-soft-gold hover:text-bright-gold transition-colors text-center leading-snug"
            aria-label={`Visit ${orgName}'s website`}
          >
            Visit their website
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M7 17 17 7M17 7H8M17 7v9"/></svg>
          </a>
        )}
        {!savedWebsite && !intentAlreadySet && (
          <Link
            to="/wallet"
            className="font-body text-[12px] text-soft-gold hover:text-bright-gold transition-colors text-center leading-snug"
            aria-label="Set a giving plan for this organization"
          >
            How would you like to support them? →
          </Link>
        )}
      </div>
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
