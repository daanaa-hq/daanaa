import { useEffect } from 'react'
import { ALL_CATEGORIES } from '../data/categories'
import LampMark from './LampMark'
import { TIER_COLORS } from './TrustBadge'
import RevenueRangeInput from './RangeSlider'
import type { TierName } from './TrustBadge'

const FILTER_CATEGORIES = [
  { id: 'all', label: 'All', emoji: '' },
  ...ALL_CATEGORIES,
]

const US_STATES = [
  ['AL','Alabama'],['AK','Alaska'],['AZ','Arizona'],['AR','Arkansas'],['CA','California'],
  ['CO','Colorado'],['CT','Connecticut'],['DE','Delaware'],['FL','Florida'],['GA','Georgia'],
  ['HI','Hawaii'],['ID','Idaho'],['IL','Illinois'],['IN','Indiana'],['IA','Iowa'],
  ['KS','Kansas'],['KY','Kentucky'],['LA','Louisiana'],['ME','Maine'],['MD','Maryland'],
  ['MA','Massachusetts'],['MI','Michigan'],['MN','Minnesota'],['MS','Mississippi'],['MO','Missouri'],
  ['MT','Montana'],['NE','Nebraska'],['NV','Nevada'],['NH','New Hampshire'],['NJ','New Jersey'],
  ['NM','New Mexico'],['NY','New York'],['NC','North Carolina'],['ND','North Dakota'],['OH','Ohio'],
  ['OK','Oklahoma'],['OR','Oregon'],['PA','Pennsylvania'],['RI','Rhode Island'],['SC','South Carolina'],
  ['SD','South Dakota'],['TN','Tennessee'],['TX','Texas'],['UT','Utah'],['VT','Vermont'],
  ['VA','Virginia'],['WA','Washington'],['WV','West Virginia'],['WI','Wisconsin'],['WY','Wyoming'],
  ['DC','Washington DC'],['PR','Puerto Rico'],
] as const

const OTHER_TERRITORIES = [
  ['AS','American Samoa'],['GU','Guam'],['MP','Northern Mariana Islands'],['VI','U.S. Virgin Islands'],
] as const

const MILITARY_STATES = [
  ['AA','Armed Forces Americas'],['AE','Armed Forces Europe'],['AP','Armed Forces Pacific'],
] as const

const SCORE_TIERS: { id: TierName; label: string }[] = [
  { id: 'Beacon',  label: 'Beacon' },
  { id: 'Torch',   label: 'Torch +' },
  { id: 'Candle',  label: 'Candle +' },
]

interface FilterSheetProps {
  open: boolean
  onClose: () => void
  activeCategory: string
  stateFilter: string
  sortBy: string
  minRevenue: number
  maxRevenue: number
  scoreTier: string
  cause?: string
  onCategoryChange: (id: string) => void
  onStateChange: (state: string) => void
  onSortChange: (sort: string) => void
  onMinRevenueChange: (value: number) => void
  onMaxRevenueChange: (value: number) => void
  onScoreTierChange: (id: string) => void
  onCauseChange?: (v: string) => void
  onClearAll: () => void
  resultCount: number
}

