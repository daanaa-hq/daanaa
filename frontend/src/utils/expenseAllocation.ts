import type { ApiOrganization } from '../data/api'

/**
 * Shared reconciliation guard for program/admin/fundraising expense splits.
 *
 * registry_enriched.program_expenses/management_expenses/fundraising_expenses
 * trace back to a legacy irs_soi ingestion pass and, for a large share of
 * orgs, do NOT reconcile with the verified-correct total_expenses field --
 * commonly summing to ~2x the real total (2026-08-16 incident: a partner
 * org flagged a wrong breakdown during a demo). Cross-check against
 * total_expenses and refuse to return percentages we can't verify, rather
 * than showing wrong numbers with a false-confidence sentence attached.
 * See DECISIONS.md 2026-08-16.
 *
 * Extracted 2026-08-19 (Codex review): this guard originally lived inline
 * in HowToHelp.tsx only. BoardReviewSimulation.tsx independently rendered
 * the same org.program_expense_pct field with no reconciliation check --
 * the exact "stewardship guard reimplemented, second copy drifts" bug
 * class already logged in LESSONS.md 2026-08-18. One shared function now,
 * both consumers use it.
 */
export interface ReconciledExpenseAllocation {
  reconciles: boolean
  programPct: number | null
  adminPct: number | null
  fundraisingPct: number | null
}

export function getReconciledExpenseAllocation(org: ApiOrganization): ReconciledExpenseAllocation {
  const programExpensesRaw = org.program_expenses ?? 0
  const managementExpensesRaw = org.management_expenses ?? 0
  const fundraisingExpensesRaw = org.fundraising_expenses ?? 0
  const partsSum = programExpensesRaw + managementExpensesRaw + fundraisingExpensesRaw
  const verifiedTotal = org.total_expenses
  const reconciles = !!verifiedTotal && verifiedTotal > 0 && partsSum > 0
    && Math.abs(partsSum - verifiedTotal) <= 0.2 * verifiedTotal

  return {
    reconciles,
    programPct: reconciles ? Math.round((programExpensesRaw / partsSum) * 100) : null,
    adminPct: reconciles ? Math.round((managementExpensesRaw / partsSum) * 100) : null,
    fundraisingPct: reconciles ? Math.round((fundraisingExpensesRaw / partsSum) * 100) : null,
  }
}
