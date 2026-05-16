import { createContext, useContext, useState } from 'react'

export const MAX_COMPARE = 4

export interface CompareItem {
  ein: string
  name: string
  ntee1?: string | null
  city?: string | null
  state?: string | null
}

interface CompareContextValue {
  items: CompareItem[]
  addItem: (item: CompareItem) => void
  removeItem: (ein: string) => void
  clearItems: () => void
  isInCompare: (ein: string) => boolean
  canAdd: boolean
}

const CompareContext = createContext<CompareContextValue | null>(null)

export function CompareProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<CompareItem[]>([])

  const addItem = (item: CompareItem) => {
    setItems(prev => {
      if (prev.length >= MAX_COMPARE || prev.some(i => i.ein === item.ein)) return prev
      return [...prev, item]
    })
  }

  const removeItem = (ein: string) => setItems(prev => prev.filter(i => i.ein !== ein))
  const clearItems = () => setItems([])
  const isInCompare = (ein: string) => items.some(i => i.ein === ein)

  return (
    <CompareContext.Provider value={{ items, addItem, removeItem, clearItems, isInCompare, canAdd: items.length < MAX_COMPARE }}>
      {children}
    </CompareContext.Provider>
  )
}

export function useCompare() {
  const ctx = useContext(CompareContext)
  if (!ctx) throw new Error('useCompare must be used within CompareProvider')
  return ctx
}
