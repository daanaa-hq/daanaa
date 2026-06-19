import React, { useState, useMemo, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { useWallet } from '../contexts/WalletContext'
import WalletCard from '../components/WalletCard'
import EditIntentModal from '../components/EditIntentModal'
import {
  validateSearchTerm,
  validateFilterValue,
  validateSortValue,
  logValidationError,
} from '../utils/walletValidation'

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
  const { wallet, removeOrg, updateIntent } = useWallet()

  const [sortBy, setSortBy] = useState<SortBy>('recent')
  const [filterState, setFilterState] = useState<FilterState>({ intent: 'all', health: 'all' })
  const [searchTerm, setSearchTerm] = useState('')
  const [searchError, setSearchError] = useState<string | null>(null)
  const [editingEin, setEditingEin] = useState<string | null>(null)

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

  // Empty state
  if (wallet.orgs.length === 0) {
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

  return (
    <div className="bg-warm-cream min-h-[100dvh] pt-[72px]">
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12 py-10">

        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="font-display italic text-deep-navy text-[32px] mb-1">Your Giving Wallet</h1>
            <p className="font-body text-[14px] text-cool-grey">
              {wallet.orgs.length} organization{wallet.orgs.length !== 1 ? 's' : ''} saved
            </p>
          </div>
          <button
            onClick={() => navigate('/directory')}
            className="px-4 py-2 rounded-xl bg-soft-gold text-deep-navy font-body text-[13px] font-semibold hover:bg-bright-gold transition-colors whitespace-nowrap"
          >
            + Add more
          </button>
        </div>

        {/* Filters */}
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
        </div>

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
            <WalletCard
              key={org.ein}
              org={org}
              onRemove={handleRemove}
              onEdit={handleEdit}
            />
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
