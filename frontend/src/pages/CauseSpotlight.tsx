import { useEffect, useState, useMemo } from 'react'
import { Link, Navigate, useParams } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { useJsonLd, categoryPageSchema, breadcrumbSchema } from '../hooks/useJsonLd'
import { NTEE_CATEGORIES } from '../data/ntee'
import { FEATURED_META } from '../data/featuredCategory'
import { loadCauseSpotlights, type SpotlightData } from '../data/causeSpotlight'
import AddToWalletButton from '../components/AddToWalletButton'

export default function CauseSpotlight() {
  const { id = '' } = useParams<{ id: string }>()
  const code = id.toUpperCase()
  const cat = NTEE_CATEGORIES.find(c => c.id === code)
  const meta = FEATURED_META[code]
  const [data, setData] = useState<SpotlightData | null>(null)
  const [asOf, setAsOf] = useState<string>('')
  const [loading, setLoading] = useState(true)

  usePageMeta(
    cat ? `${cat.name} — Featured cause` : 'Featured cause',
    {
      description: cat ? `Discover ${cat.name} nonprofits on Daanaa. ${meta?.tagline ?? ''}` : '',
      ogImage: cat ? `https://daanaa.org/categories/${code}.png` : 'https://daanaa.org/og-image-v2.png',
    }
  )

  const schemas = useMemo(() => {
    if (!cat) return { category: null, breadcrumb: null }
    return {
      category: categoryPageSchema({
        name: `${cat.name} — Featured cause`,
        description: meta?.tagline || `Organizations working in ${cat.name}`,
        url: `https://daanaa.org/causes/${code}`,
      }),
      breadcrumb: breadcrumbSchema([
        { name: 'Home', url: 'https://daanaa.org' },
        { name: 'Featured causes', url: 'https://daanaa.org/causes' },
        { name: cat.name, url: `https://daanaa.org/causes/${code}` },
      ]),
    }
  }, [cat, code, meta])

  useJsonLd(schemas.category)
  useJsonLd(schemas.breadcrumb)

  useEffect(() => {
    loadCauseSpotlights()
      .then(f => { setData(f.categories[code] ?? null); setAsOf(f.generated_at || '') })
      .catch(() => setData(null))
      .finally(() => setLoading(false))
  }, [code])

  // Category exists but no spotlight data yet → fall back to the directory view.
  if (!cat) return <Navigate to="/directory" replace />
  if (loading) return <div className="min-h-[60vh] flex items-center justify-center text-cool-grey font-body">Loading…</div>
  if (!data) return <Navigate to={`/category/${code}`} replace />

  return (
    <div className="min-h-[100dvh]">
      {/* Hero */}
      <div className="bg-deep-navy">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12 pt-12 pb-14">
          <div className="flex items-center gap-2 mb-8">
            <Link to="/" className="font-body text-[12px] text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream">/</span>
            <span className="font-body text-[12px] text-muted-cream">Featured cause</span>
          </div>

          <div className="flex flex-col md:flex-row md:items-center gap-8 md:gap-12">
            <img
              src={`/categories/${code}.png`}
              alt={`${cat.name} cause`}
              className="w-28 h-28 md:w-40 md:h-40 object-contain shrink-0 mx-auto md:mx-0 drop-shadow-[0_8px_32px_rgba(201,169,110,0.28)]"
            />
            <div className="text-center md:text-left">
              <p className="font-body text-[12px] font-semibold tracking-[0.12em] text-soft-gold uppercase mb-2">
                Featured cause
              </p>
              <h1 className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(40px, 6vw, 68px)' }}>
                {cat.name}
              </h1>
              {meta?.tagline && (
                <p className="font-display italic text-pale-gold/90 mt-3 text-[19px] md:text-[22px]">
                  {meta.tagline}
                </p>
              )}
              {meta?.focus && (
                <div className="flex flex-wrap justify-center md:justify-start gap-2 mt-5">
                  {meta.focus.map(f => (
                    <span key={f} className="font-body text-[12px] px-3 py-1 rounded-full bg-soft-gold/10 border border-soft-gold/25 text-pale-gold">
                      {f}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* The landscape */}
      <div className="bg-warm-cream py-14 md:py-18">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12">
          <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">The landscape</span>
          <h2 className="font-display italic text-deep-navy mt-3 leading-[1.1]" style={{ fontSize: 'clamp(26px, 3.5vw, 40px)' }}>
            {data.totalOrgs.toLocaleString()} {cat.name.toLowerCase()} nonprofits the IRS recognizes
          </h2>
          <p className="mt-4 font-body text-[16px] text-cool-grey leading-[1.7] max-w-[680px]">
            Most are small and local. {data.withContext.toLocaleString()} have enough public data for a peer financial
            context score so far. The rest are still part of the picture, waiting to be seen.
          </p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
            <Stat value={data.totalOrgs.toLocaleString()} label="Organizations" />
            <Stat value={data.withContext.toLocaleString()} label="With financial context" />
            <Stat value={data.topStates[0].state} label="Most organizations" />
            <Stat value={`${(data.withContext / data.totalOrgs * 100).toFixed(0)}%`} label="Scored so far" />
          </div>

          <p className="mt-6 font-body text-[14px] text-cool-grey/80">
            Most common in{' '}
            {data.topStates.map((s, i) => (
              <span key={s.state}>
                <span className="font-semibold text-deep-navy">{s.state}</span> ({s.count.toLocaleString()})
                {i < data.topStates.length - 1 ? ', ' : '.'}
              </span>
            ))}
          </p>
        </div>
      </div>

      {/* Worth discovering */}
      <div className="bg-soft-gold/[0.05] py-14 md:py-18">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12">
          <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">Worth discovering</span>
          <h2 className="font-display italic text-deep-navy mt-3 leading-[1.1]" style={{ fontSize: 'clamp(26px, 3.5vw, 40px)' }}>
            The invisible ones
          </h2>
          <p className="mt-4 font-body text-[16px] text-cool-grey leading-[1.7] max-w-[680px]">
            Small {cat.name.toLowerCase()} organizations doing quiet, steady work, far from the spotlight.
          </p>
          <p className="mt-3 font-body text-[13px] text-cool-grey leading-[1.6] max-w-[680px]">
            How these are chosen: smaller organizations (under $500K in revenue) that rank near the top
            of their peer group in peer financial context, with a public mission on file. It is a starting
            point for your own research, not a verdict.{' '}
            <Link to="/methodology" className="text-soft-gold hover:underline">See how we measure this</Link>.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8">
            {data.featured.map(org => (
              <div
                key={org.ein}
                className="p-5 rounded-2xl bg-white border border-soft-gold/15 hover:border-soft-gold/40 hover:shadow-md transition-all group"
              >
                <div className="flex items-start justify-between gap-3 mb-2">
                  <Link
                    to={`/org/${org.ein}`}
                    className="font-display text-[18px] text-deep-navy leading-snug hover:text-soft-gold transition-colors"
                  >
                    {org.name}
                  </Link>
                  <span className="font-body text-[12px] text-cool-grey whitespace-nowrap shrink-0 pt-1">{org.city}, {org.state}</span>
                </div>
                <p className="mb-4 font-body text-[14px] text-cool-grey leading-[1.6]">{org.blurb}</p>
                <AddToWalletButton ein={org.ein} orgName={org.name} />
              </div>
            ))}
          </div>

          <div className="mt-10 text-center md:text-left">
            <Link
              to={`/directory?category=${code}`}
              className="inline-flex items-center gap-2.5 px-8 py-3.5 rounded-full bg-deep-navy text-warm-cream font-body text-[14px] font-bold hover:bg-navy-mid transition-colors"
            >
              Explore all {data.totalOrgs.toLocaleString()} {cat.name} nonprofits
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6" /></svg>
            </Link>
          </div>

          {asOf && (
            <p className="mt-10 font-body text-[12px] text-cool-grey">
              Based on public IRS data. Figures current as of {new Date(asOf).toLocaleDateString()}.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div className="bg-soft-gold/10 rounded-2xl p-5">
      <div className="font-display text-soft-gold leading-none" style={{ fontSize: 'clamp(26px, 3.5vw, 38px)' }}>{value}</div>
      <div className="mt-2 font-body text-[12px] text-cool-grey">{label}</div>
    </div>
  )
}
