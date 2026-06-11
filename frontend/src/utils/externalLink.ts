// Single source of truth for the public external-link CTA (legal posture
// 2026-06-10): Daanaa is a discovery platform — public surfaces link to the
// organization's official website, never to a donation page.

export interface PrimaryExternalLink {
  url: string | null
  label: 'Visit Official Website' | null
  type: 'website' | null
}

const NONE: PrimaryExternalLink = { url: null, label: null, type: null }

/** Normalize to a safe http(s) URL, or null if the value can't be trusted. */
export function normalizeExternalUrl(raw: string | null | undefined): string | null {
  const trimmed = (raw ?? '').trim()
  if (!trimmed) return null
  // Reject any explicit non-http scheme (javascript:, data:, mailto:, etc.)
  const candidate = /^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(trimmed) ? trimmed : `https://${trimmed}`
  try {
    const url = new URL(candidate)
    if (url.protocol !== 'http:' && url.protocol !== 'https:') return null
    if (!url.hostname.includes('.')) return null
    return url.href
  } catch {
    return null
  }
}

/**
 * The one public outbound CTA for an org: its official website when we have
 * one. (Social-profile fallback deliberately omitted — no social link data
 * exists yet; revisit when claiming collects it.)
 */
export function getPrimaryExternalLink(org: {
  website?: string | null
  website_url?: string | null
  official_website?: string | null
}): PrimaryExternalLink {
  const url = normalizeExternalUrl(org.official_website ?? org.website_url ?? org.website)
  if (url) return { url, label: 'Visit Official Website', type: 'website' }
  return NONE
}
