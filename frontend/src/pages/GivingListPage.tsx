import { useState, Fragment } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useGivingList } from '../hooks/useGivingList'
import { formatCurrency } from '../data/organizations'
import ScoreBreakdown from '../components/ScoreBreakdown'
import LampMark from '../components/LampMark'
import { TIER_COLORS } from '../components/TrustBadge'
import type { ApiOrganization } from '../data/api'
import { SPLIT_THRESHOLD } from '../hooks/useWallet'

// Minimal ApiOrganization stub for ScoreBreakdown from GivingListItem
function stubOrg(item: ReturnType<typeof useGivingList>['items'][0]): ApiOrganization {
  return {
    EIN: item.ein,
    organization_name: item.orgName,
    NTEE1: item.ntee1 || null,
    NTEECC: null,
    CITY: item.city || null,
    STATE: item.state || null,
    total_revenue: null,
    total_revenue_formatted: null,
    ntee1_percentile: null,
    ntee1_total_orgs: null,
    source: null,
    revenue_band: null,
    peer_percentile: null,
    peer_rank: null,
    peer_total: null,
    peer_group: null,
    latest_tax_year: null,
    data_source: null,
    updated_at: null,
    has_mission: null,
    has_website: null,
    months_of_reserve: null,
    net_assets: null,
    total_expenses: null,
    total_liabilities: null,
    employee_count: null,
    ruling_date: null,
    zipcode: null,
    address: null,
    activ1: null,
    activ2: null,
    activ3: null,
    program_expense_pct: null,
    nccs_year: null,
  }
}

