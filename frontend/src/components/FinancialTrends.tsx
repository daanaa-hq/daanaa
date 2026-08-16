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

// 2026-08-16: this component previously claimed "5-year history available"
// and "Powered by NCCS historical data (2019-2024)" unconditionally --
// hardcoded copy shown for every org with total_revenue set, regardless of
// whether any historical data actually existed. No real chart or data
// points were ever rendered (the "chart" was literal placeholder text).
// This asserted data completeness with no basis in what was shown --
// a Stewardship P3 violation. Real multi-year trend data (org_revenue_history
// prop) is not yet wired from the backend; until it is, this component
// renders nothing rather than a false claim. See DECISIONS.md 2026-08-16
// and Track: "Show real 5-year financial trends" for the actual build.
export default function FinancialTrends({ org: _org }: FinancialTrendsProps) {
  return null
}
