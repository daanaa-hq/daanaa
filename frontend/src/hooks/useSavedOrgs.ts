import { useState, useCallback, useMemo } from 'react'

export interface SavedOrgMeta {
  ein: string
  name: string
  city?: string
  state?: string
  ntee1?: string
}

const STORAGE_KEY = 'merit_saved_orgs'

function readStorage(): SavedOrgMeta[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    // Migrate old format: array of EIN strings
    if (parsed.length > 0 && typeof parsed[0] === 'string') {
      return parsed.map((ein: string) => ({ ein, name: ein }))
    }
    return parsed as SavedOrgMeta[]
  } catch { return [] }
}

function writeStorage(orgs: SavedOrgMeta[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(orgs))
}

export function useSavedOrgs() {
  const [saved, setSaved] = useState<SavedOrgMeta[]>(readStorage)

  const savedSet = useMemo(() => new Set(saved.map(o => o.ein)), [saved])

  const toggle = useCallback((ein: string, meta?: Omit<SavedOrgMeta, 'ein'>) => {
    setSaved(prev => {
      const exists = prev.some(o => o.ein === ein)
      const next = exists
        ? prev.filter(o => o.ein !== ein)
        : [...prev, { ein, name: meta?.name || ein, city: meta?.city, state: meta?.state, ntee1: meta?.ntee1 }]
      writeStorage(next)
      return next
    })
  }, [])

  return {
    isSaved: (ein: string) => savedSet.has(ein),
    toggle,
    count: saved.length,
    savedOrgs: saved,
  }
}
