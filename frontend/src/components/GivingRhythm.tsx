import { useState } from 'react'
import { useWallet } from '../contexts/WalletContext'
import { isTemplateDue, WALLET_CONSTRAINTS } from '../types/wallet'
import type { WalletEntry, RecurringTemplate } from '../types/wallet'
import type { ApiOrganization } from '../data/api'

const CADENCE_LABEL: Record<RecurringTemplate['cadence'], string> = {
  monthly: 'every month', quarterly: 'every quarter', yearly: 'every year',
}

const MONTH_NAMES = ['January','February','March','April','May','June','July','August','September','October','November','December']

function donateHref(org: ApiOrganization | null): string | null {
  if (!org) return null
  if (org.donate_url && (org.donate_url_status === 'beta' || org.donate_url_status === 'claimed')) return org.donate_url
  if (org.website && org.website_status === 'ok') return org.website
  return null
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10)
}

/**
 * RhythmNudges — the "come back" strip at the top of the wallet.
 * Shows one card per org whose saved giving rhythm is due. Computed entirely
 * on-device (see isTemplateDue) — no reminder data ever leaves the phone.
 */
export function RhythmNudges({ entries, orgDataMap }: {
  entries: WalletEntry[]
  orgDataMap: Map<string, ApiOrganization>
}) {
  const { logDonation, snoozeRecurringTemplate } = useWallet()
  // Track which nudge is in the "did you give?" confirm state
  const [confirming, setConfirming] = useState<Set<string>>(new Set())

  const due = entries.filter(e => isTemplateDue(e))
  if (due.length === 0) return null

  return (
    <div className="mb-6 space-y-2">
      {due.map(entry => {
        const t = entry.recurringTemplate!
        const org = orgDataMap.get(entry.ein) ?? null
        const name = org?.organization_name ?? entry.ein
        const href = donateHref(org)
        const isConfirming = confirming.has(entry.ein)
        return (
          <div key={entry.ein} className="bg-soft-gold/10 border border-soft-gold/40 rounded-2xl px-5 py-4 flex flex-wrap items-center gap-3">
            <div className="flex-1 min-w-[200px]">
              <p className="font-body text-sm font-semibold text-deep-navy">
                Time for your ${t.amount.toLocaleString()} gift to {name}?
              </p>
              <p className="font-body text-caption text-cool-grey mt-0.5">
                You give {CADENCE_LABEL[t.cadence]}{t.cadence === 'yearly' && t.anchorMonth ? ` in ${MONTH_NAMES[t.anchorMonth - 1]}` : ''}. Only you can see this.
              </p>
            </div>
            {!isConfirming ? (
              <div className="flex items-center gap-2">
                {href ? (
                  <a
                    href={href} target="_blank" rel="noopener noreferrer"
                    onClick={() => setConfirming(prev => new Set(prev).add(entry.ein))}
                    className="px-4 py-2.5 rounded-xl bg-deep-navy text-warm-cream font-body text-small font-semibold hover:bg-deep-navy/90 transition-colors"
                  >
                    Give again
                  </a>
                ) : (
                  <button
                    onClick={() => setConfirming(prev => new Set(prev).add(entry.ein))}
                    className="px-4 py-2.5 rounded-xl bg-deep-navy text-warm-cream font-body text-small font-semibold hover:bg-deep-navy/90 transition-colors"
                  >
                    I gave by check
                  </button>
                )}
                <button
                  onClick={() => {
                    // Quiet for 30 days — the next cycle re-surfaces it naturally
                    const d = new Date(); d.setDate(d.getDate() + 30)
                    snoozeRecurringTemplate(entry.ein, d.toISOString().slice(0, 10))
                  }}
                  className="px-3 py-2.5 rounded-xl border border-light-grey font-body text-small text-cool-grey hover:text-deep-navy transition-colors"
                >
                  Not now
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    const irsSnapshot = org ? {
                      irsEligibilityStatus: (org.tax_deductible === false ? ('unknown' as const) : ('verified' as const)),
                      irsEligibilityCheckedAt: org.tax_deductible_checked_at,
                      irsEligibilitySources: ['IRS Business Master File', 'IRS Auto-Revocation List'],
                    } : undefined
                    logDonation(entry.ein, t.amount, todayIso(), 'Recurring gift', undefined, irsSnapshot)
                    setConfirming(prev => { const n = new Set(prev); n.delete(entry.ein); return n })
                  }}
                  className="px-4 py-2.5 rounded-xl bg-success-green text-white font-body text-small font-semibold hover:opacity-90 transition-colors"
                >
                  Log my ${t.amount.toLocaleString()} gift
                </button>
                <button
                  onClick={() => setConfirming(prev => { const n = new Set(prev); n.delete(entry.ein); return n })}
                  className="px-3 py-2.5 rounded-xl border border-light-grey font-body text-small text-cool-grey hover:text-deep-navy transition-colors"
                >
                  I didn't give
                </button>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

/**
 * RhythmControl — set/edit/remove a giving rhythm for one org.
 * Lives inside the wallet card's expandable log panel.
 */
export function RhythmControl({ entry, orgName }: { entry: WalletEntry; orgName: string }) {
  const { setRecurringTemplate, clearRecurringTemplate } = useWallet()
  const t = entry.recurringTemplate
  const [editing, setEditing] = useState(false)
  const giftAmounts = (entry.donations ?? []).map(d => d.amount)
  const lastGift = giftAmounts.length ? giftAmounts[giftAmounts.length - 1] : undefined
  const [amount, setAmount] = useState<string>(t ? String(t.amount) : lastGift ? String(lastGift) : '')
  const [cadence, setCadence] = useState<RecurringTemplate['cadence']>(t?.cadence ?? 'yearly')
  const [anchorMonth, setAnchorMonth] = useState<number>(t?.anchorMonth ?? new Date().getMonth() + 1)

  if (t && !editing) {
    return (
      <div className="flex items-center gap-3 flex-wrap">
        <p className="font-body text-small text-deep-navy">
          <span className="font-semibold">${t.amount.toLocaleString()}</span> {CADENCE_LABEL[t.cadence]}
          {t.cadence === 'yearly' && t.anchorMonth ? ` in ${MONTH_NAMES[t.anchorMonth - 1]}` : ''}
        </p>
        <button onClick={() => setEditing(true)} className="font-body text-caption text-cool-grey hover:text-deep-navy underline transition-colors">Edit</button>
        <button onClick={() => clearRecurringTemplate(entry.ein)} className="font-body text-caption text-cool-grey hover:text-destructive underline transition-colors">Remove</button>
      </div>
    )
  }

  const parsed = Number(amount)
  const valid = Number.isFinite(parsed) && parsed >= WALLET_CONSTRAINTS.AMOUNT_MIN

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <span className="font-body text-small text-cool-grey">$</span>
      <input
        type="number" inputMode="decimal" min={WALLET_CONSTRAINTS.AMOUNT_MIN} value={amount}
        onChange={e => setAmount(e.target.value)}
        placeholder="50"
        aria-label={`Gift amount for ${orgName}`}
        className="w-20 px-2 py-2 rounded-lg border border-light-grey font-body text-small text-deep-navy bg-white outline-none focus:border-soft-gold"
      />
      <select
        value={cadence}
        onChange={e => setCadence(e.target.value as RecurringTemplate['cadence'])}
        aria-label="How often"
        className="px-2 py-2 rounded-lg border border-light-grey font-body text-small text-deep-navy bg-white outline-none cursor-pointer"
      >
        <option value="monthly">every month</option>
        <option value="quarterly">every quarter</option>
        <option value="yearly">every year</option>
      </select>
      {cadence === 'yearly' && (
        <select
          value={anchorMonth}
          onChange={e => setAnchorMonth(Number(e.target.value))}
          aria-label="Which month"
          className="px-2 py-2 rounded-lg border border-light-grey font-body text-small text-deep-navy bg-white outline-none cursor-pointer"
        >
          {MONTH_NAMES.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
        </select>
      )}
      <button
        disabled={!valid}
        onClick={() => {
          setRecurringTemplate(entry.ein, {
            amount: parsed, cadence, createdAt: Date.now(),
            ...(cadence === 'yearly' ? { anchorMonth } : {}),
          })
          setEditing(false)
        }}
        className="px-3 py-2 rounded-lg bg-deep-navy text-warm-cream font-body text-caption font-semibold disabled:opacity-40 hover:bg-deep-navy/90 transition-colors"
      >
        {t ? 'Save' : 'Set rhythm'}
      </button>
      {t && editing && (
        <button onClick={() => setEditing(false)} className="font-body text-caption text-cool-grey hover:text-deep-navy underline transition-colors">Cancel</button>
      )}
    </div>
  )
}
