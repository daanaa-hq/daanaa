import React, { useState, useEffect, useRef } from 'react'
import { usePageMeta } from '../hooks/usePageMeta'
import { useSearchParams, Link } from 'react-router-dom'
import OrgCard, { OrgCardRow } from '../components/OrgCard'
import FilterSheet from '../components/FilterSheet'
import SearchBar from '../components/SearchBar'
import { useApi } from '../hooks/useApi'
import { useSavedOrgs } from '../hooks/useSavedOrgs'
import { getOrganizations } from '../data/api'
import type { ApiOrganization } from '../data/api'
import { getTierSummary, getTierFromOrg, TIER_COLORS } from '../components/TrustBadge'
import LampMark from '../components/LampMark'
import type { TierName } from '../components/TrustBadge'
import { RAIL_CATEGORIES, ALL_CATEGORIES, NTEE_SUBCATEGORIES } from '../data/categories'

const FILTER_CATEGORIES = [
  { id: 'all', label: 'All' },
  ...ALL_CATEGORIES.filter(c => ['B','E','A','C','P','S','D','Q','X','K'].includes(c.id)),
]

const SORT_OPTIONS = [
  { id: 'merit_score', label: 'Peer Financial Context' },
  { id: 'organization_name', label: 'Name A to Z' },
  { id: 'total_revenue', label: 'Revenue' },
]

// Small first. This is the mission: the smallest groups are the hardest to find.
const REVENUE_PRESETS = [
  { id: 'tiny',        label: 'Tiny (under $50K)',          min: undefined,   max: 49_999 },
  { id: 'grassroots',  label: 'Grassroots ($50K to $250K)', min: 50_000,      max: 249_999 },
  { id: 'community',   label: 'Community ($250K to $1M)',   min: 250_000,     max: 999_999 },
  { id: 'established', label: 'Established ($1M to $10M)',   min: 1_000_000,   max: 9_999_999 },
  { id: 'large',       label: 'Large ($10M to $100M)',      min: 10_000_000,  max: 99_999_999 },
  { id: 'national',    label: 'National (over $100M)',      min: 100_000_000, max: undefined },
] as const

const SCORE_TIERS: { id: TierName; label: string }[] = [
  { id: 'Beacon',  label: 'Beacon' },
  { id: 'Lantern', label: 'Lantern +' },
  { id: 'Flame',   label: 'Flame +' },
]

type RevenueId = typeof REVENUE_PRESETS[number]['id'] | ''
type ScoreTierId = TierName | ''

function hasKnownDataSource(src: string | null) {
  return src === 'propublica' || src === 'irs_soi'
}

function OrgCardApi({
  org,
  isSaved,
  onToggleSave,
  listView = false,
}: {
  org: ApiOrganization
  isSaved: boolean
  onToggleSave: (e: React.MouseEvent, ein: string, meta?: { name: string; city?: string; state?: string; ntee1?: string }) => void
  listView?: boolean
}) {
  const scored = hasKnownDataSource(org.data_source) && (org.peer_percentile ?? org.ntee1_percentile) !== null
  const cardOrg = {
    id: org.EIN,
    name: org.organization_name,
    ein: org.EIN,
    city: org.CITY || '',
    state: org.STATE || '',
    category: org.NTEE1 || '',
    subcategory: org.NTEECC || org.NTEE1 || '',
    meritScore: Math.round(org.peer_percentile ?? org.ntee1_percentile ?? 0),
    hasScore: scored,
    revenueBand: org.revenue_band ?? null,
    dataSource: org.data_source ?? null,
    latestTaxYear: org.latest_tax_year ?? null,
    ntee1TotalOrgs: org.ntee1_total_orgs ?? null,
    hasMission: org.has_mission ?? null,
    hasWebsite: org.has_website ?? null,
    revenue: org.total_revenue ?? 0,
    assets: 0,
    employees: 0,
    founded: 0,
    mission: '',
    programs: [] as string[],
    leadership: [] as { name: string; title: string; initials: string }[],
    boardSize: 0,
    revenueTrend: [] as { year: number; amount: number }[],
    programEfficiency: 0,
    fundraisingRatio: 0,
    operatingReserve: 0,
    transparencyScore: 0,
  }
  const summary = getTierSummary(getTierFromOrg(org), org)
  const props = {
    org: cardOrg,
    isSaved,
    onToggleSave: (e: React.MouseEvent, ein: string, meta?: { name: string; city?: string; state?: string; ntee1?: string }) => onToggleSave(e, ein, meta),
    apiOrg: org,
    trustSummary: summary,
  }
  return listView ? <OrgCardRow {...props} /> : <OrgCard {...props} />
}

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
  ['DC','Washington DC'],
] as const

// ── Filter Rail (desktop sidebar) ────────────────────────────────────────────

