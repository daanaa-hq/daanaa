// Static research snapshot loader.
//
// The public research page (daanaa.org/research) is served as a flat static
// page with no live server connection. All its numbers come from a single
// precomputed JSON file (frontend/public/research-snapshot.json), regenerated
// by scripts/export_research_snapshot.py whenever the data changes.
//
// This loader fetches that file once and caches the promise so every research
// component shares one network request.

export interface ResearchSnapshot {
  metadata: {
    total_organizations: number
    data_period: string
    version: string
    generated_at: string
    disclaimer: string
  }
  revenue_bands: Array<{
    operating_model: string
    revenue_band_number: number
    count: number
    pct_of_total: number
    avg_peer_percentile: number | null
    avg_months_reserve: number | null
  }>
  categories: Array<{
    ntee1: string
    ntee_label: string
    count: number
    pct_of_total: number
    avg_revenue: number | null
    avg_peer_percentile: number | null
  }>
  states: Array<{
    state: string
    count: number
    pct: number
    avg_revenue: number | null
    avg_peer_percentile: number | null
  }>
  spending: Array<{
    tier: string
    tier_name: string
    count: number
    median_program_spend: number | null
    p25_program_spend: number | null
    p75_program_spend: number | null
  }>
  entity_types?: {
    total: number
    public_charity: number
    private_foundation: number
    unclassified: number
    pct_public_charity: number
    pct_private_foundation: number
    pct_unclassified: number
  }
  v6?: {
    total_active: number
    total_scored: number
    unscored_count: number
    coverage_pct: number
    tiers: Array<{
      key: string
      name: string
      description: string
      count: number
      pct: number
      avg_percentile: number | null
      avg_peer_group_size: number | null
      avg_program_pct: number | null
      avg_months_reserve: number | null
    }>
  }
  monthly_changes?: Array<{
    month: string
    new_registrations: number
    revocations: number
    net: number
    is_batch_revocation: boolean
  }>
}

let cache: Promise<ResearchSnapshot> | null = null

export function loadResearchSnapshot(): Promise<ResearchSnapshot> {
  if (!cache) {
    cache = fetch('/research-snapshot.json').then((r) => {
      if (!r.ok) throw new Error(`research snapshot ${r.status}`)
      return r.json()
    })
  }
  return cache
}
