import { useState, useCallback, useMemo } from 'react'

export interface SavedOrgMeta {
  ein: string
  name: string
  city?: string
  state?: string
  ntee1?: string
}

const STORAGE_KEY = 'daanaa_favorites'
const LEGACY_KEY  = 'merit_saved_orgs'

function readStorage(): SavedOrgMeta[] {
  try {
    // Migrate from old key on first read
    const legacy = localStorage.getItem(LEGACY_KEY)
    if (legacy) {
      localStorage.setItem(STORAGE_KEY, legacy)
      localStorage.removeItem(LEGACY_KEY)
    }
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
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

  // Non-toggle add — used for auto-favoriting on give. Silently skips if already saved.
  const addFavorite = useCallback((ein: string, meta?: Omit<SavedOrgMeta, 'ein'>) => {
    setSaved(prev => {
      if (prev.some(o => o.ein === ein)) return prev
      const next = [...prev, { ein, name: meta?.name || ein, city: meta?.city, state: meta?.state, ntee1: meta?.ntee1 }]
      writeStorage(next)
      return next
    })
  }, [])

  return {
    isSaved: (ein: string) => savedSet.has(ein),
    toggle,
    addFavorite,
    count: saved.length,
    savedOrgs: saved,
  }
}
