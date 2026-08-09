// Privacy-safe, aggregate behavior events via Firebase Analytics
// (Google's PDPA-compliant service). No PII tracking — only coarse, org-level
// properties (revenue_band, section) aggregated by Firebase. Never EIN or identifiable data.
// This is our genchi genbutsu instrument: it lets us OBSERVE whether design changes
// actually shift behavior (the PDCA "Check" step). See docs/DESIGN_PHILOSOPHY.md.
//
// Stewardship P2 (privacy-safe) implementation:
// - Events logged to Firebase (aggregated server-side)
// - Properties only org-level (revenue_band = Micro/Professional/Established)
// - Never user-identifiable, never individual EIN
// - Dashboards show aggregates (e.g., "At a Glance visibility % by band")
// See PRIVACY-INVARIANTS.md.

import { logEvent } from '../lib/firebase'

interface EventParams {
  props?: Record<string, string | number>
}

export function trackEvent(event: string, opts?: EventParams): void {
  try {
    // Firebase logEvent is already privacy-safe (aggregates server-side)
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