export default function FilterSheet({
  open, onClose,
  activeCategory, stateFilter, sortBy, minRevenue, maxRevenue, scoreTier, cause = '',
  onCategoryChange, onStateChange, onSortChange, onMinRevenueChange, onMaxRevenueChange, onScoreTierChange,
  onCauseChange, onClearAll, resultCount,
}: FilterSheetProps) {
  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [open])

  if (!open) return null

  const hasRevenueFilter = minRevenue > 0 || maxRevenue < 500_000_000

  const activeCount = [
    activeCategory !== 'all',
    !!stateFilter,
    hasRevenueFilter,
    !!scoreTier,
    !!cause,
  ].filter(Boolean).length

  return (
    <div className="fixed inset-0 z-50 md:hidden flex flex-col justify-end">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} aria-hidden="true" />

      {/* Sheet */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Filters"
        className="relative bg-white rounded-t-2xl max-h-[85dvh] flex flex-col"
        style={{ animation: 'slideUp 0.25s ease-out' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 pt-4 pb-3 border-b border-light-grey shrink-0">
          <div className="flex items-center gap-2">
            <span className="font-display text-[18px] text-deep-navy">Filters</span>
            {activeCount > 0 && (
              <span className="min-w-[20px] h-5 flex items-center justify-center bg-soft-gold text-deep-navy text-[10px] font-bold rounded-full px-1.5">
                {activeCount}
              </span>
            )}
          </div>
          <button onClick={onClose} aria-label="Close filters" className="p-1.5 rounded-full hover:bg-light-grey transition-colors">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6B7280" strokeWidth="2" aria-hidden="true">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        {/* Scrollable body */}
        <div className="overflow-y-auto flex-1 px-5 py-4 space-y-6">

          {/* Cause — free text against the LLM cause tags */}
          {onCauseChange && (
            <div>
              <span className="font-body text-[11px] font-medium tracking-[0.08em] text-link-gold uppercase block mb-3">Cause</span>
              <input
                type="text"
                value={cause}
                onChange={e => onCauseChange(e.target.value)}
                placeholder="food bank, mental health…"
                className="w-full h-[46px] px-4 rounded-xl bg-warm-cream border border-light-grey font-body text-[14px] text-deep-navy outline-none focus:border-soft-gold transition-colors placeholder:text-cool-grey"
              />
            </div>
          )}

          {/* Category */}
          <div>
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-link-gold uppercase block mb-3">Category</span>
            <div className="flex flex-wrap gap-2">
              {FILTER_CATEGORIES.map(cat => (
                <button
                  key={cat.id}
                  onClick={() => onCategoryChange(cat.id)}
                  className="px-3.5 py-[7px] rounded-full font-body text-[13px] tracking-[0.01em] transition-all duration-150 border"
                  style={{
                    backgroundColor: activeCategory === cat.id ? '#C9A96E' : '#F5F0EB',
                    color: activeCategory === cat.id ? '#0A1628' : '#6B7280',
                    borderColor: activeCategory === cat.id ? '#C9A96E' : 'transparent',
                  }}
                >
                  {cat.emoji ? `${cat.emoji} ${cat.label}` : cat.label}
                </button>
              ))}
            </div>
          </div>

          {/* State */}
          <div>
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-link-gold uppercase block mb-3">State</span>
            <div className="relative">
              <select
                value={stateFilter}
                onChange={e => onStateChange(e.target.value)}
                className="w-full h-[46px] appearance-none pl-4 pr-10 rounded-xl bg-warm-cream border border-light-grey font-body text-[14px] text-deep-navy outline-none focus:border-soft-gold transition-colors"
              >
                <option value="">All States &amp; Territories</option>
                <optgroup label="States &amp; DC &amp; Puerto Rico">
                  {US_STATES.map(([abbr, name]) => (
                    <option key={abbr} value={abbr}>{abbr} · {name}</option>
                  ))}
                </optgroup>
                <optgroup label="Other U.S. Territories">
                  {OTHER_TERRITORIES.map(([abbr, name]) => (
                    <option key={abbr} value={abbr}>{abbr} · {name}</option>
                  ))}
                </optgroup>
                <optgroup label="Armed Forces">
                  {MILITARY_STATES.map(([abbr, name]) => (
                    <option key={abbr} value={abbr}>{abbr} · {name}</option>
                  ))}
                </optgroup>
              </select>
              <svg className="absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6B7280" strokeWidth="2"><polyline points="6 9 12 15 18 9"/></svg>
            </div>
          </div>

          {/* Revenue */}
          <div>
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-link-gold uppercase block mb-3">Revenue Range</span>
            <RevenueRangeInput
              min={minRevenue}
              max={maxRevenue}
              onMinChange={onMinRevenueChange}
              onMaxChange={onMaxRevenueChange}
            />
          </div>

          {/* Sort */}
          <div>
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-link-gold uppercase block mb-3">Sort By</span>
            <div className="flex gap-2">
              {[
                { value: 'organization_name', label: 'Name A to Z' },
                { value: 'total_revenue',     label: 'Revenue' },
              ].map(opt => (
                <button
                  key={opt.value}
                  onClick={() => onSortChange(opt.value)}
                  className="flex-1 py-2.5 rounded-xl font-body text-[13px] transition-all border"
                  style={{
                    backgroundColor: sortBy === opt.value ? '#0A1628' : '#F5F0EB',
                    color: sortBy === opt.value ? '#F5F0EB' : '#6B7280',
                    borderColor: 'transparent',
                  }}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-light-grey flex items-center gap-3 shrink-0">
          {activeCount > 0 && (
            <button
              onClick={() => { onClearAll(); onClose() }}
              className="font-body text-[14px] text-cool-grey hover:text-deep-navy transition-colors"
            >
              Clear all
            </button>
          )}
          <button
            onClick={onClose}
            className="flex-1 py-3 rounded-full bg-soft-gold text-deep-navy font-body text-[14px] font-semibold hover:bg-bright-gold transition-colors"
          >
            Show {resultCount.toLocaleString()} results
          </button>
        </div>
      </div>

      <style>{`
        @keyframes slideUp {
          from { transform: translateY(100%); }
          to   { transform: translateY(0); }
        }
      `}</style>
    </div>
  )
}
