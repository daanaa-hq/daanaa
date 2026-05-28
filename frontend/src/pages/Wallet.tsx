import React, { useState, useRef, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useSavedOrgs } from '../hooks/useSavedOrgs'
import { useWallet, SPLIT_THRESHOLD } from '../hooks/useWallet'
import { formatCurrency, formatEIN } from '../data/organizations'
import { getOrganizations } from '../data/api'
import type { ApiOrganization } from '../data/api'
import type { DonationRecord } from '../hooks/useWallet'

const IRS_THRESHOLD = 250

// ── shared components ─────────────────────────────────────────────────────────

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-white border border-light-grey rounded-xl p-5">
      <p className="font-body text-[11px] text-cool-grey uppercase tracking-[0.08em] mb-1">{label}</p>
      <p className="font-display text-[26px] text-deep-navy leading-none">{value}</p>
      {sub && <p className="font-body text-[11px] text-cool-grey mt-1">{sub}</p>}
    </div>
  )
}

function SectionHeader({ title, count }: { title: string; count?: number }) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <h2 className="font-display text-[18px] text-deep-navy">{title}</h2>
      {count !== undefined && (
        <span className="px-2 py-0.5 rounded-full bg-navy-mid/10 font-body text-[11px] text-deep-navy font-medium">
          {count}
        </span>
      )}
    </div>
  )
}

function EmptyState({ icon, message }: { icon: React.ReactNode; message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-10 text-cool-grey/50">
      <div className="mb-3">{icon}</div>
      <p className="font-body text-[13px]">{message}</p>
    </div>
  )
}

// ── donation log form ─────────────────────────────────────────────────────────

