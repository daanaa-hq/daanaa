import type { ApiOrganization } from '../data/api'

export type TierName = 'Beacon' | 'Lantern' | 'Flame' | 'Ember' | 'Spark'

// Financial bands from merit_scorer_v3_3 (only orgs with full 990 financials,
// ~4.7k). PASSING_BANDS = the "healthy" bands, used for the green/amber
// distinction in the financial-health criterion display only.
export const PASSING_BANDS = ['Exceptional', 'Strong', 'Solid']

// The tier gate is looser than the display: only the bottom band blocks
// Beacon/Lantern. Since ~99% of orgs have NO band, demoting only clearly-weak
// financials avoids penalising the minority that happen to have data.
const GATE_BLOCKING_BANDS = ['Concerns']

/** Real 0-100 financial-health score + band, only where 990 financials exist. */
export function getFinancialHealth(org: ApiOrganization): { score: number; band: string } | null {
  if (org.merit_score == null || org.merit_band == null) return null
  return { score: Math.round(org.merit_score), band: org.merit_band }
}

export const TIER_COLORS: Record<TierName, string> = {
  Beacon:  '#B8902F',
  Lantern: '#C9A84C',
  Flame:   '#D4B968',
  Ember:   '#D9A876',
  Spark:   '#E8C896',
}

// Microcopy frames the lamp as a VISIBILITY JOURNEY, never a quality verdict.
// Lower tiers get the most generous, explicitly non-judgmental wording —
// they describe how much public data backs the profile, not the org's worth.
export const TIER_MICROCOPY: Record<TierName, string> = {
  Beacon:  'Fully lit — current 990, mission, website, and verified financial health all on public record. The most complete picture donors can see.',
  Lantern: 'Brightly lit — current 990, mission, and website all on the public record.',
  Flame:   'Lit — a current 990 is on file. Mission or website not yet on the public record; easily added.',
  Ember:   'A faint light — this IRS-verified 501(c)(3) has limited public data so far. This reflects data availability, not the quality of its work.',
  Spark:   'Newly listed — an IRS-verified 501(c)(3) with little public data yet. A starting point, not a judgment; many excellent community organizations begin here.',
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
      description: 'Active 501(c)(3) on the IRS Business Master File',
      status: org.EIN ? 'met' : 'unavailable',
      shortFact: 'IRS verified',
    },
    {
      id: '990_current',
      label: '990 filing',
      description: 'Form 990 filed within the past three tax years',
      status: has990Current ? 'met' : has990Stale ? 'partial' : 'unavailable',
      shortFact: '990 current',
    },
    {
      id: 'revenue_data',
      label: 'Revenue data',
      description: 'Reported annual revenue from IRS or ProPublica records',
      status: hasRevenue ? 'met' : 'unavailable',
      shortFact: 'Revenue on file',
    },
    {
      id: 'peer_score',
      label: 'Financial scale',
      description: 'Revenue and reserves relative to similar nonprofits — not a quality or impact rating',
      status: hasPeerScore ? 'met' : hasBroadScore ? 'partial' : 'unavailable',
      shortFact: 'Financial scale',
    },
    {
      id: 'financial_health',
      label: 'Financial health',
      description: org.merit_band
        ? `990-derived score: ${Math.round(org.merit_score ?? 0)}/100 (${org.merit_band})`
        : 'Computed from 990 expense, revenue, and asset detail when filed',
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
    case 'Lantern': return 'Reach a top-quartile financial scale (75th percentile or above within peer group).'
    case 'Flame':   return 'Add a mission statement and website — once both are on public record, this org qualifies for Lantern.'
    case 'Ember':   return 'A financial scale score is assigned as revenue and asset data accumulates in public records. MERIT updates automatically.'
    case 'Spark':   return 'A current Form 990 or reported revenue on file moves this org to Ember.'
  }
}

export function getInlineVerifiedFact(org: ApiOrganization): string {
  const facts = buildCriteria(org)
    .filter(c => c.status === 'met')
    .map(c => `✓ ${c.shortFact}`)
  return facts.slice(0, 2).join(' · ')
}

const _TIER_NAMES = new Set<string>(['Beacon', 'Lantern', 'Flame', 'Ember', 'Spark'])

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
  if (has990) parts.push('IRS verified · 990 on file')
  else if (tier !== 'Spark') parts.push('IRS registered')
  if (score != null && score >= 60) parts.push(`Top ${Math.max(1, 100 - Math.round(score))}% financial scale`)
  if (org.has_mission && org.has_website) parts.push('Full profile')
  return parts.slice(0, 2).join(' · ') || 'IRS registered'
}
