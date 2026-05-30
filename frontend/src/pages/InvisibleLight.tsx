import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { getNteeCoverage, getStats, type NteeCoverage } from '../data/api'
import { NTEE_CATEGORIES } from '../data/ntee'
import LightRevealField, { type Cluster } from '../components/LightRevealField'

const NAME_BY_CODE: Record<string, string> = Object.fromEntries(
  NTEE_CATEGORIES.map(c => [c.id, c.name])
)

export default function InvisibleLight() {
  const [coverage, setCoverage] = useState<NteeCoverage[] | null>(null)
  const [totalRegistry, setTotalRegistry] = useState<number | null>(null)
  const [done, setDone] = useState(false)

  useEffect(() => {
    getNteeCoverage()
      .then(d => setCoverage(d.categories))
      .catch(() => setCoverage([]))
    getStats()
      .then(s => setTotalRegistry(s.total_organizations))
      .catch(() => setTotalRegistry(null))
  }, [])

  const clusters: Cluster[] = useMemo(() => {
    if (!coverage) return []
    return coverage
      .filter(c => c.code && c.total > 0 && NAME_BY_CODE[c.code])
      .sort((a, b) => b.total - a.total)
      .map(c => ({
        code: c.code,
        name: NAME_BY_CODE[c.code],
        total: c.total,
        coverage: c.coverage,
      }))
  }, [coverage])

  // Whole IRS registry (~1.6M), to match the count used across the rest of the site.
  // Rounds down to a clean "1.6 million" style figure.
  const registryLabel = useMemo(() => {
    if (!totalRegistry) return null
    return `${(Math.floor(totalRegistry / 100000) / 10).toFixed(1)} million`
  }, [totalRegistry])

  return (
    <div className="relative h-[100dvh] w-full overflow-hidden bg-deep-navy">
      {clusters.length > 0 && (
        <LightRevealField clusters={clusters} onComplete={() => setDone(true)} />
      )}

      {/* Intro copy — does not intercept the drag */}
      <div className="pointer-events-none absolute inset-x-0 top-0 z-30 px-6 pt-10 text-center sm:pt-14">
        <p className="font-body text-[11px] uppercase tracking-[0.22em] text-soft-gold/80">
          The invisible 97%
        </p>
        <h1 className="mx-auto mt-3 max-w-2xl font-display text-3xl leading-tight text-warm-cream sm:text-4xl">
          Only a few nonprofits ever get seen.
        </h1>
        <p className="mx-auto mt-3 max-w-md font-body text-[13px] text-muted-cream sm:text-[14px]">
          About 3% get all the attention. Drag the lamp across to reveal the{' '}
          {registryLabel ? `other ${registryLabel} ` : 'other 97% of '}
          nonprofits the IRS recognizes, by cause.
        </p>
      </div>

      {/* End CTA — appears once the field is fully lit */}
      <div
        className={`absolute inset-x-0 bottom-0 z-30 px-6 pb-9 text-center transition-all duration-700 ${
          done ? 'translate-y-0 opacity-100' : 'pointer-events-none translate-y-3 opacity-0'
        }`}
      >
        <p className="mb-3 font-display text-xl text-warm-cream">
          Now they have a place to be found.
        </p>
        <Link
          to="/directory"
          className="inline-block rounded-full bg-soft-gold px-6 py-2.5 font-body text-[14px] font-semibold text-deep-navy transition-colors hover:bg-bright-gold"
        >
          Explore every nonprofit →
        </Link>
      </div>
    </div>
  )
}
