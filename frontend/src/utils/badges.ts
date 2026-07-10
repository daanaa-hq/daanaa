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

  // 1. Tax-deductible — stale assumption fixed 2026-07-10: this used to
  // unconditionally claim "every org in our DB is an active 501(c)(3)",
  // but revoked orgs ARE reachable on this page (direct/stale link ->
  // search.db fallback, see AnswerCard.tsx's revoked branch), and this
  // badge was rendering "Tax-deductible" directly under a banner saying
  // donations would NOT be tax-deductible. Caught by visual testing, not
  // code review -- the contradiction only shows up rendered.
  const isRevoked = org.org_status === 'revoked' || org.irs_revoked === 1
  if (!isRevoked) {
    badges.push({
      id: 'tax_deductible',
      label: 'Tax-deductible',
      detail: 'Confirmed active 501(c)(3) in the IRS Business Master File, listed as eligible to receive tax-deductible contributions.',
      source: 'IRS Business Master File',
      color: 'green',
      icon: 'check-shield',
    })
  }

  // 2. Financial performance — moved to detail page "How is this scored?" section
  // Card shows only lamp tier (primary signal). Financial Health details available on demand.
  // if (isScored && score != null) { ... }

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
