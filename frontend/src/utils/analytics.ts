// Privacy-safe, aggregate behavior events via self-hosted Plausible
// (stats.daanaa.org). No PII, no cookies — Plausible custom events are anonymous
// counts, never tied to a person (Stewardship P2). This is our genchi genbutsu
// instrument: it lets us OBSERVE whether design changes actually shift behavior
// (the PDCA "Check" step). See docs/DESIGN_PHILOSOPHY.md.
//
// Deliberately minimal: only the event name is sent — no EIN, no props — so
// there is nothing to correlate back to an individual. If aggregate breakdowns
// are ever needed (e.g. conversion by cause area), add a coarse, org-level prop
// then, not before (YAGNI).
export function trackEvent(event: string): void {
  try {
    ;(window as unknown as { plausible?: (e: string) => void }).plausible?.(event)
  } catch {
    // Analytics must never break the user experience.
  }
}
