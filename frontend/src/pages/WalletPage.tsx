import React, { useState, useMemo, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { useWallet } from '../contexts/WalletContext'
import WalletCard from '../components/WalletCard'
import EditIntentModal from '../components/EditIntentModal'
import type { WalletOrg } from '../types/wallet'
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

/**
 * WalletPage: Main page showing all saved nonprofits
 * Features: sorting, filtering, search, and intent editing
 */
export default function WalletPage() {
  usePageMeta(
    'Your Giving Wallet | Daanaa',
    'Save nonprofits you\'re interested in and track your giving intentions.'
  )

  const navigate = useNavigate()
  const { wallet, removeOrg, updateIntent } = useWallet()

  const [sortBy, setSortBy] = useState<SortBy>('recent')
  const [filterState, setFilterState] = useState<FilterState>({
    intent: 'all',
    health: 'all',
  })
  const [searchTerm, setSearchTerm] = useState('')
  const [searchError, setSearchError] = useState<string | null>(null)
  const [editingEin, setEditingEin] = useState<string | null>(null)

  // Memoized filtered and sorted orgs
  const filteredOrgs = useMemo(() => {
    let result = wallet.orgs

    // Apply search filter
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

    // Apply intent filter
    if (filterState.intent !== 'all') {
      result = result.filter(org => org.givingIntent?.type === filterState.intent)
    }

    // Apply health filter
    if (filterState.health !== 'all') {
      result = result.filter(org => org.merit_health_signal_v5 === filterState.health)
    }

    // Apply sorting
    const sorted = [...result]
    switch (sortBy) {
      case 'recent':
        sorted.sort((a, b) => b.bookmarkedAt - a.bookmarkedAt)
        break
      case 'name':
        sorted.sort((a, b) => a.name.localeCompare(b.name))
        break
      case 'health':
        const healthOrder = { HEALTHY: 0, STABLE: 1, CAUTION: 2 }
        sorted.sort((a, b) => healthOrder[a.merit_health_signal_v5] - healthOrder[b.merit_health_signal_v5])
        break
    }

    return sorted
  }, [wallet.orgs, searchTerm, filterState, sortBy])

  // Handlers with validation
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

    // Allow empty search
    if (value === '') {
      setSearchTerm('')
      return
    }

    // Validate non-empty search
    try {
      const validated = validateSearchTerm(value)
      setSearchTerm(validated)
    } catch (err) {
      setSearchError((err as Error).message)
      // Don't update search term on validation error
    }
  }, [])

  const handleRemove = useCallback((ein: string) => {
    if (confirm('Remove this organization from your wallet?')) {
      removeOrg(ein)
    }
  }, [removeOrg])

  const handleEdit = useCallback((ein: string) => {
    setEditingEin(ein)
  }, [])

  const handleEditClose = useCallback(() => {
    setEditingEin(null)
  }, [])

  // Empty state
  if (wallet.orgs.length === 0) {
    return (
      <div className="bg-warm-cream min-h-screen py-12 md:py-16">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
          <h1 className="text-4xl font-display text-deep-navy mb-8">Your Giving Wallet</h1>

          <div className="bg-white rounded-lg border border-light-grey p-12 text-center">
            <svg
              className="w-16 h-16 mx-auto text-cool-grey mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M12 6v6m0 0v6m0-6h6m0 0h6m-6-6l-6-6m6 6l6-6M3 12a9 9 0 1118 0 9 9 0 01-18 0z"
              />
            </svg>

            <h2 className="text-2xl font-display text-deep-navy mb-3">Your wallet is empty</h2>
            <p className="text-cool-grey mb-6 max-w-md mx-auto">
              Add nonprofits from the directory to get started. Save organizations you're interested in supporting,
              signal your giving or volunteering intent, and track your impact.
            </p>

            <div className="flex gap-3 justify-center">
              <button
                onClick={() => navigate('/directory')}
                className="px-6 py-3 bg-soft-gold text-white rounded-lg font-medium hover:bg-soft-gold/90 transition-colors"
              >
                Browse Directory
              </button>
              <button
                onClick={() => navigate('/')}
                className="px-6 py-3 bg-warm-cream text-deep-navy rounded-lg font-medium hover:bg-warm-cream/70 transition-colors border border-light-grey"
              >
                Start Exploring
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Main view with orgs
  return (
    <div className="bg-warm-cream min-h-screen py-12 md:py-16">
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="text-4xl font-display text-deep-navy mb-2">Your Giving Wallet</h1>
            <p className="text-cool-grey">
              {wallet.orgs.length} organization{wallet.orgs.length !== 1 ? 's' : ''} saved
            </p>
          </div>
          <button
            onClick={() => navigate('/directory')}
            className="px-4 py-2 bg-soft-gold text-white rounded-lg text-sm font-medium hover:bg-soft-gold/90 transition-colors whitespace-nowrap"
          >
            + Add More
          </button>
        </div>

        {/* Filters & Search */}
        <div className="bg-white rounded-lg border border-light-grey p-4 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            {/* Sort */}
            <div>
              <label className="text-xs font-semibold text-cool-grey uppercase">Sort</label>
              <select
                value={sortBy}
                onChange={handleSort}
                aria-label="Sort by"
                className="w-full mt-1 px-3 py-2 border border-light-grey rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold"
              >
                <option value="recent">Recently Added</option>
                <option value="name">Name (A-Z)</option>
                <option value="health">Financial Health</option>
              </select>
            </div>

            {/* Filter: Intent */}
            <div>
              <label className="text-xs font-semibold text-cool-grey uppercase">Intent</label>
              <select
                value={filterState.intent}
                onChange={handleIntentFilter}
                aria-label="Filter by intent"
                className="w-full mt-1 px-3 py-2 border border-light-grey rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold"
              >
                <option value="all">All</option>
                <option value="giving">Giving</option>
                <option value="volunteer">Volunteering</option>
                <option value="board">Board</option>
              </select>
            </div>

            {/* Filter: Health */}
            <div>
              <label className="text-xs font-semibold text-cool-grey uppercase">Health</label>
              <select
                value={filterState.health}
                onChange={handleHealthFilter}
                aria-label="Filter by health"
                className="w-full mt-1 px-3 py-2 border border-light-grey rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold"
              >
                <option value="all">All</option>
                <option value="HEALTHY">Healthy</option>
                <option value="STABLE">Stable</option>
                <option value="CAUTION">Caution</option>
              </select>
            </div>

            {/* Clear Filters */}
            <div className="flex items-end">
              <button
                onClick={handleClearFilters}
                className="w-full px-3 py-2 bg-warm-cream text-deep-navy rounded-lg text-sm font-medium hover:bg-warm-cream/70 transition-colors border border-light-grey"
              >
                Clear Filters
              </button>
            </div>
          </div>

          {/* Search */}
          <div>
            <input
              type="text"
              placeholder="Search by name, location, or cause..."
              value={searchTerm}
              onChange={e => handleSearchChange(e.target.value)}
              className="w-full px-4 py-2 border border-light-grey rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold"
              aria-invalid={!!searchError}
            />
            {searchError && (
              <p className="text-red-600 text-xs mt-1" role="alert">
                {searchError}
              </p>
            )}
          </div>
        </div>

        {/* Results Message */}
        {filteredOrgs.length === 0 && wallet.orgs.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <p className="text-blue-800 text-sm">
              No organizations match your filters. Try adjusting your search or filters.
            </p>
          </div>
        )}

        {/* Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredOrgs.map(org => (
            <WalletCard
              key={org.ein}
              org={org}
              onRemove={handleRemove}
              onEdit={handleEdit}
            />
          ))}
        </div>

        {/* Footer Actions */}
        {filteredOrgs.length > 0 && (
          <div className="mt-12 text-center space-y-3">
            <div className="flex gap-3 justify-center flex-wrap">
              <button className="px-6 py-2 bg-warm-cream text-deep-navy rounded-lg text-sm font-medium hover:bg-warm-cream/70 transition-colors border border-light-grey">
                Export Wallet
              </button>
              <button className="px-6 py-2 bg-warm-cream text-deep-navy rounded-lg text-sm font-medium hover:bg-warm-cream/70 transition-colors border border-light-grey">
                Share Wallet
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Edit Intent Modal */}
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
