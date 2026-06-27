import { Link, Navigate, useParams } from 'react-router-dom'
import { useMemo, useState, useEffect } from 'react'
import { getNteeCategory, NTEE_CATEGORIES } from '../data/ntee'
import { usePageMeta } from '../hooks/usePageMeta'
import { useJsonLd, categoryPageSchema } from '../hooks/useJsonLd'
import { getOrganizations, type ApiOrganization } from '../data/api'
import { useWallet } from '../contexts/WalletContext'
import { CAUSE_ACCENT } from './Home'

const healthLabel: Record<string, string> = {
  HEALTHY: 'Financially healthy',
  STABLE: 'Financially stable',
  CAUTION: 'Needs support',
}
const healthClasses: Record<string, string> = {
  HEALTHY: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  STABLE:  'bg-blue-50 text-blue-700 border-blue-200',
  CAUTION: 'bg-amber-50 text-amber-700 border-amber-200',
}

export default function CategoryPage() {
  const { id } = useParams<{ id: string }>()
  const category = getNteeCategory(id || '')
  const { isInWallet, addEntry, removeEntry } = useWallet()
  const [orgs, setOrgs] = useState<ApiOrganization[]>([])
  const [total, setTotal] = useState(0)
  const [orgsLoading, setOrgsLoading] = useState(true)

  usePageMeta(
    category?.name ?? '',
    {
      description: category ? `Browse ${category.name} nonprofits on Daanaa. 501(c)(3) organizations from public IRS records with peer financial context and mission information.` : '',
      ogImage: category ? `https://daanaa.org/categories/${category.id}.png` : 'https://daanaa.org/og-image-v2.png',
    }
  )

  const categorySchema = useMemo(() => {
    if (!category) return null
    return categoryPageSchema({
      name: category.name,
      description: `Organizations working in ${category.name}. Find one that aligns with your values.`,
      url: `https://daanaa.org/categories/${category.id}`,
    })
  }, [category])

  useJsonLd(categorySchema)

  useEffect(() => {
    if (!category) return
    setOrgsLoading(true)
    getOrganizations({ ntee: category.id, per_page: 9, sort: 'ntee1_percentile', order: 'desc' })
      .then(r => { setOrgs(r.organizations); setTotal(r.total) })
      .catch(() => {})
      .finally(() => setOrgsLoading(false))
  }, [category?.id])

  if (!category) return <Navigate to="/directory" replace />

  return (
    <div className="min-h-[100dvh]">
      {/* Header */}
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 pt-12 pb-16">
          <div className="flex items-center gap-2 mb-8">
            <Link to="/" className="font-body text-[12px] text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream">/</span>
            <Link to="/" className="font-body text-[12px] text-muted-cream hover:text-warm-cream transition-colors">Causes</Link>
            <span className="text-muted-cream">/</span>
            <span className="font-body text-[12px] text-muted-cream">{category.name}</span>
          </div>
          <div className="max-w-[640px]">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-6 h-px bg-soft-gold/50" />
              <span className="font-body text-[11px] font-medium tracking-[0.10em] text-soft-gold uppercase">Cause</span>
            </div>
            <h1 className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(32px, 5vw, 60px)' }}>
              {category.name}
            </h1>
            <p className="mt-4 font-body text-[17px] leading-[1.6] text-muted-cream max-w-[560px]">
              Organizations working in this area. Find one that aligns with your values, explore their public record, and visit their official website.
            </p>
            <Link
              to={`/directory?category=${category.id}`}
              className="mt-8 inline-flex items-center gap-2 px-7 py-3 rounded-full bg-soft-gold text-deep-navy font-body text-[14px] font-semibold hover:bg-bright-gold transition-colors"
            >
              View organizations in {category.name}
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="9 18 15 12 9 6"/>
              </svg>
            </Link>
          </div>
        </div>
      </div>

      {/* Featured orgs */}
      <div className="bg-warm-cream py-14">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
          <div className="flex items-center justify-between mb-8">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <div className="w-6 h-px bg-soft-gold/50" />
                <span className="font-body text-[11px] font-medium tracking-[0.10em] text-soft-gold uppercase">Organizations</span>
              </div>
              <h2 className="font-display italic text-deep-navy" style={{ fontSize: 'clamp(20px, 3vw, 30px)' }}>
                {total > 0 ? `${total.toLocaleString()} organizations` : category.name}
              </h2>
            </div>
            <Link
              to={`/directory?category=${category.id}`}
              className="shrink-0 inline-flex items-center gap-1.5 font-body text-[13px] text-soft-gold hover:text-bright-gold transition-colors"
            >
              View all
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M7 17 17 7M17 7H8M17 7v9"/>
              </svg>
            </Link>
          </div>

          {orgsLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="bg-white rounded-2xl border border-light-grey p-5 animate-pulse">
                  <div className="h-4 bg-light-grey rounded w-3/4 mb-3" />
                  <div className="h-3 bg-light-grey rounded w-1/2 mb-4" />
                  <div className="h-3 bg-light-grey rounded w-full mb-1" />
                  <div className="h-3 bg-light-grey rounded w-5/6" />
                </div>
              ))}
            </div>
          ) : orgs.length > 0 ? (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                {orgs.map(org => {
                  const ein = org.EIN || ''
                  const saved = isInWallet(ein)
                  const signal = org.v5_context?.score?.health_signal ?? ''
                  const scoreV5 = org.v5_context?.score?.percentile ?? org.ntee1_percentile ?? 0
                  return (
                    <div key={ein} className="bg-white rounded-2xl border border-light-grey p-5 hover:border-soft-gold/30 transition-colors flex flex-col">
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <Link
                          to={`/org/${ein}`}
                          className="font-body text-[14px] font-semibold text-deep-navy hover:text-soft-gold transition-colors leading-snug flex-1"
                        >
                          {org.organization_name}
                        </Link>
                        <div className="flex items-center gap-1 shrink-0">
                          {org.website_status === 'ok' && org.website && (
                            <a
                              href={org.website}
                              target="_blank"
                              rel="noopener noreferrer"
                              title="Visit their website. From our public records, may not always be current."
                              aria-label={`Visit ${org.organization_name}'s website`}
                              onClick={e => e.stopPropagation()}
                              className="p-1.5 rounded-lg text-cool-grey hover:text-soft-gold transition-colors"
                            >
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M7 17 17 7M17 7H8M17 7v9"/></svg>
                            </a>
                          )}
                          <button
                            onClick={() => saved
                              ? removeEntry(ein)
                              : addEntry(ein)
                            }
                            title={saved ? 'In wallet' : 'Add to wallet'}
                            aria-pressed={saved}
                            className="p-1.5 rounded-lg transition-colors hover:bg-green-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-green-300"
                          >
                            <svg width="15" height="15" viewBox="0 0 24 24"
                              fill={saved ? '#22c55e' : 'none'} stroke="#22c55e"
                              strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                            </svg>
                          </button>
                        </div>
                      </div>
                      {(org.CITY || org.STATE) && (
                        <p className="font-body text-[11px] text-cool-grey mb-2">
                          {[org.CITY, org.STATE].filter(Boolean).join(', ')}
                        </p>
                      )}
                      {(org as any).mission && (
                        <div className="mb-3 flex-1">
                          <p className="font-body text-[12px] text-cool-grey italic line-clamp-2">
                            {(org as any).mission.replace(/^[""\s]+|[""\s]+$/g, '')}
                          </p>
                          {['ai_ntee','ai_haiku','ai_web','ai_generated'].includes(org.mission_source ?? '') && (
                            <span
                              title="Generated by AI from public records. Not confirmed by the organization."
                              className="mt-1 inline-block border border-cool-grey/40 text-cool-grey/60 rounded text-[9px] px-1.5 py-0.5 font-body tracking-[0.04em]"
                            >
                              AI assisted
                            </span>
                          )}
                        </div>
                      )}
                      <div className="flex items-center gap-2 flex-wrap mt-auto">
                        {signal && healthLabel[signal] && (
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold border font-body ${healthClasses[signal] ?? ''}`}>
                            {healthLabel[signal]}
                          </span>
                        )}
                        {org.is_hidden_gem && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold border bg-violet-50 text-violet-700 border-violet-200 font-body">
                            Hidden gem
                          </span>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
              <div className="text-center">
                <Link
                  to={`/directory?category=${category.id}`}
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-full border border-soft-gold/40 text-soft-gold font-body text-[13px] font-medium hover:bg-soft-gold/8 transition-colors"
                >
                  View all {total > 0 ? `${total.toLocaleString()} ` : ''}organizations in {category.name}
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="9 18 15 12 9 6"/>
                  </svg>
                </Link>
              </div>
            </>
          ) : null}
        </div>
      </div>

      {/* Subcategory grid */}
      <div className="bg-white py-14">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-6 h-px bg-soft-gold/50" />
            <span className="font-body text-[11px] font-medium tracking-[0.10em] text-soft-gold uppercase">Focus Areas</span>
          </div>
          <h2
            className="font-display italic text-deep-navy mb-8"
            style={{ fontSize: 'clamp(20px, 3vw, 30px)' }}
          >
            Narrow your focus
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {category.subs.map(sub => (
              <Link
                key={sub.code}
                to={`/directory?sub=${sub.code}`}
                className="group flex items-center gap-3.5 p-4 bg-white rounded-xl border border-light-grey hover:border-soft-gold/40 hover:shadow-card transition-all duration-200"
              >
                <div className="shrink-0 w-8 h-8 rounded-lg bg-soft-gold/10 flex items-center justify-center">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
                  </svg>
                </div>
                <div className="min-w-0 flex-1">
                  <p className="font-body text-[13px] font-medium text-deep-navy leading-snug group-hover:text-soft-gold transition-colors">{sub.name}</p>
                  <p className="font-body text-[11px] text-cool-grey mt-0.5">{sub.code}</p>
                </div>
                <svg
                  className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                  width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
                >
                  <polyline points="9 18 15 12 9 6"/>
                </svg>
              </Link>
            ))}
          </div>

          {/* Other categories */}
          <div className="mt-14 pt-8 border-t border-light-grey">
            <div className="flex items-center justify-between mb-5">
              <p className="font-body text-[12px] font-semibold tracking-[0.06em] text-cool-grey uppercase">
                Other categories
              </p>
              <Link to="/directory" className="font-body text-[12px] text-soft-gold hover:text-bright-gold transition-colors">
                View all ↗
              </Link>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
              {NTEE_CATEGORIES.filter(c => c.id !== category.id).map(cat => (
                <Link
                  key={cat.id}
                  to={`/category/${cat.id}`}
                  className="group flex flex-col items-center gap-1.5 p-3 rounded-xl border border-light-grey bg-white hover:border-soft-gold/40 hover:shadow-sm transition-all duration-150 text-center"
                >
                  <div className="w-9 h-9 rounded-lg bg-soft-gold/8 flex items-center justify-center">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
                    </svg>
                  </div>
                  <span className="font-body text-[11px] text-deep-navy/70 group-hover:text-deep-navy leading-tight transition-colors">
                    {cat.name}
                  </span>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
