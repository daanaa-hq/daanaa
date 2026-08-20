// Privacy-safe, aggregate behavior events via Plausible Analytics
// (privacy-first, cookieless service). No PII tracking — only coarse, org-level
// properties (revenue_band, section) aggregated by Plausible. Never EIN or identifiable data.
// This is our genchi genbutsu instrument: it lets us OBSERVE whether design changes
// actually shift behavior (the PDCA "Check" step). See docs/DESIGN_PHILOSOPHY.md.
//
// Stewardship P2 (privacy-safe) implementation:
// - Events logged to Plausible (no cookies, aggregate only)
// - Properties only org-level (revenue_band = Micro/Professional/Established)
// - Never user-identifiable, never individual EIN
// - Dashboards show aggregates (e.g., "At a Glance visibility % by band")
// See PRIVACY-INVARIANTS.md and https://plausible.io/privacy

import { logEvent } from '../lib/firebase'

interface EventParams {
  props?: Record<string, string | number>
}

export function trackEvent(event: string, opts?: EventParams): void {
  try {
    // Plausible logEvent is privacy-safe (no cookies, no third-party tracking)
    logEvent(event, opts?.props)
  } catch (e) {
    // Analytics must never break the user experience.
    console.debug('Event tracking failed:', e instanceof Error ? e.message : e)
  }
}

/**
 * Track when At a Glance component becomes visible on org detail page.
 * Used to measure if better display of leadership/stability context helps
 * small orgs reach parity with large orgs (Phase 3 → Gate A.1).
 * Stewardship P4 (small org fairness).
 */
export function trackAtAGlanceVisible(orgSize?: string | null): void {
  trackEvent('atagla nce_visible', {
    props: {
      section: 'at_a_glance',
      org_size: orgSize || 'unknown',
    }
  })
}

/**
 * Track when user bookmarks an org (adds to Giving Wallet).
 * Metadata: org size (Micro/Professional/Established).
 * Used to measure if Phase 3 improves decision-making for small orgs.
 * Stewardship P2 (privacy — no EIN stored, aggregate only).
 */
export function trackOrgBookmark(orgSize?: string | null): void {
  trackEvent('org_detail_bookmark', {
    props: {
      org_size: orgSize || 'unknown',
    }
  })
}

/**
 * Track if user engages with leadership or stability filters in search/directory.
 * Signal that context from At a Glance is influencing discovery behavior.
 * Stewardship P4 (small org visibility).
 */
export function trackSearchFilter(filterType: string): void {
  if (['leadership', 'stability', 'board_size', 'board_independence', 'org_age'].includes(filterType)) {
    trackEvent('search_filter_context', {
      props: {
        filter: filterType,
      }
    })
  }
}

/**
 * Track "Why this matches" visibility on search results or org detail.
 * Fires when SearchResultCard or WhyThisMatches component renders.
 * Segmented by org_size_bucket to measure if salience improves discovery
 * for small orgs (Phase 3B.3 measurement gate).
 * Stewardship P4 (small org fairness).
 */
export function trackWhyMatchesVisible(location: 'search' | 'org_detail', orgSize?: string | null): void {
  trackEvent('whyMatches:visible', {
    props: {
      location,
      org_size: orgSize || 'unknown',
    }
  })
}

/**
 * Track when user clicks CTA (Learn More, Save) from Why This Matches context.
 * Metadata: location (search vs. org detail), action (learn_more, save_to_wallet).
 * Used to measure if visible context drives CTR and wallet additions.
 * Stewardship P2 (privacy — no user or org identifier, aggregate only).
 */
export function trackWhyMatchesClicked(location: 'search' | 'org_detail', action: 'learn_more' | 'save_to_wallet', orgSize?: string | null): void {
  trackEvent('whyMatches:clicked', {
    props: {
      location,
      action,
      org_size: orgSize || 'unknown',
    }
  })
}
