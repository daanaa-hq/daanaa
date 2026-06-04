import type { ApiOrganization } from '../data/api'

export type TierName = 'Beacon' | 'Lantern' | 'Flame' | 'Glow' | 'Ember' | 'Spark'

export const PASSING_BANDS = ['Blazing', 'Burning Bright', 'Steady Flame']

// The tier gate is looser than the display: only the bottom band blocks
// Beacon/Lantern. Since ~99% of orgs have NO band, demoting only clearly-weak
// financials avoids penalising the minority that happen to have data.
const GATE_BLOCKING_BANDS = ['Just Starting']

// The headline score IS the documented composite (0.65 revenue + 0.35 reserve),
// i.e. peer_percentile — the same number shown in the methodology and the score-history
// table. Falls back to the revenue-only NTEE rank when no composite exists. Never use
// the legacy merit_score here; it diverges from the published methodology.
export function getFinancialHealth(org: ApiOrganization): { score: number; band: string } | null {
  const pct = org.peer_percentile ?? org.ntee1_percentile
  if (pct == null) return null
  const score = Math.round(pct)
  const band =
    score >= 85 ? 'Blazing' :
    score >= 70 ? 'Burning Bright' :
    score >= 55 ? 'Steady Flame' :
    score >= 35 ? 'Growing' : 'Just Starting'
  return { score, band }
}

// v4.0 Financial Health — separate scale from visibility.
// Represents financial health relative to peer group (model + revenue band).
export function getV4FinancialHealth(org: ApiOrganization): {
  tier: 'Strong' | 'Stable' | 'Inspiring' | null;
  operatingModel: string | null;
  peerCellSize: number | null;
} | null {
  const tier = (org.financial_health as 'Strong' | 'Stable' | 'Inspiring' | null) || null
  const model = org.operating_model || null
  const peerSize = org.peer_cell_size || null

  if (tier == null) return null
  return { tier, operatingModel: model, peerCellSize: peerSize }
}

export const TIER_COLORS: Record<TierName, string> = {
  Beacon:  '#B8902F',
  Lantern: '#C9A84C',
  Flame:   '#D4B968',
  Glow:    '#D9A876',
  Ember:   '#D9A876',
  Spark:   '#E8C896',
}

// Microcopy frames the lamp as a VISIBILITY JOURNEY, never a quality verdict.
// Lower tiers get the most generous, explicitly non-judgmental wording —
// they describe how much public data backs the profile, not the org's worth.
export const TIER_MICROCOPY: Record<TierName, string> = {
  Beacon:  'Most complete public picture. Top-quartile financial score, mission, website, and current 990 all on record.',
  Lantern: 'Strong public picture. Mission, website, financial context, and current 990 on record.',
  Flame:   'Public record found. Financial data and filing on record. Mission or website not yet confirmed.',
  Glow:    'Public record found. Limited financial data available. Reflects information availability, not the quality of its work.',
  Ember:   'Public record found. Limited financial data available. Reflects information availability, not the quality of its work.',
  Spark:   'Public record found. A registered nonprofit with little information available yet. A starting point, not a judgment.',
}

export interface TierCriterion {
  id: string
  label: string
  description: string
  status: 'met' | 'partial' | 'unavailable'
  shortFact: string
}