function DonationForm({ onSubmit, onCancel, prefillEin, prefillOrg }: {
  onSubmit: (r: Omit<DonationRecord, 'id' | 'loggedAt'>) => void
  onCancel: () => void
  prefillEin?: string
  prefillOrg?: string
}) {
  const today = new Date().toISOString().split('T')[0]
  const [orgName, setOrgName] = useState(prefillOrg ?? '')
  const [ein, setEin] = useState(prefillEin ?? '')
  const [amount, setAmount] = useState('')
  const [date, setDate] = useState(today)
  const [hasLetter, setHasLetter] = useState(false)
  const [occurrences, setOccurrences] = useState(1)
  const [suggestions, setSuggestions] = useState<ApiOrganization[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const wrapperRef = useRef<HTMLDivElement>(null)
  const amountRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (prefillOrg && amountRef.current) amountRef.current.focus()
  }, [prefillOrg])

  const parsedAmount = Math.round(parseFloat(amount) || 0)
  const needsAcknowledgment = parsedAmount >= IRS_THRESHOLD

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  function handleOrgNameChange(val: string) {
    setOrgName(val)
    setEin('')
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (val.length < 2) { setSuggestions([]); setShowSuggestions(false); return }
    debounceRef.current = setTimeout(async () => {
      try {
        const data = await getOrganizations({ q: val, per_page: 6 })
        setSuggestions(data.organizations || [])
        setShowSuggestions(true)
      } catch { /* silent */ }
    }, 280)
  }

  function selectOrg(org: ApiOrganization) {
    setOrgName(org.organization_name)
    setEin(org.EIN)
    setSuggestions([])
    setShowSuggestions(false)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!orgName.trim() || !parsedAmount || !date) return
    const status: 'acknowledged' | 'self_documented' = needsAcknowledgment && hasLetter ? 'acknowledged' : 'self_documented'
    const record = {
      ein: ein || orgName.trim(),
      orgName: orgName.trim(),
      amount: parsedAmount,
      date,
      status,
      letterRequested: needsAcknowledgment ? hasLetter : false,
    }
    for (let i = 0; i < occurrences; i++) onSubmit(record)
    onCancel()
  }

  return (
    <form onSubmit={handleSubmit} className="bg-warm-cream/40 border border-soft-gold/20 rounded-xl p-5 space-y-3">
      <div className="grid grid-cols-2 gap-3">

        {/* Org name with autocomplete */}
        <div className="col-span-2 relative" ref={wrapperRef}>
          <label className="block font-body text-[12px] text-cool-grey mb-1">Organization <span className="text-soft-gold">*</span></label>
          <div className="relative">
            <input
              value={orgName}
              onChange={e => handleOrgNameChange(e.target.value)}
              required
              placeholder="Search by name…"
              autoComplete="off"
              className="w-full border border-light-grey rounded-lg px-3 py-2 font-body text-[14px] text-deep-navy bg-white outline-none focus:border-soft-gold transition-colors"
            />
            {ein && (
              <span className="absolute right-3 top-1/2 -translate-y-1/2 font-body text-[11px] text-cool-grey/50 select-none pointer-events-none">
                EIN {formatEIN(ein)}
              </span>
            )}
          </div>
          {showSuggestions && suggestions.length > 0 && (
            <div className="absolute z-20 left-0 right-0 mt-1 bg-white border border-light-grey rounded-xl shadow-card overflow-hidden">
              {suggestions.map(org => (
                <button
                  key={org.EIN}
                  type="button"
                  onMouseDown={() => selectOrg(org)}
                  className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-warm-cream/60 transition-colors text-left"
                >
                  <div className="min-w-0">
                    <p className="font-body text-[13px] text-deep-navy font-medium truncate">{org.organization_name}</p>
                    <p className="font-body text-[11px] text-cool-grey">{[org.CITY, org.STATE].filter(Boolean).join(', ')}</p>
                  </div>
                  <span className="ml-3 shrink-0 font-body text-[10px] text-cool-grey/50">{formatEIN(org.EIN)}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Amount */}
        <div>
          <label className="block font-body text-[12px] text-cool-grey mb-1">Amount ($) <span className="text-soft-gold">*</span></label>
          <input
            ref={amountRef}
            value={amount}
            onChange={e => setAmount(e.target.value)}
            required
            type="number"
            min="1"
            step="1"
            placeholder="0"
            className="w-full border border-light-grey rounded-lg px-3 py-2 font-body text-[14px] text-deep-navy bg-white outline-none focus:border-soft-gold transition-colors"
          />
        </div>

        {/* Date */}
        <div>
          <label className="block font-body text-[12px] text-cool-grey mb-1">Date <span className="text-soft-gold">*</span></label>
          <input
            value={date}
            onChange={e => setDate(e.target.value)}
            required
            type="date"
            className="w-full border border-light-grey rounded-lg px-3 py-2 font-body text-[14px] text-deep-navy bg-white outline-none focus:border-soft-gold transition-colors"
          />
        </div>

      </div>

      {/* Occurrences stepper */}
      <div className="flex items-center gap-3">
        <label className="font-body text-[12px] text-cool-grey">Times donated</label>
        <div className="flex items-center gap-2">
          <button type="button" onClick={() => setOccurrences(n => Math.max(1, n - 1))}
            className="w-7 h-7 flex items-center justify-center rounded-full border border-light-grey text-cool-grey hover:border-soft-gold/50 transition-colors font-body text-[16px] leading-none">
            −
          </button>
          <span className="font-body text-[15px] text-deep-navy font-medium w-5 text-center">{occurrences}</span>
          <button type="button" onClick={() => setOccurrences(n => n + 1)}
            className="w-7 h-7 flex items-center justify-center rounded-full border border-light-grey text-cool-grey hover:border-soft-gold/50 transition-colors font-body text-[16px] leading-none">
            +
          </button>
        </div>
        {occurrences > 1 && (
          <span className="font-body text-[12px] text-cool-grey/60">
            will log {occurrences} × {amount ? `$${amount}` : '…'}
          </span>
        )}
      </div>

      {/* $250+ acknowledgment notice */}
      {needsAcknowledgment && (
        <div className="rounded-lg bg-soft-gold/5 border border-soft-gold/20 px-4 py-3 space-y-2.5">
          <p className="font-body text-[12px] text-cool-grey leading-relaxed">
            Gifts of $250 or more require a written acknowledgment from the organization to claim a charitable deduction.{' '}
            <a
              href="https://www.irs.gov/pub/irs-pdf/p1771.pdf"
              target="_blank"
              rel="noopener noreferrer"
              className="text-soft-gold hover:text-bright-gold underline underline-offset-2"
            >
              IRS Publication 1771
            </a>
          </p>
          <label className="flex items-center gap-2.5 cursor-pointer">
            <input
              type="checkbox"
              checked={hasLetter}
              onChange={e => setHasLetter(e.target.checked)}
              className="w-4 h-4 rounded accent-soft-gold cursor-pointer"
            />
            <span className="font-body text-[13px] text-deep-navy">I have a written acknowledgment letter for this gift</span>
          </label>
        </div>
      )}

      <div className="flex gap-2 pt-1">
        <button type="submit" className="px-5 py-2 rounded-lg bg-soft-gold text-deep-navy font-body text-[13px] font-semibold hover:bg-bright-gold transition-colors">Save</button>
        <button type="button" onClick={onCancel} className="px-5 py-2 rounded-lg border border-light-grey text-cool-grey font-body text-[13px] hover:border-soft-gold/40 transition-colors">Cancel</button>
      </div>
    </form>
  )
}

// ── main page ─────────────────────────────────────────────────────────────────

export default function Wallet() {
  const [showDonationForm, setShowDonationForm] = useState(false)
  const [searchParams, setSearchParams] = useSearchParams()
  const prefillEin = searchParams.get('ein') ?? undefined
  const prefillOrg = searchParams.get('org') ?? undefined

  useEffect(() => {
    if (prefillEin) setShowDonationForm(true)
  }, [prefillEin])

  const { savedOrgs, toggle } = useSavedOrgs()
  const { donations, addDonationDirect, markAcknowledged, removeDonation, totalDonated, totalDonatedThisYear, uniqueEins, pendingLetters } = useWallet()
  const orgsSupported = new Set([...Array.from(uniqueEins), ...savedOrgs.map(o => o.ein)]).size

  const thisYear = new Date().getFullYear()
  const [selectedYear, setSelectedYear] = useState(thisYear)

  const years = Array.from(new Set(donations.map(d => parseInt(d.date.slice(0, 4))))).sort((a, b) => b - a)
  if (!years.includes(thisYear)) years.unshift(thisYear)

  const visibleDonations = donations.filter(d => d.date.startsWith(String(selectedYear)))

  function exportCSV() {
    const rows = [
      ['Date', 'Organization', 'EIN', 'Amount', 'Status', 'Reference'],
      ...visibleDonations.map(d => [
        d.date,
        `"${d.orgName.replace(/"/g, '""')}"`,
        d.ein,
        d.amount.toFixed(2),
        d.status,
        d.referenceCode || '',
      ]),
    ]
    const csv = rows.map(r => r.join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `merit-giving-${selectedYear}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="min-h-screen bg-warm-cream">
      {/* Dark header — matches Directory / OrganizationDetail */}
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-3xl mx-auto px-6 pt-10 pb-12">
          <div className="flex items-center gap-2 mb-3">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#A89F94" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
            <span className="font-body text-[12px] text-muted-cream/60 tracking-[0.04em]">Private · stored on this device · never shared</span>
          </div>
          <h1 className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(32px, 5vw, 56px)' }}>
            Your Giving Wallet
          </h1>
          <p className="mt-3 font-body text-[14px] text-muted-cream">
            Your complete giving record. Gifts under $250 are self-documented. Letters are required for gifts of $250+ if you itemize.
          </p>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-6 py-10">

        <div className="space-y-10">

          {/* Summary stats */}
          <div className="grid grid-cols-3 gap-4">
            <StatCard label="Given all-time" value={formatCurrency(totalDonated)} />
            <StatCard label={`Given in ${thisYear}`} value={formatCurrency(totalDonatedThisYear)} />
            <StatCard label="Orgs supported" value={String(orgsSupported)} sub="donated + saved" />
          </div>

          {/* Favorites */}
          <div>
            <SectionHeader title="Favorites" count={savedOrgs.length} />
            {savedOrgs.length === 0 ? (
              <EmptyState
                icon={<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>}
                message="Star organizations from the directory, or give to one — they'll appear here automatically"
              />
            ) : (
              <div className="space-y-2">
                {savedOrgs.map(org => (
                  <div key={org.ein} className="flex items-center justify-between bg-white border border-light-grey rounded-xl px-5 py-4 hover:border-soft-gold/40 transition-colors group">
                    <Link to={`/org/${org.ein}`} className="flex-1 min-w-0">
                      <p className="font-body text-[15px] font-medium text-deep-navy group-hover:text-soft-gold transition-colors truncate">{org.name}</p>
                      {(org.city || org.state) && (
                        <p className="font-body text-[12px] text-cool-grey mt-0.5">{[org.city, org.state].filter(Boolean).join(', ')}</p>
                      )}
                    </Link>
                    <button onClick={() => toggle(org.ein)} title="Remove from saved"
                      className="ml-4 p-1.5 rounded-full text-cool-grey/40 hover:text-cool-grey hover:bg-light-grey/40 transition-colors flex-shrink-0">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Pending letters callout */}
          {pendingLetters.length > 0 && (
            <div className="bg-soft-gold/5 border border-soft-gold/20 rounded-xl px-5 py-4">
              <div className="flex items-start gap-3">
                <svg className="shrink-0 mt-0.5" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
                </svg>
                <div>
                  <p className="font-display text-[15px] text-deep-navy mb-1">
                    {pendingLetters.length} acknowledgment letter{pendingLetters.length !== 1 ? 's' : ''} pending
                  </p>
                  <p className="font-body text-[12px] text-cool-grey leading-relaxed">
                    Once each nonprofit uploads your letter to Daanaa, it will be emailed to you and marked received here.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Donation log */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <SectionHeader title="Donation Log" count={visibleDonations.length} />
              {!showDonationForm && (
                <button onClick={() => setShowDonationForm(true)}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg border border-soft-gold/40 text-soft-gold font-body text-[13px] font-medium hover:bg-soft-gold/5 transition-colors">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                  Log a donation
                </button>
              )}
            </div>

            {/* Year filter + export row */}
            {donations.length > 0 && (
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-1.5">
                  {years.map(y => (
                    <button
                      key={y}
                      onClick={() => setSelectedYear(y)}
                      className="px-3 py-1 rounded-full font-body text-[12px] font-medium transition-all"
                      style={{
                        background: selectedYear === y ? '#C9A96E' : 'transparent',
                        color: selectedYear === y ? '#0A1628' : '#6B7280',
                        border: selectedYear === y ? 'none' : '1px solid #E5E0DB',
                      }}
                    >
                      {y}
                    </button>
                  ))}
                </div>
                <button onClick={exportCSV}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-light-grey text-cool-grey font-body text-[12px] hover:border-soft-gold/40 hover:text-soft-gold transition-colors">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                  Export {selectedYear}
                </button>
              </div>
            )}

            {/* Year total + deductibility note */}
            {visibleDonations.length > 0 && (
              <div className="flex items-baseline justify-between mb-3">
                <p className="font-body text-[11px] text-cool-grey/60">
                  Deductible if you itemize · gifts under $250 documented by bank statement
                </p>
                <span className="font-display text-[15px] text-deep-navy shrink-0 ml-4">
                  {formatCurrency(visibleDonations.reduce((s, d) => s + d.amount, 0))} in {selectedYear}
                </span>
              </div>
            )}

            {showDonationForm && (
              <div className="mb-4">
                <DonationForm
                  onSubmit={r => addDonationDirect([r])}
                  onCancel={() => { setShowDonationForm(false); if (prefillEin || prefillOrg) setSearchParams({}) }}
                  prefillEin={prefillEin}
                  prefillOrg={prefillOrg}
                />
              </div>
            )}

            {donations.length === 0 && !showDonationForm ? (
              <EmptyState
                icon={<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z"/><path d="M12 6v6l4 2"/></svg>}
                message="Log donations made through any channel. Your record, your history."
              />
            ) : (
              <div className="space-y-2">
                {visibleDonations.map(d => (
                  <div key={d.id} className="flex items-center justify-between bg-white border border-light-grey rounded-xl px-5 py-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 flex-wrap">
                        <span className="font-display text-[17px] text-soft-gold">{formatCurrency(d.amount)}</span>
                        <span className="font-body text-[14px] text-deep-navy truncate">{d.orgName}</span>
                      </div>
                      <span className="font-body text-[12px] text-cool-grey">
                        {new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </span>
                      {/* Letter status — Daanaa-mediated (Giving List flow, has referenceCode) */}
                      {d.referenceCode && (
                        <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                          {d.status === 'pending_acknowledgment' && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-soft-gold/10 border border-soft-gold/20 font-body text-[10px] text-soft-gold font-medium">
                              <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                <rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
                              </svg>
                              Letter pending
                            </span>
                          )}
                          {d.status === 'acknowledged' && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-success-green/10 border border-success-green/20 font-body text-[10px] font-medium" style={{ color: '#4ADE80' }}>
                              <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                              Letter received
                            </span>
                          )}
                          <span className="font-body text-[10px] text-cool-grey/40 tracking-[0.04em]">{d.referenceCode}</span>
                        </div>
                      )}
                      {/* Acknowledgment status — manual log entries */}
                      {!d.referenceCode && d.status === 'acknowledged' && (
                        <div className="mt-1.5">
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-success-green/10 border border-success-green/20 font-body text-[10px] font-medium" style={{ color: '#4ADE80' }}>
                            <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                            Acknowledged (self-attested)
                          </span>
                        </div>
                      )}
                      {!d.referenceCode && d.status === 'self_documented' && d.amount >= IRS_THRESHOLD && (
                        <div className="mt-1.5 flex items-center gap-2">
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-alert-amber/10 border border-alert-amber/20 font-body text-[10px] text-alert-amber font-medium">
                            No acknowledgment on file
                          </span>
                          <button
                            onClick={() => markAcknowledged(d.id)}
                            className="font-body text-[10px] text-soft-gold hover:text-bright-gold underline underline-offset-2 transition-colors"
                          >
                            Mark acknowledged
                          </button>
                        </div>
                      )}
                    </div>
                    <button onClick={() => removeDonation(d.id)} title="Remove entry"
                      className="ml-4 p-1.5 rounded-full text-cool-grey/40 hover:text-cool-grey hover:bg-light-grey/40 transition-colors flex-shrink-0">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>

        {/* Footer */}
        <div className="mt-12 pt-6 border-t border-light-grey flex items-center gap-2 text-cool-grey/40">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="shrink-0"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
          <p className="font-body text-[11px]">Private by design · stored on this device · never shared · Daanaa does not process payments or issue tax documents · Letters for gifts of $250+ are delivered once the nonprofit uploads them to Daanaa</p>
        </div>

      </div>
    </div>
  )
}

