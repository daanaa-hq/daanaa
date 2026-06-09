// Loader for the generated cause-spotlight data (/cause-spotlights.json).
//
// The JSON is produced by scripts/generate_cause_spotlights.py (read-only over
// the registry) and served as a static file — droplet-safe, no live API. Fetched
// once and cached. Creative copy (taglines, focus areas) is NOT here; it stays
// human-authored in featuredCategory.ts. This file is data only.

export interface SpotlightOrg {
  ein: string
  name: string
  city: string
  state: string
  blurb: string
}

export interface SpotlightData {
  id: string
  name: string
  totalOrgs: number
  withContext: number
  topStates: { state: string; count: number }[]
  featured: SpotlightOrg[]
}

interface SpotlightFile {
  generated_at: string
  categories: Record<string, SpotlightData>
}

let cache: Promise<SpotlightFile> | null = null

export function loadCauseSpotlights(): Promise<SpotlightFile> {
  if (!cache) {
    cache = fetch('/cause-spotlights.json').then(r => {
      if (!r.ok) throw new Error(`cause-spotlights.json ${r.status}`)
      return r.json()
    })
  }
  return cache
}
