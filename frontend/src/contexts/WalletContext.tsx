import React, {
  createContext, useContext, useReducer, useCallback,
  useEffect, useRef, useState,
} from 'react'
import type { WalletEntry, GivingIntent, WalletContextType, LoggedDonation, LoggedVolunteerHours } from '../types/wallet'
import { isValidWalletEntry, isLegacyWalletV1 } from '../types/wallet'
import { validateGivingIntent, logValidationError } from '../utils/walletValidation'
import {
  deriveAll, encryptWallet, decryptWallet,
  deriveRawKeyBytes, importKeyFromBytes,
} from '../utils/wallet.crypto'
import { getApiBase } from '../utils/env'

const LS_KEY_HASH = 'dw_kh'
const LS_SALT    = 'dw_s'
// SECURITY: removed SS_RAW_KEY (raw key caching). Use JWT tokens instead (see /api/wallet/token).

function uuid(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') return crypto.randomUUID()
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0
    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16)
  })
}

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
  | { type: 'LOAD_LOCAL'; entries: WalletEntry[] }
  | { type: 'MERGE_REMOTE'; entries: WalletEntry[] }
  | { type: 'ADD'; ein: string }
  | { type: 'REMOVE'; ein: string }
  | { type: 'ADD_FUNDING'; ein: string }
  | { type: 'ADD_VOLUNTEERING'; ein: string }
  | { type: 'REMOVE_FUNDING'; ein: string }
  | { type: 'REMOVE_VOLUNTEERING'; ein: string }
  | { type: 'UPDATE_INTENT'; ein: string; intent: GivingIntent }
  | { type: 'LOG_DONATION'; ein: string; donation: LoggedDonation }
  | { type: 'LOG_VOLUNTEER_HOURS'; ein: string; hours: LoggedVolunteerHours }
  | { type: 'UPDATE_DONATION_LETTER_STATUS'; ein: string; donationId: string; status: LoggedDonation['letterStatus'] }
  | { type: 'SET_SYNC_STATUS'; status: State['syncStatus'] }
  | { type: 'LOCK' }

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'HYDRATE': {
      // Migrate legacy entries that predate the funding/volunteering split → funding list
      const entries = action.entries.map(e =>
        (e.inFunding === undefined && e.inVolunteering === undefined) ? { ...e, inFunding: true } : e
      )
      return { ...state, entries, keyHash: action.keyHash, salt: action.salt, encKey: action.encKey, syncStatus: 'idle' }
    }
    case 'ADD': {
      if (state.entries.some(e => e.ein === action.ein)) return state
      return { ...state, entries: [...state.entries, { ein: action.ein, bookmarkedAt: Date.now(), inFunding: true }] }
    }
    case 'REMOVE': {
      const target = state.entries.find(e => e.ein === action.ein)
      if (!target) return state
      // If there are activity logs, preserve the entry but clear bookmark flags.
      // This prevents log data loss when a user removes an org from their wallet.
      if (target.donations?.length || target.volunteerHours?.length) {
        return {
          ...state,
          entries: state.entries.map(e =>
            e.ein === action.ein ? { ...e, inFunding: false, inVolunteering: false } : e
          ),
        }
      }
      return { ...state, entries: state.entries.filter(e => e.ein !== action.ein) }
    }
    case 'ADD_FUNDING': {
      const idx = state.entries.findIndex(e => e.ein === action.ein)
      if (idx === -1) return { ...state, entries: [...state.entries, { ein: action.ein, bookmarkedAt: Date.now(), inFunding: true }] }
      const next = [...state.entries]
      next[idx] = { ...next[idx], inFunding: true }
      return { ...state, entries: next }
    }
    case 'ADD_VOLUNTEERING': {
      const idx = state.entries.findIndex(e => e.ein === action.ein)
      if (idx === -1) return { ...state, entries: [...state.entries, { ein: action.ein, bookmarkedAt: Date.now(), inVolunteering: true }] }
      const next = [...state.entries]
      next[idx] = { ...next[idx], inVolunteering: true }
      return { ...state, entries: next }
    }
    case 'REMOVE_FUNDING': {
      const idx = state.entries.findIndex(e => e.ein === action.ein)
      if (idx === -1) return state
      const entry = { ...state.entries[idx], inFunding: false }
      if (!entry.inFunding && !entry.inVolunteering && !entry.donations?.length && !entry.volunteerHours?.length)
        return { ...state, entries: state.entries.filter(e => e.ein !== action.ein) }
      const next = [...state.entries]; next[idx] = entry
      return { ...state, entries: next }
    }
    case 'REMOVE_VOLUNTEERING': {
      const idx = state.entries.findIndex(e => e.ein === action.ein)
      if (idx === -1) return state
      const entry = { ...state.entries[idx], inVolunteering: false }
      if (!entry.inFunding && !entry.inVolunteering && !entry.donations?.length && !entry.volunteerHours?.length)
        return { ...state, entries: state.entries.filter(e => e.ein !== action.ein) }
      const next = [...state.entries]; next[idx] = entry
      return { ...state, entries: next }
    }
    case 'UPDATE_INTENT': {
      const idx = state.entries.findIndex(e => e.ein === action.ein)
      if (idx === -1) return state
      const next = [...state.entries]
      next[idx] = { ...next[idx], givingIntent: action.intent }
      return { ...state, entries: next }
    }
    case 'LOG_DONATION': {
      const idx = state.entries.findIndex(e => e.ein === action.ein)
      if (idx === -1) return state
      const next = [...state.entries]
      const entry = { ...next[idx] }
      entry.donations = [...(entry.donations || []), action.donation]
      next[idx] = entry
      return { ...state, entries: next }
    }
    case 'LOG_VOLUNTEER_HOURS': {
      const idx = state.entries.findIndex(e => e.ein === action.ein)
      if (idx === -1) return state
      const next = [...state.entries]
      const entry = { ...next[idx] }
      entry.volunteerHours = [...(entry.volunteerHours || []), action.hours]
      next[idx] = entry
      return { ...state, entries: next }
    }
    case 'UPDATE_DONATION_LETTER_STATUS': {
      const idx = state.entries.findIndex(e => e.ein === action.ein)
      if (idx === -1) return state
      const next = [...state.entries]
      const donations = next[idx].donations || []
      const donIdx = donations.findIndex(d => d.id === action.donationId)
      if (donIdx === -1) return state
      const newDonations = [...donations]
      newDonations[donIdx] = { ...newDonations[donIdx], letterStatus: action.status }
      next[idx] = { ...next[idx], donations: newDonations }
      return { ...state, entries: next }
    }
    case 'SET_SYNC_STATUS':
      return { ...state, syncStatus: action.status }
    case 'LOAD_LOCAL': {
      // Only hydrate from localStorage if we have no in-memory entries yet
      if (state.entries.length > 0) return state
      const entries = action.entries.map(e =>
        (e.inFunding === undefined && e.inVolunteering === undefined) ? { ...e, inFunding: true } : e
      )
      return { ...state, entries }
    }
    case 'MERGE_REMOTE': {
      // Union-merge remote entries into local state — remote fills gaps, local wins on conflict
      const localByEin = new Map(state.entries.map(e => [e.ein, e]))
      const merged = [...state.entries]
      for (const remote of action.entries) {
        if (!remote.ein) continue
        const local = localByEin.get(remote.ein)
        if (!local) {
          merged.push({ ...remote, inFunding: remote.inFunding ?? true })
        } else {
          const idx = merged.findIndex(e => e.ein === remote.ein)
          const localDonIds = new Set((local.donations ?? []).map(d => d.id))
          const localVolIds = new Set((local.volunteerHours ?? []).map(v => v.id))
          merged[idx] = {
            ...local,
            inFunding: local.inFunding || remote.inFunding,
            inVolunteering: local.inVolunteering || remote.inVolunteering,
            donations: [
              ...(local.donations ?? []),
              ...(remote.donations ?? []).filter(d => !localDonIds.has(d.id)),
            ],
            volunteerHours: [
              ...(local.volunteerHours ?? []),
              ...(remote.volunteerHours ?? []).filter(v => !localVolIds.has(v.id)),
            ],
          }
        }
      }
      return { ...state, entries: merged }
    }
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
  const tokenRef = useRef<{ token: string; expiresAt: number } | null>(null)
  const [migrationData, setMigrationData] = useState<WalletEntry[] | null>(null)

  // On mount: load from localStorage (device-first — survives page refresh with no auth)
  useEffect(() => {
    try {
      const raw = localStorage.getItem('dw_entries')
      if (raw) {
        const parsed = JSON.parse(raw)
        if (Array.isArray(parsed)) {
          dispatch({ type: 'LOAD_LOCAL', entries: parsed.filter(isValidWalletEntry) })
        }
      }
    } catch { /* ignore */ }
  }, [])

  // Save entries to localStorage on every change (device-first persistence)
  useEffect(() => {
    try {
      if (state.entries.length > 0) {
        localStorage.setItem('dw_entries', JSON.stringify(state.entries))
      }
    } catch { /* ignore */ }
  }, [state.entries])

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

  // SECURITY FIX: On mount, no longer restore raw key from sessionStorage.
  // Use JWT token endpoint instead (see setupNewWallet & unlockWithPassphrase).
  // This prevents XSS from exfiltrating the key material.
  useEffect(() => {
    // Removed raw key restoration. Tokens are issued on-demand by /api/wallet/token.
  }, [])

  // Debounced sync on entries change (only when unlocked)
  useEffect(() => {
    if (!state.encKey || !state.keyHash || !state.salt) return
    if (syncTimerRef.current) clearTimeout(syncTimerRef.current)
    syncTimerRef.current = setTimeout(async () => {
      dispatch({ type: 'SET_SYNC_STATUS', status: 'syncing' })
      let lastError: Error | null = null

      // Exponential backoff retry: up to 3 attempts (400ms, 800ms, 1600ms delays)
      for (let attempt = 0; attempt < 3; attempt++) {
        try {
          const { ciphertext, iv } = await encryptWallet(state.entries, state.encKey!)

          // Request a JWT token if needed
          const now = Date.now()
          if (!tokenRef.current || tokenRef.current.expiresAt < now) {
            const tokenRes = await fetch(`${getApiBase()}/api/wallet/token`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ keyHash: state.keyHash }),
            })
            if (!tokenRes.ok) throw new Error(`token request failed: ${tokenRes.status}`)
            const { token, expiresIn } = await tokenRes.json()
            tokenRef.current = { token, expiresAt: now + expiresIn * 1000 }
          }

          // Sync with JWT token
          const r = await fetch(`${getApiBase()}/api/wallet/sync`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${tokenRef.current.token}`,
            },
            body: JSON.stringify({ ciphertext, iv, salt: state.salt }),
          })

          // If 401, token expired — refresh and retry
          if (r.status === 401) {
            const tokenRes = await fetch(`${getApiBase()}/api/wallet/token`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ keyHash: state.keyHash }),
            })
            if (!tokenRes.ok) throw new Error(`token refresh failed: ${tokenRes.status}`)
            const { token, expiresIn } = await tokenRes.json()
            tokenRef.current = { token, expiresAt: now + expiresIn * 1000 }

            const retryR = await fetch(`${getApiBase()}/api/wallet/sync`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${tokenRef.current.token}`,
              },
              body: JSON.stringify({ ciphertext, iv, salt: state.salt }),
            })
            if (!retryR.ok) throw new Error(`sync failed after token refresh: ${retryR.status}`)
          } else if (!r.ok) {
            throw new Error(`sync failed: ${r.status}`)
          }

          // Success
          dispatch({ type: 'SET_SYNC_STATUS', status: 'idle' })
          return
        } catch (e) {
          lastError = e instanceof Error ? e : new Error(String(e))
          if (attempt < 2) {
            // Exponential backoff: 400ms, 800ms
            await new Promise(resolve => setTimeout(resolve, 400 * Math.pow(2, attempt)))
          }
        }
      }

      // All retries failed
      dispatch({ type: 'SET_SYNC_STATUS', status: 'error' })
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
  const isInFunding = useCallback((ein: string) => state.entries.some(e => e.ein === ein && (e.inFunding ?? (!e.inVolunteering))), [state.entries])
  const isInVolunteering = useCallback((ein: string) => state.entries.some(e => e.ein === ein && e.inVolunteering === true), [state.entries])

  const addToFunding = useCallback((ein: string) => {
    if (!/^\d{9}$/.test(ein)) return
    dispatch({ type: 'ADD_FUNDING', ein })
  }, [])

  const addToVolunteering = useCallback((ein: string) => {
    if (!/^\d{9}$/.test(ein)) return
    dispatch({ type: 'ADD_VOLUNTEERING', ein })
    fetch(`${getApiBase()}/api/volunteer-interest/${ein}`, { method: 'POST' }).catch(() => {})
  }, [])

  const removeFromFunding = useCallback((ein: string) => {
    dispatch({ type: 'REMOVE_FUNDING', ein })
  }, [])

  const removeFromVolunteering = useCallback((ein: string) => {
    dispatch({ type: 'REMOVE_VOLUNTEERING', ein })
    fetch(`${getApiBase()}/api/volunteer-interest/${ein}`, { method: 'DELETE' }).catch(() => {})
  }, [])

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
    // Request initial token
    const tokenRes = await fetch(`${getApiBase()}/api/wallet/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keyHash }),
    })
    if (tokenRes.ok) {
      const { token, expiresIn } = await tokenRes.json()
      tokenRef.current = { token, expiresAt: Date.now() + expiresIn * 1000 }
    }
    dispatch({ type: 'HYDRATE', entries: [], keyHash, salt: saltB64, encKey })
  }, [])

  const unlockWithPassphrase = useCallback(async (passphrase: string) => {
    const saltB64 = localStorage.getItem(LS_SALT)
    const storedKeyHash = localStorage.getItem(LS_KEY_HASH)
    if (!saltB64 || !storedKeyHash) throw new Error('No wallet found on this device')
    const saltBytes = Uint8Array.from(atob(saltB64), c => c.charCodeAt(0))
    const { encKey, keyHash } = await deriveAll(passphrase, saltBytes)
    const r = await fetch(`${getApiBase()}/api/wallet/sync?keyHash=${keyHash}`)
    if (r.status === 401 || r.status === 404) throw new Error('Incorrect passphrase')
    if (!r.ok) throw new Error('Server error')
    const data = await r.json()
    const rawEntries = await decryptWallet(data.ciphertext, data.iv, encKey)
    const entries = rawEntries.filter(isValidWalletEntry)
    // Request initial token on unlock
    const tokenRes = await fetch(`${getApiBase()}/api/wallet/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keyHash }),
    })
    if (tokenRes.ok) {
      const { token, expiresIn } = await tokenRes.json()
      tokenRef.current = { token, expiresAt: Date.now() + expiresIn * 1000 }
    }
    dispatch({ type: 'HYDRATE', entries, keyHash, salt: saltB64, encKey })
  }, [])

  const lockWallet = useCallback(() => {
    tokenRef.current = null
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
    tokenRef.current = null
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

  const logDonation = useCallback((ein: string, amount: number, date: string, notes?: string, helpedDaanaa?: boolean) => {
    const donation: LoggedDonation = {
      id: `don_${uuid()}`,
      amount,
      date,
      notes,
      letterRequested: false,
      helpedDaanaa: helpedDaanaa ?? false,
    }
    dispatch({ type: 'LOG_DONATION', ein, donation })
    // Auto-sync if opted in
    if (helpedDaanaa) {
      syncImpactLog(donation, 'giving', ein).catch(e => console.error('Failed to sync impact log:', e))
    }
  }, [])

  const logVolunteerHours = useCallback((ein: string, hours: number, date: string, notes?: string, helpedDaanaa?: boolean) => {
    const entry: LoggedVolunteerHours = {
      id: `vol_${uuid()}`,
      hours,
      date,
      notes,
      helpedDaanaa: helpedDaanaa ?? false,
    }
    dispatch({ type: 'LOG_VOLUNTEER_HOURS', ein, hours: entry })
    // Auto-sync if opted in
    if (helpedDaanaa) {
      syncImpactLog(entry, 'volunteer', ein).catch(e => console.error('Failed to sync impact log:', e))
    }
  }, [])

  const mergeRemoteEntries = useCallback((entries: WalletEntry[]) => {
    dispatch({ type: 'MERGE_REMOTE', entries })
  }, [])

  const getDonations = useCallback((ein: string) => state.entries.find(e => e.ein === ein)?.donations, [state.entries])

  const getVolunteerHours = useCallback((ein: string) => state.entries.find(e => e.ein === ein)?.volunteerHours, [state.entries])

  const updateDonationLetterStatus = useCallback((ein: string, donationId: string, status: LoggedDonation['letterStatus']) => {
    dispatch({ type: 'UPDATE_DONATION_LETTER_STATUS', ein, donationId, status })
  }, [])

  const archiveDonationHistory = useCallback((ein: string, beforeDate: string) => {
    // Delete donations/volunteer hours before a given date (ISO string).
    // Use case: comply with data retention policies (e.g., keep 7 years only).
    const idx = state.entries.findIndex(e => e.ein === ein)
    if (idx === -1) return
    const next = [...state.entries]
    const entry = { ...next[idx] }
    entry.donations = (entry.donations || []).filter(d => d.date >= beforeDate)
    entry.volunteerHours = (entry.volunteerHours || []).filter(v => v.date >= beforeDate)
    next[idx] = entry
    dispatch({ type: 'HYDRATE', entries: next, keyHash: state.keyHash!, salt: state.salt!, encKey: state.encKey! })
  }, [state.entries, state.keyHash, state.salt, state.encKey])

  const syncImpactLog = useCallback(async (entry: LoggedDonation | LoggedVolunteerHours, type: 'giving' | 'volunteer', ein: string) => {
    try {
      const res = await fetch(`${getApiBase()}/api/impact/log`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ein,
          type,
          amount: type === 'giving' ? (entry as LoggedDonation).amount : null,
          hours: type === 'volunteer' ? (entry as LoggedVolunteerHours).hours : null,
          date: entry.date,
        }),
      })
      if (!res.ok) {
        console.warn(`Impact log sync failed: ${res.status}`)
      }
    } catch (e) {
      console.error('Impact log sync error:', e)
    }
  }, [])

  return (
    <WalletContext.Provider value={{
      entries: state.entries, addEntry, removeEntry,
      addToFunding, addToVolunteering, removeFromFunding, removeFromVolunteering,
      isInFunding, isInVolunteering,
      updateIntent,
      logDonation, logVolunteerHours, getDonations, getVolunteerHours, updateDonationLetterStatus,
      mergeRemoteEntries,
      isInWallet, getIntent, isUnlocked: state.encKey !== null,
      unlockWithPassphrase, setupNewWallet, lockWallet, deleteWallet,
      downloadBackup, syncStatus: state.syncStatus,
      migrationData, applyMigration, dismissMigration,
      archiveDonationHistory,
      syncImpactLog,
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
