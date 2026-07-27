import React, { useState, useMemo, useCallback, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { useWallet } from '../contexts/WalletContext'
import { useAuth } from '../contexts/AuthContext'
import { OrgCardRow } from '../components/OrgCard'
import Breadcrumb from '../components/Breadcrumb'
import ImpactSummary from '../components/ImpactSummary'
import WalletAccountLink from '../components/WalletAccountLink'
import DonationLogger from '../components/DonationLogger'
import VolunteerLogger from '../components/VolunteerLogger'
import CloseTheLoopPrompt from '../components/CloseTheLoopPrompt'
import { RhythmNudges, RhythmControl } from '../components/GivingRhythm'
import RecurringNudge from '../components/RecurringNudge'
import { isTemplateDue } from '../types/wallet'
import type { ApiOrganization } from '../data/api'
import { API_BASE } from '../lib/platform'
import {
  validateSearchTerm,
  validateFilterValue,
  validateSortValue,
  logValidationError,
} from '../utils/walletValidation'

type SortBy = 'recent' | 'name' | 'health'
type WalletTab = 'funding' | 'volunteering'
type FilterIntent = 'all' | 'giving' | 'volunteer'
type FilterHealth = 'all' | 'full_context' | 'regional_context' | 'emerging' | 'unscored'

interface FilterState {
  intent: FilterIntent
  health: FilterHealth
}

// Approval status chip for event-submitted volunteer hours. Absent status =
// private log (no chip — private is the quiet default, not a state to label).
// "Approved" is always framed as nonprofit-approved, never Daanaa-verified.
function VolunteerStatusChip({ status, rejectionReason }: { status?: string; rejectionReason?: string }) {
  if (!status || status === 'private') return null
  const styles: Record<string, string> = {
    submitted: 'bg-amber-100 text-amber-800',
    approved: 'bg-emerald-100 text-emerald-700',
    rejected: 'bg-red-100 text-destructive',
  }
  const labels: Record<string, string> = {
    submitted: 'Submitted for review',
    approved: 'Nonprofit approved',
    rejected: 'Not approved',
  }
  return (
    <span
      className={`shrink-0 px-1.5 py-0.5 rounded text-micro font-semibold ${styles[status] ?? 'bg-light-grey text-cool-grey'}`}
      title={status === 'rejected' && rejectionReason ? rejectionReason : undefined}
    >
      {labels[status] ?? status}
    </span>
  )
}

export default function WalletPage() {
  usePageMeta(
    'Your Giving Wallet | Daanaa',
    "Save nonprofits you're interested in and track your giving intentions."
  )

  const navigate = useNavigate()
  const { user, signInWithGoogle, signOut } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const {
    entries,
    removeEntry,
    syncStatus,
    migrationData,
    applyMigration,
    dismissMigration,
    refreshVolunteerStatuses,
    logDonation,
    snoozeRecurringTemplate,
  } = useWallet()

  // On open, refresh approval status of any event-submitted volunteer hours
  // (submission-id lookup only — no identity leaves the device).
  useEffect(() => {
    refreshVolunteerStatuses()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

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

  const [activeTab, setActiveTab] = useState<WalletTab>('funding')
  const [expandedLogs, setExpandedLogs] = useState<Set<string>>(new Set())
  const toggleLog = useCallback((ein: string) => {
    setExpandedLogs(prev => { const n = new Set(prev); n.has(ein) ? n.delete(ein) : n.add(ein); return n })
  }, [])

  const downloadCsv = useCallback(() => {
    const rows: string[][] = [
      ['org_name', 'ein', 'list', 'log_type', 'date', 'amount_usd', 'hours', 'notes'],
    ]
    for (const entry of entries) {
      const name = orgDataMap.get(entry.ein)?.organization_name ?? entry.ein
      const list = [entry.inFunding !== false ? 'funding' : '', entry.inVolunteering ? 'volunteering' : ''].filter(Boolean).join('+') || 'funding'
      if (!entry.donations?.length && !entry.volunteerHours?.length) {
        rows.push([name, entry.ein, list, '', '', '', '', ''])
      }
      for (const d of entry.donations ?? []) {
        rows.push([name, entry.ein, list, 'donation', d.date, String(d.amount), '', d.notes ?? ''])
      }
      for (const v of entry.volunteerHours ?? []) {
        rows.push([name, entry.ein, list, 'volunteer_hours', v.date, '', String(v.hours), v.notes ?? ''])
      }
    }
    const csv = rows.map(r => r.map(c => `"${c.replace(/"/g, '""')}"`).join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = 'daanaa-wallet.csv'; a.click()
    URL.revokeObjectURL(url)
  }, [entries, orgDataMap])

  // Filter / sort state
  const [sortBy, setSortBy] = useState<SortBy>('recent')
  const [filterState, setFilterState] = useState<FilterState>({ intent: 'all', health: 'all' })
  const [searchTerm, setSearchTerm] = useState('')
  const [searchError, setSearchError] = useState<string | null>(null)

  const fundingEntries = useMemo(() =>
    entries.filter(e => e.inFunding === true || (e.inFunding === undefined && !e.inVolunteering)),
  [entries])

  const volunteeringEntries = useMemo(() =>
    entries.filter(e => e.inVolunteering === true),
  [entries])

  const filteredEntries = useMemo(() => {
    let result = activeTab === 'funding' ? fundingEntries : volunteeringEntries

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
        const tier = org?.scoring_tier
        if (filterState.health === 'full_context') return tier === '1_Full_Context'
        if (filterState.health === 'regional_context') return tier === '2_Regional_Context'
        if (filterState.health === 'emerging') return tier === '3_Limited_Context' || tier === '4_Archetype_Only'
        if (filterState.health === 'unscored') return !tier
        return true
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
        const tierOrder: Record<string, number> = { '1_Full_Context': 0, '2_Regional_Context': 1, '3_Limited_Context': 2, '4_Archetype_Only': 3 }
        sorted.sort((a, b) => {
          const ta = orgDataMap.get(a.ein)?.scoring_tier ?? ''
          const tb = orgDataMap.get(b.ein)?.scoring_tier ?? ''
          return (tierOrder[ta] ?? 99) - (tierOrder[tb] ?? 99)
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

  const hasActiveFilters =
    filterState.intent !== 'all' || filterState.health !== 'all' || searchTerm !== ''

  // No auth gate — device-first. Passphrase/backup is optional.

  // ─── Empty state ────────────────────────────────────────────────────────────
  if (entries.length === 0) {
    return (
      <div className="bg-warm-cream min-h-[100dvh] pt-nav">
        <div className="max-w-[720px] mx-auto px-6 py-16">
          <h1 className="font-display italic text-deep-navy text-headline-lg mb-2">Your Giving Wallet</h1>
          <p className="font-body text-cool-grey mb-10">Track your giving, volunteer hours, and community impact.</p>

          {/* Device-first storage notice */}
          <div className="bg-soft-gold/10 border border-soft-gold/30 rounded-2xl p-5 mb-8">
            <p className="font-body text-sm text-deep-navy">
              📱 Your data is stored on this device for now. Sign in with Google anytime to back it up and help us measure cumulative community impact.
            </p>
          </div>

          {/* Impact dashboard — visible from day one so new users see what they're building toward */}
          <div className="mb-8">
            <p className="font-body text-xs text-cool-grey uppercase tracking-wide font-semibold mb-3">Your Impact</p>
            <ImpactSummary />
          </div>

          <div className="bg-white rounded-2xl border border-light-grey p-12 text-center">
            <div className="w-14 h-14 rounded-full bg-soft-gold/10 flex items-center justify-center mx-auto mb-5">
              <svg className="w-7 h-7 text-soft-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
              </svg>
            </div>
            <h2 className="font-display italic text-deep-navy text-title-lg mb-2">Your wallet is empty</h2>
            <p className="font-body text-body-lg text-cool-grey mb-8 max-w-sm mx-auto">
              Browse the directory and save nonprofits you care about. Then log your giving and volunteer hours.
            </p>
            <button
              onClick={() => navigate('/directory')}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-soft-gold text-deep-navy font-body text-body font-semibold hover:bg-bright-gold transition-colors"
            >
              Browse nonprofits
            </button>
          </div>

          {/* Optional Google sign-in — device-first, sign in only if you want backup */}
          {!user && (
            <div className="mt-6 text-center">
              <button
                onClick={signInWithGoogle}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-light-grey bg-white font-body text-small text-cool-grey hover:border-soft-gold/40 hover:text-deep-navy transition-colors"
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
                Sign in with Google to back up across devices
              </button>
            </div>
          )}
        </div>
      </div>
    )
  }

  // ─── Main wallet view ────────────────────────────────────────────────────────
  return (
    <div className="bg-warm-cream min-h-[100dvh] pt-nav">
      <Breadcrumb items={[{ label: 'Home', href: '/' }, { label: 'Wallet' }]} />
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12 py-10">

        {/* Header */}
        <div className="flex items-start justify-between mb-8 flex-wrap gap-4">
          <div>
            <h1 className="font-display italic text-deep-navy text-headline-lg mb-1">Your Giving Wallet</h1>
            <p className="font-body text-body text-cool-grey">
              {entries.length} organization{entries.length !== 1 ? 's' : ''} saved
            </p>
            <p className="font-body text-small text-cool-grey/70 mt-2 max-w-md">
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
              onClick={downloadCsv}
              className="font-body text-xs text-soft-gold hover:text-bright-gold transition-colors"
            >
              Download CSV
            </button>
            <button
              onClick={() => navigate('/directory')}
              className="px-4 py-2 rounded-xl bg-soft-gold text-deep-navy font-body text-small font-semibold hover:bg-bright-gold transition-colors whitespace-nowrap"
            >
              + Add more
            </button>
          </div>
        </div>

        {/* Close-the-loop prompt — log recent donations */}
        <CloseTheLoopPrompt
          walletEntries={entries}
          orgDataMap={orgDataMap}
        />

        {/* Funding / Volunteering tabs */}
        <div className="flex gap-2 mb-8">
          <button
            onClick={() => setActiveTab('funding')}
            className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-full font-body text-body font-semibold transition-colors ${activeTab === 'funding' ? 'bg-green-500 text-white shadow-sm' : 'bg-white border border-light-grey text-cool-grey hover:border-green-300 hover:text-green-600'}`}
          >
            <svg width="15" height="15" viewBox="0 0 24 24"
              fill={activeTab === 'funding' ? 'white' : 'none'}
              stroke={activeTab === 'funding' ? 'white' : '#22c55e'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
            </svg>
            Funding ({fundingEntries.length})
          </button>
          <button
            onClick={() => setActiveTab('volunteering')}
            className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-full font-body text-body font-semibold transition-colors ${activeTab === 'volunteering' ? 'bg-destructive/50 text-white shadow-sm' : 'bg-white border border-light-grey text-cool-grey hover:border-red-300 hover:text-red-500'}`}
          >
            <svg width="15" height="15" viewBox="0 0 24 24"
              fill={activeTab === 'volunteering' ? 'white' : 'none'}
              stroke={activeTab === 'volunteering' ? 'white' : '#ef4444'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
            </svg>
            Volunteering ({volunteeringEntries.length})
          </button>
        </div>

        {/* Impact Summary */}
        <div className="mb-10">
          <p className="font-body text-xs text-cool-grey uppercase tracking-wide font-semibold mb-3">Your Impact</p>
          <ImpactSummary />
        </div>

        {/* Filters — only shown when wallet is large enough to benefit from filtering */}
        {entries.length >= 5 && (
          <div className="bg-white rounded-2xl border border-light-grey p-5 mb-8">
            <p className="font-body text-xs text-cool-grey uppercase tracking-wide font-semibold mb-3">Filters & Search</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
              <div>
                <label className="font-body text-label font-semibold text-cool-grey uppercase tracking-wide block mb-1">Sort</label>
                <select
                  value={sortBy}
                  onChange={handleSort}
                  aria-label="Sort by"
                  className="w-full px-3 py-2 border border-light-grey rounded-xl font-body text-small text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold/40 bg-white"
                >
                  <option value="recent">Recently added</option>
                  <option value="name">Name (A–Z)</option>
                  <option value="health">Financial health</option>
                </select>
              </div>

              <div>
                <label className="font-body text-label font-semibold text-cool-grey uppercase tracking-wide block mb-1">List Type</label>
                <select
                  value={filterState.intent}
                  onChange={handleIntentFilter}
                  aria-label="Filter by list type"
                  className="w-full px-3 py-2 border border-light-grey rounded-xl font-body text-small text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold/40 bg-white"
                >
                  <option value="all">All</option>
                  <option value="giving">Funding</option>
                  <option value="volunteer">Volunteering</option>
                </select>
              </div>

              <div>
                <label className="font-body text-label font-semibold text-cool-grey uppercase tracking-wide block mb-1">Health</label>
                <select
                  value={filterState.health}
                  onChange={handleHealthFilter}
                  aria-label="Filter by health"
                  className="w-full px-3 py-2 border border-light-grey rounded-xl font-body text-small text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold/40 bg-white"
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
                  className="w-full px-3 py-2 rounded-xl border border-light-grey font-body text-small text-cool-grey hover:border-soft-gold/40 hover:text-deep-navy disabled:opacity-40 disabled:cursor-default transition-colors"
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
              className="w-full px-4 py-2.5 border border-light-grey rounded-xl font-body text-small text-deep-navy placeholder:text-cool-grey/60 focus:outline-none focus:ring-2 focus:ring-soft-gold/40"
              aria-invalid={!!searchError}
            />
            {searchError && (
              <p className="font-body text-caption text-destructive mt-1" role="alert">{searchError}</p>
            )}
          </div>
        )}

        {/* No results message */}
        {filteredEntries.length === 0 && entries.length > 0 && (
          <div className="bg-white border border-light-grey rounded-2xl p-6 mb-6 text-center">
            <p className="font-body text-body text-cool-grey">
              No organizations match your filters.{' '}
              <button onClick={handleClearFilters} className="text-soft-gold hover:text-bright-gold underline">
                Clear filters
              </button>
            </p>
          </div>
        )}


        {/* Recurring gift nudges — due reminders for established recurring templates */}
        {activeTab === 'funding' && (
          <div className="space-y-3 mb-6">
            {fundingEntries.map(entry => {
              if (!entry.recurringTemplate || !isTemplateDue(entry)) return null
              const apiOrg = orgDataMap.get(entry.ein)
              const today = new Date().toISOString().split('T')[0]
              return (
                <RecurringNudge
                  key={entry.ein}
                  orgName={apiOrg?.organization_name || 'Unknown organization'}
                  amount={entry.recurringTemplate.amount}
                  cadence={entry.recurringTemplate.cadence}
                  onConfirm={() => {
                    // Log donation with template amount, today's date
                    logDonation(entry.ein, entry.recurringTemplate!.amount, today)
                  }}
                  onSnooze={() => {
                    // Snooze until next cycle: 30 days for monthly, 91 for quarterly, 365 for yearly
                    const daysToAdd = entry.recurringTemplate!.cadence === 'monthly' ? 30
                      : entry.recurringTemplate!.cadence === 'quarterly' ? 91 : 365
                    const snoozeDate = new Date()
                    snoozeDate.setDate(snoozeDate.getDate() + daysToAdd)
                    snoozeRecurringTemplate(entry.ein, snoozeDate.toISOString().split('T')[0])
                  }}
                />
              )
            })}
          </div>
        )}

        {/* Giving rhythm nudges — due gifts, computed on-device only */}
        {activeTab === 'funding' && <RhythmNudges entries={fundingEntries} orgDataMap={orgDataMap} />}

        {/* Cards — OrgCardRow style (wider rectangles, matches directory) */}
        <div className={`flex flex-col gap-2 ${hydrating ? 'opacity-60' : ''}`}>
          {filteredEntries.map(entry => {
            const apiOrg = orgDataMap.get(entry.ein) ?? null
            const haslogs = (entry.donations?.length ?? 0) > 0 || (entry.volunteerHours?.length ?? 0) > 0

            if (!apiOrg && !haslogs) {
              // No API data and no logs — show loading skeleton
              return (
                <div key={entry.ein} className="bg-white border border-light-grey rounded-xl px-5 py-4 animate-pulse flex items-center gap-4">
                  <div className="flex-1 space-y-1.5">
                    <div className="h-4 w-3/4 bg-light-grey rounded" />
                    <div className="h-3 w-1/2 bg-light-grey rounded" />
                  </div>
                </div>
              )
            }

            if (!apiOrg && haslogs) {
              // No API data but has logs — show fallback card with logs
              const logOpen = expandedLogs.has(entry.ein)
              const donationCount = entry.donations?.length ?? 0
              const volCount = entry.volunteerHours?.length ?? 0
              return (
                <div key={entry.ein} className="group">
                  {/* Fallback card for unsaved org with logs */}
                  <div className="bg-white border border-light-grey rounded-xl px-5 py-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-body text-sm font-semibold text-deep-navy">{entry.ein}</p>
                        <p className="font-body text-xs text-cool-grey/70 mt-1">(removed from wallet — logs preserved)</p>
                      </div>
                      <button
                        onClick={e => { e.preventDefault(); handleRemove(entry.ein) }}
                        title="Remove from wallet"
                        className="w-6 h-6 flex items-center justify-center rounded-full bg-white border border-light-grey text-cool-grey hover:text-red-500 hover:border-red-300 transition-all"
                      >
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                      </button>
                    </div>
                  </div>

                  {/* Log action strip */}
                  <div className="flex items-center gap-3 px-5 py-2 bg-white border border-t-0 border-light-grey rounded-b-xl">
                    <button
                      onClick={() => toggleLog(entry.ein)}
                      className="inline-flex items-center gap-1.5 font-body text-caption text-deep-navy hover:text-soft-gold transition-colors font-medium"
                    >
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M12 5v14M5 12h14"/>
                      </svg>
                      {logOpen ? 'Hide log' : 'View log'}
                    </button>
                    {donationCount > 0 && (
                      <span className="font-body text-label text-green-600">
                        {donationCount} donation{donationCount !== 1 ? 's' : ''}
                      </span>
                    )}
                    {volCount > 0 && (
                      <span className="font-body text-label text-red-500">
                        {volCount} volunteer session{volCount !== 1 ? 's' : ''}
                      </span>
                    )}
                    {logOpen && (
                      <svg className="ml-auto" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="18 15 12 9 6 15"/></svg>
                    )}
                  </div>

                  {/* Expandable log panel */}
                  {logOpen && (
                    <div className="border border-t-0 border-light-grey rounded-b-xl bg-warm-cream px-5 py-5 space-y-6">
                      {donationCount > 0 && (
                        <div>
                          <p className="font-body text-label font-semibold text-deep-navy uppercase tracking-wide mb-2">Donations</p>
                          <div className="space-y-1.5">
                            {entry.donations!.map(d => (
                              <div key={d.id} className="flex items-center gap-3 font-body text-small text-deep-navy">
                                <span className="text-cool-grey font-medium w-[90px] shrink-0">{d.date}</span>
                                <span className="font-semibold text-green-700">${d.amount.toLocaleString()}</span>
                                {d.notes && <span className="text-cool-grey truncate">{d.notes}</span>}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      {volCount > 0 && (
                        <div>
                          <p className="font-body text-label font-semibold text-deep-navy uppercase tracking-wide mb-2">Volunteer hours</p>
                          <div className="space-y-1.5">
                            {entry.volunteerHours!.map(v => (
                              <div key={v.id} className="flex items-center gap-3 font-body text-small text-deep-navy">
                                <span className="text-cool-grey font-medium w-[90px] shrink-0">{v.date}</span>
                                <span className="font-semibold text-destructive">{v.hours}h</span>
                                <VolunteerStatusChip status={v.status} rejectionReason={v.rejectionReason} />
                                {v.notes && <span className="text-cool-grey truncate">{v.notes}</span>}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            }
            // At this point apiOrg is guaranteed to exist (either we returned already or it exists)
            const org = apiOrg!
            const cardOrg = {
              id: org.EIN,
              name: org.organization_name,
              ein: org.EIN,
              city: org.CITY || '',
              state: org.STATE || '',
              category: org.NTEE1 || '',
              subcategory: org.NTEECC || org.NTEE1 || '',
              meritScore: Math.round(org.peer_percentile ?? org.ntee1_percentile ?? 0),
              hasScore: (org.peer_percentile ?? org.ntee1_percentile) !== null,
              revenueBand: org.revenue_band ?? null,
              dataSource: org.data_source ?? null,
              latestTaxYear: org.latest_tax_year ?? null,
              ntee1TotalOrgs: org.ntee1_total_orgs ?? null,
              hasMission: org.has_mission ?? null,
              hasWebsite: org.has_website ?? null,
              revenue: org.total_revenue ?? 0,
              assets: 0, employees: 0, founded: 0,
              mission: org.mission || '',
              programs: [] as string[],
              leadership: [] as { name: string; title: string; initials: string }[],
              boardSize: 0,
              revenueTrend: [] as { year: number; amount: number }[],
              programEfficiency: 0, fundraisingRatio: 0, operatingReserve: 0, transparencyScore: 0,
            }
            const logOpen = expandedLogs.has(entry.ein)
            const donationCount = entry.donations?.length ?? 0
            const volCount = entry.volunteerHours?.length ?? 0
            const showDonationLogger = activeTab === 'funding' || entry.inFunding === true || (entry.inFunding === undefined && !entry.inVolunteering)
            const showVolunteerLogger = activeTab === 'volunteering' || entry.inVolunteering === true
            return (
              <div key={entry.ein} className="group">
                {/* Row + action strip */}
                <div className="relative">
                  <OrgCardRow org={cardOrg} apiOrg={org} hideCompare />
                  <button
                    onClick={e => { e.preventDefault(); handleRemove(entry.ein) }}
                    title="Remove from wallet"
                    aria-label={`Remove ${org.organization_name} from wallet`}
                    className="absolute top-3 right-3 w-6 h-6 flex items-center justify-center rounded-full bg-white border border-light-grey text-cool-grey hover:text-red-500 hover:border-red-300 opacity-0 group-hover:opacity-100 transition-all duration-150 z-10"
                  >
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  </button>
                </div>

                {/* Log action strip */}
                <div className="flex items-center gap-3 px-5 py-2 bg-white border border-t-0 border-light-grey rounded-b-xl -mt-1">
                  <button
                    onClick={() => toggleLog(entry.ein)}
                    className="inline-flex items-center gap-1.5 font-body text-caption text-deep-navy hover:text-soft-gold transition-colors font-medium"
                  >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 5v14M5 12h14"/>
                    </svg>
                    {logOpen ? 'Hide log' : 'Log activity'}
                  </button>
                  {donationCount > 0 && (
                    <span className="font-body text-label text-green-600">
                      {donationCount} donation{donationCount !== 1 ? 's' : ''}
                    </span>
                  )}
                  {volCount > 0 && (
                    <span className="font-body text-label text-red-500">
                      {volCount} volunteer session{volCount !== 1 ? 's' : ''}
                    </span>
                  )}
                  {logOpen && (
                    <svg className="ml-auto" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="18 15 12 9 6 15"/></svg>
                  )}
                </div>

                {/* Expandable log panel */}
                {logOpen && (
                  <div className="border border-t-0 border-light-grey rounded-b-xl bg-warm-cream px-5 py-5 -mt-1 space-y-6">

                    {/* Existing donations */}
                    {donationCount > 0 && (
                      <div>
                        <p className="font-body text-label font-semibold text-deep-navy uppercase tracking-wide mb-2">Donations</p>
                        <div className="space-y-1.5">
                          {entry.donations!.map(d => (
                            <div key={d.id} className="flex items-center gap-3 font-body text-small text-deep-navy">
                              <span className="text-cool-grey font-medium w-[90px] shrink-0">{d.date}</span>
                              <span className="font-semibold text-green-700">${d.amount.toLocaleString()}</span>
                              {d.notes && <span className="text-cool-grey truncate">{d.notes}</span>}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Existing volunteer hours */}
                    {volCount > 0 && (
                      <div>
                        <p className="font-body text-label font-semibold text-deep-navy uppercase tracking-wide mb-2">Volunteer hours</p>
                        <div className="space-y-1.5">
                          {entry.volunteerHours!.map(v => (
                            <div key={v.id} className="flex items-center gap-3 font-body text-small text-deep-navy">
                              <span className="text-cool-grey font-medium w-[90px] shrink-0">{v.date}</span>
                              <span className="font-semibold text-destructive">{v.hours}h</span>
                              <VolunteerStatusChip status={v.status} rejectionReason={v.rejectionReason} />
                              {v.notes && <span className="text-cool-grey truncate">{v.notes}</span>}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Giving rhythm — saved cadence for this org */}
                    {showDonationLogger && (
                      <div>
                        <p className="font-body text-label font-semibold text-deep-navy uppercase tracking-wide mb-2">Giving rhythm</p>
                        <RhythmControl entry={entry} orgName={org.organization_name} />
                      </div>
                    )}

                    {/* Logger forms */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                      {showDonationLogger && (
                        <DonationLogger ein={entry.ein} orgName={org.organization_name} />
                      )}
                      {showVolunteerLogger && (
                        <VolunteerLogger ein={entry.ein} orgName={org.organization_name} />
                      )}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Recovery */}
        <div className="mt-12">
          <p className="font-body text-xs text-cool-grey uppercase tracking-wide font-semibold mb-3">Recovery</p>
          <WalletAccountLink />
        </div>

        {/* Device-first storage notice + Optional backup */}
        <div className="mt-6 bg-soft-gold/10 border border-soft-gold/30 rounded-2xl p-6">
          <div className="flex items-start gap-4">
            <div className="flex-1">
              <p className="font-body font-semibold text-deep-navy mb-2">📱 Your data is stored locally</p>
              <p className="font-body text-sm text-cool-grey">
                Your giving logs and volunteer hours are saved on this device. Back them up and help us measure community impact.
              </p>
            </div>
            {!user && (
              <button
                onClick={signInWithGoogle}
                className="shrink-0 px-4 py-2 rounded-lg bg-soft-gold text-deep-navy font-body text-sm font-semibold hover:bg-bright-gold transition-colors whitespace-nowrap"
              >
                Sign in with Google
              </button>
            )}
            {user && (
              <div className="shrink-0 text-right">
                <p className="font-body text-xs text-cool-grey mb-1">✓ Backup enabled</p>
                <p className="font-body text-xs text-deep-navy font-semibold mb-2 break-all">{user.email}</p>
                <button
                  onClick={() => signOut().catch(e => console.error('Sign out error:', e))}
                  className="text-xs text-cool-grey hover:text-red-500 transition-colors font-medium"
                >
                  Sign out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

    </div>
  )
}
