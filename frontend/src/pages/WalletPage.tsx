import React, { useState, useMemo, useCallback, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { useWallet } from '../contexts/WalletContext'
import { useAuth } from '../contexts/AuthContext'
import WalletCard from '../components/WalletCard'
import EditIntentModal from '../components/EditIntentModal'
import {
  validateSearchTerm,
  validateFilterValue,
  validateSortValue,
  logValidationError,
} from '../utils/walletValidation'

const NUDGE_KEY = 'daanaa_wallet_nudge_ts'
const NUDGE_THROTTLE_MS = 7 * 24 * 60 * 60 * 1000
const API_BASE = import.meta.env.VITE_API_URL || ''
const STALE_CHECK_MAX = 10

type SortBy = 'recent' | 'name' | 'health'
type FilterIntent = 'all' | 'giving' | 'volunteer' | 'board'
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
  const { user, signInWithGoogle, getIdToken } = useAuth()
  const { wallet, removeOrg, updateIntent, storageError, corruptionDetected, syncToServer } = useWallet()

  const [sortBy, setSortBy] = useState<SortBy>('recent')
  const [syncing, setSyncing] = useState(false)
  const [staleEins, setStaleEins] = useState<Set<string>>(new Set())
  const [filterState, setFilterState] = useState<FilterState>({ intent: 'all', health: 'all' })
  const [searchTerm, setSearchTerm] = useState('')
  const [searchError, setSearchError] = useState<string | null>(null)
  const [editingEin, setEditingEin] = useState<string | null>(null)
  const [showNudge, setShowNudge] = useState(false)

  const hasOrgsWithoutIntent = wallet.orgs.some(o => !o.givingIntent)

  // ?intent=EIN — auto-open intent modal for a specific org (e.g. from post-save prompt)
  useEffect(() => {
    const targetEin = searchParams.get('intent')
    if (!targetEin) return
    const inWallet = wallet.orgs.some(o => o.ein === targetEin)
    if (inWallet) {
      setEditingEin(targetEin)
      setSearchParams({}, { replace: true })
    }
  }, [searchParams, wallet.orgs, setSearchParams])

  useEffect(() => {
    if (!hasOrgsWithoutIntent || wallet.orgs.length === 0) return
    const last = localStorage.getItem(NUDGE_KEY)
    if (!last || Date.now() - Number(last) > NUDGE_THROTTLE_MS) {
      setShowNudge(true)
    }
  }, [hasOrgsWithoutIntent, wallet.orgs.length])

  // Stale org check: fire-and-forget, runs once when wallet.orgs changes.
  // Checks up to STALE_CHECK_MAX EINs; any 404 is added to staleEins.
  useEffect(() => {
    if (wallet.orgs.length === 0) return
    const einsToCheck = wallet.orgs.slice(0, STALE_CHECK_MAX).map(o => o.ein)
    let cancelled = false
    Promise.all(
      einsToCheck.map(ein =>
        fetch(`${API_BASE}/api/organizations/${ein}`, { method: 'HEAD' })
          .then(res => (res.status === 404 ? ein : null))
          .catch(() => null)
      )
    ).then(results => {
      if (cancelled) return
      const found = results.filter((ein): ein is string => ein !== null)
      if (found.length > 0) {
        setStaleEins(new Set(found))
      }
    })
    return () => { cancelled = true }
  }, [wallet.orgs])

  const dismissNudge = useCallback(() => {
    setShowNudge(false)
    localStorage.setItem(NUDGE_KEY, String(Date.now()))
  }, [])

  const filteredOrgs = useMemo(() => {
    let result = wallet.orgs

    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      result = result.filter(
        org =>
          org.name.toLowerCase().includes(term) ||
          org.location.toLowerCase().includes(term) ||
          org.cause.some(c => c.toLowerCase().includes(term)) ||
          org.mission.toLowerCase().includes(term)
      )
    }

    if (filterState.intent !== 'all') {
      result = result.filter(org => org.givingIntent?.type === filterState.intent)
    }

    if (filterState.health !== 'all') {
      result = result.filter(org => org.merit_health_signal_v5 === filterState.health)
    }

    const sorted = [...result]
    switch (sortBy) {
      case 'recent':
        sorted.sort((a, b) => b.bookmarkedAt - a.bookmarkedAt)
        break
      case 'name':
        sorted.sort((a, b) => a.name.localeCompare(b.name))
        break
      case 'health': {
        const healthOrder = { HEALTHY: 0, STABLE: 1, CAUTION: 2 }
        sorted.sort((a, b) => healthOrder[a.merit_health_signal_v5] - healthOrder[b.merit_health_signal_v5])
        break
      }
    }

    return sorted
  }, [wallet.orgs, searchTerm, filterState, sortBy])

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
    removeOrg(ein)
  }, [removeOrg])

  const handleEdit = useCallback((ein: string) => {
    setEditingEin(ein)
  }, [])

  const handleEditClose = useCallback(() => {
    setEditingEin(null)
  }, [])

  const hasActiveFilters =
    filterState.intent !== 'all' || filterState.health !== 'all' || searchTerm !== ''

  const handleSaveToCloud = useCallback(async () => {
    if (!user) {
      signInWithGoogle()
      return
    }
    setSyncing(true)
    try {
      const token = await getIdToken()
      if (user.email && token) {
        await syncToServer(user.email, token)
      }
    } catch (err) {
      console.error('Sync failed:', err)
    } finally {
      setSyncing(false)
    }
  }, [user, signInWithGoogle, getIdToken, syncToServer])

  // Empty state
  if (wallet.orgs.length === 0) {
    return (
      <div className="bg-warm-cream min-h-[100dvh] pt-[72px]">
        <div className="max-w-[720px] mx-auto px-6 py-16">
          <h1 className="font-display italic text-deep-navy text-[32px] mb-2">Your Giving Wallet</h1>
          <p className="font-body text-cool-grey mb-10">Nonprofits you want to support, all in one place.</p>

          {corruptionDetected && (
            <div className="flex items-center gap-3 bg-amber-50 border border-amber-200 rounded-2xl px-5 py-4 mb-6">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#D97706" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
              </svg>
              <p className="font-body text-[13px] text-deep-navy">
                Your wallet data was unreadable and has been cleared. Browse the directory to save your nonprofits again.
              </p>
            </div>
          )}

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

  return (
    <div className="bg-warm-cream min-h-[100dvh] pt-[72px]">
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12 py-10">

        {/* Header */}
        <div className="flex items-start justify-between mb-8 flex-wrap gap-4">
          <div>
            <h1 className="font-display italic text-deep-navy text-[32px] mb-1">Your Giving Wallet</h1>
            <p className="font-body text-[14px] text-cool-grey">
              {wallet.orgs.length} organization{wallet.orgs.length !== 1 ? 's' : ''} saved
            </p>
            <p className="font-body text-[13px] text-cool-grey/70 mt-2 max-w-md">
              Track nonprofits you care about and your giving plans. All saved locally on this device.
              {user && ' Synced to your account.'}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate('/directory')}
              className="px-4 py-2 rounded-xl bg-soft-gold text-deep-navy font-body text-[13px] font-semibold hover:bg-bright-gold transition-colors whitespace-nowrap"
            >
              + Add more
            </button>
            <button
              onClick={handleSaveToCloud}
              disabled={syncing}
              title={user ? 'Sync your wallet to cloud' : 'Sign in to sync across devices'}
              className={`px-4 py-2 rounded-xl font-body text-[13px] font-semibold whitespace-nowrap transition-colors ${
                user
                  ? 'bg-deep-navy/5 text-deep-navy border border-deep-navy/20 hover:bg-deep-navy/10'
                  : 'bg-soft-gold/20 text-soft-gold border border-soft-gold/30 hover:bg-soft-gold/30'
              } disabled:opacity-50`}
            >
              {syncing ? 'Syncing...' : user ? '☁ Synced' : '☁ Save to Cloud'}
            </button>
          </div>
        </div>

        {/* Giving Intent Guide */}
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
            <div>
              <p className="font-body text-[12px] font-semibold text-deep-navy">Board service</p>
              <p className="font-body text-[12px] text-cool-grey/80 mt-1">Organizations you want to govern and guide</p>
            </div>
          </div>
        </div>

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
                    const first = wallet.orgs.find(o => !o.givingIntent)
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

        {/* localStorage quota warning */}
        {storageError === 'quota' && (
          <div className="flex items-center justify-between gap-4 bg-amber-50 border border-amber-200 rounded-2xl px-5 py-4 mb-6">
            <div className="flex items-center gap-3 min-w-0">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#D97706" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
              </svg>
              <p className="font-body text-[13px] text-deep-navy">
                Your wallet is full. Your browser's storage limit has been reached. Remove some saved nonprofits to free up space.
              </p>
            </div>
          </div>
        )}

        {/* Corruption recovery notice */}
        {corruptionDetected && (
          <div className="flex items-center gap-4 bg-amber-50 border border-amber-200 rounded-2xl px-5 py-4 mb-6">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#D97706" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            <p className="font-body text-[13px] text-deep-navy">
              Your wallet data was unreadable and has been cleared. You can browse the directory and save your nonprofits again.
            </p>
          </div>
        )}

        {/* Filters — only shown when wallet is large enough to benefit from filtering */}
        {wallet.orgs.length >= 5 && <div className="bg-white rounded-2xl border border-light-grey p-5 mb-8">
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
                <option value="board">Board</option>
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
        </div>}

        {/* No results message */}
        {filteredOrgs.length === 0 && wallet.orgs.length > 0 && (
          <div className="bg-white border border-light-grey rounded-2xl p-6 mb-6 text-center">
            <p className="font-body text-[14px] text-cool-grey">
              No organizations match your filters.{' '}
              <button onClick={handleClearFilters} className="text-soft-gold hover:text-bright-gold underline">
                Clear filters
              </button>
            </p>
          </div>
        )}

        {/* Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredOrgs.map(org => (
            <div key={org.ein} className="flex flex-col gap-2">
              {staleEins.has(org.ein) && (
                <div className="flex items-center justify-between gap-3 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
                  <div className="flex items-center gap-2 min-w-0">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#D97706" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0">
                      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                      <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                    </svg>
                    <p className="font-body text-[12px] text-deep-navy leading-snug">
                      This organization may no longer be active in our registry.
                    </p>
                  </div>
                  <button
                    onClick={() => handleRemove(org.ein)}
                    className="shrink-0 px-3 py-1.5 rounded-lg bg-amber-100 hover:bg-amber-200 text-amber-800 font-body text-[11px] font-semibold transition-colors whitespace-nowrap"
                  >
                    Remove from wallet
                  </button>
                </div>
              )}
              <WalletCard
                org={org}
                onRemove={handleRemove}
                onEdit={handleEdit}
              />
            </div>
          ))}
        </div>
      </div>

      {editingEin && (
        <EditIntentModal
          org={wallet.orgs.find(o => o.ein === editingEin)!}
          isOpen={!!editingEin}
          onClose={handleEditClose}
        />
      )}
    </div>
  )
}
