import React, {
  createContext, useContext, useReducer, useCallback,
  useEffect, useRef, useState,
} from 'react'
import type { WalletEntry, GivingIntent, WalletContextType } from '../types/wallet'
import { isValidWalletEntry, isLegacyWalletV1 } from '../types/wallet'
import { validateGivingIntent, logValidationError } from '../utils/walletValidation'
import {
  deriveAll, encryptWallet, decryptWallet,
  deriveRawKeyBytes, importKeyFromBytes,
} from '../utils/wallet.crypto'
import { getApiBase } from '../utils/env'

const LS_KEY_HASH = 'dw_kh'
const LS_SALT    = 'dw_s'
const SS_RAW_KEY = 'dw_k'

// ─── State ───────────────────────────────────────────────────────────────────

type State = {
  entries: WalletEntry[]
  keyHash: string | null
  salt: string | null
  encKey: CryptoKey | null
  syncStatus: 'idle' | 'syncing' | 'error'
}

type Action =
  | { type: 'HYDRATE'; entries: WalletEntry[]; keyHash: string; salt: string; encKey: CryptoKey }
  | { type: 'ADD'; ein: string }
  | { type: 'REMOVE'; ein: string }
  | { type: 'UPDATE_INTENT'; ein: string; intent: GivingIntent }
  | { type: 'SET_SYNC_STATUS'; status: State['syncStatus'] }
  | { type: 'LOCK' }

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'HYDRATE':
      return { ...state, entries: action.entries, keyHash: action.keyHash,
               salt: action.salt, encKey: action.encKey, syncStatus: 'idle' }
    case 'ADD': {
      if (state.entries.some(e => e.ein === action.ein)) return state
      return { ...state, entries: [...state.entries, { ein: action.ein, bookmarkedAt: Date.now() }] }
    }
    case 'REMOVE':
      return { ...state, entries: state.entries.filter(e => e.ein !== action.ein) }
    case 'UPDATE_INTENT': {
      const idx = state.entries.findIndex(e => e.ein === action.ein)
      if (idx === -1) return state
      const next = [...state.entries]
      next[idx] = { ...next[idx], givingIntent: action.intent }
      return { ...state, entries: next }
    }
    case 'SET_SYNC_STATUS':
      return { ...state, syncStatus: action.status }
    case 'LOCK':
      return { entries: [], keyHash: null, salt: null, encKey: null, syncStatus: 'idle' }
    default:
      return state
  }
}

// ─── Context ─────────────────────────────────────────────────────────────────

export const WalletContext = createContext<WalletContextType | null>(null)

