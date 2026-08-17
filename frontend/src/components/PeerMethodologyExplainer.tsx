import React from 'react'
import type { ApiOrganization } from '../data/api'
import { getNteeLabel } from '../data/ntee'

/**
 * PeerMethodologyExplainer component
 * 
 * Stewardship Principle #9: Decisions should be explainable
 * Shows how the peer group was constructed: NTEE category, revenue band,
 * region, and when it was calculated. Donors understand "top 30% of what?"
 * 
 * P3: Trust signals must be evidence-based (peer composition visible)
 * P4: Small orgs treated fairly (no size bias in peer definition)
 */

export default function PeerMethodologyExplainer({ org }: { org: ApiOrganization }) {
  // Only show if we have the data
  if (!org.NTEE1 || !org.revenue_band) {
    return null
  }

  const nteeLabel = getNteeLabel(org.NTEE1)
  const revenueBand = org.revenue_band || 'Unknown'
  const region = org.STATE || 'Unknown'
  const lastUpdated = org.latest_tax_year ? `FY ${org.latest_tax_year}` : 'Recent'

  return (
    <details className="mt-6 group">
      <summary className="cursor-pointer text-soft-gold hover:text-bright-gold font-medium flex items-center gap-2">
        <span>How peer group was defined</span>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="group-open:rotate-180 transition-transform">
          <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
      </summary>

      <div className="mt-4 p-4 bg-soft-gold/5 border border-soft-gold/20 rounded-lg space-y-3">
        <p className="font-body text-small text-deep-navy">
          This organization is compared to nonprofits with similar characteristics:
        </p>

        <div className="space-y-2">
          <div className="flex justify-between items-start">
            <span className="font-body text-label text-cool-grey">Sector (NTEE)</span>
            <span className="font-body text-small text-deep-navy font-medium text-right max-w-[200px]">{nteeLabel}</span>
          </div>
          <div className="flex justify-between items-start">
            <span className="font-body text-label text-cool-grey">Revenue Band</span>
            <span className="font-body text-small text-deep-navy font-medium">{revenueBand}</span>
          </div>
          <div className="flex justify-between items-start">
            <span className="font-body text-label text-cool-grey">Geographic Region</span>
            <span className="font-body text-small text-deep-navy font-medium">{region}</span>
          </div>
          <div className="flex justify-between items-start">
            <span className="font-body text-label text-cool-grey">Based on Data</span>
            <span className="font-body text-small text-deep-navy font-medium">{lastUpdated}</span>
          </div>
        </div>

        <p className="font-body text-caption text-cool-grey pt-2 border-t border-soft-gold/20">
          Peer groups are recalculated annually. Organizations with incomplete financial data may not be included in all comparisons.
        </p>
      </div>
    </details>
  )
}
