import type { ApiOrganization } from '../data/api'

export type TierName = 'Beacon' | 'Lantern' | 'Flame' | 'Ember' | 'Spark'

export const TIER_COLORS: Record<TierName, string> = {
  Beacon:  '#B8902F',
  Lantern: '#C9A84C',
  Flame:   '#D4B968',
  Ember:   '#D9A876',
  Spark:   '#E8C896',
}

export const TIER_MICROCOPY: Record<TierName, string> = {
  Beacon:  'Top-quartile peer score, current 990, mission statement, and website — the strongest combination of data signals available from IRS public records.',
  Lantern: 'Current 990, mission statement, and website all on public record — full transparency data verified from public filings.',
  Flame:   'Current 990 on file and benchmarked within peer group. Mission or website not yet in public records.',
  Ember:   'IRS-confirmed 501(c)(3) with some financial data on record.',
  Spark:   'Registered 501(c)(3). No financial detail available in public records yet.',
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
      label: 'Peer-group score',
      description: 'Benchmarked against nonprofits of similar size and mission',
      status: hasPeerScore ? 'met' : hasBroadScore ? 'partial' : 'unavailable',
      shortFact: 'Peer scored',
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
    case 'Lantern': return 'Reach a top-quartile peer score (75th percentile or above within peer group).'
    case 'Flame':   return 'Add a mission statement and website — once both are on public record, this org qualifies for Lantern.'
    case 'Ember':   return 'A peer-group score is assigned as financial data accumulates in public records. MERIT updates automatically.'
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
  const hasRevenue = (org.total_revenue ?? 0) > 0
  const hasScore   = (org.peer_percentile ?? org.ntee1_percentile) != null
  const hasMission = !!org.has_mission
  const hasWebsite = !!org.has_website

  if (!hasEin)                return 'Spark'
  if (!has990 && !hasRevenue) return 'Spark'

  if (hasScore && (org.peer_percentile ?? org.ntee1_percentile ?? 0) >= 75 && hasMission && hasWebsite && has990) return 'Beacon'
  if (hasScore && hasMission && hasWebsite && has990) return 'Lantern'
  if (hasScore && has990)     return 'Flame'
  if (has990 || hasRevenue)   return 'Ember'

  return 'Spark'
}

/** Dynamic trust summary for use in the giving flow — 2 facts max */
export function getTierSummary(tier: TierName, org: ApiOrganization): string {
  const score = org.peer_percentile ?? org.ntee1_percentile
  const has990 = (org.latest_tax_year ?? 0) >= 2022
  const parts: string[] = []
  if (has990) parts.push('IRS verified · 990 on file')
  else if (tier !== 'Spark') parts.push('IRS registered')
  if (score != null && score >= 60) parts.push(`Top ${Math.max(1, 100 - Math.round(score))}% of peer orgs`)
  if (org.has_mission && org.has_website) parts.push('Full profile')
  return parts.slice(0, 2).join(' · ') || 'IRS registered'
}
