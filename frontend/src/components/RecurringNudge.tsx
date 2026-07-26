import { formatCurrency } from '../data/organizations'

/**
 * RecurringNudge — Wallet card shown when recurring gift is due.
 * Donor can confirm gift or snooze (no push notifications; wallet-only).
 */
export default function RecurringNudge({
  orgName,
  amount,
  cadence,
  onConfirm,
  onSnooze,
}: {
  orgName: string
  amount: number
  cadence: 'monthly' | 'quarterly' | 'yearly'
  onConfirm: () => void
  onSnooze: () => void
}) {
  const cadenceLabel = cadence === 'monthly' ? 'month' : cadence === 'quarterly' ? 'quarter' : 'year'

  return (
    <div className="rounded-xl bg-gradient-to-r from-soft-gold/10 to-emerald-500/10 border border-soft-gold/30 p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div className="flex-1">
        <p className="font-body text-caption font-semibold text-soft-gold uppercase tracking-wide mb-1">
          Time to give
        </p>
        <p className="font-body text-body text-deep-navy">
          <strong>{orgName}</strong>
        </p>
        <p className="font-body text-small text-cool-grey mt-0.5">
          {formatCurrency(amount)} every {cadenceLabel}
        </p>
      </div>

      <div className="flex gap-2 sm:justify-end">
        <button
          onClick={onConfirm}
          className="flex-1 sm:flex-none px-5 py-2 rounded-lg bg-emerald-500 text-white font-body text-small font-semibold hover:bg-emerald-600 transition-colors"
        >
          Log gift
        </button>
        <button
          onClick={onSnooze}
          className="flex-1 sm:flex-none px-5 py-2 rounded-lg border border-cool-grey text-cool-grey font-body text-small font-semibold hover:bg-warm-cream/40 transition-colors"
        >
          Snooze
        </button>
      </div>
    </div>
  )
}
