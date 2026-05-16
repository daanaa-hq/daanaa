import { Link, Navigate, useParams } from 'react-router-dom'
import { getNteeCategory, NTEE_CATEGORIES } from '../data/ntee'
import { usePageMeta } from '../hooks/usePageMeta'

export default function CategoryPage() {
  const { id } = useParams<{ id: string }>()
  const category = getNteeCategory(id || '')

  usePageMeta(
    category?.name ?? '',
    category ? `Browse ${category.name} nonprofits on MERIT — IRS-verified 501(c)(3) organizations scored by financial health and transparency.` : ''
  )

  if (!category) return <Navigate to="/directory" replace />

  const [gradFrom, gradTo] = category.gradient

  return (
    <div className="min-h-[100dvh]">
      {/* Hero banner */}
      <div
        className="pt-[72px] pb-16 flex flex-col items-center justify-center text-center px-6"
        style={{ background: `linear-gradient(135deg, ${gradFrom}, ${gradTo})` }}
      >
        <span className="text-[72px] leading-none mb-4 mt-10">{category.emoji}</span>
        <h1
          className="font-display italic text-white tracking-[-0.01em]"
          style={{ fontSize: 'clamp(32px, 5vw, 52px)' }}
        >
          {category.name}
        </h1>
        <p className="mt-3 font-body text-[15px] text-white/70">
          {category.subs.length} subcategories
        </p>
        <Link
          to={`/directory?category=${category.id}`}
          className="mt-7 inline-flex items-center gap-2 px-7 py-3 rounded-full bg-white text-deep-navy font-body text-[14px] font-semibold hover:bg-warm-cream transition-colors shadow-md"
        >
          Browse all {category.name} nonprofits
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </Link>
      </div>

      {/* Subcategory grid */}
      <div className="bg-warm-cream py-14">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">
          <div className="flex items-center justify-between mb-8 flex-wrap gap-3">
            <div>
              <Link to="/" className="font-body text-[12px] text-cool-grey hover:text-deep-navy transition-colors">
                Home
              </Link>
              <span className="text-cool-grey/40 mx-2">/</span>
              <span className="font-body text-[12px] text-deep-navy">{category.name}</span>
            </div>
          </div>

          <h2
            className="font-display italic text-deep-navy mb-6"
            style={{ fontSize: 'clamp(20px, 3vw, 30px)' }}
          >
            Explore by subcategory
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {category.subs.map(sub => (
              <Link
                key={sub.code}
                to={`/directory?sub=${sub.code}`}
                className="group flex items-center gap-3.5 p-4 bg-white rounded-xl border border-light-grey hover:border-soft-gold/40 hover:shadow-card transition-all duration-200"
              >
                {/* Color swatch */}
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center text-[20px] shrink-0"
                  style={{ background: `linear-gradient(135deg, ${gradFrom}30, ${gradTo}30)` }}
                >
                  {category.emoji}
                </div>
                <div className="min-w-0">
                  <p className="font-body text-[13px] font-medium text-deep-navy leading-snug">{sub.name}</p>
                  <p className="font-body text-[11px] text-cool-grey/50 mt-0.5">{sub.code}</p>
                </div>
                <svg
                  className="shrink-0 ml-auto opacity-0 group-hover:opacity-100 transition-opacity"
                  width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
                >
                  <polyline points="9 18 15 12 9 6"/>
                </svg>
              </Link>
            ))}
          </div>

          {/* Other categories */}
          <div className="mt-14 pt-8 border-t border-light-grey">
            <div className="flex items-center justify-between mb-5">
              <p className="font-body text-[12px] font-semibold tracking-[0.06em] text-cool-grey/50 uppercase">
                Other categories
              </p>
              <Link to="/" className="font-body text-[12px] text-soft-gold hover:text-bright-gold transition-colors">
                View all ↗
              </Link>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
              {NTEE_CATEGORIES.filter(c => c.id !== category.id).map(cat => {
                const [from, to] = cat.gradient
                return (
                  <Link
                    key={cat.id}
                    to={`/category/${cat.id}`}
                    className="group flex flex-col items-center gap-1.5 p-3 rounded-xl border border-light-grey bg-white hover:border-soft-gold/40 hover:shadow-sm transition-all duration-150 text-center"
                  >
                    <div
                      className="w-9 h-9 rounded-lg flex items-center justify-center text-[18px]"
                      style={{ background: `linear-gradient(135deg, ${from}30, ${to}30)` }}
                    >
                      {cat.emoji}
                    </div>
                    <span className="font-body text-[11px] text-deep-navy/70 group-hover:text-deep-navy leading-tight transition-colors">
                      {cat.name}
                    </span>
                  </Link>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
