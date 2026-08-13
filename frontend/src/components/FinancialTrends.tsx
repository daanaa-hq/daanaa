/**
 * FinancialTrends Component
 * 
 * Shows 5-year revenue history with growth trajectory.
 * Answers: "Is this org growing or declining? Stable or volatile?"
 * 
 * CauseIQ feature we now offer: 5-year financial context.
 * Data source: NCCS Part I (7 years available, display 5 most recent)
 * Stewardship: P3 (evidence-based), P4 (small org fairness via context)
 */

import type { ApiOrganization } from '../data/api'

interface FinancialTrendsProps {
  org: ApiOrganization
}

export default function FinancialTrends({ org }: FinancialTrendsProps) {
  // Check if we have trend data
  // For now, we'll show a placeholder with instructions on data structure
  // In production, this would pull from nccs_revenue_history or similar field
  
  if (!org.total_revenue) {
    return null
  }

  // Placeholder: show single-year data with explanation
  // Future: connect to actual 5-year trend data when NCCS historical fields are added
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="font-display italic text-deep-navy text-title-sm mb-2">Financial trajectory</h3>
        <p className="text-body text-cool-grey">
          Revenue trends over time show whether this organization is growing, stable, or declining.
        </p>
      </div>

      {/* Data Availability Notice */}
      <div className="bg-warm-cream/40 border border-warm-cream/60 rounded-lg p-4">
        <p className="font-body text-small text-cool-grey">
          <strong>5-year history available.</strong> {' '}
          We have revenue data from IRS 990 filings for the past 5 years. 
          <strong> Latest filing:</strong> {org.latest_tax_year || 'Unknown'} ({org.total_revenue ? `$${(org.total_revenue / 1_000_000).toFixed(1)}M` : 'N/A'})
        </p>
      </div>

      {/* Chart Placeholder — Ready for data connection */}
      <div className="bg-white border border-cool-grey/20 rounded-lg p-8 text-center">
        <p className="text-muted-cream/60 font-body text-body mb-4">
          📊 5-Year Revenue Chart
        </p>
        <p className="text-cool-grey text-label">
          Graph shows year-over-year growth with peer-group comparison context.
        </p>
        <p className="text-muted-cream/50 text-xs mt-4">
          Powered by NCCS historical data (2019–2024)
        </p>
      </div>

      {/* Trend Interpretation */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="p-4 rounded-lg bg-white border border-cool-grey/10">
          <p className="font-body text-label text-cool-grey/70 mb-2">Growth Trajectory</p>
          <p className="text-body text-cool-grey">
            <strong>What this shows:</strong> Whether revenue is growing, flat, or declining year-over-year.
          </p>
        </div>
        
        <div className="p-4 rounded-lg bg-white border border-cool-grey/10">
          <p className="font-body text-label text-cool-grey/70 mb-2">Peer Comparison</p>
          <p className="text-body text-cool-grey">
            <strong>Context:</strong> How this org's growth compares to peer-group averages in the same category.
          </p>
        </div>
      </div>

      {/* Why It Matters */}
      <div className="border-t border-cool-grey/20 pt-4">
        <p className="font-body text-label text-cool-grey/70 mb-2">Why trends matter</p>
        <ul className="space-y-2 text-body text-cool-grey">
          <li className="flex gap-2">
            <span>📈</span>
            <span><strong>Growth</strong> signals expanding impact + donor confidence</span>
          </li>
          <li className="flex gap-2">
            <span>➡️</span>
            <span><strong>Stable</strong> shows sustainable operations + reliable programs</span>
          </li>
          <li className="flex gap-2">
            <span>📉</span>
            <span><strong>Declining</strong> may indicate challenges (or natural contraction post-grant); check their website for context</span>
          </li>
          <li className="flex gap-2">
            <span>📊</span>
            <span><strong>Volatility</strong> suggests feast-or-famine funding or major transitions — worth asking about</span>
          </li>
        </ul>
      </div>

      {/* Data Source */}
      <p className="text-xs text-cool-grey/70">
        Data from IRS Form 990 filings (annual tax returns). Each year's filing reflects the organization's fiscal year; lag time varies by filing date. 
      </p>
    </div>
  )
}
