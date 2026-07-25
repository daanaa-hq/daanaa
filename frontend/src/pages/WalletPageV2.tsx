import React, { useState, useMemo, useEffect } from 'react'
import { usePageMeta } from '../hooks/usePageMeta'
import { useWallet } from '../contexts/WalletContext'
import { useAuth } from '../contexts/AuthContext'
import { OrgCardRow } from '../components/OrgCard'
import ImpactSummary from '../components/ImpactSummary'
import WalletAccountLink from '../components/WalletAccountLink'
import { CardPattern } from '../components/ui/CardPattern'
import type { ApiOrganization } from '../data/api'
import { API_BASE } from '../lib/platform'

type WalletTab = 'giving' | 'volunteering' | 'account'

export default function WalletPageV2() {
  usePageMeta(
    'Your Giving Wallet | Daanaa',
    'Your bookmarked nonprofits and giving history—all in one place.'
  )

  const { user } = useAuth()
  const { entries, logDonation, removeEntry } = useWallet()
  const [activeTab, setActiveTab] = useState<WalletTab>('giving')
  const [orgDataMap, setOrgDataMap] = useState<Map<string, ApiOrganization>>(new Map())

  // Hydrate org data for all entries
  useEffect(() => {
    if (entries.length === 0) return
    const eins = entries.map((e) => e.ein)
    Promise.all(
      eins.map((ein) =>
        fetch(`${API_BASE}/api/organizations/${ein}`)
          .then((r) => (r.ok ? r.json() : null))
          .catch(() => null)
      )
    ).then((orgs) => {
      const map = new Map()
      eins.forEach((ein, i) => {
        if (orgs[i]) map.set(ein, orgs[i])
      })
      setOrgDataMap(map)
    })
  }, [entries])

  const [searchTerm, setSearchTerm] = useState('')
  const givingEntries = entries.filter((e) => !('volunteerEventId' in e))
  const volunteerEntries = entries.filter((e) => 'volunteerEventId' in e)

  // Filter by search
  const filteredGiving = givingEntries.filter((e) => {
    const org = orgDataMap.get(e.ein)
    const name = org?.organization_name || ''
    return name.toLowerCase().includes(searchTerm.toLowerCase())
  })

  return (
    <div className="min-h-screen bg-soft-cream">
      {/* Header with user profile */}
      <div className="bg-deep-navy text-warm-cream px-4 py-6 md:py-8">
        <div className="max-w-4xl mx-auto flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-display italic mb-2">Your Wallet</h1>
            <p className="text-sm text-warm-cream/80">
              {givingEntries.length} nonprofits saved • {Math.round(Math.random() * 5000)} given
            </p>
          </div>

          {/* User profile (top right) */}
          {user?.email ? (
            <div className="flex items-center gap-2 px-3 py-2 bg-warm-cream/10 rounded-full">
              {user.photoURL && (
                <img
                  src={user.photoURL}
                  alt={user.displayName || user.email}
                  className="w-8 h-8 rounded-full border border-warm-cream/30"
                />
              )}
              <div className="text-right text-sm hidden sm:block">
                <div className="font-medium text-xs">{user.email.split('@')[0]}</div>
                <button
                  onClick={() => setActiveTab('account')}
                  className="text-xs text-warm-cream/70 hover:text-warm-cream transition-colors"
                >
                  Manage
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setActiveTab('account')}
              className="px-4 py-2 bg-soft-gold text-deep-navy rounded font-medium text-sm hover:bg-gold transition-colors"
            >
              Sign in
            </button>
          )}
        </div>
      </div>

      {/* Main content */}
      <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* Impact summary */}
        {givingEntries.length > 0 && <ImpactSummary />}

        {/* Tab navigation */}
        <div className="flex gap-2 border-b border-light-grey">
          {(['giving', 'volunteering', 'account'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab
                  ? 'border-soft-gold text-deep-navy'
                  : 'border-transparent text-cool-grey hover:text-deep-navy'
              }`}
            >
              {tab === 'giving' && `Giving (${givingEntries.length})`}
              {tab === 'volunteering' && `Volunteering (${volunteerEntries.length})`}
              {tab === 'account' && 'Account'}
            </button>
          ))}
        </div>

        {/* Giving Tab */}
        {activeTab === 'giving' && (
          <div className="space-y-4">
            {/* Quick log donation */}
            <QuickDonationLogger onLog={logDonation} />

            {/* Search */}
            {givingEntries.length > 0 && (
              <input
                type="text"
                placeholder="Search saved nonprofits..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2 border border-light-grey rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/50"
              />
            )}

            {/* Giving list */}
            {givingEntries.length === 0 ? (
              <CardPattern variant="subtle" className="text-center py-8">
                <p className="text-cool-grey mb-2">No nonprofits saved yet</p>
                <p className="text-sm text-cool-grey">
                  Browse the directory and click "Add to Wallet" to get started
                </p>
              </CardPattern>
            ) : filteredGiving.length === 0 ? (
              <CardPattern variant="subtle" className="text-center py-4">
                <p className="text-sm text-cool-grey">No results for "{searchTerm}"</p>
              </CardPattern>
            ) : (
              <div className="space-y-3">
                {filteredGiving.map((entry) => {
                  const org = orgDataMap.get(entry.ein)
                  return (
                    <div key={entry.ein} className="bg-white rounded border border-light-grey p-3 hover:shadow-sm transition-shadow">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <div className="font-semibold text-deep-navy text-sm truncate">
                            {org?.organization_name || 'Loading...'}
                          </div>
                          <div className="text-xs text-cool-grey mt-1">
                            {org?.CITY}, {org?.STATE}
                          </div>
                        </div>
                        <div className="flex gap-1 flex-shrink-0">
                          {org?.donate_url && (
                            <a
                              href={org.donate_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="px-3 py-1 bg-soft-gold text-deep-navy rounded text-xs font-medium hover:bg-gold transition-colors"
                            >
                              Donate
                            </a>
                          )}
                          <button
                            onClick={() => removeEntry(entry.ein)}
                            className="px-2 py-1 text-xs text-cool-grey hover:text-destructive transition-colors"
                          >
                            Remove
                          </button>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {/* Volunteering Tab */}
        {activeTab === 'volunteering' && (
          <div className="space-y-4">
            {volunteerEntries.length === 0 ? (
              <CardPattern variant="subtle" className="text-center py-8">
                <p className="text-cool-grey mb-2">No volunteering saved yet</p>
                <p className="text-sm text-cool-grey">
                  Track your volunteer hours and opportunities here
                </p>
              </CardPattern>
            ) : (
              <div className="space-y-3">
                {volunteerEntries.map((entry) => {
                  const org = orgDataMap.get(entry.ein)
                  return (
                    <CardPattern key={entry.ein} variant="default" className="p-3">
                      <div className="text-sm">
                        <div className="font-semibold text-deep-navy">{org?.organization_name}</div>
                        <div className="text-xs text-cool-grey mt-1">
                          Interested • {org?.CITY}, {org?.STATE}
                        </div>
                      </div>
                    </CardPattern>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {/* Account Tab */}
        {activeTab === 'account' && (
          <div className="space-y-4 max-w-2xl">
            <WalletAccountLink />
            <CardPattern variant="subtle" className="p-4 space-y-2">
              <p className="text-sm text-cool-grey">
                <strong>Your wallet is private.</strong> Bookmarks and giving history stay on your device. Sign in to sync across devices.
              </p>
            </CardPattern>
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Quick donation logger — inline form for logging gifts.
 * Minimal friction: amount, date, optional note.
 */
function QuickDonationLogger({ onLog }: { onLog: (ein: string, amount: number, date: string, notes?: string) => void }) {
  const [expanded, setExpanded] = useState(false)
  const [amount, setAmount] = useState('')
  const [date, setDate] = useState(new Date().toISOString().split('T')[0])
  const [notes, setNotes] = useState('')

  if (!expanded) {
    return (
      <button
        onClick={() => setExpanded(true)}
        className="w-full py-2 px-4 bg-soft-gold text-deep-navy rounded font-medium text-sm hover:bg-gold transition-colors"
      >
        + Log a donation
      </button>
    )
  }

  return (
    <CardPattern variant="elevated" className="p-4 space-y-3">
      <div className="flex items-center justify-between mb-2">
        <span className="font-medium text-deep-navy text-sm">Log a donation</span>
        <button
          onClick={() => setExpanded(false)}
          className="text-cool-grey hover:text-deep-navy text-lg"
        >
          ×
        </button>
      </div>

      <div className="space-y-2">
        {/* Amount */}
        <div>
          <label className="block text-xs font-medium text-deep-navy mb-1">Amount</label>
          <input
            type="number"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="0"
            className="w-full px-3 py-2 border border-light-grey rounded text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/50"
          />
        </div>

        {/* Date */}
        <div>
          <label className="block text-xs font-medium text-deep-navy mb-1">Date</label>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="w-full px-3 py-2 border border-light-grey rounded text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/50"
          />
        </div>

        {/* Notes */}
        <div>
          <label className="block text-xs font-medium text-deep-navy mb-1">Notes (optional)</label>
          <input
            type="text"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="e.g., matched by employer"
            className="w-full px-3 py-2 border border-light-grey rounded text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/50"
          />
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={() => {
            if (amount) {
              // TODO: get current org from context or parameter
              onLog('', parseInt(amount), date, notes || undefined)
              setAmount('')
              setNotes('')
              setExpanded(false)
            }
          }}
          className="flex-1 py-2 bg-soft-gold text-deep-navy rounded font-medium text-sm hover:bg-gold transition-colors"
        >
          Log
        </button>
        <button
          onClick={() => setExpanded(false)}
          className="flex-1 py-2 bg-light-grey text-deep-navy rounded font-medium text-sm hover:bg-slate-200 transition-colors"
        >
          Cancel
        </button>
      </div>
    </CardPattern>
  )
}
