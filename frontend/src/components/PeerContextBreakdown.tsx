import type { ApiOrganization } from '../data/api'
import { getNteeLabel } from '../data/ntee'

interface ContextRow {
  dimension: string
  label: string
  value: string
  explanation: string
  action?: { text: string; link?: string }
}

export default function PeerContextBreakdown({ org }: { org: ApiOrganization }) {
  const rows: ContextRow[] = []

  // 1. CATEGORY CONTEXT — "You're in good company"
  if (org.NTEE1 && org.ntee1_total_orgs) {
    const nteeLabel = getNteeLabel(org.NTEE1)
    const pct = org.ntee1_percentile || 50
    const inTopQuarter = pct >= 75
    const inBottomQuarter = pct < 25

    rows.push({
      dimension: '🏛️ Your Sector',
      label: nteeLabel,
      value: inTopQuarter ? 'Strong financial position'
        : inBottomQuarter ? 'Building reserves'
        : 'Stable finances',
      explanation: inTopQuarter
        ? `You're managing resources well compared to other ${nteeLabel}. This matters to donors who want assurance.`
        : inBottomQuarter
        ? `Like many in your sector, you put most of your resources into the work. Donors understand that ${nteeLabel} often run on mission over margin, and your transparency speaks for itself.`
        : `You're in the typical range for ${nteeLabel}. Consistent and steady.`,
      action: {
        text: 'Claim profile → Show donors your story',
      }
    })
  }

  // 2. STATE CONTEXT — "Your community knows you're doing ok"
  if (org.STATE && org.state_category_total && org.state_category_total > 1) {
    rows.push({
      dimension: '📍 In Your State',
      label: `${org.state_category_total} orgs in ${org.STATE}`,
      value: `#${org.state_category_rank} in your sector`,
      explanation: `You're one of ${org.state_category_total} ${getNteeLabel(org.NTEE1)} nonprofits in ${org.STATE}. Your state's donors know this sector. They understand the market.`,
      action: {
        text: 'Check your peer group →',
      }
    })
  }

  // 3. SIZE CONTEXT — "You're not undersized, you're focused"
  if ((org as any).v5_context?.band?.label) {
    const v5 = (org as any).v5_context
    const band = v5.band.label
    const isMicro = band.includes('Micro')
    const isLarge = band.includes('Established')

    rows.push({
      dimension: '💰 Your Scale',
      label: band,
      value: isMicro ? 'Nimble & focused' : isLarge ? 'Established & scaled' : 'Growing',
      explanation: isMicro
        ? `At your scale, you're managing resources with discipline. Donors know small doesn't mean lesser. It means focused and close to the work.`
        : isLarge
        ? `You've scaled to serve more people. That takes operational skill donors respect.`
        : `You're in the growth phase. Building systems for larger impact.`,
    })
  }

  // 4. FINANCIAL HEALTH — "Here's how donors see you"
  if ((org as any).v5_context?.score?.health_signal) {
    const v5 = (org as any).v5_context
    const signal = v5.score?.health_signal

    const signals = {
      HEALTHY: {
        icon: '✓',
        title: 'Financially healthy',
        explanation: 'You have reserves, stable revenue, and room to take risks on new programs. Donors see a strong partner.',
      },
      STABLE: {
        icon: '◐',
        title: 'Financially stable',
        explanation: 'You manage year-to-year predictably. Most nonprofits run this way. It\'s normal and sustainable, and donors trust steady.',
      },
      CAUTION: {
        icon: '○',
        title: 'Building reserves',
        explanation: 'You put most of your resources into the work, like many nonprofits do. What matters to donors is your transparency and your plan, and that\'s where claiming your profile helps.',
      },
    }

    const s = signals[signal as keyof typeof signals]
    if (s) {
      rows.push({
        dimension: '🎯 Financial Health',
        label: s.title,
        value: '',
        explanation: s.explanation,
        action: signal === 'CAUTION' ? {
          text: 'Claim profile → Tell your story to reserves-minded donors',
        } : undefined,
      })
    }
  }

  if (rows.length === 0) return null

  return (
    <div className="rounded-lg border border-slate-200 bg-gradient-to-br from-slate-50 to-white p-6">
      <div className="mb-6">
        <h3 className="font-display text-[18px] font-semibold text-deep-navy mb-2">
          How Donors See You
        </h3>
        <p className="font-body text-[13px] text-cool-grey">
          Context from public IRS data. This helps donors understand your financial position without judgment.
        </p>
      </div>

      <div className="space-y-6">
        {rows.map((row, i) => (
          <div key={i} className="pb-6 last:pb-0 last:border-b-0 border-b border-slate-100">
            <div className="mb-3">
              <p className="font-body text-[12px] font-semibold text-cool-grey uppercase tracking-[0.05em] mb-1">
                {row.dimension}
              </p>
              <p className="font-display text-[16px] font-semibold text-deep-navy">
                {row.label}
              </p>
              {row.value && (
                <p className="font-body text-[13px] text-soft-gold font-semibold mt-1">
                  {row.value}
                </p>
              )}
            </div>

            <p className="font-body text-[14px] leading-relaxed text-deep-navy/80 mb-3">
              {row.explanation}
            </p>

            {row.action && (
              <button className="font-body text-[13px] font-semibold text-soft-gold hover:text-bright-gold transition-colors inline-flex items-center gap-1.5">
                <span>{row.action.text}</span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </button>
            )}
          </div>
        ))}
      </div>

      <div className="mt-6 pt-6 border-t border-slate-200">
        <p className="font-body text-[12px] text-cool-grey italic">
          <strong>For nonprofits:</strong> Claim your profile to update your story. Donors want to understand your context—not judge it.
        </p>
      </div>
    </div>
  )
}
