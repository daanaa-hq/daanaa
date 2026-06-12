import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useGivingList } from '../hooks/useGivingList'
import { formatCurrency } from '../data/organizations'
import LampMark from './LampMark'
import { TIER_COLORS } from './TrustBadge'

export default function GivingListDrawer() {
  const { items, removeItem, updateAmount, total, count } = useGivingList()
  const [open, setOpen] = useState(false)

  return (
    <>
      {/* Trigger button — shown in desktop nav */}
      <button
        onClick={() => setOpen(o => !o)}
        className="hidden md:inline-flex relative items-center gap-1.5 px-4 py-2 rounded-full font-body text-[13px] transition-all duration-150"
        style={{
          color: open ? '#2A6B45' : '#374151',
          background: open ? 'rgba(42,107,69,0.08)' : 'transparent',
          border: '1px solid',
          borderColor: open ? 'rgba(42,107,69,0.35)' : 'rgba(42,107,69,0.25)',
        }}
        aria-label="Open Giving List"
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill={count > 0 ? '#C0392B' : 'none'} stroke="#C0392B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
        </svg>
        Give
        {count > 0 && (
          <span className="min-w-[16px] h-[16px] flex items-center justify-center bg-prophetic-green text-white text-[10px] font-bold rounded-full px-1">
            {count}
          </span>
        )}
      </button>

      {/* Drawer */}
      {open && (
        <div className="fixed inset-0 z-50 flex justify-end pointer-events-none">
          {/* Backdrop */}
          <div
            className="absolute inset-0 pointer-events-auto"
            onClick={() => setOpen(false)}
          />
          {/* Panel */}
          <div
            className="relative pointer-events-auto w-[380px] h-full bg-white border-l border-light-grey shadow-card-hover flex flex-col"
            style={{ animation: 'slideInRight 0.2s ease-out' }}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-light-grey shrink-0">
              <div>
                <h2 className="font-display text-[18px] text-deep-navy">Giving List</h2>
                {count > 0 && (
                  <p className="font-body text-[12px] text-cool-grey">{count} organization{count !== 1 ? 's' : ''}</p>
                )}
              </div>
              <button onClick={() => setOpen(false)} className="p-1.5 rounded-full hover:bg-light-grey transition-colors">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6B7280" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>

            {/* Items */}
            <div className="flex-1 overflow-y-auto">
              {count === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
                  <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#E5E0DB" strokeWidth="1.5" className="mb-4">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                  </svg>
                  <p className="font-body text-[14px] text-cool-grey mb-1">Your Wallet is empty</p>
                  <p className="font-body text-[12px] text-cool-grey">Tap <strong>Save to Wallet</strong> on any organization to get started</p>
                  <Link
                    to="/directory"
                    onClick={() => setOpen(false)}
                    className="mt-5 font-body text-[13px] text-soft-gold hover:text-bright-gold transition-colors"
                  >
                    Browse organizations →
                  </Link>
                </div>
              ) : (
                <div className="divide-y divide-light-grey/60">
                  {items.map(item => (
                    <div key={item.ein} className="px-5 py-4">
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <div className="flex-1 min-w-0">
                          <p className="font-body text-[14px] font-medium text-deep-navy truncate">{item.orgName}</p>
                          <div className="flex items-center gap-1.5 mt-0.5">
                            <LampMark tier={item.trustTier} size="xs" />
                            <span className="font-body text-[11px] font-medium" style={{ color: TIER_COLORS[item.trustTier] }}>{item.trustTier}</span>
                          </div>
                          {item.trustSummary && (
                            <p className="font-body text-[11px] text-cool-grey mt-1 leading-[1.4]">{item.trustSummary}</p>
                          )}
                        </div>
                        <button
                          onClick={() => removeItem(item.ein)}
                          className="p-1 rounded-full hover:bg-light-grey transition-colors shrink-0"
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#A89F94" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                        </button>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-body text-[12px] text-cool-grey shrink-0">$</span>
                        <input
                          type="number"
                          min="1"
                          step="1"
                          value={item.amount || ''}
                          onChange={e => {
                            const v = parseFloat(e.target.value)
                            if (!isNaN(v) && v > 0) updateAmount(item.ein, v)
                          }}
                          placeholder="Amount"
                          className="flex-1 border border-light-grey rounded-lg px-3 py-1.5 font-body text-[14px] text-deep-navy bg-white outline-none focus:border-soft-gold transition-colors"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            {count > 0 && (
              <div className="px-5 py-4 border-t border-light-grey shrink-0 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-body text-[13px] text-cool-grey">Total</span>
                  <span className="font-display text-[20px] text-deep-navy">{formatCurrency(total)}</span>
                </div>
                <p className="font-body text-[11px] text-cool-grey">Gifts of $250+ — choose letter or anonymous on the next screen</p>
                <Link
                  to="/giving-list/review"
                  onClick={() => setOpen(false)}
                  className="block w-full text-center bg-soft-gold text-deep-navy font-body text-[14px] font-semibold py-3 rounded-full hover:bg-bright-gold transition-colors"
                >
                  Review & Give →
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
      <style>{`
        @keyframes slideInRight {
          from { transform: translateX(100%); opacity: 0; }
          to   { transform: translateX(0);   opacity: 1; }
        }
      `}</style>
    </>
  )
}
