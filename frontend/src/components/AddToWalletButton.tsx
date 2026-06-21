import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { useWallet } from '../contexts/WalletContext'

interface AddToWalletButtonProps {
  ein: string
  orgName: string
  onAdded?: (ein: string) => void
}

type ButtonState = 'idle' | 'success'

export default function AddToWalletButton({
  ein,
  orgName,
  onAdded,
}: AddToWalletButtonProps) {
  const { isInWallet, addEntry, removeEntry, getIntent } = useWallet()
  const [state, setState] = useState<ButtonState>('idle')

  const alreadyInWallet = isInWallet(ein)

  const handleClick = () => {
    addEntry(ein)
    setState('success')

    if (onAdded) onAdded(ein)

    // Extend to 10s so the intent prompt is visible (implementation intentions window)
    setTimeout(() => setState('idle'), 10000)
  }

  const handleRemove = () => {
    removeEntry(ein)
    setState('idle')
  }

  if (alreadyInWallet) {
    const existingIntent = getIntent(ein)
    return (
      <div className="flex flex-col gap-1.5">
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
        <Link
          to={`/wallet?intent=${ein}`}
          className="font-body text-[12px] text-soft-gold hover:text-bright-gold transition-colors text-center leading-snug"
          aria-label={existingIntent ? 'Edit your giving plan' : 'Set a giving plan'}
        >
          {existingIntent ? 'Edit your giving plan →' : 'Set a giving plan →'}
        </Link>
      </div>
    )
  }

  if (state === 'success') {
    const intentAlreadySet = getIntent(ein)
    return (
      <div className="flex flex-col gap-1.5">
        <button
          type="button"
          onClick={handleRemove}
          aria-label={`Added ${orgName} to wallet — click to remove`}
          className="inline-flex items-center justify-center gap-2 px-5 py-1.5 rounded-full font-body text-[13px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-red-50 hover:text-red-700 hover:border-red-200 transition-colors"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          Saved
        </button>
        {!intentAlreadySet && (
          <Link
            to={`/wallet?intent=${ein}`}
            className="font-body text-[12px] text-soft-gold hover:text-bright-gold transition-colors text-center leading-snug"
            aria-label="Set a giving plan for this organization"
          >
            How would you like to support them? →
          </Link>
        )}
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