function RadioDot({ active }: { active?: boolean }) {
  return (
    <div className={`mt-0.5 w-4 h-4 rounded-full border-2 flex items-center justify-center shrink-0 transition-colors ${
      active ? 'border-soft-gold' : 'border-light-grey bg-white'
    }`} style={{ backgroundColor: active ? '#C9A96E' : undefined }}>
      {active && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
    </div>
  )
}

export default function GivingListPage() {
  const { items, removeItem, updateAmount, updateLetterInfo, total, count, clearList } = useGivingList()
  const [expandedEin, setExpandedEin] = useState<string | null>(null)
  const navigate = useNavigate()

  // Ephemeral draft state for name/email inputs — synced to context on blur
  const [letterDraft, setLetterDraft] = useState<Record<string, { name: string; email: string }>>({})

  const getDraft = (ein: string) => letterDraft[ein] || { name: '', email: '' }

  const setDraft = (ein: string, field: 'name' | 'email', value: string) => {
    setLetterDraft(prev => ({ ...prev, [ein]: { ...getDraft(ein), [field]: value } }))
  }

  const syncLetterInfo = (ein: string, letterRequested: boolean) => {
    const draft = getDraft(ein)
    updateLetterInfo(ein, {
      letterRequested,
      donorName: letterRequested ? draft.name : undefined,
      donorEmail: letterRequested ? draft.email : undefined,
    })
  }

  // Validation
  const unresolvedItems = items.filter(i => i.amount >= SPLIT_THRESHOLD && i.letterRequested === undefined)
  const incompleteLetters = items.filter(i =>
    i.letterRequested === true && (!i.donorName?.trim() || !i.donorEmail?.trim())
  )
  const hasLetterItems = items.some(i => i.letterRequested === true)
  const canProceed = total > 0 && unresolvedItems.length === 0 && incompleteLetters.length === 0

  if (count === 0) {
    return (
      <div className="min-h-screen bg-warm-cream pt-[72px] pb-20 md:pb-0">
        <div className="max-w-2xl mx-auto px-6 pt-12 text-center">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#E5E0DB" strokeWidth="1.5" className="mx-auto mb-4">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
          </svg>
          <h1 className="font-display italic text-deep-navy text-[28px] mb-2">Your giving list is empty</h1>
          <p className="font-body text-[15px] text-cool-grey mb-6">
            Browse the directory and tap <strong>+ Add</strong> on any organization to build your list.
          </p>
          <Link
            to="/directory"
            className="inline-flex items-center gap-2 bg-soft-gold text-deep-navy font-body text-[14px] font-semibold px-8 py-3 rounded-full hover:bg-bright-gold transition-colors"
          >
            Browse Organizations
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="9 18 15 12 9 6"/></svg>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-warm-cream">
      {/* Dark header */}
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-2xl mx-auto px-6 pt-8 pb-10">
          <h1 className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(28px, 5vw, 44px)' }}>
            Giving List
          </h1>
          <div className="mt-2 flex items-baseline gap-3">
            <p className="font-body text-[14px] text-muted-cream">
              {(() => {
                const g = items.filter(i => i.status === 'given').length
                const o = count - g
                if (g && o) return `${o} ongoing · ${g} given`
                if (g) return `${g} given · your private record`
                return `${count} organization${count !== 1 ? 's' : ''} · Review before giving`
              })()}
            </p>
            <Link
              to="/directory"
              className="font-body text-[12px] text-soft-gold/80 hover:text-soft-gold transition-colors"
            >
              + Find more
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-6 py-8 pb-32 md:pb-10 space-y-4">
        {[...items]
          .sort((a, b) => (a.status === 'given' ? 1 : 0) - (b.status === 'given' ? 1 : 0))
          .map((item, idx, ordered) => {
          const isLarge = item.amount >= SPLIT_THRESHOLD
          const fullChunks = Math.floor(item.amount / SPLIT_THRESHOLD)
          const remainder = item.amount - fullChunks * SPLIT_THRESHOLD
          const splitCount = fullChunks + (remainder > 0 ? 1 : 0)
          const draft = getDraft(item.ein)
          const showGivenHeader = item.status === 'given' && (idx === 0 || ordered[idx - 1].status !== 'given')
          const showOngoingHeader = item.status !== 'given' && idx === 0 && ordered.some(o => o.status === 'given')

          return (
            <Fragment key={item.ein}>
            {showOngoingHeader && (
              <p className="font-body text-[11px] font-semibold tracking-[0.08em] uppercase text-cool-grey/60 pt-1">Ongoing · plan to give</p>
            )}
            {showGivenHeader && (
              <p className="font-body text-[11px] font-semibold tracking-[0.08em] uppercase text-soft-gold pt-3">Given · your private record</p>
            )}
            <div className="bg-white border border-light-grey rounded-xl overflow-hidden">
              <div className="p-5">
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex-1 min-w-0">
                    <Link
                      to={`/org/${item.ein}`}
                      className="font-display text-[17px] text-deep-navy font-medium truncate hover:text-soft-gold transition-colors block"
                    >
                      {item.orgName}
                    </Link>
                    {(item.city || item.state) && (
                      <p className="font-body text-[12px] text-cool-grey mt-0.5">{[item.city, item.state].filter(Boolean).join(', ')}</p>
                    )}
                  </div>
                  <button onClick={() => removeItem(item.ein)} className="p-1.5 rounded-full hover:bg-light-grey transition-colors shrink-0">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#A89F94" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  </button>
                </div>

                {/* Trust + score summary */}
                <div className="flex items-center gap-2 mb-3">
                  <LampMark tier={item.trustTier} size="xs" />
                  <span className="font-body text-[12px] font-medium" style={{ color: TIER_COLORS[item.trustTier] }}>{item.trustTier}</span>
                  <span className="font-body text-[11px] text-cool-grey/70">· {item.trustSummary}</span>
                </div>

                {/* Score breakdown toggle */}
                <button
                  onClick={() => setExpandedEin(expandedEin === item.ein ? null : item.ein)}
                  className="font-body text-[11px] text-soft-gold hover:text-bright-gold transition-colors mb-3"
                >
                  {expandedEin === item.ein ? 'Hide score breakdown ↑' : 'See score breakdown ↓'}
                </button>

                {/* Amount input */}
                <div className="flex items-center gap-3">
                  <span className="font-body text-[13px] text-cool-grey">Amount:</span>
                  <div className="flex items-center gap-2 flex-1">
                    <span className="font-body text-[14px] text-cool-grey">$</span>
                    <input
                      type="number"
                      min="1"
                      step="1"
                      value={item.amount || ''}
                      onChange={e => {
                        const v = Math.round(parseFloat(e.target.value))
                        if (!isNaN(v) && v > 0) {
                          updateAmount(item.ein, v)
                          if (v < SPLIT_THRESHOLD && item.letterRequested !== undefined) {
                            updateLetterInfo(item.ein, { letterRequested: false })
                          }
                        }
                      }}
                      placeholder="0"
                      className="w-32 border border-light-grey rounded-lg px-3 py-2 font-body text-[15px] text-deep-navy bg-white outline-none focus:border-soft-gold transition-colors"
                    />
                  </div>
                </div>

                {/* Letter / anonymous choice — shown when amount ≥ $250 */}
                {isLarge && (
                  <div className="mt-4 pt-4 border-t border-light-grey/60">
                    <p className="font-body text-[12px] text-cool-grey mb-3">
                      Gifts of $250+ require documentation if you itemize deductions:
                    </p>
                    <div className="space-y-2">

                      {/* Option A: Request letter */}
                      <button
                        onClick={() => {
                          updateLetterInfo(item.ein, {
                            letterRequested: true,
                            donorName: draft.name || undefined,
                            donorEmail: draft.email || undefined,
                          })
                        }}
                        className="w-full flex items-start gap-2.5 px-3 py-3 rounded-xl border transition-all text-left"
                        style={{
                          borderColor: item.letterRequested === true ? '#C9A96E' : '#E5E0DB',
                          backgroundColor: item.letterRequested === true ? 'rgba(201,169,110,0.05)' : 'transparent',
                        }}
                      >
                        <RadioDot active={item.letterRequested === true} />
                        <div>
                          <p className="font-body text-[13px] font-semibold text-deep-navy">Request acknowledgment letter</p>
                          <p className="font-body text-[11px] text-cool-grey/70 mt-0.5">Required for deducting gifts of $250+ if you itemize</p>
                        </div>
                      </button>

                      {/* Name + email fields (when letter selected) */}
                      {item.letterRequested === true && (
                        <div className="ml-6 space-y-2 pt-1 pb-1">
                          <input
                            type="text"
                            value={draft.name || item.donorName || ''}
                            onChange={e => setDraft(item.ein, 'name', e.target.value)}
                            onBlur={() => updateLetterInfo(item.ein, {
                              letterRequested: true,
                              donorName: draft.name || undefined,
                              donorEmail: item.donorEmail || undefined,
                            })}
                            placeholder="Your name (for the letter)"
                            className="w-full border border-light-grey rounded-lg px-3 py-2 font-body text-[13px] text-deep-navy bg-white outline-none focus:border-soft-gold transition-colors"
                          />
                          <div>
                            <input
                              type="email"
                              value={draft.email || item.donorEmail || ''}
                              onChange={e => setDraft(item.ein, 'email', e.target.value)}
                              onBlur={() => updateLetterInfo(item.ein, {
                                letterRequested: true,
                                donorName: item.donorName || undefined,
                                donorEmail: draft.email || undefined,
                              })}
                              placeholder="Email address"
                              className="w-full border border-light-grey rounded-lg px-3 py-2 font-body text-[13px] text-deep-navy bg-white outline-none focus:border-soft-gold transition-colors"
                            />
                            <p className="mt-1 font-body text-[10px] text-cool-grey/50">
                              Only used to deliver your letter, never shared with the nonprofit
                            </p>
                          </div>
                        </div>
                      )}

                      {/* Option B: Stay anonymous */}
                      <button
                        onClick={() => {
                          updateLetterInfo(item.ein, { letterRequested: false, donorName: undefined, donorEmail: undefined })
                          setLetterDraft(prev => ({ ...prev, [item.ein]: { name: '', email: '' } }))
                        }}
                        className="w-full flex items-start gap-2.5 px-3 py-3 rounded-xl border transition-all text-left"
                        style={{
                          borderColor: item.letterRequested === false ? '#C9A96E' : '#E5E0DB',
                          backgroundColor: item.letterRequested === false ? 'rgba(201,169,110,0.05)' : 'transparent',
                        }}
                      >
                        <RadioDot active={item.letterRequested === false} />
                        <div>
                          <p className="font-body text-[13px] font-semibold text-deep-navy">Stay anonymous</p>
                          <p className="font-body text-[11px] text-cool-grey/70 mt-0.5">Bank statement is your only documentation needed</p>
                        </div>
                      </button>

                      {/* Split explanation (anonymous path) */}
                      {item.letterRequested === false && (
                        <div className="ml-6 bg-warm-cream rounded-lg px-3 py-2">
                          <p className="font-body text-[11px] text-cool-grey leading-relaxed">
                            This gift will be logged as{' '}
                            <strong>{splitCount} {splitCount === 1 ? 'entry' : 'entries'}</strong>
                            {' '}
                            {fullChunks > 0 && remainder > 0
                              ? `(${fullChunks} × ${formatCurrency(SPLIT_THRESHOLD)} + ${formatCurrency(remainder)})`
                              : `of ${formatCurrency(SPLIT_THRESHOLD)}`
                            }
                            {' '}each covered by your bank statement.
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Inline ScoreBreakdown */}
              {expandedEin === item.ein && (
                <ScoreBreakdown
                  org={stubOrg(item)}
                  onClose={() => setExpandedEin(null)}
                  mode="inline"
                />
              )}
            </div>
            </Fragment>
          )
        })}

        {/* Total + CTA */}
        <div className="bg-white border border-light-grey rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <span className="font-body text-[14px] text-cool-grey">Total</span>
            <span className="font-display text-[24px] text-deep-navy">{formatCurrency(total)}</span>
          </div>
          <p className="font-body text-[12px] text-cool-grey/60">
            {hasLetterItems
              ? 'For gifts of $250 or more, contact the nonprofit to request a written acknowledgment letter. Smaller gifts are covered by your bank statement.'
              : 'Each contribution is under $250, so your bank statement is the only documentation the IRS requires.'
            }
          </p>

          {/* Validation hints */}
          {total === 0 && (
            <p className="font-body text-[12px] text-alert-amber">
              Enter an amount for at least one organization to continue.
            </p>
          )}
          {unresolvedItems.length > 0 && (
            <p className="font-body text-[12px] text-alert-amber">
              Choose "Request letter" or "Stay anonymous" for gifts of $250+.
            </p>
          )}
          {incompleteLetters.length > 0 && (
            <p className="font-body text-[12px] text-alert-amber">
              Add your name and email to request a letter.
            </p>
          )}

          <button
            onClick={() => navigate('/giving-list/review')}
            disabled={!canProceed}
            className="w-full bg-soft-gold text-deep-navy font-body text-[15px] font-semibold py-4 rounded-full hover:bg-bright-gold transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Review & Give →
          </button>
          <button
            onClick={() => { if (confirm('Clear your giving list?')) clearList() }}
            className="w-full font-body text-[13px] text-cool-grey/60 hover:text-cool-grey transition-colors"
          >
            Clear list
          </button>
        </div>
      </div>
    </div>
  )
}
