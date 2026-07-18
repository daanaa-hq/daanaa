/**
 * Giving rhythm due-date logic. This decides when we nudge a donor to give
 * again — a wrong answer either nags (P5 violation) or forgets (broken loop).
 */
import { isTemplateDue } from '../types/wallet'
import type { WalletEntry, RecurringTemplate } from '../types/wallet'

const DAY = 86_400_000

function entry(template: Partial<RecurringTemplate>, donations: { date: string }[] = []): WalletEntry {
  return {
    ein: '123456789',
    bookmarkedAt: 1,
    recurringTemplate: { amount: 50, cadence: 'yearly', createdAt: Date.now(), ...template },
    donations: donations.map((d, i) => ({ id: String(i), amount: 50, date: d.date })),
  }
}

describe('isTemplateDue', () => {
  const today = new Date('2026-07-17T12:00:00')

  it('is false with no template', () => {
    expect(isTemplateDue({ ein: '123456789', bookmarkedAt: 1 }, today)).toBe(false)
  })

  it('yearly: due when last gift was over a year ago', () => {
    expect(isTemplateDue(entry({ cadence: 'yearly' }, [{ date: '2025-06-01' }]), today)).toBe(true)
  })

  it('yearly: not due when gift was this cycle', () => {
    expect(isTemplateDue(entry({ cadence: 'yearly' }, [{ date: '2026-01-15' }]), today)).toBe(false)
  })

  it('yearly with anchorMonth: only fires in that month', () => {
    const overdue = [{ date: '2024-12-05' }]
    expect(isTemplateDue(entry({ cadence: 'yearly', anchorMonth: 12 }, overdue), today)).toBe(false)
    expect(isTemplateDue(entry({ cadence: 'yearly', anchorMonth: 7 }, overdue), today)).toBe(true)
  })

  it('monthly: due after 30 days since last gift', () => {
    expect(isTemplateDue(entry({ cadence: 'monthly' }, [{ date: '2026-06-01' }]), today)).toBe(true)
    expect(isTemplateDue(entry({ cadence: 'monthly' }, [{ date: '2026-07-01' }]), today)).toBe(false)
  })

  it('uses the LATEST gift, not the first logged', () => {
    const gifts = [{ date: '2025-01-01' }, { date: '2026-07-10' }]
    expect(isTemplateDue(entry({ cadence: 'monthly' }, gifts), today)).toBe(false)
  })

  it('no gifts yet: anchors to template creation time', () => {
    const oldCreate = today.getTime() - 40 * DAY
    expect(isTemplateDue(entry({ cadence: 'monthly', createdAt: oldCreate }), today)).toBe(true)
    const recentCreate = today.getTime() - 5 * DAY
    expect(isTemplateDue(entry({ cadence: 'monthly', createdAt: recentCreate }), today)).toBe(false)
  })

  it('snooze silences a due nudge until the date passes', () => {
    const overdue = [{ date: '2025-01-01' }]
    expect(isTemplateDue(entry({ cadence: 'yearly', snoozedUntil: '2026-08-01' }, overdue), today)).toBe(false)
    expect(isTemplateDue(entry({ cadence: 'yearly', snoozedUntil: '2026-07-01' }, overdue), today)).toBe(true)
  })
})
