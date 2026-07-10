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
  org: Pick<ApiOrganization, 'website_status' | 'website' | 'donate_url_status' | 'donate_url' | 'volunteer_url'> | null | undefined
): ActionRowLinks {
  const websiteVerified = org?.website_status === 'ok' || org?.website_status === 'beta'
  const link = websiteVerified ? getPrimaryExternalLink({ website: org?.website }) : { url: null, label: null, type: null }

  // Donate gate: status IN (beta, claimed) ONLY -- never donate_confidence,
  // which is NULL for ~99.7% of orgs with a URL (2026-07-10 eng review,
  // finding T3). 'beta' = AI-suggested, unverified by the org; 'claimed' =
  // org-verified via the claim flow.
  const donateOk = org?.donate_url_status === 'beta' || org?.donate_url_status === 'claimed'
  const donateUrl = donateOk ? normalizeExternalUrl(org?.donate_url) : null
  const volunteerUrl = normalizeExternalUrl(org?.volunteer_url)

  return {
    websiteUrl: link.url,
    websiteLabel: link.label,
    isWebsiteBeta: org?.website_status === 'beta',
    donateUrl,
    isDonateBeta: org?.donate_url_status === 'beta',
    volunteerUrl,
    hasAnyLink: Boolean(link.url || donateUrl || volunteerUrl),
  }
}
