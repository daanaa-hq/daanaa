import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getOrganizations, type ApiOrganization } from '../data/api'
import { usePageMeta } from '../hooks/usePageMeta'
import { getPrimaryExternalLink } from '../utils/externalLink'

// "Meet the invisible" — the rethought Invisible-97% page. No WebGL. Real
// organizations, scroll-driven, mobile-native, leads straight to the directory.
// Preview route: /invisible-preview (does not replace /the-invisible-97 yet).

const FAMOUS = ['American Red Cross', 'St. Jude', 'Habitat for Humanity', 'Salvation Army', 'Feeding America']

function shuffle<T>(arr: T[]): T[] {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

function RevealCard({ org, i }: { org: ApiOrganization; i: number }) {
  const place = [org.CITY, org.STATE].filter(Boolean).join(', ')
  const mission = (org.mission || '').replace(/^[“"\s]+|[”"\s]+$/g, '')
  const link = getPrimaryExternalLink(org)
  return (
    <div
      className="flex flex-col rounded-2xl border border-white/10 bg-white/[0.04] hover:border-soft-gold/40 transition-all p-6 opacity-0 animate-[fadeUp_0.6s_ease-out_forwards]"
      style={{ animationDelay: `${(i % 6) * 0.08}s` }}
    >
      <Link to={`/org/${org.EIN}`} className="block group">
        <p className="font-display text-warm-cream text-[19px] leading-tight group-hover:text-soft-gold transition-colors">{org.organization_name}</p>
        {place && <p className="font-body text-[12px] text-soft-gold/70 mt-1 tracking-[0.02em]">{place}</p>}
        {mission && (
          <p className="font-body text-[14px] text-muted-cream/85 leading-[1.6] mt-3 line-clamp-3">{mission}</p>
        )}
      </Link>
      <div className="flex items-center gap-3 mt-auto pt-5 border-t border-white/5">
        {link.url && (
          <a
            href={link.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-soft-gold text-deep-navy font-body text-[13px] font-bold hover:bg-bright-gold transition-colors"
          >
            {link.label}
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M7 17 17 7M17 7H8M17 7v9"/></svg>
          </a>
        )}
        <Link to={`/org/${org.EIN}`} className="inline-flex items-center gap-1 font-body text-[12px] text-soft-gold/80 hover:text-soft-gold ml-auto">
          See their page
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="9 18 15 12 9 6"/></svg>
        </Link>
      </div>
    </div>
  )
}

export default function MeetInvisible() {
  usePageMeta(
    'The Invisible 97% — Daanaa',
    'Of 1.6 million tax-deductible American nonprofits, you have heard of almost none. Meet the ones doing real work, finally findable and ready to support.',
  )
  const [orgs, setOrgs] = useState<ApiOrganization[]>([])
  const [loading, setLoading] = useState(true)

  // Only orgs with a verified, live website — so every card here leads to the
  // org's own official site. Rotate across the pool by pulling a random page
  // each visit, then shuffle, so repeat visitors meet new orgs.
  useEffect(() => {
    const base = { has_website: true, per_page: 48, sort: 'total_revenue', order: 'asc' } as const
    const pick = (batch: { organizations?: ApiOrganization[] }) =>
      shuffle((batch.organizations || []).filter(o => o.mission && o.website)).slice(0, 18)
    getOrganizations({ ...base, page: 1 })
      .then(async first => {
        const pages = first.pages || 1
        let batch = first
        if (pages > 1) {
          const r = 1 + Math.floor(Math.random() * pages)
          if (r !== 1) { try { batch = await getOrganizations({ ...base, page: r }) } catch { /* keep first */ } }
        }
        let chosen = pick(batch)
        if (chosen.length < 6 && batch !== first) chosen = pick(first) // fallback if the random page was thin
        setOrgs(chosen)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="bg-deep-navy min-h-screen">
      {/* Hero */}
      <section className="max-w-[820px] mx-auto px-6 pt-28 pb-16 text-center">
        <span className="inline-flex items-center px-3 py-1 rounded-full bg-soft-gold/10 border border-soft-gold/25 font-body text-[11px] font-semibold tracking-[0.12em] uppercase text-soft-gold mb-7">
          The invisible 97%
        </span>
        <h1 className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(34px, 6vw, 68px)' }}>
          Many are doing real work. Most are just invisible.
        </h1>
        <p className="font-body text-[17px] text-muted-cream leading-[1.7] mt-6 max-w-[560px] mx-auto">
          Of 1.6 million tax-deductible nonprofits in America, most operate without the visibility of household names. Many simply haven't published financial data yet. That doesn't make their work less real. Let's change that.
        </p>
      </section>

      {/* The few everyone knows */}
      <section className="max-w-[820px] mx-auto px-6 pb-4 text-center">
        <p className="font-body text-[12px] tracking-[0.1em] uppercase text-cool-grey/50 mb-4">The few everyone knows</p>
        <div className="flex flex-wrap justify-center gap-x-6 gap-y-2">
          {FAMOUS.map(n => (
            <span key={n} className="font-display italic text-[20px] text-cool-grey/40">{n}</span>
          ))}
        </div>
      </section>

      {/* The divider line */}
      <div className="max-w-[820px] mx-auto px-6 py-14 text-center">
        <div className="w-px h-12 bg-gradient-to-b from-transparent via-soft-gold/40 to-transparent mx-auto mb-4" />
        <p className="font-display italic text-warm-cream text-[26px]">The rest of the story</p>
        <p className="font-body text-[14px] text-muted-cream/70 mt-2">Organizations that deserve to be found and supported.</p>
      </div>

      {/* Real invisible orgs */}
      <section className="max-w-[1000px] mx-auto px-6 pb-20">
        {loading ? (
          <div className="text-center py-16">
            <div className="w-6 h-6 rounded-full border-2 border-soft-gold border-t-transparent animate-spin mx-auto" />
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {orgs.map((o, i) => <RevealCard key={o.EIN} org={o} i={i} />)}
          </div>
        )}
      </section>

      {/* CTA */}
      <section className="max-w-[820px] mx-auto px-6 pb-32 text-center">
        <p className="font-display italic text-warm-cream leading-[1.15]" style={{ fontSize: 'clamp(26px, 4vw, 40px)' }}>
          1.6 million nonprofits doing the work.<br />You just discovered 18 of them.
        </p>
        <Link
          to="/directory"
          className="inline-flex items-center gap-2 mt-8 px-9 py-4 rounded-full bg-soft-gold text-deep-navy font-body text-[15px] font-semibold hover:bg-bright-gold transition-colors"
        >
          Explore more
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="9 18 15 12 9 6"/></svg>
        </Link>
      </section>

      <style>{`@keyframes fadeUp { from { opacity:0; transform: translateY(16px) } to { opacity:1; transform: translateY(0) } }`}</style>
    </div>
  )
}
