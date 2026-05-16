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
  letterRequested?: boolean
  donorName?: string
  donorEmail?: string
}

interface GivingListContextValue {
  items: GivingListItem[]
  addItem: (item: Omit<GivingListItem, 'addedAt'>) => void
  removeItem: (ein: string) => void
  updateAmount: (ein: string, amount: number) => void
  updateLetterInfo: (ein: string, info: { letterRequested: boolean; donorName?: string; donorEmail?: string }) => void
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
    }))
  } catch { return [] }
}
function persist(items: GivingListItem[]) {
  localStorage.setItem(KEY, JSON.stringify(items))
}

const GivingListContext = createContext<GivingListContextValue | null>(null)

export function GivingListProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<GivingListItem[]>(load)

  const addItem = useCallback((item: Omit<GivingListItem, 'addedAt'>) => {
    setItems(prev => {
      if (prev.some(i => i.ein === item.ein)) return prev
      const next = [{ ...item, addedAt: new Date().toISOString() }, ...prev]
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

  const clearList = useCallback(() => {
    setItems([])
    localStorage.removeItem(KEY)
  }, [])

  const isInList = useCallback((ein: string) => items.some(i => i.ein === ein), [items])

  const total = items.reduce((s, i) => s + (i.amount || 0), 0)

  return (
    <GivingListContext.Provider value={{
      items, addItem, removeItem, updateAmount, updateLetterInfo, clearList, isInList, total, count: items.length,
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
