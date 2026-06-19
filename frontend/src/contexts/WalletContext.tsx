import React, { createContext, useContext, useReducer, useEffect, useCallback } from 'react'
import type {
  Wallet,
  WalletOrg,
  GivingIntent,
  WalletContextType,
} from '../types/wallet'
import { isValidWallet, isValidWalletOrg, isValidGivingIntent } from '../types/wallet'
import { validateGivingIntent, logValidationError } from '../utils/walletValidation'

const STORAGE_KEY = 'daanaa_wallet'
const CURRENT_VERSION = 1

/**
 * Default/empty wallet state
 */
function createEmptyWallet(): Wallet {
  return {
    version: CURRENT_VERSION,
    lastUpdated: Date.now(),
    orgs: [],
    syncedWithServer: false,
  }
}

/**
 * Wallet actions for useReducer
 */
type WalletAction =
  | { type: 'ADD_ORG'; payload: WalletOrg }
  | { type: 'REMOVE_ORG'; payload: string } // ein
  | { type: 'UPDATE_INTENT'; payload: { ein: string; intent: GivingIntent } }
  | { type: 'HYDRATE'; payload: Wallet }
  | { type: 'SYNC_WITH_SERVER'; payload: { googleEmail: string } }
  | { type: 'LOGOUT_AND_CLEAR_SYNC' }

/**
 * Reducer for wallet state management
 * All mutations return new wallet with updated lastUpdated timestamp
 */
function walletReducer(state: Wallet, action: WalletAction): Wallet {
  switch (action.type) {
    case 'ADD_ORG': {
      // Prevent duplicates
      if (state.orgs.some(org => org.ein === action.payload.ein)) {
        return state
      }
      return {
        ...state,
        orgs: [...state.orgs, action.payload],
        lastUpdated: Date.now(),
      }
    }

    case 'REMOVE_ORG': {
      const orgs = state.orgs.filter(org => org.ein !== action.payload)
      if (orgs.length === state.orgs.length) {
        // Not found, no change
        return state
      }
      return {
        ...state,
        orgs,
        lastUpdated: Date.now(),
      }
    }

    case 'UPDATE_INTENT': {
      const orgIndex = state.orgs.findIndex(org => org.ein === action.payload.ein)
      if (orgIndex === -1) {
        return state
      }
      const newOrgs = [...state.orgs]
      newOrgs[orgIndex] = {
        ...newOrgs[orgIndex],
        givingIntent: action.payload.intent,
      }
      return {
        ...state,
        orgs: newOrgs,
        lastUpdated: Date.now(),
      }
    }

    case 'HYDRATE': {
      // Only hydrate if valid wallet
      if (isValidWallet(action.payload)) {
        return action.payload
      }
      return state
    }

    case 'SYNC_WITH_SERVER': {
      return {
        ...state,
        syncedWithServer: true,
        googleEmail: action.payload.googleEmail,
        lastUpdated: Date.now(),
      }
    }

    case 'LOGOUT_AND_CLEAR_SYNC': {
      return {
        ...state,
        syncedWithServer: false,
        googleEmail: undefined,
        lastUpdated: Date.now(),
      }
    }

    default:
      return state
  }
}

export const WalletContext = createContext<WalletContextType | null>(null)

interface WalletProviderProps {
  children: React.ReactNode
}

/**
 * WalletProvider manages wallet state and localStorage persistence
 * Recovers from corrupted localStorage gracefully
 */
export function WalletProvider({ children }: WalletProviderProps) {
  const [wallet, dispatch] = useReducer(walletReducer, createEmptyWallet())

  // Hydrate from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored) as unknown
        if (isValidWallet(parsed)) {
          dispatch({ type: 'HYDRATE', payload: parsed })
        } else {
          console.warn('[Wallet] Corrupted data in localStorage, starting fresh')
          localStorage.removeItem(STORAGE_KEY)
        }
      }
    } catch (err) {
      console.error('[Wallet] Failed to hydrate from localStorage:', err)
      localStorage.removeItem(STORAGE_KEY)
    }
  }, [])

  // Persist wallet to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(wallet))
    } catch (err: any) {
      // Handle quota exceeded
      if (err.name === 'QuotaExceededError') {
        console.error('[Wallet] localStorage quota exceeded. Wallet full.')
        // In a real app, we'd show a toast/error UI
      } else {
        console.error('[Wallet] Failed to persist wallet:', err)
      }
    }
  }, [wallet])

  // Implement WalletContextType methods
  const addOrg = useCallback((org: WalletOrg) => {
    if (!isValidWalletOrg(org)) {
      logValidationError('addOrg', new Error('Invalid org structure'))
      return
    }
    dispatch({ type: 'ADD_ORG', payload: org })
  }, [])

  const removeOrg = useCallback((ein: string) => {
    dispatch({ type: 'REMOVE_ORG', payload: ein })
  }, [])

  const updateIntent = useCallback((ein: string, intent: GivingIntent) => {
    // Validate structure first
    if (!isValidGivingIntent(intent)) {
      logValidationError('updateIntent', new Error('Invalid intent structure'))
      return
    }

    // Then validate individual fields (amount, hours, notes)
    try {
      validateGivingIntent(intent)
    } catch (err) {
      logValidationError('updateIntent', err as Error)
      return
    }

    dispatch({ type: 'UPDATE_INTENT', payload: { ein, intent } })
  }, [])

  const isInWallet = useCallback(
    (ein: string): boolean => wallet.orgs.some(org => org.ein === ein),
    [wallet.orgs]
  )

  const getIntent = useCallback(
    (ein: string): GivingIntent | undefined => {
      return wallet.orgs.find(org => org.ein === ein)?.givingIntent
    },
    [wallet.orgs]
  )

  const syncToServer = useCallback(
    async (googleEmail: string, token: string): Promise<void> => {
      if (!googleEmail || !token) {
        throw new Error('googleEmail and token are required for sync')
      }
      const eins = wallet.orgs.map(org => org.ein)
      const base = import.meta.env.VITE_API_URL || 'http://localhost:5000'
      const resp = await fetch(`${base}/api/wallet/sync-saves`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ eins }),
      })
      if (!resp.ok) throw new Error(`Wallet sync failed: ${resp.status}`)
      dispatch({ type: 'SYNC_WITH_SERVER', payload: { googleEmail } })
    },
    [wallet.orgs]
  )

  const logoutAndClearSync = useCallback(() => {
    dispatch({ type: 'LOGOUT_AND_CLEAR_SYNC' })
  }, [])

  const value: WalletContextType = {
    wallet,
    addOrg,
    removeOrg,
    updateIntent,
    isInWallet,
    getIntent,
    syncToServer,
    logoutAndClearSync,
  }

  return <WalletContext.Provider value={value}>{children}</WalletContext.Provider>
}

/**
 * Hook to use wallet context
 * Throws if used outside WalletProvider
 */
export function useWallet(): WalletContextType {
  const ctx = useContext(WalletContext)
  if (!ctx) {
    throw new Error('useWallet must be used within WalletProvider')
  }
  return ctx
}
