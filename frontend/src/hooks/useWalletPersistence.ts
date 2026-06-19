/**
 * useWalletPersistence: React hook for localStorage persistence of wallet data
 * Handles:
 * - Loading wallet on mount
 * - Debounced writes on change (500ms)
 * - Quota exceeded warnings
 * - Corruption detection and recovery
 * - Cleanup on unmount
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import type { Wallet } from '../types/wallet'
import { walletStorage } from '../utils/walletStorage'

interface PersistenceState {
  synced: boolean
  error: string | null
  quotaWarning: boolean
}

/**
 * useWalletPersistence
 * @param wallet Current wallet state
 * @param isDirty Whether wallet has changed (parent component signal)
 * @param onRecovery Callback if corruption is detected and recovery succeeds
 * @returns { synced, error, quotaWarning }
 */
export function useWalletPersistence(
  wallet: Wallet,
  isDirty: boolean,
  onRecovery: (recovered: Wallet) => void
): PersistenceState {
  const [synced, setSynced] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [quotaWarning, setQuotaWarning] = useState(false)

  // Track debounce timeout
  const debounceTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Load from localStorage on mount and check for corruption
  useEffect(() => {
    try {
      // Check for corruption first
      const corruption = walletStorage.checkCorruption()
      if (corruption.corrupted) {
        if (corruption.recovered) {
          // Recovery succeeded
          console.warn('[Wallet] Data corruption detected but recovered from backup', corruption.error)
          setError(corruption.error || 'Data recovered from backup')
          onRecovery(corruption.recovered)
        } else {
          // Total loss
          console.error('[Wallet]', corruption.error)
          setError(corruption.error || 'Wallet data corrupted')
        }
        return
      }

      // If no corruption, try to load existing wallet
      const stored = walletStorage.read()
      if (stored) {
        setSynced(true)
      } else {
        setSynced(false)
      }
    } catch (err) {
      console.error('[Wallet] Failed to load from localStorage:', err)
      setError(err instanceof Error ? err.message : 'Failed to load wallet')
    }
  }, [onRecovery])

  // Write to localStorage when wallet changes (debounced)
  useEffect(() => {
    if (!isDirty) {
      return
    }

    // Cancel previous timeout if still pending
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current)
    }

    // Set new debounced write (500ms)
    debounceTimeoutRef.current = setTimeout(() => {
      try {
        walletStorage.write(wallet)

        // Check if quota is nearly exceeded
        const quota = walletStorage.getQuotaInfo()
        if (quota.percentUsed > 90) {
          setQuotaWarning(true)
        } else {
          setQuotaWarning(false)
        }

        // Clear any previous error on successful write
        setError(null)
      } catch (err: any) {
        // Handle quota exceeded
        if (err.name === 'QuotaExceededError') {
          setQuotaWarning(true)
          setError('Wallet storage quota exceeded. Please remove some orgs.')
          console.error('[Wallet] Quota exceeded:', err)
        } else {
          setError(err instanceof Error ? err.message : 'Failed to save wallet')
          console.error('[Wallet] Failed to write wallet:', err)
        }
      }
    }, 500)

    // Cleanup: cancel pending write on unmount or next change
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current)
      }
    }
  }, [wallet, isDirty])

  return {
    synced,
    error,
    quotaWarning,
  }
}
