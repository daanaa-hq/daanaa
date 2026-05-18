import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useGivingList } from '../hooks/useGivingList'
import { useWallet } from '../hooks/useWallet'
import { formatCurrency } from '../data/organizations'
import { SPLIT_THRESHOLD, generateReferenceCode } from '../hooks/useWallet'
import type { DonationRecord } from '../hooks/useWallet'
import LampMark from '../components/LampMark'
import { TIER_COLORS } from '../components/TrustBadge'

export default function GivingReview() {
  const { items, total, count, clearList, updateAmount } = useGivingList()
  const { addDonationDirect } = useWallet()
  const navigate = useNavigate()
  const [submitting, setSubmitting] = useState(false)
  const [editing, setEditing] = useState<{ ein: string; value: string } | null>(null)

  if (count === 0) {
    return (
      <div className="min-h-screen bg-warm-cream pt-[72px] flex items-center justify-center">
        <div className="text-center">
          <p className="font-body text-[16px] text-cool-grey mb-4">Nothing to review.</p>
          <Link to="/directory" className="font-body text-[14px] text-soft-gold hover:text-bright-gold transition-colors">
            Browse organizations →
          </Link>
        </div>
      </div>
    )
  }

  const invalidItems = items.filter(i => !i.amount || i.amount <= 0)
  const hasLetterItems = items.some(i => i.letterRequested === true && i.amount >= SPLIT_THRESHOLD)
  const hasSplitItems = items.some(i => i.letterRequested === false && i.amount > SPLIT_THRESHOLD)

  async function handleGive() {
    if (invalidItems.length > 0) return
    setSubmitting(true)

    const today = new Date().toISOString().split('T')[0]
    const records: Omit<DonationRecord, 'id' | 'loggedAt'>[] = []
    const refCodeMap: Record<string, string> = {}
    const splitCountMap: Record<string, number> = {}

    for (const item of items.filter(i => i.amount > 0)) {
      if (item.letterRequested === true && item.amount >= SPLIT_THRESHOLD) {
        // Single record — full amount, pending acknowledgment, with reference code
        const referenceCode = generateReferenceCode()
        refCodeMap[item.ein] = referenceCode
        records.push({
          ein: item.ein,
          orgName: item.orgName,
          amount: item.amount,
          date: today,
          status: 'pending_acknowledgment',
          letterRequested: true,
          referenceCode,
          donorName: item.donorName,
          donorEmail: item.donorEmail,
          note: referenceCode,
        })
      } else if (item.letterRequested === false && item.amount > SPLIT_THRESHOLD) {
        // Anonymous split: N × $249.99 + remainder
        const fullChunks = Math.floor(item.amount / SPLIT_THRESHOLD)
        const remainder = parseFloat((item.amount - fullChunks * SPLIT_THRESHOLD).toFixed(2))
        const totalEntries = fullChunks + (remainder > 0 ? 1 : 0)
        splitCountMap[item.ein] = totalEntries
        for (let k = 0; k < fullChunks; k++) {
          records.push({
            ein: item.ein,
            orgName: item.orgName,
            amount: SPLIT_THRESHOLD,
            date: today,
            status: 'self_documented',
            letterRequested: false,
          })
        }
        if (remainder > 0) {
          records.push({
            ein: item.ein,
            orgName: item.orgName,
            amount: remainder,
            date: today,
            status: 'self_documented',
            letterRequested: false,
          })
        }
      } else {
        // Normal sub-$250 path
        records.push({
          ein: item.ein,
          orgName: item.orgName,
          amount: item.amount,
          date: today,
          status: 'self_documented',
          letterRequested: false,
        })
      }
    }

    addDonationDirect(records)

    // Enrich items with reference codes / split counts for confirmation screen
    const enriched = items.map(item => ({
      ...item,
      referenceCode: refCodeMap[item.ein],
      splitCount: splitCountMap[item.ein],
    }))
    sessionStorage.setItem('merit_last_giving', JSON.stringify(enriched))
    clearList()
    navigate('/giving-list/confirmation')
  }

  return (
    <div className="min-h-screen bg-warm-cream">
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-2xl mx-auto px-6 pt-8 pb-10">
          <Link to="/giving-list" className="flex items-center gap-1.5 font-body text-[12px] text-muted-cream/60 hover:text-muted-cream mb-4 transition-colors">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6"/></svg>
            Back to list
          </Link>
          <h1 className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(26px, 4vw, 40px)' }}>
            Review before giving
          </h1>
          <p className="mt-2 font-body text-[14px] text-muted-cream">
            Confirm each organization and amount below.
          </p>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-6 py-8 pb-32 md:pb-10 space-y-4">

        {/* Org rows */}
        {items.map(item => {
          const isLetterItem = item.letterRequested === true && item.amount >= SPLIT_THRESHOLD
          const isSplitItem = item.letterRequested === false && item.amount > SPLIT_THRESHOLD
          const fullChunks = isSplitItem ? Math.floor(item.amount / SPLIT_THRESHOLD) : 0
          const splitRemainder = isSplitItem ? parseFloat((item.amount - fullChunks * SPLIT_THRESHOLD).toFixed(2)) : 0
          const splitCount = isSplitItem ? fullChunks + (splitRemainder > 0 ? 1 : 0) : 0

          return (
            <div key={item.ein} className="bg-white border border-light-grey rounded-xl p-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <p className="font-display text-[17px] text-deep-navy mb-1">{item.orgName}</p>
                  <div className="flex items-center gap-1.5 mb-1">
                    <LampMark tier={item.trustTier} size="xs" />
                    <span className="font-body text-[12px] font-medium" style={{ color: TIER_COLORS[item.trustTier] }}>{item.trustTier}</span>
                    <span className="font-body text-[12px] text-cool-grey/70">· {item.trustSummary}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#4ADE80" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                    <span className="font-body text-[11px] text-cool-grey/60">IRS verified · EIN {item.ein}</span>
                  </div>

                  {/* Letter badge */}
                  {isLetterItem && (
                    <div className="mt-2.5 flex items-center gap-2">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-soft-gold/10 border border-soft-gold/30 font-body text-[11px] text-soft-gold font-medium">
                        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
                        </svg>
                        Letter requested
                      </span>
                      {item.donorName && (
                        <span className="font-body text-[11px] text-cool-grey/60">Dear {item.donorName}</span>
                      )}
                    </div>
                  )}

                  {/* Split note */}
                  {isSplitItem && (
                    <p className="mt-2 font-body text-[11px] text-cool-grey/60">
                      Will be logged as {splitCount} {splitCount === 1 ? 'entry' : 'entries'}{' '}
                      {fullChunks > 0 && splitRemainder > 0
                        ? `(${fullChunks} × ${formatCurrency(SPLIT_THRESHOLD)} + ${formatCurrency(splitRemainder)})`
                        : `of ${formatCurrency(SPLIT_THRESHOLD)}`
                      }
                    </p>
                  )}
                </div>
                <div className="text-right shrink-0">
                  {editing?.ein === item.ein ? (
                    <div className="flex items-center gap-2">
                      <span className="font-body text-[15px] text-cool-grey">$</span>
                      <input
                        autoFocus
                        type="number"
                        min="1"
                        step="1"
                        value={editing.value}
                        onChange={e => setEditing({ ein: item.ein, value: e.target.value })}
                        onKeyDown={e => {
                          if (e.key === 'Enter') {
                            const n = parseFloat(editing.value)
                            if (n > 0) { updateAmount(item.ein, n); setEditing(null) }
                          }
                          if (e.key === 'Escape') setEditing(null)
                        }}
                        className="w-24 border-b border-soft-gold bg-transparent font-display text-[20px] text-deep-navy text-right outline-none"
                        placeholder="0"
                      />
                      <button
                        onClick={() => {
                          const n = parseFloat(editing.value)
                          if (n > 0) { updateAmount(item.ein, n); setEditing(null) }
                        }}
                        className="font-body text-[12px] text-soft-gold hover:text-bright-gold transition-colors"
                      >
                        Done
                      </button>
                    </div>
                  ) : item.amount > 0 ? (
                    <button
                      onClick={() => setEditing({ ein: item.ein, value: String(item.amount) })}
                      className="font-display text-[20px] text-deep-navy hover:text-soft-gold transition-colors"
                    >
                      {formatCurrency(item.amount)}
                    </button>
                  ) : (
                    <button
                      onClick={() => setEditing({ ein: item.ein, value: '' })}
                      className="font-body text-[13px] text-alert-amber hover:text-soft-gold transition-colors"
                    >
                      Enter amount
                    </button>
                  )}
                </div>
              </div>
            </div>
          )
        })}

        {/* Total block */}
        <div className="bg-deep-navy rounded-xl p-6 space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-body text-[14px] text-muted-cream">{count} organization{count !== 1 ? 's' : ''}</span>
            <span className="font-display text-[28px] text-warm-cream">{formatCurrency(total)}</span>
          </div>
          <div className="border-t border-white/10 pt-3">
            <p className="font-body text-[12px] text-muted-cream/60">
              {hasLetterItems
                ? 'Letter-requested gifts will be documented once the nonprofit uploads to MERIT. '
                : ''}
              {hasSplitItems
                ? 'Gifts over $249.99 without a letter will be logged as multiple bank-statement entries. '
                : ''}
              {!hasLetterItems && !hasSplitItems
                ? 'Each contribution is under $250. '
                : ''}
              MERIT does not process payments or issue tax acknowledgments.
            </p>
          </div>

          {invalidItems.length > 0 && (
            <p className="font-body text-[12px] text-alert-amber">
              Please enter an amount for all organizations before continuing.
            </p>
          )}

          <button
            onClick={handleGive}
            disabled={submitting || invalidItems.length > 0 || total === 0}
            className="w-full bg-soft-gold text-deep-navy font-body text-[15px] font-semibold py-4 rounded-full hover:bg-bright-gold transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {submitting ? 'Logging...' : `Confirm ${formatCurrency(total)}`}
          </button>

          <p className="font-body text-[11px] text-muted-cream/40 text-center">
            This logs your intent. Complete each gift directly with the organization.
          </p>
        </div>

        <Link to="/giving-list" className="block text-center font-body text-[13px] text-cool-grey hover:text-deep-navy transition-colors">
          ← Edit list
        </Link>
      </div>
    </div>
  )
}
