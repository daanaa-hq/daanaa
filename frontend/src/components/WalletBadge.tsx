/**
 * WalletBadge: Badge showing wallet count + status
 * - Supports three styles: inline, badge, pill
 * - Can filter by giving intent (giving/volunteer)
 * - Shows "Empty" when 0 orgs (inline only)
 *
 * Props:
 *   style?: "inline" | "badge" | "pill" (default: inline)
 *   intent?: "giving" | "volunteer" (optional filter)
 *
 * Usage:
 *   <WalletBadge style="inline" />
 *   <WalletBadge style="badge" />
 *   <WalletBadge style="pill" intent="giving" />
 */

import React, { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useWallet } from '../contexts/WalletContext'
import type { GivingIntent, WalletEntry } from '../types/wallet'

interface WalletBadgeProps {
  style?: 'inline' | 'badge' | 'pill'
  intent?: 'giving' | 'volunteer'
}

export default function WalletBadge({
  style = 'inline',
  intent,
}: WalletBadgeProps) {
  const { entries } = useWallet()

  // Compute filtered count based on intent
  const count = useMemo(() => {
    if (!intent) {
      return entries.length
    }

    return entries.filter((entry: WalletEntry) => {
      const orgIntent = entry.givingIntent as GivingIntent | undefined
      return orgIntent && orgIntent.type === intent
    }).length
  }, [entries, intent])

  // Determine label text
  const label = `${count} organization${count !== 1 ? 's' : ''} in your wallet`
  const displayText =
    count === 0 ? 'Empty' : `${count} organization${count !== 1 ? 's' : ''} in wallet`

  // Inline style (default)
  if (style === 'inline') {
    return (
      <span role="status" aria-label={label} className="text-sm text-gray-600">
        {displayText}
      </span>
    )
  }

  // Badge style (red circle with count)
  if (style === 'badge') {
    if (count === 0) {
      return null
    }

    return (
      <span
        role="status"
        aria-label={label}
        className="inline-flex items-center justify-center w-6 h-6 text-xs font-bold text-white bg-red-500 rounded-full"
      >
        {count}
      </span>
    )
  }

  // Pill style (clickable button to /giving-wallet)
  if (style === 'pill') {
    return (
      <Link
        to="/giving-wallet"
        aria-label={label}
        className="inline-flex items-center gap-1 px-3 py-1 text-sm font-medium text-gray-800 bg-orange-100 hover:bg-orange-200 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-orange-400 focus:ring-offset-2"
      >
        <span>💾 Wallet</span>
        <span className="font-bold">{count}</span>
      </Link>
    )
  }

  return null
}
