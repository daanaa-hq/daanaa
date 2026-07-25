import { useState } from 'react'
import type { RecurringTemplate } from '../types/wallet'

/**
 * RecurringSetup — Set up a monthly/quarterly/yearly giving rhythm.
 * Appears after user logs a donation. No suggested amounts (P5).
 */
export default function RecurringSetup({
  orgName,
  lastDonationAmount,
  onSetup,
  onClose,
}: {
  orgName: string
  lastDonationAmount?: number
  onSetup: (template: RecurringTemplate) => void
  onClose: () => void
}) {
  const [amount, setAmount] = useState<string>(lastDonationAmount?.toString() || '')
  const [cadence, setCadence] = useState<'monthly' | 'quarterly' | 'yearly'>('monthly')
  const [anchorMonth, setAnchorMonth] = useState<number | undefined>(
    cadence === 'yearly' ? new Date().getMonth() + 1 : undefined
  )

  const handleSetup = () => {
    const parsedAmount = parseFloat(amount)
    if (!amount || isNaN(parsedAmount) || parsedAmount <= 0) return

    const template: RecurringTemplate = {
      amount: parsedAmount,
      cadence,
      createdAt: Date.now(),
      anchorMonth: cadence === 'yearly' ? anchorMonth : undefined,
    }

    onSetup(template)
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-deep-navy/50 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-[420px] rounded-2xl bg-white shadow-2xl overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-warm-cream px-6 pt-5 pb-4 border-b border-light-grey">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="font-body text-[11px] font-semibold text-link-gold uppercase tracking-widest mb-0.5">
                Recurring giving
              </p>
              <h3 className="font-display text-[20px] text-deep-navy leading-snug">{orgName}</h3>
            </div>
            <button
              onClick={onClose}
              className="shrink-0 mt-0.5 p-1.5 rounded-lg text-cool-grey hover:text-deep-navy hover:bg-light-grey/40 transition-colors"
              aria-label="Close"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <p className="mt-2 font-body text-[12px] text-cool-grey leading-relaxed">
            Give at your own pace. Change or cancel anytime. All stored on your device.
          </p>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-4">
          {/* Amount */}
          <div>
            <label className="block font-body text-[12px] font-medium text-deep-navy mb-1.5">
              Amount per {cadence === 'yearly' ? 'year' : cadence === 'quarterly' ? 'quarter' : 'month'}
            </label>
            <div className="flex items-center gap-2">
              <span className="text-cool-grey font-body text-[14px]">$</span>
              <input
                type="number"
                value={amount}
                onChange={e => setAmount(e.target.value)}
                placeholder="0.00"
                min="0"
                step="0.01"
                className="flex-1 px-4 py-2.5 border border-light-grey rounded-xl font-body text-[14px] text-deep-navy placeholder:text-cool-grey/50 focus:outline-none focus:ring-2 focus:ring-soft-gold/40"
              />
            </div>
            <p className="mt-1.5 font-body text-[11px] text-cool-grey">
              {amount && !isNaN(parseFloat(amount))
                ? `${cadence === 'monthly' ? '12 times' : cadence === 'quarterly' ? '4 times' : 'once'} per year = $${(
                    parseFloat(amount) * (cadence === 'monthly' ? 12 : cadence === 'quarterly' ? 4 : 1)
                  ).toFixed(2)}`
                : 'Enter an amount'}
            </p>
          </div>

          {/* Cadence */}
          <div>
            <label className="block font-body text-[12px] font-medium text-deep-navy mb-1.5">Frequency</label>
            <div className="space-y-1.5">
              {['monthly', 'quarterly', 'yearly'].map(c => (
                <label key={c} className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="radio"
                    name="cadence"
                    value={c}
                    checked={cadence === c}
                    onChange={() => {
                      setCadence(c as 'monthly' | 'quarterly' | 'yearly')
                      if (c === 'yearly') setAnchorMonth(new Date().getMonth() + 1)
                      else setAnchorMonth(undefined)
                    }}
                    className="w-4 h-4 text-soft-gold"
                  />
                  <span className="font-body text-[13px] text-deep-navy capitalize">{c}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Yearly anchor month */}
          {cadence === 'yearly' && (
            <div>
              <label className="block font-body text-[12px] font-medium text-deep-navy mb-1.5">
                When do you want to give? <span className="font-normal text-cool-grey">(month)</span>
              </label>
              <select
                value={anchorMonth || new Date().getMonth() + 1}
                onChange={e => setAnchorMonth(parseInt(e.target.value))}
                className="w-full px-4 py-2.5 border border-light-grey rounded-xl font-body text-[14px] text-deep-navy bg-white focus:outline-none focus:ring-2 focus:ring-soft-gold/40"
              >
                {Array.from({ length: 12 }, (_, i) => {
                  const month = new Date(2024, i, 1).toLocaleString('en-US', { month: 'long' })
                  return (
                    <option key={i + 1} value={i + 1}>
                      {month}
                    </option>
                  )
                })}
              </select>
            </div>
          )}

          {/* Info */}
          <div className="rounded-lg bg-warm-cream border border-light-grey px-3 py-2.5">
            <p className="font-body text-[11px] text-cool-grey leading-relaxed">
              📅 We'll remind you when it's time to give. You can skip any time. All your giving is private and stored on this device.
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="px-6 pb-6 space-y-2.5">
          <button
            onClick={handleSetup}
            disabled={!amount || isNaN(parseFloat(amount)) || parseFloat(amount) <= 0}
            className="w-full py-3 rounded-xl bg-soft-gold text-deep-navy font-body text-[14px] font-semibold hover:bg-bright-gold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Set up recurring
          </button>
          <button
            onClick={onClose}
            className="w-full py-2.5 font-body text-[13px] text-cool-grey hover:text-deep-navy transition-colors"
          >
            Not now
          </button>
        </div>
      </div>
    </div>
  )
}