export function WalletProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(reducer, {
    entries: [], keyHash: null, salt: null, encKey: null, syncStatus: 'idle',
  })
  const syncTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const [migrationData, setMigrationData] = useState<WalletEntry[] | null>(null)

  // On mount: detect legacy v1 wallet
  useEffect(() => {
    try {
      const raw = localStorage.getItem('daanaa_wallet')
      if (!raw) return
      const parsed = JSON.parse(raw)
      if (!isLegacyWalletV1(parsed)) return
      const entries: WalletEntry[] = parsed.orgs.map((o: any) => ({
        ein: o.ein,
        bookmarkedAt: o.bookmarkedAt ?? Date.now(),
        givingIntent: o.givingIntent,
      })).filter(isValidWalletEntry)
      if (entries.length > 0) setMigrationData(entries)
    } catch { /* ignore */ }
  }, [])

  // On mount: try to restore session key from sessionStorage
  useEffect(() => {
    let active = true
    const rawB64 = sessionStorage.getItem(SS_RAW_KEY)
    const keyHash = localStorage.getItem(LS_KEY_HASH)
    const salt = localStorage.getItem(LS_SALT)
    if (!rawB64 || !keyHash || !salt) return

    ;(async () => {
      try {
        const bytes = Uint8Array.from(atob(rawB64), c => c.charCodeAt(0))
        const encKey = await importKeyFromBytes(bytes)
        const r = await fetch(`${getApiBase()}/api/wallet/sync?keyHash=${keyHash}`)
        if (!r.ok || !active) return
        const data = await r.json()
        if (!data.found || !active) return
        const rawEntries = await decryptWallet(data.ciphertext, data.iv, encKey)
        const entries = rawEntries.filter(isValidWalletEntry)
        if (active) dispatch({ type: 'HYDRATE', entries, keyHash, salt, encKey })
      } catch {
        if (active) sessionStorage.removeItem(SS_RAW_KEY)
      }
    })()

    return () => { active = false }
  }, [])

  // Debounced sync on entries change (only when unlocked)
  useEffect(() => {
    if (!state.encKey || !state.keyHash || !state.salt) return
    if (syncTimerRef.current) clearTimeout(syncTimerRef.current)
    syncTimerRef.current = setTimeout(async () => {
      dispatch({ type: 'SET_SYNC_STATUS', status: 'syncing' })
      try {
        const { ciphertext, iv } = await encryptWallet(state.entries, state.encKey!)
        const r = await fetch(`${getApiBase()}/api/wallet/sync`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ keyHash: state.keyHash, ciphertext, iv, salt: state.salt }),
        })
        if (!r.ok) throw new Error(`sync failed: ${r.status}`)
        dispatch({ type: 'SET_SYNC_STATUS', status: 'idle' })
      } catch {
        dispatch({ type: 'SET_SYNC_STATUS', status: 'error' })
      }
    }, 800)
    return () => { if (syncTimerRef.current) clearTimeout(syncTimerRef.current) }
  }, [state.entries, state.encKey, state.keyHash, state.salt])

  // ─── Actions ───────────────────────────────────────────────────────────────

  const addEntry = useCallback((ein: string) => {
    if (!/^\d{9}$/.test(ein)) return
    dispatch({ type: 'ADD', ein })
  }, [])

  const removeEntry = useCallback((ein: string) => {
    dispatch({ type: 'REMOVE', ein })
  }, [])

  const updateIntent = useCallback((ein: string, intent: GivingIntent) => {
    try { validateGivingIntent(intent) } catch (e) {
      logValidationError('updateIntent', e as Error); return
    }
    dispatch({ type: 'UPDATE_INTENT', ein, intent })
  }, [])

  const isInWallet = useCallback((ein: string) => state.entries.some(e => e.ein === ein), [state.entries])
  const getIntent = useCallback((ein: string) => state.entries.find(e => e.ein === ein)?.givingIntent, [state.entries])

  const setupNewWallet = useCallback(async (passphrase: string) => {
    const r = await fetch(`${getApiBase()}/api/wallet/init`, { method: 'POST' })
    const { salt: saltB64 } = await r.json()
    const saltBytes = Uint8Array.from(atob(saltB64), c => c.charCodeAt(0))
    const { encKey, keyHash } = await deriveAll(passphrase, saltBytes)
    const { ciphertext, iv } = await encryptWallet([], encKey)
    const syncResponse = await fetch(`${getApiBase()}/api/wallet/sync`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keyHash, ciphertext, iv, salt: saltB64 }),
    })
    if (!syncResponse.ok) throw new Error('Failed to save wallet to server')
    localStorage.setItem(LS_KEY_HASH, keyHash)
    localStorage.setItem(LS_SALT, saltB64)
    const rawBytes = await deriveRawKeyBytes(passphrase, saltBytes)
    sessionStorage.setItem(SS_RAW_KEY, btoa(String.fromCharCode(...rawBytes)))
    dispatch({ type: 'HYDRATE', entries: [], keyHash, salt: saltB64, encKey })
  }, [])

  const unlockWithPassphrase = useCallback(async (passphrase: string) => {
    const saltB64 = localStorage.getItem(LS_SALT)
    const storedKeyHash = localStorage.getItem(LS_KEY_HASH)
    if (!saltB64 || !storedKeyHash) throw new Error('No wallet found on this device')
    const saltBytes = Uint8Array.from(atob(saltB64), c => c.charCodeAt(0))
    const { encKey, keyHash } = await deriveAll(passphrase, saltBytes)
    const r = await fetch(`${getApiBase()}/api/wallet/sync?keyHash=${keyHash}`)
    if (r.status === 404) throw new Error('Incorrect passphrase')
    if (!r.ok) throw new Error('Server error')
    const data = await r.json()
    const rawEntries = await decryptWallet(data.ciphertext, data.iv, encKey)
    const entries = rawEntries.filter(isValidWalletEntry)
    const rawBytes = await deriveRawKeyBytes(passphrase, saltBytes)
    sessionStorage.setItem(SS_RAW_KEY, btoa(String.fromCharCode(...rawBytes)))
    dispatch({ type: 'HYDRATE', entries, keyHash, salt: saltB64, encKey })
  }, [])

  const lockWallet = useCallback(() => {
    sessionStorage.removeItem(SS_RAW_KEY)
    dispatch({ type: 'LOCK' })
  }, [])

  const deleteWallet = useCallback(async () => {
    const keyHash = localStorage.getItem(LS_KEY_HASH)
    if (keyHash) {
      await fetch(`${getApiBase()}/api/wallet/sync`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keyHash }),
      }).catch(() => {})
    }
    localStorage.removeItem(LS_KEY_HASH)
    localStorage.removeItem(LS_SALT)
    sessionStorage.removeItem(SS_RAW_KEY)
    dispatch({ type: 'LOCK' })
  }, [])

  const downloadBackup = useCallback(() => {
    const data = JSON.stringify({ version: 2, entries: state.entries, exportedAt: new Date().toISOString() }, null, 2)
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'daanaa-wallet-backup.json'; a.click()
    URL.revokeObjectURL(url)
  }, [state.entries])

  const applyMigration = useCallback(() => {
    if (!migrationData) return
    migrationData.forEach(e => {
      dispatch({ type: 'ADD', ein: e.ein })
      if (e.givingIntent) dispatch({ type: 'UPDATE_INTENT', ein: e.ein, intent: e.givingIntent })
    })
    localStorage.removeItem('daanaa_wallet')
    setMigrationData(null)
  }, [migrationData])

  const dismissMigration = useCallback(() => {
    localStorage.removeItem('daanaa_wallet')
    setMigrationData(null)
  }, [])

  return (
    <WalletContext.Provider value={{
      entries: state.entries, addEntry, removeEntry, updateIntent,
      isInWallet, getIntent, isUnlocked: state.encKey !== null,
      unlockWithPassphrase, setupNewWallet, lockWallet, deleteWallet,
      downloadBackup, syncStatus: state.syncStatus,
      migrationData, applyMigration, dismissMigration,
    }}>
      {children}
    </WalletContext.Provider>
  )
}

export function useWallet(): WalletContextType {
  const ctx = useContext(WalletContext)
  if (!ctx) throw new Error('useWallet must be used within WalletProvider')
  return ctx
}
