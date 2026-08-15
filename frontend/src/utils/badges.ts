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
  //
  // BUG FIX 2026-08-15: this badge gated only on org_status/irs_revoked,
  // never on org.tax_deductible itself — the actual computed signal.
  // taxDeductibleToStatus() (utils/taxDeductible.ts, added 2026-08-09)
  // already correctly maps tax_deductible === null/undefined to 'unknown'
  // ("a genuine data gap must never render as reassuring" — see
  // LESSONS.md 2026-08-09), and IrsEligibilityContext.tsx on this same
  // page already renders "Tax status not available" for that case — but
  // this badge kept showing the reassuring "Tax deductible" pill anyway
  // for any non-revoked org, contradicting that box directly on screen.
  // Found via a user-reported screenshot: a PTA org's page showed both
  // "Tax deductible" (this badge) and "Tax status not available" (the
  // detail box) at once. Only render this badge when tax_deductible is
  // explicitly true — the one case that's actually verified.
  if (org.tax_deductible === true) {
    badges.push({
      id: 'tax_deductible',
      // Copy reworked 2026-08-08 (founder-approved). Reached only when
      // tax_deductible is explicitly true, so the positive statement is
      // accurate — not merely "not known to be revoked."
      label: 'Tax deductible',
      detail: org.tax_deductible_checked_at
        ? `The IRS lists donations to this nonprofit as tax deductible. We check the IRS revocation list every day. Last checked ${org.tax_deductible_checked_at}.`
        : 'The IRS lists donations to this nonprofit as tax deductible. We check the IRS revocation list every day.',
      source: 'IRS Business Master File + IRS Auto-Revocation List',
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
  //
  // "Publishes" is an authorship claim — only true when the mission text
  // actually came from the org (claimed via our claim flow) or was pulled
  // from their own website (ai_web/lucido). org.has_mission is true even
  // when mission_source is 'ai_ntee' (a category template Daanaa generated
  // from the org's NTEE code, not written or published by the org at all)
  // or unset — asserting "this organization publishes its mission" in that
  // case would be an unverified claim stated as fact (Stewardship P3). When
  // provenance doesn't support authorship, we say nothing rather than guess.
  // Authorship claim requires org-authored or org-filed source. irs_990 is org-authored
  // because the organization filed it with the IRS (they wrote it on their 990 form).
  const missionIsOrgAttributed = org.mission_source === 'claimed' || org.mission_source === 'ai_web' || org.mission_source === 'lucido' || org.mission_source === 'irs_990'

  if (missionIsOrgAttributed && org.has_website) {
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
  } else if (missionIsOrgAttributed) {
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
