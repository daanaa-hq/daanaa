// Plain-English size for the "Size" field on an org profile. `revenue_band`
// is inconsistent across the codebase (a numeric 0-7 code in some call sites,
// a human string elsewhere per data/api.ts's own comment) and not safe to
// render directly. Deriving straight from `total_revenue` — always a real
// number when present — avoids the ambiguity entirely. Null when revenue is
// unknown, so the caller hides the field rather than showing a guess or a
// stray "0". Moved here 2026-08-08 from OrganizationDetail.tsx, where it was
// written but never wired up (OrgInfoHierarchy.tsx used the wrong field,
// `merit_band` — a dormant lamp-tier value — instead, showing "Size: 0").
export function nonprofitSizeLabel(revenue: number | null | undefined): string | null {
  if (revenue == null || revenue <= 0) return null
  if (revenue < 250_000) return 'Micro'
  if (revenue < 1_000_000) return 'Small'
  if (revenue < 10_000_000) return 'Mid-size'
  if (revenue < 100_000_000) return 'Large'
  return 'Major'
}