export function buildCriteria(org: ApiOrganization): TierCriterion[] {
  const has990Current = org.latest_tax_year != null && org.latest_tax_year >= 2022
  const has990Stale   = org.latest_tax_year != null && org.latest_tax_year >= 2020 && !has990Current
  const hasRevenue    = (org.total_revenue ?? 0) > 0
  const hasPeerScore  = org.peer_percentile != null
  const hasBroadScore = !hasPeerScore && org.ntee1_percentile != null

  return [
    {
      id: 'irs_registered',
      label: 'IRS registration',
      description: 'Recognized as a US nonprofit by the government',
      status: org.EIN ? 'met' : 'unavailable',
      shortFact: 'Public record found',
    },
    {
      id: '990_current',
      label: 'Annual report',
      description: 'Annual financial report filed within the past three years',
      status: has990Current ? 'met' : has990Stale ? 'partial' : 'unavailable',
      shortFact: 'Recent filing found',
    },
    {
      id: 'revenue_data',
      label: 'Revenue data',
      description: 'Reported annual revenue from public government or nonprofit records',
      status: hasRevenue ? 'met' : 'unavailable',
      shortFact: 'Financial data found',
    },
    {
      id: 'peer_score',
      label: 'Financial scale',
      description: 'Revenue and reserves compared to similar nonprofits. Not a quality or impact rating.',
      status: hasPeerScore ? 'met' : hasBroadScore ? 'partial' : 'unavailable',
      shortFact: 'Financial scale',
    },
    {
      id: 'financial_health',
      label: 'Financial health',
      description: org.merit_band
        ? `Financial report score: ${Math.round(org.merit_score ?? 0)}/100 (${org.merit_band})`
        : 'Computed from annual report expense, revenue, and asset detail when filed',
      status: org.merit_band
        ? (PASSING_BANDS.includes(org.merit_band) ? 'met' : 'partial')
        : 'unavailable',
      shortFact: org.merit_band ? `Financials: ${org.merit_band}` : 'Financials scored',
    },
    {
      id: 'mission',
      label: 'Mission statement',
      description: 'Publicly available mission statement on record',
      status: org.has_mission ? 'met' : 'unavailable',
      shortFact: 'Mission on file',
    },
    {
      id: 'website',
      label: 'Website',
      description: 'Active website address on record',
      status: org.has_website ? 'met' : 'unavailable',
      shortFact: 'Website listed',
    },
  ]
}

export function getNextTierPath(tier: TierName): string | null {
  switch (tier) {
    case 'Beacon':  return null
    case 'Lantern': return 'A top-quartile financial context score (75th percentile or higher) qualifies this org for Beacon.'
    case 'Flame':   return 'Add a mission statement and website. Once both are on public record, this org qualifies for Lantern.'
    case 'Glow':
    case 'Ember':   return 'A financial scale score is assigned as revenue and asset data accumulates in public records. Daanaa updates automatically.'
    case 'Spark':   return 'An annual financial report or revenue record on file moves this org to Glow.'
  }
}

export function getInlineVerifiedFact(org: ApiOrganization): string {
  const facts = buildCriteria(org)
    .filter(c => c.status === 'met')
    .map(c => `✓ ${c.shortFact}`)
  return facts.slice(0, 2).join(' · ')
}

const _TIER_NAMES = new Set<string>(['Beacon', 'Lantern', 'Flame', 'Glow', 'Ember', 'Spark'])

export function getTierFromOrg(org: ApiOrganization): TierName {
  if (org.merit_tier && _TIER_NAMES.has(org.merit_tier)) return org.merit_tier as TierName

  const hasEin     = !!org.EIN
  const has990     = org.latest_tax_year != null && org.latest_tax_year >= 2022
  const posRevenue = (org.total_revenue ?? 0) > 0
  const hasScore   = (org.peer_percentile ?? org.ntee1_percentile) != null
  const hasMission = !!org.has_mission
  const hasWebsite = !!org.has_website
  const bandOk     = org.merit_band == null || !GATE_BLOCKING_BANDS.includes(org.merit_band)

  if (!hasEin)                 return 'Spark'
  if (!has990 && !posRevenue)  return 'Spark'

  if (hasScore && (org.peer_percentile ?? org.ntee1_percentile ?? 0) >= 75 && hasMission && hasWebsite && has990 && posRevenue && bandOk) return 'Beacon'
  if (hasScore && hasMission && hasWebsite && has990 && posRevenue && bandOk) return 'Lantern'
  if (hasScore && has990 && posRevenue) return 'Flame'
  if (has990 || posRevenue)    return 'Ember'

  return 'Spark'
}

/** Dynamic trust summary for use in the giving flow — 2 facts max */
export function getTierSummary(tier: TierName, org: ApiOrganization): string {
  const score = org.peer_percentile ?? org.ntee1_percentile
  const has990 = (org.latest_tax_year ?? 0) >= 2022
  const parts: string[] = []
  if (has990) parts.push('Registered nonprofit · Annual report on file')
  else if (tier !== 'Spark') parts.push('Registered nonprofit')
  if (score != null && score >= 60) parts.push(`Larger financial footprint than ${Math.round(score)}% of comparable groups`)
  if (org.has_mission && org.has_website) parts.push('Full profile')
  return parts.slice(0, 2).join(' · ') || 'Registered nonprofit'
}
