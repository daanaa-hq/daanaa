import { Link, Navigate, useParams } from 'react-router-dom'
import { getNteeCategory, NTEE_CATEGORIES } from '../data/ntee'
import { usePageMeta } from '../hooks/usePageMeta'

export default function CategoryPage() {
  const { id } = useParams<{ id: string }>()
  const category = getNteeCategory(id || '')

  usePageMeta(
    category?.name ?? '',
    category ? `Browse ${category.name} nonprofits on Daanaa. 501(c)(3) organizations the IRS recognizes, scored by financial health and transparency.` : ''
  )

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
              Organizations working in this area. Find one that aligns with your values, understand their financial standing, and give where it matters to you.
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

      {/* Subcategory grid */}
      <div className="bg-warm-cream py-14">
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
