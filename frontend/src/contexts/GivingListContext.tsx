import React, { createContext, useContext, useState, useCallback } from 'react'
import type { TierName } from '../components/TrustBadge'

// Map old TrustTier names (pre-Week-1) to new TierName — runs once at localStorage load
const TIER_COMPAT: Record<string, TierName> = {
  Exemplary:   'Beacon',
  Transparent: 'Torch',
  Accountable: 'Torch',
  Verified:    'Candle',
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
  // Civic action type — 'give_money' now; 'give_time' reserved for volunteering (Phase 3)
  actionType?: 'give_money' | 'give_time'
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
}

const KEY = 'merit_giving_list'

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
const GivingListContext = createContext<GivingListContextValue | null>(null)

export function GivingListProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<GivingListItem[]>(load)

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

  const total = items.reduce((s, i) => s + (i.amount || 0), 0)

  return (
    <GivingListContext.Provider value={{
      items, addItem, removeItem, updateAmount, updateLetterInfo, markGiven,
      clearList, isInList, total, count: items.length,
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
