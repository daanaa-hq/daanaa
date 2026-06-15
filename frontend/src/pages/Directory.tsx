import React, { useState, useEffect, useRef } from 'react'
import { usePageMeta } from '../hooks/usePageMeta'
import { useSearchParams, Link } from 'react-router-dom'
import OrgCard, { OrgCardRow } from '../components/OrgCard'
import FilterSheet from '../components/FilterSheet'
import SearchBar from '../components/SearchBar'
import { useApi } from '../hooks/useApi'
import { useSavedOrgs } from '../hooks/useSavedOrgs'
import { getOrganizations, getFusedSearch, getStats } from '../data/api'
import type { ApiOrganization } from '../data/api'
import { getTierSummary, getTierFromOrg, TIER_COLORS } from '../components/TrustBadge'
import LampMark from '../components/LampMark'
import type { TierName } from '../components/TrustBadge'
import { RAIL_CATEGORIES, ALL_CATEGORIES, NTEE_SUBCATEGORIES } from '../data/categories'

const FILTER_CATEGORIES = [
  { id: 'all', label: 'All' },
  ...ALL_CATEGORIES,
]

const SCORES_ENABLED = import.meta.env.VITE_ENABLE_SCORES !== 'false'

const SORT_OPTIONS = [
  ...(SCORES_ENABLED ? [{ id: 'merit_score', label: 'Peer Financial Context' }] : []),
  { id: 'organization_name', label: 'Name A to Z' },
  { id: 'total_revenue', label: 'Revenue' },
]

// Small first. This is the mission: the smallest groups are the hardest to find.
// Eight donor-facing size bands (mirrors the methodology's eight-band thinking
// with simple, universal dollar breakpoints).
const REVENUE_PRESETS = [
  { id: 'b1', label: 'Under $50K',     min: undefined,   max: 49_999 },
  { id: 'b2', label: '$50K – $100K',   min: 50_000,      max: 99_999 },
  { id: 'b3', label: '$100K – $250K',  min: 100_000,     max: 249_999 },
  { id: 'b4', label: '$250K – $1M',    min: 250_000,     max: 999_999 },
  { id: 'b5', label: '$1M – $5M',      min: 1_000_000,   max: 4_999_999 },
  { id: 'b6', label: '$5M – $25M',     min: 5_000_000,   max: 24_999_999 },
  { id: 'b7', label: '$25M – $100M',   min: 25_000_000,  max: 99_999_999 },
  { id: 'b8', label: 'Over $100M',     min: 100_000_000, max: undefined },
] as const

const SCORE_TIERS: { id: TierName; label: string }[] = [
  { id: 'Beacon',  label: 'Beacon' },
  { id: 'Torch',   label: 'Torch +' },
  { id: 'Candle',  label: 'Candle +' },
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
    mission: org.mission || '',
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

// 50 states + DC + PR as flat options; remaining territories + military as optgroups
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
  ['PR','Puerto Rico'],
] as const

const US_TERRITORIES = [
  ['AS','American Samoa'],['GU','Guam'],['MP','Northern Mariana Islands'],['VI','U.S. Virgin Islands'],
] as const

const US_MILITARY = [
  ['AA','Armed Forces Americas'],['AE','Armed Forces Europe'],['AP','Armed Forces Pacific'],
] as const

// ── Main page ─────────────────────────────────────────────────────────────────

