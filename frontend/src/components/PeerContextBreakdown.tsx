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
      value: inTopQuarter ? 'More reserves than most peers'
        : inBottomQuarter ? 'Fewer reserves than most peers'
        : 'Within the usual peer range',
      explanation: inTopQuarter
        ? `The public filings show more reserves than most ${nteeLabel} organizations in this comparison. That is one financial measure, not a judgment about the work.`
        : inBottomQuarter
        ? `The public filings show fewer reserves than most ${nteeLabel} organizations in this comparison. A reserve figure can reflect many choices and circumstances, so it should be read with the organization's own information.`
        : `The public filings place this organization within the usual range for ${nteeLabel} organizations in this comparison. The figure is context, not a conclusion.`,
      action: {
        text: 'Claim profile → Add your own context',
      }
    })
  }

  // 2. STATE CONTEXT — "Your community knows you're doing ok"
  if (org.STATE && org.state_category_total && org.state_category_total > 1) {
    rows.push({
      dimension: '📍 In Your State',
      label: `${org.state_category_total} orgs in ${org.STATE}`,
      value: `${org.state_category_total} organizations in this comparison`,
      explanation: `This organization is one of ${org.state_category_total} ${getNteeLabel(org.NTEE1)} nonprofits in ${org.STATE} included in this comparison. Daanaa does not use this figure to rank or endorse organizations.`,
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
      dimension: 'Your Scale',
      label: band,
      value: isMicro ? 'Smaller operating scale' : isLarge ? 'Established operating scale' : 'Growing operating scale',
      explanation: isMicro
        ? `This is a description of operating scale from public records. Scale does not tell us the quality, reach, or importance of an organization's work.`
        : isLarge
        ? `This is a description of operating scale from public records. Scale does not tell us the quality, reach, or importance of an organization's work.`
        : `This is a description of operating scale from public records. Scale does not tell us the quality, reach, or importance of an organization's work.`,
    })
  }

  // 4. FINANCIAL HEALTH — "Here's how donors see you"
  if ((org as any).v5_context?.score?.health_signal) {
    const v5 = (org as any).v5_context
    const signal = v5.score?.health_signal

    const signals = {
      HEALTHY: {
        icon: '✓',
        title: 'More reserves in this comparison',
        explanation: 'The available public filings show more reserves than most organizations in this comparison. This does not measure mission results or financial need.',
      },
      STABLE: {
        icon: '◐',
        title: 'Within the usual reserve range',
        explanation: 'You manage year-to-year predictably. Most nonprofits run this way. It\'s normal and sustainable, and donors trust steady.',
      },
      CAUTION: {
        icon: '○',
        title: 'Fewer reserves than most peers',
        explanation: 'You put most of your resources into the work, like many nonprofits do. What matters to donors is your transparency and your plan, and that\'s where claiming your profile helps.',
      },
    }

    const s = signals[signal as keyof typeof signals]
    if (s) {
      rows.push({
        dimension: 'Financial Health',
        label: s.title,
        value: '',
        explanation: s.explanation,
        action: signal === 'CAUTION' ? {
          text: 'Claim profile → Add your own context',
        } : undefined,
      })
    }
  }

  if (rows.length === 0) return null

  return (
    <div className="rounded-lg border border-slate-200 bg-gradient-to-br from-slate-50 to-white p-6">
      <div className="mb-6">
        <h3 className="font-display text-[18px] font-semibold text-deep-navy mb-2">
          What the public record shows
        </h3>
        <p className="font-body text-[13px] text-cool-grey">
          A few comparisons from public IRS data. They are context, not a rating, endorsement, or complete picture of the organization.
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
                <p className="font-body text-[13px] text-link-gold font-semibold mt-1">
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
