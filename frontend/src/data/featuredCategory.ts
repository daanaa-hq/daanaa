// Bi-weekly featured NTEE category rotation.
//
// Runtime source of truth for which cause is spotlighted in the home banner.
// Mirrors brand/logos/rotation.json. As more category logos are produced and
// added to `rotation`, the cycle auto-expands — no category repeats until all
// available ones have had a turn.
//
// `rotation[0]` is the launch category shown until `firstChangeDate`; on that
// date the banner advances to `rotation[1]`, then one step every `cadenceDays`.

export interface FeaturedMeta {
  tagline: string
  focus?: string[]
}

export const FEATURED_FIRST_CHANGE = '2026-06-21'
export const FEATURED_CADENCE_DAYS = 14

// NTEE letters that currently have a logo asset in /public/categories/.
export const FEATURED_ROTATION = ['B', 'C', 'D', 'A'] as const

export const FEATURED_META: Record<string, FeaturedMeta> = {
  A: { tagline: 'Every voice deserves an audience.' },
  B: {
    tagline: 'Every mind has light. Every light can grow.',
    focus: ['Literacy & Learning', 'Youth Education', 'Mentorship', 'STEM & Innovation', 'Equal Access'],
  },
  C: { tagline: 'Every ecosystem is someone’s home.' },
  D: { tagline: 'Every creature deserves dignity.' },
}

const DAY_MS = 24 * 60 * 60 * 1000

export interface FeaturedCategory {
  id: string
  tagline: string
  focus?: string[]
  logo: string
}

/** The category to spotlight right now (or at a given date). */
export function getFeaturedCategory(now: Date = new Date()): FeaturedCategory {
  const first = new Date(`${FEATURED_FIRST_CHANGE}T00:00:00`)
  let idx = 0
  if (now >= first) {
    const periods = Math.floor((now.getTime() - first.getTime()) / (FEATURED_CADENCE_DAYS * DAY_MS))
    idx = (periods + 1) % FEATURED_ROTATION.length
  }
  const id = FEATURED_ROTATION[idx]
  return { id, ...FEATURED_META[id], logo: `/categories/${id}.png` }
}
