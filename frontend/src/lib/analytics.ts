// First-party, privacy-first analytics. No cookies, no IP, no persistent ID,
// no individual session record. We count events, never people. Fired with
// navigator.sendBeacon so it never blocks navigation. A per-browser-session
// flag (sessionStorage) lets the server mark one "session" per session start —
// still no server-side identity.

const API_BASE = import.meta.env.VITE_API_URL || ''

type EventType =
  | 'pageview' | 'search' | 'give_click' | 'save_org' | 'compare' | 'wallet_export'

function send(payload: Record<string, unknown>) {
  try {
    const body = JSON.stringify(payload)
    const url = `${API_BASE}/api/event`
    if (navigator.sendBeacon) {
      navigator.sendBeacon(url, new Blob([body], { type: 'application/json' }))
    } else {
      fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body, keepalive: true })
    }
  } catch {
    // analytics must never break the app — swallow everything
  }
}

let pageEnter = Date.now()

export function trackPageview(path: string) {
  let newSession = false
  try {
    if (!sessionStorage.getItem('da_session')) {
      sessionStorage.setItem('da_session', '1')
      newSession = true
    }
  } catch { /* private mode — just skip the session flag */ }
  pageEnter = Date.now()
  send({ type: 'pageview', path, new_session: newSession })
}

// Call when leaving a page to record aggregate dwell (seconds, capped).
export function trackDwell(path: string) {
  const dwell = Math.min(Math.round((Date.now() - pageEnter) / 1000), 3600)
  if (dwell > 0) send({ type: 'pageview', path, dwell })
}

// NOTE (2026-08-12): trackSearch() exists in the API but is NOT currently wired to any UI.
// Directory.tsx calls trackSearchMetrics() (aggregate query shapes) but never calls trackSearch()
// (individual query terms). This is by design — raw search terms were deferred pending infrastructure.
// See LESSONS.md 2026-08-12 for the full reasoning. When search term analysis is added to the
// feature backlog, this function will activate the analytics_search table on the backend.
export function trackSearch(term: string, path = '/directory') {
  send({ type: 'search', path, term })
}

// T12 Phase 1: Extended search tracking with result metrics
export interface SearchMetrics {
  query_length: number
  result_count: number
  zero_results: 'yes' | 'no'
  filters_applied: number
  mode?: 'keyword' | 'fused' | 'filtered'
}

export function trackSearchMetrics(metrics: SearchMetrics, path = '/directory') {
  send({ type: 'search', path, ...metrics })
}

export function trackEvent(type: Exclude<EventType, 'pageview' | 'search'>, path: string) {
  send({ type, path })
}
