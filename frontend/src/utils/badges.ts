import type { ApiOrganization } from '../data/api'

export type BadgeColor = 'green' | 'blue' | 'gold'
export type BadgeIcon = 'check-shield' | 'file-text' | 'trending-up' | 'star' | 'globe'

export interface OrgBadge {
  id: string
  label: string    // short — shown on card chips and detail page chips
  detail: string   // full plain-English explanation (shown when badge is expanded)
  source: string   // data source line
  color: BadgeColor
  icon: BadgeIcon
}

const SECTOR_NAMES: Record<string, string> = {
  A: 'Arts & Culture', B: 'Education', C: 'Environmental', D: 'Animal Welfare',
  E: 'Health', F: 'Mental Health', G: 'Disease Research', H: 'Medical Research',
  I: 'Crime & Legal', J: 'Employment', K: 'Food & Nutrition', L: 'Housing',
  M: 'Disaster Relief', N: 'Recreation', O: 'Youth Development',
  P: 'Human Services', Q: 'International', R: 'Civil Rights', S: 'Community Dev.',
  T: 'Philanthropy', U: 'Science & Tech', V: 'Social Science', W: 'Public Benefit',
  X: 'Faith-based', Y: 'Mutual Benefit',
}

export function getSectorName(ntee1: string | null): string {
  return SECTOR_NAMES[(ntee1 || '').toUpperCase()] || 'nonprofit'
}

export function getOrgBadges(org: ApiOrganization): OrgBadge[] {
  const badges: OrgBadge[] = []
  const score = org.peer_percentile ?? org.ntee1_percentile
  const taxYear = org.latest_tax_year
  const isScored = score != null && (org.data_source === 'propublica' || org.data_source === 'irs_soi')
  const sector = getSectorName(org.NTEE1)

  // 0. Hidden gem — small, financially healthy, mission-focused, under the radar.
  //    Surfaced first when present: this is the discovery moment.
  if (org.is_hidden_gem === 1) {
    badges.push({
      id: 'hidden_gem',
      label: 'Hidden gem',
      detail: 'A small organization doing exceptional work quietly — healthy reserves, most of every dollar reaches the mission, and far below most donors’ radar. The kind of org you won’t find on a top-charity list.',
      source: 'Daanaa ·revenue, reserves & program-spend analysis',
      color: 'gold',
      icon: 'star',
    })
  }

  // 1. Tax-deductible — every org in our DB is an active 501(c)(3)
  badges.push({
    id: 'tax_deductible',
    label: 'Tax-deductible',
    detail: 'Confirmed active 501(c)(3) in the IRS Business Master File. Your donation qualifies for a federal income tax deduction — keep your bank statement or request an acknowledgment letter for gifts of $250 or more.',
    source: 'IRS Business Master File',
    color: 'green',
    icon: 'check-shield',
  })

  // 2. Financial performance badges (scored orgs)
  if (isScored && score != null) {
    const pctAbove = Math.round(score)
    const pctBetter = Math.max(1, 100 - pctAbove)
    const peerLabel = org.peer_group
      ? (org.revenue_band ? `${org.revenue_band.toLowerCase()}-budget ${sector}` : sector)
      : sector

    const scoreNote = 'Financial scale compares revenue size and balance-sheet reserves against similar nonprofits — not program quality or governance. A lower score may reflect organizational structure (e.g. endowment-funded, pass-through) rather than weakness.'

    if (score >= 85) {
      badges.push({
        id: 'standout',
        label: `Larger financial footprint · ${sector}`,
        detail: `Financial context places this org among groups with a larger financial footprint among comparable ${peerLabel} nonprofits — based on revenue relative to peers (65%) and balance-sheet reserves (35%). ${scoreNote}`,
        source: org.data_source === 'propublica' ? 'IRS Form 990 · ProPublica Nonprofit Explorer' : 'IRS SOI Extract · Form 990',
        color: 'gold',
        icon: 'star',
      })
    } else if (score >= 70) {
      badges.push({
        id: 'strong_performer',
        label: `Larger financial footprint · ${sector}`,
        detail: `Financial context places this org among groups with a larger financial footprint among comparable ${peerLabel} nonprofits — revenue size within its peer group (65%) combined with a reserve-ratio score (35%). ${scoreNote}`,
        source: org.data_source === 'propublica' ? 'IRS Form 990 · ProPublica Nonprofit Explorer' : 'IRS SOI Extract · Form 990',
        color: 'gold',
        icon: 'trending-up',
      })
    } else if (score >= 50) {
      badges.push({
        id: 'peer_reviewed',
        label: 'Financial context available',
        detail: `Financial data is benchmarked against ${peerLabel} organizations of similar size. Ranked in the ${pctAbove}th percentile — typical financial footprint for similar groups. ${scoreNote}`,
        source: org.data_source === 'propublica' ? 'IRS Form 990 · ProPublica Nonprofit Explorer' : 'IRS SOI Extract · Form 990',
        color: 'blue',
        icon: 'trending-up',
      })
    } else {
      badges.push({
        id: 'peer_reviewed',
        label: 'Financial data found',
        detail: `Financial data is public and has been benchmarked against peer organizations — ranked in the ${pctAbove}th percentile on financial scale (revenue and reserves). ${scoreNote}`,
        source: org.data_source === 'propublica' ? 'IRS Form 990 · ProPublica Nonprofit Explorer' : 'IRS SOI Extract · Form 990',
        color: 'blue',
        icon: 'file-text',
      })
    }
  }

  // 3. 990 filing badge
  if (taxYear != null) {
    const isCurrent = taxYear >= new Date().getFullYear() - 2
    badges.push({
      id: 'tax_filing',
      label: `990 filed · FY ${taxYear}`,
      detail: isCurrent
        ? `Filed Form 990 for FY ${taxYear} — financial records are current and publicly available. The 990 is a full disclosure of revenue, expenses, programs, and governance filed annually with the IRS.`
        : `Most recent Form 990 is from FY ${taxYear}. Financial records are publicly available. The IRS allows filings up to 3 years after fiscal year end, so this may still be within the filing window.`,
      source: 'IRS BMF · Form 990',
      color: isCurrent ? 'blue' : 'blue',
      icon: 'file-text',
    })
  }

  // 4. Profile completeness
  if (org.has_mission && org.has_website) {
    badges.push({
      id: 'full_profile',
      label: 'Full profile',
      detail: 'This organization publishes its mission statement and maintains an active website. Both are accessible before you give — so you can read about their work, programs, and impact directly.',
      source: 'Daanaa ·ProPublica profile data',
      color: 'blue',
      icon: 'globe',
    })
  } else if (org.has_website) {
    badges.push({
      id: 'website_active',
      label: 'Website active',
      detail: 'This organization maintains an active website where you can learn more about their mission, programs, and team before giving.',
      source: 'Daanaa ·ProPublica profile data',
      color: 'blue',
      icon: 'globe',
    })
  } else if (org.has_mission) {
    badges.push({
      id: 'mission_published',
      label: 'Mission published',
      detail: 'This organization publishes its mission statement publicly — you can read about the work they do before making a gift.',
      source: 'Daanaa ·ProPublica profile data',
      color: 'blue',
      icon: 'globe',
    })
  }

  return badges
}

// Returns first 3 badges for card display — tax_deductible is always first
export function getCardBadges(org: ApiOrganization): OrgBadge[] {
  return getOrgBadges(org).slice(0, 3)
}
