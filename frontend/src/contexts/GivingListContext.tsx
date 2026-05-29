import React, { createContext, useContext, useState, useCallback } from 'react'
import type { TierName } from '../components/TrustBadge'

// Map old TrustTier names (pre-Week-1) to new TierName — runs once at localStorage load
const TIER_COMPAT: Record<string, TierName> = {
  Exemplary:   'Beacon',
  Transparent: 'Lantern',
  Accountable: 'Flame',
  Verified:    'Ember',
  Listed:      'Spark',
}

// 'intent' = saved / clicked to give but not confirmed.
// 'given'  = donor confirmed they actually gave (the tax-relevant records).
export type GiveStatus = 'intent' | 'given'

export interface GivingListItem {
  ein: string
  orgName: string
  city?: string
  state?: string
  ntee1?: string
  amount: number
  trustTier: TierName
  trustSummary: string
  addedAt: string
  status: GiveStatus
  gaveAt?: string
  letterRequested?: boolean
  donorName?: string
  donorEmail?: string
  donateUrl?: string
}

// Set when the donor clicks an external give CTA; the app asks "did you give?"
// when they return (LinkedIn-jobs pattern).
export interface PendingGive {
  ein: string
  orgName: string
  at: string  // ISO — used to ignore an instant tab-switch-back
}

interface GivingListContextValue {
  items: GivingListItem[]
  addItem: (item: Omit<GivingListItem, 'addedAt' | 'status'> & { status?: GiveStatus }) => void
  removeItem: (ein: string) => void
  updateAmount: (ein: string, amount: number) => void
  updateLetterInfo: (ein: string, info: { letterRequested: boolean; donorName?: string; donorEmail?: string }) => void
  markGiven: (ein: string) => void
  clearList: () => void
  isInList: (ein: string) => boolean
  total: number
  count: number
  // Give-confirmation flow
  pendingGive: PendingGive | null
  markPending: (item: Omit<GivingListItem, 'addedAt' | 'status'>) => void
  confirmGiven: () => void
  dismissPending: () => void
}

const KEY = 'merit_giving_list'
const PENDING_KEY = 'merit_pending_give'

function load(): GivingListItem[] {
  try {
    const raw: GivingListItem[] = JSON.parse(localStorage.getItem(KEY) || '[]')
    return raw.map(item => ({
      ...item,
      trustTier: TIER_COMPAT[item.trustTier as string] ?? item.trustTier,
      status: (item as GivingListItem).status ?? 'intent',  // back-compat
    }))
  } catch { return [] }
}
function persist(items: GivingListItem[]) {
  localStorage.setItem(KEY, JSON.stringify(items))
}
function loadPending(): PendingGive | null {
  try {
    const raw = localStorage.getItem(PENDING_KEY)
    return raw ? JSON.parse(raw) as PendingGive : null
  } catch { return null }
}

const GivingListContext = createContext<GivingListContextValue | null>(null)

export function GivingListProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<GivingListItem[]>(load)
  const [pendingGive, setPendingGive] = useState<PendingGive | null>(loadPending)

  const addItem = useCallback((item: Omit<GivingListItem, 'addedAt' | 'status'> & { status?: GiveStatus }) => {
    setItems(prev => {
      if (prev.some(i => i.ein === item.ein)) return prev
      const next = [{ ...item, status: item.status ?? 'intent', addedAt: new Date().toISOString() }, ...prev]
      persist(next)
      return next
    })
  }, [])

  const removeItem = useCallback((ein: string) => {
    setItems(prev => { const next = prev.filter(i => i.ein !== ein); persist(next); return next })
  }, [])

  const updateAmount = useCallback((ein: string, amount: number) => {
    setItems(prev => {
      const next = prev.map(i => i.ein === ein ? { ...i, amount } : i)
      persist(next)
      return next
    })
  }, [])

  const updateLetterInfo = useCallback((ein: string, info: {
    letterRequested: boolean
    donorName?: string
    donorEmail?: string
  }) => {
    setItems(prev => {
      const next = prev.map(i => i.ein === ein
        ? { ...i, letterRequested: info.letterRequested, donorName: info.donorName, donorEmail: info.donorEmail }
        : i
      )
      persist(next)
      return next
    })
  }, [])

  const markGiven = useCallback((ein: string) => {
    setItems(prev => {
      const next = prev.map(i => i.ein === ein
        ? { ...i, status: 'given' as GiveStatus, gaveAt: i.gaveAt ?? new Date().toISOString() }
        : i
      )
      persist(next)
      return next
    })
  }, [])

  const clearList = useCallback(() => {
    setItems([])
    localStorage.removeItem(KEY)
  }, [])

  const isInList = useCallback((ein: string) => items.some(i => i.ein === ein), [items])

  // --- Give-confirmation flow (LinkedIn-jobs style) ---

  const markPending = useCallback((item: Omit<GivingListItem, 'addedAt' | 'status'>) => {
    // Track the click as an 'intent' item if not already saved...
    setItems(prev => {
      if (prev.some(i => i.ein === item.ein)) return prev
      const next = [{ ...item, status: 'intent' as GiveStatus, addedAt: new Date().toISOString() }, ...prev]
      persist(next)
      return next
    })
    // ...and remember to ask "did you give?" when they come back.
    const p: PendingGive = { ein: item.ein, orgName: item.orgName, at: new Date().toISOString() }
    localStorage.setItem(PENDING_KEY, JSON.stringify(p))
    setPendingGive(p)
  }, [])

  const confirmGiven = useCallback(() => {
    setPendingGive(prev => {
      if (prev) {
        setItems(items2 => {
          const next = items2.map(i => i.ein === prev.ein
            ? { ...i, status: 'given' as GiveStatus, gaveAt: i.gaveAt ?? new Date().toISOString() }
            : i
          )
          persist(next)
          return next
        })
      }
      localStorage.removeItem(PENDING_KEY)
      return null
    })
  }, [])

  const dismissPending = useCallback(() => {
    localStorage.removeItem(PENDING_KEY)
    setPendingGive(null)
  }, [])

  const total = items.reduce((s, i) => s + (i.amount || 0), 0)

  return (
    <GivingListContext.Provider value={{
      items, addItem, removeItem, updateAmount, updateLetterInfo, markGiven,
      clearList, isInList, total, count: items.length,
      pendingGive, markPending, confirmGiven, dismissPending,
    }}>
      {children}
    </GivingListContext.Provider>
  )
}

export function useGivingListContext(): GivingListContextValue {
  const ctx = useContext(GivingListContext)
  if (!ctx) throw new Error('useGivingListContext must be used within GivingListProvider')
  return ctx
}
