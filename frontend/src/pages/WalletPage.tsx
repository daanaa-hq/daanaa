import React, { useState, useMemo, useCallback, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { useWallet } from '../contexts/WalletContext'
import WalletCard from '../components/WalletCard'
import EditIntentModal from '../components/EditIntentModal'
import PassphraseModal from '../components/PassphraseModal'
import LogFunding from '../components/LogFunding'
import type { ApiOrganization } from '../data/api'
import { API_BASE } from '../lib/platform'
import {
  validateSearchTerm,
  validateFilterValue,
  validateSortValue,
  logValidationError,
} from '../utils/walletValidation'

const NUDGE_KEY = 'daanaa_wallet_nudge_ts'
const NUDGE_THROTTLE_MS = 7 * 24 * 60 * 60 * 1000

type SortBy = 'recent' | 'name' | 'health'
type FilterIntent = 'all' | 'giving' | 'volunteer'
type FilterHealth = 'all' | 'HEALTHY' | 'STABLE' | 'CAUTION'

interface FilterState {
  intent: FilterIntent
  health: FilterHealth
}

export default function WalletPage() {
  usePageMeta(
    'Your Giving Wallet | Daanaa',
    "Save nonprofits you're interested in and track your giving intentions."
  )

  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const {
    entries,
    removeEntry,
    updateIntent,
    isUnlocked,
    syncStatus,
    downloadBackup,
    setupNewWallet,
    unlockWithPassphrase,
    migrationData,
    applyMigration,
    dismissMigration,
  } = useWallet()

  // Org data hydration — batch-fetch live org data for each entry
  const [orgDataMap, setOrgDataMap] = useState<Map<string, ApiOrganization>>(new Map())
  const [hydrating, setHydrating] = useState(false)

  useEffect(() => {
    if (entries.length === 0) { setOrgDataMap(new Map()); return }
    setHydrating(true)
    const eins = entries.map(e => e.ein)
    Promise.all(
      eins.map(ein =>
        fetch(`${API_BASE}/api/organizations/${ein}`)
          .then(r => r.ok ? r.json() : null)
          .catch(() => null)
      )
    ).then(results => {
      const map = new Map<string, ApiOrganization>()
      eins.forEach((ein, i) => { if (results[i]) map.set(ein, results[i] as ApiOrganization) })
      setOrgDataMap(map)
      setHydrating(false)
    })
  }, [entries])

  // Passphrase gate state
  const [showModal, setShowModal] = useState<'setup' | 'restore' | null>(null)
  const hasExistingWallet = !!localStorage.getItem('dw_kh')

  // Filter / sort state
  const [sortBy, setSortBy] = useState<SortBy>('recent')
  const [filterState, setFilterState] = useState<FilterState>({ intent: 'all', health: 'all' })
  const [searchTerm, setSearchTerm] = useState('')
  const [searchError, setSearchError] = useState<string | null>(null)
  const [editingEin, setEditingEin] = useState<string | null>(null)
  const [showNudge, setShowNudge] = useState(false)

  const hasOrgsWithoutIntent = entries.some(o => !o.givingIntent)

  // ?intent=EIN — auto-open intent modal for a specific org (e.g. from post-save prompt)
  useEffect(() => {
    const targetEin = searchParams.get('intent')
    if (!targetEin) return
    const inWallet = entries.some(o => o.ein === targetEin)
    if (inWallet) {
      setEditingEin(targetEin)
      setSearchParams({}, { replace: true })
    }
  }, [searchParams, entries, setSearchParams])

  useEffect(() => {
    if (!hasOrgsWithoutIntent || entries.length === 0) return
    const last = localStorage.getItem(NUDGE_KEY)
    if (!last || Date.now() - Number(last) > NUDGE_THROTTLE_MS) {
      setShowNudge(true)
    }
  }, [hasOrgsWithoutIntent, entries.length])

  const dismissNudge = useCallback(() => {
    setShowNudge(false)
    localStorage.setItem(NUDGE_KEY, String(Date.now()))
  }, [])

  const filteredEntries = useMemo(() => {
    let result = entries

    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      result = result.filter(entry => {
        const org = orgDataMap.get(entry.ein)
        if (!org) return false
        const name = (org.organization_name ?? '').toLowerCase()
        const location = [org.CITY, org.STATE].filter(Boolean).join(', ').toLowerCase()
        const cause = (org.cause_tags ?? []).join(' ').toLowerCase()
        const mission = (org.mission ?? '').toLowerCase()
        return name.includes(term) || location.includes(term) || cause.includes(term) || mission.includes(term)
      })
    }

    if (filterState.intent !== 'all') {
      result = result.filter(entry => entry.givingIntent?.type === filterState.intent)
    }

    if (filterState.health !== 'all') {
      result = result.filter(entry => {
        const org = orgDataMap.get(entry.ein)
        return org?.v5_context?.score.health_signal === filterState.health
      })
    }

    const sorted = [...result]
    switch (sortBy) {
      case 'recent':
        sorted.sort((a, b) => b.bookmarkedAt - a.bookmarkedAt)
        break
      case 'name':
        sorted.sort((a, b) => {
          const nameA = orgDataMap.get(a.ein)?.organization_name ?? ''
          const nameB = orgDataMap.get(b.ein)?.organization_name ?? ''
          return nameA.localeCompare(nameB)
        })
        break
      case 'health': {
        const healthOrder: Record<string, number> = { HEALTHY: 0, STABLE: 1, CAUTION: 2 }
        sorted.sort((a, b) => {
          const ha = orgDataMap.get(a.ein)?.v5_context?.score.health_signal ?? 'STABLE'
          const hb = orgDataMap.get(b.ein)?.v5_context?.score.health_signal ?? 'STABLE'
          return (healthOrder[ha] ?? 1) - (healthOrder[hb] ?? 1)
        })
        break
      }
    }

    return sorted
  }, [entries, orgDataMap, searchTerm, filterState, sortBy])

  const handleSort = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value
    if (validateSortValue(value)) {
      setSortBy(value as SortBy)
    } else {
      logValidationError('handleSort', new Error('Invalid sort value'))
    }
  }, [])

  const handleIntentFilter = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value
    if (validateFilterValue('intent', value)) {
      setFilterState(prev => ({ ...prev, intent: value as FilterIntent }))
    } else {
      logValidationError('handleIntentFilter', new Error('Invalid intent filter'))
    }
  }, [])

  const handleHealthFilter = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value
    if (validateFilterValue('health', value)) {
      setFilterState(prev => ({ ...prev, health: value as FilterHealth }))
    } else {
      logValidationError('handleHealthFilter', new Error('Invalid health filter'))
    }
  }, [])

  const handleClearFilters = useCallback(() => {
    setFilterState({ intent: 'all', health: 'all' })
    setSearchTerm('')
    setSearchError(null)
  }, [])

  const handleSearchChange = useCallback((value: string) => {
    setSearchError(null)
    if (value === '') {
      setSearchTerm('')
      return
    }
    try {
      const validated = validateSearchTerm(value)
      setSearchTerm(validated)
    } catch (err) {
      setSearchError((err as Error).message)
    }
  }, [])

  const handleRemove = useCallback((ein: string) => {
    removeEntry(ein)
  }, [removeEntry])

  const handleEdit = useCallback((ein: string) => {
    setEditingEin(ein)
  }, [])

  const handleEditClose = useCallback(() => {
    setEditingEin(null)
  }, [])

  const hasActiveFilters =
    filterState.intent !== 'all' || filterState.health !== 'all' || searchTerm !== ''

  // ─── Passphrase gate ────────────────────────────────────────────────────────
  if (!isUnlocked) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-warm-cream">
        {showModal ? (
          <PassphraseModal
            mode={showModal}
            onSetup={async (passphrase) => {
              await setupNewWallet(passphrase)
              if (migrationData) applyMigration()
              setShowModal(null)
            }}
            onRestore={async (passphrase) => {
              await unlockWithPassphrase(passphrase)
              setShowModal(null)
            }}
            onClose={() => setShowModal(null)}
          />
        ) : (
          <div className="text-center max-w-sm">
            <h1 className="font-body text-2xl font-semibold text-deep-navy mb-3">Your Giving Wallet</h1>
            <p className="font-body text-sm text-cool-grey mb-6">
              {hasExistingWallet
                ? 'Enter your passphrase to access your saved organizations.'
                : 'Set a passphrase to start saving organizations and sync across devices.'}
            </p>
            {migrationData && (
              <div className="bg-soft-cream rounded-xl p-4 mb-4 text-left">
                <p className="font-body text-sm text-cool-grey">
                  You have {migrationData.length} saved org{migrationData.length !== 1 ? 's' : ''} from an earlier Daanaa version.
                  Set a passphrase to keep them, or start fresh.
                </p>
                <button
                  onClick={dismissMigration}
                  className="mt-2 font-body text-xs text-cool-grey underline"
                >
                  Start fresh
                </button>
              </div>
            )}
            <button
              onClick={() => setShowModal(hasExistingWallet ? 'restore' : 'setup')}
              className="w-full py-3 rounded-full font-body font-semibold bg-soft-gold text-deep-navy hover:bg-bright-gold transition-colors"
            >
              {hasExistingWallet ? 'Enter passphrase' : 'Set up wallet'}
            </button>
          </div>
        )}
      </div>
    )
  }

  // ─── Empty state ────────────────────────────────────────────────────────────
  if (entries.length === 0) {
    return (
      <div className="bg-warm-cream min-h-[100dvh] pt-[72px]">
        <div className="max-w-[720px] mx-auto px-6 py-16">
          <h1 className="font-display italic text-deep-navy text-[32px] mb-2">Your Giving Wallet</h1>
          <p className="font-body text-cool-grey mb-10">Nonprofits you want to support, all in one place.</p>

          <div className="bg-white rounded-2xl border border-light-grey p-12 text-center">
            <div className="w-14 h-14 rounded-full bg-soft-gold/10 flex items-center justify-center mx-auto mb-5">
              <svg className="w-7 h-7 text-soft-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/>
              </svg>
            </div>
            <h2 className="font-display italic text-deep-navy text-[22px] mb-2">Your wallet is empty</h2>
            <p className="font-body text-[15px] text-cool-grey mb-8 max-w-sm mx-auto">
              Browse the directory and save nonprofits you care about. You can track your giving intent for each one.
            </p>
            <button
              onClick={() => navigate('/directory')}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-soft-gold text-deep-navy font-body text-[14px] font-semibold hover:bg-bright-gold transition-colors"
            >
              Browse nonprofits
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ─── Main wallet view ────────────────────────────────────────────────────────
  return (
    <div className="bg-warm-cream min-h-[100dvh] pt-[72px]">
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12 py-10">

        {/* Header */}
        <div className="flex items-start justify-between mb-8 flex-wrap gap-4">
          <div>
            <h1 className="font-display italic text-deep-navy text-[32px] mb-1">Your Giving Wallet</h1>
            <p className="font-body text-[14px] text-cool-grey">
              {entries.length} organization{entries.length !== 1 ? 's' : ''} saved
            </p>
            <p className="font-body text-[13px] text-cool-grey/70 mt-2 max-w-md">
              Track nonprofits you care about and your giving plans. Encrypted and synced to your passphrase.
            </p>
          </div>
          <div className="flex items-center gap-3">
            {syncStatus === 'syncing' && (
              <span className="font-body text-xs text-cool-grey">Saving…</span>
            )}
            {syncStatus === 'error' && (
              <span className="font-body text-xs text-red-500">Sync error — will retry</span>
            )}
            <button
              onClick={downloadBackup}
              className="font-body text-xs text-soft-gold hover:text-bright-gold transition-colors"
            >
              Download backup
            </button>
            <button
              onClick={() => navigate('/directory')}
              className="px-4 py-2 rounded-xl bg-soft-gold text-deep-navy font-body text-[13px] font-semibold hover:bg-bright-gold transition-colors whitespace-nowrap"
            >
              + Add more
            </button>
          </div>
        </div>

        {/* Giving Intent Guide — only shown when orgs without a plan exist */}
        {hasOrgsWithoutIntent && (
          <div className="bg-soft-gold/8 border border-soft-gold/20 rounded-2xl p-5 mb-8">
            <p className="font-body text-[13px] text-cool-grey mb-3 font-medium">What each giving type means:</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p className="font-body text-[12px] font-semibold text-deep-navy">Giving</p>
                <p className="font-body text-[12px] text-cool-grey/80 mt-1">Organizations you want to support financially</p>
              </div>
              <div>
                <p className="font-body text-[12px] font-semibold text-deep-navy">Volunteering</p>
                <p className="font-body text-[12px] text-cool-grey/80 mt-1">Organizations you want to give your time to</p>
              </div>
            </div>
          </div>
        )}

        {/* Welcome-back nudge */}
        {showNudge && (
          <div className="flex items-center justify-between gap-4 bg-soft-gold/10 border border-soft-gold/25 rounded-2xl px-5 py-4 mb-6">
            <div className="flex items-center gap-3 min-w-0">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0">
                <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/>
                <path d="M12 8v4M12 16h.01"/>
              </svg>
              <p className="font-body text-[13px] text-deep-navy">
                You have saved nonprofits without a plan yet.{' '}
                <button
                  onClick={() => {
                    dismissNudge()
                    const first = entries.find(o => !o.givingIntent)
                    if (first) setEditingEin(first.ein)
                  }}
                  className="text-soft-gold hover:text-bright-gold font-semibold underline"
                >
                  Add your giving plan
                </button>
              </p>
            </div>
            <button onClick={dismissNudge} aria-label="Dismiss" className="shrink-0 p-1 text-cool-grey hover:text-deep-navy transition-colors">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {/* Filters — only shown when wallet is large enough to benefit from filtering */}
        {entries.length >= 5 && (
          <div className="bg-white rounded-2xl border border-light-grey p-5 mb-8">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
              <div>
                <label className="font-body text-[11px] font-semibold text-cool-grey uppercase tracking-wide block mb-1">Sort</label>
                <select
                  value={sortBy}
                  onChange={handleSort}
                  aria-label="Sort by"
                  className="w-full px-3 py-2 border border-light-grey rounded-xl font-body text-[13px] text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold/40 bg-white"
                >
                  <option value="recent">Recently added</option>
                  <option value="name">Name (A–Z)</option>
                  <option value="health">Financial health</option>
                </select>
              </div>

              <div>
                <label className="font-body text-[11px] font-semibold text-cool-grey uppercase tracking-wide block mb-1">Intent</label>
                <select
                  value={filterState.intent}
                  onChange={handleIntentFilter}
                  aria-label="Filter by intent"
                  className="w-full px-3 py-2 border border-light-grey rounded-xl font-body text-[13px] text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold/40 bg-white"
                >
                  <option value="all">All intents</option>
                  <option value="giving">Giving</option>
                  <option value="volunteer">Volunteering</option>
                </select>
              </div>

              <div>
                <label className="font-body text-[11px] font-semibold text-cool-grey uppercase tracking-wide block mb-1">Health</label>
                <select
                  value={filterState.health}
                  onChange={handleHealthFilter}
                  aria-label="Filter by health"
                  className="w-full px-3 py-2 border border-light-grey rounded-xl font-body text-[13px] text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold/40 bg-white"
                >
                  <option value="all">All</option>
                  <option value="HEALTHY">Financially healthy</option>
                  <option value="STABLE">Financially stable</option>
                  <option value="CAUTION">Needs support</option>
                </select>
              </div>

              <div className="flex items-end">
                <button
                  onClick={handleClearFilters}
                  disabled={!hasActiveFilters}
                  className="w-full px-3 py-2 rounded-xl border border-light-grey font-body text-[13px] text-cool-grey hover:border-soft-gold/40 hover:text-deep-navy disabled:opacity-40 disabled:cursor-default transition-colors"
                >
                  Clear filters
                </button>
              </div>
            </div>

            <input
              type="text"
              placeholder="Search by name, location, or cause..."
              value={searchTerm}
              onChange={e => handleSearchChange(e.target.value)}
              className="w-full px-4 py-2.5 border border-light-grey rounded-xl font-body text-[13px] text-deep-navy placeholder:text-cool-grey/60 focus:outline-none focus:ring-2 focus:ring-soft-gold/40"
              aria-invalid={!!searchError}
            />
            {searchError && (
              <p className="font-body text-[12px] text-red-600 mt-1" role="alert">{searchError}</p>
            )}
          </div>
        )}

        {/* No results message */}
        {filteredEntries.length === 0 && entries.length > 0 && (
          <div className="bg-white border border-light-grey rounded-2xl p-6 mb-6 text-center">
            <p className="font-body text-[14px] text-cool-grey">
              No organizations match your filters.{' '}
              <button onClick={handleClearFilters} className="text-soft-gold hover:text-bright-gold underline">
                Clear filters
              </button>
            </p>
          </div>
        )}

        {/* Donation logging — track giving for tax purposes */}
        {entries.length > 0 && (
          <div className="mb-8">
            <LogFunding />
          </div>
        )}

        {/* Cards */}
        <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 ${hydrating ? 'opacity-60' : ''}`}>
          {filteredEntries.map(entry => (
            <WalletCard
              key={entry.ein}
              entry={entry}
              orgData={orgDataMap.get(entry.ein) ?? null}
              onRemove={handleRemove}
              onEdit={handleEdit}
            />
          ))}
        </div>
      </div>

      {editingEin && (() => {
        const entry = entries.find(o => o.ein === editingEin)
        if (!entry) return null
        const org = orgDataMap.get(editingEin)
        if (!org) return null
        // EditIntentModal expects a WalletOrg-shaped object; build a compatible shim
        const orgShim = {
          ein: entry.ein,
          bookmarkedAt: entry.bookmarkedAt,
          givingIntent: entry.givingIntent,
          name: org.organization_name ?? '',
          location: [org.CITY, org.STATE].filter(Boolean).join(', '),
          cause: org.cause_tags ?? [],
          mission: org.mission ?? '',
          merit_health_signal_v5: org.v5_context?.score.health_signal ?? 'STABLE',
        }
        return (
          <EditIntentModal
            org={orgShim as Parameters<typeof EditIntentModal>[0]['org']}
            isOpen={!!editingEin}
            onClose={handleEditClose}
          />
        )
      })()}
    </div>
  )
}