export default function Directory() {
  const [searchParams, setSearchParams] = useSearchParams()
  const categoryParam = searchParams.get('category') || 'all'
  const subParam      = searchParams.get('sub') || ''
  const qParam        = searchParams.get('q') || ''
  usePageMeta(
    qParam ? `"${qParam}" · Causes & Organizations` : 'Explore Causes & Organizations',
    'Search 1.8 million+ tax-deductible 501(c)(3) organizations recognized by the IRS, by cause, category, and location.'
  )
  const stateParam    = searchParams.get('state') || ''
  const revenueParam  = searchParams.get('revenue') || ''
  const tierParam     = searchParams.get('min_tier') || ''

  const [searchQuery, setSearchQuery] = useState(qParam)
  const [debouncedQuery, setDebouncedQuery] = useState(qParam)
  const subParamList = subParam.split(',').map(s => s.trim()).filter(Boolean)
  const [activeFilters, setActiveFilters] = useState<string[]>(() => {
    // Categories = explicit ?category= plus the parent letter of any ?sub= code
    const fromCats = (!categoryParam || categoryParam === 'all') ? [] : categoryParam.split(',').filter(c => c && c !== 'all')
    const fromSubs = subParamList.map(s => s[0])
    return Array.from(new Set([...fromCats, ...fromSubs]))
  })
  const [subFilters, setSubFilters] = useState<string[]>(subParamList)
  const [stateFilter, setStateFilter] = useState(stateParam)
  const [sortBy, setSortBy] = useState(SCORES_ENABLED ? 'merit_score' : 'total_revenue')

  // Sync filter state with URL params whenever they change
  useEffect(() => {
    const newFromCats = (!categoryParam || categoryParam === 'all') ? [] : categoryParam.split(',').filter(c => c && c !== 'all')
    const newFromSubs = subParamList.map(s => s[0])
    setActiveFilters(Array.from(new Set([...newFromCats, ...newFromSubs])))
    setSubFilters(subParamList)
    setStateFilter(stateParam)
  }, [categoryParam, subParam, stateParam])
  const [revenueFilter, setRevenueFilter] = useState<RevenueId>(
    REVENUE_PRESETS.some(p => p.id === revenueParam) ? revenueParam as RevenueId : ''
  )
  const [scoreTier, setScoreTier] = useState<ScoreTierId>(
    SCORE_TIERS.some(t => t.id === tierParam) ? tierParam as ScoreTierId : ''
  )
  const [hasWebsite, setHasWebsite] = useState(searchParams.get('has_website') === '1')
  // Hidden gems is the default landing view (small, healthy, low-profile orgs,
  // reshuffled weekly). On by default unless the user arrived with an explicit
  // filter in the URL, or explicitly turned it off (?hidden_gem=0).
  const _noUrlFilters = !categoryParam && !subParam && !stateParam && !qParam &&
                        !revenueParam && !searchParams.get('cause') && !searchParams.get('tier')
  const [hiddenGem, setHiddenGem] = useState(
    searchParams.get('hidden_gem') === '1' ||
    (searchParams.get('hidden_gem') !== '0' && _noUrlFilters)
  )
  const [needsSupport, setNeedsSupport] = useState(searchParams.get('needs_funding') === '1')
  const [visTier, setVisTier] = useState(searchParams.get('tier') || '')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [cause, setCause] = useState(searchParams.get('cause') || '')
  const [debouncedCause, setDebouncedCause] = useState(cause)
  const [currentPage, setCurrentPage] = useState(1)
  const [filterSheetOpen, setFilterSheetOpen] = useState(false)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list')
  const [filtersExpanded, setFiltersExpanded] = useState(false)
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
      // Normalize EIN format: "46-3120432" → "463120432" so the API matches
      const normalized = /^\d{2}-\d{7}$/.test(searchQuery.trim())
        ? searchQuery.replace(/-/g, '')
        : searchQuery
      setDebouncedQuery(normalized)
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

  // A search query searches the whole directory, so the gems-default lens is
  // dropped while typing (otherwise search would only ever find ~34k gems).
  const effectiveHiddenGem = hiddenGem && !debouncedQuery.trim()

  // Fused search mode: any meaningful query with no active structured filters
  const hasAnyFilter = activeFilters.length > 0 || subFilters.length > 0 || !!stateFilter || !!revenueFilter || !!scoreTier || hasWebsite || needsSupport || !!visTier || !!debouncedCause.trim()
  const isFusedMode = !hasAnyFilter && debouncedQuery.trim().length >= 2

  // Categories the user drilled into (picked specific subcats) are represented by
  // those subcats; remaining selected categories are sent whole. Backend ORs them.
  const catsWithSubs = new Set(subFilters.map(s => s[0]))
  const nteeToSend = activeFilters.filter(c => !catsWithSubs.has(c))

  const { data: orgsData, loading: orgsLoading, error: orgsError } = useApi(
    () => getOrganizations({
      ntee: nteeToSend.length ? nteeToSend.join(',') : undefined,
      sub: subFilters.length ? subFilters.join(',') : undefined,
      state: stateFilter || undefined,
      q: debouncedQuery || undefined,
      sort: sortBy,
      order: sortOrder,
      page: currentPage,
      per_page: itemsPerPage,
      min_revenue: revPreset?.min,
      max_revenue: revPreset?.max,
      min_tier: scoreTier || undefined,
      tier: visTier || undefined,
      has_website: hasWebsite || undefined,
      hidden_gem: effectiveHiddenGem || undefined,
      needs_funding: needsSupport || undefined,
      cause: debouncedCause.trim() || undefined,
    }),
    [activeFilters, subFilters, stateFilter, debouncedQuery, sortBy, sortOrder, currentPage, revenueFilter, scoreTier, visTier, hasWebsite, effectiveHiddenGem, needsSupport, debouncedCause, itemsPerPage]
  )

  const { data: fusedData, loading: fusedLoading, error: fusedError } = useApi(
    () => isFusedMode ? getFusedSearch(debouncedQuery) : Promise.resolve(null),
    [debouncedQuery, isFusedMode]
  )

  // Data-freshness line under the results count ("last checked <date>")
  const { data: statsData } = useApi(getStats, [])

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
    // Drop any selected subcategories whose parent category is no longer active
    const prunedSubs = subFilters.filter(s => next.includes(s[0]))
    if (prunedSubs.length !== subFilters.length) {
      setSubFilters(prunedSubs)
      if (prunedSubs.length) searchParams.set('sub', prunedSubs.join(',')); else searchParams.delete('sub')
    }
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
    const next = subFilters.includes(code) ? subFilters.filter(s => s !== code) : [...subFilters, code]
    setSubFilters(next)
    if (next.length) searchParams.set('sub', next.join(',')); else searchParams.delete('sub')
    setSearchParams(searchParams)
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
    if (id) { searchParams.set('min_tier', id) } else { searchParams.delete('min_tier') }
    setSearchParams(searchParams)
  }

  // Clear all filters returns to the default landing (hidden gems on).
  const handleClearAll = () => {
    setSearchQuery('')
    setDebouncedQuery('')
    setActiveFilters([])
    setSubFilters([])
    setStateFilter('')
    setSortBy(SCORES_ENABLED ? 'merit_score' : 'total_revenue')
    setSortOrder('desc')
    setRevenueFilter('')
    setScoreTier('')
    setVisTier('')
    setHasWebsite(false)
    setNeedsSupport(false)
    setHiddenGem(true)
    setCause('')
    setDebouncedCause('')
    setCurrentPage(1)
    searchParams.delete('category')
    searchParams.delete('sub')
    searchParams.delete('q')
    searchParams.delete('state')
    searchParams.delete('revenue')
    searchParams.delete('min_tier')
    searchParams.delete('tier')
    searchParams.delete('has_website')
    searchParams.delete('hidden_gem')
    searchParams.delete('needs_funding')
    setSearchParams(searchParams)
  }

  // "See all" — leave the gems lens and browse the full directory.
  const handleSeeAll = () => {
    setHiddenGem(false)
    setNeedsSupport(false)
    setVisTier('')
    setCurrentPage(1)
    scrollTop()
    searchParams.set('hidden_gem', '0')
    setSearchParams(searchParams)
  }

  // Use fused results when available, fall back to FTS5 keyword
  const fusedResults = fusedData?.results
  const useFusedResults = isFusedMode && !!fusedResults && fusedResults.length >= 1
  const organizations = useFusedResults ? fusedResults : (orgsData?.organizations || [])
  const total = useFusedResults ? fusedResults.length : (orgsData?.total || 0)
  const totalPages = useFusedResults ? 1 : (orgsData?.pages || 1)
  const activeLoading = useFusedResults ? fusedLoading : orgsLoading
  // Fused failures degrade to the keyword results that already loaded; only
  // surface an error when there is genuinely nothing to show the user.
  const activeError = useFusedResults
    ? null
    : (orgsError ?? (isFusedMode && fusedError && organizations.length === 0 ? fusedError : null))

  // Readable label for any subcategory code (searches across all categories)
  const subLabelOf = (code: string): string => {
    for (const arr of Object.values(NTEE_SUBCATEGORIES)) {
      const m = arr.find(s => s.code === code)
      if (m) return m.label
    }
    return code
  }

  // Readable label for active revenue filter
  const revLabel = revPreset?.label ?? ''

  // Readable label for active score tier
  const scoreLabel = SCORE_TIERS.find(t => t.id === scoreTier)?.label ?? ''

  const activeFilterCount = [
    activeFilters.length > 0,
    subFilters.length > 0,
    !!stateFilter,
    !!revenueFilter,
    !!scoreTier,
    sortBy !== (SCORES_ENABLED ? 'merit_score' : 'total_revenue'),
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
            <span className="text-cool-grey">/</span>
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

          {/* Filters collapse/expand toggle */}
          {searchMode === 'browse' && (
            <button
              onClick={() => setFiltersExpanded(!filtersExpanded)}
              className="mt-7 inline-flex items-center gap-2 px-4 py-2 rounded-full font-body text-[13px] font-medium border transition-all duration-150"
              style={{
                backgroundColor: filtersExpanded || activeFilterCount > 0 ? '#F8F5F0' : 'transparent',
                borderColor: filtersExpanded || activeFilterCount > 0 ? '#E5E0DB' : '#E5E0DB',
                color: '#0A1628',
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
              <svg
                width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
                style={{ transform: filtersExpanded ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 150ms' }}
              >
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </button>
          )}

          {/* Filters section — collapsible */}
          <div className={`overflow-hidden transition-all duration-300 ${filtersExpanded ? 'max-h-[500px] mt-4' : 'max-h-0 mt-0'}`}>
            {/* Top filter toolbar — all breakpoints. Full filter set lives in the
                drawer (Filters button); the discovery toggles are surfaced here
                because they're the point of the directory. */}
            {searchMode === 'browse' && <div className="flex items-center gap-2 flex-wrap pb-4">
            {/* Discovery toggles — each keeps its own color (even when off) + a tooltip */}
            {[
              { key: 'hg', label: 'Hidden gems', tip: 'Small, financially healthy, low-profile orgs — a fresh set each week', on: hiddenGem, color: '#C9A96E', textOn: '#0A1628',
                icon: <><path d="M6 3h12l4 6-10 13L2 9z"/><path d="M11 3 8 9l4 13 4-13-3-6"/><path d="M2 9h20"/></>,
                toggle: () => { setHiddenGem(!hiddenGem); setCurrentPage(1); scrollTop() } },
              { key: 'ns', label: 'Needs support', tip: 'Operating on under six months of financial reserve', on: needsSupport, color: '#7C3AED', textOn: '#FFFFFF',
                icon: <><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 1 0-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 0 0 0-7.78z"/></>,
                toggle: () => { setNeedsSupport(!needsSupport); setCurrentPage(1); scrollTop() } },
            ].map(t => (
              <button
                key={t.key}
                onClick={t.toggle}
                title={t.tip}
                aria-pressed={t.on}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full font-body text-[12.5px] font-medium border transition-all duration-150"
                style={{
                  backgroundColor: t.on ? t.color : `${t.color}12`,
                  color: t.on ? t.textOn : '#374151',
                  borderColor: t.on ? t.color : `${t.color}59`,
                }}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={t.on ? t.textOn : t.color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  {t.icon}
                </svg>
                {t.label}
              </button>
            ))}

            {activeFilterCount > 0 && (
              <button onClick={handleClearAll} className="font-body text-[12px] text-cool-grey hover:text-cool-grey transition-colors ml-1">
                Clear all
              </button>
            )}
          </div>}

          {/* Category quick-pills + state — all breakpoints */}
          {searchMode === 'browse' && <div className="mt-3 flex items-center gap-2 flex-wrap">
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
            <div className="ml-auto flex items-center gap-2">
              {/* Has a website */}
              <button
                onClick={() => { setHasWebsite(!hasWebsite); setCurrentPage(1); scrollTop() }}
                title="A working website you can visit to learn more"
                aria-pressed={hasWebsite}
                className="inline-flex items-center gap-1.5 h-[34px] px-3.5 rounded-full font-body text-[12px] font-medium border transition-all duration-150"
                style={{
                  backgroundColor: hasWebsite ? '#0EA5E9' : '#0EA5E912',
                  color: hasWebsite ? '#FFFFFF' : '#374151',
                  borderColor: hasWebsite ? '#0EA5E9' : '#0EA5E959',
                }}
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke={hasWebsite ? '#FFFFFF' : '#0EA5E9'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                </svg>
                Has a website
              </button>
              {/* Visibility level (lamp tier) */}
              <div className="relative">
                <select
                  value={visTier}
                  onChange={e => {
                    const v = e.target.value
                    setVisTier(v); setCurrentPage(1); scrollTop()
                    if (v) { searchParams.set('tier', v) } else { searchParams.delete('tier') }
                    setSearchParams(searchParams)
                  }}
                  title="Filter by visibility level — how much public data backs the page"
                  className="appearance-none h-[34px] pl-3 pr-8 rounded-full font-body text-[12px] tracking-[0.02em] border transition-all duration-150 outline-none cursor-pointer"
                  style={{
                    backgroundColor: visTier ? '#C9A96E' : 'transparent',
                    color: visTier ? '#0A1628' : '#4B5563',
                    borderColor: visTier ? '#C9A96E' : '#E5E0DB',
                  }}
                >
                  <option value="">Any visibility</option>
                  <option value="beacon">Beacon</option>
                  <option value="torch">Torch</option>
                  <option value="candle">Candle</option>
                  <option value="spark">Spark</option>
                </select>
                <svg className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="6 9 12 15 18 9"/></svg>
              </div>
              {/* Revenue band */}
              <div className="relative">
                <select
                  value={revenueFilter}
                  onChange={e => handleRevenueChange((e.target.value || '') as RevenueId)}
                  title="Filter by the organization's annual revenue size"
                  className="appearance-none h-[34px] pl-3 pr-8 rounded-full font-body text-[12px] tracking-[0.02em] border transition-all duration-150 outline-none cursor-pointer"
                  style={{
                    backgroundColor: revenueFilter ? '#C9A96E' : 'transparent',
                    color: revenueFilter ? '#0A1628' : '#4B5563',
                    borderColor: revenueFilter ? '#C9A96E' : '#E5E0DB',
                  }}
                >
                  <option value="">Any size</option>
                  {REVENUE_PRESETS.map(p => (
                    <option key={p.id} value={p.id}>{p.label}</option>
                  ))}
                </select>
                <svg className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="6 9 12 15 18 9"/></svg>
              </div>
              {/* State */}
              <div className="relative">
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
                  <option value="">All States & Territories</option>
                  {US_STATES.map(([abbr, name]) => (
                    <option key={abbr} value={abbr}>{abbr} · {name}</option>
                  ))}
                  <optgroup label="Other Territories">
                    {US_TERRITORIES.map(([abbr, name]) => (
                      <option key={abbr} value={abbr}>{abbr} · {name}</option>
                    ))}
                  </optgroup>
                  <optgroup label="Armed Forces">
                    {US_MILITARY.map(([abbr, name]) => (
                      <option key={abbr} value={abbr}>{abbr} · {name}</option>
                    ))}
                  </optgroup>
                </select>
                <svg className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="6 9 12 15 18 9"/></svg>
              </div>
            </div>
          </div>}
          </div>

          {/* Subcategory pills — appear for every selected category, multi-select */}
          {searchMode === 'browse' && activeFilters.some(c => (NTEE_SUBCATEGORIES[c]?.length ?? 0) > 0) && (
            <div className="mt-3 space-y-2">
              {activeFilters.filter(c => (NTEE_SUBCATEGORIES[c]?.length ?? 0) > 0).map(catId => (
                <div key={catId} className="flex items-center gap-1.5 flex-wrap">
                  <span className="font-body text-[10px] uppercase tracking-[0.06em] text-cool-grey mr-1 shrink-0">
                    {FILTER_CATEGORIES.find(c => c.id === catId)?.label ?? catId}
                  </span>
                  {NTEE_SUBCATEGORIES[catId].map(sub => {
                    const on = subFilters.includes(sub.code)
                    return (
                      <button
                        key={sub.code}
                        onClick={() => handleSubChange(sub.code)}
                        className="px-3 py-1 rounded-full font-body text-[11px] transition-all duration-150 border"
                        style={{
                          backgroundColor: on ? '#0A1628' : 'transparent',
                          color: on ? '#F5F0EB' : '#6B7280',
                          borderColor: on ? '#0A1628' : '#E5E0DB',
                        }}
                      >
                        {sub.label}
                      </button>
                    )
                  })}
                </div>
              ))}
            </div>
          )}

          {/* Clear all — always visible when any filter is active */}
          {activeFilterCount > 0 && (
            <div className="mt-2">
              <button
                onClick={handleClearAll}
                className="font-body text-[12px] text-cool-grey hover:text-cool-grey transition-colors"
              >
                Clear all filters
              </button>
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
            cause={cause}
            onCategoryChange={(id) => { handleFilterChange(id) }}
            onStateChange={handleStateChange}
            onSortChange={(s) => { setSortBy(s); setCurrentPage(1); scrollTop() }}
            onRevenueChange={(id) => handleRevenueChange(id as RevenueId)}
            onScoreTierChange={(id) => handleScoreTierChange(id as ScoreTierId)}
            onCauseChange={setCause}
            onClearAll={handleClearAll}
            resultCount={total}
          />
        </div>
      </div>

      {/* Results */}
      <div className="bg-warm-cream py-12 md:py-16">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">

          {/* Browse mode — filters now live in the top toolbar, results full-width */}
          {searchMode === 'browse' && (
          <div>

            {/* Results column */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-4 mb-8 flex-wrap">
                <div>
                  <span className="font-body text-[20px] font-semibold tracking-[-0.02em] text-deep-navy">
                    {total.toLocaleString()} {effectiveHiddenGem ? 'hidden gems' : (searchQuery || activeFilters.length > 0 || stateFilter ? 'results' : 'organizations')}
                  </span>
                  {effectiveHiddenGem && (
                    <p className="font-body text-[12px] text-cool-grey mt-1 flex items-center flex-wrap gap-x-2 gap-y-1">
                      <span>Small, overlooked organizations · a fresh set each week.</span>
                      <button onClick={handleSeeAll} className="font-semibold text-soft-gold hover:text-bright-gold transition-colors">
                        See all 1.8M →
                      </button>
                    </p>
                  )}
                  {statsData?.irs_status_verified_at && (
                    <p className="font-body text-[12px] text-cool-grey mt-1">
                      Built from public IRS data, last checked {new Date(statsData.irs_status_verified_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
                    </p>
                  )}

                  {/* Active filter chips */}
                  {(searchQuery || activeFilters.length > 0 || subFilters.length > 0 || stateFilter || revenueFilter || scoreTier) && (
                    <div className="flex items-center gap-2 mt-2 flex-wrap">
                      {searchQuery && (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-navy-mid/8 text-deep-navy font-body text-[11px]">
                          "{searchQuery}"
                        </span>
                      )}
                      {useFusedResults && (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-soft-gold/15 text-soft-gold font-body text-[11px]" title="Results ranked by combining keyword matching and meaning, not by size or revenue">
                          Name + meaning
                        </span>
                      )}
                      {activeFilters.map(f => (
                        <button
                          key={f}
                          onClick={() => handleFilterChange(f)}
                          className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-soft-gold/10 text-soft-gold font-body text-[11px] hover:bg-soft-gold/20 transition-colors"
                        >
                          {RAIL_CATEGORIES.find(c => c.id === f)?.label} ×
                        </button>
                      ))}
                      {subFilters.map(code => (
                        <button
                          key={code}
                          onClick={() => handleSubChange(code)}
                          className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-deep-navy/8 text-deep-navy font-body text-[11px] hover:bg-deep-navy/15 transition-colors"
                        >
                          {subLabelOf(code)} ×
                        </button>
                      ))}
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
                  {subFilters.includes('X70') && (
                    <p className="mt-1.5 font-body text-[11px] text-cool-grey">
                      The IRS classifies Hindu, Sikh, Jain, and other non-Western faith traditions under this code. This reflects official IRS data, not our own categorization.
                    </p>
                  )}
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  {/* Sort + direction — hidden while gems is on (static weekly order) */}
                  {effectiveHiddenGem ? (
                    <span className="hidden sm:inline font-body text-[13px] text-cool-grey italic">Shuffled weekly</span>
                  ) : (
                    <div className="hidden sm:flex items-center gap-2">
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
                      <button
                        onClick={() => { setSortOrder(o => o === 'asc' ? 'desc' : 'asc'); setCurrentPage(1) }}
                        title={sortOrder === 'asc' ? 'Ascending — tap for descending' : 'Descending — tap for ascending'}
                        aria-label={`Sort direction: ${sortOrder === 'asc' ? 'ascending' : 'descending'}`}
                        className="inline-flex items-center justify-center w-7 h-7 rounded-md border border-light-grey text-cool-grey hover:text-deep-navy hover:border-cool-grey transition-colors"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                          style={{ transform: sortOrder === 'asc' ? 'rotate(180deg)' : 'none', transition: 'transform 150ms' }}>
                          <line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/>
                        </svg>
                      </button>
                    </div>
                  )}
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
              {activeLoading ? (
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
              ) : activeError ? (
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
