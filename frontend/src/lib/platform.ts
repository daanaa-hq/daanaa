/**
 * Platform isolation layer.
 *
 * All API calls and platform-specific behaviors funnel through here so that a
 * future Capacitor (iOS/Android) port only needs to swap this file, not hunt
 * every fetch() call in the codebase.
 *
 * Current target: web (PWA). Native: reserved for Phase 3.
 */

// Base URL for all API calls.
// In web mode: '' (relative, proxied by Vite in dev; same origin in prod).
// In native mode: set VITE_API_URL=https://api.daanaa.org in the Capacitor
// build environment.
export const API_BASE: string = import.meta.env.VITE_API_URL ?? '';

/**
 * Build a full URL for an API path.
 * Use this instead of string-concatenating API_BASE everywhere.
 */
export function apiUrl(path: string): string {
  return `${API_BASE}${path}`;
}

/**
 * True when running inside a Capacitor native wrapper (iOS or Android).
 * In web-only builds this is always false.
 */
export function isNative(): boolean {
  // Capacitor sets window.Capacitor.isNative; check defensively
  return typeof window !== 'undefined' &&
    !!(window as unknown as { Capacitor?: { isNative?: boolean } })
      .Capacitor?.isNative;
}

/**
 * Open an external URL safely.
 * On web: window.open with noopener/noreferrer.
 * On native (future): use Capacitor Browser plugin instead of window.open.
 */
export function openExternalUrl(url: string): void {
  if (isNative()) {
    // TODO Phase 3: CapacitorBrowser.open({ url })
    window.open(url, '_blank', 'noopener,noreferrer');
  } else {
    window.open(url, '_blank', 'noopener,noreferrer');
  }
}
