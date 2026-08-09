// Maps the real tax_deductible boolean (computed server-side from IRS BMF
// deductibility code + the daily Auto-Revocation sync) onto the badge/detail
// vocabulary IrsEligibilityContext.tsx already speaks. Added 2026-08-09 to
// replace reads of org.irs_eligibility_status, whose source DB columns were
// dropped ~2026-08-01 (see frontend/src/data/api.ts:150-154) — every read of
// that field was silently falling back to 'unknown' for every organization.
//
// null/undefined intentionally maps to 'unknown', not 'verified' — a genuine
// data gap must never render as reassuring. See LESSONS.md 2026-08-09.
export type EligibilityStatus = 'verified' | 'unverified' | 'revoked' | 'unknown' | 'exception_possible'

export function taxDeductibleToStatus(taxDeductible: boolean | null | undefined): EligibilityStatus {
  if (taxDeductible === true) return 'verified'
  if (taxDeductible === false) return 'revoked'
  return 'unknown'
}