function FilterRail({
  activeCategories,
  subFilter,
  stateFilter,
  sortBy,
  revenueFilter,
  scoreTier,
  hiddenGem,
  directLink,
  needsFunding,
  cause,
  onCategoryChange,
  onSubChange,
  onStateChange,
  onSortChange,
  onRevenueChange,
  onScoreTierChange,
  onHiddenGemChange,
  onDirectLinkChange,
  onNeedsFundingChange,
  onCauseChange,
  onClearAll,
  resultCount,
}: {
  activeCategories: string[]
  subFilter: string
  stateFilter: string
  sortBy: string
  revenueFilter: RevenueId
  scoreTier: ScoreTierId
  hiddenGem: boolean
  directLink: boolean
  needsFunding: boolean
  cause: string
  onCategoryChange: (id: string) => void
  onSubChange: (code: string) => void
  onStateChange: (s: string) => void
  onSortChange: (s: string) => void
  onRevenueChange: (id: RevenueId) => void
  onScoreTierChange: (id: ScoreTierId) => void
  onHiddenGemChange: (v: boolean) => void
  onDirectLinkChange: (v: boolean) => void
  onNeedsFundingChange: (v: boolean) => void
  onCauseChange: (v: string) => void
  onClearAll: () => void
  resultCount: number
}) {
  const hasActive = activeCategories.length > 0 || !!stateFilter || sortBy !== 'merit_score' || !!subFilter || !!revenueFilter || !!scoreTier || hiddenGem || directLink || needsFunding || !!cause
  const subcats = activeCategories.length === 1 ? (NTEE_SUBCATEGORIES[activeCategories[0]] ?? []) : []

  return (
    <aside className="hidden lg:block w-[220px] shrink-0">
      <div className="sticky top-[88px] max-h-[calc(100vh-100px)] overflow-y-auto pb-4">
        <div className="flex items-center justify-between mb-4">
          <span className="font-body text-[11px] font-semibold tracking-[0.08em] uppercase text-cool-grey">Filters</span>
          {hasActive && (
            <button onClick={onClearAll} className="font-body text-[11px] text-soft-gold hover:text-bright-gold transition-colors">
              Clear all
            </button>
          )}
        </div>

        {/* Hidden gems — discovery toggle */}
        <button
          onClick={() => onHiddenGemChange(!hiddenGem)}
          className="w-full flex items-start gap-2.5 px-3 py-3 rounded-xl mb-4 border transition-all duration-150 text-left"
          style={{
            backgroundColor: hiddenGem ? 'rgba(201,169,110,0.12)' : 'rgba(201,169,110,0.04)',
            borderColor: hiddenGem ? '#C9A96E' : 'rgba(201,169,110,0.25)',
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill={hiddenGem ? '#C9A96E' : 'none'} stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0 mt-0.5">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
          </svg>
          <span>
            <span className="block font-body text-[13px] font-semibold" style={{ color: hiddenGem ? '#A8853E' : '#6B7280' }}>
              Hidden gems
            </span>
            <span className="block font-body text-[11px] text-cool-grey/70 leading-[1.4] mt-0.5">
              Small orgs doing exceptional work quietly
            </span>
          </span>
        </button>

        {/* Needs funding soon */}
        <button
          onClick={() => onNeedsFundingChange(!needsFunding)}
          className="w-full flex items-start gap-2.5 px-3 py-3 rounded-xl mb-4 border transition-all duration-150 text-left"
          style={{
            backgroundColor: needsFunding ? 'rgba(239,68,68,0.10)' : 'rgba(239,68,68,0.03)',
            borderColor: needsFunding ? '#EF4444' : 'rgba(239,68,68,0.25)',
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill={needsFunding ? '#EF4444' : 'none'} stroke="#EF4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0 mt-0.5">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <span>
            <span className="block font-body text-[13px] font-semibold" style={{ color: needsFunding ? '#B91C1C' : '#6B7280' }}>
              Needs funding soon
            </span>
            <span className="block font-body text-[11px] text-cool-grey/70 leading-[1.4] mt-0.5">
              Less than 6 months of operating reserves
            </span>
          </span>
        </button>

        {/* Direct donate link available */}
        <button
          onClick={() => onDirectLinkChange(!directLink)}
          className="w-full flex items-start gap-2.5 px-3 py-3 rounded-xl mb-4 border transition-all duration-150 text-left"
          style={{
            backgroundColor: directLink ? 'rgba(74,222,128,0.08)' : 'rgba(74,222,128,0.03)',
            borderColor: directLink ? '#4ADE80' : 'rgba(74,222,128,0.25)',
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={directLink ? '#4ADE80' : '#6B7280'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0 mt-0.5">
            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
          </svg>
          <span>
            <span className="block font-body text-[13px] font-semibold" style={{ color: directLink ? '#16a34a' : '#6B7280' }}>
              Direct link available
            </span>
            <span className="block font-body text-[11px] text-cool-grey/70 leading-[1.4] mt-0.5">
              Give directly — no hunting for a donate page
            </span>
          </span>
        </button>

        {/* Cause — free text against the LLM cause tags */}
        <div className="mb-4">
          <p className="font-body text-[11px] font-semibold tracking-[0.08em] uppercase text-cool-grey/50 mb-2 px-2.5">Cause</p>
          <div className="relative px-0.5">
            <input
              type="text"
              value={cause}
              onChange={e => onCauseChange(e.target.value)}
              placeholder="food bank, mental health…"
              className="w-full h-[38px] pl-3 pr-8 rounded-lg bg-warm-cream border border-light-grey font-body text-[13px] text-deep-navy outline-none focus:border-soft-gold transition-colors placeholder:text-cool-grey/60"
            />
            {!!cause && (
              <button
                onClick={() => onCauseChange('')}
                aria-label="Clear cause"
                className="absolute right-2 top-1/2 -translate-y-1/2 text-cool-grey/60 hover:text-deep-navy transition-colors"
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            )}
          </div>
        </div>

        {/* Category */}
        <div className="mb-4">
          <p className="font-body text-[11px] font-semibold tracking-[0.08em] uppercase text-cool-grey/50 mb-2 px-2.5">Category</p>
          <div className="space-y-0.5">
            {RAIL_CATEGORIES.map(cat => {
              const isActive = cat.id === 'all' ? activeCategories.length === 0 : activeCategories.includes(cat.id)
              return (
                <button
                  key={cat.id}
                  onClick={() => onCategoryChange(cat.id)}
                  className="w-full flex items-center justify-between px-2.5 py-[7px] rounded-lg transition-all duration-100 text-left"
                  style={{
                    backgroundColor: isActive ? 'rgba(201,169,110,0.10)' : 'transparent',
                    color: isActive ? '#C9A96E' : '#6B7280',
                  }}
                >
                  <span className="flex items-center gap-2 font-body text-[13px]" style={{ fontWeight: isActive ? '600' : '400' }}>
                    {cat.emoji && <span className="text-[14px] leading-none">{cat.emoji}</span>}
                    {cat.label}
                  </span>
                  {isActive && <span className="w-1.5 h-1.5 rounded-full bg-soft-gold shrink-0" />}
                </button>
              )
            })}
          </div>
        </div>

        {/* Subcategory drill-down — only when a category is selected and has subcats */}
        {activeCategories.length === 1 && subcats.length > 0 && (
          <div className="mb-4 pl-2.5">
            <p className="font-body text-[10px] font-semibold tracking-[0.08em] uppercase text-cool-grey/40 mb-2">Subcategory</p>
            <div className="flex flex-wrap gap-1.5">
              {subcats.map(sub => {
                const active = subFilter === sub.code
                return (
                  <button
                    key={sub.code}
                    onClick={() => onSubChange(active ? '' : sub.code)}
                    className="px-2.5 py-1 rounded-full font-body text-[11px] transition-all duration-100 border"
                    style={{
                      backgroundColor: active ? '#C9A96E' : 'transparent',
                      color: active ? '#0A1628' : '#6B7280',
                      borderColor: active ? '#C9A96E' : '#E5E0DB',
                    }}
                  >
                    {sub.label}
                  </button>
                )
              })}
            </div>
          </div>
        )}

        <div className="border-t border-light-grey mb-4" />

        {/* State */}
        <div className="mb-4">
          <p className="font-body text-[11px] font-semibold tracking-[0.08em] uppercase text-cool-grey/50 mb-2 px-2.5">State</p>
          <div className="relative">
            <select
              value={stateFilter}
              onChange={e => onStateChange(e.target.value)}
              className="w-full appearance-none h-[36px] pl-3 pr-8 rounded-lg font-body text-[13px] border border-light-grey bg-white text-deep-navy outline-none cursor-pointer focus:border-soft-gold transition-colors"
            >
              <option value="">All States</option>
              {US_STATES.map(([abbr, name]) => (
                <option key={abbr} value={abbr}>{abbr} · {name}</option>
              ))}
            </select>
            <svg className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#6B7280" strokeWidth="2.5">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </div>
        </div>

        <div className="border-t border-light-grey mb-4" />

        {/* Revenue range */}
        <div className="mb-4">
          <p className="font-body text-[11px] font-semibold tracking-[0.08em] uppercase text-cool-grey/50 mb-2 px-2.5">Annual Revenue</p>
          <div className="space-y-0.5">
            {REVENUE_PRESETS.map(preset => (
              <button
                key={preset.id}
                onClick={() => onRevenueChange(revenueFilter === preset.id ? '' : preset.id)}
                className="w-full flex items-center gap-2.5 px-2.5 py-[7px] rounded-lg transition-all duration-100"
                style={{
                  backgroundColor: revenueFilter === preset.id ? 'rgba(201,169,110,0.10)' : 'transparent',
                  color: revenueFilter === preset.id ? '#C9A96E' : '#6B7280',
                }}
              >
                <span
                  className="w-3.5 h-3.5 rounded-full border-[1.5px] flex items-center justify-center shrink-0"
                  style={{ borderColor: revenueFilter === preset.id ? '#C9A96E' : '#D1D5DB' }}
                >
                  {revenueFilter === preset.id && <span className="w-[6px] h-[6px] rounded-full bg-soft-gold" />}
                </span>
                <span className="font-body text-[13px]" style={{ fontWeight: revenueFilter === preset.id ? '600' : '400' }}>
                  {preset.label}
                </span>
              </button>
            ))}
          </div>
        </div>

        <div className="border-t border-light-grey mb-4" />

        {/* Trust tier filter */}
        <div className="mb-4">
          <p className="font-body text-[11px] font-semibold tracking-[0.08em] uppercase text-cool-grey/50 mb-2 px-2.5">Visibility Level</p>
          <div className="space-y-0.5">
            {SCORE_TIERS.map(tier => (
              <button
                key={tier.id}
                onClick={() => onScoreTierChange(scoreTier === tier.id ? '' : tier.id)}
                className="w-full flex items-center gap-2.5 px-2.5 py-[7px] rounded-lg transition-all duration-100"
                style={{
                  backgroundColor: scoreTier === tier.id ? 'rgba(201,169,110,0.10)' : 'transparent',
                  color: scoreTier === tier.id ? TIER_COLORS[tier.id] : '#6B7280',
                }}
              >
                <LampMark tier={tier.id} size="xs" />
                <span className="font-body text-[13px]" style={{ fontWeight: scoreTier === tier.id ? '600' : '400' }}>
                  {tier.label}
                </span>
              </button>
            ))}
          </div>
        </div>

        <div className="border-t border-light-grey mb-4" />

        {/* Sort */}
        <div className="mb-5">
          <p className="font-body text-[11px] font-semibold tracking-[0.08em] uppercase text-cool-grey/50 mb-2 px-2.5">Sort by</p>
          <div className="space-y-0.5">
            {SORT_OPTIONS.map(opt => (
              <button
                key={opt.id}
                onClick={() => onSortChange(opt.id)}
                className="w-full flex items-center gap-2.5 px-2.5 py-[7px] rounded-lg transition-all duration-100"
                style={{
                  backgroundColor: sortBy === opt.id ? 'rgba(201,169,110,0.10)' : 'transparent',
                  color: sortBy === opt.id ? '#C9A96E' : '#6B7280',
                }}
              >
                <span
                  className="w-3.5 h-3.5 rounded-full border-[1.5px] flex items-center justify-center shrink-0"
                  style={{ borderColor: sortBy === opt.id ? '#C9A96E' : '#D1D5DB' }}
                >
                  {sortBy === opt.id && <span className="w-[6px] h-[6px] rounded-full bg-soft-gold" />}
                </span>
                <span className="font-body text-[13px]" style={{ fontWeight: sortBy === opt.id ? '600' : '400' }}>
                  {opt.label}
                </span>
              </button>
            ))}
          </div>
        </div>

        <p className="font-body text-[11px] text-cool-grey/40 px-2.5">
          {resultCount.toLocaleString()} result{resultCount !== 1 ? 's' : ''}
        </p>
      </div>
    </aside>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function Directory() {
  const [searchParams, setSearchParams] = useSearchParams()
  const categoryParam = searchParams.get('category') || 'all'
  const subParam      = searchParams.get('sub') || ''
  const qParam        = searchParams.get('q') || ''
  usePageMeta(
    qParam ? `"${qParam}" · Causes & Giving Paths` : 'Explore Causes & Giving Paths',
    'Search 430,000+ nonprofits recognized by the IRS — by cause, category, location, and giving path.'
  )
  const stateParam    = searchParams.get('state') || ''
  const revenueParam  = searchParams.get('revenue') || ''
  const tierParam     = searchParams.get('min_merit_tier') || ''

  const [searchQuery, setSearchQuery] = useState(qParam)
  const [debouncedQuery, setDebouncedQuery] = useState(qParam)
  const [activeFilters, setActiveFilters] = useState<string[]>(() => {
    if (subParam) return [subParam[0]]  // derive category from first char of sub code
    if (!categoryParam || categoryParam === 'all') return []
    return categoryParam.split(',').filter(c => c && c !== 'all')
  })
  const [subFilter, setSubFilter] = useState(subParam)
  const [stateFilter, setStateFilter] = useState(stateParam)
  const [sortBy, setSortBy] = useState('merit_score')
  const [revenueFilter, setRevenueFilter] = useState<RevenueId>(
    REVENUE_PRESETS.some(p => p.id === revenueParam) ? revenueParam as RevenueId : ''
  )
  const [scoreTier, setScoreTier] = useState<ScoreTierId>(
    SCORE_TIERS.some(t => t.id === tierParam) ? tierParam as ScoreTierId : ''
  )
  const [hiddenGem, setHiddenGem] = useState(searchParams.get('hidden_gem') === '1')
  const [directLink, setDirectLink] = useState(searchParams.get('direct_link') === '1')
  const [needsFunding, setNeedsFunding] = useState(searchParams.get('needs_funding') === '1')
  const [cause, setCause] = useState(searchParams.get('cause') || '')
  const [debouncedCause, setDebouncedCause] = useState(cause)
  const [currentPage, setCurrentPage] = useState(1)
  const [filterSheetOpen, setFilterSheetOpen] = useState(false)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list')
  const searchMode = 'browse'
  const { isSaved, toggle: toggleSave } = useSavedOrgs()
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const itemsPerPage = viewMode === 'list' ? 25 : 18

  // Sync search query from URL on mount (e.g. coming from homepage search)
  useEffect(() => {
    if (qParam && qParam !== searchQuery) {
      setSearchQuery(qParam)
      setDebouncedQuery(qParam)
      setCurrentPage(1)
    }
  }, [qParam])

  // Debounce search query — 320ms after typing stops
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      setDebouncedQuery(searchQuery)
      setCurrentPage(1)
    }, 320)
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
  }, [searchQuery])

  // Debounce cause filter — same 320ms feel as search
  useEffect(() => {
    const t = setTimeout(() => {
      setDebouncedCause(cause)
      setCurrentPage(1)
    }, 320)
    return () => clearTimeout(t)
  }, [cause])

  // Resolve revenue preset to API params
  const revPreset = REVENUE_PRESETS.find(p => p.id === revenueFilter)

  const { data: orgsData, loading: orgsLoading, error: orgsError } = useApi(
    () => getOrganizations({
      ntee: subFilter ? undefined : (activeFilters.length === 0 ? undefined : activeFilters.join(',')),
      sub: subFilter || undefined,
      state: stateFilter || undefined,
      q: debouncedQuery || undefined,
      sort: sortBy,
      page: currentPage,
      per_page: itemsPerPage,
      min_revenue: revPreset?.min,
      max_revenue: revPreset?.max,
      min_merit_tier: scoreTier || undefined,
      hidden_gem: hiddenGem || undefined,
      direct_link: directLink || undefined,
      needs_funding: needsFunding || undefined,
      cause: debouncedCause.trim() || undefined,
    }),
    [activeFilters, subFilter, stateFilter, debouncedQuery, sortBy, currentPage, revenueFilter, scoreTier, hiddenGem, directLink, needsFunding, debouncedCause, itemsPerPage]
  )

  const scrollTop = () => window.scrollTo({ top: 0, behavior: 'smooth' })

  const handleFilterChange = (filterId: string) => {
    let next: string[]
    if (filterId === 'all') {
      next = []
    } else {
      const already = activeFilters.includes(filterId)
      next = already ? activeFilters.filter(f => f !== filterId) : [...activeFilters, filterId]
    }
    setActiveFilters(next)
    if (next.length !== 1) setSubFilter('')  // subcategory only makes sense for a single category
    setCurrentPage(1)
    scrollTop()
    if (next.length === 0) {
      searchParams.delete('category')
    } else {
      searchParams.set('category', next.join(','))
    }
    setSearchParams(searchParams)
  }

  const handleSubChange = (code: string) => {
    setSubFilter(code)
    setCurrentPage(1)
    scrollTop()
  }

  const handleStateChange = (s: string) => {
    setStateFilter(s)
    setCurrentPage(1)
    scrollTop()
    if (s) { searchParams.set('state', s) } else { searchParams.delete('state') }
    setSearchParams(searchParams)
  }

  const handleRevenueChange = (id: RevenueId) => {
    setRevenueFilter(id)
    setCurrentPage(1)
    scrollTop()
    if (id) { searchParams.set('revenue', id) } else { searchParams.delete('revenue') }
    setSearchParams(searchParams)
  }

  const handleScoreTierChange = (id: ScoreTierId) => {
    setScoreTier(id)
    setCurrentPage(1)
    scrollTop()
    if (id) { searchParams.set('min_merit_tier', id) } else { searchParams.delete('min_merit_tier') }
    setSearchParams(searchParams)
  }

  const handleClearAll = () => {
    setSearchQuery('')
    setDebouncedQuery('')
    setActiveFilters([])
    setSubFilter('')
    setStateFilter('')
    setSortBy('organization_name')
    setRevenueFilter('')
    setScoreTier('')
    setHiddenGem(false)
    setDirectLink(false)
    setNeedsFunding(false)
    setCause('')
    setDebouncedCause('')
    setCurrentPage(1)
    searchParams.delete('category')
    searchParams.delete('sub')
    searchParams.delete('q')
    searchParams.delete('state')
    searchParams.delete('revenue')
    searchParams.delete('min_merit_tier')
    setSearchParams(searchParams)
  }

  const organizations = orgsData?.organizations || []
  const total = orgsData?.total || 0
  const totalPages = orgsData?.pages || 1

  // Readable label for active sub filter
  const subLabel = subFilter
    ? NTEE_SUBCATEGORIES[activeFilters[0] ?? '']?.find(s => s.code === subFilter)?.label ?? subFilter
    : ''

  // Readable label for active revenue filter
  const revLabel = revPreset?.label ?? ''

  // Readable label for active score tier
  const scoreLabel = SCORE_TIERS.find(t => t.id === scoreTier)?.label ?? ''

  const activeFilterCount = [
    activeFilters.length > 0,
    !!subFilter,
    !!stateFilter,
    !!revenueFilter,
    !!scoreTier,
    sortBy !== 'merit_score',
  ].filter(Boolean).length

  return (
    <div className="min-h-[100dvh]">
      {/* Page Header */}
      <div className="bg-white border-b border-light-grey pt-[72px]">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 pt-10 pb-10">
          <div className="flex items-center gap-2 mb-5">
            <Link to="/" className="font-body text-[12px] tracking-[0.02em] text-cool-grey hover:text-deep-navy transition-colors">
              Home
            </Link>
            <span className="text-cool-grey/40">/</span>
            <span className="font-body text-[12px] tracking-[0.02em] text-deep-navy">Directory</span>
          </div>

          <h1 className="font-display italic text-deep-navy leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(32px, 4vw, 48px)' }}>
            Explore Causes &amp; Giving Paths
          </h1>
          <p className="mt-3 font-body text-[16px] leading-[1.6] text-cool-grey">
            Search public records, cause tags, locations, and giving paths across the United States.
          </p>

          {/* Search */}
          <SearchBar
            value={searchQuery}
            onChange={v => { setSearchQuery(v); setCurrentPage(1) }}
            onSearch={q => { setSearchQuery(q); setDebouncedQuery(q); setCurrentPage(1) }}
            placeholder="Search by cause, city, community, name, or EIN…"
            className="mt-7 max-w-[640px]"
          />

          {/* Mobile: single Filters button */}
          {searchMode === 'browse' && <div className="mt-5 md:hidden flex items-center gap-2">
            <button
              onClick={() => setFilterSheetOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full font-body text-[13px] font-medium border transition-all duration-150"
              style={{
                backgroundColor: activeFilterCount > 0 ? '#C9A96E' : 'transparent',
                color: activeFilterCount > 0 ? '#0A1628' : '#4B5563',
                borderColor: activeFilterCount > 0 ? '#C9A96E' : '#E5E0DB',
              }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="4" y1="6" x2="20" y2="6"/><line x1="8" y1="12" x2="16" y2="12"/><line x1="11" y1="18" x2="13" y2="18"/>
              </svg>
              Filters
              {activeFilterCount > 0 && (
                <span className="min-w-[16px] h-4 flex items-center justify-center bg-deep-navy text-soft-gold text-[10px] font-bold rounded-full px-1">
                  {activeFilterCount}
                </span>
              )}
            </button>
            {activeFilterCount > 0 && (
              <button onClick={handleClearAll} className="font-body text-[12px] text-cool-grey/60 hover:text-cool-grey transition-colors">
                Clear
              </button>
            )}
          </div>}

          {/* Tablet: category pills + state dropdown */}
          {searchMode === 'browse' && <div className="mt-5 hidden md:flex lg:hidden items-center gap-2 flex-wrap">
            {FILTER_CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                onClick={() => handleFilterChange(cat.id)}
                className="px-4 py-[6px] rounded-full font-body text-[12px] tracking-[0.02em] transition-all duration-150 border"
                style={{
                  backgroundColor: (cat.id === 'all' ? activeFilters.length === 0 : activeFilters.includes(cat.id)) ? '#C9A96E' : 'transparent',
                  color: (cat.id === 'all' ? activeFilters.length === 0 : activeFilters.includes(cat.id)) ? '#0A1628' : '#4B5563',
                  borderColor: (cat.id === 'all' ? activeFilters.length === 0 : activeFilters.includes(cat.id)) ? '#C9A96E' : '#E5E0DB',
                }}
              >
                {'emoji' in cat && cat.emoji ? `${cat.emoji} ` : ''}{cat.label}
              </button>
            ))}
            <div className="relative ml-auto">
              <select
                value={stateFilter}
                onChange={e => handleStateChange(e.target.value)}
                className="appearance-none h-[34px] pl-3 pr-8 rounded-full font-body text-[12px] tracking-[0.02em] border transition-all duration-150 outline-none cursor-pointer"
                style={{
                  backgroundColor: stateFilter ? '#C9A96E' : 'transparent',
                  color: stateFilter ? '#0A1628' : '#4B5563',
                  borderColor: stateFilter ? '#C9A96E' : '#E5E0DB',
                }}
              >
                <option value="">All States</option>
                {US_STATES.map(([abbr, name]) => (
                  <option key={abbr} value={abbr}>{abbr} · {name}</option>
                ))}
              </select>
              <svg className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="6 9 12 15 18 9"/></svg>
            </div>
          </div>}

          {/* Tablet: subcategory pills when a category is active */}
          {searchMode === 'browse' && activeFilters.length === 1 && (NTEE_SUBCATEGORIES[activeFilters[0]]?.length ?? 0) > 0 && (
            <div className="mt-3 hidden md:flex lg:hidden items-center gap-1.5 flex-wrap">
              {NTEE_SUBCATEGORIES[activeFilters[0]].map(sub => (
                <button
                  key={sub.code}
                  onClick={() => handleSubChange(subFilter === sub.code ? '' : sub.code)}
                  className="px-3 py-1 rounded-full font-body text-[11px] transition-all duration-150 border"
                  style={{
                    backgroundColor: subFilter === sub.code ? '#0A1628' : 'transparent',
                    color: subFilter === sub.code ? '#F5F0EB' : '#6B7280',
                    borderColor: subFilter === sub.code ? '#0A1628' : '#E5E0DB',
                  }}
                >
                  {sub.label}
                </button>
              ))}
            </div>
          )}

          {/* FilterSheet — mobile only */}
          <FilterSheet
            open={filterSheetOpen}
            onClose={() => setFilterSheetOpen(false)}
            activeCategory={activeFilters[0] ?? 'all'}
            stateFilter={stateFilter}
            sortBy={sortBy}
            revenueFilter={revenueFilter}
            scoreTier={scoreTier}
            hiddenGem={hiddenGem}
            directLink={directLink}
            needsFunding={needsFunding}
            cause={cause}
            onCategoryChange={(id) => { handleFilterChange(id) }}
            onStateChange={handleStateChange}
            onSortChange={(s) => { setSortBy(s); setCurrentPage(1); scrollTop() }}
            onRevenueChange={(id) => handleRevenueChange(id as RevenueId)}
            onScoreTierChange={(id) => handleScoreTierChange(id as ScoreTierId)}
            onHiddenGemChange={(v) => { setHiddenGem(v); setCurrentPage(1); scrollTop() }}
            onDirectLinkChange={(v) => { setDirectLink(v); setCurrentPage(1); scrollTop() }}
            onNeedsFundingChange={(v) => { setNeedsFunding(v); setCurrentPage(1); scrollTop() }}
            onCauseChange={setCause}
            onClearAll={handleClearAll}
            resultCount={total}
          />
        </div>
      </div>

      {/* Results */}
      <div className="bg-warm-cream py-12 md:py-16">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">

          {/* Browse mode */}
          {searchMode === 'browse' && (
          <div className="lg:flex lg:gap-8 lg:items-start">

            {/* Desktop filter rail */}
            <FilterRail
              activeCategories={activeFilters}
              subFilter={subFilter}
              stateFilter={stateFilter}
              sortBy={sortBy}
              revenueFilter={revenueFilter}
              scoreTier={scoreTier}
              hiddenGem={hiddenGem}
              directLink={directLink}
              needsFunding={needsFunding}
              cause={cause}
              onCategoryChange={handleFilterChange}
              onSubChange={handleSubChange}
              onStateChange={handleStateChange}
              onSortChange={(s) => { setSortBy(s); setCurrentPage(1); scrollTop() }}
              onRevenueChange={handleRevenueChange}
              onScoreTierChange={handleScoreTierChange}
              onHiddenGemChange={(v) => { setHiddenGem(v); setCurrentPage(1); scrollTop() }}
              onDirectLinkChange={(v) => { setDirectLink(v); setCurrentPage(1); scrollTop() }}
              onNeedsFundingChange={(v) => { setNeedsFunding(v); setCurrentPage(1); scrollTop() }}
              onCauseChange={setCause}
              onClearAll={handleClearAll}
              resultCount={total}
            />

            {/* Results column */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-4 mb-8 flex-wrap">
                <div>
                  <span className="font-body text-[20px] font-semibold tracking-[-0.02em] text-deep-navy">
                    {total.toLocaleString()} {searchQuery || activeFilters.length > 0 || stateFilter ? 'results' : 'organizations'}
                  </span>

                  {/* Active filter chips */}
                  {(searchQuery || activeFilters.length > 0 || subFilter || stateFilter || revenueFilter || scoreTier) && (
                    <div className="flex items-center gap-2 mt-2 flex-wrap">
                      {searchQuery && (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-navy-mid/8 text-deep-navy font-body text-[11px]">
                          "{searchQuery}"
                        </span>
                      )}
                      {!subFilter && activeFilters.map(f => (
                        <button
                          key={f}
                          onClick={() => handleFilterChange(f)}
                          className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-soft-gold/10 text-soft-gold font-body text-[11px] hover:bg-soft-gold/20 transition-colors"
                        >
                          {RAIL_CATEGORIES.find(c => c.id === f)?.label} ×
                        </button>
                      ))}
                      {subFilter && (
                        <button
                          onClick={() => { setSubFilter(''); setCurrentPage(1) }}
                          className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-soft-gold/10 text-soft-gold font-body text-[11px] hover:bg-soft-gold/20 transition-colors"
                        >
                          {subLabel} ×
                        </button>
                      )}
                      {stateFilter && (
                        <button
                          onClick={() => handleStateChange('')}
                          className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-soft-gold/10 text-soft-gold font-body text-[11px] hover:bg-soft-gold/20 transition-colors"
                        >
                          {stateFilter} ×
                        </button>
                      )}
                      {revenueFilter && (
                        <button
                          onClick={() => handleRevenueChange('')}
                          className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-soft-gold/10 text-soft-gold font-body text-[11px] hover:bg-soft-gold/20 transition-colors"
                        >
                          {revLabel} ×
                        </button>
                      )}
                      {scoreTier && (
                        <button
                          onClick={() => handleScoreTierChange('')}
                          className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-soft-gold/10 text-soft-gold font-body text-[11px] hover:bg-soft-gold/20 transition-colors"
                        >
                          {scoreLabel} ×
                        </button>
                      )}
                      <button onClick={handleClearAll} className="font-body text-[11px] text-cool-grey hover:text-deep-navy transition-colors">
                        Clear all
                      </button>
                    </div>
                  )}
                  {subFilter === 'X70' && (
                    <p className="mt-1.5 font-body text-[11px] text-cool-grey">
                      The IRS classifies Hindu, Sikh, Jain, and other non-Western faith traditions under this code. This reflects official IRS data, not our own categorization.
                    </p>
                  )}
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  {/* Sort — tablet only */}
                  <div className="hidden md:flex lg:hidden items-center gap-2">
                    <span className="font-body text-[14px] text-cool-grey">Sort:</span>
                    <select
                      value={sortBy}
                      onChange={(e) => { setSortBy(e.target.value); setCurrentPage(1) }}
                      className="bg-transparent font-body text-[14px] text-deep-navy outline-none cursor-pointer"
                    >
                      {SORT_OPTIONS.map(opt => (
                        <option key={opt.id} value={opt.id}>{opt.label}</option>
                      ))}
                    </select>
                  </div>
                  {/* Grid/List toggle */}
                  <div className="hidden md:flex items-center gap-1 border border-light-grey rounded-lg p-1">
                    <button
                      onClick={() => setViewMode('grid')}
                      title="Grid view"
                      className="p-1.5 rounded transition-colors"
                      style={{ backgroundColor: viewMode === 'grid' ? '#E5E0DB' : 'transparent' }}
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={viewMode === 'grid' ? '#0A1628' : '#A89F94'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>
                      </svg>
                    </button>
                    <button
                      onClick={() => setViewMode('list')}
                      title="List view"
                      className="p-1.5 rounded transition-colors"
                      style={{ backgroundColor: viewMode === 'list' ? '#E5E0DB' : 'transparent' }}
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={viewMode === 'list' ? '#0A1628' : '#A89F94'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/>
                        <line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>
                      </svg>
                    </button>
                  </div>
                </div>
              </div>

              {/* Results grid / list */}
              {orgsLoading ? (
                viewMode === 'list' ? (
                  <div className="flex flex-col gap-2">
                    {Array.from({ length: 10 }).map((_, i) => (
                      <div key={i} className="bg-white border border-light-grey rounded-xl px-5 py-4 animate-pulse flex items-center gap-4">
                        <div className="w-[110px] space-y-1.5">
                          <div className="h-5 w-20 bg-light-grey rounded-full" />
                          <div className="h-5 w-10 bg-light-grey rounded-full" />
                        </div>
                        <div className="flex-1 space-y-1.5">
                          <div className="h-4 w-3/4 bg-light-grey rounded" />
                          <div className="h-3 w-1/2 bg-light-grey rounded" />
                        </div>
                        <div className="hidden md:block w-[130px] space-y-1.5 text-right">
                          <div className="h-3 w-20 bg-light-grey rounded ml-auto" />
                          <div className="h-3 w-16 bg-light-grey rounded ml-auto" />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {Array.from({ length: 9 }).map((_, i) => (
                      <div key={i} className="bg-white border border-light-grey rounded-xl p-5 animate-pulse">
                        <div className="flex items-center gap-2 mb-3">
                          <div className="h-5 w-20 bg-light-grey rounded-full" />
                          <div className="h-5 w-10 bg-light-grey rounded-full ml-auto" />
                        </div>
                        <div className="h-5 w-3/4 bg-light-grey rounded mb-2" />
                        <div className="h-4 w-1/2 bg-light-grey rounded mb-4" />
                        <div className="h-4 w-24 bg-light-grey rounded-full mb-4" />
                        <div className="h-3 w-full bg-light-grey rounded" />
                        <div className="h-3 w-2/3 bg-light-grey rounded mt-2" />
                      </div>
                    ))}
                  </div>
                )
              ) : orgsError ? (
                <div className="text-center py-16">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#6B7280" strokeWidth="1.5" className="mx-auto mb-4">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="12" />
                    <line x1="12" y1="16" x2="12.01" y2="16" />
                  </svg>
                  <p className="font-body text-[16px] text-cool-grey">Unable to load organizations.</p>
                  <p className="font-body text-[14px] text-cool-grey mt-2">Check that the API is running, then refresh.</p>
                </div>
              ) : organizations.length > 0 ? (
                <>
                  {viewMode === 'list' ? (
                    <div className="flex flex-col gap-2">
                      {organizations.map((org) => (
                        <OrgCardApi
                          key={org.EIN}
                          org={org}
                          isSaved={isSaved(org.EIN)}
                          onToggleSave={(_e, ein, meta) => toggleSave(ein, meta)}
                          listView
                        />
                      ))}
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                      {organizations.map((org) => (
                        <OrgCardApi
                          key={org.EIN}
                          org={org}
                          isSaved={isSaved(org.EIN)}
                          onToggleSave={(_e, ein, meta) => toggleSave(ein, meta)}
                        />
                      ))}
                    </div>
                  )}

                  {/* Pagination */}
                  {totalPages > 1 && (
                    <div className="mt-12 flex items-center justify-center gap-2">
                      <button
                        onClick={() => { setCurrentPage(p => Math.max(1, p - 1)); scrollTop() }}
                        disabled={currentPage === 1}
                        className="w-8 h-8 flex items-center justify-center rounded-full text-cool-grey hover:text-deep-navy disabled:opacity-30 transition-colors"
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
                      </button>
                      {(() => {
                        const pages: (number | '…')[] = []
                        if (totalPages <= 7) {
                          for (let i = 1; i <= totalPages; i++) pages.push(i)
                        } else {
                          pages.push(1)
                          if (currentPage > 3) pages.push('…')
                          for (let i = Math.max(2, currentPage - 1); i <= Math.min(totalPages - 1, currentPage + 1); i++) pages.push(i)
                          if (currentPage < totalPages - 2) pages.push('…')
                          pages.push(totalPages)
                        }
                        return pages.map((page, idx) =>
                          page === '…' ? (
                            <span key={`ellipsis-${idx}`} className="w-8 h-8 flex items-center justify-center font-body text-[14px] text-cool-grey">…</span>
                          ) : (
                            <button
                              key={page}
                              onClick={() => { setCurrentPage(page); scrollTop() }}
                              className="w-8 h-8 flex items-center justify-center rounded-full font-body text-[14px] transition-all duration-150"
                              style={{
                                backgroundColor: currentPage === page ? '#C9A96E' : 'transparent',
                                color: currentPage === page ? '#0A1628' : '#6B7280',
                              }}
                            >
                              {page}
                            </button>
                          )
                        )
                      })()}
                      <button
                        onClick={() => { setCurrentPage(p => Math.min(totalPages, p + 1)); scrollTop() }}
                        disabled={currentPage === totalPages}
                        className="w-8 h-8 flex items-center justify-center rounded-full text-cool-grey hover:text-deep-navy disabled:opacity-30 transition-colors"
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
                      </button>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-16">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#6B7280" strokeWidth="1.5" className="mx-auto mb-4">
                    <circle cx="11" cy="11" r="8" />
                    <path d="m21 21-4.3-4.3" />
                  </svg>
                  <p className="font-body text-[16px] text-cool-grey">No organizations found.</p>
                  <button onClick={handleClearAll} className="mt-4 font-body text-[14px] text-soft-gold hover:text-bright-gold transition-colors">
                    Clear filters
                  </button>
                </div>
              )}
            </div>
          </div>
          )} {/* end browse mode */}

        </div>
      </div>
    </div>
  )
}
