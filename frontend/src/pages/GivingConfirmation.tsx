import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import type { GivingListItem } from '../hooks/useGivingList'
import { formatCurrency } from '../data/organizations'
import { SPLIT_THRESHOLD } from '../hooks/useWallet'
import LampMark from '../components/LampMark'
import { TIER_COLORS } from '../components/TrustBadge'

interface ConfirmItem extends GivingListItem {
  referenceCode?: string
  splitCount?: number
}

function maskEmail(email: string): string {
  const [user, domain] = email.split('@')
  if (!domain || !user) return email
  return `${user[0]}***@${domain}`
}

const VERIFIED_FACTS: Record<string, string> = {
  Beacon:  'Organization-provided profile confirmed. Mission, giving path, and public filing all on record.',
  Lantern: 'Official giving path confirmed. Mission and public financial filing on record.',
  Flame:   'Public financial filing on record. Mission found in public data.',
  Glow:    'Confirmed active 501(c)(3) with public record on file.',
  Ember:   'Confirmed active 501(c)(3) with public record on file.',
  Spark:   'Registered 501(c)(3) in public records.',
}

export default function GivingConfirmation() {
  const [items, setItems] = useState<ConfirmItem[]>([])

  useEffect(() => {
    try {
      const stored = sessionStorage.getItem('merit_last_giving')
      if (stored) setItems(JSON.parse(stored))
    } catch { /* empty */ }
    window.scrollTo(0, 0)
  }, [])

  const total = items.reduce((s, i) => s + i.amount, 0)
  const hasLetterItems = items.some(i => i.referenceCode)

  if (items.length === 0) {
    return (
      <div className="min-h-screen bg-warm-cream pt-[72px] flex items-center justify-center">
        <div className="text-center">
          <p className="font-body text-[16px] text-cool-grey mb-4">No recent giving on record.</p>
          <Link to="/" className="font-body text-[14px] text-soft-gold hover:text-bright-gold transition-colors">Return home →</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-warm-cream">
      {/* Confirmation header */}
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-2xl mx-auto px-6 pt-12 pb-12 text-center">
          <div className="w-16 h-16 rounded-full bg-soft-gold/20 flex items-center justify-center mx-auto mb-6">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </div>
          <h1 className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(28px, 5vw, 48px)' }}>
            Your giving reached<br />{items.length} organization{items.length !== 1 ? 's' : ''}
          </h1>
          <p className="mt-4 font-body text-[15px] text-muted-cream max-w-[480px] mx-auto leading-[1.6]">
            {hasLetterItems
              ? 'Your gifts have been logged. Letter-requested donations are pending nonprofit acknowledgment.'
              : 'Each gift has been logged to your wallet. Complete your giving directly with each organization below.'
            }
          </p>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-6 py-8 pb-32 md:pb-12 space-y-4">
        {/* Per-org cards */}
        {items.map(item => {
          const isLetterItem = !!item.referenceCode
          const isSplitItem = !item.referenceCode && item.letterRequested === false && item.amount > SPLIT_THRESHOLD
          const splitCount = item.splitCount ?? Math.ceil(item.amount / SPLIT_THRESHOLD)

          return (
            <div key={item.ein} className="bg-white border border-light-grey rounded-xl p-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <p className="font-display text-[18px] text-deep-navy mb-1">{item.orgName}</p>
                  <div className="flex items-center gap-1.5 mb-2">
                    <LampMark tier={item.trustTier} size="xs" />
                    <span className="font-body text-[12px] font-medium" style={{ color: TIER_COLORS[item.trustTier] }}>{item.trustTier}</span>
                    <span className="font-body text-[11px] text-cool-grey">· EIN {item.ein}</span>
                  </div>
                  <p className="font-body text-[12px] text-cool-grey/70 italic leading-[1.5]">
                    "{VERIFIED_FACTS[item.trustTier] || VERIFIED_FACTS['Spark']}"
                  </p>
                </div>
                <p className="font-display text-[20px] text-deep-navy shrink-0">{formatCurrency(item.amount)}</p>
              </div>

              {/* Letter path: reference code */}
              {isLetterItem && (
                <div className="mt-4 bg-warm-cream rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
                    </svg>
                    <span className="font-body text-[11px] font-semibold text-cool-grey uppercase tracking-[0.06em]">Reference code</span>
                  </div>
                  <p className="font-display text-[22px] text-soft-gold tracking-[0.06em] mb-2">
                    {item.referenceCode}
                  </p>
                  <p className="font-body text-[12px] text-cool-grey leading-[1.5]">
                    {item.orgName} will receive your name
                    {item.donorName ? ` (${item.donorName})` : ''} and this code.
                    Once they upload your letter, Daanaa emails it to{' '}
                    <span className="font-medium text-deep-navy">
                      {item.donorEmail ? maskEmail(item.donorEmail) : 'you'}
                    </span>
                    {' '}and stores it in your wallet.
                  </p>
                </div>
              )}

              {/* Anonymous split note */}
              {isSplitItem && (
                <p className="mt-3 font-body text-[12px] text-cool-grey/60">
                  Logged as {splitCount} entries of {formatCurrency(SPLIT_THRESHOLD)}, each covered by your bank statement.
                </p>
              )}

              <a
                href={`https://www.google.com/search?q=${encodeURIComponent(item.orgName + ' donate')}`}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-4 flex items-center gap-2 font-body text-[12px] text-soft-gold hover:text-bright-gold transition-colors"
              >
                Complete your gift to {item.orgName} →
              </a>
            </div>
          )
        })}

        {/* Total */}
        <div className="bg-deep-navy rounded-xl p-6">
          <div className="flex items-center justify-between mb-3">
            <span className="font-body text-[14px] text-muted-cream">Total logged</span>
            <span className="font-display text-[28px] text-warm-cream">{formatCurrency(total)}</span>
          </div>
          <p className="font-body text-[12px] text-muted-cream/50">
            {hasLetterItems
              ? 'Letter-requested entries are pending acknowledgment · All others covered by bank statement'
              : 'Entries under $250 each · Bank statement is your documentation'
            } · Logged to your wallet
          </p>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3">
          <Link
            to="/"
            className="flex-1 text-center bg-soft-gold text-deep-navy font-body text-[14px] font-semibold py-3 rounded-full hover:bg-bright-gold transition-colors"
          >
            Return home
          </Link>
          <Link
            to="/wallet"
            className="flex-1 text-center border border-deep-navy/20 text-deep-navy font-body text-[14px] py-3 rounded-full hover:bg-deep-navy/5 transition-colors"
          >
            View wallet history
          </Link>
        </div>

        <p className="text-center font-body text-[12px] text-cool-grey/50 pt-2">
          Every verified gift is a civic act. Thank you for giving with intention.
        </p>
      </div>
    </div>
  )
}
