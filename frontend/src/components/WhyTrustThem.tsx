import { ApiOrganization } from '../data/api'
import { formatCurrency, formatNumber } from '../data/organizations'

/**
 * WhyTrustThem: Unified Trust Narrative
 *
 * Combines financial health, governance quality, and verification status
 * into a coherent story for donors. Stewardship P3 (evidence-based),
 * P4 (small org fairness), P5 (honest transparency), P9 (explainability).
 */
export default function WhyTrustThem({ org }: { org: ApiOrganization }) {
  const hasFinancials = org.total_revenue !== null || org.months_of_reserve !== null || org.revenue_display_is_estimate
  const hasGovernance = org.leadership_info && (
    org.leadership_info.board_size || org.leadership_info.employee_count
  )
  const hasVerification = org.latest_tax_year !== null
  const tier = org.scoring_tier
  const hasPeerContext = tier === '1_Full_Context' ||
    tier === '2_Regional_Context' ||
    tier === '3_Broad_Category' ||
    tier === '3b_Broad_Category' ||
    tier === '4_Archetype_Only'

  if (!hasFinancials && !hasGovernance && !hasVerification && !hasPeerContext) {
    return null
  }

  return (
    <section className="mb-6 py-6 md:py-8 border-b border-cool-grey/20">
      <h2 className="font-display text-deep-navy text-title-lg mb-4">Why should you trust them?</h2>

      <div className="space-y-6">
        {/* Financial Strength */}
        {hasFinancials && (
          <div>
            <h3 className="font-body text-small font-semibold text-deep-navy mb-3 uppercase tracking-wide">Financial Strength</h3>
            <div className="space-y-2 mb-3">
              {org.total_revenue !== null && (
                <div className="flex justify-between items-baseline">
                  <span className="font-body text-base text-cool-grey">Annual revenue</span>
                  <span className="font-body text-base font-medium text-deep-navy">{formatCurrency(org.total_revenue)}</span>
                </div>
              )}
              {org.total_revenue === null && org.revenue_display_is_estimate && (
                <div className="flex justify-between items-baseline">
                  <span className="font-body text-base text-cool-grey">Annual revenue</span>
                  <span className="font-body text-base font-medium text-deep-navy italic">{org.revenue_display}</span>
                </div>
              )}
              {org.months_of_reserve !== null && (
                <div className="flex justify-between items-baseline">
                  <span className="font-body text-base text-cool-grey">Months of reserves</span>
                  <span className="font-body text-base font-medium text-deep-navy">
                    {org.months_of_reserve > 999 ? '999+' : org.months_of_reserve < 0 ? `(${Math.round(Math.abs(org.months_of_reserve))})` : Math.round(org.months_of_reserve)} months
                  </span>
                </div>
              )}
            </div>
            <p className="font-body text-small text-cool-grey leading-relaxed">
              {org.total_revenue === null && org.months_of_reserve === null && org.revenue_display_is_estimate
                ? "We don't know enough to say more about this organization's finances. No full IRS 990 filing is on record, consistent with a small organization's filing requirements. See something wrong? "
                : org.months_of_reserve === null
                ? 'This organization maintains a solid financial position to support their mission.'
                : org.months_of_reserve < 0
                ? 'This organization is managing through a challenging financial period but remains committed to their mission.'
                : org.months_of_reserve < 3
                ? 'This organization maintains modest reserves and is actively managing cash flow to continue their work.'
                : 'This organization has built a solid financial cushion and can weather economic changes while continuing their mission.'}
              {org.total_revenue === null && org.months_of_reserve === null && org.revenue_display_is_estimate && (
                <a href="#mistake-registry" className="text-deep-navy underline hover:no-underline">Tell us</a>
              )}
            </p>
          </div>
        )}

        {/* Governance & Leadership */}
        {hasGovernance && (
          <div>
            <h3 className="font-body text-small font-semibold text-deep-navy mb-3 uppercase tracking-wide">Governance & Leadership</h3>
            <div className="space-y-2 mb-3">
              {org.leadership_info!.board_size && org.leadership_info!.board_size > 0 && (
                <div className="flex justify-between items-baseline">
                  <span className="font-body text-base text-cool-grey">Board size</span>
                  <span className="font-body text-base font-medium text-deep-navy">
                    {formatNumber(org.leadership_info!.board_size)} members
                    {org.leadership_info!.board_independence_pct !== undefined && org.leadership_info!.board_independence_pct !== null && (
                      <span className="text-cool-grey">, {Math.round(org.leadership_info!.board_independence_pct)}% independent</span>
                    )}
                  </span>
                </div>
              )}
              {org.leadership_info!.employee_count && org.leadership_info!.employee_count > 0 && (
                <div className="flex justify-between items-baseline">
                  <span className="font-body text-base text-cool-grey">Staff</span>
                  <span className="font-body text-base font-medium text-deep-navy">{formatNumber(org.leadership_info!.employee_count)} employees</span>
                </div>
              )}
              {(org.leadership_info!.has_coi_policy || org.leadership_info!.has_whistleblower_policy || org.leadership_info!.has_doc_retention_policy) && (
                <div className="flex items-start gap-2">
                  <span className="font-body text-base text-cool-grey">Policies in place</span>
                  <div className="flex flex-col gap-1">
                    {org.leadership_info!.has_coi_policy && (
                      <span className="inline-flex items-center gap-1.5 text-sm text-deep-navy">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="20 6 9 17 4 12"/>
                        </svg>
                        Conflict of Interest
                      </span>
                    )}
                    {org.leadership_info!.has_whistleblower_policy && (
                      <span className="inline-flex items-center gap-1.5 text-sm text-deep-navy">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="20 6 9 17 4 12"/>
                        </svg>
                        Whistleblower Protection
                      </span>
                    )}
                    {org.leadership_info!.has_doc_retention_policy && (
                      <span className="inline-flex items-center gap-1.5 text-sm text-deep-navy">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="20 6 9 17 4 12"/>
                        </svg>
                        Document Retention
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
            <p className="font-body text-small text-cool-grey leading-relaxed">
              {org.leadership_info!.board_size && org.leadership_info!.board_size >= 5
                ? 'A strong board and experienced staff team indicate sound organizational oversight and continuity.'
                : "Active leadership is engaged in guiding the organization's mission."}
            </p>
          </div>
        )}

        {/* Peer financial context uses the live v6 scorer fields, matching the
            detailed FinancialContext card below. tier_label is the verified
            description; do not use peer_group_description_v6 or counts here. */}
        {hasPeerContext && (
          <div>
            <h3 className="font-body text-small font-semibold text-deep-navy mb-3 uppercase tracking-wide">How they compare</h3>
            <p className="font-body text-small text-cool-grey leading-relaxed">
              {(tier === '1_Full_Context' || tier === '2_Regional_Context') && org.merit_percentile_v6 != null && (
                <>Stronger reserves than {Math.round(org.merit_percentile_v6)}% of {org.tier_label ?? 'similar organizations'}.</>
              )}
              {(tier === '1_Full_Context' || tier === '2_Regional_Context') && org.merit_percentile_v6 == null && (
                <>A peer context is available, but a numeric reserve comparison is not available yet{org.tier_label ? `: ${org.tier_label}.` : '.'}</>
              )}
              {(tier === '3_Broad_Category' || tier === '3b_Broad_Category') && (
                <>Compared within a broader category{org.tier_label ? `: ${org.tier_label}.` : '.'}</>
              )}
              {tier === '4_Archetype_Only' && (
                <>Not enough detailed financial data for a numeric comparison yet — that's not a reflection on their quality.</>
              )}
            </p>
          </div>
        )}

        {/* Verification Status */}
        {hasVerification && (
          <div className="p-4 bg-soft-gold/10 rounded-lg border border-soft-gold/20">
            <h3 className="font-body text-small font-semibold text-deep-navy mb-3">Verification Status</h3>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                <span className="font-body text-small text-deep-navy">US IRS 501(c)(3) nonprofit</span>
              </div>
              <div className="flex items-center gap-2">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                <span className="font-body text-small text-deep-navy">
                  Form 990 on file {org.latest_tax_year && `(FY ${org.latest_tax_year})`}
                </span>
              </div>
              {org.data_source && (
                <div className="flex items-center gap-2 mt-2 pt-2 border-t border-soft-gold/20">
                  <span className="font-body text-caption text-cool-grey">
                    Data verified by {org.data_source === 'propublica' ? 'ProPublica Nonprofit Explorer' : org.data_source === 'nccs' ? 'NCCS' : 'IRS'}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
