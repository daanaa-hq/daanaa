import { getPrimaryExternalLink, normalizeExternalUrl } from './externalLink'
import type { ApiOrganization } from '../data/api'

// Pure gating logic for the org page action row (Website / Donate /
// Volunteer). Extracted 2026-07-10 (T9, eng review test coverage pass) --
// this logic previously lived inline in two separate places in
// OrganizationDetail.tsx (a DRY violation) and wasn't independently
// testable without rendering the whole page.
export interface ActionRowLinks {
  websiteUrl: string | null
  websiteLabel: string | null
  isWebsiteBeta: boolean
  donateUrl: string | null
  isDonateBeta: boolean
  volunteerUrl: string | null
  hasAnyLink: boolean
}

export function getActionRowLinks(
  org: Pick<ApiOrganization, 'website_status' | 'website' | 'donate_url_status' | 'donate_url' | 'volunteer_url' | 'tax_deductible'> | null | undefined
): ActionRowLinks {
  // Show website if: (1) verified as 'ok'/'beta', OR (2) URL exists but unchecked (NULL status)
  // NULL status = "we haven't checked this yet" — better to show it than hide real websites.
  const websiteVerified = (org?.website_status === 'ok' || org?.website_status === 'beta') || (org?.website && org?.website_status == null)
  const link = websiteVerified ? getPrimaryExternalLink({ website: org?.website }) : { url: null, label: null, type: null }

  // Donate gate: status IN (beta, claimed) ONLY -- never donate_confidence,
  // which is NULL for ~99.7% of orgs with a URL (2026-07-10 eng review,
  // finding T3). 'beta' = AI-suggested, unverified by the org; 'claimed' =
  // org-verified via the claim flow. Revocation check migrated 2026-08-09
  // from the dead irs_eligibility_status field (always undefined) to the
  // real tax_deductible boolean -- see LESSONS.md.
  const donateOk = org?.tax_deductible !== false && (org?.donate_url_status === 'beta' || org?.donate_url_status === 'claimed')
  const donateUrl = donateOk ? normalizeExternalUrl(org?.donate_url) : null
  const volunteerUrl = normalizeExternalUrl(org?.volunteer_url)

  return {
    websiteUrl: link.url,
    websiteLabel: link.label,
    isWebsiteBeta: Boolean(org?.website_status === 'beta' || (org?.website && org?.website_status == null)),
    donateUrl,
    isDonateBeta: org?.donate_url_status === 'beta',
    volunteerUrl,
    hasAnyLink: Boolean(link.url || donateUrl || volunteerUrl),
  }
}
