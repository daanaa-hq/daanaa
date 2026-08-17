import { useEffect } from 'react'
import { ApiOrganization } from '../data/api'
import { trackAtAGlanceVisible } from '../utils/analytics'

/**
 * AtAGlance: Small Org Clarity Display
 *
 * Trimmed 2026-08-16 (founder-reported page duplication, after AtAGlance
 * shipped to production for the first time this session): the original
 * 4-card version repeated content already shown elsewhere on the same
 * page, within a few seconds' scroll of the repeat:
 *  - Leadership's board size / independence % / employee count duplicated
 *    the "Key Stats Summary" header grid immediately above this section.
 *  - Service Scope's cause area duplicated the Categories pills further
 *    down; its state duplicated the location line at the very top; its
 *    revenue band duplicated the "Financial Context" header stat. Removed
 *    the whole card -- nothing in it was unique once the overlap was traced.
 *  - Mission Attribution's source duplicated the existing "AI assisted"
 *    pill shown next to the mission text; its one unique field
 *    (verified_date) is currently always empty (a known backend payload
 *    gap, unfixed), so the card added no real information. Removed.
 *  - Stability kept: a distinct composite signal (governance + staff +
 *    longevity + program ratio), not shown anywhere else on the page.
 *
 * Leadership kept but trimmed to governance policies only (COI,
 * whistleblower, document retention) -- the one thing in that card the
 * header stats don't already say.
 *
 * Same principle this session already applied elsewhere on this page
 * (see the ProvenanceLayers.tsx unmount note further down
 * OrganizationDetail.tsx): a fact repeated in a second box reads as
 * buggy or padded to a donor, not more trustworthy. Say each real fact
 * once, in its best place.
 *
 * Stewardship P3 (evidence-based), P4 (small org fairness), P5/P6 (honest transparency).
 */
export default function AtAGlance({ org }: { org: ApiOrganization }) {
  const { leadership_info } = org

  const hasPolicies = !!leadership_info && (
    leadership_info.has_coi_policy || leadership_info.has_whistleblower_policy || leadership_info.has_doc_retention_policy
  )

  // Don't render if we have nothing left to say that isn't said elsewhere
  if (!hasPolicies) {
    return null
  }

  // NOTE: Stability card removed 2026-08-17. It duplicated BoardReviewSimulation
  // (same signal + reasons + confidence structure), which is rendered below on the
  // same page. Keeping Governance policies card only — that's unique to this component.

  return (
    <div className="mb-12">
      {/* Section title */}
      <h2 className="font-display italic text-deep-navy text-title-sm mb-6">At a glance</h2>

      {/* Governance policies only — board size, stability signal, and other
          assessments are now handled by dedicated sections below (BoardReviewSimulation,
          FinancialContext, PeerContextBreakdown), eliminating duplication. */}
      <div>
        {/* Leadership — governance policies only. Board size / independence %
            / employee count live in the header stats grid above; repeating
            them here was the main source of the page duplication. */}
        {hasPolicies && (
          <div className="rounded-xl p-5 bg-white border border-light-grey">
            <h3 className="font-body text-small font-semibold text-deep-navy mb-3">Governance</h3>
            <div className="space-y-1 font-body text-small text-cool-grey">
              {leadership_info!.has_coi_policy && (
                <div className="flex items-center gap-1.5">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  <span className="text-xs">Conflict of Interest Policy</span>
                </div>
              )}
              {leadership_info!.has_whistleblower_policy && (
                <div className="flex items-center gap-1.5">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  <span className="text-xs">Whistleblower Policy</span>
                </div>
              )}
              {leadership_info!.has_doc_retention_policy && (
                <div className="flex items-center gap-1.5">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  <span className="text-xs">Document Retention Policy</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
