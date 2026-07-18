/**
 * Lets the single directory search bar double as a location search — a zip
 * code or "City, ST" typed into the main box routes to the real proximity
 * engine (near/radius_mi) instead of generic keyword FTS, which doesn't rank
 * by distance. Found 2026-07-18: searching "78701" returned the same loosely
 * name-ordered results as no query at all — the zip was being FTS-matched as
 * text, not resolved as a place.
 */
export function parseLocationQuery(raw: string): string | null {
  const v = raw.trim()
  if (/^\d{5}(-\d{4})?$/.test(v)) return v
  if (/^[A-Za-z][A-Za-z .'-]*,\s*[A-Za-z]{2}$/.test(v)) return v
  return null
}
