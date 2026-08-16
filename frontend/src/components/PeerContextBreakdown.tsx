import type { ApiOrganization } from '../data/api'
import { getNteeLabel } from '../data/ntee'
import { CardPattern } from './ui/CardPattern'

interface ContextRow {
  dimension: string
  label: string
  value: string
  explanation: string
  action?: { text: string; link?: string }
}

// Builds the same row set the component renders. Exported as the single
// source of truth for whether this section has anything to show, so
// OrganizationDetail.tsx can gate its wrapper div on the real condition
// instead of duplicating (and risking drifting from) this branching logic.
export function buildPeerContextRows(org: ApiOrganization): ContextRow[] {
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
  // Fixed 2026-08-16: was reading org.v5_context.band.label -- v5_context is
  // the retired scoring generation (18.1% coverage, same population as the
  // now-removed Financial Health dimension below). Rebuilt on total_revenue
  // directly, using v6's own band thresholds (Micro <$150K, Professional
  // $150K-$700K, Established >$700K -- see CLAUDE.md's v6 architecture
  // section), not a new invented scale.
  if (org.total_revenue !== null && org.total_revenue !== undefined && org.total_revenue > 0) {
    const revenue = org.total_revenue
    const band = revenue < 150_000 ? 'Micro' : revenue < 700_000 ? 'Professional' : 'Established'
    const isMicro = band === 'Micro'
    const isLarge = band === 'Established'

    rows.push({
      dimension: 'Your Scale',
      label: band,
      value: isMicro ? 'Smaller operating scale' : isLarge ? 'Established operating scale' : 'Growing operating scale',
      explanation: `This is a description of operating scale from public records. Scale does not tell us the quality, reach, or importance of an organization's work.`,
    })
  }

  // 4. FINANCIAL HEALTH — removed 2026-08-16 (page-duplication pass): this
  // dimension read org.v5_context.score.health_signal and restated it with
  // more words ('More reserves in this comparison' / 'Within the usual
  // reserve range' / 'Fewer reserves than most peers') -- the exact same
  // signal AnswerCard's health chips already show prominently at the top of
  // the page ('Financially steady' / 'Managing well' / 'Could use community
  // support'), from the identical field. Same duplication pattern already
  // fixed in AtAGlance.tsx this session: say each real fact once.

  return rows
}

export default function PeerContextBreakdown({ org }: { org: ApiOrganization }) {
  const rows = buildPeerContextRows(org)

  if (rows.length === 0) return null

  return (
    <CardPattern variant="gradient" className="mb-12">
      <div className="mb-6">
        <h3 className="font-display text-title-sm font-semibold text-deep-navy mb-2">
          What the public record shows
        </h3>
        <p className="font-body text-small text-cool-grey">
          A few comparisons from public IRS data. They are context, not a rating, endorsement, or complete picture of the organization.
        </p>
      </div>

      <div className="space-y-6">
        {rows.map((row, i) => (
          <div key={i} className="pb-6 last:pb-0 last:border-b-0 border-b border-slate-100">
            <div className="mb-3">
              <p className="font-body text-caption font-semibold text-cool-grey uppercase tracking-[0.05em] mb-1">
                {row.dimension}
              </p>
              <p className="font-display text-lead font-semibold text-deep-navy">
                {row.label}
              </p>
              {row.value && (
                <p className="font-body text-small text-link-gold font-semibold mt-1">
                  {row.value}
                </p>
              )}
            </div>

            <p className="font-body text-body leading-relaxed text-deep-navy/80 mb-3">
              {row.explanation}
            </p>

            {row.action && (
              <button className="font-body text-small font-semibold text-soft-gold hover:text-bright-gold transition-colors inline-flex items-center gap-1.5">
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
        <p className="font-body text-caption text-cool-grey italic">
          <strong>For nonprofits:</strong> Claim your profile to update your story. Donors want to understand your context—not judge it.
        </p>
      </div>
    </CardPattern>
  )
}
