import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getOrganizations, type ApiOrganization } from '../data/api'
import { usePageMeta } from '../hooks/usePageMeta'

// "Meet the invisible" — the rethought Invisible-97% page. No WebGL. Real
// organizations, scroll-driven, mobile-native, leads straight to the directory.
// Preview route: /invisible-preview (does not replace /the-invisible-97 yet).

const FAMOUS = ['American Red Cross', 'St. Jude', 'Habitat for Humanity', 'Salvation Army', 'Feeding America']

function RevealCard({ org, i }: { org: ApiOrganization; i: number }) {
  const place = [org.CITY, org.STATE].filter(Boolean).join(', ')
  const mission = (org.mission || '').replace(/^[“"\s]+|[”"\s]+$/g, '')
  return (
    <Link
      to={`/org/${org.EIN}`}
      className="block rounded-2xl border border-white/10 bg-white/[0.04] hover:bg-white/[0.07] hover:border-soft-gold/40 transition-all p-6 opacity-0 animate-[fadeUp_0.6s_ease-out_forwards]"
      style={{ animationDelay: `${(i % 6) * 0.08}s` }}
    >
      <p className="font-display text-warm-cream text-[19px] leading-tight">{org.organization_name}</p>
      {place && <p className="font-body text-[12px] text-soft-gold/70 mt-1 tracking-[0.02em]">{place}</p>}
      {mission && (
        <p className="font-body text-[14px] text-muted-cream/85 leading-[1.6] mt-3 line-clamp-3">{mission}</p>
      )}
      <span className="inline-flex items-center gap-1 font-body text-[12px] text-soft-gold mt-4">
        See their page
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="9 18 15 12 9 6"/></svg>
      </span>
    </Link>
  )
}

export default function MeetInvisible() {
  usePageMeta(
    'The Invisible 97% — Daanaa',
    'Of 1.6 million American nonprofits, you have heard of almost none. Meet the small ones doing real good, finally findable.',
  )
  const [orgs, setOrgs] = useState<ApiOrganization[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getOrganizations({ hidden_gem: true, per_page: 18, sort: 'total_revenue', order: 'asc' })
      .then(d => setOrgs((d.organizations || []).filter(o => o.mission)))
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
          You have heard of almost none of them
        </h1>
        <p className="font-body text-[17px] text-muted-cream leading-[1.7] mt-6 max-w-[560px] mx-auto">
          There are 1.6 million nonprofits in America. A handful are household names.
          The rest do real, quiet good in places you will never read about.
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
        <p className="font-display italic text-warm-cream text-[26px]">And the ones you never see</p>
        <p className="font-body text-[14px] text-muted-cream/70 mt-2">Real organizations. Real missions. Found here, maybe for the first time.</p>
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
          1.6 million of them.<br />Most have never been found.
        </p>
        <Link
          to="/directory"
          className="inline-flex items-center gap-2 mt-8 px-9 py-4 rounded-full bg-soft-gold text-deep-navy font-body text-[15px] font-semibold hover:bg-bright-gold transition-colors"
        >
          Start exploring
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="9 18 15 12 9 6"/></svg>
        </Link>
      </section>

      <style>{`@keyframes fadeUp { from { opacity:0; transform: translateY(16px) } to { opacity:1; transform: translateY(0) } }`}</style>
    </div>
  )
}
